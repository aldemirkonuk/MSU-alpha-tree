# Data dictionary: state record, scoreboard and made-basket tables

Status: **proposal** (2026-10-18, prompt 003 W2 item 5). The requirements session approves; nothing here is final.
Companion files: `schema/tables/<table>.yaml` (one per table below, status: proposed, generated from the same spec as this page) and `config/invariants.yaml` (the invariant checks, rule numbers verified against the 2026-27 rules book).
Core tables (`games`, `possessions`, `chances`, `events`, `shots`, `frames`, `tracks`, `fouls`, `rosters`) are defined in `docs/data/dictionary_games.md` by the core-table workflow; this page only refers to them by name.

Requirement families served: State record R-SR-01..15, Invariants R-IV-01..16, Scoreboard and scorer errors R-SB-01..04, Made-basket detection R-MB-01..07, and the possession engine R-PE-01..13 (state vocabulary shared with simulated games).

## 1. How the state record works

Three sensors feed one state record; none is the truth on its own (live doc, "State record and invariants").

| Sensor | Gives | Time resolution | In blind pass | In anchored pass |
| --- | --- | --- | --- | --- |
| Scoreboard OCR (broadcast scorebug, arena board when in shot) | period, game clock, shot clock, score, team fouls, bonus, timeouts, arrow (when shown) | per frame read; game clock 0.1 s under 60 s (Rule 1-18.2), else 1 s; shot clock 1 s (tenths optional under 5 s, Rule 1-19.2) | yes | yes |
| Play-by-play (official scorebook as published: CBBD plays, ESPN pbp already pulled, hoopR) | who and what: shooter, fouler, foul type, substitutions, timeouts, free-throw sequence, rebounds, turnovers | 1 s of game clock; order within a second not reliable | no | yes |
| CV (our models on the video) | where and how: positions, ball, rim and net, lane formation, everything between logged events | per frame (1/60 s at 60 fps) | yes | yes |

Rules applied everywhere:

1. **State versus invariants.** State columns are measured and always recorded. Invariants (`config/invariants.yaml`) are checks on them. A break creates a `scoreboard_flags` row (`flag_type = invariant_break`) and, by its action, a review item or a quarantine.
2. **Authority order** when sources disagree and a review cannot settle it: official scorebook (PBP and box score) > arena scoreboard > broadcast scorebug (Rule 2-9.13, verified: pdf page 41, printed page 38, heading "SECTION 9. DUTIES OF SCORERS").
3. **Raw readings are immutable.** `scoreboard_ocr` is write-once. Corrections never overwrite: they go to `state_corrections` (proposed table) and to the answer columns of `scoreboard_flags`, each with reviewer, time and reason (R-SR-15, R-SB-02).
4. **Every state column carries source, confidence and pass** (R-SR-15). Implementation: `pass` is part of the primary key of every state table (one row per pass), and each group of state fields has three companions `<group>_src` (OCR, PBP, CV, manual, derived), `<group>_conf` (0–1) and `<group>_dq` (observed, inferred, carried, imputed, quarantined, R-MD-19). Field-specific flags (`clock_inferred`, `ball_inferred`) say which field of a group was weak. PBP-sourced values carry confidence 1.0 and their provider (R-MD-09).
5. **Two passes per game** (R-SR-13): `blind` (no PBP) and `anchored` (with PBP). The field-by-field diff between them is the CV error estimate for the game, written into the run record. A third value, `pbp_only`, is proposed for games without video so the possession engine (R-PE-01, R-PE-08) uses the same state vocabulary for all D-I games (R-SY-06).
6. **No leakage** (Principle 6): anchored values are known only after the game (`as_of = by_pass` / `post_game`) and are never in-game features.
7. **Replays never change state** (Principle 7): replay frames keep the last live state with `dq = carried`.
8. **Units:** seconds, metres, degrees, m/s, points, counts; video time in milliseconds; no feet or inches in stored values (rule distances are converted: 28 ft = 8.53 m, 6 ft = 1.83 m, 3 ft = 0.91 m).
9. **Court frame:** positions use the attacked-rim frame of `src/msu_alpha/geometry.py` (origin on the floor under the centre of the attacked rim; θ in degrees from the right baseline at the rim centre), as required by R-CG-02. Ranges allow 1 m outside the court (R-DQ-02).
10. **Storage:** Parquet per game and version under `processed/<game_id>/<version>/` on the private Drive (R-EN-07); nothing derived from video or licensed data is committed to the public repo.

## 2. Legend for the column tables

Markers after a column name: **(G)** field of `schema/global_metadata.yaml`, name and meaning unchanged; **(P)** proposed addition to the global metadata (see section 4); **(null ok)** the column may be null, with the reason in its definition.

**Licence class**

| Code | Meaning |
| --- | --- |
| `computed_by_us` | Computed by this project from privately held broadcast video (OCR, CV), audio, manual labels or our pipeline. Private research use; model input allowed internally; never published raw. |
| `model_input_allowed` | Taken from CollegeBasketballData (CBBD): research and commercial use allowed (docs/research/data_sources_catalog.md, row 8). |
| `reference_only` | Taken from ESPN data already pulled, hoopR ESPN prebuilt files or hoopR NCAA-engine files: ESPN terms bar automated collection and data-set compilation, NCAA terms unverified. Reference and cross-checks only until Aldemir decides otherwise. |
| `ROW` | Depends on the row's `pbp_provider`; stored per row in `licence_class` (cbbd → model_input_allowed; espn_pulled, hoopr_espn, hoopr_ncaa → reference_only). |
| `REG` | Inherits the games registry (dictionary_games.md). |

**As-of rule** (when the value is known relative to the moment it describes; relative to tip for pre-game values)

| Code | Meaning |
| --- | --- |
| `at_frame` | Known at the video instant the row describes; usable as an in-game feature at that instant. |
| `by_pass` | Blind pass: `at_frame`. Anchored pass: `post_game`. |
| `post_game` | Known only after the game (PBP published, whole video processed). Training and description only. |
| `post_review` | Known at `reviewed_utc` of the review that set it. |
| `pre_game` | Known before tip (registry). |
| `n/a` | Keys and processing metadata. |

**Source**

| Code | Meaning |
| --- | --- |
| `OCR` | Parsed scoreboard readings (`scoreboard_ocr`). |
| `CV` | Our detection, tracking, ball, rim, net and lane models (dictionary_games.md `frames`, `tracks`). |
| `PBP` | Anchored pass only: CBBD plays, or ESPN play-by-play already pulled / hoopR `load_mbb_pbp`. Exact provider field names per state field are in `docs/data/source_field_map.md` (core workflow); none are asserted here. |
| `fused` | Fusion of OCR, CV and (anchored pass) PBP under the authority order above. |
| `derived` | Computed from other columns of the same table by the rule in the definition. |
| `pipeline` | Keys, versions, lineage written by the processing code. |
| `manual review` | Human reviewer through the review queue (R-HR-02, R-HR-05). |

## 3. Table map

| Table | Grain | Main requirements | Links to core tables |
| --- | --- | --- | --- |
| `state_frame` | frame × pass | R-SR-01, 02, 03, 04, 05, 06, 10, 13, 15; R-MD-01, 02, 08, 12 | `frames`, `possessions`, `chances`, `tracks` (players_on_floor) |
| `state_second` | second × pass (video seconds; game-clock seconds for `pbp_only`) | R-SR-05, 09, 11, 12; R-MD-05, 13, 16, 17; R-PE-04, 07 | `possessions`, `chances` |
| `score_events` | score change × pass | R-SR-02, R-IV-04, R-SB-01, 03 | `events`, `shots` |
| `foul_state` | team or player × bucket × pass | R-SR-03, 11; R-IV-03, 09; R-MD-07, 16 | `fouls`, `rosters` |
| `free_throws` | attempt × pass | R-SR-09, R-IV-11, R-PE-05 | `fouls`, `events` |
| `timeouts` | timeout × pass | R-SR-04, R-IV-10, R-MD-13 | `events` |
| `reviews` | review / challenge / appeal × pass | R-SR-04, R-RF-07, R-SB-01 | `events` |
| `restarts` | dead-to-live transition × pass | R-SR-08, R-MD-03, R-IV-07, 08, R-SY-08, 09 | `possessions`, `events` |
| `scoreboard_ocr` | OCR reading (immutable, pass-free) | R-SY-01, R-SR-15, R-SB-01, 03 | `frames` |
| `scoreboard_flags` | discrepancy or invariant break | R-SB-01..04, R-IV-01..16 | `events` |
| `made_basket_events` | candidate make × pass | R-MB-01..07 | `shots`, `events` |
| `cv_events_unmatched` | CV event with no PBP match (anchored pass) | R-SR-14, R-SY-10 | `events` |
| `state_corrections` | corrected value (proposed addition) | R-SR-15, R-SB-02 | all state tables |

Coverage check (every requirement in the four families has a home):

| Requirement | Where |
| --- | --- |
| R-SR-01 clock | `state_frame` period, game_clock_s, clock_running, clock_inferred, shot_clock_status, shot_clock_s, live_ball |
| R-SR-02 score | `state_frame` score_*, `score_events` |
| R-SR-03 fouls | `state_frame` team_fouls_*, *_bonus_state; `foul_state` (half, period, ten_minute, media_segment buckets; player rows); `state_second` fouls_to_give_* |
| R-SR-04 timeouts, reviews | `state_frame` timeouts_*, to30/60/75_left_*, challenge_available_*, stoppage_kind; `timeouts`; `reviews`; `state_second` media_segment_id |
| R-SR-05 possession | `state_second` phase, secs_since_control_change, possession_arrow; `state_frame` possession columns |
| R-SR-06 ball | `state_frame` ball_* , try_in_flight, ring_contact_this_try |
| R-SR-07 personnel | core `tracks` / positions and stints (dictionary_games.md); `state_frame.players_on_floor` |
| R-SR-08 restarts | `restarts` |
| R-SR-09 free-throw state machine | `state_second` ft_*; `free_throws` |
| R-SR-10 broadcast state | `state_frame` camera_shot_type, reverse_angle, replay_flag, court_visible_frac, court_mapping_conf, scorebug_visible |
| R-SR-11 game situation | `state_second` margin, windows, foul_trouble_*, bonus |
| R-SR-12 expected points | value layer `possession_value`; stamped as `state_second.xpts_possession` |
| R-SR-13 two passes | `pass` key on every state table; diff report in the run record |
| R-SR-14 unmatched CV events | `cv_events_unmatched` |
| R-SR-15 provenance, immutability | `*_src`, `*_conf`, `*_dq`, `pass`; `scoreboard_ocr` write-once; `state_corrections` |
| R-IV-01..16 | `config/invariants.yaml`; breaks in `scoreboard_flags`; per-row `invariant_breaks` |
| R-SB-01..04 | `scoreboard_flags`; lag in `score_events.board_lag_s` and `made_basket_events.cue3_lag_s`; per-game counts in the run record |
| R-MB-01..07 | `made_basket_events`; `ring_contact` on `shots` (core) and `free_throws`; `state_frame.ring_contact_this_try` |
| R-PE-01..13 | state vocabulary shared: `state_second` (incl. `pbp_only`), `free_throws.award_type`, `foul_state`, `timeouts`; the engine's own outputs are core / prediction tables |

## 4. Proposed additions to `schema/global_metadata.yaml` (dated note, 2026-10-18)

No field of `schema/global_metadata.yaml` is renamed or redefined here. The following additions are **proposed** (marked **(P)** in the tables):

| Proposed field | Type | Why |
| --- | --- | --- |
| `pass` | enum [blind, anchored, pbp_only] | R-SR-13, R-SR-15: every state value must say which pass produced it. |
| `video_id` | string | A game can have more than one video file; `frame_index` alone is not unique per game. |
| `shot_clock_status` | enum [on, off, unknown] | R-MD-01 asks for an explicit "off" instead of null; a float cannot hold it. `shot_clock_s` is null only when the status is off or unknown. |
| `msu_bonus_state`, `opp_bonus_state` | enum [none, bonus, double_bonus] | The global `bonus_state` is a single value and does not say whose bonus. Proposed reading of the existing `bonus_state`: the bonus a common foul by the defending team would award now (side of `team_in_possession`); none without team control. |
| `to30_left_*`, `to60_left_*`, `to75_left_*` | int | R-SR-04 asks for timeouts by type; `timeouts_msu` / `timeouts_opp` stay as totals. |
| `challenge_available_msu`, `challenge_available_opp` | bool | R-SR-04 coach's challenge state (Rule 11-4). |
| `possession_arrow` | enum [msu, opponent, none] | R-MD-12 asks for it per frame; it is not yet in the global file. |
| `reverse_angle` (flag) | bool | R-SR-10 lists "reverse angle", which the global `camera_shot_type` enum lacks. Mapping of the other R-SR-10 words onto the existing enum: tight → close_up; ad break → commercial; bench or crowd → bench / crowd. |
| `<group>_src`, `<group>_conf`, `<group>_dq` | enum, float, enum | R-SR-15 field-level provenance; the global `source` and `confidence` stay as row-level summaries. Proposed `source` vocabulary for state: OCR, PBP, CV, manual, derived (`derived` added to R-SR-15's four for values computed from other state fields). |

## 5. Notes on rules that shape the columns (verified in the 2026-27 book)

- **Halves, not quarters.** Two 20-minute halves, 5-minute extra periods (Rule 5-6.1, 5-9.3). Ten-minute and media-segment buckets are analysis buckets only.
- **Team fouls** = personal fouls (including player-control) + Class A technicals (Rule 8-2.3); bonus (one-and-one) from the 7th, double bonus from the 10th (8-2.1, 8-2.2); reset at the second half only, because each extra period is an extension of the second half (5-9.4). Administrative and Class B technicals do not count.
- **Free-throw awards** follow 10-1 Penalty b–e and the technical-foul penalties: Class A technical 2, Class B technical 1, administrative 1 (2 for 10-2.6 and 10-2.7). The live doc's R-SR-09 "technical 2" is refined accordingly (see `config/invariants.yaml` corrections).
- **Timeouts:** in the usual televised format (at least three media timeouts per half, Rule 5-14.10) each team has three 30-second and one 60-second timeout, carries at most two 30-second timeouts into the second half, and gets one more 30-second timeout per extra period. Without media timeouts (5-14.8) it is four 75-second and two 30-second, plus one 75-second per extra period. Media timeouts fall at the first dead ball at or after the 16-, 12-, 8- and 4-minute marks (or 15, 10, 5); a team timeout or review within 30 s before a mark becomes the media timeout (5-14.10.e); missed marks follow A.R. 5-33 (2026-27 interpretations).
- **Coach's challenge** (Rule 11-4, since 2025-26): one per game, a second only after an overturned first, needs a legal timeout, costs it when unsuccessful; the scorer records challenges under the new Rule 2-9.19 (post-clinic interpretations, 15 Oct 2026).
- **Shot clock:** 30 s; flat 20 s after an offensive rebound off the ring (2-11.6.d.1); 20 s or the time left, whichever is greater, after defensive fouls or kicked balls with a frontcourt throw-in (2-11.6.c); full table of causes in `config/invariants.yaml` `shot_clock_reset_table`.
- **Throw-in spot** in the frontcourt: end line 3 ft (0.91 m) outside the lane line, or the 28-foot (8.53 m) sideline mark (7-3.2.b as changed in 2025-26).
- **Second half** starts with an alternating-possession throw-in at the division line opposite the scorers' table (6-3.6); jump balls only start the game and extra periods (6-2.1).

## 6. Tables

One section per table. Columns are listed in storage order.

### state_frame

- **Grain:** one row per decoded video frame per pass (blind, anchored) of a game video.
- **Primary key:** `game_id, video_id, frame_index, pass`
- **Foreign keys:** `game_id` -> games.game_id; `video_id, frame_index` -> frames.(video_id, frame_index); `possession_id` -> possessions.possession_id; `chance_id` -> chances.chance_id; `last_score_event_id` -> score_events.score_event_id
- **Requirements:** R-SR-01, R-SR-02, R-SR-03, R-SR-04, R-SR-05, R-SR-06, R-SR-10, R-SR-13, R-SR-15, R-MD-01, R-MD-02, R-MD-04, R-MD-07, R-MD-08, R-MD-12, R-MD-19, R-IV-01..16
- **Schema file:** `schema/tables/state_frame.yaml` (status: proposed)
- Carries every field of schema/global_metadata.yaml under its exact name (R-MD-01); fields that cannot exist hold an explicit status (shot_clock_status = off), never a silent null.
- Field-level provenance: each state group has <group>_src, <group>_conf, <group>_dq companions. When one field of a group has a different source (e.g. game clock interpolated while score is read), the group companions describe the weakest field and the field-specific flag (clock_inferred, ball_inferred) says which.
- Replay frames (replay_flag = true) keep the last live state, dq = carried; no state change is ever taken from a replay frame (Principle 7, R-VI-04).
- Storage: Parquet under processed/<game_id>/<version>/ (R-EN-07), outside the repo; ~430k frames per pass for a 2-hour 60 fps video.

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `season` (G) | string |  |  | Season label as in the registry (e.g. '2026-27'). | registry/games.csv | REG | pre_game | R-MD-01 |
| `game_type` (G) | enum |  | exhibition, non_conference, big_ten, big_ten_tournament, ncaa_tournament | As in global metadata. | registry/games.csv | REG | pre_game | R-MD-01, R-MD-14 |
| `video_id` (P) | string |  |  | ID of the video file (one game can have several files); FK to the video files / frames tables in dictionary_games.md. | video registry | computed_by_us | at_frame | R-VI-01, R-MD-01 |
| `frame_index` (G) | int |  | 0 to open | 0-based decoded frame number within video_id. | video decode | computed_by_us | at_frame | R-MD-01 |
| `video_ts_ms` (G) | int | ms | 0 to open | Presentation time of the frame from the start of the video file. | video decode (frames table) | computed_by_us | at_frame | R-MD-01, R-MD-08 |
| `pass` (P) | enum |  | blind, anchored | Processing pass: blind uses no PBP; anchored uses PBP. The per-game diff of the two is the CV error estimate (R-SR-13). | pipeline | computed_by_us | n/a | R-SR-13, R-SR-15 |
| `period` (G) | int |  | 1 to 12 | 1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-01, R-IV-16 |
| `game_clock_s` (G) | float | s | 0 to 1200 | Game clock remaining in the period. 0.1 s resolution (board shows tenths under 60 s, Rule 1-18.2; whole seconds above). | fused | computed_by_us | by_pass | R-SR-01, R-IV-05 |
| `clock_running` | bool |  |  | Game clock is running in this frame (from successive readings; Rule 5-10 start and 5-11 stop events). | fused | computed_by_us | by_pass | R-SR-01, R-IV-05, R-IV-06 |
| `clock_inferred` | bool |  |  | Game clock not read in this frame (scorebug hidden, replay, ad break); value interpolated from the last reading. | pipeline | computed_by_us | by_pass | R-SR-01 |
| `shot_clock_status` (P) | enum |  | on, off, unknown | on = shot clock running or stopped with a value; off = turned off because the game clock shows less than a shot-clock period (Rule 2-11.2) or between periods; unknown = not readable and not inferable. | fused | computed_by_us | by_pass | R-SR-01, R-MD-01, R-IV-07 |
| `shot_clock_s` (G) (null ok) | float | s | 0 to 30 | Shot clock value. Null only when shot_clock_status is off or unknown (status carries the explicit value, R-MD-01). Tenths optional under 5 s (Rule 1-19.2). | fused | computed_by_us | by_pass | R-SR-01, R-IV-07, R-MD-06 |
| `live_ball` | bool |  |  | Ball is live (Rule 6-1) vs dead (Rule 6-5). Live from the toss leaving the official's hand / disposal of the thrower-in or free-thrower. | fused | computed_by_us | by_pass | R-SR-01, R-MD-05 |
| `period_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the period value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-01 |
| `period_conf` | float | 0-1 | 0 to 1 | Confidence of the period value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-01 |
| `period_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the period value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-01 |
| `game_clock_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the game clock value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-01 |
| `game_clock_conf` | float | 0-1 | 0 to 1 | Confidence of the game clock value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-01 |
| `game_clock_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the game clock value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-01 |
| `shot_clock_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the shot clock value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-01 |
| `shot_clock_conf` | float | 0-1 | 0 to 1 | Confidence of the shot clock value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-01 |
| `shot_clock_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the shot clock value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-01 |
| `live_ball_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the live/dead value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-01 |
| `live_ball_conf` | float | 0-1 | 0 to 1 | Confidence of the live/dead value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-01 |
| `live_ball_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the live/dead value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-01 |
| `score_msu` (G) | int | points | 0 to 250 | MSU points. | fused | computed_by_us | by_pass | R-SR-02, R-IV-04 |
| `score_opp` (G) | int | points | 0 to 250 | Opponent points. | fused | computed_by_us | by_pass | R-SR-02, R-IV-04 |
| `margin` (G) | int | points | -250 to 250 | score_msu - score_opp. | derived | computed_by_us | by_pass | R-SR-02, R-MD-17 |
| `last_score_event_id` (null ok) | string |  |  | Most recent score_events row at or before this frame. | pipeline | computed_by_us | by_pass | R-SR-02 |
| `score_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the score value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-02 |
| `score_conf` | float | 0-1 | 0 to 1 | Confidence of the score value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-02 |
| `score_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the score value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-02 |
| `team_fouls_msu` (G) | int | count | 0 to 60 | MSU team fouls in the current half (personal incl. player-control + Class A technicals, Rule 8-2.3). Extra periods continue the second-half count (Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-03, R-MD-07, R-IV-09 |
| `team_fouls_opp` (G) | int | count | 0 to 60 | Opponent team fouls, same definition. | fused | computed_by_us | by_pass | R-SR-03, R-MD-07, R-IV-09 |
| `bonus_state` (G) | enum |  | none, bonus, double_bonus | Global field kept as defined. Proposed reading (dated note): the bonus that a common foul by the defending team would award now, i.e. from the side of team_in_possession; none when no team control. Team-specific values are in msu_bonus_state / opp_bonus_state. | derived | computed_by_us | by_pass | R-SR-03, R-MD-07 |
| `msu_bonus_state` (P) | enum |  | none, bonus, double_bonus | MSU shoots bonus free throws: bonus when team_fouls_opp >= 7, double_bonus when >= 10 (Rule 8-2.1, 8-2.2). | derived | computed_by_us | by_pass | R-SR-03, R-SR-11 |
| `opp_bonus_state` (P) | enum |  | none, bonus, double_bonus | Opponent shoots bonus free throws: from team_fouls_msu with the same thresholds. | derived | computed_by_us | by_pass | R-SR-03, R-SR-11 |
| `fouls_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the team-foul and bonus value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-03 |
| `fouls_conf` | float | 0-1 | 0 to 1 | Confidence of the team-foul and bonus value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-03 |
| `fouls_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the team-foul and bonus value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-03 |
| `timeouts_msu` (G) | int | count | 0 to 12 | MSU charged timeouts left, all lengths together (global field). | fused | computed_by_us | by_pass | R-SR-04, R-IV-10, R-MD-07 |
| `timeouts_opp` (G) | int | count | 0 to 12 | Opponent charged timeouts left, all lengths. | fused | computed_by_us | by_pass | R-SR-04, R-IV-10, R-MD-07 |
| `to30_left_msu` (P) | int | count | 0 to 12 | MSU 30-second timeouts left (media format: 3 per game, max 2 carried into the second half, +1 per extra period; Rule 5-14.10). | fused | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `to60_left_msu` (P) | int | count | 0 to 1 | MSU 60-second timeouts left (media format: 1 per game; Rule 5-14.10.b). | fused | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `to75_left_msu` (P) | int | count | 0 to 12 | MSU 75-second timeouts left (non-media formats: 4 per game, +1 per extra period; Rule 5-14.8, 5-14.9). | fused | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `to30_left_opp` (P) | int | count | 0 to 12 | Opponent 30-second timeouts left. | fused | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `to60_left_opp` (P) | int | count | 0 to 1 | Opponent 60-second timeouts left. | fused | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `to75_left_opp` (P) | int | count | 0 to 12 | Opponent 75-second timeouts left. | fused | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `challenge_available_msu` (P) | bool |  |  | MSU head coach may still use a coach's challenge (one per game; a second only after an overturned first; needs a legal timeout; Rule 11-4.1.d-e). | fused | computed_by_us | by_pass | R-SR-04 |
| `challenge_available_opp` (P) | bool |  |  | Same for the opponent. | fused | computed_by_us | by_pass | R-SR-04 |
| `stoppage_kind` | enum |  | none, team_timeout, media_timeout, review, injury, intermission, other_dead | What the current dead ball is, if any. | fused | computed_by_us | by_pass | R-SR-04, R-SR-05 |
| `timeouts_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the timeout, challenge and stoppage value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-04 |
| `timeouts_conf` | float | 0-1 | 0 to 1 | Confidence of the timeout, challenge and stoppage value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-04 |
| `timeouts_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the timeout, challenge and stoppage value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-04 |
| `team_in_possession` (G) | enum |  | msu, opponent, none | Team with team control (Rule 4-9.2), or none (jump ball, try in flight, rebound tap, dead ball; Rule 4-9.4). | fused | computed_by_us | by_pass | R-SR-05, R-MD-04 |
| `possession_id` (G) (null ok) | int |  | 0 to open | Our possession (ends only when the other team gains control); FK possessions. | fused | computed_by_us | by_pass | R-SR-05, R-MD-04 |
| `chance_id` (G) (null ok) | int |  | 0 to open | Chance inside the possession (an offensive rebound starts a new chance); FK chances. | fused | computed_by_us | by_pass | R-SR-05, R-MD-04 |
| `chance_number` (G) (null ok) | int |  | 1 to 20 | 1 for the first chance of a possession, 2 after the first offensive rebound, ... | fused | computed_by_us | by_pass | R-SR-05, R-SY-05 |
| `possession_arrow` (P) | enum |  | msu, opponent, none | Team the alternating-possession arrow favours; none before the opening tip is controlled (Rule 6-3.4). | fused | computed_by_us | by_pass | R-SR-05, R-MD-12 |
| `possession_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the possession, chance and arrow value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-05 |
| `possession_conf` | float | 0-1 | 0 to 1 | Confidence of the possession, chance and arrow value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-05 |
| `possession_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the possession, chance and arrow value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-05 |
| `ball_control_state` (G) | enum |  | msu_ball, opponent_ball, contested, in_flight, inbound_pending, dead | Global six-state label. | fused | computed_by_us | by_pass | R-SR-06, R-MD-02 |
| `ball_handler_player_id` (null ok) | string |  |  | Roster ID of the player in control (Rule 4-9.1); null when no player control. | CV; PBP for anchored identity | computed_by_us | by_pass | R-SR-06, R-BL-02 |
| `ball_x_m` (null ok) | float | m | -8.62 to 8.62 | Ball x in the attacked-rim frame (src/msu_alpha/geometry.py: origin on the floor under the centre of the attacked rim; x across the court). | CV | computed_by_us | at_frame | R-SR-06, R-BL-01 |
| `ball_y_m` (null ok) | float | m | -2.6 to 28.05 | Ball y in the attacked-rim frame (toward half court positive). | CV | computed_by_us | at_frame | R-SR-06, R-BL-01 |
| `ball_z_m` (null ok) | float | m | 0 to 15 | Ball centre height above the floor. | CV | computed_by_us | at_frame | R-SR-06 |
| `ball_r_m` (null ok) | float | m | 0 to 30 | Distance of the ball's floor projection from the attacked rim centre. | derived | computed_by_us | at_frame | R-SR-06 |
| `ball_theta_deg` (null ok) | float | degrees | 0 to 360 | Angle from the right baseline at the rim centre (vocabulary_map.yaml). | derived | computed_by_us | at_frame | R-SR-06 |
| `ball_visible` | bool |  |  | Ball detected in this frame. | CV | computed_by_us | at_frame | R-SR-06 |
| `ball_inferred` | bool |  |  | Ball position is last-known or interpolated (not visible). | pipeline | computed_by_us | at_frame | R-SR-06 |
| `try_in_flight` | bool |  |  | A try for goal is in flight (released, not yet ended; Rule 5-1.12). | CV | computed_by_us | at_frame | R-SR-06, R-IV-07 |
| `ring_contact_this_try` | enum |  | yes, no, unknown, none | For the current or just-ended try: did it touch the ring or flange (needed for 20 s reset, Rule 2-11.6.d.1). | CV; inferred from shot-clock reset | computed_by_us | by_pass | R-SR-06, R-MB-07, R-IV-07 |
| `inbound_side` (G) | enum |  | sideline, baseline, none | Side of a pending throw-in. | fused | computed_by_us | by_pass | R-MD-03, R-SR-08 |
| `basket_attacked` (G) | enum |  | north, south | Basket attacked by team_in_possession in court-fixed terms. | CV | computed_by_us | at_frame | R-MD-01 |
| `players_on_floor` (G) | list[string] |  |  | The 10 roster IDs on court: positions 0-4 MSU, 5-9 opponent, each sorted by roster ID. | PBP substitutions + CV identity | computed_by_us | by_pass | R-SR-07, R-SY-03, R-IV-01 |
| `ball_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the ball state and position value(s) in this row. | pipeline | computed_by_us | at_frame | R-SR-15, R-MD-09, R-SR-06 |
| `ball_conf` | float | 0-1 | 0 to 1 | Confidence of the ball state and position value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | at_frame | R-SR-15, R-MD-09, R-SR-06 |
| `ball_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the ball state and position value(s). | pipeline | computed_by_us | at_frame | R-SR-15, R-MD-19, R-SR-06 |
| `players_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the players-on-floor value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-07 |
| `players_conf` | float | 0-1 | 0 to 1 | Confidence of the players-on-floor value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-07 |
| `players_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the players-on-floor value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-07 |
| `camera_shot_type` (G) | enum |  | main_wide, close_up, replay, slow_motion, crowd, bench, studio, commercial, graphic | Global enum. Mapping of R-SR-10 words: tight -> close_up; ad break -> commercial; bench or crowd -> bench / crowd. reverse_angle proposed as an added value (dated note). | CV | computed_by_us | at_frame | R-SR-10, R-VI-03 |
| `reverse_angle` (P) | bool |  |  | Live shot from a non-main camera angle (R-SR-10 'reverse angle'). | CV | computed_by_us | at_frame | R-SR-10 |
| `replay_flag` | bool |  |  | Frame belongs to a broadcast replay or slow-motion segment. | CV | computed_by_us | at_frame | R-SR-10, R-VI-04 |
| `court_visible_frac` | float | 0-1 | 0 to 1 | Fraction of the court floor area in view. | CV | computed_by_us | at_frame | R-SR-10, R-VI-05 |
| `court_mapping_conf` | float | 0-1 | 0 to 1 | Confidence of the image-to-court homography. | CV | computed_by_us | at_frame | R-SR-10 |
| `scorebug_visible` | bool |  |  | Broadcast scorebug detected. | CV | computed_by_us | at_frame | R-SR-10, R-SY-01 |
| `coverage_score` (G) | float | 0-1 | 0 to 1 | Global coverage score (R-VI-05 formula). | CV | computed_by_us | at_frame | R-VI-05, R-MD-11 |
| `defense_scheme_state` (G) (null ok) | string |  |  | Global field, label from the defense taxonomy; owned by the defense layer, stamped here. | DF layer | computed_by_us | by_pass | R-MD-01 |
| `defense_scheme_confidence` (G) (null ok) | float | 0-1 | 0 to 1 | Global field. | DF layer | computed_by_us | by_pass | R-MD-01 |
| `broadcast_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the broadcast-state value(s) in this row. | pipeline | computed_by_us | at_frame | R-SR-15, R-MD-09, R-SR-10 |
| `broadcast_conf` | float | 0-1 | 0 to 1 | Confidence of the broadcast-state value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | at_frame | R-SR-15, R-MD-09, R-SR-10 |
| `broadcast_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the broadcast-state value(s). | pipeline | computed_by_us | at_frame | R-SR-15, R-MD-19, R-SR-10 |
| `invariant_breaks` | list[string] |  |  | IDs from config/invariants.yaml broken at this frame (empty list when none). | invariant checker | computed_by_us | by_pass | R-IV-01..16, R-HR-01 |
| `flag_ids` | list[string] |  |  | scoreboard_flags rows raised at this frame. | pipeline | computed_by_us | by_pass | R-SB-01 |
| `correction_ids` | list[string] |  |  | state_corrections rows that change a value of this frame (raw values stay as written). | review | computed_by_us | post_review | R-SR-15 |
| `model_version` (G) | string |  |  | Pipeline and model versions that produced the row (semver string per stage, joined). | pipeline | computed_by_us | by_pass | R-MD-09, R-EN-04, R-DQ-04 |
| `source` (G) | string |  |  | Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Row-level confidence: minimum of the field confidences used in the row. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `created_utc` | timestamp | UTC |  | UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07). | pipeline | computed_by_us | n/a (processing metadata) | R-DQ-04, R-EN-07 |

### state_second

- **Grain:** one row per second per pass: per second of video for blind and anchored passes (time_base = video_s); per game-clock second for pbp_only (time_base = game_clock_s).
- **Primary key:** `game_id, pass, time_base, t_index`
- **Foreign keys:** `game_id` -> games.game_id; `possession_id` -> possessions.possession_id; `chance_id` -> chances.chance_id; `ft_sequence_id` -> free_throws.ft_sequence_id
- **Requirements:** R-SR-05, R-SR-09, R-SR-11, R-SR-12, R-SR-13, R-MD-05, R-MD-13, R-MD-16, R-MD-17, R-PE-01, R-PE-04, R-PE-07
- **Schema file:** `schema/tables/state_second.yaml` (status: proposed)
- Video-second rows summarise the 60 (or 30) state_frame rows of that second: state at the first frame plus shares over the second.
- pbp_only rows let the possession engine (R-PE-01, R-PE-08) use the same state vocabulary for all D-I games without video; dead-ball time is invisible there, so live shares are null.
- Window thresholds (two-for-one, foul to extend, last shot, clutch) are proposals stored in config/invariants.yaml constants, never hard-coded (R-EN-06).

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `pass` (P) | enum |  | blind, anchored, pbp_only | blind, anchored, or pbp_only (games or stretches with no video, built from PBP alone for the possession engine, R-SY-06, R-PE-08). | pipeline | computed_by_us | n/a | R-SR-13, R-SR-15, R-SY-06, R-PE-08 |
| `time_base` | enum |  | video_s, game_clock_s | video_s (t_index = whole seconds from video start, per video_id) or game_clock_s (t_index = elapsed game seconds since tip, pbp_only). | pipeline | computed_by_us | n/a | R-SR-05 |
| `t_index` | int | s | 0 to open | Second index in the chosen time base. | pipeline | computed_by_us | n/a | R-SR-05 |
| `video_id` (null ok) | string |  |  | Video file for video_s rows; null for pbp_only. | video registry | computed_by_us | at_frame | R-MD-01 |
| `video_ts_ms_start` (null ok) | int | ms | 0 to open | Video time of the first frame of the second; null for pbp_only. | video decode | computed_by_us | at_frame | R-MD-08 |
| `period` (G) | int |  | 1 to 12 | 1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-01, R-IV-16 |
| `game_clock_s` (G) | float | s | 0 to 1200 | Game clock remaining in the period. 0.1 s resolution (board shows tenths under 60 s, Rule 1-18.2; whole seconds above). | fused | computed_by_us | by_pass | R-SR-01, R-IV-05 |
| `clock_running_share` (null ok) | float | 0-1 | 0 to 1 | Share of the second with the game clock running. | derived | computed_by_us | by_pass | R-SR-01, R-MD-05 |
| `shot_clock_status` | enum |  | on, off, unknown | As in state_frame, at the first frame. | fused | computed_by_us | by_pass | R-SR-01 |
| `shot_clock_s` (null ok) | float | s | 0 to 30 | As in state_frame, at the first frame; null when status off/unknown. | fused | computed_by_us | by_pass | R-SR-01, R-PE-04 |
| `score_msu` | int | points | 0 to 250 | MSU points at the start of the second. | fused | computed_by_us | by_pass | R-SR-02 |
| `score_opp` | int | points | 0 to 250 | Opponent points at the start of the second. | fused | computed_by_us | by_pass | R-SR-02 |
| `margin` | int | points | -250 to 250 | score_msu - score_opp. | derived | computed_by_us | by_pass | R-SR-11, R-MD-17 |
| `team_in_possession` | enum |  | msu, opponent, none | At the start of the second. | fused | computed_by_us | by_pass | R-SR-05 |
| `possession_id` (null ok) | int |  | 0 to open | FK possessions. | fused | computed_by_us | by_pass | R-SR-05, R-MD-04 |
| `chance_id` (null ok) | int |  | 0 to open | FK chances. | fused | computed_by_us | by_pass | R-SR-05 |
| `chance_number` (null ok) | int |  | 1 to 20 | Chance number in the possession. | fused | computed_by_us | by_pass | R-SR-05 |
| `phase` | enum |  | half_court, transition, throw_in, free_throw, jump_ball, timeout, review, other_dead, intermission | Game phase (R-SR-05): half_court, transition (R-TR-08 definition), throw_in, free_throw, jump_ball, timeout, review, other_dead, intermission. | fused | computed_by_us | by_pass | R-SR-05, R-TR-08 |
| `secs_since_control_change` (null ok) | float | s | 0 to 1200 | Game-clock seconds since team_in_possession last changed (live time only). | derived | computed_by_us | by_pass | R-SR-05, R-PE-04 |
| `possession_arrow` | enum |  | msu, opponent, none | Arrow at the start of the second. | fused | computed_by_us | by_pass | R-SR-05, R-MD-12 |
| `share_msu_ball` (null ok) | float | 0-1 | 0 to 1 | Share of the second in state msu_ball (R-MD-05 split; the six shares sum to 1). | derived | computed_by_us | by_pass | R-MD-05 |
| `share_opponent_ball` (null ok) | float | 0-1 | 0 to 1 | Share in opponent_ball. | derived | computed_by_us | by_pass | R-MD-05 |
| `share_contested` (null ok) | float | 0-1 | 0 to 1 | Share in contested. | derived | computed_by_us | by_pass | R-MD-05 |
| `share_in_flight` (null ok) | float | 0-1 | 0 to 1 | Share in in_flight. | derived | computed_by_us | by_pass | R-MD-05 |
| `share_inbound_pending` (null ok) | float | 0-1 | 0 to 1 | Share in inbound_pending. | derived | computed_by_us | by_pass | R-MD-05 |
| `share_dead` (null ok) | float | 0-1 | 0 to 1 | Share in dead. | derived | computed_by_us | by_pass | R-MD-05 |
| `ft_state` | enum |  | none, ft_pending, lane_set, attempt, ft_result, ft_live_rebound | Free-throw state machine (R-SR-09): none, ft_pending (award known, lane not set), lane_set, attempt (ball at shooter's disposal to release), ft_result (attempt ended, another follows), ft_live_rebound (last attempt missed for a personal foul, ball live). | fused | computed_by_us | by_pass | R-SR-09, R-IV-11 |
| `ft_sequence_id` (null ok) | string |  |  | Current free-throw sequence (FK free_throws.ft_sequence_id). | pipeline | computed_by_us | by_pass | R-SR-09 |
| `ft_attempt_k` (null ok) | int |  | 1 to 3 | Attempt number within the sequence. | fused | computed_by_us | by_pass | R-SR-09 |
| `ft_attempts_n` (null ok) | int |  | 1 to 3 | Attempts awarded in the sequence (one-and-one counts 2, conditional). | fused | computed_by_us | by_pass | R-SR-09 |
| `ft_predicted` (null ok) | bool |  |  | At the most recent whistle the system predicted 'free throw coming' (from foul type, shooting act and team-foul count). | state model | computed_by_us | at_frame | R-SR-09 |
| `ft_pred_prob` (null ok) | float | 0-1 | 0 to 1 | Probability behind ft_predicted. | state model | computed_by_us | at_frame | R-SR-09 |
| `team_fouls_msu` | int | count | 0 to 60 | MSU team fouls this half (OT continues the second half). | fused | computed_by_us | by_pass | R-SR-03, R-SR-11 |
| `team_fouls_opp` | int | count | 0 to 60 | Opponent team fouls this half. | fused | computed_by_us | by_pass | R-SR-03, R-SR-11 |
| `msu_bonus_state` | enum |  | none, bonus, double_bonus | As in state_frame. | derived | computed_by_us | by_pass | R-SR-03, R-SR-11 |
| `opp_bonus_state` | enum |  | none, bonus, double_bonus | As in state_frame. | derived | computed_by_us | by_pass | R-SR-03, R-SR-11 |
| `fouls_to_give_msu` | int | count | 0 to 6 | Fouls MSU can commit before the opponent is in the bonus: max(0, 6 - team_fouls_msu). | derived | computed_by_us | by_pass | R-SR-03, R-PE-07 |
| `fouls_to_give_opp` | int | count | 0 to 6 | max(0, 6 - team_fouls_opp). | derived | computed_by_us | by_pass | R-SR-03, R-PE-07 |
| `timeouts_msu` | int | count | 0 to 12 | MSU charged timeouts left. | fused | computed_by_us | by_pass | R-SR-04 |
| `timeouts_opp` | int | count | 0 to 12 | Opponent charged timeouts left. | fused | computed_by_us | by_pass | R-SR-04 |
| `media_segment_id` | string |  |  | Media-timeout segment: H<half>-S<k>, k = number of media timeouts already taken this half (S0 = from 20:00 to the first). Extra periods: OT<n>. Boundaries are the media timeouts actually taken (first dead ball at or after 16:00, 12:00, 8:00, 4:00; Rule 5-14.10.c, A.R. 5-33). | derived + timeouts | computed_by_us | by_pass | R-SR-03, R-SR-04, R-MD-13 |
| `ten_min_bucket_id` | string |  |  | Analysis bucket H1-A (20:00-10:00), H1-B, H2-A, H2-B, OT<n>. NCAA men play halves; these are analysis buckets only (R-SR-03). | derived | computed_by_us | by_pass | R-SR-03 |
| `five_min_window_id` | string |  |  | H<half>-W<1..4>, OT<n> (R-MD-13). | derived | computed_by_us | by_pass | R-MD-13 |
| `last4_flag` | bool |  |  | Game clock <= 240 s in period >= 2. | derived | computed_by_us | by_pass | R-MD-13 |
| `clutch_flag` | bool |  |  | <= 300 s left in period >= 2 and \|margin\| <= 5 (R-MD-13). | derived | computed_by_us | by_pass | R-MD-13 |
| `two_for_one_window` | bool |  |  | Team gains or holds control with the game clock inside config window two_for_one_window_s (proposal [33, 45] s) of any period. | derived | computed_by_us | by_pass | R-SR-11, R-PE-07 |
| `foul_to_extend_window` | bool |  |  | Trailing team on defence, period >= 2, game clock <= config foul_to_extend_clock_s (proposal 60 s), deficit within config foul_to_extend_margin (proposal 1-9). | derived | computed_by_us | by_pass | R-SR-11, R-PE-07 |
| `last_shot_window` | bool |  |  | Team in control and the shot clock is off (game clock below a shot-clock period) or game clock <= shot clock. | derived | computed_by_us | by_pass | R-SR-11, R-PE-07 |
| `foul_trouble_msu` | list[string] |  |  | MSU players in foul trouble: >= 2 personal fouls in the first half, >= 4 in the second half or extra periods (R-SR-11 proposal; config). | derived + foul_state | computed_by_us | by_pass | R-SR-11, R-MD-16, R-PE-06 |
| `foul_trouble_opp` | list[string] |  |  | Same for opponent players. | derived + foul_state | computed_by_us | by_pass | R-SR-11, R-MD-16, R-PE-06 |
| `lead_changes` | int | count | 0 to 100 | Lead changes so far in the game. | derived | computed_by_us | by_pass | R-MD-17 |
| `run_msu_2min` | int | points | 0 to 40 | MSU points in the last 120 game-clock seconds. | derived | computed_by_us | by_pass | R-MD-17 |
| `run_opp_2min` | int | points | 0 to 40 | Opponent points in the last 120 game-clock seconds. | derived | computed_by_us | by_pass | R-MD-17 |
| `xpts_possession` (null ok) | float | points | 0 to 6 | Expected points of the current possession (value owned by the possession_value table, R-SR-12; stamped here). | value layer | computed_by_us | by_pass | R-SR-12 |
| `clock_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the clock value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-01 |
| `clock_conf` | float | 0-1 | 0 to 1 | Confidence of the clock value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-01 |
| `clock_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the clock value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-01 |
| `possession_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the possession and phase value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-05 |
| `possession_conf` | float | 0-1 | 0 to 1 | Confidence of the possession and phase value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-05 |
| `possession_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the possession and phase value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-05 |
| `fouls_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the foul and bonus value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-03 |
| `fouls_conf` | float | 0-1 | 0 to 1 | Confidence of the foul and bonus value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-03 |
| `fouls_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the foul and bonus value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-03 |
| `ft_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the free-throw state value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-09 |
| `ft_conf` | float | 0-1 | 0 to 1 | Confidence of the free-throw state value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-09 |
| `ft_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the free-throw state value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-09 |
| `invariant_breaks` | list[string] |  |  | Invariant IDs broken in this second. | invariant checker | computed_by_us | by_pass | R-IV-01..16 |
| `model_version` (G) | string |  |  | Pipeline and model versions that produced the row (semver string per stage, joined). | pipeline | computed_by_us | by_pass | R-MD-09, R-EN-04, R-DQ-04 |
| `source` (G) | string |  |  | Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Row-level confidence: minimum of the field confidences used in the row. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `created_utc` | timestamp | UTC |  | UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07). | pipeline | computed_by_us | n/a (processing metadata) | R-DQ-04, R-EN-07 |

### score_events

- **Grain:** one row per change of either team's score per pass, including official and scorer corrections as their own rows.
- **Primary key:** `score_event_id`
- **Foreign keys:** `game_id` -> games.game_id; `made_basket_event_id` -> made_basket_events.make_id; `free_throw_id` -> free_throws.free_throw_id; `shot_id` -> shots.shot_id; `pbp_event_id` -> events.event_id; `review_id` -> reviews.review_id
- **Requirements:** R-SR-02, R-IV-04, R-SB-01, R-SB-03, R-MB-01, R-DQ-06
- **Schema file:** `schema/tables/score_events.yaml` (status: proposed)
- Sum of delta_points per team equals the final score of the box score (R-IV-04, R-DQ-06).
- A correction (board fixed during a timeout or review) is a row with event_kind official_correction or scorer_correction and a signed delta; the earlier wrong row is never edited.

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `score_event_id` | string |  |  | game_id + pass + seq. | pipeline | computed_by_us | n/a | R-SR-02 |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `pass` (P) | enum |  | blind, anchored | Processing pass: blind uses no PBP; anchored uses PBP. The per-game diff of the two is the CV error estimate (R-SR-13). | pipeline | computed_by_us | n/a | R-SR-13, R-SR-15 |
| `seq` | int |  | 1 to 400 | Order of the score change in the game for this pass. | pipeline | computed_by_us | by_pass | R-SR-02 |
| `period` (G) | int |  | 1 to 12 | 1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-01, R-IV-16 |
| `game_clock_s` (G) | float | s | 0 to 1200 | Game clock remaining in the period. 0.1 s resolution (board shows tenths under 60 s, Rule 1-18.2; whole seconds above). | fused | computed_by_us | by_pass | R-SR-01, R-IV-05 |
| `video_ts_ms` (null ok) | int | ms | 0 to open | Video time of the make (ball through the net) or of the board change for awarded points / corrections. | CV; OCR | computed_by_us | at_frame | R-SR-02, R-SB-03 |
| `frame_index` (null ok) | int |  | 0 to open | Frame of video_ts_ms. | video decode | computed_by_us | at_frame | R-SR-02 |
| `team` | enum |  | msu, opponent | Team credited with the points. | fused | computed_by_us | by_pass | R-SR-02 |
| `delta_points` | int | points | -3 to 3 | Signed change: +1, +2, +3 for scores; negative only for corrections. | fused | computed_by_us | by_pass | R-SR-02, R-IV-04 |
| `event_kind` | enum |  | field_goal, free_throw, awarded_goaltending, awarded_basket_interference, own_basket_credit, illegal_assistance_award, official_correction, scorer_correction | field_goal, free_throw, awarded_goaltending, awarded_basket_interference (Rule 9-15 penalty), own_basket_credit (ball into own basket counts 2 for the opponent, Rule 5-1.4.a), illegal_assistance_award (Rule 9-16.1.c), official_correction, scorer_correction. | fused | computed_by_us | by_pass | R-SR-02, R-IV-04, R-MB-05 |
| `score_msu_after` | int | points | 0 to 250 | MSU score after the event. | fused | computed_by_us | by_pass | R-SR-02 |
| `score_opp_after` | int | points | 0 to 250 | Opponent score after the event. | fused | computed_by_us | by_pass | R-SR-02 |
| `scorer_player_id` (null ok) | string |  |  | Credited player; null for own-basket credit (not credited to a player, Rule 5-1.4.a) and corrections. | PBP; CV identity in blind pass | ROW | by_pass | R-SR-02 |
| `made_basket_event_id` (null ok) | string |  |  | FK made_basket_events for field goals. | pipeline | computed_by_us | by_pass | R-MB-01 |
| `free_throw_id` (null ok) | string |  |  | FK free_throws for free throws. | pipeline | computed_by_us | by_pass | R-SR-09 |
| `shot_id` (null ok) | string |  |  | FK shots (dictionary_games.md). | pipeline | computed_by_us | by_pass | R-EV-07 |
| `review_id` (null ok) | string |  |  | FK reviews when the event comes from or was changed by a review. | pipeline | computed_by_us | by_pass | R-SB-01 |
| `seen_ocr` | bool |  |  | Board score change observed. | OCR | computed_by_us | at_frame | R-SB-01 |
| `seen_cv` | bool |  |  | Vision make cue present (made_basket_events). | CV | computed_by_us | at_frame | R-SB-01, R-MB-01 |
| `seen_pbp` | bool |  |  | PBP scoring play matched (anchored pass). | PBP | ROW | post_game | R-SB-01 |
| `ocr_change_video_ts_ms` (null ok) | int | ms | 0 to open | Video time the board score changed. | OCR | computed_by_us | at_frame | R-SB-03 |
| `board_lag_s` (null ok) | float | s | -5 to 120 | ocr_change_video_ts_ms minus make video time; the per-game distribution is the lag table (R-SB-03). | derived | computed_by_us | at_frame | R-SB-03 |
| `flag_ids` | list[string] |  |  | scoreboard_flags raised for this event. | pipeline | computed_by_us | by_pass | R-SB-01 |
| `score_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the score event value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-02 |
| `score_conf` | float | 0-1 | 0 to 1 | Confidence of the score event value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-02 |
| `score_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the score event value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-02 |
| `pbp_provider` | enum |  | cbbd, espn_pulled, hoopr_espn, hoopr_ncaa, none | Provider of the PBP row this record was matched to or built from; 'none' in the blind pass. | pipeline | computed_by_us | post_game | R-DQ-01, R-DQ-04, R-SR-15 |
| `pbp_event_id` (null ok) | string |  |  | Key of the matched row in the events table (dictionary_games.md), which keeps the provider's own play ID. | PBP | ROW | post_game | R-SY-02, R-SY-10 |
| `licence_class` | enum |  | computed_by_us, model_input_allowed, reference_only | Licence class of the PBP-derived values in this row (computed_by_us when no PBP value is used). | pipeline from pbp_provider | computed_by_us | n/a | R-DQ-04 |
| `model_version` (G) | string |  |  | Pipeline and model versions that produced the row (semver string per stage, joined). | pipeline | computed_by_us | by_pass | R-MD-09, R-EN-04, R-DQ-04 |
| `source` (G) | string |  |  | Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Row-level confidence: minimum of the field confidences used in the row. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `created_utc` | timestamp | UTC |  | UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07). | pipeline | computed_by_us | n/a (processing metadata) | R-DQ-04, R-EN-07 |

### foul_state

- **Grain:** one row per game, pass, team, subject (team or one player) and bucket (half, period, ten_minute, media_segment, game).
- **Primary key:** `game_id, pass, team, subject_id, bucket_type, bucket_id`
- **Foreign keys:** `game_id` -> games.game_id; `subject_id` -> rosters.player_id (when not '_team')
- **Requirements:** R-SR-03, R-SR-11, R-IV-03, R-IV-09, R-MD-07, R-MD-16, R-RF-03, R-PE-06, R-PE-07
- **Schema file:** `schema/tables/foul_state.yaml` (status: proposed)
- Team rows: subject_id = '_team'. Player rows: personal fouls per player per bucket (R-SR-03 'personal fouls per player').
- bucket_type 'half' is the rule bucket (team fouls and bonus; H2 includes extra periods, Rule 5-9.4). 'period' splits extra periods out for analysis. 'ten_minute' and 'media_segment' are analysis buckets only.
- Individual fouls live in the fouls table (dictionary_games.md); this table is the state roll-up and must recompute from it (R-SR-11 test).

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `pass` (P) | enum |  | blind, anchored, pbp_only | blind, anchored, or pbp_only (games or stretches with no video, built from PBP alone for the possession engine, R-SY-06, R-PE-08). | pipeline | computed_by_us | n/a | R-SR-13, R-SR-15, R-SY-06, R-PE-08 |
| `team` | enum |  | msu, opponent | Team that committed the fouls. | fused | computed_by_us | by_pass | R-SR-03 |
| `subject_id` | string |  |  | '_team' for the team row, else roster player ID. | pipeline | computed_by_us | by_pass | R-SR-03, R-MD-16 |
| `bucket_type` | enum |  | half, period, ten_minute, media_segment, game | half, period, ten_minute, media_segment, game. | pipeline | computed_by_us | n/a | R-SR-03 |
| `bucket_id` | string |  |  | H1, H2 (incl. OT) \| P1, P2, OT1.. \| H1-A, H1-B, H2-A, H2-B, OT<n> \| H<h>-S<k>, OT<n> \| G. | pipeline | computed_by_us | n/a | R-SR-03, R-MD-13 |
| `bucket_start_clock_s` | float | s | 0 to 1200 | Game clock at bucket start (media segments: clock when the media timeout was taken). | derived | computed_by_us | by_pass | R-SR-03 |
| `bucket_end_clock_s` | float | s | 0 to 1200 | Game clock at bucket end. | derived | computed_by_us | by_pass | R-SR-03 |
| `team_fouls_start` | int | count | 0 to 60 | Team-foul total at bucket start (half rule count). | derived | computed_by_us | by_pass | R-SR-03, R-IV-09 |
| `team_fouls_end` | int | count | 0 to 60 | Team-foul total at bucket end. | derived | computed_by_us | by_pass | R-SR-03, R-IV-09 |
| `fouls_team_total` | int | count | 0 to 60 | Fouls in the bucket that count toward the team-foul total: personal (incl. player-control) + Class A technical (Rule 8-2.3). | fused | computed_by_us | by_pass | R-SR-03, R-IV-09 |
| `personal_fouls` | int | count | 0 to 60 | All personal fouls (Rule 4-15.2). | fused | computed_by_us | by_pass | R-SR-03 |
| `shooting_fouls` | int | count | 0 to 60 | Personal fouls on a player in the act of shooting. | fused | computed_by_us | by_pass | R-SR-03, R-RF-03 |
| `common_nonshooting_fouls` | int | count | 0 to 60 | Common fouls not on a shooter and not player/team-control. | fused | computed_by_us | by_pass | R-SR-03 |
| `player_control_fouls` | int | count | 0 to 60 | Player-control fouls (offensive, Rule 4-15.2.a.1). | fused | computed_by_us | by_pass | R-SR-03 |
| `team_control_fouls` | int | count | 0 to 60 | Team-control fouls that are not loose-ball fouls (Rule 4-15.2.a.2). | fused | computed_by_us | by_pass | R-SR-03 |
| `loose_ball_fouls` | int | count | 0 to 60 | Loose-ball fouls (Rule 4-15.2.a.3; on an offensive player also team-control but bonus-eligible). | fused | computed_by_us | by_pass | R-SR-03 |
| `flagrant1_fouls` | int | count | 0 to 10 | Flagrant 1 personal fouls. | fused | computed_by_us | by_pass | R-SR-03 |
| `flagrant2_fouls` | int | count | 0 to 10 | Flagrant 2 personal fouls. | fused | computed_by_us | by_pass | R-SR-03 |
| `double_simultaneous_fouls` | int | count | 0 to 20 | Fouls that are part of a double or simultaneous foul (no free throws, Rule 10-1 Penalty f). | fused | computed_by_us | by_pass | R-SR-03 |
| `technical_class_a` | int | count | 0 to 10 | Class A technical fouls (count toward team fouls and disqualification). | fused | computed_by_us | by_pass | R-SR-03 |
| `technical_class_b` | int | count | 0 to 10 | Class B technical fouls (no team-foul count; 1 free throw). | fused | computed_by_us | by_pass | R-SR-03 |
| `technical_admin` | int | count | 0 to 10 | Administrative technical fouls (no team-foul count). | fused | computed_by_us | by_pass | R-SR-03 |
| `bonus_reached_clock_s` (null ok) | float | s | 0 to 1200 | Game clock when this team's 7th team foul of the half put the opponent in the bonus (half buckets only). | derived | computed_by_us | by_pass | R-SR-03, R-MD-07 |
| `double_bonus_reached_clock_s` (null ok) | float | s | 0 to 1200 | Game clock of the 10th team foul of the half. | derived | computed_by_us | by_pass | R-SR-03, R-MD-07 |
| `fouls_to_give_start` | int | count | 0 to 6 | max(0, 6 - team_fouls_start). | derived | computed_by_us | by_pass | R-SR-03 |
| `fta_conceded` | int | count | 0 to 80 | Free-throw attempts awarded to the opponent from these fouls. | derived + free_throws | computed_by_us | by_pass | R-SR-03, R-SR-09 |
| `ft_points_conceded` | int | points | 0 to 80 | Opponent free-throw points from these fouls. | derived + free_throws | computed_by_us | by_pass | R-SR-03 |
| `personal_fouls_player_cum` (null ok) | int | count | 0 to 5 | Player rows: personal + Class A technical fouls so far in the game at bucket end (disqualification at 5, Rule 4-12.1). | derived | computed_by_us | by_pass | R-SR-03, R-MD-16, R-IV-03 |
| `flagrant1_player_cum` (null ok) | int | count | 0 to 3 | Player rows: Flagrant 1 fouls so far (disqualification at 3, Rule 4-12.1). | derived | computed_by_us | by_pass | R-IV-03 |
| `disqualified` (null ok) | bool |  |  | Player rows: player disqualified or ejected by bucket end. | derived | computed_by_us | by_pass | R-IV-03 |
| `foul_trouble` (null ok) | bool |  |  | Player rows: in foul trouble at bucket end (R-SR-11 thresholds in config). | derived | computed_by_us | by_pass | R-SR-11, R-MD-16 |
| `box_score_match` (null ok) | bool |  |  | Half and game buckets: counts equal the box score (R-SR-03 test). | cross-check | computed_by_us | post_game | R-SR-03, R-DQ-06 |
| `fouls_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the foul count value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-03 |
| `fouls_conf` | float | 0-1 | 0 to 1 | Confidence of the foul count value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-03 |
| `fouls_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the foul count value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-03 |
| `pbp_provider` | enum |  | cbbd, espn_pulled, hoopr_espn, hoopr_ncaa, none | Provider of the PBP row this record was matched to or built from; 'none' in the blind pass. | pipeline | computed_by_us | post_game | R-DQ-01, R-DQ-04, R-SR-15 |
| `pbp_event_id` (null ok) | string |  |  | Key of the matched row in the events table (dictionary_games.md), which keeps the provider's own play ID. | PBP | ROW | post_game | R-SY-02, R-SY-10 |
| `licence_class` | enum |  | computed_by_us, model_input_allowed, reference_only | Licence class of the PBP-derived values in this row (computed_by_us when no PBP value is used). | pipeline from pbp_provider | computed_by_us | n/a | R-DQ-04 |
| `model_version` (G) | string |  |  | Pipeline and model versions that produced the row (semver string per stage, joined). | pipeline | computed_by_us | by_pass | R-MD-09, R-EN-04, R-DQ-04 |
| `source` (G) | string |  |  | Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Row-level confidence: minimum of the field confidences used in the row. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `created_utc` | timestamp | UTC |  | UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07). | pipeline | computed_by_us | n/a (processing metadata) | R-DQ-04, R-EN-07 |

### free_throws

- **Grain:** one row per free-throw attempt (including attempts cancelled by a violation and a one-and-one second attempt not taken) per pass.
- **Primary key:** `free_throw_id`
- **Foreign keys:** `game_id` -> games.game_id; `foul_id` -> fouls.foul_id; `pbp_event_id` -> events.event_id; `score_event_id` -> score_events.score_event_id
- **Requirements:** R-SR-09, R-IV-11, R-PE-05, R-RF-03, R-SR-03
- **Schema file:** `schema/tables/free_throws.yaml` (status: proposed)
- ft_sequence_id groups the attempts of one award; for false double / multiple fouls each foul has its own sequence (Rule 10-1 Penalty g).
- award_type follows Rule 10-1 Penalty b-e, 8-2, 10-2, 10-3, 10-4. The live doc's 'technical 2' is refined: Class A = 2, Class B = 1, administrative = 1 (2 for Rule 10-2.6 and 10-2.7).
- One-and-one: attempts_n = 2 with second_attempt_conditional = true; the second row exists with result not_attempted when the first misses (makes accounting complete).

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `free_throw_id` | string |  |  | game_id + pass + ft_sequence_id + attempt_k. | pipeline | computed_by_us | n/a | R-SR-09 |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `pass` (P) | enum |  | blind, anchored | Processing pass: blind uses no PBP; anchored uses PBP. The per-game diff of the two is the CV error estimate (R-SR-13). | pipeline | computed_by_us | n/a | R-SR-13, R-SR-15 |
| `ft_sequence_id` | string |  |  | One free-throw award (one foul's penalty). | pipeline | computed_by_us | by_pass | R-SR-09 |
| `attempt_k` | int |  | 1 to 3 | Attempt number within the sequence. | fused | computed_by_us | by_pass | R-SR-09, R-IV-11 |
| `attempts_n` | int |  | 1 to 3 | Attempts in the award (1, 2 or 3; one-and-one = 2 conditional). Name as in source_field_map.md 2.10 (hoopR NCAA ft_attempts). | fused | computed_by_us | by_pass | R-SR-09, R-IV-11 |
| `second_attempt_conditional` | bool |  |  | True for one_and_one (second only if the first is made, Rule 8-2.1). | derived | computed_by_us | by_pass | R-SR-09 |
| `award_type` | enum |  | shooting_2, shooting_3, and_one, one_and_one, double_bonus, flagrant1, flagrant2, technical_class_a, technical_class_b, technical_admin_1, technical_admin_2, multiple_foul, substitute_ft | Why the free throws were awarded (see notes). | fused | computed_by_us | by_pass | R-SR-09, R-IV-11 |
| `rule_ref` | string |  |  | Rule that sets the award, e.g. '10-1 Penalty d.1'. | config/invariants.yaml mapping | computed_by_us | by_pass | R-SR-09 |
| `ball_after` | enum |  | live, throw_in_opponent, throw_in_shooting_team, point_of_interruption, next_sequence, dead_other | What follows the last attempt: live (missed last FT for a personal foul, Rule 8-7), throw_in_opponent (made last FT, Rule 7-3.1.c), throw_in_shooting_team (flagrant, Rule 8-6.1.c), point_of_interruption (technical, Rule 8-6.1.b), next_sequence. | fused | computed_by_us | by_pass | R-SR-09, R-IV-08 |
| `team` | enum |  | msu, opponent | Shooting team. | fused | computed_by_us | by_pass | R-SR-09 |
| `shooter_player_id` | string |  |  | Player attempting (source_field_map.md 2.10 calls it shooter_id). | PBP; CV identity in blind pass | ROW | by_pass | R-SR-09, R-PE-05 |
| `shooter_selection` | enum |  | offended_player, substitute_for_offended, opponent_coach_choice, own_coach_choice, designated_any | offended_player, substitute_for_offended (Rule 8-3.2), opponent_coach_choice (injured, Rule 8-3.3), designated_any (technical, Rule 8-3.4). | fused | computed_by_us | by_pass | R-SR-09 |
| `foul_id` (null ok) | string |  |  | FK fouls (dictionary_games.md). | pipeline | computed_by_us | by_pass | R-RF-03 |
| `fouling_player_id` (null ok) | string |  |  | Player charged with the foul (null for bench or team technicals). | PBP | ROW | by_pass | R-RF-03 |
| `period` (G) | int |  | 1 to 12 | 1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-01, R-IV-16 |
| `game_clock_s` (G) | float | s | 0 to 1200 | Game clock remaining in the period. 0.1 s resolution (board shows tenths under 60 s, Rule 1-18.2; whole seconds above). | fused | computed_by_us | by_pass | R-SR-01, R-IV-05 |
| `team_fouls_defence_at_foul` | int | count | 0 to 60 | Fouling team's team-foul total including this foul. | fused | computed_by_us | by_pass | R-SR-03, R-SR-09 |
| `video_ts_ms_disposal` (null ok) | int | ms | 0 to open | Ball placed at the shooter's disposal (attempt starts, Rule 8-1.3). | CV | computed_by_us | at_frame | R-SR-09 |
| `video_ts_ms_release` (null ok) | int | ms | 0 to open | Ball released. | CV | computed_by_us | at_frame | R-SR-09 |
| `release_latency_s` (null ok) | float | s | 0 to 30 | Release minus disposal; must be <= 10 s (Rule 8-5.1.a). | derived | computed_by_us | at_frame | R-IV-11 |
| `result` | enum |  | made, missed, cancelled_violation, substitute_awarded, not_attempted | made, missed, cancelled_violation (shooting team violated, Rule 9-1 Penalty a), substitute_awarded (opponent violation on a miss, Penalty b.2), not_attempted (one-and-one second after a miss). | fused | computed_by_us | by_pass | R-SR-09 |
| `made` | bool |  |  | result == 'made' (convenience column named as in source_field_map.md 2.10). | derived | computed_by_us | by_pass | R-SR-09, R-PE-05 |
| `ring_contact` | enum |  | yes, no, unknown | Attempt touched ring or flange (a free throw must, Rule 8-5.1.a). | CV | computed_by_us | at_frame | R-MB-07 |
| `lane_def_count` (null ok) | int | count | 0 to 4 | Opponents of the shooter in marked lane spaces (max 4, Rule 8-4.4). | CV | computed_by_us | at_frame | R-SR-09, R-IV-11 |
| `lane_off_count` (null ok) | int | count | 0 to 2 | Teammates of the shooter in marked lane spaces (max 2). | CV | computed_by_us | at_frame | R-SR-09, R-IV-11 |
| `lane_occupant_ids` | list[string] |  |  | Roster IDs by lane space, ordered L1..L4 left then R1..R4 right from the basket out; empty string for an empty space. | CV | computed_by_us | at_frame | R-SR-09 |
| `lane_expected_empty` | bool |  |  | Lane players not expected: ball dead regardless of result (Rule 8-4.8), double foul with one flagrant (10-1 Penalty f), or resumption of play (Rule 4-32). | derived | computed_by_us | by_pass | R-IV-11 |
| `violation` | enum |  | none, a_10s, b_fake, c_line, d_semicircle, e_lane_early, f_disconcert, g_behind_line, h_lane_plane, i_foot_beyond, j_too_many, k_block_space_empty, l_teammate_low_space | Free-throw violation code (Rule 9-1.1.a-l) or none. | CV; PBP | computed_by_us | by_pass | R-IV-11 |
| `violation_team` | enum |  | msu, opponent, none | Team that violated. | fused | computed_by_us | by_pass | R-IV-11 |
| `predicted_at_whistle` (null ok) | bool |  |  | The state model predicted 'free throws coming' at the foul whistle (R-SR-09). | state model | computed_by_us | at_frame | R-SR-09 |
| `predicted_award_type` (null ok) | enum |  | shooting_2, shooting_3, and_one, one_and_one, double_bonus, flagrant1, flagrant2, technical_class_a, technical_class_b, technical_admin_1, technical_admin_2, multiple_foul, substitute_ft, none | Predicted award type at the whistle. | state model | computed_by_us | at_frame | R-SR-09 |
| `prediction_correct` (null ok) | bool |  |  | Prediction matched the actual award. | derived | computed_by_us | post_game | R-SR-09 |
| `lane_formation_confirmed` (null ok) | bool |  |  | Lane formation seen in video confirmed the free-throw state before disposal. | CV | computed_by_us | at_frame | R-SR-09 |
| `score_event_id` (null ok) | string |  |  | FK score_events when made. | pipeline | computed_by_us | by_pass | R-SR-02 |
| `ft_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the free-throw value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-09 |
| `ft_conf` | float | 0-1 | 0 to 1 | Confidence of the free-throw value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-09 |
| `ft_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the free-throw value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-09 |
| `pbp_provider` | enum |  | cbbd, espn_pulled, hoopr_espn, hoopr_ncaa, none | Provider of the PBP row this record was matched to or built from; 'none' in the blind pass. | pipeline | computed_by_us | post_game | R-DQ-01, R-DQ-04, R-SR-15 |
| `pbp_event_id` (null ok) | string |  |  | Key of the matched row in the events table (dictionary_games.md), which keeps the provider's own play ID. | PBP | ROW | post_game | R-SY-02, R-SY-10 |
| `licence_class` | enum |  | computed_by_us, model_input_allowed, reference_only | Licence class of the PBP-derived values in this row (computed_by_us when no PBP value is used). | pipeline from pbp_provider | computed_by_us | n/a | R-DQ-04 |
| `model_version` (G) | string |  |  | Pipeline and model versions that produced the row (semver string per stage, joined). | pipeline | computed_by_us | by_pass | R-MD-09, R-EN-04, R-DQ-04 |
| `source` (G) | string |  |  | Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Row-level confidence: minimum of the field confidences used in the row. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `created_utc` | timestamp | UTC |  | UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07). | pipeline | computed_by_us | n/a (processing metadata) | R-DQ-04, R-EN-07 |

### timeouts

- **Grain:** one row per stoppage that is a timeout: team-charged, media, injury-charged, appeal- or challenge-charged, excessive; one row per (game, pass, timeout_seq).
- **Primary key:** `timeout_id`
- **Foreign keys:** `game_id` -> games.game_id; `review_id` -> reviews.review_id; `pbp_event_id` -> events.event_id
- **Requirements:** R-SR-04, R-IV-10, R-MD-07, R-MD-13, R-PE-07
- **Schema file:** `schema/tables/timeouts.yaml` (status: proposed)
- Media format per game (media_format) decides the allotment: at_least_3_media (Rule 5-14.10: three 30 s + one 60 s; at most two 30 s carried into the second half; +1 x 30 s per extra period), fewer_than_3_media (5-14.9) or no_media (5-14.8: four 75 s + two 30 s; +1 x 75 s per extra period).
- Read from PBP where available; the live doc says the format depends on the media agreement per game.

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `timeout_id` | string |  |  | game_id + pass + timeout_seq. | pipeline | computed_by_us | n/a | R-SR-04 |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `pass` (P) | enum |  | blind, anchored, pbp_only | blind, anchored, or pbp_only (games or stretches with no video, built from PBP alone for the possession engine, R-SY-06, R-PE-08). | pipeline | computed_by_us | n/a | R-SR-13, R-SR-15, R-SY-06, R-PE-08 |
| `timeout_seq` | int |  | 1 to 60 | Order in the game. | pipeline | computed_by_us | by_pass | R-SR-04 |
| `period` (G) | int |  | 1 to 12 | 1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-01, R-IV-16 |
| `game_clock_s` (G) | float | s | 0 to 1200 | Game clock remaining in the period. 0.1 s resolution (board shows tenths under 60 s, Rule 1-18.2; whole seconds above). | fused | computed_by_us | by_pass | R-SR-01, R-IV-05 |
| `video_ts_ms_start` (null ok) | int | ms | 0 to open | Video time the timeout starts (official signals). | CV; OCR | computed_by_us | at_frame | R-SR-04 |
| `video_ts_ms_end` (null ok) | int | ms | 0 to open | Video time play resumes (ball live). | CV; OCR | computed_by_us | at_frame | R-SR-04 |
| `duration_s` (null ok) | float | s | 0 to 1200 | Real time of the stoppage. | derived | computed_by_us | at_frame | R-SR-04 |
| `media_format` | enum |  | at_least_3_media, fewer_than_3_media, no_media, unknown | Game's timeout format. | PBP + registry broadcast | computed_by_us | pre_game | R-SR-04, R-IV-10 |
| `media_marks` | enum |  | 16_12_8_4, 15_10_5, agreement_other, none | Media marks in use. | PBP + OCR | computed_by_us | pre_game | R-SR-04, R-MD-13 |
| `timeout_type` | enum |  | team_30, team_60, team_75, media, injury_charged, appeal_charged, challenge, excessive, official_stoppage | team_30, team_60, team_75, media, injury_charged, appeal_charged (Rule 11-5), challenge (Rule 11-4), excessive (Rule 5-17), official_stoppage (not charged). Name as in source_field_map.md 2.12; its coarse values map: short -> team_30, full -> team_60 or team_75 by media_format, media/OfficialTVTimeOut -> media, official -> official_stoppage. | fused | computed_by_us | by_pass | R-SR-04 |
| `team` | enum |  | msu, opponent, none | Team that called or is charged; none for media and official stoppages. | fused | computed_by_us | by_pass | R-SR-04 |
| `called_by` | enum |  | head_coach, player, official, media, unknown | Who requested it. | fused | computed_by_us | by_pass | R-SR-04 |
| `requesting_player_id` (null ok) | string |  |  | Player who requested, when a player did. | PBP; CV | ROW | by_pass | R-SR-04 |
| `charged` | bool |  |  | Charged to the team (false for media, official stoppages, successful challenges, injury rules of Rule 5-16). | fused | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `became_media` | bool |  |  | Team timeout converted into the media timeout (first dead ball at or after a mark, within 30 s before a mark, or first team timeout of the second half; Rule 5-14.10.d-e). | fused | computed_by_us | by_pass | R-SR-04, R-MD-13 |
| `media_slot` | string |  |  | H<half>-<mark> (e.g. H1-16, H2-4), H2-first_team, OT<n>-first, or none. | derived | computed_by_us | by_pass | R-SR-04, R-MD-13 |
| `mark_clock_s` (null ok) | float | s | 0 to 1200 | Game-clock value of the media mark this timeout serves (960, 720, 480, 240 for 16/12/8/4). | derived | computed_by_us | by_pass | R-SR-04 |
| `first_dead_ball_after_mark` (null ok) | bool |  |  | Media timeout taken at the first dead ball at or after its mark (Rule 5-14.10.c). | derived | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `shortened` | bool |  |  | Timeout shortened by the requesting team (Rule 5-14.14). | fused | computed_by_us | by_pass | R-SR-04 |
| `left_after_msu` | int | count | 0 to 12 | MSU charged timeouts left after this row (all lengths). | fused | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `left_after_opp` | int | count | 0 to 12 | Opponent charged timeouts left after this row. | fused | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `halftime_carry_loss` (null ok) | int | count | 0 to 3 | 30 s timeouts lost at half because only two carry over (Rule 5-14.10.a.1); recorded on a synthetic row at period 2 start. | derived | computed_by_us | by_pass | R-IV-10 |
| `ato_set_instance_id` (null ok) | string |  |  | After-timeout set started at the next live ball (link to sets layer). | ST layer | computed_by_us | by_pass | R-SR-08 |
| `review_id` (null ok) | string |  |  | Linked review for challenge or appeal timeouts. | pipeline | computed_by_us | by_pass | R-SR-04 |
| `timeouts_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the timeout value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-04 |
| `timeouts_conf` | float | 0-1 | 0 to 1 | Confidence of the timeout value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-04 |
| `timeouts_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the timeout value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-04 |
| `pbp_provider` | enum |  | cbbd, espn_pulled, hoopr_espn, hoopr_ncaa, none | Provider of the PBP row this record was matched to or built from; 'none' in the blind pass. | pipeline | computed_by_us | post_game | R-DQ-01, R-DQ-04, R-SR-15 |
| `pbp_event_id` (null ok) | string |  |  | Key of the matched row in the events table (dictionary_games.md), which keeps the provider's own play ID. | PBP | ROW | post_game | R-SY-02, R-SY-10 |
| `licence_class` | enum |  | computed_by_us, model_input_allowed, reference_only | Licence class of the PBP-derived values in this row (computed_by_us when no PBP value is used). | pipeline from pbp_provider | computed_by_us | n/a | R-DQ-04 |
| `model_version` (G) | string |  |  | Pipeline and model versions that produced the row (semver string per stage, joined). | pipeline | computed_by_us | by_pass | R-MD-09, R-EN-04, R-DQ-04 |
| `source` (G) | string |  |  | Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Row-level confidence: minimum of the field confidences used in the row. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `created_utc` | timestamp | UTC |  | UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07). | pipeline | computed_by_us | n/a (processing metadata) | R-DQ-04, R-EN-07 |

### reviews

- **Grain:** one row per instant-replay review, coach's challenge, appeal or correctable-error / timing correction per pass.
- **Primary key:** `review_id`
- **Foreign keys:** `game_id` -> games.game_id; `timeout_id` -> timeouts.timeout_id; `pbp_event_id` -> events.event_id
- **Requirements:** R-SR-04, R-RF-07, R-SB-01, R-SB-02, R-MB-05, R-IV-05, R-IV-12
- **Schema file:** `schema/tables/reviews.yaml` (status: proposed)
- Broadcast replays shown during a review are flagged in state_frame.replay_flag; this table records the officials' review itself.
- Rule 2-9.19 (new in the 2026-27 post-clinic interpretations, 15 Oct 2026) makes the scorer record coach's challenges.

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `review_id` | string |  |  | game_id + pass + review_seq. | pipeline | computed_by_us | n/a | R-SR-04 |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `pass` (P) | enum |  | blind, anchored, pbp_only | blind, anchored, or pbp_only (games or stretches with no video, built from PBP alone for the possession engine, R-SY-06, R-PE-08). | pipeline | computed_by_us | n/a | R-SR-13, R-SR-15, R-SY-06, R-PE-08 |
| `review_seq` | int |  | 1 to 40 | Order in the game. | pipeline | computed_by_us | by_pass | R-SR-04 |
| `period` (G) | int |  | 1 to 12 | 1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-01, R-IV-16 |
| `game_clock_at_stop_s` | float | s | 0 to 1200 | Game clock when play stopped for the review. | fused | computed_by_us | by_pass | R-SR-04 |
| `video_ts_ms_start` (null ok) | int | ms | 0 to open | Review starts. | CV | computed_by_us | at_frame | R-SR-04 |
| `video_ts_ms_end` (null ok) | int | ms | 0 to open | Review result signalled. | CV | computed_by_us | at_frame | R-SR-04 |
| `review_kind` | enum |  | voluntary, mandatory, coach_challenge, appeal, correctable_error, timing_correction | voluntary (Rule 11-2), mandatory (11-3), coach_challenge (11-4), appeal (11-5), correctable_error (2-12), timing_correction (5-12). | fused | computed_by_us | by_pass | R-SR-04, R-RF-07 |
| `subject` | enum |  | two_vs_three, scoring_mistake, shot_clock_release, goaltending_basket_interference, out_of_bounds, restricted_area, flagrant_severity, foul_attribution, game_clock_time, shot_clock_time, end_of_period_try, end_of_period_foul, ft_shooter, wrong_basket, fight, other | What is reviewed. | fused | computed_by_us | by_pass | R-SR-04, R-MB-05 |
| `rule_ref` | string |  |  | Rule article allowing the review (e.g. '11-2.1.b.1'). | config | computed_by_us | by_pass | R-SR-04 |
| `requested_by` | enum |  | official, head_coach_msu, head_coach_opp, table | Who started it. | fused | computed_by_us | by_pass | R-SR-04 |
| `call_on_floor` (null ok) | string |  |  | Original call in plain words. | PBP; CV/manual | ROW | by_pass | R-SR-04 |
| `outcome` | enum |  | confirmed, overturned, stands, corrected | confirmed, overturned, stands (no indisputable evidence, Rule 11-1.1), corrected (clock or score changed). | fused | computed_by_us | by_pass | R-SR-04 |
| `challenge_number` (null ok) | int |  | 1 to 2 | 1 or 2 for coach's challenges (second only after a successful first, Rule 11-4.1.d). | fused | computed_by_us | by_pass | R-SR-04 |
| `timeout_charged` | bool |  |  | A timeout was charged (unsuccessful challenge or appeal, Rule 11-4.1.h, 11-5.1). | fused | computed_by_us | by_pass | R-SR-04, R-IV-10 |
| `timeout_id` (null ok) | string |  |  | FK timeouts. | pipeline | computed_by_us | by_pass | R-SR-04 |
| `game_clock_before_s` (null ok) | float | s | 0 to 1200 | Game clock before the review. | OCR | computed_by_us | at_frame | R-IV-05 |
| `game_clock_after_s` (null ok) | float | s | 0 to 1200 | Game clock after (a correction may move it up, flagged official_clock_correction). | OCR | computed_by_us | at_frame | R-IV-05 |
| `shot_clock_before_s` (null ok) | float | s | 0 to 30 | Shot clock before. | OCR | computed_by_us | at_frame | R-IV-07 |
| `shot_clock_after_s` (null ok) | float | s | 0 to 30 | Shot clock after. | OCR | computed_by_us | at_frame | R-IV-07 |
| `score_delta_msu` | int | points | -3 to 3 | Change to MSU score from the review. | fused | computed_by_us | by_pass | R-SB-01 |
| `score_delta_opp` | int | points | -3 to 3 | Change to the opponent score. | fused | computed_by_us | by_pass | R-SB-01 |
| `possession_after` | enum |  | msu, opponent, none | Team awarded the ball after the review. | fused | computed_by_us | by_pass | R-SR-04 |
| `arrow_used` | bool |  |  | Possession decided by the arrow (e.g. reversed goaltending with no team control, Rule 11-2.1.b.6.a). | fused | computed_by_us | by_pass | R-MD-12 |
| `review_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the review value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-04 |
| `review_conf` | float | 0-1 | 0 to 1 | Confidence of the review value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-04 |
| `review_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the review value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-04 |
| `pbp_provider` | enum |  | cbbd, espn_pulled, hoopr_espn, hoopr_ncaa, none | Provider of the PBP row this record was matched to or built from; 'none' in the blind pass. | pipeline | computed_by_us | post_game | R-DQ-01, R-DQ-04, R-SR-15 |
| `pbp_event_id` (null ok) | string |  |  | Key of the matched row in the events table (dictionary_games.md), which keeps the provider's own play ID. | PBP | ROW | post_game | R-SY-02, R-SY-10 |
| `licence_class` | enum |  | computed_by_us, model_input_allowed, reference_only | Licence class of the PBP-derived values in this row (computed_by_us when no PBP value is used). | pipeline from pbp_provider | computed_by_us | n/a | R-DQ-04 |
| `model_version` (G) | string |  |  | Pipeline and model versions that produced the row (semver string per stage, joined). | pipeline | computed_by_us | by_pass | R-MD-09, R-EN-04, R-DQ-04 |
| `source` (G) | string |  |  | Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Row-level confidence: minimum of the field confidences used in the row. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `created_utc` | timestamp | UTC |  | UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07). | pipeline | computed_by_us | n/a (processing metadata) | R-DQ-04, R-EN-07 |

### restarts

- **Grain:** one row per transition from dead ball to live ball (and each period start) per pass.
- **Primary key:** `restart_id`
- **Foreign keys:** `game_id` -> games.game_id; `possession_id` -> possessions.possession_id; `pbp_event_id` -> events.event_id
- **Requirements:** R-SR-08, R-MD-03, R-MD-12, R-IV-07, R-IV-08, R-SY-08, R-SY-09
- **Schema file:** `schema/tables/restarts.yaml` (status: proposed)
- Throw-in spot after a frontcourt stoppage: end line 3 ft (0.91 m) outside the lane line, or the 28-foot (8.53 m) mark on the sideline, per Rule 7-3.2.b as changed in 2025-26 (proposal 6 of the 2025-26 changes says below vs above the free-throw line extended; the 2026-27 book text describes an imaginary line from the end-line/sideline corner to the free-throw line extended; see open questions).
- The shot-clock value set at the restart is checked against config/invariants.yaml (R-SY-09).

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `restart_id` | string |  |  | game_id + pass + restart_seq. | pipeline | computed_by_us | n/a | R-SR-08 |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `pass` (P) | enum |  | blind, anchored, pbp_only | blind, anchored, or pbp_only (games or stretches with no video, built from PBP alone for the possession engine, R-SY-06, R-PE-08). | pipeline | computed_by_us | n/a | R-SR-13, R-SR-15, R-SY-06, R-PE-08 |
| `restart_seq` | int |  | 1 to 600 | Order in the game. | pipeline | computed_by_us | by_pass | R-SR-08 |
| `period` (G) | int |  | 1 to 12 | 1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-01, R-IV-16 |
| `game_clock_s` (G) | float | s | 0 to 1200 | Game clock remaining in the period. 0.1 s resolution (board shows tenths under 60 s, Rule 1-18.2; whole seconds above). | fused | computed_by_us | by_pass | R-SR-01, R-IV-05 |
| `video_ts_ms_dead` (null ok) | int | ms | 0 to open | Ball became dead. | CV; audio whistle | computed_by_us | at_frame | R-SR-08, R-RF-01 |
| `video_ts_ms_live` (null ok) | int | ms | 0 to open | Ball became live (disposal of thrower-in / free-thrower, toss). | CV | computed_by_us | at_frame | R-SR-08 |
| `dead_duration_s` (null ok) | float | s | 0 to 3600 | Real-time length of the dead ball. | derived | computed_by_us | at_frame | R-SR-08 |
| `dead_ball_reason` | enum |  | period_start, made_fg, made_last_ft, ft_followed_by_ft, personal_foul, technical_foul, double_foul, violation_out_of_bounds, violation_travel, violation_other, shot_clock_violation, held_ball, ball_lodged, timeout, injury_blood, review, inadvertent_whistle, period_end, other | Why the ball became dead (Rule 6-5.1). | fused | computed_by_us | by_pass | R-SR-08 |
| `violation_code` (null ok) | string |  |  | Rule 9 section of the violation when dead_ball_reason is a violation (e.g. '9-5' travel, '9-10' backcourt 10 s, '9-14' closely guarded). | fused | computed_by_us | by_pass | R-SR-08 |
| `restart_type` | enum |  | jump_ball, throw_in_end_line_after_score, throw_in_designated_spot, throw_in_alternating_possession, throw_in_point_of_interruption, free_throw, second_half_ap_division_line | How play resumed (Rule 6-5.2). | fused | computed_by_us | by_pass | R-SR-08, R-IV-08 |
| `throw_in_spot` | enum |  | end_line_runnable, end_line_3ft_outside_lane, sideline_28ft_mark, sideline_spot, end_line_spot, backcourt_spot, division_line_opposite_table, none | Spot class. | fused | computed_by_us | by_pass | R-SR-08, R-MD-03 |
| `spot_x_m` (null ok) | float | m | -8.62 to 8.62 | Throw-in spot x (attacked-rim frame of the throw-in team). | CV | computed_by_us | at_frame | R-SR-08 |
| `spot_y_m` (null ok) | float | m | -2.6 to 28.05 | Throw-in spot y. | CV | computed_by_us | at_frame | R-SR-08 |
| `court_half` | enum |  | front, back, none | Front or back court of the throw-in team. | fused | computed_by_us | by_pass | R-MD-03 |
| `inbound_side` (G) | enum |  | sideline, baseline, none | Global field. | fused | computed_by_us | by_pass | R-MD-03 |
| `restart_team` | enum |  | msu, opponent, none | Team putting the ball in play. | fused | computed_by_us | by_pass | R-SR-08, R-IV-08 |
| `thrower_player_id` (null ok) | string |  |  | Thrower-in or free-thrower. | CV; PBP | computed_by_us | by_pass | R-SR-08 |
| `arrow_before` | enum |  | msu, opponent, none | Arrow before the restart. | fused | computed_by_us | by_pass | R-MD-12 |
| `arrow_after` | enum |  | msu, opponent, none | Arrow after (flips when an alternating-possession throw-in ends, Rule 6-3.2). | fused | computed_by_us | by_pass | R-MD-12, R-IV-08 |
| `shot_clock_before_s` (null ok) | float | s | 0 to 30 | Shot clock at the dead ball. | OCR | computed_by_us | at_frame | R-SY-08 |
| `shot_clock_set_s` (null ok) | float | s | 0 to 30 | Shot clock shown at the restart (30, 20, unexpired or off). | OCR | computed_by_us | at_frame | R-SY-08, R-IV-07 |
| `shot_clock_expected_s` (null ok) | float | s | 0 to 30 | Value required by the rule for this reason (config/invariants.yaml shot_clock_reset_table). | derived | computed_by_us | by_pass | R-SY-09, R-IV-07 |
| `shot_clock_rule_ref` (null ok) | string |  |  | Rule 2-11.6 clause applied (e.g. '2-11.6.c.1'). | config | computed_by_us | by_pass | R-SY-09 |
| `throw_in_count_s` (null ok) | float | s | 0 to 10 | Disposal to release (<= 5 s, Rule 7-6.6). | CV | computed_by_us | at_frame | R-SR-08 |
| `after_timeout` | bool |  |  | First live ball after a timeout (ATO). | derived | computed_by_us | by_pass | R-SR-08 |
| `possession_id` (null ok) | int |  | 0 to open | Possession the restart belongs to. | fused | computed_by_us | by_pass | R-MD-04 |
| `restart_src` | enum |  | OCR, PBP, CV, manual, derived | Source of the restart value(s) in this row. | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-08 |
| `restart_conf` | float | 0-1 | 0 to 1 | Confidence of the restart value(s); PBP-sourced values carry 1.0 (R-MD-09). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-09, R-SR-08 |
| `restart_dq` | enum |  | observed, inferred, carried, imputed, quarantined | Data-quality flag of the restart value(s). | pipeline | computed_by_us | by_pass | R-SR-15, R-MD-19, R-SR-08 |
| `pbp_provider` | enum |  | cbbd, espn_pulled, hoopr_espn, hoopr_ncaa, none | Provider of the PBP row this record was matched to or built from; 'none' in the blind pass. | pipeline | computed_by_us | post_game | R-DQ-01, R-DQ-04, R-SR-15 |
| `pbp_event_id` (null ok) | string |  |  | Key of the matched row in the events table (dictionary_games.md), which keeps the provider's own play ID. | PBP | ROW | post_game | R-SY-02, R-SY-10 |
| `licence_class` | enum |  | computed_by_us, model_input_allowed, reference_only | Licence class of the PBP-derived values in this row (computed_by_us when no PBP value is used). | pipeline from pbp_provider | computed_by_us | n/a | R-DQ-04 |
| `model_version` (G) | string |  |  | Pipeline and model versions that produced the row (semver string per stage, joined). | pipeline | computed_by_us | by_pass | R-MD-09, R-EN-04, R-DQ-04 |
| `source` (G) | string |  |  | Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Row-level confidence: minimum of the field confidences used in the row. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `created_utc` | timestamp | UTC |  | UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07). | pipeline | computed_by_us | n/a (processing metadata) | R-DQ-04, R-EN-07 |

### scoreboard_ocr

- **Grain:** one row per OCR reading of one scoreboard display in one sampled frame (raw readings, immutable, pass-independent).
- **Primary key:** `reading_id`
- **Foreign keys:** `game_id` -> games.game_id; `video_id, frame_index` -> frames.(video_id, frame_index)
- **Requirements:** R-SY-01, R-SR-01, R-SR-02, R-SR-15, R-SB-01, R-SB-03, R-MD-08, R-MD-20, R-DQ-05
- **Schema file:** `schema/tables/scoreboard_ocr.yaml` (status: proposed)
- Immutable: written once, never updated or deleted; a re-read by a new OCR model is a new row with a new ocr_model_version. Corrections live in state_corrections and scoreboard_flags (R-SR-15).
- Home/away as printed on the display; mapping to msu/opponent happens downstream via games (MSU side), so a raw row never depends on our interpretation.
- Sampling: every frame where the scorebug is visible is the target (R-SY-01 asks every second of live play as the minimum).

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `reading_id` | string |  |  | game_id + video_id + frame_index + display + ocr_model_version. | pipeline | computed_by_us | n/a | R-SR-15 |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `video_id` | string |  |  | Video file. | video registry | computed_by_us | at_frame | R-SY-01 |
| `frame_index` | int |  | 0 to open | Frame read. | video decode | computed_by_us | at_frame | R-SY-01 |
| `video_ts_ms` (G) | int | ms | 0 to open | Presentation time of the frame from the start of the video file. | video decode (frames table) | computed_by_us | at_frame | R-MD-01, R-MD-08 |
| `display` | enum |  | broadcast_scorebug, arena_scoreboard, shot_clock_unit, scorer_table_led | Which display was read. | CV | computed_by_us | at_frame | R-SY-01, R-SB-01 |
| `scorebug_template_id` (null ok) | string |  |  | Broadcast graphics package template (R-MD-20). | OCR template registry | computed_by_us | at_frame | R-MD-20 |
| `bbox_x_px` | int | px | 0 to 7680 | Display box left. | CV | computed_by_us | at_frame | R-SY-01 |
| `bbox_y_px` | int | px | 0 to 4320 | Display box top. | CV | computed_by_us | at_frame | R-SY-01 |
| `bbox_w_px` | int | px | 1 to 7680 | Display box width. | CV | computed_by_us | at_frame | R-SY-01 |
| `bbox_h_px` | int | px | 1 to 4320 | Display box height. | CV | computed_by_us | at_frame | R-SY-01 |
| `period_raw` (null ok) | string |  |  | Text as read (e.g. '1st', '2ND', 'OT', 'HALF'). | OCR | computed_by_us | at_frame | R-SR-01 |
| `game_clock_raw` (null ok) | string |  |  | Text as read (e.g. '12:34', '45.6'). | OCR | computed_by_us | at_frame | R-SR-01 |
| `shot_clock_raw` (null ok) | string |  |  | Text as read; blank display recorded as ''. | OCR | computed_by_us | at_frame | R-SR-01 |
| `score_home_raw` (null ok) | string |  |  | Home score text. | OCR | computed_by_us | at_frame | R-SR-02 |
| `score_away_raw` (null ok) | string |  |  | Away score text. | OCR | computed_by_us | at_frame | R-SR-02 |
| `team_fouls_home_raw` (null ok) | string |  |  | Home team fouls text. | OCR | computed_by_us | at_frame | R-SR-03 |
| `team_fouls_away_raw` (null ok) | string |  |  | Away team fouls text. | OCR | computed_by_us | at_frame | R-SR-03 |
| `bonus_home_raw` (null ok) | string |  |  | Home bonus indicator text ('BONUS', 'BONUS+', 'DBL BONUS', ''). | OCR | computed_by_us | at_frame | R-SR-03 |
| `bonus_away_raw` (null ok) | string |  |  | Away bonus indicator text. | OCR | computed_by_us | at_frame | R-SR-03 |
| `timeouts_home_raw` (null ok) | string |  |  | Home timeouts text or pip count. | OCR | computed_by_us | at_frame | R-SR-04 |
| `timeouts_away_raw` (null ok) | string |  |  | Away timeouts text or pip count. | OCR | computed_by_us | at_frame | R-SR-04 |
| `arrow_raw` (null ok) | string |  |  | Possession-arrow indicator as read ('home', 'away', ''). | OCR | computed_by_us | at_frame | R-MD-12 |
| `period_parsed` (null ok) | int |  | 1 to 12 | Parsed period. | OCR parser | computed_by_us | at_frame | R-SR-01 |
| `game_clock_parsed_s` (null ok) | float | s | 0 to 1200 | Parsed game clock. | OCR parser | computed_by_us | at_frame | R-SR-01 |
| `shot_clock_parsed_s` (null ok) | float | s | 0 to 30 | Parsed shot clock (null when blank). | OCR parser | computed_by_us | at_frame | R-SR-01 |
| `score_home_parsed` (null ok) | int | points | 0 to 250 | Parsed home score. | OCR parser | computed_by_us | at_frame | R-SR-02 |
| `score_away_parsed` (null ok) | int | points | 0 to 250 | Parsed away score. | OCR parser | computed_by_us | at_frame | R-SR-02 |
| `team_fouls_home_parsed` (null ok) | int | count | 0 to 60 | Parsed. | OCR parser | computed_by_us | at_frame | R-SR-03 |
| `team_fouls_away_parsed` (null ok) | int | count | 0 to 60 | Parsed. | OCR parser | computed_by_us | at_frame | R-SR-03 |
| `timeouts_home_parsed` (null ok) | int | count | 0 to 12 | Parsed. | OCR parser | computed_by_us | at_frame | R-SR-04 |
| `timeouts_away_parsed` (null ok) | int | count | 0 to 12 | Parsed. | OCR parser | computed_by_us | at_frame | R-SR-04 |
| `field_conf_json` | string |  |  | JSON map field -> OCR confidence (0-1) for every parsed field. | OCR | computed_by_us | at_frame | R-SR-15, R-MD-09 |
| `ocr_model_version` | string |  |  | OCR model and template version. | pipeline | computed_by_us | n/a | R-MD-09 |
| `crop_sha256` | string |  |  | SHA-256 of the cropped display image (crop stored privately, never in the repo), so a reading can be audited. | pipeline | computed_by_us | n/a | R-DQ-04, R-DQ-05 |
| `created_utc` | timestamp | UTC |  | Write time (write-once). | pipeline | computed_by_us | n/a | R-SR-15 |

### scoreboard_flags

- **Grain:** one row per discrepancy or invariant break raised in a game pass; review answer fields are filled once (append-only versions).
- **Primary key:** `flag_id`
- **Foreign keys:** `game_id` -> games.game_id; `score_event_id` -> score_events.score_event_id; `make_id` -> made_basket_events.make_id; `restart_id` -> restarts.restart_id; `pbp_event_id` -> events.event_id
- **Requirements:** R-SB-01, R-SB-02, R-SB-03, R-SB-04, R-IV-01..16, R-HR-01, R-HR-05, R-DQ-03
- **Schema file:** `schema/tables/scoreboard_flags.yaml` (status: proposed)
- Holds the R-SB-01 types (a)-(j) and every invariant break from config/invariants.yaml (flag_type = invariant_break, invariant_id set), so one review queue serves both.
- No flag is left without review_answer before the game enters training (R-SB-02); more than 3 unresolved flags keep the game out of engine training (R-SB-04).

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `flag_id` | string |  |  | game_id + pass + flag_seq. | pipeline | computed_by_us | n/a | R-SB-01 |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `pass` (P) | enum |  | blind, anchored, pbp_only | blind, anchored, or pbp_only (games or stretches with no video, built from PBP alone for the possession engine, R-SY-06, R-PE-08). | pipeline | computed_by_us | n/a | R-SR-13, R-SR-15, R-SY-06, R-PE-08 |
| `flag_seq` | int |  | 1 to 100000 | Order raised. | pipeline | computed_by_us | by_pass | R-SB-01 |
| `flag_type` | enum |  | a_score_change_no_make_seen, b_make_seen_no_score_change, c_wrong_value, d_wrong_team, e_double_count, f_late_update, g_game_clock_not_started_or_stopped, h_shot_clock_not_reset_or_wrong, i_later_correction, j_scorebug_lag, invariant_break | R-SB-01 types a-j or invariant_break. | checker | computed_by_us | by_pass | R-SB-01 |
| `invariant_id` (null ok) | string |  |  | ID from config/invariants.yaml (R-IV-nn or new-IV-nn) for invariant breaks. | checker | computed_by_us | by_pass | R-IV-01..16 |
| `period` (G) | int |  | 1 to 12 | 1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-01, R-IV-16 |
| `game_clock_s` (G) | float | s | 0 to 1200 | Game clock remaining in the period. 0.1 s resolution (board shows tenths under 60 s, Rule 1-18.2; whole seconds above). | fused | computed_by_us | by_pass | R-SR-01, R-IV-05 |
| `video_ts_ms_start` (null ok) | int | ms | 0 to open | Start of the evidence window. | checker | computed_by_us | at_frame | R-SB-01 |
| `video_ts_ms_end` (null ok) | int | ms | 0 to open | End of the evidence window. | checker | computed_by_us | at_frame | R-SB-01 |
| `team` | enum |  | msu, opponent, none | Team concerned. | checker | computed_by_us | by_pass | R-SB-01 |
| `field` | string |  |  | State field concerned (e.g. 'score_msu', 'shot_clock_s'). | checker | computed_by_us | by_pass | R-SB-01 |
| `expected_value` (null ok) | string |  |  | Value the rule or the other sensor implies. | checker | computed_by_us | by_pass | R-SB-01 |
| `observed_value` (null ok) | string |  |  | Value read. | checker | computed_by_us | by_pass | R-SB-01 |
| `lag_s` (null ok) | float | s | -5 to 600 | Board change minus event time (types f, j). | checker | computed_by_us | at_frame | R-SB-03 |
| `window_s` | float | s | 0 to 120 | Detection window used (starts at 15 s, then reset from the measured lag; R-SB-03). | config | computed_by_us | by_pass | R-SB-03 |
| `not_seen` | bool |  |  | Camera off court at the moment: logged, not a break (R-SB-01 exception). | CV | computed_by_us | at_frame | R-SB-01 |
| `score_event_id` (null ok) | string |  |  | Linked score event. | pipeline | computed_by_us | by_pass | R-SB-01 |
| `make_id` (null ok) | string |  |  | Linked make. | pipeline | computed_by_us | by_pass | R-MB-01 |
| `restart_id` (null ok) | string |  |  | Linked restart (shot-clock flags). | pipeline | computed_by_us | by_pass | R-SY-09 |
| `reading_ids` | list[string] |  |  | scoreboard_ocr readings used as evidence. | pipeline | computed_by_us | at_frame | R-SB-01 |
| `action` | enum |  | flag, quarantine, human_review | Action from config/invariants.yaml. | config | computed_by_us | by_pass | R-HR-01, R-DQ-03 |
| `priority` (null ok) | float | score | 0 to open | Queue priority (model uncertainty x downstream impact, R-HR-03). | queue | computed_by_us | by_pass | R-HR-03 |
| `review_answer` (null ok) | enum |  | scoreboard_malfunction, scorebug_lag, official_correction, cv_miss, cv_false_positive, pbp_error, unresolved | R-SB-02 answer. | manual review | computed_by_us | post_review | R-SB-02 |
| `corrected_value` (null ok) | string |  |  | Corrected value (raw values elsewhere stay as written). | manual review | computed_by_us | post_review | R-SB-02, R-SR-15 |
| `reviewer` (null ok) | string |  |  | Who answered (R-HR-05). | manual review | computed_by_us | post_review | R-SB-02, R-HR-05 |
| `reviewed_utc` (null ok) | timestamp | UTC |  | When answered. | manual review | computed_by_us | post_review | R-SB-02, R-HR-05 |
| `review_reason` (null ok) | string |  |  | Reason in words. | manual review | computed_by_us | post_review | R-SB-02 |
| `status` | enum |  | open, answered | open or answered. | pipeline | computed_by_us | post_review | R-SB-02, R-SB-04 |
| `pbp_provider` | enum |  | cbbd, espn_pulled, hoopr_espn, hoopr_ncaa, none | Provider of the PBP row this record was matched to or built from; 'none' in the blind pass. | pipeline | computed_by_us | post_game | R-DQ-01, R-DQ-04, R-SR-15 |
| `pbp_event_id` (null ok) | string |  |  | Key of the matched row in the events table (dictionary_games.md), which keeps the provider's own play ID. | PBP | ROW | post_game | R-SY-02, R-SY-10 |
| `licence_class` | enum |  | computed_by_us, model_input_allowed, reference_only | Licence class of the PBP-derived values in this row (computed_by_us when no PBP value is used). | pipeline from pbp_provider | computed_by_us | n/a | R-DQ-04 |
| `model_version` (G) | string |  |  | Pipeline and model versions that produced the row (semver string per stage, joined). | pipeline | computed_by_us | by_pass | R-MD-09, R-EN-04, R-DQ-04 |
| `source` (G) | string |  |  | Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Row-level confidence: minimum of the field confidences used in the row. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `created_utc` | timestamp | UTC |  | UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07). | pipeline | computed_by_us | n/a (processing metadata) | R-DQ-04, R-EN-07 |

### made_basket_events

- **Grain:** one row per candidate made basket (confirmed, vision-only, flagged or rejected) per pass, with every cue.
- **Primary key:** `make_id`
- **Foreign keys:** `game_id` -> games.game_id; `shot_id` -> shots.shot_id; `score_event_id` -> score_events.score_event_id; `review_id` -> reviews.review_id
- **Requirements:** R-MB-01, R-MB-02, R-MB-03, R-MB-04, R-MB-05, R-MB-06, R-MB-07, R-SB-01, R-BL-05, R-IV-04, R-IV-12
- **Schema file:** `schema/tables/made_basket_events.yaml` (status: proposed)
- Decision rule (R-MB-01): confirmed = (cue 3 or cue 4) and (cue 1 or cue 2); vision_only (blind pass) = cue 1 and cue 2; not_seen_confirmed = camera cut, confirmed by cues 3 and 4; anything else flagged. Cue 5 is context, never decisive.
- Rim geometry: rim height 3.05 m, inner diameter 45.72 cm (18 in, Rule 1-14/1-15; check against config/court_ncaa_men.yaml).

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `make_id` | string |  |  | game_id + pass + make_seq. | pipeline | computed_by_us | n/a | R-MB-01 |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `pass` (P) | enum |  | blind, anchored | Processing pass: blind uses no PBP; anchored uses PBP. The per-game diff of the two is the CV error estimate (R-SR-13). | pipeline | computed_by_us | n/a | R-SR-13, R-SR-15 |
| `period` (G) | int |  | 1 to 12 | 1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-01, R-IV-16 |
| `game_clock_s` (G) | float | s | 0 to 1200 | Game clock remaining in the period. 0.1 s resolution (board shows tenths under 60 s, Rule 1-18.2; whole seconds above). | fused | computed_by_us | by_pass | R-SR-01, R-IV-05 |
| `video_ts_ms_make` (null ok) | int | ms | 0 to open | Video time the ball passes down through the ring plane (the make frame). | CV | computed_by_us | at_frame | R-MB-01, R-MB-04 |
| `frame_index_make` (null ok) | int |  | 0 to open | Make frame. | CV | computed_by_us | at_frame | R-MB-04 |
| `team` | enum |  | msu, opponent | Team credited. | fused | computed_by_us | by_pass | R-MB-01 |
| `shooter_player_id` (null ok) | string |  |  | Shooter. | CV; PBP | computed_by_us | by_pass | R-MB-01 |
| `shot_id` (null ok) | string |  |  | FK shots. | pipeline | computed_by_us | by_pass | R-EV-07 |
| `points_cv` (null ok) | int | points | 2 to 3 | 2 or 3 from the shooter's last floor contact vs the arc (6.75 m; 6.60 m corners; Rule 1-7.1, 5-1.5). | CV | computed_by_us | at_frame | R-IV-12, R-MB-04 |
| `points_board` (null ok) | int | points | 1 to 3 | Score change on the board. | OCR | computed_by_us | at_frame | R-MB-04 |
| `points_pbp` (null ok) | int | points | 1 to 3 | PBP score value. | PBP | ROW | post_game | R-MB-04 |
| `cue1_present` | bool |  |  | Cue 1: ball passes downward through the rim cylinder. | CV | computed_by_us | at_frame | R-MB-01 |
| `cue1_frame` (null ok) | int |  | 0 to open | Frame of cue 1. | CV | computed_by_us | at_frame | R-MB-01 |
| `cue1_conf` (null ok) | float | 0-1 | 0 to 1 | Confidence of cue 1. | CV | computed_by_us | at_frame | R-MB-01 |
| `cue2_present` | bool |  |  | Cue 2: net moves sharply and the ball is seen in or below the net. | CV | computed_by_us | at_frame | R-MB-01 |
| `cue2_frame` (null ok) | int |  | 0 to open | Frame of cue 2. | CV | computed_by_us | at_frame | R-MB-01 |
| `cue2_conf` (null ok) | float | 0-1 | 0 to 1 | Confidence of cue 2. | CV | computed_by_us | at_frame | R-MB-01 |
| `cue3_present` | bool |  |  | Cue 3: board score changes inside the lag window. | OCR | computed_by_us | at_frame | R-MB-01, R-SB-03 |
| `cue3_frame` (null ok) | int |  | 0 to open | Frame of cue 3. | OCR | computed_by_us | at_frame | R-MB-01, R-SB-03 |
| `cue3_conf` (null ok) | float | 0-1 | 0 to 1 | Confidence of cue 3. | OCR | computed_by_us | at_frame | R-MB-01, R-SB-03 |
| `cue3_lag_s` (null ok) | float | s | -5 to 120 | Board change minus make time. | derived | computed_by_us | at_frame | R-SB-03 |
| `cue4_present` | bool |  |  | Cue 4: PBP made shot at the matching game-clock second. | PBP | ROW | post_game | R-MB-01 |
| `cue4_frame` (null ok) | int |  | 0 to open | Frame of cue 4. | PBP | computed_by_us | at_frame | R-MB-01 |
| `cue4_conf` (null ok) | float | 0-1 | 0 to 1 | Confidence of cue 4. | PBP | computed_by_us | at_frame | R-MB-01 |
| `cue5_clock_stop` (null ok) | bool |  |  | Context: clock stopped after the make with <= 59.9 s left in period >= 2 (Rule 2-10.12). | OCR | computed_by_us | at_frame | R-MB-01, R-IV-06 |
| `cue5_baseline_inbound` (null ok) | bool |  |  | Context: the other team inbounds from the end line. | CV | computed_by_us | at_frame | R-MB-01 |
| `cue5_crowd_audio_conf` (null ok) | float | 0-1 | 0 to 1 | Context: crowd-audio make cue (never decisive). | audio | computed_by_us | at_frame | R-MB-01 |
| `decision` | enum |  | confirmed, vision_only, not_seen_confirmed, flagged, rejected | Outcome of the decision rule. | decision rule | computed_by_us | by_pass | R-MB-01, R-MB-02, R-MB-03 |
| `edge_case` | enum |  | none, goaltending_awarded, basket_interference_awarded, basket_interference_cancelled, waved_off_foul_before_try, waved_off_offensive_foul, waved_off_shot_clock, waved_off_period_horn, ball_stuck_on_rim, ball_up_through_net, in_and_out, tip_in, putback, dunk, alley_oop, and_one, review_reversal | R-MB-05 edge case, or none. | fused | computed_by_us | by_pass | R-MB-05 |
| `rim_visible` | bool |  |  | Rim in view at the make frame. | CV | computed_by_us | at_frame | R-MB-03 |
| `net_sharp` | bool |  |  | Net region sharp enough (no motion blur) at the frame rate used. | CV | computed_by_us | at_frame | R-MB-03 |
| `release_frame` (null ok) | int |  | 0 to open | Shot release frame. | CV | computed_by_us | at_frame | R-MB-06 |
| `release_game_clock_s` (null ok) | float | s | 0 to 1200 | Game clock at release. | fused | computed_by_us | at_frame | R-MB-06 |
| `release_shot_clock_s` (null ok) | float | s | 0 to 30 | Shot clock at release. | fused | computed_by_us | at_frame | R-MB-06 |
| `release_vs_horn` | enum |  | before, after, not_applicable, clock_not_visible | Release before the period or shot-clock horn (zeros; Rule 5-7.2.a, 11-1.2, 11-1.3). | fused | computed_by_us | at_frame | R-MB-06 |
| `and_one_pending` | bool |  |  | Foul on the make: a free throw follows. | fused | computed_by_us | by_pass | R-MB-05 |
| `review_id` (null ok) | string |  |  | Review that confirmed or changed the make. | pipeline | computed_by_us | by_pass | R-MB-05 |
| `score_event_id` (null ok) | string |  |  | FK score_events. | pipeline | computed_by_us | by_pass | R-SR-02 |
| `flag_ids` | list[string] |  |  | Flags raised. | pipeline | computed_by_us | by_pass | R-MB-01, R-SB-01 |
| `pbp_provider` | enum |  | cbbd, espn_pulled, hoopr_espn, hoopr_ncaa, none | Provider of the PBP row this record was matched to or built from; 'none' in the blind pass. | pipeline | computed_by_us | post_game | R-DQ-01, R-DQ-04, R-SR-15 |
| `pbp_event_id` (null ok) | string |  |  | Key of the matched row in the events table (dictionary_games.md), which keeps the provider's own play ID. | PBP | ROW | post_game | R-SY-02, R-SY-10 |
| `licence_class` | enum |  | computed_by_us, model_input_allowed, reference_only | Licence class of the PBP-derived values in this row (computed_by_us when no PBP value is used). | pipeline from pbp_provider | computed_by_us | n/a | R-DQ-04 |
| `model_version` (G) | string |  |  | Pipeline and model versions that produced the row (semver string per stage, joined). | pipeline | computed_by_us | by_pass | R-MD-09, R-EN-04, R-DQ-04 |
| `source` (G) | string |  |  | Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Row-level confidence: minimum of the field confidences used in the row. | pipeline | computed_by_us | by_pass | R-MD-09, R-SR-15 |
| `created_utc` | timestamp | UTC |  | UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07). | pipeline | computed_by_us | n/a (processing metadata) | R-DQ-04, R-EN-07 |

### cv_events_unmatched

- **Grain:** one row per CV-detected event that has no matching PBP event (anchored pass), kept forever as its own stream.
- **Primary key:** `cv_event_id`
- **Foreign keys:** `game_id` -> games.game_id; `event_id` -> events.event_id (the same event in the core events table); `nearest_pbp_event_id` -> events.event_id
- **Requirements:** R-SR-14, R-SY-10, R-EV-09, R-EV-01
- **Schema file:** `schema/tables/cv_events_unmatched.yaml` (status: proposed)
- Every CV event in the blind pass is unmatched by construction; this table is written in the anchored pass, where matching is possible. Blind-pass events live in events with pass = blind.
- Never zero rows for a full game without a written reason (R-SR-14 test): the reason goes into the run record.

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cv_event_id` | string |  |  | game_id + 'anchored' + seq. | pipeline | computed_by_us | n/a | R-SR-14 |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `event_id` | string |  |  | Same event's row in the core events table. | pipeline | computed_by_us | at_frame | R-EV-01 |
| `event_type` | enum |  | deflection, screen, hand_off, tip, box_out, closeout, help_rotation, loose_ball_recovery, contest, drive, pass, shot_unlogged, foul_unlogged, turnover_unlogged, rebound_unlogged, substitution_unlogged, timeout_unlogged, other | Type of event. | CV | computed_by_us | at_frame | R-SR-14, R-SY-10 |
| `period` (G) | int |  | 1 to 12 | 1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4). | fused | computed_by_us | by_pass | R-SR-01, R-IV-16 |
| `game_clock_s` (G) | float | s | 0 to 1200 | Game clock remaining in the period. 0.1 s resolution (board shows tenths under 60 s, Rule 1-18.2; whole seconds above). | fused | computed_by_us | by_pass | R-SR-01, R-IV-05 |
| `video_ts_ms_start` | int | ms | 0 to open | Event start. | CV | computed_by_us | at_frame | R-SR-14 |
| `video_ts_ms_end` | int | ms | 0 to open | Event end. | CV | computed_by_us | at_frame | R-SR-14 |
| `team` | enum |  | msu, opponent, none | Team performing the event. | CV | computed_by_us | at_frame | R-SR-14 |
| `player_ids` | list[string] |  |  | Players involved (actor first). | CV | computed_by_us | at_frame | R-SR-14 |
| `x_m` (null ok) | float | m | -8.62 to 8.62 | Location x (attacked-rim frame). | CV | computed_by_us | at_frame | R-EV-01 |
| `y_m` (null ok) | float | m | -2.6 to 28.05 | Location y. | CV | computed_by_us | at_frame | R-EV-01 |
| `r_m` (null ok) | float | m | 0 to 30 | Distance from the attacked rim. | derived | computed_by_us | at_frame | R-EV-01 |
| `theta_deg` (null ok) | float | degrees | 0 to 360 | Angle from the right baseline at the rim centre. | derived | computed_by_us | at_frame | R-EV-01 |
| `confidence` (G) | float | 0-1 | 0 to 1 | Detector confidence. | CV | computed_by_us | at_frame | R-SR-14, R-MD-09 |
| `nearest_pbp_event_id` (null ok) | string |  |  | Closest PBP event in game time (for audit). | PBP | ROW | post_game | R-SY-10 |
| `nearest_pbp_dt_s` (null ok) | float | s | 0 to 1200 | Game-clock gap to it. | derived | computed_by_us | post_game | R-SY-10 |
| `unmatched_reason` | enum |  | type_not_logged_by_pbp, pbp_missing_event, outside_time_window, identity_mismatch, possible_false_positive, unknown | Why there is no match. | matcher | computed_by_us | post_game | R-SR-14, R-SY-10 |
| `review_status` | enum |  | not_queued, queued, confirmed_real, false_positive | Review state. | manual review | computed_by_us | post_review | R-HR-01 |
| `model_version` (G) | string |  |  | Detector versions. | pipeline | computed_by_us | n/a | R-MD-09 |
| `created_utc` | timestamp | UTC |  | Write time. | pipeline | computed_by_us | n/a | R-DQ-04 |

### state_corrections

- **Grain:** one row per corrected value of any state table (append-only; raw rows are never edited).
- **Primary key:** `correction_id`
- **Foreign keys:** `game_id` -> games.game_id; `flag_id` -> scoreboard_flags.flag_id
- **Requirements:** R-SR-15, R-SB-02, R-HR-05, R-DQ-04
- **Schema file:** `schema/tables/state_corrections.yaml` (status: proposed)
- Proposed addition (not in the prompt's list): R-SR-15 needs 'corrections in a separate column with reviewer and reason'; one long table keeps every state table's raw columns untouched and gives one audit trail.
- Readers apply corrections as an overlay: corrected view = raw row + latest correction per (table, row_key, field).

| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `correction_id` | string |  |  | game_id + seq. | pipeline | computed_by_us | n/a | R-SR-15 |
| `game_id` (G) | string |  |  | ESPN game ID; the one join key across sources (FK games.game_id). | registry/games.csv | REG | pre_game | R-MD-01 |
| `target_table` | enum |  | state_frame, state_second, score_events, foul_state, free_throws, timeouts, reviews, restarts, made_basket_events, cv_events_unmatched | Table corrected. | review | computed_by_us | post_review | R-SR-15 |
| `target_row_key` | string |  |  | Primary key of the corrected row (JSON for composite keys); for frame ranges the first and last key. | review | computed_by_us | post_review | R-SR-15 |
| `target_range_end_key` (null ok) | string |  |  | Last row key when one correction covers a range of frames or seconds. | review | computed_by_us | post_review | R-SR-15 |
| `field` | string |  |  | Column corrected. | review | computed_by_us | post_review | R-SR-15 |
| `raw_value` | string |  |  | Value as written (copied for audit). | review | computed_by_us | post_review | R-SR-15 |
| `corrected_value` | string |  |  | New value. | review | computed_by_us | post_review | R-SR-15 |
| `correction_source` | enum |  | manual, PBP, OCR, CV, official_record | Basis of the correction. | review | computed_by_us | post_review | R-SR-15 |
| `flag_id` (null ok) | string |  |  | Flag that triggered it. | review | computed_by_us | post_review | R-SB-02 |
| `review_answer` (null ok) | enum |  | scoreboard_malfunction, scorebug_lag, official_correction, cv_miss, cv_false_positive, pbp_error, unresolved | R-SB-02 answer. | review | computed_by_us | post_review | R-SB-02 |
| `reviewer` | string |  |  | Who. | review | computed_by_us | post_review | R-HR-05 |
| `reviewed_utc` | timestamp | UTC |  | When. | review | computed_by_us | post_review | R-HR-05 |
| `reason` | string |  |  | Why, in words. | review | computed_by_us | post_review | R-SR-15 |
| `tool_version` | string |  |  | Review tool version (R-HR-05). | review | computed_by_us | post_review | R-HR-05 |
| `supersedes_correction_id` (null ok) | string |  |  | Earlier correction this one replaces. | review | computed_by_us | post_review | R-SR-15 |
## 7. Open questions for Aldemir

1. Licence of the ESPN data already pulled and of hoopR prebuilt ESPN / NCAA-engine files: keep as `reference_only` (current default here), or allow them as model input?
2. Approve the proposed `pass` value `pbp_only` (state vocabulary for games without video, for the possession engine)?
3. Approve the proposed global-metadata additions in section 4 (pass, video_id, shot_clock_status, team-specific bonus, timeouts by type, challenge state, possession_arrow, reverse_angle, field-level provenance)?
4. Approve the extra table `state_corrections` (one audit table for all corrections) instead of correction columns in each state table?
5. Media-timeout format per game: read it from PBP, or keep a per-game field in the games registry filled by hand from the broadcast?
6. Analysis windows (two-for-one 33–45 s, foul to extend ≤ 60 s and deficit 1–9, foul trouble 2 / 4): accept as proposals to calibrate on the first games?
7. Rule 7-3.2.b wording: the 2025-26 change says "below / above the free-throw line extended"; the 2026-27 book text describes an imaginary line from the end-line corner to the free-throw line extended. Which boundary should `restarts.throw_in_spot` checks use (ask the rules editor or follow the book text)?
8. Officials: R-IV-02 changed from "three" to "two or three (three expected in D-I)". OK?

## 8. Sources opened (2026-10-18)

- `docs/rules/PRMBB_RulesBook.pdf` (2026-27 NCAA Men's Basketball Rules, August 2026), text via `pdftotext -layout`: Rules 1-1 to 1-8, 1-18 to 1-22, 2 (all), 3 (all), 4-8 to 4-17, 4-24 to 4-34, 5 (all), 6 (all), 7 (all), 8 (all), 9 (all), 10-1 to 10-4, 11 (all); front matter pages 6–14 (2026-27 changes, points of emphasis, editorial changes).
- `docs/rules/PRMBB_CaseBook.pdf`: A.R. 2-13 to 2-16 (shot clock), A.R. 5-19 to 5-20 (technical fouls at the end of a half), A.R. 9-25 to 9-26.
- `docs/rules/2025-26PRMBB_RulesChanges.pdf` (all three pages).
- `docs/rules/2026-27PRMBB_PostClinicInterpretations.pdf` (both pages; Rule 2-9.19, A.R. 5-33, A.R. 11-32).
- Live doc export `requirements_main.md`: sections "Requirement format", "Global metadata on every record", "State record and invariants", "Possession engine: its form"; R-MD, R-SY, R-RF, R-DQ, R-EN, R-HR, R-VI, R-BL, R-EV rows; `requirement_ids.md` (R-CG, R-ST, R-DF).
- Repo: `schema/global_metadata.yaml`, `config/court_ncaa_men.yaml`, `config/vocabulary_map.yaml`, `src/msu_alpha/geometry.py` (frame definition), `registry/games.csv` (header), `docs/research/data_sources_catalog.md` (summary table and ingestion order), `coord/BOARD.md`, `coord/prompts/003-data-dictionary-and-first-games.md`.
- No web pages, APIs or data providers were called for this section.
