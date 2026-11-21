"""Generate docs/data/live_game_state.md from config/live_state/*.yaml, schema/live_state_changes.yaml and the results
in results/live_state_test/ (measured_sensors.json, harness.json).

Usage: python tools/specgen/live_state/gen_doc.py [--out docs/data/live_game_state.md] [--check]
--check regenerates in memory and exits non-zero if the file on disk differs (used by the tests).
Before writing, the script checks that every field id and key, rule, sensor, grade, profile, degradation level,
parameter, acceptance id, open question and follow-up appears on the page, that no {{PLACEHOLDER}} is left and that
every table row has as many cells as its header.

Every sentence that comes from the YAML passes through x() (escapes |, * and <); prose lives in doc_template.md.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lslib  # noqa: E402

ROOT = lslib.REPO
OUT = ROOT / "docs" / "data" / "live_game_state.md"
CORE = lslib.load_core()
FIELDS = lslib.load_fields()
FULL = lslib.resolve(CORE, FIELDS)
PARAMS = lslib.params(CORE, FIELDS)
HARNESS = ROOT / CORE["harness"]["results_file"]
# the 10 groups of the 19 Oct page, in its order; the headings themselves are in doc_template.md
GROUPS = ["keys", "time", "score", "possession_ball", "counts", "personnel", "situation", "tactics", "observability", "fixed"]
TAG_ORDER = ["measured", "rule", "decision", "requirement", "config", "definition", "published", "vendor claim", "assumed"]
NO_CUE = "cues_0.0_0.0_0.0"
AGES = ["1", "2", "3", "4", "5", "6-10", "11-20", "21-30", "31+"]


# ------------------------------------------------------------------------------------------------------- small helpers
def x(s):
    """Text from the YAML or a results file, made safe for a Markdown table cell."""
    s = re.sub(r"\s+", " ", str(s)).strip()
    s = s.replace("|", "\\|").replace("*", "\\*").replace("<", "&lt;")
    return re.sub(r"(?<![A-Za-z0-9`\\])_(?=[A-Za-z0-9])", r"\\_", s)


def xv(s):
    """x(), and every parameter named in the sentence gets its value in brackets."""
    s = x(s)
    for name in sorted((n for n in PARAMS if "_" in n and "." not in n), key=len, reverse=True):
        s = re.sub(rf"(?<![A-Za-z0-9_.`]){re.escape(name)}(?![A-Za-z0-9_`]| \()", lambda m_: f"{name} ({pv(name)})", s)
    return s


def code(s):
    return f"`{s}`"


def codes(items):
    return ", ".join(code(i) for i in items)


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        assert len(r) == len(header), (header, r)
        out.append("| " + " | ".join(str(c) if str(c) != "" else "-" for c in r) + " |")
    return "\n".join(out)


def num(v):
    """A number as the page prints it: no trailing zeros, thousands separated."""
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, int):
        return f"{v:,}"
    if isinstance(v, float):
        if v == int(v) and abs(v) < 1e12:
            return f"{int(v):,}"
        return f"{v:.4f}".rstrip("0").rstrip(".")
    return x(v)


def val(v):
    if isinstance(v, dict):
        return "; ".join(f"{x(k)} {val(w)}" for k, w in v.items())
    if isinstance(v, list):
        if v and all(isinstance(i, list) for i in v):
            return "; ".join(" / ".join(num(j) for j in i) for i in v)
        return ", ".join(val(i) if isinstance(i, (list, dict)) else num(i) for i in v)
    return num(v)


def unit(u):
    return "" if u in (None, "n/a") else x(u)


def pct(v, nd=1):
    return "-" if v is None else f"{100 * v:.{nd}f} %"


def tag(text):
    """Leading evidence tag of an evidence string (conventions.evidence_tags)."""
    head = str(text).split(":", 1)[0].strip()
    return head if head in CORE["conventions"]["evidence_tags"]["tags"] else "untagged"


def pv(name):
    """Value of a param with its unit, as text."""
    p = PARAMS[name]
    u = unit(p.get("unit"))
    return val(p["value"]) + (f" {u}" if u else "")


def by_id(keys):
    return sorted(keys, key=lambda k: FIELDS[k]["id"])


# ---------------------------------------------------------------------------------------------------------- summary
def measured():
    return json.loads(lslib.MEASURED.read_text())["summary"]


def harness():
    return json.loads(HARNESS.read_text()) if HARNESS.exists() else None


def five_numbers(m, h):
    c = m["clock"]
    wh = {r["withheld_s"]: r["last_status"]["within_1s"] for r in m["clock_carry_on_withheld_readings"]}
    lag = m["score"]["made_fg_lag_vs_pbp_clock_s"]
    foul = m["bug_fields"]["team_foul_lag_vs_pbp_clock_s"]
    rows = [
        [f"**{pct(c['availability_in_period']['pooled'], 0)}**", "of in-period seconds show a readable game clock",
         f"Median game {pct(c['availability_in_period']['median'], 0)}, worst {pct(c['availability_in_period']['min'], 0)}, best "
         f"{pct(c['availability_in_period']['max'], 0)}. About {c['hidden_runs']['per_game_median']} hidden stretches per game: median "
         f"{c['hidden_runs']['p50']} s, p90 {c['hidden_runs']['p90']} s, p99 {c['hidden_runs']['p99']} s. So the dropout rules run about once per minute of video, not once a game."],
        [f"**{pv('clock_inferred_max_s')}**", "is how long a blind game clock can be trusted",
         "Keep running if it was running, else hold: within 1 s in " + ", ".join(f"{pct(wh[k])} after {k} s" for k in (2, 3, 5, 10, 30) if k in wh)
         + f". The spec calls the value inferred for {pv('clock_inferred_max_s')}, carried up to {pv('clock_carried_max_s')}, then unknown."],
        [f"**{pv('make_to_bug_p50_s')}** and **{num(lag['p50'])} s**", "a made basket reaches the scorebug",
         f"{pv('make_to_bug_p50_s')} median from the ball through the net (frame precision, n = 10, largest {pv('make_to_bug_p95_s')}). Against the play-by-play "
         f"clock second: median {num(lag['p50'])} s, p95 {num(lag['p95'])} s, p99 {num(lag['p99'])} s (n = {num(lag['n'])}). Two different windows: "
         f"{pv('make_confirm_window_s')} (K02) and {pv('pbp_to_bug_window_s')}."],
        [f"**{num(foul['p50'])} s** and **{num(foul['p95'])} s**", "median and p95 from a foul to the team-foul count on the bug",
         f"n = {num(foul['n'])}; {foul['not_seen_within_45_s']} of {foul['tested']} not seen within 45 s. Shown as a number in "
         f"{m['bug_fields']['games_with_text_foul_counts']} of {m['games']} broadcasts. Far slower than the score, so it has its own window ({pv('foul_to_bug_window_s')}, OQ-LS-4)."],
    ]
    if h:
        s = h["summary"][NO_CUE]
        ok = all(v["pass"] for v in h["verdicts"].values())
        viol = sum(len(v) for v in h["verdicts"]["ACC-LS-H2"]["violations"].values())
        ret = s["returns"]
        rows.append([f"**{pct(s['clock_by_grade']['inferred']['within_tolerance'])}**", "of the clock values the spec calls inferred are within 1 s in the real-data replay",
                     f"Worst game {pct(s['inferred_clock_per_game']['min'])}; the promise is {pct(PARAMS['clock_inferred_promise']['value'], 0)}. "
                     f"{viol} impossible values; {num(ret['miss_beyond_tolerance'])} misses at {num(ret['n'])} bug returns, {ret['miss_log_mismatch']} without a log row. "
                     f"The same test cut the shot clock to {pv('shot_clock_inferred_max_s')} of trust. All checks {'pass' if ok else 'DO NOT pass'}."])
    return table(["Number", "What it is", "What it means for the spec"], rows)


def not_measured():
    return "\n".join([
        f"- **Play-by-play feed delay against real time.** Planning values {pv('feed_delay_p50_s')} median, {pv('feed_delay_p95_s')} p95 (OQ-LS-1; measurement allowed, next live game).",
        f"- **Stream delay of B1G+ against real time.** Planning value {pv('stream_delay_planning_s')} (OQ-LS-2; same live game). Until then `known_at_utc` is modelled.",
        f"- **Whistle and horn audio.** Recall planning value {num(PARAMS['whistle_recall']['value'])}, used only in the replay sweep (OQ-LS-3).",
        f"- **CV event timing on MSU film.** Planning values {pv('cv_make_confirm_s')} median, {pv('cv_event_delay_p95_s')} p95; measured on gold-v1 after the freeze.",
    ])


def counts_line():
    n_rules = sum(len(r.get("dropout") or []) + len(r.get("dropout_extra") or []) for r in FIELDS.values())
    n_prof = sum(len(p["dropout"]) for p in CORE["profiles"].values())
    dims = sum(1 for r in FIELDS.values() if r.get("dimension"))
    return (f"{len(FIELDS)} fields in 10 groups ({dims} carry a state-machine dimension), {len(CORE['sensors'])} sensors, "
            f"{len(CORE['grades']['ladder'])} grades and quarantine, {len(CORE['profiles'])} profiles, {len(CORE['rules'])} named rules, "
            f"{n_prof} profile dropout rules and {n_rules} field dropout rules, {len(PARAMS)} parameters, "
            f"{len(CORE['acceptance'])} acceptance checks, {len(CORE['open_questions'])} open questions.")


# ------------------------------------------------------------------------------------------------------ conventions
def conventions():
    cv = CORE["conventions"]
    out = ["**Three times per value.**\n\n" + table(["Time", "Meaning"], [
        ["event", x(cv["time_axes"]["event_time"])], ["observed", x(cv["time_axes"]["observed_time"])], ["known", x(cv["time_axes"]["known_time"])]])
        + f"\n\nStored as: {x(cv['time_axes']['stored_as'])}"]
    out.append("**Two views.**\n\n" + table(["View", "What it holds and who may read it"], [[code(k), x(v)] for k, v in cv["as_of_views"].items()]))
    out.append("**UTC.**\n\n" + table(["Name", "Meaning"], [[code(k), x(v)] for k, v in cv["utc"].items()]))
    out.append("**Modes.** The spec is written for `live`; the other modes differ as the table says.\n\n"
               + table(["Mode", "What differs"], [[code(k), x(v)] for k, v in cv["modes"].items()]))
    out.append("\n".join([f"- **Storage.** {x(cv['storage'])}", f"- **No empty values.** {x(cv['none_value'])}", f"- **Latency.** {x(cv['latency_policy'])}",
                          f"- **Replays.** {x(cv['replays'])}", f"- **Units.** {x(cv['units'])}"]))
    out.append("**Evidence tags.** " + x(cv["evidence_tags"]["rule"]) + "\n\n"
               + table(["Tag", "Meaning"], [[code(k), x(v)] for k, v in cv["evidence_tags"]["tags"].items()]))
    out.append("**How a dropout rule is read.** " + x(cv["grade_path_timing"]))
    return "\n\n".join(out)


# ---------------------------------------------------------------------------------------------------------- sensors
def delay_cell(s):
    d = s["delay"]

    def one(k):
        v = d.get(k)
        return pv(v) if v in PARAMS else x(v)
    txt = f"{x(d['of'])}: median {one('p50')}, p95 {one('p95')}"
    return txt + (f". {xv(d['note'])}" if d.get("note") else "")


def sensors():
    rows = []
    for name, s in CORE["sensors"].items():
        h = s["health"]
        rows.append([code(name), x(", ".join(s["gives"])), x(s["resolution"]), x(s["availability"]), delay_cell(s),
                     f"{x(h['signal'])}. Down: {xv(h['down_when'])}. Up: {xv(h['up_when'])}." + (f" {x(h['note'])}" if h.get("note") else ""),
                     x("; ".join(s["failure_modes"]))])
    return table(["Sensor", "Gives", "Resolution", "Availability", "Delay (event to sensor)", "Health signal: how we know it dropped", "Failure modes"], rows)


def sensor_numbers(m):
    out = []
    b, c = m["bug_fields"], m["clock"]
    out.append(f"Source: `results/live_state_test/measured_sensors.json` ({m['games']} MSU broadcasts, {num(m['video_hours'])} h, one OCR frame per second, "
               "so every number has 1 s resolution; lags against the play-by-play include the scorer's own clock error).")
    out.append(table(["What the bug shows", "Share"], [
        ["game clock, of in-period seconds (pooled)", pct(c["availability_in_period"]["pooled"])],
        ["shot clock, of the seconds with a game clock", pct(b["shot_clock_read_share"])],
        ["score total, of the seconds with a game clock (median game)", pct(m["score"]["total_read_share"]["median"])],
        ["timeouts left, of the seconds with a game clock", pct(b["timeouts_read_share"])],
        ["team fouls, of the seconds with a game clock", pct(b["team_fouls_read_share"])],
        ["OCR clock reads rejected as inconsistent", pct(c["ocr_reject_share_pooled"])],
        ["shot-clock ticks consistent between two seconds", pct(b["shot_clock_tick_consistent_share"])],
        ["score total equal to the play-by-play total, stable samples (median game)", pct(m["score"]["total_matches_pbp_share"]["median"])],
        ["game-clock time never shown on the bug (median game)", pct(c["game_clock_share_unseen"]["median"])],
    ]))
    ch = {r["hidden_s_bucket"]: r["changed_share"] for r in m["score"]["changed_during_real_hidden_run"]}
    out.append("**Real hidden stretches** (the bug was away): what the clock did, and how well the rule \"keep running if it was running, else hold\" did.\n\n"
               + table(["Length (s)", "Stretches", "Clock stopped", "Rule within 1 s at the end", "Score changed inside"],
                       [[r["hidden_s_bucket"], num(r["runs"]), pct(r["clock_stopped_share"]), pct(r["last_status"]["within_1s"]), pct(ch.get(r["hidden_s_bucket"]))]
                        for r in m["clock_carry_on_real_hidden_runs"]]))
    cw = {r["withheld_s"]: r["changed_share"] for r in m["score"]["changed_within_withheld_window"]}
    out.append("**Withheld readings** (the bug was visible; the reading was hidden on purpose at every possible moment). This is the curve the limits are set from.\n\n"
               + table(["Withheld (s)", "n", "Rule within 1 s", "Plain hold within 1 s", "Plain run within 1 s", "Score changed inside"],
                       [[r["withheld_s"], num(r["n"]), pct(r["last_status"]["within_1s"]), pct(r["hold"]["within_1s"]), pct(r["run"]["within_1s"]), pct(cw.get(r["withheld_s"]))]
                        for r in m["clock_carry_on_withheld_readings"]]))
    lag, foul = m["score"]["made_fg_lag_vs_pbp_clock_s"], b["team_foul_lag_vs_pbp_clock_s"]

    def within(d):
        return ", ".join(f"{pct(v)} within {k} s" for k, v in d["share_within_s"].items())
    out.append("**Lags.**\n\n" + table(["Lag", "n", "Median (s)", "p90 (s)", "p95 (s)", "p99 (s)", "Shares", "Not seen"], [
        ["ball through the net to the first changed score digit (frame precision, `results/w3_intake`)", 10, num(PARAMS["make_to_bug_p50_s"]["value"]), "-", "-", "-",
         f"largest {pv('make_to_bug_p95_s')}; digit animation {pv('digit_animation_s')}", "0"],
        ["play-by-play clock second of a made field goal to the score on the bug", num(lag["n"]), num(lag["p50"]), num(lag["p90"]), num(lag["p95"]), num(lag["p99"]), within(lag),
         f"{lag['not_seen_within_15_s']} of {num(lag['tested'])} within 15 s"],
        ["play-by-play clock second of a foul to the team-foul count on the bug", num(foul["n"]), num(foul["p50"]), num(foul["p90"]), num(foul["p95"]), num(foul["p99"]), within(foul),
         f"{foul['not_seen_within_45_s']} of {num(foul['tested'])} within 45 s"],
    ]))
    w = m["pbp_wallclock"]
    out.append(f"**Play-by-play wallclock.** {pct(w['backward_step_share'], 0)} of {num(w['rows'])} rows step backward (largest {num(w['backward_step_max_s'])} s); "
               f"entry jitter {num(w['entry_jitter']['robust_sigma_single_entry_s'])} s per entry ({num(w['entry_jitter']['pairs'])} pairs). "
               "It is never joined to prices raw.")
    return "\n\n".join(out)


# ----------------------------------------------------------------------------------------------------------- grades
def grades():
    g = CORE["grades"]
    rows = [[d["rank"], code(k), x(d["meaning"]), x(", ".join(d["may_feed"]) or "nothing"), code(d["dq_enum"])]
            for k, d in sorted(g["defs"].items(), key=lambda kv: kv[1]["rank"])]
    return (table(["Rank", "Grade", "Meaning", "May feed", "Written to dq today"], rows) + "\n\n" + "\n".join(f"- {x(r)}" for r in g["rules"])
            + f"\n- Stamps: {x(g['stamps'])}")


def ladder_line():
    g = CORE["grades"]
    return " > ".join(code(k) for k in g["ladder"]) + "; aside: " + codes(g["aside"])


# --------------------------------------------------------------------------------------------------- rules, profiles
def limits_text(lim):
    if not lim:
        return ""
    return ", ".join(f"{code(k)} {pv(k)}" if k in PARAMS else f"{code(k)} {num(v)}" for k, v in lim.items())


def path_text(d):
    p = " > ".join(d["grade_path"])
    if d.get("step_at"):
        p += " (steps at " + ", ".join(str(s) for s in d["step_at"]) + ")"
    return x(p)


def src_text(sources):
    """Sources by authority: value sources first in the value order of reconciliation, then confirm, timing, fallback."""
    va, ta = CORE["reconciliation"]["value_authority"], CORE["reconciliation"]["timing_authority"]
    by = {}
    for s in sources or []:
        if s["sensor"] not in by.setdefault(s["role"], []):
            by[s["role"]].append(s["sensor"])
    parts = []
    for role in lslib.ROLES:
        if role in by:
            order = ta if role == "timing" else va
            names = sorted(by[role], key=lambda n: order.index(n) if n in order else len(order))
            parts.append(f"{role}: {codes(names)}")
    return "; ".join(parts)


def timing_text(t, with_tag=True):
    if not t or "provisional" not in t:
        return ""
    p, c = t["provisional"], t["confirmed"]

    def one(b):
        return f"{num(b['p50_s'])} / {num(b['p95_s'])} s by {x(b['by'])}"
    txt = one(p) if p == c else f"provisional {one(p)}; confirmed {one(c)}"
    if t.get("driven_by"):
        txt += "; written for " + codes(t["driven_by"])
    return txt + (f" [{tag(t['evidence'])}]" if with_tag and t.get("evidence") else "")


def conflict_text(conf):
    out = []
    for c in conf or []:
        tol = "" if c.get("tolerance") is None else f" (tolerance {num(c['tolerance'])})"
        out.append(f"{x(' against '.join(c['between']))}{tol}: value {x(c['value_winner'])}, instant {x(c['timing_winner'])}; log {code(c['log_to'])}")
    return "<br>".join(out)


def rules():
    return table(["Rule", "What it does"], [[code(k), xv(v)] for k, v in CORE["rules"].items()])


def profiles():
    out = []
    for name, p in CORE["profiles"].items():
        n = sum(1 for r in FIELDS.values() if r["profile"] == name)
        head = [f"### Profile `{name}` ({n} fields)", "", x(p["summary"]), ""]
        head.append(f"- **Sources:** {src_text(p['sources']) or 'its inputs'}")
        cb = p["update"]["changed_by"]
        head.append(f"- **Changes on:** {x(', '.join(cb) if isinstance(cb, list) else cb)}")
        head.append(f"- **Live latency budget (median / p95):** {timing_text(p['latency'], False)}. Evidence: {x(p['latency']['evidence'])}")
        if p["conflict"]:
            head.append(f"- **Conflict:** {conflict_text(p['conflict'])}")
        rows = [[x(d["when"]), code(d["rule"]), path_text(d), limits_text(d["limits"]) or "-", code(d["on_return"]), x(d["evidence"])] for d in p["dropout"]]
        out.append("\n".join(head) + "\n\n" + table(["When", "Rule", "Grade path", "Limits", "On return", "Evidence"], rows))
    return "\n\n".join(out)


def max_dwell():
    rows = []
    for k, d in CORE["max_dwell"].items():
        if lslib.is_param(d):
            rows.append([code(k), f"{num(d['value'])} {d['unit']}", x(d["counts_in"]), x(d["rule"]), x(d["why"]), x(d["evidence"])])
    return table(["State", "Bound", "Counts in", "Rule", "Why", "Evidence"], rows) + "\n\n" + x(CORE["max_dwell"]["note"])


def levels():
    lv = CORE["degradation_levels"]
    cols = ["clocks", "counters", "status", "roster", "observation", "derived", "panel"]
    rows = [[code(k), x(d["when"])] + [xv(d[c]) for c in cols] for k, d in lv.items() if isinstance(d, dict) and "clocks" in d]
    fs = lv["feed_stale"]
    return (table(["Level", "When", "Clocks", "Counters", "Status", "Lineups", "Positions", "Derived", "Live panel may show"], rows)
            + f"\n\n**`feed_stale`** ({xv(fs['when'])}): {x(fs['effect'])}.\n\n{x(lv['rule'])}")


# ------------------------------------------------------------------------------------------------------- the fields
def field_cell(key, rec):
    return f"**{rec['id']}** {code(key)}<br>{x(rec['name'])}"


def values_cell(rec):
    u = unit(rec["unit"])
    return f"{x(rec['domain'])}<br>{x(rec['type'])}" + (f", {u}" if u else "") + f"; when not known: {code(rec['none_value'])}"


def stored_cell(rec):
    return x(rec["stored"]) + (f"<br>dimension {code(rec['dimension'])}" if rec.get("dimension") else "")


def sources_cell(rec, full):
    parts = [src_text(full["sources"])] if full["sources"] else []
    if rec.get("derived_from"):
        parts.append("derived from: " + codes(rec["derived_from"]))
    if rec.get("computed_from"):
        parts.append("computed from: " + codes(rec["computed_from"]))
    return "<br>".join(p for p in parts if p)


def changes_cell(rec, full):
    u = full["update"]
    cb = u["changed_by"]
    parts = [x(", ".join(cb) if isinstance(cb, list) else cb)]
    if u.get("steps_by"):
        parts.append("steps by: " + val(u["steps_by"]))
    if rec.get("recompute_on"):
        parts.append("Recomputed: " + x(rec["recompute_on"]))
    parts.append("Instant: " + x(u["event_instant"]))
    return "<br>".join(parts)


def latency_cell(rec, full):
    parts = [timing_text(full["timing"])]
    if rec.get("freshness_needed_s"):
        parts.append("needed fresh within: " + ", ".join(f"{x(k)} {num(v)} s" for k, v in rec["freshness_needed_s"].items()))
    return "<br>".join(p for p in parts if p)


def dwell_text(entry):
    d = CORE["max_dwell"][entry]
    return f"{code(entry)} {num(d['value'])} {d['unit']} ({x(d['rule'])})"


def drop_cell(rec, full):
    own = rec.get("dropout")
    lines = []
    if own is None:
        lines.append(f"Rules of profile {code(rec['profile'])}.")
    for d in (own or []) + (rec.get("dropout_extra") or []):
        lim = limits_text(d["limits"])
        nxt = f"; then {x(d['next_value'])}" if d.get("next_value") else ""
        lines.append(f"- {x(d['when'])}: {path_text(d)}" + (f" ({lim})" if lim else "") + f"; {code(d['rule'])}; back {code(d['on_return'])}{nxt} [{tag(d['evidence'])}]")
    md = rec.get("max_dwell")
    if isinstance(md, str):
        lines.append("Max dwell: " + dwell_text(md))
    elif isinstance(md, dict):
        lines.append(f"Max dwell: {num(md['value'])} {x(md.get('unit', 's'))} ({x(md['rule'])}) [{tag(md.get('evidence', ''))}]")
    if rec.get("max_dwell_by_value"):
        lines.append("Max dwell by value: " + "; ".join(f"{x(v)} {dwell_text(e)}" for v, e in rec["max_dwell_by_value"].items()))
    if rec.get("valid_if"):
        lines.append("Valid if: " + xv(rec["valid_if"]))
    if rec.get("panel"):
        lines.append("Panel: " + "; ".join(f"{x(k)} - {x(v)}" for k, v in rec["panel"].items()))
    return "<br>".join(lines)


def group_table(group):
    rows = []
    for key in by_id(k for k, r in FIELDS.items() if r["group"] == group):
        rec, full = FIELDS[key], FULL[key]
        rows.append([field_cell(key, rec), values_cell(rec), stored_cell(rec), sources_cell(rec, full), changes_cell(rec, full),
                     latency_cell(rec, full), drop_cell(rec, full), conflict_text(full["conflict"])])
    return table(["Field", "Values / unit", "Stored", "Sources by authority", "Changes on", "Live latency budget (median / p95)",
                  "When a sensor drops", "Conflict rule"], rows)


def out_of_scope():
    inv = CORE["inventory"]
    a = table(["Not a field of this pack", "Why"], [[code(k), x(v)] for k, v in CORE["out_of_scope"].items()])
    b = table(["Field added to the 19 Oct page", "Where it comes from"], [[code(k), x(v)] for k, v in inv["added_by_this_pack"].items()])
    n_cols = len({c for cols in inv["columns"].values() for c in cols})
    return (f"The audit behind ACC-LS-2 is kept in `core.yaml` (`inventory`) and run by the lint: the 32 state-machine dimensions, {n_cols} columns of "
            f"`state_frame` and `state_second`, the rows R-SR-01..20 and every row of the 19 Oct page map to a field or to the table below.\n\n{a}\n\n{b}")


# --------------------------------------------------------------------------------------------------- reconciliation
def reconciliation():
    r = CORE["reconciliation"]
    w = r["windows"]
    rows = [[x(k.replace("_", " ")), code(p), pv(p), x(PARAMS[p]["why"]), x(PARAMS[p]["evidence"])] for k, p in w.items() if p in PARAMS]
    logs = table(["Log", "What goes there"], [[code(k), x(v)] for k, v in r["logging"].items()])
    return "\n\n".join([
        f"**Who wins a value:** {' > '.join(code(s) for s in r['value_authority'])}.\n\n**Who wins an instant:** {' > '.join(code(s) for s in r['timing_authority'])}.\n\n{x(r['authority_note'])}",
        "**Confirm windows.**\n\n" + table(["Window", "Parameter", "Value", "Why", "Evidence"], rows) + f"\n\nRe-set rule: {xv(w['reset_rule'])}",
        f"**Tolerances.** {xv(r['tolerances'])}",
        "**Where a disagreement is logged.**\n\n" + logs,
        f"**Late and corrected rows.** {x(r['versions'])}. {x(CORE['rules']['LATE_CORRECTION'])}",
    ])


# ------------------------------------------------------------------------------------------------------- the replay
def cfg_note(c):
    if c["mode"] == "slot":
        return f"only the shot-clock slot hidden; reset cue at {num(c['reset'])}"
    if c["feed"] is not None:
        return f"bug hidden; score rows of made field goals arrive {num(c['feed'])} s late"
    if not (c["stop"] or c["start"] or c["reset"]):
        return "bug hidden; no cue, no feed"
    return f"bug hidden; stop / start / reset cues at {num(c['stop'])} / {num(c['start'])} / {num(c['reset'])}"


def stale_limits(h):
    return {k: (v, PARAMS[k]["value"]) for k, v in h["limits_used"].items() if k in PARAMS and PARAMS[k]["value"] != v}


def replay(h):
    if h is None:
        return "_The replay has not been run yet (`python tools/specgen/live_state/harness.py`; it needs the private recordings)._"
    s, v = h["summary"], h["verdicts"]
    none = s[NO_CUE]
    cues = [c["name"] for c in h["configs"] if c["mode"] == "bug" and c["feed"] is None]
    feeds = [c["name"] for c in h["configs"] if c["feed"] is not None]
    hidden = none["counts"]["hidden_s"]
    stale = stale_limits(h)
    out = [f"Run of {h['date']} with pack {h['pack_version']}: {h['games']} broadcasts, {h['seeds']} seeds, {len(h['configs'])} configurations, "
           f"{num(hidden)} hidden seconds over {none['counts']['runs']} runs per configuration, {h['resolution_s']} s resolution. Numbers: `{CORE['harness']['results_file']}`; "
           "all tables: `results/live_state_test/README.md`. "
           + ("**The limits on this page differ from the limits the replay used (" + ", ".join(f"`{k}` {num(a)} then, {num(b)} now" for k, (a, b) in stale.items())
              + "): every number in this section is stale until the replay is re-run.**" if stale else "The replay used the limits on this page.")]
    out.append(x(CORE["harness"]["summary"]))
    out.append(table(["Configuration", "What it is"], [[code(c["name"]), cfg_note(c)] for c in h["configs"]]))
    h1, h3 = v["ACC-LS-H1"]["game_clock_inferred"], v["ACC-LS-H3"]["returns"][NO_CUE]
    sc = v["shot_clock_inferred"]["by_config"]

    def verdict(k):
        return "pass" if v[k]["pass"] else "**FAIL**"
    out.append("**Verdicts.**\n\n" + table(["Check", "Result", "Numbers"], [
        ["ACC-LS-H1", verdict("ACC-LS-H1"), f"inferred game-clock seconds within {pv('clock_tolerance_s')}: " + ", ".join(f"{pct(h1[c]['pooled'])} ({code(c)})" for c in cues if c in h1)
         + f"; ages below the promise of {pct(v['ACC-LS-H1']['promise'], 0)}: {sum(len(r['ages_below_promise']) for r in h1.values())}"],
        ["ACC-LS-H2", verdict("ACC-LS-H2"), f"{sum(len(r) for r in v['ACC-LS-H2']['violations'].values())} impossible values in {len(v['ACC-LS-H2']['violations'])} configurations"],
        ["ACC-LS-H3", verdict("ACC-LS-H3"), f"{num(h3['n'])} bug returns; second reading observed and equal in {num(h3['second_reading_observed_and_equal'])} of {num(h3['second_reading'])}; "
         f"{num(h3['miss_beyond_tolerance'])} misses beyond the tolerance, {h3['miss_log_mismatch']} without a log row"],
        ["ACC-LS-H4", verdict("ACC-LS-H4"), f"ages where the spec rule is below plain last-status: {sum(len(r) for r in v['ACC-LS-H4']['ages_where_spec_is_below_last_status'].values())}"],
        ["shot clock (ACC-LS-H1)", verdict("shot_clock_inferred"), "inferred shot-clock seconds within 1 s: " + ", ".join(f"{pct(sc[c]['pooled'])} ({code(c)})" for c in sc if c in cues or c.startswith("slot"))],
    ]))
    ages = [a for a in AGES if a in none["clock_by_age"]]
    out.append("**Game clock: share of hidden seconds within 1 s, by seconds since the last reading.** Ages 1 to 3 are where the spec may call the value inferred; the honesty table below counts only the seconds it did.\n\n"
               + table(["Age (s)", "n", "Spec rule, no cue", "Plain last status", "Plain hold", "Plain run"] + [f"Spec, `{c}`" for c in cues[1:]],
                       [[a, num(none["clock_by_age"][a]["n"]), pct(none["clock_by_age"][a]["spec"]), pct(none["clock_by_age"][a]["last_status"]),
                         pct(none["clock_by_age"][a]["hold"]), pct(none["clock_by_age"][a]["run"])] + [pct(s[c]["clock_by_age"][a]["spec"]) for c in cues[1:]] for a in ages]))
    hon = []
    for c in cues:
        g, ia = s[c]["clock_by_grade"], s[c]["inferred_by_age"]["game_clock_s"]
        hon.append([code(c), num(g["inferred"]["n"]), pct(g["inferred"]["within_tolerance"])] + [pct(ia[a]["within_tolerance"]) if a in ia else "-" for a in ("1", "2", "3")]
                   + [pct(s[c]["inferred_clock_per_game"]["min"]), pct(g["carried"]["within_tolerance"]), num(g["unknown"]["n"])])
    out.append("**Grade honesty of the game clock.** Carried and unknown make no claim; they are shown so the ladder can be seen working.\n\n"
               + table(["Run", "Inferred seconds", "Within 1 s", "At 1 s", "At 2 s", "At 3 s", "Worst game", "Carried: within 1 s", "Graded unknown (s)"], hon)
               + f"\n\nThe guaranteed interval held the true clock in {pct(none['clock_interval_holds_truth'], 2)} of hidden seconds. The running flag graded inferred was right in "
               f"{pct(none['running_flag_inferred_right']['share'])} with no cue.")
    srows = []
    for c in [NO_CUE] + feeds:
        t = s[c]["by_grade"]["score_total"]["carried"]
        w = s[c]["score_equal_to_bug_now_or_within_window"]
        srows.append([code(c), num(t["n"]), pct(t["equal"]), pct(w["share"])])
    out.append("**Score total while the bug is hidden and nothing watches the rim** (always carried: no claim).\n\n"
               + table(["Run", "Carried seconds", "Equal to the hidden bug reading", "Equal now or within the confirm window"], srows))
    sh = [a for a in ("1", "2", "3", "4", "5", "6-10")]
    runs = [c["name"] for c in h["configs"] if c["feed"] is None]
    out.append("**Shot clock: share within 1 s, by seconds since its last reading.** Only the first second is called inferred.\n\n"
               + table(["Run"] + [f"{a} s" for a in sh], [[code(c)] + [pct(s[c]["by_age"]["shot_clock_s"][a]["equal"]) if a in s[c]["by_age"]["shot_clock_s"] else "-" for a in sh] for c in runs]))
    orow = []
    for f in ("period", "team_fouls_home", "team_fouls_away", "timeouts_left_home", "timeouts_left_away"):
        for g, d in none["by_grade"].get(f, {}).items():
            orow.append([code(f), g, num(d["n"]), pct(d["equal"])])
    out.append("**Other bug fields while hidden** (no cue; compared with the bug, which itself trails the event; home and away are the two slots of the bug).\n\n"
               + table(["Field", "Grade", "Seconds", "Equal to the hidden reading"], orow))
    return "\n\n".join(out)


# ------------------------------------------------------------------------------------------------------- acceptance
def acceptance(h):
    problems = lslib.validate(CORE, FIELDS, require_all=True)
    lint = f"met ({len(FIELDS)} fields, 0 problems)" if not problems else f"NOT met ({len(problems)} problems)"
    rows = []
    for k, a in CORE["acceptance"].items():
        if k in ("ACC-LS-1", "ACC-LS-2"):
            verdict = lint if k == "ACC-LS-1" else ("met (checked by the lint)" if not problems else "NOT met (lint problems)")
        elif k.startswith("ACC-LS-H"):
            verdict = "not run" if h is None else ("met in the replay of " + h["date"] if h["verdicts"][k]["pass"] else "NOT met")
            if h is not None and k == "ACC-LS-H1" and not h["verdicts"]["shot_clock_inferred"]["pass"]:
                verdict = "NOT met (shot clock)"
            if h is not None and stale_limits(h):
                verdict += " (stale: limits changed since)"
        elif k.startswith("ACC-LS-G"):
            verdict = "needs gold-v1 (MSU film, after the freeze)"
        else:
            verdict = "no game processed yet (the pilot is offline; K23)"
        rows.append([k, x(a["metric"]), x(a["scope"]), xv(a["threshold"]), x(a["on_fail"]), verdict])
    return table(["Id", "Metric", "Scope", "Threshold", "If it fails", "Verdict today"], rows)


# -------------------------------------------------------------------------------------------- measured and assumed
def tag_counts():
    """Evidence tags of the params, of the written dropout rules (profiles and fields) and of the latency budgets of fields."""
    ptags = Counter(tag(p.get("evidence", "")) for p in PARAMS.values())
    rtags = Counter(tag(d["evidence"]) for p in CORE["profiles"].values() for d in p["dropout"])
    rtags += Counter(tag(d["evidence"]) for r in FIELDS.values() for d in (r.get("dropout") or []) + (r.get("dropout_extra") or []))
    ttags = Counter(tag(r["timing"]["evidence"]) for r in FIELDS.values() if (r.get("timing") or {}).get("evidence"))
    return ptags, rtags, ttags


def evidence_summary():
    ptags, rtags, ttags = tag_counts()
    tags = [t for t in TAG_ORDER + ["untagged"] if ptags[t] or rtags[t] or ttags[t]]
    meaning = CORE["conventions"]["evidence_tags"]["tags"]
    rows = [[code(t), x(meaning.get(t, "")), ptags[t], rtags[t], ttags[t]] for t in tags]
    rows.append(["**all**", "", sum(ptags.values()), sum(rtags.values()), sum(ttags.values())])
    return table(["Tag", "Meaning", "Parameters", "Dropout rules", "Latency budgets of fields"], rows)


def journal_quotes():
    """The sentences of the core.yaml journal that quote counts of the pack. A test rebuilds them and checks that the
    journal still says the same, so a count cannot go stale unnoticed."""
    p, r, t = tag_counts()
    out = {
        "params": f"of {len(PARAMS)} params {p['measured']} are measured on our recordings, {p['rule']} come from the rules book, {p['decision']} from recorded "
                  f"decisions, {p['requirement']} from requirements, {p['config']} mirror another config and {p['assumed']} are assumed",
        "rules": f"Of {sum(r.values())} written dropout rules {r['measured']} rest on a measurement and {r['assumed']} on an assumption",
        "budgets": f"Of the {sum(t.values())} latency budgets written by fields, {t['measured']} are measured, {t['definition']} hold by definition and {t['assumed']} are assumed",
    }
    if lslib.CHANGES.exists():
        doc = lslib.load_yaml_strict(lslib.CHANGES)
        add = doc["column_additions"]
        out["schema"] = (f"{sum(len(c) for c in add.values())} new columns in {len(add)} tables")
        out["schema_lists"] = f"{len(doc['enum_changes'])} value-list changes"
        out["schema_defs"] = f"{len(doc['definition_changes'])} definition fixes"
    return out


def params_table():
    prod = CORE["production_only_params"]

    def order(item):
        t = tag(item[1].get("evidence", ""))
        return (TAG_ORDER.index(t) if t in TAG_ORDER else len(TAG_ORDER), item[1]["_where"], item[0])
    rows = []
    for name, p in sorted(PARAMS.items(), key=order):
        u = unit(p.get("unit"))
        rows.append([code(name), val(p["value"]) + (f" {u}" if u else ""), x(p["_where"]), x(p.get("why", "")), x(p.get("evidence", "")),
                     "replay and tests" if name not in prod else x(prod[name])])
    return table(["Parameter", "Value", "Where", "Why", "Evidence", "Read by"], rows)


# --------------------------------------------------------------------------------------- questions, follow-ups, journal
def questions():
    qs = CORE["open_questions"]
    need = [q for q in qs if "needs Aldemir" in q["status"]]
    head = f"{len(qs)} questions. {len(need)} need an answer from Aldemir; the others are measurements that are already allowed or wait for the freeze."
    return head + "\n\n" + table(["Id", "Question", "Recommended answer", "Status"], [[q["id"], x(q["question"]), x(q["recommended"]), x(q["status"])] for q in qs])


def follow_ups():
    return table(["Id", "Where", "What", "Why", "Status"], [[f["id"], x(f["where"]), x(f["what"]), x(f["why"]), x(f["status"])] for f in CORE["follow_ups"]])


def schema_changes():
    if not lslib.CHANGES.exists():
        return "_`schema/live_state_changes.yaml` is not written yet._"
    doc = lslib.load_yaml_strict(lslib.CHANGES)
    add = doc["column_additions"]
    rows = [[code(t), len(cols), codes(c["column"] for c in cols)] for t, cols in add.items()]
    for t, d in (doc.get("new_tables") or {}).items():
        rows.append([f"{code(t)} (new table)", len(d["columns"]), codes(c["column"] for c in d["columns"])])
    enums = table(["Id", "Where", "Change", "Why"], [[e["id"], x(e["where"]), x(e["change"]), x(e["why"])] for e in doc["enum_changes"]])
    defs = table(["Id", "Where", "Fix", "Why"], [[e["id"], x(e["where"]), x(e["fix"]), x(e["why"])] for e in doc["definition_changes"]])
    tn = doc["team_neutral"]
    return (f"`schema/live_state_changes.yaml`, status {x(doc['status'])}: {sum(len(c) for c in add.values())} new columns in {len(add)} tables, "
            f"{len(doc.get('new_tables') or {})} new table, {len(doc['enum_changes'])} value-list changes, {len(doc['definition_changes'])} definition fixes. "
            "Each entry gives type, unit, the field that needs it, why and the requirement id.\n\n"
            + table(["Table", "Columns", "New columns"], rows) + "\n\n" + enums + "\n\n" + defs
            + f"\n\n**Home / away names.** {x(tn['rule'])} The renames of existing columns are owned by `{x(tn['owned_by'])}`; "
            f"{tn['fields_that_read_renamed_columns']} fields of this pack read a column that is renamed there (the file lists them).")


def journal():
    out = []
    for j in CORE["journal"]:
        out.append(f"**{j['version']} ({j['date']})**\n\n" + "\n".join(f"- {x(e)}" for e in j["entries"]))
    return "\n\n".join(out)


# ------------------------------------------------------------------------------------------------------------ build
def build():
    tpl = (HERE / "doc_template.md").read_text()
    m, h = measured(), harness()
    rep = {
        "DATE": CORE["date"], "LAST_ENTRY": max(j["date"] for j in CORE["journal"]), "VERSION": CORE["version"], "STATUS": x(CORE["status"]), "SCOPE": x(CORE["scope"]),
        "THE_RULE": x(CORE["requirement"]["the_rule"]), "ASK": x(CORE["requirement"]["ask"]),
        "REQUIREMENTS": x(", ".join(CORE["requirement"]["requirements"])), "IDS_NOTE": x(CORE["requirement"]["ids_note"]),
        "LADDER": ladder_line(), "FIVE_NUMBERS": five_numbers(m, h), "NOT_MEASURED": not_measured(), "COUNTS": counts_line(),
        "CONVENTIONS": conventions(), "SENSORS": sensors(), "SENSOR_NUMBERS": sensor_numbers(m), "GRADES": grades(), "RULES": rules(),
        "PROFILES": profiles(), "MAX_DWELL": max_dwell(), "LEVELS": levels(), "OUT_OF_SCOPE": out_of_scope(),
        "RECONCILIATION": reconciliation(), "LATENCY_COMPOSITION": x(CORE["latency_budget"]["composition"]),
        "REPLAY": replay(h), "ACCEPTANCE": acceptance(h), "EVIDENCE_SUMMARY": evidence_summary(), "PARAMS": params_table(),
        "QUESTIONS": questions(), "FOLLOW_UPS": follow_ups(), "SCHEMA_CHANGES": schema_changes(), "JOURNAL": journal(),
    }
    for g in GROUPS:
        rep["GROUP_" + g.upper()] = group_table(g)
    out = tpl
    for k, v in rep.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def checks(text):
    errs = []
    if re.search(r"\{\{[A-Z_]+\}\}", text):
        errs.append("placeholder left: " + ", ".join(sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", text)))))
    for key, rec in FIELDS.items():
        if rec["id"] not in text:
            errs.append(f"field id {rec['id']} missing")
        if f"`{key}`" not in text:
            errs.append(f"field {key} missing")
    ids = sorted(r["id"] for r in FIELDS.values())
    if len(set(ids)) != len(re.findall(r"\*\*LS-[A-Z]+-\d\d\*\*", text)):
        errs.append("a field row is missing or written twice")
    for kind, names in (("rule", CORE["rules"]), ("sensor", CORE["sensors"]), ("grade", CORE["grades"]["defs"]), ("profile", CORE["profiles"]),
                        ("degradation level", [k for k in CORE["degradation_levels"] if k != "rule"]), ("parameter", PARAMS),
                        ("out-of-scope entry", CORE["out_of_scope"])):
        for n in names:
            if f"`{n}`" not in text:
                errs.append(f"{kind} {n} missing")
    for kind, names in (("acceptance", CORE["acceptance"]), ("open question", [q["id"] for q in CORE["open_questions"]]),
                        ("follow-up", [f["id"] for f in CORE["follow_ups"]])):
        for n in names:
            if not re.search(rf"\| {re.escape(n)} \|", text):
                errs.append(f"{kind} {n} missing")
    for g in GROUPS:   # the ten headings of the 19 Oct page, numbered 1..10
        if not re.search(rf"^### {GROUPS.index(g) + 1}\. ", text, re.M):
            errs.append(f"group heading {GROUPS.index(g) + 1} missing")
    width = None
    for i, line in enumerate(text.splitlines(), 1):   # every table row has as many cells as its header
        if line.startswith("|"):
            n = len(re.findall(r"(?<!\\)\|", line))
            if width is None:
                width = n
            elif n != width:
                errs.append(f"line {i}: table row has {n - 1} cells, its header has {width - 1}")
        else:
            width = None
    if re.search(r"\d\s*(feet|foot|ft)\b(?!_)", re.sub(r"`[^`]*`", "", text)):
        errs.append("a length in feet on the page")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    text = build()
    errs = checks(text)
    if errs:
        print("\n".join(errs))
        sys.exit(1)
    out = Path(a.out)
    if a.check:
        if not out.exists() or out.read_text() != text:
            print(f"{out} is out of date: run python tools/specgen/live_state/gen_doc.py")
            sys.exit(1)
        return
    out.write_text(text)
    print(f"wrote {out} ({len(text.splitlines())} lines)")


if __name__ == "__main__":
    main()
