# Court constants check: config/court_ncaa_men.yaml against the 2026-27 rules book

Date: 2026-10-18. Status: proposal. config/court_ncaa_men.yaml is not edited; the complete proposed list is in `config/vocab/court_constants_proposed.yaml`.

Source: `docs/rules/PRMBB_RulesBook.pdf` (2026-27 NCAA men's rules book). "pdf" is the PDF page; the printed page is pdf minus 3. Court diagrams are on pdf 18-19 (printed 15-16), read at 400 dpi. The restricted-area illustration is on pdf 20 (printed 17). Conversions are exact: 1 ft = 0.3048 m and 1 in = 0.0254 m.

Frame: origin on the floor under the rim centre. x runs along the end line and y runs toward half court (`src/msu_alpha/geometry.py`).

## 1. Existing values

| Key | Config | Book value | Exact m | Rule / page | Verdict |
|---|---|---|---|---|---|
| court_length_m | 28.65 | 94 ft, inside edges | 28.6512 | 1-2.2, pdf 21 / p 18 | OK (rounded) |
| court_width_m | 15.24 | 50 ft | 15.2400 | 1-2.2, pdf 21 | OK |
| rim_centre_from_baseline_m | 1.60 | 63 in from the end line (diagram) = 4 ft board + 6 in + 9 in | 1.6002 | 1-13.1, 1-15.2, pdf 26-27; diagram pdf 19 | OK |
| rim_height_m | 3.05 | 10 ft to upper edge | 3.0480 | 1-15.2, pdf 27 | OK (rounded; use 3.048) |
| lane_width_m | 3.66 | 12 ft to outside of lane lines | 3.6576 | 1-6.1, pdf 22 | OK; state that it is the outer edge |
| free_throw_line_from_rim_centre_m | 4.19 | far edge 15 ft from backboard face | 4.1910 (far edge); 4.1402 (near edge) | 1-6.5, pdf 23 | OK as the far edge; name the edge |
| three_point_arc_radius_m | 6.75 | 22 ft 1.75 in to outside edge | 6.7501 | 1-7.1, pdf 23 | OK |
| corner_three_distance_m | 6.60 | 21 ft 7.875 in to outside edge | 6.6008 | 1-7.1, pdf 23 | OK |
| restricted_area_radius_m | 1.22 | 4 ft to inner edge of 2-in arc | 1.2192 | 1-8, pdf 23; 4-31, pdf 63 | Value is right but the meaning needs correcting (see 2a) |
| half_court_from_rim_centre_m | 12.73 | 47 ft to the division-line centre minus 1.6002 | 12.7254 | 1-5.1, pdf 22 | OK; the frontcourt edge is 12.700 (see 2b) |
| ball_diameter_m | 0.24 | circumference 29.5-30 in | 0.2385-0.2426 | 1-16.8, pdf 28 | OK (store min/max) |
| shot_clock_s | 30 | 30-second shot clock | 30 | 2-11.1, pdf 43 / p 40 | OK; this belongs in rules_edition, not court geometry |
| shot_clock_reset_after_offensive_rebound_s | 20 | reset to 20 s | 20 | 2-11.6.d.1, pdf 45 | OK; this also belongs in rules_edition |

All 13 values agree with the book within rounding (largest gap 2 mm), so the `verified: false` flag can be lifted once the edge naming in section 2 is adopted.

## 2. Corrections and clarifications

a. **Restricted area boundary.** Rule 1-8 measures the 4-ft radius to the *inner* edge of the arc. Rule 4-31 says the area is bounded by the *outer* edge of the arc line, and a secondary defender is in the restricted area when any part of either foot is in or above it. The membership test should therefore be r <= 1.2700 m (1.2192 + 0.0508), not r <= 1.22 m. The straight segments run to the backboard face at y = -0.381 m.

   `geometry.spot()` uses 1.22 m, which is fine as a spot label. Block/charge logic (new-RF-1) must use 1.27 m. This is proposed as **new-CG-2**: "The restricted-area membership test uses the outer edge of the arc, r <= 1.270 m, with straight segments to y = -0.381 m. Acceptance: a unit test with feet at r = 1.25 m returns inside."

b. **Division line.** The frontcourt runs to the nearer edge of the division line, and the line itself is backcourt (9-12.1-2, pdf 99). The frontcourt test is therefore y < 12.700 m in the attacked-rim frame, not 12.73 m.

c. **Three-point geometry.** Both distances are to the outside edge, so a foot *on* the line (inside the outside edge) is a two-point location. The corner straight segment is 9 ft 10.375 in (3.0067 m) on the diagram. The geometry gives 3.0117 m from the end line for the point where the arc meets the straight segment, a 5 mm gap. `corner_theta_deg` is 12.07 degrees, which matches `geometry.py`.

d. **Free-throw line.** 4.19 m is the far edge. The 3-second lane (9-9.1) includes the FT line, so the lane test is y <= 4.191 m.

## 3. Missing constants

All are now in `court_constants_proposed.yaml`, each with rule and page.

- Line width 0.0508 m (2 in).
- Centre circle radius 1.8288 m to the outside edge, plus a 0.9144 m non-jumper space.
- FT semicircle radius 1.8288 m to the outside edge.
- Lane space marks 0.0508 x 0.2032 m and blocks 0.3048 x 0.2032 m. Lane spaces are 0.9144 m deep. The layout along the lane line (block 2.134-2.438 m from the end line, then spaces of 0.914 m separated by 2-in marks) was read from the diagram and needs a full-resolution check.
- Backboard 1.8288 m wide and 1.0668 or 1.2192 m tall. Its face is 1.2192 m from the end line (y = -0.381) and its top edge is 3.9624 m high. The target rectangle is 0.6096 x 0.4572 m.
- Ring inner diameter 0.4572 m, inner edge 0.1524 m from the board, rod at most 0.0159 m.
- Coaching box to the 38-ft line (11.5824 m from the end line). Its boundary mark is at least 0.6096 m long.
- 28-ft marks at 8.5344 m from the end line (y = 6.934). The bench-side line is about 0.914 m into the court per the diagram. The edge the 28 ft is measured to is not stated.
- End-line throw-in spots 3 ft outside the lane lines, at x = +-2.7432 m.
- Restricted-area arc: inner edge 1.2192 m, outer edge 1.2700 m.
- Three-point corner from sideline 1.0192 m, with a corner straight segment of 3.0067 m.
- Restraining line 6 ft behind the end line (y = -3.429).
- Designated-spot width 0.9144 m.
- Closely guarded distance and screen-to-boundary distance, both 1.8288 m.
- Commercial logo box: 3.048 m square, 2.5908 m from the division line and 1.3716 m from the sideline.
- Ball mass 0.567-0.624 kg and bounce 1.245-1.372 m from a 1.829 m drop.

## 4. Knock-on findings in other repo files

- `config/vocabulary_map.yaml` defines the block as `x = ±1.83 m, y 0.3–1.5 m`. The painted block is at y 0.533-0.838 m, outside the lane line at |x| 1.829-2.032 m. The coaching term can stay wider, but the painted block should be added as a separate landmark.
- `schema/tables/restarts.yaml` and the other location columns have a y range of [-2.60, 28.05]. The restraining-line area (y down to -3.43) and the far end (27.05 + 1 m) fit only partly. Widen the lower bound to -3.5 m if out-of-bounds officials and players behind the end line must be stored.
- Inbox 007 open question on 7-3.2.b: the 2026-27 text (pdf 84) is garbled. The diagram on pdf 85 (printed 82) shows the FT line extended to both sidelines, which agrees with 2025-26 change proposal 6. The elbow-to-corner reading is obsolete.

## 5. Open questions

- Which edge of the 2-in 28-ft mark is the 28 ft measured to?
- Should geometry use the exact values (6.7501, 1.6002, 3.048) or the rounded ones in the existing config?
- Should the lane-space layout be confirmed on a full-resolution diagram or a measured court before P3?
