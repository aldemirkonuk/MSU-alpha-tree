"""Data-platform pack (baseline 6): loader, lint and the helpers every prototype of the pack must use.

Usage:
  python tools/specgen/platform/dplib.py --check          # lint of config/data_platform.yaml + schema/platform_changes.yaml
  python tools/specgen/platform/dplib.py --check --final  # as above, and a row still waiting for a prototype is a problem
  python tools/specgen/platform/dplib.py --audit          # the MSU-relative audit of schema/tables (counts per table)
  python tools/specgen/platform/dplib.py --games          # game codes of the private play-by-play (codes only, never names)

The pack is one file: a header, conventions, cross_item (one id and version scheme for all four items), then one block
per item (team_neutral, query_layer, lineage, pbp_versions) and the journal. Every item block has the same parts:
ask, requirements, decisions, schemas, algorithms, params, acceptance, prototype, open_questions.

What the lint checks (validate):
  header   pack name, version, status, the four item blocks, every part of every block.
  rows     every requirement row has id, tier, requirement, product, unit, exceptions, test (and cites acceptance rows
           that exist); ids are unique; a new row is N-<FAM>-nn, a sharpened row keeps its live id.
  accept   every acceptance row has metric, scope, threshold, on_fail and a status: met (its results reference
           resolves), failed (results reference + failure_note), pending_prototype (names the results key the
           prototype will write) or not_yet_testable (with the reason). Every row is cited by a requirement row.
  params   value, unit, why, evidence; the evidence starts with a known tag; a results/ path it names exists (or is
           the results file a prototype of the pack will write); `mirrors` equals the other config.
  decide   every decision has a question, at least two options, exactly one chosen, a why on every rejected one.
  algos    numbered steps; every ALG id cited anywhere exists.
  names    every table and column named in the pack exists in schema/tables or in schema/platform_changes.yaml;
           every metric id exists in config/metrics.yaml; every transition, dimension and integrity id exists in
           config/state_machine.yaml; every id prefix of cross_item.ids equals the constants of this file.
  neutral  no MSU-relative column is introduced by the pack or by the change set; the audit of schema/tables is
           complete (every flagged column has exactly one disposition, and no disposition is stale).
  hygiene  no 9-digit id, no private path component beyond the scratch root, no licensed field value in the pack.

Helpers (all four prototypes use these, none re-implements them):
  canonical_json, content_hash, det_id, event_id, row_hash, slice_hash, config_hash, code_version, output_key,
  state_version, ensure_private, atomic_write, write_public_result, discover_games, stage_run.

Evidence code of the build freeze: nothing here is production code and nothing is imported by src/.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import secrets
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
PACK = REPO / "config" / "data_platform.yaml"
CHANGES = REPO / "schema" / "platform_changes.yaml"
SCHEMA_DIR = REPO / "schema" / "tables"
METRICS = REPO / "config" / "metrics.yaml"
STATE_MACHINE = REPO / "config" / "state_machine.yaml"
RESULTS_DIR = REPO / "results" / "platform_test"
CODE_DIR = Path(__file__).resolve().parent

PRIVATE_ENV = "MSU_ALPHA_PRIVATE"            # overrides the private root (tests point it at a temp folder)
SCRATCH_DATE = "platform_2026-11-11"

ITEMS = ("team_neutral", "query_layer", "lineage", "pbp_versions")
ITEM_CODE = {"team_neutral": "TN", "query_layer": "QL", "lineage": "LN", "pbp_versions": "PV"}
ITEM_PARTS = ("ask", "live_rows", "requirements", "decisions", "schemas", "algorithms", "params", "acceptance",
              "prototype", "open_questions")
REQ_KEYS = ("id", "tier", "requirement", "product", "unit", "exceptions", "test")
ACC_KEYS = ("metric", "scope", "threshold", "on_fail", "status")
ACC_STATUS = ("met", "failed", "pending_prototype", "not_yet_testable")
PARAM_KEYS = ("value", "unit", "why", "evidence")
TIERS = ("Shall", "Should")
AREA_CODES = {"FD", "MD", "SY", "EN", "DQ", "RR", "AS", "PR", "CS", "RG"}

ID_HEX_LEN = 16                              # mirrored by cross_item.params.id_hex_len (lint)
# prefix -> what it names. Mirrored by cross_item.ids (lint). A prefix is never reused for another thing.
ID_PREFIXES = {
    "pl": "pull_id", "pv": "pbp_version_id", "cf": "config_hash", "cv": "code_version", "ok": "output_key",
    "sv": "state_version", "sn": "snapshot_id", "run": "run_id", "tr": "transition_id", "sg": "segment_id",
    "po": "possession_key", "ch": "chance_key", "st": "stint_key", "pg": "player_game_id", "tg": "team_game_id",
    "df": "diff_id", "cs": "change_set_id", "qs": "binding_hash", "mv": "lineage_handle", "sc": "stat_correction_id",
}

# Column-name tokens that make a column relative to one programme or to "us" (the audit of ALG-TN-1).
NAME_TOKENS = ("msu", "opp", "opponent", "opponents", "our", "their", "focus", "own", "us", "them", "foe", "spartan",
               "spartans")
_NAME_RE = re.compile(r"(^|_)(" + "|".join(NAME_TOKENS) + r")(_|$)", re.I)
ALWAYS_FORBIDDEN = ("msu", "our", "their", "us", "them", "foe", "spartan", "spartans")   # in anything the pack adds
FOCUS_TOKENS = ("focus", "other")            # only in a view of layer `focus`
ROW_RELATIVE_TOKENS = ("opp", "opponent", "opponents", "own")   # only in a team-keyed or focus view, or declared row-relative
NOT_A_COLUMN = {"yaml", "yml", "json", "jsonl", "py", "md", "parquet", "sql", "tsv", "csv", "gz", "pdf", "lock", "txt"}
# Fields of a licensed play row. A public result never carries one of these as a key (aggregates only).
LICENSED_KEYS = {"playText", "participants", "onFloor", "shotInfo", "sourceId", "gameSourceId", "gameId", "wallclock",
                 "athleteId", "athleteSourceId", "homeTeam", "awayTeam", "team", "opponent", "venue", "name", "text",
                 "homeTeamId", "awayTeamId", "teamId", "opponentId", "body", "rows", "plays"}


class PackError(ValueError):
    pass


class PrivatePathError(PermissionError):
    """A licensed or row-level write was pointed inside the public repo."""


class PublicResultError(ValueError):
    """A public result holds something that looks like a licensed row, a real id or a real name."""


# ------------------------------------------------------------------------------------------------------------ loading
class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that refuses a mapping with the same key twice (plain YAML keeps the last one silently)."""


def _unique_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise PackError(f"key {key!r} is written twice (line {key_node.start_mark.line + 1})")
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def load_yaml_strict(path):
    try:
        return yaml.load(Path(path).read_text(encoding="utf-8"), Loader=_UniqueKeyLoader)
    except PackError as e:
        raise PackError(f"{Path(path).name}: {e}") from None


def load_pack(path=PACK):
    return load_yaml_strict(path)


def load_changes(path=CHANGES):
    return load_yaml_strict(path) if Path(path).exists() else None


def is_param(o):
    return isinstance(o, dict) and "value" in o and any(k in o for k in ("unit", "why", "evidence"))


def params(pack):
    """Flat {name: param} over the whole pack. A name is written once; the lint reports a second one."""
    out, dup = {}, []

    def take(block, where):
        for name, p in (block or {}).items():
            if name in out:
                dup.append(f"{name} ({where})")
            out[name] = p

    take((pack.get("cross_item") or {}).get("params"), "cross_item")
    for item in ITEMS:
        take((pack.get(item) or {}).get("params"), item)
    out["_duplicates"] = dup
    return out


def P(name, pack=None):
    """Value of one param of the pack. The reference prototypes read every number through this."""
    pack = pack or load_pack()
    return params(pack)[name]["value"]


def dig(obj, dotted):
    """Walk a dotted key. In a list a number is an index and a name picks the item whose id matches."""
    for seg in str(dotted).split("."):
        if isinstance(obj, list):
            obj = obj[int(seg)] if seg.isdigit() else next(x for x in obj if isinstance(x, dict) and str(x.get("id")) == seg)
        else:
            obj = obj[seg]
    return obj


# ------------------------------------------------------------------------------------- canonical form, hashes and ids
def _canon(o):
    if isinstance(o, dict):
        for k in o:
            if not isinstance(k, str):
                raise TypeError(f"canonical JSON needs string keys, got {type(k).__name__}")
        return {k: _canon(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_canon(v) for v in o]
    if isinstance(o, bool) or o is None or isinstance(o, (int, str)):
        return o
    if isinstance(o, float):
        if math.isnan(o) or math.isinf(o):
            raise ValueError("canonical JSON has no NaN or infinity; write null and say why")
        return 0.0 if o == 0.0 else o          # -0.0 and 0.0 are one value
    raise TypeError(f"canonical JSON cannot hold {type(o).__name__}")


def canonical_json(obj) -> bytes:
    """The one byte form every hash of the pack is taken over (cross_item.hash.canonical_json).

    UTF-8, keys sorted by code point, no white space, strings as they are (no Unicode normalisation), integers as
    integers, floats in Python's shortest round-trip form, no NaN or infinity, tuples as lists. Lists keep their
    order: where order is not content the caller sorts first.
    """
    return json.dumps(_canon(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def content_hash(obj) -> str:
    """Full 64-character sha256 of the canonical form."""
    return sha256_hex(canonical_json(obj))


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def det_id(prefix: str, *parts) -> str:
    """Deterministic id: `<prefix>-<first ID_HEX_LEN hex of sha256(canonical JSON of the list of parts)>`.

    The parts are the content that makes the thing what it is, in the order the pack's id table gives. Never a run
    number, a wall time, a row position in an output file or a host name.
    """
    if prefix not in ID_PREFIXES or prefix == "run":
        raise ValueError(f"unknown id prefix {prefix!r}; the id table is cross_item.ids of config/data_platform.yaml")
    if not parts:
        raise ValueError("an id needs at least one part")
    return f"{prefix}-{content_hash(list(parts))[:ID_HEX_LEN]}"


def event_id(game_id, source: str, source_play_id) -> str:
    """Play-by-play event id (R-EN-11): readable, taken from the source's own play id, stable under a clock fix."""
    for part in (game_id, source, source_play_id):
        if part is None or str(part) == "" or ":" in str(part):
            raise ValueError("event id parts must be non-empty and hold no colon")
    return f"{game_id}:{source}:{source_play_id}"


def row_hash(row: dict, exclude=("row_hash",)) -> str:
    """Hash of one row's content (all columns but the ones excluded). Equal hash = the row did not change."""
    return content_hash({k: v for k, v in row.items() if k not in exclude})[:ID_HEX_LEN]


def slice_hash(rows, columns, key) -> str:
    """Hash of a declared slice of a table: the rows projected to `columns`, sorted by the `key` columns.

    A stage's input key is built from slice hashes, so a change outside the columns a stage reads does not re-run it.
    """
    columns, key = list(columns), list(key)
    missing = [k for k in key if k not in columns]
    if missing:
        raise ValueError(f"slice key columns {missing} are not in the slice")
    proj = [[r.get(c) for c in columns] for r in rows]
    idx = [columns.index(k) for k in key]
    proj.sort(key=lambda r: canonical_json([r[i] for i in idx]))
    return content_hash({"columns": columns, "rows": proj})


def config_hash(refs, repo=REPO) -> str:
    """`cf-` id of the config a stage declares. refs = [(repo path, [dotted keys] or None for the whole file)].

    Taken over the PARSED content, so a comment or a journal line outside the declared keys changes nothing.
    """
    doc = {}
    for path, keys in sorted(refs, key=lambda r: str(r[0])):
        parsed = yaml.safe_load((Path(repo) / path).read_text(encoding="utf-8"))
        doc[str(path)] = parsed if not keys else {k: dig(parsed, k) for k in sorted(keys)}
    return det_id("cf", doc)


def code_version(files, repo=REPO, lockfile="uv.lock") -> str:
    """`cv-` id of the code a stage declares: (repo path, sha256 of the bytes) per file, plus the lockfile's hash."""
    parts = sorted([str(Path(f).resolve().relative_to(Path(repo).resolve())) if Path(f).is_absolute() else str(f),
                    file_sha256(Path(repo) / f)] for f in files)
    lock = Path(repo) / lockfile
    return det_id("cv", parts, file_sha256(lock) if lock.exists() else None)


def output_key(stage: str, code_ver: str, cfg_hash: str, input_keys) -> str:
    """`ok-` id of one stage output (R-EN-09): stage name, code version, config hash, sorted input keys.

    input_keys = [(input name, slice hash or body sha256)]. A stage whose key exists is skipped.
    """
    return det_id("ok", stage, code_ver, cfg_hash, sorted([str(n), str(h)] for n, h in input_keys))


def state_version(fold_output_key: str) -> str:
    """The state version of a game is the output key of its fold stage, written with the `sv-` prefix."""
    if not fold_output_key.startswith("ok-"):
        raise ValueError("state_version is derived from the fold stage's output key (ok-...)")
    return "sv-" + fold_output_key[3:]


# --------------------------------------------------------------------------------------- private and public writing
def private_root() -> Path:
    return Path(os.environ.get(PRIVATE_ENV) or "~/MSU-Alpha-3-private").expanduser()


def scratch_dir(label: str, create=True) -> Path:
    """<private root>/work/platform_2026-11-11/<label>/ - the only place a prototype writes row-level data."""
    if not re.fullmatch(r"[a-z0-9_]+", label or ""):
        raise ValueError("label is lower case letters, digits and underscores")
    d = ensure_private(private_root() / "work" / SCRATCH_DATE / label)
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def ensure_private(path, repo=REPO) -> Path:
    """Refuse any path inside the public repo (and /tmp). Every writer of row-level or licensed data calls this."""
    p = Path(path).expanduser().resolve()
    repo = Path(repo).resolve()
    if p == repo or repo in p.parents:
        raise PrivatePathError(f"row-level data must not be written inside the public repo: {p}")
    for tmp in (Path("/tmp").resolve(), Path("/private/tmp").resolve()):
        if (p == tmp or tmp in p.parents) and not os.environ.get(PRIVATE_ENV):
            raise PrivatePathError(f"row-level data must not be written under {tmp}: {p}")
    return p


def atomic_write(path, data: bytes, private=True) -> Path:
    """Write to a temp name in the same folder, then rename (R-EN-10). private=True runs the repo guard first."""
    p = ensure_private(path) if private else Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(f".{p.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, p)
    return p


def assert_public_safe(obj, forbidden=(), _path="") -> None:
    """Raise if a result meant for the repo holds a licensed field, a 9-digit id or one of the `forbidden` strings.

    forbidden = real game ids and team names of the private files (GameSet.forbidden_strings()).
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k) in LICENSED_KEYS:
                raise PublicResultError(f"public result holds the licensed field {k!r} at {_path or '/'}")
            assert_public_safe(k, forbidden, f"{_path}/{k}")
            assert_public_safe(v, forbidden, f"{_path}/{k}")
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            assert_public_safe(v, forbidden, f"{_path}[{i}]")
    elif isinstance(obj, str):
        if re.search(r"(?<!\d)\d{9,}(?!\d)", obj):
            raise PublicResultError(f"public result holds a long digit string (a source id?) at {_path}")
        low = obj.lower()
        for f in forbidden:
            if f and str(f).lower() in low:
                raise PublicResultError(f"public result holds a private id or name at {_path}")
    elif isinstance(obj, int) and not isinstance(obj, bool):
        if abs(obj) >= 10 ** 8 and str(abs(obj)) in {str(f) for f in forbidden}:
            raise PublicResultError(f"public result holds a private id at {_path}")


def write_public_result(name: str, obj, forbidden=(), results_dir=RESULTS_DIR) -> Path:
    """Write results/platform_test/<name>.json (aggregates and game codes only) after the public-safety check."""
    if not re.fullmatch(r"[a-z0-9_]+", name):
        raise ValueError("result name is lower case letters, digits and underscores")
    assert_public_safe(obj, forbidden)
    path = Path(results_dir) / f"{name}.json"
    return atomic_write(path, (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8"), private=False)


# ------------------------------------------------------------------------------------------- private data discovery
@dataclass(frozen=True)
class GameRef:
    """One held game. Prints as its code only; the path and the ids inside the files stay private."""
    code: str
    season_label: str                        # "S1", "S2", ... in order of first appearance (no year in public text)
    pulls: tuple = field(repr=False, default=())   # play-by-play files of this game, oldest pull first (private paths)
    record_file: str = field(repr=False, default="")
    cbbd_game_id: int = field(repr=False, default=0)

    def __repr__(self):
        return f"GameRef({self.code})"

    __str__ = __repr__

    @property
    def plays_path(self) -> Path:
        return Path(self.pulls[-1])

    def load_plays(self, pull: int = -1) -> list:
        return json.loads(Path(self.pulls[pull]).read_text(encoding="utf-8"))

    def load_record(self) -> dict:
        """The game record (teams, final score, neutral site). Holds names: private use only."""
        for g in json.loads(Path(self.record_file).read_text(encoding="utf-8")):
            if g.get("id") == self.cbbd_game_id:
                return g
        raise KeyError(f"{self.code}: no game record")

    def headers_path(self, pull: int = -1):
        p = Path(self.pulls[pull]).with_suffix(".headers")
        return p if p.exists() else None


class GameSet(list):
    def by_code(self, code):
        return next(g for g in self if g.code == code)

    def forbidden_strings(self) -> set:
        """Real ids and team names of the held games, for assert_public_safe. Never printed."""
        out = set()
        for g in self:
            out.add(str(g.cbbd_game_id))
            try:
                rec = g.load_record()
            except (KeyError, OSError, ValueError):
                continue
            for k in ("sourceId", "homeTeam", "awayTeam", "venue"):
                if rec.get(k):
                    out.add(str(rec[k]))
        return {s for s in out if len(s) >= 4}


def discover_games(root=None) -> GameSet:
    """Held play-by-play, as game codes P01.. (the code -> game mapping is this rule; it is stable as files are added).

    Order: every folder <root>/data/licensed/cbbd/<pull date>/ by date. In a folder: single-game files
    (NN_plays_game*.json, by name), then plays/*.json by name. A game gets its code the first time it is seen; a later
    file of the same game is one more pull of it, not a new code. Returns an empty set when the data is absent.
    """
    base = Path(root) if root else private_root()
    cbbd = base / "data" / "licensed" / "cbbd"
    if not cbbd.is_dir():
        return GameSet()
    records, seasons = {}, []
    for f in sorted(cbbd.glob("*/[0-9][0-9]_games_msu*.json")):
        try:
            for g in json.loads(f.read_text(encoding="utf-8")):
                if isinstance(g, dict) and "id" in g and "homePoints" in g:
                    records.setdefault(g["id"], (str(f), g.get("season")))
        except (OSError, ValueError):
            continue
    order, pulls = [], {}
    for day in sorted(p for p in cbbd.iterdir() if p.is_dir()):
        files = sorted(day.glob("[0-9][0-9]_plays_game*.json")) + sorted((day / "plays").glob("*.json"))
        for f in files:
            try:
                rows = json.loads(f.read_text(encoding="utf-8"))
                gid = rows[0]["gameId"]
            except (OSError, ValueError, KeyError, IndexError, TypeError):
                continue
            if gid not in pulls:
                order.append(gid)
                pulls[gid] = []
            pulls[gid].append(str(f))
    out = GameSet()
    for i, gid in enumerate(order, 1):
        rec_file, season = records.get(gid, ("", None))
        if season not in seasons:
            seasons.append(season)
        out.append(GameRef(code=f"P{i:02d}", season_label=f"S{seasons.index(season) + 1}", pulls=tuple(pulls[gid]),
                           record_file=rec_file, cbbd_game_id=gid))
    return out


# ------------------------------------------------------------------------------------------------------ run records
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def new_run_id(now: str | None = None) -> str:
    """run-<UTC compact>-<8 random hex>. A run is an event, not content: this id is never written into a table row."""
    stamp = re.sub(r"[-:]", "", (now or utc_now_iso()))[:15] + "Z"
    return f"run-{stamp}-{secrets.token_hex(4)}"


class StageRun:
    """The run record of one stage execution (lineage.schemas.stage_runs). Filled inside `with stage_run(...)`."""

    def __init__(self, stage, label, config_refs=(), code_files=(), dag_node=None, run_id=None, seed=None):
        self.doc = {
            "run_id": run_id or new_run_id(), "stage": stage, "dag_node": dag_node or stage, "label": label,
            "status": "running", "started_utc": utc_now_iso(), "finished_utc": None, "duration_s": None,
            "cost": {"cpu_s": None, "gpu_s": 0.0, "api_calls": 0, "usd": 0.0},
            "code_version": code_version(code_files) if code_files else None,
            "config_hash": config_hash(config_refs) if config_refs else None,
            "config_refs": [[str(p), sorted(k) if k else None] for p, k in config_refs],
            "code_files": sorted(str(f) for f in code_files),
            "seed": seed, "inputs": [], "outputs": [], "counts": {}, "notes": [], "error": None,
        }

    @property
    def run_id(self):
        return self.doc["run_id"]

    def add_input(self, name, key, rows=None, kind="slice"):
        """name = table or file role; key = slice hash, output key or body sha256 (never a path with a real id)."""
        self.doc["inputs"].append({"name": str(name), "key": str(key), "rows": rows, "kind": kind})

    def add_output(self, table, key, rows, content=None, bytes_=None, file_sha=None):
        self.doc["outputs"].append({"table": str(table), "output_key": str(key), "rows": rows, "content_hash": content,
                                    "bytes": bytes_, "file_sha256": file_sha})

    def count(self, name, n=1):
        self.doc["counts"][name] = self.doc["counts"].get(name, 0) + n

    def note(self, text):
        self.doc["notes"].append(str(text))

    def skipped(self):
        """The output key already existed: nothing was computed (R-EN-09)."""
        self.doc["status"] = "skipped_cached"

    def output_key(self, stage=None):
        return output_key(stage or self.doc["stage"], self.doc["code_version"], self.doc["config_hash"],
                          [(i["name"], i["key"]) for i in self.doc["inputs"]])


@contextmanager
def stage_run(stage, label, config_refs=(), code_files=(), dag_node=None, run_id=None, seed=None, scratch=None):
    """Context manager: one JSON run record per stage execution, written to <scratch>/<label>/runs/<run_id>.json.

    One file per run, never appended (R-EN-10). The file is written on success and on failure; a failure is re-raised.
    """
    run = StageRun(stage, label, config_refs, code_files, dag_node, run_id, seed)
    out_dir = ensure_private(Path(scratch) if scratch else scratch_dir(label)) / "runs"
    t0, c0 = time.perf_counter(), time.process_time()
    try:
        yield run
        if run.doc["status"] == "running":
            run.doc["status"] = "ok"
    except BaseException as e:           # the record of a failed run is kept (R-RR-08)
        run.doc["status"] = "failed"
        run.doc["error"] = f"{type(e).__name__}: {e}"[:500]
        raise
    finally:
        run.doc["finished_utc"] = utc_now_iso()
        run.doc["duration_s"] = round(time.perf_counter() - t0, 6)
        run.doc["cost"]["cpu_s"] = round(time.process_time() - c0, 6)
        atomic_write(out_dir / f"{run.run_id}.json", (json.dumps(run.doc, indent=2, sort_keys=True) + "\n").encode("utf-8"))


# --------------------------------------------------------------------------------------------------- schema helpers
_CACHE = {}


def _col_specs(spec):
    c = (spec or {}).get("columns")
    if isinstance(c, dict):
        return {k: (v if isinstance(v, dict) else {"type": v}) for k, v in c.items()}
    return {x["name"]: x for x in (c or []) if isinstance(x, dict) and "name" in x}


def schema_tables():
    """{table: {column: spec}} from schema/tables (both YAML dialects). Read once per process."""
    if "schema" not in _CACHE:
        out = {}
        for p in sorted(SCHEMA_DIR.glob("*.yaml")):
            try:
                d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                continue
            out[d.get("table") or d.get("name") or p.stem] = _col_specs(d)
        _CACHE["schema"] = out
    return _CACHE["schema"]


def _yaml_cached(path):
    if path not in _CACHE:
        _CACHE[path] = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return _CACHE[path]


def metric_ids():
    if "metric_ids" not in _CACHE:      # the registry is 109,000 lines; ids are read with a regular expression
        _CACHE["metric_ids"] = set(re.findall(r"^\s*-?\s*id:\s*(M-[A-Z]+-\d{3})\s*$", METRICS.read_text(encoding="utf-8"), re.M))
    return _CACHE["metric_ids"]


def _enum_values(c):
    vals = c.get("values") or c.get("enum") or []
    if isinstance(vals, dict):
        vals = list(vals)
    if isinstance(vals, str):
        vals = [vals]
    return [str(v) for v in vals or []]


def audit_msu_relative(tables=None):
    """ALG-TN-1. Every column of schema/tables whose NAME or ENUM VALUES hold a team-relative token.

    -> sorted list of (table, column, kind, bad_values); kind = name | enum | name+enum. Text-only mentions (a hint
    such as a team id in a range text) are counted by the change set's definition_fixes, not here.
    """
    out = []
    for table, cols in sorted((tables if tables is not None else schema_tables()).items()):
        for name, c in cols.items():
            kinds = ["name"] if _NAME_RE.search(name) else []
            bad = [v for v in _enum_values(c) if _NAME_RE.search(v)]
            if not bad and str(c.get("type", "")).startswith("enum"):
                rng = re.sub(r"[^a-z0-9_]+", " ", str(c.get("range", "")).lower()).split()
                bad = [v for v in rng if _NAME_RE.search(v)]
            if bad:
                kinds.append("enum")
            if kinds:
                out.append((table, name, "+".join(kinds), tuple(bad)))
    return out


def proposed(changes):
    """What schema/platform_changes.yaml adds: {tables: {name: set(columns)}, views: {name: {layer, columns}}}."""
    tables, views = {}, {}
    if not changes:
        return {"tables": tables, "views": views}

    def cols(entries):
        out = set()
        for c in entries or []:
            name = (c.get("column") or c.get("name")) if isinstance(c, dict) else c
            if name:
                out.add(str(name))
        return out

    for t, spec in (changes.get("new_tables") or {}).items():
        tables.setdefault(t, set()).update(cols((spec or {}).get("columns")))
    for t, entries in (changes.get("column_additions") or {}).items():
        tables.setdefault(t, set()).update(cols(entries))
    for t, entries in ((changes.get("team_neutral") or {}).get("audit") or {}).items():
        for col, d in (entries or {}).items():
            for new in ([d.get("to")] if isinstance(d.get("to"), str) else d.get("to") or []):
                tables.setdefault(t, set()).add(new)
    for t, entries in ((changes.get("team_neutral") or {}).get("other_renames") or {}).items():
        for d in entries or []:
            for new in ([d.get("to")] if isinstance(d.get("to"), str) else d.get("to") or []):
                tables.setdefault(t, set()).add(new)
    for v, spec in (changes.get("views") or {}).items():
        views[v] = {"layer": (spec or {}).get("layer"), "columns": cols((spec or {}).get("columns")),
                    "parameters": list((spec or {}).get("parameters") or [])}
    return {"tables": tables, "views": views}


def _tokens(name):
    return [t for t in re.split(r"[^a-z0-9]+", str(name).lower()) if t]


def relative_problem(name, layer=None, row_relative=False):
    """Why a column name the pack adds is not allowed, or None. layer = None (stored), team_keyed or focus."""
    toks = set(_tokens(name))
    bad = toks & set(ALWAYS_FORBIDDEN)
    if bad:
        return f"names one programme or 'us' ({', '.join(sorted(bad))})"
    if toks & set(FOCUS_TOKENS) and layer != "focus":
        return "a focus / other column outside a focus view"
    if toks & set(ROW_RELATIVE_TOKENS) and layer not in ("team_keyed", "focus") and not row_relative:
        return "an opponent / own column in a stored table that is not declared relative to the row's team"
    return None


# -------------------------------------------------------------------------------------------------------------- lint
def _walk_strings(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield f"{path}.{k}", str(k)
            yield from _walk_strings(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from _walk_strings(v, f"{path}[{i}]")
    elif isinstance(o, str):
        yield path, o


def evidence_ok(text, pack):
    tags = ((pack.get("conventions") or {}).get("evidence_tags") or {}).get("tags") or {}
    return isinstance(text, str) and any(text.startswith(f"{t}:") for t in tags)


def _results_ref_ok(ref, repo=REPO):
    """'path#dotted.key' or 'path'. -> (exists, key_resolves)."""
    path, _, key = str(ref).partition("#")
    p = Path(repo) / path.strip()
    if not p.exists():
        return False, False
    if not key:
        return True, True
    try:
        dig(json.loads(p.read_text(encoding="utf-8")) if p.suffix == ".json" else yaml.safe_load(p.read_text(encoding="utf-8")), key.strip())
        return True, True
    except (KeyError, IndexError, StopIteration, ValueError, TypeError):
        return True, False


def validate(pack=None, changes="load", final=False, repo=REPO):
    """-> list of problems (empty = the pack passes). final=True: a row still pending its prototype is a problem."""
    pack = pack if pack is not None else load_pack()
    changes = load_changes() if isinstance(changes, str) and changes == "load" else changes
    problems = []
    add = problems.append

    # ---- header
    if pack.get("pack") != "data_platform":
        add("pack: name is not data_platform")
    for k in ("version", "date", "status", "scope", "requirement", "files", "conventions", "cross_item", "journal"):
        if not pack.get(k):
            add(f"header: {k} is missing")
    if not re.fullmatch(r"\d+\.\d+\.\d+", str(pack.get("version", ""))):
        add("header: version is not semver")
    for item in ITEMS:
        block = pack.get(item)
        if not isinstance(block, dict):
            add(f"{item}: block is missing")
            continue
        for part in ITEM_PARTS:
            if part not in block or (block[part] in (None, "", [], {}) and part != "open_questions"):
                add(f"{item}: part {part} is missing or empty")

    # ---- params
    allp = params(pack)
    for d in allp.pop("_duplicates"):
        add(f"param {d}: the name is written twice in the pack")
    planned_results = {str((pack.get(i) or {}).get("prototype", {}).get("results_file")) for i in ITEMS}
    for name, p in allp.items():
        if not isinstance(p, dict):
            add(f"param {name}: not a mapping")
            continue
        for k in PARAM_KEYS:
            if k not in p or p[k] in (None, ""):
                add(f"param {name}: {k} is missing")
        ev = p.get("evidence")
        if ev and not evidence_ok(ev, pack):
            add(f"param {name}: evidence does not start with a tag of conventions.evidence_tags")
        for path in re.findall(r"\bresults/[A-Za-z0-9_./-]+\.(?:json|md)", str(ev or "")):
            if path not in planned_results and not (Path(repo) / path).exists():
                add(f"param {name}: evidence names {path}, which does not exist and is no prototype's results file")
        if p.get("mirrors"):
            mpath, _, mkey = str(p["mirrors"]).partition(":")
            try:
                other = dig(_yaml_cached(Path(repo) / mpath), mkey)
                if other != p.get("value"):
                    add(f"param {name}: value {p.get('value')!r} differs from {p['mirrors']} ({other!r})")
            except (OSError, KeyError, IndexError, StopIteration, TypeError):
                add(f"param {name}: mirrors {p['mirrors']} cannot be read")
    cip = (pack.get("cross_item") or {}).get("params") or {}
    if (cip.get("id_hex_len") or {}).get("value") != ID_HEX_LEN:
        add(f"cross_item.params.id_hex_len differs from dplib.ID_HEX_LEN ({ID_HEX_LEN})")

    # ---- id table
    ids = (pack.get("cross_item") or {}).get("ids") or {}
    seen_prefix = {}
    for name, rule in ids.items():
        if not isinstance(rule, dict):
            add(f"cross_item.ids.{name}: not a mapping")
            continue
        for k in ("made_from", "carried_by", "why"):
            if not rule.get(k):
                add(f"cross_item.ids.{name}: {k} is missing")
        pre = rule.get("prefix")
        if pre in (None, "none"):
            continue
        if pre in seen_prefix:
            add(f"cross_item.ids.{name}: prefix {pre} is already used by {seen_prefix[pre]}")
        seen_prefix[pre] = name
        if ID_PREFIXES.get(pre) != name:
            add(f"cross_item.ids.{name}: prefix {pre!r} is not this id's prefix in dplib.ID_PREFIXES")
    for pre, name in ID_PREFIXES.items():
        if name not in ids:
            add(f"cross_item.ids: {name} (prefix {pre}) of dplib.ID_PREFIXES has no rule in the pack")

    # ---- per item: requirements, acceptance, decisions, algorithms, prototype, open questions
    req_ids, acc_rows, acc_cited, alg_ids, dd_ids, oq_ids = {}, {}, set(), set(), set(), set()
    for item in ITEMS:
        block = pack.get(item) or {}
        code = ITEM_CODE[item]
        for i, r in enumerate(block.get("requirements") or []):
            rid = (r or {}).get("id", f"#{i}")
            where = f"{item}.requirements.{rid}"
            for k in REQ_KEYS:
                if not isinstance(r, dict) or r.get(k) in (None, ""):
                    add(f"{where}: {k} is missing")
            if not isinstance(r, dict):
                continue
            if rid in req_ids:
                add(f"{where}: id is already used in {req_ids[rid]}")
            req_ids[rid] = item
            m = re.fullmatch(r"(N|R)-([A-Z]{2})-(\d{2})", str(rid))
            if not m or m.group(2) not in AREA_CODES:
                add(f"{where}: id is not N-<FAM>-nn or R-<FAM>-nn with a known area code")
            elif m.group(1) == "R" and r.get("kind") != "sharpens":
                add(f"{where}: a live id is only used for a row that sharpens it (kind: sharpens)")
            elif m.group(1) == "N" and r.get("kind") not in ("new", "splits"):
                add(f"{where}: a proposed row says kind: new, or kind: splits with from: <live id>")
            if r.get("kind") == "splits" and not re.fullmatch(r"R-[A-Z]{2}-\d{2}", str(r.get("from", ""))):
                add(f"{where}: kind splits needs from: <live id>")
            if r.get("tier") not in TIERS:
                add(f"{where}: tier is not Shall or Should")
            if not r.get("acceptance"):
                add(f"{where}: cites no acceptance row")
            acc_cited.update(r.get("acceptance") or [])
        for aid, a in (block.get("acceptance") or {}).items():
            where = f"{item}.acceptance.{aid}"
            if not re.fullmatch(rf"ACC-DP-{code}-\d+", str(aid)):
                add(f"{where}: id is not ACC-DP-{code}-n")
            if aid in acc_rows:
                add(f"{where}: id is written twice")
            acc_rows[aid] = a
            if not isinstance(a, dict):
                add(f"{where}: not a mapping")
                continue
            for k in ACC_KEYS:
                if a.get(k) in (None, ""):
                    add(f"{where}: {k} is missing")
            st = a.get("status")
            if st not in ACC_STATUS:
                add(f"{where}: status is not one of {', '.join(ACC_STATUS)}")
            if st in ("met", "failed"):
                if not a.get("results"):
                    add(f"{where}: status {st} needs a results reference")
                else:
                    exists, key_ok = _results_ref_ok(a["results"], repo)
                    if not exists:
                        add(f"{where}: results file of {a['results']} does not exist")
                    elif not key_ok:
                        add(f"{where}: results key of {a['results']} does not resolve")
                if st == "failed" and not a.get("failure_note"):
                    add(f"{where}: status failed needs a failure_note")
            if st == "pending_prototype":
                if not a.get("results") or "#" not in str(a.get("results")):
                    add(f"{where}: a pending row names the results file and key the prototype will write (file#key)")
                if final:
                    add(f"{where}: still pending its prototype")
            if st == "not_yet_testable" and not a.get("reason"):
                add(f"{where}: not_yet_testable needs the reason")
        for d in block.get("decisions") or []:
            did = (d or {}).get("id", "?")
            where = f"{item}.decisions.{did}"
            dd_ids.add(did)
            if not re.fullmatch(rf"DD-{code}-\d+", str(did)):
                add(f"{where}: id is not DD-{code}-n")
            for k in ("question", "options", "choice", "why"):
                if not (d or {}).get(k):
                    add(f"{where}: {k} is missing")
            opts = (d or {}).get("options") or []
            if len(opts) < 2:
                add(f"{where}: a decision lists at least two options")
            chosen = [o for o in opts if isinstance(o, dict) and o.get("verdict") == "chosen"]
            if len(chosen) != 1:
                add(f"{where}: exactly one option is chosen (found {len(chosen)})")
            elif chosen[0].get("key") != (d or {}).get("choice"):
                add(f"{where}: choice does not name the chosen option's key")
            for o in opts:
                if not isinstance(o, dict) or not o.get("key") or not o.get("option"):
                    add(f"{where}: an option needs key and option")
                elif o.get("verdict") not in ("chosen", "rejected"):
                    add(f"{where}: option {o.get('key')} has no verdict")
                elif o["verdict"] == "rejected" and not o.get("why"):
                    add(f"{where}: rejected option {o.get('key')} has no why")
        for aid, alg in (block.get("algorithms") or {}).items():
            where = f"{item}.algorithms.{aid}"
            alg_ids.add(aid)
            if not re.fullmatch(rf"ALG-{code}-\d+", str(aid)):
                add(f"{where}: id is not ALG-{code}-n")
            steps = (alg or {}).get("steps") or []
            if not (alg or {}).get("name") or not steps:
                add(f"{where}: name or steps missing")
            for n, s in enumerate(steps, 1):
                if not str(s).startswith(f"{n}. "):
                    add(f"{where}: step {n} does not start with '{n}. '")
                    break
        proto = block.get("prototype") or {}
        for k in ("tool", "results_file", "status", "proved"):
            if k not in proto:
                add(f"{item}.prototype: {k} is missing")
        rf = str(proto.get("results_file", ""))
        if rf and not rf.startswith("results/platform_test/"):
            add(f"{item}.prototype: results_file is not under results/platform_test/")
        if proto.get("proved") and not (Path(repo) / rf).exists():
            add(f"{item}.prototype: proved is filled but {rf} does not exist")
        if final and not proto.get("proved"):
            add(f"{item}.prototype: nothing proved yet")
        for q in block.get("open_questions") or []:
            qid = (q or {}).get("id", "?")
            oq_ids.add(qid)
            if not re.fullmatch(rf"OQ-DP-{code}-\d+", str(qid)):
                add(f"{item}.open_questions.{qid}: id is not OQ-DP-{code}-n")
            for k in ("question", "recommended", "status"):
                if not (q or {}).get(k):
                    add(f"{item}.open_questions.{qid}: {k} is missing")
    for aid in sorted(acc_cited - set(acc_rows)):
        add(f"acceptance {aid} is cited by a requirement row but not defined")
    for aid in sorted(set(acc_rows) - acc_cited):
        add(f"acceptance {aid} is cited by no requirement row")

    # ---- names: everything the text mentions must exist
    schema = schema_tables()
    prop = proposed(changes)
    known_tables = set(schema) | set(prop["tables"]) | set(prop["views"])

    def column_exists(t, c):
        return c in schema.get(t, {}) or c in prop["tables"].get(t, set()) or c in prop["views"].get(t, {}).get("columns", set())

    sm = _yaml_cached(STATE_MACHINE)
    dims, trans = set(sm["dimensions"]), set(sm["transitions"])
    integrity = {x["id"] for x in sm["integrity"]}
    mids = metric_ids()
    for where, text in _walk_strings(pack):
        for t, c in re.findall(r"(?<![A-Za-z0-9_/.#-])([a-z][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\b", text):
            if t in known_tables and c not in NOT_A_COLUMN and c not in ITEM_PARTS and not column_exists(t, c):
                add(f"{where}: column {t}.{c} is in neither schema/tables nor schema/platform_changes.yaml")
        for mid in re.findall(r"\bM-[A-Z]+-\d{3}\b", text):
            if mid not in mids:
                add(f"{where}: metric {mid} is not in config/metrics.yaml")
        for tid in re.findall(r"(?<![A-Za-z0-9-])T\d{2}\b", text):
            if tid not in trans:
                add(f"{where}: transition {tid} is not in config/state_machine.yaml")
        for iid in re.findall(r"\b(?:SEG|TRN|CLK)-\d{2}\b", text):
            if iid not in integrity:
                add(f"{where}: integrity rule {iid} is not in config/state_machine.yaml")
        for ref, kind, pool in (
            (r"\bALG-(?:TN|QL|LN|PV)-\d+\b", "algorithm", alg_ids), (r"\bDD-(?:TN|QL|LN|PV)-\d+\b", "decision", dd_ids),
            (r"\bACC-DP-(?:TN|QL|LN|PV)-\d+\b", "acceptance row", set(acc_rows)), (r"\bOQ-DP-(?:TN|QL|LN|PV)-\d+\b", "open question", oq_ids),
        ):
            for x in re.findall(ref, text):
                if x not in pool:
                    add(f"{where}: {kind} {x} is cited but not defined")
        if re.search(r"(?<!\d)\d{9,}(?!\d)", text):
            add(f"{where}: a digit string of 9 or more (a real source id?) is in the public pack")
    for item in ITEMS:
        sch = (pack.get(item) or {}).get("schemas") or {}
        for t, spec in (sch.get("tables") or {}).items():
            if t not in known_tables:
                add(f"{item}.schemas.tables.{t}: not in schema/tables or schema/platform_changes.yaml")
                continue
            for c in (spec or {}).get("columns") or []:
                if not column_exists(t, c):
                    add(f"{item}.schemas.tables.{t}: column {c} is in neither schema/tables nor the change set")
            if (spec or {}).get("change") not in ("new", "changed", "kept"):
                add(f"{item}.schemas.tables.{t}: change is not new, changed or kept")
            if (spec or {}).get("change") == "new" and t in schema:
                add(f"{item}.schemas.tables.{t}: said to be new but exists in schema/tables")
        for v, spec in (sch.get("views") or {}).items():
            if v not in prop["views"]:
                add(f"{item}.schemas.views.{v}: not defined in schema/platform_changes.yaml")
                continue
            for c in (spec or {}).get("columns") or []:
                if c not in prop["views"][v]["columns"]:
                    add(f"{item}.schemas.views.{v}: column {c} is not in the change set's view")
        for d in sch.get("dimensions_read") or []:
            if d not in dims:
                add(f"{item}.schemas.dimensions_read: {d} is not a dimension of config/state_machine.yaml")
    for stage in ((pack.get("lineage") or {}).get("stage_graph") or {}).get("stages") or []:
        sid = (stage or {}).get("id", "?")
        for k in ("id", "reads", "writes", "lineage_class", "config", "code"):
            if k not in (stage or {}):
                add(f"lineage.stage_graph.{sid}: {k} is missing")
        for t in (stage or {}).get("writes") or []:
            if t not in known_tables:
                add(f"lineage.stage_graph.{sid}: writes {t}, which is in neither schema/tables nor the change set")
        for d in (stage or {}).get("dimensions") or []:
            if d not in dims:
                add(f"lineage.stage_graph.{sid}: dimension {d} is not in config/state_machine.yaml")
    problems.extend(_check_stage_graph(pack))

    # ---- change set: status lines, team-neutral audit, nothing MSU-relative added
    if changes is None:
        add("schema/platform_changes.yaml does not exist")
    else:
        problems.extend(_validate_changes(changes, schema))
    return problems


def _check_stage_graph(pack):
    out = []
    stages = ((pack.get("lineage") or {}).get("stage_graph") or {}).get("stages") or []
    by_id = {s.get("id"): s for s in stages if isinstance(s, dict)}
    writers = {}
    for s in by_id.values():
        for t in s.get("writes") or []:
            if t in writers:
                out.append(f"lineage.stage_graph: {t} is written by {writers[t]} and {s['id']}")
            writers[t] = s["id"]
    classes = set(((pack.get("lineage") or {}).get("lineage_classes") or {}))
    edges = {}
    for s in by_id.values():
        if s.get("lineage_class") not in classes:
            out.append(f"lineage.stage_graph.{s.get('id')}: lineage_class {s.get('lineage_class')!r} is not defined")
        ups = set()
        for r in s.get("reads") or []:
            t = r.get("table") if isinstance(r, dict) else r
            if t in writers:
                ups.add(writers[t])
            elif t not in ((pack.get("lineage") or {}).get("stage_graph") or {}).get("sources", []):
                out.append(f"lineage.stage_graph.{s.get('id')}: reads {t}, which no stage writes and is no source")
        edges[s.get("id")] = ups
    state = {}

    def visit(n, stack):
        if state.get(n) == 2:
            return
        if state.get(n) == 1:
            out.append("lineage.stage_graph: cycle " + " -> ".join(stack + [n]))
            return
        state[n] = 1
        for u in sorted(edges.get(n, ())):
            visit(u, stack + [n])
        state[n] = 2

    for n in sorted(edges):
        visit(n, [])
    return out


def _validate_changes(changes, schema):
    out = []
    add = out.append
    if not str(changes.get("status", "")).startswith("proposed"):
        add("platform_changes: status does not start with 'proposed'")
    NOT_APPLIED = "not applied"
    for section in ("new_tables", "column_additions", "views"):
        for name, spec in (changes.get(section) or {}).items():
            status = spec.get("status") if isinstance(spec, dict) else None
            if section == "column_additions":
                status = ((changes.get("column_additions_status") or {}).get(name))
            if not str(status or "").startswith(NOT_APPLIED):
                add(f"platform_changes.{section}.{name}: status does not start with '{NOT_APPLIED}'")
    tn = changes.get("team_neutral") or {}
    if not str(tn.get("status", "")).startswith(NOT_APPLIED):
        add(f"platform_changes.team_neutral: status does not start with '{NOT_APPLIED}'")

    # the audit is complete and not stale
    flagged = {(t, c): (kind, bad) for t, c, kind, bad in audit_msu_relative(schema)}
    disposed = {}
    for t, cols in (tn.get("audit") or {}).items():
        for c, d in (cols or {}).items():
            disposed[(t, c)] = d or {}
    for key in sorted(set(flagged) - set(disposed)):
        add(f"platform_changes.team_neutral.audit: {key[0]}.{key[1]} is flagged ({flagged[key][0]}) and has no disposition")
    for key in sorted(set(disposed) - set(flagged)):
        add(f"platform_changes.team_neutral.audit: {key[0]}.{key[1]} has a disposition but the audit no longer flags it")
    for (t, c), d in sorted(disposed.items()):
        where = f"platform_changes.team_neutral.audit.{t}.{c}"
        act = d.get("action")
        if act not in ("rename", "enum", "rename+enum", "drop", "keep", "false_hit"):
            add(f"{where}: action is not rename, enum, rename+enum, drop, keep or false_hit")
            continue
        if not d.get("why"):
            add(f"{where}: why is missing")
        kind = flagged.get((t, c), ("", ()))[0]
        if "rename" in act:
            news = [d.get("to")] if isinstance(d.get("to"), str) else (d.get("to") or [])
            if not news:
                add(f"{where}: rename needs to")
            for n in news:
                why = relative_problem(n)
                if why:
                    add(f"{where}: new name {n} {why}")
        if "enum" in act:
            vmap = d.get("values_map") or {}
            if not vmap:
                add(f"{where}: enum change needs values_map {{old: new}}")
            for old in flagged.get((t, c), ("", ()))[1]:
                if old not in vmap:
                    add(f"{where}: flagged enum value {old} has no new value in values_map")
            for v in vmap.values():
                if _NAME_RE.search(str(v)):
                    add(f"{where}: new enum value {v} is still team-relative")
        if act in ("rename", "drop") and "enum" in kind and "name" not in kind:
            add(f"{where}: the audit flags enum values, the disposition does not change them")
        if act == "enum" and "name" in kind:
            add(f"{where}: the audit flags the name, the disposition changes only the enum values")
        if act == "keep" and not d.get("row_relative"):
            add(f"{where}: keep needs row_relative: true (relative to the row's own team) and a definition fix")

    # nothing the change set adds is MSU-relative
    for t, spec in (changes.get("new_tables") or {}).items():
        why = relative_problem(t)
        if why:
            add(f"platform_changes.new_tables.{t}: table name {why}")
        for k in ("grain", "primary_key", "columns", "requirements"):
            if not (spec or {}).get(k):
                add(f"platform_changes.new_tables.{t}: {k} is missing")
        names = []
        for c in (spec or {}).get("columns") or []:
            name = c.get("column") if isinstance(c, dict) else None
            if not name or not c.get("type") or not c.get("definition"):
                add(f"platform_changes.new_tables.{t}: a column needs column, type and definition")
                continue
            names.append(name)
            why = relative_problem(name, row_relative=bool(c.get("row_relative")))
            if why:
                add(f"platform_changes.new_tables.{t}.{name}: {why}")
            for v in c.get("values") or []:
                if set(_tokens(v)) & set(ALWAYS_FORBIDDEN):
                    add(f"platform_changes.new_tables.{t}.{name}: enum value {v} names one programme")
        for k in (spec or {}).get("primary_key") or []:
            if k not in names:
                add(f"platform_changes.new_tables.{t}: primary key column {k} is not a column")
        if len(names) != len(set(names)):
            add(f"platform_changes.new_tables.{t}: a column is listed twice")
        if t in schema:
            add(f"platform_changes.new_tables.{t}: already exists in schema/tables")
    for t, entries in (changes.get("column_additions") or {}).items():
        if t not in schema:
            add(f"platform_changes.column_additions.{t}: no such table in schema/tables")
        for c in entries or []:
            name = c.get("column") if isinstance(c, dict) else None
            if not name or not c.get("type") or not c.get("definition"):
                add(f"platform_changes.column_additions.{t}: a column needs column, type and definition")
                continue
            if name in schema.get(t, {}):
                add(f"platform_changes.column_additions.{t}.{name}: the column already exists")
            why = relative_problem(name, row_relative=bool(c.get("row_relative")))
            if why:
                add(f"platform_changes.column_additions.{t}.{name}: {why}")
    for v, spec in (changes.get("views") or {}).items():
        layer = (spec or {}).get("layer")
        if layer not in ("base", "grain", "team_keyed", "focus", "catalogue"):
            add(f"platform_changes.views.{v}: layer is not base, grain, team_keyed, focus or catalogue")
        if layer == "focus" and "focus_team_id" not in ((spec or {}).get("parameters") or []):
            add(f"platform_changes.views.{v}: a focus view takes focus_team_id as a parameter")
        if (spec or {}).get("default_focus") not in (None, "none"):
            add(f"platform_changes.views.{v}: a focus view has no default focus team")
        for c in (spec or {}).get("columns") or []:
            name = c.get("column") if isinstance(c, dict) else c
            why = relative_problem(name, layer=layer if layer in ("team_keyed", "focus") else None,
                                   row_relative=isinstance(c, dict) and bool(c.get("row_relative")))
            if why:
                add(f"platform_changes.views.{v}.{name}: {why}")
    for where, text in _walk_strings(changes):
        if re.search(r"(?<!\d)\d{9,}(?!\d)", text):
            add(f"platform_changes{where}: a digit string of 9 or more is in the public change set")
    return out


def acceptance_counts(pack):
    out = {s: 0 for s in ACC_STATUS}
    for item in ITEMS:
        for a in ((pack.get(item) or {}).get("acceptance") or {}).values():
            if isinstance(a, dict) and a.get("status") in out:
                out[a["status"]] += 1
    return out


# --------------------------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="lint the pack and the change set (default action)")
    ap.add_argument("--final", action="store_true", help="with --check: a row still pending its prototype is a problem")
    ap.add_argument("--audit", action="store_true", help="print the MSU-relative audit of schema/tables")
    ap.add_argument("--games", action="store_true", help="print the game codes of the private play-by-play")
    a = ap.parse_args(argv)
    if a.audit:
        rows = audit_msu_relative()
        per = {}
        for t, c, kind, bad in rows:
            per.setdefault(t, []).append(f"{c} [{kind}{': ' + ','.join(bad) if bad else ''}]")
        for t, cols in per.items():
            print(f"{t}: {len(cols)}  " + "; ".join(cols))
        print(f"{len(rows)} flagged columns in {len(per)} of {len(schema_tables())} tables")
        return 0
    if a.games:
        games = discover_games()
        if not games:
            print("no private play-by-play found (set MSU_ALPHA_PRIVATE or mount ~/MSU-Alpha-3-private)")
            return 0
        print(" ".join(f"{g.code}:{g.season_label}:{len(g.pulls)}" for g in games))
        print(f"{len(games)} games, {sum(len(g.pulls) for g in games)} pulls (code:season:pulls)")
        return 0
    try:
        pack, changes = load_pack(), load_changes()
    except (OSError, PackError, yaml.YAMLError) as e:
        print("FAIL", " ".join(str(e).split()))
        return 2
    problems = validate(pack, changes, final=a.final)
    for p in problems:
        print("FAIL", p)
    n_req = sum(len((pack.get(i) or {}).get("requirements") or []) for i in ITEMS)
    counts = acceptance_counts(pack)
    print(f"{n_req} requirement rows, {sum(counts.values())} acceptance rows "
          f"({', '.join(f'{v} {k}' for k, v in counts.items())}), {len(params(pack)) - 1} params, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
