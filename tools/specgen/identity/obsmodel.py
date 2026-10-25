"""Broadcast observation simulator for the identity harness (config/identity_pack.yaml, harness section).

Turns true positions (ids known) into what a broadcast tracker would see: detections without ids,
position noise, the main camera's field of view following the ball, camera-model occlusions and
merged boxes, detector drop-outs, camera cuts (dead-ball gaps and rare live cuts), officials as
distractors, and cue observations (team colour, jersey sightings, appearance, height, gait) drawn
from a cue profile. It also builds what the assigner knows (Game: reference pack + lineup feed with
PBP lag and substitution windows). All randomness comes from the rng passed in.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.signal import lfilter
from scipy.special import ndtr

from idlib import NUMBERS, PARTIAL0, Dets, Game, P, SPEC, confusables, frames, jersey_code_full

COURT_L, COURT_W = 28.65, 15.24


@dataclass
class Truth:
    dt: float
    pos: np.ndarray              # (F, N, 2) metres, NaN when off court
    team: np.ndarray             # (N,) 0 / 1
    jersey: list                 # (N,) strings
    position: list               # (N,) roster position strings ('G', 'F-C', ...)
    ball: np.ndarray             # (F, 2)
    gap: np.ndarray              # (F,) True at the first frame after a data gap (dead ball, period change)
    meta: dict = field(default_factory=dict)

    @property
    def n_frames(self):
        return self.pos.shape[0]

    @property
    def n(self):
        return self.pos.shape[1]


def profile(name):
    return dict(SPEC["harness"]["cue_profiles"][name])


def ar_noise(n, sigma, rng, white_share=0.5, rho=0.9, shape=()):
    """White + AR(1) mix with stationary std sigma along axis 0 (the sim.py model, vectorised)."""
    w = rng.normal(0, 1, (n,) + shape)
    e = rng.normal(0, 1, (n,) + shape)
    x = e * math.sqrt(1 - rho**2)
    x[0] = e[0]  # start in the stationary state
    ar = lfilter([1.0], [1.0, -rho], x, axis=0)
    return sigma * (math.sqrt(white_share) * w + math.sqrt(1 - white_share) * ar)


def _unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _speed(pos, dt):
    v = np.zeros(pos.shape[:2])
    dv = np.hypot(*(np.diff(pos, axis=0) / dt).transpose(2, 0, 1))
    v[1:] = dv
    v[0] = dv[0] if len(dv) else 0
    return np.nan_to_num(v)


def _heights(truth, rng):
    hb = SPEC["harness"]["height_by_position_m"]
    out = np.zeros(truth.n)
    for p, pos in enumerate(truth.position):
        keys = [k for k in str(pos).replace("-", " ").split() if k in hb] or ["F"]
        mu = np.mean([hb[k][0] for k in keys])
        sd = np.mean([hb[k][1] for k in keys])
        out[p] = rng.normal(mu, sd)
    return out


def observe(truth: Truth, prof: dict, sigma_p: float, rng, opts: dict | None = None, prm=None):
    """-> (Dets, Game, info). opts switch parts of the model off for unit tests (see DEFAULT_OPTS)."""
    prm = prm or P
    o = dict(DEFAULT_OPTS)
    o.update(opts or {})
    dt, F, N = truth.dt, truth.n_frames, truth.n
    R = prm["n_referees"] if o["refs"] else 0
    K = N + R
    t = np.arange(F) * dt

    # ---------------- camera: main-wide frames, cuts, field of view
    main = np.ones(F, dtype=bool)
    if o["live_cuts"]:
        n_cut = rng.poisson(prm["live_cut_rate_per_min"] * F * dt / 60.0)
        for _ in range(n_cut):
            a = int(rng.integers(0, F))
            L = frames(rng.uniform(*prm["live_cut_s"]), dt)
            main[a:a + L] = False
    for a, b in o["cut_intervals"]:
        main[a:b] = False
    cut = truth.gap.copy()
    after = np.zeros(F, dtype=bool)
    after[1:] = main[1:] & ~main[:-1]
    cut |= after
    cut[0] = True
    xc = np.zeros(F)
    alpha = 1 - math.exp(-dt / prm["fov_tau_s"])
    half = prm["fov_width_m"] / 2
    bx = np.nan_to_num(truth.ball[:, 0], nan=COURT_L / 2)
    for f in range(F):
        xc[f] = bx[f] if (cut[f] or f == 0) else xc[f - 1] + alpha * (bx[f] - xc[f - 1])
    xc = np.clip(xc, half, COURT_L - half)
    if not o["fov"]:
        xc[:] = COURT_L / 2
        half = COURT_L
    fov = np.stack([xc - half, xc + half], 1)

    # ---------------- persons: players + officials
    pos = np.full((F, K, 2), np.nan)
    pos[:, :N] = truth.pos
    if R:
        offs = np.array([-7.0, 3.0, 9.0][:R])
        ys = np.array([0.6, 14.6, 0.6][:R])
        ph = rng.uniform(0, 2 * math.pi, R)
        for k in range(R):
            pos[:, N + k, 0] = np.clip(xc + offs[k] + 1.5 * np.sin(0.3 * t + ph[k]), 0.3, COURT_L - 0.3)
            pos[:, N + k, 1] = ys[k] + 0.4 * np.sin(0.5 * t + ph[k])
    on = ~np.isnan(pos[:, :, 0])
    in_fov = on & main[:, None] & (pos[:, :, 0] >= fov[:, :1]) & (pos[:, :, 0] <= fov[:, 1:])
    if not o["fov"]:
        in_fov = on & main[:, None]

    # ---------------- occlusion and merged boxes (camera model)
    present = in_fov.copy()
    nocue = np.zeros((F, K), dtype=bool)
    root = np.tile(np.arange(K), (F, 1))
    cam = np.array(prm["camera_xy_m"])
    u = rng.normal(size=(F, K))
    u = lfilter([math.sqrt(1 - 0.95**2)], [1, -0.95], u, axis=0)
    u = ndtr(u)
    if o["occlusion"]:
        for a in range(0, F, 4000):
            b = min(F, a + 4000)
            pp = pos[a:b]
            dd = np.hypot(pp[:, :, None, 0] - pp[:, None, :, 0], pp[:, :, None, 1] - pp[:, None, :, 1])
            vis = in_fov[a:b]
            pair_ok = vis[:, :, None] & vis[:, None, :]
            rr = np.hypot(pp[..., 0] - cam[0], pp[..., 1] - cam[1])
            az = np.arctan2(pp[..., 1] - cam[1], pp[..., 0] - cam[0])
            lat = 0.5 * (rr[:, :, None] + rr[:, None, :]) * np.abs(az[:, :, None] - az[:, None, :])
            dep = np.abs(rr[:, :, None] - rr[:, None, :])
            iu = np.triu(np.ones((K, K), dtype=bool), 1)[None]
            merge = pair_ok & (dd < prm["merge_m"]) & iu
            occl = pair_ok & ~merge & (lat < prm["occl_lateral_m"]) & (dep < prm["occl_depth_m"]) & iu
            for fi in np.where(merge.any((1, 2)) | occl.any((1, 2)))[0]:
                f = a + fi
                prs = np.argwhere(merge[fi])
                prs = prs[np.argsort(dd[fi][prs[:, 0], prs[:, 1]])]
                for i, j in prs:
                    near, far = (i, j) if rr[fi, i] <= rr[fi, j] else (j, i)
                    rn = root[f, near]
                    if root[f, far] != far:
                        continue
                    root[f, far] = rn
                    present[f, far] = False
                    nocue[f, rn] = True
                for i, j in np.argwhere(occl[fi]):
                    near, far = (i, j) if rr[fi, i] <= rr[fi, j] else (j, i)
                    if not present[f, far]:
                        continue
                    if u[f, far] < prm["p_occl_drop"]:
                        present[f, far] = False
                    else:
                        nocue[f, far] = True
    # detector drop-outs
    if o["misses"]:
        for k in range(K):
            starts = np.where(rng.random(F) < prm["p_miss"])[0]
            for s in starts:
                present[s:s + max(1, frames(rng.uniform(*prm["miss_len_s"]), dt)), k] = False
    # ---------------- positions with noise (merged boxes at the group mean)
    noise = ar_noise(F, sigma_p, rng, shape=(K, 2)) if sigma_p > 0 else np.zeros((F, K, 2))
    obs = pos + noise
    fr_merge = np.where((root != np.arange(K)[None, :]).any(1))[0]
    for f in fr_merge:
        for r_ in np.unique(root[f]):
            mem = np.where(root[f] == r_)[0]
            if len(mem) > 1:
                obs[f, r_] = pos[f, mem].mean(0) + noise[f, r_]
    fi, ki = np.nonzero(present)
    Dn = len(fi)
    src = np.where(ki < N, ki, -1 - (ki - N))
    xy = obs[fi, ki]
    nc = nocue[fi, ki]

    # ---------------- cues
    pal = _palette(truth, prof, rng, R, o["twins"])
    cls_true = np.where(ki < N, truth.team[np.minimum(ki, N - 1)], 2)
    cls_obs = cls_true.copy()
    e = np.where(ki < N, prof["e_team"], prm["e_ref_class"])
    flip = rng.random(Dn) < e
    cls_obs[flip] = (cls_true[flip] + rng.integers(1, 3, flip.sum())) % 3
    cls_obs[nc] = -1
    jersey = np.full(Dn, -1, dtype=np.int64)
    det_index = -np.ones((F, K), dtype=np.int64)
    det_index[fi, ki] = np.arange(Dn)
    cuepresent = present & ~nocue
    speed = _speed(np.nan_to_num(pos), dt)
    rcam = np.hypot(pos[..., 0] - cam[0], pos[..., 1] - cam[1])
    for p in range(N):
        sched = o["jersey_schedule"].get(p)
        sightings = []
        if sched is not None:
            for t0, t1, read in sched:
                code = read if isinstance(read, (int, np.integer)) else jersey_code_full(read)
                sightings.append((frames(t0, dt), frames(t1, dt), code))
        if o["random_jersey"]:
            size = np.clip(1 - 0.7 * (rcam[:, p] - prm["reach_dist_ref_m"]) / (28.0 - prm["reach_dist_ref_m"]), 0.3, 1.0)
            blur = np.where(speed[:, p] > 5.0, 0.5, 1.0)
            haz = prof["jersey_sightings_per_s"] * dt * size * blur * cuepresent[:, p]
            cand = np.where(rng.random(F) < haz)[0]
            busy = -1
            for s in cand:
                if s <= busy:
                    continue
                L = max(1, frames(rng.uniform(*prof["jersey_sighting_len_s"]), dt))
                sightings.append((s, s + L, _read(truth.jersey[p], prof, rng)))
                busy = s + L
        for a, b, code in sightings:
            for f in range(a, min(b, F)):
                if cuepresent[f, p]:
                    jersey[det_index[f, p]] = code
    stride = max(1, frames(prm["cue_stride_s"], dt))
    phase = rng.integers(0, stride, K)
    on_stride = ((np.arange(F)[:, None] + phase[None, :]) % stride == 0) & cuepresent
    E, G = prof["app_dims"], 4
    emb = np.full((Dn, E), np.nan)
    height = np.full(Dn, np.nan)
    gait = np.full((Dn, G), np.nan)
    for k in range(K):
        fr = np.where(on_stride[:, k])[0]
        if len(fr) == 0:
            continue
        js = det_index[fr, k]
        rho_s = prof["app_rho"] ** stride
        ns = ar_noise(len(fr), prof["app_noise"], rng, white_share=0.0, rho=rho_s, shape=(E,))
        emb[js] = _unit(pal["app_true"][k][None, :] + ns)
        hz = pal["height"][k] + rng.normal(0, prof["sigma_h"], len(fr))
        out = rng.random(len(fr)) < prof["outlier_h"]
        hz[out] = pal["height"][k] + np.where(rng.random(out.sum()) < 0.7, -rng.uniform(0.1, 0.5, out.sum()), rng.uniform(0.1, 0.4, out.sum()))
        height[js] = hz
        run = speed[fr, k] >= prm["gait_min_speed_mps"]
        gn = _unit(pal["gait_true"][k][None, :] + rng.normal(0, prof["gait_noise"], (len(fr), G)))
        gait[js[run]] = gn[run]
    if not o["cues_appearance"]:
        emb[:] = np.nan
    dets = Dets(dt, F, fi.astype(np.int64), xy, src.astype(np.int64), nc, cls_obs.astype(np.int64), jersey,
                emb, height, gait, cut, fov)

    # ---------------- what the assigner knows
    oncourt = ~np.isnan(truth.pos[:, :, 0])
    cand = lineup_feed(truth, oncourt, rng, o, prm)
    game = Game(truth.team.copy(), list(truth.jersey), pal["height"][:N] + rng.normal(0, 0.015, N),
                pal["template"], pal["gait_ref"], cand)
    info = {"in_fov": in_fov[:, :N], "main": main, "twins": pal["twins"], "height_true": pal["height"][:N],
            "n_officials": R, "fov": fov}
    return dets, game, info


DEFAULT_OPTS = {"refs": True, "fov": True, "live_cuts": True, "occlusion": True, "misses": True, "random_jersey": True,
                "jersey_schedule": {}, "cut_intervals": [], "lineup": True, "pbp_lag": True, "cues_appearance": True,
                "twins": None}


def _read(num, prof, rng):
    if rng.random() < prof["p_partial"]:
        digits = list(num)
        d = int(rng.choice(digits)) if rng.random() > 0.05 else int(rng.integers(0, 10))
        return PARTIAL0 + d
    if rng.random() >= prof["e_ocr"]:
        return jersey_code_full(num)
    conf = confusables(num)
    if conf and rng.random() < 0.5:
        return jersey_code_full(str(rng.choice(conf)))
    while True:
        r = NUMBERS[int(rng.integers(0, len(NUMBERS)))]
        if r != num:
            return jersey_code_full(r)


def _palette(truth, prof, rng, R, twins_override=None):
    """True appearance, height and gait per person; templates and references the pack would hold."""
    N, E, G = truth.n, prof["app_dims"], 4
    kit = _unit(rng.normal(size=(3, E)))
    ind = _unit(rng.normal(size=(N + R, E)))
    gd = _unit(rng.normal(size=(N + R, E)))
    gait = _unit(rng.normal(size=(N + R, G)))
    height = np.concatenate([_heights(truth, rng), rng.normal(1.85, 0.06, R)])
    twins = []
    npairs = prof["twin_pairs_per_team"]
    pairs = []
    if twins_override is not None:
        pairs = list(twins_override)
    else:
        for team in (0, 1):
            mem = [p for p in range(N) if truth.team[p] == team]
            rng.shuffle(mem)
            pairs += list(zip(mem[0:2 * npairs:2], mem[1:2 * npairs:2]))
    for a, b in pairs:
        ind[b] = _unit(ind[a] + 0.15 * rng.normal(size=E))
        gd[b] = _unit(gd[a] + 0.15 * rng.normal(size=E))
        height[b] = height[a] + rng.uniform(-0.01, 0.01)
        gait[b] = _unit(gait[a] + 0.2 * rng.normal(size=G))
        twins.append((a, b))
    cls = np.concatenate([truth.team, np.full(R, 2)])
    season = kit[cls] + prof["app_w_ind"] * ind
    app_true = _unit(season + prof["app_w_game"] * gd)
    tmpl = season + (prof["app_w_game"] * gd if prof["game_card"] else 0)
    tmpl = _unit(tmpl + rng.normal(0, prof["app_noise"] / math.sqrt(prof["template_crops"]), tmpl.shape))
    gref = _unit(gait + rng.normal(0, 0.1, gait.shape))
    return {"app_true": app_true, "template": tmpl[:N], "height": height, "gait_true": gait, "gait_ref": gref[:N], "twins": twins}


def lineup_feed(truth, oncourt, rng, o, prm):
    """Candidate mask (F, N): PBP lineup (true changes shifted by a random lag) widened in substitution windows."""
    F, N, dt = truth.n_frames, truth.n, truth.dt
    if not o["lineup"]:
        return np.ones((F, N), dtype=bool)
    core = np.zeros((F, N), dtype=bool)
    cand = np.zeros((F, N), dtype=bool)
    win = frames(prm["sub_window_s"], dt)
    for team in (0, 1):
        cols = np.where(truth.team == team)[0]
        sub = oncourt[:, cols]
        ch = np.where((sub[1:] != sub[:-1]).any(1))[0] + 1
        bounds = [0] + list(ch) + [F]
        prev_end = 0
        pbp_times = []
        for i in range(len(bounds) - 1):
            a = bounds[i]
            lag = frames(rng.uniform(*prm["pbp_lag_s"]), dt) if (o["pbp_lag"] and i > 0) else 0
            a2 = int(np.clip(a + lag, prev_end, F - 1)) if i > 0 else 0
            core[a2:, cols] = sub[a]
            prev_end = a2
            if i > 0:
                pbp_times.append((a2, a))
        cand[:, cols] = core[:, cols]
        for a2, f0 in pbp_times:  # the window is centred on the PBP time, the only time the assigner knows
            union = sub[f0 - 1] | sub[f0]
            cand[max(0, a2 - win):min(F, a2 + win), cols] |= union[None, :]
    return cand
