# Conflicts K01–K29 as A/B choices (2026-10-18)

A = the synthesis recommendation, B = the main alternative. Detail and every perspective's view: docs/requirements_review/synthesis.md section 2. Aldemir's choices are recorded below as he makes them.

| K | Topic | A (recommended) | B (alternative) |
| --- | --- | --- | --- |
| K01 | Speed/acceleration limits | 10.0 m/s hard + 9.0 m/s review flag over ≥ 0.3 s; 12 m/s² over ≥ 0.5 s, 8.0 m/s² once accel error ≤ 1.0 m/s² | 9.0 m/s and 8.0 m/s² over ≥ 0.2 s from the start (scientist) |
| K02 | Scorebug make window | Start 4.0 s, then per field p99 + 1.0 s (3–15 s) | Keep 15 s start, reset from measured lag (live doc) |
| K03 | Acceleration bands vs noise | Keep bands, report only where error ≤ 0.5 m/s² (≥ 0.5 s windows); change-point onsets; no jerk | Report all bands as written (±2/±3 m/s², 1 m/s² onsets, jerk) |
| K04 | Ball-screen coverages | 4 coarse always (85% → 90%); 13 fine only after 75% on 300 screens / 5 games, shown at confidence ≥ 0.8 | 13 fine coverages from the start (coarse ≥ 90%, fine ≥ 80%) |
| K05 | Runs | Primary = net ≥ 8 in 120 s; broadcast "a-b" shown at net ≥ 8 | Same primary; broadcast shown at net ≥ 6 |
| K06 | Clutch | ≤ 300 s left and margin ≤ 5 (last-240 s kept as a separate flag) | Last 240 s and margin ≤ 5 |
| K07 | Make-frame tolerance (29.97 fps) | ±2 frames on 95% (±1 frame on 80% stretch) | ±1 frame on all makes |
| K08 | Chance boundaries | A shot-clock reset inside a possession (defensive foul, kicked ball) opens a new chance | Only offensive rebounds open a new chance |
| K09 | Game-state storage | state_segments + typed transitions stored; per-frame state is a view | Every frame stores all state fields (state_frame) |
| K10 | Foul trouble | 2 (H1) / 3 (H2 > 600 s left) / 4 (H2 ≤ 600 s, OT); 2/4 kept as a view | 2 in H1, 4 in H2 |
| K11 | Shot quality | Two versions: shooter-agnostic (quality) and shooter-adjusted (prediction) | One shooter-adjusted model |
| K12 | Minimum n for tendencies | n70 per metric from a reliability study; n ≥ 30 until measured | Fixed n ≥ 20 |
| K13 | Load coverage threshold | One key at 70% | One key at 60% |
| K14 | Possession labels | Tempo (exclusive) + start type (exclusive) + situation flags (multi-label) | Two exclusive labels only |
| K15 | Off-screen estimates | 10 Hz with calibrated 95% region and is_imputed flag | Per frame |
| K16 | Reaction onset | Change-point on velocity, ±0.10 s on 80% of 100 labels | Acceleration change > 1 m/s², ±80 ms |
| K17 | Drift checks | Quantiles from game 1; verdicts and alerts from game 11 | Verdicts from game 1 |
| K18 | Shot-clock reset causes | 41-cause list (add 8 to invariants) | Keep the 33 causes |
| K19 | Short corner | 3.5 < |x| ≤ 6.0 m, y ≤ 1.50 m (provisional, confirm on film) | Define from MSU film first |
| K20 | Value model start | Layers side by side now; 10 Hz layer only after gates G1–G4 pass on two games | 10 Hz value from the start |
| K21 | Pulled-player window | First dead ball and 60 s (30 s as sensitivity), with matched baseline | 30 s only |
| K22 | Contest bins | 0–0.6 / 0.6–1.2 / 1.2–1.83 / > 1.83 m, stored continuously | NBA "tight" 1.07 m edge plus 1.83 m |
| K23 | Latency | Offline pilot; latency measured, not a gate | Half-time packet within 600 s is a pilot goal |
| K24 | Officials' roles | 1 Hz plus 10 Hz in the 2 s around whistles | Per frame |
| K25 | Court constants | Exact edge-correct values (restricted area 1.270 m, frontcourt 12.700 m); mark verified | Keep current rounded config values |
| K26 | Rule 7-3.2.b throw-in spot | Free-throw line extended (diagram, PDF p. 85) | Elbow-to-corner reading |
| K27 | "Shooting" foul | Context flag on the foul; class list follows the book | Keep "shooting" as a foul class |
| K28 | Garbage time | Win-probability rule primary; CTG-adapted and source flags kept as views | CTG-adapted rule primary |
| K29 | Numbering | One N-<FAMILY>-nn series with an old→new map | Keep the round-by-round IDs |

## Decisions (Aldemir, 2026-10-18, in chat)

"Delegated" = Aldemir left the choice to the Mac session; the session chose the recommended option, reason given.

| K | Choice | Note |
| --- | --- | --- |
| K01 | A (delegated) | Aldemir's concern: fast-break sprints exceed 30 km/h. 30 km/h = 8.33 m/s; the hard limit 10 m/s = 36 km/h is above measured D-I peaks (6.2–7.0 m/s), so real sprints are never cut. A value above 10 m/s (over ≥ 0.3 s) is marked invalid and sent to identity/tracking review; the raw value is kept, never deleted. Add distance-over-time metrics (N-PL-06). |
| K02 | A | |
| K03 | A | |
| K04 | A | Four coarse classes first, the 13 fine coverages after the gate. The coarse classes group the fine ones Aldemir named (drop, flat hedge, hard hedge, blitz/trap incl. sideline trap, ice/blue/down, switch). Note: pick-and-roll and down screen are offensive actions (the trigger), not coverages. |
| K05 | A (delegated) | Primary run = net ≥ 8 points in 120 s; broadcast "a-b" shown at net ≥ 8. |
| K06 | A | Plus a new close-game parameter (N-MD-13). |
| K07 | A | |
| K08 | A | |
| K09 | Hybrid (A refined) | Approved after research (k09_state_storage_research.md): transitions + segments + clock map stored; per-frame state rebuilt deterministically. See "K09 decision" below. |
| K10 | A, modified | Aldemir's timing: 2 fouls in the first 15 min of the first half (elapsed ≤ 900 s); 3 fouls early in the second half (> 600 s left); 4 fouls late in the second half (≤ 600 s left) and in overtime. |
| K11 | A | |
| K12 | A | |
| K13 | A (delegated) | 70%. Note: K13 is camera coverage of a player's time (share of seconds the player is in frame) for load statistics, not ball-screen coverage. |
| K14 | A | |
| K15 | A | |
| K16 | A | |
| K17 | A (delegated) | A baseline of fewer than 10 games is noise; record quantiles from game 1, give verdicts from game 11. |
| K18 | A | |
| K19 | A | |
| K20 | A | |
| K21 | A (delegated) | Substitutions happen only at dead balls (Rule 3-6), so 30 s misses legitimate hooks; first dead ball and 60 s, with matched baseline. |
| K22 | A | |
| K23 | A | |
| K24 | A | |
| K25 | A (delegated) | Exact rule-book edges are correct for rule tests; "verified: true" only after the diagram values are checked at full resolution. |
| K26 | A (delegated) | The 2026-27 diagram and the 2025-26 change summary agree; the text is a typo. |
| K27 | A | |
| K28 | A | |
| K29 | A | |

## New proposals from Aldemir's answers (2026-10-18)

| ID | Tier | Requirement | Acceptance |
| --- | --- | --- | --- |
| N-MD-13 | Shall | Store a game-closeness record per game and per possession: max absolute margin over the game, seconds spent with margin ≤ 3 / ≤ 5 / ≤ 6 points, lead changes, ties, and a close-game class (max absolute margin ≤ 6 points after the first 300 s, initial value to calibrate); every possession carries a leverage weight (change in win probability between a score and a stop) so each basket in a close game is weighted more. | All 4 fields present for 100% of games; leverage weights sum-check: mean leverage of possessions in close-class games > that of other games on the season set. |
| N-PL-06 | Shall | Store distance-over-time measures per player: metres covered in rolling 5 s windows, time to cross the division line from possession start (s), time from own baseline to the opposite free-throw line, sprint segments (speed ≥ 7.0 m/s for ≥ 1.0 s; initial value) with length (m), peak and mean speed (m/s, km/h shown). | Values reported only where position error ≤ 0.5 m over the window; distance error ≤ 5% against 50 hand-measured court-line crossings. |
| N-CX-10 | Shall | Every parameter used by any model or index is registered once (name, definition, unit, source table/column, valid range, default weight, who may change it) in a parameter registry; every model output stores its per-parameter contributions per frame and per incident (event, possession), so each frame or incident can be dissected and re-weighted without re-running the pipeline. | 100% of model inputs resolve to a registry entry; for any incident, the stored contributions sum to the output within 1e-6; changing one weight and re-scoring reproduces the new output from stored contributions. |
| N-SR-05 | Shall | Foul trouble per K10 (modified): flag a player with 2 fouls while first-half elapsed ≤ 900 s, 3 fouls with > 600 s left in the second half, 4 fouls with ≤ 600 s left in the second half or in overtime; thresholds read from config; the 2/4 rule kept as a named view. | Flags match the rule on 100% of a 200-row synthetic test; config change re-flags without code change. |

## K09 decision (Aldemir, 2026-10-18, in chat)

**Approved: hybrid** — `state_transitions` (typed, append-only) + `state_segments` (one row per dimension per interval, team-neutral, versioned) + `clock_map` (piecewise-linear game and shot clocks) are the stored truth; per-frame observations stay in `frames`, `ball_states`, `player_positions`; `state_frame` and `state_second` are rebuilt deterministically from segments after every change and never edited. This refines option A. Evidence and the approved requirement text: docs/requirements_review/k09_state_storage_research.md sections 4, 7 and 8 (R-MD-01, R-SR-06, N-MD-01, N-MD-02, N-SY-01, three segment-integrity invariants for N-IV-01, additions to N-SY-05 and N-CX-10). The texts there supersede the earlier proposed texts for those IDs in synthesis.md and proposals_consolidated.yaml.

## N-CX-10 acceptance added (Mac session, delegated by Aldemir, 2026-10-18)

N-CX-10 (with the K09 addition) gains this acceptance: after any state correction, re-scoring only the incidents that overlap the changed frame range yields exactly the same per-parameter contributions as re-scoring the whole game (0 differences, tolerance 1e-9), and no incident outside the changed frame range is re-scored (0 extra re-scores). N-IV-01 and N-SY-05 stand as written in k09_state_storage_research.md section 8.
