"""Tests of the harness itself (review round 2, RV-11 to RV-21): the simulator's optional error models, the box-order
shuffle, the seeds default, the exposure and rate bound behind a swap count, mechanism attribution, cue statistics and
the spec hashes. Synthetic scenes only (tools/specgen/identity/synth.py); no private data.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "identity"))

import harness  # noqa: E402
import idlib  # noqa: E402
import metrics  # noqa: E402
from obsmodel import FLAG_KEYS, observe, profile  # noqa: E402
from synth import DT, QUIET, make_truth, quiet_profile  # noqa: E402

SPEC = idlib.SPEC
STORED = {"good": "8244116ef501c13c", "poor": "7dcd29463a085045", "poor_uncalibrated": "7dcd29463a085045"}  # from the 0.1.1 code


def busy_scene():
    paths = {0: [(0, 3.0, 13.2), (9, 12.0, 13.2), (20, 4.0, 13.4)], 1: [(0, 12.0, 13.5), (9, 3.0, 13.5), (20, 11.0, 13.3)],
             7: [(0, 5.0, 12.8), (10, 10.0, 13.4), (22, 5.0, 13.0)]}
    return make_truth(30.0, paths=paths, off={5: [(0.0, 15.0)], 4: [(15.0, 31.0)]}, gaps=(15.0,))


def fingerprint(d, g):
    h = hashlib.sha256()
    for a in (d.frame, d.xy, d.nocue, d.cls_obs, d.jersey, d.emb, d.height, d.gait, d.cut, d.fov, d.src, g.cand, g.height_ref, g.template, g.gait_ref):
        a = np.asarray(a)
        h.update(np.round(a, 9).tobytes() if a.dtype.kind == "f" else a.tobytes())
    return h.hexdigest()[:16]


def sim(prof=None, opts=None, seed=5, truth=None, sigma=0.1, prm=None):
    o = dict(QUIET)
    o.update(opts or {})
    return observe(truth or make_truth(20.0), prof or quiet_profile(), sigma, np.random.default_rng(seed), o, prm)


@pytest.mark.parametrize("name", sorted(STORED))
def test_stored_profiles_reproduce_bit_for_bit(name):
    """The stored cue profiles give exactly the 0.1.1 detections when the box-order shuffle is off: every new error model
    draws from a side random stream and is off in them."""
    d, g, _ = observe(busy_scene(), profile(name), 0.3, np.random.default_rng(7), {"shuffle": False})
    assert fingerprint(d, g) == STORED[name]
    opt = set(SPEC["harness"]["cue_profile_options"])
    assert not opt & set(SPEC["harness"]["cue_profiles"][name]), "a stored profile switches a new option on"


def test_box_order_is_shuffled_and_the_spec_does_not_depend_on_it():
    """RV-13 (leak L2): boxes of a frame no longer arrive sorted by true roster index; the labels of config full are the
    same box for box with and without the shuffle."""
    tr = busy_scene()
    out = {}
    for sh in (False, True):
        d, g, _ = observe(tr, profile("good"), 0.3, np.random.default_rng(7), {"shuffle": sh})
        res = idlib.run(d, g, dict(SPEC["harness"]["configs"]["full"]), 0.3)
        key = np.lexsort((d.src, d.frame))
        out[sh] = (d, {m: res[m].label[key] for m in ("live", "offline")})
    sorted_frames = [bool(np.all(np.diff(np.where(d.src[a:b] >= 0, d.src[a:b], 1000 - d.src[a:b])) > 0))
                     for d in (out[True][0],) for a, b in zip(d.fstart[:-1], d.fstart[1:]) if b - a > 3]
    assert np.mean(sorted_frames) < 0.2
    assert idlib.P["shuffle_box_order"] is True
    d_def, _, _ = observe(tr, profile("good"), 0.3, np.random.default_rng(7))
    assert np.array_equal(d_def.src, out[True][0].src)  # the default is shuffled
    for m in ("live", "offline"):
        assert np.array_equal(out[False][1][m], out[True][1][m]), m
        assert (out[True][1][m] >= 0).any()


def test_seeds_default_is_five_and_acc_h1_covers_every_seed():
    """RV-11: one seed is one draw. The harness runs harness.params.seeds seeds by default and ACC-H1 covers all of them."""
    assert idlib.P["seeds"] >= 5
    assert harness.build_parser().parse_args([]).seeds == idlib.P["seeds"]
    acc = {a["id"]: a for a in SPEC["acceptance"]}
    assert "seeds 1-5" in acc["ACC-H1"]["scope"] and "== 0" in acc["ACC-H1"]["threshold"]
    assert "hard" in acc["ACC-H3"]["scope"] and "seeds 1-5" in acc["ACC-H3"]["scope"]


def test_zero_swaps_is_reported_with_exposure_and_an_upper_bound():
    """RV-11: zero events is a bound, not a proof. Stored 0.1.1 run at sigma_p 0.30: 157 min, 8.94 labelled player-hours,
    5,116 crossings, 0 events -> at most 0.335 per labelled player-hour and 0.76 per 40-minute game at 95 %."""
    assert abs(metrics.poisson_upper(0, 0.95) - 2.9957) < 1e-3
    assert abs(metrics.poisson_upper(4, 0.95) - 9.1535) < 1e-3
    e = metrics.exposure(0, 157.0, 8.94, 5116, 20000, 3)
    assert abs(e["upper_per_labelled_player_hour"] - 0.3351) < 1e-3 and abs(e["upper_per_game"] - 0.7632) < 1e-3
    assert abs(e["upper_per_crossing"] - 5.86e-4) < 1e-5 and e["rate_per_game"] == 0 and e["game_runs"] == 3
    e = metrics.exposure(4, 785.0, 44.5, 25580, 80000, 15)
    assert abs(e["rate_per_game"] - 4 / 785.0 * 40) < 1e-5 and e["upper_per_game"] > 2 * e["rate_per_game"]


def test_hard_profile_switches_every_option_on_and_options_are_documented():
    h = SPEC["harness"]
    base, opt = set(h["cue_profiles"]["good"]), h["cue_profile_options"]
    for name, prof in h["cue_profiles"].items():
        assert set(prof) <= base | set(opt), (name, sorted(set(prof) - base - set(opt)))
        assert base - {"assigner_overrides"} <= set(prof), name
    for k, v in opt.items():
        assert set(v) >= {"default", "unit", "meaning", "basis"}, k
    hard = profile("hard")
    for k in ("team_burst_per_s", "p_trunc", "p_repeat", "p_misread_persist", "p_overlap_unflagged", "app_slow_noise", "bystanders_per_team",
              "pbp_late_share", "pbp_missing_share", "pbp_wrong_player_share"):
        assert hard[k] > 0 and opt[k]["default"] == 0, k
    assert hard["twin_delta"] is not None and hard["twin_pairs_per_team"] > 1 and hard["sigma_told_range"] != [1.0, 1.0]
    assert hard["e_team"] == idlib.P["e_team"] == 0.03  # the YAML's own planning value, three times the good profile's
    assert h["cannot_show"].strip() and 0.75 in h["noise_grid_sigma_p_m"]


def test_colour_errors_come_in_runs():
    """RV-14 / SOTA-02: with team_burst_per_s a player reads as the opponent for a run of frames, not for single frames."""
    d0, _, i0 = sim()
    assert not (d0.cls_obs[d0.src >= 0] != np.repeat([0, 1], 7)[d0.src[d0.src >= 0]]).any() and not i0["flags"]["colour_run"].any()
    d, _, info = sim(quiet_profile(team_burst_per_s=0.1, team_burst_len_s=[0.8, 1.2], team_burst_hit=1.0))
    fl = info["flags"]["colour_run"]
    team = np.repeat([0, 1], 7)
    assert fl.sum() > 50 and np.all(d.cls_obs[fl & ~d.nocue] == 1 - team[d.src[fl & ~d.nocue]])
    p = int(np.bincount(d.src[fl]).argmax())
    fr = np.sort(d.frame[fl & (d.src == p)])
    runs = np.split(fr, np.where(np.diff(fr) > 1)[0] + 1)
    assert np.mean([len(r) for r in runs]) >= 10  # 0.8-1.2 s at 25 Hz; independent flips would give runs of one frame


def test_truncated_and_persistent_jersey_misreads():
    """RV-15, RV-16 / SOTA-01, SOTA-03: a two-digit number read as a full one-digit number; a read outcome that repeats; a
    misread that is read the same wrong way at the next sighting."""
    tr = make_truth(60.0)
    rj = {"random_jersey": True}
    two = [p for p in range(14) if len(tr.jersey[p]) == 2 and not np.isnan(tr.pos[0, p, 0])]
    one = [p for p in range(14) if len(tr.jersey[p]) == 1 and not np.isnan(tr.pos[0, p, 0])]
    d, _, info = sim(quiet_profile(jersey_sightings_per_s=0.5, p_trunc=1.0), rj, truth=tr)
    for p in two:
        codes = set(d.jersey[(d.src == p) & (d.jersey >= 0)].tolist())
        assert codes and codes <= {idlib.jersey_code_full(c) for c in tr.jersey[p]}, (p, codes)
    for p in one:
        assert set(d.jersey[(d.src == p) & (d.jersey >= 0)].tolist()) <= {idlib.jersey_code_full(tr.jersey[p])}
    assert info["flags"]["jersey_trunc"].sum() == int(np.sum(np.isin(d.src, two) & (d.jersey >= 0)))
    # the same view resumed: about twice the sightings, every repeat equal to the read before it
    n = {}
    for rep in (0.0, 0.5):
        d, _, _ = sim(quiet_profile(jersey_sightings_per_s=0.3, p_repeat=rep), rj, truth=tr)
        n[rep] = sum(int(np.sum(np.diff(np.r_[-9, np.sort(d.frame[(d.src == p) & (d.jersey >= 0)])]) > 1)) for p in two + one)
    assert n[0.5] > 1.5 * n[0.0]
    # a misread persists: with certain misreads and certain persistence a player's reads are all one wrong number
    d, _, info = sim(quiet_profile(jersey_sightings_per_s=0.5, e_ocr=1.0, p_misread_persist=1.0, misread_persist_s=60.0), rj, truth=tr)
    for p in two + one:
        codes = d.jersey[(d.src == p) & (d.jersey >= 0)]
        assert len(set(codes.tolist())) == 1 and codes[0] != idlib.jersey_code_full(tr.jersey[p]), p
    d, _, _ = sim(quiet_profile(jersey_sightings_per_s=0.5, e_ocr=1.0), rj, truth=tr)
    assert max(len(set(d.jersey[(d.src == p) & (d.jersey >= 0)].tolist())) for p in two + one) > 1  # independent misreads differ


def test_unflagged_overlap_carries_the_near_players_cues():
    """RV-12 / leak L3: an overlapped box that is not flagged shows the near player's colour, number and appearance."""
    cam = np.array(idlib.P["camera_xy_m"])
    near = np.array([5.0, 12.8])
    far = cam + 1.09 * (near - cam)  # same line of sight, about 2 m behind
    tr = make_truth(8.0, paths={0: [(0, *near)], 7: [(0, *far)]})
    prm = dict(idlib.P, p_occl_drop=0.0)
    js = {"jersey_schedule": {0: [(2.0, 3.0, tr.jersey[0])]}}
    d0, g, i0 = sim(opts=js, truth=tr, prm=prm)
    m0 = d0.src == 7
    assert d0.nocue[m0].all() and (d0.cls_obs[m0] == -1).all() and not i0["flags"]["overlap_unflagged"].any()  # flagged: no cue at all
    d, g, info = sim(quiet_profile(p_overlap_unflagged=1.0), js, truth=tr, prm=prm)
    m = d.src == 7
    assert info["flags"]["overlap_unflagged"][m].all() and not d.nocue[m].any()
    assert (d.cls_obs[m] == 0).all()  # the opponent in front
    assert set(d.jersey[m & (d.frame >= 52) & (d.frame < 73)].tolist()) == {idlib.jersey_code_full(tr.jersey[0])}
    e = d.emb[m & ~np.isnan(d.emb[:, 0])]
    assert len(e) and np.all(e @ g.template[0] > e @ g.template[7])


def test_same_kit_non_player_is_in_view_and_not_on_the_roster():
    """RV-12 / leak L14: a person in team kit who is not a player. Any label on him is a swap."""
    d, g, info = sim(quiet_profile(bystanders_per_team=1, bystander_per_min=20.0, bystander_len_s=[3.0, 6.0]), truth=make_truth(60.0))
    by = d.src < 0  # QUIET has no officials
    assert info["n_officials"] == 0 and info["n_bystanders"] == 2 and by.sum() > 100
    assert set(d.cls_obs[by & ~d.nocue].tolist()) <= {0, 1} and (d.jersey[by] == -1).all() and g.n == 14
    assert np.all(d.xy[by, 1] > 14.0)
    lab = np.where(by, 3, -1)
    assert metrics.swap_mechanisms(d, lab, g.cand, g.team, info["flags"], DT, 0).get("same_kit_non_player", 0) >= 1
    assert metrics.identity_metrics(d, lab, info["in_fov"], DT)["swap_events"] >= 1
    d0, _, i0 = sim(truth=make_truth(60.0))
    assert not (d0.src < 0).any() and i0["n_bystanders"] == 0


@pytest.mark.parametrize("opt, expect", [({}, "ok"), ({"pbp_late_share": 1.0}, "late"), ({"pbp_missing_share": 1.0}, "never"),
                                         ({"pbp_wrong_player_share": 1.0}, "wrong")])
def test_lineup_rows_can_be_late_missing_or_wrong(opt, expect):
    """RV-12 / leak L7: player 5 comes on for player 4 at 20 s. A correct feed lists him throughout; a late row leaves
    him out of the candidates for seconds, a missing row for good, a wrong row lists another bench teammate instead."""
    tr = make_truth(70.0, off={5: [(0.0, 20.0)], 4: [(20.0, 71.0)]})
    d, g, info = sim(quiet_profile(**opt), {"pbp_lag": True}, truth=tr)
    f = lambda t: int(round(t / DT))  # noqa: E731
    assert info["pbp_rows"]["rows"] == 1
    if expect == "ok":
        assert g.cand[f(20.0):, 5].all() and g.cand[f(13.0), 5] and info["pbp_rows"] == {"rows": 1, "late": 0, "missing": 0, "wrong_player": 0}
    if expect == "late":
        assert not g.cand[f(20.0):f(21.9), 5].any() and g.cand[f(60.0), 5] and info["pbp_rows"]["late"] == 1
    if expect == "never":
        assert not g.cand[:, 5].any() and g.cand[:, 4].all() and info["pbp_rows"]["missing"] == 1
    if expect == "wrong":
        assert not g.cand[f(40.0):, 5].any() and g.cand[f(40.0):, 6].all() and info["pbp_rows"]["wrong_player"] == 1
    # the true player is on the floor but not a candidate: any label is wrong, and the mechanism says why
    if expect != "ok":
        lab = np.where((d.src == 5) & (d.frame == f(21.0)), 4, -1)
        assert metrics.swap_mechanisms(d, lab, g.cand, g.team, info["flags"], DT, 0) == {"lineup_wrong": 1}


def test_sigma_told_factor_and_graded_lookalikes():
    _, _, i0 = sim()
    assert i0["sigma_told_factor"] == 1.0
    fs = [sim(quiet_profile(sigma_told_range=[0.67, 1.5]), seed=s)[2]["sigma_told_factor"] for s in range(8)]
    assert all(0.67 <= x <= 1.5 for x in fs) and max(fs) - min(fs) > 0.1
    # look-alike pairs with a range of similarity: closer than ordinary teammates, not all equally close
    _, g, info = sim(quiet_profile(twin_pairs_per_team=3, twin_delta=[0.15, 0.6]), seed=11)
    assert len(info["twins"]) == 6
    cos = [float(g.template[a] @ g.template[b]) for a, b in info["twins"]]
    assert max(cos) - min(cos) > 0.02


def test_swap_mechanism_attribution():
    """A wrong-label run is attributed to the simulated error that touched the person just before it."""
    d, g, info = sim(opts={"class_schedule": {0: [(4.0, 5.0, 1)]}})
    fr = lambda t: int(round(t / DT))  # noqa: E731
    lab = np.where((d.src == 0) & (d.frame >= fr(5.0)) & (d.frame < fr(5.5)), 8, -1)
    assert metrics.swap_mechanisms(d, lab, g.cand, g.team, info["flags"], DT, 0) == {"colour_run": 1, "cross_team": 1}
    lab = np.where((d.src == 0) & (d.frame >= fr(15.0)) & (d.frame < fr(15.5)), 1, -1)
    assert metrics.swap_mechanisms(d, lab, g.cand, g.team, info["flags"], DT, 0) == {"other": 1}
    assert set(info["flags"]) == set(FLAG_KEYS)


def test_cue_stats_are_in_literature_units():
    """RV-17 / RV-18: what a profile assumes, comparable with measurements: legible-frame share, sightings per visible
    second, windows without a read, single-crop rank-1 among on-court teammates."""
    tr = make_truth(60.0)
    d, g, info = observe(tr, profile("good"), 0.2, np.random.default_rng(2))
    cs = metrics.cue_stats(d, g, info, ~np.isnan(tr.pos[:, :, 0]))
    assert 0.03 < cs["legible_frame_share"] < 0.25 and 0.2 < cs["sightings_per_visible_s"] < 0.7
    assert 0.0 <= cs["no_read_window_share"] < 0.4 and 0.75 < cs["app_rank1_teammates"] <= 1.0
    lit = metrics.cue_stats(*observe(tr, profile("lit_jersey"), 0.2, np.random.default_rng(2))[:3], ~np.isnan(tr.pos[:, :, 0]))
    msk = metrics.cue_stats(*observe(tr, profile("masked_app"), 0.2, np.random.default_rng(2))[:3], ~np.isnan(tr.pos[:, :, 0]))
    assert lit["sightings_per_visible_s"] < 0.5 * cs["sightings_per_visible_s"] and lit["no_read_window_share"] > cs["no_read_window_share"]
    assert msk["app_rank1_teammates"] < cs["app_rank1_teammates"] - 0.05


def test_results_carry_spec_version_and_hashes():
    """RV-20: every run says which spec made it; the behaviour hash ignores prose (notes) and follows every parameter."""
    h = harness.spec_hashes()
    assert set(h) == {"yaml_sha256", "params_sha256"} and all(len(v) == 64 for v in h.values())
    old = idlib.P["p_lock"]
    try:
        idlib.P["p_lock"] = old - 0.001
        assert harness.spec_hashes()["params_sha256"] != h["params_sha256"]
    finally:
        idlib.P["p_lock"] = old
    assert harness.spec_hashes() == h
    src = (ROOT / "tools" / "specgen" / "identity" / "harness.py").read_text()
    assert '"spec_version": idlib.SPEC["version"]' in src and "**hashes" in src
