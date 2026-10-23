"""Defensive movement detectors (family DEFENSIVE MOVEMENT; spec tooling, not the production labeller).

Implements config/movement_grammar/defense.yaml on top of mvlib (CA-RTS kinematics, MP rules) and the
named_spots relative entries (positions are never redefined here; this module only times the movements
between them). Every numeric parameter is read from the YAML at import (single source of truth);
keyword arguments override them per call (for calibration sweeps).

Frame: attacked-rim frame of the offence, metres, rim at (0, 0); the defence defends that rim. Time base:
29.97 fps, DT = 1001/30000 s; elapsed durations are (n_frames - 1) * DT.

Conventions shared by every detector (YAML globals and DM-RULE-03):
- sigma_rel: pair-distance sigma = max(mvlib.sigma_dist, k_floor x sigma_p). The floor is the measured AR(1)
  pair-distance error of MP-19 (0.24 m at sigma_p 0.3) scaled to the track noise (sigma_p and the smoother tier
  are recovered from the RTS covariance by noise_of), because the RTS covariance under-states correlated
  noise even after K_CAL.
- Speed thresholds refer to the CA-RTS smoothed speed (MP-04, q_j 30). Short efforts lose 15-40 % of their
  true peak in that smoother, so peak gates are calibrated to the smoothed signal (see each item).
- conf = P_cond x edge_factor(t0) x gap_factor(window), minimum over the actors (MP-16). P_cond is the
  product of per-gate probabilities p_below / p_above with window-mean features. Abstain (no event) when
  the observed share in the critical window is < q_obs_min.
- Upstream anchors (passes, shots, drives, screens, change of possession) belong to other families.
  derive_anchors() gives XY-only proxies; callers may pass anchors=... to supply real ones (a supplied key
  replaces the derived list for that key).
- Every Event carries attrs['reasons'] (gate values with thresholds) and, where classes compete,
  attrs['alternatives'] (class -> probability).
"""

from __future__ import annotations

import itertools
import math
import re
import sys
from pathlib import Path

import numpy as np
import yaml

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parents[3]
for _p in (_HERE.parent, _HERE.parents[1] / "named_spots"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import spotlib  # noqa: E402
from mvlib import (  # noqa: E402
    DT,
    HOLD_R,
    K_CAL,
    Q_DEFAULT,
    Q_HIGH_NOISE,
    Event,
    Scene,
    ca_rts,
    dist,
    edge_factor,
    frames,
    gap_factor,
    hysteresis,
    p_above,
    p_below,
    sigma_dist,
    window_conf,
)

CONFIG = _ROOT / "config" / "movement_grammar" / "defense.yaml"
SPEC = yaml.safe_load(CONFIG.read_text())
ITEMS = {it["id"]: it for it in SPEC["items"]}
GLOBAL = {k: v["value"] for k, v in SPEC["globals"]["params"].items()}
_, SPOTS = spotlib.load()
C = spotlib.C


def params_of(item_id: str) -> dict:
    """Parameter values of one YAML item (units are documented in the YAML)."""
    return {k: v["value"] for k, v in (ITEMS[item_id].get("params") or {}).items()}


def merged_params(*item_ids) -> dict:
    """YAML globals + the params of several items (later items win on a shared name)."""
    p = dict(GLOBAL)
    for it in item_ids:
        p.update(params_of(it))
    return p


def _setup(item_ids, scene, params):
    """Merge YAML globals + item params + call overrides; resolve anchors. Unknown names are an error.

    item_ids is one item id or a tuple of ids whose params the detector reads (e.g. ('show', 'ball_screen')), so
    every parameter the detector uses can be overridden per call (DEF-T19)."""
    ids = (item_ids,) if isinstance(item_ids, str) else tuple(item_ids)
    params = dict(params)
    anchors = params.pop("anchors", None)
    p = merged_params(*reversed(ids))  # the first id (the item itself) wins on a shared name
    bad = set(params) - set(p)
    if bad:
        raise TypeError(f"{ids[0]}: unknown parameter(s) {sorted(bad)}")
    p.update(params)
    return p, get_anchors(scene, anchors)


# --------------------------------------------------------------------------------------
# named_spots numbers read from the entries' expressions (positions are never redefined here, DEF-T20)
# --------------------------------------------------------------------------------------
def _expr_num(spot_id: str, before: str = "", after: str = "") -> float:
    """The number that follows `before` (or precedes `after`) in a named_spots expression; error if absent."""
    src = SPOTS[spot_id].d["expr"]
    pat = re.escape(before) + r"\s*(-?[0-9]*\.?[0-9]+)" if before else r"(-?[0-9]*\.?[0-9]+)\s*" + re.escape(after)
    m = re.search(pat, src)
    if not m:
        raise ValueError(f"named_spots {spot_id}: cannot read the number next to {before or after!r}")
    return float(m.group(1))


_TAU_HI = "**2)) <="
SPOT_NUM = {
    "deny": dict(
        perp_max=_expr_num("deny_on_the_line", "seg_dist((x,y),(ax_,ay_),(bx,by)) <="),
        tau_lo=_expr_num("deny_on_the_line", after="<= (((x-ax_)"),
        tau_hi=_expr_num("deny_on_the_line", _TAU_HI),
        dist_max=_expr_num("deny_on_the_line", "hypot(x-ax_,y-ay_) <="),
    ),
    "face_guard": dict(
        perp_max=_expr_num("face_guard", "seg_dist((x,y),(ax_,ay_),(bx,by)) <="),
        tau_lo=_expr_num("face_guard", after="<= (((x-ax_)"),
        tau_hi=_expr_num("face_guard", _TAU_HI),
        dist_max=_expr_num("face_guard", "hypot(x-ax_,y-ay_) <="),
    ),
    "box_out": dict(
        dist_max=_expr_num("box_out_position", "hypot(x-ax_,y-ay_) <="),
        line_max=_expr_num("box_out_position", "seg_dist((x, y), (ax_, ay_), (0, 0)) <="),
    ),
    "post": dict(r_max=_expr_num("post_full_front", "hypot(ax_, ay_) <=")),
    "protect_rim": dict(r_max=_expr_num("transition_protect_rim", "r <=")),
    "stop_ball": dict(dist_max=_expr_num("transition_stop_ball", "hypot(x-hx,y-hy) <=")),
}


# --------------------------------------------------------------------------------------
# Track noise level (DEF-T13, DEF-T14): sigma_p and smoother tier recovered from the RTS covariance
# --------------------------------------------------------------------------------------
def _noise_table():
    """Steady-state RTS position sigma and velocity/position sigma ratio per (sigma_p, q) on mvlib's own filter."""
    grid = np.linspace(0.02, 1.2, 60)
    tab = {}
    for q in (Q_DEFAULT, Q_HIGH_NOISE):
        sp, ratio = [], []
        for s in grid:
            _, P, _ = ca_rts(np.zeros(61), np.full(61, s * s), q)
            sp.append(math.sqrt(P[30, 0, 0]))
            ratio.append(math.sqrt(P[30, 1, 1] / P[30, 0, 0]))
        tab[q] = (np.array(sp), np.array(ratio))
    return grid, tab


_NOISE_GRID, _NOISE_TAB = _noise_table()


def noise_of(k) -> tuple[float, float]:
    """(sigma_p estimate, smoother q) of one Kin. The Scene keeps no raw sigma_p, so it is inverted from the median
    steady-state RTS covariance of the observed interior frames; q (mvlib switches to Q_HIGH_NOISE when the median
    sigma_p >= 0.45) is the one whose velocity / position sigma ratio matches. Cached on k.extra."""
    if "noise" in k.extra:
        return k.extra["noise"]
    m = (k.state == "observed") & (k.edge >= 15) & ~np.isnan(k.var_p)
    if m.sum() < 5:
        m = ~np.isnan(k.var_p)
    if not m.any():
        k.extra["noise"] = (0.3, Q_DEFAULT)
        return k.extra["noise"]
    sp = float(np.median(np.sqrt(k.var_p[m])))
    ratio = float(np.median(np.sqrt(k.var_v[m] / k.var_p[m])))
    best = None
    for q, (tsp, trat) in _NOISE_TAB.items():
        s = float(np.interp(sp, tsp, _NOISE_GRID))
        err = abs(math.log(ratio / float(np.interp(s, _NOISE_GRID, trat))))
        if best is None or err < best[0]:
            best = (err, s, q)
    k.extra["noise"] = (best[1], best[2])
    return k.extra["noise"]


def high_noise(*ks) -> bool:
    """True when any of the tracks was smoothed in mvlib's high-noise tier (q = Q_HIGH_NOISE)."""
    return any(noise_of(k)[1] == Q_HIGH_NOISE for k in ks if k is not None)


def tier_param(p, name, *ks):
    """Parameter `name`, or its `<name>_q10` variant when a track was smoothed with q = 10 (DEF-T13)."""
    alt = name + "_q10"
    return p[alt] if alt in p and high_noise(*ks) else p[name]


def rel_floor(p, *ks) -> float:
    """MP-19 floor of the pair-distance sigma scaled to the measured noise (DEF-T14):
    max(sigma_rel_min, k_floor x mean sigma_p of the tracks)."""
    s = [noise_of(k)[0] for k in ks if k is not None]
    return max(p["sigma_rel_min"], p["k_floor"] * (float(np.mean(s)) if s else 0.3))


# --------------------------------------------------------------------------------------
# Small numeric helpers
# --------------------------------------------------------------------------------------
def runs(mask) -> list[tuple[int, int]]:
    """Inclusive (a, b) runs where mask is True."""
    m = np.asarray(mask, dtype=bool)
    out, a = [], None
    for i, v in enumerate(m):
        if v and a is None:
            a = i
        elif not v and a is not None:
            out.append((a, i - 1))
            a = None
    if a is not None:
        out.append((a, len(m) - 1))
    return out


def _cache(scene):
    if not hasattr(scene, "_dm"):
        scene._dm = {}
    return scene._dm


def _clip(t, n):
    return int(min(max(t, 0), n - 1))


def mean_xy(k, t, half=2):
    """5-frame mean smoothed position around t (DM-RULE-03 window means), NaN-safe."""
    a, b = max(0, t - half), min(len(k.x), t + half + 1)
    with np.errstate(all="ignore"):
        return float(np.nanmean(k.x[a:b])), float(np.nanmean(k.y[a:b]))


def mean_val(arr, t, half=2):
    a, b = max(0, t - half), min(len(arr), t + half + 1)
    seg = np.asarray(arr[a:b], dtype=float)
    seg = seg[~np.isnan(seg)]
    return float(np.mean(seg)) if len(seg) else float("nan")


def sigma_rel(ka, kb, p):
    """Pair-distance sigma per frame with the noise-scaled MP-19 floor (see module docstring, DEF-T14)."""
    return np.maximum(sigma_dist(ka, kb), rel_floor(p, ka, kb))


def sigma_own(k, a, b, p):
    """Sigma of ONE track's displacement over [a, b] (chord, excursion peak, own r change): K_CAL x sqrt(2 x mean
    var_p) floored at the one-track rel_floor (k_floor x sigma_p). Measured on the harness scenes (loop 2, NEW-R1):
    one-track displacement error over 1.0 s is 0.84 / 0.80 / 0.74 sigma_p per axis at sigma_p 0.2 / 0.3 / 0.5, the
    size of the pair-distance LEVEL error (0.82 / 0.78 / 0.74 sigma_p), not sqrt(2) x it."""
    with np.errstate(all="ignore"):
        v = float(np.nanmean(k.var_p[max(0, a) : max(a, b) + 1]))
    return max(K_CAL * math.sqrt(2 * v) if np.isfinite(v) else 0.0, rel_floor(p, k))


def hyst_h(sig, p):
    """named_spots relative hysteresis half-width h = max(0.25 m, 0.75 sigma_rel)."""
    return max(p["hyst_h_min"], p["hyst_k_sigma"] * float(sig))


def v_to(k, qx, qy):
    """Velocity component of k toward the point (qx, qy) (arrays or scalars); positive = approaching."""
    dx, dy = qx - k.x, qy - k.y
    d = np.hypot(dx, dy)
    with np.errstate(all="ignore"):
        return (k.vx * dx + k.vy * dy) / np.where(d > 0, d, np.nan)


def seg_dist_arr(px, py, ax, ay, bx, by):
    """Vectorised distance from P to segment A-B and the lane fraction tau (0 at A, 1 at B)."""
    ux, uy = bx - ax, by - ay
    L = ux * ux + uy * uy
    with np.errstate(all="ignore"):
        tau = ((px - ax) * ux + (py - ay) * uy) / np.where(L > 0, L, np.nan)
    tc = np.clip(np.nan_to_num(tau, nan=0.0), 0.0, 1.0)
    return np.hypot(px - (ax + tc * ux), py - (ay + tc * uy)), tau


def angle_at(ax, ay, px, py, qx, qy):
    """Angle in degrees at A between A->P and A->Q (vectorised)."""
    ux, uy, wx, wy = px - ax, py - ay, qx - ax, qy - ay
    return np.degrees(np.arctan2(np.abs(ux * wy - uy * wx), ux * wx + uy * wy))


def _quality(scene, oids, t0, a, b, p):
    """MP-16 c_edge x c_gap (minimum over actors) and the observed share q_obs in [a, b]."""
    c, q = 1.0, 1.0
    for o in oids:
        k = scene.kins.get(o) if o != "ball" else scene.ball
        if k is None:
            continue
        c = min(c, edge_factor(k, _clip(t0, scene.n)) * gap_factor(k, a, b))
        st = k.state[a : b + 1]
        q = min(q, float(np.mean(st == "observed")) if len(st) else 0.0)
    return c, q


def _abstain(scene, reason, kind, actors, t0, start, end):
    """Record an abstained candidate (loop 4: abstentions are reported by detect_all, never silently empty)."""
    key = (reason, kind, tuple(sorted((k, v) for k, v in actors.items() if isinstance(v, str))), int(t0), int(end))
    _cache(scene).setdefault("abstained", {})[key] = (int(start), dict(actors))


def defense_has_ball(scene):
    """Per frame: True while the labelled DEFENCE has possession (loop 4, L4-POSSESSION).

    Control at a frame = team of the player nearest the raw ball within mvlib.HOLD_R and nearer than every opponent by
    max(possession_margin_min, possession_margin_k x median sigma_p); none while the ball XY is over a rim
    (rim_ball_r). Possession changes to a team that
    controls the ball on >= possession_share of the frames of a possession_hold_s window (flicker-robust: a tightly guarded
    dribble or a deflection is no change); the change is dated at the new team's first control frame in that window. The scene contract says
    the offence has the ball; real chunks that span a change of possession (SportVU clock-running stretches, a video clip
    cut across a rebound or steal) break it, and no defensive label is defined while the 'defence' attacks."""
    cache = _cache(scene)
    if "dposs" in cache:
        return cache["dposs"]
    n = scene.n
    out = np.zeros(n, dtype=bool)
    braw = scene.ball_raw if scene.ball_raw is not None else (
        (scene.ball.x, scene.ball.y) if scene.ball is not None else None)
    if braw is None or not scene.defense:
        cache["dposs"] = out
        return out
    bx, by = np.asarray(braw[0], dtype=float), np.asarray(braw[1], dtype=float)
    near = {}
    for grp, lab in ((scene.offense, 1), (scene.defense, 2)):
        dmin = np.full(n, np.inf)
        for o in grp:
            k = scene.kins[o]
            with np.errstate(all="ignore"):
                dmin = np.fmin(dmin, np.nan_to_num(np.hypot(bx - k.x, by - k.y), nan=np.inf))
        near[lab] = dmin
    # control needs a margin over the nearest opponent (a tight on-ball defender 0.8-1.0 m from the handler is not in
    # control when tracker noise moves the ball XY toward him), scaled to the measured track noise
    sig = float(np.median([noise_of(scene.kins[o])[0] for o in list(scene.offense) + list(scene.defense)]))
    margin = max(GLOBAL["possession_margin_min"], GLOBAL["possession_margin_k"] * sig)
    team = np.zeros(n, dtype=int)  # 0 none, 1 offence, 2 defence
    team[(near[1] <= HOLD_R) & (near[1] + margin <= near[2])] = 1
    team[(near[2] <= HOLD_R) & (near[2] + margin <= near[1])] = 2
    team[_near_rim(scene, GLOBAL["rim_ball_r"])] = 0  # ball over a rim (shot, rebound): nobody's control in XY
    hf = max(1, frames(GLOBAL["possession_hold_s"]))
    need = GLOBAL["possession_share"] * hf
    cO = np.concatenate([[0], np.cumsum(team == 1)])
    cD = np.concatenate([[0], np.cumsum(team == 2)])
    cur = 1
    for t in range(n):
        lo = max(0, t - hf + 1)
        if t - lo + 1 == hf:
            if cur == 1 and cD[t + 1] - cD[lo] >= need:
                cur = 2
                t1 = lo + int(np.argmax(team[lo : t + 1] == 2))
                out[t1 : t + 1] = True  # the change happened at the first defence control frame of the window
            elif cur == 2 and cO[t + 1] - cO[lo] >= need:
                cur = 1
                t1 = lo + int(np.argmax(team[lo : t + 1] == 1))
                out[t1 : t + 1] = False
        out[t] = cur == 2
    cache["dposs"] = out
    return out


def make_event(
    scene, p, kind, actors, t0, start, end, p_cond, reasons, alternatives=None, state=False, p_emit=None, **attrs
):
    """Build an Event with MP-16 confidence, or None when abstaining (q_obs) or P_emit < emit_p_min.

    p_emit (default p_cond) is the probability that the event exists; p_cond is the probability of this exact
    label. They differ for class labels: a closeout that surely happened with an ambiguous length class is
    emitted (p_emit high) with conf = P(closeout) x P(class) and the competing classes as alternatives.

    state=True marks a hold label (deny, post position, guard-two ...): when it starts at a segment edge it is
    left-censored, so the edge factor is taken at the first frame inside the hold that is >= 15 frames from
    the edge (the hold's existence is measured there, not its onset)."""
    p_emit = p_cond if p_emit is None else p_emit
    if not np.isfinite(p_emit) or p_emit < p["emit_p_min"]:
        return None
    start, end, t0 = int(start), int(end), int(t0)
    oids = [v for v in actors.values() if isinstance(v, str)]
    if defense_has_ball(scene)[_clip(t0, scene.n)]:
        # loop 4 L4-POSSESSION: the labelled defence controls the ball (change of possession not in the scene contract)
        _abstain(scene, "dposs", kind, actors, t0, start, end)
        return None
    if kind in p["high_noise_abstain_kinds"] and high_noise(*(scene.kins.get(o) for o in oids)):
        # loop 2 HIGH-NOISE-TIER: labels below P 0.6 on the harness in the q = 10 tier abstain by default; loop 4 reports
        # the abstention (detect_all 'abstained') instead of an empty list
        _abstain(scene, "q10", kind, actors, t0, start, end)
        return None
    t_q = t0
    if state:
        ks = [scene.kins[o] for o in oids if o in scene.kins]
        while t_q < end and any(k.edge[t_q] < 15 for k in ks):
            t_q += 1
        attrs["left_censored"] = bool(t_q > t0)
    c, q = _quality(scene, oids, t_q, start, end, p)
    if q < p["q_obs_min"]:
        return None
    if p_cond * c <= p["conf_abstain_eps"]:
        return None  # DEF-T21: t0 inside the 5-frame segment edge (edge factor 0) -> abstain, no phantom label
    attrs = dict(attrs)
    attrs["reasons"] = reasons
    attrs["p_cond"] = round(float(p_cond), 4)
    attrs["p_emit"] = round(float(p_emit), 4)
    attrs["q_obs"] = round(q, 3)
    if alternatives:
        attrs["alternatives"] = {k_: round(float(v), 4) for k_, v in alternatives.items()}
    return Event(kind, dict(actors), t0, start, end, float(np.clip(p_cond * c, 0.0, 1.0)), attrs)


def band_probs(x, sig, bands):
    """DM-RULE-03 band classes: P(lo <= X < hi) under N(x, sig), renormalised over the bands."""
    pr = {}
    for name, (lo, hi) in bands.items():
        phi_hi = 1.0 if hi is None else float(p_below(x, hi, sig))
        phi_lo = 0.0 if lo is None else float(p_below(x, lo, sig))
        pr[name] = max(0.0, phi_hi - phi_lo)
    s = sum(pr.values())
    return {k: v / s for k, v in pr.items()} if s > 0 else pr


def _fmt(name, val, op, thr, unit):
    return f"{name} {val:.2f} {unit} {op} {thr} {unit}"


# --------------------------------------------------------------------------------------
# Ball position and matchup backbone (DM-RULE-02)
# --------------------------------------------------------------------------------------
def ball_xy(scene):
    """Ball position per frame: smoothed ball, else the holder, else linear interpolation (flights)."""
    cache = _cache(scene)
    if "ball_xy" in cache:
        return cache["ball_xy"]
    n = scene.n
    bx = np.full(n, np.nan) if scene.ball is None else scene.ball.x.copy()
    by = np.full(n, np.nan) if scene.ball is None else scene.ball.y.copy()
    for t in range(n):
        h = scene.holder[t]
        if h is not None and np.isnan(bx[t]):
            bx[t], by[t] = scene.kins[h].x[t], scene.kins[h].y[t]
    ok = ~np.isnan(bx)
    if ok.sum() >= 2:
        idx = np.arange(n)
        bx = np.interp(idx, idx[ok], bx[ok])
        by = np.interp(idx, idx[ok], by[ok])
    cache["ball_xy"] = (bx, by)
    return bx, by


def _logsumexp(a, axis):
    m = np.max(a, axis=axis, keepdims=True)
    return np.squeeze(m, axis=axis) + np.log(np.sum(np.exp(a - m), axis=axis))


def matchup_posterior(scene, p=None):
    """Per-defender HMM posterior over the offensive players (Franks et al. emission, forward-backward).

    Emission: D ~ N(mu, s2 I) with mu = w_o*A + w_b*B + (1 - w_o - w_b)*R (R = rim = origin), or
    mu = w_o_holder*A when A holds the ball; s2 = sigma_fit^2 + K_CAL^2 var_p(D) + w^2 K_CAL^2 var_p(A).
    Frames where A or D is beyond half court use sigma_fit_transition (Franks fitted half court only).
    Transition: stay rho (per 29.97 fps frame), the rest shared equally. Returns
    {'post': {d: (m, n) array}, 'top1': {d: object array of attacker ids or None}, 'attackers': list}.
    """
    p = {**GLOBAL, **params_of("matchup"), **(p or {})}
    key = ("matchup",) + tuple(
        p[k] for k in ("w_o", "w_b", "w_o_holder", "rho_stay", "sigma_fit", "sigma_fit_transition")
    )
    cache = _cache(scene)
    if key in cache:
        return cache[key]
    off = list(scene.offense)
    m, n = len(off), scene.n
    bx, by = ball_xy(scene)
    X = np.array([scene.kins[a].x for a in off])
    Y = np.array([scene.kins[a].y for a in off])
    VP = np.array([scene.kins[a].var_p for a in off])
    hold = np.array([[scene.holder[t] == a for t in range(n)] for a in off])
    bxf = np.where(np.isnan(bx)[None, :], X, bx[None, :])
    byf = np.where(np.isnan(by)[None, :], Y, by[None, :])
    w_o, w_b, w_h = p["w_o"], p["w_b"], p["w_o_holder"]
    mux = np.where(hold, w_h * X, w_o * X + w_b * bxf)
    muy = np.where(hold, w_h * Y, w_o * Y + w_b * byf)
    rho = p["rho_stay"]
    logT = np.full((m, m), math.log((1 - rho) / max(1, m - 1)) if m > 1 else 0.0)
    np.fill_diagonal(logT, math.log(rho) if m > 1 else 0.0)
    post, top1 = {}, {}
    for d in scene.defense:
        k = scene.kins[d]
        trans = (Y > C["HALF_Y"]) | (k.y > C["HALF_Y"])[None, :]
        sf = np.where(trans, p["sigma_fit_transition"], p["sigma_fit"])
        var = (
            sf**2
            + K_CAL**2 * np.nan_to_num(k.var_p, nan=0.0)[None, :]
            + (w_o * K_CAL) ** 2 * np.nan_to_num(VP, nan=0.0)
        )
        ll = -((k.x[None, :] - mux) ** 2 + (k.y[None, :] - muy) ** 2) / (2 * var) - np.log(var)
        ll = ll.T  # (n, m)
        bad = np.isnan(ll)
        if bad.any():
            colmean = np.nanmean(np.where(bad, np.nan, ll), axis=1, keepdims=True) if (~bad).any() else 0.0
            ll = np.where(bad, np.nan_to_num(colmean, nan=0.0) * np.ones_like(ll), ll)
        la = np.zeros((n, m))
        la[0] = -math.log(m) + ll[0]
        for t in range(1, n):
            la[t] = ll[t] + _logsumexp(la[t - 1][:, None] + logT, axis=0)
        lb = np.zeros((n, m))
        for t in range(n - 2, -1, -1):
            lb[t] = _logsumexp(logT + (ll[t + 1] + lb[t + 1])[None, :], axis=1)
        g = la + lb
        g = np.exp(g - _logsumexp(g, axis=1)[:, None])
        valid = ~np.isnan(k.x)
        post[d] = g.T
        top1[d] = np.array([off[int(np.argmax(g[t]))] if valid[t] else None for t in range(n)], dtype=object)
    out = {"post": post, "top1": top1, "attackers": off}
    cache[key] = out
    return out


def p_match(scene, d, a):
    """Posterior P(D guards A) per frame."""
    mu = matchup_posterior(scene)
    return mu["post"][d][mu["attackers"].index(a)]


def on_ball_defender(scene, h, t):
    """Defender with the highest matchup posterior on attacker h at frame t."""
    mu = matchup_posterior(scene)
    j = mu["attackers"].index(h)
    best, bp = None, -1.0
    for d in scene.defense:
        v = mu["post"][d][j, t]
        if v > bp:
            best, bp = d, v
    return best


def joint_top1(scene):
    """Per-frame one-to-one defender -> attacker assignment (DEF-T17): minimum total -log posterior over all
    defenders (exhaustive over permutations; <= 5 x 5), flicker shorter than matchup.flicker_s absorbed.
    The per-defender HMM has no one-to-one constraint, so a nail helper near the handler is matched to the
    handler; the joint assignment gives him his own man. Returns {d: object array of attacker ids or None}."""
    cache = _cache(scene)
    if "joint_top1" in cache:
        return cache["joint_top1"]
    mu = matchup_posterior(scene)
    off, dfn, n = mu["attackers"], list(scene.defense), scene.n
    raw = {d: np.array([None] * n, dtype=object) for d in dfn}
    perms_cache = {}
    for t in range(n):
        ds = [d for d in dfn if mu["top1"][d][t] is not None]
        if not ds or not off:
            continue
        cost = np.array([[-math.log(max(float(mu["post"][d][j, t]), 1e-12)) for j in range(len(off))] for d in ds])
        nd, na = cost.shape
        key = (nd, na)
        if key not in perms_cache:
            perms_cache[key] = np.array(list(itertools.permutations(range(max(nd, na)), min(nd, na))), dtype=int)
        P = perms_cache[key]
        if nd <= na:
            tot = cost[np.arange(nd)[None, :], P].sum(axis=1)
            best = P[int(np.argmin(tot))]
            for i, d in enumerate(ds):
                raw[d][t] = off[best[i]]
        else:
            tot = cost[P, np.arange(na)[None, :]].sum(axis=1)
            best = P[int(np.argmin(tot))]
            for j, i in enumerate(best):
                raw[ds[i]][t] = off[j]
    fl = frames(params_of("matchup")["flicker_s"])
    out = {}
    for d in dfn:
        arr = np.array([None] * n, dtype=object)
        for a, b, att in _runs_absorb(list(raw[d]), fl):
            arr[a : b + 1] = att
        out[d] = arr
    cache["joint_top1"] = out
    return out


def _top1_runs(scene, d, min_frames, mu=None):
    """Runs of D's top-1 attacker with flicker shorter than min_frames absorbed into the previous run."""
    return _runs_absorb((mu or matchup_posterior(scene))["top1"][d], min_frames)


def _runs_absorb(top, min_frames):
    """Runs of a per-frame label sequence with runs shorter than min_frames absorbed into a neighbour."""
    rs = []
    for t, a in enumerate(top):
        if rs and rs[-1][2] == a:
            rs[-1][1] = t
        else:
            rs.append([t, t, a])
    changed = True
    while changed and len(rs) > 1:
        changed = False
        for i, r in enumerate(rs):
            if r[1] - r[0] + 1 < min_frames:
                j = i - 1 if i > 0 else i + 1
                rs[j][0], rs[j][1] = min(rs[j][0], r[0]), max(rs[j][1], r[1])
                rs.pop(i)
                merged = []
                for q in rs:
                    if merged and merged[-1][2] == q[2]:
                        merged[-1][1] = q[1]
                    else:
                        merged.append(q)
                rs = merged
                changed = True
                break
    return [tuple(r) for r in rs]


# --------------------------------------------------------------------------------------
# Upstream anchors (DM-RULE-04): XY-only proxies, replaceable by real upstream events
# --------------------------------------------------------------------------------------
ANCHOR_KEYS = ("pass", "shot", "drive", "middle_dribble", "screen", "cop")


def _holder_runs(scene, merge_gap):
    h = list(scene.holder)
    rs = []
    for t, v in enumerate(h):
        if rs and rs[-1][2] == v:
            rs[-1][1] = t
        else:
            rs.append([t, t, v])
    # bridge short None flicker inside one holder's possession
    out = []
    for r in rs:
        if out and r[2] is None and r[1] - r[0] + 1 <= merge_gap and len(out) and out[-1][2] is not None:
            nxt = [q for q in rs if q[0] == r[1] + 1]
            if nxt and nxt[0][2] == out[-1][2]:
                out[-1][1] = r[1]
                continue
        if out and out[-1][2] == r[2]:
            out[-1][1] = r[1]
        else:
            out.append(list(r))
    return [tuple(r) for r in out]


def derive_anchors(scene):
    """XY-only anchor proxies (cached). Shots and passes come from holder runs (ball flight ending at the rim
    = shot); drives from the holder's v_r; middle dribbles from the holder moving toward the middle; screens
    from a stationary teammate within reach of the on-ball defender. Change of possession is never derived."""
    cache = _cache(scene)
    if "anchors" in cache:
        return cache["anchors"]
    p = {**GLOBAL, **params_of("anchors")}
    A = {k: [] for k in ANCHOR_KEYS}
    hr = _holder_runs(scene, p["holder_merge_gap_frames"])
    bk = scene.ball
    for i, (a, b, h) in enumerate(hr):
        if h is None:
            continue
        # shot: the next run is a flight whose smoothed ball reaches the rim area
        if i + 1 < len(hr) and hr[i + 1][2] is None and bk is not None:
            fa, fb, _ = hr[i + 1]
            r = np.hypot(bk.x[fa : fb + 1], bk.y[fa : fb + 1])
            if np.any(~np.isnan(r)) and np.nanmin(r) <= p["shot_rim_r"]:
                A["shot"].append(dict(t_rel=b, shooter=h, t_rim=fa + int(np.nanargmin(r))))
                continue
        # pass: next holder run (after an optional flight) is another attacker
        j = i + 1
        if j < len(hr) and hr[j][2] is None:
            j += 1
        if j < len(hr) and hr[j][2] is not None and hr[j][2] != h:
            ka, kb = scene.kins[h], scene.kins[hr[j][2]]
            xa, xb = ka.x[b], kb.x[hr[j][0]]
            skip = bool(xa * xb < 0 and abs(xa) >= p["skip_abs_x"] and abs(xb) >= p["skip_abs_x"])
            A["pass"].append(dict(t_rel=b, t_catch=hr[j][0], passer=h, receiver=hr[j][2], skip=skip))
        # drive and middle dribble inside the holder run
        k = scene.kins[h]
        vr = np.nan_to_num(k.v_r[a : b + 1], nan=0.0)
        for ra, rb in runs(vr >= p["drive_v_r"]):
            if rb - ra + 1 >= frames(p["drive_min_s"]) and k.r[a + ra] - k.r[a + rb] >= p["drive_min_dr"]:
                t = ra
                while t > 0 and vr[t - 1] >= p["drive_backdate_v_r"]:
                    t -= 1  # back-date the drive start to where the move toward the rim began
                A["drive"].append(dict(t=a + t, handler=h))
        sp = np.nan_to_num(k.speed[a : b + 1], nan=0.0)
        for ra, rb in runs(sp >= p["move_v"]):
            if rb - ra + 1 >= frames(p["move_min_s"]) and abs(k.x[a + ra]) - abs(k.x[a + rb]) >= p["middle_dx"]:
                A["middle_dribble"].append(dict(t_s=a + ra, t_e=a + rb, handler=h, proxy=True))
    # screens (ball): teammate S stationary within reach of the on-ball defender while H is near
    for a, b, h in hr:
        if h is None or b - a < 6:
            continue
        kh = scene.kins[h]
        xb = [on_ball_defender(scene, h, t) for t in range(a, b + 1)]
        for s in scene.offense:
            if s == h:
                continue
            ks = scene.kins[s]
            dxb = np.array(
                [
                    math.hypot(ks.x[t] - scene.kins[xb[t - a]].x[t], ks.y[t] - scene.kins[xb[t - a]].y[t])
                    for t in range(a, b + 1)
                ]
            )
            dsh = np.hypot(ks.x[a : b + 1] - kh.x[a : b + 1], ks.y[a : b + 1] - kh.y[a : b + 1])
            cond = (np.nan_to_num(dxb, nan=9) <= p["screen_xball_r"]) & (np.nan_to_num(dsh, nan=9) <= p["screen_h_r"])
            for ra, rb in runs(cond):
                if rb - ra + 1 < 3:
                    continue
                t0 = a + ra + int(np.nanargmin(dxb[ra : rb + 1]))
                if mean_val(ks.speed, t0, 5) > p["screen_still_v"]:
                    continue
                pre = max(0, t0 - frames(p["screen_pre_s"]))
                prev = [x for x in A["screen"] if x["screener"] == s and x["handler"] == h]
                if prev and t0 - prev[-1]["t0"] < frames(p["screen_merge_s"]):
                    continue  # one screen per screener / handler within screen_merge_s (noise splits the run)
                A["screen"].append(
                    dict(
                        t0=t0,
                        screener=s,
                        handler=h,
                        kind="ball",
                        xball=xb[pre - a] if pre >= a else xb[0],
                        xbig=on_ball_defender(scene, s, pre),
                    )
                )
    cache["anchors"] = A
    return A


def get_anchors(scene, supplied=None):
    """Derived anchors with supplied keys replacing the derived list for that key."""
    A = {k: list(v) for k, v in derive_anchors(scene).items()}
    if supplied:
        for k, v in supplied.items():
            if k not in ANCHOR_KEYS:
                raise KeyError(f"unknown anchor key {k}")
            A[k] = list(v)
    return A


def _next_release(A, t):
    ts = [x["t_rel"] for x in A["pass"] + A["shot"] if x["t_rel"] > t]
    return min(ts) if ts else None


# --------------------------------------------------------------------------------------
# DM-RULE-02 matchup segments
# --------------------------------------------------------------------------------------
def detect_matchup(scene, **params):
    """Stable top-1 matchup segments (kind 'matchup'); conf = mean posterior x quality."""
    p, A = _setup("matchup", scene, params)
    mu = matchup_posterior(scene, p)  # call overrides of the HMM parameters take effect here
    out = []
    for d in scene.defense:
        for a, b, att in _top1_runs(scene, d, frames(p["flicker_s"]), mu):
            if att is None or (b - a) * DT < p["min_s"] - 1e-9:
                continue
            pr = mu["post"][d][mu["attackers"].index(att)]
            pm = window_conf(pr, a, b)
            ev = make_event(
                scene,
                p,
                "matchup",
                {"defender": d, "attacker": att},
                a,
                a,
                b,
                pm,
                [f"mean posterior {pm:.2f} over {(b - a) * DT:.2f} s >= {p['min_s']} s"],
                state=True,
                right_censored=bool(b == scene.n - 1),
            )
            if ev is not None:
                out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# DM-P01 defensive locomotion relative to the facing proxy
# --------------------------------------------------------------------------------------
def detect_def_locomotion(scene, **params):
    """forward / lateral / backpedal relative to the facing proxy (toward the handler for the on-ball
    defender, else toward the midpoint of man and ball); speed >= v_min for >= min_s."""
    p, A = _setup("def_locomotion", scene, params)
    mu = matchup_posterior(scene)
    bx, by = ball_xy(scene)
    out = []
    for d in scene.defense:
        k = scene.kins[d]
        fx, fy = np.full(scene.n, np.nan), np.full(scene.n, np.nan)
        for t in range(scene.n):
            a = mu["top1"][d][t]
            if a is None:
                continue
            ka = scene.kins[a]
            if scene.holder[t] == a:
                fx[t], fy[t] = ka.x[t] - k.x[t], ka.y[t] - k.y[t]
            else:
                fx[t], fy[t] = (ka.x[t] + bx[t]) / 2 - k.x[t], (ka.y[t] + by[t]) / 2 - k.y[t]
        sp = k.speed
        with np.errstate(all="ignore"):
            ang = np.degrees(np.arccos(np.clip((k.vx * fx + k.vy * fy) / (sp * np.hypot(fx, fy)), -1, 1)))
            sig = np.degrees(k.sigma_speed / sp)
        cls = np.full(scene.n, "", dtype=object)
        # DEF-T11 (MP-09): moving = speed above v_min AND significantly non-zero (s2 >= stand_s2), never raw speed alone
        p_mov = p_above(np.nan_to_num(sp, nan=0.0), p["v_min"], np.nan_to_num(k.sigma_speed, nan=1.0))
        ok = (np.nan_to_num(sp, nan=0) >= p["v_min"]) & (np.nan_to_num(k.stationary_s2, nan=0.0) >= p["stand_s2"])
        cls[ok & (ang <= p["forward_max_deg"])] = "def_forward"
        cls[ok & (ang > p["forward_max_deg"]) & (ang < p["backward_min_deg"])] = "def_lateral"
        cls[ok & (ang >= p["backward_min_deg"])] = "def_backpedal"
        for kind in ("def_forward", "def_lateral", "def_backpedal"):
            for a, b in hysteresis(cls == kind, cls == kind, p["min_s"], frames(p["exit_gap_s"])):
                lo, hi = {
                    "def_forward": (None, p["forward_max_deg"]),
                    "def_lateral": (p["forward_max_deg"], p["backward_min_deg"]),
                    "def_backpedal": (p["backward_min_deg"], None),
                }[kind]
                pr = np.array(
                    [
                        band_probs(ang[t], max(sig[t], 1.0), {"x": (lo, hi)})["x"] if not np.isnan(ang[t]) else np.nan
                        for t in range(a, b + 1)
                    ]
                )
                alts = {}
                for kk, (l2, h2) in {
                    "def_forward": (None, p["forward_max_deg"]),
                    "def_lateral": (p["forward_max_deg"], p["backward_min_deg"]),
                    "def_backpedal": (p["backward_min_deg"], None),
                }.items():
                    alts[kk] = float(
                        np.nanmean(
                            [
                                band_probs(ang[t], max(sig[t], 1.0), {"x": (l2, h2)})["x"]
                                for t in range(a, b + 1)
                                if not np.isnan(ang[t])
                            ]
                        )
                    )
                # P_cond = P(angle in band) x P(speed >= v_min) (window means) x proxy factor (DEF-T11). The run
                # must be moving with window-mean P(speed >= v_min) >= p_move_min: smoothed noise lifts a 0.8 m/s
                # shuffle above 1.0 m/s for 0.4 s (window mean ~0.6), a real slide or step-up is >= 0.9
                pmv = window_conf(p_mov, a, b)
                if pmv < p["p_move_min"]:
                    continue
                pc = window_conf(np.concatenate([[np.nan] * a, pr]), a, b) * pmv * p["proxy_conf_factor"]
                ev = make_event(
                    scene,
                    p,
                    kind,
                    {"defender": d},
                    a,
                    a,
                    b,
                    pc,
                    [
                        f"mean angle velocity-vs-facing {np.nanmean(ang[a:b + 1]):.0f} deg",
                        f"speed >= {p['v_min']} m/s for {(b - a) * DT:.2f} s >= {p['min_s']} s",
                    ],
                    alts,
                    facing_source="proxy",
                    mean_speed=float(np.nanmean(sp[a : b + 1])),
                )
                if ev:
                    out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# DM-P02/P03/P04 closeouts and DM-P07 recover
# --------------------------------------------------------------------------------------
def _approach(scene, d, a, w0, w1, p):
    """Measure D's approach to attacker a inside [w0, w1] (no gating). None if D never starts."""
    kd, ka = scene.kins[d], scene.kins[a]
    vt = v_to(kd, ka.x, ka.y)
    m = np.nan_to_num(vt[w0 : w1 + 1], nan=0.0) >= p["v_start"]
    rs = [r for r in runs(m) if r[1] - r[0] + 1 >= frames(p["start_hold_s"]) + 1]
    if not rs:
        return None
    ts = w0 + rs[0][0]
    sp = np.nan_to_num(kd.speed, nan=0.0)
    tpk = ts + int(np.argmax(sp[ts : w1 + 1]))
    # end of the approach: first frame after the peak where D is stationary (MP-09 chi-square s2 < stand_s2;
    # a raw-speed test would end choppy closeouts while the short steps are still covering ground)
    s2 = kd.stationary_s2
    te = w1
    for t in range(tpk, w1 + 1):
        if s2[t] < p["stand_s2"]:
            te = t
            break
    dd = dist(kd, ka)
    sx, sy = mean_xy(kd, ts)
    ex, ey = mean_xy(kd, te)
    axe, aye = mean_xy(ka, te)
    sig = float(np.nanmean(sigma_rel(kd, ka, p)[ts : te + 1]))
    vpk = float(sp[tpk])
    # deceleration profile (DM-P04 revised): implied mean deceleration from the 0.8*vpk point to the stop
    il = tpk
    while il + 1 <= te and sp[il + 1] >= 0.8 * vpk:
        il += 1
    ist = il
    while ist + 1 <= w1 and sp[ist] > p["v_end"]:
        ist += 1
    lx, ly = mean_xy(kd, il, 1)
    qx, qy = mean_xy(kd, ist, 1)
    d_dec = max(math.hypot(qx - lx, qy - ly), 0.05)
    a_dec = max(((0.8 * vpk) ** 2 - p["v_end"] ** 2) / (2 * d_dec), 0.0)
    sv = float(kd.sigma_speed[tpk]) if not np.isnan(kd.sigma_speed[tpk]) else 0.4
    sig_own = float(K_CAL * math.sqrt(2 * np.nanmean(kd.var_p[il : ist + 1]))) if ist >= il else sig
    s_adec = a_dec * math.hypot(
        2 * 0.8 * sv * 0.8 * vpk / max((0.8 * vpk) ** 2 - p["v_end"] ** 2, 0.1), sig_own / d_dec
    )
    return dict(
        d=d,
        a=a,
        ts=ts,
        tpk=tpk,
        te=te,
        d_s=mean_val(dd, ts),
        d_e=mean_val(dd, te),
        chord=math.hypot(ex - sx, ey - sy),
        vpk=vpk,
        sv=sv,
        sig=sig,
        angle=float(angle_at(axe, aye, ex, ey, 0.0, 0.0)),
        a_dec=a_dec,
        s_adec=max(s_adec, 0.3),
        d_dec=d_dec,
        t_dec=(ist - il) * DT,
    )


def _closeouts(scene, p, A):
    """One record per pass: the defender with the largest distance reduction, plus gate probabilities."""
    recs = []
    for ps in sorted(A["pass"], key=lambda x: x["t_rel"]):
        a = ps["receiver"]
        w0 = max(0, ps["t_rel"] - frames(p["pre_release_s"]))
        w1 = min(scene.n - 1, ps["t_catch"] + frames(p["window_after_catch_s"]))
        nr = _next_release(A, ps["t_catch"])
        if nr is not None:
            w1 = min(w1, nr)
        best = None
        for d in scene.defense:
            r = _approach(scene, d, a, w0, w1, p)
            if r and (best is None or r["d_s"] - r["d_e"] > best["d_s"] - best["d_e"]):
                best = r
        if best is None:
            continue
        b = best
        kd = scene.kins[b["d"]]
        # dist_drop is a change of a pair distance over ~1 s: its error is sqrt(2) x the level error (measured 1.36-1.44x
        # at lags >= 1 s). The chord is ONE track's displacement: its error is about the one-track floor (measured
        # 0.74-0.84 sigma_p per axis at 1 s), not sqrt(2) x the pair sigma (NEW-R1, loop 2)
        s2 = b["sig"] * math.sqrt(2)
        s_chord = sigma_own(kd, b["ts"], b["te"], p)
        peak_min = tier_param(p, "peak_speed_min", kd)
        b.update(s_chord=s_chord, peak_min=peak_min)
        sig_ang = math.degrees(b["sig"] / max(b["d_e"], 0.3))
        gates = {
            "start_dist": float(p_above(b["d_s"], p["start_dist_min"], b["sig"])),
            "chord": float(p_above(b["chord"], p["chord_min"], s_chord)),
            "dist_drop": float(p_above(b["d_s"] - b["d_e"], p["dist_drop_min"], s2)),
            "peak_speed": float(p_above(b["vpk"], peak_min, b["sv"])),
            "end_dist": float(p_below(b["d_e"], p["end_dist_max"], b["sig"])),
        }
        # DEF-T15: the landing angle is a quality attribute (rim side vs high side), not an existence gate
        p_rim = float(p_below(b["angle"], p["landing_angle_max"], sig_ang))
        b.update(pass_=ps, gates=gates, P=float(np.prod(list(gates.values()))), p_rim_side=p_rim)
        recs.append(b)
    return recs


def _closeout_reasons(b, p):
    return [
        _fmt("start dist", b["d_s"], ">=", p["start_dist_min"], "m"),
        _fmt("chord", b["chord"], ">=", p["chord_min"], "m"),
        _fmt("dist drop", b["d_s"] - b["d_e"], ">=", p["dist_drop_min"], "m"),
        _fmt("smoothed peak", b["vpk"], ">=", b.get("peak_min", p["peak_speed_min"]), "m/s"),
        _fmt("end dist", b["d_e"], "<=", p["end_dist_max"], "m"),
        f"landing angle {b['angle']:.0f} deg (rim side <= {p['landing_angle_max']} deg; attribute only)",
    ]


def _closeout_event(scene, p, b, kind, p_extra=1.0, alts=None, **attrs):
    ps = b["pass_"]
    return make_event(
        scene,
        p,
        kind,
        {"defender": b["d"], "attacker": b["a"]},
        ps["t_catch"],
        b["ts"],
        b["te"],
        b["P"] * p_extra,
        _closeout_reasons(b, p) + attrs.pop("extra_reasons", []),
        alts,
        p_emit=b["P"],
        latency_s=(b["ts"] - ps["t_rel"]) * DT,
        closeout_distance_m=b["chord"],
        closeout_speed_mps=b["vpk"],
        end_dist_m=b["d_e"],
        angle_deg=b["angle"],
        landing_side="rim_side" if b["p_rim_side"] >= 0.5 else "high_side",
        p_rim_side=round(b["p_rim_side"], 3),
        sprint=bool(b["vpk"] >= p["sprint_flag_speed"]),
        t_s=b["ts"],
        t_e=b["te"],
        gates={k: round(v, 3) for k, v in b["gates"].items()},
        **attrs,
    )


def detect_closeout(scene, **params):
    """CLOSEOUT base event on the receiver of a pass (t0 = catch)."""
    p, A = _setup("closeout", scene, params)
    out = []
    for b in _closeouts(scene, p, A):
        ev = _closeout_event(scene, p, b, "closeout")
        if ev:
            out.append(ev)
    return out


def _length_probs(b, pl):
    return band_probs(
        b["d_e"],
        b["sig"],
        {
            "closeout_hard": (None, pl["hard_max"]),
            "closeout_standard": (pl["hard_max"], pl["standard_max"]),
            "closeout_short": (pl["standard_max"], pl["short_max"]),
        },
    )


def detect_closeout_length(scene, **params):
    """Length class of each closeout from the 5-frame mean end distance (hard / standard / short)."""
    p, A = _setup(("closeout_length", "closeout"), scene, params)
    pc = p
    out = []
    for b in _closeouts(scene, pc, A):
        pr = _length_probs(b, p)
        # the class is the band that contains the 5-frame-mean estimate; the argmax of the band probabilities never
        # picks the 0.4 m wide standard band once sigma_rel reaches ~0.4 m (noise-scaled floor at sigma_p 0.5)
        kind = (
            "closeout_hard"
            if b["d_e"] <= p["hard_max"]
            else ("closeout_standard" if b["d_e"] <= p["standard_max"] else "closeout_short")
        )
        ev = _closeout_event(
            scene,
            pc,
            b,
            kind,
            pr[kind],
            pr,
            extra_reasons=[f"end dist {b['d_e']:.2f} m -> {kind}"],
            tight_p=pr["closeout_hard"] + pr["closeout_standard"],
        )
        if ev:
            out.append(ev)
    return out


def detect_closeout_profile(scene, **params):
    """Deceleration profile (sprint_stop / mixed / choppy) from the implied mean deceleration."""
    p, A = _setup(("closeout_profile", "closeout"), scene, params)
    pc = p
    out = []
    for b in _closeouts(scene, pc, A):
        kd = scene.kins[b["d"]]
        # DEF-T13: the q = 10 smoother (sigma_p >= 0.45) smears decelerations and peaks: tier-specific edges
        min_peak = tier_param(p, "profile_min_peak", kd)
        lo, hi = tier_param(p, "choppy_max_decel", kd), tier_param(p, "sprint_stop_min_decel", kd)
        if b["vpk"] < min_peak:
            continue
        pr = band_probs(
            b["a_dec"],
            b["s_adec"],
            {
                "closeout_choppy": (None, lo),
                "closeout_mixed": (lo, hi),
                "closeout_sprint_stop": (hi, None),
            },
        )
        kind = max(pr, key=pr.get)
        ev = _closeout_event(
            scene,
            pc,
            b,
            kind,
            pr[kind],
            pr,
            extra_reasons=[
                f"implied decel {b['a_dec']:.2f} m/s^2 (choppy <= {lo}, sprint_stop >= {hi}"
                f"{', q10 tier' if high_noise(kd) else ''})"
            ],
            a_dec_mps2=b["a_dec"],
            d_dec_m=b["d_dec"],
            t_dec_s=b["t_dec"],
        )
        if ev:
            out.append(ev)
    return out


def detect_closeout_fly_by(scene, **params):
    """Fly-by: closest approach <= cpa_max at smoothed speed >= cpa_speed_min, then overshoot past A."""
    p, A = _setup("closeout_fly_by", scene, params)
    out = []
    for ps in A["pass"]:
        a = ps["receiver"]
        ka = scene.kins[a]
        w0 = ps["t_catch"]
        w1 = min(scene.n - 1, ps["t_catch"] + frames(p["window_after_catch_s"]))
        for d in scene.defense:
            kd = scene.kins[d]
            dd = dist(kd, ka)
            seg = np.nan_to_num(dd[w0 : w1 + 1], nan=99)
            tc = w0 + int(np.argmin(seg))
            if tc in (w0, w1):
                continue
            sp = kd.speed
            ux, uy = kd.vx[tc] / max(sp[tc], 1e-6), kd.vy[tc] / max(sp[tc], 1e-6)
            t2 = min(scene.n - 1, tc + frames(p["overshoot_window_s"]))
            over = max((kd.x[t] - ka.x[tc]) * ux + (kd.y[t] - ka.y[tc]) * uy for t in range(tc, t2 + 1))
            t3 = min(scene.n - 1, tc + frames(p["keep_speed_s"]))
            keep = float(np.nanmin(sp[tc : t3 + 1]))
            sig = float(sigma_rel(kd, ka, p)[tc])
            g = {
                "cpa": float(p_below(mean_val(dd, tc, 1), p["cpa_max"], sig)),
                "speed_at_cpa": float(p_above(sp[tc], p["cpa_speed_min"], kd.sigma_speed[tc])),
                "overshoot": float(p_above(over, p["overshoot_min"], sig * math.sqrt(2))),
                "keep_speed": float(p_above(keep, p["keep_speed_min"], kd.sigma_speed[tc])),
            }
            shot = [s for s in A["shot"] if s["shooter"] == a and abs(s["t_rel"] - tc) <= frames(p["shot_sync_s"])]
            ev = make_event(
                scene,
                p,
                "closeout_fly_by",
                {"defender": d, "attacker": a},
                tc,
                max(0, tc - frames(p["span_before_cpa_s"])),
                t3,
                float(np.prod(list(g.values()))),
                [
                    _fmt("cpa dist", mean_val(dd, tc, 1), "<=", p["cpa_max"], "m"),
                    _fmt("speed at cpa", float(sp[tc]), ">=", p["cpa_speed_min"], "m/s"),
                    _fmt("overshoot", over, ">=", p["overshoot_min"], "m"),
                    _fmt("min speed after cpa", keep, ">=", p["keep_speed_min"], "m/s"),
                ],
                None,
                min_dist_m=mean_val(dd, tc, 1),
                speed_at_cpa_mps=float(sp[tc]),
                overshoot_m=over,
                on_shot=bool(shot),
                gates={k: round(v, 3) for k, v in g.items()},
            )
            if ev:
                out.append(ev)
    return out


def detect_recover(scene, **params):
    """RECOVER: help-to-man return to the unchanged matchup (chord >= 1.5 m, end <= 2.0 m), excluding
    approaches already labelled CLOSEOUT."""
    p, A = _setup("recover", scene, params)
    pc = merged_params("closeout")
    taken = [(b["d"], b["ts"], b["te"]) for b in _closeouts(scene, pc, A) if b["P"] >= pc["emit_p_min"]]
    jt = joint_top1(scene)  # DEF-T17: one-to-one assignment, so a nail helper on the handler keeps his own man
    out = []
    for d in scene.defense:
        kd = scene.kins[d]
        for a in scene.offense:
            ka = scene.kins[a]
            vt = np.nan_to_num(v_to(kd, ka.x, ka.y), nan=0.0)
            for ra, rb in runs(vt >= p["v_start"]):
                if rb - ra + 1 < frames(p["start_hold_s"]) + 1:
                    continue
                w1 = min(scene.n - 1, rb + frames(p["tail_s"]))
                r = _approach(scene, d, a, max(0, ra - 1), w1, {**pc, **p})
                if r is None:
                    continue
                pre = max(0, r["ts"] - frames(p["pre_matchup_s"]))
                if jt[d][pre] != a or jt[d][r["te"]] != a:
                    continue  # matchup changed: a rotation, not a recover
                if any(dd_ == d and not (r["te"] < s_ or r["ts"] > e_) for dd_, s_, e_ in taken):
                    continue
                s2 = r["sig"] * math.sqrt(2)
                g = {
                    "chord": float(p_above(r["chord"], p["chord_min"], s2)),
                    "dist_drop": float(p_above(r["d_s"] - r["d_e"], p["dist_drop_min"], s2)),
                    "start_dist": float(p_above(r["d_s"], p["start_dist_min"], r["sig"])),
                    "end_dist": float(p_below(r["d_e"], p["end_dist_max"], r["sig"])),
                }
                ev = make_event(
                    scene,
                    p,
                    "recover",
                    {"defender": d, "attacker": a},
                    r["ts"],
                    r["ts"],
                    r["te"],
                    float(np.prod(list(g.values()))),
                    [
                        _fmt("chord", r["chord"], ">=", p["chord_min"], "m"),
                        _fmt("dist drop", r["d_s"] - r["d_e"], ">=", p["dist_drop_min"], "m"),
                        _fmt("start dist", r["d_s"], ">=", p["start_dist_min"], "m"),
                        _fmt("end dist", r["d_e"], "<=", p["end_dist_max"], "m"),
                    ],
                    None,
                    chord_m=r["chord"],
                    end_dist_m=r["d_e"],
                    peak_speed=r["vpk"],
                )
                if ev and not any(e.actors["defender"] == d and abs(e.t0 - ev.t0) < frames(p["dedupe_s"]) for e in out):
                    out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# DM-RULE-06 help excursion ladder (minor, step-release, stunt, dig, help-and-recover) and DM-P08 sink
# --------------------------------------------------------------------------------------
def _help_triggers(scene, A, p):
    trig = []
    for md in A["middle_dribble"]:
        trig.append(dict(kind="middle_dribble", t=md["t_s"], h=md["handler"], t_e=md.get("t_e")))
    for dr in A["drive"]:
        trig.append(dict(kind="drive", t=dr["t"], h=dr["handler"], t_e=None))
    for sc in A["screen"]:
        if sc.get("kind", "ball") == "ball":
            trig.append(dict(kind="screen", t=sc["t0"], h=sc["handler"], t_e=None))
    for ps in A["pass"]:
        kr = scene.kins[ps["receiver"]]
        if kr.r[ps["t_catch"]] <= p["post_catch_r"]:
            trig.append(dict(kind="post_catch", t=ps["t_catch"], h=ps["receiver"], t_e=None))
    trig.sort(key=lambda x: (x["t"], x["kind"] != "middle_dribble"))
    out = []
    for tg in trig:  # one trigger per handler per merge window; a middle dribble wins (trigger decides rung)
        if out and out[-1]["h"] == tg["h"] and tg["t"] - out[-1]["t"] < frames(p["trigger_merge_s"]):
            continue
        out.append(tg)
    return out


def _traps_cached(scene):
    cache = _cache(scene)
    if "traps" not in cache:
        cache["traps"] = detect_trap(scene)
    return cache["traps"]


def _excursions(scene, p, A):
    """Measure every off-ball defender's movement toward the handler after each trigger (no rung yet)."""
    mu = matchup_posterior(scene)
    recs = []
    for tg in _help_triggers(scene, A, p):
        t, h = tg["t"], tg["h"]
        kh = scene.kins[h]
        onb = on_ball_defender(scene, h, t)
        for d in scene.defense:
            if d == onb:
                continue
            am = mu["top1"][d][t]
            if am is None or am == h:
                continue
            kd, ka = scene.kins[d], scene.kins[am]
            w1 = min(scene.n - 1, t + frames(p["onset_window_s"]))
            vt = np.nan_to_num(v_to(kd, kh.x, kh.y), nan=0.0)
            rs = [
                r for r in runs(vt[t : w1 + 1] >= p["onset_v_to"]) if r[1] - r[0] + 1 >= frames(p["onset_hold_s"]) + 1
            ]
            if not rs:
                continue
            ton = t + rs[0][0]
            end = min(scene.n - 1, t + frames(p["excursion_max_s"]))
            d0x, d0y = mean_xy(kd, max(0, ton - frames(p["baseline_back_s"])))  # pre-onset baseline
            disp = np.hypot(kd.x[ton : end + 1] - d0x, kd.y[ton : end + 1] - d0y)
            tp = ton + int(np.nanargmax(disp))
            px, py = mean_xy(kd, tp)
            dvx, dvy = px - d0x, py - d0y
            peak = math.hypot(dvx, dvy)
            hx, hy = kh.x[tp], kh.y[tp]
            eh = math.hypot(hx - d0x, hy - d0y)
            toward_h = (dvx * (hx - d0x) + dvy * (hy - d0y)) / max(eh, 1e-6)
            er = math.hypot(d0x, d0y)
            toward_r = (dvx * (-d0x) + dvy * (-d0y)) / max(er, 1e-6)
            dH = dist(kd, kh)
            span_e = min(scene.n, tp + frames(p["span_after_peak_s"]) + 1)
            min_dh = float(np.nanmin(dH[ton:span_e]))
            dA = dist(kd, ka)
            dA_tp = mean_val(dA, tp)
            t_ret_end = min(scene.n - 1, tp + frames(p["return_window_s"]))
            dA_after = dA[tp : t_ret_end + 1]
            ret = dA_tp - float(np.nanmin(dA_after)) if len(dA_after) else 0.0
            t_st = min(scene.n - 1, tp + frames(p["stunt_return_s"]))
            ret_stunt = dA_tp - float(np.nanmin(dA[tp : t_st + 1]))
            # reversal start: first frame after the peak moving back toward the man (same onset gate)
            vta = np.nan_to_num(v_to(kd, ka.x, ka.y), nan=0.0)
            rv = [
                r
                for r in runs(vta[tp : t_ret_end + 1] >= p["onset_v_to"])
                if r[1] - r[0] + 1 >= frames(p["onset_hold_s"]) + 1
            ]
            t_rev = tp + rv[0][0] if rv else None
            t_ret = None
            for tt in range(tp, t_ret_end + 1):
                if dA_tp - dA[tt] >= p["return_min_frac"] * peak:
                    t_ret = tt
                    break
            # help share in [ton, tp + 0.3 s]: D in the drive corridor ahead of H, or D the nearest defender to H
            # while H's own defender is beaten (behind the ball, r_onb > r_H)
            span = range(ton, span_e)
            kob = scene.kins[onb]
            near = 0
            for tt in span:
                dmin = min(
                    math.hypot(scene.kins[o].x[tt] - kh.x[tt], scene.kins[o].y[tt] - kh.y[tt])
                    for o in scene.defense
                    if o != d and not np.isnan(scene.kins[o].x[tt])
                )
                sd_, tau_ = seg_dist_arr(
                    np.array(kd.x[tt]), np.array(kd.y[tt]), np.array(kh.x[tt]), np.array(kh.y[tt]), 0.0, 0.0
                )
                # in the corridor = beside the H -> rim segment AND ahead of H along it (tau > 0); a digger standing
                # just behind H is within the half width of the clamped segment end, which is not the corridor
                in_corr = float(sd_) <= p["corridor_half_width"] and float(tau_) > 0.0 and kd.r[tt] < kh.r[tt]
                if in_corr or (dH[tt] < dmin and kob.r[tt] > kh.r[tt]):
                    near += 1
            t_end = min(scene.n - 1, tp + frames(p["restore_s"]))
            restored = mu["top1"][d][t_end] == am
            rot = False
            if not restored:
                new = mu["top1"][d][t_end]
                rot = new is not None and all(
                    mu["top1"][d][tt] == new for tt in range(t_end, min(scene.n, t_end + frames(p["rot_persist_s"])))
                )
            trapped = any(
                d in (e.actors["d1"], e.actors["d2"]) and e.start <= span_e - 1 and e.end >= ton
                for e in _traps_cached(scene)
            )
            sig = float(np.nanmean(sigma_rel(kd, kh, p)[ton : tp + 1]))
            sig_own = sigma_own(kd, max(0, ton - frames(p["baseline_back_s"])), tp, p)
            recs.append(
                dict(
                    sig_own=sig_own,
                    trig=tg,
                    d=d,
                    a=am,
                    h=h,
                    ton=ton,
                    tp=tp,
                    peak=peak,
                    toward_h=toward_h,
                    toward_r=toward_r,
                    min_dh=min_dh,
                    dA_tp=dA_tp,
                    ret=ret,
                    ret_stunt=ret_stunt,
                    t_ret=t_ret,
                    t_rev=t_rev,
                    near_s=near * DT,
                    restored=restored,
                    rotation=rot,
                    trapped=trapped,
                    sig=sig,
                    end=t_ret if t_ret is not None else t_ret_end,
                )
            )
    return recs


def _ladder(scene, p, A):
    """Classify each excursion into exactly one rung (highest rung met; trigger decides step vs stunt)."""
    out = []
    for e in _excursions(scene, p, A):
        if e["rotation"] or e["trapped"]:
            continue  # rung 5 (ROTATE) and doubles are labelled by their own detectors
        if e["toward_h"] < p["dir_cos_min"] * e["peak"] or (
            e["min_dh"] > p["sink_owner_min_dh"] and e["toward_r"] > e["toward_h"]
        ):
            continue  # movement mostly toward the rim with no approach to the handler: SINK owns it
        # s: pair-distance level; s2: change of a pair distance (return toward the man, measured 1.36-1.44 x the level
        # error at lags >= 1 s); so_: ONE track's displacement (the excursion peak), loop 2 NEW-R1 (see sigma_own)
        s, s2, so_ = e["sig"], e["sig"] * math.sqrt(2), e["sig_own"]
        ret_ok = e["t_ret"] is not None
        pr = {}
        near = 1.0 if e["near_s"] >= p["har_near_s"] else 0.0
        pr["help_and_recover"] = (
            float(p_above(e["dA_tp"], p["har_off_man_min"], s))
            * near
            * float(p_above(e["ret"], p["har_return_min"], s2))
            * (1.0 if e["restored"] else 0.0)
        )
        pr["dig"] = (
            (1 - near)
            * float(p_above(e["peak"], p["dig_approach_min"], so_))
            * float(p_below(e["min_dh"], p["dig_dist_max"], s))
            * float(p_above(e["ret"], p["dig_return_min"], s2))
        )
        dribble = e["trig"]["kind"] == "middle_dribble"
        far = float(p_above(e["min_dh"], p["dig_dist_max"], s))
        if dribble:
            onset_ok = (e["ton"] - e["trig"]["t"]) * DT <= p["step_onset_max_s"]
            rel_ok = True
            if e["trig"].get("t_e") is not None:
                rel_ok = e["t_rev"] is not None and (e["t_rev"] - e["trig"]["t_e"]) * DT <= p["step_release_lag_max_s"]
            pr["step_release"] = (
                far
                * float(p_above(e["peak"], p["step_min"], so_))
                * float(p_above(e["ret"], p["step_release_min"], s2))
                * (1.0 if onset_ok and rel_ok else 0.0)
            )
        else:
            pr["stunt"] = (
                far
                * float(p_above(e["peak"], p["stunt_min"], so_))
                * float(p_above(e["ret_stunt"], p["stunt_return_min"], s2))
            )
            pr["minor_excursion"] = (
                far
                * float(p_above(e["peak"], p["minor_min"], so_))
                * float(p_below(e["peak"], p["stunt_min"], so_))
                * float(p_above(e["ret"], p["minor_return_min"], s2))
            )
        if any(noise_of(scene.kins[o])[0] >= p["subnoise_abstain_sigma_p"] for o in (e["d"], e["h"])):
            pr.pop("step_release", None)  # sub-metre rungs abstain in the high-noise tier (DEF-T13)
            pr.pop("minor_excursion", None)
        order = ["help_and_recover", "dig", "stunt", "step_release", "minor_excursion"]
        kind = next((k for k in order if pr.get(k, 0.0) >= p["emit_p_min"]), None)
        p_any = min(1.0, sum(pr.values()))  # rungs are (nearly) exclusive: P(some rung) ~ their sum
        if kind is None:
            if p_any < p["emit_p_min"]:
                continue
            kind = max(pr, key=pr.get)  # ambiguous rung: most probable one, alternatives carry the rest
        reasons = [
            f"trigger {e['trig']['kind']} at frame {e['trig']['t']}",
            _fmt(
                "peak excursion",
                e["peak"],
                ">=",
                {
                    "help_and_recover": p["minor_min"],
                    "dig": p["dig_approach_min"],
                    "stunt": p["stunt_min"],
                    "step_release": p["step_min"],
                    "minor_excursion": p["minor_min"],
                }[kind],
                "m",
            ),
            _fmt("min dist to handler", e["min_dh"], "vs", p["dig_dist_max"], "m"),
            _fmt("return toward man", e["ret"], ">=", p["minor_return_min"], "m"),
            _fmt("dist to man at peak", e["dA_tp"], "vs", p["har_off_man_min"], "m"),
        ]
        ev = make_event(
            scene,
            p,
            kind,
            {"defender": e["d"], "handler": e["h"], "attacker": e["a"]},
            e["ton"],
            e["ton"],
            e["end"],
            pr[kind],
            reasons,
            pr,
            p_emit=max(pr[kind], p_any),
            rung=order.index(kind),
            trigger=e["trig"]["kind"],
            trigger_t=e["trig"]["t"],
            latency_s=(e["ton"] - e["trig"]["t"]) * DT,
            peak_disp_m=e["peak"],
            min_dist_to_handler_m=e["min_dh"],
            hard_dig=bool(e["min_dh"] <= p["hard_dig_max"]),
            fake_trap=bool(kind == "stunt" and e["min_dh"] <= p["fake_trap_dist"]),
            return_censored=not ret_ok,
        )
        if ev:
            out.append(ev)
    return out


def _ladder_detector(item_id, kind, scene, params):
    """Rung items share the help_ladder parameters (one event, graded commitment: no double counting)."""
    p, A = _setup("help_ladder", scene, params)
    return [e for e in _ladder(scene, p, A) if e.kind == kind]


def detect_minor_excursion(scene, **params):
    """Rung 0: 0.35-1.0 m excursion toward the handler and back, no dribble trigger (fills the ladder gap)."""
    return _ladder_detector("minor_excursion", "minor_excursion", scene, params)


def detect_step_release(scene, **params):
    """Rung 1: dribble-triggered one-step help and release (Izzo); the trigger, not the size, decides."""
    return _ladder_detector("step_release", "step_release", scene, params)


def detect_stunt(scene, **params):
    """Rung 2: >= 1.0 m fake help toward the handler, back >= 0.5 m within 1.0 s, never within 1.2 m."""
    return _ladder_detector("stunt", "stunt", scene, params)


def detect_dig(scene, **params):
    """Rung 3: >= 1.5 m approach to <= 1.2 m of the handler (hard <= 0.8 m), back >= 1.0 m within 1.5 s."""
    return _ladder_detector("dig", "dig", scene, params)


def detect_help_and_recover(scene, **params):
    """Rung 4: >= 2.0 m off the man as the nearest defender / in the drive corridor, matchup restored."""
    return _ladder_detector("help_and_recover", "help_and_recover", scene, params)


def detect_sink(scene, **params):
    """SINK: help depth (r_A - r_D) rises >= delta_hd_min within window_s of a drive or post catch, with D's
    own r falling >= own_dr_min and D staying > min_dist_handler from the handler."""
    p, A = _setup(("sink", "help_ladder"), scene, params)
    pl = p
    mu = matchup_posterior(scene)
    out = []
    trig = [t for t in _help_triggers(scene, A, pl) if t["kind"] in ("drive", "post_catch")]
    for tg in trig:
        t, h = tg["t"], tg["h"]
        kh = scene.kins[h]
        onb = on_ball_defender(scene, h, t)
        w1 = min(scene.n - 1, t + frames(p["window_s"]))
        for d in scene.defense:
            am = mu["top1"][d][t]
            if d == onb or am is None or am == h:
                continue
            kd, ka = scene.kins[d], scene.kins[am]
            hd = ka.r - kd.r
            hd0 = mean_val(hd, t)
            seg = hd[t : w1 + 1]
            tp = t + int(np.nanargmax(seg))
            dhd = mean_val(hd, tp) - hd0
            dr = mean_val(kd.r, tp) - mean_val(kd.r, t)
            min_dh = float(np.nanmin(dist(kd, kh)[t : tp + 1]))
            vr = np.nan_to_num(kd.v_r[t : w1 + 1], nan=0.0)
            # loop 2: the q = 10 smoother spreads the start of the move, so the 1.0 m/s crossing comes ~5 frames early
            # (measured); onset_v_r_q10 re-centres t0 in that tier
            on = [
                r
                for r in runs(vr >= tier_param(p, "onset_v_r", kd))
                if r[1] - r[0] + 1 >= frames(p["onset_hold_s"]) + 1
            ]
            ton = t + on[0][0] if on else t
            # loop 2 NEW-R1: each gate with the sigma of what it measures - delta_hd is a change of r_A - r_D (two
            # tracks' displacements: sqrt(2) x the level sigma), own_dr ONE track's displacement (sigma_own),
            # min dist to the handler a pair-distance level (sigma_rel, no sqrt(2))
            sig = float(np.nanmean(sigma_rel(kd, ka, p)[t : tp + 1])) * math.sqrt(2)
            s_own = sigma_own(kd, t, tp, p)
            s_h = float(np.nanmean(sigma_rel(kd, kh, p)[t : tp + 1]))
            g = {
                "delta_hd": float(p_above(dhd, p["delta_hd_min"], sig)),
                "own_dr": float(p_below(dr, -p["own_dr_min"], s_own)),
                "away_from_handler": float(p_above(min_dh, p["min_dist_handler"], s_h)),
            }
            ev = make_event(
                scene,
                p,
                "sink",
                {"defender": d, "attacker": am, "handler": h},
                ton,
                ton,
                tp,
                float(np.prod(list(g.values()))),
                [
                    _fmt("help depth rise", dhd, ">=", p["delta_hd_min"], "m"),
                    _fmt("own r change", dr, "<=", -p["own_dr_min"], "m"),
                    _fmt("min dist to handler", min_dh, ">", p["min_dist_handler"], "m"),
                ],
                None,
                trigger=tg["kind"],
                trigger_t=t,
                latency_s=(ton - t) * DT,
                delta_hd_m=dhd,
                end_spot_sink_sag=bool(
                    SPOTS["sink_sag"].inside(kd.x[tp], kd.y[tp], ax_=ka.x[tp], ay_=ka.y[tp], hx=kh.x[tp], hy=kh.y[tp])
                ),
            )
            if ev:
                out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# DM-P13 jump to the ball, DM-P14 deny / face guard, DM-P15 beaten / contain, DM-P16 back pressure
# --------------------------------------------------------------------------------------
def detect_jump_to_ball(scene, **params):
    """Passer's defender moves >= 0.5 m during the flight and >= 1.0 m by catch + 0.4 s toward the
    receiver's side, ending at least 0.8 m closer to the rim than the passer (t0 = release)."""
    p, A = _setup("jump_to_ball", scene, params)
    out = []
    for ps in A["pass"]:
        P_, R_ = ps["passer"], ps["receiver"]
        tr, tc = ps["t_rel"], ps["t_catch"]
        d = on_ball_defender(scene, P_, max(0, tr - frames(p["defender_back_s"])))
        kd, kp, kr = scene.kins[d], scene.kins[P_], scene.kins[R_]
        t2 = min(scene.n - 1, tc + frames(p["after_catch_s"]))
        x0, y0 = mean_xy(kd, tr)
        x1, y1 = mean_xy(kd, tc)
        x2, y2 = mean_xy(kd, t2)
        m_flight, m_total = math.hypot(x1 - x0, y1 - y0), math.hypot(x2 - x0, y2 - y0)
        dr = mean_val(kp.r, tr) - math.hypot(x2, y2)
        sig = float(np.nanmean(sigma_rel(kd, kp, p)[tr : t2 + 1])) * math.sqrt(2)
        # DEF-T16: side = projection of D's displacement on the pass direction, or (when D dropped below the passer)
        # on the direction from D to the receiver; soft, not a 0/1 sign test on dx
        dx_, dy_ = x2 - x0, y2 - y0
        rx, ry = mean_xy(kr, tc)
        px_, py_ = mean_xy(kp, tr)
        lp = max(math.hypot(rx - px_, ry - py_), 1e-6)
        ld = max(math.hypot(rx - x0, ry - y0), 1e-6)
        proj_pass = (dx_ * (rx - px_) + dy_ * (ry - py_)) / lp
        proj_recv = (dx_ * (rx - x0) + dy_ * (ry - y0)) / ld
        p_side = max(
            float(p_above(proj_pass, 0.0, sig)),
            float(p_above(dr, p["below_passer_min"], sig)) * float(p_above(proj_recv, 0.0, sig)),
        )
        on = None
        for t in range(tr, t2 + 1):
            if math.hypot(kd.x[t] - x0, kd.y[t] - y0) >= p["onset_disp"]:
                on = t
                break
        # move on the flight: the onset must come before the catch, or as soon as physics allows after a short flight
        t_min = p["t_react"] + math.sqrt(2 * p["onset_disp"] / p["a_first_step"])
        deadline = max(tc, tr + frames(t_min)) + frames(p["onset_slack_s"])
        g = {
            "onset_on_flight": 1.0 if (on is not None and on <= deadline) else 0.0,
            "by_catch": float(p_above(m_total, p["total_min"], sig)),
            "below_passer": float(p_above(dr, p["below_passer_min"], sig)),
            "side": p_side,
        }
        ev = make_event(
            scene,
            p,
            "jump_to_ball",
            {"defender": d, "passer": P_, "receiver": R_},
            tr,
            tr,
            t2,
            float(np.prod(list(g.values()))),
            [
                f"onset (>= {p['onset_disp']} m) at frame {on}, deadline {deadline} (catch {tc})",
                _fmt(f"move by catch+{p['after_catch_s']}s", m_total, ">=", p["total_min"], "m"),
                _fmt("r below passer", dr, ">=", p["below_passer_min"], "m"),
                f"toward the receiver: along the pass {proj_pass:.2f} m, toward the receiver {proj_recv:.2f} m (> 0)",
            ],
            None,
            latency_s=None if on is None else (on - tr) * DT,
            jump_m_in_flight=m_flight,
            jump_m_total=m_total,
        )
        if ev:
            out.append(ev)
    return out


def _spot_series(scene, spot_id, d, a_of_t, t_range):
    """Per-frame named_spots membership of defender d with assigned attacker a_of_t[t] (None -> False)."""
    sp = SPOTS[spot_id]
    kd = scene.kins[d]
    bx, by = ball_xy(scene)
    out = np.zeros(scene.n, dtype=bool)
    for t in t_range:
        a, h = a_of_t[t], scene.holder[t]
        if a is None or h is None:
            continue
        ka, kh = scene.kins[a], scene.kins[h]
        v = sp.inside(kd.x[t], kd.y[t], ax_=ka.x[t], ay_=ka.y[t], hx=kh.x[t], hy=kh.y[t], bx=bx[t], by=by[t])
        out[t] = bool(v)
    return out


def _mean5(arr):
    """NaN-aware centred 5-frame mean (DM-RULE-03 window means) of a per-frame series."""
    v = np.asarray(arr, dtype=float)
    ok = ~np.isnan(v)
    k = np.ones(5)
    num = np.convolve(np.where(ok, v, 0.0), k, "same")
    den = np.convolve(ok.astype(float), k, "same")
    with np.errstate(all="ignore"):
        return np.where(den > 0, num / den, np.nan)


def _position_hold(scene, p, spot_id, kind, exclude=None):
    """Hold of a named_spots man-ball position (deny / face guard): enter on the spot, stay on relaxed
    perp/tau/dist gates (relative hysteresis), min duration from the item. The perp / tau / dist numbers are read
    from the named_spots expression (SPOT_NUM). exclude: {defender: bool mask} of frames owned by another label.

    t0 is back-dated over the frames just before the first entry where the 5-frame-mean features, measured to the
    hold's attacker, already satisfy the entry predicate (DEF-T18: noise at the entry edge and the matchup HMM's
    lag delay the first raw entry). P_cond = window mean of P(perp) x P(tau in band) times the window-mean matchup
    posterior of the assigned attacker over the HMM-assigned frames (DEF-T12); P_emit = window mean of P(perp)
    (the existence test of the position, as before)."""
    mu = matchup_posterior(scene)
    bx, by = ball_xy(scene)
    sn = SPOT_NUM[kind]
    perp_max, tau_lo, tau_hi, dist_max = sn["perp_max"], sn["tau_lo"], sn["tau_hi"], sn["dist_max"]
    out = []
    # loop 4 L4-PERIMETER: deny / face guard are half-court perimeter positions: no frame with the ball beyond half court
    # (transition pick-up) or with the man in the named_spots post area (post_position owns those frames)
    front = np.nan_to_num(by, nan=0.0) <= C["HALF_Y"]
    post_r = SPOT_NUM["post"]["r_max"]
    for d in scene.defense:
        kd = scene.kins[d]
        top = mu["top1"][d]
        enter = _spot_series(scene, spot_id, d, top, range(scene.n))
        excl = exclude.get(d, np.zeros(scene.n, dtype=bool)) if exclude is not None else np.zeros(scene.n, dtype=bool)
        in_post = np.array([top[t] is not None and bool(scene.kins[top[t]].r[t] <= post_r) for t in range(scene.n)])
        notown = ~front | in_post  # loop 4: frames this label does not own (enter and stay)
        enter &= ~excl & ~notown
        if not enter.any():
            continue
        feats = {}

        def feat(att_of_t):
            """perp, tau, dist, |ball - A| and sigma per frame to the attacker att_of_t(t) (NaN when he holds)."""
            perp, tau, dA, L, sig = (np.full(scene.n, np.nan) for _ in range(5))
            for t in range(scene.n):
                a = att_of_t(t)
                if a is None or scene.holder[t] is None or scene.holder[t] == a:
                    continue
                ka = scene.kins[a]
                s_, tt = seg_dist_arr(
                    np.array(kd.x[t]), np.array(kd.y[t]), np.array(ka.x[t]), np.array(ka.y[t]),
                    np.array(bx[t]), np.array(by[t]),
                )
                perp[t], tau[t] = float(s_), float(tt)
                dA[t] = math.hypot(kd.x[t] - ka.x[t], kd.y[t] - ka.y[t])
                L[t] = math.hypot(bx[t] - ka.x[t], by[t] - ka.y[t])
                sig[t] = float(sigma_rel(kd, ka, p)[t])
            return perp, tau, dA, L, sig

        def fixed(att):
            if att not in feats:
                feats[att] = feat(lambda t: att)
            return feats[att]

        perp, tau, dA, L, sig = feat(lambda t: top[t])
        h = hyst_h(np.nanmedian(sig) if np.any(~np.isnan(sig)) else rel_floor(p, kd), p)
        stay = (
            (np.nan_to_num(perp, nan=99) <= perp_max + h)
            & (np.nan_to_num(tau, nan=-9) >= tau_lo - p["tau_hyst"])
            & (np.nan_to_num(tau, nan=9) <= tau_hi + p["tau_hyst"])
            & (np.nan_to_num(dA, nan=99) <= dist_max + h)
            & ~notown
        )
        prev_end = -1
        for a_, b_ in hysteresis(enter, stay | enter, p["min_s"], p["dwell_frames"]):
            att = top[a_ + (b_ - a_) // 2]
            fp_, ft_, fd_, fL_, fs_ = fixed(att)
            perp5, tau5, dA5 = _mean5(fp_), _mean5(ft_), _mean5(fd_)
            excl_h = excl | ~front | (np.nan_to_num(scene.kins[att].r, nan=0.0) <= post_r)
            enter5 = (
                (np.nan_to_num(perp5, nan=99) <= perp_max)
                & (np.nan_to_num(tau5, nan=-9) >= tau_lo)
                & (np.nan_to_num(tau5, nan=9) <= tau_hi)
                & (np.nan_to_num(dA5, nan=99) <= dist_max)
                & ~excl_h
            )
            a0 = a_
            while a0 - 1 > prev_end and enter5[a0 - 1]:
                a0 -= 1
            # loop 2 (DEF-T18 still failing): at the noisy entry edge the strict 5-frame-mean predicate is not met, so
            # also walk back while the RELAXED stay predicate (+h, +tau_hyst) holds on 5-frame means and D is still
            # closing on the attacker (dA5 non-increasing forward in time), at most backdate_max_s before the entry
            relaxed5 = (
                (np.nan_to_num(perp5, nan=99) <= perp_max + h)
                & (np.nan_to_num(tau5, nan=-9) >= tau_lo - p["tau_hyst"])
                & (np.nan_to_num(tau5, nan=9) <= tau_hi + p["tau_hyst"])
                & (np.nan_to_num(dA5, nan=99) <= dist_max + h)
                & ~excl_h
            )
            a_s = a0  # strict back-dated entry: P_cond / P_emit are measured on the hold from here (not the approach)
            lim = max(prev_end + 1, a_ - frames(tier_param(p, "backdate_max_s", kd, scene.kins[att])))
            while a0 - 1 >= lim and relaxed5[a0 - 1] and dA5[a0 - 1] >= dA5[a0] - 1e-9:
                a0 -= 1
            prev_end = b_
            with np.errstate(all="ignore"):
                sig_tau = fs_ / np.maximum(fL_, 1.0)
                p_perp = p_below(fp_, perp_max, fs_)
                pr = p_perp * (p_below(ft_, tau_hi, sig_tau) - p_below(ft_, tau_lo, sig_tau))
            pr = np.where(np.isnan(fp_), np.nan, pr)
            p_perp = np.where(np.isnan(fp_), np.nan, p_perp)
            pm = window_conf(p_match(scene, d, att), a_, b_)
            pc = window_conf(pr, a_s, b_) * pm
            ev = make_event(
                scene,
                p,
                kind,
                {"defender": d, "attacker": att},
                a0,
                a0,
                b_,
                pc,
                [
                    f"named_spots {spot_id} entered",
                    _fmt("mean perp", float(np.nanmean(fp_[a0 : b_ + 1])), "<=", perp_max, "m"),
                    f"mean tau {np.nanmean(ft_[a0:b_ + 1]):.2f} in [{tau_lo}, {tau_hi}]",
                    f"matchup posterior {pm:.2f}",
                    f"held {(b_ - a0) * DT:.2f} s >= {p['min_s']} s",
                ],
                None,
                state=True,
                p_emit=window_conf(p_perp, a_s, b_),
                mean_perp_m=float(np.nanmean(fp_[a0 : b_ + 1])),
                mean_tau=float(np.nanmean(ft_[a0 : b_ + 1])),
                duration_s=(b_ - a0) * DT,
                backdated_s=(a_ - a0) * DT,
                strict_start=int(a_s),
            )
            if ev:
                out.append(ev)
    return out


def detect_face_guard(scene, **params):
    """FACE_GUARD: named_spots face_guard held >= 1.0 s."""
    p, A = _setup("face_guard", scene, params)
    return _position_hold(scene, p, "face_guard", "face_guard")


def detect_deny(scene, **params):
    """DENY_HOLD: named_spots deny_on_the_line held >= 1.0 s. Frames inside an emitted FACE_GUARD event of the same
    defender are excluded (face_guard owns them); a pass through the face-guard region that is no face-guard hold
    does not block the deny (DEF-T04)."""
    p, A = _setup("deny", scene, params)
    fg = {}
    for e in detect_face_guard(scene):
        m = fg.setdefault(e.actors["defender"], np.zeros(scene.n, dtype=bool))
        # from the strict (5-frame-mean) entry: the relaxed back-dated approach frames of a face guard (loop 2) are
        # not owned by it, so a deny entered on the way in is not blocked
        m[e.attrs.get("strict_start", e.start) : e.end + 1] = True
    return _position_hold(scene, p, "deny_on_the_line", "deny", exclude=fg)


def detect_beaten(scene, **params):
    """BEATEN: during a drive the handler gets closer to the rim than his defender by >= margin for >= min_s."""
    p, A = _setup("beaten", scene, params)
    out = []
    for dr in A["drive"]:
        t, h = dr["t"], dr["handler"]
        d = on_ball_defender(scene, h, t)
        kd, kh = scene.kins[d], scene.kins[h]
        w1 = min(scene.n - 1, t + frames(p["window_s"]))
        sep = kh.r - kd.r  # negative = handler deeper
        sig = sigma_rel(kd, kh, p)
        m = np.zeros(scene.n, dtype=bool)
        m[t : w1 + 1] = np.nan_to_num(sep[t : w1 + 1], nan=9) < -p["margin"]
        rs = [r for r in runs(m) if (r[1] - r[0]) * DT >= p["min_s"] - 1e-9]
        if not rs:
            continue
        a, b = rs[0]
        pc = window_conf(p_below(sep, -p["margin"], sig), a, b)
        ev = make_event(
            scene,
            p,
            "beaten",
            {"defender": d, "handler": h},
            a,
            a,
            b,
            pc,
            [
                _fmt("r_H - r_D", float(np.nanmean(sep[a : b + 1])), "<", -p["margin"], "m"),
                f"for {(b - a) * DT:.2f} s >= {p['min_s']} s",
            ],
            None,
            separation_m=float(-np.nanmin(sep[a : b + 1])),
            trigger_t=t,
        )
        if ev:
            out.append(ev)
    return out


def detect_contain(scene, **params):
    """CONTAIN: the on-ball defender stays between the driver and the rim and the drive is slowed or turned."""
    p, A = _setup("contain", scene, params)
    beaten = {(e.actors["defender"], e.attrs["trigger_t"]) for e in detect_beaten(scene, anchors=A)}
    out = []
    for dr in A["drive"]:
        t, h = dr["t"], dr["handler"]
        d = on_ball_defender(scene, h, t)
        if (d, t) in beaten:
            continue
        kd, kh = scene.kins[d], scene.kins[h]
        w1 = min(scene.n - 1, t + frames(p["window_s"]))
        sd_, _ = seg_dist_arr(kd.x[t : w1 + 1], kd.y[t : w1 + 1], kh.x[t : w1 + 1], kh.y[t : w1 + 1], 0.0, 0.0)
        between = (sd_ <= p["between_max"]) & (kd.r[t : w1 + 1] < kh.r[t : w1 + 1])
        share = float(np.mean(between))
        # DEF-T05: drives still accelerate for 0.5-0.8 s and the beat-to-the-spot slow-down comes later: the peak is
        # taken over the whole window and the slow-down measured from the peak to slow_tail_s past the window
        w2 = min(scene.n - 1, w1 + frames(p["slow_tail_s"]))
        sp = np.nan_to_num(kh.speed[t : w2 + 1], nan=0.0)
        ipk = int(np.argmax(sp[: w1 - t + 1]))
        vmax = float(sp[ipk])
        drop = 1 - float(np.min(sp[ipk:])) / max(vmax, 1e-6)
        sig = float(np.nanmean(kh.sigma_speed[t : w2 + 1])) / max(vmax, 1e-6)
        g = {
            "between": float(p_above(share, p["between_share_min"], 0.1)),
            "slowed": float(p_above(drop, p["slow_drop_min"], sig)),
        }
        ev = make_event(
            scene,
            p,
            "contain",
            {"defender": d, "handler": h},
            t,
            t,
            w1,
            float(np.prod(list(g.values()))),
            [
                f"between handler and rim on {share:.0%} of frames >= {p['between_share_min']:.0%}",
                f"handler speed drop {drop:.0%} >= {p['slow_drop_min']:.0%}",
            ],
            None,
        )
        if ev:
            out.append(ev)
    return out


def detect_back_pressure(scene, **params):
    """BACK_PRESSURE: defender behind the ball (r_D > r_H), fast, closing on the handler and getting within reach."""
    p, A = _setup("back_pressure", scene, params)
    out = []
    for d in scene.defense:
        kd = scene.kins[d]
        for h in scene.offense:
            kh = scene.kins[h]
            held = np.array([scene.holder[t] == h for t in range(scene.n)])
            dd = dist(kd, kh)
            cs = (kd.vx * (kh.x - kd.x) + kd.vy * (kh.y - kd.y)) / np.where(dd > 0, dd, np.nan) - (
                kh.vx * (kh.x - kd.x) + kh.vy * (kh.y - kd.y)
            ) / np.where(dd > 0, dd, np.nan)
            m = (
                held
                & (np.nan_to_num(kd.r - kh.r, nan=-9) > 0)
                & (np.nan_to_num(kd.speed, nan=0) >= p["speed_min"])
                & (np.nan_to_num(cs, nan=0) >= p["closing_min"])
            )
            for a, b in hysteresis(m, m, p["min_s"], p["dwell_frames"]):
                e2 = min(scene.n - 1, b + frames(p["reach_window_s"]))
                md = float(np.nanmin(dd[a : e2 + 1]))
                sig = float(np.nanmean(sigma_rel(kd, kh, p)[a : e2 + 1]))
                pc = window_conf(p_above(cs, p["closing_min"], np.sqrt(2) * kd.sigma_speed), a, b) * float(
                    p_below(md, p["reach_max"], sig)
                )
                ev = make_event(
                    scene,
                    p,
                    "back_pressure",
                    {"defender": d, "handler": h},
                    a,
                    a,
                    e2,
                    pc,
                    [
                        f"behind the ball, speed >= {p['speed_min']} m/s, closing >= {p['closing_min']} m/s for {(b - a) * DT:.2f} s",
                        _fmt("min dist", md, "<=", p["reach_max"], "m"),
                    ],
                    None,
                    min_dist_m=md,
                )
                if ev:
                    out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# DM-P18 box-out, DM-P21 get-back, DM-P22 safety back
# --------------------------------------------------------------------------------------
def detect_box_out(scene, **params):
    """BOX_OUT: named_spots box_out_position held >= min_contact_s (named_spots 0.4 s), starting between shot
    release and rim contact (+ jitter); classic when contact >= classic_s."""
    p, A = _setup("box_out", scene, params)
    out = []
    for sh in A["shot"]:
        tr = sh["t_rel"]
        t_rim = sh.get("t_rim") or min(scene.n - 1, tr + frames(p["rim_fallback_s"]))
        w1 = min(scene.n - 1, t_rim + frames(p["after_rim_s"]))
        for d in scene.defense:
            kd = scene.kins[d]
            for tgt in scene.offense:
                if tgt == sh["shooter"]:
                    continue
                kt = scene.kins[tgt]
                sp_ = SPOTS["box_out_position"]
                enter = np.zeros(scene.n, dtype=bool)
                for t in range(tr, w1 + 1):
                    enter[t] = bool(sp_.inside(kd.x[t], kd.y[t], ax_=kt.x[t], ay_=kt.y[t]))
                if not enter.any():
                    continue
                dd = dist(kd, kt)
                sd_, _ = seg_dist_arr(kd.x, kd.y, kt.x, kt.y, 0.0, 0.0)
                sig = sigma_rel(kd, kt, p)
                h = hyst_h(np.nanmedian(sig[tr : w1 + 1]), p)
                bo = SPOT_NUM["box_out"]
                stay = (
                    (np.nan_to_num(dd, nan=99) <= bo["dist_max"] + h)
                    & (sd_ <= bo["line_max"] + h)
                    & (np.nan_to_num(kd.r - kt.r, nan=9) < p["rim_side_tol"])
                )
                for a, b in hysteresis(enter, stay, p["min_contact_s"], 3):
                    if a > t_rim + frames(p["start_jitter_s"]):
                        continue
                    pr = p_below(dd, bo["dist_max"], sig) * p_below(sd_, bo["line_max"], sig)
                    pc = window_conf(pr, a, b)
                    pre = slice(max(0, a - frames(p["effect_pre_s"])), a)
                    v_pre = float(np.nanmean(kt.v_r[pre])) if a > 0 else float("nan")
                    v_in = float(np.nanmean(kt.v_r[a : b + 1]))
                    eff = (1 - v_in / v_pre) if v_pre and v_pre > 0.5 else float("nan")
                    dur = (b - a) * DT
                    ev = make_event(
                        scene,
                        p,
                        "box_out",
                        {"defender": d, "target": tgt},
                        a,
                        a,
                        b,
                        pc,
                        [
                            "named_spots box_out_position",
                            f"contact {dur:.2f} s >= {p['min_contact_s']} s",
                            f"start {(a - tr) * DT:.2f} s after release (rim contact at {(t_rim - tr) * DT:.2f} s)",
                        ],
                        None,
                        contact_duration_s=dur,
                        classic=bool(dur >= p["classic_s"]),
                        effect_pct=eff,
                        shot_t=tr,
                    )
                    if ev:
                        out.append(ev)
    return out


def detect_get_back(scene, **params):
    """GET_BACK: after a change of possession, speed toward the defended rim >= onset_v_r held >= hold_s
    (t0 = onset). Requires a supplied 'cop' anchor (never derived from XY)."""
    p, A = _setup("get_back", scene, params)
    out = []
    for cp in A["cop"]:
        t = cp["t"]
        w1 = min(scene.n - 1, t + frames(p["onset_window_s"]))
        for d in scene.defense:
            kd = scene.kins[d]
            vr = np.nan_to_num(kd.v_r, nan=0.0)
            m = np.zeros(scene.n, dtype=bool)
            m[t:] = vr[t:] >= p["onset_v_r"]
            rs = [r for r in runs(m) if r[0] <= w1 and (r[1] - r[0]) * DT >= p["hold_s"] - 1e-9]
            if not rs:
                continue
            a, b = rs[0]
            pc = window_conf(p_above(kd.v_r, p["onset_v_r"], kd.sigma_speed), a, a + frames(p["hold_s"]))
            sp = np.nan_to_num(kd.speed, nan=0.0)
            sprint = any((rb - ra) * DT >= p["sprint_s"] for ra, rb in runs(sp[a : b + 1] > p["sprint_speed"]))
            ev = make_event(
                scene,
                p,
                "get_back",
                {"defender": d},
                a,
                a,
                b,
                pc,
                [f"v_r >= {p['onset_v_r']} m/s held {(b - a) * DT:.2f} s >= {p['hold_s']} s"],
                None,
                onset_delay_s=(a - t) * DT,
                retreat_speed=float(np.nanmean(kd.speed[a : b + 1])),
                sprint_back=sprint,
                cop_t=t,
            )
            if ev:
                out.append(ev)
    return out


def detect_safety_back(scene, **params):
    """SAFETY_BACK: at shot release + check_s, shooting-team players beyond r_min moving away from the
    attacked rim at >= v_away_min (floor balance of the team that will defend next)."""
    p, A = _setup("safety_back", scene, params)
    out = []
    for sh in A["shot"]:
        t = min(scene.n - 1, sh["t_rel"] + frames(p["check_s"]))
        for o in scene.offense:
            k = scene.kins[o]
            r, v_away = mean_val(k.r, t), -mean_val(k.v_r, t)
            if np.isnan(r):
                continue
            pc = float(p_above(r, p["r_min"], rel_floor(p, k))) * float(
                p_above(v_away, p["v_away_min"], k.sigma_speed[t])
            )
            ev = make_event(
                scene,
                p,
                "safety_back",
                {"player": o, "shooter": sh["shooter"]},
                sh["t_rel"],
                sh["t_rel"],
                t,
                pc,
                [_fmt("r", r, ">", p["r_min"], "m"), _fmt("speed away from rim", v_away, ">=", p["v_away_min"], "m/s")],
                None,
                shooter_back=bool(o == sh["shooter"]),
            )
            if ev:
                out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# DM-A01 rotate, DM-A02 switch, DM-A04 x-out, DM-A05 sink-and-fill, guard-two
# --------------------------------------------------------------------------------------
def _flips(scene, p):
    """Matchup flips per defender between consecutive stable top-1 runs (>= old_min_s); short transitional runs
    (a rotating defender passing another attacker's canonical point) are skipped. t = first frame after the old
    run where P(new) > P(old). Returns dicts (d, t, old, new, end, censored, old_start)."""
    out = []
    mu = matchup_posterior(scene)
    jt = joint_top1(scene)
    # loop 4 L4-FLIP-HALFCOURT: a switch / rotation changes an established half-court assignment; matchups picked up and
    # sorted while the ball is beyond half court (transition) are not one. The flip needs the ball in the frontcourt and
    # the old run >= old_min_s of frontcourt frames.
    front = np.nan_to_num(ball_xy(scene)[1], nan=0.0) <= C["HALF_Y"]
    # loop 4 L4-FLIP-REBOUND: from a shot to the rebound defenders hit whoever is nearest; a flip with the ball over a rim
    # within [t - rim_phase_back_s, t + rim_phase_fwd_s] is a rebound assignment, not a switch / rotation
    rim = _near_rim(scene, GLOBAL["rim_ball_r"])
    rb, rf = frames(GLOBAL["rim_phase_back_s"]), frames(GLOBAL["rim_phase_fwd_s"])
    for d in scene.defense:
        rs = [r for r in _runs_absorb(jt[d], frames(p["flicker_s"])) if r[2] is not None]
        stable = [r for r in rs if (r[1] - r[0]) * DT >= p["old_min_s"] or r[1] == scene.n - 1]
        for i, ((a0, b0, old), (a1, b1, new)) in enumerate(zip(stable, stable[1:])):
            if old == new:
                continue
            # DEF-T03: A -> B -> A with the B run shorter than persist_s is a help excursion that returned (a recover),
            # not a rotation back to A
            if i >= 1 and stable[i - 1][2] == new and (b0 - a0) * DT < p["persist_s"]:
                continue
            po, pn = mu["post"][d][mu["attackers"].index(old)], mu["post"][d][mu["attackers"].index(new)]
            t = next((t for t in range(b0 + 1, a1 + 1) if pn[t] > po[t]), a1)
            if not front[t] or (np.sum(front[a0 : b0 + 1]) - 1) * DT < p["old_min_s"] - 1e-9:
                continue
            if rim[max(0, t - rb) : t + rf + 1].any():
                continue
            out.append(dict(d=d, t=t, old=old, new=new, end=b1, censored=b1 == scene.n - 1, old_start=a0))
    return out


def _guard_two_intervals(scene, p):
    cache = _cache(scene)
    if "g2" not in cache:
        cache["g2"] = detect_guard_two(scene)
    return cache["g2"]


def _swaps(scene, p, A):
    """Reciprocal matchup exchanges, classified as x_out (pass-triggered, crossing paths) or switch."""
    fl = _flips(scene, p)
    used, swaps = set(), []
    for i, f1 in enumerate(fl):
        for j, f2 in enumerate(fl):
            if j <= i or f1["d"] == f2["d"] or (i in used) or (j in used):
                continue
            if f1["old"] == f2["new"] and f1["new"] == f2["old"] and abs(f1["t"] - f2["t"]) <= frames(p["pair_max_s"]):
                used.update((i, j))
                swaps.append((f1, f2))
    return swaps, fl, used


def _paths_cross(k1, k2, a, b, step=3):
    """Spatial crossing of two smoothed polylines over [a, b]: (crossed, point, angle_deg)."""
    P = [(k1.x[t], k1.y[t]) for t in range(a, b + 1, step)]
    Q = [(k2.x[t], k2.y[t]) for t in range(a, b + 1, step)]

    def inter(p1, p2, q1, q2):
        d = (p2[0] - p1[0]) * (q2[1] - q1[1]) - (p2[1] - p1[1]) * (q2[0] - q1[0])
        if abs(d) < 1e-12:
            return None
        u = ((q1[0] - p1[0]) * (q2[1] - q1[1]) - (q1[1] - p1[1]) * (q2[0] - q1[0])) / d
        v = ((q1[0] - p1[0]) * (p2[1] - p1[1]) - (q1[1] - p1[1]) * (p2[0] - p1[0])) / d
        if 0 <= u <= 1 and 0 <= v <= 1:
            return (p1[0] + u * (p2[0] - p1[0]), p1[1] + u * (p2[1] - p1[1]))
        return None

    for i in range(len(P) - 1):
        for j in range(len(Q) - 1):
            if any(np.isnan(v) for v in (*P[i], *P[i + 1], *Q[j], *Q[j + 1])):
                continue
            pt = inter(P[i], P[i + 1], Q[j], Q[j + 1])
            if pt is not None:
                a1 = math.atan2(P[-1][1] - P[0][1], P[-1][0] - P[0][0])
                a2 = math.atan2(Q[-1][1] - Q[0][1], Q[-1][0] - Q[0][0])
                ang = abs((math.degrees(a1 - a2) + 180) % 360 - 180)
                return True, pt, min(ang, 180 - ang)
    return False, None, 0.0


def _classify_swap(scene, p, px, A, f1, f2):
    """X-out if a pass released within xout_window_s before the later flip and the two paths cross."""
    k1, k2 = scene.kins[f1["d"]], scene.kins[f2["d"]]
    tl = max(f1["t"], f2["t"])
    for ps in sorted(A["pass"], key=lambda x: -x["t_rel"]):
        if 0 <= tl - ps["t_rel"] <= frames(px["window_s"]):
            b = min(scene.n - 1, ps["t_rel"] + frames(px["window_s"]))
            crossed, pt, ang = _paths_cross(k1, k2, ps["t_rel"], b)
            ch1 = math.hypot(k1.x[b] - k1.x[ps["t_rel"]], k1.y[b] - k1.y[ps["t_rel"]])
            ch2 = math.hypot(k2.x[b] - k2.x[ps["t_rel"]], k2.y[b] - k2.y[ps["t_rel"]])
            if crossed and ang >= px["cross_angle_min"] and min(ch1, ch2) >= px["chord_min"]:
                return "x_out", dict(pass_=ps, point=pt, angle=ang, chords=(ch1, ch2))
    return "switch", None


def detect_rotate(scene, **params):
    """ROTATE: a single persistent matchup change (not reciprocal, not inside a guard-two interval)."""
    p, A = _setup("rotate", scene, params)
    ps = merged_params("switch")
    ps["flicker_s"], ps["old_min_s"], ps["persist_s"] = p["flicker_s"], p["old_min_s"], p["persist_s"]
    swaps, fl, used = _swaps(scene, ps, A)
    g2 = _guard_two_intervals(scene, p)
    out = []
    for i, f in enumerate(fl):
        if i in used:
            continue
        if (f["end"] - f["t"]) * DT < p["persist_s"] and not (
            f["censored"] and (f["end"] - f["t"]) * DT >= p["censored_min_s"]
        ):
            continue
        if any(
            e.actors["defender"] == f["d"]
            and {e.actors["a1"], e.actors["a2"]} == {f["old"], f["new"]}
            and e.start - frames(p["guard_two_margin_s"]) <= f["t"] <= e.end + frames(p["guard_two_margin_s"])
            for e in g2
        ):
            continue
        tq = min(scene.n - 1, f["t"] + frames(p["check_s"]))
        pn = float(p_match(scene, f["d"], f["new"])[tq])
        pc = window_conf(p_match(scene, f["d"], f["new"]), f["t"], f["end"]) * (1.0 if pn >= p["p_new_min"] else 0.0)
        kd, kn = scene.kins[f["d"]], scene.kins[f["new"]]
        vt = np.nan_to_num(v_to(kd, kn.x, kn.y), nan=0)
        lat_t = next((t for t in range(max(0, f["t"] - frames(p["move_back_s"])), f["end"]) if vt[t] >= p["move_v"]), None)
        trig = None
        for key in ("pass", "drive", "screen"):
            for x in A[key]:
                tt = x.get("t_rel", x.get("t", x.get("t0")))
                if 0 <= f["t"] - tt <= frames(p["trigger_lookback_s"]) and (trig is None or tt > trig[1]):
                    trig = (key, tt)
        ev = make_event(
            scene,
            p,
            "rotate",
            {"defender": f["d"], "from": f["old"], "to": f["new"]},
            f["t"],
            f["t"],
            f["end"],
            pc,
            [
                f"top-1 {f['old']} -> {f['new']}, P(new) {pn:.2f} >= {p['p_new_min']} at t0+{p['check_s']} s",
                f"persists {(f['end'] - f['t']) * DT:.2f} s >= {p['persist_s']} s"
                + (" (censored)" if f["censored"] else ""),
            ],
            None,
            censored=f["censored"],
            trigger=trig[0] if trig else None,
            latency_s=None if (trig is None or lat_t is None) else (lat_t - trig[1]) * DT,
            chord_m=float(math.hypot(kd.x[f["end"]] - kd.x[f["t"]], kd.y[f["end"]] - kd.y[f["t"]])),
        )
        if ev:
            out.append(ev)
    return out


def _screen_frame(scene, sc, p):
    """Screen geometry (DM-RULE-05 revised): S, H, X-ball, X-big, depth axis e_r (S -> rim, named_spots
    pnr_big_* frame) and H's pre-screen travel direction u (fallback: perpendicular to e_r toward H)."""
    t0 = sc["t0"]
    S, H = sc["screener"], sc["handler"]
    pre = max(0, t0 - frames(p["pre_screen_s"]))
    xball = sc.get("xball") or on_ball_defender(scene, H, pre)
    xbig = sc.get("xbig") or on_ball_defender(scene, S, pre)
    ks, kh = scene.kins[S], scene.kins[H]
    sx, sy = mean_xy(ks, t0)
    rn = math.hypot(sx, sy)
    er = (-sx / rn, -sy / rn) if rn > 0 else (0.0, -1.0)
    vx, vy = float(np.nanmean(kh.vx[pre : t0 + 1])), float(np.nanmean(kh.vy[pre : t0 + 1]))
    if math.hypot(vx, vy) >= p["u_min_speed"]:
        u, src = (vx / math.hypot(vx, vy), vy / math.hypot(vx, vy)), "velocity"
    else:
        hx, hy = mean_xy(kh, pre)
        pr = (-er[1], er[0])
        sgn = 1.0 if ((sx - hx) * pr[0] + (sy - hy) * pr[1]) >= 0 else -1.0
        u, src = (sgn * pr[0], sgn * pr[1]), "rim"
    return dict(t0=t0, S=S, H=H, xball=xball, xbig=xbig, sx=sx, sy=sy, er=er, u=u, u_src=src)


def _depth(scene, F, oid, t):
    k = scene.kins[oid]
    return (k.x[t] - F["sx"]) * F["er"][0] + (k.y[t] - F["sy"]) * F["er"][1]


def _lat(scene, F, oid, t):
    k = scene.kins[oid]
    return (k.x[t] - F["sx"]) * F["u"][0] + (k.y[t] - F["sy"]) * F["u"][1]


def detect_switch(scene, **params):
    """SWITCH: reciprocal matchup exchange (flips <= pair_max_s apart, both persisting >= persist_s), t0 = the
    geometric exchange (closest approach of the two defenders); timing vs the screen and intensity classes."""
    p, A = _setup("switch", scene, params)
    px = merged_params("x_out")
    swaps, _, _ = _swaps(scene, p, A)
    out = []
    for f1, f2 in swaps:
        if _classify_swap(scene, p, px, A, f1, f2)[0] != "switch":
            continue
        dur = min(f1["end"] - f1["t"], f2["end"] - f2["t"]) * DT
        cens = f1["censored"] or f2["censored"]
        if dur < p["persist_s"] and not (cens and dur >= p["censored_min_s"]):
            continue
        k1, k2 = scene.kins[f1["d"]], scene.kins[f2["d"]]
        lo = max(0, min(f1["t"], f2["t"]) - frames(p["exchange_back_s"]))
        hi = min(scene.n - 1, max(f1["t"], f2["t"]) + frames(p["exchange_fwd_s"]))
        d12 = dist(k1, k2)
        # loop 2 (SWITCH-early-t0): the exchange happens while a defender moves; with both defenders stationary
        # (MP-09 s2 < stand_s2) an AR(1) dip of a shallow closest approach (true 2.33 -> 1.77 m) was taken at the clip
        # start (t0 frames 5-15 vs truth 46)
        moving = (np.nan_to_num(k1.stationary_s2, nan=0.0) >= p["stand_s2"]) | (
            np.nan_to_num(k2.stationary_s2, nan=0.0) >= p["stand_s2"]
        )
        seg = np.where(moving[lo : hi + 1], d12[lo : hi + 1], np.nan)
        if np.all(np.isnan(seg)):
            seg = d12[lo : hi + 1]
        tx = lo + int(np.nanargmin(seg))
        # timing vs the nearest screen involving either attacker
        scr = [s for s in A["screen"] if {s["screener"], s["handler"]} & {f1["old"], f1["new"]}]
        timing, F = "no_screen", None
        if scr:
            sc = min(scr, key=lambda s: abs(s["t0"] - tx))
            dt_ = (tx - sc["t0"]) * DT
            if p["pre_lo_s"] <= dt_ <= p["pre_hi_s"]:
                timing = "pre_switch"
            elif p["pre_hi_s"] < dt_ <= p["on_time_hi_s"]:
                timing = "on_time"
            elif p["on_time_hi_s"] < dt_ <= p["late_hi_s"]:
                timing = "late"
            elif dt_ > p["late_hi_s"]:
                timing = "very_late"
            else:
                timing = "unclassified"
            F = _screen_frame(scene, sc, merged_params("ball_screen"))
            ball_att = sc["handler"]
        else:
            bx, by = ball_xy(scene)
            ball_att = min(
                (f1["old"], f1["new"]),
                key=lambda a: math.hypot(scene.kins[a].x[tx] - bx[tx], scene.kins[a].y[tx] - by[tx]),
            )
        nd = f1["d"] if f1["new"] == ball_att else f2["d"]
        kn, kb = scene.kins[nd], scene.kins[ball_att]
        dd = dist(kn, kb)
        t_end = min(scene.n - 1, tx + frames(p["hard_window_s"]))
        d_start, d_min = mean_val(dd, tx), float(np.nanmin(dd[tx : t_end + 1]))
        sig = float(np.nanmean(sigma_rel(kn, kb, p)[tx : t_end + 1]))
        lam = None
        if F is not None:
            mx, my = (k1.x[tx] + k2.x[tx]) / 2, (k1.y[tx] + k2.y[tx]) / 2
            lam = (mx - F["sx"]) * F["u"][0] + (my - F["sy"]) * F["u"][1]
        p_hard_close = float(p_above(d_start, p["hard_from_min"], sig)) * float(p_below(d_min, p["hard_to_max"], sig))
        p_hard = max(p_hard_close, float(p_below(lam, 0.0, sig)) if lam is not None else 0.0)
        t_soft = min(scene.n - 1, tx + frames(p["soft_hold_s"]))
        cushion = float(np.nanmin(dd[tx : t_soft + 1]))
        p_soft = float(p_above(cushion, p["soft_cushion_min"], sig)) * (
            float(p_above(lam, p["soft_lambda_min"], sig)) if lam is not None else 1.0
        )
        p_soft *= 1 - p_hard
        intens = {"hard": p_hard, "soft": p_soft, "neutral": max(0.0, 1 - p_hard - p_soft)}
        iclass = max(intens, key=intens.get)
        pc = min(
            window_conf(p_match(scene, f1["d"], f1["new"]), f1["t"], f1["end"]),
            window_conf(p_match(scene, f2["d"], f2["new"]), f2["t"], f2["end"]),
        )
        ev = make_event(
            scene,
            p,
            "switch",
            {"d1": f1["d"], "d2": f2["d"], "a1": f1["old"], "a2": f1["new"]},
            tx,
            min(f1["t"], f2["t"], tx),
            max(f1["end"], f2["end"]),
            pc,
            [
                f"{f1['d']}: {f1['old']}->{f1['new']}, {f2['d']}: {f2['old']}->{f2['new']}, flips {abs(f1['t'] - f2['t']) * DT:.2f} s apart <= {p['pair_max_s']} s",
                f"persist {dur:.2f} s >= {p['persist_s']} s" + (" (censored)" if cens else ""),
                f"timing {timing}",
                f"intensity {iclass}: closing {d_start:.2f}->{d_min:.2f} m, cushion {cushion:.2f} m",
            ],
            intens,
            timing=timing,
            intensity=iclass,
            exchange_lambda_m=lam,
            new_ball_defender=nd,
            hmm_flip_lag_s=(max(f1["t"], f2["t"]) - tx) * DT,
            censored=cens,
            persistence_s=dur,
            coverage_label=bool(dur >= p["coverage_persist_s"] or cens),
        )
        if ev:
            out.append(ev)
    return out


def detect_x_out(scene, **params):
    """X_OUT: reciprocal exchange of two defenders whose paths cross within window_s after a pass (t0 = release)."""
    p, A = _setup("x_out", scene, params)
    ps = merged_params("switch")
    swaps, _, _ = _swaps(scene, ps, A)
    out = []
    for f1, f2 in swaps:
        cls, info = _classify_swap(scene, ps, p, A, f1, f2)
        if cls != "x_out":
            continue
        dur = min(f1["end"] - f1["t"], f2["end"] - f2["t"]) * DT
        if dur < p["persist_s"] and not (f1["censored"] or f2["censored"]):
            continue
        pc = min(
            window_conf(p_match(scene, f1["d"], f1["new"]), f1["t"], f1["end"]),
            window_conf(p_match(scene, f2["d"], f2["new"]), f2["t"], f2["end"]),
        )
        tr = info["pass_"]["t_rel"]
        ev = make_event(
            scene,
            p,
            "x_out",
            {"d1": f1["d"], "d2": f2["d"], "a1": f1["old"], "a2": f1["new"]},
            tr,
            tr,
            max(f1["end"], f2["end"]),
            pc,
            [
                f"reciprocal exchange within {p['window_s']} s of the pass at frame {tr}",
                f"paths cross at ({info['point'][0]:.1f}, {info['point'][1]:.1f}), angle {info['angle']:.0f} deg >= {p['cross_angle_min']} deg",
                f"chords {info['chords'][0]:.1f} / {info['chords'][1]:.1f} m >= {p['chord_min']} m",
            ],
            None,
            skip=bool(info["pass_"].get("skip")),
            crossing_point=info["point"],
            crossing_angle_deg=info["angle"],
        )
        if ev:
            out.append(ev)
    return out


def detect_sink_and_fill(scene, **params):
    """SINK_AND_FILL: a SINK by Da and, within window_s of its onset, Db shifting >= fill_min toward Da's man,
    with no path crossing (else X-out)."""
    p, A = _setup("sink_and_fill", scene, params)
    # loop 2 NEW-R2: global overrides of this call reach the inner SINK (it used to get the anchors only)
    sinks = detect_sink(scene, anchors=A, **{k: v for k, v in params.items() if k in GLOBAL})
    out = []
    for s in sinks:
        da, am = s.actors["defender"], s.actors["attacker"]
        ka = scene.kins[am]
        t0 = s.t0
        w1 = min(scene.n - 1, t0 + frames(p["window_s"]))
        for db in scene.defense:
            if db == da or db == on_ball_defender(scene, s.actors["handler"], s.attrs["trigger_t"]):
                continue
            kb = scene.kins[db]
            dd = dist(kb, ka)
            shift = mean_val(dd, t0) - float(np.nanmin(dd[t0 : w1 + 1]))
            crossed, _, _ = _paths_cross(scene.kins[da], kb, t0, w1)
            sig = float(np.nanmean(sigma_rel(kb, ka, p)[t0 : w1 + 1])) * math.sqrt(2)
            p_fill = float(p_above(shift, p["fill_min"], sig)) * (0.0 if crossed else 1.0)
            pc = s.attrs["p_cond"] * p_fill
            ev = make_event(
                scene,
                p,
                "sink_and_fill",
                {"sinker": da, "filler": db, "attacker": am},
                t0,
                t0,
                w1,
                pc,
                [
                    f"sink by {da} (p {s.attrs['p_cond']:.2f})",
                    _fmt("filler shift toward vacated man", shift, ">=", p["fill_min"], "m"),
                    "no path crossing",
                ],
                None,
                p_emit=min(s.attrs["p_cond"], p_fill),
                p_fill=round(p_fill, 4),
            )
            if ev:
                out.append(ev)
    return out


def detect_guard_two(scene, **params):
    """GUARD_TWO: one defender between two attackers that no other defender guards (zone-in-man, sagging off
    a non-shooter, cover-two in transition)."""
    p, A = _setup("guard_two", scene, params)
    out = []
    off = scene.offense
    for d in scene.defense:
        kd = scene.kins[d]
        for i in range(len(off)):
            for j in range(i + 1, len(off)):
                k1, k2 = scene.kins[off[i]], scene.kins[off[j]]
                # loop 4 L4-G2-SEP: the attackers must be apart; a defender next to two attackers who stand together (a
                # screen, a hand-off, a stack) is in that action, not guarding two
                apart = np.nan_to_num(_mean5(dist(k1, k2)), nan=0.0) >= p["sep_min"]
                if not apart.any():
                    continue
                d1, d2 = dist(kd, k1), dist(kd, k2)
                sd_, tau = seg_dist_arr(kd.x, kd.y, k1.x, k1.y, k2.x, k2.y)
                free = np.ones(scene.n, dtype=bool)
                for o in scene.defense:
                    if o == d:
                        continue
                    ko = scene.kins[o]
                    free &= (np.nan_to_num(dist(ko, k1), nan=99) > p["others_min"]) & (
                        np.nan_to_num(dist(ko, k2), nan=99) > p["others_min"]
                    )
                m = (
                    (np.nan_to_num(np.abs(d1 - d2), nan=99) <= p["balance_max"])
                    & (np.nan_to_num(d1, nan=99) <= p["reach_max"])
                    & (np.nan_to_num(d2, nan=99) <= p["reach_max"])
                    & (sd_ <= p["between_max"])
                    & free
                    & apart
                )
                # DEF-T18: relaxed stay (balance / between + h) and dwell bridging, so noise does not split one hold
                h = hyst_h(float(np.nanmedian(sigma_rel(kd, k1, p))), p)
                stay = (
                    (np.nan_to_num(np.abs(d1 - d2), nan=99) <= p["balance_max"] + h)
                    & (np.nan_to_num(d1, nan=99) <= p["reach_max"])
                    & (np.nan_to_num(d2, nan=99) <= p["reach_max"])
                    & (sd_ <= p["between_max"] + h)
                    & free
                    & apart
                )
                trans = (k1.y > C["HALF_Y"]) | (k2.y > C["HALF_Y"])
                # loop 4 L4-G2-OUTNUMBERED: cover-two is a numbers disadvantage, D the only defender between the two
                # attackers and the rim (every other defender farther from the rim than the farther attacker)
                rfar = np.fmax(k1.r, k2.r)
                outnum = np.ones(scene.n, dtype=bool)
                for o in scene.defense:
                    if o != d:
                        outnum &= np.nan_to_num(scene.kins[o].r, nan=0.0) > rfar
                for a, b in hysteresis(m, stay, p["min_s_transition"], p["dwell_frames"]):
                    tr_ = bool(np.mean(trans[a : b + 1]) > 0.5)
                    if (b - a) * DT < (p["min_s_transition"] if tr_ else p["min_s"]) - 1e-9:
                        continue
                    if tr_ and np.mean(outnum[a : b + 1]) < 0.5:
                        continue
                    sig = sigma_rel(kd, k1, p)
                    pc = window_conf(p_below(np.abs(d1 - d2), p["balance_max"], sig * math.sqrt(2)), a, b)
                    ev = make_event(
                        scene,
                        p,
                        "guard_two",
                        {"defender": d, "a1": off[i], "a2": off[j]},
                        a,
                        a,
                        b,
                        pc,
                        [
                            _fmt("|d1-d2|", float(np.nanmean(np.abs(d1 - d2)[a : b + 1])), "<=", p["balance_max"], "m"),
                            f"no other defender within {p['others_min']} m of either",
                            f"{(b - a) * DT:.2f} s",
                        ],
                        None,
                        state=True,
                        transition=tr_,
                        variant="cover_two" if tr_ else "zone_in_man",
                    )
                    if ev:
                        out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# Ball-screen coverage (DM-A08..A13) and off-ball screens (DM-A15)
# --------------------------------------------------------------------------------------
def _rim_dist(x, y):
    """Distance to the nearer rim centre (attacked rim at the origin, the other rim FAR_END_Y - RIM_Y_FROM_END up the floor)."""
    far = C["FAR_END_Y"] - C["RIM_Y_FROM_END"]
    with np.errstate(all="ignore"):
        return np.fmin(np.hypot(x, y), np.hypot(x, np.asarray(y) - far))


def _near_rim(scene, r):
    """Per frame: the raw ball XY (smoothed when no raw) is within r of either rim centre (NaN -> False)."""
    braw = scene.ball_raw if scene.ball_raw is not None else (
        (scene.ball.x, scene.ball.y) if scene.ball is not None else None)
    if braw is None:
        return np.zeros(scene.n, dtype=bool)
    return np.nan_to_num(_rim_dist(np.asarray(braw[0], float), np.asarray(braw[1], float)), nan=np.inf) <= r


def detect_trap(scene, **params):
    """TRAP: two defenders both <= enter_dist of the holder and <= pair_dist of each other for >= min_s,
    exit at +h (DM-RULE-07); one trapper may be Kalman-carried (interp_short) with conf x 0.8."""
    p, A = _setup("trap", scene, params)
    out = []
    dfn = scene.defense
    hold = np.array([scene.holder[t] for t in range(scene.n)], dtype=object)
    # loop 4 L4-TRAP-RIM: the holder relation (nearest attacker within HOLD_R of the ball XY) is no hold while the ball
    # is over a rim (shot, tip, rebound scramble; globals.rim_ball_r) or the 'handler' stands in the restricted area
    at_rim = _near_rim(scene, p["rim_ball_r"])
    for i in range(len(dfn)):
        for j in range(i + 1, len(dfn)):
            k1, k2 = scene.kins[dfn[i]], scene.kins[dfn[j]]
            for h in scene.offense:
                kh = scene.kins[h]
                held = np.array([v == h for v in hold])
                held_br = held.copy()
                for a, b in runs(~held):  # bridge short flight/None gaps inside the hold
                    if b - a + 1 <= 3 and a > 0 and b < scene.n - 1 and held[a - 1] and held[b + 1]:
                        held_br[a : b + 1] = True
                held_br &= ~at_rim & (np.nan_to_num(_rim_dist(kh.x, kh.y), nan=0.0) >= C["RA_R"])
                d1, d2, d12 = dist(k1, kh), dist(k2, kh), dist(k1, k2)
                nn = lambda v: np.nan_to_num(v, nan=99)  # noqa: E731
                enter = (
                    held_br & (nn(d1) <= p["enter_dist"]) & (nn(d2) <= p["enter_dist"]) & (nn(d12) <= p["pair_dist"])
                )
                stay = (
                    held_br
                    & (nn(d1) <= p["enter_dist"] + p["exit_h"])
                    & (nn(d2) <= p["enter_dist"] + p["exit_h"])
                    & (nn(d12) <= p["pair_dist"] + p["exit_h"])
                )
                for a, b in hysteresis(enter, stay, p["min_s"], p["dwell_frames"]):
                    # DEF-T01 commitment test: a short stay that one defender abandons (retreats >= release_dist within
                    # release_s) while H still holds the ball is a dig / show, not a trap. The stay is the time both
                    # 5-frame-mean distances are inside enter_dist (the exit hysteresis would lengthen it).
                    inside = (np.nan_to_num(_mean5(d1)[a : b + 1], nan=99) <= p["enter_dist"]) & (
                        np.nan_to_num(_mean5(d2)[a : b + 1], nan=99) <= p["enter_dist"]
                    )
                    hold_s = float(np.sum(inside)) * DT
                    still_held = b + 1 < scene.n and bool(held_br[b + 1])
                    if hold_s < p["trap_commit_s"] and still_held:
                        e3 = min(scene.n - 1, b + frames(p["trap_release_s"]))
                        # retreat measured from the closest 5-frame-mean distance during the stay (the stay ends at
                        # the exit threshold, part of the way back already)
                        rel = [
                            float(np.nanmax(dk[b : e3 + 1])) - float(np.nanmin(_mean5(dk)[a : b + 1])) if e3 > b else 0.0
                            for dk in (d1, d2)
                        ]
                        if max(rel) >= p["trap_release_dist"]:
                            continue
                    # loop 4 L4-TRAP-MOVING: a trap stops the ball; a handler who runs (median smoothed speed over the stay
                    # above the walk edge) is driving or pushing in transition past two defenders, not trapped
                    if float(np.nanmedian(kh.speed[a : b + 1])) > p["handler_v_max"]:
                        continue
                    # loop 4 L4-TRAP-SHOT: a trap takes the ball out of H's hands (pass / turnover); when H's own shot
                    # reaches a rim (ball XY within rim_ball_r) within shot_after_s of the stay end, no other attacker
                    # holding in between, the two defenders were contesting a drive / post move, not trapping
                    e_s = min(scene.n - 1, b + frames(p["shot_after_s"]))
                    shot = False
                    for t_ in range(b, e_s + 1):
                        if at_rim[t_]:
                            shot = True
                            break
                        if hold[t_] is not None and hold[t_] != h:
                            break
                    if shot:
                        continue
                    # loop 2 (DEF-T18 trap entry late): back-date t0 while both 5-frame-mean distances are inside the
                    # middle of the hysteresis band (enter_dist + exit_h / 2, as p_emit), H holds, and the trappers are still closing
                    # (the larger 5-frame-mean distance non-increasing forward in time), at most backdate_max_s
                    m1, m2, m12 = _mean5(d1), _mean5(d2), _mean5(d12)
                    dmax5 = np.fmax(m1, m2)
                    t0_ = a
                    lim = max(0, a - frames(tier_param(p, "backdate_max_s", k1, k2, kh)))
                    while (
                        t0_ - 1 >= lim
                        and held_br[t0_ - 1]
                        and nn(m1[t0_ - 1]) <= p["enter_dist"] + p["exit_h"] / 2
                        and nn(m2[t0_ - 1]) <= p["enter_dist"] + p["exit_h"] / 2
                        and nn(m12[t0_ - 1]) <= p["pair_dist"] + p["exit_h"] / 2
                        and dmax5[t0_ - 1] >= dmax5[t0_] - 1e-9
                    ):
                        t0_ -= 1
                    s1, s2 = sigma_rel(k1, kh, p), sigma_rel(k2, kh, p)
                    # DEF-T02(c) / DEF-T12(b): conf (P_cond) on the entry threshold, not the exit threshold; existence
                    # (p_emit) at the middle of the hysteresis band (enter + exit_h / 2), so a 1.75 m near miss is not
                    # emitted while a true 1.2-1.3 m trapper (P(d <= 1.5) ~ 0.6-0.8 under noise) still is
                    pc = window_conf(
                        p_below(d1, p["enter_dist"], s1) * p_below(d2, p["enter_dist"], s2),
                        a,
                        b,
                    )
                    mid = p["enter_dist"] + p["exit_h"] / 2
                    pe = window_conf(p_below(d1, mid, s1) * p_below(d2, mid, s2), a, b)
                    x, y = kh.x[a], kh.y[a]
                    m_ = math.degrees(math.atan2(y, abs(x)))
                    if y > C["HALF_Y"]:
                        loc = "press_trap"
                    elif m_ <= p["corner_angle_max_deg"] and y <= C["BREAK_Y"]:
                        loc = "corner_trap"
                    elif abs(x) >= p["sideline_abs_x_min"] and y > C["BREAK_Y"]:
                        loc = "sideline_trap"
                    elif y <= p["baseline_y_max"]:
                        loc = "baseline_trap"
                    elif kh.r[a] <= p["post_r_max"]:
                        loc = "post_area"
                    else:
                        loc = "middle"
                    ev = make_event(
                        scene,
                        p,
                        "trap",
                        {"d1": dfn[i], "d2": dfn[j], "handler": h},
                        t0_,
                        t0_,
                        b,
                        pc,
                        [
                            f"both <= {p['enter_dist']} m of the handler and <= {p['pair_dist']} m apart",
                            f"held {(b - a) * DT:.2f} s >= {p['min_s']} s",
                            f"committed: held >= {p['trap_commit_s']} s, or no trapper retreated >= {p['trap_release_dist']} m "
                            f"(from his closest distance) within {p['trap_release_s']} s after the stay while H kept the ball",
                        ],
                        None,
                        p_emit=max(pc, pe),
                        location=loc,
                        backdated_s=(a - t0_) * DT,
                        handler_dr_m=float(kh.r[b] - kh.r[a]),
                        duration_s=(b - a) * DT,
                    )
                    if ev:
                        out.append(ev)
    return out


def _debounced_cross(series, a, b, hold, up_only=False):
    """First crossing of 0 in [a, b) of the 5-frame-mean series whose new sign holds for >= hold frames (DEF-T10).
    up_only: only <= 0 -> > 0 crossings. Returns the frame before the crossing, or None."""
    s5 = _mean5(series)
    n = len(s5)
    for t in range(a, min(b, n - 1)):
        u, v = s5[t], s5[t + 1]
        if np.isnan(u) or np.isnan(v):
            continue
        hit = (u <= 0 < v) if up_only else (u * v < 0)
        if not hit:
            continue
        seg = s5[t + 1 : min(n, t + 1 + hold)]
        if np.all(np.sign(seg[~np.isnan(seg)]) == np.sign(v)):
            return t
    return None


def _xball_path(scene, F, p, xb=None, ref=None):
    """Crossing classifier (DM-RULE-05 revised): where X-ball crosses the line through S along the
    S -> X-big axis (S -> rim when X-big is within big_near of S). q < -margin: over; 0..d_big: through;
    beyond X-big: under. Returns (class, probs, q, t_cross) or ('no_cross', ...)."""
    t0, n = F["t0"], scene.n
    xb = xb or F["xball"]
    ks, kx = scene.kins[F["S"]], scene.kins[xb]
    kb = scene.kins[ref or F["xbig"]] if (ref or F["xbig"]) else None
    a = max(0, t0 - frames(p["cross_back_s"]))
    b = min(n - 1, t0 + frames(p["cross_fwd_s"]))
    bx_, by_ = mean_xy(kb, t0) if kb is not None else (np.nan, np.nan)
    dbig = math.hypot(bx_ - F["sx"], by_ - F["sy"]) if kb is not None else 0.0
    if kb is not None and dbig >= p["big_near"]:
        e = ((bx_ - F["sx"]) / dbig, (by_ - F["sy"]) / dbig)
    else:
        e, dbig = F["er"], 0.0
    nrm = (-e[1], e[0])
    # signed side of X-ball w.r.t. the screen axis through P_s (the screen point, not the rolling screener)
    side = (kx.x - F["sx"]) * nrm[0] + (kx.y - F["sy"]) * nrm[1]
    tc = _debounced_cross(side, a, b, p["cross_hold_frames"])
    if tc is None:
        return "no_cross", {"no_cross": 1.0}, None, None
    mx, my = mean_xy(kx, tc)
    q = (mx - F["sx"]) * e[0] + (my - F["sy"]) * e[1]
    sig = float(sigma_rel(kx, ks, p)[tc])
    m = p["class_margin"]
    if dbig >= p["big_near"]:
        bands = {"over": (None, -m), "through": (-m, dbig - m), "under": (dbig - m, None)}
    else:
        bands = {"over": (None, m), "under": (m, None)}
    pr = band_probs(q, sig, bands)
    return max(pr, key=pr.get), pr, q, tc


def _lambda_path(scene, F, p, xb):
    """DM-RULE-05 lambda/s crossing (used for off-ball screens, where the cutter runs along the S -> screener's
    defender axis): lambda(p) = (p - P_s).u with u the cutter's travel direction; n is the normal pointing to the
    side on which the cutter crosses lambda = 0. At X's first crossing, s_X = (X - S).n: same side as the
    cutter (s_X >= -class_margin) = over / trail, else under. Returns (class, probs, s_X, t_cross)."""
    t0, n = F["t0"], scene.n
    ks, kc, kx = scene.kins[F["S"]], scene.kins[F["H"]], scene.kins[xb]
    a = max(0, t0 - frames(p["cross_back_s"]))
    b = min(n - 1, t0 + frames(p["cross_fwd_s"]))
    u = F["u"]
    lam = lambda k: (k.x - F["sx"]) * u[0] + (k.y - F["sy"]) * u[1]  # noqa: E731
    nrm = (-u[1], u[0])
    hold = p["cross_hold_frames"]
    tcu = _debounced_cross(lam(kc), a, b, hold, up_only=True)
    if tcu is not None:
        cx, cy = mean_xy(kc, tcu)
        sxs, sys_ = mean_xy(ks, tcu)
        if (cx - sxs) * nrm[0] + (cy - sys_) * nrm[1] < 0:
            nrm = (-nrm[0], -nrm[1])
    tc = _debounced_cross(lam(kx), a, b, hold, up_only=True)
    if tc is None:
        return "no_cross", {"no_cross": 1.0}, None, None
    mx, my = mean_xy(kx, tc)
    sxs, sys_ = mean_xy(ks, tc)
    sx_ = (mx - sxs) * nrm[0] + (my - sys_) * nrm[1]
    sig = float(sigma_rel(kx, ks, p)[tc])
    pr = band_probs(sx_, sig, {"over": (-p["class_margin"], None), "under": (None, -p["class_margin"])})
    return max(pr, key=pr.get), pr, sx_, tc


def _screens(A, kind="ball"):
    return [s for s in A["screen"] if s.get("kind", "ball") == kind]


def detect_xball_path(scene, **params):
    """X-ball path on a ball screen: over / through / under / no_cross (kind = class), t0 = crossing frame
    (screen t0 for no_cross); hip vs wide recorded for over."""
    p, A = _setup(("xball_path", "ball_screen"), scene, params)
    pb = p
    out = []
    for sc in _screens(A, "ball"):
        F = _screen_frame(scene, sc, pb)
        cls, pr, q, tc = _xball_path(scene, F, pb)
        t0 = tc if tc is not None else F["t0"]
        kx, ks = scene.kins[F["xball"]], scene.kins[F["S"]]
        hip = None
        if cls == "over":
            hip = bool(float(np.nanmin(dist(kx, ks)[max(0, tc - 3) : tc + 4])) <= pb["hip_max"])
        ev = make_event(
            scene,
            pb,
            cls,
            {"xball": F["xball"], "screener": F["S"], "handler": F["H"], "xbig": F["xbig"]},
            t0,
            max(0, F["t0"] - frames(pb["cross_back_s"])),
            min(scene.n - 1, F["t0"] + frames(pb["cross_fwd_s"])),
            pr[cls],
            [
                f"X-ball crossing q = {q:.2f} m on the S->X-big axis"
                if q is not None
                else "X-ball never crosses the screen axis",
                f"frame source {F['u_src']}",
            ],
            pr,
            crossing_q_m=q,
            over_hip=hip,
            screen_t0=F["t0"],
        )
        if ev:
            out.append(ev)
    return out


def _coverage(scene, sc, p, A):
    """Mutually exclusive X-big coverage class with probabilities (priority: blitz > hard_hedge > soft_show >
    flat > at_level > drop bands). Switches are labelled by detect_switch. Returns the class, its probability,
    p_emit (existence probability of the show for hard_hedge / soft_show) and the attributes."""
    F = _screen_frame(scene, sc, p)
    t0, n = F["t0"], scene.n
    xbig, H = F["xbig"], F["H"]
    if xbig is None:
        return None
    kb, ks = scene.kins[xbig], scene.kins[F["S"]]
    sig = float(np.nanmean(sigma_rel(kb, ks, p)[max(0, t0 - 6) : min(n, t0 + 25)]))
    dep = np.array([_depth(scene, F, xbig, t) for t in range(n)])
    lat = np.array([_lat(scene, F, xbig, t) for t in range(n)])
    dep5, lat5 = _mean5(dep), _mean5(lat)
    # blitz: a trap on H by X-ball and X-big starting near t0 with X-big at or above the screen level
    for tr in _traps_cached(scene):
        if (
            tr.actors["handler"] == H
            and {tr.actors["d1"], tr.actors["d2"]} == {F["xball"], xbig}
            and t0 - frames(p["blitz_back_s"]) <= tr.t0 <= t0 + frames(p["blitz_fwd_s"])
        ):
            # DEF-T08: X-big may still be arriving at trap entry (a blitz from a drop): use the shallowest 5-frame-mean
            # depth during the trap
            d_entry = mean_val(dep, tr.t0)
            dtrap = float(np.nanmin(dep5[tr.start : tr.end + 1]))
            # confidence as the YAML states: P(depth <= blitz_depth_max) x trap P_cond (entry-threshold P_cond, so a
            # big who stops 1.75 m from H - inside the exit band only by noise - does not make a blitz)
            pb = float(p_below(dtrap, p["blitz_depth_max"], sig)) * float(tr.attrs["p_cond"])
            reasons = [
                _fmt("X-big min depth during the trap", dtrap, "<=", p["blitz_depth_max"], "m"),
                f"depth at trap entry {d_entry:.2f} m",
                f"trap P_cond {tr.attrs['p_cond']:.2f}",
            ]
            # DEF-T02(b): a big who leaves the 'trap' and retreats >= soft_retreat_min while H keeps the ball showed
            ret = None
            if tr.end + 1 < n and scene.holder[tr.end + 1] == H:
                ret = mean_val(dep, min(n - 1, tr.end + frames(p["blitz_retreat_s"]))) - mean_val(dep, tr.end)
                pb *= float(p_below(ret, p["soft_retreat_min"], sig * math.sqrt(2)))
                reasons.append(_fmt("retreat after the trap (H still holds)", ret, "<", p["soft_retreat_min"], "m"))
            if pb >= 0.5:
                return dict(
                    F=F,
                    cls="blitz",
                    probs={"blitz": pb},
                    p_emit=pb,
                    t0=tr.t0,
                    start=tr.start,
                    end=tr.end,
                    depth=dtrap,
                    depth_at_entry=d_entry,
                    trap=tr,
                    reasons=reasons,
                )
    a = max(0, t0 - frames(p["show_back_s"]))
    b = min(n - 1, t0 + frames(p["show_fwd_s"]))
    dmin = float(np.nanmin(dep[a : b + 1]))
    tmin = a + int(np.nanargmin(dep[a : b + 1]))
    lmax = float(np.nanmax(lat[a : b + 1]))
    # DEF-T06: the hold is measured on 5-frame means with relative hysteresis (enter at the hedge position, stay
    # within + h) and dwell bridging, so lateral noise at the 0.8 m edge does not break it
    hh = hyst_h(sig, p)
    w_e = min(n, b + frames(p["hold_tail_s"]))
    enter_h = (np.nan_to_num(dep5, nan=9) <= p["hold_depth"]) & (np.nan_to_num(lat5, nan=-9) >= p["hold_lat"])
    stay_h = (np.nan_to_num(dep5, nan=9) <= p["hold_depth"] + hh) & (np.nan_to_num(lat5, nan=-9) >= p["hold_lat"] - hh)
    hold_runs = hysteresis(enter_h[a:w_e], stay_h[a:w_e], 0.0, p["dwell_frames"])
    hold = max([(r[1] - r[0]) * DT for r in hold_runs], default=0.0)
    h_end = a + max(hold_runs, key=lambda r: r[1] - r[0])[1] if hold_runs else tmin
    # recovery after the show: chord back toward the screener / roller within recovery_s
    r1 = min(n - 1, h_end + frames(p["recovery_s"]))
    rx, ry = mean_xy(kb, h_end)
    ex, ey = mean_xy(kb, r1)
    rchord = math.hypot(ex - rx, ey - ry)
    rpeak = float(np.nanmax(kb.speed[h_end : r1 + 1]))
    sv = float(np.nanmean(kb.sigma_speed[h_end : r1 + 1]))
    retreat = mean_val(dep, r1) - mean_val(dep, h_end)
    hard_peak = tier_param(p, "hard_recovery_peak", kb)
    soft_peak = tier_param(p, "soft_recovery_peak", kb)
    probs = {}
    # P(hard_hold_min_s <= hold <= hard_hold_max_s): the hold edges blur by position noise at the gate crossings
    p_hold = float(
        p_below(hold, p["hard_hold_max_s"], p["hold_sigma_s"]) - p_below(hold, p["hard_hold_min_s"], p["hold_sigma_s"])
    )
    # DEF-T06(c): existence of a show (the big stepped up into H's path and then recovered) is separated from the
    # class: P(class | show) uses only the discriminating gates (depth, lateral, hold); the recovery gates are the
    # existence probability (p_emit), not factors of P(class)
    # existence = the big stepped up into the path (shape) and went back (recovery chord or retreat); the smoothed
    # recovery peak is a hard-hedge class gate and a soft-show quality attribute (quick_recovery), not existence
    shape = float(p_below(dmin, p["soft_depth_max"], sig)) * float(p_above(lmax, p["soft_lat_min"], sig))
    rec_h = float(p_above(rchord, p["recovery_chord_min"], sig * math.sqrt(2)))
    rec_s = float(p_above(retreat, p["soft_retreat_min"], sig * math.sqrt(2)))
    p_show = shape * max(rec_h, rec_s)
    p_quick = float(p_above(rpeak, soft_peak, sv))
    c_hard = (
        float(p_below(dmin, p["hard_depth_max"], sig))
        * float(p_above(lmax, p["hard_lat_min"], sig))
        * p_hold
        * float(p_above(rpeak, hard_peak, sv))
    )
    c_soft = (1 - c_hard) * float(p_above(dmin, p["soft_depth_min"], sig))
    probs["hard_hedge"] = p_show * c_hard
    probs["soft_show"] = p_show * c_soft
    deep_unclassified = p_show * (1 - c_hard - c_soft)  # deeper than soft_depth_min, no hard hold: abstain
    t3 = min(n - 1, t0 + frames(p["depth_at_s"]))
    d3 = mean_val(dep, t3)
    l3 = mean_val(lat, t3)
    rest = max(0.0, 1 - p_show)
    flat_p = (
        float(p_above(d3, 0.0, sig))
        * float(p_below(d3, p["level_max"], sig))
        * float(p_above(l3, p["flat_lat_min"], sig))
    )
    probs["flat"] = rest * flat_p
    rest2 = rest * (1 - flat_p)
    bands = band_probs(
        d3,
        sig,
        {
            "show_unclassified": (None, -p["level_max"]),  # above the level, not a show: abstain
            "at_level": (-p["level_max"], p["level_max"]),
            "drop_high": (p["level_max"], p["high_max"]),
            "drop_standard": (p["high_max"], p["standard_max"]),
            "drop_deep": (p["standard_max"], None),
        },
    )
    r_big = mean_val(kb.r, t3)
    # DEF-T07: r(X-big) <= deep_r_max promotes a standard drop to deep (never a high drop): soft mix with
    # P(r <= deep_r_max) x P(depth > high_max)
    q_deep = float(p_below(r_big, p["deep_r_max"], sig)) * float(p_above(d3, p["high_max"], sig))
    bands = {k_: v * (1 - q_deep) for k_, v in bands.items()}
    bands["drop_deep"] += q_deep
    for k_, v in bands.items():
        probs[k_] = rest2 * v
    probs["show_unclassified"] += deep_unclassified
    cls = max(probs, key=probs.get)
    # loop 2 (SHOW-hard-vs-soft): a show whose hard / soft class probabilities (given the show) differ by less than
    # class_margin_min is not labelled: show_unclassified (abstain), the hard / soft values stay as alternatives
    if cls in ("hard_hedge", "soft_show") and abs(c_hard - c_soft) < p["class_margin_min"]:
        cls = "show_unclassified"
    t_nmb = min(n, t0 + frames(p["no_man_behind_s"]))
    no_man_behind = float(np.mean(np.nan_to_num(ks.r[t0:t_nmb] - kb.r[t0:t_nmb], nan=0) > 0))
    reasons = [
        _fmt("min depth (S->rim axis)", dmin, "vs hard <=", p["hard_depth_max"], "m"),
        _fmt("max lateral into H's path", lmax, "vs", p["hard_lat_min"], "m"),
        f"hold {hold:.2f} s (5-frame means, relative hysteresis) vs [{p['hard_hold_min_s']}, {p['hard_hold_max_s']}] s",
        _fmt("depth at t0+0.3 s", d3, "bands", f"{p['level_max']}/{p['high_max']}/{p['standard_max']}", "m"),
        f"recovery chord {rchord:.2f} m, retreat {retreat:.2f} m, peak {rpeak:.2f} m/s"
        f" (hard >= {hard_peak}, soft >= {soft_peak}); P(show) {p_show:.2f}; frame {F['u_src']}",
    ]
    # show t0 = entry into the show position (threshold crossing, stable under noise): hard hedge = first frame
    # with depth <= hard_depth_max, soft show = first frame stepping into H's path (lateral >= soft_lat_min)
    t_hard = next((t for t in range(a, b + 1) if dep[t] <= p["hard_depth_max"]), tmin)
    t_soft = next((t for t in range(a, b + 1) if lat[t] >= p["soft_lat_min"]), tmin)
    tt = {"hard_hedge": t_hard, "soft_show": t_soft}.get(cls, F["t0"])
    return dict(
        F=F,
        cls=cls,
        probs=probs,
        p_emit=p_show if cls in ("hard_hedge", "soft_show") else probs[cls],
        t0=tt,
        start=a,
        end=max(b, r1),
        depth=d3,
        depth_min=dmin,
        lat_max=lmax,
        hold=hold,
        recovery_chord=rchord,
        recovery_peak=rpeak,
        quick_recovery=p_quick,
        reasons=reasons,
        no_man_behind=no_man_behind,
        r_big=r_big,
    )


def _coverage_events(scene, item_id, kinds, params):
    p, A = _setup((item_id, "ball_screen"), scene, params)
    out = []
    for sc in _screens(A, "ball"):
        cv = _coverage(scene, sc, p, A)
        if cv is None or cv["cls"] not in kinds:
            continue
        F = cv["F"]
        extra = {"depth_at_entry_m": cv["depth_at_entry"]} if "depth_at_entry" in cv else {}
        ev = make_event(
            scene,
            p,
            cv["cls"],
            {"xbig": F["xbig"], "screener": F["S"], "handler": F["H"], "xball": F["xball"]},
            cv["t0"],
            cv["start"],
            cv["end"],
            cv["probs"][cv["cls"]],
            cv["reasons"],
            cv["probs"],
            p_emit=cv["p_emit"],
            depth_m=cv["depth"],
            screen_t0=F["t0"],
            frame_dir_source=F["u_src"],
            no_man_behind_share=cv.get("no_man_behind"),
            hold_s=cv.get("hold"),
            quick_recovery=None if cv.get("quick_recovery") is None else bool(cv["quick_recovery"] >= 0.5),
            **extra,
        )
        if ev:
            out.append(ev)
    return out


def detect_drop_coverage(scene, **params):
    """X-big depth class at t0 + 0.3 s: at_level / drop_high / drop_standard / drop_deep / flat."""
    return _coverage_events(
        scene, "drop_coverage", {"at_level", "drop_high", "drop_standard", "drop_deep", "flat"}, params
    )


def detect_show(scene, **params):
    """Show family: hard_hedge / soft_show (t0 = frame of minimum depth)."""
    return _coverage_events(scene, "show", {"hard_hedge", "soft_show"}, params)


def detect_blitz(scene, **params):
    """BLITZ: TRAP of the handler by X-ball and X-big starting in [t0 - 0.2, t0 + 1.5] with X-big at or above
    the screen level (t0 = trap start)."""
    return _coverage_events(scene, "blitz", {"blitz"}, params)


def detect_ice(scene, **params):
    """ICE: side screen; before t0 X-ball sits on the H->screen segment (perp <= perp_max, tau in band) for
    >= pre_hold_s; H then rejects away from the screen (|x| up or y down) and X-ball never crosses."""
    p, A = _setup(("ice", "ball_screen"), scene, params)
    pb = p
    out = []
    for sc in _screens(A, "ball"):
        F = _screen_frame(scene, sc, pb)
        t0 = F["t0"]
        if abs(F["sx"]) < p["side_abs_x_min"]:
            continue
        kx, kh = scene.kins[F["xball"]], scene.kins[F["H"]]
        a = max(0, t0 - frames(p["pre_back_s"]))
        b = max(a, t0 - frames(p["pre_end_s"]))
        sd_, tau = seg_dist_arr(kx.x[a : b + 1], kx.y[a : b + 1], kh.x[a : b + 1], kh.y[a : b + 1], F["sx"], F["sy"])
        on = (
            (sd_ <= p["perp_max"])
            & (np.nan_to_num(tau, nan=-1) >= p["tau_lo"])
            & (np.nan_to_num(tau, nan=9) <= p["tau_hi"])
        )
        pre = max([(r[1] - r[0] + 1) * DT for r in runs(on)], default=0.0)
        t1 = min(scene.n - 1, t0 + frames(p["reject_s"]))
        dx = abs(mean_val(kh.x, t1)) - abs(mean_val(kh.x, t0))
        dy = mean_val(kh.y, t1) - mean_val(kh.y, t0)
        cls, _, _, _ = _xball_path(scene, F, pb)
        sig = float(np.nanmean(sigma_rel(kx, kh, p)[a : b + 1]))
        p_pre = float(window_conf(np.concatenate([np.full(a, np.nan), p_below(sd_, p["perp_max"], sig)]), a, b))
        p_rej = max(float(p_above(dx, p["reject_min"], sig)), float(p_below(dy, -p["reject_min"], sig)))
        g = {
            "pre_position": p_pre * (1.0 if pre >= p["pre_hold_s"] else 0.0),
            "reject": p_rej,
            "no_cross": 1.0 if cls == "no_cross" else 0.0,
        }
        ev = make_event(
            scene,
            pb,
            "ice",
            {"xball": F["xball"], "handler": F["H"], "screener": F["S"], "xbig": F["xbig"]},
            t0,
            a,
            t1,
            float(np.prod(list(g.values()))),
            [
                f"side screen |x_S| {abs(F['sx']):.1f} m >= {p['side_abs_x_min']} m",
                f"X-ball on the H->screen segment {pre:.2f} s >= {p['pre_hold_s']} s (perp <= {p['perp_max']} m)",
                f"handler reject: d|x| {dx:.2f} m, dy {dy:.2f} m (>= {p['reject_min']} m)",
                f"X-ball path {cls}",
            ],
            None,
            pre_s=pre,
            h_reject=bool(p_rej >= 0.5),
        )
        if ev:
            out.append(ev)
    return out


def detect_tag(scene, **params):
    """TAG: a defender other than X-big / X-ball reaches <= contact_max of the roller in [t0+0.5, t0+1.8 s] with
    r_roller <= roller_r_max and leaves (> leave_dist) within leave_s (t0 = first contact). Origin sub-class
    from named_spots (corner man, gap_occupancy, low man, tag_ready_spot)."""
    p, A = _setup(("tag", "ball_screen"), scene, params)
    pb = p
    mu = matchup_posterior(scene)
    out = []
    for sc in _screens(A, "ball"):
        F = _screen_frame(scene, sc, pb)
        t0, S = F["t0"], F["S"]
        ks = scene.kins[S]
        a = min(scene.n - 1, t0 + frames(p["contact_from_s"]))
        # loop 2: in the q = 10 tier the smoothed distance reaches P(d <= contact_max) >= contact_p only near the
        # rounded-off minimum, 0.2-0.5 s after the true first contact, so the window end is tier-aware
        b = min(scene.n - 1, t0 + frames(tier_param(p, "contact_to_s", ks)))
        bx, by = ball_xy(scene)
        cands = [d for d in scene.defense if d not in (F["xbig"], F["xball"])]
        # low man at t0: min r among away-side candidates (named_spots low_man aggregate)
        side = np.sign(bx[t0]) if abs(bx[t0]) >= 0.9 else 0
        away = [d for d in cands if side == 0 or scene.kins[d].x[t0] * side <= 0.3048] or cands
        low = min(away, key=lambda d: scene.kins[d].r[t0]) if away else None
        for d in cands:
            kd = scene.kins[d]
            dd = dist(kd, ks)
            sig = sigma_rel(kd, ks, p)
            pc_ = p_below(dd, p["contact_max"], sig)
            cont = [t for t in range(a, b + 1) if pc_[t] >= p["contact_p"] and ks.r[t] <= p["roller_r_max"]]
            if not cont:
                continue
            tc = cont[0]
            t_leave = None
            for t in range(tc, min(scene.n, tc + frames(p["leave_s"]) + 1)):
                if dd[t] > p["leave_dist"]:
                    t_leave = t
                    break
            if t_leave is None:
                continue  # stays with the roller: a rotation / switch, labelled there
            am = mu["top1"][d][max(0, t0 - frames(p["origin_back_s"]))]
            origin = "other"
            if am is not None:
                ka = scene.kins[am]
                if math.degrees(math.atan2(ka.y[t0], abs(ka.x[t0]))) <= p["corner_angle_max_deg"]:
                    origin = "corner"
                elif SPOTS["gap_occupancy"].inside(
                    kd.x[t0],
                    kd.y[t0],
                    ax_=ka.x[t0],
                    ay_=ka.y[t0],
                    bx=bx[t0],
                    by=by[t0],
                    hx=scene.kins[F["H"]].x[t0],
                    hy=scene.kins[F["H"]].y[t0],
                ):
                    origin = "gap"
            if origin == "other" and d == low:
                origin = "low_man"
            if origin == "other" and SPOTS["tag_ready_spot"].inside(
                kd.x[t0],
                kd.y[t0],
                ax_=(scene.kins[am].x[t0] if am else 9.0),
                ay_=(scene.kins[am].y[t0] if am else 9.0),
                hx=scene.kins[F["H"]].x[t0],
                hy=scene.kins[F["H"]].y[t0],
                bx=bx[t0],
                by=by[t0],
            ):
                origin = "tag_ready_spot"
            pc = window_conf(pc_, tc, min(tc + 2, scene.n - 1))
            ev = make_event(
                scene,
                p,
                "tag",
                {"tagger": d, "roller": S, "handler": F["H"]},
                tc,
                tc,
                t_leave,
                pc,
                [
                    f"contact P(d <= {p['contact_max']} m) >= {p['contact_p']} at {(tc - t0) * DT:.2f} s after the screen",
                    f"roller r {ks.r[tc]:.1f} m <= {p['roller_r_max']} m",
                    f"left after {(t_leave - tc) * DT:.2f} s <= {p['leave_s']} s",
                ],
                None,
                origin=origin,
                gap_bump=origin == "gap",
                meet_roller=bool(d == low),
                screen_t0=t0,
            )
            if ev:
                out.append(ev)
    return out


def detect_offball_screen_coverage(scene, **params):
    """Off-ball screen coverage of the cutter's defender: top_lock (pre-screen), else trail / under from the
    crossing classifier with U = cutter (t0 = screen t0)."""
    p, A = _setup(("offball_screen_coverage", "xball_path", "ball_screen"), scene, params)
    pb = p
    out = []
    for sc in _screens(A, "offball"):
        S, Cc = sc["screener"], sc["cutter"]
        t0 = sc["t0"]
        pre = max(0, t0 - frames(p["defender_back_s"]))
        dc = sc.get("dcut") or on_ball_defender(scene, Cc, pre)
        dscr = sc.get("dscr") or on_ball_defender(scene, S, pre)
        F = _screen_frame(scene, dict(t0=t0, screener=S, handler=Cc, xball=dc, xbig=dscr), pb)
        kd, kc, ks = scene.kins[dc], scene.kins[Cc], scene.kins[S]
        a = max(0, t0 - frames(p["lock_back_s"]))
        u = F["u"]
        nS = (-u[1], u[0])  # unit normal of the cutter's travel, pointing to the screener's side
        if (mean_val(ks.x, t0) - mean_val(kc.x, t0)) * nS[0] + (mean_val(ks.y, t0) - mean_val(kc.y, t0)) * nS[1] < 0:
            nS = (-nS[0], -nS[1])
        rx_, ry_ = kd.x[a : t0 + 1] - kc.x[a : t0 + 1], kd.y[a : t0 + 1] - kc.y[a : t0 + 1]
        lead = rx_ * u[0] + ry_ * u[1]
        latS = rx_ * nS[0] + ry_ * nS[1]
        dd = dist(kd, kc)[a : t0 + 1]
        h_ = hyst_h(float(np.nanmean(sigma_rel(kd, kc, p)[a : t0 + 1])), p)
        close = np.nan_to_num(dd, nan=9) <= p["lock_dist_max"] + h_
        lock = (np.nan_to_num(lead, nan=-9) >= p["lock_lead_min"]) & close
        lock_s = max([(r[1] - r[0] + 1) * DT for r in runs(lock)], default=0.0)
        sig = float(np.nanmean(sigma_rel(kd, kc, p)[a : t0 + 1]))
        # DEF-T09: lock = ahead of the cutter (lead) AND not on the screener's side of his path (a defender who
        # shoots the gap under the screen also leads the cutter). Means over the frames within lock distance, not
        # over the lock frames themselves (that mean is biased above the lead threshold by selection).
        sel = close if close.any() else np.ones(len(dd), dtype=bool)
        m_lead, m_lat = float(np.nanmean(lead[sel])), float(np.nanmean(latS[sel]))
        p_lock = float(p_above(m_lead, p["lock_lead_min"], sig)) * float(p_below(m_lat, p["lock_lat_tol"], sig))
        if lock_s >= p["lock_min_s"] and p_lock >= 0.5:
            pc = pc_emit = p_lock
            cls, probs = "top_lock", {"top_lock": p_lock}
        else:
            c2, pr, q, tc = _lambda_path(scene, F, pb, dc)
            cls = {"over": "trail", "under": "under", "no_cross": "no_cross"}[c2]
            probs = (
                {"trail": pr.get("over", 0.0), "under": pr.get("under", 0.0)} if c2 != "no_cross" else {"no_cross": 1.0}
            )
            pc_emit = probs[cls]  # the event exists when its crossing class does; top_lock competes only in conf
            pc = probs[cls] * (1 - p_lock if lock_s >= p["lock_min_s"] else 1.0)
            probs = {k_: v * (1 - p_lock if lock_s >= p["lock_min_s"] else 1.0) for k_, v in probs.items()}
            if lock_s >= p["lock_min_s"]:
                probs["top_lock"] = p_lock
        ev = make_event(
            scene,
            pb,
            cls,
            {"defender": dc, "cutter": Cc, "screener": S},
            t0,
            a,
            min(scene.n - 1, t0 + frames(p["span_after_s"])),
            pc,
            [
                f"top-lock lead >= {p['lock_lead_min']} m within {p['lock_dist_max']} m for {lock_s:.2f} s (min {p['lock_min_s']} s)",
                _fmt("mean lead", m_lead, ">=", p["lock_lead_min"], "m")
                + "; "
                + _fmt("mean offset toward the screener", m_lat, "<=", p["lock_lat_tol"], "m"),
                f"class {cls}",
            ],
            probs,
            p_emit=pc_emit,
            lock_s=lock_s,
            mean_lead_m=m_lead,
            mean_offset_to_screener_m=m_lat,
        )
        if ev:
            out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# Post defence (DM-A17, A18, A19)
# --------------------------------------------------------------------------------------
_POST = {
    "post_front": "post_full_front",
    "post_three_quarter_high": "post_three_quarter_high",
    "post_three_quarter_low": "post_three_quarter_low",
    "post_behind": "post_behind",
}


def detect_post_position(scene, **params):
    """Post position holds from named_spots post_* entries (>= min_s, abstain when mean distance < 0.4 m)."""
    p, A = _setup("post_position", scene, params)
    mu = matchup_posterior(scene)
    bx, by = ball_xy(scene)
    out = []
    for d in scene.defense:
        kd = scene.kins[d]
        top = mu["top1"][d]
        cls = np.full(scene.n, "", dtype=object)
        for kind, sid in _POST.items():
            m = _spot_series(scene, sid, d, top, range(scene.n))
            cls[m] = kind
        cls[np.nan_to_num(by, nan=0.0) > C["HALF_Y"]] = ""  # loop 4 L4-POST: half-court positions (ball in the frontcourt)
        for kind in _POST:
            for a, b in hysteresis(cls == kind, cls == kind, p["min_s"], p["dwell_frames"]):
                att = top[(a + b) // 2]
                ka = scene.kins[att]
                dA = dist(kd, ka)
                if float(np.nanmean(dA[a : b + 1])) < p["abstain_dist"]:
                    continue
                # loop 4 L4-POST: the post holds his spot (posting / sealing); a man running through the post area
                # (median smoothed speed above the walk edge) is cutting or rolling, not posting
                if float(np.nanmedian(ka.speed[a : b + 1])) > p["post_v_max"]:
                    continue
                phi = angle_at(ka.x, ka.y, kd.x, kd.y, bx, by)
                sphi = np.degrees(sigma_rel(kd, ka, p) / np.maximum(dA, 0.3))
                fm, bm = p["front_max_deg"], p["behind_min_deg"]
                bands = {"post_front": (None, fm), "post_three_quarter": (fm, bm), "post_behind": (bm, None)}
                pr = {
                    k_: float(np.nanmean([band_probs(phi[t], sphi[t], {"x": v})["x"] for t in range(a, b + 1)]))
                    for k_, v in bands.items()
                }
                key = "post_three_quarter" if "three_quarter" in kind else kind
                ev = make_event(
                    scene,
                    p,
                    kind,
                    {"defender": d, "post": att},
                    a,
                    a,
                    b,
                    pr[key] * float(np.mean(cls[a : b + 1] == kind)),
                    [
                        f"named_spots {_POST[kind]}",
                        f"mean angle at post {np.nanmean(phi[a:b + 1]):.0f} deg",
                        f"held {(b - a) * DT:.2f} s >= {p['min_s']} s",
                    ],
                    pr,
                    state=True,
                    mean_dist_m=float(np.nanmean(dA[a : b + 1])),
                )
                if ev:
                    out.append(ev)
    return out


def detect_lob_protection(scene, **params):
    """While a post is fronted (front or three-quarter high) >= min_s, the weak-side low defender stays at
    r <= r_max and |x| <= abs_x_max on >= share_min of frames (attrs protected True/False)."""
    p, A = _setup("lob_protection", scene, params)
    bx, _ = ball_xy(scene)
    out = []
    for e in detect_post_position(scene, anchors=A):
        if e.kind not in ("post_front", "post_three_quarter_high") or e.duration_s < p["min_s"]:
            continue
        a, b = e.start, e.end
        others = [
            d
            for d in scene.defense
            if d != e.actors["defender"]
            and all(on_ball_defender(scene, scene.holder[t], t) != d for t in (a, b) if scene.holder[t] is not None)
        ]
        if not others:
            continue
        side = np.sign(np.nanmean(bx[a : b + 1]))
        weak = [d for d in others if np.nanmean(scene.kins[d].x[a : b + 1]) * side <= 0.5] or others
        low = min(weak, key=lambda d: np.nanmean(scene.kins[d].r[a : b + 1]))
        kl = scene.kins[low]
        ok = (kl.r[a : b + 1] <= p["r_max"]) & (np.abs(kl.x[a : b + 1]) <= p["abs_x_max"])
        share = float(np.mean(ok))
        pr = float(p_above(share, p["share_min"], 0.1))
        ev = make_event(
            scene,
            p,
            "lob_protection",
            {"low_defender": low, "post_defender": e.actors["defender"], "post": e.actors["post"]},
            a,
            a,
            b,
            max(pr, 1 - pr) * e.conf,
            [
                f"weak-side low defender in r <= {p['r_max']} m, |x| <= {p['abs_x_max']} m on {share:.0%} of frames (>= {p['share_min']:.0%})"
            ],
            {"protected": pr, "unprotected": 1 - pr},
            state=True,
            protected=bool(pr >= 0.5),
            protected_share=share,
        )
        if ev:
            out.append(ev)
    # loop 4 L4-Q10-REPORT: a front / three-quarter-high hold that abstained in the q = 10 tier carries its lob-protection
    # label with it; report that abstention too (sigma 0.5 real-data run: lob_protection 0 with no abstain record)
    min_f = p["min_s"] / DT + 1
    for (reason, kind, _, t0, end), (start, actors) in list(_cache(scene).get("abstained", {}).items()):
        if reason == "q10" and kind in ("post_front", "post_three_quarter_high") and end - start + 1 >= min_f:
            _abstain(scene, "q10", "lob_protection", {"post_defender": actors.get("defender"), "post": actors.get("post")}, t0, start, end)
    return out


def detect_post_double(scene, **params):
    """POST_DOUBLE: a TRAP on a post receiver (r <= post_r) starting within trigger windows after the catch;
    origin of the doubler from its position at the catch."""
    p, A = _setup("post_double", scene, params)
    out = []
    for ps in A["pass"]:
        R_, tc = ps["receiver"], ps["t_catch"]
        if scene.kins[R_].r[tc] > p["post_r"]:
            continue
        pd = on_ball_defender(scene, R_, max(0, tc - frames(p["pre_catch_s"])))
        for tr in _traps_cached(scene):
            if tr.actors["handler"] != R_ or not (
                tc - frames(p["pre_catch_s"]) <= tr.t0 <= tc + frames(p["max_after_catch_s"])
            ):
                continue
            doubler = tr.actors["d1"] if tr.actors["d2"] == pd else tr.actors["d2"]
            kdb = scene.kins[doubler]
            x, y = kdb.x[tc], kdb.y[tc]
            origin = (
                "top"
                if y > p["top_y"]
                else ("baseline" if y < p["baseline_y"] else ("middle" if abs(x) < p["middle_abs_x"] else "wing"))
            )
            lat = (tr.t0 - tc) * DT
            trig = "on_catch" if lat <= p["on_catch_s"] else "late"
            ev = make_event(
                scene,
                p,
                "post_double",
                {"doubler": doubler, "post_defender": pd, "post": R_},
                tr.t0,
                tr.start,
                tr.end,
                tr.attrs["p_cond"],
                [
                    f"trap on post receiver (r {scene.kins[R_].r[tc]:.1f} m <= {p['post_r']} m)",
                    f"{lat:.2f} s after the catch -> {trig}",
                    f"origin {origin}",
                ],
                None,
                origin=origin,
                trigger=trig,
                latency_s=lat,
            )
            if ev:
                out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# Transition (DM-A20..A23) and press pickup
# --------------------------------------------------------------------------------------
def detect_protect_rim(scene, **params):
    """PROTECT_RIM: first defender to reach named_spots transition_protect_rim after a change of possession."""
    p, A = _setup("protect_rim", scene, params)
    out = []
    spot = SPOTS["transition_protect_rim"]
    for cp in A["cop"]:
        t = cp["t"]
        w1 = min(scene.n - 1, t + frames(p["window_s"]))
        best = None
        for d in scene.defense:
            kd = scene.kins[d]
            if kd.r[t] <= p["start_r_min"]:
                continue
            for tt in range(t, w1 + 1):
                if spot.inside(kd.x[tt], kd.y[tt]):
                    if best is None or tt < best[1]:
                        best = (d, tt)
                    break
        if best is None:
            continue
        d, tt = best
        kd = scene.kins[d]
        r_max = SPOT_NUM["protect_rim"]["r_max"]
        pc = float(p_below(mean_val(kd.r, tt + 2, 2), r_max, rel_floor(p, kd)))
        loose = next((x for x in range(t, w1 + 1) if kd.r[x] <= p["loose_r"]), None)
        ev = make_event(
            scene,
            p,
            "protect_rim",
            {"defender": d},
            tt,
            t,
            tt,
            pc,
            [
                f"named_spots transition_protect_rim (r <= {r_max} m) reached {(tt - t) * DT:.2f} s after the change of possession"
            ],
            None,
            t_protect_s=(tt - t) * DT,
            t_protect_loose_s=None if loose is None else (loose - t) * DT,
        )
        if ev:
            out.append(ev)
    return out


def detect_stop_ball(scene, **params):
    """STOP_BALL: first defender within 2.0 m of the handler and between him and the rim after a change of
    possession; stopped if the handler slows below stop_speed within stop_window_s."""
    p, A = _setup("stop_ball", scene, params)
    out = []
    for cp in A["cop"]:
        t = cp["t"]
        w1 = min(scene.n - 1, t + frames(p["window_s"]))
        for tt in range(t, w1 + 1):
            h = scene.holder[tt]
            if h is None:
                continue
            kh = scene.kins[h]
            hit = [
                d
                for d in scene.defense
                if SPOTS["transition_stop_ball"].inside(
                    scene.kins[d].x[tt], scene.kins[d].y[tt], hx=kh.x[tt], hy=kh.y[tt]
                )
                and scene.kins[d].r[tt] < kh.r[tt]
            ]
            if not hit:
                continue
            d = min(hit, key=lambda o: math.hypot(scene.kins[o].x[tt] - kh.x[tt], scene.kins[o].y[tt] - kh.y[tt]))
            t2 = min(scene.n - 1, tt + frames(p["stop_window_s"]))
            vmin = float(np.nanmin(kh.speed[tt : t2 + 1]))
            pst = float(p_below(vmin, p["stop_speed"], float(np.nanmean(kh.sigma_speed[tt : t2 + 1]))))
            pk = window_conf(
                p_below(dist(scene.kins[d], kh), SPOT_NUM["stop_ball"]["dist_max"], sigma_rel(scene.kins[d], kh, p)),
                tt,
                min(scene.n - 1, tt + 4),
            )
            ev = make_event(
                scene,
                p,
                "stop_ball",
                {"defender": d, "handler": h},
                tt,
                t,
                t2,
                pk,
                [
                    f"named_spots transition_stop_ball at {(tt - t) * DT:.2f} s after the change of possession",
                    _fmt("handler min speed", vmin, "<", p["stop_speed"], "m/s") + f" within {p['stop_window_s']} s",
                ],
                {"stopped": pst, "not_stopped": 1 - pst},
                stopped=bool(pst >= 0.5),
                pickup_y=float(kh.y[tt]),
                turned=bool(abs(kh.x[t2]) >= p["turned_abs_x"]),
            )
            if ev:
                out.append(ev)
            break
    return out


def detect_set_def(scene, **params):
    """SET_DEF: all defenders inside the half court (y < HALF_Y) and mean defender speed < v_max for >= min_s,
    after an unset period (left-censored sets at clip start are flagged)."""
    p, A = _setup("set_def", scene, params)
    ks = [scene.kins[d] for d in scene.defense]
    inside = np.all([np.nan_to_num(k.y, nan=99) < C["HALF_Y"] for k in ks], axis=0)
    msp = np.nanmean([k.speed for k in ks], axis=0)
    m = inside & (np.nan_to_num(msp, nan=9) < p["v_max"])
    sets = hysteresis(m, m, p["min_s"], p["dwell_frames"])
    real = [r for r in sets if r[0] > 0 and not m[r[0] - 1]]  # preceded by an unset frame
    pick = real[:1] or sets[:1]
    out = []
    for a, b in pick:
        sig = float(np.nanmean([np.nanmean(k.sigma_speed[a : b + 1]) for k in ks])) / math.sqrt(len(ks))
        pc = window_conf(p_below(msp, p["v_max"], sig), a, b)
        ev = make_event(
            scene,
            p,
            "set_def",
            {"team": "D", **{f"d{i}": d for i, d in enumerate(scene.defense)}},
            a,
            a,
            b,
            pc,
            [
                f"all defenders y < {C['HALF_Y']} m, mean speed < {p['v_max']} m/s for {(b - a) * DT:.2f} s >= {p['min_s']} s"
            ],
            None,
            state=not real,
        )
        if ev:
            if not real:
                ev.conf *= 0.5  # set already at the clip start: the transition into SET_DEF was not seen
            out.append(ev)
    return out


def detect_transition_matched(scene, **params):
    """MATCHED: first time after a change of possession that every attacker has a defender within match_r
    (match_r_paint when r < 3 m) for >= hold_s."""
    p, A = _setup("transition_matched", scene, params)
    out = []
    for cp in A["cop"]:
        t = cp["t"]
        ok = np.zeros(scene.n, dtype=bool)
        for tt in range(t, scene.n):
            good = True
            for a in scene.offense:
                ka = scene.kins[a]
                thr = p["match_r_paint"] if ka.r[tt] < 3.0 else p["match_r"]
                dm = min(
                    math.hypot(scene.kins[d].x[tt] - ka.x[tt], scene.kins[d].y[tt] - ka.y[tt]) for d in scene.defense
                )
                good &= dm <= thr
            ok[tt] = good
        rs = [r for r in runs(ok) if (r[1] - r[0]) * DT >= p["hold_s"] - 1e-9]
        if not rs:
            continue
        a, b = rs[0]
        pr = np.ones(scene.n)
        for a_ in scene.offense:
            ka = scene.kins[a_]
            best = np.max(
                [
                    p_below(
                        dist(scene.kins[d], ka),
                        np.where(ka.r < 3.0, p["match_r_paint"], p["match_r"]),
                        sigma_rel(scene.kins[d], ka, p),
                    )
                    for d in scene.defense
                ],
                axis=0,
            )
            pr = pr * best
        ev = make_event(
            scene,
            p,
            "transition_matched",
            {"team": "D"},
            a,
            t,
            b,
            window_conf(pr, a, b),
            [
                f"every attacker within {p['match_r']} m ({p['match_r_paint']} m in the paint) of a defender for {(b - a) * DT:.2f} s"
            ],
            None,
            t_matched_s=(a - t) * DT,
        )
        if ev:
            out.append(ev)
    return out


def detect_press_pickup(scene, **params):
    """PRESS_PICKUP: a defender within pickup_r of the handler, between him and the rim, while the handler is
    in the backcourt (y > HALF_Y) for >= min_s."""
    p, A = _setup("press_pickup", scene, params)
    out = []
    for d in scene.defense:
        kd = scene.kins[d]
        for h in scene.offense:
            kh = scene.kins[h]
            held = np.array([scene.holder[t] == h for t in range(scene.n)])
            dd = dist(kd, kh)
            m = (
                held
                & (np.nan_to_num(kh.y, nan=0) > C["HALF_Y"])
                & (np.nan_to_num(dd, nan=99) <= p["pickup_r"])
                & (np.nan_to_num(kd.y - kh.y, nan=9) < 0)
            )
            for a, b in hysteresis(m, m, p["min_s"], p["dwell_frames"]):
                pc = window_conf(p_below(dd, p["pickup_r"], sigma_rel(kd, kh, p)), a, b)
                ev = make_event(
                    scene,
                    p,
                    "press_pickup",
                    {"defender": d, "handler": h},
                    a,
                    a,
                    b,
                    pc,
                    [
                        f"handler in the backcourt (y > {C['HALF_Y']} m), defender within {p['pickup_r']} m for {(b - a) * DT:.2f} s"
                    ],
                    None,
                    state=True,
                    pickup_y=float(kh.y[a]),
                )
                if ev:
                    out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------
DETECTORS = {
    "matchup": detect_matchup,
    "def_locomotion": detect_def_locomotion,
    "closeout": detect_closeout,
    "closeout_length": detect_closeout_length,
    "closeout_profile": detect_closeout_profile,
    "closeout_fly_by": detect_closeout_fly_by,
    "recover": detect_recover,
    "minor_excursion": detect_minor_excursion,
    "step_release": detect_step_release,
    "stunt": detect_stunt,
    "dig": detect_dig,
    "help_and_recover": detect_help_and_recover,
    "sink": detect_sink,
    "jump_to_ball": detect_jump_to_ball,
    "deny": detect_deny,
    "face_guard": detect_face_guard,
    "beaten": detect_beaten,
    "contain": detect_contain,
    "back_pressure": detect_back_pressure,
    "box_out": detect_box_out,
    "get_back": detect_get_back,
    "safety_back": detect_safety_back,
    "rotate": detect_rotate,
    "switch": detect_switch,
    "x_out": detect_x_out,
    "sink_and_fill": detect_sink_and_fill,
    "guard_two": detect_guard_two,
    "trap": detect_trap,
    "xball_path": detect_xball_path,
    "drop_coverage": detect_drop_coverage,
    "show": detect_show,
    "blitz": detect_blitz,
    "ice": detect_ice,
    "tag": detect_tag,
    "offball_screen_coverage": detect_offball_screen_coverage,
    "post_position": detect_post_position,
    "lob_protection": detect_lob_protection,
    "post_double": detect_post_double,
    "protect_rim": detect_protect_rim,
    "stop_ball": detect_stop_ball,
    "transition_matched": detect_transition_matched,
    "set_def": detect_set_def,
    "press_pickup": detect_press_pickup,
}


def _needs_data(item_id):
    def fn(scene, **params):
        """Not detectable from XY (+ ball XY): see needs_data in the YAML. Always returns []."""
        return []

    fn.__name__ = f"detect_{item_id}"
    return fn


NOT_DETECTABLE = {}  # items marked needs_data (or built by the composition engine): stubs that return []
for _it in SPEC["items"]:
    if _it.get("detectability") in ("needs_data", "composition"):
        globals()[f"detect_{_it['id']}"] = _needs_data(_it["id"])
        NOT_DETECTABLE[_it["id"]] = globals()[f"detect_{_it['id']}"]


def abstained_events(scene) -> list:
    """Candidates that passed P_emit but abstained (loop 4): one Event of kind 'abstain_<reason>:<kind>' per candidate,
    conf 0, attrs {'reason', 'kind'}. Reasons: 'q10' (globals.high_noise_abstain_kinds in the q = 10 tier), 'dposs' (the
    labelled defence had the ball at t0, L4-POSSESSION)."""
    out = []
    for (reason, kind, _, t0, end), (start, actors) in sorted(_cache(scene).get("abstained", {}).items(), key=lambda kv: kv[0][3]):
        out.append(Event(f"abstain_{reason}:{kind}", actors, t0, start, end, 0.0, {"reason": reason, "kind": kind}))
    return out


def detect_all(scene: Scene, anchors=None) -> dict:
    """Run every detector on one scene: {item_id: [Event, ...]} plus 'abstained' (abstained_events, loop 4: an abstaining
    kind is reported, not silently empty)."""
    out = {k: fn(scene, anchors=anchors) if anchors is not None else fn(scene) for k, fn in DETECTORS.items()}
    out["abstained"] = abstained_events(scene)
    return out
