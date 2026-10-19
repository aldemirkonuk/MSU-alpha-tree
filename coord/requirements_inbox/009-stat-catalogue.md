# Requirements inbox 009 · Stat catalogue and metric registry

From: stat-catalogue build (2026-10-18). To: requirements session. Status: proposal, not yet agreed with Aldemir. Nothing in the live doc, `schema/` or `src/` was edited; this pass added only the files below.

## What exists (add-only)

| File | Content |
| --- | --- |
| `config/metrics.yaml` | Machine-readable registry (status proposed): 1571 metrics in 18 categories, enums, counts, `parameter_index` (275 keys). Validated: ids unique, all required keys present, enums closed, references resolve, counts block matches the entries, `repo:` sources exist, no absolute local paths. |
| `docs/stats/README.md` | Purpose, how to read an entry, id scheme, data tiers, count tables, links to tables and requirements, how parameters and re-weighting work. |
| `docs/stats/<category>.md` (18) | One table per category (id, name, formula, unit, level, tier, now?, why) plus notes and sources. Generated from the YAML. |

## Counts

- Metrics: 1571. Per category: team_efficiency 53, team_ratings 79, shooting 77, shot_quality 59, playmaking 93, turnovers_steals 53, rebounding 68, fouls_ft 161, defense 134, transition 68, play_types 69, spacing_offball 57, physical 103, impact 74, player_profile 95, situational 100, coaching 95, market 133.
- Data tier: box 326, pbp 433, tracking_broadcast 574, tracking_pro_only 15, market 113, external_only 109, experimental 1.
- Computable now: yes 399, after_pbp 442, after_tracking 586, external 120, conditional 6, reference_only 9, no 9.
- Verified: true 1071, partial 115, false 331, internal 49, harvest_only 5.
- Inputs: 9818 references; 9153 of 9170 `table.column` references resolve to `schema/tables` (99.8%); 397 external fields; 189 proposed columns; unresolved: table `defender_attacker_probs` (4 refs) and 11 columns (screens.tag_defender_id, ratings_snapshots.as_of, shots.xpts_loc, shots.xpts_contest, market_snapshots.captured_utc, player_positions.passes_away, defensive_matchups.help_position, defensive_matchups.ghost_dev_m, defensive_matchups.ghost_xy_m, post_touches.possession_id, post_touches.video_ts_ms).
- Parameters: 185 metrics declare 275 distinct keys (0 conflicting defaults); 15 need a schema change; 8 alias or cross-reference stubs; 412 requirement IDs cited, all found in the live-doc export or the fold map.
- Sources: 3763 citations; 5 metrics have none (project definitions, verified = false: M-SHOOT-067, M-REB-013, M-PROF-054, M-MKT-037, M-MKT-083).
- Corrections made in assembly: 52 (parameter registry cited as R-CX-20 in impact entries and M-MKT-121, now R-CX-29; M-MKT-113 pointed at retired M-SIT-084, now M-SIT-084a; M-SQ-028 null formula; M-DEF-125 `see_owner`; source URL normalisation).

## Proposed requirements

New family R-MR (metric registry) unless the session prefers to file them under R-CX.

| Proposal | Tier | Text | Acceptance |
| --- | --- | --- | --- |
| new-MR-01 | Shall | `config/metrics.yaml` is the single metric registry. Every statistic the code computes, stores or displays, and every external statistic it reads, resolves to exactly one registry id; no stat is defined anywhere else. | A registry check over every output table and column declared in `schema/tables` and every stat label in `results/` finds 100% mapped to one id (0 unmapped, 0 mapped to two ids); the registry validates (unique ids, closed enums, all references resolve) in CI on every change. |
| new-MR-02 | Shall | Every metric with computable_now in {yes, after_pbp, after_tracking} has a unit test of its formula on a fixture before its first use in a result. | One test per id on hand-computed fixtures (first two MSU games plus synthetic edge cases: overtime, zero denominators, missing rows); counts and ratios exact, floats within 1e-9; coverage = 100% of `yes` metrics before the first release, and 100% of each later tier before that tier ships. |
| new-MR-03 | Shall | Every metric used as a pre-game or in-game feature obeys its `as_of_rule` (no data after the cutoff). | Leakage test: replacing all rows stamped after the cutoff (tip for pre-game, the frame time for in-game) with random values changes 0 feature values (tolerance 0) across all registered features on the fixture games; external rating features use only snapshots dated before tip. |
| new-MR-04 | Shall | Every threshold, window, weight or constant inside a registered formula is a parameter of that metric and an R-CX-29 registry entry. | A linter finds 0 numeric literals in metric code other than unit conversions and registry lookups; 100% of `parameters` keys exist in the R-CX-29 registry; `parameter_index` has 0 keys with conflicting defaults or units. |
| new-MR-05 | Should | Registry inputs resolve to the schema and units follow the project unit list. | 100% of `table.column` inputs resolve to `schema/tables` once the proposed columns are adopted (now 99.8%); 0 units in feet, inches or mph; every percent unit on 0-100 and every probability on 0-1. |
| new-MR-06 | Should | Registry change control: ids are never reused or renumbered; a retired id points to its successor; every change bumps `version` and is logged in `registry_change_log`. | Diff check between versions: 0 reused ids, 0 dangling references, 100% of changes logged with date and reason. |

## Open questions for Aldemir

- Adopt `config/metrics.yaml` as the single metric registry (new-MR-01), yes or no?
- File the six proposals as a new family R-MR, or under R-CX next to the parameter registry R-CX-29?
- Confirm the parameter registry is R-CX-29 (the brief said R-CX-20, which is the previous-game context requirement)?
- Which two games are the unit-test fixtures for new-MR-02 (the first two MSU games of the minimum build)?
- Keep the 109 external-only vendor metrics (KenPom, Torvik, EvanMiya, NBA, Synergy) as dated `external` entries, or keep only those we can recompute?
- Keep the 15 tracking_pro_only metrics (3-D ball and hand precision) as research-only behind the R-CG-11 gate, or drop them?
- Keep the 9 `no` metrics (no planned data or model) in the registry as placeholders, or remove them?
- Only 185 of 1571 metrics declare parameters today: require every inline number to become a parameter before a metric is computed (new-MR-04)?
- Send the schema gaps (table defender_attacker_probs, 11 missing columns, 189 proposed columns) to the schema session as one change set?
- Percent on 0-100 and probability on 0-1 everywhere, confirmed?
- The registry is 4.2 MB in one file: keep one file, or split into `config/metrics/<category>.yaml` with the same ids?

> Note 2026-10-18 (Mac session review): verification status corrected in config/metrics.yaml (it had been flattened to true): true 1,071 · false 340 · partial 105 · internal 50 · harvest_only 5. Unit tests on a fixture game must confirm every false/partial formula before use.

## Answers from Aldemir (2026-10-19)

| Question | Decision |
| --- | --- |
| Single registry (new-MR-01) | Yes. `config/metrics.yaml` is the single metric registry; CI enforces the mapping. |
| Family | New family R-MR, cross-referenced to R-CX-29. |
| Parameter registry id | R-CX-29 (already confirmed by the fold map: N-CX-10 → R-CX-29). |
| Unit-test fixtures (new-MR-02) | Games 401856571 (UConn, 27 Mar 2026) and 401856531 (Louisville, 21 Mar 2026). |
| 109 external-only vendor stats | Keep as dated snapshots (as-of date; model use only where the licence allows). |
| 15 tracking_pro_only stats | Keep, research-only, behind the calibration gate R-CG-11. |
| 9 `no` stats | Keep as placeholders; ids reserved, never reused. |
| Inline numbers (new-MR-04) | Every threshold, window, weight and constant becomes an R-CX-29 parameter before the stat is first computed; linter enforces it. |
| Schema gaps | Send to the schema session as one change set. |
| Number ranges | One universal convention: percent 0-100, probability 0-1. Any other bounded unit (ratings, z-scores, indexes) declares its range in the entry; unit tests reject values outside the declared range. Decided by the Mac session on Aldemir's "keep it universal and stick with certain num range". |
| File layout | Keep one file, `config/metrics.yaml`. Decided by the Mac session on Aldemir's "you decide": one file keeps the loader and the id-uniqueness check simple; per-category views stay in `docs/stats/`. |

Browsable view (private artifact): https://claude.ai/artifact/16Vgj5XFcqU7gDAJtJSotB
