"""Generate docs/data/named_spots.md from config/named_spots.yaml and doc_template.md.

Rules the page follows:
- Never shorten text. Each entry shows its `plain` field if it has one, else its full
  `bounds_text`, plus the exact rule (`expr`) in code font in its own column.
- Tables stay narrow (4 columns) and are split by layer and by side (centre, side, bench side,
  no side).
- Every anchor is shown as (x, y) in metres and as r (m, ft) and full angle theta (deg).

After writing, the script checks that every entry id appears, that every shown text appears in
full, that every table row has the same column count as its header, and that no {{PLACEHOLDER}}
is left. It exits non-zero if any check fails.

Usage: python tools/specgen/named_spots/gen_doc.py [--out docs/data/named_spots.md]
"""
import argparse
import json
import math
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spotlib import CTX_NAMES, load  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TEMPLATE = HERE / "doc_template.md"
OUT = ROOT / "docs" / "data" / "named_spots.md"
CBBD = ROOT / "results" / "named_spots_test" / "cbbd_summary.json"
FT = 0.3048

CONST_MEANING = OrderedDict([
    ("RIM_Y_FROM_END", "rim centre to the end line's inside edge"),
    ("END_Y", "end line (inside edge); y of the baseline"),
    ("BOARD_Y", "backboard face, 4 ft in front of the end line"),
    ("LANE_X", "half-width of the lane to the lane line's outside edge (lane is 12 ft wide)"),
    ("FT_Y", "FT line, far edge (15 ft from the backboard face)"),
    ("ARC_R", "three-point arc radius to its outside edge"),
    ("CORNER_X", "corner three-point line, outside edge"),
    ("BREAK_Y", "the break: where the corner straight meets the arc"),
    ("BREAK_T", "full angle of the break, in degrees (not a distance)"),
    ("RA_R", "restricted-area arc, outside edge (4-ft inner radius plus the 2-in line)"),
    ("HALF_Y", "division line, near edge; frontcourt is y <= this"),
    ("SIDE_X", "sideline, inside edge"),
    ("FAR_END_Y", "far end line, inside edge"),
    ("LINE_W", "width of every painted line (2 in)"),
])

LAYER_MEANING = OrderedDict([
    ("zone_scheme:court_region", "the main label: exactly one region per point (section 3)"),
    ("zone_scheme:three_depth", "how deep a three is: corner, standard, deep, logo, heave (section 3)"),
    ("spot", "coaching spots; one winner per player (section 4)"),
    ("landmark", "painted marks, rule areas, coaching tags, named points; many at once (section 5)"),
    ("relative", "positions measured from the ball, the handler or the assigned attacker (section 6)"),
    ("restart", "dead-ball and throw-in positions (section 8.1)"),
    ("restart_alignment", "a throw-in alignment spot (section 8.1)"),
    ("fullcourt", "transition, press and backcourt positions (section 8.2)"),
    ("shot_zone_alt", "shot-zone labels kept as alternatives (section 8.3)"),
    ("rule", "labelling rules and other providers' encodings (section 8.4)"),
    ("zone_scheme:*", "the other schemes: crosswalks, zone defences, presses, coaching bands (section 7)"),
])

COURT_ORDER = ["restricted_area", "paint_non_ra", "short_mid", "long_mid_baseline", "long_mid_wing",
               "long_mid_top", "corner_three", "wing_three", "slot_three", "top_three", "backcourt",
               "out_of_bounds"]
DEPTH_ORDER = ["three_depth_corner", "three_depth_standard", "three_depth_deep", "three_depth_logo",
               "three_depth_heave"]
SPOT_ORDER = ["under_basket", "dunker_spot", "low_post", "lane_middle", "mid_post", "short_corner",
              "high_short_corner", "elbow", "nail_area", "pinch_post", "high_post_strip", "mr_baseline", "mr_wing",
              "mr_elbow", "mr_top", "corner_deep", "corner_high", "wing_low", "wing_mid", "wing_high",
              "slot_lane_line", "centre_circle_logo"]

LANDMARK_GROUPS = OrderedDict([
    ("5.1 Painted lines and marks", (
        "Things painted on the floor or fixed to the basket. Most are thinner than tracking error, so they "
        "are stored as a probability, not a yes/no.",
        {"backboard", "backcourt_28ft_mark", "division_line", "end_line", "free_throw_line", "lane_block",
         "lane_line_landmark", "lane_mark_1", "lane_mark_2", "lane_mark_3", "mark_28ft", "restraining_line",
         "restricted_area_arc_line", "restricted_area_straight_leg", "ring", "sideline", "three_point_arc",
         "three_point_corner_straight", "backboard_target_rectangle", "endline_throw_in_mark",
         "out_of_bounds_colour_belt", "free_throw_semicircle", "legacy_restricted_area_arc_3ft",
         "second_three_point_line", "charge_circle", "coaching_box_38ft_line_landmark", "coaching_box_38ft_line",
         "division_line_extended", "scorers_x_mark", "commercial_logo_box", "painted_block"})),
    ("5.2 Rule areas", (
        "Areas the rules book defines (lane, three-point area, bench and table areas, neutral zones).",
        {"three_point_area", "post_area_rule", "paint", "rim", "block_zone", "lane_mark_1_zone", "lane_mark_2_zone",
         "lane_mark_3_zone", "oob_endline_to_restraining_line", "oob_far_endline_to_restraining_line",
         "sideline_clear_space", "coaching_box", "team_bench_area", "scorers_table_area",
         "timeout_huddle_rectangle", "second_half_throw_in_division_line"})),
    ("5.3 Named points with a capture disk", (
        "A single named point; a player within the capture radius carries the tag.",
        {"court_corner", "elbow_landmark", "ft_circle_top", "nail", "half_court_centre", "block_outside_lane",
         "mid_post_lane_line", "wide_pin_spot", "break_point"})),
    ("5.4 Coaching tags (non-exclusive)", (
        "Coaching words for areas that overlap the spots of section 4. A player can carry several.", None)),
])

RELATIVE_GROUPS = OrderedDict([
    ("Ball side and weak side", "which side of the floor the player is on, seen from the ball"),
    ("On-ball defence", "the defender guarding the ball and how close he is"),
    ("Deny and passing lanes", "defenders one or two passes away from the ball"),
    ("Help defence", "help positions: low man, nail, gaps, split line, block and elbow help"),
    ("Post defence and rebounding", "fronting, playing behind, doubling the post, boxing out"),
    ("Ball screens, hand-offs and drives", "pick-and-roll coverages, screen direction, drive direction"),
    ("Off-ball movement", "lift, drift, shake, fill, seams and stacks"),
    ("Transition", "getting back, stopping the ball, trailing"),
    ("Restarts, presses and press breaks", "throw-in alignments, press roles, leak-outs"),
    ("Rule geometry and officials", "rules-book distances around players, and the referees' positions"),
])


def relative_group(i):
    if i.startswith("official_") or i in ("rule_closely_guarded_distance", "rule_verticality_cylinder"):
        return "Rule geometry and officials"
    if i in ("ball_side_interior", "weak_side_interior", "strong_side", "weak_side", "ball_in_middle"):
        return "Ball side and weak side"
    if i.startswith(("blob_", "inbound_", "pb_", "press_", "slob_")) or i in ("leak_out_runner", "rim_run_lane"):
        return "Restarts, presses and press breaks"
    if i.startswith(("transition_",)) or i == "trail_spot":
        return "Transition"
    if i.startswith(("pnr_", "ball_screen_", "drive_")) or i in (
            "handoff_exchange_spot", "short_roll_pocket", "screener_pop", "spain_pop_spot"):
        return "Ball screens, hand-offs and drives"
    if i.startswith("post_") or i in ("box_out_position", "weak_side_rebound_area"):
        return "Post defence and rebounding"
    if i in ("shake", "drift", "lift", "fill_slide", "seam", "i_stack"):
        return "Off-ball movement"
    if i.startswith("on_ball") or i in ("face_guard", "closeout_landing", "canonical_defender_point", "sink_sag",
                                        "charge_position"):
        return "On-ball defence"
    if i in ("deny_on_the_line", "one_pass_away", "two_passes_away", "gap_one_pass", "up_the_line",
             "ball_you_man_pistols") or i.startswith("offball_"):
        return "Deny and passing lanes"
    return "Help defence"


SCHEME_GROUPS = OrderedDict([
    ("7.1 Crosswalks to other companies' shot maps", [
        ("nba_basic", "NBA.com's basic shot zones (restricted area, paint, mid-range, corner 3, above the break 3)."),
        ("nba_basic_literal_break", "NBA corner 3 using the NBA's own break height, for comparing with NBA numbers."),
        ("nba_range", "NBA.com distance bands: under 8 ft, 8-16 ft, 16-24 ft, 24+ ft, backcourt."),
        ("nba_area", "NBA.com floor areas: left side, left-centre, centre, right-centre, right side, backcourt."),
        ("ctg", "Cleaning the Glass zones: rim, short mid, long mid, corner three, non-corner three."),
        ("ctg_shot", "Cleaning the Glass extras: heave zone and rim zone."),
        ("pbpstats", "pbpstats.com zones: at rim, short mid, long mid, corner three, arc three."),
        ("br_distance", "Basketball-Reference distance bands: 0-3 ft, 3-10 ft, 10-16 ft, 16 ft to the arc, three."),
        ("rebound_distance", "Opta rebound distance: at the rim (under 5 ft), short (5-10 ft), long (10 ft and more)."),
    ]),
    ("7.2 Shot and distance bands", [
        ("three_offset", "How far a player is inside or behind the three-point line, in six bands (uses d3)."),
        ("arc_offset", "Distance to the three-point line at the catch or shot, in 2-ft and 5-ft bands."),
        ("rim_radius", "Plain distance rings from the rim centre used by individual metrics (5 ft, 6 ft, 15 ft, ...)."),
        ("shot_entry_angle", "How steeply the ball comes down into the rim: flat, optimal, steep."),
        ("shot_entry_depth", "How deep the ball enters the ring along the shot line: front of rim, swish band (7-11 in), back of rim, long."),
        ("transition_band", "Where the team's centre of mass is relative to half court during a transition (a band 4 m either side)."),
        ("alignment_snap", "The ball position band used to take the half-court alignment snapshot."),
        ("post_depth", "How deep a post-up catch is: deep (6 ft or less), standard, high."),
        ("contest_distance", "Distance from the shooter to the nearest defender: very tight, tight, open, wide open."),
        ("canon_flags", "Two flags kept from an older scheme: paint outside the restricted area, behind the board."),
    ]),
    ("7.3 Coaching bands", [
        ("ball_zone", "Where the ball is: high post, low post, short corner, corner, wing, top."),
        ("ball_reversal", "Which side band the ball is in, for counting ball reversals."),
        ("pnr_location", "Where a ball screen is set: high, slot, side, corner, logo."),
        ("pickup_y", "Where the defence first picks up the ball: full court, three-quarter, half court, top of the key."),
        ("court_thirds", "Middle third or outer third of the court width."),
        ("transition_lanes_3", "Three running lanes in transition: middle and two wings."),
        ("transition_lanes_5", "Five running lanes in transition: middle, two lane-line lanes, two sideline lanes."),
        ("screener_catch", "Where a screener catches after the screen: short roll, pop to the arc, pop to mid-range."),
        ("spacing", "The perimeter band used to judge spacing."),
        ("anchor_capture", "Named offensive points with a small capture disk (Horns bigs, deep slot, lane line high/low ...)."),
        ("defense_landmarks", "Defensive reference points used by the defence taxonomy."),
        ("defensive_depth", "The pack line as a single defensive depth label."),
        ("pack_line", "Inside the pack line, and the band on it."),
        ("out_of_bounds", "Which out-of-bounds strip a player or the ball is in (behind which line, which corner)."),
    ]),
    ("7.4 Zone defences", [
        ("2-3", "2-3 zone: where each of the five defenders should be for each ball position."),
        ("1-3-1", "1-3-1 zone positions for ball at the top, wing and corner."),
        ("1-1-3", "1-1-3 (Baylor) zone positions."),
        ("1-2-2", "1-2-2 zone positions."),
        ("2-1-2", "2-1-2 zone positions."),
        ("3-2", "3-2 zone positions."),
        ("box_and_1", "Box-and-1: the four zone defenders' box."),
        ("diamond_and_1", "Diamond-and-1: the four zone defenders' diamond."),
        ("triangle_and_2", "Triangle-and-2: the three zone defenders' triangle."),
    ]),
    ("7.5 Presses", [
        ("press_1-2-1-1", "1-2-1-1 full-court press roles."),
        ("press_1-2-2", "1-2-2 press roles."),
        ("press_1-3-1", "1-3-1 full-court press roles."),
        ("press_1-3-1_halfcourt", "1-3-1 half-court trap roles."),
        ("press_2-2-1", "2-2-1 full and three-quarter press roles."),
        ("press_2-2-1_halfcourt", "2-2-1 half-court trap roles."),
        ("press_41_deny", "41 Deny: the inbound safety."),
    ]),
])

SIDE_CAPTION = OrderedDict([
    ("centre", "Centre labels (one label for both sides)"),
    ("mirrored", "Side labels (written for the right side; the left side is the mirror image, suffix `_right` / `_left`)"),
    ("table_side", "Bench-side labels (drawn on the scorers'-table side; need `table_side_x_sign`)"),
    ("n/a", "No side (not mirrored; relative entries are measured from the ball or another player)"),
    ("other", "Other"),
])

CTX_WORDS = [({"bx", "by", "ball_side"}, "ball"), ({"hx", "hy"}, "handler"), ({"ax_", "ay_"}, "assigned attacker"),
             ({"dribbling"}, "dribble state"), ({"lowest_defender_y"}, "all five defenders"),
             ({"lowest_attacker_y"}, "all five attackers"), ({"px", "py"}, "previous frame"),
             ({"sx", "sy"}, "screener"), ({"game_clock_s", "shot_clock_s"}, "clock"),
             ({"table_side_x_sign"}, "table side"), ({"t_since_catch_s"}, "time since catch"),
             ({"n_off_in_paint", "team_centroid_x", "team_centroid_y"}, "team aggregate")]
ORIGINAL_CTX = {"bx", "by", "hx", "hy", "ax_", "ay_", "ball_side"}


# ---------------------------------------------------------------- formatting helpers
def esc(s):
    """Text for a table cell or prose: one line; pipes, '*' and tag-like '<' escaped."""
    s = " ".join(str(s).split())
    s = s.replace("\\", "\\\\").replace("|", "\\|").replace("*", "\\*")
    return re.sub(r"<(?=[A-Za-z/!?])", "&lt;", s)  # only a '<' that could open an HTML tag


def code(s):
    s = " ".join(str(s).split()).replace("|", "\\|")
    return f"`{s}`"


def ft(v):
    return v / FT


def anchor_cell(e):
    a = e.get("anchor")
    if not isinstance(a, dict) or a.get("x") is None or a.get("y") is None:
        return "none (no single point)"
    x, y = float(a["x"]), float(a["y"])
    r = math.hypot(x, y)
    th = math.degrees(math.atan2(y + 0.0, x)) if (x or y) else 90.0
    out = f"({x:.2f}, {y:.2f}) m<br>r {r:.2f} m ({ft(r):.1f} ft), θ {th:.1f}°"
    z = a.get("z")
    if z not in (None, 0, 0.0):
        out += f"<br>height z {float(z):.2f} m"
    return out


def side_labels(e):
    if e.get("side") == "mirrored":
        return f"`{e['id']}_right`, `{e['id']}_left`"
    return f"`{e['id']}`"


def label_cell(e, show_rank=False):
    parts = [side_labels(e)]
    if e.get("name"):
        parts.append(esc(e["name"]))
    if e.get("aliases"):
        parts.append("Also called: " + esc(", ".join(str(a) for a in e["aliases"])))
    if e.get("speech_alias"):
        parts.append("In speech: " + esc(e["speech_alias"]))
    meta = []
    if show_rank and e.get("rank") is not None:
        meta.append(f"rank {e['rank']}")
    if e.get("confidence"):
        meta.append(f"confidence {e['confidence']}")
    if meta:
        parts.append(", ".join(meta))
    return "<br>".join(parts)


def meaning(e):
    return e.get("plain") or e["bounds_text"]


def rule_cell(e):
    if e.get("expr"):
        return code(e["expr"])
    return "none: a procedure or team-level rule, described in words"


def needs(e, spots):
    s = spots.get(e["id"])
    names = s.ctx if s is not None else set()
    if not e.get("expr"):
        return "event layer (no exact rule)"
    words = [w for keys, w in CTX_WORDS if names & keys]
    return ", ".join(words) if words else "own position only"


def table(entries, show_rank=False, extra=None):
    head = ["Label", "Meaning", "Exact rule (expr)", "Anchor"]
    if extra:
        head.insert(2, extra[0])
    rows = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for e in entries:
        cells = [label_cell(e, show_rank), esc(meaning(e)), rule_cell(e), anchor_cell(e)]
        if extra:
            cells.insert(2, extra[1](e))
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def side_key(e):
    s = e.get("side")
    return s if s in SIDE_CAPTION else "other"


def by_side(entries, show_rank=False, extra=None, level="**"):
    """One table per side group, each with a caption; a single group gets no caption."""
    groups = OrderedDict((k, []) for k in SIDE_CAPTION)
    for e in entries:
        groups[side_key(e)].append(e)
    groups = [(k, v) for k, v in groups.items() if v]
    out = []
    for k, v in groups:
        if len(groups) > 1:
            out.append(f"{level}{SIDE_CAPTION[k]}{level}")
            out.append("")
        out.append(table(v, show_rank, extra))
        out.append("")
    return "\n".join(out).rstrip()


def ordered(entries, order):
    pos = {k: i for i, k in enumerate(order)}
    return sorted(entries, key=lambda e: (pos.get(e["id"], len(order)), e["id"]))


# ---------------------------------------------------------------- sections
def constants_table(doc):
    rows = ["| Name | Value | In feet | Meaning |", "|---|---|---|---|"]
    for k, v in doc["constants"].items():
        if not isinstance(v, (int, float)):
            continue
        if k == "BREAK_T":
            val, feet = f"{v}°", "-"
        else:
            val, feet = f"{v} m", f"{ft(v):.2f} ft"
        rows.append(f"| `{k}` | {val} | {feet} | {esc(CONST_MEANING.get(k, ''))} |")
    rows.append("")
    rows.append(f"Source: {esc(doc['constants'].get('source', ''))}.")
    return "\n".join(rows)


def layer_counts(doc, E):
    c = Counter(e["layer"] for e in E)
    yaml_counts = doc.get("layer_counts", {})
    rows = ["| Layer | Entries | Of which with an exact rule | What it holds |", "|---|---|---|---|"]
    other = [k for k in c if k.startswith("zone_scheme:") and k not in LAYER_MEANING]
    for k, what in LAYER_MEANING.items():
        if k == "zone_scheme:*":
            n = sum(c[o] for o in other)
            nx = sum(1 for e in E if e["layer"] in other and e.get("expr"))
            rows.append(f"| other `zone_scheme:` ({len(other)} schemes) | {n} | {nx} | {esc(what)} |")
            continue
        nx = sum(1 for e in E if e["layer"] == k and e.get("expr"))
        rows.append(f"| `{k}` | {c[k]} | {nx} | {esc(what)} |")
    rows.append(f"| total | {len(E)} | {sum(1 for e in E if e.get('expr'))} | |")
    stale = sorted(k for k in set(c) | set(yaml_counts) if yaml_counts.get(k) != c.get(k))
    note = ""
    if stale:
        note = (f"\n\nCounts are taken from the entries. The `layer_counts` block at the top of the YAML is older "
                f"and differs for {len(stale)} layers ({', '.join('`' + s + '`' for s in stale)}).")
    return "\n".join(rows) + note


def spot_gap(spots, E):
    """Share of the in-bounds half court with no coaching spot, and where those points are."""
    sp = [s for s in spots.values() if s.d["layer"] == "spot" and s.code]
    reg = [s for s in spots.values() if s.d["layer"] == "zone_scheme:court_region"]
    tot = empty = 0
    where = Counter()
    step = 0.1
    nx, ny = int(2 * 7.6 / step) + 1, int((12.7 + 1.55) / step) + 1
    for i in range(nx):
        x = -7.6 + i * step
        for j in range(ny):
            y = -1.55 + j * step
            tot += 1
            if not any(s.labels(x, y) for s in sp):
                empty += 1
                lab = [l for s in reg for l in s.labels(x, y)]
                base = re.sub(r"_(left|right)$", "", lab[0]) if lab else "unknown"
                where[base] += 1
    top = ", ".join(f"{k} {100 * v / empty:.0f}%" for k, v in where.most_common(4))
    return (f"About {100 * empty / tot:.0f}% of the half court has no coaching spot (checked on a 0.1 m grid of "
            f"{tot:,} in-bounds points; by region: {top}). There the court region label is the answer.")


def landmarks(E):
    lm = [e for e in E if e["layer"] == "landmark"]
    claimed = set()
    out = []
    for title, (intro, ids) in LANDMARK_GROUPS.items():
        if ids is None:
            sel = [e for e in lm if e["id"] not in claimed]
        else:
            sel = [e for e in lm if e["id"] in ids]
        claimed |= {e["id"] for e in sel}
        if not sel:
            continue
        out += [f"### {title}", "", intro, "", by_side(sel), ""]
    return "\n".join(out).rstrip()


def relative(E, spots):
    rel = [e for e in E if e["layer"] == "relative"]
    groups = OrderedDict((g, []) for g in RELATIVE_GROUPS)
    for e in rel:
        groups[relative_group(e["id"])].append(e)
    rows = ["| Group | What it covers | Labels | Needs |", "|---|---|---|---|"]
    for g, v in groups.items():
        if not v:
            continue
        need = Counter(needs(e, spots) for e in v)
        need_s = "; ".join(f"{k} ({n})" for k, n in need.most_common())
        rows.append(f"| {g} | {esc(RELATIVE_GROUPS[g])} | {', '.join('`' + e['id'] + '`' for e in v)} | {esc(need_s)} |")
    out = ["Summary: " + f"{len(rel)} entries in {sum(1 for v in groups.values() if v)} groups.", "", "\n".join(rows), ""]
    extra = ("Needs", lambda e: esc(needs(e, spots)))
    for i, (g, v) in enumerate(groups.items(), 1):
        if v:
            out += [f"### 6.{i} {g}", "", by_side(v, extra=extra), ""]
    return "\n".join(out).rstrip()


def schemes(E):
    by = OrderedDict()
    for e in E:
        if e["layer"].startswith("zone_scheme:") and e["layer"] not in ("zone_scheme:court_region",
                                                                         "zone_scheme:three_depth"):
            by.setdefault(e["layer"].split(":", 1)[1], []).append(e)
    known = {k for _, lst in SCHEME_GROUPS.items() for k, _ in lst}
    missing = sorted(set(by) - known)
    if missing:
        raise SystemExit(f"gen_doc: add a plain sentence for these zone schemes: {missing}")
    summary = ["| Scheme | Partition | What it is | Labels |", "|---|---|---|---|"]
    detail = []
    for title, lst in SCHEME_GROUPS.items():
        detail += [f"### {title}", ""]
        for k, sentence in lst:
            if k not in by:
                continue
            v = by[k]
            part = "yes" if any(e.get("partition") for e in v) else "no"
            summary.append(f"| `{k}` | {part} | {esc(sentence)} | {len(v)} |")
            detail += [f"**`{k}`** (partition {part}). {esc(sentence)}", "", by_side(v, level="*"), ""]
    return "\n".join(summary) + "\n\n" + "\n".join(detail).rstrip()


def rules(E):
    ru = [e for e in E if e["layer"] == "rule"]
    with_expr = [e for e in ru if e.get("expr")]
    words = [e for e in ru if not e.get("expr")]
    prov = ("cbbd_", "espn_", "hoopmath_", "torvik_", "nba_loc", "nba_distance", "synergy_")
    out = ["#### Rules with an exact area", "", "Rule-book areas and ball-height zones that the computer can check directly.", "",
           by_side(with_expr, level="*"), ""]

    def block(title, intro, sel):
        res = [f"#### {title}", "", intro, ""]
        for e in sel:
            res.append(f"- **`{e['id']}`** ({esc(e.get('name') or e['id'])}). {esc(meaning(e))}")
        return res + [""]

    labelling = [e for e in words if e["id"].startswith("rule_")]
    providers = [e for e in words if e["id"].startswith(prov)]
    rest = [e for e in words if e not in labelling and e not in providers]
    out += block("How labels are computed", "Procedures, written in words (no single formula).", labelling)
    out += block("Other providers' encodings", "How CBBD, ESPN, NBA.com, Synergy, Hoop-Math and Torvik store "
                 "shot locations, and how we translate them.", providers)
    out += block("Team-level and other procedures", "Rules that need several players, a sequence of frames "
                 "or a speech convention.", rest)
    return "\n".join(out).rstrip()


def tests_section(doc, E):
    n_expr = sum(1 for e in E if e.get("expr"))
    lines = [
        "- Static: every exact rule passes the whitelist of allowed operations; every anchor and test point lands "
        "where it should, on both sides (`tools/specgen/named_spots/check.py`; 0 failures in 0.2.0).",
        "- Partitions (0.05 m grid, 231,401 points): 20 partition schemes checked, 0 overlaps in every one. "
        "court_region, nba_basic, nba_range, nba_area, ctg, pbpstats and br_distance cover 100% of the points. "
        "The others cover only their own part of the floor (for example three_depth covers the three-point area and "
        "the backcourt; shot_entry_angle covers no floor points because it labels the ball's flight).",
    ]
    if CBBD.exists():
        c = json.loads(CBBD.read_text())
        x = c.get("cbbd_range_x_court_region", {})
        lines.append(
            f"- Real data: {c['located_field_goal_attempts']} located MSU 2025-26 field-goal attempts in CBBD "
            f"({c['files']} games). Every shot gets exactly one label in each scheme. Two-vs-three agreement with "
            f"CBBD: {c['two_vs_three_agreement']} (the disagreements are within 4 cm of the line). CBBD 'rim' shots: "
            f"{x.get('rim -> restricted_area', 0)} restricted area, {x.get('rim -> paint_non_ra', 0)} paint. "
            "Transform: CBBD x 0..940, y 0..500 tenths of a foot, rim 5.25 ft from each end line, nearer basket "
            "attacked. CBBD's left/right orientation was checked on four UConn made baskets against video "
            "(2026-10-20): CBBD's y axis points to the attacker's left, and the transform negates it. Source: "
            "`results/named_spots_test/cbbd_summary.json`.")
    lines.append(
        f"- Speed: all {n_expr} exact rules for 10 players and the ball cost about 1.9 ms per frame with one "
        "right-side and one mirrored environment per object-frame (measured 2026-10-20 on the Mac; budget 33.37 ms "
        "at 29.97 fps).")
    lines.append("- Picture: `gen_svg.py` samples 300 random points inside every shaded cell of the court picture, "
                 "on both sides, and stops if any point gets a different court_region label from the evaluator.")
    lines.append("- This page: `gen_doc.py` stops if any entry is missing, any text is shortened, any table row has "
                 "the wrong number of columns, or a template placeholder is left unfilled.")
    return "\n".join(lines)


def dropped(doc):
    by = OrderedDict()
    for d in doc.get("dropped_schemes", []):
        by.setdefault((d["layer"], d["why"]), []).append(d["id"])
    return "\n".join(f"  - `{layer}` ({', '.join(ids)}): {esc(why)}" for (layer, why), ids in by.items())


def decision9(E):
    seven = ["press_goalie", "spot_of_exit", "leak_out_runner", "dead_ball_deny", "offball_top_lock",
             "offball_trail", "offball_under_gap"]
    Ed = {e["id"]: e for e in E}
    got = [i for i in seven if Ed.get(i, {}).get("expr")]
    still = [i for i in seven if i in Ed and not Ed[i].get("expr")]
    new_ctx = sorted(CTX_NAMES - ORIGINAL_CTX)
    used = Counter()
    for e in E:
        if e.get("expr"):
            for n in set(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", e["expr"])) & set(new_ctx):
                used[n] += 1
    n_null = sum(1 for e in E if not e.get("expr"))
    return (f"The evaluator now accepts the context names {', '.join('`' + n + '`' for n in new_ctx)}. "
            f"Exact rules use these today: {', '.join(f'`{k}` ({v} entry)' if v == 1 else f'`{k}` ({v} entries)' for k, v in sorted(used.items())) or 'none'}. "
            f"Of the 7 entries loop 2 named, these now have an exact rule: {', '.join('`' + i + '`' for i in got)}; "
            f"these stay in words: {', '.join('`' + i + '`' for i in still)}. "
            f"{n_null} entries in total have no exact rule (most are labelling procedures, provider encodings and "
            "team-level rules added in 0.2.0). The PnR depth sign in defense_full is a separate repo edit.")


def ctx_used(E):
    new_ctx = CTX_NAMES - ORIGINAL_CTX
    used = sorted({n for e in E if e.get("expr")
                   for n in re.findall(r"[A-Za-z_][A-Za-z_0-9]*", e["expr"]) if n in new_ctx})
    return ", ".join(f"`{n}`" for n in used)


def decision13(E):
    hits = []
    for e in E:
        al = [a for a in (e.get("aliases") or []) if re.search(r"elbow[ -]extended", str(a), re.I)]
        if al:
            hits.append(f"`{e['id']}` ({esc(', '.join(al))})")
    owner = [e["id"] for e in E if re.search(r"elbow[ -]extended", str(e.get("speech_alias") or ""), re.I)]
    s = f"open. The speech alias \"elbow extended\" sits on {', '.join('`' + o + '`' for o in owner) or 'no entry'}."
    if hits:
        s += (" The YAML still lists it (or a close form) as an ordinary alias on " + ", ".join(hits) +
              "; removing those aliases is a YAML edit waiting for this decision.")
    return s


# ---------------------------------------------------------------- checks
def check(md, E, shown):
    problems = []
    for e in E:
        if f"`{e['id']}" not in md:
            problems.append(f"entry {e['id']} not on the page")
    for e in shown:
        if esc(meaning(e)) not in md:
            problems.append(f"text of {e['id']} not shown in full")
    lines = md.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i])
                i += 1
            counts = [len(re.findall(r"(?<!\\)\|", re.sub(r"\\\\", "", row))) for row in block]
            if len(set(counts)) != 1:
                problems.append(f"table starting '{block[0][:60]}' has rows with {sorted(set(counts))} pipes")
            if not re.fullmatch(r"\|(---\|)+", block[1]):
                problems.append(f"table starting '{block[0][:60]}' has no separator row")
        else:
            i += 1
    left = re.findall(r"\{\{[A-Z0-9_]+\}\}", md)
    if left:
        problems.append(f"unfilled placeholders {sorted(set(left))}")
    return problems


def build():
    doc, spots = load()
    E = doc["entries"]
    t = TEMPLATE.read_text()
    t = re.sub(r"\A<!--.*?-->\n", "", t, flags=re.S)
    L = lambda layer: [e for e in E if e["layer"] == layer]  # noqa: E731
    fill = {
        "DATE": str(doc.get("date")),
        "VERSION": str(doc["version"]),
        "N_ENTRIES": str(len(E)),
        "N_EXPR": str(sum(1 for e in E if e.get("expr"))),
        "N_NULL": str(sum(1 for e in E if not e.get("expr"))),
        "CONSTANTS": constants_table(doc),
        "EDGE_RULES": "\n".join(f"- {esc(r)}" for r in doc["edge_rules"]),
        "PRECEDENCE": esc(doc["precedence"]),
        "LAYER_COUNTS": layer_counts(doc, E),
        "COURT_REGION": by_side(ordered(L("zone_scheme:court_region"), COURT_ORDER)),
        "THREE_DEPTH": by_side(ordered(L("zone_scheme:three_depth"), DEPTH_ORDER)),
        "SPOT_GAP": spot_gap(spots, E),
        "SPOTS": by_side(ordered(L("spot"), SPOT_ORDER), show_rank=True),
        "LANDMARKS": landmarks(E),
        "RELATIVE": relative(E, spots),
        "SCHEMES": schemes(E),
        "RESTARTS": by_side(L("restart") + L("restart_alignment")),
        "FULLCOURT": by_side(L("fullcourt")),
        "SHOT_ZONE_ALT": by_side(L("shot_zone_alt")),
        "RULES": rules(E),
        "TESTS": tests_section(doc, E),
        "DROPPED": dropped(doc),
        "DECISION9": decision9(E),
        "DECISION13": decision13(E),
        "CTX_NEW": ctx_used(E),
    }
    for k, v in fill.items():
        t = t.replace("{{" + k + "}}", v)
    return t, E


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    md, E = build()
    problems = check(md, E, E)
    if problems:
        for p in problems[:40]:
            print("FAIL", p)
        raise SystemExit(f"gen_doc: {len(problems)} problems; page not written")
    Path(args.out).write_text(md)
    print(f"wrote {args.out} ({md.count(chr(10))} lines, {len(E)} entries)")


if __name__ == "__main__":
    main()
