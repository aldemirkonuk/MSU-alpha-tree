"""Cuts and off-ball paths family: reference detectors (spec tooling, not the production labeller).

Implements config/movement_grammar/cuts.yaml. Every numeric threshold is read from that file at
import (single source of truth); a detector call may override any of its parameters by keyword.

Frame: the named-spot attacked-rim frame (metres; rim at the origin, +y up the floor). Time base:
29.97 fps (mvlib.DT). Every detector returns mvlib.Event objects. Confidence follows MP-16:
conf = P_cond x edge_factor x gap_factor, where P_cond is the weakest link of the rule's tests
(each test is Phi of its z-margin, CU.R1) and of the window_conf of the rule's per-frame condition.
An event is emitted only when every test passes at its nominal value and conf >= min_conf.

Building blocks shared by the detectors (consumer proxies, documented in the YAML):
- MOVE intervals (CU.P1): sigma-adaptive speed hysteresis on off-ball frames.
- Chord turns (CU.R0, MP-13): the angle between the displacement over [t-0.6, t-0.1] s and over
  [t+0.1, t+0.6] s. The plant phase is skipped, so a stop-and-reverse still measures its full angle.
- Ball events from scene.holder: passes (holder run A -> flight -> holder run B), drives
  (holder from r > 6.1 to r < 3.05), ball screens (handler within 1.2 m of a stationary teammate),
  paint touches.
- Off-ball screen contacts: an off-ball mover within 1.2 m of a stationary teammate (chi-square
  stationary_s2 < 5.99 on >= 60 % of a 0.3 s window); each contact carries p = P(true d <= 1.2 m) with the
  scaled pair sigma, and rules that need borderline contacts search to 1.2 m + 2 sigma (loop 1, F09).
- Chord-turn plant skip widens to 0.2 s for tracks in the mvlib high-noise tier (loop 1, F08).
- Every item's min_duration_s is enforced at emission (loop 1, F18).

Loop-1 changes (tester failures F01-F21) are listed in the YAML under changes_loop1; loop-2 changes (confirmer
regressions and residuals: R1, R2, F08r, F09r, F21r, C1, and the declined F13r / F14r) under changes_loop2.
Loop-5 changes (L5-01..L5-06, YAML changes_loop5): every registered detector runs through cu_postrules (half-court gate
for non-transition labels, per-(kind, actors) de-duplication, tracking-glitch drop); cut_i needs a significant rimward
in-leg; the high-noise-tier veer needs a significant approach.
Loop-7 changes (L7-01..L7-05, YAML changes_loop7): cut_i's 60 deg in-leg rule is an angular test (I axis and in-leg chord
against the bearing to the rim); the half-court carry's run test uses the walk-run gait speed plus ball-holder status
(a pass followed by a burst is a half-court action) instead of a 3.0 m/s sustain speed.
Loop-8 changes (L8-01..L8-05, YAML changes_loop8): the carry exemption applies only while the actor is the ball handler
(after the release the label is judged on its own pace, a walk-pace relocation after the pass is half-court), it needs
a release by the label start, and a burst must be significant; cut_i's chord tolerance is bounded and an I that reaches
the rim zone needs radial depth.
Loop-9 changes (L9-01..L9-05, YAML changes_loop9): the transition carry separates a push from a half-court pass-and-cut
by structure: a push (TRN-P08 pace) released on the run that keeps running is the transition (the L8-03 burst margin is
gone; the burst ratio is a secondary cue after a jog-up only); keeps running is judged on the post-release segment; an
off-ball runner who slows to a walk after the crossing is half-court; a dribble whose holder flag drops out is on-ball.
- Matched defender: the defender with the smallest mean distance over a window; ambiguous when
  the runner-up is within 0.5 m.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np
import yaml

_HERE = Path(__file__).resolve()
for _p in (_HERE.parents[1], _HERE.parents[2] / "named_spots"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mvlib  # noqa: E402
import spotlib  # noqa: E402
from mvlib import DT, K_CAL, Event, edge_factor, gap_factor, p_above, p_below, window_conf  # noqa: E402

CONFIG = _HERE.parents[4] / "config" / "movement_grammar" / "cuts.yaml"
DOC = yaml.safe_load(CONFIG.read_text())
ITEMS = {it["id"]: it for it in DOC["items"]}


def _plain(params):
    """YAML params {name: {value, unit}} -> {name: value}."""
    return {k: (v["value"] if isinstance(v, dict) and "value" in v else v) for k, v in (params or {}).items()}


PARAMS = {i: _plain(it.get("params")) for i, it in ITEMS.items()}
G = PARAMS["cu_features"]  # shared kinematic and geometric constants
_SPOT_DOC, SPOTS = spotlib.load()
C = spotlib.C
OWN_RIM_Y = C["FAR_END_Y"] - C["RIM_Y_FROM_END"]  # defensive rim in the attacked-rim frame (25.45 m)


def F(seconds: float) -> int:
    """Frames covering an elapsed time."""
    return int(round(seconds / DT))


# --------------------------------------------------------------------------------------
# Test bookkeeping (CU.R1): each test is a z-margin; P_cond is the weakest link
# --------------------------------------------------------------------------------------
class Tests:
    """Collects the rule's tests as z-margins (CU.R1). ok is False as soon as one test fails at its
    nominal value; p = Phi(z) is the probability that the true value passes."""

    def __init__(self):
        self.p, self.z, self.ok = {}, {}, True

    def _add(self, name, z, passed):
        z = float(np.clip(np.nan_to_num(z, nan=-9.0), -9.0, 9.0))
        self.z[name] = round(z, 2)
        self.p[name] = float(mvlib.phi(z))
        self.ok = self.ok and bool(passed)
        return bool(passed)

    @staticmethod
    def _bad(v):
        return v is None or not np.isfinite(v)

    def ge(self, name, v, thr, sig):
        if self._bad(v):
            return self._add(name, -9.0, False)
        return self._add(name, (v - thr) / max(sig, 1e-6), v >= thr)

    def le(self, name, v, thr, sig):
        if self._bad(v):
            return self._add(name, -9.0, False)
        return self._add(name, (thr - v) / max(sig, 1e-6), v <= thr)

    def band(self, name, v, lo, hi, sig):
        if self._bad(v):
            return self._add(name, -9.0, False)
        return self._add(name, min(v - lo, hi - v) / max(sig, 1e-6), lo <= v <= hi)

    def flag(self, name, passed, p=None):
        """Boolean test; p (optional) is its probability when it was computed elsewhere."""
        p = (1.0 if passed else 0.0) if p is None else float(np.clip(p, 0.0, 1.0))
        return self._add(name, _NORM.inv_cdf(min(max(p, 1e-9), 1 - 1e-9)), passed)

    def frac(self, name, mask_p, thr):
        """Fraction-of-frames test from per-frame probabilities p_k: f = mean p_k against thr, with a
        Poisson-binomial normal approximation whose variance is inflated x9 for ~0.3 s frame correlation."""
        mp = np.asarray(mask_p, dtype=float)
        mp = mp[np.isfinite(mp)]
        if len(mp) == 0:
            return self._add(name, -9.0, False)
        n = len(mp)
        f = float(np.mean(mp))
        sig = max(0.01, math.sqrt(9.0 * float(np.sum(mp * (1 - mp)))) / n)
        return self._add(name, (f - thr) / sig, float(np.mean(mp >= 0.5)) >= thr)

    def pmin(self):
        return min(self.p.values()) if self.p else 1.0

    def binding(self):
        return min(self.p, key=self.p.get) if self.p else None


_NORM = NormalDist()


def _emit(kind, actors, t0, a, b, tests, kins, attrs=None, p_frame=None, cap=None, min_conf=None):
    """Build an Event (MP-16) or return None when a test failed, conf < min_conf, or the event is
    shorter than the item's min_duration_s (YAML; fix F18)."""
    if not tests.ok:
        return None
    a, b, t0 = int(a), int(b), int(t0)
    kind_min = ITEMS.get(kind, {}).get("min_duration_s")
    if kind_min and (b - a) * DT < kind_min - 1e-9:
        return None
    pc = tests.pmin()
    if p_frame is not None:
        pc = min(pc, window_conf(p_frame, a, b))
    ef = min(edge_factor(k, t0) for k in kins)
    gf = min(gap_factor(k, a, b) for k in kins)
    conf = pc * ef * gf
    if cap is not None:
        conf = min(conf, cap)
    min_conf = G["min_conf"] if min_conf is None else min_conf
    if conf < min_conf:
        return None
    at = dict(attrs or {})
    at.update(margins=tests.z, binding_test=tests.binding(), p_cond=round(pc, 3), edge=round(ef, 3), gap=gf,
              strict=conf >= G["strict_conf"], cap=cap)
    return Event(kind, actors, t0, a, b, round(float(conf), 4), at)


# --------------------------------------------------------------------------------------
# Geometry helpers
# --------------------------------------------------------------------------------------
def _ang(u, v):
    """Signed angle (deg) from vector u to vector v, in (-180, 180]."""
    return math.degrees(math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1]))


def _norm(v):
    return math.hypot(v[0], v[1])


def _m(x, y):
    return np.degrees(np.arctan2(y, np.abs(x)))


def _d3(x, y):
    r = np.hypot(x, y)
    return np.where(y <= C["BREAK_Y"], np.abs(x) - C["CORNER_X"], r - C["ARC_R"])


def _sd_paint_out(x, y):
    ax = np.abs(x)
    cy = (C["FT_Y"] + C["END_Y"]) / 2
    hy = (C["FT_Y"] - C["END_Y"]) / 2
    dx, dy = ax - C["LANE_X"], np.abs(y - cy) - hy
    return np.hypot(np.maximum(dx, 0), np.maximum(dy, 0)) + np.minimum(np.maximum(dx, dy), 0)


def _intervals(mask):
    """Inclusive runs of True."""
    out, a = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and a is None:
            a = i
        elif not v and a is not None:
            out.append((a, i - 1))
            a = None
    return out


def _path_stats(x, y, a, b):
    """Path descriptors over [a, b]: length, chord, straightness, signed roundness (+ = rim side)."""
    px, py = x[a:b + 1], y[a:b + 1]
    ok = np.isfinite(px) & np.isfinite(py)
    px, py = px[ok], py[ok]
    if len(px) < 2:
        return dict(L=0.0, C=0.0, straightness=np.nan, roundness_m=0.0, roundness_side=0)
    L = float(np.sum(np.hypot(np.diff(px), np.diff(py))))
    cx, cy = px[-1] - px[0], py[-1] - py[0]
    Cn = math.hypot(cx, cy)
    if Cn < 1e-6:
        return dict(L=L, C=0.0, straightness=0.0, roundness_m=0.0, roundness_side=0)
    perp = ((px - px[0]) * cy - (py - py[0]) * cx) / Cn  # signed distance from the chord line
    i = int(np.argmax(np.abs(perp)))
    rim_side = -((0 - px[0]) * cy - (0 - py[0]) * cx) / Cn  # sign of the rim relative to the chord
    side = 1 if (perp[i] * -rim_side) > 0 else -1
    return dict(L=L, C=Cn, straightness=Cn / L if L > 0 else np.nan, roundness_m=float(abs(perp[i])),
                roundness_side=side)


def _resampled_length(x, y, a, b, step=0.25):
    """Path length of the smoothed path resampled at `step` m (suppresses residual jitter)."""
    L, lx, ly = 0.0, x[a], y[a]
    for t in range(a + 1, b + 1):
        if not (np.isfinite(x[t]) and np.isfinite(y[t])):
            continue
        d = math.hypot(x[t] - lx, y[t] - ly)
        if d >= step:
            L += d
            lx, ly = x[t], y[t]
    return L


def _bezier(x, y, a, b):
    """Least-squares cubic Bezier (4 control points) with chord-length parameterisation."""
    px, py = x[a:b + 1], y[a:b + 1]
    ok = np.isfinite(px) & np.isfinite(py)
    px, py = px[ok], py[ok]
    if len(px) < 4:
        return None
    s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(px), np.diff(py)))])
    u = s / s[-1] if s[-1] > 0 else np.linspace(0, 1, len(px))
    B = np.stack([(1 - u) ** 3, 3 * u * (1 - u) ** 2, 3 * u ** 2 * (1 - u), u ** 3], axis=1)
    cx = np.linalg.lstsq(B, px, rcond=None)[0]
    cy = np.linalg.lstsq(B, py, rcond=None)[0]
    return [[round(float(a_), 3), round(float(b_), 3)] for a_, b_ in zip(cx, cy)]


def _circle_fit(px, py):
    """Algebraic (Kasa) circle fit -> centre x, centre y, radius."""
    A = np.stack([px, py, np.ones_like(px)], axis=1)
    bb = px ** 2 + py ** 2
    sol = np.linalg.lstsq(A, bb, rcond=None)[0]
    cx, cy = sol[0] / 2, sol[1] / 2
    return cx, cy, math.sqrt(max(sol[2] + cx * cx + cy * cy, 0.0))


# --------------------------------------------------------------------------------------
# Per-scene context (cached on the scene object)
# --------------------------------------------------------------------------------------
class _Feat:
    """Arrays for one player, derived once per scene."""

    def __init__(self, k):
        self.k = k
        self.x, self.y = k.x, k.y
        self.speed = k.speed
        self.sig_speed = k.sigma_speed
        self.sig_p = K_CAL * np.sqrt(k.var_p)
        self.r = k.r
        self.m = _m(k.x, k.y)
        self.d3 = _d3(k.x, k.y)
        self.sdp = _sd_paint_out(k.x, k.y)
        self.vr = k.v_r  # + = toward the rim
        self.s2 = k.stationary_s2
        self.hd = k.heading


class _Ctx:
    def __init__(self, scene):
        self.s = scene
        self.n = scene.n
        self.f = {o: _Feat(scene.k(o)) for o in scene.players()}
        n = self.n
        bx, by = np.full(n, np.nan), np.full(n, np.nan)
        if scene.ball is not None:
            bx, by = scene.ball.x.copy(), scene.ball.y.copy()
        for t in range(n):  # ball proxy: the holder's position when the ball track is missing
            h = scene.holder[t]
            if h is not None and not np.isfinite(bx[t]):
                bx[t], by[t] = self.f[h].x[t], self.f[h].y[t]
        self.bx, self.by = bx, by
        db = G["ball_dead_band_m"]
        self.bs = np.where(np.isfinite(bx), np.where(np.abs(bx) < db, 0, np.sign(bx)), 0).astype(int)
        self._cache = {}
        self.own = self._own_possession()

    def _own_possession(self):
        """Team possession mask (fix L4-01, loop 4): True while the offense has the ball. scene.holder only looks at
        offensive players, so a defender with the ball (a rebound, a steal, or a stretch of the clip in which the
        other team attacks) still reads as offense when a guarding offensive player is within 1.0 m. A frame is
        defense-controlled when a defender is within poss_ctrl_r_m of the raw ball and every offensive player is at
        least poss_margin_m farther; offense-controlled when an offensive player is within poss_ctrl_r_m and no
        nearer than the nearest defender. Possession switches after poss_switch_s of sustained control by the
        other team (back-dated to the start of that run). No ball or no defenders -> always the offense's ball."""
        n, s = self.n, self.s
        own = np.ones(n, dtype=bool)
        raw = s.ball_raw if s.ball_raw is not None else ((s.ball.x, s.ball.y) if s.ball is not None else None)
        if raw is None or not s.defense or not s.offense:
            return own
        bx, by = np.asarray(raw[0], float), np.asarray(raw[1], float)

        def nearest(ids):
            d = np.full(n, np.inf)
            for o in ids:
                k = s.k(o)
                d = np.fmin(d, np.hypot(bx - k.x, by - k.y))
            return d
        dO, dD = nearest(s.offense), nearest(s.defense)
        r, mg = G["poss_ctrl_r_m"], G["poss_margin_m"]
        ok = np.isfinite(bx) & np.isfinite(by)
        ctrl_d = ok & (dD <= r) & (dO >= dD + mg)
        ctrl_o = ok & (dO <= r) & (dO <= dD)
        k_sw = max(1, F(G["poss_switch_s"]))
        cur, run = True, 0
        for t in range(n):
            other = ctrl_d[t] if cur else ctrl_o[t]
            same = ctrl_o[t] if cur else ctrl_d[t]
            if other:
                run += 1
                if run >= k_sw:
                    cur = not cur
                    own[t - run + 1:t] = cur
                    run = 0
            elif same:
                run = 0
            own[t] = cur
        return own

    # ---- noise tier (fix F08): mvlib switches to Q_HIGH_NOISE when the raw median sigma_p >= 0.45 m ----
    def high_noise(self, o):
        """True when o's track was smoothed in the mvlib high-noise tier. The Kin keeps no raw sigma, but the
        steady-state CA-RTS ratio sqrt(var_p / var_v) depends only on (q, sigma_p): <= 0.35 s in the default
        tier for every sigma_p < 0.45 m and >= 0.41 s in the high-noise tier, so a 0.38 s cut separates them."""
        def run():
            k = self.s.k(o)
            ok = np.isfinite(k.var_p) & np.isfinite(k.var_v) & (k.var_v > 0)
            if not ok.any():
                return False
            return bool(np.median(np.sqrt(k.var_p[ok] / k.var_v[ok])) >= G["high_noise_ratio_s"])
        return self.memo(("hinoise", o), run)

    def skip_s(self, o):
        """Plant skip of the chord turn: turn_skip_s, or turn_skip_high_noise_s in the high-noise tier."""
        return G["turn_skip_high_noise_s"] if self.high_noise(o) else G["turn_skip_s"]

    # ---- memo helper ----
    def memo(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def offball(self, o):
        """Off-ball frames of o while his team has the ball (fix L4-01)."""
        return self.memo(("offball", o), lambda: np.array([h != o for h in self.s.holder]) & self.own)

    # ---- named spots (membership on either side for mirrored spots) ----
    def spot(self, o, sid):
        def run():
            sp, fe = SPOTS[sid], self.f[o]
            out = np.zeros(self.n, dtype=bool)
            for t in range(self.n):
                if np.isfinite(fe.x[t]):
                    out[t] = bool(sp.labels(float(fe.x[t]), float(fe.y[t])))
            return out
        return self.memo(("spot", o, sid), run)

    def in_any(self, o, sids):
        m = np.zeros(self.n, dtype=bool)
        for s_ in sids:
            m |= self.spot(o, s_)
        return m

    def region(self, o, t):
        fe = self.f[o]
        lab = spotlib.court_region(SPOTS, float(fe.x[t]), float(fe.y[t])) if np.isfinite(fe.x[t]) else ["unknown"]
        return lab[0] if lab else "unknown"

    def stationary(self, o):
        """Chi-square stationarity (MP-09): s2 < 5.99 on >= stationary_frac of a centred window."""
        def run():
            # fix L4-06 (loop 4): var_v floored at stationary_var_v_floor_mps^2 (the CA-RTS steady-state velocity sigma
            # at sigma_p 0.2, the lowest production tier; the screens family's SCR-L4-01 floor). On vendor-smoothed
            # tracks var_v is tiny and s2 < 5.99 meant |v| < 0.4-0.7 m/s, so a screener still settling at 0.6-1.0 m/s
            # was a mover on clean tracks and a screener once noise was added (cut_straight x2.2 at added noise 0.3)
            k = self.s.k(o)
            fl = G["stationary_var_v_floor_mps"]
            s2 = (k.vx**2 + k.vy**2) / ((K_CAL**2) * np.maximum(k.var_v, fl**2))
            # fix L4-03 (loop 4): 'not significantly moving' loses power as sigma grows (s2 = v^2 / var_v), so at
            # sigma_p 0.3 a teammate jogging at 1.0-1.5 m/s passed as a set screener; the point speed must also be
            # below stationary_max_mps (the MOVE exit speed)
            sp = np.nan_to_num(self.f[o].speed, nan=99.0)
            ok = (np.where(np.isfinite(s2), s2 < G["stationary_s2_max"], False) & (sp <= G["stationary_max_mps"])).astype(float)
            h = F(G["stationary_window_s"]) // 2
            out = np.zeros(self.n, dtype=bool)
            for t in range(self.n):
                out[t] = np.mean(ok[max(0, t - h):t + h + 1]) >= G["stationary_frac"]
            return out
        return self.memo(("stat", o), run)

    def dist(self, a, b):
        return self.memo(("dist",) + tuple(sorted((a, b))), lambda: mvlib.dist(self.s.k(a), self.s.k(b)))

    def dball(self, o):
        fe = self.f[o]
        return np.hypot(fe.x - self.bx, fe.y - self.by)

    # ---- MOVE intervals (CU.P1) ----
    def moves(self, o, enter=None, exit_=None):
        enter = G["move_enter_mps"] if enter is None else enter
        exit_ = G["move_exit_mps"] if exit_ is None else exit_

        def run():
            fe = self.f[o]
            sp = np.nan_to_num(fe.speed, nan=0.0)
            thr = np.maximum(enter, G["move_enter_sigma_k"] * np.nan_to_num(fe.sig_speed, nan=99.0))
            ob = self.offball(o)
            k_in = int(G["move_enter_frames"])
            above = (sp >= thr) & ob
            ent = np.array([above[t:t + k_in].all() and t + k_in <= self.n for t in range(self.n)])
            stay = (sp >= exit_) & ob & np.isin(self.s.k(o).state, ["observed", "interp_short"])
            iv = mvlib.hysteresis(ent, stay, G["leg_min_s"], int(G["move_exit_frames"]) - 1)
            return iv
        return self.memo(("moves", o, enter, exit_), run)

    def in_move(self, o):
        def run():
            m = np.zeros(self.n, dtype=bool)
            for a, b in self.moves(o):
                m[a:b + 1] = True
            return m
        return self.memo(("inmove", o), run)

    def move_at(self, o, t, enter=None):
        for a, b in self.moves(o, enter):
            if a <= t <= b:
                return a, b
        return None

    # ---- chord turns (CU.R0 item 5, MP-13) ----
    def turn_curve(self, o):
        def run():
            fe = self.f[o]
            n, s, w = self.n, F(self.skip_s(o)), F(G["turn_window_s"])
            A = np.full(n, np.nan)
            c1 = np.full(n, np.nan)
            c2 = np.full(n, np.nan)
            sg = np.full(n, np.nan)
            for t in range(s + w, n - s - w):
                pre = (fe.x[t - s] - fe.x[t - s - w], fe.y[t - s] - fe.y[t - s - w])
                post = (fe.x[t + s + w] - fe.x[t + s], fe.y[t + s + w] - fe.y[t + s])
                l1, l2 = _norm(pre), _norm(post)
                if not (np.isfinite(l1) and np.isfinite(l2)) or min(l1, l2) < G["turn_min_chord_m"]:
                    continue
                A[t], c1[t], c2[t] = _ang(pre, post), l1, l2
                sd = math.sqrt(2) * np.nanmax(fe.sig_p[t - s - w:t + s + w + 1])
                sg[t] = math.degrees(math.hypot(sd / l1, sd / l2))
            return A, c1, c2, sg
        return self.memo(("turncurve", o), run)

    def turns(self, o, min_deg):
        """Turn events: local maxima of |A| (NMS +-turn_nms_s); t_turn = slowest frame of the peak plateau."""
        A, c1, c2, sg = self.turn_curve(o)
        sp = np.nan_to_num(self.f[o].speed, nan=0.0)
        aa = np.nan_to_num(np.abs(A), nan=0.0)
        h = F(G["turn_nms_s"])
        out = []
        for t in range(self.n):
            if aa[t] < min_deg:
                continue
            lo, hi = max(0, t - h), min(self.n, t + h + 1)
            if aa[t] < aa[lo:hi].max() or (aa[lo:t] == aa[t]).any():
                continue
            plateau = [j for j in range(lo, hi) if aa[j] >= 0.9 * aa[t]]
            tt = min(plateau, key=lambda j: sp[j])
            # fix R2 (loop 2): two NMS peaks whose plateaus collapse onto the same slowest frame are one turn;
            # keep the larger |A| (V / L / I emitted identical duplicate events)
            dup = [i for i, o_ in enumerate(out) if o_["t"] == tt]
            if dup:
                if abs(A[t]) <= abs(out[dup[0]]["A"]):
                    continue
                out.pop(dup[0])
            out.append(dict(t=tt, t_peak=t, A=float(A[t]), c_pre=float(c1[t]), c_post=float(c2[t]), sig=float(sg[t])))
        return out

    def leg_end(self, o, t, direction, max_s):
        """Far end of the leg adjacent to t: skip the plant, then walk until settled or max_s."""
        sp = np.nan_to_num(self.f[o].speed, nan=0.0)
        n, slow, settle = self.n, G["move_exit_mps"], int(G["move_exit_frames"])
        k = t + direction * F(self.skip_s(o))
        j = 0
        while 0 <= k < n and sp[k] < slow and j < F(G["plant_max_s"]):
            k += direction
            j += 1
        last, run = min(max(k, 0), n - 1), 0
        while 0 <= k < n and abs(k - t) <= F(max_s):
            if sp[k] < slow:
                run += 1
                if run >= settle:
                    break
            else:
                run, last = 0, k
            k += direction
        return last

    # ---- ball events ----
    def holder_runs(self):
        def run():
            raw, cur = [], None
            for t, h in enumerate(self.s.holder):
                if h is None:
                    continue
                if cur and cur[0] == h and t - cur[2] <= 3:
                    cur[2] = t
                else:
                    if cur:
                        raw.append(cur)
                    cur = [h, t, t]
            if cur:
                raw.append(cur)
            # drop blips (< 3 frames, e.g. the ball passing a screener), then bridge gaps <= holder_gap_s
            # between runs of the same holder
            runs = []
            for r_ in (r_ for r_ in raw if r_[2] - r_[1] >= 2):
                if runs and runs[-1][0] == r_[0] and r_[1] - runs[-1][2] <= F(G["holder_gap_s"]) + 1:
                    runs[-1][2] = r_[2]
                else:
                    runs.append(list(r_))
            return [tuple(r_) for r_ in runs]
        return self.memo("hruns", run)

    def passes(self):
        def run():
            out, R = [], self.holder_runs()
            for (a, a0, a1), (b, b0, b1) in zip(R, R[1:]):
                if a != b and 2 <= b0 - a1 <= F(G["pass_max_flight_s"]):
                    fa, fb = self.f[a], self.f[b]
                    out.append(dict(passer=a, receiver=b, t_rel=a1, t_catch=b0, x0=fa.x[a1], y0=fa.y[a1],
                                    x1=fb.x[b0], y1=fb.y[b0]))
            return out
        return self.memo("passes", run)

    def drives(self):
        """DRIVE (motion_starts): the holder goes from r > 6.1 to r < 3.05 within drive_max_s."""
        def run():
            out = []
            for h, a, b in self.holder_runs():
                fe = self.f[h]
                ins = [t for t in range(a, b + 1) if fe.r[t] < G["drive_in_r_m"]]
                if not ins:
                    continue
                t_in = ins[0]
                outs = [t for t in range(a, t_in) if fe.r[t] >= G["drive_out_r_m"]]
                if not outs or t_in - outs[-1] > F(G["drive_max_s"]):
                    continue
                t_d = outs[-1]
                kind = "baseline" if fe.m[t_in] < G["baseline_drive_m_deg"] else "middle"
                out.append(dict(driver=h, t=t_d, t_in=t_in, kind=kind, side=int(np.sign(fe.x[t_d]) or 1)))
            return out
        return self.memo("drives", run)

    def ball_screens(self):
        """Ball-screen moments (proxy for the screen family): handler within 1.2 m of a stationary teammate."""
        def run():
            out = []
            for h, a, b in self.holder_runs():
                for s_ in self.s.offense:
                    if s_ == h:
                        continue
                    d = self.dist(h, s_)
                    st = self.stationary(s_)
                    sp = np.nan_to_num(self.f[h].speed, nan=0.0)
                    mask = np.zeros(self.n, dtype=bool)
                    mask[a:b + 1] = (d[a:b + 1] <= G["screen_contact_m"]) & st[a:b + 1]
                    ivs = []
                    for i0, i1 in _intervals(mask):  # one screen: merge pieces of the same pair < 1.0 s apart
                        if ivs and i0 - ivs[-1][1] <= F(1.0):
                            ivs[-1] = (ivs[-1][0], i1)
                        else:
                            ivs.append((i0, i1))
                    for i0, i1 in ivs:
                        t_s = i0 + int(np.nanargmin(d[i0:i1 + 1]))
                        if sp[max(0, t_s - 9):t_s + 10].max() >= G["move_exit_mps"]:
                            out.append(dict(handler=h, screener=s_, t=t_s, d=float(d[t_s])))
            return out
        return self.memo("bscreens", run)

    def paint_touches(self):
        def run():
            out = []
            for h, a, b in self.holder_runs():
                fe = self.f[h]
                inside = (np.abs(fe.x) <= C["LANE_X"]) & (fe.y <= C["FT_Y"])
                for i0, _ in _intervals(inside[a:b + 1]):
                    out.append(dict(holder=h, t=a + i0))
            return out
        return self.memo("ptouch", run)

    def triggers(self, o):
        """All candidate ball-event triggers for player o (CU.R2), as (kind, t, actor)."""
        tr = [("drive", d["t"], d["driver"]) for d in self.drives() if d["driver"] != o]
        tr += [("ball_screen", s_["t"], s_["handler"]) for s_ in self.ball_screens() if o not in (s_["handler"], s_["screener"])]
        for p in self.passes():
            tr.append(("own_pass" if p["passer"] == o else "pass", p["t_rel"], p["passer"]))
            if p["receiver"] != o:
                tr.append(("catch", p["t_catch"], p["receiver"]))
        tr += [("paint_touch", q["t"], q["holder"]) for q in self.paint_touches() if q["holder"] != o]
        return tr

    # ---- off-ball screen contacts ----
    def contacts(self, u, a=0, b=None, max_d=None, need_stationary=True, need_moving=True, widen=False):
        """Off-ball u passes within max_d of a teammate s (stationary unless need_stationary=False).

        need_moving: u must be inside one of his MOVEs (False for set-ups where u starts next to s).
        widen (fix F09): candidates are taken at d <= max_d + contact_widen_k x sigma_pair (per frame), so a
        borderline pass-by is seen at all; every contact carries p = P(true d <= max_d) and its sigma."""
        b = self.n - 1 if b is None else b
        max_d = G["screen_contact_m"] if max_d is None else max_d
        out = []
        obu = self.offball(u) & (self.in_move(u) if need_moving else True)
        fu = self.f[u]
        for s_ in self.s.offense:
            if s_ == u:
                continue
            d = self.dist(u, s_)
            # pair sigma inflated by contact_sigma_scale: under AR(1)-correlated noise the CA-RTS sigma
            # understates the pair-distance error by 1.35-1.45 x (measured at sigma_p 0.2-0.5 m)
            sp = G["contact_sigma_scale"] * np.hypot(fu.sig_p, self.f[s_].sig_p)
            lim = max_d + (G["contact_widen_k"] * np.nan_to_num(sp, nan=0.0) if widen else 0.0)
            mask = np.zeros(self.n, dtype=bool)
            seg = (np.nan_to_num(d[a:b + 1], nan=99) <= (lim[a:b + 1] if widen else lim)) & obu[a:b + 1] \
                & self.offball(s_)[a:b + 1]
            if need_stationary:
                seg &= self.stationary(s_)[a:b + 1]
            mask[a:b + 1] = seg
            for i0, i1 in _intervals(mask):
                t_s = i0 + int(np.nanargmin(d[i0:i1 + 1]))
                sg = float(np.nan_to_num(sp[t_s], nan=0.3))
                out.append(dict(s=s_, t=t_s, d=float(d[t_s]), sig=sg, p=float(p_below(d[t_s], max_d, sg))))
        return sorted(out, key=lambda c: c["t"])

    def all_contacts(self, u):
        return self.memo(("contacts", u), lambda: self.contacts(u))

    # ---- matched defender (defense_full HMM proxy) ----
    def defender(self, u, a, b):
        if not self.s.defense:
            return None, True, None
        md = []
        for d_ in self.s.defense:
            dd = self.dist(u, d_)[a:b + 1]
            md.append((np.nanmean(dd) if np.isfinite(dd).any() else np.inf, d_))
        md.sort()
        amb = len(md) > 1 and md[1][0] - md[0][0] < G["def_ambiguous_m"]
        return md[0][1], amb, float(md[0][0])


def _ctx(scene) -> _Ctx:
    c = scene.__dict__.get("_cuts_ctx")
    if c is None:
        c = _Ctx(scene)
        scene.__dict__["_cuts_ctx"] = c
    return c


def _p(item, overrides):
    p = dict(PARAMS[item])
    unknown = set(overrides) - set(p) - {"min_conf"}
    if unknown:
        raise TypeError(f"{item}: unknown parameters {sorted(unknown)}")
    p.update(overrides)
    p.setdefault("min_conf", G["min_conf"])
    return p


def _sigd(fe, a, b):
    """Displacement sigma between frames a and b."""
    return math.hypot(fe.sig_p[a], fe.sig_p[b])


def _pframe_moving(fe, thr=None):
    thr = G["move_exit_mps"] if thr is None else thr
    return p_above(np.nan_to_num(fe.speed, nan=0.0), thr, np.nan_to_num(fe.sig_speed, nan=9.0))


def _contact_test(ts, ct, thr=None):
    """Soft contact test (fix F09): passes nominally when d <= thr; p = P(true d <= thr)."""
    thr = G["screen_contact_m"] if thr is None else thr
    return ts.flag("contact", ct["d"] <= thr, float(p_below(ct["d"], thr, ct["sig"])))


def _was_screener(c, o, t, before_s):
    """True when o was the screener of a ball screen in [t - before_s, t] (screen family precedence)."""
    return any(s_["screener"] == o and t - F(before_s) <= s_["t"] <= t for s_ in c.ball_screens())


def _received(c, o, a, b):
    hs = [t for t in range(a, min(c.n, b + 1)) if c.s.holder[t] == o]
    return (True, hs[0]) if hs else (False, None)


def _best_window_speed(fe, a, b, w_s):
    """Peak of the window-mean speed (chord over w_s / w_s) in [a, b] and its sigma (CU.R1)."""
    w = F(w_s)
    best, tb = -1.0, a
    for t in range(a, max(a, b - w) + 1):
        if t + w >= len(fe.x):
            break
        v = math.hypot(fe.x[t + w] - fe.x[t], fe.y[t + w] - fe.y[t]) / (w * DT)
        if np.isfinite(v) and v > best:
            best, tb = v, t
    sig = math.sqrt(2) * np.nanmax(fe.sig_p[a:b + 1]) / (w * DT) if b > a else 9.0
    return best, sig, tb


# ======================================================================================
# CU.P1 MOVE
# ======================================================================================
def detect_move(scene, **params):
    """Off-ball movement segments with legs split at chord turns (CU.P1)."""
    p = _p("move", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        turns = c.turns(o, p["split_turn_deg"])
        for a, b in c.moves(o):
            splits = [a] + [tt["t"] for tt in turns if a < tt["t"] < b] + [b]
            legs = []
            for l0, l1 in zip(splits, splits[1:]):
                ch = math.hypot(fe.x[l1] - fe.x[l0], fe.y[l1] - fe.y[l0])
                if ch >= p["leg_min_chord_m"] and (l1 - l0) * DT >= p["leg_min_s"]:
                    legs.append(dict(start=l0, end=l1, chord=round(ch, 2)))
            if not legs:
                continue
            ts = Tests()
            best = max(legs, key=lambda lg: lg["chord"])
            ts.ge("leg_chord", best["chord"], p["leg_min_chord_m"], _sigd(fe, best["start"], best["end"]))
            st = _path_stats(fe.x, fe.y, a, b)
            rec, tc = _received(c, o, b, b + 3)
            ev = _emit("move", {"player": o}, a, a, b, ts, [scene.k(o)], p_frame=_pframe_moving(fe), min_conf=p["min_conf"],
                       attrs=dict(t_onset=a, t_end=b, legs=legs, **{k: round(v, 3) if isinstance(v, float) else v for k, v in st.items()},
                                  Dr=round(float(fe.r[b] - fe.r[a]), 2), Dm=round(float(fe.m[b] - fe.m[a]), 1),
                                  mean_speed=round(float(np.nanmean(fe.speed[a:b + 1])), 2),
                                  peak_speed=round(float(np.nanmax(fe.speed[a:b + 1])), 2),
                                  start_region=c.region(o, a), end_region=c.region(o, b),
                                  received_ball=rec, bezier_ctrl=_bezier(fe.x, fe.y, a, b)))
            if ev:
                out.append(ev)
    return out


# ======================================================================================
# CU.P2 CUT gate
# ======================================================================================
def _cuts(c, o, p):
    """Generic CUT records for player o (CU.P2), cached per parameter set."""
    key = ("cuts", o, tuple(sorted(p.items())))

    def run():
        fe = c.f[o]
        recs = []
        turns60 = c.turns(o, p["end_turn_deg"])
        hc = p["frontcourt_y_max_m"]
        for a, b in c.moves(o):
            ta, nwin = a, 0
            # fix L4-02 (loop 4): a MOVE that starts in the backcourt is a transition run; its windows up to
            # transition_carry_s after the player crosses half court are not half-court cuts (rim runs and lane
            # sprints belong to the transition labels)
            t_carry = -1
            if fe.y[a] > hc:
                cross = np.flatnonzero(np.nan_to_num(fe.y[a:b + 1], nan=99.0) <= hc)
                t_carry = (a + int(cross[0]) if len(cross) else b) + F(p["transition_carry_s"])
            while ta <= b:
                nwin += 1  # windows searched in this MOVE so far (look-elsewhere correction, fix F21)
                # window: the largest displacement reached within window_s of t_a (margin, not first touch)
                hi_ = min(b, ta + F(p["window_s"]))
                dd = np.hypot(fe.x[ta:hi_ + 1] - fe.x[ta], fe.y[ta:hi_ + 1] - fe.y[ta])
                tb = ta + int(np.nanargmax(dd)) if len(dd) > 1 and np.nanmax(dd) >= p["disp_m"] else None
                if tb is None:
                    ta += 3
                    continue
                if not fe.y[ta] <= hc or ta <= t_carry:  # backcourt or transition carry: not a half-court cut
                    ta += 3
                    continue
                if not fe.y[tb] <= hc:  # fix L4-02: a run back over half court is not a half-court cut either
                    ta += 3
                    continue
                # onset: latest upward 1.5 m/s crossing at or before ta (search back <= 1.0 s)
                on = ta
                for t in range(ta, max(a, ta - F(p["onset_search_s"])) - 1, -1):
                    if t > 0 and fe.speed[t - 1] < G["move_enter_mps"] <= fe.speed[t]:
                        on = t
                        break
                else:
                    on = a if ta - a <= F(p["onset_search_s"]) else ta
                # end: first of catch, MOVE exit, a >= 60 deg turn after tb, rim-stop, onset + 4 s
                ends = [b, on + F(p["max_s"])]
                rec, tcat = _received(c, o, tb, b + 3)
                if rec:
                    ends.append(tcat)
                ends += [tt["t"] for tt in turns60 if tt["t"] > tb]
                vr = np.nan_to_num(fe.vr, nan=0.0)
                run_ = 0
                for t in range(tb, min(b, on + F(p["max_s"])) + 1):
                    if fe.r[t] - fe.r[on] <= -p["rim_dir_dr_m"]:
                        run_ = run_ + 1 if vr[t] <= p["rim_stop_vr_mps"] else 0
                        if run_ >= F(p["rim_stop_s"]):
                            ends.append(t - run_ + 1)
                            break
                end = int(min(min(ends), c.n - 1))
                pk = float(np.nanmax(fe.speed[ta:tb + 1]))
                disp = math.hypot(fe.x[tb] - fe.x[ta], fe.y[tb] - fe.y[ta])
                hs = np.nan_to_num(fe.speed[on:end + 1], nan=0) >= p["hard_cut_mps"]
                hard = any(i1 - i0 + 1 >= F(p["hard_cut_s"]) for i0, i1 in _intervals(hs))
                recs.append(dict(o=o, on=on, ta=ta, tb=tb, end=end, move=(a, b), disp=disp, peak=pk, nwin=nwin,
                                 t_pk=ta + int(np.nanargmax(fe.speed[ta:tb + 1])), hard=hard,
                                 received=rec and tcat <= end, t_catch=tcat if rec and tcat <= end else None))
                ta = max(end, tb) + 1
        return recs
    return c.memo(key, run)


def _cut_tests(c, rec, p):
    """CUT tests (fix F21): displacement with its sigma inflated by sqrt(1 + ln n_windows) for the windows
    searched in the MOVE; window-mean speed disp / (t_b - t_a) >= mean_mps; best speed_window_s-mean speed
    >= peak_mps (sigma sqrt2 sigma_pos / W). The instantaneous peak (biased about +1 sigma) is stored only."""
    fe = c.f[rec["o"]]
    ta, tb = rec["ta"], rec["tb"]
    ts = Tests()
    infl = math.sqrt(1.0 + math.log(max(1, rec.get("nwin", 1))))
    ts.ge("disp", rec["disp"], p["disp_m"], _sigd(fe, ta, tb) * infl)
    w_s = max(tb - ta, 1) * DT
    # fix F21r (loop 2): a window picked by the sliding search (nwin > 1) must clear mean_mps by
    # lookelse_k x sigma x sqrt(ln nwin) (expected excess of the best of n noisy windows); under the weakest-link
    # conf any positive margin gave conf > 0.5, so a 1.7 m/s jog still passed in 2 of 10 runs. The best
    # speed_window_s speed is a max over the window too and gets the same margin.
    sig_ms = math.sqrt(2) * float(np.nanmax(fe.sig_p[ta:tb + 1])) / w_s
    shift = p["lookelse_k"] * sig_ms * math.sqrt(math.log(max(1, rec.get("nwin", 1))))
    ts.ge("mean_speed", rec["disp"] / w_s, p["mean_mps"] + shift, sig_ms)
    v5, sv, _ = _best_window_speed(fe, ta, tb, p["speed_window_s"])
    # the best of n_ind ~ (t_b - t_a) / speed_window_s independent windows gets the same look-elsewhere margin
    n_ind = max(1.0, (tb - ta) * DT / p["speed_window_s"])
    ts.ge("peak_speed", v5, p["peak_mps"] + p["lookelse_k"] * sv * math.sqrt(math.log(n_ind)), sv)
    return ts


def _cut_attrs(c, rec):
    o, on, end = rec["o"], rec["on"], rec["end"]
    fe = c.f[o]
    st = _path_stats(fe.x, fe.y, on, end)
    did, amb, _ = c.defender(o, on, end)
    sep = None
    if did is not None:
        dd = c.dist(o, did)
        sep = round(float(dd[end] - dd[on]), 2)
    bs = c.bs[on]
    side = "none" if bs == 0 else ("strong" if fe.x[on] * bs >= 0.9 else ("weak" if fe.x[on] * bs <= -0.9 else "none"))
    delayed = any(d["driver"] != o and on - F(3.0) <= d["t"] <= on - F(1.0) for d in c.drives())
    stampede = bool(rec["t_catch"] is not None and fe.speed[rec["t_catch"]] >= PARAMS["cut"]["hard_cut_mps"])
    return dict(t_onset=on, t_a=rec["ta"], t_b=rec["tb"], t_end=end, displacement_m=round(rec["disp"], 2),
                mean_speed=round(float(np.nanmean(fe.speed[on:end + 1])), 2), peak_speed=round(rec["peak"], 2),
                hard_cut=rec["hard"], received_ball=rec["received"], t_catch=rec["t_catch"],
                start_region=c.region(o, on), end_region=c.region(o, end), start_r=round(float(fe.r[on]), 2),
                end_r=round(float(fe.r[end]), 2), Dr=round(float(fe.r[end] - fe.r[on]), 2),
                Dm=round(float(fe.m[end] - fe.m[on]), 1), roundness_m=round(st["roundness_m"], 2),
                roundness_side=st["roundness_side"], straightness=round(float(st["straightness"]), 3),
                defender_id=did, defender_ambiguous=amb, separation_gain_m=sep, ball_side_at_onset=side,
                delayed_cut=delayed, stampede=stampede)


def detect_cut(scene, **params):
    """Generic off-ball CUT: >= 3.0 m within 1.5 s with peak speed >= 2.5 m/s (CU.P2)."""
    p = _p("cut", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        for rec in _cuts(c, o, p):
            ts = _cut_tests(c, rec, p)
            ev = _emit("cut", {"cutter": o}, rec["on"], rec["on"], rec["end"], ts, [scene.k(o)],
                       p_frame=_pframe_moving(fe), attrs=_cut_attrs(c, rec), min_conf=p["min_conf"])
            if ev:
                out.append(ev)
    return out


def _cut_recs(c, o):
    """CUT records with the canonical (YAML) parameters, used by every derived label."""
    return _cuts(c, o, _p("cut", {}))


# ======================================================================================
# CU.P3 basket cut, CU.P4 dive, CU.P5 45, front cut
# ======================================================================================
def _basket(c, rec, p):
    """Shared basket-cut evaluation -> (Tests, attrs) or None when a hard precondition fails."""
    o, on, end = rec["o"], rec["on"], rec["end"]
    fe = c.f[o]
    if _was_screener(c, o, on, p["screener_precedence_s"]):
        return None  # ROLL / SLIP belong to the screen family (CU.R3 item 1)
    # fix F06: a teammate standing near the path does not suppress the label; when a screen-cut class also
    # fires, resolve() ranks it above the basket cut (CU.R3 item 2). The contacts are stored for audit.
    near = c.contacts(o, on, end)
    seg = slice(on, end + 1)
    i_min = on + int(np.nanargmin(fe.r[seg]))
    min_r = float(fe.r[i_min])
    dr = float(fe.r[i_min] - fe.r[on])
    ts = _cut_tests(c, rec, PARAMS["cut"])
    ts.le("Dr", dr, p["dr_max_m"], _sigd(fe, on, i_min))
    partial = min_r > p["rim_end_r_m"]
    if partial:
        ts.le("min_r_partial", min_r, p["partial_r_max_m"], fe.sig_p[i_min])
    else:
        ts.le("min_r", min_r, p["rim_end_r_m"], fe.sig_p[i_min])
    # heading vs rim bearing on the main leg (frames with speed >= 2.0 m/s)
    fr = [t for t in range(rec["ta"], rec["tb"] + 1) if fe.speed[t] >= p["bearing_min_mps"]]
    if fr:
        angs = [abs(_ang((_vel(c, o, t)), (-fe.x[t], -fe.y[t]))) for t in fr]
        sig_a = math.degrees(np.nanmean([fe.sig_speed[t] / fe.speed[t] for t in fr])) / math.sqrt(max(1, len(fr) / 9))
        ts.le("rim_bearing", float(np.mean(angs)), p["bearing_max_deg"], sig_a)
    else:
        ts.flag("rim_bearing", False)
    p_out = max(float(p_above(fe.sdp[on], 0.0, fe.sig_p[on])), float(p_above(fe.r[on], p["start_out_r_m"], fe.sig_p[on])))
    ts.flag("start_outside_paint", fe.sdp[on] > 0 or fe.r[on] >= p["start_out_r_m"], p_out)
    at = _cut_attrs(c, rec)
    at.update(min_r=round(min_r, 2), t_min_r=i_min, variant="partial" if partial else "rim",
              screen_contacts=[(q["s"], q["t"], round(q["d"], 2)) for q in near],
              is_cross_court=bool(np.sign(fe.x[on]) != np.sign(fe.x[end]) and abs(fe.x[on]) > 0.9 and abs(fe.x[end]) > 0.9),
              end_spot=[s_ for s_ in ("restricted_area", "front_of_rim", "low_post", "dunker_spot") if c.spot(o, s_)[i_min]])
    return ts, at, i_min


def _vel(c, o, t):
    k = c.s.k(o)
    return (k.vx[t], k.vy[t])


def _basket_events(c, p):
    out = []
    for o in c.s.offense:
        for rec in _cut_recs(c, o):
            r_ = _basket(c, rec, p)
            if r_ is None:
                continue
            out.append((rec, r_))
    return out


def detect_cut_basket(scene, **params):
    """Basket cut (CU.P3): Dr <= -3.0 m, min r <= 2.0 m (partial: <= 3.5 m), rim-directed, unscreened."""
    p = _p("cut_basket", params)
    c = _ctx(scene)
    out = []
    for rec, (ts, at, _) in _basket_events(c, p):
        fe = c.f[rec["o"]]
        ev = _emit("cut_basket", {"cutter": rec["o"]}, rec["on"], rec["on"], rec["end"], ts, [scene.k(rec["o"])],
                   p_frame=_pframe_moving(fe), attrs=at, min_conf=p["min_conf"])
        if ev:
            out.append(ev)
    return out


def detect_cut_dive(scene, **params):
    """Dive (CU.P4): a rim basket cut that is straight and aimed at the rim."""
    p = _p("cut_dive", params)
    c = _ctx(scene)
    out = []
    for rec, (ts, at, i_min) in _basket_events(c, PARAMS["cut_basket"]):
        if at["variant"] != "rim":
            continue
        o, on = rec["o"], rec["on"]
        fe = c.f[o]
        fr = [t for t in range(on, i_min + 1) if fe.speed[t] >= p["min_mps"] and fe.r[t] >= p["min_r_m"]]
        if len(fr) < 3:
            continue
        pf = []
        for t in fr:
            a_ = abs(_ang(_vel(c, o, t), (-fe.x[t], -fe.y[t])))
            sa = math.degrees(fe.sig_speed[t] / fe.speed[t])
            pf.append(float(p_below(a_, p["bearing_max_deg"], sa)))
        ts.frac("rimward_frames", pf, p["rimward_frac"])
        st = _path_stats(fe.x, fe.y, on, i_min)
        ts.ge("straightness", st["straightness"], p["straightness_min"], 0.02)
        ts.le("roundness", st["roundness_m"], p["roundness_max_m"], float(np.nanmax(fe.sig_p[on:i_min + 1])))
        at2 = dict(at, pct_frames_rimward=round(float(np.mean(np.array(pf) >= 0.5)), 2))
        ev = _emit("cut_dive", {"cutter": o}, on, on, rec["end"], ts, [scene.k(o)], p_frame=_pframe_moving(fe),
                   attrs=at2, min_conf=p["min_conf"])
        if ev:
            out.append(ev)
    return out


def detect_cut_45(scene, **params):
    """45 cut (CU.P5): a basket cut from the wing along a 30-60 deg line (sub-label of basket)."""
    p = _p("cut_45", params)
    c = _ctx(scene)
    out = []
    for rec, (ts, at, i_min) in _basket_events(c, PARAMS["cut_basket"]):
        o, on = rec["o"], rec["on"]
        fe = c.f[o]
        sig_m = math.degrees(fe.sig_p[on] / max(fe.r[on], 1.0))
        ts.band("start_m", float(fe.m[on]), p["m_lo_deg"], p["m_hi_deg"], sig_m)
        ts.ge("start_r", float(fe.r[on]), p["start_r_min_m"], fe.sig_p[on])
        fr = [t for t in range(on, i_min + 1) if fe.r[t] >= p["m_eval_r_min_m"]]
        pf = [float(min(p_above(fe.m[t], p["m_lo_deg"], math.degrees(fe.sig_p[t] / fe.r[t])),
                        p_below(fe.m[t], p["m_hi_deg"], math.degrees(fe.sig_p[t] / fe.r[t])))) for t in fr]
        ts.frac("m_band_frames", pf, p["m_band_frac"])
        at2 = dict(at, m_mean=round(float(np.nanmean(fe.m[on:i_min + 1])), 1), rim_45=at["variant"] == "rim")
        ev = _emit("cut_45", {"cutter": o}, on, on, rec["end"], ts, [scene.k(o)], p_frame=_pframe_moving(fe),
                   attrs=at2, min_conf=p["min_conf"])
        if ev:
            out.append(ev)
    return out


def detect_cut_front(scene, **params):
    """Front (face) cut: a rim basket cut that passes the defender on the ball side (in front)."""
    p = _p("cut_front", params)
    c = _ctx(scene)
    out = []
    for rec, (ts, at, i_min) in _basket_events(c, PARAMS["cut_basket"]):
        if at["variant"] != "rim":
            continue
        o, on = rec["o"], rec["on"]
        fe = c.f[o]
        did, amb, _ = c.defender(o, max(0, on - F(1.0)), on)
        if did is None:
            continue  # needs the defender track
        dd = c.dist(o, did)
        fd = c.f[did]
        # pass-by (fix F12): the first frame the cutter is level with his man (r_cutter <= r_defender); else the
        # closest approach after the cutter has moved >= pass_by_moved_m from his onset position
        lvl = [k for k in range(on, i_min + 1) if fe.r[k] <= fd.r[k]]
        if lvl:
            tc = lvl[0]
        else:
            mv = [k for k in range(on, i_min + 1)
                  if math.hypot(fe.x[k] - fe.x[on], fe.y[k] - fe.y[on]) >= p["pass_by_moved_m"]]
            tc = (min(mv, key=lambda k: dd[k]) if mv else on + int(np.nanargmin(dd[on:i_min + 1])))
        db_c = math.hypot(fe.x[tc] - c.bx[tc], fe.y[tc] - c.by[tc])
        db_d = math.hypot(fd.x[tc] - c.bx[tc], fd.y[tc] - c.by[tc])
        sig = math.hypot(fe.sig_p[tc], fd.sig_p[tc])
        ts.ge("ball_side_of_defender", db_d - db_c, p["front_margin_m"], sig)
        pass_and_cut = any(q["passer"] == o and on - F(p["pass_window_s"]) <= q["t_rel"] <= on for q in c.passes())
        ev = _emit("cut_front", {"cutter": o, "defender": did}, on, on, rec["end"], ts, [scene.k(o), scene.k(did)],
                   p_frame=_pframe_moving(fe), attrs=dict(at, t_pass_by=tc, pass_and_cut=pass_and_cut),
                   cap=G["identity_cap"] if amb else None, min_conf=p["min_conf"])
        if ev:
            out.append(ev)
    return out


# ======================================================================================
# CU.P6 backdoor
# ======================================================================================
def detect_cut_backdoor(scene, **params):
    """Backdoor (CU.P6): step-out or deny set-up, reversal >= 120 deg (chord test), behind the defender, rim."""
    p = _p("cut_backdoor", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        cands = [(tt["t"], tt, "step") for tt in c.turns(o, p["turn_min_deg"])]
        # deny-only branch: rim-ward cut onsets with the defender on the passing line beforehand
        for rec in _cut_recs(c, o):
            cands.append((rec["on"], None, "deny"))
        seen = []
        for t_rev, tt, kind in sorted(cands, key=lambda z: z[0]):
            if any(abs(t_rev - s_) <= F(p["dedup_s"]) for s_ in seen):
                continue
            if not c.offball(o)[t_rev]:
                continue
            hi = min(c.n - 1, t_rev + F(p["rim_within_s"]))
            if hi <= t_rev + 3:
                continue
            i_min = t_rev + int(np.nanargmin(fe.r[t_rev:hi + 1]))
            # fix F10: a rim cut that uses an off-ball screen after the reversal belongs to the screen cuts
            # (chin, UCLA, shuffle), as CU.R3 item 2 does for the basket cut
            if c.contacts(o, max(0, t_rev - F(p["screen_skip_before_s"])), i_min):
                continue
            ts = Tests()
            did, amb, _ = c.defender(o, max(0, t_rev - F(1.0)), t_rev)
            setup = []
            if tt is not None:
                ts.ge("reversal", abs(tt["A"]), p["turn_min_deg"], tt["sig"])
                a0 = max(0, t_rev - F(c.skip_s(o) + G["turn_window_s"]))
                a1 = t_rev - F(c.skip_s(o))
                pre = math.hypot(fe.x[a1] - fe.x[a0], fe.y[a1] - fe.y[a0])
                d_out = fe.r[a1] - fe.r[a0]
                d_ball = c.dball(o)[a0] - c.dball(o)[a1]
                if pre >= p["setup_chord_m"] and (d_out >= p["setup_dr_m"] or d_ball >= p["setup_dr_m"]):
                    setup.append("step")
            # overplay (the ball-you-man stance turned toward the ball): the defender's bearing from the
            # cutter is nearer the bearing to the ball than the bearing to the rim (margin in deg)
            def overplay(t):
                fd_ = c.f[did]
                dv = (fd_.x[t] - fe.x[t], fd_.y[t] - fe.y[t])
                bv = (c.bx[t] - fe.x[t], c.by[t] - fe.y[t])
                rv = (-fe.x[t], -fe.y[t])
                if not (np.isfinite(bv[0]) and _norm(dv) > 0.1):
                    return np.nan, 99.0
                sg = math.degrees(math.hypot(fe.sig_p[t], fd_.sig_p[t]) / _norm(dv))
                return abs(_ang(dv, rv)) - abs(_ang(dv, bv)), sg
            def in_lane(t):
                """Deny stance (fix F10): the defender sits in the passing lane, i.e. within deny_lane_m of the
                cutter -> ball segment, at a projection fraction in [deny_frac_lo, deny_frac_hi]."""
                fd_ = c.f[did]
                bv = (c.bx[t] - fe.x[t], c.by[t] - fe.y[t])
                L2 = bv[0] ** 2 + bv[1] ** 2
                if not (np.isfinite(L2) and L2 > 0.25):
                    return False
                dv = (fd_.x[t] - fe.x[t], fd_.y[t] - fe.y[t])
                fr = (dv[0] * bv[0] + dv[1] * bv[1]) / L2
                perp = abs(dv[0] * bv[1] - dv[1] * bv[0]) / math.sqrt(L2)
                return bool(p["deny_frac_lo"] <= fr <= p["deny_frac_hi"] and perp <= p["deny_lane_m"]
                            and c.dist(o, did)[t] <= p["deny_dist_m"])
            deny_s = 0.0
            if did is not None:
                cnt = sum(1 for t in range(max(0, t_rev - F(1.0)), t_rev + 1) if in_lane(t))
                deny_s = cnt * DT
                if deny_s >= p["deny_min_s"]:
                    setup.append("deny")
            if kind == "deny" and "deny" not in setup:
                continue
            if kind == "deny":
                # fix R1 (loop 2): the deny-only branch starts a rim-ward cut. The onset of a step-OUT (the set-up
                # of a step backdoor, ~0.7 s before the plant) is not one; with the 2.0 s rim window it passed and
                # claimed the dedup_s window before the true reversal.
                k1 = min(c.n - 1, t_rev + F(p["deny_rimward_s"]))
                ts.le("deny_rimward", float(fe.r[k1] - fe.r[t_rev]), -p["deny_rimward_dr_m"], _sigd(fe, t_rev, k1))
            ts.flag("setup", bool(setup))
            ts.le("min_r", float(fe.r[i_min]), G["rim_end_r_m"], fe.sig_p[i_min])
            ts.le("Dr", float(fe.r[i_min] - fe.r[t_rev]), -p["dr_m"], _sigd(fe, t_rev, i_min))
            long_ = fe.r[t_rev] >= p["start_r_m"] or fe.d3[t_rev] >= p["start_d3_m"]
            short = (not long_) and fe.r[t_rev] >= p["short_r_min_m"]
            ts.flag("start", long_ or short)
            behind, cap = None, G["identity_cap"]
            if did is not None:
                fd = c.f[did]
                t_ov = max(0, t_rev - F(c.skip_s(o) + 0.2))  # stance just before the plant
                ov, sg = overplay(t_ov)
                sig = math.hypot(fe.sig_p[t_rev], fd.sig_p[t_rev])
                passed_r = np.nanmin(fe.r[t_rev:i_min + 1] - fd.r[t_rev:i_min + 1])
                behind = bool(ov > 0 and passed_r < 0)
                ts.ge("defender_overplay", ov, 0.0, sg)
                ts.le("passes_defender_r", float(passed_r), 0.0, sig)
                cap = G["identity_cap"] if amb else None
            h = scene.holder[t_rev]
            dribble_at = False
            if h is not None and h != o:
                d_h = c.dist(o, h)
                lo = max(0, t_rev - F(p["dribble_at_s"]))
                dribble_at = bool(np.nanmax(d_h[lo:t_rev + 1]) - d_h[t_rev] >= p["dribble_at_close_m"])
            rec_, tcat = _received(c, o, t_rev, i_min + F(0.5))
            ev = _emit("cut_backdoor", {"cutter": o, "defender": did, "ball_handler": h}, t_rev,
                       max(0, t_rev - F(p["start_before_s"])),
                       i_min, ts, [scene.k(o)], p_frame=_pframe_moving(fe), cap=cap, min_conf=p["min_conf"],
                       attrs=dict(t_rev=t_rev, Dpsi_rev=None if tt is None else round(tt["A"], 1),
                                  setup_kind="+".join(setup) or None, deny_duration_s=round(deny_s, 2),
                                  r_rev=round(float(fe.r[t_rev]), 2), min_r=round(float(fe.r[i_min]), 2),
                                  variant="standard" if long_ else "short", behind=behind,
                                  dribble_at=dribble_at, received_ball=rec_, t_catch=tcat,
                                  pass_fake=None, lob=None))
            if ev:
                seen.append(t_rev)
                out.append(ev)
    return out


# ======================================================================================
# CU.P7 flash
# ======================================================================================
def detect_cut_flash(scene, **params):
    """Flash (CU.P7): from behind the defence toward the ball into the high/mid/low post, unscreened."""
    p = _p("cut_flash", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        for rec in _cut_recs(c, o):
            on = rec["on"]
            hi = min(c.n - 1, on + F(p["end_within_s"]))
            if c.contacts(o, on, hi):
                continue
            if not np.isfinite(c.bx[on]):
                continue
            bvec = (c.bx[on] - fe.x[on], c.by[on] - fe.y[on])
            bl = _norm(bvec)
            if bl < 1.0:
                continue
            ux, uy = bvec[0] / bl, bvec[1] / bl
            bs = c.bs[on]
            interior = fe.r[on] <= p["interior_r_m"]
            weak = bs != 0 and fe.x[on] * bs <= -0.9 and fe.y[on] <= p["weak_y_max_m"] and fe.d3[on] < p["weak_d3_max_m"]
            if not (interior or weak):
                continue
            # arrival: the frame of greatest progress toward the ball within end_within_s; it must lie in
            # an end region (high: high_post_area/elbow/nail; mid: ball-side mid_post/pinch_post;
            # low: ball-side low_post/block reached from the other side)
            e = min(hi, max(rec["end"], rec["tb"]))
            projs = [(fe.x[t] - fe.x[on]) * ux + (fe.y[t] - fe.y[on]) * uy for t in range(on, e + 1)]
            t_end = on + int(np.nanargmax(projs))
            proj = float(projs[t_end - on])
            bst = c.bs[t_end]
            kind = None
            if c.in_any(o, ("high_post_area", "elbow", "nail"))[t_end]:
                kind = "high"
            elif bst != 0 and fe.x[t_end] * bst > 0 and c.in_any(o, ("mid_post", "pinch_post"))[t_end]:
                kind = "mid"
            elif bst != 0 and fe.x[t_end] * bst > 0 and fe.x[on] * bst < 0 and c.in_any(o, ("low_post", "block"))[t_end] \
                    and float(np.nanmin(fe.y[on:t_end + 1])) >= p["low_min_y_m"]:
                kind = "low"  # fix F17: a path through the dunker band (y < 0.5334) is a baseline run, not a flash
            if kind is None:
                continue
            dv = (fe.x[t_end] - fe.x[on], fe.y[t_end] - fe.y[on])
            alpha = abs(_ang(dv, bvec))
            ts = Tests()
            ts.ge("toward_ball_disp", proj, p["toward_m"], _sigd(fe, on, t_end))
            ts.le("alpha_ball", alpha, p["alpha_max_deg"], math.degrees(_sigd(fe, on, t_end) / max(_norm(dv), 0.5)))
            ts.flag("start_behind_defence", True)
            stack = sum(1 for q in scene.offense if q != o and abs(c.f[q].x[on] - fe.x[on]) <= p["stack_dx_m"]
                        and abs(c.f[q].x[on]) <= C["LANE_X"]) >= 2 and fe.r[on] < p["stack_r_m"]
            rec_, tcat = _received(c, o, on, t_end + F(1.0))
            opn = None
            if tcat is not None and scene.defense:
                opn = round(float(min(c.dist(o, d_)[tcat] for d_ in scene.defense)), 2)
            ev = _emit("cut_flash", {"cutter": o, "ball_handler": scene.holder[on]}, on, on, t_end, ts, [scene.k(o)],
                       p_frame=_pframe_moving(fe), min_conf=p["min_conf"],
                       attrs=dict(flash_kind=kind, stack_flash=stack, zone_flash=None, t_arrival=t_end,
                                  toward_ball_m=round(proj, 2), Dd_ball=round(float(c.dball(o)[t_end] - c.dball(o)[on]), 2),
                                  received_ball=rec_, receiver_open_m=opn))
            if ev:
                out.append(ev)
    return out


# ======================================================================================
# CU.P8 V, CU.P9 L, CU.P10 I (chord-turn shapes)
# ======================================================================================
def _legs(c, o, t, max_s):
    a = c.leg_end(o, t, -1, max_s)
    b = c.leg_end(o, t, +1, max_s)
    return a, b


def detect_cut_v(scene, **params):
    """V-cut (CU.P8): in-leg toward the rim/defender, reversal >= 120 deg, out-leg to the perimeter."""
    p = _p("cut_v", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        for tt in c.turns(o, p["turn_soft_deg"]):
            t = tt["t"]
            if not c.offball(o)[t]:
                continue
            a, b = _legs(c, o, t, p["leg_max_s"])
            in_len = math.hypot(fe.x[t] - fe.x[a], fe.y[t] - fe.y[a])
            out_len = math.hypot(fe.x[b] - fe.x[t], fe.y[b] - fe.y[t])
            dr_in, dr_out = fe.r[t] - fe.r[a], fe.r[b] - fe.r[t]
            dy_in = fe.y[t] - fe.y[a]
            post_v = bool(c.in_any(o, ("low_post", "block"))[a] and c.in_any(o, ("high_post_area", "elbow"))[t]
                          and dy_in >= p["post_v_dy_m"])
            ts = Tests()
            ts.ge("turn", abs(tt["A"]), p["turn_min_deg"], tt["sig"])
            ts.ge("in_leg", in_len, p["leg_min_m"], _sigd(fe, a, t))
            if not post_v:
                did, _, _ = c.defender(o, a, t)
                to_def = did is not None and c.dist(o, did)[a] - c.dist(o, did)[t] >= p["in_dr_m"]
                ts.flag("in_toward_rim", dr_in <= -p["in_dr_m"] or to_def,
                        max(float(p_below(dr_in, -p["in_dr_m"], _sigd(fe, a, t))), 1.0 if to_def else 0.0))
            ts.ge("out_leg", out_len, p["leg_min_m"], _sigd(fe, t, b))
            ts.ge("out_Dr", dr_out, p["out_dr_m"], _sigd(fe, t, b))
            ts.ge("out_peak", float(np.nanmax(fe.speed[t:b + 1])), G["cut_peak_mps"], float(np.nanmedian(fe.sig_speed[t:b + 1])))
            rec_, tcat = _received(c, o, t, b + 3)
            ts.flag("out_end", fe.d3[b] >= p["end_d3_m"] or rec_)
            # out-leg must start promptly (separates a V from a basket cut then a relocation)
            mv = [k for k in range(t, min(c.n, t + F(p["out_start_s"]) + 1)) if fe.speed[k] >= G["move_enter_mps"]]
            ts.flag("out_prompt", bool(mv))
            min_r_in = float(np.nanmin(fe.r[a:t + 1]))
            back_out = any(fe.d3[k] >= p["end_d3_m"] for k in range(t, min(c.n, t + F(p["return_s"]) + 1)))
            lo = p["turn_r_lo_ext_m"] if back_out else p["turn_r_lo_m"]
            ts.band("turn_r", float(fe.r[t]), lo, p["turn_r_hi_m"], fe.sig_p[t])
            ts.flag("in_not_rim", min_r_in > (p["turn_r_lo_ext_m"] if back_out else G["rim_end_r_m"]))
            ts.flag("whole", b - a <= F(p["max_s"]))  # frame count (F02 class)
            pv = float(p_above(abs(tt["A"]), p["turn_min_deg"], tt["sig"]))
            ev = _emit("cut_v", {"cutter": o}, t, a, b, ts, [scene.k(o)], p_frame=None, min_conf=p["min_conf"],
                       attrs=dict(t_turn=t, Dpsi_turn=round(tt["A"], 1), in_leg_len=round(in_len, 2),
                                  out_leg_len=round(out_len, 2), r_turn=round(float(fe.r[t]), 2),
                                  variant="post_v" if post_v else "standard", received_ball=rec_,
                                  p_v_vs_l=round(pv, 3), turn_spot=c.region(o, t)))
            if ev:
                out.append(ev)
    return out


def detect_cut_l(scene, **params):
    """L-cut (CU.P9): up the lane line >= 2.0 m, 60-120 deg turn at y 3.0-5.5, out toward the sideline."""
    p = _p("cut_l", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        for tt in c.turns(o, min(p["turn_lo_deg"], p["turn_wing_lo_deg"]) - 15):
            t = tt["t"]
            if not c.offball(o)[t]:
                continue
            a, b = _legs(c, o, t, p["leg_max_s"])
            l1 = (fe.x[t] - fe.x[a], fe.y[t] - fe.y[a])
            l2 = (fe.x[b] - fe.x[t], fe.y[b] - fe.y[t])
            ts = Tests()
            wing = False
            up = abs(_ang((0, 1), l1))
            # fix F20: wing_l (arc then down to the corner) turns 45-55 deg on real paths, so it has its own lower edge
            lo_deg = p["turn_lo_deg"] if up <= p["leg1_dir_deg"] + 20 else p["turn_wing_lo_deg"]
            ts.band("turn", abs(tt["A"]), lo_deg, p["turn_hi_deg"], tt["sig"])
            ts.ge("leg1", _norm(l1), p["leg_min_m"], _sigd(fe, a, t))
            ts.ge("leg2", _norm(l2), p["leg_min_m"], _sigd(fe, t, b))
            if up <= p["leg1_dir_deg"] + 20:
                ts.le("leg1_up", up, p["leg1_dir_deg"], math.degrees(_sigd(fe, a, t) / max(_norm(l1), 0.5)))
                lane = [float(min(p_above(abs(fe.x[k]), p["lane_x_lo_m"], fe.sig_p[k]),
                                  p_below(abs(fe.x[k]), p["lane_x_hi_m"], fe.sig_p[k]))) for k in range(a, t + 1)]
                ts.frac("leg1_lane_band", lane, p["lane_frac"])
                ts.le("start_r", float(fe.r[a]), p["start_r_max_m"], fe.sig_p[a])
                ts.band("turn_y", float(fe.y[t]), p["turn_y_lo_m"], p["turn_y_hi_m"], fe.sig_p[t])
                ts.ge("leg2_out", float(abs(fe.x[b]) - abs(fe.x[t])), p["leg2_dx_m"], _sigd(fe, t, b))
            else:  # wing_l: along the arc, then toward the corner
                wing = True
                ts.le("leg1_along_arc", float(abs(fe.r[t] - fe.r[a])), p["wing_arc_dr_m"], _sigd(fe, a, t))
                ts.ge("leg1_r", float(fe.r[a]), p["wing_r_min_m"], fe.sig_p[a])
                ts.le("leg2_Dm", float(fe.m[b] - fe.m[t]), -p["wing_dm_deg"], math.degrees(_sigd(fe, t, b) / max(fe.r[b], 1)))
                ts.flag("leg2_corner", bool(c.in_any(o, ("corner_three", "wing_low"))[b]))
            rec_, _ = _received(c, o, t, b + 3)
            ts.flag("end", fe.d3[b] >= p["end_d3_m"] or rec_)
            ts.flag("whole", b - a <= F(p["max_s"]))  # frame count (F02 class)
            pl = float(p_below(abs(tt["A"]), p["turn_hi_deg"], tt["sig"]))
            ev = _emit("cut_l", {"cutter": o}, t, a, b, ts, [scene.k(o)], min_conf=p["min_conf"],
                       attrs=dict(t_turn=t, Dpsi_turn=round(tt["A"], 1), leg1_len=round(_norm(l1), 2),
                                  leg2_len=round(_norm(l2), 2), variant="wing_l" if wing else "standard",
                                  received_ball=rec_, p_l_vs_v=round(pl, 3), turn_spot=c.region(o, t)))
            if ev:
                out.append(ev)
    return out


def detect_cut_i(scene, **params):
    """I-cut (CU.P10): step in >= 1.0 m, reverse >= 150 deg, straight back out along the same line."""
    p = _p("cut_i", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        # fix F08r (loop 2): the high-noise-tier smoother (Q_HIGH_NOISE) cuts the apex of a short out-and-back:
        # a 1.48 m in-leg reads 0.91 m on average at sigma_p 0.5 (0.32-1.39 m over 10 seeds; 1.31 m at 0.2), a
        # bias, not noise. Legs are tested against leg_min_high_noise_m in that tier.
        leg_min = p["leg_min_high_noise_m"] if c.high_noise(o) else p["leg_min_m"]
        for tt in c.turns(o, p["turn_min_deg"] - 10):
            t = tt["t"]
            if not c.offball(o)[t]:
                continue
            a, b = _legs(c, o, t, p["leg_max_s"])
            l1 = (fe.x[t] - fe.x[a], fe.y[t] - fe.y[a])
            L1 = _norm(l1)
            ts = Tests()
            ts.ge("turn", abs(tt["A"]), p["turn_min_deg"], tt["sig"])
            ts.ge("in_leg", L1, leg_min, _sigd(fe, a, t))
            # fix L5-02 (loop 5, C4-B): the step in must close on the rim by a significant amount, Dr <= -in_dr_k x
            # sigma_disp (was Dr <= 0). In the high-noise tier, sideways or outward jiggles of a loitering wing / corner
            # player (clean median speed 0.6-1.8 m/s) read as 150+ deg reversals with 1.0-1.6 m legs; their in-leg Dr
            # margin is the one test that separates them from a true I (z 2.9-6.7 on the synthetic I at sigma_p 0.5)
            sd_in = _sigd(fe, a, t)
            # fix L6-03 (loop 6, replaced by L7-01): the in-leg must point within 60 deg of the rim (L6-03 tested it as
            # Dr <= -in_dir_frac x L1, in_dir_frac 0.5). The sigma margin alone let a corner
            # player walking down the sideline and back (Dr -0.4 to -0.6 m on a 1.5-2.4 m leg, 70-80 deg off the
            # radial) and lateral slides along the arc read as I-cuts at low noise (clean real: 23 of 63 cut_i events)
            # fix L7-01 (loop 7, C6-1): the 60 deg rule is now the documented angular test: the angle between the I's
            # in-leg direction and the bearing to the rim from its outer end is <= in_dir_max_deg. An I goes in and comes
            # straight back out along the same line (lateral_offset), so its axis is measured from the midpoint of the two
            # outer ends (a, b) to the apex t, with the bearing to the rim taken from that midpoint: the out-leg is a second,
            # 0.6-1 s later look at the same line, which cuts the direction noise (synthetic sigma 0.2: 5.7 -> 4.5 deg on
            # the 55 deg corner I). The test's sigma combines the axis direction noise and the bearing noise (sigma_p / r).
            # L6-03 used Dr / L1 >= 0.5, the angle at the chord's midpoint bearing (the radial turns along an off-radial
            # leg): 50-53 deg from the start for a 2 m leg at r 7 m, so a corner I-cut 55 deg off its start radial failed.
            # The significance margin of L5-02 (Dr <= -in_dr_k x sigma_disp) is unchanged.
            ts.le("in_Dr", float(fe.r[t] - fe.r[a]), -p["in_dr_k"] * sd_in, sd_in)
            mx, my = 0.5 * float(fe.x[a] + fe.x[b]), 0.5 * float(fe.y[a] + fe.y[b])
            ax = (float(fe.x[t]) - mx, float(fe.y[t]) - my)
            La, rm = _norm(ax), math.hypot(mx, my)
            ang_in = abs(_ang(ax, (-mx, -my))) if La > 0 and rm > 0 else 180.0
            sd_ax = math.sqrt(float(fe.sig_p[t]) ** 2 + 0.25 * (float(fe.sig_p[a]) ** 2 + float(fe.sig_p[b]) ** 2))
            sig_ang = math.degrees(math.hypot(sd_ax / max(La, 0.5), 0.5 * math.hypot(fe.sig_p[a], fe.sig_p[b]) / max(rm, 1.0)))
            ts.le("in_axis", ang_in, p["in_dir_max_deg"], sig_ang)
            # the in-leg chord itself (from its start) must also be within in_dir_max_deg up to a sigma-aware tolerance
            # (in_dir_tol_k x its direction sigma): when the out-leg does not come back to the start the axis is pulled
            # toward the radial, and a lateral in-leg (73 deg off the radial on a clean real arc slide) read 57 deg on it.
            # in_dir_tol_k 0.5: 1.0 let that lateral in-leg back (synthetic 3 of 20 at sigma 0.2 / 0.3), 0 cost the 55
            # deg corner I (16 -> 13 of 20)
            ang_ch = abs(_ang(l1, (-float(fe.x[a]), -float(fe.y[a])))) if L1 > 0 else 180.0
            sig_ch = math.degrees(sd_in / max(L1, 0.5))
            # fix L8-04 (loop 8, C7-3): the chord's tolerance is bounded (in_dir_tol_max_deg). Unbounded it grew with the
            # noise (0.5 x 4-9 deg at sigma 0.2-0.5), so a 67-70 deg lateral in-leg whose out-leg overshoots past the start
            # (axis 58 deg) passed on chord noise alone (confirmer I1 0 | 1 | 0 -> 3 | 3 | 1)
            ts.le("in_dir", ang_ch, p["in_dir_max_deg"] + min(p["in_dir_tol_k"] * sig_ch, p["in_dir_tol_max_deg"]), sig_ch)
            # fix L8-05 (loop 8, C7-4): when the I reaches the rim zone (r < cut_basket.rim_end_r_m 2.0 m at its start,
            # apex or axis midpoint) the bearing to the rim is ill-defined (a 1-1.5 m leg ending under the rim spans
            # 40-90 deg of bearing, and sigma_p / r is 15-25 deg at sigma_p 0.5), so the in-leg must also have the radial
            # depth of a 60 deg step: -Dr / L1 >= cos(in_dir_max_deg) (the L6-03 form; outside the zone the L7-01 angles
            # replace it). Under-rim shuffles and lateral drifts read as I-cuts at added noise 0.5 (loop-7 confirmer).
            if min(float(fe.r[a]), float(fe.r[t]), rm) < PARAMS["cut_basket"]["rim_end_r_m"]:
                ts.ge("in_depth", -float(fe.r[t] - fe.r[a]) / max(L1, 1e-6), math.cos(math.radians(p["in_dir_max_deg"])),
                      sd_in / max(L1, 0.5))
            L2 = math.hypot(fe.x[b] - fe.x[t], fe.y[b] - fe.y[t])
            ts.ge("out_leg", L2, leg_min, _sigd(fe, t, b))
            # fix L4-04 (loop 4): the out-leg is a cut (burst to get open), as for the V-cut; without it a perimeter
            # player's slow 1.2-1.5 m shuffle back and forth (peak 1.5-2.0 m/s) read as an I-cut. The smoother lowers
            # a 0.6 s burst's peak (a 5.9 m/s truth peak reads 2.4-3.4 m/s at sigma_p 0.3) and in the high-noise tier
            # the I-cut and the shuffle overlap (1.1-2.9 vs 1.1-2.7 m/s), so the test is not applied there.
            if not c.high_noise(o):
                ts.ge("out_peak", float(np.nanmax(fe.speed[t:b + 1])), p["out_peak_mps"],
                      float(np.nanmedian(fe.sig_speed[t:b + 1])))
            if c.high_noise(o):
                # with the lower leg floor, a run that stops reads a spurious >= 150 deg 'reversal' whose out-leg is
                # the smoother's 0.7-0.9 m jitter after a 2.5-4 m in-leg; a real I comes back out comparably far
                ts.ge("leg_balance", min(L1, L2) / max(L1, L2, 1e-6), p["leg_ratio_high_noise"],
                      _sigd(fe, a, b) / max(L1, L2, 0.5))
            if L1 > 0:
                # mean perpendicular offset of the out-leg from the in-leg line (robust to per-frame jitter)
                offs = [abs((fe.x[k] - fe.x[a]) * l1[1] - (fe.y[k] - fe.y[a]) * l1[0]) / L1 for k in range(t, b + 1)]
                n_eff = max(1.0, len(offs) / 9.0)
                ts.le("lateral_offset", float(np.nanmean(offs)), p["offset_max_m"],
                      float(np.nanmax(fe.sig_p[a:b + 1])) / math.sqrt(n_eff))
            r1 = _path_stats(fe.x, fe.y, a, t)["roundness_m"]
            r2 = _path_stats(fe.x, fe.y, t, b)["roundness_m"]
            ts.le("roundness", max(r1, r2), p["roundness_max_m"], float(np.nanmax(fe.sig_p[a:b + 1])))
            ts.flag("whole", b - a <= F(p["max_s"]))  # frame count (F02 class)
            ev = _emit("cut_i", {"cutter": o}, t, a, b, ts, [scene.k(o)], min_conf=p["min_conf"],
                       attrs=dict(t_turn=t, Dpsi_turn=round(tt["A"], 1), in_len=round(L1, 2),
                                  out_len=round(math.hypot(fe.x[b] - fe.x[t], fe.y[b] - fe.y[t]), 2)))
            if ev:
                out.append(ev)
    return out


# ======================================================================================
# CU.P11 banana, CU.P12 shallow, CU.P13 weak baseline, CU.P14 thru
# ======================================================================================
def _cum_turn(fe, a, b, min_mps):
    """Signed cumulative heading change (deg) over frames with speed >= min_mps, and the arc length."""
    h, prev, tot, arc = fe.hd, None, 0.0, 0.0
    for t in range(a, b + 1):
        if not (np.isfinite(h[t]) and fe.speed[t] >= min_mps):
            continue
        if prev is not None:
            tot += ((h[t] - h[prev]) + 540) % 360 - 180
            arc += float(np.nansum(np.hypot(np.diff(fe.x[prev:t + 1]), np.diff(fe.y[prev:t + 1]))))
        prev = t
    return tot, arc


def _arc_points(x, y, a, b, step=0.25):
    """Path points over [a, b] kept every >= step m (residual jitter suppressed) -> arrays px, py, s."""
    px, py = [x[a]], [y[a]]
    for t in range(a + 1, b + 1):
        if not (np.isfinite(x[t]) and np.isfinite(y[t])):
            continue
        if math.hypot(x[t] - px[-1], y[t] - py[-1]) >= step:
            px.append(x[t])
            py.append(y[t])
    px, py = np.array(px, float), np.array(py, float)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(px), np.diff(py)))])
    return px, py, s


def _arc_turn(fe, a, b, end_frac, local_arc_m):
    """Banana turn measure (fix F13) -> (turn_deg, arc_m, max_local_kappa, end_arc_m).

    turn: signed angle between the chord over the first end_frac and the chord over the last end_frac of the
    arc length, divided by (1 - end_frac) (exact for a circular arc). max_local_kappa: the largest turn over any
    local_arc_m of arc, in rad per m (angle between the two half-window chords / half window)."""
    px, py, s = _arc_points(fe.x, fe.y, a, b)
    S = float(s[-1]) if len(s) else 0.0
    if len(px) < 4 or S <= 0:
        return 0.0, S, 0.0, 0.0
    se = end_frac * S

    def at(v):
        return float(np.interp(v, s, px)), float(np.interp(v, s, py))

    p0, p1, p2, p3 = at(0.0), at(se), at(S - se), at(S)
    u, v = (p1[0] - p0[0], p1[1] - p0[1]), (p3[0] - p2[0], p3[1] - p2[1])
    turn = _ang(u, v) / (1 - end_frac) if min(_norm(u), _norm(v)) > 1e-6 else 0.0
    h = local_arc_m / 2
    kmax = 0.0
    for sc in np.arange(h, S - h + 1e-9, 0.25):
        q0, q1, q2 = at(sc - h), at(sc), at(sc + h)
        c1, c2 = (q1[0] - q0[0], q1[1] - q0[1]), (q2[0] - q1[0], q2[1] - q1[1])
        if min(_norm(c1), _norm(c2)) > 1e-6:
            kmax = max(kmax, math.radians(abs(_ang(c1, c2))) / h)
    return turn, S, kmax, se


def detect_cut_banana(scene, **params):
    """Banana (CU.P11): a wide curved cut; roundness is the primary noise-robust test."""
    p = _p("cut_banana", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        big = c.turns(o, p["corner_turn_deg"])
        # the arc window enters at window_enter_mps (fix F13): the CUT-style 1.5 m/s entry cuts the slow ends
        # of a curved run off, which shrinks both the measured turn and the roundness
        for a, b in c.moves(o, enter=p["window_enter_mps"]):
            st = _path_stats(fe.x, fe.y, a, b)
            if st["L"] < p["chord_min_m"]:
                continue
            # fix F13: the turn is the angle between the chords of the first and last end_frac of the arc length
            # (no speed gate, so the slow ends count), divided by 1 - end_frac (exact for a circular arc).
            tot, arc, kmax, s_end = _arc_turn(fe, a, b, p["end_frac"], p["kappa_local_arc_m"])
            kap = math.radians(abs(tot)) / arc if arc > 0 else 0.0
            sig_r = float(np.nanmax(fe.sig_p[a:b + 1]))
            sig_turn = math.degrees(math.sqrt(2) * sig_r / max(s_end, 0.5)) * math.sqrt(2) / (1 - p["end_frac"])
            ts = Tests()
            ts.ge("chord", st["C"], p["chord_min_m"], _sigd(fe, a, b))
            ts.ge("roundness", st["roundness_m"], max(p["roundness_min_m"], p["roundness_chord_frac"] * st["C"]), sig_r)
            ts.ge("cum_turn", abs(tot), p["cum_turn_min_deg"], sig_turn)
            ts.band("kappa", kap, p["kappa_lo_per_m"], p["kappa_hi_per_m"], p["kappa_sig_per_m"])
            ts.ge("arc", arc, p["arc_min_m"], p["arc_sig_m"])
            # a rounded L/V corner or a curl concentrates its turn: max turn over any kappa_local_arc_m of arc
            ts.le("kappa_local_max", kmax, p["kappa_local_max_per_m"], p["kappa_local_sig_per_m"])
            ts.flag("no_corner", not any(a < tt["t"] < b for tt in big))
            ts.le("Dr", float(fe.r[b] - fe.r[a]), p["dr_max_m"], _sigd(fe, a, b))
            inside = [q for q in c.contacts(o, a, b)]
            ts.flag("no_inside_screener", not inside)
            ev = _emit("cut_banana", {"cutter": o}, a, a, b, ts, [scene.k(o)], p_frame=_pframe_moving(fe),
                       min_conf=p["min_conf"],
                       attrs=dict(roundness_m=round(st["roundness_m"], 2), roundness_side=st["roundness_side"],
                                  cum_turn=round(tot, 1), kappa_mean=round(kap, 3), kappa_local_max=round(kmax, 3),
                                  radius_est_m=round(1 / kap, 2) if kap > 0 else None, chord=round(st["C"], 2)))
            if ev:
                out.append(ev)
    return out


def detect_cut_shallow(scene, **params):
    """Shallow (CU.P12): top/slot to the ball-side corner or low wing, never inside r 4.27."""
    p = _p("cut_shallow", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        for rec in _cut_recs(c, o):
            on = rec["on"]
            start_ok = bool(c.in_any(o, ("top_three", "slot_three", "slot_lane_line"))[on]
                            or (fe.m[on] > p["start_m_deg"] and fe.d3[on] >= p["start_d3_m"]))
            if not start_ok:
                continue
            arr = None
            for t in range(on, min(c.n, on + F(p["arrive_s"]) + 1)):
                bs = c.bs[t]
                stable = bs != 0 and all(c.bs[max(0, t - F(p["ball_side_stable_s"])):t + 1] == bs)
                if stable and fe.x[t] * bs >= 0.9 and c.in_any(o, ("corner_three", "wing_low"))[t]:
                    arr = t
                    break
            if arr is None:
                continue
            ts = _cut_tests(c, rec, PARAMS["cut"])
            min_r = float(np.nanmin(fe.r[on:arr + 1]))
            ts.ge("min_r", min_r, p["min_r_m"], float(np.nanmax(fe.sig_p[on:arr + 1])))
            ts.flag("start", start_ok)
            trig = "none"
            h = scene.holder[on]
            if any(q["passer"] == o and on - F(p["pass_window_s"]) <= q["t_rel"] <= on for q in c.passes()):
                trig = "pass"
            elif h is not None and h != o:
                lo = max(0, on - F(1.0))
                hh = c.f[h]
                if np.sign(hh.x[min(c.n - 1, on + F(0.5))] - hh.x[lo]) == np.sign(fe.x[on]) and \
                        abs(hh.x[min(c.n - 1, on + F(0.5))] - hh.x[lo]) >= p["dribble_at_m"]:
                    trig = "dribble_at"
            ev = _emit("cut_shallow", {"cutter": o, "ball_handler": h}, on, on, arr, ts, [scene.k(o)],
                       p_frame=_pframe_moving(fe), min_conf=p["min_conf"],
                       attrs=dict(trigger=trig, min_r=round(min_r, 2), t_arrival=arr, end_region=c.region(o, arr)))
            if ev:
                out.append(ev)
    return out


def detect_cut_weak_baseline(scene, **params):
    """Weak-side baseline cut / runner (CU.P13): along the baseline band, |Dx| >= 4.0 m in <= 1.8 s."""
    p = _p("cut_weak_baseline", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        for a, b in c.moves(o):
            bs = c.bs[a]
            if bs == 0 or fe.x[a] * bs > -0.9:
                continue
            t4 = None
            for t in range(a, min(b, a + F(p["within_s"])) + 1):
                if abs(fe.x[t] - fe.x[a]) >= p["dx_m"]:
                    t4 = t
                    break
            if t4 is None:
                continue
            # fix F05: Dx is tested at its maximum within within_s (t4, the first crossing, is only the end)
            wnd = range(a, min(b, a + F(p["within_s"])) + 1)
            k_dx = max(wnd, key=lambda k: abs(fe.x[k] - fe.x[a]) if np.isfinite(fe.x[k]) else -1)
            ts = Tests()
            ts.ge("Dx", abs(fe.x[k_dx] - fe.x[a]), p["dx_m"], _sigd(fe, a, k_dx))
            pf = [float(p_below(fe.y[t], p["band_y_m"], fe.sig_p[t])) for t in range(a, t4 + 1)]
            ts.frac("baseline_band", pf, p["band_frac"])
            ts.le("start_y", float(fe.y[a]), p["start_y_max_m"], fe.sig_p[a])
            ts.le("deep_pass", float(np.nanmin(fe.y[a:t4 + 1])), p["deep_y_m"], float(np.nanmax(fe.sig_p[a:t4 + 1])))
            pk = float(np.nanmax(fe.speed[a:t4 + 1]))
            ts.ge("peak_speed", pk, G["cut_peak_mps"], float(np.nanmedian(fe.sig_speed[a:t4 + 1])))
            far = max(scene.offense, key=lambda q: abs(c.f[q].x[a] - c.bx[a]) if np.isfinite(c.bx[a]) else -1) == o
            min_r = float(np.nanmin(fe.r[a:b + 1]))
            cross = bool(np.sign(fe.x[a]) != np.sign(fe.x[b]) and min_r <= p["to_rim_r_m"])
            scr = [q for q in c.contacts(o, a, t4) if c.in_any(q["s"], ("block", "low_post"))[q["t"]]]
            ev = _emit("cut_weak_baseline", {"runner": o, "screener": scr[0]["s"] if scr else None}, a, a, t4, ts,
                       [scene.k(o)], p_frame=_pframe_moving(fe), min_conf=p["min_conf"],
                       attrs=dict(farthest=far, baseline_to_rim=min_r <= p["to_rim_r_m"], cross_under=cross,
                                  runner_off_screen=bool(scr), end_region=c.region(o, t4)))
            if ev:
                out.append(ev)
    return out


def detect_cut_thru(scene, **params):
    """Thru cut (CU.P14): pass, then the passer cuts through the paint to the weak-side perimeter."""
    p = _p("cut_thru", params)
    c = _ctx(scene)
    out = []
    for q in c.passes():
        o, tp = q["passer"], q["t_rel"]
        fe = c.f[o]
        recs = [r_ for r_ in _cut_recs(c, o) if tp - F(0.3) <= r_["on"] <= tp + F(p["cut_within_s"])]
        if not recs:
            continue
        hi = min(c.n - 1, tp + F(p["exit_within_s"]))
        paint = [t for t in range(tp, min(c.n - 1, tp + F(p["paint_within_s"])) + 1)
                 if abs(fe.x[t]) <= C["LANE_X"] and fe.y[t] <= C["FT_Y"]]
        if not paint:
            continue
        t_exit = None
        for t in range(paint[0], hi + 1):
            bs = c.bs[t]
            if bs != 0 and fe.x[t] * bs <= -0.9 and fe.d3[t] >= p["exit_d3_m"]:
                t_exit = t
                break
        if t_exit is None:
            continue
        rec_, tcat = _received(c, o, tp + 3, t_exit)
        if rec_ and fe.r[tcat] <= G["rim_end_r_m"]:
            continue  # give-and-go owns it
        ts = _cut_tests(c, recs[0], PARAMS["cut"])
        min_r = float(np.nanmin(fe.r[tp:t_exit + 1]))
        ts.le("min_r", min_r, p["min_r_max_m"], fe.sig_p[tp])
        ts.flag("paint_entry", True)
        ts.flag("weak_exit", True)
        ev = _emit("cut_thru", {"cutter": o, "receiver": q["receiver"]}, tp, tp, t_exit, ts, [scene.k(o)],
                   min_conf=p["min_conf"],
                   attrs=dict(t_pass=tp, t_paint_entry=paint[0], t_exit=t_exit, exit_region=c.region(o, t_exit),
                              dwell_in_paint_s=round(len(paint) * DT, 2), min_r=round(min_r, 2),
                              variant="to_corner" if c.spot(o, "corner_three")[t_exit] else "wing"))
        if ev:
            out.append(ev)
    return out


# ======================================================================================
# Screen-relative cuts (CU.A1 - CU.A11 and the off-ball screen exits)
# ======================================================================================
def detect_cut_curl(scene, **params):
    """Curl (CU.A1): around a stationary screener toward the rim; tight or wide."""
    p = _p("cut_curl", params)
    c = _ctx(scene)
    out = []
    for u in scene.offense:
        fe = c.f[u]
        for ct in c.all_contacts(u):
            t_s, s_ = ct["t"], ct["s"]
            lo, hi = t_s - F(p["turn_window_s"]), t_s + F(p["turn_window_s"])
            if lo < 0 or hi >= c.n or fe.speed[t_s] < G["move_exit_mps"]:
                continue
            k3 = F(0.3)
            pre = (fe.x[t_s - k3] - fe.x[lo], fe.y[t_s - k3] - fe.y[lo])
            post = (fe.x[hi] - fe.x[t_s + k3], fe.y[hi] - fe.y[t_s + k3])
            if min(_norm(pre), _norm(post)) < G["turn_min_chord_m"]:
                continue
            turn = _ang(pre, post)
            fs = c.f[s_]
            # screener side (fix F07): relative to the user's tangent at the closest approach, where the vector to
            # the screener is near perpendicular (the pre-chord can point straight away from him on a tight curl)
            ks = F(p["side_chord_s"])
            tan = (fe.x[min(c.n - 1, t_s + ks)] - fe.x[max(0, t_s - ks)], fe.y[min(c.n - 1, t_s + ks)] - fe.y[max(0, t_s - ks)])
            side = _ang(tan, (fs.x[t_s] - fe.x[t_s], fs.y[t_s] - fe.y[t_s]))
            sd = math.sqrt(2) * fe.sig_p[t_s]
            sig_t = math.degrees(math.hypot(sd / _norm(pre), sd / _norm(post)))
            # integrated curvature over the arc of length kappa_arc_m centred on t_s
            sarc = np.concatenate([[0], np.cumsum(np.nan_to_num(np.hypot(np.diff(fe.x), np.diff(fe.y))))])
            idx = [t for t in range(lo, hi + 1) if abs(sarc[t] - sarc[t_s]) <= p["kappa_arc_m"] / 2]
            tot, arc = _cum_turn(fe, idx[0], idx[-1], G["move_exit_mps"])
            kap = math.radians(abs(tot)) / arc if arc > 0 else 0.0
            # fix F07: the chord angle lies in (-180, 180], so a tight curl (167-178 deg) has a random sign; the
            # integrated heading over [lo, hi] keeps the sign and the size beyond 180
            tot_w, _ = _cum_turn(fe, lo, hi, G["move_exit_mps"])
            turn_v = max(abs(turn), abs(tot_w)) if abs(turn) > p["wrap_deg"] else abs(turn)
            sgn = np.sign(tot_w) if abs(turn) > p["wrap_deg"] else np.sign(turn)
            ts = Tests()
            _contact_test(ts, ct)
            ts.ge("cum_turn", turn_v, p["turn_min_deg"], sig_t)
            ts.flag("toward_screener", sgn == np.sign(side) or ct["d"] < p["merge_d_m"])
            ts.ge("kappa_3m", kap, p["kappa_min_per_m"], 0.05)
            ts.le("exit_inside", float(fe.r[hi] - fs.r[t_s]), -p["exit_inside_m"], math.hypot(fe.sig_p[hi], fs.sig_p[t_s]))
            tight = ct["d"] <= p["tight_d_m"] and (fe.r[hi] <= p["tight_r_m"] or (abs(fe.x[hi]) <= C["LANE_X"] and fe.y[hi] <= C["FT_Y"]))
            did, amb, _ = c.defender(u, lo, t_s)
            dpath = None
            if did is not None:
                fd = c.f[did]
                td = lo + int(np.nanargmin(c.dist(did, s_)[lo:hi + 1]))
                dpath = "under" if fd.r[td] < fs.r[td] else "over_or_trail"
            rec_, tcat = _received(c, u, t_s, hi + F(1.0))
            # fix C1 (loop 2): a curl wraps around the screener, so the pair distance is flat over the arc and its
            # argmin (t_s) lands anywhere on it under noise (tight curls 0.25-0.6 s late at sigma_p 0.5). t0 is the
            # centre of the frames within t0_flat_k x sigma_pair of the minimum, in the contact's run.
            dd = c.dist(u, s_)
            near = np.nan_to_num(dd, nan=99.0) <= ct["d"] + p["t0_flat_k"] * ct["sig"]
            i0 = i1 = t_s
            while i0 - 1 >= lo and near[i0 - 1]:
                i0 -= 1
            while i1 + 1 <= hi and near[i1 + 1]:
                i1 += 1
            t0 = (i0 + i1) // 2
            ev = _emit("cut_curl", {"user": u, "screener": s_}, t0, lo, hi, ts, [scene.k(u), scene.k(s_)],
                       p_frame=_pframe_moving(fe), min_conf=p["min_conf"],
                       attrs=dict(t_s=t_s, closest_approach_m=round(ct["d"], 2), cum_turn_pm1s=round(turn, 1),
                                  kappa_3m=round(kap, 3), exit_r=round(float(fe.r[hi]), 2),
                                  variant="tight" if tight else ("wide" if fe.r[hi] >= p["wide_r_m"] else "standard"),
                                  defender_path=dpath, received_ball=rec_, t_catch=tcat))
            if ev:
                # one curl per (user, screener) within turn_window_s (loop 2, C1: two contact pieces of one wrap
                # gave two events, now centred on the same t0); keep the higher conf
                dup = [k for k, e in enumerate(out) if e.actors["user"] == u and e.actors["screener"] == s_
                       and abs(e.t0 - ev.t0) <= F(p["turn_window_s"])]
                if dup and out[dup[0]].conf >= ev.conf:
                    continue
                for k in reversed(dup):
                    out.pop(k)
                out.append(ev)
    return out


def _away(c, u, a, e, p):
    """Common away-from-ball test for flare / fade (CU.A2) over [a, e] -> Tests or None."""
    fe = c.f[u]
    if not np.isfinite(c.bx[a]):
        return None
    D = (fe.x[e] - fe.x[a], fe.y[e] - fe.y[a])
    vb = (c.bx[a] - fe.x[a], c.by[a] - fe.y[a])
    if _norm(D) < 0.5 or _norm(vb) < 0.5:
        return None
    alpha = abs(_ang(D, vb))
    dball = c.dball(u)
    ts = Tests()
    sd = _sigd(fe, a, e)
    ts.ge("move", _norm(D), p["move_min_m"], sd)
    ts.ge("alpha_ball", alpha, p["alpha_min_deg"], math.degrees(sd / _norm(D)))
    ts.ge("Dd_ball", float(dball[e] - dball[a]), p["dd_ball_m"], sd)
    ts.ge("Dr", float(fe.r[e] - fe.r[a]), p["dr_min_m"], sd)
    ts.ge("end_d3", float(fe.d3[e]), p["end_d3_m"], fe.sig_p[e])
    return ts, alpha


def detect_cut_flare(scene, **params):
    """Flare (CU.A2, screened) away from the ball off a screener on the ball side; ghost flag when the
    screener never stops."""
    p = _p("cut_flare", params)
    return _flare_fade(scene, p, screened=True)


def detect_cut_fade(scene, **params):
    """Fade (CU.A2, unscreened) away from the ball to the arc; fade_off_downscreen variant."""
    p = _p("cut_fade", params)
    return _flare_fade(scene, p, screened=False)


def _flare_fade(scene, p, screened):
    c = _ctx(scene)
    out = []
    for u in scene.offense:
        fe = c.f[u]
        for a, b in c.moves(u):
            e = min(b, a + F(p["within_s"]))
            r_ = _away(c, u, a, e, p)
            if r_ is None:
                continue
            ts, alpha = r_
            # the user may start next to the screener: contacts from 0.3 s before the MOVE, moving or not.
            # Soft contacts (fix F09): candidates to 1.2 m + 2 sigma_pair, each with p = P(true d <= 1.2 m);
            # the flare carries p_contact and the fade 1 - max p_contact, so a borderline screen splits them.
            cts = c.contacts(u, max(0, a - F(p["pre_s"])), e, need_moving=False, widen=True)
            vb = (c.bx[a] - fe.x[a], c.by[a] - fe.y[a])
            ball_side = [q for q in cts if (c.f[q["s"]].x[q["t"]] - fe.x[q["t"]]) * vb[0]
                         + (c.f[q["s"]].y[q["t"]] - fe.y[q["t"]]) * vb[1] > 0]
            p_any = max((q["p"] for q in cts), default=0.0)
            ghost = []
            if p_any < 0.5:
                ghost = c.contacts(u, max(0, a - F(p["pre_s"])), e, need_stationary=False, need_moving=False)
            if screened:
                if ball_side and max(q["p"] for q in ball_side) >= 0.5:
                    q, variant = max(ball_side, key=lambda z: z["p"]), "flare"
                    _contact_test(ts, q)
                elif ghost:
                    q, variant = ghost[0], "ghost_flare"
                else:
                    continue
                t0 = max(q["t"], a)  # screen moment, clipped to the departure when u starts at the screener
                ts.flag("screen_ball_side", True)
                actors = {"user": u, "screener": q["s"]}
                kins = [scene.k(u), scene.k(q["s"])]
                cap = G["identity_cap"] if variant == "ghost_flare" else None
                p_ff = round(max((z["p"] for z in ball_side), default=0.0), 3)
            else:
                if p_any >= 0.5:
                    q = max(cts, key=lambda z: z["p"])
                    down = c.in_any(u, ("corner_three", "wing_low"))[e] and fe.m[e] - fe.m[a] <= -p["down_dm_deg"]
                    if not down:
                        continue
                    # fix F16: a down screen needs a screener who came down from above the user (not a
                    # baseline screener on an exit to the corner)
                    if not (_arrived_from_above(c, q["s"], q["t"], p["down_scr_dy_m"], p["down_scr_back_s"])
                            and fe.y[a] < c.f[q["s"]].y[q["t"]]):
                        continue
                    _contact_test(ts, q)
                    variant, t0, actors = "fade_off_downscreen", max(q["t"], a), {"user": u, "screener": q["s"]}
                else:
                    ts.flag("no_screen", True, 1.0 - p_any)
                    variant, t0, actors = "fade", a, {"user": u}
                # a standing teammate within 2 sigma of screen contact makes flare vs fade ambiguous: cap
                kins, cap = [scene.k(u)], (G["identity_cap"] if cts and variant == "fade" else None)
                p_ff = round(p_any, 3)
            rec_, tcat = _received(c, u, a, e + F(0.5))
            ev = _emit("cut_flare" if screened else "cut_fade", actors, t0, a, e, ts, kins, p_frame=_pframe_moving(fe),
                       cap=cap, min_conf=p["min_conf"],
                       attrs=dict(variant=variant, t_onset=a, alpha_ball=round(alpha, 1),
                                  Dd_ball=round(float(c.dball(u)[e] - c.dball(u)[a]), 2), end_region=c.region(u, e),
                                  skip_pass_received=rec_, t_catch=tcat, p_flare_vs_fade=p_ff))
            if ev:
                out.append(ev)
    return out


def detect_cut_straight(scene, **params):
    """Straight read off a screen (CU.A3): heading kept within 30 deg, lifting to the perimeter."""
    p = _p("cut_straight", params)
    return _straight_pop(scene, p, "straight")


def detect_cut_pop_out(scene, **params):
    """Pop-out (CU.A3): straight toward the ball after the screen, ending >= 1.0 m outside the screener."""
    p = _p("cut_pop_out", params)
    return _straight_pop(scene, p, "pop_out")


def _straight_pop(scene, p, which):
    c = _ctx(scene)
    out = []
    for u in scene.offense:
        fe = c.f[u]
        for ct in c.all_contacts(u):
            t_s, s_ = ct["t"], ct["s"]
            pre0, post1 = t_s - F(p["dir_window_s"]), t_s + F(p["dir_window_s"])
            e = t_s + F(p["exit_s"])
            if pre0 < 0 or e >= c.n:
                continue
            fs = c.f[s_]
            ts = Tests()
            _contact_test(ts, ct)  # fix F09: the pass-by distance enters conf
            ms = math.hypot(fe.x[e] - fe.x[t_s], fe.y[e] - fe.y[t_s]) / (p["exit_s"])
            ts.ge("exit_speed", ms, p["exit_mps"], math.sqrt(2) * fe.sig_p[e] / p["exit_s"])
            if which == "straight":
                pre = (fe.x[t_s] - fe.x[pre0], fe.y[t_s] - fe.y[pre0])
                post = (fe.x[post1] - fe.x[t_s], fe.y[post1] - fe.y[t_s])
                if min(_norm(pre), _norm(post)) < G["turn_min_chord_m"]:
                    continue
                dh = abs(_ang(pre, post))
                sd = math.sqrt(2) * fe.sig_p[t_s]
                ts.le("heading_change", dh, p["heading_max_deg"], math.degrees(math.hypot(sd / _norm(pre), sd / _norm(post))))
                ts.ge("Dr_exit", float(fe.r[e] - fe.r[t_s]), p["dr_min_m"], _sigd(fe, t_s, e))
                # fix L6-04 (loop 6): the two tests that make the label (the pass-by contact and the straight exit)
                # were each near their edge on the events noise adds (real n0.3 noise-only: contact z median 1.2,
                # heading z p25 0.4); their summed z must reach evidence_k (every clean real event has >= 2.0)
                ts.ge("straight_evidence", ts.z["contact"] + ts.z["heading_change"], p["evidence_k"], math.sqrt(2.0))
                attrs = dict(exit_heading_change=round(dh, 1))
            else:
                if not np.isfinite(c.bx[t_s]):
                    continue
                D = (fe.x[e] - fe.x[t_s], fe.y[e] - fe.y[t_s])
                vb = (c.bx[t_s] - fe.x[t_s], c.by[t_s] - fe.y[t_s])
                if _norm(D) < 0.5:
                    continue
                al = abs(_ang(D, vb))
                ts.le("alpha_ball", al, p["alpha_max_deg"], math.degrees(_sigd(fe, t_s, e) / _norm(D)))
                ts.le("Dd_ball", float(c.dball(u)[e] - c.dball(u)[t_s]), -p["dd_ball_m"], _sigd(fe, t_s, e))
                ts.ge("outside_screener", float(fe.r[e] - fs.r[t_s]), p["outside_m"], math.hypot(fe.sig_p[e], fs.sig_p[t_s]))
                attrs = dict(alpha_ball_exit=round(al, 1))
            rec_, tcat = _received(c, u, t_s, e + F(0.5))
            attrs.update(t_s=t_s, exit_r_minus_screener_r=round(float(fe.r[e] - fs.r[t_s]), 2), received_ball=rec_)
            ev = _emit("cut_" + which, {"user": u, "screener": s_}, t_s, pre0, e, ts, [scene.k(u), scene.k(s_)],
                       p_frame=_pframe_moving(fe), min_conf=p["min_conf"], attrs=attrs)
            if ev:
                out.append(ev)
    return out


def _behind_screener(c, u, s_, t_s, a, p_gap):
    """Back-screen geometry: r(S) <= r(def_u) - gap. Returns (passed, p, defender, ambiguous)."""
    did, amb, _ = c.defender(u, a, t_s)
    if did is None:
        return None, 1.0, None, True
    fd, fs = c.f[did], c.f[s_]
    v = float(fd.r[t_s] - fs.r[t_s])
    sig = math.hypot(fd.sig_p[t_s], fs.sig_p[t_s])
    return v >= p_gap, float(p_above(v, p_gap, sig)), did, amb


def detect_cut_ucla(scene, **params):
    """UCLA (CU.A4): top/slot passer passes to the same-side wing, cuts off a high-post back screen to the rim."""
    p = _p("cut_ucla", params)
    c = _ctx(scene)
    out = []
    for q in c.passes():
        A, tp = q["passer"], q["t_rel"]
        fa = c.f[A]
        if not (fa.r[tp] >= p["start_r_m"] and fa.m[tp] > p["start_m_deg"]):
            continue
        rv = q["receiver"]
        if not c.spot(rv, "wing_three")[q["t_catch"]]:
            continue
        if not (np.sign(c.f[rv].x[q["t_catch"]]) == np.sign(fa.x[tp]) or abs(fa.x[tp]) <= p["centre_x_m"]):
            continue
        recs = [r_ for r_ in _cut_recs(c, A) if tp - F(0.3) <= r_["on"] <= tp + F(p["cut_within_s"])]
        if not recs:
            continue
        rec = recs[0]
        hi = min(c.n - 1, tp + F(p["rim_within_s"]))
        i_min = rec["on"] + int(np.nanargmin(fa.r[rec["on"]:hi + 1]))
        ts = Tests()
        ts.le("min_r", float(fa.r[i_min]), G["rim_end_r_m"], fa.sig_p[i_min])
        ts.ge("neg_Dr", float(fa.r[rec["on"]] - fa.r[i_min]), p["neg_dr_m"], _sigd(fa, rec["on"], i_min))
        bside = np.sign(c.f[rv].x[q["t_catch"]])
        hp = ("elbow", "high_post_strip", "pinch_post")
        # fix F01 (d): soft contacts, candidates to 1.2 m + 2 sigma_pair with p = P(true d <= 1.2 m)
        scr = [ct for ct in c.contacts(A, rec["on"], i_min, widen=True)
               if c.in_any(ct["s"], hp)[ct["t"]] and (c.f[ct["s"]].x[ct["t"]] * bside >= -p["ball_side_tol_m"])]
        good = [ct for ct in scr if ct["p"] >= 0.5]
        cap = None
        if good:
            ct = max(good, key=lambda z: z["p"])
            _contact_test(ts, ct)
            beh, pb, did, amb = _behind_screener(c, A, ct["s"], ct["t"], rec["on"], p["behind_gap_m"])
            if beh is None:
                cap = G["identity_cap"]
            else:
                ts.flag("screener_behind_defender", beh, pb)
                cap = G["identity_cap"] if amb else None
            t0, variant, actors = ct["t"], "screened", {"cutter": A, "receiver": rv, "screener": ct["s"], "defender": did}
            kins = [scene.k(A), scene.k(ct["s"])]
            hp_player = ct["s"]
        else:
            # fix F01 (a, b): the no-screen variant needs a teammate in the high post on the ball side at t_pass
            # whose distance to the cutter's path [onset, min-r frame] is <= no_screen_path_m; capped at 0.6.
            # t0 (fix F01 c): the cutter's closest approach to that player, the same anchor as the screened
            # variant, so a borderline contact cannot move t0 (t_pass is stored).
            best = None
            for v in scene.offense:
                if v in (A, rv) or not c.in_any(v, hp)[tp] or c.f[v].x[tp] * bside < -p["ball_side_tol_m"]:
                    continue
                dv = c.dist(A, v)[rec["on"]:i_min + 1]
                if not np.isfinite(dv).any():
                    continue
                k_ = rec["on"] + int(np.nanargmin(dv))
                if dv[k_ - rec["on"]] <= p["no_screen_path_m"] and (best is None or dv[k_ - rec["on"]] < best[2]):
                    best = (v, k_, float(dv[k_ - rec["on"]]))
            if best is None:
                continue
            ts.le("high_post_near_path", best[2], p["no_screen_path_m"],
                  math.hypot(fa.sig_p[best[1]], c.f[best[0]].sig_p[best[1]]))
            t0, variant, cap = best[1], "ucla_path_no_screen", G["identity_cap"]
            actors, kins, hp_player = {"cutter": A, "receiver": rv, "high_post": best[0]}, [scene.k(A)], best[0]
        rec_, tcat = _received(c, A, tp + 3, i_min + F(0.5))
        ev = _emit("cut_ucla", actors, t0, tp, i_min, ts, kins, p_frame=_pframe_moving(fa), cap=cap,
                   min_conf=p["min_conf"],
                   attrs=dict(t_pass=tp, t_s=t0, variant=variant, min_r=round(float(fa.r[i_min]), 2), t_min_r=i_min,
                              screener_spot=c.region(hp_player, t0),
                              received_ball=rec_, lob=None))
        if ev:
            out.append(ev)
    return out


def detect_cut_iverson(scene, **params):
    """Iverson (CU.A5): wing-to-wing over the elbows, crossing x = 0 at y 4.4-7.5 m."""
    p = _p("cut_iverson", params)
    c = _ctx(scene)
    out = []
    for u in scene.offense:
        fe = c.f[u]
        ob = c.offball(u)
        for t in range(1, c.n):
            if not (np.isfinite(fe.x[t - 1]) and np.sign(fe.x[t - 1]) != np.sign(fe.x[t]) and ob[t]):
                continue
            if not p["cross_y_lo_m"] - 0.5 <= fe.y[t] <= p["cross_y_hi_m"] + 0.5:
                continue
            lo = max(0, t - F(p["within_s"]))
            starts = [k for k in range(lo, t) if fe.r[k] >= p["wing_r_m"] and abs(fe.x[k]) >= p["wing_x_m"]]
            if not starts:
                continue
            ts_ = starts[-1]
            ends = [k for k in range(t, min(c.n, ts_ + F(p["within_s"]) + 1))
                    if np.sign(fe.x[k]) != np.sign(fe.x[ts_]) and abs(fe.x[k]) >= p["wing_x_m"]
                    and (fe.r[k] >= p["wing_r_m"] or fe.r[k] < p["curl_r_m"])]
            if not ends:
                continue
            te = ends[0]
            ts = Tests()
            ts.band("y_cross", float(fe.y[t]), p["cross_y_lo_m"], p["cross_y_hi_m"], fe.sig_p[t])
            ts.ge("Dx", abs(fe.x[te] - fe.x[ts_]), p["dx_m"], _sigd(fe, ts_, te))
            ts.ge("peak_speed", float(np.nanmax(fe.speed[ts_:te + 1])), G["move_enter_mps"], 0.4)
            scr = [ct for ct in c.contacts(u, ts_, te)
                   if c.in_any(ct["s"], ("elbow", "high_post_strip", "pinch_post"))[ct["t"]]]
            n_scr = len({ct["s"] for ct in scr})
            ram = any(bs_["screener"] in {ct["s"] for ct in scr} and te <= bs_["t"] <= te + F(p["ram_s"])
                      for bs_ in c.ball_screens())
            bm = bool(np.isfinite(c.bx[t]) and abs(c.bx[t]) <= p["ball_middle_x_m"])
            exit_ = "curl" if fe.r[te] < p["curl_r_m"] else "wing"
            ev = _emit("cut_iverson", {"cutter": u, "screeners": sorted({ct["s"] for ct in scr})}, t, ts_, te, ts,
                       [scene.k(u)], p_frame=_pframe_moving(fe), min_conf=p["min_conf"],
                       attrs=dict(t_cross=t, y_cross=round(float(fe.y[t]), 2), n_screens=n_scr,
                                  variant="screened" if n_scr else "iverson_path_unscreened", exit=exit_,
                                  ball_middle=bm, iverson_ram=ram, end_region=c.region(u, te)))
            if ev:
                out.append(ev)
    return out


def _screen_cut_generic(scene, kind, p, screener_ok, start_ok, end_ok, extra=None):
    """Template for screen-relative cuts driven by a contact (u, S, t_s).

    screener_ok(c, s, t_s) -> bool; start_ok(c, u, a) -> bool; end_ok(c, u, t, a) -> bool.
    The window is u's MOVE around t_s, at most back_s before and fwd_s after. extra(c, u, s, t_s, a, e, ts)
    adds rule-specific tests and returns attrs (or None to reject).
    """
    c = _ctx(scene)
    out = []
    for u in scene.offense:
        fe = c.f[u]
        for ct in c.all_contacts(u):
            t_s, s_ = ct["t"], ct["s"]
            if not screener_ok(c, s_, t_s):
                continue
            # start: the departure frame from the rule's start region. Take the run of start-region frames
            # ending at the last one in [t_s - back_s, t_s]; the start is its last slow frame (speed < 1.0),
            # else its first frame.
            lo = max(0, t_s - F(p["back_s"]))
            starts = [k for k in range(lo, t_s + 1) if start_ok(c, u, k)]
            if not starts:
                continue
            k = starts[-1]
            while k - 1 >= lo and start_ok(c, u, k - 1):
                k -= 1
            # departure (fix F03): the start of the MOVE that contains t_s when it lies in the start-region run;
            # else the last chi-square-stationary frame of the run; else the run's first frame. Raw speed at
            # rest reads 0.3-1.2 m/s at sigma_p 0.5 m, so 'speed < 1.0' is not used.
            mv = c.move_at(u, t_s)
            if mv is not None and k <= mv[0] <= starts[-1]:
                a = mv[0]
            else:
                st_ = [j for j in range(k, starts[-1] + 1) if c.stationary(u)[j]]
                a = st_[-1] if st_ else k
            ends = [k for k in range(t_s, min(c.n, a + F(p["total_s"]) + 1)) if end_ok(c, u, k, a)]
            if not ends:
                continue
            # end: the arrival, i.e. the first end-region frame advanced while u keeps moving inside it
            e = ends[0]
            while e + 1 < min(c.n, a + F(p["total_s"]) + 1) and end_ok(c, u, e + 1, a) and \
                    fe.speed[e + 1] >= G["move_exit_mps"]:
                e += 1
            ts = Tests()
            _contact_test(ts, ct)
            attrs = extra(c, u, s_, t_s, a, e, ts) if extra else {}
            if attrs is None:
                continue
            cap = attrs.pop("_cap", None)
            rec_, tcat = _received(c, u, t_s, e + F(0.5))
            attrs.update(t_s=t_s, t_start=a, t_end=e, closest_approach_m=round(ct["d"], 2), received_ball=rec_,
                         end_region=c.region(u, e))
            actors = {"cutter": u, "screener": s_}
            actors.update(attrs.pop("_actors", {}))
            ev = _emit(kind, actors, t_s, a, e, ts, [scene.k(u), scene.k(s_)], p_frame=_pframe_moving(fe), cap=cap,
                       min_conf=p["min_conf"], attrs=attrs)
            if ev:
                out.append(ev)
    return out


def detect_cut_flex(scene, **params):
    """Flex (CU.A6): weak-side corner along the baseline off a low-post screen to the ball-side post."""
    p = _p("cut_flex", params)

    def scr_ok(c, s_, t):
        return bool(c.in_any(s_, ("low_post", "block", "dunker_spot"))[t])

    def start_ok(c, u, k):
        fe = c.f[u]
        bs = c.bs[k]
        corner = c.spot(u, "corner_three")[k] or (c.spot(u, "wing_low")[k] and fe.m[k] <= p["wing_low_m_deg"])
        return bool(corner and bs != 0 and fe.x[k] * bs <= -0.9)

    def end_ok(c, u, k, a):
        fe = c.f[u]
        bs = c.bs[k]
        crossed = np.sign(fe.x[k]) != np.sign(fe.x[a])
        inside = c.in_any(u, ("low_post", "block", "dunker_spot", "restricted_area"))[k] and bs != 0 and fe.x[k] * bs >= 0
        return bool(crossed or inside)

    def extra(c, u, s_, t_s, a, e, ts):
        fe = c.f[u]
        pf = [float(p_below(fe.y[k], p["band_y_m"], fe.sig_p[k])) for k in range(a, e + 1)]
        ts.frac("baseline_band", pf, p["band_frac"])
        ts.flag("within", e - a <= F(p["total_s"]))  # frame count, as the end search (fix F02)
        cont = False
        for v in c.s.offense:
            if v in (u, s_):
                continue
            dd = c.dist(v, s_)
            for k in range(t_s, min(c.n, t_s + F(p["continuity_s"]) + 1)):
                if dd[k] <= G["screen_contact_m"] and c.f[v].y[max(0, k - F(1.5))] - c.f[v].y[k] >= 1.5:
                    cont = True
                    break
        return dict(over_or_under="over" if fe.y[t_s] > c.f[s_].y[t_s] else "under", flex_continuity=cont)

    return _screen_cut_generic(scene, "cut_flex", p, scr_ok, start_ok, end_ok, extra)


def _screener_descent(c, s_, t_s, back_s):
    """Descent of the screener's last approach (fix F11): max y over [t_s - back_s, t_s] minus y(t_s), so a
    screener who came down and then held before the cut still counts."""
    fs = c.f[s_]
    k = max(0, t_s - F(back_s))
    return float(np.nanmax(fs.y[k:t_s + 1]) - fs.y[t_s])


def _arrived_from_above(c, s_, t_s, dy, back_s):
    return _screener_descent(c, s_, t_s, back_s) >= dy


def detect_cut_zipper(scene, **params):
    """Zipper (CU.A7): from the block straight up to the slot/top off a down screener."""
    p = _p("cut_zipper", params)

    def scr_ok(c, s_, t):
        return bool(p["scr_r_lo_m"] <= c.f[s_].r[t] <= p["scr_r_hi_m"]
                    and _arrived_from_above(c, s_, t, p["scr_dy_m"], p["scr_arrive_back_s"]))

    def start_ok(c, u, k):
        return bool(c.f[u].r[k] <= p["start_r_m"] and c.in_any(u, ("block", "low_post", "dunker_spot", "lane_middle"))[k])

    def end_ok(c, u, k, a):
        fe = c.f[u]
        return bool(c.in_any(u, ("slot_three", "top_three", "slot_lane_line", "wing_high"))[k]
                    or (fe.m[k] > p["end_m_deg"] and fe.d3[k] >= p["end_d3_m"]))

    def extra(c, u, s_, t_s, a, e, ts):
        fe = c.f[u]
        dy, dx = fe.y[e] - fe.y[a], abs(fe.x[e] - fe.x[a])
        ts.ge("Dy", float(dy), p["dy_m"], _sigd(fe, a, e))
        ts.flag("vertical", dx < p["vertical_ratio"] * dy)
        ts.flag("within", e - a <= F(p["total_s"]))
        return dict(screener_Dy_arrival=round(_screener_descent(c, s_, t_s, p["scr_arrive_back_s"]), 2), inbound=None)

    return _screen_cut_generic(scene, "cut_zipper", p, scr_ok, start_ok, end_ok, extra)


def detect_cut_pin_down(scene, **params):
    """Pin-down exit: from low (y <= 3.68) up and out to the wing/corner off a down screener."""
    p = _p("cut_pin_down", params)

    def scr_ok(c, s_, t):
        fs = c.f[s_]
        return bool(_arrived_from_above(c, s_, t, p["scr_dy_m"], p["scr_arrive_back_s"]) and fs.y[t] <= p["scr_y_max_m"]
                    and p["scr_x_lo_m"] <= abs(fs.x[t]) <= p["scr_x_hi_m"])

    def start_ok(c, u, k):
        fe = c.f[u]
        return bool(fe.y[k] <= p["start_y_max_m"] and fe.r[k] <= p["start_r_max_m"])

    def end_ok(c, u, k, a):
        fe = c.f[u]
        return bool(fe.d3[k] >= p["end_d3_m"] and fe.m[k] <= p["end_m_max_deg"])

    def extra(c, u, s_, t_s, a, e, ts):
        fe = c.f[u]
        ts.ge("Dy", float(fe.y[e] - fe.y[a]), p["dy_m"], _sigd(fe, a, e))
        ts.flag("within", e - a <= F(p["total_s"]))  # frame count, as the end search (fix F02)
        return dict(variant="wide" if c.f[s_].m[t_s] <= p["wide_m_deg"] else "standard")

    return _screen_cut_generic(scene, "cut_pin_down", p, scr_ok, start_ok, end_ok, extra)


def detect_cut_turnout(scene, **params):
    """Turnout (offense A5.4): from the paint/rim turning out to the arc off a block/lane-line screener."""
    p = _p("cut_turnout", params)

    def scr_ok(c, s_, t):
        return bool(p["scr_r_lo_m"] <= c.f[s_].r[t] <= p["scr_r_hi_m"])

    def start_ok(c, u, k):
        return bool(c.f[u].r[k] < p["start_r_m"])

    def end_ok(c, u, k, a):
        return bool(c.f[u].r[k] >= p["end_r_m"])

    def extra(c, u, s_, t_s, a, e, ts):
        fe = c.f[u]
        ts.ge("Dr", float(fe.r[e] - fe.r[a]), p["dr_m"], _sigd(fe, a, e))
        ts.flag("within", e - a <= F(p["total_s"]))  # frame count, as the end search (fix F02)
        hs = np.nan_to_num(fe.speed[a:e + 1], nan=0) >= PARAMS["cut"]["hard_cut_mps"]
        return dict(hard_cut=bool(hs.any()))

    return _screen_cut_generic(scene, "cut_turnout", p, scr_ok, start_ok, end_ok, extra)


def detect_cut_cross_screen(scene, **params):
    """Cross-screen cut: low post to the opposite low post across the lane past a stationary screener."""
    p = _p("cut_cross_screen", params)

    def scr_ok(c, s_, t):
        fs = c.f[s_]
        return bool(fs.y[t] < p["band_y_m"] and abs(fs.x[t]) <= p["scr_x_max_m"])

    def start_ok(c, u, k):
        fe = c.f[u]
        return bool(fe.y[k] < p["band_y_m"] and abs(fe.x[k]) >= p["start_x_min_m"])

    def end_ok(c, u, k, a):
        fe = c.f[u]
        return bool(np.sign(fe.x[k]) != np.sign(fe.x[a]) and abs(fe.x[k] - fe.x[a]) > p["dx_m"]
                    and c.in_any(u, ("low_post", "block", "dunker_spot", "mid_post"))[k])

    def extra(c, u, s_, t_s, a, e, ts):
        fe = c.f[u]
        pf = [float(p_below(fe.y[k], p["band_y_m"], fe.sig_p[k])) for k in range(a, e + 1)]
        ts.frac("low_band", pf, p["band_frac"])
        ts.ge("Dx", abs(float(fe.x[e] - fe.x[a])), p["dx_m"], _sigd(fe, a, e))
        bs = c.bs[e]
        return dict(ball_side_end=bool(bs != 0 and fe.x[e] * bs > 0))

    return _screen_cut_generic(scene, "cut_cross_screen", p, scr_ok, start_ok, end_ok, extra)


def detect_cut_baseline_exit(scene, **params):
    """Baseline exit: along the baseline to the corner off a screener at y < 1.0 (taxonomy section 8.1)."""
    p = _p("cut_baseline_exit", params)

    def scr_ok(c, s_, t):
        return bool(c.f[s_].y[t] < p["scr_y_max_m"])

    def start_ok(c, u, k):
        return bool(c.f[u].y[k] <= p["band_y_m"] and abs(c.f[u].x[k]) <= p["start_x_max_m"])

    def end_ok(c, u, k, a):
        fe = c.f[u]
        return bool(c.spot(u, "corner_three")[k] and np.sign(fe.x[k]) == np.sign(fe.x[a]) or
                    (c.spot(u, "corner_three")[k] and abs(fe.x[a]) < 0.9))

    def extra(c, u, s_, t_s, a, e, ts):
        fe = c.f[u]
        pf = [float(p_below(fe.y[k], p["band_y_m"], fe.sig_p[k])) for k in range(a, e + 1)]
        ts.frac("baseline_band", pf, p["band_frac"])
        ts.ge("outward", float(abs(fe.x[e]) - abs(fe.x[a])), p["outward_m"], _sigd(fe, a, e))
        return {}

    return _screen_cut_generic(scene, "cut_baseline_exit", p, scr_ok, start_ok, end_ok, extra)


def detect_cut_shuffle(scene, **params):
    """Shuffle (CU.A10): weak-side wing/slot diagonal past a high-post screener to the ball-side block;
    hawk variant when the handler dribbled slot -> wing just before."""
    p = _p("cut_shuffle", params)

    def scr_ok(c, s_, t):
        return bool(c.in_any(s_, ("elbow", "high_post_strip", "pinch_post", "nail"))[t])

    def start_ok(c, u, k):
        fe = c.f[u]
        bs = c.bs[k]
        return bool(bs != 0 and fe.x[k] * bs <= -0.9 and fe.r[k] >= p["start_r_m"]
                    and c.in_any(u, ("wing_three", "slot_three", "wing_high"))[k])

    def end_ok(c, u, k, a):
        fe = c.f[u]
        bs = c.bs[k]
        if bs == 0 or fe.x[k] * bs < 0:
            return False
        return bool(c.in_any(u, ("low_post", "block", "restricted_area"))[k] or fe.r[k] <= p["end_r_m"])

    def extra(c, u, s_, t_s, a, e, ts):
        fe = c.f[u]
        ts.ge("neg_Dr", float(fe.r[a] - fe.r[e]), p["neg_dr_m"], _sigd(fe, a, e))
        ts.flag("after_screen", (e - t_s) * DT <= p["after_s"])
        pa = any(q["passer"] == u and a - F(p["pass_away_s"]) <= q["t_rel"] <= a for q in c.passes())
        hawk = False
        h = c.s.holder[a]
        if h is not None and h != u:
            fh = c.f[h]
            k0 = max(0, a - F(p["hawk_s"]) - F(1.0))
            if all(c.s.holder[k] in (h, None) for k in range(k0, a + 1)):
                hawk = bool(fh.m[k0] - fh.m[a] >= p["hawk_dm_deg"] and c.spot(h, "wing_three")[a]
                            and abs(fe.x[e] - fe.x[a]) >= p["hawk_dx_m"])
        return dict(variant="hawk" if hawk else "shuffle", trigger="dribble_hawk" if hawk else ("pass_away" if pa else "none"),
                    cross_x=bool(np.sign(fe.x[a]) != np.sign(fe.x[e])))

    return _screen_cut_generic(scene, "cut_shuffle", p, scr_ok, start_ok, end_ok, extra)


def detect_cut_chin(scene, **params):
    """Chin (CU.A8): after a reversal, slot/wing cutter to the rim off an elbow back-screener."""
    p = _p("cut_chin", params)
    c = _ctx(scene)
    out = []
    revs = [q for q in c.passes() if (np.sign(q["x0"]) != np.sign(q["x1"]) and min(abs(q["x0"]), abs(q["x1"])) >= 0.9)
            or abs(q["x1"] - q["x0"]) >= p["reversal_dx_m"]]
    for q in revs:
        for u in scene.offense:
            if u in (q["passer"], q["receiver"]):
                continue
            fe = c.f[u]
            for ct in c.contacts(u, max(0, q["t_catch"] - F(0.5)), min(c.n - 1, q["t_catch"] + F(p["after_catch_s"]))):
                s_, t_s = ct["s"], ct["t"]
                if not c.in_any(s_, ("elbow", "high_post_strip", "pinch_post"))[t_s]:
                    continue
                if not c.stationary(s_)[q["t_catch"]:min(c.n, q["t_catch"] + F(p["screener_after_catch_s"]) + 1)].any():
                    continue
                lo = max(0, t_s - F(1.5))
                starts = [k for k in range(lo, t_s + 1) if p["start_r_lo_m"] <= fe.r[k] <= p["start_r_hi_m"]
                          and c.in_any(u, ("slot_three", "wing_three"))[k]]
                if not starts:
                    continue
                a = starts[-1]
                hi = min(c.n - 1, t_s + F(p["rim_within_s"]))
                i_min = t_s + int(np.nanargmin(fe.r[t_s:hi + 1]))
                ts = Tests()
                ts.le("min_r", float(fe.r[i_min]), G["rim_end_r_m"], fe.sig_p[i_min])
                ts.ge("neg_Dr", float(fe.r[a] - fe.r[i_min]), p["neg_dr_m"], _sigd(fe, a, i_min))
                beh, pb, did, amb = _behind_screener(c, u, s_, t_s, a, p["behind_gap_m"])
                cap = None
                if beh is None:
                    cap = G["identity_cap"]
                else:
                    ts.flag("screener_behind_defender", beh, pb)
                    cap = G["identity_cap"] if amb else None
                clear = not any(abs(c.f[v].x[k]) > 3.0 and np.sign(c.f[v].x[k]) == np.sign(fe.x[i_min])
                                for v in scene.offense if v != u for k in range(max(0, i_min - F(1.0)), i_min + 1))
                ev = _emit("cut_chin", {"cutter": u, "screener": s_, "defender": did, "reversal_passer": q["passer"]},
                           t_s, a, i_min, ts, [scene.k(u), scene.k(s_)], p_frame=_pframe_moving(fe), cap=cap,
                           min_conf=p["min_conf"],
                           attrs=dict(t_rev=q["t_rel"], t_s=t_s, min_r=round(float(fe.r[i_min]), 2),
                                      peak_speed=round(float(np.nanmax(fe.speed[a:i_min + 1])), 2), clear_lob=clear, lob=None))
                if ev:
                    out.append(ev)
    return out


def detect_cut_loop(scene, **params):
    """Loop (CU.A9): >= 180 deg cumulative turn within 2.5 s around a stationary teammate."""
    p = _p("cut_loop", params)
    c = _ctx(scene)
    out = []
    for u in scene.offense:
        fe = c.f[u]
        h = fe.hd
        ok = np.isfinite(h) & (np.nan_to_num(fe.speed) >= G["move_exit_mps"]) & c.offball(u)
        cum = np.full(c.n, np.nan)
        acc, prev = 0.0, None
        for t in range(c.n):
            if not ok[t]:
                if prev is not None and t - prev > 3:
                    prev = None
                continue
            if prev is not None:
                acc += ((h[t] - h[prev]) + 540) % 360 - 180
            else:
                acc = 0.0 if np.isnan(cum[max(0, t - 1)]) else acc
            cum[t], prev = acc, t
        t = 0
        while t < c.n:
            if np.isnan(cum[t]):
                t += 1
                continue
            hit = None
            for j in range(t + 1, min(c.n, t + F(p["within_s"]) + 1)):
                if np.isfinite(cum[j]) and abs(cum[j] - cum[t]) >= p["turn_min_deg"]:
                    hit = j
                    break
            if hit is None:
                t += 3
                continue
            idx = [k for k in range(t, hit + 1) if np.isfinite(fe.x[k])]
            cx, cy, R = _circle_fit(fe.x[idx], fe.y[idx])
            best = None
            for s_ in scene.offense:
                if s_ == u:
                    continue
                fs = c.f[s_]
                k_mid = (t + hit) // 2
                dcen = math.hypot(fs.x[k_mid] - cx, fs.y[k_mid] - cy)
                md = float(np.nanmean(c.dist(u, s_)[t:hit + 1]))
                if c.stationary(s_)[t:hit + 1].mean() >= 0.5 and (best is None or dcen < best[1]):
                    best = (s_, dcen, md)
            # fix F05: test the turn at its extremum inside the window, not at the first crossing frame
            jw = [j for j in range(t, min(c.n, t + F(p["within_s"]) + 1)) if np.isfinite(cum[j])]
            j_star = max(jw, key=lambda j: abs(cum[j] - cum[t]))
            ts = Tests()
            ts.ge("cum_turn", abs(cum[j_star] - cum[t]), p["turn_min_deg"], p["cum_turn_sig_deg"])
            if best is None:
                t = hit + 1
                continue
            ts.le("centre_to_teammate", best[1], p["centre_max_m"], 0.3)
            ts.band("orbit_dist", best[2], p["orbit_lo_m"], p["orbit_hi_m"], 0.2)
            mv = c.move_at(u, hit)
            e = mv[1] if mv else hit
            ex = "loop_back" if math.hypot(fe.x[e] - fe.x[t], fe.y[e] - fe.y[t]) <= p["back_m"] else (
                "loop_under" if fe.r[e] < p["under_r_m"] else ("loop_out" if fe.d3[e] >= p["out_d3_m"] else "other"))
            ev = _emit("cut_loop", {"cutter": u, "centre": best[0]}, t, t, e, ts, [scene.k(u)], p_frame=_pframe_moving(fe),
                       min_conf=p["min_conf"],
                       attrs=dict(cum_turn=round(float(cum[j_star] - cum[t]), 1), loop_radius_m=round(R, 2),
                                  exit=ex, variant="canonical"))
            if ev:
                out.append(ev)
            t = e + 1
    return out


# ---- CU.A11 repo variants ----
def detect_cut_blade(scene, **params):
    """Blade (CU.A11): ball-side corner player cuts to the rim during a same-side ball screen and roll."""
    p = _p("cut_blade", params)
    c = _ctx(scene)
    out = []
    for bs_ in c.ball_screens():
        t_b, h, s_ = bs_["t"], bs_["handler"], bs_["screener"]
        hi = min(c.n - 1, t_b + F(p["within_s"]))
        fs = c.f[s_]
        roll = float(fs.r[t_b] - np.nanmin(fs.r[t_b:hi + 1]))
        for u in scene.offense:
            if u in (h, s_):
                continue
            fe = c.f[u]
            if not (c.spot(u, "corner_three")[t_b] and c.bs[t_b] != 0 and fe.x[t_b] * c.bs[t_b] > 0):
                continue
            i_min = t_b + int(np.nanargmin(fe.r[t_b:hi + 1]))
            ts = Tests()
            ts.le("min_r", float(fe.r[i_min]), G["rim_end_r_m"], fe.sig_p[i_min])
            ts.ge("screener_roll", roll, p["roll_dr_m"], math.sqrt(2) * fs.sig_p[t_b])
            ev = _emit("cut_blade", {"cutter": u, "screener": s_, "ball_handler": h}, t_b, t_b, i_min, ts,
                       [scene.k(u), scene.k(s_)], min_conf=p["min_conf"],
                       attrs=dict(min_r=round(float(fe.r[i_min]), 2), screener_roll_m=round(roll, 2)))
            if ev:
                out.append(ev)
    return out


def detect_cut_rub(scene, **params):
    """Rub cut (CU.A11): brushes a stationary post (<= 0.8 m, r < 3.5) at speed to the rim; defender held up."""
    p = _p("cut_rub", params)
    c = _ctx(scene)
    out = []
    for u in scene.offense:
        fe = c.f[u]
        for ct in c.contacts(u, max_d=p["pass_by_m"], widen=True):
            s_, t_c = ct["s"], ct["t"]
            if not c.f[s_].r[t_c] < p["post_r_m"]:
                continue
            hi = min(c.n - 1, t_c + F(p["rim_within_s"]))
            i_min = t_c + int(np.nanargmin(fe.r[t_c:hi + 1]))
            lo = max(0, t_c - F(p["before_s"]))
            ts = Tests()
            # fix F14: the pass-by distance is a test (sigma = pair sigma), so a 1.1 m pass-by cannot be strict
            ts.le("pass_by", ct["d"], p["pass_by_m"], ct["sig"])
            ts.le("min_r", float(fe.r[i_min]), G["rim_end_r_m"], fe.sig_p[i_min])
            pk = float(np.nanmax(fe.speed[lo:hi + 1]))
            ts.ge("peak_speed", pk, p["peak_mps"], float(np.nanmedian(fe.sig_speed[lo:hi + 1])))
            did, amb, _ = c.defender(u, lo, t_c)
            held, cap = None, G["identity_cap"]
            if did is not None:
                fd = c.f[did]
                near = np.nanmin(c.dist(did, s_)[lo:hi + 1]) <= p["def_post_m"]
                v0 = float(np.nanmean(fd.speed[lo:t_c + 1]))
                v1 = float(np.nanmin(fd.speed[t_c:hi + 1]))
                held = bool(near and v0 > 0 and (v0 - v1) / v0 >= p["def_slow_frac"])
                ts.flag("defender_held", held)
                cap = G["identity_cap"] if amb else None
            ev = _emit("cut_rub", {"cutter": u, "post": s_, "defender": did}, t_c, lo, i_min, ts, [scene.k(u), scene.k(s_)],
                       p_frame=_pframe_moving(fe), cap=cap, min_conf=p["min_conf"],
                       attrs=dict(closest_approach_m=round(ct["d"], 2), min_r=round(float(fe.r[i_min]), 2), defender_held=held))
            if ev:
                out.append(ev)
    return out


def detect_cut_circle(scene, **params):
    """Circle cut (CU.A11, MSU 14-Circle): over the elbows, then down around an elbow player to the rim."""
    p = _p("cut_circle", params)
    c = _ctx(scene)
    out = []
    for u in scene.offense:
        fe = c.f[u]
        for tt in c.turns(u, p["turn_lo_deg"] - 15):
            t = tt["t"]
            lo = max(0, t - F(1.5))
            hi = min(c.n - 1, t + F(p["rim_within_s"]))
            w3 = slice(max(0, t - F(0.3)), t + F(0.3) + 1)  # closest approach around the turn
            els = [s_ for s_ in scene.offense if s_ != u and c.spot(s_, "elbow")[t] and c.stationary(s_)[t]
                   and np.nanmin(c.dist(u, s_)[w3]) <= p["turn_d_m"]]
            if not els:
                continue
            i_min = t + int(np.nanargmin(fe.r[t:hi + 1]))
            ts = Tests()
            ts.band("turn", abs(tt["A"]), p["turn_lo_deg"], p["turn_hi_deg"], tt["sig"])
            ts.ge("start_r", float(np.nanmax(fe.r[lo:t + 1])), p["start_r_m"], fe.sig_p[lo])
            t_a = max(lo, t - F(c.skip_s(u) + 0.2))  # approach only (excludes the plant and the down leg)
            # 10th percentile rather than the minimum: robust to single-frame excursions of the smoothed y
            ts.ge("above_elbows", float(np.nanpercentile(fe.y[lo:t_a + 1], 10)), p["min_y_m"],
                  float(np.nanmax(fe.sig_p[lo:t_a + 1])))
            ts.le("min_r", float(fe.r[i_min]), G["rim_end_r_m"], fe.sig_p[i_min])
            br = math.hypot(c.bx[t], c.by[t]) if np.isfinite(c.bx[t]) else np.nan
            ts.band("ball_high_post", br, p["ball_r_lo_m"], p["ball_r_hi_m"], 0.2)
            ev = _emit("cut_circle", {"cutter": u, "screener": els[0]}, t, lo, i_min, ts, [scene.k(u)],
                       p_frame=_pframe_moving(fe), min_conf=p["min_conf"],
                       attrs=dict(t_turn=t, Dpsi_turn=round(tt["A"], 1), min_r=round(float(fe.r[i_min]), 2)))
            if ev:
                out.append(ev)
    return out


def detect_cut_laker(scene, **params):
    """Laker cut (CU.A11): post entry pass, the passer cuts off the post receiver to the rim."""
    p = _p("cut_laker", params)
    c = _ctx(scene)
    out = []
    for q in c.passes():
        A, P_, tp = q["passer"], q["receiver"], q["t_rel"]
        fp = c.f[P_]
        if not fp.r[q["t_catch"]] < p["post_r_m"]:
            continue
        fe = c.f[A]
        hi = min(c.n - 1, tp + F(p["rim_within_s"]))
        dd = c.dist(A, P_)
        tc = tp + int(np.nanargmin(dd[tp:hi + 1]))
        i_min = tp + int(np.nanargmin(fe.r[tp:hi + 1]))
        ts = Tests()
        ts.le("pass_by", float(dd[tc]), G["screen_contact_m"], math.hypot(fe.sig_p[tc], fp.sig_p[tc]))
        ts.le("min_r", float(fe.r[i_min]), G["rim_end_r_m"], fe.sig_p[i_min])
        recs = [r_ for r_ in _cut_recs(c, A) if tp - F(0.3) <= r_["on"] <= tp + F(1.0)]
        ts.flag("cut", bool(recs))
        ret = any(q2["passer"] == P_ and q2["receiver"] == A and tc <= q2["t_rel"] <= tc + F(p["return_s"])
                  for q2 in c.passes())
        ev = _emit("cut_laker", {"cutter": A, "post": P_}, tp, tp, i_min, ts, [scene.k(A), scene.k(P_)],
                   p_frame=_pframe_moving(fe), min_conf=p["min_conf"],
                   attrs=dict(t_pass=tp, side="high" if fe.y[tc] > fp.y[tc] else "low", return_pass=ret,
                              min_r=round(float(fe.r[i_min]), 2)))
        if ev:
            out.append(ev)
    return out


def detect_cut_veer(scene, **params):
    """Veer cut (hoopsgeek): approach the defender, veer 30-90 deg next to him, accelerate away."""
    p = _p("cut_veer", params)
    c = _ctx(scene)
    out = []
    if not scene.defense:
        return out
    for u in scene.offense:
        fe = c.f[u]
        # fix F08r (loop 2): in the high-noise tier t_turn scatters +-0.3-0.5 s along an unplanted veer. The away
        # window is padded by turn_pad_high_noise_s, and the defender tests (approach, near) are taken at the
        # closest approach to the defender within +-turn_pad_high_noise_s of t_turn.
        pad = p["turn_pad_high_noise_s"] if c.high_noise(u) else 0.0
        away_s = p["away_s"] + pad
        for tt in c.turns(u, p["turn_lo_deg"] - 10):
            t = tt["t"]
            lo, hi = max(0, t - F(p["approach_s"])), min(c.n - 1, t + F(away_s))
            if not c.offball(u)[t]:
                continue
            did, amb, _ = c.defender(u, lo, t)
            if did is None:
                continue
            dd = c.dist(u, did)
            # the defender tests use the closest approach within +-pad of t_turn (pad 0 outside the high-noise tier)
            w0, w1 = max(0, t - F(pad)), min(c.n - 1, t + F(pad))
            tn = w0 + int(np.nanargmin(dd[w0:w1 + 1])) if np.isfinite(dd[w0:w1 + 1]).any() else t
            ln = max(0, tn - F(p["approach_s"]))
            ts = Tests()
            ts.band("turn", abs(tt["A"]), p["turn_lo_deg"], p["turn_hi_deg"], tt["sig"])
            # fix L5-03 (loop 5, C4-C): in the high-noise tier tn is the closest approach picked inside +-pad (a
            # look-elsewhere selection that biases the closing distance up), and real defenders are always near, so a
            # jog past one read as a veer (real cut_veer x6.7 at added noise 0.5). There the closing must clear
            # approach_m by approach_k_high_noise x its sigma (a significant approach), as F21r does for the CUT edge.
            sa = math.sqrt(2) * fe.sig_p[tn]
            ts.ge("approach", float(dd[ln] - dd[tn]), p["approach_m"] + (p["approach_k_high_noise"] * sa if pad > 0 else 0.0), sa)
            ts.le("near_defender", float(dd[tn]), p["near_m"], math.hypot(fe.sig_p[tn], c.f[did].sig_p[tn]))
            ts.ge("away", math.hypot(fe.x[hi] - fe.x[t], fe.y[hi] - fe.y[t]), p["away_m"], _sigd(fe, t, hi))
            if pad > 0:
                # fix L6-02 (loop 6): in the high-noise tier the veer needs joint evidence beyond its noise. The turn and
                # the approach are the two veer-specific tests and both sat near their edges on the events noise adds
                # (real n0.5 noise-only: turn z median 0.75, approach z 1.8, vs 1.3 / 3.1 on events that are also
                # veers clean); their summed z must reach evidence_k_high_noise. Declined: an away margin
                # (away_m + 1 sigma: synthetic veer_slot mirror 7 -> 3 of 10) and a defender-distance gain test (cost
                # synthetic veers, did not separate real noise-only events).
                zt, za = ts.z["turn"], ts.z["approach"]
                ts.ge("veer_evidence", zt + za, p["evidence_k_high_noise"], math.sqrt(2.0))
            # t0 = t_turn; in the high-noise tier the closest approach tn (the veer happens next to the defender)
            t0 = tn if pad > 0 else t
            ev = _emit("cut_veer", {"cutter": u, "defender": did}, t0, min(lo, ln), hi, ts, [scene.k(u)],
                       cap=G["identity_cap"] if amb else None, min_conf=p["min_conf"],
                       attrs=dict(t_turn=t, t_closest=tn, Dpsi_turn=round(tt["A"], 1)))
            if ev:
                out.append(ev)
    return out


# ======================================================================================
# Relocations (CU.P15 - CU.P20, CU.A13)
# ======================================================================================
def _reloc_windows(c, o):
    """Relocation motion windows: speed >= 1.0 m/s hysteresis, no speed gate beyond that."""
    return c.moves(o, enter=G["move_exit_mps"], exit_=G["move_exit_mps"])


def _assoc(c, o, t_on, kinds, lo_s, hi_s):
    """CU.R2: the trigger with dt = t_on - t_trig in [lo_s, hi_s] s and the smallest |dt|."""
    cands = [(k, t, a) for k, t, a in c.triggers(o) if k in kinds and lo_s <= (t_on - t) * DT <= hi_s]
    if not cands:
        return None
    return min(cands, key=lambda z: abs(t_on - z[1]))


def detect_relocate(scene, **params):
    """Generic relocation (CU.P15): >= 2.0 m to a different region, triggered by a ball event."""
    p = _p("relocate", params)
    c = _ctx(scene)
    out = []
    kinds = ("drive", "ball_screen", "pass", "own_pass", "catch", "paint_touch")
    for o in scene.offense:
        fe = c.f[o]
        for a, b in _reloc_windows(c, o):
            if (b - a) * DT > p["max_s"]:
                continue
            if not (fe.d3[a] >= p["start_d3_m"] or c.in_any(o, ("dunker_spot", "short_corner"))[a]):
                continue
            disp = math.hypot(fe.x[b] - fe.x[a], fe.y[b] - fe.y[a])
            if fe.r[b] - fe.r[a] <= -p["cut_dr_m"]:
                continue
            dw = F(p["dwell_s"])
            r0, r1 = c.region(o, a), c.region(o, b)
            stable = c.region(o, max(0, a - dw)) == r0 and c.region(o, min(c.n - 1, b + dw)) == r1
            rec_, _ = _received(c, o, b, b + 3)
            settled = rec_ or bool(np.all(np.nan_to_num(fe.speed[b + 1:b + 1 + F(0.2)], nan=0) < G["move_exit_mps"]))
            ts = Tests()
            ts.ge("disp", disp, p["disp_m"], _sigd(fe, a, b))
            ts.flag("new_region", r0 != r1 and stable)
            ts.flag("settled", settled)
            trg = _assoc(c, o, a, kinds, p["trig_lo_s"], p["trig_hi_s"])
            t0 = trg[1] if trg else a
            ev = _emit("relocate", {"player": o, "trigger_actor": trg[2] if trg else None}, t0, min(a, t0), b, ts,
                       [scene.k(o)], min_conf=p["min_conf"],
                       attrs=dict(variant="relocate" if trg else "reposition", trigger_kind=trg[0] if trg else None,
                                  dt_trigger_s=round((a - trg[1]) * DT, 2) if trg else None, t_onset=a, t_arrival=b,
                                  start_region=r0, end_region=r1, Dr=round(float(fe.r[b] - fe.r[a]), 2),
                                  Dm=round(float(fe.m[b] - fe.m[a]), 1), received_ball=rec_))
            if ev:
                out.append(ev)
    return out


def _corner_move(c, o, a, b, landing, dm_sign, dm_min, within_s, start_sids):
    """Relocation from a (in start_sids when given) into `landing` (same side) with signed Dm >= dm_min within
    within_s; returns (t_landing, Dm) or None."""
    fe = c.f[o]
    if start_sids is not None and not c.in_any(o, start_sids)[a]:
        return None
    hi = min(c.n - 1, a + F(within_s))
    ok = [t for t in range(a, hi + 1)
          if c.spot(o, landing)[t] and np.sign(fe.x[t]) == np.sign(fe.x[a]) and dm_sign * (fe.m[t] - fe.m[a]) >= dm_min]
    if not ok:
        return None
    # landing = the arrival: the in-region frame (until the relocation settles) with the largest signed Dm
    cand = [t for t in ok if t <= max(ok[0], b + F(0.2))]
    t = max(cand, key=lambda k: dm_sign * (fe.m[k] - fe.m[a]))
    return t, float(fe.m[t] - fe.m[a])


def _dm_sig(fe, a, t):
    return math.degrees(math.hypot(fe.sig_p[a] / max(fe.r[a], 1), fe.sig_p[t] / max(fe.r[t], 1)))


def detect_lift(scene, **params):
    """Lift (CU.P16, named_spots 0.3.2): corner_three to the lift landing, m +10 deg within 2.5 s."""
    p = _p("lift", params)
    c = _ctx(scene)
    out = []
    for o in scene.offense:
        fe = c.f[o]
        for a, b in _reloc_windows(c, o):
            hit = _corner_move(c, o, a, b, "lift", +1, p["dm_deg"], p["within_s"], ("corner_three",))
            if hit is None or _was_screener(c, o, a, p["screener_precedence_s"]):
                continue
            tl, dm = hit
            ts = Tests()
            ts.ge("Dm", dm, p["dm_deg"], _dm_sig(fe, a, tl))
            ts.flag("start_corner", True)
            ts.flag("landing", True)
            trg = _assoc(c, o, a, ("drive", "ball_screen"), p["trig_lo_s"], p["trig_hi_s"])
            t0 = trg[1] if trg else a
            rec_, tcat = _received(c, o, tl, tl + F(1.0))
            ev = _emit("lift", {"player": o, "trigger_actor": trg[2] if trg else None}, t0, min(a, t0), tl, ts,
                       [scene.k(o)], min_conf=p["min_conf"],
                       attrs=dict(Dm=round(dm, 1), t_onset=a, t_landing=tl, trigger_kind=trg[0] if trg else None,
                                  dt_trigger_s=round((a - trg[1]) * DT, 2) if trg else None,
                                  end_region=c.region(o, tl), received_ball=rec_))
            if ev:
                out.append(ev)
    return out


def detect_drift(scene, **params):
    """Drift (CU.P17, named_spots 0.3.2): m -10 deg within 2.0 s of a DRIVE start into the drift landing."""
    p = _p("drift", params)
    return _drift_like(scene, p, "drift")


def detect_cut_hammer(scene, **params):
    """Hammer: a drift to the weak-side corner off a flare screen during a baseline drive (taxonomy 8.1)."""
    p = _p("cut_hammer", params)
    return _drift_like(scene, p, "cut_hammer")


def _drift_like(scene, p, kind):
    c = _ctx(scene)
    out = []
    for d in c.drives():
        for o in scene.offense:
            if o == d["driver"]:
                continue
            fe = c.f[o]
            for a, b in _reloc_windows(c, o):
                if not (d["t"] - F(p["onset_before_s"]) <= a <= d["t"] + F(p["onset_after_s"])):
                    continue
                if not fe.d3[a] >= p["start_d3_m"]:
                    continue
                landing = "drift" if kind == "drift" else "corner_three"
                hit = _corner_move(c, o, a, b, landing, -1, p["dm_deg"], p["within_s"], None)
                if hit is None:
                    continue
                tl = hit[0]
                ts = Tests()
                ts.le("Dm", float(fe.m[tl] - fe.m[a]), -p["dm_deg"], _dm_sig(fe, a, tl))
                same = np.sign(fe.x[a]) == d["side"]
                tag = ("baseline_drive_drift" if d["kind"] == "baseline" and not same else
                       "middle_drive_drift" if d["kind"] == "middle" and same else "other")
                actors = {"player": o, "driver": d["driver"]}
                kins = [scene.k(o)]
                if kind == "cut_hammer":
                    if d["kind"] != "baseline" or same:
                        continue
                    scr = c.contacts(o, a, tl)
                    if not scr:
                        continue
                    ts.flag("flare_screen", True)
                    actors["screener"] = scr[0]["s"]
                    kins.append(scene.k(scr[0]["s"]))
                rec_, _ = _received(c, o, tl, tl + F(1.0))
                ev = _emit(kind, actors, d["t"], min(a, d["t"]), tl, ts, kins, min_conf=p["min_conf"],
                           attrs=dict(Dm=round(float(fe.m[tl] - fe.m[a]), 1), t_onset=a, t_landing=tl, side_tag=tag,
                                      drive_kind=d["kind"], dt_from_drive_s=round((a - d["t"]) * DT, 2),
                                      end_region=c.region(o, tl), received_ball=rec_))
                if ev:
                    out.append(ev)
                    break
    return out


def detect_shake(scene, **params):
    """Shake (CU.P18, named_spots 0.3.2): ball-side corner lift within 1.0 s of a side/slot/high ball screen."""
    p = _p("shake", params)
    c = _ctx(scene)
    out = []
    for bs_ in c.ball_screens():
        t_b, h = bs_["t"], bs_["handler"]
        if not c.in_any(h, ("pnr_location_side", "pnr_location_slot", "pnr_location_high"))[t_b]:
            continue
        fh = c.f[h]
        hi = min(c.n - 1, t_b + F(p["handler_within_s"]))
        h_dx = float(abs(fh.x[t_b]) - np.nanmin(np.abs(fh.x[t_b:hi + 1])))
        for o in scene.offense:
            if o in (h, bs_["screener"]):
                continue
            fe = c.f[o]
            if not (c.bs[t_b] != 0 and fe.x[t_b] * c.bs[t_b] > 0):
                continue
            for a, b in _reloc_windows(c, o):
                if abs(a - t_b) > F(p["start_within_s"]):
                    continue
                hit = _corner_move(c, o, a, b, "shake", +1, p["dm_deg"], p["within_s"], ("corner_three",))
                if hit is None:
                    continue
                tl, dm = hit
                ts = Tests()
                ts.ge("Dm", dm, p["dm_deg"], _dm_sig(fe, a, tl))
                ts.ge("handler_to_middle", h_dx, p["handler_dx_m"], math.sqrt(2) * fh.sig_p[t_b])
                ev = _emit("shake", {"player": o, "ball_handler": h, "screener": bs_["screener"]}, t_b, min(a, t_b), tl, ts,
                           [scene.k(o)], min_conf=p["min_conf"],
                           attrs=dict(Dm=round(dm, 1), handler_dx=round(h_dx, 2), dt_from_screen_s=round((a - t_b) * DT, 2),
                                      t_landing=tl))
                if ev:
                    out.append(ev)
    return out


def detect_dunker_slide(scene, **params):
    """Dunker slide (Hoiberg slide): weak dunker to the strong dunker/short corner as a teammate enters the lane."""
    p = _p("dunker_slide", params)
    c = _ctx(scene)
    out = []
    for e_ in scene.offense:
        fr = c.f[e_]
        for t in range(1, c.n):
            if not (fr.r[t - 1] > p["lane_r_m"] >= fr.r[t] and fr.vr[t] >= p["entry_vr_mps"] and c.offball(e_)[t]):
                continue
            for o in scene.offense:
                if o == e_:
                    continue
                fe = c.f[o]
                lo = max(0, t - F(0.5))
                if not c.spot(o, "dunker_spot")[lo:t + 1].any():
                    continue
                k0 = lo + int(np.argmax(c.spot(o, "dunker_spot")[lo:t + 1]))
                hi = min(c.n - 1, t + F(p["within_s"]))
                cross = [k for k in range(k0 + 1, hi + 1) if np.sign(fe.x[k]) != np.sign(fe.x[k0])]
                if not cross:
                    continue
                kc = cross[0]
                ends = [k for k in range(kc, hi + 1) if c.in_any(o, ("dunker_spot", "short_corner"))[k]]
                if not ends:
                    continue
                ts = Tests()
                ts.le("cross_y", float(fe.y[kc]), p["cross_y_m"], fe.sig_p[kc])
                ts.flag("arrive", True)
                scr = any(bs_["screener"] == e_ and t - F(2.0) <= bs_["t"] <= t for bs_ in c.ball_screens())
                ev = _emit("dunker_slide", {"player": o, "roller": e_}, t, k0, ends[0], ts, [scene.k(o)],
                           min_conf=p["min_conf"],
                           attrs=dict(t_cross=kc, t_arrival=ends[0], roller_was_screener=scr,
                                      end_spot=c.region(o, ends[0])))
                if ev:
                    out.append(ev)
    return out


def detect_fill(scene, **params):
    """Fill / replace / refill / fill_slide_arc (CU.A13, named_spots fill_slide) into a vacated perimeter spot."""
    p = _p("fill", params)
    c = _ctx(scene)
    out = []
    anchors = []
    for sid in ("corner_three", "wing_three", "slot_three", "top_three"):
        an = SPOTS[sid].d["anchor"]
        anchors.append((sid, an["x"], an["y"]))
        if an["x"]:
            anchors.append((sid, -an["x"], an["y"]))
    for sid, axp, ayp in anchors:
        for A in scene.offense:
            fa = c.f[A]
            da = np.hypot(fa.x - axp, fa.y - ayp)
            occ = np.nan_to_num(da, nan=99) <= p["arrive_m"]
            spa = np.nan_to_num(fa.speed, nan=99.0)
            for i0, i1 in _intervals(occ):
                if (i1 - i0) * DT < p["occupy_s"]:
                    continue
                # fix L4-05 (loop 4): A must have occupied the spot (settled), not run through its 1.2 m disc. The
                # smoothed speed of a resting player is biased up by about its sigma (median 0.4-0.9 m/s at rest at
                # sigma_p 0.3-0.5), so the median-speed limit is occupy_max_mps + occupy_sig_k x median sig_speed
                lim_a = p["occupy_max_mps"] + p["occupy_sig_k"] * float(np.nanmedian(fa.sig_speed[i0:i1 + 1]))
                if float(np.median(spa[i0:i1 + 1])) > lim_a:
                    continue
                left = [t for t in range(i1, c.n) if da[t] > p["leave_m"]]
                if not left:
                    continue
                tv = left[0]
                for B in scene.offense:
                    if B == A:
                        continue
                    fb = c.f[B]
                    db = np.hypot(fb.x - axp, fb.y - ayp)
                    arr = [t for t in range(tv, min(c.n, tv + F(p["within_s"]) + 1)) if db[t] <= p["arrive_m"]]
                    if not arr or db[tv] <= p["arrive_m"]:
                        continue
                    # fix F04: arrival = the closest frame to the anchor within settle_s after the first entry
                    # (t_settle); 'moved' is measured to it, so wing->slot (2.86 m) and slot->top fills pass
                    ta0 = arr[0]
                    seg = db[ta0:min(c.n, ta0 + F(p["settle_s"]) + 1)]
                    ta = ta0 + int(np.nanargmin(seg))
                    # fix L4-05: B must settle in the spot, during his own team's possession; a teammate running
                    # through the vacated spot is not a fill. Settled = within arrive_m on >= stay_frac of the
                    # stay_s after t_arrival (a fraction, so one noisy frame beyond arrive_m does not break it; the
                    # window is cut at the end of the clip but must hold >= occupy_s)
                    stay = np.nan_to_num(db[ta:min(c.n, ta + F(p["stay_s"]) + 1)], nan=99.0)
                    if len(stay) < F(p["occupy_s"]) + 1 or float(np.mean(stay <= p["arrive_m"])) < p["stay_frac"] \
                            or not c.own[ta] or not c.own[tv]:
                        continue
                    k0 = max(0, tv - F(p["pre_s"]))
                    moved = max(math.hypot(fb.x[ta] - fb.x[k], fb.y[ta] - fb.y[k]) for k in range(k0, tv + 1))
                    ts = Tests()
                    ts.ge("filler_move", moved, p["move_m"], _sigd(fb, k0, ta))
                    ts.le("arrive", float(db[ta]), p["arrive_m"], fb.sig_p[ta])
                    w0, w1 = tv - F(p["vacate_before_s"]), tv + F(p["vacate_after_s"])
                    drove = any(d["driver"] == A and w0 <= d["t"] <= w1 for d in c.drives())
                    cut = any(w0 <= r_["on"] <= w1 for r_ in _cut_recs(c, A))
                    scr = any(s_["screener"] == A and w0 <= s_["t"] <= w1 for s_ in c.ball_screens())
                    kind = "fill" if (drove or cut) else ("replace" if scr else "refill")
                    arc = abs(fb.r[ta] - fb.r[k0]) <= p["slide_dr_m"]
                    ev = _emit("fill", {"vacator": A, "filler": B}, tv, tv, ta, ts, [scene.k(A), scene.k(B)],
                               min_conf=p["min_conf"],
                               attrs=dict(spot_id=sid, anchor=(axp, ayp), kind=kind, fill_slide_arc=bool(arc),
                                          dt_fill_s=round((ta - tv) * DT, 2), t_arrival=ta))
                    if ev:
                        out.append(ev)
                        break
    return out


def detect_sprint_to_corner(scene, **params):
    """Sprint to corner (CU.P19): transition (needs scene.possession_t0) or half-court high-speed corner fill."""
    p = _p("sprint_to_corner", params)
    c = _ctx(scene)
    out = []
    pt0 = getattr(scene, "possession_t0", None)
    for o in scene.offense:
        fe = c.f[o]
        if pt0 is not None:
            hi = min(c.n - 1, pt0 + F(p["transition_within_s"]))
            arr = [t for t in range(pt0, hi + 1) if c.spot(o, "transition_corner_arrival")[t]]
            if arr:
                ta = arr[0]
                L = _resampled_length(fe.x, fe.y, pt0, ta)
                v5, sv, _ = _best_window_speed(fe, pt0, ta, p["speed_window_s"])
                ts = Tests()
                ts.ge("path_length", L, p["transition_len_m"], 0.5)
                ts.ge("best_0p5s_speed", v5, p["peak_mps"], sv)
                hc = [t for t in range(pt0, ta) if fe.y[t] > C["HALF_Y"] >= fe.y[t + 1]]
                lane_x = round(float(abs(fe.x[hc[0]])), 2) if hc else None
                ev = _emit("sprint_to_corner", {"player": o}, pt0, pt0, ta, ts, [scene.k(o)], min_conf=p["min_conf"],
                           attrs=dict(variant="transition", arrival_t_since_t0_s=round((ta - pt0) * DT, 2),
                                      best_0p5s_speed=round(v5, 2), path_length=round(L, 1), lane_x_at_half=lane_x,
                                      wing_lane=bool(lane_x is not None and 5.3 <= lane_x <= 7.62)))
                if ev:
                    out.append(ev)
                continue
        ent = [t for t in range(1, c.n) if c.spot(o, "corner_three")[t] and not c.spot(o, "corner_three")[t - 1]]
        cz = c.spot(o, "corner_three")
        ent = [t for t in ent if not cz[max(0, t - F(1.0)):t].any()]  # a new entry: out of the corner for >= 1.0 s
        for ta in ent:
            lo = max(0, ta - F(p["half_within_s"]))
            st = [k for k in range(lo, ta) if math.hypot(fe.x[ta] - fe.x[k], fe.y[ta] - fe.y[k]) >= p["half_travel_m"]]
            if not st:
                continue
            # fix F05: travel is tested at its extremum in the window (the farthest frame), and the event starts
            # at the run start (the start of the MOVE that reaches the corner, clipped to the window), not at the
            # last frame >= 4.0 m away
            k_far = max(st, key=lambda k: math.hypot(fe.x[ta] - fe.x[k], fe.y[ta] - fe.y[k]))
            mv = c.move_at(o, st[-1])
            a = max(lo, mv[0]) if mv is not None and mv[0] <= st[-1] else st[-1]
            v5, sv, _ = _best_window_speed(fe, max(lo, st[-1] - F(p["speed_lead_s"])), ta, p["speed_window_s"])
            ts = Tests()
            ts.ge("travel", math.hypot(fe.x[ta] - fe.x[k_far], fe.y[ta] - fe.y[k_far]), p["half_travel_m"],
                  _sigd(fe, k_far, ta))
            ts.ge("best_0p5s_speed", v5, p["peak_mps"], sv)
            ev = _emit("sprint_to_corner", {"player": o}, a, a, ta, ts, [scene.k(o)], min_conf=p["min_conf"],
                       attrs=dict(variant="half_court", best_0p5s_speed=round(v5, 2), t_arrival=ta))
            if ev:
                out.append(ev)
    return out


def detect_rim_run(scene, **params):
    """Rim run (CU.P20): own rim area to the attacked rim, >= 20 m down the middle, fast."""
    p = _p("rim_run", params)
    c = _ctx(scene)
    out = []
    pt0 = getattr(scene, "possession_t0", None)
    for o in scene.offense:
        fe = c.f[o]
        r_own = np.hypot(fe.x, fe.y - OWN_RIM_Y)
        near_own = np.nan_to_num(r_own, nan=99) <= p["start_r_own_m"]
        arrive = np.nan_to_num(fe.r, nan=99) <= p["end_r_m"]
        for ta in [t for t in range(1, c.n) if arrive[t] and not arrive[t - 1]]:
            dep = [t for t in range(0, ta) if near_own[t]]
            if not dep:
                continue
            # start of the run: the last slow frame (speed < 1.0) of the own-rim stay, else its first frame
            k = dep[-1]
            while k - 1 >= 0 and near_own[k - 1]:
                k -= 1
            slow = [j for j in range(k, dep[-1] + 1) if fe.speed[j] < G["move_exit_mps"]]
            t_s = slow[-1] if slow else k
            if pt0 is not None and not (pt0 - F(p["start_before_s"]) <= t_s <= pt0 + F(p["start_within_s"])):
                continue
            L = _resampled_length(fe.x, fe.y, t_s, ta)
            T = (ta - t_s) * DT
            v5, sv, _ = _best_window_speed(fe, t_s, ta, p["speed_window_s"])
            ts = Tests()
            ts.ge("path_length", L, p["length_m"], 0.5)
            ts.le("mean_abs_x", float(np.nanmean(np.abs(fe.x[t_s:ta + 1]))), p["mean_abs_x_m"], 0.1)
            ts.ge("mean_speed", L / T, p["mean_mps"], 0.15)
            ts.ge("best_0p5s_speed", v5, p["peak_mps"], sv)
            tb = None
            if np.isfinite(c.bx).any():
                br = np.hypot(c.bx, c.by)
                hit = [t for t in range(t_s, c.n) if np.isfinite(br[t]) and br[t] < C["ARC_R"]]
                tb = hit[0] if hit else None
            if tb is not None:
                ts.flag("arrival_vs_ball", ta <= tb + F(p["after_ball_s"]))
            sp = np.nan_to_num(fe.speed[t_s:ta + 1], nan=0) >= p["repo_mps"]
            repo = any((i1 - i0) * DT >= p["repo_s"] for i0, i1 in _intervals(sp))
            t0 = pt0 if pt0 is not None else t_s
            ev = _emit("rim_run", {"runner": o}, t0, min(t0, t_s), ta, ts, [scene.k(o)], min_conf=p["min_conf"],
                       attrs=dict(t_start=t_s, t_arrival=ta, path_length=round(L, 1), mean_speed=round(L / T, 2),
                                  best_0p5s_speed=round(v5, 2), t0_proxy=pt0 is None,
                                  arrival_vs_ball_s=None if tb is None else round((ta - tb) * DT, 2),
                                  rim_run_repo=repo, first_big_down=None))
            if ev:
                out.append(ev)
    return out


# ======================================================================================
# Sequence tags (CU.R4)
# ======================================================================================
def detect_give_and_go(scene, **params):
    """Give-and-go (CU.R4): pass a->b, a rim cut by a within 1.0 s, return pass b->a within 2.0 s of onset."""
    p = _p("give_and_go", params)
    c = _ctx(scene)
    out = []
    P = c.passes()
    for q in P:
        a_, b_ = q["passer"], q["receiver"]
        fe = c.f[a_]
        for rec in _cut_recs(c, a_):
            if not (q["t_rel"] - F(0.3) <= rec["on"] <= q["t_rel"] + F(p["cut_within_s"])):
                continue
            back = [q2 for q2 in P if q2["passer"] == b_ and q2["receiver"] == a_ and
                    rec["on"] <= q2["t_rel"] <= rec["on"] + F(p["return_within_s"])]
            if not back:
                continue
            tcat = back[0]["t_catch"]
            ts = _cut_tests(c, rec, PARAMS["cut"])
            ts.le("catch_r", float(fe.r[tcat]), p["catch_r_m"], fe.sig_p[tcat])
            ev = _emit("give_and_go", {"cutter": a_, "receiver": b_}, q["t_rel"], q["t_rel"], tcat, ts, [scene.k(a_)],
                       min_conf=p["min_conf"], attrs=dict(t_pass=q["t_rel"], t_onset=rec["on"], t_return=back[0]["t_rel"]))
            if ev:
                out.append(ev)
            break
    return out


def detect_blind_pig(scene, **params):
    """Blind pig (offense A5.22): pass to a high-post flasher, backdoor by a wing, pass to the cutter."""
    p = _p("blind_pig", params)
    c = _ctx(scene)
    out = []
    P = c.passes()
    bds = detect_cut_backdoor(scene)
    for q in P:
        big = q["receiver"]
        if not c.in_any(big, ("high_post_area", "elbow"))[q["t_catch"]]:
            continue
        for bd in bds:
            u = bd.actors["cutter"]
            if u in (big, q["passer"]):
                continue
            if not (q["t_catch"] - F(0.5) <= bd.t0 <= q["t_catch"] + F(p["backdoor_within_s"])):
                continue
            hit = [q2 for q2 in P if q2["passer"] == big and q2["receiver"] == u and bd.t0 <= q2["t_rel"] <= bd.t0 + F(p["feed_within_s"])]
            if not hit:
                continue
            fb = c.f[big]
            k = max(0, q["t_catch"] - F(2.0))
            flash = bool(fb.y[q["t_catch"]] - fb.y[k] >= p["flash_dy_m"])
            ts = Tests()
            ts.flag("sequence", True, bd.conf)
            ev = _emit("blind_pig", {"handler": q["passer"], "big": big, "cutter": u}, q["t_rel"], q["t_rel"],
                       hit[0]["t_catch"], ts, [scene.k(u), scene.k(big)], min_conf=p["min_conf"],
                       attrs=dict(t_entry=q["t_catch"], t_rev=bd.t0, t_feed=hit[0]["t_rel"], big_flashed=flash))
            if ev:
                out.append(ev)
    return out


def detect_wiper(scene, **params):
    """Wiper (offense 8.1): the same cutter uses a flare and a pin-down within 2.5 s."""
    p = _p("wiper", params)
    out = []
    fl = detect_cut_flare(scene)
    pd = detect_cut_pin_down(scene)
    for f_ in fl:
        for d_ in pd:
            if f_.actors["user"] != d_.actors["cutter"]:
                continue
            if abs(d_.t0 - f_.t0) * DT <= p["within_s"]:
                t0 = min(f_.t0, d_.t0)
                ts = Tests()
                ts.flag("flare", True, f_.conf)
                ts.flag("pin_down", True, d_.conf)
                ev = _emit("wiper", {"cutter": f_.actors["user"]}, t0, min(f_.start, d_.start), max(f_.end, d_.end), ts,
                           [scene.k(f_.actors["user"])], min_conf=p["min_conf"],
                           attrs=dict(order="flare_then_pin" if f_.t0 <= d_.t0 else "pin_then_flare"))
                if ev:
                    out.append(ev)
    return out


# --------------------------------------------------------------------------------------
# Items that need data beyond XY (needs_data in the YAML): they return no events
# --------------------------------------------------------------------------------------
def detect_cut_lob_finish(scene, **params):
    """Lob finish needs ball and hand height (z); broadcast XY cannot detect it."""
    _p("cut_lob_finish", params)
    return []


# ======================================================================================
# Registry, precedence (CU.R3) and detect_all
# ======================================================================================
DETECTORS = {
    "move": detect_move, "cut": detect_cut, "cut_basket": detect_cut_basket, "cut_dive": detect_cut_dive,
    "cut_45": detect_cut_45, "cut_front": detect_cut_front, "cut_backdoor": detect_cut_backdoor,
    "cut_flash": detect_cut_flash, "cut_v": detect_cut_v, "cut_l": detect_cut_l, "cut_i": detect_cut_i,
    "cut_banana": detect_cut_banana, "cut_shallow": detect_cut_shallow, "cut_weak_baseline": detect_cut_weak_baseline,
    "cut_thru": detect_cut_thru, "cut_curl": detect_cut_curl, "cut_flare": detect_cut_flare, "cut_fade": detect_cut_fade,
    "cut_straight": detect_cut_straight, "cut_pop_out": detect_cut_pop_out, "cut_ucla": detect_cut_ucla,
    "cut_iverson": detect_cut_iverson, "cut_flex": detect_cut_flex, "cut_zipper": detect_cut_zipper,
    "cut_pin_down": detect_cut_pin_down, "cut_turnout": detect_cut_turnout, "cut_cross_screen": detect_cut_cross_screen,
    "cut_baseline_exit": detect_cut_baseline_exit, "cut_chin": detect_cut_chin, "cut_loop": detect_cut_loop,
    "cut_shuffle": detect_cut_shuffle, "cut_blade": detect_cut_blade, "cut_rub": detect_cut_rub,
    "cut_circle": detect_cut_circle, "cut_laker": detect_cut_laker, "cut_veer": detect_cut_veer,
    "cut_hammer": detect_cut_hammer, "relocate": detect_relocate, "lift": detect_lift, "drift": detect_drift,
    "shake": detect_shake, "dunker_slide": detect_dunker_slide, "fill": detect_fill,
    "sprint_to_corner": detect_sprint_to_corner, "rim_run": detect_rim_run, "give_and_go": detect_give_and_go,
    "blind_pig": detect_blind_pig, "wiper": detect_wiper,
    "cut_lob_finish": detect_cut_lob_finish,
}

PRECEDENCE = PARAMS["cu_precedence"]["order"]


# --------------------------------------------------------------------------------------
# Loop 5: shared post-emission rules applied to every registered detector (CU.R6 in the YAML, cu_postrules)
# --------------------------------------------------------------------------------------
_POST = PARAMS["cu_postrules"]


def _halfcourt_ok(c, e):
    """Half-court gate (fix L5-01, loop 5; carry rule fix L6-01, loop 6). A half-court label needs its primary actor
    in the frontcourt (y <= frontcourt_y_max_m) on every frame of [start, end] (where the action happens). The
    transition carry (frames of [start - transition_carry_s, start) beyond half court) rejects the label only when
    the crossing was part of a transition (_transition_carry: a sustained run into the label, a defense that is not
    set, or the ball still in the backcourt). L5-01 rejected every carry, which removed half-court pass-and-cuts by
    a handler who walked the ball over half court less than 2 s earlier (loop-5 confirmer, synthetic 10 -> 0)."""
    o = _primary_actor(e)
    if o is None or o not in c.f:
        return True
    hc = PARAMS["cut"]["frontcourt_y_max_m"]
    fe = c.f[o]
    a, b = int(e.start), int(e.end)
    y = np.nan_to_num(fe.y, nan=-99.0)
    if (y[a:b + 1] > hc).any():
        return False
    lo = max(0, a - F(PARAMS["cut"]["transition_carry_s"]))
    bc = np.flatnonzero(y[lo:a] > hc)
    if not len(bc):
        return True
    return not _transition_carry(c, o, lo + int(bc[-1]), lo, a, b)


def _transition_carry(c, o, tx, lo, a, b):
    """fix L6-01 (loop 6; rule (1) replaced by L7-02, loop 7, L8-01/02, loop 8, and redesigned by structure in loop 9,
    L9-01..L9-04): True when o's half-court crossing at frame tx (his last backcourt frame) belongs to a transition, i.e.
    the offense is not yet in a half-court phase when the label starts at a:
    (1) a run carried into the label: every carry_sustain_chord_s chord from the crossing to the label start is at
        running pace, >= carry_run_mps - carry_sustain_k x sigma, and their median >= carry_run_mps (carry_run_mps
        2.0 m/s is the human walk-run gait transition, Froude number 0.5, below the 2.5-3.5 m/s band of real jog-ups).
        After such a run the phase is read from the structure of the action, not from a burst-ratio threshold:
        - on-ball: o still holds the ball after the label start (L8-02), or his next ball touch after his holder run
          is his own (L9-04: a dribble whose holder flag dropped out, not a release): the run is the transition;
        - the post-release segment (L9-02, C8-2): "keeps running" is judged on the label's first carry_post_s (up to
          the settle), not on the whole label, whose median a settle at the end drags below the gait speed;
        - off-ball runner (no holder run of o in [tx - carry_hold_back_s, a)): the run is the transition while he keeps
          running pace (median post-release chord >= carry_run_mps); one who slows to a walk after the crossing starts
          a half-court action (L9-03, C8-3), so a jog-up into a walk-pace relocation is half-court for him as for a
          handler;
        - handler who released the ball by the label start: a push released on the run (L9-01: every carry_push_chord_s
          chord ending in the last carry_push_span_s before the release at >= carry_push_mps, the TRN-P08 push speed)
          that keeps running is the transition, whatever he does next (the push that hits ahead and sprints or
          accelerates to the rim, synthetic N1); after a jog-up the pass is the phase change: he keeps running only when
          the post-release median clears carry_run_mps by carry_post_k sigma of that median (one-sided: a relocation at
          1.7-1.9 m/s must not read as a run on noise), and only a steady continuation (whole-label median chord <
          carry_burst_ratio x the carry median, the secondary cue, no margin) stays a transition; a slow-down or a burst
          after the pass is a half-court action;
    (2) the defense is not set: >= carry_def_unset_n defenders beyond half court on a frame of [lo, a] (needs
        carry_def_min_tracked tracked defenders, so a broadcast frame with missing defenders falls back to (1, 3));
    (3) the ball is still beyond half court during the label (the actor is ahead of the ball).
    A walk-up, a settle or a stop between the crossing and the label starts the half-court phase. XY only (no ball
    height). L6-01 used one absolute sustain speed (carry_sustain_mps 3.0) inside the dense band of real jog-up speeds;
    L8-03 separated the push from the pass-and-burst by a 1-sigma burst margin (effective ratio 1.5-1.8 at noise),
    replaced by the push structure in L9-01."""
    fe = c.f[o]
    hc = PARAMS["cut"]["frontcourt_y_max_m"]
    w = max(1, F(_POST["carry_sustain_chord_s"]))

    def chords(t0, t1):
        vs = [math.hypot(fe.x[t + w] - fe.x[t], fe.y[t + w] - fe.y[t]) / (w * DT) for t in range(max(0, t0), t1 + 1) if t + w < c.n]
        return [v for v in vs if np.isfinite(v)]
    t_lo, t_hi = max(0, tx - w), max(max(0, tx - w), a - w)
    vs = chords(t_lo, t_hi)
    sig = math.sqrt(2) * float(np.nan_to_num(np.nanmax(fe.sig_p[t_lo:a + 1]), nan=0.0)) / (w * DT)
    run, k = _POST["carry_run_mps"], _POST["carry_sustain_k"]
    # fix L8-01b (loop 8, C7-1): the run must also be at running pace on its median chord (no sigma allowance)
    if vs and min(vs) >= run - k * sig and float(np.median(vs)) >= run:
        hruns = [r_ for r_ in c.holder_runs() if r_[0] == o and r_[2] >= max(0, tx - F(_POST["carry_hold_back_s"])) and r_[1] <= b]
        pre = [r_ for r_ in hruns if r_[1] < a]
        # fix L8-02 (loop 8, C7-2): a holder run of o that goes on past the label start is on-ball (a dribble drive), not
        # a cut; releasing on the start frame is a release, a catch inside the label is allowed
        if any(r_[1] < a < r_[2] for r_ in hruns):
            return True
        t_rel = max(r_[2] for r_ in pre) if pre else None
        # fix L9-04 (loop 9): his next ball touch after his holder run is his own, inside the label: the holder flag
        # dropped out during a dribble (real n0.5: the raw ball and the smoothed handler drift > 1.0 m apart for 0.5-1 s),
        # so the ball was never released (no pass, no shot, no other player touched it)
        if t_rel is not None:
            nxt = next((r_ for r_ in c.holder_runs() if r_[1] > t_rel), None)
            if nxt is not None and nxt[0] == o and nxt[1] <= b:
                return True
        # fix L9-02 (loop 9, C8-2): keeps running is judged on the post-release segment, the label's first carry_post_s
        vp = chords(a, max(a, min(b, a + F(_POST["carry_post_s"])) - w))
        mp = float(np.median(vp)) if vp else 0.0
        if t_rel is None:
            # fix L9-03 (loop 9, C8-3): an off-ball runner who keeps running pace is the transition run (a lane run, a
            # fill); one who slows to a walk after the crossing starts a half-court action (rules (2) / (3) still apply)
            if mp >= run:
                return True
        else:
            # fix L9-01 (loop 9, C8-1): a push released on the run that keeps running is the transition (structure, not
            # a burst ratio: the hit-ahead push that sprints or accelerates to the rim, synthetic N1)
            if mp >= run and _carry_push(c, fe, t_rel):
                return True
            # after a jog-up the pass is the phase change: a steady continuation at running pace (no burst) is the
            # transition run; a slow-down after the pass (L8-01; L9-02: one-sided carry_post_k margin on the median)
            # or a burst (whole-label median >= carry_burst_ratio x the carry median, the secondary cue; L9-01: the
            # L8-03 sigma margin is dropped) is a half-court action
            s_p = 1.2533 * sig / math.sqrt(max(1.0, (len(vp) + w - 1) / w))
            if vp and mp - run >= _POST["carry_post_k"] * s_p:
                vl = chords(a, max(a, b - w))
                if not vl or float(np.median(vl)) < _POST["carry_burst_ratio"] * float(np.median(vs)):
                    return True
    dfs = [d for d in c.s.defense if d in c.f]
    if len(dfs) >= _POST["carry_def_min_tracked"]:
        n_bc = np.zeros(a - lo + 1, dtype=int)
        for d in dfs:
            n_bc += (np.nan_to_num(c.f[d].y[lo:a + 1], nan=-99.0) > hc).astype(int)
        if n_bc.max() >= _POST["carry_def_unset_n"]:
            return True
    return bool((np.nan_to_num(c.by[a:b + 1], nan=-99.0) > hc).any())


def _carry_push(c, fe, t_rel):
    """fix L9-01 (loop 9): the handler released the ball out of a push, every carry_push_chord_s (1.0 s) chord ending in
    the last carry_push_span_s (0.5 s) before the release is at >= carry_push_mps (4.0 m/s): the TRN-P08 push, vbar(1.0)
    >= 4.0 m/s for 1.5 s while holding the ball (transition family). A jog-up that slows into the pass is no push."""
    w1 = max(1, F(_POST["carry_push_chord_s"]))
    t0 = t_rel - F(_POST["carry_push_span_s"])
    if t0 - w1 < 0:
        return False
    v1 = [math.hypot(fe.x[t] - fe.x[t - w1], fe.y[t] - fe.y[t - w1]) / (w1 * DT) for t in range(t0, t_rel + 1)]
    v1 = [v for v in v1 if np.isfinite(v)]
    return bool(v1) and min(v1) >= _POST["carry_push_mps"]


def _no_glitch(c, e):
    """fix L5-04b (loop 5, C4-D): drop a label whose primary actor's smoothed speed exceeds glitch_max_mps inside
    the event (a tracking teleport; the fastest NBA sprints are about 9 m/s)."""
    o = _primary_actor(e)
    if o is None or o not in c.f:
        return True
    sp = c.f[o].speed[int(e.start):int(e.end) + 1]
    return not bool((np.nan_to_num(sp, nan=0.0) > _POST["glitch_max_mps"]).any())


def _dedup(events):
    """fix L5-04 (loop 5, C4-D): one event per (kind, actors) within dedup_t0_s of t0; the higher conf is kept
    (near-duplicates came from neighbouring contact intervals and turn peaks of the same move)."""
    w = F(_POST["dedup_t0_s"])
    keep = []
    for e in sorted(events, key=lambda e: -e.conf):
        key = (e.kind, tuple(sorted((k, str(v)) for k, v in e.actors.items())))
        if any(k2 == key and abs(e.t0 - t2) <= w for k2, t2, _ in keep):
            continue
        keep.append((key, e.t0, e))
    kept = {id(e) for _, _, e in keep}
    return [e for e in events if id(e) in kept]


def _postrules(kind, fn):
    exempt = kind in _POST["exempt_kinds"]

    def wrapped(scene, **params):
        evs = fn(scene, **params)
        if not evs:
            return evs
        c = _ctx(scene)
        evs = [e for e in evs if _no_glitch(c, e) and (exempt or _halfcourt_ok(c, e))]
        return _dedup(evs)
    wrapped.__name__, wrapped.__doc__, wrapped.raw = fn.__name__, fn.__doc__, fn
    return wrapped


DETECTORS = {k: _postrules(k, fn) for k, fn in DETECTORS.items()}
for _k, _fn in DETECTORS.items():  # module-level names call the same rules (components such as wiper inherit them)
    globals()[_fn.__name__] = _fn


def _primary_actor(ev):
    for k in ("cutter", "user", "runner", "player", "filler"):
        if ev.actors.get(k) is not None:
            return ev.actors[k]
    return None


def resolve(events):
    """CU.R3: mark one primary label per (actor, overlapping interval); others become secondary (kept)."""
    rank = {k: i for i, k in enumerate(PRECEDENCE)}

    def rk(e):  # "kind:variant" entries (e.g. sprint_to_corner:half_court) override the kind's rank
        return rank.get(f"{e.kind}:{e.attrs.get('variant')}", rank.get(e.kind))

    evs = sorted(events, key=lambda e: (rk(e) if rk(e) is not None else len(rank), -e.conf))
    taken = []
    for e in evs:
        if e.kind in ("move", "cut") or rk(e) is None:
            continue
        who = _primary_actor(e)
        clash = next((t for t in taken if _primary_actor(t) == who and not (e.end < t.start or t.end < e.start)), None)
        if clash is None:
            e.attrs["primary"] = True
            taken.append(e)
        else:
            e.attrs["primary"] = False
            e.attrs["secondary_of"] = clash.kind
    return events


def detect_all(scene, resolve_labels=True):
    """Run every detector on the scene; optionally apply the CU.R3 precedence (labels are kept, ranked)."""
    out = []
    for fn in DETECTORS.values():
        out.extend(fn(scene))
    return resolve(out) if resolve_labels else out


# Single-source check: every detector id is an item in the YAML with detector: true
_missing = [k for k in DETECTORS if k not in ITEMS]
assert not _missing, f"detectors without a YAML item: {_missing}"
