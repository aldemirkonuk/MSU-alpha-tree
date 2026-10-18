# Ontology gap closures, round 2 (non-rules leaves)

Status: PROPOSAL, 2026-10-18. Nothing here edits the live requirements doc or the existing schema; the requirements session decides. Inputs: `config/game_ontology.yaml` (576 leaves, statuses as of 2026-10-18), `coord/requirements_inbox/007-game-ontology-gaps.md` (first-round proposals), `schema/tables/*.yaml`, `docs/taxonomy/*.md`, `docs/research/load_thresholds.md`, `docs/data/source_field_map.md`, the 2026-27 rules book (local text copy).

Companion files:
- `schema/tables_proposed_changes.yaml`: every added column (table, column, type, unit, range, definition, as-of, requirement IDs), enum additions and the 3 new tables.
- `config/vocab/actions_extra.yaml`: the new action, event and descriptor vocabularies with their measured signatures.

## Scope

All leaves with status partial or missing in domains B, C, D, E, G, H, I, J, L, M, plus two domain-A state leaves the task named (A.04.12 frontcourt status, A.09.02 last touch before out of bounds) and the six non-rules partial leaves in F and K. Excluded because another agent owns rules vocabularies (fouls, signals, violations, shot-clock resets, restarts, officials' mechanics, rules edition, court constants):

- B.01.02 Boundary lines and the out-of-bounds plane: court constants (line widths, marks).
- B.01.03 Centre circle: court constants (centre circle).
- B.01.05 Free-throw lane, line and lane spaces: court constants (lane, lane spaces).
- B.01.09 28-ft throw-in marks and designated spots: court constants (throw-in marks, designated spots).
- B.01.10 Backboard and basket geometry: court constants (backboard and basket geometry).
- B.01.16 Court constants verification status: court constants verification (sign-off).
- E.06.04 Illegal (moving) screens: foul contact types (illegal screen).
- E.08.04 Post dislodging and hook-and-hold: foul contact types (post dislodging, hook-and-hold).

B.01.08 (coaching box) is closed only for the measured coach position; the box geometry is a court constant left to the rules work.

## Conventions used in every definition

- Attacked-rim frame: origin on the floor under the attacked rim centre; x along the baseline, + to the attacker's right; y toward half court; baseline at y = -1.60 m, free-throw line y = 4.19 m, division line y = 12.73 m; r in m and theta in degrees from the right baseline at the rim centre (`src/msu_alpha/geometry.py`). Full-court frame x_fc, y_fc with +y_fc toward the scorers' table (`player_positions.y_fc_m`).
- Pose: COCO-17 body keypoints only (shoulders, elbows, wrists, hips, knees, ankles). No face keypoints, no face data, no speech content. 3-D heights only after R-CG-11 passes; before that, image-plane distances are scaled by 0.24 m / ball diameter in pixels at the ball's depth and rows are flagged `image_scaled`.
- 1.83 m (6 ft) is used as the pressure/contest radius: it is the rules' closely-guarded distance and the distance beyond which defender distance stops changing make probability in Franks et al. 2015.
- Every threshold is a proposed default to be kept in config and re-tuned on labelled data. Evaluation-set sizes marked (proposal) are first-pass sizes, not decisions.
- Requirement IDs continue after the highest new-<FAMILY>-n found in the repo on 2026-10-18; each round-2 requirement names the first-round proposal it refines.

## Summary

- Leaves handled: 69 (68 closed by a specification, 1 cannot be closed by a specification).
- Proposed requirements: 71 (19 Shall, 52 Should).
- Column additions: 185 on existing tables (+ 26 profile_snapshots metric codes); enum additions on 11 existing columns; 3 new tables (runs, fakes, source_definitions).

| Domain | Leaves closed | Requirements |
|---|---|---|
| A Game structure and rules | 2 of 2 | 2 |
| B Court, equipment and venue | 9 of 9 | 9 |
| C Participants | 7 of 7 | 8 |
| D Game state | 5 of 5 | 5 |
| E Individual actions | 17 of 17 | 19 |
| F Group tactics: offence | 5 of 5 | 5 |
| G Group tactics: defence | 3 of 3 | 3 |
| H Outcomes and value | 3 of 3 | 4 |
| I Physical and load | 3 of 3 | 2 |
| J Context | 5 of 6 | 5 |
| K Coaching and decisions | 1 of 1 | 1 |
| L Media and video | 4 of 4 | 5 |
| M Data, quality and governance | 4 of 4 | 3 |

| Family | New requirements |
|---|---|
| AU | 2: new-AU-3, new-AU-4 |
| BL | 1: new-BL-2 |
| CC | 3: new-CC-5, new-CC-6, new-CC-7 |
| CD | 1: new-CD-2 |
| CH | 1: new-CH-2 |
| CO | 1: new-CO-1 |
| CX | 8: new-CX-9, new-CX-10, new-CX-11, new-CX-12, new-CX-13, new-CX-14, new-CX-15, new-CX-16 |
| DF | 5: new-DF-6, new-DF-7, new-DF-8, new-DF-9, new-DF-10 |
| DQ | 3: new-DQ-2, new-DQ-3, new-DQ-4 |
| DS | 1: new-DS-3 |
| DT | 2: new-DT-3, new-DT-4 |
| EV | 9: new-EV-14, new-EV-15, new-EV-16, new-EV-17, new-EV-18, new-EV-19, new-EV-20, new-EV-21, new-EV-22 |
| FD | 2: new-FD-6, new-FD-7 |
| HR | 1: new-HR-2 |
| ID | 1: new-ID-2 |
| MD | 7: new-MD-6, new-MD-7, new-MD-8, new-MD-9, new-MD-10, new-MD-11, new-MD-12 |
| MK | 1: new-MK-20 |
| OS | 1: new-OS-2 |
| PC | 2: new-PC-8, new-PC-9 |
| PL | 4: new-PL-5, new-PL-6, new-PL-7, new-PL-8 |
| RF | 1: new-RF-13 |
| ST | 7: new-ST-9, new-ST-10, new-ST-11, new-ST-12, new-ST-13, new-ST-14, new-ST-15 |
| VI | 4: new-VI-4, new-VI-5, new-VI-6, new-VI-7 |
| VL | 3: new-VL-3, new-VL-4, new-VL-5 |

## Domain A: Game structure and rules

### A.04.12 Frontcourt and backcourt status of team control (was partial)

- **Definition.** Per frame, whether the live ball of the team in control is in that team's frontcourt, using the Rule 9-12.3 location test: a ball touching a player or the floor is in the backcourt if the ball or that player touches the backcourt; a ball in the air keeps the status of its last contact; during a dribble from backcourt to frontcourt the ball gains frontcourt status only when both feet of the dribbler and the ball touch the frontcourt (Rule 9-10 sentence on frontcourt status). The division line belongs to the backcourt (Rule 9-12.2).
- **Signature.** Full-court frame. Division line far edge at x_fc = 0 +/- 0.0254 m (line 0.0508 m wide; the half-width comes from the rules agent's court constant). Ball contact with the floor = ball_states.ball_height_m <= 0.15 m (ball radius 0.12 m + 0.03 m) at a local minimum of height. Player contact = ankle keypoint ground projection (tracked_point ankle_mid per foot). A foot is 'in frontcourt' when its ground point is >= 0.10 m beyond the frontcourt edge of the line; within +/- 0.10 m of the line edge the frame is 'uncertain'. Status flips to frontcourt on the first frame all required contacts are in frontcourt; flips back only on a ball/player contact in the backcourt by the team in control. No team control (state_frame.ball_control_state contested/in flight after a try) -> 'none'.
- **Evidence.** Tracking (ball 3D height, ankle keypoints); PBP backcourt and 10-second violations as checks; broadcast replays never create the status.
- **Lands in.**
  - `state_frame.frontcourt_status` (enum[frontcourt, backcourt, none, uncertain]; range enum; IN_GAME): Rule 9-12.3 location of the live ball for the team in control this frame.
  - `state_frame.frontcourt_established_ts_ms` (int64, ms; range [0, video duration]; IN_GAME): Video time at which the current frontcourt status was established (null while backcourt/none).
  - `state_frame.frontcourt_basis` (enum[ball_floor_contact, ball_player_contact, dribbler_both_feet_and_ball, holder_both_feet, inherited_in_air]; range enum; IN_GAME): Which Rule 9-12.3 / 9-10 clause established the status.
  - `possessions.frontcourt_entry_s` (float32, s; range [0, 30]; IN_GAME): Game-clock seconds from team control to frontcourt status (backcourt count length; null for frontcourt starts).
- **Vocabulary.** frontcourt_basis (actions_extra.yaml: state_tags.frontcourt_basis)
- **new-MD-6 (Shall).** Store per frame the team in control's frontcourt status, the frame it was established and the clause that established it (ball-floor contact, ball-player contact, dribbler both feet and ball, holder both feet, inherited in the air), with a 'uncertain' state when the deciding foot or ball point is within 0.10 m of the division-line edge. *Acceptance:* Status-change time within +/- 0.20 s of gold on >= 95% of 200 labelled backcourt-to-frontcourt crossings (proposal); 'uncertain' <= 5% of crossing frames; every PBP backcourt or 10-second violation shows a status sequence consistent with it (frontcourt -> backcourt, or backcourt for >= 10.0 s of the count). Refines new-SR-3 (inbox 007).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 9-10 (frontcourt status sentence), Rule 9-12.1-3 (local text copy, scratchpad rules.txt lines 3655-3710)

### A.09.02 Player who caused the ball out of bounds (was partial)

- **Definition.** Rule 7-2.1: the last player to touch the ball before it goes out of bounds caused it to go out, unless the ball is out because it touched a player who is out of bounds, in which case that player caused it (7-2.2). A player is out of bounds when he touches the floor on or outside a boundary; an airborne player keeps the status of his last floor contact (7-1.1). The ball is out when it touches anything on or outside a boundary, the backboard supports or back, or passes over the backboard (7-1.2, 7-1.3).
- **Signature.** OOB frame t_oob = ball_states.out_of_bounds_event. Last touch = latest frame t* < t_oob in which a player's nearest wrist keypoint is <= 0.20 m from the ball centre (3D when ball_height_m is available; else image-plane distance scaled by 0.24 m / ball diameter_px) OR the ball's velocity direction changes by >= 20 degrees within 0.15 m of a player's bounding box (deflection). Two different-team players both satisfying the test within 0.10 s of each other -> 'simultaneous' (7-2 and Rule 6 alternating-possession case). Player-out cause: ball-holder's ankle point on or beyond the boundary line inner edge at t_oob.
- **Evidence.** Tracking and pose; PBP 'out of bounds' turnovers and the next possession team as the awarded-team check; coach's-challenge outcomes (coaches_challenges) as gold where present.
- **Lands in.**
  - `restarts.oob_cause` (enum[last_touch, player_out_of_bounds, over_backboard, backboard_support, simultaneous_touch, unknown]; range enum; IN_GAME): Rule 7-1 / 7-2 cause of the out-of-bounds that produced this throw-in (null for other restarts).
  - `restarts.oob_last_touch_player_id` (string; range ESPN athlete ID or local x- ID; IN_GAME): Player who caused the ball to go out (last toucher, or the out-of-bounds player).
  - `restarts.oob_last_touch_ts_ms` (int64, ms; range [0, video duration]; IN_GAME): Video time of the last touch.
  - `restarts.oob_exit_x_fc_m` (float32, m; range [-15.33, 15.33]; IN_GAME): Full-court x where the ball (or the player's foot) first met the boundary.
  - `restarts.oob_exit_y_fc_m` (float32, m; range [-8.62, 8.62]; IN_GAME): Full-court y of the same point.
  - `restarts.oob_call_agrees` (bool; range true/false; IN_GAME): Our last-touch team equals the team the officials charged (the team NOT awarded the throw-in).
- **Vocabulary.** oob_cause (actions_extra.yaml: state_tags.oob_cause)
- **new-BL-2 (Shall).** Every out-of-bounds throw-in row stores the Rule 7-2 cause, the player who caused it, the touch time, the exit point (m) and whether our team-level reading agrees with the call on the floor. *Acceptance:* Awarded team equals PBP on 100% of rows; last toucher correct on >= 90% of 200 labelled out-of-bounds plays (proposal); exit point within 0.30 m of a hand-mapped point on 50 plays; every 'simultaneous_touch' row resolves to an arrow throw-in in PBP. Refines new-BL-1 (inbox 007).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 7-1.1-3, 7-2.1-2 (scratchpad rules.txt lines 2995-3015)

## Domain B: Court, equipment and venue

### B.01.08 Coaching box (head-coach position only) (was missing)

- **Definition.** Where the head coach stands relative to the coaching box. The box geometry itself is a Rule 1-9 court constant handled by the rules/court-constants work (key coaching_box_m); this closure covers only the measured coach position and the time spent outside the box.
- **Signature.** Coach detected as detections.person_class = coach (or bench_events.actor_type head_coach) with identity from the bench side (B.02.07) and the game registry. Floor point = ground projection of the ankle midpoint through the main-camera homography (full-court frame). in_coaching_box = point inside the box polygon expanded by 0.15 m (mapping tolerance). Out-of-box episode = >= 3.0 s continuous outside while the coach is visible.
- **Evidence.** Main camera (coach visible in the near-sideline lower band in roughly half of wide frames); bench and iso camera frames are not mapped.
- **Lands in.**
  - `bench_events.x_fc_m` (float32, m; range [-16.5, 16.5]; IN_GAME): Full-court x of the actor's ankle-midpoint ground point (sideline zone allowed).
  - `bench_events.y_fc_m` (float32, m; range [-10.0, 10.0]; IN_GAME): Full-court y of the same point.
  - `bench_events.in_coaching_box` (bool; range true/false; IN_GAME): Inside the Rule 1-9 box polygon (+0.15 m tolerance).
  - `bench_events.dist_outside_box_m` (float32, m; range [0, 15]; IN_GAME): 0 inside the box; otherwise distance to the nearest box edge.
  - `bench_events.duration_s` (float32, s; range [0, 3600]; IN_GAME): Episode duration for state-type events (standing, out_of_coaching_box).
  - enum addition `bench_events.event_type`: out_of_coaching_box, seated
- **new-CC-5 (Should).** When the head coach is visible on the main camera, store his floor position (m) each second and an out_of_coaching_box event for every continuous stay of >= 3.0 s outside the Rule 1-9 box, with duration (s) and maximum distance outside (m). *Acceptance:* Position within 0.50 m median of hand-mapped points on 50 frames; in/out label agrees with labels on >= 90% of 100 clips (proposal); box geometry read from the court config (no hard-coded constant). Refines new-CC-2 (inbox 007).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 1-9 (coaching box)

### B.01.13 Undefined spots (short corner, one pass away, tag, help position) (was partial)

- **Definition.** Measured definitions for the coaching terms still marked 'to be defined' in config/vocabulary_map.yaml, in the attacked-rim frame (origin under the rim centre, x along the baseline, + to the attacker's right; baseline at y = -1.60 m).
- **Signature.** short_corner: 3.5 < |x| <= 6.0 m and -1.60 <= y <= 1.50 m and r < 6.60 m (disjoint from dunker_spot |x| <= 3.5 and from corner r >= 6.60). passes_away (per offensive player, per frame with a holder): 0 = holder; 1 = the straight segment holder->player is <= 9.0 m long, no other offensive player lies within 1.50 m of that segment, and no defender lies within 0.60 m of it with projection between 20% and 90% of its length; 2 = otherwise. help_position (per defender): >= 1.50 m farther from his man than goal_side requires (dist_to_man_m >= 2.5 m) AND perpendicular distance to the ball-rim line <= 3.0 m. tag (event): a weak-side defender comes within 1.00 m of the screener-roller for >= 0.20 s inside 1.5 s after the screen moment, then is >= 1.50 m away again within 1.5 s. two_side / weak_side keep the existing sign-of-x definitions.
- **Evidence.** Tracking only; coaching labels for agreement tests.
- **Lands in.**
  - `player_positions.passes_away` (int8, count; range {0, 1, 2}; IN_GAME): 0 holder, 1 one pass away, 2 two or more passes away (definition above).
  - `defensive_matchups.help_position` (bool; range true/false; IN_GAME): Defender in help position this second (definition above).
  - `screens.tag_defender_id` (string; range ESPN athlete ID or local x- ID; IN_GAME): Weak-side defender who tagged the roller (null if none).
  - `screens.tag_contact_s` (float32, s; range [0, 3]; IN_GAME): Time the tagger stayed within 1.00 m of the roller.
  - enum addition `player_positions.spot`: short_corner
- **Vocabulary.** spot_terms (actions_extra.yaml) -> to be merged into config/vocabulary_map.yaml by the requirements session
- **new-MD-7 (Shall).** Short corner, one pass away, help position and tag are defined in metres and degrees (values above) in the vocabulary map, and geometry.spot() returns short_corner; passes_away, help_position and the screen tag are stored per frame, second or screen. *Acceptance:* 0 vocabulary entries say 'to be defined'; spot() unit tests on 20 hand-placed points pass; passes_away agrees with coach labels on >= 85% of 300 player-frames and tag with labels on >= 80% of 100 ball screens (proposal). Refines new-MD-1 (inbox 007).
- **Sources.** config/vocabulary_map.yaml; src/msu_alpha/geometry.py (frame definition); docs/taxonomy/defense_full.md (tag, help)

### B.02.02 Game ball model per game (was missing)

- **Definition.** Manufacturer and model of the game ball (Rule 1-16 ball specification), as published by the team, conference or NCAA championship.
- **Signature.** Registry fact, no measurement. 'not_public' when no public statement exists; never inferred from video logos.
- **Evidence.** Conference or championship equipment announcements; team equipment pages.
- **Lands in.**
  - `games.ball_model` (string; range free text or 'not_public'; PRE_GAME): Ball manufacturer and model used.
  - `games.ball_model_source` (string; range URL + checked date; PRE_GAME): Where the ball model was published.
- **new-FD-6 (Should).** Each game row stores the game-ball manufacturer and model with its public source, or 'not_public'. *Acceptance:* Filled (value or 'not_public') for 100% of registered games; every non-'not_public' value has a URL and checked date. Refines new-FD-4 (inbox 007).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 1-16 (ball)

### B.02.07 Team benches and scorers' table side (was missing)

- **Definition.** Which half of the scorers'-table sideline each team's bench occupies, and which basket each team attacks in the first half. The table side is fixed by the full-court frame (+y_fc = scorers'-table side, player_positions.y_fc_m).
- **Signature.** home_bench_end_fc = sign of x_fc of the home bench centre (x_pos / x_neg). Check: bench-class detections (detections.person_class in {bench_player, staff, coach}) with y_fc >= 7.62 m cluster on the declared end for that team (jersey/warm-up colour). First-half attacked basket from the first made field goal's rim.
- **Evidence.** Registry entry before tracking; verified on video.
- **Lands in.**
  - `games.home_bench_end_fc` (enum[x_pos, x_neg, unknown]; range enum; PRE_GAME): End of the table sideline where the home bench sits.
  - `games.home_attacks_first_half_fc` (enum[x_pos, x_neg, unknown]; range enum; IN_GAME): Basket the home team attacks in the first half (full-court frame).
  - `venues.home_bench_end_default_fc` (enum[x_pos, x_neg, unknown]; range enum; REGISTRY): Usual home-bench end at this venue.
- **new-FD-7 (Shall).** Each game stores the home bench end and the home team's first-half attacked basket in the full-court frame before tracking runs; tracking verifies both. *Acceptance:* Filled for 100% of processed games before tracking; bench-person detections fall on the declared end on >= 99% of main-camera frames where bench persons are visible; first-half basket agrees with the first made field goal on 100% of games. Refines new-FD-5 (inbox 007).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 1-21 (team benches), Rule 6-3 (choice of baskets)

### B.02.10 Player equipment (goggles, masks, braces) (was partial)

- **Definition.** Visible protective or supportive equipment worn by a player in a game, recorded only as a re-identification cue. No health or injury inference is made from it.
- **Signature.** Appearance classifier on player crops (>= readable size, R-ID-05), majority vote over the game; one list per player-game.
- **Evidence.** Video only.
- **Lands in.**
  - `appearance_cards.protective_equipment` (list<enum[face_mask, goggles, knee_brace_left, knee_brace_right, knee_sleeve_left, knee_sleeve_right, ankle_brace_visible, wrist_wrap, finger_tape, elbow_pad, none, unresolved]>; range list of enum; IN_GAME): Visible equipment this game (ID cue only).
- **Vocabulary.** protective_equipment (actions_extra.yaml)
- **new-ID-2 (Should).** Appearance cards list visible protective equipment per player-game as an identity tie-breaker only; no load, availability or injury model reads the field. *Acceptance:* Field present on 100% of cards ('none' allowed); item-level agreement >= 85% on 100 labelled player-games (proposal); an import/feature-registry test shows 0 non-ID consumers. Refines new-ID-1 (inbox 007).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 1-26 (player equipment)

### B.02.12 Rim type and stiffness (was missing)

- **Definition.** Rim model per venue where public, plus a measured stiffness proxy: how far rim-contact misses travel.
- **Signature.** rim_rebound_dist_median_m = median distance from the rim centre (m) of the ball's first floor contact or first player touch after a missed field goal with ring contact and no backboard first, over >= 100 such misses at the venue (both baskets pooled; per-basket if >= 100 each). Higher = livelier rim.
- **Evidence.** Public venue/equipment information; tracking of missed shots.
- **Lands in.**
  - `venues.rim_model` (string; range free text or 'unknown'; REGISTRY): Rim manufacturer/model where public.
  - `venues.rim_rebound_dist_median_m` (float32, m; range [0, 10]; PRE_GAME): Stiffness proxy (definition above), recomputed as of each game date.
  - `venues.rim_rebound_n` (int32, count; range [0, 1e5]; PRE_GAME): Misses used for the proxy.
- **new-CX-9 (Should).** Venues store the rim model where public and a rim-liveliness proxy: median rebound distance (m) of ring-contact misses, with its sample size, as of each game date. *Acceptance:* rim_model filled or 'unknown' for every venue; proxy reported only with n >= 100 and a 95% interval; computed from games before the as-of date only. Refines new-CX-1 (inbox 007).

### B.03.04 Other fixed camera positions (was partial)

- **Definition.** Each arena's secondary camera positions (reverse angle, baseline/under-basket, high end, backboard/stanchion, rail, skycam, handheld), as 3-D positions in the full-court frame.
- **Signature.** Camera centre C = (x_fc, y_fc, z) recovered from the frame homography with the focal length (PnP on court keypoints, frames with >= 6 keypoints, R-CG-03). A secondary camera is registered when >= 20 frames of the same camera_view give centres within 1.5 m of their median.
- **Evidence.** Video frames whose court mapping resolves; replays and iso views included for the registry only.
- **Lands in.**
  - `venues.secondary_cameras` (json, m; range list of {camera_view, x_fc_m, y_fc_m, z_m, n_frames, first_seen_game_id}; REGISTRY): Registered secondary cameras with estimated 3-D centres.
- **Vocabulary.** camera_views (actions_extra.yaml)
- **new-VI-4 (Should).** Each venue row lists its secondary cameras with view kind and estimated 3-D centre (m), from frames whose court mapping resolves, so non-main frames can be mapped later. *Acceptance:* Every registered camera has >= 20 supporting frames; centre within 2.0 m of a hand estimate from seating charts or broadcast stills for >= 90% of cameras (proposal). Refines new-VI-1 (inbox 007).

### B.04.04 Student-section location (was missing)

- **Definition.** Which end(s) or sideline the home student section occupies, and whether a free throw or shot is taken facing it.
- **Signature.** Registry value per venue (override per game). A shot or free throw faces the student section when the attacked basket's end (x_fc sign) equals the student-section end.
- **Evidence.** Public seating charts; broadcast crowd frames.
- **Lands in.**
  - `venues.student_section_fc` (enum[x_pos_end, x_neg_end, table_sideline, far_sideline, multiple, none, unknown]; range enum; REGISTRY): Usual student-section location.
  - `games.student_section_fc` (enum[x_pos_end, x_neg_end, table_sideline, far_sideline, multiple, none, unknown]; range enum; PRE_GAME): Override for this game (null = venue default).
  - `free_throws.facing_student_section` (bool; range true/false; IN_GAME): Attacked basket is in front of the home student section.
  - `shots.facing_student_section` (bool; range true/false; IN_GAME): Same, for field-goal attempts.
- **new-CX-10 (Should).** Venues store the home student-section location (override per game) with source, and every shot and free throw is flagged when taken toward it. *Acceptance:* Filled for 100% of processed venues; flags recompute from attacked basket per half on 100% of rows; used by the end-of-floor shooting test (C48). Refines new-CX-2 (inbox 007).

### B.04.05 Court placement (dome midcourt / dome end / arena) (was missing)

- **Definition.** Whether the court sits in a standard arena or in a dome (at midfield or at one end), and how far the first seats or backdrop are behind each basket.
- **Signature.** backdrop_distance = horizontal distance (m) from the end line's outer edge to the first row of seats or the backdrop curtain, behind each basket, from published plans or measured on wide frames.
- **Evidence.** Venue plans; NCAA tournament site information.
- **Lands in.**
  - `venues.court_placement` (enum[standard_arena, dome_midfield, dome_end, other]; range enum; REGISTRY): Court placement class.
  - `venues.backdrop_distance_x_pos_m` (float32, m; range [0, 80]; REGISTRY): Distance from the x_pos end line to the first seats/backdrop.
  - `venues.backdrop_distance_x_neg_m` (float32, m; range [0, 80]; REGISTRY): Same behind the x_neg basket.
- **new-CX-11 (Should).** Venue rows store court placement and the backdrop distance behind each basket (m). *Acceptance:* Filled for every NCAA-tournament and neutral venue processed; distances within 5 m of published plans where plans exist. Refines new-CX-3 (inbox 007).

## Domain C: Participants

### C.01.14 NIL valuation (public estimates) (was partial)

- **Definition.** A publicly reported or estimated NIL valuation of a player, stored with its provenance; exploratory context only.
- **Signature.** Registry fact; kind = estimate (third-party model) or reported (stated by the player/collective/team).
- **Evidence.** Public web pages only.
- **Lands in.**
  - `player_card_template.nil_source` (string; range URL; PRE_GAME): Where the valuation was published.
  - `player_card_template.nil_as_of_date` (date; range YYYY-MM-DD; PRE_GAME): Publication date of the value.
  - `player_card_template.nil_kind` (enum[estimate, reported]; range enum; PRE_GAME): Estimate vs reported.
- **new-PC-8 (Should).** NIL values on player cards carry source URL, publication date and kind (estimate/reported) and are excluded from every model feature set until a registered hypothesis names them. *Acceptance:* 100% of non-null NIL values have all three fields; feature-registry test shows 0 model inputs using NIL without a registered hypothesis ID. Refines new-PC-6 (inbox 007).

### C.01.17 Captain (was partial)

- **Definition.** Player designated captain for the season (team announcement) or for the game (the player at the pre-game captains' meeting, Rule 3-3).
- **Signature.** Registry fact; per game optionally from the pre-game meeting on video.
- **Evidence.** Team roster pages and game notes.
- **Lands in.**
  - `rosters.captain` (enum[season_captain, not_captain, unknown]; range enum; PRE_GAME): Season captain designation.
  - `rosters.captain_source` (string; range URL + checked date; PRE_GAME): Source of the designation.
  - `player_game_context.game_captain` (bool; range true/false; IN_GAME): Acted as captain in this game (where shown).
- **new-PC-9 (Should).** Rosters store each player's season captain designation with source, and player-game context the game captain where visible. *Acceptance:* Filled ('unknown' allowed) for 100% of rostered players; every 'season_captain' has a source URL. Refines new-PC-7 (inbox 007).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 3-3 (captain)

### C.02.03 Bench personnel list per game (was partial)

- **Definition.** Counts of bench personnel by role per team-game (Rule 4-3/4-4 bench personnel), with no names beyond public staff lists.
- **Signature.** Counts from the official box/game notes where given; else from a broadcast bench frame count (persons in team apparel on the bench, person_class staff/coach), labelled source = video.
- **Evidence.** Box score staff lines, team staff directories, video.
- **Lands in.**
  - `team_game_context.bench_personnel_counts` (json, count; range map role -> int; IN_GAME): Counts per role (vocabulary bench_roles).
  - `team_game_context.bench_personnel_source` (enum[official, team_directory, video, unknown]; range enum; IN_GAME): Basis of the counts.
- **Vocabulary.** bench_roles (actions_extra.yaml)
- **new-CC-6 (Should).** Each team-game stores bench personnel counts by role (head coach, assistants, trainers, managers, other staff, uniformed non-playing players) with the basis of the count. *Acceptance:* Filled or 'unknown' for 100% of processed team-games; video-based counts within +/- 1 person of a hand count on 20 games (proposal). Refines new-CC-3 (inbox 007).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 4-3, 4-4 (bench personnel)

### C.03.03 Official experience and assignment level (was partial)

- **Definition.** For each official as of a game date: games worked this season and in total (in our D-I PBP data), seasons seen, distinct conferences worked, postseason games worked.
- **Signature.** Counts over game_officials rows with games.tip_scheduled_utc < as-of date; conference = home team's conference for conference games, else 'non_conf'.
- **Evidence.** PBP officials lists (game_officials).
- **Lands in.**
  - `profile_snapshots.metric_code` add: ref_games_season_asof, ref_games_total_asof, ref_seasons_seen_asof, ref_conferences_worked_asof, ref_postseason_games_asof. Official experience metrics (entity_type = official).
- **new-RF-13 (Should).** Official profile snapshots hold games worked this season and in total, seasons seen, conferences worked and postseason games, as of each game date, from D-I PBP officials lists. *Acceptance:* Recomputes from game_officials; leakage test shows 0 games on or after the as-of date counted; values equal a hand count for 5 officials. Refines new-RF-12 (inbox 007).

### C.04.01 Official scorer and scorebook authority (was partial)

- **Definition.** Rule 2-9: the official scorebook governs; when our state record disagrees with the official record after review, the official record wins and the disagreement is logged.
- **Signature.** Final score, team fouls per half, player fouls and timeouts used compared with the official box/PBP at game end; any difference creates a state_corrections row with correction_source = official_record.
- **Evidence.** Official box score and PBP.
- **Lands in.**
  - `games.official_record_reconciled` (bool; range true/false; POST_GAME): All end-of-game counts equal the official record after corrections.
  - enum addition `state_corrections.correction_source`: official_record
- **new-DQ-2 (Shall).** At game end, final score, team fouls per half, player fouls and timeouts in our state record are reconciled to the official record; each disagreement becomes a correction whose source is the official record. *Acceptance:* After reconciliation the four counts equal the official record on 100% of processed games; every applied correction links to a scoreboard flag or review. Refines new-IV-33 (config/invariants.yaml).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 2-9 (scorers)

### C.04.04 Home stat crew bias (and M.03.06 known-bias register) (was partial)

- **Definition.** Systematic over- or under-crediting of judgement stats (assists, blocks, steals, rebounds credited to teams vs players) by the home stat crew. Measured as the gap between officially credited and video-derived events for the same plays, by venue.
- **Signature.** Assist: official assist on a made FG vs video assist (passes.is_official_assist vs assister_video_id under our rule: last pass, catch-to-release <= 2.0 s or <= 2 dribbles). crew_assist_gap(venue) = (official assists - video assists) / made FGs with a visible prior pass, for home and away teams, with 95% interval; same for blocks (official vs video blocked shots) and steals. The known-bias register (config/bias_register.yaml) has one row per bias with field, direction, measured effect, correction or flag, evidence.
- **Evidence.** Official PBP vs our video events; literature on home-crew assist inflation (FiveThirtyEight Huntsville article, not opened -> unverified).
- **Lands in.**
  - `shots.assist_official_vs_video` (enum[agree_assisted, agree_unassisted, official_only, video_only, not_visible]; range enum; IN_GAME): Agreement of the official assist with our video assist on a made FG.
  - `venues.crew_assist_gap` (float32, share; range [-1, 1]; PRE_GAME): Official minus video assists per made FG with a visible pass, as of date.
  - `venues.crew_block_gap` (float32, share; range [-1, 1]; PRE_GAME): Official minus video blocks per FGA, as of date.
  - `venues.crew_steal_gap` (float32, share; range [-1, 1]; PRE_GAME): Official minus video steals per opponent turnover, as of date.
- **Vocabulary.** bias_register rows (actions_extra.yaml: bias_register_seed)
- **new-DQ-3 (Shall).** A known-bias register lists each known source bias (listed heights, home-crew assists, blocks and steals, shot-location entry, substitution timing) with affected field, direction, measured size, correction or flag and evidence, and every affected column references its register row. *Acceptance:* Register has >= 5 rows; 100% of affected columns in schema/tables reference a row; register validated by the ontology check. Refines new-DQ-1 (inbox 007).
- **new-DQ-4 (Should).** Per venue, measure the home stat crew's assist, block and steal gap against video-derived events, with a 95% interval, and flag venues whose gap interval excludes 0. *Acceptance:* Gap reported for every venue with >= 150 made FGs with a visible prior pass; video assist rule fixed before measuring; intervals by bootstrap over games.
- **Sources.** https://fivethirtyeight.com/features/its-easier-to-get-assists-in-huntsville-texas-than-anywhere-else (search result only, not opened: unverified)

### C.05.03 Crowd allegiance share (neutral sites) and crowd reaction (was partial)

- **Definition.** Estimated share of the crowd supporting each team at a neutral site, plus an audio check: how much louder the arena reacts to each team's made baskets.
- **Signature.** crowd_share_est = model on log campus-to-venue distance (km), enrollment, conference footprint and historic travel; 80% interval. audio_make_reaction_db(team) = mean over the team's made FGs of (max 1-s loudness_rel_db in [t_make, t_make + 3 s]) - (median loudness_rel_db over [t_make - 10 s, t_make - 1 s]); asymmetry = team A minus team B (dB). Commentary-active seconds are excluded when commentary energy dominates (audio_seconds.commentary_active and voice-band share > 0.6).
- **Evidence.** Audio of the broadcast; distances from team_game_context.
- **Lands in.**
  - `team_game_context.crowd_share_est` (float32, share; range [0, 1]; PRE_GAME): Estimated crowd share for this team (neutral sites).
  - `team_game_context.crowd_share_ci80` (json, share; range [lo, hi]; PRE_GAME): 80% interval.
  - `team_game_context.audio_make_reaction_db` (float32, dB; range [-20, 40]; POST_GAME): Mean crowd reaction to this team's makes (definition above).
- **new-CX-12 (Should).** For every neutral-site game, estimate each team's crowd share with an 80% interval and measure the crowd's reaction to each team's made baskets from audio (dB), so the estimate can be validated. *Acceptance:* Estimate with interval on 100% of neutral-site games; audio reaction measured where audio exists; rank correlation between share and reaction asymmetry reported on >= 30 games (C69). Refines new-CX-4 (inbox 007).
- **Sources.** https://arxiv.org/abs/2210.13687 (Pelechrinis 2022: home-team refereeing bias in the NBA declined after COVID-19; crowd mechanism not established)

## Domain D: Game state

### D.01.03 Lead changes, ties and largest lead (was partial)

- **Definition.** Lead change = a score event after which the leading team differs from the last team that held a lead (ties do not reset the last leader). Tie = a score event after which the margin is 0 (the 0-0 start is not counted). Largest lead = maximum positive margin for each team so far.
- **Signature.** Recomputed from score_events in order; state_second carries running counts.
- **Evidence.** Score events; ESPN 'leadChanges' (78% of Job D box rows) and team_box.largest_lead as checks.
- **Lands in.**
  - `state_second.times_tied` (int16, count; range [0, 100]; IN_GAME): Ties so far (definition above).
  - `state_second.largest_lead_msu` (int16, points; range [0, 100]; IN_GAME): MSU's largest lead so far.
  - `state_second.largest_lead_opp` (int16, points; range [0, 100]; IN_GAME): Opponent's largest lead so far.
- **new-MD-8 (Should).** Score state carries times tied and each team's largest lead as of each second, with lead changes counted only when the leader differs from the last leader. *Acceptance:* End-of-game values equal ESPN leadChanges and team_box.largest_lead on 100% of games where published (differences logged with the source's definition). Refines new-MD-2 (inbox 007).
- **Sources.** docs/data/source_field_map.md section 1.2 (Job D box fields leadChanges, largestLead)

### D.01.05 Run events (was partial)

- **Definition.** Strict run: a maximal sequence of consecutive score events by one team totalling >= 8 points with no opponent points, ended by the next opponent score or period end. Register run: a maximal game-clock window of <= 120 s in which one team's net points are >= 8 (beliefs register definition). Both kept side by side.
- **Signature.** Recomputed from score_events; timeouts during the run and the ending event recorded.
- **Evidence.** Score events; timeouts.
  - new table `runs` (one row per run per definition): game_id (string), run_id (string), definition_code (enum[strict_unanswered_8, register_net8_120s]), team_id (string), start_score_event_id (string), end_score_event_id (string), start_game_clock_s (float32, s), end_game_clock_s (float32, s), duration_s (float32, s), pts_for (int16, points), pts_against (int16, points), timeouts_during (int8, count), ended_by (enum[opponent_score, period_end, game_end, window_expired])
- **Vocabulary.** run_definitions (actions_extra.yaml)
- **new-MD-9 (Shall).** Runs are stored under both definitions (strict unanswered >= 8 points; net >= 8 within 120 s game clock) with start and end score events, points for and against, timeouts during and the ending cause. *Acceptance:* Runs recompute identically from score_events (bit-equal on re-run); every run has an ending cause; counts per game per definition reported. Refines new-EV-5 (inbox 007).
- **Sources.** docs/research/beliefs_register.md (run definition)

### D.01.06 Scoring droughts (was missing)

- **Definition.** Game-clock seconds since each team's last made field goal and last point of any kind; a drought event when a team goes >= 240 s of game clock without a field goal.
- **Signature.** Running counters from score_events in game-clock time; carried across half time (flag carried = true in the first second of a new period).
- **Evidence.** Score events.
- **Lands in.**
  - `state_second.secs_since_fg_msu` (float32, s; range [0, 2400]; IN_GAME): Game-clock seconds since MSU's last made FG.
  - `state_second.secs_since_fg_opp` (float32, s; range [0, 2400]; IN_GAME): Same for the opponent.
  - `state_second.secs_since_point_msu` (float32, s; range [0, 2400]; IN_GAME): Since MSU's last point (FG or FT).
  - `state_second.secs_since_point_opp` (float32, s; range [0, 2400]; IN_GAME): Same for the opponent.
- **new-MD-10 (Should).** Every second carries game-clock seconds since each team's last made field goal and last point, carried across period breaks. *Acceptance:* Recomputes from score_events within 0.1 s; values carried across half time are flagged; drought counts (>= 240 s) per game reported. Refines new-MD-3 (inbox 007).

### D.02.04 Garbage time (was partial)

- **Definition.** Possessions whose result cannot plausibly change, under named definitions stored side by side: (1) source flag (hoopR NCAA is_garbage_time); (2) CTG-adapted: Cleaning the Glass's NBA rule (4th quarter only; lead >= 25 with 12:00-9:00 left, >= 20 with 9:00-6:00, >= 10 under 6:00; no more than two starters on the floor combined), applied to the last 12:00 of the second half (our adaptation, flagged); (3) win-probability rule: pre-possession win probability >= 0.98 or <= 0.02 with <= 300 s left in regulation.
- **Signature.** All inputs already stored: possessions.margin_start, start_game_clock_s, start_period, pre_win_prob, lineup keys with player_box.starter.
- **Evidence.** Derived; CTG definition opened.
- **Lands in.**
  - `possessions.garbage_time_ctg_adapted` (bool; range true/false; IN_GAME): Definition (2).
  - `possessions.garbage_time_wp` (bool; range true/false; IN_GAME): Definition (3).
  - `possessions.starters_on_floor_total` (int8, count; range [0, 10]; IN_GAME): Starters on the floor, both teams.
- **Vocabulary.** garbage_time_definitions (actions_extra.yaml)
- **new-MD-11 (Should).** Each possession stores garbage-time flags under the source definition, the CTG-adapted margin/time/starters rule and the win-probability rule; no rows are ever dropped by them. *Acceptance:* All three flags present on every possession; per-game share under each definition reported; CTG thresholds read from config with the source URL. Refines new-MD-4 (inbox 007).
- **Sources.** https://cleaningtheglass.com/stats/guide/garbage_time (opened 2026-10-18)

### D.07.04 Lineup composition descriptors (was missing)

- **Definition.** Size, position mix, shooting, ball handling and experience of each five-man unit, as of the game date, for both teams and their differences.
- **Signature.** From rosters (listed_height_cm, listed_position, class_year) and as-of profile snapshots: big = listed C, or listed F with listed height >= 206 cm; shooter = >= 50 D-I 3PA before the game date and shrunk 3P% >= 0.33 (beta prior on position group); ball handler = as-of assist rate >= 20% or tracked share of the team's backcourt-to-frontcourt ball advances >= 25%. Archetype by rules in actions_extra.yaml lineup_archetypes.
- **Evidence.** Rosters (listed heights carry the known listed-height bias, register row); profile snapshots.
- **Lands in.**
  - `lineup_stints.mean_height_cm` (float32, cm; range [170, 230]; IN_GAME): Mean listed height on the floor.
  - `lineup_stints.max_height_cm` (float32, cm; range [170, 235]; IN_GAME): Tallest listed height.
  - `lineup_stints.min_height_cm` (float32, cm; range [160, 230]; IN_GAME): Shortest listed height.
  - `lineup_stints.height_diff_cm` (float32, cm; range [-40, 40]; IN_GAME): Mean height minus opponent lineup's mean height.
  - `lineup_stints.n_listed_g` (int8, count; range [0, 5]; IN_GAME): Players listed G.
  - `lineup_stints.n_listed_f` (int8, count; range [0, 5]; IN_GAME): Players listed F.
  - `lineup_stints.n_listed_c` (int8, count; range [0, 5]; IN_GAME): Players listed C.
  - `lineup_stints.n_bigs` (int8, count; range [0, 5]; IN_GAME): Bigs (definition above).
  - `lineup_stints.n_shooters_asof` (int8, count; range [0, 5]; IN_GAME): Shooters as of the game date.
  - `lineup_stints.n_ball_handlers_asof` (int8, count; range [0, 5]; IN_GAME): Ball handlers as of the game date.
  - `lineup_stints.mean_class_year` (float32, years; range [1, 6]; IN_GAME): Mean class year (1 = freshman).
  - `lineup_stints.archetype` (enum[five_out, one_big, two_big, jumbo, small, three_guard, other]; range enum; IN_GAME): Lineup archetype.
- **Vocabulary.** lineup_archetypes (actions_extra.yaml)
- **new-MD-12 (Should).** Each lineup stint stores composition descriptors for its five players (mean, max and min listed height in cm, height difference to the opponent unit, listed-position counts, bigs, shooters and ball handlers as of the game date, mean class year, archetype). *Acceptance:* Filled on 100% of stints with five known players; recomputes from rosters and as-of snapshots; leakage test shows 0 post-tip inputs. Refines new-MD-5 (inbox 007).
- **Sources.** docs/data/source_field_map.md section 1.7 (EvanMiya lineup colour fields height_mean etc., reference only)

## Domain E: Individual actions

### E.01.02 Defensive slide, backpedal and crossover run (was partial)

- **Definition.** Movement primitives classified by the angle between the movement heading and the torso facing: forward run, lateral slide (feet do not cross), crossover run (lateral with feet crossing), backpedal.
- **Signature.** d = wrap(heading_deg - torso_facing_deg) in the same frame. forward |d| <= 45; lateral 45 < |d| < 135; backward |d| >= 135. Segment = >= 0.40 s continuous in one class at speed >= 0.5 m/s. Lateral segments split: crossover_run if the left/right ankle order along the movement direction swaps >= 1 time in the segment, else defensive_slide. Stored with mean and peak speed (m/s) and duration (s).
- **Evidence.** Tracking + pose (torso facing from the shoulder and hip keypoints, R-DT-10).
- **Lands in.**
  - `movement_primitives.dir_rel_torso_deg` (float32, degrees; range [-180, 180]; IN_GAME): Mean heading minus torso facing over the segment.
  - enum addition `movement_primitives.primitive_type`: forward_run, defensive_slide, crossover_run, backpedal
- **Vocabulary.** movement_direction_classes (actions_extra.yaml)
- **new-ST-9 (Shall).** Movement primitives include forward run, defensive slide, crossover run and backpedal, classified from heading minus torso facing (45/135-degree edges) with ankle-crossing for crossover runs, each with mean and peak speed (m/s) and duration (s). *Acceptance:* F1 >= 0.80 per class on >= 50 labelled segments each (proposal); torso-facing error <= 20 degrees median (R-DT-10); segments shorter than 0.40 s never stored. Refines new-ST-2 (inbox 007).
- **Sources.** https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/ (Tuttle et al. 2024: recommends reporting movement direction; via docs/research/load_thresholds.md)

### E.01.03 Jumps (and I.02.06 jump load) (was partial)

- **Definition.** A jump = both feet off the floor for >= 0.10 s. Stored with takeoff foot pattern, purpose and height.
- **Signature.** Airborne when both ankle points are >= 0.05 m above the floor plane (3-D) or player_positions.airborne. Flight time t_f = landing frame - takeoff frame (s); height h = 9.81 * t_f^2 / 8 (m; flight-time method). Takeoff pattern: one_foot if the two ankles leave the floor > 0.08 s apart, else two_feet. Purpose: shot (release inside the flight), rebound (ball within 1.0 m of a wrist at the apex after ring/board contact), block_or_contest (defender within 1.83 m of a shooter whose release falls inside the flight), tip (ball touched in flight within 1.0 m of the rim), pass, other. High jump = h >= 0.40 m (the most common basketball high-intensity jump threshold).
- **Evidence.** Tracking + pose; frame rate limits flight-time precision (1 frame = 0.033-0.040 s).
- **Lands in.**
  - `movement_primitives.flight_time_s` (float32, s; range [0.10, 1.20]; IN_GAME): Jump flight time.
  - `movement_primitives.jump_height_m` (float32, m; range [0, 1.30]; IN_GAME): 9.81 * t_f^2 / 8.
  - `movement_primitives.takeoff_pattern` (enum[one_foot, two_feet, unresolved]; range enum; IN_GAME): Takeoff.
  - `movement_primitives.jump_purpose` (enum[shot, rebound, block_or_contest, tip, pass, other]; range enum; IN_GAME): Purpose.
  - `profile_snapshots.metric_code` add: jumps_per_min, high_jumps_per_min (h >= 0.40 m). Jump load per minute played.
  - enum addition `movement_primitives.primitive_type`: jump
- **Vocabulary.** jump_purposes (actions_extra.yaml)
- **new-PL-5 (Should).** Jumps are stored as movement primitives with flight time (s), flight-time height (m), takeoff pattern and purpose, and player profiles report jumps and high jumps (>= 0.40 m) per minute played. *Acceptance:* Jump recall >= 90% and precision >= 90% on 200 labelled jumps (proposal); flight time within +/- 2 frames of gold; height reported only where 3-D foot heights pass R-CG-11, error <= 0.10 m on hand-measured jumps. Refines new-PL-1 (inbox 007).
- **Sources.** https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/ (jumps > 40 cm high-intensity in 10 studies; via load_thresholds.md)

### E.01.04 Stops, pivots, first step and plant foot (with E.01.05 gather and pre-dribble cues) (was partial)

- **Definition.** Per touch: how the player stopped on the catch (jump stop, stride stop), which foot became the pivot, the direction and kind of the first step, the number of steps in the gather, and whether the pivot foot appears to lift before the ball leaves the hand on the first dribble (flag only; we never call violations).
- **Signature.** Jump stop: both feet land within 0.10 s of each other after an airborne catch or gather. Stride stop: feet land one after the other 0.15-0.60 s apart. Pivot foot: the foot whose ankle point moves <= 0.10 m while the other moves >= 0.25 m during the hold. First step: first displacement >= 0.30 m of the non-pivot foot; direction (degrees) relative to the player->rim vector; kind direct (same side as the step foot), crossover_step (across the body), jab (returns within 0.6 s), drop_step (back toward the baseline with the back to the rim), none. Pre-dribble lift suspected: pivot ankle rises >= 0.05 m or moves >= 0.15 m before the ball leaves the hand on the first dribble.
- **Evidence.** Pose (ankles, wrists) and ball tracking. 2026-27 point of emphasis on gather/travel (flag only).
- **Lands in.**
  - `touches.stop_type` (enum[jump_stop, stride_stop, none, unresolved]; range enum; IN_GAME): Stop on the catch or gather.
  - `touches.pivot_foot` (enum[left, right, none, unresolved]; range enum; IN_GAME): Pivot foot during the hold.
  - `touches.first_step_kind` (enum[direct, crossover_step, jab, drop_step, none, unresolved]; range enum; IN_GAME): First step kind.
  - `touches.first_step_dir_deg` (float32, degrees; range [-180, 180]; IN_GAME): First-step direction relative to the player->rim vector.
  - `touches.gather_steps` (int8, count; range [0, 4]; IN_GAME): Foot contacts between gather and release/first dribble.
  - `touches.pre_dribble_lift_suspected` (bool; range true/false; IN_GAME): Pivot lifted before the first dribble left the hand (flag only).
- **Vocabulary.** footwork (actions_extra.yaml)
- **new-DT-3 (Should).** Each touch stores stop type, pivot foot, first-step kind and direction (degrees from the player->rim vector) and gather step count from pose. *Acceptance:* Precision >= 80% on 200 labelled touches (as R-DT-16); pivot foot correct >= 85%; direction within 20 degrees median (proposal). Refines new-DT-1 (inbox 007).
- **new-DT-4 (Should).** Each touch that starts a dribble from a hold flags a suspected pivot lift before the ball leaves the hand, as a count of possible travels; it never creates a violation row. *Acceptance:* Flag agrees with frame-by-frame gold on >= 80% of 200 labelled starts (proposal); 0 turnovers or violations created from the flag. Refines new-DT-2 (inbox 007).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 4 (pivot, traveling definitions), Points of Emphasis 5 (gather)

### E.01.05 Gather and pre-dribble travel cues (was missing)

Closed together with E.01.04; requirement(s): new-DT-4.

### E.01.06 Change of direction (was partial)

- **Definition.** A heading change of >= 45 degrees completed within 0.5 s at an entry speed of >= 3.0 m/s, with exit speed and recovery time.
- **Signature.** Heading from smoothed velocity. Entry speed = mean speed over [t0 - 0.3 s, t0]; exit speed = mean over [t1, t1 + 0.3 s]; recovery_s = time from t1 until speed regains 90% of entry speed (null if not within 2.0 s). Classes: cut_45_90 (45-90 degrees), reversal_gt90 (> 90; the threshold used by Irid et al. 2025). Only where speed RMSE checks pass (load_thresholds.md section 7).
- **Evidence.** Tracking.
- **Lands in.**
  - `movement_primitives.heading_change_deg` (float32, degrees; range [45, 180]; IN_GAME): Absolute heading change.
  - `movement_primitives.entry_speed_mps` (float32, m/s; range [3.0, 10]; IN_GAME): Entry speed.
  - `movement_primitives.exit_speed_mps` (float32, m/s; range [0, 10]; IN_GAME): Exit speed.
  - `movement_primitives.recovery_s` (float32, s; range [0, 2.0]; IN_GAME): Time to regain 90% of entry speed.
  - enum addition `movement_primitives.primitive_type`: cod_45_90, cod_reversal_gt90
- **new-PL-6 (Should).** Changes of direction (>= 45 degrees within 0.5 s at entry speed >= 3.0 m/s) are stored with heading change, entry and exit speed (m/s) and recovery time (s), split at 90 degrees. *Acceptance:* Recomputes from smoothed tracks; count per minute reported with coverage (R-PL-05); detection agrees with labels on >= 85% of 100 labelled cuts (proposal). Refines new-PL-2 (inbox 007).
- **Sources.** https://pmc.ncbi.nlm.nih.gov/articles/PMC12490299/ (Irid et al. 2025, change of direction > 90 degrees; via load_thresholds.md)

### E.01.08 Landing space of jump shooters (was missing)

- **Definition.** Whether a defender occupies the area where a jump shooter will land (2026-27 point of emphasis 7; Appendix VIII 'landing space').
- **Signature.** Takeoff point P0 = shooter's ankle-midpoint ground point at takeoff; landing point P1 = same at first floor contact after release. landing_def_dist_m = minimum over defenders of the distance from P1 to the defender's nearest ankle point at the landing frame. Encroachment = a defender's ankle point within 0.60 m of P1 at landing AND that defender's point was > 0.60 m from P1 at takeoff (he moved into the space).
- **Evidence.** Tracking + pose; fouls on the play from PBP for comparison only.
- **Lands in.**
  - `shots.landing_x_m` (float32, m; range [-8.62, 8.62]; IN_GAME): Landing point x (attacked-rim frame).
  - `shots.landing_y_m` (float32, m; range [-2.60, 28.05]; IN_GAME): Landing point y.
  - `shots.landing_drift_m` (float32, m; range [0, 3]; IN_GAME): |P1 - P0|.
  - `shots.landing_def_dist_m` (float32, m; range [0, 15]; IN_GAME): Nearest defender foot to P1 at landing.
  - `shots.landing_space_encroached` (bool; range true/false; IN_GAME): Encroachment test above (flag only).
- **new-DF-6 (Should).** For every jump shot, store the shooter's landing point, drift (m), the nearest defender's foot distance to the landing point at landing (m) and an encroachment flag; the flag never creates a foul. *Acceptance:* Landing point within 0.30 m of gold on 100 labelled jump shots (proposal); encroachment flag agrees with labels >= 85%; 0 fouls created from it. Refines new-DF-1 (inbox 007).
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Points of Emphasis 7, Appendix VIII (landing space)

### E.02.04 Other dribble moves (was partial)

- **Definition.** Adds in-and-out, push (speed) dribble, pound (control) dribble, snatch-back and half spin to the dribble-move vocabulary.
- **Signature.** Signatures per move in actions_extra.yaml dribble_moves_extra (ball and wrist trajectories, handler speed, heading change).
- **Evidence.** Pose + ball tracking.
  - enum addition `dribbles.move_type`: in_and_out, push, pound, snatch_back, half_spin
- **Vocabulary.** dribble_moves_extra (actions_extra.yaml)
- **new-EV-14 (Should).** The dribble-move vocabulary adds in-and-out, push, pound, snatch-back and half spin, each with the measured signature in the action vocabulary. *Acceptance:* >= 75% correct on 300 labelled moves including >= 30 of each new class (as R-EV-05). Refines new-EV-6 (inbox 007).

### E.02.06 Fakes (shot fake, pass fake, jab step, others) (was missing)

- **Definition.** A deceptive movement by the ball holder that simulates a shot, pass or drive without completing it, with the guarding defender's reaction and the value change after it.
- **Signature.** shot_fake: ball centre rises >= 0.30 m within <= 0.60 s from below the holder's shoulder line to at or above it (shooting pocket), no release, the ball then lowers >= 0.20 m or a dribble/pass starts within 1.0 s; holder's feet stay on the floor. jump_fake: same with the holder airborne (flag; any subsequent violation is the officials' call). pass_fake: a wrist moves >= 0.35 m away from the torso centre within <= 0.40 s with the ball, direction within 20 degrees of a teammate's bearing, no release, wrist returns >= 0.20 m within 0.50 s. jab_step: non-pivot foot moves >= 0.30 m and its ankle returns within 0.20 m of its start within 0.60 s, ball held, no dribble. rocker_step: jab followed within 0.6 s by a second step of the same foot back past the start (>= 0.30 m). head_or_shoulder_fake: shoulder-line rotation >= 25 degrees and return within 0.5 s with no step (lower confidence). Defender reaction (on-ball defender, window 0.0-0.40 s after the fake's peak): left_feet (ankles >= 0.05 m off the floor), rose (pelvis up >= 0.10 m or both wrists above shoulders), shifted (pelvis moves >= 0.20 m in the fake's direction), closed_out (moved >= 0.30 m toward the holder), no_reaction. value_delta = possession value 1.0 s after the fake minus at the fake start (xpts).
- **Evidence.** Pose (wrists, shoulders, ankles) and ball 3-D height.
  - new table `fakes` (one row per fake): game_id (string), fake_id (string), touch_id (string), possession_id (string), player_id (string), kind (enum[shot_fake, jump_fake, pass_fake, jab_step, rocker_step, head_or_shoulder_fake]), ts_ms (int64, ms), ball_rise_m (float32, m), foot_disp_m (float32, m), direction_deg (float32, degrees), defender_id (string), defender_reaction (enum[left_feet, rose, shifted, closed_out, no_reaction, not_visible]), reaction_latency_s (float32, s), next_action (enum[shot, drive, pass, dribble_hold, another_fake, turnover, foul_drawn]), value_delta (float32, xpts)
- **Vocabulary.** fakes, defender_reactions (actions_extra.yaml)
- **new-EV-15 (Shall).** Fake events (shot fake, jump fake, pass fake, jab step, rocker step, head/shoulder fake) are detected with the measured signatures in the action vocabulary and stored with touch, player, time and direction. *Acceptance:* Recall >= 80% and precision >= 80% on 200 labelled fakes, per kind with >= 30 examples (proposal); head/shoulder fakes reported separately. Refines new-EV-7 (inbox 007).
- **new-EV-16 (Should).** Each fake stores the on-ball defender's reaction (left feet, rose, shifted, closed out, none), its latency (s), the next action within 1.5 s and the value change after 1.0 s. *Acceptance:* Reaction class correct >= 80% on 200 labelled fakes; latency within +/- 2 frames; value change recomputes from possession_value.

### E.03.06 Pass delivery (was missing)

- **Definition.** How the pass was delivered: hands, from a hold / off the dribble / one-touch, release height, and whether it was a no-look pass.
- **Signature.** two_handed: both wrists within 0.25 m of the ball centre at release; one_handed otherwise. Delivery: off_dribble = release <= 0.30 s after the last dribble contact with no hold > 0.30 s; one_touch = catch-to-release <= 0.30 s; from_hold otherwise. No-look proxy: the upper-torso normal (perpendicular to the shoulder line, pointing forward) differs from the pass direction by > 60 degrees at release; flagged no_look_torso. True head yaw would need face keypoints, which the project does not store or use, so the torso proxy under-counts passes where only the head turns.
- **Evidence.** Pose (wrists, shoulders) and ball tracking.
- **Lands in.**
  - `passes.hands` (enum[one, two, unresolved]; range enum; IN_GAME): Hands at release.
  - `passes.delivery` (enum[from_hold, off_dribble, one_touch, unresolved]; range enum; IN_GAME): Delivery.
  - `passes.release_height_m` (float32, m; range [0, 3.5]; IN_GAME): Ball height at release.
  - `passes.torso_to_pass_angle_deg` (float32, degrees; range [0, 180]; IN_GAME): Angle between upper-torso normal and pass direction at release.
  - `passes.no_look_torso` (bool; range true/false; IN_GAME): torso_to_pass_angle_deg > 60.
- **Vocabulary.** pass_delivery (actions_extra.yaml)
- **new-EV-17 (Should).** Each pass stores hands, delivery (from hold, off the dribble, one-touch), release height (m) and a torso-based no-look flag (angle > 60 degrees), without face keypoints. *Acceptance:* >= 80% correct on 300 labelled passes where the passer is at readable size (R-ID-05); release height within 0.20 m once R-CG-11 passes. Refines new-EV-8 (inbox 007).

### E.03.07 Throw-in passes (was partial)

- **Definition.** The throw-in's first pass, stored like any other pass and linked to its restart.
- **Signature.** A pass whose passer is out of bounds (ankle point beyond the boundary) and whose release follows the restart's video_ts_ms_live.
- **Evidence.** Restarts + passes.
- **Lands in.**
  - `passes.is_throw_in` (bool; range true/false; IN_GAME): First pass of a throw-in.
  - `passes.restart_id` (string; range FK restarts; IN_GAME): Restart it belongs to.
  - `passes.defender_on_thrower` (bool; range true/false; IN_GAME): A defender within 1.83 m of the thrower at release.
- **new-EV-18 (Shall).** Every throw-in with a visible release creates a passes row flagged as a throw-in and linked to its restart, with whether the thrower was guarded within 1.83 m. *Acceptance:* 100% of throw-ins with a visible release have exactly one is_throw_in pass; thrower equals restarts.thrower_player_id on 100%. Refines new-EV-9 (inbox 007).

### E.04.02 Layup and finish subtypes (was partial)

- **Definition.** Finish subtype per layup or dunk attempt, with the finishing hand.
- **Signature.** Signatures per subtype in actions_extra.yaml finish_subtypes (path relative to the rim, steps after gather, release hand position, takeoff pattern from E.01.03).
- **Evidence.** Pose + ball tracking + the gather/step data of E.01.04.
- **Lands in.**
  - `shots.finish_subtype` (enum[standard, reverse, euro_step, finger_roll, scoop, up_and_under, power_two_foot, hop_step, floater_runner, putback_tip, dunk_one_hand, dunk_two_hand, alley_oop_finish, unresolved]; range enum; IN_GAME): Finish subtype (actions_extra.yaml).
- **Vocabulary.** finish_subtypes (actions_extra.yaml)
- **new-EV-19 (Should).** Each layup or dunk attempt stores a finish subtype (standard, reverse, Euro step, finger roll, scoop, up-and-under, power two-foot, hop step, runner, tip, one/two-hand dunk, alley-oop) from the measured signatures. *Acceptance:* >= 75% correct on 300 labelled finishes, >= 20 per class where available (proposal). Refines new-EV-10 (inbox 007).

### E.04.05 Contest form (hand up, hand-to-ball distance, contest height, class) (was partial)

- **Definition.** How the closest defender contests the release: whether a hand is up, how close the nearest hand gets to the ball, how high it is relative to the ball, whether it blocks the shooter's line of sight, whether he left his feet, when he arrived, and a contest class.
- **Signature.** Contest window W = [release - 0.50 s, release + 0.10 s]. Closest defender = argmin distance shooter-defender at release (existing shots.closest_defender_id). hand_up: the defender's nearer wrist is above his same-side shoulder keypoint in the body frame in >= 1 frame of W while he is within 1.83 m. hand_to_ball_m: minimum over W of the 3-D distance from his nearer wrist keypoint to the ball centre (image-plane fallback scaled by 0.24 m / ball diameter_px; flagged). hand_height_rel_ball_m: wrist height minus ball height at release (+ above the ball). contest_angle_deg: angle at the ball between the ball->rim-centre vector and the ball->wrist vector at release (small = hand in the shot path). vision_interference: wrist inside a 10-degree cone around the shooter's shoulder-midpoint->rim line, between shooter and rim, at release. contest_airborne: defender's ankles >= 0.05 m off the floor at release. arrival_s: time defender first came within 1.83 m minus release time (negative = before release). Class: none (> 1.83 m at release or no hand up), late (first hand-up frame after release), soft (hand up, 1.07-1.83 m), tight (hand up, <= 1.07 m, i.e. NBA's 'contested' 3.5 ft), smothered (<= 0.61 m and hand_to_ball_m <= 0.30 m), block_attempt (airborne and hand_to_ball_m <= 0.30 m with the hand above the ball).
- **Evidence.** Pose + ball 3-D. Literature: NBA.com glossary 'Contested Shot' = closest defender within 3.5 ft (1.07 m) and hustle 'Contested Shots' = defender closes out and raises a hand before release; NBA xFG uses nearest-hand-to-ball distance, relative contest height, hand contest angle, vision interference, hip distance, defender angle and speed, from 1 s before release to release; Franks et al. 2015 find the log-odds of a make rise roughly linearly with defender distance up to about 6 ft (1.83 m) and flat beyond.
- **Lands in.**
  - `shots.contest_hand_up` (bool; range true/false; IN_GAME): Hand up inside the window within 1.83 m.
  - `shots.contest_hand_side` (enum[near_side, far_side, both, none, unresolved]; range enum; IN_GAME): Which hand contested relative to the shooter's shooting hand.
  - `shots.hand_to_ball_m` (float32, m; range [0, 5]; IN_GAME): Minimum wrist-to-ball distance in the window.
  - `shots.hand_height_rel_ball_m` (float32, m; range [-2.5, 1.5]; IN_GAME): Wrist height minus ball height at release.
  - `shots.contest_angle_deg` (float32, degrees; range [0, 180]; IN_GAME): Angle between ball->rim and ball->wrist at release.
  - `shots.vision_interference` (bool; range true/false; IN_GAME): Wrist in the 10-degree sight cone.
  - `shots.contest_airborne` (bool; range true/false; IN_GAME): Defender off the floor at release.
  - `shots.contest_arrival_s` (float32, s; range [-3, 0.5]; IN_GAME): Arrival within 1.83 m relative to release.
  - `shots.contest_class` (enum[none, late, soft, tight, smothered, block_attempt, unresolved]; range enum; IN_GAME): Contest class (actions_extra.yaml contest_classes).
  - `shots.contest_geometry_basis` (enum[3d, image_scaled]; range enum; IN_GAME): Whether hand metrics used 3-D or the ball-diameter image scale.
- **Vocabulary.** contest_classes (actions_extra.yaml)
- **new-EV-20 (Shall).** Each field-goal attempt stores the closest defender's contest form from pose: hand up, contesting hand, minimum hand-to-ball distance (m), hand height relative to the ball (m), contest angle (degrees), vision interference, airborne, arrival time (s) and a contest class (none, late, soft, tight <= 1.07 m, smothered, block attempt). *Acceptance:* Hand-up correct >= 85% on 300 labelled shots; hand-to-ball within 0.30 m median where both are visible in 3-D; class agreement >= 80%; image-scaled rows flagged and reported separately (proposal). Refines new-EV-11 (inbox 007).
- **Sources.** https://www.nba.com/stats/help/glossary (opened 2026-10-18: Contested Shot within 3.5 ft; Contested Shots hustle definition); https://www.nba.com/news/intro-to-expected-field-goal-percentage (opened 2026-10-18: xFG contest features, 1 s window); https://arxiv.org/pdf/1405.0231 (Franks, Miller, Bornn, Goldsberry 2015, Ann. Appl. Stat. 9(1):94-121; opened: section 4.3 and Fig. 7, 0-6 ft linear effect)

### E.04.12 Shooter's footwork into the shot (was partial)

- **Definition.** How the shooter's feet arrive at a jump shot: set (spot-up), 1-2 step, hop, turnaround, fade, sidestep, step-back, spin, drift.
- **Signature.** Signatures in actions_extra.yaml shot_footwork (foot-contact order in the last 0.8 s before takeoff, rotation between gather and release, pelvis velocity at release).
- **Evidence.** Pose (ankles, hips, shoulders).
- **Lands in.**
  - `shots.footwork` (enum[set_feet, one_two_step, hop, turnaround, fade, sidestep, step_back, spin, drift_forward, unresolved]; range enum; IN_GAME): Shot footwork.
- **Vocabulary.** shot_footwork (actions_extra.yaml)
- **new-EV-21 (Should).** Each jump shot stores the shooter's footwork class from the measured foot-contact order, body rotation and release-time pelvis velocity. *Acceptance:* >= 75% correct on 300 labelled jumpers (proposal); step_back agrees with shots.shot_type_code = step_back on >= 95%. Refines new-EV-12 (inbox 007).

### E.05.05 Rebound positioning at the release (was partial)

- **Definition.** Each player's distance to the rim and inside position at the release of a missed shot, and where the rebound came down.
- **Signature.** Snapshot at trigger = shot_release (configuration_snapshots). Inside position for player p vs his nearest opponent q: |p - rim| <= |q - rim| - 0.30 m and the perpendicular distance from p to the rim->q line <= 1.0 m. Landing point = ball position at the first floor contact or first player touch after the last rim/board contact.
- **Evidence.** Tracking.
- **Lands in.**
  - `rebounds.landing_r_m` (float32, m; range [0, 15]; IN_GAME): Distance from the rim centre to the landing point.
  - `rebounds.landing_theta_deg` (float32, degrees; range [-180, 180]; IN_GAME): Angle of the landing point.
  - `rebounds.n_inside_off` (int8, count; range [0, 5]; IN_GAME): Offensive players holding inside position at release.
  - `rebounds.n_inside_def` (int8, count; range [0, 5]; IN_GAME): Defensive players holding inside position at release.
  - `rebounds.rebounder_dist_at_release_m` (float32, m; range [0, 15]; IN_GAME): Eventual rebounder's distance to the rim at release.
- **new-EV-22 (Should).** Every missed-shot rebound stores the landing point (r in m, theta in degrees), the count of each team's players holding inside position at release (0.30 m / 1.0 m rule) and the rebounder's distance at release. *Acceptance:* Recomputes from the shot_release snapshot; landing point within 0.50 m on 100 labelled misses (proposal). Refines new-EV-13 (inbox 007).

### E.07.02 Named cuts (OFF.F8.2) (was partial)

- **Definition.** Every OFF.F8.2 cut gets a primitive code and a geometric signature (m, degrees, s, m/s).
- **Signature.** Per-cut signatures in actions_extra.yaml cuts_named; shared preconditions: off-ball, displacement >= 3.0 m in <= 1.5 s (offense_full.md CUT primitive).
- **Evidence.** Tracking; screens table for screen-dependent cuts (UCLA, shuffle, flex, Iverson).
  - enum addition `movement_primitives.primitive_type`: cut_ucla, cut_iverson, cut_zipper, cut_flash, cut_v, cut_l, cut_shuffle, cut_flex, cut_i, cut_banana, cut_pop_out, cut_thru, cut_45, cut_weak_baseline, cut_dive
- **Vocabulary.** cuts_named (actions_extra.yaml)
- **new-ST-10 (Shall).** The movement-primitive cut vocabulary covers every OFF.F8.2 path cut (UCLA, Iverson, zipper, flash, V, L, shuffle, flex, I, banana, pop-out, thru, 45, weak-side baseline, dive) with one geometric signature each; sequence labels (give-and-go, blind pig, delayed, stampede) are tags on top of primitives. *Acceptance:* Every OFF.F8.2 cut has a code and a signature with numbers; F1 >= 0.80 per cut on >= 50 labelled instances (proposal). Refines new-ST-3 (inbox 007).
- **Sources.** docs/taxonomy/offense_full.md F8.2 (cut list), section 0 CUT primitive

### E.09.06 Off-ball denial posture (was partial)

- **Definition.** A defender denying the pass to his man: close to him, inside the passing lane, with a hand in it.
- **Signature.** For a defender whose man has passes_away = 1: dist_to_man_m <= 1.50 m; the defender's projection on the ball->man segment lies at 55-95% of its length; perpendicular offset from the segment <= 0.60 m; and (when pose is available) the nearer wrist within 0.30 m of the segment. Held >= 0.50 s inside the second.
- **Evidence.** Tracking + pose.
- **Lands in.**
  - `defensive_matchups.deny_posture` (bool; range true/false; IN_GAME): Denial held >= 0.50 s this second.
  - `defensive_matchups.deny_lane_offset_m` (float32, m; range [0, 5]; IN_GAME): Perpendicular offset from the ball->man segment.
  - `defensive_matchups.deny_hand_in_lane` (bool; range true/false; IN_GAME): Nearer wrist within 0.30 m of the segment.
- **new-DF-7 (Should).** Per defender-second, store a denial flag (man one pass away, within 1.50 m, inside the lane at 55-95% of the ball->man segment, offset <= 0.60 m, hand in lane when visible) with the lane offset (m). *Acceptance:* Agrees with labels on >= 80% of 300 labelled defender-seconds (proposal). Refines new-DF-2 (inbox 007).

### E.11.03 Player gestures and on-court communication (was missing)

- **Definition.** Body-pose gestures by players toward officials, opponents, teammates or the crowd (conduct: Rule 10-3.1 lists disrespectfully addressing an official or gesturing to show resentment, taunting, baiting, pointing at an opponent), and defensive communication gestures (pointing out an assignment, switch call) as observable proxies. Pose only; no face or audio-of-speech content.
- **Signature.** Signatures in actions_extra.yaml gestures (arm/hand pose, target within distance, duration, live/dead ball).
- **Evidence.** Video pose; PBP technicals for linking; communication gestures validated against R-CO-08 switch outcomes.
- **Lands in.**
  - `bench_events.actor_on_court` (bool; range true/false; IN_GAME): Actor is one of the ten players on the floor.
  - `bench_events.gesture_code` (enum (actions_extra.yaml gestures); range enum; IN_GAME): Gesture class.
  - `bench_events.target_type` (enum[official, opponent, teammate, crowd, own_bench, opponent_bench, none]; range enum; IN_GAME): Gesture target.
  - `bench_events.target_id` (string; range player/official ID; IN_GAME): Target where identifiable.
  - `bench_events.followed_by_technical_event_id` (string; range FK events; IN_GAME): Technical foul within 10 s after, if any.
  - enum addition `bench_events.actor_type`: on_court_player
- **Vocabulary.** gestures (actions_extra.yaml)
- **new-CC-7 (Should).** Conduct gestures (complaint to an official, taunt/stand-over, pointing at an opponent, crowd incitement, celebration) by on-court players are logged from pose with player, target, time and any technical foul within 10 s. *Acceptance:* Every PBP technical foul on a player has a linked gesture row or 'not_visible'; labels agree >= 80% on 100 clips (proposal); no face keypoints used. Refines new-CC-4 (inbox 007).
- **new-CO-1 (Should).** Defensive communication gestures (assignment point, switch call, help call by arm) are logged before screens and drives as proxies of communication, and their rate per 100 ball screens is reported with the coverage outcome. *Acceptance:* Gesture labels agree >= 75% on 200 labelled screens (proposal); rate reported only with pose coverage >= 70% of the window.
- **Sources.** docs/rules/PRMBB_RulesBook.pdf Rule 10-3.1 (Class A unsporting infractions; scratchpad rules.txt lines 4120-4130)

## Domain F: Group tactics: offence

### F.04.01 System label and cycles (was partial)

- **Definition.** For continuity and rule-based systems, the system label per chance and the number of completed pattern cycles.
- **Signature.** Cycle = the template's action sequence completed once and restarted after a reversal (ball x changes sign with |x| >= 3.0 m); system share = chances labelled / half-court chances.
- **Evidence.** set_instances action sequences.
- **Lands in.**
  - `set_instances.system_code` (enum (OFF.F4.1/F4.2 codes); range enum; IN_GAME): System label.
  - `set_instances.cycles_completed` (int8, count; range [0, 10]; IN_GAME): Completed cycles.
- **new-ST-11 (Should).** Continuity and rule-based system chances store the system code and completed cycles, and team-games report system share of half-court chances. *Acceptance:* System label agrees with Aldemir's labels on >= 80% of 100 chances (proposal); cycles recompute from the action sequence. Refines new-ST-4 (inbox 007).
- **Sources.** docs/taxonomy/offense_full.md F4

### F.05.02 Screener pre-action (was partial)

- **Definition.** How the ball screener arrives (OFF.F5.3): walk-up, sprint, ram, wedge, zipper, Iverson step-up, exit, touch, drag, flip, re-screen, with arrival speed.
- **Signature.** Arrival speed = screener mean speed over the 1.0 s before the screen moment; sprint if > 3.5 m/s from y < 1 m (F5.3 detection); ram if the screener used an off-ball screen <= 2.0 s before; others per F5.3 table.
- **Evidence.** Tracking + screens.
- **Lands in.**
  - `screens.screener_arrival_code` (enum (OFF.F5.3); range enum; IN_GAME): Arrival.
  - `screens.screener_arrival_speed_mps` (float32, m/s; range [0, 9]; IN_GAME): Arrival speed.
- **new-ST-12 (Shall).** Every ball screen stores the screener's arrival code (OFF.F5.3) and arrival speed (m/s, mean over the last 1.0 s). *Acceptance:* Code present on 100% of ball screens; >= 80% correct on 200 labelled screens (proposal). Refines new-ST-5 (inbox 007).
- **Sources.** docs/taxonomy/offense_full.md F5.3

### F.05.04 Off-ball spacing tags during the PnR (was partial)

- **Definition.** Spacing tags (OFF.F5.6) of the three off-ball attackers at the screen moment.
- **Signature.** From configuration_snapshots at trigger = screen_moment; tags per F5.6 detection (empty side: no teammate with the ball's sign(x) and |x| > 3 m; etc.).
- **Evidence.** Tracking.
- **Lands in.**
  - `screens.spacing_tags` (list<enum (OFF.F5.6)>; range list; IN_GAME): Spacing tags at the screen moment.
- **new-ST-13 (Should).** Each ball screen stores the OFF.F5.6 spacing tags of the off-ball attackers at the screen moment. *Acceptance:* Tags recompute from the snapshot; >= 80% agreement with labels on 200 screens (proposal). Refines new-ST-6 (inbox 007).
- **Sources.** docs/taxonomy/offense_full.md F5.6

### F.09.02 Paint touches per chance (was partial)

- **Definition.** Number of paint touches per chance (ball held or dribbled inside the lane) and time of the first one; NBA.com 'Paint Touch' = receives the ball inside the 3-second lane.
- **Signature.** Lane: |x| <= 1.83 m and -1.60 <= y <= 4.19 m. A paint touch = a touch whose catch point, or any dribble contact, is inside the lane; first_paint_touch_s = seconds from chance start.
- **Evidence.** Tracking.
- **Lands in.**
  - `chances.paint_touches` (int8, count; range [0, 20]; IN_GAME): Paint touches.
  - `chances.first_paint_touch_s` (float32, s; range [0, 30]; IN_GAME): Time to the first paint touch.
- **new-ST-14 (Should).** Each chance stores paint touches (catch or dribble inside |x| <= 1.83 m, y <= 4.19 m) and the time to the first one. *Acceptance:* Recomputes from touches/dribbles; first paint touch within +/- 0.20 s of gold (proposal). Refines new-ST-7 (inbox 007).
- **Sources.** https://www.nba.com/stats/help/glossary (Paint Touch definition)

### F.13.09 Ball movement per chance (was partial)

- **Definition.** Passes before the shot, ball reversals and time from first frontcourt catch to shot.
- **Signature.** Reversal = ball x changes sign with |x| >= 3.0 m on both sides within one chance; frontcourt_to_shot_s from the first frontcourt catch (A.04.12 status) to release.
- **Evidence.** Passes, ball_states.
- **Lands in.**
  - `chances.n_passes` (int8, count; range [0, 30]; IN_GAME): Passes in the chance.
  - `chances.n_reversals` (int8, count; range [0, 10]; IN_GAME): Ball reversals.
  - `chances.frontcourt_to_shot_s` (float32, s; range [0, 30]; IN_GAME): First frontcourt catch to shot.
- **new-ST-15 (Should).** Each chance stores passes, ball reversals (sign change of x with |x| >= 3.0 m both sides) and time from the first frontcourt catch to the shot. *Acceptance:* Counts recompute; reversal count agrees with labels on >= 90% of 200 chances (proposal). Refines new-ST-8 (inbox 007).

## Domain G: Group tactics: defence

### G.01.04 Defensive pick-up point (was missing)

- **Definition.** Where the defence first puts sustained pressure on the ball handler in a possession: the handler's distance from the rim he attacks when an on-ball defender first stays within 1.83 m of him for >= 1.0 s.
- **Signature.** Attacked-rim frame, y in m (rim at y = 0, division line at y = 12.73, opposite three-point arc top at y = 18.71, opposite baseline at y = 27.05). pickup_ts = first time in the possession at which one defender stays <= 1.83 m from the ball handler (holder or dribbler) for >= 1.0 s continuous while the ball is live; pickup_y_m = handler's y at pickup_ts. Class: full_court y >= 18.71; three_quarter 14.00 <= y < 18.71; half_court 9.50 <= y < 14.00; top_of_key y < 9.50; none = no pickup before the first shot/turnover. Possessions starting with a frontcourt throw-in are classed 'frontcourt_start'.
- **Evidence.** Tracking; scheme labels (scheme_states) for agreement.
- **Lands in.**
  - `possessions.pickup_ts_ms` (int64, ms; range [0, video duration]; IN_GAME): Time of pickup.
  - `possessions.pickup_y_m` (float32, m; range [-1.6, 27.05]; IN_GAME): Handler's distance up-court from the attacked rim at pickup.
  - `possessions.pickup_class` (enum[full_court, three_quarter, half_court, top_of_key, none, frontcourt_start]; range enum; IN_GAME): Pick-up class.
  - `possessions.pickup_defender_id` (string; range ESPN athlete ID; IN_GAME): Defender who picked up.
  - `possessions.pickup_handler_speed_mps` (float32, m/s; range [0, 10]; IN_GAME): Handler speed at pickup.
- **Vocabulary.** pickup_classes (actions_extra.yaml)
- **new-DF-8 (Shall).** Each possession stores the defensive pick-up point: time, the handler's distance from the attacked rim (m), class (full, three-quarter, half court, top of key, none, frontcourt start; edges 18.71/14.00/9.50 m) and the picking-up defender, using the 1.83 m for >= 1.0 s rule. *Acceptance:* Recomputes from tracks; class agrees with labels on >= 85% of 200 possessions (proposal); pickup_y within 1.0 m of a hand-marked point on 50 possessions. Refines new-DF-3 (inbox 007).
- **Sources.** src/msu_alpha/geometry.py and config/court_ncaa_men.yaml (frame and distances); docs/rules/PRMBB_RulesBook.pdf closely-guarded distance 1.83 m (6 ft) used as the pressure radius

### G.03.03 Lob protection against a fronted post (was partial)

- **Definition.** When the post player is fronted, whether a weak-side defender is in position to take away the lob, and the result of lob attempts.
- **Signature.** Fronted: the post defender's pelvis lies between the ball and the post player (projection at 10-90% of the ball->post segment, offset <= 0.60 m) while the post is at r <= 4.0 m. Lob help present: another defender within 2.0 m of the rim->post segment or within 2.5 m of the rim on the side opposite the ball (sign of x). Lob attempt: pass with apex height >= 3.35 m (rim 3.05 m + 0.30 m) whose intended receiver is at r <= 2.0 m at catch or tip.
- **Evidence.** Tracking with ball 3-D apex (lob apex measurable once R-CG-11 passes).
- **Lands in.**
  - `post_touches.fronted` (bool; range true/false; IN_GAME): Post was fronted before the entry.
  - `post_touches.lob_help_present` (bool; range true/false; IN_GAME): Weak-side lob help (definition above).
  - `post_touches.lob_help_defender_id` (string; range ESPN athlete ID; IN_GAME): Helper.
  - `passes.apex_height_m` (float32, m; range [0, 8]; IN_GAME): Maximum ball height in flight.
  - `passes.is_lob_over_front` (bool; range true/false; IN_GAME): Lob attempt to a fronted post.
- **new-DF-9 (Should).** When a post is fronted, store whether weak-side lob help is present (within 2.0 m of the rim->post line or 2.5 m of the rim), the helper, and every lob over the front (apex >= 3.35 m, receiver r <= 2.0 m) with its result. *Acceptance:* Fronted flag agrees with labels >= 85% on 100 post possessions; lob outcomes equal shot/turnover records on 100% (proposal). Refines new-DF-4 (inbox 007).

### G.09.03 Foul-trouble effect on defensive aggressiveness (was partial)

- **Definition.** Within-player change in defensive behaviour while in foul trouble (foul_state.foul_trouble, thresholds per R-SR-11).
- **Signature.** For each player-season, compare in-trouble vs not-in-trouble defensive possessions, matched on half and score-margin band (|margin| <= 5, 6-12, > 12): mean on-ball distance (m), contest rate and mean contest distance at release (m), help-position share, fouls per 100 defensive possessions. Difference = trouble minus normal, bootstrap 95% interval.
- **Evidence.** Derived from defensive_matchups, shots, foul_state.
- **Lands in.**
  - `profile_snapshots.metric_code` add: def_onball_dist_ft_delta_m, def_contest_rate_ft_delta, def_contest_dist_ft_delta_m, def_help_share_ft_delta, def_fouls_per100_ft_delta. Foul-trouble deltas (entity_type = player).
- **new-DF-10 (Should).** Per player-season, report the in-foul-trouble minus normal difference in on-ball distance (m), contest rate, contest distance (m), help share and fouls per 100 possessions, matched on half and margin band, with 95% intervals. *Acceptance:* Interval reported for players with >= 30 defensive possessions in each state; descriptive only below that. Refines new-DF-5 (inbox 007).

## Domain H: Outcomes and value

### H.02.04 Bench points and starter/bench split (was partial)

- **Definition.** Points, minutes share and net rating of non-starters per team-game and as of date.
- **Signature.** From player_box.starter = false rows; bench minutes share = bench minutes / (200 + 25 * OT periods).
- **Evidence.** Box scores.
- **Lands in.**
  - `team_box.bench_points` (int16, points; range [0, 150]; POST_GAME): Points by non-starters.
  - `team_box.bench_minutes_share` (float32, share; range [0, 1]; POST_GAME): Bench minutes / team minutes.
  - `profile_snapshots.metric_code` add: bench_points_pg, bench_minutes_share, bench_net_per100. As-of team metrics.
- **new-OS-2 (Should).** Team box rows store bench points and bench minutes share, and team profiles report them as of each date with bench net rating per 100 possessions. *Acceptance:* Recomputes from player_box; equals published bench points where a source gives them; minutes total check (200 + 25 per OT) passes. Refines new-OS-1 (inbox 007).

### H.03.05 Shot-making (points above shot quality) (was partial)

- **Definition.** Per shot: points scored minus shot-quality expected points; per shooter: the shrunk average per attempt.
- **Signature.** residual = made * value_attempted - shot_quality_xpts. Shooter value = empirical-Bayes shrinkage toward the position-group mean with prior strength k fitted on split-half reliability; as of the game date.
- **Evidence.** shots.shot_quality_xpts (R-VL-04).
- **Lands in.**
  - `shots.shot_making_residual` (float32, points; range [-3, 3]; POST_GAME): Points minus expected points for this attempt.
  - `profile_snapshots.metric_code` add: shot_making_pts_per_fga. Shrunk shooter value with n and ci95.
- **new-VL-3 (Shall).** Each shot stores its shot-making residual (points minus expected points), and shooter profiles report the shrunk residual per attempt with n and a 95% interval as of each date. *Acceptance:* Interval on every value; < 50 attempts reported as shrunk-only; split-half reliability of the raw residual reported per season. Refines new-VL-1 (inbox 007).

### H.04.06 Defensive value credits (contests, rotations, rim deterrence) (was partial)

- **Definition.** Defensive credit beyond steals and blocks, split, as in Franks et al. 2015, into effects on shot efficiency (contests: lowering make probability) and on shot frequency (deterrence: shots not taken), plus rotations, ball pressure and denial.
- **Signature.** contest credit = xpts(shot | contest features set to 'none') - xpts(shot | observed contest features of E.04.05), to the contesting defender. rim deterrence: for each chance, defender d is rim protector if defensive_matchups.is_rim_protector for >= 50% of the chance's live seconds; deterrence = (E[rim attempts | offensive configuration, no defender identity] - observed rim attempts) x (xPPS_rim - xPPS_alternative), rim attempt = release r <= 1.83 m. rotation: help defender leaves his man (dist_to_man rises by >= 1.5 m) after a trigger (drive start, roll catch, post entry) and within 1.2 s is within 1.83 m of the ball handler or within 1.0 m of the handler's line to the rim; credit = value 1.0 s after arrival minus value at the trigger, relative to the model's expected change for the trigger. rim defender of a shot (descriptive 'defended at rim' stat): defender within 1.52 m (5 ft) of the rim's floor point and within 1.52 m of the shooter at release. All credits for a chance sum to the chance's defensive value change (bookkeeping).
- **Evidence.** Tracking + E.04.05 contest features + possession_value. Literature: Franks et al. 2015 (frequency vs efficiency); SportVU 'defended at rim' 5 ft/5 ft rule reported in secondary sources (unverified, not opened).
- **Lands in.**
  - `value_credits.counterfactual_basis` (enum[contest_off, expected_rim_attempts, expected_trigger_change, observed_delta]; range enum; POST_GAME): Counterfactual used for this credit.
  - `shots.rim_defender_id` (string; range ESPN athlete ID; IN_GAME): Rim defender (5 ft / 5 ft rule), null if none.
  - `profile_snapshots.metric_code` add: def_value_per100, contest_value_per100, rim_deterrence_per100, rotation_value_per100, rim_dfg_pct. Defensive value metrics.
  - enum addition `value_credits.credit_role`: contest, rotation, rim_deterrence, closeout, ball_pressure, denial, box_out, charge_drawn
- **Vocabulary.** defensive_credit_roles (actions_extra.yaml)
- **new-VL-4 (Shall).** Defensive value credits go to on-ball and help defenders for contests, rotations, rim deterrence, closeouts, ball pressure, denial, box-outs and charges, each with its counterfactual basis, summed per 100 defensive possessions with an interval. *Acceptance:* Credits for every chance sum to its defensive value change within 0.01 xpts (bookkeeping test); interval on every player value; players ranked only with n >= 100 defensive possessions. Refines new-VL-2 (inbox 007).
- **new-VL-5 (Should).** Each shot stores its rim defender (within 1.52 m of the rim and of the shooter at release), and player profiles report rim field-goal percentage allowed and rim attempts deterred per 100 possessions. *Acceptance:* Rim defender agrees with labels on >= 90% of 100 rim attempts (proposal); rim_dfg_pct reported with n and 95% interval.
- **Sources.** https://arxiv.org/pdf/1405.0231 (Franks et al. 2015: defensive impact on shot frequency vs efficiency; HMM matchups); https://www.nba.com/stats/help/glossary (Defended at Rim percentage; definition text of the distance rule not on the page)

## Domain I: Physical and load

### I.02.06 Jump load (count and height per minute) (was partial)

Closed together with E.01.03; requirement(s): new-PL-5.

### I.02.07 Direction-weighted load (lateral and backward running) (was missing)

- **Definition.** Time and distance per stint split by movement direction relative to torso facing, alongside the speed bins.
- **Signature.** Per frame with speed >= 0.5 m/s and torso-facing confidence: d = wrap(heading - torso_facing); forward |d| <= 45, lateral 45-135, backward >= 135 degrees. Stint coverage of pose >= 70% required.
- **Evidence.** Tracking + pose.
- **Lands in.**
  - `load_stint_bins.time_forward_s` (float32, s; range [0, 2400]; IN_GAME): Time moving forward in this speed bin.
  - `load_stint_bins.time_lateral_s` (float32, s; range [0, 2400]; IN_GAME): Time moving laterally.
  - `load_stint_bins.time_backward_s` (float32, s; range [0, 2400]; IN_GAME): Time moving backward.
  - `load_stint_bins.dist_forward_m` (float32, m; range [0, 10000]; IN_GAME): Distance forward.
  - `load_stint_bins.dist_lateral_m` (float32, m; range [0, 10000]; IN_GAME): Distance lateral.
  - `load_stint_bins.dist_backward_m` (float32, m; range [0, 10000]; IN_GAME): Distance backward.
  - `load_stint_bins.dir_pose_coverage` (float32, share; range [0, 1]; IN_GAME): Share of stint frames with usable torso facing.
- **Vocabulary.** movement_direction_classes (actions_extra.yaml)
- **new-PL-7 (Should).** Load stint bins split time (s) and distance (m) into forward, lateral and backward movement relative to torso facing, reported only where pose coverage is >= 70% of the stint. *Acceptance:* Direction split sums to the bin totals within 1%; recomputes from player_positions; low-coverage stints flagged and excluded from rankings. Refines new-PL-3 (inbox 007).
- **Sources.** https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/ (recommendation to report movement direction; via load_thresholds.md)

### I.02.08 Contact load (was partial)

- **Definition.** Physical contacts per minute played: screens set and absorbed, box-out contacts, post contacts, charges taken, floor dives.
- **Signature.** screen_set: screens.screener_id with contact_distance_m <= 0.30; screen_absorbed: the screened defender of such a screen; box_out_contact: box_outs.contact_duration_s >= 0.30; post_contact: post_touches with the defender within 0.30 m for >= 1.0 s; charge_taken: defensive_events.type = charge_drawn; floor_dive: player_positions.stance = on_floor during a loose ball.
- **Evidence.** Derived.
- **Lands in.**
  - `profile_snapshots.metric_code` add: contact_events_per_min, screens_set_per_min, screens_absorbed_per_min, boxout_contacts_per_min, post_contacts_per_min. Contact load metrics.
- **Vocabulary.** contact_event_kinds (actions_extra.yaml)
- **new-PL-8 (Should).** Per player-game, count contact events (screens set and absorbed at <= 0.30 m, box-out contacts >= 0.30 s, post contacts >= 1.0 s, charges, floor dives) per minute played, with coverage. *Acceptance:* Counts recompute from source tables; reported only for games with tracking coverage >= 70% of the player's minutes. Refines new-PL-4 (inbox 007).

## Domain J: Context

### J.01.04 Road-trip structure (was missing)

- **Definition.** Index of a game within a run of consecutive away/neutral games with no home game in between, and days since the team's last home game.
- **Signature.** From the schedule: road_trip_index = 0 for home games, else 1 + previous game's index if the previous game was also away/neutral. days_since_last_home_game = (tip - last home tip) in days.
- **Evidence.** Schedule (games).
- **Lands in.**
  - `team_game_context.road_trip_index` (int8, count; range [0, 10]; PRE_GAME): 0 home; n = n-th consecutive away/neutral game.
  - `team_game_context.days_since_last_home_game` (float32, days; range [0, 120]; PRE_GAME): Days since the last home tip.
- **new-CX-13 (Should).** Each team-game stores its road-trip index and days since the team's last home game. *Acceptance:* Recomputes from games; 100% filled; leakage test passes (no future games read). Refines new-CX-5 (inbox 007).

### J.01.05 Tip time on each team's body clock (was partial)

- **Definition.** Scheduled tip expressed in the team's campus time zone (decimal hours), and days since the team last played in a different time zone.
- **Signature.** tip_body_clock_h = local hour of games.tip_scheduled_utc in teams.campus_tz (zoneinfo); days_since_tz_shift = days since the team's previous game whose venue tz offset differed from campus tz.
- **Evidence.** Schedule, venues.tz, teams.campus_tz.
- **Lands in.**
  - `team_game_context.tip_body_clock_h` (float32, hours; range [0, 24); PRE_GAME): Tip on the team's campus clock.
  - `team_game_context.days_since_tz_shift` (float32, days; range [0, 365]; PRE_GAME): Days since a game in another time zone.
- **new-CX-14 (Should).** Each team-game stores the tip time on the team's campus clock (h) and days since its last game in another time zone. *Acceptance:* Recomputes with zoneinfo from UTC tip and campus tz on 100% of games; daylight-saving transitions covered by unit tests. Refines new-CX-6 (inbox 007).

### J.03.03 Recent form (both teams) (was partial)

- **Definition.** Previous game's result, margin, margin against the closing spread and overtime flag, and the current streak, as of tip.
- **Signature.** prev_ats_residual = prev margin + prev closing spread (team perspective, spread negative for favourites); streak = +n consecutive wins / -n consecutive losses.
- **Evidence.** games; lines_odds_snapshots closing lines.
- **Lands in.**
  - `team_game_context.prev_margin` (int16, points; range [-80, 80]; PRE_GAME): Previous game margin.
  - `team_game_context.prev_ats_residual` (float32, points; range [-80, 80]; PRE_GAME): Margin versus the closing spread.
  - `team_game_context.prev_overtime` (bool; range true/false; PRE_GAME): Previous game went to overtime.
  - `team_game_context.streak` (int8, games; range [-40, 40]; PRE_GAME): Signed win/loss streak.
- **new-CX-15 (Should).** Each team-game carries the previous game's margin, margin against the closing spread, overtime flag and the current signed streak, as of tip. *Acceptance:* Recomputes from games and closing lines; leakage test shows no post-tip data; 100% filled after each team's first game. Refines new-CX-7 (inbox 007).

### J.04.03 Season phase and game number (was partial)

- **Definition.** Game number in the season and in conference play, and season phase.
- **Signature.** Ordered by tip time per team; exhibitions excluded from numbering.
- **Evidence.** games.game_type, conference_game.
- **Lands in.**
  - `team_game_context.game_num_season` (int8, count; range [1, 45]; PRE_GAME): Game number in the season.
  - `team_game_context.game_num_conf` (int8, count; range [0, 25]; PRE_GAME): Conference game number (0 = non-conference).
  - `team_game_context.season_phase` (enum[exhibition, non_conference, conference, conference_tournament, ncaa_tournament, other_postseason]; range enum; PRE_GAME): Season phase.
- **new-CX-16 (Should).** Each team-game carries its season game number, conference game number and season phase. *Acceptance:* Recomputes from the schedule; 100% filled; exhibitions get no number. Refines new-CX-8 (inbox 007).

### J.05.06 Public betting share (was missing)

- **Definition.** Share of tickets and of money on each side of a market, where a public source exists, used only in the market-input model variant.
- **Signature.** Stored per market snapshot; never imputed.
- **Evidence.** No source chosen; a free, terms-compliant source must be registered first.
- **Lands in.**
  - `market_snapshots.public_ticket_share` (float32, share; range [0, 1]; IN_GAME): Share of bets on this side.
  - `market_snapshots.public_money_share` (float32, share; range [0, 1]; IN_GAME): Share of handle on this side.
  - `market_snapshots.public_share_source` (string; range source_register.source; IN_GAME): Source of the share.
- **new-MK-20 (Should).** Public ticket and money shares are stored per market snapshot only from a source registered in the source register with terms checked, and only the market-input model variant may read them. *Acceptance:* Source register row with terms URL and permission status exists before the first value; 0 values read by the market-free variant (import test). Refines new-MK-19 (inbox 007).
- **Open.** No terms-compliant free source identified; columns specified but data cannot be collected yet.

### J.06.01 Beliefs register and hypothesis candidates (was partial)

**Cannot be closed by a specification.** Not a data gap: 82 candidates (C1-C82) await Aldemir's registration in the live doc. No requirement or column can close it; the requirements session must register them.

## Domain K: Coaching and decisions

### K.01.11 Icing the free-throw shooter (was partial)

- **Definition.** A timeout called between a foul and the first free throw of its sequence.
- **Signature.** timeouts.video_ts_ms_start between the foul's whistle and free_throws.video_ts_ms_release of attempt_k = 1 of the same ft_sequence_id.
- **Evidence.** timeouts, free_throws.
- **Lands in.**
  - `free_throws.preceded_by_timeout_id` (string; range FK timeouts; IN_GAME): Timeout between the foul and this sequence's first attempt.
  - `free_throws.icing_team` (enum[defence, offence, media, none]; range enum; IN_GAME): Who called it.
- **new-CH-2 (Should).** Every free-throw sequence links any timeout called between the foul and the first attempt, with the calling team (icing flag). *Acceptance:* Recomputes from timeouts and free_throws ordering; 100% of such timeouts linked. Refines new-CH-1 (inbox 007).

## Domain L: Media and video

### L.02.02 Finer camera views (was partial)

- **Definition.** A second per-frame label naming the camera view for non-main frames, beside the 9 camera shot types.
- **Signature.** From the recovered camera centre (B.03.04) when the court mapping resolves: reverse_angle y_fc < -8.0 m and z >= 3 m; baseline_low |x_fc| >= 14.5 m and z <= 2.0 m; end_high |x_fc| >= 14.5 m and z > 4 m; backboard_cam within 0.5 m of a backboard; rail_low y_fc > 7.6 m and z <= 1.5 m; skycam z >= 6 m over the court (|x_fc| < 14.3, |y_fc| < 7.6); otherwise by image classifier (handheld_iso, bench, crowd, studio).
- **Evidence.** Video.
- **Lands in.**
  - `frames.camera_view` (enum (actions_extra.yaml camera_views); range enum; IN_GAME): Camera view sub-class.
- **Vocabulary.** camera_views (actions_extra.yaml)
- **new-VI-5 (Should).** Every frame carries a camera-view label (main high side, reverse angle, baseline low, end high, backboard, rail, skycam, handheld iso, bench, crowd, studio, graphic) from the recovered camera centre where mapping resolves and from an image classifier otherwise; the 9-class shot type is unchanged. *Acceptance:* >= 90% correct on 500 labelled non-main frames (proposal); camera-centre rules unit-tested on the registered cameras. Refines new-VI-2 (inbox 007).

### L.02.07 Broadcast replays as secondary evidence (was partial)

- **Definition.** Each replay segment linked to the live event it shows, with the time offset and the replay's camera view; no event, position or count is ever created from a replay frame.
- **Signature.** Candidate events = events within 60 s before the replay start; link = event whose type and participants best match the replay content (players re-identified, ball path), offset = replay start - event video_ts.
- **Evidence.** Video replays.
- **Lands in.**
  - `frames.replay_of_event_id` (string; range FK events; IN_GAME): Live event this replay frame shows.
  - `frames.replay_offset_s` (float32, s; range [0, 600]; IN_GAME): Replay start minus the live event time.
- **new-VI-6 (Should).** Replay segments are linked to the live event they replay with the time offset (s) and camera view, as evidence for reviewers and labellers only. *Acceptance:* >= 90% of replay segments linked on 3 games (proposal); 0 statistics computed from rows with events.from_replay_frame = true. Refines new-VI-3 (inbox 007).

### L.03.04 Stat graphics and lower thirds as weak labels (was missing)

- **Definition.** On-screen broadcast graphics other than the score bug (player foul counts, team fouls, timeouts left, stat lines, set or lineup graphics), read as weak labels and compared with our state record.
- **Signature.** Graphic region detected outside the scorebug bbox; OCR text with per-field confidence; parsed into fields; disagreements become scoreboard_flags rows.
- **Evidence.** Video graphics.
- **Lands in.**
  - `scoreboard_ocr.graphic_kind` (enum[none, player_fouls, team_fouls, timeouts_left, player_stat_line, team_stat_comparison, lineup, set_name, other]; range enum; IN_GAME): Kind of non-scorebug graphic.
  - `scoreboard_ocr.graphic_text_raw` (string; range free text; IN_GAME): OCR text.
  - `scoreboard_ocr.graphic_parsed_json` (json; range fields; IN_GAME): Parsed fields.
  - `scoreboard_ocr.graphic_subject_player_id` (string; range ESPN athlete ID; IN_GAME): Player the graphic is about.
  - enum addition `scoreboard_ocr.display`: broadcast_graphic
- **new-VI-7 (Should).** Broadcast stat graphics are read as weak labels (kind, text, parsed fields, subject player, confidence) in the score-reading table and every disagreement with the state record raises a flag; graphics never overwrite state. *Acceptance:* >= 95% character accuracy on 200 labelled graphics (proposal); 100% of disagreements logged as scoreboard_flags. Refines new-AU-1 (inbox 007).

### L.04.02 Buzzers and horns (and crowd reactions) (was partial)

- **Definition.** Horn events with kind and onset time; crowd-reaction peaks as a second audio event type.
- **Signature.** Horn: narrow-band sustained tone >= 0.3 s; onset = first 10 ms frame above the horn template threshold. Kind: period_end if game clock reads 0.0 within 0.3 s; shot_clock if the shot clock reads 0 within 0.3 s; substitution_or_timeout if the ball is dead and both clocks are non-zero; other. Crowd reaction: 1-s loudness >= 6 dB above the trailing 10-s median, not a horn, not commentary-dominated.
- **Evidence.** Broadcast audio aligned to video (video_files.audio_offset_ms).
- **Lands in.**
  - `audio_seconds.buzzer_kind` (enum[none, period_end, shot_clock, substitution_or_timeout, other]; range enum; IN_GAME): Horn kind in this second.
  - `audio_seconds.buzzer_onset_ms` (int16, ms; range [0, 999]; IN_GAME): Onset offset inside the second.
  - `audio_seconds.crowd_reaction_db` (float32, dB; range [0, 40]; IN_GAME): Excess over the trailing 10-s median (0 if none).
- **Vocabulary.** audio_events (actions_extra.yaml)
- **new-AU-3 (Should).** Horns are detected from audio with kind (period end, shot clock, substitution/timeout, other) and onset time to 10 ms, linked to the clock state. *Acceptance:* Recall >= 90% and onset within +/- 0.10 s on 200 labelled horns (proposal). Refines new-AU-2 (inbox 007).
- **new-AU-4 (Should).** Crowd reactions are stored per second as the excess loudness (dB) over the trailing 10-s median when >= 6 dB and not a horn or commentary peak. *Acceptance:* Reaction seconds agree with labels on >= 80% of 200 labelled seconds (proposal); used by C.05.03 crowd-share validation.

## Domain M: Data, quality and governance

### M.01.06 Source definition register (was partial)

- **Definition.** For every ingested source field that encodes a definition (possession, chance, assist, block, steal, transition/fast break, shot zone/range, garbage time, minutes, points in paint), the source's own definition, URL and check date, linked to the column carrying it.
- **Signature.** Registry; one row per (source, field). Seed rows from docs/data/source_field_map.md sections 4 and V.5-V.6 (e.g. KenPom possessions = FGA - OR + TO + 0.475 x FTA; CBBD shotInfo.range derived from play text; CBBD lineup possessions = event count; hoopR NCAA is_garbage_time and is_transition, definitions unverified; NCAA assist = statistician judgement, manual not opened).
- **Evidence.** Source documentation and code (already opened in source_field_map.md).
  - new table `source_definitions` (one row per source x field definition): source (string), source_field (string), concept (enum[possession, chance, assist, block, steal, rebound, turnover, transition, fast_break, shot_zone, shot_range, garbage_time, minutes, points_in_paint, other]), definition_text (string), url (string), verified (bool), checked_on (date), our_columns (list<string>), difference_from_ours (string)
- **Vocabulary.** source_definition_concepts (actions_extra.yaml)
- **new-DS-3 (Shall).** A source-definition register holds, per source field that encodes a definition, the source's own definition (paraphrased), URL, verified flag, check date, the columns carrying it and its difference from our definition. *Acceptance:* 100% of source-derived definitional columns link to a register row; every row re-checked each season (R-DS-01); seeded from source_field_map.md sections 4 and V with >= 15 rows. Refines new-DS-2 (inbox 007).
- **Sources.** docs/data/source_field_map.md sections 4, V.5, V.6

### M.03.06 Known-bias register (was partial)

Closed together with C.04.04; requirement(s): new-DQ-3, new-DQ-4.

### M.03.09 Ontology coverage check (was partial)

- **Definition.** A script that keeps config/game_ontology.yaml in step with the live requirement IDs, schema/tables and proposed changes.
- **Signature.** scripts/check_ontology.py fails when: a leaf cites an unknown requirement ID (live export or a new-<FAMILY>-n in coord/requirements_inbox, docs/data/gap_closures_round2.md); a <table>.<column> is in neither schema/tables nor schema/tables_proposed_changes.yaml; a live requirement or a table is referenced by no leaf; a status disagrees with its evidence (covered without requirement or column); a vocab code is unknown.
- **Evidence.** Repo files.
- **new-CD-2 (Shall).** A repository check validates the game ontology against the live requirement IDs, inbox proposals, schema tables, proposed column changes and vocabularies, and regenerates the coverage statistics. *Acceptance:* Script exits 0 on the current repo; runs in repository tests (R-EN-08); coverage numbers in docs/data/game_ontology_coverage.md equal its output. Refines new-CD-1 (inbox 007).

### M.04.06 External consultant (JEV) log (was partial)

- **Definition.** Private log of each JEV consultation, outside the pipeline read path.
- **Signature.** Stored at ~/MSU-Alpha-3-private/jev/jev_log.parquet (never in the repo); columns question_id, items_sent_hash, options_shown, answer, model_version, asked_utc. An import-graph test asserts no src/ module opens that path.
- **Evidence.** Process.
- **new-HR-2 (Shall).** Every JEV consultation is logged privately (question ID, hash of items sent, options shown, answer, exact model version, time), and an automated test proves no pipeline module reads the log. *Acceptance:* One row per consultation; import-graph and path-grep test shows 0 references from src/ to the JEV log path. Refines new-HR-1 (inbox 007).

## What still cannot be closed, and why

- J.06.01 beliefs register: needs Aldemir to register the 82 candidates; no data or schema change closes it.
- J.05.06 public betting share: specified, but no free, terms-compliant source is registered, so no data can be collected (new-MK-20 blocks collection until one is).
- Height-dependent parts (E.01.03 jump height, E.04.05 hand height and hand-to-ball in 3-D, G.03.03 lob apex, E.03.06 release height) stay provisional until R-CG-11 (3-D calibration) passes; image-scaled values are flagged.
- B.01.08 coaching-box geometry and every court constant: owned by the rules work; the coach-position columns read the constant from config.
- C.04.04 home-crew bias needs our video assist rule fixed before measuring, and enough venues with >= 150 made FGs with a visible prior pass.
- E.11.03 head-turn and verbal communication: not measurable without face or speech data, which the project excludes; only body-pose gestures are specified.

## Open questions

- Numbering collision: the rules agent may also be issuing new-SR/RF/EV/DT/BL IDs today; whose numbers win?
- Short corner: accept 3.5 < |x| <= 6.0 m, y <= 1.50 m, or define from MSU film first?
- Contest classes: keep NBA's 3.5 ft (1.07 m) 'tight' edge or use the 1.83 m saturation edge only?
- Pick-up classes: are the 18.71 / 14.00 / 9.50 m edges the staff's notion of full / three-quarter / half court?
- Lineup 'big' rule: listed C or listed F >= 206 cm, given listed heights run high?
- Garbage time: is the CTG-adapted last-12-minutes mapping acceptable for 40-minute college games, or use the win-probability rule only?
- Runs: keep both definitions, or pick one as primary for C-series hypotheses?
- Fakes, runs and source definitions get new tables; is that acceptable, or must they become event-family rows in `events`?
- Gesture logging of players toward officials: is it within the project's conduct/ethics bounds for publication, or private only?
- Rim liveliness proxy: is median rebound distance enough, or should rim model be required before any arena-shooting test?
- NIL: keep the field at all, given it is exploratory-only?
- Public betting share: is any paid source acceptable, or drop the leaf?

## Sources opened for this round (2026-10-18)

- https://www.nba.com/stats/help/glossary (Contested Shot 3.5 ft; Contested Shots, Deflections, Defended at Rim %, Paint Touch, Box Outs definitions)
- https://www.nba.com/news/intro-to-expected-field-goal-percentage (xFG contest features: nearest hand to ball, relative contest height, contest angle, vision interference, 1 s window)
- https://arxiv.org/abs/1405.0231 and https://arxiv.org/pdf/1405.0231 (Franks, Miller, Bornn, Goldsberry 2015, Ann. Appl. Stat. 9(1):94-121: frequency vs efficiency, HMM matchups, Fig. 7 distance effect to ~6 ft)
- https://cleaningtheglass.com/stats/guide/garbage_time (CTG garbage-time thresholds)
- https://arxiv.org/abs/2210.13687 (Pelechrinis 2022, home-team refereeing bias in the NBA and its post-COVID decline)
- docs/rules/PRMBB_RulesBook.pdf via the local text copy: Rules 7-1, 7-2, 9-10, 9-12, 10-3
- Repo research reused (already source-cited there): docs/research/load_thresholds.md (Tuttle 2024 PMC11467009, Irid 2025 PMC12490299, Petway 2020 PMC7058381), docs/data/source_field_map.md sections 4 and V
- Not opened, cited as unverified: FiveThirtyEight 'it's easier to get assists in Huntsville' (home-crew assists); SportVU 'defended at rim' 5 ft / 5 ft rule (FiveThirtyEight URL redirected; secondary search snippets only)
