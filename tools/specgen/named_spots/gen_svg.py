"""Draw docs/data/named_spots_court.svg from config/named_spots.yaml.

The half court is drawn in metres in the attacked-rim frame (rim centre at (0, 0), x to the
attacker's right, y toward half court). Every line comes from the YAML constants. The 12
court_region cells are shaded on both sides; region names are written on the left half and the
main coaching-spot anchors are drawn as labelled dots on the right half (the left half is the
mirror image). Before writing, random points inside every shaded cell are checked against the
reference evaluator (spotlib), so the picture cannot drift from the rules.

Usage: python tools/specgen/named_spots/gen_svg.py [--out docs/data/named_spots_court.svg]
"""
import argparse
import math
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spotlib import load  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "docs" / "data" / "named_spots_court.svg"
FT = 0.3048
R14 = 14 * FT  # short/long mid-range split, 4.2672 m
R27 = 27 * FT  # three_depth standard/deep split
R30 = 30 * FT  # three_depth deep/logo split
TOP_Y = 13.6   # how much of the backcourt the picture shows

# Main coaching spots: (label, entry id, label dx, label dy, text-anchor), offsets in metres.
SPOTS = [
    ("corner", "corner_three", 0.0, 0.32, "middle"),
    ("short corner", "short_corner", 0.0, -0.42, "middle"),
    ("dunker", "dunker_spot", 0.0, -0.42, "middle"),
    ("block", "lane_block", 0.22, -0.12, "start"),
    ("low post", "low_post", 0.22, 0.14, "start"),
    ("mid post", "mid_post", 0.22, -0.08, "start"),
    ("elbow", "elbow", 0.0, -0.40, "middle"),
    ("nail", "nail", 0.0, -0.40, "middle"),
    ("high post", "high_post_strip", 0.0, 0.24, "middle"),
    ("pinch post", "pinch_post", 0.08, 0.26, "middle"),
    ("FT line extended", "ft_line_extended", 0.0, 0.26, "middle"),
    ("wing (45)", "wing_mid", 0.22, -0.08, "start"),
    ("slot", "slot_three", 0.22, -0.08, "start"),
    ("top", "top_three", 0.0, 0.26, "middle"),
]

# Region name positions (written on the left half; centre cells straddle x = 0).
REGION_LABELS = [
    ("restricted area", "restricted_area", 0.0, 0.62, 0),
    ("paint (non-RA)", "paint_non_ra", 0.0, 2.55, 0),
    ("short mid", "short_mid", -2.95, 1.15, 0),
    ("long mid baseline", "long_mid_baseline", -5.25, 0.15, 0),
    ("long mid wing", "long_mid_wing", -4.35, 4.25, 0),
    ("long mid top", "long_mid_top", -1.55, 5.75, 0),
    ("corner three", "corner_three", -7.11, -0.1, -90),
    ("wing three", "wing_three", -6.1, 7.7, 0),
    ("slot three", "slot_three", -3.55, 9.3, 0),
    ("top three", "top_three", 0.0, 10.3, 0),
    ("backcourt", "backcourt", 0.0, 13.15, 0),
]

STYLE = """
.bg{fill:#f7f5f0}.oob{fill:#e2ded6}
.c-ra{fill:#e57373}.c-paint{fill:#f4b0a8}.c-smid{fill:#f7cc8f}.c-lmb{fill:#c9df94}.c-lmw{fill:#a3d6b3}
.c-lmt{fill:#acd2d8}.c-c3{fill:#7099dc}.c-w3{fill:#92b2e8}.c-s3{fill:#acc4f0}.c-t3{fill:#c6d6f5}.c-bc{fill:#d3cfc7}
.ln{fill:none;stroke:#2f2f2f;stroke-width:0.0508}.ln-d{fill:none;stroke:#2f2f2f;stroke-width:0.0508;stroke-dasharray:0.18 0.12}
.gd{fill:none;stroke:#555;stroke-width:0.025;stroke-dasharray:0.14 0.1}
.tx{fill:#1c1c1c;font-family:Helvetica,Arial,sans-serif;paint-order:stroke;stroke:#f7f5f0;stroke-width:0.06;stroke-linejoin:round}
.rg{font-size:0.27px;font-style:italic}.sp{font-size:0.27px;font-weight:bold}.ax{font-size:0.24px}.sm{font-size:0.22px}
.ti{font-size:0.38px;font-weight:bold}.dot{fill:#111;stroke:#fff;stroke-width:0.04}.dotm{fill:none;stroke:#111;stroke-width:0.035}
.tk{stroke:#2f2f2f;stroke-width:0.025}.blk{fill:#2f2f2f}
@media (prefers-color-scheme: dark){
.bg{fill:#1c1c1e}.oob{fill:#2a2a2d}
.c-ra{fill:#9a3b3b}.c-paint{fill:#8d5a54}.c-smid{fill:#8f6a36}.c-lmb{fill:#5f7a39}.c-lmw{fill:#3f7758}
.c-lmt{fill:#3f6f79}.c-c3{fill:#2f4f92}.c-w3{fill:#3c5e9d}.c-s3{fill:#4a6aa6}.c-t3{fill:#5a77ad}.c-bc{fill:#47443f}
.ln,.ln-d{stroke:#f2f2f2}.gd{stroke:#cfcfcf}
.tx{fill:#f0f0f0;stroke:#1c1c1e}.dot{fill:#fff;stroke:#111}.dotm{stroke:#eee}.tk{stroke:#e0e0e0}.blk{fill:#f2f2f2}
}
"""

CLASS = {"restricted_area": "c-ra", "paint_non_ra": "c-paint", "short_mid": "c-smid",
         "long_mid_baseline": "c-lmb", "long_mid_wing": "c-lmw", "long_mid_top": "c-lmt",
         "corner_three": "c-c3", "wing_three": "c-w3", "slot_three": "c-s3", "top_three": "c-t3",
         "backcourt": "c-bc", "out_of_bounds": "oob"}


def pol(r, a):
    return (r * math.cos(math.radians(a)), r * math.sin(math.radians(a)))


def arc(r, a0, a1, step=0.5, c=(0.0, 0.0)):
    n = max(2, int(abs(a1 - a0) / step) + 1)
    return [(c[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             c[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def deg(x, y):
    return math.degrees(math.atan2(y, x))


def region_polygons(C):
    """Right-side (and centre) court_region cells as point lists in court metres."""
    END_Y, LANE_X, FT_Y, ARC_R = C["END_Y"], C["LANE_X"], C["FT_Y"], C["ARC_R"]
    CORNER_X, BREAK_Y, BREAK_T, RA_R = C["CORNER_X"], C["BREAK_Y"], C["BREAK_T"], C["RA_R"]
    HALF_Y, SIDE_X, BOARD_Y = C["HALF_Y"], C["SIDE_X"], C["BOARD_Y"]
    xe = math.sqrt(R14 ** 2 - END_Y ** 2)    # 14-ft circle meets the end line
    yl = math.sqrt(R14 ** 2 - LANE_X ** 2)   # 14-ft circle meets the lane line
    xf = math.sqrt(R14 ** 2 - FT_Y ** 2)     # 14-ft circle meets the FT line
    aE, aL, aF = deg(xe, END_Y), deg(LANE_X, yl), deg(xf, FT_Y)
    x60, x80 = HALF_Y / math.tan(math.radians(60)), HALF_Y / math.tan(math.radians(80))
    P = {
        "restricted_area": [(RA_R, BOARD_Y)] + arc(RA_R, 0, 180) + [(-RA_R, BOARD_Y)],
        "paint_non_ra": [(LANE_X, END_Y), (LANE_X, FT_Y), (-LANE_X, FT_Y), (-LANE_X, END_Y)],
        "short_mid": [(LANE_X, END_Y), (xe, END_Y)] + arc(R14, aE, aL),
        "short_mid#cap": [(0.0, FT_Y), (xf, FT_Y)] + arc(R14, aF, 90),
        "long_mid_baseline": [(xe, END_Y), (CORNER_X, END_Y), (CORNER_X, BREAK_Y)]
        + arc(ARC_R, BREAK_T, 30) + arc(R14, 30, aE),
        "long_mid_wing": arc(ARC_R, 30, 60) + arc(R14, 60, 30),
        "long_mid_top": arc(ARC_R, 60, 120) + arc(R14, 120, 180 - aL) + [(-LANE_X, FT_Y)]
        + arc(R14, 180 - aF, aF) + [(LANE_X, FT_Y)] + arc(R14, aL, 60),
        "corner_three": [(CORNER_X, END_Y), (SIDE_X, END_Y), (SIDE_X, BREAK_Y), (CORNER_X, BREAK_Y)],
        "wing_three": [(CORNER_X, BREAK_Y), (SIDE_X, BREAK_Y), (SIDE_X, HALF_Y), (x60, HALF_Y)]
        + arc(ARC_R, 60, BREAK_T),
        "slot_three": [(x60, HALF_Y), (x80, HALF_Y)] + arc(ARC_R, 80, 60),
        "top_three": [(x80, HALF_Y), (-x80, HALF_Y)] + arc(ARC_R, 100, 80),
        "backcourt": [(-SIDE_X, HALF_Y), (SIDE_X, HALF_Y), (SIDE_X, TOP_Y), (-SIDE_X, TOP_Y)],
    }
    return P


def pip(p, poly):
    x, y = p
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[i - 1]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    return inside


def verify(P, spots, n=300, seed=1):
    """Sample points inside each drawn cell; spotlib must give that cell's label (2 cm tolerance)."""
    region = [s for s in spots.values() if s.d["layer"] == "zone_scheme:court_region"]
    sides = {s.id: s.side for s in region}

    def labels(x, y):
        return [lab for s in region for lab in s.labels(x, y)]

    rng = random.Random(seed)
    bad = []
    for key, poly in P.items():
        rid = key.split("#")[0]
        for flip in ((1,) if sides[rid] == "centre" else (1, -1)):
            want = rid if sides[rid] == "centre" else f"{rid}_{'right' if flip == 1 else 'left'}"
            xs = [q[0] for q in poly]
            ys = [q[1] for q in poly]
            k = 0
            while k < n:
                p = (rng.uniform(min(xs), max(xs)), rng.uniform(min(ys), max(ys)))
                if not pip(p, poly) or (rid == "paint_non_ra" and pip(p, P["restricted_area"])):
                    continue
                if rid == "backcourt" and p[1] <= 12.71:
                    continue
                k += 1
                q = (p[0] * flip, p[1])
                if labels(*q) == [want]:
                    continue
                near = any(labels(q[0] + dx, q[1] + dy) == [want]
                           for dx in (-0.02, 0, 0.02) for dy in (-0.02, 0, 0.02))
                if not near:
                    bad.append((want, q, labels(*q)))
    return bad


def sx(x):
    return f"{x:.4f}"


def sy(y):
    return f"{-y:.4f}"


def poly_path(poly):
    return "M" + " L".join(f"{sx(x)} {sy(y)}" for x, y in poly) + " Z"


def line_path(pts):
    return "M" + " L".join(f"{sx(x)} {sy(y)}" for x, y in pts)


def text(x, y, s, cls, anchor="middle", rot=0):
    tr = f' transform="rotate({rot} {sx(x)} {sy(y)})"' if rot else ""
    return (f'<text class="tx {cls}" x="{sx(x)}" y="{sy(y)}" text-anchor="{anchor}" '
            f'dominant-baseline="middle"{tr}>{s}</text>')


def build(doc, spots):
    C = {k: v for k, v in doc["constants"].items() if isinstance(v, (int, float))}
    E = {e["id"]: e for e in doc["entries"]}
    P = region_polygons(C)
    bad = verify(P, spots)
    if bad:
        raise SystemExit(f"court_region drawing disagrees with spotlib at {len(bad)} points, e.g. {bad[:3]}")
    SIDE_X, END_Y, HALF_Y, LANE_X, FT_Y = C["SIDE_X"], C["END_Y"], C["HALF_Y"], C["LANE_X"], C["FT_Y"]
    ARC_R, CORNER_X, BREAK_Y, BREAK_T, RA_R = C["ARC_R"], C["CORNER_X"], C["BREAK_Y"], C["BREAK_T"], C["RA_R"]
    BOARD_Y, LINE_W = C["BOARD_Y"], C["LINE_W"]
    div_c = HALF_Y + LINE_W / 2  # division line centre, 12.7254
    vb = (-8.8, -15.0, 17.6, 20.6)
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{" ".join(str(v) for v in vb)}" '
         f'width="880" height="1030" role="img" aria-labelledby="t d">',
         '<title id="t">MSU Alpha named spots: court regions and coaching spots</title>',
         '<desc id="d">Half court in metres, rim centre at (0, 0). Shaded: the 12 court_region cells '
         '(region names on the left half). Dots: coaching-spot anchors (named on the right half). '
         f'Generated from config/named_spots.yaml version {doc["version"]} by '
         'tools/specgen/named_spots/gen_svg.py.</desc>',
         f"<style>{STYLE}</style>",
         f'<rect class="bg" x="{vb[0]}" y="{vb[1]}" width="{vb[2]}" height="{vb[3]}"/>',
         # out of bounds band around the court (court cells are painted over it)
         f'<rect class="oob" x="-8.4" y="{sy(TOP_Y)}" width="16.8" height="{TOP_Y + 2.4:.4f}"/>',
         '<g id="court_region">']
    mirrored = []
    for key, poly in P.items():
        rid = key.split("#")[0]
        if rid == "paint_non_ra":
            continue
        cls = CLASS[rid]
        o.append(f'<path class="{cls}" d="{poly_path(poly)}"><title>{rid}</title></path>')
        if E[rid]["side"] == "mirrored":
            mirrored.append(f'<path class="{cls}" d="{poly_path(poly)}"><title>{rid}</title></path>')
    o.append('<g transform="scale(-1,1)">' + "".join(mirrored) + "</g>")
    o.append(f'<path class="c-paint" d="{poly_path(P["paint_non_ra"])}"><title>paint_non_ra</title></path>')
    o.append(f'<path class="c-ra" d="{poly_path(P["restricted_area"])}"><title>restricted_area</title></path>')
    o.append("</g>")

    # guides: 14 ft circle, 27 ft and 30 ft arcs, angle-m rays at 30, 60, 80 deg
    g = ['<g id="guides">']
    xe = math.sqrt(R14 ** 2 - END_Y ** 2)
    g.append(f'<path class="gd" d="{line_path(arc(R14, deg(xe, END_Y), 180 - deg(xe, END_Y)))}"/>')
    for rr in (R27, R30):
        a0 = math.degrees(math.acos(SIDE_X / rr))
        g.append(f'<path class="gd" d="{line_path(arc(rr, a0, 180 - a0))}"/>')
    for a in (30, 60, 80):
        x1, y1 = pol(R14, a)
        t = math.tan(math.radians(a))
        x2, y2 = (SIDE_X, SIDE_X * t) if SIDE_X * t <= HALF_Y else (HALF_Y / t, HALF_Y)
        for f in (1, -1):
            g.append(f'<path class="gd" d="{line_path([(f * x1, y1), (f * x2, y2)])}"/>')
    g.append(f'<path class="gd" d="{line_path([(CORNER_X, BREAK_Y), (SIDE_X, BREAK_Y)])}"/>')
    g.append(f'<path class="gd" d="{line_path([(-CORNER_X, BREAK_Y), (-SIDE_X, BREAK_Y)])}"/>')
    g.append("</g>")
    o += g

    # painted lines, drawn at their real 2-in width, positions from the constants
    h = LINE_W / 2  # lines are drawn along the middle of their painted width
    L = ['<g id="lines">',
         f'<path class="ln" d="{line_path([(-SIDE_X - h, TOP_Y), (-SIDE_X - h, END_Y - h), (SIDE_X + h, END_Y - h), (SIDE_X + h, TOP_Y)])}"/>',
         f'<path class="ln" d="{line_path([(-LANE_X + h, END_Y), (-LANE_X + h, FT_Y - h), (LANE_X - h, FT_Y - h), (LANE_X - h, END_Y)])}"/>',
         f'<path class="ln" d="{line_path([(CORNER_X - h, END_Y), (CORNER_X - h, BREAK_Y)])}"/>',
         f'<path class="ln" d="{line_path([(-CORNER_X + h, END_Y), (-CORNER_X + h, BREAK_Y)])}"/>',
         f'<path class="ln" d="{line_path(arc(ARC_R - h, BREAK_T, 180 - BREAK_T))}"/>',
         f'<path class="ln" d="{line_path(arc(1.8288 - h, 0, 180, c=(0.0, FT_Y)))}"/>',
         f'<path class="ln-d" d="{line_path(arc(1.8288 - h, 180, 360, c=(0.0, FT_Y)))}"/>',
         f'<path class="ln" d="{line_path([(RA_R - h, BOARD_Y), (RA_R - h, 0.0)] + arc(RA_R - h, 0, 180) + [(-RA_R + h, 0.0), (-RA_R + h, BOARD_Y)])}"/>',
         f'<path class="ln" d="{line_path([(-0.9144, BOARD_Y), (0.9144, BOARD_Y)])}" style="stroke-width:0.08"/>',
         '<circle class="ln" cx="0" cy="0" r="0.2286"/>',
         f'<path class="ln" d="{line_path([(-SIDE_X, div_c), (SIDE_X, div_c)])}"/>',
         f'<path class="ln" d="{line_path(arc(1.8288 - h, 180, 360, c=(0.0, div_c)))}"/>']
    for f in (1, -1):  # block and the three lane-space marks, outside each lane line
        x0 = LANE_X if f == 1 else -LANE_X - 0.2032
        L.append(f'<rect class="blk" x="{x0:.4f}" y="{sy(0.8382)}" width="0.2032" height="0.3048"/>')
        for ym in (1.7526, 2.7178, 3.683):
            L.append(f'<rect class="blk" x="{x0:.4f}" y="{sy(ym + LINE_W)}" width="0.2032" height="{LINE_W}"/>')
    L.append("</g>")
    o += L

    # metre ticks and labels
    t = ['<g id="axes">']
    for i in range(-7, 8):
        t.append(f'<path class="tk" d="{line_path([(i, END_Y - 0.05), (i, END_Y - 0.25)])}"/>')
        t.append(text(i, END_Y - 0.45, str(i), "ax"))
    for j in range(-1, 14):
        t.append(f'<path class="tk" d="{line_path([(-8.4, j), (-8.25, j)])}"/>')
        t.append(text(-8.43, j, str(j), "ax", "end"))
    t.append(text(7.7, END_Y - 0.45, "x (m)", "ax", "start"))
    t.append(text(-8.4, 13.95, "y (m)", "ax", "start"))
    t.append(text(0.0, -0.95, "rim at (0, 0)", "sm"))
    t.append(text(7.72, 3.35, "27 ft", "sm", "start"))
    t.append(text(7.72, 5.3, "30 ft", "sm", "start"))
    t.append(text(4.15, -1.3, "14 ft", "sm", "middle"))
    for a, (x, y) in ((30, (7.72, 4.4)), (60, (7.33, 12.45)), (80, (2.24, 12.45))):
        t.append(text(x, y, f"{a}°", "sm", "start" if a == 30 else "middle"))
    t.append(text(-8.8 + 0.3, 14.55, "Named spots: court regions (shaded) and coaching spots (dots), metres", "ti", "start"))
    t.append("</g>")
    o += t

    # region names on the left half
    o.append('<g id="region_labels">')
    for lab, rid, x, y, rot in REGION_LABELS:
        o.append(text(x, y, lab, "rg", rot=rot))
    o.append(text(-8.03, 7.0, "out of bounds", "rg", rot=-90))
    o.append(text(8.03, 9.5, "out of bounds", "rg", rot=90))
    o.append("</g>")

    # coaching spots: labelled dots on the right, unlabelled rings at the mirror on the left
    o.append('<g id="spots">')
    for lab, sid, dx, dy, anc in SPOTS:
        a = E[sid]["anchor"]
        x, y = float(a["x"]), float(a["y"])
        o.append(f'<circle class="dot" cx="{sx(x)}" cy="{sy(y)}" r="0.11"><title>{sid} ({x:.2f}, {y:.2f})</title></circle>')
        if E[sid]["side"] == "mirrored" or x != 0:
            o.append(f'<circle class="dotm" cx="{sx(-x)}" cy="{sy(y)}" r="0.09"/>')
        o.append(text(x + dx, y + dy, lab, "sp", anc))
    o.append("</g>")

    # legend below the court
    lg = ['<g id="legend">']
    y0 = END_Y - 1.25
    order = ["restricted_area", "paint_non_ra", "short_mid", "long_mid_baseline", "long_mid_wing",
             "long_mid_top", "corner_three", "wing_three", "slot_three", "top_three", "backcourt", "out_of_bounds"]
    for i, rid in enumerate(order):
        col, row = i // 4, i % 4
        x, y = -8.4 + col * 4.3, y0 - row * 0.5
        lg.append(f'<rect class="{CLASS[rid]}" x="{sx(x)}" y="{sy(y + 0.17)}" width="0.34" height="0.34" '
                  f'style="stroke:#888;stroke-width:0.02"/>')
        lg.append(text(x + 0.48, y, rid, "ax", "start"))
    x = 4.5
    lg.append(f'<circle class="dot" cx="{sx(x + 0.17)}" cy="{sy(y0)}" r="0.11"/>')
    lg.append(text(x + 0.48, y0, "spot anchor (named)", "ax", "start"))
    lg.append(f'<circle class="dotm" cx="{sx(x + 0.17)}" cy="{sy(y0 - 0.5)}" r="0.09"/>')
    lg.append(text(x + 0.48, y0 - 0.5, "same spot, left side", "ax", "start"))
    lg.append(f'<path class="gd" d="{line_path([(x, y0 - 1.0), (x + 0.36, y0 - 1.0)])}"/>')
    lg.append(text(x + 0.48, y0 - 1.0, "guide: 14/27/30 ft, angle m", "ax", "start"))
    lg.append(f'<path class="ln" d="{line_path([(x, y0 - 1.5), (x + 0.36, y0 - 1.5)])}"/>')
    lg.append(text(x + 0.48, y0 - 1.5, "painted line", "ax", "start"))
    lg.append(text(-8.4, y0 - 2.15, "1 m = 3.28 ft. Left/right as the attacker faces the basket. "
                   "Mirrored regions are named once (left half); spots are named once (right half).", "sm", "start"))
    lg.append("</g>")
    o += lg
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    doc, spots = load()
    svg = build(doc, spots)
    ET.fromstring(svg)  # must parse
    Path(args.out).write_text(svg)
    print(f"wrote {args.out} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
