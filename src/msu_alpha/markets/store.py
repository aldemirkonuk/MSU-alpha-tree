"""Snapshot and quarantine writers (design section 3.2; R-MK-03, R-RG-08, new-MK-12).

Snapshots: Parquet dataset under {root}/snapshots/source=…/season=…/month=…/part-{run_id}-{n}.parquet,
timestamps as timestamp[us, UTC]. Quarantine: JSONL under {root}/quarantine/. The root must be
outside the git repository: market tables are private and never committed.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from .config import REPO
from .models import QuarantineRow, SnapshotRow

try:  # pyarrow is optional at import time so the rest of the package works without it
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:  # pragma: no cover
    pa = pq = None


class PrivatePathError(PermissionError):
    pass


def ensure_private(root: Path) -> Path:
    root = Path(root).expanduser().resolve()
    if root == REPO or REPO in root.parents:
        raise PrivatePathError(f"market data root must be outside the git repo: {root}")
    return root


def snapshot_schema():
    if pa is None:
        raise ImportError("pyarrow is required to write snapshots: pip install 'msu-alpha[markets]'")
    ts = pa.timestamp("us", tz="UTC")
    f = pa.float64()
    return pa.schema([
        ("game_id", pa.string()), ("source", pa.dictionary(pa.int8(), pa.string())),
        ("book", pa.dictionary(pa.int16(), pa.string())), ("market", pa.dictionary(pa.int8(), pa.string())),
        ("market_phase", pa.string()), ("side", pa.string()), ("team_id", pa.string()), ("player_id", pa.string()),
        ("line", f), ("line_is_integer", pa.bool_()), ("price_american", pa.int32()), ("price_decimal", f),
        ("price_decimal_source", f), ("implied_prob", f), ("booksum", f), ("fair_prob_power", f),
        ("fair_prob_shin", f), ("fair_prob_mult", f), ("power_k", f), ("shin_z", f),
        ("bid", f), ("ask", f), ("last", f), ("bid_size", f), ("ask_size", f), ("volume", f), ("open_interest", f),
        ("snapshot_time_utc", ts), ("source_time_utc", ts), ("fetched_at_utc", ts),
        ("snapshot_label", pa.string()), ("observed_post_event", pa.bool_()), ("source_event_id", pa.string()),
        ("season", pa.int16()), ("dq_flags", pa.list_(pa.string())), ("raw_ref", pa.string()),
        ("schema_version", pa.int16()),
    ])


def dedupe(rows: list[SnapshotRow]) -> list[SnapshotRow]:
    seen: set[tuple] = set()
    out = []
    for r in rows:
        k = r.dedup_key()
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


_KEY_COLUMNS = ("game_id", "source_event_id", "source", "book", "market", "market_phase", "snapshot_label",
                "side", "team_id", "player_id", "line", "snapshot_time_utc")


def _record_key(rec: dict) -> tuple:
    """Same fields and order as SnapshotRow.dedup_key(), built from a stored record."""
    return (rec["game_id"], rec["source_event_id"], rec["source"], rec["book"], rec["market"], rec["market_phase"],
            rec["snapshot_label"], rec["side"], rec["team_id"] or rec["player_id"], rec["line"],
            rec["snapshot_time_utc"])


def _existing_keys(partition_dir: Path) -> set[tuple]:
    keys: set[tuple] = set()
    for f in partition_dir.glob("*.parquet"):
        for rec in pq.read_table(f, columns=list(_KEY_COLUMNS)).to_pylist():
            keys.add(_record_key(rec))
    return keys


class SnapshotStore:
    def __init__(self, root: str | Path):
        self.root = ensure_private(Path(root))

    def write(self, rows: list[SnapshotRow], run_id: str) -> list[Path]:
        """Write rows (de-duplicated on the C-14 key) as one file per partition; never overwrites."""
        schema = snapshot_schema()
        parts: dict[tuple, list[dict]] = defaultdict(list)
        for r in dedupe(rows):
            rec = r.to_record()
            parts[(rec["source"], rec["season"], f"{r.snapshot_time_utc:%Y-%m}")].append(rec)
        written = []
        for (source, season, month), recs in sorted(parts.items()):
            d = self.root / "snapshots" / f"source={source}" / f"season={season}" / f"month={month}"
            d.mkdir(parents=True, exist_ok=True)
            existing = _existing_keys(d)                 # idempotent across runs, not only within a batch
            recs = [r for r in recs if _record_key(r) not in existing]
            if not recs:
                continue
            n = 0
            while (path := d / f"part-{run_id}-{n}.parquet").exists():
                n += 1
            table = pa.Table.from_pylist(recs, schema=schema)
            pq.write_table(table, path)
            written.append(path)
        return written

    def read(self) -> "pa.Table":
        return pq.read_table(self.root / "snapshots", schema=snapshot_schema(), partitioning=None)


class QuarantineStore:
    def __init__(self, root: str | Path):
        self.root = ensure_private(Path(root)) / "quarantine"

    def write(self, rows: list[QuarantineRow], run_id: str) -> Path | None:
        if not rows:
            return None
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"quarantine-{run_id}.jsonl"
        with open(path, "a", encoding="utf-8") as fh:
            for q in rows:
                fh.write(json.dumps(q.__dict__, default=str, ensure_ascii=False) + "\n")
        return path
