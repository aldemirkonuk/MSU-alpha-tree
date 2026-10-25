"""Identity metrics of config/identity_pack.yaml (metrics section), computed against harness truth.

Inputs: detections (src = true person; officials negative), emitted labels (HOLD = -1), and the
in-view mask (F, N) of true players. All counts are plain integers so results can be aggregated.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import linear_sum_assignment

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


def true_crossings(pos, dt, d_cross=1.0, flip_deg=90.0, pad_s=0.3):
    """Crossing events from true positions: centre distance < d_cross with bearing flip >= flip_deg
    (the id_swap_risk crossed attribute of config/movement_grammar/bigs.yaml). -> list of (end_frame, p, q)."""
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


def reconfirm_times(d, label, crossings, dt, horizon_s=10.0):
    """Time from the end of each true crossing to each player's first correctly labelled detection."""
    H = int(round(horizon_s / dt))
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


def calibration(d, label, post, edges=(0.995, 0.999, 0.9999, 1.0000001)):
    """Emitted labels per posterior bin and how many were wrong (ACC-8)."""
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
