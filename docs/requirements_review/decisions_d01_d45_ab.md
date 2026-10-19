# Open decisions D01–D45 and inbox 010 as A/B choices, by family (2026-10-19)

A = the recommendation, B = the main alternative. Sources: `docs/requirements_review/synthesis.md` (D01–D45) and
`coord/requirements_inbox/010-state-machine-and-clock-map.md` (Q1–Q3 there, here E1–E3). Aldemir's choices are
recorded below as he makes them. D45 is an action, not a decision.

## 1. Rules, invariants and game state (R-IV, R-RL, R-SR, R-MD, R-SY)

| # | Decision | A (recommended) | B |
| --- | --- | --- | --- |
| D01 | 13 rule-number corrections and 34 new invariants (N-IV-02..33) | Adopt into the live doc | Adopt the corrections only; review invariants one by one |
| D02 | Rules edition per game (family R-RL); foul type "intentional" | Adopt R-RL; drop "intentional" (not a 2026-27 class) | Adopt R-RL; keep "intentional" as an alias of flagrant 1 |
| D03 | Officials on court | 2 or 3 allowed, 3 expected in D-I | Exactly 3 always |
| D17 | Tier changes | R-SB-04, R-SR-11 to Shall; R-PL-01 to Should; R-IV-14 to Shall once frontcourt status is stored | Keep current tiers |
| D30 | Disqualified-player replacement time | 20 s (rules book), flag the officials' manual's 15 s | 15 s (officials' manual) |
| D31 | Rules-edition season window | 1 July – 30 June | Effective from the first game of each season |
| D32 | Get the 2025-26 rules book to confirm that edition | Yes | No, derive from the 2025-26 rule changes only |
| D35 | New restart types `throw_in_where_ball_went_out`, `division_line_after_review` | Add | Fold into existing throw-in types |
| D36 | Shooter-team lane violation on the last free throw | Counts as a turnover, typed separately | A violation only, no turnover |
| D37 | Was the "shot clock near expiration" signal in the 2025-26 book | Check with the 2025-26 book (D32) | Assume it is new in 2026-27 |
| E1 | State machine additions: T00 (game record opened), T26 (timeout/review ends), flow state S4 (split unknown) | Approve | Keep T01–T24 and S0–S11 only; handle these in code |
| E2 | `restricted_area_radius_m` in config/invariants.yaml is 1.22 m; K25 chose edge-correct 1.270 m | Update to 1.270 m | Keep 1.22 m (line centre) and note the difference |

## 2. Schema and metadata (R-MD, R-EN)

| # | Decision | A (recommended) | B |
| --- | --- | --- | --- |
| D04 | First build size | The engineer's 43 tables (incl. clock_map, state_transitions, state_segments) plus video_segments, pbp_versions, stat_corrections, stage_outputs; defer the other specs | Build all 104 proposed tables |
| D05 | `state_corrections` table and one pass enum {blind, anchored, pbp_only, none} | Approve | Corrections as rows in the main tables; pass as free text |
| D06 | Global-metadata additions (pass, video_id, shot_clock_status, per-team bonus, timeouts by length, challenge, arrow, reverse_angle) | Approve, stored home/away with MSU views | Approve, stored MSU-relative |
| D29 | Fakes, runs and source definitions | Runs and source definitions as tables; fakes as event rows | All three as event rows |

## 3. Registry, players and privacy (R-FD, R-PC, R-RG)

| # | Decision | A (recommended) | B |
| --- | --- | --- | --- |
| D07 | One player key | `player_id` (ESPN athlete ID; local x- IDs where none) | W1's `player_uid` (our own surrogate) |
| D13 | ESPN-pulled registry CSVs in the public repo; `headshot_url` | Rebuild from CBBD; drop `headshot_url` (no-face rule) | Keep the ESPN CSVs; drop `headshot_url` only |
| D14 | Birth date | Store age at tip only | Store birth date privately |
| D15 | New registry columns (cbbd_game_id, video ids and hash, fps, resolution, codec, length, scorebug left team, media format, pbp_status, bench end, first-half basket) | Approve | Approve the video columns only |
| D16 | Bench and scorers'-table side per game | Filled by you at intake, verified by tracking | Detected automatically only |
| D24 | NIL valuations on player cards | Keep as public estimates, never a model input | Drop |
| D28 | Lineup "big" rule | Listed C, or listed F ≥ 206 cm, flagged | Listed C only |
| D44 | MSU film agreement status for R-RG-09 | Record the current status | Leave open |

## 4. Data sources and licences (R-DS)

| # | Decision | A (recommended) | B |
| --- | --- | --- | --- |
| D08 | Torvik, NBA combine, EvanMiya values | Licence class per source in data_sources_catalog.md | All reference only |
| D09 | Kaggle March Madness archive (has KenPom/Torvik columns) | Reference only, private copy | Model input |
| D10 | hoopR ESPN-based prebuilt files | Reference only until ESPN terms are checked | Model input (hoopR release) |
| D11 | Kaggle Massey Ordinals (terms forbid ML training without consent) | Reference only until permission (R-DS-12) | Drop |
| D12 | KenPom via the Parse tool (your 18 Oct approval) | Record in R-DS-14, reference only | Record as model input |
| D43 | Written permission requests (Sports-Reference, Massey; Synergy via staff) | Send them | Do not ask; keep those sources reference only |
| E3 | CBBD challenge rows say "Stands" while the text says "Overturned" | Log it and report to CBBD | Log only |

## 5. Officials and conduct (R-RF)

| # | Decision | A (recommended) | B |
| --- | --- | --- | --- |
| D20 | Officials' mechanics (rotations, areas, calling distance, full signals) | Label after gate G7; get the CCA officials' manual first | Label now |
| D21 | Official names on staff sheets; unwhistled-contact candidates | Crew IDs on shared sheets; candidates private, review-only | Names on sheets |
| D22 | Conduct events (flopping, taunting, gestures, fights, suspensions) | In scope as private labels, never published | Out of scope |

## 6. Court geometry (R-CG)

| # | Decision | A (recommended) | B |
| --- | --- | --- | --- |
| D27 | Pick-up point edges 18.71 / 14.00 / 9.50 m (full / three-quarter / half court) | Confirm with staff | Accept as written |
| D33 | Which edge of the 28-ft mark the 28 ft is measured to | Check on a measured court | Assume the near edge |
| D34 | Lane-space layout | Confirm on a full-resolution diagram or measured court before P3 | Accept the current layout |

## 7. Video, pose and context (R-DT, R-CO, R-CX)

| # | Decision | A (recommended) | B |
| --- | --- | --- | --- |
| D23 | Fakes and contest form from pose | Should until pose quality at broadcast distance is measured | Shall now |
| D26 | Context extras (ball model, rim type and liveliness, dome placement, student-section end, crowd share) | Should, stored as "unknown" when missing | Collect all now |

## 8. Validation and game understanding (R-VA, R-GU)

| # | Decision | A (recommended) | B |
| --- | --- | --- | --- |
| D18 | Coach-quiz pass marks per question type | Set after game 3 | Set now (e.g. "who guards X" ≥ 90%) |
| D19 | Held-out game register (≥ 20% of footage games, by game, stratified home/away and opponent tier) before any fit | Approve | Hold out by possession, not game |
| D38 | A coach to rate 50 broadcast phrases and 100 timeout purposes | Ask staff | Rate them yourself |

## 9. Markets (R-MK)

| # | Decision | A (recommended) | B |
| --- | --- | --- | --- |
| D25 | Public betting share | Drop the leaf until a free, terms-compliant source is registered | Pay for a source |
| D39 | ESPN in the markets collector | (iii) None | (i) Schedule only |
| D40 | Kalshi and Polymarket (incl. stripping identity fields) | Keep disabled until terms are checked | Enable read-only now |
| D41 | Collector host | Always-on Mac | Small cloud VM |
| D42 | Cross-source tolerances | Split: single 0.5-point rule is Shall, tiers XS-1..XS-4 are Should | Single 0.5-point rule only |

D39 and D41 had no recommendation in the synthesis; A is this session's pick. D39 A: ESPN terms bar automated collection, and CBBD already gives schedules. D41 A: the Mac already runs the runner; move to a VM only if uptime fails.

## Action (not a decision)

- D45: start Google Drive for desktop (to move private files into MyDrive) and rotate the CBBD and Parse keys that appeared in chat.

## Decisions (Aldemir)

| # | Choice | Note |
| --- | --- | --- |
| all | Delegated (19 Oct) | Aldemir: "do the most advanced selection and most real life applicable, meaning it actually works". The Mac session picked per row; where A was refined, the refinement is stated. |
| D01 | A | Adopt the 13 corrections and 34 invariants. |
| D02 | A | R-RL adopted; "intentional" dropped (not a 2026-27 class); old PBP text "intentional" maps to flagrant 1 on import. |
| D03 | A | 2 or 3 allowed, 3 expected; a 2-person crew is flagged, not an error. |
| D17 | A | |
| D30 | A | 20 s; officials' manual 15 s flagged. |
| D31 | A | |
| D32 | A | Action for Aldemir: get the 2025-26 rules book. |
| D35 | A | |
| D36 | A | |
| D37 | A | Answered once D32 arrives. |
| E1 | A | T00, T26 and S4 approved. |
| E2 | A | restricted_area_radius_m becomes 1.270 m (edge-correct, K25); centre-line 1.22 m kept as a comment. |
| D04 | A | 43 + 4 tables first; the other specs stay proposed, built when a requirement needs them. |
| D05 | A | |
| D06 | A | Home/away storage, MSU views. |
| D29 | A | |
| D07 | A, refined | ESPN athlete ID as player_id, plus a crosswalk to CBBD, KenPom/Torvik and EvanMiya names (bitemporal, R-FD); local x- IDs for players with no ESPN ID. |
| D13 | A | Rebuild registry CSVs from CBBD; drop headshot_url. |
| D14 | A | Age at tip only. |
| D15 | A | |
| D16 | A | Filled at intake, verified by tracking (basket attacked and bench end must agree). |
| D24 | A | Keep as public estimate, never a model input. |
| D28 | A, refined | Listed C, or listed F ≥ 206 cm, flagged; replaced by the measured role cluster once tracking gives heights and positions. |
| D44 | A | Record the current status (action for Aldemir: state it). |
| D08 | A | Per source in data_sources_catalog.md. |
| D09 | A | |
| D10 | A | |
| D11 | A | |
| D12 | A | |
| D43 | A | Drafts prepared for Aldemir to send; nothing is sent by a session. |
| E3 | A | Log it; a report to CBBD is drafted for Aldemir to send. |
| D20 | A | After G7; get the CCA manual first. |
| D21 | A | |
| D22 | A | |
| D27 | A | Confirm with staff; until then the edges are parameters in R-CX-29. |
| D33 | A | |
| D34 | A | |
| D23 | A | Should until pose error at broadcast distance is measured; then Shall if the error gate passes. |
| D26 | A | |
| D18 | A | Set after game 3 from the measured distribution. |
| D19 | A, refined | Held out by game (≥ 20%, stratified), and every model also scored walk-forward in time. |
| D38 | A | Ask staff; fallback Aldemir rates them. |
| D25 | A | |
| D39 | A | No ESPN in the collector. |
| D40 | A | Disabled until terms are checked. |
| D41 | A, refined | Always-on Mac now; move to a small cloud VM if collection uptime falls below 99% over any 2 weeks. |
| D42 | A | |
| D45 | action | Aldemir: start Google Drive for desktop; rotate the CBBD and Parse keys. |
