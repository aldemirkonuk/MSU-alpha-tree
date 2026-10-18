# Requirements inbox 008 · Requirements improvement: consolidated proposal set

From: requirements improvement synthesis (2026-10-18). To: requirements session. Status: proposal, not yet agreed with Aldemir. Nothing in the live doc, `config/`, `schema/` or `src/` was edited by this pass; the markets fixes in `src/msu_alpha/markets/` were made earlier today by the main session and are only recorded here.

## What was produced (add-only)

| File | Content |
| --- | --- |
| `docs/requirements_review/synthesis.md` | Perspective synthesis (Think, Understand, Analyze), 29 conflicts with resolutions, top 15 changes, merged verdicts, the N-series, the game-flow spine, the minimum build, resolved code findings, decisions |
| `docs/requirements_review/proposals_consolidated.yaml` | Machine-readable: `existing_verdicts` (518), `new_requirements` (198), `id_map` (312 rows), `conflicts`, `decisions`, `game_flow_spine`, `minimum_build_first_two_games`, `resolved_code_findings`; validated with yaml.safe_load |
| this file | how to apply, counts, decisions |

Inputs consolidated: quality review + acceptance tests (518 IDs, 181 with issues), the three panel reviews (ESPN analyst, data engineer, NBA team data scientist), round-2 gap closures (71 requirements, 185 columns), the rules vocabularies and court-constants check, inbox 007 (93), `config/invariants.yaml` (new-IV-01..34), inbox 006 (dictionaries, markets).

## Counts

- Existing IDs: 518 merged verdicts: keep 308, tighten 133, loosen 6, rewrite 44, split 15, merge-into 12, drop 0.
- New proposals read: 290; absorbed into existing IDs: 17; merged into 198 N-requirements (P0 56, P1 84, P2 58; Shall 108, Should 90).
- N-requirements per family: N-AU 2, N-BL 1, N-CC 6, N-CD 1, N-CG 2, N-CH 2, N-CO 1, N-CS 2, N-CX 9, N-DF 10, N-DQ 7, N-DS 1, N-DT 3, N-EN 7, N-EV 13, N-FD 6, N-HR 1, N-HY 1, N-ID 1, N-IV 33, N-MB 1, N-MD 12, N-MK 1, N-OS 1, N-PC 6, N-PL 5, N-PR 2, N-RF 14, N-RL 2, N-RR 1, N-SR 4, N-ST 12, N-SY 7, N-VA 6, N-VI 6, N-VL 5, N-VZ 4.
- Inbox 006 markets proposals: all 22 already in the live doc as R-MK-12..33 (mapped in id_map).
- Conflicts resolved: 29 (K01-K29); open decisions after de-duplication: 45 (D01-D45).
- Game-flow spine: 27 transitions (T00-T24 with T03a/T03b) and 14 decision points, every transition with detection, timing and analysis requirements.
- Minimum build for the first two games: 47 table entries (the engineer's 43 plus video_segments, pbp_versions, stat_corrections, stage_outputs); 222 existing and 56 new P0 requirements.
- Code: markets findings M1-M5 resolved in code with regression tests (recorded in R-MK-27, R-MK-13, R-RG-11); M6 (atomic writes) and M8 (schema_version in Parquet metadata) remain open as N-EN-02 and R-MK-31.

## How to apply (order)

1. **Decisions first.** Get Aldemir's answers to K01-K29 (they set config values that several rewrites cite) and to D01-D06 (rules corrections, R-RL, officials, 43-table build, pass enum, global metadata).
2. **Rules layer.** Adopt the rules edition (N-RL-01, N-RL-02), the 13 rule-number corrections and the N-IV invariants (was new-IV-01..34; new-IV-12 folds into R-IV-10, new-IV-34 into R-IV-13), the 41-cause shot-clock list (K18), the foul classes (R-RF-03) and the edge-correct court constants (N-CG-01, N-CG-02). Many rewrites cite these.
3. **Merge-into rows** (12): mark each superseded row "superseded by <ID>" (add-only, row kept) before editing the keepers, so no edit lands on a superseded row.
4. **Splits** (15): add the child rows ID-a, ID-b (ID-c) with their own tier and test; keep the parent as a pointer.
5. **Rewrites, then tighten and loosen** (44, 133, 6): replace text and Test cells from `existing_verdicts`; numbers marked "(proposal)" or "(initial value, to calibrate)" stay marked; tier changes (R-SB-04, R-SR-11 to Shall; R-PL-01 to Should) per D17.
6. **New requirements**: add the N-series by priority (P0, then P1, then P2), renumbering into R-<FAMILY>-nn freely; keep the N-ID and the old IDs in a "was" column so the id_map survives. New family R-RL if D02 is yes.
7. **Schema**: for P0 only, add `clock_map`, `state_transitions`, `state_segments`, `video_segments`, `pbp_versions`, `stat_corrections`, `stage_outputs`, `frames.stage_mask` and the key fixes (pass in frame PKs, time_base keys, game_id in state-table PKs); apply `schema/tables_proposed_changes.yaml` columns for the adopted N-requirements; regenerate specs in one dialect (R-EN-01).
8. **Tests and ontology**: copy the acceptance criteria into `acceptance_tests.yaml`, then run the ontology check (N-CD-01) so every leaf, ID and column stays traced.

## Decisions for Aldemir (one line each)

- K01: Approve physics key: speed 10.0 m/s hard + 9.0 m/s soft flag (>= 0.3 s windows), acceleration 12 m/s² over >= 0.5 s, to 8.0 m/s² after sigma <= 1.0 m/s²? [see synthesis section 2]
- K02: Set the scorebug window to 4.0 s initial, then per-field p99 + 1.0 s (3-15 s bounds)? [see synthesis section 2]
- K03: Adopt the resolvability gate (sigma <= 0.5 m/s², >= 0.5 s windows, change-point onsets, no jerk)? [see synthesis section 2]
- K04: Approve coverage gates: coarse 85% then 90%; fine 75% on 300 screens/5 games; publish fine only at confidence >= 0.8? [see synthesis section 2]
- K05: Primary run = register (net >= 8 in 120 s); broadcast display threshold 8 or 6? [see synthesis section 2]
- K06: Clutch = <= 300 s and margin <= 5 (late_240 kept as a separate flag)? [see synthesis section 2]
- K07: Make frame +/- 2 frames on 95% (and +/- 1 frame on 80% as stretch)? [see synthesis section 2]
- K08: Confirm: a shot-clock reset inside a possession (defensive foul, kicked ball) opens a new chance? [see synthesis section 2]
- K09: Approve state_segments + state_transitions as stored truth, state_frame as a view? [see synthesis section 2]
- K10: Foul-trouble default 2/3/4 (analyst) or 2/4, or a coach-supplied MSU rule? [see synthesis section 2]
- K11: Approve two stored shot-quality versions (agnostic for quality, adjusted for prediction)? [see synthesis section 2]
- K12: Display threshold: n70 per metric, n >= 30 until measured? [see synthesis section 2]
- K13: Single coverage key at 0.70? [see synthesis section 2]
- K14: Approve tempo + start type (exclusive) + situation flags (multi-label)? [see synthesis section 2]
- K15: Off-screen estimates at 10 Hz (not per frame)? [see synthesis section 2]
- K16: Reaction onset by change-point, +/- 0.10 s on 80% of 100 labels? [see synthesis section 2]
- K17: Start drift verdicts at game 11? [see synthesis section 2]
- K18: Adopt the 41-cause shot-clock list (add 8 causes to invariants.yaml)? [see synthesis section 2]
- K19: Short corner = 3.5 < |x| <= 6.0 m, y <= 1.50 m, or define from MSU film first? [see synthesis section 2]
- K20: Approve layered value with the G1-G4 gate on layer 3? [see synthesis section 2]
- K21: Pulled-player windows = first dead ball and 60 s, with matched baseline? [see synthesis section 2]
- K22: Contest bins 0-0.6 / 0.6-1.2 / 1.2-1.83 / > 1.83 m? [see synthesis section 2]
- K23: Is the half-time deadline a pilot goal, or offline-only this season? [see synthesis section 2]
- K24: Officials' roles at 1 Hz plus 10 Hz around whistles? [see synthesis section 2]
- K25: Adopt exact edge-correct court constants (1.270 m restricted area, 12.700 m frontcourt) and lift verified: false? [see synthesis section 2]
- K26: Adopt the FT-line-extended reading of Rule 7-3.2.b? [see synthesis section 2]
- K27: Store "shooting" as a context flag, not a foul class? [see synthesis section 2]
- K28: Garbage time: WP rule primary, CTG-adapted and source flags kept as views? [see synthesis section 2]
- K29: Adopt the N-<FAMILY>-nn renumbering? [see synthesis section 2]
- D01: Adopt the 13 rule-number corrections and the 34 proposed invariants of config/invariants.yaml (renumbered N-IV-02..N-IV-33; two absorbed into R-IV-10 and R-IV-13) into the live doc? [recommended: yes]
- D02: Adopt the new family R-RL (rules edition per game) and drop the foul type "intentional"? [recommended: yes]
- D03: Confirm R-IV-02 / R-FD-08 / R-DT-12 / R-SR-07: two or three officials (three expected in D-I)? [recommended: yes]
- D04: Approve the first build of the engineer's 43 tables (incl. new clock_map, state_transitions, state_segments) plus video_segments, pbp_versions, stat_corrections and stage_outputs, and defer the other specs until their gates pass? [recommended: yes]
- D05: Approve the extra state_corrections table and one pass enum {blind, anchored, pbp_only, none}? [recommended: yes]
- D06: Approve the global-metadata additions (pass, video_id, shot_clock_status, per-team bonus, timeouts by length, challenge state, arrow, reverse_angle), stored team-neutral with MSU views? [recommended: yes, team-neutral]
- D07: One player key: player_id (ESPN athlete ID, local x- IDs) or W1's player_uid? [recommended: player_id]
- D08: Use class of Torvik, NBA combine and EvanMiya values: model input or reference only? [recommended: decide per source in data_sources_catalog.md]
- D09: Kaggle March Madness archive (contains KenPom/Torvik columns): reference only, private copy only? [recommended: reference only, private]
- D10: hoopR ESPN-based prebuilt files: model input or reference only (ESPN terms)? [recommended: reference only until terms checked]
- D11: Kaggle Massey Ordinals: model input or reference only (Massey terms forbid AI/ML training without consent)? [recommended: reference only until permission (R-DS-12)]
- D12: Record your 18 Oct chat approval of the KenPom (Parse.bot) tool in R-DS-14 and its licence class (reference only?) [recommended: record, reference only]
- D13: Keep the ESPN-pulled registry/*.csv in the public repo or rebuild from CBBD; drop headshot_url (no-face rule)? [recommended: rebuild from CBBD; drop headshot_url]
- D14: Store player birth date, or only age at tip? [recommended: age at tip only]
- D15: Approve registry columns cbbd_game_id, video_ids, video hash, fps, resolution, codec, length, scorebug_left_team_id, media_format, pbp_status, bench end and first-half basket? [recommended: yes]
- D16: Bench side and scorers' table side per game: filled by you at intake or detected automatically? [recommended: filled at intake, verified by tracking]
- D17: Approve tier changes: R-SB-04 and R-SR-11 to Shall, R-PL-01 to Should, R-IV-14 to Shall once frontcourt status is stored? [recommended: yes]
- D18: Pass marks for the coach quiz per question type (R-GU-03), e.g. "who guards X" >= 90%? [recommended: set after game 3]
- D19: Approve the held-out game register (>= 20% of footage games, chosen by game, stratified by home/away and opponent tier) before any fit? [recommended: yes]
- D20: Officials' mechanics (rotations, primary areas, calling distance, full signal list): label now or after gate G7, and obtain the CCA Men's Officials Manual first? [recommended: after G7; obtain the manual]
- D21: Staff sheets: show official names next to crew tendencies, or crew IDs only; keep unwhistled-contact candidates review-only and private? [recommended: crew IDs on shared sheets; candidates private]
- D22: Conduct events (flopping, taunting, gestures toward officials, fighting and suspensions): in scope, and private only or publishable? [recommended: in scope as private labels; not published]
- D23: Fakes and contest form from pose as Shall now, or Should until pose quality at broadcast distance is measured? [recommended: Should until measured]
- D24: NIL valuations on player cards: keep as public estimates (exploratory only) or drop? [recommended: keep, never a model input]
- D25: Public betting share: look for a free terms-compliant source, accept a paid one, or drop the leaf? [recommended: drop until a free source is registered]
- D26: Context extras (ball model, rim type and liveliness proxy, dome placement, student-section end, crowd share): collect, or Should with "unknown"? [recommended: Should with unknown]
- D27: Pick-up point class edges 18.71 / 14.00 / 9.50 m: the staff's notion of full / three-quarter / half court? [recommended: confirm with staff]
- D28: Lineup "big" rule: listed C, or listed F >= 206 cm (listed heights run high)? [recommended: listed C or F >= 206 cm, flagged]
- D29: Fakes, runs and source definitions as new tables, or as event-family rows in events? [recommended: runs and source_definitions as tables; fakes as events rows]
- D30: Disqualified-player replacement: 20 s (RB 4-12.5) or 15 s (DIF p 2)? [recommended: 20 s (rules book wins), flag DIF]
- D31: Rules-edition season window 1 July - 30 June acceptable (no effective date printed)? [recommended: yes]
- D32: Obtain the 2025-26 rules book to confirm the derived 2025-26 edition record? [recommended: yes]
- D33: Which edge of the 2-in 28-ft mark is the 28 ft measured to? [recommended: check on a measured court]
- D34: Confirm the lane-space layout on a full-resolution diagram or a measured court before P3? [recommended: yes]
- D35: Add restart_type values throw_in_where_ball_went_out and division_line_after_review to restarts? [recommended: yes]
- D36: Count a shooter-team FT lane violation on the last free throw as a turnover (possession lost)? [recommended: yes, typed separately]
- D37: Was the "shot clock near expiration" signal in the 2025-26 book (affects the 2025-26 edition)? [recommended: check with the 2025-26 book (D32)]
- D38: Is a coach available to rate 50 broadcast phrases and 100 timeout purposes? [recommended: ask staff]
- D39: Markets: ESPN option (i) schedule only, (ii) schedule and odds, (iii) none? [recommended: decide]
- D40: Markets: Kalshi and Polymarket terms (incl. identity-field stripping): enable or keep disabled? [recommended: keep disabled until terms checked]
- D41: Markets: collector host (always-on Mac or small cloud VM)? [recommended: decide]
- D42: Markets: tiered cross-source tolerances XS-1..XS-4 vs the single 0.5-point rule (R-MK-22 split)? [recommended: split: 0.5 Shall, tiers Should]
- D43: Send the written permission requests (Sports-Reference, Massey; Synergy via staff) for R-DS-08 / R-DS-12? [recommended: yes]
- D44: Record the MSU film agreement status for R-RG-09? [recommended: record]
- D45: Actions (not decisions): start Google Drive for desktop; rotate the CBBD and Parse keys that appeared in chat. [recommended: do]
