"""Validate config/named_spots.yaml: whitelist, anchors, probes, mirrors and partitions.

Usage: python tools/specgen/named_spots/check.py [--step 0.05]
"""
import argparse, collections, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spotlib import load  # noqa: E402

CTX = re.compile(r"\b(bx|by|hx|hy|ax_|ay_|ball_side|dribbling|lowest_defender_y|px|py|sx|sy|n_off_in_paint|team_centroid_x|team_centroid_y|t_since_catch_s|lowest_attacker_y|game_clock_s|shot_clock_s)\b")


def entry_checks(doc, spots):
    bad = collections.defaultdict(list)
    for e in doc["entries"]:
        s = spots.get(e["id"])
        if s is None or s.code is None:
            continue
        for pr in e.get("probes_ctx") or []:
            p = pr["p"]
            got = s.inside(p[0], p[1], p[2] if len(p) > 2 else None, side="right" if (s.side != "mirrored" or p[0] >= 0) else "left", **pr.get("ctx", {}))
            if got != pr.get("want"):
                bad["probe_ctx"].append((e["id"], pr))
        if e["layer"] == "relative" or CTX.search(e["expr"]):
            continue

        def chk(p, want, kind):
            x, y = p[0], p[1]
            z = p[2] if len(p) > 2 else (0.0 if "z" in s.names else None)
            side = "right" if (s.side != "mirrored" or x >= 0) else "left"
            if s.inside(x, y, z, side=side, **({"table_side_x_sign": 1} if s.side == "table_side" else {})) != want:
                bad[kind].append((e["id"], p))

        a = e.get("anchor") or {}
        if a.get("x") is not None and a.get("y") is not None:
            chk([a["x"], a["y"], a.get("z")] if a.get("z") is not None else [a["x"], a["y"]], True, "anchor")
            if s.side == "mirrored" and a["x"] > 0 and not s.inside(-a["x"], a["y"], a.get("z") if a.get("z") is not None else (0.0 if "z" in s.names else None), side="left"):
                bad["mirror"].append(e["id"])
        for p in e.get("probes_inside") or []:
            chk(p, True, "probe_in")
        for p in e.get("probes_outside") or []:
            if s.side == "mirrored" and p[0] < 0:
                continue
            chk(p, False, "probe_out")
    return bad


def partition_checks(doc, spots, step):
    schemes = collections.defaultdict(list)
    for e in doc["entries"]:
        if e.get("partition") and e.get("expr") and not CTX.search(e["expr"]):
            schemes[e["layer"]].append(spots[e["id"]])
    nx, ny = int(18 / step) + 1, int(32 / step) + 1
    out = {}
    for name, sp in schemes.items():
        cover = over = 0
        for i in range(nx):
            x = round(-9 + i * step, 4)
            for j in range(ny):
                y = round(-3 + j * step, 4)
                n = sum(len(s.labels(x, y)) for s in sp)
                cover += n > 0
                over += n > 1
        out[name] = {"points": nx * ny, "covered": cover, "overlaps": over}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=float, default=0.05)
    a = ap.parse_args()
    doc, spots = load()
    bad = entry_checks(doc, spots)
    part = partition_checks(doc, spots, a.step)
    print(json.dumps({"entries": len(doc["entries"]), "with_expr": sum(1 for s in spots.values() if s.code),
                      "entry_failures": {k: v for k, v in bad.items()}, "partitions": part}, indent=1, default=str))
    full = part.get("zone_scheme:court_region", {})
    ok = not bad and full.get("covered") == full.get("points") and full.get("overlaps") == 0
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
