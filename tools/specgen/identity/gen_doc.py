"""Generate docs/data/identity_pack.md from config/identity_pack.yaml and the harness results.

Usage: python tools/specgen/identity/gen_doc.py [--out docs/data/identity_pack.md] [--check]
--check regenerates in memory and exits non-zero if the file on disk differs (used by the tests).
After writing, the script checks that every parameter, hard case, acceptance test and transition id appears
on the page and that no {{PLACEHOLDER}} is left.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import idlib  # noqa: E402

ROOT = HERE.parents[2]
SPEC = idlib.SPEC
OUT = ROOT / "docs" / "data" / "identity_pack.md"
RESULTS = ROOT / SPEC["harness"]["results_file"]
CONFIG_ORDER = list(SPEC["harness"]["configs"])
CONFIG_NOTE = {
    "naive_tracker": "standard tracker, labels kept once given",
    "motion_team": "pure tracklets + team colour",
    "motion_team_lineup": "+ PBP lineup",
    "plus_jersey": "+ jersey numbers",
    "plus_appearance": "+ torso/legs appearance",
    "full": "+ height and gait (the spec)",
    "full_no_jersey": "spec without jersey numbers",
    "full_no_lineup": "spec without the lineup",
    "full_forced": "spec, but always emits its best guess",
    "naive_tracklets_full_catch": "standard tracker upstream + all cues, alarms, splits",
}


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows:
        assert len(r) == len(header), (header, r)
        out.append("| " + " | ".join(esc(x) for x in r) + " |")
    return "\n".join(out)


def params_table(block):
    if not block:
        return "_No parameters._"
    rows = []
    for k, p in block.items():
        v = p["value"]
        rows.append([f"`{k}`", v if not isinstance(v, list) else ", ".join(str(x) for x in v), p["unit"], p["why"]])
    return table(["Parameter", "Value", "Unit", "Why"], rows)


def fmt(x, nd=3):
    if x is None:
        return "-"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def results_section(res):
    if res is None:
        return ("_The harness has not been run yet (`python tools/specgen/identity/harness.py`)._", "", "")
    summ = [s for s in res["summary"]]
    by = {(s["config"], s["profile"], s["sigma_p"], s["mode"]): s for s in summ}
    games = sorted({r["game"] for r in res["per_game"]})
    frames = {}
    for r in res["per_game"]:
        frames[r["game"]] = r["frames"]
    minutes = sum(frames.values()) * 0.04 / 60
    tables = []
    for prof in SPEC["harness"]["cue_profiles"]:
        rows = []
        for cfg in CONFIG_ORDER:
            for sig in sorted({s["sigma_p"] for s in summ if s["profile"] == prof and s["config"] == cfg}):
                off, live = by.get((cfg, prof, sig, "offline")), by.get((cfg, prof, sig, "live"))
                if off is None:
                    continue
                rows.append([f"`{cfg}`", CONFIG_NOTE.get(cfg, ""), f"{sig:.2f}", off["swap_events"], live["swap_events"] if live else "-",
                             fmt(off["idf1"]), fmt(off["hota"]), fmt(off["coverage"]), fmt(live["coverage"]) if live else "-",
                             fmt(off["reconfirm_median_s"], 2), off["games"]])
        if rows:
            note = SPEC["harness"]["cue_profiles"][prof]["note"]
            tables.append(f"**Cue profile `{prof}`** ({note}). Swaps are summed over the games; the scores are weighted by player boxes.\n\n"
                          + table(["Config", "What it is", "sigma_p (m)", "Swaps offline", "Swaps live", "IDF1 offline", "HOTA offline",
                                   "Coverage offline", "Coverage live", "Re-confirm median (s)", "Games"], rows))
    full_good = [by.get(("full", "good", sg, "offline")) for sg in (0.15, 0.3)]
    acc_h1 = all(x is not None and x["swap_events"] == 0 for x in full_good)
    naive = by.get(("naive_tracker", "good", 0.3, "offline"))
    head = (f"Three NBA SportVU 2015-16 games ({', '.join(games)}; {minutes:.0f} minutes of tracked play) with true ids; ids stripped, "
            "noise, broadcast view, occlusions, cuts and simulated cues added (section 14). ")
    if all(x is not None for x in full_good):
        head += (f"The spec (`full`, cue profile good) makes **{full_good[0]['swap_events']} swap events offline at sigma_p 0.15 m and "
                 f"{full_good[1]['swap_events']} at 0.30 m** (acceptance ACC-H1: {'met' if acc_h1 else 'NOT met'}). ")
    if naive is not None:
        head += f"A standard tracker on the same detections makes {naive['swap_events']} (sigma_p 0.30 m)."
    f = []
    s3 = {c: by.get((c, "good", 0.3, "offline")) for c in CONFIG_ORDER}
    if all(s3.get(c) for c in ("full", "naive_tracker")):
        f.append(f"- **Prevention, not repair.** The standard tracker extends tracks through crossings and keeps the first label: "
                 f"{s3['naive_tracker']['swap_events']} swap events at sigma_p 0.30 m. With the same detections and cues, pure tracklets, "
                 f"encounter groups and abstention give {s3['full']['swap_events']}.")
    if s3.get("naive_tracklets_full_catch"):
        f.append(f"- **Catching after the fact is not enough.** Giving the standard tracker every cue, live alarms and offline "
                 f"change-point splits still leaves {s3['naive_tracklets_full_catch']['swap_events']} swap events "
                 f"({s3['naive_tracklets_full_catch']['offline_splits']} splits applied): swaps must be prevented at the tracklet layer, "
                 "and alarms and splits are the safety net.")
    if s3.get("full_forced"):
        f.append(f"- **Abstention is necessary.** The same spec forced to always emit its best guess makes "
                 f"{s3['full_forced']['swap_events']} swap events, with coverage {fmt(s3['full_forced']['coverage'])} instead of "
                 f"{fmt(s3['full']['coverage'])}.")
    if s3.get("motion_team") and s3.get("motion_team_lineup"):
        f.append(f"- **Team colour and the lineup alone label nobody** (coverage {fmt(s3['motion_team']['coverage'])} and "
                 f"{fmt(s3['motion_team_lineup']['coverage'])}): they only decide which five candidates a box can be.")
    steps = [c for c in ("plus_jersey", "plus_appearance", "full") if s3.get(c)]
    if steps:
        f.append("- **Each identity cue adds coverage without adding swaps:** " + "; ".join(
            f"`{c}` {fmt(s3[c]['coverage'])} (swaps {s3[c]['swap_events']})" for c in steps) + ".")
    if s3.get("full_no_jersey") and s3.get("full_no_lineup"):
        f.append(f"- **Dropping a cue costs coverage:** without jersey numbers {fmt(s3['full_no_jersey']['coverage'])} "
                 f"(swaps {s3['full_no_jersey']['swap_events']}); without the lineup {fmt(s3['full_no_lineup']['coverage'])} "
                 f"(swaps {s3['full_no_lineup']['swap_events']}).")
    fs = [by.get(("full", "good", sg, "offline")) for sg in (0.15, 0.3, 0.5)]
    if all(fs):
        f.append(f"- **Position precision sets the coverage.** At sigma_p 0.15 / 0.30 / 0.50 m the spec labels "
                 f"{fmt(fs[0]['coverage'])} / {fmt(fs[1]['coverage'])} / {fmt(fs[2]['coverage'])} of player boxes offline "
                 f"(swaps {fs[0]['swap_events']} / {fs[1]['swap_events']} / {fs[2]['swap_events']}). Two players closer than "
                 "about 4 sigma cannot be kept apart by motion, so their boxes wait on HOLD until a cue says who is who.")
    fp = [by.get(("full", "poor", sg, "offline")) for sg in (0.15, 0.3, 0.5)]
    fu = [by.get(("full", "poor_uncalibrated", sg, "offline")) for sg in (0.15, 0.3, 0.5)]
    if all(fp):
        f.append(f"- **Poor video** (720p, dim, blur), assigner calibrated for it: swaps {fp[0]['swap_events']} / {fp[1]['swap_events']} / "
                 f"{fp[2]['swap_events']}, coverage {fmt(fp[0]['coverage'])} / {fmt(fp[1]['coverage'])} / {fmt(fp[2]['coverage'])} at sigma_p "
                 "0.15 / 0.30 / 0.50 m: appearance no longer separates teammates, so almost every label waits for two jersey sightings.")
    if all(fu):
        f.append(f"- **Calibration is a safety rule, not a tuning detail.** The same poor video read with the good-video cue parameters "
                 f"makes {fu[0]['swap_events']} / {fu[1]['swap_events']} / {fu[2]['swap_events']} swap events (coverage {fmt(fu[0]['coverage'])} / "
                 f"{fmt(fu[1]['coverage'])} / {fmt(fu[2]['coverage'])}): overconfident appearance evidence locks wrong labels. Cue "
                 "parameters must be refitted per recording quality on labelled crops before any label is trusted.")
    prow = []
    for prof in SPEC["harness"]["cue_profiles"]:
        for sg in (0.15, 0.3, 0.5):
            x = by.get(("full", prof, sg, "offline"))
            if x is not None and x.get("probable_labels") is not None:
                prow.append([f"`{prof}`", f"{sg:.2f}", x["swap_events"], fmt(x["coverage"]), fmt(x["probable_coverage_gain"]),
                             fmt(x["coverage_with_probable"]), x["probable_labels"], x["probable_wrong_frames"],
                             fmt(x["probable_error_rate"], 4), x["probable_wrong_events"]])
    if prow:
        tables.append("**Probable tier** (owner decision OD-8: offline only, flagged, shown to viewers, never feeds stats; config `full`). "
                      "Locked swaps and coverage are the locked tier's own numbers and do not change; probable errors are logged "
                      "here and are not locked swaps.\n\n"
                      + table(["Cue profile", "sigma_p (m)", "Locked swaps", "Locked coverage", "Probable gain", "Coverage with probable",
                               "Probable labels", "Probable wrong", "Probable error rate", "Probable wrong runs"], prow))
        g3 = by.get(("full", "good", 0.3, "offline"))
        if g3 and g3.get("probable_labels") is not None:
            f.append(f"- **Probable tier** (OD-8, offline, flagged, never in stats): at sigma_p 0.30 m on good video it adds "
                     f"{fmt(g3['probable_coverage_gain'])} of player boxes ({fmt(g3['coverage'])} -> {fmt(g3['coverage_with_probable'])}) "
                     f"with {g3['probable_wrong_frames']} wrong of {g3['probable_labels']} probable labels "
                     f"(error rate {fmt(g3['probable_error_rate'], 4)}, {g3['probable_wrong_events']} wrong runs); locked swaps unchanged.")
    fg = by.get(("full", "good", 0.3, "offline"))
    if fg and fg.get("calibration"):
        f.append("- **Posterior calibration** (`full`, good, sigma_p 0.30 m, offline): " + "; ".join(
            f"posterior {b['bin'][0]}-{b['bin'][1]}: {b['labels']} labels, {b['wrong']} wrong" for b in fg["calibration"]) + ".")
    if summ:
        inv = sum(s_.get("inv1_duplicates", 0) + s_.get("inv2_over_five", 0) + s_.get("inv3_outside_lineup", 0) for s_ in summ
                  if s_["config"] not in ("naive_tracker",))
        f.append(f"- Invariants ID-INV-1 to ID-INV-3 broken {inv} times over every config and noise level.")
    f.append("- The cue error rates are assumptions (section 14); the real jersey read rate and OCR error on our recordings are the "
             "largest unknowns (open question OQ-3).")
    return head, "\n\n".join(tables), "\n".join(f)


def build():
    tpl = (HERE / "doc_template.md").read_text()
    res = json.loads(RESULTS.read_text()) if RESULTS.exists() else None
    head, rtable, findings = results_section(res)
    rep = {
        "DATE": SPEC["date"], "VERSION": SPEC["version"], "STATUS": SPEC["status"], "RESULTS_FILE": SPEC["harness"]["results_file"],
        "P_LOCK": idlib.P["p_lock"], "HEADLINE": head, "RESULTS_TABLE": rtable, "FINDINGS": findings,
    }
    rq = SPEC["requirement"]
    rs = rq.get("recording_standard")
    rep["CONSTRAINTS"] = "\n".join(f"- {c}" for c in SPEC["standing_constraints"]) + \
        "\n\nForbidden as cues: " + ", ".join(f"`{c}`" for c in SPEC["forbidden_cues"]) + "." + \
        (f"\n\n**Zero swaps.** {rq['zero_swaps']}" if rq.get("zero_swaps") else "") + \
        (f"\n\n**Recording standard ({rs['acceptance']}).** {rs['rule']} Why: {rs['why']}." if rs else "")
    r = SPEC["research"]
    rep["RESEARCH"] = r["summary"].strip() + "\n\n" + table(["Source", "What it supports"], [[f"[{s['ref']}]({s['url']})", s["supports"]] for s in r["sources"]]) \
        + "\n\n" + r["provider_note"].strip()
    rep["PRINCIPLES"] = table(["Id", "Rule", "Why"], [[p["id"], p["rule"], p["why"]] for p in SPEC["design_principles"]])
    rp = SPEC["reference_pack"]
    parts = [rp["summary"]]
    for key, title in (("per_player_season", "Per player, per season"), ("per_player_game_card", "Per player, per game (appearance card)"),
                       ("per_team_game_kit", "Per team, per game (kit card)")):
        blk = rp[key]
        if "filled" in blk:
            title += f". Filled {blk['filled']}"
        rows = [[f"`{k}`", v.get("type", ""), v.get("source", v.get("unit", "")), v.get("why", "")] for k, v in blk["fields"].items()]
        parts.append(f"**{title}.**\n\n" + table(["Field", "Type", "Source", "Why"], rows))
    parts.append(f"Privacy: {rp['privacy']}")
    rep["PACK"] = "\n\n".join(parts)
    cues = []
    for c in SPEC["cues"]:
        s = [f"### 6.{c['order']} `{c['id']}`", "", f"- **Observation:** {c['observation']}", f"- **Model:** {c['model'].strip()}",
             f"- **Valid when:** {c['validity']}"]
        if c.get("hard_cases"):
            s.append("- **Hard cases:** " + "; ".join(c["hard_cases"]))
        s += ["", params_table(c.get("params") or {})]
        cues.append("\n".join(s))
    cues.append("### Common to all cues\n\n" + params_table(SPEC["cue_common"]["params"]))
    rep["CUES"] = "\n\n".join(cues)
    rules = []
    for sec, title in (("tracklets", "7.1 Tracklets"), ("chains", "7.2 Chains"), ("assignment", "7.3 Joint assignment")):
        b = SPEC[sec]
        rules.append(f"### {title}\n\n{b['summary']}\n\n```text\n{b['rule'].rstrip()}\n```\n\n{params_table(b['params'])}"
                     + (f"\n\nOutputs: {', '.join(b['outputs'])}." if b.get("outputs") else ""))
    rep["RULES"] = "\n\n".join(rules)
    sm = SPEC["state_machine"]
    rep["STATE_MACHINE"] = sm["summary"] + "\n\n" + table(["State", "Meaning"], [[f"`{k}`", v] for k, v in sm["states"].items()]) + "\n\n" \
        + table(["Id", "From", "To", "When"], [[t["id"], ", ".join(t["from"]) if isinstance(t["from"], list) else t["from"], t["to"], t["when"]]
                                                for t in sm["transitions"]]) \
        + "\n\nInvariants checked on every frame:\n\n" + "\n".join(f"- **{i['id']}**: {i['rule']}" for i in sm["invariants"])
    sc = SPEC["swap_catch"]
    rep["SWAP_CATCH"] = f"{sc['summary']}\n\n```text\n{sc['rule'].rstrip()}\n```\n\n{params_table(sc['params'])}"
    ca = SPEC["confidence_and_abstention"]
    rep["ABSTAIN"] = f"```text\n{ca['rule'].rstrip()}\n```\n\n{params_table(ca['params'])}"
    rep["HARD_CASES"] = table(["Id", "Case", "Handling", "Test"], [[h["id"], h["case"], h["handling"], f"`{h['test']}`"] for h in SPEC["hard_cases"]])
    o = SPEC["outputs"]
    rep["OUTPUTS"] = "\n".join(
        f"- **{k.replace('_', ' ')}**: " + ", ".join(f"`{x}`" for x in v["fields"]) + (f". {v['rule']}" if v.get("rule") else "")
        for k, v in o.items())
    rep["METRICS"] = table(["Id", "Metric", "Definition"], [[f"`{m['id']}`", m["name"], m["definition"]] for m in SPEC["metrics"]]) + "\n\n" \
        + table(["Id", "Metric", "Scope", "Threshold", "If it fails"], [[a["id"], f"`{a['metric']}`", a["scope"], a["threshold"], a["on_fail"]]
                                                                        for a in SPEC["acceptance"]]) \
        + f"\n\n**Gold sample.** {SPEC['gold_sample']['plan']}"
    h = SPEC["harness"]
    prof_keys = list(h["cue_profiles"]["good"])

    def cell(v):
        if isinstance(v, list):
            return ", ".join(map(str, v))
        if isinstance(v, dict):
            return "; ".join(f"{a} {b}" for a, b in v.items()) or "none (YAML values)"
        return v
    prof_rows = [[k] + [cell(h["cue_profiles"][p].get(k, "")) for p in h["cue_profiles"]] for k in prof_keys]
    cfg_rows = [[f"`{k}`", v["tracklets"], ", ".join(v["cues"]), v["lineup"], v["abstain"], v["alarms"], v["splits"], v.get("note", "")]
                for k, v in h["configs"].items()]
    rep["HARNESS"] = h["summary"].strip() + f"\n\nData: {h['data']}\n\n" + params_table(h["params"]) \
        + f"\n\n{h['calibration_note']}" \
        + f"\n\nNoise grid sigma_p: {', '.join(map(str, h['noise_grid_sigma_p_m']))} m (white + AR(1) mix of tools/specgen/movement/sim.py)." \
        + "\n\nHeights are not in SportVU; they are drawn per roster position (G / F / C mean and sd: " \
        + "; ".join(f"{k} {v[0]} / {v[1]} m" for k, v in h["height_by_position_m"].items()) + ")." \
        + "\n\n**Cue profiles** (simulator truth; the assigner keeps the YAML cue parameters):\n\n" \
        + table(["Field"] + list(h["cue_profiles"]), prof_rows) \
        + "\n\n**Configs** (ablations of the spec):\n\n" + table(["Config", "Tracklets", "Cues", "Lineup", "Abstain", "Alarms", "Splits", "Note"], cfg_rows) \
        + ("\n\nProduction-only parameters (act on pixels, OCR scores, crop banks or the gold sample; the harness has none): "
           + ", ".join(f"`{p}`" for p in SPEC["production_only_params"]) + ".")
    rep["QUESTIONS"] = "\n".join(f"- **{q['id']}**: {q['question']}" + (f" **{q['decision']}**" if q.get("decision") else "")
                                  for q in SPEC["open_questions"])
    if SPEC.get("open_items"):
        rep["QUESTIONS"] += "\n\n**Action items**\n\n" + table(["Id", "Action", "Owner", "Status"], [
            [x["id"], x["action"], x["owner"], x["status"]] for x in SPEC["open_items"]])
    if SPEC.get("planned_work"):
        rep["QUESTIONS"] += "\n\n**Planned work (coverage levers)**\n\n" + table(["Id", "Lever", "Why", "How it is measured"], [
            [x["id"], x["lever"], x["why"], x["measure"]] for x in SPEC["planned_work"]])
    jr = []
    for j in SPEC["journal"]:
        jr.append(f"**{j['version']} ({j['date']})**\n\n" + "\n".join(f"- {c}" for c in j["changes"])
                  + ("\n\n" + table(["Id", "What", "Why", "Evidence"], [[x["id"], x["what"], x["why"], x["evidence"]]
                                                                        for x in j["decisions"]]) if j.get("decisions") else ""))
    if SPEC.get("review_round_1"):
        rr = SPEC["review_round_1"]
        jr.append("**Review round 1 (self-review against the requirements and hard cases)**\n\n"
                  + table(["Id", "Finding", "Fix", "Evidence"], [[x["id"], x["finding"], x["fix"], x["evidence"]] for x in rr]))
    rep["JOURNAL"] = "\n\n".join(jr)
    out = tpl
    for k, v in rep.items():
        out = out.replace("{{" + k + "}}", str(v))
    return out


def checks(text):
    errs = []
    if re.search(r"\{\{[A-Z_]+\}\}", text):
        errs.append("placeholder left")
    for name in idlib.P:
        if f"`{name}`" not in text:
            errs.append(f"param {name} missing")
    for h in SPEC["hard_cases"]:
        if h["id"] not in text:
            errs.append(f"hard case {h['id']} missing")
    for a in SPEC["acceptance"]:
        if a["id"] not in text:
            errs.append(f"acceptance {a['id']} missing")
    for t in SPEC["state_machine"]["transitions"]:
        if t["id"] not in text:
            errs.append(f"transition {t['id']} missing")
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
            print(f"{out} is out of date: run python tools/specgen/identity/gen_doc.py")
            sys.exit(1)
        return
    out.write_text(text)
    print(f"wrote {out} ({len(text.splitlines())} lines)")


if __name__ == "__main__":
    main()
