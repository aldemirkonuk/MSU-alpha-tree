# Requirements inbox 011 · Expansion: data platform, capture and products

From: Mac session (msu-colab), 2026-10-19. Aldemir: "do the most advanced selection and most real life applicable,
meaning it actually works, keep expanding. what else can we add". To: requirements session. Status: proposal
(add-only). Each row closes a gap marked red in the alpha tree's "Data platform" branch, or adds something the
two pilot games showed we will need. IDs are placeholders (new-XX-nn); the requirements session assigns live IDs.

## A. Data platform (the parts that make the numbers trustworthy and repeatable)

| Proposal | Tier | Text | Acceptance |
| --- | --- | --- | --- |
| new-EN-10 | Shall | One command rebuilds any processed game from raw video, raw pulls and config. Stage outputs are stored under a content hash of their inputs, with a manifest and a `current` pointer, so a fix re-runs only the stages whose inputs changed. | Rebuilding a game twice gives byte-identical outputs; changing one config value re-runs only the dependent stages (measured on the two pilot games). |
| new-EN-11 | Shall | Every row ID is derived from content (source, game, type, clock, order, source row ID), never from run order. | Two runs on the same inputs give identical IDs (already shown for transitions on the pilot games); 0 duplicate keys after a re-run. |
| new-EN-12 | Shall | One query layer: SQL (DuckDB) over the Parquet lake, with a view per grain (frame, second, event, possession, chance, player-game, lineup stint, team-season), and every stat served through its metric-registry ID. | Every metric with computable_now = yes is queryable by ID; a dashboard number and the same query return the same value. |
| new-EN-13 | Shall | Stages run as a dependency graph with a run record per stage (inputs, versions, row counts, duration, cost) and lineage from every output row to its inputs and config version. | For a random 1% of output rows the lineage resolves to input files and config hashes (100%). |
| new-EN-14 | Shall | Continuous integration on every push: tests, data contracts, invariants, the metric unit tests on the pilot fixtures, and a secret and licensed-data scanner (the repo is public). | A push containing an API key pattern or a licensed file is blocked; CI runs on every commit to main. |
| new-EN-15 | Shall | Reproducible environment: pinned Python version and a committed lockfile; tests run from a clean checkout. | A fresh clone passes all tests with one install command (today the repo .venv is broken). |
| new-DQ-11 | Shall | Data observability per table and game: row volume, null rates, freshness and value distributions, with alerts; drift verdicts from game 11 (K17). | Every table has monitors; an injected fault (dropped rows, shifted clock) raises an alert within one run. |
| new-FD-13 | Shall | An ID crosswalk over time for teams, players, coaches and officials across ESPN, CBBD, KenPom, Torvik and EvanMiya, with valid-from, valid-to and known-at dates. | 100% of players on the pilot rosters resolve in every source we use; transfers and name changes resolve to one player_id. |
| new-SY-12 | Shall | Play-by-play is pulled again after a game and every revision is versioned and diffed; downstream tables are re-scored only where the changed clock range overlaps. | A synthetic PBP correction changes only the overlapping segments and stats; old versions stay readable. |
| new-DT-15 | Should | Uncertainty is carried into every tracking-based stat as an interval (position error, identity confidence, imputed share), not dropped after tracking. | Each tracking stat has a 95% interval; coverage of the interval checked on gold-v1 (90–98%). |
| new-MD-21 | Shall | Stored state is team-neutral; MSU views are derived (D06). The whole state fold runs for any D-I game from play-by-play alone. | The pbp_only fold runs on a non-MSU game with 0 untyped transitions and 0 segment breaks. |
| new-CS-11 | Should | A measured cost and throughput model per game: GPU-seconds, storage, API calls and money, per stage. | Season plan computed from measured per-game numbers; actuals within 25% of plan after 5 games. |
| new-HR-10 | Shall | A chosen labelling tool for gold-v1 with inter-rater agreement measured on a shared sample. | Tool chosen and documented; agreement (Cohen's kappa) reported per label type on ≥ 50 shared possessions. |

## B. Capture: better video for 2026-27 (the YouTube replays are 29.97 fps)

| Proposal | Tier | Text | Acceptance |
| --- | --- | --- | --- |
| new-VI-17 | Shall | Own recordings of 2026-27 games capture the broadcast at its native rate (US sports broadcasts are 720p59.94 or 1080i59.94), deinterlaced to 59.94 fps progressive, full game including stoppages, with original audio. | Recorded files show 59.94 fps constant and no dropped frames over a full game; timing tests then use ±2 frames at 16.7 ms. |
| new-VI-18 | Should | Record the live game start to final without cuts, so the clock map is continuous (condensed replays remove stopped time). | Video time is linear to UTC for the whole recording (one clock map stretch per stoppage, no cuts). |
| new-VI-19 | Should | Capture timestamps in UTC at recording time, so in-game market prices join by real time, not by PBP wallclock (which runs backwards up to 227 s). | est_utc error ≤ 1 s for every transition of a recorded game. |

## C. What the data serves (products, each built only from registered metrics)

| Proposal | Tier | Text | Acceptance |
| --- | --- | --- | --- |
| new-PR-12 | Shall | A views catalogue: each output (post-game report, opponent scouting packet, player card, lineup board, in-game state panel, pre-game card) lists its audience, grain, metrics by registry ID, refresh time and as-of rule. | Every view's numbers resolve to metric IDs; 0 numbers defined only in a view. |
| new-OS-05 | Should | League-wide opponent packets from play-by-play alone (state fold, possessions, chances, the box and PBP tiers of the stat catalogue) for every Big Ten opponent before each game. | Packet ready 24 h before tip for every 2026-27 Big Ten opponent. |
| new-PR-13 | Should | The live game state (docs/data/live_game_state.md) is shown as one panel per game, readable at any instant of a recorded game. | The panel at any instant equals the as-of view of the stored truth (0 differences on the pilot games). |
| new-PR-14 | Shall | Every model has a model card (data, period, features by metric ID, held-out and walk-forward scores, known failures) and every prediction stores the model version. | 100% of stored predictions resolve to a model card. |
