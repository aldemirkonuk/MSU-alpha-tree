<!-- Template for docs/data/named_spots.md. Edit the prose here, then run
     python tools/specgen/named_spots/gen_doc.py
     Every {{NAME}} is filled from config/named_spots.yaml by gen_doc.py. Do not edit the generated page by hand. -->
# Named-spot dictionary

Date: {{DATE}}. Version {{VERSION}}. Status: proposal under the build freeze.

This page is generated from `config/named_spots.yaml` by `tools/specgen/named_spots/gen_doc.py` (prose from `tools/specgen/named_spots/doc_template.md`). Do not edit it by hand. The YAML holds {{N_ENTRIES}} entries; {{N_EXPR}} of them have an exact rule that a computer can check, and {{N_NULL}} are procedures or team-level rules written in words only.

The dictionary gives a name to every place on the floor, for every player and the ball, in every frame. Each name sits on exact boundaries in metres and degrees. Names are labels on the math. When coaches say a word differently from the math (for example "45"), the word is stored as a speech alias; the boundary never moves (Aldemir's "45" rule).

## 0. How to read this page

![Half court in metres with the 12 court regions shaded and the main coaching spots as dots](named_spots_court.svg)

The picture is drawn from the YAML by `tools/specgen/named_spots/gen_svg.py`. Shaded areas are the 12 court regions (names on the left half). Dots are the main coaching spots (names on the right half). The left half is the mirror image of the right.

- **x**: metres to the right of the rim, as the attacker faces the basket. Negative x is the left side.
- **y**: metres from the rim toward half court. The end line is at y = -1.6002 m (5.25 ft behind the rim centre). The near edge of the division line is y = 12.700 m.
- **r**: straight-line distance from the rim centre, in metres.
- **angle m**: degrees measured from the nearest end line, seen from the rim. 0 = along the baseline, 90 = straight up the middle. The same number on the left and the right. It goes below 0 behind the rim line (deep corner, under the board).
- **right / left**: as the attacker faces the basket.
- **centre label**: one label for both sides (for example `top_three`).
- **side label**: written once for the right side and copied to the left by flipping x. The stored label carries `_right` or `_left` (for example `wing_three_left`).
- **single winner**: a layer where a player has exactly one label (court region, coaching spot). **Tag**: a layer where a player can have many labels at once (landmarks, relative positions).
- **rank**: which spot wins when two overlap; the smaller number wins.
- **confidence**: high = rule book; medium = common staff usage; low = our proposal, to be checked on film.
- **reference point**: which body point is measured. Normally the midpoint of the feet; for a shot, the last floor contact; for the ball, the ball centre.
- **Exact rule (expr)**: the formula the computer checks, in code font. You do not need to read it; the "Meaning" column says the same thing in words. Names in it: `ax` = |x|; `t` = the full angle (0 to 180 across the court); `m` = angle m; `is_three(x, y)` = true when the point is past the three-point line; `bx, by` = ball; `hx, hy` = ball handler; `ax_, ay_` = the attacker this defender guards.
- **Anchor**: the typical point of a label, as (x, y) in metres and as distance r and full angle θ from the rim (θ = 0 to the right along the end line, 90 straight up the middle, 180 to the left).

Distances in prose are written as metres (feet), for example 4.2672 m (14 ft). 1 ft = 0.3048 m exactly.

## 1. Glossary

| Short form | Meaning |
|---|---|
| RA | Restricted area: the 4-ft half circle under the basket where a help defender cannot draw a charge. In prose this page writes "restricted area". |
| FT | Free throw. "FT line" = the free-throw line, 15 ft from the backboard. |
| OOB | Out of bounds. |
| BLOB / SLOB | Baseline / sideline out-of-bounds play (a throw-in from the end line / sideline). |
| PnR | Pick and roll (ball screen). |
| DHO | Dribble hand-off. |
| CTG | Cleaning the Glass, an NBA stats site with its own shot-zone map. |
| CBBD | College Basketball Data, the source of our MSU shot locations. |
| pb | Press break (the offence beating a full-court press). |
| p1211, p122, p131, p221 | Press shapes: 1-2-1-1, 1-2-2, 1-3-1, 2-2-1 (players per line from the ball outward). |
| z23, z131, z113, z122, z212, z32 | Zone-defence shapes: 2-3, 1-3-1, 1-1-3, 1-2-2, 2-1-2, 3-2. |
| crosswalk | A translation from our labels to another company's zone map (NBA.com, CTG, pbpstats, Basketball-Reference). |
| partition | A scheme where every floor point gets exactly one label of that scheme (no gaps, no overlaps). |
| three-point area | The floor strictly past the three-point line. A foot on the line is a two. |
| ctx (context) | Extra information a label needs besides the player's own position: the ball, the handler or the assigned attacker. |
| no_context | The reason stored when a label cannot be decided because that extra information is missing. The label is left empty, never "false". |
| P (probability) | How sure we are that a player is inside a region, given tracking error (about 0.30 m). |
| hysteresis | A small buffer at a boundary so a player standing on the line does not flicker between two labels. |
| dwell | How long a new label must hold before it is accepted. |
| signed distance | How far a player is inside (+) or outside (-) a region's boundary, in metres. |

## 2. Frame and edge rules

**The frame** (where (0, 0) is and which way the axes point):

- **origin**: the floor point under the centre of the basket attacked by the team in team control (rule 4-9). With no team control, the last team in control. Before the first control of a period, the absolute frame (`rule_rim_frame_selection`). This is not the same as the game state's `possession_team`, which flips at a made basket or a violation (T05, T13) and at the whistle of T09/T11, before the frame does (`rule_no_team_control_frames`).
- **x**: along the end line, positive to the attacker's right facing the basket.
- **y**: from the rim toward half court.
- **r**: hypot(x, y), in metres.
- **t (full angle θ)**: atan2(y, x) in degrees, in (-180, 180]. A y of -0.0 is set to +0.0 first, so the left end of y = 0 is 180, never -180. At r = 0, t is defined as 90. 0 = right end line, 90 = top of the key, 180 = left end line.
- **angle m**: m = degrees(atan2(y, |x|)), and 90 at the origin. It equals the folded full angle (t on the right, 180 - t on the left) but gives exactly the same number for x and -x.
- **left and right**: a side label is written once for the right side (x >= 0) and copied to the left by flipping x; the ball, handler and assigned-attacker x are flipped too. A point exactly on the middle line x = 0 belongs to the right label, except for centre labels (restricted_area, paint_non_ra, long_mid_top, top_three, backcourt, out_of_bounds), which have no side.
- **units**: metres, degrees, seconds. 1 ft = 0.3048 m exactly. Stored to 0.01 m and 0.1 degree.
- **full court**: far end line y = 27.051 m, far rim y = 25.4508 m. Backcourt points stay in the same frame.

**Court constants** (2026-27 NCAA men's rules book; `docs/data/court_constants_check.md`). Every line position is the edge named in the table.

{{CONSTANTS}}

**Edge rules** (who owns a point that sits exactly on a line):

{{EDGE_RULES}}

**When two labels overlap** (precedence, from the YAML): {{PRECEDENCE}}

**Layers** (how the {{N_ENTRIES}} entries are grouped):

{{LAYER_COUNTS}}

## 3. Court regions (every object, every frame)

`court_region` is the main label. Every floor point gets exactly one of 18 labels: 6 side cells x 2 sides + 6 centre cells. When x or y is missing the label is `unknown`. This was checked on a 0.05 m grid of 231,401 points over and beyond the court: 100% covered, 0 overlaps. The table runs from the rim outward.

{{COURT_REGION}}

### Three-point depth (an extra label on three-point attempts and positions)

{{THREE_DEPTH}}

Why 27 ft and 30 ft: MSU 2025-26 above-the-break attempts in CBBD sit a median 0.78 m (2.6 ft) behind the arc, and 90% are within 1.40 m (4.6 ft), that is r < 8.15 m. 27 ft (8.2296 m) puts the "deep" label on the last ~10%.

## 4. Coaching spots (one winner per player)

These are the words staff use for where a player stands. A player gets at most one spot; when two overlap, the smaller rank wins. The table runs from the rim outward. {{SPOT_GAP}}

{{SPOTS}}

## 5. Landmarks (painted marks, rule areas, coaching tags, named points)

A player can carry many landmark tags at once. They never replace the court region or the coaching spot.

{{LANDMARKS}}

## 6. Ball- and player-relative positions

These labels depend on where the ball, the ball handler or the assigned attacker is, not only on the player's own spot. If that information is missing in a frame, the label is left empty with reason `no_context`. It is never "false" and never "out of bounds". Entries with no exact rule (team-level or timing rules such as low man or the I-stack) are labelled by the event layer from the words in their "Meaning".

Scenario tests after the 0.1.0 fixes: man-to-man 47/47 entries (322 cases), zones 53/53 (925 scenarios), presses and full court 38/39 (the one failure is the tester's old half-court edge expectation; the dictionary follows rule 9-12.2), restarts 61/61.

{{RELATIVE}}

## 7. Zone schemes and crosswalks

A scheme is a family of labels that belong together, such as the five spots of a 2-3 zone or NBA.com's shot zones. "Partition yes" means no point ever gets two labels of that scheme. The court-wide schemes (court_region and the shot-zone crosswalks NBA, CTG, pbpstats and Basketball-Reference) also give every floor point a label; the other partition schemes cover only their own area (for example three_offset covers the frontcourt, a zone slot only exists near its anchor). "Partition no" means labels of that scheme may overlap.

The crosswalks to NBA.com (basic, range, area), Cleaning the Glass, pbpstats and Basketball-Reference distance bands each cover the floor with 0 overlaps. CBBD shot range (rim, jumper, three_pointer), Hoop-Math and Torvik buckets are shot types, stored as `shot_family`, not translated by location.

{{SCHEMES}}

## 8. Restarts, full court, other shot zones and labelling rules

### 8.1 Restarts (dead balls, throw-ins, free throws, jump balls)

Evaluated at the restart snapshot (the frame the ball is put in play).

{{RESTARTS}}

### 8.2 Full court (transition, presses, backcourt)

{{FULLCOURT}}

### 8.3 Other shot-zone labels (kept as alternatives)

Shot-zone labels from other research families. They do not replace `court_region`; they are stored next to it.

{{SHOT_ZONE_ALT}}

### 8.4 Labelling rules

These rules say how labels are computed: which body point is measured, which frame, how to handle noise, missing players and airborne players. Key numbers: dwell 133 ms (5 frames) on painted lines and 233 ms (8 frames) on convention lines before a new label is accepted; a player is "set at a spot" after 0.50 s (16 frames at 29.97 fps); boundary buffer (hysteresis) at least 0.10 m on painted lines and 0.25 m on convention lines.

{{RULES}}

### 8.5 Missing data, in plain words

1. If the feet are hidden but the body is visible, use the bottom of the player box.
2. If the player is fully hidden, predict straight-line motion for up to 0.5 s (15 frames) and keep the last labels.
3. After 0.5 s the label becomes `unknown`; the last known spot and time are kept.
4. When the player reappears, relabel at once.
5. Never make a rule call (three, restricted area, backcourt) from a predicted position.
6. If a label needs the ball, the handler or the assigned attacker and that is missing, the label is left empty with reason `no_context`. That is not "false" and not "out of bounds".

Loader contract (for the programmer):

- A position x or y that is None, NaN, plus or minus infinity, or larger than 100 m in size counts as missing: emit `court_region = unknown` once and evaluate nothing else. A context value (ball, handler, attacker) with the same faults counts as missing (reason `no_context`).
- `unknown` is emitted once per object, by the court_region step; other entries return no label for a missing position, so one hidden player never produces hundreds of `unknown` labels.
- Bench-side labels need `table_side_x_sign(t)` = +1 if the scorers' table is on the attacker's right in the frame of frame t, else -1. Recompute it every frame: it flips with every change of the attacked basket, not only at half time. If it is missing, those labels are left empty.
- Membership probability P for every emitted label: a closed form when the boundary is one straight line (Phi(sd / sigma_n)) or one circle (noncentral chi-square, k = 2); otherwise 1024 scrambled-Sobol samples with a fixed per-game seed, only when the signed distance is within 3 sigma_n (else P = 1 or 0). Rule decisions are final at P >= 0.90 or P <= 0.10 (`rule_probabilistic_membership`).

## 9. Tests

{{TESTS}}

## 10. What it replaces

- `src/msu_alpha/geometry.py` spot(), post_zone(), landmark() and `config/vocabulary_map.yaml`: superseded when production starts (code unchanged under the freeze; dated note in the YAML).
- Conflicting spot coordinates in `docs/taxonomy/offense_full.md`, `motion_starts.md`, `set_taxonomy.md` and `docs/requirements.md`: each entry lists what it supersedes. Rim 1.575 m (old offense_full 0.1) and 1.60 m become 1.6002 m.
- Schemes not adopted:
{{DROPPED}}

## 11. Decisions for Aldemir

107 open questions from the research families were sorted: 29 are already answered in the dictionary, 49 fold into the first 12 decisions below, and 29 can only be settled on film (section 12). Decision 13 was added in loop 2. Format: question, then the recommended answer.

1. Question: Which edge of each painted mark do distances use (28-ft and 38-ft marks, 3-ft end-line mark, throw-in spot, restraining line, logo box)? Recommended: from the boundary's inside edge, spots centred on their marks, FT line far edge 4.191 everywhere (applied 2026-10-20). Every difference is 5 cm or less, under the ~0.30 m tracking error; one tape measure of the Breslin floor closes it.
2. Question: Are the lane-space and block y limits right? Recommended: lock the current values (block 0.5334-0.8382, spaces 0.8382-1.7526 / 1.8034-2.7178 / 2.7686-3.6830) after one full-resolution read of the rules-book diagram; the under-basket, dunker, post, elbow, nail and lane-space spots depend on them.
3. Question: How should the rules-book gaps be read (fully airborne player over the lane, a jumper's foot on the circle or division line, backcourt designated spots, charge area behind the board, height of the post area, 2026-27 post-clinic PDF)? Recommended: last floor contact for an airborne player; split at 12.700 with both lines counting as the jumper's half; mirror the frontcourt spots; exclude behind the board; cap the post area at the FT line; then read the post-clinic PDF once.
4. Question: Does the 10-second count end at shot clock 20 or 19? Recommended: keep "count start minus 10 s" until a source for 19 is found; no file in docs/rules says 19.
5. Question: Pack-line radius: 16 ft with a 16-17 ft band, 5.2 m, or 5.3 m? Recommended: 16 ft inside with the 16-17 ft band (the only value with an opened source); retire 5.2 and 5.3 and align defense_full F1.1.
6. Question: Do the interior zones match MSU staff speech (high short corner as its own spot, pinch post as a strip outside the elbow, high post as a box, low-post inner edge 1.3716)? Recommended: keep as defined (the box form keeps zones from overlapping) and confirm the words with staff.
7. Question: Perimeter terms: approve extended_corner (12-22 deg), keep "corner pocket" and "slot of the corner" as aliases, FT-extended wing anchor 6.0 or 6.5? Recommended: extended_corner as an optional tag only, keep the aliases, anchor 6.0.
8. Question: What does "two-side" in docs/requirements.md mean? Recommended: alias of help_side_two_away, unless staff use it for ball reversal.
9. Question: Should the expression language gain screener coordinates, a dribble flag and team aggregates, and should the PnR depth sign in defense_full be fixed? Recommended: yes to both; several of the 11 entries without an expression become computable.
   Status in {{VERSION}}: adopted. {{DECISION9}}
10. Question: May the repo follow the dictionary as one batch (is_three strict, restricted area 1.22 -> 1.27, corner_deep rename, post_zone switch, A0 lane-stack spots, storage y range -3.6 to 29.0)? Recommended: yes, as one change set when the freeze lifts; every edit is listed under supersedes on its entry.
11. Question: Pay for or log into KenPom, ShotQuality, CBB Analytics, ShotTracker or Torvik to read their zone definitions? Recommended: no for v1; CBBD and the rules book cover the canonical zones.
12. Question: Frame conventions: defenders labelled only in the offence's frame, relative entries unmirrored, transition safety in his own rim's frame, "passes away" from a learned model later? Recommended: offence frame only, no mirroring for side n/a, own-rim frame for the safety, learned model later.
13. Question: What does MSU staff mean by 'elbow extended': the slot above the elbow out at the arc (slot_lane_line), the wing at FT-line height (ft_line_extended / wing_mid), or the strip just outside the elbow inside the arc (pinch_post)? Recommended: give it to slot_lane_line only (its current speech_alias) and confirm with staff.
   Status in {{VERSION}}: {{DECISION13}}

## 12. Settled only on film or tracking

- Capture radii of landmarks (0.45-1.2 m), wing band edges, FT-extended half-width, dunker box and short-corner depth: density of off-ball positions on MSU film.
- Mid-range 30/60/80 deg cuts and wing 60/80 cuts: gaps in off-ball tracking positions (shot charts are not enough).
- Lift, drift, shake, fill and trail timing, low-man rotation window, transition thresholds: labelled possessions.
- Zone and press anchors: fit to positions players hold on film (assignment residuals).
- Sign conventions (CBBD, ESPN, NBA, Synergy left/right): match about 10 known corner threes to video. CBBD is done (4 UConn makes, 2026-10-20); ESPN, NBA and Synergy remain.
- Grounded-foot classifier, foot keypoint confidence, broadcast floor-position error: hand-labelled MSU frames.
- Backboard thickness and box position on a 48-in board, rim offset: one venue frame or manufacturer spec.

## 13. Follow-up edits outside this page

The loop-2 clarity review asked for these changes in other files. They are listed here so nothing is lost. Items already made in 0.3.0 and 0.3.1 have been removed; the rest wait for the freeze to lift or for their owner.

**In `config/named_spots.yaml`:**

1. Use one word per idea in every `bounds_text`: "angle m" (not theta, θ, t, "folded angle" or "mirrored theta" when m is meant), "restricted area" (not RA or R.A. in prose), "three-point area" (not beyond_arc, and not "three" as a noun), and metres (feet) for distances. This page prints `bounds_text` exactly as written, so it still shows the older words in the tables.

**In other repo files (when the freeze lifts):**

17. Schema `*_spot` columns (ball_states, defensive_events, dribbles, drives, events, fouls, movement_primitives, passes, player_positions, rebounds, screens, shots, touches, track_exits, turnovers) and `docs/data/dictionary_games.md` line 121 plus every `*_spot` row: range = the 18 court_region labels plus `unknown`; definition "court_region label from config/named_spots.yaml (single winner, never null: unknown when x or y is missing)". Add `player_positions.named_spot` (the single-winner coaching spot).
18. `config/state_machine.yaml`: add the dimension `frame_team` (home, away, none): the team whose attacked basket defines the frame. Add matching rows to `docs/data/live_game_state.md` section 4, and replace "the team in possession" with "frame_team" in the player_positions location columns and `dictionary_games.md` lines 1641-1650.
19. `config/invariants.yaml` IV-34 and every schema location range: |x| <= 9.62, -3.61 <= y <= 29.06, 0 <= ball z <= 15 (court plus 2.0 m beyond each line, which covers the restraining lines and sideline throw-ins); r [0, 30.62]; ring_0p5m [0, 61]. Bench, coaching-box and table spots: x in [-13.0, 13.0], only in bench and official tables.
20. `player_positions.side`: enum [left, middle, right], middle if |x| < 0.30 m (display buffer 0.20/0.40). `restarts.court_half`: [frontcourt, backcourt, none]; frontcourt iff y <= 12.700 in the frame_team frame.
21. Schema theta ranges: "(-180, 180]; 90 at r = 0".
22. `config/game_ontology.yaml` B.01.04 to B.01.15 and E.04.03: restate in the exact constants (division line centre 12.7254, frontcourt y <= 12.700; arc 6.7501 and corners 6.6008 outside edges; restricted area r <= 1.2700; 28-ft marks y = 6.9342; end-line spots x = ±2.7432; backboard y = -0.381; ring centre 1.6002 from the end line), point B.01.12 to config/named_spots.yaml, mark B.01.13 covered with short_corner = 3.5 < |x| < 6.6008 and y < 1.5, B.01.14 sectors per `sector_ring_cell`, B.01.15 post zones per low_post / mid_post / high_post / high_post_area, E.04.03 release spot = court_region.
23. `config/invariants.yaml` constants: three_point_arc_m 6.7501; three_point_corner_m 6.6008; closely_guarded_distance_m 1.8288; designated_spot_width_m 0.9144; throw_in_spot_end_line_outside_lane_m 0.9144; throw_in_spot_sideline_mark_m 8.5344 (y = 6.9342); restricted_area_radius_edge_m 1.270 as the live value.
24. `docs/requirements.md` lines 101 and 229-250 and `dictionary_games.md` line 120: rim 1.6002 m; lane x = ±1.8288 (outer edge); FT line 4.191 (far edge); arc 6.7501 / corner 6.6008 (outside edges, the line is two-point); restricted area 1.2700 (outer edge); frontcourt y <= 12.700. Replace the named-spot table with a pointer to config/named_spots.yaml. Basket attacked = frame_team's basket.
25. `docs/taxonomy/motion_starts.md` section 0.2: HIGH POST (±0.90, 4.30) -> (0.00, 4.95); ELBOW, SLOT-LL and BLOCK x ±1.83 -> ±1.8288; ELBOW y 4.19 -> 4.191; class column -> named_spots ids.
26. `schema/tables/restarts.yaml` throw_in_spot: add sideline_28ft_mark_backcourt; crosswalk the other four values through aliases (inbound_after_make_endline: end_line_runnable; second_half_throw_in_division_line: division_line_opposite_table; spot_of_exit: sideline_spot, end_line_spot; spot_8p53m_backcourt: sideline_28ft_mark_backcourt).

**In the metric registry (`config/metrics.yaml`):**

27. M-SQ-004 (also M-SQ-014, M-SQ-015, M-SQ-040): SQ.Z_CORNER_Y_M = 3.0120 (= 1.4118 + 1.6002), or use the court_region corner_three label. Today 3.0067 leaves a 5.3 mm band labelled differently.
28. M-PROF-031: corner = release spot in corner_three (y <= 1.4118 and |x| > 6.6008), not "theta <= 12 deg, r >= 6.60 m".
29. M-PROF-035: rim zone r <= 1.2192 (SQ.Z_RIM_M, entry ctg_rim), not 1.25.
30. M-TRN-023 (also M-TRN-024, -026, -056): scoring-zone edge y <= 10.2616 (HALF_Y - 2.4384), not 10.29.
31. M-TRN-022 (also M-TRN-032, -053): half-court crossing when the ball is frontcourt (y <= 12.700), not 12.73.
32. M-DEF-080: pick-up classes = pickup_full_court / three_quarter / half_court / top_of_key, half-court edge 12.700 (not 12.725).
33. M-SQ-007: half-court attempts = release point in court_region backcourt (y > 12.700).
34. M-SQ-015: deep three = three_depth_deep (8.2296 < r <= 9.144) plus three_depth_logo (r > 9.144); retire 7.5 m.
35. M-PLAY-048: ball-screen bands = pnr_location_* with high r 6.5 to 9.144 m, logo beyond 9.144 (not 9.5).
36. M-SPACE-013: middle band = strong_side / weak_side (0.9 m dead band) or rule_side_and_mirror (0.30 m), not 0.5 m.
37. M-REB-055: inside position = box_out_position (within 1.0 m of the man, within 0.5 m of the man-to-rim segment, closer to the rim), or change box_out_position to rule R-EV-20 (closer by at least 0.30 m along the segment).
38. M-FOUL-134: officials' primary coverage areas (lead, trail, centre) exist only as unverified free text in config/vocab/officials_mechanics.yaml lines 34-44. Add them as entries after the CCA manual check that file asks for.

## Appendix A. How it was built (version 0.1.0)

- Research: 9 families of sources (painted and rule landmarks, perimeter, interior, defensive and ball-relative, shot-zone crosswalks, restarts and full court, measurement rules, empirical calibration, repo reconciliation). Each family was followed by a "skeptic": a second agent that recomputed every anchor and opened every cited source (18 agents).
- Synthesis (rewriting each family as entries): every entry got a machine rule, anchors and inside/outside test points, then an independent agent tested it (18 agents).
- Merge: one main `court_region` partition and a `three_depth` label (a decision of the Mac work session). When two families defined the same place, the order of trust was painted > interior > perimeter > defensive > restart > rule > shot-zone > empirical > repo. Losing definitions are kept on each entry as `variants_not_adopted`.
- Verification: 4 scenario testers (man-to-man help, zone slides, presses and full court, restarts) and 4 reviewers (rules book, coaching meaning, data engineering, completeness); 104 fixes applied and every test rerun.

## Appendix B. Loop history

**0.1.0 (2026-10-20, first build).** Research in 9 families, each rechecked by a skeptic; synthesis into entries with exact rules and test points; merge into one main court_region partition; verification by 4 scenario testers and 4 reviewers; 104 fixes applied and every test rerun (Appendix A). Result: 555 entries, 474 with an exact rule.

**0.2.0 (2026-10-20, loop 2).** Eight review lenses, each run by a separate agent:

1. Beyond the state of the art: what the best published tracking work does that we did not.
2. Noise robustness: does a label flicker under about 0.30 m of tracking error?
3. Edge-case adversary: points exactly on lines, broken inputs (NaN, infinity), left-side rays.
4. Cross-spec consistency: does the dictionary agree with the schema, the metrics, the state machine and the ontology?
5. Metric coverage: can every metric in the registry find the spot or zone it needs?
6. Null expressions: which entries written only in words can get an exact rule?
7. Completeness: missing spots and zones.
8. Clarity: can the owner read every label?

Skeptics then challenged every proposed fix: 106 high- and medium-severity fixes were accepted and 25 rejected. The 41 accepted fixes that concern documentation are applied on this page or listed in section 13.

New in 0.2.0:

- Signed distance field (`rule_signed_distance_field`): for every label, how far inside (+) or outside (-) its boundary the player is, the neighbouring region across the nearest boundary, and the time until he crosses it at his current speed.
- Exact circle probability (`rule_probabilistic_membership`): the chance of being inside a circular boundary comes from a closed formula (noncentral chi-square); straight boundaries use the normal curve; everything else uses 1024 fixed random samples.
- Continuous coordinates (`rule_continuous_coordinates`): besides x, y, r and the angles, every object stores d3 (the signed distance behind the three-point line), distances to the sideline, end line and division line, the signed distance to the paint, and the angle to the ball.
- Space control (`rule_space_control`): which player reaches each 10 cm square first, the offence's share of the floor, and an "open" tag for a spot the offence controls for at least 0.20 s.
- Formation slots (`rule_offense_formation_slots`): 5-out, 4-out-1-in, 4-out high and 3-out-2-in templates matched to the five attackers in every frame.
- Learned soft zones (`rule_learned_soft_zones`): 10 shot zones learned once from CBBD team shot maps, then frozen with a version number.
- The `three_offset` scheme: six bands from far inside the arc to a deep three, measured with d3. Other new schemes: rim_radius, rebound_distance, ball_reversal, shot_entry_angle, arc_offset, post_depth.
- Grammar 0.2.0: the exact rules may now use these extra context names: {{CTX_NEW}}. Each is empty when unknown, and the label is then left empty with reason no_context.
- Division-line convention: the frontcourt is y <= 12.700 m (the line's near edge); the painted line itself is backcourt (rule 9-12.2).
- CBBD left/right sign checked on video: four UConn made baskets (2026-10-20) show that CBBD's y axis points to the attacker's left, so the transform negates it.

Result: 599 entries, 515 with an exact rule.

**0.3.0 (2026-10-20, loop 3, convergence round 1).** Five lenses (regressions from loop 2, adversary on the new entries, compute budget, rules-book recheck, completeness) with skeptics. Main fixes: loop 2 had merged alias lists instead of replacing them, so 41 alias phrases had two owners; aliases now replace, and an alias_resolution table gives every ambiguous coaching word one owner (high_post renamed high_post_strip). The restart and full-court layers became multi-label (a player can be in several restart roles at once). The reference evaluator now treats NaN, infinity and positions beyond 100 m as missing. Shot entry depth was added (front of rim, swish band 7-11 in, back of rim, long). This page and the court picture are generated from the YAML.

**0.3.1 (2026-10-20, loop 4, convergence round 2).** Four fresh lenses: regressions 0.2.0 to 0.3.0, property-based random testing (mirror symmetry, monotonicity, partitions, context and height rules), real-world labelling of CBBD shots and common alignments, and doc truth. No geometry or logic defect was found in the main partitions. Fixed: three rule texts still called restart and full court single-winner; a sliver of wide threes just above the corner break got neither corner nor above-the-break; twelve in-court zones owned the boundary lines; the 38-ft coaching-box line now follows the bench side; one alias phrase had two owners; the CBBD encoding entry now records the video-checked sign; stale doc lists removed.

Result: {{N_ENTRIES}} entries, {{N_EXPR}} with an exact rule.
