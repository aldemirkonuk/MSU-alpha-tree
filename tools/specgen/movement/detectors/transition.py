"""Transition, restarts and special-situation detectors (TRN family; spec tooling, not the production labeller).

Implements config/movement_grammar/transition.yaml. Every numeric parameter is read from that file at import
(single source of truth); each detector accepts keyword overrides for tuning. Detectors read an mvlib.Scene and
return mvlib.Event objects whose conf follows MP-16: window_conf of the binding per-frame probability times the
geometric mean, over the involved objects, of edge_factor x gap_factor.

Frame convention (see the YAML header): a scene that contains a possession change is built in the attacked-rim
frame of the team that GAINS the ball (scene.offense). The losing team (scene.defense) attacked the far rim at
(0, FAR_RIM_Y) and defends the origin, so every transition run, offense upcourt or defense retreat, is toward the
origin. Restart scenes (BLOB, SLOB, press, FT) use the frame of the team in control.

Ball control is inferred from ball XY only (has_ball proxy, TRN-R01); shots, passes, possession changes and
throw-ins are all derived from the sequence of sustained holds. Items that need ball height, the game / shot clock
or PBP return [] and are marked needs_data in the YAML.
"""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import yaml

_HERE = Path(__file__).resolve()
ROOT = _HERE.parents[4]
for _p in (_HERE.parents[1], ROOT / "tools" / "specgen" / "named_spots"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mvlib as mv  # noqa: E402
import spotlib  # noqa: E402
from mvlib import DT, K_CAL, Event, edge_factor, frames, gap_factor, p_above, p_below, phi, window_conf  # noqa: E402

GRAMMAR = ROOT / "config" / "movement_grammar" / "transition.yaml"
CFG = yaml.safe_load(GRAMMAR.read_text())
PARAMS = {it["id"]: {k: v["value"] for k, v in (it.get("params") or {}).items()} for it in CFG["items"]}
STATUS = {it["id"]: it["status"] for it in CFG["items"]}
MIN_DUR = {it["id"]: it.get("min_duration_s") for it in CFG["items"]}

C = spotlib.C
_, SPOTS = spotlib.load()
FAM = PARAMS["family_kinematics"]
HALF_Y = FAM["half_y"]
SZ_Y = FAM["scoring_zone_y"]
THREE_R = FAM["three_r"]
FAR_RIM_Y = FAM["far_rim_y"]
SIDE_X, END_Y, FAR_END_Y, LANE_X, FT_Y = C["SIDE_X"], C["END_Y"], C["FAR_END_Y"], C["LANE_X"], C["FT_Y"]
CHI2 = FAM["stationary_chi2"]


VS, VL = FAM["vbar_short_s"], FAM["vbar_long_s"]  # window-speed lengths (fix TRN-T14: no literal 0.5 / 1.0)


def _prm(item_id: str, over: dict | None = None) -> dict:
    """YAML parameters of one item with keyword overrides applied (unknown keys are an error)."""
    p = dict(PARAMS[item_id])
    over = over or {}
    bad = set(over) - set(p)
    if bad:
        raise TypeError(f"{item_id}: unknown parameters {sorted(bad)}")
    p.update(over)
    return p


def _pkey(name, p, item="possession_change"):
    """Memo key: the bare name for the YAML defaults, the name plus the merged parameters when overridden (fix
    TRN-T11: overrides reach the shared anchors instead of being silently replaced by the cached defaults)."""
    if p is None or p == PARAMS[item]:
        return name
    return (name, item, tuple(sorted(p.items())))


def _pc(pc=None) -> dict:
    return PARAMS["possession_change"] if pc is None else pc


def _stay_r(pc=None) -> float:
    """Radius a sustained hold is kept within (hold_r_m + hold_stay_hyst_m); hold confidences test against it."""
    pc = _pc(pc)
    return pc["hold_r_m"] + pc["hold_stay_hyst_m"]


# --------------------------------------------------------------------------------------
# Shared geometry and kinematics helpers
# --------------------------------------------------------------------------------------
def _cache(scene) -> dict:
    """Per-scene memo for anchors computed with the YAML defaults (detectors with overrides bypass it)."""
    return scene.__dict__.setdefault("_trn_cache", {})


def _memo(scene, key, fn):
    c = _cache(scene)
    if key not in c:
        c[key] = fn()
    return c[key]


def _kin(scene, oid):
    return scene.ball if oid == "ball" else scene.kins[oid]


def _team(scene, oid):
    return "O" if oid in scene.offense else ("D" if oid in scene.defense else None)


def _sig_p(k) -> np.ndarray:
    """Calibrated position sigma per frame (m)."""
    return K_CAL * np.sqrt(np.where(np.isnan(k.var_p), 0.09, k.var_p))


def _in_spot(sid: str, x: float, y: float) -> bool:
    if not (np.isfinite(x) and np.isfinite(y)):
        return False
    return bool(SPOTS[sid].labels(float(x), float(y)))


def _d_in(x, y):
    """Signed distance inside the court boundary (negative = out of bounds)."""
    return np.minimum(np.minimum(SIDE_X - np.abs(x), y - END_Y), FAR_END_Y - y)


def _r_far(k):
    return np.hypot(k.x, k.y - FAR_RIM_Y)


def _wvel(scene, oid, w_s):
    """Window velocity on the smoothed track: (vx, vy, sigma) with vbar = |p(t+W/2) - p(t-W/2)| / W."""

    def calc():
        k = _kin(scene, oid)
        n = len(k.x)
        h = max(1, frames(w_s / 2))
        vx, vy, sg = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
        if n > 2 * h:
            span = 2 * h * DT
            vx[h : n - h] = (k.x[2 * h :] - k.x[: n - 2 * h]) / span
            vy[h : n - h] = (k.y[2 * h :] - k.y[: n - 2 * h]) / span
            sg[h : n - h] = (
                K_CAL
                * np.sqrt(np.nan_to_num(k.var_p[2 * h :], nan=0.09) + np.nan_to_num(k.var_p[: n - 2 * h], nan=0.09))
                / span
            )
        return vx, vy, sg

    return _memo(scene, ("wvel", oid, w_s), calc)


def _vbar(scene, oid, w_s):
    vx, vy, sg = _wvel(scene, oid, w_s)
    return np.hypot(vx, vy), sg


def _v_back(scene, oid, w_s=VS):
    """Window radial velocity toward the origin rim (positive = toward), with sigma."""

    def calc():
        k = _kin(scene, oid)
        n = len(k.x)
        h = max(1, frames(w_s / 2))
        r = np.hypot(k.x, k.y)
        v = np.full(n, np.nan)
        if n > 2 * h:
            v[h : n - h] = (r[: n - 2 * h] - r[2 * h :]) / (2 * h * DT)
        return v, _wvel(scene, oid, w_s)[2]

    return _memo(scene, ("vback", oid, w_s), calc)


def _swap_edge(scene, oid):
    """Identity-swap gate (TRN-R00, fix TRN-T14): frames whose implied speed over swap_window_s of SMOOTHED
    displacement exceeds swap_speed_mps split the track like a segment boundary. Returns per frame the number of
    frames to the nearest swap frame (large when there is none); _qobj uses min(segment edge, swap edge), so an
    anchor next to a suspected re-ID gets edge_factor 0 exactly as at a camera cut (MP-06). Never applied to the
    ball."""

    def calc():
        k = scene.k(oid)
        n = len(k.x)
        h = max(1, frames(FAM["swap_window_s"] / 2))
        m = np.zeros(n, dtype=bool)
        if n > 2 * h:
            v = np.hypot(k.x[2 * h :] - k.x[: n - 2 * h], k.y[2 * h :] - k.y[: n - 2 * h]) / (2 * h * DT)
            m[h : n - h] = np.nan_to_num(v, nan=0.0) > FAM["swap_speed_mps"]
        idx = np.flatnonzero(m)
        if not len(idx):
            return np.full(n, 10**6)
        t = np.arange(n)
        return np.min(np.abs(t[:, None] - idx[None, :]), axis=1)

    return _memo(scene, ("swap_edge", oid), calc)


def _qobj(scene, oids, t, a, b) -> float:
    """Geometric mean over objects of edge_factor(k, t) x gap_factor(k, a, b) (MP-16, fix TRN-R04); a suspected
    identity swap counts as a segment edge (fix TRN-T14)."""
    vals = []
    for o in oids:
        k = _kin(scene, o)
        if k is None:
            return 0.0
        t_ = int(np.clip(t, 0, len(k.x) - 1))
        ef = edge_factor(k, t_)
        if o != "ball":
            se = int(_swap_edge(scene, o)[t_])
            if se < 5:
                ef = 0.0
            elif se < mv.EDGE_FRAMES:
                ef = min(ef, 1.0 / mv.K_EDGE.get(se, 1.0))
        vals.append(ef * gap_factor(k, max(0, a), min(len(k.x) - 1, b)))
    vals = np.asarray(vals, dtype=float)
    if len(vals) == 0 or np.any(vals <= 0):
        return 0.0
    return float(np.exp(np.mean(np.log(vals))))


def _ev(kind, actors, t0, a, b, conf, **attrs) -> Event:
    return Event(kind, actors, int(t0), int(a), int(b), float(np.clip(conf, 0.0, 1.0)), attrs)


def _runs_of(mask: np.ndarray, min_frames: int = 1, max_gap: int = 0):
    """Inclusive [a, b] runs where mask is true, bridging false gaps of <= max_gap frames."""
    out, a, last, gap = [], None, None, 0
    for t, v in enumerate(mask):
        if v:
            if a is None:
                a = t
            last, gap = t, 0
        elif a is not None:
            gap += 1
            if gap > max_gap:
                out.append((a, last))
                a, gap = None, 0
    if a is not None:
        out.append((a, last))
    return [(a, b) for a, b in out if b - a + 1 >= min_frames]


def _dwell(seconds: float) -> int:
    """Number of frames spanning an elapsed time (n frames span n - 1 intervals)."""
    return frames(seconds) + 1


def _pb_count(p: np.ndarray, k_min: float) -> float:
    """P(count >= k_min) for independent Bernoulli p (normal approximation of the Poisson-binomial)."""
    p = np.asarray(p, dtype=float)
    e, v = p.sum(), (p * (1 - p)).sum()
    return float(phi((e - (k_min - 0.5)) / math.sqrt(v + 0.02)))


def _assign(cost: np.ndarray):
    """Minimum-cost one-to-one assignment for small square matrices (brute force, n <= 6)."""
    n = cost.shape[0]
    best, perm = np.inf, None
    for pr in itertools.permutations(range(cost.shape[1]), n):
        c = sum(cost[i, pr[i]] for i in range(n))
        if c < best:
            best, perm = c, pr
    return perm, best


def _seg_dist(px, py, ax, ay, bx, by):
    """Distance from point p to segment a-b (vectorised over p)."""
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    u = np.clip(((px - ax) * dx + (py - ay) * dy) / np.where(L > 0, L, 1.0), 0.0, 1.0)
    return np.hypot(px - (ax + u * dx), py - (ay + u * dy))


# --------------------------------------------------------------------------------------
# Ball control: holders, hold runs, shots, passes, possession changes, throw-ins (TRN-R01, TRN-R05)
# --------------------------------------------------------------------------------------
def _hold_state(scene, pc=None):
    """has_ball proxy with holder hysteresis (TRN-R01, fixes TRN-T02 / TRN-T12).

    Returns (holder, relv): per frame the id of the player of EITHER team in control of the ball (or None) and the
    smoothed relative speed |v_ball - v_holder| at that frame. Control starts when the ball is within hold_enter_r_m,
    or within hold_r_m once it moves with the player and no longer closes on him (relative speed <= hold_core_v_mps,
    closing speed <= hold_settle_v_mps; loop 2 dropped the bare moving-ball branch, TRN-T12); so a player walking up
    to a RESTING ball holds it only from hold_enter_r_m, and
    stays while it is within hold_r_m + hold_stay_hyst_m with relative speed <= hold_rel_v_mps. Another player (within
    hold_r_m) takes over only after hold_min_frames consecutive frames on which he is >= hold_switch_m nearer, or
    nearer while the ball moves with him (relative speed <= hold_core_v_mps) and not with the current holder; so a
    screener at contact distance, a trapper or a stationary on-ball defender no longer steals the hold on noise,
    while a catcher still takes the ball from a player it brushed past. A switch is backdated to the start of the
    unbroken run on which the new holder was nearer with the ball moving with him (loop 2, TRN-T02). A fresh hold
    (no holder before) is backdated to the ball's arrival at the catcher (catch_onset, loop 3). Control ends at the
    last frame the ball is still with the player (within hold_enter_r_m, or within hold_r_m moving with him). Runs
    shorter than hold_min_frames are dropped (debounce).
    """
    pc = _pc(pc)

    def calc():
        n = scene.n
        out = np.array([None] * n, dtype=object)
        relv = np.full(n, np.nan)
        b = scene.ball
        if b is None:
            return out, relv
        ids = scene.players()
        obs = b.state == "observed"
        bx = np.where(obs, b.x, np.nan)
        by = np.where(obs, b.y, np.nan)
        D = np.array([np.hypot(scene.k(o).x - bx, scene.k(o).y - by) for o in ids])
        # a ball flying past a player is not in his control: the relative speed must be small too
        V = np.array([np.hypot(scene.k(o).vx - b.vx, scene.k(o).vy - b.vy) for o in ids])
        D = np.where(np.isnan(D), np.inf, D)
        # loop 4 (TRN-L4-rimfree, real SportVU): a ball inside the footprint (rim_contact_r_m in XY) of the rim a
        # player's team ATTACKS is at rim height (a layup or dunk at the rim, on the rim, dropping through the net),
        # so that player does not hold it there: the shooter's control ends where the ball enters the footprint, which
        # leaves the unheld shot gap the shot proxy needs (on the real tracks the shooter's XY "hold" ran on to the
        # rim and the defender under it took over at once, so 1 in 3 far-rim field-goal attempts had no gap). A
        # defender catching a rebound at his own rim is not affected (synthetic rim-catch rebounds).
        if pc["hold_rim_free"]:
            for i_, o_ in enumerate(ids):
                ry_ = _attacked_rim_y(_team(scene, o_))
                if _team(scene, o_) in ("O", "D"):
                    D[i_, np.hypot(bx, by - ry_) <= pc["rim_contact_r_m"]] = np.inf
        V = np.where(np.isnan(V), np.inf, V)
        ok_v = V <= pc["hold_rel_v_mps"]
        stay = (D <= pc["hold_r_m"] + pc["hold_stay_hyst_m"]) & ok_v
        # closing speed of the ball on the player (positive = the distance shrinks)
        CL = np.array(
            [
                -((bx - scene.k(o).x) * (b.vx - scene.k(o).vx) + (by - scene.k(o).y) * (b.vy - scene.k(o).vy))
                / np.where(np.isfinite(D[i]) & (D[i] > 0), D[i], np.nan)
                for i, o in enumerate(ids)
            ]
        )
        settle = (V <= pc["hold_core_v_mps"]) & (np.nan_to_num(CL, nan=9.0) <= pc["hold_settle_v_mps"])
        # fix TRN-T12 (loop 2): no onset inside hold_r_m merely because the ball moves (a ball dropping from the rim
        # or a pass still closing on the player); inside hold_r_m only a settled ball starts control
        enter = ((D <= pc["hold_enter_r_m"]) | ((D <= pc["hold_r_m"]) & settle)) & ok_v
        core = V <= pc["hold_core_v_mps"]
        # 'with the player' for the release: within the onset radius, or within hold_r_m while moving with him
        held = ((D <= pc["hold_enter_r_m"]) | ((D <= pc["hold_r_m"]) & core)) & ok_v
        minf = int(pc["hold_min_frames"])
        sig_d = {}

        def sd_(j):
            """MP-19 player-ball distance sigma per frame (noise tier of this pair)."""
            if j not in sig_d:
                sig_d[j] = np.nan_to_num(mv.sigma_dist(scene.k(ids[j]), b), nan=0.3)
            return sig_d[j]

        def catch_onset(j, t):
            """Fix TRN-T12 side effect (loop 3): onset of a fresh hold of player j that starts at t, backdated to the
            ball's ARRIVAL. The smoothed ball overshoots and rings after a pass is caught on the run (D 0.8-1.2 m
            and relative speed > hold_core_v_mps for 0.3-0.5 s), so the settle branch fires late. Walk back from t
            over at most catch_backdate_s + catch_backdate_k_s_per_m x sigma_dist (the smoother lag grows with the
            noise tier) while j is the nearest player, no one else holds and D <= hold_r_m + hold_stay_hyst_m +
            catch_chain_sigma_k x sigma_dist; the onset is the first frame of that chain where the ball stops
            closing on j (local minimum of D) within hold_r_m and away from both rims (shot_rim_r_m: a ball at the
            rim is at rim height, XY proximity there is no catch)."""
            sd = sd_(j)
            lo = max(0, t - frames(pc["catch_backdate_s"] + pc["catch_backdate_k_s_per_m"] * float(sd[t])))
            stay_r = pc["hold_r_m"] + pc["hold_stay_hyst_m"]
            m = t - 1
            while (
                m >= lo
                and raw[m] in (-1, j)
                and D[j, m] <= stay_r + pc["catch_chain_sigma_k"] * sd[m]
                and int(np.argmin(D[:, m])) == j
                # loop 4 (confirm-3 NEW-T12-catch-rimguard-bypass): the chain stops at the first rim-zone frame, so
                # it can no longer run back into a shot still in flight (dreb became steal)
                and min(math.hypot(bx[m], by[m]), math.hypot(bx[m], by[m] - FAR_RIM_Y)) > pc["shot_rim_r_m"]
            ):
                m -= 1
            for s_ in range(m + 1, t):
                if (
                    D[j, s_] <= pc["hold_r_m"]
                    and D[j, s_] <= D[j, s_ + 1]
                    and min(math.hypot(bx[s_], by[s_]), math.hypot(bx[s_], by[s_] - FAR_RIM_Y)) > pc["shot_rim_r_m"]
                    # loop 4 (confirm-3 NEW-T12-catch-loose-ball-early): not a fly-by minimum the ball then recedes
                    # from (D rises by more than hold_stay_hyst_m + catch_recede_sigma_k x sigma_dist before t: the
                    # player chased a loose ball; the sigma term keeps smoother jitter at sigma_p 0.5 from tripping it)
                    and np.max(D[j, s_ : t + 1]) - D[j, s_] <= pc["hold_stay_hyst_m"] + pc["catch_recede_sigma_k"] * sd[s_]
                ):
                    return s_
            return t

        raw = np.full(n, -1)
        cur, cand, cnt = None, None, 0
        for t in range(n):
            if cur is not None and stay[cur, t]:
                dt_ = D[:, t].copy()
                dt_[cur] = np.inf
                j = int(np.argmin(dt_))
                nearer = dt_[j] <= D[cur, t] - pc["hold_switch_m"] or (
                    dt_[j] < D[cur, t] and core[j, t] and not core[cur, t]
                )
                if dt_[j] <= pc["hold_r_m"] and ok_v[j, t] and nearer:
                    cnt = cnt + 1 if cand == j else 1
                    cand = j
                else:
                    cand, cnt = None, 0
                if cnt >= minf:
                    # fix TRN-T02 (loop 2): the new holder's control starts where his unbroken run of being nearer
                    # than the current holder (with the ball moving with him, within hold_r_m) began, not where
                    # the switch margin was finally reached (a steal received at 0.6-0.8 m contact distance).
                    # Loop 3: deliberately NOT capped (a 0.1 / 0.3 s cap or a stop at the holder's core frames each
                    # measured net worse on both seed sets, see changes_loop3 TRN-T02-cap)
                    s0 = t - minf + 1
                    while (
                        s0 - 1 >= 0
                        and raw[s0 - 1] == cur
                        and D[cand, s0 - 1] < D[cur, s0 - 1]
                        and core[cand, s0 - 1]
                        and ok_v[cand, s0 - 1]
                        and D[cand, s0 - 1] <= pc["hold_r_m"]
                    ):
                        s0 -= 1
                    cur = cand
                    raw[s0 : t + 1] = cur
                    cand, cnt = None, 0
                raw[t] = cur
                continue
            cur, cand, cnt = None, None, 0
            de = np.where(enter[:, t], D[:, t], np.inf)
            j = int(np.argmin(de))
            if np.isfinite(de[j]):
                cur = j
                raw[catch_onset(j, t) : t + 1] = j
        t = 0
        while t < n:
            if raw[t] < 0:
                t += 1
                continue
            u = t
            while u + 1 < n and raw[u + 1] == raw[t]:
                u += 1
            j = raw[t]
            # the stay hysteresis only keeps the holder's identity through noise: control ends at the last frame
            # the ball is still with him (onset radius, or hold_r_m while moving with him), so the release (t_rel,
            # t_ft) is not delayed by the wider stay radius or by a pass that is already flying
            ok = np.flatnonzero(held[j, t : u + 1])
            u2 = t + int(ok[-1]) if len(ok) else t - 1
            if u2 - t + 1 >= minf:  # debounce: keep only runs of >= hold_min_frames
                out[t : u2 + 1] = ids[j]
                relv[t : u2 + 1] = V[j, t : u2 + 1]
            t = u + 1
        return out, relv

    return _memo(scene, _pkey("holders", pc), calc)


def _holders(scene, pc=None):
    """Per frame the id of the player of EITHER team in control of the ball, or None (has_ball proxy)."""
    return _hold_state(scene, pc)[0]


def _attacked_rim_y(team):
    """The rim a team attacks in the scene frame: offense the origin, defense (the losing team) the far rim."""
    return 0.0 if team == "O" else FAR_RIM_Y


def _shot_gap(scene, team, e, hi, pc=None):
    """Shot proxy test on the unheld gap [e + 1, hi] after a hold of `team` ending at e (fix TRN-T04): the observed
    ball comes within shot_rim_r_m of the rim that team ATTACKS and, right after the release, closes on it (min
    distance over the next shot_closing_frames frames < distance at release). Returns (rim, t_rim) or None."""
    pc = _pc(pc)
    b = scene.ball
    if b is None or hi < e + 1:
        return None
    ry = _attacked_rim_y(team)
    seg = np.arange(e + 1, hi + 1)
    seg = seg[b.state[seg] == "observed"]
    if len(seg) == 0:
        return None
    d = np.hypot(b.x[seg], b.y[seg] - ry)
    if not np.nanmin(d) <= pc["shot_rim_r_m"]:
        return None
    bx, by, _ = _ball_filled(scene, pc)
    df = np.hypot(bx, by - ry)
    k = int(pc["shot_closing_frames"])
    k3 = min(hi, e + k)
    if not np.nanmin(df[e + 1 : k3 + 1]) < df[e]:
        # fix TRN-T04 (loop 2): a release AT the rim (layup, dunk, put-back) carried in toward it is a shot even
        # though the ball then moves away from the rim
        a0 = max(0, e - k)
        if df[e] <= pc["shot_at_rim_r_m"] and df[a0] > df[e]:
            t_rim = int(np.argmin(df[a0 : k3 + 1])) + a0
            return ("near" if team == "O" else "far"), max(t_rim, e + 1)
        return None  # a ball that leaves the rim area (rebound secured at the rim, kick-out) is not a shot
    close = seg[d <= pc["rim_contact_r_m"]]
    t_rim = int(close[0]) if len(close) else int(seg[np.nanargmin(d)])
    return ("near" if team == "O" else "far"), t_rim


def _hold_runs(scene, pc=None):
    """[(oid, a, b)] sustained holds after merging and dropping non-control touches (TRN-R01).

    Holds of the same player split by <= hold_merge_gap_s are merged. Touch length is measured on core-control frames
    (relative speed <= hold_core_v_mps, fix TRN-T02). Dropped (never a change of control):
      - pass-through: a short touch by the other team with fewer than hold_min_frames core frames while the ball keeps
        closing on the rim the previous holder's team attacks (a free throw flying over a player near the rim, fix
        TRN-T04; a teammate catching a pass ahead on the run is never a pass-through);
      - deflection: shorter than control_min_s, by the other team, between two holds of the same team;
      - scrum touch: shorter than control_min_s, starting after a shot proxy of the previous holder's team and
        followed by a hold of the other team (a crasher's touch before the rebounder secures it, fix TRN-T03);
      - brush: shorter than control_min_s and followed within hold_merge_gap_s by the hold of a teammate standing
        within hold_r_m + hold_stay_hyst_m of him (the ball reached the catcher past him; a real handoff is longer).
    The dropped touches are kept in _touches() (touched_by attribute).
    """
    pc = _pc(pc)

    def calc():
        h, relv = _hold_state(scene, pc)
        runs, t, n = [], 0, scene.n
        merge = frames(pc["hold_merge_gap_s"])
        while t < n:
            if h[t] is None:
                t += 1
                continue
            u = t
            while u + 1 < n and h[u + 1] == h[t]:
                u += 1
            if runs and runs[-1][0] == h[t] and t - runs[-1][2] - 1 <= merge:
                runs[-1][2] = u
            else:
                runs.append([h[t], t, u])
            t = u + 1
        cmin = frames(pc["control_min_s"])
        minf = int(pc["hold_min_frames"])
        bx, by, _ = _ball_filled(scene, pc)

        def core_n(r):
            return int(np.sum(relv[r[1] : r[2] + 1] <= pc["hold_core_v_mps"]))

        dropped = []
        # loop 4 (TRN-L4-rimtouch, real SportVU): a hold by a player whose ball never leaves the rim footprint
        # (rim_touch_r_m = rim_contact_r_m) of the rim HIS team defends, is still there rim_touch_after_s after the
        # hold ends (or when the next hold starts, if sooner) and that lasts <= rim_touch_max_s is not control. In XY
        # the ball at rim height (a layup or dunk rising off the shooter's hand, a ball on the rim, a make dropping
        # through the net) is "held" by the defender standing under the basket: those touches cut the shot gap, so
        # the make or the miss became a steal dated 1-4 s before the rebound or the inbound. A rebounder who
        # secures the ball over the rim carries it out or passes it out, so the ball leaves the footprint.
        # Loop 4 (TRN-L4-rimscrum, real SportVU): the same test with the wider rim_scrum_r_m when the NEXT hold is the
        # other team's: a contested layup or a rebound bouncing off the rim (ball at rim height, up to ~1.5 m out in
        # XY) passes over the defender under the basket and the shooting team taps or rebounds it (PBP: missed shot
        # + offensive rebound, no change). A rebounder who secures the ball gives it to a teammate (outlet) or keeps
        # it, so this never applies to him.
        rz = pc["rim_touch_r_m"]
        rzs = pc["rim_scrum_r_m"]
        rmax = frames(pc["rim_touch_max_s"])
        aft = frames(pc["rim_touch_after_s"])

        def rim_pass(runs):
            """One pass of the rim-touch / rim-scrum filter; returns (kept runs, whether a rim_scrum was dropped)."""
            keep, scrum = [], False
            for i, r in enumerate(runs):
                tm = _team(scene, r[0])
                if tm is not None and r[2] - r[1] <= rmax:
                    ry = _attacked_rim_y("D" if tm == "O" else "O")
                    nx_ = runs[i + 1] if i + 1 < len(runs) else None
                    f2 = min(n - 1, r[2] + aft, nx_[1] if nx_ is not None else n - 1)
                    dr_ = np.nanmax(np.hypot(bx[r[1] : r[2] + 1], by[r[1] : r[2] + 1] - ry))
                    d2_ = math.hypot(bx[f2], by[f2] - ry)
                    if dr_ <= rz and d2_ <= rz:
                        dropped.append((r[0], r[1], r[2], "rim_touch"))
                        continue
                    if nx_ is not None and _team(scene, nx_[0]) not in (None, tm) and dr_ <= rzs and d2_ <= rzs:
                        dropped.append((r[0], r[1], r[2], "rim_scrum"))
                        scrum = True
                        continue
                if keep and keep[-1][0] == r[0] and r[1] - keep[-1][2] - 1 <= merge:
                    keep[-1][2] = r[2]
                else:
                    keep.append(r)
            return keep, scrum

        # repeat: dropping a scrum touch can leave the hold before it followed by the other team (a chain of short
        # defender 'holds' while the ball bounces on the rim)
        runs, again = rim_pass(runs)
        while again:
            runs, again = rim_pass(runs)
        changed = True
        while changed:
            changed = False
            for i, r in enumerate(runs):
                if i == 0:
                    continue
                prev = runs[i - 1]
                nxt = runs[i + 1] if i + 1 < len(runs) else None
                tp, tr = _team(scene, prev[0]), _team(scene, r[0])
                cn = core_n(r)
                short = cn - 1 < cmin
                reason = None
                ry = _attacked_rim_y(tp)
                dr = np.hypot(bx - 0.0, by - ry)
                if tr != tp and short and cn < minf and (r[2] - r[1]) < cmin and dr[r[2]] < dr[r[1]] < dr[prev[2]]:
                    reason = "pass_through"
                elif short and nxt is not None:
                    tn = _team(scene, nxt[0])
                    kr_, kn_ = scene.k(r[0]), scene.k(nxt[0])
                    hand = nxt[1] - 1
                    if (
                        tn == tr
                        and nxt[1] - r[2] - 1 <= merge
                        and math.hypot(kr_.x[hand] - kn_.x[hand], kr_.y[hand] - kn_.y[hand])
                        <= pc["hold_r_m"] + pc["hold_stay_hyst_m"]
                    ):
                        reason = "brush"  # the ball brushed a teammate standing next to the catcher
                    elif tp == tn and tr != tp:
                        reason = "deflection"
                    elif tn != tr and _shot_gap(scene, tp, prev[2], r[1] - 1, pc) is not None:
                        reason = "scrum_touch"
                if (
                    reason is None
                    and nxt is not None
                    and tr != tp
                    and _team(scene, nxt[0]) == tp
                    and r[2] - r[1] < frames(pc["deflect_max_s"])
                    and nxt[1] - r[2] - 1 <= frames(pc["deflect_max_s"])
                ):
                    # loop 4 (TRN-L4-sandwich, real SportVU): an other-team hold shorter than deflect_max_s that gives
                    # the ball straight back (next hold by the previous team within deflect_max_s) is a deflection or
                    # a contact-distance misread (on-ball defender beside a dribbler, loose-ball scramble), not a
                    # change of possession
                    reason = "deflection"
                if reason is not None:
                    dropped.append((r[0], r[1], r[2], reason))
                    del runs[i]
                    if i < len(runs) and runs[i - 1][0] == runs[i][0] and runs[i][1] - runs[i - 1][2] - 1 <= merge:
                        runs[i - 1][2] = runs[i][2]
                        del runs[i]
                    changed = True
                    break
        _cache(scene)[_pkey("touches", pc)] = dropped
        return [tuple(r) for r in runs]

    return _memo(scene, _pkey("runs", pc), calc)


def _touches(scene, pc=None):
    """Touches dropped by _hold_runs: [(oid, a, b, reason)]."""
    _hold_runs(scene, pc)
    return _cache(scene)[_pkey("touches", pc)]


def _ball_filled(scene, pc=None):
    """Ball (x, y, estimated) per frame: observed smoothed ball, else the holder, else linear interpolation."""

    def calc():
        n = scene.n
        bx, by = np.full(n, np.nan), np.full(n, np.nan)
        b = scene.ball
        if b is not None:
            ok = b.state == "observed"
            bx[ok], by[ok] = b.x[ok], b.y[ok]
        h = _holders(scene, pc)
        for t in np.flatnonzero(np.isnan(bx)):
            if h[t] is not None:
                bx[t], by[t] = scene.k(h[t]).x[t], scene.k(h[t]).y[t]
        est = np.isnan(bx)
        idx = np.flatnonzero(~est)
        if len(idx):
            bx = np.interp(np.arange(n), idx, bx[idx])
            by = np.interp(np.arange(n), idx, by[idx])
        return bx, by, est

    return _memo(scene, _pkey("ball_filled", _pc(pc)), calc)


def _last_ball(scene, a, b):
    """Last frame in [a, b] at which the ball is still inside a tracked segment (q_obj of the ball stops there)."""
    if scene.ball is None:
        return a
    idx = np.flatnonzero(scene.ball.state[a : b + 1] != "none")
    return a + int(idx[-1]) if len(idx) else a


def _ball_sig(scene):
    b = scene.ball
    return _sig_p(b) if b is not None else np.full(scene.n, 0.5)


def _shots(scene, pc=None):
    """Shot proxies: after a hold the observed, unheld ball closes on the rim the holder's team attacks (_shot_gap)."""
    pc = _pc(pc)

    def calc():
        runs = _hold_runs(scene, pc)
        bxf, byf, _ = _ball_filled(scene, pc)
        out = []
        for i, (oid, a, e) in enumerate(runs):
            nxt = runs[i + 1][1] if i + 1 < len(runs) else scene.n
            res = _shot_gap(scene, _team(scene, oid), e, nxt - 1, pc)
            if res is None:
                continue
            rim, t_rim = res
            # loop 4 (TRN-L4-tipdup, real SportVU): a re-release by the same team at the same rim from a hold that
            # starts within shot_merge_s of the previous shot reaching the rim and whose ball never leaves
            # rim_scrum_r_m of that rim is the same attempt (ball rolling on the rim, a tip battle, a make dropping to
            # a teammate under the net): kept for the possession logic but flagged, so the per-shot crash / safety
            # reads are taken once per attempt
            tm = _team(scene, oid)
            ry = _attacked_rim_y(tm)
            prev = out[-1] if out else None
            same = bool(
                prev is not None
                and prev["team"] == tm
                and prev["rim"] == rim
                and a - prev["t_rim"] <= frames(pc["shot_merge_s"])
                and np.nanmax(np.hypot(bxf[a : e + 1], byf[a : e + 1] - ry)) <= pc["rim_scrum_r_m"]
            )
            out.append(
                dict(
                    shooter=oid,
                    team=tm,
                    t_rel=e,
                    t_rim=t_rim,
                    rim=rim,
                    run=i,
                    next_run=i + 1 if i + 1 < len(runs) else None,
                    same_attempt=same,
                )
            )
        return out

    return _memo(scene, _pkey("shots", pc), calc)


def _shot_after(scene, run_index, pc=None):
    for s in _shots(scene, pc):
        if s["run"] == run_index:
            return s
    return None


def _passes(scene, pc=None):
    """Ball transfers between consecutive holds of different players with no shot in between."""
    pc = _pc(pc)

    def calc():
        runs = _hold_runs(scene, pc)
        out = []
        for i in range(len(runs) - 1):
            (pa, _, e0), (pb, a1, _) = runs[i], runs[i + 1]
            if pa == pb or _shot_after(scene, i, pc) is not None or (a1 - e0) * DT > pc["pass_max_flight_s"]:
                continue
            kp, kr = scene.k(pa), scene.k(pb)  # pass vector from the passer at release to the receiver at the catch
            x0, y0, x1, y1 = float(kp.x[e0]), float(kp.y[e0]), float(kr.x[a1]), float(kr.y[a1])
            out.append(
                dict(
                    passer=pa,
                    receiver=pb,
                    t_rel=e0,
                    t_catch=a1,
                    catch_end=runs[i + 1][2],
                    run=i,
                    x0=x0,
                    y0=y0,
                    x1=x1,
                    y1=y1,
                    same_team=_team(scene, pa) == _team(scene, pb),
                    length=float(math.hypot(x1 - x0, y1 - y0)),
                )
            )
        return out

    return _memo(scene, _pkey("passes", pc), calc)


def _oob_start(scene, oid, a, e, tol, pc=None, z=None):
    """First frame of the out-of-bounds part of a hold that ENDS out of bounds (fix TRN-T01), else None.

    The last run of frames with the holder's boundary distance below tol (sideline: tol + oob_side_noise_z sigma_p;
    >= hold_min_frames long) must reach the
    end of the hold within oob_release_slack_frames: an inbounder who catches the ball under the net (in bounds) and
    then steps out is a throw-in from the frame he is out; a player who steps back in before releasing is not."""
    pc = _pc(pc)
    k = scene.k(oid)
    xs, ys = k.x[a : e + 1], k.y[a : e + 1]
    # fix TRN-T01 (loop 2): the SIDELINE test is noise-aware. A sideline thrower stands still just behind the line, so
    # smoothed-track noise reads him in bounds for long stretches at high sigma_p; he counts as in bounds only beyond
    # tol + oob_side_noise_z * sigma_p (p_in >= 0.9). The end lines keep the plain tolerance: an inbounder legitimately
    # runs along the end line (run_endline) and steps in right after the release (inbounder_step_in).
    dside = np.nan_to_num(SIDE_X - np.abs(xs), nan=9.0)
    dend = np.nan_to_num(np.minimum(ys - END_Y, FAR_END_Y - ys), nan=9.0)
    # loop 3 (TRN-T11 contract): z comes from the caller's merged throw_in params, the YAML default otherwise
    z = PARAMS["throw_in"]["oob_side_noise_z"] if z is None else z
    mask = (dend < tol) | (dside < tol + z * _sig_p(k)[a : e + 1])
    rr = _runs_of(mask, min(int(pc["hold_min_frames"]), e - a + 1))
    if rr and rr[-1][1] >= (e - a) - int(PARAMS["throw_in"]["oob_release_slack_frames"]):
        return a + rr[-1][0]
    return None


def _made_before(scene, t, window_s=None, pc=None):
    """A made-basket proxy (a far-rim shot of the losing team) within made_window_s before t."""
    window_s = PARAMS["throw_in"]["made_window_s"] if window_s is None else window_s
    return any(
        s["rim"] == "far" and s["team"] == "D" and 0 <= (t - s["t_rim"]) * DT <= window_s for s in _shots(scene, pc)
    )


def _throw_ins(scene, pc=None, **over):
    """TRN-R05 state machine on the hold sequence (see detect_throw_in)."""
    p = _prm("throw_in", over)
    pc = _pc(pc)

    def calc():
        runs = _hold_runs(scene, pc)
        bx, by, _ = _ball_filled(scene, pc)
        out, used = [], set()
        for i, (oid, a, e) in enumerate(runs):
            s0 = None if i in used else _oob_start(scene, oid, a, e, p["oob_tol_m"], pc, p["oob_side_noise_z"])
            if s0 is None:
                continue
            team = _team(scene, oid)
            j, thrower, relay, rel = i + 1, oid, False, e
            while (
                j < len(runs)
                and _team(scene, runs[j][0]) == team
                and _oob_start(scene, runs[j][0], runs[j][1], runs[j][2], p["oob_tol_m"], pc, p["oob_side_noise_z"])
                is not None
            ):
                used.add(j)
                relay, thrower, rel = True, runs[j][0], runs[j][2]
                j += 1
            if j >= len(runs) or (runs[j][1] - rel) * DT > p["max_flight_s"]:
                continue
            rcv, t_ft = runs[j][0], runs[j][1]
            k = scene.k(oid)
            x0, y0 = float(np.nanmean(k.x[s0 : min(e, s0 + 4) + 1])), float(np.nanmean(k.y[s0 : min(e, s0 + 4) + 1]))
            if y0 <= END_Y + p["oob_tol_m"]:
                rtype = "blob"
            elif y0 >= FAR_END_Y - p["oob_tol_m"]:
                rtype = "backcourt_endline"
            else:
                rtype = "slob_frontcourt" if y0 <= HALF_Y else "slob_backcourt"
            opp = scene.defense if team == "O" else scene.offense
            dmin = min(
                (
                    math.hypot(scene.k(d).x[t_ft] - scene.k(rcv).x[t_ft], scene.k(d).y[t_ft] - scene.k(rcv).y[t_ft])
                    for d in opp
                ),
                default=np.inf,
            )
            length = float(math.hypot(bx[t_ft] - bx[rel], by[t_ft] - by[rel]))
            out.append(
                dict(
                    thrower=oid,
                    last_thrower=thrower,
                    receiver=rcv,
                    team=team,
                    t_disposal=s0,
                    t_pickup=a,
                    t_release=rel,
                    t_first_touch=t_ft,
                    count_s=(e - s0) * DT,
                    restart_type=rtype,
                    after_make=bool(rtype == "backcourt_endline" and _made_before(scene, s0, pc=pc)),
                    x0=x0,
                    y0=y0,
                    relay=relay,
                    length=length,
                    contested=bool(dmin <= p["contested_m"]),
                    run=i,
                    recv_run=j,
                )
            )
        return out

    if over or pc != PARAMS["possession_change"]:
        return calc()
    return _memo(scene, "throw_ins", calc)


def _gathered(scene, oid, e, pc):
    """The loser gathered before releasing: stationary (s2 < chi2) on >= block_gather_share of his last
    block_gather_s (a shot or a pass from a set position, not a dribble picked by a defender)."""
    k = scene.k(oid)
    a = max(0, e - frames(pc["block_gather_s"]))
    return bool(np.mean(k.stationary_s2[a : e + 1] < CHI2) >= pc["block_gather_share"])


def _possessions(scene, pc=None):
    """D -> O possession changes with start type and anchors (TRN-R01)."""
    pc = _pc(pc)

    def calc():
        runs = _hold_runs(scene, pc)
        bx, by, _ = _ball_filled(scene, pc)
        touches = _touches(scene, pc)
        tws = {tw["run"]: tw for tw in _throw_ins(scene, pc)}
        out = []
        for i in range(len(runs) - 1):
            lo, (go, ga, ge) = runs[i], runs[i + 1]
            if _team(scene, lo[0]) != "D" or _team(scene, go) != "O":
                continue
            shot = _shot_after(scene, i, pc)
            s_oob = _oob_start(scene, go, ga, ge, pc["oob_tol_m"], pc)
            oob = s_oob is not None
            t0, t_disp, alt = ga, None, None
            if shot is not None:
                stype = "made_fg" if oob else "dreb"
            elif oob:
                stype = "dead_ball_to"
            else:
                stype = "steal"
                ks, kg = scene.k(lo[0]), scene.k(go)
                e = lo[2]
                h = frames(pc["block_heading_s"])
                if e + h < scene.n:
                    vx, vy = bx[e + h] - bx[e], by[e + h] - by[e]
                    tx, ty = -bx[e], FAR_RIM_Y - by[e]
                    cosang = (vx * tx + vy * ty) / max(1e-6, math.hypot(vx, vy) * math.hypot(tx, ty))
                    if (
                        math.hypot(ks.x[e], ks.y[e] - FAR_RIM_Y) <= pc["block_shooter_r_m"]
                        and cosang >= 0.7
                        and math.hypot(kg.x[ga] - ks.x[e], kg.y[ga] - ks.y[e]) <= pc["block_dist_m"]
                    ):
                        # fix TRN-T08: without a gather before the release it is more likely a steal of a forward
                        # pass; the block reading is kept as the alternative until ball z exists
                        if _gathered(scene, lo[0], e, pc):
                            stype = "block_to_break"
                        else:
                            alt = "block_to_break"
            if oob:  # t0 of a throw-in start is the first legal touch (CTG convention)
                t_disp = s_oob
                tw = tws.get(i + 1)
                if tw is not None:
                    t0 = tw["t_first_touch"]
            after = np.arange(t0, scene.n)

            def first(mask):
                idx = after[mask[after]]
                return int(idx[0]) if len(idx) else None

            kg = scene.k(go)
            conf_b = min(scene.n - 1, t0 + frames(pc["conf_window_s"]))
            holder_now = _holders(scene, pc)[t0]
            kh = scene.k(holder_now) if holder_now is not None else kg
            d = np.hypot(scene.ball.x - kh.x, scene.ball.y - kh.y)
            pr = p_below(d, _stay_r(pc), mv.sigma_dist(kh, scene.ball))
            conf = window_conf(pr, t0, conf_b) * _qobj(scene, [holder_now or go, "ball"], t0, t0, conf_b)
            touched = [tc[0] for tc in touches if lo[2] < tc[1] < ga]
            out.append(
                dict(
                    t0=t0,
                    gainer=go,
                    loser=lo[0],
                    start_type=stype,
                    alt_start_type=alt,
                    touched_by=touched,
                    t_rel=shot["t_rel"] if shot else None,
                    t_rim=shot["t_rim"] if shot else None,
                    shooter=shot["shooter"] if shot else None,
                    t_disposal=t_disp,
                    run=i + 1,
                    conf=conf,
                    gain_xy=(float(kg.x[ga]), float(kg.y[ga])),
                    t_cross_half=first(by <= HALF_Y),
                    t_scoring_zone=first(by <= SZ_Y),
                    t_three_zone=first(np.hypot(bx, by) <= THREE_R),
                )
            )
        return out

    return _memo(scene, _pkey("possessions", pc), calc)


def _handler(scene):
    """Offensive ball handler per frame, forward-filled through passes in flight (None before any O hold)."""

    def calc():
        h = _holders(scene)
        out = np.array([None] * scene.n, dtype=object)
        last = None
        for t in range(scene.n):
            if h[t] is not None:
                last = h[t] if _team(scene, h[t]) == "O" else None
            out[t] = last
        return out

    return _memo(scene, "handler", calc)


def _first_shot_after(scene, t, team="O"):
    for s in _shots(scene):
        if s["t_rel"] >= t and s["team"] == team:
            return s
    return None


# --------------------------------------------------------------------------------------
# Rules (TRN-R01, R02, R03, R05)
# --------------------------------------------------------------------------------------
def detect_possession_change(scene, **params) -> list[Event]:
    """TRN-R01: D -> O changes of control with start type (rebound / steal / made-basket proxies)."""
    pc = _prm("possession_change", params)
    out = []
    for p in _possessions(scene, pc):
        actors = {"gainer": p["gainer"], "loser": p["loser"]}
        out.append(
            _ev(
                "possession_change",
                actors,
                p["t0"],
                p["t_rel"] if p["t_rel"] is not None else p["t0"],
                p["t0"],
                p["conf"],
                start_type=p["start_type"],
                alt_start_type=p["alt_start_type"],
                touched_by=p["touched_by"],
                t_rel=p["t_rel"],
                t_rim=p["t_rim"],
                t_net_proxy=p["t_rim"] if p["start_type"] == "made_fg" else None,
                t_disposal=p["t_disposal"],
                t_cross_half=p["t_cross_half"],
                t_scoring_zone=p["t_scoring_zone"],
                t_three_zone=p["t_three_zone"],
                gain_xy=p["gain_xy"],
                anchor_source="tracking_only",
            )
        )
    return out


def detect_transition_phase(scene, **params) -> list[Event]:
    """TRN-R02: transition interval (rule_transition_window) plus the scheme-aware defense-set time."""
    p = _prm("transition_phase", params)
    bx, by, _ = _ball_filled(scene)
    hd = _handler(scene)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        tmax = min(scene.n - 1, t0 + frames(p["max_s"]))
        need = _dwell(p["handler_slow_s"])
        run, end, reason = 0, tmax, "cap"
        for t in range(t0, tmax + 1):
            n_front = sum(scene.k(o).y[t] <= HALF_Y for o in scene.offense)
            slow = hd[t] is not None and _vbar(scene, hd[t], VS)[0][t] < p["handler_slow_mps"]
            run = run + 1 if (by[t] <= HALF_Y and n_front >= p["min_attackers_front"] and slow) else 0
            if run >= need:
                end, reason = t, "settled"
                break
        if (end - t0) * DT < MIN_DUR["transition_phase"] - 1e-9:
            continue
        set_t, set_reason = _defense_set(scene, t0, p)
        conf = ps["conf"]
        if reason == "settled":
            a = end - need + 1
            conf *= window_conf(p_below(by, HALF_Y, _ball_sig(scene)), a, end)
        out.append(
            _ev(
                "transition",
                {"gainer": ps["gainer"]},
                t0,
                t0,
                end,
                conf,
                end_reason=reason,
                defense_set_t=set_t,
                defense_set_reason=set_reason,
                poss_t0=t0,
            )
        )
    return out


def _defense_set(scene, t0, p):
    """First frame of a held defense set (guarded or help-covered attackers), else the 12-s timeout."""
    tmax = min(scene.n - 1, t0 + frames(p["set_timeout_s"]))
    need = _dwell(p["set_dwell_s"])
    run, used_help = 0, False
    for t in range(t0, tmax + 1):
        ok, helped = True, False
        if any(scene.k(o).y[t] > HALF_Y for o in scene.players()):
            ok = False
        else:
            for a in scene.offense:
                ka = scene.k(a)
                ra = math.hypot(ka.x[t], ka.y[t])
                g = h = False
                for d in scene.defense:
                    kd = scene.k(d)
                    dd = math.hypot(kd.x[t] - ka.x[t], kd.y[t] - ka.y[t])
                    rd = math.hypot(kd.x[t], kd.y[t])
                    if rd < ra and dd <= p["guard_r_m"]:
                        g = True
                    elif (
                        rd < ra
                        and dd <= p["help_r_m"]
                        and _seg_dist(kd.x[t], kd.y[t], ka.x[t], ka.y[t], 0.0, 0.0) <= p["help_lateral_m"]
                    ):
                        h = True
                if not g and not h:
                    ok = False
                    break
                helped |= not g and h
        run = run + 1 if ok else 0
        used_help = (used_help or helped) if ok else False
        if run >= need:
            return t - need + 1, ("help_covered" if used_help else "rtr08_guarded")
    return None, "timeout_12s"


def detect_early_offense_window(scene, **params) -> list[Event]:
    """TRN-R02b: early-offense interval after transition until t0 + 12 s or the first shot."""
    p = _prm("early_offense_window", params)
    out = []
    for tr in _memo(scene, "transition", lambda: detect_transition_phase(scene)):
        t0 = tr.attrs["poss_t0"]
        a = tr.end + 1
        b, reason = min(scene.n - 1, t0 + frames(p["end_s"])), "clock_12s"
        s = _first_shot_after(scene, a)
        if s is not None and s["t_rel"] < b:
            b, reason = s["t_rel"], "shot"
        if (b - a) * DT < MIN_DUR["early_offense_window"] - 1e-9:
            continue
        out.append(_ev("early_offense", tr.actors, a, a, b, tr.conf, end_reason=reason, poss_t0=t0))
    return out


CONTE_PRIMARY = {"1v0", "1v1", "2v1", "2v2", "3v1", "3v2", "3v3", "4v2"}
CONTE_SECONDARY = {"4v3", "4v4", "5v4"}


def _numbers_counts(scene, t0, tmax, margin, hyst):
    """Per-frame A_play / D_back with symmetric bins and per-player hysteresis (TRN-R03)."""
    bx, by, _ = _ball_filled(scene)
    A = np.zeros(tmax - t0 + 1, dtype=int)
    D = np.zeros_like(A)
    for team, arr in (("O", A), ("D", D)):
        for o in scene.offense if team == "O" else scene.defense:
            y = scene.k(o).y
            inside = False
            for i, t in enumerate(range(t0, tmax + 1)):
                m = by[t] + margin - y[t]
                inside = (m >= 0) if not inside else (m >= -hyst)
                if team == "O" and y[t] > HALF_Y + 3.0:
                    continue
                arr[i] += int(inside)
    return A, D


def detect_numbers_advantage(scene, **params) -> list[Event]:
    """TRN-R03: advantage episodes A_play - D_back >= 1 (enter 0.3 s, exit <= 0 for 0.5 s)."""
    p = _prm("numbers_advantage", params)
    bx, by, _ = _ball_filled(scene)
    sb = _ball_sig(scene)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        tmax = min(scene.n - 1, t0 + frames(p["max_s"]))
        if tmax <= t0:
            continue
        A, D = _numbers_counts(scene, t0, tmax, p["margin_m"], p["hyst_m"])
        diff = A - D
        need_in, need_out = _dwell(p["enter_s"]), _dwell(p["exit_s"])
        i, L = 0, len(diff)
        while i < L:
            if diff[i] < 1:
                i += 1
                continue
            j = i
            while j < L and diff[j] >= 1:
                j += 1
            if j - i < need_in:
                i = j
                continue
            # episode from i; it ends at the start of the first run of >= need_out frames with diff <= 0
            k, end = i, L - 1
            while k < L:
                if diff[k] <= 0:
                    m = k
                    while m < L and diff[m] <= 0:
                        m += 1
                    if m - k >= need_out or m == L:
                        end = k - 1
                        break
                    k = m
                else:
                    k += 1
            a, b = t0 + i, t0 + end
            cfg = f"{A[i]}v{D[i]}"
            # per-frame probability that the advantage holds (Poisson-binomial over players)
            pr = np.zeros(b - a + 1)
            for q, t in enumerate(range(a, b + 1)):
                pa = [
                    phi((by[t] + p["margin_m"] - scene.k(o).y[t]) / math.hypot(_sig_p(scene.k(o))[t], sb[t]))
                    * float(scene.k(o).y[t] <= HALF_Y + 3.0)
                    for o in scene.offense
                ]
                pd = [
                    phi((by[t] + p["margin_m"] - scene.k(o).y[t]) / math.hypot(_sig_p(scene.k(o))[t], sb[t]))
                    for o in scene.defense
                ]
                pa, pd = np.asarray(pa), np.asarray(pd)
                e = pa.sum() - pd.sum()
                v = (pa * (1 - pa)).sum() + (pd * (1 - pd)).sum()
                pr[q] = phi((e - 0.5) / math.sqrt(v + 0.02))
            conf = float(np.mean(pr)) * _qobj(scene, ["ball"], a, a, _last_ball(scene, a, b))
            typ = "prim_conte" if cfg in CONTE_PRIMARY else ("sec_conte" if cfg in CONTE_SECONDARY else "unlisted")
            alt = {}
            for mm in (0.5, 1.5):
                Am, Dm = _numbers_counts(scene, a, a, mm, p["hyst_m"])
                alt[f"config_m{mm}"] = f"{Am[0]}v{Dm[0]}"
            out.append(
                _ev(
                    "numbers_advantage",
                    {"gainer": ps["gainer"]},
                    a,
                    a,
                    b,
                    conf,
                    config=cfg,
                    typology=typ,
                    max_adv=int(diff[i : end + 1].max()),
                    poss_t0=t0,
                    **alt,
                )
            )
            i = end + need_out
    return out


def detect_throw_in(scene, **params) -> list[Event]:
    """TRN-R05 + TRN-A12: disposal, count, release, first legal touch and the inbound pass."""
    p = _prm("throw_in", params)
    out = []
    for tw in _throw_ins(scene, **params):
        kt = scene.k(tw["thrower"])
        a, rel, ft = tw["t_disposal"], tw["t_release"], tw["t_first_touch"]
        pout = p_below(_d_in(kt.x, kt.y), p["oob_tol_m"], _sig_p(kt))
        kr = scene.k(tw["receiver"])
        ph = p_below(
            np.hypot(scene.ball.x - kr.x, scene.ball.y - kr.y),
            _stay_r(),
            mv.sigma_dist(kr, scene.ball),
        )
        fb = min(scene.n - 1, ft + frames(0.2))
        conf = (
            window_conf(pout, a, rel)
            * window_conf(ph, ft, fb)
            * _qobj(scene, [tw["thrower"], tw["receiver"]], rel, a, fb)
        )
        out.append(
            _ev(
                "throw_in",
                {"thrower": tw["thrower"], "receiver": tw["receiver"]},
                rel,
                a,
                ft,
                conf,
                t_disposal=a,
                t_release=rel,
                t_first_touch=ft,
                count_s=tw["count_s"],
                restart_type=tw["restart_type"],
                after_make=tw["after_make"],
                pass_length_m=tw["length"],
                long_inbound=tw["length"] >= p["long_m"],
                endline_relay=tw["relay"],
                near_5s=tw["count_s"] >= p["near_5s_s"],
                burned_inbound=tw["count_s"] >= p["burned_s"],
                receiver_contested=tw["contested"],
            )
        )
    return out


# --------------------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------------------
def _upcourt(scene, oid, a, b, enter, stay, dwell_s, min_dy, min_dur, w=VS):
    """Runs toward the origin rim: enter vy_bar <= enter, stay <= stay; returns [(s, e)] inside [a, b]."""
    vx, vy, sg = _wvel(scene, oid, w)
    n = scene.n
    win = np.zeros(n, dtype=bool)
    win[max(0, a) : min(n - 1, b) + 1] = True
    ent = win & (np.nan_to_num(vy, nan=9) <= enter)
    sty = win & (np.nan_to_num(vy, nan=9) <= stay)
    y = scene.k(oid).y
    res = []
    for s, e in mv.hysteresis(ent, sty, min_dur, frames(dwell_s)):
        if y[e] - y[s] <= min_dy:
            res.append((s, e))
    return res


def _upcourt_runs(scene, p=None):
    """Upcourt runs per possession: [(poss, oid, s, e, conf)] with the upcourt_run parameters (YAML defaults unless
    detect_upcourt_run passes overrides, fix TRN-T11). rim_run, wing_lane_run, corner_fill and middle_lane_run are
    built on the default runs (their own items carry only their own parameters)."""
    p = _prm("upcourt_run") if p is None else p

    def calc():
        out = []
        for ps in _possessions(scene):
            t0 = ps["t0"]
            for o in scene.offense:
                for s, e in _upcourt(
                    scene,
                    o,
                    t0 - frames(p["pre_s"]),
                    t0 + frames(p["post_s"]),
                    p["enter_vy_mps"],
                    p["exit_vy_mps"],
                    p["exit_dwell_s"],
                    p["min_dy_m"],
                    MIN_DUR["upcourt_run"],
                    VS,
                ):
                    vx, vy, sg = _wvel(scene, o, VS)
                    conf = window_conf(p_below(vy, p["exit_vy_mps"], sg), s, e) * _qobj(scene, [o], s, s, e)
                    out.append((ps, o, s, e, conf))
        return out

    return _memo(scene, _pkey("upcourt", p, "upcourt_run"), calc)


def _holds_share(scene, oid, a, b):
    h = _holders(scene)[a : b + 1]
    return float(np.mean([x == oid for x in h])) if b >= a else 0.0


def detect_upcourt_run(scene, **params) -> list[Event]:
    """TRN-P01: sustained run toward the attacked rim after a possession change."""
    p = _prm("upcourt_run", params)
    out = []
    for ps, o, s, e, conf in _upcourt_runs(scene, p):
        k = scene.k(o)
        v10, _ = _vbar(scene, o, VL)
        yl = FAR_RIM_Y - k.y[s]
        area = (
            "below_ft_extended"
            if yl <= FT_Y
            else ("between_ft_and_arc_extended" if yl <= THREE_R else "beyond_arc_extended")
        )
        cr = np.flatnonzero(k.y[s : e + 1] <= HALF_Y)
        out.append(
            _ev(
                "upcourt_run",
                {"runner": o},
                s,
                s,
                e,
                conf,
                delta_y=float(k.y[e] - k.y[s]),
                mean_vbar10=float(np.nanmean(v10[s : e + 1])),
                peak_vbar10=float(np.nanmax(v10[s : e + 1])),
                start_area=area,
                t_cross_half=int(s + cr[0]) if len(cr) else None,
                poss_t0=ps["t0"],
                onset_rel_t0_s=(s - ps["t0"]) * DT,
            )
        )
    return out


def _v_peak(scene, oid):
    """v_peak by shrinkage (TRN-R00, fix TRN-T14): (k_prior * prior + n * median_games) / (k_prior + n).

    Kin.extra may carry 'position' ('G' | 'F' | 'C'; default C, the most lenient prior) and 'v_peak_games' (per-game
    maxima of vbar(1.0) on the smoothed track). An explicit extra['v_peak'] is taken as already blended."""
    ex = scene.k(oid).extra
    if "v_peak" in ex:
        return float(ex["v_peak"])
    prior = {"G": FAM["v_peak_prior_g_mps"], "F": FAM["v_peak_prior_f_mps"]}.get(
        ex.get("position"), FAM["v_peak_default_mps"]
    )
    games = [float(g) for g in ex.get("v_peak_games", ()) if np.isfinite(g)]
    if not games:
        return float(prior)
    k0, n = FAM["v_peak_shrink_games"], len(games)
    return float((k0 * prior + n * np.median(games)) / (k0 + n))


def detect_rim_run(scene, **params) -> list[Event]:
    """TRN-P02: rim-to-rim run (path, lane, relative speed and arrival-before-ball tests)."""
    p = _prm("rim_run", params)
    bx, by, _ = _ball_filled(scene)
    out = []
    for ps, o, s, e, uconf in _upcourt_runs(scene):
        k = scene.k(o)
        pre = max(0, s - frames(1.0))
        near = np.flatnonzero(_r_far(k)[pre : s + 1] <= p["start_r_far_m"])
        if not len(near):
            continue
        dep = pre + int(near[-1])  # departure: last frame within start_r_far_m of the rim he leaves
        r = np.hypot(k.x, k.y)
        hi = min(scene.n - 1, e + frames(2.0))
        arr = np.flatnonzero(r[s : hi + 1] <= p["end_r_m"])
        if len(arr) == 0:
            continue
        f = s + int(arr[0])
        if (f - dep) * DT < MIN_DUR["rim_run"] - 1e-9:
            continue  # fix TRN-T15: min_duration_s is the rim-to-rim time, departure to arrival
        path = float(np.nansum(np.hypot(np.diff(k.x[dep : f + 1]), np.diff(k.y[dep : f + 1]))))
        mean_ax = float(np.nanmean(np.abs(k.x[s : f + 1])))
        v10, _ = _vbar(scene, o, VL)
        mean_v, peak_v = float(np.nanmean(v10[s : min(e, f) + 1])), float(np.nanmax(v10[s : f + 1]))
        vp = _v_peak(scene, o)
        if path < p["min_path_m"] or mean_ax > p["max_mean_abs_x_m"]:
            continue
        if mean_v < max(p["min_speed_mps"], p["rel_mean"] * vp) or peak_v < p["rel_peak"] * vp:
            continue
        t_arc = ps["t_three_zone"]
        if t_arc is not None and (f - t_arc) * DT > p["arrive_after_ball_s"]:
            continue
        fb = min(scene.n - 1, f + frames(0.2))
        sx = float(np.nanmedian(_sig_p(k)[s : f + 1]))
        conf = (
            uconf
            * window_conf(p_below(r, p["end_r_m"], _sig_p(k)), f, fb)
            * float(phi((p["max_mean_abs_x_m"] - mean_ax) / sx))
        )
        fast = _runs_of(np.nan_to_num(v10, nan=0) >= p["repo_speed_mps"], _dwell(p["repo_dur_s"]))
        out.append(
            _ev(
                "rim_run",
                {"runner": o},
                s,
                s,
                f,
                conf,
                t_rim_arrive=f,
                path_m=path,
                mean_abs_x=mean_ax,
                mean_vbar10=mean_v,
                peak_vbar10=peak_v,
                v_rel=mean_v / vp,
                poss_t0=ps["t0"],
                ahead_of_ball_s=None if t_arc is None else (t_arc - f) * DT,
                rim_run_repo=any(a_ <= f and b_ >= s for a_, b_ in fast),
            )
        )
    firsts = sorted(out, key=lambda ev: ev.attrs["t_rim_arrive"])
    if firsts:
        firsts[0].attrs["first_big_down"] = True
    return out


def _lane_samples(k, s, e):
    sl = np.arange(s, e + 1)
    m = (k.y[sl] >= 6.0) & (k.y[sl] <= 22.0)
    return sl[m]


def detect_wing_lane_run(scene, **params) -> list[Event]:
    """TRN-P03a: non-handler upcourt run in the sideline or lane-line lane (transition_lanes_5)."""
    p = _prm("wing_lane_run", params)
    out = []
    for ps, o, s, e, uconf in _upcourt_runs(scene):
        if _holds_share(scene, o, s, e) >= 0.5:
            continue
        k = scene.k(o)
        sm = _lane_samples(k, s, e)
        if len(sm) < p["min_lane_samples"]:
            continue
        med = float(np.median(np.abs(k.x[sm])))
        if med < LANE_X or (e - s) * DT < MIN_DUR["wing_lane_run"] - 1e-9:
            continue
        sx = float(np.median(_sig_p(k)[sm]))
        # fix TRN-T13: the label confidence uses the wing-vs-middle edge (LANE_X); the sideline / lane-line split is
        # a sub-class stored with its own probability
        p_side = float(phi((med - p["sideline_x_m"]) / sx))
        lane = "sideline" if p_side >= 0.5 else "laneline"
        vx = _wvel(scene, o, VS)[0]
        back = sm[k.y[sm] > HALF_Y]
        stable = bool(len(back) and np.nanmedian(np.abs(vx[back])) < p["stable_vx_mps"])
        conf = uconf * float(phi((med - LANE_X) / sx))
        out.append(
            _ev(
                "wing_lane_run",
                {"runner": o},
                s,
                s,
                e,
                conf,
                lane=lane,
                p_sideline=p_side,
                side=int(np.sign(np.median(k.x[sm]))),
                median_abs_x=med,
                stable=stable,
                wing_lane_thirds=med >= 2.54,
                msu_wing_lane_v2=med >= 6.0,
                poss_t0=ps["t0"],
            )
        )
    return out


def detect_corner_fill(scene, **params) -> list[Event]:
    """TRN-P03b: upcourt run ending with occupation of transition_corner_arrival."""
    p = _prm("corner_fill", params)
    passes = _passes(scene)
    out = []
    for ps, o, s, e, uconf in _upcourt_runs(scene):
        k = scene.k(o)
        hi = min(scene.n - 1, e + frames(3.0))
        f = next((t for t in range(s, hi + 1) if _in_spot("transition_corner_arrival", k.x[t], k.y[t])), None)
        if f is None:
            continue
        t_arc = ps["t_three_zone"]
        if (f - ps["t0"]) * DT > p["arrive_max_s"] and (t_arc is None or (f - t_arc) * DT > p["after_ball_s"]):
            continue
        need = _dwell(max(p["dwell_s"], MIN_DUR["corner_fill"]))
        stat = (k.stationary_s2 < CHI2) & np.array(
            [_in_spot("transition_corner_arrival", k.x[t], k.y[t]) for t in range(scene.n)]
        )
        stat[:f] = False
        runs = [ab for ab in _runs_of(stat, need) if ab[0] <= f + frames(2.0)]
        caught = any(
            q["receiver"] == o
            and q["same_team"]
            and q["t_catch"] >= f
            and _in_spot("transition_corner_arrival", k.x[q["t_catch"]], k.y[q["t_catch"]])
            for q in passes
        )
        if not runs and not caught:
            continue
        a, b = runs[0] if runs else (f, min(scene.n - 1, f + need))
        r = np.hypot(k.x, k.y)
        margin = np.minimum(r - 6.6, 7.3 - r)
        conf = window_conf(phi(margin / _sig_p(k)), a, b) * _qobj(scene, [o], f, f, b)
        out.append(
            _ev(
                "corner_fill",
                {"runner": o},
                f,
                s,
                b,
                conf,
                arrival_rel_t0_s=(f - ps["t0"]) * DT,
                side=int(np.sign(k.x[f])),
                caught=caught,
                poss_t0=ps["t0"],
            )
        )
    return out


def detect_middle_lane_run(scene, **params) -> list[Event]:
    """TRN-P04: non-handler upcourt run in the middle lane (|x| < LANE_X on >= 60% of lane samples)."""
    p = _prm("middle_lane_run", params)
    out = []
    for ps, o, s, e, uconf in _upcourt_runs(scene):
        if _holds_share(scene, o, s, e) >= 0.5:
            continue
        k = scene.k(o)
        sm = _lane_samples(k, s, e)
        if len(sm) < 10 or (e - s) * DT < MIN_DUR["middle_lane_run"] - 1e-9:
            continue
        inside = np.abs(k.x[sm]) < LANE_X
        share = float(np.mean(inside))
        if share < p["min_share"]:
            continue
        pin = phi((LANE_X - np.abs(k.x[sm])) / _sig_p(k)[sm])
        conf = uconf * _pb_count(pin, p["min_share"] * len(sm))
        mts = bool(abs(k.x[s]) < LANE_X and k.y[s] >= 15 and abs(k.x[e]) >= 5.3 and k.y[e] <= 6)
        out.append(
            _ev("middle_lane_run", {"runner": o}, s, s, e, conf, share=share, middle_to_side=mts, poss_t0=ps["t0"])
        )
    return out


def _first_cross(scene, oid, a, b, y_line=HALF_Y):
    y = scene.k(oid).y
    idx = np.flatnonzero(y[max(0, a) : b + 1] <= y_line)
    return int(max(0, a) + idx[0]) if len(idx) else None


def detect_leak_out(scene, **params) -> list[Event]:
    """TRN-P05: early release toward the attacked rim around the possession change; first attacker across."""
    p = _prm("leak_out", params)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        a = max(0, t0 - frames(p["search_before_t0_s"]))
        b = min(scene.n - 1, t0 + frames(8.0))
        cross = {o: _first_cross(scene, o, a, b) for o in scene.offense}
        for o in scene.offense:
            vx, vy, sg = _wvel(scene, o, VS)
            ent = np.nan_to_num(vy, nan=9) <= p["enter_vy_mps"]
            sty = np.nan_to_num(vy, nan=9) <= p["exit_vy_mps"]
            ent[:a] = False
            ent[t0 + frames(p["max_after_t0_s"]) + 1 :] = False
            ivs = mv.hysteresis(ent, sty, MIN_DUR["leak_out"], frames(p["exit_dwell_s"]))
            if not ivs or cross[o] is None:
                continue
            others = [cross[q] for q in scene.offense if q != o and cross[q] is not None]
            if others and min(others) <= cross[o]:
                continue
            s, e = ivs[0]
            k = scene.k(o)
            c = cross[o]
            deep = min(scene.k(d).y[c] for d in scene.defense) if scene.defense else np.nan
            sub = "early_leak" if s < t0 else "leak_out"
            tr_ = ps["t_rel"]
            if tr_ is not None and s < tr_:
                sub = "cherry_pick"
            elif tr_ is not None and ps["shooter"] is not None:
                # fix TRN-T16: the YAML alternative - already > cherry_far_m from the shooter and moving away at t_rel
                ksh = scene.k(ps["shooter"])
                far = math.hypot(k.x[tr_] - ksh.x[tr_], k.y[tr_] - ksh.y[tr_]) > p["cherry_far_m"]
                if far and vy[tr_] <= p["exit_vy_mps"]:
                    sub = "cherry_pick"
            sb = min(scene.n - 1, s + frames(0.5))
            conf = window_conf(p_below(vy, p["enter_vy_mps"], sg), s, sb) * _qobj(scene, [o], s, s, e)
            out.append(
                _ev(
                    "leak_out",
                    {"runner": o},
                    s,
                    s,
                    e,
                    conf,
                    sub_type=sub,
                    onset_rel_t0_s=(s - t0) * DT,
                    onset_rel_trel_s=None if ps["t_rel"] is None else (s - ps["t_rel"]) * DT,
                    lead_m=float(k.y[c] - deep),
                    t_cross_half=c,
                    poss_t0=t0,
                )
            )
    return out


def _trailers(scene, p=None):
    """Trailer ranking per possession: [(poss, oid, rank, cross, margin_s)] (fix TRN-T07).

    All attackers are ranked by their first frame at y <= half_y; trailer_1 is the 4th across and trailer_2 the 5th
    (the handler included). When that player held the ball at his crossing the rank gets no event (the 3rd across
    is never promoted). Players not across by the first shot or the window end are censored."""
    p = _prm("trailer") if p is None else p

    def calc():
        out = []
        h = _holders(scene)
        for ps in _possessions(scene):
            t0 = ps["t0"]
            a = max(0, t0 - frames(1.5))
            b = min(scene.n - 1, t0 + frames(p["window_s"]))
            s = _first_shot_after(scene, t0)
            if s is not None:
                b = min(b, s["t_rel"])
            cr = []
            for o in scene.offense:
                c = _first_cross(scene, o, a, b)
                if c is not None:
                    cr.append((c, o))
            cr.sort()

            def is_handler(c, o):
                return any(x == o for x in h[max(0, c - 2) : c + 3])

            for rank, idx in ((1, 3), (2, 4)):
                if idx < len(cr):
                    c, o = cr[idx]
                    tie = False
                    if is_handler(c, o):
                        # the handler at his crossing is never a trailer; the 3rd across takes trailer_1 only when he
                        # crossed within tie_s of the handler (an order the noise cannot resolve), never otherwise
                        c3, o3 = cr[idx - 1]
                        if rank != 1 or (c - c3) * DT > p["tie_s"] or is_handler(c3, o3):
                            continue
                        c, o, idx, tie = c3, o3, idx - 1, True
                    gaps = [abs(c - cr[idx - 1][0])] + ([abs(cr[idx + 1][0] - c)] if idx + 1 < len(cr) else [])
                    out.append((ps, o, rank, c, min(gaps) * DT, tie))
        return out

    return _memo(scene, _pkey("trailers", p, "trailer"), calc)


def detect_trailer(scene, **params) -> list[Event]:
    """TRN-P06: first / second trailer by half-court crossing order (non-handlers), with trail arrival."""
    p = _prm("trailer", params)
    out = []
    for ps, o, rank, c, margin, tie in _trailers(scene, p):
        k = scene.k(o)
        t0 = ps["t0"]
        tb = ps["t_cross_half"]
        sz_b = ps["t_scoring_zone"]
        sz_o = _first_cross(scene, o, c, scene.n - 1, SZ_Y)
        ctg = sz_b is not None and sz_o is not None and (sz_o - sz_b) * DT > p["ctg_delay_s"]
        v05, _ = _vbar(scene, o, VS)
        hi = min(scene.n - 1, t0 + frames(p["arrival_max_s"]))
        arr = next(
            (t for t in range(c, hi + 1) if v05[t] < p["arrive_vbar_mps"] and _in_spot("trail_spot", k.x[t], k.y[t])),
            None,
        )
        cb = min(scene.n - 1, c + frames(0.3))
        conf = (
            window_conf(p_below(k.y, HALF_Y, _sig_p(k)), c, cb) * float(phi(margin / 0.1)) * _qobj(scene, [o], c, c, cb)
        )
        out.append(
            _ev(
                "trailer",
                {"trailer": o},
                c,
                c,
                arr if arr is not None else cb,
                conf,
                rank=rank,
                delay_s=None if tb is None else (c - tb) * DT,
                trailer_ctg=bool(ctg),
                trail_arrival=arr,
                order_margin_s=margin,
                tie_with_handler=tie,
                poss_t0=t0,
            )
        )
    return out


def detect_outlet_release(scene, **params) -> list[Event]:
    """TRN-P07: a rebounder's teammate moves to the outlet (sideline or ball-ward) and arrives in time."""
    p = _prm("outlet_release", params)
    bx, by, _ = _ball_filled(scene)
    passes = _passes(scene)
    out = []
    for ps in _possessions(scene):
        if ps["start_type"] != "dreb":
            continue
        t_dreb, a = ps["t0"], ps["t_rel"]
        b = min(scene.n - 1, t_dreb + frames(p["arrive_s"]))
        for o in scene.offense:
            if o == ps["gainer"]:
                continue
            k = scene.k(o)
            vx, vy, sg = _wvel(scene, o, VS)
            lat = np.sign(k.x) * vx
            dxb, dyb = bx - k.x, by - k.y
            db = np.hypot(dxb, dyb)
            vball = (vx * dxb + vy * dyb) / np.where(db > 0, db, np.nan)
            mv_ = np.maximum(np.nan_to_num(lat, nan=-9), np.nan_to_num(vball, nan=-9))
            mask = mv_ >= p["move_mps"]
            mask[:a] = False
            mask[b + 1 :] = False
            for s, e in _runs_of(mask, _dwell(MIN_DUR["outlet_release"])):
                arr = next(
                    (
                        t
                        for t in range(s, b + 1)
                        if _in_spot("outlet_ballside", k.x[t], k.y[t])
                        or _in_spot("outlet_middle", k.x[t], k.y[t])
                        or (abs(k.x[t]) >= p["arrive_abs_x_m"] and k.y[t] > HALF_Y)
                    ),
                    None,
                )
                if arr is None:
                    continue
                spot = (
                    "outlet_ballside"
                    if _in_spot("outlet_ballside", k.x[arr], k.y[arr])
                    else ("outlet_middle" if _in_spot("outlet_middle", k.x[arr], k.y[arr]) else "wide")
                )
                caught = any(
                    q["passer"] == ps["gainer"] and q["receiver"] == o and q["t_rel"] >= t_dreb for q in passes
                )
                conf = window_conf(p_above(mv_, p["move_mps"], sg), s, e) * _qobj(scene, [o], s, s, e)
                gx = ps["gain_xy"][0]
                out.append(
                    _ev(
                        "outlet_release",
                        {"receiver": o, "rebounder": ps["gainer"]},
                        s,
                        s,
                        arr,
                        conf,
                        spot=spot,
                        arrive_rel_dreb_s=(arr - t_dreb) * DT,
                        ballside=bool(np.sign(k.x[arr]) == np.sign(gx)),
                        caught=caught,
                        poss_t0=t_dreb,
                    )
                )
                break
    return out


def detect_push(scene, **params) -> list[Event]:
    """TRN-P08: handler advances with vbar(1.0) >= 4.0 m/s for >= 1.5 s while holding the ball."""
    p = _prm("push", params)
    runs = _hold_runs(scene)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        if ps["t_cross_half"] is None or (ps["t_cross_half"] - t0) * DT > p["max_cross_s"]:
            continue
        stop = ps["t_three_zone"] if ps["t_three_zone"] is not None else scene.n - 1
        for oid, a, e in runs:
            if _team(scene, oid) != "O" or e < t0 or a > stop:
                continue
            v10, sg = _vbar(scene, oid, VL)
            mask = np.zeros(scene.n, dtype=bool)
            lo, hi = max(a, t0), min(e, stop)
            mask[lo : hi + 1] = np.nan_to_num(v10[lo : hi + 1], nan=0) >= p["min_speed_mps"]
            for s, f in _runs_of(mask, _dwell(MIN_DUR["push"])):
                k = scene.k(oid)
                high = bool(
                    _runs_of(mask & (np.nan_to_num(v10, nan=0) >= p["high_speed_mps"]), _dwell(p["high_dur_s"]))
                )
                c = ps["t_cross_half"]
                mode = "pass" if _holders(scene)[c] is None else "dribble"
                conf = window_conf(p_above(v10, p["min_speed_mps"], sg), s, f) * _qobj(scene, [oid, "ball"], s, s, f)
                out.append(
                    _ev(
                        "push",
                        {"handler": oid},
                        s,
                        s,
                        f,
                        conf,
                        mean_vbar10=float(np.nanmean(v10[s : f + 1])),
                        peak_vbar10=float(np.nanmax(v10[s : f + 1])),
                        high_push=high,
                        backcourt_share=float(np.mean(k.y[s : f + 1] > HALF_Y)),
                        cross_rel_t0_s=(c - t0) * DT,
                        advance_mode=mode,
                        poss_t0=t0,
                    )
                )
                break
    return out


def detect_diagonal_dribble(scene, **params) -> list[Event]:
    """TRN-P09: dribble segments >= 10 m whose chord is 20-45 deg off the long axis."""
    p = _prm("diagonal_dribble", params)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        hi = min(scene.n - 1, (ps["t_cross_half"] if ps["t_cross_half"] is not None else scene.n - 1) + frames(2.0))
        for oid, a, e in _hold_runs(scene):
            if _team(scene, oid) != "O" or e < t0 or a > hi:
                continue
            k = scene.k(oid)
            mask = np.zeros(scene.n, dtype=bool)
            lo, up = max(a, t0), min(e, hi)
            mask[lo : up + 1] = np.nan_to_num(k.speed[lo : up + 1], nan=0) >= p["min_speed_mps"]
            for s, f in _runs_of(mask, _dwell(MIN_DUR["diagonal_dribble"])):
                dx, dy = k.x[f] - k.x[s], k.y[f] - k.y[s]
                L = math.hypot(dx, dy)
                if L < p["min_len_m"]:
                    continue
                ang = math.degrees(math.atan2(abs(dx), abs(dy)))
                if not (p["min_deg"] <= ang <= p["max_deg"]):
                    continue
                sa = math.degrees(K_CAL * math.sqrt(k.var_p[s] + k.var_p[f]) / L)
                conf = (
                    window_conf(p_above(k.speed, p["min_speed_mps"], k.sigma_speed), s, f)
                    * float(phi(min(ang - p["min_deg"], p["max_deg"] - ang) / max(sa, 0.5)))
                    * _qobj(scene, [oid], s, s, f)
                )
                out.append(
                    _ev(
                        "diagonal_dribble",
                        {"handler": oid},
                        s,
                        s,
                        f,
                        conf,
                        angle_deg=ang,
                        length_m=L,
                        cls="diagonal",
                        poss_t0=t0,
                    )
                )
    return out


def detect_pull_back(scene, **params) -> list[Event]:
    """TRN-P10: ball pulled back out after reaching the scoring zone, or a held reset beyond 7.5 m."""
    p = _prm("pull_back", params)
    bx, by, _ = _ball_filled(scene)
    hd = _handler(scene)
    trans = {ev.attrs["poss_t0"]: ev for ev in _memo(scene, "transition", lambda: detect_transition_phase(scene))}
    adv = _memo(scene, "numbers", lambda: detect_numbers_advantage(scene))
    out = []
    for ps in _possessions(scene):
        tsz = ps["t_scoring_zone"]
        if tsz is None:
            continue
        tr = trans.get(ps["t0"])
        end = min(scene.n - 1, (tr.end if tr is not None else ps["t0"] + frames(8.0)) + frames(p["after_phase_s"]))
        hi = min(end, tsz + frames(p["rise_window_s"]))
        run_min = np.minimum.accumulate(by[tsz : hi + 1])
        rise = by[tsz : hi + 1] - run_min
        ia = np.flatnonzero(rise >= p["rise_m"])
        cand = []
        if len(ia):
            cand.append((tsz + int(ia[0]), "a"))
        for t in range(tsz, end + 1):  # (b) held reset
            hh = hd[t]
            if hh is None:
                continue
            k = scene.k(hh)
            v05 = _vbar(scene, hh, VS)[0]
            u = t
            while (
                u <= end and hd[u] == hh and math.hypot(k.x[u], k.y[u]) >= p["hold_r_m"] and v05[u] < p["hold_vbar_mps"]
            ):
                u += 1
            if (u - t) >= _dwell(p["hold_s"]):
                cand.append((t, "b"))
                break
        if not cand:
            continue
        t_pull, trig = min(cand)
        s = _first_shot_after(scene, tsz)
        if s is not None and s["t_rel"] <= t_pull:
            continue
        hh = hd[t_pull]
        if trig == "a":
            sdy = math.sqrt(2) * float(_ball_sig(scene)[t_pull])
            conf = float(np.max(phi((rise - p["rise_m"]) / max(sdy, 0.05))))
        else:
            v05, sg = _vbar(scene, hh, VS)
            conf = window_conf(p_below(v05, p["hold_vbar_mps"], sg), t_pull, min(end, t_pull + frames(p["hold_s"])))
        conf *= _qobj(scene, [hh or ps["gainer"], "ball"], t_pull, t_pull, min(scene.n - 1, t_pull + frames(0.5)))
        with_adv = any(ev.start <= t_pull <= ev.end for ev in adv if ev.attrs["poss_t0"] == ps["t0"])
        out.append(
            _ev(
                "pull_back",
                {"handler": hh},
                t_pull,
                tsz,
                t_pull,
                conf,
                trigger=trig,
                pull_rel_t0_s=(t_pull - ps["t0"]) * DT,
                with_advantage=with_adv,
                poss_t0=ps["t0"],
            )
        )
    return out


def detect_retreat(scene, **params) -> list[Event]:
    """TRN-P11: losing-team player runs back toward the rim he defends (radial window speed >= 2.0 m/s)."""
    p = _prm("retreat", params)
    bx, by, _ = _ball_filled(scene)
    out = []
    for ps in _possessions(scene):
        anchor = ps["t_rel"] if ps["t_rel"] is not None else ps["t0"]
        hi = min(scene.n - 1, anchor + frames(p["window_s"]))
        for d in scene.defense:
            vb, sg = _v_back(scene, d)
            ent = np.nan_to_num(vb, nan=-9) >= p["onset_mps"]
            sty = np.nan_to_num(vb, nan=-9) >= p["exit_mps"]
            ent[:anchor] = False
            ent[hi + 1 :] = False
            ivs = mv.hysteresis(ent, sty, MIN_DUR["retreat"], frames(p["exit_dwell_s"]))
            if not ivs:
                continue
            s, e = ivs[0]
            k = scene.k(d)
            c = ps["t_cross_half"]
            sb = min(scene.n - 1, s + frames(0.5))
            conf = window_conf(p_above(vb, p["onset_mps"], sg), s, sb) * _qobj(scene, [d], s, s, e)
            out.append(
                _ev(
                    "retreat",
                    {"player": d},
                    s,
                    s,
                    e,
                    conf,
                    reaction_delay_s=(s - anchor) * DT,
                    late_retreat=(s - ps["t0"]) * DT > p["late_s"],
                    peak_v_back=float(np.nanmax(vb[s : e + 1])),
                    behind_ball_at_cross=None if c is None else bool(k.y[c] < by[c]),
                    anchor=anchor,
                    poss_t0=ps["t0"],
                )
            )
    return out


def _far_shots(scene):
    return [s for s in _shots(scene) if s["team"] == "D" and s["rim"] == "far" and not s["same_attempt"]]


def detect_shot_rebound_decision(scene, **params) -> list[Event]:
    """TRN-P12: crash / retreat / hold / watch of each shooting-team player between release and rebound."""
    p = _prm("shot_rebound_decision", params)
    runs = _hold_runs(scene)
    out = []
    for s in _far_shots(scene):
        a = s["t_rel"]
        nxt = runs[s["next_run"]][1] if s["next_run"] is not None else None
        b = nxt if nxt is not None and (nxt - s["t_rim"]) * DT <= 3.0 else min(scene.n - 1, s["t_rim"] + frames(1.0))
        if (b - a) * DT < 0.5:
            continue
        rows = []
        for d in scene.defense:
            if d == s["shooter"]:
                continue
            k = scene.k(d)
            rf = _r_far(k)
            r0 = float(np.nanmean(rf[max(0, a - 2) : a + 3]))
            dr = float(rf[b] - r0)
            L = float(np.nansum(np.hypot(np.diff(k.x[a : b + 1]), np.diff(k.y[a : b + 1]))))
            sg = math.sqrt(2) * float(np.nanmedian(_sig_p(k)[a : b + 1]))
            if r0 <= p["pi_r_m"]:
                cls, pr = "PI", phi((p["pi_r_m"] - r0) / sg)
            elif r0 >= p["po_r_m"]:
                cls, pr = "PO", phi((r0 - p["po_r_m"]) / sg)
            elif dr <= -p["delta_r_m"]:
                cls, pr = "crash", phi((-dr - p["delta_r_m"]) / sg)
            elif dr >= p["delta_r_m"]:
                cls, pr = "retreat", phi((dr - p["delta_r_m"]) / sg)
            else:
                cls, pr = "hold", phi((p["delta_r_m"] - abs(dr)) / sg)
                if L < p["watch_len_m"]:
                    cls = "watch"
            rows.append((d, cls, float(pr), dr, L))
        ci = sum(c in ("PI", "crash") for _, c, *_ in rows)
        ri = sum(c in ("PO", "retreat") for _, c, *_ in rows)
        for d, cls, pr, dr, L in rows:
            out.append(
                _ev(
                    "shot_rebound_decision",
                    {"player": d, "shooter": s["shooter"]},
                    a,
                    a,
                    b,
                    pr * _qobj(scene, [d], a, a, b),
                    cls=cls,
                    delta_r=dr,
                    path_m=L,
                    CI=ci,
                    RI=ri,
                )
            )
    return out


def detect_safety(scene, **params) -> list[Event]:
    """TRN-P13: shooting-team player back and moving toward his own rim at t_rel + 1.0 s."""
    p = _prm("safety", params)
    out = []
    for s in _far_shots(scene):
        t = s["t_rel"] + frames(p["at_s"])
        if t >= scene.n:
            continue
        a, b = max(0, t - 5), min(scene.n - 1, t + 5)
        for d in scene.defense:
            k = scene.k(d)
            rf = _r_far(k)
            vb, sg = _v_back(scene, d)
            if rf[t] > p["safety_r_m"] and vb[t] >= p["v_mps"]:
                var = "repo"
                pr = np.minimum(p_above(rf, p["safety_r_m"], _sig_p(k)), p_above(vb, p["v_mps"], sg))
            elif rf[t] >= THREE_R and (vb[t] >= p["v_mps"] or k.y[t] <= FAR_RIM_Y - p["wide_dy_m"]):
                var = "wide"
                pr = p_above(rf, THREE_R, _sig_p(k))
            else:
                continue
            out.append(
                _ev(
                    "safety",
                    {"player": d, "shooter": s["shooter"]},
                    t,
                    a,
                    b,
                    window_conf(pr, a, b) * _qobj(scene, [d], t, a, b),
                    variant=var,
                    shooter_back=d == s["shooter"],
                    t_rel=s["t_rel"],
                )
            )
    return out


def detect_protect_rim(scene, **params) -> list[Event]:
    """TRN-P14: first defender to reach r <= 1.5 m at the rim he defends after the change."""
    p = _prm("protect_rim", params)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        hi = min(scene.n - 1, t0 + frames(p["window_s"]))
        best = None
        for d in scene.defense:
            k = scene.k(d)
            r = np.hypot(k.x, k.y)
            if r[t0] <= p["from_r_m"]:
                cand = (t0, d, True)
            else:
                idx = np.flatnonzero(r[t0 : hi + 1] <= p["arrive_r_m"])
                if not len(idx):
                    continue
                cand = (t0 + int(idx[0]), d, False)
            if best is None or cand[0] < best[0]:
                best = cand
        if best is None:
            continue
        f, d, already = best
        k = scene.k(d)
        r = np.hypot(k.x, k.y)
        fb = min(scene.n - 1, f + frames(0.2))
        thr = p["from_r_m"] if already else p["arrive_r_m"]
        conf = window_conf(p_below(r, thr, _sig_p(k)), f, fb) * _qobj(scene, [d], f, f, fb)
        f25 = np.flatnonzero(r[t0 : hi + 1] <= 2.5)
        c = ps["t_cross_half"]
        out.append(
            _ev(
                "protect_rim",
                {"defender": d},
                f,
                t0,
                fb,
                conf,
                rel_t0_s=(f - t0) * DT,
                already_back=already,
                before_cross=c is None or f <= c,
                flag_25=int(t0 + f25[0]) if len(f25) else None,
                poss_t0=t0,
            )
        )
    return out


def detect_inbounder_step_in(scene, **params) -> list[Event]:
    """TRN-P15: the thrower re-enters the court within 2.0 s of the release."""
    p = _prm("inbounder_step_in", params)
    runs = _hold_runs(scene)
    out = []
    for tw in _throw_ins(scene):
        o, rel = tw["last_thrower"], tw["t_release"]
        k = scene.k(o)
        din = _d_in(k.x, k.y)
        h = frames(0.25)
        hi = min(scene.n - 1 - h, rel + frames(p["window_s"]))
        f = None
        for t in range(rel, hi + 1):
            v_in = (din[min(scene.n - 1, t + h)] - din[max(0, t - h)]) / (2 * h * DT)
            if din[t] >= p["d_in_m"] and v_in >= p["v_in_mps"]:
                f = t
                break
        if f is None:
            continue
        ret = any(r[0] == o and rel < r[1] <= rel + frames(p["return_s"]) for r in runs)
        fb = min(scene.n - 1, f + frames(0.2))
        conf = window_conf(p_above(din, p["d_in_m"], _sig_p(k)), f, fb) * _qobj(scene, [o], f, f, fb)
        out.append(
            _ev(
                "inbounder_step_in",
                {"thrower": o},
                f,
                rel,
                fb,
                conf,
                step_in_rel_release_s=(f - rel) * DT,
                return_catch=ret,
            )
        )
    return out


def detect_run_endline(scene, **params) -> list[Event]:
    """TRN-P16: thrower moves >= 2.0 m along the far end line between disposal and release."""
    p = _prm("run_endline", params)
    out = []
    for tw in _throw_ins(scene):
        if tw["restart_type"] != "backcourt_endline":
            continue
        o, a, rel = tw["thrower"], tw["t_disposal"], tw["t_release"]
        if (rel - a) * DT < MIN_DUR["run_endline"] - 1e-9:
            continue
        k = scene.k(o)
        dx = float(k.x[rel] - k.x[a])
        sp = abs(dx) / ((rel - a) * DT)
        if abs(dx) < p["min_dx_m"] or sp < p["min_speed_mps"]:
            continue
        sdx = math.sqrt(2) * float(np.nanmedian(_sig_p(k)[a : rel + 1]))
        after = _made_before(scene, a)
        conf = float(phi((abs(dx) - p["min_dx_m"]) / sdx)) * _qobj(scene, [o], a, a, rel)
        out.append(
            _ev(
                "run_endline",
                {"thrower": o},
                a,
                a,
                rel,
                conf,
                delta_x=dx,
                mean_speed=sp,
                after_make=after,
                violation_candidate=not after,
                endline_relay=tw["relay"],
            )
        )
    return out


def _legs(k, a, b, move):
    """Movement legs: runs of smoothed speed >= move (gaps <= 2 frames bridged) with chord >= 0.5 m."""
    mask = np.zeros(len(k.x), dtype=bool)
    mask[a : b + 1] = np.nan_to_num(k.speed[a : b + 1], nan=0) >= move
    return [(s, e) for s, e in _runs_of(mask, 3, 2) if math.hypot(k.x[e] - k.x[s], k.y[e] - k.y[s]) >= 0.5]


def detect_inbound_get_open(scene, **params) -> list[Event]:
    """TRN-P17: receiver movement before the throw-in catch (V-cut, flash, basket cut, pop)."""
    p = _prm("inbound_get_open", params)
    out = []
    for tw in _throw_ins(scene):
        team = scene.offense if tw["team"] == "O" else scene.defense
        kt = scene.k(tw["thrower"])
        bxp = float(np.nanmean(kt.x[tw["t_disposal"] : tw["t_release"] + 1]))
        byp = float(np.nanmean(kt.y[tw["t_disposal"] : tw["t_release"] + 1]))
        a = max(0, tw["t_disposal"] - frames(p["pre_s"]))
        b = tw["t_first_touch"]
        for o in team:
            if o in (tw["thrower"], tw["last_thrower"]):
                continue
            k = scene.k(o)
            dball = np.hypot(k.x - bxp, k.y - byp)
            cls, margin = None, 0.0
            # V-cut: a direction reversal with the plant skipped (MP-13), out >= leg_m away, back >= leg_m toward
            rv = _plant(k, a, b, p["pre_post_s"], p["skip_s"], p["vcut_deg"], p["leg_min_disp_m"])
            if rv is not None:
                # plant = the turn point: farthest from the thrower around the reversal run (the run itself is
                # biased toward the longer leg)
                lo_, hi_ = max(a, rv[0] - frames(0.2)), min(scene.n - 1, rv[1] + frames(0.3))
                pl = lo_ + int(np.nanargmax(dball[lo_ : hi_ + 1]))
                lo, hi = max(0, pl - frames(1.0)), min(scene.n - 1, b + frames(0.3))
                out_m = dball[pl] - np.nanmin(dball[lo : pl + 1])
                back_m = dball[pl] - np.nanmin(dball[pl : hi + 1])
                peak = float(np.nanmax(k.speed[pl : hi + 1]))
                if out_m >= p["leg_m"] and back_m >= p["leg_m"] and peak >= p["vcut_speed_mps"]:
                    cls, margin = "v_cut", min(out_m, back_m) - p["leg_m"]
                    s, e = pl, b
            legs = [lg for lg in _legs(k, a, b, p["move_mps"]) if lg[0] < b]
            if cls is None and not legs:
                continue
            if cls is None:
                s, e = legs[-1]
            d_fin = dball[e] - dball[s]
            peak = float(np.nanmax(k.speed[s : e + 1]))
            r = np.hypot(k.x, k.y)
            if cls is None and d_fin <= -p["flash_m"] and peak >= p["flash_speed_mps"]:
                cls, margin = "flash", -d_fin - p["flash_m"]
            if cls is None and r[e] <= 2.0 and np.nanmax(k.v_r[s : e + 1]) >= 2.5:
                cls, margin = "basket_cut", 2.0 - r[e]
            if cls is None and r[e] - r[s] >= p["pop_m"]:
                cls, margin = "pop", r[e] - r[s] - p["pop_m"]
            if cls is None or (e - s) * DT < MIN_DUR["inbound_get_open"] - 1e-9:
                continue
            sg = math.sqrt(2) * float(np.nanmedian(_sig_p(k)[s : e + 1]))
            conf = (
                window_conf(p_above(k.speed, p["move_mps"], k.sigma_speed), s, e)
                * float(phi(margin / sg))
                * _qobj(scene, [o], s, s, e)
            )
            out.append(
                _ev(
                    "inbound_get_open",
                    {"player": o, "thrower": tw["thrower"]},
                    s,
                    s,
                    e,
                    conf,
                    cls=cls,
                    receives=tw["receiver"] == o,
                    t_disposal=tw["t_disposal"],
                )
            )
    return out


def _plant(k, a, b, L_s, skip_s, min_deg, min_disp):
    """Frames [q0, q1] of the last run of direction-reversal frames in [a, b] (MP-13): mean displacement over L
    before [q - skip - L, q - skip] vs after [q + skip, q + skip + L]; both legs >= min_disp m, turn >= min_deg."""
    L, sk = frames(L_s), frames(skip_s)
    best = None
    for q in range(max(a, sk + L), min(b, len(k.x) - 1 - sk - L) + 1):
        v1 = np.array([k.x[q - sk] - k.x[q - sk - L], k.y[q - sk] - k.y[q - sk - L]])
        v2 = np.array([k.x[q + sk + L] - k.x[q + sk], k.y[q + sk + L] - k.y[q + sk]])
        n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
        if not (n1 >= min_disp and n2 >= min_disp):
            continue
        ang = math.degrees(math.acos(np.clip(v1 @ v2 / (n1 * n2), -1.0, 1.0)))
        if ang >= min_deg:
            if best is not None and q == best[1] + 1:
                best[1] = q  # extend the current run of reversal frames
            elif best is None or q > best[1] + 1:
                best = [q, q]  # keep the LAST run before the catch
    return None if best is None else (best[0], best[1])


def _ft_releases(scene):
    """FT release proxies: a shot at the origin rim by a stationary holder standing in ft_shooter."""

    def calc():
        out = []
        for s in _shots(scene):
            if s["rim"] != "near":
                continue
            k = scene.k(s["shooter"])
            t = s["t_rel"]
            if not _in_spot("ft_shooter", k.x[t], k.y[t]):
                continue
            a = max(0, t - frames(0.5))
            if np.mean(k.stationary_s2[a : t + 1] < CHI2) < 0.6:
                continue
            lane = [
                o
                for o in scene.players()
                if any(_in_spot(f"ft_lane_space_{i}", scene.k(o).x[t], scene.k(o).y[t]) for i in (1, 2, 3))
            ]
            if len(lane) < 2:
                continue
            out.append(dict(t_ft=t, t_rim=s["t_rim"], shooter=s["shooter"], team=s["team"]))
        return out

    return _memo(scene, "ft", calc)


def _mean_pos(k, a, b):
    return float(np.nanmean(k.x[a : b + 1])), float(np.nanmean(k.y[a : b + 1]))


def detect_ft_lane_entry(scene, **params) -> list[Event]:
    """TRN-P18: lane occupants step toward the lane at the FT release; early-entry candidates."""
    p = _prm("ft_lane_entry", params)
    out = []
    for ft in _ft_releases(scene):
        t = ft["t_ft"]
        ra, rb = max(0, t - frames(p["ref_from_s"])), max(0, t - frames(p["ref_to_s"]))
        for o in scene.players():
            k = scene.k(o)
            x0, y0 = _mean_pos(k, ra, rb)
            space = next((i for i in (1, 2, 3) if _in_spot(f"ft_lane_space_{i}", x0, y0)), None)
            if space is None:
                continue
            move = abs(x0) - np.abs(k.x)
            lo, hi = max(0, t - frames(0.5)), min(scene.n - 1, t + frames(p["window_s"]))
            mask = np.zeros(scene.n, dtype=bool)
            mask[lo : hi + 1] = move[lo : hi + 1] >= p["enter_m"]
            rr = _runs_of(mask, _dwell(p["hold_s"]))
            if not rr:
                continue
            f = rr[0][0]
            # fix TRN-T17: the reference is a window MEAN (n_eff = window / corr_s looks), the current position a
            # single frame, so sigma_move = sqrt(sigma_ref^2 / n_eff + sigma_t^2) instead of sqrt(2) sigma
            sp = _sig_p(k)
            n_eff = max(1.0, (rb - ra) * DT / p["corr_s"])
            s_ref = float(np.nanmedian(sp[ra : rb + 1]))
            sg = np.sqrt(s_ref**2 / n_eff + sp**2)
            thr_early = max(p["early_m"], 3 * float(np.nanmedian(sg[lo : t + 1])))
            # the entry must START before the release; its size is read over the entry's hold window, because the
            # smoothed track trails a 0.4 s step by about 0.2 m (V0, sigma_p 0.1), so a step that ends at the
            # release reads only about 0.5 m by then
            early = bool(f < t and np.sum(move[f : f + _dwell(p["hold_s"]) + frames(p["ref_to_s"])] >= thr_early) >= 2)
            fb = min(scene.n - 1, f + frames(0.2))
            conf = window_conf(p_above(move, p["enter_m"], sg), f, fb) * _qobj(scene, [o], f, f, fb)
            crash = (
                _team(scene, o) == ft["team"]
                and np.nanmin(np.hypot(k.x, k.y)[ft["t_rim"] : min(scene.n, ft["t_rim"] + frames(1.0) + 1)]) <= 1.5
            )
            out.append(
                _ev(
                    "ft_lane_entry",
                    {"player": o, "shooter": ft["shooter"]},
                    f,
                    f,
                    fb,
                    conf,
                    space=space,
                    entry_rel_release_s=(f - t) * DT,
                    early_entry_candidate=early,
                    ft_crash=bool(crash),
                    t_ft=t,
                )
            )
    return out


def detect_ft_release_runner(scene, **params) -> list[Event]:
    """TRN-P19: a player outside the lane runs away from the FT rim at the release (leak or safety)."""
    p = _prm("ft_release_runner", params)
    out = []
    for ft in _ft_releases(scene):
        t = ft["t_ft"]
        for o in scene.players():
            k = scene.k(o)
            x0, y0 = _mean_pos(k, max(0, t - frames(0.5)), t)
            if not (
                _in_spot("ft_leak_out", x0, y0)
                or _in_spot("ft_perimeter_top", x0, y0)
                or _in_spot("ft_perimeter_wing", x0, y0)
            ):
                continue
            vx, vy, sg = _wvel(scene, o, VS)
            ent = np.nan_to_num(vy, nan=-9) >= p["run_vy_mps"]
            ent[: max(0, t - frames(p["pre_s"]))] = False
            ent[min(scene.n, ft["t_rim"] + frames(p["post_s"]) + 1) :] = False
            ivs = mv.hysteresis(
                ent, np.nan_to_num(vy, nan=-9) >= p["run_vy_mps"] - 1.0, MIN_DUR["ft_release_runner"], frames(0.3)
            )
            if not ivs:
                continue
            s, e = ivs[0]
            sb = min(scene.n - 1, s + frames(0.5))
            role = "ft_safety_retreat" if _team(scene, o) == ft["team"] else "ft_leak"
            conf = window_conf(p_above(vy, p["run_vy_mps"], sg), s, sb) * _qobj(scene, [o], s, s, e)
            out.append(
                _ev(
                    "ft_release_runner",
                    {"runner": o, "shooter": ft["shooter"]},
                    s,
                    s,
                    e,
                    conf,
                    role=role,
                    onset_rel_release_s=(s - t) * DT,
                    t_ft=t,
                )
            )
    return out


def detect_jump_ball_release(scene, **params) -> list[Event]:
    """TRN-P20 (needs_data): t_toss and t_tap need ball height."""
    return []


def detect_hold_for_one(scene, **params) -> list[Event]:
    """TRN-P21 (needs_data): the hold label needs the game and shot clock gate."""
    return []


def _press_intervals(scene):
    return _memo(scene, "press", lambda: detect_press_active(scene))


def detect_press_flash_middle(scene, **params) -> list[Event]:
    """TRN-P22: during press_active a receiver enters pb_middle closing on the ball."""
    p = _prm("press_flash_middle", params)
    bx, by, _ = _ball_filled(scene)
    runs = _hold_runs(scene)
    out = []
    for pr in _press_intervals(scene):
        a, b = pr.start, pr.end
        for o in scene.offense:
            k = scene.k(o)
            vx, vy, sg = _wvel(scene, o, VS)
            dxb, dyb = bx - k.x, by - k.y
            db = np.hypot(dxb, dyb)
            close = (vx * dxb + vy * dyb) / np.where(db > 0, db, np.nan)
            inm = np.array([_in_spot("pb_middle", k.x[t], k.y[t]) for t in range(scene.n)])
            appr_all = _runs_of(np.nan_to_num(close, nan=0) >= p["close_mps"], _dwell(MIN_DUR["press_flash_middle"]))
            for ent, _ in _runs_of(
                inm, _dwell(MIN_DUR["press_flash_middle"])
            ):  # entries that stay >= 0.3 s (edge flicker is not an entry)
                if not (max(a, 1) <= ent <= b):
                    continue
                appr = [ab for ab in appr_all if ab[0] <= ent + frames(0.3) and ab[1] >= ent - frames(0.5)]
                if not appr:
                    continue
                s, e = appr[0]
                catch = any(
                    r[0] == o and ent <= r[1] and r[1] - ent <= frames(p["catch_s"]) and inm[r[1]] for r in runs
                )
                conf = window_conf(p_above(close, p["close_mps"], sg), s, e) * _qobj(scene, [o], ent, s, e)
                out.append(_ev("press_flash_middle", {"player": o}, ent, s, e, conf, middle_catch=catch))
                break
    return out


def detect_sideline_release(scene, **params) -> list[Event]:
    """TRN-P23: attacker in pb_sideline_halfcourt at the first touch of a pressed backcourt inbound."""
    p = _prm("sideline_release", params)
    out = []
    for tw in _throw_ins(scene):
        if tw["restart_type"] != "backcourt_endline" or tw["team"] != "O":
            continue
        t = tw["t_first_touch"]
        if sum(scene.k(d).y[t] > HALF_Y for d in scene.defense) < 2:
            continue
        for o in scene.offense:
            if o == tw["thrower"]:
                continue
            k = scene.k(o)
            if not _in_spot("pb_sideline_halfcourt", k.x[t], k.y[t]):
                continue
            margin = min(abs(k.x[t]) - p["zone_min_abs_x"], SIDE_X - abs(k.x[t]) + 0.3, k.y[t] - 11.0, 16.0 - k.y[t])
            conf = float(phi(margin / _sig_p(k)[t])) * _qobj(scene, [o], t, t, t)
            out.append(
                _ev(
                    "sideline_release",
                    {"player": o},
                    t,
                    t,
                    t,
                    conf,
                    type="sideline_receiver",
                    side=int(np.sign(k.x[t])),
                )
            )
    return out


def detect_press_safety(scene, **params) -> list[Event]:
    """TRN-P24: attacker staying behind the ball (and near it) through a press interval."""
    p = _prm("press_safety", params)
    bx, by, _ = _ball_filled(scene)
    h = _holders(scene)
    out = []
    tws = _throw_ins(scene)
    for pr in _press_intervals(scene):
        a, b = pr.start, pr.end
        for tw in tws:  # nobody can be behind an out-of-bounds thrower: start at the inbound's first touch
            if a <= tw["t_disposal"] <= b:
                a = max(a, tw["t_first_touch"])
        if (b - a) * DT < MIN_DUR["press_safety"]:
            continue
        best = None
        for o in scene.offense:
            k = scene.k(o)
            sl = slice(a, b + 1)
            ok = (k.y[sl] > by[sl] + p["behind_m"]) & (np.hypot(k.x[sl] - bx[sl], k.y[sl] - by[sl]) <= p["near_m"])
            ok &= np.array([x != o for x in h[sl]])
            share = float(np.mean(ok))
            if best is None or share > best[1]:
                best = (o, share)
        if best is None or best[1] < p["min_share"]:
            continue
        o, share = best
        k = scene.k(o)
        sr = np.hypot(_sig_p(k), _ball_sig(scene))
        conf = window_conf(p_above(k.y - by, p["behind_m"], sr), a, b) * _qobj(scene, [o], a, a, b)
        out.append(_ev("press_safety", {"player": o}, a, a, b, conf, share=share))
    return out


def detect_build_wall(scene, **params) -> list[Event]:
    """TRN-P25: >= 3 defenders loaded between the ball and the rim during transition."""
    p = _prm("build_wall", params)
    bx, by, _ = _ball_filled(scene)
    trans = _memo(scene, "transition", lambda: detect_transition_phase(scene))
    out = []
    for tr in trans:
        a, b = tr.start, tr.end
        mask = np.zeros(scene.n, dtype=bool)
        prob = np.zeros(scene.n)
        for t in range(a, b + 1):
            if by[t] <= THREE_R:
                continue
            ps_ = []
            cnt = 0
            for d in scene.defense:
                k = scene.k(d)
                m = min(k.y[t] - (by[t] - p["depth_m"]), (by[t] - 1.0) - k.y[t], p["lateral_m"] - abs(k.x[t] - bx[t]))
                cnt += m >= 0
                ps_.append(phi(m / _sig_p(k)[t]))
            mask[t] = cnt >= p["min_defenders"]
            prob[t] = _pb_count(np.array(ps_), p["min_defenders"])
        for s, e in _runs_of(mask, _dwell(MIN_DUR["build_wall"])):
            ids = [
                d
                for d in scene.defense
                if (by[s] - p["depth_m"]) <= scene.k(d).y[s] <= by[s] - 1.0
                and abs(scene.k(d).x[s] - bx[s]) <= p["lateral_m"]
            ]
            conf = window_conf(prob, s, e) * _qobj(scene, ["ball"], s, s, _last_ball(scene, s, e))
            out.append(_ev("build_wall", {"defenders": tuple(ids)}, s, s, e, conf, poss_t0=tr.attrs["poss_t0"]))
            break
    return out


def detect_sink_to_paint(scene, **params) -> list[Event]:
    """TRN-P26: >= 2 defenders in the lane before the ball reaches the arc during transition."""
    p = _prm("sink_to_paint", params)
    trans = _memo(scene, "transition", lambda: detect_transition_phase(scene))
    poss = {ps["t0"]: ps for ps in _possessions(scene)}
    out = []
    for tr in trans:
        ps = poss[tr.attrs["poss_t0"]]
        a = tr.start
        b = min(tr.end, ps["t_three_zone"] if ps["t_three_zone"] is not None else tr.end)
        mask = np.zeros(scene.n, dtype=bool)
        prob = np.zeros(scene.n)
        for t in range(a, b + 1):
            ps_ = []
            for d in scene.defense:
                k = scene.k(d)
                m = min(LANE_X - abs(k.x[t]), FT_Y - k.y[t], k.y[t] - END_Y)
                ps_.append(phi(m / _sig_p(k)[t]))
            ps_ = np.array(ps_)
            mask[t] = np.sum(ps_ > 0.5) >= p["min_defenders"]
            prob[t] = _pb_count(ps_, p["min_defenders"])
        rr = _runs_of(mask, _dwell(MIN_DUR["sink_to_paint"]))
        if not rr:
            continue
        s, e = rr[0]
        ids = tuple(d for d in scene.defense if abs(scene.k(d).x[s]) < LANE_X and END_Y < scene.k(d).y[s] <= FT_Y)
        out.append(
            _ev(
                "sink_to_paint",
                {"defenders": ids},
                s,
                s,
                e,
                window_conf(prob, s, e) * _qobj(scene, list(ids), s, s, e),
                poss_t0=ps["t0"],
            )
        )
    return out


# --------------------------------------------------------------------------------------
# Actions
# --------------------------------------------------------------------------------------
def _hold_p(scene, oid, t, t_end=None, dur=0.2):
    """P(the ball is in oid's control) over [t, t + dur], cut at the end of his hold (a one-touch pass is short)."""
    k = scene.k(oid)
    d = np.hypot(scene.ball.x - k.x, scene.ball.y - k.y)
    pr = p_below(d, _stay_r(), mv.sigma_dist(k, scene.ball))
    b = min(scene.n - 1, t + frames(dur), t_end if t_end is not None else scene.n - 1)
    return window_conf(pr, t, max(t, b))


def detect_outlet_pass(scene, **params) -> list[Event]:
    """TRN-A01: the rebounder's first pass (or a dribble-out) after a defensive rebound."""
    p = _prm("outlet_pass", params)
    runs = _hold_runs(scene)
    out = []
    for ps in _possessions(scene):
        if ps["start_type"] != "dreb":
            continue
        reb = ps["gainer"]
        i = ps["run"]
        _, a, e = runs[i]
        k = scene.k(reb)
        disp = float(math.hypot(k.x[e] - k.x[a], k.y[e] - k.y[a]))
        q = next((q for q in _passes(scene) if q["run"] == i), None)
        if disp >= p["dribble_m"]:
            conf = float(phi((disp - p["dribble_m"]) / (math.sqrt(2) * float(_sig_p(k)[a])))) * _qobj(
                scene, [reb], a, a, e
            )
            out.append(_ev("dribble_out", {"rebounder": reb}, a, a, e, conf, distance_m=disp, poss_t0=ps["t0"]))
            continue
        if q is None or not q["same_team"] or q["length"] < p["min_len_m"]:
            continue
        rc = q["receiver"]
        kr = scene.k(rc)
        xc, yc = float(kr.x[q["t_catch"]]), float(kr.y[q["t_catch"]])
        spot = next(
            (sid for sid in ("outlet_ballside", "outlet_middle", "long_outlet_zone") if _in_spot(sid, xc, yc)), "other"
        )
        delay = (q["t_rel"] - ps["t0"]) * DT
        c = ps["t_cross_half"]
        ctg = c is not None and _holders(scene)[c] == rc
        conf = _hold_p(scene, rc, q["t_catch"], q["catch_end"]) * _qobj(
            scene, [reb, rc, "ball"], q["t_rel"], q["t_rel"], q["t_catch"]
        )  # fix TRN-T16: q_obj includes the ball, as the YAML states
        out.append(
            _ev(
                "outlet_pass",
                {"rebounder": reb, "receiver": rc},
                q["t_rel"],
                q["t_rel"],
                q["t_catch"],
                conf,
                delay_s=delay,
                quick=delay <= p["quick_s"],
                length_m=q["length"],
                spot=spot,
                long_len15=q["length"] >= p["long_len_m"],
                ballside=bool(np.sign(xc) == np.sign(ps["gain_xy"][0])),
                outlet_height_m=FAR_END_Y - yc,
                ctg_compatible=bool(ctg),
                poss_t0=ps["t0"],
            )
        )
    return out


def detect_hit_ahead(scene, **params) -> list[Event]:
    """TRN-A02: forward pass of >= 8 m released before (or <= 1.5 s after) the passer crosses half court."""
    p = _prm("hit_ahead", params)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        hi = min(scene.n - 1, t0 + frames(p["window_s"]))
        for q in _passes(scene):
            if not q["same_team"] or _team(scene, q["passer"]) != "O" or not (t0 <= q["t_rel"] <= hi):
                continue
            dy = q["y1"] - q["y0"]
            if dy > p["max_dy_m"]:
                continue
            kp = scene.k(q["passer"])
            c = _first_cross(scene, q["passer"], t0, scene.n - 1)
            if c is not None and (q["t_rel"] - c) * DT > p["after_cross_s"]:
                continue
            sdy = math.sqrt(2) * float(_ball_sig(scene)[q["t_rel"]])
            conf = (
                float(phi((p["max_dy_m"] - dy) / sdy))
                * _hold_p(scene, q["receiver"], q["t_catch"], q["catch_end"])
                * _qobj(scene, [q["passer"], q["receiver"]], q["t_rel"], q["t_rel"], q["t_catch"])
            )
            out.append(
                _ev(
                    "hit_ahead",
                    {"passer": q["passer"], "receiver": q["receiver"]},
                    q["t_rel"],
                    q["t_rel"],
                    q["t_catch"],
                    conf,
                    delta_y=float(dy),
                    length_m=q["length"],
                    passed_before_timeline=bool(kp.y[q["t_rel"]] > HALF_Y),
                    poss_t0=t0,
                )
            )
    return out


def _roles(scene):
    """Possession-indexed transition roles from trailers and rim runs (for drag / pitch-back gating)."""

    def calc():
        roles = {}
        for ps, o, rank, c, m, _tie in _trailers(scene):
            roles.setdefault(ps["t0"], {})[o] = f"trailer_{rank}"
        # loop 1 (TRN-T07): trailer ranks now count the handler, so a big who crosses 3rd, just ahead of the
        # handler, has no trailer rank; he is still a late (non-wing) runner who can set the drag ('late_runner':
        # 3rd-5th across, not the handler at his crossing)
        h = _holders(scene)
        for ps in _possessions(scene):
            t0 = ps["t0"]
            a = max(0, t0 - frames(1.5))
            b = min(scene.n - 1, t0 + frames(PARAMS["trailer"]["window_s"]))
            cr = sorted((c, o) for o in scene.offense if (c := _first_cross(scene, o, a, b)) is not None)
            for c, o in cr[2:]:
                if not any(x == o for x in h[max(0, c - 2) : c + 3]):
                    roles.setdefault(t0, {}).setdefault(o, "late_runner")
        for ev in detect_rim_run(scene):
            roles.setdefault(ev.attrs["poss_t0"], {}).setdefault(ev.actors["runner"], "rim_runner")
        return roles

    return _memo(scene, "roles", calc)


def _drags(scene, **over):
    p = _prm("drag_screen", over)

    def calc():
        hd = _handler(scene)
        trans = {ev.attrs["poss_t0"]: ev for ev in _memo(scene, "transition", lambda: detect_transition_phase(scene))}
        roles = _roles(scene)
        out = []
        for ps in _possessions(scene):
            t0 = ps["t0"]
            tr = trans.get(t0)
            te = tr.end if tr is not None else t0 + frames(8.0)
            hi = min(scene.n - 6, t0 + frames(p["window_s"]), te + frames(p["after_phase_s"]))
            done = set()
            for t in range(t0, hi + 1):
                h = hd[t]
                if h is None:
                    continue
                kh = scene.k(h)
                rh = math.hypot(kh.x[t], kh.y[t])
                if rh <= p["handler_r_m"] or kh.y[t] > HALF_Y + 2.0:
                    continue
                for s in scene.offense:
                    if s == h or (h, s) in done:
                        continue
                    ks = scene.k(s)
                    if math.hypot(ks.x[t] - kh.x[t], ks.y[t] - kh.y[t]) > p["contact_m"]:
                        continue
                    fw = slice(t, t + frames(0.3) + 1)  # the screener stays set for 0.3 s from contact
                    if np.mean(ks.stationary_s2[fw] < CHI2) < 0.6 or np.any(
                        mv.dist(kh, ks)[fw] > p["contact_m"] + 0.25
                    ):
                        continue
                    vy = _wvel(scene, s, VS)[1]
                    if np.nanmin(vy[max(0, t - frames(p["run_back_s"])) : t + 1]) > p["run_vy_mps"]:
                        continue
                    role = roles.get(t0, {}).get(s)
                    if role is None:
                        continue
                    done.add((h, s))
                    r_s = np.hypot(ks.x, ks.y)
                    ah = min(scene.n - 1, t + frames(p["action_s"]))
                    if (
                        np.nanmin(r_s[t : ah + 1]) < p["roll_r_m"]
                        or r_s[t] - np.nanmin(r_s[t : ah + 1]) >= p["roll_dr_m"]
                    ):
                        act = "roll"
                    elif r_s[ah] >= THREE_R and r_s[ah] > r_s[t]:
                        act = "pop"
                    else:
                        act = "none"
                    d = mv.dist(kh, ks)
                    tb = min(scene.n - 1, t + frames(0.3))
                    conf = window_conf(p_below(d, p["contact_m"], mv.sigma_dist(kh, ks)), t, tb) * _qobj(
                        scene, [h, s], t, t, tb
                    )
                    out.append(
                        _ev(
                            "drag_screen",
                            {"handler": h, "screener": s},
                            t,
                            t,
                            ah,
                            conf,
                            screener_role=role,
                            contact_r=float(math.hypot(ks.x[t], ks.y[t])),
                            drag_at_arc=bool(6.0 <= r_s[t] <= 8.5),
                            screener_action=act,
                            side=int(np.sign(kh.x[t])),
                            poss_t0=t0,
                            moving_screen_candidate=bool(ks.speed[t] > 1.0),
                        )
                    )
        return out

    if over:
        return calc()
    return _memo(scene, "drags", calc)


def detect_drag_screen(scene, **params) -> list[Event]:
    """TRN-A03: transition ball screen by a trailer or returning rim runner on a handler beyond 7.5 m."""
    return list(_drags(scene, **params))


def detect_double_drag(scene, **params) -> list[Event]:
    """TRN-A04: two drag screens on the same handler <= 1.5 s apart with screeners 0.5-1.75 m apart."""
    p = _prm("double_drag", params)
    ds = sorted(_drags(scene), key=lambda e: e.t0)
    out = []
    for e1, e2 in itertools.combinations(ds, 2):
        if e1.actors["handler"] != e2.actors["handler"] or (e2.t0 - e1.t0) * DT > p["gap_s"]:
            continue
        k1, k2 = scene.k(e1.actors["screener"]), scene.k(e2.actors["screener"])
        t = e2.t0  # both screeners are set at the second contact
        sep = float(math.hypot(k1.x[t] - k2.x[t], k1.y[t] - k2.y[t]))
        if not (p["min_sep_m"] < sep <= p["max_sep_m"]):
            continue
        sd = float(mv.sigma_dist(k1, k2)[t])
        conf = min(e1.conf, e2.conf) * float(phi((p["max_sep_m"] - sep) / sd))
        r2 = np.hypot(k2.x, k2.y)
        pops = bool(np.nanmax(r2[e2.t0 : min(scene.n, e2.t0 + frames(1.5) + 1)]) >= THREE_R)
        out.append(
            _ev(
                "double_drag",
                {
                    "handler": e1.actors["handler"],
                    "screener_1": e1.actors["screener"],
                    "screener_2": e2.actors["screener"],
                },
                e1.t0,
                e1.t0,
                max(e1.end, e2.end),
                conf,
                gap_s=(e2.t0 - e1.t0) * DT,
                separation_m=sep,
                second_pops=pops,
            )
        )
    return out


def detect_trailer_pitch_back(scene, **params) -> list[Event]:
    """TRN-A05: backward or flat pass to a trailer at the top of the arc (6.75-8.5 m, 70-110 deg)."""
    p = _prm("trailer_pitch_back", params)
    roles = _roles(scene)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        trs = {o for o, r in roles.get(t0, {}).items() if r.startswith("trailer")}
        for q in _passes(scene):
            if not q["same_team"] or q["receiver"] not in trs or not (t0 <= q["t_catch"] <= t0 + frames(p["window_s"])):
                continue
            k = scene.k(q["receiver"])
            t = q["t_catch"]
            r = math.hypot(k.x[t], k.y[t])
            m_ = math.degrees(math.atan2(k.y[t], abs(k.x[t])))
            if not (p["r_min_m"] <= r <= p["r_max_m"] and m_ >= 70.0 and q["y1"] >= q["y0"] - p["flat_tol_m"]):
                continue
            sr = float(_sig_p(k)[t])
            conf = (
                _hold_p(scene, q["receiver"], t, q["catch_end"])
                * float(phi(min(r - p["r_min_m"], p["r_max_m"] - r) / sr))
                * _qobj(scene, [q["passer"], q["receiver"]], t, q["t_rel"], t)
            )
            out.append(
                _ev(
                    "trailer_pitch_back",
                    {"passer": q["passer"], "trailer": q["receiver"]},
                    t,
                    q["t_rel"],
                    t,
                    conf,
                    catch_r=r,
                    rel_t0_s=(t - t0) * DT,
                    poss_t0=t0,
                )
            )
    return out


def detect_rim_runner_hit(scene, **params) -> list[Event]:
    """TRN-A06: pass caught by the rim runner at r <= 3.0 within 2.0 s of his arrival."""
    p = _prm("rim_runner_hit", params)
    roles = _roles(scene)
    out = []
    for rr in detect_rim_run(scene):
        o, f, t0 = rr.actors["runner"], rr.attrs["t_rim_arrive"], rr.attrs["poss_t0"]
        k = scene.k(o)
        for q in _passes(scene):
            t = q["t_catch"]
            if (
                q["receiver"] != o
                or not q["same_team"]
                or not (f - frames(0.5) <= t <= f + frames(p["after_arrive_s"]))
            ):
                continue
            if (t - t0) * DT > p["window_s"]:
                continue
            r = math.hypot(k.x[t], k.y[t])
            if r > p["catch_r_m"]:
                continue
            a = max(0, t - frames(p["seal_s"]))
            seal = math.hypot(k.x[t] - k.x[a], k.y[t] - k.y[a]) < p["seal_disp_m"] and r < 2.5
            sub = (
                "seal_pass"
                if seal
                else ("big_to_big" if str(roles.get(t0, {}).get(q["passer"], "")).startswith("trailer") else "hit")
            )
            conf = (
                _hold_p(scene, o, t, q["catch_end"])
                * float(phi((p["catch_r_m"] - r) / float(_sig_p(k)[t])))
                * _qobj(scene, [q["passer"], o], t, q["t_rel"], t)
            )
            out.append(
                _ev(
                    "rim_runner_hit",
                    {"passer": q["passer"], "runner": o},
                    t,
                    q["t_rel"],
                    t,
                    conf,
                    sub_type=sub,
                    catch_r=r,
                    delay_after_arrival_s=(t - f) * DT,
                    lob="needs_ball_z",
                    poss_t0=t0,
                )
            )
    return out


def detect_stop_ball(scene, **params) -> list[Event]:
    """TRN-A07: first goal-side defender within 2.0 m of the handler in the open court, handler slows."""
    p = _prm("stop_ball", params)
    hd = _handler(scene)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        hi = min(scene.n - 1, t0 + frames(p["window_s"]))
        found = None
        for t in range(t0, hi + 1):
            h = hd[t]
            if h is None:
                continue
            kh = scene.k(h)
            if kh.y[t] > FAR_RIM_Y - p["open_court_dy_m"]:
                continue  # near the rebound: that is a jam, not a pickup
            for d in scene.defense:
                kd = scene.k(d)
                if kd.y[t] < kh.y[t] and math.hypot(kd.x[t] - kh.x[t], kd.y[t] - kh.y[t]) <= p["pickup_m"]:
                    v05, sg = _vbar(scene, h, VS)
                    w = v05[t : min(scene.n, t + frames(p["slow_within_s"]) + 1)]
                    if np.nanmin(w) < p["slow_mps"]:
                        found = (t, h, d)
                        break
            if found:
                break
        if not found:
            continue
        t, h, d = found
        kh, kd = scene.k(h), scene.k(d)
        tb = min(scene.n - 1, t + frames(0.3))
        dd = mv.dist(kh, kd)
        v05, sg = _vbar(scene, h, VS)
        sw = min(scene.n - 1, t + frames(p["slow_within_s"]))
        conf = (
            window_conf(p_below(dd, p["pickup_m"] + p["hyst_m"], mv.sigma_dist(kh, kd)), t, tb)
            * float(np.nanmax(p_below(v05[t : sw + 1], p["slow_mps"], sg[t : sw + 1])))
            * _qobj(scene, [h, d], t, t, tb)
        )
        turned = bool(np.nanmax(np.abs(kh.x[t : min(scene.n, t + frames(2.0) + 1)])) >= 3.0)
        out.append(
            _ev(
                "stop_ball",
                {"handler": h, "defender": d},
                t,
                t,
                tb,
                conf,
                rel_t0_s=(t - t0) * DT,
                pickup_y=float(kh.y[t]),
                backcourt=bool(kh.y[t] > HALF_Y),
                turned_to_side=turned,
                poss_t0=t0,
            )
        )
    return out


def detect_jam_rebounder(scene, **params) -> list[Event]:
    """TRN-A08: the rebounder's nearest opponent stays within 1.5 m for >= 0.5 s after the rebound."""
    p = _prm("jam_rebounder", params)
    out = []
    for ps in _possessions(scene):
        if ps["start_type"] != "dreb":
            continue
        reb, t0 = ps["gainer"], ps["t0"]
        hi = min(scene.n - 1, t0 + frames(p["window_s"]))
        kr = scene.k(reb)
        D = {d: mv.dist(kr, scene.k(d)) for d in scene.defense}
        for d in scene.defense:
            mask = np.zeros(scene.n, dtype=bool)
            for t in range(t0, hi + 1):
                mask[t] = D[d][t] <= p["jam_m"] and all(D[d][t] <= D[q][t] for q in scene.defense)
            rr = _runs_of(mask, _dwell(MIN_DUR["jam_rebounder"]))
            if not rr:
                continue
            s, e = rr[0]
            kd = scene.k(d)
            conf = window_conf(p_below(D[d], p["jam_m"], mv.sigma_dist(kr, kd)), s, e) * _qobj(scene, [reb, d], s, s, e)
            out.append(
                _ev(
                    "jam_rebounder",
                    {"rebounder": reb, "defender": d},
                    s,
                    s,
                    e,
                    conf,
                    duration_s=(e - s) * DT,
                    poss_t0=t0,
                )
            )
    return out


def detect_matchup(scene, **params) -> list[Event]:
    """TRN-A09: first time every attacker is matched (2.5 / 1.5 m) for 1 s; cross-matches vs the pre-change pairs."""
    p = _prm("matchup", params)
    out = []
    if len(scene.offense) != len(scene.defense) or not scene.offense:
        return out
    for ps in _possessions(scene):
        t0 = ps["t0"]
        hi = min(scene.n - 1, t0 + frames(p["window_s"]))
        ok = np.zeros(scene.n, dtype=bool)
        pmin = np.zeros(scene.n)
        for t in range(t0, hi + 1):
            pr = []
            for a in scene.offense:
                ka = scene.k(a)
                rad = p["near_m"] if math.hypot(ka.x[t], ka.y[t]) >= 3.0 else p["close_m"]
                ds = [(math.hypot(scene.k(d).x[t] - ka.x[t], scene.k(d).y[t] - ka.y[t]), d) for d in scene.defense]
                dm, dn = min(ds)
                sd = float(mv.sigma_dist(ka, scene.k(dn))[t])
                pr.append(float(phi((rad - dm) / sd)))
            pmin[t] = min(pr)
            ok[t] = pmin[t] > 0.5
        rr = _runs_of(ok, _dwell(MIN_DUR["matchup"]))
        if not rr:
            continue
        s, e = rr[0]

        def pairs(t):
            cost = np.array(
                [
                    [
                        math.hypot(scene.k(d).x[t] - scene.k(a).x[t], scene.k(d).y[t] - scene.k(a).y[t])
                        for d in scene.defense
                    ]
                    for a in scene.offense
                ]
            )
            perm, _ = _assign(cost)
            return {a: scene.defense[perm[i]] for i, a in enumerate(scene.offense)}

        now = pairs(s)
        pre = pairs(max(0, t0 - frames(p["pre_s"])))
        xm = sum(now[a] != pre[a] for a in scene.offense)
        conf = window_conf(pmin, s, e) * _qobj(scene, scene.players(), s, s, e)
        out.append(
            _ev(
                "matchup",
                {"gainer": ps["gainer"]},
                s,
                s,
                e,
                conf,
                assignment=now,
                pre_assignment=pre,
                cross_matches=int(xm),
                automatic_pickup=xm == 0,
                rel_t0_s=(s - t0) * DT,
                poss_t0=t0,
            )
        )
    return out


def detect_tandem_stack(scene, **params) -> list[Event]:
    """TRN-A10: two defenders stacked in line (|dx| <= 1.5, |dy| >= 2.0) during a numbers advantage."""
    p = _prm("tandem_stack", params)
    bx, by, _ = _ball_filled(scene)
    out = []
    for adv in _memo(scene, "numbers", lambda: detect_numbers_advantage(scene)):
        a, b = adv.start, adv.end
        for d1, d2 in itertools.combinations(scene.defense, 2):
            k1, k2 = scene.k(d1), scene.k(d2)
            dx, dy = np.abs(k1.x - k2.x), np.abs(k1.y - k2.y)
            mask = (dx <= p["max_dx_m"]) & (dy >= p["min_dy_m"]) & (k1.y < by) & (k2.y < by)
            mask[:a] = False
            mask[b + 1 :] = False
            rr = _runs_of(mask, _dwell(MIN_DUR["tandem_stack"]))
            if not rr:
                continue
            s, e = rr[0]
            sd = mv.sigma_dist(k1, k2)
            pr = np.minimum(p_below(dx, p["max_dx_m"], sd), p_above(dy, p["min_dy_m"], sd))
            top, bot = (d1, d2) if k1.y[s] > k2.y[s] else (d2, d1)
            out.append(
                _ev(
                    "tandem_stack",
                    {"top": top, "bottom": bot},
                    s,
                    s,
                    e,
                    window_conf(pr, s, e) * _qobj(scene, [d1, d2], s, s, e),
                    poss_t0=adv.attrs["poss_t0"],
                )
            )
    return out


def detect_run_out(scene, **params) -> list[Event]:
    """TRN-A11: within 3 s of a steal / block / long rebound, nobody between the handler and the rim, and the handler
    takes the ball toward the rim (fix TRN-T09)."""
    p = _prm("run_out", params)
    hd = _handler(scene)
    out = []
    for ps in _possessions(scene):
        gx, gy = ps["gain_xy"]
        long_reb = ps["start_type"] == "dreb" and math.hypot(gx, gy - FAR_RIM_Y) >= p["long_reb_m"]
        if ps["start_type"] not in ("steal", "block_to_break") and not long_reb:
            continue
        t0 = ps["t0"]
        hi = min(scene.n - 1, t0 + frames(p["within_s"]))
        mask = np.zeros(scene.n, dtype=bool)
        prob = np.zeros(scene.n)
        for t in range(t0, hi + 1):
            h = hd[t]
            if h is None:
                continue
            kh = scene.k(h)
            if kh.y[t] <= 2.0:
                continue
            pr = [1.0]
            for d in scene.defense:
                kd = scene.k(d)
                if kd.y[t] >= kh.y[t]:
                    continue
                sd = _seg_dist(kd.x[t], kd.y[t], kh.x[t], kh.y[t], 0.0, 0.0)
                pr.append(float(phi((sd - p["seg_m"]) / float(mv.sigma_dist(kh, kd)[t]))))
            prob[t] = min(pr)
            mask[t] = prob[t] > 0.5
        for s, e in _runs_of(mask, _dwell(MIN_DUR["run_out"])):
            # one handler per open-lane run (a pass ahead hands the run-out to the receiver)
            for s2, e2 in _runs_of(np.array([mask[t] and hd[t] == hd[s] for t in range(scene.n)]), 1):
                if not (s <= s2 <= e):
                    continue
                if (e2 - s2) * DT < MIN_DUR["run_out"] - 1e-9:
                    continue
                h = hd[s2]
                vb, sgb = _v_back(scene, h)
                seg = np.nan_to_num(vb[s2 : e2 + 1], nan=-9.0)
                if not np.max(seg) >= p["move_mps"]:
                    continue  # a standing rebounder or stealer is not a run-out: the ball must go toward the rim
                im = s2 + int(np.argmax(seg))
                conf = (
                    window_conf(prob, s2, e2)
                    * float(p_above(vb[im], p["move_mps"], sgb[im]))
                    * _qobj(scene, [h], s2, s2, e2)
                )
                out.append(
                    _ev(
                        "run_out",
                        {"handler": h},
                        s2,
                        s2,
                        e2,
                        conf,
                        variant="segment",
                        start_type=ps["start_type"],
                        rel_t0_s=(s2 - t0) * DT,
                        peak_v_back=float(vb[im]),
                        poss_t0=t0,
                    )
                )
                break
            else:
                continue
            break
    return out


def detect_screen_the_inbounder(scene, **params) -> list[Event]:
    """TRN-A13: after stepping in, the inbounder runs off a stationary teammate's screen."""
    p = _prm("screen_the_inbounder", params)
    runs = _hold_runs(scene)
    tws = {tw["last_thrower"]: tw for tw in _throw_ins(scene)}
    out = []
    for st in detect_inbounder_step_in(scene):
        o = st.actors["thrower"]
        tw = tws.get(o)
        if tw is None:
            continue
        ko = scene.k(o)
        team = scene.offense if tw["team"] == "O" else scene.defense
        hi = min(scene.n - 6, st.t0 + frames(p["contact_after_s"]))
        hit = None
        for t in range(st.t0, hi + 1):
            for s in team:
                if s == o:
                    continue
                ks = scene.k(s)
                if (
                    math.hypot(ks.x[t] - ko.x[t], ks.y[t] - ko.y[t]) <= p["contact_m"]
                    and np.mean(ks.stationary_s2[t - 5 : t + 6] < CHI2) >= 0.6
                ):
                    hit = (t, s)
                    break
            if hit:
                break
        if hit is None:
            continue
        t, s = hit
        ks = scene.k(s)
        ah = min(scene.n - 1, t + frames(p["catch_s"]))
        catch = any(r[0] == o and t <= r[1] <= ah for r in runs)
        ro = np.hypot(ko.x, ko.y)[t : ah + 1]
        if not (catch or np.nanmin(ro) <= 2.0 or np.nanmax(ro) >= THREE_R):
            continue
        d = mv.dist(ko, ks)
        tb = min(scene.n - 1, t + frames(0.3))
        conf = window_conf(p_below(d, p["contact_m"], mv.sigma_dist(ko, ks)), t, tb) * _qobj(scene, [o, s], t, t, tb)
        out.append(_ev("screen_the_inbounder", {"inbounder": o, "screener": s}, t, st.t0, ah, conf, catch=catch))
    return out


TRAP_SPOTS = (
    "backcourt_corner_trap",
    "trap_backcourt_corner",
    "backcourt_sideline_trap",
    "trap_halfcourt_backcourt_corner",
    "trap_coffin_corner",
    "frontcourt_halfcourt_corner_trap",
    "baseline_corner_trap",
)


def _traps(scene, p=None):
    """[((handler, (d1, d2)), a, b)] press traps with the press_trap parameters (overrides honoured, fix TRN-T11).

    Window statistics (fix TRN-T10, loop 2): over the last entry_window_s, with the same holder throughout, the
    MEDIAN distance of the handler to each of his two nearest defenders is <= trap_m + entry_sigma_k x sigma_dist and
    the median pair distance <= pair_m + entry_sigma_k x sigma_dist (sigma_dist = median MP-19 pair sigma over the
    window, so the margin scales with the measured noise tier and vanishes on clean tracks). The trap starts at the
    window centre (the frame the medians describe). Stay while the same holder (holder hysteresis, TRN-T02) keeps the
    window medians within the thresholds + hyst_m + the same sigma margin; gaps <= gap_s bridged; >= min_duration_s.
    A per-frame hard conjunction of three smoothed distances failed on noise alone; the joint-probability entry of
    TRN-T10 can only remove entries (loop 1), so the joint probability is stored as p_enter instead."""
    p = _prm("press_trap") if p is None else p

    def calc():
        hd = _holders(scene)
        ids = scene.players()
        X = {o: scene.k(o).x for o in ids}
        Y = {o: scene.k(o).y for o in ids}
        VP = {o: np.nan_to_num(scene.k(o).var_p, nan=0.09) for o in ids}
        kk, W = p["entry_sigma_k"], max(1, frames(p["entry_window_s"]) + 1)
        ks = p["stay_sigma_k"]  # loop 4 (confirm-3 NEW-T10-k2-conf-dilution): the stay test keeps a 1-sigma margin

        def d(o1, o2, t):
            return math.hypot(X[o1][t] - X[o2][t], Y[o1][t] - Y[o2][t])

        def within(o1, o2, t0_, t1_, thr, kx=None):
            """Median distance over [t0_, t1_] <= thr + kx x median sigma_dist (kx defaults to entry_sigma_k)."""
            kx = kk if kx is None else kx
            dd = np.hypot(X[o1][t0_ : t1_ + 1] - X[o2][t0_ : t1_ + 1], Y[o1][t0_ : t1_ + 1] - Y[o2][t0_ : t1_ + 1])
            sd = np.median(K_CAL * np.sqrt(VP[o1][t0_ : t1_ + 1] + VP[o2][t0_ : t1_ + 1]))
            return bool(np.nanmedian(dd) <= thr + kx * sd)

        rc = p["rim_clear_m"]

        def press_zone(h, t):
            """Loop 4 (TRN-L4-trapzone, real SportVU): a press trap is set where a press traps, i.e. the handler is in
            the backcourt outside rim_clear_m of the far rim (a crowd around a rebounder is not a trap) or in one of
            the frontcourt trap spots (TRAP_SPOTS: sideline/halfcourt corners, coffin corner, baseline corner). Two
            defenders around a handler in the paint or at the arc are help, a post double or a ball-screen show/blitz
            (defense family), not a press trap."""
            x, y = X[h][t], Y[h][t]
            if not (np.isfinite(x) and np.isfinite(y)):
                return False
            if y > HALF_Y:
                return math.hypot(x, y - FAR_RIM_Y) > rc
            return any(_in_spot(sid, x, y) for sid in TRAP_SPOTS)

        out, cur, gap = [], None, frames(p["gap_s"])
        for t in range(scene.n):
            h = hd[t]
            if cur is not None:
                (hh, (d1, d2)), a, last = cur
                ta, h_ = max(a, t - W + 1), p["hyst_m"]
                if (
                    h == hh
                    and within(hh, d1, ta, t, p["trap_m"] + h_, ks)
                    and within(hh, d2, ta, t, p["trap_m"] + h_, ks)
                    and within(d1, d2, ta, t, p["pair_m"] + h_, ks)
                ):
                    cur[2] = t
                    continue
                if t - last <= gap:
                    continue
                out.append(tuple(cur))
                cur = None
            if h is not None and _team(scene, h) == "O" and press_zone(h, t):
                ds = sorted((d(h, q, t), q) for q in scene.defense)
                if len(ds) < 2 or not np.isfinite(ds[1][0]):
                    continue
                q1, q2 = ds[0][1], ds[1][1]
                ta = t - W + 1
                if (
                    ta >= 0
                    and all(hd[u] == h for u in range(ta, t + 1))
                    and within(h, q1, ta, t, p["trap_m"])
                    and within(h, q2, ta, t, p["trap_m"])
                    and within(q1, q2, ta, t, p["pair_m"])
                ):
                    cur = [(h, tuple(sorted((q1, q2)))), t - (W - 1) // 2, t]
        if cur is not None:
            out.append(tuple(cur))
        return [(pr, a, b) for pr, a, b in out if (b - a) * DT >= MIN_DUR["press_trap"] - 1e-9]

    return _memo(scene, _pkey("traps", p, "press_trap"), calc)


def detect_press_trap(scene, **params) -> list[Event]:
    """TRN-A14a: two defenders within 1.5 m of the handler (and 2.5 m of each other) for >= 0.6 s."""
    p = _prm("press_trap", params)
    bx, by, _ = _ball_filled(scene)
    out = []
    for (h, (d1, d2)), a, b in _traps(scene, p):
        kh, k1, k2 = scene.k(h), scene.k(d1), scene.k(d2)
        pr = np.minimum(
            p_below(mv.dist(kh, k1), p["trap_m"], mv.sigma_dist(kh, k1)),
            p_below(mv.dist(kh, k2), p["trap_m"], mv.sigma_dist(kh, k2)),
        )
        m = (a + b) // 2  # location at the middle of the trap (the onset is still moving)
        locs = [sid for sid in TRAP_SPOTS if _in_spot(sid, bx[m], by[m])]
        out.append(
            _ev(
                "press_trap",
                {"handler": h, "defender_1": d1, "defender_2": d2},
                a,
                a,
                b,
                window_conf(pr, a, b) * _qobj(scene, [h, d1, d2], a, a, b),
                locations=locs,
                duration_s=(b - a) * DT,
                p_enter=float(
                    p_below(mv.dist(kh, k1)[a], p["trap_m"], mv.sigma_dist(kh, k1)[a])
                    * p_below(mv.dist(kh, k2)[a], p["trap_m"], mv.sigma_dist(kh, k2)[a])
                    * p_below(mv.dist(k1, k2)[a], p["pair_m"], mv.sigma_dist(k1, k2)[a])
                ),
            )
        )
    return out


def detect_trap_breaker_pass(scene, **params) -> list[Event]:
    """TRN-A14b: pass out of a trap released after the second defender arrives."""
    p = _prm("trap_breaker_pass", params)
    traps = detect_press_trap(scene)
    out = []
    for q in _passes(scene):
        if not q["same_team"] or _team(scene, q["passer"]) != "O":
            continue
        for tp in traps:
            if tp.actors["handler"] != q["passer"]:
                continue
            if not (tp.start - frames(p["lead_s"]) <= q["t_rel"] <= tp.end + frames(p["hold_after_s"])):
                continue
            dy = q["y1"] - q["y0"]
            tgt = (
                "over_the_top"
                if dy <= -8.0
                else "middle"
                if abs(q["x1"]) < 3.0
                else "reversal"
                if dy >= 1.0
                else "sideline"
                if abs(q["x1"]) >= 5.0
                else "other"
            )
            conf = (
                tp.conf
                * _hold_p(scene, q["receiver"], q["t_catch"], q["catch_end"])
                * _qobj(scene, [q["receiver"]], q["t_catch"], q["t_rel"], q["t_catch"])
            )
            out.append(
                _ev(
                    "trap_breaker_pass",
                    {"passer": q["passer"], "receiver": q["receiver"]},
                    q["t_rel"],
                    q["t_rel"],
                    q["t_catch"],
                    conf,
                    delay_s=(q["t_rel"] - tp.start) * DT,
                    target=tgt,
                )
            )
            break
    return out


def detect_press_reversal(scene, **params) -> list[Event]:
    """TRN-A15: backward or cross-court pass in the backcourt while (or just after) a trap is on."""
    p = _prm("press_reversal", params)
    traps = detect_press_trap(scene)
    out = []
    for q in _passes(scene):
        if not q["same_team"] or _team(scene, q["passer"]) != "O" or q["y0"] <= HALF_Y:
            continue
        if not any(
            tp.start <= q["t_rel"] <= tp.end + frames(0.2) or 0 <= (q["t_rel"] - tp.start) * DT <= p["recent_s"]
            for tp in traps
        ):
            continue
        dy, dx = q["y1"] - q["y0"], q["x1"] - q["x0"]
        if not (dy >= p["back_dy_m"] or (abs(dx) >= p["across_dx_m"] and dy >= -1.0)):
            continue
        conf = _hold_p(scene, q["receiver"], q["t_catch"], q["catch_end"]) * _qobj(
            scene, [q["passer"], q["receiver"]], q["t_rel"], q["t_rel"], q["t_catch"]
        )
        out.append(
            _ev(
                "press_reversal",
                {"passer": q["passer"], "receiver": q["receiver"]},
                q["t_rel"],
                q["t_rel"],
                q["t_catch"],
                conf,
                direction="back" if dy >= p["back_dy_m"] else "across",
                length_m=q["length"],
            )
        )
    return out


def detect_home_run_inbound(scene, **params) -> list[Event]:
    """TRN-A16: long (>= 15 m) inbound from the far end line caught in the frontcourt."""
    p = _prm("home_run_inbound", params)
    out = []
    for ev in detect_throw_in(scene):
        if ev.attrs["restart_type"] != "backcourt_endline" or ev.attrs["pass_length_m"] < p["min_len_m"]:
            continue
        kr = scene.k(ev.actors["receiver"])
        t = ev.attrs["t_first_touch"]
        if kr.y[t] > HALF_Y:
            continue
        sd = math.sqrt(2) * float(_ball_sig(scene)[t])
        conf = ev.conf * float(phi((ev.attrs["pass_length_m"] - p["min_len_m"]) / sd))
        out.append(
            _ev(
                "home_run_inbound",
                dict(ev.actors),
                ev.t0,
                ev.start,
                ev.end,
                conf,
                length_m=ev.attrs["pass_length_m"],
                target=_in_spot("pb_home_run_target", kr.x[t], kr.y[t]),
            )
        )
    return out


def detect_jump_ball_tip(scene, **params) -> list[Event]:
    """TRN-A17 (needs_data): needs t_tap from ball height."""
    return []


def detect_ft_box_out(scene, **params) -> list[Event]:
    """TRN-A18: defender holds an attacker off the rim after an FT release while the attacker moves in."""
    p = _prm("ft_box_out", params)
    out = []
    for ft in _ft_releases(scene):
        a = ft["t_ft"]
        b = min(scene.n - 1, ft["t_rim"] + frames(p["after_rim_s"]))
        att = scene.offense if ft["team"] == "O" else scene.defense
        dfn = scene.defense if ft["team"] == "O" else scene.offense
        for o in att:
            if o == ft["shooter"]:
                continue
            ko = scene.k(o)
            rs = np.convolve(np.hypot(ko.x, ko.y), np.ones(7) / 7, mode="same")  # 7-frame mean r
            if rs[a] - np.nanmin(rs[a : b + 1]) < p["attacker_move_m"]:
                continue  # nobody is boxed out if the attacker does not go for the rim
            ro = np.hypot(ko.x, ko.y)
            for d in dfn:
                kd = scene.k(d)
                rd = np.hypot(kd.x, kd.y)
                sep = mv.dist(ko, kd)
                lat = _seg_dist(kd.x, kd.y, ko.x, ko.y, 0.0, 0.0)
                mask = (lat <= p["lateral_m"]) & (rd < ro) & (sep >= p["sep_min_m"]) & (sep <= p["sep_max_m"])
                mask[: a + 2] = False
                mask[b + 1 :] = False
                rr = _runs_of(mask, _dwell(MIN_DUR["ft_box_out"]))
                if not rr:
                    continue
                s, e = rr[0]
                sd = mv.sigma_dist(ko, kd)
                pr = np.minimum(
                    np.minimum(p_above(sep, p["sep_min_m"], sd), p_below(sep, p["sep_max_m"], sd)),
                    p_above(ro - rd, 0.0, sd),
                )
                out.append(
                    _ev(
                        "ft_box_out",
                        {"defender": d, "attacker": o},
                        s,
                        s,
                        e,
                        window_conf(pr, s, e) * _qobj(scene, [o, d], s, s, e),
                        t_ft=a,
                    )
                )
    return out


def detect_take_foul(scene, **params) -> list[Event]:
    """TRN-A19 (needs_data): needs the PBP foul."""
    return []


def detect_tag_and_recover(scene, **params) -> list[Event]:
    """TRN-A20: a defender tags the leak-out runner, then recovers toward the ball."""
    p = _prm("tag_and_recover", params)
    bx, by, _ = _ball_filled(scene)
    out = []
    for lk in detect_leak_out(scene):
        o = lk.actors["runner"]
        ko = scene.k(o)
        for d in scene.defense:
            kd = scene.k(d)
            dd = mv.dist(ko, kd)
            mask = (dd <= p["tag_m"]) & (by > HALF_Y)
            mask[: lk.t0] = False
            rr = _runs_of(mask, 2)
            if not rr:
                continue
            t = rr[0][0]
            vx, vy, sg = _wvel(scene, d, VS)
            dxb, dyb = bx - kd.x, by - kd.y
            db = np.hypot(dxb, dyb)
            close = (vx * dxb + vy * dyb) / np.where(db > 0, db, np.nan)
            hi = min(scene.n - 1, t + frames(p["recover_s"]))
            m2 = np.zeros(scene.n, dtype=bool)
            m2[t : hi + 1] = (np.nan_to_num(close[t : hi + 1], nan=0) >= p["recover_mps"]) & (
                np.gradient(dd)[t : hi + 1] > 0
            )
            r2 = _runs_of(m2, _dwell(0.3))
            if not r2:
                continue
            s, e = r2[0]
            tb = min(scene.n - 1, t + frames(0.2))
            conf = (
                window_conf(p_below(dd, p["tag_m"], mv.sigma_dist(ko, kd)), t, tb)
                * window_conf(p_above(close, p["recover_mps"], sg), s, e)
                * _qobj(scene, [o, d], t, t, e)
            )
            out.append(_ev("tag_and_recover", {"defender": d, "leaker": o}, t, t, e, conf, recover_onset=s))
            break
    return out


# --------------------------------------------------------------------------------------
# Set components
# --------------------------------------------------------------------------------------
def detect_primary_break(scene, **params) -> list[Event]:
    """TRN-S01: advantage active at the half-court crossing (or a run-out) with a shot before it ends."""
    p = _prm("primary_break", params)
    advs = _memo(scene, "numbers", lambda: detect_numbers_advantage(scene))
    outs = detect_run_out(scene)
    pulls = detect_pull_back(scene)
    out = []
    for ps in _possessions(scene):
        t0, c = ps["t0"], ps["t_cross_half"]
        shot = _first_shot_after(scene, t0)
        if shot is None:
            continue
        hit = None
        for adv in advs:
            if adv.attrs["poss_t0"] != t0:
                continue
            active_at_cross = c is not None and adv.start <= c <= adv.end
            started_front = c is not None and adv.start >= c
            if (active_at_cross or started_front) and adv.start <= shot["t_rel"] <= adv.end + frames(p["grace_s"]):
                hit = adv
                break
        # fix TRN-T05: a run-out counts only when the shot follows it within runout_shot_s and the ball was not
        # pulled back out before the shot (that possession is played in the half court)
        pulled = any(e.attrs["poss_t0"] == t0 and e.t0 < shot["t_rel"] for e in pulls)
        ro = next(
            (
                r
                for r in outs
                if r.attrs["poss_t0"] == t0
                and r.start <= shot["t_rel"] <= r.end + frames(p["runout_shot_s"])
                and not pulled
            ),
            None,
        )
        if hit is None and ro is None:
            continue
        src = hit or ro
        dt = (shot["t_rel"] - t0) * DT
        mode = "dribble" if c is None or _holders(scene)[c] is not None else "pass"
        cfg = hit.attrs["config"] if hit is not None else "run_out"
        out.append(
            _ev(
                "primary_break",
                {"gainer": ps["gainer"], "shooter": shot["shooter"]},
                t0,
                t0,
                shot["t_rel"],
                min(ps["conf"], src.conf),
                config=cfg,
                prim_time_2_3s=dt <= 3.0,
                prim_time_3_9s=3.0 < dt <= 9.0,
                name=f"{ps['start_type']} -> {mode} -> {cfg} -> shot",
                shot_rel_t0_s=dt,
            )
        )
    return out


def _structured(scene):
    return sorted(
        detect_drag_screen(scene) + detect_double_drag(scene) + detect_trailer_pitch_back(scene), key=lambda e: e.t0
    )


def detect_secondary_break(scene, **params) -> list[Event]:
    """TRN-S02: no primary break, and a structured transition action (drag, 77, pitch-back) within 12 s."""
    p = _prm("secondary_break", params)
    prim = {e.t0 for e in detect_primary_break(scene)}
    bx, by, _ = _ball_filled(scene)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        if t0 in prim:
            continue
        acts = [e for e in _structured(scene) if t0 <= e.t0 <= t0 + frames(12.0)]
        if not acts:
            continue
        first = acts[0]
        a, b = first.t0, min(scene.n - 1, first.end + frames(3.0))
        need = frames(p["stall_s"])
        stall = any(math.hypot(bx[t + need] - bx[t], by[t + need] - by[t]) < 0.5 for t in range(a, max(a, b - need)))
        out.append(
            _ev(
                "secondary_break",
                {"gainer": ps["gainer"]},
                first.t0,
                t0,
                first.end,
                max(e.conf for e in acts),
                actions=[e.kind for e in acts],
                flow=not stall,
                poss_t0=t0,
            )
        )
    return out


def detect_early_offense_sequence(scene, **params) -> list[Event]:
    """TRN-S03: compositional name and ordered action sequence of each transition / early-offense possession."""
    _prm("early_offense_sequence", params)
    evs = []
    for fid in (
        "outlet_pass",
        "hit_ahead",
        "push",
        "leak_out",
        "rim_run",
        "wing_lane_run",
        "corner_fill",
        "trailer",
        "drag_screen",
        "double_drag",
        "trailer_pitch_back",
        "rim_runner_hit",
        "stop_ball",
        "pull_back",
    ):
        evs += DETECTORS[fid](scene)
    evs += _memo(scene, "numbers", lambda: detect_numbers_advantage(scene))
    prim = {e.t0 for e in detect_primary_break(scene)}
    sec = {e.attrs["poss_t0"] for e in detect_secondary_break(scene)}
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        mine = sorted([e for e in evs if t0 - frames(3.0) <= e.t0 <= t0 + frames(12.0)], key=lambda e: e.t0)
        kinds = [e.kind for e in mine]
        slots = [ps["start_type"]]
        op = next((e for e in mine if e.kind in ("outlet_pass", "dribble_out")), None)
        if op is not None:
            slots.append(f"outlet({op.attrs.get('spot', 'dribble')})" if op.kind == "outlet_pass" else "dribble_out")
        elif ps["t_disposal"] is not None:
            slots.append("inbound")
        slots.append("push" if "push" in kinds else ("pass_ahead" if "hit_ahead" in kinds else "walk"))
        slots.append("primary" if t0 in prim else ("secondary" if t0 in sec else "none"))
        first_act = next((e for e in mine if e.kind in ("double_drag", "drag_screen", "trailer_pitch_back")), None)
        if first_act is not None:
            nm = {"double_drag": "77", "drag_screen": "drag", "trailer_pitch_back": "pitch_back"}[first_act.kind]
            if first_act.kind == "drag_screen":
                nm += f"({first_act.attrs['screener_action']})"
            slots.append(nm)
        seq = [dict(kind=e.kind, t_rel_t0_s=round((e.t0 - t0) * DT, 3), actors=e.actors) for e in mine]
        out.append(
            _ev(
                "early_offense_sequence",
                {"gainer": ps["gainer"]},
                t0,
                t0,
                mine[-1].end if mine else t0,
                ps["conf"],
                compositional_name=" -> ".join(slots),
                action_sequence=seq,
                situation="transition_flow",
            )
        )
    return out


def detect_push_after_make(scene, **params) -> list[Event]:
    """TRN-S04: quick inbound (<= 2.0 s after the make proxy) and half-court crossing <= 5.0 s after it."""
    p = _prm("push_after_make", params)
    out = []
    for ps in _possessions(scene):
        if ps["start_type"] != "made_fg" or ps["t_rim"] is None:
            continue
        t_net = ps["t_rim"]
        tw = next((ev for ev in detect_throw_in(scene) if ev.attrs["t_disposal"] == ps["t_disposal"]), None)
        if tw is None or ps["t_cross_half"] is None:
            continue
        delay = (tw.attrs["t_release"] - t_net) * DT
        cross = (ps["t_cross_half"] - t_net) * DT
        if delay > p["quick_s"] or cross > p["cross_s"]:
            continue
        rel = tw.attrs["t_release"]
        press = sum(scene.k(d).y[rel] > HALF_Y for d in scene.defense) >= 2
        out.append(
            _ev(
                "push_after_make",
                {"inbounder": tw.actors["thrower"], "receiver": tw.actors["receiver"]},
                t_net,
                t_net,
                ps["t_cross_half"],
                tw.conf,
                inbound_delay_s=delay,
                cross_after_net_s=cross,
                press_present=press,
                q_anchor=0.6,
                poss_t0=ps["t0"],
            )
        )
    return out


def detect_passed_up_break(scene, **params) -> list[Event]:
    """TRN-S05: an early numbers opportunity followed by a slow crossing, a held ball or a pull-back."""
    p = _prm("passed_up_break", params)
    advs = _memo(scene, "numbers", lambda: detect_numbers_advantage(scene))
    pulls = detect_pull_back(scene)
    jams = detect_jam_rebounder(scene)
    traps = detect_press_trap(scene)
    trans = {ev.attrs["poss_t0"]: ev for ev in _memo(scene, "transition", lambda: detect_transition_phase(scene))}
    hd = _holders(scene)  # the ball must actually be held (a pass in flight is not a held ball)
    out = []
    for ps in _possessions(scene):
        t0 = ps["t0"]
        # fix TRN-T06: the opportunity is anchored on the ball (half-court crossing, else t0); after a defensive
        # rebound at the far rim the attackers only count once they are near the ball, 2-3 s after t0
        anchor = ps["t_cross_half"] if ps["t_cross_half"] is not None else t0
        opp = next((a for a in advs if a.attrs["poss_t0"] == t0 and (a.start - anchor) * DT <= p["opp_s"]), None)
        if opp is None:
            continue
        c = ps["t_cross_half"]
        fired = None
        if c is None or (c - t0) * DT > p["slow_cross_s"]:
            fired = ("slow_crossing", t0 + frames(p["slow_cross_s"]), 0.9)
        hi = c if c is not None else min(scene.n - 1, t0 + frames(p["slow_cross_s"]))
        need = _dwell(p["held_s"])
        run = 0
        for t in range(t0, hi + 1):
            h = hd[t] if hd[t] is not None and _team(scene, hd[t]) == "O" else None
            v = _vbar(scene, h, VS)[0][t] if h is not None else np.nan
            run = run + 1 if (h is not None and v < p["held_mps"]) else 0
            if run >= need:
                v05, sg = _vbar(scene, h, VS)
                cand = ("held_ball", t - need + 1, window_conf(p_below(v05, p["held_mps"], sg), t - need + 1, t))
                if fired is None or cand[1] < fired[1]:
                    fired = cand
                break
        pb = next((e for e in pulls if e.attrs["poss_t0"] == t0 and e.attrs["with_advantage"]), None)
        if pb is not None and (fired is None or pb.t0 < fired[1]):
            fired = ("pull_back_with_advantage", pb.t0, pb.conf)
        if fired is None:
            continue
        cond, t, pc = fired
        denied = any(j.attrs["poss_t0"] == t0 for j in jams) or any(t0 <= tp.start <= t for tp in traps)
        # fix TRN-T16: failed = the other team takes control (a hold of >= control_min_s) before the defense is set
        tr = trans.get(t0)
        set_t = tr.attrs["defense_set_t"] if tr is not None else None
        lim = set_t if set_t is not None else min(scene.n - 1, t0 + frames(PARAMS["transition_phase"]["set_timeout_s"]))
        cmin = frames(PARAMS["possession_change"]["control_min_s"])
        failed = any(_team(scene, r[0]) == "D" and t0 < r[1] <= lim and r[2] - r[1] >= cmin for r in _hold_runs(scene))
        out.append(
            _ev(
                "passed_up_break",
                {"gainer": ps["gainer"]},
                t,
                t0,
                t,
                opp.conf * pc,
                condition=cond,
                category="failed" if failed else ("denied" if denied else "declined"),
                poss_t0=t0,
            )
        )
    return out


def detect_defensive_transition_scheme(scene, **params) -> list[Event]:
    """TRN-S06: one back / two back / shooter back / send the house per missed shot of the losing team."""
    _prm("defensive_transition_scheme", params)
    dec = detect_shot_rebound_decision(scene)
    saf = detect_safety(scene)
    bx, by, _ = _ball_filled(scene)
    out = []
    for s in _far_shots(scene):
        mine = [e for e in dec if e.t0 == s["t_rel"]]
        if not mine:
            continue
        sf = [e for e in saf if e.attrs["t_rel"] == s["t_rel"]]
        ci = mine[0].attrs["CI"]
        n_s = len(sf)
        shooter_safe = any(e.attrs["shooter_back"] for e in sf)
        if shooter_safe and ci >= 3:
            label = "shooter_back"
        elif n_s == 1 and ci >= 3:
            label = "one_back"
        elif n_s == 2:
            label = "two_back"
        elif ci >= 4 and n_s == 0:
            label = "send_house"
        elif ci <= 1:
            label = "everyone_back"
        else:
            label = "balanced"
        t3 = next((t for t in range(s["t_rel"], scene.n) if math.hypot(bx[t], by[t]) <= THREE_R), None)
        nml = None if t3 is None else int(sum(scene.k(d).y[t3] > HALF_Y for d in scene.defense))
        conf = float(np.mean([e.conf for e in mine + sf]))
        out.append(
            _ev(
                "defensive_transition_scheme",
                {"shooter": s["shooter"]},
                s["t_rel"],
                s["t_rel"],
                mine[0].end,
                conf,
                label=label,
                crash_n=ci,
                safety_count=n_s,
                safeties=[e.actors["player"] for e in sf],
                no_mans_land=nml,
            )
        )
    return out


def _press_context(scene):
    """Loop 4 (TRN-L4-press, real SportVU): frames of an offense possession that started with a throw-in (from the
    throw-in's t_disposal until the next defense hold). A press is set against an inbound (made basket, dead ball);
    after a live rebound or steal the defenders still in the backcourt are the shooter and the crashers, which is
    transition defense (stop_ball, jam_rebounder), not a press."""

    def calc():
        m = np.zeros(scene.n, dtype=bool)
        runs = _hold_runs(scene)
        for tw in _throw_ins(scene):
            if tw["team"] != "O":
                continue
            end = scene.n - 1
            for oid, a, _ in runs[tw["recv_run"] :]:
                if _team(scene, oid) == "D":
                    end = a - 1
                    break
            m[tw["t_disposal"] : end + 1] = True
        return m

    return _memo(scene, "press_ctx", calc)


def detect_press_active(scene, **params) -> list[Event]:
    """TRN-S07a: >= 3 non-retreating defenders in the backcourt with the ball there after an offense throw-in and its
    nearest defender within 2.0 m."""
    p = _prm("press_active", params)
    bx, by, _ = _ball_filled(scene)
    if not scene.defense:
        return []
    hd = _handler(scene)
    cond = np.zeros(scene.n, dtype=bool)
    dmin = np.full(scene.n, np.inf)
    smin = np.full(scene.n, 0.3)
    ctx = _press_context(scene)
    vback = {d: np.nan_to_num(_v_back(scene, d)[0], nan=0.0) for d in scene.defense}
    for t in range(scene.n):
        if by[t] <= HALF_Y or hd[t] is None or not ctx[t]:
            continue  # the ball must be in the backcourt and in the offense's control after a throw-in (loop 4)
        # loop 4: a defender retreating (window speed toward his own rim >= max_back_mps = retreat.onset_mps) is
        # getting back, not pressing
        nb = sum(scene.k(d).y[t] > HALF_Y and vback[d][t] < p["max_back_mps"] for d in scene.defense)
        kh = scene.k(hd[t])  # the handler (forward-filled through passes), not the ball in flight
        ds = [(math.hypot(scene.k(d).x[t] - kh.x[t], scene.k(d).y[t] - kh.y[t]), d) for d in scene.defense]
        dm, dn = min(ds)
        dmin[t] = dm
        smin[t] = float(mv.sigma_dist(kh, scene.k(dn))[t])
        cond[t] = nb >= p["min_defenders"] and dm <= p["engage_m"]
    out = []
    for a, b in mv.hysteresis(cond, cond, MIN_DUR["press_active"], frames(p["exit_s"])):
        depth = "full" if by[a] >= 21.2598 else ("three_quarter" if by[a] > HALF_Y else "half_court")
        conf = window_conf(np.where(cond, p_below(dmin, p["engage_m"], smin), 0.0), a, b) * _qobj(
            scene, [hd[a]], a, a, b
        )
        out.append(_ev("press_active", {"defense": tuple(scene.defense)}, a, a, b, conf, depth=depth))
    return out


def detect_press_fall_back(scene, **params) -> list[Event]:
    """TRN-S07b: after a press, >= 4 defenders back at y < 9.0 m."""
    p = _prm("press_fall_back", params)
    out = []
    for pr in _press_intervals(scene):
        lo, hi = pr.end + 1, min(scene.n - 1, pr.end + frames(10.0))
        mask = np.zeros(scene.n, dtype=bool)
        prob = np.zeros(scene.n)
        for t in range(lo, hi + 1):
            ps_ = np.array([phi((p["fall_y_m"] - scene.k(d).y[t]) / _sig_p(scene.k(d))[t]) for d in scene.defense])
            mask[t] = np.sum(ps_ > 0.5) >= p["min_defenders"]
            prob[t] = _pb_count(ps_, p["min_defenders"])
        rr = _runs_of(mask, _dwell(MIN_DUR["press_fall_back"]))
        if not rr:
            continue
        s, e = rr[0]
        out.append(
            _ev(
                "press_fall_back",
                {"defense": tuple(scene.defense)},
                s,
                s,
                e,
                window_conf(prob, s, e) * _qobj(scene, ["ball"], s, s, _last_ball(scene, s, e)),
                after_press_s=(s - pr.end) * DT,
            )
        )
    return out


PRESS_TEMPLATES = {
    "4_across": [(-6.0, 20.5), (-2.0, 20.5), (2.0, 20.5), (6.0, 20.5)],
    "80": [(-7.0, 12.5), (7.0, 12.5), (0.0, 4.0), (2.5, 23.0)],
    "diamond": [(-3.0, 21.26), (3.0, 21.26), (-6.5, 12.7), (6.5, 12.7)],
    "60": [(0.0, 17.0), (-6.5, 13.0), (6.5, 13.0), (3.0, 23.0)],
}


def _template_fit(pts, tpl):
    best = np.inf
    for sx in (1, -1):
        T = np.array([(sx * x, y) for x, y in tpl])
        cost = np.hypot(pts[:, None, 0] - T[None, :, 0], pts[:, None, 1] - T[None, :, 1])
        _, c = _assign(cost)
        best = min(best, c / len(tpl))
    return best


def _snapshot(scene, ids, a, b):
    return np.array([_mean_pos(scene.k(o), a, b) for o in ids])


def detect_press_break_alignment(scene, **params) -> list[Event]:
    """TRN-S08: press-break template (4-Across, 80, Diamond, 60) at a pressed backcourt inbound."""
    p = _prm("press_break_alignment", params)
    out = []
    for tw in _throw_ins(scene):
        if tw["restart_type"] != "backcourt_endline":
            continue
        a = tw["t_disposal"]
        b = min(scene.n - 1, a + frames(p["snap_s"]))
        team = scene.offense if tw["team"] == "O" else scene.defense
        opp = scene.defense if tw["team"] == "O" else scene.offense
        loose = sum(scene.k(d).y[a] > HALF_Y for d in opp) >= 2
        if not loose:
            continue
        ids = [o for o in team if o != tw["thrower"]][:4]
        if len(ids) < 4:
            continue
        pts = _snapshot(scene, ids, a, b)
        fits = sorted((_template_fit(pts, tpl), name) for name, tpl in PRESS_TEMPLATES.items())
        (e1, n1), (e2, _) = fits[0], fits[1]
        if e1 >= p["max_err_m"] or e2 - e1 < p["margin_m"]:
            continue
        # fix TRN-T16: sigma_fit from the measured (calibrated) position sigma of the four, halved for a 4-point mean
        sf = float(np.nanmedian([np.nanmedian(_sig_p(scene.k(o))[a : b + 1]) for o in ids])) / 2
        conf = float(phi((p["max_err_m"] - e1) / sf) * phi((e2 - e1) / sf)) * _qobj(scene, ids, a, a, b)
        out.append(
            _ev(
                "press_break_alignment",
                {"thrower": tw["thrower"]},
                a,
                a,
                b,
                conf,
                template=n1,
                fit_error_m=float(e1),
                margin_m=float(e2 - e1),
                press_present_loose=loose,
            )
        )
    return out


def _throw_in_conf(scene, tw):
    """conf of the throw_in event built from this state-machine record (1.0 when none matches)."""
    ev = next((e for e in detect_throw_in(scene) if e.attrs["t_disposal"] == tw["t_disposal"]), None)
    return 1.0 if ev is None else float(ev.conf)


def _box_margin(x, y, x0, x1, y0, y1):
    return min(x - x0, x1 - x, y - y0, y1 - y)


def _alignment_window(scene, ids, a, rel, snap_s, move_mps):
    """Snapshot window: the snap_s before the first cut (an in-bounds attacker moving >= move_mps for >= 3 frames)
    after disposal, else the last snap_s before the release."""
    w = frames(snap_s)
    for t in range(a + w, rel + 1):
        if any(np.all(np.nan_to_num(scene.k(o).speed[t : t + 3], nan=0) >= move_mps) for o in ids):
            return t - w, t - 1
    return max(a, rel - w), rel


def detect_blob_alignment(scene, **params) -> list[Event]:
    """TRN-S09: BLOB alignment (box / line / stack / 4-low) in the last 0.5 s before the release."""
    p = _prm("blob_alignment", params)
    out = []
    for tw in _throw_ins(scene):
        if tw["restart_type"] != "blob":
            continue
        team = scene.offense if tw["team"] == "O" else scene.defense
        ids = [o for o in team if o != tw["thrower"]]
        if len(ids) < 4:
            continue
        a, rel = _alignment_window(scene, ids, tw["t_disposal"], tw["t_release"], p["snap_s"], p["cut_mps"])
        pts = _snapshot(scene, ids, a, rel)
        sg = float(np.nanmedian([np.nanmedian(_sig_p(scene.k(o))[a : rel + 1]) for o in ids]))
        X, Y = pts[:, 0], pts[:, 1]
        hi = [(i, _box_margin(abs(X[i]), Y[i], 1.0, 3.2, 3.2, 5.2)) for i in range(len(ids))]
        lo = [(i, _box_margin(abs(X[i]), Y[i], 1.2, 3.2, 0.0, 2.0)) for i in range(len(ids))]
        hiL = [m for i, m in hi if m >= 0 and X[i] < 0]
        hiR = [m for i, m in hi if m >= 0 and X[i] >= 0]
        loL = [m for i, m in lo if m >= 0 and X[i] < 0]
        loR = [m for i, m in lo if m >= 0 and X[i] >= 0]
        med = np.median(X)
        near = np.abs(X - med) < p["line_dx_m"]
        if len(hiL) == len(hiR) == len(loL) == len(loR) == 1:
            align, margins = "box", hiL + hiR + loL + loR
        elif np.sum(near) >= 4:
            align, margins = "line", list(p["line_dx_m"] - np.abs(X - med))
        elif np.all(Y <= 1.5) and (X.max() - X.min()) >= p["spread_m"]:
            align, margins = "4_low", list(1.5 - Y) + [X.max() - X.min() - p["spread_m"]]
        elif np.sum(near) >= 3:
            align, margins = "stack", list(p["line_dx_m"] - np.abs(X[near] - med))
        else:
            align, margins = "other", [0.0]
        conf = (
            float(np.mean(phi(np.asarray(margins) / sg)))
            * _throw_in_conf(scene, tw)  # fix TRN-T16: x throw_in conf, as the YAML states
            * _qobj(scene, ids + [tw["thrower"]], rel, a, rel)
        )
        safety = next((ids[i] for i in range(len(ids)) if _in_spot("blob_safety_top", X[i], Y[i])), None)
        out.append(
            _ev(
                "blob_alignment",
                {"thrower": tw["thrower"]},
                tw["t_disposal"],
                a,
                rel,
                conf,
                alignment=align,
                safety=safety,
                name=f"BLOB {align}",
            )
        )
    return out


def detect_slob_alignment(scene, **params) -> list[Event]:
    """TRN-S10: SLOB alignment (line / stack / box / spread) in the last 0.5 s before the release."""
    p = _prm("slob_alignment", params)
    out = []
    for tw in _throw_ins(scene):
        if not tw["restart_type"].startswith("slob"):
            continue
        team = scene.offense if tw["team"] == "O" else scene.defense
        ids = [o for o in team if o != tw["thrower"]]
        if len(ids) < 4:
            continue
        a, rel = _alignment_window(scene, ids, tw["t_disposal"], tw["t_release"], p["snap_s"], p["cut_mps"])
        pts = _snapshot(scene, ids, a, rel)
        X, Y = pts[:, 0], pts[:, 1]
        sg = float(np.nanmedian([np.nanmedian(_sig_p(scene.k(o))[a : rel + 1]) for o in ids]))
        L = p["line_m"]
        xs, ys = np.abs(X - np.median(X)), np.abs(Y - np.median(Y))
        n_stack = sum(_in_spot("slob_stack_region", X[i], Y[i]) for i in range(len(ids)))
        order = np.argsort(Y)
        top, bot = order[-2:], order[:2]
        if np.all(xs < L) or np.all(ys < L):
            align, margins = "line", list(L - (xs if np.all(xs < L) else ys))
        elif n_stack >= 2:
            align, margins = "stack", [0.5]
        elif (
            abs(Y[top[0]] - Y[top[1]]) < 1.5 * L
            and abs(Y[bot[0]] - Y[bot[1]]) < 1.5 * L
            and np.mean(Y[top]) - np.mean(Y[bot]) >= 2.5
        ):
            align, margins = "box", [1.5 * L - abs(Y[top[0]] - Y[top[1]]), 1.5 * L - abs(Y[bot[0]] - Y[bot[1]])]
        else:
            align, margins = "spread", [0.0]
        conf = (
            float(np.mean(phi(np.asarray(margins) / sg)))
            * _throw_in_conf(scene, tw)
            * _qobj(scene, ids + [tw["thrower"]], rel, a, rel)
        )
        out.append(
            _ev(
                "slob_alignment",
                {"thrower": tw["thrower"]},
                tw["t_disposal"],
                a,
                rel,
                conf,
                alignment=align,
                backcourt=tw["restart_type"] == "slob_backcourt",
                name=f"SLOB {align}",
            )
        )
    return out


def detect_ato(scene, **params) -> list[Event]:
    """TRN-S11 (needs_data): ATO is a PBP join on the throw_in event's t_disposal."""
    return []


def detect_late_clock(scene, **params) -> list[Event]:
    """TRN-S12 (needs_data): needs the shot clock."""
    return []


def detect_end_of_game(scene, **params) -> list[Event]:
    """TRN-S13 (needs_data): needs the game clock and score."""
    return []


def detect_jump_ball_alignment(scene, **params) -> list[Event]:
    """TRN-S14 (needs_data): the snapshot is taken at t_toss, which needs ball height."""
    return []


def detect_ft_alignment(scene, **params) -> list[Event]:
    """TRN-S15: lane-space, perimeter and leak occupancy at the FT release proxy."""
    p = _prm("ft_alignment", params)
    zones = [
        "ft_lane_space_1",
        "ft_lane_space_2",
        "ft_lane_space_3",
        "ft_lane_open_low",
        "ft_shooter",
        "ft_perimeter_top",
        "ft_perimeter_wing",
        "ft_leak_out",
    ]
    out = []
    for ft in _ft_releases(scene):
        t = ft["t_ft"]
        a = max(0, t - frames(0.3))
        occ, pl = {}, []
        spaces = {"1": (0.8382, 1.7526), "2": (1.8034, 2.7178), "3": (2.7686, 3.683)}
        for o in scene.players():
            k = scene.k(o)
            x, y = _mean_pos(k, a, t)
            # lane spaces are thin (0.91 m): the best space within the occupancy hysteresis counts (P_in stored)
            m_best = max(
                ((_box_margin(abs(x), y, LANE_X, LANE_X + 0.9144, y0, y1), i) for i, (y0, y1) in spaces.items())
            )
            z = (
                f"ft_lane_space_{m_best[1]}"
                if m_best[0] >= -p["space_hyst_m"]
                else next((zid for zid in zones if _in_spot(zid, x, y)), None)
            )
            occ[o] = z
            if z and z.startswith("ft_lane_space"):
                pl.append(float(phi(m_best[0] / float(_sig_p(k)[t]))))
        if len(pl) < p["min_lane"]:
            continue
        conf = float(np.mean(pl)) * _qobj(scene, [ft["shooter"], "ball"], t, a, t)
        out.append(
            _ev(
                "ft_alignment",
                {"shooter": ft["shooter"]},
                t,
                a,
                t,
                conf,
                occupancy=occ,
                n_lane=len(pl),
                leakers=[o for o, z in occ.items() if z == "ft_leak_out"],
            )
        )
    return out


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------
DETECTORS = {
    "possession_change": detect_possession_change,
    "transition_phase": detect_transition_phase,
    "early_offense_window": detect_early_offense_window,
    "numbers_advantage": detect_numbers_advantage,
    "throw_in": detect_throw_in,
    "upcourt_run": detect_upcourt_run,
    "rim_run": detect_rim_run,
    "wing_lane_run": detect_wing_lane_run,
    "corner_fill": detect_corner_fill,
    "middle_lane_run": detect_middle_lane_run,
    "leak_out": detect_leak_out,
    "trailer": detect_trailer,
    "outlet_release": detect_outlet_release,
    "push": detect_push,
    "diagonal_dribble": detect_diagonal_dribble,
    "pull_back": detect_pull_back,
    "retreat": detect_retreat,
    "shot_rebound_decision": detect_shot_rebound_decision,
    "safety": detect_safety,
    "protect_rim": detect_protect_rim,
    "inbounder_step_in": detect_inbounder_step_in,
    "run_endline": detect_run_endline,
    "inbound_get_open": detect_inbound_get_open,
    "ft_lane_entry": detect_ft_lane_entry,
    "ft_release_runner": detect_ft_release_runner,
    "jump_ball_release": detect_jump_ball_release,
    "hold_for_one": detect_hold_for_one,
    "press_flash_middle": detect_press_flash_middle,
    "sideline_release": detect_sideline_release,
    "press_safety": detect_press_safety,
    "build_wall": detect_build_wall,
    "sink_to_paint": detect_sink_to_paint,
    "outlet_pass": detect_outlet_pass,
    "hit_ahead": detect_hit_ahead,
    "drag_screen": detect_drag_screen,
    "double_drag": detect_double_drag,
    "trailer_pitch_back": detect_trailer_pitch_back,
    "rim_runner_hit": detect_rim_runner_hit,
    "stop_ball": detect_stop_ball,
    "jam_rebounder": detect_jam_rebounder,
    "matchup": detect_matchup,
    "tandem_stack": detect_tandem_stack,
    "run_out": detect_run_out,
    "screen_the_inbounder": detect_screen_the_inbounder,
    "press_trap": detect_press_trap,
    "trap_breaker_pass": detect_trap_breaker_pass,
    "press_reversal": detect_press_reversal,
    "home_run_inbound": detect_home_run_inbound,
    "jump_ball_tip": detect_jump_ball_tip,
    "ft_box_out": detect_ft_box_out,
    "take_foul": detect_take_foul,
    "tag_and_recover": detect_tag_and_recover,
    "primary_break": detect_primary_break,
    "secondary_break": detect_secondary_break,
    "early_offense_sequence": detect_early_offense_sequence,
    "push_after_make": detect_push_after_make,
    "passed_up_break": detect_passed_up_break,
    "defensive_transition_scheme": detect_defensive_transition_scheme,
    "press_active": detect_press_active,
    "press_fall_back": detect_press_fall_back,
    "press_break_alignment": detect_press_break_alignment,
    "blob_alignment": detect_blob_alignment,
    "slob_alignment": detect_slob_alignment,
    "ato": detect_ato,
    "late_clock": detect_late_clock,
    "end_of_game": detect_end_of_game,
    "jump_ball_alignment": detect_jump_ball_alignment,
    "ft_alignment": detect_ft_alignment,
}
NEEDS_DATA = sorted(it["id"] for it in CFG["items"] if it.get("needs_data") and it["id"] in DETECTORS)


def detect_all(scene) -> dict:
    """Run every detector with the YAML parameters; returns {item id: [Event, ...]}."""
    return {fid: fn(scene) for fid, fn in DETECTORS.items()}
