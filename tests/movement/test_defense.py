"""Tests for the defensive movement detectors (tools/specgen/movement/detectors/defense.py).

Validation tier V0: synthetic scenes from sim.scenario (minimum-jerk legs that start and end at rest,
white + AR(1) noise) at sigma_p 0.3 m with fixed seeds. Every detector in defense.DETECTORS gets at least
one positive and one negative scene. Positives check kind, actors, t0 within +-0.3 s of a truth reference
frame computed from the noise-free paths with the item's own definition, and the confidence range.
Upstream anchors (passes, drives, screens, change of possession) are supplied as the scenario author's
truth, because they belong to other families; one test exercises the XY anchor proxies.
"""

from __future__ import annotations

import functools
import math
import os
import sys
from pathlib import Path

# DEF-T22: single-threaded BLAS before numpy loads. Under a heavy machine load multithreaded BLAS made each 3x3
# inverse in mvlib.ca_rts take ~12 ms and one scene ~16 s (tests/conftest.py is outside this family's files).
for _k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_k, "1")

import numpy as np  # noqa: E402
import pytest  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "movement"))
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "named_spots"))

import mvlib  # noqa: E402
import sim  # noqa: E402
import spotlib  # noqa: E402,F401  (named_spots evaluator used through defense.SPOTS)
from detectors import defense as DF  # noqa: E402
from mvlib import DT  # noqa: E402

SIGMA = 0.3
SEED = 7
TOL_S = 0.3
F = mvlib.frames


# --------------------------------------------------------------------------------------
# Scene builders and truth helpers
# --------------------------------------------------------------------------------------
A_MAX, V_MAX = 10.0, 9.5  # m/s^2, m/s: physical limits for a player's minimum-jerk leg


def check_physics(spec):
    """Reject unphysical scenarios: a minimum-jerk leg of d metres over T s peaks at 1.875 d/T (speed) and
    5.77 d/T^2 (acceleration). Faster legs make the CA-RTS innovation gate reject observations and the
    smoothed track overshoot, which tests the scenario, not the detector."""
    bad = []
    for aid, a in spec["actors"].items():
        for (ta, xa, ya), (tb, xb, yb) in zip(a["wp"], a["wp"][1:]):
            d, T = math.hypot(xb - xa, yb - ya), tb - ta
            if d > 0 and (5.77 * d / T**2 > A_MAX + 1e-6 or 1.875 * d / T > V_MAX + 1e-6):
                bad.append(f"{aid} {ta}->{tb}s {d:.2f} m: a {5.77 * d / T**2:.1f} m/s^2, v {1.875 * d / T:.1f} m/s")
    assert not bad, "unphysical legs: " + "; ".join(bad)


def leg_time(d, k=1.0):
    """Fastest physical minimum-jerk duration for d metres (x k to move slower)."""
    return 1.01 * k * max(math.sqrt(5.77 * d / A_MAX), 1.875 * d / V_MAX, 0.2)


def mv(t, p0, *steps):
    """Waypoints: stand at p0 until t, then each step is (x, y) at the fastest physical pace, (x, y, k) k times
    slower, or a number of seconds to pause."""
    wp, cur = [(0.0, *p0)], tuple(p0)
    if t > 0:
        wp.append((t, *p0))
    for st in steps:
        if isinstance(st, (int, float)):
            t += st
        else:
            t += leg_time(math.hypot(st[0] - cur[0], st[1] - cur[1]), st[2] if len(st) > 2 else 1.0)
            cur = (st[0], st[1])
        wp.append((math.ceil(t * 1000) / 1000, *cur))
    return wp


def profile_path(duration, t0, p0, p1, a_up, v_max, a_down):
    """Straight run p0 -> p1 starting at t0 with constant acceleration a_up up to v_max and constant deceleration
    a_down to a stop at p1 (an asymmetric speed profile that minimum-jerk legs cannot express)."""
    n = int(round(duration / DT)) + 1
    d = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    v_pk = min(v_max, math.sqrt(d / (1 / (2 * a_up) + 1 / (2 * a_down))))
    s, v, out = 0.0, 0.0, np.zeros(n)
    for i in range(n):
        if i * DT >= t0 and s < d:
            brake = v * v / (2 * a_down) >= d - s
            v = max(0.0, v - a_down * DT) if brake else min(v_pk, v + a_up * DT)
            s = min(d, s + v * DT) if v > 0 else s
            if brake and v == 0.0:
                s = d
        out[i] = s
    u = ((p1[0] - p0[0]) / d, (p1[1] - p0[1]) / d)
    return p0[0] + u[0] * out, p0[1] + u[1] * out


def build(spec, duration, seed=None, shot=None, paths=None, sigma=None):
    """sim.scenario -> (truth, Scene). shot = (shooter, t_rel_s, t_rim_s): ball flies to the rim. paths = {actor:
    (x, y)} replaces an actor's truth path (observed with the same sim.observe noise model). sigma overrides SIGMA."""
    check_physics(spec)
    seed = SEED if seed is None else seed
    sigma = SIGMA if sigma is None else sigma
    truth, tracks = sim.scenario(spec, duration, sigma, seed)
    for i, (aid, (x, y)) in enumerate((paths or {}).items()):
        k = [j for j, tr in enumerate(tracks) if tr.oid == aid][0]
        tracks[k] = sim.observe(x, y, sigma, np.random.default_rng(seed + 1000 + i), oid=aid, team=tracks[k].team)
        truth[aid] = (x, y)
    if shot is not None:
        shooter, t1, t2 = shot
        ball = [t for t in tracks if t.oid == "ball"][0]
        a, b = F(t1), F(t2)
        s = np.linspace(0, 1, b - a + 1)
        rng = np.random.default_rng(seed + 100)
        sx, sy = truth[shooter][0][a], truth[shooter][1][a]
        ball.x[a : b + 1] = sx * (1 - s) + rng.normal(0, 0.2, len(s))
        ball.y[a : b + 1] = sy * (1 - s) + rng.normal(0, 0.2, len(s))
        ball.x[b + 1 :] = np.nan
        ball.y[b + 1 :] = np.nan
    return truth, mvlib.build_scene(tracks)


def still(*p):
    return [(0.0, *p)]


def tvel(truth, a):
    x, y = truth[a]
    return np.gradient(x) / DT, np.gradient(y) / DT


def tdist(truth, a, b):
    return np.hypot(truth[a][0] - truth[b][0], truth[a][1] - truth[b][1])


def first(mask, after=0):
    idx = np.flatnonzero(np.asarray(mask)[after:])
    assert len(idx), "truth condition never met"
    return after + int(idx[0])


def v_toward(truth, d, q):
    vx, vy = tvel(truth, d)
    ex, ey = truth[q][0] - truth[d][0], truth[q][1] - truth[d][1]
    return (vx * ex + vy * ey) / np.hypot(ex, ey)


def find(events, kind, **actors):
    return [e for e in events if e.kind == kind and all(e.actors.get(k) == v for k, v in actors.items())]


def assert_hit(events, kind, t0_truth, conf_lo=0.5, **actors):
    """The expected label: kind, actors, t0 within +-TOL_S, conf in [conf_lo, 1], reasons present."""
    hits = find(events, kind, **actors)
    assert hits, f"no {kind} {actors}; got {[(e.kind, e.actors, e.t0, round(e.conf, 2)) for e in events]}"
    e = min(hits, key=lambda e: abs(e.t0 - t0_truth))
    assert abs(e.t0 - t0_truth) <= F(TOL_S), f"{kind} t0 {e.t0 * DT:.2f}s vs truth {t0_truth * DT:.2f}s"
    assert conf_lo <= e.conf <= 1.0, f"{kind} conf {e.conf:.3f} outside [{conf_lo}, 1]"
    assert e.attrs.get("reasons"), "every label carries reasons"
    return e


def assert_none(events, kind, **actors):
    hits = find(events, kind, **actors)
    assert not hits, f"unexpected {kind}: {[(e.actors, e.t0, round(e.conf, 2)) for e in hits]}"


ANCH_EMPTY = {k: [] for k in DF.ANCHOR_KEYS}


def anchors(**kw):
    a = dict(ANCH_EMPTY)
    a.update(kw)
    return a


def passes(*items):
    """(t_rel_s, t_catch_s, passer, receiver[, skip]) -> anchor dicts."""
    return [
        dict(t_rel=F(it[0]), t_catch=F(it[1]), passer=it[2], receiver=it[3], skip=bool(it[4]) if len(it) > 4 else False)
        for it in items
    ]


def drive(t, h="H"):
    return anchors(drive=[dict(t=F(t), handler=h)])


def truth_spot(truth, spot_id, d, a, h):
    """Per-frame named_spots membership on the noise-free paths (ball = handler)."""
    sp = DF.SPOTS[spot_id]
    n = len(truth[d][0])
    return np.array(
        [
            bool(
                sp.inside(
                    truth[d][0][t],
                    truth[d][1][t],
                    ax_=truth[a][0][t],
                    ay_=truth[a][1][t],
                    hx=truth[h][0][t],
                    hy=truth[h][1][t],
                    bx=truth[h][0][t],
                    by=truth[h][1][t],
                )
            )
            for t in range(n)
        ]
    )


# --------------------------------------------------------------------------------------
# Scenarios (attacked-rim frame, metres, seconds; every leg physically timed by mv)
# --------------------------------------------------------------------------------------
def closeout_spec(end=(5.15, 3.45), t=1.2, start=(2.0, 2.2), k=1.0):
    """Top P passes to the right wing A at 1.0-1.5 s; A's defender closes out from the help side."""
    da = mv(t, start, (*end, k)) if end != start else still(*start)
    return {
        "actors": {
            "P": {"team": "O", "wp": still(0, 7.5)},
            "A": {"team": "O", "wp": still(6, 4)},
            "DP": {"team": "D", "wp": still(0, 6.6)},
            "DA": {"team": "D", "wp": da},
        },
        "ball": {"held": [(0, 1.0, "P"), (1.5, 5, "A")], "flights": [(1.0, 1.5, "P", "A")]},
    }


@functools.lru_cache(None)
def sc_closeout(kind="standard"):
    cfg = {
        "standard": {},
        "sprint_stop": {},
        "choppy": {},
        "hard": dict(end=(5.45, 3.65)),
        "short": dict(start=(1.8, 2.0), end=(4.65, 3.1)),
        "none": dict(start=(5.1, 3.3), end=(5.1, 3.3)),
    }[kind]
    paths = None
    if kind == "sprint_stop":  # run at up to 5 m/s, stop at 8 m/s^2
        paths = {"DA": profile_path(4.5, 1.15, (2.0, 2.2), (5.15, 3.45), 6.0, 5.0, 8.0)}
    elif kind == "choppy":  # up to 3.6 m/s, then a long 2.3 m/s^2 deceleration over the last ~2.8 m
        paths = {"DA": profile_path(4.5, 0.8, (1.4, 1.9), (5.15, 3.45), 6.0, 3.6, 2.3)}
    return build(closeout_spec(**cfg), 4.5, paths=paths)


D0 = (-2.8, 4.6)


def help_spec(d_wp, h_wp, dh_wp):
    """H drives, his defender DH trails, D guards A on the left wing (d_wp)."""
    return {
        "actors": {
            "H": {"team": "O", "wp": h_wp},
            "A": {"team": "O", "wp": still(-4.5, 5.5)},
            "DH": {"team": "D", "wp": dh_wp},
            "D": {"team": "D", "wp": d_wp},
        },
        "ball": {"held": [(0, 6, "H")]},
    }


@functools.lru_cache(None)
def sc_ladder(kind):
    d = {
        "stunt": mv(1.15, D0, (-1.5, 4.5), 0.1, (-2.7, 4.6)),
        "minor": mv(1.15, D0, (-2.1, 4.6), 0.1, (-2.8, 4.6)),
        "step": mv(1.15, D0, (-1.9, 4.6), 0.1, (-2.8, 4.6)),
        "still": still(*D0),
    }[kind]
    if kind == "step":
        h, dh = mv(1.0, (3.0, 6.0), (1.5, 5.8)), mv(1.0, (3.3, 5.4), (1.8, 5.2))
    else:
        h, dh = mv(1.0, (3.0, 6.0), (1.5, 2.5)), mv(1.0, (3.3, 6.6), (1.8, 3.1))
    return build(help_spec(d, h, dh), 4.0)


def ladder_anchors(kind):
    if kind == "step":
        return anchors(middle_dribble=[dict(t_s=F(1.0), t_e=F(1.95), handler="H")])
    return drive(1.0)


@functools.lru_cache(None)
def sc_dig(dig=True):
    """Wing passer A hits the post H at 1.0-1.3 s; A's defender D digs at the post and recovers."""
    d = mv(1.35, (4.4, 2.5), (2.55, 1.8), 0.1, (4.4, 2.6)) if dig else still(4.4, 2.5)
    spec = {
        "actors": {
            "A": {"team": "O", "wp": still(6.0, 3.2)},
            "H": {"team": "O", "wp": still(1.8, 1.5)},
            "D": {"team": "D", "wp": d},
            "DH": {"team": "D", "wp": still(0.5, 0.2)},
        },
        "ball": {"held": [(0, 1.0, "A"), (1.3, 4.5, "H")], "flights": [(1.0, 1.3, "A", "H")]},
    }
    return build(spec, 4.5)


@functools.lru_cache(None)
def sc_har(help_=True):
    """H drives the middle past DH; weak-side D helps in front of the rim and recovers to A."""
    d = mv(1.25, (-3.2, 2.8), (-0.3, 2.3), 0.3, (-3.5, 2.9)) if help_ else still(-3.2, 2.8)
    spec = {
        "actors": {
            "H": {"team": "O", "wp": mv(1.0, (0.5, 7.0), (0.4, 1.8))},
            "A": {"team": "O", "wp": still(-5.0, 3.5)},
            "DH": {"team": "D", "wp": mv(1.0, (0.5, 6.3), (0.9, 3.8))},
            "D": {"team": "D", "wp": d},
        },
        "ball": {"held": [(0, 5.0, "H")]},
    }
    return build(spec, 5.0)


@functools.lru_cache(None)
def sc_sink(sink=True, fill=False):
    """Baseline drive on the right; weak-side D (on A, left wing) sinks; DB (left corner) may fill."""
    spec = {
        "actors": {
            "H": {"team": "O", "wp": mv(1.0, (5.5, 5.0), (3.5, 1.5))},
            "A": {"team": "O", "wp": still(-5.5, 4.0)},
            "DH": {"team": "D", "wp": mv(1.0, (5.1, 5.6), (3.1, 2.1))},
            "D": {"team": "D", "wp": mv(1.15, (-4.0, 3.4), (-2.5, 1.8)) if sink else still(-4.0, 3.4)},
            "B": {"team": "O", "wp": still(-6.5, 0.8)},
            "DB": {"team": "D", "wp": mv(1.25, (-5.3, 1.2), (-5.1, 2.7)) if fill else still(-5.3, 1.2)},
        },
        "ball": {"held": [(0, 4, "H")]},
    }
    return build(spec, 3.5)


S_POS = (0.5, 7.5)
DROP = {"drop_standard": (0.34, 5.1), "drop_high": (0.42, 6.3), "drop_deep": (0.26, 3.9), "at_level": (0.0, 7.2)}


@functools.lru_cache(None)
def sc_screen(cov):
    """Top pick-and-roll: H comes off S's screen to the right from 1.0 s; coverage by X-ball / X-big."""
    H = mv(1.0, (-1.0, 9.0), (3.0, 6.6))
    S = mv(1.8, S_POS, (0.5, 3.0))
    XB = mv(1.1, (-0.9, 8.2), (0.5, 8.45), (2.6, 7.0))  # over the top
    XBIG = mv(2.2, DROP["drop_standard"], (0.3, 2.6))
    extra = {}
    if cov in DROP:
        XBIG = mv(2.2, DROP[cov], (0.3, 2.6))
    elif cov == "hard_hedge":
        XBIG = mv(0.35, (1.2, 6.8), (2.1, 8.4), 0.6, (0.6, 4.6))
        XB = mv(1.9, (-0.9, 8.2), (0.5, 8.6), (3.0, 7.2))
    elif cov == "soft_show":
        XBIG = mv(0.55, (0.7, 6.5), (1.3, 7.4), 0.2, (0.5, 5.0))
    elif cov == "blitz":
        H = mv(1.0, (-1.0, 9.0), (0.3, 8.7))
        XBIG = mv(0.9, (1.2, 6.9), (1.0, 8.2))
        XB = mv(1.1, (-0.9, 8.2), (-0.4, 8.0))
        S = still(*S_POS)
    elif cov == "under":
        XBIG = still(0.4, 6.0)
        XB = mv(1.1, (-0.9, 8.0), (-0.3, 5.4), (1.8, 5.0))
    elif cov == "through":
        XBIG = still(0.34, 4.6)
        XB = mv(1.1, (-0.9, 8.0), (0.1, 6.3), (2.4, 6.2))
    elif cov == "tag":
        S = mv(1.3, S_POS, (0.5, 2.8))
        extra["D3"] = {"team": "D", "wp": mv(1.7, (3.0, 1.6), (1.0, 3.1), 0.15, (4.5, 1.2))}
    elif cov == "switch":
        H = mv(1.3, (0.0, 8.6), (3.6, 5.6))
        S = mv(1.8, (0.9, 7.6), (0.6, 3.2))
        XB = mv(1.2, (0.3, 8.0), (1.3, 7.0), (0.8, 3.5))
        XBIG = mv(1.2, (2.0, 6.4), (1.7, 6.9), 0.1, (3.3, 5.2))
    if cov in ("tag", "drop_standard"):
        extra["C"] = {"team": "O", "wp": still(6.5, 0.8)}
        extra.setdefault("D3", {"team": "D", "wp": still(4.8, 1.2)})
    actors = {
        "H": {"team": "O", "wp": H},
        "S": {"team": "O", "wp": S},
        "XB": {"team": "D", "wp": XB},
        "XBIG": {"team": "D", "wp": XBIG},
        **extra,
    }
    return build({"actors": actors, "ball": {"held": [(0, 5.0, "H")]}}, 4.8)


SCREEN_T0 = 1.1


def screen_anchor(t0=SCREEN_T0, **kw):
    return anchors(screen=[dict(t0=F(t0), screener="S", handler="H", kind="ball", xball="XB", xbig="XBIG", **kw)])


# --------------------------------------------------------------------------------------
# Registry coverage
# --------------------------------------------------------------------------------------
def test_registry_and_yaml_single_source():
    for k, fn in DF.DETECTORS.items():
        assert fn.__name__ == f"detect_{k}"
        assert DF.ITEMS[k]["detectability"] == "xy" and DF.ITEMS[k]["detector"] == f"detect_{k}"
    for k, fn in DF.NOT_DETECTABLE.items():
        assert fn(None) == []
        assert DF.ITEMS[k]["needs_data"]
    for it in DF.SPEC["items"]:
        for p in (it.get("params") or {}).values():
            assert "value" in p and "unit" in p
    with pytest.raises(TypeError):
        DF.detect_closeout(sc_closeout()[1], not_a_param=1)


def test_anchor_proxies_derive_pass_and_shot():
    _, sc = sc_closeout()
    A = DF.derive_anchors(sc)
    assert len(A["pass"]) == 1 and A["pass"][0]["receiver"] == "A"
    assert abs(A["pass"][0]["t_catch"] - F(1.5)) <= F(TOL_S)
    spec = {
        "actors": {"S": {"team": "O", "wp": still(0, 7.5)}, "DS": {"team": "D", "wp": still(0, 6.3)}},
        "ball": {"held": [(0, 1.0, "S")]},
    }
    _, sc2 = build(spec, 3.0, shot=("S", 1.0, 2.0))
    A2 = DF.derive_anchors(sc2)
    assert len(A2["shot"]) == 1 and A2["shot"][0]["shooter"] == "S" and not A2["pass"]


def test_anchor_proxies_drive_and_screen():
    truth, sc = sc_har(True)
    A = DF.derive_anchors(sc)
    vx, vy = tvel(truth, "H")
    x, y = truth["H"]
    t_truth = first(-(vx * x + vy * y) / np.hypot(x, y) >= DF.params_of("anchors")["drive_backdate_v_r"])
    assert any(d["handler"] == "H" and abs(d["t"] - t_truth) <= F(TOL_S) for d in A["drive"])
    assert find(DF.detect_help_and_recover(sc), "help_and_recover", defender="D")  # end to end on derived anchors
    truth2, sc2 = sc_screen("switch")
    A2 = DF.derive_anchors(sc2)
    t_truth2 = int(np.argmin(tdist(truth2, "S", "XB")[: F(1.8) + 1]))  # S is still until 1.8 s
    assert any(
        s["screener"] == "S" and s["handler"] == "H" and abs(s["t0"] - t_truth2) <= F(TOL_S) for s in A2["screen"]
    ), A2["screen"]


# --------------------------------------------------------------------------------------
# DM-RULE-02 matchup, DM-P01 locomotion
# --------------------------------------------------------------------------------------
def test_matchup_positive():
    _, sc = sc_closeout()
    ev = DF.detect_matchup(sc)
    assert_hit(ev, "matchup", 0, defender="DA", attacker="A")
    assert_hit(ev, "matchup", 0, defender="DP", attacker="P")
    assert_none(ev, "matchup", defender="DA", attacker="P")


def test_matchup_negative_short_clip():
    spec = {
        "actors": {"P": {"team": "O", "wp": still(0, 7.5)}, "DP": {"team": "D", "wp": still(0, 6.6)}},
        "ball": {"held": [(0, 1, "P")]},
    }
    _, sc = build(spec, 0.9)
    assert DF.detect_matchup(sc) == []


def test_def_locomotion_backpedal():
    spec = {
        "actors": {
            "H": {"team": "O", "wp": mv(1.0, (0, 9.5), (0, 5.0))},
            "D": {"team": "D", "wp": mv(1.0, (0, 8.5), (0, 4.0))},
        },
        "ball": {"held": [(0, 4, "H")]},
    }
    truth, sc = build(spec, 4.0)
    vx, vy = tvel(truth, "D")
    t0 = first(np.hypot(vx, vy) >= DF.params_of("def_locomotion")["v_min"])
    assert_hit(DF.detect_def_locomotion(sc), "def_backpedal", t0, conf_lo=0.4, defender="D")


def test_def_locomotion_negative_still():
    spec = {
        "actors": {"H": {"team": "O", "wp": still(0, 9.5)}, "D": {"team": "D", "wp": still(0, 8.5)}},
        "ball": {"held": [(0, 4, "H")]},
    }
    _, sc = build(spec, 3.0)
    assert [e for e in DF.detect_def_locomotion(sc) if e.actors["defender"] == "D"] == []


# --------------------------------------------------------------------------------------
# Closeouts and recover
# --------------------------------------------------------------------------------------
def test_closeout_positive():
    _, sc = sc_closeout()
    e = assert_hit(DF.detect_closeout(sc), "closeout", F(1.5), defender="DA", attacker="A")
    assert e.attrs["closeout_distance_m"] >= 2.5 and e.attrs["latency_s"] >= 0


def test_closeout_negative_already_home():
    _, sc = sc_closeout("none")
    assert DF.detect_closeout(sc) == []


@pytest.mark.parametrize("kind", ["hard", "short"])
def test_closeout_length_classes(kind):
    _, sc = sc_closeout(kind)
    e = assert_hit(DF.detect_closeout_length(sc), f"closeout_{kind}", F(1.5), conf_lo=0.3, defender="DA")
    assert set(e.attrs["alternatives"]) == {"closeout_hard", "closeout_standard", "closeout_short"}


def test_closeout_length_negative():
    _, sc = sc_closeout("none")
    assert DF.detect_closeout_length(sc) == []


@pytest.mark.parametrize("kind", ["sprint_stop", "choppy"])
def test_closeout_profile_classes(kind):
    _, sc = sc_closeout(kind)
    assert_hit(DF.detect_closeout_profile(sc), f"closeout_{kind}", F(1.5), conf_lo=0.3, defender="DA")


def test_closeout_profile_negative():
    _, sc = sc_closeout("none")
    assert DF.detect_closeout_profile(sc) == []


def fly_by_spec(fly=True):
    d = mv(1.4, (2.5, 2.5), (7.0, 5.3)) if fly else mv(1.4, (2.5, 2.5), (4.9, 4.0))
    return {
        "actors": {
            "P": {"team": "O", "wp": still(0, 7.5)},
            "A": {"team": "O", "wp": still(5.5, 4.5)},
            "DP": {"team": "D", "wp": still(0, 6.6)},
            "DA": {"team": "D", "wp": d},
        },
        "ball": {"held": [(0, 1.0, "P"), (1.5, 5, "A")], "flights": [(1.0, 1.5, "P", "A")]},
    }


def test_closeout_fly_by_positive():
    truth, sc = build(fly_by_spec(True), 4.0)
    dd = tdist(truth, "DA", "A")
    t0 = F(1.5) + int(np.argmin(dd[F(1.5) : F(3.0)]))
    assert_hit(DF.detect_closeout_fly_by(sc), "closeout_fly_by", t0, defender="DA", attacker="A")


def test_closeout_fly_by_negative_stops():
    _, sc = build(fly_by_spec(False), 4.0)
    assert DF.detect_closeout_fly_by(sc) == []


def recover_spec(move=True):
    d = mv(1.0, (3.5, 2.5), (5.4, 3.6)) if move else still(3.5, 2.5)
    return {
        "actors": {
            "P": {"team": "O", "wp": still(0, 7.5)},
            "A": {"team": "O", "wp": still(6, 4)},
            "DP": {"team": "D", "wp": still(0, 6.6)},
            "DA": {"team": "D", "wp": d},
        },
        "ball": {"held": [(0, 4, "P")]},
    }


def test_recover_positive():
    truth, sc = build(recover_spec(True), 3.5)
    vt = v_toward(truth, "DA", "A")
    assert_hit(
        DF.detect_recover(sc), "recover", first(vt >= DF.params_of("recover")["v_start"]), defender="DA", attacker="A"
    )


def test_recover_negative():
    _, sc = build(recover_spec(False), 3.5)
    assert DF.detect_recover(sc) == []
    _, sc2 = sc_closeout()
    assert DF.detect_recover(sc2) == []  # the pass-triggered approach is a CLOSEOUT, not a RECOVER


# --------------------------------------------------------------------------------------
# Help ladder and sink
# --------------------------------------------------------------------------------------
def ladder_t0(truth, h="H", d="D", after=0):
    """Truth onset with the help_ladder gate: v_to(H) >= onset_v_to."""
    return first(v_toward(truth, d, h) >= DF.params_of("help_ladder")["onset_v_to"], after)


@pytest.mark.parametrize(
    "kind,det", [("stunt", "detect_stunt"), ("minor", "detect_minor_excursion"), ("step", "detect_step_release")]
)
def test_ladder_rungs(kind, det):
    truth, sc = sc_ladder(kind)
    ev = getattr(DF, det)(sc, anchors=ladder_anchors(kind))
    name = {"stunt": "stunt", "minor": "minor_excursion", "step": "step_release"}[kind]
    e = assert_hit(ev, name, ladder_t0(truth, after=F(1.0)), conf_lo=0.3, defender="D", handler="H")
    assert name in e.attrs["alternatives"]


@pytest.mark.parametrize(
    "det", ["detect_stunt", "detect_minor_excursion", "detect_step_release", "detect_dig", "detect_help_and_recover"]
)
def test_ladder_negative_still_defender(det):
    _, sc = sc_ladder("still")
    assert getattr(DF, det)(sc, anchors=ladder_anchors("stunt")) == []
    assert getattr(DF, det)(sc, anchors=ladder_anchors("step")) == []


def test_ladder_one_rung_per_excursion():
    _, sc = sc_ladder("stunt")
    A = ladder_anchors("stunt")
    assert DF.detect_minor_excursion(sc, anchors=A) == [] and DF.detect_dig(sc, anchors=A) == []
    _, sc2 = sc_ladder("step")
    assert DF.detect_stunt(sc2, anchors=ladder_anchors("step")) == []  # the trigger decides


def test_dig_positive():
    truth, sc = sc_dig(True)
    A = anchors(**{"pass": passes((1.0, 1.3, "A", "H"))})
    e = assert_hit(
        DF.detect_dig(sc, anchors=A), "dig", ladder_t0(truth, after=F(1.3)), conf_lo=0.3, defender="D", handler="H"
    )
    assert e.attrs["trigger"] == "post_catch"


def test_dig_negative():
    _, sc = sc_dig(False)
    assert DF.detect_dig(sc, anchors=anchors(**{"pass": passes((1.0, 1.3, "A", "H"))})) == []


def test_help_and_recover_positive():
    truth, sc = sc_har(True)
    A = anchors(drive=[dict(t=F(1.0), handler="H")])
    assert_hit(
        DF.detect_help_and_recover(sc, anchors=A),
        "help_and_recover",
        ladder_t0(truth, after=F(1.0)),
        conf_lo=0.3,
        defender="D",
        handler="H",
    )
    assert DF.detect_stunt(sc, anchors=A) == [] and DF.detect_dig(sc, anchors=A) == []


def test_help_and_recover_negative():
    _, sc = sc_har(False)
    assert DF.detect_help_and_recover(sc, anchors=anchors(drive=[dict(t=F(1.0), handler="H")])) == []


def test_sink_positive():
    truth, sc = sc_sink(True)
    vx, vy = tvel(truth, "D")
    x, y = truth["D"]
    vr = -(vx * x + vy * y) / np.hypot(x, y)
    A = drive(1.0)
    assert_hit(
        DF.detect_sink(sc, anchors=A),
        "sink",
        first(vr >= DF.params_of("sink")["onset_v_r"], F(1.0)),
        defender="D",
        attacker="A",
    )
    assert DF.detect_stunt(sc, anchors=A) == [] and DF.detect_minor_excursion(sc, anchors=A) == []


def test_sink_negative():
    _, sc = sc_sink(False)
    assert DF.detect_sink(sc, anchors=anchors(drive=[dict(t=F(1.0), handler="H")])) == []


def test_sink_and_fill_positive():
    truth, sc = sc_sink(True, True)
    A = anchors(drive=[dict(t=F(1.0), handler="H")])
    sink = DF.detect_sink(sc, anchors=A)
    s = [e for e in sink if e.actors["defender"] == "D"][0]
    assert_hit(DF.detect_sink_and_fill(sc, anchors=A), "sink_and_fill", s.t0, sinker="D", filler="DB")


def test_sink_and_fill_negative():
    _, sc = sc_sink(True, False)
    assert DF.detect_sink_and_fill(sc, anchors=anchors(drive=[dict(t=F(1.0), handler="H")])) == []


# --------------------------------------------------------------------------------------
# Jump to ball, deny, face guard, beaten, contain, back pressure
# --------------------------------------------------------------------------------------
def jump_spec(jump=True):
    dp = mv(1.05, (0, 6.6), (1.6, 5.4)) if jump else still(0, 6.6)
    return {
        "actors": {
            "P": {"team": "O", "wp": still(0, 7.5)},
            "A": {"team": "O", "wp": still(6, 4)},
            "DP": {"team": "D", "wp": dp},
            "DA": {"team": "D", "wp": still(5.2, 3.6)},
        },
        "ball": {"held": [(0, 1.0, "P"), (1.5, 5, "A")], "flights": [(1.0, 1.5, "P", "A")]},
    }


def test_jump_to_ball_positive():
    _, sc = build(jump_spec(True), 3.5)
    e = assert_hit(DF.detect_jump_to_ball(sc), "jump_to_ball", F(1.0), defender="DP", passer="P")
    assert e.attrs["latency_s"] is not None


def test_jump_to_ball_negative():
    _, sc = build(jump_spec(False), 3.5)
    assert DF.detect_jump_to_ball(sc) == []


def deny_spec(pos):
    """A on the right wing, ball at the top; DA moves from the gap into pos from 1.0 s."""
    da = mv(1.0, GAP_POS, pos) if pos != GAP_POS else still(*GAP_POS)
    return {
        "actors": {
            "P": {"team": "O", "wp": still(0, 7.5)},
            "A": {"team": "O", "wp": still(5.5, 4.5)},
            "DP": {"team": "D", "wp": still(0, 6.6)},
            "DA": {"team": "D", "wp": da},
        },
        "ball": {"held": [(0, 4, "P")]},
    }


DENY_POS, FACE_POS, GAP_POS = (4.3, 5.05), (5.0, 4.85), (3.9, 3.6)


def test_deny_positive():
    truth, sc = build(deny_spec(DENY_POS), 3.5)
    e = assert_hit(
        DF.detect_deny(sc),
        "deny",
        first(truth_spot(truth, "deny_on_the_line", "DA", "A", "P")),
        defender="DA",
        attacker="A",
    )
    assert e.attrs["mean_perp_m"] <= 0.6


def test_deny_negative_gap_position():
    _, sc = build(deny_spec(GAP_POS), 3.5)
    assert DF.detect_deny(sc) == []


def test_face_guard_positive_and_deny_exclusion():
    truth, sc = build(deny_spec(FACE_POS), 3.5)
    assert_hit(
        DF.detect_face_guard(sc),
        "face_guard",
        first(truth_spot(truth, "face_guard", "DA", "A", "P")),
        defender="DA",
        attacker="A",
    )


def test_face_guard_negative():
    _, sc = build(deny_spec(DENY_POS), 3.5)
    assert DF.detect_face_guard(sc) == []


def drive_spec(beaten=True):
    if beaten:
        h, dh = mv(1.0, (0.5, 7.0), (0.4, 1.8)), mv(1.0, (0.5, 6.2), (0.9, 4.0))
    else:
        h, dh = mv(1.0, (0.5, 7.0), (0.5, 5.5)), mv(1.0, (0.5, 6.2), (0.5, 4.6))
    return {"actors": {"H": {"team": "O", "wp": h}, "DH": {"team": "D", "wp": dh}}, "ball": {"held": [(0, 4, "H")]}}


def test_beaten_positive():
    truth, sc = build(drive_spec(True), 3.5)
    sep = np.hypot(*truth["H"]) - np.hypot(*truth["DH"])
    e = assert_hit(
        DF.detect_beaten(sc, anchors=anchors(drive=[dict(t=F(1.0), handler="H")])),
        "beaten",
        first(sep < -0.3),
        defender="DH",
        handler="H",
    )
    assert e.attrs["separation_m"] > 0.3


def test_beaten_negative_contained():
    _, sc = build(drive_spec(False), 3.5)
    assert DF.detect_beaten(sc, anchors=anchors(drive=[dict(t=F(1.0), handler="H")])) == []


def test_contain_positive():
    _, sc = build(drive_spec(False), 3.5)
    assert_hit(
        DF.detect_contain(sc, anchors=anchors(drive=[dict(t=F(1.0), handler="H")])),
        "contain",
        F(1.0),
        defender="DH",
        handler="H",
    )


def test_contain_negative_beaten():
    _, sc = build(drive_spec(True), 3.5)
    assert DF.detect_contain(sc, anchors=anchors(drive=[dict(t=F(1.0), handler="H")])) == []


def bp_spec(close=True):
    d = mv(0.5, (0.5, 20.0), (0.4, 4.6)) if close else mv(0.5, (0.5, 17.5), (0.5, 7.5))
    return {
        "actors": {"H": {"team": "O", "wp": mv(0.5, (0, 14.0), (0, 4.0))}, "D": {"team": "D", "wp": d}},
        "ball": {"held": [(0, 4, "H")]},
    }


def test_back_pressure_positive():
    truth, sc = build(bp_spec(True), 3.6)
    vx, vy = tvel(truth, "D")
    hx, hy = tvel(truth, "H")
    ex, ey = truth["H"][0] - truth["D"][0], truth["H"][1] - truth["D"][1]
    dd = np.hypot(ex, ey)
    cs = ((vx - hx) * ex + (vy - hy) * ey) / dd
    t0 = first((np.hypot(vx, vy) >= 4.5) & (cs >= 1.0))
    assert_hit(DF.detect_back_pressure(sc), "back_pressure", t0, defender="D", handler="H")


def test_back_pressure_negative_no_closing():
    _, sc = build(bp_spec(False), 3.6)
    assert DF.detect_back_pressure(sc) == []


# --------------------------------------------------------------------------------------
# Box-out, get-back, safety back
# --------------------------------------------------------------------------------------
def box_spec(box=True):
    d = mv(0.9, (2.4, 3.0), (1.7, 1.8)) if box else still(1.0, 4.8)
    t = mv(1.0, (3.6, 3.9), (2.3, 2.4)) if box else mv(1.0, (3.6, 3.9), (0.6, 0.8))
    return {
        "actors": {
            "S": {"team": "O", "wp": still(0, 7.5)},
            "T": {"team": "O", "wp": t},
            "DS": {"team": "D", "wp": still(0, 6.3)},
            "D": {"team": "D", "wp": d},
        },
        "ball": {"held": [(0, 1.0, "S")]},
    }


def test_box_out_positive():
    truth, sc = build(box_spec(True), 3.5, shot=("S", 1.0, 2.0))
    sp = DF.SPOTS["box_out_position"]
    m = [
        bool(sp.inside(truth["D"][0][t], truth["D"][1][t], ax_=truth["T"][0][t], ay_=truth["T"][1][t]))
        for t in range(len(truth["D"][0]))
    ]
    e = assert_hit(DF.detect_box_out(sc), "box_out", first(m, F(1.0)), defender="D", target="T")
    assert e.attrs["classic"]


def test_box_out_negative():
    _, sc = build(box_spec(False), 3.5, shot=("S", 1.0, 2.0))
    assert DF.detect_box_out(sc) == []


def gb_spec(run=True, d1_end=(-0.5, 1.5)):
    ds = {"D1": ((-1.0, 12.0), d1_end), "D2": ((3.0, 13.0), (3.5, 4.0))}
    actors = {"O1": {"team": "O", "wp": mv(0.5, (0, 14.0), (0.5, 5.0))}}
    for k, (p0, p1) in ds.items():
        actors[k] = {"team": "D", "wp": mv(0.6, p0, p1) if run else still(*p0)}
    return {"actors": actors, "ball": {"held": [(0, 4, "O1")]}}


def test_get_back_positive():
    truth, sc = build(gb_spec(True), 4.0)
    vx, vy = tvel(truth, "D1")
    x, y = truth["D1"]
    vr = -(vx * x + vy * y) / np.hypot(x, y)
    e = assert_hit(
        DF.detect_get_back(sc, anchors=anchors(cop=[dict(t=F(0.3))])),
        "get_back",
        first(vr >= DF.params_of("get_back")["onset_v_r"], F(0.3)),
        defender="D1",
    )
    assert e.attrs["onset_delay_s"] >= 0


def test_get_back_negative():
    _, sc = build(gb_spec(False), 4.0)
    assert DF.detect_get_back(sc, anchors=anchors(cop=[dict(t=F(0.3))])) == []
    _, sc2 = build(gb_spec(True), 4.0)
    assert DF.detect_get_back(sc2) == []  # change of possession is never derived from XY


def safety_spec(run=True):
    g = mv(1.0, (0, 8.5), (0, 14.0)) if run else still(0, 8.5)
    return {
        "actors": {
            "S": {"team": "O", "wp": still(5.0, 5.0)},
            "G": {"team": "O", "wp": g},
            "DS": {"team": "D", "wp": still(4.3, 4.3)},
        },
        "ball": {"held": [(0, 1.0, "S")]},
    }


def test_safety_back_positive():
    _, sc = build(safety_spec(True), 3.5, shot=("S", 1.0, 2.0))
    assert_hit(DF.detect_safety_back(sc), "safety_back", F(1.0), player="G", shooter="S")


def test_safety_back_negative():
    _, sc = build(safety_spec(False), 3.5, shot=("S", 1.0, 2.0))
    assert DF.detect_safety_back(sc) == []


# --------------------------------------------------------------------------------------
# Matchup changes: rotate, switch, x-out, guard-two
# --------------------------------------------------------------------------------------
def rotate_spec(rot=True):
    d1 = mv(1.5, (-3.8, 4.0), (5.0, 1.4)) if rot else mv(1.5, (-3.8, 4.0), (-2.6, 3.6), 0.1, (-3.8, 4.0))
    return {
        "actors": {
            "H": {"team": "O", "wp": still(0, 7.5)},
            "A1": {"team": "O", "wp": still(-5.0, 4.5)},
            "A2": {"team": "O", "wp": still(6.0, 1.0)},
            "DH": {"team": "D", "wp": still(0, 6.6)},
            "D1": {"team": "D", "wp": d1},
        },
        "ball": {"held": [(0, 5, "H")]},
    }


def emission_cross(truth, d, a_old, a_new, holder="H"):
    """Truth t0 of a matchup change: D becomes closer to the canonical point of A_new than of A_old."""
    bx, by = truth[holder]

    def mu(a):
        return 0.62 * truth[a][0] + 0.11 * bx, 0.62 * truth[a][1] + 0.11 * by

    (ox, oy), (nx, ny) = mu(a_old), mu(a_new)
    x, y = truth[d]
    return first(np.hypot(x - nx, y - ny) < np.hypot(x - ox, y - oy))


def test_rotate_positive():
    truth, sc = build(rotate_spec(True), 5.0)
    assert_hit(
        DF.detect_rotate(sc),
        "rotate",
        emission_cross(truth, "D1", "A1", "A2"),
        defender="D1",
        **{"from": "A1", "to": "A2"},
    )


def test_rotate_negative_brief_excursion():
    _, sc = build(rotate_spec(False), 5.0)
    assert DF.detect_rotate(sc) == []


def test_switch_positive():
    truth, sc = sc_screen("switch")
    dd = tdist(truth, "XB", "XBIG")
    t0 = F(1.0) + int(np.argmin(dd[F(1.0) : F(3.0)]))
    ev = DF.detect_switch(sc, anchors=screen_anchor(1.3))
    e = assert_hit(ev, "switch", t0)
    assert {e.actors["d1"], e.actors["d2"]} == {"XB", "XBIG"}
    assert e.attrs["timing"] == "on_time"
    assert set(e.attrs["alternatives"]) == {"hard", "soft", "neutral"}


def test_switch_negative_drop():
    _, sc = sc_screen("drop_standard")
    assert DF.detect_switch(sc, anchors=screen_anchor()) == []


def xout_spec(xo=True):
    dlow = mv(1.2, (1.0, 1.2), (4.8, 4.4)) if xo else mv(1.2, (1.0, 1.2), (5.7, 1.2))
    dtop = mv(1.3, (1.5, 4.0), (5.8, 1.0)) if xo else mv(1.3, (1.5, 4.0), (4.8, 4.5))
    return {
        "actors": {
            "P": {"team": "O", "wp": still(-5.5, 4.5)},
            "W": {"team": "O", "wp": still(5.5, 5.0)},
            "CO": {"team": "O", "wp": still(6.5, 0.8)},
            "DP": {"team": "D", "wp": still(-4.6, 4.0)},
            "DLOW": {"team": "D", "wp": dlow},
            "DTOP": {"team": "D", "wp": dtop},
        },
        "ball": {"held": [(0, 1.0, "P"), (1.7, 5, "W")], "flights": [(1.0, 1.7, "P", "W")]},
    }


def test_x_out_positive():
    _, sc = build(xout_spec(True), 5.0)
    e = assert_hit(DF.detect_x_out(sc), "x_out", F(1.0))
    assert {e.actors["d1"], e.actors["d2"]} == {"DLOW", "DTOP"} and e.attrs["skip"]
    assert DF.detect_switch(sc) == []


def test_x_out_negative_no_swap():
    _, sc = build(xout_spec(False), 5.0)
    assert DF.detect_x_out(sc) == []
    _, sc2 = sc_screen("switch")
    assert DF.detect_x_out(sc2, anchors=screen_anchor(1.3)) == []


def g2_spec(between=True):
    d = (0.0, 5.6) if between else (-2.4, 6.0)
    return {
        "actors": {
            "P": {"team": "O", "wp": still(6.5, 0.8)},
            "A1": {"team": "O", "wp": still(-3.0, 6.0)},
            "A2": {"team": "O", "wp": still(3.0, 6.0)},
            "DP": {"team": "D", "wp": still(5.8, 1.3)},
            "D": {"team": "D", "wp": still(*d)},
        },
        "ball": {"held": [(0, 4, "P")]},
    }


def test_guard_two_positive():
    _, sc = build(g2_spec(True), 3.0)
    assert_hit(DF.detect_guard_two(sc), "guard_two", 0, defender="D", a1="A1", a2="A2")


def test_guard_two_negative():
    _, sc = build(g2_spec(False), 3.0)
    assert DF.detect_guard_two(sc) == []


# --------------------------------------------------------------------------------------
# Traps and ball-screen coverage
# --------------------------------------------------------------------------------------
def trap_spec(trap=True):
    d2 = mv(0.9, (2.5, 6.5), (6.6, 6.6)) if trap else mv(0.9, (2.5, 6.5), (6.2, 7.5), 0.1, (2.5, 6.5))
    return {
        "actors": {
            "H": {"team": "O", "wp": still(6.0, 5.5)},
            "D1": {"team": "D", "wp": still(5.2, 5.0)},
            "D2": {"team": "D", "wp": d2},
        },
        "ball": {"held": [(0, 5, "H")]},
    }


def test_trap_positive():
    truth, sc = build(trap_spec(True), 4.0)
    m = (tdist(truth, "D1", "H") <= 1.5) & (tdist(truth, "D2", "H") <= 1.5) & (tdist(truth, "D1", "D2") <= 2.5)
    e = assert_hit(DF.detect_trap(sc), "trap", first(m), d1="D1", d2="D2", handler="H")
    assert e.attrs["location"] == "sideline_trap"


def test_trap_negative_fake():
    _, sc = build(trap_spec(False), 4.5)
    assert DF.detect_trap(sc) == []


def screen_cross_t0(truth, xb="XB", s="S", big="XBIG", t0=SCREEN_T0):
    k = F(t0)
    sx, sy = truth[s][0][k], truth[s][1][k]
    bx, by = truth[big][0][k], truth[big][1][k]
    e = np.array([bx - sx, by - sy]) / math.hypot(bx - sx, by - sy)
    side = (truth[xb][0] - truth[s][0]) * -e[1] + (truth[xb][1] - truth[s][1]) * e[0]
    return first(np.sign(side[1:]) != np.sign(side[:-1]), k - F(0.5))


@pytest.mark.parametrize("cov,kind", [("drop_standard", "over"), ("under", "under"), ("through", "through")])
def test_xball_path_classes(cov, kind):
    truth, sc = sc_screen(cov)
    e = assert_hit(
        DF.detect_xball_path(sc, anchors=screen_anchor()), kind, screen_cross_t0(truth), conf_lo=0.4, xball="XB"
    )
    assert kind in e.attrs["alternatives"]


def test_xball_path_negative():
    _, sc = sc_screen("under")
    assert_none(DF.detect_xball_path(sc, anchors=screen_anchor()), "over")
    _, sc2 = sc_screen("drop_standard")
    assert DF.detect_xball_path(sc2, anchors=anchors()) == []  # no screen, no label


@pytest.mark.parametrize("cov", ["drop_standard", "drop_high", "drop_deep", "at_level"])
def test_drop_coverage_classes(cov):
    _, sc = sc_screen(cov)
    e = assert_hit(DF.detect_drop_coverage(sc, anchors=screen_anchor()), cov, F(SCREEN_T0), conf_lo=0.4, xbig="XBIG")
    assert cov in e.attrs["alternatives"]


def test_drop_coverage_negative_hedge():
    _, sc = sc_screen("hard_hedge")
    assert DF.detect_drop_coverage(sc, anchors=screen_anchor()) == []


@pytest.mark.parametrize("cov", ["hard_hedge", "soft_show"])
def test_show_classes(cov):
    truth, sc = sc_screen(cov)
    k = F(SCREEN_T0)
    sx, sy = truth["S"][0][k], truth["S"][1][k]
    er = np.array([-sx, -sy]) / math.hypot(sx, sy)
    dep = (truth["XBIG"][0] - sx) * er[0] + (truth["XBIG"][1] - sy) * er[1]
    lat = (truth["XBIG"][0] - sx) * er[1] * -1 + (truth["XBIG"][1] - sy) * er[0]  # u = er rotated toward S (rim frame)
    a, b = k - F(0.2), k + F(0.8)
    pb = DF.params_of("ball_screen")
    t0 = a + (
        first(dep[a : b + 1] <= pb["hard_depth_max"])
        if cov == "hard_hedge"
        else first(lat[a : b + 1] >= pb["soft_lat_min"])
    )
    assert_hit(DF.detect_show(sc, anchors=screen_anchor()), cov, t0, conf_lo=0.4, xbig="XBIG")


def test_show_negative_drop():
    _, sc = sc_screen("drop_standard")
    assert DF.detect_show(sc, anchors=screen_anchor()) == []


def test_blitz_positive():
    truth, sc = sc_screen("blitz")
    m = (tdist(truth, "XB", "H") <= 1.5) & (tdist(truth, "XBIG", "H") <= 1.5) & (tdist(truth, "XB", "XBIG") <= 2.5)
    assert_hit(DF.detect_blitz(sc, anchors=screen_anchor()), "blitz", first(m), xbig="XBIG", handler="H")


def test_blitz_negative():
    _, sc = sc_screen("drop_standard")
    assert DF.detect_blitz(sc, anchors=screen_anchor()) == []


def ice_spec(ice=True):
    if ice:
        h, xb = mv(1.2, (5.5, 5.5), (6.0, 2.5)), mv(1.3, (4.6, 5.95), (5.2, 2.9))
    else:
        h, xb = mv(1.2, (5.5, 5.5), (2.5, 6.4)), mv(1.3, (5.0, 4.9), (4.1, 7.0), (2.8, 5.7))
    return {
        "actors": {
            "H": {"team": "O", "wp": h},
            "S": {"team": "O", "wp": still(3.1, 6.6)},
            "XB": {"team": "D", "wp": xb},
            "XBIG": {"team": "D", "wp": still(2.9, 4.8)},
        },
        "ball": {"held": [(0, 4, "H")]},
    }


def test_ice_positive():
    _, sc = build(ice_spec(True), 4.0)
    e = assert_hit(DF.detect_ice(sc, anchors=screen_anchor(1.2)), "ice", F(1.2), xball="XB", handler="H")
    assert e.attrs["h_reject"]


def test_ice_negative():
    _, sc = build(ice_spec(False), 4.0)
    assert DF.detect_ice(sc, anchors=screen_anchor(1.2)) == []
    _, sc2 = sc_screen("drop_standard")  # middle screen: never ice
    assert DF.detect_ice(sc2, anchors=screen_anchor()) == []


def test_tag_positive():
    truth, sc = sc_screen("tag")
    t0 = first(tdist(truth, "D3", "S") <= 1.0, F(SCREEN_T0 + 0.5))
    e = assert_hit(DF.detect_tag(sc, anchors=screen_anchor()), "tag", t0, tagger="D3", roller="S")
    assert e.attrs["origin"] == "corner"


def test_tag_negative():
    _, sc = sc_screen("drop_standard")
    assert DF.detect_tag(sc, anchors=screen_anchor()) == []


def offball_spec(cov):
    dc = {
        "trail": mv(1.2, (1.0, 0.5), (2.0, 2.9), (3.3, 4.6)),
        "under": mv(1.1, (1.0, 0.5), (3.0, 1.8), (3.4, 4.6)),
        "top_lock": mv(1.15, (1.46, 1.43), (3.4, 4.6)),
    }[cov]  # top lock: 0.5 m ahead on the cutter's path
    return {
        "actors": {
            "P": {"team": "O", "wp": still(5.5, 6.5)},
            "S": {"team": "O", "wp": still(2.4, 2.4)},
            "C": {"team": "O", "wp": mv(1.0, (1.2, 1.0), (3.6, 5.2))},
            "DP": {"team": "D", "wp": still(4.8, 5.9)},
            "DC": {"team": "D", "wp": dc},
            "DS": {"team": "D", "wp": still(2.0, 1.5)},
        },
        "ball": {"held": [(0, 4, "P")]},
    }


def offball_anchor(t0):
    return anchors(screen=[dict(t0=t0, screener="S", cutter="C", kind="offball", dcut="DC", dscr="DS")])


@pytest.mark.parametrize("cov", ["trail", "top_lock"])
def test_offball_screen_coverage_positive(cov):
    truth, sc = build(offball_spec(cov), 4.0)
    t0 = int(np.argmin(tdist(truth, "C", "S")))
    assert_hit(
        DF.detect_offball_screen_coverage(sc, anchors=offball_anchor(t0)),
        cov,
        t0,
        conf_lo=0.4,
        defender="DC",
        cutter="C",
    )


def test_offball_screen_coverage_negative():
    truth, sc = build(offball_spec("under"), 4.0)
    ev = DF.detect_offball_screen_coverage(sc, anchors=offball_anchor(int(np.argmin(tdist(truth, "C", "S")))))
    assert_none(ev, "trail")
    assert_none(ev, "top_lock")


# --------------------------------------------------------------------------------------
# Post defence
# --------------------------------------------------------------------------------------
POST_A, POST_B = (1.5, 1.8), (5.5, 3.5)


def post_spec(pos, low=None, double=False, enter=False):
    d_wp = mv(1.0, (POST_A[0] - 1.9, POST_A[1] + 0.6), pos) if enter else still(*pos)
    actors = {
        "P": {"team": "O", "wp": still(*POST_B)},
        "A": {"team": "O", "wp": still(*POST_A)},
        "DP": {"team": "D", "wp": still(4.7, 3.1)},
        "D": {"team": "D", "wp": d_wp},
    }
    if low is not None:
        actors["A3"] = {"team": "O", "wp": still(-5.5, 4.0)}
        actors["D3"] = {"team": "D", "wp": still(*low)}
    ball = {"held": [(0, 4.5, "P")]}
    if double:
        actors["D2"] = {"team": "D", "wp": mv(1.5, (0.0, 6.2), (2.0, 2.8))}
        actors["A2"] = {"team": "O", "wp": still(-1.0, 8.0)}
        ball = {"held": [(0, 1.0, "P"), (1.4, 4.5, "A")], "flights": [(1.0, 1.4, "P", "A")]}
    return {"actors": actors, "ball": ball}


u = np.array([POST_B[0] - POST_A[0], POST_B[1] - POST_A[1]]) / math.hypot(POST_B[0] - POST_A[0], POST_B[1] - POST_A[1])
POST_POS = {
    "post_front": (POST_A[0] + 0.8 * u[0], POST_A[1] + 0.8 * u[1]),
    "post_three_quarter_high": (POST_A[0] - 0.8 * u[1], POST_A[1] + 0.8 * u[0]),
    "post_behind": (POST_A[0] - 0.8 * u[0], POST_A[1] - 0.8 * u[1]),
}


@pytest.mark.parametrize("kind", list(POST_POS))
def test_post_position_classes(kind):
    truth, sc = build(post_spec(POST_POS[kind], enter=True), 3.5)
    m = truth_spot(truth, DF._POST[kind], "D", "A", "P")
    t0 = first(m & np.concatenate([m[F(0.5) :], np.zeros(F(0.5), dtype=bool)]))  # entry of the held class
    assert_hit(DF.detect_post_position(sc), kind, t0, conf_lo=0.4, defender="D", post="A")


def test_post_position_negative_far():
    _, sc = build(post_spec((POST_A[0] + 1.6, POST_A[1] + 1.2)), 3.0)
    assert [e for e in DF.detect_post_position(sc) if e.actors["defender"] == "D"] == []


def test_lob_protection_positive():
    truth, sc = build(post_spec(POST_POS["post_front"], low=(-1.0, 1.2), enter=True), 3.5)
    m = truth_spot(truth, "post_full_front", "D", "A", "P")
    e = assert_hit(DF.detect_lob_protection(sc), "lob_protection", first(m), conf_lo=0.4, low_defender="D3")
    assert e.attrs["protected"]


def test_lob_protection_negative():
    _, sc = build(post_spec(POST_POS["post_front"], low=(-4.5, 3.5)), 3.0)
    assert all(not e.attrs["protected"] for e in DF.detect_lob_protection(sc))
    _, sc2 = build(post_spec(POST_POS["post_behind"], low=(-1.0, 1.2)), 3.0)
    assert DF.detect_lob_protection(sc2) == []


def test_post_double_positive():
    truth, sc = build(post_spec(POST_POS["post_behind"], double=True), 4.5)
    m = (tdist(truth, "D2", "A") <= 1.5) & (tdist(truth, "D", "A") <= 1.5) & (tdist(truth, "D", "D2") <= 2.5)
    e = assert_hit(DF.detect_post_double(sc), "post_double", first(m, F(1.4)), doubler="D2", post="A")
    assert e.attrs["origin"] == "top"


def test_post_double_negative():
    spec = post_spec(POST_POS["post_behind"], double=True)
    spec["actors"]["D2"] = {"team": "D", "wp": still(0.0, 6.2)}
    _, sc = build(spec, 4.5)
    assert DF.detect_post_double(sc) == []


# --------------------------------------------------------------------------------------
# Transition and press
# --------------------------------------------------------------------------------------
def test_protect_rim_positive():
    truth, sc = build(gb_spec(True), 4.0)
    x, y = truth["D1"]
    t0 = first((np.hypot(x, y) <= 1.8) & (y >= -0.381))
    assert_hit(DF.detect_protect_rim(sc, anchors=anchors(cop=[dict(t=F(0.3))])), "protect_rim", t0, defender="D1")


def test_protect_rim_negative():
    _, sc = build(gb_spec(True, d1_end=(-0.5, 4.5)), 4.0)
    assert DF.detect_protect_rim(sc, anchors=anchors(cop=[dict(t=F(0.3))])) == []


def stop_spec(stop=True):
    d = still(1.0, 15.0) if stop else still(6.0, 8.0)
    return {
        "actors": {"H": {"team": "O", "wp": mv(0.5, (0, 22.0), (0, 16.0))}, "D": {"team": "D", "wp": d}},
        "ball": {"held": [(0, 4, "H")]},
    }


def test_stop_ball_positive():
    truth, sc = build(stop_spec(True), 3.5)
    e = assert_hit(
        DF.detect_stop_ball(sc, anchors=anchors(cop=[dict(t=F(0.3))])),
        "stop_ball",
        first(tdist(truth, "D", "H") <= 2.0),
        defender="D",
        handler="H",
    )
    assert e.attrs["stopped"]


def test_stop_ball_negative():
    _, sc = build(stop_spec(False), 3.5)
    assert DF.detect_stop_ball(sc, anchors=anchors(cop=[dict(t=F(0.3))])) == []


def tm_spec(matched=True):
    att = {"O1": (0.5, 7.0), "O2": (5.0, 4.0), "O3": (-5.5, 3.0)}
    dfn = {"X1": (0.4, 6.0), "X2": (4.3, 3.4), "X3": (-4.7, 2.6) if matched else (-1.0, 2.0)}
    actors = {}
    for k, (x, y) in att.items():
        actors[k] = {"team": "O", "wp": mv(0.5, (x, y + 14.0), (x, y))}
    for k, (x, y) in dfn.items():
        actors[k] = {"team": "D", "wp": mv(0.4, (x, y + 9.0), (x, y))}
    return {"actors": actors, "ball": {"held": [(0, 5, "O1")]}}


def test_transition_matched_positive():
    truth, sc = build(tm_spec(True), 4.5)
    ok = np.ones(len(truth["O1"][0]), dtype=bool)
    for a in ("O1", "O2", "O3"):
        r = np.hypot(*truth[a])
        thr = np.where(r < 3.0, 1.5, 2.5)
        ok &= np.min([tdist(truth, d, a) for d in ("X1", "X2", "X3")], axis=0) <= thr
    assert_hit(
        DF.detect_transition_matched(sc, anchors=anchors(cop=[dict(t=F(0.3))])), "transition_matched", first(ok, F(0.3))
    )


def test_transition_matched_negative():
    _, sc = build(tm_spec(False), 4.5)
    assert DF.detect_transition_matched(sc, anchors=anchors(cop=[dict(t=F(0.3))])) == []


def test_set_def_positive():
    truth, sc = build(tm_spec(True), 4.5)
    ys = np.max([truth[d][1] for d in ("X1", "X2", "X3")], axis=0)
    sp = np.mean([np.hypot(*tvel(truth, d)) for d in ("X1", "X2", "X3")], axis=0)
    assert_hit(DF.detect_set_def(sc), "set_def", first((ys < 12.7) & (sp < 2.5), F(1.0)))


def test_set_def_negative():
    spec = tm_spec(True)
    spec["actors"]["X3"] = {"team": "D", "wp": still(-4.7, 15.0)}  # one defender stays beyond half court
    _, sc = build(spec, 4.5)
    assert DF.detect_set_def(sc) == []


def press_spec(press=True):
    d = mv(0.5, (0.2, 19.5), (0.2, 15.6)) if press else still(4.0, 18.0)
    return {
        "actors": {"H": {"team": "O", "wp": mv(0.5, (0, 20.8), (0, 16.8))}, "D": {"team": "D", "wp": d}},
        "ball": {"held": [(0, 4, "H")]},
    }


def test_press_pickup_positive():
    _, sc = build(press_spec(True), 3.5)
    assert_hit(DF.detect_press_pickup(sc), "press_pickup", 0, defender="D", handler="H")


def test_press_pickup_negative():
    _, sc = build(press_spec(False), 3.5)
    assert DF.detect_press_pickup(sc) == []


# --------------------------------------------------------------------------------------
# Loop 1 regressions: one test (or more) per fixed failure of the independent tester's report (DEF-T01..T22).
# Scenes follow the tester's harness geometry (scratchpad test_defense/harness.py); hit = kind, actors, t0 +- 0.3 s.
# --------------------------------------------------------------------------------------
def hits_over_seeds(make, check, seeds=range(1, 7)):
    """Number of seeds for which check(truth, scene) holds (noise-sensitive items are tested as k of n)."""
    n = 0
    for sd in seeds:
        truth, sc = make(sd)
        n += bool(check(truth, sc))
    return n


def dig_spec(dig=True, hold=0.0):
    """Elbow drive by H; D (guarding P at the top) digs to ~0.75 m of H and goes straight back (tester dig_spec)."""
    H = mv(1.0, (5.5, 5.0), (2.4, 4.8, 1.2))
    DH = mv(1.0, (4.8, 4.4), (2.0, 4.0, 1.2))
    if not dig:
        d = still(0.3, 6.5)
    elif hold:
        d = mv(1.3, (0.3, 6.5), (1.85, 5.3), hold, (0.3, 6.4))
    else:
        d = mv(1.3, (0.3, 6.5), (1.85, 5.3), (0.3, 6.4))
    return {
        "actors": {
            "H": {"team": "O", "wp": H},
            "P": {"team": "O", "wp": still(0, 7.6)},
            "DH": {"team": "D", "wp": DH},
            "D": {"team": "D", "wp": d},
        },
        "ball": {"held": [(0, 5, "H")]},
    }


def test_t01_dig_is_not_swallowed_by_trap():
    def make(sd):
        return build(dig_spec(True), 4.5, seed=sd)

    def check(truth, sc):
        A = drive(1.0)
        t0 = first(v_toward(truth, "D", "H") >= 0.7, F(1.0))
        no_trap = not [e for e in DF.detect_trap(sc) if "D" in (e.actors["d1"], e.actors["d2"])]
        dig = [e for e in DF.detect_dig(sc, anchors=A) if e.actors["defender"] == "D" and abs(e.t0 - t0) <= F(TOL_S)]
        return no_trap and dig

    assert hits_over_seeds(make, check) >= 5  # baseline 0/6: every dig became a TRAP


def test_t01_trap_commitment_keeps_real_traps():
    spec = {
        "actors": {
            "H": {"team": "O", "wp": still(6.3, 0.9)},
            "D1": {"team": "D", "wp": still(5.6, 1.6)},
            "D2": {"team": "D", "wp": mv(0.9, (3.2, 2.6), (6.0, 2.1))},
        },
        "ball": {"held": [(0, 5, "H")]},
    }
    truth, sc = build(spec, 4.0, seed=1)
    t0 = first((tdist(truth, "D1", "H") <= 1.5) & (tdist(truth, "D2", "H") <= 1.5) & (tdist(truth, "D1", "D2") <= 2.5))
    e = assert_hit(DF.detect_trap(sc), "trap", t0, d1="D1", d2="D2", handler="H")
    assert e.conf <= e.attrs["p_emit"] + 1e-9  # conf on the entry threshold, existence on the band middle (T02c/T12b)
    assert e.attrs["location"] == "corner_trap"


S_W = (4.9, 6.9)  # right-wing side pick-and-roll of the tester's harness
UH = (-3.4 / math.hypot(3.4, 1.4), 1.4 / math.hypot(3.4, 1.4))


def sp_pt(depth, lat=0.0, S=S_W):
    er = (-S[0] / math.hypot(*S), -S[1] / math.hypot(*S))
    return (S[0] + depth * er[0] + lat * UH[0], S[1] + depth * er[1] + lat * UH[1])


def side_pnr(xb="over", big=("drop", 2.4), S=S_W, H0=(6.2, 6.0), H1=(2.8, 7.4)):
    H = mv(1.0, H0, H1)
    XB = {
        "over": mv(1.1, (5.6, 5.4), (5.0, 7.7), (3.3, 7.0)),
        "trapside": mv(1.1, (5.6, 5.4), (6.2, 5.6)),
    }[xb]
    kind, val = big
    if kind == "drop":
        XBIG = mv(2.2, sp_pt(val, S=S), (1.0, 3.0))
    elif kind == "hard_hedge":
        XBIG = mv(0.4, sp_pt(2.0), sp_pt(-1.15, 1.0), val or 0.35, (2.4, 3.6))
    elif kind == "soft_show":
        XBIG = mv(0.6, sp_pt(1.6), sp_pt(0.0, 0.8), 0.25, sp_pt(1.6, 0.0))
    elif kind == "blitz_from_drop":
        H = mv(1.0, H0, (5.6, 6.4, 1.5))
        XBIG = mv(0.7, sp_pt(2.0), (5.2, 7.2))
    elif kind == "show_2m":
        H = mv(1.0, H0, (5.6, 6.4, 1.5))
        XBIG = mv(0.7, sp_pt(2.0), (4.9, 8.0))
    return {
        "actors": {
            "H": {"team": "O", "wp": H},
            "S": {"team": "O", "wp": mv(1.9, S, (1.5, 2.0))},
            "XB": {"team": "D", "wp": XB},
            "XBIG": {"team": "D", "wp": XBIG},
        },
        "ball": {"held": [(0, 5, "H")]},
    }


def side_anchor(t0=1.3):
    return screen_anchor(t0)


def test_t02_soft_show_is_not_a_trap_or_blitz():
    def make(sd):
        return build(side_pnr("over", ("soft_show", None)), 4.5, seed=sd)

    def check(truth, sc):
        return not DF.detect_trap(sc) and not DF.detect_blitz(sc, anchors=side_anchor())

    assert hits_over_seeds(make, check) == 6


def test_t02_big_stopping_1_75m_is_not_a_blitz():
    def make(sd):
        return build(side_pnr("trapside", ("show_2m", None)), 4.5, seed=sd)

    assert hits_over_seeds(make, lambda tr, sc: not DF.detect_blitz(sc, anchors=side_anchor(1.2))) >= 5


def test_t08_blitz_from_a_drop_reads_the_depth_during_the_trap():
    truth, sc = build(side_pnr("trapside", ("blitz_from_drop", None)), 4.5, seed=2)
    t0 = first((tdist(truth, "XB", "H") <= 1.5) & (tdist(truth, "XBIG", "H") <= 1.5) & (tdist(truth, "XB", "XBIG") <= 2.5))
    e = assert_hit(DF.detect_blitz(sc, anchors=side_anchor(1.2)), "blitz", t0, conf_lo=0.4, xbig="XBIG")
    assert "depth_at_entry_m" in e.attrs and e.attrs["depth_m"] <= e.attrs["depth_at_entry_m"] + 1e-9


def rot_spec(kind):
    D = {
        "rot": mv(1.5, (-4.0, 1.5), (1.4, 1.3)),
        "brief": mv(1.5, (-4.0, 1.5), (-1.2, 1.4), 0.3, (-4.0, 1.5)),
    }[kind]
    return {
        "actors": {
            "H": {"team": "O", "wp": still(0, 7.5)},
            "C": {"team": "O", "wp": still(-6.5, 0.8)},
            "B": {"team": "O", "wp": still(2.0, 1.0)},
            "DH": {"team": "D", "wp": still(0, 6.5)},
            "D": {"team": "D", "wp": D},
        },
        "ball": {"held": [(0, 5, "H")]},
    }


def test_t03_excursion_that_returns_is_not_a_rotation():
    def make(sd):
        return build(rot_spec("brief"), 5.0, seed=sd)

    assert hits_over_seeds(make, lambda tr, sc: not DF.detect_rotate(sc)) == 6  # baseline 13/20 false rotations
    truth, sc = build(rot_spec("rot"), 5.0)
    assert find(DF.detect_rotate(sc), "rotate", defender="D", **{"from": "C", "to": "B"})


def deny_line_spec(ball, A, pos, start):
    return {
        "actors": {
            "W": {"team": "O", "wp": still(*ball)},
            "A": {"team": "O", "wp": still(*A)},
            "DW": {"team": "D", "wp": still(ball[0] - 0.6, ball[1] - 0.7)},
            "DA": {"team": "D", "wp": mv(1.0, start, pos)},
        },
        "ball": {"held": [(0, 5, "W")]},
    }


def line_pos(A, B, tau, perp):
    ux, uy = B[0] - A[0], B[1] - A[1]
    L = math.hypot(ux, uy)
    px, py = A[0] + tau * ux, A[1] + tau * uy
    nx, ny = -uy / L, ux / L
    if (px + nx) ** 2 + (py + ny) ** 2 > px**2 + py**2:
        nx, ny = -nx, -ny
    return (px + perp * nx, py + perp * ny)


def test_t04_deny_entry_not_blocked_by_raw_face_guard_frames():
    """Frames that meet the per-frame face_guard predicate but belong to no FACE_GUARD event stay available to DENY."""
    WA, WB = (5.6, 4.6), (6.5, 0.9)  # wing deny (tau 0.2, perp 0.3), ball in the corner
    checked = 0
    for sd in range(1, 11):
        _, sc = build(deny_line_spec(WB, WA, line_pos(WA, WB, 0.2, 0.3), (4.4, 3.4)), 3.5, seed=sd)
        raw = DF._spot_series(sc, "face_guard", "DA", DF.matchup_posterior(sc)["top1"]["DA"], range(sc.n))
        if not raw.any() or find(DF.detect_face_guard(sc), "face_guard", defender="DA"):
            continue
        t_raw = int(np.flatnonzero(raw)[0])
        ev = find(DF.detect_deny(sc), "deny", defender="DA", attacker="A")
        assert any(e.start <= t_raw <= e.end for e in ev), (sd, t_raw, [(e.start, e.end) for e in ev])
        checked += 1
    assert checked >= 3  # seeds 2, 4, 5, 7, 9 at sigma 0.3


def test_t04_t12_deny_conf_carries_tau_and_posterior():
    WA, WB = (5.6, 4.6), (6.5, 0.9)
    _, sc = build(deny_line_spec(WB, WA, line_pos(WA, WB, 0.2, 0.3), (4.4, 3.4)), 3.5, seed=2, sigma=0.2)
    ev = find(DF.detect_deny(sc), "deny", defender="DA")
    assert ev and all(any("matchup posterior" in r for r in e.attrs["reasons"]) for e in ev)
    assert all(e.attrs["p_cond"] <= e.attrs["p_emit"] + 1e-9 for e in ev)


def contain_spec():
    return {
        "actors": {
            "H": {"team": "O", "wp": mv(1.0, (5.4, 4.4), (4.6, 2.4, 1.2))},
            "DH": {"team": "D", "wp": mv(1.0, (4.70, 3.83), (3.80, 1.98, 1.2))},
        },
        "ball": {"held": [(0, 5, "H")]},
    }


def test_t05_contain_slowdown_after_the_first_second():
    def make(sd):
        return build(contain_spec(), 3.5, seed=sd)

    def check(truth, sc):
        return any(abs(e.t0 - F(1.0)) <= F(TOL_S) for e in find(DF.detect_contain(sc, anchors=drive(1.0)), "contain"))

    assert hits_over_seeds(make, check) >= 5  # baseline 8/20


def show_truth_t0(truth, cls, t0=1.3):
    k = F(t0)
    sx, sy = truth["S"][0][k], truth["S"][1][k]
    er = np.array([-sx, -sy]) / math.hypot(sx, sy)
    dep = (truth["XBIG"][0] - sx) * er[0] + (truth["XBIG"][1] - sy) * er[1]
    vx, vy = tvel(truth, "H")
    hv = (np.mean(vx[k - F(0.5) : k + 1]), np.mean(vy[k - F(0.5) : k + 1]))
    u = np.array(hv) / np.hypot(*hv)
    lat = (truth["XBIG"][0] - sx) * u[0] + (truth["XBIG"][1] - sy) * u[1]
    return first(dep <= -0.6, k - F(0.2)) if cls == "hard_hedge" else first(lat >= 0.5, k - F(0.2))


@pytest.mark.parametrize("cls,big,need", [("soft_show", ("soft_show", None), 5), ("hard_hedge", ("hard_hedge", 0.9), 3)])
def test_t06_show_hold_and_existence(cls, big, need):
    def make(sd):
        return build(side_pnr("over", big), 4.5, seed=sd)

    def check(truth, sc):
        t0 = show_truth_t0(truth, cls)
        return any(abs(e.t0 - t0) <= F(TOL_S) for e in find(DF.detect_show(sc, anchors=side_anchor()), cls))

    assert hits_over_seeds(make, check) >= need  # baseline soft 7/20, hard hedge held 0.9 s 2/20 (sigma 0.3)


def test_t07_elbow_high_drop_is_not_forced_deep():
    S_E = (2.4, 4.7)
    truth, sc = build(side_pnr("over", ("drop", 1.1), S=S_E, H0=(4.6, 5.4), H1=(0.6, 5.6)), 4.5)
    ev = DF.detect_drop_coverage(sc, anchors=side_anchor())
    assert_hit(ev, "drop_high", F(1.3), conf_lo=0.3, xbig="XBIG")
    assert_none(ev, "drop_deep")


def ob_spec(kind):
    C0, C1, SO = (2.6, 0.8), (5.8, 4.8), (4.85, 2.7)
    UC = ((C1[0] - C0[0]) / math.hypot(3.2, 4.0), (C1[1] - C0[1]) / math.hypot(3.2, 4.0))
    if kind == "under":
        DC = mv(1.0, (3.2, 0.4), (5.7, 2.0), (5.9, 3.9))
    else:
        sh = {"lock": 0.6, "level": 0.05}[kind]
        DC = mv(1.0, (C0[0] + sh * UC[0], C0[1] + sh * UC[1]), (C1[0] + sh * UC[0], C1[1] + sh * UC[1]))
    return {
        "actors": {
            "P": {"team": "O", "wp": still(0.5, 7.6)},
            "S": {"team": "O", "wp": still(*SO)},
            "C": {"team": "O", "wp": mv(1.0, C0, C1)},
            "DP": {"team": "D", "wp": still(0.5, 6.6)},
            "DC": {"team": "D", "wp": DC},
            "DS": {"team": "D", "wp": still(4.3, 2.0)},
        },
        "ball": {"held": [(0, 5, "P")]},
    }


def ob_anchors(truth):
    t0 = int(np.argmin(tdist(truth, "C", "S")))
    return anchors(screen=[dict(t0=t0, screener="S", cutter="C", kind="offball", dcut="DC", dscr="DS")]), t0


def test_t09_shooting_the_gap_under_is_not_top_lock():
    def make(sd):
        return build(ob_spec("under"), 4.0, seed=sd)

    def check(truth, sc):
        A, _ = ob_anchors(truth)
        ev = DF.detect_offball_screen_coverage(sc, anchors=A)
        return not find(ev, "top_lock") and find(ev, "under", defender="DC")

    assert hits_over_seeds(make, check) == 6  # baseline 3/20 under -> top_lock


def test_t09_top_lock_still_detected():
    truth, sc = build(ob_spec("lock"), 4.0, seed=2)
    A, t0 = ob_anchors(truth)
    e = assert_hit(DF.detect_offball_screen_coverage(sc, anchors=A), "top_lock", t0, defender="DC", cutter="C")
    assert e.attrs["mean_offset_to_screener_m"] <= DF.params_of("offball_screen_coverage")["lock_lat_tol"]


def test_t10_crossing_is_debounced():
    side = np.concatenate([np.full(20, 1.0), [-1.0], np.full(10, 1.0), np.full(20, -1.0)])  # one-frame noise flip
    tc = DF._debounced_cross(side, 0, len(side) - 1, 5)
    assert tc is not None and 28 <= tc <= 32  # the real crossing at frame 30-31, not the flip at 20
    assert DF._debounced_cross(np.concatenate([np.full(20, 1.0), [-1.0, -1.0], np.full(20, 1.0)]), 0, 41, 5) is None


def test_t11_slow_shuffle_is_not_locomotion():
    spec = {
        "actors": {"H": {"team": "O", "wp": still(0, 7.6)}, "D": {"team": "D", "wp": mv(0.8, (-0.45, 6.6), (0.45, 6.6, 3.0))}},
        "ball": {"held": [(0, 5, "H")]},
    }

    def make(sd):
        return build(spec, 4.5, seed=sd)

    assert hits_over_seeds(make, lambda tr, sc: not DF.detect_def_locomotion(sc)) >= 5  # baseline 8/20 FP


def test_t13_noise_tier_estimate_and_q10_parameters():
    _, sc3 = sc_closeout()
    _, sc5 = build(closeout_spec(), 4.5, sigma=0.5)
    s3, q3 = DF.noise_of(sc3.kins["DA"])
    s5, q5 = DF.noise_of(sc5.kins["DA"])
    assert abs(s3 - 0.3) <= 0.05 and q3 == mvlib.Q_DEFAULT
    assert abs(s5 - 0.5) <= 0.07 and q5 == mvlib.Q_HIGH_NOISE
    p = DF.merged_params("closeout_profile", "closeout")
    assert DF.tier_param(p, "sprint_stop_min_decel", sc5.kins["DA"]) == p["sprint_stop_min_decel_q10"]
    assert DF.tier_param(p, "sprint_stop_min_decel", sc3.kins["DA"]) == p["sprint_stop_min_decel"]


def test_t13_sprint_stop_at_sigma_0_5():
    def make(sd):
        sp = profile_path(4.5, 1.1, (1.6, 1.2), (5.45, 1.1), 6.0, 5.2, 8.0)
        spec = {
            "actors": {
                "P": {"team": "O", "wp": still(5.6, 4.6)},
                "A": {"team": "O", "wp": still(6.4, 0.9)},
                "DP": {"team": "D", "wp": still(4.9, 4.1)},
                "DA": {"team": "D", "wp": still(1.6, 1.2)},
            },
            "ball": {"held": [(0, 1.0, "P"), (1.4, 5, "A")], "flights": [(1.0, 1.4, "P", "A")]},
        }
        return build(spec, 4.5, seed=sd, sigma=0.5, paths={"DA": sp})

    def check(truth, sc):
        A = anchors(**{"pass": passes((1.0, 1.4, "P", "A"))})
        return find(DF.detect_closeout_profile(sc, anchors=A), "closeout_sprint_stop", defender="DA")

    # d' ~2 between the classes at q10, so this is a rate test: 6/10 now, baseline 6/20 (12 called choppy) with q30 edges
    assert hits_over_seeds(make, check, seeds=range(1, 11)) >= 5


def test_t13_subnoise_rungs_abstain_in_high_noise_tier():
    truth, sc = build(help_spec(mv(1.15, D0, (-2.1, 4.6), 0.1, (-2.8, 4.6)), mv(1.0, (3.0, 6.0), (1.5, 2.5)),
                                mv(1.0, (3.3, 6.6), (1.8, 3.1))), 4.0, sigma=0.5)
    assert DF.detect_minor_excursion(sc, anchors=drive(1.0)) == []
    assert DF.detect_step_release(sc, anchors=drive(1.0)) == []


def test_t14_sigma_rel_floor_scales_with_noise():
    _, sc2 = build(closeout_spec(), 4.5, sigma=0.2)
    _, sc5 = build(closeout_spec(), 4.5, sigma=0.5)
    p = DF.merged_params("closeout")
    f2 = DF.rel_floor(p, sc2.kins["DA"], sc2.kins["A"])
    f5 = DF.rel_floor(p, sc5.kins["DA"], sc5.kins["A"])
    assert abs(f2 - p["k_floor"] * 0.2) <= 0.04 and abs(f5 - p["k_floor"] * 0.5) <= 0.06
    assert DF.rel_floor(p) >= p["sigma_rel_min"]


def co_spec(start=(2.0, 1.0), end=(5.4, 1.1), t=1.15):
    return {
        "actors": {
            "P": {"team": "O", "wp": still(5.6, 4.6)},
            "A": {"team": "O", "wp": still(6.4, 0.9)},
            "DP": {"team": "D", "wp": still(4.9, 4.1)},
            "DA": {"team": "D", "wp": mv(t, start, end)},
        },
        "ball": {"held": [(0, 1.0, "P"), (1.4, 5, "A")], "flights": [(1.0, 1.4, "P", "A")]},
    }


def test_t15_high_side_landing_is_still_a_closeout():
    _, sc = build(co_spec(end=(5.6, 2.15)), 4.5)
    A = anchors(**{"pass": passes((1.0, 1.4, "P", "A"))})
    e = assert_hit(DF.detect_closeout(sc, anchors=A), "closeout", F(1.4), defender="DA", attacker="A")
    assert e.attrs["landing_side"] == "high_side" and "landing_angle" not in e.attrs["gates"]


def test_t16_drop_to_the_ball_side_on_wing_to_corner_pass():
    spec = {
        "actors": {
            "P": {"team": "O", "wp": still(5.6, 4.6)},
            "R": {"team": "O", "wp": still(6.5, 0.9)},
            "DP": {"team": "D", "wp": mv(1.05, (4.9, 4.1), (4.6, 2.9))},
            "DR": {"team": "D", "wp": still(5.9, 0.1)},
        },
        "ball": {"held": [(0, 1.0, "P"), (1.4, 5, "R")], "flights": [(1.0, 1.4, "P", "R")]},
    }
    _, sc = build(spec, 3.5)
    A = anchors(**{"pass": passes((1.0, 1.4, "P", "R"))})
    assert_hit(DF.detect_jump_to_ball(sc, anchors=A), "jump_to_ball", F(1.0), defender="DP", passer="P")


def test_t17_nail_helper_recovers_to_his_own_man():
    spec = {
        "actors": {
            "H": {"team": "O", "wp": still(0, 7.5)},
            "A": {"team": "O", "wp": still(5.5, 4.5)},
            "C": {"team": "O", "wp": still(6.4, 0.9)},
            "DH": {"team": "D", "wp": still(0, 6.5)},
            "DC": {"team": "D", "wp": still(3.6, 4.6)},
            "D": {"team": "D", "wp": mv(1.0, (1.0, 5.0), (5.6, 1.4, 1.3))},
        },
        "ball": {"held": [(0, 5, "H")]},
    }
    truth, sc = build(spec, 4.0)
    jt = DF.joint_top1(sc)
    assert jt["D"][F(0.5)] == "C"  # the per-defender HMM gives D the ball handler; the joint assignment gives C
    t0 = first(v_toward(truth, "D", "C") >= 1.5)
    assert_hit(DF.detect_recover(sc), "recover", t0, defender="D", attacker="C")  # baseline 0/20


def test_t18_guard_two_hold_is_not_split():
    spec = {
        "actors": {
            "P": {"team": "O", "wp": still(5.6, 4.6)},
            "A1": {"team": "O", "wp": still(-5.5, 4.6)},
            "A2": {"team": "O", "wp": still(-6.4, 0.8)},
            "DP": {"team": "D", "wp": still(4.9, 4.0)},
            "D": {"team": "D", "wp": still(-5.0, 2.7)},
        },
        "ball": {"held": [(0, 5, "P")]},
    }

    def make(sd):
        return build(spec, 3.0, seed=sd)

    assert hits_over_seeds(make, lambda tr, sc: len(find(DF.detect_guard_two(sc), "guard_two", defender="D")) == 1) == 6


def test_t19_shared_parameters_can_be_overridden():
    _, sc = sc_screen("drop_standard")
    A = screen_anchor()
    DF.detect_drop_coverage(sc, anchors=A, level_max=0.7)
    DF.detect_show(sc, anchors=A, hard_lat_min=0.9)
    DF.detect_blitz(sc, anchors=A, blitz_depth_max=0.4)
    DF.detect_xball_path(sc, anchors=A, class_margin=0.2)
    DF.detect_ice(sc, anchors=A, u_min_speed=1.2)
    DF.detect_tag(sc, anchors=A, cross_back_s=0.4)
    _, sc2 = sc_closeout()
    DF.detect_closeout_length(sc2, chord_min=2.4)
    DF.detect_closeout_profile(sc2, chord_min=2.4)
    with pytest.raises(TypeError):
        DF.detect_drop_coverage(sc, anchors=A, not_a_param=1)
    # the item's own value wins over a shared name, and an override reaches the detector
    assert DF.merged_params("closeout_length", "closeout")["chord_min"] == DF.params_of("closeout")["chord_min"]
    assert DF.detect_closeout(sc2, start_dist_min=9.0) == []


def test_t20_spot_numbers_are_read_from_named_spots():
    assert DF.SPOT_NUM["deny"] == dict(perp_max=0.6, tau_lo=0.05, tau_hi=0.35, dist_max=2.0)
    assert DF.SPOT_NUM["face_guard"] == dict(perp_max=0.6, tau_lo=0.0, tau_hi=0.15, dist_max=0.9)
    assert DF.SPOT_NUM["box_out"] == dict(dist_max=1.0, line_max=0.5)
    assert DF.SPOT_NUM["protect_rim"]["r_max"] == 1.8 and DF.SPOT_NUM["stop_ball"]["dist_max"] == 2.0
    for k in ("pair_max_s",):
        assert k not in DF.params_of("x_out")  # x_out pairs flips with switch.pair_max_s (text says so)
    assert "switch.pair_max_s" in DF.ITEMS["x_out"]["rule"] and "switch.pair_max_s" in DF.ITEMS["rotate"]["rule"]
    assert "stationary_s2" in DF.ITEMS["recover"]["rule"] and "pre_catch_s" in DF.ITEMS["post_double"]["rule"]


def test_t21_no_zero_confidence_events():
    _, sc = sc_closeout()
    p = DF.merged_params("closeout")
    ev = DF.make_event(sc, p, "closeout", {"defender": "DA", "attacker": "A"}, 2, 2, 40, 0.9, ["edge"])
    assert ev is None  # t0 inside the 5-frame segment edge: abstain, no phantom conf-0 label
    out = DF.detect_all(sc)
    assert all(e.conf > 0 for evs in out.values() for e in evs)


def test_changes_loop1_recorded():
    ch = DF.SPEC["changes_loop1"]
    ids = {c["id"] for c in ch}
    for i in range(1, 23):
        assert any(x.startswith(f"DEF-T{i:02d}") for x in ids), i
    assert all({"id", "what", "why", "evidence"} <= set(c) for c in ch)


# --------------------------------------------------------------------------------------
# Loop 2 regression tests (independent confirmer's still_failing / regressions; scenes of the tester's harness)
# --------------------------------------------------------------------------------------
def mirror(spec):
    """x -> -x (the tester runs every scene as written and mirrored)."""
    out = {k: v for k, v in spec.items() if k != "actors"}
    out["actors"] = {a: dict(v, wp=[(t, -x, y) for (t, x, y) in v["wp"]]) for a, v in spec["actors"].items()}
    return out


def co_hits(sd, sigma, det="closeout", kind="closeout", end=(5.4, 1.1), mir=False):
    sp = co_spec(end=end)
    _, sc = build(mirror(sp) if mir else sp, 4.5, seed=sd, sigma=sigma)
    A = anchors(**{"pass": passes((1.0, 1.4, "P", "A"))})
    return any(abs(e.t0 - F(1.4)) <= F(TOL_S) for e in find(DF.DETECTORS[det](sc, anchors=A), kind, defender="DA"))


def test_l2_r1_closeout_recall_at_sigma_0_5():
    # NEW-R1: k_floor 0.8 x sigma_p made the chord gate sqrt(2) x the pair sigma; baseline 7/10 seeds (16/20 harness)
    runs = [(sd, m) for sd in range(1, 11) for m in (False, True)]
    assert sum(co_hits(sd, 0.5, mir=m) for sd, m in runs) >= 18  # baseline 16/20
    assert sum(co_hits(sd, 0.5, "closeout_length", "closeout_short", (4.85, 1.2), m) for sd, m in runs) >= 6  # baseline 4


def test_l2_r1_gate_sigmas_follow_what_they_measure():
    _, sc = build(co_spec(), 4.5, seed=3, sigma=0.5)
    p = DF.merged_params("closeout")
    b = DF._closeouts(sc, p, anchors(**{"pass": passes((1.0, 1.4, "P", "A"))}))[0]
    kd = sc.kins["DA"]
    # chord = one track's displacement: its sigma is the one-track floor, not sqrt(2) x the pair sigma
    assert b["s_chord"] == pytest.approx(DF.sigma_own(kd, b["ts"], b["te"], p))
    assert b["s_chord"] < b["sig"] * math.sqrt(2) - 0.05
    assert b["peak_min"] == p["peak_speed_min_q10"] < p["peak_speed_min"]  # q = 10 tier threshold
    # the global k_floor stays the measured honest one (0.74-0.82 x sigma_p pair error, fix2 floor_meas.py)
    assert DF.GLOBAL["k_floor"] == 0.8 and "k_floor_q10" not in DF.GLOBAL


def sink_spec_h(fill=None):
    """Tester's wing sink on a middle drive (sink_spec) with an optional corner filler DB."""
    return {
        "actors": {
            "H": {"team": "O", "wp": mv(1.0, (0.0, 7.6), (0.3, 2.2))},
            "A": {"team": "O", "wp": still(5.6, 4.6)},
            "B": {"team": "O", "wp": still(6.6, 0.8)},
            "DH": {"team": "D", "wp": mv(1.0, (0.0, 6.7), (0.6, 3.0))},
            "D": {"team": "D", "wp": mv(1.15, (4.4, 4.0), (2.8, 2.6))},
            "DB": {"team": "D", "wp": {"fill": mv(1.3, (5.6, 1.4), (5.4, 2.9)), None: still(5.6, 1.4)}[fill]},
        },
        "ball": {"held": [(0, 5, "H")]},
    }


def sink_truth_t0(truth):
    vx, vy = tvel(truth, "D")
    x, y = truth["D"]
    return first(-(vx * x + vy * y) / np.hypot(x, y) >= 1.0, F(1.0))


def test_l2_r2_sink_and_fill_at_sigma_0_5():
    def make(sd):
        return build(sink_spec_h("fill"), 3.5, seed=sd, sigma=0.5)

    def check_sink(truth, sc):
        t0 = sink_truth_t0(truth)
        return any(abs(e.t0 - t0) <= F(TOL_S) for e in find(DF.detect_sink(sc, anchors=drive(1.0)), "sink", defender="D"))

    def check_sf(truth, sc):
        t0 = sink_truth_t0(truth)
        ev = find(DF.detect_sink_and_fill(sc, anchors=drive(1.0)), "sink_and_fill", sinker="D", filler="DB")
        return any(abs(e.t0 - t0) <= F(TOL_S) and e.conf <= e.attrs["p_emit"] + 1e-9 for e in ev)

    # onset_v_r_q10 re-centres the sink t0 (baseline: 1.0 m/s crossing ~5 frames early, 3/10 here); existence of
    # sink_and_fill = min(sink, fill), conf stays the product (baseline 1/10)
    assert hits_over_seeds(make, check_sink, seeds=range(1, 11)) >= 6
    assert hits_over_seeds(make, check_sf, seeds=range(1, 11)) >= 4

    def make_no(sd):
        return build(sink_spec_h(None), 3.5, seed=sd, sigma=0.5)

    no_fill = lambda tr, sc: not find(DF.detect_sink_and_fill(sc, anchors=drive(1.0)), "sink_and_fill", filler="DB")  # noqa: E731
    assert hits_over_seeds(make_no, no_fill, seeds=range(1, 11)) == 10


def test_l2_r2_sink_and_fill_forwards_global_overrides():
    _, sc = build(sink_spec_h("fill"), 3.5, seed=1)
    e0 = find(DF.detect_sink_and_fill(sc, anchors=drive(1.0)), "sink_and_fill", sinker="D", filler="DB")[0]
    e1 = find(DF.detect_sink_and_fill(sc, anchors=drive(1.0), k_floor=1.6, emit_p_min=0.01), "sink_and_fill",
              sinker="D", filler="DB")[0]
    # the inner SINK's P_cond (first reason) changes with a global override of the call (it got the anchors only)
    assert e1.attrs["reasons"][0] != e0.attrs["reasons"][0]


def tag_spec_h():
    s = side_pnr("over", ("drop", 2.4))
    s["actors"]["S"]["wp"] = mv(1.4, S_W, (1.4, 2.2))
    s["actors"]["C"] = {"team": "O", "wp": still(-6.4, 0.9)}
    s["actors"]["D3"] = {"team": "D", "wp": mv(1.9, (-1.8, 1.4), (0.9, 2.5), 0.15, (-3.8, 1.4))}
    return s


def test_l2_tag_contact_window_in_the_q10_tier():
    A = anchors(screen=[dict(t0=F(1.3), screener="S", handler="H", kind="ball", xball="XB", xbig="XBIG")])

    def make(sd):
        return build(tag_spec_h(), 4.5, seed=sd, sigma=0.5)

    def check(truth, sc):
        t0 = first(tdist(truth, "D3", "S") <= 1.0, F(1.8))
        return any(abs(e.t0 - t0) <= F(TOL_S) for e in find(DF.detect_tag(sc, anchors=A), "tag", tagger="D3"))

    assert hits_over_seeds(make, check, seeds=range(1, 11)) >= 6  # baseline 3/10 (contact found after 1.8 s)


CW_H, CA_H = (5.8, 4.8), (6.6, 0.8)


def line_pos_h(A, B, tau, perp):
    ux, uy = B[0] - A[0], B[1] - A[1]
    L = math.hypot(ux, uy)
    px, py = A[0] + tau * ux, A[1] + tau * uy
    nx, ny = -uy / L, ux / L
    if (px + nx) ** 2 + (py + ny) ** 2 > px**2 + py**2:
        nx, ny = -nx, -ny
    return (px + perp * nx, py + perp * ny)


def dn_spec_h(ball, A, pos, start):
    return {
        "actors": {
            "W": {"team": "O", "wp": still(*ball)},
            "A": {"team": "O", "wp": still(*A)},
            "DW": {"team": "D", "wp": still(ball[0] - 0.6, ball[1] - 0.7)},
            "DA": {"team": "D", "wp": mv(1.0, start, pos)},
        },
        "ball": {"held": [(0, 5, "W")]},
    }


def test_l2_t18_face_guard_t0_not_late():
    spec = dn_spec_h(CW_H, CA_H, line_pos_h(CA_H, CW_H, 0.07, 0.15), (5.0, 2.3))

    def make(sd):
        return build(spec, 3.5, seed=sd)

    def check(truth, sc):
        t0 = first(truth_spot(truth, "face_guard", "DA", "A", "W"))
        return any(abs(e.t0 - t0) <= F(TOL_S) for e in find(DF.detect_face_guard(sc), "face_guard", defender="DA"))

    assert hits_over_seeds(make, check, seeds=range(1, 11)) >= 9  # baseline 5/10: t0 0.33-0.6 s late


def test_l2_t18_deny_on_the_way_in_not_blocked_by_backdated_face_guard():
    WB, WA = (6.5, 0.9), (5.6, 4.6)
    spec = dn_spec_h(WB, WA, line_pos_h(WA, WB, 0.2, 0.3), (4.4, 3.4))

    def make(sd):
        return build(spec, 3.5, seed=sd, sigma=0.2)

    def check(truth, sc):
        t0 = first(truth_spot(truth, "deny_on_the_line", "DA", "A", "W"))
        fg = DF.detect_face_guard(sc)
        assert all(e.attrs["strict_start"] >= e.start for e in fg)
        return any(abs(e.t0 - t0) <= F(TOL_S) for e in find(DF.detect_deny(sc), "deny", defender="DA"))

    assert hits_over_seeds(make, check, seeds=range(1, 11)) >= 8


def trap_spec_h(kind):
    H, D1, D2 = {
        "corner": (still(6.3, 0.9), still(5.6, 1.6), mv(0.9, (3.2, 2.6), (6.0, 2.1))),
        "press": (still(-5.0, 17.0), still(-4.4, 16.0), mv(0.9, (-1.0, 15.0), (-5.3, 15.8))),
    }[kind]
    return {"actors": {"H": {"team": "O", "wp": H}, "D1": {"team": "D", "wp": D1}, "D2": {"team": "D", "wp": D2}},
            "ball": {"held": [(0, 5, "H")]}}


def test_l2_t18_trap_t0_backdated():
    hits, back = 0, []
    for kind in ("corner", "press"):
        for sd in range(1, 11):
            for m in (False, True):
                truth, sc = build(mirror(trap_spec_h(kind)) if m else trap_spec_h(kind), 4.0, seed=sd)
                t0 = first((tdist(truth, "D1", "H") <= 1.5) & (tdist(truth, "D2", "H") <= 1.5) & (tdist(truth, "D1", "D2") <= 2.5))
                ev = find(DF.detect_trap(sc), "trap", d1="D1", d2="D2", handler="H")
                hits += any(abs(e.t0 - t0) <= F(TOL_S) for e in ev)
                back += [e.attrs["backdated_s"] for e in ev]
    assert hits >= 33  # baseline 31 of 40 (entries 0.6-1.0 s late)
    assert max(back) > 0 and max(back) <= F(DF.GLOBAL["backdate_max_s"]) * DT + 1e-9


def sw_spec_h():
    return {
        "actors": {
            "H": {"team": "O", "wp": still(0, 7.6)},
            "A1": {"team": "O", "wp": mv(1.0, (-2.2, 1.0), (2.2, 1.0))},
            "A2": {"team": "O", "wp": mv(1.2, (0.0, 2.2), (-2.8, 4.2))},
            "DH": {"team": "D", "wp": still(0, 6.6)},
            "D1": {"team": "D", "wp": mv(1.0, (-1.6, 1.6), (-0.6, 1.9), (-2.3, 3.6))},
            "D2": {"team": "D", "wp": mv(1.1, (0.4, 2.8), (1.8, 1.6))},
        },
        "ball": {"held": [(0, 5, "H")]},
    }


def test_l2_switch_exchange_not_at_the_clip_start():
    # the confirmer blamed a left-censored HMM run; the flips are at frames 48-52 in every run. The early t0 came from
    # the closest-approach search catching an AR(1) dip while both defenders still stood (true dip only 0.56 m)
    def make(sd):
        return build(sw_spec_h(), 5.0, seed=sd)

    def check(truth, sc):
        dd = tdist(truth, "D1", "D2")
        t0 = F(1.0) + int(np.argmin(dd[F(1.0) : F(3.0)]))
        ev = DF.detect_switch(sc)
        return len(ev) == 1 and abs(ev[0].t0 - t0) <= F(TOL_S)

    assert hits_over_seeds(make, check, seeds=range(1, 11)) == 10  # baseline 8/10 (t0 at frames 5-15)


def test_l2_show_ambiguous_class_abstains():
    _, sc = build(side_pnr("over", ("hard_hedge", None)), 4.5, seed=2, sigma=0.2)
    A = anchors(screen=[dict(t0=F(1.3), screener="S", handler="H", kind="ball", xball="XB", xbig="XBIG")])
    assert DF.detect_show(sc, anchors=A, class_margin_min=1.01) == []  # no class margin is ever enough
    assert find(DF.detect_show(sc, anchors=A, class_margin_min=0.0), "hard_hedge") or find(
        DF.detect_show(sc, anchors=A, class_margin_min=0.0), "soft_show"
    )
    assert DF.params_of("ball_screen")["class_margin_min"] == 0.2


def test_l2_high_noise_tier_abstains_listed_kinds():
    _, sc5 = build(co_spec(), 4.5, seed=1, sigma=0.5)
    _, sc3 = build(co_spec(), 4.5, seed=1, sigma=0.3)
    p = DF.merged_params("face_guard")
    for kind in ("face_guard", "blitz", "hard_hedge", "post_front", "lob_protection", "dig", "stunt"):
        assert kind in p["high_noise_abstain_kinds"]
    args = ({"defender": "DA", "attacker": "A"}, 60, 60, 100, 0.9, ["r"])
    assert DF.make_event(sc5, p, "face_guard", *args) is None
    assert DF.make_event(sc3, p, "face_guard", *args) is not None
    assert DF.make_event(sc5, p, "deny", *args) is not None  # not listed: deny keeps emitting at sigma 0.5
    spec = dn_spec_h(CW_H, CA_H, line_pos_h(CA_H, CW_H, 0.07, 0.15), (5.0, 2.3))
    _, scf = build(spec, 3.5, seed=6, sigma=0.5)
    assert DF.detect_face_guard(scf) == []


def test_changes_loop2_recorded():
    ch = DF.SPEC["changes_loop2"]
    ids = " ".join(c["id"] for c in ch)
    for k in ("NEW-R1", "NEW-R2", "DEF-T18", "SWITCH", "SHOW", "HIGH-NOISE", "TAG", "DEF-T22"):
        assert k in ids, k
    assert all({"id", "what", "why", "evidence"} <= set(c) for c in ch)


# --------------------------------------------------------------------------------------
# Loop 4: real-data failure modes (2015-16 SportVU calibration) reproduced on synthetic scenes; no real data here
# --------------------------------------------------------------------------------------
def test_l4_possession_guard_defence_has_ball():
    """L4-POSSESSION: SportVU stretches (and clips cut across a rebound / steal) contain possessions of the labelled
    defence. The face-guard scene with the ball held by a DEFENDER is no face guard, and the abstention is reported."""
    spec = deny_spec(FACE_POS)
    spec["ball"] = {"held": [(0, 4, "DP")]}
    _, sc = build(spec, 3.5, sigma=0.1)  # P stays 0.9 m from the ball: holder for the face-guard geometry
    assert DF.defense_has_ball(sc).all()
    assert DF.detect_face_guard(sc) == []
    out = DF.detect_all(sc)
    assert all(not evs for k, evs in out.items() if k != "abstained")
    assert any(e.kind == "abstain_dposs:face_guard" and e.conf == 0.0 for e in out["abstained"])
    # control: the same scene with the ball at the offence keeps the face guard and has no dposs abstention
    _, sc2 = build(deny_spec(FACE_POS), 3.5, sigma=0.1)
    assert not DF.defense_has_ball(sc2).any()
    assert find(DF.detect_face_guard(sc2), "face_guard", defender="DA")


def test_l4_possession_guard_switches_after_one_second():
    """Control changes only after >= possession_share of a possession_hold_s window: a 0.5 s touch by a defender
    (deflection) is no change; a kept ball changes possession from the first control frame. The controller (0.9 m from
    the nearest opponent) clears the 0.5 m margin at sigma 0.1; the noise margin is checked by the sigma 0.5 harness."""
    spec = deny_spec(DENY_POS)
    spec["ball"] = {"held": [(0, 1.5, "P"), (1.5, 2.0, "DP"), (2.0, 3.5, "P")]}
    _, sc = build(spec, 3.5, sigma=0.1)
    assert not DF.defense_has_ball(sc).any()
    spec["ball"] = {"held": [(0, 1.5, "P"), (1.5, 3.5, "DP")]}
    _, sc = build(spec, 3.5, sigma=0.1)
    m = DF.defense_has_ball(sc)
    assert not m[: F(1.4)].any() and m[F(1.6) :].all()


def g2_screen_spec():
    """L4-G2-SEP: a defender between a screener and the man he screens for (1.6 m apart), nobody else near."""
    return {
        "actors": {
            "P": {"team": "O", "wp": still(6.5, 0.8)},
            "A1": {"team": "O", "wp": still(-0.8, 6.0)},
            "A2": {"team": "O", "wp": still(0.8, 6.0)},
            "DP": {"team": "D", "wp": still(5.8, 1.3)},
            "D": {"team": "D", "wp": still(0.0, 5.5)},
        },
        "ball": {"held": [(0, 4, "P")]},
    }


def test_l4_guard_two_needs_separated_attackers():
    _, sc = build(g2_screen_spec(), 3.0)
    assert DF.detect_guard_two(sc) == []
    truth, sc = build(g2_spec(True), 3.0)  # 6 m apart: still guard-two
    assert_hit(DF.detect_guard_two(sc), "guard_two", 0, defender="D", a1="A1", a2="A2")


def cover_two_spec(outnumbered=True):
    """L4-G2-OUTNUMBERED: two attackers beyond half court, D between them; the other defenders either trail the play
    (farther from the rim: a 2-on-1) or are already back (closer to the rim: a backcourt pick-up, no numbers advantage)."""
    ys = (19.0, 20.0) if outnumbered else (6.0, 8.0)
    return {
        "actors": {
            "H": {"team": "O", "wp": still(-2.5, 14.5)},
            "A2": {"team": "O", "wp": still(2.5, 14.5)},
            "D": {"team": "D", "wp": still(0.0, 13.5)},
            "X1": {"team": "D", "wp": still(-3.0, ys[0])},
            "X2": {"team": "D", "wp": still(3.0, ys[1])},
            "B1": {"team": "O", "wp": still(-4.0, ys[1] + 1.0)},
        },
        "ball": {"held": [(0, 3, "H")]},
    }


def test_l4_cover_two_needs_outnumbered_defender():
    _, sc = build(cover_two_spec(True), 2.5)
    e = find(DF.detect_guard_two(sc), "guard_two", defender="D")
    assert e and e[0].attrs["variant"] == "cover_two"
    _, sc = build(cover_two_spec(False), 2.5)
    assert find(DF.detect_guard_two(sc), "guard_two", defender="D") == []


def test_l4_trap_not_at_the_rim():
    """L4-TRAP-RIM: a putback under the rim with two defenders within 1 m (ball over the rim, handler in the restricted
    area) is no trap; the same three bodies on the sideline are (trap_spec)."""
    spec = {
        "actors": {
            "H": {"team": "O", "wp": still(0.3, 0.6)},
            "D1": {"team": "D", "wp": still(-0.5, 0.9)},
            "D2": {"team": "D", "wp": still(0.9, 1.3)},
        },
        "ball": {"held": [(0, 4, "H")]},
    }
    _, sc = build(spec, 3.0)
    assert DF.detect_trap(sc) == []


def test_l4_trap_not_on_a_drive():
    """L4-TRAP-MOVING: a handler driving past two defenders who run with him (both within 1.5 m, 3+ m/s) is not trapped."""
    spec = {
        "actors": {
            "H": {"team": "O", "wp": mv(0.5, (6.0, 9.0), (1.5, 3.0, 1.2))},
            "D1": {"team": "D", "wp": mv(0.5, (5.4, 8.4), (1.0, 2.5, 1.2))},
            "D2": {"team": "D", "wp": mv(0.5, (6.8, 8.3), (2.3, 2.4, 1.2))},
        },
        "ball": {"held": [(0, 4, "H")]},
    }
    truth, sc = build(spec, 3.5)
    assert np.max(np.hypot(*tvel(truth, "H"))) > 3.0
    assert DF.detect_trap(sc) == []


def post_shot_spec(shot=True):
    """L4-TRAP-SHOT: a post man (3 m from the rim) held by two defenders for 2.4 s who then shoots (the ball reaches
    the rim, where a third defender waits to rebound) vs passes out to a wing teammate."""
    return {
        "actors": {
            "H": {"team": "O", "wp": still(2.6, 1.6)},
            "W": {"team": "O", "wp": still(7.0, 4.5)},
            "D1": {"team": "D", "wp": still(1.8, 1.0)},
            "D2": {"team": "D", "wp": mv(0.6, (5.0, 4.0), (3.4, 2.4))},
            "D3": {"team": "D", "wp": still(-0.2, -0.3)},
            "D4": {"team": "D", "wp": still(7.5, 6.5)},
        },
        "ball": {"held": [(0, 3.0, "H")], "flights": [(3.0, 3.6, "H", "D3" if shot else "W")]}
        | ({} if shot else {"held": [(0, 3.0, "H"), (3.6, 5.0, "W")]}),
    }


def test_l4_trap_not_on_a_post_shot():
    """L4-TRAP-SHOT: two defenders on a post man whose own shot reaches the rim is a contested post move, not a trap;
    the same hold ended by a pass out is a trap (real SportVU: 14 of 23 post-area 'traps' ended in the handler's shot)."""
    hit_shot = hit_pass = 0
    for sd in range(1, 5):
        _, sc = build(post_shot_spec(True), 5.0, seed=sd)
        hit_shot += bool(find(DF.detect_trap(sc), "trap", handler="H"))
        _, sc = build(post_shot_spec(False), 5.0, seed=sd)
        hit_pass += bool(find(DF.detect_trap(sc), "trap", handler="H"))
    assert hit_shot == 0 and hit_pass >= 3


def big_spec(ball_y=8.0, pos=(0.8, 1.75)):
    """L4-PERIMETER: a big standing 1.1 m from the rim, his defender on his ball side 0.75 m away, ball at the top."""
    return {
        "actors": {
            "P": {"team": "O", "wp": still(0.0, ball_y)},
            "A": {"team": "O", "wp": still(0.5, 1.0)},
            "DP": {"team": "D", "wp": still(0.0, ball_y - 0.9)},
            "DA": {"team": "D", "wp": still(*pos)},
        },
        "ball": {"held": [(0, 4, "P")]},
    }


def test_l4_post_area_is_not_face_guard_or_deny():
    truth, sc = build(big_spec(), 3.0)
    assert truth_spot(truth, "face_guard", "DA", "A", "P").all()  # the named spot holds: ownership, not geometry
    assert DF.detect_face_guard(sc) == [] and DF.detect_deny(sc) == []
    assert find(DF.detect_post_position(sc), "post_front", defender="DA", post="A")


def test_l4_no_face_guard_with_ball_in_backcourt():
    spec = deny_spec(FACE_POS)
    spec["actors"]["P"]["wp"] = still(0.0, 16.0)
    spec["actors"]["DP"]["wp"] = still(0.0, 15.1)
    spec["actors"]["DA"]["wp"] = still(5.2, 5.3)  # face_guard spot toward the backcourt ball (tau 0.07, 0.85 m)
    _, sc = build(spec, 3.5)
    assert DF.detect_face_guard(sc) == []


def test_l4_cutter_is_not_posting():
    """L4-POST: a man cutting through the post area (3+ m/s) with his defender on his ball side is not a post hold."""
    spec = {
        "actors": {
            "P": {"team": "O", "wp": still(5.5, 6.0)},
            "A": {"team": "O", "wp": mv(0.3, (-5.0, 1.0), (5.0, 1.0))},
            "DP": {"team": "D", "wp": still(4.8, 5.4)},
            "D": {"team": "D", "wp": mv(0.3, (-5.0, 1.8), (5.0, 1.8))},
        },
        "ball": {"held": [(0, 3.5, "P")]},
    }
    truth, sc = build(spec, 3.0)
    assert np.max(np.hypot(*tvel(truth, "A"))) > 3.0
    assert [e for e in DF.detect_post_position(sc) if e.actors["defender"] == "D"] == []


def test_l4_no_rotation_in_the_backcourt():
    """L4-FLIP-HALFCOURT: the rotate scene shifted 11 m up the floor (ball beyond half court) is a transition pick-up."""
    spec = rotate_spec(True)
    for a in spec["actors"].values():
        a["wp"] = [(t, x, y + 11.0) for t, x, y in a["wp"]]
    _, sc = build(spec, 5.0)
    assert DF.detect_rotate(sc) == []


def test_l4_no_rotation_in_the_rebound_phase(monkeypatch):
    """L4-FLIP-REBOUND: the same matchup change while a shot reaches the rim is a rebound assignment (hit the nearest),
    not a rotation; without the rule the scene would give a rotate."""
    def run():
        spec = rotate_spec(True)
        spec["actors"]["R"] = {"team": "O", "wp": still(0.3, 0.3)}  # tip / putback man under the rim
        spec["ball"] = {"held": [(0, 2.4, "H"), (2.8, 5, "R")], "flights": [(2.4, 2.8, "H", "R")]}
        _, sc = build(spec, 5.0)
        return find(DF.detect_rotate(sc), "rotate", defender="D1")

    assert run() == []
    monkeypatch.setitem(DF.GLOBAL, "rim_phase_back_s", 0.0)
    monkeypatch.setitem(DF.GLOBAL, "rim_phase_fwd_s", 0.0)
    assert run()


def test_l4_q10_abstention_is_reported():
    """L2-HIGH-NOISE-TIER kinds abstain in the q = 10 tier; loop 4 reports them in detect_all['abstained']."""

    def make(sd):
        return build(post_spec(POST_POS["post_front"], enter=True), 3.5, seed=sd, sigma=0.55)

    def check(truth, sc):
        if not DF.high_noise(sc.kins["D"]):
            return False
        out = DF.detect_all(sc)
        return not out["post_position"] and any(e.kind.startswith("abstain_q10:post_") for e in out["abstained"])

    assert hits_over_seeds(make, check, seeds=range(1, 4)) >= 2


def test_l4_q10_lob_protection_abstention_is_reported():
    """L4-Q10-REPORT: lob_protection rides on front holds; when the hold abstains in the q = 10 tier the
    lob-protection label is reported as abstained too (real sigma 0.5 run: lob_protection was silently empty)."""

    def make(sd):
        return build(post_spec(POST_POS["post_front"], enter=True), 3.5, seed=sd, sigma=0.55)

    def check(truth, sc):
        if not DF.high_noise(sc.kins["D"]):
            return False
        out = DF.detect_all(sc)
        return not out["lob_protection"] and any(e.kind == "abstain_q10:lob_protection" for e in out["abstained"])

    assert hits_over_seeds(make, check, seeds=range(1, 4)) >= 2


def test_changes_loop4_recorded():
    ch = DF.SPEC["changes_loop4"]
    ids = {c["id"].split()[0] for c in ch}
    for need in ("L4-POSSESSION", "L4-TRAP-RIM", "L4-TRAP-MOVING", "L4-G2-SEP", "L4-G2-OUTNUMBERED", "L4-PERIMETER",
                 "L4-POST", "L4-FLIP-HALFCOURT", "L4-FLIP-REBOUND", "L4-Q10-REPORT"):
        assert need in ids
    for c in ch:
        assert c["what"] and c["why"] and c["evidence"]


# --------------------------------------------------------------------------------------
# Every registered detector is covered by a positive test above (guard against silent additions)
# --------------------------------------------------------------------------------------
COVERED = {
    "matchup",
    "def_locomotion",
    "closeout",
    "closeout_length",
    "closeout_profile",
    "closeout_fly_by",
    "recover",
    "minor_excursion",
    "step_release",
    "stunt",
    "dig",
    "help_and_recover",
    "sink",
    "jump_to_ball",
    "deny",
    "face_guard",
    "beaten",
    "contain",
    "back_pressure",
    "box_out",
    "get_back",
    "safety_back",
    "rotate",
    "switch",
    "x_out",
    "sink_and_fill",
    "guard_two",
    "trap",
    "xball_path",
    "drop_coverage",
    "show",
    "blitz",
    "ice",
    "tag",
    "offball_screen_coverage",
    "post_position",
    "lob_protection",
    "post_double",
    "protect_rim",
    "stop_ball",
    "transition_matched",
    "set_def",
    "press_pickup",
}


def test_every_detector_has_tests():
    assert set(DF.DETECTORS) == COVERED


def test_detect_all_runs():
    _, sc = sc_closeout()
    out = DF.detect_all(sc)
    assert set(out) == set(DF.DETECTORS) | {"abstained"}
    assert out["closeout"] and all(0.0 <= e.conf <= 1.0 for evs in out.values() for e in evs)


def test_changes_loop5_recorded():
    """L5-DEF-T22: shared BLAS setup (tests/movement/conftest.py) and the batched RTS inverse are journalled."""
    ch = DF.SPEC["changes_loop5"]
    assert [c["id"].split()[0] for c in ch] == ["L5-DEF-T22"] and all(ch[0][k] for k in ("what", "why", "evidence"))
    assert str(DF.SPEC["version"]) in ("0.3.1", "0.3.2")  # 0.3.2: changes_decisions_oct25 (OD-6)


def test_od6_switch_definition_pending_recorded():
    """OD-6 (owner decision 25 Oct 2026): hard vs soft switch is pending agreement with MSU staff (open item owned by
    the owner); no behaviour change - the switch intensity params are the 0.3.1 values."""
    ch = {c["id"].split()[0]: c for c in DF.SPEC["changes_decisions_oct25"]}
    assert set(ch) == {"OD-6", "version"} and all(ch["OD-6"][k] for k in ("what", "why", "evidence"))
    assert "25 Oct" in ch["OD-6"]["why"] and str(DF.SPEC["version"]) == "0.3.2"
    sw = next(it for it in DF.SPEC["items"] if it["id"] == "switch")
    assert {k: sw["params"][k]["value"] for k in ("hard_window_s", "hard_from_min", "hard_to_max", "soft_hold_s",
                                                  "soft_cushion_min", "soft_lambda_min")} == \
        {"hard_window_s": 0.8, "hard_from_min": 1.5, "hard_to_max": 0.8, "soft_hold_s": 1.0, "soft_cushion_min": 1.2,
         "soft_lambda_min": 0.5}
    assert any("OD-6" in c for c in sw["conflicts_resolved"]) and any("OD-6" in q for q in DF.SPEC["open_questions"])
