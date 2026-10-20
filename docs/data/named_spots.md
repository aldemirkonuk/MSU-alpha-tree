# Named-spot dictionary

Date: 2026-10-20. Status: proposal under the build freeze. Machine source: `config/named_spots.yaml` (0.1.0, 555 entries, 474 with a checkable expression). Validator: `tools/specgen/named_spots/check.py`. Tests: `tests/test_named_spots.py`.

This is item 1 of the ordered list on coord/BOARD.md: every player and the ball, every frame, labelled with exact boundaries in metres and degrees. Names are labels on the math; speech can differ from the math, and the dictionary stores that as a speech alias instead of bending a boundary (Aldemir's "45" rule).

## 1. Frame and edge rules

- **origin**: floor point under the centre of the attacked rim (team in possession attacks it)
- **x**: along the end line, + to the attacker's right facing the basket
- **y**: from the end line toward half court
- **r**: hypot(x, y), m
- **t**: theta = atan2(y, x) in degrees, (-180, 180]; 0 = right end line, 90 = top of the key, 180 = left end line
- **m**: folded angle: t if -90 <= t <= 90; 180 - t if t > 90; -180 - t if t < -90
- **mirror**: side = mirrored entries are written for the right (x >= 0); the left is x -> -x (ball, handler and assigned attacker x are negated too); right owns x = 0
- **units**: metres, degrees, seconds; 1 ft = 0.3048 m exactly; stored to 0.01 m and 0.1 deg
- **full_court**: far end line y = 27.051, far rim y = 25.4508; backcourt points stay in the same frame

Court constants (2026-27 NCAA men's rules book, `docs/data/court_constants_check.md`): RIM_Y_FROM_END = 1.6002, END_Y = -1.6002, BOARD_Y = -0.381, LANE_X = 1.8288, FT_Y = 4.191, ARC_R = 6.7501, CORNER_X = 6.6008, BREAK_Y = 1.4118, BREAK_T = 12.073, RA_R = 1.27, HALF_Y = 12.7, SIDE_X = 7.62, FAR_END_Y = 27.051, LINE_W = 0.0508.

Edge rules:

- Boundary lines are out of bounds (|x| >= 7.62, y <= -1.6002, y >= 27.051).
- The division line is backcourt except its mathematical edge nearest the attacked basket (frontcourt is y <= 12.700).
- Three-point line: the line is two-point territory (strict is_three).
- Restricted area: the arc line is inside (r <= 1.2700, outer edge), straight segments to the board face.
- Lane and FT line: the lines are part of the lane (|x| <= 1.8288, y <= 4.191).
- Exact ties between non-rule zones go to the zone nearer the rim.

## 2. How it was built

- Research: 9 families (painted and rule landmarks, perimeter, interior, defensive and ball-relative, shot-zone crosswalks, restarts and full court, measurement rules, empirical calibration, repo reconciliation), each followed by a skeptic who recomputed every anchor and opened cited sources (18 agents).
- Synthesis: each family rewritten as entries with a machine expression, anchors and inside/outside probes, then tested by an independent agent (18 agents).
- Merge: one canonical `court_region` partition and `three_depth` attribute (Mac session decision), family precedence painted > interior > perimeter > defensive > restart > rule > shot-zone > empirical > repo; losing definitions kept as `variants_not_adopted`.
- Verification: 4 scenario testers (man-to-man help, zone slides, presses and full court, restarts) and 4 reviewers (rules book, coaching meaning, data engineering, completeness); 104 fixes applied and every test rerun.

## 3. Canonical court region (every object, every frame)

Exactly one label for every floor point (checked on a 0.05 m grid of 231,401 points over and beyond the court: 100% covered, 0 overlaps). Mirrored labels carry `_right`/`_left`; the right owns x = 0.

| Label | Side | Bounds (right side; left by x → −x) | Anchor | Aliases |
|---|---|---|---|---|
| `backcourt` | centre | in bounds, y >= 12.700 (the division line is backcourt, 9-12) | (0.00, 20.00) r 20.00, θ 90.0° | back court |
| `corner_three` | mirrored | \|x\| > 6.6008 (outside edge of the straight) and y <= 1.4118 (the break) | (6.95, 0.00) r 6.95, θ 0.0° | corner, corner 3, dead corner |
| `long_mid_baseline` | mirrored | two-point, r > 4.2672, folded angle <= 30 deg (includes behind the board line) | (5.50, 1.50) r 5.70, θ 15.3° | baseline two, short corner jumper |
| `long_mid_top` | centre | two-point, outside the paint, r > 4.2672, m > 60 (elbow and top-of-key twos) | (1.00, 5.60) r 5.69, θ 79.9° | elbow jumper, top-of-key two |
| `long_mid_wing` | mirrored | two-point, r > 4.2672, 30 < m <= 60 | (4.20, 4.20) r 5.94, θ 45.0° | wing two, elbow-extended two |
| `out_of_bounds` | centre | \|x\| >= 7.62 or y <= -1.6002 or y >= 27.051 (boundary lines are out) | (8.00, 0.00) r 8.00, θ 0.0° | OOB, opponent baseline |
| `paint_non_ra` | centre | \|x\| <= 1.8288 (lane outer edge), y <= 4.191 (FT line far edge), not RA | (0.00, 2.50) r 2.50, θ 90.0° | paint (non-RA), lane outside the RA |
| `restricted_area` | centre | RA polygon to the outer edge of the arc (r <= 1.27; straight to the board face) | (0.00, 0.60) r 0.60, θ 90.0° | RA, charge circle, no-charge semicircle, rim zone, no-charge zone, restricted area arc (NCAA), restricted arc |
| `short_mid` | mirrored | two-point, outside the paint, r <= 4.2672 m (14 ft) | (2.60, 2.60) r 3.68, θ 45.0° | short two, floater range |
| `slot_three` | mirrored | three, 60 < m <= 80 | (3.00, 7.00) r 7.62, θ 66.8° | slot, gap three, guard spot |
| `top_three` | centre | three, m > 80 (both sides of the axis) | (0.00, 7.60) r 7.60, θ 90.0° | top of the key three, straightaway three, top, point |
| `wing_three` | mirrored | three, above the break, folded angle <= 60 deg (45 deg is the wing centre) | (5.30, 5.30) r 7.50, θ 45.0° | 45, wing, free-throw line extended three, side |

**Three-point depth** (attribute):

| Label | Rule |
|---|---|
| `three_depth_corner` | `is_three(x, y) and END_Y < y <= BREAK_Y and ax < SIDE_X` |
| `three_depth_deep` | `is_three(x, y) and BREAK_Y < y <= HALF_Y and 8.2296 < r <= 9.144 and ax < SIDE_X` |
| `three_depth_heave` | `HALF_Y < y < FAR_END_Y and ax < SIDE_X` |
| `three_depth_logo` | `BREAK_Y < y <= HALF_Y and r > 9.144 and ax < SIDE_X` |
| `three_depth_standard` | `is_three(x, y) and BREAK_Y < y <= HALF_Y and r <= 8.2296 and ax < SIDE_X` |

Why 27 ft and 30 ft: MSU 2025-26 above-the-break attempts in CBBD sit a median 0.78 m behind the arc; 90% are within 1.40 m (r < 8.15 m). 27 ft (8.2296 m) puts the "deep" label on the last ~10%.

## 4. Coaching spots (single winner by rank)

| Spot | Side | Bounds | Anchor | Aliases | Confidence |
|---|---|---|---|---|---|
| `lane_mark_2_zone` | mirrored | 1.8288 < x <= 2.7432 and 2.7178 <= y < 2.7686. | (2.29, 2.74) r 3.57, θ 50.2° | lane_mark_2_zone_right | medium |
| `under_basket` | centre | \|x\| <= 1.8288 (lane line outer edge) and -1.6002 <= y < 0.5334 (bottom edge of the painted block), minus restricted_area. Sub-tag baseline_under_board covers \|x\| <= 0.9144 behind the board plane. | (0.91, -0.60) r 1.09, θ -33.3° | baseline under the rim, behind the board, under, UNDER | medium |
| `dunker_spot` | mirrored | 1.8288 < x <= 3.5 and -1.6002 <= y < 0.5334 (right; left by x -> -x). Polar corners (right): (1.905, 16.3) top-inner, (3.540, 8.7) top-outer, (3.848, -24.6) end-line outer, (2.430, -41.19) end-line inner; the zone spans theta -41.2..16.3 deg. (1.868, -11.8) =  | (2.74, 0.00) r 2.74, θ 0.0° | dunker, porch (Iowa State), ghost spot (Wizards), dunker_spot_right, dunker_spot_left | medium |
| `short_corner` | mirrored | 3.5 < x < 6.6008 (corner-three line OUTSIDE edge; the line is a two) and -1.6002 <= y < 1.5, two-point area only. Edge convention shared with high_short_corner: y = 1.5 belongs to high_short_corner. Polar corners (right): (3.808, 23.2), (6.769, 12.8), (6.792,  | (4.72, 0.00) r 4.72, θ 0.0° | short corner, baseline short corner, short-corner post, behind the zone (2-3 zone context), SHORT CORNER | medium |
| `high_short_corner` | mirrored | 3.5 < x <= 5.0 and 1.5 <= y <= 2.5 (all inside the arc; farthest corner r 5.59). Takes y = 1.5 from short_corner so the repo landmark (4.0, 1.5) = (4.27, 20.6 deg) is inside it. | (4.00, 1.50) r 4.27, θ 20.6° | high short corner, short corner high | low |
| `low_post` | mirrored | 1.3716 <= x <= 2.7432 and 0.5334 <= y <= 1.7526. Does not touch the R.A. (R.A. at y 0.5334 reaches only \|x\| 1.152). Polar corners (right): (1.472, 21.3), (2.795, 11.0), (2.226, 52.0), (3.255, 32.6). | (1.83, 0.90) r 2.04, θ 26.2° | low block, post | medium |
| `mid_post` | mirrored | 1.3716 <= x <= 2.7432 and 1.7526 < y < 3.683 (between the first lane space top and the third lane space top). Polar corners (right): (2.226, 52.0), (3.255, 32.6), (3.930, 69.6), (4.592, 53.3). | (2.20, 2.20) r 3.11, θ 45.0° | mid post, mid-block, MID-POST | medium |
| `elbow` | mirrored | 0.9144 <= x <= 2.7432 and 3.683 <= y <= 4.699 (band = FT line far edge +/- 0.508, bottom = top of the third lane space). Polar corners (right): (3.795, 76.1), (4.592, 53.3), (4.787, 79.0), (5.441, 59.7). | (1.83, 4.19) r 4.57, θ 66.4° | elbow, FT-line corner, elbow area, high post elbow, 45 (speech, inside the arc; see speech_45) | high |
| `high_post` | centre | Primary remainder: \|x\| <= 2.7432 and 4.699 < y <= 5.2. The coaching 'high post' umbrella (elbows + nail + this strip) is the separate tag high_post_area. | (0.00, 4.95) r 4.95, θ 90.0° | high post, FT line (as a position), flash spot, HIGH POST | medium |
| `pinch_post` | mirrored | Primary strip 2.7432 < x <= 3.6576 and 3.683 <= y <= 4.699. Anchor moved into the strip: (3.2004, 4.191), r 5.273, theta 52.63. The role tag pinch_post_role (player in elbow or this strip, catch from the same-side wing/slot, holds >= 1.0 s facing up) needs bal | (3.20, 4.19) r 5.27, θ 52.6° | pinch post, elbow extended (inside arc), FT-line extended inside, elbow post | low |
| `lane_middle` | centre | \|x\| < 1.3716 and 0.5334 <= y < 3.683, minus restricted_area. Sub-tags duck_in and floater_zone. | (0.00, 2.70) r 2.70, θ 90.0° | middle of the lane, lane middle | medium |
| `mr_baseline` | mirrored | Two-point area, outside the lane, mirrored theta <= 30 (incl. negative theta below the rim line). Fallback primary: wins only where no higher spot matches. Evaluated alone (with last_floor_contact of the shooter) the same expr is the 2PT shot-zone label. | (5.50, 2.60) r 6.08, θ 25.3° | baseline jumper, short-corner jumper, baseline two | medium |
| `mr_elbow` | mirrored | Two-point area, outside the lane, 60 < mirrored theta <= 80. Fallback primary and 2PT shot zone; a shot from the elbow spot gets spot elbow + shot zone mr_elbow. | (2.30, 5.60) r 6.05, θ 67.7° | elbow jumper, slot two, pull-up at the elbow | medium |
| `mr_top` | centre | Two-point area, outside the lane, 80 < theta < 100. As a primary spot it effectively holds only y > 5.2 near the centre (high_post, elbow, nail claim y <= 5.2 for \|x\| <= 2.7432), i.e. the cap of the FT semicircle (5.2-6.02) up to the arc; as a shot zone it c | (0.00, 5.80) r 5.80, θ 90.0° | top of the key two, FT-circle jumper, top two | medium |
| `mr_wing` | mirrored | Two-point area, outside the lane, 30 < mirrored theta <= 60. Fallback primary and 2PT shot zone. | (4.60, 4.60) r 6.51, θ 45.0° | wing 2, wing two, elbow-extended jumper, FT-line-extended jumper | medium |
| `break_point` | mirrored | The exact point is (6.6008, 1.4118), r 6.7501, theta 12.073. It lies on the line, so the region anchor is (6.70, 1.45). Region: beyond_arc, 9 <= m <= 15, r <= 9.144, in bounds. It overlaps corner_high and wing_low. | (6.70, 1.45) r 6.86, θ 12.2° | the break, corner/wing break, short wing (one usage), break_point_right | medium |
| `centre_circle_logo` | centre | A circle segment: within 1.8288 m (outside edge) of the centre (0, 12.7254), with y < 12.700. r runs from 10.8966 to 12.700. It is a subset of logo_range. | (0.00, 11.80) r 11.80, θ 90.0° | the logo (literal), centre circle, half court | high |
| `ft_line_extended` | mirrored | beyond_arc, 3.591 <= y <= 4.791 and x < 7.62. Along y = 4.191, x runs from 5.2914 (on the arc, theta 38.38) to 7.62 (sideline, theta 28.81, r 8.696). There is no r cap. | (6.00, 4.19) r 7.32, θ 34.9° | FT line extended, free-throw line extended, foul line extended, FTX, ft_line_extended_right | medium |
| `slot_lane_line` | mirrored | beyond_arc, 1.2288 <= x <= 2.4288, r <= 9.144. Theta runs from 68.91 (x 2.4288 on the arc) to 81.69 (x 1.2288 at r 9.144), so the region overlaps both slot_three (m <= 80) and top_three (m > 80). The lane line extended meets the arc at (1.8288, 6.4976), 74.28 de | (1.83, 7.40) r 7.62, θ 76.1° | lane-line slot, narrow slot, Princeton slot, SLOT-LL (motion_starts), lane line extended | medium |
| `corner_deep` | mirrored | corner_three and y <= 0 (m from -13.63 to 0). | (6.90, -0.80) r 6.95, θ -6.6° | deep corner, low corner, bottom of the corner, baseline corner, corner_deep_right | medium |
| `corner_high` | mirrored | corner_three and y > 0 (0 < m <= 12.073). | (6.90, 0.90) r 6.96, θ 7.4° | high corner, top of the corner, corner_high_right | low |
| `wing_high` | mirrored | beyond_arc, 52.5 < m <= 60, r <= 9.144. | (4.40, 6.00) r 7.44, θ 53.7° | high wing, wing-slot gap, wide slot, wing_high_right | low |
| `wing_low` | mirrored | beyond_arc, 12.073 < m <= 30, r <= 9.144. Below 26.30 deg the sideline is reached before r 9.144. | (6.60, 2.40) r 7.02, θ 20.0° | low wing, short wing, baseline wing, wing_low_right | medium |
| `wing_mid` | mirrored | beyond_arc, 30 < m <= 52.5, r <= 9.144. It contains the point where the FT line extended crosses the arc (38.38) and the 45 deg ray. | (5.30, 5.30) r 7.50, θ 45.0° | 45, the 45, wing (strict), FT line extended wing, wing_mid_right | medium |
| `lob_catch_above_rim` | centre | Ball caught or tipped with its centre above ring height (z > 3.048) within 2.0 m of the rim centre and in front of the board plane. The 2.0 m radius is a proposal. | (0.00, 0.80) r 0.80, θ 90.0° |  | low |
| `long_rebound_zone` | centre | Rebound secured between 14 ft and 25 ft from the rim (outside short_mid, up to just beyond the arc). Band edges are proposals. | (0.00, 5.50) r 5.50, θ 90.0° |  | low |

## 5. Landmarks (painted and rule-defined; multi-label)

| Landmark | Bounds | Anchor |
|---|---|---|
| `backboard` | Front face plane y = -0.381; \|x\| <= 0.9144 (6 ft wide); z 2.8956 (3.5-ft board, recommended) to 3.9624 (top at 13 ft). For a 4-ft board the bottom is 2.7432. A 5-cm depth behind the face is allowed for contact detectio | (0.00, -0.38) r 0.38, θ -90.0° |
| `backcourt_28ft_mark` | y = 18.5166 (28 ft from the far end line's inside edge, 27.0510); same mark geometry as the frontcourt mark. | (7.62, 18.52) r 20.02, θ 67.6° |
| `block_zone` | 1.8288 < x <= 2.7432 and 0.5334 <= y < 0.8382 (7-8 ft from the end line, half-open in y). | (2.29, 0.69) r 2.39, θ 16.7° |
| `division_line` | 12.7000 <= y <= 12.7508 (centre 12.7254 = 47 ft - 1.6002). The line itself is backcourt. | (0.00, 12.73) r 12.73, θ 90.0° |
| `end_line` | -1.6510 <= y <= -1.6002, \|x\| <= 7.6708. The line is out of bounds; inbounds is y > -1.6002. | (0.00, -1.63) r 1.63, θ -90.0° |
| `free_throw_line` | \|x\| <= 1.8288, 4.1402 <= y <= 4.1910 (far edge 15 ft from the board face). Part of the lane. | (0.00, 4.17) r 4.17, θ 90.0° |
| `lane_block` | 1.8288 < x <= 2.0320 (8 in out from the lane line's outer edge), 0.5334 <= y <= 0.8382 (7-8 ft from the end line). Paint only; the rule zone is block_zone_right. | (1.93, 0.69) r 2.05, θ 19.6° |
| `lane_line_landmark` | 1.7780 <= x <= 1.8288, -1.6002 < y < 4.1402 (meets the FT line, which owns the corner). | (1.80, 1.27) r 2.21, θ 35.2° |
| `lane_mark_1` | 1.8288 < x <= 2.0320, 1.7526 <= y <= 1.8034. Paint only; rule zone is lane_mark_1_zone_right. | (1.93, 1.78) r 2.62, θ 42.6° |
| `lane_mark_1_zone` | 1.8288 < x <= 2.7432 and 1.7526 <= y < 1.8034. | (2.29, 1.78) r 2.90, θ 37.9° |
| `lane_mark_2` | 1.8288 < x <= 2.0320, 2.7178 <= y <= 2.7686. Paint only. | (1.93, 2.74) r 3.35, θ 54.9° |
| `lane_mark_3` | 1.8288 < x <= 2.0320, 3.6830 <= y <= 3.7338. Paint only. | (1.93, 3.71) r 4.18, θ 62.5° |
| `lane_mark_3_zone` | 1.8288 < x <= 2.7432 and 3.6830 <= y < 3.7338. The lane line above it (y 3.7338..4.1402) is unmarked. | (2.29, 3.71) r 4.36, θ 58.3° |
| `mark_28ft` | y = 6.9342 (28 ft from the end line); the 2-in paint is 6.8834..6.9342 or 6.9342..6.9850 (edge unstated), so the expr covers both. Bench side: from 3 ft inside the court (x >= 6.7056) on through the bench area; opposite  | (7.62, 6.93) r 10.30, θ 42.3° |
| `restraining_line` | Line 6 ft (1.8288 m) behind the end line inside edge: y from -3.4798 to -3.4290 (2-in line, edge nearest the court at -3.429; the rule does not name the edge, nearest-edge reading adopted). Line 6 ft from the end line's  | (0.00, -3.45) r 3.45, θ -90.0° |
| `restricted_area_arc_line` | Painted arc 1.2192 <= r <= 1.2700 for y >= 0 (2-in line, inner edge 4 ft). The straight legs below y = 0 are restricted_area_straight_leg_right/left. | (0.00, 1.24) r 1.24, θ 90.0° |
| `restricted_area_straight_leg` | 1.2192 <= x <= 1.2700, -0.381 <= y < 0 (diameter point to the backboard face). | (1.24, -0.19) r 1.26, θ -8.7° |
| `ring` | Ring metal: 0.2286 <= r <= 0.2445 (9-in inside radius plus a rod of at most 5/8 in), z 3.0321 to the upper edge 3.048. Near inner edge at y = -0.2286, 0.1524 in front of the board face. | (0.00, 0.24) r 0.24, θ 90.0° |
| `sideline` | 7.6200 <= x <= 7.6708 for the full length; inbounds is x < 7.6200. | (7.65, 0.00) r 7.65, θ 0.0° |
| `three_point_arc` | 6.6993 <= r <= 6.7501 for y > 1.4118 (corner/arc split is the horizontal line y = 1.4118 where the outside edges meet, theta 12.073). | (0.00, 6.72) r 6.72, θ 90.0° |
| `three_point_corner_straight` | 6.5500 <= x <= 6.6008, -1.6002 < y <= 1.4118 (joins the arc at y = 1.4118, 3.0120 m from the end line by geometry; the diagram says 3.0067). | (6.58, 0.00) r 6.58, θ 0.0° |
| `backboard_target_rectangle` | Plane y = -0.381; \|x\| <= 0.3048 (24 in outside width); z 3.048..3.5052 (18 in tall; outside bottom edge 6 in above the bottom of a 42-in board, level with the ring's upper edge). 2-in white line. | (0.00, -0.38) r 0.38, θ -90.0° |
| `endline_throw_in_mark` | 2-in wide, 12-in long mark perpendicular to the end line at x = 2.7432 (centred, assumed), drawn on the court side: -1.6002 < y <= -1.2954. Recommended, not mandatory. | (2.74, -1.45) r 3.10, θ -27.8° |
| `out_of_bounds_colour_belt` | Where a court uses a painted out-of-bounds belt instead of 2-in lines, the boundary is the colour change at the same inside-edge positions; the belt is at least 8 in (0.2032 m) wide. The expr covers the minimum 8-in band | (7.72, 5.00) r 9.20, θ 32.9° |
| `free_throw_semicircle` | y >= 4.191 and hypot(x, y - 4.191) <= 1.8288 (6-ft outside radius). Painted arc 1.7780..1.8288. Top point (0, 6.0198). | (0.00, 4.97) r 4.97, θ 90.0° |
| `legacy_restricted_area_arc_3ft` | Old 3-ft arc that may remain beside the 4-ft arc in a contrasting colour: 0.9144 <= r <= 0.9652, y >= 0 (inner-edge convention assumed as for the 4-ft arc). Straight legs, if any, are not described. No rule effect; kept  | (0.00, 0.94) r 0.94, θ 90.0° |
| `court_corner` | Point (7.62, -1.6002), the inside-edge corner, with a 0.45-m proximity radius. Corner of the 7-3.2.b end-line throw-in rectangle (end line to the FT line extended, full width); the pre-2025 corner-to-elbow diagonal no lo | (7.62, -1.60) r 7.79, θ -11.9° |
| `elbow_landmark` | Point (1.8288, 4.191), r 4.5726, theta 66.43, with the repo's 0.9-m landmark proximity radius. | (1.83, 4.19) r 4.57, θ 66.4° |
| `ft_circle_top` | Point (0, 6.0198) with a 0.45-m proximity radius (stays inside the 3-pt arc's inner edge, 0.68 m away). | (0.00, 6.02) r 6.02, θ 90.0° |
| `nail` | Point (0, 4.191) with the repo's 0.9-m landmark proximity radius (geometry.LANDMARK_RADIUS_M). | (0.00, 4.19) r 4.19, θ 90.0° |
| `rim_centre` | Origin x=0, y=0, 1.6002 m from the end line's inside edge. The label covers the floor projection of the ring's inside (r <= 0.2286). Ring upper edge z = 3.048. | (0.00, 0.00) r 0.00, θ 90.0° |
| `three_point_area` | Inbounds and strictly beyond the outside edge of the 3-pt line: \|x\| > 6.6008 for y <= 1.4118, r > 6.7501 above. A foot on the line is a 2. | (0.00, 7.60) r 7.60, θ 90.0° |
| `second_three_point_line` | Venue-specific: 1-7.2 allows more than one 3-pt line on a court (contrasting colour, no belt between). Its radius and corner distance are not in the men's rules, so no fixed expr; detect it at venue calibration and tag i | - |
| `rim` | Disk r <= 0.2286 (ring inner radius) under the ring; for ball_3d also test z near 3.048 outside this expr. | (0.00, 0.00) r 0.00, θ 90.0° |
| `charge_circle` | The painted 2-in line: 1.2192 <= r <= 1.2700 for y >= 0 plus the straight legs 1.2192 <= \|x\| <= 1.2700, -0.381 <= y < 0. Non-exclusive tag; the line belongs to restricted_area. 'Outside the charge circle' for a defende | (0.00, 1.24) r 1.24, θ 90.0° |
| `painted_block` | 1.8288 < x <= 2.0320 and 0.5334 <= y <= 0.8382 (12 in along the lane x 8 in outward from the lane line outer edge). The block is NOT part of the lane (Rule 1-6.1), hence x > 1.8288. Non-exclusive tag; primary label there | (1.93, 0.69) r 2.05, θ 19.6° |
| `lane_line` | Positional tag on_lane_line: \| x - 1.8034 \| <= 0.3048 (1 ft either side of the painted line centre) from the end line to the FT line. Painted line itself = 1.7780 <= x <= 1.8288. NON-EXCLUSIVE tag: it overlaps under_ba | (1.83, 1.50) r 2.37, θ 39.4° |
| `mikan_spot` | 0.4572 <= x <= 1.524 and -0.381 <= y <= 0.9144: one side of the rim, in front of the backboard plane, close finishes off the glass. Non-exclusive tag; primary is mostly restricted_area, the outer part under_basket / lane | (0.91, 0.30) r 0.96, θ 18.2° |
| `block_outside_lane` | Named variant point (2.10, 0.60) = (2.18, 15.9 deg) with a 0.6 m capture disk; primary label there is low_post. Nearest variant wins when disks overlap. | (2.10, 0.60) r 2.18, θ 15.9° |
| `mid_post_lane_line` | Named variant point (1.8288, 2.40) = (3.02, 52.7 deg) with a 0.6 m capture disk; primary label is mid_post (or low_post / lane_middle at the disk edge). | (1.83, 2.40) r 3.02, θ 52.7° |
| `wide_pin_spot` | Named point (5.516, 1.792) = (5.8, 18 deg) with a 0.6 m capture disk; primary label mr_baseline (overlaps short_corner at the disk bottom). Screener location for wide pin-downs; offense_full §8.1 heuristic: screener at t | (5.52, 1.79) r 5.80, θ 18.0° |
| `deep_seal` | Spatial gate: 0.9144 <= x <= 2.7432, -0.381 <= y <= 0.8382 (board face to the block top), outside the R.A. The deep_seal label also needs back-to-basket posture with a defender pinned on the high side; that posture test  | (1.60, 0.40) r 1.65, θ 14.0° |
| `front_of_rim` | r < 2.5 and in front of the backboard plane (y >= -0.381). Matches the ROLL / rim_run_repo endpoint r < 2.5; the dump-off primitive uses the inner part r < 2.0. | (0.00, 1.00) r 1.00, θ 90.0° |
| `baseline_dunker` | Dunker spot below the backboard-face plane: 1.8288 < x <= 3.5, -1.6002 <= y < -0.381 (heels-on-baseline setup). Anchor r 2.917, theta -19.86. | (2.74, -0.99) r 2.92, θ -19.9° |
| `baseline_under_board` | \|x\| <= 0.9144 (backboard half-width) and -1.6002 <= y < -0.381. Sub-tag of under_basket. | (0.00, -1.00) r 1.00, θ -90.0° |
| `duck_in` | \|x\| < 1.3716, 0.5334 <= y < 1.7526, outside the R.A. Sub-tag of lane_middle (Carolina duck-in landing). | (0.60, 1.40) r 1.52, θ 66.8° |
| `floater_zone` | Inside the lane (lines included) with 2.4384 (8 ft) <= r < 4.191. | (0.00, 3.30) r 3.30, θ 90.0° |
| `ft_line_extended_inside` | \|y - 4.191\| <= 0.508, outside the lane (x > 1.8288), inside the arc (at y = 4.191 the arc outside edge is x = 5.2914). | (4.00, 4.19) r 5.79, θ 46.3° |
| `high_post_area` | \|x\| <= 2.7432 and 3.683 <= y <= 5.2. Always set inside the band; the primary is elbow, nail or high_post. | (0.00, 4.40) r 4.40, θ 90.0° |
| `upper_dunker` | 1.8288 < x <= 3.5, -0.381 <= y < 0.5334. Corner (1.8288, -0.381) = (1.868, -11.8 deg). | (2.74, 0.00) r 2.74, θ 0.0° |
| `long_two` | Two-point area with r >= 4.8768 (16 ft). | (3.00, 5.80) r 6.53, θ 62.7° |
| `post_area_rule` | \|x\| <= 2.7432 and -1.6002 <= y <= 4.191: the lane plus the 36-in lane-space depth on each side. The post_player flag also needs back-to-basket orientation (outside the expr). | (0.00, 1.30) r 1.30, θ 90.0° |
| `toe_on_line` | Two-point area within 0.3048 of the three-point line OUTSIDE edge: 6.2960 <= \|x\| <= 6.6008 on the corner straight (y <= 1.4118), 6.4453 <= r <= 6.7501 on the arc. | (0.00, 6.60) r 6.60, θ 90.0° |
| `ft_lane_block` | LANE_X <= x <= 2.0320 (8 in out from the lane line) and 0.5334 <= y <= 0.8382 (12 in along the lane) | (1.93, 0.69) r 2.05, θ 19.6° |
| `halfcourt_crossing_line` | the painted division line HALF_Y <= y <= 12.7508 (backcourt); the crossing event is a ball/player transition from y >= HALF_Y to y < HALF_Y | (0.00, 12.70) r 12.70, θ 90.0° |
| `coaching_box_38ft_line_landmark` | x > SIDE_X and \|y − 9.9822\| <= 0.4572 (38 ft from the attacked end line) or \|y − 15.4686\| <= 0.4572 (38 ft from the far end line) | (7.92, 9.98) r 12.74, θ 51.6° |
| `oob_endline_to_restraining_line` | −3.4798 <= y < END_Y and \|x\| <= SIDE_X (6 ft beyond the end line's outer edge) | (0.00, -2.50) r 2.50, θ -90.0° |
| `oob_far_endline_to_restraining_line` | FAR_END_Y < y <= 28.9306 and \|x\| <= SIDE_X | (0.00, 27.60) r 27.60, θ 90.0° |
| `sideline_clear_space` | At least 3 ft (preferably 10 ft) of unobstructed space outside each sideline (Rule 1-3.1). Expr covers the mandatory 3-ft band from the sideline's outer edge. | (8.10, 5.00) r 9.52, θ 31.7° |
| `half_court_centre` | Point (0, 12.7254), captured within 0.9 m. | (0.00, 12.73) r 12.73, θ 90.0° |
| `paint` | \|x\| <= 1.8288 and -1.6002 < y <= 4.191 (lane-line outer edges, FT line far edge, in bounds). The lane lines are part of the lane. | (0.00, 2.00) r 2.00, θ 90.0° |
| `ft_semicircle` | y > 4.191 and hypot(x, y - 4.191) <= 1.8288 (outside radius 6 ft); top point (0, 6.0198). The centre convention is unverified: if the centre is the middle of the FT line (y 4.1656), the top point is (0, 5.9944). | (0.00, 5.10) r 5.10, θ 90.0° |

## 6. Ball- and player-relative positions

101 entries. They need context (ball bx, by; handler hx, hy; assigned attacker ax_, ay_). Missing context gives no label (reason no_context), never False. Scenario tests after fixes: man-to-man 47/47 entries (322 cases), zones 53/53 (925 scenarios), presses and full court 38/39 (the one failure is the tester's old half-court edge expectation; the dictionary follows rule 9-12.2), restarts 61/61. Entries without an expression (team-level or temporal: low_man, i_stack, x-out help-the-helper and similar) are labelled by the event layer.

`coaching_box`, `coaching_box_38ft_line`, `second_half_throw_in_division_line`, `division_line_extended`, `scorers_x_mark`, `team_bench_area`, `scorers_table_area`, `timeout_huddle_rectangle`, `commercial_logo_box`, `short_roll_pocket`, `ball_side_interior`, `weak_side_interior`, `seam`, `shake`, `spain_pop_spot`, `drift`, `lift`, `screener_pop`, `trail_spot`, `fill_slide`, `strong_side`, `weak_side`, `box_out_position`, `charge_position`, `deny_on_the_line`, `face_guard`, `i_stack`, `load_to_ball`, `low_man`, `nail_defender`, `offball_top_lock`, `offball_trail`, `offball_under_gap`, `on_ball_tight`, `open_corner`, `pnr_big_blitz`, `post_full_front`, `transition_protect_rim`, `xout_help_the_helper`, `ball_in_middle`, `help_side_line_foot_on`, `high_split`, `izzo_help_spot`, `on_ball_normal`, `one_pass_away`, `pnr_big_at_level`, `pnr_big_hedge`, `post_double_spot`, `post_three_quarter_high`, `transition_stop_ball`, `two_passes_away`, `baseline_drive_help`, `dig_position`, `dunker_spot_defender`, `gap_one_pass`, `low_man_home`, `low_split`, `on_ball_cushion`, `pnr_big_high_drop`, `post_three_quarter_low`, `split_line_neutral`, `transition_safety_back`, `block_help`, `closeout_landing`, `elbow_help`, `gap_occupancy`, `help_side_two_away`, `pnr_big_deep_drop`, `post_behind`, `up_the_line`, `ball_you_man_pistols`, `on_ball`, `tag_ready_spot`, `ball_line_depth`, `sink_sag`, `blob_4_low`, `blob_diamond_131`, `blob_line`, `blob_stack`, `inbound_second_oob_teammate`, `leak_out_runner`, `pb_4_across_line`, `pb_inbounder_screener`, `press_goalie`, `press_on_inbounder`, `rim_run_lane`, `pb_reverse_safety`, `slob_safety_back`, `rule_closely_guarded_distance`, `weak_side_rebound_area`, `ball_screen_to_middle`, `ball_screen_to_sideline`, `drive_baseline`, `drive_middle`, `handoff_exchange_spot`, `official_centre`, `official_lead`, `official_trail`, `rule_verticality_cylinder`, `canonical_defender_point`, `help_position`

## 7. Zone schemes and crosswalks

| Scheme | Partition | Labels |
|---|---|---|
| 1-1-3 | no | z113_centre, z113_high_post_guard, z113_low_wing, z113_point |
| 1-2-2 | no | z122_high, z122_low, z122_top |
| 1-3-1 | no | z131_corner_ball_wing, z131_corner_middle, z131_corner_point, z131_top_baseline, z131_top_middle, z131_top_point, z131_top_wing, z131_wing_baseline, z131_wing_middle, z131_wing_point, z131_wing_weak_wing |
| 2-1-2 | no | z212_guard, z212_low, z212_middle |
| 2-3 | no | z23_corner_ball_guard, z23_corner_centre, z23_corner_weak_forward, z23_corner_weak_guard, z23_hp_guard_deny, z23_hp_low_middle, z23_sc_centre_field, z23_sc_high_post_deny, z23_sc_wing_deny, z23_top_centre, z23_top_forward, z23_top_guard, z23_wing_ball_forward, z23_wing_centre, z23_wing_weak_forward, z23_wing_weak_guard |
| 3-2 | no | z32_low, z32_top, z32_wing |
| anchor_capture | no | arc_high, below_the_block, deep_slot, ft_line_ext_arc, ft_line_ext_inside, ft_line_ext_wing, lane_line_high, lane_line_low, wide_pin_screen_spot |
| ball_zone | yes | ball_zone_high_post, ball_zone_low_post, ball_zone_short_corner, ball_zone_corner, ball_zone_top, ball_zone_wing |
| box_and_1 | no | box_high, box_low |
| br_distance | yes | br_0_3ft, br_3_10ft, br_10_16ft, br_16ft_to_3p, br_3p |
| canon_flags | no | canon_paint_non_ra, canon_behind_board |
| contest_distance | no | contest_open, contest_tight, contest_very_tight, contest_wide_open |
| court_thirds | yes | middle_third, outer_third |
| ctg | yes | ctg_rim, ctg_short_mid, ctg_long_mid, ctg_corner_3, ctg_non_corner_3 |
| ctg_shot | no | heave_zone, rim_zone |
| defense_landmarks | no | def_high_screen_point, def_right_wing, def_wing_screen_point |
| defensive_depth | no | pack_line |
| diamond_and_1 | no | diamond_bottom, diamond_top, diamond_wing |
| nba_area | yes | nba_area_back_court, nba_area_center, nba_area_side, nba_area_side_center |
| nba_basic | yes | nba_backcourt, nba_restricted_area, nba_in_the_paint_non_ra, nba_mid_range, nba_corner_3, nba_above_the_break_3 |
| nba_basic_literal_break | no | nba_corner_3_literal_break |
| nba_range | yes | nba_range_lt8ft, nba_range_8_16ft, nba_range_16_24ft, nba_range_24plus_ft, nba_range_back_court |
| out_of_bounds | yes | oob_backcourt_sideline, oob_behind_attacked_endline, oob_behind_far_endline, oob_corner, oob_far_corner, oob_frontcourt_sideline |
| pack_line | no | pack_line_inside, pack_line_band |
| pbpstats | yes | pbpstats_at_rim, pbpstats_short_mid_range, pbpstats_long_mid_range, pbpstats_corner3, pbpstats_arc3 |
| pickup_y | yes | pickup_full_court, pickup_half_court, pickup_three_quarter, pickup_top_of_key |
| pnr_location | yes | pnr_location_corner, pnr_location_high, pnr_location_logo, pnr_location_side, pnr_location_slot |
| press_1-2-1-1 | no | p1211_disruptor, p1211_interceptor, p1211_safety, p1211_wing |
| press_1-2-2 | no | p122_wing, p122_x1, p122_x4, p122_x5 |
| press_1-3-1 | no | p131_full_centre, p131_full_chaser, p131_full_warrior, p131_full_wing |
| press_1-3-1_halfcourt | no | p131_half_centre, p131_half_chaser, p131_half_warrior, p131_half_wing |
| press_2-2-1 | no | p221_34_guard, p221_full_guard, p221_full_mid, p221_full_prevent |
| press_2-2-1_halfcourt | no | p221_half_back, p221_half_front, p221_half_middle |
| press_41_deny | no | p41_deny_safety |
| screener_catch | no | short_roll_zone, pop_arc_zone, pop_mid_zone |
| spacing | no | arc_band |
| transition_lanes_3 | yes | lane3_middle, lane3_wing |
| transition_lanes_5 | yes | lane5_laneline, lane5_middle, lane5_sideline |
| triangle_and_2 | no | triangle_bottom, triangle_top |

The crosswalks to NBA.com (basic, range, area), Cleaning the Glass, pbpstats and Basketball-Reference distance bands each partition the floor exactly (0 overlaps). CBBD shot range (rim, jumper, three_pointer), Hoop-Math and Torvik buckets are shot types, stored as shot_family, not crosswalked by location.

## 8. Restarts, full court, rules

- Restart positions (51): `blob_endline_spot`, `jump_ball_jumper_half_attacking_team`, `slob_28ft_spot`, `spot_of_exit`, `throw_in_zone_endline_rectangle`, `throw_in_zone_sideline_28ft`, `jump_ball_non_jumper_spaces`, `lane_space_1`, `lane_space_2`, `lane_space_3`, `lane_space_low_open`, `inbounder_defender`, `blob_backcourt_designated_spot`, `blob_designated_spot_restart`, `ft_lane_open_low`, `ft_lane_space_1`, `ft_lane_space_2`, `ft_lane_space_3`, `ft_shooter`, `inbound_after_make_endline`, `jump_ball_jumper_attacking`, `jump_ball_jumper_defending`, `slob_28ft_frontcourt`, `slob_division_line_designated_spot`, `jump_ring_back`, `jump_ring_front`, `slob_28ft_backcourt`, `slob_division_line_backcourt`, `slob_division_line_frontcourt`, `slob_ft_extended_backcourt`, `blob_ballside_corner`, `ft_leak_out`, `ft_perimeter_top`, `ft_perimeter_wing`, `slob_receiver_ballside_corner`, `blob_box_high`, `blob_box_low`, `blob_safety_top`, `ft_rebound_lane_zone`, `jump_ball_deep_safety`, `jump_ball_unrestricted`, `slob_backcourt_point_of_interruption`, `slob_spot_of_exit_frontcourt`, `rule_free_throw_lane_space_membership`, `rule_jump_ball_jumper_half`, `rule_throw_in_designated_spot`, `blob_designated_spot`, `spot_8p53m`, `spot_8p53m_backcourt`, `slob_stack_region`, `four_low_band`.
- Full court (38): `far_restricted_area`, `far_three_point_line`, `frontcourt`, `centre_circle`, `far_lane_paint`, `backcourt_heave`, `transition_wing_lane`, `backcourt_corner_trap`, `backcourt_sideline_trap`, `baseline_corner_trap`, `frontcourt_halfcourt_corner_trap`, `press_backcourt_zone`, `press_depth_full`, `press_depth_three_quarter`, `press_depth_half_court`, `pb_backcourt_elbow`, `long_outlet_zone`, `outlet_ballside`, `outlet_middle`, `pb_home_run_target`, `pb_inbound_receiver`, `pb_inbounder_return`, `pb_middle`, `pb_sideline_halfcourt`, `trailer_spot`, `transition_corner_arrival`, `trap_backcourt_corner`, `trap_coffin_corner`, `trap_halfcourt_backcourt_corner`, `pb_deep_long`, `rule_backcourt_labels`, `rule_backcourt_third_deep`, `rule_backcourt_third_mid`, `rule_backcourt_third_near`, `drag_screen_spot`, `far_rim`, `opp_ft_line`, `opp_top_of_arc`.
- Labelling rules (87): reference points, frame selection, airborne freeze, occlusion, hysteresis and dwell, boundary probability, precedence. Key numbers: dwell 133 ms (5 frames) painted / 233 ms (8 frames) convention; occupancy ≥ 0.50 s (16 frames at 29.97 fps); hysteresis h_min 0.10 m painted, 0.25 m convention.
- Loader contract: with P recomputed. After 0.5 s: label = unknown, keeping last_known_spot and t_last_seen. On re-acquisition, relabel at once (no dwell). Never emit rule decisions from predicted positions. expr null: procedural rule, not a floor region. Loader contract: if x or y is NaN or None, or the object is predicted past 0.5 s, emit court_region=unknown and evaluate nothing. An entry whose expr references a ctx name (bx, by, hx, hy, ax_, ay_, ball_side) returns null, not False, when any of those ctx values is missing. Null is stored as label absent with reason=no_context, never as an exception or as OOB.

## 9. Tests

- Static: every expression passes the AST whitelist; every anchor and probe lands where it should, both sides.
- Partitions (0.05 m grid, 231,401 points): court_region, nba_basic, nba_range, nba_area, ctg, pbpstats, br_distance cover 100% with 0 overlaps; every other partition scheme has 0 overlaps.
- Real data: 3675 located MSU 2025-26 field-goal attempts in CBBD (34 games). Every shot gets exactly one label in each scheme. Two-vs-three agreement with CBBD: 3672/3675 (the 3 disagreements are within 4 cm of the line). CBBD 'rim' shots: 761 restricted area, 347 paint. Transform: CBBD x 0..940, y 0..500 tenths of a foot, rim 5.25 ft from each end line, nearer basket attacked. CBBD's left/right orientation was checked on four UConn made baskets against video (2026-10-20): CBBD's y axis points to the attacker's left, and the transform negates it.
- Speed: all 474 expressions for 10 players and the ball cost 0.81 ms per frame with one environment per object-frame (budget 33.37 ms at 29.97 fps).

## 10. What it replaces

- `src/msu_alpha/geometry.py` spot(), post_zone(), landmark() and `config/vocabulary_map.yaml`: superseded when production starts (code unchanged under the freeze; dated note in the YAML).
- Conflicting spot coordinates in `docs/taxonomy/offense_full.md`, `motion_starts.md`, `set_taxonomy.md` and `docs/requirements.md`: each entry lists what it supersedes. Rim 1.575 m (old offense_full 0.1) and 1.60 m become 1.6002 m.
- Schemes not adopted: zone_scheme:perimeter_class (replaced by court_region + three_depth); zone_scheme:nba_shot_zone (duplicate of nba_basic above_the_break); zone_scheme:canon (replaced by court_region); zone_scheme:court_spot (replaced by court_region (same cells, now full court and exhaustive)); zone_scheme:shot_zone (replaced by court_region); zone_scheme:three_depth (replaced by three_depth (27 ft / 30 ft bands from CBBD p90)); zone_scheme:transition_lanes (overlaps transition_lanes_3/_5 (restart family kept)); zone_scheme:pnr_location (duplicate of the perimeter pnr_location_* scheme).


## 11. Decisions for Aldemir

107 open questions from the families were sorted: 29 are already answered in the dictionary, 49 fold into the 12 decisions below, and 29 can only be settled on film (section 12). Format: question, then the recommended answer.

1. Question: Which edge of each painted mark do distances use (28-ft and 38-ft marks, 3-ft end-line mark, throw-in spot, restraining line, logo box)? Recommended: from the boundary's inside edge, spots centred on their marks, FT line far edge 4.191 everywhere (applied 2026-10-20). Every difference is 5 cm or less, under the ~0.30 m tracking error; one tape measure of the Breslin floor closes it.
2. Question: Are the lane-space and block y limits right? Recommended: lock the current values (block 0.5334-0.8382, spaces 0.8382-1.7526 / 1.8034-2.7178 / 2.7686-3.6830) after one full-resolution read of the rules-book diagram; the under-basket, dunker, post, elbow, nail and lane-space spots depend on them.
3. Question: How should the rules-book gaps be read (fully airborne player over the lane, a jumper's foot on the circle or division line, backcourt designated spots, charge area behind the board, height of the post area, 2026-27 post-clinic PDF)? Recommended: last floor contact for an airborne player; split at 12.700 with both lines counting as the jumper's half; mirror the frontcourt spots; exclude behind the board; cap the post area at the FT line; then read the post-clinic PDF once.
4. Question: Does the 10-second count end at shot clock 20 or 19? Recommended: keep "count start minus 10 s" until a source for 19 is found; no file in docs/rules says 19.
5. Question: Pack-line radius: 16 ft with a 16-17 ft band, 5.2 m, or 5.3 m? Recommended: 16 ft inside with the 16-17 ft band (the only value with an opened source); retire 5.2 and 5.3 and align defense_full F1.1.
6. Question: Do the interior zones match MSU staff speech (high short corner as its own spot, pinch post as a strip outside the elbow, high post as a box, low-post inner edge 1.3716)? Recommended: keep as defined (the box form keeps zones from overlapping) and confirm the words with staff.
7. Question: Perimeter terms: approve extended_corner (12-22 deg), keep "corner pocket" and "slot of the corner" as aliases, FT-extended wing anchor 6.0 or 6.5? Recommended: extended_corner as an optional tag only, keep the aliases, anchor 6.0.
8. Question: What does "two-side" in docs/requirements.md mean? Recommended: alias of help_side_two_away, unless staff use it for ball reversal.
9. Question: Should the expression language gain screener coordinates, a dribble flag and team aggregates, and should the PnR depth sign in defense_full be fixed? Recommended: yes to both; several of the 11 entries without an expression become computable.
10. Question: May the repo follow the dictionary as one batch (is_three strict, restricted area 1.22 -> 1.27, corner_deep rename, post_zone switch, A0 lane-stack spots, storage y range -3.6 to 29.0)? Recommended: yes, as one change set when the freeze lifts; every edit is listed under supersedes on its entry.
11. Question: Pay for or log into KenPom, ShotQuality, CBB Analytics, ShotTracker or Torvik to read their zone definitions? Recommended: no for v1; CBBD and the rules book cover the canonical zones.
12. Question: Frame conventions: defenders labelled only in the offence's frame, relative entries unmirrored, transition safety in his own rim's frame, "passes away" from a learned model later? Recommended: offence frame only, no mirroring for side n/a, own-rim frame for the safety, learned model later.

## 12. Settled only on film or tracking

- Capture radii of landmarks (0.45-1.2 m), wing band edges, FT-extended half-width, dunker box and short-corner depth: density of off-ball positions on MSU film.
- Mid-range 30/60/80 deg cuts and wing 60/80 cuts: gaps in off-ball tracking positions (shot charts are not enough).
- Lift, drift, shake, fill and trail timing, low-man rotation window, transition thresholds: labelled possessions.
- Zone and press anchors: fit to positions players hold on film (assignment residuals).
- Sign conventions (CBBD, ESPN, NBA, Synergy left/right): match about 10 known corner threes to video.
- Grounded-foot classifier, foot keypoint confidence, broadcast floor-position error: hand-labelled MSU frames.
- Backboard thickness and box position on a 48-in board, rim offset: one venue frame or manufacturer spec.
