"""Broadcast observation simulator for the identity harness (config/identity_pack.yaml, harness section).

Turns true positions (ids known) into what a broadcast tracker would see: detections without ids,
position noise, the main camera's field of view following the ball, camera-model occlusions and
merged boxes, detector drop-outs, camera cuts (dead-ball gaps and rare live cuts), officials as
distractors, and cue observations (team colour, jersey sightings, appearance, height, gait) drawn
from a cue profile. It also builds what the assigner knows (Game: reference pack + lineup feed with
PBP lag and substitution windows). All randomness comes from the rng passed in.

Optional error models (harness.cue_profile_options; review round 2, RV-12 to RV-16, RV-21) are off in the stored
profiles good / poor / poor_uncalibrated and draw from a side random stream spawned from the rng's seed, so
the main stream, and with it every stored detection, is unchanged when they are off: colour errors in runs,
truncated / repeated / persistent jersey misreads, unflagged overlaps (the near player's cues inside the far
player's box), slow appearance error, graded look-alike pairs, same-kit non-players, late / missing / wrong
play-by-play rows, sigma_p told inexactly. info["flags"] marks the detections each error touched (harness
mechanism attribution only; the assigner never sees it).
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


def with_options(prof):
    """A cue profile with every optional key filled with its default (off) value (harness.cue_profile_options)."""
    out = {k: v["default"] for k, v in SPEC["harness"]["cue_profile_options"].items()}
    out.update(prof)
    return out


def profile(name):
    return with_options(SPEC["harness"]["cue_profiles"][name])


def ar_noise(n, sigma, rng, white_share, rho, shape=()):
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
    prof = with_options(prof)
    o = dict(DEFAULT_OPTS)
    o.update(opts or {})
    rngx, rngo = (np.random.default_rng(c) for c in rng.bit_generator.seed_seq.spawn(2))  # side streams: options, box order
    lo_, hi_ = prof["sigma_told_range"]
    told = float(math.exp(rngx.uniform(math.log(lo_), math.log(hi_))))
    dt, F, N = truth.dt, truth.n_frames, truth.n
    R = prm["n_referees"] if o["refs"] else 0
    B = 2 * int(prof["bystanders_per_team"]) if o["bystanders"] else 0
    K = N + R + B
    bteam = np.arange(B) % 2
    cls_person = np.concatenate([np.asarray(truth.team), np.full(R, 2), bteam]).astype(np.int64)
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
    for b in range(B):  # same-kit non-players: stand just inside the far sideline near the table for a while
        for s0 in np.where(rngx.random(F) < prof["bystander_per_min"] * dt / 60.0)[0]:
            L = max(1, frames(rngx.uniform(*prof["bystander_len_s"]), dt))
            pos[s0:s0 + L, N + R + b, 0] = np.clip(rngx.normal(COURT_L / 2, prm["bystander_x_sd_m"]), 0.5, COURT_L - 0.5)
            pos[s0:s0 + L, N + R + b, 1] = COURT_W - rngx.uniform(*prm["bystander_y_inset_m"])
    on = ~np.isnan(pos[:, :, 0])
    in_fov = on & main[:, None] & (pos[:, :, 0] >= fov[:, :1]) & (pos[:, :, 0] <= fov[:, 1:])
    if not o["fov"]:
        in_fov = on & main[:, None]

    # ---------------- occlusion and merged boxes (camera model)
    present = in_fov.copy()
    nocue = np.zeros((F, K), dtype=bool)
    root = np.tile(np.arange(K), (F, 1))
    cam = np.array(prm["camera_xy_m"])
    rho_o = prm["occl_ar_rho"]
    u = rng.normal(size=(F, K))
    u = lfilter([math.sqrt(1 - rho_o**2)], [1, -rho_o], u, axis=0)
    u = ndtr(u)
    cue_from = np.tile(np.arange(K), (F, 1))  # person whose cues are read in each box (the near player in an unflagged overlap)
    u2 = None
    if prof["p_overlap_unflagged"] > 0 and o["occlusion"]:
        u2 = ndtr(lfilter([math.sqrt(1 - rho_o**2)], [1, -rho_o], rngx.normal(size=(F, K)), axis=0))
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
                    elif u2 is not None and u2[f, far] < prof["p_overlap_unflagged"]:
                        cue_from[f, far] = near  # overlap not flagged: the box carries the near player's cues
                    else:
                        nocue[f, far] = True
    # detector drop-outs
    if o["misses"]:
        for k in range(K):
            starts = np.where(rng.random(F) < prm["p_miss"])[0]
            for s in starts:
                present[s:s + max(1, frames(rng.uniform(*prm["miss_len_s"]), dt)), k] = False
    # ---------------- positions with noise (merged boxes at the group mean)
    noise = (ar_noise(F, sigma_p, rng, prm["position_noise_white_share"], prm["position_noise_rho"], shape=(K, 2))
             if sigma_p > 0 else np.zeros((F, K, 2)))
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
    pal = _palette(truth, prof, rng, R, o["twins"], prm, rngx, bteam)
    det_index = -np.ones((F, K), dtype=np.int64)
    det_index[fi, ki] = np.arange(Dn)
    ksrc = cue_from[fi, ki]
    flags = {k: np.zeros(Dn, dtype=bool) for k in FLAG_KEYS}
    flags["overlap_unflagged"] = (ksrc != ki) & ~nc
    cls_true = cls_person[ksrc]
    cls_obs = cls_true.copy()
    e = np.where(cls_person[ki] < 2, prof["e_team"], prm["e_ref_class"])
    flip = rng.random(Dn) < e
    cls_obs[flip] = (cls_true[flip] + rng.integers(1, 3, flip.sum())) % 3
    if prof["team_burst_per_s"] > 0:  # colour errors in runs: a player reads as the opponent, a non-player as a team
        for k in range(K):
            for s0 in np.where(rngx.random(F) < prof["team_burst_per_s"] * dt)[0]:
                L = max(1, frames(rngx.uniform(*prof["team_burst_len_s"]), dt))
                js = det_index[s0:s0 + L, k]
                js = js[js >= 0]
                js = js[rngx.random(len(js)) < prof["team_burst_hit"]]
                cls_obs[js] = 1 - cls_person[k] if cls_person[k] < 2 else int(rngx.integers(0, 2))
                flags["colour_run"][js] = True
    for p, sched in o["class_schedule"].items():  # unit tests: force the class read of person p in [t0, t1)
        for t0, t1, c in sched:
            js = det_index[frames(t0, dt):frames(t1, dt), p]
            js = js[js >= 0]
            cls_obs[js] = c
            flags["colour_run"][js] = True
    cls_obs[nc] = -1
    jersey = np.full(Dn, -1, dtype=np.int64)
    cuepresent = present & ~nocue
    own_cue = cuepresent & (cue_from == np.arange(K)[None, :])  # the box shows its own person's number
    ov_f, ov_far = {}, {}
    if u2 is not None:  # boxes that show person p's number although they are another person's box
        fo, ko = np.nonzero((cue_from != np.arange(K)[None, :]) & cuepresent)
        for near in np.unique(cue_from[fo, ko]):
            m = cue_from[fo, ko] == near
            ov_f[int(near)], ov_far[int(near)] = fo[m], ko[m]  # np.nonzero is sorted by frame
    speed = _speed(np.nan_to_num(pos), dt)
    rcam = np.hypot(pos[..., 0] - cam[0], pos[..., 1] - cam[1])
    for p in range(N):
        sched = o["jersey_schedule"].get(p)
        sightings = []
        num = truth.jersey[p]
        if sched is not None:
            for t0, t1, read in sched:
                code = read if isinstance(read, (int, np.integer)) else jersey_code_full(read)
                sightings.append((frames(t0, dt), frames(t1, dt), code, None))
        if o["random_jersey"]:
            ff = prm["sighting_far_factor"]
            size = np.clip(1 - (1 - ff) * (rcam[:, p] - prm["reach_dist_ref_m"]) / (prm["sighting_far_m"] - prm["reach_dist_ref_m"]), ff, 1.0)
            blur = np.where(speed[:, p] > prm["sighting_blur_speed_mps"], prm["sighting_blur_factor"], 1.0)
            haz = prof["jersey_sightings_per_s"] * dt * size * blur * cuepresent[:, p]
            cand = np.where(rng.random(F) < haz)[0]
            busy = -1
            last_wrong = None  # (code, end frame) of the last wrong full read, while it can persist
            for s in cand:
                if s <= busy:
                    continue
                L = max(1, frames(rng.uniform(*prof["jersey_sighting_len_s"]), dt))
                code, kind = _read(num, prof, rng, prm), None
                if prof["p_trunc"] > 0 and len(num) == 2 and num != "00" and rngx.random() < prof["p_trunc"]:
                    code, kind = jersey_code_full(num[int(rngx.integers(0, 2))]), "jersey_trunc"  # one digit hidden, read as a full number
                if (prof["p_misread_persist"] > 0 and last_wrong is not None and (s - last_wrong[1]) * dt <= prof["misread_persist_s"]
                        and rngx.random() < prof["p_misread_persist"]):
                    code, kind = last_wrong[0], "jersey_repeat"  # the same misread again
                sightings.append((s, s + L, code, kind))
                busy = s + L
                while prof["p_repeat"] > 0 and rngx.random() < prof["p_repeat"]:  # the same view interrupted and resumed
                    g_ = frames(rngx.uniform(*prof["repeat_gap_s"]), dt)
                    L2 = max(1, frames(rngx.uniform(*prof["jersey_sighting_len_s"]), dt))
                    sightings.append((busy + g_, busy + g_ + L2, code, "jersey_repeat"))
                    busy = busy + g_ + L2
                if code < PARTIAL0:
                    last_wrong = (code, busy) if code != jersey_code_full(num) else None
        for a, b, code, kind in sightings:
            bad = kind is not None and code < PARTIAL0 and code != jersey_code_full(num)
            for f in range(a, min(b, F)):
                if own_cue[f, p]:
                    jersey[det_index[f, p]] = code
                    if bad:
                        flags[kind][det_index[f, p]] = True
            if p in ov_f:  # his number is read inside the boxes of the players he hides
                i0, i1 = np.searchsorted(ov_f[p], [a, b])
                jersey[det_index[ov_f[p][i0:i1], ov_far[p][i0:i1]]] = code
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
        base = pal["app_true"][cue_from[fr, k]] + ns
        if prof["app_slow_noise"] > 0:  # error that persists (pose, orientation, lighting): one value per second, AR(1)
            grid = ar_noise(int(F * dt) + 2, prof["app_slow_noise"], rngx, 0.0, math.exp(-1.0 / prof["app_slow_tau_s"]), shape=(E,))
            base = base + grid[(fr * dt).astype(int)]
        emb[js] = _unit(base)
        hz = pal["height"][k] + rng.normal(0, prof["sigma_h"], len(fr))
        out = rng.random(len(fr)) < prof["outlier_h"]
        hz[out] = pal["height"][k] + np.where(rng.random(out.sum()) < 0.7, -rng.uniform(0.1, 0.5, out.sum()), rng.uniform(0.1, 0.4, out.sum()))
        height[js] = hz
        run = speed[fr, k] >= prm["gait_min_speed_mps"]
        gn = _unit(pal["gait_true"][k][None, :] + rng.normal(0, prof["gait_noise"], (len(fr), G)))
        gait[js[run]] = gn[run]
    if not o["cues_appearance"]:
        emb[:] = np.nan
    if prm["shuffle_box_order"] if o["shuffle"] is None else o["shuffle"]:
        # boxes of a frame in random order: sorted by true roster index, the order itself leaked identity (RV-13)
        order = np.lexsort((rngo.random(Dn), fi))
        fi, xy, src, nc, cls_obs, jersey, emb, height, gait = (a[order] for a in (fi, xy, src, nc, cls_obs, jersey, emb, height, gait))
        flags = {k: v[order] for k, v in flags.items()}
    dets = Dets(dt, F, fi.astype(np.int64), xy, src.astype(np.int64), nc, cls_obs.astype(np.int64), jersey,
                emb, height, gait, cut, fov)

    # ---------------- what the assigner knows
    oncourt = ~np.isnan(truth.pos[:, :, 0])
    cand, pbp = lineup_feed(truth, oncourt, rng, o, prm, prof, rngx)
    game = Game(truth.team.copy(), list(truth.jersey), pal["height"][:N] + rng.normal(0, prm["height_ref_noise_m"], N),
                pal["template"], pal["gait_ref"], cand)
    info = {"in_fov": in_fov[:, :N], "main": main, "twins": pal["twins"], "height_true": pal["height"][:N],
            "n_officials": R, "n_bystanders": B, "fov": fov, "flags": flags, "pbp_rows": pbp, "sigma_told_factor": told}
    return dets, game, info


FLAG_KEYS = ("colour_run", "overlap_unflagged", "jersey_trunc", "jersey_repeat")
DEFAULT_OPTS = {"refs": True, "fov": True, "live_cuts": True, "occlusion": True, "misses": True, "random_jersey": True,
                "jersey_schedule": {}, "cut_intervals": [], "lineup": True, "pbp_lag": True, "cues_appearance": True,
                "twins": None, "class_schedule": {}, "bystanders": True, "pbp_errors": True, "shuffle": None}


def _read(num, prof, rng, prm=None):
    prm = prm or P
    if rng.random() < prof["p_partial"]:
        digits = list(num)
        d = int(rng.choice(digits)) if rng.random() > prm["partial_random_digit_share"] else int(rng.integers(0, 10))
        return PARTIAL0 + d
    if rng.random() >= prof["e_ocr"]:
        return jersey_code_full(num)
    conf = confusables(num)
    if conf and rng.random() < prm["sim_confusable_share"]:
        return jersey_code_full(str(rng.choice(conf)))
    while True:
        r = NUMBERS[int(rng.integers(0, len(NUMBERS)))]
        if r != num:
            return jersey_code_full(r)


def _palette(truth, prof, rng, R, twins_override, prm, rngx, bteam):
    """True appearance, height and gait per person; templates and references the pack would hold. Same-kit non-players
    (bteam: their team per person) are drawn from the side stream and appended after the officials."""
    N, E, G, B = truth.n, prof["app_dims"], 4, len(bteam)
    kit = _unit(rng.normal(size=(3, E)))
    ind = _unit(rng.normal(size=(N + R, E)))
    gd = _unit(rng.normal(size=(N + R, E)))
    gait = _unit(rng.normal(size=(N + R, G)))
    height = np.concatenate([_heights(truth, rng), rng.normal(*prm["official_height_m"], R)])
    if B:
        hb = SPEC["harness"]["height_by_position_m"]["F"]
        ind = np.concatenate([ind, _unit(rngx.normal(size=(B, E)))])
        gd = np.concatenate([gd, _unit(rngx.normal(size=(B, E)))])
        gait = np.concatenate([gait, _unit(rngx.normal(size=(B, G)))])
        height = np.concatenate([height, rngx.normal(hb[0], hb[1], B)])
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
    d0, dh = prm["twin_app_delta"], prm["twin_height_delta_m"]
    for a, b in pairs:
        dl = d0 if prof["twin_delta"] is None else float(rngx.uniform(*prof["twin_delta"]))  # graded look-alikes
        sc = dl / d0
        ind[b] = _unit(ind[a] + dl * rng.normal(size=E))
        gd[b] = _unit(gd[a] + dl * rng.normal(size=E))
        height[b] = height[a] + sc * rng.uniform(-dh, dh)
        gait[b] = _unit(gait[a] + prm["twin_gait_delta"] * sc * rng.normal(size=G))
        twins.append((a, b))
    cls = np.concatenate([truth.team, np.full(R, 2), bteam]).astype(int)
    season = kit[cls] + prof["app_w_ind"] * ind
    app_true = _unit(season + prof["app_w_game"] * gd)
    tmpl = season + (prof["app_w_game"] * gd if prof["game_card"] else 0)
    tmpl = _unit(tmpl + rng.normal(0, prof["app_noise"] / math.sqrt(prof["template_crops"]), tmpl.shape))
    gref = _unit(gait[:N + R] + rng.normal(0, prm["gait_ref_noise"], (N + R, G)))
    return {"app_true": app_true, "template": tmpl[:N], "height": height, "gait_true": gait, "gait_ref": gref[:N], "twins": twins}


def lineup_feed(truth, oncourt, rng, o, prm, prof=None, rngx=None):
    """-> (candidate mask (F, N), row counts). PBP lineup (true changes shifted by a random lag) widened in substitution
    windows around the PBP time, the only time the assigner knows. With the pbp_* options of the cue profile a row can
    be late, missing (the feed keeps the old five) or name a wrong incoming player, until the team's next logged row."""
    F, N, dt = truth.n_frames, truth.n, truth.dt
    stats = {"rows": 0, "late": 0, "missing": 0, "wrong_player": 0}
    if not o["lineup"]:
        return np.ones((F, N), dtype=bool), stats
    prof = with_options(prof or {})
    err = o["pbp_errors"] and rngx is not None and max(prof["pbp_late_share"], prof["pbp_missing_share"], prof["pbp_wrong_player_share"]) > 0
    core = np.zeros((F, N), dtype=bool)
    cand = np.zeros((F, N), dtype=bool)
    win = frames(prm["sub_window_s"], dt)
    for team in (0, 1):
        cols = np.where(truth.team == team)[0]
        sub = oncourt[:, cols]
        ch = np.where((sub[1:] != sub[:-1]).any(1))[0] + 1
        bounds = [0] + list(ch) + [F]
        prev_end = 0
        feed = sub[0].copy()  # the five the feed lists
        core[:, cols] = feed
        rows = []
        for i in range(1, len(bounds) - 1):
            a = bounds[i]
            lag = frames(rng.uniform(*prm["pbp_lag_s"]), dt) if o["pbp_lag"] else 0
            new = sub[a].copy()
            stats["rows"] += 1
            if err:
                r = rngx.random(5)
                late_lag = frames(rngx.uniform(*prof["pbp_late_s"]), dt)
                if r[0] < prof["pbp_missing_share"]:
                    stats["missing"] += 1
                    continue
                inc, bench = np.where(new & ~feed)[0], np.where(~new & ~feed)[0]
                if r[1] < prof["pbp_wrong_player_share"] and len(inc) and len(bench):
                    new[inc[int(r[2] * len(inc))]] = False
                    new[bench[int(r[3] * len(bench))]] = True
                    stats["wrong_player"] += 1
                if r[4] < prof["pbp_late_share"]:
                    lag = late_lag
                    stats["late"] += 1
            a2 = int(np.clip(a + lag, prev_end, F - 1))
            core[a2:, cols] = new
            prev_end = a2
            rows.append((a2, feed | new))
            feed = new
        cand[:, cols] = core[:, cols]
        for a2, union in rows:
            cand[max(0, a2 - win):min(F, a2 + win), cols] |= union[None, :]
    return cand, stats
