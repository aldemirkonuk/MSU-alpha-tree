"""Synthetic scenario generator for movement-grammar tests (validation tier V0).

A scenario is a dict of actors, each a list of waypoints (t_s, x_m, y_m) in the attacked-rim
frame; motion between waypoints is minimum-jerk (smooth start and stop), holds are repeated
waypoints. The ball has 'held_by' intervals and 'flights' (straight-line passes). Noise
follows the measurement research: white + AR(1) (rho 0.9 per frame) mix, sigma_p per game,
optional outlier bursts and missing runs. Truth events are supplied by the scenario author.
"""
from __future__ import annotations

import numpy as np

from mvlib import DT, Track


def min_jerk(p0, p1, n):
    s = np.linspace(0.0, 1.0, n)
    b = 10 * s**3 - 15 * s**4 + 6 * s**5
    return p0 + (p1 - p0) * b


def path(waypoints, n_frames):
    """Waypoints [(t, x, y), ...] sorted by t -> arrays x, y over n_frames (held at the ends)."""
    t = np.arange(n_frames) * DT
    x = np.full(n_frames, float(waypoints[0][1]))
    y = np.full(n_frames, float(waypoints[0][2]))
    for (ta, xa, ya), (tb, xb, yb) in zip(waypoints, waypoints[1:]):
        ia, ib = int(round(ta / DT)), int(round(tb / DT))
        ib = min(ib, n_frames - 1)
        if ib <= ia:
            continue
        x[ia:ib + 1] = min_jerk(xa, xb, ib - ia + 1)
        y[ia:ib + 1] = min_jerk(ya, yb, ib - ia + 1)
    last = waypoints[-1]
    il = int(round(last[0] / DT))
    if il < n_frames:
        x[il:] = last[1]
        y[il:] = last[2]
    return x, y


def noise(n, sigma_p, rng, white_share=0.5, rho=0.9):
    w = rng.normal(0, 1, n)
    ar = np.zeros(n)
    e = rng.normal(0, 1, n) * np.sqrt(1 - rho**2)
    for k in range(1, n):
        ar[k] = rho * ar[k - 1] + e[k]
    return sigma_p * (np.sqrt(white_share) * w + np.sqrt(1 - white_share) * ar)


def observe(x, y, sigma_p=0.3, rng=None, missing_runs=0, outlier_rate=0.0, oid="p", team="", role="player"):
    """Noisy observations of a true path -> Track."""
    rng = rng or np.random.default_rng(0)
    n = len(x)
    ox = x + noise(n, sigma_p, rng)
    oy = y + noise(n, sigma_p, rng)
    for _ in range(missing_runs):
        a = int(rng.integers(0, max(1, n - 40)))
        L = int(rng.integers(3, 30))
        ox[a:a + L] = np.nan
        oy[a:a + L] = np.nan
    if outlier_rate > 0:
        k = rng.random(n) < outlier_rate
        ox[k] += rng.normal(0, 2.0, k.sum())
        oy[k] += rng.normal(0, 2.0, k.sum())
    return Track(oid, ox, oy, np.full(n, float(sigma_p)), team=team, role=role)


def scenario(spec, duration_s, sigma_p=0.3, seed=0, **obs_kw):
    """spec = {'actors': {id: {'team': 'O'|'D', 'wp': [(t,x,y),...]}},
               'ball': {'held': [(t0, t1, actor_id)], 'flights': [(t0, t1, from_id, to_id)]}}
    Returns (truth dict of arrays, list of observed Tracks)."""
    rng = np.random.default_rng(seed)
    n = int(round(duration_s / DT)) + 1
    truth, tracks = {}, []
    for aid, a in spec["actors"].items():
        x, y = path(a["wp"], n)
        truth[aid] = (x, y)
        tracks.append(observe(x, y, sigma_p, rng, oid=aid, team=a.get("team", ""), **obs_kw))
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
        tr = observe(np.nan_to_num(bx, nan=0.0), np.nan_to_num(by, nan=0.0), sigma_p * 0.7, rng, oid="ball", role="ball")
        tr.x[np.isnan(bx)] = np.nan
        tr.y[np.isnan(by)] = np.nan
        tracks.append(tr)
    return truth, tracks
