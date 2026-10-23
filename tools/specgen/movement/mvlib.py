"""Reference core for the movement grammar (spec tooling, not the production labeller).

Implements the measurement pipeline of config/movement_grammar.yaml (MP rules):
segmenting, a 2-D constant-acceleration Kalman filter with RTS smoothing per segment,
derived features with validity gates, calibrated sigmas, hysteresis intervals and
probability helpers. Detectors in tools/specgen/movement/detectors/ build on it.

Frame: the named-spot attacked-rim frame (metres; rim at the origin). Time base:
29.97 fps, dt = 1001/30000 s. Elapsed durations are (n_frames - 1) * dt.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

DT = 1001 / 30000
FPS = 1 / DT
K_CAL = 1.8  # MP-09 default sigma inflation until measured on our footage
Q_DEFAULT = 30.0  # MP-04 white-jerk intensity m^2/s^5
Q_HIGH_NOISE = 10.0  # MP-04 when median sigma_p >= 0.45 m
Q_BALL = 5000.0  # ball: passes and catches change velocity within a frame or two (proposal; tune on data)
REINIT_AFTER = 3  # MP-03: three consecutive rejections end the run and re-initialise at the measurement
GAP_SHORT_S = 1.0  # MP-05
GAP_LONG_S = 2.0
EDGE_FRAMES = 15  # MP-06
K_EDGE = {0: 2.9, 1: 2.65, 2: 2.4, 3: 2.2, 4: 2.0, 5: 1.83, 6: 1.67, 7: 1.5, 8: 1.38, 9: 1.27, 10: 1.15,
          11: 1.12, 12: 1.09, 13: 1.06, 14: 1.03}


def frames(seconds: float) -> int:
    """Number of intervals covering an elapsed time (rounded to the nearest frame)."""
    return int(round(seconds / DT))


def phi(z):
    """Standard normal CDF (vectorised)."""
    z = np.asarray(z, dtype=float)
    return 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))


# --------------------------------------------------------------------------------------
# Tracks and segments (MP-01, MP-05)
# --------------------------------------------------------------------------------------
@dataclass
class Track:
    """Raw floor observations of one object: NaN where unobserved."""
    oid: str
    x: np.ndarray
    y: np.ndarray
    sigma_p: np.ndarray  # per-frame measurement sigma (m)
    cut: np.ndarray | None = None  # True at frames that start a new camera segment
    team: str = ""
    role: str = ""  # 'player' or 'ball'
    z: np.ndarray | None = None  # optional height (m), ball only; None when the source has none

    def __post_init__(self):
        n = len(self.x)
        if self.cut is None:
            self.cut = np.zeros(n, dtype=bool)


def segments(tr: Track, max_gap_s: float = GAP_LONG_S) -> list[tuple[int, int]]:
    """Inclusive frame ranges [a, b] with no camera cut and no gap longer than max_gap_s."""
    obs = ~np.isnan(tr.x)
    out, a, last = [], None, None
    max_gap = frames(max_gap_s)
    for i in range(len(obs)):
        if tr.cut[i] and a is not None:
            out.append((a, last))
            a, last = None, None
        if obs[i]:
            if a is None:
                a = i
            elif i - last > max_gap:
                out.append((a, last))
                a = i
            last = i
    if a is not None:
        out.append((a, last))
    return [(a, b) for a, b in out if b - a >= 4]


# --------------------------------------------------------------------------------------
# CA Kalman + RTS (MP-03, MP-04)
# --------------------------------------------------------------------------------------
def _ca_mats(q: float, dt: float = DT):
    F1 = np.array([[1, dt, dt * dt / 2], [0, 1, dt], [0, 0, 1]])
    Q1 = q * np.array([[dt**5 / 20, dt**4 / 8, dt**3 / 6], [dt**4 / 8, dt**3 / 3, dt**2 / 2], [dt**3 / 6, dt**2 / 2, dt]])
    return F1, Q1


def ca_rts(z: np.ndarray, r: np.ndarray, q: float = Q_DEFAULT, gate: float = 13.8):
    """Smooth one axis. z: observations (NaN = missing); r: measurement variance per frame.

    Returns state means (n, 3) [p, v, a], covariances (n, 3, 3) and a rejected-outlier mask.
    The 2-dof chi-square gate of MP-03 is applied per axis with 1 dof equivalent (6.63*...)
    by the caller; here `gate` is the per-axis squared-innovation threshold.
    """
    n = len(z)
    F, Q = _ca_mats(q)
    H = np.array([1.0, 0.0, 0.0])
    xs_f = np.zeros((n, 3)); Ps_f = np.zeros((n, 3, 3)); xs_p = np.zeros((n, 3)); Ps_p = np.zeros((n, 3, 3))
    rejected = np.zeros(n, dtype=bool)
    first = np.flatnonzero(~np.isnan(z))
    if len(first) == 0:
        return np.full((n, 3), np.nan), np.full((n, 3, 3), np.nan), rejected
    k0 = first[: min(5, len(first))]
    x = np.array([np.nanmean(z[k0]), 0.0, 0.0])
    P = np.diag([4 * np.nanmean(r[k0]), 25.0, 50.0])
    run = 0
    for k in range(n):
        if k > 0:
            x = F @ x
            P = F @ P @ F.T + Q
        xs_p[k], Ps_p[k] = x, P
        if not np.isnan(z[k]):
            S = H @ P @ H + r[k]
            y = z[k] - H @ x
            if y * y / S > gate and run < REINIT_AFTER - 1:
                rejected[k] = True
                run += 1
            elif y * y / S > gate:
                # third rejection in a row: the model lost the object (identity jump or real impulse).
                # Re-initialise at the measurement with wide velocity/acceleration uncertainty.
                x = np.array([z[k], 0.0, 0.0])
                P = np.diag([r[k], 25.0, 50.0])
                rejected[k] = True
                run = 0
            else:
                run = 0
                K = P @ H / S
                x = x + K * y
                P = P - np.outer(K, H @ P)
        xs_f[k], Ps_f[k] = x, P
    xs, Ps = xs_f.copy(), Ps_f.copy()
    for k in range(n - 2, -1, -1):
        C = Ps_f[k] @ F.T @ np.linalg.inv(Ps_p[k + 1])
        xs[k] = xs_f[k] + C @ (xs[k + 1] - xs_p[k + 1])
        Ps[k] = Ps_f[k] + C @ (Ps[k + 1] - Ps_p[k + 1]) @ C.T
    return xs, Ps, rejected


# --------------------------------------------------------------------------------------
# Features (MP-07, MP-09)
# --------------------------------------------------------------------------------------
@dataclass
class Kin:
    """Smoothed kinematics of one object over the whole clip (NaN outside segments)."""
    oid: str
    x: np.ndarray
    y: np.ndarray
    vx: np.ndarray
    vy: np.ndarray
    ax: np.ndarray
    ay: np.ndarray
    var_v: np.ndarray  # per-axis velocity variance (isotropic approximation)
    var_a: np.ndarray
    var_p: np.ndarray
    state: np.ndarray  # 'observed' | 'interp_short' | 'interp_long' | 'none'
    edge: np.ndarray  # frames to the nearest segment edge
    rejected: np.ndarray
    team: str = ""
    role: str = ""
    extra: dict = field(default_factory=dict)

    # ---- derived features with validity gates (MP-07) ----
    @property
    def speed(self):
        s = np.hypot(self.vx, self.vy)
        s[self.state == "interp_long"] = np.nan
        return s

    @property
    def sigma_speed(self):
        return K_CAL * np.sqrt(self.var_v) * self.k_edge

    @property
    def k_edge(self):
        return np.array([K_EDGE.get(int(e), 1.0) if e >= 0 else np.nan for e in self.edge])

    @property
    def heading(self):
        h = np.degrees(np.arctan2(self.vy, self.vx))
        h[~(self.speed >= 1.0)] = np.nan
        return h

    @property
    def accel_along(self):
        s = self.speed
        a = (self.vx * self.ax + self.vy * self.ay) / np.where(s > 0, s, np.nan)
        a[~(s >= 0.5)] = np.nan
        return a

    @property
    def turn_rate(self):
        s2 = self.vx**2 + self.vy**2
        tr = np.degrees((self.vx * self.ay - self.vy * self.ax) / np.where(s2 > 0, s2, np.nan))
        tr[~(np.sqrt(s2) >= 2.0)] = np.nan
        return tr

    @property
    def curvature(self):
        return np.abs(np.radians(self.turn_rate)) / self.speed

    @property
    def r(self):
        return np.hypot(self.x, self.y)

    @property
    def v_r(self):
        """Velocity toward the rim (positive = toward)."""
        rr = self.r
        return -(self.vx * self.x + self.vy * self.y) / np.where(rr > 0, rr, np.nan)

    @property
    def stationary_s2(self):
        """MP-09 significance statistic s2 = v^T P_v^-1 v (chi-square 2 dof under v = 0)."""
        return (self.vx**2 + self.vy**2) / ((K_CAL**2) * self.var_v)


def smooth(tr: Track, q: float | None = None) -> Kin:
    """Run CA-RTS on every segment of a track and return per-frame kinematics."""
    n = len(tr.x)
    if q is None:
        med = np.nanmedian(tr.sigma_p) if np.any(~np.isnan(tr.sigma_p)) else 0.3
        q = Q_BALL if tr.role == "ball" else (Q_HIGH_NOISE if med >= 0.45 else Q_DEFAULT)
    out = {k: np.full(n, np.nan) for k in ("x", "y", "vx", "vy", "ax", "ay", "var_v", "var_a", "var_p")}
    state = np.array(["none"] * n, dtype=object)
    edge = np.full(n, -1)
    rejected = np.zeros(n, dtype=bool)
    obs = ~np.isnan(tr.x)
    for a, b in segments(tr):
        sl = slice(a, b + 1)
        rvar = np.where(np.isnan(tr.sigma_p[sl]), 0.09, tr.sigma_p[sl] ** 2)
        xs, Px, rx = ca_rts(tr.x[sl], rvar, q)
        ys, Py, ry = ca_rts(tr.y[sl], rvar, q)
        out["x"][sl], out["vx"][sl], out["ax"][sl] = xs[:, 0], xs[:, 1], xs[:, 2]
        out["y"][sl], out["vy"][sl], out["ay"][sl] = ys[:, 0], ys[:, 1], ys[:, 2]
        out["var_p"][sl] = (Px[:, 0, 0] + Py[:, 0, 0]) / 2
        out["var_v"][sl] = (Px[:, 1, 1] + Py[:, 1, 1]) / 2
        out["var_a"][sl] = (Px[:, 2, 2] + Py[:, 2, 2]) / 2
        rejected[sl] = rx | ry
        idx = np.arange(a, b + 1)
        edge[sl] = np.minimum(idx - a, b - idx)
        # gap classification (MP-05)
        seg_obs = obs[sl]
        st = np.where(seg_obs, "observed", "interp_short").astype(object)
        run_start = None
        for k, o in enumerate(list(seg_obs) + [True]):
            if not o and run_start is None:
                run_start = k
            elif o and run_start is not None:
                if (k - run_start) * DT > GAP_SHORT_S:
                    st[run_start:k] = "interp_long"
                    for j in range(run_start, k):  # gap edges count as segment edges for warm-up
                        edge[a + j] = 0
                run_start = None
        state[sl] = st
    return Kin(tr.oid, out["x"], out["y"], out["vx"], out["vy"], out["ax"], out["ay"], out["var_v"], out["var_a"],
               out["var_p"], state, edge, rejected, tr.team, tr.role)


# --------------------------------------------------------------------------------------
# Intervals and probabilities (MP-10, MP-11, MP-16)
# --------------------------------------------------------------------------------------
@dataclass
class Event:
    """One detected instance of a primitive, action or set component."""
    kind: str
    actors: dict
    t0: int  # reference frame
    start: int
    end: int  # inclusive
    conf: float
    attrs: dict = field(default_factory=dict)

    @property
    def duration_s(self):
        return (self.end - self.start) * DT


def hysteresis(enter: np.ndarray, stay: np.ndarray, min_s: float, max_gap_frames: int = 0) -> list[tuple[int, int]]:
    """Intervals that start where `enter` is true and continue while `stay` is true.

    NaN-safe: pass boolean arrays (False where invalid). Intervals shorter than min_s elapsed
    are dropped; gaps of <= max_gap_frames inside an interval are bridged.
    """
    n = len(enter)
    out, k = [], 0
    while k < n:
        if enter[k]:
            a = k
            gap = 0
            j = k + 1
            last = k
            while j < n:
                if stay[j]:
                    last, gap = j, 0
                elif gap < max_gap_frames:
                    gap += 1
                else:
                    break
                j += 1
            if (last - a) * DT >= min_s - 1e-9:
                out.append((a, last))
            k = max(j, last + 1)
        else:
            k += 1
    return out


def p_below(value, thr, sigma):
    """P(true value < thr) given estimate and sigma (MP-10)."""
    return phi((thr - np.asarray(value)) / np.maximum(np.asarray(sigma), 1e-6))


def p_above(value, thr, sigma):
    return phi((np.asarray(value) - thr) / np.maximum(np.asarray(sigma), 1e-6))


def window_conf(p: np.ndarray, a: int, b: int, corr_s: float = 0.3) -> float:
    """Confidence that a per-frame condition held over [a, b] (MP-16 P_cond).

    Uses the window-mean of the per-frame probability with an effective-sample correction:
    frames within corr_s are correlated, so the window behaves like n_eff independent looks.
    """
    seg = np.asarray(p[a:b + 1], dtype=float)
    seg = seg[~np.isnan(seg)]
    if len(seg) == 0:
        return 0.0
    return float(np.clip(np.mean(seg), 0.0, 1.0))


def edge_factor(k: Kin, t: int) -> float:
    e = k.edge[t]
    return 0.0 if e < 0 or e < 5 else 1.0 / K_EDGE.get(int(e), 1.0)


def gap_factor(k: Kin, a: int, b: int) -> float:
    st = set(k.state[a:b + 1])
    if "interp_long" in st or "none" in st:
        return 0.0
    if "interp_short" in st:
        return 0.8
    return 1.0


def dist(ka: Kin, kb: Kin) -> np.ndarray:
    return np.hypot(ka.x - kb.x, ka.y - kb.y)


def sigma_dist(ka: Kin, kb: Kin, common: float = 0.0) -> np.ndarray:
    """MP-19 pair-distance sigma; `common` is the shared calibration variance to subtract."""
    v = ka.var_p + kb.var_p - 2 * common
    return K_CAL * np.sqrt(np.maximum(v, 1e-6))


def closing_speed(ka: Kin, kb: Kin) -> np.ndarray:
    """Rate at which the distance a-b shrinks (positive = closing)."""
    dx, dy = kb.x - ka.x, kb.y - ka.y
    d = np.hypot(dx, dy)
    ex, ey = dx / np.where(d > 0, d, np.nan), dy / np.where(d > 0, d, np.nan)
    return -((kb.vx - ka.vx) * ex + (kb.vy - ka.vy) * ey)


# --------------------------------------------------------------------------------------
# Scene: everything a detector may read for one clip
# --------------------------------------------------------------------------------------
@dataclass
class Scene:
    """Smoothed kinematics of all players and the ball for one clip, in the attacked-rim frame.

    offense / defense: lists of object ids. holder[t]: id of the offensive player in control of
    the ball at frame t, or None (flight, loose, unknown). Built by build_scene().
    """
    kins: dict
    offense: list
    defense: list
    ball: Kin | None
    holder: np.ndarray
    n: int
    ball_raw: tuple | None = None  # (x, y) raw ball observations; holder logic uses these (MP-15)
    ball_z: np.ndarray | None = None  # raw ball height (m) when the source provides it, else None

    def k(self, oid):
        return self.kins[oid]

    def players(self):
        return self.offense + self.defense


HOLD_R = 1.0  # m: ball within this distance of a player's reference point = in that player's control (proposal)


def build_scene(tracks, offense_team="O", q=None):
    """Smooth every track and infer the ball holder per frame (nearest offensive player within HOLD_R)."""
    kins = {tr.oid: smooth(tr, q) for tr in tracks}
    ball = kins.pop("ball", None)
    braw = next(((t.x, t.y) for t in tracks if t.oid == "ball"), None)
    bz = next((t.z for t in tracks if t.oid == "ball"), None)
    off = [t.oid for t in tracks if t.role != "ball" and t.team == offense_team]
    dfn = [t.oid for t in tracks if t.role != "ball" and t.team != offense_team]
    n = len(tracks[0].x)
    holder = np.array([None] * n, dtype=object)
    if braw is not None:
        bxr, byr = braw
        for t in range(n):
            if np.isnan(bxr[t]):
                continue
            best, bd = None, HOLD_R
            for o in off:
                kk = kins[o]
                d = math.hypot(bxr[t] - kk.x[t], byr[t] - kk.y[t]) if not np.isnan(kk.x[t]) else 9e9
                if d <= bd:
                    best, bd = o, d
            holder[t] = best
    return Scene(kins, off, dfn, ball, holder, n, braw, bz)
