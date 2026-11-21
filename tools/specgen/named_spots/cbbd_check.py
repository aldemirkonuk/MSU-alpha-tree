"""Label CBBD shot locations with the dictionary and compare with CBBD's own shot range.

Reads licensed CBBD play files from the private folder; writes aggregates only.
Usage: python tools/specgen/named_spots/cbbd_check.py <cbbd_plays_glob>... --out results/named_spots_test/cbbd_summary.json
CBBD location: x 0..940, y 0..500 (tenths of a foot); the rim is 52.5 (5.25 ft) from each end line;
the attacked basket is the nearer one (fit: 99.92% of shots agree on two vs three).
Lateral sign checked against video 2026-10-20 (UConn game, makes 3, 4, 9, 10 from
_audit/uconn/made_basket_lag.csv): CBBD y runs toward the attacker's LEFT, so x = -(y - 250) at
the low-x end and x = (y - 250) at the high-x end (attacker's right is +x in our frame).
"""
import argparse, collections, glob, json, math, statistics, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spotlib import C, is_three, load  # noqa: E402

FT = 0.03048  # one tenth of a foot in metres
NEAR_LINE_M = 0.05  # a two-vs-three disagreement this close to the line is a location rounding, not a wrong label


def to_rim_frame(X, Y):
    if X < 470:
        return (250 - Y) * FT, (X - 52.5) * FT
    return (Y - 250) * FT, (887.5 - X) * FT


def line_offset(x, y):
    """Three-point offset d3 of rule_continuous_coordinates: metres past the line (inside is negative)."""
    return abs(x) - C["CORNER_X"] if y <= C["BREAK_Y"] else math.hypot(x, y) - C["ARC_R"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("globs", nargs="+")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    doc, spots = load()
    schemes = collections.defaultdict(list)
    for e in doc["entries"]:
        if e.get("partition") and e["layer"] in ("zone_scheme:court_region", "zone_scheme:three_depth", "zone_scheme:nba_basic", "zone_scheme:ctg"):
            schemes[e["layer"].split(":")[1]].append(spots[e["id"]])
    per = {k: collections.Counter() for k in schemes}
    cross = collections.Counter()
    bad_count = collections.Counter()
    n = 0
    behind = []  # above-the-break threes: metres behind the arc's outside edge
    off_line = []  # shots where CBBD's range and our three-point line disagree: metres from the line
    files = [f for g in a.globs for f in glob.glob(g)]
    for f in files:
        for p in json.load(open(f)):
            s = p.get("shotInfo")
            if not s or not s.get("location") or s["location"]["x"] is None or s["range"] == "free_throw":
                continue
            n += 1
            x, y = to_rim_frame(s["location"]["x"], s["location"]["y"])
            if (s["range"] == "three_pointer") != is_three(x, y):
                off_line.append(abs(line_offset(x, y)))
            for k, sp in schemes.items():
                labs = [l for q in sp for l in q.labels(x, y)]
                if k != "three_depth" and len(labs) != 1:
                    bad_count[k] += 1
                lab = labs[0] if labs else "none"
                per[k][lab] += 1
                if k == "court_region":
                    base = lab.removesuffix("_right").removesuffix("_left")
                    cross[f"{s['range']} -> {base}"] += 1
                    if base in ("wing_three", "slot_three", "top_three"):
                        behind.append(math.hypot(x, y) - C["ARC_R"])
    three = {"three_pointer": 0, "agree": 0}
    for key, v in cross.items():
        rng, lab = key.split(" -> ")
        is3 = lab.endswith("_three")
        three["agree"] += v if (rng == "three_pointer") == is3 else 0
    if three["agree"] + len(off_line) != n:  # the court_region labels and is_three must tell the same story
        sys.exit(f"two-vs-three: {three['agree']} agree by court_region label, {len(off_line)} disagree by is_three, {n} shots")
    disagree = {"n": len(off_line), "max_from_line_m": round(max(off_line), 2) if off_line else None,
                "within_0p05_m": sum(d <= NEAR_LINE_M for d in off_line)}
    behind.sort()
    depth = per["three_depth"]
    above = {"n": len(behind), "median_behind_arc_m": round(statistics.median(behind), 2),
             "p90_behind_arc_m": round(behind[math.ceil(0.9 * len(behind)) - 1], 2),
             "deep_or_logo": depth.get("three_depth_deep", 0) + depth.get("three_depth_logo", 0)}
    out = {"version": str(doc["version"]), "files": len(files), "located_field_goal_attempts": n, "label_count_problems": dict(bad_count),
           "above_break_three": above,
           "two_vs_three_agreement": f"{three['agree']}/{n}", "two_vs_three_disagreements": disagree, "cbbd_range_x_court_region": dict(sorted(cross.items())),
           "labels": {k: dict(v.most_common()) for k, v in per.items()}}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
