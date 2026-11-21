"""Seeded property tests for config/named_spots.yaml. Exits non-zero when any property fails.

Usage: python tools/specgen/named_spots/proptest.py [--scale 1.0] [--write-summary]

--scale 1.0 is the full run (about 4 minutes); tests/test_named_spots.py runs a reduced copy.
--write-summary stores the counts in results/named_spots_test/proptest_summary.json (full run only).

Properties (random points from fixed seeds):
 1 mirror        a side label gives the same answer for (x, y) and (-x, y); a centre label is symmetric
 2 partitions    no partition scheme gives two labels; court_region gives exactly one
 3 rays          along rays from the rim, three-point status never turns back to two, and court_region
                 agrees with is_three
 4 lines         no entry without oob_ok is true on a boundary line
 5 gating        an entry that needs context returns None without it, and None when any one of the
                 names it uses is NaN, infinite or None; an entry that needs height returns None without it
 6 corner/above  corner and above-the-break labels of every scheme split the threes at the break
                 (pbpstats at its own literal 8.7 ft cut, y <= 2.65176)
 7 values        value expressions are null without their context, never 0; bearings stay in (-180, 180]
"""
import argparse, collections, json, math, random, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spotlib import C, Values, court_region, is_three, load, rules_sha  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SUMMARY = ROOT / "results" / "named_spots_test" / "proptest_summary.json"
SEED = 20261020
FULL = {"mirror_points": 30000, "partition_points": 40000, "rays": 4000, "line_points": 3000, "corner_points": 60000,
        "value_points": 5000}
# a complete, finite context: every context name an expr may use
CTX_OK = dict(bx=1.0, by=5.0, hx=1.0, hy=5.0, ax_=1.0, ay_=4.0, mx=1.0, my=4.0, px=1.0, py=4.9, sx=2.0, sy=5.0,
              dribbling=1, lowest_defender_y=1.0, lowest_attacker_y=1.0, n_off_in_paint=1, team_centroid_x=0.5,
              team_centroid_y=5.0, t_since_catch_s=1.0, game_clock_s=100.0, shot_clock_s=10.0, table_side_x_sign=1)
PBP_CUT = 2.65176  # pbpstats corner three: locY <= 87 tenths of a foot (the literal NBA cut), by design


def run(scale=1.0, log=print, loaded=None):
    """Returns (bad, counts, seconds): failures by kind, and how many cases each property ran.

    loaded = (document, spots) tests another dictionary than the file on disk (the tests use it to show
    that a broken dictionary fails)."""
    doc, SP = loaded or load()
    R = random.Random(SEED)
    n = {k: max(1, int(round(v * scale))) for k, v in FULL.items()}
    bad = collections.defaultdict(list)
    counts = collections.OrderedDict()
    t0 = time.time()
    static = [s for s in SP.values() if s.code and not s.ctx and "z" not in s.names]

    def pt():
        return R.uniform(-8.5, 8.5), R.uniform(-2.5, 28.0)

    # 1 mirror symmetry
    for _ in range(n["mirror_points"]):
        x, y = pt()
        if x == 0:
            continue
        for s in static:
            if s.side == "mirrored":
                if s.inside(x, y, side="right" if x >= 0 else "left") != s.inside(-x, y, side="right" if -x >= 0 else "left"):
                    bad["mirror:" + s.id].append((x, y))
            elif s.side == "centre":
                if s.inside(x, y) != s.inside(-x, y):
                    bad["centre_sym:" + s.id].append((x, y))
    counts["mirror"] = {"points": n["mirror_points"], "entries": len(static)}
    log("mirror done", round(time.time() - t0, 1))

    # 2 partitions
    parts = collections.defaultdict(list)
    for e in doc["entries"]:
        s = SP[e["id"]]
        if e.get("partition") and s.code and not s.ctx and "z" not in s.names:
            parts[e["layer"]].append(s)
    for _ in range(n["partition_points"]):
        x, y = pt()
        for k, sp in parts.items():
            m = sum(len(s.labels(x, y)) for s in sp)
            if m > 1:
                bad["overlap:" + k].append((x, y))
            if k == "zone_scheme:court_region" and m != 1:
                bad["court_region_cover"].append((x, y))
    counts["partitions"] = {"points": n["partition_points"], "schemes": len(parts)}
    log("partitions done", round(time.time() - t0, 1))

    # 3 rays: three never turns back to two moving away from the rim (in bounds)
    steps = 0
    for _ in range(n["rays"]):
        a = math.radians(R.uniform(-15, 195))
        prev = None
        for k in range(1300):
            r = 5.5 + k * 0.002
            x, y = r * math.cos(a), r * math.sin(a)
            if abs(x) >= C["SIDE_X"] or y <= C["END_Y"]:
                break
            steps += 1
            th = is_three(x, y)
            cr = court_region(SP, x, y)[0]
            if th != cr.replace("_right", "").replace("_left", "").endswith("_three"):
                bad["court_region_vs_is_three"].append((x, y, cr))
            if prev and not th:
                bad["ray_back_to_two"].append((math.degrees(a), r))
            prev = th
    counts["rays"] = {"rays": n["rays"], "points": steps}
    log("rays done", round(time.time() - t0, 1))

    # 4 boundary lines belong to nobody without oob_ok
    gated = [s for s in static if not s.d.get("oob_ok")]
    for _ in range(n["line_points"]):
        for (x, y) in ((C["SIDE_X"] * R.choice([1, -1]), R.uniform(-1.6, 27.0)), (R.uniform(-7.6, 7.6), C["END_Y"]),
                       (R.uniform(-7.6, 7.6), C["FAR_END_Y"])):
            for s in gated:
                if s.labels(x, y):
                    bad["owns_line:" + s.id].append((x, y))
    counts["lines"] = {"points": 3 * n["line_points"], "entries": len(gated)}
    log("lines done", round(time.time() - t0, 1))

    # 5 context and height gating
    ctxents = [s for s in SP.values() if s.code and s.ctx]
    cases = 0
    for s in ctxents:
        z = 3.0 if "z" in s.names else None
        if s.inside(1.0, 5.0, z) is not None:
            bad["ctx_not_gated:" + s.id].append(1)
        if s.inside(1.0, 5.0, z, **CTX_OK) is None:
            bad["full_ctx_still_none:" + s.id].append(1)
        need = (s.ctx - {"ball_side", "table_side_x_sign"}) | ({"bx", "by"} if "ball_side" in s.ctx else set())
        for name in sorted(need):
            for v in (float("nan"), float("inf"), None):
                cases += 1
                if s.inside(1.0, 5.0, z, **dict(CTX_OK, **{name: v})) is not None:
                    bad["bad_ctx_not_none:" + s.id].append((name, str(v)))
    zents = [s for s in SP.values() if s.code and "z" in s.names]
    for s in zents:
        cases += 1
        if s.inside(0.1, 0.1, **CTX_OK) is not None:
            bad["z_not_gated:" + s.id].append(1)
    counts["gating"] = {"context_entries": len(ctxents), "height_entries": len(zents), "cases": cases}
    log("gating done", round(time.time() - t0, 1))

    # 6 corner vs above the break, every scheme at its own cut
    CORNER = ["corner_three", "nba_corner_3", "ctg_corner_3", "three_depth_corner"]
    ABOVE = ["above_the_break", "above_the_break_three", "nba_above_the_break_3", "ctg_non_corner_3"]
    for i in CORNER + ["pbpstats_corner3", "pbpstats_arc3"]:
        if i not in SP:
            bad["missing_entry:" + i].append(1)
    threes = 0
    for _ in range(n["corner_points"]):
        x, y = R.uniform(-7.61, 7.61), R.uniform(-1.6, 3.5)
        if not is_three(x, y):
            continue
        threes += 1
        corner = y <= C["BREAK_Y"]
        for e in CORNER:
            if e in SP and bool(SP[e].labels(x, y)) != corner:
                bad["corner:" + e].append((x, y))
        for e in ABOVE:
            if e in SP and bool(SP[e].labels(x, y)) != (not corner):
                bad["above:" + e].append((x, y))
        if bool(SP["pbpstats_corner3"].labels(x, y)) != (y <= PBP_CUT):
            bad["corner:pbpstats_corner3"].append((x, y))
        if bool(SP["pbpstats_arc3"].labels(x, y)) != (y > PBP_CUT):
            bad["above:pbpstats_arc3"].append((x, y))
    counts["corner_above"] = {"points": n["corner_points"], "threes": threes}
    log("corner done", round(time.time() - t0, 1))

    # 7 value expressions
    vals = 0
    for e in doc["entries"]:
        if not e.get("value_exprs"):
            continue
        V = Values(e["value_exprs"])
        ctx_names = {k: sorted(names & set(CTX_OK)) for k, (names, _) in V.items.items()}
        for _ in range(n["value_points"]):
            x, y = pt()
            c = dict(bx=R.uniform(-8, 8), by=R.uniform(-2, 28), mx=R.uniform(-8, 8), my=R.uniform(-2, 28))
            vals += 1
            full, none = V.at(x, y, **c), V.at(x, y)
            for k, need in ctx_names.items():
                if full[k] is None or not math.isfinite(full[k]):
                    bad["value_missing:" + k].append((x, y))
                if need and none[k] is not None:
                    bad["value_not_null:" + k].append((x, y))
                if k.endswith("_bearing") and not (-180.0 < full[k] <= 180.0):
                    bad["bearing_range:" + k].append((x, y, full[k]))
                if k.endswith("_dist") and full[k] < 0:
                    bad["negative_distance:" + k].append((x, y, full[k]))
            for name in ("bx", "by", "mx", "my"):
                broken = V.at(x, y, **dict(c, **{name: float("nan")}))
                for k, need in ctx_names.items():
                    if name in need and broken[k] is not None:
                        bad["value_nan_not_null:" + k].append((name, x, y))
    counts["values"] = {"points": vals}
    log("values done", round(time.time() - t0, 1))
    return bad, counts, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--write-summary", action="store_true")
    a = ap.parse_args()
    bad, counts, secs = run(a.scale)
    for k, v in sorted(bad.items()):
        print(k, len(v), v[:2])
    print("TOTAL failed properties", len(bad))
    if a.write_summary:
        if a.scale != 1.0:
            sys.exit("the summary is written from the full run only (--scale 1.0)")
        doc, _ = load()
        out = {"version": str(doc["version"]), "rules_sha256": rules_sha(doc), "seed": SEED,
               "scale": a.scale, "seconds": round(secs), "counts": counts,
               "failed_properties": {k: len(v) for k, v in sorted(bad.items())}}
        SUMMARY.write_text(json.dumps(out, indent=1) + "\n")
        print("wrote", SUMMARY)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
