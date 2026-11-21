"""Live-state pack: loader, profile resolution and lint (config/live_state/*.yaml).

Usage:
  python tools/specgen/live_state/lslib.py --check                      # everything; index entries without a record are problems
  python tools/specgen/live_state/lslib.py --check config/live_state/fields_play.yaml   # one fields file on its own

The pack is core.yaml (conventions, grades, sensors, rules, profiles, limits, field_index, inventory) plus three fields
files. A field names one profile; the profile gives the default sources, update, dropout, conflict and latency. A
field's own `sources`, `dropout` or `conflict` list REPLACES the profile's list; `dropout_extra` and `conflict_extra`
are APPENDED to it. Every numeric limit is a param {value, unit, why, evidence}.

What the lint checks (validate):
  core    params complete, evidence tags, mirrors of other configs, measured_key against measured_sensors.json,
          sensor delay models and health fields, profile dropout rules, the index (ids, groups, dimensions) and the
          inventory (columns of state_frame / state_second, R-SR rows, rows of the 19 Oct page).
  field   id / group / profile / file / dimension equal the index; required keys; none_value; lands_in columns exist
          and include the inventory's columns; sensors, rules, grades, transitions, invariants and log targets exist;
          grade paths move down; limits equal their params; timing is complete and ordered; derived inputs exist, form
          no cycle and are not slower than the field (timing.driven_by names the inputs the timing block is written
          for; default: all of them); the R-SR rows of the inventory are cited.
  whole   (require_all) every index entry has a record, every Shall row R-SR-01..20 is cited, and - once the reference
          code exists - every param is read by it or listed under production_only_params.
  rules   a dropout rule has only known keys and its steps can be timed (conventions.grade_path_timing, step_at);
          max_dwell_by_value and computed_from name existing things.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
PACK_DIR = REPO / "config" / "live_state"
CORE = PACK_DIR / "core.yaml"
FIELD_FILES = ["fields_scoreboard", "fields_play", "fields_meta"]
STATE_MACHINE = REPO / "config" / "state_machine.yaml"
INVARIANTS = REPO / "config" / "invariants.yaml"
SCHEMA_DIR = REPO / "schema" / "tables"
CHANGES = REPO / "schema" / "live_state_changes.yaml"
MEASURED = REPO / "results" / "live_state_test" / "measured_sensors.json"
CODE_DIR = Path(__file__).resolve().parent
REFERENCE_CODE = ["fuse.py", "harness.py", "sensors_sim.py"]  # the files that must read every param (once fuse.py exists)

STORED = {"key", "segment", "clock_map", "obs", "derived", "fixed"}
UPDATE_WORDS = {"continuous", "per_frame", "on_input_change", "all", "per field"}  # "per field" = a profile leaves it open
NONE_VALUES = {"off", "none", "unknown"}
ROLES = ("value", "confirm", "timing", "fallback")
NO_WINNER = {"neither", "n/a"}
INVENTORY_TABLES = ("state_frame", "state_second")
REQUIRED = ["id", "group", "name", "type", "unit", "domain", "none_value", "stored", "lands_in", "requirements",
            "profile", "consumers"]
SHOULD_SR = (12, 19)  # Should rows of the live requirements; every other R-SR-01..20 is a Shall row
SHALL_SR = [f"R-SR-{n:02d}" for n in range(1, 21) if n not in SHOULD_SR]
GROUP_CODE = {"keys": "KEY", "time": "TIME", "score": "SCORE", "counts": "COUNT", "possession_ball": "POSS",
              "personnel": "PERS", "tactics": "TAC", "situation": "SIT", "observability": "OBS", "fixed": "FIX"}
PARAM_KEYS = ("value", "unit", "why", "evidence")
DROPOUT_KEYS = {"when", "rule", "grade_path", "limits", "on_return", "evidence", "next_value", "step_at", "note"}
ON_RETURN = "on_return"  # a step that happens when the condition of the rule ends
LIVE_DOC_INVARIANTS = {f"R-IV-{n:02d}" for n in range(17, 50)}  # in the live requirements; config/invariants.yaml names them new-IV-NN


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that refuses a mapping with the same key twice (plain YAML keeps the last one silently)."""


def _unique_mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise ValueError(f"key {key!r} is written twice (line {key_node.start_mark.line + 1})")
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _unique_mapping)


def load_yaml_strict(path):
    try:
        return yaml.load(Path(path).read_text(), Loader=_UniqueKeyLoader)
    except ValueError as e:
        raise ValueError(f"{Path(path).name}: {e}") from None


def load_core(path=CORE):
    return load_yaml_strict(path)


def load_fields(files=None):
    """-> {field_key: record}, each record tagged with _file (the stem of its fields file)."""
    out = {}
    for stem in (files or FIELD_FILES):
        if str(stem).endswith(".yaml"):
            p = Path(stem)
            if not p.exists():  # a path given relative to the repo root, whatever the working directory
                p = REPO / stem
            if not p.exists():
                raise FileNotFoundError(f"fields file not found: {stem}")
        else:
            p = PACK_DIR / f"{stem}.yaml"
            if not p.exists():  # a fields file of the pack that is not written yet
                continue
        doc = load_yaml_strict(p) or {}
        for key, rec in (doc.get("fields") or {}).items():
            if key in out:
                raise ValueError(f"field {key} is written twice ({out[key]['_file']} and {p.stem})")
            rec = dict(rec or {})
            rec["_file"] = p.stem
            out[key] = rec
    return out


def is_param(o):
    return isinstance(o, dict) and "value" in o and any(k in o for k in ("unit", "why", "evidence"))


def params(core, fields=None):
    """Flat {name: param}. Names are unique across the pack; max_dwell entries are named max_dwell.<state>."""
    out = {}

    def take(name, p, where):
        if name in out:
            raise ValueError(f"parameter {name} defined twice ({out[name]['_where']} and {where})")
        out[name] = dict(p, _where=where)
    for sname, s in core["sensors"].items():
        for k, p in (s.get("params") or {}).items():
            take(k, p, f"sensors.{sname}")
    for pname, pr in core["profiles"].items():
        for k, p in (pr.get("params") or {}).items():
            take(k, p, f"profiles.{pname}")
    for k, p in core["max_dwell"].items():
        if is_param(p):
            take(f"max_dwell.{k}", p, "max_dwell")
    for k, p in core["latency_budget"]["end_to_end"].items():
        take(k, p, "latency_budget.end_to_end")
    for k, p in core["harness"]["params"].items():
        take(k, p, "harness")
    for fkey, rec in (fields or {}).items():
        for k, p in (rec.get("params") or {}).items():
            take(k, p, f"field {fkey}")
    return out


def P(name, core=None, fields=None):
    return params(core or load_core(), fields)[name]["value"]


def resolve(core, fields):
    """Full per-field records: profile defaults, overlaid by the field."""
    out = {}
    for key, rec in fields.items():
        prof = core["profiles"].get(rec.get("profile"), {})
        full = {"sources": prof.get("sources", []), "update": prof.get("update", {}), "dropout": prof.get("dropout", []),
                "conflict": prof.get("conflict", []), "timing": prof.get("latency", {})}
        for k, v in rec.items():
            if k in ("dropout_extra", "conflict_extra"):
                continue
            if k == "update":
                full["update"] = {**full["update"], **(v or {})}
            elif k == "timing":
                full["timing"] = {**full["timing"], **(v or {})}
            else:
                full[k] = v
        full["dropout"] = list(full["dropout"]) + list(rec.get("dropout_extra") or [])
        full["conflict"] = list(full["conflict"]) + list(rec.get("conflict_extra") or [])
        out[key] = full
    return out


# ---------------------------------------------------------------------------------------------------------- helpers
_SCHEMA_CACHE = {}
_YAML_CACHE = {}


def _schema_columns():
    """{table: list of column names in file order} from schema/tables; read once per process (104 files)."""
    if _SCHEMA_CACHE:
        return _SCHEMA_CACHE
    for p in SCHEMA_DIR.glob("*.yaml"):
        try:
            d = yaml.safe_load(p.read_text()) or {}
        except yaml.YAMLError:
            continue
        c = d.get("columns") or []
        _SCHEMA_CACHE[p.stem] = list(c) if isinstance(c, dict) else [x.get("name") for x in c if isinstance(x, dict)]
    return _SCHEMA_CACHE


def _yaml(path):
    path = Path(path)
    if path not in _YAML_CACHE:
        _YAML_CACHE[path] = json.loads(path.read_text()) if path.suffix == ".json" else yaml.safe_load(path.read_text())
    return _YAML_CACHE[path]


def _state_machine():
    return _yaml(STATE_MACHINE)


def dig(obj, dotted):
    """Walk a dotted key. In a list a number is an index and a name picks the item whose id (or key=value) matches."""
    for seg in str(dotted).split("."):
        if isinstance(obj, list):
            if seg.isdigit():
                obj = obj[int(seg)]
            else:
                k, _, v = seg.partition("=") if "=" in seg else ("id", "", seg)
                obj = next(x for x in obj if isinstance(x, dict) and str(x.get(k)) == v)
        else:
            obj = obj[seg]
    return obj


def _proposed_columns():
    """table.column names of schema/live_state_changes.yaml (None while the file does not exist).
    Accepts the layout of schema/named_spots_changes.yaml (column_additions: {table: [{column: name}]}) and any
    table.column written out in the text."""
    if not CHANGES.exists():
        return None
    text = CHANGES.read_text()
    out = set(re.findall(r"\b([a-z_0-9]+\.[a-z_0-9]+)\b", text))
    try:
        doc = yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return out
    for table, cols in (doc.get("column_additions") or {}).items():
        for c in cols or []:
            name = c.get("column") or c.get("name") if isinstance(c, dict) else c
            if name:
                out.add(f"{table}.{name}")
    for table in (doc.get("new_tables") or {}):
        cols = (doc["new_tables"][table] or {}).get("columns") or []
        for c in cols:
            name = c.get("column") or c.get("name") if isinstance(c, dict) else c
            if name:
                out.add(f"{table}.{name}")
    return out


def invariant_ids():
    """Ids a field may name under `invariants`."""
    ids = {x["id"] for x in _yaml(INVARIANTS)["invariants"]}
    ids |= {x["id"] for x in _state_machine()["integrity"]}
    return ids | LIVE_DOC_INVARIANTS


def evidence_ok(text, core):
    tags = (core.get("conventions", {}).get("evidence_tags") or {}).get("tags") or {}
    return isinstance(text, str) and any(text.startswith(f"{t}:") for t in tags)


def unread_params(core, fields=None, code_files=None):
    """Params that no reference-code file reads as P["name"], prm["name"] or P("name"), and that the generic machine
    of fuse.py does not read from a record either (machine_params). None while fuse.py is absent."""
    files = [CODE_DIR / f for f in (code_files or REFERENCE_CODE)]
    if code_files is None and not (CODE_DIR / "fuse.py").exists():
        return None
    code = "\n".join(p.read_text() for p in files if p.exists())
    used = set(re.findall(r"""(?:prm|P)[\[(]\s*["']([A-Za-z0-9_.]+)["']""", code))
    if "lslib.step_ages(" in code and "def dwell(" in code:   # the generic machine reads rule limits and dwell bounds by name
        used |= machine_params(core, fields)
    return sorted(set(params(core, fields)) - used)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def path_steps(grade_path):
    """(start grades, later grades). confirmed, observed at the head of a path is one start, not a step."""
    gp = list(grade_path or [])
    n = 2 if gp[:2] == ["confirmed", "observed"] else 1
    return gp[:n], gp[n:]


def step_ages(d, allp):
    """Ages (s since the condition started) at which a dropout rule moves one grade down; ON_RETURN for a step taken
    when the condition ends. core.yaml conventions.grade_path_timing. Raises ValueError when the rule cannot be read."""
    _, later = path_steps(d.get("grade_path"))
    limits = d.get("limits") or {}
    if "step_at" in d:
        out = []
        for s in d["step_at"]:
            if s == ON_RETURN or s == 0:
                out.append(s)
            elif s in limits and s in allp and allp[s].get("unit") == "s":
                out.append(float(allp[s]["value"]))
            else:
                raise ValueError(f"step_at entry {s!r} must be 0, {ON_RETURN} or a limit of the rule whose unit is s")
        if len(out) != len(later):
            raise ValueError(f"step_at has {len(out)} entries for {len(later)} steps")
    else:
        times = [float(allp[k]["value"]) for k in limits if k in allp and allp[k].get("unit") == "s"]
        if not later:
            return []
        if len(times) > len(later):
            raise ValueError(f"{len(times)} time limits for {len(later)} steps: write step_at")
        out = [0] * (len(later) - len(times)) + times
    nums = [x for x in out if x != ON_RETURN]
    if nums != sorted(nums):
        raise ValueError(f"step ages {out} are not in rising order")
    return out


def step_params(d, allp):
    """Names of the limits of a dropout rule that are step ages (what fuse.GradeTrack reads through step_ages)."""
    limits = d.get("limits") or {}
    if "step_at" in d:
        return [s for s in d["step_at"] if s in limits]
    _, later = path_steps(d.get("grade_path"))
    return [k for k in limits if k in allp and allp[k].get("unit") == "s"] if later else []


def machine_params(core, fields):
    """Params the generic machine of fuse.py reads by name from the records, not by a literal in the code: the step
    ages of every dropout rule (GradeTrack) and the max-dwell bounds a field names (Spec.dwell)."""
    allp, out = params(core, fields), set()
    for rec in resolve(core, fields or {}).values():
        for d in rec.get("dropout") or []:
            out.update(step_params(d, allp))
        for entry in [rec.get("max_dwell")] + list((rec.get("max_dwell_by_value") or {}).values()):
            if isinstance(entry, str):
                out.add(f"max_dwell.{entry}")
    for prof in core["profiles"].values():
        for d in prof.get("dropout") or []:
            out.update(step_params(d, allp))
    return out & set(allp)


def _check_dropout(where, d, core, allp, rank, problems):
    for k in set(d) - DROPOUT_KEYS:
        problems.append(f"{where}: unknown key {k!r} (a `when` text with a comma must be quoted)")
    try:
        step_ages(d, allp)
    except ValueError as e:
        problems.append(f"{where}: {e}")
    ladder, rules = core["grades"]["ladder"], set(core["rules"])
    for k in ("when", "rule", "grade_path", "on_return", "evidence"):
        if d.get(k) in (None, "", []):
            problems.append(f"{where}: missing {k}")
    if not isinstance(d.get("limits"), dict):
        problems.append(f"{where}: limits missing (write limits: {{}} when the rule has none)")
    if d.get("evidence") and not evidence_ok(d["evidence"], core):
        problems.append(f"{where}: evidence must start with a tag of conventions.evidence_tags")
    for r in (d.get("rule"), d.get("on_return")):
        if r is not None and r not in rules:
            problems.append(f"{where}: unknown rule {r!r}")
    gp = d.get("grade_path") or []
    if any(g not in rank for g in gp):
        problems.append(f"{where}: grade_path {gp} has a grade outside the ladder {ladder}")
    elif any(rank[a] >= rank[b] for a, b in zip(gp, gp[1:])):
        problems.append(f"{where}: grade_path {gp} does not move strictly down the ladder")
    for lim, val in (d.get("limits") or {}).items() if isinstance(d.get("limits"), dict) else []:
        if lim not in allp:
            problems.append(f"{where}: limit {lim} is not a param of the pack")
        elif not _num(val) or not _num(allp[lim]["value"]) or abs(float(val) - float(allp[lim]["value"])) > 1e-9:
            problems.append(f"{where}: limit {lim} = {val} differs from the param value {allp[lim]['value']}")


def _check_timing(where, t, sensors, core, problems, need_evidence=True, sources=None):
    pv, cf = (t.get("provisional") or {}), (t.get("confirmed") or {})
    for nm, blk in (("provisional", pv), ("confirmed", cf)):
        for k in ("by", "p50_s", "p95_s"):
            if k not in blk:
                problems.append(f"{where}: timing.{nm}.{k} missing")
        if "by" in blk and blk["by"] not in sensors and blk["by"] != "inputs":
            problems.append(f"{where}: timing.{nm}.by {blk['by']!r} is neither a sensor nor 'inputs'")
        elif sources is not None and blk.get("by") in sensors and blk["by"] not in sources:
            problems.append(f"{where}: timing.{nm}.by {blk['by']} is not one of the field's sources")
        for k in ("p50_s", "p95_s"):
            if k in blk and (not _num(blk[k]) or blk[k] < 0):
                problems.append(f"{where}: timing.{nm}.{k} must be a number >= 0")
        if _num(blk.get("p50_s")) and _num(blk.get("p95_s")) and blk["p50_s"] > blk["p95_s"]:
            problems.append(f"{where}: timing.{nm} p50 above p95")
    for k in ("p50_s", "p95_s"):
        if _num(pv.get(k)) and _num(cf.get(k)) and pv[k] > cf[k]:
            problems.append(f"{where}: provisional {k[:3]} ({pv[k]}) is later than confirmed {k[:3]} ({cf[k]})")
    if need_evidence:
        if not t.get("evidence"):
            problems.append(f"{where}: timing.evidence missing (measured: where | assumed: why)")
        elif not evidence_ok(t["evidence"], core):
            problems.append(f"{where}: timing.evidence must start with a tag of conventions.evidence_tags")


def _check_conflict(where, c, sensors, logs, problems):
    for s in c.get("between") or []:
        if s not in sensors:
            problems.append(f"{where}: conflict names unknown sensor {s!r}")
    for k in ("value_winner", "timing_winner", "log_to"):
        if k not in c:
            problems.append(f"{where}: conflict {c.get('between')} missing {k}")
    for k in ("value_winner", "timing_winner"):
        if k in c and c[k] not in sensors and c[k] not in NO_WINNER:
            problems.append(f"{where}: conflict {k} {c[k]!r} is not a sensor (or neither / n/a)")
    if "log_to" in c and c["log_to"] not in logs:
        problems.append(f"{where}: conflict log_to {c['log_to']!r} is not listed under reconciliation.logging")


def _validate_core(core, allp, problems):
    """Checks that need no field record."""
    sm = _state_machine()
    dims, trans = set(sm["dimensions"]), set(sm["transitions"])
    rank = {g: i for i, g in enumerate(core["grades"]["ladder"])}
    sensors, profiles, index = set(core["sensors"]), set(core["profiles"]), core["field_index"]
    logs = set(core["reconciliation"]["logging"])
    schema = _schema_columns()

    # params: complete, tagged, linked
    for name, p in allp.items():
        for k in PARAM_KEYS:
            if p.get(k) in (None, ""):
                problems.append(f"param {name} ({p['_where']}): missing {k}")
        if p.get("evidence") and not evidence_ok(p["evidence"], core):
            problems.append(f"param {name}: evidence must start with a tag of conventions.evidence_tags")
        if p.get("mirrors"):
            try:
                rel, _, key = str(p["mirrors"]).partition(":")
                other = dig(_yaml(REPO / rel), key)
            except (OSError, KeyError, IndexError, StopIteration, TypeError):
                problems.append(f"param {name}: mirrors {p['mirrors']!r} cannot be read")
            else:
                if other != p["value"]:
                    problems.append(f"param {name}: value {p['value']} differs from {p['mirrors']} = {other}")
        if p.get("measured_key") and MEASURED.exists():
            try:
                m = dig(_yaml(MEASURED), p["measured_key"])
            except (KeyError, IndexError, StopIteration, TypeError):
                problems.append(f"param {name}: measured_key {p['measured_key']!r} is not in {MEASURED.name}")
            else:
                want = round(float(m), int(p.get("measured_round", 6))) + float(p.get("measured_plus", 0))
                if not _num(p["value"]) or abs(want - float(p["value"])) > 1e-9:
                    problems.append(f"param {name}: value {p['value']} differs from the measurement {want} ({p['measured_key']})")
    for k, e in core["max_dwell"].items():
        if is_param(e) and not e.get("rule"):
            problems.append(f"max_dwell {k}: missing rule (a rule number or 'physics')")
        if is_param(e) and e.get("counts_in") not in ("real", "game_clock"):
            problems.append(f"max_dwell {k}: counts_in must be real or game_clock (the time the bound runs in)")

    # sensors: delay model and health fields
    for sname, s in core["sensors"].items():
        for k in ("gives", "resolution", "availability", "delay", "failure_modes", "health"):
            if not s.get(k):
                problems.append(f"sensor {sname}: missing {k}")
        d = s.get("delay") or {}
        vals = []
        for q in ("p50", "p95"):
            if d.get(q) in (None, ""):
                problems.append(f"sensor {sname}: delay.{q} missing (a param name or n/a)")
            elif d[q] != "n/a":
                if d[q] not in allp:
                    problems.append(f"sensor {sname}: delay.{q} {d[q]!r} is not a param of the pack")
                else:
                    vals.append(allp[d[q]]["value"])
        if len(vals) == 2 and vals[0] > vals[1]:
            problems.append(f"sensor {sname}: delay p50 above p95")
        h = s.get("health") or {}
        for k in ("signal", "down_when", "up_when"):
            if not h.get(k):
                problems.append(f"sensor {sname}: health.{k} missing")
        if not isinstance(h.get("fields"), list):
            problems.append(f"sensor {sname}: health.fields missing (the fields that carry the health signal; [] with a note when none)")
        for f in h.get("fields") or []:
            if f not in index:
                problems.append(f"sensor {sname}: health field {f!r} is not in the field index")
        if isinstance(h.get("fields"), list) and not h["fields"] and not h.get("note"):
            problems.append(f"sensor {sname}: health.fields is empty and no note says why")

    # profiles
    for pname, prof in core["profiles"].items():
        where = f"profile {pname}"
        for s in prof.get("sources") or []:
            if s.get("sensor") not in sensors:
                problems.append(f"{where}: unknown sensor {s.get('sensor')!r}")
            if s.get("role") not in ROLES:
                problems.append(f"{where}: source role {s.get('role')!r} must be one of {ROLES}")
        cb = (prof.get("update") or {}).get("changed_by")
        for c in cb if isinstance(cb, list) else [cb]:
            if c not in trans and c not in UPDATE_WORDS:
                problems.append(f"{where}: update.changed_by {c!r} is not a transition of config/state_machine.yaml")
        if not prof.get("dropout"):
            problems.append(f"{where}: no dropout rule")
        for d in prof.get("dropout") or []:
            _check_dropout(f"{where}: dropout '{d.get('when')}'", d, core, allp, rank, problems)
        for c in prof.get("conflict") or []:
            _check_conflict(where, c, sensors, logs, problems)
        _check_timing(where, prof.get("latency") or {}, sensors, core, problems,
                      sources={s.get("sensor") for s in prof.get("sources") or []})

    # degradation levels and reconciliation refer to existing things
    for k, w in (core["reconciliation"].get("windows") or {}).items():
        if k != "reset_rule" and w not in allp:
            problems.append(f"reconciliation.windows.{k}: {w!r} is not a param of the pack")
    for s in core["reconciliation"]["value_authority"] + core["reconciliation"]["timing_authority"]:
        if s not in sensors and s != "arena_scoreboard":
            problems.append(f"reconciliation: authority names unknown sensor {s!r}")

    # index
    seen_ids, dim_owner = {}, {}
    for key, ix in index.items():
        code = GROUP_CODE.get(ix.get("group"))
        if code is None:
            problems.append(f"index {key}: unknown group {ix.get('group')}")
            continue
        if not re.fullmatch(rf"LS-{code}-\d\d", str(ix.get("id"))):
            problems.append(f"index {key}: id {ix.get('id')} does not match group {ix['group']} (LS-{code}-NN)")
        if ix.get("id") in seen_ids:
            problems.append(f"index {key}: id {ix.get('id')} already used by {seen_ids[ix.get('id')]}")
        seen_ids[ix.get("id")] = key
        if ix.get("profile") not in profiles:
            problems.append(f"index {key}: unknown profile {ix.get('profile')}")
        if ix.get("file") not in FIELD_FILES:
            problems.append(f"index {key}: unknown owner file {ix.get('file')}")
        if ix.get("dimension") is not None:
            if ix["dimension"] not in dims:
                problems.append(f"index {key}: dimension {ix['dimension']} is not in config/state_machine.yaml")
            dim_owner.setdefault(ix["dimension"], []).append(key)
    for code in set(GROUP_CODE.values()):
        nums = sorted(int(str(i)[-2:]) for i in seen_ids if str(i).startswith(f"LS-{code}-"))
        if nums != list(range(1, len(nums) + 1)):
            problems.append(f"ids of group {code} are not gap-free from 01: {nums}")
    for d in sorted(dims):
        if len(dim_owner.get(d, [])) != 1:
            problems.append(f"state-machine dimension {d} is carried by {len(dim_owner.get(d, []))} index entries (must be exactly 1)")

    # inventory (ACC-LS-2)
    inv, oos = core.get("inventory") or {}, core.get("out_of_scope") or {}
    covered = set()
    for f, cols in (inv.get("columns") or {}).items():
        if f not in index:
            problems.append(f"inventory.columns: {f!r} is not in the field index")
        for c in cols or []:
            t, _, col = str(c).partition(".")
            if t not in INVENTORY_TABLES or col not in schema.get(t, []):
                problems.append(f"inventory.columns {f}: {c} is not a column of {' / '.join(INVENTORY_TABLES)}")
            covered.add(c)
    for t in INVENTORY_TABLES:
        for col in schema.get(t, []):
            name = f"{t}.{col}"
            if name not in covered and name not in oos:
                problems.append(f"inventory: column {name} maps to no field and is not in out_of_scope")
            if name in covered and name in oos:
                problems.append(f"inventory: column {name} is both under a field and in out_of_scope")
    for k in oos:
        if "." in k and k.split(".")[0] in INVENTORY_TABLES and k.split(".", 1)[1] not in schema.get(k.split(".")[0], []):
            problems.append(f"out_of_scope: {k} is not a column of schema/tables")
    reqs = inv.get("requirements") or {}
    for n in range(1, 21):
        rid = f"R-SR-{n:02d}"
        if rid not in reqs:
            problems.append(f"inventory.requirements: {rid} is missing")
        elif not reqs[rid] and rid in SHALL_SR:
            problems.append(f"inventory.requirements: Shall row {rid} maps to no field")
        elif not reqs[rid] and not any(rid in str(v) for v in oos.values()):
            problems.append(f"inventory.requirements: {rid} maps to no field and no out_of_scope reason names it")
        for f in reqs.get(rid) or []:
            if f not in index:
                problems.append(f"inventory.requirements {rid}: {f!r} is not in the field index")
    on_page = set()
    rows = inv.get("page_rows") or {}
    for g in GROUP_CODE:
        if not rows.get(g):
            problems.append(f"inventory.page_rows: group {g} of the 19 Oct page is missing")
    for g, table in rows.items():
        for row, fs in (table or {}).items():
            if not fs:
                problems.append(f"inventory.page_rows {g}: row {row!r} maps to no field")
            for f in fs or []:
                if f not in index:
                    problems.append(f"inventory.page_rows {g}: {f!r} is not in the field index")
                elif index[f].get("group") != g:
                    problems.append(f"inventory.page_rows {g}: {f} is in group {index[f].get('group')} of the index")
                on_page.add(f)
    added = inv.get("added_by_this_pack") or {}
    for f in index:
        if (f in on_page) == (f in added):
            problems.append(f"inventory: field {f} must be either on the 19 Oct page (page_rows) or under added_by_this_pack")
    for f in added:
        if f not in index:
            problems.append(f"inventory.added_by_this_pack: {f!r} is not in the field index")


def validate(core=None, fields=None, require_all=True):
    """-> list of problems (strings). Empty list = the pack passes the lint."""
    core = core or load_core()
    fields = load_fields() if fields is None else fields
    problems = []
    sm = _state_machine()
    dims, trans = set(sm["dimensions"]), set(sm["transitions"])
    rank = {g: i for i, g in enumerate(core["grades"]["ladder"])}
    sensors, profiles = set(core["sensors"]), set(core["profiles"])
    index = core["field_index"]
    logs = set(core["reconciliation"]["logging"])
    schema = {t: set(c) for t, c in _schema_columns().items()}
    proposed = _proposed_columns()
    inv = core.get("inventory") or {}
    inv_ids = invariant_ids()

    try:
        allp = params(core, fields)
    except ValueError as e:
        return [str(e)]
    _validate_core(core, allp, problems)

    full = resolve(core, fields)
    dim_used = {}
    for key, rec in full.items():
        ix = index.get(key)
        if ix is None:
            problems.append(f"{key}: not in core.yaml field_index")
            continue
        for k in ("id", "group", "profile"):
            if rec.get(k) != ix.get(k):
                problems.append(f"{key}: {k} {rec.get(k)!r} differs from the index ({ix.get(k)!r})")
        if rec.get("profile") not in profiles:
            problems.append(f"{key}: unknown profile {rec.get('profile')!r}")
        if rec.get("_file") != ix.get("file"):
            problems.append(f"{key}: written in {rec.get('_file')} but the index gives {ix.get('file')}")
        for k in REQUIRED:
            if k not in rec or rec[k] in (None, ""):
                problems.append(f"{key}: missing {k}")
        if rec.get("none_value") is not None and rec["none_value"] not in NONE_VALUES:
            problems.append(f"{key}: none_value {rec['none_value']!r} must be one of {sorted(NONE_VALUES)}")
        if rec.get("stored") not in STORED:
            problems.append(f"{key}: stored {rec.get('stored')!r} not in {sorted(STORED)}")
        if not rec.get("consumers"):
            problems.append(f"{key}: consumers is empty")
        for c in rec.get("freshness_needed_s") or {}:
            if c not in (rec.get("consumers") or []):
                problems.append(f"{key}: freshness_needed_s names {c!r}, which is not a consumer of the field")
        dim = rec.get("dimension")
        if dim is not None and dim not in dims:
            problems.append(f"{key}: dimension {dim} is not in config/state_machine.yaml")
        if dim != ix.get("dimension"):
            problems.append(f"{key}: dimension {dim!r} differs from the index ({ix.get('dimension')!r})")
        if dim is not None:
            dim_used.setdefault(dim, []).append(key)
        # where it lands
        for target in rec.get("lands_in") or []:
            m = re.fullmatch(r"([a-z_0-9]+)\.([a-z_0-9]+)", str(target))
            if m:
                if m.group(2) not in schema.get(m.group(1), set()):
                    problems.append(f"{key}: lands_in {target} is not a column of schema/tables (move it to lands_in_proposed)")
            elif str(target).startswith("state_segments:"):
                if str(target).split(":", 1)[1] not in dims:
                    problems.append(f"{key}: lands_in {target} names no state-machine dimension")
            elif str(target) not in ("clock_map:game", "clock_map:shot", "view"):
                problems.append(f"{key}: lands_in {target!r} must be table.column, state_segments:<dimension>, clock_map:game|shot or view")
        for target in rec.get("lands_in_proposed") or []:
            m = re.fullmatch(r"([a-z_0-9]+)\.([a-z_0-9]+)", str(target))
            if not m:
                problems.append(f"{key}: lands_in_proposed {target!r} must be table.column")
            elif m.group(2) in schema.get(m.group(1), set()):
                problems.append(f"{key}: lands_in_proposed {target} already exists in schema/tables (move it to lands_in)")
            elif proposed is not None and target not in proposed:
                problems.append(f"{key}: lands_in_proposed {target} is not in schema/live_state_changes.yaml")
        for col in (inv.get("columns") or {}).get(key) or []:
            if col not in (rec.get("lands_in") or []):
                problems.append(f"{key}: lands_in lacks {col} (core.yaml inventory.columns gives it to this field)")
        if dim in dims:
            sm_stored = sm["dimensions"][dim].get("stored")
            if rec.get("stored") != sm_stored:
                problems.append(f"{key}: stored {rec.get('stored')!r} differs from the state machine ({sm_stored!r} for dimension {dim})")
            home = {"segment": f"state_segments:{dim}", "clock_map": "clock_map:" + dim.split("_")[0]}.get(sm_stored)
            if home and home not in (rec.get("lands_in") or []):
                problems.append(f"{key}: lands_in lacks {home} (where the state machine stores dimension {dim})")
        # requirements
        cited = set(rec.get("requirements") or [])
        cited |= {re.sub(r"[a-c]$", "", x) for x in cited}
        for rid, fs in (inv.get("requirements") or {}).items():
            if key in (fs or []) and rid not in cited:
                problems.append(f"{key}: requirements lacks {rid} (core.yaml inventory.requirements gives it to this field)")
        for inv_id in rec.get("invariants") or []:
            if inv_id not in inv_ids:
                problems.append(f"{key}: invariant {inv_id!r} is not an id of config/invariants.yaml or of the state-machine integrity rules")
        # sources
        for s in rec.get("sources") or []:
            if s.get("sensor") not in sensors:
                problems.append(f"{key}: unknown sensor {s.get('sensor')!r}")
            if s.get("role") not in ROLES:
                problems.append(f"{key}: source role {s.get('role')!r} must be value, confirm, timing or fallback")
            for m in s.get("modes") or []:
                if m not in core["conventions"]["modes"]:
                    problems.append(f"{key}: source mode {m!r} is not a mode of conventions.modes")
        if not rec.get("sources") and rec.get("profile") != "derived":
            problems.append(f"{key}: no sources")
        # update
        upd = rec.get("update") or {}
        cb = upd.get("changed_by")
        for c in cb if isinstance(cb, list) else [cb]:
            if c in (None, "per field"):
                problems.append(f"{key}: update.changed_by not set (the profile leaves it to the field)")
            elif c not in trans and c not in UPDATE_WORDS:
                problems.append(f"{key}: update.changed_by {c!r} is not a transition of config/state_machine.yaml")
        sm_cb = (sm["dimensions"].get(dim) or {}).get("changed_by") if dim in dims else None
        if isinstance(sm_cb, list):
            for c in sm_cb:
                if c not in (cb if isinstance(cb, list) else [cb]):
                    problems.append(f"{key}: update.changed_by lacks {c}, which config/state_machine.yaml lists for dimension {dim}")
        elif sm_cb == "all" and cb != "all":
            problems.append(f"{key}: update.changed_by must be 'all' (config/state_machine.yaml: every transition changes dimension {dim})")
        for c in upd.get("steps_by") or []:
            if c not in trans:
                problems.append(f"{key}: update.steps_by {c!r} is not a transition of config/state_machine.yaml")
        if "event_instant" not in upd and rec.get("profile") in ("counter", "status", "clock", "roster", "derived"):
            problems.append(f"{key}: update.event_instant missing (the exact definition of the true instant)")
        # timing
        _check_timing(key, rec.get("timing") or {}, sensors, core, problems, need_evidence=rec.get("profile") != "fixed",
                      sources={s.get("sensor") for s in rec.get("sources") or []})
        # dropout
        if not rec.get("dropout"):
            problems.append(f"{key}: no dropout rule")
        for d in rec.get("dropout") or []:
            _check_dropout(f"{key}: dropout '{d.get('when')}'", d, core, allp, rank, problems)
        # conflict
        for c in rec.get("conflict") or []:
            _check_conflict(key, c, sensors, logs, problems)
        # max dwell
        md = rec.get("max_dwell")
        if isinstance(md, str) and md not in core["max_dwell"]:
            problems.append(f"{key}: max_dwell {md!r} is not in core.yaml max_dwell")
        if isinstance(md, dict):
            if not all(k in md for k in ("value", "unit", "rule", "why", "evidence")):
                problems.append(f"{key}: inline max_dwell needs value, unit, rule, why, evidence")
            elif not evidence_ok(md["evidence"], core):
                problems.append(f"{key}: max_dwell evidence must start with a tag of conventions.evidence_tags")
        for val, entry in (rec.get("max_dwell_by_value") or {}).items():
            if entry not in core["max_dwell"]:
                problems.append(f"{key}: max_dwell_by_value {val} -> {entry!r} is not in core.yaml max_dwell")
        for inp in rec.get("computed_from") or []:
            if inp not in index:
                problems.append(f"{key}: computed_from {inp!r} is not a field")
        if rec.get("computed_from") and rec.get("profile") != "meta":
            problems.append(f"{key}: computed_from is for meta fields (a derived field lists derived_from)")
        # derived
        if rec.get("profile") == "derived":
            for k in ("derived_from", "recompute_on", "valid_if"):
                if not rec.get(k):
                    problems.append(f"{key}: derived field missing {k}")
            for inp in rec.get("derived_from") or []:
                if inp not in index:
                    problems.append(f"{key}: derived_from {inp!r} is not a field")
        elif rec.get("derived_from"):
            problems.append(f"{key}: derived_from on a field whose profile is {rec.get('profile')} (only derived fields have inputs)")
    for d, keys in dim_used.items():
        if len(keys) > 1:
            problems.append(f"state-machine dimension {d} is carried by {len(keys)} fields: {keys}")

    # derived_from: no cycle; a derived value is never known before its slowest input
    graph = {k: list(r.get("derived_from") or []) for k, r in full.items()}

    def cyc(node, stack):
        if node in stack:
            return stack[stack.index(node):] + [node]
        for nxt in graph.get(node, []):
            c = cyc(nxt, stack + [node])
            if c:
                return c
        return None
    reported = set()
    for k in graph:
        c = cyc(k, [])
        if c and frozenset(c) not in reported:
            reported.add(frozenset(c))
            problems.append("derived_from cycle: " + " -> ".join(c))
    for k, r in full.items():
        mine = ((r.get("timing") or {}).get("provisional") or {}).get("p50_s")
        driven = (r.get("timing") or {}).get("driven_by")
        for inp in driven or []:
            if inp not in graph.get(k, []):
                problems.append(f"{k}: timing.driven_by {inp!r} is not one of its derived_from inputs")
        for inp in (driven if driven else graph.get(k, [])):
            theirs = (((full.get(inp) or {}).get("timing") or {}).get("provisional") or {}).get("p50_s")
            if _num(mine) and _num(theirs) and mine < theirs:
                problems.append(f"{k}: provisional p50 {mine} is earlier than its input {inp} ({theirs}); "
                                "a derived value is never known before the input that drives it (timing.driven_by names those inputs)")

    if require_all:
        for key in index:
            if key not in full:
                problems.append(f"index entry {key} has no record")
        cited = {x for r in full.values() for x in (r.get("requirements") or [])}
        cited |= {re.sub(r"[a-c]$", "", x) for x in cited}
        for rid in SHALL_SR:
            if rid not in cited:
                problems.append(f"requirement {rid} (Shall) is cited by no field")
        for name in core.get("production_only_params") or []:   # needs every fields file: field params are listed too
            if name not in allp:
                problems.append(f"production_only_params: {name!r} is not a param of the pack")
        unread = unread_params(core, fields)
        if unread is not None:
            listed = set(core.get("production_only_params") or [])
            for name in sorted(set(unread) ^ listed):
                problems.append(f"param {name}: " + ("is read by no reference code and is not listed under production_only_params"
                                                     if name in unread else "is listed under production_only_params but the reference code reads it"))
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", nargs="?", const="ALL", default="ALL", help="a fields file to check on its own; default: the whole pack")
    a = ap.parse_args()
    try:
        core = load_core()
        fields = load_fields() if a.check == "ALL" else load_fields([a.check])
    except (FileNotFoundError, ValueError, yaml.YAMLError) as e:  # a missing file, a field written twice, broken YAML
        print("FAIL", " ".join(str(e).split()))
        sys.exit(2)
    require_all = a.check == "ALL"
    if not require_all and not fields:
        print(f"FAIL {a.check} holds no field records")
        sys.exit(2)
    problems = validate(core, fields, require_all=require_all)
    for p in problems:
        print("FAIL", p)
    print(f"{len(fields)} fields checked, {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
