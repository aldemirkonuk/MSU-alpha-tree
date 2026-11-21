"""Views catalogue: loader, reference resolvers, palette contrast and lint (config/views/*.yaml).

Usage:
  python tools/specgen/views/vwlib.py --check                               # everything; index entries without a record are problems
  python tools/specgen/views/vwlib.py --check config/views/views_live.yaml  # one views file on its own
  python tools/specgen/views/vwlib.py --palette                             # print the computed contrast of every pair

The pack is core.yaml (conventions, audiences, surfaces, the display contract, components, interaction grammar,
refresh classes, view_index, inventory, acceptance) plus three views files. A views file holds `views: {key: record}`.
A record is one view; a tile or panel inside it is an element.

What the lint checks (validate):
  core    params complete with evidence tags, mirrors and measured keys; the grade table equals the live-state grades;
          degraded defaults for every surface and level; palette: tokens in both themes, every text pair at least
          4.5:1 and every mark at least 3:1 with the stored ratio equal to the computed one, a categorical set of at
          least 8, a sequential scale that rises in luminance, a diverging scale with the lightest stop in the middle;
          privacy classes; components (inputs resolve); actions; refresh classes; the index (ids unique and gap-free
          per surface); the inventory (every target exists, every required row has a view, every live-state group and
          every registry category has a row, no view without an inventory row; a row without a view is a reported
          row and gives its reason); acceptance ids; follow-ups.
  record  equals its index entry; required keys and no unknown key; audience and privacy; question, grain; as_of
          (a live_panel view reads as_of_known only; a mixed view marks every element); refresh class and budget; all
          six degraded states; elements (keys unique, kind, inputs resolve: live-state keys, table.column, metric ids,
          spot ids and layers, grammar and transition ids); a number_rule on every element that shows a number, with
          the parts its class asks for and no other key; grade_rule; identity_rule where identity is read; a court
          names its named-spots layers; no banned column; no banned unit; interactions; requirement ids and the rows
          the inventory assigns; depends_on covers what is read; acceptance ids; wireframe and wireframe_states;
          with covers_all_live_state: every live-state field is in an element or in not_shown, and every tile says
          what it shows at every grade and every level.
  whole   (require_all) every index entry has a record; every registry category is read by a view; every reported
          requirement row is cited by a record or has its reason.

The wireframes (gen_wireframes.py) and the two pages (gen_doc.py) are generated from the pack; both have --check.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[3]
PACK_DIR = REPO / "config" / "views"
CORE = PACK_DIR / "core.yaml"
VIEW_FILES = ["views_live", "views_review", "views_studio"]
LIVE_STATE_CORE = REPO / "config" / "live_state" / "core.yaml"
METRICS = REPO / "config" / "metrics.yaml"
NAMED_SPOTS = REPO / "config" / "named_spots.yaml"
GRAMMAR_DIR = REPO / "config" / "movement_grammar"
STATE_MACHINE = REPO / "config" / "state_machine.yaml"
SCHEMA_DIR = REPO / "schema" / "tables"
CHANGES_GLOB = "*_changes.yaml"          # schema/views_changes.yaml and the proposals of the sister baselines
CHANGES = REPO / "schema" / "views_changes.yaml"

PARAM_KEYS = ("value", "unit", "why", "evidence")
INPUT_KEYS = ("live_state", "tables", "metrics", "spots", "events")
AS_OF = ("as_of_known", "as_of_event")
REQ_RE = re.compile(r"^R-[A-Z]{2,3}-\d{2}[a-z]?$")
VIEW_ID_RE = re.compile(r"^VW-([A-Z]+)-(\d{2})$")
ACC_RE = re.compile(r"^ACC-VW-[A-Z]?\d+$")
METRIC_RE = re.compile(r"^M-[A-Z]+-\d{3}$")
HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
NUMBER_KINDS = {"tile", "chart", "table"}        # kinds that show a number unless the element says numbers: none
MISSING = "missing record:"                      # prefix of the problems an unfinished pack is expected to have


# --------------------------------------------------------------------------------------------------------------------
# loading
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


def load_views(files=None):
    """-> {view_key: record}, each record tagged with _file (the stem of its views file)."""
    out = {}
    for stem in (files or VIEW_FILES):
        if str(stem).endswith(".yaml"):
            p = Path(stem)
            if not p.exists():  # a path given relative to the repo root, whatever the working directory
                p = REPO / stem
            if not p.exists():
                raise FileNotFoundError(f"views file not found: {stem}")
        else:
            p = PACK_DIR / f"{stem}.yaml"
            if not p.exists():  # a views file of the pack that is not written yet
                continue
        doc = load_yaml_strict(p) or {}
        for key, rec in (doc.get("views") or {}).items():
            if key in out:
                raise ValueError(f"view {key} is written twice ({out[key]['_file']} and {p.stem})")
            rec = dict(rec or {})
            rec["_file"] = p.stem
            out[key] = rec
    return out


# --------------------------------------------------------------------------------------------------------------------
# palette: WCAG 2.1 relative luminance and contrast ratio
def luminance(hex_colour):
    """Relative luminance of an sRGB colour written #RRGGBB (WCAG 2.1 definition)."""
    h = hex_colour.lstrip("#")
    lin = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255.0
        lin.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(hex_a, hex_b):
    """WCAG 2.1 contrast ratio of two colours, 1.0 to 21.0."""
    la, lb = sorted((luminance(hex_a), luminance(hex_b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def tokens(core, theme):
    """Every colour token of one theme: the theme's own tokens plus the shared ones."""
    vs = core["display_contract"]["visual_standard"]
    return {**(vs.get("shared_tokens") or {}), **(vs["themes"][theme] or {})}


def palette_table(core):
    """[(kind, a, b, theme, computed ratio)] for every pair of the visual standard."""
    vs = core["display_contract"]["visual_standard"]
    rows = []
    for theme in vs["themes"]:
        tk = tokens(core, theme)
        for p in vs.get("text_pairs") or []:
            rows.append(("text", p["text"], p["bg"], theme, contrast(tk[p["text"]], tk[p["bg"]])))
        for p in vs.get("graphic_pairs") or []:
            rows.append(("mark", p["mark"], p["bg"], theme, contrast(tk[p["mark"]], tk[p["bg"]])))
        for c in (vs.get("categorical") or {}).get("set") or []:
            rows.append(("categorical", c["name"], vs["categorical"]["use_on"], theme, contrast(c["hex"], tk[vs["categorical"]["use_on"]])))
    return rows


# --------------------------------------------------------------------------------------------------------------------
# references into the other baselines (each read once per process)
_CACHE = {}
_FAST = getattr(yaml, "CSafeLoader", yaml.SafeLoader)   # the reference files are large (the metric registry alone is several MB)


def _read(path):
    return yaml.load(Path(path).read_text(), Loader=_FAST)


def _yaml(path):
    path = Path(path)
    if path not in _CACHE:
        _CACHE[path] = json.loads(path.read_text()) if path.suffix == ".json" else _read(path)
    return _CACHE[path]


def dig(obj, dotted):
    """Walk a dotted key. In a list a number is an index."""
    for seg in str(dotted).split("."):
        obj = obj[int(seg)] if isinstance(obj, list) else obj[seg]
    return obj


def _column_names(cols):
    if isinstance(cols, dict):
        return [str(c) for c in cols]
    out = []
    for c in cols or []:
        name = (c.get("column") or c.get("name")) if isinstance(c, dict) else c
        if name:
            out.append(str(name))
    return out


class Refs:
    """Everything a view may name by id, read from the other packs at lint time (no count is hard-coded)."""

    _shared = {}   # one cache per process: the other packs do not change while a lint or a test run lasts

    def __init__(self):
        self._c = Refs._shared

    def _get(self, key, fn):
        if key not in self._c:
            self._c[key] = fn()
        return self._c[key]

    # live state -------------------------------------------------------------------------------------------------
    def ls_index(self):
        return self._get("ls", lambda: _yaml(LIVE_STATE_CORE)["field_index"])

    def ls_key(self, ref):
        """The field key for a key or an LS id; None when unknown."""
        idx = self.ls_index()
        if ref in idx:
            return ref
        by_id = self._get("ls_by_id", lambda: {v["id"]: k for k, v in idx.items()})
        return by_id.get(ref)

    def ls_groups(self):
        return self._get("ls_groups", lambda: {v["group"] for v in self.ls_index().values()})

    def grades(self):
        g = _yaml(LIVE_STATE_CORE)["grades"]
        return list(g["ladder"]) + list(g["aside"])

    def levels(self):
        return [k for k in _yaml(LIVE_STATE_CORE)["degradation_levels"] if k != "rule"]

    # metrics ----------------------------------------------------------------------------------------------------
    def metric_ids(self):
        return self._get("metrics", lambda: {m["id"] for c in _yaml(METRICS)["categories"] for m in c.get("metrics") or []})

    def metric_categories(self):
        return self._get("metric_cats", lambda: {c["code"] for c in _yaml(METRICS)["categories"]})

    # schema -----------------------------------------------------------------------------------------------------
    def schema(self):
        def build():
            out = {}
            for p in SCHEMA_DIR.glob("*.yaml"):
                try:
                    d = _read(p) or {}
                except yaml.YAMLError:
                    continue
                out[p.stem] = set(_column_names(d.get("columns")))
            return out
        return self._get("schema", build)

    def proposed_by_file(self):
        """{change file name: {table: set(columns)}} for every schema/*_changes.yaml: column additions, new tables, renames."""
        def build():
            out = {}
            for p in sorted(SCHEMA_DIR.parent.glob(CHANGES_GLOB)):
                try:
                    d = _read(p) or {}
                except yaml.YAMLError:
                    continue
                got = out.setdefault(p.name, {})
                add = d.get("column_additions") or {}
                if isinstance(add, dict):          # {table: [{column: name}]}
                    for table, cols in add.items():
                        got.setdefault(table, set()).update(_column_names(cols))
                else:                              # [{table: t, column: name}] (schema/tables_proposed_changes.yaml)
                    for c in add:
                        if isinstance(c, dict) and c.get("table") and c.get("column"):
                            got.setdefault(str(c["table"]), set()).add(str(c["column"]))
                new = d.get("new_tables") or {}
                if isinstance(new, list):
                    new = {str(t.get("table") or t.get("name")): t for t in new if isinstance(t, dict)}
                for table, spec in new.items():
                    got.setdefault(table, set()).update(_column_names((spec or {}).get("columns") if isinstance(spec, dict) else None))
                audit = (d.get("team_neutral") or {}).get("audit") if isinstance(d.get("team_neutral"), dict) else None
                for table, cols in (audit or {}).items():
                    for spec in (cols or {}).values():
                        if isinstance(spec, dict) and spec.get("action") == "rename" and spec.get("to"):
                            got.setdefault(table, set()).add(str(spec["to"]))
            return out
        return self._get("proposed_by_file", build)

    def proposed(self):
        """{table: set(columns)} proposed in any schema/*_changes.yaml."""
        def build():
            out = {}
            for tables in self.proposed_by_file().values():
                for table, cols in tables.items():
                    out.setdefault(table, set()).update(cols)
            return out
        return self._get("proposed", build)

    def column_state(self, ref):
        """'schema', 'proposed' or None for a table.column reference."""
        table, _, col = str(ref).partition(".")
        if not col:
            return None
        if col in self.schema().get(table, ()):
            return "schema"
        if col in self.proposed().get(table, ()):
            return "proposed"
        return None

    def table_known(self, table):
        return table in self.schema() or table in self.proposed()

    # named spots ------------------------------------------------------------------------------------------------
    def spots(self):
        def build():
            entries = _yaml(NAMED_SPOTS)["entries"]
            return {e["id"] for e in entries}, {e["layer"] for e in entries}
        return self._get("spots", build)

    def spot_ok(self, ref):
        ids, layers = self.spots()
        ref = str(ref)
        return ref[len("layer:"):] in layers if ref.startswith("layer:") else ref in ids

    # events -----------------------------------------------------------------------------------------------------
    def grammar(self):
        def build():
            out = {}
            for p in sorted(GRAMMAR_DIR.glob("*.yaml")):
                try:
                    d = _read(p) or {}
                except yaml.YAMLError:
                    continue
                items = d.get("items")
                if isinstance(items, list):
                    out[p.stem] = {x["id"] for x in items if isinstance(x, dict) and x.get("id")}
            return out
        return self._get("grammar", build)

    def event_kind(self, ref):
        """'transition', 'dimension', 'grammar' or None."""
        ref = str(ref)
        sm = _yaml(STATE_MACHINE)
        if ref in sm["transitions"]:
            return "transition"
        if ref.startswith("dim:"):
            return "dimension" if ref[4:] in sm["dimensions"] else None
        family, _, item = ref.partition(":")
        return "grammar" if item and item in self.grammar().get(family, ()) else None


# --------------------------------------------------------------------------------------------------------------------
# small helpers
def is_param(o):
    return isinstance(o, dict) and "value" in o and any(k in o for k in ("unit", "why", "evidence"))


def iter_params(obj, path=""):
    """Every param {value, unit, why, evidence} below obj, with its dotted path."""
    if is_param(obj):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_params(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_params(v, f"{path}.{i}")


def iter_strings(obj, path="", skip=()):
    """Every string below obj with its dotted path; keys named in skip are not entered."""
    if isinstance(obj, str):
        yield path, obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in skip or str(k).startswith("_"):
                continue
            yield from iter_strings(v, f"{path}.{k}" if path else str(k), skip)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_strings(v, f"{path}.{i}", skip)


def evidence_ok(text, core):
    tags = ((core.get("conventions") or {}).get("evidence_tags") or {}).get("tags") or {}
    return isinstance(text, str) and any(text.startswith(f"{t}:") for t in tags)


def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _text(x):
    return isinstance(x, str) and x.strip() != ""


def unit_problems(obj, banned, skip=("banned_units",)):
    """Strings that name a banned (non-metric) unit: '<number> ft', the words feet / inches / yards / mph, or a unit key."""
    if not banned:
        return []
    alts = "|".join(sorted((re.escape(b) for b in banned), key=len, reverse=True))
    attached = re.compile(rf"\d\s*(?:{alts})\b")
    words = [b for b in banned if b in ("feet", "inches", "yards", "mph")]
    standalone = re.compile(rf"\b(?:{'|'.join(words)})\b") if words else None
    out = []
    for path, s in iter_strings(obj, skip=skip):
        leaf = path.rsplit(".", 1)[-1]
        if leaf in ("unit", "units") and s.strip().lower() in banned:
            out.append(f"{path}: unit {s!r} is not metric")
        elif attached.search(s) or (standalone and standalone.search(s)):
            out.append(f"{path}: names a non-metric unit ({s[:60]!r})")
    return out


def check_param(where, p, core, problems):
    for k in PARAM_KEYS:
        if k not in p or p[k] in (None, ""):
            problems.append(f"{where}: param lacks {k}")
    if "evidence" in p and not evidence_ok(p["evidence"], core):
        problems.append(f"{where}: evidence must start with a tag of conventions.evidence_tags ({str(p.get('evidence'))[:40]!r})")
    if "mirrors" in p:
        try:
            file, _, key = str(p["mirrors"]).partition(":")
            other = dig(_yaml(REPO / file), key)
            if other != p.get("value"):
                problems.append(f"{where}: value {p.get('value')} differs from {p['mirrors']} ({other})")
        except (OSError, KeyError, IndexError, ValueError, TypeError):
            problems.append(f"{where}: mirrors {p['mirrors']!r} cannot be resolved")
    if "measured_key" in p:
        try:
            got = dig(_yaml(REPO / p["measured_file"]), p["measured_key"])
            if p.get("measured_one_minus"):
                got = 1 - got
            if "measured_round" in p:
                got = round(got, int(p["measured_round"]))
            if got != p.get("value"):
                problems.append(f"{where}: value {p.get('value')} differs from the measured {got} ({p['measured_file']}:{p['measured_key']})")
        except (OSError, KeyError, IndexError, ValueError, TypeError):
            problems.append(f"{where}: measured_key {p.get('measured_key')!r} cannot be resolved in {p.get('measured_file')!r}")


def check_inputs(where, inputs, refs, problems, banned_col=None):
    """Resolve every input reference. -> {'live_state': keys, 'tables': table names, 'metrics', 'spots', 'events': kinds}."""
    used = {"live_state": set(), "tables": set(), "metrics": set(), "spots": set(), "events": set(), "columns": set()}
    if inputs is None:
        return used
    if not isinstance(inputs, dict):
        problems.append(f"{where}: inputs must be a mapping of {list(INPUT_KEYS)}")
        return used
    for k in inputs:
        if k not in INPUT_KEYS:
            problems.append(f"{where}: unknown input kind {k!r}")
    for ref in inputs.get("live_state") or []:
        key = refs.ls_key(ref)
        if key is None:
            problems.append(f"{where}: unknown live-state key {ref!r}")
        else:
            used["live_state"].add(key)
    for ref in inputs.get("tables") or []:
        state = refs.column_state(ref)
        if state is None:
            problems.append(f"{where}: unknown table.column {ref!r} (not in schema/tables and not in a schema/*_changes.yaml file)")
        else:
            used["tables"].add(str(ref).partition(".")[0])
            used["columns"].add(str(ref))
        if banned_col and banned_col.search(str(ref).partition(".")[2]):
            problems.append(f"{where}: column {ref!r} is banned (no face image in any view)")
    for ref in inputs.get("metrics") or []:
        if not METRIC_RE.match(str(ref)) or ref not in refs.metric_ids():
            problems.append(f"{where}: unknown metric id {ref!r}")
        else:
            used["metrics"].add(ref)
    for ref in inputs.get("spots") or []:
        if not refs.spot_ok(ref):
            problems.append(f"{where}: unknown named-spots id or layer {ref!r}")
        else:
            used["spots"].add(ref)
    for ref in inputs.get("events") or []:
        kind = refs.event_kind(ref)
        if kind is None:
            problems.append(f"{where}: unknown event id {ref!r} (a transition T00-T26, dim:<dimension> or <family>:<grammar item>)")
        else:
            used["events"].add(kind)
    return used


# --------------------------------------------------------------------------------------------------------------------
# core
def _validate_palette(core, problems):
    vs = core["display_contract"]["visual_standard"]
    themes = vs.get("themes") or {}
    if set(themes) != {"light", "dark"}:
        problems.append("visual_standard.themes: must hold exactly light and dark")
        return
    if set(themes["light"]) != set(themes["dark"]):
        problems.append(f"visual_standard.themes: light and dark differ in tokens {sorted(set(themes['light']) ^ set(themes['dark']))}")
    for theme in themes:
        for name, hx in tokens(core, theme).items():
            if not isinstance(hx, str) or not HEX_RE.match(hx):
                problems.append(f"visual_standard token {name} ({theme}): {hx!r} is not #RRGGBB")
    if any("is not #RRGGBB" in p for p in problems):
        return
    prm = vs.get("params") or {}
    text_min = (prm.get("text_contrast_min") or {}).get("value")
    mark_min = (prm.get("graphic_contrast_min") or {}).get("value")
    if not _num(text_min) or text_min < 4.5:
        problems.append("visual_standard.params.text_contrast_min: must be at least 4.5 (R-VZ-07)")
        text_min = 4.5
    if not _num(mark_min) or mark_min < 3.0:
        problems.append("visual_standard.params.graphic_contrast_min: must be at least 3.0")
        mark_min = 3.0

    def pair(kind, a, b, stored, floor):
        for theme in themes:
            tk = tokens(core, theme)
            if a not in tk or b not in tk:
                problems.append(f"visual_standard {kind} pair {a} on {b}: token missing in theme {theme}")
                continue
            got = contrast(tk[a], tk[b])
            st = (stored or {}).get(theme)
            if not _num(st) or abs(st - got) > 0.006:
                problems.append(f"visual_standard {kind} pair {a} on {b} ({theme}): stored ratio {st} differs from the computed {got:.2f}")
            if got < floor:
                problems.append(f"visual_standard {kind} pair {a} on {b} ({theme}): contrast {got:.2f} is below {floor}")

    paired_text = set()
    for p in vs.get("text_pairs") or []:
        pair("text", p.get("text"), p.get("bg"), p.get("ratio"), text_min)
        paired_text.add(p.get("text"))
    for p in vs.get("graphic_pairs") or []:
        pair("mark", p.get("mark"), p.get("bg"), p.get("ratio"), mark_min)
    for name in themes["light"]:
        if name.startswith("text.") and name not in paired_text:
            problems.append(f"visual_standard: text token {name} is in no text pair, so its contrast is unchecked")
    for side, tm in (vs.get("team_marks") or {}).items():
        if (tm.get("label_text"), tm.get("token")) not in {(p.get("text"), p.get("bg")) for p in vs.get("text_pairs") or []}:
            problems.append(f"visual_standard.team_marks.{side}: label text on the team colour is not a checked text pair")
    marks = vs.get("team_marks") or {}
    if set(marks) != {"home", "away"} or len({m.get("shape") for m in marks.values()}) != 2:
        problems.append("visual_standard.team_marks: home and away each need a token and a different shape")

    cat = vs.get("categorical") or {}
    cset = cat.get("set") or []
    if len(cset) < 8:
        problems.append(f"visual_standard.categorical: {len(cset)} colours, at least 8 are required")
    if len({c.get("hex", "").upper() for c in cset}) != len(cset) or [c.get("slot") for c in cset] != list(range(1, len(cset) + 1)):
        problems.append("visual_standard.categorical: slots must run 1..n and every hex must differ")
    if len(cat.get("second_channel") or []) < len(cset):
        problems.append("visual_standard.categorical: second_channel needs one shape or dash per colour (colour is never the only carrier)")
    for c in cset:
        if not HEX_RE.match(str(c.get("hex"))):
            problems.append(f"visual_standard.categorical slot {c.get('slot')}: bad hex")
            continue
        for theme in themes:
            got = contrast(c["hex"], tokens(core, theme).get(cat.get("use_on"), "#000000"))
            if got < mark_min:
                problems.append(f"visual_standard.categorical {c.get('name')} ({theme}): contrast {got:.2f} on {cat.get('use_on')} is below {mark_min}")
            if not _num(c.get("ratio_on_chart")) or abs(c["ratio_on_chart"] - got) > 0.006:
                problems.append(f"visual_standard.categorical {c.get('name')} ({theme}): stored ratio {c.get('ratio_on_chart')} differs from the computed {got:.2f}")
    seq = (vs.get("sequential") or {}).get("stops") or []
    if len(seq) < 5 or not all(HEX_RE.match(str(s)) for s in seq):
        problems.append("visual_standard.sequential: at least 5 hex stops are required")
    else:
        lum = [luminance(s) for s in seq]
        if any(b <= a for a, b in zip(lum, lum[1:])):
            problems.append("visual_standard.sequential: luminance must rise from the first stop to the last")
    div = (vs.get("diverging") or {}).get("stops") or []
    if len(div) < 5 or len(div) % 2 == 0 or not all(HEX_RE.match(str(s)) for s in div):
        problems.append("visual_standard.diverging: an odd number of hex stops, at least 5, is required")
    else:
        lum = [luminance(s) for s in div]
        mid = len(div) // 2
        if any(b <= a for a, b in zip(lum[:mid + 1], lum[1:mid + 1])) or any(b >= a for a, b in zip(lum[mid:], lum[mid + 1:])):
            problems.append("visual_standard.diverging: the middle stop must be the lightest and each arm must darken away from it")
    for k in ("caption_px", "body_px", "value_px", "hero_px", "large_text_px"):
        if not is_param((vs.get("text_sizes") or {}).get(k)):
            problems.append(f"visual_standard.text_sizes.{k}: missing")
    sizes = {k: v.get("value") for k, v in (vs.get("text_sizes") or {}).items() if is_param(v)}
    order = [sizes.get(k) for k in ("caption_px", "body_px", "value_px", "hero_px")]
    if all(_num(x) for x in order) and order != sorted(order):
        problems.append("visual_standard.text_sizes: caption, body, value, hero must not shrink in that order")
    if not vs.get("banned_units"):
        problems.append("visual_standard.banned_units: missing")


def _validate_core(core, refs, problems):
    conv = core.get("conventions") or {}
    dc = core.get("display_contract") or {}
    for k in ("pack", "version", "date", "status", "scope", "requirement", "files", "conventions", "view_record", "audiences", "surfaces",
              "display_contract", "components", "interaction_grammar", "refresh_classes", "view_index", "out_of_scope", "inventory",
              "acceptance", "journal", "open_questions"):
        if not core.get(k):
            problems.append(f"core: section {k} is missing")
    if problems:
        return
    if core["pack"] != "views" or not isinstance(core["date"], str):
        problems.append("core: pack must be views and date a quoted string")
    for path, p in iter_params(core):
        check_param(f"core.{path}", p, core, problems)
    for rid in (core["requirement"].get("requirements") or []):
        if not REQ_RE.match(str(rid)):
            problems.append(f"core.requirement: {rid!r} is not a requirement id")

    # audiences and surfaces
    codes = {}
    for name, s in core["surfaces"].items():
        if s.get("code") in codes:
            problems.append(f"surface {name}: code {s.get('code')} is used twice")
        codes[s.get("code")] = name
        for a in s.get("as_of_allowed") or []:
            if a not in AS_OF + ("mixed",):
                problems.append(f"surface {name}: as_of_allowed {a!r} is not known")
        if not s.get("as_of_allowed"):
            problems.append(f"surface {name}: as_of_allowed is empty")
        if s.get("width_rule") not in ((dc.get("visual_standard") or {}).get("width_rules") or {}):
            problems.append(f"surface {name}: width_rule {s.get('width_rule')!r} is not in visual_standard.width_rules")
        if s.get("refresh_default") not in core["refresh_classes"]:
            problems.append(f"surface {name}: refresh_default {s.get('refresh_default')!r} is not a refresh class")
    if core["surfaces"].get("live_panel", {}).get("as_of_allowed") != ["as_of_known"]:
        problems.append("surface live_panel: must allow as_of_known only")

    # rule 1: grades
    grades = dc.get("grades") or {}
    app = grades.get("appearance") or {}
    if list(app) != refs.grades():
        problems.append(f"display_contract.grades.appearance: grades {list(app)} differ from the live-state pack {refs.grades()}")
    light = set(((dc.get("visual_standard") or {}).get("themes") or {}).get("light") or {})
    for g, a in app.items():
        for k in ("value_text", "tile_edge", "court_marker", "badge", "shows_age", "shows_region", "visible_in", "in_words"):
            if k not in a:
                problems.append(f"display_contract.grades.appearance.{g}: lacks {k}")
        if a.get("value_text") not in light:
            problems.append(f"display_contract.grades.appearance.{g}: value_text {a.get('value_text')!r} is not a theme token")
        if a.get("visible_in") not in ("all", "review_queue_only"):
            problems.append(f"display_contract.grades.appearance.{g}: visible_in must be all or review_queue_only")
        if a.get("badge") != "none" and a.get("badge") not in (grades.get("badge_texts") or {}):
            problems.append(f"display_contract.grades.appearance.{g}: badge {a.get('badge')!r} has no text in badge_texts")
    for g in ("inferred", "carried", "imputed", "unknown", "quarantined"):
        if (app.get(g) or {}).get("badge") in (None, "none"):
            problems.append(f"display_contract.grades.appearance.{g}: needs a text badge (grade is never carried by colour alone)")
    for g in ("carried", "imputed"):
        if not (app.get(g) or {}).get("shows_age"):
            problems.append(f"display_contract.grades.appearance.{g}: must show its age")
    if not (app.get("imputed") or {}).get("shows_region"):
        problems.append("display_contract.grades.appearance.imputed: must show its region")
    if (app.get("quarantined") or {}).get("visible_in") != "review_queue_only":
        problems.append("display_contract.grades.appearance.quarantined: must be visible in the review queue only")
    for v in grades.get("review_views") or []:
        if v not in core["view_index"]:
            problems.append(f"display_contract.grades.review_views: {v!r} is not in the index")

    # rule 2: identity
    ident = dc.get("identity") or {}
    for f in ident.get("live_state_fields") or []:
        if refs.ls_key(f) is None:
            problems.append(f"display_contract.identity.live_state_fields: unknown live-state key {f!r}")
    for k in ("column_pattern", "banned_column_pattern"):
        try:
            re.compile(ident.get(k) or "(")
        except re.error:
            problems.append(f"display_contract.identity.{k}: missing or not a regular expression")
    if set(ident.get("rules") or {}) != {"locked_or_hold", "probable_flagged_offline"}:
        problems.append("display_contract.identity.rules: must define locked_or_hold and probable_flagged_offline")

    # rule 3: numbers
    numbers = dc.get("numbers") or {}
    for c, spec in (numbers.get("classes") or {}).items():
        if not spec.get("must_show") or "link" not in (spec.get("needs") or []):
            problems.append(f"display_contract.numbers.classes.{c}: needs must_show and a link (R-VZ-02)")
    for need in ("estimate", "official", "live_state", "model", "descriptive"):
        if need not in (numbers.get("classes") or {}):
            problems.append(f"display_contract.numbers.classes: class {need} is missing")
    if not is_param((numbers.get("params") or {}).get("min_n_default")):
        problems.append("display_contract.numbers.params.min_n_default: missing (K12)")

    # rule 4 and 5: as-of and degraded states
    if set(AS_OF + ("mixed",)) - set((dc.get("as_of") or {}).get("rules") or {}):
        problems.append("display_contract.as_of.rules: must define as_of_known, as_of_event and mixed")
    deg = dc.get("degraded") or {}
    want_levels = [x for x in refs.levels() if x != "D0_full"]
    if list(deg.get("levels") or []) != want_levels:
        problems.append(f"display_contract.degraded.levels: {deg.get('levels')} differ from the live-state pack {want_levels}")
    for s in core["surfaces"]:
        d = (deg.get("defaults") or {}).get(s)
        if not isinstance(d, dict) or list(d) != want_levels or not all(_text(v) for v in d.values()):
            problems.append(f"display_contract.degraded.defaults.{s}: must say what is shown at each of {want_levels}")

    # rule 6: palette
    _validate_palette(core, problems)
    problems.extend(f"core.{p}" for p in unit_problems({k: core[k] for k in ("display_contract", "components", "interaction_grammar", "refresh_classes")},
                                                      (dc.get("visual_standard") or {}).get("banned_units") or []))

    # rule 7: privacy
    priv = dc.get("privacy") or {}
    exports = priv.get("exports") or {}
    for c, spec in (priv.get("classes") or {}).items():
        for a in spec.get("audiences") or []:
            if a not in core["audiences"]:
                problems.append(f"display_contract.privacy.classes.{c}: unknown audience {a!r}")
        for e in spec.get("exports") or []:
            if e not in exports:
                problems.append(f"display_contract.privacy.classes.{c}: unknown export {e!r}")
        if not spec.get("video") and "video_clip_private" in (spec.get("exports") or []):
            problems.append(f"display_contract.privacy.classes.{c}: a class without video cannot export a video clip")
        if "video" not in spec or "player_level" not in spec:
            problems.append(f"display_contract.privacy.classes.{c}: must state video and player_level")
    if set(priv.get("classes") or {}) != {"owner_only", "msu_staff", "shareable_aggregate", "public_demo"}:
        problems.append("display_contract.privacy.classes: must be owner_only, msu_staff, shareable_aggregate, public_demo")
    for c in ("shareable_aggregate", "public_demo"):
        spec = (priv.get("classes") or {}).get(c) or {}
        if spec.get("video") or spec.get("player_level") or "clip_reference" in (spec.get("exports") or []):
            problems.append(f"display_contract.privacy.classes.{c}: may hold no video, no player-level output and no clip reference")
    for g in priv.get("player_grains") or []:
        if g not in (conv.get("grains") or []):
            problems.append(f"display_contract.privacy.player_grains: {g!r} is not a grain")

    # components
    banned_col = re.compile(ident.get("banned_column_pattern") or "$^")
    for name, c in core["components"].items():
        w = f"component {name}"
        if c.get("kind") not in (conv.get("element_kinds") or []):
            problems.append(f"{w}: kind {c.get('kind')!r} is not an element kind")
        if not _text(c.get("purpose")) or not isinstance(c.get("behaviour"), list) or not c.get("behaviour"):
            problems.append(f"{w}: needs a purpose and a list of behaviour rules")
        check_inputs(w, c.get("inputs"), refs, problems, banned_col)
        for rid in c.get("requirements") or []:
            if not REQ_RE.match(str(rid)):
                problems.append(f"{w}: {rid!r} is not a requirement id")
        if not c.get("requirements"):
            problems.append(f"{w}: cites no requirement")

    # interaction grammar
    ig = core["interaction_grammar"]
    for name, a in (ig.get("actions") or {}).items():
        if not all(_text(a.get(k)) for k in ("gesture", "result")) or not REQ_RE.match(str(a.get("requirement"))):
            problems.append(f"interaction_grammar.actions.{name}: needs gesture, result and a requirement id")
    if len((ig.get("shortcuts") or {}).get("keys") or {}) < 20:
        problems.append("interaction_grammar.shortcuts: fewer than 20 keys (R-AS-07)")

    # refresh classes
    for name, r in core["refresh_classes"].items():
        if name in ("policy", "budget_meaning"):
            continue
        if not _text(r.get("trigger")) or not is_param(r.get("budget_s")) or not _num(r["budget_s"].get("value")) or r["budget_s"]["value"] <= 0:
            problems.append(f"refresh_classes.{name}: needs a trigger and a positive budget_s param")
    if "K23" not in str(core["refresh_classes"].get("policy")):
        problems.append("refresh_classes.policy: must state decision K23 (reported, not gated)")

    # index
    index = core["view_index"]
    seen_ids, per_surface = {}, {}
    for key, e in index.items():
        m = VIEW_ID_RE.match(str(e.get("id")))
        if not m:
            problems.append(f"view_index.{key}: id {e.get('id')!r} is not VW-<SURFACE>-NN")
            continue
        if e["id"] in seen_ids:
            problems.append(f"view_index.{key}: id {e['id']} is also {seen_ids[e['id']]}")
        seen_ids[e["id"]] = key
        if e.get("surface") not in core["surfaces"] or core["surfaces"][e["surface"]].get("code") != m.group(1):
            problems.append(f"view_index.{key}: id {e['id']} does not carry the code of surface {e.get('surface')!r}")
        per_surface.setdefault(m.group(1), []).append(int(m.group(2)))
        if e.get("file") not in VIEW_FILES:
            problems.append(f"view_index.{key}: file {e.get('file')!r} is not one of {VIEW_FILES}")
        if e.get("phase") not in (conv.get("phases") or []):
            problems.append(f"view_index.{key}: phase {e.get('phase')!r} is not a phase")
        if not _text(e.get("name")):
            problems.append(f"view_index.{key}: name is missing")
    for code, nums in per_surface.items():
        if sorted(nums) != list(range(1, len(nums) + 1)):
            problems.append(f"view_index: ids of surface {code} are not 01..{len(nums):02d} without a gap ({sorted(nums)})")
    for code, name in codes.items():
        if code not in per_surface:
            problems.append(f"view_index: surface {name} has no view")
    for key, f in (core.get("future_views") or {}).items():
        if key in index or not _text(f.get("why_future")):
            problems.append(f"future_views.{key}: must not be in the index and must say why it is future")
    for key, why in core["out_of_scope"].items():
        if key in index or not _text(why):
            problems.append(f"out_of_scope.{key}: must not be in the index and must give a reason")

    # inventory
    inv = core["inventory"]
    rows = inv.get("rows") or []
    covered, targeted, groups, cats = set(), set(), set(), set()
    for i, r in enumerate(rows):
        w = f"inventory row {i + 1} ({str(r.get('item'))[:40]})"
        if not _text(r.get("item")):
            problems.append(f"{w}: item is missing")
        if not any(k in r for k in ("view", "out_of_scope", "future", "component", "contract")):
            problems.append(f"{w}: points nowhere (view, component, contract, out_of_scope or future)")
        for rid in r.get("req") or []:
            if not REQ_RE.match(str(rid)):
                problems.append(f"{w}: {rid!r} is not a requirement id")
        if "view" in r:
            if r["view"] not in index:
                problems.append(f"{w}: view {r['view']!r} is not in the index")
            else:
                targeted.add(r["view"])
                covered.update(r.get("req") or [])
        if "element" in r and "view" not in r:
            problems.append(f"{w}: an element needs its view")
        if "component" in r and r["component"] not in core["components"]:
            problems.append(f"{w}: component {r['component']!r} does not exist")
        if "contract" in r and r["contract"] not in dc:
            problems.append(f"{w}: contract rule {r['contract']!r} does not exist")
        if "out_of_scope" in r and r["out_of_scope"] not in core["out_of_scope"]:
            problems.append(f"{w}: out_of_scope {r['out_of_scope']!r} does not exist")
        if "future" in r and r["future"] not in (core.get("future_views") or {}):
            problems.append(f"{w}: future view {r['future']!r} does not exist")
        if "live_state_group" in r:
            groups.add(r["live_state_group"])
        if "metric_category" in r:
            cats.add(r["metric_category"])
    for rid in inv.get("required_rows") or []:
        if rid not in covered:
            problems.append(f"inventory: required row {rid} is covered by no view")
    if groups != refs.ls_groups():
        problems.append(f"inventory: live-state groups differ from the live-state pack ({sorted(groups ^ refs.ls_groups())})")
    if cats != refs.metric_categories():
        problems.append(f"inventory: stat categories differ from the metric registry ({sorted(cats ^ refs.metric_categories())})")
    for key in index:
        if key not in targeted:
            problems.append(f"inventory: view {key} comes from no inventory row")
    for key in list(core["out_of_scope"]) + list(core.get("future_views") or {}):
        if not any(r.get("out_of_scope") == key or r.get("future") == key for r in rows):
            problems.append(f"inventory: {key} is named by no inventory row")
    for rid in list(inv.get("reported_rows") or []) + list(inv.get("no_view_rows") or {}):
        if not REQ_RE.match(str(rid)):
            problems.append(f"inventory: {rid!r} is not a requirement id")
    for rid, why in (inv.get("no_view_rows") or {}).items():
        if rid not in (inv.get("reported_rows") or []) or not _text(why):
            problems.append(f"inventory.no_view_rows.{rid}: must be a reported row and give its reason")
    for i, f in enumerate(core.get("follow_ups") or []):
        if not isinstance(f, dict) or not all(_text(f.get(k)) for k in ("id", "owner", "where", "what", "why")):
            problems.append(f"follow_ups {i + 1}: needs id, owner, where, what and why")

    # acceptance, questions
    acc_ids = [a.get("id") for a in core["acceptance"]]
    if len(set(acc_ids)) != len(acc_ids):
        problems.append("acceptance: an id is written twice")
    for a in core["acceptance"]:
        if not ACC_RE.match(str(a.get("id"))):
            problems.append(f"acceptance: id {a.get('id')!r} is not ACC-VW-<n>")
        for k in ("level", "runnable_now", "metric", "scope", "threshold", "on_fail", "requirement"):
            if k not in a or a[k] in (None, ""):
                problems.append(f"acceptance {a.get('id')}: lacks {k}")
        if a.get("level") not in ("lint", "render", "audit", "style"):
            problems.append(f"acceptance {a.get('id')}: level must be lint, render, audit or style")
        if not REQ_RE.match(str(a.get("requirement"))):
            problems.append(f"acceptance {a.get('id')}: requirement {a.get('requirement')!r} is not a requirement id")
    for lvl in ("lint", "render", "audit", "style"):
        if not any(a.get("level") == lvl for a in core["acceptance"]):
            problems.append(f"acceptance: no test at level {lvl}")
    qids = [q.get("id") for q in core["open_questions"]]
    if len(set(qids)) != len(qids):
        problems.append("open_questions: an id is written twice")
    for q in core["open_questions"]:
        if not all(_text(q.get(k)) for k in ("id", "question", "recommended", "status")):
            problems.append(f"open_questions {q.get('id')}: needs question, recommended answer and status")


# --------------------------------------------------------------------------------------------------------------------
# one record
def element_inputs(el, core):
    """The inputs of an element merged with those of its component."""
    merged = {k: list((el.get("inputs") or {}).get(k) or []) for k in INPUT_KEYS} if isinstance(el.get("inputs") or {}, dict) else {}
    comp = (core.get("components") or {}).get(el.get("component")) or {}
    for k in INPUT_KEYS:
        merged.setdefault(k, [])
        merged[k] += [x for x in (comp.get("inputs") or {}).get(k) or [] if x not in merged[k]]
    return merged


def shows_number(el):
    if el.get("numbers") == "none":
        return False
    return bool((el.get("inputs") or {}).get("metrics")) or el.get("kind") in NUMBER_KINDS or el.get("numbers") is True


def _check_number_rule(where, el, core, problems):
    dc = core["display_contract"]["numbers"]
    rule = el.get("number_rule")
    if rule is None:
        problems.append(f"{where}: shows a number but has no number_rule")
        return
    blocks = rule if isinstance(rule, list) else [rule]
    for b in blocks:
        if not isinstance(b, dict) or b.get("class") not in dc["classes"]:
            problems.append(f"{where}: number_rule class {b.get('class') if isinstance(b, dict) else b!r} is not one of {list(dc['classes'])}")
            continue
        spec = dc["classes"][b["class"]]
        for k in b:   # a comma inside an unquoted flow value splits it into a second key; that key is caught here
            if k not in ("class", "min_n", "notes") and k not in spec["must_show"] and k not in spec["needs"]:
                problems.append(f"{where}: number_rule of class {b['class']} has the unknown key {k!r}")
        for part in list(spec["must_show"]) + list(spec["needs"]):
            if b.get(part) in (None, ""):
                problems.append(f"{where}: number_rule of class {b['class']} lacks {part}")
        if b.get("link") is not None and b.get("link") not in dc["link_kinds"]:
            problems.append(f"{where}: number_rule link {b.get('link')!r} is not one of {list(dc['link_kinds'])}")
        if "min_n" in b and not (_num(b["min_n"]) or b["min_n"] in ("default", "registry")):
            problems.append(f"{where}: number_rule min_n must be a number, default (K12) or registry (the metric's own minimum)")
        if "level" in b and not (_num(b["level"]) and 0 < b["level"] < 1):
            problems.append(f"{where}: number_rule level must be a probability such as 0.95")


def _validate_view(key, rec, core, refs, problems):
    conv = core["conventions"]
    dc = core["display_contract"]
    vr = core["view_record"]
    index = core["view_index"]
    w = f"view {key}"
    if key not in index:
        problems.append(f"{w}: not in view_index")
        return
    e = index[key]
    for k in vr["required"]:
        if k not in rec:
            problems.append(f"{w}: lacks {k}")
    for k in rec:
        if not k.startswith("_") and k not in vr["required"] and k not in vr["optional"]:
            problems.append(f"{w}: unknown key {k!r}")
    for k in ("id", "surface", "name", "phase"):
        if rec.get(k) != e.get(k):
            problems.append(f"{w}: {k} {rec.get(k)!r} differs from the index ({e.get(k)!r})")
    if rec.get("_file") != e.get("file"):
        problems.append(f"{w}: written in {rec.get('_file')}, the index says {e.get('file')}")
    surface = core["surfaces"].get(rec.get("surface")) or {}

    # audience, privacy, question, grain
    aud = rec.get("audience") or []
    pclass = (dc["privacy"]["classes"]).get(rec.get("privacy"))
    if not aud or any(a not in core["audiences"] for a in aud):
        problems.append(f"{w}: audience {aud!r} must be a non-empty list of {list(core['audiences'])}")
    if pclass is None:
        problems.append(f"{w}: privacy {rec.get('privacy')!r} is not one of {list(dc['privacy']['classes'])}")
        pclass = {}
    else:
        for a in aud:
            if a not in pclass["audiences"]:
                problems.append(f"{w}: audience {a} may not see a view of privacy class {rec['privacy']}")
    if not _text(rec.get("question")) or not str(rec.get("question")).strip().endswith("?"):
        problems.append(f"{w}: question must be one plain question ending with ?")
    if rec.get("grain") not in conv["grains"]:
        problems.append(f"{w}: grain {rec.get('grain')!r} is not one of conventions.grains")
    if rec.get("grain") in dc["privacy"]["player_grains"] and pclass and not pclass.get("player_level"):
        problems.append(f"{w}: an individual player output cannot have privacy class {rec.get('privacy')}")

    # as-of
    as_of = rec.get("as_of") or {}
    view_as_of = as_of.get("view") if isinstance(as_of, dict) else None
    if view_as_of not in (surface.get("as_of_allowed") or []):
        if rec.get("surface") == "live_panel":
            problems.append(f"{w}: a live_panel view reads as_of_known only (as_of.view is {view_as_of!r})")
        else:
            problems.append(f"{w}: as_of.view {view_as_of!r} is not allowed on surface {rec.get('surface')} ({surface.get('as_of_allowed')})")
    passes = (as_of.get("pass") or []) if isinstance(as_of, dict) else []
    if any(p not in dc["as_of"]["passes"] for p in passes):
        problems.append(f"{w}: as_of.pass {passes} must be among {dc['as_of']['passes']}")
    if view_as_of in ("as_of_event", "mixed") and not passes:
        problems.append(f"{w}: a view that reads as_of_event names its pass")

    # refresh
    rf = rec.get("refresh") or {}
    cls = core["refresh_classes"].get(rf.get("class")) if isinstance(rf, dict) else None
    if not isinstance(cls, dict) or rf.get("class") in ("policy", "budget_meaning"):
        problems.append(f"{w}: refresh.class {rf.get('class') if isinstance(rf, dict) else rf!r} is not a refresh class")
    elif "budget_s" in rf:
        if not _num(rf["budget_s"]) or rf["budget_s"] <= 0:
            problems.append(f"{w}: refresh.budget_s must be a positive number of seconds")
        if not evidence_ok(rf.get("evidence"), core):
            problems.append(f"{w}: refresh.budget_s needs an evidence string with a tag")
    elif not is_param(cls.get("budget_s")):
        problems.append(f"{w}: refresh has no budget (neither its own nor one of the class)")

    # degraded states
    levels = dc["degraded"]["levels"]
    deg = rec.get("degraded") or {}
    for lv in levels:
        if not _text(deg.get(lv) if isinstance(deg, dict) else None):
            problems.append(f"{w}: degraded state {lv} is missing")
    for lv in (deg if isinstance(deg, dict) else {}):
        if lv not in levels:
            problems.append(f"{w}: degraded state {lv!r} is not a level")

    # elements
    ident = dc["identity"]
    id_fields = {refs.ls_key(f) for f in ident["live_state_fields"]}
    id_col = re.compile(ident["column_pattern"])
    banned_col = re.compile(ident["banned_column_pattern"])
    grades = refs.grades()
    all_levels = refs.levels()
    review_views = dc["grades"].get("review_views") or []
    elements = rec.get("elements") or []
    if not isinstance(elements, list) or not elements:
        problems.append(f"{w}: has no elements")
        elements = []
    keys, used_ls, used_tables, used = [], set(), set(), {k: set() for k in ("metrics", "spots", "events")}
    cited = set(rec.get("requirements") or [])
    needs_identity = False
    for i, el in enumerate(elements):
        if not isinstance(el, dict):
            problems.append(f"{w} element {i + 1}: must be a mapping")
            continue
        we = f"{w} element {el.get('key', i + 1)}"
        keys.append(el.get("key"))
        for k in el:
            if k not in vr["element_keys"]:
                problems.append(f"{we}: unknown key {k!r}" + (" (YAML reads a bare on, yes or no as a boolean; use another word)" if isinstance(k, bool) else ""))
        if not _text(el.get("key")) or not _text(el.get("shows")):
            problems.append(f"{we}: needs key and shows")
        if el.get("kind") not in conv["element_kinds"]:
            problems.append(f"{we}: kind {el.get('kind')!r} is not one of {conv['element_kinds']}")
        if "inputs" not in el:
            problems.append(f"{we}: lacks inputs (write inputs: {{}} for a control with none)")
        if "phase" in el and el["phase"] not in conv["phases"]:
            problems.append(f"{we}: phase {el['phase']!r} is not a phase")
        if "layers" in el and not (isinstance(el["layers"], list) and all(_text(x) for x in el["layers"])):
            problems.append(f"{we}: layers must be a list of layer names")
        comp = el.get("component")
        if comp is not None:
            if comp not in core["components"]:
                problems.append(f"{we}: component {comp!r} does not exist")
            elif core["components"][comp].get("kind") != el.get("kind"):
                problems.append(f"{we}: component {comp} is a {core['components'][comp].get('kind')}, the element says {el.get('kind')}")
        emb = el.get("embeds")
        if emb is not None and (emb not in index or emb == key):
            problems.append(f"{we}: embeds {emb!r}, which is not another view of the index")
        own = check_inputs(we, el.get("inputs"), refs, problems, banned_col)
        merged = check_inputs(we, element_inputs(el, core), refs, [], None)
        used_ls |= merged["live_state"]
        used_tables |= merged["tables"]
        for k in used:
            used[k] |= merged[k]
        has_data = any(merged[k] for k in ("live_state", "tables", "metrics")) or emb is not None
        if el.get("kind") == "court" and not merged["spots"] and emb is None:
            problems.append(f"{we}: a court names the named-spots layers or ids it draws (rule 6: the court is drawn from config/named_spots.yaml)")

        # as-of of the element
        el_as_of = el.get("as_of")
        if el_as_of is not None and el_as_of not in AS_OF:
            problems.append(f"{we}: as_of {el_as_of!r} must be as_of_known or as_of_event")
        if rec.get("surface") == "live_panel" and el_as_of == "as_of_event":
            problems.append(f"{we}: an element of a live_panel view cannot read as_of_event")
        if view_as_of == "mixed" and el_as_of is None and has_data and el.get("kind") != "control":
            problems.append(f"{we}: the view is mixed, so the element states its as_of")
        if emb in index and index[emb].get("surface") == "live_panel" and (el_as_of or view_as_of) != "as_of_known":
            problems.append(f"{we}: an embedded live panel reads as_of_known")
        effective = el_as_of or view_as_of

        # numbers and grades
        if shows_number(el):
            _check_number_rule(we, el, core, problems)
        elif "number_rule" in el and el.get("numbers") == "none":
            problems.append(f"{we}: says numbers: none but has a number_rule")
        gr = el.get("grade_rule")
        if has_data and gr is None and el.get("kind") != "control":
            problems.append(f"{we}: lacks grade_rule (the word contract, or the overrides)")
        if isinstance(gr, dict):
            for g in gr:
                if g not in grades:
                    problems.append(f"{we}: grade_rule names {g!r}, which is not a grade")
            if "quarantined" in gr and key not in review_views:
                problems.append(f"{we}: only the review screens may show a quarantined value")
        elif gr is not None and gr != "contract":
            problems.append(f"{we}: grade_rule must be the word contract or a mapping of grades")
        for g in (el.get("by_grade") or {}):
            if g not in grades:
                problems.append(f"{we}: by_grade names {g!r}, which is not a grade")
        if "quarantined" in (el.get("by_grade") or {}) and key not in review_views and "unknown" not in str(el["by_grade"]["quarantined"]).lower() and "dash" not in str(el["by_grade"]["quarantined"]).lower():
            problems.append(f"{we}: by_grade.quarantined must say the value is hidden (shown as unknown)")
        for lv in (el.get("by_level") or {}):
            if lv not in all_levels:
                problems.append(f"{we}: by_level names {lv!r}, which is not a degradation level")
        if rec.get("covers_all_live_state") and own["live_state"] and list(el.get("by_level") or {}) != all_levels:
            problems.append(f"{we}: by_level must say what the tile shows at each of {all_levels}, in that order")
        if rec.get("covers_all_live_state") and own["live_state"] and el.get("kind") != "control" and list(el.get("by_grade") or {}) != grades:
            problems.append(f"{we}: by_grade must say what the tile shows at each of {grades}, in that order")

        # identity
        reads_identity = bool(merged["live_state"] & id_fields) or any(id_col.search(c.partition(".")[2]) for c in merged["columns"])
        rule = el.get("identity_rule")
        if reads_identity or rule is not None:
            needs_identity = True
            if rule not in ident["rules"]:
                problems.append(f"{we}: reads player identity, so identity_rule must be one of {list(ident['rules'])}")
            elif rule == "probable_flagged_offline":
                if rec.get("surface") == "live_panel" or effective == "as_of_known":
                    problems.append(f"{we}: the probable tier is offline only; a live or as_of_known element shows locked or HOLD (OD-10)")
                if el.get("kind") not in ("video", "court", "overlay"):
                    problems.append(f"{we}: a probable label may appear on video, court and overlay layers only, never in a {el.get('kind')} (OD-8)")

        # privacy of the element
        if pclass and not pclass.get("video") and (el.get("kind") == "video" or comp == "video_player"):
            problems.append(f"{we}: a view of privacy class {rec.get('privacy')} cannot show video")
        for rid in el.get("requirements") or []:
            if not REQ_RE.match(str(rid)):
                problems.append(f"{we}: {rid!r} is not a requirement id")
            cited.add(rid)
    if len(set(keys)) != len(keys):
        problems.append(f"{w}: an element key is written twice")

    # all live-state fields (the live panel)
    if rec.get("covers_all_live_state"):
        own_ls = set()
        for el in elements:
            for ref in ((el.get("inputs") or {}).get("live_state") or []) if isinstance(el, dict) else []:
                own_ls.add(refs.ls_key(ref))
        not_shown = rec.get("not_shown") or {}
        for f in refs.ls_index():
            if f not in own_ls and not _text(not_shown.get(f)):
                problems.append(f"{w}: live-state field {f} is in no element and not in not_shown")
        for f in not_shown:
            if refs.ls_key(f) is None or refs.ls_key(f) in own_ls:
                problems.append(f"{w}: not_shown names {f!r}, which is unknown or shown")

    # interactions
    inter = rec.get("interactions") or []
    if not isinstance(inter, list) or not inter:
        problems.append(f"{w}: has no interaction (every number at least links to its frames, R-VZ-02)")
        inter = []
    actions = core["interaction_grammar"]["actions"]
    for i, it in enumerate(inter):
        wi = f"{w} interaction {i + 1}"
        if not isinstance(it, dict) or it.get("action") not in actions:
            problems.append(f"{wi}: action {it.get('action') if isinstance(it, dict) else it!r} is not in the interaction grammar")
            continue
        for k in it:
            if k not in vr["interaction_keys"]:
                problems.append(f"{wi}: unknown key {k!r}" + (" (YAML reads a bare on, yes or no as a boolean; write at)" if isinstance(k, bool) else ""))
        if it.get("at") != "view" and it.get("at") not in keys:
            problems.append(f"{wi}: at {it.get('at')!r} is neither the word view nor an element key")
        if not _text(it.get("target")):
            problems.append(f"{wi}: target is missing")
        if "to" in it and it["to"] not in index:
            problems.append(f"{wi}: to {it['to']!r} is not a view of the index")
        if it["action"] == "export":
            if it.get("produces") not in dc["privacy"]["exports"]:
                problems.append(f"{wi}: export produces {it.get('produces')!r}, not one of {list(dc['privacy']['exports'])}")
            elif pclass and it["produces"] not in pclass.get("exports", []):
                problems.append(f"{wi}: privacy class {rec.get('privacy')} does not allow the export {it['produces']}")
        elif "produces" in it:
            problems.append(f"{wi}: only an export has produces")
    if not any(isinstance(it, dict) and it.get("action") in ("drill_down", "select") for it in inter):
        problems.append(f"{w}: no select or drill_down interaction, so a number cannot be followed to its frames (R-VZ-02)")

    # requirements and the inventory
    reqs = rec.get("requirements") or []
    if not reqs:
        problems.append(f"{w}: cites no requirement")
    for rid in reqs:
        if not REQ_RE.match(str(rid)):
            problems.append(f"{w}: {rid!r} is not a requirement id")
    for r in core["inventory"]["rows"]:
        if r.get("view") != key:
            continue
        if "element" in r and r["element"] not in keys:
            problems.append(f"{w}: the inventory expects an element {r['element']!r} ({r.get('item')})")
        for rid in r.get("req") or []:
            if rid not in cited:
                problems.append(f"{w}: the inventory assigns {rid} ({r.get('item')}) but the record does not cite it")

    # depends_on
    dep = rec.get("depends_on") or {}
    if not isinstance(dep, dict):
        problems.append(f"{w}: depends_on must be {{baselines: [...], tables: [...]}}")
        dep = {}
    declared_b = set(dep.get("baselines") or [])
    for b in declared_b:
        if b not in conv["baselines"]:
            problems.append(f"{w}: depends_on names the baseline {b!r}, not one of {conv['baselines']}")
    need_b = set()
    embeds_live = any(isinstance(el, dict) and index.get(el.get("embeds"), {}).get("surface") == "live_panel" for el in elements)
    if used_ls or embeds_live:
        need_b.add("live_state")
    if used["metrics"]:
        need_b.add("metrics")
    if used["spots"]:
        need_b.add("named_spots")
    if "grammar" in used["events"]:
        need_b.add("movement_grammar")
    if used["events"] & {"transition", "dimension"}:
        need_b.add("state_machine")
    if needs_identity:
        need_b.add("identity_pack")
    for b in sorted(need_b - declared_b):
        problems.append(f"{w}: reads the baseline {b} but depends_on does not name it")
    declared_t = set(dep.get("tables") or [])
    for t in sorted(declared_t):
        if not refs.table_known(t):
            problems.append(f"{w}: depends_on names the table {t!r}, which is not in schema/tables or a schema/*_changes.yaml file")
    for t in sorted(used_tables - declared_t):
        problems.append(f"{w}: reads the table {t} but depends_on does not name it")

    # acceptance, wireframe, empty state, units, params
    acc = {a["id"] for a in core["acceptance"]}
    if not rec.get("acceptance"):
        problems.append(f"{w}: names no acceptance test")
    for a in rec.get("acceptance") or []:
        if a not in acc:
            problems.append(f"{w}: acceptance {a!r} is not defined in core.yaml")
    wf = rec.get("wireframe")
    if wf is not None and not (isinstance(wf, str) and wf.startswith("docs/data/views/") and wf.endswith(".svg")):
        problems.append(f"{w}: wireframe must be docs/data/views/<file>.svg or null")
    states = rec.get("wireframe_states")
    if states is not None:
        if not isinstance(states, dict) or not states or wf is None:
            problems.append(f"{w}: wireframe_states must be a mapping of level to file, beside a wireframe of the view at D0")
        else:
            for lv, path in states.items():
                if lv not in levels:
                    problems.append(f"{w}: wireframe_states names {lv!r}, which is not a degradation level")
                if not (isinstance(path, str) and path.startswith("docs/data/views/") and path.endswith(".svg")) or path == wf:
                    problems.append(f"{w}: wireframe_states.{lv} must be its own docs/data/views/<file>.svg")
    if not _text(rec.get("empty_state")):
        problems.append(f"{w}: empty_state is missing (no view goes blank without saying why)")
    if "min_width_px" in rec and not _num(rec["min_width_px"]):
        problems.append(f"{w}: min_width_px must be a number")
    problems.extend(f"{w} {p}" for p in unit_problems(rec, dc["visual_standard"].get("banned_units") or []))
    for path, p in iter_params(rec):
        check_param(f"{w} {path}", p, core, problems)


# --------------------------------------------------------------------------------------------------------------------
def validate(core=None, views=None, require_all=True):
    """-> list of problems. require_all: every index entry must have a record (the whole pack)."""
    core = core if core is not None else load_core()
    views = views if views is not None else load_views()
    refs = Refs()
    problems = []
    _validate_core(core, refs, problems)
    if any(p.startswith("core: section") for p in problems):
        return problems
    ids = {}
    for key, rec in views.items():
        _validate_view(key, rec, core, refs, problems)
        if rec.get("id") in ids:
            problems.append(f"view {key}: id {rec.get('id')} is also the id of {ids[rec.get('id')]}")
        ids[rec.get("id")] = key
    if require_all:
        for key, e in core["view_index"].items():
            if key not in views:
                problems.append(f"{MISSING} {key} ({e.get('id')}) has no record in {e.get('file')}.yaml")
        if not any(p.startswith(MISSING) for p in problems):
            cited = {m.split("-")[1] for rec in views.values() for el in rec.get("elements") or [] if isinstance(el, dict)
                     for m in (el.get("inputs") or {}).get("metrics") or [] if isinstance(m, str) and m.count("-") == 2}
            for code in sorted(refs.metric_categories() - cited):
                problems.append(f"whole pack: no view reads a metric of the registry category {code}")
            cov = requirement_coverage(views)
            inv = core["inventory"]
            for rid in inv.get("reported_rows") or []:
                if rid in (inv.get("no_view_rows") or {}):
                    if cov.get(rid):
                        problems.append(f"inventory.no_view_rows.{rid}: the row is cited by {sorted(cov[rid])[0]}; drop the reason")
                elif not cov.get(rid):
                    problems.append(f"inventory: reported row {rid} is cited by no record and has no reason in no_view_rows")
    return problems


def requirement_coverage(views):
    """{requirement id: set of view keys whose record or elements cite it}."""
    cov = {}
    for key, rec in views.items():
        for rid in rec.get("requirements") or []:
            cov.setdefault(rid, set()).add(key)
        for el in rec.get("elements") or []:
            for rid in (el.get("requirements") or []) if isinstance(el, dict) else []:
                cov.setdefault(rid, set()).add(key)
    return cov


def good_copy(views, key):
    """A deep copy of one loaded record, for tests that break it on purpose."""
    return {key: copy.deepcopy(views[key])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", nargs="?", const="ALL", default="ALL", help="a views file to check on its own; default: the whole pack")
    ap.add_argument("--palette", action="store_true", help="print the computed contrast ratio of every palette pair and stop")
    a = ap.parse_args()
    try:
        core = load_core()
        if a.palette:
            for kind, x, y, theme, ratio in palette_table(core):
                print(f"{kind:12s} {x:26s} on {y:10s} {theme:5s} {ratio:6.2f}")
            return
        views = load_views() if a.check == "ALL" else load_views([a.check])
    except (FileNotFoundError, ValueError, yaml.YAMLError) as e:  # a missing file, a view written twice, broken YAML
        print("FAIL", " ".join(str(e).split()))
        sys.exit(2)
    require_all = a.check == "ALL"
    if not require_all and not views:
        print(f"FAIL {a.check} holds no view records")
        sys.exit(2)
    problems = validate(core, views, require_all=require_all)
    for p in problems:
        print("FAIL", p)
    missing = sum(p.startswith(MISSING) for p in problems)
    print(f"{len(views)} views checked, {len(problems)} problems" + (f" ({missing} index entries without a record)" if missing else ""))
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
