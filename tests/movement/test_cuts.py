"""Acceptance tests (validation tier V0) for the cuts and off-ball paths family.

Every detector in tools/specgen/movement/detectors/cuts.py gets at least one positive and one
negative synthetic scenario. Three layers:

1. Smoke cases (CASES): sigma_p 0.3 m, seeds 1 and 2. A positive check asserts the event kind, the
   actor in its role, t0 within +-0.3 s of the scenario truth and conf in [min_conf, 1]. A negative
   check asserts that no event of that kind names the actor.
2. Noise sweep (loop 1, fix F15): every case over 10 seeds x sigma_p (0.2, 0.3, 0.5) plus mirrored
   copies (x -> -x) at sigma_p 0.3, matched as in cu_storage_eval (same kind and actor, |t0 error|
   <= 0.5 s), with per-detector recall floors and negative fire-rate ceilings. An exact-mirror test
   checks that mirrored noisy tracks give identical events.
3. Regression tests for the independent tester's loop-1 failures F01-F21 (scenarios ported from the
   tester's harness, scratchpad movement/test_cuts/scenarios.py).

Every scenario has realistic speeds: the truth peak speed of every actor is <= 7.5 m/s (min-jerk legs
peak at 1.875 x the leg mean, so cut legs are timed at <= 3.7 m/s mean).

Court frame: attacked-rim frame, metres (rim at the origin, +y up the floor).
Actors use either 'wp' waypoints (t_s, x_m, y_m), with minimum-jerk motion that stops at each waypoint
(sim.path), or 'start' + 'legs' [(t0, t1, [points], profile)], a Chaikin-smoothed polyline traversed
with one min-jerk ('mj') or trapezoidal ('trap') arc-length profile, so curved paths do not stop.
"""
import math
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "movement"))
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "named_spots"))

import mvlib  # noqa: E402
import sim  # noqa: E402
from detectors import cuts  # noqa: E402

DT = mvlib.DT
SIGMA = 0.3
SEEDS = (1, 2)
T0_TOL_S = 0.3
SWEEP_SIGMAS = (0.2, 0.3, 0.5)
SWEEP_SEEDS = tuple(range(10))
SWEEP_TOL_S = 0.5  # cu_storage_eval match tolerance
MAX_TRUTH_MPS = 7.5


# --------------------------------------------------------------------------------------
# Scenario builder
# --------------------------------------------------------------------------------------
def O(*wp):
    return {"team": "O", "wp": list(wp)}


def D(*wp):
    return {"team": "D", "wp": list(wp)}


def OL(start, *legs):
    """Offensive actor with smooth legs: start (x, y), legs (t0, t1, [points], profile='mj')."""
    return {"team": "O", "start": start, "legs": list(legs)}


def DL(start, *legs):
    return {"team": "D", "start": start, "legs": list(legs)}


def arc(cx, cy, R, a0, a1, t0, t1, n):
    """Waypoints along a circular arc (angles in degrees), evenly spaced in time."""
    out = []
    for i in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * i / n)
        out.append((t0 + (t1 - t0) * i / n, cx + R * math.cos(a), cy + R * math.sin(a)))
    return out


def arc_pts(cx, cy, R, a0, a1, n):
    """Points along a circular arc (degrees), excluding the start point."""
    return [(cx + R * math.cos(math.radians(a0 + (a1 - a0) * i / n)), cy + R * math.sin(math.radians(a0 + (a1 - a0) * i / n)))
            for i in range(1, n + 1)]


def _chaikin(pts, it=3):
    pts = [np.array(p, float) for p in pts]
    if len(pts) < 3:
        return pts
    for _ in range(it):
        out = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            out += [0.75 * a + 0.25 * b, 0.25 * a + 0.75 * b]
        out.append(pts[-1])
        pts = out
    return pts


def _profile(s, kind):
    if kind == "mj":
        return 10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5
    if isinstance(kind, tuple) and kind[0] == "pace":
        # loop 7: two paces without a stop (time fraction tf covers distance fraction df, then the rest), trapezoid
        # ramps at both ends and a 0.1-time-fraction blend at the change of pace (a jog that bursts)
        _, tf, df = kind
        v = np.where(s < tf, df / tf, (1 - df) / (1 - tf)) * np.minimum(1.0, np.minimum(s, 1 - s) / 0.15 + 0.02)
        k = max(1, int(round(0.1 * (len(s) - 1))))
        v = np.convolve(np.pad(v, k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="same")[k:-k]
        d = np.concatenate([[0.0], np.cumsum(0.5 * (v[1:] + v[:-1]) * np.diff(s))])
        return d / d[-1]
    a = 0.15  # trapezoid: accelerate over the first 15 %, decelerate over the last 15 % of the time
    v = 1.0 / (1 - a)
    return np.where(s < a, 0.5 * v / a * s ** 2,
                    np.where(s > 1 - a, 1 - 0.5 * v / a * (1 - s) ** 2, 0.5 * v * a + v * (s - a)))


def _legs_path(actor, n):
    x = np.full(n, float(actor["start"][0]))
    y = np.full(n, float(actor["start"][1]))
    cur = np.array(actor["start"], float)
    for leg in actor.get("legs", []):
        t0, t1, pts = leg[0], leg[1], leg[2]
        kind = leg[3] if len(leg) > 3 else "mj"
        ia, ib = int(round(t0 / DT)), min(n - 1, int(round(t1 / DT)))
        P = np.array(_chaikin([cur] + [np.array(p, float) for p in pts]))
        cum = np.concatenate([[0], np.cumsum(np.hypot(np.diff(P[:, 0]), np.diff(P[:, 1])))])
        d = _profile(np.linspace(0, 1, ib - ia + 1), kind) * cum[-1]
        x[ia:ib + 1] = np.interp(d, cum, P[:, 0])
        y[ia:ib + 1] = np.interp(d, cum, P[:, 1])
        x[ib:], y[ib:] = P[-1, 0], P[-1, 1]
        cur = P[-1]
    return x, y


def _actor_path(actor, n):
    return sim.path(actor["wp"], n) if "wp" in actor else _legs_path(actor, n)


def scenario(spec, duration_s, sigma_p, seed):
    """sim.scenario with smooth-leg actors; identical to sim.scenario (same RNG order) for 'wp' actors."""
    rng = np.random.default_rng(seed)
    n = int(round(duration_s / DT)) + 1
    truth, tracks = {}, []
    for aid, a in spec["actors"].items():
        x, y = _actor_path(a, n)
        truth[aid] = (x, y)
        tracks.append(sim.observe(x, y, sigma_p, rng, oid=aid, team=a.get("team", "")))
    if "ball" in spec:
        bx, by = np.full(n, np.nan), np.full(n, np.nan)
        for t0, t1, aid in spec["ball"].get("held", []):
            a, b = int(round(t0 / DT)), min(n - 1, int(round(t1 / DT)))
            bx[a:b + 1], by[a:b + 1] = truth[aid][0][a:b + 1], truth[aid][1][a:b + 1]
        for t0, t1, fa, fb in spec["ball"].get("flights", []):
            a, b = int(round(t0 / DT)), min(n - 1, int(round(t1 / DT)))
            s = np.linspace(0, 1, b - a + 1)
            bx[a:b + 1] = truth[fa][0][a] + (truth[fb][0][b] - truth[fa][0][a]) * s
            by[a:b + 1] = truth[fa][1][a] + (truth[fb][1][b] - truth[fa][1][a]) * s
        truth["ball"] = (bx, by)
        tr = sim.observe(np.nan_to_num(bx, nan=0.0), np.nan_to_num(by, nan=0.0), sigma_p * 0.7, rng, oid="ball", role="ball")
        tr.x[np.isnan(bx)] = np.nan
        tr.y[np.isnan(by)] = np.nan
        tracks.append(tr)
    return truth, tracks


def mirror_spec(spec):
    out = {"actors": {}}
    for aid, a in spec["actors"].items():
        b = dict(a)
        if "wp" in a:
            b["wp"] = [(t, -x, y) for t, x, y in a["wp"]]
        else:
            b["start"] = (-a["start"][0], a["start"][1])
            b["legs"] = [tuple([lg[0], lg[1], [(-p[0], p[1]) for p in lg[2]]] + list(lg[3:])) for lg in a.get("legs", [])]
        out["actors"][aid] = b
    if "ball" in spec:
        out["ball"] = spec["ball"]
    return out


def build(spec, dur, seed, sigma=SIGMA, mirror=False, **attrs):
    truth, tracks = scenario(mirror_spec(spec) if mirror else spec, dur, sigma, seed)
    sc = mvlib.build_scene(tracks)
    for k, v in attrs.items():
        setattr(sc, k, v)
    return truth, sc


# ---- truth-time helpers (all mirror-symmetric) ----
def truth_speed(truth, a):
    x, y = truth[a]
    return np.concatenate([[0.0], np.hypot(np.diff(x), np.diff(y)) / DT])


def onset(truth, a, t_from, thr=1.5):
    """First truth frame after t_from with speed >= 1.5 m/s (the CUT onset definition)."""
    sp = truth_speed(truth, a)
    k = int(round(t_from / DT))
    return (k + int(np.argmax(sp[k:] >= thr))) * DT


def closest(truth, a, b, t_lo, t_hi):
    xa, ya = truth[a]
    xb, yb = truth[b]
    k0, k1 = int(round(t_lo / DT)), int(round(t_hi / DT))
    d = np.hypot(xa - xb, ya - yb)[k0:k1 + 1]
    return (k0 + int(np.argmin(d))) * DT


def last_r_ge(truth, a, r, t_hi):
    x, y = truth[a]
    k1 = int(round(t_hi / DT))
    rr = np.hypot(x, y)[:k1 + 1]
    return int(np.flatnonzero(rr >= r)[-1]) * DT


def cross_x(truth, a, t_lo):
    x, _ = truth[a]
    k0 = int(round(t_lo / DT))
    s = np.sign(x[k0:])
    return (k0 + int(np.argmax(s != s[0]))) * DT


def r_cross_in(truth, a, r, t_lo):
    x, y = truth[a]
    k0 = int(round(t_lo / DT))
    rr = np.hypot(x, y)
    return (k0 + int(np.argmax(rr[k0:] <= r))) * DT


def leave_from(truth, a, d, t_lo):
    """First time after t_lo that a is > d from his own position at t_lo."""
    x, y = truth[a]
    k0 = int(round(t_lo / DT))
    dd = np.hypot(x - x[k0], y - y[k0])
    return (k0 + int(np.argmax(dd[k0:] > d))) * DT


TOP = O((0, 0.0, 7.6))
TOPL = OL((0.0, 7.6))


def held(aid, t1=9.0):
    return {"held": [(0, t1, aid)]}


# --------------------------------------------------------------------------------------
# Smoke scenarios: name -> (spec, duration_s, scene attrs). Loop 1 (fix F15): every leg retimed to a
# truth peak <= 7.0 m/s; banana, loop and the transition runs use smooth legs.
# --------------------------------------------------------------------------------------
S = {}

# basket / dive / 45: straight wing-to-rim cut, defender in a normal (rim-side) stance
S["basket"] = ({"actors": {"h": TOP, "c": O((0, 5.3, 5.3), (2.0, 5.3, 5.3), (3.8, 0.8, 0.8)),
                           "d": D((0, 4.5, 4.6), (2.1, 4.5, 4.6), (4.0, 1.6, 1.4))},
                "ball": {"held": [(0, 8, "h")]}}, 6.0, {})
# relocation along the arc (not a cut)
S["arc_slide"] = ({"actors": {"h": TOP, "c": O((0, 5.3, 5.3), (2.0, 5.3, 5.3), (3.2, 3.6, 6.4))},
                   "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# curved rim cut (basket, not dive): bulges 1.2 m off the chord
S["curved_basket"] = ({"actors": {"h": TOP, "c": O((0, 6.0, 4.5), (2.0, 6.0, 4.5), (2.9, 5.2, 1.6), (4.1, 1.2, 0.8))},
                       "ball": {"held": [(0, 8, "h")]}}, 6.0, {})
# rim cut from the slot (m about 67 deg): basket but not 45
S["slot_basket"] = ({"actors": {"h": O((0, -5.3, 5.3)), "c": O((0, 2.8, 7.0), (2.0, 2.8, 7.0), (3.8, 0.4, 0.9))},
                     "ball": {"held": [(0, 8, "h")]}}, 6.0, {})
# front cut: the defender sags toward the baseline, the cutter passes on the ball side
S["front"] = ({"actors": {"h": TOP, "c": O((0, 5.3, 5.3), (2.0, 5.3, 5.3), (3.8, 0.8, 0.8)),
                          "d": D((0, 5.2, 3.4), (2.6, 5.2, 3.4), (4.2, 2.0, 1.2))},
               "ball": {"held": [(0, 8, "h")]}}, 6.0, {})
# backdoor: overplayed wing steps toward the ball, plants, cuts behind to the rim
S["backdoor"] = ({"actors": {"h": O((0, 2.5, 7.2)),
                             "c": O((0, 6.0, 4.6), (1.5, 6.0, 4.6), (2.1, 6.4, 6.0), (2.2, 6.4, 6.0), (4.3, 0.8, 0.8)),
                             "d": D((0, 5.3, 5.3), (1.5, 5.3, 5.3), (2.2, 5.6, 6.7), (2.5, 5.4, 6.4), (4.2, 1.8, 1.6))},
                  "ball": {"held": [(0, 8, "h")]}}, 6.0, {})
# flash: weak-side low post to the high post, ball on the right wing
S["flash"] = ({"actors": {"h": O((0, 5.3, 5.3)), "c": O((0, -2.0, 1.1), (2.0, -2.0, 1.1), (3.2, 0.5, 4.6))},
               "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# V: wing steps in to r 5.0, plants, pops out (about 140 deg)
S["vcut"] = ({"actors": {"h": TOP, "c": O((0, 6.0, 4.5), (2.0, 6.0, 4.5), (2.7, 4.0, 3.0), (2.8, 4.0, 3.0), (3.8, 5.0, 6.5))},
              "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# I: in 1.75 m and straight back out along the same line
S["icut"] = ({"actors": {"h": TOP, "c": O((0, 6.0, 4.5), (2.0, 6.0, 4.5), (2.6, 4.6, 3.45), (2.7, 4.6, 3.45), (3.3, 6.1, 4.6))},
              "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# L: up the lane line from the low post, 90 deg out to the wing
S["lcut"] = ({"actors": {"h": TOP, "c": O((0, 2.0, 1.0), (2.0, 2.0, 1.0), (2.9, 2.0, 4.2), (3.0, 2.0, 4.2), (4.0, 5.5, 4.4))},
              "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# banana: 90 deg arc of radius 5.6 m from the deep wing to near the rim (one smooth leg)
S["banana"] = ({"actors": {"h": TOP, "c": OL((7.46, 4.68), (2.0, 4.5, arc_pts(2.2, 6.6, 5.6, -20.0, -110.0, 16)))},
                "ball": {"held": [(0, 8, "h")]}}, 6.0, {})
# shallow: slot to the ball-side corner, inside the receiver
S["shallow"] = ({"actors": {"h": O((0, 5.3, 5.3)), "c": O((0, 2.5, 7.3), (1.5, 2.5, 7.3), (2.6, 4.3, 4.0), (3.9, 6.95, 0.3))},
                 "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# cut to the weak-side corner (not shallow)
S["weak_corner"] = ({"actors": {"h": O((0, 5.3, 5.3)), "c": O((0, -2.5, 7.3), (1.5, -2.5, 7.3), (2.6, -4.3, 4.0), (3.9, -6.95, 0.3))},
                     "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# weak-side baseline runner
S["baseline"] = ({"actors": {"h": O((0, 5.3, 5.3)), "c": O((0, -6.9, 0.3), (1.5, -6.9, 0.3), (4.2, 2.6, 0.4))},
                  "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
S["midband_run"] = ({"actors": {"h": O((0, 5.3, 5.3)), "c": O((0, -6.0, 3.0), (1.5, -6.0, 3.0), (4.0, 2.6, 3.0))},
                     "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# thru: slot passer to the wing, cuts through the paint to the weak wing
S["thru"] = ({"actors": {"a": O((0, 2.5, 7.2), (2.1, 2.5, 7.2), (3.6, 0.0, 2.5), (5.3, -5.3, 5.3)), "w": O((0, 5.3, 5.3))},
              "ball": {"held": [(0, 2.0, "a"), (2.4, 8, "w")], "flights": [(2.0, 2.4, "a", "w")]}}, 6.5, {})
# pass and stay (no thru, no give-and-go)
S["pass_stay"] = ({"actors": {"a": O((0, 2.5, 7.2)), "w": O((0, 5.3, 5.3))},
                   "ball": {"held": [(0, 2.0, "a"), (2.4, 8, "w")], "flights": [(2.0, 2.4, "a", "w")]}}, 5.0, {})
# give-and-go: pass, rim cut, return pass at the rim
S["give_go"] = ({"actors": {"a": O((0, 2.5, 7.2), (2.1, 2.5, 7.2), (3.9, 0.8, 1.0)), "w": O((0, 5.3, 5.3))},
                 "ball": {"held": [(0, 2.0, "a"), (2.4, 3.4, "w"), (3.8, 8, "a")],
                          "flights": [(2.0, 2.4, "a", "w"), (3.4, 3.8, "w", "a")]}}, 5.5, {})
# curl: around a stationary wing screener into the paint
S["curl"] = ({"actors": {"h": TOP, "s": O((0, 4.0, 3.0)),
                         "u": O((0, 6.5, 0.8), (1.5, 6.5, 0.8), (2.2, 4.9, 2.6), (2.65, 4.3, 4.0), (3.1, 2.8, 3.9), (3.85, 1.5, 1.6))},
              "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# straight: up past a stationary screener without turning
S["straight"] = ({"actors": {"h": TOP, "s": O((0, 3.5, 3.0)), "u": O((0, 2.0, 0.8), (1.8, 2.0, 0.8), (3.6, 5.6, 6.3))},
                  "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# pop-out: lane middle past an elbow screener straight to the ball on the wing
S["pop_out"] = ({"actors": {"h": O((0, 5.6, 5.6)), "s": O((0, 1.5, 4.5)), "u": O((0, 0.2, 2.5), (1.8, 0.2, 2.5), (3.3, 3.8, 6.3))},
                 "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# flare: high post away from the ball (left slot) off a ball-side screener
S["flare"] = ({"actors": {"h": O((0, -3.0, 7.0)), "s": O((0, -0.3, 5.3)), "u": O((0, 0.5, 4.9), (1.8, 0.5, 4.9), (3.0, 4.6, 5.8))},
               "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
S["fade"] = ({"actors": {"h": O((0, -3.0, 7.0)), "u": O((0, 0.5, 4.9), (1.8, 0.5, 4.9), (3.0, 4.6, 5.8))},
              "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# UCLA: slot passes to the same-side wing, cuts off the elbow back screen to the rim
S["ucla"] = ({"actors": {"a": O((0, 1.5, 7.3), (2.1, 1.5, 7.3), (2.95, 2.4, 4.4), (4.05, 0.6, 0.9)), "w": O((0, 5.3, 5.3)),
                         "s": O((0, 1.8, 4.2)), "da": D((0, 1.6, 6.5), (2.1, 1.6, 6.5), (3.05, 2.6, 5.5), (4.3, 1.2, 2.0))},
              "ball": {"held": [(0, 2.0, "a"), (2.4, 8, "w")], "flights": [(2.0, 2.4, "a", "w")]}}, 5.5, {})
# Iverson: wing to wing over two elbow screeners, ball at the top
S["iverson"] = ({"actors": {"h": O((0, 0.0, 8.0)), "s1": O((0, 1.8, 4.2)), "s2": O((0, -1.8, 4.2)),
                            "u": O((0, 5.5, 5.0), (1.5, 5.5, 5.0), (4.5, -5.5, 5.0))},
                 "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
S["iverson_low"] = ({"actors": {"h": O((0, 0.0, 8.0)), "u": O((0, 5.5, 5.0), (1.5, 5.5, 5.0), (3.2, 0.0, 2.3), (4.9, -5.5, 5.0))},
                     "ball": {"held": [(0, 8, "h")]}}, 6.0, {})
# flex: weak corner along the baseline off a weak-side low-post screener
S["flex"] = ({"actors": {"h": O((0, 5.3, 5.3)), "s": O((0, -2.0, 1.0)),
                         "u": O((0, -6.9, 0.4), (1.5, -6.9, 0.4), (2.7, -2.6, 1.3), (3.85, 1.6, 1.0))},
              "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
S["flex_noscreen"] = ({"actors": {"h": O((0, 5.3, 5.3)),
                                  "u": O((0, -6.9, 0.4), (1.5, -6.9, 0.4), (2.7, -2.6, 1.3), (3.85, 1.6, 1.0))},
                       "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# zipper: down screener arrives at r 4, block player straight up to the slot
S["zipper"] = ({"actors": {"h": O((0, -5.3, 5.3)), "s": O((0, 3.0, 6.5), (1.0, 3.0, 6.5), (2.0, 2.6, 3.0)),
                           "u": O((0, 2.0, 0.9), (2.3, 2.0, 0.9), (4.0, 2.9, 7.1))},
                "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
S["zipper_static"] = ({"actors": {"h": O((0, -5.3, 5.3)), "s": O((0, 2.6, 3.0)),
                                  "u": O((0, 2.0, 0.9), (2.3, 2.0, 0.9), (4.0, 2.9, 7.1))},
                       "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# pin-down: screener comes down to (3.6, 2.2), block player up and out to the wing
S["pin_down"] = ({"actors": {"h": O((0, -3.0, 7.0)), "s": O((0, 5.5, 5.5), (1.0, 5.5, 5.5), (2.1, 3.6, 2.2)),
                             "u": O((0, 2.2, 1.0), (2.3, 2.2, 1.0), (3.7, 6.8, 2.8))},
                  "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# turnout: from under the rim around a block screener out to the wing
S["turnout"] = ({"actors": {"h": O((0, -3.0, 7.0)), "s": O((0, 2.2, 1.2)),
                            "u": OL((0.5, 0.5), (2.0, 4.0, [(2.6, 0.3), (6.0, 4.5)]))},
                 "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
S["turnout_high"] = ({"actors": {"h": O((0, -3.0, 7.0)), "s": O((0, 2.2, 3.6)),
                                 "u": OL((0.8, 4.5), (2.0, 4.0, [(2.6, 4.4), (6.0, 4.5)]))},
                      "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# cross screen: left block to right block past a lane screener
S["cross"] = ({"actors": {"h": O((0, 5.3, 5.3)), "s": O((0, 0.0, 1.6)),
                          "u": O((0, -2.0, 0.9), (2.0, -2.0, 0.9), (3.2, 2.0, 1.0))},
               "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
S["cross_noscreen"] = ({"actors": {"h": O((0, 5.3, 5.3)), "u": O((0, -2.0, 0.9), (2.0, -2.0, 0.9), (3.2, 2.0, 1.0))},
                        "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# baseline exit: under the basket out to the corner past a baseline screener
S["bl_exit"] = ({"actors": {"h": O((0, -5.3, 5.3)), "s": O((0, 3.2, 0.2)),
                            "u": O((0, -0.5, 0.9), (2.0, -0.5, 0.9), (4.1, 7.0, 0.9))},
                 "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
S["bl_exit_noscreen"] = ({"actors": {"h": O((0, -5.3, 5.3)), "u": O((0, -0.5, 0.9), (2.0, -0.5, 0.9), (4.1, 7.0, 0.9))},
                          "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# chin: reversal right wing -> left slot, right-slot cutter off the elbow back screen
S["chin"] = ({"actors": {"p": O((0, 5.3, 5.3)), "q": O((0, -2.5, 7.2)), "s": O((0, 1.8, 4.2)),
                         "c": O((0, 2.8, 7.0), (2.7, 2.8, 7.0), (3.4, 2.2, 4.6), (4.5, 0.5, 1.0)),
                         "dc": D((0, 2.6, 7.9), (2.7, 2.6, 7.9), (3.45, 2.4, 5.6), (4.75, 1.0, 2.0))},
              "ball": {"held": [(0, 2.0, "p"), (2.5, 8, "q")], "flights": [(2.0, 2.5, "p", "q")]}}, 5.5, {})
S["chin_nopass"] = ({"actors": {"p": O((0, 5.3, 5.3)), "s": O((0, 1.8, 4.2)),
                                "c": O((0, 2.8, 7.0), (2.7, 2.8, 7.0), (3.4, 2.2, 4.6), (4.5, 0.5, 1.0)),
                                "dc": D((0, 2.6, 7.9), (2.7, 2.6, 7.9), (3.45, 2.4, 5.6), (4.75, 1.0, 2.0))},
                     "ball": {"held": [(0, 8, "p")]}}, 5.5, {})
# loop: 270 deg around a stationary teammate at radius 1.6 m (one smooth leg at about 3 m/s; a 6 m/s orbit
# of radius 1.6 m would need 2.6 g), then up the lane line
S["loop"] = ({"actors": {"h": TOP, "s": O((0, 3.0, 2.5)),
                         "u": OL((3.0, 0.9), (1.8, 4.3, arc_pts(3.0, 2.5, 1.6, -90, 180, 18), "trap"), (4.3, 5.0, [(1.4, 4.5)]))},
              "ball": {"held": [(0, 8, "h")]}}, 5.6, {})
# shuffle: weak-side wing diagonal past an elbow screener to the ball-side block
S["shuffle"] = ({"actors": {"h": O((0, -5.3, 5.3)), "s": O((0, 1.8, 4.1)),
                            "u": O((0, 5.3, 5.3), (1.5, 5.3, 5.3), (2.7, 1.6, 3.1), (3.85, -2.0, 1.0))},
                 "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
S["shuffle_noscreen"] = ({"actors": {"h": O((0, -5.3, 5.3)),
                                     "u": O((0, 5.3, 5.3), (1.5, 5.3, 5.3), (2.7, 1.6, 3.1), (3.85, -2.0, 1.0))},
                          "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# side/slot ball screen: handler dribbles past a stationary screener who then rolls
_BS = {"h": O((0, 5.5, 6.5), (1.5, 5.5, 6.5), (3.0, 2.0, 6.5)),
       "s": O((0, 3.8, 5.8), (2.4, 3.8, 5.8), (3.8, 1.0, 1.5))}
S["blade"] = ({"actors": dict(_BS, k=O((0, 6.95, 0.3), (2.3, 6.95, 0.3), (4.0, 0.8, 0.6))),
               "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
S["shake"] = ({"actors": dict(_BS, k=O((0, 6.95, 0.3), (2.4, 6.95, 0.3), (3.4, 6.7, 3.3))),
               "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# rub: wing cutter brushes a stationary post at speed, the defender is held up
S["rub"] = ({"actors": {"h": TOP, "s": O((0, 2.0, 2.0)), "u": O((0, 5.5, 5.6), (2.0, 5.5, 5.6), (3.9, 1.2, 0.4)),
                        "d": D((0, 5.0, 6.0), (2.0, 5.0, 6.0), (3.15, 2.5, 2.8), (3.85, 2.5, 2.8), (4.65, 1.5, 1.2))},
             "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
S["rub_nopost"] = ({"actors": {"h": TOP, "u": O((0, 5.5, 5.6), (2.0, 5.5, 5.6), (3.9, 1.2, 0.4)),
                               "d": D((0, 5.0, 6.0), (2.0, 5.0, 6.0), (3.15, 2.5, 2.8), (3.85, 2.5, 2.8), (4.65, 1.5, 1.2))},
                    "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
# circle: over the elbows, then down around the elbow player to the rim; ball at the high post
S["circle"] = ({"actors": {"h": O((0, 0.0, 4.8)), "s": O((0, 1.8, 4.2)),
                           "u": O((0, 6.2, 5.2), (1.5, 6.2, 5.2), (2.8, 1.4, 5.4), (2.9, 1.4, 5.4), (4.3, 1.75, 0.4))},
                "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
S["circle_noelbow"] = ({"actors": {"h": O((0, 0.0, 4.8)),
                                   "u": O((0, 6.2, 5.2), (1.5, 6.2, 5.2), (2.8, 1.4, 5.4), (2.9, 1.4, 5.4), (4.3, 1.75, 0.4))},
                        "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# laker: wing enters to the low post and cuts off the post receiver to the rim
S["laker"] = ({"actors": {"a": O((0, 5.3, 5.3), (2.2, 5.3, 5.3), (3.3, 2.9, 2.0), (4.05, 0.5, 0.8)), "p": O((0, 2.2, 1.5))},
               "ball": {"held": [(0, 2.0, "a"), (2.4, 8, "p")], "flights": [(2.0, 2.4, "a", "p")]}}, 5.0, {})
S["laker_wing"] = ({"actors": {"a": O((0, 2.5, 7.2), (2.2, 2.5, 7.2), (3.1, 4.3, 4.6), (4.6, 0.5, 0.8)), "p": O((0, 5.6, 4.6))},
                    "ball": {"held": [(0, 2.0, "a"), (2.4, 8, "p")], "flights": [(2.0, 2.4, "a", "p")]}}, 5.0, {})
# veer: approach the defender, veer 65 deg next to him, accelerate away
S["veer"] = ({"actors": {"h": TOP, "u": O((0, 6.5, 6.0), (1.5, 6.5, 6.0), (2.3, 4.9, 4.6), (2.4, 4.9, 4.6), (3.2, 5.7, 2.0)),
                         "d": D((0, 4.3, 4.1))},
              "ball": {"held": [(0, 8, "h")]}}, 4.6, {})
S["veer_far"] = ({"actors": {"h": TOP, "u": O((0, 6.5, 6.0), (1.5, 6.5, 6.0), (2.3, 4.9, 4.6), (2.4, 4.9, 4.6), (3.2, 5.7, 2.0)),
                             "d": D((0, -4.0, 2.0))},
                  "ball": {"held": [(0, 8, "h")]}}, 4.6, {})
# relocation: wing to slot right after a catch in the corner
S["relocate"] = ({"actors": {"a": TOP, "k": O((0, 6.95, 0.3)), "w": O((0, 5.3, 5.3), (2.6, 5.3, 5.3), (3.6, 2.8, 7.2))},
                  "ball": {"held": [(0, 2.0, "a"), (2.5, 8, "k")], "flights": [(2.0, 2.5, "a", "k")]}}, 5.0, {})
# drives: right-slot drive with a corner lift; left middle drive with a right-wing drift
S["lift"] = ({"actors": {"h": O((0, 3.0, 7.0), (2.0, 3.0, 7.0), (3.5, 1.2, 2.0)), "k": O((0, 6.95, 0.5), (2.4, 6.95, 0.5), (3.4, 6.5, 3.6))},
              "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
S["drift"] = ({"actors": {"h": O((0, -3.0, 7.0), (2.0, -3.0, 7.0), (3.6, -1.0, 1.5)), "w": O((0, 6.0, 3.9), (2.4, 6.0, 3.9), (3.5, 6.95, 0.4))},
               "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# hammer: baseline drive from the left wing, right-wing shooter to the corner off a screener
S["hammer"] = ({"actors": {"h": O((0, -6.3, 3.0), (2.0, -6.3, 3.0), (3.6, -1.3, 0.2)), "s": O((0, 6.2, 2.2)),
                           "w": O((0, 6.0, 4.2), (2.3, 6.0, 4.2), (3.5, 7.0, 0.3))},
                "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# dunker slide: roller enters the lane, weak dunker slides under to the other dunker spot
S["slide"] = ({"actors": {"h": O((0, -5.3, 5.3)), "r": O((0, 0.5, 7.0), (1.5, 0.5, 7.0), (3.1, 0.3, 1.5)),
                          "d": O((0, -2.8, 0.3), (2.4, -2.8, 0.3), (3.9, 2.8, 0.3))},
               "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
S["slide_stay"] = ({"actors": {"h": O((0, -5.3, 5.3)), "r": O((0, 0.5, 7.0), (1.5, 0.5, 7.0), (3.1, 0.3, 1.5)),
                               "d": O((0, -2.8, 0.3))},
                    "ball": {"held": [(0, 8, "h")]}}, 5.0, {})
# fill: corner player cuts, the wing fills the corner
S["fill"] = ({"actors": {"h": TOP, "a": O((0, 6.95, 0.0), (2.0, 6.95, 0.0), (3.7, 1.0, 0.8)),
                         "b": O((0, 5.3, 5.3), (2.6, 5.3, 5.3), (4.1, 6.9, 0.2))},
              "ball": {"held": [(0, 8, "h")]}}, 5.5, {})
S["fill_late"] = ({"actors": {"h": TOP, "a": O((0, 6.95, 0.0), (2.0, 6.95, 0.0), (3.7, 1.0, 0.8)),
                              "b": O((0, 5.3, 5.3), (4.8, 5.3, 5.3), (6.3, 6.9, 0.2))},
                   "ball": {"held": [(0, 8, "h")]}}, 7.0, {})
# sprints to the corner
S["sprint_half"] = ({"actors": {"h": TOP, "p": O((0, 3.5, 6.5), (1.5, 3.5, 6.5), (3.5, 7.0, 0.2))},
                     "ball": {"held": [(0, 8, "h")]}}, 4.5, {})
S["jog_corner"] = ({"actors": {"h": TOP, "p": O((0, 3.5, 6.5), (1.5, 3.5, 6.5), (4.5, 7.0, 0.2))},
                    "ball": {"held": [(0, 8, "h")]}}, 6.0, {})
S["sprint_trans"] = ({"actors": {"h": O((0, 0.0, 20.0), (1.0, 0.0, 20.0), (6.0, 0.0, 8.0)),
                                 "p": OL((6.0, 22.0), (1.0, 5.2, [(7.0, 0.3)], "trap"))},
                      "ball": {"held": [(0, 8, "h")]}}, 6.5, {"possession_t0": 30})
# rim run in transition
S["rim_run"] = ({"actors": {"h": O((0, -3.0, 22.0), (1.0, -3.0, 22.0), (6.5, -2.0, 6.0)),
                            "p": OL((0.5, 24.5), (1.2, 5.6, [(0.3, 1.2)], "trap"))},
                 "ball": {"held": [(0, 9, "h")]}}, 7.5, {"possession_t0": 30})
S["rim_jog"] = ({"actors": {"h": O((0, -3.0, 22.0), (1.0, -3.0, 22.0), (6.5, -2.0, 6.0)),
                            "p": O((0, 0.5, 24.5), (1.2, 0.5, 24.5), (9.0, 0.3, 1.2))},
                 "ball": {"held": [(0, 10, "h")]}}, 10.0, {"possession_t0": 30})
# blind pig: big flashes to the high post and catches, overplayed wing back-cuts, big feeds him
S["blind_pig"] = ({"actors": {"h": O((0, -2.5, 7.2)), "b": O((0, -2.0, 1.0), (1.0, -2.0, 1.0), (2.1, 0.0, 4.4)),
                              "c": O((0, 6.0, 4.6), (1.8, 6.0, 4.6), (2.4, 6.4, 6.0), (2.5, 6.4, 6.0), (4.6, 0.8, 0.8)),
                              "d": D((0, 5.3, 5.3), (1.8, 5.3, 5.3), (2.5, 5.6, 6.7), (2.8, 5.4, 6.4), (4.5, 1.8, 1.6))},
                   "ball": {"held": [(0, 2.0, "h"), (2.4, 3.4, "b"), (3.8, 8, "c")],
                            "flights": [(2.0, 2.4, "h", "b"), (3.4, 3.8, "b", "c")]}}, 6.0, {})
S["blind_pig_nofeed"] = ({"actors": S["blind_pig"][0]["actors"],
                          "ball": {"held": [(0, 2.0, "h"), (2.4, 8, "b")], "flights": [(2.0, 2.4, "h", "b")]}}, 6.0, {})
# wiper: pin-down to the wing, pause, then flare to the deep wing off a second screener
S["wiper"] = ({"actors": {"h": O((0, -3.0, 7.0)), "s2": O((0, 5.5, 5.5), (1.0, 5.5, 5.5), (2.1, 3.6, 2.2)),
                          "s1": O((0, 5.0, 3.6)),
                          "u": O((0, 2.2, 1.0), (2.3, 2.2, 1.0), (3.4, 5.6, 3.2), (4.0, 5.6, 3.2), (5.0, 7.5, 1.6))},
               "ball": {"held": [(0, 8, "h")]}}, 6.0, {})
# a still clip: everyone stands (negative for MOVE / CUT)
S["still"] = ({"actors": {"h": TOP, "c": O((0, 5.3, 5.3)), "k": O((0, 6.95, 0.3))}, "ball": {"held": [(0, 8, "h")]}}, 5.0, {})


# --------------------------------------------------------------------------------------
# Regression scenarios (loop 1), ported from the independent tester's harness (smooth legs)
# --------------------------------------------------------------------------------------
_PASS_W = {"held": [(0, 2.0, "a"), (2.4, 9, "w")], "flights": [(2.0, 2.4, "a", "w")]}
_REV = {"held": [(0, 2.0, "p"), (2.5, 9, "q")], "flights": [(2.0, 2.5, "p", "q")]}
R = {
    # F01: pass then a straight basket cut, nobody in the high post (not UCLA)
    "pass_cut_noscreen": ({"actors": {"a": OL((2.0, 7.3), (2.2, 4.2, [(0.6, 0.9)])), "w": OL((5.3, 5.3))}, "ball": _PASS_W}, 5.5, {}),
    "ucla_top": ({"actors": {"a": OL((0.4, 7.5), (2.2, 4.3, [(0.9, 4.9), (0.5, 0.9)])), "w": OL((5.3, 5.3)), "s": OL((1.9, 4.3)),
                             "da": DL((0.6, 6.6), (2.6, 4.9, [(1.3, 5.6), (1.0, 2.0)]))}, "ball": _PASS_W}, 5.5, {}),
    # F06: wing basket cut passing 1.1 m from a standing post
    "bk_past_post": ({"actors": {"h": TOPL, "p": OL((2.3, 1.0)), "c": OL((5.0, 5.0), (2.0, 4.0, [(0.5, 0.9)]))},
                      "ball": held("h")}, 5.5, {}),
    # F12: pass and face cut, the passer starts 1 m from his man
    "front_pass": ({"actors": {"a": OL((2.6, 7.0), (2.2, 4.3, [(3.4, 5.1), (0.8, 0.9)])), "w": OL((5.3, 5.3)),
                               "da": DL((2.2, 6.1), (2.6, 4.4, [(1.6, 2.6)]))}, "ball": _PASS_W}, 5.5, {}),
    # F09: flare off a ball-side high-post screener the user starts 1.1 m from
    "flare_elbow": ({"actors": {"h": OL((-5.3, 5.3)), "s": OL((0.6, 5.0)), "u": OL((1.6, 4.5), (2.0, 3.6, [(6.0, 3.4)]))},
                     "ball": held("h")}, 5.0, {}),
    "fade_corner": ({"actors": {"h": OL((-5.3, 5.3)), "u": OL((2.4, 5.2), (2.0, 3.6, [(6.7, 2.6)]))}, "ball": held("h")}, 5.0, {}),
    # F10: chin cut (back screen after a reversal) and the same cut without the screener
    "chin_wing": ({"actors": {"p": OL((2.8, 7.0)), "q": OL((-2.8, 7.0)), "s": OL((1.8, 4.3)),
                              "c": OL((5.4, 5.0), (2.6, 4.7, [(2.5, 4.9), (0.6, 0.8)])),
                              "dc": DL((4.6, 5.4), (2.7, 4.9, [(3.6, 5.8), (1.4, 1.8)]))}, "ball": _REV}, 5.5, {}),
    "chin_noscreen": ({"actors": {"p": OL((2.8, 7.0)), "q": OL((-2.8, 7.0)),
                                  "c": OL((5.4, 5.0), (2.6, 4.7, [(2.5, 4.9), (0.6, 0.8)])),
                                  "dc": DL((4.6, 5.4), (2.7, 4.9, [(3.6, 5.8), (1.4, 1.8)]))}, "ball": _REV}, 5.5, {}),
    # F11: the pin-down screener descends 3.4 m, then holds about 1 s before the cutter uses him
    "pindown_wl": ({"actors": {"h": OL((-3.0, 7.0)), "s": OL((5.0, 6.0), (0.8, 2.0, [(3.6, 2.6)])),
                               "u": OL((2.0, 0.8), (2.3, 3.9, [(4.4, 1.9), (6.6, 3.4)]))}, "ball": held("h")}, 5.5, {}),
    # F02 / F03: under the rim, around the lane-line screener, out to the wing
    "turnout_lane": ({"actors": {"h": OL((-3.0, 7.0)), "s": OL((2.0, 2.2)),
                                 "u": OL((-0.4, 0.6), (2.0, 4.2, [(2.6, 1.1), (3.5, 2.3), (5.6, 4.6)]))}, "ball": held("h")}, 5.5, {}),
    "flex_under": ({"actors": {"h": OL((5.3, 5.3)), "s": OL((-2.0, 1.4)),
                               "u": OL((-6.9, 0.4), (1.5, 3.9, [(-3.0, 0.4), (-1.0, 0.6), (1.8, 1.0)]))}, "ball": held("h")}, 5.5, {}),
    # F07: tight curl, block up and around a mid-post screener back down into the lane
    "curl_down": ({"actors": {"h": TOPL, "s": OL((3.6, 2.8)),
                              "u": OL((2.1, 0.7), (1.5, 4.1, [(4.3, 1.9), (4.5, 3.3), (3.3, 4.2), (1.5, 3.5), (0.6, 1.8)]))},
                   "ball": held("h")}, 5.5, {}),
    # F14: wing cutter passes the post at 1.1 m (not a rub) / at 0.6 m (rub)
    "rub_wide": ({"actors": {"h": OL((5.6, 5.0)), "s": OL((-1.9, 1.6)),
                             "u": OL((-5.2, 4.8), (2.0, 4.2, [(-3.1, 3.2), (-1.0, 2.6), (-0.3, 0.6)])),
                             "d": DL((-4.6, 4.3), (2.1, 2.9, [(-2.7, 2.5)]), (3.6, 4.2, [(-1.0, 1.0)]))}, "ball": held("h")}, 5.0, {}),
    # F13: 70 deg banana of radius 5 m; a nearly straight cut
    "banana_slot": ({"actors": {"h": OL((-5.3, 5.3)), "c": OL((1.21, 5.83), (2.0, 4.2, arc_pts(-2.0, 2.0, 5.0, 50, -20, 14)))},
                     "ball": held("h")}, 5.5, {}),
    "banana_flat": ({"actors": {"h": OL((-5.3, 5.3)), "c": OL((1.21, 5.83), (2.0, 4.0, arc_pts(-12.0, 2.5, 13.6, 14.2, -9.4, 8)))},
                     "ball": held("h")}, 5.5, {}),
    # F04: the slot cuts, the wing fills the slot (2.86 m away); the wing stops 1.6 m short
    "fill_slot": ({"actors": {"h": OL((-5.3, 5.3)), "a": OL((3.0, 7.0), (2.0, 3.9, [(0.8, 1.2)])),
                              "b": OL((5.3, 5.3), (2.6, 3.8, [(3.0, 7.0)]))}, "ball": held("h")}, 5.0, {}),
    "fill_short": ({"actors": {"h": OL((-5.3, 5.3)), "a": OL((3.0, 7.0), (2.0, 3.9, [(0.8, 1.2)])),
                               "b": OL((5.3, 5.3), (2.6, 3.6, [(4.4, 6.0)]))}, "ball": held("h")}, 5.0, {}),
    # F20: realistic wing L (along the arc, then down to the corner; turn about 50 deg)
    "l_wing": ({"actors": {"h": TOPL, "c": OL((-1.5, 7.6), (2.0, 3.6, [(4.0, 6.4)]), (3.7, 5.5, [(6.95, 1.0)]))},
                "ball": held("h")}, 5.5, {}),
    # F21: jog toward the rim at 1.7 m/s
    "jog_rim_slow": ({"actors": {"h": TOPL, "a": OL((5.0, 5.0), (2.0, 5.2, [(1.4, 1.6)], "trap"))}, "ball": held("h")}, 6.0, {}),
    # F05: loop of 235 deg around a post; weak corner under the rim to the ball-side corner; half-court sprint
    "loop_back": ({"actors": {"h": TOPL, "s": OL((3.0, 1.2)),
                              "u": OL((5.6, 0.4), (1.5, 4.3, [(4.5, 0.5)] + arc_pts(3.0, 1.2, 1.5, -5, 230, 12) + [(4.8, -0.2)]))},
                   "ball": held("h")}, 5.5, {}),
    "wb_under": ({"actors": {"h": OL((5.3, 5.3)), "c": OL((-6.9, 0.4), (1.5, 5.3, [(-2.5, 0.0), (2.5, 0.0), (6.9, 0.4)]))},
                  "ball": held("h")}, 6.0, {}),
    "sprint_half_real": ({"actors": {"h": TOPL, "p": OL((3.4, 6.8), (1.5, 3.6, [(6.95, 0.3)]))}, "ball": held("h")}, 4.5, {}),
    # F16: baseline exit to the corner over a baseline screener
    "blexit_left": ({"actors": {"h": OL((3.0, 7.0)), "s": OL((-4.2, 0.4)),
                                "u": OL((-1.9, 0.9), (2.0, 3.6, [(-4.2, 1.3), (-6.95, 0.6)]))}, "ball": held("h")}, 5.0, {}),
    # loop 2, R1: dunker-line step-out, plant, back cut (truth t_rev 2.15 s); denied wing back-cuts from rest
    "bd_short": ({"actors": {"h": TOPL, "c": OL((3.9, 1.4), (1.5, 2.1, [(4.3, 2.8)]), (2.2, 3.4, [(0.6, 0.5)])),
                             "d": DL((3.4, 2.2), (1.5, 2.2, [(3.8, 3.5)]), (2.4, 3.8, [(1.4, 1.4)]))}, "ball": held("h")}, 5.0, {}),
    "bd_deny": ({"actors": {"h": TOPL, "c": OL((5.8, 4.4), (2.0, 3.9, [(0.7, 0.6)])),
                            "d": DL((4.9, 5.0), (2.3, 4.2, [(1.5, 1.4)]))}, "ball": held("h")}, 5.0, {}),
    # loop 2, F08 residual: attack the defender, veer 70 deg next to him (truth 2.35 s); slot I-cut (truth 2.6 s)
    "veer_slot": ({"actors": {"h": OL((-5.3, 5.3)), "u": OL((3.4, 7.6), (1.5, 2.3, [(2.6, 6.0)]), (2.4, 3.2, [(4.4, 4.2)])),
                              "d": DL((2.3, 5.4))}, "ball": held("h")}, 4.5, {}),
    "i_slot": ({"actors": {"h": OL((5.3, 5.3)), "c": OL((2.9, 7.4), (2.0, 2.55, [(2.2, 6.1)]), (2.65, 3.25, [(3.0, 7.5)]))},
                "ball": held("h")}, 5.0, {}),
}
ALL_SCEN = dict(S, **R)


# --------------------------------------------------------------------------------------
# Cases: detector, positive scenario, role->actor, truth t0 (fn of truth), negative scenario
# --------------------------------------------------------------------------------------
CASES = [
    ("move", "basket", {"player": "c"}, lambda T: onset(T, "c", 2.0), "still"),
    ("cut", "basket", {"cutter": "c"}, lambda T: onset(T, "c", 2.0), "arc_slide"),
    ("cut_basket", "basket", {"cutter": "c"}, lambda T: onset(T, "c", 2.0), "arc_slide"),
    ("cut_dive", "basket", {"cutter": "c"}, lambda T: onset(T, "c", 2.0), "curved_basket"),
    ("cut_45", "basket", {"cutter": "c"}, lambda T: onset(T, "c", 2.0), "slot_basket"),
    ("cut_front", "front", {"cutter": "c"}, lambda T: onset(T, "c", 2.0), "basket"),
    ("cut_backdoor", "backdoor", {"cutter": "c"}, lambda T: 2.15, "basket"),
    ("cut_flash", "flash", {"cutter": "c"}, lambda T: onset(T, "c", 2.0), "basket"),
    ("cut_v", "vcut", {"cutter": "c"}, lambda T: 2.75, "lcut"),
    ("cut_l", "lcut", {"cutter": "c"}, lambda T: 2.95, "vcut"),
    ("cut_i", "icut", {"cutter": "c"}, lambda T: 2.65, "vcut"),
    ("cut_banana", "banana", {"cutter": "c"}, lambda T: onset(T, "c", 2.0), "basket"),
    ("cut_shallow", "shallow", {"cutter": "c"}, lambda T: onset(T, "c", 1.5), "weak_corner"),
    ("cut_weak_baseline", "baseline", {"runner": "c"}, lambda T: onset(T, "c", 1.5), "midband_run"),
    ("cut_thru", "thru", {"cutter": "a"}, lambda T: 2.05, "pass_stay"),
    ("give_and_go", "give_go", {"cutter": "a"}, lambda T: 2.05, "thru"),
    ("cut_curl", "curl", {"user": "u"}, lambda T: closest(T, "u", "s", 1.5, 4.0), "straight"),
    ("cut_straight", "straight", {"user": "u"}, lambda T: closest(T, "u", "s", 1.8, 4.0), "curl"),
    ("cut_pop_out", "pop_out", {"user": "u"}, lambda T: closest(T, "u", "s", 1.8, 4.0), "curl"),
    ("cut_flare", "flare", {"user": "u"}, lambda T: onset(T, "u", 1.8), "fade"),
    ("cut_fade", "fade", {"user": "u"}, lambda T: onset(T, "u", 1.8), "flare"),
    ("cut_ucla", "ucla", {"cutter": "a"}, lambda T: closest(T, "a", "s", 2.0, 4.5), "thru"),
    ("cut_iverson", "iverson", {"cutter": "u"}, lambda T: cross_x(T, "u", 1.5), "iverson_low"),
    ("cut_flex", "flex", {"cutter": "u"}, lambda T: closest(T, "u", "s", 1.5, 4.0), "flex_noscreen"),
    ("cut_zipper", "zipper", {"cutter": "u"}, lambda T: closest(T, "u", "s", 2.3, 4.0), "zipper_static"),
    ("cut_pin_down", "pin_down", {"cutter": "u"}, lambda T: closest(T, "u", "s", 2.3, 4.0), "zipper"),
    ("cut_turnout", "turnout", {"cutter": "u"}, lambda T: closest(T, "u", "s", 2.0, 4.2), "turnout_high"),
    ("cut_cross_screen", "cross", {"cutter": "u"}, lambda T: closest(T, "u", "s", 2.0, 4.0), "cross_noscreen"),
    ("cut_baseline_exit", "bl_exit", {"cutter": "u"}, lambda T: closest(T, "u", "s", 2.0, 4.5), "bl_exit_noscreen"),
    ("cut_chin", "chin", {"cutter": "c"}, lambda T: closest(T, "c", "s", 2.7, 4.7), "chin_nopass"),
    ("cut_loop", "loop", {"cutter": "u"}, lambda T: onset(T, "u", 1.5), "banana"),
    ("cut_shuffle", "shuffle", {"cutter": "u"}, lambda T: closest(T, "u", "s", 1.5, 4.0), "shuffle_noscreen"),
    ("cut_blade", "blade", {"cutter": "k"}, lambda T: closest(T, "h", "s", 1.5, 3.0), "shake"),
    ("shake", "shake", {"player": "k"}, lambda T: closest(T, "h", "s", 1.5, 3.0), "blade"),
    ("cut_rub", "rub", {"cutter": "u"}, lambda T: closest(T, "u", "s", 2.0, 4.2), "rub_nopost"),
    ("cut_circle", "circle", {"cutter": "u"}, lambda T: 2.85, "circle_noelbow"),
    ("cut_laker", "laker", {"cutter": "a"}, lambda T: 2.05, "laker_wing"),
    ("cut_veer", "veer", {"cutter": "u"}, lambda T: 2.35, "veer_far"),
    ("relocate", "relocate", {"player": "w"}, lambda T: 2.5, "basket"),
    ("lift", "lift", {"player": "k"}, lambda T: last_r_ge(T, "h", 6.1, 3.5), "drift"),
    ("drift", "drift", {"player": "w"}, lambda T: last_r_ge(T, "h", 6.1, 3.6), "lift"),
    ("cut_hammer", "hammer", {"player": "w"}, lambda T: last_r_ge(T, "h", 6.1, 3.6), "drift"),
    ("dunker_slide", "slide", {"player": "d"}, lambda T: r_cross_in(T, "r", 4.27, 1.5), "slide_stay"),
    ("fill", "fill", {"filler": "b"}, lambda T: leave_from(T, "a", 2.0, 2.0), "fill_late"),
    ("sprint_to_corner", "sprint_half", {"player": "p"}, lambda T: None, "jog_corner"),
    ("sprint_to_corner", "sprint_trans", {"player": "p"}, lambda T: 1.0, "jog_corner"),
    ("rim_run", "rim_run", {"runner": "p"}, lambda T: 1.0, "rim_jog"),
    ("blind_pig", "blind_pig", {"cutter": "c"}, lambda T: 2.05, "blind_pig_nofeed"),
    ("wiper", "wiper", {"cutter": "u"}, lambda T: closest(T, "u", "s2", 2.3, 3.6), "pin_down"),
]


def _matching(events, kind, roles):
    return [e for e in events if e.kind == kind and all(e.actors.get(k) == v for k, v in roles.items())]


@pytest.mark.parametrize("det,pos,roles,t0fn,neg", CASES, ids=[f"{c[0]}:{c[1]}" for c in CASES])
@pytest.mark.parametrize("seed", SEEDS)
def test_positive(det, pos, roles, t0fn, neg, seed):
    spec, dur, attrs = S[pos]
    truth, sc = build(spec, dur, seed, **attrs)
    evs = _matching(cuts.DETECTORS[det](sc), det, roles)
    assert evs, f"{det} not detected in {pos} (seed {seed})"
    t_true = t0fn(truth)
    best = max(evs, key=lambda e: e.conf)
    assert cuts.G["min_conf"] <= best.conf <= 1.0
    if t_true is not None:
        assert any(abs(e.t0 * DT - t_true) <= T0_TOL_S for e in evs), \
            f"{det}: t0 {[round(e.t0 * DT, 2) for e in evs]} vs truth {t_true:.2f}"


@pytest.mark.parametrize("det,pos,roles,t0fn,neg", CASES, ids=[f"{c[0]}:{c[2]}:{c[4]}" for c in CASES])
@pytest.mark.parametrize("seed", SEEDS)
def test_negative(det, pos, roles, t0fn, neg, seed):
    spec, dur, attrs = S[neg]
    _, sc = build(spec, dur, seed, **attrs)
    evs = _matching(cuts.DETECTORS[det](sc), det, roles)
    assert not evs, f"{det} fired in negative scenario {neg}: {[(e.t0 * DT, e.conf, e.attrs.get('binding_test')) for e in evs]}"


# --------------------------------------------------------------------------------------
# Loop 6 (finishing pass): carry rule of the half-court gate, joint evidence, I-cut geometry
# --------------------------------------------------------------------------------------
def _ball(*held_, flights=()):
    return {"held": list(held_), "flights": list(flights)}


L6 = {
    # L6-01: the handler walks the ball over half court (2.2 m/s, crosses y 12.7 at ~1.6 s), passes to the wing at
    # 2.4 s and cuts: half-court pass-and-cuts (loop 4 10 | 10 | 9 of 10, loop 5 0 | 0 | 0)
    "l6_walkup_basket": ({"actors": {"a": O((0, 2.0, 16.0), (2.4, 2.0, 10.8), (2.6, 2.0, 10.8), (5.2, 0.6, 1.0)),
                                     "w": O((0, 5.3, 5.3)), "d": D((0, 2.0, 15.0), (2.4, 2.0, 9.8), (5.4, 1.0, 2.5))},
                          "ball": _ball((0, 2.4, "a"), (2.8, 9, "w"), flights=[(2.4, 2.8, "a", "w")])}, 7.0, {}),
    "l6_walkup_thru": ({"actors": {"a": O((0, 2.5, 16.0), (2.4, 2.5, 10.8), (2.6, 2.5, 10.8), (5.0, 0.0, 2.5), (6.8, -5.3, 5.3)),
                                   "w": O((0, 5.3, 5.3))},
                        "ball": _ball((0, 2.4, "a"), (2.8, 9, "w"), flights=[(2.4, 2.8, "a", "w")])}, 7.5, {}),
    # off-ball wing walks over half court (trapezoid, ~2 m/s), then a basket cut 1.4 s after crossing
    "l6_offball_walk": ({"actors": {"h": O((0, -3.0, 8.0)), "a": OL((5.3, 15.0), (0.0, 2.4, [(5.3, 10.8)], "trap"), (2.6, 5.6, [(1.0, 1.0)]))},
                         "ball": held("h")}, 6.5, {}),
    # negatives: the handler pushes the ball across (steady ~4-5 m/s), passes ahead without slowing and keeps running
    # to the rim; and the walk-up while the defense is still coming back (3 defenders beyond half court)
    "l6_push_run": ({"actors": {"a": OL((2.0, 21.0), (0.0, 4.4, [(2.0, 12.0), (1.6, 6.0), (0.6, 1.0)], "trap")), "w": O((0, 5.3, 5.3))},
                     "ball": _ball((0, 2.3, "a"), (2.7, 9, "w"), flights=[(2.3, 2.7, "a", "w")])}, 5.5, {}),
    "l6_jog_push_run": ({"actors": {"a": OL((2.0, 20.0), (0.0, 5.6, [(2.0, 12.0), (1.4, 6.0), (0.6, 1.0)], "trap")), "w": O((0, 5.3, 5.3))},
                         "ball": _ball((0, 2.9, "a"), (3.3, 9, "w"), flights=[(2.9, 3.3, "a", "w")])}, 6.5, {}),
    "l6_walkup_defense_back": ({"actors": {"a": O((0, 2.0, 16.0), (2.4, 2.0, 10.8), (2.6, 2.0, 10.8), (5.2, 0.6, 1.0)),
                                           "w": O((0, 5.3, 5.3)), "d": D((0, 2.0, 15.0), (2.4, 2.0, 9.8), (5.4, 1.0, 2.5)),
                                           "e": D((0, -3.0, 19.0), (3.0, -3.0, 8.0)), "f": D((0, 4.0, 18.0), (3.0, 4.0, 9.0))},
                                "ball": _ball((0, 2.4, "a"), (2.8, 9, "w"), flights=[(2.4, 2.8, "a", "w")])}, 7.0, {}),
    # L6-03: a corner player walks down the sideline and back up (Dr -0.56 m on a 1.8 m leg, 72 deg off the radial)
    # and a wing player slides down the arc to the corner and back: not I-cuts (loop 5 at sigma 0.2: 10 and 4 of 10)
    "l6_corner_down_up": ({"actors": {"h": TOP, "c": O((0, 7.0, 3.2), (2.0, 7.0, 3.2), (2.7, 7.0, 1.4), (2.8, 7.0, 1.4), (3.5, 7.0, 3.3))},
                           "ball": held("h", 8)}, 5.0, {}),
    "l6_wing_corner_back": ({"actors": {"h": TOP, "c": O((0, 6.4, 3.4), (2.0, 6.4, 3.4), (2.7, 6.9, 1.7), (2.8, 6.9, 1.7), (3.5, 6.4, 3.5))},
                             "ball": held("h", 8)}, 5.0, {}),
    # ... while I-cuts 50 deg and 30 deg off the radial and along the baseline keep their recall
    "l6_i_oblique": ({"actors": {"h": TOP, "c": O((0, 6.0, 4.5), (2.0, 6.0, 4.5), (2.6, 5.75, 2.77), (2.7, 5.75, 2.77), (3.3, 6.05, 4.6))},
                      "ball": held("h", 8)}, 5.0, {}),
    "l6_i_30deg": ({"actors": {"h": TOP, "c": O((0, 5.5, 5.0), (2.0, 5.5, 5.0), (2.6, 4.75, 3.6), (2.7, 4.75, 3.6), (3.3, 5.5, 5.0))},
                    "ball": held("h", 8)}, 5.0, {}),
    "l6_i_baseline": ({"actors": {"h": TOP, "c": O((0, 6.9, 0.4), (2.0, 6.9, 0.4), (2.6, 5.2, 0.4), (2.7, 5.2, 0.4), (3.3, 6.9, 0.5))},
                       "ball": held("h", 8)}, 5.0, {}),
    # L6-04: pass-bys of a set screener at about 1 m, straight and with a bend (borderline contact and heading)
    "l6_straight_wide": ({"actors": {"h": TOP, "s": O((0, 4.3, 2.5)), "u": O((0, 2.0, 0.8), (1.8, 2.0, 0.8), (3.6, 5.6, 6.3))},
                          "ball": held("h", 8)}, 5.0, {}),
    "l6_straight_bend": ({"actors": {"h": TOP, "s": O((0, 4.2, 2.6)), "u": O((0, 2.0, 0.8), (1.8, 2.0, 0.8), (2.7, 3.3, 3.2), (3.6, 4.4, 6.4))},
                          "ball": held("h", 8)}, 5.0, {}),
}
ALL_SCEN.update(L6)


def test_l6_01_walk_up_pass_and_cut_keeps_its_half_court_labels():
    # handler walk-up, pass and cut within transition_carry_s of crossing half court (loop 5: 0 of 20 at 0.2 / 0.3)
    assert _rate("l6_walkup_basket", "cut_basket", {"cutter": "a"}) >= 0.9
    assert _rate("l6_walkup_basket", "cut", {"cutter": "a"}) >= 0.9
    assert _rate("l6_walkup_thru", "cut_thru", {"cutter": "a"}) >= 0.9
    assert _rate("l6_offball_walk", "cut_basket", {"cutter": "a"}) >= 0.9
    # a transition push (sustained run into the action) and a defense still coming back keep the carry
    for name in ("l6_push_run", "l6_jog_push_run", "l6_walkup_defense_back"):
        for det in ("cut", "cut_basket"):
            assert _rate(name, det, {"cutter": "a"}, sigmas=(0.2, 0.3, 0.5)) == 0.0, (name, det)
    # the carry rule is XY only (production video has no reliable ball height)
    assert {"carry_run_mps", "carry_burst_ratio", "carry_def_unset_n"} <= set(cuts.PARAMS["cu_postrules"])


def test_l6_02_high_noise_veer_needs_joint_turn_and_approach_evidence():
    k = cuts.PARAMS["cut_veer"].get("evidence_k_high_noise", 2.0)
    for name in ("veer", "veer_slot", "l5_veer_jog", "l5_veer_jog2"):
        spec, dur, attrs = ALL_SCEN[name]
        for seed in range(10):
            _, sc = build(spec, dur, seed, sigma=0.5, **attrs)
            for e in _matching(cuts.detect_cut_veer(sc), "cut_veer", {"cutter": "u"}):
                m = e.attrs["margins"]
                assert m["turn"] + m["approach"] >= k - 1e-6, (name, seed, m)
    # jogs past an always-near defender: loop 5 9 of 30 runs at sigma 0.5
    hits = sum(_rate(nm, "cut_veer", {"cutter": "u"}, sigmas=(0.5,)) for nm in ("l5_veer_jog", "l5_veer_jog2", "l5_veer_shadow"))
    assert round(hits * 10) <= 4
    # below the high-noise tier the rule is unchanged
    assert _rate("veer", "cut_veer", {"cutter": "u"}, sigmas=(0.2, 0.3), t0fn=lambda T: 2.35) >= 0.9


def test_l6_03_i_cut_in_leg_points_at_the_rim():
    for name in ("l6_corner_down_up", "l6_wing_corner_back", "l5_lateral_i"):
        assert _rate(name, "cut_i", {"cutter": "c"}, sigmas=(0.2, 0.3)) <= 0.2, name
    for name in ("l6_i_oblique", "l6_i_baseline", "icut"):
        assert _rate(name, "cut_i", {"cutter": "c"}, sigmas=(0.2, 0.3)) >= 0.85, name
    assert _rate("l6_i_30deg", "cut_i", {"cutter": "c"}, sigmas=(0.2, 0.3)) >= 0.8
    assert cuts.PARAMS["cut_i"]["in_dir_max_deg"] == 60  # L7-01: the documented angular test (was in_dir_frac 0.5)


def test_l6_04_straight_cut_needs_joint_contact_and_heading_evidence():
    k = cuts.PARAMS["cut_straight"].get("evidence_k", 2.0)
    n = 0
    for name in ("l6_straight_wide", "l6_straight_bend", "straight"):
        spec, dur, attrs = ALL_SCEN[name]
        for sg in (0.3, 0.5):
            for seed in range(10):
                _, sc = build(spec, dur, seed, sigma=sg, **attrs)
                for e in _matching(cuts.detect_cut_straight(sc), "cut_straight", {"user": "u"}):
                    m = e.attrs["margins"]
                    assert m["contact"] + m["heading_change"] >= k - 1e-6, (name, sg, seed, m)
                    n += 1
    assert n >= 40  # the clear pass-bys still fire
    assert _rate("straight", "cut_straight", {"user": "u"}) >= 0.9


def test_yaml_changes_loop6_recorded():
    ch = cuts.DOC.get("changes_loop6")
    assert ch and all({"id", "what", "why", "evidence"} <= set(c) for c in ch)
    ids = {c["id"].split()[0] for c in ch}
    assert {"L6-00", "L6-01", "L6-02", "L6-03", "L6-04", "L6-05", "L6-06"} <= ids
    assert cuts.DOC["version"] >= "0.6.0"


# --------------------------------------------------------------------------------------
# Loop 7 (regression-only finishing pass): documented I-cut angle, speed-band-free carry rule
# --------------------------------------------------------------------------------------
def _icut_at(p0, off_deg, L, t_in=2.0, dur=0.6):
    """Out-and-back I-cut from p0, its in-leg off_deg off the bearing to the rim from p0 (+ = counter-clockwise)."""
    r = math.hypot(*p0)
    a = math.atan2(-p0[1], -p0[0]) + math.radians(off_deg)
    p1 = (p0[0] + L * math.cos(a), p0[1] + L * math.sin(a))
    return O((0, *p0), (t_in, *p0), (t_in + dur, *p1), (t_in + dur + 0.1, *p1), (t_in + 2 * dur + 0.1, *p0))


L7 = {
    # L7-01: corner I-cut 55 deg off the bearing to the rim from its start (inside the documented 60 deg; loop 6, whose
    # Dr / L1 >= 0.5 test is about 52 deg from the start here: 3 | 4 | 3 of 10 at sigma 0.2 | 0.3 | 0.5)
    "l7_i_corner_55": ({"actors": {"h": TOP, "c": _icut_at((6.6, 1.5), -55, 2.0)}, "ball": held("h", 8)}, 5.0, {}),
    "l7_i_wing_55": ({"actors": {"h": TOP, "c": _icut_at((5.3, 5.3), -55, 1.8)}, "ball": held("h", 8)}, 5.0, {}),
    # ... while 70 deg out-and-backs and a lateral in-leg whose out-leg comes back elsewhere (the axis reads 57 deg,
    # the in-leg chord 73 deg) are not I-cuts
    "l7_i_corner_70": ({"actors": {"h": TOP, "c": _icut_at((6.6, 1.5), -70, 2.0)}, "ball": held("h", 8)}, 5.0, {}),
    "l7_i_lateral_back_out": ({"actors": {"h": TOP, "c": O((0, 5.2, 6.3), (2.0, 5.2, 6.3), (2.6, 3.95, 6.8), (2.7, 3.95, 6.8), (3.3, 5.7, 6.95))},
                               "ball": held("h", 8)}, 5.0, {}),
    # L7-02: the handler jogs the ball over half court at ~3.4 m/s (no stop), passes to the wing at 2.5 s and bursts
    # to the rim (~5.5 m/s): a pass-and-cut (loop 6: 0 of 20, the 3.0 m/s sustain test read it as a transition push)
    "l7_jog_pass_burst": ({"actors": {"a": OL((2.0, 19.0), (0.0, 4.8, [(2.0, 11.0), (0.8, 1.0)], ("pace", 0.58, 0.44))),
                                      "w": O((0, 5.3, 5.3))},
                           "ball": _ball((0, 2.5, "a"), (2.9, 9, "w"), flights=[(2.5, 2.9, "a", "w")])}, 6.0, {}),
    # ... while the same jog that passes and keeps its pace to the rim stays a transition carry
    "l7_jog_pass_same": ({"actors": {"a": OL((2.0, 19.0), (0.0, 5.8, [(2.0, 11.0), (0.8, 1.0)], "trap")), "w": O((0, 5.3, 5.3))},
                          "ball": _ball((0, 2.5, "a"), (2.9, 9, "w"), flights=[(2.5, 2.9, "a", "w")])}, 7.0, {}),
}
ALL_SCEN.update(L7)


def test_l7_01_i_cut_angle_is_the_documented_60_deg():
    # 55 deg I-cuts from the corner and the wing (loop 6: 0.35 and 0.5 at sigma 0.2 / 0.3)
    assert _rate("l7_i_corner_55", "cut_i", {"cutter": "c"}) >= 0.75
    assert _rate("l7_i_wing_55", "cut_i", {"cutter": "c"}) >= 0.7
    # the sideline walk (65 deg), 70 deg out-and-backs and the lateral in-leg stay out
    assert _rate("l6_corner_down_up", "cut_i", {"cutter": "c"}) <= 0.2
    assert _rate("l7_i_corner_70", "cut_i", {"cutter": "c"}) <= 0.1
    assert _rate("l7_i_lateral_back_out", "cut_i", {"cutter": "c"}) <= 0.1
    # the 30 / 50 deg and baseline I-cuts keep their recall
    for name in ("l6_i_oblique", "l6_i_baseline", "icut"):
        assert _rate(name, "cut_i", {"cutter": "c"}) >= 0.85, name
    p = cuts.PARAMS["cut_i"]
    assert p["in_dir_max_deg"] == 60 and 0.25 <= p["in_dir_tol_k"] <= 1.0 and "in_dir_frac" not in p


def test_l7_02_carry_rule_has_no_speed_in_the_jog_up_band():
    p = cuts.PARAMS["cu_postrules"]
    assert "carry_sustain_mps" not in p and p["carry_run_mps"] <= 2.2  # walk-run gait speed, below the 2.5-3.5 m/s band
    assert _rate("l7_jog_pass_burst", "cut_basket", {"cutter": "a"}) >= 0.9
    assert _rate("l7_jog_pass_same", "cut_basket", {"cutter": "a"}, sigmas=(0.2, 0.3, 0.5)) == 0.0
    assert _rate("l7_jog_pass_same", "cut", {"cutter": "a"}, sigmas=(0.2, 0.3, 0.5)) == 0.0
    # stability: perturbing the gait speed by +-0.25 m/s, the burst ratio by +-0.1, the post-release margin (L9-02) by
    # +-0.5 sigma or the push speed (L9-01) by +-0.25 m/s changes no outcome (loop 8 had to narrow the ratio to +-0.05
    # because of the L8-03 1-sigma burst margin, removed in loop 9)
    base = dict(p)
    try:
        for k, v in (("carry_run_mps", 1.75), ("carry_run_mps", 2.25), ("carry_burst_ratio", 1.15), ("carry_burst_ratio", 1.35),
                     ("carry_post_k", 0.5), ("carry_post_k", 1.5), ("carry_push_mps", 3.75), ("carry_push_mps", 4.25)):
            p.update(base)
            p[k] = v
            assert _rate("l7_jog_pass_burst", "cut_basket", {"cutter": "a"}, seeds=range(5)) >= 0.9, (k, v)
            for name in ("l7_jog_pass_same", "l6_push_run", "l6_jog_push_run"):
                assert _rate(name, "cut_basket", {"cutter": "a"}, seeds=range(5)) == 0.0, (name, k, v)
            assert _rate("l6_walkup_basket", "cut_basket", {"cutter": "a"}, seeds=range(5)) >= 0.9, (k, v)
    finally:
        p.update(base)


# --------------------------------------------------------------------------------------
# Loop 8 (final targeted pass): the loop-7 confirmer's C7-1..C7-4 and synthetic N1
# --------------------------------------------------------------------------------------
_SET3 = {"d1": D((0, 0.5, 6.5)), "d2": D((0, -4.5, 4.5)), "d3": D((0, 4.0, 2.0))}


def _rot(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def _icut_back(p0, off_deg, L, back, t_in=2.0, dur_in=0.6, dur_out=0.6):
    """Out-and-back from p0 whose in-leg is off_deg off the rim bearing and whose out-leg returns to back."""
    r = math.hypot(*p0)
    d = _rot((-p0[0] / r, -p0[1] / r), off_deg)
    p1 = (p0[0] + L * d[0], p0[1] + L * d[1])
    return O((0, *p0), (t_in, *p0), (t_in + dur_in, *p1), (t_in + dur_in + 0.1, *p1), (t_in + dur_in + 0.1 + dur_out, *back))


_I1_P0 = (5.3, 5.3)
_I1_D = _rot((-_I1_P0[0] / math.hypot(*_I1_P0), -_I1_P0[1] / math.hypot(*_I1_P0)), 70)
_I1_BACK = (_I1_P0[0] - 1.2 * _I1_D[0] - 0.7 * _I1_D[1], _I1_P0[1] - 1.2 * _I1_D[1] + 0.7 * _I1_D[0])
L8 = {
    # L8-01 (C7-1): the handler jogs the ball over half court (2.8 / 2.5 m/s), passes at y ~11 and slows to a walk-pace
    # relocation to the wing against a set defense: half-court labels (loop 7 0 of 20 and 1 of 20 at sigma 0.2 / 0.3)
    "l8_jog_pass_slow_relocate": ({"actors": {"a": OL((2.0, 17.0), (0.0, 5.0, [(2.0, 11.0), (5.5, 8.5)], ("pace", 0.43, 0.58))),
                                              "w": O((0, -5.3, 5.3)), **_SET3},
                                   "ball": _ball((0, 2.1, "a"), (2.5, 9, "w"), flights=[(2.1, 2.5, "a", "w")])}, 6.5, {}),
    "l8_jog25_pass_slow_relocate": ({"actors": {"a": OL((2.0, 17.0), (0.0, 6.0, [(2.0, 11.0), (5.5, 8.5)], ("pace", 0.45, 0.58))),
                                                "w": O((0, -5.3, 5.3)), **_SET3},
                                     "ball": _ball((0, 2.4, "a"), (2.8, 9, "w"), flights=[(2.4, 2.8, "a", "w")])}, 7.5, {}),
    # L8-01b: a sub-gait walk-up (~1.85 m/s, no stop), pass at y 10.8, then a 2.2 m/s move (no burst)
    "l8_walk185_pass_go": ({"actors": {"a": OL((2.0, 16.0), (0.0, 6.0, [(2.0, 10.8), (0.6, 6.0)], ("pace", 0.55, 0.51))),
                                       "w": O((0, 5.3, 5.3)), **_SET3},
                            "ball": _ball((0, 3.2, "a"), (3.6, 9, "w"), flights=[(3.2, 3.6, "a", "w")])}, 7.5, {}),
    # L8-02 (C7-2): the handler jogs the ball over (3.0 m/s) and keeps it, accelerating to the rim (a dribble drive)
    "l8_jog_drive_keep": ({"actors": {"a": OL((2.0, 17.7), (0.0, 4.76, [(2.0, 11.0), (0.6, 1.0)], ("pace", 0.47, 0.40))),
                                      "w": O((0, 5.3, 5.3)), **_SET3},
                           "ball": _ball((0, 9, "a"))}, 6.0, {}),
    # L8-03 (synthetic N1): the handler pushes at 4.5 m/s, hits ahead at y ~11 and accelerates 1.24x to the rim (set
    # defense): a transition push (loop 7: 2 of 10 at sigma 0.3 passed the burst ratio on noise)
    "l8_push_pass_sprint": ({"actors": {"a": OL((2.0, 22.0), (0.0, 4.24, [(2.0, 11.0), (0.6, 1.0)], ("pace", 0.575, 0.52))),
                                        "w": O((0, 5.3, 5.3)), **_SET3},
                             "ball": _ball((0, 2.4, "a"), (2.8, 9, "w"), flights=[(2.4, 2.8, "a", "w")])}, 5.5, {}),
    # L8-04 (C7-3): lateral in-leg 70 deg off the rim bearing whose out-leg overshoots past the start (axis ~58 deg)
    "l8_i_lateral_overshoot": ({"actors": {"h": TOP, "c": _icut_back(_I1_P0, 70, 1.8, _I1_BACK, dur_out=0.95)},
                                "ball": held("h", 8)}, 5.0, {}),
    # L8-05 (C7-4): an under-rim lateral shuffle and a lateral drift under the rim (r 1.3-1.6 m) are not I-cuts ...
    "l8_rim_lateral_shuffle": ({"actors": {"h": TOP, "c": O((0, 1.3, 0.6), (2.0, 1.3, 0.6), (2.6, 0.1, 1.3), (2.7, 0.1, 1.3), (3.3, 1.3, 0.6))},
                                "ball": held("h", 8)}, 5.0, {}),
    "l8_rim_drift_back": ({"actors": {"h": TOP, "c": O((0, -1.5, 0.3), (2.0, -1.5, 0.3), (2.6, -0.4, 1.4), (2.7, -0.4, 1.4), (3.3, -1.6, 0.4))},
                           "ball": held("h", 8)}, 5.0, {}),
    # ... while radial I-cuts into the rim zone keep their recall
    "l8_block_radial_i": ({"actors": {"h": TOP, "c": O((0, 2.4, 1.0), (2.0, 2.4, 1.0), (2.6, 1.1, 0.45), (2.7, 1.1, 0.45), (3.3, 2.4, 1.0))},
                           "ball": held("h", 8)}, 5.0, {}),
    "l8_rim_radial_dip": ({"actors": {"h": O((0, 5.3, 5.3)), "c": _icut_back((-1.5, 2.6), 0, 1.4, (-1.5, 2.6))}, "ball": held("h", 8)}, 5.0, {}),
}
ALL_SCEN.update(L8)


def _carry_call(name, seed, sigma, a_from_release_s=0.1, b_len_s=1.5):
    """Calls the half-court carry rule for actor a on scene name: tx = his last backcourt frame, label [a, b] from
    a_from_release_s after the end of his first holder run (or after tx + 0.5 s when he never releases)."""
    spec, dur, attrs = ALL_SCEN[name]
    _, sc = build(spec, dur, seed, sigma=sigma, **attrs)
    c = cuts._ctx(sc)
    fe = c.f["a"]
    hc = cuts.PARAMS["cut"]["frontcourt_y_max_m"]
    tx = int(np.flatnonzero(np.nan_to_num(fe.y, nan=99.0) > hc)[-1])
    runs = [r for r in c.holder_runs() if r[0] == "a"]
    t_rel = runs[0][2] if runs and runs[0][2] < c.n - 5 else tx + cuts.F(0.5)
    a = t_rel + cuts.F(a_from_release_s)
    b = min(c.n - 1, a + cuts.F(b_len_s))
    lo = max(0, a - cuts.F(cuts.PARAMS["cut"]["transition_carry_s"]))
    return cuts._transition_carry(c, "a", tx, lo, a, b)


def test_l8_01_post_pass_slow_down_is_judged_on_its_own_phase():
    # jog-up, pass, walk-pace relocation vs a set defense: half-court labels (loop 7: 0.0 and 0.05)
    assert _rate("l8_jog_pass_slow_relocate", "relocate", {"player": "a"}) >= 0.4
    assert _rate("l8_jog25_pass_slow_relocate", "relocate", {"player": "a"}) >= 0.25
    for name in ("l8_jog_pass_slow_relocate", "l8_jog25_pass_slow_relocate"):
        assert sum(not _carry_call(name, s, sg, b_len_s=2.5) for sg in (0.2, 0.3) for s in range(10)) >= 18, name
    # L8-01b: a walk-up below the gait speed is not a run (loop 7: the -1 sigma allowance made it one)
    assert sum(not _carry_call("l8_walk185_pass_go", s, 0.2) for s in range(10)) >= 9
    # the transition carries stay: push and jog push that keep running, the jog that keeps its pace
    for name in ("l6_push_run", "l6_jog_push_run", "l7_jog_pass_same"):
        for det in ("cut", "cut_basket"):
            assert _rate(name, det, {"cutter": "a"}, sigmas=(0.2, 0.3, 0.5)) == 0.0, (name, det)


def test_l8_02_burst_exception_needs_a_release_before_the_label():
    # the handler keeps the ball through the label (a dribble drive that accelerates 1.3x): not a half-court cut
    # (loop 7 returned False: held + burst, without checking the release)
    assert sum(_carry_call("l8_jog_drive_keep", s, sg, a_from_release_s=0.0) for sg in (0.2, 0.3) for s in range(10)) == 20
    # a release on the label's first frame is a release: the jog-up pass-and-burst keeps its label
    assert _rate("l7_jog_pass_burst", "cut_basket", {"cutter": "a"}) >= 0.9


def test_l8_03_push_that_hits_ahead_and_accelerates_stays_a_transition():
    for det in ("cut", "cut_basket"):
        assert _rate("l8_push_pass_sprint", det, {"cutter": "a"}, sigmas=(0.2, 0.3, 0.5)) == 0.0, det
    # loop 9 (L9-01): the push is excluded by structure (TRN-P08 pace released on the run), not by a burst margin
    assert "carry_burst_k" not in cuts.PARAMS["cu_postrules"] and cuts.PARAMS["cu_postrules"]["carry_push_mps"] > 0


def _i_chords(name, sigmas):
    out = []
    for sg in sigmas:
        for seed in range(10):
            _, sc = build(*ALL_SCEN[name][:2], seed, sigma=sg)
            fe = cuts._ctx(sc).f["c"]
            for e in _matching(cuts.detect_cut_i(sc), "cut_i", {"cutter": "c"}):
                a, t = int(e.start), int(e.t0)
                out.append(abs(cuts._ang((fe.x[t] - fe.x[a], fe.y[t] - fe.y[a]), (-fe.x[a], -fe.y[a]))))
    return out


def test_l8_04_i_cut_chord_tolerance_is_bounded():
    p = cuts.PARAMS["cut_i"]
    assert 0 < p["in_dir_tol_max_deg"] <= 3.0
    # no emitted I-cut has an in-leg chord beyond the bounded tolerance (loop 7: up to 60 + 0.5 x 4-9 deg)
    for name in ("l8_i_lateral_overshoot", "l7_i_lateral_back_out", "l7_i_corner_55", "l7_i_wing_55"):
        assert all(ch <= p["in_dir_max_deg"] + p["in_dir_tol_max_deg"] + 1e-6 for ch in _i_chords(name, (0.2, 0.3, 0.5))), name
    assert _rate("l8_i_lateral_overshoot", "cut_i", {"cutter": "c"}, sigmas=(0.2, 0.3, 0.5)) <= 0.2
    assert _rate("l7_i_corner_55", "cut_i", {"cutter": "c"}) >= 0.75


def test_l8_05_rim_zone_i_cut_needs_radial_depth():
    # under-rim shuffles and drifts (loop 7: 3 / 20 and 6 / 20 at sigma 0.2 / 0.3)
    for name in ("l8_rim_lateral_shuffle", "l8_rim_drift_back"):
        assert _rate(name, "cut_i", {"cutter": "c"}, sigmas=(0.2, 0.3)) == 0.0, name
    assert _rate("l8_block_radial_i", "cut_i", {"cutter": "c"}, sigmas=(0.2,)) >= 0.8
    assert _rate("l8_rim_radial_dip", "cut_i", {"cutter": "c"}, sigmas=(0.2,)) >= 0.6
    for name in ("icut", "l6_i_baseline", "l6_i_oblique"):
        assert _rate(name, "cut_i", {"cutter": "c"}) >= 0.85, name


def test_yaml_changes_loop8_recorded():
    ch = cuts.DOC.get("changes_loop8")
    assert ch and all({"id", "what", "why", "evidence"} <= set(c) for c in ch)
    ids = {c["id"].split()[0] for c in ch}
    assert {"L8-00", "L8-01", "L8-02", "L8-03", "L8-04", "L8-05"} <= ids
    assert cuts.DOC["version"] >= "0.8.0"
    ev = " ".join(c["evidence"] for c in ch)
    assert "realdata.py" in ev


def test_yaml_changes_loop7_recorded():
    ch = cuts.DOC.get("changes_loop7")
    assert ch and all({"id", "what", "why", "evidence"} <= set(c) for c in ch)
    ids = {c["id"].split()[0] for c in ch}
    assert {"L7-00", "L7-01", "L7-02", "L7-03", "L7-04", "L7-05"} <= ids
    assert cuts.DOC["version"] >= "0.7.0"
    # C6-4: every loop-7 real rate is from the official runner (realdata.py, sequential RNG), and the record says so
    ev = " ".join(c["evidence"] for c in ch)
    assert "realdata.py" in ev and "per-chunk" not in ev.replace("not per-chunk", "")


# --------------------------------------------------------------------------------------
# Loop 9 (structural redesign of the transition carry): the loop-8 confirmer's C8-1..C8-3
# --------------------------------------------------------------------------------------
_DEFBACK = {"d1": DL((3.0, 19.0), (0.0, 4.0, [(1.5, 3.0)], "trap")), "d2": DL((-2.0, 20.0), (0.0, 4.5, [(-2.0, 4.0)], "trap")),
            "d3": D((0, 0.5, 3.0))}
L9 = {
    # L9-01 (C8-1): the handler jogs the ball over (~3.7 m/s at the release), passes to the wing at y ~11 and bursts to the
    # rim (~5.3 / ~4.9 m/s) vs a set defense: pass-and-cuts (loop 8: 12 | 7 and 3 | 2 of 20 at sigma 0.2 | 0.3, the 1-sigma
    # burst margin)
    "l9_jog_pass_burst45": ({"actors": {"a": OL((2.0, 17.7), (0.0, 4.47, [(2.0, 11.0), (0.6, 1.0)], ("pace", 0.50, 0.40))),
                                        "w": O((0, 5.3, 5.3)), **_SET3},
                             "ball": _ball((0, 2.1, "a"), (2.5, 9, "w"), flights=[(2.1, 2.5, "a", "w")])}, 6.0, {}),
    "l9_jog_pass_burst42": ({"actors": {"a": OL((2.0, 17.7), (0.0, 4.63, [(2.0, 11.0), (0.6, 1.0)], ("pace", 0.48, 0.40))),
                                        "w": O((0, 5.3, 5.3)), **_SET3},
                             "ball": _ball((0, 2.1, "a"), (2.5, 9, "w"), flights=[(2.1, 2.5, "a", "w")])}, 6.0, {}),
    # ... while a push (~4.9 m/s at the release) that hits ahead and accelerates ~1.2x to the rim stays a transition
    # (loop 8: 1 of 20 at every sigma passed the margin)
    "l9_push_pass_accel": ({"actors": {"a": OL((2.0, 21.0), (0.0, 4.6, [(2.0, 11.0), (0.6, 1.0)], ("pace", 0.56, 0.51))),
                                       "w": O((0, 5.3, 5.3)), **_SET3},
                            "ball": _ball((0, 2.6, "a"), (3.0, 9, "w"), flights=[(2.6, 3.0, "a", "w")])}, 6.0, {}),
    # L9-02 (C8-2): push, hit-ahead, a ~4.5 m/s run to the corner for ~1.3 s, then a settle (loop 8: cut 5 | 1 | 2 of 20,
    # the whole-label median read the run as a walk)
    "l9_push_pass_corner_settle": ({"actors": {"a": OL((2.0, 22.0), (0.0, 3.9, [(2.0, 11.0), (5.6, 6.0)], ("pace", 0.5, 0.5)),
                                                       (3.9, 6.4, [(6.6, 2.0)], "trap")), "w": O((0, -5.3, 5.3)), **_SET3},
                                    "ball": _ball((0, 2.5, "a"), (2.9, 9, "w"), flights=[(2.5, 2.9, "a", "w")])}, 7.0, {}),
    # ... and the same run after a ~3 m/s jog-up (the n0.5 g493 pattern)
    "l9_jog_pass_corner_settle": ({"actors": {"a": OL((2.0, 17.5), (0.0, 3.7, [(2.0, 11.0), (5.6, 6.0)], ("pace", 0.58, 0.51)),
                                                      (3.7, 6.2, [(6.6, 2.0)], "trap")), "w": O((0, -5.3, 5.3)), **_SET3},
                                   "ball": _ball((0, 2.1, "a"), (2.5, 9, "w"), flights=[(2.1, 2.5, "a", "w")])}, 7.0, {}),
    # L9-02 margin: jog ~3 m/s, pass, ~1.9 m/s relocation (a relocation pace near the gait speed is not a run on noise)
    "l9_jog_pass_reloc18": ({"actors": {"a": OL((2.0, 17.0), (0.0, 4.75, [(2.0, 11.0), (5.5, 8.5)], ("pace", 0.45, 0.58))),
                                        "w": O((0, -5.3, 5.3)), **_SET3},
                             "ball": _ball((0, 2.1, "a"), (2.5, 9, "w"), flights=[(2.1, 2.5, "a", "w")])}, 6.0, {}),
    # L9-03 (C8-3): an off-ball jog-up (~3 m/s) into a walk-pace relocation vs a set defense / with 2 defenders still back
    "l9_offball_jog_walk": ({"actors": {"h": O((0, -3.0, 8.0)), "a": OL((2.0, 17.0), (0.0, 5.0, [(2.0, 11.0), (5.5, 8.5)], ("pace", 0.43, 0.58))),
                                        **_SET3}, "ball": held("h", 9)}, 6.5, {}),
    "l9_offball_jog_walk_defback": ({"actors": {"h": O((0, -3.0, 8.0)), "a": OL((2.0, 17.0), (0.0, 5.0, [(2.0, 11.0), (5.5, 8.5)], ("pace", 0.43, 0.58))),
                                                **_DEFBACK}, "ball": held("h", 9)}, 6.5, {}),
    # ... while an off-ball sprint over half court into the rim stays a transition run
    "l9_offball_sprint": ({"actors": {"h": O((0, -5.3, 5.3)), "a": OL((3.0, 21.0), (0.0, 3.8, [(3.0, 12.0), (0.6, 1.0)], "trap"))},
                           "ball": held("h", 8)}, 5.0, {}),
}
ALL_SCEN.update(L9)


def test_l9_01_push_is_a_structural_transition_and_the_burst_has_no_margin():
    # jog-up, pass, burst vs a set defense: half-court pass-and-cuts (loop 8: 0.48 and 0.12)
    assert _rate("l9_jog_pass_burst45", "cut_basket", {"cutter": "a"}) >= 0.7
    assert _rate("l9_jog_pass_burst42", "cut_basket", {"cutter": "a"}) >= 0.35
    # pushes that hit ahead and keep running (or accelerate) are transitions (loop 8 passed l9_push_pass_accel 1 in 20)
    for name in ("l8_push_pass_sprint", "l9_push_pass_accel", "l6_push_run"):
        for det in ("cut", "cut_basket"):
            assert _rate(name, det, {"cutter": "a"}, sigmas=(0.2, 0.3, 0.5), seeds=range(20)) == 0.0, (name, det)
    p = cuts.PARAMS["cu_postrules"]
    assert "carry_burst_k" not in p and p["carry_push_mps"] == 4.0  # TRN-P08 push speed


def test_l9_02_keeps_running_is_judged_on_the_post_release_segment():
    # a push that hits ahead and sprints to the corner before settling is a transition fill (loop 8: cut 5 | 1 | 2 of 20)
    for det, role in (("cut", "cutter"), ("cut_basket", "cutter"), ("cut_banana", "cutter"), ("relocate", "player")):
        assert _rate("l9_push_pass_corner_settle", det, {role: "a"}, sigmas=(0.2, 0.3, 0.5), seeds=range(20)) == 0.0, det
    # ... and so is the same run after a jog-up (loop 8 read the 3.5 s label's median as a walk: half-court)
    assert sum(_carry_call("l9_jog_pass_corner_settle", s, sg, b_len_s=3.5) for sg in (0.2, 0.3) for s in range(10)) >= 18
    # a 1.9 m/s relocation after the pass stays half-court at noise (the one-sided carry_post_k margin)
    assert sum(not _carry_call("l9_jog_pass_reloc18", s, sg, b_len_s=2.5) for sg in (0.3, 0.5) for s in range(10)) >= 16
    for name in ("l8_jog_pass_slow_relocate", "l8_jog25_pass_slow_relocate"):
        assert sum(not _carry_call(name, s, sg, b_len_s=2.5) for sg in (0.2, 0.3, 0.5) for s in range(10)) >= 27, name
    p = cuts.PARAMS["cu_postrules"]
    assert 1.0 <= p["carry_post_s"] <= 1.5 and p["carry_post_k"] > 0


def test_l9_03_off_ball_runner_who_slows_after_the_crossing_is_half_court():
    # off-ball jog-up into a walk-pace relocation vs a set defense (loop 8: every off-ball run was a transition)
    assert sum(not _carry_call("l9_offball_jog_walk", s, sg) for sg in (0.2, 0.3) for s in range(10)) >= 18
    # with two defenders still back, rule (2) keeps it a transition
    assert all(_carry_call("l9_offball_jog_walk_defback", s, sg) for sg in (0.2, 0.3, 0.5) for s in range(10))
    # an off-ball sprint into the rim stays a transition run
    for det in ("cut", "cut_basket"):
        assert _rate("l9_offball_sprint", det, {"cutter": "a"}, sigmas=(0.2, 0.3, 0.5)) == 0.0, det


def test_l9_04_dribble_with_a_holder_dropout_is_on_ball():
    # the handler keeps the ball (a dribble drive that bursts 1.3x) but the holder flag drops for 0.85 s around the label
    # start, so his holder run ends before the label and the next one is his own: on-ball, not a pass and cut
    out = []
    for sg in (0.2, 0.3):
        for seed in range(10):
            spec, dur, attrs = ALL_SCEN["l8_jog_drive_keep"]
            _, sc = build(spec, dur, seed, sigma=sg, **attrs)
            hc = cuts.PARAMS["cut"]["frontcourt_y_max_m"]
            tx = int(np.flatnonzero(np.nan_to_num(sc.k("a").y, nan=99.0) > hc)[-1])
            a = tx + cuts.F(0.6)
            sc.holder[a - cuts.F(0.15):a + cuts.F(0.7)] = None
            c = cuts._ctx(sc)
            b = min(c.n - 1, a + cuts.F(1.5))
            lo = max(0, a - cuts.F(cuts.PARAMS["cut"]["transition_carry_s"]))
            assert any(r_[0] == "a" and r_[2] < a for r_ in c.holder_runs()) and not any(r_[0] == "a" and r_[1] < a < r_[2] for r_ in c.holder_runs())
            out.append(cuts._transition_carry(c, "a", tx, lo, a, b))
    assert sum(out) == 20


def test_yaml_changes_loop9_recorded():
    ch = cuts.DOC.get("changes_loop9")
    assert ch and all({"id", "what", "why", "evidence"} <= set(c) for c in ch)
    ids = {c["id"].split()[0] for c in ch}
    assert {"L9-00", "L9-01", "L9-02", "L9-03", "L9-04", "L9-05"} <= ids
    assert cuts.DOC["version"] == "0.9.0"
    ev = " ".join(c["evidence"] for c in ch)
    assert "realdata.py" in ev and "team_ends" in ev


# --------------------------------------------------------------------------------------
# Realistic speeds (fix F15)
# --------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", sorted(ALL_SCEN))
def test_scenario_truth_speed_is_realistic(name):
    spec, dur, _ = ALL_SCEN[name]
    truth, _ = scenario(spec, dur, 0.01, 0)
    for aid in spec["actors"]:
        pk = float(np.max(truth_speed(truth, aid)[1:]))
        assert pk <= MAX_TRUTH_MPS, f"{name}:{aid} truth peak {pk:.1f} m/s > {MAX_TRUTH_MPS}"


# --------------------------------------------------------------------------------------
# Noise sweep (fix F15): 10 seeds x sigma_p 0.2 / 0.3 / 0.5, plus mirrored copies at 0.3
# --------------------------------------------------------------------------------------
SWEEP_RUNS = [(s, seed, False) for s in SWEEP_SIGMAS for seed in SWEEP_SEEDS] + [(0.3, seed, True) for seed in SWEEP_SEEDS]
# recall floors per detector at sigma 0.2 and 0.3 (default) and at 0.5 (reported; a floor guards regressions)
RECALL_FLOOR = 0.8
# sigma 0.5 floors guard regressions. Loop 2 (F08 residual) raised the I-cut (0.1 -> 0.5) and veer (0.0 -> 0.4)
# floors with their high-noise-tier rules; the wiper needs both a flare and a pin-down to survive (known limit)
RECALL_FLOOR_05 = {"default": 0.5, "cut_i": 0.5, "cut_veer": 0.4, "wiper": 0.1}
NEG_CEIL = {0.2: 0.1, 0.3: 0.1, 0.5: 0.2}
# the author's flare screener stands 0.9 m from the user: at sigma 0.5 the measured distance passes 1.2 m + 2 sigma
# in about 3 of 10 runs and the fade fires (capped at 0.6, F09)
NEG_CEIL_OVERRIDE = {("cut_fade", 0.5): 0.3}


@lru_cache(maxsize=None)
def _sweep():
    """{(case index, 'pos'|'neg', sigma, seed, mirror): [(t0_s, conf)] matching events, truth t0}."""
    need = defaultdict(set)  # scenario -> detectors to run
    for det, pos, _, _, neg in CASES:
        need[pos].add(det)
        need[neg].add(det)
    out = {}
    for name, dets in need.items():
        spec, dur, attrs = S[name]
        for sg, seed, mir in SWEEP_RUNS:
            truth, sc = build(spec, dur, seed, sigma=sg, mirror=mir, **attrs)
            evs = {d: cuts.DETECTORS[d](sc) for d in dets}
            for i, (det, pos, roles, t0fn, neg) in enumerate(CASES):
                for role, nm in (("pos", pos), ("neg", neg)):
                    if nm != name:
                        continue
                    m = [(e.t0 * DT, e.conf) for e in _matching(evs[det], det, roles)]
                    out[(i, role, sg, seed, mir)] = (m, t0fn(truth) if role == "pos" else None)
    return out


def _sweep_rates(i):
    res = _sweep()
    rec, neg = defaultdict(list), defaultdict(list)
    for sg, seed, mir in SWEEP_RUNS:
        key = (sg, mir)
        m, tt = res[(i, "pos", sg, seed, mir)]
        rec[key].append(any(tt is None or abs(t - tt) <= SWEEP_TOL_S for t, _ in m))
        mn, _ = res[(i, "neg", sg, seed, mir)]
        neg[key].append(bool(mn))
    return {k: float(np.mean(v)) for k, v in rec.items()}, {k: float(np.mean(v)) for k, v in neg.items()}


@pytest.mark.parametrize("i", range(len(CASES)), ids=[f"{c[0]}:{c[1]}" for c in CASES])
def test_noise_sweep_recall_and_negatives(i):
    det = CASES[i][0]
    rec, neg = _sweep_rates(i)
    msg = f"{det}: recall {rec}, negative fire rate {neg}"
    for sg in (0.2, 0.3):
        assert rec[(sg, False)] >= RECALL_FLOOR, msg
    assert rec[(0.3, True)] >= RECALL_FLOOR, msg
    assert rec[(0.5, False)] >= RECALL_FLOOR_05.get(det, RECALL_FLOOR_05["default"]), msg
    for (sg, _), v in neg.items():
        assert v <= NEG_CEIL_OVERRIDE.get((det, sg), NEG_CEIL[sg]), msg


@pytest.mark.parametrize("name", sorted(S))
def test_exact_mirror_symmetry(name):
    """Negating x of every noisy track gives the same events (kinds, actors, t0, conf, variant)."""
    spec, dur, attrs = S[name]
    _, tracks = scenario(spec, dur, 0.3, 0)
    mtracks = []
    for t in tracks:
        m = mvlib.Track(t.oid, -t.x, t.y.copy(), t.sigma_p.copy(), team=t.team, role=t.role)
        mtracks.append(m)

    def evs(trs):
        sc = mvlib.build_scene(trs)
        for k, v in attrs.items():
            setattr(sc, k, v)
        return sorted([(e.kind, cuts._primary_actor(e), e.t0, round(e.conf, 3), e.attrs.get("variant"))
                       for e in cuts.detect_all(sc, resolve_labels=False)], key=str)

    assert evs(tracks) == evs(mtracks)


# --------------------------------------------------------------------------------------
# Regression tests for the loop-1 failures (F01-F21)
# --------------------------------------------------------------------------------------
def _rate(name, det, roles, sigmas=(0.2, 0.3), seeds=range(10), t0fn=None, tol=SWEEP_TOL_S, pred=None, mirror=False):
    """Fraction of runs in which det emits a matching event (optionally |t0 - truth| <= tol, pred(event))."""
    spec, dur, attrs = ALL_SCEN[name]
    hits, n = 0, 0
    for sg in sigmas:
        for seed in seeds:
            truth, sc = build(spec, dur, seed, sigma=sg, mirror=mirror, **attrs)
            m = _matching(cuts.DETECTORS[det](sc), det, roles)
            if t0fn is not None:
                tt = t0fn(truth)
                m = [e for e in m if abs(e.t0 * DT - tt) <= tol]
            if pred is not None:
                m = [e for e in m if pred(e)]
            hits += bool(m)
            n += 1
    return hits / n


def test_f01_ucla_needs_a_high_post_player():
    assert _rate("pass_cut_noscreen", "cut_ucla", {"cutter": "a"}, sigmas=(0.2, 0.3, 0.5)) == 0.0
    assert _rate("pass_cut_noscreen", "cut_basket", {"cutter": "a"}) >= 0.8
    # the real UCLA keeps its t0 at the high-post pass-by in every variant
    assert _rate("ucla_top", "cut_ucla", {"cutter": "a"}, sigmas=(0.2, 0.3, 0.5),
                 t0fn=lambda T: closest(T, "a", "s", 2.0, 4.5)) >= 0.9


def test_f01_ucla_no_screen_variant_is_capped():
    spec, dur, attrs = ALL_SCEN["ucla_top"]
    for seed in range(10):
        _, sc = build(spec, dur, seed, sigma=0.5, **attrs)
        for e in cuts.detect_cut_ucla(sc):
            if e.attrs["variant"] == "ucla_path_no_screen":
                assert e.conf <= cuts.G["identity_cap"] and not e.attrs["strict"]


def test_f02_f03_screen_cut_window_and_departure_at_high_noise():
    assert _rate("turnout_lane", "cut_turnout", {"cutter": "u"}, sigmas=(0.5,),
                 t0fn=lambda T: closest(T, "u", "s", 2.0, 4.0)) >= 0.7
    assert _rate("turnout", "cut_turnout", {"cutter": "u"}, sigmas=(0.5,)) >= 0.7
    assert _rate("flex", "cut_flex", {"cutter": "u"}, sigmas=(0.5,)) >= 0.7
    # the 'within' test counts frames exactly as the end search: F(total_s) frames always pass
    assert cuts.F(2.0) * DT > 2.0  # the rounding that broke the seconds comparison


def test_f04_fill_from_a_short_distance():
    assert _rate("fill_slot", "fill", {"filler": "b"}, t0fn=lambda T: leave_from(T, "a", 2.0, 2.0)) >= 0.8
    assert _rate("fill_short", "fill", {"filler": "b"}, sigmas=(0.2, 0.3, 0.5)) <= 0.1


def _median_conf(name, det, roles, sigma=0.3):
    spec, dur, attrs = ALL_SCEN[name]
    cs = []
    for seed in range(10):
        _, sc = build(spec, dur, seed, sigma=sigma, **attrs)
        m = _matching(cuts.DETECTORS[det](sc), det, roles)
        cs.append(max((e.conf for e in m), default=0.0))
    return float(np.median(cs))


def test_f05_margins_are_tested_at_their_extremum():
    assert _median_conf("loop_back", "cut_loop", {"cutter": "u"}) >= 0.8
    assert _median_conf("loop", "cut_loop", {"cutter": "u"}) >= 0.8
    assert _median_conf("wb_under", "cut_weak_baseline", {"runner": "c"}) >= 0.8
    assert _median_conf("sprint_half_real", "sprint_to_corner", {"player": "p"}) >= 0.8


def test_f06_standing_post_near_the_path_keeps_the_basket_cut():
    assert _rate("bk_past_post", "cut_basket", {"cutter": "c"}, t0fn=lambda T: onset(T, "c", 2.0)) >= 0.8


def test_f07_tight_curl_direction():
    assert _rate("curl_down", "cut_curl", {"user": "u"}, t0fn=lambda T: closest(T, "u", "s", 1.5, 4.5)) >= 0.8


def test_f08_high_noise_tier_and_turn_reads():
    spec, dur, _ = S["vcut"]
    for sg, want in ((0.3, False), (0.44, False), (0.45, True), (0.5, True)):
        _, sc = build(spec, dur, 0, sigma=sg)
        assert cuts._ctx(sc).high_noise("c") is want, sg
    # a planted 120 deg turn reads within 10 deg at sigma 0.5 (it read about 104 deg with the 0.1 s skip)
    reads = []
    for seed in range(10):
        p1, h = (4.0, 4.6), math.radians(90 - 120)
        p2 = (p1[0] + 2.6 * math.cos(h), p1[1] + 2.6 * math.sin(h))
        spec = {"actors": {"h": OL((-5.0, 5.0)), "u": OL((4.0, 2.0), (1.5, 2.4, [p1]), (2.5, 3.4, [p2]))}, "ball": held("h")}
        _, sc = build(spec, 5.0, seed, sigma=0.5)
        tt = [t for t in cuts._ctx(sc).turns("u", 20) if abs(t["t"] * DT - 2.45) < 0.4]
        if tt:
            reads.append(abs(tt[0]["A"]))
    assert len(reads) >= 9 and abs(np.median(reads) - 120) <= 10, reads


def test_f09_flare_and_fade_split_a_borderline_screen():
    spec, dur, attrs = ALL_SCEN["flare_elbow"]
    for seed in range(10):
        _, sc = build(spec, dur, seed, sigma=0.3, **attrs)
        fades = [e for e in cuts.detect_cut_fade(sc) if e.actors.get("user") == "u"]
        assert not any(e.attrs["strict"] for e in fades), seed  # a fade next to a screener is never strict
        for e in fades + [e for e in cuts.detect_cut_flare(sc) if e.actors.get("user") == "u"]:
            assert 0.0 <= e.attrs["p_flare_vs_fade"] <= 1.0
    # the user starts 1.12 m from the screener (contact edge 1.2 m): flare and fade split the runs, and every
    # run gets one of the two
    assert _rate("flare_elbow", "cut_flare", {"user": "u"}) >= 0.5
    spec, dur, attrs = ALL_SCEN["flare_elbow"]
    for seed in range(10):
        _, sc = build(spec, dur, seed, sigma=0.3, **attrs)
        assert cuts.detect_cut_flare(sc) or cuts.detect_cut_fade(sc), seed
    assert _rate("fade_corner", "cut_fade", {"user": "u"}) >= 0.8


def test_f10_backdoor_does_not_fire_on_chin_cuts():
    # chin cuts use an elbow back screen after the reversal: the screen cuts own them. (The tester's
    # chin_noscreen, the same path with no screener and the defender in the passing lane, is a backdoor.)
    for name in ("chin_wing", "chin"):
        assert _rate(name, "cut_backdoor", {"cutter": "c"}, sigmas=(0.2, 0.3, 0.5)) <= 0.1, name
    # a defender trailing on the high side is not a deny stance (bd_no_overplay geometry, rim-side defender)
    spec = {"actors": {"h": OL((2.5, 7.2)), "c": OL((6.0, 4.6), (1.5, 2.1, [(6.4, 6.0)]), (2.2, 4.4, [(0.8, 0.8)])),
                       "d": DL((5.2, 4.0), (2.3, 3.9, [(1.6, 1.4)]))}, "ball": held("h")}
    hits = 0
    for seed in range(10):
        _, sc = build(spec, 5.5, seed, sigma=0.3)
        hits += bool(_matching(cuts.detect_cut_backdoor(sc), "cut_backdoor", {"cutter": "c"}))
    assert hits <= 1
    assert _rate("backdoor", "cut_backdoor", {"cutter": "c"}, t0fn=lambda T: 2.15) >= 0.8


def test_f11_pin_down_screener_that_holds():
    assert _rate("pindown_wl", "cut_pin_down", {"cutter": "u"}, t0fn=lambda T: closest(T, "u", "s", 2.3, 4.0)) >= 0.8


def test_f12_front_cut_evaluated_at_the_pass_by():
    assert _rate("front_pass", "cut_front", {"cutter": "a"}, t0fn=lambda T: onset(T, "a", 2.1)) >= 0.8


def test_f13_banana_turn_measure_and_corners():
    assert _rate("banana_slot", "cut_banana", {"cutter": "c"}, t0fn=lambda T: onset(T, "c", 2.0)) >= 0.8
    assert _rate("banana_flat", "cut_banana", {"cutter": "c"}, sigmas=(0.2, 0.3, 0.5)) <= 0.1
    # planted corners (L, curved basket with a corner) are not bananas
    for name in ("lcut", "curved_basket"):
        assert _rate(name, "cut_banana", {"cutter": "c"}) <= 0.1, name


def test_f14_rub_pass_by_enters_confidence():
    spec, dur, attrs = ALL_SCEN["rub_wide"]
    for seed in range(10):
        for sg in (0.2, 0.3, 0.5):
            _, sc = build(spec, dur, seed, sigma=sg, **attrs)
            for e in _matching(cuts.detect_cut_rub(sc), "cut_rub", {"cutter": "u"}):
                assert "pass_by" in e.attrs["margins"] and not e.attrs["strict"]
    assert _rate("rub_wide", "cut_rub", {"cutter": "u"}, sigmas=(0.2,)) <= 0.1
    assert _rate("bk_past_post", "cut_rub", {"cutter": "c"}, sigmas=(0.2, 0.3)) <= 0.1


def test_f15_sweep_layout():
    assert len(SWEEP_SEEDS) == 10 and SWEEP_SIGMAS == (0.2, 0.3, 0.5)
    assert any(m for _, _, m in SWEEP_RUNS)


def test_f16_no_fade_off_downscreen_on_baseline_exits():
    for name in ("bl_exit", "blexit_left"):
        assert _rate(name, "cut_fade", {"user": "u"}, sigmas=(0.2, 0.3, 0.5),
                     pred=lambda e: e.attrs["variant"] == "fade_off_downscreen") == 0.0, name


def test_f17_baseline_runner_is_not_a_low_flash():
    assert _rate("baseline", "cut_flash", {"cutter": "c"}, sigmas=(0.2, 0.3, 0.5),
                 pred=lambda e: e.attrs["flash_kind"] == "low") == 0.0
    assert _rate("flash", "cut_flash", {"cutter": "c"}) >= 0.8


def test_f18_min_duration_is_enforced():
    _, sc = build(*S["basket"][:2], 1)
    k = sc.k("c")
    ts = cuts.Tests()
    ts.ge("x", 1.0, 0.0, 0.1)
    need = cuts.ITEMS["sprint_to_corner"]["min_duration_s"]
    n_short = int(need / DT) - 1
    assert cuts._emit("sprint_to_corner", {"player": "c"}, 60, 60, 60 + n_short, ts, [k]) is None
    assert cuts._emit("sprint_to_corner", {"player": "c"}, 60, 60, 60 + n_short + 2, ts, [k]) is not None
    # every emitted event in the smoke scenarios respects its item's minimum duration
    for name in ("basket", "sprint_half", "fill", "wiper", "rim_run"):
        spec, dur, attrs = S[name]
        _, sc = build(spec, dur, 1, **attrs)
        for e in cuts.detect_all(sc):
            md = cuts.ITEMS[e.kind].get("min_duration_s")
            assert not md or (e.end - e.start) * DT >= md - 1e-9, (e.kind, e.start, e.end)


def test_f19_thresholds_live_in_the_yaml():
    want = {"lift": ["screener_precedence_s"], "shake": ["within_s"], "rim_run": ["start_before_s"],
            "cut_backdoor": ["start_before_s", "dedup_s", "deny_lane_m", "screen_skip_before_s"],
            "fill": ["vacate_before_s", "vacate_after_s", "settle_s", "pre_s"],
            "cut_banana": ["kappa_sig_per_m", "arc_sig_m", "kappa_local_max_per_m"],
            "cut_zipper": ["scr_arrive_back_s"], "cut_pin_down": ["scr_arrive_back_s"], "cut_flash": ["low_min_y_m"],
            "cut_flare": ["pre_s"], "cut_fade": ["pre_s", "down_scr_dy_m", "down_scr_back_s"]}
    for item, names in want.items():
        for nm in names:
            assert nm in cuts.PARAMS[item], (item, nm)
    # the overrides are read at call time
    _, sc = build(*S["lift"][:2], 1)
    assert cuts.detect_lift(sc, screener_precedence_s=0.5) is not None
    _, sc = build(*S["shake"][:2], 1)
    assert _matching(cuts.detect_shake(sc), "shake", {"player": "k"})
    assert not _matching(cuts.detect_shake(sc, within_s=0.2), "shake", {"player": "k"})


def test_f20_wing_l_with_a_realistic_turn():
    assert _rate("l_wing", "cut_l", {"cutter": "c"}, pred=lambda e: e.attrs["variant"] == "wing_l") >= 0.7


def test_f21_jog_toward_the_rim_is_not_a_cut():
    for det, roles in (("cut", {"cutter": "a"}), ("cut_basket", {"cutter": "a"})):
        assert _rate("jog_rim_slow", det, roles, sigmas=(0.2, 0.3, 0.5)) <= 0.15, det
        assert _rate("jog_rim_slow", det, roles, sigmas=(0.2, 0.3, 0.5), mirror=True) <= 0.2, det
        # what survives is near the threshold: never strict
        assert _rate("jog_rim_slow", det, roles, sigmas=(0.2, 0.3, 0.5), pred=lambda e: e.attrs["strict"]) == 0.0, det


# --------------------------------------------------------------------------------------
# Regression tests for the loop-2 fixes (confirmer regressions and still-failing items)
# --------------------------------------------------------------------------------------
def test_r1_blind_pig_and_backdoor_rim_window():
    # the 2.0 s rim window fits a 7-8 m rim leg at peak <= 7 m/s once t_rev sits at the plant (was 5/10 at 0.5)
    assert _rate("blind_pig", "blind_pig", {"cutter": "c"}, sigmas=(0.5,)) >= 0.7
    assert _rate("blind_pig", "blind_pig", {"cutter": "c"}, sigmas=(0.2, 0.3)) >= 0.9
    assert cuts.PARAMS["cut_backdoor"]["rim_within_s"] == 2.0


def test_r1_deny_branch_needs_a_rimward_start():
    # the step-out onset (1.5 s) of a short backdoor is not a deny cut: the reversal (2.15 s) keeps t0
    assert _rate("bd_short", "cut_backdoor", {"cutter": "c"}, sigmas=(0.2, 0.3), t0fn=lambda T: 2.15) >= 0.9
    spec, dur, attrs = ALL_SCEN["bd_short"]
    for seed in range(10):
        _, sc = build(spec, dur, seed, sigma=0.2, **attrs)
        for e in _matching(cuts.detect_cut_backdoor(sc), "cut_backdoor", {"cutter": "c"}):
            assert abs(e.t0 * DT - 2.15) <= SWEEP_TOL_S, (seed, e.t0 * DT)
    # a real deny back-cut (from rest, straight to the rim) still passes, and carries the rim-ward test
    assert _rate("bd_deny", "cut_backdoor", {"cutter": "c"}, sigmas=(0.2, 0.3), t0fn=lambda T: onset(T, "c", 2.0)) >= 0.9
    _, sc = build(*ALL_SCEN["bd_deny"][:2], 0, sigma=0.2)
    evs = _matching(cuts.detect_cut_backdoor(sc), "cut_backdoor", {"cutter": "c"})
    assert evs and all("deny_rimward" in e.attrs["margins"] for e in evs if e.attrs["Dpsi_rev"] is None)


def test_r2_no_duplicate_turn_events():
    for name in ("vcut", "icut", "lcut", "i_slot"):
        spec, dur, attrs = ALL_SCEN[name]
        for sg in (0.2, 0.5):
            for seed in range(10):
                _, sc = build(spec, dur, seed, sigma=sg, **attrs)
                c = cuts._ctx(sc)
                for o in sc.offense:
                    ts = [t["t"] for t in c.turns(o, 20)]
                    assert len(ts) == len(set(ts)), (name, sg, seed, o)
                evs = cuts.detect_cut_v(sc) + cuts.detect_cut_i(sc) + cuts.detect_cut_l(sc)
                keys = [(e.kind, cuts._primary_actor(e), e.t0) for e in evs]
                assert len(keys) == len(set(keys)), (name, sg, seed)


def test_f08r_veer_in_the_high_noise_tier():
    # away window padded and defender tests at the closest approach within +-0.3 s (was 0/10 and 1/10 at 0.5)
    assert _rate("veer_slot", "cut_veer", {"cutter": "u"}, sigmas=(0.5,), t0fn=lambda T: 2.35) >= 0.6
    assert _rate("veer", "cut_veer", {"cutter": "u"}, sigmas=(0.5,), t0fn=lambda T: 2.35) >= 0.4
    assert _rate("veer_slot", "cut_veer", {"cutter": "u"}, sigmas=(0.2, 0.3), t0fn=lambda T: 2.35) >= 0.9
    # the defender must still be near: a far defender gives no veer at any sigma
    assert _rate("veer_far", "cut_veer", {"cutter": "u"}, sigmas=(0.2, 0.3, 0.5)) == 0.0
    # the pad applies only in the high-noise tier
    _, sc = build(*ALL_SCEN["veer_slot"][:2], 0, sigma=0.3)
    assert not cuts._ctx(sc).high_noise("u")


def test_f08r_i_cut_in_the_high_noise_tier():
    # legs against 0.7 m in the high-noise tier (smoother apex bias) with a leg-balance test (was 2/10 at 0.5)
    assert _rate("i_slot", "cut_i", {"cutter": "c"}, sigmas=(0.5,), t0fn=lambda T: 2.6) >= 0.5
    assert _rate("icut", "cut_i", {"cutter": "c"}, sigmas=(0.5,), t0fn=lambda T: 2.65) >= 0.5
    # a run that stops (long in-leg, jitter out-leg) and standing players give no I-cut
    assert _rate("sprint_half_real", "cut_i", {"cutter": "p"}, sigmas=(0.5,)) <= 0.1
    spec, dur, attrs = ALL_SCEN["still"]
    for seed in range(10):
        _, sc = build(spec, dur, seed, sigma=0.5, **attrs)
        assert not cuts.detect_cut_i(sc), seed
    _, sc = build(*ALL_SCEN["i_slot"][:2], 3, sigma=0.5)
    for e in cuts.detect_cut_i(sc):
        assert "leg_balance" in e.attrs["margins"]


def test_f09r_flare_contact_searched_before_a_late_onset():
    # pre_s 1.0 s: the user stands 1.12 m from the screener before the MOVE (flare 0.6 -> 0.8 at sigma 0.2 / 0.3)
    assert _rate("flare_elbow", "cut_flare", {"user": "u"}, sigmas=(0.2, 0.3)) >= 0.8
    assert _rate("flare_elbow", "cut_fade", {"user": "u"}, sigmas=(0.2, 0.3)) <= 0.2
    assert _rate("fade_corner", "cut_fade", {"user": "u"}, sigmas=(0.2, 0.3, 0.5)) >= 0.9
    assert cuts.PARAMS["cut_flare"]["pre_s"] == cuts.PARAMS["cut_fade"]["pre_s"] == 1.0


def test_f21r_jog_toward_the_rim_never_passes_the_look_elsewhere_edge():
    for det, roles in (("cut", {"cutter": "a"}), ("cut_basket", {"cutter": "a"})):
        for mirror in (False, True):
            assert _rate("jog_rim_slow", det, roles, sigmas=(0.2, 0.3, 0.5), mirror=mirror) == 0.0, (det, mirror)
    # the first window carries no shift; real cuts keep their recall (sweep floors) and conf
    _, sc = build(*S["basket"][:2], 1)
    assert all(e.conf >= 0.8 for e in cuts.detect_cut(sc))


def test_c1_curl_t0_is_the_centre_of_the_wrap():
    t0fn = lambda T: closest(T, "u", "s", 1.5, 4.0)  # noqa: E731
    assert _rate("curl", "cut_curl", {"user": "u"}, sigmas=(0.5,), t0fn=t0fn) >= 0.9
    assert _rate("curl", "cut_curl", {"user": "u"}, sigmas=(0.2, 0.3), t0fn=t0fn) >= 0.95
    # one curl per (user, screener) wrap
    for seed in range(10):
        _, sc = build(*S["circle"][:2], seed, sigma=0.5)
        evs = cuts.detect_cut_curl(sc)
        for i, e in enumerate(evs):
            for e2 in evs[i + 1:]:
                same = e.actors == e2.actors
                assert not (same and abs(e.t0 - e2.t0) <= cuts.F(cuts.PARAMS["cut_curl"]["turn_window_s"])), seed


def test_yaml_changes_loop2_recorded():
    ch = cuts.DOC.get("changes_loop2")
    assert ch and all({"id", "what", "why", "evidence"} <= set(c) for c in ch)
    ids = {c["id"].split()[0] for c in ch}
    for f in ("R1", "R2", "F08r", "F09r", "F21r", "C1", "F13r", "F14r"):
        assert f in ids, f
    for item, name in (("cut_veer", "turn_pad_high_noise_s"), ("cut_i", "leg_min_high_noise_m"),
                       ("cut_i", "leg_ratio_high_noise"), ("cut", "lookelse_k"), ("cut_curl", "t0_flat_k"),
                       ("cut_backdoor", "deny_rimward_s"), ("cut_backdoor", "deny_rimward_dr_m")):
        assert name in cuts.PARAMS[item], (item, name)


# --------------------------------------------------------------------------------------
# Structural and acceptance checks
# --------------------------------------------------------------------------------------
def test_every_detector_has_cases():
    covered = {c[0] for c in CASES}
    needs = {k for k in cuts.DETECTORS if not cuts.ITEMS[k].get("needs_data")}
    assert needs <= covered, sorted(needs - covered)


def test_yaml_is_single_source():
    for k in cuts.DETECTORS:
        it = cuts.ITEMS[k]
        assert it["detector"] in (True, False)
        for field in ("id", "level", "name", "aliases", "actors", "t0", "rule", "params", "min_duration_s", "outputs",
                      "confidence", "noise", "conflicts_resolved", "sources", "status"):
            assert field in it, (k, field)
        for name, v in (it.get("params") or {}).items():
            assert isinstance(v, dict) and "value" in v and "unit" in v, (k, name)
    # overriding a parameter changes the result (parameters are read at call time)
    _, sc = build(*S["basket"][:2], 1)
    assert cuts.detect_cut(sc)
    assert not cuts.detect_cut(sc, disp_m=12.0)
    with pytest.raises(TypeError):
        cuts.detect_cut(sc, not_a_param=1)


def test_yaml_changes_loop1_recorded():
    ch = cuts.DOC.get("changes_loop1")
    assert ch and all({"id", "what", "why", "evidence"} <= set(c) for c in ch)
    ids = {c["id"].split()[0] for c in ch}
    for f in [f"F{i:02d}" for i in range(1, 22)]:
        assert f in ids, f


def test_needs_data_items_return_empty():
    _, sc = build(*S["basket"][:2], 1)
    for k, it in cuts.ITEMS.items():
        if it.get("needs_data"):
            assert cuts.DETECTORS[k](sc) == []


def test_chord_turn_reads_planted_reversal():
    """Check-fix OB.P6/P8: a step-out, 0.1 s plant and reversal must read close to its true angle."""
    spec, dur, _ = S["backdoor"]
    reads = []
    for seed in range(5):
        _, sc = build(spec, dur, seed)
        c = cuts._ctx(sc)
        tt = [t for t in c.turns("c", 90) if abs(t["t"] * DT - 2.15) <= 0.4]
        assert tt, f"no turn found (seed {seed})"
        reads.append(abs(tt[0]["A"]))
    true = abs(cuts._ang((0.4, 1.4), (0.8 - 6.4, 0.8 - 6.0)))
    assert abs(np.median(reads) - true) <= 15.0, (reads, true)


def test_still_players_make_no_moves():
    """Check-fix OB.P1: no MOVE onsets on standing players at sigma_p 0.3 m (5 seeds x 3 players x 5 s)."""
    spec, dur, _ = S["still"]
    n = 0
    for seed in range(5):
        _, sc = build(spec, dur, seed)
        n += len(cuts.detect_move(sc))
    assert n == 0


def test_detect_all_and_precedence():
    _, sc = build(*S["basket"][:2], 1)
    evs = cuts.detect_all(sc)
    kinds = {e.kind for e in evs}
    assert {"cut_basket", "cut_dive"} <= kinds
    prim = [e for e in evs if e.attrs.get("primary")]
    assert len({(cuts._primary_actor(e), e.kind) for e in prim}) == len(prim)
    dive = next(e for e in evs if e.kind == "cut_dive")
    basket = next(e for e in evs if e.kind == "cut_basket")
    assert dive.attrs["primary"] and basket.attrs["secondary_of"] == "cut_dive"


def test_event_contract():
    _, sc = build(*S["ucla"][:2], 1)
    for e in cuts.detect_all(sc):
        assert isinstance(e, mvlib.Event)
        assert 0.0 <= e.conf <= 1.0 and e.start <= e.t0 <= max(e.end, e.t0) and e.start <= e.end
        assert "margins" in e.attrs and "binding_test" in e.attrs


# --------------------------------------------------------------------------------------
# Loop 4: regression scenes for failure modes found on real (SportVU 2015-16) tracking.
# Synthetic only; no real data. Each negative fired on the loop-3 detector.
# --------------------------------------------------------------------------------------
L4 = {
    # L4-01: the defense holds the ball (rebound / steal / the other team's possession inside one clip); the
    # offensive wing's run to the rim is not an off-ball cut (loop 3: cut 10/10 at every sigma)
    "l4_def_ball": ({"actors": {"h": O((0, 0.0, 7.6)), "c": O((0, 5.3, 5.3), (2.0, 5.3, 5.3), (3.8, 0.8, 0.8)),
                                "d": D((0, 0.0, 9.6), (6.0, 0.3, 9.6))}, "ball": {"held": [(0, 8, "d")]}}, 6.0, {}),
    "l4_off_ball": ({"actors": {"h": O((0, 0.0, 7.6)), "c": O((0, 5.3, 5.3), (2.0, 5.3, 5.3), (3.8, 0.8, 0.8)),
                                "d": D((0, 0.0, 9.6), (6.0, 0.3, 9.6))}, "ball": {"held": [(0, 8, "h")]}}, 6.0, {}),
    # L4-02: a run that starts in the backcourt and goes all the way to the rim (transition), not a half-court cut
    "l4_backcourt_run": ({"actors": {"h": O((0, -3.0, 7.0)),
                                     "c": OL((2.0, 20.0), (1.0, 4.6, [(1.5, 8.0), (0.5, 0.8)], "trap"))},
                          "ball": {"held": [(0, 8, "h")]}}, 6.0, {}),
    # L4-04: perimeter shuffle, 1.4 m in and back out at a truth peak of 1.8 m/s (a jab / reset, not an I-cut)
    "l4_shuffle": ({"actors": {"h": TOP, "c": O((0, 6.0, 4.5), (2.0, 6.0, 4.5), (3.4, 5.0, 3.55), (3.5, 5.0, 3.55),
                                                (4.9, 6.0, 4.5))}, "ball": {"held": [(0, 8, "h")]}}, 6.0, {}),
    # L4-05: the 'vacator' only runs through the corner disc (never settles) -> nothing was vacated
    "l4_fill_vac_passing": ({"actors": {"h": TOP,
                                        "a": OL((5.0, 5.0), (1.0, 3.6, [(6.9, 1.2), (6.9, 0.2), (3.5, 0.6)], "trap")),
                                        "b": O((0, 5.3, 5.3), (2.6, 5.3, 5.3), (4.1, 6.9, 0.2))},
                             "ball": {"held": [(0, 8, "h")]}}, 5.5, {}),
    # L4-05: the corner is vacated, but the teammate runs through it along the baseline (no fill)
    "l4_fill_runthrough": ({"actors": {"h": TOP, "a": O((0, 6.95, 0.0), (2.0, 6.95, 0.0), (3.7, 1.0, 0.8)),
                                       "b": OL((5.3, 5.3), (2.6, 4.8, [(6.9, 1.0), (6.6, 0.2), (3.5, 0.9)], "trap"))},
                            "ball": {"held": [(0, 8, "h")]}}, 5.5, {}),
    # L4-06: a screener still settling (truth 0.75 m/s) and a jogger (1.0 m/s mean) next to the ball side
    "l4_drift": ({"actors": {"h": TOP, "s": OL((2.0, 4.0), (0.5, 5.5, [(4.0, 6.5)], "trap")),
                             "j": OL((-2.0, 4.0), (0.5, 3.0, [(-6.0, 6.5)], "trap"))},
                  "ball": {"held": [(0, 8, "h")]}}, 6.0, {}),
}
ALL_SCEN.update(L4)


def test_l4_01_no_cut_while_the_defense_has_the_ball():
    assert _rate("l4_def_ball", "cut", {"cutter": "c"}, sigmas=(0.2, 0.3, 0.5)) == 0.0
    assert _rate("l4_def_ball", "cut_basket", {"cutter": "c"}, sigmas=(0.2, 0.3, 0.5)) == 0.0
    # the same run with the offense holding the ball is a cut
    assert _rate("l4_off_ball", "cut", {"cutter": "c"}, sigmas=(0.2, 0.3, 0.5)) >= 0.9


def test_l4_02_backcourt_run_is_not_a_half_court_cut():
    assert _rate("l4_backcourt_run", "cut", {"cutter": "c"}, sigmas=(0.2, 0.3, 0.5)) == 0.0
    # it is still a MOVE
    assert _rate("l4_backcourt_run", "move", {"player": "c"}, sigmas=(0.2, 0.3, 0.5)) >= 0.9


def test_l4_04_shuffle_is_not_an_i_cut():
    # below the high-noise tier the out-leg peak separates the shuffle (reads 1.4-2.0 m/s) from an I (2.4-3.9 m/s)
    assert _rate("l4_shuffle", "cut_i", {"cutter": "c"}, sigmas=(0.2, 0.3)) <= 0.1
    # and the I-cut itself keeps its recall there
    assert _rate("icut", "cut_i", {"cutter": "c"}, sigmas=(0.2, 0.3), t0fn=lambda T: 2.65) >= 0.85


def test_l4_05_fill_needs_a_settled_vacator_and_a_settled_filler():
    assert _rate("l4_fill_vac_passing", "fill", {"filler": "b"}, sigmas=(0.2, 0.3, 0.5)) == 0.0
    assert _rate("l4_fill_runthrough", "fill", {"filler": "b"}, sigmas=(0.2, 0.3, 0.5)) <= 0.05
    # the settle tests are noise-aware: the plain fill keeps its recall at sigma_p 0.5
    assert _rate("fill", "fill", {"filler": "b"}, sigmas=(0.5,), t0fn=lambda T: leave_from(T, "a", 2.0, 2.0)) >= 0.8


def test_l4_06_stationary_is_no_stricter_on_precise_tracks():
    """A settling screener (0.75 m/s) reads stationary about as often on near-noiseless tracks as at sigma_p 0.2-0.3
    (loop 3: 0.0 at sigma 0.05 vs 0.56-0.75), and a 1.0 m/s jogger is never stationary."""
    spec, dur, _ = L4["l4_drift"]
    frac = {}
    for sg in (0.05, 0.1, 0.2, 0.3):
        fs, fj = [], []
        for seed in range(5):
            _, sc = build(spec, dur, seed, sigma=sg)
            c = cuts._ctx(sc)
            fs.append(c.stationary("s")[int(1.5 / DT):int(4.5 / DT)].mean())
            fj.append(c.stationary("j")[int(1.0 / DT):int(2.5 / DT)].mean())
        frac[sg] = float(np.mean(fs))
        assert max(fj) == 0.0, (sg, fj)
    assert min(frac.values()) >= 0.4, frac
    assert max(frac.values()) - min(frac.values()) <= 0.3, frac


# --------------------------------------------------------------------------------------
# Loop 5: regression scenes for the confirmer's loop-4 residuals (C4-A..C4-D), found on real SportVU tracking.
# Synthetic only; no real data. Each negative fired on the loop-4 detector.
# --------------------------------------------------------------------------------------
def _shift_y(spec, dy):
    """The same scene dy metres up the floor (dy = 16 puts it beyond half court, y > 12.7 m)."""
    out = {"actors": {}}
    for aid, a in spec["actors"].items():
        b = dict(a)
        if "wp" in a:
            b["wp"] = [(t, x, y + dy) for t, x, y in a["wp"]]
        else:
            b["start"] = (a["start"][0], a["start"][1] + dy)
            b["legs"] = [tuple([lg[0], lg[1], [(p[0], p[1] + dy) for p in lg[2]]] + list(lg[3:])) for lg in a["legs"]]
        out["actors"][aid] = b
    if "ball" in spec:
        out["ball"] = spec["ball"]
    return out


def _on_arc(r, deg):
    return (r * math.cos(math.radians(deg)), r * math.sin(math.radians(deg)))


_ARC0, _ARC1 = _on_arc(7.4, 42.0), _on_arc(7.4, 53.0)
L5 = {
    # L5-01 (C4-A): an I-cut, a veer and a banana run under the defended rim (after a rebound / inbound); loop 4:
    # cut_i 24/30, cut_veer 24/30, cut_banana 27/30 over sigma 0.2 / 0.3 / 0.5
    "l5_bc_icut": (_shift_y(S["icut"][0], 16.0), S["icut"][1], {}),
    "l5_bc_veer": (_shift_y(S["veer"][0], 16.0), S["veer"][1], {}),
    "l5_bc_banana": (_shift_y(S["banana"][0], 16.0), S["banana"][1], {}),
    # L5-01: a run that crosses half court and turns on the wing 1.0 s later (transition carry)
    "l5_carry_veer": ({"actors": {"h": TOP, "u": O((0, 6.5, 13.0), (2.0, 6.5, 6.0), (2.8, 4.9, 4.6), (2.9, 4.9, 4.6), (3.7, 5.7, 2.0)),
                                  "d": D((0, 4.3, 4.1))}, "ball": {"held": [(0, 8, "h")]}}, 5.1, {}),
    # L5-02 (C4-B): an out-and-back along the 7.4 m arc (no step toward the rim): a lateral jab, not an I-cut
    "l5_lateral_i": ({"actors": {"h": TOP, "c": O((0, *_ARC0), (2.0, *_ARC0), (2.6, *_ARC1), (2.7, *_ARC1), (3.3, *_ARC0))},
                      "ball": {"held": [(0, 8, "h")]}}, 5.0, {}),
    # L5-03 (C4-C): jogs past an always-near defender with a mild bend (marginal approach)
    "l5_veer_jog": ({"actors": {"h": TOP, "u": O((0, 6.6, 6.2), (0.8, 6.6, 6.2), (2.3, 5.2, 4.4), (3.6, 4.8, 1.0)),
                                "d": D((0, 4.3, 4.1))}, "ball": {"held": [(0, 8, "h")]}}, 4.6, {}),
    "l5_veer_jog2": ({"actors": {"h": TOP, "u": O((0, 7.4, 5.4), (0.8, 7.4, 5.4), (2.3, 5.3, 4.6), (3.6, 4.6, 1.5)),
                                 "d": D((0, 4.3, 4.1))}, "ball": {"held": [(0, 8, "h")]}}, 4.6, {}),
    # L5-04 (C4-D): scenes whose screen / ball-screen labels came out twice for one moment (tester harness lift_bs and
    # pop_low: neighbouring contact intervals of the same pair)
    "l5_lift_bs": ({"actors": {"h": OL((5.6, 5.2), (1.4, 2.8, [(2.8, 6.8)])), "s": OL((4.4, 5.6)),
                               "k": OL((6.9, 0.4), (2.3, 3.4, [(6.5, 3.0)]))}, "ball": {"held": [(0, 8, "h")]}}, 5.0, {}),
    "l5_pop_low": ({"actors": {"h": OL((5.8, 5.0)), "s": OL((2.6, 2.4)), "u": OL((1.0, 0.8), (1.8, 3.4, [(4.6, 4.0)]))},
                    "ball": {"held": [(0, 8, "h")]}}, 4.5, {}),
    "l5_veer_shadow": ({"actors": {"h": TOP, "u": S["veer"][0]["actors"]["u"],
                                   "d": D((0, 4.6, 4.9), (1.5, 4.6, 4.9), (2.4, 4.2, 4.2), (3.2, 4.6, 2.2))},
                        "ball": {"held": [(0, 8, "h")]}}, 4.6, {}),
}
ALL_SCEN.update(L5)


def test_l5_01_no_half_court_labels_beyond_half_court():
    for name, det, roles in (("l5_bc_icut", "cut_i", {"cutter": "c"}), ("l5_bc_veer", "cut_veer", {"cutter": "u"}),
                             ("l5_bc_banana", "cut_banana", {"cutter": "c"})):
        assert _rate(name, det, roles, sigmas=(0.2, 0.3, 0.5)) == 0.0, name
    # transition carry: the label starts < transition_carry_s after a sustained run crossed half court (loop 6,
    # L6-01: l5_carry_veer stops on the wing before it veers, which is a half-court action under the carry rule)
    assert _rate("l6_jog_push_run", "cut_basket", {"cutter": "a"}, sigmas=(0.2, 0.3)) == 0.0
    # the same moves in the frontcourt keep their recall
    assert _rate("icut", "cut_i", {"cutter": "c"}, sigmas=(0.2,), t0fn=lambda T: 2.65) >= 0.9
    assert _rate("veer", "cut_veer", {"cutter": "u"}, sigmas=(0.2, 0.3), t0fn=lambda T: 2.35) >= 0.9
    # transition labels are exempt (they start in the backcourt by definition)
    assert _rate("rim_run", "rim_run", {"runner": "p"}, sigmas=(0.3,)) >= 0.9
    assert "rim_run" in cuts.PARAMS["cu_postrules"]["exempt_kinds"]


def test_l5_02_i_cut_needs_a_significant_step_toward_the_rim():
    # lateral out-and-back along the arc: loop 4 fired 11/30 (5, 4, 2 of 10 at sigma 0.2 / 0.3 / 0.5)
    assert _rate("l5_lateral_i", "cut_i", {"cutter": "c"}, sigmas=(0.2, 0.3, 0.5)) <= 0.05
    # the rimward I keeps its recall at every sigma (the family sweep floors are 0.8 / 0.8 / 0.5)
    assert _rate("icut", "cut_i", {"cutter": "c"}, sigmas=(0.2, 0.3), t0fn=lambda T: 2.65) >= 0.85
    assert _rate("icut", "cut_i", {"cutter": "c"}, sigmas=(0.5,), t0fn=lambda T: 2.65) >= 0.5


def test_l5_03_high_noise_veer_needs_a_significant_approach():
    k = cuts.PARAMS["cut_veer"]["approach_k_high_noise"]
    n = 0
    for name in ("l5_veer_jog", "l5_veer_jog2", "l5_veer_shadow", "veer", "veer_slot"):
        spec, dur, attrs = ALL_SCEN[name]
        for seed in range(10):
            _, sc = build(spec, dur, seed, sigma=0.5, **attrs)
            c = cuts._ctx(sc)
            assert c.high_noise("u")
            for e in _matching(cuts.detect_cut_veer(sc), "cut_veer", {"cutter": "u"}):
                # closing on the defender over approach_s before the closest approach, recomputed from the tracks
                tn = e.attrs["t_closest"]
                ln = max(0, tn - cuts.F(cuts.PARAMS["cut_veer"]["approach_s"]))
                dd = c.dist("u", e.actors["defender"])
                sa = math.sqrt(2) * c.f["u"].sig_p[tn]
                assert dd[ln] - dd[tn] >= cuts.PARAMS["cut_veer"]["approach_m"] + k * sa - 1e-9, (name, seed)
                n += 1
    assert n >= 8  # the true veers still fire (recall floors in test_f08r)
    # jogs past the defender fire less (loop 4: 13 of 30 runs at sigma 0.5; loop 5: 9)
    hits = sum(_rate(nm, "cut_veer", {"cutter": "u"}, sigmas=(0.5,)) for nm in ("l5_veer_jog", "l5_veer_jog2", "l5_veer_shadow"))
    assert round(hits * 10) <= 10


def test_l5_04_one_event_per_kind_actor_and_moment():
    w = cuts.F(cuts.PARAMS["cu_postrules"]["dedup_t0_s"])
    for name in ("l5_lift_bs", "l5_pop_low", "shake", "straight", "veer"):
        spec, dur, attrs = ALL_SCEN[name]
        for sg in (0.2, 0.3, 0.5):
            for seed in range(10):
                _, sc = build(spec, dur, seed, sigma=sg, **attrs)
                evs = cuts.detect_all(sc, resolve_labels=False)
                for i, e in enumerate(evs):
                    for e2 in evs[i + 1:]:
                        assert not (e.kind == e2.kind and e.actors == e2.actors and abs(e.t0 - e2.t0) <= w), \
                            (name, sg, seed, e.kind, e.t0, e2.t0)


def test_l5_04b_tracking_teleport_is_not_a_cut():
    """A corner player whose track jumps to the other corner in 2 frames (a SportVU id swap) is not a cut."""
    spec, dur, attrs = S["still"]
    for seed in range(5):
        _, tracks = scenario(spec, dur, 0.15, seed)
        for tr in tracks:
            if tr.oid == "k":
                i = int(2.0 / DT)
                tr.x[i:i + 2] = [3.0, -3.0]
                tr.x[i + 2:] = -tr.x[i + 2:]
        sc = mvlib.build_scene(tracks)
        evs = [e for e in cuts.detect_all(sc, resolve_labels=False) if cuts._primary_actor(e) == "k" and e.kind != "move"]
        assert not evs, (seed, [(e.kind, e.t0) for e in evs])


def test_yaml_changes_loop5_recorded():
    ch = cuts.DOC.get("changes_loop5")
    assert ch and all({"id", "what", "why", "evidence"} <= set(c) for c in ch)
    ids = {c["id"].split()[0] for c in ch}
    assert {"L5-01", "L5-02", "L5-03", "L5-04", "L5-05", "L5-06"} <= ids
    assert cuts.DOC["version"] >= "0.5.0"
    assert "in_dr_k" in cuts.PARAMS["cut_i"] and "approach_k_high_noise" in cuts.PARAMS["cut_veer"]
    assert {"exempt_kinds", "dedup_t0_s", "glitch_max_mps"} <= set(cuts.PARAMS["cu_postrules"])
