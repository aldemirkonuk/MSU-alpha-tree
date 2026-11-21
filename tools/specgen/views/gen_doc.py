"""Generate the two pages of the views catalogue from config/views/*.yaml and schema/views_changes.yaml.

docs/data/views_catalogue.md            the page to read: contract, map, every view with its inputs by id, coverage,
                                        phases, open questions, follow-ups, journal (prose from doc_template.md)
docs/data/views_catalogue_reference.md  the rules of every element in full: number rule, grade rule, every grade and
                                        level, interactions, definitions, the inventory and the metrics read

The catalogue is two pages because a rendered Markdown page is cut off near 500 KiB; the first page must stay under
MAX_PAGE_BYTES so that its last sections (the open questions) are never cut.

Usage: python tools/specgen/views/gen_doc.py [--out-dir docs/data] [--check]
--check regenerates in memory and exits non-zero if a file on disk differs (used by the tests).
Before writing, the script lints the pack and checks that every view id, element key, component, contract rule,
acceptance id, open question, follow-up and wireframe appears and that no {{PLACEHOLDER}} is left.
"""
from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import vwlib  # noqa: E402

ROOT = vwlib.REPO
OUT_DIR = ROOT / "docs" / "data"
PAGE, REFERENCE = "views_catalogue.md", "views_catalogue_reference.md"
MAX_PAGE_BYTES = 450_000   # a rendered Markdown page is cut off near 500 KiB (published: GitHub truncates a README beyond 500 KiB)
TEMPLATE = HERE / "doc_template.md"
WIRE_DIR = ROOT / "docs" / "data" / "views"
SURFACE_TITLE = {"live_panel": "Live panel", "review": "Review and film room", "studio": "Analyst Studio and review screens",
                 "report": "Reports and packets", "card": "Cards"}
AS_OF_WORDS = {"as_of_known": "as known", "as_of_event": "as of event", "mixed": "mixed (each element says which)"}
LEVEL_WORDS = {"D0_full": "D0 full", "D1_bug_away": "D1 bug away", "D2_off_main": "D2 off the main camera", "D3_replay": "D3 replay", "D4_break": "D4 break",
               "D5_no_video": "D5 no video", "feed_stale": "feed stale"}


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


ALLOWED_TAG = re.compile(r"<(?!(?:br>|/?details>|/?summary>|/?b>|/?p>|img ))")


def html_safe(text):
    """A bare < in prose ("<n> s ago") would be read as a tag and vanish; write it as an entity. Our own tags stay."""
    return ALLOWED_TAG.sub("&lt;", text)


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        assert len(r) == len(header), (header, r)
        out.append("| " + " | ".join(esc(x) for x in r) + " |")
    return "\n".join(out)


def code(x):
    return f"`{x}`"


def codes(xs):
    return ", ".join(code(x) for x in xs)


def bullets(xs):
    return "\n".join(f"- {x}" for x in xs)


def slug(heading):
    """The anchor GitHub gives a heading."""
    s = re.sub(r"[^a-z0-9 \-]", "", heading.lower())
    return s.replace(" ", "-")


def num(v):
    return f"{v:g}" if isinstance(v, float) else str(v)


def params_table(block):
    rows = [[code(k), num(p["value"]), p["unit"], p["why"], p["evidence"]] for k, p in block.items()]
    return table(["Parameter", "Value", "Unit", "Why", "Evidence"], rows)


class Doc:
    def __init__(self):
        self.core = vwlib.load_core()
        self.views = vwlib.load_views()
        self.refs = vwlib.Refs()
        self.dc = self.core["display_contract"]
        self.index = self.core["view_index"]
        self.ls = self.refs.ls_index()
        self.changes = vwlib.load_yaml_strict(vwlib.CHANGES)
        self.metric_names = {m["id"]: m["name"] for c in vwlib._yaml(vwlib.METRICS)["categories"] for m in c.get("metrics") or []}
        self.acc = {a["id"]: a for a in self.core["acceptance"]}

    # small pieces -------------------------------------------------------------------------------------------
    def heading(self, key):
        e = self.index[key]
        return f"{e['id']} {e['name']}"

    def link(self, key):
        return f"[{self.index[key]['id']}](#{slug(self.heading(key))})"

    def budget(self, rec):
        rf = rec["refresh"]
        cls = self.core["refresh_classes"][rf["class"]]
        b = rf.get("budget_s", cls["budget_s"]["value"])
        return f"{code(rf['class'])}, budget {num(float(b))} s" + (" (own budget)" if "budget_s" in rf else "")

    def as_of(self, rec):
        a = rec["as_of"]
        return AS_OF_WORDS[a["view"]] + (f"; pass {', '.join(a['pass'])}" if a.get("pass") else "")

    def inputs_cell(self, el):
        inp = el.get("inputs") or {}
        parts = []
        if inp.get("live_state"):
            parts.append("**live state** " + ", ".join(f"{code(self.refs.ls_key(k))} ({self.ls[self.refs.ls_key(k)]['id']})" for k in inp["live_state"]))
        if inp.get("tables"):
            by = {}
            for ref in inp["tables"]:
                t, _, c = ref.partition(".")
                by.setdefault(t, []).append(c + ("\u2020" if self.refs.column_state(ref) == "proposed" else ""))
            parts.append("**tables** " + "; ".join(f"{code(t)}: {', '.join(cs)}" for t, cs in by.items()))
        if inp.get("metrics"):
            parts.append("**metrics** " + codes(inp["metrics"]))
        if inp.get("spots"):
            parts.append("**spots** " + codes(inp["spots"]))
        if inp.get("events"):
            parts.append("**events** " + codes(inp["events"]))
        if el.get("component"):
            parts.append(f"plus the inputs of component {code(el['component'])}")
        if el.get("embeds"):
            parts.append(f"embeds {self.link(el['embeds'])}")
        return "<br>".join(parts) if parts else "none"

    @staticmethod
    def number_cell(el, full=True):
        rule = el.get("number_rule")
        if rule is None:
            return "no number"
        blocks = rule if isinstance(rule, list) else [rule]
        if not full:
            return ", ".join(code(b["class"]) for b in blocks)
        return "<br>".join(f"**{b['class']}**: " + "; ".join(f"{k} = {v}" for k, v in b.items() if k != "class") for b in blocks)

    @staticmethod
    def grade_cell(el, full=True):
        g = el.get("grade_rule")
        if g is None:
            return "n/a (control)" if el["kind"] == "control" else "n/a (no data)"
        if g == "contract":
            return "contract"
        if not full:
            return "contract, except " + ", ".join(g)
        return "contract, except<br>" + "<br>".join(f"**{k}**: {v}" for k, v in g.items())

    def shows_cell(self, el):
        tags = []
        if el.get("as_of"):
            tags.append(AS_OF_WORDS[el["as_of"]])
        if el.get("identity_rule"):
            tags.append(f"identity {code(el['identity_rule'])}")
        if el.get("phase"):
            tags.append(f"from {el['phase']}")
        if el.get("layers"):
            tags.append("layers: " + ", ".join(el["layers"]))
        if el.get("requirements"):
            tags.append(", ".join(el["requirements"]))
        return el["shows"] + ("<br>" + " \u00b7 ".join(tags) if tags else "")

    @staticmethod
    def more_cell(el):
        out = [f"*{d}*" for d in el.get("definitions") or []]
        if el.get("notes"):
            out.append(f"Note: {' '.join(str(el['notes']).split())}")
        return "<br>".join(out)

    def drawn_keys(self, path):
        root = ET.parse(ROOT / path).getroot()
        return [t.text for t in root.iter("{http://www.w3.org/2000/svg}text") if t.get("class") == "key"]

    # one view -----------------------------------------------------------------------------------------------
    def view_block(self, key):
        rec = self.views[key]
        surface = rec["surface"]
        o = [f"### {self.heading(key)}", "", f"**Question.** {rec['question']}", ""]
        o.append(table(["Audience", "Privacy", "Grain", "As-of", "Refresh", "Width", "First phase", "File"],
                       [[", ".join(rec["audience"]), code(rec["privacy"]), rec["grain"], self.as_of(rec), self.budget(rec), f"{rec['min_width_px']} px",
                         rec["phase"], f"`{rec['_file']}.yaml`, key `{key}`"]]))
        o.append("")
        if rec.get("wireframe"):
            states = rec.get("wireframe_states") or {}
            name = Path(rec["wireframe"]).name
            if states:
                files = [("D0_full", rec["wireframe"])] + list(states.items())
                o.append("<p>" + " ".join(f'<img src="views/{Path(p).name}" alt="{rec["id"]} wireframe at {LEVEL_WORDS[lv]}" width="32%">' for lv, p in files) + "</p>")
                o.append("")
                o.append("Left to right: " + ", ".join(f"{LEVEL_WORDS[lv]} ([`{Path(p).name}`](views/{Path(p).name}))" for lv, p in files)
                         + ". The tiles keep their place and size at every level; only their marks change.")
            else:
                o.append(f"![{rec['id']} wireframe](views/{name})")
                o.append("")
                o.append(f"Wireframe: [`{name}`](views/{name}).")
            drawn = self.drawn_keys(rec["wireframe"])
            missing = [e["key"] for e in rec["elements"] if e["key"] not in drawn]
            o.append(f"Drawn with their keys: {codes(drawn)}." + (f" Not drawn: {codes(missing)}." if missing else " Every element is drawn."))
            o.append("")
        else:
            o += ["No wireframe yet.", ""]

        # degraded states and the empty state
        defaults = self.dc["degraded"]["defaults"][surface]
        rows = []
        for lv in self.dc["degraded"]["levels"]:
            t = rec["degraded"][lv]
            rows.append([LEVEL_WORDS[lv], f"{defaults[lv]} *(surface default)*" if t == "default" else t])
        o += ["**When data is missing or unsure**", "", table(["Level", "What the view shows"], rows), "", f"**Empty state.** {rec['empty_state']}", ""]

        # elements
        els = rec["elements"]
        o += [f"<details><summary><b>Elements ({len(els)}) and their inputs by id</b></summary>", ""]
        o.append(table(["Element", "Kind", "Shows", "Inputs by id", "Number class", "Grade rule"],
                       [[code(e["key"]), e["kind"], self.shows_cell(e), self.inputs_cell(e), self.number_cell(e, full=False), self.grade_cell(e, full=False)] for e in els]))
        o += ["", "\u2020 a column that exists only as a proposal in a `schema/*_changes.yaml` file.", "", "</details>", ""]
        if rec.get("params"):
            o += ["**Parameters**", "", params_table(rec["params"]), ""]
        dep = rec["depends_on"]
        facts = [["Requirements", ", ".join(rec["requirements"])]]
        if rec.get("decisions"):
            facts.append(["Decisions", ", ".join(rec["decisions"])])
        facts.append(["Depends on", "baselines " + ", ".join(dep.get("baselines") or ["none"]) + "; tables " + (codes(dep.get("tables") or []) or "none")])
        facts.append(["Acceptance", ", ".join(rec["acceptance"])])
        facts.append(["In full", f"[number and grade rule of every element, interactions, definitions]({REFERENCE}#{slug(self.heading(key))})"])
        o += [table(["", ""], facts), ""]
        if rec.get("notes"):
            o += [f"**Notes.** {' '.join(str(rec['notes']).split())}", ""]
        return "\n".join(o)

    def reference_block(self, key):
        """The same view on the reference page: every rule in full."""
        rec = self.views[key]
        els = rec["elements"]
        o = [f"### {self.heading(key)}", "", f"Entry on the catalogue page: [{rec['id']}]({PAGE}#{slug(self.heading(key))}). {rec['question']}", ""]
        if rec.get("definitions"):
            o += ["**Definitions**", "", bullets(rec["definitions"]), ""]
        o += ["**Elements: the rules in full**", "",
              table(["Element", "Number rule", "Grade rule", "Definitions and notes"], [[code(e["key"]), self.number_cell(e), self.grade_cell(e), self.more_cell(e)] for e in els]), ""]
        graded = [e for e in els if e.get("by_grade") or e.get("by_level")]
        if graded:
            o += [f"**Every element at every grade and level ({len(graded)})**", ""]
            for e in graded:
                rows = [[f"grade {g}", t] for g, t in (e.get("by_grade") or {}).items()] + [[LEVEL_WORDS[lv], t] for lv, t in (e.get("by_level") or {}).items()]
                o += [f"{code(e['key'])}", "", table(["At", "Shows"], rows), ""]
        rows = []
        for it in rec["interactions"]:
            to = f" \u2192 [{self.index[it['to']]['id']}](#{slug(self.heading(it['to']))})" if it.get("to") else ""
            prod = f" (produces {code(it['produces'])})" if it.get("produces") else ""
            rows.append([code(it["action"]), "the view" if it["at"] == "view" else code(it["at"]), f"{it['target']}{to}{prod}" + (f" {it['notes']}" if it.get("notes") else "")])
        o += [f"**Interactions ({len(rows)})**", "", table(["Action", "At", "Target"], rows), ""]
        if rec.get("not_shown"):
            o += ["**Live-state fields not shown**", "", bullets(f"{code(k)}: {v}" for k, v in rec["not_shown"].items()), ""]
        return "\n".join(o)

    # sections -----------------------------------------------------------------------------------------------
    def counts(self):
        views, core = self.views, self.core
        per = {}
        for rec in views.values():
            per[rec["surface"]] = per.get(rec["surface"], 0) + 1
        els = [e for r in views.values() for e in r["elements"]]
        used = {k: set() for k in vwlib.INPUT_KEYS}
        for e in els:
            for k in vwlib.INPUT_KEYS:
                used[k].update((e.get("inputs") or {}).get(k) or [])
        ls = {self.refs.ls_key(k) for k in used["live_state"]}
        proposed = [c for c in used["tables"] if self.refs.column_state(c) == "proposed"]
        wires = sum(1 for r in views.values() if r.get("wireframe")) + sum(len(r.get("wireframe_states") or {}) for r in views.values())
        now = sum(1 for a in core["acceptance"] if a["runnable_now"])
        rows = [["Views", f"{len(views)} ({', '.join(f'{s.replace(chr(95), chr(32))} {per.get(s, 0)}' for s in core['surfaces'])})"],
                ["Elements", str(len(els))],
                ["Live-state fields read", f"{len(ls)} of {len(self.ls)}"],
                ["Table columns read", f"{len(used['tables'])} in {len({c.partition('.')[0] for c in used['tables']})} tables; {len(proposed)} exist only as proposals"],
                ["Metrics read", f"{len(used['metrics'])} of {len(self.metric_names)} in the registry, from all {len(self.refs.metric_categories())} categories"],
                ["Named-spots ids and layers, events", f"{len(used['spots'])} and {len(used['events'])}"],
                ["Wireframes", f"{wires} drawings of {sum(1 for r in views.values() if r.get('wireframe'))} views, and the grade legend"],
                ["Acceptance tests", f"{len(core['acceptance'])}, of which {now} run now"],
                ["Open questions", f"{len(core['open_questions'])}, each with a recommended answer"]]
        return table(["What", "Count"], rows)

    def grade_table(self):
        rows = [[g, a["in_words"], a["tile_edge"], a["court_marker"], "none" if a["badge"] == "none" else f"\"{self.dc['grades']['badge_texts'][a['badge']]}\"",
                 "every view" if a["visible_in"] == "all" else "the review screens only"] for g, a in self.dc["grades"]["appearance"].items()]
        return table(["Grade", "How it looks", "Tile edge", "Court marker", "Badge", "Shown in"], rows)

    def identity(self):
        i = self.dc["identity"]
        return bullets([f"**Locked or HOLD.** {i['rules']['locked_or_hold']}", f"**Probable, flagged, offline.** {i['rules']['probable_flagged_offline']}",
                        f"**HOLD on screen.** {i['hold_display']}", f"**No face.** {i['no_face']}", f"Source: {i['source']}"])

    def number_classes(self):
        rows = [[code(k), c["what"], ", ".join(c["must_show"]), ", ".join(c["needs"]), c["example"]] for k, c in self.dc["numbers"]["classes"].items()]
        links = bullets(f"{code(k)}: {v}" for k, v in self.dc["numbers"]["link_kinds"].items())
        return table(["Class", "What it is", "Must show beside it", "Also needs", "Example"], rows) + "\n\nWhat a number links to:\n\n" + links

    def as_of_section(self):
        a = self.dc["as_of"]
        return bullets(f"**{k}.** {v}" for k, v in a["rules"].items()) + f"\n\nPasses: {', '.join(a['passes'])}. Source: {a['source']}"

    def degraded_defaults(self):
        d = self.dc["degraded"]["defaults"]
        return table(["Level"] + [SURFACE_TITLE[s] for s in d], [[LEVEL_WORDS[lv]] + [d[s][lv] for s in d] for lv in self.dc["degraded"]["levels"]])

    def visual(self):
        vs = self.dc["visual_standard"]
        o = [f"**Labels.** {vs['labels']}", "", f"**Court.** {vs['court']}", ""]
        cd = vs["court_drawing"]
        o += [f"**Which way up.** Orientation `{cd['orientation']}`: {cd['options'][cd['orientation']]} {cd['why']} ({cd['status']})", ""]
        o += ["**Colour rules**", "", bullets(vs["colour_rules"]), ""]
        names = list(vs["themes"]["light"])
        o += ["**Tokens**", "", table(["Token", "Light", "Dark"], [[code(k), vs["themes"]["light"][k], vs["themes"]["dark"][k]] for k in names]
                                      + [[code(k), v, v] for k, v in vs["shared_tokens"].items()]), ""]
        o += ["**Contrast of every text pair** (WCAG 2.1; the lint recomputes each ratio)", "",
              table(["Text", "On", "Light", "Dark"], [[code(p["text"]), code(p["bg"]), f"{p['ratio']['light']:.2f}", f"{p['ratio']['dark']:.2f}"] for p in vs["text_pairs"]]), ""]
        o += ["**Marks on the chart surface**", "", table(["Mark", "On", "Ratio"], [[code(p["mark"]), code(p["bg"]), f"{p['ratio']['dark']:.2f}"] for p in vs["graphic_pairs"]]), ""]
        cat = vs["categorical"]
        o += [f"**Categorical set** ({cat['source']})", "",
              table(["Slot", "Name", "Hex", "Ratio on the chart surface"], [[c["slot"], c["name"], c["hex"], f"{c['ratio_on_chart']:.2f}"] for c in cat["set"]]), "",
              f"Second channel beside colour: {', '.join(cat['second_channel'])}. {cat['on_light_note']}", ""]
        for k in ("sequential", "diverging"):
            sc = vs[k]
            o += [f"**{k.capitalize()} scale: {sc['name']}.** {sc['use']} Stops: {' '.join(sc['stops'])}. {sc['source']}", ""]
        o += ["**Team marks.** " + "; ".join(f"{t}: {m['shape']}, {code(m['token'])}, label {code(m['label_text'])}" for t, m in vs["team_marks"].items()) + ".", ""]
        o += ["**Text sizes**", "", params_table(vs["text_sizes"]), "", "**Limits**", "", params_table(vs["params"]), ""]
        o += ["**Width rules**", "", bullets(f"{code(k)}: {v}" for k, v in vs["width_rules"].items()), "", f"Units never shown: {', '.join(vs['banned_units'])}."]
        return "\n".join(o)

    def privacy(self):
        p = self.dc["privacy"]
        rows = [[code(k), ", ".join(c["audiences"]), "yes" if c["video"] else "no", "yes" if c["player_level"] else "no", codes(c["exports"])] for k, c in p["classes"].items()]
        return bullets(p["rules"]) + "\n\n" + table(["Class", "Who may see it", "Video", "Player-level output", "May export"], rows) \
            + "\n\nExport kinds:\n\n" + bullets(f"{code(k)}: {v}" for k, v in p["exports"].items())

    def surfaces(self):
        rows = []
        for s, spec in self.core["surfaces"].items():
            keys = [k for k, e in self.index.items() if e["surface"] == s]
            rows.append([f"[{SURFACE_TITLE[s]}](#{slug(SURFACE_SECTION[s])})", spec["code"], spec["what"], ", ".join(AS_OF_WORDS[a].split(" (")[0] for a in spec["as_of_allowed"]),
                         spec["width_rule"], code(spec["refresh_default"]), str(len(keys))])
        return table(["Surface", "Code", "What it is", "As-of allowed", "Width", "Default refresh", "Views"], rows)

    def view_map(self):
        rows = []
        for key, e in self.index.items():
            rec = self.views[key]
            wf = "none"
            if rec.get("wireframe"):
                files = [rec["wireframe"]] + list((rec.get("wireframe_states") or {}).values())
                wf = ", ".join(f"[{Path(p).stem}](views/{Path(p).name})" for p in files)
            rows.append([f"[{e['id']}](#{slug(self.heading(key))})", e["name"], rec["question"], ", ".join(rec["audience"]), rec["grain"], rec["phase"], wf])
        return table(["Id", "View", "The one question", "Audience", "Grain", "Phase", "Wireframe"], rows)

    def surface_section(self, surface):
        keys = [k for k, e in self.index.items() if e["surface"] == surface]
        spec = self.core["surfaces"][surface]
        head = f"{spec['what']} {len(keys)} view{'s' if len(keys) != 1 else ''}: " + ", ".join(self.link(k) + " " + self.index[k]["name"] for k in keys) + "."
        return head + "\n\n" + "\n\n".join(self.view_block(k) for k in keys)

    def components(self):
        o = []
        used = {}
        for key, rec in self.views.items():
            for e in rec["elements"]:
                if e.get("component"):
                    used.setdefault(e["component"], set()).add(key)
        for name, c in self.core["components"].items():
            o += [f"**{code(name)}** ({c['kind']}). {c['purpose']} Used by {len(used.get(name, ()))} views. Requirements: {', '.join(c['requirements'])}.", "",
                  bullets(c["behaviour"]), ""]
            inp = self.inputs_cell({"inputs": c.get("inputs") or {}})
            if inp != "none":
                o += [f"Inputs: {inp.replace('<br>', '; ')}", ""]
            if c.get("params"):
                o += [params_table(c["params"]), ""]
        return "\n".join(o)

    def refresh(self):
        rc = self.core["refresh_classes"]
        rows = []
        for k, r in rc.items():
            if k in ("policy", "budget_meaning"):
                continue
            n_views = sum(1 for v in self.views.values() if v["refresh"]["class"] == k)
            b = r["budget_s"]
            rows.append([code(k), r["trigger"], f"{num(b['value'])} s", b["why"], b["evidence"], str(n_views)])
            for pk, pv in (r.get("params") or {}).items():
                rows.append([f"{code(k)} / {code(pk)}", "", f"{num(pv['value'])} {pv['unit']}", pv["why"], pv["evidence"], ""])
        return f"{rc['policy']} {rc['budget_meaning']}\n\n" + table(["Class", "Trigger", "Budget", "Why", "Evidence", "Views"], rows)

    def coverage(self):
        inv = self.core["inventory"]
        cov = vwlib.requirement_coverage(self.views)
        rows = []
        for rid in list(inv["required_rows"]) + list(inv["reported_rows"]):
            items = [r["item"] for r in inv["rows"] if rid in (r.get("req") or [])]
            views = sorted(cov.get(rid, ()), key=lambda k: self.index[k]["id"])
            where = ", ".join(self.link(k) for k in views) if views else f"no view: {inv['no_view_rows'][rid]}"
            rows.append([rid, "; ".join(items) if items else "", where, "required" if rid in inv["required_rows"] else "reported"])
        return table(["Requirement", "What it asks for (inventory item)", "Views that cite it", "Kind"], rows)

    def inventory(self):
        rows = []
        for r in self.core["inventory"]["rows"]:
            where = []
            if "view" in r:
                where.append(self.link(r["view"]) + (f" element {code(r['element'])}" if "element" in r else ""))
            if "component" in r:
                where.append(f"component {code(r['component'])}")
            if "contract" in r:
                where.append(f"contract rule {code(r['contract'])}")
            if "out_of_scope" in r:
                where.append(f"not a view ({code(r['out_of_scope'])})")
            if "future" in r:
                where.append(f"future view ({code(r['future'])})")
            rows.append([r["item"], ", ".join(r.get("req") or []), "; ".join(where)])
        return table(["Output", "Requirement", "Where it lives"], rows)

    def out_of_scope(self):
        o = [table(["Not a view", "Why"], [[code(k), v] for k, v in self.core["out_of_scope"].items()]), ""]
        for k, f in (self.core.get("future_views") or {}).items():
            o += [f"**Future view: {f['name']}** ({code(k)}, no id yet). {f['why_future']} {f['note']} Privacy {code(f['privacy'])}. Requirements: {', '.join(f['requirements'])}.", ""]
            wr = f.get("will_read") or {}
            o += [bullets(f"{k2}: {', '.join(v) if isinstance(v, list) else v}" for k2, v in wr.items()), "", f"Guardrails: {f['guardrails']}"]
        return "\n".join(o)

    def metrics(self):
        used = {}
        for key, rec in self.views.items():
            for e in rec["elements"]:
                for m in (e.get("inputs") or {}).get("metrics") or []:
                    used.setdefault(m, set()).add(key)
        for name, c in self.core["components"].items():
            for m in (c.get("inputs") or {}).get("metrics") or []:
                used.setdefault(m, set())
        rows = [[code(m), self.metric_names[m], ", ".join(self.index[k]["id"] for k in sorted(used[m], key=lambda k: self.index[k]["id"])) or "through a component"]
                for m in sorted(used)]
        return table(["Metric", "Name in the registry", "Views"], rows)

    def phases(self):
        conv = self.core["conventions"]
        rows = []
        for ph in conv["phases"]:
            views = [k for k in self.index if self.views[k]["phase"] == ph]
            later = [f"{self.index[k]['id']} {code(e['key'])}" for k in self.index for e in self.views[k]["elements"] if e.get("phase") == ph and self.views[k]["phase"] != ph]
            if not views and not later:
                continue
            rows.append([f"{ph} {conv['phase_names'][ph]}", ", ".join(f"{self.link(k)} {self.index[k]['name']}" for k in views) or "none", ", ".join(later) or "none"])
        return table(["Phase", "Views first renderable", "Elements of earlier views that arrive here"], rows)

    def questions(self):
        qs = self.core["open_questions"]
        first = [q for q in qs if q.get("first")]
        o = ["**Answer these first**", "", table(["Id", "Question", "Recommended answer"], [[q["id"], q["question"], q["recommended"]] for q in first]), ""]
        topics = []
        for q in qs:
            if q["topic"] not in topics:
                topics.append(q["topic"])
        for t in topics:
            rows = [[q["id"], q["question"], q["recommended"], q["raised_by"], q["status"]] for q in qs if q["topic"] == t and not q.get("first")]
            if rows:
                o += [f"**{t.capitalize()}**", "", table(["Id", "Question", "Recommended answer", "Raised by", "Status"], rows), ""]
        return "\n".join(o)

    def acceptance(self):
        rows = []
        for a in self.core["acceptance"]:
            n_views = sum(1 for v in self.views.values() if a["id"] in v["acceptance"])
            rows.append([a["id"], a["level"], "yes" if a["runnable_now"] else "no", a["metric"], a["scope"], a["threshold"], a["on_fail"], a["requirement"], str(n_views) if n_views else ""])
        return table(["Id", "Level", "Runs now", "What", "Scope", "Passes when", "On fail", "Requirement", "Views"], rows)

    def follow_ups(self):
        return table(["Id", "Owner", "Where", "What", "Why"], [[f["id"], f["owner"], code(f["where"]) if "/" in f["where"] else f["where"], f["what"], f["why"]] for f in self.core["follow_ups"]])

    def schema_changes(self):
        ch = self.changes
        o = [f"`schema/views_changes.yaml` ({ch['status']}). {' '.join(ch['design'].split())}", ""]
        rows = []
        for t, spec in ch["new_tables"].items():
            rows.append([code(t), spec["grain"], str(len(spec["columns"])), ", ".join(spec["requirement"]), spec["why"], codes(spec["read_by"])])
        o += ["**New tables**", "", table(["Table", "Grain", "Columns", "Requirement", "Why", "Read by"], rows), ""]
        rows = [[code(f"{t}.{c['column']}"), c["type"], ", ".join(c["requirement"]), c["why"], codes(c["read_by"])] for t, cols in ch["column_additions"].items() for c in cols]
        o += ["**Column additions**", "", table(["Column", "Type", "Requirement", "Why", "Read by"], rows), ""]
        o += ["**Removals**", "", table(["Column", "Decision", "Why"], [[code(f"{r['table']}.{r['column']}"), r["decision"], r["why"]] for r in ch["removals"]]), ""]
        o += [bullets(ch["cross_file_notes"]), ""]
        used = {c for r in self.views.values() for e in r["elements"] for c in (e.get("inputs") or {}).get("tables") or [] if self.refs.column_state(c) == "proposed"}
        rows = []
        for fname, tables in self.refs.proposed_by_file().items():
            hit = sorted(c for c in used if c.partition(".")[2] in tables.get(c.partition(".")[0], ()))
            if hit:
                rows.append([code(f"schema/{fname}"), str(len(hit)), codes(sorted({c.partition('.')[0] for c in hit}))])
        o += ["**Proposed columns the views already read, by the file that proposes them** (a column proposed by two files counts in both)", "",
              table(["Change file", "Columns read", "Tables"], rows)]
        return "\n".join(o)

    def journal(self):
        return "\n\n".join(f"**{j['date']}, step {j['step']}**\n\n" + bullets(j["entries"]) for j in self.core["journal"])

    # the page -----------------------------------------------------------------------------------------------
    def build(self):
        core, dc = self.core, self.dc
        rep = {
            "DATE": core["date"], "VERSION": core["version"], "STATUS": core["status"],
            "THE_RULE": f"**{' '.join(core['requirement']['the_rule'].split())}**",
            "COUNTS": self.counts(),
            "RULES_SUMMARY": bullets(dc["summary"]),
            "GRADE_TABLE": self.grade_table(),
            "GRADE_RULES": bullets(dc["grades"]["rules"]) + "\n\n" + params_table(dc["grades"]["params"]) + f"\n\nSource: {dc['grades']['source']}",
            "IDENTITY": self.identity(),
            "NUMBER_RULES": bullets(dc["numbers"]["rules"]),
            "NUMBER_CLASSES": self.number_classes(),
            "NUMBER_PARAMS": params_table(dc["numbers"]["params"]),
            "AS_OF": self.as_of_section(),
            "DEGRADED_RULES": bullets(dc["degraded"]["rules"]) + f"\n\nSource: {dc['degraded']['source']}",
            "DEGRADED_DEFAULTS": self.degraded_defaults(),
            "VISUAL": self.visual(),
            "PRIVACY": self.privacy(),
            "IDS_ONLY": bullets(dc["ids_only"]["rules"]),
            "SURFACES": self.surfaces(),
            "AUDIENCES": table(["Audience", "Who", "Status"], [[code(k), a["who"], a["status"]] for k, a in core["audiences"].items()]),
            "VIEW_MAP": self.view_map(),
            "COMPONENTS": self.components(),
            "INTERACTION_PRINCIPLES": bullets(core["interaction_grammar"]["principles"]) + f"\n\n{core['interaction_grammar']['edits_are_drafts']} {core['interaction_grammar']['recompute']}",
            "ACTIONS": table(["Action", "Gesture", "Result", "Requirement"], [[code(k), a["gesture"], a["result"], a["requirement"]] for k, a in core["interaction_grammar"]["actions"].items()]),
            "SHORTCUTS": f"Keys ({core['interaction_grammar']['shortcuts']['status']}):\n\n" + table(["Key", "Does"], [[code(k), v] for k, v in core["interaction_grammar"]["shortcuts"]["keys"].items()]),
            "REFRESH": self.refresh(),
            "COVERAGE": self.coverage(),
            "OUT_OF_SCOPE": self.out_of_scope(),
            "PHASES": self.phases(),
            "QUESTIONS": self.questions(),
            "ACCEPTANCE": self.acceptance(),
            "FOLLOW_UPS": self.follow_ups(),
            "SCHEMA_CHANGES": self.schema_changes(),
            "JOURNAL": self.journal(),
        }
        for s in core["surfaces"]:
            rep[f"SURFACE_{s.upper()}"] = self.surface_section(s)
        out = TEMPLATE.read_text()
        for k, v in rep.items():
            if "{{" + k + "}}" not in out:
                raise SystemExit(f"doc_template.md has no placeholder {k}")
            out = out.replace("{{" + k + "}}", str(v))
        return html_safe(out)

    def build_reference(self):
        core = self.core
        o = ["# Views catalogue: reference", "", f"Date: {core['date']}. Version {core['version']}. Status: {core['status']}", "",
             f"This page is generated from `config/views/*.yaml` by `tools/specgen/views/gen_doc.py`. Do not edit it by hand. It is the second page of the "
             f"[views catalogue]({PAGE}): for every view the number rule and the grade rule of each element in full, what each element shows at every grade "
             "and level, the interactions and the definitions; then the inventory of every named output and the metrics the views read. "
             "Start with the catalogue page; come here to check one element.", ""]
        n = 1
        for s_, title in SURFACE_TITLE.items():
            keys = [k for k, e in self.index.items() if e["surface"] == s_]
            o += [f"## {n}. {title}", "", "\n\n".join(self.reference_block(k) for k in keys), ""]
            n += 1
        o += [f"## {n}. Where every named output lives", "", "Every output named by a requirement or by an owner input, and the view, element, component or contract rule that holds it.", "",
              self.inventory(), "", f"## {n + 1}. Metrics the views read", "", "By registry id (`config/metrics.yaml`). A view lists ids and never a formula.", "", self.metrics(), ""]
        return html_safe("\n".join(o))

    def checks(self, text, ref):
        errs = []
        if len(text.encode()) > MAX_PAGE_BYTES:
            errs.append(f"the catalogue page has {len(text.encode())} bytes, more than {MAX_PAGE_BYTES}: its end would not be rendered")
        if re.search(r"\{\{[A-Z_]+\}\}", text):
            errs.append("placeholder left")
        for key, e in self.index.items():
            head = f"### {self.heading(key)}"
            if head not in text:
                errs.append(f"view {e['id']} has no entry")
                continue
            start = text.index(head)
            nxt = re.search(r"^#{2,3} ", text[start + len(head):], re.M)
            block = text[start: start + len(head) + nxt.start()] if nxt else text[start:]
            for el in self.views[key]["elements"]:
                if f"| `{el['key']}` |" not in block:
                    errs.append(f"view {e['id']}: element {el['key']} missing")
            for a in self.views[key]["acceptance"]:
                if a not in block:
                    errs.append(f"view {e['id']}: acceptance {a} missing")
            if head not in ref:
                errs.append(f"view {e['id']} has no entry on the reference page")
            else:
                rstart = ref.index(head)
                rnxt = re.search(r"^#{2,3} ", ref[rstart + len(head):], re.M)
                rblock = ref[rstart: rstart + len(head) + rnxt.start()] if rnxt else ref[rstart:]
                for el in self.views[key]["elements"]:
                    if f"| `{el['key']}` |" not in rblock:
                        errs.append(f"reference page, view {e['id']}: element {el['key']} missing")
            for p in [self.views[key].get("wireframe")] + list((self.views[key].get("wireframe_states") or {}).values()):
                if p and f"views/{Path(p).name}" not in block:
                    errs.append(f"view {e['id']}: wireframe {p} not embedded")
        for name in self.core["components"]:
            if f"**`{name}`**" not in text:
                errs.append(f"component {name} missing")
        for line in self.dc["summary"]:
            if line not in text:
                errs.append(f"contract rule missing: {line[:30]}")
        for g in self.dc["grades"]["appearance"]:
            if f"| {g} |" not in text:
                errs.append(f"grade {g} missing")
        for group, ids in (("acceptance", [a["id"] for a in self.core["acceptance"]]), ("open question", [q["id"] for q in self.core["open_questions"]]),
                           ("follow-up", [f["id"] for f in self.core["follow_ups"]]), ("action", [f"`{a}`" for a in self.core["interaction_grammar"]["actions"]]),
                           ("refresh class", [f"`{k}`" for k in self.core["refresh_classes"] if k not in ("policy", "budget_meaning")]),
                           ("requirement row", list(self.core["inventory"]["required_rows"]) + list(self.core["inventory"]["reported_rows"]))):
            for i in ids:
                if f"| {i} |" not in text:
                    errs.append(f"{group} {i} missing")
        if "views/grade_legend.svg" not in text:
            errs.append("grade legend not embedded")
        for m in re.findall(r"\(views/([a-z0-9_]+\.svg)\)|src=\"views/([a-z0-9_]+\.svg)\"", text):
            name = m[0] or m[1]
            if not (WIRE_DIR / name).exists():
                errs.append(f"page links to {name}, which does not exist")
        anchors = {PAGE: {slug(h) for h in re.findall(r"^#+ (.*)$", text, re.M)}, REFERENCE: {slug(h) for h in re.findall(r"^#+ (.*)$", ref, re.M)}}
        for here, body in ((PAGE, text), (REFERENCE, ref)):
            for target, anchor in re.findall(r"\]\(([a-z_]*\.md)?#([a-z0-9\-]+)\)", body):
                if anchor not in anchors[target or here]:
                    errs.append(f"{here}: link to {target}#{anchor} has no heading")
        if re.search(r"\{\{[A-Z_]+\}\}", ref):
            errs.append("placeholder left on the reference page")
        return sorted(set(errs))


SURFACE_SECTION = {"live_panel": "3. Live panel", "review": "4. Review and film room", "studio": "5. Analyst Studio and review screens",
                   "report": "6. Reports and packets", "card": "7. Cards"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    doc = Doc()
    problems = vwlib.validate(doc.core, doc.views)
    if problems:
        print("\n".join(f"FAIL {p}" for p in problems[:20]))
        print("the pack does not pass its lint; the page is not written")
        sys.exit(1)
    pages = {PAGE: doc.build(), REFERENCE: doc.build_reference()}
    errs = doc.checks(pages[PAGE], pages[REFERENCE])
    if errs:
        print("\n".join(errs))
        sys.exit(1)
    out = Path(a.out_dir)
    if a.check:
        stale = [name for name, text in pages.items() if not (out / name).exists() or (out / name).read_text() != text]
        if stale:
            print(f"{', '.join(stale)} out of date in {out}: run python tools/specgen/views/gen_doc.py")
            sys.exit(1)
        return
    for name, text in pages.items():
        (out / name).write_text(text)
        print(f"wrote {out / name} ({len(text.splitlines())} lines, {len(text.encode()) // 1024} KB)")


if __name__ == "__main__":
    main()
