"""Run records: counts only, never prices (design section 8; R-MK-09).

Written to results/markets_<YYYY-MM-DD>/run_<run_id>.json, which is safe to commit.
"""
from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field, fields
from pathlib import Path

from . import COLLECTOR_VERSION
from .timeutil import iso_utc, utc_now

FORBIDDEN_KEYS = {"line", "price", "price_american", "price_decimal", "implied_prob", "bid", "ask", "last",
                  "fair_prob_power", "fair_prob_shin", "fair_prob_mult", "booksum", "body"}


@dataclass
class RunRecord:
    run_id: str
    started_utc: str = field(default_factory=lambda: iso_utc(utc_now()))
    collector_version: str = COLLECTOR_VERSION
    requests_by_source: Counter = field(default_factory=Counter)
    rows_by_source: Counter = field(default_factory=Counter)
    quarantined_by_rule: Counter = field(default_factory=Counter)
    flags_by_rule: Counter = field(default_factory=Counter)
    match_queue_by_reason: Counter = field(default_factory=Counter)
    quota_headers: dict[str, dict[str, str]] = field(default_factory=dict)
    completeness: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    finished_utc: str | None = None

    def write(self, results_dir: Path) -> Path:
        self.finished_utc = self.finished_utc or iso_utc(utc_now())
        # Counter is serialised as a plain dict (dataclasses.asdict would mangle Counter keys)
        doc = {f.name: (dict(getattr(self, f.name)) if isinstance(getattr(self, f.name), Counter) else getattr(self, f.name))
               for f in fields(self)}
        _assert_counts_only(doc)
        out = Path(results_dir) / f"markets_{self.started_utc[:10]}"
        out.mkdir(parents=True, exist_ok=True)
        path = out / f"run_{self.run_id}.json"
        path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path


def _assert_counts_only(node, path: str = "") -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            if str(k).lower() in FORBIDDEN_KEYS:
                raise ValueError(f"run record must not contain price fields: {path}/{k}")
            _assert_counts_only(v, f"{path}/{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _assert_counts_only(v, f"{path}[{i}]")
