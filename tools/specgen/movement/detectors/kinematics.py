"""Kinematics family detectors (spec tooling, not the production labeller).

One detector per item of config/movement_grammar/kinematics.yaml, signature
detect_<id>(scene, **params) -> list[mvlib.Event]. Every threshold is read from that YAML file at
import (single source of truth); keyword arguments override single parameters for experiments.

Inputs are mvlib.Scene objects: CA-RTS kinematics per player and ball (MP-04), the per-frame ball
holder, attacked-rim frame in metres, 29.97 fps. Conventions shared by every detector:
- stationary means the chi-square statistic stationary_s2 < 5.99 (MP-09), never raw speed < 0.3;
- speed_L is the 0.5 s centred mean of CA-RTS speed, sigma_L its window sigma (MP-10);
- v_c is the bias-corrected low speed sqrt(max(speed_L^2 - 2 sigma^2, 0)) (Rician floor removed);
- direction changes use pre/post mean velocities that skip the plant phase (MP-13);
- conf = P_cond x c_edge x c_gap x c_id x cap (MP-16), emitted when conf >= emit_min.
Each Event carries attrs.reasons (thresholds passed, with units), attrs.alternatives (competing
labels with probabilities) and attrs.conf_components.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import yaml

_HERE = Path(__file__).resolve()
_MOVEMENT = _HERE.parents[1]  # tools/specgen/movement
_ROOT = _HERE.parents[4]  # repository root
for _p in (_MOVEMENT, _MOVEMENT.parent / "named_spots"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mvlib  # noqa: E402
import spotlib  # noqa: E402
from mvlib import DT, K_CAL, Event, frames, phi  # noqa: E402

YAML_PATH = _ROOT / "config" / "movement_grammar" / "kinematics.yaml"


# --------------------------------------------------------------------------------------
# Parameters (loaded once from the YAML; {value, unit} pairs flattened to values)
# --------------------------------------------------------------------------------------
def _flatten(block) -> dict:
    return {k: (v["value"] if isinstance(v, dict) and "value" in v else v) for k, v in (block or {}).items()}


def load_params(path: Path = YAML_PATH):
    """Return (document, common params, {item id: params})."""
    doc = yaml.safe_load(Path(path).read_text())
    common = _flatten(doc["common"]["params"])
    items = {it["id"]: _flatten(it.get("params")) for it in doc["items"]}
    return doc, common, items


DOC, COMMON, PARAMS = load_params()
SCHEME = DOC["scheme_version"]
BANDS = ("walk", "jog", "run", "high_speed", "sprint")


def _cfg(item: str, overrides: dict) -> dict:
    """Common params, then the band rule for band items, then the item, then caller overrides."""
    c = dict(COMMON)
    if item in BANDS:
        c.update(PARAMS["kin_speed_bands"])
    c.update(PARAMS[item])
    c.update(overrides)
    return c


# --------------------------------------------------------------------------------------
# Noise tier (KIN-T09): mvlib switches CA-RTS to q 10 when median sigma_p >= tier_sigma_p, but Kin
# does not carry sigma_p. The smoothed covariance ratio sqrt(var_v / var_p) is a deterministic
# function of (q, sigma_p) in steady state and drops by about 20% when q switches, so the tier is read
# from it against the steady-state ratios of both q values at tier_sigma_p (computed, not hard-coded).
# --------------------------------------------------------------------------------------
def _steady_ratio(q: float, sigma_p: float) -> float:
    n = 241
    _, Ps, _ = mvlib.ca_rts(np.zeros(n), np.full(n, sigma_p**2), q)
    m = n // 2
    return math.sqrt(Ps[m, 1, 1] / Ps[m, 0, 0])


_TIER_SPLIT = math.sqrt(_steady_ratio(mvlib.Q_DEFAULT, COMMON["tier_sigma_p"])
                        * _steady_ratio(mvlib.Q_HIGH_NOISE, COMMON["tier_sigma_p"]))


def _tier(k) -> str:
    """'q10' when the track was smoothed at the high-noise q (median sigma_p >= tier_sigma_p), else 'q30'."""
    inner = (k.edge >= mvlib.EDGE_FRAMES) & ~np.isnan(k.var_p)
    if not inner.any():
        inner = ~np.isnan(k.var_p)
    if not inner.any():
        return "q30"
    ratio = np.sqrt(k.var_v[inner] / np.maximum(k.var_p[inner], 1e-12))
    return "q10" if float(np.nanmedian(ratio)) < _TIER_SPLIT else "q30"


def _tv(c: dict, key: str, tier: str):
    """Tier value: c[key + '_q10'] at the q 10 tier when the YAML defines it, else c[key]."""
    return c.get(f"{key}_q10", c[key]) if tier == "q10" else c[key]


# --------------------------------------------------------------------------------------
# Named spots (labels only; never redefined here)
# --------------------------------------------------------------------------------------
_SPOTS = None


def _spot(x, y) -> str:
    """Canonical court_region label of a point (first label), 'unknown' when missing."""
    global _SPOTS
    if _SPOTS is None:
        _SPOTS = spotlib.load()[1]
    if x is None or y is None or not (np.isfinite(x) and np.isfinite(y)):
        return "unknown"
    labs = spotlib.court_region(_SPOTS, float(x), float(y))
    return labs[0] if labs else "none"


# --------------------------------------------------------------------------------------
# Array helpers
# --------------------------------------------------------------------------------------
def _odd(seconds: float) -> int:
    """Odd window length in frames covering `seconds`."""
    n = max(1, frames(seconds))
    return n if n % 2 == 1 else n + 1


def _mov_mean(a, n: int, min_frac: float = 0.5) -> np.ndarray:
    """Centred NaN-aware moving mean over n frames; NaN where fewer than min_frac of n are valid."""
    a = np.asarray(a, dtype=float)
    m = ~np.isnan(a)
    z = np.where(m, a, 0.0)
    cs = np.concatenate([[0.0], np.cumsum(z)])
    cn = np.concatenate([[0], np.cumsum(m)])
    h = n // 2
    idx = np.arange(len(a))
    lo = np.clip(idx - h, 0, len(a))
    hi = np.clip(idx + h + 1, 0, len(a))
    s, c = cs[hi] - cs[lo], cn[hi] - cn[lo]
    need = max(1, int(math.ceil(min_frac * n)))
    return np.where(c >= need, s / np.maximum(c, 1), np.nan)


def _shift(a, k: int) -> np.ndarray:
    """out[t] = a[t - k] (NaN where out of range)."""
    a = np.asarray(a, dtype=float)
    out = np.full(len(a), np.nan)
    if k >= 0:
        out[k:] = a[: len(a) - k]
    else:
        out[:k] = a[-k:]
    return out


def _runs(mask) -> list[tuple[int, int]]:
    """Inclusive runs of True."""
    out, a = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and a is None:
            a = i
        elif not v and a is not None:
            out.append((a, i - 1))
            a = None
    return out


def _wrap(deg):
    return (np.asarray(deg) + 180.0) % 360.0 - 180.0


def _nanmean(a, lo, hi):
    seg = np.asarray(a[max(0, lo):hi + 1], dtype=float)
    seg = seg[~np.isnan(seg)]
    return float(np.mean(seg)) if len(seg) else float("nan")


def _nanmax(a, lo, hi):
    seg = np.asarray(a[max(0, lo):hi + 1], dtype=float)
    seg = seg[~np.isnan(seg)]
    return float(np.max(seg)) if len(seg) else float("nan")


def _nanmin_masked(a, ok, lo, hi):
    lo, hi = max(0, lo), min(len(a) - 1, hi)
    seg = np.where(ok[lo:hi + 1], a[lo:hi + 1], np.nan)
    seg = seg[~np.isnan(seg)]
    return float(np.min(seg)) if len(seg) else float("nan")


def _r(v, nd=2):
    return None if v is None or not np.isfinite(v) else round(float(v), nd)


# --------------------------------------------------------------------------------------
# Shared per-player features (kin_features, kin_speed_bands)
# --------------------------------------------------------------------------------------
class _F:
    """Derived per-frame features of one Kin used by several detectors."""

    def __init__(self, k: mvlib.Kin, c: dict):
        self.k = k
        n = len(k.x)
        self.tier = _tier(k)
        self.corr = _tv(c, "corr_time_s", self.tier)  # KIN-T09: longer error correlation at q 10
        self.v = k.speed
        # secondary artefact check (kin_features.artefact_speed_cap); MP-03 screens raw positions first
        self.artefact = np.nan_to_num(self.v) > PARAMS["kin_features"]["artefact_speed_cap"]
        self.ok = np.isin(k.state, ["observed", "interp_short"]) & (k.edge >= c["edge_min_frames"]) & ~self.artefact
        self.sig = k.sigma_speed  # per-axis velocity sigma incl. k_cal and edge inflation (MP-09)
        nb = _odd(c["band_window_s"])
        self.vL = _mov_mean(self.v, nb)
        red = math.sqrt(max(1.0, nb * DT / self.corr))
        self.sL = self.sig / red
        # v_c from the RMS speed (MP-09: E[speed^2 | v] = v^2 + 2 sigma^2), KIN-T03
        ms2 = _mov_mean(self.v**2, nb)
        self.vc = np.sqrt(np.maximum(ms2 - 2.0 * self.sig**2, 0.0))
        self.p_stand = phi((c["stand_speed"] - self.vc) / np.maximum(self.sL, 1e-6))
        self.p_stand[np.isnan(self.vL)] = np.nan
        self.s2 = k.stationary_s2
        self.n = n

    def band_probs(self, his: dict | None = None) -> dict:
        """MP-10 soft membership: six probabilities that sum to 1 (stand via the bias-corrected speed).

        his: optional upper edges per band (m/s); defaults to the YAML edges.
        """
        his = his or {b: PARAMS[b]["hi"] for b in BANDS}
        moving = 1.0 - self.p_stand
        out = {"stand": self.p_stand}
        prev = np.zeros(self.n)
        for b in BANDS:
            hi = his[b]
            cdf = phi((hi - self.vL) / np.maximum(self.sL, 1e-6))
            out[b] = moving * (cdf - prev)
            prev = cdf
        for b in out:
            out[b] = np.where(np.isnan(self.vL), np.nan, out[b])
        return out


def _run_check(f: _F, a: int, b: int, st: dict) -> tuple[float, float | None]:
    """KIN-T03 run-level stand test: net displacement speed between the first and last end windows.

    v_run = |mean pos over the last end window - mean pos over the first| / (duration - end window) is a
    mean velocity over the span, so its per-axis sigma is the family's mean-velocity sigma
    sigma_run = mean sigma_speed / sqrt(max(1, span / corr_time)) (MP-09 / MP-12; the posterior var_p
    ignores the AR(1) position error and rejected true stands at sigma_p 0.5), and the Rician floor is
    removed as for v_c: v_run_c = sqrt(max(v_run^2 - 2 sigma_run^2, 0)). Returns (P(v_run_c < stand_speed),
    v_run_c). Runs shorter than two disjoint end windows return (1.0, None): the frame gates decide alone.
    """
    k = f.k
    w = frames(st["run_check_end_s"])
    span = (b - a) * DT - w * DT
    if span < w * DT:
        return 1.0, None
    ax_, ay_ = _nanmean(k.x, a, a + w), _nanmean(k.y, a, a + w)
    bx_, by_ = _nanmean(k.x, b - w, b), _nanmean(k.y, b - w, b)
    v_run = math.hypot(bx_ - ax_, by_ - ay_) / span
    sp = _nanmean(f.sig, a, b) / math.sqrt(max(1.0, span / f.corr))
    if not (np.isfinite(v_run) and np.isfinite(sp)):
        return 1.0, None
    v_c = math.sqrt(max(v_run**2 - 2.0 * sp**2, 0.0))
    return float(phi((st["stand_speed"] - v_c) / max(sp, 1e-6))), v_c


def _stationary_runs(f: _F, c: dict, min_s: float, run_check: bool = True) -> list[tuple[int, int, float, float | None]]:
    """Stand gate shared by stand, stop and start: s2 test plus bias-corrected soft membership, then (stand
    only) the run-level displacement check (KIN-T03). Returns (a, b, p_run, v_run) per run.

    stop and start pass run_check=False: their runs begin (stop) or end (start) inside the speed transition,
    so the end windows carry the residual motion (S_sprint stop: v_run 0.50 m/s, P 0.499, rejected)."""
    st = {**COMMON, **PARAMS["stand"], **{key: v for key, v in c.items() if key in PARAMS["stand"]}}  # caller overrides win
    ps = np.nan_to_num(f.p_stand, nan=0.0)
    enter = f.ok & (f.s2 < st["s2_enter"]) & (ps >= st["p_enter"])
    stay = f.ok & (f.s2 < st["s2_stay"]) & (ps >= st["p_stay"])
    out = []
    e = frames(_tv(st, "run_check_ext_s", f.tier))
    for a, b in mvlib.hysteresis(enter, stay, min_s, frames(st["bridge_s"])):
        p_run, v_run = _run_check(f, a, b, st) if run_check else (1.0, None)
        if run_check and e > 0:
            # KIN2-STAND: a slow walker moves on both sides of a noise-stalled fragment, a true stand is
            # entered or left on at most one side (or runs into the clip edge). Repeat the check on the run
            # extended by run_check_ext_s on each side; keep the larger one-sided P (an extension past the
            # clip edge is not evidence of motion), and the run passes on min(P_run, that).
            n = len(f.v)
            pl = _run_check(f, a - e, b, st)[0] if a - e >= 0 else 1.0
            pr = _run_check(f, a, b + e, st)[0] if b + e <= n - 1 else 1.0
            p_run = min(p_run, max(pl, pr))
        if p_run >= _tv(st, "run_check_p_min", f.tier):
            out.append((a, b, p_run, v_run))
    return out


def _coverage(k, a, b) -> float:
    st = k.state[a:b + 1]
    return float(np.mean(st == "observed")) if len(st) else 0.0


def _c_id(scene, oid, a, b, c) -> float:
    """MP-16 c_id: another player within id_ambig_r while either track had a rejected innovation nearby."""
    k = scene.k(oid)
    pad = frames(c["id_ambig_pad_s"])
    lo, hi = max(0, a - pad), min(scene.n - 1, b + pad)
    for other in scene.players():
        if other == oid:
            continue
        ko = scene.k(other)
        d = np.hypot(k.x[lo:hi + 1] - ko.x[lo:hi + 1], k.y[lo:hi + 1] - ko.y[lo:hi + 1])
        near = np.nan_to_num(d, nan=9e9) <= c["id_ambig_r"]
        if not near.any():
            continue
        rej = k.rejected[lo:hi + 1] | ko.rejected[lo:hi + 1]
        if rej.any():
            return c["c_id_ambiguous"]
    return 1.0


def _edge_mean(k, a, b) -> float:
    """Mean of the per-frame MP-06 edge factor over [a, b] (0 within 5 frames of an edge)."""
    e = k.edge[a:b + 1]
    f = np.array([0.0 if x < 5 else 1.0 / mvlib.K_EDGE.get(int(x), 1.0) for x in e])  # same rule as mvlib.edge_factor
    return float(np.mean(f)) if len(f) else 0.0


def _dead_mask(scene) -> np.ndarray:
    """kin_validity all-players-slow proxy (tag only, never excludes time): every player's speed_L below
    dead_proxy_speed, ball speed below dead_proxy_ball_speed and the player centroid static (speed below
    dead_proxy_centroid_speed) for >= dead_proxy_s. False where the ball is unobserved. Cached per scene."""
    cached = getattr(scene, "_kin_dead_mask", None)
    if cached is not None:
        return cached
    v = PARAMS["kin_validity"]
    nb = _odd(COMMON["band_window_s"])
    mask = np.zeros(scene.n, dtype=bool)
    if scene.ball is not None and scene.players():
        slow = np.ones(scene.n, dtype=bool)
        cx, cy = np.zeros(scene.n), np.zeros(scene.n)
        for oid in scene.players():
            k = scene.k(oid)
            slow &= np.nan_to_num(_mov_mean(k.speed, nb), nan=99.0) < v["dead_proxy_speed"]
            cx, cy = cx + k.x, cy + k.y
        m = len(scene.players())
        cvx, cvy = np.gradient(cx / m) / DT, np.gradient(cy / m) / DT
        cspeed = _mov_mean(np.hypot(cvx, cvy), nb)
        bspeed = np.hypot(scene.ball.vx, scene.ball.vy)
        cond = slow & (np.nan_to_num(bspeed, nan=99.0) < v["dead_proxy_ball_speed"]) \
            & (np.nan_to_num(cspeed, nan=99.0) < v["dead_proxy_centroid_speed"])
        for a, b in mvlib.hysteresis(cond, cond, v["dead_proxy_s"]):
            mask[a:b + 1] = True
    try:
        scene._kin_dead_mask = mask
    except AttributeError:
        pass
    return mask


def _event(scene, oid, kind, t0, a, b, p_cond, c, attrs, reasons, alternatives=None, cap=1.0, actors=None, state=False):
    """Assemble an Event with the MP-16 confidence, or None when it fails coverage or emit_min.

    Point events take c_edge at t0; states (state=True) take the window mean of the per-frame edge
    factor, so a stand that is already under way when the segment starts is not discarded for its
    first frame (it is flagged left_censored instead).
    """
    k = scene.k(oid)
    a, b = int(max(0, a)), int(min(scene.n - 1, b))
    t0 = int(min(max(t0, 0), scene.n - 1))
    cov = _coverage(k, a, b)
    if cov < c["coverage_min"]:
        return None
    ce = _edge_mean(k, a, b) if state else mvlib.edge_factor(k, t0)
    cg = mvlib.gap_factor(k, a, b)
    ci = _c_id(scene, oid, a, b, c)
    p_cond = float(np.clip(np.nan_to_num(p_cond, nan=0.0), 0.0, 1.0))
    conf = float(p_cond * ce * cg * ci * cap)
    if conf < c["emit_min"]:
        return None
    attrs = dict(attrs)
    attrs.update(
        reasons=reasons,
        alternatives=alternatives or {},
        conf_components={"P_cond": round(p_cond, 3), "c_edge": round(ce, 3), "c_gap": cg, "c_id": ci, "cap": cap},
        coverage=round(cov, 3),
        left_censored=bool(k.edge[a] < mvlib.EDGE_FRAMES and a + 1 < scene.n and k.edge[a + 1] > k.edge[a]),
        review=conf < c["review_below"],
        scheme_version=SCHEME,
        context="dead_candidate" if _dead_mask(scene)[t0] else "live_or_unknown",
        artefact=bool(np.any(np.nan_to_num(k.speed[a:b + 1]) > PARAMS["kin_features"]["artefact_speed_cap"])),
    )
    return Event(kind, actors or {"player": oid}, t0, a, b, conf, attrs)


def _nms(events: list[Event], nms_s: float) -> list[Event]:
    """Keep the highest-confidence event of each kind and player within +-nms_s."""
    out = []
    w = frames(nms_s)
    for e in sorted(events, key=lambda e: -e.conf):
        if all(not (o.kind == e.kind and o.actors == e.actors and abs(o.t0 - e.t0) <= w) for o in out):
            out.append(e)
    return sorted(out, key=lambda e: e.t0)


# --------------------------------------------------------------------------------------
# Speed states
# --------------------------------------------------------------------------------------
def detect_stand(scene, **params) -> list[Event]:
    """stand: s2 < 5.99 (stay < 13.82) with bias-corrected P_stand, >= 0.5 s; t0 = first frame of the run."""
    c = _cfg("stand", params)
    out = []
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        for a, b, p_run, v_run in _stationary_runs(f, c, _tv(c, "min_s", f.tier)):
            cx, cy = _nanmean(k.x, a, b), _nanmean(k.y, a, b)
            dev = np.nanmax(np.hypot(k.x[a:b + 1] - cx, k.y[a:b + 1] - cy))
            sig_pos = K_CAL * math.sqrt(max(_nanmean(k.var_p, a, b), 0.0))
            strict_thr = max(c["strict_disp_m"], c["strict_sigma_mult"] * sig_pos)
            p_frame = mvlib.window_conf(f.p_stand, a, b)
            # P_run gates the run (>= run_check_p_min) but multiplies the confidence only when
            # run_check_conf is true: at sigma_p 0.5 the frame confidence of a true stand is already
            # 0.5-0.86, and the product dropped half of the true stands below emit_min
            p = p_frame * (p_run if c["run_check_conf"] else 1.0)
            reasons = [f"s2 < {c['s2_enter']} (chi2 2 dof) at entry, < {c['s2_stay']} throughout",
                       f"bias-corrected P(speed < {c['stand_speed']} m/s) mean {p_frame:.2f}",
                       f"run displacement speed {'n/a' if v_run is None else f'{v_run:.2f}'} m/s, P(< {c['stand_speed']} m/s) {p_run:.2f} >= {c['run_check_p_min']}",
                       f"duration {(b - a) * DT:.2f} s >= {c['min_s']} s"]
            p_walk = max(1 - p_frame, 1 - p_run)
            alt = {"walk": round(p_walk, 2)} if p_walk >= 0.2 else {}
            attrs = dict(centroid_x=_r(cx), centroid_y=_r(cy), spot=_spot(cx, cy), mean_speed=_r(_nanmean(f.vL, a, b)),
                         max_dev_m=_r(dev), stand_strict=bool(dev <= strict_thr), strict_thr_m=_r(strict_thr),
                         p_run=_r(p_run, 3), v_run=_r(v_run))
            ev = _event(scene, oid, "stand", a, a, b, p, c, attrs, reasons, alt, state=True)
            if ev:
                out.append(ev)
    return out


def _band_p_max_median(f: _F, c: dict) -> float | None:
    """Median over valid frames of the best attainable band membership 2 Phi(half width / sigma_L) - 1 (the
    membership of a frame whose speed_L sits exactly at the band centre); None when no frame is valid."""
    sl = f.sL[f.ok & np.isfinite(f.sL)]
    if sl.size == 0:
        return None
    return float(np.median(2.0 * phi(0.5 * (c["hi"] - c["lo"]) / np.maximum(sl, 1e-6)) - 1.0))


def _unresolvable_reports(scene, oid, band: str, f: _F, probs: dict, c: dict, p_max_med: float) -> list[Event]:
    """Abstention reports (conf 0, kind 'abstain_unresolvable:<band>') for the stretches of >= min_s whose
    speed_L lies in [lo, hi): the band is unresolvable on this track, so the time it would cover is reported."""
    inband = f.ok & np.nan_to_num((f.vL >= c["lo"]) & (f.vL < c["hi"]), nan=False).astype(bool)
    sl = f.sL[f.ok & np.isfinite(f.sL)]
    out = []
    for a, b in mvlib.hysteresis(inband, inband, c["min_s"], frames(c["bridge_s"])):
        alts = {o: round(mvlib.window_conf(probs[o], a, b), 2) for o in probs if o != band}
        attrs = dict(band=band, reason="unresolvable", tier=f.tier, p_max_median=_r(p_max_med, 3),
                     p_enter=c["p_enter"], sigma_L_median=_r(float(np.median(sl)), 3),
                     mean_speed=_r(_nanmean(f.vL, a, b)), peak_speed=_r(_nanmax(f.vL, a, b)),
                     mean_posterior=_r(mvlib.window_conf(probs[band], a, b), 3),
                     alternatives={o: v for o, v in alts.items() if v >= 0.2}, scheme_version=SCHEME,
                     reasons=[f"median best attainable P({band}) {p_max_med:.3f} < p_enter {c['p_enter']} "
                              f"(band {c['lo']}-{c['hi']} m/s, median sigma_L {float(np.median(sl)):.2f} m/s)",
                              f"speed_L in [{c['lo']}, {c['hi']}) m/s for {(b - a) * DT:.2f} s >= {c['min_s']} s"])
        out.append(Event(f"abstain_unresolvable:{band}", {"player": oid}, a, a, b, 0.0, attrs))
    return out


def _band_detector(band: str, scene, params) -> list[Event]:
    """MP-10 band segments: enter P(band) >= 0.7, stay >= 0.3, min 0.5 s; t0 back-dated to P >= 0.5."""
    c = _cfg(band, params)
    out = []
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        his = {b: PARAMS[b]["hi"] for b in BANDS}
        his[band] = c["hi"]  # caller overrides of this band's edges move the neighbours' edges too
        if BANDS.index(band) > 0:
            his[BANDS[BANDS.index(band) - 1]] = c["lo"]
        probs = f.band_probs(his)
        p = np.nan_to_num(probs[band], nan=0.0)
        if c.get("abstain_unresolvable", False):
            p_max_med = _band_p_max_median(f, c)
            if p_max_med is not None and p_max_med < c["p_enter"]:
                # decision 25 Oct (abstain but report): the band cannot reach p_enter on this track, so it is
                # reported as unresolvable over the stretches whose speed_L lies in the band, never emitted
                out += _unresolvable_reports(scene, oid, band, f, probs, c, p_max_med)
                continue
        enter = f.ok & (p >= c["p_enter"])
        stay = f.ok & (p >= c["p_stay"])
        for a, b in mvlib.hysteresis(enter, stay, c["min_s"], frames(c["bridge_s"])):
            t0 = a
            while t0 - 1 >= 0 and f.ok[t0 - 1] and p[t0 - 1] >= c["p_backdate"]:
                t0 -= 1
            pc = mvlib.window_conf(probs[band], t0, b)
            alts = {o: round(mvlib.window_conf(probs[o], t0, b), 2) for o in probs if o != band}
            alts = {o: v for o, v in alts.items() if v >= 0.2}
            dist_m = float(np.nansum(f.v[t0:b + 1]) * DT)
            reasons = [f"P({band}) >= {c['p_enter']} at entry, >= {c['p_stay']} throughout (edges {c['lo']}-{c['hi']} m/s on speed_L)",
                       f"duration {(b - t0) * DT:.2f} s >= {c['min_s']} s"]
            attrs = dict(band=band, mean_speed=_r(_nanmean(f.vL, t0, b)), peak_speed=_r(_nanmax(f.vL, t0, b)),
                         distance_m=_r(dist_m), mean_posterior=_r(pc, 3))
            ev = _event(scene, oid, band, t0, t0, b, pc, c, attrs, reasons, alts, state=True)
            if ev:
                out.append(ev)
    return out


def detect_walk(scene, **params) -> list[Event]:
    """walk band segment (not-stand and speed_L < 2.0 m/s)."""
    return _band_detector("walk", scene, params)


def detect_jog(scene, **params) -> list[Event]:
    """jog band segment (speed_L 2.0-4.0 m/s)."""
    return _band_detector("jog", scene, params)


def detect_run(scene, **params) -> list[Event]:
    """run band segment (speed_L 4.0-5.0 m/s)."""
    return _band_detector("run", scene, params)


def detect_high_speed(scene, **params) -> list[Event]:
    """high_speed band segment (speed_L 5.0-5.83 m/s)."""
    return _band_detector("high_speed", scene, params)


def detect_sprint(scene, **params) -> list[Event]:
    """sprint band segment (speed_L > 5.83 m/s)."""
    return _band_detector("sprint", scene, params)


def _direction_word(k, a, b, r: float) -> str:
    """Effort direction relative to the attacked rim: toward / away / lateral (mean v_r / mean speed vs +-r)."""
    vr = _nanmean(k.v_r, a, b)
    sp = _nanmean(k.speed, a, b)
    if not np.isfinite(vr) or not np.isfinite(sp) or sp <= 0:
        return "unknown"
    ratio = vr / sp
    return "toward_rim" if ratio >= r else "away_from_rim" if ratio <= -r else "lateral"


def _effort_detector(item: str, kind: str, scene, params) -> list[Event]:
    """Speed effort: enter at the published edge, exit at edge - h (exit-side hysteresis), min 1.0 s."""
    c = _cfg(item, params)
    out = []
    e = c["edge"]
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        h = np.maximum(c["h_min"], c["h_sigma_mult"] * f.sL)
        vL = np.nan_to_num(f.vL, nan=-1.0)
        enter = f.ok & (vL >= e)
        stay = f.ok & (vL >= e - h)
        for a, b in mvlib.hysteresis(enter, stay, c["min_s"]):
            # KIN-T09: the window was selected because speed_L crossed the edge, so the window mean of a
            # per-frame P(above) is optimistic; score the effort mean against the edge with the sigma of a
            # mean over the effort (duration in correlation times) minus a selection allowance z_sel.
            dur = (b - a + 1) * DT
            s_mean = _nanmean(f.sig, a, b) / math.sqrt(max(1.0, dur / f.corr))
            m_vL = _nanmean(f.vL, a, b)
            # KIN4-EFFORT: the reference is the stay level edge - conf_ref_h (the lowest true mean a rule-conforming
            # effort can have), not the entry edge: on real tracking ~20% of efforts peak at 5.0-5.4 m/s and scored < 0.5
            ref = e - _tv(c, "conf_ref_h", f.tier)
            pc = float(phi((m_vL - ref) / max(s_mean, 1e-6) - c["z_sel"]))
            attrs = dict(distance_m=_r(float(np.nansum(f.v[a:b + 1]) * DT)), peak_speed=_r(_nanmax(f.vL, a, b)),
                         mean_speed=_r(m_vL), direction=_direction_word(k, a, b, c["direction_ratio"]),
                         start_spot=_spot(k.x[a], k.y[a]), end_spot=_spot(k.x[b], k.y[b]),
                         duration_s=_r((b - a) * DT))
            reasons = [f"speed_L >= {e} m/s at entry, >= {e} - h throughout (h = max({c['h_min']}, {c['h_sigma_mult']} sigma_L))",
                       f"duration {(b - a) * DT:.2f} s >= {c['min_s']} s",
                       f"effort mean speed_L {m_vL:.2f} m/s vs stay level {ref:.2f} m/s: Phi(margin / {s_mean:.2f} - {c['z_sel']}) = {pc:.2f}"]
            alts = {}
            if "view_edge" in c:
                above = np.nan_to_num(f.vL[a:b + 1], nan=0) > c["view_edge"]
                attrs["time_above_6p69_s"] = _r(float(np.sum(above)) * DT)
                runs = [(x, y) for x, y in _runs(np.nan_to_num(f.vL[a:b + 1], nan=0) >= c["vhs_edge"])]
                attrs["vhs"] = any((y - x) * DT >= c["min_s"] for x, y in runs)
                alts = {"sprint_6p69_view": attrs["time_above_6p69_s"] >= c["min_s"]}
            ev = _event(scene, oid, kind, a, a, b, pc, c, attrs, reasons, alts, state=True)
            if ev:
                out.append(ev)
    return out


def detect_hsr_effort(scene, **params) -> list[Event]:
    """hsr_effort: speed_L >= 5.0 m/s for >= 1.0 s (exit at 5.0 - h)."""
    return _effort_detector("hsr_effort", "hsr_effort", scene, params)


def detect_sprint_effort(scene, **params) -> list[Event]:
    """sprint_effort: speed_L > 5.83 m/s for >= 1.0 s, with the 6.69 view and the 7.0 vhs flag."""
    return _effort_detector("sprint_effort", "sprint_effort", scene, params)


def detect_peak_speed(scene, **params) -> list[Event]:
    """peak_speed: frame of the max 1 s rolling-mean speed per player per clip (>= 3.5 m/s, frame >= 4.0)."""
    c = _cfg("peak_speed", params)
    out = []
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        n1 = _odd(c["window_s"])
        v_ok = np.where(f.ok, f.v, np.nan)  # KIN-T10: inflated edge frames never enter the mean
        v1 = _mov_mean(v_ok, n1, min_frac=0.9)
        v1 = np.where(f.ok, v1, np.nan)
        if np.all(np.isnan(v1)):
            continue
        t = int(np.nanargmax(v1))
        h = n1 // 2
        a, b = max(0, t - h), min(scene.n - 1, t + h)
        frame_max = _nanmax(v_ok, a, b)
        if not (v1[t] >= c["mean_min"] and frame_max >= c["frame_min"]):
            continue
        s1 = f.sig[t] / math.sqrt(max(1.0, n1 * DT / f.corr))
        # the clip maximum of N_eff roughly independent 1 s means is biased high by about sqrt(2 ln N_eff) sigma
        n_eff = float(np.sum(f.ok)) * DT / c["window_s"]
        z_max = math.sqrt(2.0 * math.log(max(1.0, n_eff)))
        pc = float(phi((v1[t] - c["mean_min"]) / max(s1, 1e-6) - z_max))
        reasons = [f"1 s mean speed {v1[t]:.2f} m/s >= {c['mean_min']} m/s", f"frame speed {frame_max:.2f} m/s >= {c['frame_min']} m/s",
                   f"max-selection allowance sqrt(2 ln N_eff) = {z_max:.2f} sigma (N_eff {n_eff:.1f})"]
        attrs = dict(peak_1s=_r(v1[t]), peak_frame_speed=_r(frame_max), x=_r(k.x[t]), y=_r(k.y[t]),
                     spot=_spot(k.x[t], k.y[t]), scope="clip")
        ev = _event(scene, oid, "peak_speed", t, a, b, pc, c, attrs, reasons)
        if ev:
            out.append(ev)
    return out


def _accel_view(item: str, sign: float, scene, params) -> list[Event]:
    """Instantaneous acceleration view on CA-RTS accel_along (exploratory, capped until released)."""
    c = _cfg(item, params)
    out = []
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        acc = sign * k.accel_along
        sa = K_CAL * np.sqrt(k.var_a) * k.k_edge
        a_ok = np.nan_to_num(acc, nan=-99.0)
        hi = f.ok & (a_ok >= c["a_enter"])
        for a, b in mvlib.hysteresis(hi, hi, c["min_s"]):
            e = b
            while e + 1 < scene.n and f.ok[e + 1] and a_ok[e + 1] > 0:
                e += 1
            dv = sign * (_nanmean(f.v, e - 1, e + 1) - _nanmean(f.v, a - 1, a + 1))
            if not dv >= c["dv_check"]:
                continue
            peak = float(np.nanmax(acc[a:e + 1]))
            pc = mvlib.window_conf(mvlib.p_above(acc, c["a_enter"], sa), a, b)
            cap = 1.0 if c["released"] else c["view_cap"]
            reasons = [f"{'accel' if sign > 0 else 'decel'}_along >= {c['a_enter']} m/s^2 for {(b - a) * DT:.2f} s >= {c['min_s']} s",
                       f"speed change {dv:.2f} m/s >= {c['dv_check']} m/s"]
            attrs = dict(peak_a=_r(peak), mean_a=_r(float(np.nanmean(acc[a:e + 1]))), delta_v=_r(dv),
                         start_speed=_r(f.v[a]), end_speed=_r(f.v[e]),
                         band="high" if peak >= c["a_high"] else "moderate", peak_capped=bool(peak > c["a_report_max"]),
                         gate_status="released" if c["released"] else "exploratory",
                         primary_equivalent="burst" if sign > 0 else "brake")  # MP-14 primary acc/dec primitive
            ev = _event(scene, oid, item, a, a, e, pc, c, attrs, reasons, cap=cap, state=True)
            if ev:
                out.append(ev)
    return out


def detect_accel_effort(scene, **params) -> list[Event]:
    """accel_effort view: accel_along >= 2.0 m/s^2 for >= 0.5 s (exploratory until MP-18 gate)."""
    return _accel_view("accel_effort", 1.0, scene, params)


def detect_decel_effort(scene, **params) -> list[Event]:
    """decel_effort view: accel_along <= -2.0 m/s^2 for >= 0.5 s (exploratory until MP-18 gate)."""
    return _accel_view("decel_effort", -1.0, scene, params)


# --------------------------------------------------------------------------------------
# Velocity-change events (MP-14): zig-zag turning points on the smoothed speed
# --------------------------------------------------------------------------------------
def _zigzag(v, a, b, r) -> list[tuple[int, str]]:
    """Alternating turning points ('min' / 'max') of v[a..b] with retrace >= r."""
    pts, mode, lo, hi = [], None, a, a
    for i in range(a + 1, b + 1):
        if mode is None:
            if v[i] < v[lo]:
                lo = i
            if v[i] > v[hi]:
                hi = i
            if v[i] - v[lo] >= r and lo < i:
                pts.append((lo, "min")); mode, hi = "up", i
            elif v[hi] - v[i] >= r and hi < i:
                pts.append((hi, "max")); mode, lo = "down", i
        elif mode == "up":
            if v[i] > v[hi]:
                hi = i
            elif v[hi] - v[i] >= r:
                pts.append((hi, "max")); mode, lo = "down", i
        else:
            if v[i] < v[lo]:
                lo = i
            elif v[i] - v[lo] >= r:
                pts.append((lo, "min")); mode, hi = "up", i
    if mode == "up":
        pts.append((hi, "max"))
    elif mode == "down":
        pts.append((lo, "min"))
    return pts


def _hinge_onset(v, lo: int, hi: int) -> int:
    """Change-point onset: tc minimising the SSE of v ~ p + s * max(0, t - tc) over [lo, hi]."""
    t = np.arange(lo, hi + 1, dtype=float)
    y = v[lo:hi + 1]
    best, best_tc = np.inf, lo
    for tc in range(lo, hi - 1):
        X = np.column_stack([np.ones_like(t), np.maximum(0.0, t - tc)])
        coef, *_ = np.linalg.lstsq(X, y, rcond=None)
        sse = float(np.sum((y - X @ coef) ** 2))
        if sse < best:
            best, best_tc = sse, tc
    return best_tc


def _velocity_changes(k, f, c, sign) -> list[dict]:
    """Raw rises (sign +1) or falls (sign -1) between zig-zag turning points, gated on delta_v."""
    vs = _mov_mean(f.v, _odd(c["smooth_s"]))
    vs = np.where(f.ok, vs, np.nan)
    wmax = frames(_tv(c, "win_max_s", f.tier))  # KIN-T08: one extra smoother support at q 10
    out = []
    for a, b in _runs(~np.isnan(vs)):
        pts = _zigzag(vs, a, b, c["retrace"])
        prev_tp = {pts[n + 1][0]: pts[n][0] for n in range(len(pts) - 1)}
        for (i, ti), (j, tj) in zip(pts, pts[1:]):
            if (sign > 0 and (ti, tj) != ("min", "max")) or (sign < 0 and (ti, tj) != ("max", "min")):
                continue
            if (j - i) * DT < c["min_s"] - 1e-9:
                continue
            seg = sign * vs[i:j + 1]
            # steepest gain inside any <= win_max_s sub-window (mean acceleration >= dv_min / 1 s)
            best = 0.0
            for q in range(len(seg)):
                best = max(best, float(np.max(seg[q:q + wmax + 1]) - seg[q]))
            dv = sign * (vs[j] - vs[i])
            sig_dv = math.sqrt(f.sig[i] ** 2 + f.sig[j] ** 2)  # MP-14 (k_cal already in sigma_speed)
            if best < c["dv_min"] - 2.0 * sig_dv:  # cheap pre-filter; the confidence decides emission
                continue
            # 20% / 80% level frames, searched outward from the steepest frame so that a noisy
            # plateau before the change cannot pull them early
            lev20, lev80 = vs[i] + sign * 0.2 * dv, vs[i] + sign * 0.8 * dv
            t_mid = i + int(np.argmax(sign * np.gradient(vs[i:j + 1]))) if j - i >= 2 else i
            before = [t for t in range(i, t_mid + 1) if sign * (vs[t] - lev20) < 0]
            t20 = before[-1] + 1 if before else i
            t80 = next((t for t in range(t_mid, j + 1) if sign * (vs[t] - lev80) >= 0), j)
            t20 = min(t20, t80)
            # onset = change-point (hinge) fit over the plateau before the change and the change
            # itself up to the 80% level; the fit window may start onset_lookback_s before the turning
            # point (bounded by the previous turning point) because a noisy plateau puts that point late;
            # KIN-T07: it never starts more than hinge_before_t20_s before the 20% level, so an early
            # zig-zag extreme on a long noisy plateau cannot drag the onset back
            lo = max(a, prev_tp.get(i, a), i - frames(c["onset_lookback_s"]), t20 - frames(c["hinge_before_t20_s"]))
            t0 = _hinge_onset(vs, lo, max(t80, lo + 3)) if t80 - lo >= 3 else i
            t_end = min(j, int(round(t80 + (t80 - t20) / 3.0)))  # tangent extrapolated to the end level
            out.append(dict(i=i, j=j, t0=t0, t20=t20, t80=t80, t_end=t_end, dv=dv, dv_1s=best, sig_dv=sig_dv,
                            v_i=vs[i], v_j=vs[j], vc_i=f.vc[i], vc_j=f.vc[j]))
    return out


def _vc_events(item: str, sign: float, scene, params) -> list[Event]:
    c = _cfg(item, params)
    out = []
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        for r in _velocity_changes(k, f, c, sign):
            pc = float(phi((r["dv_1s"] - c["dv_min"]) / max(r["sig_dv"], 1e-6)))
            end = min(r["j"], r["t0"] + frames(c["max_s"]))
            word = "rise" if sign > 0 else "fall"
            reasons = [f"speed {word} {r['dv_1s']:.2f} m/s within <= {c['win_max_s']} s (>= {c['dv_min']} m/s)",
                       f"trough-peak duration {(r['j'] - r['i']) * DT:.2f} s >= {c['min_s']} s"]
            attrs = dict(start_speed=_r(r["v_i"]), end_speed=_r(r["v_j"]), delta_v=_r(r["dv"]), delta_v_1s=_r(r["dv_1s"]),
                         band="high" if r["dv_1s"] >= c["dv_high"] else "moderate", t_extreme=r["j"])
            alts = {}
            if sign > 0:
                attrs["mean_acc"] = _r(r["dv"] / max((r["j"] - r["t0"]) * DT, DT))
                vc0 = r["vc_i"]
                if k.edge[r["i"]] < c["edge_min_frames"] + 1:
                    sub = "start_unknown"
                elif vc0 < c["from_stand_below"]:
                    sub = "from_stand"
                elif vc0 >= c["change_of_pace_from"]:
                    sub = "change_of_pace"
                else:
                    sub = "from_walk"
                attrs.update(sub_type=sub, heading_end=_r(k.heading[r["j"]], 1), v_r_end=_r(k.v_r[r["j"]]),
                             has_ball=bool(scene.holder[r["t0"]] == oid))
            else:
                attrs.update(mean_dec=_r(r["dv"] / max((r["j"] - r["t0"]) * DT, DT)), end_speed_bias_corrected=_r(r["vc_j"]))
            if r["dv_1s"] < c["dv_high"] and r["dv_1s"] >= c["dv_high"] - r["sig_dv"]:
                alts["high"] = round(float(phi((r["dv_1s"] - c["dv_high"]) / r["sig_dv"])), 2)
            ev = _event(scene, oid, item, r["t0"], r["t0"], end, pc, c, attrs, reasons, alts)
            if ev:
                out.append(ev)
    return _nms(out, c["nms_s"])


def detect_burst(scene, **params) -> list[Event]:
    """burst: speed gain >= 2.0 m/s within <= 1.0 s between zig-zag trough and peak (MP-14)."""
    return _vc_events("burst", 1.0, scene, params)


def detect_brake(scene, **params) -> list[Event]:
    """brake: speed loss >= 2.0 m/s within <= 1.0 s between zig-zag peak and trough (MP-14); attrs.next."""
    evs = _vc_events("brake", -1.0, scene, params)
    if not evs:
        return evs
    c = _cfg("brake", params)
    w = frames(c["next_window_s"])
    passthrough = {key: v for key, v in params.items() if key in COMMON}  # common overrides reach the linked detectors
    later = {"cod": detect_cod(scene, **passthrough), "burst": detect_burst(scene, **passthrough)}
    for e in evs:  # what follows the trough within 0.5 s: stop, cod, burst or continue
        pid = e.actors["player"]
        j = e.attrs["t_extreme"]
        s2 = scene.k(pid).stationary_s2[j:j + w + 1]
        nxt = "continue"
        if np.nanmin(np.nan_to_num(s2, nan=99.0)) < PARAMS["stand"]["s2_enter"]:
            nxt = "stop"
        elif any(x.actors == e.actors and abs(x.t0 - j) <= w for x in later["cod"]):
            nxt = "cod"
        elif any(x.actors == e.actors and 0 <= x.t0 - j <= w for x in later["burst"]):
            nxt = "burst"
        e.attrs["next"] = nxt
    return evs


def _dip_pairs(scene, c) -> list[dict]:
    """Brake then burst sharing the zig-zag trough with dwell <= gap_max_s (hesitation params), classified by
    the trough: change_of_pace (trough >= trough_min) or stop_and_go (below, and no stop fires inside)."""
    stops = detect_stop(scene)
    out = []
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        dv_min = _tv(c, "dv_min", f.tier)  # KIN-T07: q 10 attenuates a 2 m/s dip to about 1.1-1.7 m/s
        trough_min = _tv(c, "trough_min", f.tier)  # q 10 blur lifts a 0.1 s, 0.3 m/s trough to 1.0-1.6 m/s
        cb = {**_cfg("burst", {}), "dv_min": dv_min}
        ck = {**_cfg("brake", {}), "dv_min": dv_min}
        rises = {r["i"]: r for r in _velocity_changes(k, f, cb, 1.0)}
        tw = frames(c["trough_window_s"])
        # per-frame bias-corrected CA-RTS speed (the 0.5 s v_c window blurs a 0.1 s trough to about 1 m/s)
        vcf = np.sqrt(np.maximum(f.v**2 - 2.0 * f.sig**2, 0.0))
        for fl in _velocity_changes(k, f, ck, -1.0):
            ri = rises.get(fl["j"])
            if ri is None:
                continue
            dwell = (ri["t0"] - fl["t_end"]) * DT  # end of the slow-down to onset of the speed-up
            gap_max = _tv(c, "gap_max_s", f.tier)
            if not dwell <= gap_max:
                continue
            j = fl["j"]
            # trough on the bias-corrected speed around the zig-zag trough (the 0.2 s smoothed speed is
            # attenuated and reads a 0.3 m/s trough far too high)
            trough = _nanmin_masked(vcf, f.ok, j - tw, j + tw)
            if not np.isfinite(trough):
                continue
            p_trough = float(phi((trough - trough_min) / max(f.sL[j], 1e-6)))
            sub = "change_of_pace" if trough >= trough_min else "stop_and_go"
            if sub == "stop_and_go" and any(e.actors == {"player": oid} and fl["t0"] <= e.t0 <= ri["j"] for e in stops):
                continue  # stop + start label it
            # KIN2-HESI: the non-causal smoother leaks a 0.5 s fall early (the hinge onset led a 5 -> 3 -> 5
            # dip by 0.4-0.7 s at sigma_p 0.3-0.5); the brake that defines the dip lies within
            # onset_max_before_trough_s of its trough
            t0 = max(fl["t0"], j - frames(c["onset_max_before_trough_s"]))
            out.append(dict(oid=oid, f=f, fl=fl, ri=ri, j=j, t0=t0, dwell=dwell, gap_max=gap_max, trough=trough, sub=sub,
                            p_trough=p_trough, dv_min=dv_min, trough_min=trough_min,
                            p_brake=float(phi((fl["dv_1s"] - dv_min) / fl["sig_dv"])),
                            p_burst=float(phi((ri["dv_1s"] - dv_min) / ri["sig_dv"]))))
    return out


def _dip_events(scene, kind, want, c) -> list[Event]:
    out = []
    for d in _dip_pairs(scene, c):
        if d["sub"] != want:
            continue
        oid, fl, ri, f = d["oid"], d["fl"], d["ri"], d["f"]
        p_sub = d["p_trough"] if want == "change_of_pace" else 1.0 - d["p_trough"]
        pc = min(d["p_brake"], d["p_burst"]) * p_sub
        reasons = [f"brake {fl['dv_1s']:.2f} m/s and burst {ri['dv_1s']:.2f} m/s (each >= {d['dv_min']} m/s, tier {f.tier})",
                   f"dwell {d['dwell']:.2f} s <= {d['gap_max']} s",
                   f"min bias-corrected speed within +-{c['trough_window_s']} s of the trough {d['trough']:.2f} m/s "
                   f"{'>=' if want == 'change_of_pace' else '<'} {d['trough_min']} m/s -> {want}",
                   f"t0 = brake onset, no earlier than {c['onset_max_before_trough_s']} s before the trough"]
        has_ball = bool(np.any(scene.holder[fl["t0"]:ri["j"] + 1] == oid))
        attrs = dict(t_trough=d["j"], trough_speed=_r(d["trough"]), brake_dv=_r(fl["dv"]), burst_dv=_r(ri["dv"]),
                     dwell_s=_r(d["dwell"]), has_ball=has_ball, sub_type=want, noise_tier=f.tier, t0_hinge=fl["t0"])
        other = "stop_and_go" if want == "change_of_pace" else "hesitation"
        alts = {other: round(1 - p_sub, 2)} if 1 - p_sub >= 0.2 else {}
        ev = _event(scene, oid, kind, d["t0"], d["t0"], ri["j"], pc, c, attrs, reasons, alts)
        if ev:
            out.append(ev)
    return out


def detect_hesitation(scene, **params) -> list[Event]:
    """hesitation: brake then burst sharing the trough, dwell <= 0.6 s, trough bias-corrected speed >= 1.0 m/s
    (sub_type change_of_pace). A dip below that is the separate item stop_and_go (KIN2-HESI)."""
    return _dip_events(scene, "hesitation", "change_of_pace", _cfg("hesitation", params))


def detect_stop_and_go(scene, **params) -> list[Event]:
    """stop_and_go: the hesitation brake/burst pair whose trough is below trough_min while no stop fires
    (still phase under stop's 0.3 s); uses the hesitation params (KIN2-HESI)."""
    c = {**_cfg("hesitation", {}), **PARAMS["stop_and_go"], **params}
    return _dip_events(scene, "stop_and_go", "stop_and_go", c)


def detect_stop(scene, **params) -> list[Event]:
    """stop: stationary run (s2 gate) >= 0.3 s preceded within 1.2 s by speed_L >= 3.0 m/s; t0 = run start."""
    c = _cfg("stop", params)
    out = []
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        # KIN-T14: hard_stop is tested on a short (hard_smooth_s) mean of the CA-RTS speed, not on speed_L,
        # whose 0.5 s window falls below 4.0 m/s about 0.65 s before rest
        vh = np.where(f.ok, _mov_mean(np.where(f.ok, f.v, np.nan), _odd(c["hard_smooth_s"])), np.nan)
        sh = f.sig / math.sqrt(max(1.0, c["hard_smooth_s"] / f.corr))
        for a, b, _p_run, _v_run in _stationary_runs(f, c, c["still_min_s"], run_check=False):
            lo, hi = a - frames(c["fall_max_s"]), a - frames(c["pre_gap_s"])
            if lo < 0 or not f.ok[lo:hi + 1].any():
                continue
            vpre = np.where(f.ok[lo:hi + 1], f.vL[lo:hi + 1], np.nan)
            pre = float(np.nanmax(vpre)) if np.any(~np.isnan(vpre)) else float("nan")
            if not pre >= c["pre_min"]:
                continue
            fast = [t for t in range(lo, a) if f.vL[t] >= c["pre_min"]]
            t_fast = fast[-1]
            # fall time from the last frame at >= hard_pre to the first frame below hard_end_speed (independent
            # of the lag of the s2-gate t0 behind rest)
            hi_idx = [t for t in range(max(0, lo), a + 1) if vh[t] >= c["hard_pre"]]
            fall_t = None
            if hi_idx:
                t_lo = next((t for t in range(hi_idx[-1], b + 1) if vh[t] < c["hard_end_speed"]), None)
                fall_t = (t_lo - hi_idx[-1]) * DT if t_lo is not None else None
            hard_fall = _tv(c, "hard_fall_s", f.tier)  # q 10 smears the fall by about one smoother support
            hard = bool(fall_t is not None and fall_t <= hard_fall)
            near = max(0, a - frames(c["fall_max_s"]))
            v_hard = _nanmax(vh, near, a)
            ws = min(b, a + frames(c["still_min_s"]))
            wc = min(b, a + frames(c["conf_window_s"]))  # KIN2-STOP: stand evidence over the first conf_window_s
            sL = _nanmean(f.sL, lo, hi)
            pc = float(phi((pre - c["pre_min"]) / max(sL, 1e-6))) * mvlib.window_conf(f.p_stand, a, wc)
            dist = float(np.hypot(k.x[a] - k.x[t_fast], k.y[a] - k.y[t_fast]))
            reasons = [f"speed_L {pre:.2f} m/s >= {c['pre_min']} m/s within {c['fall_max_s']} s before",
                       f"stationary (s2 < {PARAMS['stand']['s2_enter']}) for {(b - a) * DT:.2f} s >= {c['still_min_s']} s",
                       f"hard: {c['hard_smooth_s']} s mean speed fell from >= {c['hard_pre']} to < {c['hard_end_speed']} m/s in "
                       f"{'n/a' if fall_t is None else f'{fall_t:.2f}'} s ({'<=' if hard else 'not <='} {hard_fall} s)"]
            attrs = dict(pre_speed=_r(pre), stop_time_s=_r((a - t_fast) * DT), stop_distance_m=_r(dist), x=_r(k.x[a]),
                         y=_r(k.y[a]), spot=_spot(k.x[a], k.y[a]), hard=hard, hard_speed=_r(v_hard), hard_fall_time_s=_r(fall_t), stop_type="unknown",
                         has_ball=bool(scene.holder[a] == oid))
            p_hard = float(phi((v_hard - c["hard_pre"]) / max(_nanmean(sh, near, a), 1e-6))) if np.isfinite(v_hard) else 0.0
            if fall_t is not None and fall_t > hard_fall:
                p_hard = 0.0  # fast enough before, but the fall itself was slow
            alts = {"hard_stop" if not hard else "soft_stop": round(p_hard if not hard else 1 - p_hard, 2)}
            alts = {kk: v for kk, v in alts.items() if v >= 0.2}
            ev = _event(scene, oid, "stop", a, a, ws, pc, c, attrs, reasons, alts)
            if ev:
                out.append(ev)
    return out


def detect_start(scene, **params) -> list[Event]:
    """start: after a >= 0.5 s stand, v_c >= 1.0 m/s for >= 0.3 s within 1.0 s of the gate exit; t0 is
    the change-point onset of the speed rise (KIN-T13), the s2 gate exit is kept as attrs.t0_gate."""
    c = _cfg("start", params)
    out = []
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        vs = np.where(f.ok, _mov_mean(np.where(f.ok, f.v, np.nan), _odd(c["refine_smooth_s"])), np.nan)
        for a, b, _p_run, _v_run in _stationary_runs(f, c, c["stand_min_s"], run_check=False):
            calm = [t for t in range(a, b + 1) if f.s2[t] < PARAMS["stand"]["s2_enter"]]
            t_gate = calm[-1] + 1
            hi = min(scene.n - 1, t_gate + frames(c["reach_window_s"]))
            if hi <= t_gate or not f.ok[t_gate:hi + 1].all():
                continue
            mv = np.nan_to_num(f.vc[t_gate:hi + 1], nan=0) >= c["move_speed"]
            runs = [(x, y) for x, y in _runs(mv) if (y - x) * DT >= c["move_min_s"] - 1e-9]
            if not runs:
                continue
            ra, rb = t_gate + runs[0][0], t_gate + runs[0][1]
            # change-point onset of the rise on the short mean speed over [gate exit - lookback, first frame
            # with that speed >= refine_end_speed (at most refine_end_max_s after the moving run starts)],
            # clamped to [t_gate - refine_max_lead_s, t_gate]
            lo = max(a, t_gate - frames(c["refine_lookback_s"]))
            r_end = min(scene.n - 1, ra + frames(c["refine_end_max_s"]))
            hi_fit = next((t for t in range(ra, r_end + 1) if vs[t] >= c["refine_end_speed"]), r_end)
            seg_ok = np.all(~np.isnan(vs[lo:hi_fit + 1]))
            t0 = _hinge_onset(vs, lo, hi_fit) if (hi_fit - lo >= 3 and seg_ok) else t_gate
            t0 = int(min(max(t0, t_gate - frames(c["refine_max_lead_s"]), a + 1), t_gate))
            p_move = mvlib.window_conf(phi((f.vc - c["move_speed"]) / np.maximum(f.sL, 1e-6)), ra, rb)
            pc = mvlib.window_conf(f.p_stand, a, max(a, t0 - 1)) * p_move
            reasons = [f"stand {(t0 - a) * DT:.2f} s >= {c['stand_min_s']} s before",
                       f"bias-corrected speed >= {c['move_speed']} m/s for {(rb - ra) * DT:.2f} s within {c['reach_window_s']} s",
                       f"t0 = change-point onset of the speed rise ({(t_gate - t0) * DT:.2f} s before the s2 gate exit)"]
            attrs = dict(stand_duration_s=_r((t0 - a) * DT), x=_r(k.x[t0]), y=_r(k.y[t0]), spot=_spot(k.x[t0], k.y[t0]),
                         peak_speed_1s=_r(_nanmax(f.vL, t0, hi)), has_ball=bool(scene.holder[t0] == oid), t0_gate=t_gate)
            ev = _event(scene, oid, "start", t0, t0, rb, pc, c, attrs, reasons)
            if ev:
                out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# Direction change (MP-13) and path shape
# --------------------------------------------------------------------------------------
def _cod_arrays(k, f, c) -> dict:
    """Per-frame pre/post mean velocities that skip the plant phase, dpsi and its sigma (MP-13)."""
    n_pre, n_gap = frames(_tv(c, "pre_s", f.tier)), frames(_tv(c, "gap_s", f.tier))  # KIN-T05: q 10 blur is wider
    L = n_pre - n_gap + 1  # frames in each window
    off = (n_pre + n_gap) // 2  # window centre offset from t
    vx = np.where(f.ok, k.vx, np.nan)
    vy = np.where(f.ok, k.vy, np.nan)
    mx, my = _mov_mean(vx, L, 1.0), _mov_mean(vy, L, 1.0)
    px, py, qx, qy = _shift(mx, off), _shift(my, off), _shift(mx, -off), _shift(my, -off)
    sp_pre, sp_post = np.hypot(px, py), np.hypot(qx, qy)
    cosang = (px * qx + py * qy) / np.maximum(sp_pre * sp_post, 1e-9)
    dpsi = np.degrees(np.arccos(np.clip(cosang, -1, 1)))
    cross = px * qy - py * qx
    dv = np.hypot(qx - px, qy - py)
    # window sigmas: mean of the per-frame sigma (k_cal and edge inflation included) over each window,
    # reduced for the window length in correlation times (MP-13)
    red = math.sqrt(max(1.0, L * DT / f.corr))
    ms = _mov_mean(f.sig, L, 1.0)
    sv_pre, sv_post = _shift(ms, off) / red, _shift(ms, -off) / red
    sig_vbar = np.sqrt((sv_pre**2 + sv_post**2) / 2.0)
    s_pre = sv_pre / np.maximum(sp_pre, 1e-6)
    s_post = sv_post / np.maximum(sp_post, 1e-6)
    sig_dpsi = np.degrees(np.sqrt(s_pre**2 + s_post**2))
    return dict(px=px, py=py, qx=qx, qy=qy, sp_pre=sp_pre, sp_post=sp_post, dpsi=dpsi, cross=cross, dv=dv,
                sig_vbar=sig_vbar, sv_pre=sv_pre, sv_post=sv_post, sig_dpsi=sig_dpsi)


def _cod_raw(k, f, c) -> list[dict]:
    """Firing runs of the MP-13 rule with the significance dv gate; one candidate (argmax dpsi) per run."""
    A = _cod_arrays(k, f, c)
    dv_thr = np.maximum(c["dv_abs_min"], c["z_dv"] * math.sqrt(2.0) * A["sig_vbar"])
    hz = PARAMS["kin_features"]["heading_z"]
    v_lo = np.minimum(np.nan_to_num(A["sp_pre"] - np.maximum(c["v_min"], hz * A["sv_pre"]), nan=-1),
                      np.nan_to_num(A["sp_post"] - np.maximum(c["v_min"], hz * A["sv_post"]), nan=-1))
    z_psi = np.nan_to_num(A["dpsi"] / np.maximum(A["sig_dpsi"], 1e-6))
    fire = (f.ok & (np.nan_to_num(A["dpsi"]) >= c["angle_min"])
            & (v_lo >= 0)  # both arms faster than max(v_min, 2.5 sigma): heading defined
            & (z_psi >= c["z_psi"])  # turn significant against zero (multiple-testing guard)
            & (np.nan_to_num(A["dv"]) >= dv_thr))
    out = []
    for a, b in _runs(fire):
        t0 = a + int(np.nanargmax(A["dpsi"][a:b + 1]))
        out.append(dict(t0=t0, a=a, b=b, **{key: A[key][t0] for key in A}))
    return out


def _class_probs(dpsi, s, c) -> dict:
    p45 = float(phi((dpsi - c["angle_min"]) / s))
    p90 = float(phi((dpsi - c["sharp"]) / s))
    p120 = float(phi((dpsi - c["reversal"]) / s))
    return {"angle": p45 - p90, "sharp": p90 - p120, "reversal": p120, "none": 1 - p45}


def _apex_turn(hd, t0: int, cc: dict) -> float:
    """|heading change| (deg) of the frame heading across +-arc_apex_half_s around t0 (NaN when undefined)."""
    h = frames(cc["arc_apex_half_s"])
    lo_, hi_ = max(0, t0 - h), min(len(hd) - 1, t0 + h)
    if not (np.isfinite(hd[lo_]) and np.isfinite(hd[hi_])):
        return float("nan")
    return abs(float(_wrap(hd[hi_] - hd[lo_])))


def _arc_covering(arcs, oid, t0):
    return [e for e in arcs if e.actors == {"player": oid} and e.start <= t0 <= e.end]


def detect_cod(scene, **params) -> list[Event]:
    """cod: MP-13 pre/post mean-velocity direction change >= 45 deg; classes angle / sharp / reversal."""
    c = _cfg("cod", params)
    arcs = detect_curved_run(scene) if c["suppress_in_arc"] else []
    out = []
    hz = PARAMS["kin_features"]["heading_z"]
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        hd = np.degrees(np.arctan2(k.vy, k.vx))
        for r in _cod_raw(k, f, c):
            t0, dpsi, s = r["t0"], float(r["dpsi"]), max(float(r["sig_dpsi"]), 1.0)
            cls = "reversal" if dpsi >= c["reversal"] else "sharp" if dpsi >= c["sharp"] else "angle"
            probs = _class_probs(dpsi, s, c)
            alts = {kk: round(v, 2) for kk, v in probs.items() if kk != cls and v >= 0.2}
            # KIN-T04: a uniform turn inside a curved_run is an arc, not a cut (the heading change within
            # +-arc_apex_half_s of the apex is under arc_uniform_ratio of the arc's total turn)
            path_shape = "cut"
            for arc in _arc_covering(arcs, oid, t0):
                apex = _apex_turn(hd, t0, c)
                total = abs(arc.attrs["dpsi_total_deg"] or 0.0)
                if np.isfinite(apex) and total > 0 and apex < c["arc_uniform_ratio"] * total:
                    path_shape = "arc"
                    break
                alts["curved_run"] = round(arc.conf, 2)
            if path_shape == "arc":
                continue
            # exit tags over [t0 + 0.2, t0 + 0.6] s
            e0, e1 = t0 + frames(c["exit_from_s"]), t0 + frames(c["exit_to_s"])
            exit_speed = _nanmean(f.v, e0, e1)
            vr = _nanmean(k.v_r, e0, e1)
            exit_rim = "toward" if vr >= c["rel_speed"] else "away" if vr <= -c["rel_speed"] else "neutral"
            exit_ball = "unknown"
            if scene.ball is not None:
                bx, by = scene.ball.x, scene.ball.y
                d = np.hypot(bx - k.x, by - k.y)
                vb = (k.vx * (bx - k.x) + k.vy * (by - k.y)) / np.where(d > 0, d, np.nan)
                m = _nanmean(vb, e0, e1)
                if np.isfinite(m):
                    exit_ball = "toward" if m >= c["rel_speed"] else "away" if m <= -c["rel_speed"] else "neutral"
            # turn duration from the frame-level heading (valid speed only)
            psi_pre = math.degrees(math.atan2(r["py"], r["px"]))
            psi_post = math.degrees(math.atan2(r["qy"], r["qx"]))
            spd = np.maximum(f.v, 1e-6)
            sp_ok = f.v >= max(c["v_min"], hz * float(r["sig_vbar"]))
            tol = np.maximum(c["turn_tol_deg"], 2 * np.degrees(f.sig / spd))
            w = frames(c["turn_search_s"])
            near_pre = [t for t in range(max(0, t0 - w), t0 + 1) if sp_ok[t] and abs(_wrap(hd[t] - psi_pre)) <= tol[t]]
            near_post = [t for t in range(t0, min(scene.n, t0 + w + 1)) if sp_ok[t] and abs(_wrap(hd[t] - psi_post)) <= tol[t]]
            turn_dur = (near_post[0] - near_pre[-1]) * DT if near_pre and near_post else None
            # KIN-T05: the turn is only meaningful if both arms are truly moving; P(min arm speed > v_min)
            arm = min(float(r["sp_pre"]), float(r["sp_post"]))
            p_speed = float(phi((arm - c["v_min"]) / max(float(r["sig_vbar"]), 1e-6)))
            pc = (probs["angle"] + probs["sharp"] + probs["reversal"]) * p_speed
            gap = _tv(c, "gap_s", f.tier)
            win = _tv(c, "pre_s", f.tier) - gap
            reasons = [f"dpsi {dpsi:.1f} deg >= {c['angle_min']} deg (pre/post {win:.2f} s windows skipping +-{gap} s)",
                       f"min(|pre|, |post|) {arm:.2f} m/s >= {c['v_min']} m/s (P {p_speed:.2f})",
                       f"|post - pre| {r['dv']:.2f} m/s >= max({c['dv_abs_min']}, {c['z_dv']} sqrt2 sigma_vbar)"]
            # KIN-T01: the named-spot frame is mirrored (x = attacker's right while facing -y), so a positive
            # pre x post cross product is a physical RIGHT turn
            attrs = dict(dpsi_deg=_r(dpsi, 1), cod_class=cls, P_class={kk: round(v, 3) for kk, v in probs.items()},
                         reversal_alt_135=bool(dpsi >= c["reversal_alt"]), side="right" if r["cross"] > 0 else "left",
                         entry_speed=_r(r["sp_pre"]), exit_speed=_r(r["sp_post"]), turn_duration_s=_r(turn_dur),
                         hard_cut=bool(exit_speed >= c["hard_cut_speed"]), exit_rim=exit_rim, exit_ball=exit_ball,
                         x=_r(k.x[t0]), y=_r(k.y[t0]), spot=_spot(k.x[t0], k.y[t0]), sigma_dpsi_deg=_r(s, 1),
                         has_ball=bool(scene.holder[t0] == oid), path_shape=path_shape, noise_tier=f.tier)
            ev = _event(scene, oid, "cod", t0, t0 - frames(_tv(c, "pre_s", f.tier)), t0 + frames(_tv(c, "pre_s", f.tier)),
                        pc, c, attrs, reasons, alts)
            if ev:
                out.append(ev)
    return _nms(out, c["nms_s"])


def _plant_test(f: _F, t0: int, c: dict) -> dict | None:
    """Plant drop test around a turn apex t0 (plant_step params): approach speed over
    [t0 - approach_from_s, t0 - approach_to_s] (KIN-T06: before the braking phase), quadratic-fit speed
    minimum in [t0 - search_before_s, t0 + search_after_s], drop >= max(drop_abs, drop_frac x approach,
    drop_z x sigma_fit)."""
    n = len(f.v)
    v_ok = np.where(f.ok, f.v, np.nan)
    a0, a1 = t0 - frames(c["approach_from_s"]), t0 - frames(c["approach_to_s"])
    if a0 < 0:
        return None
    entry = _nanmean(v_ok, a0, a1)
    lo, hi = max(t0 - frames(c["search_before_s"]), 0), min(t0 + frames(c["search_after_s"]), n - 1)
    seg = v_ok[lo:hi + 1]
    if not np.isfinite(entry) or np.all(np.isnan(seg)):
        return None
    tm = lo + int(np.nanargmin(seg))
    h = int(c["fit_frames"]) // 2
    ts = np.arange(max(0, tm - h), min(n, tm + h + 1))
    ys = f.v[ts]
    good = ~np.isnan(ys)
    if good.sum() < 5:
        return None
    A2, A1, A0 = np.polyfit(ts[good] - tm, ys[good], 2)
    if A2 > 0 and abs(-A1 / (2 * A2)) <= h:
        tv = -A1 / (2 * A2)
        vmin = A0 - A1 * A1 / (4 * A2)
    else:
        tv, vmin = 0.0, A0
    vmin = max(float(vmin), 0.0)
    sig_fit = float(f.sig[tm])  # 9 frames = 0.3 s: one correlation time, no reduction
    drop = entry - vmin
    thr = max(c["drop_abs"], _tv(c, "drop_frac", f.tier) * entry, c["drop_z"] * sig_fit)  # KIN2-PLANT: tiered
    sig_entry = _nanmean(f.sig, a0, a1) / math.sqrt(max(1.0, (c["approach_from_s"] - c["approach_to_s"]) / f.corr))
    p_drop = float(phi((drop - thr) / math.sqrt(sig_entry**2 + sig_fit**2)))
    return dict(entry=entry, vmin=vmin, tp=int(round(tm + tv)), drop=drop, thr=thr, p_drop=p_drop, sig_fit=sig_fit, h=h)


def detect_plant_step(scene, **params) -> list[Event]:
    """plant_step: fitted speed minimum before a cod >= 60 deg with approach >= 2.5 m/s and a noise-scaled drop."""
    c = _cfg("plant_step", params)
    out = []
    for e in detect_cod(scene):
        oid = e.actors["player"]
        k = scene.k(oid)
        f = _F(k, c)
        if not e.attrs["dpsi_deg"] >= c["angle_min"]:
            continue
        pt = _plant_test(f, e.t0, c)
        if pt is None or not pt["entry"] >= c["entry_min"]:
            continue
        entry, vmin, tp, h, sig_fit = pt["entry"], pt["vmin"], pt["tp"], pt["h"], pt["sig_fit"]
        vc = math.sqrt(max(vmin**2 - 2 * sig_fit**2, 0.0))
        reasons = [f"cod {e.attrs['dpsi_deg']} deg >= {c['angle_min']} deg, approach {entry:.2f} m/s >= {c['entry_min']} m/s "
                   f"(mean speed over [t0 - {c['approach_from_s']}, t0 - {c['approach_to_s']}] s)",
                   f"speed drop {pt['drop']:.2f} m/s >= max({c['drop_abs']}, {c['drop_frac']} approach, {c['drop_z']} sigma_fit) = {pt['thr']:.2f} m/s"]
        attrs = dict(entry_speed=_r(entry), plant_speed=_r(vmin), plant_ratio=_r(vmin / entry), plant_ratio_corrected=_r(vc / entry),
                     drop=_r(pt["drop"]), turn_side=e.attrs["side"], cod_t0=e.t0, plant_foot="unknown",
                     x=_r(k.x[tp]), y=_r(k.y[tp]), spot=_spot(k.x[tp], k.y[tp]))
        ev = _event(scene, oid, "plant_step", tp, tp - h, tp + h, pt["p_drop"], c, attrs, reasons)
        if ev:
            ev.conf = min(ev.conf, e.conf)
            if ev.conf >= c["emit_min"]:
                out.append(ev)
    return out


def _kasa(x, y):
    """Algebraic least-squares circle fit -> (cx, cy, R) or Nones."""
    m = ~(np.isnan(x) | np.isnan(y))
    x, y = x[m], y[m]
    if len(x) < 5:
        return None, None, None
    A = np.column_stack([x, y, np.ones_like(x)])
    bb = x**2 + y**2
    sol, *_ = np.linalg.lstsq(A, bb, rcond=None)
    cx, cy = sol[0] / 2, sol[1] / 2
    R = math.sqrt(max(sol[2] + cx * cx + cy * cy, 0.0))
    return cx, cy, R


def detect_curved_run(scene, **params) -> list[Event]:
    """curved_run: geometric chord curvature >= 0.15 1/m with sigma_kappa, z gate, no cod inside."""
    c = _cfg("curved_run", params)
    cc = _cfg("cod", {})
    # KIN2-PLANT: the arc's plant exclusion asks 'is there a plant at all', so it keeps its own drop fraction
    # (plant_step's emission edge was raised to drop the shallow 65 deg cut, which must not re-admit planted cuts as arcs)
    cp = {**_cfg("plant_step", {}), "drop_frac": c["plant_exclusion_drop_frac"], "drop_frac_q10": c["plant_exclusion_drop_frac"]}
    out = []
    W, w = frames(c["arm_s"]), _odd(c["end_w_s"])
    off = W - w // 2
    for oid in scene.players():
        k = scene.k(oid)
        f = _F(k, c)
        vx, vy = np.where(f.ok, k.vx, np.nan), np.where(f.ok, k.vy, np.nan)
        hd = np.degrees(np.arctan2(k.vy, k.vx))
        mx, my = _mov_mean(vx, w, 1.0), _mov_mean(vy, w, 1.0)
        ix, iy, ox, oy = _shift(mx, off), _shift(my, off), _shift(mx, -off), _shift(my, -off)
        dpsi = np.arctan2(ix * oy - iy * ox, ix * ox + iy * oy)  # signed, rad
        cs = np.concatenate([[0.0], np.cumsum(np.nan_to_num(f.v) * DT)])
        idx = np.arange(scene.n)
        path = np.full(scene.n, np.nan)
        okp = (idx - off >= 0) & (idx + off < scene.n)
        path[okp] = cs[idx[okp] + off + 1] - cs[idx[okp] - off]
        kappa = dpsi / np.where(path > 0, path, np.nan)
        sig_vbar = f.sig / math.sqrt(max(1.0, w * DT / f.corr))
        s_dpsi = np.sqrt((sig_vbar / np.maximum(np.hypot(ix, iy), 1e-6)) ** 2 + (sig_vbar / np.maximum(np.hypot(ox, oy), 1e-6)) ** 2)
        s_kap = s_dpsi / np.where(path > 0, path, np.nan)
        z = np.abs(dpsi) / np.maximum(s_dpsi, 1e-6)
        fast = f.ok & (np.nan_to_num(f.vL) >= c["speed_min"])
        n_fast = np.concatenate([[0], np.cumsum(fast)])
        all_fast = np.zeros(scene.n, dtype=bool)
        okw = (idx - W >= 0) & (idx + W < scene.n)
        all_fast[okw] = (n_fast[idx[okw] + W + 1] - n_fast[idx[okw] - W]) == 2 * W + 1
        cod_dpsi = _cod_arrays(k, f, cc)["dpsi"]
        cod_raw = _cod_raw(k, f, cc) if c["plant_exclusion"] else []
        # KIN-T01: mirrored frame, positive signed dpsi (CCW in x/y) is a physical RIGHT turn
        for side, sgn in (("right", 1.0), ("left", -1.0)):
            P = phi((sgn * kappa - c["kappa_min"]) / np.maximum(s_kap, 1e-6))
            P = np.where(np.isnan(kappa), 0.0, P)
            enter = all_fast & (P >= c["p_enter"]) & (z >= c["z_enter"])
            stay = all_fast & (P >= c["p_stay"]) & (z >= c["z_stay"])
            for a, b in mvlib.hysteresis(enter, stay, c["min_s"]):
                t0 = a
                while t0 - 1 >= 0 and all_fast[t0 - 1] and P[t0 - 1] >= c["p_backdate"]:
                    t0 -= 1
                arc_path = float(cs[min(scene.n, b + off + 1)] - cs[max(0, t0 - off)])
                if arc_path < c["path_min"]:
                    continue
                max_cod = float(np.nanmax(cod_dpsi[t0:b + 1])) if np.any(~np.isnan(cod_dpsi[t0:b + 1])) else 0.0
                inside = [r for r in cod_raw if t0 <= r["t0"] <= b]
                if c["plant_exclusion"]:
                    # KIN-T04: drop the arc only when a cod inside it shows a plant (approach-to-minimum drop)
                    planted = [r for r in inside if (pt := _plant_test(f, r["t0"], cp)) is not None
                               and pt["p_drop"] >= c["plant_exclusion_p"]]
                    if planted:
                        continue  # a planted cut, not an arc (cod and plant_step report it)
                    # KIN2-CURVE: the apex test detect_cod uses, from the arc side: a cod inside whose heading change
                    # within +-arc_apex_half_s is >= cut_apex_ratio of the arc's total turn is a cut (detect_cod emits
                    # it), so the arc is not emitted for it. Between cod.arc_uniform_ratio and cut_apex_ratio both
                    # are emitted and the cod carries alternative curved_run.
                    tot_abs = abs(float(np.degrees(np.arctan2(ix[t0] * oy[b] - iy[t0] * ox[b], ix[t0] * ox[b] + iy[t0] * oy[b]))))
                    if c["cut_apex_exclusion"] and tot_abs > 0 and any(
                            float(r["dpsi"]) >= cc["angle_min"] and _apex_turn(hd, r["t0"], cc) >= c["cut_apex_ratio"] * tot_abs
                            for r in inside):
                        continue
                elif max_cod >= c["cod_exclude_deg"]:
                    continue
                lo, hi = max(0, t0 - off), min(scene.n - 1, b + off)
                cx, cy, R = _kasa(k.x[lo:hi + 1], k.y[lo:hi + 1])
                around_tm, around_rim = None, False
                if cx is not None:
                    around_rim = bool(math.hypot(cx, cy) <= c["around_rim_r"])
                    team = scene.offense if oid in scene.offense else scene.defense
                    for tm in team:
                        if tm == oid:
                            continue
                        kt = scene.k(tm)
                        ft = _F(kt, c)
                        d = math.hypot(_nanmean(kt.x, t0, b) - cx, _nanmean(kt.y, t0, b) - cy)
                        if d <= c["around_teammate_r"] and mvlib.window_conf(ft.p_stand, t0, b) >= c["around_stand_p"]:
                            around_tm = tm
                pc = mvlib.window_conf(P, t0, b)
                # total heading change from the first entry window to the last exit window
                total = float(np.degrees(np.arctan2(ix[t0] * oy[b] - iy[t0] * ox[b], ix[t0] * ox[b] + iy[t0] * oy[b])))
                reasons = [f"chord curvature {np.nanmean(np.abs(kappa[t0:b + 1])):.3f} 1/m >= {c['kappa_min']} 1/m with z >= {c['z_enter']}",
                           f"speed_L >= {c['speed_min']} m/s, arc path {arc_path:.1f} m >= {c['path_min']} m",
                           (f"no planted cod inside (max MP-13 dpsi {max_cod:.0f} deg)" if c["plant_exclusion"]
                            else f"max MP-13 dpsi {max_cod:.0f} deg < {c['cod_exclude_deg']} deg")]
                alts = {}
                for r in inside:  # unplanted cods inside the arc are alternatives
                    cls_p = _class_probs(float(r["dpsi"]), max(float(r["sig_dpsi"]), 1.0), cc)
                    for kk in ("angle", "sharp", "reversal"):
                        if cls_p[kk] >= 0.2:
                            alts["cod_" + kk] = max(alts.get("cod_" + kk, 0.0), round(cls_p[kk], 2))
                if not inside and max_cod >= cc["angle_min"] - c["alt_margin_deg"]:
                    alts["cod_angle"] = round(float(phi((max_cod - cc["angle_min"]) / c["alt_sigma_deg"])), 2)
                attrs = dict(side=side, mean_kappa=_r(float(np.nanmean(np.abs(kappa[t0:b + 1]))), 3), radius_m=_r(R),
                             centre_x=_r(cx), centre_y=_r(cy), dpsi_total_deg=_r(total, 1), path_m=_r(arc_path),
                             mean_speed=_r(_nanmean(f.vL, t0, b)), around_teammate=around_tm, around_rim=around_rim)
                ev = _event(scene, oid, "curved_run", t0, t0, b, pc, c, attrs, reasons, alts, state=True)
                if ev:
                    out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# Direction classes with the XY facing proxy
# --------------------------------------------------------------------------------------
def _facing(scene, oid) -> tuple[np.ndarray, str]:
    """XY facing proxy phi_hat (deg): defenders face the ball, else the nearest attacker; offense = heading."""
    k = scene.k(oid)
    n = scene.n
    if oid in scene.offense:
        return np.degrees(np.arctan2(k.vy, k.vx)), "default_forward"
    phi_hat = np.full(n, np.nan)
    if scene.ball is not None:
        phi_hat = np.degrees(np.arctan2(scene.ball.y - k.y, scene.ball.x - k.x))
    miss = np.isnan(phi_hat)
    if miss.any() and scene.offense:
        best = np.full(n, np.inf)
        alt = np.full(n, np.nan)
        for o in scene.offense:
            ko = scene.k(o)
            d = np.nan_to_num(np.hypot(ko.x - k.x, ko.y - k.y), nan=np.inf)
            m = d < best
            best[m] = d[m]
            alt[m] = np.degrees(np.arctan2(ko.y - k.y, ko.x - k.x))[m]
        phi_hat[miss] = alt[miss]
    return phi_hat, "xy_proxy_ball_or_man"


def _direction(scene, oid, c) -> dict:
    """Per-frame |d|, class probabilities and moving probability from the 0.3 s mean velocity."""
    k = scene.k(oid)
    f = _F(k, c)
    w = _odd(c["dir_window_s"])
    vx, vy = _mov_mean(np.where(f.ok, k.vx, np.nan), w, 1.0), _mov_mean(np.where(f.ok, k.vy, np.nan), w, 1.0)
    vbar = np.hypot(vx, vy)
    sig_vbar = f.sig / math.sqrt(max(1.0, w * DT / f.corr))
    psi = np.degrees(np.arctan2(vy, vx))
    fac, src = _facing(scene, oid)
    absd = np.abs(_wrap(psi - fac))
    s_psi = np.degrees(sig_vbar / np.maximum(vbar, 1e-6))
    s_d = np.sqrt(s_psi**2 + (c["facing_sigma_deg"] if src != "default_forward" else 0.0) ** 2)
    s_d = np.maximum(s_d, 1.0)
    # KIN-T12: class edges from the YAML (forward_run.edge_deg, backpedal.edge_deg)
    p_fwd = phi((PARAMS["forward_run"]["edge_deg"] - absd) / s_d)
    p_back = phi((absd - PARAMS["backpedal"]["edge_deg"]) / s_d)
    p_lat = np.clip(1.0 - p_fwd - p_back, 0.0, 1.0)
    # KIN-T11: moving gate on the bias-corrected mean speed (Rician floor of the 0.3 s mean removed)
    vbar_c = np.sqrt(np.maximum(vbar**2 - 2.0 * sig_vbar**2, 0.0))
    vmin = np.maximum(c["speed_min"], PARAMS["kin_features"]["heading_z"] * sig_vbar)
    moving = f.ok & (np.nan_to_num(vbar_c) >= vmin) & ~np.isnan(absd)
    p_mov = phi((vbar_c - c["speed_min"]) / np.maximum(sig_vbar, 1e-6))
    # KIN-T11: a lateral class needs coupling to the ball (or, when the ball is unobserved, the nearest
    # attacker): its velocity along the defender's motion >= couple_speed, or distance <= on_ball_r.
    # Offense has no facing proxy (heading = facing), so coupling is moot there.
    coupled = np.ones(scene.n, dtype=bool)
    if src != "default_forward":
        cp = PARAMS["kin_features"]
        ux, uy = vx / np.maximum(vbar, 1e-6), vy / np.maximum(vbar, 1e-6)
        rx, ry, rvx, rvy = (np.full(scene.n, np.nan) for _ in range(4))
        if scene.ball is not None:
            b = scene.ball
            rx, ry, rvx, rvy = b.x.copy(), b.y.copy(), b.vx.copy(), b.vy.copy()
        miss = np.isnan(rx)
        if miss.any() and scene.offense:
            best = np.full(scene.n, np.inf)
            for o in scene.offense:
                ko = scene.k(o)
                d = np.nan_to_num(np.hypot(ko.x - k.x, ko.y - k.y), nan=np.inf)
                m = miss & (d < best)
                best[m] = d[m]
                rx[m], ry[m], rvx[m], rvy[m] = ko.x[m], ko.y[m], ko.vx[m], ko.vy[m]
        dist = np.hypot(rx - k.x, ry - k.y)
        along = rvx * ux + rvy * uy
        coupled = (np.nan_to_num(along, nan=-99.0) >= cp["couple_speed"]) | (np.nan_to_num(dist, nan=99.0) <= cp["on_ball_r"])
    return dict(k=k, f=f, absd=np.nan_to_num(absd, nan=-1.0), vbar=np.nan_to_num(vbar), p_fwd=p_fwd, p_back=p_back,
                p_lat=p_lat, p_mov=p_mov, moving=moving, src=src, sig_vbar=sig_vbar, coupled=coupled)


def _class_events(scene, oid, kind, D, enter, stay, p_class, c, cap, extra=None) -> list[Event]:
    f = D["f"]
    out = []
    for a, b in mvlib.hysteresis(enter, stay, c["min_s"]):
        pc = mvlib.window_conf(np.where(D["moving"], p_class * D["p_mov"], 0.0), a, b)
        attrs = dict(mean_abs_d=_r(float(np.mean(D["absd"][a:b + 1])), 1), mean_speed=_r(float(np.mean(D["vbar"][a:b + 1]))),
                     peak_speed=_r(float(np.max(D["vbar"][a:b + 1]))), distance_m=_r(float(np.nansum(f.v[a:b + 1]) * DT)),
                     facing_source=D["src"], duration_s=_r((b - a) * DT))
        alts = {}
        for name, arr in (("forward", D["p_fwd"]), ("lateral", D["p_lat"]), ("backward", D["p_back"])):
            m = float(np.nanmean(arr[a:b + 1]))
            if m >= 0.2 and name not in kind:
                alts[name] = round(m, 2)
        reasons = [f"direction class held {(b - a) * DT:.2f} s >= {c['min_s']} s (|d| = |heading - facing|, facing {D['src']})",
                   f"mean speed {attrs['mean_speed']} m/s >= max({c['speed_min']} m/s, 2.5 sigma_vbar)"]
        if kind in ("defensive_slide", "crossover_run"):
            attrs["ball_coupled_share"] = _r(float(np.mean(D["coupled"][a:b + 1])))
        if extra:
            attrs.update(extra(a, b))
        ev = _event(scene, oid, kind, a, a, b, pc, c, attrs, reasons, alts, cap=cap, state=True)
        if ev:
            out.append(ev)
    return out


def detect_forward_run(scene, **params) -> list[Event]:
    """forward_run (defenders, XY proxy): |d| <= 40 (stay 50) deg for >= 0.4 s, plus uncoupled lateral
    motion (rotation_run, KIN-T11). Offense is not emitted until pose exists (offense_emit, KIN-T15)."""
    c = _cfg("forward_run", params)
    out = []
    for oid in scene.players():
        D = _direction(scene, oid, c)
        if D["src"] == "default_forward" and not c["offense_emit"]:
            continue  # heading = facing for offense: forward by construction, carries no information
        lat_lo, lat_hi = PARAMS["defensive_slide"]["lat_stay_lo"], PARAMS["defensive_slide"]["lat_stay_hi"]
        rot = D["moving"] & ~D["coupled"] & (D["absd"] >= lat_lo) & (D["absd"] <= lat_hi)
        enter = (D["moving"] & (D["absd"] >= 0) & (D["absd"] <= c["enter_deg"])) | rot
        stay = (D["moving"] & (D["absd"] >= 0) & (D["absd"] <= c["stay_deg"])) | rot
        p_class = D["p_fwd"] + np.where(D["coupled"], 0.0, D["p_lat"])
        cap = c["offense_default_cap"] if D["src"] == "default_forward" else c["facing_cap_proxy"]

        def extra(a, b, rot=rot):
            share = float(np.mean(rot[a:b + 1]))
            return dict(rotation_share=_r(share), sub_type="rotation_run" if share >= 0.5 else "forward")
        evs = _class_events(scene, oid, "forward_run", D, enter, stay, p_class, c, cap, extra)
        for e in evs:
            if e.attrs["rotation_share"] and e.attrs["rotation_share"] >= 0.2:
                e.attrs["alternatives"]["rotation_run"] = e.attrs["rotation_share"]
        out += evs
    return out


def detect_backpedal(scene, **params) -> list[Event]:
    """backpedal (defenders, XY proxy): |d| >= 140 (stay 130) deg, 0.8-5.0 m/s, >= 0.4 s."""
    c = _cfg("backpedal", params)
    out = []
    for oid in scene.defense:
        D = _direction(scene, oid, c)
        k = D["k"]
        inc = D["moving"] & (D["vbar"] <= c["speed_cap"])
        enter = inc & (D["absd"] >= c["enter_deg"])
        stay = inc & (D["absd"] >= c["stay_deg"])

        def extra(a, b, k=k):
            vr = _nanmean(k.v_r, a, b)  # positive = toward the rim the defence protects
            bd = _nanmean(np.hypot(scene.ball.x - k.x, scene.ball.y - k.y), a, b) if scene.ball is not None else float("nan")
            return dict(toward_rim_speed=_r(vr), transition=bool(vr >= c["retreat_speed"]), ball_distance=_r(bd))
        out += _class_events(scene, oid, "backpedal", D, enter, stay, D["p_back"], c, c["facing_cap_proxy"], extra)
    return out


def detect_defensive_slide(scene, **params) -> list[Event]:
    """defensive_slide (defenders, XY proxy): lateral 50-130 (stay 45-135) deg at 0.8-3.0 m/s for >= 0.4 s."""
    c = _cfg("defensive_slide", params)
    out = []
    for oid in scene.defense:
        D = _direction(scene, oid, c)
        d, v = D["absd"], D["vbar"]
        cpl = D["coupled"]
        enter = D["moving"] & cpl & (d >= c["lat_enter_lo"]) & (d <= c["lat_enter_hi"]) & (v <= c["speed_max"])
        stay = D["moving"] & cpl & (d >= c["lat_stay_lo"]) & (d <= c["lat_stay_hi"]) & (v <= c["speed_max_stay"])
        p_slow = phi((c["speed_max"] - v) / np.maximum(D["sig_vbar"], 1e-6))

        def extra(a, b, D=D):
            k = D["k"]
            mean_v = float(np.mean(D["vbar"][a:b + 1]))
            vb = "unknown"
            if scene.ball is not None:
                d0 = _nanmean(np.hypot(scene.ball.x - k.x, scene.ball.y - k.y), a, a + 3)
                d1 = _nanmean(np.hypot(scene.ball.x - k.x, scene.ball.y - k.y), b - 3, b)
                tol = c["ball_dist_tol_m"]
                vb = "toward_ball" if d1 < d0 - tol else "away_from_ball" if d1 > d0 + tol else "with_ball"
            return dict(sub_band="slide_low" if mean_v < c["low_high_split"] else "slide_high", direction_vs_ball=vb)
        evs = _class_events(scene, oid, "defensive_slide", D, enter, stay, D["p_lat"] * p_slow * cpl, c, c["facing_cap_proxy"], extra)
        if evs and c["xover_ramp_max_s"] > 0:
            # KIN2-DSLIDE: a defender who opens into a crossover run passes through slide speeds while he
            # accelerates (and again while he slows out of it); a short slide segment touching a crossover_run
            # segment of the same player is that ramp, not a slide. A longer slide phase before the opening
            # stays (crossover_run.preceded_by_slide).
            xo = _crossover_core(scene, oid, _cfg("crossover_run", {}))
            gap, rmax = frames(c["xover_ramp_gap_s"]), frames(c["xover_ramp_max_s"])
            evs = [e for e in evs if not (e.end - e.start <= rmax and any(
                e.start - gap <= x.end and x.start <= e.end + gap for x in xo))]
        out += evs
    return out


def _crossover_core(scene, oid, c, extra=None) -> list[Event]:
    """crossover_run segments of one defender (no slide context)."""
    D = _direction(scene, oid, c)
    d, v = D["absd"], D["vbar"]
    cpl = D["coupled"]
    enter = D["moving"] & cpl & (d >= c["lat_enter_lo"]) & (d <= c["lat_enter_hi"]) & (v >= c["speed_enter"])
    stay = D["moving"] & cpl & (d >= c["lat_stay_lo"]) & (d <= c["lat_stay_hi"]) & (v >= c["speed_stay"])
    p_fast = phi((v - c["speed_enter"]) / np.maximum(D["sig_vbar"], 1e-6))
    return _class_events(scene, oid, "crossover_run", D, enter, stay, D["p_lat"] * p_fast * cpl, c, c["facing_cap_proxy"], extra)


def detect_crossover_run(scene, **params) -> list[Event]:
    """crossover_run (defenders, XY proxy): lateral class at >= 3.0 m/s (stay 2.7) for >= 0.4 s."""
    c = _cfg("crossover_run", params)
    slides = detect_defensive_slide(scene)
    out = []
    for oid in scene.defense:
        mine = [s for s in slides if s.actors["player"] == oid]

        def extra(a, b, mine=mine):
            pre = [s for s in mine if 0 <= (a - s.end) * DT <= c["preceded_gap_s"]]
            return dict(preceded_by_slide=bool(pre))
        out += _crossover_core(scene, oid, c, extra)
    return out


# --------------------------------------------------------------------------------------
# Vertical proxies and pose-only items
# --------------------------------------------------------------------------------------
def _scene_tier(scene) -> str:
    """KIN5-BRIDGE: noise tier of a scene = majority tier of its players (ties -> q30). Cached per scene."""
    cached = getattr(scene, "_kin_tier", None)
    if cached is not None:
        return cached
    tiers = [_tier(scene.k(o)) for o in scene.players()]
    tier = "q10" if tiers and 2 * sum(t == "q10" for t in tiers) > len(tiers) else "q30"
    try:
        scene._kin_tier = tier
    except AttributeError:
        pass
    return tier


def _ball_control(scene, c) -> tuple[list, np.ndarray]:
    """KIN4-JUMP: sustained ball control by ANY player (either team), for the release proxy only.

    ctl[t] = the nearest player to the raw ball when within mvlib.HOLD_R; a run of the same ctl counts as control only
    when it lasts >= control_min_s and the ball moves with the player: the chord relative speed |mean offset (ball -
    player) over the last control_end_s - mean over the first| / run duration <= control_rel_v, after removing
    control_noise_z sigma of chord noise; gaps of control_bridge_s inside a run are bridged. A shot in flight passes
    over defenders and over players under the rim for 0.1-0.35 s (real tracking) at 3-8 m/s relative speed, which the
    one-frame offence-only mvlib holder read as a catch. Returns (players, sus) with sus[t] = player index or -1."""
    # KIN5-BRIDGE: the bridge is noise-tier aware (control_bridge_s_q10 at the q 10 tier: a noisier held ball leaves
    # the 1 m disc for longer and fragments the control run)
    bridge = _tv(c, "control_bridge_s", _scene_tier(scene))
    key = (c["control_min_s"], c["control_rel_v"], c["control_end_s"], bridge, c["control_noise_z"], c["control_tail_min_s"])
    cached = getattr(scene, "_kin_ctl", None)
    if cached is not None and cached[0] == key:
        return cached[1], cached[2]
    pl = scene.players()
    n = scene.n
    sus = np.full(n, -1)
    if scene.ball_raw is not None and pl:
        bx, by = scene.ball_raw
        D = np.array([np.hypot(bx - scene.k(o).x, by - scene.k(o).y) for o in pl])
        D = np.where(np.isnan(D), np.inf, D)
        j = np.argmin(D, axis=0)
        ctl = np.where(D[j, np.arange(n)] <= mvlib.HOLD_R, j, -1)
        w = max(1, frames(c["control_end_s"]))
        mn = frames(c["control_min_s"])
        sb = np.sqrt(np.nan_to_num(scene.ball.var_p, nan=0.0)) if scene.ball is not None else np.zeros(n)
        runs = []
        for i in range(len(pl)):
            # runs of player i, bridging gaps <= control_bridge_s (a noisy ball steps out of the 1 m disc for a frame
            # or two while held; a released ball does not come back)
            m = ctl == i
            for a, b in mvlib.hysteresis(m, m, 0.0, frames(bridge)):
                # KIN5-BRIDGE: a bridged run ends at its last in-disc stretch of >= control_tail_min_s; a released ball
                # that noise dips back into the disc for a frame after a gap (a runner following his floater) does not
                # extend the control
                tail = max(1, frames(c["control_tail_min_s"]))
                while True:
                    e = b
                    while e - 1 >= a and m[e - 1]:
                        e -= 1
                    if b - e + 1 >= tail or e == a:
                        break
                    b = e - 1
                    while b > a and not m[b]:
                        b -= 1
                if b - a + 1 < max(mn, 2 * w):
                    continue
                k = scene.k(pl[i])
                ox, oy = bx - k.x, by - k.y
                d = math.hypot(_nanmean(ox, b - w + 1, b) - _nanmean(ox, a, a + w - 1),
                               _nanmean(oy, b - w + 1, b) - _nanmean(oy, a, a + w - 1))
                # noise allowance: the end-window means of the raw ball differ by ~ sqrt(2 / w) sigma_ball per axis
                allow = c["control_noise_z"] * math.sqrt(2.0) * math.sqrt(2.0 / w) * _nanmean(sb, a, b)
                if np.isfinite(d) and max(d - allow, 0.0) / max((b - a + 1 - w) * DT, DT) <= c["control_rel_v"]:
                    runs.append((a, b, i))
        for a, b, i in sorted(runs):
            sus[a:b + 1] = i
    try:
        scene._kin_ctl = (key, pl, sus)
    except AttributeError:
        pass
    return pl, sus


def _rims(c) -> dict:
    """Both rims in the attacked-rim frame: the attacked one at the origin and the far one court_length - 2 x
    rim_setback up the court (KIN4-JUMP: SportVU stretches hold possessions of both teams)."""
    return {"attacked": (0.0, 0.0), "far": (0.0, c["court_length_m"] - 2.0 * c["rim_setback_m"])}


def _to_shot_frame(x, y, rim: str, c: dict) -> tuple[float, float]:
    """Attacked-rim frame -> frame of the rim that was shot at (far rim: the court rotated by 180 deg)."""
    if rim == "far":
        return -x, _rims(c)["far"][1] - y
    return x, y


def _oob_excess(x, y) -> float:
    """Distance (m) beyond the named_spots in-bounds gate (|x| < SIDE_X, END_Y < y < FAR_END_Y; spotlib.C), <= 0 inside."""
    C = spotlib.C
    return float(max(abs(x) - C["SIDE_X"], C["END_Y"] - y, y - C["FAR_END_Y"]))


def _releases(scene, c) -> list[dict]:
    """Shot-like releases (KIN-T02, KIN4-JUMP): a player of either team ends a sustained control run, the ball reaches
    the rim area of either rim before anyone gains sustained control, it flew toward that rim, was released at least
    release_min_r from it, and does not pass through it; KIN5-OOB: the shooter stands in bounds (shot-rim frame).
    KIN5-BALLZ (optional, ball_z_path and Scene.ball_z present): the flight apex must reach z_apex_min_m, and then a
    release down to z_close_min_r from the rim is accepted. The height path is chosen per release: when ball_z is
    missing (None, or NaN over this release and flight) that release falls back to the XY rules (release_min_r, no
    apex test). Returns dicts t_rel, player, rim, release_r, apex_z, path."""
    out = []
    if scene.ball is None or scene.ball_raw is None:
        return out
    b = scene.ball
    z_wanted = bool(c["ball_z_path"]) and scene.ball_z is not None
    pl, sus = _ball_control(scene, c)
    rims = _rims(c)
    fmax = frames(c["flight_max_s"])
    pthru = frames(c["passthrough_s"])
    nxt = np.full(scene.n + 1, scene.n)  # next frame >= t with sustained control by anyone
    for t in range(scene.n - 1, -1, -1):
        nxt[t] = t if sus[t] >= 0 else nxt[t + 1]
    for t in range(1, scene.n):
        if sus[t - 1] < 0 or sus[t] == sus[t - 1] or np.isnan(b.x[t]):
            continue
        p = pl[sus[t - 1]]
        stop = min(scene.n, t + fmax + 1, nxt[t])
        hit = None
        for u in range(t, stop):
            if not np.isfinite(b.x[u]):
                continue
            hit = next(((name, rx, ry) for name, (rx, ry) in rims.items() if math.hypot(b.x[u] - rx, b.y[u] - ry) <= c["rim_reach_r"]), None)
            if hit:
                break
        if hit is None:
            continue
        name, rx, ry = hit
        # the control test lets go once the ball is HOLD_R away: back-date the release by the travel time
        kp = scene.k(p)
        d = math.hypot(b.x[t] - kp.x[t], b.y[t] - kp.y[t])
        bs = math.hypot(b.vx[t], b.vy[t])
        lag = int(round(d / bs / DT)) if np.isfinite(d) and bs > 1.0 else 0
        t_rel = max(0, t - lag)
        # ball height over the release and flight (a layup peaks at the rim); NaN-only -> this release uses XY rules
        apex = None
        if scene.ball_z is not None:
            zs = np.asarray(scene.ball_z[t_rel:min(scene.n, u + pthru + 1)], dtype=float)
            apex = float(np.nanmax(zs)) if np.any(np.isfinite(zs)) else None
        use_z = z_wanted and apex is not None
        min_r = c["z_close_min_r"] if use_z else c["release_min_r"]
        # (a) a release inside the rim zone (kick-out from the restricted area) is not a shot proxy
        rel_r = math.hypot(b.x[t_rel] - rx, b.y[t_rel] - ry)
        if not rel_r >= min_r:
            continue
        # (b) the flight must head for the rim: mean radial speed >= radial_share_min x mean ball speed
        seg = slice(t_rel, u + 1)
        dx, dy = b.x[seg] - rx, b.y[seg] - ry
        rr = np.hypot(dx, dy)
        vr = -(b.vx[seg] * dx + b.vy[seg] * dy) / np.maximum(rr, 1e-6)
        sp = float(np.nanmean(np.hypot(b.vx[seg], b.vy[seg])))
        if not float(np.nanmean(vr)) >= c["radial_share_min"] * sp:
            continue
        # (c) pass-through: within passthrough_s the ball leaves the rim zone again at speed
        w = slice(u, min(scene.n, u + pthru + 1))
        rw = np.nan_to_num(np.hypot(b.x[w] - rx, b.y[w] - ry), nan=0.0)
        vout = np.nan_to_num(np.hypot(b.vx[w], b.vy[w]), nan=0.0)
        if np.any((rw > c["rim_reach_r"] + c["passthrough_margin_m"]) & (vout > c["passthrough_speed_frac"] * sp)):
            continue
        # (d) KIN5-OOB: a shooter beyond the in-bounds gate (by more than oob_z position sigmas) is an inbounder
        sx, sy = _to_shot_frame(kp.x[t_rel], kp.y[t_rel], name, c)
        sig_pos = K_CAL * math.sqrt(max(float(np.nan_to_num(kp.var_p[t_rel], nan=0.0)), 0.0))
        if np.isfinite(sx) and np.isfinite(sy) and _oob_excess(sx, sy) > c["oob_z"] * sig_pos:
            continue
        # (e) KIN5-BALLZ (optional): the ball rises above the rim on its way there
        if use_z and not apex >= c["z_apex_min_m"]:
            continue
        out.append(dict(t_rel=t_rel, player=p, rim=name, release_r=rel_r, apex_z=apex,
                        path="ball_z_apex" if use_z else "xy_release_proxy"))
    return out


def detect_jump(scene, **params) -> list[Event]:
    """jump (XY proxy): a shot-like release implies a jump; takeoff 0.2 s before release, conf cap 0.3."""
    c = _cfg("jump", params)
    out = []
    for r in _releases(scene, c):
        t_rel, oid, rim = r["t_rel"], r["player"], r["rim"]
        k = scene.k(oid)
        f = _F(k, c)
        t0 = max(0, t_rel - frames(c["takeoff_lead_s"]))
        ps = mvlib.window_conf(f.p_stand, max(0, t_rel - frames(c["stationary_check_s"])), t_rel)
        pc = 1.0 - c["stationary_discount"] * ps
        reasons = ["ball released after sustained control (either team) at >= "
                   f"{c['z_close_min_r'] if r['path'] == 'ball_z_apex' else c['release_min_r']} m from the rim, flew toward it "
                   f"(radial share >= {c['radial_share_min']}) and reached <= "
                   f"{c['rim_reach_r']} m of the {rim} rim within {c['flight_max_s']} s before any sustained control "
                   f"(>= {c['control_min_s']} s, chord relative speed <= {c['control_rel_v']} m/s) and no pass-through (shot context)",
                   f"shooter in bounds (in-bounds gate, {c['oob_z']} sigma margin)",
                   f"takeoff placed {c['takeoff_lead_s']} s before release (proxy); P(stationary before release) {ps:.2f}"]
        if r["path"] == "ball_z_apex":
            reasons.append(f"ball apex {r['apex_z']:.2f} m >= {c['z_apex_min_m']} m (optional ball-height path)")
        # KIN5-FRAME: x, y and spot are all in the frame of the rim that was shot at (far rim: court rotated by 180 deg)
        sx, sy = _to_shot_frame(k.x[t0], k.y[t0], rim, c)
        attrs = dict(release_frame=t_rel, path=r["path"], purpose="shot", shooter_speed=_r(f.vL[t_rel]),
                     x=_r(sx), y=_r(sy), spot=_spot(sx, sy), frame="shot_rim", rim=rim, release_r=_r(r["release_r"]),
                     apex_z=_r(r["apex_z"]) if r["path"] == "ball_z_apex" else None, height_m=None)
        alts = {"set_shot_no_jump": round(ps, 2)} if ps >= 0.2 else {}
        ev = _event(scene, oid, "jump", t0, t0, t_rel, pc, c, attrs, reasons, alts, cap=c["cap"])
        if ev:
            out.append(ev)
    return out


def detect_landing(scene, **params) -> list[Event]:
    """landing (XY proxy): jump proxy takeoff + 0.5 s; type stick / land_and_step / run_out; cap 0.25."""
    c = _cfg("landing", params)
    out = []
    for j in detect_jump(scene):
        oid = j.actors["player"]
        k = scene.k(oid)
        f = _F(k, c)
        t0 = j.t0 + frames(c["nominal_flight_s"])
        if t0 >= scene.n:
            continue
        t1 = min(scene.n - 1, t0 + frames(c["after_s"]))
        v = _nanmean(f.vc, t0, t1)
        typ = "stick" if v < c["stick_speed"] else "run_out" if v >= c["run_out_speed"] else "land_and_step"
        reasons = [f"landing placed {c['nominal_flight_s']} s after the jump proxy takeoff",
                   f"bias-corrected speed {v:.2f} m/s over {c['after_s']} s -> {typ}"]
        lx, ly = _to_shot_frame(k.x[t0], k.y[t0], j.attrs["rim"], _cfg("jump", {}))  # KIN5-FRAME: the linked jump's frame
        attrs = dict(landing_type=typ, x=_r(lx), y=_r(ly), spot=_spot(lx, ly), frame="shot_rim", rim=j.attrs["rim"],
                     linked_jump_t0=j.t0, path=j.attrs["path"], landing_drift=None)
        ev = _event(scene, oid, "landing", t0, t0, t1, j.conf / j.attrs["conf_components"]["cap"], c, attrs, reasons, cap=c["cap"])
        if ev:
            ev.conf = min(ev.conf, j.conf)
            if ev.conf >= c["emit_min"]:
                out.append(ev)
    return out


def detect_turn_in_place(scene, **params) -> list[Event]:
    """turn_in_place: needs pose torso facing (needs_data); invisible to XY, returns []."""
    return []


def detect_jab_step(scene, **params) -> list[Event]:
    """jab_step: needs pose ankle keypoints (needs_data); below XY noise, returns []."""
    return []


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------
DETECTORS = {
    "stand": detect_stand,
    "walk": detect_walk,
    "jog": detect_jog,
    "run": detect_run,
    "high_speed": detect_high_speed,
    "sprint": detect_sprint,
    "hsr_effort": detect_hsr_effort,
    "sprint_effort": detect_sprint_effort,
    "peak_speed": detect_peak_speed,
    "accel_effort": detect_accel_effort,
    "decel_effort": detect_decel_effort,
    "burst": detect_burst,
    "brake": detect_brake,
    "hesitation": detect_hesitation,
    "stop_and_go": detect_stop_and_go,
    "stop": detect_stop,
    "start": detect_start,
    "cod": detect_cod,
    "plant_step": detect_plant_step,
    "curved_run": detect_curved_run,
    "forward_run": detect_forward_run,
    "backpedal": detect_backpedal,
    "defensive_slide": detect_defensive_slide,
    "crossover_run": detect_crossover_run,
    "jump": detect_jump,
    "landing": detect_landing,
    "turn_in_place": detect_turn_in_place,
    "jab_step": detect_jab_step,
}


def detect_all(scene) -> list[Event]:
    """Run every kinematics detector on a scene; events sorted by t0."""
    out = []
    for fn in DETECTORS.values():
        out += fn(scene)
    return sorted(out, key=lambda e: (e.t0, e.kind))
