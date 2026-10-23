"""Screener / big-man actions after screens (movement grammar family 'bigs').

Reference detectors for config/movement_grammar/bigs.yaml (spec tooling, not the production
labeller). Every numeric threshold is read from that file at import: the YAML is the single
source of truth and keyword arguments only override it for experiments.

Frame and units: attacked-rim frame, metres, seconds, 29.97 fps (mvlib.DT). Sign convention:
mvlib.Kin.v_r is POSITIVE TOWARD THE RIM (rimward). The research text writes dr/dt (negative
toward the rim); every gate here is written in the mvlib sign.

Input contract (see YAML `input_contract`): screener post-actions take the screen moment as an
mvlib.Event of kind 'screen' supplied by the caller (the screens family or a hand label), so this
module never imports screens code:
    Event(kind='screen', actors={'screener': id, 'user': id, ['screener_defender': id],
          ['user_defender': id]}, t0=<frame of minimum smoothed screener-user distance>,
          start, end, conf, attrs={'screen_class': 'ball'|'dho'|'off_ball', ['screen_type': ...]})
Other optional context events: kind 'fga' (t0 = release, actors {'shooter'}), kind
'possession_change' (t0 = change frame). When they are absent, FGA is approximated from ball XY
(ball_xy_proxy) and transition starts from the path itself.

Every detector returns mvlib.Event objects with conf = product of test probabilities (each a
window_conf of a per-frame probability or a Phi(margin / sigma)) x edge_factor x gap_factor
(MP-16), times the input screen's own conf when there is one.
"""
from __future__ import annotations

import functools
import inspect
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import yaml

_HERE = Path(__file__).resolve()
for _p in (_HERE.parents[1], _HERE.parents[2] / "named_spots"):  # movement/ (mvlib) and named_spots/ (spotlib)
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import mvlib as M  # noqa: E402
import spotlib  # noqa: E402
from mvlib import DT, Event, edge_factor, frames, gap_factor, hysteresis, p_above, p_below, phi, window_conf  # noqa: E402

GRAMMAR = _HERE.parents[4] / "config" / "movement_grammar" / "bigs.yaml"
OWN_RIM_Y = 25.4508  # far rim (the team's own basket) in the attacked-rim frame (named_spots full_court)


# --------------------------------------------------------------------------------------
# Parameters (single source of truth: the YAML file)
# --------------------------------------------------------------------------------------
def _value(v):
    return v["value"] if isinstance(v, dict) and "value" in v else v


def load_grammar(path: Path = GRAMMAR):
    """Return (document, shared params, {item_id: params}) with units stripped."""
    doc = yaml.safe_load(Path(path).read_text())
    shared = {k: _value(v) for k, v in (doc.get("shared_params") or {}).items()}
    items = {it["id"]: {k: _value(v) for k, v in (it.get("params") or {}).items()} for it in doc["items"]}
    return doc, shared, items


DOC, SHARED, ITEMS = load_grammar()
_, SPOTS = spotlib.load()


def params(item_id: str, overrides: dict | None = None) -> dict:
    """Shared params, then the item's params, then caller overrides."""
    p = dict(SHARED)
    p.update(ITEMS.get(item_id, {}))
    if overrides:
        p.update(overrides)
    return p


# --------------------------------------------------------------------------------------
# Small numeric helpers
# --------------------------------------------------------------------------------------
def _fwd_mean(a: np.ndarray, n: int, min_cov: float = 0.8) -> np.ndarray:
    """m[t] = mean of a[t : t+n] (forward window of n frames); NaN if < min_cov of it is finite."""
    a = np.asarray(a, dtype=float)
    ok = np.isfinite(a)
    c = np.concatenate([[0.0], np.cumsum(np.where(ok, a, 0.0))])
    k = np.concatenate([[0], np.cumsum(ok)])
    L = len(a)
    out = np.full(L, np.nan)
    for t in range(L - n + 1):
        cnt = k[t + n] - k[t]
        if cnt >= min_cov * n:
            out[t] = (c[t + n] - c[t]) / cnt
    return out


def _c_mean(a: np.ndarray, half: int) -> np.ndarray:
    """Centred moving mean over [t - half, t + half] (NaN-aware, truncated at the ends)."""
    a = np.asarray(a, dtype=float)
    ok = np.isfinite(a)
    c = np.concatenate([[0.0], np.cumsum(np.where(ok, a, 0.0))])
    k = np.concatenate([[0], np.cumsum(ok)])
    L = len(a)
    lo = np.clip(np.arange(L) - half, 0, L)
    hi = np.clip(np.arange(L) + half + 1, 0, L)
    cnt = k[hi] - k[lo]
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(cnt > 0, (c[hi] - c[lo]) / np.maximum(cnt, 1), np.nan)


def _first(mask: np.ndarray, lo: int, hi: int):
    """First index in [lo, hi] where mask is True, else None."""
    lo, hi = max(lo, 0), min(hi, len(mask) - 1)
    if hi < lo:
        return None
    idx = np.flatnonzero(mask[lo:hi + 1])
    return int(lo + idx[0]) if len(idx) else None


def _clamp(v, a, b):
    return max(a, min(b, v))


def _xy(k, t):
    return float(k.x[t]), float(k.y[t])


def _r(x, y):
    return math.hypot(x, y)


def _angle_at(o, a, b):
    """Angle (deg) at point o between rays o->a and o->b; NaN if a ray is degenerate."""
    ax, ay = a[0] - o[0], a[1] - o[1]
    bx, by = b[0] - o[0], b[1] - o[1]
    na, nb = math.hypot(ax, ay), math.hypot(bx, by)
    if na < 1e-6 or nb < 1e-6 or not np.isfinite(na * nb):
        return float("nan")
    c = _clamp((ax * bx + ay * by) / (na * nb), -1.0, 1.0)
    return math.degrees(math.acos(c))


def _sig_v(k):
    """Per-frame 1-sigma of a velocity component (calibrated, edge-inflated)."""
    return k.sigma_speed


def _sig_p(k):
    return M.K_CAL * np.sqrt(np.maximum(k.var_p, 1e-6))


def noise_tier(k, P=None) -> str:
    """L2: per-track noise tier from the smoother's own position sigma: 'high' when the median K_CAL*sqrt(var_p)
    >= high_noise_sig_p_m (sim: 0.088 / 0.124 / 0.16 / 0.18 m at sigma_p 0.2 / 0.3 / 0.4 / 0.5, so the cut sits
    between 0.3 and 0.4, next to mvlib's own Q_HIGH_NOISE switch at sigma_p 0.45), else 'low'. Cached on k.extra."""
    P = P or SHARED
    key = ("bigs_tier", P["high_noise_sig_p_m"])
    if key not in k.extra:
        sp = _sig_p(k)
        med = float(np.nanmedian(sp)) if np.any(np.isfinite(sp)) else 0.0
        k.extra[key] = "high" if med >= P["high_noise_sig_p_m"] else "low"
    return k.extra[key]


def tiered(P, name, k):
    """Value of a noise-tier-aware param: P[name + '_high'] on a high-noise track, else P[name + '_low']."""
    return P[name + ("_high" if noise_tier(k, P) == "high" else "_low")]


def run_lengths(mask: np.ndarray) -> np.ndarray:
    """Per frame, the length in frames of the run of True that contains it (0 on False frames)."""
    out = np.zeros(len(mask), dtype=int)
    a = None
    for t, v in enumerate(list(mask) + [False]):
        if v and a is None:
            a = t
        elif not v and a is not None:
            out[a:t] = t - a
            a = None
    return out


def _conf(k, parts, t0, a, b, extra=1.0):
    """MP-16 confidence: product of test probabilities x edge_factor x gap_factor x extra."""
    p = float(np.prod([_clamp(float(x), 0.0, 1.0) for x in parts])) if parts else 1.0
    return float(_clamp(p * edge_factor(k, int(t0)) * gap_factor(k, int(a), int(b)) * extra, 0.0, 1.0))


_NEVER = -10**9  # "no previous event" sentinel for dedupe counters


def _memo(scene, key, fn):
    """Per-scene memo (B18): scene-level results (holder sequence, passes, screen frames, detector
    outputs reused by composite detectors) are computed once per scene and key."""
    cache = scene.__dict__.setdefault("_bigs_memo", {})
    if key not in cache:
        cache[key] = fn()
    return cache[key]


def _ev_key(ev):
    """Hashable signature of an input event (Events are mutable dataclasses, not hashable)."""
    return (ev.kind, tuple(sorted(ev.actors.items())), int(ev.t0), int(ev.start), int(ev.end), float(ev.conf),
            tuple(sorted((k, str(v)) for k, v in ev.attrs.items())))


def _evs_key(evs):
    return tuple(_ev_key(e) for e in (evs or []))


def _ov_key(overrides):
    return tuple(sorted((k, str(v)) for k, v in (overrides or {}).items()))


def _nonzero(fn):
    """Shared rule (B10): a detector never emits an event with conf == 0.0 (an event nobody can trust is
    not an event). Exception: screener_post_action's 'unknown_post_action' label (camera_cut_policy)."""
    @functools.wraps(fn)
    def wrapped(scene, *a, **kw):
        return [e for e in fn(scene, *a, **kw) if e.conf > 0.0 or e.attrs.get("label") == "unknown_post_action"]
    return wrapped


# --------------------------------------------------------------------------------------
# Spots (named_spots is the only spot dictionary; never redefined here)
# --------------------------------------------------------------------------------------
def in_spot(sid: str, x: float, y: float, **ctx) -> bool:
    """True if (x, y) carries label `sid` (either side for mirrored spots)."""
    if not (np.isfinite(x) and np.isfinite(y)):
        return False
    return bool(SPOTS[sid].labels(float(x), float(y), **ctx))


def in_any(sids, x, y) -> bool:
    return any(in_spot(s, x, y) for s in sids)


def spot_mask(sid: str, k, a: int = 0, b: int | None = None) -> np.ndarray:
    """Per-frame membership of a track in a spot (False outside [a, b] or where unknown)."""
    b = len(k.x) - 1 if b is None else b
    m = np.zeros(len(k.x), dtype=bool)
    for t in range(max(a, 0), min(b, len(k.x) - 1) + 1):
        m[t] = in_spot(sid, k.x[t], k.y[t])
    return m


def spot_labels(x, y, sids) -> list:
    return [s for s in sids if in_spot(s, x, y)]


# --------------------------------------------------------------------------------------
# Shared kinematic states
# --------------------------------------------------------------------------------------
def stationary_runs(k, P=None):
    """Shared stationary state (MP-09): enter stationary_s2 < s2_enter, stay while < s2_stay.

    B10 precision gate: a run can only START on a frame whose velocity estimate is precise (edge >=
    stat_min_edge_frames and K_CAL*sqrt(var_v) <= stat_sigv_rel x the track's median) and whose CA-RTS speed
    is < stat_enter_speed_mps. During smoother warm-up var_v is huge, so s2 alone calls the first frames of
    every segment stationary (and the stay test then carries a 3 m/s approach into the run).
    Cached on k.extra. Returns (mask, list of (a, b) runs)."""
    P = P or SHARED
    key = ("bigs_stat", P["s2_enter"], P["s2_stay"], P["stat_sigv_rel"], P["stat_min_edge_frames"], P["stat_enter_speed_mps"])
    if key not in k.extra:
        s2 = k.stationary_s2
        sigv = M.K_CAL * np.sqrt(np.maximum(k.var_v, 0.0))
        med = np.nanmedian(sigv) if np.any(np.isfinite(sigv)) else np.nan
        precise = np.nan_to_num((sigv <= P["stat_sigv_rel"] * med) & (k.edge >= P["stat_min_edge_frames"]), nan=False).astype(bool)
        slow = np.nan_to_num(k.speed < P["stat_enter_speed_mps"], nan=False).astype(bool)
        enter = (np.nan_to_num(s2, nan=np.inf) < P["s2_enter"]) & precise & slow
        stay = np.nan_to_num(s2, nan=np.inf) < P["s2_stay"]
        runs = hysteresis(enter, stay, 0.0, int(P["stat_bridge_frames"]))
        mask = np.zeros(len(s2), dtype=bool)
        for a, b in runs:
            mask[a:b + 1] = True
        k.extra[key] = (mask, runs)
    return k.extra[key]


def merge_runs(k, runs, max_gap_s, max_shift_m):
    """Merge consecutive stationary runs separated by <= max_gap_s whose mean positions differ by
    < max_shift_m: correlated (AR) tracker noise breaks a held screen into pieces at the same spot."""
    out = []
    for a, b in runs:
        if out:
            pa, pb = out[-1]
            shift = math.hypot(np.nanmean(k.x[a:b + 1]) - np.nanmean(k.x[pa:pb + 1]),
                               np.nanmean(k.y[a:b + 1]) - np.nanmean(k.y[pa:pb + 1]))
            if (a - pb) * DT <= max_gap_s and shift < max_shift_m:
                out[-1] = (pa, b)
                continue
        out.append((a, b))
    return out


def held_mask(k, P=None):
    """Stationary mask after merge_runs: the 'held position' state used by sets, seals and posts."""
    P = P or SHARED
    _, runs = stationary_runs(k, P)
    m = np.zeros(len(k.x), dtype=bool)
    for a, b in merge_runs(k, runs, P["merge_gap_s"], P["merge_shift_m"]):
        m[a:b + 1] = True
    return m


def p_stationary(k, P=None):
    """Per-frame P(stationary) = Phi((s2_enter - s2) / 2), 2 = sd of chi-square(2)."""
    P = P or SHARED
    return phi((P["s2_enter"] - np.nan_to_num(k.stationary_s2, nan=1e9)) / 2.0)


def speed_long(k, P=None):
    """Speed of the centred 1.0 s-support mean velocity (removes most of the Rayleigh bias)."""
    P = P or SHARED
    h = frames(P["support_long_s"]) // 2
    return np.hypot(_c_mean(k.vx, h), _c_mean(k.vy, h))


def gate_onset(v: np.ndarray, thr: float, n: int, lo: int, hi: int, above: bool = True):
    """First window start a in [lo, hi] whose n-frame forward mean of v passes thr (E4 fix:
    window mean, not every frame). Returns (a, window mean) or (None, nan)."""
    m = _fwd_mean(v, n)
    ok = (m >= thr) if above else (m <= thr)
    a = _first(np.nan_to_num(ok, nan=False).astype(bool), lo, hi)
    return (a, float(m[a])) if a is not None else (None, float("nan"))


def gate_conf(k, thr, n_g, lo, hi):
    """B4: confidence of a window-mean v_r gate, read at the BEST gate window starting in [lo, hi] (the
    extremum), not at the first window that crosses thr (whose mean is ~thr, so P ~ 0.5 by construction)."""
    m = _fwd_mean(k.v_r, n_g + 1)
    hi = max(lo, min(hi, len(m) - 1))
    seg = m[lo:hi + 1]
    b = lo + int(np.nanargmax(seg)) if np.any(np.isfinite(seg)) else lo
    return window_conf(p_above(k.v_r, thr, _sig_v(k)), b, b + n_g)


def run_start(v: np.ndarray, thr: float, a: int, above: bool = True) -> int:
    """Walk back from frame a to the first frame of the per-frame run v >= thr (or <= thr)."""
    t = a
    while t - 1 >= 0 and np.isfinite(v[t - 1]) and ((v[t - 1] >= thr) if above else (v[t - 1] <= thr)):
        t -= 1
    return t


# --------------------------------------------------------------------------------------
# Ball context from XY (holder runs, passes, catches, FGA proxy)
# --------------------------------------------------------------------------------------
def _runs(seq):
    """[(value, a, b)] maximal runs of equal values (None included)."""
    out, a = [], 0
    for t in range(1, len(seq) + 1):
        if t == len(seq) or seq[t] != seq[a]:
            out.append((seq[a], a, t - 1))
            a = t
    return out


def holder_seq(scene, min_run_s: float | None = None) -> list:
    """Debounced holder per frame. mvlib's nearest-within-HOLD_R holder flickers when two attackers
    are within ~1 m of the ball (handoffs, screens): a player run shorter than holder_min_run_s that
    follows another player's run is given to that player, and a short None gap between two runs of
    the same player is filled with him."""
    mr = SHARED["holder_min_run_s"] if min_run_s is None else min_run_s
    return list(_memo(scene, ("holder_seq", mr), lambda: _holder_seq(scene, mr)))


def _holder_seq(scene, min_run_s):
    m = frames(min_run_s)
    seq = list(scene.holder)
    runs = _runs(seq)
    for i, (p, a, b) in enumerate(runs):
        if b - a + 1 >= m or i == 0:
            continue
        prev = seq[a - 1]
        nxt = seq[b + 1] if b + 1 < len(seq) else None
        if p is not None and prev is not None:
            seq[a:b + 1] = [prev] * (b - a + 1)
        elif p is None and prev is not None and prev == nxt:
            seq[a:b + 1] = [prev] * (b - a + 1)
    return seq


def holder_runs(scene):
    """[(pid, a, b)] maximal runs of a constant non-None (debounced) holder."""
    return [(p, a, b) for p, a, b in _runs(holder_seq(scene)) if p is not None]


def ball_observed(scene, a, b):
    if scene.ball is None:
        return False
    seg = scene.ball.x[max(a, 0):b + 1]
    return len(seg) > 0 and np.mean(np.isfinite(seg)) >= 0.8


def passes(scene, max_flight_s: float = 2.0):
    """[(passer, release_frame, receiver, catch_frame)] between offensive players, from holder runs
    separated by an observed ball flight (holder None, ball tracked)."""
    return list(_memo(scene, ("passes", max_flight_s), lambda: _passes(scene, max_flight_s)))


def _passes(scene, max_flight_s):
    runs = holder_runs(scene)
    out = []
    for (pa, a0, a1), (pb, b0, b1) in zip(runs, runs[1:]):
        if pa == pb or (b0 - a1) * DT > max_flight_s:
            continue
        if b0 - a1 > 1 and not ball_observed(scene, a1 + 1, b0 - 1):
            continue
        out.append((pa, a1, pb, b0))
    return out


def catches(scene, pid):
    """Catch frames of pid: starts of pid's holder runs that follow a flight or another holder."""
    return [a for (p, a, b) in holder_runs(scene) if p == pid and a > 0]


def fga_events(scene, shots=None, P=None):
    """FGA list [(shooter, release_frame, source)]: caller 'fga' events first, else the ball-XY
    proxy (ball reaches r <= fga_rim_r with no holder within fga_max_flight_s of a release)."""
    P = P or SHARED
    if shots:
        return [(ev.actors.get("shooter"), int(ev.t0), "event") for ev in shots if ev.kind == "fga"]
    out = []
    if scene.ball is None:
        return out
    br = np.hypot(scene.ball.x, scene.ball.y)
    hs = holder_seq(scene)
    for pid, a, b in holder_runs(scene):
        hi = min(scene.n - 1, b + frames(P["fga_max_flight_s"]))
        for t in range(b + 1, hi + 1):
            if hs[t] is not None:
                break
            if np.isfinite(br[t]) and br[t] <= P["fga_rim_r"]:
                out.append((pid, b, "ball_xy_proxy"))
                break
    return out


def ball_xy(scene, t):
    """Ball position at t, falling back to the holder's position (ball above heads / occluded)."""
    if scene.ball is not None and np.isfinite(scene.ball.x[t]):
        return float(scene.ball.x[t]), float(scene.ball.y[t])
    h = scene.holder[t]
    if h is not None:
        return _xy(scene.k(h), t)
    return float("nan"), float("nan")


def nearest_defender(scene, pid, a, b):
    """Defender with the smallest mean distance to pid over [a, b] (and that distance)."""
    kp = scene.k(pid)
    best, bd = None, np.inf
    for d in scene.defense:
        dd = np.nanmean(M.dist(kp, scene.k(d))[max(a, 0):b + 1]) if b >= a else np.nan
        if np.isfinite(dd) and dd < bd:
            best, bd = d, dd
    return best, bd


# --------------------------------------------------------------------------------------
# P-SCREEN-FRAME: the shared reference frame of a screener's post-action
# --------------------------------------------------------------------------------------
@dataclass
class ScreenFrame:
    screen: Event
    s: str
    h: str
    cls: str
    t0: int
    px: float
    py: float
    r0: float
    t_set: int | None
    set_end: int | None
    dwell_s: float
    never_set: bool
    min_speed: float  # minimum CA-RTS speed within +-never_set_half_s of t0
    t_rel: int | None
    t_use: int | None
    use_fallback: bool
    release: str  # never_set | early | post_use | held
    p_early: float
    p_slow: float  # P(slow slip | early): dwell above the calibrated quick/slow split
    first_move: str  # rimward | outward | lateral | hold
    t_first_move: int | None
    w_end: int
    D_s: str | None
    D_h: str | None
    drag: bool
    attrs: dict = field(default_factory=dict)


def screen_class(ev) -> str:
    """Screen class of an input screen event: attrs 'screen_class' (this module's contract), else the screens
    family's own attrs 'kind' mapped by shared screen_kind_map (L4-1: the screens family writes kind on_ball /
    off_ball / handoff and no screen_class, so every off-ball screen was read as a ball screen), else 'ball'."""
    c = ev.attrs.get("screen_class")
    if c is None:
        c = SHARED["screen_kind_map"].get(ev.attrs.get("kind"), "ball")
    return c


def _screens(screens, classes=("ball", "dho")):
    return [e for e in (screens or []) if e.kind == "screen" and screen_class(e) in classes]


def screen_frame(scene, ev: Event, **overrides) -> ScreenFrame | None:
    """Build the post-action frame of one input screen event (YAML item screen_frame). Memoised per scene,
    event signature and overrides (B18); callers must not mutate the returned frame."""
    return _memo(scene, ("screen_frame", _ev_key(ev), _ov_key(overrides)), lambda: _screen_frame(scene, ev, overrides))


def _screen_frame(scene, ev, overrides):
    P = params("screen_frame", overrides)
    s, h = ev.actors.get("screener"), ev.actors.get("user")
    if s not in scene.kins or h not in scene.kins:
        return None
    ks, kh = scene.k(s), scene.k(h)
    n, t0 = scene.n, int(ev.t0)
    if not (0 <= t0 < n) or not np.isfinite(ks.x[t0]) or not np.isfinite(kh.x[t0]):
        return None
    cls = screen_class(ev)
    mask, runs = stationary_runs(ks, P)
    runs = merge_runs(ks, runs, P["merge_gap_s"], P["merge_shift_m"])
    # stationary run that contains t0, ends <= set_before_s before it, or starts <= set_after_s after it
    lo, hi = t0 - frames(P["set_before_s"]), t0 + frames(P["set_after_s"])
    cand = [(a, b) for a, b in runs if b >= lo and a <= hi]
    run = min(cand, key=lambda ab: 0 if ab[0] <= t0 <= ab[1] else min(abs(ab[0] - t0), abs(ab[1] - t0))) if cand else None
    # minimum CA-RTS speed near t0 (not the 1 s-mean speed: averaging the velocity vector across the
    # turn at the screen hides a stop). Sim: pass-through 2.35+-0.24 m/s, stop-and-go 1.35+-0.31 at sigma 0.3
    sp = ks.speed
    w = slice(max(0, t0 - frames(P["never_set_half_s"])), min(n, t0 + frames(P["never_set_half_s"]) + 1))
    min_sl = float(np.nanmin(sp[w])) if np.any(np.isfinite(sp[w])) else float("nan")
    never_set = run is None and np.isfinite(min_sl) and min_sl >= P["never_set_speed_mps"]
    p_never = float(phi((min_sl - P["never_set_speed_mps"]) / P["never_set_sigma_mps"])) if run is None else 0.0
    t_set = set_end = None
    dwell = 0.0
    if run is not None:
        t_set, set_end = run
        dwell = (set_end - t_set) * DT
    elif not never_set:  # slowed but never significantly stationary: a touch set at the speed minimum
        t_set = set_end = int(w.start + np.nanargmin(sp[w]))
    # screen spot P_s (B12 / E8): mean smoothed position over the set run within +-ps_half_s of t0 (or of
    # set_end when the screener left before t0, a slip); a single frame only at the speed minimum when he
    # never set (ghost / pass-through) or for a touch set. One AR-noisy frame moved P_s by 0.3-0.5 m.
    t_min = None
    if never_set:
        a_, b_ = max(0, t0 - frames(P["never_rel_before_s"])), min(n - 1, t0 + frames(P["never_rel_after_s"]))
        t_min = int(a_ + np.nanargmin(sp[a_:b_ + 1]))
    tp = t_min if never_set else (t0 if set_end is None or set_end >= t0 else set_end)
    if never_set or set_end is None or set_end == t_set:
        px, py = _xy(ks, tp)
    else:
        lo_p = max(t_set, min(t0, set_end) - frames(P["ps_half_s"]))
        hi_p = min(set_end, t0 + frames(P["ps_half_s"]))
        if hi_p < lo_p:
            lo_p = hi_p = tp
        px, py = float(np.nanmean(ks.x[lo_p:hi_p + 1])), float(np.nanmean(ks.y[lo_p:hi_p + 1]))
    r0 = _r(px, py)
    # window end: cap, next screen by the same screener is handled by callers (move_to_screen)
    w_end = min(n - 1, t0 + frames(P["window_cap_s"]))
    # release: first moving frame after the set (minus the calibrated smoother lag), provided the
    # screener later gets release_disp_m away from P_s inside the window
    dist_ps = np.hypot(ks.x - px, ks.y - py)
    if never_set:  # release = the speed minimum of the pass near the screen
        t_rel = t_min
    else:
        cand_rel = set_end + 1 - frames(P["release_lag_s"])
        far = _first(dist_ps >= P["release_disp_m"], set_end, w_end)
        t_rel = max(cand_rel, t_set) if far is not None else None
    # use: handler passes the screen line (ball/off-ball) or receives the handoff (DHO)
    use_fallback = False
    t_use = None
    if cls == "dho":
        hs = holder_seq(scene)
        t_use = _first(np.array([hs[t] == h for t in range(n)]), t0 - frames(P["use_before_s"]), w_end)
    else:
        a, b = max(0, t0 - frames(P["heading_from_s"])), max(0, t0 - frames(P["heading_to_s"]))
        ux, uy = np.nanmean(kh.vx[a:b + 1]), np.nanmean(kh.vy[a:b + 1])
        sp = math.hypot(ux, uy) if np.isfinite(ux) else 0.0
        if sp >= P["use_min_speed_mps"]:
            ux, uy = ux / sp, uy / sp
            proj = (kh.x - px) * ux + (kh.y - py) * uy
            near = np.hypot(kh.x - px, kh.y - py) <= P["use_radius_m"]
            t_use = _first(np.nan_to_num(proj >= 0, nan=False).astype(bool) & near, t0 - frames(P["use_before_s"]), w_end)
    if t_use is None:  # handler stopped at the screen or turned away: use the screen moment + lag
        t_use, use_fallback = t0 + frames(P["use_fallback_s"]), True
    # release timing axis (A)
    if t_rel is None:
        release, p_early, early = "held", 0.0, False
    else:
        # L2-R3: tier-aware. At sigma_p 0.5 the smoothed roll start leads the true release by up to 0.3 s on some
        # seeds, so a post-use top roll read t_use - t_rel = 3 frames (0.1001 s) against the 0.1 s cut: 'early'.
        margin = (t_use - t_rel) * DT - tiered(P, "early_margin_s", ks)
        p_early = float(phi(margin / P["timing_sigma_s"]))
        early = margin > 0
        release = "never_set" if never_set else ("early" if early else "post_use")
    p_slow = float(phi((dwell - P["slow_dwell_split_s"]) / P["dwell_sigma_s"])) if t_set is not None else 0.0
    # first move axis (B): direction of the displacement when the screener is first d_first_move_m from P_s
    first_move, t_fm = "hold", None
    if t_rel is not None:
        t_fm = _first(dist_ps >= P["first_move_m"], t_rel, w_end)
        if t_fm is not None:
            c = (ks.r[t_fm] - r0) / max(dist_ps[t_fm], 1e-6)
            first_move = "rimward" if c <= -P["first_move_cos"] else ("outward" if c >= P["first_move_cos"] else "lateral")
    D_s = ev.actors.get("screener_defender") or nearest_defender(scene, s, t0 - frames(P["defender_window_s"]), t0)[0]
    D_h = ev.actors.get("user_defender") or nearest_defender(scene, h, t0 - frames(P["defender_window_s"]), t0)[0]
    a, b = max(0, t0 - frames(P["drag_from_s"])), max(0, t0 - frames(P["drag_to_s"]))
    drag = bool(np.nanmean(-ks.vy[a:b + 1]) >= P["drag_speed_mps"]) if b > a else False
    return ScreenFrame(ev, s, h, cls, t0, px, py, r0, t_set, set_end, dwell, never_set, min_sl, t_rel, t_use,
                       use_fallback, release, p_early, p_slow, first_move, t_fm, w_end, D_s, D_h, drag,
                       dict(early=early, p_never_set=round(p_never, 3)))


def _frame_attrs(f: ScreenFrame) -> dict:
    return dict(screen_t0=f.t0, P_s=(round(f.px, 2), round(f.py, 2)), r_s0=round(f.r0, 2), t_set=f.t_set,
                dwell_s=round(f.dwell_s, 3), t_rel=f.t_rel, t_use=f.t_use, use_fallback=f.use_fallback,
                release_timing=f.release, p_early=round(f.p_early, 3), p_slow=round(f.p_slow, 3),
                first_move=f.first_move, min_speed=round(f.min_speed, 2), drag=f.drag, **f.attrs,
                screener_defender=f.D_s, user_defender=f.D_h)


# --------------------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------------------
@_nonzero
def detect_screen_frame(scene, screens=None, **params_):
    """P-SCREEN-FRAME as an event: one 'screen_frame' per input screen (t0 = screen moment)."""
    out = []
    for ev in _screens(screens, ("ball", "dho", "off_ball")):
        f = screen_frame(scene, ev, **params_)
        if f is None:
            continue
        k = scene.k(f.s)
        a, b = (f.t_set if f.t_set is not None else f.t0), f.w_end
        conf = _conf(k, [], f.t0, min(a, f.t0), b, ev.conf)
        out.append(Event("screen_frame", {"screener": f.s, "user": f.h}, f.t0, min(a, f.t0), b, conf, _frame_attrs(f)))
    return out


@_nonzero
def detect_screener_set_state(scene, screens=None, **params_):
    """Screener's set (stationary run at the screen): t0 = t_set; quick/slow as a probability (E2)."""
    P = params("screener_set_state", params_)
    Pf = params("screen_frame", params_)  # never_set_* live only under screen_frame (B17)
    out = []
    for ev in _screens(screens, ("ball", "dho", "off_ball")):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.never_set or f.t_set is None:
            continue
        k = scene.k(f.s)
        a, b = f.t_set, max(f.set_end, f.t_set)
        pst = window_conf(p_stationary(k, P), a, b)
        if f.set_end == f.t_set:  # touch set (speed minimum only): confidence from the long-support speed
            pst = float(p_below(f.min_speed, P["never_set_speed_mps"], Pf["never_set_sigma_mps"]))
        conf = _conf(k, [pst], a, a, b, ev.conf)
        out.append(Event("screen_set", {"screener": f.s, "user": f.h}, a, a, b, conf,
                         dict(dwell_s=round(f.dwell_s, 3), p_slow=round(f.p_slow, 3), touch_set=(f.set_end == f.t_set),
                              moving_screen_candidate=bool(f.min_speed >= P["moving_screen_mps"] and f.dwell_s < P["moving_screen_dwell_s"]))))
    return out


def _behind_iv(cond, a, b, min_s):
    c = cond.copy()
    c[:a] = False
    c[b + 1:] = False
    iv = hysteresis(c, c, min_s, 1)
    return iv[0] if iv else None


@_nonzero
def detect_behind_def(scene, screens=None, **params_):
    """Roller behind his screener's defender along the roller's rim direction (B8), t0 = t_rel.

    lead = (D_s - s) . u with u = (x_s, y_s) / r_s, the unit vector from the rim through the roller, so a
    positive lead means the defender is farther from the rim (= r(D_s) - r(s) to first order). CTG's
    y-axis lead (2.5 ft toward the baseline) is stored as ctg_y_lead_m, and ctg_behind evaluates the gate
    only until the end of the handler's touch (B19 / E15)."""
    P = params("behind_def", params_)
    out = []
    for ev in _screens(screens):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.t_rel is None or f.D_s is None:
            continue
        ks, kd = scene.k(f.s), scene.k(f.D_s)
        a, b = f.t_rel, f.w_end
        rs = np.where(ks.r > 0, ks.r, np.nan)
        lead = ((kd.x - ks.x) * ks.x + (kd.y - ks.y) * ks.y) / rs
        lead_y = kd.y - ks.y
        sig = np.sqrt(_sig_p(ks) ** 2 + _sig_p(kd) ** 2)
        vr_m = _c_mean(ks.v_r, frames(P["gate_window_s"]) // 2)
        rimward = np.nan_to_num(vr_m >= P["rimward_mps"], nan=False).astype(bool)
        cond = np.nan_to_num(lead >= P["behind_m"], nan=False).astype(bool) & rimward
        iv = _behind_iv(cond, a, b, P["min_s"])
        if iv is None:
            continue
        i0, i1 = iv
        # CTG-compatible value: the y-axis test bounded by the end of the handler's holder run containing t0
        hs = holder_seq(scene)
        t_end = None
        if hs[f.t0] == f.h:
            t_end = f.t0
            while t_end + 1 < scene.n and hs[t_end + 1] == f.h:
                t_end += 1
        cond_y = np.nan_to_num(lead_y >= P["behind_m"], nan=False).astype(bool) & rimward
        ctg = bool(t_end is not None and _behind_iv(cond_y, a, t_end, P["min_s"]) is not None)
        pc = window_conf(p_above(lead, P["behind_m"], sig), i0, i1)
        conf = _conf(ks, [pc], f.t_rel, a, i1, ev.conf)
        out.append(Event("behind_def", {"roller": f.s, "screener_defender": f.D_s}, f.t_rel, i0, i1, conf,
                         dict(first_behind_frame=i0, max_lead_m=round(float(np.nanmax(lead[i0:i1 + 1])), 2),
                              radial_lead_m=round(float(kd.r[i1] - ks.r[i1]), 2),
                              ctg_y_lead_m=round(float(np.nanmax(lead_y[i0:i1 + 1])), 2), ctg_behind=ctg,
                              handler_touch_end=t_end, **_frame_attrs(f))))
    return out


def _seal_mask(scene, o, region, P, phi_min):
    """Per-frame seal condition for player o: in region, stationary, nearest defender within
    seal_def_m (and >= seal_def_min_m), angle defender-o-ball > phi_min. Returns (mask, unk, loose, cand,
    d_ids, phis): cand = held, in region, nearest defender within seal_def_m + seal_slack_m."""
    ko = scene.k(o)
    mask_stat = held_mask(ko, P)
    n = scene.n
    m = np.zeros(n, dtype=bool)
    unk = np.zeros(n, dtype=bool)  # defender closer than seal_def_min_m: angle undefined, bridge only
    loose = np.zeros(n, dtype=bool)  # geometry met with seal_slack_m extra distance: onset walk-back only
    dids = [None] * n
    phis = np.full(n, np.nan)
    dk = {d: scene.k(d) for d in scene.defense}
    # L2-B13: seal_def_m is tier-aware. At sigma_p 0.5 a true 0.89 m post-defender gap reads 1.2-1.9 m for most of
    # the seal (correlated tracker error on two players), so the 1.2 m cut only opened 0.5-1.0 s late, or never.
    def_m = tiered(P, "seal_def_m", ko)
    for t in range(n):
        x, y = ko.x[t], ko.y[t]
        if not (mask_stat[t] and np.isfinite(x) and region(x, y)):
            continue
        best, bd = None, np.inf
        for d, kd in dk.items():
            dd = math.hypot(kd.x[t] - x, kd.y[t] - y)
            if np.isfinite(dd) and dd < bd:
                best, bd = d, dd
        if best is None or bd > def_m + P["seal_slack_m"]:
            continue
        dids[t] = best
        if bd < P["seal_def_min_m"]:
            unk[t] = True
            continue
        bx, by = ball_xy(scene, t)
        ph = _angle_at((x, y), _xy(dk[best], t), (bx, by))
        phis[t] = ph
        ok = np.isfinite(ph) and ph > phi_min
        m[t] = ok and bd <= def_m
        loose[t] = ok
    cand = np.array([d is not None for d in dids])
    return m, unk, loose, cand, dids, phis


def seal_intervals(m, unk, cand, P, min_s, merge_gap=0):
    """Seal intervals (B13): enter on m, stay on m or unknown-angle frames; the onset is walked back
    <= walk_back_s over candidate frames (held, in the region, defender within seal_def_m + seal_slack_m:
    noise in a pair distance and an undefined angle delay the first strict frame), intervals that then
    touch are merged, and only then is min_s applied (unk frames count toward it)."""
    raw = []
    for a, b in hysteresis(m, m | unk, 0.0, int(P["stat_bridge_frames"])):
        lim = max(0, a - frames(P["walk_back_s"]))
        while a - 1 >= lim and cand[a - 1]:
            a -= 1
        if raw and a <= raw[-1][1] + 1 + merge_gap:  # L2-R5: merge_gap frames bridge a noise break in one seal
            raw[-1] = (raw[-1][0], b)
        else:
            raw.append((a, b))
    return [(a, b) for a, b in raw if (b - a) * DT >= min_s - 1e-9]


@_nonzero
def detect_post_seal(scene, **params_):
    """Post seal: stationary in post_area at r <= r_max, defender <= 1.2 m on the far side from the ball."""
    P = params("post_seal", params_)
    out = []
    for o in scene.offense:
        ko = scene.k(o)

        r_max = tiered(P, "r_max", ko)  # L2-B13: a true r 3.12 post reads 3.5-3.9 m at sigma_p 0.5

        def region(x, y):
            return _r(x, y) <= r_max and in_spot("post_area", x, y)

        m, unk, loose, cand, dids, phis = _seal_mask(scene, o, region, P, P["phi_partial_deg"])
        hs = holder_seq(scene)
        free = np.array([hs[t] != o for t in range(scene.n)])
        p_reg = p_below(ko.r, r_max, _sig_p(ko))
        for a, b in seal_intervals(m & free, unk & free, cand & free, P, P["min_s"], frames(P["seal_merge_gap_s"])):
            ph = float(np.nanmean(phis[a:b + 1]))
            d = max(set(x for x in dids[a:b + 1] if x), key=dids[a:b + 1].count)
            pst = window_conf(p_stationary(ko, P), a, b)
            pphi = float(phi((ph - P["phi_partial_deg"]) / P["phi_sigma_deg"]))
            strict = float(np.mean(m[a:b + 1]))  # B13: conf falls when most frames are unknown-angle / slack
            conf = _conf(ko, [pst, pphi, strict, window_conf(p_reg, a, b)], a, a, b)
            stype = "behind" if ph > P["phi_behind_deg"] else "partial"
            out.append(Event("post_seal", {"post": o, "defender": d}, a, a, b, conf,
                             dict(seal_type=stype, phi_mean_deg=round(ph, 1), r=round(float(np.nanmean(ko.r[a:b + 1])), 2),
                                  strict_frac=round(strict, 2), deep_seal=in_spot("deep_seal", ko.x[a], ko.y[a]),
                                  three_second_risk=bool((b - a) * DT > P["three_sec_s"] and in_spot("three_second_lane", ko.x[a], ko.y[a])))))
    return out


@_nonzero
def detect_id_swap_risk(scene, **params_):
    """Attacker and defender centres within swap_dist_m in the paint area: identity-swap risk flag."""
    P = params("id_swap_risk", params_)
    out = []
    for o in scene.offense:
        ko = scene.k(o)
        for d in scene.defense:
            kd = scene.k(d)
            dd = M.dist(ko, kd)
            cond = np.nan_to_num((dd < P["swap_dist_m"]) & (ko.r <= P["r_max"]), nan=False).astype(bool)
            stay = np.nan_to_num((dd < P["stay_dist_m"]) & (ko.r <= P["r_max"]), nan=False).astype(bool)
            pd = p_below(dd, P["swap_dist_m"], M.sigma_dist(ko, kd))
            # B14: an ENTER run (d < swap_dist_m, small gaps bridged) needs a mean P(d < swap_dist_m) of at least
            # enter_p_min. L2-B14: min_s applies to the STAY interval, not the enter run: a 5 m/s crossing is under
            # 0.6 m for only 3 frames, and hysteresis measures (last - a) * DT, so min_s on the enter run lost it.
            enters = [(x, y) for x, y in hysteresis(cond, cond, 0.0, int(P["bridge_frames"]))
                      if window_conf(pd, x, y) >= P["enter_p_min"]]
            used = -1
            for x, _ in enters:
                if x <= used:
                    continue
                a, b, j, gap = x, x, x + 1, 0
                while j < scene.n:  # stay while d < stay_dist_m, gaps <= bridge_frames bridged
                    if stay[j]:
                        b, gap = j, 0
                    elif gap < P["bridge_frames"]:
                        gap += 1
                    else:
                        break
                    j += 1
                used = b
                while a - 1 >= 0 and stay[a - 1]:
                    a -= 1  # onset = start of the approach inside stay_dist_m
                if (b - a) * DT < P["min_s"] - 1e-9:
                    continue
                pc = window_conf(pd, a, b)
                # L4-7: relative-bearing change of d around o from flip_pad_s before the onset to flip_pad_s after the end:
                # a crossing (>= cross_deg) is the classic swap geometry; a stay on one side (post defence, box-out,
                # screen contact) is centre overlap only. Attribute for consumers; the flag itself is unchanged.
                lo, hi = max(0, a - frames(P["flip_pad_s"])), min(scene.n - 1, b + frames(P["flip_pad_s"]))
                ang = np.arctan2(kd.y[[lo, hi]] - ko.y[[lo, hi]], kd.x[[lo, hi]] - ko.x[[lo, hi]])
                flip = float(np.degrees(abs((ang[1] - ang[0] + np.pi) % (2 * np.pi) - np.pi)))
                out.append(Event("id_swap_risk", {"attacker": o, "defender": d}, a, a, b, _conf(ko, [pc], a, a, b),
                                 dict(min_dist_m=round(float(np.nanmin(dd[a:b + 1])), 2),
                                      flip_deg=round(flip, 1) if np.isfinite(flip) else None,
                                      crossed=bool(np.isfinite(flip) and flip >= P["cross_deg"]))))
    return out


@_nonzero
def detect_lob_catch_proxy(scene, **params_):
    """Lob to a big without ball height: catch at r < lob_r while moving rimward >= lob_vr_mps."""
    P = params("lob_catch_proxy", params_)
    out = []
    for pa, rel, pb, c in passes(scene, P["max_flight_s"]):
        kb = scene.k(pb)
        cr = float(np.nanmin(kb.r[c:min(scene.n, c + frames(P["catch_settle_s"]) + 1)]))
        if not cr < P["lob_r"]:
            continue  # the holder model catches ~1 m before the hands: test r up to catch_settle_s later
        a = max(0, c - frames(P["approach_s"]))
        vr = float(np.nanmean(kb.v_r[a:c + 1]))
        if not vr >= P["lob_vr_mps"]:
            continue
        pv = float(p_above(vr, P["lob_vr_mps"], float(np.nanmean(_sig_v(kb)[a:c + 1]))))
        pr = float(p_below(cr, P["lob_r"], _sig_p(kb)[c]))
        out.append(Event("lob_catch_proxy", {"passer": pa, "receiver": pb}, c, rel, c, _conf(kb, [pv, pr], c, a, c),
                         dict(release_frame=rel, mean_v_r=round(vr, 2), catch_r=round(cr, 2))))
    return out


# --------------------------------------------------------------------------------------
# Screener post-actions
# --------------------------------------------------------------------------------------
def _roll_window(P, r0):
    """Distance-scaled roll window T_roll = clamp(t_base + (r0 - rim_r) / travel, t_min, t_max)."""
    return _clamp(P["t_base_s"] + (r0 - P["rim_r"]) / P["travel_mps"], P["t_min_s"], P["t_max_s"])


def _roll_start(scene, f, P):
    k = scene.k(f.s)
    lo, hi = f.t0 - frames(P["onset_before_s"]), f.t0 + frames(P["onset_after_s"])
    return gate_onset(k.v_r, P["v_r_gate_mps"], frames(P["gate_window_s"]) + 1, lo, hi)


def _slip_onset(k, f):
    """L4-6: slip's onset gate (a 0.5 s window starting in [t_rel - onset_before_s, t_rel + onset_after_s] with mean v_r
    >= slip v_r_gate_mps). An 'early' release WITHOUT it is not a slip (the screener left a few frames before the use
    but accelerated like a roller), so roll accepts it."""
    Ps = params("slip")
    a, _ = gate_onset(k.v_r, Ps["v_r_gate_mps"], frames(Ps["gate_window_s"]) + 1, f.t_rel - frames(Ps["onset_before_s"]),
                      f.t_rel + frames(Ps["onset_after_s"]))
    return a


@_nonzero
def detect_roll(scene, screens=None, **params_):
    """Roll: post-use rimward release, window-mean v_r gate, then r <= rim_r (or a catch) inside T_roll
    counted from t_rel (B3: a hold / pivot after the screen moment no longer eats the travel budget)."""
    P = params("roll", params_)
    out = []
    for ev in _screens(screens, ("ball", "dho", "off_ball")):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.first_move != "rimward":
            continue
        k = scene.k(f.s)
        if f.release != "post_use" and not (P["early_without_slip_gate"] and f.release == "early" and _slip_onset(k, f) is None):
            continue
        a, vr_mean = _roll_start(scene, f, P)
        if a is None:
            continue
        T = _roll_window(P, f.r0)
        end = min(scene.n - 1, f.t_rel + frames(T))
        comp = _first(np.nan_to_num(k.r <= P["rim_r"], nan=False).astype(bool), a, end)
        via = "rim"
        if comp is None:  # completion by a catch in stride near the rim
            for c in catches(scene, f.s):
                if a <= c <= end and k.r[c] <= P["catch_r"] and k.v_r[c] >= P["catch_vr_mps"]:
                    comp, via = c, "catch"
                    break
        if comp is None:
            continue
        # B6: the drop needed is capped by the distance to the rim zone, and is read a little past the first
        # frame inside it (at the first crossing r is ~rim_r by construction, so elbow rolls failed)
        hi_d = min(end, comp + frames(P["dr_eval_after_s"]))
        dr_min = float(np.nanmin(k.r[f.t0:hi_d + 1]) - f.r0)
        if dr_min > -min(P["dr_min_m"], f.r0 - P["rim_r"]):
            continue
        runs = merge_runs(k, stationary_runs(k, P)[1], P["merge_gap_s"], P["merge_shift_m"])
        short = [(x, y) for x, y in runs if a <= x <= comp and (y - x) * DT >= P["short_stop_s"]
                 and P["rim_r"] < np.nanmean(k.r[x:y + 1]) <= P["pocket_r_max"]]
        if short:
            continue
        n_g = frames(P["gate_window_s"])
        pv = gate_conf(k, P["v_r_gate_mps"], n_g, a, comp)
        # B4: the point test is read at the extremum inside the window, not at the first crossing (where
        # r ~ rim_r and P(r < rim_r) ~ 0.5 by construction, capping every roll's conf near 0.5)
        hi_r = max(comp, end)
        i_min = a + int(np.nanargmin(k.r[a:hi_r + 1]))
        rmin = float(k.r[i_min])
        pr = float(p_below(rmin, P["rim_r"] if via == "rim" else P["catch_r"], float(_sig_p(k)[i_min])))
        conf = _conf(k, [pv, pr], f.t0, f.t_rel, comp, ev.conf)
        out.append(Event("roll", {"screener": f.s, "handler": f.h}, f.t0, f.t_rel, comp, conf,
                         dict(roll_start_frame=a, t_complete_s=round((comp - f.t0) * DT, 2), completion=via,
                              T_roll_s=round(T, 2), r_min=round(rmin, 2), mean_v_r_gate=round(vr_mean, 2),
                              peak_speed=round(float(np.nanmax(k.speed[a:comp + 1])), 2),
                              deep_roll=bool(rmin <= P["ra_r"]), ctg_roll_compat=bool(rmin <= P["ctg_roll_r"]),
                              **_frame_attrs(f))))
    return out


def _no_rimward_run(k, a, b, P):
    """True if no window of rimward_run_s has mean v_r >= rimward_mps inside [a, b]."""
    n = frames(P["rimward_run_s"]) + 1
    m = _fwd_mean(k.v_r, n)
    seg = m[a:max(a, b - n + 2)]
    return not np.any(np.nan_to_num(seg, nan=-9) >= P["rimward_mps"])


@_nonzero
def detect_short_roll(scene, screens=None, **params_):
    """Short roll: post-use rimward release that stops or catches in the pocket band (2.5, 6.0], never r <= 2.5."""
    P = params("short_roll", params_)
    out = []
    for ev in _screens(screens, ("ball", "dho")):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.release != "post_use" or f.first_move != "rimward":
            continue
        k = scene.k(f.s)
        end = min(scene.n - 1, f.t0 + frames(P["window_s"]))
        variant, tf = None, None
        sl = speed_long(k, P)
        hs = holder_seq(scene)
        for c in catches(scene, f.s):
            if f.t_rel <= c <= end and P["pocket_r_min"] < k.r[c] <= P["pocket_r_max"] and k.r[c] <= f.r0 - P["min_sink_m"]:
                # B9: a catch in stride on a full roll is a roll. The pocket catch needs a deceleration
                # around the catch, or the holder must not reach the rim zone within catch_after_s.
                w0, w1 = max(0, c - frames(P["catch_slow_before_s"])), min(scene.n - 1, c + frames(P["catch_slow_after_s"]))
                slowed = bool(np.any(np.nan_to_num(sl[w0:w1 + 1] < P["stop_speed_mps"], nan=False)))
                c1 = min(scene.n - 1, c + frames(P["catch_after_s"]))
                to_rim = any(hs[t] == f.s and np.isfinite(k.r[t]) and k.r[t] <= P["pocket_r_min"] for t in range(c, c1 + 1))
                if slowed or not to_rim:
                    variant, tf = "catch", c
                    break
        if variant is None:
            slow = sl < P["stop_speed_mps"]
            band = np.nan_to_num((k.r > P["pocket_r_min"]) & (k.r <= P["pocket_r_max"]) & (k.r <= f.r0 - P["min_sink_m"]),
                               nan=False).astype(bool)
            cond = slow & band
            cond[:f.t_rel] = False
            # B5: the stop must START by stop_by_s (YAML); it may then run past the window end for stop_min_s
            # plus the half-support of the 1.0 s speed (the old cut at the window end truncated side-PnR stops)
            cond[min(scene.n, end + frames(P["stop_min_s"]) + 1 + frames(P["support_long_s"]) // 2):] = False
            iv = [(x, y) for x, y in hysteresis(cond, cond, P["stop_min_s"], 2) if x <= f.t0 + frames(P["stop_by_s"])]
            if iv:
                variant, tf = "stop", iv[0][0]
                stop_end = iv[0][1]
        if variant is None:
            continue
        hi = min(scene.n - 1, (tf if variant == "catch" else stop_end) + frames(P["after_s"]))
        rmin = float(np.nanmin(k.r[f.t0:hi + 1]))
        if rmin <= P["pocket_r_min"]:
            continue
        x, y = _xy(k, tf)
        pr = float(p_above(rmin, P["pocket_r_min"], float(_sig_p(k)[tf])))
        if variant == "stop":
            ps = window_conf(p_below(speed_long(k, P), P["stop_speed_mps"], _sig_v(k)), tf, stop_end)
        else:
            ps = 1.0
        conf = _conf(k, [pr, ps], f.t0, f.t_rel, hi, ev.conf)
        out.append(Event("short_roll", {"screener": f.s, "handler": f.h}, f.t0, f.t_rel, hi, conf,
                         dict(variant=variant, frame=tf, r=round(_r(x, y), 2), theta=round(math.degrees(math.atan2(y, x)), 1),
                              t_minus_t0_s=round((tf - f.t0) * DT, 2), r_min=round(rmin, 2),
                              in_short_roll_zone=in_spot("short_roll_zone", x, y), short_roll_pocket=in_spot("short_roll_pocket", x, y),
                              strict=bool(P["strict_r_min"] <= _r(x, y) <= P["strict_r_max"]),
                              trap_context=_trap(scene, f, P), **_frame_attrs(f))))
    return out


def _trap(scene, f, P):
    """Two defenders within trap_dist_m of the handler for >= trap_min_s in [t0 + 0.3, t0 + 1.0] s."""
    kh = scene.k(f.h)
    a, b = f.t0 + frames(P["trap_from_s"]), min(scene.n - 1, f.t0 + frames(P["trap_to_s"]))
    cnt = np.zeros(scene.n, dtype=int)
    for d in scene.defense:
        cnt += np.nan_to_num(M.dist(kh, scene.k(d)) <= P["trap_dist_m"], nan=False).astype(int)
    c = (cnt >= 2)
    c[:a] = False
    c[b + 1:] = False
    return bool(hysteresis(c, c, P["trap_min_s"], 1))


def _pop(scene, f, P, zone, t_from):
    """Shared pop test (E7, E16): screener's OWN displacement, no rimward run, r >= r0 - 0.75,
    arrival in `zone` within the distance-scaled T_pop from t_from (+ extension while moving out).
    Returns (arrival_frame, attrs) or (None, None)."""
    k = scene.k(f.s)
    n = scene.n
    if (t_from - f.t0) * DT > P["release_within_s"]:
        return None, None  # a hold then a late walk-out is not a pop (sim: 80% false pops without this)
    d_need = max(0.0, P["zone_r_min"] - f.r0)  # B17: zone_r_min is the radius of the item's arrival zone
    T = _clamp(P["t_base_s"] + d_need / P["travel_mps"], P["t_min_s"], P["t_max_s"])
    end = min(n - 1, t_from + frames(T))
    disp = np.hypot(k.x - f.px, k.y - f.py)
    inz = spot_mask(zone, k, t_from, min(n - 1, end + frames(P["extend_s"])))
    ok = inz & np.nan_to_num(disp >= P["disp_m"], nan=False).astype(bool)
    arr = _first(ok, t_from, end)
    extended = False
    if arr is None:  # extension while the screener is still moving outward at the window end
        vo = _c_mean(-k.v_r, frames(P["gate_window_s"]) // 2)
        if np.isfinite(vo[end]) and vo[end] >= P["outward_mps"]:
            arr = _first(ok, end, min(n - 1, end + frames(P["extend_s"])))
            extended = arr is not None
    if arr is None:
        return None, None
    if np.nanmin(k.r[t_from:arr + 1]) < f.r0 - P["r_drop_m"]:
        return None, None
    if not _no_rimward_run(k, t_from, arr, P):
        return None, None
    x, y = _xy(k, arr)
    return arr, dict(arrival_frame=arr, arrival_minus_t0_s=round((arr - f.t0) * DT, 2), T_pop_s=round(T, 2),
                     extended=extended, r_end=round(_r(x, y), 2), displacement_m=round(float(disp[arr]), 2),
                     arrival_spots=spot_labels(x, y, ["screener_pop", "top_three", "slot_three", "wing_three", "corner_three"]))


def _peak_after(scene, arr, P, arr_vals):
    """B4: (extremum value, frame) of arr_vals over [arr, arr + point_window_s] (point tests are read at the
    extremum after the first crossing, not at the crossing itself, where they sit at ~0.5 by construction)."""
    hi = min(scene.n - 1, arr + frames(P["point_window_s"]))
    seg = np.asarray(arr_vals[arr:hi + 1], dtype=float)
    if not np.any(np.isfinite(seg)):
        return float(arr_vals[arr]), arr
    i = int(np.nanargmax(seg))
    return float(seg[i]), arr + i


@_nonzero
def detect_pop_arc(scene, screens=None, **params_):
    """Pop to the arc: post-use outward/lateral release; arrives in pop_arc_zone inside T_pop from t_rel."""
    P = params("pop_arc", params_)
    out = []
    for ev in _screens(screens, ("ball", "dho")):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.release != "post_use" or f.first_move not in ("outward", "lateral"):
            continue
        arr, at = _pop(scene, f, P, "pop_arc_zone", f.t_rel)
        if arr is None:
            continue
        k = scene.k(f.s)
        x, y = _xy(k, arr)
        rpk, ipk = _peak_after(scene, arr, P, k.r)
        pz = float(p_above(rpk, P["zone_r_min"], float(_sig_p(k)[ipk])))
        dpk, idk = _peak_after(scene, arr, P, np.hypot(k.x - f.px, k.y - f.py))
        pdsp = float(p_above(dpk, P["disp_m"], float(_sig_p(k)[idk]) * math.sqrt(2)))
        conf = _conf(k, [pz, pdsp], f.t0, f.t_rel, arr, ev.conf)
        out.append(Event("pop_arc", {"screener": f.s, "handler": f.h}, f.t0, f.t_rel, arr, conf,
                         dict(pop_fast=bool((arr - f.t0) * DT <= P["fast_s"]), beyond_arc=bool(spotlib.is_three(x, y)),
                              **at, **_frame_attrs(f))))
    return out


@_nonzero
def detect_pop_mid(scene, screens=None, **params_):
    """Pop to mid-range: outward/lateral, displacement >= 1.5 m, dr >= +0.5, stop or catch in pop_mid_zone."""
    P = params("pop_mid", params_)
    out = []
    for ev in _screens(screens, ("ball", "dho")):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.release != "post_use" or f.first_move not in ("outward", "lateral") or f.r0 >= P["r0_max"]:
            continue
        k = scene.k(f.s)
        end = min(scene.n - 1, f.t0 + frames(P["window_s"]))
        disp = np.hypot(k.x - f.px, k.y - f.py)
        inz = spot_mask("pop_mid_zone", k, f.t_rel, end)
        good = inz & np.nan_to_num((disp >= P["disp_m"]) & (k.r - f.r0 >= P["dr_min_m"]), nan=False).astype(bool)
        slow = speed_long(k, P) < P["stop_speed_mps"]
        cond = good & slow
        iv = hysteresis(cond, cond, P["stop_min_s"], 2)
        tf, variant = (iv[0][0], "stop") if iv else (None, None)
        for c in catches(scene, f.s):
            if f.t_rel <= c <= end and good[c] and (tf is None or c < tf):
                tf, variant = c, "catch"
                break
        if tf is None:
            continue
        if np.any(spot_mask("pop_arc_zone", k, f.t_rel, tf)[f.t_rel:tf + 1]):
            continue  # precedence: a pop that reached the arc is pop_arc
        if np.nanmin(k.r[f.t_rel:tf + 1]) < f.r0 - P["r_drop_m"] or not _no_rimward_run(k, f.t_rel, tf, P):
            continue
        x, y = _xy(k, tf)
        # B12 / B4: displacement and dr are read at the settled position (mean over [tf, tf + settle_s]), not at
        # the first frame that crosses 1.5 m (where they sit at the threshold); a 1.22 m slide read 1.50-1.74 there
        hi_s = min(scene.n - 1, tf + frames(P["settle_s"]))
        d_set = float(np.nanmean(disp[tf:hi_s + 1]))
        dr_set = float(np.nanmean(k.r[tf:hi_s + 1])) - f.r0
        if d_set < P["disp_m"] or dr_set < P["dr_min_m"]:
            continue
        pd = float(p_above(d_set, P["disp_m"], float(_sig_p(k)[tf]) * math.sqrt(2)))
        pdr = float(p_above(dr_set, P["dr_min_m"], float(_sig_p(k)[tf]) * math.sqrt(2)))
        conf = _conf(k, [pd, pdr], f.t0, f.t_rel, tf, ev.conf)
        out.append(Event("pop_mid", {"screener": f.s, "handler": f.h}, f.t0, f.t_rel, tf, conf,
                         dict(variant=variant, frame=tf, r=round(_r(x, y), 2), dr=round(dr_set, 2),
                              displacement_m=round(d_set, 2), t_minus_t0_s=round((tf - f.t0) * DT, 2),
                              spots=spot_labels(x, y, ["elbow", "pinch_post", "short_corner", "high_short_corner", "mid_post"]),
                              **_frame_attrs(f))))
    return out


@_nonzero
def detect_slip(scene, screens=None, **params_):
    """Slip: early release (before use) to the rim (or the pocket); gate on window-mean v_r >= 2.0."""
    P = params("slip", params_)
    out = []
    for ev in _screens(screens, ("ball", "dho", "off_ball")):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.release not in ("early", "never_set") or not f.attrs["early"] or f.first_move != "rimward":
            continue
        k = scene.k(f.s)
        lo, hi = f.t_rel - frames(P["onset_before_s"]), f.t_rel + frames(P["onset_after_s"])
        a, vr_mean = gate_onset(k.v_r, P["v_r_gate_mps"], frames(P["gate_window_s"]) + 1, lo, hi)
        if a is None:
            continue
        T = _roll_window(P, f.r0)
        end = min(scene.n - 1, f.t_rel + frames(T))
        comp = _first(np.nan_to_num(k.r <= P["rim_end_r"], nan=False).astype(bool), a, end)
        dest = "rim"
        if comp is None:
            slow = speed_long(k, P) < P["stop_speed_mps"]
            band = np.nan_to_num((k.r > P["rim_r"]) & (k.r <= P["pocket_r_max"]), nan=False).astype(bool)
            c = slow & band
            c[:a] = False
            # B5 (same fix as short_roll): the pocket stop must start by the window end, it may run past it
            c[min(scene.n, end + frames(P["stop_min_s"]) + 1 + frames(P["support_long_s"]) // 2):] = False
            iv = [(x, y) for x, y in hysteresis(c, c, P["stop_min_s"], 2) if x <= end]
            if not iv:
                continue
            comp, dest = iv[0][0], "pocket"
        n_g = frames(P["gate_window_s"])
        pv = gate_conf(k, P["v_r_gate_mps"], n_g, a, comp)
        peak = float(np.nanmax(k.speed[a:comp + 1]))
        touch = False
        if f.D_h is not None:
            dd = M.dist(k, scene.k(f.D_h))
            w0, w1 = max(0, f.t_rel - frames(P["touch_window_s"])), f.t_rel
            touch = bool(np.nanmin(dd[w0:w1 + 1]) <= P["touch_dist_m"] and f.min_speed < P["never_set_speed_mps"])
        conf = _conf(k, [pv, f.p_early], f.t_rel, f.t_rel, comp, ev.conf)
        out.append(Event("slip", {"screener": f.s, "handler": f.h}, f.t_rel, f.t_rel, comp, conf,
                         dict(destination=dest, slip_type="ghost_in" if f.never_set else ("slow" if f.p_slow >= P["slow_p_min"] else "quick"),
                              lead_s=round((f.t_use - f.t_rel) * DT, 2), mean_v_r_gate=round(vr_mean, 2), peak_speed=round(peak, 2),
                              slip_strict=bool(peak >= P["strict_speed_mps"]), touch=touch,
                              r_min=round(float(np.nanmin(k.r[a:comp + 1])), 2), **_frame_attrs(f))))
    return out


@_nonzero
def detect_slip_to_arc(scene, screens=None, **params_):
    """Slip to the arc: early release with an outward first move, arc reached inside T_pop from t_rel."""
    P = params("slip_to_arc", params_)
    out = []
    for ev in _screens(screens, ("ball", "dho")):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.release not in ("early", "never_set") or not f.attrs["early"] or f.first_move != "outward":
            continue
        arr, at = _pop(scene, f, P, "pop_arc_zone", f.t_rel)
        if arr is None:
            continue
        k = scene.k(f.s)
        rpk, ipk = _peak_after(scene, arr, P, k.r)
        pz = float(p_above(rpk, P["zone_r_min"], float(_sig_p(k)[ipk])))
        # E2: a <= 0.2 s stop is often unresolvable from a pass-through; the ghost share goes to GHOST
        conf = _conf(k, [pz, f.p_early, 1.0 - f.attrs["p_never_set"]], f.t_rel, f.t_rel, arr, ev.conf)
        out.append(Event("slip_to_arc", {"screener": f.s, "handler": f.h}, f.t_rel, f.t_rel, arr, conf,
                         dict(t_arrival_minus_t_rel_s=round((arr - f.t_rel) * DT, 2), **at, **_frame_attrs(f))))
    return out


def _turn_deg(k, t, pre, post):
    """Heading change (deg) between the displacement over [t - pre, t] and over [t, t + post] (smoothed track)."""
    a0, b1 = max(0, t - pre), min(len(k.x) - 1, t + post)
    h1 = math.atan2(k.y[t] - k.y[a0], k.x[t] - k.x[a0])
    h2 = math.atan2(k.y[b1] - k.y[t], k.x[b1] - k.x[t])
    dh = abs((h2 - h1 + math.pi) % (2 * math.pi) - math.pi)
    return math.degrees(dh) if math.isfinite(dh) else float("nan")


@_nonzero
def detect_ghost(scene, screens=None, **params_):
    """Ghost: an attacker runs at the ball handler (or his defender) and leaves without ever stopping."""
    P = params("ghost", params_)
    Pf = params("screen_frame", params_)  # never_set_half_s / never_set_sigma_mps live under screen_frame (B17)
    out = []
    n = scene.n
    hold = holder_seq(scene)
    for s in scene.offense:
        ks = scene.k(s)
        sl = speed_long(ks, P)
        last = _NEVER
        # full length of each slow run (a run that starts before the never-set window still counts in full: a
        # screener who held a 1 s set and then walks past the handler is not a ghost)
        slow_len = run_lengths(np.nan_to_num(ks.speed < P["never_set_speed_mps"], nan=True).astype(bool))
        max_slow = tiered(P, "never_set_slow_frames", ks)
        for h in scene.offense:
            if h == s:
                continue
            kh = scene.k(h)
            d = M.dist(ks, kh)
            close = M.closing_speed(ks, kh)
            with np.errstate(invalid="ignore", divide="ignore"):
                appr = (ks.vx * (kh.x - ks.x) + ks.vy * (kh.y - ks.y)) / d
            sep = _fwd_mean(-close, frames(P["gate_window_s"]) + 1)  # B7: separation speed from h
            vo = _fwd_mean(-ks.v_r, frames(P["gate_window_s"]) + 1)
            for tc in range(1, n - 1):
                if not (np.isfinite(d[tc]) and d[tc] <= d[tc - 1] and d[tc] <= d[tc + 1]):
                    continue
                if tc - last < frames(P["dedupe_s"]):
                    continue
                w0, w1 = max(0, tc - frames(Pf["never_set_half_s"])), min(n - 1, tc + frames(Pf["never_set_half_s"]))
                if np.mean([hold[t] == h for t in range(w0, w1 + 1)]) < P["hold_frac"]:
                    continue
                Dh, _ = nearest_defender(scene, h, tc - frames(P["dh_window_s"]), tc)
                ddh = M.dist(ks, scene.k(Dh))[tc] if Dh else np.inf
                # L2-B7: approach distances and closing speed are tier-aware. At sigma_p 0.5 the smoother (q = 10)
                # cuts the corner of a sharp turn by 0.7-1.0 m (true 1.35 m to h reads 2.0-2.4 m) and the closing
                # speed into the corner reads 1.0-1.45 m/s instead of ~3.
                ah, adh = tiered(P, "approach_h_m", ks), tiered(P, "approach_dh_m", ks)
                if not (d[tc] <= ah or ddh <= adh):
                    continue
                a0 = max(0, tc - frames(P["approach_s"]))
                cl = float(np.nanmean(close[a0:tc]))
                if not cl >= tiered(P, "closing_mps", ks):
                    continue
                # L4-3: the SCREENER runs at the handler: his own velocity component toward h must supply at least
                # screener_share_min of the closing speed (a handler driving past a standing teammate closes the gap too)
                if not float(np.nanmean(appr[a0:tc])) >= P["screener_share_min"] * cl:
                    continue
                if ks.r[tc] > kh.r[tc] + P["farther_m"]:
                    continue  # McQueen geometry: screener not > 2 ft farther from the basket than the handler
                # L4-3: a ghost is a half-court action: a teammate running past the handler in the backcourt (transition)
                # is not a fake screen
                if in_spot("backcourt", kh.x[tc], kh.y[tc]) or in_spot("backcourt", ks.x[tc], ks.y[tc]):
                    continue
                # L2-B7: never set = no run of CA-RTS speed < never_set_speed_mps longer than never_set_slow_frames
                # (tier-aware) within +-never_set_half_s. The old tests (min speed >= 1.0 and no stationary run)
                # failed every sharp reversal: the smoother rounds a 150 deg turn at 3 m/s into a 0.26-0.97 m/s
                # minimum and an s2-stationary blip, the same reading as a real 0.3 s stop. The DURATION of the slow
                # reading separates them: reversal 0-0.13 s median, real 0.5 s set 0.17-0.37 s (sigma 0.2-0.3).
                slow = int(slow_len[w0:w1 + 1].max())
                if slow > max_slow:
                    continue
                # L4-8: a ghost runs AT the handler and leaves in another direction (a fake set is a corner of the
                # path); a run straight past him is a cut or a transition run. The corner is searched within
                # +-turn_search_s of t_closest (the closest approach to h is not at the corner of the path)
                ts = frames(P["turn_search_s"])
                turn = max((_turn_deg(ks, u, frames(P["turn_pre_s"]), frames(P["turn_post_s"]))
                            for u in range(max(0, tc - ts), min(n - 1, tc + ts) + 1)), default=float("nan"))
                if not turn >= P["turn_min_deg"]:
                    continue
                # exit
                ex_end = min(n - 1, tc + frames(P["exit_s"]))
                sub, tf = None, None
                ain, _ = gate_onset(ks.v_r, P["in_v_r_mps"], frames(P["gate_window_s"]) + 1, tc - frames(P["in_lead_s"]), ex_end)
                if ain is not None:
                    tf = _first(np.nan_to_num(ks.r <= P["in_r"], nan=False).astype(bool), ain, min(n - 1, tc + frames(P["arrive_s"])))
                    sub = "in" if tf is not None else None
                if sub is None:
                    # B7: 'out' = moves away from h (any direction that is not rimward) to the arc. A fade along
                    # the arc is mostly lateral (outward v_r ~ 1.0 m/s), so the separation speed from h counts too.
                    away = max(np.nanmax(np.nan_to_num(vo[tc:ex_end + 1], nan=-9)),
                               np.nanmax(np.nan_to_num(sep[tc:ex_end + 1], nan=-9)))
                    if away >= P["out_mps"]:
                        disp = np.hypot(ks.x - ks.x[tc], ks.y - ks.y[tc])
                        arr_end = min(n - 1, tc + frames(P["arrive_s"]))
                        okz = spot_mask("pop_arc_zone", ks, tc, arr_end) & np.nan_to_num(disp >= P["disp_m"], nan=False).astype(bool)
                        tf = _first(okz, tc, arr_end)
                        sub = "out" if tf is not None else None
                        if sub is None:
                            okm = spot_mask("pop_mid_zone", ks, tc, arr_end) & (sl < P["stop_speed_mps"])
                            tf = _first(okm, tc, arr_end)
                            sub = "mid" if tf is not None else None
                if sub is None:
                    continue
                psp = float(phi((max_slow + 1 - slow) / P["never_set_slow_sigma_frames"]))
                pd = float(p_below(min(d[tc] - ah, ddh - adh), 0.0,
                                   float(M.sigma_dist(ks, kh)[tc])))
                conf = _conf(ks, [psp, pd], tc, w0, tf)
                out.append(Event("ghost", {"screener": s, "handler": h, "handler_defender": Dh}, tc, a0, tf, conf,
                                 dict(subtype=sub, d_min_to_h=round(float(d[tc]), 2), d_min_to_Dh=round(float(ddh), 2),
                                      min_speed=round(float(np.nanmin(ks.speed[w0:w1 + 1])), 2), arrival_frame=tf)))
                last = tc
    return out


@_nonzero
def detect_seal(scene, screens=None, **params_):
    """Hostage / Gortat seal: roll start, then a stationary seal at 1.5 <= r <= 3.5 on a defender."""
    P = params("seal", params_)
    Pr = params("roll")
    out = []
    for ev in _screens(screens, ("ball", "dho")):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.t_rel is None or f.first_move != "rimward":
            continue
        a, _ = _roll_start(scene, f, Pr)
        if a is None:
            continue
        ks = scene.k(f.s)
        runs = merge_runs(ks, stationary_runs(ks, P)[1], P["merge_gap_s"], P["merge_shift_m"])
        # B2: the window is distance-scaled like T_roll / T_pop (travel from r_s0 to the seal band edge),
        # so seals after wing and top screens are reachable; plus min_s for the held run to register
        within = _clamp(P["t_base_s"] + (f.r0 - P["r_max"]) / P["travel_mps"], P["t_min_s"], P["t_max_s"]) + P["min_s"]
        hit = None
        for x, y in runs:
            if a <= x <= a + frames(within) and (y - x) * DT >= P["min_s"]:
                rr = float(np.nanmean(ks.r[x:y + 1]))
                if P["r_min"] <= rr <= P["r_max"]:
                    hit = (x, y)
                    break
        if hit is None:
            continue
        x0, x1 = hit
        d, dd = nearest_defender(scene, f.s, x0, x1)
        if d is None or dd > P["def_m"]:
            continue
        sp = (float(np.nanmean(ks.x[x0:x1 + 1])), float(np.nanmean(ks.y[x0:x1 + 1])))
        kd = scene.k(d)
        # beneficiary: handler or a cutter passes within ben_m of the seal point toward r < ben_r
        ben = None
        bend = min(scene.n - 1, x0 + frames(P["ben_s"]))
        for q in [f.h] + [o for o in scene.offense if o not in (f.s, f.h)]:
            kq = scene.k(q)
            near = np.hypot(kq.x - sp[0], kq.y - sp[1]) <= P["ben_m"]
            deep = kq.r < P["ben_r"]
            if _first(np.nan_to_num(near & deep, nan=False).astype(bool), x0, bend) is not None:
                ben = q
                break
        if ben is None:
            continue
        kb = scene.k(ben)
        dsp = float(np.nanmean(kd.speed[x0:x1 + 1]))
        dh = M.dist(kd, kb)
        blocked = dsp < P["def_speed_mps"] or not (dh[min(bend, x1)] < dh[x0] - P["pin_shrink_m"])
        if not blocked:
            continue
        pst = window_conf(p_stationary(ks, P), x0, x1)
        pdist = float(p_below(dd, P["def_m"], float(np.nanmean(M.sigma_dist(ks, kd)[x0:x1 + 1]))))
        conf = _conf(ks, [pst, pdist], x0, x0, x1, ev.conf)
        out.append(Event("seal", {"screener": f.s, "defender": d, "beneficiary": ben}, x0, x0, x1, conf,
                         dict(seal_spot=(round(sp[0], 2), round(sp[1], 2)), r=round(_r(*sp), 2), seal_dwell_s=round((x1 - x0) * DT, 2),
                              seal_window_s=round(within, 2),
                              defender_role="screener_defender" if d == f.D_s else "help", roll_start_frame=a, **_frame_attrs(f))))
    return out


@_nonzero
def detect_crash(scene, screens=None, shots=None, **params_):
    """Crash: screener holds (< 1.0 m net), a teammate's FGA within 3.0 s, then a rimward burst."""
    P = params("crash", params_)
    out = []
    fgas = fga_events(scene, shots, P)
    for ev in _screens(screens, ("ball", "dho")):
        f = screen_frame(scene, ev, **params_)
        if f is None:
            continue
        k = scene.k(f.s)
        for shooter, tf, src in fgas:
            if shooter == f.s or not (f.t0 <= tf <= f.t0 + frames(P["fga_within_s"])):
                continue
            net = math.hypot(k.x[tf] - f.px, k.y[tf] - f.py)
            if net >= P["held_m"]:
                continue
            a, vr = gate_onset(k.v_r, P["v_r_gate_mps"], frames(P["gate_window_s"]) + 1, tf, tf + frames(P["after_s"]))
            if a is None:
                continue
            b = min(scene.n - 1, a + frames(P["gate_window_s"]))
            pv = gate_conf(k, P["v_r_gate_mps"], frames(P["gate_window_s"]), a, tf + frames(P["after_s"]))
            ph = float(p_below(net, P["held_m"], float(_sig_p(k)[tf]) * math.sqrt(2)))
            conf = _conf(k, [pv, ph], tf, f.t0, b, ev.conf * (1.0 if src == "event" else P["proxy_factor"]))
            out.append(Event("crash", {"screener": f.s, "shooter": shooter}, tf, f.t0, b, conf,
                             dict(fga_source=src, t_fga_minus_t0_s=round((tf - f.t0) * DT, 2), r_at_fga=round(float(k.r[tf]), 2),
                                  r_min_after=round(float(np.nanmin(k.r[tf:b + 1])), 2), mean_v_r=round(vr, 2), **_frame_attrs(f))))
            break
    return out


@_nonzero
def detect_move_to_screen(scene, screens=None, **params_):
    """Move to screen: the same screener sets another screen whose set starts <= 2.0 s after t_rel."""
    P = params("move_to_screen", params_)
    out = []
    evs = sorted(_screens(screens, ("ball", "dho", "off_ball")), key=lambda e: e.t0)
    for i, ea in enumerate(evs):
        fa = screen_frame(scene, ea, **params_)
        if fa is None:
            continue
        for eb in evs[i + 1:]:
            if eb.actors.get("screener") != fa.s:
                continue
            fb = screen_frame(scene, eb, **params_)
            if fb is None:
                continue
            rel = fa.t_rel if fa.t_rel is not None else fa.t0
            set_b = fb.t_set if fb.t_set is not None else fb.t0
            gap = (set_b - rel) * DT
            if not (0 <= gap <= P["within_s"]) and not (fb.t0 - fa.t0) * DT <= P["within_s"]:
                break
            moved = math.hypot(fb.px - fa.px, fb.py - fa.py)
            same_user = fb.h == fa.h
            if same_user and moved <= P["rescreen_split_m"]:
                break  # CTG: same screen
            k = scene.k(fa.s)
            pm = 1.0
            if same_user:  # B12: a re-screen must have moved beyond the CTG split with >= 50% probability
                sig_ps = math.sqrt(float(_sig_p(k)[fa.t0]) ** 2 + float(_sig_p(k)[fb.t0]) ** 2)
                pm = float(p_above(moved, P["rescreen_split_m"], sig_ps))
                if pm < P["rescreen_p_min"]:
                    break
            sub = "veer" if fb.cls == "off_ball" else ("twist" if same_user and np.sign(fb.px) != np.sign(fa.px) else
                                                      ("re_screen" if same_user else "new_user"))
            pg = float(phi((P["within_s"] - max(gap, 0.0)) / P["gap_sigma_s"]))
            conf = _conf(k, [pg, pm], fb.t0, fa.t0, fb.t0, min(ea.conf, eb.conf))
            out.append(Event("move_to_screen", {"screener": fa.s, "first_user": fa.h, "second_user": fb.h}, fb.t0, fa.t0, fb.t0,
                             conf, dict(subtype=sub, gap_s=round(gap, 2), moved_m=round(moved, 2), first_screen_t0=fa.t0)))
            break
    return out


@_nonzero
def detect_roll_into_post(scene, screens=None, **params_):
    """Roll (or lateral release) into a post seal within 2.5 s: deep (r <= 3.5) or mid_post (3.5-5.0)."""
    P = params("roll_into_post", params_)
    out = []
    for ev in _screens(screens, ("ball", "dho")):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.t_rel is None or f.first_move not in ("rimward", "lateral"):
            continue
        ks = scene.k(f.s)
        # B3: distance-scaled from t_rel (travel from r_s0 to the deep-post edge) + min_s for the seal itself
        T = _clamp(P["t_base_s"] + (f.r0 - P["deep_r"]) / P["travel_mps"], P["t_min_s"], P["t_max_s"]) + P["min_s"]
        end = min(scene.n - 1, f.t_rel + frames(T))

        def region(x, y):
            rr = _r(x, y)
            return (rr <= P["deep_r"] and in_spot("post_area", x, y)) or \
                (P["deep_r"] < rr <= P["mid_r"] and in_any(("mid_post", "elbow", "pinch_post"), x, y))

        m, unk, loose, cand, dids, phis = _seal_mask(scene, f.s, region, P, P["phi_partial_deg"])
        for arr in (m, unk, loose, cand):
            arr[:f.t_rel] = False
        iv = [(a, b) for a, b in seal_intervals(m, unk, cand, P, P["min_s"]) if a <= end]
        if not iv:
            continue
        a, b = iv[0]
        rr = float(np.nanmean(ks.r[a:b + 1]))
        d = max(set(x for x in dids[a:b + 1] if x), key=dids[a:b + 1].count)
        pst = window_conf(p_stationary(ks, P), a, b)
        pphi = float(phi((float(np.nanmean(phis[a:b + 1])) - P["phi_partial_deg"]) / P["phi_sigma_deg"]))
        conf = _conf(ks, [pst, pphi, float(np.mean(m[a:b + 1]))], a, a, b, ev.conf)
        out.append(Event("roll_into_post", {"screener": f.s, "defender": d}, a, f.t_rel, b, conf,
                         dict(subtype="deep_post" if rr <= P["deep_r"] else "mid_post", r=round(rr, 2),
                              switch_flag=bool(f.D_s is not None and d != f.D_s), **_frame_attrs(f))))
    return out


@_nonzero
def detect_spain_pop(scene, screens=None, **params_):
    """Spain back-screener's pop to spain_pop_spot after the back screen (screen_type 'spain')."""
    P = params("spain_pop", params_)
    out = []
    for ev in [e for e in (screens or []) if e.kind == "screen" and e.attrs.get("screen_type") == "spain"]:
        f = screen_frame(scene, ev, **params_)
        if f is None or f.t_rel is None or f.first_move not in ("outward", "lateral"):
            continue
        arr, at = _pop(scene, f, P, "spain_pop_spot", f.t_rel)
        if arr is None:
            continue
        k = scene.k(f.s)
        dpk, ipk = _peak_after(scene, arr, P, np.hypot(k.x - f.px, k.y - f.py))
        pz = float(p_above(dpk, P["disp_m"], float(_sig_p(k)[ipk]) * math.sqrt(2)))
        out.append(Event("spain_pop", {"screener": f.s, "user": f.h}, f.t0, f.t_rel, arr, _conf(k, [pz], f.t0, f.t_rel, arr, ev.conf),
                         dict(**at, **_frame_attrs(f))))
    return out


# --------------------------------------------------------------------------------------
# Big-man actions not tied to one screen
# --------------------------------------------------------------------------------------
@_nonzero
def detect_dive(scene, screens=None, bigs=None, **params_):
    """Dive: a big without the ball from r >= 3.5 to r <= 2.0 (v_r >= 2.0 window mean), with a context event."""
    P = params("dive", params_)
    out = []
    evs = list(screens or [])
    # B15: horns alignment from the mean position over the first catch_mean_s of the holder run (one noisy
    # catch frame fell outside the elbow), any of context_spots
    elbow_catches = []
    for pid, c0, c1 in holder_runs(scene):
        if c0 == 0:
            continue
        kp = scene.k(pid)
        c2 = min(c1, c0 + frames(P["catch_mean_s"]))
        mx, my = float(np.nanmean(kp.x[c0:c2 + 1])), float(np.nanmean(kp.y[c0:c2 + 1]))
        if in_any(P["context_spots"], mx, my):
            elbow_catches.append((pid, c0))
    hs = holder_seq(scene)
    for b in scene.offense:
        if bigs is not None and b not in bigs:
            continue
        k = scene.k(b)
        n_g = frames(P["gate_window_s"]) + 1
        m = _fwd_mean(k.v_r, n_g)
        t = 0
        while t < scene.n:
            if not (np.isfinite(m[t]) and m[t] >= P["v_r_gate_mps"]):
                t += 1
                continue
            onset = run_start(k.v_r, P["onset_v_r_mps"], t)
            r_start = float(k.r[onset])
            T = max(P["window_s"], _roll_window(params("roll"), r_start))
            end = min(scene.n - 1, onset + frames(T))
            arr = _first(np.nan_to_num(k.r <= P["end_r"], nan=False).astype(bool), t, end)
            if r_start < P["start_r"] or arr is None or any(hs[x] == b for x in range(onset + frames(P["handoff_grace_s"]), arr + 1)):
                t += n_g
                continue
            dx, dy = k.x[arr] - k.x[onset], k.y[arr] - k.y[onset]
            disp = math.hypot(dx, dy)
            ang = _angle_at((k.x[onset], k.y[onset]), (k.x[onset] + dx, k.y[onset] + dy), (0.0, 0.0))
            if disp < P["disp_m"] or not ang <= P["angle_deg"]:
                t = arr + 1
                continue
            # context: ball screens by b are rolls/slips (excluded); DHO/off-ball screen by b, or Horns
            sub = None
            for e in evs:
                if e.kind != "screen":
                    continue
                dt_ = (onset - e.t0) * DT
                cls = screen_class(e)
                if e.actors.get("screener") == b and cls == "ball" and -P["context_s"] <= dt_ <= P["exclude_after_s"]:
                    sub = "excluded_roll"
                    break
                if e.actors.get("screener") == b and -P["context_before_s"] <= dt_ <= P["context_s"]:
                    sub = "dho_dive" if cls == "dho" else "screen_dive"
                elif e.actors.get("screener") != b and cls == "ball" and -P["context_before_s"] <= dt_ <= P["context_s"] and sub is None:
                    sub = "horns_dive"
            if sub is None:
                for pid, c in elbow_catches:
                    if pid != b and -P["context_before_s"] <= (onset - c) * DT <= P["context_s"]:
                        sub = "horns_dive"
            if sub is None or sub == "excluded_roll":
                t = arr + 1
                continue
            pv = gate_conf(k, P["v_r_gate_mps"], n_g - 1, t, arr)
            pr = float(p_below(k.r[arr], P["end_r"], float(_sig_p(k)[arr])))
            out.append(Event("dive", {"big": b}, onset, onset, arr, _conf(k, [pv, pr], onset, onset, arr),
                             dict(subtype=sub, start_r=round(r_start, 2), end_r=round(float(k.r[arr]), 2),
                                  t_to_arrival_s=round((arr - onset) * DT, 2), angle_deg=round(ang, 1),
                                  peak_speed=round(float(np.nanmax(k.speed[onset:arr + 1])), 2))))
            t = arr + 1
    return out


@_nonzero
def detect_rim_run(scene, transitions=None, bigs=None, v_peak=None, **params_):
    """Rim run: own rim (r_own <= 4) to attacked rim (r <= 2.5), net -dy >= 18 m, mean |x| <= 3, fast."""
    P = params("rim_run", params_)
    out = []
    v_peak = v_peak or {}
    pcs = sorted(int(e.t0) for e in (transitions or []) if e.kind == "possession_change")
    for b in scene.offense:
        if bigs is not None and b not in bigs:
            continue
        k = scene.k(b)
        r_own = np.hypot(k.x, k.y - OWN_RIM_Y)
        near_own = np.nan_to_num(r_own <= P["start_r_own"], nan=False).astype(bool)
        at_rim = np.nan_to_num(k.r <= P["end_r"], nan=False).astype(bool)
        t = 0
        while t < scene.n:
            arr = _first(at_rim, t, scene.n - 1)
            if arr is None:
                break
            dep = None
            for u in range(arr, -1, -1):
                if near_own[u]:
                    dep = u
                    break
            if dep is None:
                t = arr + frames(P["skip_s"])
                continue
            dy = float(k.y[dep] - k.y[arr])
            mx = float(np.nanmean(np.abs(k.x[dep:arr + 1])))
            plen = float(np.nansum(np.hypot(np.diff(k.x[dep:arr + 1]), np.diff(k.y[dep:arr + 1]))))
            vp = v_peak.get(b, P["v_peak_prior_mps"])
            n15 = frames(P["speed_window_s"]) + 1
            ms = _fwd_mean(k.speed, n15)[dep:max(dep + 1, arr - n15 + 2)]
            best = float(np.nanmax(ms)) if np.any(np.isfinite(ms)) else float("nan")
            gate = P["v_frac"] * vp
            if not (dy >= P["net_dy_m"] and mx <= P["mean_abs_x_m"] and best >= gate):
                t = arr + frames(P["skip_s"])
                continue
            t0 = dep
            for pc in pcs:
                if dep - frames(P["pc_before_s"]) <= pc <= arr:
                    t0 = pc
                    break
            n20 = frames(P["repo_window_s"]) + 1
            ms2 = _fwd_mean(k.speed, n20)[dep:max(dep + 1, arr - n20 + 2)]
            repo = bool(np.any(np.nan_to_num(ms2, nan=0) >= P["repo_speed_mps"]))
            before_ball = None
            if scene.ball is not None:
                br = np.hypot(scene.ball.x, scene.ball.y)
                tb = _first(np.nan_to_num(br < P["ball_arc_r"], nan=False).astype(bool), dep, scene.n - 1)
                before_ball = tb is None or arr <= tb + frames(P["after_ball_s"])
                if before_ball is False:
                    t = arr + frames(P["skip_s"])
                    continue
            # sigma of a speed_window_s mean: ~one independent look per gate_window_s of smoothed speed
            ps = float(p_above(best, gate, float(np.nanmedian(_sig_v(k)[dep:arr + 1]))
                               / math.sqrt(max(n15 / frames(P["gate_window_s"]), 1))))
            conf = _conf(k, [ps], max(t0, dep), dep, arr, P["prior_factor"] if b not in v_peak else 1.0)
            out.append(Event("rim_run", {"big": b}, t0, dep, arr, conf,
                             dict(net_dy_m=round(dy, 2), path_m=round(plen, 2), mean_abs_x=round(mx, 2),
                                  t_to_arrival_s=round((arr - dep) * DT, 2), best_1p5s_speed=round(best, 2),
                                  frac_of_peak=round(best / vp, 2), v_peak_source="player" if b in v_peak else "prior",
                                  rim_run_repo=repo, before_ball=before_ball, departure_frame=dep)))
            t = arr + frames(P["dedupe_s"])
    return out


@_nonzero
def detect_dunker_relocation(scene, screens=None, **params_):
    """Dunker relocation: a dunker-spot big moves >= 1.2 m to a new label when a teammate attacks the paint."""
    P = params("dunker_relocation", params_)
    out = []
    n = scene.n
    trig = []  # (frame, attacker) paint entries moving rimward
    for q in scene.offense:
        kq = scene.k(q)
        inp = spot_mask("paint", kq)
        vr = _fwd_mean(kq.v_r, frames(P["gate_window_s"]) + 1)
        for t in range(frames(P["out_before_s"]), n):
            if inp[t] and not inp[t - 1] and np.mean(~inp[t - frames(P["out_before_s"]):t]) >= P["out_frac"] \
                    and np.nanmean(np.nan_to_num(vr[max(0, t - frames(P["entry_vr_window_s"])):t + 1], nan=0)) >= P["entry_v_r_mps"]:
                trig.append((t, q))
    for kid in scene.offense:
        kk = scene.k(kid)
        dmask = spot_mask("dunker_spot", kk)
        last = _NEVER
        for t_trig, q in sorted(trig):
            if q == kid or t_trig - last < frames(P["dedupe_s"]):
                continue
            a0, a1 = t_trig - frames(P["dwell_s"] + P["pre_s"]), t_trig - frames(P["pre_s"])
            if a0 < 0 or np.mean(dmask[a0:a1 + 1]) < P["dwell_frac"]:
                continue
            sx, sy = float(np.nanmean(kk.x[a0:a1 + 1])), float(np.nanmean(kk.y[a0:a1 + 1]))
            w0, w1 = t_trig - frames(P["pre_s"]), min(n - 1, t_trig + frames(P["post_s"]))
            disp = np.hypot(kk.x - sx, kk.y - sy)
            tm = _first(np.nan_to_num(disp >= P["move_m"], nan=False).astype(bool), w0, w1)
            if tm is None:
                continue
            mask_stat, _ = stationary_runs(kk, P)
            te = _first(mask_stat, tm, min(n - 1, tm + frames(P["settle_s"])))
            te = te if te is not None else min(n - 1, tm + frames(P["settle_s"]))
            ex, ey = _xy(kk, te)
            sub = None
            if np.sign(ex) != np.sign(sx) and in_any(("dunker_spot", "low_post"), ex, ey):
                cross = [kk.y[t] for t in range(w0, te + 1) if abs(kk.x[t]) < P["slide_x_m"]]
                sub = "slide" if cross and min(cross) < P["slide_cross_y"] else None
            elif in_any(("duck_in", "restricted_area", "lane_middle"), ex, ey):
                sub = "up_lane"
            elif in_any(("short_corner", "high_short_corner"), ex, ey):
                sub = "to_short_corner"
            elif in_spot("upper_dunker", sx, sy) and in_spot("baseline_dunker", ex, ey):
                sub = "to_baseline_hide"
            elif in_spot("corner_three", ex, ey):
                sub = "lift_to_corner"
            if sub is None:
                continue
            pdm = float(p_above(disp[te], P["move_m"], float(_sig_p(kk)[te]) * math.sqrt(2)))
            pdw = float(np.mean(dmask[a0:a1 + 1]))
            out.append(Event("dunker_relocation", {"dunker": kid, "trigger": q}, t_trig, a0, te, _conf(kk, [pdm, pdw], t_trig, a0, te),
                             dict(subtype=sub, start=(round(sx, 2), round(sy, 2)), end=(round(ex, 2), round(ey, 2)),
                                  moved_m=round(float(disp[te]), 2), t_minus_trig_s=round((tm - t_trig) * DT, 2),
                                  trigger_kind="paint_entry")))
            last = t_trig
    # pre-screen angle_short: arrives in the dunker spot <= 1.0 s before a same-side ball screen and dwells >= 0.5 s
    for ev in _screens(screens, ("ball",)):
        s = ev.actors.get("screener")
        if s not in scene.kins:
            continue
        sx = scene.k(s).x[ev.t0]
        for kid in scene.offense:
            if kid in (s, ev.actors.get("user")):
                continue
            kk = scene.k(kid)
            dm = spot_mask("dunker_spot", kk, max(0, ev.t0 - frames(P["angle_short_before_s"]) - frames(P["angle_short_lookback_s"])), ev.t0)
            a0 = ev.t0 - frames(P["dwell_s"])
            if a0 < 0 or np.mean(dm[a0:ev.t0 + 1]) < P["dwell_frac"] or np.sign(kk.x[ev.t0]) != np.sign(sx):
                continue
            arr = a0
            while arr > 0 and dm[arr - 1]:
                arr -= 1
            if (ev.t0 - arr) * DT > P["angle_short_before_s"]:
                continue
            out.append(Event("dunker_relocation", {"dunker": kid, "screener": s}, ev.t0, arr, ev.t0,
                             _conf(kk, [float(np.mean(dm[a0:ev.t0 + 1]))], ev.t0, arr, ev.t0, ev.conf),
                             dict(subtype="angle_short", arrival_frame=arr)))
    return out


@_nonzero
def detect_duck_in(scene, **params_):
    """Duck-in: a post player steps to the lane middle on a ball reversal and seals his defender."""
    P = params("duck_in", params_)
    out = []
    n = scene.n
    if scene.ball is None:
        return out
    bx = np.array([ball_xy(scene, t)[0] for t in range(n)])
    by = np.array([ball_xy(scene, t)[1] for t in range(n)])
    trig = []
    for t in range(1, n):
        if np.isfinite(bx[t]) and abs(bx[t]) < P["reversal_x_m"] and by[t] >= P["ball_min_y"]:
            back = bx[max(0, t - frames(P["reversal_from_s"])):t]
            if np.any(np.nan_to_num(np.abs(back), nan=0) >= P["reversal_x_m"]) and abs(bx[t - 1]) >= P["reversal_x_m"]:
                trig.append(t)
    start_spots = ("low_post", "block_zone", "dunker_spot", "mid_post", "deep_seal")
    hs = holder_seq(scene)
    for o in scene.offense:
        ko = scene.k(o)
        for tt in trig:
            a, b = tt - frames(P["before_s"]), min(n - 1, tt + frames(P["after_s"]))
            if a < 0 or hs[tt] == o:
                continue
            sx, sy = _xy(ko, a)
            if not (_r(sx, sy) <= P["start_r"] and in_any(start_spots, sx, sy)):
                continue
            tgt = np.array([in_any(("duck_in", "lane_middle"), ko.x[t], ko.y[t]) if a <= t <= b else False for t in range(n)])
            dsp = np.hypot(ko.x - sx, ko.y - sy)
            ok = tgt & np.nan_to_num((dsp >= P["move_m"]) & (np.abs(ko.x) - abs(sx) <= -P["dx_m"]) & (ko.y - sy <= P["dy_max_m"]),
                                     nan=False).astype(bool)
            ta = _first(ok, a, b)
            if ta is None:
                continue
            # seal at the end: defender within seal_def_m with defender-o-ball angle >= phi_deg, >= seal_s
            seal = np.zeros(n, dtype=bool)
            for t in range(ta, min(n, ta + frames(P["seal_check_s"]))):
                d, dd = nearest_defender(scene, o, t, t)
                if d is None or dd > P["seal_def_m"]:
                    continue
                ph = _angle_at(_xy(ko, t), _xy(scene.k(d), t), ball_xy(scene, t))
                seal[t] = np.isfinite(ph) and ph >= P["phi_deg"]
            iv = hysteresis(seal, seal, P["seal_s"], 2)
            if not iv:
                continue
            pm = float(p_above(dsp[ta], P["move_m"], float(_sig_p(ko)[ta]) * math.sqrt(2)))
            psl = float(np.mean(seal[iv[0][0]:iv[0][1] + 1]))
            out.append(Event("duck_in", {"post": o}, tt, a, iv[0][1], _conf(ko, [pm, psl], tt, a, iv[0][1]),
                             dict(start_spot=spot_labels(sx, sy, start_spots), arrival_frame=ta, t_arrive_minus_trig_s=round((ta - tt) * DT, 2),
                                  dx=round(float(abs(ko.x[ta]) - abs(sx)), 2))))
            break
    return out


@_nonzero
def detect_high_low(scene, **params_):
    """High-low pass: from the high region (high post, elbow, pinch post, short-roll zone, top <= 7.5 m)
    to a low receiver (r <= 3.0 or a named low spot), ball dy <= -1.5 m."""
    P = params("high_low", params_)
    out = []
    high = ("high_post_area", "elbow", "pinch_post", "short_roll_zone")
    low = ("low_post", "duck_in", "lane_middle", "restricted_area", "dunker_spot", "deep_seal")
    priors = None  # B18: post_seal and duck_in once per call, not once per pass
    for pa, rel, pb, c in passes(scene, P["max_flight_s"]):
        ka, kb = scene.k(pa), scene.k(pb)
        ax_, ay_ = _xy(ka, rel)
        bx_, by_ = _xy(kb, c)
        hi = in_any(high, ax_, ay_) or (in_spot("top_three", ax_, ay_) and _r(ax_, ay_) <= P["top_r_max"])
        lo = _r(bx_, by_) <= P["receiver_r"] or in_any(low, bx_, by_)
        if not (hi and lo and by_ - ay_ <= -P["dy_m"]):
            continue
        prior = None
        w0 = max(0, rel - frames(P["prior_s"]))
        if priors is None:
            priors = (("post_seal", detect_post_seal(scene)), ("duck_in", detect_duck_in(scene)))
        for kind, evs_ in priors:
            if any(e.actors.get("post") == pb and e.end >= w0 and e.start <= rel for e in evs_):
                prior = kind
                break
        lob = bool(_r(bx_, by_) < P["lob_r"] and np.nanmean(kb.v_r[max(0, c - frames(P["lob_window_s"])):c + 1]) >= P["lob_vr_mps"])
        pdy = float(p_below(by_ - ay_, -P["dy_m"], float(math.hypot(_sig_p(ka)[rel], _sig_p(kb)[c]))))
        conf = _conf(ka, [pdy], rel, rel, c, 1.0 if prior else P["no_prior_factor"])
        out.append(Event("high_low", {"passer": pa, "receiver": pb}, rel, rel, c, conf,
                         dict(passer_spot=spot_labels(ax_, ay_, high + ("top_three",)), receiver_spot=spot_labels(bx_, by_, low),
                              receiver_r=round(_r(bx_, by_), 2), flight_s=round((c - rel) * DT, 2), prior_action=prior, lob=lob)))
    return out


@_nonzero
def detect_short_roll_playmaking(scene, screens=None, shots=None, **params_):
    """Decision of a short roller after his pocket catch (within 1.5 s): finish, drive, dump_off, lob, kick, reset, hold."""
    P = params("short_roll_playmaking", params_)
    out = []
    srs = [e for e in detect_short_roll(scene, screens) if e.attrs["variant"] == "catch"]
    fgas = fga_events(scene, shots, P)
    pss = passes(scene)
    for e in srs:
        s, h, tc = e.actors["screener"], e.actors["handler"], e.attrs["frame"]
        ks = scene.k(s)
        end = min(scene.n - 1, tc + frames(P["decide_s"]))
        dec, td, recv = "hold", end, None
        for shooter, tf, _ in fgas:
            if shooter == s and tc <= tf <= end:
                dec, td = ("finish" if ks.r[tf] < P["finish_r"] else "jumper"), tf
                break
        for pa, rel, pb, c in pss:
            if pa == s and tc <= rel <= end and rel < td:
                kb = scene.k(pb)
                rb = kb.r[c]
                if rb < P["lob_r"]:
                    dec = "lob"
                elif rb < P["dump_r"]:
                    dec = "dump_off"
                elif pb == h or (rb >= P["arc_r"] and kb.y[c] > ks.y[rel] + P["behind_m"]):
                    dec = "reset"
                elif rb >= P["arc_r"]:
                    dec = "kick"
                else:
                    dec = "pass_other"
                td, recv = rel, pb
                break
        if dec == "hold":
            dr = ks.r[tc:end + 1] - ks.r[tc]
            hs = holder_seq(scene)
            hold_ball = np.array([hs[t] == s for t in range(tc, end + 1)])
            if np.any(np.nan_to_num(dr <= -P["drive_m"], nan=False) & hold_ball):
                dec, td = "drive", tc + int(np.flatnonzero(np.nan_to_num(dr <= -P["drive_m"], nan=False) & hold_ball)[0])
        free = 0
        for d in scene.defense:
            kd = scene.k(d)
            if M.dist(kd, scene.k(h))[tc] > P["trap_dist_m"] and M.dist(kd, ks)[tc] > P["near_roller_m"]:
                free += 1
        open_m = None
        if recv is not None:
            _, open_m = nearest_defender(scene, recv, td, td)
        out.append(Event("short_roll_playmaking", {"roller": s, "handler": h, "receiver": recv}, tc, tc, td,
                         _conf(ks, [], tc, tc, td, e.conf),
                         dict(decision=dec, time_to_decision_s=round((td - tc) * DT, 2), four_on_three=bool(free == P["four_on_three_free"]),
                              receiver_open_m=None if open_m is None else round(float(open_m), 2), trap_context=e.attrs["trap_context"])))
    return out


@_nonzero
def detect_replace(scene, screens=None, **params_):
    """Replace: a third attacker fills the screen spot or lifts to the arc as the roller goes (third-player),
    or the screener sinks then pops while a teammate rolls (screener-level)."""
    P = params("replace", params_)
    out = []
    rolls = detect_roll(scene, screens)
    for rv in rolls:
        s, h, rs = rv.actors["screener"], rv.actors["handler"], rv.attrs["roll_start_frame"]
        px, py = rv.attrs["P_s"]
        ks = scene.k(s)
        for p in scene.offense:
            if p in (s, h):
                continue
            kp = scene.k(p)
            lo, hi = rs - frames(P["start_before_s"]), rs + frames(P["start_after_s"])
            spd = _fwd_mean(kp.speed, frames(P["gate_window_s"]) + 1)
            a = _first(np.nan_to_num(spd >= P["move_speed_mps"], nan=False).astype(bool), lo, hi)
            if a is None:
                continue
            a = run_start(kp.speed, P["onset_speed_mps"], a)
            sx, sy = _xy(kp, a)
            end = min(scene.n - 1, a + frames(P["move_s"]))
            near_ps = np.nan_to_num(np.hypot(kp.x - px, kp.y - py) <= P["end_near_ps_m"], nan=False).astype(bool)
            arc = spot_mask("pop_arc_zone", kp, a, end)
            sub, te = None, None
            if _r(sx, sy) < P["lift_start_r"]:
                te = _first(arc, a, end)
                sub = "lift_from_dunker" if te is not None else None
            elif math.hypot(sx - px, sy - py) >= P["fill_start_m"]:
                te = _first(near_ps, a, end)
                if te is not None:
                    sub = "perimeter_fill" if _r(sx, sy) >= P["arc_r"] else "fill_behind"
            if sub is None:
                continue
            sep = float(np.nanmin(M.dist(kp, ks)[a:te + 1]))
            if sep < P["min_sep_m"]:
                continue
            pd = float(p_above(sep, P["min_sep_m"], float(np.nanmean(M.sigma_dist(kp, ks)[a:te + 1]))))
            out.append(Event("replace", {"replacer": p, "roller": s, "handler": h}, rs, a, te, _conf(kp, [pd], rs, a, te, rv.conf),
                             dict(subtype=sub, start=(round(sx, 2), round(sy, 2)), end=tuple(round(v, 2) for v in _xy(kp, te)),
                                  t_start_minus_roll_start_s=round((a - rs) * DT, 2), min_sep_m=round(sep, 2),
                                  end_dist_to_Ps=round(float(math.hypot(kp.x[te] - px, kp.y[te] - py)), 2))))
    # screener-level replace (screens.yaml enum 'replace'): sink, then pop, while a teammate rolls
    Pr = params("roll")
    for ev in _screens(screens, ("ball",)):
        f = screen_frame(scene, ev, **params_)
        if f is None or f.t_rel is None:
            continue
        ks = scene.k(f.s)
        e1 = min(scene.n - 1, f.t_rel + frames(P["sink_within_s"]))
        sink_thr = min(f.r0 - P["sink_m"], P["sink_r"])
        tk = _first(np.nan_to_num(ks.r <= sink_thr, nan=False).astype(bool), f.t_rel, e1)
        if tk is None:
            continue
        e2 = min(scene.n - 1, f.t0 + frames(P["pop_within_s"]))
        tp = _first(spot_mask("pop_arc_zone", ks, tk, e2), tk, e2)
        if tp is None:
            continue
        roller = None
        for q in scene.offense:
            if q in (f.s, f.h):
                continue
            kq = scene.k(q)
            aq, _ = gate_onset(kq.v_r, Pr["v_r_gate_mps"], frames(Pr["gate_window_s"]) + 1, f.t0, e2)
            if aq is not None and _first(np.nan_to_num(kq.r <= Pr["rim_r"], nan=False).astype(bool), aq, e2) is not None:
                roller = (q, aq)
                break
        if roller is None:
            continue
        out.append(Event("replace", {"replacer": f.s, "roller": roller[0], "handler": f.h}, roller[1], f.t_rel, tp,
                         _conf(ks, [float(p_below(ks.r[tk], sink_thr, float(_sig_p(ks)[tk])))], roller[1], f.t_rel, tp, ev.conf),
                         dict(subtype="screener_sink_pop", sink_frame=tk, pop_frame=tp, **_frame_attrs(f))))
    return out


@_nonzero
def detect_roll_and_replace(scene, screens=None, **params_):
    """Set component: central high ball screen -> roll -> third-player replace, with a 4-around-1 shape check."""
    P = params("roll_and_replace", params_)
    out = []
    reps = [e for e in detect_replace(scene, screens) if e.attrs["subtype"] != "screener_sink_pop"]
    for rv in detect_roll(scene, screens):
        th = math.degrees(math.atan2(rv.attrs["P_s"][1], rv.attrs["P_s"][0]))
        if abs(th - P["theta_center_deg"]) > P["theta_dev_deg"] or not (P["r0_min"] <= rv.attrs["r_s0"] <= P["r0_max"]):
            continue
        rep = [e for e in reps if e.actors["roller"] == rv.actors["screener"]]
        if not rep:
            continue
        s, h = rv.actors["screener"], rv.actors["handler"]
        # B1: the 4-around-1 shape is checked from the roll's completion (first frame at r <= rim_r), not at a
        # fixed t0 + 1.8-2.2 s: a top roll released 0.6 s after t0 is still at r 3.7 then
        a = min(scene.n - 1, rv.end + frames(P["shape_after_completion_s"]))
        b = min(scene.n - 1, a + frames(P["shape_len_s"]))
        ok = []
        for t in range(a, b + 1):
            inside = [o for o in scene.offense if o != h and scene.k(o).r[t] < P["inside_r"]
                      and not in_spot("dunker_spot", *_xy(scene.k(o), t))]
            arc = [o for o in scene.offense if o != h and scene.k(o).r[t] >= P["arc_r"]]
            ok.append(inside == [s] and len(arc) >= P["min_arc_players"])
        frac = float(np.mean(ok)) if ok else 0.0
        if frac < P["shape_frac"]:
            continue
        out.append(Event("roll_and_replace", {"handler": h, "roller": s, "replacer": rep[0].actors["replacer"]}, rv.t0, rv.start,
                         max(rv.end, rep[0].end), _conf(scene.k(s), [frac], rv.t0, rv.start, rv.end, min(rv.conf, rep[0].conf)),
                         dict(compositional_name="roll_and_replace", action_sequence=["screen", "roll", "replace"],
                              shape_frac=round(frac, 2), replace_subtype=rep[0].attrs["subtype"])))
    return out


@_nonzero
def detect_offensive_rebound_crash(scene, shots=None, bigs=None, **params_):
    """Any non-shooter attacker bursting rimward (window-mean v_r >= 1.5) right after an FGA, reaching r <= 3.0."""
    P = params("offensive_rebound_crash", params_)
    out = []
    for shooter, tf, src in fga_events(scene, shots, P):
        for o in scene.offense:
            if o == shooter or (bigs is not None and o not in bigs):
                continue
            k = scene.k(o)
            a, vr = gate_onset(k.v_r, P["v_r_gate_mps"], frames(P["gate_window_s"]) + 1, tf, tf + frames(P["after_s"]))
            if a is None:
                continue
            e = _first(np.nan_to_num(k.r <= P["end_r"], nan=False).astype(bool), a, min(scene.n - 1, tf + frames(P["arrive_s"])))
            if e is None:
                continue
            pv = gate_conf(k, P["v_r_gate_mps"], frames(P["gate_window_s"]), a, e)
            out.append(Event("offensive_rebound_crash", {"crasher": o, "shooter": shooter}, tf, tf, e,
                             _conf(k, [pv], tf, tf, e, 1.0 if src == "event" else P["proxy_factor"]),
                             dict(fga_source=src, onset_frame=a, r_at_fga=round(float(k.r[tf]), 2), mean_v_r=round(vr, 2))))
    return out


@_nonzero
def detect_post_up(scene, shots=None, **params_):
    """Post-up after a catch in the post (r <= 4.5 in post_area): back_down, pass_out, shot or hold."""
    P = params("post_up", params_)
    out = []
    fgas = fga_events(scene, shots, P)
    caught = {(pb, c) for pa, rel, pb, c in passes(scene) if pa != pb}
    br = np.hypot(scene.ball.x, scene.ball.y) if scene.ball is not None else None
    for pid, a, b in holder_runs(scene):
        if pid not in scene.offense or a == 0 or (b - a) * DT < P["min_hold_s"]:
            continue
        k = scene.k(pid)
        x, y = _xy(k, a)
        # L4-2: catch_r_min (outside the restricted area: under the rim a 'catch' is a finish, a tip or a rebound)
        if not (P["catch_r_min"] <= _r(x, y) <= P["catch_r"] and in_spot("post_area", x, y)):
            continue
        # L4-2: a post-up starts with a post CATCH: the run must begin with a pass reception from a teammate (a run that
        # starts after a dribble gap, a loose ball or a rebound is not an entry)
        if P["require_pass"] and (pid, a) not in caught:
            continue
        # L4-2: the ball must not visit the rim cylinder (r <= fga_rim_r) in the rim_visit_before_s before the catch (a
        # shot arriving or a rebound over a player in the paint: the XY holder model has no ball height) or in the
        # rim_visit_after_s after it (a shot in flight passing over a teammate: no post player catches, gathers, shoots
        # and reaches the rim within 1 s)
        if br is not None:
            seg = br[max(0, a - frames(P["rim_visit_before_s"])):min(scene.n, a + frames(P["rim_visit_after_s"]) + 1)]
            if np.any(np.nan_to_num(seg <= P["fga_rim_r"], nan=False)):
                continue
        # L4-2: a post catch is made from a held or slow position; a catch at speed is a cut or a drive
        sp = float(np.nanmean(k.speed[max(0, a - frames(P["catch_speed_window_s"])):a + 1]))
        if not sp <= P["catch_speed_max_mps"]:
            continue
        d, dd = nearest_defender(scene, pid, a, min(b, a + frames(P["def_window_s"])))
        if d is None or dd > P["def_m"]:
            continue
        dr = np.nanmin(k.r[a:b + 1]) - k.r[a]
        sub = "back_down" if dr <= -P["back_down_m"] else None
        if sub is None:
            sub = "shot" if any(s_ == pid and abs(tf - b) <= frames(P["shot_tol_s"]) for s_, tf, _ in fgas) else None
        if sub is None:
            sub = "pass_out" if any(pa == pid and rel == b for pa, rel, _, _ in passes(scene)) else "hold"
        pdef = float(p_below(dd, P["def_m"], float(np.nanmean(M.sigma_dist(k, scene.k(d))[a:b + 1]))))
        w0 = max(0, a - frames(P["catch_speed_window_s"]))
        pspd = float(p_below(sp, P["catch_speed_max_mps"], float(np.nanmean(_sig_v(k)[w0:a + 1]))))
        out.append(Event("post_up", {"post": pid, "defender": d}, a, a, b, _conf(k, [pdef, pspd], a, a, b),
                         dict(subtype=sub, catch_r=round(_r(x, y), 2), hold_s=round((b - a) * DT, 2), dr=round(float(dr), 2),
                              catch_speed=round(sp, 2))))
    return out


# --------------------------------------------------------------------------------------
# Rule: factorised screener post-action label with precedence (fills screens.screener_action_after)
# --------------------------------------------------------------------------------------
PRECEDENCE = ["move_to_screen", "ghost", "slip", "slip_to_arc", "seal", "roll", "short_roll", "pop_arc", "pop_mid",
              "replace", "crash", "roll_into_post"]
CTG_COMPAT = {"roll": "roll", "short_roll": "short_roll", "pop_arc": "pop", "pop_mid": "pop", "slip": "roll",
              "slip_to_arc": "pop", "seal": "roll", "ghost": "none", "replace": "pop", "crash": "crash",
              "roll_into_post": "mid_post", "move_to_screen": "move_to_screen", "none": "none"}
SYNERGY_ROLL_MAN = {"roll", "short_roll", "pop_arc", "pop_mid", "slip", "slip_to_arc", "seal"}


@_nonzero
def detect_screener_post_action(scene, screens=None, shots=None, **params_):
    """One 'screener_post_action' per input screen: label by precedence, renormalised probabilities,
    top-2 and margin; 'ambiguous:a|b' when top-1 < 0.5; 'unknown_post_action' on a camera cut / long gap."""
    P = params("screener_post_action", params_)
    out = []
    # B18: screen-independent detectors run once per call, not once per screen
    m2s_all = detect_move_to_screen(scene, screens=screens)
    ghosts = None
    for ev in _screens(screens, ("ball", "dho", "off_ball")):
        f = screen_frame(scene, ev, **params_)
        if f is None:
            continue
        k = scene.k(f.s)
        if gap_factor(k, max(0, f.t0 - frames(P["gap_check_before_s"])), f.w_end) == 0.0:
            out.append(Event("screener_post_action", {"screener": f.s, "user": f.h}, f.t0, f.t0, f.w_end, 0.0,
                             dict(label="unknown_post_action", reason="cut_or_long_gap", **_frame_attrs(f))))
            continue
        # L4-5: the labels compete CONDITIONAL on the screen: each label detector sees the screen with conf 1 (its
        # standalone event multiplies the screen's conf in, so a sure 6 m roll behind a conf-0.45 screen read 0.45
        # against 'none' 0.55 and came out ambiguous:roll|none). The screen's own conf multiplies the output conf.
        one = [Event(ev.kind, ev.actors, ev.t0, ev.start, ev.end, 1.0, ev.attrs)] if P["label_given_screen"] else [ev]
        p_scr = float(ev.conf) if P["label_given_screen"] else 1.0
        cand = {}
        for lab, fn, kw in (("move_to_screen", lambda scene_, **_: m2s_all, {}),
                            ("slip", detect_slip, {"screens": one}), ("slip_to_arc", detect_slip_to_arc, {"screens": one}),
                            ("seal", detect_seal, {"screens": one}), ("roll", detect_roll, {"screens": one}),
                            ("short_roll", detect_short_roll, {"screens": one}), ("pop_arc", detect_pop_arc, {"screens": one}),
                            ("pop_mid", detect_pop_mid, {"screens": one}), ("crash", detect_crash, {"screens": one, "shots": shots}),
                            ("roll_into_post", detect_roll_into_post, {"screens": one})):
            evs = fn(scene, **kw)
            if lab == "move_to_screen":
                evs = [e for e in evs if e.actors["screener"] == f.s and e.attrs["first_screen_t0"] == f.t0]
            if evs:
                cand[lab] = max(e.conf for e in evs)
        reps = [e for e in detect_replace(scene, one) if e.attrs.get("subtype") == "screener_sink_pop"]
        if reps:
            cand["replace"] = max(e.conf for e in reps)
        if f.never_set:
            if ghosts is None:
                ghosts = detect_ghost(scene)
            g = [e for e in ghosts if e.actors["screener"] == f.s and abs(e.t0 - f.t0) <= frames(P["ghost_match_s"])]
            # a ghost 'in' is the same event as slip's ghost_in subtype (YAML ghost rule): when slip fired it is
            # not a competing label (slip_type carries it); ghost out / mid still compete
            if "slip" in cand:
                g = [e for e in g if e.attrs["subtype"] != "in"]
            if g:
                cand["ghost"] = max(e.conf for e in g)
        fired = [lab for lab in PRECEDENCE if lab in cand]
        p_none = float(np.prod([1 - cand[x] for x in fired])) if fired else 1.0
        tot = sum(cand[x] for x in fired) + p_none
        probs = {x: cand[x] / tot for x in fired}
        probs["none"] = p_none / tot
        # B11: label = argmax of the renormalised probabilities over fired labels; PRECEDENCE only breaks
        # near-ties (within precedence_margin). Ghost outranks slip only when p_never_set >= ghost_never_set_min.
        prec_label = fired[0] if fired else "none"
        label = "none"
        if fired:
            best = max(probs[x] for x in fired)
            near = [x for x in fired if best - probs[x] < P["precedence_margin"]]
            if "ghost" in near and "slip" in near and f.attrs["p_never_set"] < P["ghost_never_set_min"]:
                near.remove("ghost")
            label = near[0]  # `fired` is in PRECEDENCE order
        ranked = sorted(probs.items(), key=lambda kv: -kv[1])
        second = [x for x in ranked if x[0] != label]
        lab2, p2 = (second[0] if second else ("none", 0.0))
        p1 = probs[label]
        stored = label if p1 >= P["ambiguous_below"] else f"ambiguous:{label}|{lab2}"
        out.append(Event("screener_post_action", {"screener": f.s, "user": f.h}, f.t0, f.t0, f.w_end, float(p1) * p_scr,
                         dict(label=stored, top1=label, p_screen=round(p_scr, 3), precedence_label=prec_label, p_label=round(p1, 3), label_2=lab2,
                              p_label_2=round(p2, 3),
                              margin=round(p1 - p2, 3), probs={k_: round(v, 3) for k_, v in probs.items()},
                              ctg_compat_label=CTG_COMPAT.get(label, "none"),
                              synergy_compat="roll_man" if label in SYNERGY_ROLL_MAN else "other", **_frame_attrs(f))))
    return out


# --------------------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------------------
DETECTORS = {
    "screen_frame": detect_screen_frame,
    "screener_set_state": detect_screener_set_state,
    "behind_def": detect_behind_def,
    "post_seal": detect_post_seal,
    "id_swap_risk": detect_id_swap_risk,
    "lob_catch_proxy": detect_lob_catch_proxy,
    "roll": detect_roll,
    "short_roll": detect_short_roll,
    "pop_arc": detect_pop_arc,
    "pop_mid": detect_pop_mid,
    "slip": detect_slip,
    "slip_to_arc": detect_slip_to_arc,
    "ghost": detect_ghost,
    "seal": detect_seal,
    "crash": detect_crash,
    "move_to_screen": detect_move_to_screen,
    "roll_into_post": detect_roll_into_post,
    "spain_pop": detect_spain_pop,
    "dive": detect_dive,
    "rim_run": detect_rim_run,
    "dunker_relocation": detect_dunker_relocation,
    "duck_in": detect_duck_in,
    "high_low": detect_high_low,
    "short_roll_playmaking": detect_short_roll_playmaking,
    "replace": detect_replace,
    "roll_and_replace": detect_roll_and_replace,
    "offensive_rebound_crash": detect_offensive_rebound_crash,
    "post_up": detect_post_up,
    "screener_post_action": detect_screener_post_action,
}


def _needs_data_stub(item_id):
    def f(scene, **_):
        """Not detectable from XY (+ ball XY): see the YAML item's needs_data."""
        return []
    f.__name__ = f"detect_{item_id}"
    return f


for _it in DOC["items"]:  # items marked needs_data get a stub that returns []
    if _it.get("needs_data") and _it["id"] not in DETECTORS:
        DETECTORS[_it["id"]] = _needs_data_stub(_it["id"])


def detect_all(scene, **context):
    """Run every detector. `context` may carry screens, shots, transitions, bigs, v_peak; each
    detector receives only the context names in its signature. Returns events sorted by t0."""
    out = []
    for fn in DETECTORS.values():
        names = inspect.signature(fn).parameters
        kw = {k: v for k, v in context.items() if k in names}
        out.extend(fn(scene, **kw))
    return sorted(out, key=lambda e: (e.t0, e.kind))
