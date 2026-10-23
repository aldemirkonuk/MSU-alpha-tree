"""Run every movement-grammar family on SportVU games and report event rates (validation tier V1b).

Usage: python tools/specgen/movement/realdata.py <game.json>... --out results/movement_test/sportvu_rates.json
       [--max-chunks N] [--noise SIGMA]
Writes aggregates only (events per kind per 48 minutes, timing per family, errors). The SportVU
files stay in the private folder. --noise adds the sim.py noise model to every position first
(validation tier V2: robustness on real motion). --sigma sets the per-frame position sigma the
detectors are told (default 0.15 m, the order of SportVU's own error; with --noise it is
sqrt(sigma^2 + noise^2)). --dump writes every event (game, period, clock, family, kind, actors,
frames, conf, attrs) as JSON lines for calibration; dumps are derived from licensed-unknown data,
so write them only under the private folder or a scratch directory, never the repo.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
import time
import traceback
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[0] / "named_spots"))

from mvlib import DT, build_scene  # noqa: E402
from sim import noise  # noqa: E402
from sportvu import chunks, load_game, team_ends, to_tracks, unique_moments  # noqa: E402

FAMILIES = ["kinematics", "screens", "cuts", "ball_actions", "bigs", "defense", "transition", "composition"]


def flatten(res):
    """detect_all returns a list of Events or a dict of id -> list of Events."""
    if res is None:
        return []
    if isinstance(res, dict):
        out = []
        for v in res.values():
            out.extend(v if isinstance(v, list) else [])
        return out
    return list(res)


def run_chunk(scene, mods, timing, errors, extra_ctx):
    events = {}
    for fam, mod in mods.items():
        t = time.time()
        try:
            if fam == "bigs":
                res = mod.detect_all(scene, screens=extra_ctx.get("screens", []))
            elif fam == "composition" and "cuts" in events:
                res = mod.detect_all(scene, cuts=events["cuts"])  # motion from real cut events (composition C5/C8)
            else:
                res = mod.detect_all(scene)
            events[fam] = flatten(res)
            if fam == "screens":
                extra_ctx["screens"] = [e for e in events[fam] if getattr(e, "kind", "") in ("screen", "ball_screen", "screen_set")]
        except Exception as ex:  # keep going; count the failure
            errors[fam][type(ex).__name__ + ": " + str(ex)[:120]] += 1
            if errors[fam].total() <= 1:
                traceback.print_exc()
            events[fam] = []
        timing[fam] += time.time() - t
    return events


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("games", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-chunks", type=int, default=0)
    ap.add_argument("--noise", type=float, default=0.0)
    ap.add_argument("--sigma", type=float, default=0.15)
    ap.add_argument("--dump", default="")
    ap.add_argument("--families", default=",".join(FAMILIES))
    ap.add_argument("--frame", choices=["nearest_player", "team_ends"], default="team_ends",
                    help="team_ends (default since loop 4): offense = the team that attacks the chunk's end "
                         "in this half (sportvu.team_ends; 12/12 team-halves agree with PBP scoring "
                         "ends); nearest_player is the old rule, wrong in ~25%% of chunks")
    a = ap.parse_args()
    if a.dump and Path(a.dump).resolve().is_relative_to(HERE.parents[2]):
        sys.exit("--dump must point outside the repo (private folder or scratch)")
    dump = open(a.dump, "w") if a.dump else None
    fams = [f for f in FAMILIES if f in a.families.split(",")]
    mods = {f: importlib.import_module(f"detectors.{f}") for f in fams}
    rng = np.random.default_rng(7)
    counts = defaultdict(Counter)
    conf_hist = defaultdict(list)
    timing, errors = Counter(), defaultdict(Counter)
    seconds = 0.0
    n_chunks = 0
    for g in a.games:
        game = load_game(g)
        moments = unique_moments(game)
        ends = team_ends(moments) if a.frame == "team_ends" else None
        for ci, ch in enumerate(chunks(moments)):
            if a.max_chunks and ci >= a.max_chunks:
                break
            got = to_tracks(ch, sigma_p=float(np.hypot(a.sigma, a.noise)), ends=ends)
            if got is None:
                continue
            tracks, off, meta = got
            if a.noise > 0:
                for tr in tracks:
                    tr.x = tr.x + noise(len(tr.x), a.noise, rng)
                    tr.y = tr.y + noise(len(tr.y), a.noise, rng)
            scene = build_scene(tracks)
            seconds += (scene.n - 1) * DT
            n_chunks += 1
            evs = run_chunk(scene, mods, timing, errors, {})
            for fam, lst in evs.items():
                for e in lst:
                    if dump:
                        dump.write(json.dumps({"game": Path(g).stem, "chunk": ci, "period": meta["period"],
                                               "clock0": meta["clock_start"], "fam": fam, "kind": getattr(e, "kind", "?"),
                                               "actors": getattr(e, "actors", {}), "t0": getattr(e, "t0", None),
                                               "start": getattr(e, "start", None), "end": getattr(e, "end", None),
                                               "conf": getattr(e, "conf", None), "attrs": getattr(e, "attrs", {})},
                                              default=str) + "\n")
                    k = getattr(e, "kind", "?")
                    counts[fam][k] += 1
                    c = getattr(e, "conf", None)
                    if c is not None and len(conf_hist[f"{fam}:{k}"]) < 5000:
                        conf_hist[f"{fam}:{k}"].append(float(c))
    per48 = 48 * 60 / max(seconds, 1)
    out = {
        "games": [Path(g).name for g in a.games], "chunks": n_chunks, "seconds_of_play": round(seconds, 1),
        "noise_sigma_p": a.noise, "sigma_told": a.sigma, "frame": a.frame, "note": "rates are per 48 minutes of tracked play, both teams combined",
        "rates_per48": {fam: {k: round(v * per48, 1) for k, v in sorted(c.items(), key=lambda kv: -kv[1])} for fam, c in counts.items()},
        "median_conf": {k: round(float(np.median(v)), 3) for k, v in conf_hist.items() if v},
        "seconds_per_family": {k: round(v, 1) for k, v in timing.items()},
        "realtime_factor": {k: round(v / max(seconds, 1), 4) for k, v in timing.items()},
        "errors": {k: dict(v) for k, v in errors.items()},
    }
    if dump:
        dump.close()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("chunks", "seconds_of_play", "seconds_per_family", "errors")}, indent=1))


if __name__ == "__main__":
    main()
