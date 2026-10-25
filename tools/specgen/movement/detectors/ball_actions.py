"""Ball-action detectors (movement grammar family BALL ACTIONS; spec tooling, not the production labeller).

Implements config/movement_grammar/ball_actions.yaml. Every numeric threshold is read from that file at
import (single source of truth); keyword arguments to a detector override its own item's params only.

Layering (BA design note 1):
  L0  ball-control decode: per-player control segments (enter 1.0 m / exit 1.5 m hysteresis, nearest by
      a margin, relative-speed gate) and the free-ball intervals between them (flight, loose, exchange).
  L1  touch, catch, release, flight, loose ball, contested ball, team possession, dribble presence.
  L2  drives (+ direction, depth, paint touch, defender reaction), passes (+ lob / skip / swing / entry /
      kick-out / dump-off / outlet), post seal and post-up, isolation, shot release and shot families.
  L3  pass chains (potential / hockey assist), drive outcome, reversals, rebounds, live-ball turnovers under the
      NCAA official-statistics rules (control gates, steal credit, abstentions, PBP reconciliation; changes_loop5).

Without ball z (and without pose) dribble bounces, dribble-move types, bounce / chest / overhead passes,
fakes and footwork cannot be observed: those detectors return [] and the YAML marks them needs_data.

Confidence (rule ba_confidence, MP-16): conf = P_cond x edge_factor x gap_factor, where P_cond is the MIN
over the item's criteria of the window probability of each criterion (min, not product: criteria share the
same noisy positions, and a product of k criteria at a 1-sigma margin collapses to 0.84^k). Candidates are
emitted on the point-estimate rule; conf is attached, never used as a pre-calibration gate.

Frame: attacked-rim frame, metres; 29.97 fps (mvlib.DT). Positions are the CA-RTS smoothed stance centres.
"""
from __future__ import annotations

import math
import sys
from dataclasses import dataclass, field
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import yaml

_HERE = Path(__file__).resolve()
for _p in (_HERE.parents[1], _HERE.parents[2] / "named_spots"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mvlib as mv  # noqa: E402
import spotlib  # noqa: E402
from mvlib import DT, K_CAL, Event, edge_factor, gap_factor, p_above, p_below, phi, window_conf  # noqa: E402

YAML_PATH = _HERE.parents[4] / "config" / "movement_grammar" / "ball_actions.yaml"


# --------------------------------------------------------------------------------------
# Parameters (single source of truth: the YAML file)
# --------------------------------------------------------------------------------------
def _load_yaml(path=YAML_PATH):
    doc = yaml.safe_load(Path(path).read_text())
    params = {}
    for it in doc["items"]:
        params[it["id"]] = {k: v["value"] for k, v in (it.get("params") or {}).items()}
    return doc, params


DOC, PARAMS = _load_yaml()
STATUS = {it["id"]: it.get("status") for it in DOC["items"]}


def _params(item: str, overrides: dict) -> SimpleNamespace:
    """Item params from the YAML with keyword overrides; unknown names are an error."""
    base = dict(PARAMS[item])
    bad = set(overrides) - set(base)
    if bad:
        raise TypeError(f"{item}: unknown params {sorted(bad)}")
    base.update(overrides)
    return SimpleNamespace(**base)


def _frames(seconds: float) -> int:
    return mv.frames(seconds)


# --------------------------------------------------------------------------------------
# Named spots (labels and continuous coordinates come from config/named_spots.yaml only)
# --------------------------------------------------------------------------------------
SPOT_DOC, SPOTS = spotlib.load()
_RCC = next(e for e in SPOT_DOC["entries"] if e["id"] == "rule_continuous_coordinates")
_COORD = {}
for _name, _src in _RCC["value_exprs"].items():
    if _name == "ball_angle_delta":
        continue  # needs ball context; not used here
    spotlib.check_expr(_src)
    _COORD[_name] = compile(_src, _name, "eval")


def coord(name: str, x: float, y: float) -> float:
    """Continuous coordinate (d3, sd_paint_out, ...) from rule_continuous_coordinates."""
    if not (np.isfinite(x) and np.isfinite(y)):
        return float("nan")
    return float(eval(_COORD[name], {"__builtins__": {}}, spotlib.env(float(x), float(y))))


def in_spot(sid: str, x: float, y: float, **ctx) -> bool:
    """True if the point carries any (side-qualified) label of named spot `sid`."""
    if not (np.isfinite(x) and np.isfinite(y)):
        return False
    return bool(SPOTS[sid].labels(float(x), float(y), **ctx))


def spot_labels(x: float, y: float, layer: str = "spot") -> list:
    """All labels of one named-spot layer at a point (e.g. layer 'spot' -> ['low_post_right'])."""
    if not (np.isfinite(x) and np.isfinite(y)):
        return []
    out = []
    for s in SPOTS.values():
        if s.d.get("layer") == layer and s.code is not None and not s.ctx:
            out += s.labels(float(x), float(y))
    return out


def region(x: float, y: float) -> list:
    return spotlib.court_region(SPOTS, float(x), float(y)) if np.isfinite(x) and np.isfinite(y) else ["unknown"]


def _sample_probs(classify, pts, sigmas, n, seed=20261020):
    """Class probabilities by Monte-Carlo over independent isotropic position errors.

    classify(*xy) -> label; pts = [(x, y), ...]; sigmas = [s, ...] per point. Fixed seed, so results are
    reproducible (rule_probabilistic_membership case c, small sample).
    """
    rng = np.random.default_rng(seed)
    counts = {}
    for _ in range(int(n)):
        xy = []
        for (x, y), s in zip(pts, sigmas):
            xy += [x + rng.normal(0, s), y + rng.normal(0, s)]
        lab = classify(*xy)
        counts[lab] = counts.get(lab, 0) + 1
    return {k: v / n for k, v in sorted(counts.items(), key=lambda kv: -kv[1])}


def _pick(probs: dict, unresolved_margin: float):
    """(label, p, status, alternatives) from a class distribution (BA-R1 rule 3)."""
    items = list(probs.items())
    lab, p = items[0]
    p2 = items[1][1] if len(items) > 1 else 0.0
    status = "unresolved" if p - p2 < unresolved_margin else "ok"
    return lab, p, status, {k: round(v, 3) for k, v in items}


# --------------------------------------------------------------------------------------
# Small geometry / uncertainty helpers
# --------------------------------------------------------------------------------------
def _xy(k, t):
    return float(k.x[t]), float(k.y[t])


def _r(k, t):
    return float(math.hypot(k.x[t], k.y[t]))


def _sig(k, t):
    """Calibrated position sigma (m) of one object at frame t (MP-09)."""
    v = k.var_p[t]
    return float(K_CAL * math.sqrt(v)) if np.isfinite(v) else 0.3


def _sig2(ka, ta, kb, tb):
    return math.hypot(_sig(ka, ta), _sig(kb, tb))


def _d(ka, kb, t):
    return float(math.hypot(ka.x[t] - kb.x[t], ka.y[t] - kb.y[t]))


def _theta(x, y):
    return math.degrees(math.atan2(y, x))


def _m(x, y):
    return math.degrees(math.atan2(y, abs(x)))


def _ang(u, v):
    """Unsigned angle between two 2-D vectors in degrees (nan if either is ~0)."""
    nu, nv = math.hypot(*u), math.hypot(*v)
    if nu < 1e-9 or nv < 1e-9:
        return float("nan")
    c = max(-1.0, min(1.0, (u[0] * v[0] + u[1] * v[1]) / (nu * nv)))
    return math.degrees(math.acos(c))


def _nearest(scene, ids, t, x, y, exclude=()):
    """(id, distance) of the nearest object in `ids` to point (x, y) at frame t."""
    best, bd = None, float("inf")
    for o in ids:
        if o in exclude:
            continue
        k = scene.kins[o]
        if not np.isfinite(k.x[t]):
            continue
        d = math.hypot(k.x[t] - x, k.y[t] - y)
        if d < bd:
            best, bd = o, d
    return best, bd


def _conf(pcond, k, t0, a, b):
    """MP-16: P_cond x c_edge x c_gap, clipped to [0, 1]."""
    a, b = max(0, int(a)), max(int(a), int(b))
    return float(np.clip(pcond * edge_factor(k, int(t0)) * gap_factor(k, a, b), 0.0, 1.0))


def _crit(value, thr, p):
    return {"value": round(float(value), 3), "thr": thr, "p": round(float(p), 3)}


def _cache(scene, key, fn):
    store = scene.__dict__.setdefault("_ba_cache", {})
    if key not in store:
        store[key] = fn()
    return store[key]


def _key(name, ov):
    return (name, tuple(sorted(ov.items())))


# --------------------------------------------------------------------------------------
# Team rims (changes_loop4 BA-R4a / BA-R4b): a clip can hold possessions toward both baskets
# --------------------------------------------------------------------------------------
FAR_RIM_Y = spotlib.C["FAR_END_Y"] - spotlib.C["RIM_Y_FROM_END"]  # the other basket in the attacked-rim frame


def _team_rims(scene):
    """{True: rim of the offence list, False: rim of the defence list} as (x, y).

    The scene frame puts one basket at the origin; a live-ball clip (SportVU clock-running stretch, a broadcast
    clip across a rebound) also holds the other team's possessions toward the far basket. Each team attacks one
    basket for the whole clip.

    changes_loop4 BA-R4b (goal-side vote): on every frame where all players stand in one half, the defending team
    is the one whose players stand goal-side (nearer that half's basket) of the nearest opponent for most of the
    other team's players (defenders play between their man and the basket). The net vote over the clip (frames
    of 'offence list attacks the origin' minus frames of 'offence list attacks the far basket') decides when it
    reaches touch.rim_goalside_min_s and both teams have at least touch.rim_goalside_min_players tracked;
    otherwise the default holds (offence list -> origin rim). The loop-4 first draft (BA-R4a: the team whose ball-control frames lie in the origin half more often attacks it) put 43 of
    194 real chunks at the wrong basket and was replaced."""
    P = PARAMS["touch"]
    out = {True: (0.0, 0.0), False: (0.0, FAR_RIM_Y)}
    swap = {True: (0.0, FAR_RIM_Y), False: (0.0, 0.0)}
    ball = scene.ball
    if ball is None or not scene.offense or not scene.defense:
        return out
    if min(len(scene.offense), len(scene.defense)) < P["rim_goalside_min_players"]:
        return out  # a team shape needs (nearly) the whole team
    O = [(scene.kins[o].x, scene.kins[o].y) for o in scene.offense]
    D = [(scene.kins[o].x, scene.kins[o].y) for o in scene.defense]
    with np.errstate(invalid="ignore"):
        allY = np.stack([y for _, y in O + D])
        low = np.all(allY < FAR_RIM_Y / 2, 0)
        high = np.all(allY > FAR_RIM_Y / 2, 0)

        ox, oy = np.stack([x for x, _ in O]), np.stack([y for _, y in O])
        dx, dy = np.stack([x for x, _ in D]), np.stack([y for _, y in D])
        dd = np.hypot(ox[:, None] - dx[None], oy[:, None] - dy[None])  # (n_off, n_def, n)
        near = np.argmin(np.where(np.isnan(dd), np.inf, dd), 1)  # each attacker's nearest defender
        mx = np.take_along_axis(dx[None].repeat(len(O), 0), near[:, None], 1)[:, 0]
        my = np.take_along_axis(dy[None].repeat(len(O), 0), near[:, None], 1)[:, 0]

        def gs(ry):  # +1 on a frame where most attackers have their nearest defender nearer the basket at ry
            return np.sign(np.nansum(np.sign(np.hypot(ox, oy - ry) - np.hypot(mx, my - ry)), 0))

        v_low = gs(0.0)[low]
        v_high = gs(FAR_RIM_Y)[high]
    vote = float(np.nansum(v_low) - np.nansum(v_high))
    if abs(vote) >= _frames(P["rim_goalside_min_s"]):
        return out if vote > 0 else swap
    return out


def _rim(scene, off):
    return _cache(scene, ("rims", ()), lambda: _team_rims(scene))[bool(off)]


def _rim_dist(scene, off, x, y):
    """Distance(s) of point(s) (x, y) to the rim attacked by the team `off` (vectorised)."""
    rx, ry = _rim(scene, off)
    return np.hypot(np.asarray(x) - rx, np.asarray(y) - ry)


def _att(scene, off, x, y):
    """A point in the attack frame of team `off` (rim at the origin, +y toward half court): the far basket's
    team sees the court rotated by 180 degrees."""
    rx, ry = _rim(scene, off)
    if ry == 0.0:
        return float(x), float(y)
    return float(rx - x), float(ry - y)


# --------------------------------------------------------------------------------------
# L0: ball-control decode (item touch; BA-00 + BA-04)
# --------------------------------------------------------------------------------------
@dataclass
class Ctl:
    """One control segment of one player."""
    pid: str
    off: bool  # controller is on the offence list
    a: int  # first control frame (start of the enter run)
    b: int  # last control frame (d_bp <= exit radius)
    conf: float = 1.0
    t_catch: int | None = None  # refined catch frame when the segment follows a flight


@dataclass
class Free:
    """The ball between two control segments (or after the last one)."""
    a: int
    b: int
    prev: Ctl | None
    nxt: Ctl | None
    kind: str  # flight | loose | exchange | unknown
    travel: float = 0.0  # ball travel between the refined release and catch frames (m)
    air: float = 0.0  # refined release to refined catch (s)
    speed0: float = 0.0  # mean smoothed ball speed over the first 3 free frames
    away: bool = False  # ball distance to the releaser grows over the first 3 free frames
    loose_s: float = 0.0  # longest slow (< flight speed) run inside the interval
    t_release: int | None = None
    t_catch: int | None = None
    shot: bool = False
    rim_frame: int | None = None
    shot_crit: dict = field(default_factory=dict)
    airball: bool = False  # BA-T9: shot that fell short of rim reach


@dataclass
class BallModel:
    segs: list
    frees: list
    taps: list
    D: np.ndarray  # (players, n) ball-player distances
    ids: list
    contacts: list = field(default_factory=list)  # dropped short opponent segments (pid, a, b)


def _decode(scene, P):
    """Per-frame control decode with hysteresis (hard-threshold form of the BA-00 HMM)."""
    ball = scene.ball
    n = scene.n
    ids = scene.offense + scene.defense
    if ball is None or not ids:
        return [], ids, np.zeros((0, n)), [], np.zeros(0, bool)
    kins = [scene.kins[o] for o in ids]
    D = np.stack([np.hypot(ball.x - k.x, ball.y - k.y) for k in kins])
    Dn = np.where(np.isnan(D), np.inf, D)
    order = np.argsort(Dn, axis=0)
    rng_n = np.arange(n)
    d1 = Dn[order[0], rng_n]
    d2 = Dn[order[1], rng_n] if len(ids) > 1 else np.full(n, np.inf)
    rel = np.stack([np.hypot(ball.vx - k.vx, ball.vy - k.vy) for k in kins])
    team = np.array([o in scene.offense for o in ids])
    win = max(1, _frames(P.rel_speed_window_s))
    hold = _frames(P.occlusion_hold_s)

    def gate(i, s):
        # minimum relative speed over the forward window, on the frames where player i is the nearest
        # player and the ball is near him: a pass flying past him is his only while fast (once it sits
        # with the receiver it is the receiver's); a catch (even a 0.2 s one-touch, which the CA-RTS
        # smoother smears) brings the ball to the player's velocity at some frame
        sl = slice(s, min(n, s + win + 1))
        mine = (D[i, sl] <= P.enter_radius_m) & (order[0, sl] == i)
        seg = rel[i, sl][mine]
        seg = seg[np.isfinite(seg)]
        return len(seg) == 0 or float(np.min(seg)) <= P.rel_speed_max_mps

    raw = []  # (player index, first frame, last frame)
    last_team = None  # team of the last controller: pass-completion prior for the next entry
    cur = a = last_in = None  # current controller and its segment
    out_run = 0  # consecutive frames beyond the exit radius
    cand, cand_n, cand_s = None, 0, 0  # entry candidate while nobody controls the ball
    tk, tk_n, tk_s = None, 0, 0  # takeover candidate while someone controls the ball
    for t in range(n):
        if not np.isfinite(ball.x[t]):
            if cur is not None and t - last_in > hold:
                raw.append((cur, a, last_in))
                last_team, cur = team[cur], None
            cand = None
            continue
        if cur is not None:
            if D[cur, t] <= P.exit_radius_m:
                last_in, out_run = t, 0
            else:
                out_run += 1
                if out_run >= P.exit_frames:
                    raw.append((cur, a, last_in))
                    last_team, cur = team[cur], None
            if cur is not None:  # takeover by another player (handoff, strip)
                q = int(order[0, t])
                if q != cur and d1[t] <= P.enter_radius_m and D[cur, t] - d1[t] >= P.nearest_margin_m:
                    if tk == q:
                        tk_n += 1
                    else:
                        tk, tk_n, tk_s = q, 1, t
                    if tk_n >= P.takeover_frames:
                        if gate(q, tk_s):
                            raw.append((cur, a, max(a, tk_s - 1)))
                            cur, a, last_in, out_run = q, tk_s, t, 0
                        tk = None  # failed gate: a new run may start on the next frame
                else:
                    tk = None
        if cur is None:
            q = int(order[0, t])
            clear = d2[t] - d1[t] >= P.nearest_margin_m
            if not clear and last_team is not None and team[q] == last_team:
                # rivals within the margin are all opponents of the team that released the ball:
                # the pass-completion prior wins (a defender in contact with the receiver)
                riv = order[1:, t][Dn[order[1:, t], t] - d1[t] < P.nearest_margin_m]
                clear = bool(np.all(team[riv] != last_team))
            if d1[t] <= P.enter_radius_m and clear:
                if cand == q:
                    cand_n += 1
                else:
                    cand, cand_n, cand_s = q, 1, t
                if cand_n >= P.enter_frames:
                    if gate(q, cand_s):
                        cur, a, last_in, out_run = q, cand_s, t, 0
                    cand = None  # failed gate: a new run may start on the next frame
            else:
                cand = None
    if cur is not None:
        raw.append((cur, a, last_in))
    raw = _split_rim_finishes(scene, ball, raw, D, kins, team, P)
    return raw, ids, D, kins, team


def _split_rim_finishes(scene, ball, raw, D, kins, team, P):
    """changes_loop1 BA-T1: a finish released inside the exit radius (layup, dunk, putback, post hook) never
    leaves control. Split the segment at the first frame t where the ball is at r <= rim_finish_reach_m, the
    holder's stance is >= rim_finish_holder_gap_m farther from the rim than the ball, and the ball's r fell by
    >= rim_finish_approach_m over the previous rim_finish_approach_s. The segment ends at the last frame
    before t with d_bp <= refine_radius_m (else t - 3); it resumes rim_finish_resume_s after t when it lasts
    that long (the finisher's own rebound, or the ball dropping through the net next to him)."""
    out = []
    rbs = {f: _rim_dist(scene, f, ball.x, ball.y) for f in (True, False)}
    win = _frames(P.rim_finish_approach_s)
    for i, a, b in raw:
        k = kins[i]
        rb = rbs[bool(team[i])]  # changes_loop4 BA-R4a: the finisher's own basket
        rp = _rim_dist(scene, team[i], k.x, k.y)
        cut = None
        for t in range(a + win, b + 1):
            if not (np.isfinite(rb[t]) and rb[t] <= P.rim_finish_reach_m):
                continue
            if not (rp[t] - rb[t] >= P.rim_finish_holder_gap_m):
                continue
            if np.nanmax(rb[t - win:t + 1]) - rb[t] < P.rim_finish_approach_m:
                continue
            cut = t
            break
        if cut is None:
            out.append((i, a, b))
            continue
        near = [t for t in range(max(a, cut - win), cut) if D[i, t] <= P.refine_radius_m]
        rel = near[-1] if near else max(a, cut - 3)
        out.append((i, a, rel))
        res = cut + _frames(P.rim_finish_resume_s)
        if res <= b:
            out.append((i, res, b))
    return out


def _shot_like(scene, t_rel, t_end, S, off=True):
    """Geometry-only shot test on the ball after frame t_rel (used before the free intervals exist):
    heading within dir_tol_deg of the rim bearing and reaching r <= rim_reach_m by t_end. `off`: the
    releasing team (its basket, changes_loop4 BA-R4a)."""
    ball = scene.ball
    hi = min(t_end, t_rel + _frames(S.max_flight_s), scene.n - 1)
    if hi <= t_rel + 1:
        return False
    rx, ry = _rim(scene, off)
    rr = np.hypot(ball.x[t_rel:hi + 1] - rx, ball.y[t_rel:hi + 1] - ry)
    if not np.any(np.isfinite(rr)):
        return False
    j = int(np.nanargmin(rr))
    if rr[j] > S.rim_reach_m:
        return False
    bx0, by0 = ball.x[t_rel] - rx, ball.y[t_rel] - ry
    r0 = math.hypot(bx0, by0)
    if r0 < S.layup_r_m:
        return True
    tdir = min(t_rel + j, t_rel + max(2, _frames(S.dir_window_s)))
    dang = _ang((ball.x[tdir] - rx - bx0, ball.y[tdir] - ry - by0), (-bx0, -by0))
    return bool(np.isfinite(dang) and dang <= S.dir_tol_deg)


def _attempt_like(scene, t_rel, t_nxt, S, off=True):
    """changes_loop3 BA-T10c: the ball leaving frame t_rel goes at the attacked rim as a shot or an airball
    does: heading within dir_tol_deg (+ airball_noise_k direction standard errors) of the rim bearing and
    coming within airball_r_max_m (+ airball_noise_k ball sigma) of the rim before the next control starts at
    t_nxt (followed pass_through_window_s into it). A defender never shoots at the offence's rim, so a
    defence segment the ball leaves this way is a closeout on the shooter."""
    ball = scene.ball
    hi = min(scene.n - 1, t_nxt + _frames(S.pass_through_window_s), t_rel + _frames(S.max_flight_s))
    if hi <= t_rel + 1:
        return False
    rx, ry = _rim(scene, off)
    rr = np.hypot(ball.x[t_rel:hi + 1] - rx, ball.y[t_rel:hi + 1] - ry)
    if not np.any(np.isfinite(rr)):
        return False
    j = int(np.nanargmin(rr))
    sig_b = _sig(ball, t_rel + j)
    if rr[j] > S.airball_r_max_m + S.airball_noise_k * sig_b:
        return False
    bx0, by0 = ball.x[t_rel] - rx, ball.y[t_rel] - ry
    r0 = math.hypot(bx0, by0)
    if r0 < S.layup_r_m:
        return True
    tdir = min(t_rel + j, t_rel + max(2, _frames(S.dir_window_s)))
    dvec = (ball.x[tdir] - rx - bx0, ball.y[tdir] - ry - by0)
    dang = _ang(dvec, (-bx0, -by0))
    dlen = float(math.hypot(*dvec)) if np.all(np.isfinite(dvec)) else 0.0
    sd_ang = math.degrees(math.sqrt(2) * _sig(ball, t_rel) / max(dlen, 0.5))
    return bool(np.isfinite(dang) and dang <= S.dir_tol_deg + S.airball_noise_k * sd_ang)


def _possession_prior(scene, P, S, merged, D, ids, team, contacts):
    """changes_loop2 BA-T10b: offence possession prior. A defence segment during which one offensive player
    keeps the ball within exit_radius_m on >= possession_prior_frac of its frames is that offensive player's
    control (an on-ball defender in contact, a tie-up, a closeout at the catch), not a change of possession:
    a defender who really gains the ball (steal, interception, rebound) moves it away from every opponent.
    Not applied after a shot-like flight (a rebound). The defender's segment is recorded as contact and
    adjacent segments of the same player are re-merged (merge_gap_s / merge_max_travel_m).
    changes_loop3 BA-T10c: a strip with the victim still within the exit radius is a real steal when (a) the
    next control is the defence's, is itself not absorbed by the prior and the ball does not reach it on a
    shot-like path (the stealer gives the ball to a teammate; a closeout followed by the shooter's miss is not:
    decided from the last segment backwards), or (b) the ball moves >= possession_prior_upcourt_m
    away from the attacked rim over the segment (the stealer heads up-court with the victim chasing)."""
    ball = scene.ball
    offs = np.where(team)[0]
    if len(offs) == 0:
        return merged
    defs = np.where(~np.asarray(team, bool))[0]
    n_m = len(merged)
    # changes_loop4 BA-R4h: the prior favours the team in possession, not the offence list: a clip also holds the
    # other team's possessions toward the far basket, where the offence list defends. The defence list is taken
    # as the possessor when the ball at the segment start is within possession_prior_frontcourt_r_m of its
    # basket (its half-court offence); otherwise the offence list, as before.
    poss = [True] * n_m
    for j in range(n_m):
        qa = merged[j][1]
        if np.isfinite(ball.x[qa]):
            poss[j] = not bool(_rim_dist(scene, False, ball.x[qa], ball.y[qa]) <= P.possession_prior_frontcourt_r_m)
    absorb, cand = [False] * n_m, [None] * n_m
    for j in range(n_m - 1, -1, -1):  # backwards: guard (a) needs the next segment's final decision
        qi, qa, qb = merged[j]
        pt = poss[j]
        if bool(team[qi]) == pt:
            continue
        holders = offs if pt else defs
        if len(holders) == 0:
            continue
        with np.errstate(invalid="ignore"):
            frac = np.mean(D[holders, qa:qb + 1] <= P.exit_radius_m, axis=1)
        cand[j] = int(holders[int(np.argmax(frac))])
        pb = merged[j - 1][2] if j > 0 else None
        rebound = pb is not None and qa - pb > 1 and _shot_like(scene, pb, qa - 1, S, team[merged[j - 1][0]])
        if float(np.max(frac)) < P.possession_prior_frac or rebound:
            continue
        # changes_loop4 BA-R4i: guards (a) and (b) free the segment only when the defender leads the ball, not
        # when it sits between him and a glued ball handler: (a) over the last possession_prior_lead_s of the
        # segment the ball is on average >= possession_prior_lead_m nearer the defender than the absorbing
        # player (the pass that follows leaves the defender's hands, not the handler's); (b) the defender is
        # nearer the ball on most of the segment's frames and the absorbing player does not take the next control
        # (a back-out dribble under pressure gives the A-DA-A pattern)
        c = cand[j]
        w0 = max(qa, qb - _frames(P.possession_prior_lead_s))
        with np.errstate(invalid="ignore"):
            lead_end = float(np.nanmean(D[c, w0:qb + 1] - D[qi, w0:qb + 1])) >= P.possession_prior_lead_m
            lead_seg = float(np.nanmean(D[qi, qa:qb + 1] < D[c, qa:qb + 1])) > 0.5
        nq = merged[j + 1][0] if j + 1 < n_m else None
        if nq is not None and team[nq] == team[qi] and not absorb[j + 1] and lead_end and \
                not _attempt_like(scene, qb, merged[j + 1][1], S, pt):
            continue  # (a) the gaining team keeps the ball in its next control (not via a shot at the possessor's rim)
        rb = _rim_dist(scene, pt, ball.x[[qa, qb]], ball.y[[qa, qb]])
        up = rb[1] - rb[0]
        if np.isfinite(up) and up >= P.possession_prior_upcourt_m and lead_seg and nq != c:
            continue  # (b) the ball heads up-court
        absorb[j] = True
    out = []
    for j, (qi, qa, qb) in enumerate(merged):
        if absorb[j]:
            contacts.append((ids[qi], qa, qb))
            qi = cand[j]
        if out and out[-1][0] == qi and (qa - out[-1][2]) * DT <= P.merge_gap_s and \
                math.hypot(ball.x[qa] - ball.x[out[-1][2]], ball.y[qa] - ball.y[out[-1][2]]) < P.merge_max_travel_m:
            out[-1] = (qi, out[-1][1], qb)
        else:
            out.append((qi, qa, qb))
    return out


def _handoff_cut(scene, P, merged, D, ids, team):
    """changes_loop2 BA-T11b: a dribble handoff to a teammate running past is decoded late: the giver keeps the
    ball inside his 1.5 m exit radius while the receiver runs away with it, so the exchange becomes a short
    'flight' (a pass) and the receiver's control starts 0.4-0.9 s late. For consecutive teammates' segments,
    take the giver-receiver closest approach over [giver end - pass.handoff_lookback_s, receiver start]; when
    the two are within pass.handoff_max_dist_m there and the ball is within exit_radius_m of both, the
    exchange happened at that frame: the giver's segment ends one frame before it and the receiver's starts
    at it (an 'exchange' free interval: start_kind handoff, no pass)."""
    Pp = PARAMS["pass"]
    out = list(merged)
    for j in range(1, len(out)):
        (pi, pa, pb), (qi, qa, qb) = out[j - 1], out[j]
        if pi == qi or team[pi] != team[qi] or qa - pb <= 1:
            continue
        ka, kb = scene.kins[ids[pi]], scene.kins[ids[qi]]
        w0 = max(pa + 1, pb - _frames(Pp["handoff_lookback_s"]))
        dd = mv.dist(ka, kb)[w0:qa + 1]
        if len(dd) == 0 or not np.any(np.isfinite(dd)):
            continue
        t = w0 + int(np.nanargmin(dd))
        if t >= qa or float(dd[t - w0]) > Pp["handoff_max_dist_m"]:
            continue
        if not (D[pi, t] <= P.exit_radius_m and D[qi, t] <= P.exit_radius_m):
            continue
        out[j - 1] = (pi, pa, t - 1)
        out[j] = (qi, t, qb)
    return out


def _confirm_team_changes(scene, P, S, merged, D, ids, team, contacts):
    """Team-change confirmation: a short segment of one team between two segments of the other team is
    contact (deflection, reach-in, defender in contact with a driver), not a change of possession.
    changes_loop3 BA-T3c: run again after the possession prior, which can turn a short defence segment
    between the deflector and the recoverer into the recoverer's control and so form a new O-D-O triplet."""
    ball = scene.ball
    j = 1
    nb = len(ball.speed)
    while j < len(merged):
        (pi, pa, pb), (qi, qa, qb) = merged[j - 1], merged[j]
        short = (qb - qa) * DT < P.team_change_confirm_s
        nxt_a = merged[j + 1][1] if j + 1 < len(merged) else scene.n
        # changes_loop1 BA-T10: a short defender segment in the shooter's last frames followed by a shot
        # flight is a closeout contest, not a possession change; the flight is the shooter's
        # changes_loop4 BA-R4a: either team's shooter (each at its own basket)
        if team[pi] != team[qi] and short and (qa - pb) * DT <= P.contact_merge_max_s and qb + 3 < nb \
                and np.any(np.isfinite(ball.speed[qb + 1:qb + 4])) \
                and float(np.nanmean(ball.speed[qb + 1:qb + 4])) >= P.flight_min_speed_mps \
                and _shot_like(scene, qb, nxt_a - 1, S, team[pi]):
            contacts.append((ids[qi], qa, qb))
            merged[j - 1] = (pi, pa, qb)
            del merged[j]
            continue
        if j + 1 >= len(merged):
            break
        ri, ra, rb = merged[j + 1]
        # changes_loop1 BA-T3: a deflected ball rolling slowly away stays inside the deflector's exit radius
        # for longer than team_change_confirm_s; a slow, receding ball after his segment marks contact
        nxt_slow = False
        # changes_loop2 BA-T3b: also when the recoverer's control starts right after the deflector's (an
        # adjacent 'exchange'): at sigma 0.3-0.5 the rolling ball is handed from the deflector's exit radius
        # straight into the recoverer's enter radius
        if qb + 1 < nb:
            sl = ball.speed[qb + 1:min(nb, qb + 1 + P.deflect_slow_frames)]
            nxt_slow = bool(np.any(np.isfinite(sl)) and np.nanmean(sl) < P.flight_min_speed_mps)
        recede = bool(D[qi, qb] - np.nanmin(D[qi, qa:qb + 1]) >= P.deflect_recede_m)
        deflect = nxt_slow and recede and (qb - qa) * DT < P.deflect_max_s
        if team[pi] == team[ri] != team[qi] and (short or deflect):
            contacts.append((ids[qi], qa, qb))
            del merged[j]
            if pi == ri and (ra - pb) * DT <= P.contact_merge_max_s:
                merged[j - 1] = (pi, pa, rb)
                del merged[j]
            continue
        j += 1
    return merged


def _build_model(scene, P) -> BallModel:
    raw, ids, D, kins, team = _decode(scene, P)
    if not raw:
        return BallModel([], [], [], D, ids)
    ball = scene.ball
    # merge same-player flicker (short gap, ball barely moved)
    merged = []
    for i, a, b in raw:
        if merged and merged[-1][0] == i and (a - merged[-1][2]) * DT <= P.merge_gap_s:
            pb = merged[-1][2]
            if math.hypot(ball.x[a] - ball.x[pb], ball.y[a] - ball.y[pb]) < P.merge_max_travel_m:
                merged[-1] = (i, merged[-1][1], b)
                continue
        merged.append((i, a, b))
    # team-change confirmation (contact, not a possession change), before and after the possession prior
    contacts = []
    S = _params("shot_release", {})
    merged = _confirm_team_changes(scene, P, S, merged, D, ids, team, contacts)
    merged = _possession_prior(scene, P, S, merged, D, ids, team, contacts)
    merged = _confirm_team_changes(scene, P, S, merged, D, ids, team, contacts)
    merged = _handoff_cut(scene, P, merged, D, ids, team)
    segs, taps = [], []
    for i, a, b in merged:
        pid = ids[i]
        k = scene.kins[pid]
        sd = np.hypot(np.sqrt(np.maximum(ball.var_p, 0)), np.sqrt(np.maximum(k.var_p, 0))) * K_CAL
        pin = p_below(D[i], P.exit_radius_m, sd)
        c = Ctl(pid, pid in scene.offense, a, b, window_conf(pin, a, b))
        if (b - a) * DT >= P.min_touch_s - 1e-9:
            segs.append(c)
        else:
            taps.append(c)  # < 0.1 s: a tap, not a touch (BA-04); flights pass through it
    frees = []
    for j, s in enumerate(segs):
        nxt = segs[j + 1] if j + 1 < len(segs) else None
        a = s.b + 1
        if nxt is not None:
            b = nxt.a - 1
        else:
            b = s.b
            while b + 1 < scene.n and np.isfinite(ball.x[b + 1]):
                b += 1
        if nxt is not None and b < a:
            frees.append(Free(a, b, s, nxt, "exchange", t_release=s.b, t_catch=nxt.a))
            continue
        if b < a:
            continue
        si = ids.index(s.pid)
        ed = ball.edge[a - 1:b + 1]
        cut = np.any((ed[1:] == 0) & (ed[:-1] == 0))  # end of one ball segment next to the start of another
        bad = np.isin(ball.state[a:b + 1], ("interp_long", "none"))
        if np.any(~np.isfinite(ball.x[a:b + 1])) or cut or np.any(bad):
            frees.append(Free(a, b, s, nxt, "unknown"))  # no FLIGHT may span a cut or a long gap
            continue
        end = nxt.a if nxt is not None else b
        travel = float(math.hypot(ball.x[end] - ball.x[s.b], ball.y[end] - ball.y[s.b]))
        air = (end - s.b) * DT
        k3 = min(b, s.b + 3)
        speed0 = float(np.nanmean(ball.speed[a:k3 + 1]))
        away = bool(D[si, k3] > D[si, s.b])
        slow = ball.speed[a:b + 1] < P.flight_min_speed_mps
        run = best = 0
        for v in slow:
            run = run + 1 if v else 0
            best = max(best, run)
        loose_s = best * DT
        # BA-T1: a close finish leaves the hand slowly (smoothed speed0 < flight speed); the ball still
        # reaches the rim, so it is a flight
        ks = scene.kins[s.pid]
        rim_fin = bool(np.nanmin(_rim_dist(scene, s.off, ball.x[a:b + 1], ball.y[a:b + 1])) <= P.rim_finish_reach_m) \
            and float(_rim_dist(scene, s.off, ks.x[s.b], ks.y[s.b])) <= P.rim_finish_releaser_r_max_m
        kind = "flight" if ((speed0 >= P.flight_min_speed_mps or rim_fin) and away) else "loose"
        # mean flight speed between the control frames (both ends are inside the radii, so the ratio is
        # unbiased); the smoothed speed at the ends is not (CA-RTS lag)
        v = max(travel / max(air, DT), P.flight_min_speed_mps)
        look = _frames(P.refine_window_s)
        # release: the later of (a) the last frame with the ball within refine_radius_m of the releaser and
        # (b) the extrapolation back from the control end at the mean flight speed. (a) wins for slow
        # exchanges (handoffs, pitches) where (b) over-corrects; (b) wins when noise pushes the ball
        # beyond 0.5 m for a few frames before the true release. Catch: the earlier of the mirrored pair.
        t_ext = int(np.clip(s.b - round(max(0.0, P.exit_radius_m - P.refine_radius_m) / (v * DT)), s.a, s.b))
        near = [t for t in range(max(s.a, s.b - look), s.b + 1) if D[si, t] <= P.refine_radius_m]
        t_rel = max(near[-1], t_ext) if near else t_ext
        t_cat = None
        if nxt is not None:
            ni = ids.index(nxt.pid)
            t_ext = int(np.clip(nxt.a + round(max(0.0, P.enter_radius_m - P.refine_radius_m) / (v * DT)),
                                nxt.a, nxt.b))
            near = [t for t in range(nxt.a, min(nxt.b, nxt.a + look) + 1) if D[ni, t] <= P.refine_radius_m]
            t_cat = min(near[0], t_ext) if near else t_ext
            nxt.t_catch = t_cat
        # travel and air between the refined release and catch frames (the control frames sit 1.5 m and
        # 1.0 m from the hands, so raw values understate short passes by up to 2.5 m)
        te = t_cat if t_cat is not None else b
        travel_ref = float(math.hypot(ball.x[te] - ball.x[t_rel], ball.y[te] - ball.y[t_rel]))
        air_ref = (te - t_rel) * DT
        frees.append(Free(a, b, s, nxt, kind, travel_ref, air_ref, speed0, away, loose_s, t_rel, t_cat))
    return BallModel(segs, frees, taps, D, ids, contacts)


def _model(scene, **ov) -> BallModel:
    """Cached control decode; flights are always shot-classified with the YAML shot_release params."""
    P = _params("touch", ov)

    def build():
        m = _build_model(scene, P)
        S = _params("shot_release", {})
        for f, info in zip(m.frees, _shot_scan(scene, m, S)):
            f.shot, f.rim_frame, f.shot_crit, f.airball = info
        return m
    return _cache(scene, _key("model", ov), build)


def _shot_scan(scene, m, S):
    """BA-80 XY proxy on every flight: toward the rim, reaches the rim, does not pass through, not an oop.

    Returns one (is_shot, rim_frame, criteria) tuple per free interval of the model (no mutation).
    """
    ball = scene.ball
    res = []
    for f in m.frees:
        res.append((False, None, {}, False))
        if f.kind != "flight":
            continue
        s = f.prev
        # changes_loop4 BA-R4a: coordinates relative to the releasing team's basket
        rx, ry = _rim(scene, s.off)
        BX, BY = ball.x - rx, ball.y - ry
        hi = min(f.b, s.b + _frames(S.max_flight_s))
        # changes_loop4 BA-R4d: a player standing under the rim (rebounder, tipper) enters his 1.0 m control run
        # while the ball is still flying over him to the rim; the rim-reach search follows the ball into his
        # control for up to rim_reach_ext_s while it keeps flight speed (a caught ball slows to the catcher's pace)
        if f.nxt is not None and hi == f.b:
            lim = min(f.nxt.b, f.b + _frames(S.rim_reach_ext_s))
            vmin = PARAMS["touch"]["flight_min_speed_mps"]
            while hi < lim and np.isfinite(ball.speed[hi + 1]) and ball.speed[hi + 1] >= vmin:
                hi += 1
        rr = np.hypot(BX[s.b:hi + 1], BY[s.b:hi + 1])
        if len(rr) == 0 or not np.any(np.isfinite(rr)):
            continue
        j = int(np.nanargmin(rr))
        rim_t, rmin = s.b + j, float(rr[j])
        bx0, by0 = float(BX[s.b]), float(BY[s.b])
        r0 = math.hypot(bx0, by0)
        tdir = min(rim_t, s.b + max(2, _frames(S.dir_window_s)))
        dvec = (BX[tdir] - bx0, BY[tdir] - by0)
        dang = _ang(dvec, (-bx0, -by0)) if r0 >= S.layup_r_m else 0.0
        # pass-through: forward progress beyond the rim along the release direction
        # BA-T2: measured on the ball track through the receiver's control (f.b stops where the receiver's
        # 1.0 m enter run starts, which hides most of a dump-off's progress past the rim)
        hi_pt = f.nxt.b if f.nxt is not None else f.b
        tpt = min(hi_pt, rim_t + _frames(S.pass_through_window_s))
        u = np.array([-bx0, -by0]) / max(r0, 1e-6)
        prog = float((BX[tpt] - BX[rim_t]) * u[0] + (BY[tpt] - BY[rim_t]) * u[1])
        oop = False
        # changes_loop4 BA-R4c: an alley-oop is caught by another player as the ball arrives (refined catch within
        # oop_catch_lag_s of the rim frame); a teammate (or the shooter) who gains the ball later took a rebound
        t_cat = f.t_catch if f.t_catch is not None else (f.nxt.a if f.nxt is not None else None)
        if f.nxt is not None and f.nxt.off == s.off and f.nxt.pid != s.pid \
                and f.nxt.a <= rim_t + _frames(S.oop_window_s) and (t_cat - rim_t) * DT <= S.oop_catch_lag_s:
            rk = scene.kins[f.nxt.pid]
            oop = float(_rim_dist(scene, s.off, rk.x[f.nxt.a], rk.y[f.nxt.a])) <= S.oop_catch_r_m
        sig_b = _sig(ball, rim_t)
        crit = {
            "rim_reach": _crit(rmin, S.rim_reach_m, float(p_below(rmin, S.rim_reach_m, sig_b))),
            "direction": _crit(dang if np.isfinite(dang) else 180.0, S.dir_tol_deg,
                               float(phi((S.dir_tol_deg - (dang if np.isfinite(dang) else 180.0)) / 5.0))),
            "pass_through": _crit(prog, S.pass_through_max_m,
                                  float(p_below(prog, S.pass_through_max_m, sig_b * 1.5))),
        }
        aimed = np.isfinite(dang) and dang <= S.dir_tol_deg
        ok = rmin <= S.rim_reach_m and aimed and prog <= S.pass_through_max_m and not oop
        airball = False
        # the free interval stops at the grabber's 1.0 m enter run; follow the ball into his hands
        hi_air = min(f.nxt.b, f.nxt.a + _frames(S.pass_through_window_s)) if f.nxt is not None else hi
        ra_ = np.hypot(BX[s.b:hi_air + 1], BY[s.b:hi_air + 1])
        rmin_air = float(np.nanmin(ra_)) if np.any(np.isfinite(ra_)) else float("inf")
        # changes_loop2 BA-T9b: the airball tests are noise-aware; the direction, short-of-rim and pass-through
        # thresholds widen by airball_noise_k standard errors of the measured quantity (ball sigma at the rim
        # frame; direction error sqrt(2) sigma / |release displacement|), so the class does not flip with
        # the tracking tier
        dlen = float(math.hypot(*dvec)) if np.all(np.isfinite(dvec)) else 0.0
        sd_ang = math.degrees(math.sqrt(2) * sig_b / max(dlen, 0.5))
        k_air = S.airball_noise_k
        aimed_air = np.isfinite(dang) and dang <= S.dir_tol_deg + k_air * sd_ang
        if not ok and aimed_air and not oop and S.rim_reach_m < rmin_air <= S.airball_r_max_m + k_air * sig_b and \
                r0 >= S.airball_release_r_min_m and prog <= S.pass_through_max_m + k_air * sig_b * 1.5:
            # changes_loop1 BA-T9: a jumper that falls short (airball) and ends loose or with an opponent,
            # with no teammate near the ball where it came closest to the rim, is still an FGA
            lost = f.nxt is None or f.nxt.off != s.off or f.loose_s >= PARAMS["touch"]["loose_min_s"]
            mates = [o for o in (scene.offense if s.off else scene.defense) if o != s.pid]
            t_air = s.b + int(np.nanargmin(ra_))
            _, dm = _nearest(scene, mates, t_air, *_xy(ball, t_air))
            if lost and dm > S.airball_teammate_clear_m:
                airball = ok = True
                rim_t = t_air
                crit["rim_reach"] = _crit(rmin_air, S.airball_r_max_m,
                                          float(p_below(rmin_air, S.airball_r_max_m, sig_b)))
        res[-1] = (bool(ok), rim_t if ok else None, crit, airball)
    return res


def _free_after(m, seg):
    for f in m.frees:
        if f.prev is seg:
            return f
    return None


def _free_before(m, seg):
    for f in m.frees:
        if f.nxt is seg:
            return f
    return None


def _start_kind(scene, m, s):
    f = _free_before(m, s)
    if f is None:
        return "clip_start" if s.a < _frames(PARAMS["touch"]["clip_start_s"]) else "unknown"
    if f.kind == "unknown":
        return "unknown"
    same = f.prev.off == s.off
    if f.kind == "exchange":
        return "handoff" if same else "steal"
    if f.shot:
        return "rebound"
    if f.kind == "flight" and f.loose_s < PARAMS["touch"]["loose_min_s"]:
        return "pass" if same and f.prev.pid != s.pid else ("interception" if not same else "regather")
    return "loose_ball"


def _end_kind(scene, m, s):
    f = _free_after(m, s)
    if f is None:
        return "dead"
    if f.kind == "unknown":
        return "unknown"
    if f.kind == "exchange":
        return "handoff" if f.nxt.off == s.off else "turnover"
    if f.shot:
        return "shot"
    if f.kind == "flight":
        if f.nxt is None:
            return "pass_unresolved"
        if f.loose_s >= PARAMS["touch"]["loose_min_s"]:
            return "lost"
        return "pass" if f.nxt.off == s.off and f.nxt.pid != s.pid else (
            "turnover" if f.nxt.off != s.off else "regather")
    return "lost"


# --------------------------------------------------------------------------------------
# L1 detectors
# --------------------------------------------------------------------------------------
def detect_touch(scene, **params) -> list[Event]:
    """BA-00/BA-04: one event per control segment (touch) with start / end kinds and touch time."""
    m = _model(scene, **params) if params else _model(scene)
    out = []
    for s in m.segs:
        k = scene.kins[s.pid]
        t0 = s.t_catch if s.t_catch is not None else s.a
        out.append(Event("touch", {"holder": s.pid, "team": "offense" if s.off else "defense"}, t0, s.a, s.b,
                         _conf(s.conf, k, t0, s.a, s.b),
                         {"touch_time_s": round((s.b - t0) * DT, 3), "start_kind": _start_kind(scene, m, s),
                          "end_kind": _end_kind(scene, m, s), "x": round(_xy(k, t0)[0], 2),
                          "y": round(_xy(k, t0)[1], 2), "spot": spot_labels(*_xy(k, t0)),
                          "research_id": "BA-00/BA-04"}))
    return out


def detect_team_possession(scene, **params) -> list[Event]:
    """BA-00 team_in_control: maximal run of one team's touches (flights between teammates bridged)."""
    P = _params("team_possession", params)
    m = _model(scene)
    out, run = [], []
    for s in m.segs + [None]:
        if run and (s is None or s.off != run[-1].off):
            a, b = run[0].a, run[-1].b
            if (b - a) * DT >= P.min_s:
                pc = min(x.conf for x in run)
                out.append(Event("team_possession", {"team": "offense" if run[0].off else "defense"}, a, a, b,
                                 _conf(pc, scene.ball, a, a, b),
                                 {"n_touches": len(run), "holders": [x.pid for x in run],
                                  "research_id": "BA-00"}))
            run = []
        if s is not None:
            run.append(s)
    return out


def detect_ball_flight(scene, **params) -> list[Event]:
    """BA-00 FLIGHT: release -> ball moving >= flight speed away from the holder -> next control or end."""
    P = _params("ball_flight", params)
    m = _model(scene)
    out = []
    for f in m.frees:
        if f.kind != "flight":
            continue
        end = f.nxt.a if f.nxt is not None else f.b
        if f.air < P.min_air_s - 1e-9 or f.travel < P.min_travel_m:
            continue
        sb = _sig(scene.ball, f.t_release)
        pc = min(float(p_above(f.travel, P.min_travel_m, sb * math.sqrt(2))), f.prev.conf)
        out.append(Event("ball_flight", {"from": f.prev.pid, "to": f.nxt.pid if f.nxt else None},
                         f.t_release, f.t_release, end, _conf(pc, scene.ball, f.t_release, f.t_release, end),
                         {"travel_m": round(f.travel, 2), "air_s": round(f.air, 3), "shot": f.shot,
                          "loose_s": round(f.loose_s, 3), "research_id": "BA-00"}))
    return out


def detect_loose_ball(scene, **params) -> list[Event]:
    """BA-00 LOOSE: ball outside control, slower than flight speed, for >= loose_min_s."""
    P = _params("loose_ball", params)
    m = _model(scene)
    ball = scene.ball
    out = []
    oob = None
    for f in m.frees:
        if f.kind not in ("flight", "loose") or f.b < f.a:
            continue
        if oob is None:  # changes_loop1 BA-T12: a ball resting out of bounds is dead, not loose
            oob = np.array([np.isfinite(ball.x[t]) and "out_of_bounds" in region(*_xy(ball, t))
                            for t in range(scene.n)], dtype=bool)
        slow = (ball.speed < P.max_speed_mps) & ~oob
        for a, b in mv.hysteresis(slow[f.a:f.b + 1], slow[f.a:f.b + 1], P.min_s):
            a, b = a + f.a, b + f.a
            pc = window_conf(p_below(ball.speed, P.max_speed_mps, ball.sigma_speed), a, b)
            out.append(Event("loose_ball", {"last_holder": f.prev.pid, "recovered_by": f.nxt.pid if f.nxt else None},
                             a, a, b, _conf(pc, ball, a, a, b),
                             {"after_shot": f.shot, "duration_s": round((b - a) * DT, 3), "research_id": "BA-00"}))
    return out


def detect_contested_ball(scene, **params) -> list[Event]:
    """BA-00 CONTESTED / held-ball candidate: an offensive and a defensive player both on a slow ball.

    changes_loop1 BA-T4: distances alone fire on ordinary on-ball defence (precision 0.02-0.05). A frame is
    contested only when, besides the distance test, (a) no stable controller exists (a free-ball frame of the
    control decode) or (b) the ball lies between the two players (moving-mean projection onto the O-D segment
    in [between_proj_lo, between_proj_hi], lateral offset <= between_lateral_m) while both are still
    (stationary_s2 < still_s2_max) and the moving-mean ball speed is < ball_still_mps; a (b) run must last
    held_ball_min_s. Events whose t0 is within 5 frames of a ball segment edge (edge_factor 0) are dropped.
    """
    P = _params("contested_ball", params)
    ball = scene.ball
    if ball is None or not scene.offense or not scene.defense:
        return []
    n = scene.n
    off_d = np.stack([np.hypot(ball.x - scene.kins[o].x, ball.y - scene.kins[o].y) for o in scene.offense])
    def_d = np.stack([np.hypot(ball.x - scene.kins[o].x, ball.y - scene.kins[o].y) for o in scene.defense])
    Do, Dd = np.min(off_d, 0), np.min(def_d, 0)
    w = max(1, _frames(P.mean_window_s))
    ker = np.ones(w) / w

    def mmean(v, fill):
        return np.convolve(np.nan_to_num(v, nan=fill), ker, mode="same")

    mDo, mDd = mmean(Do, 99.0), mmean(Dd, 99.0)
    with np.errstate(invalid="ignore"):
        near = (mDo <= P.radius_m) & (mDd <= P.radius_m) & (np.abs(mDo - mDd) <= P.margin_m) & \
            (ball.speed < P.ball_max_speed_mps)
    # (a) free-ball frames of the control decode
    free = np.array([h is None for h in _holder_array(scene)], dtype=bool)
    # (b) ball between the nearest offensive and defensive player, both still, ball still
    io = np.argmin(np.where(np.isnan(off_d), np.inf, off_d), 0)
    idf = np.argmin(np.where(np.isnan(def_d), np.inf, def_d), 0)
    rows = np.arange(n)
    OX = np.stack([scene.kins[o].x for o in scene.offense])[io, rows]
    OY = np.stack([scene.kins[o].y for o in scene.offense])[io, rows]
    DX = np.stack([scene.kins[o].x for o in scene.defense])[idf, rows]
    DY = np.stack([scene.kins[o].y for o in scene.defense])[idf, rows]
    S2o = np.stack([scene.kins[o].stationary_s2 for o in scene.offense])[io, rows]
    S2d = np.stack([scene.kins[o].stationary_s2 for o in scene.defense])[idf, rows]
    wb = max(1, _frames(P.between_window_s))
    kb = np.ones(wb) / wb

    def bmean(v):
        return np.convolve(np.nan_to_num(v, nan=0.0), kb, mode="same")

    bx, by = bmean(ball.x), bmean(ball.y)
    OX, OY, DX, DY = bmean(OX), bmean(OY), bmean(DX), bmean(DY)
    with np.errstate(invalid="ignore", divide="ignore"):
        ux, uy = DX - OX, DY - OY
        L2 = ux * ux + uy * uy
        lam = ((bx - OX) * ux + (by - OY) * uy) / L2
        lat = np.abs((bx - OX) * uy - (by - OY) * ux) / np.sqrt(L2)
        still = (mmean((S2o < P.still_s2_max).astype(float), 0.0) >= 0.5) & \
            (mmean((S2d < P.still_s2_max).astype(float), 0.0) >= 0.5)
        between = (lam >= P.between_proj_lo) & (lam <= P.between_proj_hi) & (lat <= P.between_lateral_m) & \
            still & (bmean(ball.speed) < P.ball_still_mps)
    runs = mv.hysteresis(near & free, near & free, P.min_frames * DT, max_gap_frames=P.max_gap_frames)
    # a confirmed run spans the enclosing distance run: the stillness test lags the arrival by 0.2-0.4 s,
    # and the tie-up starts when both players are on the ball
    near_runs = mv.hysteresis(near, near, 0.0, max_gap_frames=P.max_gap_frames)
    lb = _frames(P.onset_lookback_s)
    runs = [next(((max(na, a - lb), nb) for na, nb in near_runs if na <= a and b <= nb), (a, b)) for a, b in runs]
    # changes_loop2 BA-T4b: a ball-between (tie-up) run starts when both players have come to rest on the ball:
    # the start of the rest stretch (the faster of the two smoothed speeds below onset_still_mps for >=
    # onset_still_s, gaps <= onset_still_gap_frames) that contains the run start, back by at most onset_search_s. The near
    # run's own start scatters 0.3-1.0 s either way under noise (the moving-mean distances cross the margin
    # early or break late); the speeds do not.
    So = np.stack([scene.kins[o].speed for o in scene.offense])[io, rows]
    Sd = np.stack([scene.kins[o].speed for o in scene.defense])[idf, rows]
    with np.errstate(invalid="ignore"):
        rest = np.maximum(So, Sd) < P.onset_still_mps
    ws, sb = _frames(P.onset_still_s), _frames(P.onset_search_s)
    rest_runs = mv.hysteresis(rest, rest, P.onset_still_s, max_gap_frames=P.onset_still_gap_frames)
    for a, b in mv.hysteresis(near & between, near & between, P.held_ball_min_s, max_gap_frames=P.max_gap_frames):
        # the rest stretch that contains the run start (else the first one that starts inside the run),
        # back by at most onset_search_s
        t0 = next((max(ra_, a - sb) for ra_, rb_ in rest_runs if ra_ <= a <= rb_), None)
        if t0 is None:
            t0 = next((ra_ for ra_, rb_ in rest_runs if a < ra_ <= b), None)
        if t0 is None:
            t0 = next((max(na, a - lb) for na, nb in near_runs if na <= a and b <= nb), a)
        runs.append((t0, b))
    runs = sorted(set(runs))
    merged = []
    for a, b in runs:
        if merged and a <= merged[-1][1] + P.max_gap_frames + 1:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    out = []
    s = mv.K_CAL * np.sqrt(np.maximum(ball.var_p, 1e-6)) * math.sqrt(2) / math.sqrt(w)
    for a, b in merged:
        if edge_factor(ball, a) == 0.0:
            continue
        pc = min(window_conf(p_below(mDo, P.radius_m, s), a, b), window_conf(p_below(mDd, P.radius_m, s), a, b))
        t = (a + b) // 2
        oo = _nearest(scene, scene.offense, t, *_xy(ball, t))[0]
        dd = _nearest(scene, scene.defense, t, *_xy(ball, t))[0]
        # changes_loop3 BA-T4c: at the high-noise tier a ball 0.3 m from both players and a ball at the holder
        # with a defender 0.75 m away overlap in every gate (measured P/R 0.30 / 0.30 at sigma_p 0.5); say so
        sp = max(math.hypot(_sig(ball, a), _sig(scene.kins[o], a)) for o in (oo, dd) if o is not None) \
            if oo is not None or dd is not None else _sig(ball, a)
        status = "noise_limited" if sp > P.noise_limited_pair_sigma_m else "ok"
        out.append(Event("contested_ball", {"offense": oo, "defense": dd}, a, a, b, _conf(pc, ball, a, a, b),
                         {"held_ball_candidate": (b - a) * DT >= P.held_ball_min_s, "noise_status": status,
                          "pair_sigma_m": round(sp, 3),
                          "basis": "free_ball" if free[a:b + 1].mean() >= 0.5 else "ball_between",
                          "possession_arrow": "needs_pbp", "research_id": "BA-00"}))
    return out


def detect_catch(scene, **params) -> list[Event]:
    """BA-01: first control frame after a FLIGHT or LOOSE ball, refined to d_bp = 0.5 m."""
    P = _params("catch", params)
    m = _model(scene)
    out = []
    for f in m.frees:
        s = f.nxt
        if s is None or f.kind not in ("flight", "loose"):
            continue
        k = scene.kins[s.pid]
        t0 = s.t_catch if s.t_catch is not None else s.a
        w = _frames(P.speed_window_s)
        sp = float(np.nanmean(k.speed[t0:min(s.b, t0 + w) + 1]))
        x, y = _xy(k, t0)
        others = scene.defense if s.off else scene.offense
        dn, dd = _nearest(scene, others, t0, x, y)
        clos = float("nan")
        if dn is not None:
            c0 = max(0, t0 - _frames(P.closing_window_s))
            clos = float(np.nanmean(mv.closing_speed(k, scene.kins[dn])[c0:t0 + 1]))
        out.append(Event("catch", {"receiver": s.pid, "passer": f.prev.pid if f.prev else None}, t0, s.a, s.b,
                         _conf(s.conf, scene.ball, t0, s.a, min(s.b, t0 + w)),
                         {"after": "shot" if f.shot else f.kind, "catch_on_move": bool(sp >= P.on_move_speed_mps),
                          "speed_mps": round(sp, 2), "r": round(math.hypot(x, y), 2), "d3": round(coord("d3", x, y), 2),
                          "spot": spot_labels(x, y), "court_region": region(x, y),
                          "nearest_def": dn, "nearest_def_m": round(dd, 2), "def_closing_mps": round(clos, 2),
                          "research_id": "BA-01"}))
    return out


def detect_release(scene, **params) -> list[Event]:
    """BA-02: last control frame before a FLIGHT; kind order shot > lost > intercepted > pass (checker fix)."""
    _params("release", params)
    m = _model(scene)
    out = []
    for f in m.frees:
        if f.kind != "flight":
            continue
        s = f.prev
        if f.shot:
            kind = "shot"
        elif f.loose_s >= PARAMS["touch"]["loose_min_s"] or f.nxt is None:
            kind = "lost" if f.nxt is not None else "unresolved"
        elif not f.nxt.off == s.off:
            kind = "intercepted"
        elif f.nxt.pid == s.pid:
            continue  # regather by the same player: not a release (CMU dribble-through-traffic error)
        else:
            kind = "pass"
        t0 = f.t_release
        # changes_loop2 T18b: a shot release (rim finishes especially) sits next to the end of the ball track
        # segment (the ball is lost at the rim), so the ball's edge factor is 0 there; as in shot_release, the
        # edge factor of a shot release is the shooter's
        kc = scene.kins[s.pid] if kind == "shot" else scene.ball
        out.append(Event("release", {"holder": s.pid}, t0, t0, s.b, _conf(s.conf, kc, t0, t0, s.b),
                         {"release_kind": kind, "ball_speed_mps": round(f.speed0, 2), "research_id": "BA-02"}))
    return out


def _dribble_interval(scene, m, s, P):
    """Travel-bound dribble proxy inside one touch -> (t0, tc, te, max_disp, conf) or None."""
    k = scene.kins[s.pid]
    sk = _start_kind(scene, m, s)
    # changes_loop1 BA-T7: the gather allowance applies only to a catch on the move; after a set catch the
    # pivot foot is down at the catch. The end is measured from the refined release, not the control end.
    t_c = s.t_catch if s.t_catch is not None else s.a
    sp_c = float(np.nanmean(k.speed[t_c:min(s.b, t_c + _frames(P.catch_move_window_s)) + 1]))
    moving = sp_c >= PARAMS["catch"]["on_move_speed_mps"]
    tp = t_c + (_frames(P.gather_allowance_s) if sk not in ("clip_start", "unknown") and moving else 0)
    ek = _end_kind(scene, m, s)
    fa = _free_after(m, s)
    tend = fa.t_release if fa is not None and fa.t_release is not None else s.b
    te = tend - (_frames(P.final_gather_s) if ek in ("pass", "shot", "handoff", "lost") else 0)
    if te <= tp:
        return None
    x0, y0 = _xy(k, tp)
    disp = np.hypot(k.x[tp:te + 1] - x0, k.y[tp:te + 1] - y0)
    if not np.any(disp >= P.travel_bound_m):
        return None
    tc = tp + int(np.argmax(disp >= P.travel_bound_m))
    t0 = tc  # onset of the travelling run, not before the touch start
    # changes_loop1 BA-T14: walk back only while the holder is also not stationary (MP-09 chi-square);
    # smoothed noise speed alone reaches ~1 m/s at sigma 0.5
    s2 = k.stationary_s2
    sp0 = _sig(k, tp) * math.sqrt(2)
    while t0 - 1 >= s.a and k.speed[t0 - 1] >= P.onset_speed_mps and s2[t0 - 1] >= P.onset_s2_min and \
            (moving or t0 - 1 < tp or math.hypot(k.x[t0 - 1] - x0, k.y[t0 - 1] - y0) >= P.onset_disp_k * sp0):
        t0 -= 1
    jmax = tp + int(np.nanargmax(disp))
    pc = float(p_above(float(np.nanmax(disp)), P.travel_bound_m, _sig2(k, tp, k, jmax)))
    return t0, tc, te, float(np.nanmax(disp)), pc


def detect_dribble_inferred(scene, **params) -> list[Event]:
    """BA-03 XY proxy: the holder leaves a travel-bound circle around his pivot point, so he must dribble."""
    P = _params("dribble_inferred", params)
    m = _model(scene)
    out = []
    for s in m.segs:
        r = _dribble_interval(scene, m, s, P)
        if r is None:
            continue
        t0, tc, te, md, pc = r
        k = scene.kins[s.pid]
        out.append(Event("dribble_inferred", {"handler": s.pid}, t0, t0, te, _conf(min(pc, s.conf), k, t0, t0, te),
                         {"max_disp_m": round(md, 2), "dribble_count": "unknown_needs_ball_z",
                          "method": "travel_bound", "research_id": "BA-03"}))
    return out


def _dribbled(scene, s):
    """Cached dribble proxy result for a touch (default params)."""
    m = _model(scene)
    P = _params("dribble_inferred", {})
    return _cache(scene, ("drib", s.pid, s.a), lambda: _dribble_interval(scene, m, s, P))


# --------------------------------------------------------------------------------------
# L2: drives
# --------------------------------------------------------------------------------------
@dataclass
class _Drive:
    s: Ctl
    t0: int
    t1: int
    ra: int
    rb: int
    r0: float
    rmin: float
    gain: float
    vr_mean: float
    subtype: str
    pc: float
    crit: dict
    te: int = -1  # changes_loop2 BA-T14b: approach-end time (event t0 of drive_depth / drive_outcome)


def _find_drives(scene, P):
    m = _model(scene)
    out = []
    for s in m.segs:
        if not s.off:
            continue
        k = scene.kins[s.pid]
        vr = -k.v_r  # mvlib v_r is positive toward the rim; research v_r is negative toward the rim
        r = k.r
        with np.errstate(invalid="ignore"):
            enter = vr <= P.vr_max_mps
        enter[:s.a] = False
        enter[s.b + 1:] = False
        last_t1 = -1
        lo = s.a
        fb = _free_before(m, s)
        if fb is not None and fb.kind == "exchange" and fb.prev is not None and fb.prev.off == s.off:
            # changes_loop1 BA-T11: after a handoff the decoded control starts late (the receiver runs
            # past); the onset may walk back to the closest approach of giver and receiver
            kg = scene.kins[fb.prev.pid]
            w0 = max(fb.prev.a, fb.prev.b - _frames(P.handoff_lookback_s))
            dd = mv.dist(k, kg)[w0:s.a + 1]
            if np.any(np.isfinite(dd)):
                lo = w0 + int(np.nanargmin(dd))
        s2 = k.stationary_s2
        for ra, rb in mv.hysteresis(enter, enter, P.sustain_s, max_gap_frames=P.run_max_gap_frames):
            if ra <= last_t1:
                continue
            t0 = ra
            # changes_loop1 BA-T14: walk back only on frames that are also not stationary (MP-09)
            while t0 - 1 >= lo and vr[t0 - 1] < P.onset_vr_mps and s2[t0 - 1] >= P.onset_s2_min:
                t0 -= 1
            # changes_loop2 BA-T14b: the chi-square statistic needs a few frames to rise after a start from
            # rest, and a slow ramp from rest crosses onset_vr_mps late; continue up to onset_s2_lag_s further
            # while vr < onset_lag_vr_mps (still moving toward the rim), ignoring s2. Only in the
            # low-noise tiers (calibrated sigma <= onset_s2_lag_sigma_max_m): at sigma 0.5 the s2 gate is what
            # stops the noise-driven early drift (BA-T14), and the extra frames would undo it
            lag = _frames(P.onset_s2_lag_s) if _sig(k, t0) <= P.onset_s2_lag_sigma_max_m else 0
            while lag > 0 and t0 - 1 >= lo and vr[t0 - 1] < P.onset_lag_vr_mps:
                t0 -= 1
                lag -= 1
            end, run, t = s.b, 0, rb + 1
            while t <= s.b:
                run = run + 1 if vr[t] > 0 else 0
                if run >= _frames(P.retreat_s):
                    end = t - run
                    break
                t += 1
            tmin = t0 + int(np.nanargmin(r[t0:end + 1]))
            r0, rmin = float(r[t0]), float(r[tmin])
            # end of the approach: first frame after the run with vr >= end_vr_mps, capped at the r minimum
            # (a driver standing still at the end must not move t1 to a noise minimum). t1 is the geometric end
            # (depth class, direction, defender reaction and outcome windows use it).
            t1 = rb
            while t1 + 1 <= tmin and vr[t1 + 1] < P.end_vr_mps:
                t1 += 1
            t1 = min(t1 + 1, tmin) if t1 < tmin else tmin
            # changes_loop2 BA-T14b: te = the time the approach ends (event t0 of drive_depth / drive_outcome):
            # the first frame after the run's peak (most negative vr) where vr rises above a noise-tier-aware
            # threshold, capped at t1. The smoother stretches the deceleration more as the position sigma
            # grows (mvlib Q_HIGH_NOISE at sigma_p >= 0.45), so the fixed end_vr_mps crossing lands 0.2-0.4 s late
            # at sigma 0.5; the threshold moves down by end_vr_sigma_slope per metre of calibrated sigma above
            # end_vr_sigma_ref_m (-1.0 / -1.4 / -2.0 m/s at sigma_p 0.2 / 0.3 / 0.5).
            fin = np.isfinite(vr[ra:rb + 1])
            if np.any(fin):
                thr_end = P.end_vr_mps - P.end_vr_sigma_slope * max(0.0, _sig(k, t1) - P.end_vr_sigma_ref_m)
                te = min(ra + int(np.nanargmin(vr[ra:rb + 1])), t1)
                while te + 1 <= t1 and vr[te + 1] < thr_end:
                    te += 1
                te = min(te + 1, t1)
            else:
                te = t1
            gain = r0 - rmin
            dur = (t1 - t0) * DT
            vrm = float(np.nanmean(vr[ra:rb + 1]))
            x1, y1 = _xy(k, t1)
            d3min = coord("d3", x1, y1)
            if r0 >= P.start_r_min_m and gain >= P.gain_min_m and (rmin <= P.r_min_max_m or d3min <= P.d3_min_max_m):
                sub = "drive"
            elif P.short_start_r_min_m <= r0 < P.start_r_min_m and gain >= P.short_gain_min_m:
                sub = "short_drive"
            else:
                continue
            app = -(r0 - float(r[t1])) / max(dur, DT)  # mean vr over the whole approach [t0, t1]
            if dur < P.min_duration_s - 1e-9 or vrm > P.vr_max_mps or app > P.vr_max_mps:
                continue
            sg = _sig2(k, t0, k, t1)
            thr_r0 = P.start_r_min_m if sub == "drive" else P.short_start_r_min_m
            thr_g = P.gain_min_m if sub == "drive" else P.short_gain_min_m
            crit = {
                "start_r": _crit(r0, thr_r0, p_above(r0, thr_r0, _sig(k, t0))),
                "gain": _crit(gain, thr_g, p_above(gain, thr_g, sg)),
                "v_r": _crit(vrm, P.vr_max_mps, window_conf(p_below(vr, P.vr_max_mps, k.sigma_speed), ra, rb)),
                "approach_v_r": _crit(app, P.vr_max_mps, p_below(app, P.vr_max_mps, sg / max(dur, DT))),
                "duration": _crit(dur, P.min_duration_s, phi((dur - P.min_duration_s) / DT)),
            }
            if sub == "drive":
                crit["depth"] = _crit(rmin, P.r_min_max_m, max(p_below(rmin, P.r_min_max_m, _sig(k, t1)),
                                                               p_below(d3min, P.d3_min_max_m, _sig(k, t1))))
            pc = min([c["p"] for c in crit.values()] + [s.conf])
            out.append(_Drive(s, t0, t1, ra, rb, r0, rmin, gain, vrm, sub, pc, crit, te))
            last_t1 = t1
    return out


def _drives(scene):
    return _cache(scene, ("drives", ()), lambda: _find_drives(scene, _params("drive", {})))


def detect_drive(scene, **params) -> list[Event]:
    """BA-30: holder attack toward the rim (start r >= 5.5, gain >= 3 m, sustained v_r <= -1.5 m/s)."""
    P = _params("drive", params)
    drives = _find_drives(scene, P) if params else _drives(scene)
    m = _model(scene)
    out = []
    for d in drives:
        k = scene.kins[d.s.pid]
        x0, y0 = _xy(k, d.t0)
        dn, dd = _nearest(scene, scene.defense, d.t0, x0, y0)
        # closeout attack: drive within 1.0 s of a catch at which the nearest defender closed fast
        closeout = False
        if d.s.t_catch is not None and (d.t0 - d.s.t_catch) * DT <= P.closeout_window_s:
            dc, _ = _nearest(scene, scene.defense, d.s.t_catch, *_xy(k, d.s.t_catch))
            if dc is not None:
                c0 = max(0, d.s.t_catch - _frames(P.closeout_closing_window_s))
                cs = float(np.nanmean(mv.closing_speed(k, scene.kins[dc])[c0:d.s.t_catch + 1]))
                closeout = cs >= P.closeout_speed_mps
        lb = max(0, d.t0 - _frames(P.transition_lookback_s))
        transition = bool(np.nanmax(k.y[lb:d.t0 + 1]) > spotlib.C["HALF_Y"])
        out.append(Event("drive", {"driver": d.s.pid, "defender": dn}, d.t0, d.t0, d.t1,
                         _conf(d.pc, k, d.t0, d.t0, d.t1),
                         {"subtype": d.subtype, "start_r": round(d.r0, 2), "r_min": round(d.rmin, 2),
                          "gain_m": round(d.gain, 2), "mean_v_r": round(d.vr_mean, 2),
                          "duration_s": round((d.t1 - d.t0) * DT, 3),
                          "nba_drive": bool(d.r0 >= P.nba_start_r_m and d.rmin <= P.nba_rmin_m and not transition),
                          "closeout_attack": closeout, "transition_drive": transition,
                          "start_spot": spot_labels(x0, y0), "criteria": d.crit,
                          "end_kind": _end_kind(scene, m, d.s), "research_id": "BA-30"}))
    return out


def detect_drive_direction(scene, **params) -> list[Event]:
    """BA-31/32: baseline / middle / straight / top via named_spots drive_baseline, drive_middle; side L/R."""
    P = _params("drive_direction", params)
    out = []
    for d in _drives(scene):
        k = scene.kins[d.s.pid]
        hx, hy = _xy(k, d.t0)
        x, y = _xy(k, d.t1)

        def cls(hx_, hy_, x_, y_):
            if in_spot("drive_baseline", x_, y_, hx=hx_, hy=hy_):
                return "baseline"
            if in_spot("drive_middle", x_, y_, hx=hx_, hy=hy_):
                return "middle"
            return "top" if abs(hx_) < P.top_abs_x_m else "straight"

        probs = _sample_probs(cls, [(hx, hy), (x, y)], [_sig(k, d.t0), _sig(k, d.t1)], P.samples)
        lab, p, status, alts = _pick(probs, P.unresolved_margin)
        u = np.array([-hx, -hy]) / max(math.hypot(hx, hy), 1e-6)
        dv = np.array([x - hx, y - hy])
        lat = float(u[0] * dv[1] - u[1] * dv[0])  # > 0: displacement to the driver's left when facing the rim
        side = "left" if lat > P.side_deadband_m else ("right" if lat < -P.side_deadband_m else "straight")
        out.append(Event("drive_direction", {"driver": d.s.pid}, d.t0, d.t0, d.t1,
                         _conf(min(p, d.pc), k, d.t0, d.t0, d.t1),
                         {"label": lab, "status": status, "alternatives": alts, "side": side,
                          "lateral_m": round(lat, 2), "research_id": "BA-31/BA-32"}))
    return out


def _depth_class(x, y):
    """BA-33 fixed partition: rim > floater > paint > baseline_dead > outside_lane_short > short."""
    if in_spot("post_depth_deep", x, y):
        return "rim"
    if in_spot("floater_zone", x, y):
        return "floater"
    if in_spot("paint", x, y):
        return "paint"
    if in_spot("dunker_spot", x, y) or in_spot("short_corner", x, y):
        return "baseline_dead"
    if in_spot("post_depth_standard", x, y):
        return "outside_lane_short"
    return "short"


def detect_drive_depth(scene, **params) -> list[Event]:
    """BA-33: depth class at the drive's r_min frame (complete partition, P from position sampling)."""
    P = _params("drive_depth", params)
    out = []
    for d in _drives(scene):
        k = scene.kins[d.s.pid]
        x, y = _xy(k, d.t1)
        probs = _sample_probs(_depth_class, [(x, y)], [_sig(k, d.t1)], P.samples)
        lab, p, status, alts = _pick(probs, P.unresolved_margin)
        out.append(Event("drive_depth", {"driver": d.s.pid}, d.te, d.t0, d.t1, _conf(p, k, d.te, d.t0, d.t1),
                         {"label": lab, "status": status, "alternatives": alts, "r_min": round(d.rmin, 2),
                          "sd_paint_out": round(coord("sd_paint_out", x, y), 2), "research_id": "BA-33"}))
    return out


def detect_paint_touch(scene, **params) -> list[Event]:
    """BA-34: holder stance in the paint (P_in >= 0.5) for >= 0.2 s cumulative in one touch."""
    P = _params("paint_touch", params)
    m = _model(scene)
    drives = _drives(scene)
    out = []
    for s in m.segs:
        if not s.off:
            continue
        k = scene.kins[s.pid]
        idx = np.arange(s.a, s.b + 1)
        sd = np.array([coord("sd_paint_out", k.x[t], k.y[t]) for t in idx])
        sg = K_CAL * np.sqrt(np.maximum(k.var_p[idx], 1e-6))
        pin = np.asarray(phi(-sd / sg))
        ok = pin >= P.p_in_min
        # changes_loop1 BA-T15: one consecutive run (gaps <= max_gap_frames) of >= min_dwell_s whose window
        # confidence passes p_in_min, not a cumulative count of flickering frames
        runs = [(a, b) for a, b in mv.hysteresis(ok, ok, P.min_dwell_s, max_gap_frames=P.max_gap_frames)
                if window_conf(pin, a, b) >= P.p_in_min]
        if not runs:
            continue
        ra_, rb_ = runs[0]
        t0 = int(idx[ra_])
        tc = s.t_catch if s.t_catch is not None else s.a
        catch_in = bool(coord("sd_paint_out", *_xy(k, tc)) <= 0) and _start_kind(scene, m, s) in ("pass", "handoff")
        via = "catch" if catch_in else ("drive" if any(d.s is s and d.t0 <= t0 <= d.t1 + 3 for d in drives)
                                        else "other")
        pc = window_conf(pin, ra_, rb_)
        out.append(Event("paint_touch", {"holder": s.pid}, t0, t0, s.b, _conf(min(pc, s.conf), k, t0, t0, s.b),
                         {"via": via, "dwell_s": round((rb_ - ra_) * DT, 3), "nba_paint_touch": catch_in,
                          "research_id": "BA-34"}))
    return out


def detect_drive_defender_reaction(scene, **params) -> list[Event]:
    """BA-35 fixed: beaten / recovered / contained, plus first help defender (matchup = nearest at t0)."""
    P = _params("drive_defender_reaction", params)
    out = []
    for d in _drives(scene):
        k = scene.kins[d.s.pid]
        dn, _ = _nearest(scene, scene.defense, d.t0, *_xy(k, d.t0))
        if dn is None:
            continue
        kd = scene.kins[dn]
        sl = slice(d.t0, d.t1 + 1)
        rd, rp = kd.r[sl], k.r[sl]
        sep = mv.dist(k, kd)[sl]
        with np.errstate(invalid="ignore"):
            beat = (rp < rd - P.beaten_margin_m) & (sep >= P.beaten_sep_m)
            rim_side = rd <= rp + P.rim_side_margin_m
        b_runs = mv.hysteresis(beat, beat, P.beaten_min_s)
        sig = mv.sigma_dist(k, kd)[sl]
        if b_runs:
            ba = b_runs[0][0]
            rec = mv.hysteresis(rim_side[ba:], rim_side[ba:], P.recovered_min_s)
            rec_after = [r for r in rec if r[0] > b_runs[0][1] - ba]
            lab = "recovered" if rec_after else "beaten"
            pb = window_conf(np.asarray(p_below(rp - rd, -P.beaten_margin_m, sig)), b_runs[0][0], b_runs[0][1])
        elif rim_side.mean() >= P.contained_frac:
            lab = "contained"
            pb = float(np.mean(p_below(rd - rp, P.rim_side_margin_m, sig)))
        else:
            lab, pb = "unresolved", 0.5
        help_id = help_t = None
        for t in range(d.t0, d.t1 + 1):
            h, hd = _nearest(scene, scene.defense, t, *_xy(k, t), exclude=(dn,))
            if h is not None and hd <= P.help_radius_m:
                help_id, help_t = h, t
                break
        out.append(Event("drive_defender_reaction", {"driver": d.s.pid, "defender": dn, "help": help_id},
                         d.t0, d.t0, d.t1, _conf(min(pb, d.pc), k, d.t0, d.t0, d.t1),
                         {"label": lab, "matchup": "nearest_at_t0_proxy",
                          "help_arrival_s": None if help_t is None else round((help_t - d.t0) * DT, 3),
                          "research_id": "BA-35"}))
    return out


# --------------------------------------------------------------------------------------
# L2: passes
# --------------------------------------------------------------------------------------
@dataclass
class _Pass:
    f: Free
    a: Ctl  # passer touch
    b: Ctl  # receiver touch
    t0: int  # release
    tc: int  # catch
    pc: float
    attrs: dict


def _find_passes(scene, P):
    m = _model(scene)
    ball = scene.ball
    out = []
    for f in m.frees:
        if f.kind != "flight" or f.shot or f.nxt is None:
            continue
        A, B = f.prev, f.nxt
        if B.off != A.off or B.pid == A.pid or f.loose_s >= PARAMS["touch"]["loose_min_s"]:
            continue
        ka, kb = scene.kins[A.pid], scene.kins[B.pid]
        t0, tc = f.t_release, (f.t_catch if f.t_catch is not None else B.a)
        # changes_loop1 BA-T11: closest approach of giver and receiver over [A.b - handoff_lookback_s, B.a]
        # (the receiver of a DHO runs past, so at his late control start he is already > 1.5 m away)
        w0 = max(A.a, A.b - _frames(P.handoff_lookback_s))
        dd = mv.dist(ka, kb)[w0:B.a + 1]
        dex = float(np.nanmin(dd)) if np.any(np.isfinite(dd)) else _d(ka, kb, B.a)
        if dex <= P.handoff_max_dist_m and (f.air <= P.handoff_max_air_s or f.travel <= P.handoff_max_travel_m):
            continue  # handoff exchange (screens family), not a pass
        if f.travel < P.min_travel_m or f.air < P.min_air_s - 1e-9:
            continue
        sb = _sig(ball, t0)
        pc = min(A.conf, B.conf, float(p_above(f.travel, P.min_travel_m, sb * math.sqrt(2))),
                 float(phi((f.air - P.min_air_s) / (2 * DT))))
        xa, ya = _xy(ka, t0)
        xb, yb = _xy(kb, tc)
        tA = A.t_catch if A.t_catch is not None else A.a
        hold = (t0 - tA) * DT
        dr = _dribbled(scene, A)
        if A.t_catch is not None and hold <= P.one_touch_max_s:
            delivery = "one_touch"
        elif dr is not None and (t0 - dr[2]) * DT <= P.off_dribble_max_s + PARAMS["dribble_inferred"]["final_gather_s"]:
            delivery = "off_dribble_inferred"
        else:
            delivery = "from_hold"
        tm = (t0 + tc) // 2
        lane = min((spotlib.seg_dist(_xy(scene.kins[o], tm), (xa, ya), (xb, yb)) for o in scene.defense
                    if np.isfinite(scene.kins[o].x[tm])), default=float("nan"))
        _, dpa = _nearest(scene, scene.defense, t0, xa, ya)
        _, drb = _nearest(scene, scene.defense, tc, xb, yb)
        attrs = {"distance_m": round(math.hypot(xb - xa, yb - ya), 2), "travel_m": round(f.travel, 2),
                 "air_s": round(f.air, 3), "speed_mps": round(f.travel / max(f.air, DT), 2), "delivery": delivery,
                 "pitch": bool(P.pitch_air_min_s <= f.air <= P.pitch_air_max_s and
                               P.pitch_dist_min_m <= f.travel <= P.pitch_dist_max_m),
                 "lane_openness_m": round(lane, 2), "passer_def_m": round(dpa, 2), "receiver_def_m": round(drb, 2),
                 "advantage_pass": bool(drb >= P.open_dist_m and drb >= dpa + P.advantage_gain_m),
                 "release_xy": (round(xa, 2), round(ya, 2)), "catch_xy": (round(xb, 2), round(yb, 2)),
                 "release_spot": spot_labels(xa, ya), "catch_spot": spot_labels(xb, yb),
                 "catch_region": region(xb, yb)}
        out.append(_Pass(f, A, B, t0, tc, pc, attrs))
    return out


def _passes(scene):
    return _cache(scene, ("passes", ()), lambda: _find_passes(scene, _params("pass", {})))


def _pass_event(scene, p, kind, pc, extra, rid):
    return Event(kind, {"passer": p.a.pid, "receiver": p.b.pid}, p.t0, p.t0, p.tc,
                 _conf(pc, scene.ball, p.t0, p.t0, p.tc), dict(extra, research_id=rid))


def detect_pass(scene, **params) -> list[Event]:
    """BA-40/41: completed pass release -> flight -> teammate catch (handoffs and regathers excluded)."""
    P = _params("pass", params)
    ps = _find_passes(scene, P) if params else _passes(scene)
    return [_pass_event(scene, p, "pass", p.pc, p.attrs, "BA-40/BA-41") for p in ps]


def detect_pass_incomplete(scene, **params) -> list[Event]:
    """BA-40 incomplete: intercepted (opponent control) or thrown away (loose / out of bounds)."""
    P = _params("pass_incomplete", params)
    m = _model(scene)
    ball = scene.ball
    out = []
    for f in m.frees:
        if f.kind != "flight" or f.shot:
            continue
        A = f.prev
        if _scramble(m, A):  # changes_loop4 BA-R4f: a tip out of the rebound scramble is not a pass
            continue
        if f.nxt is not None and f.nxt.off != A.off and f.loose_s < PARAMS["touch"]["loose_min_s"]:
            lab, end = "intercepted", f.nxt.a
        else:
            oob = [t for t in range(f.a, f.b + 1) if "out_of_bounds" in region(*_xy(ball, t))]
            if oob:
                lab, end = "thrown_away_oob", oob[0]
            elif f.nxt is not None and f.loose_s >= PARAMS["touch"]["loose_min_s"] and f.nxt.off != A.off:
                # changes_loop1 BA-T3 follow-up: a loose ball recovered by the passer's own team (a deflection
                # the offence recovers) is not an incomplete pass / possession loss
                lab, end = "thrown_away_loose", f.nxt.a
            else:
                continue
        t0 = f.t_release
        bx, by = _xy(ball, t0)
        th = min(f.b, t0 + P.heading_frames)
        hv = (ball.x[th] - bx, ball.y[th] - by)
        best, ba = None, P.intended_max_angle_deg
        for o in scene.offense if A.off else scene.defense:
            if o == A.pid:
                continue
            ang = _ang(hv, (scene.kins[o].x[t0] - bx, scene.kins[o].y[t0] - by))
            if np.isfinite(ang) and ang < ba:
                best, ba = o, ang
        pc = A.conf if lab != "intercepted" else min(A.conf, f.nxt.conf)
        out.append(Event("pass_incomplete", {"passer": A.pid, "intended": best,
                                             "defender": f.nxt.pid if lab == "intercepted" else None},
                         t0, t0, end, _conf(pc, ball, t0, t0, end),
                         {"label": lab, "intended_angle_deg": None if best is None else round(ba, 1),
                          "research_id": "BA-40"}))
    return out


def detect_lob_pass(scene, **params) -> list[Event]:
    """BA-42 fixed (no z): long time of flight to a rim target, or the fast rimward-cutter proxy."""
    P = _params("lob_pass", params)
    out = []
    for p in _passes(scene):
        kb = scene.kins[p.b.pid]
        tc = p.tc
        r_c = _r(kb, tc)
        w0 = max(0, tc - _frames(P.receiver_vr_window_s))
        vr = float(np.nanmean(-kb.v_r[w0:tc + 1]))
        # changes_loop1 BA-T13: the refined release and catch sit refine_radius_m from the hands, so the
        # measured air misses refine_radius / speed at each end (-0.12 s on a 1.1 s lob to a cutter). Add it
        # back, with the closing speed of ball and receiver at the catch end.
        rr = PARAMS["touch"]["refine_radius_m"]
        vmin = PARAMS["touch"]["flight_min_speed_mps"]
        v = max(p.f.travel / max(p.f.air, DT), vmin)
        xa, ya = p.attrs["release_xy"]
        xb, yb = p.attrs["catch_xy"]
        u = np.array([xb - xa, yb - ya]) / max(math.hypot(xb - xa, yb - ya), 1e-6)
        v_close = max(vmin, v - float(kb.vx[tc] * u[0] + kb.vy[tc] * u[1])) if np.isfinite(kb.vx[tc]) else v
        air = p.f.air + rr / v + rr / v_close
        dist = p.attrs["distance_m"]
        sT = math.sqrt(2) * P.catch_jitter_frames * DT
        sv = float(np.nanmean(kb.sigma_speed[w0:tc + 1]))
        p_target = max(float(p_below(r_c, P.target_r_max_m, _sig(kb, tc))), float(p_below(vr, P.target_vr_max_mps, sv)))
        tof = air >= P.tof_min_s and dist <= P.tof_max_dist_m and (r_c < P.target_r_max_m or vr <= P.target_vr_max_mps)
        prox = r_c < P.proxy_catch_r_m and vr <= P.proxy_vr_mps and air >= P.proxy_min_air_s
        if not (tof or prox):
            continue
        if tof:
            pc = min(float(p_above(air, P.tof_min_s, sT)), p_target)
            method = "tof"
            apex = 9.81 * air * air / 8.0
        else:
            pc = min(float(p_below(vr, P.proxy_vr_mps, sv)), float(p_below(r_c, P.proxy_catch_r_m, _sig(kb, tc))),
                     float(p_above(air, P.proxy_min_air_s, sT)))
            method, apex = "proxy", None
        pc = min(pc, p.pc) * P.max_conf_xy  # multiplier (XY cannot see the arc), not a cap
        out.append(_pass_event(scene, p, "lob_pass", pc,
                               {"method": method, "apex_above_release_est_m": None if apex is None else round(apex, 2),
                                "air_corrected_s": round(air, 3),
                                "catch_r": round(r_c, 2), "receiver_v_r": round(vr, 2), "lob_to_rim": r_c < P.lob_to_rim_r_m,
                                "bounce_checked": "needs_ball_z"}, "BA-42"))
    return out


def _perimeter_between(scene, p, t, rmin, margin):
    """Perimeter teammates whose polar angle lies strictly between passer and receiver (by >= margin)."""
    xa, ya = p.attrs["release_xy"]
    xb, yb = p.attrs["catch_xy"]
    ta, tb = _theta(xa, ya), _theta(xb, yb)
    lo, hi = min(ta, tb), max(ta, tb)
    out = []
    for o in scene.offense:
        if o in (p.a.pid, p.b.pid):
            continue
        k = scene.kins[o]
        if not np.isfinite(k.x[t]) or _r(k, t) < rmin:
            continue
        th = _theta(*_xy(k, t))
        if lo + margin <= th <= hi - margin:
            out.append(o)
    return out


def detect_skip_pass(scene, **params) -> list[Event]:
    """BA-45: crosses x = 0 with |dx| > 8 m, both ends at r >= 5.5 (half-court); skip_true flag."""
    P = _params("skip_pass", params)
    out = []
    for p in _passes(scene):
        xa, ya = p.attrs["release_xy"]
        xb, yb = p.attrs["catch_xy"]
        dx = abs(xb - xa)
        ra, rb = math.hypot(xa, ya), math.hypot(xb, yb)
        if not (xa * xb < 0 and dx > P.min_dx_m and ra >= P.min_r_m and rb >= P.min_r_m
                and max(ya, yb) <= spotlib.C["HALF_Y"]):
            continue
        sk = _perimeter_between(scene, p, p.t0, P.min_r_m, P.skipped_margin_deg)
        sb = _sig(scene.ball, p.t0) * 2
        pc = min(p.pc, float(p_above(dx, P.min_dx_m, sb)), float(p_above(min(ra, rb), P.min_r_m, sb)))
        out.append(_pass_event(scene, p, "skip_pass", pc, {"dx_m": round(dx, 2), "skip_true": bool(sk),
                                                           "n_skipped": len(sk), "skipped_ids": sk}, "BA-45"))
    return out


def detect_swing_pass(scene, **params) -> list[Event]:
    """BA-47 swing: one perimeter-to-perimeter pass between adjacent players, |d theta| >= 25 deg."""
    P = _params("swing_pass", params)
    out = []
    for p in _passes(scene):
        xa, ya = p.attrs["release_xy"]
        xb, yb = p.attrs["catch_xy"]
        dth = abs(_theta(xb, yb) - _theta(xa, ya))
        if math.hypot(xa, ya) < P.min_r_m or math.hypot(xb, yb) < P.min_r_m or dth < P.min_dtheta_deg:
            continue
        if _perimeter_between(scene, p, p.t0, P.min_r_m, P.adjacent_margin_deg):
            continue
        out.append(_pass_event(scene, p, "swing_pass", p.pc, {"dtheta_deg": round(dth, 1)}, "BA-47"))
    return out


def _post_ups(scene):
    return _cache(scene, ("postups", ()), lambda: detect_post_up(scene))


def _seals(scene):
    return _cache(scene, ("seals", ()), lambda: detect_post_seal(scene))


def detect_entry_pass(scene, **params) -> list[Event]:
    """BA-46: high_low > post_entry > entry > wing_entry (labels from named spots)."""
    P = _params("entry_pass", params)
    posts = _post_ups(scene)
    seals = _seals(scene)
    ps = _passes(scene)
    drives = _drives(scene)
    special = {e.t0 for e in detect_lob_pass(scene)} | {e.t0 for e in detect_dump_off(scene)}
    out = []
    for i, p in enumerate(ps):
        xa, ya = p.attrs["release_xy"]
        xb, yb = p.attrs["catch_xy"]
        ra, rb = math.hypot(xa, ya), math.hypot(xb, yb)
        high = in_spot("high_post_strip", xa, ya) or in_spot("elbow", xa, ya)
        low = any(in_spot(s, xb, yb) for s in ("low_post", "mid_post", "deep_seal", "block_outside_lane"))
        posted = any(e.actors["post"] == p.b.pid and abs(e.t0 - p.tc) <= _frames(P.post_match_s) for e in posts)
        sealed = any(e.actors["post"] == p.b.pid and e.start <= p.tc and
                     p.tc - e.end <= _frames(P.seal_lookback_s) for e in seals)
        in_post = in_spot("post_area_rule", xb, yb) or rb < P.post_receiver_r_m
        first = all(q.a.off != p.a.off or q.t0 >= p.t0 for q in ps)
        if high and low and ya - yb >= P.high_low_dy_m:
            lab = "high_low"
        elif in_post and (posted or sealed) and ra >= P.passer_min_r_m:
            lab = "post_entry"
        elif rb < P.post_receiver_r_m:
            # changes_loop1 BA-T16: a dump-off by a driver or a lob to a cutter is not an entry pass
            if ra < P.passer_min_r_m or p.t0 in special or any(
                    d.s is p.a and d.t1 >= p.t0 - _frames(P.drive_exclusion_s) and d.t0 <= p.t0 for d in drives):
                continue
            lab = "entry"
        elif first and _m(xa, ya) >= P.wing_top_m_deg and ra >= P.wing_top_r_m and \
                P.wing_m_lo_deg <= _m(xb, yb) <= P.wing_m_hi_deg and rb >= P.wing_r_m:
            lab = "wing_entry"
        else:
            continue
        out.append(_pass_event(scene, p, "entry_pass", p.pc,
                               {"label": lab, "sealed_before": sealed, "post_up_after": posted,
                                "entry_angle_m_deg": round(_m(xa, ya), 1), "posture": "unknown_needs_pose"}, "BA-46"))
    return out


def _band_side(x, y):
    """+1 / -1 when the point is in the right / left named_spots reversal_band, else 0."""
    labs = SPOTS["reversal_band"].labels(x, y)
    return 1 if "reversal_band_right" in labs else (-1 if "reversal_band_left" in labs else 0)


def detect_ball_reversal(scene, **params) -> list[Event]:
    """BA-47 fixed: ball caught in reversal_band on one side, then on the other, via <= 2 passes in <= 4 s."""
    P = _params("ball_reversal", params)
    ps = _passes(scene)
    drives = _drives(scene)
    skips = {e.t0 for e in detect_skip_pass(scene)}
    ball = scene.ball
    out = []

    band_side = _band_side
    for s in _model(scene).segs:
        if not s.off:
            continue
        ts = s.t_catch if s.t_catch is not None else s.a
        side = band_side(*_xy(ball, ts))
        if side == 0:
            continue
        chain = [p for p in ps if p.a is s]
        if not chain:
            continue
        seq = [chain[0]]
        while len(seq) < P.max_passes:
            nxt = [p for p in ps if p.a is seq[-1].b]
            if not nxt or band_side(*seq[-1].attrs["catch_xy"]) == -side:
                break
            seq.append(nxt[0])
        for j, p in enumerate(seq):
            if band_side(*p.attrs["catch_xy"]) != -side:
                continue
            body = seq[:j + 1]
            if (p.tc - body[0].t0) * DT > P.max_s:
                break
            if any(math.hypot(*q.attrs["catch_xy"]) < P.perimeter_r_m for q in body[:-1]):
                break
            # changes_loop1 BA-T8: any drive overlapping [first passer's touch start, final catch] blocks
            if any(d.t1 >= ts and d.t0 <= p.tc and d.gain >= P.drive_gain_block_m for d in drives):
                break
            if len(body) == 1:
                via = "skip" if body[0].t0 in skips else "one_pass"
            else:
                via = "top_swing" if any(_m(*q.attrs["catch_xy"]) >= P.top_m_deg for q in body[:-1]) else "two_pass"
            pc = min(q.pc for q in body)
            out.append(Event("ball_reversal", {"first_passer": body[0].a.pid, "final_receiver": p.b.pid},
                             body[0].t0, body[0].t0, p.tc, _conf(pc, ball, body[0].t0, body[0].t0, p.tc),
                             {"via": via, "n_passes": len(body), "duration_s": round((p.tc - body[0].t0) * DT, 3),
                              "start_side": "right" if side > 0 else "left", "research_id": "BA-47"}))
            break
    return out


def detect_dribble_reversal(scene, **params) -> list[Event]:
    """BA-47 dribble_reversal: within one touch the holder carries the ball from one reversal band to the other."""
    P = _params("dribble_reversal", params)
    out = []
    for s in _model(scene).segs:
        if not s.off:
            continue
        k = scene.kins[s.pid]
        sides = np.array([_band_side(*_xy(k, t)) for t in range(s.a, s.b + 1)])
        last = {1: None, -1: None}
        for i, sd in enumerate(sides):
            if sd == 0:
                continue
            if last[-sd] is not None and (i - last[-sd]) * DT <= P.max_s:
                t0 = s.a + last[-sd]
                t1 = s.a + i
                # P from the deepest band points on each side (the crossing frames sit on the band edge)
                ia = [j for j in range(0, last[-sd] + 1) if sides[j] == -sd]
                ib = [j for j in range(i, len(sides)) if sides[j] == sd]
                ja = s.a + max(ia, key=lambda j: abs(k.x[s.a + j]))
                jb = s.a + max(ib, key=lambda j: abs(k.x[s.a + j]))
                probs = _sample_probs(lambda a_, b_, c_, d_: _band_side(a_, b_) * _band_side(c_, d_),
                                      [_xy(k, ja), _xy(k, jb)], [_sig(k, ja), _sig(k, jb)], P.samples)
                pc = min(probs.get(-1, 0.0), s.conf)
                out.append(Event("dribble_reversal", {"handler": s.pid}, t0, t0, t1, _conf(pc, k, t0, t0, t1),
                                 {"start_side": "right" if sd < 0 else "left", "research_id": "BA-47"}))
                break
            last[sd] = i
    return out


def detect_kick_out(scene, **params) -> list[Event]:
    """BA-48/66 fixed: pass from a drive (or post-up) to a receiver at the arc (three) or mid-range (mid)."""
    P = _params("kick_out", params)
    drives = _drives(scene)
    posts = _post_ups(scene)
    out = []
    for p in _passes(scene):
        src = None
        for d in drives:
            if d.s is p.a and d.t0 <= p.t0 <= d.t1 + _frames(P.window_after_s):
                src = "drive"
        for e in posts:
            if e.actors["post"] == p.a.pid and e.start <= p.t0 <= e.end + _frames(P.window_after_s):
                src = src or "post"
        if src is None:
            continue
        xa, ya = p.attrs["release_xy"]
        xb, yb = p.attrs["catch_xy"]
        if src == "drive" and math.hypot(xa, ya) > P.passer_max_r_m:
            continue
        d3 = coord("d3", xb, yb)
        rb = math.hypot(xb, yb)
        kb = scene.kins[p.b.pid]
        if d3 >= P.three_d3_min_m:
            sub = "three"
            pc = min(p.pc, float(p_above(d3, P.three_d3_min_m, _sig(kb, p.tc))))
        elif rb >= P.mid_r_min_m and src == "drive":
            sub = "mid"
            pc = min(p.pc, float(p_above(rb, P.mid_r_min_m, _sig(kb, p.tc))),
                     float(p_below(d3, P.three_d3_min_m, _sig(kb, p.tc))))
        else:
            continue
        rd = p.attrs["receiver_def_m"]
        out.append(_pass_event(scene, p, "kick_out", pc,
                               {"subtype": sub, "source": src, "corner": in_spot("corner_three", xb, yb),
                                "receiver_d3": round(d3, 2), "receiver_def_m": rd,
                                "open": bool(rd >= P.open_dist_m)}, "BA-48"))
    return out


def detect_dump_off(scene, **params) -> list[Event]:
    """BA-49: pass during or <= 1.0 s after a drive to an interior receiver (r < 2.5 or a dunker spot)."""
    P = _params("dump_off", params)
    drives = _drives(scene)
    out = []
    for p in _passes(scene):
        if not any(d.s is p.a and d.t0 <= p.t0 <= d.t1 + _frames(P.window_after_s) for d in drives):
            continue
        xa, ya = p.attrs["release_xy"]
        xb, yb = p.attrs["catch_xy"]
        if math.hypot(xa, ya) > P.passer_max_r_m:
            continue
        rb = math.hypot(xb, yb)
        dunker = any(in_spot(s, xb, yb) for s in ("dunker_spot", "baseline_dunker", "upper_dunker"))
        if not (rb < P.receiver_r_max_m or dunker):
            continue
        kb = scene.kins[p.b.pid]
        t1 = max(0, p.tc - _frames(P.origin_lookback_s))
        pc = min(p.pc, max(float(p_below(rb, P.receiver_r_max_m, _sig(kb, p.tc))), 1.0 if dunker else 0.0))
        out.append(_pass_event(scene, p, "dump_off", pc, {"catch_r": round(rb, 2), "dunker_spot": dunker,
                                                          "receiver_origin_spot": spot_labels(*_xy(kb, t1))},
                               "BA-49"))
    return out


# --------------------------------------------------------------------------------------
# L2: shots (XY proxies)
# --------------------------------------------------------------------------------------
@dataclass
class _Shot:
    f: Free
    s: Ctl
    t0: int
    rim_frame: int
    pc: float
    attrs: dict


def _find_shots(scene, S):
    m = _model(scene)
    out = []
    for f, (is_shot, rim_t, crit, airball) in zip(m.frees, _shot_scan(scene, m, S)):
        if not is_shot:
            continue
        s = f.prev
        k = scene.kins[s.pid]
        t0 = f.t_release
        x, y = _xy(k, t0)
        xa, ya = _att(scene, s.off, x, y)  # changes_loop4 BA-R4a: the shooter's own basket frame
        tA = s.t_catch if s.t_catch is not None else s.a
        dr = _dribbled(scene, s)
        gather = dr[2] if dr is not None else tA
        others = scene.defense if s.off else scene.offense
        dn, dd = _nearest(scene, others, t0, x, y)
        clos = float("nan")
        if dn is not None:
            c0 = max(0, t0 - _frames(S.closing_window_s))
            clos = float(np.nanmean(mv.closing_speed(k, scene.kins[dn])[c0:t0 + 1]))
        pc = min([c["p"] for c in crit.values()] + [s.conf])
        attrs = {"airball": bool(airball), "release_r": round(math.hypot(xa, ya), 2),
                 "three": bool(spotlib.is_three(xa, ya)), "spot": spot_labels(xa, ya), "court_region": region(xa, ya),
                 "basket": "origin" if _rim(scene, s.off)[1] == 0.0 else "far", "gather_frame": int(gather),
                 "touch_time_before_s": round((t0 - tA) * DT, 3), "touch_start": _start_kind(scene, m, s),
                 "dribble_inferred": dr is not None, "dribbles_before": "unknown_needs_ball_z",
                 "speed_at_gather": round(float(k.speed[gather]), 2), "speed_at_release": round(float(k.speed[t0]), 2),
                 "nearest_def_m": round(dd, 2), "def_closing_mps": round(clos, 2), "criteria": crit,
                 "made": "needs_pbp_or_ball_z"}
        if airball:
            pa = min(crit["direction"]["p"], crit["rim_reach"]["p"])
            attrs["alternatives"] = {"shot_airball": round(pa, 3), "pass_intercepted": round(1 - pa, 3)}
        out.append(_Shot(f, s, t0, rim_t, pc, attrs))
    return out


def _shots(scene):
    return _cache(scene, ("shotlist", ()), lambda: _find_shots(scene, _params("shot_release", {})))


def detect_shot_release(scene, **params) -> list[Event]:
    """BA-80 XY proxy: release with the ball heading at the rim (<= 15 deg) and reaching r <= 0.75 m."""
    S = _params("shot_release", params)
    shots = _find_shots(scene, S) if params else _shots(scene)
    return [Event("shot_release", {"shooter": sh.s.pid}, sh.t0, sh.t0, sh.rim_frame,
                  _conf(sh.pc, scene.kins[sh.s.pid], sh.t0, sh.s.a, sh.t0), dict(sh.attrs, research_id="BA-80"))
            for sh in shots]


def detect_catch_and_shoot(scene, **params) -> list[Event]:
    """BA-81 proxy: jump shot (r > 3.048) after a catch, no inferred dribble, catch-to-release <= 2.0 s."""
    P = _params("catch_and_shoot", params)
    out = []
    for sh in _shots(scene):
        a = sh.attrs
        if a["release_r"] <= P.min_r_m or a["dribble_inferred"] or a["touch_start"] not in ("pass", "handoff"):
            continue
        tt = a["touch_time_before_s"]
        if tt > P.max_touch_s:
            continue
        p_hidden = P.p_hidden_dribble_short if tt <= P.short_touch_s else P.p_hidden_dribble_long
        k = scene.kins[sh.s.pid]
        tc = sh.s.t_catch if sh.s.t_catch is not None else sh.s.a
        sp = float(np.nanmean(k.speed[tc:min(sh.t0, tc + _frames(P.catch_speed_window_s)) + 1]))
        pc = min(sh.pc, float(phi((P.max_touch_s - tt) / (2 * DT)))) * (1 - p_hidden)
        out.append(Event("catch_and_shoot", {"shooter": sh.s.pid}, sh.t0, tc, sh.t0,
                         _conf(pc, k, sh.t0, tc, sh.t0),
                         {"cs_set": sp <= P.set_speed_mps, "cs_on_move": sp >= P.move_speed_mps,
                          "one_motion": tt <= P.one_motion_s, "catch_speed_mps": round(sp, 2),
                          "touch_time_s": tt, "three": a["three"],
                          "alternatives": {"catch_and_shoot": round(1 - p_hidden, 3), "pull_up": round(p_hidden, 3)},
                          "research_id": "BA-81"}))
    return out


def detect_pull_up(scene, **params) -> list[Event]:
    """BA-82 proxy: jump shot (r > 3.048) in a touch with an inferred dribble (>= 1 dribble certain)."""
    P = _params("pull_up", params)
    out = []
    for sh in _shots(scene):
        a = sh.attrs
        if a["release_r"] <= P.min_r_m or not a["dribble_inferred"]:
            continue
        dr = _dribbled(scene, sh.s)
        k = scene.kins[sh.s.pid]
        pc = min(sh.pc, dr[4])
        out.append(Event("pull_up", {"shooter": sh.s.pid}, sh.t0, dr[0], sh.t0, _conf(pc, k, sh.t0, dr[0], sh.t0),
                         {"on_move": a["speed_at_gather"] >= P.on_move_speed_mps, "three": a["three"],
                          "touch_time_s": a["touch_time_before_s"], "research_id": "BA-82"}))
    return out


def detect_held_jumper(scene, **params) -> list[Event]:
    """BA-91 proxy: jump shot with no inferred dribble after > 2.0 s of holding (stationary dribble not excluded)."""
    P = _params("held_jumper", params)
    out = []
    for sh in _shots(scene):
        a = sh.attrs
        if a["release_r"] <= P.min_r_m or a["dribble_inferred"] or a["touch_time_before_s"] <= P.max_touch_cs_s:
            continue
        k = scene.kins[sh.s.pid]
        pc = sh.pc * (1 - P.p_hidden_dribble)
        out.append(Event("held_jumper", {"shooter": sh.s.pid}, sh.t0, sh.s.a, sh.t0, _conf(pc, k, sh.t0, sh.s.a, sh.t0),
                         {"touch_time_s": a["touch_time_before_s"], "jab": "needs_pose",
                          "alternatives": {"held_jumper": round(1 - P.p_hidden_dribble, 3),
                                           "pull_up_stationary_dribble": round(P.p_hidden_dribble, 3)},
                          "research_id": "BA-91"}))
    return out


def detect_rebound_control(scene, **params) -> list[Event]:
    """New (checker missing item): first control after a shot flight -> offensive / defensive rebound."""
    P = _params("rebound_control", params)
    m = _model(scene)
    out = []
    for f in m.frees:
        if not f.shot or f.nxt is None or (f.nxt.a - f.prev.b) * DT > P.max_after_shot_s:
            continue
        s = f.nxt
        k = scene.kins[s.pid]
        t0 = s.t_catch if s.t_catch is not None else s.a
        lab = "offensive" if s.off == f.prev.off else "defensive"
        out.append(Event("rebound", {"rebounder": s.pid, "shooter": f.prev.pid}, t0, s.a, s.b,
                         _conf(s.conf, k, t0, s.a, s.b),
                         {"label": lab, "r": round(_r(k, s.a), 2), "tip": "needs_ball_z",
                          "research_id": "missing:rebound"}))
    return out


def _scramble(m, seg, P=None):
    """changes_loop4 BA-R4f: `seg` is a rebound-scramble touch (a tip, a bobble, a hand on the ball under the rim),
    not an established possession: it starts <= rebound_control.scramble_window_s after the rim frame of the last
    shot before it and lasts < rebound_control.secure_min_s."""
    P = P or PARAMS["rebound_control"]
    rim = None
    for f in m.frees:
        if f.a > seg.a:
            break
        if f.shot and f.rim_frame is not None and f.rim_frame <= seg.a:
            rim = f.rim_frame
    return rim is not None and (seg.a - rim) * DT <= P["scramble_window_s"] and (seg.b - seg.a) * DT < P["secure_min_s"]


# --------------------------------------------------------------------------------------
# L3: turnovers under the NCAA official-statistics rules (changes_loop5; rule ba_turnover_rules)
# --------------------------------------------------------------------------------------
@dataclass
class _TO:
    """One possible turnover: control of team A (seg L) followed by control of team B (seg G)."""
    f: Free
    L: Ctl  # last control of the losing team
    G: Ctl  # first control of the gaining team (the deflector's touch when a teammate secures the ball)
    S: Ctl  # the gaining team's securing control (G, or the recoverer's after a deflection)
    decision: str  # turnover | abstain | no_turnover
    reason: str
    label: str = ""
    deflector: str | None = None
    steal_to: str | None = None
    steal_basis: str = ""
    charged_to: str | None = None
    charged_basis: str = ""
    alt_charged: str | None = None
    throw_in: bool = False
    merged: list = field(default_factory=list)


def _rim_min(scene, a, b, rims=(True, False)):
    """(frame, distance) of the ball's closest XY approach over frames [a, b] to the listed team baskets."""
    ball = scene.ball
    a, b = max(0, int(a)), min(scene.n - 1, int(b))
    best = (None, float("inf"))
    if b < a:
        return best
    for o in rims:
        r = _rim_dist(scene, o, ball.x[a:b + 1], ball.y[a:b + 1])
        if np.any(np.isfinite(r)):
            j = int(np.nanargmin(r))
            if float(r[j]) < best[1]:
                best = (a + j, float(r[j]))
    return best


def _rim_scramble(scene, m, seg, P):
    """changes_loop5 TO-C1 (control gate, losing side): `seg` is a rebound-battle touch, not team control, when it
    lasts < rebound_control.secure_min_s and starts <= rebound_control.scramble_window_s after a shot's rim frame
    (BA-R4f) or after an XY rim visit (ball within rim_visit_r_m of either basket: a try the shot proxy missed;
    floor-only ball, no z)."""
    R = PARAMS["rebound_control"]
    if (seg.b - seg.a) * DT >= R["secure_min_s"]:
        return None
    if _scramble(m, seg):
        return "shot"
    t, r = _rim_min(scene, seg.a - _frames(R["scramble_window_s"]), seg.a + _frames(P.rim_visit_pad_s))
    return "rim_visit" if t is not None and r <= P.rim_visit_r_m else None


def _next_seg(m, s):
    for j, x in enumerate(m.segs):
        if x is s:
            return m.segs[j + 1] if j + 1 < len(m.segs) else None
    return None


def _team_of(scene, pid):
    return pid in scene.offense


def _touches_between(scene, m, team_off, a, b):
    """Opponent touches inside a free interval: taps (< min_touch_s) and contact segments the decode dropped,
    by players of team `team_off`, overlapping frames [a, b]; earliest first."""
    out = [(c.a, c.pid) for c in m.taps if c.off == team_off and c.b >= a and c.a <= b]
    out += [(qa, pid) for pid, qa, qb in m.contacts if _team_of(scene, pid) == team_off and qb >= a and qa <= b]
    return [pid for _, pid in sorted(out)]


def _slight_tip(scene, a, b, P):
    """A deflection over frames [a, b] is a slight tip when the ball keeps flight speed through it and its heading
    turns by <= tip_max_turn_deg (SM 6 A.R.5(b)); else it is a clean deflection (A.R.5(a))."""
    ball = scene.ball
    n = scene.n
    a0, b0 = max(1, a - 3), min(n - 2, b + 3)
    sp = ball.speed[a:b + 1]
    if not np.any(np.isfinite(sp)) or float(np.nanmin(sp)) < PARAMS["touch"]["flight_min_speed_mps"]:
        return False
    u = (ball.x[a] - ball.x[a0], ball.y[a] - ball.y[a0])
    v = (ball.x[b0] - ball.x[b], ball.y[b0] - ball.y[b])
    turn = _ang(u, v)
    return bool(np.isfinite(turn) and turn <= P.tip_max_turn_deg)


def _initiated(scene, pid, t_rel, t_cat, P):
    """The interceptor moved to the ball (SM 6(e), A.R.4(a)/(c)): his displacement over [t_rel -
    intercept_move_window_s, t_cat] is >= intercept_move_min_m. A defender the pass reaches standing still got an
    errant pass (A.R.4(b): turnover, no steal)."""
    k = scene.kins[pid]
    a = max(0, t_rel - _frames(P.intercept_move_window_s))
    if not (np.isfinite(k.x[a]) and np.isfinite(k.x[t_cat])):
        return True  # doubt: credit the defender
    return math.hypot(k.x[t_cat] - k.x[a], k.y[t_cat] - k.y[a]) >= P.intercept_move_min_m


def _knocked_loose(scene, L, f, team_off, P):
    """A gaining-team player within knock_reach_m of the ball around the refined release (+- knock_window_s): the ball was
    knocked loose (SM 6(c)/(d)), he is the deflector; else the fumble was unforced (A.R.7: no steal)."""
    ball = scene.ball
    w = _frames(P.knock_window_s)
    t_rel = f.t_release if f.t_release is not None else L.b  # the refined release (L.b is 1.5 m out)
    best, bd = None, float("inf")
    for t in range(max(0, t_rel - w), min(scene.n - 1, t_rel + w) + 1):
        if not np.isfinite(ball.x[t]):
            continue
        o, d = _nearest(scene, scene.offense if team_off else scene.defense, t, *_xy(ball, t))
        if o is not None and d < bd:
            best, bd = o, d
    return best if bd <= P.knock_reach_m else None


def _merge_duplicates(recs, window_s):
    """TO-M1 (Aldemir R7): two counted records (turnover or abstention) in the same direction within window_s are
    one loss seen twice (the change back between them was not counted): keep one, preferring a decided turnover
    over an abstention, and list the other's t0 in .merged."""
    keep = []
    for to in recs:
        prev = next((x for x in reversed(keep) if x.decision != "no_turnover"), None)
        if to.decision != "no_turnover" and prev is not None and prev.L.off == to.L.off and \
                (to.G.a - prev.G.a) * DT <= window_s:
            if prev.decision == "abstain" and to.decision == "turnover":
                keep[keep.index(prev)] = to
                to.merged.append(int(prev.G.a))
            else:
                prev.merged.append(int(to.G.a))
            continue
        keep.append(to)
    return keep


def _turnovers(scene, **ov):
    """Every change of control between the teams, classified by the NCAA turnover rules (cached)."""
    P = _params("live_ball_turnover", ov)

    def build():
        m = _model(scene)
        ball = scene.ball
        clock = getattr(scene, "game_clock", None)
        out = []
        for f in m.frees:
            L, G = f.prev, f.nxt
            if G is None or G.off == L.off:
                continue
            to = _TO(f, L, G, G, "turnover", "")
            if f.shot:  # a try: the opponent's control is a rebound (SM 3), never a turnover
                continue
            # throw-in: the releaser stands out of bounds (SM 4 A.R.17(a): an intercepted throw-in is a turnover)
            to.throw_in = bool(np.isfinite(scene.kins[L.pid].x[L.b]) and
                               "out_of_bounds" in region(*_xy(scene.kins[L.pid], L.b)))
            # TO-C1 control gate, losing side: a rebound-battle touch is not team control
            why = _rim_scramble(scene, m, L, P)
            if why == "shot":
                continue  # BA-R4f: a decided rebound battle (the shot proxy saw the try)
            if why == "rim_visit":
                to.decision, to.reason = "abstain", "rim_visit_scramble"
            if f.kind == "unknown":
                to.decision, to.reason = "abstain", "gap"
            # TO-D1: the ball passes over a basket between the loss and the gain: a try the proxy missed (rebound)
            # or a pass off the rim (turnover); XY cannot tell them apart without ball z
            t_v, r_v = _rim_min(scene, L.b - _frames(P.rim_visit_pad_s), G.a + _frames(P.rim_visit_pad_s))
            if to.decision == "turnover" and not to.throw_in and t_v is not None and r_v <= P.rim_visit_r_m:
                to.decision, to.reason = "abstain", "rim_visit"
            # deflection: the first gaining-team touch is short and a teammate secures the ball
            nx = _next_seg(m, G)
            defl, tip = None, False
            fg = _free_after(m, G)
            short = (G.b - G.a) * DT < P.deflect_touch_max_s and nx is not None and nx.off == G.off \
                and nx.pid != G.pid and (nx.a - G.b) * DT <= P.deflect_recover_max_s and fg is not None
            # a bat (the ball goes on loose) or a slight tip (it keeps flight speed and line) is a deflection; a short
            # touch followed by a pass is a catch and a quick pass (doubt = control, SM B.I.4): he secured it
            if short and (fg.kind in ("loose", "exchange") or fg.loose_s >= PARAMS["touch"]["loose_min_s"]
                          or _slight_tip(scene, G.a, G.b, P)):
                defl, to.S = G.pid, nx
                tip = _slight_tip(scene, G.a, G.b, P)
            else:
                taps = [p for p in _touches_between(scene, m, G.off, L.b - 2, G.a - 1) if p != G.pid]
                if taps:
                    defl = taps[0]
                    tip = f.kind == "flight" and f.loose_s < PARAMS["touch"]["loose_min_s"]
            S = to.S
            # TO-C2 control gate, gaining side: the opponent must secure control before the ball goes dead
            ns = _next_seg(m, S)
            fs = _free_after(m, S)
            if to.decision == "turnover" and (S.b - S.a) * DT < P.gain_secure_min_s and \
                    (ns is None or (fs is not None and fs.kind == "unknown")):
                to.decision, to.reason = "abstain", "dead_before_secured"
            # TO-E1: end of period (SM 4 Art.1 exception): the gain comes with the game clock expired
            if clock is not None and np.isfinite(clock[S.a]) and clock[S.a] <= P.period_end_eps_s:
                to.decision, to.reason = "no_turnover", "end_of_period"
            # label and steal credit (SM 6)
            if f.kind == "exchange":
                to.label = "strip"
            elif f.kind == "flight" and f.loose_s < PARAMS["touch"]["loose_min_s"]:
                to.label = "interception"
            else:
                to.label = "loose_recovery"
            if defl is not None and defl != S.pid:
                to.label = "deflection"
                to.deflector = defl
                if tip:  # slight tip, the recoverer intercepts (A.R.5(b))
                    to.steal_to, to.steal_basis = S.pid, "recoverer_after_slight_tip"
                else:  # clean deflection, or doubt (A.R.5(a), A.R.5(c) tie-break)
                    to.steal_to, to.steal_basis = defl, "deflector"
            elif to.label == "strip":
                to.deflector = defl
                to.steal_to, to.steal_basis = S.pid, "take_away"
            elif to.label == "interception":
                to.deflector = defl
                if defl == S.pid or _initiated(scene, S.pid, f.t_release or L.b, S.t_catch or S.a, P):
                    to.steal_to, to.steal_basis = S.pid, "interception"
                else:
                    to.steal_basis = "errant_pass_no_steal"
            else:  # loose ball: knocked loose by a defender, or an unforced fumble
                k = defl or _knocked_loose(scene, L, f, G.off, P)
                to.deflector = k
                if k is not None:
                    to.steal_to, to.steal_basis = k, "knocked_loose"
                else:
                    to.steal_basis = "unforced_no_steal"
            # charged player (SM 4 Art.1, A.R.4(d)/(e)): the last controller; a receiver who loses a teammate's pass
            # loose within muff_max_s of the catch (refined catch to refined release: the ball in his hands; the
            # segment also holds the roll out of his 1.5 m radius) muffed it: charged to him, passer as the alternative
            to.charged_to, to.charged_basis = L.pid, "last_control"
            fb = _free_before(m, L)
            hands = ((f.t_release if f.t_release is not None else L.b) - (L.t_catch if L.t_catch is not None else L.a)) * DT
            lost_loose = f.kind == "loose" or f.loose_s >= PARAMS["touch"]["loose_min_s"]
            if fb is not None and fb.prev is not None and fb.prev.off == L.off and fb.prev.pid != L.pid \
                    and fb.kind in ("flight", "exchange") and lost_loose and hands < P.muff_max_s:
                to.charged_basis, to.alt_charged = "receiver_muff", fb.prev.pid
            out.append(to)
        return _merge_duplicates(out, P.dedupe_window_s)
    return _cache(scene, _key("turnovers", ov), build)


def _to_event(scene, to, kind):
    s = to.S
    pc = min(s.conf, to.L.conf)
    clock = getattr(scene, "game_clock", None)
    attrs = {"label": to.label, "live": True, "deflector": to.deflector, "recoverer": s.pid,
             "steal_to": to.steal_to, "steal_basis": to.steal_basis, "charged_to": to.charged_to,
             "charged_basis": to.charged_basis, "alt_charged": to.alt_charged, "throw_in": to.throw_in,
             "secured_t": int(s.a), "merged_t0": to.merged,
             "period_end_check": "ok" if clock is not None else "needs_game_clock",
             "pbp_check": "steal/turnover rows within 2.0 s", "research_id": "missing:turnover"}
    actors = {"lost_by": to.L.pid, "gained_by": s.pid}
    if kind == "turnover_abstention":
        attrs["reason"] = to.reason
        attrs["resolve_with"] = {"rim_visit": "ball_z_or_pbp", "rim_visit_scramble": "ball_z_or_pbp",
                                 "gap": "pbp", "dead_before_secured": "pbp"}.get(to.reason, "pbp")
    return Event(kind, actors, to.G.a, to.L.b, s.b, _conf(pc, scene.ball, to.G.a, to.L.b, s.b), attrs)


def detect_live_ball_turnover(scene, **params) -> list[Event]:
    """Live-ball turnover under the NCAA rules (changes_loop5): the losing team had control (TO-C1), the
    gaining team secured it (TO-C2), no try (shot proxy; an XY rim visit abstains), not at an expired clock
    (TO-E1); duplicates merged (TO-M1). Steal credit and charged player in attrs (SM 4, SM 6)."""
    return [_to_event(scene, t, "live_ball_turnover") for t in _turnovers(scene, **params) if t.decision == "turnover"]


def detect_turnover_abstention(scene, **params) -> list[Event]:
    """Possible turnovers tracking cannot decide (rim visit: try or pass; rebound battle after a rim visit; a gap;
    the ball dead before the gainer secured it; a held ball whose arrow decides). Shares the live_ball_turnover
    params; resolved by ball z or PBP (reconcile_turnovers)."""
    P = _params("live_ball_turnover", params)
    out = [_to_event(scene, t, "turnover_abstention") for t in _turnovers(scene, **params) if t.decision == "abstain"]
    # TO-H1 held ball: a tie-up of a player in control; the alternating-possession arrow (PBP) decides the
    # turnover (arrow to the defence: turnover to the tied-up player, steal to the tying defender, SM 4 A.R.10)
    m = _model(scene)
    for e in detect_contested_ball(scene):
        if not e.attrs.get("held_ball_candidate"):
            continue
        a = int(e.start)
        prior = next((s for s in reversed(m.segs) if s.a < a and s.b >= a - _frames(P.held_prior_max_gap_s)), None)
        # player control before the tie-up: a segment that reaches the tie-up and began >= held_prior_min_s before
        # it (a segment that starts with the tie-up is the tie-up itself, e.g. two players reaching a rebound)
        if prior is None or prior.pid not in (e.actors.get("offense"), e.actors.get("defense")) \
                or (a - prior.a) * DT < P.held_prior_min_s or _rim_scramble(scene, m, prior, P) is not None:
            continue  # no player control before the tie-up (rebound / loose ball): no turnover either way
        tier = e.actors["defense"] if prior.off else e.actors["offense"]
        out.append(Event("turnover_abstention", {"lost_by": prior.pid, "gained_by": tier}, a, a, int(e.end), e.conf,
                         {"label": "held_ball", "reason": "held_ball_arrow", "resolve_with": "pbp_arrow",
                          "charged_to": prior.pid, "steal_to": tier, "steal_basis": "tying_defender_if_arrow_to_defence",
                          "live": False, "research_id": "missing:turnover"}))
    return sorted(out, key=lambda e: e.t0)


def reconcile_turnovers(scene, rows, **ov) -> dict:
    """PBP reconciliation hook (rule ba_turnover_rules): applies the NCAA rules tracking cannot see to the tracking
    turnovers and abstentions of one clip. `rows`: PBP rows aligned to the clip (t = seconds from the clip start),
    each {t, type: turnover | foul | held_ball | review | period_end, team: offense | defense (the scene lists),
    player, ...}; turnover rows may carry turnover_type, fouler, live; foul rows offensive (bool) and
    forced_by_pass; held_ball rows arrow_team, tying_player; review rows outcome (overturned | upheld).
    Returns {'turnovers': final records, 'dropped': [(record or row, rule)]}."""
    R = _params("ba_turnover_rules", ov)
    tos = detect_live_ball_turnover(scene)
    abst = detect_turnover_abstention(scene)
    m = _model(scene)
    rows = sorted(rows, key=lambda r: r["t"])
    team = lambda pid: "offense" if pid in scene.offense else "defense"  # noqa: E731
    dropped = []
    reviews = [r for r in rows if r["type"] == "review" and r.get("outcome") == "overturned"]

    def overturned(t):  # TO-R1 final ruling: an event a review overturns does not count
        return any(0.0 <= rv["t"] - t <= R.review_window_s for rv in reviews)
    pbp = []
    for r in (r for r in rows if r["type"] == "turnover"):
        if overturned(r["t"]):
            dropped.append((r, "final_ruling_overturned"))
        elif pbp and pbp[-1]["team"] == r["team"] and r["t"] - pbp[-1]["t"] <= R.dup_window_s:
            dropped.append((r, "duplicate"))  # TO-M1: the same turnover logged twice
        else:
            pbp.append(dict(r))
    fouls = [r for r in rows if r["type"] == "foul" and r.get("offensive")]
    pend = next((r["t"] for r in rows if r["type"] == "period_end"), None)
    final, used = [], set()
    for e in tos:
        t = e.t0 * DT
        if overturned(t):
            dropped.append((e, "final_ruling_overturned"))
            continue
        j = min((i for i, r in enumerate(pbp) if i not in used and abs(r["t"] - t) <= R.match_window_s
                 and r["team"] == team(e.actors["lost_by"])), key=lambda i: abs(pbp[i]["t"] - t), default=None)
        if j is not None:
            used.add(j)
        final.append({"t": round(t, 3), "team": team(e.actors["lost_by"]), "charged_to": e.attrs["charged_to"],
                      "steal_to": e.attrs["steal_to"], "deflector": e.attrs["deflector"],
                      "recoverer": e.attrs["recoverer"], "live": True, "fouler": None,
                      "source": "both" if j is not None else "tracking", "rule": e.attrs["steal_basis"]})
    for i, r in enumerate(pbp):
        if i in used:
            continue
        rec = {"t": r["t"], "team": r["team"], "charged_to": r.get("player"), "steal_to": r.get("stealer"),
               "deflector": None, "recoverer": None, "live": bool(r.get("live", False)), "fouler": None,
               "source": "pbp", "rule": r.get("turnover_type", "")}
        ab = min((a for a in abst if abs(a.t0 * DT - r["t"]) <= R.match_window_s
                  and team(a.actors["lost_by"]) == r["team"]), key=lambda a: abs(a.t0 * DT - r["t"]), default=None)
        if ab is not None and ab.attrs["reason"] != "held_ball_arrow":
            rec.update(charged_to=ab.attrs["charged_to"], steal_to=ab.attrs["steal_to"],
                       deflector=ab.attrs.get("deflector"), recoverer=ab.attrs.get("recoverer"),
                       live=ab.attrs["reason"] != "dead_before_secured", source="abstention+pbp")
        fl = next((x for x in fouls if abs(x["t"] - r["t"]) <= R.foul_link_s), None)
        if r.get("turnover_type") == "offensive_foul" or fl is not None:
            # TO-F1: an offensive foul is a turnover charged to the fouler, also off the ball (SM 4 A.R.19(e)/(f));
            # a pass that forces the receiver into the charge is charged to the passer (A.R.21); no steal (6 A.R.9)
            fouler = (fl or {}).get("player") or r.get("fouler") or r.get("player")
            rec.update(fouler=fouler, charged_to=fouler, steal_to=None, live=False, rule="offensive_foul")
            k = int(round(r["t"] / DT))
            seg = next((s for s in m.segs if s.pid == fouler and s.a <= k + _frames(R.foul_link_s)
                        and k - _frames(R.pass_forced_charge_s) <= s.a), None)
            fb = _free_before(m, seg) if seg is not None else None
            passer = r.get("passer") or (fb.prev.pid if fb is not None and fb.prev is not None
                                         and fb.prev.off == seg.off and fb.kind == "flight" else None)
            if (fl or r).get("forced_by_pass") and passer is not None:
                rec.update(charged_to=passer, rule="pass_forced_charge")
            elif passer is not None:
                rec["needs_review"] = "pass_forced_charge?"  # a catch just before the charge: judgment call
                rec["passer"] = passer
        if pend is not None and r["t"] >= pend - R.period_end_eps_s and rec["source"] == "pbp" \
                and rec["rule"] != "offensive_foul":
            dropped.append((rec, "end_of_period"))  # TO-E1: the clock expired with the team in control
            continue
        final.append(rec)
    for h in (r for r in rows if r["type"] == "held_ball"):
        # TO-H1: held ball with player control: arrow to the opponent = turnover + steal to the tying defender;
        # arrow to the controlling team = nothing (SM 4 A.R.10); no prior control (rebound) = no turnover (3 A.R.1)
        ab = min((a for a in abst if a.attrs["reason"] == "held_ball_arrow" and
                  abs(a.t0 * DT - h["t"]) <= R.match_window_s), key=lambda a: abs(a.t0 * DT - h["t"]), default=None)
        if ab is None:
            dropped.append((h, "held_ball_without_control"))
            continue
        lost = team(ab.actors["lost_by"])
        if h.get("arrow_team") == lost or h.get("arrow_team") is None:
            dropped.append((h, "held_ball_arrow_to_controlling_team" if h.get("arrow_team") else "held_ball_no_arrow"))
            continue
        final.append({"t": round(ab.t0 * DT, 3), "team": lost, "charged_to": h.get("player") or ab.actors["lost_by"],
                      "steal_to": h.get("tying_player") or ab.actors["gained_by"], "deflector": None,
                      "recoverer": None, "live": False, "fouler": None, "source": "abstention+pbp",
                      "rule": "held_ball_arrow_to_defence"})
    return {"turnovers": sorted(final, key=lambda x: x["t"]), "dropped": dropped}


# --------------------------------------------------------------------------------------
# L3: drive outcome, assists, outlet
# --------------------------------------------------------------------------------------
def detect_drive_outcome(scene, **params) -> list[Event]:
    """BA-36 (window unified to 1.0 s): first event after the drive end -> shot / kick_out / dump_off / ..."""
    P = _params("drive_outcome", params)
    m = _model(scene)
    kicks = detect_kick_out(scene)
    dumps = detect_dump_off(scene)
    shots = _shots(scene)
    passes = _passes(scene)
    w = _frames(P.window_s)
    out = []
    for d in _drives(scene):
        k = scene.kins[d.s.pid]
        lab, t_res = None, None
        for sh in shots:
            if sh.s is d.s and d.t0 <= sh.t0 <= d.t1 + w:
                lab, t_res = "shot", sh.t0
        if lab is None:
            for e, name in [(e, "kick_out_pass") for e in kicks] + [(e, "dump_off_pass") for e in dumps]:
                if e.actors["passer"] == d.s.pid and d.t0 <= e.t0 <= d.t1 + w:
                    lab, t_res = name, e.t0
        if lab is None:
            for p in passes:
                if p.a is d.s and d.t0 <= p.t0 <= d.t1 + w:
                    lab, t_res = "other_pass", p.t0
        if lab is None:
            f = _free_after(m, d.s)
            if f is not None and f.nxt is not None and f.nxt.off != d.s.off and f.prev.b <= d.t1 + w:
                lab, t_res = "turnover", f.nxt.a
        if lab is None:
            hi = min(d.s.b, d.t1 + w)
            if np.nanmax(k.r[d.t1:hi + 1]) >= P.reset_r_m:
                lab, t_res = "reset", hi
            elif d.t1 + w > d.s.b and _free_after(m, d.s) is None:
                lab = "unresolved_clip_end"
            else:
                lab = "continue"
        out.append(Event("drive_outcome", {"driver": d.s.pid}, d.te, d.t0, t_res or d.t1,
                         _conf(d.pc, k, d.te, d.t0, d.t1),
                         {"label": lab, "foul_drawn": "needs_pbp", "research_id": "BA-36"}))
    return out


def detect_potential_assist(scene, **params) -> list[Event]:
    """BA-51 potential assist: completed pass whose receiver shoots <= 2.0 s after the catch (dribbles unknown)."""
    P = _params("potential_assist", params)
    out = []
    for sh in _shots(scene):
        for p in _passes(scene):
            if p.b is not sh.s:
                continue
            dt = (sh.t0 - p.tc) * DT
            if dt > P.max_catch_to_shot_s:
                continue
            pc = min(p.pc, sh.pc, float(phi((P.max_catch_to_shot_s - dt) / (2 * DT))))
            if sh.attrs["dribble_inferred"]:
                # changes_loop1 BA-T17: travel beyond one dribble's reach needs >= 2 dribbles (NBA: <= 1)
                dr = _dribbled(scene, sh.s)
                if dr is not None and dr[3] > P.max_one_dribble_travel_m:
                    continue
                pc *= P.p_le_one_dribble_if_dribbled
            out.append(_pass_event(scene, p, "potential_assist", pc,
                                   {"shooter": sh.s.pid, "catch_to_shot_s": round(dt, 3),
                                    "dribbles": "unknown_needs_ball_z", "assist": "needs_pbp_made_fg"}, "BA-51"))
    return out


def detect_hockey_assist(scene, **params) -> list[Event]:
    """BA-51 hockey assist (broad) with the NBA flag (assister touch <= 1.0 s, no inferred dribble)."""
    P = _params("hockey_assist", params)
    out = []
    pas = detect_potential_assist(scene)
    passes = _passes(scene)
    for e in pas:
        assister = e.actors["passer"]
        pa = next(p for p in passes if p.t0 == e.t0 and p.a.pid == assister)
        prev = [p for p in passes if p.b is pa.a]
        if not prev:
            continue
        h = prev[-1]
        touch = (pa.t0 - h.tc) * DT
        nba = touch <= P.nba_max_touch_s and _dribbled(scene, pa.a) is None
        out.append(_pass_event(scene, h, "hockey_assist", min(h.pc, e.conf),
                               {"assister": assister, "shooter": e.attrs["shooter"], "hockey_assist_nba": nba,
                                "assister_touch_s": round(touch, 3)}, "BA-51"))
    return out


def detect_outlet_pass(scene, **params) -> list[Event]:
    """BA-50: pass by the defensive rebounder <= 3.0 s after rebound control; outlet_quick flag (<= 1.5 s, 6-15 m)."""
    P = _params("outlet_pass", params)
    rebs = [e for e in detect_rebound_control(scene) if e.attrs["label"] == "defensive"]
    out = []
    for p in _passes(scene):
        for e in rebs:
            if e.actors["rebounder"] == p.a.pid and p.a.a == e.start and (p.t0 - e.t0) * DT <= P.max_after_rebound_s:
                dt = (p.t0 - e.t0) * DT
                quick = dt <= P.quick_s and P.quick_min_len_m <= p.attrs["distance_m"] <= P.quick_max_len_m
                out.append(_pass_event(scene, p, "outlet_pass", min(p.pc, e.conf),
                                       {"after_rebound_s": round(dt, 3), "outlet_quick": quick}, "BA-50"))
    return out


# --------------------------------------------------------------------------------------
# L2: post play and isolation
# --------------------------------------------------------------------------------------
def _phi_deg(px, py, ax_, ay_, bx, by):
    return _ang((ax_ - px, ay_ - py), (bx - px, by - py))


def detect_post_seal(scene, **params) -> list[Event]:
    """BA-60 fixed: off-ball post player still in the post, defender in contact on the far side from the ball."""
    P = _params("post_seal", params)
    ball = scene.ball
    if ball is None:
        return []
    holder = _holder_array(scene)
    out = []
    for o in scene.offense:
        k = scene.kins[o]
        n = scene.n
        cond = np.zeros(n, bool)
        dsel = [None] * n
        pphi = np.full(n, np.nan)
        pcon = np.full(n, np.nan)
        for t in range(n):
            if not np.isfinite(k.x[t]) or not np.isfinite(ball.x[t]):
                continue
            h = holder[t]
            if h is None or h == o or h not in scene.offense:
                continue
            x, y = _xy(k, t)
            gate = in_spot("post_area_rule", x, y) or math.hypot(x, y) <= P.gate_r_m
            dn, dd = _nearest(scene, scene.defense, t, x, y)
            if dn is None:
                continue
            kd = scene.kins[dn]
            ph = _phi_deg(x, y, kd.x[t], kd.y[t], ball.x[t], ball.y[t])
            dsel[t] = dn
            sd = _sig2(k, t, kd, t)
            pcon[t] = float(p_below(dd, P.contact_radius_m, sd))
            pphi[t] = float(phi((ph - P.phi_min_deg) / max(math.degrees(sd / max(dd, 0.3)), 1.0)))
            cond[t] = (gate and k.stationary_s2[t] < P.s2_max and dd <= P.contact_radius_m and ph >= P.phi_min_deg
                       and math.hypot(ball.x[t], ball.y[t]) >= P.ball_min_r_m)
        for a, b in mv.hysteresis(cond, cond, P.min_s, max_gap_frames=P.max_gap_frames):
            w = min(b, a + _frames(P.min_s))
            disp = float(np.nanmax(np.hypot(k.x[a:w + 1] - k.x[a], k.y[a:w + 1] - k.y[a])))
            if disp > P.max_disp_m:
                continue
            still = float(np.mean(k.stationary_s2[a:b + 1] < P.s2_max))
            pc = min(window_conf(pcon, a, b), window_conf(pphi, a, b), still,
                     float(p_below(disp, P.max_disp_m, _sig2(k, a, k, w))))
            ds = [x for x in dsel[a:b + 1] if x]
            dmode = max(set(ds), key=ds.count) if ds else None
            x, y = _xy(k, a)
            phis = [_phi_deg(k.x[t], k.y[t], scene.kins[dsel[t]].x[t], scene.kins[dsel[t]].y[t], ball.x[t], ball.y[t])
                    for t in range(a, b + 1) if dsel[t]]
            out.append(Event("post_seal", {"post": o, "defender": dmode}, a, a, b, _conf(pc, k, a, a, b),
                             {"phi_median_deg": round(float(np.median(phis)), 1), "duration_s": round((b - a) * DT, 3),
                              "deep_seal": in_spot("deep_seal", x, y), "spot": spot_labels(x, y),
                              "seal_strict": bool(math.hypot(x, y) < P.seal_strict_r_m), "research_id": "BA-60"}))
    return out


def _holder_array(scene):
    """Per-frame controller id from the decoded touches (None in flights / loose)."""
    def build():
        h = np.array([None] * scene.n, dtype=object)
        for s in _model(scene).segs:
            h[s.a:s.b + 1] = s.pid
        return h
    return _cache(scene, ("holder", ()), build)


def detect_post_up(scene, **params) -> list[Event]:
    """BA-61 fixed: catch in the post gate, defender in contact >= 0.5 s, holder quiet; posture needs pose."""
    P = _params("post_up", params)
    m = _model(scene)
    ball = scene.ball
    if ball is None:
        return []
    out = []
    for s in m.segs:
        if not s.off:
            continue
        sk = _start_kind(scene, m, s)
        if sk not in ("pass", "handoff", "rebound", "loose_ball"):
            continue
        k = scene.kins[s.pid]
        tc = s.t_catch if s.t_catch is not None else s.a
        x, y = _xy(k, tc)
        # changes_loop1 BA-T6: the |x| / FT-line clause also needs r <= gate_r_max_m (an 18-ft face-up at
        # (3.9, 3.9) passed it)
        if not (in_spot("post_area_rule", x, y) or (abs(x) <= P.gate_abs_x_m and y <= spotlib.C["FT_Y"]
                                                     and math.hypot(x, y) <= P.gate_r_max_m)):
            continue
        hi = min(s.b, tc + _frames(P.window_s))
        dn, _ = _nearest(scene, scene.defense, tc, x, y)
        if dn is None:
            continue
        kd = scene.kins[dn]
        dd = mv.dist(k, kd)
        sgd = mv.sigma_dist(k, kd)
        contact = int(np.sum(dd[tc:hi + 1] <= P.contact_radius_m))
        if contact * DT < P.contact_min_s - 1e-9:
            continue
        q = _frames(P.quiet_s)
        disp = [math.hypot(k.x[t + q] - k.x[t], k.y[t + q] - k.y[t]) for t in range(tc, max(tc, hi - q) + 1)
                if t + q <= s.b]
        if not disp or min(disp) > P.quiet_disp_m:
            continue
        ek = _end_kind(scene, m, s)
        dur = (s.b - tc) * DT
        # changes_loop1 BA-T6: the pass / shot exception is for post entries only; a rebound or loose-ball
        # touch must last min_s (a 0.5 s putback is not a post-up)
        if dur < P.min_s - 1e-9 and (ek not in ("pass", "shot") or sk in ("rebound", "loose_ball")):
            continue
        pcon = window_conf(p_below(dd, P.contact_radius_m, sgd), tc, hi)
        pq = float(p_below(min(disp), P.quiet_disp_m, _sig(k, tc) * math.sqrt(2)))
        pc = min(pcon, pq, s.conf)
        # defence position (BA-62, attribute): median angles at P toward rim / ball
        ang_rim, ang_ball = [], []
        for t in range(tc, hi + 1):
            px, py = _xy(k, t)
            ang_rim.append(_ang((-px, -py), (kd.x[t] - px, kd.y[t] - py)))
            ang_ball.append(_ang((ball.x[t] - px, ball.y[t] - py), (kd.x[t] - px, kd.y[t] - py))
                            if np.isfinite(ball.x[t]) else float("nan"))
        ar = float(np.nanmedian(ang_rim))
        ab = float(np.nanmedian(ang_ball)) if np.any(np.isfinite(ang_ball)) else 180.0
        dpos = "behind" if ar <= P.behind_max_deg else ("front" if ab <= P.front_max_deg else "three_quarter")
        # changes_loop2 BA-T6b: the angle is measured between two stances 0.5-0.9 m apart, so its standard error
        # (sqrt(2) x pair sigma / distance, 8-15 deg at sigma_p 0.2-0.5) is comparable to the distance of a real
        # post-defence geometry from the 45 deg boundary. The label stays the point estimate; its probability
        # is attached as alternatives (status unresolved when the top two are within unresolved_margin).
        dmed = float(np.nanmedian(dd[tc:hi + 1]))
        sd_ang = max(1.0, math.degrees(float(np.nanmedian(sgd[tc:hi + 1])) / max(dmed, 0.3)))
        p_b = float(phi((P.behind_max_deg - ar) / sd_ang))
        p_f = (1.0 - p_b) * float(phi((P.front_max_deg - ab) / sd_ang))
        dalt = {"behind": round(p_b, 3), "front": round(p_f, 3), "three_quarter": round(max(0.0, 1.0 - p_b - p_f), 3)}
        top = sorted(dalt.values(), reverse=True)
        dstat = "unresolved" if top[0] - top[1] < P.unresolved_margin else "ok"
        depth = next((s_ for s_ in ("post_depth_deep", "post_depth_standard", "post_depth_high")
                      if in_spot(s_, x, y)), None)
        f = _free_before(m, s)
        out.append(Event("post_up", {"post": s.pid, "defender": dn, "passer": f.prev.pid if f and f.prev else None},
                         tc, tc, s.b, _conf(pc, k, tc, tc, s.b),
                         {"touch_duration_s": round(dur, 3), "end_kind": ek, "post_depth": depth,
                          "spot": spot_labels(x, y), "defense_position": dpos, "posture": "unknown_needs_pose",
                          "defense_position_alternatives": dalt, "defense_position_status": dstat,
                          "defender_rim_side": bool(ar <= P.behind_max_deg), "research_id": "BA-61"}))
    return out


def detect_isolation(scene, **params) -> list[Event]:
    """BA-70: holder with a defender <= 2.5 m and no teammate within 4.0 m for >= 2.0 s; screen-proxy check."""
    P = _params("isolation", params)
    m = _model(scene)
    drives = _drives(scene)
    shots = _shots(scene)
    out = []
    for s in m.segs:
        if not s.off:
            continue
        k = scene.kins[s.pid]
        tc = s.t_catch if s.t_catch is not None else s.a
        sdr = [d for d in drives if d.s is s]
        spot_up = bool(s.t_catch is not None and any((d.t0 - tc) * DT <= P.catch_drive_exclusion_s for d in sdr))
        dr = _dribbled(scene, s)
        n = scene.n
        mates = [o for o in scene.offense if o != s.pid]
        dD = np.min(np.stack([mv.dist(k, scene.kins[o]) for o in scene.defense]), 0) if scene.defense else \
            np.full(n, np.inf)
        dT = np.min(np.stack([mv.dist(k, scene.kins[o]) for o in mates]), 0) if mates else np.full(n, np.inf)
        sg = K_CAL * np.sqrt(np.maximum(k.var_p, 1e-6)) * math.sqrt(2)
        # changes_loop3 BA-I1: the teammate-clear test is noise-aware: a teammate must read
        # teammate_min_m + teammate_noise_k x pair sigma away
        with np.errstate(invalid="ignore"):
            cond = (dD <= P.defender_max_m) & (dT >= P.teammate_min_m + P.teammate_noise_k * sg)
        cond[:s.a] = False
        cond[s.b + 1:] = False
        for a, b in mv.hysteresis(cond, cond, P.min_s, max_gap_frames=P.max_gap_frames):
            lb = max(0, a - _frames(P.screen_lookback_s))
            screened = bool(np.nanmin(dT[lb:a + 1]) <= P.screen_proxy_m) if a > lb else False
            if screened:
                continue
            # changes_loop1 BA-T5: an isolation is an attack. Keep the window only if, in
            # [a - attack_before_s, b + attack_after_s], the handler drives, shoots, or dribbles with the
            # defender within attack_def_m for >= attack_dribble_min_s; drop spot-up drives (a window that
            # starts right after a catch followed by a quick drive) and windows starting at a segment edge.
            # changes_loop2 BA-T10b follow-up: a window starting within touch.clip_start_s of the clip start
            # has no screen lookback (the screen-proxy check cannot run), like an edge window
            if edge_factor(k, a) == 0.0 or a < _frames(PARAMS["touch"]["clip_start_s"]):
                continue
            if spot_up and (a - tc) * DT <= P.catch_drive_exclusion_s:
                continue
            w0, w1 = a - _frames(P.attack_before_s), b + _frames(P.attack_after_s)
            attack = "drive" if any(d.t1 >= w0 and d.t0 <= w1 for d in sdr) else None
            if attack is None and any(sh.s is s and w0 <= sh.t0 <= w1 for sh in shots):
                attack = "shot"
            if attack is None and dr is not None and dr[0] <= w1 and dr[2] >= w0:
                lo, hi = max(dr[0], w0, s.a), min(dr[2], w1, s.b)
                with np.errstate(invalid="ignore"):
                    tight = int(np.sum(dD[lo:hi + 1] <= P.attack_def_m)) if hi >= lo else 0
                # attacking dribble: tight defender and ground gained toward the rim (a dribble reversal
                # across the top with a shadowing defender is not an isolation attack)
                r_lo = float(np.nanmin(k.r[lo:hi + 1])) if hi >= lo else float("nan")
                # changes_loop3 BA-I1: the gain is a start-minus-minimum of a noisy series (biased upward by
                # about two position sigmas): the bound widens by attack_gain_noise_k pair sigmas
                if tight * DT >= P.attack_dribble_min_s - 1e-9 and \
                        float(k.r[lo]) - r_lo >= P.attack_dribble_gain_m + P.attack_gain_noise_k * float(sg[lo]):
                    attack = "dribble"
            if attack is None:
                continue
            pc = min(window_conf(p_below(dD, P.defender_max_m, sg), a, b),
                     window_conf(p_above(dT, P.teammate_min_m, sg), a, b), s.conf)
            x, _ = _xy(k, a)
            ballside = [o for o in mates if np.isfinite(scene.kins[o].x[a]) and scene.kins[o].x[a] * x > 0
                        and abs(scene.kins[o].x[a]) >= P.clear_abs_x_m and _d(k, scene.kins[o], a) <= P.clear_ballside_m]
            lb2 = max(s.a, a - _frames(P.broken_lookback_s))
            vr = -k.v_r
            with np.errstate(invalid="ignore"):
                retreat = mv.hysteresis(vr[lb2:a + 1] >= P.retreat_vr_mps, vr[lb2:a + 1] >= P.retreat_vr_mps, P.retreat_s)
            dn, _ = _nearest(scene, scene.defense, a, *_xy(k, a))
            out.append(Event("isolation", {"handler": s.pid, "defender": dn}, a, a, b, _conf(pc, k, a, a, b),
                             {"clear": len(ballside) <= 1, "from_broken_action": bool(retreat), "attack": attack,
                              "screen_check": "proxy_no_teammate_within_1.5m" if a - lb >= _frames(P.screen_lookback_s)
                              else "partial_lookback", "duration_s": round((b - a) * DT, 3), "research_id": "BA-70"}))
    return out


# --------------------------------------------------------------------------------------
# Items that need ball z, pose, PBP or restart data: declared, never guessed
# --------------------------------------------------------------------------------------
def detect_dribble_bounce(scene, **params) -> list[Event]:
    """BA-03 bounces / pickup need ball z (or the ray-oscillation method): needs_ball_z."""
    _params("dribble_bounce", params)
    return []


def detect_dribble_move_type(scene, **params) -> list[Event]:
    """BA-10..20 dribble-move types (crossover, hesitation, retreat, push, pound, ...): needs_ball_z / pose."""
    _params("dribble_move_type", params)
    return []


def detect_pass_height_type(scene, **params) -> list[Event]:
    """BA-43/44 bounce / chest / overhead pass: needs ball z or pose."""
    _params("pass_height_type", params)
    return []


def detect_throw_in_pass(scene, **params) -> list[Event]:
    """BA-52 throw-in flag: needs restart state (dead ball, inbounder out of bounds) from the transition family / PBP."""
    _params("throw_in_pass", params)
    return []


def detect_violation_turnover(scene, **params) -> list[Event]:
    """Travel, 5-second, offensive foul: need whistle / PBP (and pose for travel)."""
    _params("violation_turnover", params)
    return []


def detect_fakes(scene, **params) -> list[Event]:
    """Pump fake, pass fake, fake handoff ball-side: need pose (ball z for pump fakes)."""
    _params("fakes", params)
    return []


def detect_footwork(scene, **params) -> list[Event]:
    """Euro step, jump stop, two-foot gather, pivot: need foot keypoints."""
    _params("footwork", params)
    return []


def _tag_edge(fn):
    """changes_loop1 BA-T18: an event whose conf is 0 because t0 sits within 5 frames of a track segment edge
    (edge_factor 0, typically the clip start) is kept but tagged attrs.edge_status = 'edge' so consumers
    can drop it; contested_ball and isolation drop such events themselves."""
    def run(scene, **params):
        evs = fn(scene, **params)
        for e in evs:
            if e.conf > 0.0:
                continue
            ks = [scene.ball] + [scene.kins[v] for v in e.actors.values() if isinstance(v, str) and v in scene.kins]
            if any(k is not None and edge_factor(k, int(e.t0)) == 0.0 for k in ks):
                e.attrs["edge_status"] = "edge"
        return evs
    run.__name__, run.__doc__ = fn.__name__, fn.__doc__
    return run


DETECTORS = {
    "touch": detect_touch,
    "team_possession": detect_team_possession,
    "ball_flight": detect_ball_flight,
    "loose_ball": detect_loose_ball,
    "contested_ball": detect_contested_ball,
    "catch": detect_catch,
    "release": detect_release,
    "dribble_inferred": detect_dribble_inferred,
    "dribble_bounce": detect_dribble_bounce,
    "dribble_move_type": detect_dribble_move_type,
    "drive": detect_drive,
    "drive_direction": detect_drive_direction,
    "drive_depth": detect_drive_depth,
    "paint_touch": detect_paint_touch,
    "drive_defender_reaction": detect_drive_defender_reaction,
    "drive_outcome": detect_drive_outcome,
    "pass": detect_pass,
    "pass_incomplete": detect_pass_incomplete,
    "lob_pass": detect_lob_pass,
    "pass_height_type": detect_pass_height_type,
    "skip_pass": detect_skip_pass,
    "swing_pass": detect_swing_pass,
    "entry_pass": detect_entry_pass,
    "ball_reversal": detect_ball_reversal,
    "dribble_reversal": detect_dribble_reversal,
    "kick_out": detect_kick_out,
    "dump_off": detect_dump_off,
    "potential_assist": detect_potential_assist,
    "hockey_assist": detect_hockey_assist,
    "outlet_pass": detect_outlet_pass,
    "throw_in_pass": detect_throw_in_pass,
    "post_seal": detect_post_seal,
    "post_up": detect_post_up,
    "isolation": detect_isolation,
    "shot_release": detect_shot_release,
    "catch_and_shoot": detect_catch_and_shoot,
    "pull_up": detect_pull_up,
    "held_jumper": detect_held_jumper,
    "rebound_control": detect_rebound_control,
    "live_ball_turnover": detect_live_ball_turnover,
    "turnover_abstention": detect_turnover_abstention,
    "violation_turnover": detect_violation_turnover,
    "fakes": detect_fakes,
    "footwork": detect_footwork,
}


DETECTORS = {k: _tag_edge(fn) for k, fn in DETECTORS.items()}


def detect_all(scene) -> dict:
    """Run every detector with YAML parameters; returns {item_id: [Event, ...]}."""
    return {k: fn(scene) for k, fn in DETECTORS.items()}
