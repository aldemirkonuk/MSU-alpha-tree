"""Synthetic rule tests of the live-state pack: hand-built timelines that assert each rule of the spec on the reference
fuser (tools/specgen/live_state/fuse.py). Every limit is read from the YAML, never typed here."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "specgen" / "live_state"))
import fuse  # noqa: E402
import lslib  # noqa: E402

SPEC = fuse.Spec()
P = SPEC.P
RANK = SPEC.rank
INF, CAR = int(P["clock_inferred_max_s"]), int(P["clock_carried_max_s"])


def bug(f, t, clock_s, period=1, **kw):
    f.feed_msg({"t": t, "kind": "bug", "period": period, "clock_s": clock_s, **kw})


def running(f, t0, t1, start=600, **kw):
    """The bug is read every second from t0 to t1 with the clock running down from `start`."""
    for t in range(t0, t1 + 1):
        bug(f, t, start - (t - t0), **kw)


def stopped(f, t0, t1, clock_s=600, **kw):
    for t in range(t0, t1 + 1):
        bug(f, t, clock_s, **kw)


def at(f, t, field="game_clock_s"):
    f.advance(t)
    return f.snapshot()[field]


def rows(f, log, field=None, kind=None):
    return [r for r in f.log if r["log"] == log and (field is None or r["field"] == field) and (kind is None or r["kind"] == kind)]


def no_nulls(f):
    return all(v["value"] is not None and v["grade"] in RANK for v in f.snapshot().values())


# ------------------------------------------------------------------------------------------------ the game clock
def test_bug_hidden_during_a_running_clock_walks_inferred_carried_unknown_at_the_yaml_limits():
    f = fuse.Fuser(SPEC)
    running(f, 0, 9)                                  # last reading at t = 9: 591
    assert at(f, 9)["grade"] == "observed"
    for age in range(1, CAR + 5):
        s = at(f, 9 + age)
        want = "inferred" if age <= INF else "carried" if age <= CAR else "unknown"
        assert s["grade"] == want, (age, s)
        assert s["age_s"] == age
        assert (s["lo"], s["hi"]) == (591 - age, 591)             # the guaranteed interval
        if want == "unknown":
            assert s["value"] == "unknown"                          # explicit, never null
        else:
            assert s["value"] == 591 - age                          # dead-reckoned at 1.0 s per second
        assert no_nulls(f)


def test_bug_hidden_during_a_stopped_clock_holds_the_value_and_walks_the_same_grades():
    f = fuse.Fuser(SPEC)
    stopped(f, 0, 9, clock_s=432)
    for age in range(1, CAR + 1):
        s = at(f, 9 + age)
        assert s["value"] == 432 and s["grade"] == ("inferred" if age <= INF else "carried")
        assert s["lo"] == 432 - age and s["hi"] == 432              # the clock may have started unseen
    assert at(f, 9 + CAR + 1)["value"] == "unknown"


def test_a_clock_whose_flag_was_never_read_is_carried_at_once_never_inferred():
    f = fuse.Fuser(SPEC)
    bug(f, 0, 600)                                                   # one reading: running or stopped is not known
    s = at(f, 1)
    assert s["grade"] == "carried" and s["value"] == 600
    assert at(f, 1, "game_clock_running")["value"] == "unknown"


def test_the_first_reading_after_a_gap_is_inferred_and_the_second_makes_it_observed_and_a_miss_is_logged():
    f = fuse.Fuser(SPEC)
    running(f, 0, 9)                                                 # 591 at t = 9, running
    f.advance(15)                                                    # held estimate at t = 15: 585
    bug(f, 15, 589)                                                  # the clock had stopped: a miss of 4 s
    s = f.snapshot()["game_clock_s"]
    assert s["value"] == 589 and s["grade"] == "inferred"
    miss = rows(f, "latency_report", "game_clock_s", "snap_miss")
    assert len(miss) == 1 and miss[0]["held"] == 585 and miss[0]["seen"] == 589 and miss[0]["known_at"] == 15
    bug(f, 16, 589)
    assert f.snapshot()["game_clock_s"]["grade"] == "observed"
    assert f.snapshot()["game_clock_running"] == {"value": "stopped", "grade": "observed", "age_s": 0, "known_at": 16}


def test_a_return_inside_the_tolerance_is_not_logged():
    f = fuse.Fuser(SPEC)
    running(f, 0, 9)
    bug(f, 12, 588)                                                  # exactly what dead reckoning said
    assert rows(f, "latency_report", "game_clock_s") == []


def test_a_dead_reckoned_clock_never_goes_below_zero_and_ends_unknown_not_in_a_new_period():
    f = fuse.Fuser(SPEC)
    running(f, 0, 5, start=7)                                        # 2 s left at t = 5
    assert at(f, 6)["value"] == 1 and at(f, 6)["grade"] == "inferred"
    s = at(f, 7)
    assert s["value"] == "unknown" and s["lo"] == 0                  # period end reached while hidden (MAX_DWELL)
    assert at(f, 7, "game_clock_running")["value"] == "unknown"     # the clock cannot run past 0
    assert at(f, 7, "period")["value"] == 1 and at(f, 7, "period")["grade"] == "carried"


def test_period_stays_inferred_while_the_clock_interval_says_it_cannot_have_ended():
    f = fuse.Fuser(SPEC)
    running(f, 0, 9)
    assert at(f, 9 + CAR + 20, "period") == {"value": 1, "grade": "inferred", "age_s": CAR + 20, "known_at": 0}


def test_official_clock_correction_upward_is_logged_not_an_error():
    """R-IV-05: one higher read is a misread; an upward step that persists is an official correction."""
    need = P["clock_upward_confirm_reads"]
    f = fuse.Fuser(SPEC)
    stopped(f, 0, 5, clock_s=246)
    bug(f, 6, 250)                                                   # one odd read
    assert f.snapshot()["game_clock_s"]["value"] == 246 and f.counts["rejected_reads"] == 1
    bug(f, 7, 246)
    assert rows(f, "state_corrections") == []                        # it did not persist: no correction
    for i in range(need):
        bug(f, 8 + i, 250)
    assert f.snapshot()["game_clock_s"]["value"] == 250
    cor = rows(f, "state_corrections", "game_clock_s", "official_clock_correction")
    assert len(cor) == 1 and cor[0]["old"] == 246 and cor[0]["new"] == 250 and cor[0]["known_at"] == 8 + need - 1
    assert rows(f, "scoreboard_flags") == []                         # logged, not flagged as an error


def test_a_stop_cue_re_anchors_the_estimate_but_never_lengthens_the_claim():
    f = fuse.Fuser(SPEC, audio=True)
    running(f, 0, 9)                                                 # 591 at t = 9
    f.feed_msg({"t": 11, "kind": "cue", "what": "stop"})            # whistle 2 s into the gap: clock stopped at 589
    assert at(f, 11, "game_clock_running") == {"value": "stopped", "grade": "inferred", "age_s": 0, "known_at": 11}
    assert at(f, 12)["value"] == 589 and at(f, 12)["grade"] == "inferred"
    s = at(f, 9 + INF + 1)
    assert s["value"] == 589 and s["grade"] == "carried"             # the inferred limit counts from the READING
    assert at(f, 11 + CAR)["grade"] == "carried"                     # the carried limit counts from the cue
    assert at(f, 11 + CAR + 1)["grade"] == "unknown"
    f2 = fuse.Fuser(SPEC, audio=True)
    running(f2, 0, 9)
    f2.advance(9 + INF + 2)                                          # already carried
    f2.feed_msg({"t": 9 + INF + 2, "kind": "cue", "what": "stop"})
    assert at(f2, 9 + INF + 3)["grade"] == "carried"                 # a cue never moves a value's grade up


def test_a_start_cue_makes_a_stopped_clock_run_from_the_cue():
    f = fuse.Fuser(SPEC)
    stopped(f, 0, 9, clock_s=300)
    f.feed_msg({"t": 11, "kind": "cue", "what": "start"})
    assert at(f, 13)["value"] == 298


# ------------------------------------------------------------------------------------------------- replay, break
def test_replay_freezes_the_state_and_a_replayed_score_change_is_ignored():
    f = fuse.Fuser(SPEC, main_camera=True)
    running(f, 0, 9, score_home=10, score_away=8)
    f.feed_msg({"t": 10, "kind": "meta", "what": "replay", "on": True})
    assert f.level() == "D3_replay"
    for t in range(10, 20):                                          # the replay shows an older clock and a made basket
        bug(f, t, 640 - t, score_home=12, score_away=8)
    f.feed_msg({"t": 19.5, "kind": "cv_make", "field": "score_home", "points": 2})
    s = at(f, 20, "score_home")
    assert s["value"] == 10 and s["grade"] == "carried"              # state record principle 7
    c = at(f, 20)
    assert c["value"] == 590 and c["grade"] == "carried" and c["hi"] == 591
    assert f.raw_ignored == 11 and len(rows(f, "latency_report", kind="ignored_in_freeze")) == 11   # stored raw, never used
    f.feed_msg({"t": 21, "kind": "meta", "what": "replay", "on": False})
    assert at(f, 22)["grade"] == "carried"                           # no grade moves up without a new observation
    bug(f, 23, 585, score_home=10, score_away=8)
    bug(f, 24, 584, score_home=10, score_away=8)
    assert at(f, 24)["grade"] == "observed" and at(f, 24, "score_home")["grade"] == "observed"


def test_a_cv_make_just_before_a_replay_is_dropped_by_the_replay_guard():
    guard = P["replay_guard_s"]
    f = fuse.Fuser(SPEC, main_camera=True)
    running(f, 0, 9, score_home=10)
    f.feed_msg({"t": 9.5, "kind": "cv_make", "field": "score_home", "points": 3})
    f.feed_msg({"t": 9.5 + guard / 2, "kind": "meta", "what": "replay", "on": True})   # the detector objects in time
    assert at(f, 9.5 + 3 * guard, "score_home")["value"] == 10
    g = fuse.Fuser(SPEC, main_camera=True)
    running(g, 0, 9, score_home=10)
    g.feed_msg({"t": 9.5, "kind": "cv_make", "field": "score_home", "points": 3})
    assert at(g, 9.5 + guard / 2, "score_home")["value"] == 10       # held back for the guard
    assert at(g, 9.5 + guard, "score_home") == {"value": 13, "grade": "inferred", "age_s": 9.5 + guard - 9, "known_at": 9.5 + guard}


def test_break_freezes_and_the_return_re_acquires_everything_and_a_changed_count_is_a_correction():
    f = fuse.Fuser(SPEC)
    stopped(f, 0, 9, clock_s=723, score_home=20, score_away=18, timeouts_left_home=3)
    f.feed_msg({"t": 10, "kind": "meta", "what": "break", "on": True})
    assert f.level() == "D4_break"
    s = {k: at(f, 100, k) for k in ("game_clock_s", "score_home", "period", "timeouts_left_home")}
    assert all(v["grade"] == "carried" for v in s.values())          # frozen at the last pre-break value, at any age
    assert s["game_clock_s"]["value"] == 723 and s["score_home"]["value"] == 20
    f.feed_msg({"t": 130, "kind": "meta", "what": "break", "on": False})
    assert rows(f, "latency_report", "degradation_level", "reacquire")
    assert at(f, 131)["grade"] == "carried"                          # not trusted until read again
    assert at(f, 131, "shot_clock_s")["grade"] in ("carried", "unknown")
    for t in (132, 133):
        bug(f, t, 723, score_home=20, score_away=18, timeouts_left_home=2)
    assert at(f, 133)["grade"] == "observed"
    assert at(f, 133, "timeouts_left_home")["value"] == 2
    assert rows(f, "state_corrections", "timeouts_left_home", "correction_seen_on_return")   # changed over a break
    assert rows(f, "state_corrections", "score_home") == []


def test_degradation_level_is_first_match_and_a_lost_stream_is_d5():
    f = fuse.Fuser(SPEC, main_camera=True)
    running(f, 0, 5)
    assert f.level() == "D0_full"
    f.advance(6 + P["scorebug_down_after_s"])
    assert f.level() == "D1_bug_away"
    f.feed_msg({"t": 8, "kind": "meta", "what": "main_camera", "on": False})
    assert f.level() == "D2_off_main"
    f.feed_msg({"t": 9, "kind": "meta", "what": "replay", "on": True})
    f.feed_msg({"t": 9, "kind": "meta", "what": "break", "on": True})
    assert f.level() == "D4_break"                                   # the worse level wins
    f.advance(9 + P["stream_lost_after_s"] + 1, frame=False)         # no frame arrived
    assert f.level() == "D5_no_video"
    assert set(lslib.load_core()["degradation_levels"]) >= {"D0_full", "D1_bug_away", "D2_off_main", "D3_replay", "D4_break", "D5_no_video"}


# --------------------------------------------------------------------------------------------------------- score
def test_score_with_nothing_watching_the_rim_is_carried_from_the_first_missed_second_and_marked_stale():
    f = fuse.Fuser(SPEC)
    running(f, 0, 9, score_home=10, score_away=8)
    assert at(f, 9, "score_home")["grade"] == "observed"
    assert at(f, 9 + P["scorebug_down_after_s"], "score_home")["grade"] == "carried"
    stale = int(P["counter_stale_after_s"])
    f.advance(9 + stale)
    assert not f.stale("score_home")
    f.advance(9 + stale + 1)
    assert f.stale("score_home") and f.snapshot()["score_home"]["grade"] == "carried"   # stale, still carried, never guessed


def test_score_with_cv_watching_the_rim_keeps_its_grade_while_the_bug_is_hidden():
    f = fuse.Fuser(SPEC, main_camera=True)
    running(f, 0, 9, score_home=10)
    assert at(f, 30, "score_home") == {"value": 10, "grade": "observed", "age_s": 21, "known_at": 1}


def test_a_new_score_needs_two_agreeing_bug_readings():
    need = P["scorebug_up_after_reads"]
    f = fuse.Fuser(SPEC)
    running(f, 0, 9, score_home=10)
    bug(f, 10, 590, score_home=12)
    assert f.snapshot()["score_home"]["value"] == 10                 # one read: animation or misread
    for i in range(1, need):
        bug(f, 10 + i, 590 - i, score_home=12)
    s = f.snapshot()["score_home"]
    assert s["value"] == 12 and s["grade"] == "observed"
    tr = f.as_of_known("score_home", 10 + need - 1)
    assert tr["value"] == 12 and tr["event_t"] == pytest.approx(10 - P["make_to_bug_p50_s"])   # the make came before the digits


def test_cv_make_then_bug_inside_the_window_is_confirmed():
    f = fuse.Fuser(SPEC, main_camera=True)
    running(f, 0, 9, score_home=10)
    f.feed_msg({"t": 10, "kind": "cv_make", "field": "score_home", "points": 2})
    for t in (10, 11):
        bug(f, t, 600 - t, score_home=10)                            # the bug has not caught up yet
    s = at(f, 11, "score_home")
    assert s["value"] == 12 and s["grade"] == "inferred"             # provisional: CV only
    assert s["known_at"] == 10 + P["replay_guard_s"]
    bug(f, 12, 588, score_home=12)                                   # inside make_confirm_window_s
    assert 12 - 10 < P["make_confirm_window_s"]
    assert f.snapshot()["score_home"] == {"value": 12, "grade": "confirmed", "age_s": 0.0, "known_at": 10 + P["replay_guard_s"]}
    lag = rows(f, "latency_report", "score_home", "confirmed_by_bug")
    assert len(lag) == 1 and lag[0]["lag_s"] == 2 and rows(f, "scoreboard_flags") == []


def test_cv_make_not_confirmed_inside_the_window_raises_a_flag_and_stays_provisional():
    w = P["make_confirm_window_s"]
    f = fuse.Fuser(SPEC, main_camera=True)
    running(f, 0, 9, score_home=10)
    f.feed_msg({"t": 10, "kind": "cv_make", "field": "score_home", "points": 2})
    s = at(f, 10 + w + 1, "score_home")                              # bug hidden: nothing confirms it
    assert s["value"] == 12 and s["grade"] == "inferred"             # never silently confirmed
    flags = rows(f, "scoreboard_flags", "score_home", "make_not_confirmed_in_window")
    assert len(flags) == 1 and flags[0]["known_at"] > 10 + w
    assert len(rows(f, "scoreboard_flags")) == 1 and at(f, 60, "score_home")["grade"] == "inferred"   # flagged once
    # the bug comes back and never shows the make: the board wins the value, CV keeps an unmatched event
    for t in (61, 62):
        bug(f, t, 560, score_home=10)
    assert f.snapshot()["score_home"]["value"] == 10
    assert rows(f, "scoreboard_flags", "score_home", "cv_make_differs_from_board")
    assert rows(f, "cv_events_unmatched", "score_home", "make_not_on_board")


def test_late_play_by_play_row_corrects_a_provisional_value_as_a_new_version_and_the_old_one_stays_readable():
    f = fuse.Fuser(SPEC, main_camera=True, feed=True)
    running(f, 0, 9, score_home=10)
    f.feed_msg({"t": 10, "kind": "cv_make", "field": "score_home", "points": 3})     # CV saw a three
    known = 10 + P["replay_guard_s"]
    assert at(f, 20, "score_home")["value"] == 13 and f.version == 1
    f.feed_msg({"t": 40, "kind": "pbp", "field": "score_home", "value": 12, "period": 1, "clock_s": 590})   # the scorebook: a two
    s = f.snapshot()["score_home"]
    assert s["value"] == 12 and s["grade"] == "observed" and s["known_at"] == 40
    assert f.version == 2
    assert f.as_of_known("score_home", 30)["value"] == 13            # what the system knew at t = 30 never changes
    assert f.as_of_known("score_home", 40)["value"] == 12
    assert f.as_of_event("score_home", 12, version=1)["value"] == 13 # version 1 stays readable
    new = f.as_of_event("score_home", 12)                            # version 2: what was true, known late
    assert new["value"] == 12 and new["known_at"] == 40 and new["supersedes"] == f.as_of_known("score_home", 30)["id"]
    assert f.as_of_known("score_home", 30)["known_at"] == known
    assert rows(f, "cv_events_unmatched", "score_home", "cv_value_overruled_by_scorebook")


def test_a_late_row_that_only_confirms_opens_no_new_version():
    f = fuse.Fuser(SPEC, feed=True)
    running(f, 0, 30, score_home=10)
    f.feed_msg({"t": 30, "kind": "pbp", "field": "score_home", "value": 10, "period": 1, "clock_s": 595})
    assert f.version == 1 and f.snapshot()["score_home"]["grade"] == "confirmed"
    lag = rows(f, "latency_report", "score_home", "confirmed_by_feed")
    assert lag and lag[0]["lag_s"] == 25                              # the bug clock showed 595 at t = 5


def test_conflicting_score_between_bug_and_play_by_play_follows_authority_and_writes_a_flag():
    w = P["pbp_to_bug_window_s"]
    f = fuse.Fuser(SPEC, feed=True)
    running(f, 0, 60, score_home=44)
    f.feed_msg({"t": 60, "kind": "pbp", "field": "score_home", "value": 45, "period": 1, "clock_s": 590})
    assert 60 - 10 > w                                               # the row's clock second was shown at t = 10: window closed
    s = f.snapshot()["score_home"]
    assert s["value"] == 45 and s["grade"] == "observed"             # official scorebook > broadcast scorebug
    flag = rows(f, "scoreboard_flags", "score_home", "bug_differs_from_scorebook")
    assert len(flag) == 1 and flag[0]["bug"] == 44 and flag[0]["scorebook"] == 45
    assert f.version == 2 and f.as_of_known("score_home", 59)["value"] == 44
    for t in range(61, 70):
        bug(f, t, 600 - t, score_home=44)                            # the bug keeps saying 44
    assert f.snapshot()["score_home"]["value"] == 45                 # it may not pull the value back
    assert f.k["score_home"].bug_raw == 44                           # the raw reading is never overwritten
    assert len(rows(f, "scoreboard_flags")) == 1                     # one flag, not one per reading


def test_a_fresh_play_by_play_row_waits_for_the_bug_inside_its_window_then_is_confirmed():
    f = fuse.Fuser(SPEC, feed=True)
    running(f, 0, 9, score_home=44)
    f.feed_msg({"t": 9, "kind": "pbp", "field": "score_home", "value": 46, "period": 1, "clock_s": 591})
    assert f.snapshot()["score_home"]["value"] == 46 and f.version == 1
    for t in (10, 11, 12):
        bug(f, t, 600 - t, score_home=44)                            # the bug lags the scorer: expected, no flag
    assert f.snapshot()["score_home"]["value"] == 46 and rows(f, "scoreboard_flags") == []
    bug(f, 13, 587, score_home=46)
    assert f.snapshot()["score_home"]["grade"] == "confirmed"


def test_an_implausible_bug_step_is_flagged_and_a_fall_is_a_correction_candidate():
    f = fuse.Fuser(SPEC)
    running(f, 0, 9, score_home=30)
    for t in (10, 11):
        bug(f, t, 600 - t, score_home=37)                            # +7 in one step breaks R-IV-04
    assert rows(f, "scoreboard_flags", "score_home", "implausible_step")
    for t in (12, 13):
        bug(f, t, 600 - t, score_home=35)                            # the operator takes two points back
    assert f.snapshot()["score_home"]["value"] == 35
    assert rows(f, "state_corrections", "score_home", "correction_candidate")


def test_a_review_answer_wins_and_keeps_the_old_version():
    f = fuse.Fuser(SPEC)
    running(f, 0, 9, score_home=30)
    f.feed_msg({"t": 20, "kind": "human", "field": "score_home", "value": 29})
    assert f.snapshot()["score_home"]["value"] == 29 and f.version == 2
    assert rows(f, "state_corrections", "score_home", "review_answer")
    assert f.as_of_known("score_home", 19)["value"] == 30


# ------------------------------------------------------------------------------------------- fouls, shot clock
def test_team_fouls_follow_the_feed_the_whistle_and_the_half():
    f = fuse.Fuser(SPEC, feed=True, audio=True)
    running(f, 0, 9, team_fouls_home=3)
    f.feed_msg({"t": 9, "kind": "pbp", "field": "team_fouls_home", "value": 3, "period": 1, "clock_s": 595})
    assert at(f, 30, "team_fouls_home")["grade"] == "confirmed"      # the bug slot is away, the feed is healthy
    stale_t = 9 + P["feed_stale_after_s"] + 1
    assert at(f, stale_t, "team_fouls_home")["grade"] == "inferred"  # feed stale, no whistle heard: no foul
    f.feed_msg({"t": stale_t + 1, "kind": "cue", "what": "stop"})    # a whistle of unknown cause
    assert at(f, stale_t + 2, "team_fouls_home")["grade"] == "carried"
    g = fuse.Fuser(SPEC)
    running(g, 0, 9, team_fouls_home=6)
    for t in (10, 11):
        bug(g, t, 1200, period=2, team_fouls_home=6)                 # second half: the count is back at 0 by rule
    s = g.snapshot()
    assert s["period"]["value"] == 2 and s["team_fouls_home"]["value"] == 0 and s["team_fouls_home"]["grade"] == "inferred"


def test_the_bug_cannot_contradict_a_foul_count_at_its_cap():
    cap = P["team_foul_bug_cap"]
    f = fuse.Fuser(SPEC, feed=True)
    running(f, 0, 9, team_fouls_home=cap)
    f.feed_msg({"t": 9, "kind": "pbp", "field": "team_fouls_home", "value": cap + 2, "period": 1, "clock_s": 591})
    for t in range(10, 10 + int(P["foul_to_bug_window_s"]) + 5):
        bug(f, t, 600 - t, team_fouls_home=cap)
    assert f.snapshot()["team_fouls_home"]["value"] == cap + 2 and rows(f, "scoreboard_flags") == []


def test_shot_clock_is_a_claim_for_one_horizon_then_carried_then_unknown():
    inf, car = P["shot_clock_inferred_max_s"], P["shot_clock_carried_max_s"]
    f = fuse.Fuser(SPEC)
    running(f, 0, 9, shot_s=25)
    for t in range(10, 10 + int(car) + 3):                           # only the slot is unreadable: FOLLOW_FIELD
        bug(f, t, 600 - t)
        s = f.snapshot()["shot_clock_s"]
        age = t - 9
        want = "inferred" if age <= inf else "carried" if age <= car else "unknown"
        assert s["grade"] == want and (s["value"] == 25 - age if want != "unknown" else s["value"] == "unknown"), (age, s)
    g = fuse.Fuser(SPEC)
    stopped(g, 0, 9, shot_s=14)                                      # whole bug away, clock stopped: the value holds
    assert at(g, 10, "shot_clock_s") == {"value": 14, "grade": "inferred", "age_s": 1, "known_at": 9}
    assert at(g, 9 + car, "shot_clock_s")["grade"] == "carried"
    assert at(g, 9 + car + 1, "shot_clock_s")["grade"] == "unknown"


def test_a_shot_clock_reset_cue_re_anchors_the_value_without_raising_the_grade():
    f = fuse.Fuser(SPEC, main_camera=True)
    running(f, 0, 9, shot_s=8)
    f.advance(13)
    f.feed_msg({"t": 13, "kind": "cue", "what": "shot_reset", "value": 30})
    s = at(f, 15, "shot_clock_s")
    assert s["value"] == 28 and s["grade"] == "carried"


def test_a_frozen_shot_clock_cannot_outlive_a_full_shot_clock_period():
    dwell = SPEC.dwell("shot_clock_s")
    assert dwell == P["max_dwell.shot_clock_period"]
    f = fuse.Fuser(SPEC)
    stopped(f, 0, 9, shot_s=20)
    f.feed_msg({"t": 10, "kind": "meta", "what": "replay", "on": True})
    assert at(f, 9 + dwell, "shot_clock_s")["grade"] == "carried"
    assert at(f, 9 + dwell + 1, "shot_clock_s")["value"] == "unknown"


# ----------------------------------------------------------------------------- the generic machine: any profile
def test_max_dwell_ends_a_carried_try_in_flight_with_the_rule_implied_next_value():
    dwell = SPEC.dwell("try_in_flight", "in_flight")
    assert dwell == SPEC.core["max_dwell"]["try_in_flight"]["value"]
    h = fuse.HeldValue(SPEC, "try_in_flight")
    h.observe(100.0, "in_flight")                                    # released at t = 100
    h.drop(101.0, "not main camera")                                 # a cut to the shooter 1 s into the flight
    assert h.at(101.5) == {"value": "in_flight", "grade": "carried", "age_s": 0.5, "ended": False, "unverified": True}
    assert h.at(100.0 + dwell)["value"] == "in_flight"
    h2 = fuse.GradeTrack(SPEC, "try_in_flight", "carried in_flight or ring_contact older than the max dwell",
                         value="in_flight", start_grade="carried", value_age_s=1.0)
    end = h2.at(dwell - 1.0 + 0.1)
    assert end["ended"] and end["value"] == "none" and end["grade"] == "inferred"   # next_value of the rule


def test_max_dwell_of_a_throw_in_and_a_free_throw_come_from_the_rules():
    assert SPEC.dwell("restart_pending", "throw_in") == SPEC.core["max_dwell"]["throw_in"]["value"]
    assert SPEC.dwell("restart_pending", "free_throw") == SPEC.core["max_dwell"]["free_throw_attempt"]["value"]
    assert SPEC.dwell("restart_pending", "jump_ball") is None        # no bound in the book for this value
    h = fuse.HeldValue(SPEC, "restart_pending")
    h.observe(0.0, "throw_in")                                       # ball at the thrower's disposal
    h.drop(1.0, "not main camera and no clock reading")
    carried_max, dwell = P["status_carried_max_s"], SPEC.dwell("restart_pending", "throw_in")
    assert h.at(1.0 + min(carried_max, dwell - 1.0) - 0.1)["value"] == "throw_in"
    late = h.at(1.0 + max(carried_max, dwell) + 0.1)
    assert late["value"] == "unknown" and late["grade"] == "unknown"  # five seconds are over: it cannot still be pending


def test_max_dwell_of_a_charged_timeout():
    dwell = SPEC.dwell("stoppage", "timeout_team")
    assert dwell == SPEC.core["max_dwell"]["timeout_75"]["value"]
    t = fuse.GradeTrack(SPEC, "stoppage", "charged timeout older than its length", value="timeout_team", start_grade="carried")
    assert t.at(dwell)["value"] == "timeout_team" and t.at(dwell + 0.1)["value"] == "unknown"


def test_lineup_carried_through_a_break_is_marked_unverified_until_seen_again():
    h = fuse.HeldValue(SPEC, "lineup_home")
    five = ("p1", "p2", "p3", "p4", "p5")
    h.observe(0.0, five, grade="confirmed")
    live = fuse.GradeTrack(SPEC, "lineup_home", "live ball", value=five, start_grade="confirmed")
    assert live.at(300.0)["grade"] == "confirmed"                    # R-IV-03: no substitution during live play
    h.drop(400.0, "break")
    s = h.at(460.0)
    assert s["value"] == five and s["grade"] == "carried" and s["unverified"] is True
    h.back(520.0)
    assert h.at(521.0)["unverified"] is True                         # the break is over; still nobody has checked
    h.observe(530.0, ("p1", "p2", "p3", "p4", "p9"), grade="observed")
    assert h.at(531.0)["unverified"] is False and h.at(531.0)["grade"] == "observed"
    assert h.log and h.log[0]["rule"] == "REACQUIRE"                  # the lineup changed during the break: logged


def test_a_status_carried_through_a_break_is_unknown_on_return():
    h = fuse.HeldValue(SPEC, "team_control")
    h.observe(0.0, "home")
    h.drop(5.0, "break")
    assert h.at(50.0)["grade"] == "carried"
    h.back(60.0)
    assert h.at(60.5)["value"] == "unknown"                          # re-acquired, not assumed (step_at on_return)


ALL_RULES = [(k, i) for k, rec in sorted(SPEC.full.items()) for i in range(len(rec["dropout"]))]


@pytest.mark.parametrize("field,i", ALL_RULES)
def test_every_grade_path_of_the_spec_runs_on_the_generic_machine(field, i):
    """Every dropout rule of every field: the grade only moves down the ladder, starts inside the path, ends at its
    last grade, never yields a null, and unknown always carries the value "unknown"."""
    d = SPEC.full[field]["dropout"][i]
    starts, later = lslib.path_steps(d["grade_path"])
    ages = lslib.step_ages(d, SPEC.params)
    nums = [a for a in ages if a != lslib.ON_RETURN]
    horizon = (max(nums) if nums else 0) + 2.0
    for start in starts:
        tr = fuse.GradeTrack(SPEC, field, d["when"], value="v", start_grade=start)
        tr.dwell_s = None                                            # the path alone; max dwell is tested below
        seen = [tr.at(a / 4.0) for a in range(0, int(horizon * 4) + 1)] + [tr.at(horizon, returned=True)]
        ranks = [RANK[s["grade"]] for s in seen]
        assert ranks == sorted(ranks), (field, d["when"])
        assert all(s["value"] is not None and (s["value"] == "unknown") == (s["grade"] == "unknown") for s in seen)
        assert seen[0]["grade"] in ([start] + later)
        assert seen[-1]["grade"] == SPEC.worst(start, *(later or [start]))
        for g, a in zip(later, ages):                                 # each step is taken at its age, not before
            if a != lslib.ON_RETURN and a > 0:
                assert RANK[tr.at(a)["grade"]] < RANK[SPEC.worst(start, g)] or RANK[start] >= RANK[g]
                assert RANK[tr.at(a + 0.01)["grade"]] >= RANK[g]


DWELLS = [(k, v) for k, rec in sorted(SPEC.full.items())
          for v in ([None] if isinstance(rec.get("max_dwell"), (str, dict)) and not rec.get("max_dwell_by_value") else [])
          + list(rec.get("max_dwell_by_value") or {})]


@pytest.mark.parametrize("field,value", DWELLS)
def test_every_max_dwell_of_the_spec_ends_a_carried_value(field, value):
    dwell = SPEC.dwell(field, value)
    assert dwell and dwell > 0
    rule = next(d for d in SPEC.full[field]["dropout"] if "carried" in d["grade_path"])
    tr = fuse.GradeTrack(SPEC, field, rule["when"], value=value or "v", start_grade="carried")
    assert tr.at(dwell + 0.01)["ended"] and tr.at(dwell + 0.01)["value"] != (value or "v")
    obs = fuse.GradeTrack(SPEC, field, rule["when"], value=value or "v", start_grade="observed")
    obs.later, obs.ages = [], []                                      # a value still observed is never ended by the bound
    assert not obs.at(dwell + 100)["ended"]


def test_every_entry_of_the_max_dwell_table_is_used_or_listed_as_not_asked_for():
    used = lslib.machine_params(SPEC.core, SPEC.fields) | {k for k in P if k.startswith("max_dwell.") and f'P["{k}"]' in
                                                             (REPO / "tools/specgen/live_state/fuse.py").read_text()}
    for k in SPEC.core["max_dwell"]:
        if k != "note":
            assert f"max_dwell.{k}" in used or f"max_dwell.{k}" in SPEC.core["production_only_params"], k


# ------------------------------------------------------------------------------------------------ derived fields
def test_a_derived_field_takes_the_worst_input_grade_and_the_oldest_age():
    d = fuse.derive(SPEC, {"score_home": {"grade": "confirmed", "age_s": 0.0}, "score_away": {"grade": "observed", "age_s": 2.0},
                           "game_clock_s": {"grade": "inferred", "age_s": 3.0}})
    assert d["grade"] == "inferred" and d["age_s"] == 3.0 and d["published"]
    d = fuse.derive(SPEC, {"a": {"grade": "observed", "age_s": 1.0}, "b": {"grade": "carried", "age_s": 40.0}})
    assert d["grade"] == "carried" and d["age_s"] == 40.0
    for bad in ("unknown", "quarantined"):
        d = fuse.derive(SPEC, {"a": {"grade": "observed", "age_s": 0.0}, "b": {"grade": bad, "age_s": 0.0}})
        assert d["value"] == "unknown" and not d["published"]
    assert not fuse.derive(SPEC, {"a": {"grade": "observed", "age_s": 0.0}}, valid=False)["published"]


def test_valid_if_of_win_probability_on_the_live_state():
    f = fuse.Fuser(SPEC, counters=("score_home", "score_away"))
    running(f, 0, 9, score_home=50, score_away=48)
    assert fuse.win_probability_valid(SPEC, f.snapshot())
    f.advance(9 + INF)                                               # clock inferred, scores carried and fresh
    s = f.snapshot()
    assert fuse.win_probability_valid(SPEC, s)
    d = fuse.derive(SPEC, {k: s[k] for k in ("score_home", "score_away", "period", "game_clock_s")}, valid=True)
    assert d["grade"] == "carried" and d["age_s"] == INF             # worst input, oldest age
    wide = int(P["wp_clock_interval_max_s"])
    f.advance(9 + wide)
    assert fuse.win_probability_valid(SPEC, f.snapshot())            # carried clock, interval still narrow enough
    f.advance(9 + wide + 1)
    assert not fuse.win_probability_valid(SPEC, f.snapshot())        # interval too wide: withheld
    g = fuse.Fuser(SPEC, counters=("score_home", "score_away"), main_camera=True)
    stopped(g, 0, 9, score_home=50, score_away=48)
    g.feed_msg({"t": 10, "kind": "meta", "what": "main_camera", "on": False})
    g.advance(9 + P["counter_stale_after_s"] + 1)
    assert not fuse.win_probability_valid(SPEC, g.snapshot())        # score carried past its stale mark


def test_bonus_foul_trouble_clutch_and_the_window_reset_follow_their_params():
    one, double = P["bonus_from_team_foul"], P["double_bonus_from_team_foul"]
    assert [fuse.bonus_state(SPEC, n) for n in (one - 1, one, double - 1, double)] == ["none", "one_and_one", "one_and_one", "double_bonus"]
    assert fuse.bonus_state(SPEC, one - 1, "carried") == "unknown" and fuse.bonus_state(SPEC, double - 1, "carried") == "unknown"
    assert fuse.bonus_state(SPEC, one - 2, "carried") == "none" and fuse.bonus_state(SPEC, "unknown") == "unknown"
    h1, e = P["foul_trouble_h1_fouls"], P["foul_trouble_h1_elapsed_max_s"]
    assert fuse.foul_trouble(SPEC, h1, 1, SPEC.half_s - e) and not fuse.foul_trouble(SPEC, h1, 1, SPEC.half_s - e - 1)   # K10
    split = P["foul_trouble_h2_split_s"]
    assert fuse.foul_trouble(SPEC, P["foul_trouble_h2_early_fouls"], 2, split + 1)
    assert not fuse.foul_trouble(SPEC, P["foul_trouble_h2_early_fouls"], 2, split)
    assert fuse.foul_trouble(SPEC, P["foul_trouble_late_fouls"], 2, split) and fuse.foul_trouble(SPEC, P["foul_trouble_late_fouls"], 3, 100)
    c, m = P["clutch_clock_max_s"], P["clutch_margin_max_pts"]
    assert fuse.clutch_flags(SPEC, 2, c, c, m) == {"clutch": "yes", "late_240": "no" if c > P["late_window_s"] else "yes"}
    assert fuse.clutch_flags(SPEC, 2, c - 10, c + 10, m)["clutch"] == "unknown"       # the interval straddles the limit
    assert fuse.clutch_flags(SPEC, 2, c + 1, c + 30, m)["clutch"] == "no"
    assert fuse.clutch_flags(SPEC, 1, 10, 10, 0)["clutch"] == "no"
    assert fuse.clutch_flags(SPEC, 2, 10, 10, m + 1)["clutch"] == "no" and fuse.clutch_flags(SPEC, 2, 10, 10, "unknown")["clutch"] == "unknown"
    assert fuse.reset_make_window(SPEC, 0.5) == P["make_window_min_s"]
    assert fuse.reset_make_window(SPEC, 100.0) == P["make_window_max_s"]
    assert fuse.reset_make_window(SPEC, 5.0) == 5.0 + P["window_margin_s"]


# ----------------------------------------------------------------------------------------------------- contract
def test_messages_must_be_fed_in_time_order():
    f = fuse.Fuser(SPEC)
    bug(f, 10, 600)
    with pytest.raises(ValueError):
        f.advance(9)


def test_no_value_is_ever_null_from_the_first_instant():
    f = fuse.Fuser(SPEC)
    f.advance(0)
    s = f.snapshot()
    assert set(s) >= {"period", "game_clock_s", "game_clock_running", "shot_clock_s", "score_home", "team_fouls_home", "timeouts_left_home"}
    assert all(v["value"] == "unknown" and v["grade"] == "unknown" for v in s.values())


def test_every_param_is_read_by_the_reference_code_or_listed_production_only_with_a_reason():
    core, fields = lslib.load_core(), lslib.load_fields()
    unread = set(lslib.unread_params(core, fields))
    listed = core["production_only_params"]
    assert unread == set(listed)
    assert all(isinstance(r, str) and len(r) > 20 for r in listed.values())
    code = "".join((REPO / "tools/specgen/live_state" / n).read_text() for n in ("fuse.py", "harness.py"))
    for name in ("clock_inferred_max_s", "clock_carried_max_s", "scorebug_down_after_s", "make_confirm_window_s",
                 "pbp_to_bug_window_s", "replay_guard_s", "extra_hidden_share", "shot_clock_inferred_max_s"):
        assert f'P["{name}"]' in code, name                         # the limits the replay rests on are read by name


def test_every_field_the_fuser_handles_is_a_field_of_the_pack_with_the_right_profile():
    index = SPEC.core["field_index"]
    assert index["game_clock_s"]["profile"] == index["shot_clock_s"]["profile"] == "clock"
    for name in fuse.DEFAULT_COUNTERS + ("period",):
        assert index[name]["profile"] == "counter", name
    assert index["game_clock_running"]["profile"] == "status"
