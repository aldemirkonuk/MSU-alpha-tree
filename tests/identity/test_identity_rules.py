"""Synthetic rule tests for config/identity_pack.yaml (state machine, assignment, swap catch, hard cases).

Scenes come from tools/specgen/identity/synth.py (two teams of seven, 25 Hz, absolute court metres) and the
observation simulator with random parts switched off, so every test controls exactly which cues exist and
when. The zero-swap rule is checked in every test: no detection may carry a wrong label, live or offline.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "identity"))

import idlib  # noqa: E402
import metrics  # noqa: E402
from obsmodel import observe  # noqa: E402
from synth import DT, QUIET, make_truth, quiet_profile  # noqa: E402

SIGMA = 0.1
ALL = ["team", "jersey", "appearance", "height", "gait"]


def run_scene(truth, cues=ALL, opts=None, prof=None, sigma=SIGMA, seed=3, **cfg_kw):
    o = dict(QUIET)
    o.update(opts or {})
    d, g, info = observe(truth, prof or quiet_profile(), sigma, np.random.default_rng(seed), o)
    cfg = {"tracklets": "pure", "cues": cues, "lineup": True, "abstain": True, "alarms": True, "splits": True}
    cfg.update(cfg_kw)
    res = idlib.run(d, g, cfg, sigma)
    return d, g, info, res


def wrong(d, r):
    return int(np.sum((r.label >= 0) & (r.label != d.src)))


def assert_no_swaps(d, g, res):
    for mode in ("live", "offline"):
        r = res[mode]
        assert wrong(d, r) == 0, f"{mode}: {wrong(d, r)} wrongly labelled detections"
        inv = metrics.invariant_breaks(d, r.label, g.cand)
        assert inv == {"inv1_duplicates": 0, "inv3_outside_lineup": 0}, (mode, inv)


def labels_of(d, r, p, t0, t1):
    m = (d.src == p) & (d.frame >= int(round(t0 / DT))) & (d.frame <= int(round(t1 / DT)))
    return r.label[m]


def reads(t0, t1, num):
    """Two sightings 0.6 s apart: one sighting alone never locks (sighting_cap_nats)."""
    return [(t0, t1, num), (t0 + 0.6, t1 + 0.6, num)]


# Scenes run in the free area x < 15 m, y > 12.5 m (synth's default spots are elsewhere, > 2.5 m away).
# a cross of two teammates: 0 runs right along y = 13.2, 1 runs left along y = 13.5, they pass at t ~ 4.5 s
Y0 = 13.2
CROSS = {0: [(0, 6, Y0), (3, 6, Y0), (6, 12, Y0), (12, 12, Y0)], 1: [(0, 12, Y0 + 0.3), (3, 12, Y0 + 0.3), (6, 6, Y0 + 0.3), (12, 6, Y0 + 0.3)]}
JERSEY = {0: "0", 1: "1", 2: "3", 3: "11", 4: "23", 7: "2", 8: "4", 9: "10", 10: "12", 11: "21"}


# --------------------------------------------------------------------------------------
# State machine
# --------------------------------------------------------------------------------------
def test_sm2_lock_needs_evidence_and_locks_with_it():
    tr = make_truth(6, {0: [(0, 8, Y0), (6, 8, Y0)]})
    sched = {0: reads(1.0, 1.3, "0")}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched})
    assert_no_swaps(d, g, res)
    assert np.all(labels_of(d, res["live"], 0, 0.0, 0.9) == idlib.HOLD)  # nothing before the first read
    assert np.all(labels_of(d, res["live"], 0, 2.2, 6.0) == 0)  # locked after two sightings, kept to the end
    assert np.all(labels_of(d, res["offline"], 0, 0.0, 6.0) == 0)  # offline: the whole chain


def test_sm2_elimination_alone_never_locks():
    """Four teammates confirmed by jersey; the fifth has no cue of his own and must stay HOLD."""
    tr = make_truth(6)
    sched = {p: reads(1.0, 1.3, JERSEY[p]) for p in (0, 1, 2, 3)}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched})
    assert_no_swaps(d, g, res)
    for mode in ("live", "offline"):
        assert np.all(labels_of(d, res[mode], 4, 0, 6) == idlib.HOLD)
        assert np.all(labels_of(d, res[mode], 1, 2.2, 6) == 1)


def test_sm3_unique_continuation_inherits_lock():
    """A short detector drop-out of an isolated player keeps the same chain and its lock."""
    tr = make_truth(6, {0: [(0, 4, Y0), (6, 12, Y0)]})
    sched = {0: reads(0.5, 0.8, "0")}
    o = dict(QUIET, jersey_schedule=sched)
    d, g, info = observe(tr, quiet_profile(), SIGMA, np.random.default_rng(3), o)
    gapf = (d.src == 0) & (d.frame >= 75) & (d.frame < 79)  # 4 missing frames at 3.0 s
    keep = ~gapf
    d2 = idlib.Dets(d.dt, d.n_frames, d.frame[keep], d.xy[keep], d.src[keep], d.nocue[keep], d.cls_obs[keep], d.jersey[keep],
                    d.emb[keep], d.height[keep], d.gait[keep], d.cut, d.fov)
    res = idlib.run(d2, g, {"tracklets": "pure", "cues": ["team", "jersey"]}, SIGMA)
    assert_no_swaps(d2, g, res)
    r = res["live"]
    ch = np.unique(r.det_chain[d2.src == 0])
    assert len(ch) == 1, "the drop-out must not break the chain"
    assert np.all(labels_of(d2, r, 0, 1.5, 6.0) == 0)


def test_crossing_reconfirmed_by_jersey():
    tr = make_truth(12, CROSS)
    sched = {0: reads(1.0, 1.3, "0") + reads(8.0, 8.3, "0"), 1: reads(1.0, 1.3, "1") + reads(9.0, 9.3, "1")}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched})
    assert_no_swaps(d, g, res)
    live = res["live"]
    assert np.all(labels_of(d, live, 0, 6.5, 7.9) == idlib.HOLD)  # RECONFIRM: no label until a cue says who
    assert np.all(labels_of(d, live, 0, 9.1, 12) == 0)
    assert np.all(labels_of(d, live, 1, 10.1, 12) == 1)
    kinds = {live.chains[c].kind for c in np.unique(live.det_chain[d.src == 0])}
    assert "group" in kinds
    # offline frame matching: one read after the crossing labels the whole post-crossing chain
    assert np.all(labels_of(d, res["offline"], 0, 6.5, 12) == 0)


def test_crossing_without_evidence_holds():
    tr = make_truth(12, CROSS)
    sched = {0: reads(1.0, 1.3, "0"), 1: reads(1.0, 1.3, "1")}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched})
    assert_no_swaps(d, g, res)
    for mode in ("live", "offline"):
        assert np.all(labels_of(d, res[mode], 0, 6.5, 12) == idlib.HOLD)
        assert np.all(labels_of(d, res[mode], 1, 6.5, 12) == idlib.HOLD)
        assert np.all(labels_of(d, res[mode], 0, 2.2, 2.5) == 0)


def test_opponent_crossing_resolved_by_team_colour():
    """An attacker and a defender cross: team colour separates them, no jersey re-confirmation needed (appearance
    samples only have to not contradict the inherited label)."""
    paths = {0: CROSS[0], 7: CROSS[1]}
    tr = make_truth(12, paths)
    sched = {0: reads(1.0, 1.3, "0"), 7: reads(1.0, 1.3, "2")}
    d, g, info, res = run_scene(tr, cues=ALL, opts={"jersey_schedule": sched})
    assert_no_swaps(d, g, res)
    assert np.mean(labels_of(d, res["offline"], 0, 6.5, 12) == 0) > 0.9
    assert np.mean(labels_of(d, res["offline"], 7, 6.5, 12) == 7) > 0.9


def test_pileup_group_of_four():
    pts = [(9.0, 13.2), (9.4, 13.5), (9.2, 13.8), (8.8, 13.5)]
    starts = {0: (5, 12.8), 1: (13, 12.8), 7: (3, 14.8), 8: (15.5, 14.8)}  # not on one camera ray
    paths = {p: [(0, *starts[p]), (2, *starts[p]), (4, *pt), (6, *pt), (8, *starts[p]), (12, *starts[p])]
             for p, pt in zip(starts, pts)}
    tr = make_truth(12, paths)
    sched = {p: reads(0.5, 0.8, JERSEY[p]) + reads(10.0, 10.3, JERSEY[p]) for p in starts}
    d, g, info = observe(tr, quiet_profile(), SIGMA, np.random.default_rng(3), dict(QUIET, jersey_schedule=sched))
    trks, det_trk, groups = idlib.build_tracklets(d, SIGMA, "pure", None, {"team"})
    assert max((len(v) for v in groups.values()), default=0) >= 3, "the pile-up must form one encounter group"
    res = idlib.run(d, g, {"tracklets": "pure", "cues": ["team", "jersey"]}, SIGMA)
    assert_no_swaps(d, g, res)
    for p in starts:
        assert np.all(labels_of(d, res["live"], p, 11.2, 12) == p)


def test_same_build_pair_needs_jersey():
    tr = make_truth(12, CROSS)
    prof = quiet_profile()
    cues = ["team", "appearance", "height", "gait"]
    sched = {0: reads(1.0, 1.3, "0"), 1: reads(1.0, 1.3, "1")}
    d, g, info, res = run_scene(tr, cues=cues, prof=prof, opts={"jersey_schedule": sched, "twins": [(0, 1)]})
    assert_no_swaps(d, g, res)
    sched2 = {0: reads(1.0, 1.3, "0") + reads(8.0, 8.3, "0"), 1: reads(1.0, 1.3, "1") + reads(8.0, 8.3, "1")}
    d, g, info, res = run_scene(tr, cues=cues + ["jersey"], prof=prof, opts={"jersey_schedule": sched2, "twins": [(0, 1)]})
    assert_no_swaps(d, g, res)
    assert np.all(labels_of(d, res["live"], 0, 9.2, 12) == 0)


def test_partial_digit_reads_count():
    """Only partial reads ('2' of 23): enough among the on-court numbers 0, 1, 3, 11, 23."""
    tr = make_truth(6, {4: [(0, 8, Y0), (6, 8, Y0)]})
    code2 = idlib.PARTIAL0 + 2
    sched = {4: reads(1.0, 1.1, code2) + reads(2.0, 2.1, code2) + reads(3.0, 3.1, code2) + reads(4.0, 4.1, code2)}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched})
    assert_no_swaps(d, g, res)
    assert np.all(labels_of(d, res["offline"], 4, 0, 6) == 4)


def test_same_number_both_teams():
    js = ["0", "1", "3", "11", "23", "35", "5", "0", "4", "10", "12", "21", "33", "44"]  # 0 and 7 both wear 0
    paths = {0: CROSS[0], 7: CROSS[1]}
    tr = make_truth(12, paths, jerseys=js)
    sched = {0: reads(1.0, 1.3, "0") + reads(8.0, 8.3, "0"), 7: reads(1.0, 1.3, "0") + reads(8.0, 8.3, "0")}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched})
    assert_no_swaps(d, g, res)
    assert np.all(labels_of(d, res["live"], 0, 9.2, 12) == 0)
    assert np.all(labels_of(d, res["live"], 7, 9.2, 12) == 7)


def test_camera_cut_releases_and_reacquires():
    paths = {0: [(0, 6, Y0), (4, 6, Y0), (6, 12, 14.5), (12, 12, 14.5)], 1: [(0, 12, Y0), (4, 12, Y0), (6, 4, 14.0), (12, 4, 14.0)]}
    tr = make_truth(12, paths)
    cut = (int(4.0 / DT), int(6.0 / DT))
    sched = {0: reads(1.0, 1.3, "0") + reads(9.0, 9.3, "0"), 1: reads(1.0, 1.3, "1") + reads(9.5, 9.8, "1")}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched, "cut_intervals": [cut]})
    assert_no_swaps(d, g, res)
    live = res["live"]
    for c in live.chains:  # SM-9: no chain crosses the cut
        fr = d.frame[c.dets]
        assert not (fr.min() < cut[0] and fr.max() >= cut[1])
        if fr.min() >= cut[1]:
            assert c.parents == []
    assert np.all(labels_of(d, live, 0, 6.0, 8.9) == idlib.HOLD)
    assert np.all(labels_of(d, live, 0, 10.1, 12) == 0)


def test_fov_exit_releases():
    paths = {0: [(0, 12, Y0), (2, 12, Y0), (5, 24, 14.5), (7, 24, 14.5), (10, 12, Y0), (14, 12, Y0)]}
    tr = make_truth(14, paths, ball=np.tile([10.0, 7.0], (int(round(14 / DT)) + 1, 1)))
    sched = {0: reads(0.5, 0.8, "0") + reads(12.0, 12.3, "0")}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched, "fov": True})
    assert_no_swaps(d, g, res)
    live = res["live"]
    back = (d.src == 0) & (d.frame >= int(9.0 / DT))
    ch = np.unique(live.det_chain[back])
    assert all(live.chains[c].parents == [] for c in ch), "re-entry starts without parents (released on exit)"
    assert np.all(labels_of(d, live, 0, 9.0, 11.9) == idlib.HOLD)
    assert np.all(labels_of(d, live, 0, 13.1, 14) == 0)


def test_substitution_window():
    """Player 4 goes to the bench at a dead ball; bench player 5 takes his place."""
    paths = {5: [(0, 19.7, 11.8), (14, 19.7, 11.8)]}
    tr = make_truth(14, paths, off={4: [(6.0, 15.0)], 5: [(0.0, 6.0)]}, gaps=[6.0])
    sched = {4: reads(1.0, 1.3, "23"), 5: reads(9.0, 9.3, "35")}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched})
    assert_no_swaps(d, g, res)
    assert np.all(labels_of(d, res["live"], 5, 10.1, 14) == 5)
    assert not np.any(res["offline"].label[d.frame >= int(6.0 / DT)] == 4)


def test_free_throw_lineup_reacquired():
    """After the dead-ball cut, eight players stand in the lane spaces (0.9 m apart); jersey reads re-acquire them."""
    lane = [(-2.3, 2.1), (2.3, 2.1), (-2.3, 3.0), (2.3, 3.0), (-2.3, 3.9), (2.3, 3.9), (-2.3, 4.8), (2.3, 4.8)]
    who = [7, 8, 0, 1, 9, 10, 2, 3]
    paths = {p: [(0, 6 + k, 3 + 0.5 * k), (4, 6 + k, 3 + 0.5 * k), (6, 26.0 - y, 7.62 + x), (12, 26.0 - y, 7.62 + x)]
             for k, (p, (x, y)) in enumerate(zip(who, lane))}
    tr = make_truth(12, paths, gaps=[5.0])
    sched = {p: reads(6.0 + 0.3 * k, 6.2 + 0.3 * k, JERSEY[p]) for k, p in enumerate(who)}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched, "cut_intervals": [(int(4.5 / DT), int(5.5 / DT))]})
    assert_no_swaps(d, g, res)
    for p in who:
        assert np.all(labels_of(d, res["live"], p, 10.0, 12) == p)


def test_referee_never_labelled():
    tr = make_truth(20)
    sched = {p: reads(1.0, 1.3, JERSEY[p]) for p in JERSEY}
    prof = quiet_profile()
    d, g, info, res = run_scene(tr, cues=ALL, prof=prof, opts={"jersey_schedule": sched, "refs": True}, sigma=0.15)
    assert_no_swaps(d, g, res)
    for mode in ("live", "offline"):
        assert not np.any(res[mode].label[d.src < 0] >= 0)


def test_injected_tracker_swap_is_split_offline():
    """Two teammates run side by side 1.2 m apart; at 6 s the cue streams of the two boxes are exchanged (an upstream
    tracker swap the motion layer cannot see). Live raises an alarm; offline splits the chain at the encounter."""
    paths = {0: [(0, 1.0, 2.0), (12, 1.0, 14.0)], 1: [(0, 2.2, 2.0), (12, 2.2, 14.0)]}  # side by side, not on one camera ray
    tr = make_truth(12, paths)
    sched = {p: reads(1.0, 1.3, n) + reads(8.0, 8.3, n) + [(10.0, 10.3, n)] for p, n in ((0, "0"), (1, "1"))}
    o = dict(QUIET, jersey_schedule=sched)
    d, g, info = observe(tr, quiet_profile(), SIGMA, np.random.default_rng(3), o)
    k = int(6.0 / DT)
    a = np.where((d.src == 0) & (d.frame >= k))[0]
    b = np.where((d.src == 1) & (d.frame >= k))[0]
    fa, fb = d.frame[a], d.frame[b]
    common = np.intersect1d(fa, fb)
    ia, ib = a[np.isin(fa, common)], b[np.isin(fb, common)]
    d.src[ia], d.src[ib] = 1, 0  # the boxes keep their smooth paths but now show the other person
    for arr in (d.jersey, d.emb, d.height, d.gait, d.cls_obs):
        tmp = arr[ia].copy()
        arr[ia] = arr[ib]
        arr[ib] = tmp
    prm = dict(idlib.P, encounter_m=1.5)
    res = idlib.run(d, g, {"tracklets": "pure", "cues": ["team", "jersey"]}, SIGMA, prm)
    off = res["offline"]
    assert wrong(d, off) == 0
    assert any(x["kind"] == "offline_split" for x in off.log)
    assert any(x["kind"] == "alarm" for x in res["live"].log)
    assert np.all(labels_of(d, off, 1, 8.5, 12) == 1)


# --------------------------------------------------------------------------------------
# Assignment and cue models
# --------------------------------------------------------------------------------------
def test_joint_marginals_exact_and_exclusive():
    rng = np.random.default_rng(0)
    S = rng.normal(size=(3, 5)) * 3
    marg, exact = idlib.joint_marginals(S, 10000)
    assert exact
    import itertools
    w, M = [], np.zeros((3, 5))
    for perm in itertools.permutations(range(5), 3):
        w.append(np.exp(sum(S[i, perm[i]] for i in range(3))))
    w = np.array(w) / np.sum(w)
    for wt, perm in zip(w, itertools.permutations(range(5), 3)):
        for i in range(3):
            M[i, perm[i]] += wt
    assert np.allclose(marg, M)
    assert np.all(marg.sum(0) <= 1 + 1e-9)  # one label holds at most probability 1 over all chains


def test_joint_marginals_fallback_flagged():
    marg, exact = idlib.joint_marginals(np.zeros((6, 9)), 100)
    assert not exact and np.allclose(marg.sum(1), 1)


def test_jersey_likelihoods():
    full, part = idlib.jersey_ll_table(["23", "3", "0"], 0.1, 0.5, 0.05)
    i23 = idlib.NUM_INDEX["23"]
    assert full[i23, 0] == pytest.approx(np.log(0.9))
    assert "28" in idlib.confusables("23")
    assert full[idlib.NUM_INDEX["28"], 0] > full[idlib.NUM_INDEX["45"], 0]  # a confusable error is likelier
    assert part[2, 0] > part[2, 1]  # partial '2' supports 23 over 3
    assert np.allclose(np.exp(full).sum(0), 1.0)


def test_cue_ablation_switches_cues_off():
    tr = make_truth(4)
    d, g, info = observe(tr, quiet_profile(), SIGMA, np.random.default_rng(1), dict(QUIET))
    assert np.all(idlib.own_evidence(d, g, set()) == 0)
    assert np.any(idlib.own_evidence(d, g, {"appearance"}) != 0)
    assert np.all(idlib.class_evidence(d, set()) == 0)


# --------------------------------------------------------------------------------------
# Owner decisions of 25 Oct 2026: OD-8 probable tier (offline, flagged, never in `label`), OD-10 live panel HOLD
# --------------------------------------------------------------------------------------
def test_od8_single_sighting_gives_a_probable_label_not_a_lock():
    """One jersey sighting (capped at sighting_cap_nats) is not enough to lock (posterior about 0.93 < p_lock) but passes the
    probable bar: the locked label stays HOLD, the offline probable label is the right player, and nothing is wrong."""
    tr = make_truth(6, {0: [(0, 8, Y0), (6, 8, Y0)]})
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": {0: [(1.0, 1.3, "0")]}})
    assert_no_swaps(d, g, res)
    off = res["offline"]
    m0 = d.src == 0
    assert np.all(off.label[m0] == idlib.HOLD)
    assert np.mean(off.probable[m0] == 0) > 0.9 and not np.any((off.probable >= 0) & (off.probable != d.src))
    pm = metrics.probable_metrics(d, off.label, off.probable, d.dt)
    assert pm["probable_wrong_frames"] == 0 and pm["probable_coverage_gain"] > 0
    # OD-10: the live result carries no probable or provisional label
    live = res["live"]
    assert live.probable is None or np.all(live.probable == idlib.HOLD)
    assert np.all(live.label[m0] == idlib.HOLD)


def test_od8_elimination_never_gives_a_probable_label():
    """The probable bar still needs the chain's own cue: the fifth player of sm2_elimination stays HOLD in both tiers."""
    tr = make_truth(6)
    sched = {p: reads(1.0, 1.3, JERSEY[p]) for p in (0, 1, 2, 3)}
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": sched})
    m4 = d.src == 4
    assert np.all(res["offline"].probable[m4] == idlib.HOLD) and np.all(res["offline"].label[m4] == idlib.HOLD)


def test_od8_probable_tier_never_changes_locked_labels():
    """The probable tier is a separate output: switching it off (p_probable > 1) leaves every locked label identical, and
    a probable label never repeats a locked or another probable label in a frame."""
    tr = make_truth(8, CROSS)
    sched = {0: [(1.0, 1.3, "0")], 1: reads(0.5, 0.8, "1") + [(7.0, 7.3, "1")]}
    o = dict(QUIET, jersey_schedule=sched)
    d, g, info = observe(tr, quiet_profile(), SIGMA, np.random.default_rng(3), o)
    cfg = {"tracklets": "pure", "cues": ["team", "jersey"], "lineup": True, "abstain": True, "alarms": True, "splits": True}
    on = idlib.run(d, g, cfg, SIGMA)
    off = idlib.run(d, g, cfg, SIGMA, dict(idlib.P, p_probable=1.1))
    for mode in ("live", "offline"):
        assert np.array_equal(on[mode].label, off[mode].label)
    assert np.all(off["offline"].probable == idlib.HOLD)
    lab, pb = on["offline"].label, on["offline"].probable
    for f in np.unique(d.frame[pb >= 0]):
        lo, hi = d.fstart[f], d.fstart[f + 1]
        both = np.concatenate([lab[lo:hi][lab[lo:hi] >= 0], pb[lo:hi][pb[lo:hi] >= 0]])
        assert len(both) == len(np.unique(both))
