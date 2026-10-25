"""Synthetic scenes for the identity rule tests (absolute court frame, metres, 25 Hz).

A scene is a roster (two teams of seven: five on court, two on the bench by default) and per-player
waypoint paths [(t_s, x_m, y_m), ...] with minimum-jerk motion between waypoints. Players without a
path stand still at a default spot. Off-court intervals are given per player as (t0, t1).
"""
from __future__ import annotations

import numpy as np

from obsmodel import COURT_L, COURT_W, Truth

DT = 0.04
JERSEYS = [["0", "1", "3", "11", "23", "35", "5"], ["2", "4", "10", "12", "21", "33", "44"]]
POSITIONS = ["G", "G", "F", "F", "C", "G", "F"]


def min_jerk(p0, p1, n):
    s = np.linspace(0.0, 1.0, n)
    b = 10 * s**3 - 15 * s**4 + 6 * s**5
    return p0 + (p1 - p0) * b


def default_spot(p):
    team, k = divmod(p, 7)
    x = 6.0 + 3.5 * (k % 5) + (0.0 if team == 0 else 1.7)
    y = 3.0 + (k % 5) * 2.2 + (0.0 if team == 0 else 1.1)
    return x, y


def make_truth(duration_s, paths=None, off=None, jerseys=None, ball=None, gaps=()):
    """-> Truth. players 0-6 team 0 (5 and 6 on the bench), 7-13 team 1 (12 and 13 on the bench)."""
    paths = paths or {}
    F = int(round(duration_s / DT)) + 1
    N = 14
    pos = np.full((F, N, 2), np.nan)
    t = np.arange(F) * DT
    bench = {5, 6, 12, 13}
    off = dict(off or {})
    for p in bench:
        off.setdefault(p, [(0.0, duration_s + 1)])
    for p in range(N):
        if p in paths:
            wp = sorted(paths[p])
            x = np.full(F, float(wp[0][1]))
            y = np.full(F, float(wp[0][2]))
            for (ta, xa, ya), (tb, xb, yb) in zip(wp, wp[1:]):
                ia, ib = int(round(ta / DT)), min(F - 1, int(round(tb / DT)))
                if ib > ia:
                    x[ia:ib + 1] = min_jerk(xa, xb, ib - ia + 1)
                    y[ia:ib + 1] = min_jerk(ya, yb, ib - ia + 1)
            il = int(round(wp[-1][0] / DT))
            if il < F:
                x[il:], y[il:] = wp[-1][1], wp[-1][2]
        else:
            sx, sy = default_spot(p)
            x = np.full(F, sx) + 0.3 * np.sin(0.7 * t + p)
            y = np.full(F, sy) + 0.3 * np.cos(0.5 * t + p)
        pos[:, p, 0], pos[:, p, 1] = x, y
        for t0, t1 in off.get(p, []):
            pos[int(round(t0 / DT)):int(round(t1 / DT)), p] = np.nan
    team = np.array([0] * 7 + [1] * 7)
    js = jerseys or (JERSEYS[0] + JERSEYS[1])
    b = np.tile([COURT_L / 2, COURT_W / 2], (F, 1)) if ball is None else ball
    gap = np.zeros(F, dtype=bool)
    gap[0] = True
    for g in gaps:
        gap[int(round(g / DT))] = True
    return Truth(DT, pos, team, list(js), POSITIONS + POSITIONS, b, gap)


QUIET = {"refs": False, "fov": False, "live_cuts": False, "occlusion": True, "misses": False, "random_jersey": False,
         "pbp_lag": False}


def quiet_profile(**kw):
    """A cue profile with no random errors (tests switch individual cues on)."""
    p = {"e_team": 0.0, "jersey_sightings_per_s": 0.0, "jersey_sighting_len_s": [0.2, 0.2], "e_ocr": 0.0, "p_partial": 0.0,
         "app_dims": 16, "app_w_ind": 0.35, "app_w_game": 0.0, "app_noise": 0.12, "app_rho": 0.9, "game_card": True,
         "template_crops": 200, "sigma_h": 0.05, "outlier_h": 0.0, "gait_noise": 0.6, "twin_pairs_per_team": 0}
    p.update(kw)
    return p
