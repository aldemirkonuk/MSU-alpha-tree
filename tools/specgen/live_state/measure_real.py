"""Measured behaviour of the scorebug and play-by-play sensors on real MSU broadcasts (live-state baseline 4).

Reads, and never copies, private research data:
  ~/MSU-Alpha-3-private/work/review_tool/msu/state/<game>/{state.json, align.json, ocr.jsonl}
      1 frame per second of the scorebug band, read with OCR (built by the private review-tool pipeline)
  the CBBD play-by-play file each state.json points to (licensed, private)

Writes aggregates only (game codes B01.., no team names, no ids):
  results/live_state_test/measured_sensors.json
and the private code -> game mapping to ~/MSU-Alpha-3-private/work/live_state_2026-11-11/game_codes.json.

Usage: python tools/specgen/live_state/measure_real.py [--out results/live_state_test/measured_sensors.json]

Everything here has a time resolution of 1 s (one OCR frame per second) and the game clock shows whole
seconds above 1:00. Numbers are therefore reported in whole seconds; "within 1 s" is the resolution floor.
What is measured:
  M1 clock availability and the length of the stretches in which no clock could be read
  M2 what the game clock did during those stretches, and the error of three carry rules (hold, run, last status)
  M3 the same carry rules on withheld readings (stretches where the bug was visible, hidden on purpose)
  M4 clock running / stopped shares and the OCR reject rate
  M5 score-on-bug lag after a made field goal, referenced to the play-by-play clock second; how often the score
     changed while the bug could not be read
  M6 shot clock, team fouls, timeouts and bonus label: availability, and agreement / lag where it can be checked
  M7 play-by-play wallclock: backward steps and entry-time jitter between events on a running clock
"""
from __future__ import annotations

import argparse
import bisect
import datetime as dt
import json
import re
import statistics
import time
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PRIVATE = Path.home() / "MSU-Alpha-3-private"
STATE = PRIVATE / "work" / "review_tool" / "msu" / "state"
PRIV_OUT = PRIVATE / "work" / "live_state_2026-11-11"
OUT = REPO / "results" / "live_state_test" / "measured_sensors.json"

GAP_BUCKETS = [(1, 2), (3, 5), (6, 10), (11, 20), (21, 60), (61, 10 ** 6)]
WITHHELD_K = [2, 3, 5, 10, 20, 30, 60]
FG_TYPES = {"JumpShot", "LayUpShot", "DunkShot", "TipShot"}
SCORE_LAG_WINDOW_S = 15
FOUL_LAG_WINDOW_S = 45


def period_len(p):
    return 1200 if p <= 2 else 300


def gtime(p, rem):
    base = (p - 1) * 1200 if p <= 2 else 2400 + (p - 3) * 300
    return base + period_len(p) - rem


def q(xs, p):
    """Quantile by nearest rank on a sorted copy; None for an empty list."""
    if not xs:
        return None
    s = sorted(xs)
    return s[min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))]


def dist(xs, nd=2):
    xs = list(xs)
    if not xs:
        return {"n": 0}
    return {"n": len(xs), "mean": round(statistics.fmean(xs), nd), "p50": q(xs, 0.5), "p90": q(xs, 0.9),
            "p95": q(xs, 0.95), "p99": q(xs, 0.99), "max": max(xs)}


def share(n, d, nd=4):
    return round(n / d, nd) if d else None


def bucket(n):
    for lo, hi in GAP_BUCKETS:
        if lo <= n <= hi:
            return f"{lo}-{hi}" if hi < 10 ** 6 else f"{lo}+"
    return None


def bucket_names():
    return [f"{lo}-{hi}" if hi < 10 ** 6 else f"{lo}+" for lo, hi in GAP_BUCKETS]


# ------------------------------------------------------------------------------------------ loading
def load_games():
    games = []
    for d in sorted(STATE.iterdir()):
        st_p, al_p, ocr_p = d / "state.json", d / "align.json", d / "ocr.jsonl"
        if not (st_p.exists() and al_p.exists() and ocr_p.exists()):
            continue
        st = json.loads(st_p.read_text())
        plays_file = st.get("plays_file")
        if not plays_file or not Path(plays_file).exists():
            continue
        al = json.loads(al_p.read_text())
        if len(al.get("samples", [])) < 600:
            continue
        games.append({"key": d.name, "state": st, "align": al, "ocr": ocr_p, "plays": json.loads(Path(plays_file).read_text())})
    return games


# ------------------------------------------------------------------------------------------ clock
def clock_stats(S):
    """S = kept samples [t, period, rem, G, total] sorted by t. Returns per-game clock measures."""
    out = {"pairs": Counter(), "gaps": [], "intermission_gaps": 0}
    for a, b in zip(S, S[1:]):
        dT, dG = b[0] - a[0], b[3] - a[3]
        if a[1] != b[1]:
            out["intermission_gaps"] += 1
            continue
        if dT == 1:
            out["pairs"]["running" if 0.5 <= dG <= 1.5 else "stopped" if abs(dG) < 0.5 else "other"] += 1
        elif dT >= 2:
            out["gaps"].append((a[0], dT, dG))
    return out


def status_before(S, i):
    """Clock status just before sample i: running if the clock advanced over the last reading pair within 2 s."""
    if i == 0:
        return "unknown"
    a, b = S[i - 1], S[i]
    if a[1] != b[1] or b[0] - a[0] > 2:
        return "unknown"
    return "running" if b[3] - a[3] >= 0.5 else "stopped"


def carry_errors(dT, dG, status, rem_at_start):
    """Error in s of the game clock after a blind stretch of dT s in which the clock really advanced dG s."""
    run_pred = min(dT, rem_at_start)  # a running clock cannot pass 0
    e_hold = abs(dG)
    e_run = abs(run_pred - dG)
    e_last = e_run if status == "running" else e_hold
    return e_hold, e_run, e_last


def gap_measures(S):
    by_t = {s[0]: i for i, s in enumerate(S)}
    real = defaultdict(lambda: {"n": 0, "hidden_s": 0, "clock_stopped": 0, "clock_ran_all": 0, "clock_ran_part": 0,
                                "status_known": 0, "e_hold": [], "e_run": [], "e_last": [], "live_s_unseen": 0.0})
    for i in range(len(S) - 1):
        a, b = S[i], S[i + 1]
        dT, dG = b[0] - a[0], b[3] - a[3]
        if a[1] != b[1] or dT < 2:
            continue
        r = real[bucket(dT - 1)]
        st = status_before(S, i)
        eh, er, el = carry_errors(dT, dG, st, a[2])
        r["n"] += 1
        r["hidden_s"] += dT - 1
        r["live_s_unseen"] += max(0.0, dG - 1)
        r["clock_stopped"] += abs(dG) < 0.5
        r["clock_ran_all"] += dG >= dT - 1.5 and dG >= 0.5
        r["clock_ran_part"] += 0.5 <= dG < dT - 1.5
        if st != "unknown":
            r["status_known"] += 1
            r["e_last"].append(round(el, 1))
        r["e_hold"].append(round(eh, 1))
        r["e_run"].append(round(er, 1))
    withheld = {k: {"n": 0, "by_status": Counter(), "e_last": [], "e_last_running": [], "e_last_stopped": [],
                    "e_hold": [], "e_run": []} for k in WITHHELD_K}
    for i, a in enumerate(S):
        st = status_before(S, i)
        if st == "unknown":
            continue
        for k in WITHHELD_K:
            j = by_t.get(a[0] + k)
            if j is None or S[j][1] != a[1]:
                continue
            dG = S[j][3] - a[3]
            eh, er, el = carry_errors(k, dG, st, a[2])
            w = withheld[k]
            w["n"] += 1
            w["by_status"][st] += 1
            w["e_last"].append(round(el, 1))
            w["e_last_" + st].append(round(el, 1))
            w["e_hold"].append(round(eh, 1))
            w["e_run"].append(round(er, 1))
    return real, withheld


def score_change_measures(S):
    """Did the score total change while the bug could not be read? Real hidden runs (by length) and withheld windows."""
    real = defaultdict(lambda: [0, 0])  # bucket -> [runs with a total on both sides, runs where it changed]
    for a, b in zip(S, S[1:]):
        if a[1] != b[1] or b[0] - a[0] < 2 or a[4] is None or b[4] is None:
            continue
        r = real[bucket(b[0] - a[0] - 1)]
        r[0] += 1
        r[1] += a[4] != b[4]
    by_t = {s[0]: s for s in S}
    held = {k: [0, 0] for k in WITHHELD_K}
    for a in S:
        if a[4] is None:
            continue
        for k in WITHHELD_K:
            b = by_t.get(a[0] + k)
            if b is None or b[1] != a[1] or b[4] is None:
                continue
            held[k][0] += 1
            held[k][1] += a[4] != b[4]
    return real, held


# ------------------------------------------------------------------------------------------ plays
def sorted_plays(plays):
    ps = [p for p in plays if p.get("period") and p.get("secondsRemaining") is not None]
    for n, p in enumerate(ps):
        p["_n"] = n
        p["_G"] = gtime(p["period"], p["secondsRemaining"])
    return sorted(ps, key=lambda p: (p["_G"], (p.get("homeScore") or 0) + (p.get("awayScore") or 0), p["_n"]))


def exact_time(S, Gs, G, period):
    """Video second at which the bug clock first shows game time G, only when the bug was read continuously
    (previous reading <= 2 s earlier) and the clock was running into it. Else None."""
    i = bisect.bisect_left(Gs, G - 1e-6)
    if i <= 0 or i >= len(S):
        return None, None
    s, p = S[i], S[i - 1]
    if s[1] != period or p[1] != period or abs(s[3] - G) > 0.5 or s[0] - p[0] > 2 or s[3] - p[3] < 0.5:
        return None, None
    return s[0], i


def score_lag(S, plays):
    Gs = [s[3] for s in S]
    lags, unseen, tested = [], 0, 0
    for p in plays:
        if not p.get("scoringPlay") or p.get("playType") not in FG_TYPES or p.get("scoreValue") not in (2, 3):
            continue
        new_total = (p.get("homeScore") or 0) + (p.get("awayScore") or 0)
        t0, i = exact_time(S, Gs, p["_G"], p["period"])
        if t0 is None:
            continue
        before = [s[4] for s in S[max(0, i - 4):i + 1] if s[4] is not None]
        if not before or before[-1] not in (new_total - p["scoreValue"], new_total):
            continue  # the bug total just before the event is not the play-by-play total: unusable
        tested += 1
        first = next((s[0] for s in S[max(0, i - 4):] if s[0] <= t0 + SCORE_LAG_WINDOW_S and s[0] >= t0 - 4
                      and s[4] == new_total), None)
        if first is None:
            unseen += 1
        else:
            lags.append(first - t0)
    return lags, tested, unseen


def wallclock_measures(plays_raw, S):
    Gs = [s[3] for s in S]
    w = []
    for p in plays_raw:
        try:
            w.append(dt.datetime.fromisoformat(p["wallclock"].replace("Z", "+00:00")).timestamp())
        except (KeyError, AttributeError, ValueError, TypeError):
            w.append(None)
    steps = [(b - a) for a, b in zip(w, w[1:]) if a is not None and b is not None]
    back = [-s for s in steps if s < 0]
    seen_max, behind = None, []
    for x in w:
        if x is None:
            continue
        if seen_max is not None and x < seen_max:
            behind.append(seen_max - x)
        seen_max = x if seen_max is None else max(seen_max, x)
    # entry-time jitter: consecutive events located on one uninterrupted running-clock stretch
    loc = []
    for p, wx in zip(plays_raw, w):
        if wx is None or not p.get("period") or p.get("secondsRemaining") is None:
            continue
        G = gtime(p["period"], p["secondsRemaining"])
        t0, _ = exact_time(S, Gs, G, p["period"])
        if t0 is not None:
            loc.append((G, t0, wx))
    loc.sort()
    deltas = []
    for (G1, t1, w1), (G2, t2, w2) in zip(loc, loc[1:]):
        if 1 <= G2 - G1 <= 60 and abs((t2 - t1) - (G2 - G1)) <= 1.5:
            deltas.append((w2 - w1) - (t2 - t1))
    return {"rows": len(w), "rows_with_wallclock": sum(x is not None for x in w), "backward_steps": len(back),
            "backward_step_max_s": max(back) if back else 0, "rows_behind_running_max": len(behind),
            "behind_running_max_p50_s": q(behind, 0.5), "behind_running_max_max_s": max(behind) if behind else 0,
            "jitter_deltas": deltas}


# ------------------------------------------------------------------------------------------ bug tokens
WORD = re.compile(r"\S+")
FOULS_A = re.compile(r"F[O0]ULS?:?\s*(\d{1,2})\+?", re.I)      # "FOULS: 7"
FOULS_B = re.compile(r"(\d{1,2})\+?\s*F[O0]ULS?\b", re.I)        # "7 Fouls"
TOUTS = re.compile(r"TIME[O0D]UTS?:?\s*(\d)", re.I)
BONUS = re.compile(r"B[O0]NUS\s*(\+)?", re.I)


def parse_tokens(items, cal):
    """One OCR frame -> {fouls_l, fouls_r, to_l, to_r, bonus_l, bonus_r, shot}. Sides by x against the clock x."""
    y0, y1 = cal["band"]
    cx0, cy0 = cal["cx"], cal["cy"]
    o = {}
    for text, _conf, x, y, w, h in items:
        n = max(len(text), 1)

        def side(m):
            c = x + w * (m.start() + m.end()) / (2 * n)
            return "l" if c < cx0 else "r"
        for rx in (FOULS_A, FOULS_B):
            for m in rx.finditer(text):
                if int(m.group(1)) <= 30:
                    o.setdefault("fouls_" + side(m), int(m.group(1)))
        for m in TOUTS.finditer(text):
            o.setdefault("to_" + side(m), int(m.group(1)))
        for m in BONUS.finditer(text):
            o.setdefault("bonus_" + side(m), "double" if m.group(1) else "bonus")
        Y = y0 + (y + h / 2) * (y1 - y0)
        if abs(Y - cy0) < 0.03:  # clock row: the shot clock is the small integer just right of the clock
            for m in WORD.finditer(text):
                t = m.group().strip("•.,'\"|()[]")
                c = x + w * (m.start() + m.end()) / (2 * n)
                if re.fullmatch(r"\d{1,2}", t) and 0.025 < c - cx0 < 0.085 and int(t) <= 30:
                    o.setdefault("shot", int(t))
    return o


def token_measures(g, S, plays):
    cal = g["state"]["calib"]
    kept = {s[0]: s for s in S}
    tok = {}
    with open(g["ocr"]) as fh:
        for line in fh:
            r = json.loads(line)
            if r["t"] in kept:
                tok[r["t"]] = parse_tokens(r["o"], cal)
    n = len(kept)
    have = Counter()
    for t, o in tok.items():
        have["fouls_both"] += "fouls_l" in o and "fouls_r" in o
        have["timeouts_both"] += "to_l" in o and "to_r" in o
        have["shot_clock"] += "shot" in o
        have["bonus_any"] += "bonus_l" in o or "bonus_r" in o
    # shot clock: with both clocks running, it should drop 1 per second
    sc_pairs = sc_ok = 0
    ts = sorted(tok)
    for a, b in zip(ts, ts[1:]):
        if b - a == 1 and "shot" in tok[a] and "shot" in tok[b] and 0.5 <= kept[b][3] - kept[a][3] <= 1.5 \
                and kept[a][1] == kept[b][1]:
            sc_pairs += 1
            sc_ok += tok[a]["shot"] - tok[b]["shot"] in (0, 1, 2) or tok[b]["shot"] >= 19  # tick, or a reset
    # team fouls against play-by-play: which side is home?
    home = g["state"].get("home")
    fouls = [p for p in plays if p.get("playType") == "PersonalFoul" and p.get("team")]
    Gs = [s[3] for s in S]
    best = None
    for left_is_home in (False, True):
        agree = tested = 0
        lags, unseen = [], 0
        cnt = defaultdict(int)
        for p in fouls:
            half = 1 if p["period"] == 1 else 2
            is_home = p["team"] == home
            cnt[(half, is_home)] += 1
            new = cnt[(half, is_home)]
            key = "fouls_" + ("l" if is_home == left_is_home else "r")
            i = bisect.bisect_left(Gs, p["_G"] - 1e-6)
            if i >= len(S) or S[i][1] != p["period"] or abs(S[i][3] - p["_G"]) > 0.5 or new > 9:
                continue
            t0 = S[i][0]
            prev = [tok[s[0]].get(key) for s in S[max(0, i - 5):i] if s[0] in tok and tok[s[0]].get(key) is not None]
            if not prev or prev[-1] != new - 1:
                continue
            tested += 1
            first = next((s[0] for s in S[i:] if s[0] <= t0 + FOUL_LAG_WINDOW_S and s[0] in tok
                          and tok[s[0]].get(key) == new), None)
            if first is None:
                unseen += 1
            else:
                agree += 1
                lags.append(first - t0)
        cand = {"left_is_home": left_is_home, "tested": tested, "seen": agree, "unseen": unseen, "lags": lags}
        if best is None or cand["seen"] > best["seen"]:
            best = cand
    return {"kept": n, "have": dict(have), "shot_pairs": sc_pairs, "shot_pairs_consistent": sc_ok, "fouls": best,
            "fouls_layout_seen": have["fouls_both"] > 0.2 * n}


# ------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    games = load_games()
    if not games:
        raise SystemExit("no private scorebug reads found under " + str(STATE))
    codes = {g["key"]: f"B{n + 1:02d}" for n, g in enumerate(games)}
    PRIV_OUT.mkdir(parents=True, exist_ok=True)
    (PRIV_OUT / "game_codes.json").write_text(json.dumps(codes, indent=1))

    per_game = []
    A = {"pairs": Counter(), "real": defaultdict(lambda: defaultdict(list)), "real_n": defaultdict(Counter),
         "withheld": {k: defaultdict(list) for k in WITHHELD_K}, "withheld_n": {k: Counter() for k in WITHHELD_K},
         "score_lags": [], "score_tested": 0, "score_unseen": 0, "jitter": [], "foul_lags": [], "foul_tested": 0,
         "foul_unseen": 0, "hidden_runs": [], "wall": Counter(), "wall_behind_max": 0, "wall_back_max": 0,
         "tok": Counter(), "tok_games_with_fouls_layout": 0, "sc_real": defaultdict(lambda: [0, 0]),
         "sc_held": {k: [0, 0] for k in WITHHELD_K}}
    for g in games:
        S = g["align"]["samples"]
        plays = sorted_plays(g["plays"])
        cs = clock_stats(S)
        real, withheld = gap_measures(S)
        in_period_s = sum(b[0] - a[0] for a, b in zip(S, S[1:]) if a[1] == b[1])
        hidden = [dT - 1 for _, dT, _ in cs["gaps"]]
        live_unseen = sum(r["live_s_unseen"] for r in real.values())
        lags, tested, unseen = score_lag(S, plays)
        sc_real, sc_held = score_change_measures(S)
        for b, (n, c) in sc_real.items():
            A["sc_real"][b][0] += n
            A["sc_real"][b][1] += c
        for k, (n, c) in sc_held.items():
            A["sc_held"][k][0] += n
            A["sc_held"][k][1] += c
        wm = wallclock_measures(g["plays"], S)
        tm = token_measures(g, S, plays)
        n_total = sum(1 for s in S if s[4] is not None)
        al = g["align"]
        row = {
            "game": codes[g["key"]],
            "video_s": int(al["n_frames"]),
            "in_period_s": int(in_period_s),
            "clock_read_s": len(S),
            "clock_availability": share(len(S), in_period_s + 2),
            "ocr_parsed": al["n_parsed"], "ocr_kept": al["n_kept"],
            "ocr_reject_share": share(al["n_parsed"] - al["n_kept"], al["n_parsed"]),
            "hidden_runs": len(hidden), "hidden_s": int(sum(hidden)), "hidden_run_max_s": max(hidden) if hidden else 0,
            "game_clock_s_unseen": round(live_unseen, 1),
            "game_clock_share_unseen": share(live_unseen, 2400.0),
            "score_total_read_share": share(n_total, len(S)),
            "score_total_matches_pbp_share": (al.get("score_check") or {}).get("exact_share"),
            "fg_tested": tested, "fg_score_unseen_15s": unseen, "fg_score_lag_p50_s": q(lags, 0.5),
            "shot_clock_read_share": share(tm["have"].get("shot_clock", 0), tm["kept"]),
            "fouls_read_share": share(tm["have"].get("fouls_both", 0), tm["kept"]),
            "timeouts_read_share": share(tm["have"].get("timeouts_both", 0), tm["kept"]),
            "pbp_rows": wm["rows"], "pbp_wallclock_backward_steps": wm["backward_steps"],
            "pbp_wallclock_backward_max_s": round(wm["backward_step_max_s"], 1),
        }
        per_game.append(row)
        A["pairs"].update(cs["pairs"])
        A["hidden_runs"].extend(hidden)
        for b, r in real.items():
            for k in ("e_hold", "e_run", "e_last"):
                A["real"][b][k].extend(r[k])
            for k in ("n", "hidden_s", "clock_stopped", "clock_ran_all", "clock_ran_part", "status_known"):
                A["real_n"][b][k] += r[k]
            A["real_n"][b]["live_s_unseen"] += r["live_s_unseen"]
        for k in WITHHELD_K:
            for kk in ("e_last", "e_last_running", "e_last_stopped", "e_hold", "e_run"):
                A["withheld"][k][kk].extend(withheld[k][kk])
            A["withheld_n"][k].update(withheld[k]["by_status"])
        A["score_lags"].extend(lags)
        A["score_tested"] += tested
        A["score_unseen"] += unseen
        A["jitter"].extend(wm["jitter_deltas"])
        for k in ("rows", "rows_with_wallclock", "backward_steps", "rows_behind_running_max"):
            A["wall"][k] += wm[k]
        A["wall_behind_max"] = max(A["wall_behind_max"], wm["behind_running_max_max_s"])
        A["wall_back_max"] = max(A["wall_back_max"], wm["backward_step_max_s"])
        for k, v in tm["have"].items():
            A["tok"][k] += v
        A["tok"]["kept"] += tm["kept"]
        A["tok"]["shot_pairs"] += tm["shot_pairs"]
        A["tok"]["shot_pairs_consistent"] += tm["shot_pairs_consistent"]
        if tm["fouls_layout_seen"] and tm["fouls"]:
            A["tok_games_with_fouls_layout"] += 1
            A["foul_lags"].extend(tm["fouls"]["lags"])
            A["foul_tested"] += tm["fouls"]["tested"]
            A["foul_unseen"] += tm["fouls"]["unseen"]

    def within(xs, lim):
        return share(sum(1 for x in xs if x <= lim), len(xs))

    def err_block(xs):
        return {"n": len(xs), "within_1s": within(xs, 1.0), "within_2s": within(xs, 2.0), "p50": q(xs, 0.5),
                "p90": q(xs, 0.9), "p99": q(xs, 0.99), "max": max(xs) if xs else None}

    real_rows = []
    for b in bucket_names():
        n = A["real_n"][b]
        if not n["n"]:
            continue
        real_rows.append({"hidden_s_bucket": b, "runs": n["n"], "hidden_s": n["hidden_s"],
                          "clock_stopped_share": share(n["clock_stopped"], n["n"]),
                          "clock_ran_throughout_share": share(n["clock_ran_all"], n["n"]),
                          "clock_ran_part_share": share(n["clock_ran_part"], n["n"]),
                          "game_clock_s_unseen": round(n["live_s_unseen"], 1),
                          "hold": err_block(A["real"][b]["e_hold"]), "run": err_block(A["real"][b]["e_run"]),
                          "last_status": err_block(A["real"][b]["e_last"])})
    withheld_rows = []
    for k in WITHHELD_K:
        w = A["withheld"][k]
        withheld_rows.append({"withheld_s": k, "n": len(w["e_last"]), "status_before": dict(A["withheld_n"][k]),
                              "last_status": err_block(w["e_last"]), "last_status_when_running": err_block(w["e_last_running"]),
                              "last_status_when_stopped": err_block(w["e_last_stopped"]),
                              "hold": err_block(w["e_hold"]), "run": err_block(w["e_run"])})
    hr = A["hidden_runs"]
    hist = Counter(bucket(h) for h in hr)
    jit = A["jitter"]
    mad = statistics.median(abs(x - statistics.median(jit)) for x in jit) if jit else None
    lag_hist = Counter(int(x) for x in A["score_lags"])
    pairs = A["pairs"]
    n_pairs = sum(pairs.values())
    tok = A["tok"]
    g_n = len(per_game)
    summary = {
        "games": g_n,
        "video_hours": round(sum(r["video_s"] for r in per_game) / 3600, 1),
        "clock": {
            "availability_in_period": {"min": min(r["clock_availability"] for r in per_game),
                                       "median": q([r["clock_availability"] for r in per_game], 0.5),
                                       "max": max(r["clock_availability"] for r in per_game),
                                       "pooled": share(sum(r["clock_read_s"] for r in per_game),
                                                       sum(r["in_period_s"] for r in per_game))},
            "ocr_reject_share_pooled": share(sum(r["ocr_parsed"] - r["ocr_kept"] for r in per_game),
                                             sum(r["ocr_parsed"] for r in per_game)),
            "consecutive_second_pairs": {"n": n_pairs, "running": share(pairs["running"], n_pairs),
                                         "stopped": share(pairs["stopped"], n_pairs), "other": share(pairs["other"], n_pairs)},
            "hidden_runs": {"per_game_median": q([r["hidden_runs"] for r in per_game], 0.5), **dist(hr, 1),
                            "count_by_length_s": {k: hist.get(k, 0) for k in bucket_names()}},
            "game_clock_share_unseen": {"median": q([r["game_clock_share_unseen"] for r in per_game], 0.5),
                                        "max": max(r["game_clock_share_unseen"] for r in per_game)},
        },
        "clock_carry_on_real_hidden_runs": real_rows,
        "clock_carry_on_withheld_readings": withheld_rows,
        "score": {
            "total_read_share": {"median": q([r["score_total_read_share"] for r in per_game], 0.5),
                                 "min": min(r["score_total_read_share"] for r in per_game)},
            "total_matches_pbp_share": {"median": q([r["score_total_matches_pbp_share"] for r in per_game
                                                     if r["score_total_matches_pbp_share"] is not None], 0.5),
                                        "min": min(r["score_total_matches_pbp_share"] for r in per_game
                                                   if r["score_total_matches_pbp_share"] is not None)},
            "changed_during_real_hidden_run": [{"hidden_s_bucket": b, "runs": A["sc_real"][b][0],
                                                "changed_share": share(A["sc_real"][b][1], A["sc_real"][b][0])}
                                               for b in bucket_names() if A["sc_real"][b][0]],
            "changed_within_withheld_window": [{"withheld_s": k, "n": A["sc_held"][k][0],
                                                "changed_share": share(A["sc_held"][k][1], A["sc_held"][k][0])}
                                               for k in WITHHELD_K],
            "made_fg_lag_vs_pbp_clock_s": {"tested": A["score_tested"], "not_seen_within_15_s": A["score_unseen"],
                                           **dist(A["score_lags"], 2),
                                           "share_within_s": {str(k): within(A["score_lags"], k) for k in (2, 4, 6, 8, 10)},
                                           "histogram": {str(k): lag_hist[k] for k in sorted(lag_hist)}},
        },
        "bug_fields": {
            "seconds_with_clock": tok["kept"],
            "shot_clock_read_share": share(tok["shot_clock"], tok["kept"]),
            "shot_clock_tick_consistent_share": share(tok["shot_pairs_consistent"], tok["shot_pairs"]),
            "team_fouls_read_share": share(tok["fouls_both"], tok["kept"]),
            "timeouts_read_share": share(tok["timeouts_both"], tok["kept"]),
            "bonus_label_seen_share": share(tok["bonus_any"], tok["kept"]),
            "games_with_text_foul_counts": A["tok_games_with_fouls_layout"],
            "team_foul_lag_vs_pbp_clock_s": {"tested": A["foul_tested"], "not_seen_within_45_s": A["foul_unseen"],
                                             **dist(A["foul_lags"], 2),
                                             "share_within_s": {str(k): within(A["foul_lags"], k) for k in (5, 10, 20, 30)}},
        },
        "pbp_wallclock": {
            "rows": A["wall"]["rows"], "rows_with_wallclock": A["wall"]["rows_with_wallclock"],
            "backward_steps": A["wall"]["backward_steps"],
            "backward_step_share": share(A["wall"]["backward_steps"], A["wall"]["rows_with_wallclock"]),
            "backward_step_max_s": round(A["wall_back_max"], 1),
            "rows_behind_running_max": A["wall"]["rows_behind_running_max"],
            "behind_running_max_max_s": round(A["wall_behind_max"], 1),
            "entry_jitter": {"pairs": len(jit), "delta_p05_s": q(jit, 0.05), "delta_p50_s": q(jit, 0.5),
                             "delta_p95_s": q(jit, 0.95),
                             "robust_sigma_single_entry_s": round(1.4826 * mad / 2 ** 0.5, 2) if mad is not None else None},
        },
    }
    out = {
        "what": "Measured scorebug and play-by-play sensor behaviour on MSU broadcast recordings (live-state baseline 4)",
        "date": time.strftime("%Y-%m-%d"),
        "resolution_s": 1,
        "notes": [
            "One OCR frame per second of the scorebug band; the game clock shows whole seconds above 1:00.",
            "Recordings are B1G+ replays with breaks shortened; video time is not wall-clock time.",
            "Lags are referenced to the second the play-by-play gives for the event, so they include the scorer's clock error.",
            "Private inputs; this file holds aggregates and game codes only.",
        ],
        "summary": summary,
        "per_game": per_game,
    }
    outp = Path(a.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=1))
    print("wrote", outp, "games", g_n)


if __name__ == "__main__":
    main()
