"""Identity harness on SportVU 2015-16 (config/identity_pack.yaml, harness section).

Usage:
  python tools/specgen/identity/sportvu_truth.py            # once: build the private truth caches
  python tools/specgen/identity/harness.py [--configs full,naive_tracker] [--sigmas 0.15,0.3,0.5]
         [--profiles good,hard] [--games <game id>,...] [--workers 4] [--max-minutes 0] [--seeds 5]
         [--out results/identity_test/sportvu_harness.json]

For every (game, cue profile, sigma_p, seed) the observation simulator draws one set of detections; every
config is run on that same set, so configs differ only in the assigner. --seeds defaults to harness.params.seeds
(seeds 1 .. n): one seed is one draw, and a zero on one draw is not a result (RV-11). Writes aggregates only to
--out (repo); per-player rows and the switch logs go to --private-out (never the repo). Every run entry carries
the spec version and the hashes of the YAML it ran with; every summary row carries its exposure (labelled
player-hours, crossings, chains) and the upper bound on the swap rate. Pools are capped at 4 workers
(memory-limited machine); run one harness at a time.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import zlib
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import idlib  # noqa: E402
import metrics  # noqa: E402
import sportvu_truth  # noqa: E402
from obsmodel import observe, profile  # noqa: E402

REPO = HERE.parents[2]
MAX_WORKERS = 4
PROBABLE_KEYS = ["probable_labels", "probable_wrong_frames", "probable_wrong_events", "probable_on_officials",
                 "probable_error_rate", "probable_coverage_gain", "coverage_with_probable"]
CUE_STAT_KEYS = ["legible_frame_share", "full_read_frame_share", "sightings_per_visible_s", "no_read_window_share",
                 "app_rank1_teammates", "app_rank1_teammates_lookalikes"]
SUMMARY_KEYS = ["swap_events", "idsw", "wrong_label_frames", "labels_on_officials", "idf1", "idp", "idr", "hota", "deta",
                "assa", "coverage", "coverage_of_view", "min_player_coverage", "crossings", "reconfirm_median_s",
                "reconfirm_p90_s", "reconfirm_within_2s", "reconfirm_censored"]


def game_code(gid):
    """Repo outputs carry G1 / G2 / G3, never a real game id: the private game_codes.json mapping when present, else
    the position of the game in the sorted private truth cache."""
    if str(gid).startswith("G"):
        return str(gid)
    f = sportvu_truth.PRIVATE / "work" / "identity_harness_2026-10-25" / "game_codes.json"
    if f.exists():
        inv = {v: k for k, v in json.loads(f.read_text()).items()}
        if gid in inv:
            return inv[gid]
    cached = sorted(p.stem for p in sportvu_truth.CACHE.glob("*.npz"))
    return f"G{cached.index(gid) + 1}" if gid in cached else "G?"


def spec_hashes():
    """sha256 of the YAML file, and of what the code reads from it (every parameter, the cue profiles with their option
    defaults, the configs and the height table): the second does not change when only prose or the journal is edited."""
    h = idlib.SPEC["harness"]
    strip = lambda blk: {k: {a: b for a, b in v.items() if a != "note"} for k, v in blk.items()}  # noqa: E731
    behaviour = json.dumps({"params": idlib.P, "cue_profiles": strip(h["cue_profiles"]), "configs": strip(h["configs"]),
                            "option_defaults": {k: v["default"] for k, v in h["cue_profile_options"].items()},
                            "height_by_position_m": h["height_by_position_m"]}, sort_keys=True, default=str)
    return {"yaml_sha256": hashlib.sha256(idlib.SPEC_PATH.read_bytes()).hexdigest(),
            "params_sha256": hashlib.sha256(behaviour.encode()).hexdigest()}


def swap_contexts(d, label, crossings, dt, near_s=3.0):
    """Classify each wrong-label run: after a true crossing of that player (<= near_s), after a cut, other."""
    near = int(round(near_s / dt))
    cuts = np.where(d.cut)[0]
    by_p = defaultdict(list)
    for e, p, q in crossings:
        by_p[p].append(e)
        by_p[q].append(e)
    out = defaultdict(int)
    wrong = (label >= 0) & (label != d.src)
    merge = int(round(1.0 / dt))
    for p in np.unique(d.src[wrong]):
        fr = np.sort(d.frame[wrong & (d.src == p)])
        starts = fr[np.r_[True, np.diff(fr) > merge]]
        for s in starts:
            if p < 0:
                out["official"] += 1
            elif any(0 <= s - e <= near for e in by_p.get(int(p), [])):
                out["after_crossing"] += 1
            elif len(cuts) and 0 <= s - cuts[np.searchsorted(cuts, s, "right") - 1] <= 5 * near:
                out["after_cut"] += 1
            else:
                out["other"] += 1
    return dict(out)


def job(args):
    gid, prof_name, sigma, seed, cfg_names, max_minutes = args
    t0 = time.time()
    tr = sportvu_truth.load(gid, max_minutes=max_minutes)
    rng = np.random.default_rng(zlib.crc32(f"{gid}|{prof_name}|{sigma}|{seed}".encode()))
    prof = profile(prof_name)
    d, g, info = observe(tr, prof, sigma, rng)
    told = sigma * info["sigma_told_factor"]  # the assigner's sigma_p (exact unless the profile sets sigma_told_range)
    cue = {"game": game_code(gid), "profile": prof_name, "sigma_p": sigma, "seed": seed,
           **metrics.cue_stats(d, g, info, ~np.isnan(tr.pos[:, :, 0])), "pbp_rows": info["pbp_rows"],
           "sigma_told_factor": round(info["sigma_told_factor"], 4)}
    prm = dict(idlib.P)
    prm.update(prof.get("assigner_overrides") or {})  # cue parameters fitted for this recording quality
    crossings = metrics.true_crossings(tr.pos, tr.dt)
    t_sim = time.time() - t0
    rows, private = [], []
    for name in cfg_names:
        cfg = dict(idlib.SPEC["harness"]["configs"][name])
        if not cfg.get("lineup", True):
            g2 = idlib.Game(g.team, g.jersey, g.height_ref, g.template, g.gait_ref, np.ones_like(g.cand))
        else:
            g2 = g
        t1 = time.time()
        res = idlib.run(d, g2, cfg, told, prm)
        for mode in ("live", "offline"):
            r = res[mode]
            m = metrics.identity_metrics(d, r.label, info["in_fov"], d.dt, crossings)
            inv = metrics.invariant_breaks(d, r.label, g.cand, g.team)
            row = {"game": game_code(gid), "profile": prof_name, "sigma_p": sigma, "seed": seed, "config": name, "mode": mode}
            row.update({k: m.get(k) for k in SUMMARY_KEYS})
            row.update(inv)
            row["swap_context"] = swap_contexts(d, r.label, crossings, d.dt)
            row["swap_mechanism"] = metrics.swap_mechanisms(d, r.label, g.cand, g.team, info["flags"], d.dt, info["n_officials"],
                                                           r.det_chain)
            row.update(metrics.chain_purity(d, r.chains, g.team, r.label))
            row["labels"] = int(np.sum((r.label >= 0) & (d.src >= 0)))
            row["labels_on_bystanders"] = int(np.sum((r.label >= 0) & (d.src < -info["n_officials"])))
            row["calibration"] = metrics.calibration(d, r.label, r.post)
            row["alarms"] = r.stats["alarms"]
            row["offline_splits"] = sum(1 for x in r.log if x.get("kind") == "offline_split")
            row["dup_guard"] = r.stats["dup_guard"]
            row["enum_fallback_frames"] = r.stats["enum_fallback_frames"]
            row["n_tracklets"], row["n_chains"] = res["n_tracklets"], res["n_chains"]
            row["end_reasons"] = res["end_reasons"]
            row["seconds"] = round(time.time() - t1, 1)
            row["frames"] = int(d.n_frames)
            row["player_dets"] = m["player_dets"]
            pc = []
            if mode == "offline" and r.probable is not None:  # OD-8 probable tier: reported apart, never in the locked metrics
                pm = metrics.probable_metrics(d, r.label, r.probable, d.dt)
                pc = pm.pop("probable_confusion_pairs")
                row.update(pm)
            rows.append(row)
            private.append({**{k: row[k] for k in ("game", "profile", "sigma_p", "seed", "config", "mode")}, "game_id": gid,
                            "per_player": m["per_player"], "confusion_pairs": m["confusion_pairs"],
                            "probable_confusion_pairs": pc, "log": r.log[:500]})
    return rows, private, round(t_sim, 1), cue


def aggregate(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[(r["config"], r["profile"], r["sigma_p"], r["mode"])].append(r)
    out = []
    for (cfg, prof, sig, mode), rs in sorted(groups.items()):
        a = {"config": cfg, "profile": prof, "sigma_p": sig, "mode": mode, "games": len(rs)}
        a["seeds"] = sorted({r["seed"] for r in rs})
        a["runs_with_swaps"] = int(sum(1 for r in rs if r["swap_events"]))
        for k in ("swap_events", "idsw", "wrong_label_frames", "labels_on_officials", "labels_on_bystanders", "alarms", "offline_splits",
                  "inv1_duplicates", "inv2_over_five", "inv3_outside_lineup", "crossings", "reconfirm_censored", "dup_guard",
                  "clean_chains", "clean_chain_boxes", "impure_clean_chains", "impure_minority_boxes", "impure_teammate_boxes",
                  "impure_opponent_boxes", "impure_non_player_boxes", "impure_labelled_boxes"):
            a[k] = int(sum(r.get(k) or 0 for r in rs))
        if all(r.get("labels") is not None for r in rs):
            dt = sportvu_truth.SV_DT
            a["exposure"] = metrics.exposure(a["swap_events"], sum(r["frames"] for r in rs) * dt / 60.0, sum(r["labels"] for r in rs) * dt / 3600.0,
                                             a["crossings"], sum(r["n_chains"] for r in rs), len(rs))
        cal = None
        for r in rs:
            if r.get("calibration"):
                if cal is None:
                    cal = [dict(b) for b in r["calibration"]]
                else:
                    for b, x in zip(cal, r["calibration"]):
                        b["labels"] += x["labels"]
                        b["wrong"] += x["wrong"]
        a["calibration"] = cal
        w = np.array([r["player_dets"] for r in rs], dtype=float)
        for k in ("idf1", "idp", "idr", "hota", "deta", "assa", "coverage", "coverage_of_view", "reconfirm_within_2s"):
            v = np.array([r[k] if r[k] is not None else np.nan for r in rs], dtype=float)
            a[k] = round(float(np.nansum(v * w) / w[~np.isnan(v)].sum()), 4) if (~np.isnan(v)).any() else None
        for k in ("reconfirm_median_s", "reconfirm_p90_s", "min_player_coverage"):
            v = [r[k] for r in rs if r[k] is not None]
            a[k] = round(float(np.median(v) if "reconfirm" in k else np.min(v)), 3) if v else None
        ctx = defaultdict(int)
        for r in rs:
            for k, v in r["swap_context"].items():
                ctx[k] += v
        a["swap_context"] = dict(ctx)
        mech = defaultdict(int)
        for r in rs:
            for k, v in (r.get("swap_mechanism") or {}).items():
                mech[k] += v
        a["swap_mechanism"] = dict(mech)
        if any(r.get("probable_labels") is not None for r in rs):  # OD-8 probable tier (offline)
            for k in ("probable_labels", "probable_wrong_frames", "probable_wrong_events", "probable_on_officials"):
                a[k] = int(sum(r.get(k) or 0 for r in rs))
            a["probable_error_rate"] = round(a["probable_wrong_frames"] / a["probable_labels"], 5) if a["probable_labels"] else None
            for k in ("probable_coverage_gain", "coverage_with_probable"):
                v = np.array([r.get(k) if r.get(k) is not None else np.nan for r in rs], dtype=float)
                a[k] = round(float(np.nansum(v * w) / w[~np.isnan(v)].sum()), 4) if (~np.isnan(v)).any() else None
        out.append(a)
    return out


def aggregate_cue_stats(cues):
    """Per cue profile: what the simulator assumes, in literature units (weighted by player boxes), and the lineup rows."""
    out = []
    for prof in sorted({c["profile"] for c in cues}):
        cs = [c for c in cues if c["profile"] == prof]
        w = np.array([c["player_dets"] for c in cs], dtype=float)
        a = {"profile": prof, "runs": len(cs)}
        for k in CUE_STAT_KEYS:
            v = np.array([c[k] if c.get(k) is not None else np.nan for c in cs], dtype=float)
            a[k] = round(float(np.nansum(v * w) / w[~np.isnan(v)].sum()), 4) if (~np.isnan(v)).any() else None
        a["pbp_rows"] = {k: int(sum(c["pbp_rows"][k] for c in cs)) for k in cs[0]["pbp_rows"]}
        out.append(a)
    return out


def build_parser():
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", default=",".join(sorted(p.stem for p in sportvu_truth.CACHE.glob("*.npz"))),
                    help="SportVU game ids in the private truth cache (default: all cached games)")
    ap.add_argument("--configs", default=",".join(idlib.SPEC["harness"]["configs"]))
    ap.add_argument("--sigmas", default=",".join(str(s) for s in idlib.SPEC["harness"]["noise_grid_sigma_p_m"]))
    ap.add_argument("--profiles", default="good")
    ap.add_argument("--seeds", type=int, default=int(idlib.P["seeds"]), help="seeds 1 .. n per game, profile and sigma_p")
    ap.add_argument("--workers", type=int, default=MAX_WORKERS)
    ap.add_argument("--max-minutes", type=float, default=0.0)
    ap.add_argument("--out", default=str(REPO / idlib.SPEC["harness"]["results_file"]))
    ap.add_argument("--private-out", default=str(sportvu_truth.PRIVATE / "work" / "identity_harness_2026-10-25" / "runs"))
    ap.add_argument("--tag", default="")
    ap.add_argument("--append", action="store_true", help="merge into an existing --out (rows with the same key are replaced)")
    return ap


def main():
    a = build_parser().parse_args()
    priv = Path(a.private_out)
    sportvu_truth._guard(priv)
    workers = max(1, min(a.workers, MAX_WORKERS))
    cfgs = a.configs.split(",")
    jobs = [(gm, pf, float(s), sd, [c], a.max_minutes) for c in cfgs for gm in a.games.split(",") for pf in a.profiles.split(",")
            for s in a.sigmas.split(",") for sd in range(1, a.seeds + 1)]
    t0 = time.time()
    hashes = spec_hashes()  # of the YAML the workers loaded
    rows, private, cues = [], [], []
    with Pool(workers) as pool:
        for r, p, ts, cue in pool.imap_unordered(job, jobs):
            rows.extend(r)
            private.extend(p)
            cues.append(cue)
            print(f"done {r[0]['game']} {r[0]['profile']} sigma {r[0]['sigma_p']} (sim {ts}s); "
                  + "; ".join(f"{x['config']}/{x['mode']}: swaps {x['swap_events']} idf1 {x['idf1']:.3f} cov {x['coverage']:.3f}" for x in r),
                  flush=True)
    outp = Path(a.out)
    if a.tag:
        outp = outp.with_name(outp.stem + f"_{a.tag}" + outp.suffix)
    key = lambda r: (r["game"], r["profile"], r["sigma_p"], r["seed"], r["config"], r["mode"])  # noqa: E731
    runs = [{"games": len(a.games.split(",")), "profiles": a.profiles.split(","), "sigmas": [float(s) for s in a.sigmas.split(",")],
             "configs": cfgs, "seeds": a.seeds, "max_minutes": a.max_minutes, "wall_s": round(time.time() - t0, 1),
             "spec_version": idlib.SPEC["version"], "date": time.strftime("%Y-%m-%d"), **hashes}]
    for r in rows:  # every row says which spec produced it (rows of older runs survive --append)
        r["spec_version"], r["params_sha256"] = idlib.SPEC["version"], hashes["params_sha256"]
    ckey = lambda c: (c["game"], c["profile"], c["sigma_p"], c["seed"])  # noqa: E731
    seen = set()
    cues = [c for c in cues if not (ckey(c) in seen or seen.add(ckey(c)))]  # one per detection set (jobs are per config)
    if a.append and outp.exists():
        prev = json.loads(outp.read_text())
        new_keys = {key(r) for r in rows}
        rows = [r for r in prev["per_game"] if key(r) not in new_keys] + rows
        runs = prev.get("runs", []) + runs
        cues = [c for c in prev.get("cue_stats_runs", []) if ckey(c) not in seen] + cues
    out = {"spec_version": idlib.SPEC["version"], **hashes, "date": time.strftime("%Y-%m-%d"), "dt": sportvu_truth.SV_DT, "runs": runs,
           "frames_note": "SportVU 25 Hz; truth ids from SportVU; cues simulated (obsmodel.py)",
           "summary": aggregate(rows), "cue_stats": aggregate_cue_stats(cues), "cue_stats_runs": cues, "per_game": rows}
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=1, default=float))
    priv.mkdir(parents=True, exist_ok=True)
    pp = priv / (outp.stem + "_private.jsonl")
    with open(pp, "a" if a.append else "w") as fh:
        for row in private:
            fh.write(json.dumps(row, default=str) + "\n")
    print("wrote", outp)


if __name__ == "__main__":
    main()
