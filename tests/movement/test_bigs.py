"""Tests for the bigs movement family (config/movement_grammar/bigs.yaml,
tools/specgen/movement/detectors/bigs.py), validation tier V0 (synthetic, sim.scenario).

Every detector gets at least one positive and one negative scenario at sigma_p = 0.3 m with fixed
seeds. Positives check kind, actors, t0 within +-0.3 s of the scenario truth and conf in (0, 1].
Scenario truth t0 is computed from the noise-free paths with the item's own t0 definition.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "movement"))
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "movement" / "detectors"))
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "named_spots"))

import bigs  # noqa: E402
import mvlib as M  # noqa: E402
import sim  # noqa: E402
from mvlib import DT, Event  # noqa: E402

SIGMA = 0.3
TOL = int(round(0.3 / DT))  # +-0.3 s in frames
SEEDS = (1, 2)


# --------------------------------------------------------------------------------------
# Scenario helpers
# --------------------------------------------------------------------------------------
def fr(t):
    return int(round(t / DT))


def build(spec, dur, seed, sigma=SIGMA, extra_tracks=()):
    """Simulate; a pseudo actor 'rim' (team X) is only a ball-flight target and is dropped."""
    truth, tracks = sim.scenario(spec, dur, sigma, seed)
    tracks = [t for t in tracks if t.oid != "rim"] + list(extra_tracks)
    return truth, M.build_scene(tracks)


def screen_ev(truth, s, h, lo_s, hi_s, cls="ball", **attrs):
    """Input screen event per the contract: t0 = minimum true screener-user distance in [lo, hi]."""
    a, b = fr(lo_s), fr(hi_s)
    d = np.hypot(truth[s][0][a:b + 1] - truth[h][0][a:b + 1], truth[s][1][a:b + 1] - truth[h][1][a:b + 1])
    t0 = a + int(np.argmin(d))
    return Event("screen", {"screener": s, "user": h}, t0, max(0, t0 - 15), t0 + 15, 1.0, dict(screen_class=cls, **attrs))


def truth_speed(truth, aid):
    x, y = truth[aid]
    return np.hypot(np.gradient(x, DT), np.gradient(y, DT))


def truth_v_r(truth, aid):
    x, y = truth[aid]
    r = np.hypot(x, y)
    return -np.gradient(r, DT)


def first_after(mask, t_from_s):
    idx = np.flatnonzero(mask[fr(t_from_s):])
    return fr(t_from_s) + int(idx[0]) if len(idx) else None


def last_slow_before(truth, aid, t_s, v=0.3):
    """Departure frame: last frame <= t_s where the true speed is below v (start of a move)."""
    sp = truth_speed(truth, aid)
    t = fr(t_s)
    while t > 0 and sp[t] >= v:
        t -= 1
    return t


def check(evs, kind, actors, t0, lo=0.0, hi=1.0):
    """Exactly-one-match assertion helper: returns the matching event."""
    m = [e for e in evs if e.kind == kind and all(e.actors.get(k) == v for k, v in actors.items())]
    assert m, f"no {kind} for {actors}; got {[(e.kind, e.actors, e.t0) for e in evs]}"
    e = min(m, key=lambda e: abs(e.t0 - t0))
    assert abs(e.t0 - t0) <= TOL, f"{kind} t0 {e.t0} vs truth {t0} (+-{TOL})"
    assert lo < e.conf <= hi, f"{kind} conf {e.conf}"
    return e


# Handler path for a top ball screen: comes from the left, passes ~1.2 m above the screen at ~1.9 s
H_TOP = [(0.0, -5.0, 9.0), (0.5, -4.0, 8.5), (2.6, 2.0, 6.2)]
S_SET = (0.8, 8.0)  # top screen spot, r 8.04 m


def spec_top(s_wp, h_wp=None, extra=None, ball=True, h_hold_to=None):
    actors = {"s": {"team": "O", "wp": s_wp}, "h": {"team": "O", "wp": h_wp or H_TOP}}
    actors.update(extra or {})
    spec = {"actors": actors}
    if ball:
        spec["ball"] = {"held": [(0.0, h_hold_to or 99.0, "h")], "flights": []}
    return spec


ROLL_WP = [(0.0, 2.5, 9.5), (1.0, *S_SET), (2.2, *S_SET), (4.2, 0.3, 1.0)]
POP_TOP_HOLD_WP = [(0.0, 2.5, 9.5), (1.0, *S_SET)]  # screener holds at the top all clip
LATE_DRIFT_WP = [(0.0, 2.5, 9.5), (1.0, *S_SET), (3.6, *S_SET), (6.6, 0.5, 4.5)]  # holds, then walks in at ~1.2 m/s


def roll_scene(seed, extra=None, s_wp=None, dur=5.5):
    truth, sc = build(spec_top(s_wp or ROLL_WP, extra=extra), dur, seed)
    return truth, sc, screen_ev(truth, "s", "h", 1.0, 3.0)


# --------------------------------------------------------------------------------------
# Parameters and registry
# --------------------------------------------------------------------------------------
def test_yaml_is_single_source_and_items_complete():
    doc = bigs.DOC
    assert doc["family"] == "bigs" and doc["version"] == "0.3.1" and str(doc["date"]) == "2026-10-25"
    req = {"id", "level", "name", "aliases", "actors", "t0", "rule", "params", "min_duration_s", "outputs", "confidence",
           "noise", "conflicts_resolved", "sources", "status"}
    for it in doc["items"]:
        assert req <= set(it), (it["id"], req - set(it))
        assert it["level"] in ("primitive", "action", "set_component", "rule")
        assert it["status"] in ("canonical", "proposal")
        for k, v in (it["params"] or {}).items():
            assert isinstance(v, dict) and "value" in v and "unit" in v, (it["id"], k)
        if it.get("detector"):
            assert it["detector"] == f"detect_{it['id']}" and it["id"] in bigs.DETECTORS
    assert bigs.params("roll")["v_r_gate_mps"] == bigs.ITEMS["roll"]["v_r_gate_mps"]


@pytest.mark.parametrize("item", [it["id"] for it in bigs.DOC["items"] if it.get("needs_data")])
def test_needs_data_items_return_empty(item):
    truth, sc, ev = roll_scene(1)
    assert bigs.DETECTORS[item](sc, screens=[ev]) == []


# --------------------------------------------------------------------------------------
# Screen frame primitives
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("seed", SEEDS)
def test_screen_frame(seed):
    truth, sc, ev = roll_scene(seed)
    e = check(bigs.detect_screen_frame(sc, screens=[ev]), "screen_frame", {"screener": "s", "user": "h"}, ev.t0)
    assert e.attrs["release_timing"] == "post_use" and e.attrs["first_move"] == "rimward"
    bad = Event("screen", {"screener": "zz", "user": "h"}, ev.t0, ev.start, ev.end, 1.0, {"screen_class": "ball"})
    assert bigs.detect_screen_frame(sc, screens=[bad]) == []


# L4-8: the loop-0 path ran straight past h ((3.0, 5.0) -> (-3.5, 8.5)); a ghost turns at the fake set (a straight run
# past the handler is a cut: test_l4_8_ghost_straight_run_past_is_a_cut keeps that path as a negative)
GHOST_S_STRAIGHT = [(0.0, 3.6, 4.6), (0.5, 3.0, 5.0), (3.0, -3.5, 8.5)]
GHOST_S = [(0.0, 3.6, 4.6), (0.5, 3.0, 5.0), (1.7, 0.6, 7.0), (3.2, -4.0, 6.5)]
GHOST_H = [(0.0, -0.3, 7.8)]


def ghost_scene(seed, s_wp=None):
    spec = {"actors": {"s": {"team": "O", "wp": s_wp or GHOST_S}, "h": {"team": "O", "wp": GHOST_H}},
            "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}
    truth, sc = build(spec, 4.5, seed)
    return truth, sc, screen_ev(truth, "s", "h", 0.6, 3.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_screener_set_state(seed):
    truth, sc, ev = roll_scene(seed)
    check(bigs.detect_screener_set_state(sc, screens=[ev]), "screen_set", {"screener": "s"}, fr(1.0))
    truth, sc, ev = ghost_scene(seed)
    assert bigs.detect_screener_set_state(sc, screens=[ev]) == []


@pytest.mark.parametrize("seed", SEEDS)
def test_behind_def(seed):
    hedge = {"ds": {"team": "D", "wp": [(0.0, 1.0, 7.0), (1.0, 0.6, 7.2), (3.0, 1.6, 6.8)]}}
    truth, sc, ev = roll_scene(seed, extra=hedge)
    t_rel = last_slow_before(truth, "s", 2.6)
    e = check(bigs.detect_behind_def(sc, screens=[ev]), "behind_def", {"roller": "s", "screener_defender": "ds"}, t_rel)
    assert e.attrs["first_behind_frame"] >= e.t0
    drop = {"ds": {"team": "D", "wp": [(0.0, 1.0, 7.0), (1.0, 0.6, 7.2), (2.0, 0.2, 0.8)]}}  # retreats ahead of the roll
    truth, sc, ev = roll_scene(seed, extra=drop)
    assert bigs.detect_behind_def(sc, screens=[ev]) == []


def post_scene(seed, d_xy, dur=3.5):
    spec = {"actors": {"o": {"team": "O", "wp": [(0.0, 3.5, 3.2), (1.0, 2.0, 1.2)]}, "w": {"team": "O", "wp": [(0.0, 6.0, 3.0)]},
                       "d": {"team": "D", "wp": [(0.0, 2.8, 3.4), (1.0, *d_xy)]}},
            "ball": {"held": [(0.0, 99.0, "w")], "flights": []}}
    return build(spec, dur, seed)


@pytest.mark.parametrize("seed", SEEDS)
def test_post_seal(seed):
    truth, sc = post_scene(seed, (1.27, 0.87))  # defender behind, away from the ball
    e = check(bigs.detect_post_seal(sc), "post_seal", {"post": "o", "defender": "d"}, fr(1.0))
    assert e.attrs["seal_type"] == "behind"
    truth, sc = post_scene(seed, (2.73, 1.53))  # fronting: between the post and the ball
    assert [e for e in bigs.detect_post_seal(sc) if e.actors["post"] == "o"] == []


@pytest.mark.parametrize("seed", SEEDS)
def test_id_swap_risk(seed):
    spec = {"actors": {"o": {"team": "O", "wp": [(0.0, 2.0, 2.0)]},
                       "d": {"team": "D", "wp": [(0.0, 3.5, 2.5), (1.0, 2.1, 2.0), (2.0, 2.1, 2.0), (2.6, 3.5, 2.5)]}}}
    truth, sc = build(spec, 3.0, seed)
    dd = np.hypot(truth["o"][0] - truth["d"][0], truth["o"][1] - truth["d"][1])
    check(bigs.detect_id_swap_risk(sc), "id_swap_risk", {"attacker": "o", "defender": "d"}, first_after(dd < 0.6, 0.0))
    spec["actors"]["d"]["wp"] = [(0.0, 3.5, 2.5)]
    truth, sc = build(spec, 3.0, seed)
    assert bigs.detect_id_swap_risk(sc) == []


def lob_scene(seed, b_wp):
    spec = {"actors": {"a": {"team": "O", "wp": [(0.0, -3.0, 7.0)]}, "b": {"team": "O", "wp": b_wp}},
            "ball": {"held": [(0.0, 1.8, "a"), (2.4, 99.0, "b")], "flights": [(1.8, 2.4, "a", "b")]}}
    return build(spec, 3.5, seed)


@pytest.mark.parametrize("seed", SEEDS)
def test_lob_catch_proxy(seed):
    truth, sc = lob_scene(seed, [(0.0, 2.0, 7.5), (1.2, 2.0, 7.5), (2.8, 0.1, 0.2)])
    c = fr(2.4)
    check(bigs.detect_lob_catch_proxy(sc), "lob_catch_proxy", {"passer": "a", "receiver": "b"}, c)
    truth, sc = lob_scene(seed, [(0.0, 0.6, 0.8)])  # standing under the rim
    assert bigs.detect_lob_catch_proxy(sc) == []


# --------------------------------------------------------------------------------------
# Screener post-actions
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("seed", SEEDS)
def test_roll(seed):
    truth, sc, ev = roll_scene(seed)
    e = check(bigs.detect_roll(sc, screens=[ev]), "roll", {"screener": "s", "handler": "h"}, ev.t0)
    assert e.attrs["completion"] == "rim"
    truth, sc, ev = roll_scene(seed, s_wp=LATE_DRIFT_WP, dur=7.0)  # hold then late drift into the paint
    assert bigs.detect_roll(sc, screens=[ev]) == []


SHORT_WP = [(0.0, 2.5, 9.5), (1.0, *S_SET), (2.2, *S_SET), (3.4, 0.4, 4.5)]


@pytest.mark.parametrize("seed", SEEDS)
def test_short_roll(seed):
    truth, sc, ev = roll_scene(seed, s_wp=SHORT_WP)
    e = check(bigs.detect_short_roll(sc, screens=[ev]), "short_roll", {"screener": "s", "handler": "h"}, ev.t0)
    assert e.attrs["variant"] == "stop" and e.attrs["in_short_roll_zone"]
    assert bigs.detect_roll(sc, screens=[ev]) == []  # the stop in the pocket excludes a roll
    truth, sc, ev = roll_scene(seed)  # full roll: not a short roll
    assert bigs.detect_short_roll(sc, screens=[ev]) == []


# Elbow ball screen: handler comes down from the slot, screen at the right elbow (r 4.83)
H_ELBOW = [(0.0, -1.5, 8.0), (0.5, -1.0, 7.5), (2.6, 3.8, 3.2)]
ELBOW_SET = (2.2, 4.3)


def elbow_scene(seed, s_wp, dur=5.0):
    truth, sc = build(spec_top(s_wp, h_wp=H_ELBOW), dur, seed)
    return truth, sc, screen_ev(truth, "s", "h", 1.0, 3.0)


POP_ELBOW_WP = [(0.0, 3.5, 6.5), (1.0, *ELBOW_SET), (2.2, *ELBOW_SET), (3.8, 4.5, 6.3)]


@pytest.mark.parametrize("seed", SEEDS)
def test_pop_arc(seed):
    truth, sc, ev = elbow_scene(seed, POP_ELBOW_WP)
    e = check(bigs.detect_pop_arc(sc, screens=[ev]), "pop_arc", {"screener": "s", "handler": "h"}, ev.t0)
    assert e.attrs["r_end"] >= 6.6
    # E7 regression: top screener who only holds while the handler drives away is NOT a pop
    truth, sc, ev = roll_scene(seed, s_wp=POP_TOP_HOLD_WP)
    assert bigs.detect_pop_arc(sc, screens=[ev]) == []


LOW_SET = (2.6, 2.6)
H_LOW = [(0.0, 6.0, 6.0), (0.5, 5.5, 5.0), (2.6, 0.5, 1.5)]
POP_MID_WP = [(0.0, 3.5, 1.0), (1.0, *LOW_SET), (2.2, *LOW_SET), (3.3, 4.0, 4.2)]
ROLL_LOW_WP = [(0.0, 3.5, 1.0), (1.0, *LOW_SET), (2.2, *LOW_SET), (3.0, 0.4, 0.8)]


def low_scene(seed, s_wp, dur=5.0):
    truth, sc = build(spec_top(s_wp, h_wp=H_LOW), dur, seed)
    return truth, sc, screen_ev(truth, "s", "h", 1.0, 3.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_pop_mid(seed):
    truth, sc, ev = low_scene(seed, POP_MID_WP)
    e = check(bigs.detect_pop_mid(sc, screens=[ev]), "pop_mid", {"screener": "s", "handler": "h"}, ev.t0)
    assert e.attrs["variant"] == "stop"
    truth, sc, ev = low_scene(seed, ROLL_LOW_WP)
    assert bigs.detect_pop_mid(sc, screens=[ev]) == []


SLIP_WP = [(0.0, 2.5, 9.5), (1.0, *S_SET), (1.2, *S_SET), (3.0, 0.3, 1.0)]


@pytest.mark.parametrize("seed", SEEDS)
def test_slip(seed):
    truth, sc, ev = roll_scene(seed, s_wp=SLIP_WP)
    t_rel = last_slow_before(truth, "s", 1.6)
    e = check(bigs.detect_slip(sc, screens=[ev]), "slip", {"screener": "s", "handler": "h"}, t_rel)
    assert e.attrs["destination"] == "rim" and e.attrs["release_timing"] in ("early", "never_set")
    truth, sc, ev = roll_scene(seed)  # rolls after use: not a slip
    assert bigs.detect_slip(sc, screens=[ev]) == []


SLIP_ARC_WP = [(0.0, 3.5, 6.5), (1.0, *ELBOW_SET), (1.2, *ELBOW_SET), (2.6, 4.6, 6.4)]


@pytest.mark.parametrize("seed", SEEDS)
def test_slip_to_arc(seed):
    truth, sc, ev = elbow_scene(seed, SLIP_ARC_WP)
    t_rel = last_slow_before(truth, "s", 1.6)
    check(bigs.detect_slip_to_arc(sc, screens=[ev]), "slip_to_arc", {"screener": "s", "handler": "h"}, t_rel)
    truth, sc, ev = elbow_scene(seed, POP_ELBOW_WP)  # pops after use: pop_arc, not slip_to_arc
    assert bigs.detect_slip_to_arc(sc, screens=[ev]) == []


@pytest.mark.parametrize("seed", SEEDS)
def test_ghost(seed):
    truth, sc, ev = ghost_scene(seed)
    e = check(bigs.detect_ghost(sc), "ghost", {"screener": "s", "handler": "h"}, ev.t0)
    assert e.attrs["subtype"] == "out"
    set_wp = [(0.0, 3.6, 4.6), (0.5, 3.0, 5.0), (1.6, 0.5, 6.9), (2.8, 0.5, 6.9), (4.0, -3.5, 8.5)]  # stops: a real screen
    truth, sc, ev = ghost_scene(seed, set_wp)
    assert [e for e in bigs.detect_ghost(sc) if e.actors["screener"] == "s"] == []


SEAL_WP = [(0.0, 2.5, 9.5), (1.0, *S_SET), (2.3, *S_SET), (3.8, 0.9, 2.6)]
SEAL_H = [(0.0, -5.0, 9.0), (0.5, -4.0, 8.5), (2.6, 2.0, 6.2), (4.6, 1.6, 1.4)]


def seal_scene(seed, d_wp):
    extra = {"ds": {"team": "D", "wp": d_wp}}
    truth, sc = build(spec_top(SEAL_WP, h_wp=SEAL_H, extra=extra), 6.0, seed)
    return truth, sc, screen_ev(truth, "s", "h", 1.0, 2.4)


@pytest.mark.parametrize("seed", SEEDS)
def test_seal(seed):
    truth, sc, ev = seal_scene(seed, [(0.0, 0.5, 6.5), (1.5, 0.5, 6.5), (3.4, 0.0, 2.2)])
    arrive = first_after(truth_speed(truth, "s") < 0.3, 3.0)
    check(bigs.detect_seal(sc, screens=[ev]), "seal", {"screener": "s", "defender": "ds", "beneficiary": "h"}, arrive)
    truth, sc, ev = seal_scene(seed, [(0.0, -3.0, 5.0)])  # defender far away: no seal
    assert bigs.detect_seal(sc, screens=[ev]) == []


def crash_scene(seed, s_wp):
    spec = {"actors": {"s": {"team": "O", "wp": s_wp}, "h": {"team": "O", "wp": H_TOP + [(3.0, 2.0, 6.2)]},
                       "rim": {"team": "X", "wp": [(0.0, 0.0, 0.0)]}},
            "ball": {"held": [(0.0, 3.0, "h")], "flights": [(3.0, 3.9, "h", "rim")]}}
    truth, sc = build(spec, 5.5, seed)
    return truth, sc, screen_ev(truth, "s", "h", 1.0, 2.8)


@pytest.mark.parametrize("seed", SEEDS)
def test_crash(seed):
    truth, sc, ev = crash_scene(seed, [(0.0, 2.5, 9.5), (1.0, *S_SET), (3.1, *S_SET), (4.6, 0.6, 1.6)])
    rel = fr(3.0)  # FGA release = end of the shooter's hold
    e = check(bigs.detect_crash(sc, screens=[ev]), "crash", {"screener": "s", "shooter": "h"}, rel)
    assert e.attrs["fga_source"] == "ball_xy_proxy"
    truth, sc, ev = crash_scene(seed, [(0.0, 2.5, 9.5), (1.0, *S_SET)])
    assert bigs.detect_crash(sc, screens=[ev]) == []


def rescreen_scene(seed):
    s_wp = [(0.0, 2.5, 9.5), (1.0, *S_SET), (2.2, *S_SET), (3.1, -2.2, 7.6)]
    h_wp = H_TOP + [(3.4, 2.0, 6.2), (4.6, -4.0, 7.3)]
    truth, sc = build(spec_top(s_wp, h_wp=h_wp), 5.5, seed)
    return truth, sc, screen_ev(truth, "s", "h", 1.0, 3.0), screen_ev(truth, "s", "h", 3.5, 5.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_move_to_screen(seed):
    truth, sc, e1, e2 = rescreen_scene(seed)
    e = check(bigs.detect_move_to_screen(sc, screens=[e1, e2]), "move_to_screen", {"screener": "s"}, e2.t0)
    assert e.attrs["subtype"] in ("re_screen", "twist")
    late = Event("screen", e2.actors, e2.t0 + fr(3.0), e2.start, e2.end, 1.0, dict(e2.attrs))
    truth, sc, e1, _ = rescreen_scene(seed)
    assert bigs.detect_move_to_screen(sc, screens=[e1, late]) == []


RIP_WP = [(0.0, 2.5, 9.5), (1.0, *S_SET), (2.2, *S_SET), (3.7, 2.0, 1.4)]


def rip_scene(seed, d_wp):
    extra = {"ds": {"team": "D", "wp": d_wp}}
    truth, sc = build(spec_top(RIP_WP, h_wp=H_TOP + [(3.0, 5.5, 3.5)], extra=extra), 6.0, seed)
    return truth, sc, screen_ev(truth, "s", "h", 1.0, 3.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_roll_into_post(seed):
    # defender trails the roll and ends behind the post, away from the ball (handler on the wing)
    truth, sc, ev = rip_scene(seed, [(0.0, 0.5, 7.0), (2.2, 0.5, 7.0), (4.0, 1.2, 1.1)])
    arrive = first_after(truth_speed(truth, "s") < 0.3, 3.0)
    e = check(bigs.detect_roll_into_post(sc, screens=[ev]), "roll_into_post", {"screener": "s", "defender": "ds"}, arrive)
    assert e.attrs["subtype"] == "deep_post"
    truth, sc, ev = rip_scene(seed, [(0.0, -3.0, 6.0)])
    assert bigs.detect_roll_into_post(sc, screens=[ev]) == []


def spain_scene(seed, s2_wp):
    spec = {"actors": {"s2": {"team": "O", "wp": s2_wp}, "r": {"team": "O", "wp": [(0.0, 0.8, 8.0), (2.0, 0.8, 8.0), (3.5, 0.3, 1.0)]}},
            "ball": {"held": [], "flights": []}}
    truth, sc = build(spec, 5.0, seed)
    ev = screen_ev(truth, "s2", "r", 1.5, 3.2, cls="off_ball", screen_type="spain")
    return truth, sc, ev


@pytest.mark.parametrize("seed", SEEDS)
def test_spain_pop(seed):
    truth, sc, ev = spain_scene(seed, [(0.0, 0.3, 2.5), (1.0, 0.3, 5.0), (2.4, 0.3, 5.0), (3.8, 0.6, 7.5)])
    check(bigs.detect_spain_pop(sc, screens=[ev]), "spain_pop", {"screener": "s2", "user": "r"}, ev.t0)
    truth, sc, ev = spain_scene(seed, [(0.0, 0.3, 2.5), (1.0, 0.3, 5.0)])
    assert bigs.detect_spain_pop(sc, screens=[ev]) == []


# --------------------------------------------------------------------------------------
# Big-man actions not tied to one screen
# --------------------------------------------------------------------------------------
def dho_scene(seed):
    spec = {"actors": {"b": {"team": "O", "wp": [(0.0, 2.0, 7.0), (1.6, 2.0, 7.0), (3.4, 0.3, 1.0)]},
                       "h": {"team": "O", "wp": [(0.0, 5.5, 6.0), (0.4, 5.0, 6.5), (1.5, 2.6, 7.6), (2.6, -1.5, 8.0)]}},
            "ball": {"held": [(0.0, 1.45, "b"), (1.45, 99.0, "h")], "flights": []}}
    truth, sc = build(spec, 4.5, seed)
    return truth, sc, screen_ev(truth, "b", "h", 1.0, 2.0, cls="dho")


@pytest.mark.parametrize("seed", SEEDS)
def test_dive(seed):
    truth, sc, ev = dho_scene(seed)
    onset = first_after(truth_v_r(truth, "b") >= 1.0, 1.6)
    e = check(bigs.detect_dive(sc, screens=[ev]), "dive", {"big": "b"}, onset)
    assert e.attrs["subtype"] == "dho_dive"
    assert bigs.detect_dive(sc, screens=[]) == []  # same path without a context event is a CUT


def cruise_track(oid, team, pts, v, seed, ramp_s=0.8, dur=7.0):
    """Polyline at constant speed v with linear speed ramps (sim waypoints always stop)."""
    rng = np.random.default_rng(seed + 100)
    n = int(round(dur / DT)) + 1
    seg = np.diff(np.array(pts), axis=0)
    L = np.concatenate([[0], np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))])
    s, sp, out = 0.0, 0.0, []
    acc = v / ramp_s
    for _ in range(n):
        left = L[-1] - s
        sp = min(v, sp + acc * DT, math.sqrt(max(0.0, 2 * acc * left)))
        s = min(L[-1], s + sp * DT)
        i = min(np.searchsorted(L, s, side="right") - 1, len(seg) - 1)
        u = (s - L[i]) / max(L[i + 1] - L[i], 1e-9)
        out.append(np.array(pts[i]) + u * seg[i])
    out = np.array(out)
    return out[:, 0], out[:, 1], sim.observe(out[:, 0], out[:, 1], SIGMA, rng, oid=oid, team=team)


@pytest.mark.parametrize("seed", SEEDS)
def test_rim_run(seed):
    x, y, tr = cruise_track("b", "O", [(0.6, 24.5), (0.8, 12.0), (0.4, 1.0)], 5.4, seed)
    sc = M.build_scene([tr])
    dep = int(np.flatnonzero(np.hypot(x, y - bigs.OWN_RIM_Y) <= 4.0)[-1])  # last frame within 4 m of the own rim
    e = check(bigs.detect_rim_run(sc), "rim_run", {"big": "b"}, dep)
    assert e.attrs["v_peak_source"] == "prior"
    x, y, tr = cruise_track("b", "O", [(0.6, 24.5), (0.8, 12.0), (0.4, 1.0)], 3.4, seed, dur=9.0)  # jog
    assert bigs.detect_rim_run(M.build_scene([tr])) == []


def dunker_scene(seed, k_wp):
    spec = {"actors": {"k": {"team": "O", "wp": k_wp},
                       "q": {"team": "O", "wp": [(0.0, 4.0, 8.0), (0.8, 3.5, 7.0), (2.6, 0.9, 2.6)]}},
            "ball": {"held": [(0.0, 99.0, "q")], "flights": []}}
    truth, sc = build(spec, 4.5, seed)
    q = truth["q"]
    inp = (np.abs(q[0]) <= 1.8288) & (q[1] <= 4.191)
    return truth, sc, first_after(inp, 0.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_dunker_relocation(seed):
    truth, sc, trig = dunker_scene(seed, [(0.0, -2.6, -0.2), (1.9, -2.6, -0.2), (3.3, 2.4, -0.1)])
    e = check(bigs.detect_dunker_relocation(sc), "dunker_relocation", {"dunker": "k", "trigger": "q"}, trig)
    assert e.attrs["subtype"] == "slide"
    truth, sc, trig = dunker_scene(seed, [(0.0, -2.6, -0.2)])
    assert bigs.detect_dunker_relocation(sc) == []


def duck_scene(seed, o_wp):
    spec = {"actors": {"o": {"team": "O", "wp": o_wp}, "w": {"team": "O", "wp": [(0.0, 6.0, 3.5)]},
                       "t": {"team": "O", "wp": [(0.0, 0.0, 8.0)]},
                       "d": {"team": "D", "wp": [(0.0, 2.3, 0.5), (2.2, 2.3, 0.5), (3.0, 0.7, 0.5)]}},
            "ball": {"held": [(0.0, 2.0, "w"), (2.5, 99.0, "t")], "flights": [(2.0, 2.5, "w", "t")]}}
    truth, sc = build(spec, 4.5, seed)
    bx = truth["ball"][0]
    return truth, sc, first_after(np.nan_to_num(np.abs(bx), nan=9) < 2.0, 1.5)


@pytest.mark.parametrize("seed", SEEDS)
def test_duck_in(seed):
    truth, sc, trig = duck_scene(seed, [(0.0, 2.0, 1.1), (2.2, 2.0, 1.1), (3.0, 0.6, 1.3)])
    check(bigs.detect_duck_in(sc), "duck_in", {"post": "o"}, trig)
    truth, sc, trig = duck_scene(seed, [(0.0, 2.0, 1.1)])
    assert bigs.detect_duck_in(sc) == []


def pass_scene(seed, a_xy, b_xy):
    spec = {"actors": {"a": {"team": "O", "wp": [(0.0, *a_xy)]}, "b": {"team": "O", "wp": [(0.0, *b_xy)]}},
            "ball": {"held": [(0.0, 1.5, "a"), (1.9, 99.0, "b")], "flights": [(1.5, 1.9, "a", "b")]}}
    return build(spec, 3.0, seed)


@pytest.mark.parametrize("seed", SEEDS)
def test_high_low(seed):
    truth, sc = pass_scene(seed, (0.5, 4.5), (1.9, 1.2))
    check(bigs.detect_high_low(sc), "high_low", {"passer": "a", "receiver": "b"}, fr(1.5))
    truth, sc = pass_scene(seed, (0.0, 8.0), (6.0, 3.0))
    assert bigs.detect_high_low(sc) == []


def srp_scene(seed, catch=True):
    extra = {"c": {"team": "O", "wp": [(0.0, 7.0, 0.5)]}}
    spec = spec_top(SHORT_WP, extra=extra)
    spec["ball"] = ({"held": [(0.0, 3.3, "h"), (3.7, 4.3, "s"), (4.6, 99.0, "c")], "flights": [(3.3, 3.7, "h", "s"), (4.3, 4.6, "s", "c")]}
                    if catch else {"held": [(0.0, 99.0, "h")], "flights": []})
    truth, sc = build(spec, 5.5, seed)
    return truth, sc, screen_ev(truth, "s", "h", 1.0, 3.0)


@pytest.mark.parametrize("seed", SEEDS)
def test_short_roll_playmaking(seed):
    truth, sc, ev = srp_scene(seed)
    e = check(bigs.detect_short_roll_playmaking(sc, screens=[ev]), "short_roll_playmaking", {"roller": "s", "handler": "h"}, fr(3.7))
    assert e.attrs["decision"] == "kick" and e.actors["receiver"] == "c"
    truth, sc, ev = srp_scene(seed, catch=False)
    assert bigs.detect_short_roll_playmaking(sc, screens=[ev]) == []


LIFT = {"p": {"team": "O", "wp": [(0.0, -2.6, 0.2), (2.4, -2.6, 0.2), (4.0, -5.4, 5.6)]}}
SPACERS = {"c1": {"team": "O", "wp": [(0.0, 6.9, 0.4)]}, "c2": {"team": "O", "wp": [(0.0, 6.0, 5.0)]}}


@pytest.mark.parametrize("seed", SEEDS)
def test_replace(seed):
    truth, sc, ev = roll_scene(seed, extra=LIFT)
    rs = bigs.detect_roll(sc, screens=[ev])[0].attrs["roll_start_frame"]
    e = check(bigs.detect_replace(sc, screens=[ev]), "replace", {"replacer": "p", "roller": "s"}, rs)
    assert e.attrs["subtype"] == "lift_from_dunker"
    truth, sc, ev = roll_scene(seed, extra={"p": {"team": "O", "wp": [(0.0, -2.6, 0.2)]}})
    assert bigs.detect_replace(sc, screens=[ev]) == []


@pytest.mark.parametrize("seed", SEEDS)
def test_roll_and_replace(seed):
    truth, sc, ev = roll_scene(seed, extra={**LIFT, **SPACERS})
    check(bigs.detect_roll_and_replace(sc, screens=[ev]), "roll_and_replace", {"roller": "s", "replacer": "p"}, ev.t0)
    truth, sc, ev = roll_scene(seed, extra=SPACERS)
    assert bigs.detect_roll_and_replace(sc, screens=[ev]) == []


def orb_scene(seed, b_wp):
    spec = {"actors": {"h": {"team": "O", "wp": [(0.0, 3.5, 5.5)]}, "b": {"team": "O", "wp": b_wp},
                       "rim": {"team": "X", "wp": [(0.0, 0.0, 0.0)]}},
            "ball": {"held": [(0.0, 1.5, "h")], "flights": [(1.5, 2.4, "h", "rim")]}}
    return build(spec, 4.0, seed)


@pytest.mark.parametrize("seed", SEEDS)
def test_offensive_rebound_crash(seed):
    truth, sc = orb_scene(seed, [(0.0, -5.0, 4.0), (1.6, -5.0, 4.0), (3.0, -1.0, 1.5)])
    check(bigs.detect_offensive_rebound_crash(sc), "offensive_rebound_crash", {"crasher": "b", "shooter": "h"}, fr(1.5))
    truth, sc = orb_scene(seed, [(0.0, -5.0, 4.0)])
    assert bigs.detect_offensive_rebound_crash(sc) == []


def postup_scene(seed, b_wp, d_wp):
    spec = {"actors": {"a": {"team": "O", "wp": [(0.0, 5.5, 4.0)]}, "b": {"team": "O", "wp": b_wp},
                       "d": {"team": "D", "wp": d_wp}},
            "ball": {"held": [(0.0, 1.0, "a"), (1.3, 99.0, "b")], "flights": [(1.0, 1.3, "a", "b")]}}
    return build(spec, 4.0, seed)


@pytest.mark.parametrize("seed", SEEDS)
def test_post_up(seed):
    truth, sc = postup_scene(seed, [(0.0, 2.0, 1.4), (1.6, 2.0, 1.4), (3.2, 0.8, 0.5)],
                             [(0.0, 1.3, 0.8), (1.6, 1.3, 0.8), (3.2, 0.3, 0.1)])
    e = check(bigs.detect_post_up(sc), "post_up", {"post": "b", "defender": "d"}, fr(1.3))
    assert e.attrs["subtype"] == "back_down"
    truth, sc = postup_scene(seed, [(0.0, 0.0, 8.0)], [(0.0, 0.0, 7.0)])
    assert bigs.detect_post_up(sc) == []


# --------------------------------------------------------------------------------------
# Rule: factorised post-action label
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("seed", SEEDS)
def test_screener_post_action(seed):
    truth, sc, ev = roll_scene(seed)
    e = check(bigs.detect_screener_post_action(sc, screens=[ev]), "screener_post_action", {"screener": "s"}, ev.t0)
    assert e.attrs["top1"] == "roll" and e.attrs["synergy_compat"] == "roll_man"
    truth, sc, ev = elbow_scene(seed, POP_ELBOW_WP)
    e = check(bigs.detect_screener_post_action(sc, screens=[ev]), "screener_post_action", {"screener": "s"}, ev.t0)
    assert e.attrs["top1"] == "pop_arc"
    truth, sc, ev = roll_scene(seed, s_wp=POP_TOP_HOLD_WP)  # holds: none
    e = bigs.detect_screener_post_action(sc, screens=[ev])[0]
    assert e.attrs["top1"] == "none" and e.attrs["label"] == "none"


def test_detect_all_runs_and_sorts():
    truth, sc, ev = roll_scene(1)
    evs = bigs.detect_all(sc, screens=[ev])
    assert any(e.kind == "roll" for e in evs)
    assert [e.t0 for e in evs] == sorted(e.t0 for e in evs)
    assert all(isinstance(e, Event) and 0.0 <= e.conf <= 1.0 for e in evs)


# ======================================================================================
# Loop-1 regression tests (independent tester report, failures B1-B19). Scenarios use
# constant-speed legs with linear ramps (cv_legs) as well as min-jerk waypoints, wing / elbow /
# baseline geometry and sigma_p up to 0.5, which the loop-0 tests did not cover.
# ======================================================================================
def cv_legs(legs, n, ramp_s=0.5):
    """legs: [(t_start, [pts], v)] constant-speed polylines with linear ramps; holds between legs."""
    x = np.full(n, float(legs[0][1][0][0]))
    y = np.full(n, float(legs[0][1][0][1]))
    for t_start, pts, v in legs:
        pts = np.array(pts, dtype=float)
        seg = np.diff(pts, axis=0)
        L = np.concatenate([[0], np.cumsum(np.hypot(seg[:, 0], seg[:, 1]))])
        acc = v / ramp_s
        s, sp, k = 0.0, 0.0, fr(t_start)
        while k < n:
            sp = min(v, sp + acc * DT, math.sqrt(max(0.0, 2 * acc * (L[-1] - s))))
            s = min(L[-1], s + sp * DT)
            i = min(np.searchsorted(L, s, side="right") - 1, len(seg) - 1)
            p = pts[i] + (s - L[i]) / max(L[i + 1] - L[i], 1e-9) * seg[i]
            x[k:], y[k:] = p[0], p[1]
            k += 1
            if s >= L[-1] - 1e-9:
                break
    return x, y


def make_cv(spec, dur, seed, sigma=SIGMA):
    """Like sim.scenario, but an actor may give 'cv' legs instead of 'wp' waypoints."""
    rng = np.random.default_rng(seed)
    n = int(round(dur / DT)) + 1
    truth, tracks = {}, []
    for aid, a in spec["actors"].items():
        x, y = cv_legs(a["cv"], n) if "cv" in a else sim.path(a["wp"], n)
        truth[aid] = (x, y)
        tracks.append(sim.observe(x, y, sigma, rng, oid=aid, team=a.get("team", "")))
    if "ball" in spec:
        bx, by = np.full(n, np.nan), np.full(n, np.nan)
        for t0, t1, aid in spec["ball"].get("held", []):
            a, b = fr(t0), min(n - 1, fr(t1))
            bx[a:b + 1], by[a:b + 1] = truth[aid][0][a:b + 1], truth[aid][1][a:b + 1]
        for t0, t1, fa, fb in spec["ball"].get("flights", []):
            a, b = fr(t0), min(n - 1, fr(t1))
            u = np.linspace(0, 1, b - a + 1)
            bx[a:b + 1] = truth[fa][0][a] + (truth[fb][0][b] - truth[fa][0][a]) * u
            by[a:b + 1] = truth[fa][1][a] + (truth[fb][1][b] - truth[fa][1][a]) * u
        tr = sim.observe(np.nan_to_num(bx), np.nan_to_num(by), sigma * 0.7, rng, oid="ball", role="ball")
        tr.x[np.isnan(bx)] = np.nan
        tr.y[np.isnan(by)] = np.nan
        tracks.append(tr)
    return truth, M.build_scene([t for t in tracks if t.oid != "rim"])


def arrival_frame(truth, aid, t_s, v=0.3):
    return first_after(truth_speed(truth, aid) < v, t_s)


# wing ball screen at (5.2, 6.5) (r 8.32); handler from the right wing to the middle, uses it at ~1.4 s
H_W = [(0.0, 7.0, 4.0), (0.5, 6.6, 4.6), (2.6, 1.0, 7.6)]
H_W_SLOW = [(0.0, 7.0, 4.0), (0.8, 6.6, 4.6), (3.0, 1.0, 7.6)]
S_W = (5.2, 6.5)
W_APP = (0.0, [(4.0, 5.6), S_W], 3.0)  # arrives ~1.0 s


def wing_cv(seed, s_cv, extra=None, h_wp=None, dur=6.0, sigma=SIGMA, ball=None):
    actors = {"s": {"team": "O", "cv": s_cv}, "h": {"team": "O", "wp": h_wp or H_W}}
    actors.update(extra or {})
    truth, sc = make_cv({"actors": actors, "ball": ball or {"held": [(0.0, 99.0, "h")], "flights": []}}, dur, seed, sigma)
    return truth, sc, screen_ev(truth, "s", "h", 0.8, 3.0)


def roll_legs(v, go=2.0, dest=(0.8, 1.0)):
    return [W_APP, (go, [S_W, dest], v)]


# top ball screen: screener arrives at (0.8, 8.0), rolls at 3 m/s from 2.0 s (0.6 s after use)
S_T2 = (0.8, 8.0)
T_APP = (0.0, [(2.0, 9.5), S_T2], 2.5)
TOP_ROLL = [T_APP, (2.0, [S_T2, (0.3, 1.0)], 3.0)]


def top_cv(seed, s_cv, extra=None, ball=None, dur=6.0, sigma=SIGMA):
    actors = {"s": {"team": "O", "cv": s_cv}, "h": {"team": "O", "wp": H_TOP}}
    actors.update(extra or {})
    truth, sc = make_cv({"actors": actors, "ball": ball or {"held": [(0.0, 99.0, "h")], "flights": []}}, dur, seed, sigma)
    return truth, sc, screen_ev(truth, "s", "h", 0.8, 3.0)


# ---- B1 roll_and_replace: shape window anchored to the roll's completion ----
@pytest.mark.parametrize("seed", SEEDS)
def test_b1_roll_and_replace_top_roll_fill_behind(seed):
    ex = {"p": {"team": "O", "cv": [(2.1, [(-3.0, 5.0), (0.0, 7.4)], 3.0)]},
          "c1": {"team": "O", "wp": [(0.0, -6.9, 0.5)]}, "c2": {"team": "O", "wp": [(0.0, 6.5, 3.5)]}}
    truth, sc, ev = top_cv(seed, TOP_ROLL, extra=ex)
    e = check(bigs.detect_roll_and_replace(sc, screens=[ev]), "roll_and_replace", {"roller": "s", "replacer": "p"}, ev.t0)
    assert e.attrs["replace_subtype"] == "fill_behind"
    # a second big parked in the lane breaks the 4-around-1 shape
    ex["b2"] = {"team": "O", "wp": [(0.0, -1.2, 1.6)]}
    truth, sc, ev = top_cv(seed, TOP_ROLL, extra=ex)
    assert bigs.detect_roll_and_replace(sc, screens=[ev]) == []


def test_b1_yaml_shape_window_params():
    p = bigs.params("roll_and_replace")
    assert "shape_from_s" not in p and "shape_to_s" not in p
    assert p["shape_after_completion_s"] == 0.0 and p["shape_len_s"] == 0.4


# ---- B2 seal: distance-scaled window reaches seals after wing screens ----
SEAL_H_W = [(0.0, 7.0, 4.0), (0.5, 6.6, 4.6), (2.6, 1.6, 7.0), (4.6, 0.4, 1.6)]


def n_hits(seeds, fn):
    """Number of seeds for which fn(seed) returns True (noise-limited regressions: recall over seeds)."""
    return sum(bool(fn(s)) for s in seeds)


def hit(evs, kind, actors, t0):
    return any(e.kind == kind and all(e.actors.get(k) == v for k, v in actors.items()) and abs(e.t0 - t0) <= TOL
               and 0 < e.conf <= 1 for e in evs)


SEEDS5 = (1, 2, 3, 4, 5)
SEAL_DS = {"ds": {"team": "D", "wp": [(0.0, 5.6, 7.3), (2.4, 4.4, 7.0), (3.9, 1.5, 3.4)]}}


def test_b2_seal_after_wing_roll():
    def one(seed):
        truth, sc, ev = wing_cv(seed, roll_legs(3.0, dest=(1.6, 2.4)), extra=SEAL_DS, h_wp=SEAL_H_W, dur=6.5)
        evs = bigs.detect_seal(sc, screens=[ev])
        assert all(e.attrs["seal_window_s"] > 2.3 for e in evs)  # r_s0 8.3: 0.5 + (8.3 - 3.5) / 2.5 = 2.42 (+ min_s)
        return hit(evs, "seal", {"screener": "s", "defender": "ds"}, arrival_frame(truth, "s", 2.5))
    assert n_hits(SEEDS5, one) >= 4  # loop 0: 0 of 40 at sigma 0.2 (window 2.0 s from the roll onset)


@pytest.mark.parametrize("seed", SEEDS)
def test_b2_seal_negative_roll_through(seed):
    truth, sc, ev = wing_cv(seed, roll_legs(3.0, dest=(0.6, 0.8)), extra=SEAL_DS, h_wp=SEAL_H_W, dur=6.5)
    assert bigs.detect_seal(sc, screens=[ev]) == []


# ---- B3 roll anchored to t_rel; roll_into_post likewise ----
@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("legs", [roll_legs(3.0), roll_legs(2.2, go=1.8)], ids=["wing_3mps_hold_0p6s", "wing_2p2mps"])
def test_b3_wing_rolls(seed, legs):
    truth, sc, ev = wing_cv(seed, legs, dur=7.0)
    e = check(bigs.detect_roll(sc, screens=[ev]), "roll", {"screener": "s", "handler": "h"}, ev.t0)
    assert e.attrs["completion"] == "rim"


@pytest.mark.parametrize("seed", SEEDS)
def test_b3_roll_into_mid_post_from_wing(seed):
    ex = {"ds": {"team": "D", "wp": [(0.0, 5.6, 7.3), (2.4, 4.6, 6.6), (3.8, 2.0, 2.3)]}}
    truth, sc, ev = wing_cv(seed, roll_legs(3.0, dest=(2.4, 3.2)), extra=ex, dur=6.5)
    e = check(bigs.detect_roll_into_post(sc, screens=[ev]), "roll_into_post", {"screener": "s", "defender": "ds"},
              arrival_frame(truth, "s", 2.5))
    assert e.attrs["subtype"] == "mid_post"


# ---- B4 point tests read at the extremum: correct rolls and pops are no longer capped near 0.5 ----
def test_b4_confidence_not_capped():
    roll_c, pop_c = [], []
    for seed in range(1, 6):
        truth, sc, ev = wing_cv(seed, roll_legs(3.0))
        roll_c += [e.conf for e in bigs.detect_roll(sc, screens=[ev])]
        truth, sc, ev = wing_cv(seed, [W_APP, (1.8, [S_W, (7.3, 4.2)], 3.0)])
        pop_c += [e.conf for e in bigs.detect_pop_arc(sc, screens=[ev])]
    assert len(roll_c) == 5 and len(pop_c) == 5
    assert np.mean(roll_c) >= 0.7, roll_c  # loop 0: 0.33-0.39
    assert np.mean(pop_c) >= 0.7, pop_c


def test_b4_conf_ranks_pop_mid_false_positives_below_true_ones():
    """Reliability (weak form): events on the 1.22 m lateral-slide negative carry lower conf than true mid pops."""
    S_C, C_APP = (5.0, 1.4), (0.0, [(4.0, 0.4), (5.0, 1.4)], 2.5)
    H_B = [(0.0, 6.9, 1.0), (0.5, 6.6, 1.6), (2.6, 2.4, 4.6)]
    tp, fp = [], []
    for seed in range(1, 13):
        for dest, v, bucket in (((5.4, 3.4), 2.5, tp), ((5.2, 2.6), 2.0, fp)):
            actors = {"s": {"team": "O", "cv": [C_APP, (1.6, [S_C, dest], v)]}, "h": {"team": "O", "wp": H_B}}
            truth, sc = make_cv({"actors": actors, "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}, 5.5, seed)
            bucket += [e.conf for e in bigs.detect_pop_mid(sc, screens=[screen_ev(truth, "s", "h", 0.6, 2.6)])]
    assert len(tp) >= 9 and len(fp) <= 2, (tp, fp)
    assert np.mean(tp) > np.mean(fp or [0.0]) + 0.2, (tp, fp)


# ---- B5 short roll stop not truncated at the window end (side pick-and-roll) ----
@pytest.mark.parametrize("seed", SEEDS)
def test_b5_side_short_roll_stop(seed):
    truth, sc, ev = wing_cv(seed, roll_legs(3.0, go=1.7, dest=(3.0, 3.8)))
    e = check(bigs.detect_short_roll(sc, screens=[ev]), "short_roll", {"screener": "s", "handler": "h"}, ev.t0)
    assert e.attrs["variant"] == "stop"
    lab = bigs.detect_screener_post_action(sc, screens=[ev])[0]
    assert lab.attrs["top1"] == "short_roll"


# ---- B6 elbow roll: drop test capped by r_s0 - rim_r ----
def test_b6_elbow_roll():
    S_E, H_E = (2.0, 4.4), [(0.0, 5.6, 6.6), (0.5, 5.0, 6.2), (2.4, -1.0, 5.0)]

    def one(seed, sigma):
        actors = {"s": {"team": "O", "cv": [(0.0, [(3.0, 5.6), S_E], 2.5), (1.9, [S_E, (0.6, 0.8)], 3.0)]},
                  "h": {"team": "O", "wp": H_E}}
        truth, sc = make_cv({"actors": actors, "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}, 5.5, seed, sigma)
        ev = screen_ev(truth, "s", "h", 0.6, 2.6)
        return hit(bigs.detect_roll(sc, screens=[ev]), "roll", {"screener": "s", "handler": "h"}, ev.t0)
    assert n_hits(SEEDS5, lambda s: one(s, 0.3)) == 5
    assert n_hits(SEEDS5, lambda s: one(s, 0.5)) >= 4  # loop 0: 0.75 at sigma 0.5
    assert "dr_floor_r" not in bigs.params("roll")


# ---- B7 ghost 'out' along the arc: mostly lateral, so the separation speed from h counts ----
@pytest.mark.parametrize("seed", SEEDS)
def test_b7_ghost_out_along_the_arc(seed):
    # runs at the handler, turns 60 deg at the closest approach and fades along the arc: outward v_r 0.3-0.8 m/s
    # (the loop-0 exit gate needed 1.0), separation speed from h ~3 m/s
    s_cv = [(0.0, [(-4.0, 4.6), (-0.6, 7.4), (5.2, 5.2)], 3.0)]
    actors = {"s": {"team": "O", "cv": s_cv}, "h": {"team": "O", "wp": [(0.0, 0.0, 8.3)]}}
    truth, sc = make_cv({"actors": actors, "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}, 5.0, seed)
    d = np.hypot(truth["s"][0] - truth["h"][0], truth["s"][1] - truth["h"][1])
    e = check([g for g in bigs.detect_ghost(sc) if g.actors["screener"] == "s"], "ghost", {"screener": "s", "handler": "h"},
              int(np.argmin(d)))
    assert e.attrs["subtype"] == "out"
    # the same path 3 m farther from the handler is a cut, not a ghost
    actors["h"] = {"team": "O", "wp": [(0.0, 0.0, 11.0)]}
    truth, sc = make_cv({"actors": actors, "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}, 5.0, seed)
    assert [g for g in bigs.detect_ghost(sc) if g.actors["screener"] == "s"] == []


# ---- B8 / B19 behind_def along the rim direction (baseline roll), CTG fields stored ----
@pytest.mark.parametrize("seed", SEEDS)
def test_b8_behind_def_baseline_roll(seed):
    h_wp = [(0.0, 6.8, 3.2), (0.5, 6.6, 2.8), (2.6, 2.0, 4.6)]
    s_cv = [(0.0, [(4.0, 0.2), (5.0, 1.2)], 3.0), (2.0, [(5.0, 1.2), (0.8, 0.8)], 3.0)]
    d_cv = [(0.0, [(6.0, 0.6), (5.9, 1.0)], 2.0), (2.15, [(5.9, 1.0), (2.3, 0.9)], 2.8)]
    spec = {"actors": {"s": {"team": "O", "cv": s_cv}, "h": {"team": "O", "wp": h_wp}, "ds": {"team": "D", "cv": d_cv}},
            "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}
    truth, sc = make_cv(spec, 5.5, seed)
    ev = screen_ev(truth, "s", "h", 0.8, 3.0)
    e = check(bigs.detect_behind_def(sc, screens=[ev]), "behind_def", {"roller": "s", "screener_defender": "ds"},
              last_slow_before(truth, "s", 2.3))
    assert e.attrs["max_lead_m"] >= 0.76 and abs(e.attrs["ctg_y_lead_m"]) < 0.76  # the y axis alone misses it
    assert isinstance(e.attrs["ctg_behind"], bool) and "handler_touch_end" in e.attrs


# ---- B9 a catch in stride on a full roll is not a short roll ----
@pytest.mark.parametrize("seed", SEEDS)
def test_b9_catch_in_stride_is_not_short_roll(seed):
    ball = {"held": [(0.0, 3.0, "h"), (3.4, 99.0, "s")], "flights": [(3.0, 3.4, "h", "s")]}
    truth, sc, ev = top_cv(seed, TOP_ROLL, ball=ball)
    assert bigs.detect_short_roll(sc, screens=[ev]) == []
    assert bigs.detect_short_roll_playmaking(sc, screens=[ev]) == []
    # a real pocket catch (roller stops at the FT line) still is one
    ball = {"held": [(0.0, 2.9, "h"), (3.25, 99.0, "s")], "flights": [(2.9, 3.25, "h", "s")]}
    truth, sc, ev = top_cv(seed, [T_APP, (2.0, [S_T2, (0.3, 4.4)], 3.0)], ball=ball)
    e = check(bigs.detect_short_roll(sc, screens=[ev]), "short_roll", {"screener": "s"}, ev.t0)
    assert e.attrs["variant"] == "catch"


# ---- B10 stationary warm-up; set onset at sigma 0.5; no conf-0 events ----
def test_b10_no_stationary_run_in_warmup_of_a_moving_track():
    for seed in range(1, 6):
        x, y, tr = cruise_track("p", "O", [(-6.0, 8.0), (6.0, 8.0)], 3.0, seed, ramp_s=0.01, dur=3.0)
        tr.sigma_p[:] = 0.5
        tr.x[:] = x + sim.noise(len(x), 0.5, np.random.default_rng(seed))
        k = M.build_scene([tr]).k("p")
        _, runs = bigs.stationary_runs(k)
        assert all(a >= bigs.SHARED["stat_min_edge_frames"] for a, b in runs), runs
        assert not any(a < fr(1.0) for a, b in runs), runs


def test_b10_set_onset_at_sigma_0p5():
    def one(seed):
        truth, sc, ev = wing_cv(seed, roll_legs(3.0), sigma=0.5)
        return hit(bigs.detect_screener_set_state(sc, screens=[ev]), "screen_set", {"screener": "s"}, arrival_frame(truth, "s", 0.5))
    assert n_hits(range(1, 9), one) >= 7  # loop 0: 0.63 (t_set = 0 from the warm-up run)


def test_b10_no_zero_conf_events():
    truth, sc, ev = wing_cv(1, roll_legs(3.0), sigma=0.5)
    evs = bigs.detect_all(sc, screens=[ev])
    assert evs and all(e.conf > 0.0 or e.attrs.get("label") == "unknown_post_action" for e in evs)
    real = {it["id"] for it in bigs.DOC["items"] if it.get("detector") and not it.get("needs_data")}
    assert real and all(hasattr(bigs.DETECTORS[k], "__wrapped__") for k in real)  # every detector carries the conf-0 filter


# ---- B11 label = argmax of the renormalised probabilities; ghost 'in' folded into slip ----
@pytest.mark.parametrize("seed", SEEDS)
def test_b11_label_is_argmax(seed):
    cases = [(roll_legs(3.0), H_W, "roll"), ([W_APP, (1.2, [S_W, (0.8, 1.0)], 3.5)], H_W_SLOW, "slip")]
    margin = bigs.params("screener_post_action")["precedence_margin"]
    for legs, h_wp, want in cases:
        truth, sc, ev = wing_cv(seed, legs, h_wp=h_wp)
        e = bigs.detect_screener_post_action(sc, screens=[ev])[0]
        assert e.attrs["top1"] == want, e.attrs
        fired = {k: v for k, v in e.attrs["probs"].items() if k != "none"}
        assert fired[e.attrs["top1"]] >= max(fired.values()) - margin
        assert "precedence_label" in e.attrs


# ---- B12 P_s averaged over the set; same-user re-screen 0.8 m away is the same screen ----
def test_b12_ps_is_set_mean():
    errs = []
    for seed in range(1, 7):
        truth, sc, ev = wing_cv(seed, roll_legs(3.0), sigma=0.5)
        f = bigs.screen_frame(sc, ev)
        errs.append(math.hypot(f.px - S_W[0], f.py - S_W[1]))
    assert np.median(errs) < 0.35, errs


@pytest.mark.parametrize("seed", SEEDS)
def test_b12_same_user_rescreen_0p8m(seed):
    hw = H_W[:2] + [(1.8, 3.6, 6.0), (2.8, 6.4, 4.8), (4.4, 1.0, 7.8)]
    truth, sc, e1 = wing_cv(seed, [W_APP, (2.0, [S_W, (4.6, 7.0)], 2.0)], h_wp=hw)
    e1 = screen_ev(truth, "s", "h", 0.8, 2.0)
    e2 = screen_ev(truth, "s", "h", 3.0, 4.4)
    assert bigs.detect_move_to_screen(sc, screens=[e1, e2]) == []


# ---- B13 seal intervals: onset walked back over candidate frames, min_s applied after merging ----
def test_b13_seal_intervals_unit():
    n = 60
    m, unk, cand = np.zeros(n, bool), np.zeros(n, bool), np.zeros(n, bool)
    cand[10:50] = True       # held, in the region, defender near: from frame 10
    m[20:24] = True          # first strict frame late (pair-distance noise)
    unk[24:34] = True        # defender centre too close: angle undefined
    m[40:44] = True          # strict again after a gap > stat_bridge_frames
    P = bigs.params("post_seal")
    iv = bigs.seal_intervals(m, unk, cand, P, P["min_s"])
    assert iv == [(10, 43)], iv  # walked back to 10, the two pieces merged, 1.1 s >= 0.8 s
    assert bigs.seal_intervals(m, unk, np.zeros(n, bool), P, P["min_s"]) == []  # no walk-back: pieces < 0.8 s


# ---- B14 id swap: crossings still fire; enter run needs mean P(d < 0.6) >= enter_p_min ----
@pytest.mark.parametrize("seed", SEEDS)
def test_b14_paths_cross_in_lane(seed):
    spec = {"actors": {"o": {"team": "O", "wp": [(0.0, 3.0, 1.0), (2.0, -3.0, 1.0)]},
                       "d": {"team": "D", "wp": [(0.0, -1.0, 3.5), (2.0, 1.0, -1.0)]}}}
    truth, sc = build(spec, 3.0, seed)
    dd = np.hypot(truth["o"][0] - truth["d"][0], truth["o"][1] - truth["d"][1])
    check(bigs.detect_id_swap_risk(sc), "id_swap_risk", {"attacker": "o", "defender": "d"}, first_after(dd < 0.9, 0.0))
    assert bigs.params("id_swap_risk")["enter_p_min"] == 0.5


# ---- B15 horns dive: catch position averaged, pinch_post / high_post_area accepted ----
def test_b15_horns_dive_sigma_0p5():
    def one(seed):
        spec = {"actors": {"g": {"team": "O", "wp": [(0.0, 0.0, 8.2)]}, "b1": {"team": "O", "wp": [(0.0, -2.0, 4.4)]},
                           "b": {"team": "O", "cv": [(1.6, [(2.0, 4.4), (0.4, 0.6)], 3.0)]}},
                "ball": {"held": [(0.0, 1.0, "g"), (1.4, 99.0, "b1")], "flights": [(1.0, 1.4, "g", "b1")]}}
        truth, sc = make_cv(spec, 5.0, seed, 0.5)
        evs = [e for e in bigs.detect_dive(sc) if e.attrs["subtype"] == "horns_dive"]
        return hit(evs, "dive", {"big": "b"}, first_after(truth_v_r(truth, "b") >= 1.0, 1.4))
    assert n_hits(range(1, 9), one) >= 6  # loop 0: 0.60 at sigma 0.5 (single noisy catch frame)
    assert set(bigs.params("dive")["context_spots"]) == {"elbow", "pinch_post", "high_post_area"}


# ---- B16 no hard-coded thresholds in detector bodies ----
ALLOWED_LITERALS = {0, 1, 2, -1, 0.0, 1.0, 2.0, -9, 9, 1e-6, 1e-9, 1e9}


def test_b16_no_numeric_literals_in_detectors():
    import ast
    import inspect as _inspect
    tree = ast.parse(Path(_inspect.getsourcefile(bigs)).read_text())
    names = {f"detect_{k}" for k in bigs.DETECTORS} | {"_screen_frame", "_pop", "_trap", "_roll_start", "_roll_window",
                                                          "_seal_mask", "seal_intervals", "_no_rimward_run", "stationary_runs"}
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in names:
            ndigits = {id(c.args[1]) for c in ast.walk(node) if isinstance(c, ast.Call) and getattr(c.func, "id", "") == "round"
                       and len(c.args) == 2}  # round(x, 3): output formatting, not a threshold
            for c in ast.walk(node):
                if id(c) in ndigits:
                    continue
                if isinstance(c, ast.Constant) and isinstance(c.value, (int, float)) and not isinstance(c.value, bool) \
                        and c.value not in ALLOWED_LITERALS:
                    bad.append((node.name, c.lineno, c.value))
    assert not bad, bad


# ---- B17 dead / duplicated params; overrides reach screen_frame ----
def test_b17_params_single_place_and_overrides_reach_screen_frame():
    assert "never_set_sigma_mps" not in bigs.ITEMS["ghost"] and "never_set_half_s" not in bigs.ITEMS["ghost"]
    assert "never_set_sigma_mps" not in bigs.ITEMS["screener_set_state"]
    assert "timing_sigma_s" not in bigs.ITEMS["move_to_screen"]
    src = Path(bigs.__file__).read_text()
    assert 'P["zone_r_min"] - f.r0' in src and 'P["arc_r"] - f.r0' not in src
    truth, sc, ev = wing_cv(1, roll_legs(3.0))
    assert bigs.detect_roll(sc, screens=[ev])
    assert bigs.detect_roll(sc, screens=[ev], first_move_m=50.0) == []  # screen_frame override: first move never reached


# ---- B18 per-scene memo: one post-action call is fast and the frame is computed once ----
def test_b18_memo_and_speed():
    import time
    truth, sc, ev = wing_cv(1, roll_legs(3.0), extra={"p": {"team": "O", "wp": [(0.0, -2.6, 0.2)]}})
    assert bigs.screen_frame(sc, ev) is bigs.screen_frame(sc, ev)
    t = time.time()
    bigs.detect_screener_post_action(sc, screens=[ev])
    assert time.time() - t < 5.0


def test_changes_loop1_recorded():
    ch = bigs.DOC["changes_loop1"]
    assert [c["id"] for c in ch] == [f"B{i}" for i in range(1, 20)]
    assert all({"id", "what", "why", "evidence"} <= set(c) for c in ch)


# ======================================================================================
# Loop 2 (fix pass 2) regressions: one test per changes_loop2 entry
# ======================================================================================
SEEDS8 = tuple(range(1, 9))


def test_l2_noise_tier_from_smoother_sigma():
    # the tier comes from the track's own smoothed position sigma: sigma_p 0.2 / 0.3 low, 0.5 high
    def tier(sigma):
        truth, sc, ev = wing_cv(1, roll_legs(3.0), sigma=sigma)
        return bigs.noise_tier(sc.k("s"))
    assert (tier(0.2), tier(0.3), tier(0.5)) == ("low", "low", "high")
    P = bigs.params("ghost")
    truth, sc, ev = wing_cv(1, roll_legs(3.0), sigma=0.5)
    assert bigs.tiered(P, "approach_h_m", sc.k("s")) == P["approach_h_m_high"]


# ---- L2-B14: min_s applies to the stay interval, so a 3-frame enter run of a fast crossing still fires ----
def test_l2_b14_fast_crossing_enter_run_under_min_s():
    def one(seed):
        # 5 m/s relative crossing: under 0.6 m for only ~3 frames
        spec = {"actors": {"o": {"team": "O", "wp": [(0.0, 3.0, 1.0), (1.2, -3.0, 1.0)]},
                           "d": {"team": "D", "wp": [(0.0, -1.0, 3.5), (1.2, 1.0, -1.0)]}}}
        truth, sc = build(spec, 2.0, seed, sigma=0.2)
        dd = np.hypot(truth["o"][0] - truth["d"][0], truth["o"][1] - truth["d"][1])
        return hit(bigs.detect_id_swap_risk(sc), "id_swap_risk", {"attacker": "o", "defender": "d"}, first_after(dd < 0.9, 0.0))
    assert n_hits(SEEDS8, one) >= 7
    # min_s still drops a stay interval shorter than min_s (overrides reach it)
    spec = {"actors": {"o": {"team": "O", "wp": [(0.0, 3.0, 1.0), (1.2, -3.0, 1.0)]},
                       "d": {"team": "D", "wp": [(0.0, -1.0, 3.5), (1.2, 1.0, -1.0)]}}}
    truth, sc = build(spec, 2.0, 1, sigma=0.2)
    assert bigs.detect_id_swap_risk(sc, min_s=5.0) == []


# ---- L2-B7: ghost never-set test = duration of the slow reading, not the minimum speed ----
GH_TURN = [(0.0, [(3.0, 4.5), (1.0, 6.6), (6.2, 5.0)], 3.0)]  # 150 deg reversal at 3 m/s next to the handler's defender
GH_SET = [(0.0, [(3.5, 4.0), (0.7, 6.9)], 3.0), (1.9, [(0.7, 6.9), (0.3, 1.2)], 3.5)]  # real ~0.3 s stop, then rolls


def gh_cv(seed, s_cv, sigma, h_xy=(0.0, 8.0)):
    actors = {"s": {"team": "O", "cv": s_cv}, "h": {"team": "O", "wp": [(0.0, *h_xy)]},
              "dh": {"team": "D", "wp": [(0.0, 0.2, 7.0)]}}
    truth, sc = make_cv({"actors": actors, "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}, 4.5, seed, sigma)
    d = np.hypot(truth["s"][0] - truth["h"][0], truth["s"][1] - truth["h"][1])
    return sc, int(np.argmin(d))


def test_l2_b7_ghost_sharp_reversal_is_never_set():
    def one(seed):
        sc, t0 = gh_cv(seed, GH_TURN, 0.2)
        return hit([g for g in bigs.detect_ghost(sc) if g.attrs["subtype"] == "out"], "ghost", {"screener": "s", "handler": "h"}, t0)
    assert n_hits(SEEDS8, one) >= 4  # loop 1: ~1-2 of 8 (min speed 0.3-0.9 at the reversal)


@pytest.mark.parametrize("sigma", (0.2, 0.3, 0.5))
def test_l2_b7_ghost_real_short_set_still_rejected(sigma):
    fps = 0
    for seed in SEEDS8:
        sc, t0 = gh_cv(seed, GH_SET, sigma, h_xy=(-0.3, 7.8))
        fps += any(g.actors["screener"] == "s" for g in bigs.detect_ghost(sc))
    assert fps == 0


def test_l2_b7_slow_run_counted_in_full():
    # a run of slow frames that starts before the never-set window counts with its full length
    m = np.array([0, 1, 1, 1, 1, 1, 0, 1, 0], dtype=bool)
    assert list(bigs.run_lengths(m)) == [0, 5, 5, 5, 5, 5, 0, 1, 0]


def test_l2_b7_ghost_in_sigma_0p5_corner_cut():
    # at sigma 0.5 the smoother cuts the corner: a true 1.35 m approach reads 2.0-2.4 m (tier-aware approach_h_m)
    def one(seed):
        actors = {"s": {"team": "O", "cv": [(0.0, [(3.5, 4.0), (0.7, 6.9), (0.3, 1.2)], 3.5)]},
                  "h": {"team": "O", "wp": [(0.0, -0.3, 7.8)]}}
        truth, sc = make_cv({"actors": actors, "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}, 4.5, seed, 0.5)
        d = np.hypot(truth["s"][0] - truth["h"][0], truth["s"][1] - truth["h"][1])
        return hit(bigs.detect_ghost(sc), "ghost", {"screener": "s", "handler": "h"}, int(np.argmin(d)))
    assert n_hits(range(1, 17), one) >= 10  # loop 1: 6 of 16 (approach_h_m 2.0 at every tier)
    # the same run 3 m from the handler stays a cut at the high tier
    actors = {"s": {"team": "O", "cv": [(0.0, [(3.4, 3.0), (3.0, 7.5), (5.5, 6.5)], 3.0)]}, "h": {"team": "O", "wp": [(0.0, -0.3, 7.8)]}}
    for seed in SEEDS8:
        truth, sc = make_cv({"actors": actors, "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}, 4.5, seed, 0.5)
        assert [g for g in bigs.detect_ghost(sc) if g.actors["screener"] == "s"] == []


# ---- L2-B13: post seal at sigma 0.5 (tier-aware seal_def_m / r_max) ----
def test_l2_b13_post_seal_sigma_0p5():
    # mid post, ball at the top, defender rim-side (true gap 0.89 m reads 1.2-1.9 m; true r 3.12 reads 3.5-3.9)
    def one(seed):
        spec = {"actors": {"o": {"team": "O", "wp": [(0.0, 3.0, 4.0), (1.0, 2.0, 2.4)]}, "w": {"team": "O", "wp": [(0.0, 0.0, 7.5)]},
                           "d": {"team": "D", "wp": [(0.0, 2.6, 3.2), (1.0, 1.6, 1.6)]}},
                "ball": {"held": [(0.0, 99.0, "w")], "flights": []}}
        truth, sc = build(spec, 3.5, seed, sigma=0.5)
        return hit(bigs.detect_post_seal(sc), "post_seal", {"post": "o", "defender": "d"}, fr(1.0))
    assert n_hits(range(1, 17), one) >= 15  # loop 1: 12 of 16
    for it in ("post_seal", "roll_into_post"):
        P = bigs.params(it)
        assert P["seal_def_m_low"] == 1.2 and P["seal_def_m_high"] > P["seal_def_m_low"]


@pytest.mark.parametrize("seed", SEEDS)
def test_l2_b13_post_seal_negatives_sigma_0p5(seed):
    truth, sc = post_scene(seed, (2.73, 1.53))  # fronting at the high tier
    spec = {"actors": {"o": {"team": "O", "wp": [(0.0, 3.0, 3.0), (1.0, 2.1, 1.2)]}, "w": {"team": "O", "wp": [(0.0, 6.0, 3.5)]},
                       "d": {"team": "D", "wp": [(0.0, 3.2, 3.6), (1.0, 2.9, 1.9)]}},
            "ball": {"held": [(0.0, 99.0, "w")], "flights": []}}
    truth, sc = build(spec, 3.5, seed, sigma=0.5)  # three-quarter front, angle ~40 deg
    assert [e for e in bigs.detect_post_seal(sc) if e.actors["post"] == "o"] == []


# ---- L2-R5: a noise break inside one post seal does not split it into two events ----
def test_l2_r5_seal_intervals_merge_gap():
    P = bigs.params("post_seal")
    n = 80
    m = np.zeros(n, bool)
    m[10:30] = True  # two 0.63 s pieces of one seal, broken for 10 frames (0.33 s) by noise
    m[40:60] = True
    unk = np.zeros(n, bool)
    cand = m.copy()
    assert bigs.seal_intervals(m, unk, cand, P, P["min_s"]) == []  # loop 1: both pieces < min_s 0.8 s
    assert bigs.seal_intervals(m, unk, cand, P, P["min_s"], bigs.frames(P["seal_merge_gap_s"])) == [(10, 59)]


# ---- L2-R3: early-release margin is tier-aware (top roll at sigma 0.5 is post_use, not early) ----
def test_l2_r3_top_roll_post_use_at_sigma_0p5():
    # the independent harness's top roll (handler path H_TOP2) at sigma 0.5, seed 1004: the smoothed roll start leads
    # the true release, t_use - t_rel = 3 frames (0.1001 s) read as 'early' against a 0.1 s margin (loop 1)
    h_top2 = [(0.0, -5.0, 9.0), (0.5, -4.0, 8.5), (2.6, 2.0, 6.2)]
    actors = {"s": {"team": "O", "cv": TOP_ROLL}, "h": {"team": "O", "wp": h_top2}}
    truth, sc = make_cv({"actors": actors, "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}, 6.0, 1004, 0.5)
    ev = screen_ev(truth, "s", "h", 0.8, 3.0)
    P = bigs.params("screen_frame")
    assert P["early_margin_s_low"] == 0.1 and P["early_margin_s_high"] > P["early_margin_s_low"]
    assert bigs.screen_frame(sc, ev, early_margin_s_high=P["early_margin_s_low"]).release == "early"
    f = bigs.screen_frame(sc, ev)
    assert f.release == "post_use" and f.first_move == "rimward"
    assert [e for e in bigs.detect_roll(sc, screens=[ev]) if e.actors["screener"] == "s"]  # loop 1: no roll


def test_changes_loop2_recorded():
    ch = bigs.DOC["changes_loop2"]
    assert [c["id"] for c in ch] == ["L2-B14", "L2-B7", "L2-B13", "L2-R5", "L2-R3", "L2-R1", "L2-B11"]
    assert all({"id", "what", "why", "evidence"} <= set(c) for c in ch)


# --------------------------------------------------------------------------------------
# Loop 4 (real SportVU calibration): synthetic scenes that reproduce each real failure mode (no real data here)
# --------------------------------------------------------------------------------------
# ---- L4-1: the screens family writes attrs 'kind' (on_ball / off_ball / handoff), not 'screen_class' ----
def test_l4_1_screens_family_kind_is_the_screen_class():
    def ev_kind(kind):
        e = Event("screen", {"screener": "s", "user": "h"}, 10, 0, 20, 1.0, {"kind": kind})
        return bigs.screen_class(e)
    assert (ev_kind("on_ball"), ev_kind("off_ball"), ev_kind("handoff")) == ("ball", "off_ball", "dho")
    assert bigs.screen_class(Event("screen", {}, 0, 0, 0, 1.0, {})) == "ball"  # hand labels without a class: unchanged
    assert bigs.screen_class(Event("screen", {}, 0, 0, 0, 1.0, {"screen_class": "dho", "kind": "off_ball"})) == "dho"
    # real failure: every screens-family off-ball screen was read as a ball screen, so a screener drifting out after a
    # down screen became a 'pop_arc' (19 of 64 real off-ball screens carried pop_arc / pop_mid labels)
    for seed in SEEDS:
        truth, sc, ev = elbow_scene(seed, POP_ELBOW_WP)
        on = Event("screen", ev.actors, ev.t0, ev.start, ev.end, 1.0, {"kind": "on_ball"})
        off = Event("screen", ev.actors, ev.t0, ev.start, ev.end, 1.0, {"kind": "off_ball"})
        assert [e for e in bigs.detect_pop_arc(sc, screens=[on]) if e.actors["screener"] == "s"]
        assert bigs.detect_pop_arc(sc, screens=[off]) == []
        lab = bigs.detect_screener_post_action(sc, screens=[off])[0].attrs["label"]
        assert "pop_arc" not in lab, lab


# ---- L4-2: post_up needs a pass catch outside the restricted area, slow, with no rim visit around it ----
L4_POST_A = [(0.0, 5.5, 4.0)]


def l4_post_scene(seed, b_wp, d_wp, ball, sigma=SIGMA, dur=4.0):
    actors = {"a": {"team": "O", "wp": L4_POST_A}, "b": {"team": "O", "wp": b_wp}, "d": {"team": "D", "wp": d_wp},
              "rim": {"team": "X", "wp": [(0.0, 0.0, 0.0)]}}
    return build({"actors": actors, "ball": ball}, dur, seed, sigma=sigma)


L4_PU = {
    # a shot comes off the rim to a big on the block (the XY holder model reads a 'pass' to a post catch)
    "rebound": ([(0.0, 1.9, 1.5)], [(0.0, 1.3, 0.9)], {"held": [(0.0, 1.0, "a"), (2.2, 3.4, "b"), (3.8, 99, "a")],
                "flights": [(1.0, 1.8, "a", "rim"), (1.8, 2.2, "rim", "b"), (3.4, 3.8, "b", "a")]}, 4.5),
    # the ball is 'held' on the block for 0.5 s and reaches the rim 0.7 s after the catch (shot in flight / tip)
    "tip": ([(0.0, 1.9, 1.5)], [(0.0, 1.3, 0.9)], {"held": [(0.0, 1.0, "a"), (1.4, 1.9, "b"), (2.1, 2.6, "rim")],
            "flights": [(1.0, 1.4, "a", "b"), (1.9, 2.1, "b", "rim")]}, 4.0),
    # a wing cutter catches at ~4 m/s at r ~3 inside post_area (a cut or a drive, not a post catch)
    "cut": ([(0.0, 5.5, 6.0), (2.2, 0.5, 0.5)], [(0.0, 5.8, 6.6), (2.2, 0.9, 1.1)],
            {"held": [(0.0, 1.1, "a"), (1.4, 99, "b")], "flights": [(1.1, 1.4, "a", "b")]}, 3.5),
    # the holder model loses a dribble for 0.4 s and the same player 'catches' again on the block (no entry pass)
    "dribble": ([(0.0, 3.5, 3.0), (1.0, 2.0, 1.6)], [(0.0, 3.0, 2.4), (1.0, 1.4, 1.0)],
                {"held": [(0.0, 1.0, "b"), (1.4, 99, "b")], "flights": []}, 4.0),
    # a dump-off caught under the rim (r 0.8): a finish, not a post-up
    "under_rim": ([(0.0, 0.5, 0.6)], [(0.0, 0.0, 0.2)], {"held": [(0.0, 1.0, "a"), (1.3, 99, "b")],
                  "flights": [(1.0, 1.3, "a", "b")]}, 3.5),
}
L4_PU_OFF = dict(catch_r_min=0.0, require_pass=False, rim_visit_before_s=0.0, rim_visit_after_s=0.0, catch_speed_max_mps=99.0)


@pytest.mark.parametrize("case", sorted(L4_PU))
def test_l4_2_post_up_real_failure_modes(case):
    b_wp, d_wp, ball, dur = L4_PU[case]
    for sigma in (0.2, 0.5):
        for seed in SEEDS:
            truth, sc = l4_post_scene(seed, b_wp, d_wp, ball, sigma, dur)
            # loop 3 rule (gates off) fired on every one of these scenes
            assert [e for e in bigs.detect_post_up(sc, **L4_PU_OFF) if e.actors["post"] == "b"], (case, sigma, seed)
            assert [e for e in bigs.detect_post_up(sc) if e.actors["post"] == "b"] == [], (case, sigma, seed)


def test_l4_2_post_up_low_post_entry_still_fires():
    for sigma in (0.2, 0.3, 0.5):
        for seed in SEEDS:
            truth, sc = l4_post_scene(seed, [(0.0, 2.1, 1.1)], [(0.0, 1.4, 0.7)],
                                      {"held": [(0.0, 1.0, "a"), (1.3, 99, "b")], "flights": [(1.0, 1.3, "a", "b")]}, sigma)
            e = check(bigs.detect_post_up(sc), "post_up", {"post": "b", "defender": "d"}, fr(1.3))
            assert e.attrs["catch_speed"] <= bigs.params("post_up")["catch_speed_max_mps"]


# ---- L4-3: ghost only in the half court, and the SCREENER must run at the handler ----
L4_GH = {
    # transition: a teammate sprints past the handler bringing the ball up in the backcourt
    "transition": ({"h": {"team": "O", "wp": [(0.0, 2.0, 17.0), (4.0, 2.0, 13.5)]},
                    "s": {"team": "O", "wp": [(0.0, -1.0, 23.0), (1.5, 1.2, 16.6), (3.5, 5.0, 7.5)]}}, 4.0),
    # the handler drives hard past a teammate who drifts toward the baseline: the closing speed is the handler's
    "handler_drive": ({"h": {"team": "O", "wp": [(0.0, 7.5, 4.0), (0.6, 6.4, 4.4), (2.4, -1.0, 6.0)]},
                       "s": {"team": "O", "wp": [(0.0, 2.4, 6.0), (0.5, 2.6, 5.8), (2.2, 3.0, 3.2)]}}, 3.5),
}


@pytest.mark.parametrize("case", sorted(L4_GH))
def test_l4_3_ghost_real_failure_modes(case):
    actors, dur = L4_GH[case]
    for sigma in (0.2, 0.3, 0.5):
        for seed in SEEDS8:
            truth, sc = build({"actors": actors, "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}, dur, seed, sigma=sigma)
            assert [e for e in bigs.detect_ghost(sc) if e.actors["screener"] == "s"] == [], (case, sigma, seed)


def test_l4_3_ghost_closing_is_the_screeners_own_speed():
    # the unit-test ghost (screener runs at a standing handler) is unchanged by the own-speed test
    for seed in SEEDS:
        truth, sc, ev = ghost_scene(seed)
        check(bigs.detect_ghost(sc), "ghost", {"screener": "s", "handler": "h"}, ev.t0)


# ---- L4-5: screener_post_action labels compete conditional on the screen ----
def test_l4_5_label_given_screen():
    # real failure: a sure 6 m roll behind a conf-0.45 screen read roll 0.45 vs none 0.55 -> 'ambiguous:roll|none'
    for seed in SEEDS:
        truth, sc, ev = roll_scene(seed)
        weak = Event(ev.kind, ev.actors, ev.t0, ev.start, ev.end, 0.4, ev.attrs)
        e = bigs.detect_screener_post_action(sc, screens=[weak])[0]
        assert e.attrs["label"] == "roll", e.attrs["label"]
        assert e.attrs["p_screen"] == 0.4 and abs(e.conf - 0.4 * e.attrs["p_label"]) < 1e-3
        old = bigs.detect_screener_post_action(sc, screens=[weak], label_given_screen=False)[0]
        assert old.attrs["label"].startswith("ambiguous:roll"), old.attrs["label"]
        # a conf-1 screen (every hand label) is unchanged
        assert bigs.detect_screener_post_action(sc, screens=[ev])[0].attrs["label"] == "roll"


# ---- L4-6: an 'early' release without slip's onset gate is a roll ----
EARLY_ROLL_WP = [(0.0, 2.5, 9.5), (1.0, *S_SET), (1.5, *S_SET), (2.5, 0.6, 6.9), (4.2, 0.3, 1.0)]


def test_l4_6_early_release_slow_start_is_a_roll():
    # real failure: the screener leaves 0.1-0.2 s before the use but reaches v_r 2 m/s only ~0.8 s later (r 6.9 -> 1.8):
    # release 'early' barred roll, slip's gate failed, and the label was 'none'
    lost = 0
    for sigma in (0.2, 0.3, 0.5):
        for seed in (1, 2, 3, 4):
            truth, sc = build(spec_top(EARLY_ROLL_WP), 5.5, seed, sigma=sigma)
            ev = screen_ev(truth, "s", "h", 1.0, 3.0)
            assert [e for e in bigs.detect_roll(sc, screens=[ev]) if e.actors["screener"] == "s"], (sigma, seed)
            assert bigs.detect_slip(sc, screens=[ev]) == [], (sigma, seed)
            lost += not bigs.detect_roll(sc, screens=[ev], early_without_slip_gate=False)
    assert lost >= 3  # the old rule lost the roll whenever the noisy release read 'early'


def test_l4_6_quick_slip_is_still_a_slip():
    for seed in SEEDS:
        truth, sc, ev = roll_scene(seed, s_wp=SLIP_WP)
        assert bigs.detect_slip(sc, screens=[ev]), seed
        assert bigs.detect_roll(sc, screens=[ev]) == [], seed


# ---- L4-7: id_swap_risk tells a crossing from one-sided contact (attributes only) ----
def test_l4_7_id_swap_crossed_attr():
    cross = {"o": {"team": "O", "wp": [(0.0, -2.5, 1.6), (2.0, 2.5, 1.6)]}, "d": {"team": "D", "wp": [(0.0, 2.5, 1.2), (2.0, -2.5, 1.2)]}}
    side = {"o": {"team": "O", "wp": [(0.0, 1.8, 1.5)]}, "d": {"team": "D", "wp": [(0.0, 1.8, 3.2), (0.8, 1.8, 2.0)]}}  # steps in, bodies
    for sigma in (0.2, 0.3):
        for seed in SEEDS:
            truth, sc = build({"actors": cross}, 2.5, seed, sigma=sigma)
            ev = [e for e in bigs.detect_id_swap_risk(sc) if e.actors == {"attacker": "o", "defender": "d"}]
            assert ev and any(e.attrs["crossed"] for e in ev), (sigma, seed, [e.attrs for e in ev])
            truth, sc = build({"actors": side}, 2.5, seed, sigma=sigma)
            ev = [e for e in bigs.detect_id_swap_risk(sc) if e.actors == {"attacker": "o", "defender": "d"}]
            assert ev and not any(e.attrs["crossed"] for e in ev), (sigma, seed, [e.attrs for e in ev])


# ---- L4-8: a ghost turns at the fake set; a straight run past the handler is a cut ----
def test_l4_8_ghost_straight_run_past_is_a_cut():
    old_hits = 0
    for sigma in (0.2, 0.3, 0.5):
        for seed in SEEDS8:
            spec = {"actors": {"s": {"team": "O", "wp": GHOST_S_STRAIGHT}, "h": {"team": "O", "wp": GHOST_H}},
                    "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}
            truth, sc = build(spec, 4.5, seed, sigma=sigma)
            assert [e for e in bigs.detect_ghost(sc) if e.actors["screener"] == "s"] == [], (sigma, seed)
            old_hits += bool([e for e in bigs.detect_ghost(sc, turn_min_deg=0.0) if e.actors["screener"] == "s"])
    assert old_hits >= 12  # the loop-3 rule called this straight run a ghost


def test_l4_8_turning_ghost_sigma_0p5():
    hits = 0
    for seed in SEEDS8:
        spec = {"actors": {"s": {"team": "O", "wp": GHOST_S}, "h": {"team": "O", "wp": GHOST_H}},
                "ball": {"held": [(0.0, 99.0, "h")], "flights": []}}
        truth, sc = build(spec, 4.5, seed, sigma=0.5)
        hits += bool([e for e in bigs.detect_ghost(sc) if e.actors["screener"] == "s"])
    assert hits >= 6


def test_changes_loop4_recorded():
    ch = bigs.DOC["changes_loop4"]
    assert [c["id"] for c in ch] == ["L4-1", "L4-2", "L4-3", "L4-4", "L4-5", "L4-6", "L4-7", "L4-8"]
    assert all({"id", "what", "why", "evidence"} <= set(c) for c in ch)
    assert not any("TBD" in str(c[k]) for c in ch for k in ("what", "why", "evidence"))


# ---- changes_loop5 (B17 rare branches): trap context, slip touch, angle_short, high-low lob ----
# Each branch gets a positive scene and a near-miss scene, run on seeds 1-10 at sigma_p 0.2 / 0.3 / 0.5. The floors are
# the measured hit counts of 10 minus one (L5-1 .. L5-4 in bigs.yaml changes_loop5); near misses must never fire.
L5_SIGMAS = (0.2, 0.3, 0.5)
L5_SEEDS = range(1, 11)
# trap: h's defender trails him over the screen; the screener's defender jumps out to him (trap) or drops with the
# roller to 2.6 m below the screen (drop: never within 2 m of h in [t0 + 0.3, t0 + 1.0] s)
L5_DH_TRAIL = [(0.0, -4.6, 7.8), (0.5, -3.6, 7.6), (2.6, 2.0, 5.4)]
L5_DS_TRAP = [(0.0, 1.3, 7.0), (1.7, 1.3, 7.0), (2.4, 2.7, 6.9)]
L5_DS_DROP = [(0.0, 1.3, 6.4), (1.7, 1.0, 5.6), (2.2, 0.6, 4.0), (3.0, 0.4, 3.0)]
# slip touch: the screener stops 0.4 s at the top and slips; h's defender meets him there (0.6 m) or trails h on the
# high side (never within 1.5 m of the screener)
L5_SLIP_TOUCH_WP = [(0.0, 2.5, 9.5), (1.0, *S_SET), (1.4, *S_SET), (3.2, 0.3, 1.0)]
L5_DH_BRUSH = [(0.0, -4.6, 7.8), (0.5, -3.6, 7.6), (1.0, -0.1, 7.9), (1.5, 0.2, 7.9), (2.6, 2.0, 5.4)]
L5_DH_FAR = [(0.0, -4.6, 9.6), (0.5, -3.6, 9.4), (1.5, -1.0, 9.6), (2.6, 2.0, 7.4)]
# angle_short: a third attacker reaches the screen-side dunker spot 0.6-0.8 s before the ball screen and stays; near
# misses: parked there from the start (arrived > angle_short_before_s earlier) or the opposite dunker spot
L5_K_ARRIVE = [(0.0, 5.2, 1.6), (0.6, 5.2, 1.6), (1.3, 2.6, -0.5)]
L5_K_PARKED = [(0.0, 2.6, -0.5)]
L5_K_OTHER_SIDE = [(0.0, -5.2, 1.6), (0.6, -5.2, 1.6), (1.3, -2.6, -0.5)]
# high-low lob: high-post passer, receiver cutting rimward at >= 3 m/s into a catch at r < 1.5 m (lob) or standing
L5_B_CUT = [(0.0, 3.8, 3.4), (0.9, 3.8, 3.4), (2.1, 0.4, 0.3)]
L5_B_STAND = [(0.0, 1.0, 0.8)]


def _l5_top(seed, sigma, s_wp, extra):
    truth, sc = build(spec_top(s_wp, extra=extra), 5.5, seed, sigma=sigma)
    return sc, screen_ev(truth, "s", "h", 1.0, 3.0)


def _l5_trap(seed, sigma, ds):
    sc, ev = _l5_top(seed, sigma, SHORT_WP, {"Dh": {"team": "D", "wp": L5_DH_TRAIL}, "Ds": {"team": "D", "wp": ds}})
    return [e.attrs["trap_context"] for e in bigs.detect_short_roll(sc, screens=[ev])]


def _l5_touch(seed, sigma, dh):
    sc, ev = _l5_top(seed, sigma, L5_SLIP_TOUCH_WP, {"Dh": {"team": "D", "wp": dh}})
    return [e.attrs["touch"] for e in bigs.detect_slip(sc, screens=[ev])]


def _l5_angle_short(seed, sigma, k_wp):
    sc, ev = _l5_top(seed, sigma, ROLL_WP, {"k": {"team": "O", "wp": k_wp}})
    return [e for e in bigs.detect_dunker_relocation(sc, screens=[ev])
            if e.attrs.get("subtype") == "angle_short" and e.actors.get("dunker") == "k"]


def _l5_lob(seed, sigma, b_wp):
    spec = {"actors": {"a": {"team": "O", "wp": [(0.0, 0.5, 4.5)]}, "b": {"team": "O", "wp": b_wp}},
            "ball": {"held": [(0.0, 1.5, "a"), (1.9, 99.0, "b")], "flights": [(1.5, 1.9, "a", "b")]}}
    truth, sc = build(spec, 3.0, seed, sigma=sigma)
    return [e.attrs["lob"] for e in bigs.detect_high_low(sc) if e.actors == {"passer": "a", "receiver": "b"}]


# (name, positive hit, near-miss hit, floors at sigma_p 0.2 / 0.3 / 0.5); measured hits of 10 in the comments
L5_BRANCHES = {
    # trap scene 10 / 10 / 9; drop scene 0 / 0 / 0 (short_roll itself found 10 / 10 / 9 in both)
    "trap_context": (lambda sd, sg: True in _l5_trap(sd, sg, L5_DS_TRAP),
                     lambda sd, sg: True in _l5_trap(sd, sg, L5_DS_DROP), (9, 9, 8)),
    # brush 10 / 9 / 1 (sigma 0.5: the q 10 smoother floors the 0.4 s stop above never_set_speed_mps, documented
    # limit L5-2); far 0 / 0 / 0; the slip itself is found 10 / 10 / 10 in both
    "slip_touch": (lambda sd, sg: True in _l5_touch(sd, sg, L5_DH_BRUSH),
                   lambda sd, sg: True in _l5_touch(sd, sg, L5_DH_FAR), (9, 8, 0)),
    # arrive 10 / 10 / 10; parked 0 / 0 / 0, other side 0 / 0 / 0
    "angle_short": (lambda sd, sg: bool(_l5_angle_short(sd, sg, L5_K_ARRIVE)),
                    lambda sd, sg: bool(_l5_angle_short(sd, sg, L5_K_PARKED)) or bool(_l5_angle_short(sd, sg, L5_K_OTHER_SIDE)),
                    (9, 9, 9)),
    # cut 10 / 9 / 7 (high_low found 10 / 10 / 10, lob False on the rest); standing receiver lob 0 / 0 / 0
    "high_low_lob": (lambda sd, sg: True in _l5_lob(sd, sg, L5_B_CUT),
                     lambda sd, sg: True in _l5_lob(sd, sg, L5_B_STAND), (9, 8, 6)),
}


@pytest.mark.parametrize("branch", sorted(L5_BRANCHES))
@pytest.mark.parametrize("sigma", L5_SIGMAS)
def test_l5_rare_branch_rates(branch, sigma):
    pos, neg, floors = L5_BRANCHES[branch]
    hits = sum(bool(pos(seed, sigma)) for seed in L5_SEEDS)
    false = [seed for seed in L5_SEEDS if neg(seed, sigma)]
    assert hits >= floors[L5_SIGMAS.index(sigma)], (branch, sigma, hits)
    assert false == [], (branch, sigma, false)


def test_l5_branch_parents_still_found():
    """The near misses change only the attribute / subtype: the parent event is still emitted."""
    for seed in (1, 2, 3):
        assert _l5_trap(seed, 0.3, L5_DS_DROP) and _l5_touch(seed, 0.3, L5_DH_FAR) and _l5_lob(seed, 0.3, L5_B_STAND)
        assert not any(_l5_trap(seed, 0.3, L5_DS_DROP)) and not any(_l5_touch(seed, 0.3, L5_DH_FAR))
        assert _l5_lob(seed, 0.3, L5_B_STAND) == [False]


def test_changes_loop5_recorded():
    ch = bigs.DOC["changes_loop5"]
    assert [c["id"] for c in ch] == ["L5-1", "L5-2", "L5-3", "L5-4"]
    assert all({"id", "what", "why", "evidence"} <= set(c) for c in ch)
