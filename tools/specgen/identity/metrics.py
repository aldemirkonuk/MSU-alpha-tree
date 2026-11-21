"""Identity metrics of config/identity_pack.yaml (metrics section), computed against harness truth.

Inputs: detections (src = true person; officials negative), emitted labels (HOLD = -1), and the
in-view mask (F, N) of true players. All counts are plain integers so results can be aggregated.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import chi2

from idlib import P, PARTIAL0

HOLD = -1


def _runs(frames_sorted, merge_gap):
    """Number of runs in a sorted frame list, runs closer than merge_gap merged."""
    if len(frames_sorted) == 0:
        return 0
    return int(1 + np.sum(np.diff(frames_sorted) > merge_gap))


def identity_metrics(d, label, in_fov, dt, crossings=None):
    src, fr = d.src, d.frame
    N = in_fov.shape[1]
    is_pl = src >= 0
    emitted = label >= 0
    correct = emitted & is_pl & (label == src)
    wrong = emitted & ~(is_pl & (label == src))
    out = {}
    # swap events and IDSW
    merge = int(round(1.0 / dt))
    swap_events, idsw = 0, 0
    swap_frames_by_pair = {}
    for p in range(N):
        m = is_pl & (src == p)
        if not m.any():
            continue
        lab = label[m]
        f = fr[m]
        w = (lab >= 0) & (lab != p)
        swap_events += _runs(f[w], merge)
        for q in np.unique(lab[w]):
            swap_frames_by_pair[(p, int(q))] = int(np.sum(lab[w] == q))
        e = lab[lab >= 0]
        idsw += int(np.sum(e[1:] != e[:-1]))
    off_wrong = emitted & ~is_pl
    for k in np.unique(src[~is_pl]):
        swap_events += _runs(fr[off_wrong & (src == k)], merge)
    out["swap_events"] = swap_events
    out["idsw"] = idsw
    out["wrong_label_frames"] = int(wrong.sum())
    out["labels_on_officials"] = int(off_wrong.sum())
    out["confusion_pairs"] = sorted(swap_frames_by_pair.items(), key=lambda kv: -kv[1])[:20]
    # IDF1 (Ristani): optimal 1-1 matching true player <-> label
    gt_total = int(in_fov.sum())
    pred_total = int(emitted.sum())
    co = np.zeros((N, N))
    np.add.at(co, (src[emitted & is_pl], label[emitted & is_pl]), 1)
    r, c = linear_sum_assignment(-co)
    idtp = float(co[r, c].sum())
    out["idf1"] = 2 * idtp / max(1.0, gt_total + pred_total)
    out["idp"] = idtp / max(1.0, pred_total)
    out["idr"] = idtp / max(1.0, gt_total)
    # HOTA (source-matched, single threshold)
    tp_mask = emitted & is_pl
    TP = int(tp_mask.sum())
    FN = gt_total - TP
    FP = int((emitted & ~is_pl).sum())
    deta = TP / max(1, TP + FN + FP)
    gt_count = in_fov.sum(0).astype(float)
    pred_count = np.bincount(label[emitted], minlength=N).astype(float)
    tpa = co
    ass = 0.0
    if TP:
        gi, li = np.nonzero(tpa)
        vals = tpa[gi, li]
        ratio = vals / (gt_count[gi] + pred_count[li] - vals)
        ass = float((vals * ratio).sum() / TP)
    out["deta"] = deta
    out["assa"] = ass
    out["hota"] = float(np.sqrt(deta * ass))
    # coverage and per-player accuracy
    out["player_dets"] = int(is_pl.sum())
    out["coverage"] = float(tp_mask.sum() / max(1, is_pl.sum()))
    out["coverage_of_view"] = float(correct.sum() / max(1, gt_total))
    acc = {}
    for p in range(N):
        g = int(in_fov[:, p].sum())
        if g == 0:
            continue
        cp = int((correct & (src == p)).sum())
        ep = int((emitted & (label == p)).sum())
        acc[p] = {"in_view": g, "accuracy": cp / g, "precision": cp / ep if ep else None}
    out["per_player"] = acc
    out["min_player_coverage"] = min((v["accuracy"] for v in acc.values() if v["in_view"] * dt >= 300.0), default=None)
    if crossings is not None:
        out.update(reconfirm_times(d, label, crossings, dt))
    return out


def true_crossings(pos, dt, d_cross=None, flip_deg=None, pad_s=None):
    """Crossing events from true positions: centre distance < d_cross with bearing flip >= flip_deg
    (the id_swap_risk crossed attribute of config/movement_grammar/bigs.yaml). -> list of (end_frame, p, q)."""
    d_cross = P["crossing_dist_m"] if d_cross is None else d_cross
    flip_deg = P["crossing_flip_deg"] if flip_deg is None else flip_deg
    pad_s = P["crossing_pad_s"] if pad_s is None else pad_s
    F, N, _ = pos.shape
    pad = max(1, int(round(pad_s / dt)))
    on = ~np.isnan(pos[:, :, 0])
    out = []
    for p in range(N):
        for q in range(p + 1, N):
            both = on[:, p] & on[:, q]
            if not both.any():
                continue
            dv = pos[:, q] - pos[:, p]
            dist = np.hypot(dv[:, 0], dv[:, 1])
            close = both & (dist < d_cross)
            if not close.any():
                continue
            idx = np.where(close)[0]
            brk = np.where(np.diff(idx) > 1)[0] + 1
            for run in np.split(idx, brk):
                a, b = run[0], run[-1]
                a0, b1 = a - pad, b + pad
                if a0 < 0 or b1 >= F or not (both[a0] and both[b1]):
                    continue
                ang0 = np.degrees(np.arctan2(dv[a0, 1], dv[a0, 0]))
                ang1 = np.degrees(np.arctan2(dv[b1, 1], dv[b1, 0]))
                flip = abs((ang1 - ang0 + 180) % 360 - 180)
                if flip >= flip_deg:
                    out.append((int(b), p, q))
    return out


def reconfirm_times(d, label, crossings, dt, horizon_s=None):
    """Time from the end of each true crossing to each player's first correctly labelled detection."""
    H = int(round((P["reconfirm_horizon_s"] if horizon_s is None else horizon_s) / dt))
    by_p = {}
    for p in np.unique(d.src[d.src >= 0]):
        m = (d.src == p) & (label == p)
        by_p[int(p)] = np.sort(d.frame[m])
    times, censored = [], 0
    for e, p, q in crossings:
        for x in (p, q):
            arr = by_p.get(x, np.zeros(0))
            k = np.searchsorted(arr, e)
            if k < len(arr) and arr[k] - e <= H:
                times.append((arr[k] - e) * dt)
            else:
                censored += 1
    t = np.array(times)
    n = len(t) + censored
    return {"crossings": len(crossings),
            "reconfirm_median_s": float(np.median(t)) if len(t) else None,
            "reconfirm_p90_s": float(np.percentile(t, 90)) if len(t) else None,
            "reconfirm_within_2s": float(np.sum(t <= 2.0) / n) if n else None,
            "reconfirm_censored": censored}


def calibration(d, label, post, edges=None):
    """Emitted labels per posterior bin and how many were wrong (ACC-8)."""
    edges = tuple(P["calibration_edges"]) + (1.0000001,) if edges is None else edges
    out = []
    m = label >= 0
    for lo, hi in zip(edges[:-1], edges[1:]):
        b = m & (post >= lo) & (post < hi)
        out.append({"bin": [lo, min(hi, 1.0)], "labels": int(b.sum()), "wrong": int(np.sum(b & (label != d.src)))})
    return out


def invariant_breaks(d, label, cand, team=None):
    """ID-INV-1 (duplicate label in a frame), ID-INV-2 (more than five labels of a team in a frame outside a
    substitution window) and ID-INV-3 (label outside the candidate set)."""
    dup, over5 = 0, 0
    for f in np.unique(d.frame[label >= 0]):
        lo, hi = d.fstart[f], d.fstart[f + 1]
        lab = label[lo:hi]
        lab = lab[lab >= 0]
        dup += len(lab) - len(np.unique(lab))
        if team is not None:
            for t in (0, 1):
                if np.sum(team[lab] == t) > 5 and cand[f, team == t].sum() <= 5:
                    over5 += 1
    m = label >= 0
    outside = int(np.sum(~cand[d.frame[m], label[m]]))
    out = {"inv1_duplicates": int(dup), "inv3_outside_lineup": outside}
    if team is not None:
        out["inv2_over_five"] = int(over5)
    return out


def probable_metrics(d, label, probable, dt):
    """OD-8 probable tier (offline, flagged, viewer-only): coverage it adds on top of the locked labels and how often it
    is wrong. Wrong probable labels are logged here and are never counted as locked swaps (swap_events reads `label`)."""
    src, fr = d.src, d.frame
    is_pl = src >= 0
    pm = (probable >= 0) & (label < 0)  # probable only where the locked tier abstains
    wrong = pm & ~(is_pl & (probable == src))
    merge = int(round(1.0 / dt))
    events, pairs = 0, {}
    for p in np.unique(src[wrong]):
        m = wrong & (src == p)
        events += _runs(np.sort(fr[m]), merge)
        if p >= 0:
            for q in np.unique(probable[m]):
                pairs[(int(p), int(q))] = int(np.sum(probable[m] == q))
    n_pl = max(1, int(is_pl.sum()))
    locked_cov = float(((label >= 0) & is_pl).sum() / n_pl)
    gain = float((pm & is_pl).sum() / n_pl)
    return {"probable_labels": int(pm.sum()), "probable_wrong_frames": int(wrong.sum()), "probable_wrong_events": events,
            "probable_on_officials": int((pm & ~is_pl).sum()),
            "probable_error_rate": float(wrong.sum() / pm.sum()) if pm.any() else None,
            "probable_coverage_gain": gain, "coverage_with_probable": locked_cov + gain,
            "probable_confusion_pairs": sorted(pairs.items(), key=lambda kv: -kv[1])[:20]}


def poisson_upper(k, conf=None):
    """One-sided upper confidence bound on a Poisson mean after k events (exact; 3.0 for k = 0 at 95 %)."""
    conf = P["bound_confidence"] if conf is None else conf
    return float(chi2.ppf(conf, 2 * (k + 1)) / 2)


def exposure(swap_events, play_minutes, labelled_player_hours, crossings, chains, game_runs):
    """What a swap count was measured on, and the rate it supports: zero events is a bound, never a proof of zero.
    Rates and one-sided upper bounds (bound_confidence) per labelled player-hour, per true crossing and per game of
    game_minutes of play."""
    up = poisson_upper(int(swap_events))
    per = lambda x, d_: (round(x / d_, 6) if d_ else None)  # noqa: E731
    games = play_minutes / P["game_minutes"]
    return {"game_runs": int(game_runs), "play_minutes": round(play_minutes, 1), "labelled_player_hours": round(labelled_player_hours, 2),
            "crossings": int(crossings), "chains": int(chains), "swap_events": int(swap_events),
            "rate_per_labelled_player_hour": per(swap_events, labelled_player_hours), "upper_per_labelled_player_hour": per(up, labelled_player_hours),
            "rate_per_crossing": per(swap_events, crossings), "upper_per_crossing": per(up, crossings),
            "rate_per_game": per(swap_events, games), "upper_per_game": per(up, games), "confidence": P["bound_confidence"]}


def chain_purity(d, chains, team, label=None):
    """Purity of the clean chains (every chain that may carry a label), measured against the truth ids.

    A clean chain is impure when its boxes belong to more than one true person; its minority boxes are the boxes of
    anyone but its most frequent person, counted by what the foreign person is to that person (teammate, opponent,
    non_player = official or same-kit bystander). impure_labelled_boxes = minority boxes that carry a locked label
    (each one is a wrong label or a label on a non-player). Purity is a measured property: the tracklet tests
    reduce it, they do not guarantee it. -> dict of counts."""
    out = {"clean_chains": 0, "clean_chain_boxes": 0, "impure_clean_chains": 0, "impure_minority_boxes": 0,
           "impure_teammate_boxes": 0, "impure_opponent_boxes": 0, "impure_non_player_boxes": 0, "impure_labelled_boxes": 0}
    for c in chains:
        if c.kind == "amb" or len(c.dets) == 0:
            continue
        src = d.src[c.dets]
        out["clean_chains"] += 1
        out["clean_chain_boxes"] += len(src)
        if np.all(src == src[0]):
            continue
        vals, cnt = np.unique(src, return_counts=True)
        maj = int(vals[np.argmax(cnt)])
        mn = src != maj
        out["impure_clean_chains"] += 1
        out["impure_minority_boxes"] += int(mn.sum())
        non = mn & (src < 0) if maj >= 0 else mn & (src >= 0)
        same = mn & (src >= 0) & (team[np.maximum(src, 0)] == team[maj]) if maj >= 0 else mn & (src < 0)
        out["impure_non_player_boxes"] += int(non.sum())
        out["impure_teammate_boxes"] += int(same.sum())
        out["impure_opponent_boxes"] += int((mn & ~non & ~same).sum())
        if label is not None:
            out["impure_labelled_boxes"] += int(np.sum(label[c.dets][mn] >= 0))
    return out


def swap_mechanisms(d, label, cand, team, flags, dt, n_officials, det_chain=None):
    """Each wrong-label run (the swap_events definition) attributed to the first simulated error that fits, in this
    order: same_kit_non_player / official (the box is not a player), lineup_wrong (the true player was not a candidate),
    overlap_unflagged, colour_run (that error touched the person within mechanism_window_s before the run or during
    it), jersey_misread (truncated or repeated wrong read within jersey_mechanism_window_s), else other (tracklet
    impurity, appearance, ...). Attribution by co-occurrence. cross_team counts runs labelled as a player of the
    other team. impure_chain (needs det_chain) counts, on top of that attribution, the runs whose chain also holds
    boxes of the labelled player himself: the chain's label is right and the box is foreign (tracklet impurity);
    every other run is a wrong decision about a whole chain (evidence model or lineup). -> dict of counts."""
    out = {}
    merge = int(round(1.0 / dt))
    w_s, w_j = int(round(P["mechanism_window_s"] / dt)), int(round(P["jersey_mechanism_window_s"] / dt))
    wrong = (label >= 0) & (label != d.src)
    jersey_bad = flags["jersey_trunc"] | flags["jersey_repeat"]
    own_chains = set()  # (chain, label) pairs where the chain holds boxes of the labelled player
    if det_chain is not None:
        m_ = (det_chain >= 0) & (d.src >= 0)
        own_chains = set(zip(det_chain[m_].tolist(), d.src[m_].tolist()))
    for p in np.unique(d.src[wrong]):
        mp = d.src == p
        fr_p = d.frame[mp]
        o_ = np.argsort(fr_p, kind="stable")
        fr_p = fr_p[o_]
        w_p, lab_p = wrong[mp][o_], label[mp][o_]
        ch_p = det_chain[mp][o_] if det_chain is not None else None
        fl = {k: flags[k][mp][o_] for k in ("overlap_unflagged", "colour_run")}
        jb = jersey_bad[mp][o_]
        fw = fr_p[w_p]
        starts = np.r_[True, np.diff(fw) > merge]
        for a, b in zip(fw[starts], _run_ends(fw, merge)):
            if p < 0:
                key = "official" if p >= -n_officials else "same_kit_non_player"
            else:
                near = (fr_p >= a - w_s) & (fr_p <= b)
                if not cand[a, p]:
                    key = "lineup_wrong"
                elif fl["overlap_unflagged"][near].any():
                    key = "overlap_unflagged"
                elif fl["colour_run"][near].any():
                    key = "colour_run"
                elif jb[(fr_p >= a - w_j) & (fr_p <= b)].any():
                    key = "jersey_misread"
                else:
                    key = "other"
                lab = lab_p[w_p & (fr_p >= a) & (fr_p <= b)]
                if (team[lab] != team[p]).any():
                    out["cross_team"] = out.get("cross_team", 0) + 1
            out[key] = out.get(key, 0) + 1
            if ch_p is not None:
                in_run = w_p & (fr_p >= a) & (fr_p <= b)
                if any((int(c_), int(l_)) in own_chains for c_, l_ in zip(ch_p[in_run], lab_p[in_run])):
                    out["impure_chain"] = out.get("impure_chain", 0) + 1
    return out


def _run_ends(frames_sorted, merge_gap):
    """Last frame of each run of a sorted frame list (runs closer than merge_gap merged)."""
    brk = np.diff(frames_sorted) > merge_gap
    return np.r_[frames_sorted[:-1][brk], frames_sorted[-1]]


def cue_stats(d, g, info, oncourt):
    """What a cue profile assumes, in the units the literature reports (so it can be compared with measurements):
    share of player boxes with a jersey read, sightings per visible second, share of sighting_window_s windows of
    visible time without any read, and single-crop appearance rank-1 among the on-court teammates (look-alike pairs
    apart). oncourt: (F, N) true on-court mask."""
    N, F, dt = g.n, d.n_frames, d.dt
    isp = d.src >= 0
    has_read = d.jersey >= 0
    out = {"player_dets": int(isp.sum()), "legible_frame_share": float((has_read & isp).sum() / max(1, isp.sum())),
           "full_read_frame_share": float((has_read & (d.jersey < PARTIAL0) & isp).sum() / max(1, isp.sum()))}
    w = int(round(P["sighting_window_s"] / dt))
    n_sight, vis_s, n_win, n_null = 0, 0.0, 0, 0
    for p in range(N):
        m = d.src == p
        if not m.any():
            continue
        fr = d.frame[m]
        rd = np.zeros(F, dtype=bool)
        rd[fr[has_read[m]]] = True
        vis = np.zeros(F, dtype=bool)
        vis[fr] = True
        n_sight += int(np.sum(np.diff(np.r_[0, rd.astype(np.int8)]) == 1))
        vis_s += vis.sum() * dt
        r = rd[vis]
        k = len(r) // w
        if k:
            n_win += k
            n_null += int((~r[:k * w].reshape(k, w).any(1)).sum())
    out["sightings_per_visible_s"] = n_sight / vis_s if vis_s else None
    out["no_read_window_share"] = n_null / n_win if n_win else None
    if d.emb is not None and g.template is not None:
        idx = np.flatnonzero(isp & ~np.isnan(d.emb[:, 0]))
        src = d.src[idx]
        sims = d.emb[idx] @ g.template.T
        mates = oncourt[d.frame[idx]] & (g.team[None, :] == g.team[src][:, None])
        hit = np.argmax(np.where(mates, sims, -np.inf), axis=1) == src
        tw = np.isin(src, [int(x) for pair in info["twins"] for x in pair])
        out["app_rank1_teammates"] = float(hit[~tw].mean()) if (~tw).any() else None
        out["app_rank1_teammates_lookalikes"] = float(hit[tw].mean()) if tw.any() else None
    return out
