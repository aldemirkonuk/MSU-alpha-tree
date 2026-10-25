"""Screens family detectors (spec tooling, not the production labeller).

Implements config/movement_grammar/screens.yaml: one canonical screen engine (SET -> screen
moment -> USE/REJECT -> interaction, with STRICT and LOOSE flags per R-ST-17), ball screens,
off-ball screens, handoffs, defender response (coverage) and legality hints. Every numeric
parameter is read from the YAML at import (single source of truth); detectors accept keyword
overrides for their own item's params.

All kinematics come from mvlib (CA-RTS smoothing, validity gates). Positions are in the
attacked-rim frame (metres, rim at the origin); time base 29.97 fps (mvlib.DT). Every detector
returns mvlib.Event objects whose conf follows MP-16:
    conf = window_conf(p, start, end) x min edge_factor(actor, t0) x min gap_factor(actor, start, end)
Location labels come only from config/named_spots.yaml through spotlib (never redefined here).
"""
from __future__ import annotations

import math
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

_HERE = Path(__file__).resolve()
_MOVEMENT = _HERE.parents[1]
_REPO = _HERE.parents[4]
for _p in (_MOVEMENT, _REPO / "tools" / "specgen" / "named_spots"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mvlib  # noqa: E402
import spotlib  # noqa: E402
from mvlib import (DT, K_CAL, Event, edge_factor, frames, gap_factor, hysteresis, p_above,  # noqa: E402
                   p_below, sigma_dist, window_conf)

# --------------------------------------------------------------------------------------
# Parameters (single source of truth: config/movement_grammar/screens.yaml)
# --------------------------------------------------------------------------------------
CONFIG = _REPO / "config" / "movement_grammar" / "screens.yaml"
DOC = yaml.safe_load(CONFIG.read_text())
ITEMS = {it["id"]: it for it in DOC["items"]}
PARAMS = {iid: {k: v["value"] for k, v in (it.get("params") or {}).items()} for iid, it in ITEMS.items()}


def prm(item: str, over: dict | None = None) -> dict:
    """Parameters of one item, with optional overrides (unknown names are an error)."""
    d = dict(PARAMS[item])
    for k, v in (over or {}).items():
        if k not in d:
            raise KeyError(f"{item} has no parameter {k!r}")
        d[k] = v
    return d


# D3 (25 Oct): the screens-table enum screener_action_after (base values + the bigs sub-labels) and each sub-label's
# base parent. This family's own post_action values are base values; bigs.screener_post_action fills the sub-labels.
SCREENER_ACTION_AFTER = tuple(prm("screen_record_schema")["screener_action_after"])
SCREENER_ACTION_SUB_LABELS = dict(prm("screen_record_schema")["screener_action_sub_labels"])

_SPOT_DOC, SPOTS = spotlib.load()
PNR_LOCATION_IDS = sorted((s for s in SPOTS.values() if s.d["layer"] == "zone_scheme:pnr_location"),
                          key=lambda s: s.d.get("rank", 0))
PNR_BIG_ORDER = ["pnr_big_blitz", "pnr_big_hedge", "pnr_big_at_level", "pnr_big_high_drop", "pnr_big_deep_drop"]
SIDE_X, END_Y = 7.62, -1.6002  # named_spots constants (boundary lines are out of bounds)


# --------------------------------------------------------------------------------------
# Small helpers: spots, geometry, probabilities
# --------------------------------------------------------------------------------------
def _fin(*v) -> bool:
    return all(v_ is not None and np.isfinite(v_) for v_ in v)


def _labels(spot_id: str, x, y, **ctx) -> list:
    """Side-qualified labels of one named spot at (x, y); [] when the position is unknown."""
    if not _fin(x, y):
        return []
    return SPOTS[spot_id].labels(float(x), float(y), **ctx)


def _in(spot_id: str, x, y, **ctx) -> bool:
    return bool(_labels(spot_id, x, y, **ctx))


def _pnr_location(x, y):
    """First label of the named_spots pnr_location partition (rank order), or None."""
    for s in PNR_LOCATION_IDS:
        lab = _labels(s.id, x, y)
        if lab:
            return lab[0]
    return None


def _region(x, y):
    r = spotlib.court_region(SPOTS, float(x), float(y)) if _fin(x, y) else ["unknown"]
    return r[0] if r else "unknown"


def _unit(v):
    v = np.asarray(v, dtype=float)
    n = float(np.hypot(v[0], v[1]))
    return v / n if n > 1e-9 and np.isfinite(n) else np.array([np.nan, np.nan])


def _ang(a, b) -> float:
    """Unsigned angle between two vectors in degrees (nan if either is zero/undefined)."""
    a, b = _unit(a), _unit(b)
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        return float("nan")
    return float(np.degrees(np.arccos(np.clip(a @ b, -1.0, 1.0))))


def _m_deg(x, y) -> float:
    """named_spots folded angle m = degrees(atan2(y, |x|))."""
    return float(math.degrees(math.atan2(y, abs(x)))) if (x or y) else 90.0


def _seg_proj(p, a, b):
    """(distance from p to segment ab, projection parameter of p on ab)."""
    ab = b - a
    L = float(ab @ ab)
    if L < 1e-12:
        return float(np.hypot(*(p - a))), 0.0
    u = float((p - a) @ ab) / L
    q = a + min(max(u, 0.0), 1.0) * ab
    return float(np.hypot(*(p - q))), u


def _i0e(z):
    """Exponentially scaled modified Bessel I0 (overflow-safe)."""
    z = np.asarray(z, dtype=float)
    zc = np.minimum(z, 600.0)
    small = np.i0(zc) * np.exp(-zc)
    big = 1.0 / np.sqrt(2 * np.pi * np.maximum(z, 1e-9)) * (1 + 1 / (8 * np.maximum(z, 1e-9)))
    return np.where(z < 600.0, small, big)


_trapz = getattr(np, "trapezoid", None) or np.trapz  # numpy < 2.0 has only trapz (SCR-T21)


def rice_below(vhat: float, thr: float, sig: float, n: int = 400) -> float:
    """P(true |v| < thr) for a 2-D velocity estimate of magnitude vhat with per-axis sigma sig.

    Posterior under a flat prior: true v ~ N(v_hat, sig^2 I), so |v| is Rice(vhat, sig).
    Replaces Phi((thr - |v|)/sig), which treats a Rayleigh-like magnitude as Gaussian (check SCR-R01-b).
    """
    if not _fin(vhat, thr, sig) or sig <= 0:
        return float("nan")
    r = np.linspace(0.0, thr, n)
    f = (r / sig**2) * np.exp(-((r - vhat) ** 2) / (2 * sig**2)) * _i0e(r * vhat / sig**2)
    return float(np.clip(_trapz(f, r), 0.0, 1.0))


def _pb(value, thr, sigma) -> float:
    """Scalar p_below with nan -> 0."""
    v = float(p_below(value, thr, sigma)) if _fin(value, thr, sigma) else 0.0
    return v if np.isfinite(v) else 0.0


def _pa(value, thr, sigma) -> float:
    v = float(p_above(value, thr, sigma)) if _fin(value, thr, sigma) else 0.0
    return v if np.isfinite(v) else 0.0


# --------------------------------------------------------------------------------------
# Scene access with a per-scene cache
# --------------------------------------------------------------------------------------
def _cache(scene) -> dict:
    return scene.__dict__.setdefault("_screens_cache", {})


def _cl(scene, t) -> int:
    return int(min(max(int(t), 0), scene.n - 1))


def _win(scene, t, s0: float, s1: float):
    """Clipped inclusive frame window [t + s0, t + s1] (seconds)."""
    return _cl(scene, t + frames(s0)), _cl(scene, t + frames(s1))


def _kv(scene, oid) -> dict:
    """Cached derived arrays of one player (speed, s2, v_r, r)."""
    c = _cache(scene).setdefault("kv", {})
    if oid not in c:
        k = scene.k(oid)
        # stand statistic with the velocity variance floored at the production-tier value (loop 4, SCR-L4-01): on
        # vendor-smoothed tracks var_v is tiny and s2 < 5.99 meant |v| < 0.40-0.70 m/s, so brief NBA screen plants
        # (smoothed minimum 0.6-0.8 m/s) never formed a stop, while the same plants pass at sigma_p >= 0.2
        fl = prm("screen_stationarity")["s2_var_v_floor_sigma_mps"]
        s2 = (k.vx**2 + k.vy**2) / ((K_CAL**2) * np.maximum(k.var_v, fl**2))
        c[oid] = dict(speed=k.speed, s2=s2, vr=k.v_r, r=k.r)
    return c[oid]


def _pos(scene, oid, t):
    if oid == "ball":
        k = scene.ball
        return np.array([k.x[t], k.y[t]]) if k is not None else np.array([np.nan, np.nan])
    k = scene.k(oid)
    return np.array([k.x[t], k.y[t]])


def _r_at(scene, oid, t) -> float:
    return float(np.hypot(*_pos(scene, oid, t)))


def _dist(scene, a, b) -> np.ndarray:
    c = _cache(scene).setdefault("dist", {})
    key = (a, b) if a < b else (b, a)
    if key not in c:
        c[key] = mvlib.dist(scene.k(a), scene.k(b))
    return c[key]


def _sigd(scene, a, b, t) -> float:
    c = _cache(scene).setdefault("sigd", {})
    key = (a, b) if a < b else (b, a)
    if key not in c:
        c[key] = sigma_dist(scene.k(a), scene.k(b))
    v = c[key][t] * prm("screen_noise_calibration")["dist_sigma_scale"]
    return float(v) if np.isfinite(v) else 0.5


def _med5(scene, a, b) -> np.ndarray:
    """Cached 5-frame running median of d(a, b) (NaN where the whole window is missing)."""
    c = _cache(scene).setdefault("med5", {})
    key = (a, b) if a < b else (b, a)
    if key not in c:
        d = _dist(scene, a, b)
        win = np.lib.stride_tricks.sliding_window_view(np.pad(d, 2, mode="constant", constant_values=np.nan), 5)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            c[key] = np.nanmedian(win, axis=1)
    return c[key]


def _med(arr, t, half=2) -> float:
    seg = arr[max(0, t - half): t + half + 1]
    seg = seg[np.isfinite(seg)]
    return float(np.median(seg)) if len(seg) else float("nan")


def _mean_v(scene, oid, a, b):
    k = scene.k(oid)
    if b < a:
        return np.array([np.nan, np.nan])
    return np.array([np.nanmean(k.vx[a:b + 1]), np.nanmean(k.vy[a:b + 1])])


def _sig_pos(scene, oid, t) -> float:
    v = scene.k(oid).var_p[t]
    return float(K_CAL * np.sqrt(v)) if np.isfinite(v) else 0.5


def _min_r(scene, oid, a, b) -> float:
    r = _kv(scene, oid)["r"][a:b + 1]
    return float(np.nanmin(r)) if np.any(np.isfinite(r)) else float("nan")


def _conf(scene, actors, t0, a, b, p) -> float:
    """MP-16 confidence: window_conf(p) x min edge_factor(t0) x min gap_factor([a, b])."""
    parr = np.full(scene.n, np.nan)
    parr[a:b + 1] = p
    wc = window_conf(parr, a, b)
    ks = [scene.k(o) for o in actors if o in scene.kins]
    ef = min(edge_factor(k, t0) for k in ks) if ks else 1.0
    gf = min(gap_factor(k, a, b) for k in ks) if ks else 1.0
    return float(wc * ef * gf)


def _event(scene, kind, actors: dict, t0, a, b, p, attrs) -> Event | None:
    """Build an Event with MP-16 confidence; None when below emit_min_conf."""
    a, b, t0 = _cl(scene, min(a, t0)), _cl(scene, max(b, t0)), _cl(scene, t0)
    ids = [v for v in actors.values() if isinstance(v, str)]
    conf = _conf(scene, ids, t0, a, b, float(np.clip(p, 0.0, 1.0)) if _fin(p) else 0.0)
    if conf < prm("screen_confidence")["emit_min_conf"]:
        return None
    return Event(kind, dict(actors), int(t0), int(a), int(b), conf, dict(attrs))


# --------------------------------------------------------------------------------------
# Matchup proxy and possession (screen_target_defender, dho_pitch_disambiguation)
# --------------------------------------------------------------------------------------
def _matchup(scene, t, window_s=None) -> dict:
    """{defender: {attacker: P(d guards o)}} from mean distances over [t - window, t].

    The default window (matchup_window_s) stands in for the persistence of the matchup HMM, so a
    defender caught on a screener for half a second is not reassigned to him.
    """
    P = prm("screen_target_defender")
    w = P["matchup_window_s"] if window_s is None else window_s
    t = _cl(scene, t)
    c = _cache(scene).setdefault("mu", {})
    if (t, w) in c:
        return c[(t, w)]
    a = _cl(scene, t - frames(w))
    out = {}
    for d in scene.defense:
        cost = np.array([np.nanmean(_dist(scene, d, o)[a:t + 1]) for o in scene.offense])
        cost = np.where(np.isfinite(cost), cost, 50.0)
        lw = -cost**2 / (2 * P["matchup_tau_m"] ** 2)
        wt = np.exp(lw - lw.max())
        out[d] = dict(zip(scene.offense, wt / wt.sum()))
    c[(t, w)] = out
    return out


def _matchup_excl(scene, t, s, excl) -> dict:
    """_matchup at t, with the frames where the screener s stood screening defender d (excl: [(a, b, d)] of earlier
    SET rows of s) removed from the cost of the pair (d, s): contact with a standing screener is not guarding him
    (SCR-T04; without this a second screen within ~3 s reads the first screen's contact as an own-man matchup)."""
    base = _matchup(scene, t)
    if not excl:
        return base
    P = prm("screen_target_defender")
    t = _cl(scene, t)
    a = _cl(scene, t - frames(P["matchup_window_s"]))
    rad = prm("screen_set")["set_def_radius_m"]
    out = dict(base)
    for d in {x[2] for x in excl}:
        dds = _dist(scene, d, s)[a:t + 1]
        keep = np.ones(t - a + 1, dtype=bool)
        for ea, eb, dd in excl:
            if dd == d and eb >= a and ea <= t:
                sl = slice(max(ea, a) - a, min(eb, t) - a + 1)
                keep[sl] &= ~(dds[sl] <= rad)
        if keep.all():
            continue
        cost = []
        for o in scene.offense:
            v = dds[keep] if o == s else _dist(scene, d, o)[a:t + 1]
            cost.append(np.nanmean(v) if np.any(np.isfinite(v)) else np.nan)
        cost = np.where(np.isfinite(cost), cost, 50.0)
        lw = -cost**2 / (2 * P["matchup_tau_m"] ** 2)
        wt = np.exp(lw - lw.max())
        out[d] = dict(zip(scene.offense, wt / wt.sum()))
    return out


def _guard_of(scene, d, t, window_s=None):
    probs = _matchup(scene, t, window_s)[d]
    o = max(probs, key=probs.get)
    return o, float(probs[o])


def _defender_of(scene, o, t):
    """Defender with the highest P(d guards o) at t, and that probability."""
    mu = _matchup(scene, t)
    if not mu:
        return None, 0.0
    d = max(mu, key=lambda dd: mu[dd].get(o, 0.0))
    return d, float(mu[d].get(o, 0.0))


def _holder(scene) -> np.ndarray:
    """Holder per frame: mvlib nearest-player holder with a sticky switch and short runs removed.

    A change from holder a to teammate b is accepted only when b is nearer the ball than a by
    max(holder_switch_margin_m, holder_margin_k x K_CAL x sqrt(var_p_a + var_p_b)) (a screener brushing past the
    ball handler does not take the ball);
    runs shorter than holder_min_run_frames are then removed (the 3-frame hysteresis analogue).
    """
    c = _cache(scene)
    if "holder" in c:
        return c["holder"]
    P = prm("dho")
    raw = np.array(scene.holder, dtype=object)
    h = raw.copy()
    cur = None
    for t in range(len(raw)):
        cand = raw[t]
        if cand is None or cur is None or cand == cur or not np.isfinite(scene.ball.x[t]):
            cur = cand
        else:
            bp = _pos(scene, "ball", t)
            d_new = float(np.hypot(*(_pos(scene, cand, t) - bp)))
            d_cur = float(np.hypot(*(_pos(scene, cur, t) - bp)))
            # the margin grows with the pair's position noise (SCR-T13: at sigma_p 0.5 a fixed 0.15 m let the holder
            # flip between the handler and a passing screener)
            vv = scene.k(cand).var_p[t] + scene.k(cur).var_p[t]
            margin = max(P["holder_switch_margin_m"],
                         P["holder_margin_k"] * K_CAL * math.sqrt(vv) if np.isfinite(vv) else 0.0)
            if d_new + margin < d_cur or not d_cur <= mvlib.HOLD_R:
                cur = cand
        h[t] = cur
    mn = int(P["holder_min_run_frames"])
    i = 0
    while i < len(h):
        j = i
        while j + 1 < len(h) and h[j + 1] == h[i]:
            j += 1
        if h[i] is not None and j - i + 1 < mn:
            h[i:j + 1] = None
        i = j + 1
    c["holder"] = h
    return h


def _segments(scene) -> list:
    """Possession segments (oid, start, end) from the cleaned holder."""
    c = _cache(scene)
    if "segs" in c:
        return c["segs"]
    h = _holder(scene)
    out, i = [], 0
    while i < len(h):
        j = i
        while j + 1 < len(h) and h[j + 1] == h[i]:
            j += 1
        if h[i] is not None:
            out.append((h[i], i, j))
        i = j + 1
    c["segs"] = out
    return out


def _ball_raw(scene, t):
    """Raw ball observation at t (holder logic uses raw ball positions, MP-15); smoothed ball if none."""
    if getattr(scene, "ball_raw", None) is not None:
        return np.array([scene.ball_raw[0][t], scene.ball_raw[1][t]], dtype=float)
    return _pos(scene, "ball", t)


def _flight(scene, a, b, a0, a1, b0, b1, Pp):
    """(release, catch) frames from the raw ball track (SCR-T15): release = last frame of a's segment whose 5-frame
    median ball distance to a is <= hand_r_m, catch = first later frame within hand_r_m of b. HOLD_R (1.0 m) absorbs
    about 2 m of flight, so the holder-segment gap under-measures air time and travel. Falls back to (a1, b0)."""
    if getattr(scene, "ball_raw", None) is None:
        return a1, b0
    bx, by = (np.asarray(v, dtype=float) for v in scene.ball_raw)
    ka, kb = scene.k(a), scene.k(b)
    da = np.hypot(bx - ka.x, by - ka.y)
    db = np.hypot(bx - kb.x, by - kb.y)
    rel = next((t for t in range(a1, a0 - 1, -1) if _med(da, t) <= Pp["hand_r_m"]), None)
    if rel is None:
        return a1, b0
    cat = next((t for t in range(rel + 1, b1 + 1) if _med(db, t) <= Pp["hand_r_m"]), None)
    if cat is None:
        return a1, b0
    return rel, max(cat, rel + 1)


def _transfers(scene) -> list:
    """Possession changes a -> b with air time, travel, exchange distance and type (dho | pitch | pass)."""
    c = _cache(scene)
    if "xfer" in c:
        return c["xfer"]
    P, Pp = prm("dho"), prm("dho_pitch_disambiguation")
    segs = _segments(scene)
    out = []
    for (a, a0, a1), (b, b0, b1) in zip(segs, segs[1:]):
        if a == b:
            continue
        rel, cat = _flight(scene, a, b, a0, a1, b0, b1, Pp)
        air = max(0, cat - rel - 1) * DT
        bp0, bp1 = _ball_raw(scene, rel), _ball_raw(scene, cat)
        travel = float(np.hypot(*(bp1 - bp0))) if np.all(np.isfinite(bp0 + bp1)) else float("nan")
        # the exchange is anchored on the raw-ball catch frame (the holder segment of b can start late at high noise)
        tx = min(cat, b0)
        sp = max(_med(_kv(scene, a)["speed"], tx), _med(_kv(scene, b)["speed"], tx))
        # exchange distance: closest 3-frame median within +-exch_win_s of the catch (hands meet at the closest point)
        ew = frames(P["exch_win_s"])
        dd_ab = _dist(scene, a, b)
        d_ab = min(_med(dd_ab, t, 1) for t in range(max(0, tx - ew), min(scene.n, tx + ew + 1)))
        held = (a1 - a0 + 1) * DT >= P["hander_hold_s"] - 1e-9 and (b1 - tx + 1) * DT >= P["receiver_hold_s"] - 1e-9
        is_dho = (d_ab <= P["dist_max_m"] and air <= P["air_max_s"] + 1e-9 and held  # held: SCR-T13
                  and (not np.isfinite(travel) or travel <= P["travel_max_m"]) and sp > P["min_speed_mps"])
        if is_dho:
            typ = "dho"
        elif air <= Pp["pitch_max_air_s"] and np.isfinite(travel) and travel <= Pp["pitch_max_travel_m"]:
            typ = "pitch"
        else:
            typ = "pass"
        out.append(dict(frm=a, to=b, release=rel, catch=tx, ball_catch=cat, air_s=air, travel_m=travel, d_ab=d_ab,
                        speed=sp, type=typ, seg_from=(a0, a1), seg_to=(b0, b1)))
    c["xfer"] = out
    return out


def _holds(scene, oid, a, b) -> int:
    h = _holder(scene)[_cl(scene, a):_cl(scene, b) + 1]
    return int(sum(1 for v in h if v == oid))


def _ball_sigma(scene) -> float:
    """Robust 2-D sigma of the raw ball around the smoothed ball (MAD of the residual, both axes): the observed ball
    noise of this clip (about 0.05 m on SportVU, sigma_p x 0.7 x sqrt 2 on V0 tracks)."""
    c = _cache(scene)
    if "ball_sigma" not in c:
        v = 0.0
        if getattr(scene, "ball_raw", None) is not None and scene.ball is not None:
            rx = np.asarray(scene.ball_raw[0], dtype=float) - scene.ball.x
            ry = np.asarray(scene.ball_raw[1], dtype=float) - scene.ball.y
            ok = np.isfinite(rx) & np.isfinite(ry)
            if ok.sum() >= 10:
                v = float(math.hypot(1.4826 * np.median(np.abs(rx[ok] - np.median(rx[ok]))),
                                     1.4826 * np.median(np.abs(ry[ok] - np.median(ry[ok])))))
        c["ball_sigma"] = v
    return c["ball_sigma"]


def _poss(scene) -> np.ndarray:
    """Ball possession per frame for the on-ball tests (mastery r1, SCR-M1-01; ball_screen_model).

    The cleaned holder (_holder) collapses under position noise: noise on the ball and the player pushes the
    ball-handler distance over HOLD_R, and its 12-frame minimum runs then delete the dribble (real tracks with
    sigma_p 0.3 / 0.5 added: cleaned holder coverage 0.55 -> 0.42 -> 0.15, and 32 / 49 of 54 clean ball screens
    became off-ball rows). Here: the 5-frame median distance of the raw ball to each attacker, a radius widened by
    the clip's measured ball noise (HOLD_R + poss_k x ball sigma), a sticky owner (a teammate takes over only when
    nearer by poss_switch_margin_m), None gaps up to poss_bridge_s between two runs of the same attacker filled (a
    dribble), and runs shorter than poss_min_run_frames removed. Used for the on-ball kind, the ball defender and
    the contact candidates; DHO / pass logic keeps _holder."""
    c = _cache(scene)
    if "poss" in c:
        return c["poss"]
    if getattr(scene, "ball_raw", None) is None or not scene.offense:
        c["poss"] = _holder(scene)
        return c["poss"]
    P = prm("ball_screen_model")
    n = scene.n
    bx, by = (np.asarray(v, dtype=float) for v in scene.ball_raw)
    half = int(P["poss_med_frames"]) // 2
    D = {}
    for o in scene.offense:
        k = scene.k(o)
        d = np.hypot(bx - k.x, by - k.y)
        win = np.lib.stride_tricks.sliding_window_view(np.pad(d, half, mode="edge"), 2 * half + 1)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)  # all-NaN windows (ball in flight / missing) stay NaN
            D[o] = np.nanmedian(win, axis=1)
    R = mvlib.HOLD_R + P["poss_k"] * _ball_sigma(scene)
    h = np.array([None] * n, dtype=object)
    cur = None
    for t in range(n):
        best, bd = None, R
        for o in scene.offense:
            v = D[o][t]
            if np.isfinite(v) and v <= bd:
                best, bd = o, v
        if best is not None and cur is not None and best != cur:
            dc = D[cur][t]
            if np.isfinite(dc) and dc <= R and bd + P["poss_switch_margin_m"] >= dc:
                best = cur
        h[t] = best
        cur = best if best is not None else cur
    # fill short None gaps between runs of the same attacker (a dribble or a noisy hand)
    gap = frames(P["poss_bridge_s"])
    last_o, last_t = None, -10**9
    for t in range(n):
        if h[t] is None:
            continue
        if h[t] == last_o and 1 < t - last_t <= gap + 1:
            h[last_t + 1:t] = last_o
        last_o, last_t = h[t], t
    mn = int(P["poss_min_run_frames"])
    i = 0
    while i < n:
        j = i
        while j + 1 < n and h[j + 1] == h[i]:
            j += 1
        if h[i] is not None and j - i + 1 < mn:
            h[i:j + 1] = None
        i = j + 1
    c["poss"] = h
    return h


def _poss_holds(scene, oid, a, b) -> int:
    h = _poss(scene)[_cl(scene, a):_cl(scene, b) + 1]
    return int(sum(1 for v in h if v == oid))


# --------------------------------------------------------------------------------------
# Stationarity (screen_stationarity)
# --------------------------------------------------------------------------------------
@dataclass
class Stop:
    oid: str
    a: int
    b: int
    dwell: float
    v_ls: float
    sigma: float
    p_loose: float
    p_strict: float
    loose: bool | None
    strict: bool | None
    synthetic: bool = False  # mastery r1 (SCR-M1-02): a contact window of a moving screener, not a stand


def _split_disp(k, a, b, P) -> list:
    """Split a stand interval where the position leaves the stop anchor by more than exit_disp_m."""
    # exit threshold: the larger of exit_disp_m and exit_k_sigma x the smoothed two-point position sigma
    sp = K_CAL * math.sqrt(2.0 * float(np.nanmean(k.var_p[a:b + 1])))
    thr = max(P["exit_disp_m"], P["exit_k_sigma"] * sp)
    out, start = [], a
    while start <= b:
        na = min(int(P["anchor_frames"]), b - start + 1)
        ax, ay = np.nanmean(k.x[start:start + na]), np.nanmean(k.y[start:start + na])
        end = b
        for t in range(start, b + 1):
            if math.hypot(k.x[t] - ax, k.y[t] - ay) > thr:
                end = t - 1
                break
        if end >= start and (end - start) * DT >= P["loose_dwell_s"] - 1e-9:
            out.append((start, end))
        if end >= b:
            break
        start = max(end + 1, start + 1)
    return out


def _stops(scene, oid) -> list:
    """Stand intervals of one player with LS window speed, Rice probabilities and strict/loose flags."""
    c = _cache(scene).setdefault("stops", {})
    if oid in c:
        return c[oid]
    P = prm("screen_stationarity")
    k = scene.k(oid)
    s2 = _kv(scene, oid)["s2"]
    enter = np.where(np.isfinite(s2), s2 < P["s2_max"], False)
    stay = np.where(np.isfinite(s2), s2 < P["s2_stay"], False)
    out = []
    for a0, b0 in hysteresis(enter, stay, P["loose_dwell_s"], int(P["stand_gap_frames"])):
        for a, b in _split_disp(k, a0, b0, P):
            out.append(_stop_stats(scene, k, oid, a, b, P))
    c[oid] = out
    return out


def _stop_stats(scene, k, oid, a, b, P) -> Stop:
    n_min, trim = int(P["min_ls_frames"]), int(P["trim_frames"])
    N = b - a + 1
    if N - 2 * trim >= n_min:
        wa, wb = a + trim, b - trim
    elif N >= n_min:
        wa, wb = a, b
    else:
        wa = _cl(scene, (a + b) // 2 - n_min // 2)
        wb = _cl(scene, wa + n_min - 1)
    idx = np.arange(wa, wb + 1)
    good = np.isfinite(k.x[idx]) & np.isfinite(k.y[idx])
    if good.sum() >= 3:
        tt = idx[good] * DT
        vx = np.polyfit(tt, k.x[idx][good], 1)[0]
        vy = np.polyfit(tt, k.y[idx][good], 1)[0]
        v = float(math.hypot(vx, vy))
    else:
        v = float("nan")
    nc = P["vel_err_corr_frames"]
    sig = float(K_CAL * np.sqrt(np.nanmean(k.var_v[wa:wb + 1])) * math.sqrt(nc / (nc + len(idx))))
    dwell = (b - a) * DT
    lv, sv, ratio = P["loose_v_mps"], P["strict_v_mps"], P["testable_ratio"]
    loose = (v <= lv) if (np.isfinite(v) and lv / sig >= ratio) else None
    if dwell < P["strict_dwell_s"] - 1e-9:
        strict = False
    else:
        strict = (v <= sv) if (np.isfinite(v) and sv / sig >= ratio) else None
    return Stop(oid, a, b, dwell, v, sig, rice_below(v, lv, sig), rice_below(v, sv, sig), loose, strict)


def _moving(st: Stop, Pset) -> bool:
    """P(true |v| > loose_v) >= moving_p_min: the stop is a walk, not a stand (disjoint from LOOSE)."""
    return bool(np.isfinite(st.p_loose) and 1.0 - st.p_loose >= Pset["moving_p_min"])


def _disp_speed(scene, oid, half_s) -> np.ndarray:
    """Mean speed from the displacement over [t - half_s, t + half_s] (robust to a momentary stop at a corner)."""
    c = _cache(scene).setdefault("dspeed", {})
    if (oid, half_s) not in c:
        k, h = scene.k(oid), frames(half_s)
        x = np.pad(k.x, h, mode="edge")
        y = np.pad(k.y, h, mode="edge")
        c[(oid, half_s)] = np.hypot(x[2 * h:] - x[:-2 * h], y[2 * h:] - y[:-2 * h]) / (2 * h * DT)
    return c[(oid, half_s)]


def _stops_near(scene, oid, a, b) -> list:
    return [st for st in _stops(scene, oid) if st.b >= a and st.a <= b]


def _stand_run(scene, oid, a, b, min_frames=5) -> bool:
    """True when the player stands (s2 below the stay level) on >= min_frames consecutive frames of [a, b]."""
    s2 = _kv(scene, oid)["s2"][a:b + 1]
    ok = np.where(np.isfinite(s2), s2 < prm("screen_stationarity")["s2_stay"], False)
    run = best = 0
    for v in ok:
        run = run + 1 if v else 0
        best = max(best, run)
    return best >= min_frames


# --------------------------------------------------------------------------------------
# The canonical screen record (screen_set, screen, screen_moment, screen_read, interaction)
# --------------------------------------------------------------------------------------
@dataclass
class Rec:
    """One SET row: screener s stopped near D, the defender of teammate u."""
    s: str
    u: str
    D: str
    Ds: str | None
    stop: Stop
    ts: int
    kind: str  # on_ball | off_ball
    is_screen: bool
    p_set: float
    p: float
    m: dict = field(default_factory=dict)  # every measurement and label of the row


def _t_s(scene, dd, lo, hi, P, dsu=None, u_speed=None, su_from=None):
    """Screen moment over [lo, hi] (screen_moment).

    Dips of d_sD are minima <= d_su_max_m separated by a rise of >= screen_window.hyst_m. Each dip's
    contact window is the contiguous run of frames with d <= max(dip min + dip_band_m,
    set_def_radius_m) (the defender is still engaged with the screener). The window used is the one
    nearest the user's closest approach to the screener (taken over frames where the user moves), and
    t_s is its frame nearest that approach; with no user motion (unused screen), t_s is the first frame
    of the earliest contact window (contact is made).
    A defender parked on the screener therefore does not move the reference (CTG: the frame is
    chosen close to the use), and correlated noise on a flat contact does not split it.
    Returns (frame, dip half-width in frames).
    """
    seg = dd[lo:hi + 1]
    if not np.any(np.isfinite(seg)):
        return None, None
    seg = np.where(np.isfinite(seg), seg, np.inf)
    thr, hyst = prm("screen")["d_su_max_m"], prm("screen_window")["hyst_m"]
    # closest approach of the user while moving
    tsu = None
    if dsu is not None:
        su = np.array(dsu[lo:hi + 1], dtype=float)
        if u_speed is not None:  # the use happens in motion; a user who never moves gives no closest approach
            moving = np.asarray(u_speed[lo:hi + 1]) >= P["tsu_min_speed_mps"] - 1e-9
            su = np.where(moving, su, np.nan)
        if su_from is not None:  # the use happens while the screener stands (not while he runs past the user)
            su[:max(0, su_from - lo)] = np.nan
        if np.any(np.isfinite(su)):
            tsu = int(np.nanargmin(su))
    # dips of d_sD
    mins = [i for i in range(len(seg)) if seg[i] <= thr and seg[i] == seg[max(0, i - 3):i + 4].min()]
    dips = []
    for i in mins:
        if dips and seg[dips[-1][-1]:i + 1].max() < max(seg[dips[-1][-1]], seg[i]) + hyst:
            dips[-1].append(i)
        else:
            dips.append([i])
    dips_ext = []
    engaged = prm("screen_set")["set_def_radius_m"]
    for dp in dips or [[int(np.argmin(seg))]]:
        i0 = min(dp, key=lambda i: seg[i])
        band = max(seg[i0] + P["dip_band_m"], engaged)  # contact window: the defender is still engaged
        a0, b0 = dp[0], dp[-1]
        while a0 - 1 >= 0 and seg[a0 - 1] <= band:
            a0 -= 1
        while b0 + 1 < len(seg) and seg[b0 + 1] <= band:
            b0 += 1
        dips_ext.append((i0, a0, b0, [i for i in range(a0, b0 + 1) if seg[i] <= band]))
    if tsu is None:  # unused: the moment contact is first made while the screener stands
        i0, a0, b0, inside = dips_ext[0]
        k0 = max(0, (su_from - lo) if su_from is not None else 0)
        later = [i for i in inside if i >= k0]
        return lo + (later[0] if later else inside[-1]), (b0 - a0) // 2
    i0, a0, b0, inside = min(dips_ext, key=lambda d: min(abs(i - tsu) for i in d[3]))
    return lo + min(inside, key=lambda i: abs(i - tsu)), (b0 - a0) // 2


def _records(scene, set_over=None, screen_over=None) -> list:
    """All SET rows of the clip (screens, rejected and unused), de-duplicated and re-screen merged."""
    key = ("recs", tuple(sorted((set_over or {}).items())), tuple(sorted((screen_over or {}).items())))
    c = _cache(scene)
    if key in c:
        return c[key]
    Pset, Pscr = prm("screen_set", set_over), prm("screen", screen_over)
    Ptd, Pmo, Pb = prm("screen_target_defender"), prm("screen_moment"), prm("ball_screen_model")
    recs, still = [], []
    for s in scene.offense:
        excl = []  # (a, b, D) of earlier SET rows of s: D was screened there, not guarding s (SCR-T04)
        for st in _stops(scene, s):
            if _moving(st, Pset):
                continue  # confidently moving (lower bound above the loose band): not a SET
            if _holds(scene, s, st.a, st.b) >= Pset["holder_frac"] * (st.b - st.a + 1):
                continue  # the screener holds the ball (handoff phase is handled by dho)
            ra_, rb_ = _win(scene, st.a, -Pset["pad_s"], 0)[0], _win(scene, st.b, 0, Pset["receive_s"])[1]
            if any(x["to"] == s and ra_ <= x["catch"] <= rb_
                   and not (x["catch"] > st.b and _rolling_catch(scene, s, x["catch"], Pb, h=x["frm"]))
                   for x in _transfers(scene)):
                # s receives the ball at this stop: a handoff receiver or a catch, not a screener (a catch after the stand
                # while he rolls to the rim is a pocket pass to the roller, SCR-M3-01)
                continue
            tf = _cl(scene, st.a - frames(Ptd["freeze_offset_s"]))
            tf = _inherit_freeze(scene, s, st, tf, recs)
            mu = _matchup_excl(scene, tf, s, excl)
            lo, hi = _win(scene, st.a, -Pmo["pad_s"], 0)[0], _win(scene, st.b, 0, Pmo["pad_s"])[1]
            for d in scene.defense:
                dd = _dist(scene, s, d)
                # the defender is within reach while s stands (SCR-T06: not anywhere in the padded window, so a
                # player who runs past a defender and stops just after is not a SET on him)
                if np.sum(dd[st.a:st.b + 1] <= Pset["set_def_radius_m"]) < Pset["def_contact_frames"]:
                    continue
                probs = mu[d]
                ob = _onball_defender(scene, s, d, st.a, Ptd)
                if ob is not None and ob[2] and not (max(probs, key=probs.get) == s
                                                     or probs.get(s, 0.0) >= Ptd["own_man_p"]):
                    ob = None  # SCR-M2-09: the screener-came override is used only against an own-man reading
                if ob is not None and max(probs, key=probs.get) != ob[0]:
                    # loop 4 (SCR-L4-02): d is guarding the ball (nearest defender to the holder over the second before the
                    # stand); the on-ball role is instantaneous, the 2 s mean-distance proxy still reads his previous man
                    probs = {o: (ob[1] if o == ob[0] else (1.0 - ob[1]) * probs[o] / max(1e-9, 1.0 - probs[ob[0]]))
                             for o in probs}
                u = max(probs, key=probs.get)
                if u == s or probs.get(s, 0.0) >= Ptd["own_man_p"]:
                    continue  # own-man stop
                ts, half = _t_s(scene, dd, lo, hi, Pmo, _dist(scene, s, u), _disp_speed(scene, u, Pmo["tsu_half_s"]),
                                su_from=st.a)
                source = "defender"
                if np.sum(scene.k(d).state[lo:hi + 1] != "observed") * DT > Pmo["occl_max_s"]:
                    # D_u bridged too long: the user's closest approach to the screener sets t_s (user_fallback)
                    su = _dist(scene, s, u)[st.a:hi + 1]
                    if np.any(np.isfinite(su)):
                        ts, source = st.a + int(np.nanargmin(su)), "user_fallback"
                if ts is None:
                    continue
                if _role_reversal(scene, s, u, ts, tf, Pset):
                    continue
                rec = _build(scene, s, u, d, st, ts, half, tf, probs, Pset, Pscr)
                if rec is not None and ob is not None and ob[2]:
                    # SCR-M2-09: a row kept only by the screener-came test must be a used on-ball screen (a roller who
                    # meets his own dropping defender is not an unused SET row on him)
                    rec.m["screener_came"] = True
                    if not (rec.kind == "on_ball" and rec.is_screen):
                        rec = None
                if rec is not None and _coincident(scene, [(s, d), (s, u)],
                                                   *_win(scene, ts, -Pb["coincident_pre_s"], 0.5), Pb):
                    rec = None  # SCR-M1-05 / SCR-M2-08: tracker pile-up / merged identity of the screener
                if rec is not None and rec.kind == "off_ball":
                    veto = _off_ball_veto(scene, s, u, ts, Pset, rec.m["passed"])
                    if veto == "still_user":
                        rec.m["veto"] = veto
                        still.append(rec)  # kept aside: veer_screen's second leg is a stand for a standing teammate
                    if veto:
                        rec = None
                if rec is not None and rec.kind == "off_ball" and not rec.is_screen and (
                        not _guards_user(scene, d, u, ts, Pb)
                        or not rec.m["approach_min_m"] <= prm("screen_read")["reject_approach_m"]):
                    # SCR-M1-04: an unused stand next to a help defender (not on the user's own defender), or one the
                    # user never comes near (min d(s, u) over [t_s - 1.0, t_s + 1.5] > screen_read.reject_approach_m), is
                    # not a SET row (after the still-user veto, whose rows veer_screen keeps)
                    rec = None
                if rec is not None and rec.kind == "on_ball" and not rec.is_screen:
                    # SCR-M1-04 (on-ball): an unused / rejected on-ball row needs D near the ball - mean d(D, h) over
                    # [t_s - 1.0, t_s] <= bd_max_m (real SportVU rows with D 5-10 m from the handler were stands next to
                    # a help defender)
                    ga_, gb_ = _win(scene, ts, -1.0, 0)
                    dh_ = _dist(scene, d, u)[ga_:gb_ + 1]
                    if not (np.any(np.isfinite(dh_)) and np.nanmean(dh_) <= Pb["bd_max_m"]):
                        rec = None
                if rec is not None:
                    rec.m["t_s_source"] = source
                    rec.m["t_freeze"] = int(tf)
                    recs.append(rec)
                    excl.append((st.a, st.b, d))
    # SCR-M2-09: a screener-came row yields to any other row of the same pair near it (the override is a recovery path for
    # a screen the matchup proxy vetoed, never a second reading of one it kept - a roller meeting his own defender)
    cont = _contact_rows(scene, recs, Pset, Pscr)  # SCR-M1-02: rolling / moving ball screeners
    if cont:
        # an off-ball row of the same pair at the same contact (the user caught the ball during the screen) is replaced
        lim = frames(Pb["contact_win_s"]) * 3
        for q in cont:
            # SCR-M3-08: the SET onset of the replaced stand row is the screen_set onset of the contact row (the contact
            # episode can start 0.5 s before the screener stood: screen_set t0 off by 0.5 s at sigma_p 0.3)
            st_ = [r.stop for r in recs if r.kind == "off_ball" and q.s == r.s and q.u == r.u and abs(q.ts - r.ts) <= lim
                   and not r.stop.synthetic]
            if st_:
                q.m["set_stop"] = (st_[0].a, st_[0].b)
        recs = [r for r in recs if not (r.kind == "off_ball" and any(
            q.s == r.s and q.u == r.u and abs(q.ts - r.ts) <= lim for q in cont))]
    recs = recs + cont
    dd_ = frames(prm("screen_window")["window_s"])
    recs = [r for r in recs if not (r.m.get("screener_came") and any(
        q is not r and q.s == r.s and q.u == r.u and not q.m.get("screener_came") and abs(q.ts - r.ts) <= dd_
        for q in recs))]
    recs = _merge(scene, recs)
    c[key] = recs
    c[key + ("still_user",)] = still
    return recs


def _runs(arr) -> list:
    """(value, start, end) runs of a per-frame object array (None runs skipped)."""
    out, i, n = [], 0, len(arr)
    while i < n:
        j = i
        while j + 1 < n and arr[j + 1] == arr[i]:
            j += 1
        if arr[i] is not None:
            out.append((arr[i], i, j))
        i = j + 1
    return out


def _coincident(scene, pairs, a, b, Pb) -> bool:
    """SCR-M1-05: two tracks closer than coincident_m (5-frame median) for coincident_frames consecutive frames of [a, b]
    are a tracker pile-up or a merged identity, not a screen (bodies cannot be closer than about 0.45 m centre to
    centre). Tested only when the pair's distance sigma is <= coincident_sigma_max_m (precise tracking, e.g. SportVU):
    at sigma_p >= 0.2 a real contact at 0.2-0.4 m reads below coincident_m by noise.
    Mastery r2 (SCR-M2-08): the pairs are the screener's - (s, D) and (s, u) - over [t_s - coincident_pre_s, t_s + 0.5]
    (a pile-up just before the window faked a contact; judged J03); (u, D) is not tested (a defender glued to the
    handler or user does not fake a screen: judged J35, a real screen, was lost to it)."""
    for x, y in pairs:
        if x is None or y is None:
            continue
        if _sigd(scene, x, y, _cl(scene, (a + b) // 2)) > Pb["coincident_sigma_max_m"]:
            continue  # on noisy tracks a close contact reads as coincident: the artefact is only testable on precise ones
        m5 = _med5(scene, x, y)[_cl(scene, a):_cl(scene, b) + 1]
        run = best = 0
        for v in np.nan_to_num(m5, nan=99.0) < Pb["coincident_m"]:
            run = run + 1 if v else 0
            best = max(best, run)
        if best >= Pb["coincident_frames"]:  # persistent: a brush past the screener's centre is not a pile-up
            return True
    return False


def _guards_user(scene, d, u, ts, Pb, used=False) -> bool:
    """SCR-M1-04 (off-ball, unused rows): d guards u before the screen - within offball_du_max_m of him on average over
    [t_s - offball_guard_pre_s, t_s - offball_guard_post_s], and either the joint assignment (_assignment) gives d to u
    or d is the defender nearest u on >= offball_guard_frac of that window (Hojo: the assignment and the nearest
    defender). A screener standing next to a help defender whose softmax matchup names a far-away attacker is not a
    screen_set row. Used screens skip this test (the user came through the screen at speed)."""
    a, b = _win(scene, ts, -Pb["offball_guard_pre_s"], -Pb["offball_guard_post_s"])
    if b < a:
        return True
    du = _dist(scene, d, u)[a:b + 1]
    if not np.any(np.isfinite(du)) or np.nanmean(du) > Pb["offball_du_max_m"]:
        return False
    if used and np.nanmean(du) <= Pb["offball_du_close_m"]:
        return True  # SCR-M2-11: a used row whose D_u stayed on u (a screener's defender may stand nearer)
    asg = _assignment(scene, b, Pb["offball_guard_pre_s"] - Pb["offball_guard_post_s"])
    if asg.get(d) == u:
        return True
    others = [_dist(scene, x, u)[a:b + 1] for x in scene.defense if x != d]
    near = np.ones(b - a + 1, dtype=bool)
    for o in others:
        near &= ~(np.nan_to_num(o, nan=99.0) < np.nan_to_num(du, nan=99.0))
    return bool(near.mean() >= Pb["offball_guard_frac"])


def _contact_rows(scene, recs, Pset, Pscr) -> list:
    """On-ball contact candidates (SCR-M1-02, ball_screen_model): screens of screeners who never form a stand.

    The stand-based SET misses rolling / moving screeners (0.6-1.5 m/s through the contact; about 16 real ball screens
    per 48 on the judged SportVU sample had no stand) and, under noise, real plants whose window speed reads above the
    loose band. For every possession run of the handler h (_poss) and every teammate s, the contact episodes are the
    frames where the 5-frame median d(s, d) <= contact_on_m + contact_k x sigma_d for a defender d that guards the ball
    (_onball_defender at the episode onset: nearest h on >= onball_def_frac of the holder frames, nearer h than s - the
    own-man veto), with >= contact_min_frames frames. Each episode becomes an on-ball row (the contact window as a
    synthetic stop, plant = moving / loose), unless a stand-based row of the same (s, h) covers it; only rows that pass
    the on-ball decision (_onball_decision) are kept, so the contact path never adds unused / rejected SET rows."""
    Pb, Ptd, Pmo, Pst = (prm("ball_screen_model"), prm("screen_target_defender"), prm("screen_moment"),
                         prm("screen_stationarity"))
    if not scene.defense:
        return []
    n = scene.n
    poss = _poss(scene)
    pad = frames(Pmo["pad_s"])
    scale = prm("screen_noise_calibration")["dist_sigma_scale"]
    out = []
    for h, a0, b0 in _runs(poss):
        if h not in scene.offense or b0 - a0 + 1 < Pb["contact_min_frames"]:
            continue
        for s in scene.offense:
            if s == h:
                continue
            ks = scene.k(s)
            for d in scene.defense:
                dd = _dist(scene, s, d)
                sg = sigma_dist(ks, scene.k(d)) * scale
                med = _med5(scene, s, d)[a0:b0 + 1]
                thr = Pb["contact_on_m"] + Pb["contact_k"] * np.nan_to_num(sg[a0:b0 + 1], nan=0.5)
                mask = np.zeros(n, dtype=bool)
                mask[a0:b0 + 1] = np.nan_to_num(med, nan=99.0) <= thr
                if mask.sum() < Pb["contact_min_frames"]:
                    continue
                for ea, eb in hysteresis(mask, mask, (Pb["contact_min_frames"] - 1) * DT,
                                         int(Pb["contact_gap_frames"])):
                    if eb - ea + 1 < Pb["contact_min_frames"]:
                        continue
                    if any(r.s == s and r.u == h and r.kind != "off_ball" and r.stop.a - pad <= eb and r.stop.b + pad >= ea
                           and not r.m.get("screener_came") for r in recs + out):
                        continue  # an on-ball / handoff row of the pair covers this contact
                    if _poss_holds(scene, s, ea, eb) >= 0.5 * (eb - ea + 1):
                        continue  # s has the ball (handoff phase / post entry)
                    ra_, rb_ = _win(scene, ea, -Pset["pad_s"], 0)[0], _win(scene, eb, 0, Pset["receive_s"])[1]
                    if any(x["to"] == s and ra_ <= x["catch"] <= rb_
                           and not (x["catch"] > eb and _rolling_catch(scene, s, x["catch"], Pb, h=x["frm"]))
                           for x in _transfers(scene)):
                        continue  # s receives the ball: a handoff receiver or a catch (not a pocket pass, SCR-M3-01)
                    # d guards the ball before the contact (SCR-M1-07), read at the onset or half a second into it
                    # (h caught the ball just before)
                    frac = _ball_defender(scene, s, d, h, ea, Pb)
                    if frac is None:
                        frac = _ball_defender(scene, s, d, h, min(eb, ea + frames(Pb["contact_win_s"])), Pb)
                    if frac is None:
                        continue  # d does not guard the ball, or he is s's own man
                    probs = {o: (frac if o == h else (1.0 - frac) / max(1, len(scene.offense) - 1))
                             for o in scene.offense}
                    lo, hi = _cl(scene, ea - pad), _cl(scene, eb + pad)
                    ts, half = _t_s(scene, dd, lo, hi, Pmo, _dist(scene, s, h),
                                    _disp_speed(scene, h, Pmo["tsu_half_s"]), su_from=ea)
                    if ts is None:
                        continue
                    st = _stop_stats(scene, ks, s, ea, eb, Pst)
                    st.synthetic = True
                    tf = _cl(scene, ea - frames(Ptd["freeze_offset_s"]))
                    rec = _build(scene, s, h, d, st, ts, half, tf, probs, Pset, Pscr, force_on_ball=True)
                    if rec is None or rec.kind != "on_ball" or not rec.is_screen:
                        continue
                    if _coincident(scene, [(s, d), (s, h)], *_win(scene, ts, -Pb["coincident_pre_s"], 0.5), Pb):
                        continue
                    # a second row of the pair within screen_window.window_s is kept only as a real re-screen: the
                    # screener relocated by > split_move_m + hyst_m (CTG 4 ft); otherwise it is the same screen read
                    # again (a stand fragment at high noise)
                    Pw = prm("screen_window")
                    if any(q.s == s and q.u == h and q.kind != "off_ball" and abs(q.ts - rec.ts) <= frames(Pw["window_s"])
                           and math.hypot(*(np.array(q.m["P_s"]) - np.array(rec.m["P_s"])))
                           <= Pw["split_move_m"] + Pw["hyst_m"] for q in recs + out):
                        continue
                    rec.m["t_s_source"] = "defender"
                    rec.m["t_freeze"] = int(tf)
                    out.append(rec)
    return out


def _assignment(scene, t, w_s) -> dict:
    """One-to-one defender -> attacker assignment minimising the summed mean distance over [t - w_s, t] (SCR-M1-07).

    The softmax proxy scores each defender alone, so a ball defender sagging into the screener's approach reads as the
    screener's man even when the screener's own defender stands next to him; the joint assignment gives each attacker
    one defender. Exhaustive over the permutations (5! = 120); {} when the teams are not 5 v 5 or distances are missing."""
    t = _cl(scene, t)
    c = _cache(scene).setdefault("assign", {})
    if (t, w_s) in c:
        return c[(t, w_s)]
    import itertools
    off, dfn = list(scene.offense), list(scene.defense)
    out = {}
    if 0 < len(dfn) <= len(off) <= 6:
        a = _cl(scene, t - frames(w_s))
        M = np.array([[np.nanmean(_dist(scene, d, o)[a:t + 1]) for o in off] for d in dfn])
        M = np.where(np.isfinite(M), M, 50.0)
        best, bp = float("inf"), None
        for perm in itertools.permutations(range(len(off)), len(dfn)):
            v = float(sum(M[i, j] for i, j in enumerate(perm)))
            if v < best:
                best, bp = v, perm
        out = {dfn[i]: off[j] for i, j in enumerate(bp)}
    c[(t, w_s)] = out
    return out


def _ball_defender(scene, s, d, h, t, Pb) -> float | None:
    """Contact path ball defender (SCR-M1-07): fraction of the handler's possession frames of [t - bd_pre_s, t - bd_post_s]
    on which d is the defender nearest h within bd_max_m (research: 12 ft), when that fraction >= bd_frac and the joint
    assignment at t - bd_post_s does not give d to s (own-man veto); also accepted when the assignment gives d to h.
    None otherwise."""
    a, b = _win(scene, t, -Pb["bd_pre_s"], -Pb["bd_post_s"])
    if b <= a:
        return None
    asg = _assignment(scene, b, Pb["bd_pre_s"] - Pb["bd_post_s"])
    if asg.get(d) == s and not _screener_came(scene, s, d, t):
        return None
    poss = _poss(scene)
    n = ok = 0
    dh = []
    for k in range(a, b + 1):
        if poss[k] != h:
            continue
        n += 1
        dists = {x: _dist(scene, x, h)[k] for x in scene.defense}
        dn = min(dists, key=lambda x: dists[x] if np.isfinite(dists[x]) else 1e9)
        ok += int(dn == d and dists[d] <= Pb["bd_max_m"])
        dh.append(dists[d])
    if n < 0.5 * (b - a + 1):
        return None
    frac = ok / n
    if frac >= Pb["bd_frac"] or (asg.get(d) == h and np.nanmean(dh) <= Pb["bd_max_m"]):
        return max(frac, 0.5)
    return None


def _onball_defender(scene, s, d, a, Ptd):
    """(holder h, frac) when d guards the ball before the stand of s that starts at a (loop 4, SCR-L4-02): over
    [a - onball_window_s, a] one teammate h != s holds the ball on >= onball_hold_frac of the frames and d is the defender
    nearest h, within onball_def_max_m, on frac >= onball_def_frac of the frames where h holds it. None otherwise."""
    wa, wb = _win(scene, a, -Ptd["onball_window_s"], 0)
    hold = _poss(scene)[wa:wb + 1]  # mastery r1 (SCR-M1-01): noise-robust possession
    hs = [x for x in hold if x is not None]
    if not hs:
        return None
    h = max(set(hs), key=hs.count)
    if h == s or h not in scene.offense or hs.count(h) < Ptd["onball_hold_frac"] * len(hold):
        return None
    n = ok = 0
    dh_, ds_ = [], []
    for t in range(wa, wb + 1):
        if hold[t - wa] != h:
            continue
        n += 1
        dists = {dd: _dist(scene, dd, h)[t] for dd in scene.defense}
        dn = min(dists, key=lambda k: dists[k] if np.isfinite(dists[k]) else 1e9)
        ok += int(dn == d and dists[d] <= Ptd["onball_def_max_m"])
        dh_.append(dists[d])
        ds_.append(_dist(scene, d, s)[t])
    frac = ok / n if n else 0.0
    if frac < Ptd["onball_def_frac"]:
        return None
    came = False
    if Ptd["onball_nearer_holder"] and not np.nanmean(dh_) < np.nanmean(ds_):
        if not _screener_came(scene, s, d, a):
            return None  # d sits on the screener, not on the ball (a help defender dropping with his own man)
        came = True
    return h, float(frac), came


def _screener_came(scene, s, d, a) -> bool:
    """SCR-M2-09 (own-man veto revisited): the screener closed the distance to d himself - over [a - came_s, a] his
    displacement toward d's position at a is >= came_m and d's own displacement toward him is <= came_ratio of that. A
    defender who guards s follows s; one whom s runs at to screen does not (judged J34: D stood beside the handler's path,
    the screener ran 2.5 m to him, and the 2 s matchup proxy / joint assignment called D the screener's man)."""
    P = prm("ball_screen_model")
    a0, a1 = _win(scene, a, -P["came_s"], 0)
    s0, s1, d0, d1 = _pos(scene, s, a0), _pos(scene, s, a1), _pos(scene, d, a0), _pos(scene, d, a1)
    if not _fin(*s0, *s1, *d0, *d1):
        return False
    u_sd = _unit(d1 - s0)
    u_ds = _unit(s0 - d0)
    if not (np.all(np.isfinite(u_sd)) and np.all(np.isfinite(u_ds))):
        return False
    adv_s = float((s1 - s0) @ u_sd)
    adv_d = float((d1 - d0) @ u_ds)
    # and d was not with s when he set off (a roller meeting his own dropping defender): at a - came_s, d is no nearer s
    # than the nearest other attacker is to d
    near_other = min((float(_dist(scene, d, o)[a0]) for o in scene.offense if o != s), default=float("inf"))
    return bool(adv_s >= P["came_m"] and adv_d <= P["came_ratio"] * adv_s
                and not float(_dist(scene, d, s)[a0]) < near_other)


def _still_user_rows(scene) -> list:
    """Off-ball stands on a standing teammate's defender, vetoed as SET rows (loop 2) but kept for veer_screen."""
    key = ("recs", (), ())
    _records(scene)
    return _cache(scene)[key + ("still_user",)]


def _inherit_freeze(scene, s, st, tf, recs) -> int:
    """Freeze frame for a stop of s that follows an earlier SET row of s within screen_window.window_s (SCR-T04).

    The default window [a - 1 - 2 s, a - 1] of a second screen covers the first one, where the screened defender
    stood next to s; the softmax proxy then reads him as s's own man and the used re-screen is dropped. The earlier
    row's freeze is reused unless that screen was switched or the ball changed hands in between (then the matchup
    really changed)."""
    w = frames(prm("screen_window")["window_s"])
    prev = [q for q in recs if q.s == s and 0 < st.a - q.stop.b <= w]
    if not prev:
        return tf
    q = min(prev, key=lambda q: q.stop.a)
    if any(q.ts < x["catch"] <= st.a for x in _transfers(scene)):
        return tf
    if q.Ds is not None and _switch(scene, q.D, q.s, q.Ds, q.u, q.ts, prm("ball_screen_coverage"))["switch"] != "none":
        return tf
    return min(tf, q.m.get("t_freeze", tf))


def _still_user(scene, u, ts, Pset, passed=False) -> bool:
    """True when u stands through the screen: a stop of u covers [t_s - still_cover_s, t_s + still_cover_s] and his
    5-frame median speed stays below still_user_mps over [t_s - still_pre_s, t_s + still_post_s]; or u, without
    passing the screener, settles into a stand that starts within still_cover_s of t_s and outlasts the window."""
    ca, cb = _win(scene, ts, -Pset["still_cover_s"], Pset["still_cover_s"])
    if any(ust.a <= ca and ust.b >= cb for ust in _stops(scene, u)):
        return _peak_speed(scene, u, ts, Pset) < Pset["still_user_mps"]
    # u settles into his own stand at t_s (two screeners arriving side by side): his stop starts by t_s + still_cover_s,
    # lasts past t_s + still_post_s and he does not move again from its onset
    if passed:
        return False  # a user who comes through the screen and stops (end of a stagger cut) used it
    pe = _win(scene, ts, 0, Pset["still_post_s"])[1]
    sp = _kv(scene, u)["speed"]
    for ust in _stops(scene, u):
        if ca < ust.a <= cb and ust.b >= pe and not _moving(ust, Pset):
            v = [_med(sp, t) for t in range(ust.a, pe + 1)]
            if np.any(np.isfinite(v)) and np.nanmax(v) < Pset["still_user_mps"]:
                return True
    return False


def _peak_speed(scene, u, ts, Pset) -> float:
    """Peak 5-frame median speed of u over [t_s - still_pre_s, t_s + still_post_s]."""
    sp = _kv(scene, u)["speed"]
    a, b = _win(scene, ts, -Pset["still_pre_s"], Pset["still_post_s"])
    v = [_med(sp, t) for t in range(a, b + 1)]
    return float(np.nanmax(v)) if np.any(np.isfinite(v)) else float("nan")


def _off_ball_veto(scene, s, u, ts, Pset, passed=False):
    """Loop 2 (SCR-T06 residual): an off-ball row is dropped when the 'screener' holds the ball around t_s (a ball
    holder is not an off-ball screener) or when the 'user' stands through it (nobody used or rejected it: a cutter
    stopping next to a standing teammate's defender, a second screener 'screening' the first)."""
    h = frames(Pset["holder_veto_s"])
    if _holds(scene, s, ts - h, ts + h) >= Pset["holder_veto_frames"]:
        return "holder"
    return "still_user" if _still_user(scene, u, ts, Pset, passed) else None


def _role_reversal(scene, s, u, ts, tf, Pset) -> bool:
    """True when the 'user' u starts a stand within role_reversal_s after t_s next to s's own defender: u was running
    in to screen for s (double / stagger / elevator set-ups, a cutter ending next to a screener), so the row (s, u)
    has the roles reversed (SCR-T06)."""
    Ds, pDs = _defender_of(scene, s, tf)
    if Ds is None or pDs < 0.5:
        return False
    lim = frames(Pset["role_reversal_s"])
    n_on = frames(prm("screen_stationarity")["loose_dwell_s"])
    for st in _stops(scene, u):
        if not (ts <= st.a <= ts + lim) or _moving(st, Pset):
            continue
        if _holds(scene, u, st.a, st.b) >= Pset["holder_frac"] * (st.b - st.a + 1):
            continue  # u holds the ball there: a handler picked up by a switch, not a screener
        dd = _dist(scene, u, Ds)[st.a:min(st.b, st.a + n_on) + 1]
        if np.any(np.isfinite(dd)) and np.nanmedian(dd) <= Pset["set_def_radius_m"]:
            return True
    return False


def _build(scene, s, u, D, st, ts, half, tf, probs, Pset, Pscr, force_on_ball=False) -> Rec | None:
    """Measure one (s, u, D) candidate around its screen moment (force_on_ball: a contact candidate, SCR-M1-02)."""
    Pf, Ptd, Pr, Pi = prm("screen_frame"), prm("screen_target_defender"), prm("screen_read"), prm("screen_interaction")
    Pa, Pb = prm("screen_angle"), prm("ball_screen_model")
    # screen point: mean of the standing screener within +-ps_avg_s of t_s (s(t_s) outside the stop)
    pa_, pb_ = max(st.a, _win(scene, ts, -Pf["ps_avg_s"], 0)[0]), min(st.b, _win(scene, ts, 0, Pf["ps_avg_s"])[1])
    ks_ = scene.k(s)
    Ps = (np.array([np.nanmean(ks_.x[pa_:pb_ + 1]), np.nanmean(ks_.y[pa_:pb_ + 1])]) if pb_ >= pa_
          else _pos(scene, s, ts))
    if not _fin(*Ps):
        return None
    xs, ys = Ps
    if not (abs(xs) < SIDE_X and ys > END_Y):
        return None  # screener out of bounds (Rule 4-35.2.c / named_spots in-bounds gate)
    if ys > Pset["frontcourt_y_m"] + Pset["drag_allowance_m"]:
        return None
    m = {}
    # ---- kind, inbound context, location gates ----
    bpos = _pos(scene, "ball", ts)
    inbound = bool(_fin(*bpos) and (abs(bpos[0]) >= prm("screen_inbound_context")["side_x_m"]
                                    or bpos[1] <= prm("screen_inbound_context")["end_y_m"]))
    # on-ball kind from the noise-robust possession (SCR-M1-01; the cleaned holder lost the dribble under noise)
    on_ball = force_on_ball or ((not inbound) and _poss_holds(scene, u, ts - 4, ts + 4) >= Pscr["onball_frames"])
    handoff = any(x["frm"] == s and x["to"] == u and x["type"] == "dho"
                  and _win(scene, st.a, -Pset["pad_s"], 0)[0] <= x["catch"] <= _win(scene, st.b, 0, Pset["pad_s"])[1]
                  for x in _transfers(scene))
    # SCR-M1-06: s handed the ball to u at close range just before t_s (a pitch-typed exchange of a handoff): a handoff
    # row, not a ball screen (judged SportVU sample: handoffs were 2 of the stand-based ball-screen FPs)
    hx0, hx1 = _win(scene, ts, -Pb["handoff_s"], 0.3)
    handoff = handoff or any(x["frm"] == s and x["to"] == u and hx0 <= x["catch"] <= hx1 and x["d_ab"] <= Pb["handoff_d_m"]
                             and x["air_s"] <= Pb["handoff_air_s"] + 1e-9 for x in _transfers(scene))
    if not handoff:
        # the same from the noise-robust possession (the transfer list loses the exchange under noise): s owned the
        # ball in [t_s - handoff_s, t_s + 0.3] and u right after, with the pair within handoff_d_m at the change
        ps_ = _poss(scene)
        for t in range(max(hx0, 1), hx1 + 1):
            if ps_[t] == u and ps_[t - 1] != u:
                k = t - 1
                while k >= max(0, t - frames(Pb["handoff_air_s"])) and ps_[k] is None:
                    k -= 1
                if k >= 0 and ps_[k] == s:
                    ca_, cb_ = _cl(scene, k - 3), _cl(scene, t + 3)
                    if np.nanmin(_dist(scene, s, u)[ca_:cb_ + 1]) <= Pb["handoff_d_m"]:
                        handoff = True
                        break
    tg_ = _gives_to(scene, u, s, ts, Pb) if on_ball else None
    if tg_ is not None and not _rolling_catch(scene, s, tg_, Pb, h=u):
        # SCR-M2-04: the 'handler' hands the ball to the 'screener' right after t_s: a DHO (u -> s), not a screen; a
        # catch while the screener rolls to the rim is a pocket pass to the roller and keeps the screen (SCR-M3-01)
        return None
    xf = [x for x in _transfers(scene) if x["frm"] == s and x["to"] == u
          and _win(scene, ts, -Pb["pass_screen_s"], 0)[0] <= x["catch"] <= ts]
    m["pass_and_screen"] = bool(xf) and not handoff  # SCR-M2-06: s passed to u, then screened for him
    r_s = float(math.hypot(xs, ys))
    if on_ball and not (Pset["on_ball_r_min_m"] <= r_s <= Pset["on_ball_r_max_m"]):
        return None
    if not on_ball and _fin(*bpos) and ys - bpos[1] > Pset["off_ball_upcourt_max_m"]:
        return None
    ambiguous = max(probs.values()) < Ptd["ambiguous_p"]
    top2 = sorted(probs, key=probs.get, reverse=True)[:2]
    # screener's own defender at the freeze
    Ds, pDs = _defender_of(scene, s, tf)
    if Ds == D or pDs < 0.5:
        Ds = None
    # ---- defender distance, contact ----
    dd = _dist(scene, s, D)
    dsD_ts = _med(dd, ts)
    sig_sD = _sigd(scene, s, D, ts)
    lo, hi = _win(scene, st.a, -Pset["pad_s"], 0)[0], _win(scene, st.b, 0, Pset["pad_s"])[1]
    dsD_min = float(np.nanmin(dd[lo:hi + 1]))
    contact = ("likely" if dsD_ts <= Pset["contact_likely_m"] else "possible" if dsD_ts <= Pset["contact_possible_m"]
               else "unlikely" if dsD_ts <= Pset["set_def_radius_m"] else "none")
    # ---- closest approach of the user ----
    dsu = _dist(scene, s, u)
    a1, b1 = _win(scene, ts, -Pscr["ca_pre_s"], Pscr["ca_post_s"])
    # closest approach while the user moves and the screener stands (SCR-T03): a stationary set-up next to a
    # standing handler is not the approach; fall back to the plain minimum only when no frame qualifies
    Pmo = prm("screen_moment")
    usp_ = _disp_speed(scene, u, Pmo["tsu_half_s"])[a1:b1 + 1]
    seg_ = np.array(dsu[a1:b1 + 1], dtype=float)
    idx_ = np.arange(a1, b1 + 1)
    ok_ = (usp_ >= Pmo["tsu_min_speed_mps"] - 1e-9) & (idx_ >= st.a)
    for ust in _stops(scene, u):  # a user settling into his own stand is not using the screen (side-by-side arrivals)
        if not _moving(ust, Pset):
            ok_ &= ~((idx_ >= ust.a - frames(Pscr["user_arrive_s"])) & (idx_ <= ust.b))
    gated = np.where(ok_, seg_, np.nan)
    if np.any(np.isfinite(gated)):
        tc = a1 + int(np.nanargmin(gated))
    else:
        tc = a1 + int(np.nanargmin(seg_)) if np.any(np.isfinite(seg_)) else ts
    dsu_ca = _med(dsu, tc, int(Pscr["ca_median_frames"]) // 2)
    sig_su = _sigd(scene, s, u, tc)
    user_speed = _med(_kv(scene, u)["speed"], tc)
    # ---- user path direction, screen line, crossing ----
    u0 = _pos(scene, u, _win(scene, ts, -Pf["disp_pre_s"], 0)[0])
    u1 = _pos(scene, u, _win(scene, ts, 0, Pf["disp_post_s"])[1])
    disp = u1 - u0
    d_hat = _unit(disp) if np.hypot(*disp) >= Pf["min_disp_m"] else _unit(Ps - u0)
    e_perp = np.array([-d_hat[1], d_hat[0]])
    pa, pb = _win(scene, ts, -Pf["pass_pre_s"], Pf["pass_post_s"])
    ku = scene.k(u)
    lam = (ku.x[pa:pb + 1] - xs) * d_hat[0] + (ku.y[pa:pb + 1] - ys) * d_hat[1]
    lat = np.abs((ku.x[pa:pb + 1] - xs) * e_perp[0] + (ku.y[pa:pb + 1] - ys) * e_perp[1])
    passed, t_h = False, None
    below = np.flatnonzero(lam <= -Pf["pass_margin_m"])
    if len(below):
        after = np.flatnonzero(lam[below[0]:] >= Pf["pass_margin_m"])
        if len(after):
            zero = int(np.flatnonzero(lam[below[0]:] >= 0)[0])
            k0 = below[0] + zero
            # the crossing happens within reach of the screener (on-ball: a handler going wide at up to use_near_m still
            # uses the screen, SCR-M1-03)
            if lat[k0] <= (max(Pf["pass_lateral_m"], Pb["use_near_m"]) if on_ball else Pf["pass_lateral_m"]):
                passed = True
                t_h = pa + k0
    inter = _interaction(scene, s, u, D, ts, dsD_ts, Ps, d_hat, Pi)
    # away use (off-ball flare / fade, SCR-T05; on the ball moving away is a reject): the user starts beside the screener and moves straight away from him while
    # gaining separation from D_u; he never crosses the screen line, which the passed test needs
    # SCR-M1-08: 'straight away' is read from the gain of the user-screener distance over the displacement (radial
    # component >= cos(away_use_deg) x |displacement|), not from the angle to u0 - P_s, whose direction is noise when the
    # user starts within about 1 m of the screener (V0 sigma_p 0.3: 70-84 deg on true 0-deg fades)
    away_use = bool(not passed and not on_ball and np.hypot(*disp) >= Pa["flare_disp_m"]
                    and np.hypot(*(u1 - Ps)) - np.hypot(*(u0 - Ps)) >= math.cos(math.radians(Pf["away_use_deg"]))
                    * np.hypot(*disp)
                    and np.isfinite(inter["sep_gain_m"]) and inter["sep_gain_m"] >= Pi["sep_gain_m"])
    if away_use:
        passed, t_h = True, ts
        # the closest approach of a fade is its first step: read the speed gate as the peak over [t_c, t_c + 0.5 s]
        sp_ = _kv(scene, u)["speed"]
        user_speed = max(user_speed, max(_med(sp_, t) for t in range(tc, _win(scene, tc, 0, Pf["away_speed_s"])[1] + 1)))
    # ---- blocking: screener on the defender's route to where the user is going ----
    ba, bb = _win(scene, ts, -0.3, 0.5)
    look = frames(Pf["block_lookahead_s"])
    nblock, bmargin = 0, float("inf")
    for t in range(ba, bb + 1):
        tgt = _pos(scene, u, _cl(scene, t + look))
        dseg, uu = _seg_proj(_pos(scene, s, t), _pos(scene, D, t), tgt)
        if np.isfinite(dseg) and uu > 0.0:
            bmargin = min(bmargin, dseg)
            if dseg <= Pf["block_radius_m"]:
                nblock += 1
    blocking = nblock >= Pf["block_min_frames"] or contact == "likely"
    # ---- screen normal, angle, generic direction ----
    na, nb = _win(scene, ts, -Pf["n_avg_pre_s"], Pf["n_avg_post_s"])
    na = max(na, min(st.a, ts))  # the set: do not average over the screener's approach
    nvec = np.nanmean([_unit(_pos(scene, D, t) - _pos(scene, s, t)) for t in range(na, nb + 1)], axis=0)
    n = _unit(nvec)
    n_r = float(n @ _unit(Ps)) if r_s > 0.3 else float("nan")
    upa, upb = _win(scene, ts, -0.5, -0.1)
    v_pre = _mean_v(scene, u, upa, upb)
    u_hat_pre = _unit(v_pre) if np.hypot(*v_pre) >= 1.0 else d_hat
    angle = _ang(n, -u_hat_pre)
    orient = _ang(n, np.array([0.0, 1.0]))
    o_fold = min(orient, 180.0 - orient) if np.isfinite(orient) else float("nan")  # angle of n from the y axis
    angle_class = None if not np.isfinite(angle) else ("glancing" if angle > Pa["glancing_deg"] else "square")
    orient_class = (None if not np.isfinite(o_fold) else "flat" if o_fold <= Pa["flat_deg"]
                    else "angled" if Pa["angled_lo_deg"] <= o_fold <= Pa["angled_hi_deg"] else "other")
    r_u0, r_u1 = float(np.hypot(*u0)), float(np.hypot(*u1))
    dr_u = r_u1 - r_u0
    to_ball = (bpos - u0) if _fin(*bpos) else np.array([np.nan, np.nan])
    ang_ball = _ang(disp, to_ball)
    if np.isfinite(ang_ball) and ang_ball >= Pa["flare_deg"] and np.hypot(*disp) >= Pa["flare_disp_m"]:
        gen = "flare"
    elif n_r >= Pa["n_r_back"] and dr_u <= Pa["back_dr_m"]:
        gen = "back"
    elif n_r <= Pa["n_r_down"] and dr_u >= Pa["down_dr_m"]:
        gen = "down"
    elif (ys < Pa["cross_y_m"] and u0[1] < Pa["cross_y_m"] and abs(disp[0]) >= 2 * abs(disp[1])
          and abs(disp[0]) >= Pa["cross_dx_m"]):
        gen = "cross"
    elif np.isfinite(ang_ball) and ang_ball < Pa["middle_deg"]:
        gen = "middle"
    else:
        gen = "other"
    # ---- read (screen_read) ----
    gate_speed = Pscr["user_speed_on_mps"] if on_ball else Pscr["user_speed_off_mps"]
    if on_ball:
        # SCR-M1-03: the handler's use is the crossing of the screen line within use_near_m of the screener with the
        # screener on D_h's route or in contact (the 1.2 m centre gate dropped real screens where the handler goes
        # wide at 1.3-1.8 m: 4 real and 2 ambiguous of 8 judged not_geo rows)
        # SCR-M2-10: the use distance tightens with the pair's distance sigma (use_near_m - use_k x sigma_d): under noise a
        # handler passing 1.7-2.0 m from the screener is as likely a reject or a pass-by (noise-only rows at sigma_p 0.3 /
        # 0.5 judged mostly ambiguous or not screens)
        use = bool(dsu_ca <= Pb["use_near_m"] - min(Pb["use_k"] * sig_su, Pb["use_k_cap_m"]) and passed and (blocking or contact != "none")
                   and user_speed >= gate_speed)
    else:
        use = bool(dsu_ca <= Pscr["d_su_max_m"] and passed and blocking and user_speed >= gate_speed)
    ra, rb = _win(scene, ts, -1.0, 1.5)
    approach_min = float(np.nanmin(dsu[ra:rb + 1]))
    # attack direction: the user's mean velocity over 0.5 s from the first frame (from t_s - 0.5) at which he moves
    usp = _disp_speed(scene, u, prm("screen_moment")["tsu_half_s"])
    ga, gb = _win(scene, ts, -0.5, 1.5)
    t_go = next((t for t in range(ga, gb + 1) if usp[t] >= prm("screen_moment")["tsu_min_speed_mps"]), tc)
    v_post = _mean_v(scene, u, *_win(scene, t_go, 0, 0.5))
    turn = _ang(v_post, Ps - _pos(scene, u, t_go))
    # on-ball (SCR-M1-03): the use is the crossing, so a handler who comes close but turns away without crossing is a
    # reject at any closest approach (an ICE handler can brush the screener at 0.9 m)
    reject = bool((not use) and approach_min <= Pr["reject_approach_m"] and (on_ball or dsu_ca > Pscr["d_su_max_m"])
                  and not passed and np.isfinite(turn) and turn >= Pr["reject_turn_deg"]
                  and _peak_speed(scene, u, ts, Pset) >= Pset["still_user_mps"])  # loop 2: a reject is a move
    if reject and on_ball:
        # mastery r3 (SCR-M3-07): an on-ball reject is a move - the handler gets >= reject_disp_m from h(t_s - 0.5) within
        # [t_s - 0.5, t_s + use_disp_post_s] (smoothed positions); at sigma_p 0.5 a handler standing through an unused
        # set-up read a reject from his speed noise (0.9-1.1 m/s peak) and became a ball_screen_coverage row
        ra2, rb2 = _win(scene, ts, -0.5, Pb["use_disp_post_s"])
        dd2 = np.hypot(ku.x[ra2:rb2 + 1] - ku.x[ra2], ku.y[ra2:rb2 + 1] - ku.y[ra2])
        reject = bool(np.any(np.isfinite(dd2)) and np.nanmax(dd2) >= Pr["reject_disp_m"])
    read = "use" if use else "reject" if reject else "unused"
    if on_ball:
        rta, rtb = _win(scene, ts, 0.1, 0.1 + Pr["retreat_s"])
        if np.nanmean(_kv(scene, u)["vr"][rta:rtb + 1]) <= -Pr["retreat_vr_mps"]:
            read = "retreat"
        elif use and t_h is not None:
            # side of the rim->screener line (CourtMotion side test): the use flips it, a snake flips it back
            wa_, wb_ = t_h, _win(scene, t_h, 0, Pr["snake_s"])[1]
            rs = _unit(Ps)
            wl = (rs[0] * ku.y[wa_:wb_ + 1] - rs[1] * ku.x[wa_:wb_ + 1])
            pre_side = np.sign(rs[0] * u0[1] - rs[1] * u0[0])
            if pre_side != 0 and np.any(wl * pre_side >= Pf["pass_margin_m"]) and \
                    np.nanmin(wl[:5] * pre_side) < 0:
                read = "snake"
            elif Ds is not None:
                for t in range(max(0, t_h - 3), min(scene.n, t_h + 4)):
                    dseg, uu = _seg_proj(_pos(scene, u, t), _pos(scene, D, t), _pos(scene, Ds, t))
                    if dseg <= Pr["split_seg_m"] and 0.15 < uu < 0.85 and _dist(scene, D, Ds)[t] < Pr["split_gap_m"]:
                        read = "split"
                        break
    exit_cls = None
    if not on_ball and use:
        ue = _pos(scene, u, _win(scene, ts, 0, 1.5)[1])
        dpost = ue - _pos(scene, u, t_h if t_h is not None else ts)
        if float(np.hypot(*ue)) < r_s - Pr["curl_dr_m"]:
            exit_cls = "curl"
        elif np.isfinite(_ang(dpost, to_ball)) and _ang(dpost, to_ball) > Pr["fade_deg"]:
            exit_cls = "fade"
        else:
            exit_cls = "straight"
    # ---- flags (R-ST-17) ----
    u_moving = bool(_disp_speed(scene, u, prm("screen_moment")["tsu_half_s"])[tc] >= Pscr["user_moving_mps"])
    geo = bool(dsu_ca <= Pscr["d_su_max_m"] and dsD_ts <= Pset["set_def_radius_m"] and u_moving)
    onb = None
    if not on_ball:
        # SCR-M1-08 (research OFF-BALL USED): an off-ball screen row is a used screen - besides the closest approach of
        # the screen test (d_su_ca <= d_su_max_m, user moving), the user comes through it (passed, or the away use of a
        # fade) at >= screen.user_speed_off_mps: peak 5-frame median speed within +-offball_use_win_s of his closest
        # approach (a fade: also the peak over its first away_speed_s; research: 2.0 m/s around the screen);
        # the rest stays in the screen_set / screen_read layer. Judged SportVU off-ball screen rows that failed this
        # were post scrums, pairs jogging side by side, slow drifts (user 1.1-1.9 m/s) and users who turned back
        # before the screener. No blocking term (a second stagger screener's defender already trails).
        spu = _kv(scene, u)["speed"]
        ua_, ub_ = _win(scene, tc, -Pb["offball_use_win_s"], Pb["offball_use_win_s"])
        upk = max([user_speed] + [_med(spu, t) for t in range(ua_, ub_ + 1)])
        m["user_peak_mps"] = upk
        # SCR-M1-10: no off-ball screen under the rim (P_s within offball_r_min_m: rebound / post scrums)
        # SCR-M2-07: and the offense has the ball around t_s (box-outs and rebound scrums after a shot are not screens)
        ob_ = _offense_has_ball(scene, ts, Pb)
        m["ball_unobserved"] = ob_ is None
        m["offense_ball"] = bool(ob_) or (ob_ is None and dr_u >= Pb["offball_dropout_dr_m"])
        # SCR-M2-11: the screener blocks D_u's route or interacts with him, or the user sprints by (>= offball_fast_use_mps:
        # a second stagger screener's defender already trails; judged SportVU used rows with none of the three, users at
        # 2.0-2.7 m/s, were 1 ambiguous and 2 not screens of 3),
        # and D_u guarded u before the screen (Hojo: the assignment, the nearest defender, or within offball_du_close_m of
        # him on average - judged rows with D_u 1.5-2 m off u while another defender guarded him were not screens)
        # (tested on precise tracks only, pair sigma <= offball_guard_sigma_max_m: with sigma_p >= 0.2 the 1.2 s mean
        # distances blur and stack / stagger users lost their screens to it in the synthetic sweep)
        m["guards_user"] = (_sigd(scene, D, u, ts) > Pb["offball_guard_sigma_max_m"]
                            or _guards_user(scene, D, u, ts, Pb, used=True))
        # SCR-M2-12 (research OFF-BALL: s makes CONTACT on D_u): min 5-frame median d(s, D_u) over t_s +- contact_win_s
        # <= contact_on_m + contact_k x sigma_d, as for ball screens (rows with D_u 1.3-1.5 m off the screener throughout
        # were judged mostly ambiguous: the defender went under or was never on the screener's line)
        ca_, cb_ = _win(scene, ts, -Pb["contact_win_s"], Pb["contact_win_s"])
        cm_ = [_med(dd, t) for t in range(ca_, cb_ + 1)]
        m["contact_min_m"] = float(np.nanmin(cm_)) if np.any(np.isfinite(cm_)) else float("nan")
        # mastery r3 (SCR-M3-03): the off-ball contact is tighter than the on-ball one - offball_contact_m + contact_k x
        # sigma_d (judged SportVU used rows: every real one had D_u within 0.80 m of the screener; rows whose D_u never came
        # nearer than 0.9-1.2 m were 6 ambiguous and 1 not a screen - the defender went under or trailed wide)
        m["contact_thr_m"] = float(Pb["offball_contact_m"] + Pb["offball_contact_k"] * sig_sD)
        m["sigma_sD"] = float(sig_sD)
        contact_ok = bool(m["contact_min_m"] <= m["contact_thr_m"])
        # SCR-M3-04: the user passes the screener - the displacement of u relative to s over t_s +- offball_rel_win_s is
        # >= offball_rel_pass_m + offball_rel_k x sigma_d (two teammates jogging or stopping side by side never pass each other; a user cutting off
        # a screen at 2 m/s moves about 2.4 m relative to him)
        ra_, rb_ = _win(scene, ts, -Pb["offball_rel_win_s"], Pb["offball_rel_win_s"])
        ks2_ = scene.k(s)
        rel_ = np.array([ku.x[rb_] - ks2_.x[rb_] - (ku.x[ra_] - ks2_.x[ra_]),
                         ku.y[rb_] - ks2_.y[rb_] - (ku.y[ra_] - ks2_.y[ra_])])
        m["rel_pass_m"] = float(np.hypot(*rel_))
        rel_ok = not m["rel_pass_m"] < Pb["offball_rel_pass_m"] + Pb["offball_rel_k"] * sig_su
        geo = bool(geo and passed and (user_speed >= gate_speed or (upk >= gate_speed and inter["interaction"]
                                                                    and blocking))
                   and r_s >= Pb["offball_r_min_m"] and m["offense_ball"]
                   and (blocking or inter["interaction"] or user_speed >= Pb["offball_fast_use_mps"])
                   and m["guards_user"] and contact_ok and rel_ok)
    if on_ball:
        onb = _onball_decision(scene, s, u, D, st, ts, read, dsu_ca, sig_sD, sig_su, Pb, Pscr,
                               blocking=blocking, interacts=inter["interaction"], Pset=Pset)
        geo = onb["screen"]
    loose_rule = (None if st.loose is None else bool(st.loose)) if geo else False
    terms = [st.strict, dsu_ca <= Pscr["d_su_max_m"], user_speed >= gate_speed,
             inter["interaction"] and (dsD_ts <= Pscr["strict_contact_m"] or inter["deflect"] or inter["delay"])]
    strict_rule = False if any(t is False for t in terms) else (None if any(t is None for t in terms) else True)
    # ---- probabilities ----
    amb = Ptd["ambiguity_penalty"] if ambiguous else 1.0
    p_stat = st.p_loose if np.isfinite(st.p_loose) else 0.0
    p_set = p_stat * _pb(dsD_min, Pset["set_def_radius_m"], sig_sD) * amb
    p = p_stat * _pb(dsu_ca, Pscr["d_su_max_m"], sig_su) * _pb(dsD_ts, Pset["set_def_radius_m"], sig_sD) * amb
    if onb is not None:
        p = onb["p"] * amb  # SCR-M1-03: plant is a likelihood term (floored), contact and use are sigma-aware
    Pc = prm("screen_confidence")
    z = [(prm("screen_stationarity")["loose_v_mps"] - st.v_ls) / st.sigma, (Pscr["d_su_max_m"] - dsu_ca) / sig_su,
         (1.0 - dsD_ts) / sig_sD, float(inter["deflect"]), float(inter["delay"]),
         min(inter["sep_gain_m"], 1.5) if np.isfinite(inter["sep_gain_m"]) else 0.0, float(use)]
    logit = (Pc["b0"] + Pc["b1_z_stat"] * z[0] + Pc["b2_user_gate"] * z[1] + Pc["b3_def_gate"] * z[2]
             + Pc["b4_deflect"] * z[3] + Pc["b5_delay"] * z[4] + Pc["b6_sep_gain"] * z[5] + Pc["b7_use"] * z[6])
    # pre-switch (screen_target_defender): the defender nearest u just before t_s is the screener's defender
    psa, psb = _win(scene, ts, -0.5, 0)
    pre_switch = False
    if Ds is not None:
        pre_switch = bool(np.nanmean(_dist(scene, u, Ds)[psa:psb + 1]) < np.nanmean(_dist(scene, u, D)[psa:psb + 1]))
    m.update(
        P_s=(float(xs), float(ys)), r_s=r_s, m_s=_m_deg(xs, ys), court_region=_region(xs, ys), inbound=inbound,
        t_s_source="defender", t_s_uncertainty_s=half * DT, t_su_min=int(tc), tc=int(tc),
        d_sD_ts=dsD_ts, d_sD_min=dsD_min, contact_class=contact, d_su_ca=dsu_ca, sigma_d=sig_su,
        user_speed=user_speed, d_hat=d_hat, e_perp=e_perp, passed=passed, t_h=t_h, blocking=blocking,
        blocking_margin_m=bmargin, n=n, n_r=n_r, screen_angle_deg=angle, orientation_deg=orient,
        angle_class=angle_class, orientation_class=orient_class,
        orientation_source="xy", dir_class_generic=gen, dr_u=dr_u, dx_u=float(disp[0]), dy_u=float(disp[1]),
        u_start=u0, interaction=inter, away_use=away_use, read=read, approach_min_m=approach_min, exit=exit_cls, loose_rule_fired=loose_rule,
        strict_rule_fired=strict_rule, v_ls_mps=st.v_ls, sigma_win_mps=st.sigma, dwell_s=st.dwell,
        p_loose=st.p_loose, p_strict=st.p_strict, D_u_ambiguous=ambiguous, top2=top2, P_D_u=float(max(probs.values())),
        pre_switch=pre_switch, p_logit=float(1 / (1 + math.exp(-logit))), features=z, rescreen_count=0,
        rescreen_of=None, merged_into=None, source="contact" if st.synthetic else "stand",
        plant=_plant_class(st), **({} if onb is None else {k: onb[k] for k in ("contact_min_m", "d_sh_min_m",
                                                                                 "handler_peak_mps", "screener_mps",
                                                                                 "handler_disp_m")}))
    is_screen = geo
    kind = "handoff" if handoff else ("on_ball" if on_ball else "off_ball")
    return Rec(s, u, D, Ds, st, ts, kind, is_screen, p_set, p, m)


def _rolling_catch(scene, s, tc, Pb, h=None) -> bool:
    """SCR-M3-01: a pocket pass to the roller, not a handoff back to the screener (confirm r2: the reverse-handoff veto and
    the SET receive veto removed a true pocket pass, 10 -> 6 of 10 at sigma_p 0.05, 2 -> 0 at 0.2 / 0.3). The screener
    moves toward the rim at >= pocket_roll_mps (median radial speed over [catch - pocket_win_s / 2, catch + pocket_win_s])
    and, when the passer h is known, the pair separates into the catch (min 5-frame median d(s, h) over [catch -
    pocket_sep_win_s, catch - 0.15 s] <= d(s, h) at the catch - pocket_sep_m) while h still attacks the rim (median radial
    speed over [catch - pocket_win_s, catch] >= pocket_handler_vr_mps): the handler went past the screener and passed back
    to him. A handoff is exchanged at the pair's closest approach and the giver steps away (under noise the detected catch
    of a handoff lags by up to 0.35 s, when the pair has already separated)."""
    # radial speeds from smoothed positions over the window (the CA-RTS velocity of a manoeuvring player is unreliable on
    # precise tracks, see noise_driven_design)
    a, b = _win(scene, tc, -0.5 * Pb["pocket_win_s"], Pb["pocket_win_s"])
    ks = scene.k(s)
    vs = (math.hypot(ks.x[a], ks.y[a]) - math.hypot(ks.x[b], ks.y[b])) / max(DT, (b - a) * DT)
    if not vs >= Pb["pocket_roll_mps"]:
        return False
    if h is None:
        return True
    # the passer attacks the rim through the catch (a handoff giver steps out or away after the exchange)
    ha, hb = _win(scene, tc, -Pb["pocket_win_s"], 0)
    kh = scene.k(h)
    vh = (math.hypot(kh.x[ha], kh.y[ha]) - math.hypot(kh.x[hb], kh.y[hb])) / max(DT, (hb - ha) * DT)
    if not vh >= Pb["pocket_handler_vr_mps"]:
        return False
    dsh = _dist(scene, s, h)
    pa, pb = _win(scene, tc, -Pb["pocket_sep_win_s"], -0.15)
    pre = [_med(dsh, t) for t in range(pa, pb + 1)]
    return bool(np.any(np.isfinite(pre)) and np.nanmin(pre) <= _med(dsh, tc) - Pb["pocket_sep_m"])


def _gives_to(scene, a, b, ts, Pb):
    """SCR-M2-04: a hands the ball to b within [t_s - 0.3, t_s + handoff_rev_post_s] at close range (a transfer with d_ab <=
    handoff_d_m and air <= handoff_air_s, or a possession change a -> b with the pair within handoff_d_m). Returns the
    catch frame, or None."""
    x0, x1 = _win(scene, ts, -0.3, Pb["handoff_rev_post_s"])
    xs = _transfers(scene)
    keep = frames(Pb["handoff_keep_s"])
    for x in xs:
        if (x["frm"] == a and x["to"] == b and x0 <= x["catch"] <= x1 and x["d_ab"] <= Pb["handoff_d_m"]
                and x["air_s"] <= Pb["handoff_air_s"] + 1e-9
                and not any(y["frm"] == b and y["to"] == a and x["catch"] < y["catch"] <= x["catch"] + keep for y in xs)):
            return int(x["catch"])  # (a ball that comes straight back to a within handoff_keep_s is a possession flip)
    ps_ = _poss(scene)
    for t in range(max(x0, 1), x1 + 1):
        if ps_[t] == b and ps_[t - 1] != b:
            k = t - 1
            while k >= max(0, t - frames(Pb["handoff_air_s"])) and ps_[k] is None:
                k -= 1
            if k >= 0 and ps_[k] == a:
                # b keeps the ball (a noise flip of the possession between two players at a screen lasts a few frames)
                hb = ps_[t:_cl(scene, t + frames(Pb["handoff_keep_s"])) + 1]
                if np.mean([x == b for x in hb]) < 0.8 or any(x == a for x in hb):
                    continue
                ca_, cb_ = _cl(scene, k - 3), _cl(scene, t + 3)
                if np.nanmin(_dist(scene, a, b)[ca_:cb_ + 1]) <= Pb["handoff_d_m"]:
                    return int(t)
    return None


def _offense_has_ball(scene, ts, Pb):
    """SCR-M2-07: an attacker owns the ball (noise-robust possession) on >= offball_poss_frac of [t_s - offball_poss_pre_s,
    t_s + offball_poss_post_s]: box-outs and rebound scrums after a shot are not off-ball screens."""
    a, b = _win(scene, ts, -Pb["offball_poss_pre_s"], Pb["offball_poss_post_s"])
    ps_ = _poss(scene)[a:b + 1]
    braw = getattr(scene, "ball_raw", None)
    obs = (np.mean(np.isfinite(np.asarray(braw[0], dtype=float)[a:b + 1])) if braw is not None
           else (np.mean(np.isfinite(scene.ball.x[a:b + 1])) if scene.ball is not None else 0.0))
    if not obs >= Pb["offball_ball_obs_min"]:
        # SCR-M3-05: the tracker lost the ball (production dropout) - no evidence either way; the caller then accepts only
        # a user who leaves the rim (confirm r2: a down screen with the ball missing went 8 -> 0 of 10 at every sigma_p,
        # while a box-out crash with the ball lost after the shot must stay out)
        return None
    return bool(np.mean([x is not None for x in ps_]) >= Pb["offball_poss_frac"]) if len(ps_) else False


def _plant_class(st: Stop) -> str:
    """Screener plant as an attribute (SCR-M1-02): strict / loose / moving from the window LS speed and the dwell."""
    P = prm("screen_stationarity")
    if not np.isfinite(st.v_ls):
        return "unknown"
    if st.v_ls <= P["strict_v_mps"] and st.dwell >= P["strict_dwell_s"] - 1e-9 and not st.synthetic:
        return "strict"
    return "loose" if st.v_ls <= P["loose_v_mps"] else "moving"


def _onball_decision(scene, s, h, D, st, ts, read, dsu_ca, sig_sD, sig_su, Pb, Pscr, blocking=True, interacts=True,
                     Pset=None) -> dict:
    """On-ball screen decision (SCR-M1-03, ball_screen_model): a probabilistic score instead of the off-ball centre gate.

    screen = CONTACT on D_h (min 5-frame median d(s, D_h) within +-contact_win_s of t_s <= contact_on_m + contact_k x
    sigma_d: 1.2 m on precise tracks, about 1.5 m at sigma_p 0.3) AND d(s, h) <= near_m somewhere in t_s +- contact_win_s
    AND the handler holds the ball (possession on >= hold_frac of [t_s - 0.5, t_s + 0.3]) AND he moves (peak 5-frame
    median speed over [t_s - 0.5, t_s + handler_post_s] >= screen.user_speed_on_mps) AND he uses it (read use / snake /
    split, or a retreat with the old centre gate) AND the screener is not running through (5-frame median speed at the
    contact <= screener_max_mps; rolling and brush screens run 0.6-1.5 m/s). The plant enters p as max(p_loose,
    plant_floor), so a rolling screener is a lower-confidence screen, not a missing one.
    A contact candidate (synthetic stop: the screener never stood) needs more evidence that he screened rather than ran
    by: his speed at the contact <= moving_screener_max_mps, the blocking test, and an interaction with D_h (contact,
    deflection, delay or separation gain) or a close contact (<= screen_set.contact_likely_m + contact_k x sigma_d / 2).
    On the judged SportVU sample the moving rows without these were drives with a big running alongside, pass-and-cut
    traffic and drifts past a trailing defender."""
    ca, cb = _win(scene, ts, -Pb["contact_win_s"], Pb["contact_win_s"])
    dd = _dist(scene, s, D)
    cm = [_med(dd, t) for t in range(ca, cb + 1)]
    cmin = float(np.nanmin(cm)) if np.any(np.isfinite(cm)) else float("nan")
    c_on = Pb["contact_on_m"] + Pb["contact_k"] * sig_sD
    dsh_seg = _dist(scene, s, h)[ca:cb + 1]
    dsh = float(np.nanmin(dsh_seg)) if np.any(np.isfinite(dsh_seg)) else float("nan")
    sp = _kv(scene, h)["speed"]
    ha, hb = _win(scene, ts, -0.5, Pb["handler_post_s"])
    hv = [_med(sp, t) for t in range(ha, hb + 1)]
    hpk = float(np.nanmax(hv)) if np.any(np.isfinite(hv)) else float("nan")
    # screener speed at the contact (mastery r2, SCR-M2-05): the median of the 5-frame median speed over t_s +-
    # screener_win_s, not the single value at t_s - a 0.15 s track jump of the screener read 4.5 m/s at t_s and removed a
    # planted screen (confirm r1: 10 -> 0 of 10 at sigma_p 0.05); runners through the ball keep their speed over the window
    ssp = _kv(scene, s)["speed"]
    wa_, wb_ = _win(scene, ts, -Pb["screener_win_s"], Pb["screener_win_s"])
    sv_ = [_med(ssp, t) for t in range(wa_, wb_ + 1)]
    s_sp = float(np.nanmedian(sv_)) if np.any(np.isfinite(sv_)) else float("nan")
    if not st.synthetic and st.b >= ca and st.a <= cb and np.isfinite(st.v_ls):
        # a stand row whose stand overlaps the contact window: the screener stood at the contact, so his speed is the
        # stand's window speed (judged J34: planted 0.5 s before the handler's closest approach, rolling at 2.6 m/s by it)
        s_sp = min(s_sp, st.v_ls) if np.isfinite(s_sp) else st.v_ls
    pa, pb = _win(scene, ts, -0.5, 0.3)
    hold = _poss_holds(scene, h, pa, pb) >= Pb["hold_frac"] * (pb - pa + 1)
    used = read in ("use", "snake", "split") or (read == "retreat" and dsu_ca <= Pscr["d_su_max_m"])
    # the handler travels through the screen (SCR-M2-03): his largest displacement from h(t_s - 0.5) over [t_s - 0.5,
    # t_s + use_disp_post_s] >= use_disp_m (judged SportVU rows of a handler who dribbles in place next to the screener,
    # stops at him or receives and stands were not screens); smoothed positions, so the test keeps its meaning at sigma_p 0.5;
    # a retreat read needs retreat_travel_m (SCR-M3-06: at sigma_p 0.5 a handler standing beside the screener near the rim
    # read a retreat from the velocity noise and kept a stand on the screener's own defender)
    ka_, kb_ = _win(scene, ts, -0.5, Pb["use_disp_post_s"])
    kh_ = scene.k(h)
    dd_ = np.hypot(kh_.x[ka_:kb_ + 1] - kh_.x[ka_], kh_.y[ka_:kb_ + 1] - kh_.y[ka_])
    hdisp = float(np.nanmax(dd_)) if np.any(np.isfinite(dd_)) else float("nan")
    screen = bool(np.isfinite(cmin) and cmin <= c_on and dsh <= Pb["near_m"] and hold and used
                  and hpk >= Pscr["user_speed_on_mps"] and not s_sp > Pb["screener_max_mps"]
                  and ((read == "retreat" and not hdisp < Pb["retreat_travel_m"]) or not hdisp < Pb["use_disp_m"]))
    if screen and st.synthetic:
        close = cmin <= (Pset or prm("screen_set"))["contact_likely_m"] + 0.5 * Pb["contact_k"] * sig_sD
        # a screener moving between moving_screener_max_mps and screener_max_mps through the contact (a brush screen at
        # 2.0-2.5 m/s) is kept only with a close contact and a close use (SCR-M2-02; judged SportVU rows: 4 real, 1
        # ambiguous with both; 3 ambiguous without)
        fast_ok = bool(close and dsu_ca <= Pscr["d_su_max_m"])
        screen = bool((not s_sp > Pb["moving_screener_max_mps"] or fast_ok) and blocking and (interacts or close))
    p_plant = max(st.p_loose if np.isfinite(st.p_loose) else 0.0, Pb["plant_floor"])
    p = p_plant * _pb(cmin, c_on, sig_sD) * _pb(dsu_ca, Pb["use_near_m"], sig_su)
    return dict(screen=screen, p=p, contact_min_m=cmin, d_sh_min_m=dsh, handler_peak_mps=hpk, screener_mps=s_sp,
                handler_disp_m=hdisp)


def _interaction(scene, s, u, D, ts, dsD_ts, Ps, d_hat, Pi) -> dict:
    """screen_interaction tests: contact, deflect, delay, residual separation gain."""
    pa, pb = _win(scene, ts, -0.6, -0.1)
    qa, qb = _win(scene, ts, 0.1, 0.6)
    vpre, vpost = _mean_v(scene, D, pa, pb), _mean_v(scene, D, qa, qb)
    sp_pre, sp_post = float(np.hypot(*vpre)), float(np.hypot(*vpost))
    kD = scene.k(D)
    nc = prm("screen_stationarity")["vel_err_corr_frames"]
    sig_v = float(K_CAL * np.sqrt(np.nanmean(kD.var_v[pa:qb + 1])) * math.sqrt(nc / (nc + (pb - pa + 1))))
    dh = _ang(vpre, vpost)
    sig_h = math.degrees(sig_v / max(sp_pre, 1e-6)) * math.sqrt(2)
    deflect = bool(sp_pre >= Pi["deflect_min_speed_mps"] and np.isfinite(dh)
                   and dh >= max(Pi["deflect_deg"], Pi["deflect_sigma_k"] * sig_h))
    delay = bool(sp_pre > 0 and sp_post <= Pi["delay_ratio"] * sp_pre and sp_pre - sp_post >= Pi["delay_drop_mps"])
    sep = _dist(scene, u, D)
    s0, s1 = _win(scene, ts, -0.3, 0.7)
    sep_gain = _med(sep, s1) - _med(sep, s0)
    up_pre = float(np.hypot(*_mean_v(scene, u, pa, pb)))
    up_post = float(np.hypot(*_mean_v(scene, u, qa, qb)))
    resid = sep_gain - Pi["reaction_lag_s"] * max(0.0, up_post - up_pre)
    contact = bool(dsD_ts <= Pi["contact_m"])
    near = bool(dsD_ts <= Pi["radius_m"])
    interaction = near and (contact or deflect or delay or (np.isfinite(resid) and resid >= Pi["sep_gain_m"]))
    # continuous measures
    da, db = _win(scene, ts, 0, 2.0)
    ku = scene.k(u)
    lam_u = (ku.x[da:db + 1] - Ps[0]) * d_hat[0] + (ku.y[da:db + 1] - Ps[1]) * d_hat[1]
    near_s = _dist(scene, s, D)[da:db + 1] <= Pi["radius_m"]
    delay_s = float(np.sum(near_s & (lam_u > 0)) * DT)
    xa, xb = _win(scene, ts, -0.3, 0.7)
    path = float(np.nansum(np.hypot(np.diff(kD.x[xa:xb + 1]), np.diff(kD.y[xa:xb + 1]))))
    chord = float(math.hypot(kD.x[xb] - kD.x[xa], kD.y[xb] - kD.y[xa]))
    return dict(interaction=bool(interaction), contact=contact, deflect=deflect, deflect_deg=dh, delay=delay,
                delay_ratio=(sp_post / sp_pre) if sp_pre > 0 else float("nan"), speed_pre=sp_pre, speed_post=sp_post,
                sep_gain_m=sep_gain, residual_sep_gain_m=resid, defender_delay_s=delay_s, detour_m=path - chord)


def _merge(scene, recs) -> list:
    """De-duplicate (s, u, t_s) within dedupe_s; merge or split re-screens (screen_window)."""
    P = prm("screen_window")
    recs = sorted(recs, key=lambda r: (r.s, r.u, r.ts, -r.p))
    out = []
    for r in recs:
        prev = [q for q in out if q.s == r.s and q.u == r.u and q.m["merged_into"] is None]
        dup = [q for q in prev if abs(q.ts - r.ts) <= frames(P["dedupe_s"])]
        if dup:
            continue
        # SCR-M1-09: a used on-ball screen whose stand is cut in two by noise (the second stop starts within
        # fragment_gap_s of the first one's end, same spot within split_move_m) is one screen, not a re-screen
        if r.kind != "off_ball" and any(
                q.is_screen and q.kind == r.kind and 0 <= (r.stop.a - q.stop.b) * DT <= P["fragment_gap_s"]
                and math.hypot(*(np.array(r.m["P_s"]) - np.array(q.m["P_s"]))) <= P["split_move_m"] for q in prev):
            continue
        # a re-screen is linked by its t_s gap (<= window_s) or, beyond that, by the gap between the two stands
        # (<= rescreen_gap_s; REG-re_screen loop 2: a screener who steps off and comes back sets t_s 3.3 s apart)
        win = frames(P["window_s"])
        first = [q for q in prev if 0 < r.ts - q.ts and (r.ts - q.ts <= win or
                                                          0 < (r.stop.a - q.stop.b) * DT <= P["rescreen_gap_s"])]
        if first:
            q = first[-1]
            if r.ts - q.ts > win or _rescreen_split(scene, q, r, P):  # beyond window_s: a new stand, never merged
                r.m["rescreen_of"] = (q.s, q.u, q.ts)
            else:
                r.m["merged_into"] = (q.s, q.u, q.ts)
                q.m["rescreen_count"] += 1
        else:
            # SCR-M2-13: the pair's latest contact may be a row already merged into an earlier one (a reset of the same
            # screen); a used screen within window_s of that contact, from a new stand, is its re-screen
            late = [q for q in out if q.s == r.s and q.u == r.u and q.m["merged_into"] is not None
                    and 0 < r.ts - q.ts <= win and r.stop.a > q.stop.b]
            if late and r.is_screen and _rescreen_split(scene, late[-1], r, P):
                q = late[-1]
                r.m["rescreen_of"] = (q.s, q.u, q.ts)
        out.append(r)
    return out


def _rescreen_split(scene, q, r, P) -> bool:
    """True when the second screen is a new row: the screener relocated, the defender left, or the ball moved; or
    (loop 2) the first screen went unused / rejected and the second, from a new stand, is used (a merge would hide
    the use)."""
    if (q.m["read"] in ("unused", "reject") and r.m["read"] not in ("unused", "reject") and r.stop.a > q.stop.b):
        return True
    n3 = int(P["hyst_dwell_frames"])
    Ps = np.array(q.m["P_s"])
    ks = scene.k(q.s)
    run = 0
    for t in range(q.ts, r.ts + 1):
        run = run + 1 if math.hypot(ks.x[t] - Ps[0], ks.y[t] - Ps[1]) > P["split_move_m"] + P["hyst_m"] else 0
        if run >= n3:
            return True
    dd = _dist(scene, q.s, q.D)
    run = 0
    for t in range(q.ts, r.ts + 1):
        run = run + 1 if dd[t] > P["split_def_m"] + P["hyst_m"] else 0
        if run >= n3:
            return True
    return any(q.ts < x["catch"] <= r.ts for x in _transfers(scene))


def _screens(scene, kind=None) -> list:
    """Primary screen rows (is_screen, not merged), optionally of one kind."""
    return [r for r in _records(scene) if r.is_screen and r.m["merged_into"] is None
            and (kind is None or r.kind == kind)]


def _screen_attrs(r: Rec) -> dict:
    """The stored row of a screen (scalars only)."""
    m = r.m
    keep = ("P_s", "r_s", "court_region", "inbound", "t_s_source", "t_s_uncertainty_s", "t_su_min",
            "d_sD_ts", "d_sD_min", "contact_class", "d_su_ca", "user_speed", "passed", "t_h", "blocking",
            "n_r", "screen_angle_deg", "angle_class", "orientation_deg", "orientation_class", "orientation_source",
            "dir_class_generic", "dr_u",
            "read", "exit", "loose_rule_fired", "strict_rule_fired", "v_ls_mps", "sigma_win_mps", "dwell_s",
            "p_loose", "p_strict", "D_u_ambiguous", "top2", "P_D_u", "pre_switch", "p_logit", "rescreen_count",
            "rescreen_of", "source", "plant")
    a = {k: m[k] for k in keep}
    a.update({k: m[k] for k in ("contact_min_m", "d_sh_min_m", "handler_peak_mps", "screener_mps", "handler_disp_m",
                                "pass_and_screen", "screener_came", "rel_pass_m", "contact_thr_m", "sigma_sD") if k in m})
    a.update(kind=r.kind, screener_defender=r.Ds, interaction=m["interaction"]["interaction"],
             strict=m["strict_rule_fired"], loose=m["loose_rule_fired"])
    return a


def _actors(r: Rec, user_key="user", def_key="defender") -> dict:
    return {"screener": r.s, user_key: r.u, def_key: r.D}


def _scr_window(r: Rec):
    return min(r.stop.a, r.ts), max(r.stop.b, r.ts, r.m["tc"])


# --------------------------------------------------------------------------------------
# Screener post-action, ball-screen location, coverage
# --------------------------------------------------------------------------------------
def _post_action(scene, s, ts, t_h, Ps, h=None) -> dict:
    """screener_post_action: roll > short_roll > pop_arc > pop_mid (first match), else None."""
    P = prm("screener_post_action")
    r = _kv(scene, s)["r"]
    vr = _kv(scene, s)["vr"]
    nv, ns = frames(P["roll_vr_window_s"]), int(P["stand_frames"])
    r_ps = float(np.hypot(*Ps))
    t_h = ts if t_h is None else t_h
    wa, wb = _win(scene, ts, 0, P["roll_window_s"])
    min_r = float(np.nanmin(r[wa:wb + 1]))
    roll_start = None
    for t0 in range(t_h, _win(scene, t_h, 0, P["roll_start_s"])[1] + 1):
        if t0 + nv < scene.n and np.nanmean(vr[t0:t0 + nv]) >= P["roll_vr_mps"]:
            roll_start = t0
            break
    da, db = _win(scene, ts, 0, 1.5)
    out = dict(action=None, min_r=min_r, deep_roll=bool(np.nanmin(r[da:db + 1]) <= P["deep_r_m"]),
               roll_ctg=bool(min_r <= P["roll_ctg_r_m"]), t_start=roll_start)
    if roll_start is not None and min_r <= P["roll_r_m"] and min_r - r_ps <= -P["roll_dr_m"]:
        out["action"] = "roll"
        return out
    ks = scene.k(s)
    if min_r - r_ps <= -P["short_dr_m"]:
        for t in range(wa, wb + 1):
            if _in("short_roll_zone", ks.x[t], ks.y[t]) and (_stand_run(scene, s, t, min(wb, t + ns))
                                                              or _holder(scene)[t] == s):
                out["action"] = "short_roll"
                return out
    disp = np.hypot(ks.x[wa:wb + 1] - Ps[0], ks.y[wa:wb + 1] - Ps[1])
    in_arc = [t for t in range(wa, wb + 1) if _in("pop_arc_zone", ks.x[t], ks.y[t])]
    if (in_arc and np.nanmax(disp) >= P["pop_move_m"] and min_r >= P["pop_min_r_m"]
            and r[wb] >= r_ps - 1e-9):
        out["action"] = "pop_arc"
        return out
    if np.nanmax(disp) >= P["pop_move_m"] and r[wb] > r_ps:
        for t in range(wa, wb + 1):
            if P["pop_mid_r_lo_m"] <= r[t] < P["pop_mid_r_hi_m"] and _stand_run(scene, s, t, min(wb, t + ns)):
                out["action"] = "pop_mid"
                return out
    return out


def _location(scene, r: Rec) -> dict:
    """Ball-screen location (named_spots pnr_location) and direction, both at the handler's set-up, and empty side."""
    td = _t_dir(scene, r)
    hp = _pos(scene, r.u, td)  # the handler's set-up position, as for direction (SCR-T17)
    xs, ys = r.m["P_s"]
    loc = _pnr_location(*hp)
    if loc == "pnr_location_logo":
        # REG-location (loop 2): the side and direction come from the set-up, the depth from the screen. A handler
        # waiting at r 9 m for a screen set at r 7.5 m is a high (or side / slot) ball screen; logo only when the
        # screen itself is set at logo depth
        loc_s = _pnr_location(xs, ys)
        if loc_s is not None and loc_s != "pnr_location_logo":
            loc = loc_s
    direction = _dir_label(scene, r.s, r.u, td)
    ex = prm("ball_screen")["empty_side_x_m"]
    mates = [o for o in scene.offense if o not in (r.s, r.u)]
    empty = not any(np.sign(_pos(scene, o, r.ts)[0]) == np.sign(xs) and abs(_pos(scene, o, r.ts)[0]) > ex
                    for o in mates)
    return dict(location=loc.rsplit("_", 1)[0].replace("pnr_location_", "") if loc and loc.endswith(("_right", "_left"))
                else (loc.replace("pnr_location_", "") if loc else None),
                location_label=loc, handler_region=_region(*hp), direction=direction, empty_side=bool(empty))


def _switch(scene, D1, o1, D2, o2, ts, P) -> dict:
    """Reciprocal matchup exchange D1 -> o1, D2 -> o2 after t_s; 'normal' / 'late' / None."""
    lim = _win(scene, ts, 0, P["late_switch_s"])[1]
    hold = frames(P["switch_hold_s"])
    w = P["switch_window_s"]
    for t in range(ts, lim + 1, 3):
        g1, p1 = _guard_of(scene, D1, t, w)
        g2, p2 = _guard_of(scene, D2, t, w) if D2 is not None else (o2, 1.0)
        if g1 == o1 and g2 == o2 and p1 >= P["switch_p"] and p2 >= P["switch_p"]:
            ok = all(_guard_of(scene, D1, _cl(scene, t2), w)[0] == o1 for t2 in range(t, t + hold + 1, 5))
            if ok:
                held2 = all(_guard_of(scene, D1, _cl(scene, t2), w)[0] == o1 for t2 in range(t, t + frames(2.0) + 1, 5))
                return dict(switch="normal" if t <= ts + frames(1.0) else "late", t_switch=int(t), switch_held_2s=held2)
    return dict(switch="none", t_switch=None, switch_held_2s=False)


def _coverage_on(scene, r: Rec) -> dict:
    """ball_screen_coverage for one on-ball screen row."""
    P = prm("ball_screen_coverage")
    h, s, Dh, Ds, ts = r.u, r.s, r.D, r.Ds, r.ts
    Ps = np.array(r.m["P_s"])
    d_hat, e_perp = r.m["d_hat"], r.m["e_perp"]
    sig = r.m["sigma_d"]
    out = dict(route="none", route_margin_m=float("nan"), route_unresolved=False)
    # ---- route of D_h at its crossing of the screen line ----
    t_h = r.m["t_h"]
    if t_h is not None:
        side = np.sign((_pos(scene, h, t_h) - Ps) @ e_perp) or 1.0
        a, b = _win(scene, ts, -0.3, P["route_post_s"])
        tx = None
        for t in range(a, b + 1):
            if (_pos(scene, Dh, t) - Ps) @ d_hat >= prm("screen_frame")["pass_margin_m"]:
                tx = t
                break
        if tx is not None:
            wD = float((_pos(scene, Dh, tx) - Ps) @ e_perp * side)
            wS = float((_pos(scene, Ds, tx) - Ps) @ e_perp * side) if Ds is not None else None
            if wD > 0:
                route, margin = "over", wD
            elif wS is not None and wS < 0 and wD > wS:
                route, margin = "through", min(-wD, wD - wS)
            else:
                route, margin = "under", (-wD if wS is None or wS >= 0 else min(-wD, wS - wD))
            out.update(route=route, route_margin_m=float(margin), route_unresolved=bool(abs(margin) < sig), t_cross=tx)
    # ---- ice: D_h between the handler and P_s before t_s, handler rejects ----
    if r.m["read"] == "reject":
        a, b = _win(scene, ts, -1.0, 0)
        n_ice = 0
        for t in range(a, b + 1):
            dseg, uu = _seg_proj(_pos(scene, Dh, t), _pos(scene, h, t), Ps)
            if 0.1 < uu < 0.9 and dseg <= P["ice_lateral_m"]:
                n_ice += 1
        if n_ice * DT >= P["ice_s"]:
            out.update(route="ice", route_margin_m=float("nan"), route_unresolved=False)
    # ---- screener's defender depth (named_spots pnr_big_*) ----
    big, depth = None, float("nan")
    if Ds is not None:
        t2 = _win(scene, ts, 0, P["depth_delay_s"])[1]
        xd, yd = _pos(scene, Ds, t2)
        sx, sy = _pos(scene, s, t2)
        hx, hy = _pos(scene, h, t2)
        depth = float(((xd - sx) * (-sx) + (yd - sy) * (-sy)) / max(1e-9, math.hypot(sx, sy)))
        labs = [i for i in PNR_BIG_ORDER if _in(i, xd, yd, ax_=float(sx), ay_=float(sy), hx=float(hx), hy=float(hy))]
        near_h = math.hypot(xd - hx, yd - hy) <= P["near_h_m"]
        ba, bb = _win(scene, ts, 0, P["blitz_window_s"])
        dh_near = float(np.sum(_dist(scene, Dh, h)[ba:bb + 1] <= P["near_h_m"]) * DT)
        if "pnr_big_blitz" in labs and dh_near >= P["blitz_dh_s"]:
            big = "blitz"
        elif near_h and _med(_kv(scene, Ds)["speed"], t2) >= P["contain_speed_mps"] and _dist(scene, Dh, h)[t2] > P["near_h_m"]:
            big = "contain"
        else:
            rest = [i for i in labs if i != "pnr_big_blitz"]
            if rest:
                big = rest[0].replace("pnr_big_", "")
            elif math.hypot(sx - hx, sy - hy) > P["screener_far_m"]:
                big = "screener_far"
            elif depth >= P["deep_drop_high_m"]:
                big = "deep_drop_high"
    out.update(big=big, drop_depth_m=depth)
    out.update(_switch(scene, Dh, s, Ds, h, ts, P) if Ds is not None else dict(switch="none", t_switch=None,
                                                                                switch_held_2s=False))
    order = ["switch", "blitz", "ice", "hedge", "contain", "at_level", "high_drop", "deep_drop", "deep_drop_high"]
    cands = (["switch"] if out["switch"] != "none" else []) + ([big] if big else []) + (
        ["ice"] if out["route"] == "ice" else [])
    valid = [c for c in cands if c in order]  # 'screener_far' has no coarse class (SCR-T01: it crashed order.index)
    out["coverage_coarse"] = min(valid, key=order.index) if valid else "none"
    ctg_cov = {"blitz": "blitz", "hedge": "hedge", "contain": "contain", "at_level": "drop_contest", "high_drop": "drop",
               "deep_drop": "drop", "deep_drop_high": "drop", "screener_far": "none", None: "none"}
    out["ctg_route"] = {"over": "over", "under": "under", "through": "under", "ice": "ice"}.get(out["route"], "none")
    out["ctg_coverage"] = "switch" if out["switch"] != "none" else ctg_cov.get(big, "none")
    return out


def _coverage_off(scene, r: Rec) -> dict:
    """off_ball_screen_coverage for one off-ball screen row (first match)."""
    P, Pb = prm("off_ball_screen_coverage"), prm("ball_screen_coverage")
    u, s, D, Ds, ts = r.u, r.s, r.D, r.Ds, r.ts
    Ps = np.array(r.m["P_s"])
    d_hat, e_perp = r.m["d_hat"], r.m["e_perp"]
    if Ds is not None:
        lim = _win(scene, ts, 0, P["switch_within_s"])[1]
        sw = _switch(scene, D, s, Ds, u, ts, dict(Pb, late_switch_s=P["switch_within_s"]))
        if sw["switch"] != "none" and sw["t_switch"] <= lim:
            return dict(offball_coverage="switch", **sw)
    if r.m["pre_switch"]:
        return dict(offball_coverage="pre_switch")
    t5 = _win(scene, ts, -0.5, 0)[0]
    bp = _pos(scene, "ball", t5)
    if _fin(*bp) and r.m["read"] in ("reject", "unused"):
        dseg, uu = _seg_proj(_pos(scene, D, t5), _pos(scene, u, t5), bp)
        if dseg <= P["toplock_m"] and 0.05 <= uu <= 0.6:
            return dict(offball_coverage="top_lock", margin_m=dseg)
    a, b = _win(scene, ts, -0.3, 1.0)
    tx = next((t for t in range(a, b + 1) if (_pos(scene, D, t) - Ps) @ d_hat >= 0), None)
    if tx is not None:
        rD = _r_at(scene, D, tx)
        side = np.sign((_pos(scene, u, r.m["t_h"] if r.m["t_h"] is not None else ts) - Ps) @ e_perp) or 1.0
        wD = float((_pos(scene, D, tx) - Ps) @ e_perp * side)
        if rD < r.m["r_s"] - P["under_margin_m"] and wD < 0:
            tgt = _pos(scene, u, _win(scene, ts, 0, 1.0)[1])
            dD = np.hypot(scene.k(D).x - tgt[0], scene.k(D).y - tgt[1])
            dU = np.hypot(scene.k(u).x - tgt[0], scene.k(u).y - tgt[1])
            tD = next((t for t in range(tx, scene.n) if dD[t] <= 1.0), None)
            tU = next((t for t in range(ts, scene.n) if dU[t] <= 1.0), None)
            if tD is not None and tU is not None and (tD - tU) * DT <= P["under_lag_s"]:
                return dict(offball_coverage="under", margin_m=-wD)
        ca, cb = _win(scene, ts, -0.3, 0.7)
        if np.nanmean(_dist(scene, D, u)[ca:cb + 1]) <= P["chase_m"] and wD >= 0:
            return dict(offball_coverage="chase", margin_m=wD)
    if Ds is not None:
        # bump: D_s steps toward u's path (its displacement along d_hat-normal toward the user side) and comes back
        ba, bb = _win(scene, ts, 0, 0.5)
        p0 = _pos(scene, Ds, ts)
        step = max(abs(float((_pos(scene, Ds, t) - p0) @ e_perp)) for t in range(ba, bb + 1))
        back = float(np.hypot(*(_pos(scene, Ds, _win(scene, ts, 0, 1.5)[1]) - p0)))
        if step >= P["bump_m"] and back < step:
            return dict(offball_coverage="bump", margin_m=step)
    return dict(offball_coverage="none")


# --------------------------------------------------------------------------------------
# Detectors: primitives
# --------------------------------------------------------------------------------------
def detect_screen_set(scene, **params) -> list:
    """screen_set: one event per SET row (used, rejected or unused); t0 = stop onset."""
    out = []
    for r in _records(scene, set_over=params):
        if r.m["merged_into"] is not None:
            continue
        sa, sb = r.m.get("set_stop") or (r.stop.a, r.stop.b)  # SCR-M3-08: a contact row keeps the replaced stand
        a, b = sa, max(sb, r.ts)
        e = _event(scene, "screen_set", {"screener": r.s, "user": r.u, "defender": r.D}, sa, a, b, r.p_set,
                   dict(stop=(sa, sb), dwell_s=r.stop.dwell, v_ls_mps=r.stop.v_ls,
                        strict=r.stop.strict, loose=r.stop.loose, contact_distance_m=r.m["d_sD_ts"],
                        contact_class=r.m["contact_class"], court_region=r.m["court_region"], t_s=r.ts,
                        own_man=False, D_u_ambiguous=r.m["D_u_ambiguous"]))
        if e:
            out.append(e)
    return out


def detect_screen(scene, **params) -> list:
    """screen (R-ST-17): canonical screens with strict and loose flags; t0 = t_s."""
    out = []
    for r in _records(scene, screen_over=params):
        if not (r.is_screen and r.m["merged_into"] is None):
            continue
        a, b = _scr_window(r)
        e = _event(scene, "screen", _actors(r), r.ts, a, b, r.p, _screen_attrs(r))
        if e:
            out.append(e)
    return out


def detect_screen_moment(scene, **params) -> list:
    """screen_moment: t_s of every screen with its uncertainty and source."""
    out = []
    for r in _screens(scene):
        a, b = _scr_window(r)
        e = _event(scene, "screen_moment", _actors(r), r.ts, a, b, r.p,
                   dict(screen_moment_frame=r.ts, t_s_source=r.m["t_s_source"],
                        t_s_uncertainty_s=r.m["t_s_uncertainty_s"], d_sD_min=r.m["d_sD_min"],
                        t_su_min=r.m["t_su_min"]))
        if e:
            out.append(e)
    return out


def detect_screen_read(scene, **params) -> list:
    """screen_read: use / reject / unused / snake / split / retreat for every SET row."""
    P = prm("screen_read", params)
    out = []
    for r in _records(scene):
        if r.m["merged_into"] is not None:
            continue
        read = r.m["read"]
        sig = r.m["sigma_d"]
        if read in ("use", "snake", "split"):
            p = r.p
        elif read == "reject":
            p = r.p_set * _pa(r.m["d_su_ca"], prm("screen")["d_su_max_m"], sig)
        elif read == "retreat":
            p = r.p_set
        else:
            ra, rb = _win(scene, r.ts, 0, P["unused_s"])
            dmin = float(np.nanmin(_dist(scene, r.s, r.u)[ra:rb + 1]))
            p = r.p_set * _pa(dmin, prm("screen")["d_su_max_m"], sig)
        a, b = _scr_window(r)
        e = _event(scene, "screen_read", _actors(r), r.ts, a, b, p,
                   dict(read=read, d_su_ca=r.m["d_su_ca"], t_h=r.m["t_h"], user_speed=r.m["user_speed"],
                        exit=r.m["exit"], kind=r.kind))
        if e:
            out.append(e)
    return out


def detect_screen_interaction(scene, **params) -> list:
    """screen_interaction: screens whose target defender was contacted, deflected, delayed or lost separation."""
    P = prm("screen_interaction", params)
    out = []
    for r in _screens(scene):
        it = r.m["interaction"]
        if not it["interaction"]:
            continue
        p = r.p * _pb(r.m["d_sD_ts"], P["radius_m"], r.m["sigma_d"])
        a, b = _scr_window(r)
        e = _event(scene, "screen_interaction", {"defender": r.D, "screener": r.s, "user": r.u}, r.ts, a, b, p,
                   dict(it, contact_class=r.m["contact_class"]))
        if e:
            out.append(e)
    return out


def detect_screener_post_action(scene, **params) -> list:
    """screener_post_action: roll / short roll / pop after on-ball screens and DHOs; t0 = t_h."""
    out = []
    for r in _screens(scene, "on_ball"):
        pa = _post_action(scene, r.s, r.ts, r.m["t_h"], r.m["P_s"], r.u)
        if pa["action"] is None:
            continue
        t0 = r.m["t_h"] if r.m["t_h"] is not None else r.ts
        b = _win(scene, r.ts, 0, prm("screener_post_action")["roll_window_s"])[1]
        sp = _sig_pos(scene, r.s, t0)
        extra = (_pb(pa["min_r"], prm("screener_post_action")["roll_r_m"], sp) if pa["action"] == "roll"
                 else _pa(_kv(scene, r.s)["r"][b], prm("screener_post_action")["pop_arc_r_m"], sp)
                 if pa["action"] == "pop_arc" else 1.0)
        e = _event(scene, "screener_post_action", {"screener": r.s, "user": r.u}, t0, r.ts, b, r.p * extra,
                   dict(pa, source="ball_screen"))
        if e:
            out.append(e)
    return out


# --------------------------------------------------------------------------------------
# Detectors: ball screens
# --------------------------------------------------------------------------------------
def _ball_attrs(scene, r: Rec) -> dict:
    a = _screen_attrs(r)
    a.update(_location(scene, r))
    P = prm("ball_screen")
    ks = scene.k(r.s)
    t1 = _win(scene, r.stop.a, -1.0, 0)[0]
    sp = float(np.nanmean(_kv(scene, r.s)["speed"][t1:r.stop.a + 1]))
    a["pre_action"] = "sprint_up" if (sp > P["sprint_up_mps"] and ks.y[t1] < P["sprint_up_y_m"]) else "none"
    a["post_action"] = _post_action(scene, r.s, r.ts, r.m["t_h"], r.m["P_s"], r.u)["action"]
    a["coverage"] = _coverage_on(scene, r)["coverage_coarse"]
    return a


def detect_ball_screen(scene, **params) -> list:
    """ball_screen: on-ball screens with location, direction, empty side, pre/post action, read, coverage."""
    out = []
    for r in _screens(scene, "on_ball"):
        a, b = _scr_window(r)
        e = _event(scene, "ball_screen", _actors(r, "handler", "defender"), r.ts, a, b, r.p, _ball_attrs(scene, r))
        if e:
            out.append(e)
    return out


def detect_high_ball_screen(scene, **params) -> list:
    """high_ball_screen: ball screens with the handler in pnr_location_high at t_s."""
    P = prm("high_ball_screen", params)
    out = []
    for r in _screens(scene, "on_ball"):
        loc = _location(scene, r)
        if loc["location_label"] != "pnr_location_high":
            continue
        side = np.sign(_pos(scene, r.u, _win(scene, r.ts, 0, 1.0)[1])[0] - r.m["P_s"][0])
        tag = sum(1 for o in scene.offense if o not in (r.s, r.u)
                  and np.sign(_pos(scene, o, r.ts)[0]) == side and abs(_pos(scene, o, r.ts)[0]) > P["tag_x_m"])
        a, b = _scr_window(r)
        e = _event(scene, "high_ball_screen", _actors(r, "handler"), r.ts, a, b, r.p,
                   dict(_ball_attrs(scene, r), double_tag=tag >= 2))
        if e:
            out.append(e)
    return out


def detect_side_ball_screen(scene, **params) -> list:
    """side_ball_screen: ball screens with the handler in pnr_location_side_* at t_s; shake flag."""
    P = prm("side_ball_screen", params)
    out = []
    for r in _screens(scene, "on_ball"):
        loc = _location(scene, r)
        if not (loc["location_label"] or "").startswith("pnr_location_side"):
            continue
        hx = _pos(scene, r.u, r.ts)[0]
        sa, sb = _win(scene, r.ts, -0.5, 2.0)
        shake = False
        for o in scene.offense:
            if o in (r.s, r.u) or np.sign(_pos(scene, o, sa)[0]) != np.sign(hx):
                continue
            if _m_deg(*_pos(scene, o, sa)) <= 15.0:  # corner player (pnr_location_corner angle band)
                if np.nanmax(_kv(scene, o)["r"][sa:sb + 1]) - _r_at(scene, o, sa) >= P["shake_dr_m"] or \
                        _m_deg(*_pos(scene, o, sb)) - _m_deg(*_pos(scene, o, sa)) >= P["shake_dm_deg"]:
                    shake = True
        a, b = _scr_window(r)
        e = _event(scene, "side_ball_screen", _actors(r, "handler"), r.ts, a, b, r.p,
                   dict(_ball_attrs(scene, r), shake=shake))
        if e:
            out.append(e)
    return out


def detect_step_up_screen(scene, **params) -> list:
    """step_up_screen: screener arrives from below and screens toward the sideline for a wing/slot handler."""
    P = prm("step_up_screen", params)
    out = []
    for r in _screens(scene, "on_ball"):
        loc = _location(scene, r)["location_label"] or ""
        if not (loc.startswith("pnr_location_side") or loc.startswith("pnr_location_slot")):
            continue
        ks = scene.k(r.s)
        t1 = _win(scene, r.stop.a, -1.0, 0)[0]
        hy = _pos(scene, r.u, r.ts)[1]
        vy = float(np.nanmean(ks.vy[t1:_win(scene, r.stop.a, -0.1, 0)[0] + 1]))
        ea, eb = _win(scene, r.ts, 0, 1.0)
        hvy = float(np.nanmean(scene.k(r.u).vy[ea:eb + 1]))
        xs, ys = r.m["P_s"]
        td = _t_dir(scene, r)
        na = max(r.stop.a, _win(scene, td, -P["n_avg_s"], 0)[0])
        n_set = _unit(np.nanmean([_unit(_pos(scene, r.D, t) - _pos(scene, r.s, t)) for t in range(na, max(na, td) + 1)],
                                 axis=0))  # screen normal at the handler's set-up (window mean)
        # n_y is an attribute, not a gate (loop 1): D_h is above the screener only on wing step-ups; at the slot he is
        # beside him and n_y at d_sD ~0.9 m is noise-dominated (V0 slot_step_up: -0.81..0.0); 'from below' is the
        # below_m + approach_vy_mps test
        if not (ks.y[t1] <= hy - P["below_m"] and vy >= P["approach_vy_mps"]
                and hvy < 0 and _location(scene, r)["direction"] == "to_sideline"):
            continue
        a, b = _scr_window(r)
        e = _event(scene, "step_up_screen", _actors(r, "handler"), r.ts, a, b, r.p,
                   dict(_ball_attrs(scene, r), pre_action="step_up", delta_y_approach=float(ys - ks.y[t1]),
                        n_y_setup=float(n_set[1]),
                        screener_start_region=_region(ks.x[t1], ks.y[t1])))
        if e:
            out.append(e)
    return out


def _t_dir(scene, r: Rec) -> int:
    """Frame of the handler's set-up: the last frame before t_s (within dir_search_s) with speed < dir_setup_speed_mps,
    else t_s - dir_lead_s. Direction labels are read there (at t_s the handler is already turning the corner)."""
    P = prm("ball_screen")
    sp = _kv(scene, r.u)["speed"]
    lo = _win(scene, r.ts, -P["dir_search_s"], 0)[0]
    for t in range(r.ts, lo - 1, -1):
        if np.isfinite(sp[t]) and sp[t] < P["dir_setup_speed_mps"]:
            return t
    return _win(scene, r.ts, -P["dir_lead_s"], 0)[0]


def _dir_label(scene, s, h, t):
    sp, hp = _pos(scene, s, t), _pos(scene, h, t)
    if _in("ball_screen_to_middle", *sp, hx=float(hp[0]), hy=float(hp[1])):
        return "to_middle"
    if _in("ball_screen_to_sideline", *sp, hx=float(hp[0]), hy=float(hp[1])):
        return "to_sideline"
    return None


def detect_flip_screen(scene, **params) -> list:
    """flip_screen: the screener switches sides of the handler->rim line before contact."""
    P = prm("flip_screen", params)
    out = []
    for r in _screens(scene, "on_ball"):
        td = _t_dir(scene, r)
        a, b = _win(scene, r.stop.a, -P["window_s"], 0)[0], max(td, r.stop.a)
        hp = _pos(scene, r.u, td)  # handler -> rim line from the handler's set-up position
        nrm = _unit(np.array([-hp[1], hp[0]]))
        offs = np.array([float((_pos(scene, r.s, t) - hp) @ nrm) for t in range(a, b + 1)])
        if len(offs) < 10:
            continue
        offs = np.convolve(offs, np.ones(5) / 5, mode="same")
        lq = float(np.nanmean(offs[-5:]))
        dsh = _dist(scene, r.s, r.u)[a:b + 1]
        spd = _kv(scene, r.s)["speed"][a:b + 1]
        ok = [bool(np.sign(offs[i]) == -np.sign(lq) and abs(offs[i]) >= P["min_offset_m"] and dsh[i] <= P["max_sh_m"]
                   and spd[i] < P["show_speed_mps"]) for i in range(len(offs) - 5)]
        # a show on the first side: >= show_frames consecutive slow frames there (SCR-T09: a run-past is not a flip)
        runs, k = [], 0
        while k < len(ok):
            if ok[k]:
                j = k
                while j + 1 < len(ok) and ok[j + 1]:
                    j += 1
                if j - k + 1 >= P["show_frames"]:
                    runs.extend(range(k, j + 1))
                k = j + 1
            else:
                k += 1
        pre = runs
        if not pre or abs(lq) < P["min_offset_m"]:
            continue
        i_pre = max(pre, key=lambda i: abs(offs[i]))  # the screener's set-up on the first side
        lp = float(offs[i_pre])
        if abs(lp) < P["min_offset_m"]:
            continue
        t_pre = a + i_pre
        d0, d1 = _dir_label(scene, r.s, r.u, t_pre), _dir_label(scene, r.s, r.u, td)
        if d0 is None or d1 is None or d0 == d1:
            continue
        sp_ = _sig_pos(scene, r.s, r.ts) * prm("screen_noise_calibration")["dist_sigma_scale"]
        p = r.p * _pa(abs(lp), P["min_offset_m"], sp_) * _pa(abs(lq), P["min_offset_m"], sp_)
        e = _event(scene, "flip_screen", _actors(r, "handler"), r.ts, a, b, p,
                   dict(flip=True, offset_pre_m=lp, offset_post_m=lq, direction_pre=d0, direction_post=d1,
                        t_pre=int(t_pre)))
        if e:
            out.append(e)
    return out


def detect_re_screen(scene, **params) -> list:
    """re_screen: a second ball screen by the same screener for the same handler (split or merged)."""
    P = prm("re_screen", params)
    recs = [r for r in _records(scene) if r.kind == "on_ball"]
    out = []
    for r in recs:
        ref = r.m["rescreen_of"] or r.m["merged_into"]
        if not r.is_screen:
            continue
        if ref is None:
            continue
        q = next((x for x in recs if (x.s, x.u, x.ts) == ref), None)
        if q is None:
            continue
        d1, d2 = _location(scene, q)["direction"], _location(scene, r)["direction"]
        trig = "reject" if q.m["read"] == "reject" else (
            "under" if _coverage_on(scene, q)["route"] == "under" else None)
        twist = [x.s for x in _screens(scene, "on_ball") if x.u == r.u and x.s != r.s
                 and abs(x.ts - r.ts) <= frames(P["twist_s"]) and _location(scene, x)["direction"] not in (None, d2)]
        a, b = _scr_window(r)
        e = _event(scene, "re_screen", _actors(r, "handler"), r.ts, a, b, r.p,
                   dict(rescreen_of=ref, merged=r.m["merged_into"] is not None,
                        rescreen_side=("opposite" if (d1 and d2 and d1 != d2) else "same"), trigger=trig,
                        twist_with=twist, dt_s=(r.ts - q.ts) * DT))
        if e:
            out.append(e)
    return out


def _approaches(scene) -> list:
    """Screener approaches to the ball handler without a full screen (slip / ghost / fake candidates)."""
    c = _cache(scene)
    if "approach" in c:
        return c["approach"]
    P, Pst = prm("slip_screen"), prm("screen_stationarity")
    out = []
    for h, a0, b0 in _segments(scene):
        if h not in scene.offense:
            continue
        Dh, _ = _defender_of(scene, h, a0)
        for s in scene.offense:
            if s == h:
                continue
            dsh = _dist(scene, s, h)
            dsd = _dist(scene, s, Dh) if Dh is not None else dsh
            last = -10**9
            for t in range(max(a0, frames(1.0)), min(b0, scene.n - 2) + 1):
                v = dsd[t]
                if not np.isfinite(v) or v != np.nanmin(dsd[max(a0, t - 6):t + 7]):
                    continue
                if not (dsh[t] <= P["approach_h_m"] or (Dh is not None and v <= P["approach_d_m"])):
                    continue
                if t - last < frames(1.0):
                    continue
                pa, pb = _win(scene, t, -1.0, -0.1)
                ks = scene.k(s)
                toward = np.nanmean([(ks.vx[k] * (scene.k(h).x[k] - ks.x[k]) + ks.vy[k] * (scene.k(h).y[k] - ks.y[k]))
                                     / max(1e-6, dsh[k]) for k in range(pa, pb + 1)])
                if not toward >= P["approach_speed_mps"]:
                    continue
                vh = _mean_v(scene, h, *_win(scene, t, -0.6, -0.1))
                if np.hypot(*vh) >= 1.0 and _ang(vh, _pos(scene, s, t) - _pos(scene, h, t)) <= 30.0:
                    continue  # the holder is bringing the ball to s: handoff approach
                near = _stops_near(scene, s, *_win(scene, t, -0.5, 0.5))
                if any(st.dwell >= Pst["strict_dwell_s"] - 1e-9 for st in near):
                    continue  # a full SET: handled by the screen engine
                # movement right after s's own full stand or screen for h is its post-action, not a new approach (SCR-T11)
                if any(st.dwell >= Pst["strict_dwell_s"] - 1e-9 and t - frames(P["after_stop_s"]) <= st.b <= t
                       for st in _stops(scene, s)):
                    continue
                if any(r.s == s and r.u == h and t - frames(P["after_screen_s"]) <= r.ts <= t for r in _screens(scene)):
                    continue
                ra, rb = _win(scene, t, -0.5, 1.0)
                if _holds(scene, s, ra, rb) >= 5:
                    continue  # s receives the ball (handoff / pass)
                if any(fc["a"] == h and fc["b"] == s and abs(fc["t_c"] - t) <= frames(1.0) for fc in _fake_candidates(scene)):
                    continue  # the holder brings the ball to s: a (fake) handoff, not a screen action
                last = t
                out.append(dict(s=s, h=h, D=Dh, t_a=t, d_sh=_med(dsh, t), d_sD=_med(dsd, t),
                                loose_stop=any(st.loose is True for st in near), dwell=max([st.dwell for st in near], default=0.0),
                                sig=_sigd(scene, s, h, t)))
    c["approach"] = out
    return out


def _slip(scene, ap) -> dict | None:
    P = prm("slip_screen")
    r = _kv(scene, ap["s"])["r"]
    t_a = ap["t_a"]
    n15 = frames(0.5)
    start = None
    for t0 in range(_win(scene, t_a, -0.5, 0)[0], _win(scene, t_a, 0, P["slip_start_max_s"])[1] + 1):
        if t0 + n15 < scene.n and r[t0 + n15] - r[t0] <= -P["slip_dr_m"]:
            start = t0
            break
    wa, wb = _win(scene, t_a, 0, P["slip_window_s"])
    mr = float(np.nanmin(r[wa:wb + 1]))
    if start is None or mr > P["slip_r_m"]:
        return None
    return dict(start=start, min_r=mr, slip_type="slow" if ap["loose_stop"] else "quick",
                touch=bool(ap["d_sD"] <= prm("screen_set")["contact_likely_m"]),
                peak_vr=float(np.nanmax(_kv(scene, ap["s"])["vr"][start:wb + 1])), dwell_before_exit=ap["dwell"])


def _ghost(scene, ap) -> dict | None:
    P = prm("ghost_screen")
    if ap["loose_stop"] or not ap["d_sD"] > P["no_contact_m"]:
        return None
    s, t_a = ap["s"], ap["t_a"]
    r = _kv(scene, s)["r"]
    # leaves away from the rim: r rises by >= ghost_dr_m within rise_window_s. SCR-T11: the old 1.0 m within 1.0 s
    # failed for screeners who start near the arc (V0: ghosts rise 0.95-2.5 m in 1.5 s, fake-lateral exits <= 0.66 m)
    a1, b1 = _win(scene, t_a, 0, P["rise_window_s"])
    if not np.nanmax(r[a1:b1 + 1]) - r[t_a] >= P["ghost_dr_m"]:
        return None
    a2, b2 = _win(scene, t_a, 0, P["ghost_window_s"])
    ks = scene.k(s)
    hit = next((t for t in range(a2, b2 + 1) if _in("pop_arc_zone", ks.x[t], ks.y[t])), None)
    if hit is None:
        return None
    return dict(exit_frame=hit, max_r=float(np.nanmax(r[a2:b2 + 1])), exit_region=_region(ks.x[hit], ks.y[hit]))


def _ap_event(scene, kind, ap, p, attrs, end_s=1.5):
    a, b = _win(scene, ap["t_a"], -1.0, end_s)
    return _event(scene, kind, {"screener": ap["s"], "handler": ap["h"], "defender": ap["D"]}, ap["t_a"], a, b, p, attrs)


def _ap_gate_p(ap) -> float:
    P = prm("slip_screen")
    return max(_pb(ap["d_sh"], P["approach_h_m"], ap["sig"]), _pb(ap["d_sD"], P["approach_d_m"], ap["sig"]))


def detect_slip_screen(scene, **params) -> list:
    """slip_screen: approach without a full stop, then an early dive to the rim (quick/slow, touch flag)."""
    out = []
    for ap in _approaches(scene):
        sl = _slip(scene, ap)
        if sl is None:
            continue
        p = _ap_gate_p(ap) * _pb(sl["min_r"], prm("slip_screen")["slip_r_m"], _sig_pos(scene, ap["s"], ap["t_a"]))
        e = _ap_event(scene, "slip_screen", ap, p, sl)
        if e:
            out.append(e)
    return out


def detect_ghost_screen(scene, **params) -> list:
    """ghost_screen: approach without stand or contact, then an exit away from the rim to the arc."""
    out = []
    for ap in _approaches(scene):
        g = _ghost(scene, ap)
        if g is None or _slip(scene, ap) is not None:
            continue
        p = _ap_gate_p(ap) * _pa(ap["d_sD"], prm("ghost_screen")["no_contact_m"], ap["sig"]) * \
            _pa(g["max_r"], prm("ghost_screen")["arc_r_m"], _sig_pos(scene, ap["s"], ap["t_a"]))
        e = _ap_event(scene, "ghost_screen", ap, p, g, end_s=2.0)
        if e:
            out.append(e)
    return out


def detect_fake_screen(scene, **params) -> list:
    """fake_screen: approach without a screen, then a lateral exit or a move to another screen."""
    P = prm("fake_screen", params)
    out = []
    for ap in _approaches(scene):
        if ap["loose_stop"] or _slip(scene, ap) is not None or _ghost(scene, ap) is not None:
            continue
        s, t_a = ap["s"], ap["t_a"]
        t1 = _win(scene, t_a, 0, 1.0)[1]
        disp = float(np.hypot(*(_pos(scene, s, t1) - _pos(scene, s, t_a))))
        dr = _r_at(scene, s, t1) - _r_at(scene, s, t_a)
        exit_ = None
        if any(r.s == s and r.u != ap["h"] and 0 < r.ts - t_a <= frames(P["move_to_screen_s"])
               for r in _records(scene)):
            exit_ = "move_to_screen"
        elif disp >= P["lateral_disp_m"] and abs(dr) < P["lateral_dr_max_m"]:
            exit_ = "lateral"
        if exit_ is None:
            continue
        e = _ap_event(scene, "fake_screen", ap, _ap_gate_p(ap), dict(exit=exit_, exit_disp_m=disp, exit_dr_m=dr))
        if e:
            out.append(e)
    return out


def _is_drag(scene, r: Rec, P) -> bool:
    ks = scene.k(r.s)
    a1, b1 = _win(scene, r.stop.a, -P["trail_s"], -0.1)
    vy = float(np.nanmean(ks.vy[a1:b1 + 1]))
    hp = _pos(scene, r.u, r.ts)
    # the trailer comes from beyond the top of the key / the backcourt (SCR-T08: a half-court screener running
    # down from the top is not a drag)
    return bool(vy <= -P["trail_vy_mps"] and ks.y[a1] >= P["trail_start_y_m"]
                and P["ps_r_lo_m"] <= r.m["r_s"] <= P["ps_r_hi_m"] and _in("drag_screen_spot", *hp))


def detect_drag_screen(scene, **params) -> list:
    """drag_screen: transition ball screen by a trailing screener near the arc."""
    P = prm("drag_screen", params)
    out = []
    for r in _screens(scene, "on_ball"):
        if not _is_drag(scene, r, P):
            continue
        a, b = _scr_window(r)
        e = _event(scene, "drag_screen", _actors(r, "handler"), r.ts, a, b, r.p,
                   dict(_ball_attrs(scene, r), pre_action="drag", phase_checked=False))
        if e:
            out.append(e)
    return out


def detect_double_drag(scene, **params) -> list:
    """double_drag: two ball screens on one handler by different screeners in quick order."""
    P, Pd = prm("double_drag", params), prm("drag_screen")
    scr = sorted(_screens(scene, "on_ball"), key=lambda r: r.ts)
    out = []
    for i, r1 in enumerate(scr):
        for r2 in scr[i + 1:]:
            if r2.u != r1.u or r2.s == r1.s:
                continue
            dt = (r2.ts - r1.ts) * DT
            sep = float(_dist(scene, r1.s, r2.s)[r1.ts])
            if not (P["dt_lo_s"] <= dt <= P["dt_hi_s"] and r1.m["r_s"] >= P["min_r_m"] and r2.m["r_s"] >= P["min_r_m"]
                    and P["sep_lo_m"] <= sep <= P["sep_hi_m"] + P["sep_tol_m"]):
                continue
            if min(r1.ts - r1.stop.a, r2.ts - r2.stop.a) * DT < P["set_before_s"]:
                continue  # loop 4 (SCR-L4-03): a screener still arriving at his screen moment is not a set second screen
            if not (_is_drag(scene, r1, Pd) or _is_drag(scene, r2, Pd)):
                continue
            pa1 = _post_action(scene, r1.s, r1.ts, r1.m["t_h"], r1.m["P_s"])["action"]
            pa2 = _post_action(scene, r2.s, r2.ts, r2.m["t_h"], r2.m["P_s"])["action"]
            e = _event(scene, "double_drag", {"screener_1": r1.s, "screener_2": r2.s, "handler": r1.u}, r1.ts,
                       min(r1.stop.a, r1.ts), max(r2.stop.b, r2.ts), r1.p * r2.p,
                       dict(dt_s=dt, separation_m=sep, spacing_in_band=bool(P["sep_lo_m"] <= sep <= P["sep_hi_m"]),
                            first_rolls=pa1 == "roll", second_pops=pa2 == "pop_arc"))
            if e:
                out.append(e)
    return out


def detect_spain_pnr(scene, **params) -> list:
    """spain_pnr: ball screen by s1, then s2 back-screens s1's defender while s1 rolls and s2 pops."""
    P = prm("spain_pnr", params)
    off = _screens(scene, "off_ball")
    out = []
    for r1 in _screens(scene, "on_ball"):
        for r2 in off:
            dt = (r2.ts - r1.ts) * DT
            if r2.u != r1.s or r2.s == r1.u or not (0 <= dt <= P["dt_max_s"]):
                continue
            if not (np.isfinite(r2.m["n_r"]) and r2.m["n_r"] >= P["n_r_min"]):
                continue
            wa, wb = _win(scene, r1.ts, 0, 2.0)
            if _min_r(scene, r1.s, wa, wb) > P["roll_r_m"]:
                continue
            ka, kb = _win(scene, r2.ts, 0, P["pop_window_s"])
            k2 = scene.k(r2.s)
            if not any(_in("spain_pop_spot", k2.x[t], k2.y[t]) for t in range(ka, kb + 1)):
                continue
            t0 = _win(scene, r1.ts, -1.0, 0)[0]
            stack = bool(_dist(scene, r1.s, r2.s)[t0] <= P["stack_m"])
            cov = _coverage_on(scene, r1)
            e = _event(scene, "spain_pnr", {"screener": r1.s, "back_screener": r2.s, "handler": r1.u,
                                            "defender": r2.D}, r1.ts, min(r1.stop.a, r1.ts), kb, r1.p * r2.p,
                       dict(stack=stack, s2_pops=True, D_s1_depth=cov["big"], dt_s=dt))
            if e:
                out.append(e)
    return out


def detect_double_ball_screen(scene, **params) -> list:
    """double_ball_screen: Detroit (side-by-side) and double high (trade / sink)."""
    P = prm("double_ball_screen", params)
    sets = sorted([r for r in _records(scene) if r.kind == "on_ball" and r.m["merged_into"] is None],
                  key=lambda r: r.ts)
    out = []
    for i, r1 in enumerate(sets):
        for r2 in sets[i + 1:]:
            if r2.u != r1.u or r2.s == r1.s or not (r1.is_screen or r2.is_screen):
                continue
            dt = (r2.ts - r1.ts) * DT
            gap = float(_dist(scene, r1.s, r2.s)[r1.ts])
            sub = None
            oa, ob = max(r1.stop.a, r2.stop.a), min(r1.stop.b, r2.stop.b)
            overlap = (ob - oa) * DT
            k1, k2 = scene.k(r1.s), scene.k(r2.s)
            dy = abs(float(k1.y[r1.ts] - k2.y[r1.ts]))  # court-length (vertical) offset of the two screeners
            if ob > oa:  # both standing: mean gap / offset over the shared stand (noise)
                gap = float(np.nanmean(_dist(scene, r1.s, r2.s)[oa:ob + 1]))
                dy = abs(float(np.nanmean(k1.y[oa:ob + 1] - k2.y[oa:ob + 1])))
            # OD-7 (owner decision 25 Oct): screeners staggered along the court length by >= stagger_min_dy_m are a
            # double drag / stagger, not side by side
            if gap <= P["detroit_gap_m"] and (dt <= P["detroit_dt_s"] or overlap >= P["detroit_overlap_s"]) \
                    and dy < P["stagger_min_dy_m"]:
                sub = "detroit"
            elif r1.is_screen and r2.is_screen and P["dh_dt_lo_s"] <= dt <= P["dh_dt_hi_s"]:
                t0 = _win(scene, r1.ts, -1.0, 0)[0]
                p1, p2 = _pos(scene, r1.s, t0), _pos(scene, r2.s, t0)
                pre = all(P["pre_r_lo_m"] <= np.hypot(*p) <= P["pre_r_hi_m"] and _m_deg(*p) >= P["pre_m_min"]
                          for p in (p1, p2)) and np.hypot(*(p1 - p2)) <= P["pre_gap_m"]
                if pre:
                    wa, wb = _win(scene, r1.ts, 0, 2.0)
                    rr = _kv(scene, r1.s)["r"][wa:wb + 1]
                    # SCR-M4-03: trade = the first screener MOVES to the arc (>= trade_move_m from where he stood at
                    # t_s1); a screener who set above the arc and stays there is a plain double high, not a trade
                    k1, p1s = scene.k(r1.s), _pos(scene, r1.s, r1.ts)
                    mv = np.hypot(k1.x[wa:wb + 1] - p1s[0], k1.y[wa:wb + 1] - p1s[1])
                    trade = bool(np.any(np.nan_to_num((rr >= P["trade_r_m"]) & (mv >= P["trade_move_m"]), nan=False)))
                    sub = ("double_high_sink" if np.nanmin(rr) < P["sink_r_m"] else
                           "double_high_trade" if trade else "double_high")
            if sub is None:
                continue
            e = _event(scene, "double_ball_screen", {"screener_1": r1.s, "screener_2": r2.s, "handler": r1.u},
                       r1.ts, min(r1.stop.a, r1.ts), max(r2.stop.b, r2.ts),
                       (r1.p if r1.is_screen else r1.p_set) * (r2.p if r2.is_screen else r2.p_set),
                       dict(sub_label=sub, dt_s=dt, gap_m=gap, dy_m=dy, used_by=[r.s for r in (r1, r2) if r.is_screen]))
            if e:
                out.append(e)
    return out


def detect_ram_screen(scene, **params) -> list:
    """ram_screen: s uses an off-ball screen by g, then sets a ball screen; wedge_ram / rub_ram flags."""
    P = prm("ram_screen", params)
    out = []
    for r1 in _screens(scene, "off_ball"):
        for r2 in _screens(scene, "on_ball"):
            dt = (r2.ts - r1.ts) * DT
            if r2.s != r1.u or not (P["dt_lo_s"] <= dt <= P["dt_hi_s"]):
                continue
            if _r_at(scene, r1.u, r1.ts) >= P["max_r_m"]:
                continue
            p0, p1 = _pos(scene, r1.u, r1.ts), _pos(scene, r1.u, r2.ts)
            hp = _pos(scene, r2.u, r1.ts)
            toward = float((p1 - p0) @ _unit(hp - p0))
            if toward < P["move_m"]:
                continue
            tg = _win(scene, r1.stop.a, -1.0, 0)[0]
            wedge = _r_at(scene, r1.s, tg) >= P["wedge_r_m"]
            e = _event(scene, "ram_screen", {"first_screener": r1.s, "screener": r1.u, "handler": r2.u}, r1.ts,
                       min(r1.stop.a, r1.ts), max(r2.stop.b, r2.ts), r1.p * r2.p,
                       dict(pre_action="wedge_ram" if wedge else "ram", rub_ram=r1.m["loose_rule_fired"] is not True,
                            dt_s=dt, move_toward_handler_m=toward))
            if e:
                out.append(e)
    return out


def detect_veer_screen(scene, **params) -> list:
    """veer_screen: ball screen, then the same screener sets an off-ball SET."""
    P = prm("veer_screen", params)
    out = []
    # the off-ball leg is any stand on a teammate's defender, also for a standing teammate (loop 2: those rows are not
    # screen_set rows any more, see screen_set still_user_mps)
    sets = [r for r in _records(scene) if r.kind == "off_ball" and r.m["merged_into"] is None] + _still_user_rows(scene)
    for r1 in _screens(scene, "on_ball"):
        for r2 in sets:
            dt = (r2.ts - r1.ts) * DT
            if r2.s != r1.s or not (P["dt_min_s"] < dt <= P["dt_max_s"]):
                continue
            if r2.stop.a <= r1.stop.b:
                continue  # SCR-T10: the off-ball row must come from a new stand (the screener moved on)
            e = _event(scene, "veer_screen", {"screener": r1.s, "handler": r1.u, "user_2": r2.u}, r1.ts,
                       min(r1.stop.a, r1.ts), max(r2.stop.b, r2.ts), r1.p * r2.p_set, dict(dt_s=dt))
            if e:
                out.append(e)
    return out


# --------------------------------------------------------------------------------------
# Detectors: defender response
# --------------------------------------------------------------------------------------
def detect_ball_screen_coverage(scene, **params) -> list:
    """ball_screen_coverage: D_h route, D_s depth band, switch, CTG mapping for every ball screen."""
    out = []
    # rejected ball screens are rows too: ICE is a reject read (SCR-T02); is_screen and reject are disjoint
    rows = [r for r in _records(scene) if r.kind == "on_ball" and r.m["merged_into"] is None
            and (r.is_screen or r.m["read"] == "reject")]
    for r in rows:
        cov = _coverage_on(scene, r)
        p = r.p if r.is_screen else r.p_set
        if np.isfinite(cov["route_margin_m"]):
            p *= float(mvlib.phi(abs(cov["route_margin_m"]) / max(r.m["sigma_d"], 1e-3)))
        a, b = _scr_window(r)
        e = _event(scene, "ball_screen_coverage", {"handler_defender": r.D, "screener_defender": r.Ds,
                                                   "handler": r.u, "screener": r.s}, r.ts, a, b, p, cov)
        if e:
            out.append(e)
    return out


def detect_off_ball_screen_coverage(scene, **params) -> list:
    """off_ball_screen_coverage: chase / top-lock / under / switch / bump / pre-switch for off-ball screens."""
    out = []
    for r in [x for x in _records(scene) if x.kind == "off_ball" and x.m["merged_into"] is None
              and (x.is_screen or x.m["read"] in ("reject", "unused"))]:
        cov = _coverage_off(scene, r)
        if not r.is_screen and cov["offball_coverage"] not in ("top_lock", "switch", "pre_switch"):
            continue  # an unused / rejected SET is a coverage row only when the defence did something (SCR-T07)
        a, b = _scr_window(r)
        e = _event(scene, "off_ball_screen_coverage", {"defender": r.D, "screener_defender": r.Ds, "user": r.u,
                                                       "screener": r.s}, r.ts, a, b, r.p if r.is_screen else r.p_set,
                   cov)
        if e:
            out.append(e)
    return out


# --------------------------------------------------------------------------------------
# Detectors: off-ball geometry (predicates are shared with the residual 'middle' class)
# --------------------------------------------------------------------------------------
def _arrive(scene, r: Rec, axis="r", back_s=1.5) -> float:
    """Screener's change of r (or y) over [a - back_s, a] (arrival before the stop onset)."""
    t0 = _win(scene, r.stop.a, -back_s, 0)[0]
    if axis == "r":
        return _r_at(scene, r.s, r.stop.a) - _r_at(scene, r.s, t0)
    return float(scene.k(r.s).y[r.stop.a] - scene.k(r.s).y[t0])


def _u_start(scene, r: Rec):
    """(frame, position) of the user's set-up before t_s: the last frame within user_start_search_s before t_s
    whose displacement speed is below screen_moment.tsu_min_speed_mps, else t_s - 0.5 s (start-position gates use it)."""
    Pm, Pa = prm("screen_moment"), prm("screen_angle")
    sp = _disp_speed(scene, r.u, Pm["tsu_half_s"])
    lo = _win(scene, r.ts, -Pa["user_start_search_s"], 0)[0]
    for t in range(r.ts, lo - 1, -1):
        if np.isfinite(sp[t]) and sp[t] < Pm["tsu_min_speed_mps"]:
            return t, _pos(scene, r.u, t)
    t = _win(scene, r.ts, -0.5, 0)[0]
    return t, _pos(scene, r.u, t)


def _du(scene, r: Rec, s0, s1):
    """User displacement vector and dr over [t_s + s0, t_s + s1]."""
    a, b = _win(scene, r.ts, s0, s1)
    p0, p1 = _pos(scene, r.u, a), _pos(scene, r.u, b)
    return p1 - p0, float(np.hypot(*p1) - np.hypot(*p0)), p0, p1


def _off_used(r: Rec) -> bool:
    return r.is_screen and r.kind == "off_ball"


def _is_down(scene, r, P=None):
    P = P or prm("down_screen")
    if not (_off_used(r) and np.isfinite(r.m["n_r"]) and r.m["n_r"] <= P["n_r_max"]):
        return None
    _, dr, p0, _ = _du(scene, r, -0.5, 1.0)
    if dr < P["user_dr_m"] or _arrive(scene, r) > -P["arrive_dr_m"] or np.hypot(*p0) >= r.m["r_s"]:
        return None
    return dict(geometry="down", user_dr_m=dr)


def _is_pin_down(scene, r, P=None):
    P = P or prm("pin_down")
    if not _off_used(r):
        return None
    t5, u0 = _u_start(scene, r)
    if (np.isfinite(r.m["n"][1]) and r.m["n"][1] <= P["wide_n_y_max"] and _m_deg(*u0) <= P["wide_user_m_max"]
            and np.hypot(*u0) >= P["wide_user_r_min_m"] and _arrive(scene, r, "y") <= -P["wide_arrive_dy_m"]
            and P["wide_ps_r_lo_m"] <= r.m["r_s"] <= P["wide_ps_r_hi_m"]
            and P["wide_ps_m_lo"] <= r.m["m_s"] <= P["wide_ps_m_hi"]):
        return dict(geometry="wide_pin_down", wide_pin_screen_spot=bool(_labels("wide_pin_screen_spot", *r.m["P_s"])))
    if _is_down(scene, r) and (u0[1] <= P["low_y_m"] or np.hypot(*u0) <= P["low_r_m"]):
        # the screen-point angle is an attribute, not a geometry split (SCR-T18: m_s = 40 deg flipped it under noise)
        return dict(geometry="pin_down", high_screen_point=bool(r.m["m_s"] > P["wide_ps_m_hi"]),
                    wide_pin_screen_spot=bool(_labels("wide_pin_screen_spot", *r.m["P_s"])))
    return None


def _is_flare(scene, r, P=None):
    P = P or prm("flare_screen")
    if not _off_used(r):
        return None
    d, _, p0, p1 = _du(scene, r, -0.3, 1.2)
    bp = _pos(scene, "ball", _win(scene, r.ts, -0.3, 0)[0])
    if not _fin(*bp):
        return None
    ang = _ang(d, bp - p0)
    if not (np.isfinite(ang) and ang >= P["flare_deg"] and np.hypot(*d) >= P["disp_m"]):
        return None
    if not (np.hypot(*p1) >= P["end_r_m"] or abs(p1[0]) - abs(p0[0]) >= P["dx_m"]):
        return None
    # D_u stands on the ball side of the screener, so the screener blocks his chase of a user fading away from the
    # ball (SCR-T05; n points from s to D_u). A pin-down fade has n toward the rim, away from the ball.
    n_ball = float(r.m["n"] @ _unit(bp - np.array(r.m["P_s"])))
    if not (np.isfinite(n_ball) and n_ball >= P["n_ball_min"]):
        return None
    # not a down-screen orientation (D_u inside / below the screener): a user popping off a pin-down or double to the
    # weak-side wing moves away from the ball too (loop 1, SCR-T05)
    if not (np.isfinite(r.m["n_r"]) and r.m["n_r"] > P["n_r_min"]):
        return None
    return dict(geometry="flare", angle_to_ball_deg=ang, n_ball=n_ball, user_end_region=_region(*p1))


def _is_back(scene, r, P=None):
    P = P or prm("back_screen")
    if not (_off_used(r) and np.isfinite(r.m["n_r"]) and r.m["n_r"] >= P["n_r_min"]):
        return None
    _, dr, _, _ = _du(scene, r, -0.3, 1.2)
    mr = _min_r(scene, r.u, *_win(scene, r.ts, 0, P["end_window_s"]))
    if dr > -P["user_dr_m"] or mr > P["end_r_m"]:
        return None
    if _is_flex(scene, r):
        return None  # loop 2 (back_screen-on-flex): a flex cut off a baseline screen is flex_screen, not back_screen
    return dict(geometry="back", end_r=mr, to_rim=bool(mr < 2.0))


def _passes_by(scene, u):
    return [x for x in _transfers(scene) if x["frm"] == u and x["type"] in ("pass", "pitch")]


def _is_ucla(scene, r, P=None):
    P = P or prm("ucla_screen")
    if not _off_used(r):
        return None
    xs, ys = r.m["P_s"]
    if not (_labels("elbow", xs, ys) or _labels("elbow_landmark", xs, ys)):
        return None
    for x in _passes_by(scene, r.u):
        rel = x["release"]
        up = _pos(scene, r.u, rel)
        if not (np.hypot(*up) >= P["pass_r_min_m"] and _m_deg(*up) >= P["pass_m_min"]):
            continue
        if not (0 <= (r.ts - rel) * DT <= P["cut_window_s"]):
            continue
        a, b = _win(scene, rel, 0, P["cut_window_s"])
        mr = _min_r(scene, r.u, a, b)
        rec_x = _pos(scene, x["to"], x["catch"])[0]
        end_x = _pos(scene, r.u, b)[0]
        if mr < P["end_r_m"] and np.hypot(*up) - mr >= P["cut_dr_m"] and np.sign(end_x) in (np.sign(rec_x), 0):
            return dict(geometry="ucla", pass_release=int(rel), receiver=x["to"], cut_end_r=mr)
    return None


def _is_rip(scene, r, P=None):
    P = P or prm("rip_screen")
    if not _is_back(scene, r):
        return None
    t5, u0 = _u_start(scene, r)
    wing = any(_labels(w, *u0) for w in ("wing_high", "wing_mid", "wing_low"))
    t0 = _win(scene, r.stop.a, -1.5, 0)[0]
    s0 = _pos(scene, r.s, t0)
    low = any(_labels(w, *s0) for w in ("low_post", "mid_post", "block"))
    if wing and low and _arrive(scene, r, "y") >= P["arrive_dy_m"]:
        return dict(geometry="rip")
    return None


def _is_cross(scene, r, P=None):
    P = P or prm("cross_screen")
    if not _off_used(r):
        return None
    if not (r.m["P_s"][1] < P["y_max_m"] and _pos(scene, r.u, r.ts)[1] < P["y_max_m"]):
        return None
    d, _, p0, p1 = _du(scene, r, -0.3, 1.2)
    if not (abs(d[0]) >= P["dx_m"] and abs(d[0]) >= P["ratio"] * abs(d[1])):
        return None
    bx = _pos(scene, "ball", r.ts)[0]
    if _fin(bx) and not (np.sign(p1[0]) == np.sign(bx) or abs(p1[0]) <= P["lane_x_m"]):
        return None
    return dict(geometry="cross", user_end_region=_region(*p1), strict_stationary=r.stop.strict)


def _is_flex(scene, r, P=None):
    P = P or prm("flex_screen")
    if not _off_used(r):
        return None
    xs, ys = r.m["P_s"]
    bx = _pos(scene, "ball", r.ts)[0]
    post = any(_labels(w, xs, ys) for w in ("low_post", "mid_post", "block"))  # SCR-T18: low_post alone was brittle
    if not (post and _fin(bx) and np.sign(xs) == -np.sign(bx)):
        return None
    a, b = _win(scene, r.ts, -P["window_s"] / 2, P["window_s"] / 2)
    u0, u1 = _pos(scene, r.u, a), _pos(scene, r.u, b)
    ys_path = scene.k(r.u).y[a:b + 1]
    if not (_m_deg(*u0) <= P["start_m_max"] and np.hypot(*u0) >= P["start_r_min_m"] and np.sign(u0[0]) == np.sign(xs)):
        return None
    if not (np.nanmax(ys_path) < P["path_y_m"] and np.hypot(*u1) <= P["end_r_m"]
            and np.sign(u1[0]) == np.sign(bx) and abs(u1[0] - u0[0]) >= P["dx_m"]):
        return None
    return dict(geometry="flex")


def _is_zipper(scene, r, P=None):
    P = P or prm("zipper_screen")
    if not _off_used(r):
        return None
    t5, u0 = _u_start(scene, r)
    low = any(_labels(w, *u0) for w in ("low_post", "block", "mid_post"))  # SCR-T18: replaces start_r_max_m
    if not (low and P["start_m_lo"] <= _m_deg(*u0) <= P["start_m_hi"]):
        return None
    if not (_arrive(scene, r, "y") <= -P["arrive_dy_m"] and P["ps_r_lo_m"] <= r.m["r_s"] <= P["ps_r_hi_m"]):
        return None
    b = _win(scene, t5, 0, P["window_s"])[1]
    for t in range(t5, b + 1):
        p = _pos(scene, r.u, t)
        dy, dx = p[1] - u0[1], p[0] - u0[0]
        if dy >= P["dy_m"] and np.hypot(*p) >= P["end_r_m"] and P["end_m_lo"] <= _m_deg(*p) <= P["end_m_hi"]:
            if abs(dx) < P["vert_ratio"] * dy:
                return dict(geometry="zipper", inbound=r.m["inbound"], reach_frame=int(t))
    return None


def _is_wedge(scene, r, P=None):
    P = P or prm("wedge_screen")
    if not (_off_used(r) and np.isfinite(r.m["n_r"]) and r.m["n_r"] >= P["n_r_min"]):
        return None
    t1 = _win(scene, r.stop.a, -1.0, 0)[0]
    if _r_at(scene, r.s, t1) < P["perim_r_m"]:
        return None
    t5, u0 = _u_start(scene, r)
    if not any(_labels(w, *u0) for w in ("high_post_area", "elbow", "elbow_landmark")):
        return None
    dive = _min_r(scene, r.u, *_win(scene, r.ts, 0, 1.5)) <= P["end_r_m"]
    becomes = any(x.s == r.u and 0 < (x.ts - r.ts) * DT <= 2.0 for x in _screens(scene, "on_ball"))
    if not (dive or becomes):
        return None
    xs = r.m["P_s"][0]
    radial_dev = _ang(r.m["n"], _unit(np.array(r.m["P_s"])))
    sub = "gut" if abs(xs) < P["gut_x_m"] else "slice" if radial_dev <= P["slice_deg"] else "diagonal"
    return dict(geometry="wedge_offball", sub_label=sub, becomes_ball_screener=becomes)


def _is_shuffle(scene, r, P=None):
    P = P or prm("shuffle_screen")
    if not _off_used(r):
        return None
    if not (P["ps_r_lo_m"] <= r.m["r_s"] <= P["ps_r_hi_m"] and r.m["m_s"] >= P["ps_m_min"]):
        return None
    for x in _passes_by(scene, r.u):
        rel = x["release"]
        if not (0 <= (r.ts - rel) * DT <= P["window_s"]):
            continue
        up = _pos(scene, r.u, rel)
        a, b = _win(scene, rel, 0, P["window_s"])
        mr = _min_r(scene, r.u, a, b)
        end_x = _pos(scene, r.u, b)[0]
        if mr < P["end_r_m"] and np.hypot(*up) - mr >= P["dr_m"] and np.sign(end_x) != np.sign(up[0]):
            return dict(geometry="shuffle", pass_release=int(rel))
    return None


_GEOMS = {"down": _is_down, "pin_down": _is_pin_down, "flare": _is_flare, "back": _is_back, "ucla": _is_ucla,
          "rip": _is_rip, "cross": _is_cross, "flex": _is_flex, "zipper": _is_zipper, "wedge": _is_wedge,
          "shuffle": _is_shuffle}


def _geom_detector(kind, pred, t0_key=None):
    def det(scene, **params):
        P = prm(kind, params)
        out = []
        for r in _screens(scene, "off_ball"):
            g = pred(scene, r, P)
            if not g:
                continue
            t0 = g.get(t0_key, r.ts) if t0_key else r.ts
            a, b = _scr_window(r)
            attrs = dict(_screen_attrs(r), **g)
            attrs["coverage"] = _coverage_off(scene, r)["offball_coverage"]
            e = _event(scene, kind, _actors(r), t0, a, b, r.p, attrs)
            if e:
                out.append(e)
        return out
    det.__name__ = f"detect_{kind}"
    det.__doc__ = f"{kind}: off-ball screen geometry (see config/movement_grammar/screens.yaml)."
    return det


detect_down_screen = _geom_detector("down_screen", _is_down)
detect_pin_down = _geom_detector("pin_down", _is_pin_down)
detect_flare_screen = _geom_detector("flare_screen", _is_flare)
detect_back_screen = _geom_detector("back_screen", _is_back)
detect_ucla_screen = _geom_detector("ucla_screen", _is_ucla, "pass_release")
detect_rip_screen = _geom_detector("rip_screen", _is_rip)
detect_cross_screen = _geom_detector("cross_screen", _is_cross)
detect_flex_screen = _geom_detector("flex_screen", _is_flex)
detect_zipper_screen = _geom_detector("zipper_screen", _is_zipper)
detect_wedge_screen = _geom_detector("wedge_screen", _is_wedge)
detect_shuffle_screen = _geom_detector("shuffle_screen", _is_shuffle, "pass_release")


def detect_stagger_screen(scene, **params) -> list:
    """stagger_screen: consecutive used off-ball screens on one user by different screeners."""
    P = prm("stagger_screen", params)
    # the first screen is used; a later one only needs the user to pass it (its defender may already trail, so the
    # blocking term of 'use' can fail: SCR-T18)
    scr = sorted([r for r in _screens(scene, "off_ball") if r.m["passed"]], key=lambda r: r.m["tc"])
    out = []
    for i, r1 in enumerate(scr):
        if r1.m["read"] != "use":
            continue
        chain = [r1]
        for r2 in scr[i + 1:]:
            last = chain[-1]
            if r2.u != r1.u or r2.s in [c.s for c in chain]:
                continue
            dt = (r2.m["tc"] - last.m["tc"]) * DT
            gap = float(np.hypot(*(np.array(r2.m["P_s"]) - np.array(last.m["P_s"]))))
            if P["dt_lo_s"] <= dt <= P["dt_hi_s"] and P["gap_lo_m"] < gap <= P["gap_hi_m"]:
                chain.append(r2)
        if len(chain) < 2:
            continue
        if any(r1 is c for e_ in out for c in e_.attrs.get("_chain", [])):
            continue
        gaps = [float(np.hypot(*(np.array(b_.m["P_s"]) - np.array(a_.m["P_s"])))) for a_, b_ in zip(chain, chain[1:])]
        g0 = gaps[0]
        cls = "tight" if g0 <= P["tight_m"] else "standard" if g0 <= P["standard_m"] else "wide"
        p = float(np.prod([c.p for c in chain]))
        actors = {"user": r1.u, **{f"screener_{k + 1}": c.s for k, c in enumerate(chain)}}
        e = _event(scene, "stagger_screen", actors, r1.ts, min(r1.stop.a, r1.ts), max(chain[-1].m["tc"], chain[-1].ts),
                   p, dict(gap_m=g0, gaps_m=gaps, gap_class=cls, n_screens=len(chain),
                           triple=len(chain) >= 3, ambiguous_double_stagger=abs(g0 - P["gap_lo_m"]) < 0.4,
                           dt_s=(chain[1].m["tc"] - r1.m["tc"]) * DT, _chain=chain))
        if e:
            out.append(e)
    for e_ in out:
        e_.attrs.pop("_chain", None)
    return out


def detect_double_screen(scene, **params) -> list:
    """double_screen: two adjacent screeners screen the same user together."""
    P = prm("double_screen", params)
    scr = sorted(_screens(scene, "off_ball"), key=lambda r: r.ts)
    out = []
    for i, r1 in enumerate(scr):
        for r2 in scr[i + 1:]:
            if r2.u != r1.u or r2.s == r1.s:
                continue
            gap = float(_dist(scene, r1.s, r2.s)[r1.ts])
            if gap > P["gap_max_m"] or abs(r2.m["tc"] - r1.m["tc"]) * DT > P["dt_max_s"]:
                continue
            along = abs(float((_pos(scene, r2.s, r1.ts) - _pos(scene, r1.s, r1.ts)) @ r1.m["d_hat"]))
            e = _event(scene, "double_screen", {"screener_1": r1.s, "screener_2": r2.s, "user": r1.u}, r1.ts,
                       min(r1.stop.a, r2.stop.a, r1.ts), max(r1.m["tc"], r2.m["tc"]), r1.p * r2.p,
                       dict(layout="side_by_side" if along <= P["side_m"] else "stacked_double", gap_m=gap))
            if e:
                out.append(e)
    return out


def detect_elevator_screen(scene, **params) -> list:
    """elevator_screen: two standing screeners close the gate after the user runs through it."""
    P = prm("elevator_screen", params)
    out = []
    off = scene.offense
    for i, s1 in enumerate(off):
        for s2 in off[i + 1:]:
            gap = _dist(scene, s1, s2)
            for u in off:
                if u in (s1, s2):
                    continue
                k1, k2, ku = scene.k(s1), scene.k(s2), scene.k(u)
                cr = (k2.x - k1.x) * (ku.y - k1.y) - (k2.y - k1.y) * (ku.x - k1.x)
                for t in range(frames(0.7), scene.n - frames(0.7)):
                    if not (np.isfinite(cr[t]) and np.isfinite(cr[t + 1]) and np.sign(cr[t]) != np.sign(cr[t + 1])):
                        continue
                    _, uu = _seg_proj(_pos(scene, u, t), _pos(scene, s1, t), _pos(scene, s2, t))
                    if not (0.0 <= uu <= 1.0):
                        continue
                    va, vb = _win(scene, t, -0.15, 0.15)
                    v = _mean_v(scene, u, va, vb)
                    if not (v[1] > 0 and np.hypot(*v) >= P["cross_speed_mps"]):
                        continue
                    pa, pb = _win(scene, t, -0.6, -0.1)
                    need = int(0.6 * (pb - pa + 1))
                    if not (_stand_run(scene, s1, pa, pb, need) and _stand_run(scene, s2, pa, pb, need)):
                        continue
                    pre = float(np.nanmean(gap[pa:pb + 1]))
                    if not (P["pre_lo_m"] <= pre <= P["wide_hi_m"]):
                        continue
                    qa, qb = _win(scene, t, 0.1, P["close_s"])
                    post = float(np.nanmin(gap[qa:qb + 1]))
                    e12 = _unit(_pos(scene, s2, t) - _pos(scene, s1, t))
                    m1 = float((_pos(scene, s1, qb) - _pos(scene, s1, t)) @ e12)
                    m2 = float((_pos(scene, s2, qb) - _pos(scene, s2, t)) @ -e12)
                    change = pre - post
                    if change < P["gap_change_m"] or m1 < P["move_m"] or m2 < P["move_m"]:
                        continue
                    sig = _sigd(scene, s1, s2, t)
                    e = _event(scene, "elevator_screen", {"screener_1": s1, "screener_2": s2, "user": u}, t, pa, qb,
                               _pa(change, P["gap_change_m"], sig),
                               dict(pre_gap_m=pre, closed_gap_m=post, gap_change_m=change,
                                    wide=bool(pre > P["pre_hi_m"]), close_time_s=(qb - t) * DT))
                    if e:
                        out.append(e)
                    break
    return out


def _drives(scene) -> list:
    """Drives by the holder: r from > drive_r_start_m to < drive_r_end_m within one possession segment."""
    P = prm("hammer_screen")
    out = []
    for h, a0, b0 in _segments(scene):
        r = _kv(scene, h)["r"]
        inside = np.flatnonzero(r[a0:b0 + 1] < P["drive_r_end_m"])
        if not len(inside):
            continue
        t_end = a0 + int(inside[0])
        outside = np.flatnonzero(r[a0:t_end + 1] > P["drive_r_start_m"])
        if not len(outside):
            continue
        out.append(dict(h=h, start=a0 + int(outside[-1]), end=t_end, seg=(a0, b0)))
    return out


def detect_hammer_screen(scene, **params) -> list:
    """hammer_screen: baseline drive, weak-side screen, user fades to the corner, kick-out pass."""
    P = prm("hammer_screen", params)
    out = []
    for dv in _drives(scene):
        h = dv["h"]
        he = _pos(scene, h, dv["end"])
        if _m_deg(*he) > P["drive_m_max"]:
            continue
        # SCR-M1-08: the weak-side screen of a hammer may be an off-ball SET row whose user came through it at speed
        # without a used-screen reading (he fades to the corner; the drive, the corner and the kick-out pass carry the
        # evidence)
        rows = _screens(scene, "off_ball") + [x for x in _records(scene) if x.kind == "off_ball" and not x.is_screen
                                              and x.m["merged_into"] is None and x.m["passed"]
                                              and x.m.get("user_peak_mps", 0.0) >= prm("screen")["user_speed_off_mps"]]
        for r in rows:
            if np.sign(r.m["P_s"][0]) == np.sign(he[0]) or not (dv["start"] - frames(1.0) <= r.ts <= dv["end"] + frames(1.5)):
                continue
            t5, u0 = _u_start(scene, r)
            if not (np.hypot(*u0) >= P["user_r_min_m"] and P["user_m_lo"] <= _m_deg(*u0) <= P["user_m_hi"]):
                continue
            a, b = _win(scene, r.ts, 0, 2.0)
            t_corner = next((t for t in range(a, b + 1) if _m_deg(*_pos(scene, r.u, t)) <= P["corner_m_max"]), None)
            if t_corner is None:
                continue
            ps = [x for x in _transfers(scene) if x["frm"] == h and x["to"] == r.u
                  and _r_at(scene, h, x["release"]) < P["pass_r_max_m"]
                  and abs(_pos(scene, r.u, x["catch"])[0] - _pos(scene, h, x["release"])[0]) > P["pass_dx_m"]
                  and -frames(0.8) <= x["release"] - t_corner <= frames(P["pass_window_s"])]
            if not ps:
                continue
            x = ps[0]
            fl_a, fl_b = x["release"], x["catch"]
            close = float(np.nanmean(mvlib.closing_speed(scene.k(r.D), scene.k(r.u))[fl_a:fl_b + 1]))
            e = _event(scene, "hammer_screen", {"driver": h, "screener": r.s, "user": r.u, "defender": r.D},
                       dv["start"], dv["start"], x["catch"], r.p,
                       dict(geometry="hammer", drive=(dv["start"], dv["end"]), pass_release=int(x["release"]),
                            closeout_speed_mps=close, t_s=r.ts))
            if e:
                out.append(e)
    return out


def detect_iverson_screen(scene, **params) -> list:
    """iverson_screen: wing-to-wing cut across the top past one or two elbow screeners."""
    P = prm("iverson_screen", params)
    scr = _screens(scene, "off_ball")
    out = []
    for u in scene.offense:
        ku = scene.k(u)
        done = -10**9
        for t in range(1, scene.n):
            if t < done or not (np.isfinite(ku.x[t - 1]) and np.sign(ku.x[t - 1]) != np.sign(ku.x[t])):
                continue
            if not (P["y_lo_m"] <= ku.y[t] <= P["y_hi_m"]):
                continue
            lim = frames(P["window_s"])
            ts_ = t
            while ts_ > max(0, t - lim) and abs(ku.vx[ts_ - 1]) >= P["run_vx_mps"]:
                ts_ -= 1
            te = t
            while te < min(scene.n - 1, t + lim) and abs(ku.vx[te + 1]) >= P["run_vx_mps"]:
                te += 1
            p0, p1 = _pos(scene, u, ts_), _pos(scene, u, te)
            if not (np.hypot(*p0) >= P["start_r_m"] and abs(p0[0]) >= P["start_x_m"] and abs(p1[0] - p0[0]) >= P["dx_m"]
                    and (te - ts_) * DT <= P["window_s"] and np.sign(p1[0]) != np.sign(p0[0])):
                continue
            ea, eb = te, _win(scene, te, 0, 0.7)[1]
            end_r = float(np.nanmax(_kv(scene, u)["r"][ea:eb + 1]))
            if end_r < P["end_r_m"]:
                continue
            used = [r for r in scr if r.u == u and ts_ - frames(0.5) <= r.ts <= te + frames(0.3)
                    and P["ps_r_lo_m"] <= r.m["r_s"] <= P["ps_r_hi_m"] and r.m["m_s"] >= P["ps_m_min"]]
            if not used:
                continue
            curl = _min_r(scene, u, *_win(scene, max(r.ts for r in used), 0, 1.0)) < P["curl_r_m"]
            p = max(r.p for r in used)
            actors = {"user": u, **{("screener" if k == 0 else f"screener_{k + 1}"): r.s for k, r in enumerate(used)}}
            e = _event(scene, "iverson_screen", actors, ts_, ts_, te, p,
                       dict(geometry="iverson", n_screeners=len(used), curl=curl,
                            iverson_loose_band=bool(P["loose_band_lo_m"] <= ku.y[t] <= P["loose_band_hi_m"]),
                            cross_y_m=float(ku.y[t])))
            if e:
                out.append(e)
            done = te + frames(1.0)
    return out


def detect_screen_the_screener(scene, **params) -> list:
    """screen_the_screener: a screener becomes the user of a second screen within dt_max_s."""
    P = prm("screen_the_screener", params)
    scr = _screens(scene)
    out = []
    for r1 in scr:
        for r2 in _screens(scene, "off_ball"):
            dt = (r2.ts - r1.ts) * DT
            if r2.u != r1.s or r2.s == r1.s or not (0 <= dt <= P["dt_max_s"]):
                continue
            if r2.s == r1.u or r2.m["read"] != "use":
                continue  # a mutual pair (u screens back for s) is a role reversal; the second screen is used (SCR-T06)
            _, dr, _, _ = _du(scene, r2, -0.3, 1.2)
            g1 = r1.m["dir_class_generic"]
            ok = (dr <= -P["back_dr_m"]) if g1 in ("back", "cross") else (dr >= P["down_dr_m"]) if g1 == "down" \
                else (abs(dr) >= P["down_dr_m"])
            if not ok:
                continue
            e = _event(scene, "screen_the_screener", {"first_screener_user": r1.s, "screener_2": r2.s,
                                                      "first_user": r1.u}, r1.ts, min(r1.stop.a, r1.ts),
                       max(r2.m["tc"], r2.ts), r1.p * r2.p, dict(first_geometry=g1, sts_user_dr_m=dr, dt_s=dt))
            if e:
                out.append(e)
    return out


def detect_off_ball_screen_other(scene, **params) -> list:
    """off_ball_screen_other: pin_in, out, baseline_exit, middle (residual) off-ball screens."""
    P = prm("off_ball_screen_other", params)
    out = []
    for r in [x for x in _records(scene) if x.kind == "off_ball" and x.m["merged_into"] is None]:
        geo = None
        t5, u0 = _u_start(scene, r)
        ta = _win(scene, r.stop.a, -1.5, 0)[0]
        ua, ub = _win(scene, r.ts, -0.5, 1.0)
        umove = float(np.nanmax(np.hypot(scene.k(r.u).x[ua:ub + 1] - u0[0], scene.k(r.u).y[ua:ub + 1] - u0[1])))
        if (_r_at(scene, r.s, ta) < 4.5 and _arrive(scene, r) > P["pin_in_dr_m"] and 4.0 <= r.m["r_s"] <= 6.5
                and np.hypot(*u0) >= 6.6 and umove <= P["pin_in_user_move_m"]
                and _r_at(scene, r.D, r.ts) < np.hypot(*u0) - 1.0 and r.m["interaction"]["delay"]):
            geo = "pin_in"
        elif r.is_screen:
            claimed = any(f(scene, r) for f in _GEOMS.values())
            d, dr, p0, p1 = _du(scene, r, -0.5, 1.5)
            if (not _is_down(scene, r)  # an elbow down screen is not also an out screen (SCR-T16)
                    and P["out_ps_r_lo_m"] <= r.m["r_s"] <= P["out_ps_r_hi_m"] and r.m["m_s"] >= P["out_ps_m_min"]
                    and dr >= P["out_dr_m"] and np.hypot(*p1) >= 6.6 and np.sign(p1[0]) == np.sign(p0[0])
                    and abs(_m_deg(*p1) - _m_deg(*p0)) <= P["out_turn_deg"]):
                geo = "out"
            elif r.m["P_s"][1] < P["base_y_m"] and _m_deg(*p1) <= P["base_m_max"] and np.nanmax(
                    scene.k(r.u).y[_win(scene, r.ts, -0.5, 1.5)[0]:_win(scene, r.ts, -0.5, 1.5)[1] + 1]) < 2.5:
                geo = "baseline_exit"
            elif not claimed:
                bp = _pos(scene, "ball", t5)
                ang = _ang(d, bp - p0) if _fin(*bp) else float("nan")
                if np.isfinite(ang) and ang < 60.0 and abs(p0[0]) - abs(p1[0]) >= P["middle_dx_m"]:
                    geo = "middle"
        if geo is None:
            continue
        a, b = _scr_window(r)
        e = _event(scene, "off_ball_screen_other", _actors(r), r.ts, a, b, r.p if r.is_screen else r.p_set,
                   dict(_screen_attrs(r), geometry=geo))
        if e:
            out.append(e)
    return out


# --------------------------------------------------------------------------------------
# Detectors: handoffs
# --------------------------------------------------------------------------------------
def _dho_list(scene) -> list:
    return [x for x in _transfers(scene) if x["type"] == "dho" and x["frm"] in scene.offense and x["to"] in scene.offense]


def detect_dho(scene, **params) -> list:
    """dho: possession transfer hand to hand; the hander acts as the screener."""
    P = prm("dho", params)
    out = []
    for x in _dho_list(scene):
        a, b, t_ex = x["frm"], x["to"], x["catch"]
        Db, _ = _defender_of(scene, b, _cl(scene, t_ex - frames(1.0)))
        ta, tb = _win(scene, t_ex, -0.5, 1.0)
        t_s = ta + int(np.nanargmin(_dist(scene, a, Db)[ta:tb + 1])) if Db is not None else t_ex
        hp = _pos(scene, a, t_ex)
        sp_b = _med(_kv(scene, b)["speed"], t_ex)
        pa = _post_action(scene, a, t_s, t_ex, tuple(hp))
        rp = _pos(scene, b, t_ex)
        p = _pb(x["d_ab"], P["dist_max_m"], _sigd(scene, a, b, t_ex))
        e = _event(scene, "dho", {"hander": a, "receiver": b, "defender": Db}, t_ex, x["release"] - 5,
                   _win(scene, t_ex, 0, 0.5)[1], p,
                   dict(screen_kind="handoff", t_ex=int(t_ex), t_s=int(t_s), dist_at_exchange_m=x["d_ab"],
                        air_time_s=x["air_s"], ball_travel_m=x["travel_m"],
                        strict=bool(x["d_ab"] <= P["strict_dist_m"] and x["air_s"] <= P["strict_air_s"] + 1e-9),
                        conventional=bool(sp_b > P["conventional_mps"]), post_dho=bool(np.hypot(*hp) < P["post_r_m"]),
                        handoff_exchange_spot=_in("handoff_exchange_spot", *rp, hx=float(hp[0]), hy=float(hp[1])),
                        hander_post_action=pa["action"], region=_region(*hp)))
        if e:
            out.append(e)
    return out


def _fake_candidates(scene) -> list:
    """Holder a moves the ball to teammate b, closes within approach_m, and keeps it (no transfer)."""
    c = _cache(scene)
    if "fake" in c:
        return c["fake"]
    P = prm("fake_dho")
    out = []
    for a, a0, b0 in _segments(scene):
        for b in scene.offense:
            if b == a:
                continue
            dab = _dist(scene, a, b)
            last = -10**9
            for t in range(max(a0 + frames(0.6), 1), min(b0, scene.n - 2) + 1):
                if not (np.isfinite(dab[t]) and dab[t] == np.nanmin(dab[max(0, t - 6):t + 7])):
                    continue
                if _med(dab, t) > P["approach_m"] or t - last < frames(1.0):  # SCR-T12: the YAML gate, no +0.3 m
                    continue
                va, vb = _win(scene, t, -0.6, -0.1)
                va_ = _mean_v(scene, a, va, vb)
                head = _ang(va_, _pos(scene, b, va) - _pos(scene, a, va))
                if not (np.hypot(*va_) >= 1.0 and np.isfinite(head) and head <= P["heading_deg"]):
                    continue
                close = float(np.nanmean(mvlib.closing_speed(scene.k(a), scene.k(b))[va:vb + 1]))
                if close < P["closing_mps"]:
                    continue
                # the receiver comes to the ball (SCR-T12: a driver passing a static spot-up is not a handoff fake)
                # REG-fake_dho (loop 2): the peak 5-frame mean over [t_c - receiver_window_s, t_c - 0.1], not the mean
                # over [t_c - 0.6, t_c - 0.1]: a backdoor receiver comes up and plants just before the fake
                kb = scene.k(b)
                ra = _win(scene, t, -P["receiver_window_s"], 0)[0]
                vproj = np.array([np.array([kb.vx[k], kb.vy[k]]) @ _unit(_pos(scene, a, k) - _pos(scene, b, k))
                                  for k in range(ra, vb + 1)], dtype=float)
                nm = int(P["receiver_mean_frames"])
                vb_to_a = (float(np.nanmax(np.convolve(np.nan_to_num(vproj), np.ones(nm) / nm, mode="valid")))
                           if len(vproj) >= nm else float(np.nanmean(vproj)))
                if not vb_to_a >= P["receiver_close_mps"]:
                    continue
                if any(r.u == a and r.kind == "on_ball" and 0 <= t - r.ts <= frames(P["after_screen_s"])
                       for r in _screens(scene)):
                    continue  # the handler attacking after a used ball screen (spain, double drag)
                xa, xb = _win(scene, t, -0.3, 0.5)
                if _holds(scene, b, xa, xb) >= 5 or _holds(scene, a, t + 1, t + 9) < 5:
                    continue
                if any(r.s == b and r.u == a and abs(r.ts - t) <= frames(P["screen_excl_s"]) for r in _records(scene)):
                    continue  # b is standing as a ball screener for a: a ball screen, not a handoff fake
                last = t
                Db, _ = _defender_of(scene, b, _cl(scene, t - frames(1.0)))
                out.append(dict(a=a, b=b, t_c=t, d_ab=_med(dab, t), sig=_sigd(scene, a, b, t), D=Db))
    c["fake"] = out
    return out


def detect_fake_dho(scene, **params) -> list:
    """fake_dho: handoff approach without transfer; the receiver goes away or backdoor."""
    P = prm("fake_dho", params)
    out = []
    for fc in _fake_candidates(scene):
        a, b, t = fc["a"], fc["b"], fc["t_c"]
        sub = None
        pre = _mean_v(scene, b, *_win(scene, t, -0.6, -0.1))
        post = _mean_v(scene, b, *_win(scene, t, 0.1, 0.6))
        turn = _ang(pre, post)
        wa, wb = _win(scene, t, 0, 1.5)
        rb = _kv(scene, b)["r"]
        if (np.isfinite(turn) and turn >= P["backdoor_turn_deg"] and np.nanmin(rb[wa:wb + 1]) < P["backdoor_r_m"]
                and rb[t] - np.nanmin(rb[wa:wb + 1]) >= P["backdoor_dr_m"]):
            sub = "backdoor"
        else:
            bw = _win(scene, t, 0, P["away_s"])[1]
            moved = float(np.hypot(*(_pos(scene, b, bw) - _pos(scene, b, t))))
            if moved >= P["away_m"] and _dist(scene, a, b)[bw] > fc["d_ab"] + 1.0:
                sub = "away"
        if sub is None:
            continue
        between = False
        if fc["D"] is not None:
            dseg, uu = _seg_proj(_pos(scene, fc["D"], t), _pos(scene, b, t), _pos(scene, a, t))
            between = bool(dseg <= P["between_m"] and 0 < uu < 1)
        e = _event(scene, "fake_dho", {"hander": a, "receiver": b, "defender": fc["D"]}, t,
                   _win(scene, t, -0.6, 0)[0], _win(scene, t, 0, 1.0)[1], _pb(fc["d_ab"], P["approach_m"], fc["sig"]),
                   dict(screen_kind="fake_handoff", sub_label=sub, t_c=int(t), d_ab_m=fc["d_ab"],
                        defender_between=between))
        if e:
            out.append(e)
    return out


def detect_dho_keep(scene, **params) -> list:
    """dho_keep: handoff approach without transfer, then the hander drives with the ball."""
    P, Pf = prm("dho_keep", params), prm("fake_dho")
    out = []
    for fc in _fake_candidates(scene):
        a, t = fc["a"], fc["t_c"]
        r = _kv(scene, a)["r"]
        n15 = frames(0.5)
        start = None
        for t0 in range(t, _win(scene, t, 0, P["keep_s"])[1] + 1):
            if t0 + n15 < scene.n and r[t0 + n15] - r[t0] <= -P["keep_dr_m"] and _holds(scene, a, t0, t0 + n15) >= n15 // 2:
                start = t0
                break
        if start is None:
            continue
        e = _event(scene, "dho_keep", {"hander": a, "receiver": fc["b"]}, t, _win(scene, t, -0.6, 0)[0], start + n15,
                   _pb(fc["d_ab"], Pf["approach_m"], fc["sig"]),
                   dict(screen_kind="fake_handoff", sub_label="keep", drive_start=int(start), d_ab_m=fc["d_ab"]))
        if e:
            out.append(e)
    return out


def detect_handoff_chain(scene, **params) -> list:
    """handoff_chain: get, handback, zoom (Chicago), miami, weave."""
    P = prm("handoff_chain", params)
    dhos = {(e.actors["hander"], e.actors["receiver"], e.t0): e for e in detect_dho(scene)}
    xf = _transfers(scene)
    out = []

    def emit(chain, actors, t0, a, b, p, extra):
        e = _event(scene, "handoff_chain", actors, t0, a, b, p, dict(chain=chain, **extra))
        if e:
            out.append(e)

    for x in xf:
        if x["type"] not in ("pass", "pitch"):
            continue
        a, b = x["frm"], x["to"]
        for (h, rcv, t), ev in dhos.items():
            dt = (t - x["catch"]) * DT
            if h == b and rcv == a and P["get_lo_s"] <= dt <= P["get_hi_s"]:
                emit("get", {"a": a, "b": b}, x["release"], x["release"], t, ev.conf, dict(dho_frame=int(t)))
        for y in xf:
            # both legs are real passes: raw-ball air time >= handback_min_air_s (SCR-T22; holder flicker at sigma_p 0.5)
            if y["frm"] == b and y["to"] == a and 0 < (y["catch"] - x["catch"]) * DT <= P["handback_s"] \
                    and P["handback_min_air_s"] <= y["air_s"] <= P["handback_air_s"] \
                    and x["air_s"] >= P["handback_min_air_s"] \
                    and (np.isfinite(y["travel_m"]) and y["travel_m"] <= P["handback_travel_m"]) \
                    and _r_at(scene, a, y["catch"]) >= P["handback_r_m"] and _r_at(scene, b, y["release"]) >= P["handback_r_m"]:
                emit("handback", {"a": a, "b": b}, x["release"], x["release"], y["catch"], 1.0, {})
    for r in _screens(scene, "off_ball"):
        if not (_is_down(scene, r) or _is_pin_down(scene, r)):
            continue
        for (h, rcv, t), ev in dhos.items():
            if rcv == r.u and 0 < (t - r.ts) * DT <= P["zoom_s"]:
                emit("zoom", {"a": h, "b": r.u, "screener": r.s}, r.ts, min(r.stop.a, r.ts), t, r.p * ev.conf,
                     dict(dho_frame=int(t)))
    for (h, rcv, t), ev in dhos.items():
        for r in _screens(scene, "on_ball"):
            if r.s == h and r.u == rcv and 0 < (r.ts - t) * DT <= P["miami_s"]:
                emit("miami", {"a": h, "b": rcv}, t, t, r.ts, ev.conf * r.p, dict(screen_frame=int(r.ts)))
    wv = sorted([ev for ev in dhos.values()
                 if P["weave_r_lo_m"] <= np.hypot(*_pos(scene, ev.actors["hander"], ev.t0)) <= P["weave_r_hi_m"]
                 and _m_deg(*_pos(scene, ev.actors["hander"], ev.t0)) >= P["weave_m_min"]], key=lambda e: e.t0)
    for e1, e2 in zip(wv, wv[1:]):
        if (e2.t0 - e1.t0) * DT <= P["weave_s"]:
            emit("weave", {"a": e1.actors["hander"], "b": e1.actors["receiver"]}, e1.t0, e1.t0, e2.t0,
                 e1.conf * e2.conf, dict(n_dho=2))
    return out


# --------------------------------------------------------------------------------------
# Detectors: legality hints
# --------------------------------------------------------------------------------------
def detect_moving_screen_hint(scene, **params) -> list:
    """moving_screen_hint: contact with a defender while the screener is confidently moving into him."""
    P = prm("moving_screen_hint", params)
    Pst, Pi = prm("screen_stationarity"), prm("screen_interaction")
    hold = _holder(scene)
    out = []
    for s in scene.offense:
        ks = scene.k(s)
        for D in scene.defense:
            dd = _dist(scene, s, D)
            last = -10**9
            for t in range(frames(0.7), scene.n - frames(0.7)):
                if not (np.isfinite(dd[t]) and dd[t] == np.nanmin(dd[t - 6:t + 7]) and _med(dd, t) <= P["contact_m"]):
                    continue
                if t - last < frames(1.0) or hold[t] == s or _guard_of(scene, D, _cl(scene, t - frames(1.0)))[0] == s:
                    continue
                n15 = int(Pst["min_ls_frames"])
                wa = _cl(scene, t - frames(0.1) - n15 // 2)
                wb = _cl(scene, wa + n15 - 1)
                st = _stop_stats(scene, ks, s, wa, wb, Pst)
                p_mov = 1.0 - rice_below(st.v_ls, Pst["loose_v_mps"], st.sigma)
                if p_mov < P["p_moving"]:
                    continue
                # velocity toward the defender before contact: mean of v(t') . unit(D(t') - s(t')) over the approach
                aa, ab = _win(scene, t, -P["along_pre_s"], -P["along_post_s"])
                along = float(np.nanmean([np.array([ks.vx[k], ks.vy[k]]) @ _unit(_pos(scene, D, k) - _pos(scene, s, k))
                                          for k in range(aa, ab + 1)]))
                if not along >= P["along_n_mps"]:
                    continue
                # the defender is moving into the screener's path (SCR-T20: not two players arriving side by side)
                kD = scene.k(D)
                ca_, cb_ = _win(scene, t, -P["along_pre_s"], -P["along_post_s"])
                spD = float(np.hypot(*_mean_v(scene, D, ca_, cb_)))
                vD = float(np.nanmean([np.array([kD.vx[k], kD.vy[k]]) @ _unit(_pos(scene, s, k) - _pos(scene, D, k))
                                       for k in range(ca_, cb_ + 1)]))
                if not (spD >= P["def_speed_mps"] and vD >= P["def_closing_mps"]):
                    continue
                v = _mean_v(scene, s, *_win(scene, t, -0.3, 0.1))
                it = _interaction(scene, s, s, D, t, _med(dd, t), _pos(scene, s, t), _unit(v), Pi)
                if not (it["delay"] or it["deflect"]):
                    continue
                last = t
                e = _event(scene, "moving_screen_hint", {"screener": s, "defender": D}, t, wa, wb,
                           p_mov * _pb(_med(dd, t), P["contact_m"], _sigd(scene, s, D, t)),
                           dict(moving_screen_hint=True, p_moving=p_mov, v_ls_mps=st.v_ls, v_along_n_mps=along,
                                d_sD_min=_med(dd, t), delay=it["delay"], deflect=it["deflect"]))
                if e:
                    out.append(e)
    return out


def detect_blind_screen_hint(scene, **params) -> list:
    """blind_screen_hint: blind-screen spacing hints (Rule 4-35.3) and boundary-parallel screens (4-35.7)."""
    P = prm("blind_screen_hint", params)
    out = []
    recs = [r for r in _records(scene) if r.m["merged_into"] is None]
    for r in recs:
        a = r.stop.a
        kD = scene.k(r.D)
        spD = _med(_kv(scene, r.D)["speed"], a)
        if spD >= P["facing_speed_mps"]:
            facing = np.array([kD.vx[a], kD.vy[a]])
        else:
            bp = _pos(scene, "ball", a)
            mid = (_pos(scene, r.u, a) + bp) / 2 if _fin(*bp) else _pos(scene, r.u, a)
            facing = mid - _pos(scene, r.D, a)
        fa = _ang(facing, _pos(scene, r.s, a) - _pos(scene, r.D, a))
        d_a = _med(_dist(scene, r.s, r.D), a)
        if not (np.isfinite(fa) and np.isfinite(d_a)):
            continue
        # outside the visual field with probability >= blind_p_min (SCR-T14): the direction D -> s has an angular
        # sigma of about sigma_d / d (both ends noisy: x sqrt 2); a point test fired on any side-behind screen
        sig_ang = math.degrees(_sigd(scene, r.s, r.D, a) / max(d_a, 0.1)) * math.sqrt(2)
        p_blind = _pa(fa, P["blind_deg"], sig_ang)
        if p_blind < P["blind_p_min"]:
            continue
        d_c = min(d_a, r.m["d_sD_ts"])  # contact at the stop onset or at t_s (5-frame medians)
        contact = d_c <= prm("screen_set")["contact_likely_m"]
        hint = None
        if spD < P["facing_speed_mps"] and d_a < P["step_m"] and contact:
            hint = "blind_no_step"
        elif spD >= P["facing_speed_mps"]:
            close = max(0.0, float(mvlib.closing_speed(scene.k(r.s), kD)[a]))
            if d_a < P["step_m"] + P["stride_s"] * close and contact:
                hint = "too_close_moving"
        if hint is None:
            continue
        sig = _sigd(scene, r.s, r.D, a)
        e = _event(scene, "blind_screen_hint", {"screener": r.s, "defender": r.D}, a, a, max(r.stop.b, r.ts),
                   _pb(d_a, P["step_m"], sig) * _pb(d_c, prm("screen_set")["contact_likely_m"], sig),
                   dict(hint=hint, blind=True, facing_deg=fa, p_blind=p_blind, d_at_onset_m=d_a, step_m_unverified=True))
        if e:
            out.append(e)
    # boundary-parallel pairs
    for i, r1 in enumerate(recs):
        for r2 in recs[i + 1:]:
            if r1.s == r2.s or abs(r1.ts - r2.ts) > frames(0.5):
                continue
            p1, p2 = np.array(r1.m["P_s"]), np.array(r2.m["P_s"])
            if not (_in("screen_boundary_6ft_band", *p1) and _in("screen_boundary_6ft_band", *p2)):
                continue
            if np.hypot(*(p1 - p2)) > P["mutual_m"]:
                continue
            line = p2 - p1
            near_side = SIDE_X - max(abs(p1[0]), abs(p2[0])) < min(p1[1], p2[1]) - END_Y
            bound = np.array([0.0, 1.0]) if near_side else np.array([1.0, 0.0])
            ang = _ang(line, bound)
            ang = min(ang, 180 - ang)
            if ang > P["parallel_deg"] or not (r1.m["contact_class"] == "likely" or r2.m["contact_class"] == "likely"):
                continue
            e = _event(scene, "blind_screen_hint", {"screener": r1.s, "screener_2": r2.s, "defender": r1.D}, r1.ts,
                       min(r1.stop.a, r2.stop.a), max(r1.stop.b, r2.stop.b), min(r1.p_set, r2.p_set),
                       dict(hint="boundary_parallel", angle_to_boundary_deg=ang))
            if e:
                out.append(e)
    return out


def detect_screen_pose_legality(scene, **params) -> list:
    """screen_pose_legality: needs pose keypoints (wide stance, leaning, tripping, forcing through); returns []."""
    return []


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------
DETECTORS = {
    "screen_set": detect_screen_set,
    "screen": detect_screen,
    "screen_moment": detect_screen_moment,
    "screen_read": detect_screen_read,
    "screen_interaction": detect_screen_interaction,
    "screener_post_action": detect_screener_post_action,
    "ball_screen": detect_ball_screen,
    "high_ball_screen": detect_high_ball_screen,
    "side_ball_screen": detect_side_ball_screen,
    "step_up_screen": detect_step_up_screen,
    "flip_screen": detect_flip_screen,
    "re_screen": detect_re_screen,
    "slip_screen": detect_slip_screen,
    "ghost_screen": detect_ghost_screen,
    "fake_screen": detect_fake_screen,
    "drag_screen": detect_drag_screen,
    "double_drag": detect_double_drag,
    "spain_pnr": detect_spain_pnr,
    "double_ball_screen": detect_double_ball_screen,
    "ram_screen": detect_ram_screen,
    "veer_screen": detect_veer_screen,
    "ball_screen_coverage": detect_ball_screen_coverage,
    "off_ball_screen_coverage": detect_off_ball_screen_coverage,
    "down_screen": detect_down_screen,
    "pin_down": detect_pin_down,
    "flare_screen": detect_flare_screen,
    "back_screen": detect_back_screen,
    "ucla_screen": detect_ucla_screen,
    "rip_screen": detect_rip_screen,
    "cross_screen": detect_cross_screen,
    "stagger_screen": detect_stagger_screen,
    "double_screen": detect_double_screen,
    "elevator_screen": detect_elevator_screen,
    "hammer_screen": detect_hammer_screen,
    "flex_screen": detect_flex_screen,
    "zipper_screen": detect_zipper_screen,
    "iverson_screen": detect_iverson_screen,
    "wedge_screen": detect_wedge_screen,
    "shuffle_screen": detect_shuffle_screen,
    "screen_the_screener": detect_screen_the_screener,
    "off_ball_screen_other": detect_off_ball_screen_other,
    "dho": detect_dho,
    "fake_dho": detect_fake_dho,
    "dho_keep": detect_dho_keep,
    "handoff_chain": detect_handoff_chain,
    "moving_screen_hint": detect_moving_screen_hint,
    "blind_screen_hint": detect_blind_screen_hint,
    "screen_pose_legality": detect_screen_pose_legality,
}

# every item with a detector in the YAML must be registered here, and nothing else
assert {i for i, it in ITEMS.items() if it.get("detector")} == set(DETECTORS), "YAML/DETECTORS mismatch"


def detect_all(scene) -> dict:
    """Run every detector on one scene: {item id: [Event, ...]}."""
    return {k: f(scene) for k, f in DETECTORS.items()}
