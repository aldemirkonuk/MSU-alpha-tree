"""Real-data replay of the reference fuser (live-state baseline 4).

Truth = the kept 1 fps scorebug readings of the private MSU broadcasts (game clock, period, score total; shot clock,
team fouls and timeouts where read). For each game and seed, extra stretches of the bug are hidden on purpose
(lengths drawn from the real hidden-stretch distribution, about extra_hidden_share of the visible seconds). The
fuser (fuse.py) sees only what stays visible, plus, per configuration:
  cues   stand-ins for whistle audio and CV: the true stop / start instants of the clock and the true shot-clock
         resets, each delivered with a set probability. AN ASSUMPTION SWEEP - no such sensor is measured yet.
  feed   the play-by-play score rows, arriving L seconds after the video time at which the bug clock showed the
         clock second of the row. The absolute feed latency is NOT measured (OQ-LS-1): L is swept.
  slot   only the shot-clock slot is hidden (the game clock stays read): rule FOLLOW_FIELD.
Every hidden second is scored against the reading the fuser was not shown.

Reads private data, writes aggregates only (game codes B01.., no team names, no ids):
  results/live_state_test/harness.json and results/live_state_test/README.md

Usage: python tools/specgen/live_state/harness.py [--games N] [--seeds N] [--workers 2] [--no-write]
"""
from __future__ import annotations

import argparse
import bisect
import json
import random
import sys
import time
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fuse  # noqa: E402
import lslib  # noqa: E402
import measure_real as mr  # noqa: E402

OUT = lslib.REPO / "results" / "live_state_test" / "harness.json"
README = lslib.REPO / "results" / "live_state_test" / "README.md"
AGES = [(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 10), (11, 20), (21, 30), (31, 10 ** 6)]
MIN_N_PER_AGE = 200   # an age bucket is held to the promise only with at least this many inferred seconds
COUNTERS = ("score_total", "team_fouls_home", "team_fouls_away", "timeouts_left_home", "timeouts_left_away")
ALIAS = {"score_total": "score_home"}   # the private reads keep the score total only; it follows the score rules
CATCH_UP_CAP_S = 30


def age_bucket(a):
    for lo, hi in AGES:
        if lo <= a <= hi:
            return str(lo) if lo == hi else f"{lo}-{hi}" if hi < 10 ** 6 else f"{lo}+"
    return "0"


def configs(P):
    """The runs of one game and seed, from the harness params of core.yaml."""
    if not any(P["whistle_recall"] in c for c in P["cue_configs"]):
        raise SystemExit("cue_configs must hold a run at whistle_recall of the audio sensor")
    out = [{"name": f"cues_{s}_{a}_{r}", "mode": "bug", "stop": s, "start": a, "reset": r, "feed": None}
           for s, a, r in P["cue_configs"]]
    out += [{"name": f"feed_{L}s", "mode": "bug", "stop": 0, "start": 0, "reset": 0, "feed": L}
            for L in P["feed_delay_sweep_s"] if L != "none"]
    out += [{"name": f"slot_{r}", "mode": "slot", "stop": 0, "start": 0, "reset": r, "feed": None}
            for r in P["shot_slot_configs"]]
    return out


# ------------------------------------------------------------------------------------------------- one game's data
def prepare(g):
    """Private game record -> what a run needs: truth per second, true cue instants, score rows."""
    S = g["align"]["samples"]
    cal = g["state"]["calib"]
    kept = {s[0] for s in S}
    tok = {}
    with open(g["ocr"]) as fh:
        for line in fh:
            r = json.loads(line)
            if r["t"] in kept:
                tok[r["t"]] = mr.parse_tokens(r["o"], cal)
    truth = {}
    for t, period, rem, _G, total in S:
        o = tok.get(t, {})
        truth[t] = {"period": period, "rem": rem, "score_total": total, "shot": o.get("shot"),
                    "team_fouls_home": o.get("fouls_l"), "team_fouls_away": o.get("fouls_r"),
                    "timeouts_left_home": o.get("to_l"), "timeouts_left_away": o.get("to_r")}
    stops, starts, resets = [], [], []
    for a, b, c in zip(S, S[1:], S[2:]):
        if not (b[0] - a[0] == 1 and c[0] - b[0] == 1 and a[1] == b[1] == c[1]):
            continue
        ran_ab, ran_bc = b[3] - a[3] >= 0.5, c[3] - b[3] >= 0.5
        if ran_ab and not ran_bc:
            stops.append(b[0])
        if not ran_ab and ran_bc:
            starts.append(b[0])
    for a, b in zip(S, S[1:]):
        sa, sb = truth[a[0]]["shot"], truth[b[0]]["shot"]
        if b[0] - a[0] == 1 and a[1] == b[1] and sa is not None and sb is not None and sb > sa:
            resets.append((b[0], sb))
    Gs = [s[3] for s in S]
    rows, last = [], None
    for p in mr.sorted_plays(g["plays"]):
        total = (p.get("homeScore") or 0) + (p.get("awayScore") or 0)
        if not p.get("scoringPlay") or p.get("playType") not in mr.FG_TYPES or total == last:
            continue   # made field goals only: a free throw has no clock second of its own, so its row cannot be placed in video time
        last = total
        i = bisect.bisect_left(Gs, p["_G"] - 1e-6)
        if i < len(S):
            rows.append((S[i][0], p["period"], p["secondsRemaining"], total))
    return {"code": g["code"], "S": S, "truth": truth, "stops": stops, "starts": starts, "resets": resets, "rows": rows}


def hide(S, lengths, share, rng):
    """Seconds hidden on purpose: stretches whose lengths are drawn from the measured real hidden stretches."""
    ts = [s[0] for s in S][10:-10]
    want, hidden = int(share * len(ts)), set()
    have = set(ts)
    while len(hidden) < want:
        t0, n = rng.choice(ts), rng.choice(lengths)
        hidden.update(t for t in range(t0, t0 + n) if t in have)
    return hidden


# --------------------------------------------------------------------------------------------------------- one run
def run_one(spec, d, hidden, cfg, rng, A, per_game):
    P = spec.P
    tol, name, slot = P["clock_tolerance_s"], cfg["name"], cfg["mode"] == "slot"
    truth, S = d["truth"], d["S"]
    f = fuse.Fuser(spec, counters=COUNTERS, alias=ALIAS, feed=cfg["feed"] is not None, audio=cfg["stop"] > 0,
                   rim_watch=False, feed_fields={"score_total"})
    cue_delay = int(round(P["audio_delay_p50_s"]))            # 0 at the 1 s resolution of the replay
    msgs = {}
    for ts, what, p in ((d["stops"], "stop", cfg["stop"]), (d["starts"], "start", cfg["start"])):
        for t in ts:
            if rng.random() < p:
                msgs.setdefault(t + cue_delay, []).append({"kind": "cue", "what": what})
    for t, v in d["resets"]:
        if rng.random() < cfg["reset"]:
            msgs.setdefault(t, []).append({"kind": "cue", "what": "shot_reset", "value": v})
    if cfg["feed"] is not None:
        for t, period, rem, total in d["rows"]:
            msgs.setdefault(t + cfg["feed"], []).append({"kind": "pbp", "field": "score_total", "value": total,
                                                         "period": period, "clock_s": rem})
    vis_rem = vis_t = vis_status = vis_period = None   # the plain rules on every reading shown, kept by the harness
    acc = None                                         # last status on the readings the fuser accepted: (rem, t, status, period)
    prev_vis, prev_hidden = None, False
    prev_snap, prev_period, catch = None, None, None
    for t in range(S[0][0], S[-1][0] + 1):
        tr = truth.get(t)
        is_hidden = t in hidden
        n_log = len(f.log)
        f.advance(t)
        for m in msgs.get(t, ()):
            if m["kind"] != "pbp":
                f.feed_msg({"t": t, **m})
        pbp_now = False
        for m in msgs.get(t, ()):
            if m["kind"] == "pbp":
                f.feed_msg({"t": t, **m})
                pbp_now = True
        shown_clock = tr is not None and (slot or not is_hidden)
        before = None
        if shown_clock and f.c.read is not None:
            before = (f.clock_est(), f.snapshot()["game_clock_s"]["grade"], fuse.Fuser._gap(f, f.c.read_t) or f.c.reads == 0)
        if shown_clock:
            m = {"t": t, "kind": "bug", "period": tr["period"], "clock_s": tr["rem"]}
            for k in COUNTERS:
                if tr[k] is not None:
                    m[k] = tr[k]
            if tr["shot"] is not None and not (slot and is_hidden):
                m["shot_s"] = tr["shot"]
            f.feed_msg(m)
        s = f.snapshot()
        new_logs = f.log[n_log:]
        # ---- H2: impossible values
        for k, v in s.items():
            if v["value"] is None or v["grade"] is None:
                A[name, "violations", "null"] += 1
            if v["grade"] in ("observed", "confirmed"):
                seen = (shown_clock and k in ("game_clock_s", "game_clock_running", "period")) \
                    or (shown_clock and k == "shot_clock_s" and tr["shot"] is not None and not (slot and is_hidden)) \
                    or (shown_clock and tr.get(k) is not None) or (pbp_now and k == "score_total")
                if not seen:
                    A[name, "violations", "observed_without_observation"] += 1
        cv, pv = s["game_clock_s"]["value"], None if prev_snap is None else prev_snap["game_clock_s"]["value"]
        if isinstance(cv, float) and isinstance(pv, float) and s["period"]["value"] == prev_period and cv > pv + tol \
                and not any(r["field"] in ("game_clock_s", "period") for r in new_logs):
            A[name, "violations", "clock_rise_without_log"] += 1
        if prev_snap is not None:
            a, b = prev_snap["score_total"]["value"], s["score_total"]["value"]
            if isinstance(a, int) and isinstance(b, int) and b < a \
                    and not any(r["field"] == "score_total" and r["log"] == "state_corrections" for r in new_logs):
                A[name, "violations", "score_fall_without_correction"] += 1
        # ---- H3: return behaviour
        if before is not None and before[2] and not slot and s["period"]["value"] == prev_period:
            est, grade, _ = before
            A[name, "returns", "n"] += 1
            accepted = f.c.read_t == t
            miss = accepted and abs(tr["rem"] - est) > P["snap_log_tolerance_s"]
            logged = any(r["field"] == "game_clock_s" for r in new_logs)   # snap_miss, or an official correction
            A[name, "returns", "miss_beyond_tolerance"] += bool(miss)
            A[name, "returns", "miss_log_mismatch"] += bool(miss) != logged
        if shown_clock and prev_vis is not None and prev_vis[0] == t - 1 and prev_vis[1] and not slot and f.c.read_t == t \
                and prev_vis[2] == tr["period"]:
            A[name, "returns", "second_reading"] += 1          # the reading that follows a return
            A[name, "returns", "second_reading_observed_and_equal"] += \
                s["game_clock_s"]["grade"] == "observed" and abs(s["game_clock_s"]["value"] - tr["rem"]) < 1e-9
        prev_vis = (t, before is not None and before[2] and f.c.read_t == t, tr["period"]) if shown_clock else prev_vis
        # ---- score: time to catch up after a hidden stretch in which it changed
        if catch is not None and tr is not None and not is_hidden and tr["score_total"] is not None:
            if s["score_total"]["value"] == tr["score_total"] or t - catch >= CATCH_UP_CAP_S:
                A[name, "score_catch_up_s", str(min(t - catch, CATCH_UP_CAP_S))] += 1
                catch = None
        # ---- hidden seconds: the value the fuser holds against the reading it was not shown
        if is_hidden and tr is not None:
            if slot:
                _score(A, name, "shot_clock_s", s["shot_clock_s"], tr["shot"], tol, age=True)
            else:
                c = s["game_clock_s"]
                if vis_t is not None and tr["period"] == vis_period:
                    age = t - vis_t
                    b = age_bucket(age)
                    hold, run = vis_rem, max(0.0, vis_rem - age)
                    last = run if vis_status == "running" else hold
                    spec_est = None if f.clock_est() is None else min(max(f.clock_est(), c["lo"]), c["hi"])
                    A[name, "clock_by_age", b, "n"] += 1
                    last_acc = None
                    if acc is not None and acc[3] == tr["period"]:
                        last_acc = max(0.0, acc[0] - (t - acc[1])) if acc[2] == "running" else acc[0]
                    for rule, est in (("hold", hold), ("run", run), ("last_status", last), ("last_status_accepted", last_acc), ("spec", spec_est)):
                        A[name, "clock_by_age", b, rule] += est is not None and abs(est - tr["rem"]) <= tol
                    A[name, "clock_by_age", b, "grade_" + c["grade"]] += 1
                    ok = isinstance(c["value"], float) and abs(c["value"] - tr["rem"]) <= tol
                    A[name, "clock_by_grade", c["grade"], "n"] += 1
                    A[name, "clock_by_grade", c["grade"], "within"] += ok
                    A[name, "clock_interval", "n"] += 1
                    A[name, "clock_interval", "truth_inside"] += c["lo"] - tol <= tr["rem"] <= c["hi"] + tol
                    if c["grade"] == "inferred":
                        per_game[name, "n"] += 1
                        per_game[name, "within"] += ok
                        A[name, "inferred_by_age", "game_clock_s", b, "n"] += 1
                        A[name, "inferred_by_age", "game_clock_s", b, "equal"] += ok
                    rs = s["game_clock_running"]
                    if rs["grade"] == "inferred" and t + 1 in truth and truth[t + 1]["period"] == tr["period"]:
                        ran = tr["rem"] - truth[t + 1]["rem"] >= 0.5
                        A[name, "running_flag_inferred", "n"] += 1
                        A[name, "running_flag_inferred", "right"] += (rs["value"] == "running") == ran
                _score(A, name, "period", s["period"], tr["period"], 0)
                _score(A, name, "shot_clock_s", s["shot_clock_s"], tr["shot"], tol, age=True)
                for k in COUNTERS:
                    _score(A, name, k, s[k], tr[k], 0, age=True)
                if tr["score_total"] is not None and isinstance(s["score_total"]["value"], int):
                    # the feed can be ahead of the bug: equal to what the bug shows now or inside the confirm window
                    ahead = {truth[u]["score_total"] for u in range(t, t + int(P["pbp_to_bug_window_s"]) + 1) if u in truth}
                    A[name, "score_now_or_ahead", "n"] += 1
                    A[name, "score_now_or_ahead", "equal"] += s["score_total"]["value"] in ahead
        if tr is not None and not is_hidden and not slot:
            if prev_hidden and tr["score_total"] is not None and isinstance(prev_snap["score_total"]["value"], int) \
                    and prev_snap["score_total"]["value"] != tr["score_total"] and catch is None:
                catch = t
        if shown_clock:
            if vis_t is None or t - vis_t > 2 or vis_period != tr["period"]:
                vis_status = "unknown"                         # as measure_real.status_before
            else:
                vis_status = "running" if vis_rem - tr["rem"] >= 0.5 else "stopped"
            vis_rem, vis_t, vis_period = tr["rem"], t, tr["period"]
            if f.c.read_t == t:                                # the fuser accepted this reading
                st = "unknown" if acc is None or t - acc[1] > 2 or acc[3] != tr["period"] else \
                    "running" if acc[0] - tr["rem"] >= 0.5 else "stopped"
                acc = (tr["rem"], t, st, tr["period"])
        prev_hidden = is_hidden and tr is not None
        prev_snap, prev_period = s, s["period"]["value"]
    for r in f.log:
        A[name, "log", r["log"], r["field"], r["kind"]] += 1
    A[name, "counts", "rejected_reads"] += f.counts["rejected_reads"]
    A[name, "counts", "versions_opened"] += f.version - 1
    A[name, "counts", "runs"] += 1
    A[name, "counts", "hidden_s"] += len(hidden)


def _score(A, name, field, state, truth_value, tol, age=False):
    if truth_value is None:
        return
    g, v = state["grade"], state["value"]
    ok = isinstance(v, (int, float)) and abs(v - truth_value) <= tol
    A[name, "by_grade", field, g, "n"] += 1
    A[name, "by_grade", field, g, "equal"] += ok
    if g == "inferred":
        b = age_bucket(int(state["age_s"]))
        A[name, "inferred_by_age", field, b, "n"] += 1
        A[name, "inferred_by_age", field, b, "equal"] += ok
    if age:
        b = age_bucket(int(state["age_s"]))
        A[name, "by_age", field, b, "n"] += 1
        A[name, "by_age", field, b, "equal"] += ok


def run_game(args):
    d, seeds, lengths = args
    spec = fuse.Spec()
    A, rows = Counter(), []
    per_game = Counter()
    for seed in range(seeds):
        rng = random.Random(f"{d['code']}-{seed}")
        hidden = hide(d["S"], lengths, spec.P["extra_hidden_share"], rng)
        for cfg in configs(spec.P):
            run_one(spec, d, hidden, cfg, random.Random(f"{d['code']}-{seed}-{cfg['name']}"), A, per_game)
    for cfg in configs(spec.P):
        n = per_game[cfg["name"], "n"]
        rows.append({"game": d["code"], "config": cfg["name"], "inferred_clock_s": n,
                     "inferred_within_tolerance": round(per_game[cfg["name"], "within"] / n, 4) if n else None})
    return A, rows


def _prepare_worker(args):
    """Load one private game (same files as measure_real.load_games) and prepare it."""
    key, code = args
    d = mr.STATE / key
    st = json.loads((d / "state.json").read_text())
    g = {"key": key, "code": code, "state": st, "align": json.loads((d / "align.json").read_text()),
         "ocr": d / "ocr.jsonl", "plays": json.loads(Path(st["plays_file"]).read_text())}
    return prepare(g)


# ------------------------------------------------------------------------------------------------------- aggregate
def nest(A):
    out = {}
    for key, v in sorted(A.items(), key=lambda kv: tuple(map(str, kv[0]))):
        d = out
        for k in key[:-1]:
            d = d.setdefault(str(k), {})
        d[str(key[-1])] = int(v)
    return out


def share(n, d):
    return round(n / d, 4) if d else None


def summarise(tree, rows, P):
    """Shares and the acceptance verdicts, from the raw counts."""
    out = {}
    for name, c in tree.items():
        o = {}
        cg = c.get("clock_by_grade", {})
        o["clock_by_grade"] = {g: {"n": x["n"], "within_tolerance": share(x.get("within", 0), x["n"])} for g, x in cg.items()}
        o["clock_by_age"] = {b: {"n": x["n"], **{r: share(x.get(r, 0), x["n"]) for r in ("spec", "last_status_accepted", "last_status", "hold", "run")},
                                 "grades": {k[6:]: v for k, v in x.items() if k.startswith("grade_")}}
                             for b, x in c.get("clock_by_age", {}).items()}
        ci = c.get("clock_interval", {})
        o["clock_interval_holds_truth"] = share(ci.get("truth_inside", 0), ci.get("n", 0))
        rf = c.get("running_flag_inferred", {})
        o["running_flag_inferred_right"] = {"n": rf.get("n", 0), "share": share(rf.get("right", 0), rf.get("n", 0))}
        o["by_grade"] = {f: {g: {"n": x["n"], "equal": share(x.get("equal", 0), x["n"])} for g, x in fg.items()}
                         for f, fg in c.get("by_grade", {}).items()}
        o["inferred_by_age"] = {f: {b: {"n": x["n"], "within_tolerance": share(x.get("equal", 0), x["n"])} for b, x in fb.items()}
                                for f, fb in c.get("inferred_by_age", {}).items()}
        o["by_age"] = {f: {b: {"n": x["n"], "equal": share(x.get("equal", 0), x["n"])} for b, x in fb.items()}
                       for f, fb in c.get("by_age", {}).items()}
        na = c.get("score_now_or_ahead", {})
        o["score_equal_to_bug_now_or_within_window"] = {"n": na.get("n", 0), "share": share(na.get("equal", 0), na.get("n", 0))}
        cu = {int(k): v for k, v in c.get("score_catch_up_s", {}).items()}
        n = sum(cu.values())
        flat = sorted(k for k, v in cu.items() for _ in range(v))
        o["score_catch_up_s"] = {"n": n, "p50": flat[n // 2] if n else None, "p90": flat[int(0.9 * (n - 1))] if n else None,
                                 "max": flat[-1] if n else None, "cap_s": CATCH_UP_CAP_S}
        o["returns"] = c.get("returns", {})
        o["violations"] = c.get("violations", {})
        o["log_rows"] = c.get("log", {})
        o["counts"] = c.get("counts", {})
        mine = [r["inferred_within_tolerance"] for r in rows if r["config"] == name and r["inferred_within_tolerance"] is not None]
        o["inferred_clock_per_game"] = {"games": len(mine), "min": min(mine) if mine else None,
                                        "median": sorted(mine)[len(mine) // 2] if mine else None,
                                        "games_below_promise": sum(x < P["clock_inferred_promise"] for x in mine)}
        out[name] = o
    return out


def _honesty(summary, field, promise, pick):
    """Grade honesty of one field: pooled over its inferred seconds and at every age with enough of them."""
    out, ok = {}, True
    for n, s in summary.items():
        if not pick(n):
            continue
        ages = s["inferred_by_age"].get(field, {})
        tot = sum(x["n"] for x in ages.values())
        if not tot:
            continue
        pooled = round(sum(x["n"] * x["within_tolerance"] for x in ages.values()) / tot, 4)
        low = {b: x["within_tolerance"] for b, x in ages.items() if x["n"] >= MIN_N_PER_AGE and x["within_tolerance"] < promise}
        out[n] = {"n": tot, "pooled": pooled, "ages_below_promise": low}
        ok = ok and pooled >= promise and not low
    return out, ok


def verdicts(summary, P):
    v = {}
    promise = P["clock_inferred_promise"]
    h1, ok = _honesty(summary, "game_clock_s", promise, lambda n: not n.startswith("slot"))
    v["ACC-LS-H1"] = {"promise": promise, "min_n_per_age": MIN_N_PER_AGE, "game_clock_inferred": h1, "pass": ok}
    v["ACC-LS-H2"] = {"violations": {n: s["violations"] for n, s in summary.items()},
                      "pass": all(not s["violations"] for s in summary.values())}
    h3 = {n: s["returns"] for n, s in summary.items() if s["returns"]}
    v["ACC-LS-H3"] = {"returns": h3, "pass": all(r.get("miss_log_mismatch", 0) == 0 and
                                                 r.get("second_reading", 0) == r.get("second_reading_observed_and_equal", 0)
                                                 for r in h3.values())}
    worse = {}
    for n, s in summary.items():
        for b, x in s["clock_by_age"].items():
            if x["spec"] is not None and x["last_status_accepted"] is not None and x["spec"] < x["last_status_accepted"]:
                worse.setdefault(n, {})[b] = [x["spec"], x["last_status_accepted"]]
    v["ACC-LS-H4"] = {"compared_with": "plain last-status on the readings the fuser accepted",
                      "ages_where_spec_is_below_last_status": worse, "pass": not worse}
    shot, ok = _honesty(summary, "shot_clock_s", promise, lambda n: True)
    v["shot_clock_inferred"] = {"promise": promise, "min_n_per_age": MIN_N_PER_AGE, "by_config": shot, "pass": ok}
    return v


# ----------------------------------------------------------------------------------------------- text from numbers
def pc(x):
    return "n/a" if x is None else f"{100 * x:.1f} %"


def quoted_evidence(out):
    """The sentences of config/live_state/fields_scoreboard.yaml that quote this file. A spec test rebuilds them from
    harness.json and checks that the YAML still says the same."""
    s = out["summary"]

    def sh(n, b):
        return s[n]["by_age"]["shot_clock_s"][b]["equal"]

    def ca(n, b):
        return s[n]["clock_by_age"][b]["spec"]
    none, some, full = "cues_0.0_0.0_0.0", "cues_0.8_0.8_0.8", "cues_1.0_1.0_1.0"
    return {
        "shot_follow": f"following the game clock is within 1 s in {pc(sh('slot_0.0', '1'))} of hidden slot seconds after 1 s with no reset cue at all, and in {pc(sh('slot_0.0', '2'))} after 2 s and {pc(sh('slot_0.0', '3'))} after 3 s; with every reset the bug shows delivered as a cue {pc(sh('slot_1.0', '1'))}, {pc(sh('slot_1.0', '2'))} and {pc(sh('slot_1.0', '3'))}",
        "shot_blind": f"with the whole bug hidden and no cue the reckoned shot clock is within 1 s in {pc(sh(none, '1'))} after 1 s, {pc(sh(none, '2'))} after 2 s and {pc(sh(none, '3'))} after 3 s",
        "shot_horizon": f"within 1 s after 1 s in {pc(sh(none, '1'))} (bug hidden, no cue) and {pc(sh('slot_0.0', '1'))} (slot hidden, no cue); after 2 s in {pc(sh(none, '2'))} and {pc(sh('slot_0.0', '2'))}, and with every visible reset delivered as a cue still only {pc(sh(full, '2'))} and {pc(sh('slot_1.0', '2'))}; after 3 s {pc(sh(full, '3'))} and {pc(sh('slot_1.0', '3'))}",
        "cue_gain": f"with stand-in stop, start and reset cues at recall 0.8 the estimate is within 1 s in {pc(ca(some, '4'))} at 4 s, {pc(ca(some, '6-10'))} at 6-10 s and {pc(ca(some, '11-20'))} at 11-20 s after the last reading, against {pc(ca(none, '4'))}, {pc(ca(none, '6-10'))} and {pc(ca(none, '11-20'))} with no cue",
        "flag": f"{pc(s[none]['running_flag_inferred_right']['share'])} with no cue and {pc(s[some]['running_flag_inferred_right']['share'])} with cues at recall 0.8",
        # journal of core.yaml
        "journal_clock": "within 1 s in " + ", ".join(pc(s[none]["inferred_by_age"]["game_clock_s"][b]["within_tolerance"]) for b in ("1", "2")) +
                         f" and {pc(s[none]['inferred_by_age']['game_clock_s']['3']['within_tolerance'])} of inferred seconds at 1, 2 and 3 s, "
                         f"{pc(s[none]['clock_by_grade']['inferred']['within_tolerance'])} pooled, worst game {pc(s[none]['inferred_clock_per_game']['min'])}",
        "journal_shot": f"At 1 s the reckoned value is within 1 s in {pc(sh(none, '1'))} even with nothing watching for a reset; at 2 s it is {pc(sh(none, '2'))}, and {pc(sh(full, '2'))} with every visible reset delivered as a cue",
        "journal_interval": f"held the true clock in {100 * s[none]['clock_interval_holds_truth']:.2f} % of hidden seconds",
        "journal_cue": f"within 1 s in {pc(ca(some, '6-10'))} against {pc(ca(none, '6-10'))} at 6-10 s",
    }


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]
    return "\n".join(out + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows])


def write_readme(out):
    s, v, L = out["summary"], out["verdicts"], out["limits_used"]
    none, stop, some, full = "cues_0.0_0.0_0.0", "cues_0.8_0.0_0.0", "cues_0.8_0.8_0.8", "cues_1.0_1.0_1.0"
    ages = [b for b in ("1", "2", "3", "4", "5", "6-10", "11-20", "21-30", "31+") if b in s[none]["clock_by_age"]]
    a0 = s[none]
    runs = a0["counts"]["runs"]
    lines = [
        "# Live game state: replay of the reference fuser on real scorebug readings",
        "",
        f"Generated by `tools/specgen/live_state/harness.py` on {out['date']} (pack {out['pack_version']}). Numbers: `harness.json` in this folder.",
        "Aggregates only. Games are named B01..; no team names, no ids, no frames, no play-by-play rows.",
        "",
        "## What was run",
        "",
        f"- Truth: the kept 1 fps scorebug readings of {out['games']} private MSU broadcasts (the data of `measured_sensors.json`).",
        f"- Per game and seed ({out['seeds']} seeds) extra stretches of the bug were hidden on purpose: {pc(out['extra_hidden_share'])} of the visible seconds, "
        f"lengths drawn from the {out['hidden_lengths']['n']:,} real hidden stretches (median {out['hidden_lengths']['p50']} s, p90 {out['hidden_lengths']['p90']} s, p99 {out['hidden_lengths']['p99']} s).",
        f"- The fuser (`fuse.py`) saw only what stayed visible. Every hidden second was scored against the reading it was not shown: {a0['counts']['hidden_s']:,} hidden seconds over {runs} runs per configuration.",
        f"- {len(out['configs'])} configurations: 4 cue runs (no cue; stop cues at 0.8; stop, start and shot-reset cues at 0.8; all three at 1.0), 3 feed runs (score rows of made field goals arriving 0, 15, 45 s late), 3 runs with only the shot-clock slot hidden.",
        "- Cues are a stand-in for whistle audio and CV: the true stop and start instants of the clock, known to 1 s. An assumption sweep, not a measurement (OQ-LS-3).",
        "- The feed delay is not measured (OQ-LS-1): the three delays are a sweep. Free-throw rows are left out because their clock second does not place them in video time.",
        f"- Limits read from the YAML: {', '.join(f'{k} = {val}' for k, val in L.items())}.",
        "",
        "## Verdicts",
        "",
        table(["Check", "What it asks", "Result"], [
            ["ACC-LS-H1", f"game-clock seconds graded inferred are within {L['clock_tolerance_s']} s in at least {pc(L['clock_inferred_promise'])}, pooled and at every age", "pass" if v["ACC-LS-H1"]["pass"] else "FAIL"],
            ["ACC-LS-H2", "no null; no clock rise and no score fall without a log row; no observed grade without an observation", "pass" if v["ACC-LS-H2"]["pass"] else "FAIL"],
            ["ACC-LS-H3", "after a return the value equals the reading and is observed at the second reading; every miss beyond the tolerance has a log row", "pass" if v["ACC-LS-H3"]["pass"] else "FAIL"],
            ["ACC-LS-H4", "the spec rule is not worse than plain last-status at any age", "pass" if v["ACC-LS-H4"]["pass"] else "FAIL"],
            ["shot clock", "shot-clock seconds graded inferred meet the same promise", "pass" if v["shot_clock_inferred"]["pass"] else "FAIL"],
        ]),
        "",
        "## Game clock: share of hidden seconds within 1 s, by seconds since the last reading",
        "",
        table(["Age (s)", "n", "Spec rule, no cue", "Plain last status", "Plain hold", "Plain run", "Spec, stop cues 0.8", "Spec, all cues 0.8", "Spec, all cues 1.0"],
              [[b, f"{a0['clock_by_age'][b]['n']:,}", pc(a0["clock_by_age"][b]["spec"]), pc(a0["clock_by_age"][b]["last_status"]), pc(a0["clock_by_age"][b]["hold"]),
                pc(a0["clock_by_age"][b]["run"]), pc(s[stop]["clock_by_age"][b]["spec"]), pc(s[some]["clock_by_age"][b]["spec"]), pc(s[full]["clock_by_age"][b]["spec"])] for b in ages]),
        "",
        "With no cue the spec rule IS last-status reckoning; the two columns differ only where the fuser refused a single odd reading that the plain rule took.",
        "",
        "## Grade honesty of the game clock",
        "",
        table(["Run", "Inferred seconds", "Within 1 s", "At 1 s", "At 2 s", "At 3 s", "Worst game", "Median game", "Carried: within 1 s (no claim)"],
              [[n, f"{s[n]['clock_by_grade']['inferred']['n']:,}", pc(s[n]["clock_by_grade"]["inferred"]["within_tolerance"]),
                *[pc(s[n]["inferred_by_age"]["game_clock_s"].get(b, {}).get("within_tolerance")) for b in ("1", "2", "3")],
                pc(s[n]["inferred_clock_per_game"]["min"]), pc(s[n]["inferred_clock_per_game"]["median"]),
                pc(s[n]["clock_by_grade"]["carried"]["within_tolerance"])] for n in (none, stop, some, full)]),
        "",
        f"- The guaranteed interval [last reading - elapsed time, last reading] held the true clock in {100 * a0['clock_interval_holds_truth']:.2f} % of hidden seconds. The rest are clock steps the bug itself shows (corrections, cuts in the recording).",
        f"- The running flag graded inferred was right in {pc(a0['running_flag_inferred_right']['share'])} of hidden seconds with no cue and {pc(s[some]['running_flag_inferred_right']['share'])} with cues at 0.8 (no promise is set for the flag).",
        f"- Unknown is never a claim: {a0['clock_by_grade'].get('unknown', {}).get('n', 0):,} hidden seconds were graded unknown with no cue.",
        "",
        "## Returns of the bug",
        "",
        table(["Returns", "Second reading observed and equal", "Misses beyond the tolerance", "Misses without a log row", "Readings refused (single odd read)", "Clock fell faster than time (logged)"],
              [[f"{a0['returns']['n']:,}", f"{a0['returns']['second_reading_observed_and_equal']:,} of {a0['returns']['second_reading']:,}",
                f"{a0['returns']['miss_beyond_tolerance']:,}", a0["returns"]["miss_log_mismatch"], a0["counts"]["rejected_reads"],
                a0["log_rows"].get("latency_report", {}).get("game_clock_s", {}).get("clock_fell_faster_than_time", 0)]]),
        "",
        f"Upward clock steps that persisted for two readings (official corrections, R-IV-05): {a0['log_rows'].get('state_corrections', {}).get('game_clock_s', {}).get('official_clock_correction', 0)} in {runs} runs.",
        "",
        "## Score total (always carried when the bug is hidden and no CV watches the rim: no claim)",
        "",
        table(["Run", "Equal to the hidden bug reading", "Equal to the bug now or within the confirm window", "Catch-up after a changed stretch: n", "p50 (s)", "p90 (s)", "Flags: bug differs from scorebook"],
              [[n, pc(s[n]["by_grade"]["score_total"]["carried"]["equal"]), pc(s[n]["score_equal_to_bug_now_or_within_window"]["share"]),
                s[n]["score_catch_up_s"]["n"], s[n]["score_catch_up_s"]["p50"], s[n]["score_catch_up_s"]["p90"],
                s[n]["log_rows"].get("scoreboard_flags", {}).get("score_total", {}).get("bug_differs_from_scorebook", 0)] for n in (none, "feed_0s", "feed_15s", "feed_45s")]),
        "",
        table(["Age of the held score (s)"] + ages, [["Equal to the hidden reading, no feed"] + [pc(a0["by_age"]["score_total"].get(b, {}).get("equal")) for b in ages]]),
        "",
        "## Shot clock: share within 1 s, by seconds since its last reading",
        "",
        table(["Run"] + ages[:6], [[label] + [pc(s[n]["by_age"]["shot_clock_s"].get(b, {}).get("equal")) for b in ages[:6]] for label, n in
                                    (("Bug hidden, no cue", none), ("Bug hidden, all cues 0.8", some), ("Bug hidden, all cues 1.0", full),
                                     ("Slot hidden, no cue", "slot_0.0"), ("Slot hidden, reset cues 0.8", "slot_0.8"), ("Slot hidden, reset cues 1.0", "slot_1.0"))]),
        "",
        "## Other fields while the bug is hidden (no cue)",
        "",
        table(["Field", "Grade", "n", "Equal to the hidden reading"],
              [[f, g, f"{x['n']:,}", pc(x["equal"])] for f in ("period", "team_fouls_home", "team_fouls_away", "timeouts_left_home", "timeouts_left_away")
               for g, x in sorted(a0["by_grade"].get(f, {}).items())]),
        "",
        "Team fouls and timeouts are compared with the bug, which itself trails the foul (median 7 s, `measured_sensors.json`); home and away here are the left and right slot of the bug.",
        "",
        "## What the replay changed in the spec",
        "",
        "- Shot clock: graded inferred for 1 s after its last reading (was 3 s with the bug away and 5 s with only the slot unreadable). Beyond 1 s the promise is met in one run only (slot hidden, every visible reset delivered as a cue, at 2 s), so one limit of 1 s is used.",
        "- Cues: a cue re-anchors the estimate and restarts the carried limit, but no longer restarts the inferred limit of the clock value. Restarted at the cue, the claim fell below the promise.",
        "- The game-clock horizon of 3 s stands.",
        "",
        "## What this proves and what it cannot prove",
        "",
        "- Proves: on real readings the rules never claim more than they hold. Inferred clock values keep the promise in every game; carried and unknown values are marked as such; nothing is null; every correction and every miss leaves a log row.",
        "- Proves: the rule is no worse than the plain rules at any age, and cues would help from 3 s on.",
        "- Cannot prove: anything at finer than 1 s; the bug itself is the truth here, so a late or wrong bug is not seen.",
        "- Cannot prove: real whistle or CV cues (stand-ins), the real feed delay (swept), made-basket detection by CV (not in the replay), lineups, possession or any field that needs pixels.",
        "- Hidden stretches made on purpose sit at random moments. Real hidden stretches sit more often at dead balls (`measured_sensors.json`), where holding is easier.",
        "",
        "## Per game: inferred game-clock seconds within 1 s (no cue)",
        "",
        table(["Game", "Inferred seconds", "Within 1 s"], [[r["game"], r["inferred_clock_s"], pc(r["inferred_within_tolerance"])] for r in out["per_game"] if r["config"] == none]),
        "",
    ]
    README.write_text("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=0, help="first N games only (0 = all)")
    ap.add_argument("--seeds", type=int, default=0, help="0 = the seeds param of core.yaml")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--no-write", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    spec = fuse.Spec()
    P = spec.P
    games = mr.load_games()
    if not games:
        raise SystemExit("no private scorebug reads found under " + str(mr.STATE))
    codes = json.loads((mr.PRIV_OUT / "game_codes.json").read_text())
    if P["hidden_length_source"] != "measured":
        raise SystemExit("hidden_length_source must be 'measured'")
    lengths = [b[0] - a[0] - 1 for g in games for a, b in zip(g["align"]["samples"], g["align"]["samples"][1:])
               if a[1] == b[1] and b[0] - a[0] >= 2]
    todo = [(g["key"], codes[g["key"]]) for g in games][: a.games or None]
    del games
    seeds = a.seeds or P["seeds"]
    A, rows = Counter(), []
    with Pool(min(2, max(1, a.workers))) as pool:              # at most 2 worker processes (shared machine)
        data = pool.map(_prepare_worker, todo, chunksize=1)
        for part, r in pool.imap_unordered(run_game, [(d, seeds, lengths) for d in data], chunksize=1):
            A.update(part)
            rows.extend(r)
    tree = nest(A)
    summary = summarise(tree, rows, P)
    out = {
        "what": "Real-data replay of the reference fuser (tools/specgen/live_state/harness.py).",
        "date": time.strftime("%Y-%m-%d"),
        "pack_version": spec.core["version"],
        "games": len(todo), "seeds": seeds, "resolution_s": 1,
        "extra_hidden_share": P["extra_hidden_share"], "hidden_lengths": mr.dist(lengths),
        "configs": configs(P),
        "limits_used": {k: P[k] for k in ("clock_inferred_max_s", "clock_carried_max_s", "clock_tolerance_s", "clock_inferred_promise",
                                         "scorebug_down_after_s", "scorebug_up_after_reads", "shot_clock_carried_max_s",
                                         "shot_clock_inferred_max_s", "counter_stale_after_s", "pbp_to_bug_window_s")},
        "verdicts": verdicts(summary, P),
        "summary": summary,
        "per_game": sorted(rows, key=lambda r: (r["config"], r["game"])),
        "run_seconds": round(time.time() - t0, 1),
    }
    if not a.no_write:
        OUT.write_text(json.dumps(out, indent=1) + "\n")
        write_readme(out)
    v = out["verdicts"]
    print(json.dumps({k: x["pass"] for k, x in v.items()}))
    print(f"{len(todo)} games, {seeds} seeds, {len(configs(P))} configs, {out['run_seconds']} s")
    return out


if __name__ == "__main__":
    main()
