# Stat catalogue

Status: proposed, 2026-10-18. Registry: [`config/metrics.yaml`](../../config/metrics.yaml). Requirements note: [`coord/requirements_inbox/009-stat-catalogue.md`](../../coord/requirements_inbox/009-stat-catalogue.md).

## Purpose

One list of every basketball statistic this project computes, reads from an outside system, or keeps for reference: box score, play-by-play, broadcast tracking, betting markets and published rating systems (ESPN, KenPom, Torvik, EvanMiya, NBA.com, Synergy-style play types, research papers). Each statistic has one id, one formula, its inputs as `table.column` from `schema/tables/`, its unit, the grain it is stored at, when it is knowable (as-of rule), the data it needs, and the parameters a user may re-weight. Code that computes a stat resolves it to one id here; the parameter registry (R-CX-29) reads each metric's `parameters`, so any frame or incident can be dissected and re-weighted.

## How to read an entry

| Field | Meaning |
| --- | --- |
| id | Stable id `M-<CODE>-nnn` (see id scheme). |
| name, aliases | Our name; aliases are the names other sources use (ESPN, KenPom, Torvik, EvanMiya, NBA.com, Synergy, papers), so any external name finds one id. |
| definition, formula | What it measures and how it is computed from the inputs. `sub_metrics` splits a bundled entry into lettered outputs. |
| inputs | `table.column` in `schema/tables/*.yaml`; `external:<source>.<field>` for an outside field; `proposed:` for a column this catalogue proposes (`proposed_columns`). |
| unit, level | Unit (metres, seconds, degrees, m/s, m/s², points, possessions, percent 0-100, probability 0-1) and grain (frame, event, shot, possession, chance, player-game, team-season, lineup ...). |
| direction | higher_is_better, lower_is_better, neutral (descriptive), by_variant or per_component (`direction_note` explains). |
| data_tier, computable_now | Data the metric needs and whether it can be computed today (tables below). |
| min_sample | Smallest sample at which the number is shown or used. |
| as_of_rule | When the value is knowable. Pre-game features use only data stamped before tip; in-game features only rows known at that instant (blind pass). |
| variants | Splits and re-scalings stored with the same id (per 40, per 100, by half, by zone ...). |
| parameters | Thresholds, windows, weights and constants: `key`, `default`, `unit`, `registry: R-CX-29`. |
| related_requirements | Live requirement IDs (acceptance_tests.yaml, fold_id_map.csv). |
| why | Why the project needs it. |
| verified, sources | Whether the formula was confirmed on an opened source, and the sources (web URL, `repo:` path, or `local:` header-only file). |
| depends_on, alias_of, variant_of, canonical_id | Links between entries; an alias stub points at the owner entry. |
| provenance | Harvest bookkeeping (merged input names, former ids). Not used by code. |

## Id scheme

`M-<CODE>-nnn`: `M` = metric, `<CODE>` = category code, `nnn` = three-digit number, stable and never reused. A letter after the number (`M-SIT-084a`) marks a split of a retired id; `sub_metrics` use the parent id plus a letter inside the entry. Category codes:

| Code | Category | Metrics | Scope |
| --- | --- | --- | --- |
| TEFF | [team_efficiency](team_efficiency.md) | 53 | Possessions, chances, pace, raw offensive and defensive efficiency, Four Factors and per-100 rates (not opponent-adjusted). |
| TRAT | [team_ratings](team_ratings.md) | 79 | Opponent-adjusted ratings, Elo, RPI/NET-style resumes, quadrants, polls, prediction systems and blends, strength of schedule, luck, program context. |
| SHOOT | [shooting](shooting.md) | 77 | Makes, attempts and percentages by shot type and zone, TS% and eFG%, shooter skill posteriors, hot hand, release and footwork. |
| SQ | [shot_quality](shot_quality.md) | 59 | Shot location in the attacked-rim frame, shot diet, shot-clock at release, contest geometry, expected points and shot-making over expected. |
| PASS | [playmaking](playmaking.md) | 93 | Assists, potential and adjusted assists, passes, touches, drives, decision latency, advantage chains, passing networks and creation. |
| TOV | [turnovers_steals](turnovers_steals.md) | 53 | Turnovers by type, turnover rates per possession and chance, steals, held balls, points off turnovers, expected turnovers. |
| REB | [rebounding](rebounding.md) | 68 | Offensive and defensive rebounds and rates, rebound chances, box-outs, putbacks, second-chance efficiency, rebounds over expected. |
| FOUL | [fouls_ft](fouls_ft.md) | 161 | Fouls by class and situation, fouls drawn, bonus, free throws and free-throw mechanics, and-ones, officials, reviews. |
| DEF | [defense](defense.md) | 134 | Opponent shooting and shot diet allowed, contests, rim protection, coverages, rotations, matchups, scheme states, defensive ratings. |
| TRN | [transition](transition.md) | 68 | Transition flags and windows, start types, seconds to first shot, numbers advantage, get-back, take fouls, transition efficiency both ways. |
| PLAY | [play_types](play_types.md) | 69 | Synergy-style play types, ball-screen and hand-off actions, cuts, alignments, mismatch hunting, PPP by play type and coverage. |
| SPACE | [spacing_offball](spacing_offball.md) | 57 | Spacing geometry, floor balance, Voronoi real estate, off-ball scoring opportunity, gravity, cuts and off-ball movement. |
| PHYS | [physical](physical.md) | 103 | Court-plane kinematics, distance, speed and acceleration bands, high-intensity efforts, jumps, load and recovery (no private health data). |
| IMP | [impact](impact.md) | 74 | Plus-minus, on/off, lineup ratings, RAPM and box priors (BPM, BPR), win shares, wins above replacement, per-frame value credit. |
| PROF | [player_profile](player_profile.md) | 95 | Games, minutes, usage, roles and positions, role clusters, class and eligibility, returning minutes, transfers, honours. |
| SIT | [situational](situational.md) | 100 | Game clock and score state, runs, clutch, leverage, win probability and WPA, game descriptors, schedule and venue spots. |
| COACH | [coaching](coaching.md) | 95 | Timeouts, challenges, substitutions and rotations, foul-trouble and end-game decisions, play calling, adjustments, coach measures. |
| MKT | [market](market.md) | 133 | Betting lines and implied probabilities, fair-probability methods, line movement, CLV, ATS, totals, forecast scoring and calibration. |
| | **Total** | **1571** | |

## Data tiers

| Tier | Meaning | Metrics |
| --- | --- | --- |
| box | Box-score totals (team_box, player_box) from ESPN or CBBD box rows; computable today. | 326 |
| pbp | Play-by-play events (events, shots, free_throws, timeouts, substitutions): needs the PBP load and possession builder. | 433 |
| tracking_broadcast | Our computer-vision tracking from broadcast video (player_positions, ball_states, pose): needs the tracking pipeline. | 574 |
| tracking_pro_only | Needs 3-D ball or hand/pose precision that in-arena optical tracking gives; from single-camera broadcast it is research-only until the calibration gate (R-CG-11) passes. | 15 |
| market | Betting-market data (market_snapshots, lines_odds_snapshots): needs the markets collector (config/markets.yaml). | 113 |
| external_only | Published by an outside system (KenPom, Torvik, EvanMiya, NBA, Synergy, BBall Index ...); we store their values as-of-date, we cannot recompute them. | 109 |
| experimental | Needs a model or label set that does not exist yet (e.g. a validated gesture classifier). | 1 |

| computable_now | Meaning | Metrics |
| --- | --- | --- |
| yes | Computable today from data already pulled or describable from box rows. | 399 |
| after_pbp | Computable once play-by-play is loaded and possessions are built. | 442 |
| after_tracking | Computable once broadcast tracking (positions, ball, pose) runs. | 586 |
| external | Read from an external publisher's snapshot; not recomputed by us. | 120 |
| conditional | Computable once a named load or verification is done (see computable_now_note). | 6 |
| reference_only | Kept for definition and comparison only (method unpublished or data licence blocks use). | 9 |
| no | Not computable with any planned data or model yet. | 9 |

## Counts

Per category and data tier:

| Category | box | pbp | tracking_broadcast | tracking_pro_only | market | external_only | experimental | Total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| team_efficiency | 24 | 20 | 4 | 0 | 0 | 5 | 0 | 53 |
| team_ratings | 53 | 11 | 0 | 0 | 1 | 14 | 0 | 79 |
| shooting | 21 | 26 | 19 | 3 | 1 | 7 | 0 | 77 |
| shot_quality | 2 | 36 | 19 | 1 | 0 | 1 | 0 | 59 |
| playmaking | 13 | 10 | 68 | 0 | 0 | 2 | 0 | 93 |
| turnovers_steals | 16 | 11 | 25 | 0 | 0 | 1 | 0 | 53 |
| rebounding | 15 | 17 | 35 | 0 | 0 | 1 | 0 | 68 |
| fouls_ft | 36 | 82 | 35 | 5 | 1 | 2 | 0 | 161 |
| defense | 22 | 14 | 92 | 1 | 0 | 4 | 1 | 134 |
| transition | 4 | 16 | 48 | 0 | 0 | 0 | 0 | 68 |
| play_types | 0 | 5 | 64 | 0 | 0 | 0 | 0 | 69 |
| spacing_offball | 0 | 2 | 51 | 0 | 0 | 4 | 0 | 57 |
| physical | 14 | 2 | 74 | 4 | 0 | 9 | 0 | 103 |
| impact | 25 | 27 | 6 | 0 | 0 | 16 | 0 | 74 |
| player_profile | 40 | 18 | 13 | 1 | 1 | 22 | 0 | 95 |
| situational | 15 | 71 | 9 | 0 | 3 | 2 | 0 | 100 |
| coaching | 11 | 65 | 12 | 0 | 0 | 7 | 0 | 95 |
| market | 15 | 0 | 0 | 0 | 106 | 12 | 0 | 133 |
| **Total** | **326** | **433** | **574** | **15** | **113** | **109** | **1** | **1571** |

Per category and computable now:

| Category | yes | after_pbp | after_tracking | external | conditional | reference_only | no |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| team_efficiency | 26 | 20 | 4 | 3 | 0 | 0 | 0 |
| team_ratings | 54 | 11 | 0 | 14 | 0 | 0 | 0 |
| shooting | 21 | 26 | 22 | 7 | 1 | 0 | 0 |
| shot_quality | 3 | 35 | 20 | 1 | 0 | 0 | 0 |
| playmaking | 12 | 9 | 66 | 2 | 0 | 0 | 4 |
| turnovers_steals | 16 | 11 | 25 | 1 | 0 | 0 | 0 |
| rebounding | 15 | 17 | 35 | 1 | 0 | 0 | 0 |
| fouls_ft | 37 | 82 | 41 | 1 | 0 | 0 | 0 |
| defense | 21 | 15 | 92 | 3 | 0 | 0 | 3 |
| transition | 4 | 16 | 48 | 0 | 0 | 0 | 0 |
| play_types | 0 | 5 | 64 | 0 | 0 | 0 | 0 |
| spacing_offball | 0 | 2 | 51 | 3 | 0 | 1 | 0 |
| physical | 14 | 2 | 77 | 10 | 0 | 0 | 0 |
| impact | 25 | 23 | 6 | 10 | 0 | 8 | 2 |
| player_profile | 47 | 18 | 14 | 16 | 0 | 0 | 0 |
| situational | 35 | 54 | 9 | 2 | 0 | 0 | 0 |
| coaching | 5 | 65 | 12 | 8 | 5 | 0 | 0 |
| market | 64 | 31 | 0 | 38 | 0 | 0 | 0 |
| **Total** | **399** | **442** | **586** | **120** | **6** | **9** | **9** |

Per category and verification:

| Category | true | partial | false | internal | harvest_only |
| --- | ---: | ---: | ---: | ---: | ---: |
| team_efficiency | 24 | 12 | 3 | 14 | 0 |
| team_ratings | 55 | 15 | 6 | 3 | 0 |
| shooting | 55 | 0 | 22 | 0 | 0 |
| shot_quality | 48 | 0 | 11 | 0 | 0 |
| playmaking | 66 | 11 | 16 | 0 | 0 |
| turnovers_steals | 29 | 6 | 18 | 0 | 0 |
| rebounding | 50 | 0 | 18 | 0 | 0 |
| fouls_ft | 124 | 0 | 37 | 0 | 0 |
| defense | 70 | 14 | 50 | 0 | 0 |
| transition | 43 | 0 | 25 | 0 | 0 |
| play_types | 61 | 0 | 8 | 0 | 0 |
| spacing_offball | 27 | 8 | 22 | 0 | 0 |
| physical | 80 | 10 | 13 | 0 | 0 |
| impact | 35 | 31 | 1 | 7 | 0 |
| player_profile | 70 | 0 | 25 | 0 | 0 |
| situational | 58 | 3 | 9 | 25 | 5 |
| coaching | 76 | 5 | 14 | 0 | 0 |
| market | 100 | 0 | 33 | 0 | 0 |
| **Total** | **1071** | **115** | **331** | **49** | **5** |

Other counts: 9818 input references (9153 resolve to a proposed schema column, 397 external fields, 189 columns proposed by this catalogue, 79 unresolved); 3763 source citations (5 metrics without a source, all project definitions marked verified = false); 185 metrics declare parameters (275 distinct keys); 15 need a schema change; 8 alias or cross-reference stubs; 412 distinct requirement IDs cited.

## How a metric links to tables and requirements

- **Tables.** `inputs` name the columns of `schema/tables/<table>.yaml` (status proposed). The dictionaries `docs/data/dictionary_games.md`, `dictionary_players.md` and `dictionary_state.md` define those columns, and `docs/data/source_field_map.md` maps them to ESPN, CBBD, hoopR, Torvik and KenPom fields. A column the catalogue needs but the schema lacks is listed in the metric's `proposed_columns` (or the category's `schema_gaps`).
- **Grain.** `level` says where the value is stored (frame, event, possession, chance, player-game, lineup, team-season ...). Season and profile values aggregate the stored atoms; nothing is computed only at season level when an atom exists.
- **Time.** `as_of_rule` follows the leakage rule: pre-game features use only rows stamped before tip (ratings snapshots dated the day before, closing lines captured before tip); in-game features use only blind-pass rows known at that instant; forward-looking windows are outcomes, never features.
- **Requirements.** `related_requirements` cite live requirement IDs. The parameter registry is **R-CX-29** (was N-CX-10); R-CX-20 is the previous-game context requirement.
- **Licence.** Values copied from ESPN, hoopR ESPN and NCAA-engine files are reference only (see the `licence` legend in the schema tables); CBBD values may be model inputs. External ratings (KenPom, Torvik, EvanMiya) are stored as dated snapshots and labelled `external`.

## How weights and parameters work

1. Every threshold, window, weight or constant in a formula is a parameter with a `key`, `default` and `unit` (for example the free-throw coefficient in possessions, a transition window in seconds, a garbage-time margin). The metric lists it under `parameters`; `parameter_index` at the end of the YAML lists each key once with the metrics that use it. That index seeds the R-CX-29 registry, which adds valid range, owner and who may change it.
2. Computation stores the atom (per frame, event, possession or incident) and, for model-based metrics, each parameter's contribution to the output keyed by (video_id, frame_index or incident_id, state_version), as R-CX-29 requires. Some entries already describe this under `contributions`.
3. Re-weighting changes a parameter value in the registry and re-scores from the stored contributions, without re-running video or PBP processing. R-CX-29's acceptance: stored contributions sum to the output within 1e-6, and re-scoring after one weight change reproduces the new output.
4. Keys marked `key_status: provisional` were named during assembly from a text description; the registry owner fixes the final name. Only 185 of 1571 entries declare parameters today; many formulas carry fixed numbers inline that must become parameters before they are computed (see inbox 009).

## Verification and caveats

- `verified: true` means the formula or definition was confirmed on a page or file opened while writing the entry; `partial` means the measure is named by a source but the formula was partly inferred; `false` marks our own proposal or an unconfirmed claim. Treat `false` and `partial` formulas as proposals until a unit test on a fixture game confirms them.
- Paid or keyed systems (KenPom, EvanMiya, Synergy, BBall Index) were read only from public pages and glossaries, and local EvanMiya/Kaggle exports only for their header rows. No data tables were scraped and no keyed API was called.
- Excluded by project rule: race or ethnicity, face data, private health (heart rate and similar), private social media.
- Corrections made while assembling (52): the parameter registry was cited as R-CX-20 in the impact category and one market entry and is now R-CX-29; one dangling reference to the split id M-SIT-084 now points to M-SIT-084a; one null formula (vendor projection) now says the formula is unpublished; one `see_owner` computable-now value now inherits from its owner; bare repository paths and local export names in source URLs now use `repo:` and `local:`; absolute local paths were removed.

> Note 2026-10-18 (Mac session review): the assembled registry had `verified: true` on every metric; the true status was restored from each entry's `verified_source_value`. Current counts: true 1,071, false 340, partial 105, internal 50, harvest_only 5.

## Dated note 2026-10-19

- Verification pass on the 450 unconfirmed formulas: [verification_2026-10-19.md](verification_2026-10-19.md). Registry version 0.2.0. Verified now: true 1,105 · partial 154 · internal 287 · reference_only 41 · false 4. Every metric now declares a `value_range` (percent 0-100, probability 0-1, other units by rule or by the verifier).
- New category [decision_trees](decision_trees.md) (TREE, 20 stats): pre-registered condition → branch → leaf trees with shrinkage, false-discovery control and walk-forward checks, plus the Monte Carlo lineup duel and game-script what-if simulator. Total metrics: 1,591.
- L4 reproduction on CBBD data for MSU 2025-26 and the 30 unit fixes: [l4_reproduction_2026-10-19.md](l4_reproduction_2026-10-19.md). Registry version 0.3.0; 42 metrics now at L4, 10 at L5.
- L4 round 2 (play-by-play, situational, KenPom and Torvik): [l4_round2_2026-10-19.md](l4_round2_2026-10-19.md). Registry 0.3.1; 46 metrics at L4, 12 at L5.
- Depth pass on the 1,115 previously confirmed stats and play-by-play counts reproduced against the box: [depth_pass_2026-10-19.md](depth_pass_2026-10-19.md). Registry 0.4.0: every stat has a depth label (L4 119, L5 16); verified true 397, partial 637, internal 480, reference_only 63, false 14.
- L4 round 4 (the 80 recipe metrics) and the 108 unit and range fixes: [l4_round4_units_2026-10-19.md](l4_round4_units_2026-10-19.md). Registry 0.5.0: L4 137, L5 34.
- 35 formula fixes approved by Aldemir and applied: registry 0.6.0 ([formula_fixes_proposed_2026-10-19.md](formula_fixes_proposed_2026-10-19.md)).
