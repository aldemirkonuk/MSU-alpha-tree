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
