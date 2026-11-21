"""Synthetic tests of the scorebug measurement code (tools/specgen/live_state/measure_real.py). No private data."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "live_state"))

import measure_real as mr  # noqa: E402


def running(t0, t1, rem0, period=1, total=10):
    """One reading per second while the clock runs: [t, period, rem, G, total]."""
    return [[t, period, rem0 - (t - t0), mr.gtime(period, rem0 - (t - t0)), total] for t in range(t0, t1 + 1)]


def stopped(t0, t1, rem, period=1, total=10):
    return [[t, period, rem, mr.gtime(period, rem), total] for t in range(t0, t1 + 1)]


def test_gtime_halves_and_overtime():
    assert mr.gtime(1, 1200) == 0 and mr.gtime(1, 0) == 1200
    assert mr.gtime(2, 1200) == 1200 and mr.gtime(2, 0) == 2400
    assert mr.gtime(3, 300) == 2400 and mr.gtime(3, 0) == 2700


def test_pairs_classify_running_and_stopped():
    S = running(0, 10, 1000) + stopped(11, 20, 990)
    cs = mr.clock_stats(S)
    assert cs["pairs"]["running"] == 10 and cs["pairs"]["stopped"] == 10 and cs["pairs"]["other"] == 0


def test_carry_errors_for_the_three_rules():
    # 10 s blind; the clock really ran 4 s then stopped
    e_hold, e_run, e_last_running = mr.carry_errors(10, 4, "running", 500)
    assert (e_hold, e_run, e_last_running) == (4, 6, 6)
    assert mr.carry_errors(10, 4, "stopped", 500)[2] == 4
    # a running clock cannot pass 0: 10 s blind with 3 s left, clock ran 3 s
    assert mr.carry_errors(10, 3, "running", 3)[1] == 0


def test_real_gap_is_measured_with_the_status_before_it():
    # running 0..10, bug hidden 11..15, back at 16 having run throughout
    S = running(0, 10, 1000) + running(16, 20, 984)
    real, _ = mr.gap_measures(S)
    b = real["3-5"]
    assert b["n"] == 1 and b["hidden_s"] == 5 and b["clock_ran_all"] == 1
    assert b["e_last"] == [0.0] and b["e_hold"] == [6.0] and b["e_run"] == [0.0]
    # same gap but the clock was stopped throughout
    S = stopped(0, 10, 1000) + stopped(16, 20, 1000)
    real, _ = mr.gap_measures(S)
    assert real["3-5"]["clock_stopped"] == 1 and real["3-5"]["e_last"] == [0.0] and real["3-5"]["e_run"] == [6.0]


def test_withheld_windows_on_a_running_then_stopped_clock():
    S = running(0, 30, 1000) + stopped(31, 60, 970)
    _, held = mr.gap_measures(S)
    k = held[5]
    # windows that start while running and end before the stop are exact; those that straddle the stop err
    assert k["n"] > 0 and min(k["e_last"]) == 0.0 and max(k["e_last"]) > 0.0
    assert k["by_status"]["running"] > 0 and k["by_status"]["stopped"] > 0


def test_score_lag_is_referenced_to_the_play_clock_second():
    # made 2 at 16:40 remaining (1000 s), first shown on the bug at t = 10; the new total appears at t = 14: lag 4 s
    S = running(0, 10, 1010, total=10) + running(11, 13, 999, total=10) + running(14, 30, 996, total=12)
    plays = mr.sorted_plays([{"period": 1, "secondsRemaining": 1000, "scoringPlay": True, "playType": "JumpShot",
                              "scoreValue": 2, "homeScore": 12, "awayScore": 0}])
    lags, tested, unseen = mr.score_lag(S, plays)
    assert tested == 1 and unseen == 0 and lags == [4]


def test_score_change_while_hidden_is_counted():
    S = running(0, 10, 1000, total=10) + running(16, 20, 984, total=12)
    real, held = mr.score_change_measures(S)
    assert real["3-5"] == [1, 1]
    assert held[2][1] == 0


def test_bug_tokens_are_parsed_by_side():
    cal = {"band": [0.79, 0.98], "cx": 0.48, "cy": 0.88}
    items = [["TIMEOUTS: 4 FOULS: 5", 1.0, 0.16, 0.85, 0.09, 0.14], ["4:20", 1.0, 0.45, 0.41, 0.06, 0.2],
             ["23", 1.0, 0.52, 0.41, 0.02, 0.2], ["BONUS", 1.0, 0.59, 0.87, 0.05, 0.1],
             ["TIMEOUTS: 3 FOULS: 6", 1.0, 0.68, 0.85, 0.15, 0.13]]
    o = mr.parse_tokens(items, cal)
    assert o["fouls_l"] == 5 and o["fouls_r"] == 6 and o["to_l"] == 4 and o["to_r"] == 3 and o["bonus_r"] == "bonus"


def test_quantile_and_bucket_helpers():
    assert mr.q([1, 2, 3, 4, 5], 0.5) == 3 and mr.q([], 0.5) is None
    assert mr.bucket(1) == "1-2" and mr.bucket(7) == "6-10" and mr.bucket(500) == "61+"
