"""Composition engine of the movement grammar: primitives -> actions -> set components -> named sets.

Reference implementation (spec tooling, not the production labeller) of
config/movement_grammar/composition.yaml, which is the single source of truth for every
threshold used here: the module reads all parameters from that file at import.

Pipeline (one clip = one Scene from mvlib.build_scene):
  1. Lattice (event_lattice): every action the engine composes, as mvlib.Event objects with a
     probability (conf). Upstream family detectors can be passed in; until they are wired, a
     minimal set of documented proxy primitives (holder runs, PASS, DHO, loose screens, cuts,
     drives, roll/pop) is built here so the engine runs stand-alone.
  2. ALIGN snapshot (align_snapshot): role-free Hungarian match of the 5 attackers to the metric
     alignment templates, mirror-aware, probabilistic (top-3 always), with a separate accept flag.
  3. Set components (iverson ... ram): chunk-level detectors that combine primitives with spot
     labels (named_spots 0.3.2, never redefined) and continuous coordinates.
  4. Matcher (matcher / probability): role-bound, timed, weighted edit distance by beam search
     over the lattice, scored per template and its mirror, one length normalisation C_hat = C / W
     for both ranking and acceptance, plus a hard floor on matched required steps.
  5. Naming, departures, segmentation, live belief and the storage row.

Frame: attacked-rim frame, metres, 29.97 fps (mvlib.DT). Stationarity uses the chi-square
statistic mvlib.Kin.stationary_s2 (< 5.99), never raw CA-RTS speed, which is biased upward at
rest. Every detector returns mvlib.Event objects; conf = window_conf x edge_factor x gap_factor
(MP-16), times the evidence probabilities of the parts a composite is built from.
"""
from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
for _p in (HERE.parent, HERE.parents[1] / "named_spots"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mvlib  # noqa: E402
import spotlib  # noqa: E402
from mvlib import DT, Event, edge_factor, frames, gap_factor, hysteresis, p_above, p_below, window_conf  # noqa: E402

CONFIG = HERE.parents[3] / "config" / "movement_grammar" / "composition.yaml"
DOC = yaml.safe_load(CONFIG.read_text())
ITEMS = {it["id"]: it for it in DOC["items"]}


def _defaults(item):
    """Parameter values of one item ({name: {value, unit}} in the YAML -> {name: value})."""
    out = {}
    for k, v in (item.get("params") or {}).items():
        out[k] = v["value"] if isinstance(v, dict) and "value" in v else v
    return out


PRM = {iid: _defaults(it) for iid, it in ITEMS.items()}
ALIGNMENTS = DOC["alignments"]
TEMPLATES = DOC["templates"]
_SPOT_DOC, SPOTS = spotlib.load()
C = spotlib.C
S2_STATIONARY = PRM["event_lattice"]["s2_stationary"]  # chi-square 2 dof, 95 %


def _prm(item_id, params):
    p = dict(PRM[item_id])
    p.update(params)
    return p


# --------------------------------------------------------------------------------------
# Geometry and small helpers
# --------------------------------------------------------------------------------------
def d3(x, y):
    """Signed distance to the three-point line (m), positive outside (named_spots is_three geometry)."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    return np.where(y <= C["BREAK_Y"], np.abs(x) - C["CORNER_X"], np.hypot(x, y) - C["ARC_R"])


def m_angle(x, y):
    """named_spots m: degrees(atan2(y, |x|)), 90 at the top of the key, same for x and -x."""
    return np.degrees(np.arctan2(y, np.abs(x)))


def in_spot(spot_id, x, y, side=None):
    """True when (x, y) carries the named_spots label (any side, or 'right'/'left' for mirrored spots)."""
    if not (np.isfinite(x) and np.isfinite(y)):
        return False
    labels = SPOTS[spot_id].labels(float(x), float(y))
    if side is None:
        return bool(labels)
    return f"{spot_id}_{side}" in labels


def pos(scene, oid, t):
    k = scene.kins[oid]
    return float(k.x[t]), float(k.y[t])


def ball_pos(scene, t):
    if scene.ball is None or t < 0 or t >= scene.n:
        return (np.nan, np.nan)
    return float(scene.ball.x[t]), float(scene.ball.y[t])


def _clip(t, n):
    return int(max(0, min(n - 1, t)))


def _stationary_p(k):
    """Per-frame P(stationary) surrogate from the MP-09 statistic s2 (chi-square 2 dof).

    Logistic step centred on the 95 % critical value 5.99 with width event_lattice.stat_logistic_width
    (proposal): 1 well below the gate, 0 well above, NaN where the track is not smoothed.
    """
    s2 = k.stationary_s2
    z = np.clip((s2 - S2_STATIONARY) / PRM["event_lattice"]["stat_logistic_width"], -50.0, 50.0)
    p = 1.0 / (1.0 + np.exp(z))
    p[~np.isfinite(s2)] = np.nan
    return p


def _factor(scene, oids, a, b, t):
    """MP-16 edge x gap factor for a composite: the worst actor decides."""
    f = 1.0
    for o in oids:
        if o is None or o not in scene.kins:
            continue
        k = scene.kins[o]
        f = min(f, edge_factor(k, _clip(t, scene.n)) * gap_factor(k, _clip(a, scene.n), _clip(b, scene.n)))
    return float(f)


def _sigma_track(scene, oids, t):
    """Calibrated position sigma (m) at frame t, worst of the given objects (MP-09 K_CAL inflation)."""
    s = 0.0
    for o in oids:
        k = scene.kins[o]
        v = k.var_p[_clip(t, scene.n)]
        if np.isfinite(v):
            s = max(s, mvlib.K_CAL * math.sqrt(v))
    return s if s > 0 else 0.3


def _first_holder_frame(scene):
    for t in range(scene.n):
        if _H(scene)[t] is not None:
            return t
    return None


def _ball_side(scene, t, dead=None):
    """Side of the ball (+1 right, -1 left, 0 inside the mirror.dead_band_m band or unknown)."""
    dead = PRM["mirror"]["dead_band_m"] if dead is None else dead
    bx = ball_pos(scene, t)[0]
    if not np.isfinite(bx) or abs(bx) < dead:
        return 0
    return 1 if bx > 0 else -1


def _cache(scene):
    return scene.__dict__.setdefault("_composition_cache", {})


# --------------------------------------------------------------------------------------
# Event lattice: proxy primitives (event_lattice item). Replaced by the owning families'
# detectors when they are passed in through build_lattice(events=...).
# --------------------------------------------------------------------------------------
def _defender_margin(scene):
    """Per-frame distance (m) from the ball to the nearest defender, or None when the scene has no defenders."""
    cache = _cache(scene)
    if "dmin_def" not in cache:
        if scene.ball is None or not scene.defense:
            cache["dmin_def"] = None
        else:
            X = np.vstack([scene.kins[o].x for o in scene.defense])
            Y = np.vstack([scene.kins[o].y for o in scene.defense])
            Dd = np.hypot(X - scene.ball.x[None, :], Y - scene.ball.y[None, :])
            Dd[~np.isfinite(Dd)] = 9e9
            cache["dmin_def"] = Dd.min(axis=0)
            cache["dmin_def_id"] = [scene.defense[i] for i in Dd.argmin(axis=0)]
    return cache["dmin_def"]


def _def_gate(scene, oid, t):
    """Margin (m) by which a defender must be nearer to the ball than attacker oid to take control at frame t:
    possession_split.def_margin_m + def_noise_k x sigma_dist(attacker, that defender) (pair noise, MP-19)."""
    p = PRM["possession_split"]
    d_id = _cache(scene)["dmin_def_id"][t]
    v = scene.kins[oid].var_p[t] + scene.kins[d_id].var_p[t]
    sd = mvlib.K_CAL * math.sqrt(max(float(v), 1e-6)) if np.isfinite(v) else np.nan
    return p["def_margin_m"] + p["def_noise_k"] * (sd if np.isfinite(sd) else 0.3)


def _set_p(k, p):
    """Per-frame P(screener set), loop 4 L6: the larger of the MP-09 stationarity surrogate (_stationary_p) and
    P(speed < scr_set_max_mps) with the calibrated speed sigma. The s2 test asks whether any motion is significant,
    so with precise tracking (SportVU, sigma ~ 0.15 m told) a screener shuffling at 0.4-0.8 m/s failed it while the
    same screen passed at sigma_p 0.3-0.5; the physical bound keeps 'set' the same at every noise level. NaN where
    the track is not smoothed."""
    ps = _stationary_p(k)
    pv = p_below(k.speed, p["scr_set_max_mps"], k.sigma_speed)
    out = np.fmax(ps, pv)
    out[~np.isfinite(ps)] = np.nan
    return out


def _H(scene):
    """Sticky ball holder per frame (proxy): mvlib's nearest-attacker holder with switch hysteresis.

    The current holder keeps the ball while it is within HOLD_R of him unless another attacker is nearer by
    >= hold_switch_margin_m; this removes the flicker to a screener standing next to the handler.
    Catch rule (loop 1 F7): a NEW holder run cannot start while the ball moves relative to that player faster
    than catch_max_ball_mps (CA-RTS ball velocity, Q_BALL): a ball in flight past a cutter or a roller under the
    rim is not his until it slows down with him.
    """
    cache = _cache(scene)
    if "holder" in cache:
        return cache["holder"]
    p = PRM["event_lattice"]
    out = np.array([None] * scene.n, dtype=object)
    if scene.ball is not None:
        X = np.vstack([scene.kins[o].x for o in scene.offense])
        Y = np.vstack([scene.kins[o].y for o in scene.offense])
        D = np.hypot(X - scene.ball.x[None, :], Y - scene.ball.y[None, :])
        D[~np.isfinite(D)] = 9e9
        VX = np.vstack([scene.kins[o].vx for o in scene.offense])
        VY = np.vstack([scene.kins[o].vy for o in scene.offense])
        REL = np.hypot(scene.ball.vx[None, :] - VX, scene.ball.vy[None, :] - VY)
        REL[~np.isfinite(REL)] = 0.0
        DM = _defender_margin(scene)
        prev = None
        for t in range(scene.n):
            if not np.isfinite(scene.ball.x[t]):
                prev = None
                continue
            j = int(np.argmin(D[:, t]))
            best = scene.offense[j] if D[j, t] <= mvlib.HOLD_R else None
            if prev is not None:
                dp = D[scene.offense.index(prev), t]
                if dp <= mvlib.HOLD_R and (best is None or D[j, t] > dp - p["hold_switch_margin_m"]):
                    best = prev
            if best is not None and best != prev and REL[scene.offense.index(best), t] > p["catch_max_ball_mps"]:
                best = None  # ball still in flight relative to him: no catch yet
            # loop 4 L1: a defender clearly nearer to the ball than the attacker holds it (steal, defensive rebound,
            # the defence's own possession in a multi-possession clip): no offensive holder
            if best is not None and DM is not None and DM[t] < D[scene.offense.index(best), t] - _def_gate(scene, best, t):
                best = None
            out[t] = best
            prev = best
    # drop control runs shorter than hold_min_frames (noise flicker), then bridge short gaps
    min_f = int(p["hold_min_frames"])
    t = 0
    while t < scene.n:
        if out[t] is None:
            t += 1
            continue
        j = t
        while j + 1 < scene.n and out[j + 1] == out[t]:
            j += 1
        if j - t + 1 < min_f:
            out[t:j + 1] = None
        t = j + 1
    cache["holder"] = out
    return out


def _soft_holder(scene, k):
    """Loop 5 C2: per-frame holder with hysteresis - _H plus the frames by which _extend_holds (k x sigma_dist around
    HOLD_R) extends each holder run; the hard holder is unchanged where it names someone. k <= 0 returns _H."""
    H = _H(scene)
    if k <= 0:
        return H
    cache = _cache(scene)
    key = ("soft_holder", float(k))
    if key not in cache:
        out = np.array(H, dtype=object)
        for h, a, b in _extend_holds(scene, holder_runs(scene), k):
            for t in range(a, b + 1):
                if out[t] is None:
                    out[t] = h
        cache[key] = out
    return cache[key]


def holder_runs(scene, p=None):
    """Runs (holder, a, b) of ball control from scene.holder, short gaps bridged, short runs dropped."""
    p = p or PRM["event_lattice"]
    bridge, min_f = int(p["hold_bridge_frames"]), 1
    raw, cur = [], None
    for t in range(scene.n):
        h = _H(scene)[t]
        if h is None:
            continue
        if cur and cur[0] == h and t - cur[2] <= bridge + 1:
            cur[2] = t
        else:
            if cur:
                raw.append(tuple(cur))
            cur = [h, t, t]
    if cur:
        raw.append(tuple(cur))
    runs = [r for r in raw if r[2] - r[1] + 1 >= min_f]
    merged = []
    for r in runs:
        if merged and merged[-1][0] == r[0]:
            merged[-1] = (r[0], merged[-1][1], r[2])
        else:
            merged.append(r)
    return merged


def _transfer_events(scene, p):
    """PASS and DHO from consecutive holder runs a -> b (a != b)."""
    out = []
    runs = holder_runs(scene, p)
    if scene.ball is None:
        return out, runs
    for (ha, a0, a1), (hb, b0, b1) in zip(runs, runs[1:]):
        if ha == hb:
            continue
        air_s = (b0 - a1) * DT
        bx0, by0 = ball_pos(scene, a1)
        bx1, by1 = ball_pos(scene, b0)
        travel = math.hypot(bx1 - bx0, by1 - by0)
        # giver-receiver gap: minimum distance within +-dho_gap_window_s of the transfer (the hand-off moment)
        w0, w1 = _clip(a1 - frames(p["dho_gap_window_s"]), scene.n), _clip(b0 + frames(p["dho_gap_window_s"]), scene.n)
        gap_ab = float(np.nanmin(mvlib.dist(scene.kins[ha], scene.kins[hb])[w0:w1 + 1]))
        # holder certainty around the transfer: ball within HOLD_R of the holder (p_below with pair sigma)
        pr = []
        hf = int(p["hold_cert_frames"])
        for oid, lo, hi in ((ha, max(a0, a1 - hf), a1), (hb, b0, min(b1, b0 + hf))):
            k = scene.kins[oid]
            d = np.hypot(scene.ball.x[lo:hi + 1] - k.x[lo:hi + 1], scene.ball.y[lo:hi + 1] - k.y[lo:hi + 1])
            sig = mvlib.sigma_dist(k, scene.ball)[lo:hi + 1]
            pr.append(window_conf(p_below(d, mvlib.HOLD_R + 0.5, sig), 0, len(d) - 1))
        base = float(np.mean(pr)) * _factor(scene, [ha, hb], a1, b0, (a1 + b0) // 2)
        # DHO (loop 1 F9): close giver-receiver gap and either a short air time or, when the ball barely travelled
        # (< pass_min_flight_m), an air time up to dho_max_air_short_travel_s (holder flicker at high noise);
        # a long air time lowers the conf through p_below(air_s, dho_max_air_short_travel_s, dho_air_sigma_s)
        # (about 1.0 at 0 s, 0.98 at 0.3 s, 0.5 at 0.6 s) instead of a hard cut.
        # A short-travel transfer (it cannot be a PASS) also gets a noise-widened gap gate: smoother lag at the
        # hand-off inflates the smoothed giver-receiver gap (sim: true 0.64 m reads 0.8-1.2 m at sigma_p 0.3 and
        # 1.4-1.9 m at 0.5), far beyond sigma_dist; gate dho_max_gap_m + dho_gap_noise_k x sigma_dist, conf x
        # p_below(gap, that gate, sigma_dist).
        short_travel = not (travel >= p["pass_min_flight_m"])
        sd = float(np.nanmax(mvlib.sigma_dist(scene.kins[ha], scene.kins[hb])[w0:w1 + 1]))
        gap_wide = p["dho_max_gap_m"] + p["dho_gap_noise_k"] * sd
        close = gap_ab <= p["dho_max_gap_m"] or (short_travel and gap_ab <= gap_wide)
        # loop 4 L10: a holder change with the ball within dho_min_r_m of the rim is a tip / rebound scrum (the
        # ball is at the rim above the players), not a hand-off
        if math.hypot(bx1, by1) < p["dho_min_r_m"]:
            close = False
        if close and (air_s <= p["dho_max_air_s"] or (short_travel and air_s <= p["dho_max_air_short_travel_s"])):
            p_air = float(p_below(air_s, p["dho_max_air_short_travel_s"], p["dho_air_sigma_s"]))
            p_gap = 1.0 if gap_ab <= p["dho_max_gap_m"] else float(p_below(gap_ab, gap_wide, sd))
            out.append(Event("DHO", {"giver": ha, "receiver": hb}, b0, a1, b0, base * p["p_dho"] * p_air * p_gap,
                             {"air_s": air_s, "gap_m": gap_ab, "travel_m": travel, "evidence": "proxy"}))
        elif travel >= p["pass_min_flight_m"]:
            sx, sy = pos(scene, ha, a1)
            rx, ry = pos(scene, hb, b0)
            skip = (sx * rx < 0) and abs(rx - sx) > p["skip_min_dx_m"]
            out.append(Event("PASS", {"passer": ha, "receiver": hb}, a1, a1, b0, base * p["p_pass"],
                             {"air_s": air_s, "travel_m": travel, "skip": bool(skip), "evidence": "proxy"}))
    return out, runs


def _moves(scene, oid, p):
    """Moving intervals of one player (CA-RTS speed hysteresis), onset backtracked to the stay level."""
    k = scene.kins[oid]
    spd = np.nan_to_num(k.speed, nan=0.0)
    ivs = hysteresis(spd > p["move_enter_mps"], spd > p["move_stay_mps"], p["move_min_s"], int(p["move_bridge_frames"]))
    out = []
    for a, b in ivs:
        while a > 0 and spd[a - 1] > p["move_stay_mps"]:
            a -= 1
        out.append((a, b))
    return out


def _cut_events(scene, runs, p):
    """CUT: off-ball move with displacement >= cut_min_disp_m (path class left to the cuts family)."""
    out = []
    held = {}
    for h, a, b in runs:
        for t in range(a, b + 1):
            held[t] = h
    for o in scene.offense:
        k = scene.kins[o]
        for a, b in _moves(scene, o, p):
            if sum(held.get(t) == o for t in range(a, b + 1)) > 0.5 * (b - a + 1):
                continue  # the holder's moves are drives / dribbles, not cuts
            disp = math.hypot(k.x[b] - k.x[a], k.y[b] - k.y[a])
            if disp < p["cut_min_disp_m"]:
                continue
            spd = k.speed
            conf = window_conf(p_above(spd, p["move_stay_mps"], k.sigma_speed), a, b) * _factor(scene, [o], a, b, a)
            cls = "basket" if math.hypot(k.x[b], k.y[b]) < p["basket_cut_end_r_m"] else "other"
            out.append(Event("CUT", {"cutter": o}, a, a, b, conf * p["p_cut"],
                             {"start": (float(k.x[a]), float(k.y[a])), "end": (float(k.x[b]), float(k.y[b])),
                              "cls": cls, "disp_m": disp, "evidence": "proxy"}))
    return out


def _is_flare(ku, t, t_a, t_b):
    """Flare by geometry (loop 1 F14): the user's heading turns by >= flare_min_turn_deg between the mean velocity
    of his approach over [t - flare_pre_s, t] and of his exit over [t, t_b] (pre / post means skip the plant phase,
    MP-13; the minimum distance often falls on the way out, so the approach window is longer than the exit
    window), and after the screen he runs toward the outside (|x| increasing) with |v_x| >= |v_y|."""
    p = PRM["event_lattice"]
    t_a = max(0, t - frames(p["flare_pre_s"]))
    pre = (np.nanmean(ku.vx[t_a:t + 1]), np.nanmean(ku.vy[t_a:t + 1]))
    post = (np.nanmean(ku.vx[t:t_b + 1]), np.nanmean(ku.vy[t:t_b + 1]))
    if not all(np.isfinite(v) for v in pre + post) or math.hypot(*pre) < 0.5 or math.hypot(*post) < 0.5:
        return False
    turn = abs((math.degrees(math.atan2(post[1], post[0])) - math.degrees(math.atan2(pre[1], pre[0])) + 180) % 360 - 180)
    outward = post[0] * np.sign(ku.x[t]) > 0
    return bool(turn >= p["flare_min_turn_deg"] and outward and abs(post[0]) >= abs(post[1]))


def _screen_events(scene, p):
    """Loose screen evidence (proxy): stationary screener, moving teammate passes within contact range.

    t_ref = minimum screener-user distance (t_ref_proxy: the defender is not used here).
    Direction class from the user's displacement over +-0.5 s (offense_full section 0.2 classes).
    """
    out = []
    n = scene.n
    half = frames(p["scr_dir_half_s"])
    on_f = int(p["on_ball_frames"])
    HS = _soft_holder(scene, p["on_ball_hold_ext_k"])
    for s in scene.offense:
        ks = scene.kins[s]
        pstat = _set_p(ks, p)
        for u in scene.offense:
            if u == s:
                continue
            ku = scene.kins[u]
            d = mvlib.dist(ks, ku)
            sdd = mvlib.sigma_dist(ks, ku)
            close = np.nan_to_num(d, nan=99.0) <= p["scr_contact_m"]
            ivs = hysteresis(close, close, 0.0, int(p["contact_bridge_frames"]))
            # loop 5 C2: ball-screen contacts also from a noise-widened gate scr_contact_m + scr_on_contact_k x
            # sigma_dist (position noise biases the minimum pair distance upward: SportVU --noise 0.5 lost 17 of 81
            # ball screens with the noisy minimum at 1.22-1.53 m); a widened interval that holds no frame inside
            # scr_contact_m is kept only as an on-ball screen below (off-ball screens keep the 1.2 m gate)
            if p["scr_on_contact_k"] > 0:
                wide = np.nan_to_num(d, nan=99.0) <= p["scr_contact_m"] + p["scr_on_contact_k"] * np.nan_to_num(sdd, nan=0.0)
                ivs += [(a, b) for a, b in hysteresis(wide, wide, 0.0, int(p["contact_bridge_frames"])) if not close[a:b + 1].any()]
            for a, b in sorted(ivs):
                t = a + int(np.nanargmin(d[a:b + 1]))
                widened = not close[t]
                w0, w1 = _clip(t - frames(p["scr_stat_pre_s"]), n), _clip(t + frames(p["scr_stat_post_s"]), n)
                # loop 4 L6: the screener must be set in some window of the same length that ends between
                # scr_set_lookback_s before t and t + scr_stat_post_s (real screeners set, then roll or slip while
                # the handler is still coming off: the minimum handler distance often falls in the roll)
                # loop 4 L8: ... or up to scr_set_lookahead_s after it: the screen acts on the user's defender, who
                # trails the user by 0.2-0.4 s, and a screener who sprints in often plants only as the user passes
                stat = max(window_conf(pstat, _clip(e - (w1 - w0), n), e)
                           for e in range(_clip(t - frames(p["scr_set_lookback_s"]) + (w1 - t), n),
                                          _clip(w1 + frames(p["scr_set_lookahead_s"]), n) + 1))
                if stat < p["scr_stat_frac"]:
                    continue
                if not (np.nanmean(ku.speed[_clip(t - on_f, n):_clip(t + on_f, n) + 1]) >= p["scr_user_min_mps"]):
                    continue
                t_a, t_b = _clip(t - half, n), _clip(t + half, n)
                dx, dy = ku.x[t_b] - ku.x[t_a], ku.y[t_b] - ku.y[t_a]
                if math.hypot(dx, dy) < p["scr_user_min_disp_m"]:
                    continue
                if _H(scene)[t] == s:
                    continue  # the screener holds the ball: that is a DHO / keep, not a screen
                # loop 5 C2: on-ball uses the holder with hysteresis (_soft_holder): a dribbled ball under noise leaves
                # the hard-radius holder empty around the screen (SportVU --noise 0.5: 10 of 81 ball screens lost so)
                on_ball = any(HS[_clip(t + j, n)] == u for j in range(-on_f, on_f + 1))
                # ... and a widened contact (minimum distance beyond scr_contact_m) needs the screen's actual contact:
                # the handler's defender (nearest defender over the last scr_on_def_lookback_s) passes within
                # scr_on_wide_def_m of the screener in [t - scr_stat_pre_s, t + scr_on_def_after_s]; without defenders
                # (synthetic) a widened contact is never a screen (a handler passing a teammate 1.5 m away is a miss)
                if widened and not (on_ball and _defender_meets(scene, s, u, t, p)):
                    continue
                if on_ball:
                    # loop 4 L7: a ball screen is a half-court action set away from the rim. A 'screen' with the
                    # screener inside scr_on_min_r_m of the rim is a shot / rebound scrum (the 'holder' is a shooter
                    # or rebounder with the ball at the rim) and one beyond the half-court line by more than
                    # scr_on_max_past_half_m is bring-up / inbound traffic in the backcourt
                    if ks.r[t] < p["scr_on_min_r_m"] or ks.y[t] > C["HALF_Y"] + p["scr_on_max_past_half_m"]:
                        continue
                    kind = "SCR.on"
                else:
                    flare = _is_flare(ku, t, t_a, t_b)
                    if abs(dx) > p["cross_dx_ratio"] * abs(dy) and ks.y[t] < p["cross_max_y_m"]:
                        kind = "SCR.cross"
                    elif flare:
                        kind = "SCR.flare"
                    elif dy > 0:
                        kind = "SCR.down"
                    else:
                        kind = "SCR.back"
                # loop 5 C2: the contact probability of a ball screen uses scr_on_pc_k x sigma_dist (the CA-RTS posterior
                # sigma understates the smoothed error of AR(1)-correlated noise ~1.7x at sigma_p 0.3-0.5)
                pc = float(p_below(d[t], p["scr_contact_m"], (p["scr_on_pc_k"] if on_ball else 1.0) * sdd[t]))
                conf = stat * pc * _factor(scene, [s, u], w0, w1, t)
                out.append(Event(kind, {"screener": s, "user": u}, t, w0, max(w1, t_b), conf * p["p_screen_loose"],
                                 {"d_min_m": float(d[t]), "stat_conf": stat, "t_ref_proxy": True, "evidence": "loose",
                                  "spot": (float(ks.x[t]), float(ks.y[t]))}))
    return out


def _handler_defender(scene, u, t, p):
    """Loop 6 C2: the defender guarding attacker u at frame t, by sustained matchup.

    With the defense family's matchup (detect_all(scene, matchup=...) -> _cache 'matchup_family', {defender: per-frame
    attacker id}): the defender assigned to u on the most frames of [t - scr_on_def_match_s, t]. Otherwise (the measured
    default): the defender with the lowest mean distance to u over [t - scr_on_def_match_s, t - scr_on_def_match_end_s]
    (the loop-5 nearest over the last scr_on_def_lookback_s when that window is empty, at a clip start), and only when
    his mean distance to u over the last scr_on_def_lookback_s is <= scr_on_def_max_m. A 1 s nearest picked the screener's hedging defender over the handler's own
    sagging defender (he stands between the screener and the handler's path) and then 'met' the screener trivially."""
    if not scene.defense:
        return None
    n = scene.n
    lo = _clip(t - frames(p["scr_on_def_match_s"]), n)
    hi = _clip(t - frames(p["scr_on_def_match_end_s"]), n)
    mf = _cache(scene).get("matchup_family")
    if mf:
        cnt = {d: int(sum(1 for j in range(lo, t + 1) if j < len(mf[d]) and mf[d][j] == u)) for d in scene.defense if d in mf}
        if cnt and max(cnt.values()) > 0:
            return max(cnt, key=lambda d: (cnt[d], d))
    lo1 = _clip(t - frames(p["scr_on_def_lookback_s"]), n)
    if hi <= lo:
        lo, hi = lo1, t
    ku = scene.kins[u]

    def mean_d(d, a, b):
        x = mvlib.dist(ku, scene.kins[d])[a:b + 1]
        return float(np.nanmean(x)) if np.any(np.isfinite(x)) else np.nan
    md = [mean_d(d, lo, hi) for d in scene.defense]
    if not np.any(np.isfinite(md)):
        return None
    d_id = scene.defense[int(np.nanargmin(md))]
    # he must actually be on the handler now: mean distance over the last scr_on_def_lookback_s <= scr_on_def_max_m
    # (the loop-5 2 x scr_contact_m cap; over the long window a defender trailing a handler who comes from far away
    # averages more)
    return d_id if mean_d(d_id, lo1, t) <= p["scr_on_def_max_m"] else None


def _defender_meets(scene, s, u, t, p, radius=None):
    """Loop 5 C2: True when u's defender (_handler_defender, loop 6 C2: sustained matchup) comes within
    scr_on_wide_def_m (or radius) of screener s in [t - scr_stat_pre_s, t + scr_on_def_after_s]."""
    d_id = _handler_defender(scene, u, t, p)
    if d_id is None:
        return False
    n = scene.n
    kd, ks = scene.kins[d_id], scene.kins[s]
    a, b = _clip(t - frames(p["scr_stat_pre_s"]), n), _clip(t + frames(p["scr_on_def_after_s"]), n)
    dd = mvlib.dist(kd, ks)[a:b + 1]
    r = p["scr_on_wide_def_m"] if radius is None else radius
    return bool(np.any(np.isfinite(dd))) and float(np.nanmin(dd)) <= r


def _drive_events(scene, runs, p):
    """DRIVE: a holder run in which r goes from > drive_start_r_m to < drive_end_r_m (offense_full 0.2)."""
    out = []
    for h, a, b in runs:
        k = scene.kins[h]
        r = k.r
        inside = np.flatnonzero(r[a:b + 1] < p["drive_end_r_m"])
        if len(inside) == 0:
            continue
        f2 = a + int(inside[0])
        outside = np.flatnonzero(r[a:f2] > p["drive_start_r_m"])
        if len(outside) == 0:
            continue
        f1 = a + int(outside[-1])
        while f1 > a and k.v_r[f1 - 1] > p["drive_backtrack_vr_mps"]:
            f1 -= 1
        x2, y2 = float(k.x[f2]), float(k.y[f2])
        direction = "baseline" if y2 <= p["drive_baseline_y_m"] else "middle"
        conf = window_conf(p_above(k.v_r, 0.0, k.sigma_speed), f1, f2) * _factor(scene, [h], f1, f2, f1)
        out.append(Event("DRIVE", {"handler": h}, f1, f1, f2, conf * p["p_drive"],
                         {"t_rim": f2, "direction": direction, "side": 1 if x2 >= 0 else -1, "evidence": "proxy"}))
    return out


def _roll_pop_events(scene, screens, p):
    """ROLL / POP after an on-ball screen (motion_starts section 0.3 definitions); t_ref = screen moment."""
    out = []
    n = scene.n
    for e in screens:
        if e.kind != "SCR.on":
            continue
        s, h, t = e.actors["screener"], e.actors["user"], e.t0
        k = scene.kins[s]
        r0 = float(k.r[t])
        w_roll = _clip(t + frames(p["roll_window_s"]), n)
        rr = k.r[t:w_roll + 1]
        hit = np.flatnonzero(rr <= p["roll_end_r_m"])
        if len(hit) and float(rr[hit[0]]) - r0 <= -p["roll_min_dr_m"]:
            tb = t + int(hit[0])
            conf = e.conf * _factor(scene, [s], t, tb, t)
            out.append(Event("ROLL", {"screener": s, "handler": h}, t, t, tb, conf, {"parent": "SCR.on", "evidence": "proxy"}))
            continue
        w_pop = _clip(t + frames(p["pop_window_s"]), n)
        rp = k.r[t:w_pop + 1]
        dh = mvlib.dist(k, scene.kins[h])
        own = float(np.nanmax(np.hypot(k.x[t:w_pop + 1] - k.x[t], k.y[t:w_pop + 1] - k.y[t])))
        # pop: the screener himself moves >= pop_min_away_m, away from the handler, never inside pop_min_r_inside_m
        if (np.nanmin(rp) >= p["pop_min_r_inside_m"] and rp[-1] >= p["pop_end_r_m"] and rp[-1] - r0 >= 0
                and own >= p["pop_min_away_m"] and dh[w_pop] > dh[t]):
            out.append(Event("POP", {"screener": s, "handler": h}, t, t, w_pop, e.conf, {"parent": "SCR.on", "evidence": "proxy"}))
    return out


def primitives(scene, **params):
    """Proxy primitive lattice for a scene (cached per parameter set)."""
    p = _prm("event_lattice", params)
    key = ("prims", repr(sorted(p.items())))
    cache = _cache(scene)
    if key not in cache:
        transfers, runs = _transfer_events(scene, p)
        screens = _screen_events(scene, p)
        evs = transfers + screens + _cut_events(scene, runs, p) + _drive_events(scene, runs, p) + _roll_pop_events(scene, screens, p)
        evs = [e for e in evs if e.conf >= p["p_min_keep"]]
        evs.sort(key=lambda e: (e.t0, e.kind, tuple(sorted(e.actors.items()))))
        cache[key] = (evs, runs)
    return cache[key][0]


def cold_start_p(e):
    """Fallback probability per evidence class when an upstream event carries no calibrated p."""
    tab = PRM["event_lattice"]["cold_start_p"]
    if e.conf is not None and np.isfinite(e.conf) and e.conf > 0:
        return float(e.conf)
    return float(tab.get(e.attrs.get("evidence", "proposal"), tab["proposal"]))


def build_lattice(scene, events=None, components=True):
    """The lattice the matcher consumes: primitives (proxy or upstream) + set-component events.

    events: optional upstream Events (other families). When given they replace the proxies.
    Low-probability events (< p_min_keep) are dropped from the lattice (logged as unmatched).
    """
    key = ("lattice", id(events) if events is not None else None, components)
    cache = _cache(scene)
    if key in cache:
        return cache[key]
    p = PRM["event_lattice"]
    base = list(events) if events is not None else primitives(scene)
    for e in base:
        e.conf = cold_start_p(e)
    base = [e for e in base if e.conf >= p["p_min_keep"]]
    lat = list(base)
    if components:
        for cid in COMPONENTS:
            lat += DETECTORS[cid](scene)
    lat.sort(key=lambda e: (e.t0, e.kind))
    cache[key] = lat
    return lat


def _of(lat, *kinds):
    return [e for e in lat if any(e.kind == k or e.kind.startswith(k + ".") for k in kinds)]


def _screen_like(scene):
    return [e for e in primitives(scene) if e.kind.startswith("SCR.")]


def _contacts(scene, mover, t_a, t_b, p, spot_test=None):
    """Teammates the mover passes within scr_contact_m of while they are stationary (loose screen evidence).

    Returns [(screener, t_ref, conf)] sorted by time; spot_test(x, y) filters the screener location.
    """
    out = []
    n = scene.n
    km = scene.kins[mover]
    lp = PRM["event_lattice"]
    for s in scene.offense:
        if s == mover:
            continue
        ks = scene.kins[s]
        d = mvlib.dist(km, ks)[t_a:t_b + 1]
        if len(d) == 0 or not np.any(np.isfinite(d)):
            continue
        j = int(np.nanargmin(d))
        t = t_a + j
        contact_m = p.get("contact_m", lp["scr_contact_m"])
        if d[j] > contact_m:
            continue
        w0, w1 = _clip(t - frames(lp["scr_stat_pre_s"]), n), _clip(t + frames(lp["scr_stat_post_s"]), n)
        stat = window_conf(_stationary_p(ks), w0, w1)
        if stat < lp["scr_stat_frac"]:
            continue
        if spot_test is not None and not spot_test(float(ks.x[t]), float(ks.y[t])):
            continue
        pc = float(p_below(d[j], contact_m, mvlib.sigma_dist(km, ks)[t]))  # same distance that gates (loop 1 F3)
        out.append((s, t, stat * pc))
    out.sort(key=lambda z: z[1])
    return out


# --------------------------------------------------------------------------------------
# ALIGN snapshot (align_snapshot)
# --------------------------------------------------------------------------------------
PERMS = np.array(list(itertools.permutations(range(5))))


def _align_variants():
    """Every alignment template in both mirrors (asymmetric ones) -> list of (code, mirrored, Q, slots)."""
    out = []
    for a in ALIGNMENTS:
        Q = np.array([[pp[0], pp[1]] for pp in a["positions"]], float)
        slots = [pp[2] for pp in a["positions"]]
        out.append((a["code"], False, Q, slots))
        if a.get("mirror", "symmetric") == "asymmetric":
            Qm = Q.copy()
            Qm[:, 0] *= -1
            out.append((a["code"], True, Qm, [s.replace("_r", "_x").replace("_l", "_r").replace("_x", "_l") for s in slots]))
    return out


ALIGN_VARIANTS = _align_variants()


def align_frame(scene, t, p=None):
    """Score every alignment at frame t. Returns {code: (err_m, sum_d2, mirrored, perm, slots)} best mirror per code."""
    p = p or PRM["align_snapshot"]
    P = np.array([pos(scene, o, t) for o in scene.offense[:5]], float)
    if len(P) < 5:
        P = np.vstack([P, np.full((5 - len(P), 2), np.nan)])
    best = {}
    for code, mir, Q, slots in ALIGN_VARIANTS:
        D = np.hypot(P[:, None, 0] - Q[None, :, 0], P[:, None, 1] - Q[None, :, 1])
        D[~np.isfinite(D)] = p["missing_slot_penalty_m"]  # occluded attacker: fixed penalty for his slot
        cost = (D[np.arange(5)[None, :], PERMS] ** 2).sum(axis=1)
        i = int(np.argmin(cost))
        dd = D[np.arange(5), PERMS[i]]
        err = float(dd.mean())
        if code not in best or err < best[code][0]:
            best[code] = (err, float((dd ** 2).sum()), mir, PERMS[i], slots)
    return best


def _align_probs(best, p):
    """Softmax over alignments (best mirror each) plus the 'free/motion' class (always emitted)."""
    names = list(best) + ["free"]
    logl = [-best[c][1] / (2 * p["slot_sigma_m"] ** 2) for c in best] + [-5 * p["accept_err_m"] ** 2 / 2]
    logl = np.array(logl)
    pr = np.exp(logl - logl.max())
    pr /= pr.sum()
    order = np.argsort(-pr)
    return [(names[i], float(pr[i])) for i in order]


def _frontcourt_frame(scene, p):
    if scene.ball is None:
        return None
    fc = np.nan_to_num(scene.ball.y, nan=99.0) <= C["HALF_Y"]
    need = int(p["frontcourt_hold_frames"])
    run = 0
    for t in range(scene.n):
        run = run + 1 if fc[t] else 0
        if run >= need:
            return t - need + 1
    return None


def detect_align_snapshot(scene, **params):
    """ALIGN snapshot (CE-R06, fixed): trigger, 1.5 s scan, Hungarian per frame, top-3 probs, accept flag."""
    p = _prm("align_snapshot", params)
    n = scene.n
    t_front = _frontcourt_frame(scene, p)
    if t_front is None or len(scene.offense) < 4:
        return []
    trig, how = None, "snap"
    hold = int(p["trigger_hold_frames"])
    for t in range(t_front, n):
        h = _H(scene)[t]
        bx, by = ball_pos(scene, t)
        if h is None or not in_spot("alignment_snap_zone", bx, by):
            continue
        spd = scene.kins[h].speed
        ok = hysteresis(np.nan_to_num(spd, nan=9) < p["trigger_enter_mps"], np.nan_to_num(spd, nan=9) <= p["trigger_exit_mps"],
                        (hold - 1) * DT)
        hit = [a for a, b in ok if a <= t <= b]
        if hit:
            trig = max(hit[0], t)
            break
    if trig is None:
        passes = [e for e in primitives(scene) if e.kind == "PASS" and e.t0 >= t_front]
        if passes:
            trig, how = passes[0].t0, "first_pass"
        else:
            trig, how = _clip(t_front + frames(p["fallback_after_cross_s"]), n), "crossing_plus"
    f0, f1 = _clip(trig - frames(p["scan_pre_s"]), n), _clip(trig + frames(p["scan_post_s"]), n)
    scan = list(range(f0, f1 + 1, int(p["scan_stride_frames"])))
    rows = []
    for f in scan:
        best = align_frame(scene, f, p)
        order = sorted(best, key=lambda c: best[c][0])
        rows.append((f, order[0], best[order[0]][0], best[order[1]][0], best))
    gmin = min(r[2] for r in rows)
    pick = next(r for r in rows if r[2] <= gmin + p["snap_tie_m"])
    f, code, err, err2, best = pick
    # stability: longest run of consecutive evaluated frames with the same best code
    stable, run = 0, 0
    for r in rows:
        run = run + 1 if r[1] == code else 0
        stable = max(stable, run)
    probs = _align_probs(best, p)
    margin = err2 - err
    accepted = err <= p["accept_err_m"] and margin >= p["accept_margin_m"] and stable >= p["stable_frames"]
    _, _, mirrored, perm, slots = best[code]
    actors = {slots[perm[i]]: scene.offense[i] for i in range(min(5, len(scene.offense)))}
    p_top = dict(probs).get(code, 0.0)
    conf = p_top * _factor(scene, scene.offense, f0, f1, f)
    disp = next(a["display"] for a in ALIGNMENTS if a["code"] == code)
    return [Event("align", actors, f, f0, f1, conf,
                  {"code": code, "display": disp, "probs_top3": probs[:3], "err_m": err, "margin_m": margin,
                   "accepted": bool(accepted), "mirrored": bool(mirrored), "stable_frames": stable,
                   "trigger": how, "trigger_f": trig})]


def _align_accepted_at(scene, t, p=None):
    p = p or PRM["align_snapshot"]
    best = align_frame(scene, t, p)
    order = sorted(best, key=lambda c: best[c][0])
    err, err2 = best[order[0]][0], best[order[1]][0]
    return (err <= p["accept_err_m"] and err2 - err >= p["accept_margin_m"]), order[0]


# --------------------------------------------------------------------------------------
# Set components (CE-C01 .. CE-C15)
# --------------------------------------------------------------------------------------
def _screen_spot_elbow(x, y, p):
    return (in_spot("elbow", x, y) or in_spot("high_post_strip", x, y) or in_spot("nail_area", x, y)
            or (p["elbow_fb_y"][0] <= y <= p["elbow_fb_y"][1] and abs(x) <= p["elbow_fb_absx"]))


def detect_iverson(scene, **params):
    """Iverson: wing-to-wing cut over the elbows past >= 1 stationary elbow / high-post teammate."""
    p = _prm("iverson", params)
    out = []
    n = scene.n
    for c in scene.offense:
        k = scene.kins[c]
        x = np.nan_to_num(k.x, nan=0.0)
        sgn = np.sign(x)
        for fc in range(1, n):
            if not (sgn[fc - 1] != 0 and sgn[fc] != 0 and sgn[fc] != sgn[fc - 1]):
                continue
            s = int(sgn[fc - 1])
            pre = np.flatnonzero((x[:fc] * s) >= p["side_absx_m"])
            post = np.flatnonzero((x[fc:] * -s) >= p["side_absx_m"])
            if len(pre) == 0 or len(post) == 0:
                continue
            fa, fb = int(pre[-1]), fc + int(post[0])
            dur = (fb - fa) * DT
            if not (p["duration_s"][0] <= dur <= p["duration_s"][1]):
                continue
            if abs(x[fb] - x[fa]) < p["min_abs_dx_m"]:
                continue
            if not (p["start_y_m"][0] <= k.y[fa] <= p["start_y_m"][1]):
                continue
            yc = float(k.y[fc])
            if not (p["cross_y_m"][0] <= yc <= p["cross_y_m"][1]):
                continue
            if sum(_H(scene)[t] == c for t in range(fa, fb + 1)) > 0.5 * (fb - fa + 1):
                continue
            scr = _contacts(scene, c, fa, fb, p, lambda xx, yy: _screen_spot_elbow(xx, yy, p))
            if not scr:
                continue
            t_ref = scr[0][1]
            sig = _sigma_track(scene, [c], fc)
            p_y = float(p_above(yc, p["cross_y_m"][0], sig) * p_below(yc, p["cross_y_m"][1], sig))
            double = len(scr) >= 2 and (scr[1][1] - scr[0][1]) * DT <= p["double_within_s"]
            conf = p_y * scr[0][2] * _factor(scene, [c, scr[0][0]], fa, fb, t_ref)
            out.append(Event("iverson", {"cutter": c, "screener": scr[0][0]}, t_ref, fa, fb, conf,
                             {"screeners": [z[0] for z in scr], "crossing_y": yc, "double": bool(double),
                              "start_side": s, "duration_s": dur}))
    return _calibrated(scene, _dedup(out))


KIND_ITEM = {"get": "get_dho_chain", "dho_chain": "get_dho_chain"}


def _long_enough(e):
    """min_duration_s of the event's item is enforced on (end - start) x dt (loop 1 F12); null = no floor."""
    it = ITEMS.get(KIND_ITEM.get(e.kind, e.kind))
    md = it.get("min_duration_s") if it else None
    return md is None or (e.end - e.start) * DT >= md - 1e-9


# --------------------------------------------------------------------------------------
# Confidence calibration (calibration item, loop 1 F10)
# --------------------------------------------------------------------------------------
def scene_sigma_track(scene):
    """Median calibrated position sigma (K_CAL sqrt(var_p), m) over the attackers: the scene's noise level."""
    cache = _cache(scene)
    if "sigma_track" not in cache:
        v = np.concatenate([mvlib.K_CAL * np.sqrt(scene.kins[o].var_p) for o in scene.offense]) if scene.offense else np.array([])
        cache["sigma_track"] = float(np.nanmedian(v)) if np.any(np.isfinite(v)) else 0.123
    return cache["sigma_track"]


def sigma_band(scene):
    """'low' / 'mid' / 'high' noise band from scene_sigma_track and calibration.band_edges_m."""
    lo, hi = PRM["calibration"]["band_edges_m"]
    st = scene_sigma_track(scene)
    return "low" if st <= lo else ("mid" if st <= hi else "high")


def calibrate(kind, raw, band):
    """Map a raw component conf to P(correct | detected) with the kind's isotonic table for the noise band
    (piecewise linear between knots, constant outside); kinds without a table pass through unchanged."""
    tab = (PRM["calibration"]["tables"] or {}).get(kind)
    if not tab:
        return float(raw)
    knots = tab.get(band) or tab.get("all")
    if not knots:
        return float(raw)
    xs, ys = [k[0] for k in knots], [k[1] for k in knots]
    return float(np.clip(np.interp(raw, xs, ys), 0.0, 1.0))


def _calibrated(scene, evs):
    """Replace each component event's conf by its calibrated value; the raw conf stays in attrs['conf_raw']."""
    band = sigma_band(scene) if evs else None
    for e in evs:
        if "conf_raw" not in e.attrs:
            e.attrs["conf_raw"] = float(e.conf)
            e.attrs["calibration_band"] = band
            e.conf = calibrate(e.kind, e.conf, band)
    return evs


def fit_isotonic(pairs, prior=1.0, max_knots=6):
    """Isotonic (PAV) fit of P(correct) on raw conf. pairs = [(raw, correct 0/1)] -> knots [[raw, p], ...].

    PAV pools violators and ties (equal block means), so an all-correct run is one block; block values are
    Laplace-smoothed ((k + prior) / (n + 2 prior)) and re-made monotone; adjacent blocks are pooled until at most
    max_knots remain (smallest pair first). Used to build calibration.tables."""
    groups = {}
    for r, y in pairs:  # equal raw values (3 decimals) start as one block: the map cannot separate them
        g = groups.setdefault(round(float(r), 3), [0.0, 0.0, 0])
        g[0], g[1], g[2] = g[0] + float(r), g[1] + float(y), g[2] + 1
    blocks = []  # [sum_x, sum_y, n]
    for _, g in sorted(groups.items()):
        blocks.append(list(g))
        while len(blocks) > 1 and blocks[-2][1] / blocks[-2][2] >= blocks[-1][1] / blocks[-1][2]:  # pool ties too
            b = blocks.pop()
            blocks[-1] = [blocks[-1][0] + b[0], blocks[-1][1] + b[1], blocks[-1][2] + b[2]]
    while len(blocks) > max_knots:
        i = min(range(len(blocks) - 1), key=lambda j: blocks[j][2] + blocks[j + 1][2])
        b = blocks.pop(i + 1)
        blocks[i] = [blocks[i][0] + b[0], blocks[i][1] + b[1], blocks[i][2] + b[2]]
    knots, last = [], 0.0
    for sx, sy, nn in blocks:
        v = max(last, (sy + prior) / (nn + 2 * prior))
        knots.append([round(sx / nn, 3), round(v, 3)])
        last = v
    return knots


def _dedup(evs, tol_f=None):
    """Keep one event per (kind, actors) within tol frames (highest conf); drop events shorter than their item's
    min_duration_s."""
    tol_f = tol_f if tol_f is not None else frames(1.0)
    evs = sorted([e for e in evs if _long_enough(e)], key=lambda e: -e.conf)
    keep = []
    for e in evs:
        if any(k.kind == e.kind and k.actors == e.actors and abs(k.t0 - e.t0) <= tol_f for k in keep):
            continue
        keep.append(e)
    return sorted(keep, key=lambda e: e.t0)


def detect_zipper(scene, **params):
    """Zipper: block / low-post player cuts up the lane line to the slot / top past a stationary teammate."""
    p = _prm("zipper", params)
    out = []
    n = scene.n
    lp = PRM["event_lattice"]
    for z in scene.offense:
        k = scene.kins[z]
        at_block = np.array([in_spot("block", k.x[t], k.y[t]) or in_spot("low_post", k.x[t], k.y[t])
                             or (k.y[t] <= p["block_fb_y_max"] and p["block_fb_absx"][0] <= abs(k.x[t]) <= p["block_fb_absx"][1])
                             for t in range(n)])
        lb = frames(p["block_lookback_s"])
        for a, b in _moves(scene, z, lp):
            blk = np.flatnonzero(at_block[max(0, a - lb):b + 1])
            if len(blk) == 0:
                continue
            fa = max(0, a - lb) + int(blk[-1])
            arr = [t for t in range(fa, b + 1) if k.y[t] >= p["end_min_y_m"] and d3(k.x[t], k.y[t]) >= p["end_min_d3_m"]]
            if not arr:
                continue
            fb = arr[0]
            if (fb - fa) * DT > p["max_duration_s"]:
                continue
            path = float(np.nansum(np.hypot(np.diff(k.x[fa:fb + 1]), np.diff(k.y[fa:fb + 1]))))
            if path < p["min_path_m"]:
                continue
            scr = _contacts(scene, z, fa, fb, p, lambda xx, yy: p["screener_y_m"][0] <= yy <= p["screener_y_m"][1])
            if not scr:
                continue
            s, t_ref, cs = scr[0]
            catch = any(_H(scene)[_clip(t, n)] == z for t in range(fb, _clip(fb + frames(p["catch_within_s"]), n) + 1))
            follow = None
            for e in _screen_like(scene):
                if e.kind == "SCR.on" and fb <= e.t0 <= fb + frames(p["follow_pnr_within_s"]) and e.actors["screener"] in (s, z):
                    follow = "middle_pnr"
                    break
            conf = cs * _factor(scene, [z, s], fa, fb, t_ref)
            out.append(Event("zipper", {"cutter": z, "screener": s}, t_ref, fa, fb, conf,
                             {"catch": bool(catch), "follow_up": follow, "path_m": path}))
    return _calibrated(scene, _dedup(out))


def detect_chicago(scene, **params):
    """Chicago / Zoom: down (pin-down) screen on u, then DHO b -> u within 2.0 s at r 6-9 m."""
    p = _prm("chicago", params)
    prims = primitives(scene)
    out = []
    for s in [e for e in prims if e.kind in ("SCR.down",)]:
        u, scr = s.actors["user"], s.actors["screener"]
        for d in [e for e in prims if e.kind == "DHO" and e.actors["receiver"] == u]:
            if not (s.t0 <= d.t0 <= s.t0 + frames(p["dho_within_s"])):
                continue
            ru = math.hypot(*pos(scene, u, d.t0))
            if not (p["dho_r_m"][0] <= ru <= p["dho_r_m"][1]):
                continue
            giver = d.actors["giver"]
            variant = "chicago" if giver != scr else "down_then_dho_by_screener"
            conf = min(s.conf, d.conf) * _factor(scene, [u, giver, scr], s.t0, d.t0, s.t0)
            out.append(Event("chicago", {"user": u, "screener": scr, "giver": giver}, s.t0, s.start, d.end, conf,
                             {"delay_s": (d.t0 - s.t0) * DT, "variant": variant}))
    return _calibrated(scene, _dedup(out))


def _arrived(scene, oid, a, b, min_m):
    """True when player oid was >= min_m away from his position at frame b at some frame of [a, b] (he came in)."""
    k = scene.kins[oid]
    a, b = _clip(a, scene.n), _clip(b, scene.n)
    dd = np.hypot(k.x[a:b + 1] - k.x[b], k.y[a:b + 1] - k.y[b])
    return bool(np.any(np.isfinite(dd)) and np.nanmax(dd) >= min_m)


def _defender_reacts(scene, dfn, s2, w0, w1, p):
    """Defender mode reaction (loop 1 F15): for each frame e of [w0, w1] with the defender within contact_m of s2,
    compare the defender's mean velocity over [e - react_window_s, e] with [e, e + react_window_s] (pre / post means
    skip the plant phase, MP-13, instead of single-frame headings at the minimum distance, which falls late in the
    stuck phase where both speeds are about 0): reaction = pre speed >= defender_min_mps and a heading turn >
    defender_turn_deg or a speed drop >= defender_slow_frac. Returns the first reacting frame or None."""
    n = scene.n
    kd, k2 = scene.kins[dfn], scene.kins[s2]
    d = mvlib.dist(kd, k2)[w0:w1 + 1]
    h = frames(p["react_window_s"])
    for j in np.flatnonzero(np.nan_to_num(d, nan=99.0) <= PRM["event_lattice"]["scr_contact_m"]):
        e = w0 + int(j)
        a, b = _clip(e - h, n), _clip(e + h, n)
        pre = (np.nanmean(kd.vx[a:e + 1]), np.nanmean(kd.vy[a:e + 1]))
        post = (np.nanmean(kd.vx[e:b + 1]), np.nanmean(kd.vy[e:b + 1]))
        if not all(np.isfinite(v) for v in pre + post):
            continue
        v0, v1 = math.hypot(*pre), math.hypot(*post)
        if v0 < p["defender_min_mps"]:
            continue
        turn = abs((math.degrees(math.atan2(post[1], post[0])) - math.degrees(math.atan2(pre[1], pre[0])) + 180) % 360 - 180) \
            if v1 >= p["defender_min_mps"] else 0.0
        if turn > p["defender_turn_deg"] or (v0 - v1) / v0 >= p["defender_slow_frac"]:
            return e
    return None


def detect_spain(scene, **params):
    """Spain PnR: ball screen s1 -> h, s1 rolls, s2 screens s1's defender within [-0.3, +1.5] s.

    s2 must ARRIVE (loop 1 F3): he moved >= arrive_min_m within [t1 - arrive_from_s, t2]; a teammate standing on
    the roll path the whole possession is a post, not a back-screener."""
    p = _prm("spain", params)
    prims = primitives(scene)
    rolls = [e for e in prims if e.kind == "ROLL"]
    out = []
    n = scene.n
    for e in [x for x in prims if x.kind == "SCR.on"]:
        s1, h, t1 = e.actors["screener"], e.actors["user"], e.t0
        roll = next((r for r in rolls if r.actors["screener"] == s1 and r.t0 == t1), None)
        if roll is None:
            continue
        w0, w1 = _clip(t1 + frames(p["back_window_s"][0]), n), _clip(t1 + frames(p["back_window_s"][1]), n)
        arrive = lambda s2, t2: _arrived(scene, s2, t1 - frames(p["arrive_from_s"]), t2, p["arrive_min_m"])
        best, mode = None, None
        if scene.defense:
            # defender of s1 = nearest defender over the matchup_lookback_s before the screen (matchup proxy)
            lb = _clip(t1 - frames(p["matchup_lookback_s"]), n)
            dfs = [(np.nanmean(mvlib.dist(scene.kins[d], scene.kins[s1])[lb:t1 + 1]), d) for d in scene.defense]
            dfn = min(dfs)[1] if dfs and np.isfinite(min(dfs)[0]) and min(dfs)[0] < p["matchup_max_m"] else None
            if dfn is not None:
                for c in _contacts(scene, dfn, w0, w1, {"contact_m": PRM["event_lattice"]["scr_contact_m"]}):
                    s2 = c[0]
                    if s2 in (s1, h):
                        continue
                    t_e = _defender_reacts(scene, dfn, s2, w0, w1, p)
                    if t_e is not None and arrive(s2, c[1]):
                        best, mode = (s2, c[1], c[2]), "defender"
                        break
        if best is None:
            # no tracked defender: s2 stationary within the proxy distance of the roller's path (evidence 'proxy')
            for c in _contacts(scene, s1, w0, w1, {"contact_m": p["proxy_path_m"]}):
                if c[0] != h and arrive(c[0], c[1]):
                    best, mode = (c[0], c[1], c[2] * p["proxy_conf_factor"]), "proxy"
                    break
        if best is None:
            continue
        s2, t2, c2 = best
        k2 = scene.kins[s2]
        tp = _clip(t2 + frames(p["pop_within_s"]), n)
        pop = bool(np.nanmax(d3(k2.x[t2:tp + 1], k2.y[t2:tp + 1])) >= p["pop_min_d3_m"])
        conf = min(e.conf, c2) * _factor(scene, [s1, s2, h], t1, roll.end, t1)
        out.append(Event("spain", {"handler": h, "screener": s1, "back_screener": s2}, t1, e.start, max(roll.end, t2), conf,
                         {"s2_pop": pop, "back_screen_t": t2, "evidence_mode": mode}))
    return _calibrated(scene, _dedup(out))


def detect_elevator(scene, **params):
    """Elevator: two stationary teammates, a user crosses their segment, the gap then closes (fixed rule)."""
    p = _prm("elevator", params)
    out = []
    n = scene.n
    off = scene.offense
    for i, s1 in enumerate(off):
        for s2 in off[i + 1:]:
            k1, k2 = scene.kins[s1], scene.kins[s2]
            gap = mvlib.dist(k1, k2)
            for u in off:
                if u in (s1, s2):
                    continue
                ku = scene.kins[u]
                ex, ey = k2.x - k1.x, k2.y - k1.y
                cross = ex * (ku.y - k1.y) - ey * (ku.x - k1.x)
                L2 = ex * ex + ey * ey
                proj = ((ku.x - k1.x) * ex + (ku.y - k1.y) * ey) / np.where(L2 > 0, L2, np.nan)
                sg = np.sign(np.nan_to_num(cross))
                for t in range(1, n):
                    if sg[t] == 0 or sg[t - 1] == 0 or sg[t] == sg[t - 1] or not (0.0 <= proj[t] <= 1.0):
                        continue
                    pre0, pre1 = _clip(t - frames(p["pre_window_s"]), n), _clip(t - 1, n)
                    g0 = float(np.nanmedian(gap[_clip(pre0 - 2, n):pre0 + 3]))
                    if not (p["g0_m"][0] <= g0 <= p["g0_m"][1]):
                        continue
                    stat = min(window_conf(_stationary_p(k1), pre0, pre1), window_conf(_stationary_p(k2), pre0, pre1))
                    if stat < PRM["event_lattice"]["scr_stat_frac"]:
                        continue
                    wide = g0 > p["standard_g0_max_m"]
                    w_end = _clip(t + frames(p["close_window_wide_s"] if wide else p["close_window_s"]), n)
                    hw = int(p["end_median_frames"]) // 2  # persistence: a real close outlasts an AR noise dip
                    med = [float(np.nanmedian(gap[_clip(j - hw, n):_clip(j + hw, n) + 1])) for j in range(t, w_end + 1)]
                    g_end = min(med)
                    sig = _sigma_track(scene, [s1, s2], t)
                    drop = g0 - g_end
                    if drop < p["min_drop_frac"] * g0 or drop < p["drop_sigma_k"] * math.sqrt(2) * sig:
                        continue
                    target = p["target_wide_m"] if wide else p["target_m"]
                    soft = 1.0 if g_end < target else p["target_miss_factor"]
                    j_close = t + int(np.argmin(med))
                    conf = stat * soft * float(p_above(drop, p["min_drop_frac"] * g0, math.sqrt(2) * sig)) * _factor(scene, [s1, s2, u], pre0, j_close, t)
                    out.append(Event("elevator", {"user": u, "screener_1": s1, "screener_2": s2}, t, pre0, j_close, conf,
                                     {"g0_m": g0, "g_min_m": g_end, "close_time_s": (j_close - t) * DT,
                                      "variant": "wide" if wide else "standard", "target_met": g_end < target}))
    return _calibrated(scene, _dedup(out))


def detect_floppy(scene, **params):
    """Floppy: shooter starts under the rim (r < 1.5 m), exits to a wing / corner off >= 1 screen within 3 s."""
    p = _prm("floppy", params)
    out = []
    n = scene.n
    lp = PRM["event_lattice"]
    for sh in scene.offense:
        k = scene.kins[sh]
        under = np.nan_to_num(k.r, nan=99) < p["start_r_m"]
        for a, b in _moves(scene, sh, lp):
            pre = np.flatnonzero(under[_clip(a - frames(p["dwell_s"]) - 3, n):a + 3])
            if len(pre) < frames(p["dwell_s"]) // 2:
                continue
            onset = a
            w = _clip(onset + frames(p["exit_within_s"]), n)
            ends = [t for t in range(onset, w + 1) if d3(k.x[t], k.y[t]) >= p["end_min_d3_m"] or in_spot("corner_three", k.x[t], k.y[t])]
            if not ends:
                continue
            fb = ends[0]
            scr = _contacts(scene, sh, onset, fb, p)
            if not scr:
                continue
            if len(scr) == 1:
                choice = "single"
            else:
                g = math.dist(pos(scene, scr[0][0], scr[0][1]), pos(scene, scr[1][0], scr[1][1]))
                choice = "double" if g <= p["double_gap_m"] else "stagger"
            conf = scr[0][2] * window_conf(under.astype(float), _clip(onset - frames(p["dwell_s"]), n), onset) * _factor(scene, [sh], onset, fb, onset)
            out.append(Event("floppy", {"shooter": sh, "screener": scr[0][0]}, onset, onset, fb, conf,
                             {"side_choice": choice, "screeners": [z[0] for z in scr], "exit_side": 1 if k.x[fb] >= 0 else -1}))
    return _calibrated(scene, _dedup(out))


def detect_hammer(scene, **params):
    """Hammer: baseline drive on side s + weak-side (side -s) flare to the corner around the drive's rim arrival."""
    p = _prm("hammer", params)
    prims = primitives(scene)
    out = []
    n = scene.n
    for dr in [e for e in prims if e.kind == "DRIVE" and e.attrs["direction"] == "baseline"]:
        h, t_rim, s = dr.actors["handler"], dr.attrs["t_rim"], dr.attrs["side"]
        for u in scene.offense:
            if u == h:
                continue
            ku = scene.kins[u]
            w0, w1 = _clip(t_rim - frames(p["screen_window_s"]), n), _clip(t_rim + frames(p["screen_window_s"]), n)
            spot = lambda xx, yy: yy <= p["screener_max_y_m"] and p["screener_absx_m"][0] <= abs(xx) <= p["screener_absx_m"][1] and xx * s < 0
            scr = _contacts(scene, u, w0, w1, p, spot)
            if not scr:
                continue
            fs, t_s, cs = scr[0]
            w_end = _clip(t_s + frames(p["corner_within_s"]), n)
            corner = any(in_spot("corner_three", ku.x[t], ku.y[t]) and ku.x[t] * s < 0 for t in range(t_s, w_end + 1))
            if not corner:
                continue
            thrown = any(e.kind == "PASS" and e.actors["passer"] == h and e.actors["receiver"] == u
                         and t_rim <= e.t0 <= t_rim + frames(p["thrown_within_s"]) for e in prims)
            conf = min(dr.conf, cs) * _factor(scene, [h, u, fs], dr.t0, w_end, t_rim)
            out.append(Event("hammer", {"driver": h, "shooter": u, "screener": fs}, t_rim, dr.t0, w_end, conf,
                             {"thrown": bool(thrown), "drive_side": s}))
    return _calibrated(scene, _dedup(out))


def _t_control(scene, params):
    t = params.get("t_control_f")
    return t if t is not None else _first_holder_frame(scene)


def detect_pistol(scene, **params):
    """Pistol / 21: early side action (screen or DHO between handler and wing) with a teammate at the top."""
    p = _prm("pistol", params)
    early = _prm("drag", {})["early_window_s"]
    prims = primitives(scene)
    tc = _t_control(scene, params)
    if tc is None:
        return []
    out = []
    for e in [x for x in prims if x.kind in ("SCR.on", "DHO")]:
        if not (tc <= e.t0 <= tc + frames(early)):
            continue
        if e.kind == "SCR.on":
            h, w = e.actors["user"], e.actors["screener"]
        else:
            h, w = e.actors["giver"], e.actors["receiver"]
        kh = scene.kins[h]
        if not np.nanmax(kh.y[tc:e.t0 + 1]) > p["handler_from_y_m"]:
            continue
        # loop 2 R1: the action location is where the action happens - the screener for a screen, the giver (the
        # ball's hands) for a DHO; a DHO receiver is already running past the hand-off at t0 (r 8.6-9.3 m)
        ax, ay = pos(scene, w if e.kind == "SCR.on" or p["dho_location_actor"] == "receiver" else h, e.t0)
        ra = math.hypot(ax, ay)
        if not (p["action_r_m"][0] <= ra <= p["action_r_m"][1]) or abs(ax) < p["action_min_absx_m"]:
            continue
        side = 1 if ax > 0 else -1
        top = [o for o in scene.offense if o not in (h, w)
               and p["top_r_m"][0] <= math.hypot(*pos(scene, o, e.t0)) <= p["top_r_m"][1]
               and m_angle(*pos(scene, o, e.t0)) >= p["top_min_m_deg"]]
        if not top:
            continue
        paint = [o for o in scene.offense if abs(pos(scene, o, e.t0)[0]) <= C["LANE_X"] and pos(scene, o, e.t0)[1] <= C["FT_Y"]]
        if paint:
            continue
        conf = e.conf * _factor(scene, [h, w, top[0]], e.start, e.end, e.t0)
        out.append(Event("pistol", {"handler": h, "wing": w, "big": top[0]}, e.t0, e.start, e.end, conf,
                         {"action_kind": "screen" if e.kind == "SCR.on" else "dho", "side": side,
                          "since_control_s": (e.t0 - tc) * DT}))
    return _calibrated(scene, _dedup(out))


def _distance_minima(d, a, b, rise):
    """Local minima of d on [a, b] separated by a rise >= rise on both sides (extremum tracking with hysteresis);
    always at least the global minimum. NaN frames are skipped."""
    seg = np.asarray(d[a:b + 1], float)
    if not np.any(np.isfinite(seg)):
        return []
    mins, seek_min, m, M = [], True, None, None
    for i, v in enumerate(seg):
        if not np.isfinite(v):
            continue
        if seek_min:
            if m is None or v < seg[m]:
                m = i
            elif v >= seg[m] + rise:
                mins.append(m)
                seek_min, M = False, i
        else:
            if v > seg[M]:
                M = i
            elif v <= seg[M] - rise:
                seek_min, m = True, i
    if seek_min and m is not None:
        mins.append(m)
    return [a + i for i in mins] or [a + int(np.nanargmin(seg))]


def detect_drag(scene, **params):
    """Drag / double drag: early ball screen by a trailer who came from the backcourt (transition_full drag row).

    Loop 1 F2: the trailer-run test replaces the mean v_y <= -3.0 m/s test (which only a screener still sprinting
    through the handler, i.e. an illegal moving screen, could pass): the screener's y fell by >= min_drop_m over the
    run_window_s before contact (he may stop to set a legal screen), the handler-screener relative speed at contact
    is >= min_rel_mps (two players running side by side are not a screen), and contacts of the same pair within
    pair_merge_s are merged keeping the last one (a trailer running past the handler before he sets the screen)."""
    p = _prm("drag", params)
    tc = _t_control(scene, params)
    if tc is None:
        return []
    n = scene.n
    lp = PRM["event_lattice"]
    on_f = int(lp["on_ball_frames"])
    HS = _soft_holder(scene, lp["on_ball_hold_ext_k"])
    contacts = []
    for s in scene.offense:
        ks = scene.kins[s]
        for h in scene.offense:
            if h == s:
                continue
            kh = scene.kins[h]
            d = mvlib.dist(ks, kh)
            sd = mvlib.sigma_dist(ks, kh)
            # loop 5 C7: the ball-screen contact rule of C2 - noise-widened gate scr_contact_m + scr_on_contact_k x
            # sigma_dist, a widened contact needs the handler's defender at the screener, the on-ball test uses the
            # holder with hysteresis and the contact probability scr_on_pc_k x sigma_dist (SportVU: 9 of 12 drags
            # lost under noise had the noisy minimum distance at 1.21-1.73 m)
            # loop 7 C7: the drag contact gate includes the physical band (wide_body_m) before the noise widening
            close = np.nan_to_num(d, nan=99) <= (lp["scr_contact_m"] + p["wide_body_m"]
                                                 + lp["scr_on_contact_k"] * np.nan_to_num(sd, nan=0.0))
            pair = []
            hw = frames(p["holder_window_s"])
            for a, b in hysteresis(close, close, 0.0, int(lp["contact_bridge_frames"])):
                # loop 2 R4: one contact interval can hold two approaches (the trailer running past the handler,
                # then the screen); split it at every noise-significant local minimum (_distance_minima), the
                # pair merge below keeps the last one
                rise = max(p["split_rise_min_m"], p["split_rise_k"] * float(np.nanmedian(sd[a:b + 1])))
                for t in _distance_minima(d, a, b, rise):
                    if not (tc <= t <= tc + frames(p["early_window_s"])):
                        continue
                    if not any(HS[_clip(t + j, n)] == h for j in range(-on_f, on_f + 1)):
                        continue
                    # loop 6 C7: a widened contact (minimum beyond scr_contact_m) needs evidence that the trailer reached
                    # the handler - P(true distance <= scr_contact_m) = p_below(d, scr_contact_m, wide_reach_k x
                    # sigma_dist) >= wide_reach_p - besides the handler's defender meeting him. The widened gate alone
                    # admitted trailers running past 1.5-1.9 m away (SportVU --noise 0.5: 6 of 8 added drags had a clean
                    # minimum of 1.43-1.84 m; synthetic rim run 1.7 m off the handler: FP 0/0 -> 3/4 of 10)
                    # loop 7 C7: the reach edge is the physical contact width scr_contact_m + wide_body_m - the
                    # handler's defender, who must meet the screener for a widened contact, is the body between the
                    # two attackers - not scr_contact_m itself: with the loop-6 edge the band collapsed to 1.2-1.34 m
                    # at the told sigma and dropped plausible 1.27-1.39 m drags (stop-drag 1.35 m TP 10/9 -> 5/6)
                    # loop 8 C7: the reach test is the measured minimum itself inside that width, a hard geometric
                    # edge. The loop-6/7 form p_below(d, edge, wide_reach_k x sigma_dist) >= wide_reach_p is exactly
                    # this edge at p 0.5 (k had no effect); p != 0.5 was measured and is no net gain (p 0.6: stop-drag
                    # 1.35 m TP 9/8/5 -> 7/6/5 at 0.2/0.3/0.5 with the 1.5 m FP 2/5/5 -> 2/3/5; p 0.4: 1.5 m FP 2 -> 4
                    # at 0.2), because a noisy minimum is biased low and the noise allowance already sits in the gate
                    if d[t] > lp["scr_contact_m"] and not (
                            (not p["wide_reach_test"] or d[t] <= lp["scr_contact_m"] + p["wide_body_m"])
                            and _defender_meets(scene, s, h, t, lp)):
                        continue
                    # loop 2 R3: the handler, not the screener, holds the ball around the contact (holder flicker
                    # between two close players at high noise made the handler a 'screener' of the trailer)
                    hs = [_H(scene)[_clip(t + j, n)] for j in range(-hw, hw + 1)]
                    if not hs.count(h) > hs.count(s):
                        continue
                    rel = math.hypot(kh.vx[t] - ks.vx[t], kh.vy[t] - ks.vy[t])
                    if not rel >= p["min_rel_mps"]:
                        continue
                    r = math.hypot(*pos(scene, s, t))
                    if not (p["screen_r_m"][0] <= r <= p["screen_r_m"][1]):
                        continue
                    pre = _clip(t - frames(p["run_window_s"]), n)
                    drop = float(np.nanmax(ks.y[pre:t + 1]) - ks.y[t])
                    pv = float(p_above(drop, p["min_drop_m"], _sigma_track(scene, [s], t) * math.sqrt(2)))
                    if pv < 0.5:
                        continue
                    pc = float(p_below(d[t], lp["scr_contact_m"], lp["scr_on_pc_k"] * sd[t]))
                    pair.append((t, s, h, pc * pv * _factor(scene, [s, h], pre, t, t), drop, pre))
            # merge contacts of the same pair within pair_merge_s, keeping the last one
            merged = []
            for c in pair:
                if merged and (c[0] - merged[-1][0]) * DT <= p["pair_merge_s"]:
                    merged[-1] = c
                else:
                    merged.append(c)
            contacts += merged
    contacts.sort()
    out, used = [], set()
    for i, (t, s, h, c, drop, pre) in enumerate(contacts):
        if i in used:
            continue
        k = scene.kins[s]
        w = _clip(t + frames(p["read_window_s"]), n)
        read = "roll" if np.nanmin(k.r[t:w + 1]) < p["roll_r_m"] else ("pop" if k.r[w] >= C["ARC_R"] else "none")
        second = None
        for j in range(i + 1, len(contacts)):
            t2, s2, h2, c2 = contacts[j][:4]
            if h2 == h and s2 != s and (t2 - t) * DT <= p["double_within_s"]:
                gap = math.dist(pos(scene, s, t), pos(scene, s2, t2))
                if p["double_gap_m"][0] <= gap <= p["double_gap_m"][1]:
                    second = (s2, c2)
                    used.add(j)
                    break
        actors = {"handler": h, "screener": s}
        if second:
            actors["screener_2"] = second[0]
        out.append(Event("drag", actors, t, pre, w, min(c, second[1]) if second else c,
                         {"double": second is not None, "read": read, "drop_m": drop, "since_control_s": (t - tc) * DT}))
    return _calibrated(scene, _dedup(out))


PNR_TOKEN = {"pnr_location_high": "top", "pnr_location_side": "side", "pnr_location_slot": "slot",
             "pnr_location_corner": "corner", "pnr_location_logo": "deep"}


def pnr_location_label(x, y):
    """named_spots zone_scheme:pnr_location label of a point -> (canonical token, raw side-qualified label)."""
    for sid in PNR_TOKEN:
        labs = SPOTS[sid].labels(float(x), float(y))
        if labs:
            return PNR_TOKEN[sid], labs[0]
    return "inside", None


def detect_pnr_location(scene, **params):
    """PnR location and side qualifiers at each ball-screen moment (named_spots pnr_location layer)."""
    p = _prm("pnr_location", params)
    out = []
    n = scene.n
    ons = [e for e in primitives(scene) if e.kind == "SCR.on"]
    hw = frames(p["loc_median_half_s"])
    draws = np.random.default_rng(int(p["loc_seed"])).standard_normal((int(p["loc_samples"]), 2))  # fixed: deterministic
    for e in ons:
        s, h, t = e.actors["screener"], e.actors["user"], e.t0
        ks = scene.kins[s]
        # loop 1 F11: median screener position over [t - loc_median_half_s, t + loc_median_half_s], label
        # probabilities by propagating N(position, sigma_track) through the named_spots labels
        a, b = _clip(t - hw, n), _clip(t + hw, n)
        x, y = float(np.nanmedian(ks.x[a:b + 1])), float(np.nanmedian(ks.y[a:b + 1]))
        # loop 2 R2: sigma_track is a per-frame posterior sigma; the error of the 0.6 s median is larger and grows
        # with noise (measured rms / sigma_track 1.18 / 1.29 / 1.66 at sigma_p 0.2 / 0.3 / 0.5), so the sampling
        # sigma is inflated per noise band (the median's standard error std / sqrt(n) adds only ~0.01 m)
        sig = _sigma_track(scene, [s], t) * float(p["loc_sigma_inflation"][sigma_band(scene)])
        cnt = {}
        for dx, dy in draws:
            tk = pnr_location_label(x + sig * dx, y + sig * dy)[0]
            cnt[tk] = cnt.get(tk, 0) + 1
        probs = sorted(((k_, v / len(draws)) for k_, v in cnt.items()), key=lambda z: (-z[1], z[0]))
        tok, raw = pnr_location_label(x, y)
        alts = [k_ for k_, v in probs[:2] if v >= p["loc_alt_min_p"]] if len(probs) > 1 and probs[1][1] >= p["loc_alt_min_p"] else [tok]
        side = 1 if pos(scene, h, t)[0] >= 0 else -1
        others = [o for o in scene.offense if o not in (s, h)]
        empty = all(pos(scene, o, t)[0] * side < p["empty_side_min_x_m"] for o in others)
        pre = _clip(t - frames(p["step_up_lookback_s"]), n)
        step_up = bool(np.nanmin(ks.y[pre:t + 1]) <= p["step_up_from_y_m"] and y >= p["step_up_to_y_m"])
        re = any(o is not e and o.actors == e.actors and 0 < (e.t0 - o.t0) * DT <= p["re_screen_within_s"] for o in ons)
        out.append(Event("pnr_location", {"screener": s, "handler": h}, t, e.start, e.end, e.conf,
                         {"location": tok, "label": raw, "location_probs": probs, "location_alternatives": alts,
                          "strong_side_sign": side, "empty_side": bool(empty),
                          "step_up": step_up, "re_screen": bool(re)}))
    return out


def detect_stagger(scene, **params):
    """Stagger / triple stagger: >= 2 off-ball screens on one user, screeners 2-5 m apart, <= 1.5 s between contacts."""
    p = _prm("stagger", params)
    offs = [e for e in primitives(scene) if e.kind.startswith("SCR.") and e.kind != "SCR.on"]
    out = []
    n = scene.n
    for u in scene.offense:
        mine = sorted([e for e in offs if e.actors["user"] == u], key=lambda e: e.t0)
        members = set()  # loop 1 F5: a screen already inside an emitted chain does not start a (suffix) chain
        for i, e1 in enumerate(mine):
            if id(e1) in members:
                continue
            chain = [e1]
            for e2 in mine[i + 1:]:
                last = chain[-1]
                if e2.actors["screener"] in [c.actors["screener"] for c in chain]:
                    continue
                dt = (e2.t0 - last.t0) * DT
                g = math.dist(e2.attrs["spot"], last.attrs["spot"])
                if 0 < dt <= p["second_within_s"] and p["gap_m"][0] <= g <= p["gap_m"][1]:
                    chain.append(e2)
            if len(chain) < 2:
                continue
            members |= {id(c) for c in chain}
            ku = scene.kins[u]
            a, b = chain[0].t0, chain[-1].t0
            tb = _clip(b + frames(p["exit_after_s"]), n)
            s0 = _ball_side(scene, a)  # stagger-away: the user ends opposite the ball's side at the first screen
            away = bool(s0 != 0 and np.sign(ku.x[tb]) == -s0)
            exit_ = "curl" if ku.r[tb] < p["curl_end_r_m"] else ("flare" if chain[-1].kind == "SCR.flare" else "straight")
            actors = {"user": u, "screener_1": chain[0].actors["screener"], "screener_2": chain[1].actors["screener"]}
            if len(chain) >= 3:
                actors["screener_3"] = chain[2].actors["screener"]
            out.append(Event("stagger", actors, a, chain[0].start, chain[-1].end, min(c.conf for c in chain),
                             {"triple": len(chain) >= 3, "away": away, "exit": exit_,
                              "gaps_m": [math.dist(c2.attrs["spot"], c1.attrs["spot"]) for c1, c2 in zip(chain, chain[1:])]}))
    return _calibrated(scene, _dedup(out))


def _ball_lead(scene, d):
    """Loop 5 C4: median over the receiver's holder run that starts at DHO d of dist(ball, giver) - dist(ball, receiver)."""
    g, r = d.actors["giver"], d.actors["receiver"]
    run = next(((a, b) for h, a, b in holder_runs(scene) if h == r and a <= d.t0 <= b), None)
    if run is None or scene.ball is None:
        return -np.inf
    a, b = run
    kg, kr = scene.kins[g], scene.kins[r]
    lead = (np.hypot(scene.ball.x[a:b + 1] - kg.x[a:b + 1], scene.ball.y[a:b + 1] - kg.y[a:b + 1])
            - np.hypot(scene.ball.x[a:b + 1] - kr.x[a:b + 1], scene.ball.y[a:b + 1] - kr.y[a:b + 1]))
    return float(np.nanmedian(lead)) if np.any(np.isfinite(lead)) else -np.inf


def _receiver_run_s(scene, d):
    """Loop 6 C4: length (s) of the receiver's holder run that contains DHO d's t0 (0 when there is none)."""
    r = d.actors["receiver"]
    run = next(((a, b) for h, a, b in holder_runs(scene) if h == r and a <= d.t0 <= b), None)
    return 0.0 if run is None else (run[1] - run[0] + 1) * DT


def detect_get_dho_chain(scene, **params):
    """Get / chase (PASS a -> b then DHO b -> a) and DHO chains (>= 2 DHOs, distinct givers, within 5 s)."""
    p = _prm("get_dho_chain", params)
    prims = primitives(scene)
    # loop 4 L10: get and DHO chains are half-court set components; transfers with the ball more than
    # max_past_half_m beyond the half-court line (outlet / inbound hand-offs in the backcourt) do not take part
    yb = np.nan_to_num(scene.ball.y, nan=99.0) if scene.ball is not None else np.full(scene.n, 99.0)
    fc = lambda e: yb[e.t0] <= C["HALF_Y"] + p["max_past_half_m"]  # noqa: E731
    passes = [e for e in prims if e.kind == "PASS" and fc(e)]
    dhos = [e for e in prims if e.kind == "DHO" and fc(e)]
    out = []
    for ps in passes:
        a, b = ps.actors["passer"], ps.actors["receiver"]
        for d in dhos:
            if d.actors["giver"] == b and d.actors["receiver"] == a and ps.t0 < d.t0 <= ps.t0 + frames(p["get_within_s"]):
                out.append(Event("get", {"passer": a, "receiver": b}, ps.t0, ps.start, d.end, min(ps.conf, d.conf),
                                 {"delay_s": (d.t0 - ps.t0) * DT}))
    # DHO chain (loop 1 F4): the receiver of DHO k gives DHO k+1 within chain_within_s of DHO k (gap from the last
    # DHO, not the first); givers distinct; a DHO already inside a chain does not start a suffix chain.
    # Loop 5 C4: a chain link must be a holder change the ball supports - over the receiver's run the ball is nearer
    # to him than to the giver by >= chain_min_lead_m (median). Two attackers standing together (0.3-0.5 m) trade
    # the nearest-attacker label without any hand-off; the hand-back A -> B -> A then read as a chain
    dhos = [d for d in dhos if _ball_lead(scene, d) >= p["chain_min_lead_m"]]
    # Loop 6 C4: ... and the receiver keeps the ball for >= chain_min_hold_s (his holder run that starts at the DHO). A
    # 'hand-back' of 0.2-0.3 s is the two players' label flicker surviving the lead test (SportVU --noise 0.3: a
    # noisy-only A -> B -> A chain whose last run was 0.30 s; on clean positions B kept the ball)
    dhos = [d for d in dhos if _receiver_run_s(scene, d) >= p["chain_min_hold_s"]]
    members = set()
    for i, d1 in enumerate(dhos):
        if i in members:
            continue
        chain, idx = [d1], [i]
        for j, d2 in enumerate(dhos[i + 1:], start=i + 1):
            last = chain[-1]
            if (0 < (d2.t0 - last.t0) * DT <= p["chain_within_s"] and d2.actors["giver"] == last.actors["receiver"]
                    and d2.actors["giver"] not in [c.actors["giver"] for c in chain]):
                chain.append(d2)
                idx.append(j)
        if len(chain) >= p["chain_min"]:
            members |= set(idx)
            actors = {f"giver_{j + 1}": c.actors["giver"] for j, c in enumerate(chain)}
            actors["receiver"] = chain[-1].actors["receiver"]
            out.append(Event("dho_chain", actors, d1.t0, d1.start, chain[-1].end, min(c.conf for c in chain),
                             {"chain_length": len(chain)}))
    return _calibrated(scene, _dedup(out))


def detect_ucla(scene, **params):
    """UCLA: passer from the top / slot cuts to the block over a stationary high-post teammate within 1.5 s."""
    p = _prm("ucla", params)
    prims = primitives(scene)
    out = []
    n = scene.n
    lp = PRM["event_lattice"]
    for ps in [e for e in prims if e.kind == "PASS"]:
        c, w = ps.actors["passer"], ps.actors["receiver"]
        cx, cy = pos(scene, c, ps.t0)
        wx, wy = pos(scene, w, ps.end)
        if cy < p["passer_min_y_m"] or abs(wx) < p["receiver_min_absx_m"]:
            continue
        kc = scene.kins[c]
        for a, b in _moves(scene, c, lp):
            if not (ps.t0 - frames(p["cut_lead_s"]) <= a <= ps.t0 + frames(p["cut_within_s"])):
                continue
            arr = [t for t in range(a, b + 1) if (kc.y[t] <= p["end_max_y_m"] and abs(kc.x[t]) <= p["end_max_absx_m"]) or kc.r[t] < p["end_r_m"]]
            if not arr or (arr[0] - a) * DT > p["cut_max_s"]:
                continue
            scr = _contacts(scene, c, a, arr[0], p, lambda xx, yy: p["screener_y_m"][0] <= yy <= p["screener_y_m"][1] and abs(xx) <= p["screener_max_absx_m"])
            if not scr:
                continue
            s, t_ref, cs = scr[0]
            conf = min(ps.conf, cs) * _factor(scene, [c, s], a, arr[0], t_ref)
            out.append(Event("ucla", {"cutter": c, "screener": s, "receiver": w}, t_ref, ps.t0, arr[0], conf,
                             {"catch": any(_H(scene)[_clip(t, n)] == c for t in range(arr[0], _clip(arr[0] + frames(p["catch_within_s"]), n)))}))
    return _calibrated(scene, _dedup(out))


def detect_flex(scene, **params):
    """Flex cycle: weak-corner cutter runs the baseline to the ball-side block past a block screener, then the
    flex screener receives a down screen (screen-the-screener) within 2.0 s."""
    p = _prm("flex", params)
    out = []
    n = scene.n
    lp = PRM["event_lattice"]
    for f in scene.offense:
        k = scene.kins[f]
        for a, b in _moves(scene, f, lp):
            bs = _ball_side(scene, a)
            if bs == 0:
                continue
            # loop 1 F6: the weak-side corner start is tested on any frame of the corner_lookback_s before the move
            # (corner players stand 0.1-0.3 m behind the line; one noisy frame flipped the label)
            if not any(in_spot("corner_three", k.x[j], k.y[j]) and k.x[j] * bs < 0
                       for j in range(_clip(a - frames(p["corner_lookback_s"]), n), a + 1)):
                continue
            arr = [t for t in range(a, b + 1) if k.x[t] * bs > 0 and abs(k.x[t]) <= p["block_max_absx_m"] and k.y[t] <= p["block_max_y_m"]]
            if not arr:
                continue
            fb = arr[0]
            if np.nanmax(k.y[a:fb + 1]) > p["path_max_y_m"]:
                continue
            scr = _contacts(scene, f, a, fb, p, lambda xx, yy: yy <= p["screener_max_y_m"] and p["screener_absx_m"][0] <= abs(xx) <= p["screener_absx_m"][1])
            if not scr:
                continue
            b_scr, t_flex, cs = scr[0]
            w1 = _clip(t_flex + frames(p["sts_within_s"]), n)
            sts = _contacts(scene, b_scr, t_flex, w1, p)
            dw = frames(p["sts_dir_window_s"])
            sts = [z for z in sts if z[0] != f and scene.kins[b_scr].y[_clip(z[1] + dw, n)] > scene.kins[b_scr].y[_clip(z[1] - dw, n)]]
            if not sts:
                continue
            conf = min(cs, sts[0][2]) * _factor(scene, [f, b_scr, sts[0][0]], a, w1, t_flex)
            out.append(Event("flex", {"cutter": f, "screener": b_scr, "sts_screener": sts[0][0]}, t_flex, a, max(fb, sts[0][1]), conf,
                             {"ball_side": bs, "sts_t": sts[0][1]}))
    return _calibrated(scene, _dedup(out))


def detect_ram(scene, **params):
    """Ram: player s uses an off-ball screen, then sets a ball screen <= 2.0 s later (veer flag)."""
    p = _prm("ram", params)
    prims = primitives(scene)
    offs = [e for e in prims if e.kind.startswith("SCR.") and e.kind != "SCR.on"]
    ons = [e for e in prims if e.kind == "SCR.on"]
    out = []
    for e1 in offs:
        s = e1.actors["user"]
        for e2 in ons:
            if e2.actors["screener"] == s and e1.t0 < e2.t0 <= e1.t0 + frames(p["ball_screen_within_s"]):
                veer = any(e3.actors["screener"] == s and e2.t0 < e3.t0 <= e2.t0 + frames(p["veer_within_s"]) for e3 in offs)
                conf = min(e1.conf, e2.conf)
                out.append(Event("ram", {"ram_screener": e1.actors["screener"], "big": s, "handler": e2.actors["user"]},
                                 e1.t0, e1.start, e2.end, conf, {"veer": bool(veer), "delay_s": (e2.t0 - e1.t0) * DT}))
                break
    return _calibrated(scene, _dedup(out))


# --------------------------------------------------------------------------------------
# Special classes: ISO, motion, continuity, style (CE-R16, CE-R17, R-ST-25)
# --------------------------------------------------------------------------------------
def _extend_holds(scene, runs, k):
    """Loop 5 C1 (holder hysteresis for the ISO hold): extend each holder run outward over frames with no holder in
    which the ball stays within HOLD_R + k x sigma_dist(holder, ball) of the holder and does not move away from him
    faster than event_lattice.catch_max_ball_mps. A dribbled ball sits 0.3-0.9 m from the handler; with position
    noise the hard HOLD_R test drops the catch and release frames (SportVU at --noise 0.5: holds shrink by a median
    0.10 s, p90 0.88 s), which pushed real 3.0-3.6 s holds under min_hold_s. Runs never extend into another holder."""
    if k <= 0 or scene.ball is None:
        return runs
    H = _H(scene)
    n = scene.n
    rel_max = PRM["event_lattice"]["catch_max_ball_mps"]
    out = []
    for i, (h, a, b) in enumerate(runs):
        kh = scene.kins[h]
        D = np.hypot(scene.ball.x - kh.x, scene.ball.y - kh.y)
        R = mvlib.HOLD_R + k * mvlib.sigma_dist(kh, scene.ball)
        REL = np.hypot(scene.ball.vx - kh.vx, scene.ball.vy - kh.vy)
        ok = lambda t: H[t] is None and np.isfinite(D[t]) and D[t] <= R[t] and not REL[t] > rel_max  # noqa: E731
        lo = runs[i - 1][2] + 1 if i > 0 else 0
        hi = runs[i + 1][1] - 1 if i + 1 < len(runs) else n - 1
        while a - 1 >= lo and ok(a - 1):
            a -= 1
        while b + 1 <= hi and ok(b + 1):
            b += 1
        out.append((h, a, b))
    return out


def _trim_flights(scene, runs, vmin, min_f, rel_p=0.5, gap=0, half=False, peak_f=0, vfast=0.0):
    """Loop 6 C1, loop 7 C1: a hold ends where the ball's release flight starts and starts where the arriving flight
    ends.

    v_r = d/dt dist(ball, holder) from the CA-RTS velocities (radial component of the ball's velocity relative to the
    holder), sigma_vr = K_CAL x sqrt(var_v(ball) + var_v(holder)). A frame is release evidence when
    P(v_r > vmin) >= rel_p (p_above with sigma_vr; arrival evidence: P(v_r < -vmin) >= rel_p). At the end of a run
    the final stretch of release frames is cut, at the start the first stretch of arrival frames, when the stretch
    holds at least min_f evidence frames. Loop 7: up to `gap` frames without evidence inside the stretch (or before
    it at the run edge) do not end it - the cut still stops at the stretch's earliest evidence frame, so a gap is only
    bridged when more evidence follows. A soft pass (~4.3 m/s, under catch_max_ball_mps) is inside HOLD_R for ~0.25 s
    at each end and inside the hold hysteresis even longer, so a 2.6 s hold read >= 3 s; a dribble's outward bounce
    mid-hold is not at a run boundary and is never cut."""
    if vmin <= 0 or scene.ball is None:
        return runs
    out = []
    bl = scene.ball
    for h, a, b in runs:
        kh = scene.kins[h]
        rx, ry = bl.x - kh.x, bl.y - kh.y
        rv = np.hypot(rx, ry)
        vr = np.nan_to_num((rx * (bl.vx - kh.vx) + ry * (bl.vy - kh.vy)) / np.maximum(rv, 1e-6), nan=0.0)
        sv = np.nan_to_num(mvlib.K_CAL * np.sqrt(bl.var_v + kh.var_v), nan=9.0)
        rel = p_above(vr, vmin, sv) >= rel_p
        arr = p_below(vr, -vmin, sv) >= rel_p

        def stretch(ev, t, step, stop):
            """Earliest (in walking order) evidence frame of the edge stretch and its evidence count."""
            e, cnt, miss = None, 0, 0
            while (t >= stop if step < 0 else t <= stop):
                if ev[t]:
                    e, cnt, miss = t, cnt + 1, 0
                else:
                    miss += 1
                    if miss > gap:
                        break
                t += step
            return e, cnt

        e, cnt = stretch(rel, b, -1, a + 1)
        b2 = b
        if e is not None and cnt >= min_f:
            b2 = e - 1
            if half:
                # loop 7 C1: the symmetric RTS smoother spreads a velocity step over several frames centred on the
                # true release, so the release is where v_r crosses half the flight's radial speed (peak over the
                # stretch and the following peak_f frames), not where it first exceeds vmin: a fast pass otherwise
                # cuts 3-5 held frames (true 3.25 s hold -> 2.97 s at sigma_p 0.5). Only for flights faster than the
                # catch rule's catch_max_ball_mps (a soft pass's flight is in the run itself, and its first vmin frame
                # is the release), and never into frames with the ball beyond HOLD_R (out of reach = in flight; a
                # bounce pass decelerating before the catch put the half-speed point 2.3 m from the receiver), and only
                # when the restored frames fit in the smoothed step width peak_f: a slower ramp is the ball really
                # decelerating into the hands (a real SportVU catch at --noise 0.5: -6 -> -2 m/s over 17 frames)
                vp = float(np.max(vr[e:_clip(b + peak_f, scene.n) + 1]))
                thr = max(vmin, 0.5 * vp) if vp >= vfast else vmin
                t = e
                while t <= b and vr[t] < thr and not rv[t] > mvlib.HOLD_R:
                    t += 1
                if t - e <= peak_f:  # a longer ramp is a real (soft) acceleration of the flight, not smoothing
                    b2 = t - 1
        e, cnt = stretch(arr, a, 1, b2 - 1)
        a2 = a
        if e is not None and cnt >= min_f:
            a2 = e + 1
            if half:
                vp = float(-np.min(vr[_clip(a - peak_f, scene.n):e + 1]))
                thr = max(vmin, 0.5 * vp) if vp >= vfast else vmin
                t = e
                while t >= a and vr[t] > -thr and not rv[t] > mvlib.HOLD_R:
                    t -= 1
                if e - t <= peak_f:  # a longer ramp is the flight decelerating into the hands, not smoothing
                    a2 = t + 1
        out.append((h, a2, b2))
    return out


def _clear_cut(scene, e, pmin):
    """Loop 5 C1: a proxy CUT counts against an ISO only when its speed clears event_lattice.move_enter_mps with
    P >= pmin at some frame (p_above with the calibrated speed sigma). Position noise lifts the speed of a 1.5-2 m/s
    relocation over the 2 m/s entry by chance (SportVU --noise 0.5: 11 of 19 off-ball actions that cost real ISOs had
    no clean counterpart)."""
    k = scene.kins[e.actors["cutter"]]
    seg = slice(e.start, e.end + 1)
    pr = p_above(np.nan_to_num(k.speed[seg], nan=0.0), PRM["event_lattice"]["move_enter_mps"], np.nan_to_num(k.sigma_speed[seg], nan=9.0))
    return bool(len(pr)) and float(np.max(pr)) >= pmin


def detect_iso(scene, **params):
    """ISO / clear-out ISO: one holder >= 3 s, no ball-screen evidence, no teammate within 3 m, others spaced."""
    p = _prm("iso", params)
    out = []
    n = scene.n
    _ = primitives(scene)
    runs = _cache(scene)[("prims", repr(sorted(PRM["event_lattice"].items())))][1]
    runs = _extend_holds(scene, runs, p["hold_ext_k"])
    full = runs
    runs = _trim_flights(scene, runs, p["release_vr_mps"], int(p["release_min_frames"]), p["release_p"], int(p["release_gap_frames"]),
                         bool(p["release_half_peak"]), frames(p["release_peak_s"]),
                         PRM["event_lattice"]["catch_max_ball_mps"])
    pad = {(h, a, b): (a0 - a, b0 - b) for (h, a, b), (_, a0, b0) in zip(runs, full)}  # frames trimmed (<= 0, >= 0)
    ons = [e for e in primitives(scene) if e.kind == "SCR.on"]
    fc = (np.nan_to_num(scene.ball.y, nan=99.0) <= C["HALF_Y"]) if scene.ball is not None else np.zeros(n, bool)
    for h, a, b in runs:
        da, db = pad[(h, a, b)]
        # loop 4 L4: only the half-court part of a hold counts (the longest frontcourt stretch of the run); bringing
        # the ball up the floor with teammates spread out is not an isolation. Loop 5 C1: backcourt flickers of the
        # noisy ball shorter than fc_bridge_frames (the frontcourt rule's own 10-frame hold) do not cut the stretch
        sub = hysteresis(fc[a:b + 1], fc[a:b + 1], 0.0, int(p["fc_bridge_frames"]))
        if not sub:
            continue
        a, b = max(((a + i, a + j) for i, j in sub), key=lambda z: z[1] - z[0])
        if (b - a) * DT < p["min_hold_s"]:
            continue
        kh = scene.kins[h]
        aa, bb = _clip(a + da, n), _clip(b + db, n)
        # loop 4 L4: a hold that starts in the post (median r over the first post_window_s < post_max_r_m) is a
        # post-up (its own play type in Synergy), not an isolation. Loop 7 C1: the window is anchored at the
        # untrimmed hold start aa (the catch), like the attack test - the flight trim moved it later and a
        # short-corner back-down caught at r ~4.6 m slid out of the post window into an ISO
        if float(np.nanmedian(kh.r[aa:_clip(aa + frames(p["post_window_s"]), n) + 1])) < p["post_max_r_m"]:
            continue
        # loop 4 L5: an isolation attacks - the handler gets within attack_max_d3_m of the three-point line at some
        # frame of the hold; holding the ball 2-3 m behind the arc while the play is called is not an ISO
        # (loop 6 C1: over the hold plus its trimmed catch / release frames - a catch on the arc is an attack position)
        if not np.nanmin(d3(kh.x[aa:bb + 1], kh.y[aa:bb + 1])) <= p["attack_max_d3_m"]:
            continue
        if any(e.actors["user"] == h and a <= e.t0 <= b and e.conf >= p["screen_p_exclude"] for e in ons):
            continue
        # a clear-out: teammates space and wait; off-ball screens / cuts during the hold (beyond one clear-out
        # relocation) mean motion, not ISO
        offball = [e for e in primitives(scene) if (e.kind == "CUT" or (e.kind.startswith("SCR.") and e.kind != "SCR.on"))
                   and a <= e.t0 <= b and e.conf >= p["screen_p_exclude"]]
        # loop 5 C1: off-ball means the handler's teammates - his own moves (a CUT when holder flicker left him under
        # half of the move's frames) do not count; actions are counted per teammate (a relocation split in two by
        # noise is still one) and a CUT must clear the entry speed with P >= cut_peak_p
        offball = [e for e in offball if (e.actors.get("cutter") or e.actors.get("user")) != h
                   and (e.kind != "CUT" or _clear_cut(scene, e, p["cut_peak_p"]))]
        if len({e.actors.get("cutter") or e.actors.get("user") for e in offball}) > p["max_offball_actions"]:
            continue
        mates = [o for o in scene.offense if o != h]
        pf = np.ones(b - a + 1)
        spaced = np.zeros(b - a + 1)
        side = _ball_side(scene, a) or 1
        for o in mates:
            ko = scene.kins[o]
            d = mvlib.dist(kh, ko)[a:b + 1]
            pf *= np.nan_to_num(p_above(d, p["no_teammate_within_m"], mvlib.sigma_dist(kh, ko)[a:b + 1]), nan=0.0)
            dd = d3(ko.x[a:b + 1], ko.y[a:b + 1])
            spaced += ((dd >= p["spacer_min_d3_m"]) | (ko.x[a:b + 1] * side < -p["weak_side_min_x_m"])).astype(float)
        frac_spaced = float(np.mean(spaced >= p["min_spacers"]))
        clear = window_conf(pf, 0, len(pf) - 1)
        if clear < p["min_clear_conf"] or frac_spaced < p["spaced_frac"]:
            continue
        clear_out = False
        w0 = _clip(a - frames(p["clear_out_lookback_s"]), n)
        for o in mates:
            ko = scene.kins[o]
            d_before = math.dist(pos(scene, o, w0), pos(scene, h, a))
            d_after = math.dist(pos(scene, o, _clip(a + frames(p["clear_out_after_s"]), n)), pos(scene, h, a))
            if d_after - d_before >= p["clear_out_min_m"]:
                clear_out = True
        conf = clear * _factor(scene, scene.offense, a, b, a)
        out.append(Event("iso", {"handler": h}, a, a, b, conf, {"clear_out": clear_out, "spaced_frac": frac_spaced}))
    return out


def detect_motion(scene, cuts=None, **params):
    """Generic motion: off-ball screens + cuts >= 3 per 10 s over >= 8 s, ball screens < 50 %, no set accepted.

    Loop 4 L9: counted per half-court set window (only actions with t0 inside a window of segment_kind
    'halfcourt'): on a real possession the bring-up sprint of four players registers as four CUTs and the
    transition / backcourt part of the clip made almost every possession 'motion'."""
    p = _prm("motion", params)
    lat = build_lattice(scene)
    # loop 5 C5: with the cuts family's events (detect_all(scene, cuts=...) or cuts= here) the cuts are the real
    # off-ball cut events of kinds motion.cut_kinds instead of the proxy CUT; the proxy stays the fallback
    cuts = cuts if cuts is not None else _cache(scene).get("cuts_family")
    if cuts is not None:
        real = [e for e in cuts if e.kind in p["cut_kinds"] and e.actors.get("cutter") in scene.offense]
        acts_all = sorted([e for e in lat if e.kind.startswith("SCR.") and e.kind != "SCR.on"] + real, key=lambda e: e.t0)
    else:
        acts_all = [e for e in lat if e.kind == "CUT" or (e.kind.startswith("SCR.") and e.kind != "SCR.on")]
    ons_all = [e for e in lat if e.kind == "SCR.on" or e.kind == "DHO"]
    if not acts_all:
        return []
    wins = [w for w in detect_set_window(scene) if w.attrs.get("segment_kind") == "halfcourt"]
    out = []
    win = frames(p["min_window_s"])
    accepted = None
    for w in wins:
        acts = [e for e in acts_all if w.start <= e.t0 <= w.end]
        if not acts:
            continue
        t_first = acts[0].t0
        t_last = acts[-1].t0
        if t_last - t_first < win * 0.75:
            continue
        a, b = t_first, max(t_last, t_first + win)
        dur = (b - a) * DT
        rate = len(acts) / dur * 10.0
        share_on = len([e for e in ons_all if a <= e.t0 <= b]) / max(1, len(acts) + len(ons_all))
        if rate < p["min_rate_per_10s"] or share_on >= p["max_on_ball_share"]:
            continue
        if accepted is None:
            accepted = any(e.attrs.get("accepted") for e in detect_set_match(scene))
        if accepted:
            return []
        al = detect_align_snapshot(scene)
        code = al[0].attrs["code"] if al and al[0].attrs["accepted"] else "free"
        label = {"five_out": "5-out motion", "four_out_one_in": "4-out 1-in motion"}.get(code, "motion")
        conf = p["conf_scale"] * min(1.0, rate / p["min_rate_per_10s"]) * _factor(scene, scene.offense, a, b, (a + b) // 2)
        out.append(Event("motion", {}, a, a, b, conf, {"label": label, "rate_per_10s": rate, "on_ball_share": share_on,
                                                       "alignment": code, "cut_source": "proxy" if cuts is None else "cuts_family"}))
    return out


def detect_continuity(scene, **params):
    """Continuity: >= 2 cycles of a motif (Flex) with a ball reversal between, period 3-10 s, within 25 s."""
    p = _prm("continuity", params)
    flex = sorted(detect_flex(scene), key=lambda e: e.t0)
    out = []
    i = 0
    while i < len(flex):
        chain = [flex[i]]
        for e in flex[i + 1:]:
            per = (e.t0 - chain[-1].t0) * DT
            rev = _reversal_between(scene, chain[-1].t0, e.t0)
            if p["period_s"][0] <= per <= p["period_s"][1] and rev and (e.t0 - chain[0].t0) * DT <= p["max_span_s"]:
                chain.append(e)
        if len(chain) >= p["min_cycles"]:
            pers = [(b.t0 - a.t0) * DT for a, b in zip(chain, chain[1:])]
            out.append(Event("continuity", {"cutter_1": chain[0].actors["cutter"]}, chain[0].t0, chain[0].start, chain[-1].end,
                             min(c.conf for c in chain), {"code": "flex", "cycle_count": len(chain),
                                                          "cycle_period_s": float(np.mean(pers))}))
            i += len(chain)
        else:
            i += 1
    return out


def _reversal_between(scene, a, b, dead=None):
    """REVERSAL: the ball's side (sign of x, dead band mirror.dead_band_m) changes between frames a and b."""
    sides = {_ball_side(scene, t, dead) for t in range(a, b + 1)} - {0}
    return sides == {1, -1}


def detect_style_measures(scene, **params):
    """Per-window style measures (R-ST-25 input): rates per 10 s of passes, screens, cuts, DHOs, drives, reversals."""
    p = _prm("style_measures", params)
    out = []
    lat = build_lattice(scene, components=False)
    for w in _halfcourt_windows(scene):
        a, b = w.start, w.end
        dur = max((b - a) * DT, p["min_window_s"])
        ev = [e for e in lat if a <= e.t0 <= b]
        cnt = lambda pred: sum(1 for e in ev if pred(e)) / dur * 10.0
        paint = 0.0
        if scene.ball is not None:
            inp = (np.abs(scene.ball.x[a:b + 1]) <= C["LANE_X"]) & (scene.ball.y[a:b + 1] <= C["FT_Y"])
            paint = float(len(hysteresis(inp, inp, p["paint_touch_min_s"])))
        rev = 0
        last = 0
        for t in range(a, b + 1):
            s = _ball_side(scene, t)
            if s and last and s != last:
                rev += 1
            last = s or last
        rates = {"passes": cnt(lambda e: e.kind == "PASS"), "ball_screens": cnt(lambda e: e.kind == "SCR.on"),
                 "off_ball_screens": cnt(lambda e: e.kind.startswith("SCR.") and e.kind != "SCR.on"),
                 "cuts": cnt(lambda e: e.kind == "CUT"), "dhos": cnt(lambda e: e.kind == "DHO"),
                 "drives": cnt(lambda e: e.kind == "DRIVE"), "reversals": rev / dur * 10.0, "paint_touches": paint / dur * 10.0}
        out.append(Event("style", {}, a, a, b, w.conf, {"per_10s": rates, "window_s": (b - a) * DT}))
    return out


# --------------------------------------------------------------------------------------
# Set windows and resets (CE-R01, CE-R02)
# --------------------------------------------------------------------------------------
ACTION_KINDS = ("SCR", "CUT", "DRIVE", "DHO", "ROLL", "POP")


def detect_reset(scene, **params):
    """Reset inside a chance (fixed CE-R02): quiet 1.5 s, ball outside the arc, relative team slow-down,
    and a re-ALIGN or a retreat dribble; >= 3 s after the current set t0; cancelled by an action within 0.5 s."""
    p = _prm("reset", params)
    al = detect_align_snapshot(scene)
    if not al:
        return []
    n = scene.n
    prims = primitives(scene)
    acts = [e for e in prims if e.kind.split(".")[0] in ACTION_KINDS]
    t_open = al[0].t0
    quiet = frames(p["quiet_s"])
    prev = frames(p["prev_window_s"])
    out = []
    set_t0 = next((e.t0 for e in acts if e.t0 >= t_open), None)
    t = t_open + quiet
    spd = np.vstack([np.nan_to_num(scene.kins[o].speed, nan=0.0) for o in scene.offense])
    sig = np.vstack([np.nan_to_num(scene.kins[o].sigma_speed, nan=1.0) for o in scene.offense])
    team = spd.mean(axis=0)
    team_sig = np.sqrt((sig ** 2).mean(axis=0) / len(scene.offense))
    while t < n and set_t0 is not None:
        if t < set_t0 + frames(p["min_after_set_s"]):
            t += 1
            continue
        busy = any(e.end >= t - quiet and e.start <= t for e in acts)
        h = next((_H(scene)[j] for j in range(t, max(-1, t - quiet), -1) if _H(scene)[j] is not None), None)
        bx, by = ball_pos(scene, t)
        ok = not busy and h is not None and np.isfinite(bx) and float(d3(bx, by)) >= p["ball_min_d3_m"]
        if ok:
            kh = scene.kins[h]
            ok = float(np.nanmean(kh.speed[_clip(t - frames(p["handler_window_s"]), n):t + 1])) < p["handler_max_mps"]
        if ok:
            now = float(team[t - quiet:t + 1].mean())
            before = float(team[max(0, t - quiet - prev):t - quiet].mean()) if t - quiet > 0 else np.nan
            ok = np.isfinite(before) and now < p["team_slow_frac"] * before
        trig = None
        if ok:
            re_ok, code = _align_accepted_at(scene, t)
            if re_ok:
                # loop 1 F16: a re-ALIGN counts only when the ball went back out (d3 >= re_align_min_ball_d3_m) or
                # was pulled >= re_align_pull_out_m away from the rim since the closest point in the last
                # quiet_s + prev_window_s; a team standing still after a PnR is not a reset
                rb = np.hypot(scene.ball.x, scene.ball.y)
                lo = _clip(t - quiet - prev, n)
                pulled = float(rb[t] - np.nanmin(rb[lo:t + 1])) if np.any(np.isfinite(rb[lo:t + 1])) else 0.0
                re_ok = float(d3(bx, by)) >= p["re_align_min_ball_d3_m"] or pulled >= p["re_align_pull_out_m"]
            if re_ok:
                trig = "re_align"
            else:
                vr = np.nan_to_num(kh.v_r[t - quiet:t + 1], nan=0.0) <= -p["retreat_min_mps"]
                ivs = hysteresis(vr, vr, p["retreat_min_s"], 2)
                if ivs and kh.r[t - quiet + ivs[-1][1]] >= p["retreat_end_r_m"]:
                    trig = "retreat_dribble"
        if trig:
            nxt = [e for e in acts if t < e.t0 <= t + frames(p["cancel_window_s"])]
            if not nxt:
                a = t - quiet
                pc = window_conf(p_below(team, p["team_slow_frac"] * before, team_sig), a, t)
                conf = pc * _factor(scene, scene.offense, a, t, t)
                out.append(Event("reset", {"handler": h}, t, a, t, conf, {"trigger": trig, "team_speed_mps": now,
                                                                         "team_speed_before_mps": before}))
                set_t0 = next((e.t0 for e in acts if e.t0 > t), None)
                t += 1
                continue
        t += 1
    return out


TRANSITION_NAME = "transition_early"


def _halfcourt_windows(scene):
    """Half-court set windows only (loop 5 C6: name and style events are emitted for these, not for transition_early)."""
    return [w for w in detect_set_window(scene) if w.attrs.get("segment_kind") != "transition_early"]


def _window_conf(scene, a, b):
    """Window conf (loop 1 F8): gap factor over [a, b] x edge factor at the window midpoint (the evidence frame),
    worst attacker; never the edge factor of a bookkeeping boundary frame (a window opening at clip frame 0)."""
    return _factor(scene, scene.offense, a, b, (a + b) // 2)


def _rim_before(scene, a, p):
    """Loop 5 C3: the ball was within scramble_rim_r_m of the rim (XY) at some frame of [a - scramble_lookback_s, a].
    XY only by default; with use_ball_z and a scene.ball_z (SportVU) a ball above rim height (>= rim_z_m) within
    scramble_rim_z_r_m also counts. Production video has no reliable ball height, so the XY test is the default."""
    if scene.ball is None:
        return False
    lo = _clip(a - frames(p["scramble_lookback_s"]), scene.n)
    bx, by = scene.ball.x[lo:a + 1], scene.ball.y[lo:a + 1]
    rb = np.hypot(bx, by)
    # loop 6 C3: a dead-ball inbound is no scramble. (1) Lookback frames with the ball out of bounds (behind the
    # baseline or past a sideline) are not rim frames; (2) when a holder run in the lookback is an inbound - the
    # holder's median position over his frames there is out of bounds - the window opens on a dead ball (BLOB / SLOB
    # play, after-timeout inbound), so it is a set however near the rim the inbounder stood (synthetic BLOB quick
    # hitter: 10/10 -> 0/10 under the loop-5 rule)
    if p["scramble_inbound_excl"]:
        if _inbound_in(scene, lo, a, p):
            return False
        # loop 7 C3: a lookback frame is an out-of-bounds (non-rim) frame only when the ball is beyond the line by
        # inbound_oob_k x its calibrated position sigma at that frame (a ball 0.15 m inside the baseline under
        # sigma_p 0.5 noise read out of bounds on single frames and turned a putback into a set)
        sb = mvlib.K_CAL * np.sqrt(np.nan_to_num(scene.ball.var_p[lo:a + 1], nan=0.09))
        mg = p["inbound_oob_k"] * sb
        oob = (np.nan_to_num(by, nan=0.0) < C["END_Y"] - mg) | (np.abs(np.nan_to_num(bx, nan=0.0)) > C["SIDE_X"] + mg)
        rb = np.where(oob, np.inf, rb)
    if np.any(np.nan_to_num(rb, nan=99.0) < p["scramble_rim_r_m"]):
        return True
    bz = getattr(scene, "ball_z", None)
    if p["use_ball_z"] and bz is not None:
        z = np.asarray(bz, float)[lo:a + 1]
        return bool(np.any((np.nan_to_num(z, nan=0.0) >= p["rim_z_m"]) & (np.nan_to_num(rb, nan=99.0) < p["scramble_rim_z_r_m"])))
    return False


def _run_frames(H, o, lo, hi):
    """Frames of the holder runs of o that touch [lo, hi], each run taken whole (it may extend past hi)."""
    n, out, t = len(H), [], lo
    while t <= hi:
        if H[t] != o:
            t += 1
            continue
        a = t
        while a > 0 and H[a - 1] == o:
            a -= 1
        b = t
        while b + 1 < n and H[b + 1] == o:
            b += 1
        out.extend(range(a, b + 1))
        t = b + 1
    return out


def _inbound_in(scene, lo, hi, p=None):
    """Loop 6 C3, loop 7 C3, loop 8 C3: True when an attacker holds the ball in [lo, hi] (hard holder) on a dead ball
    out of bounds, judged over his whole holder run(s) touching [lo, hi]. Two independent routes:
    (a) ball route: the ball's median position is out of bounds (the ball itself is held outside) and the mean of
        the holder's and the ball's medians is beyond the line by inbound_oob_k sigma of that mean
        (0.5 x hypot(sigma_holder, sigma_ball));
    (b) holder route (loop 8): the holder's median alone is beyond the line by inbound_oob_k x sigma_holder and the
        ball median is no farther in bounds than inbound_reach_m (arm reach from the body centre): an inbounder just
        behind the line holds the ball out in front of his body, over the plane, so the ball is not a measurement of
        where he stands and the holder must carry the margin alone.
    The sigma of each median is the median per-frame calibrated sigma (K_CAL x sqrt(var_p)), not divided by sqrt(n):
    smoothed errors are correlated over a <= 1 s hold, and the measured median error on the synthetic rebounder (sd
    0.15-0.18 m at sigma_p 0.5) matches the per-frame value (0.19-0.22 m). Loop 6 tested the holder median alone
    with no margin, over the lookback frames only (one frame when the window opens at clip frame 0), so an in-bounds
    rebounder 0.15 m inside the baseline read as an inbounder under noise."""
    p = p or PRM["set_window"]
    kz = p["inbound_oob_k"]
    H = _H(scene)
    b = scene.ball
    for o in {H[t] for t in range(lo, hi + 1)} - {None}:
        fr = _run_frames(H, o, lo, hi)
        k = scene.kins[o]
        bxf, byf = b.x[fr], b.y[fr]
        if not np.any(np.isfinite(bxf)):
            continue
        sh = float(np.nanmedian(mvlib.K_CAL * np.sqrt(k.var_p[fr])))
        sb = float(np.nanmedian(mvlib.K_CAL * np.sqrt(b.var_p[fr])))
        sh, sb = (sh if np.isfinite(sh) else 0.3), (sb if np.isfinite(sb) else 0.3)
        mx, my = float(np.nanmedian(k.x[fr])), float(np.nanmedian(k.y[fr]))
        bmx, bmy = float(np.nanmedian(bxf)), float(np.nanmedian(byf))
        # (a) the holder and the ball are two independent measurements of where the inbound stands (ball within
        # HOLD_R of him): their mean has sigma 0.5 x hypot(sh, sb); the ball median itself must be out of bounds
        # (the dead-ball evidence: the ball is held outside, not just a player standing near the line). A source
        # that knows the game clock may instead set scene.clock_stop_start (clock stopped at the clip start); it
        # counts only for a lookback that reaches the clip's first frame. Nothing sets it today (video has no clock).
        # (b) loop 8: the holder alone beyond the line by kz x sh, the ball within arm reach (inbound_reach_m) of it
        sc = 0.5 * math.hypot(sh, sb)
        clk = bool(getattr(scene, "clock_stop_start", False)) and lo == 0
        reach = p["inbound_reach_m"]
        base = ((bmy < C["END_Y"] or clk) and (my + bmy) / 2 < C["END_Y"] - kz * sc) or (
            my < C["END_Y"] - kz * sh and bmy < C["END_Y"] + reach)
        side = ((abs(bmx) > C["SIDE_X"] or clk) and (abs(mx) + abs(bmx)) / 2 > C["SIDE_X"] + kz * sc) or (
            abs(mx) > C["SIDE_X"] + kz * sh and abs(bmx) > C["SIDE_X"] - reach)
        if base or side:
            return True
    return False


def detect_set_window(scene, **params):
    """Set windows of the clip (CE-R01): open at ALIGN t_snap / first frontcourt action, close at the first of
    ball back in the backcourt (>= 10 frames), shot proxy, reset (new window) or clip end."""
    p = _prm("set_window", params)
    n = scene.n
    t_front = _frontcourt_frame(scene, PRM["align_snapshot"])
    if t_front is None:
        return []
    al = detect_align_snapshot(scene)
    acts = [e for e in primitives(scene) if e.t0 >= t_front]
    cands = [x for x in [al[0].t0 if al else None, acts[0].t0 if acts else None] if x is not None]
    if not cands:
        return []
    t_open = min(cands)
    t_close, reason = n - 1, "clip_end"
    back = np.nan_to_num(scene.ball.y, nan=0.0) > C["HALF_Y"]
    H = _H(scene)
    for a, b in hysteresis(back, back, (PRM["align_snapshot"]["frontcourt_hold_frames"] - 1) * DT):
        if a > t_open:
            t_close, reason = a, "backcourt"
            # loop 4 L3: the offense itself carries / passes the ball back over half court (no shot, no defensive
            # control in between): a backcourt violation in a real frame, and on SportVU the signature of a stretch
            # whose attacked end belongs to the other team (the offense walks the ball up from under 'our' rim)
            rw = frames(p["retreat_holder_s"])
            if any(H[_clip(j, n)] is not None for j in range(a - rw, a + rw + 1)):
                reason = "offense_retreat"
            break
    # shot proxy (loop 1 F7): a ball flight of >= shot_min_free_frames frames with no holder that moves toward the
    # rim, and the ball inside shot_end_r_m of the rim within shot_holder_grace_s after the flight's last free frame
    # (a holder that appears in that grace, e.g. a roller under the rim, is ignored)
    H = _H(scene)
    rb = np.hypot(scene.ball.x, scene.ball.y)
    m = int(p["shot_min_free_frames"])
    g = frames(p["shot_holder_grace_s"])
    for t in range(t_open, t_close):
        if not (np.isfinite(rb[t]) and rb[t] < p["shot_end_r_m"]):
            continue
        hit = False
        for j in range(max(t_open + m - 1, t - g), t + 1):
            run = range(j - m + 1, j + 1)
            if all(H[i] is None and np.isfinite(rb[i]) for i in run) and rb[j - m + 1] > rb[j]:
                hit = True
                break
        if hit:
            t_close, reason = t, "shot_proxy"
            break
    if reason == "offense_retreat":
        return []
    cuts = [r.t0 for r in detect_reset(scene) if t_open < r.t0 < t_close]
    bounds = [t_open] + cuts + [t_close]
    out = []
    # transition / early segment: lattice events between team control and t_open (CE-R01; S4a / S4b)
    tc = _t_control(scene, params)
    if tc is not None and tc < t_open:
        early = [e for e in build_lattice(scene) if e.kind != "align" and tc <= e.t0 < t_open]
        if early:
            a = min(e.t0 for e in early)
            # loop 5 C6: a transition / early window carries the fixed name 'transition_early' and gets no name /
            # style event (names count about one per half-court possession)
            out.append(Event("set_window", {}, a, a, t_open - 1, _window_conf(scene, a, t_open - 1),
                             {"close_reason": "halfcourt_open", "segment_kind": "transition_early", "window_index": -1,
                              "transition_early_f": [tc, t_open - 1], "name": TRANSITION_NAME}))
    for i, (a, b) in enumerate(zip(bounds, bounds[1:])):
        if (b - a) * DT < p["min_window_s"] and out and out[-1].attrs["segment_kind"] == "halfcourt":
            out[-1].end = b  # merge a too-short window into its neighbour
            continue
        if (b - a) * DT < p["min_window_s"] and len(bounds) == 2:
            continue  # loop 4 L3: a lone half-court window shorter than min_window_s (a touch before a shot) is no set
        if i == 0 and (b - a) * DT < p["scramble_max_s"] and _rim_before(scene, a, p):
            continue  # loop 5 C3: a short window opened by a ball at the rim (putback / tip scramble) is no set
        why = "reset" if i < len(cuts) else reason
        conf = _window_conf(scene, a, b)
        out.append(Event("set_window", {}, a, a, b, conf,
                         {"close_reason": why, "segment_kind": "halfcourt", "window_index": i,
                          "transition_early_f": [_t_control(scene, params), a - 1] if i == 0 else None}))
    return out


# --------------------------------------------------------------------------------------
# Matcher (CE-R07..CE-R11 fixed): role-bound timed weighted edit distance, beam search
# --------------------------------------------------------------------------------------
def _kind_match(pattern, kind):
    if isinstance(pattern, (list, tuple)):
        return any(_kind_match(q, kind) for q in pattern)
    return kind == pattern or kind.startswith(pattern + ".")


def _subst(pattern, kind):
    """Substitution cost S(step pattern, observed kind) in [0, 1] from the substitution item."""
    if _kind_match(pattern, kind):
        return 0.0
    pats = pattern if isinstance(pattern, (list, tuple)) else [pattern]
    best = 1.0
    for a, b, s in PRM["substitution"]["pairs"]:
        for q in pats:
            if (q == a and kind == b) or (q == b and kind == a):
                best = min(best, s)
    return best


def _box_dist(x, y, box):
    """Distance (m) from a point to an axis box / radial band; 0 inside."""
    dx = dy = 0.0
    if "x" in box:
        lo, hi = box["x"]
        dx = max(lo - x, 0.0, x - hi)
    if "y" in box:
        lo, hi = box["y"]
        dy = max(lo - y, 0.0, y - hi)
    d = math.hypot(dx, dy)
    if "r" in box:
        r = math.hypot(x, y)
        lo, hi = box["r"]
        d = max(d, lo - r, r - hi, 0.0)
    return d


def _ins_weight(e, binding_vals, p):
    involved = [v for v in e.actors.values() if v in binding_vals]
    if not involved:
        return p["w_ins_spacer"]  # unbound / spacer actions: small cost (still kept in action_sequence)
    if e.kind in ("PASS", "DHO", "DRIVE", "SCR.on"):
        return p["w_ins_ball"]
    return p["w_ins_bound_offball"]


def _covered(e, used_events):
    """A primitive is explained by a matched event when it lies inside a matched component (same actors,
    inside its span), or when it is the screener's own CUT during a matched ROLL / POP (the read's path)."""
    for u in used_events:
        if u is e:
            continue
        if u.kind[0].islower() and e.start <= u.end and e.end >= u.start and set(e.actors.values()) <= set(u.actors.values()):
            return True
        if u.kind in ("ROLL", "POP") and e.kind == "CUT" and e.actors.get("cutter") == u.actors.get("screener") \
                and e.start <= u.end and e.end >= u.t0:
            return True
        if e.kind[0].islower() and u.kind[0].islower() and e.start <= u.end and e.end >= u.start \
                and len(set(e.actors.values()) & set(u.actors.values())) >= 2:
            return True  # an alternative component reading of the same action (e.g. Floppy vs Elevator exit)
    return False


def _unify(T, rmap, e, bind):
    """Extend binding `bind` with the event's actors for role map rmap; None when unification fails."""
    nb = dict(bind)
    eq_groups = T.get("equal_roles", [])
    for ak, role in rmap.items():
        oid = e.actors.get(ak)
        if oid is None:
            return None
        if role in nb:
            if nb[role] != oid:
                return None
            continue
        eq = {r for grp in eq_groups if role in grp for r in grp}
        if any(v == oid and r != role and r not in eq for r, v in nb.items()):
            return None  # distinct roles must be distinct players unless declared equal
        nb[role] = oid
    return nb


def match_template(scene, T, lattice, align_ev=None, sign=1, swaps=None, **params):
    """Best alignment path of template T (mirror sign) over the lattice.

    Returns a dict with C, W, c_hat, frac_required, path, binding, insertions, t0, used events.
    Costs (CE-R09 with the fixes in this file's 'matcher' item):
      matched step  = min(-ln p, cap) + 2 S + 0.5 (dt_out / sigma_t)^2 + 0.5 (d_sp / sigma_s)^2
      deleted step  = w_del (x unobservable_factor when the bound actor is not visible)
      insertions    = only events between the first matched t_ref and the last matched t_end that involve a
                      bound role and are not explained by a matched component; total capped at ins_cap_frac x W
      alignment     = -ln P(alignment in T.alignments), capped; prior binding cost per ALIGN-slot disagreement
      C_hat         = C / W with W = sum of step weights (single normalisation for ranking and acceptance)
    """
    p = _prm("matcher", params)
    if swaps:
        # tracker id swaps (t_f, a, b): allow one re-binding by exchanging a and b from t_f on, at a fixed cost
        best = match_template(scene, T, lattice, align_ev, sign, None, **params)
        cost = PRM["role_binding"]["swap_rebind_cost"]
        for swp in swaps:
            t_f, a, b = swp[:3]
            # a reported swap may carry its ambiguity window (s) as a 4th element; only swaps resolved within
            # role_binding.swap_window_s may re-bind (loop 1 F12)
            if len(swp) > 3 and swp[3] is not None and swp[3] > PRM["role_binding"]["swap_window_s"]:
                continue
            sw = {a: b, b: a}
            lat2 = [Event(e.kind, {k: (sw.get(v, v) if e.t0 >= t_f else v) for k, v in e.actors.items()}, e.t0, e.start,
                          e.end, e.conf, e.attrs) for e in lattice]
            r = match_template(scene, T, lat2, align_ev, sign, None, **params)
            r["C"] += cost
            r["c_hat"] = r["C"] / r["W"]
            r["swap"] = (t_f, a, b)
            if r["C"] < best["C"]:
                best = r
        return best
    steps = T["steps"]
    W = sum(p["w_required"] if s.get("weight", "required") == "required" else p["w_optional"] for s in steps)
    if not _any_step_matchable(steps, lattice):
        # exact prefilter (CE-R20, loop 1 F12): no lattice event can fill any step, so the best path is all-deleted;
        # build it directly instead of running the beam
        path = tuple((st["id"], None, {"deleted": p["w_required"] if st.get("weight", "required") == "required" else p["w_optional"],
                                       "unobservable": False}) for st in steps)
        best = dict(C=sum(pp["deleted"] for _, _, pp in path), path=path, binding={}, used=(), ins=[], t0=None, span=None)
        c_al, c_bind = _align_cost(T, align_ev, {}, p)
        best["C"] += c_al + c_bind
        best["c_align"], best["c_bind"] = c_al, c_bind
        best.update(W=W, c_hat=best["C"] / W, frac_required=0.0, sign=sign, template=T["id"], prefiltered=True)
        return best
    beam = [(0.0, {}, (), (), {}, None)]  # cost, binding, used idx, path, lane_last {lane: (tref, step_id)}, first t
    for st in steps:
        req = st.get("weight", "required") == "required"
        w_del = p["w_required"] if req else p["w_optional"]
        lane = st.get("lane", "main")
        new = []
        for cost, bind, used, path, lanes, first in beam:
            # deletion (unobservable bound actor -> reduced cost, flagged)
            unobs = False
            for role in st.get("roles", {}).values():
                oid = bind.get(role)
                if oid is not None and oid in scene.kins:
                    a = lanes.get(lane, (first or 0, None))[0]
                    lo = _clip(a, scene.n)
                    hi = _clip(a + frames(st.get("window_s", p["default_window_s"])[1]), scene.n)
                    if gap_factor(scene.kins[oid], lo, hi) == 0.0:
                        unobs = True
            dc = w_del * (p["unobservable_factor"] if unobs else 1.0)
            new.append((cost + dc, bind, used, path + ((st["id"], None, {"deleted": dc, "unobservable": unobs}),), lanes, first))
            for i, e in enumerate(lattice):
                if i in used:
                    continue
                S = _subst(st["kind"], e.kind)
                counter = None
                for ct in st.get("counters", []):
                    if _kind_match(ct["kind"], e.kind):
                        counter = ct
                if S >= 1.0 and counter is None:
                    continue
                # unification of roles (roles_alt lists alternative actor -> role maps, e.g. 'by s or by z')
                nb = None
                for rmap in [st.get("roles", {})] + list(st.get("roles_alt", [])):
                    cand = _unify(T, rmap, e, bind)
                    if cand is not None:
                        nb = cand
                        break
                if nb is None:
                    continue
                # timing relative to the lane anchor (or the first matched step for a new lane)
                sig_t = math.sqrt(p["sigma_t_s"] ** 2 + e.attrs.get("sigma_t_ref_s", p["sigma_t_ref_default_s"]) ** 2)
                anchor = lanes.get(lane, (first, None))[0]
                lo, hi = st.get("window_s", p["default_window_s"])
                if st.get("group") and lanes.get(lane, (None, None))[1] in T.get("_groups", {}).get(st["group"], ()):
                    lo, hi = -p["parallel_tol_s"], p["parallel_tol_s"]
                if anchor is None:
                    dt_out = 0.0
                else:
                    dt = (e.t0 - anchor) * DT
                    if dt < lo - 3 * sig_t or dt > hi + 3 * sig_t:
                        continue
                    dt_out = max(0.0, lo - dt, dt - hi)
                # space
                d_sp = 0.0
                reg = st.get("region")
                if reg:
                    oid = nb.get(reg["role"])
                    if oid is not None:
                        x, y = pos(scene, oid, e.t0)
                        d_sp = _box_dist(sign * x, y, reg["box"])
                        sig_s = math.sqrt(p["sigma_s_m"] ** 2 + _sigma_track(scene, [oid], e.t0) ** 2)
                    else:
                        sig_s = p["sigma_s_m"]
                else:
                    sig_s = p["sigma_s_m"]
                c_ev = min(-math.log(max(e.conf, 1e-9)), p["neglogp_cap"])
                c_sub = counter["cost"] if counter is not None else 2.0 * S
                c = c_ev + c_sub + 0.5 * (dt_out / sig_t) ** 2 + 0.5 * (d_sp / sig_s) ** 2
                parts = {"event": c_ev, "type": c_sub, "time": 0.5 * (dt_out / sig_t) ** 2, "space": 0.5 * (d_sp / sig_s) ** 2,
                         "counter": counter["code"] if counter else None, "dt_out_s": dt_out}
                nl = dict(lanes)
                nl[lane] = (e.t0, st["id"])
                new.append((cost + c, nb, used + (i,), path + ((st["id"], i, parts),), nl, first if first is not None else e.t0))
        new.sort(key=lambda h: (h[0], h[3].__repr__()))
        beam = new[: int(p["beam"])]
    best = None
    for cost, bind, used, path, lanes, first in beam:
        if not used:
            res = dict(C=cost, path=path, binding=bind, used=used, ins=[], t0=None, span=None)
        else:
            ev_used = [lattice[i] for i in used]
            a = min(e.t0 for e in ev_used)
            b = max(e.end for e in ev_used)
            vals = set(bind.values())
            ins, c_ins = [], 0.0
            for j, e in enumerate(lattice):
                if j in used or not (a <= e.t0 <= b) or _covered(e, ev_used):
                    continue
                w = _ins_weight(e, vals, p)
                if w > 0:
                    ins.append(j)
                    c_ins += w
            c_ins = min(c_ins, p["ins_cap_frac"] * W)
            first_req = next((lattice[i].t0 for sid, i, _ in path if i is not None), a)
            res = dict(C=cost + c_ins, path=path, binding=bind, used=used, ins=ins, t0=first_req, span=(a, b), c_ins=c_ins)
        # alignment and binding priors
        c_al, c_bind = _align_cost(T, align_ev, res["binding"], p)
        res["C"] += c_al + c_bind
        res["c_align"], res["c_bind"] = c_al, c_bind
        if best is None or res["C"] < best["C"]:
            best = res
    req_ids = [s["id"] for s in steps if s.get("weight", "required") == "required"]
    matched = {sid for sid, i, _ in best["path"] if i is not None}
    best.update(W=W, c_hat=best["C"] / W, frac_required=(len([s for s in req_ids if s in matched]) / max(1, len(req_ids))),
                sign=sign, template=T["id"])
    return best


def _any_step_matchable(steps, lattice):
    """True when at least one lattice event could fill at least one step (substitution S < 1 or a listed counter)."""
    kinds = {e.kind for e in lattice}
    for st in steps:
        for k in kinds:
            if _subst(st["kind"], k) < 1.0 or any(_kind_match(ct["kind"], k) for ct in st.get("counters", [])):
                return True
    return False


def _align_cost(T, align_ev, binding, p):
    al = T.get("alignments", "any")
    if al == "any" or not al:
        return 0.0, 0.0
    if align_ev is None:
        return p["c_align_missing"], 0.0
    probs = dict(align_ev.attrs["probs_top3"])
    pa = sum(probs.get(c, 0.0) for c in al)
    c_al = min(-math.log(pa), p["c_align_cap"]) if pa > 0 else p["c_align_cap"]
    c_bind = 0.0
    slots = {v: k for k, v in align_ev.actors.items()}
    for role, grp in (T.get("align_slots") or {}).items():
        oid = binding.get(role)
        if oid is not None and align_ev.attrs["code"] in al and not str(slots.get(oid, "")).startswith(grp):
            c_bind += p["binding_disagree_cost"]
    return c_al, c_bind


def _template_groups(T):
    g = {}
    for s in T["steps"]:
        if s.get("group"):
            g.setdefault(s["group"], set()).add(s["id"])
    T["_groups"] = g
    return T


for _T in TEMPLATES:
    _template_groups(_T)


def score_templates(scene, lattice, align_ev=None, templates=None, **params):
    """Score every template in both mirrors; probabilities over candidates + NULL (CE-R11 fixed).

    s_T = -C_hat_T / tau + ln pi(T) + len_prior x n_matched_required  (one normalisation, C_hat)
    s_NULL = -c_null / tau
    Candidates must match >= floor_required_frac of their required steps; acceptance needs
    C_hat <= c_null, the floor, and P >= p_probable.
    """
    pm = _prm("probability", params)
    templates = templates or TEMPLATES
    res = []
    for T in templates:
        r1 = match_template(scene, T, lattice, align_ev, sign=1)
        r2 = match_template(scene, T, lattice, align_ev, sign=-1)
        r = r1 if r1["C"] <= r2["C"] else r2
        r["mirrored"] = r is r2
        r["side_ambiguous"] = abs(r1["C"] - r2["C"]) < PRM["mirror"]["ambiguous_cost"]
        r["T"] = T
        res.append(r)
    cands = [r for r in res if r["frac_required"] >= pm["floor_required_frac"]]
    s = []
    for r in cands:
        n_req = sum(1 for sid, i, _ in r["path"] if i is not None
                    and next(st for st in r["T"]["steps"] if st["id"] == sid).get("weight", "required") == "required")
        s.append(-r["c_hat"] / pm["tau"] + math.log(r["T"].get("prior", 1.0)) + pm["len_prior"] * n_req)
    s_null = -pm["c_null"] / pm["tau"]
    allv = np.array(s + [s_null])
    pr = np.exp(allv - allv.max())
    pr /= pr.sum()
    for r, pv in zip(cands, pr[:-1]):
        r["P"] = float(pv)
    for r in res:
        r.setdefault("P", 0.0)
        r["accepted"] = (r["c_hat"] <= pm["c_null"] and r["frac_required"] >= pm["floor_required_frac"] and r["P"] >= pm["p_probable"])
    res.sort(key=lambda r: (-r["P"], r["c_hat"], r["template"]))
    return res, float(pr[-1])


def _window_lattice(lattice, w):
    return [e for e in lattice if w.start <= e.t0 <= w.end or (e.kind == "align" and w.attrs.get("window_index") == 0)]


def _align_in(scene, w):
    al = detect_align_snapshot(scene)
    if al and w.start - frames(1.0) <= al[0].t0 <= w.end:
        return al[0]
    return None


def _set_events(scene, w, lat, scored, p_null):
    out = []
    pm = PRM["probability"]
    for r in scored[:5]:
        if not r["accepted"]:
            continue
        T = r["T"]
        evs = [lat[i] for i in r["used"]]
        a, b = r["span"]
        actors = dict(r["binding"])
        conf = r["P"] * _factor(scene, list(actors.values()), a, b, r["t0"])
        dep = departure(r, lat)
        out.append(Event("set", actors, r["t0"], a, b, conf,
                         {"set_code": T["namespace"] + T["id"], "name": T["name"], "family_code": T.get("family_code"),
                          "P": r["P"], "c_hat": r["c_hat"], "frac_required": r["frac_required"], "mirrored": r["mirrored"],
                          "side_ambiguous": r["side_ambiguous"], "probable": r["P"] < pm["p_display"],
                          "top_k": [(x["T"]["namespace"] + x["template"], x["P"], x["c_hat"], x["mirrored"]) for x in scored[:5]],
                          "null_prob": p_null, "path": r["path"], "insertions": r["ins"], "accepted": True,
                          "counter_codes": [pp.get("counter") for _, i, pp in r["path"] if i is not None and pp.get("counter")],
                          "departure": dep, "status": T.get("status"), "action_ids": [lat.index(e) for e in evs]}))
    return out


def detect_set_match(scene, **params):
    """Named sets per set window: the accepted templates (top-5 stored), as 'set' events."""
    key = ("set_match", tuple(sorted(params.items())))
    cache = _cache(scene)
    if key in cache:
        return cache[key]
    lat = build_lattice(scene)
    out = []
    for w in _halfcourt_windows(scene):
        wl = _window_lattice(lat, w)
        al = _align_in(scene, w)
        scored, p_null = score_templates(scene, wl, al, **params)
        out += _set_events(scene, w, wl, scored, p_null)
    cache[key] = out
    return out


def departure(r, lattice, **params):
    """Departure step on an alignment path (CE-R12 fixed): first required step deleted, too costly or too late,
    with the steps after it staying bad; prefix flag when >= 2 required steps matched cleanly before it."""
    p = _prm("departure", params)
    T = r["T"]
    W_req = PRM["matcher"]["w_required"]
    steps = {s["id"]: s for s in T["steps"]}
    path = r["path"]
    for k, (sid, i, parts) in enumerate(path):
        st = steps[sid]
        if st.get("weight", "required") != "required":
            continue
        if i is not None and parts.get("counter"):
            continue  # a listed counter continues the play: no departure
        step_cost = parts.get("deleted", 0.0) if i is None else sum(v for kk, v in parts.items() if kk in ("event", "type", "time", "space"))
        late = i is not None and parts.get("dt_out_s", 0.0) > p["late_s"]
        if not (i is None or step_cost > p["step_cost"] or late):
            continue
        rest = [pp for _, _, pp in path[k + 1:]]
        rest_cost = [pp.get("deleted", 0.0) if "deleted" in pp else sum(v for kk, v in pp.items() if kk in ("event", "type", "time", "space")) for pp in rest]
        if rest and np.mean(rest_cost) / W_req <= PRM["probability"]["c_null"]:
            continue  # later steps match well: a single detector miss, not a departure
        prefix = [(s2, i2, pp) for s2, i2, pp in path[:k] if steps[s2].get("weight", "required") == "required"]
        pref_cost = [sum(v for kk, v in pp.items() if kk in ("event", "type", "time", "space")) for _, i2, pp in prefix if i2 is not None]
        start_matched = len(pref_cost) >= p["prefix_min_steps"] and len(pref_cost) == len(prefix) and \
            (np.mean(pref_cost) / W_req if pref_cost else 9) <= PRM["probability"]["c_null"]
        t_k = lattice[i].t0 if i is not None else None
        return {"step": sid, "index": k, "deleted": i is None, "cost": step_cost, "late": late, "t_f": t_k,
                "start_matched_continuation_unknown": bool(start_matched), "cause": "read"}
    return None


def _best_live(scored):
    """Best template with >= 1 matched step, ranked by the probability score without the acceptance floor."""
    pm = PRM["probability"]
    live = [r for r in scored if any(i is not None for _, i, _ in r["path"])]
    if not live:
        return None

    def s(r):
        steps = {st["id"]: st for st in r["T"]["steps"]}
        n_req = sum(1 for sid, i, _ in r["path"] if i is not None and steps[sid].get("weight", "required") == "required")
        return (-r["c_hat"] / pm["tau"] + pm["len_prior"] * n_req, r["template"])
    return max(live, key=s)


def detect_departure(scene, **params):
    """Departure / broken play on the best template of each window (counters suppress departures)."""
    lat = build_lattice(scene)
    out = []
    for w in _halfcourt_windows(scene):
        wl = _window_lattice(lat, w)
        scored, _ = score_templates(scene, wl, _align_in(scene, w))
        best = _best_live(scored)
        if best is None:
            continue
        dep = departure(best, wl)
        if dep is None:
            continue
        t = dep["t_f"]
        if t is None:
            prev = [wl[i].end for _, i, _ in best["path"][:dep["index"]] if i is not None]
            t = max(prev) if prev else w.start
        conf = (1.0 - best["P"]) * _factor(scene, list(best["binding"].values()), w.start, w.end, t) if best["binding"] else 0.0
        out.append(Event("departure", dict(best["binding"]), t, w.start, w.end, conf,
                         {"template": best["template"], **dep, "c_hat": best["c_hat"],
                          "name": best["T"]["name"] + " (start)" if dep["start_matched_continuation_unknown"] else best["T"]["name"]}))
    return out


# --------------------------------------------------------------------------------------
# Naming, precedence, segmentation, storage (CE-R13..CE-R15, CE-R21)
# --------------------------------------------------------------------------------------
CHUNK_NAMES = {"iverson": "Iverson", "zipper": "Zipper", "chicago": "Chicago", "spain": "Spain PnR", "elevator": "Elevator",
               "floppy": "Floppy", "hammer": "Hammer", "pistol": "Pistol", "drag": "Drag", "stagger": "Stagger",
               "get": "Get", "dho_chain": "DHO chain", "ucla": "UCLA", "flex": "Flex", "ram": "Ram"}


def _single_token(scene, e):
    """Fallback single-action token of the chunk lexicon, or None for spacer / unnamed actions."""
    if e.kind == "SCR.on":
        x, y = pos(scene, e.actors["screener"], e.t0)
        return f"{pnr_location_label(x, y)[0]} PnR"
    return {"DHO": "DHO", "SCR.down": "down screen", "SCR.back": "back screen", "SCR.flare": "flare",
            "SCR.cross": "cross screen"}.get(e.kind) or (
        f"drive {e.attrs['direction']}" if e.kind == "DRIVE" else
        ("skip" if e.kind == "PASS" and e.attrs.get("skip") else ("basket cut" if e.kind == "CUT" and e.attrs.get("cls") == "basket" else None)))


def compositional_name(scene, lat, set_res=None, align_ev=None, prefix="", **params):
    """MDL chunk cover + deterministic rendering (CE-R14). Returns (display name, canonical tokens, cost)."""
    p = _prm("compositional_name", params)
    explained = set()
    items = []  # (t_ref, display token, canonical code, is_ball)
    if set_res is not None:
        T = set_res["T"]
        evs = [lat[i] for i in set_res["used"]]
        explained |= set(set_res["used"])
        for j, e in enumerate(lat):
            if _covered(e, evs):
                explained.add(j)
        tok = T["name"]
        cc = [pp.get("counter") for _, i, pp in set_res["path"] if i is not None and pp.get("counter")]
        if cc:
            tok += f" ({cc[0]} counter)"
        dep = departure(set_res, lat)
        if dep and not set_res.get("accepted"):
            tok = T["name"] + " (start)" if dep["start_matched_continuation_unknown"] else tok
            tok += f" [broke at {dep['step']}: {dep['cause']}]"
        items.append((set_res["t0"], tok, T["namespace"] + T["id"], True))
    comps = [(j, e) for j, e in enumerate(lat) if e.kind in CHUNK_NAMES and j not in explained]
    cost = 0.0
    # greedy MDL: components by gain (covered single tokens saved minus own cost), deterministic tie-break
    gains = []
    for j, e in comps:
        cov = [i for i, x in enumerate(lat) if i != j and i not in explained and _covered(x, [e])]
        saved = sum(min(-math.log(max(lat[i].conf, 1e-9)) + p["chunk_penalty"], p["w_uncovered"]) for i in cov if _single_token(scene, lat[i]))
        own = -math.log(max(e.conf, 1e-9)) + p["chunk_penalty"]
        gains.append((saved + p["w_uncovered"] - own, -e.t0, j, cov))
    for g, _, j, cov in sorted(gains, reverse=True):
        if j in explained or g <= 0:
            continue
        e = lat[j]
        explained |= {j, *cov}
        cost += -math.log(max(e.conf, 1e-9)) + p["chunk_penalty"]
        items.append((e.t0, CHUNK_NAMES[e.kind], e.kind, True))
    for j, e in enumerate(lat):
        if j in explained:
            continue
        tok = _single_token(scene, e)
        if tok is None:
            continue
        own = -math.log(max(e.conf, 1e-9)) + p["chunk_penalty"]
        if own < p["w_uncovered"]:
            items.append((e.t0, tok, e.kind, e.kind in ("SCR.on", "DHO", "DRIVE", "PASS")))
            cost += own
        else:
            cost += p["w_uncovered"]
    items.sort(key=lambda z: (z[0], not z[3], z[1]))
    # join tokens closer than join_s with ' + ' (ball-side first)
    groups = []
    for it in items:
        if groups and (it[0] - groups[-1][-1][0]) * DT < p["join_s"]:
            groups[-1].append(it)
        else:
            groups.append([it])
    toks = [" + ".join(z[1] for z in sorted(g, key=lambda z: (not z[3], z[1]))) for g in groups]
    codes = [z[2] for g in groups for z in g]
    head = "Free" if set_res is None and not prefix else None  # no alignment head in a transition / early window
    if align_ev is not None and align_ev.attrs["accepted"]:
        head = align_ev.attrs["display"]
        if set_res is not None and align_ev.attrs["code"] in (set_res["T"].get("alignments") or []):
            head = None  # the set name already carries its alignment
    mx = int(p["max_tokens"])
    body = toks[:mx]
    if len(toks) > mx:
        body.append(f"(+{len(toks) - mx})")
    parts = ([head] if head else []) + body
    name = prefix + " -> ".join(parts) if parts else prefix + "Free"
    return name, codes, cost


def name_precedence(set_res, coverage, departed_prefix=False, **params):
    """Primary-name kind (CE-R15): set / probable_set / prefix / compositional."""
    p = _prm("name_precedence", params)
    p = {**PRM["probability"], **p}  # p_display / p_probable live in probability only (loop 1 F12)
    if set_res is not None and set_res["accepted"] and set_res["P"] >= p["p_display"] and coverage >= p["min_coverage"]:
        return "set"
    if set_res is not None and set_res["accepted"] and set_res["P"] >= p["p_probable"]:
        return "probable_set"
    if departed_prefix:
        return "prefix"
    return "compositional"


def _coverage(set_res, lat):
    """Share of window events involving bound roles that the path explains (matched or covered)."""
    if set_res is None:
        return 0.0
    vals = set(set_res["binding"].values())
    evs = [lat[i] for i in set_res["used"]]
    rel = [j for j, e in enumerate(lat) if e.kind != "align" and set(e.actors.values()) & vals]
    if not rel:
        return 1.0
    ok = [j for j in rel if j in set_res["used"] or _covered(lat[j], evs)]
    return len(ok) / len(rel)


def storage_row(scene, w, lat, scored, p_null, align_ev, name, tokens, kind, set_res=None):
    """set_instances row (CE-R21): name AND the full ordered action sequence, path, binding, top-k, versions."""
    seq = []
    for j, e in enumerate(lat):
        acts = ",".join(f"{k}={v}" for k, v in sorted(e.actors.items()))
        seq.append(f"{e.kind}[{acts}]@{(e.t0 - w.start) * DT:.1f}")
    ali = f"ALIGN({align_ev.attrs['code']})|" if align_ev is not None else ""
    row = {
        "compositional_name": name, "name_tokens": tokens, "primary_name_kind": kind,
        "action_sequence": list(range(len(lat))), "sequence_string": ali + "|".join(seq),
        "set_code": (set_res["T"]["namespace"] + set_res["template"]) if set_res else None,
        "family_code": set_res["T"].get("family_code") if set_res else None,
        "alignment_code": align_ev.attrs["code"] if align_ev is not None else None,
        "match_confidence": set_res["P"] if set_res else None,
        "alignment_path": [{"step_id": sid, "action_id": i, **{k: v for k, v in pp.items()}} for sid, i, pp in set_res["path"]] if set_res else [],
        "insertions": set_res["ins"] if set_res else [], "role_binding": dict(set_res["binding"]) if set_res else {},
        "mirrored": set_res["mirrored"] if set_res else None, "side_ambiguous": set_res["side_ambiguous"] if set_res else None,
        "strong_side_sign": _ball_side(scene, set_res["t0"]) if set_res and set_res["t0"] is not None else _ball_side(scene, w.start),
        "top_k": [{"set_code": r["T"]["namespace"] + r["template"], "p": r["P"], "C_hat": r["c_hat"], "mirrored": r["mirrored"]}
                  for r in scored[:5]],
        "null_prob": p_null, "departure_step": None, "counter_code": None,
        "start_matched_continuation_unknown": False, "segment_seq": w.attrs.get("window_index", 0),
        "revision_number": 0, "revision_reason": "window_close", "label_status": "final",
        "lattice_version": DOC["version"], "matcher_version": DOC["version"], "library_version": DOC["version"],
        "t_open_f": w.start, "t_close_f": w.end,
    }
    if set_res:
        dep = departure(set_res, lat)
        if dep:
            row["departure_step"] = dep["step"]
            row["start_matched_continuation_unknown"] = dep["start_matched_continuation_unknown"]
        cc = [pp.get("counter") for _, i, pp in set_res["path"] if i is not None and pp.get("counter")]
        row["counter_code"] = cc[0] if cc else None
    return row


def detect_compositional_name(scene, **params):
    """One 'name' event per set window: display name, canonical tokens, primary-name kind and storage row."""
    lat = build_lattice(scene)
    out = []
    for w in _halfcourt_windows(scene):
        wl = _window_lattice(lat, w)
        al = _align_in(scene, w)
        scored, p_null = score_templates(scene, wl, al)
        top = scored[0] if scored and scored[0]["accepted"] else None
        dep_res = None
        if top is None:
            cand = _best_live(scored)
            if cand is not None:
                d = departure(cand, wl)
                if d and d["start_matched_continuation_unknown"]:
                    dep_res = cand
        use = top or dep_res
        cov = _coverage(top, wl) if top else 0.0
        kind = name_precedence(top, cov, departed_prefix=dep_res is not None)
        prefix = ""
        name, toks, cost = compositional_name(scene, [e for e in wl if e.kind != "align"], use, al, prefix=prefix)
        if top is None:
            # special classes (CE-R16 / CE-R17) name the window when no set is accepted
            spec = [(e, e.attrs["label"]) for e in detect_motion(scene) if w.start <= e.t0 <= w.end]
            spec += [(e, f"{e.attrs['code'].capitalize()} x{e.attrs['cycle_count']}") for e in detect_continuity(scene)
                     if w.start <= e.t0 <= w.end]
            spec += [(e, "Clear-out ISO" if e.attrs["clear_out"] else "ISO") for e in detect_iso(scene) if w.start <= e.t0 <= w.end]
            if spec:
                lab = " -> ".join(z[1] for z in sorted(spec, key=lambda z: z[0].t0))
                rest = name[len(prefix):].split(" -> ", 1)  # drop the alignment / 'Free' head, keep the chunks
                name = prefix + lab + (" -> " + rest[1] if len(rest) > 1 else "")
                toks = [z[0].kind for z in spec] + toks
                kind = "special_class"
        row = storage_row(scene, w, [e for e in wl if e.kind != "align"], scored, p_null, al, name, toks, kind, use)
        conf = (top["P"] if top else 1.0 - (scored[0]["P"] if scored else 0.0)) * w.conf
        out.append(Event("name", {}, w.start, w.start, w.end, float(conf),
                         {"name": name, "tokens": toks, "primary_name_kind": kind, "coverage": cov, "chunk_cost": cost,
                          "row": row}))
    return out


def detect_segments(scene, **params):
    """Semi-Markov segmentation of each set window (CE-R13): boundaries at resets or >= 1.0 s event gaps,
    minimising sum(segment cost + lambda_seg)."""
    p = _prm("segmentation", params)
    lat = [e for e in build_lattice(scene) if e.kind != "align"]
    out = []
    for w in detect_set_window(scene):
        ev = sorted([e for e in lat if w.start <= e.t0 <= w.end], key=lambda e: e.t0)
        if not ev:
            continue
        al = _align_in(scene, w)
        cuts = [0]
        for i in range(1, len(ev)):
            if (ev[i].t0 - max(e.end for e in ev[:i])) * DT >= p["min_gap_s"]:
                cuts.append(i)
        cuts.append(len(ev))
        m = len(cuts)
        best = [0.0] + [math.inf] * (m - 1)
        back = [0] * m
        seg_info = {}
        for j in range(1, m):
            for i in range(j):
                sub = ev[cuts[i]:cuts[j]]
                if len(sub) < p["min_events"] and (sub[-1].end - sub[0].t0) * DT < p["min_s"]:
                    continue
                # the window's ALIGN snapshot belongs to the segment that starts the window
                scored, _ = score_templates(scene, sub, al if i == 0 else None)
                acc = [r for r in scored if r["accepted"]]
                c_set = acc[0]["C"] if acc else math.inf
                _, _, c_chunk = compositional_name(scene, sub)
                c = min(c_set, c_chunk) + p["lambda_seg"]
                if best[i] + c < best[j]:
                    best[j], back[j] = best[i] + c, i
                    seg_info[(i, j)] = (acc[0] if acc and c_set <= c_chunk else None, c - p["lambda_seg"])
        j, segs = m - 1, []
        while j > 0:
            i = back[j]
            segs.append((i, j))
            j = i
        for k, (i, j) in enumerate(reversed(segs)):
            sub = ev[cuts[i]:cuts[j]]
            sr, c = seg_info.get((i, j), (None, 0.0))
            name, toks, _ = compositional_name(scene, sub, sr, al if i == 0 else None)
            if w.attrs.get("segment_kind") == "transition_early":
                name = TRANSITION_NAME  # loop 5 C6: transition segments carry the fixed name, no chunk name
            t0 = sr["t0"] if sr else sub[0].t0  # a set segment starts at its first matched step (CE-R04)
            out.append(Event("segment", dict(sr["binding"]) if sr else {}, t0, sub[0].t0, max(e.end for e in sub),
                             float(sr["P"] * w.conf) if sr else float(w.conf * 0.5),
                             {"segment_seq": k, "name": name, "set_code": (sr["T"]["namespace"] + sr["template"]) if sr else None,
                              "segment_cost": c}))
    return out


# --------------------------------------------------------------------------------------
# Live belief (CE-R20): provisional evidence, commit hysteresis, append-only revision log
# --------------------------------------------------------------------------------------
def _visible_at(e, p):
    """Frame at which an event becomes usable live: window close + per-kind confirmation delay."""
    head = e.kind.split(".")[0]
    delay = p["confirm_delay_s"].get(e.kind, p["confirm_delay_s"].get(head, 0.0))
    return max(e.end, e.t0 + frames(delay))


def live_belief(scene, w, lat, **params):
    """Emulate the online labeller over one window. Returns (stream, commits, revisions)."""
    p = _prm("live_belief", params)
    al = _align_in(scene, w)
    step = int(p["update_every_frames"])
    stream, revisions = [], []
    shown, cand, cand_n = None, None, 0
    committed, held = None, 0
    memo = {}
    last_t = min(scene.n - 1, w.end + frames(p["final_after_close_s"]))
    for t in range(w.start, last_t + 1, step):
        vis = tuple(j for j, e in enumerate(lat) if _visible_at(e, p) <= t)
        if vis not in memo:
            sub = [lat[j] for j in vis]
            memo[vis] = score_templates(scene, sub, al)[0] if sub else []
        scored = memo[vis]
        top = scored[0] if scored and scored[0]["accepted"] else None
        code, pv = (top["template"], top["P"]) if top else (None, 0.0)
        # displayed-name hysteresis: switch only when the new top-1 beats the shown P by the margin for N frames
        if shown is None and code is not None:
            shown = code
            revisions.append({"revision_number": len(revisions), "t_f": t, "label": code, "P": pv, "reason": "new_evidence"})
        elif code is not None and code != shown:
            cur_shown_p = next((r["P"] for r in scored if r["template"] == shown), 0.0)
            if pv - cur_shown_p >= p["switch_margin"]:
                cand_n = cand_n + step if cand == code else step
                cand = code
                if cand_n >= p["switch_hold_frames"]:
                    revisions.append({"revision_number": len(revisions), "t_f": t, "label": code, "P": pv,
                                      "reason": "new_evidence", "previous": shown})
                    shown, cand, cand_n, held = code, None, 0, 0
            else:
                cand, cand_n = None, 0
        if shown is not None:
            r_shown = next((r for r in scored if r["template"] == shown and r["accepted"]), None)
            sp = r_shown["P"] if r_shown else 0.0
            held = held + step if sp >= p["commit_p"] else 0
            if committed is None and held >= frames(p["commit_hold_s"]):
                committed = (t, shown, sp, r_shown)
        stream.append((t, [(r["template"], r["P"]) for r in scored[:3]]))
    final = memo.get(tuple(range(len(lat)))) or score_templates(scene, lat, al)[0]
    fcode = final[0]["template"] if final and final[0]["accepted"] else None
    if fcode != shown:
        revisions.append({"revision_number": len(revisions), "t_f": last_t, "label": fcode, "P": final[0]["P"] if final else 0.0,
                          "reason": "window_close", "previous": shown})
    return stream, committed, revisions


def detect_live_belief(scene, **params):
    """'commit' events: the frame a set name is committed live (P >= 0.80 held 1.0 s), with the revision log."""
    lat = [e for e in build_lattice(scene) if e.kind != "align"]
    out = []
    for w in detect_set_window(scene):
        wl = [e for e in lat if w.start <= e.t0 <= w.end]
        if not wl:
            continue
        stream, committed, revs = live_belief(scene, w, wl, **params)
        if committed is None:
            continue
        t, code, pv, r = committed
        first = r["t0"] if r["t0"] is not None else w.start
        out.append(Event("commit", dict(r["binding"]), t, w.start, w.end, float(pv * w.conf),
                         {"set_code": r["T"]["namespace"] + code, "P": pv, "latency_s": (t - first) * DT,
                          "revisions": revs, "n_updates": len(stream)}))
    return out


# --------------------------------------------------------------------------------------
# Items that cannot be detected from XY (+ ball XY) alone: marked needs_data in the YAML
# --------------------------------------------------------------------------------------
def _needs_data(scene, **params):
    """Needs data the XY scene does not carry (PBP, shot clock, corpus, labels, matchup HMM): returns []."""
    return []


detect_scramble = detect_unmatched_clustering = detect_learned_classifier = _needs_data
detect_team_priors = detect_synergy_outcome = detect_defensive_context = _needs_data
detect_situation_routing = detect_defensive_namespace = detect_noise_acceptance = _needs_data

COMPONENTS = ["iverson", "zipper", "chicago", "spain", "elevator", "floppy", "hammer", "pistol", "drag", "stagger",
              "get_dho_chain", "ucla", "flex", "ram"]

DETECTORS = {
    "set_window": detect_set_window, "reset": detect_reset, "align_snapshot": detect_align_snapshot,
    "set_match": detect_set_match, "departure": detect_departure, "segmentation": detect_segments,
    "compositional_name": detect_compositional_name, "continuity": detect_continuity, "motion": detect_motion,
    "iso": detect_iso, "live_belief": detect_live_belief, "style_measures": detect_style_measures,
    "iverson": detect_iverson, "zipper": detect_zipper, "chicago": detect_chicago, "spain": detect_spain,
    "elevator": detect_elevator, "floppy": detect_floppy, "hammer": detect_hammer, "pistol": detect_pistol,
    "drag": detect_drag, "pnr_location": detect_pnr_location, "stagger": detect_stagger,
    "get_dho_chain": detect_get_dho_chain, "ucla": detect_ucla, "flex": detect_flex, "ram": detect_ram,
    "scramble": detect_scramble, "unmatched_clustering": detect_unmatched_clustering,
    "learned_classifier": detect_learned_classifier, "team_priors": detect_team_priors,
    "synergy_outcome": detect_synergy_outcome, "defensive_context": detect_defensive_context,
    "situation_routing": detect_situation_routing, "defensive_namespace": detect_defensive_namespace,
    "noise_acceptance": detect_noise_acceptance,
}


# --------------------------------------------------------------------------------------
# Possession split (loop 4 L2): a clip may hold several possessions of both teams
# --------------------------------------------------------------------------------------
def _defense_control(scene):
    """Per-frame bool: a defender controls the ball (nearest defender within HOLD_R, no offensive holder, and the
    defender nearer than every attacker by the _def_gate margin)."""
    n = scene.n
    DM = _defender_margin(scene)
    out = np.zeros(n, bool)
    if DM is None:
        return out
    H = _H(scene)
    X = np.vstack([scene.kins[o].x for o in scene.offense])
    Y = np.vstack([scene.kins[o].y for o in scene.offense])
    D = np.hypot(X - scene.ball.x[None, :], Y - scene.ball.y[None, :])
    D[~np.isfinite(D)] = 9e9
    for t in np.flatnonzero(DM <= mvlib.HOLD_R):
        if H[t] is None:
            j = int(np.argmin(D[:, t]))
            out[t] = DM[t] < D[j, t] - _def_gate(scene, scene.offense[j], t)
    return out


def possession_spans(scene, **params):
    """Offense possession spans [(a, b)] of a clip: the clip is cut at every defensive control run of >=
    def_control_min_s (gaps <= def_bridge_frames bridged); spans shorter than min_span_s or with less than min_control_s of
    offensive holder frames (a defender's possession with a momentary offensive touch) are dropped. A clip without such a run (every synthetic single-possession scene) is one span
    (0, n - 1), so the engine's one-clip-one-possession contract is unchanged there."""
    p = _prm("possession_split", params)
    n = scene.n
    dc = _defense_control(scene)
    breaks = hysteresis(dc, dc, p["def_control_min_s"], int(p["def_bridge_frames"]))
    if not breaks:
        return [(0, n - 1)]
    H = _H(scene)
    spans, lo = [], 0
    for a, b in breaks + [(n, n)]:
        hi = a - 1
        held = sum(1 for t in range(lo, hi + 1) if H[t] is not None)
        if (hi - lo) * DT >= p["min_span_s"] and held * DT >= p["min_control_s"]:
            spans.append((lo, hi))
        lo = b + 1
    return spans


def sub_scene(scene, a, b):
    """Frames [a, b] of a scene as a new Scene (smoothed kinematics sliced, not re-smoothed: edge factors keep the
    track edges, a span boundary is not a track edge)."""
    import dataclasses

    def cut(k):
        kw = {}
        for fl in dataclasses.fields(k):
            v = getattr(k, fl.name)
            kw[fl.name] = v[a:b + 1] if isinstance(v, np.ndarray) and len(v) == scene.n else (dict(v) if isinstance(v, dict) else v)
        return type(k)(**kw)
    kins = {o: cut(k) for o, k in scene.kins.items()}
    ball = cut(scene.ball) if scene.ball is not None else None
    braw = tuple(np.asarray(v)[a:b + 1] for v in scene.ball_raw) if scene.ball_raw is not None else None
    bz = getattr(scene, "ball_z", None)
    bz = np.asarray(bz)[a:b + 1] if bz is not None else None
    return mvlib.Scene(kins, list(scene.offense), list(scene.defense), ball, scene.holder[a:b + 1], b - a + 1, braw, bz)


FRAME_KEYS = {"trigger_f", "transition_early_f", "t_f", "t_open_f", "t_close_f", "sts_t"}


def _shift(v, a, key=None):
    if isinstance(v, dict):
        return {k: _shift(x, a, k) for k, x in v.items()}
    if isinstance(v, list):
        return [_shift(x, a, key) for x in v]
    if key in FRAME_KEYS and isinstance(v, (int, np.integer)) and not isinstance(v, bool):
        return int(v) + a
    return v


def shift_event(e, a):
    """Move an event found on sub_scene(scene, a, b) back to the clip's frame numbers."""
    e.t0, e.start, e.end = e.t0 + a, e.start + a, e.end + a
    e.attrs = _shift(e.attrs, a)
    return e


def _cuts_in(cuts, a, b):
    """Copies of the cuts-family events with t0 in [a, b], moved to frame numbers of sub_scene(scene, a, b)."""
    return [Event(e.kind, dict(e.actors), e.t0 - a, max(0, e.start - a), min(b - a, e.end - a), e.conf, dict(e.attrs))
            for e in cuts if a <= e.t0 <= b]


def _matchup_in(matchup, a, b):
    """Loop 6 C2: the defense family's per-frame matchup {defender: attacker id per frame} restricted to frames [a, b]."""
    return {d: list(v[a:b + 1]) for d, v in matchup.items()}


def detect_all(scene, cuts=None, matchup=None):
    """Run every detector on a scene -> {item id: [Event, ...]}.

    Loop 4 L2: a clip holding several possessions (real tracking: a clock-running stretch) is cut into offense
    possession spans (possession_spans) and every detector runs on each span as its own clip; events come back in
    the clip's frame numbers. A single-span clip runs unchanged.
    Loop 5 C5: cuts = the cuts family's events on this scene (cuts.detect_all), optional; when given, motion (and so
    the names that carry it) counts the real cut events instead of the proxy CUT.
    Loop 6 C2: matchup = the defense family's per-frame matchup on this scene ({defender: attacker id per frame}, e.g.
    defense.joint_top1(scene)), optional; when given, the handler's defender of a widened ball screen / drag contact is
    the defender matched to the handler, otherwise the sustained-distance matchup (_handler_defender)."""
    spans = possession_spans(scene)
    if spans == [(0, scene.n - 1)]:
        if cuts is not None:
            _cache(scene)["cuts_family"] = list(cuts)
        if matchup is not None:
            _cache(scene)["matchup_family"] = _matchup_in(matchup, 0, scene.n - 1)
        return {k: f(scene) for k, f in DETECTORS.items()}
    out = {k: [] for k in DETECTORS}
    for a, b in spans:
        sub = sub_scene(scene, a, b)
        if cuts is not None:
            _cache(sub)["cuts_family"] = _cuts_in(cuts, a, b)
        if matchup is not None:
            _cache(sub)["matchup_family"] = _matchup_in(matchup, a, b)
        for k, f in DETECTORS.items():
            out[k] += [shift_event(e, a) for e in f(sub)]
    return out
