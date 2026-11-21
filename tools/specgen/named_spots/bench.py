"""Time the evaluation of every exact rule for 10 players and the ball (one frame).

One environment is built per object for the right side and one for the mirrored side, and every
compiled expr is evaluated in it: the loop a loader would run. Contexts are all present.
Usage: python tools/specgen/named_spots/bench.py [--frames 300] [--write-summary]
--write-summary stores the result in results/named_spots_test/speed.json (the page prints it).
"""
import argparse, datetime, json, random, statistics, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spotlib import MIRROR_X, env, load  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SUMMARY = ROOT / "results" / "named_spots_test" / "speed.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=300)
    ap.add_argument("--write-summary", action="store_true")
    a = ap.parse_args()
    doc, spots = load()
    coded = [s for s in spots.values() if s.code]
    plain = [s.code for s in coded if s.side != "mirrored"]
    mirrored = [s.code for s in coded if s.side == "mirrored"]
    R = random.Random(7)
    G = {"__builtins__": {}}
    times, evals = [], 0
    for _ in range(a.frames):
        pos = [(R.uniform(-7.5, 7.5), R.uniform(-1.5, 26.9)) for _ in range(11)]
        ball = pos[10]
        t0 = time.perf_counter()
        n = 0
        for i, (x, y) in enumerate(pos):
            other = pos[(i + 5) % 10]
            ctx = dict(bx=ball[0], by=ball[1], hx=pos[0][0], hy=pos[0][1], ax_=other[0], ay_=other[1], mx=other[0], my=other[1],
                       px=x - 0.05, py=y - 0.05, sx=pos[4][0], sy=pos[4][1], dribbling=1, lowest_defender_y=0.5,
                       lowest_attacker_y=0.5, n_off_in_paint=1, team_centroid_x=0.0, team_centroid_y=6.0, t_since_catch_s=1.0,
                       game_clock_s=600.0, shot_clock_s=20.0, table_side_x_sign=1)
            z = 2.0 if i == 10 else 0.0
            right = env(x, y, z, **ctx)
            left = env(-x, y, z, **{k: (-v if k in MIRROR_X else v) for k, v in ctx.items()})
            for c in plain:
                eval(c, G, right)
            for c in mirrored:
                eval(c, G, right)
                eval(c, G, left)
            n += len(plain) + 2 * len(mirrored)
        times.append((time.perf_counter() - t0) * 1000.0)
        evals = n
    times.sort()
    out = {"version": str(doc["version"]), "date": datetime.date.today().isoformat(), "frames": a.frames, "objects": 11,
           "exprs": len(coded), "evaluations_per_frame": evals,
           "ms_per_frame_median": round(statistics.median(times), 2), "ms_per_frame_p95": round(times[int(0.95 * len(times))], 2),
           "budget_ms": round(1001 / 30, 2), "note": "pure Python, one process; other jobs were running on the machine"}
    print(json.dumps(out, indent=1))
    if a.write_summary:
        SUMMARY.write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()
