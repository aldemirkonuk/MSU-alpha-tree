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


def test_sm3_continuation_reconfirms():
    """Review round 2 (ATK-06, RV-25): a short detector drop-out of an isolated player ends the chain. The continuation is
    a new chain with the old one as its only parent (a prior, not a lock): HOLD until its own cues confirm it (with
    team colour and jersey only every teammate is a confusable pair, so two sightings), labelled again right after.
    Replaces test_sm3_unique_continuation_inherits_lock (0.1.1 joined the two and kept the lock)."""
    tr = make_truth(6, {0: [(0, 4, Y0), (6, 12, Y0)]})
    sched = {0: reads(0.5, 0.8, "0") + reads(4.0, 4.3, "0")}
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
    assert len(ch) == 2, "the drop-out ends the chain; nothing is joined"
    first, second = sorted(ch, key=lambda c: d2.frame[r.chains[c].dets[0]])
    assert r.chains[second].kind == "group" and r.chains[second].parents == [first]
    assert np.all(labels_of(d2, r, 0, 1.5, 2.9) == 0)
    assert np.all(labels_of(d2, r, 0, 3.2, 3.9) == idlib.HOLD)  # RECONFIRM: the parent's label is a prior only
    assert np.all(labels_of(d2, r, 0, 5.0, 6.0) == 0)  # own cues at 4.0 and 4.6 s -> locked again


def hijack_scene(seed, gap, dist):
    """Player 0 is locked and isolated; at 5.0 s his box is lost for good in mid-frame. Teammate 1, never seen before,
    appears gap seconds later, dist metres away (attack lens script b5_hijack.py). The lineup has both on the floor."""
    paths = {0: [(0, 6.0, 13.6), (14, 6.0, 13.6)], 1: [(0, 6.0 + dist, 13.6), (14, 6.0 + dist, 13.6)]}
    tr = make_truth(14, paths, off={0: [(5.0, 15.0)], 1: [(0.0, 5.0 + gap)]})
    sched = {p_: reads(1.0, 1.3, JERSEY[p_]) for p_ in (0, 2, 3, 4, 7, 8, 9, 10, 11)}
    d, g, info = observe(tr, quiet_profile(), SIGMA, np.random.default_rng(seed), dict(QUIET, jersey_schedule=sched))
    g.cand[:] = False
    g.cand[:, [0, 1, 2, 3, 4, 7, 8, 9, 10, 11]] = True
    return d, g


@pytest.mark.parametrize("gap,dist", [(0.4, 2.0), (1.2, 6.0)])
def test_continuation_of_another_person_is_not_labelled(gap, dist):
    """Review round 2 (ATK-06, RV-25): geometry alone never hands a lock over. In 0.1.1 the teammate who appeared within
    link_window_s and reach inherited player 0's label to the end of the scene, live and offline, with no alarm."""
    for cues in (["team", "jersey"], ALL):
        for seed in (0, 1, 2):
            d, g = hijack_scene(seed, gap, dist)
            res = idlib.run(d, g, {"tracklets": "pure", "cues": cues}, SIGMA)
            assert_no_swaps(d, g, res)
            for mode in ("live", "offline"):
                assert not np.any(res[mode].label[d.src == 1] == 0), (cues, seed, mode)
            if cues == ["team", "jersey"]:  # no cue of his own: HOLD
                assert np.all(res["live"].label[d.src == 1] == idlib.HOLD)


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
# Tracklet and chain purity (review round 2: ST-1, ATK-03, ATK-04, TR-06; RV-22 to RV-26)
# --------------------------------------------------------------------------------------
TOLD = 0.3  # the assigner is told sigma_p 0.30 m: jump test 1.27 m, merge radius 2.27 m


def hand_scene(F, tracks, reads_=None, fov=(-50.0, 80.0), cls_override=None):
    """Detections written by hand: tracks = [(person, {frame: (x, y)})]; team colour read without error unless
    cls_override {(person, frame): class}; jersey reads_ {person: [(f0, f1, number)]}. Cues: team and jersey only."""
    team = np.array([0] * 7 + [1] * 7)
    js = ["0", "1", "3", "11", "23", "35", "5", "2", "4", "10", "12", "21", "33", "44"]
    rows = []
    for p_, pts in tracks:
        for f, (x, y) in pts.items():
            cls = 2 if p_ < 0 else int(team[p_])
            cls = (cls_override or {}).get((p_, f), cls)
            code = -1
            for f0, f1, num in (reads_ or {}).get(p_, []):
                if f0 <= f < f1:
                    code = idlib.jersey_code_full(num)
            rows.append((f, x, y, p_, cls, code))
    rows.sort(key=lambda r_: r_[0])
    a = np.array(rows, dtype=float)
    cut = np.zeros(F, dtype=bool)
    cut[0] = True
    d = idlib.Dets(DT, F, a[:, 0].astype(np.int64), a[:, 1:3].copy(), a[:, 3].astype(np.int64), np.zeros(len(a), dtype=bool),
                   a[:, 4].astype(np.int64), a[:, 5].astype(np.int64), None, None, None, cut, np.tile(np.array(fov, dtype=float), (F, 1)))
    cand = np.zeros((F, 14), dtype=bool)
    cand[:, [0, 1, 2, 3, 4, 7, 8, 9, 10, 11]] = True
    g = idlib.Game(team, js, np.full(14, 1.98), None, None, cand)
    return d, g


def clean_tracklets_are_pure(d, told=TOLD, prm=None):
    trks, det_trk, groups = idlib.build_tracklets(d, told, "pure", prm, ("team",))
    return all(len(set(d.src[t.dets].tolist())) == 1 for t in trks if not t.amb), trks


JCFG = {"tracklets": "pure", "cues": ["team", "jersey"]}


def test_hidden_teammate_handover_is_not_labelled():
    """ATK-03 (RV-23): teammate 1 is lost 2.0 m from player 0 and walks hidden to his other side; 0.32 s later the one
    visible box is his, 0.7 m from player 0's last box (below the jump test, off the vanished man's predicted path, so
    the contested test stays silent). 0.1.1 let player 0's track leave the group after clear_s: one clean tracklet with
    both men, labelled as teammate 1 offline. UNRESOLVED GROUP keeps the track ambiguous while the member is hidden."""
    F = 260
    t0 = {f: (8.0, 13.5) for f in range(0, 108)}
    t1 = {f: (10.0, 13.5) for f in range(0, 100)}
    t1.update({f: (7.3, 13.5) for f in range(108, F)})
    d, g = hand_scene(F, [(0, t0), (1, t1)], {1: [(150, 158, "1"), (170, 178, "1")], 0: [(20, 28, "0"), (40, 48, "0")]})
    pure, trks = clean_tracklets_are_pure(d)
    assert pure, "a clean tracklet holds boxes of two people"
    res = idlib.run(d, g, JCFG, TOLD)
    assert_no_swaps(d, g, res)
    assert np.all(res["offline"].label[(d.src == 1) & (d.frame >= 180)] == 1)  # the teammate is still re-acquired


def test_unresolved_group_resolves_when_the_hidden_member_is_back():
    """UNRESOLVED GROUP waits only while somebody is missing: when the lost teammate re-appears as a track of his own,
    both leave the group after clear_s again (a wait of unresolved_clear_s every time would cost coverage for nothing)."""
    F = 200
    t0 = {f: (8.0, 13.5) for f in range(F)}
    t1 = {f: (10.0, 13.5) for f in range(F) if not 100 <= f < 104}
    d, g = hand_scene(F, [(0, t0), (1, t1)])
    pure, trks = clean_tracklets_are_pure(d)
    assert pure
    back = [t for t in trks if not t.amb and t.start > 100 and d.src[t.dets[0]] == 0]
    assert back and min(t.start for t in back) <= 104 + 2 * idlib.frames(idlib.P["clear_s"], DT) + 1
    assert all(t.parents for t in back)  # group children of {0, 1}


def test_same_edge_exit_and_entry_is_not_one_tracklet():
    """ATK-03 (RV-23): player 0 steps out of view at the right frame edge in the frame in which teammate 1 steps in
    0.7 m away. The motion layer sees one smooth track. EDGE BAND: boxes within edge_band_m of the frame edge are never
    part of a clean tracklet, and the track comes out of the band with no parents (as FOV ENTRY)."""
    F = 260
    t0 = {f: (15.0 + 0.03 * f, 13.5) for f in range(0, 100)}          # walks right, last box at x = 17.97
    t1 = {f: (17.3 - 0.03 * (f - 100), 13.5) for f in range(100, F)}   # walks left from x = 17.3
    d, g = hand_scene(F, [(0, t0), (1, t1)], {0: [(5, 13, "0"), (25, 33, "0")], 1: [(200, 208, "1"), (220, 228, "1")]}, fov=(0.0, 18.0))
    pure, trks = clean_tracklets_are_pure(d)
    assert pure, "exit and entry at the same edge ended up in one clean tracklet"
    band = idlib.P["edge_band_m"]
    for t in trks:
        if not t.amb:
            assert np.all(d.xy[t.dets, 0] < 18.0 - band + 1e-9), "a clean tracklet has a box inside the edge band"
    res = idlib.run(d, g, JCFG, TOLD)
    assert_no_swaps(d, g, res)
    r = res["offline"]
    after = np.unique(r.det_chain[(d.src == 1) & (d.frame >= 200)])
    assert all(r.chains[c].parents == [] for c in after if r.chains[c].kind != "amb")
    assert np.all(r.label[(d.src == 1) & (d.frame >= 230)] == 1)


def test_exit_through_the_edge_band_is_still_an_exit():
    """EDGE BAND makes every track at the frame edge an amb segment; a track lost there still ends with fov_exit (the
    identity is released, it is no parent of anything, and no group waits for it as for a hidden person)."""
    F = 160
    t0 = {f: (15.0 + 0.03 * f, 13.5) for f in range(0, 100)}        # walks out at the right edge (x = 18)
    t1 = {f: (13.0, 13.5) for f in range(110, F)}                    # a teammate is first seen 5 m inside, 0.4 s later
    d, g = hand_scene(F, [(0, t0), (1, t1)], fov=(0.0, 18.0))
    trks, det_trk, groups = idlib.build_tracklets(d, TOLD, "pure", None, ("team",))
    last = trks[det_trk[np.where((d.src == 0) & (d.frame == 99))[0][0]]]
    assert last.amb and last.reason == "fov_exit"
    chains = idlib.link_chains(trks, det_trk, d, TOLD, "pure", None, groups)
    late = [c for c in chains if d.src[c.dets[0]] == 1]
    assert late and all(c.parents == [] for c in late)


def test_fov_edge_start_next_to_another_player_has_no_parents():
    """TR-06 (RV-26): FOV ENTRY also holds for a tracklet that leaves an encounter group next to the frame edge. In 0.1.1
    explicit group parents were returned before the entry test: a teammate entering beside a tracked player became a
    group child of that player. Checked with the edge band switched off (the chain rule alone) and with the pack values."""
    F = 200
    t0 = {f: (16.9, 13.5) for f in range(F)}                                   # stands 1.1 m inside the right edge
    t1 = {f: (17.9, 13.5 + 0.06 * (f - 50)) for f in range(50, F)}              # enters at the edge beside him, walks away along it
    d, g = hand_scene(F, [(0, t0), (1, t1)], {0: [(5, 13, "0"), (25, 33, "0")]}, fov=(0.0, 18.0))
    prm = dict(idlib.P, edge_band_m=0.0)
    trks, det_trk, groups = idlib.build_tracklets(d, TOLD, "pure", prm, ("team",))
    chains = idlib.link_chains(trks, det_trk, d, TOLD, "pure", prm, groups)
    late = [c for c in chains if c.kind != "amb" and d.frame[c.dets[0]] > 50]
    assert late, "the scene must produce clean tracklets after the entry"
    for c in late:
        assert d.fov[0, 1] - d.xy[c.dets[0], 0] < idlib.P["fov_edge_m"] and c.parents == []
    res = idlib.run(d, g, JCFG, TOLD)  # pack values: nothing inside the band is ever labelled
    assert_no_swaps(d, g, res)
    for mode in ("live", "offline"):
        assert np.all(res[mode].label[d.frame > 50] == idlib.HOLD)


def test_opponent_hidden_behind_a_player_takes_his_box_no_label():
    """ST-1 / ATK-04 (RV-22, RV-24): opponent 7 is lost 1.6 m from locked player 0; 0.28 s later player 0 is hidden and
    the one visible box is the opponent's, 0.6 m away; one of its colour reads is wrong. 0.1.1 exempted other classes
    from the merge and contested tests (team colour was meant to separate them) and labelled the misread box.
    OPP GUARD: a track that loses its detection fails with every track in the merge radius, whatever the class."""
    F = 220
    t0 = {f: (8.0, 13.5) for f in range(0, 107)}
    t7 = {f: (9.6, 13.5) for f in range(0, 100)}
    t7.update({f: (8.6, 13.5) for f in range(107, F)})
    d, g = hand_scene(F, [(0, t0), (7, t7)], {0: [(20, 28, "0"), (40, 48, "0")]}, cls_override={(7, 109): 0})
    pure, trks = clean_tracklets_are_pure(d)
    assert pure, "the player's clean tracklet continues on the opponent's box"
    res = idlib.run(d, g, JCFG, TOLD)
    assert_no_swaps(d, g, res)
    assert np.all(res["live"].label[(d.src == 0) & (d.frame >= 60) & (d.frame < 96)] == 0)  # locked before the encounter


def official_takeover(n_off, misread_at):
    """A locked, isolated player whose boxes are an official's for n_off frames from frame 150 (same place, no jump,
    nobody lost nearby: no tracklet test can fire). One official box is read as the player's team."""
    F = 320
    t0 = {f: (8.0, 13.5) for f in range(F) if not 150 <= f < 150 + n_off}
    tr_ = {f: (8.0, 13.5) for f in range(150, 150 + n_off)}
    return hand_scene(F, [(0, t0), (-1, tr_)], {0: [(20, 28, "0"), (40, 48, "0")]}, cls_override={(-1, misread_at): 0})


def test_track_jump_to_official_with_one_colour_misread_emits_no_label():
    """ATK-04 (RV-24): the colour check is per box, so the one official box read as the team carried the locked label
    (posterior 0.9999) before the 1 s class alarm. COLOUR LATCH: after a box that shows another class the label is
    withheld until colour_latch_n boxes in a row show the chain's class again (offline also before such a box)."""
    d, g = official_takeover(15, 155)
    res = idlib.run(d, g, JCFG, TOLD)
    for mode in ("live", "offline"):
        assert not np.any(res[mode].label[d.src < 0] >= 0), f"{mode}: label on an official's box"
    assert_no_swaps(d, g, res)
    assert res["live"].stats["latch_hold"] >= 1
    d, g = official_takeover(15, 150)  # the FIRST official box is the misread one: only offline can know (latch before)
    res = idlib.run(d, g, JCFG, TOLD)
    assert not np.any(res["offline"].label[d.src < 0] >= 0)


def test_class_alarm_splits_at_the_first_contradicting_box():
    """ATK-04 (RV-24): with no encounter on record the class alarm used to split at the alarm frame, 1 s after the
    swap. It now splits at the first box of the run of contradicting boxes and logs it."""
    d, g = official_takeover(60, 155)
    res = idlib.run(d, g, JCFG, TOLD)
    assert_no_swaps(d, g, res)
    al = [x for x in res["live"].log if x["kind"] == "class_alarm"]
    assert len(al) == 1 and al[0]["frame"] > 150 + 5
    assert al[0]["split_frame"] == 150 and al[0]["first_bad_frame"] == 150


def test_foreign_teammate_tail_is_not_labelled_offline():
    """ST-1 (RV-22), BRACKET: the last nine boxes of a locked chain are a teammate's (a hand-over no tracklet test saw).
    The posterior of the chain's label stays 1.0. Offline no label stays outside two agreeing own-cue samples; live the
    label stops at the first sample that contradicts it (the boxes before that sample cannot be known live)."""
    tr = make_truth(12, {0: [(0, 8, Y0), (12, 8, Y0)]})
    d, g, info = observe(tr, quiet_profile(), SIGMA, np.random.default_rng(3), dict(QUIET, jersey_schedule={0: reads(1.0, 1.3, "0")}))
    own = np.where(d.src == 0)[0]
    samp = own[~np.isnan(d.emb[own, 0])]
    fs = int(d.frame[samp[np.searchsorted(d.frame[samp], 200)]])  # an own-cue sample of player 0 near 8 s
    keep = ~((d.src == 0) & (d.frame > fs + 9))
    d = idlib.Dets(d.dt, d.n_frames, d.frame[keep], d.xy[keep], d.src[keep], d.nocue[keep], d.cls_obs[keep], d.jersey[keep],
                   d.emb[keep], d.height[keep], d.gait[keep], d.cut, d.fov)
    tail = np.where((d.src == 0) & (d.frame > fs))[0]
    assert len(tail) == 9
    d.src[tail] = 1                                 # the boxes are teammate 1's ...
    s1 = tail[d.frame[tail] == fs + 5]              # ... and the one cue sample among them is his
    assert not np.isnan(d.emb[s1[0], 0])
    d.emb[s1], d.height[s1], d.gait[s1] = g.template[1], g.height_ref[1], g.gait_ref[1]
    res = idlib.run(d, g, {"tracklets": "pure", "cues": ALL}, SIGMA)
    off, live = res["offline"], res["live"]
    assert np.all(off.label[tail] == idlib.HOLD) and wrong(d, off) == 0
    body = off.label[(d.src == 0) & (d.frame >= 100) & (d.frame <= fs)]
    assert np.all((body == 0) | (body == idlib.HOLD)) and np.mean(body == 0) > 0.25  # the chain keeps its label where samples agree
    assert np.all(live.label[tail[d.frame[tail] >= fs + 5]] == idlib.HOLD)
    assert wrong(d, live) <= 4  # the four boxes before the contradicting sample: unknowable live (live residual, RV-22)
    assert off.stats["bracket_hold"] >= 9


def test_bracket_needs_a_dense_cue():
    """Configurations without appearance, height or gait have no dense samples and skip the BRACKET rule (their rows in
    the cue-ablation table are not protected by it)."""
    tr = make_truth(6, {0: [(0, 8, Y0), (6, 8, Y0)]})
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": {0: reads(1.0, 1.3, "0")}})
    assert res["offline"].stats["bracket_hold"] == 0 and np.all(labels_of(d, res["offline"], 0, 0.0, 6.0) == 0)
    d, g, info, res = run_scene(tr, cues=ALL, opts={"jersey_schedule": {0: reads(1.0, 1.3, "0")}})
    lab = labels_of(d, res["offline"], 0, 0.0, 6.0)
    assert_no_swaps(d, g, res)
    assert np.sum(lab == idlib.HOLD) <= 2 * idlib.frames(idlib.P["cue_stride_s"], DT) and np.sum(lab == 0) > 130


def test_no_cue_box_never_starts_a_clean_tracklet():
    """A track born on a merged / no-cue box starts as an amb segment (RV-23): the box may hold two people."""
    F = 60
    t0 = {f: (8.0, 13.5) for f in range(10, F)}
    d, g = hand_scene(F, [(0, t0)])
    d.nocue[d.frame == 10] = True
    trks, det_trk, groups = idlib.build_tracklets(d, TOLD, "pure", None, ("team",))
    first = trks[det_trk[np.where(d.frame == 10)[0][0]]]
    assert first.amb


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


# ---- review round 2 (RV-15, RV-16): jersey reads are not independent after 0.2 s, and a two-digit number is read as one digit.
# Both scenes fail on the 0.2.0 harness-batch rules (the wrong label is emitted, live and offline); the assigner batch that
# changes the jersey rules must make them pass and then remove the xfail marks.
@pytest.mark.xfail(strict=True, reason="RV-15 / SOTA-01: two reads 0.3 s apart count as two independent sightings and lock the misread number")
def test_repeated_misread_within_one_view_never_locks():
    """One view of the jersey of player 4 (number 23), interrupted for 0.3 s, misread both times as 11 (player 3, a
    teammate on the floor). Jersey and team colour only: the wrong label must never be emitted."""
    tr = make_truth(12.0, paths={4: [(0, 5.0, 13.2)]})
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": {4: [(3.0, 3.2, "11"), (3.5, 3.7, "11")]}})
    assert_no_swaps(d, g, res)


@pytest.mark.xfail(strict=True, reason="RV-16 / SOTA-03: a full one-digit read of a two-digit number counts 7.5 nats against the truth and locks the teammate who wears that digit")
def test_truncated_read_never_locks_the_one_digit_teammate():
    """Player 4 wears 23; player 2 (number 3) is on the floor. Two full reads '3' on the chain of 23 (one digit hidden,
    not flagged partial): label 3 must never be emitted for him."""
    tr = make_truth(12.0, paths={4: [(0, 5.0, 13.2)]})
    d, g, info, res = run_scene(tr, cues=["team", "jersey"], opts={"jersey_schedule": {4: reads(3.0, 3.2, "3")}})
    assert_no_swaps(d, g, res)
