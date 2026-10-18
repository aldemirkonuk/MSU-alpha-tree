# Requirements inbox 006 · Market data collector requirements (proposed IDs)

Written 2026-10-18 by the Mac session (msu-colab) while building the B2 foundation. For the requirements session: these are **proposals**. `docs/requirements.md` has the market requirements only as prose ("Layered prediction and market benchmarks", "Odds and prediction-market data"), and the IDs named in prompt 002 (R-MK-01 to R-MK-09, R-DQ-01, R-DQ-05, R-RG-07, R-RG-08) do not exist there yet (`docs/markets/collector_design.md` section 0). Please renumber freely; every proposal keeps a pointer to the design section, the code module and the test that checks it, so the mapping survives renumbering.

Format: **Shall** = must hold before any live collection; **Should** = target, may be relaxed with a recorded reason. "Test" names the pytest file in `tests/markets/` that checks it today; "pending" means it needs a live source or a decision first.

## Proposed IDs for the names already used in prompt 002

| ID | Requirement | Design § | Module | Test |
|---|---|---|---|---|
| R-MK-01 | The collector **shall** be read-only by construction: one HTTP client with an allowlist of exact (host, method, path pattern); GET only except the listed Polymarket batch reads; refuses `POLY_*` headers and any `Authorization` header except the CBBD bearer on the CBBD host; no account, order, trading, portfolio, balance or wallet code anywhere in the package. | 6 | `markets/http.py`, `markets/sources/registry.py` | `test_guard.py` |
| R-MK-02 | Every response **shall** be written to the raw store before any parsing: gzip body as received, plus one manifest line (UTC fetch time in µs, source, method, endpoint, URL with credentials removed, status, quota headers, sha256, byte length, collector version, run ID, job ID). The only permitted change to a body is the Polymarket identity-field redaction, recorded in the manifest. | 3.1 | `markets/raw_store.py` | `test_raw_store.py` |
| R-MK-03 | Parsed prices **shall** be stored one row per priced outcome per market per book per snapshot, keyed on the ESPN event ID as the single join key, with the columns in design § 3.2. Spreads and moneylines are stored per team, never as home/away. | 3.2 | `markets/models.py`, `markets/store.py` | `test_models.py`, `test_store.py` |
| R-MK-04 | Every two-way or n-way market with a full set of prices **shall** carry fair probabilities by the power and Shin methods (plus multiplicative as baseline), each summing to 1 within 1e-9; one-sided markets store implied probability only. | 3.3 | `markets/devig.py` | `test_devig.py` |
| R-MK-05 | Snapshot schedule **shall** cover open, T−24 h (86,400 s), T−1 h (3,600 s) and close for every MSU and Big Ten game; first-half lines and props on game days; 1-minute prediction-market prices from T−10,800 s to final + 3,600 s for every MSU game. | 2 | `markets/schedule.py` | `test_schedule.py` |
| R-MK-06 | Each source's game **shall** be mapped to the ESPN event ID by unordered team pair plus time window; auto-accept needs exactly one candidate and \|Δt\| ≤ 5,400 s (or same US-Eastern date when one side has no time); everything else goes to the review queue with a reason code; unmatched rows are kept with `game_id = null` and flag `unmatched`. | 5 | `markets/matching.py` | `test_matching.py` |
| R-MK-07 | Team names **shall** resolve through a versioned crosswalk to ESPN team IDs; the fuzzy fallback never auto-accepts "State" vs non-"State" pairs or ambiguous "St." names. | 5.1 | `markets/matching.py` | `test_matching.py` |
| R-MK-08 | A source **shall** run only when it is enabled in `config/markets.yaml` and its blocking decision (design § 0) is recorded; all sources ship disabled. Paid sources (The Odds API) need Aldemir's written approval before any call. | 0, 7 | `markets/config.py` | `test_config.py` |
| R-MK-09 | Each run **shall** write a run record in `results/markets_<date>/` with counts only (rows per source, quota headers seen, contract failures by rule ID, match-queue size, completeness), never prices. | 8 | `markets/run_record.py` | `test_run_record.py` |
| R-DQ-01 | Every parsed row **shall** pass the row contracts C-01 to C-16; a failing row goes to quarantine with its rule ID and is never dropped silently (fail closed). | 4.2 | `markets/contracts.py` | `test_contracts.py` |
| R-DQ-05 | Cross-source differences above 0.5 points **shall** be flagged (`xsrc_gt_0p5`); the tiered rules XS-1 to XS-4 **should** run alongside with thresholds read from config until calibrated. | 4.1 | `markets/checks.py` | `test_checks.py` |
| R-RG-07 | Credentials **shall** come only from environment variables (`CBBD_API_KEY`, later `ODDS_API_KEY`), never from files in git, and **shall** be stripped from every stored URL, manifest line and log. | 3.1, 6 | `markets/http.py`, `markets/raw_store.py` | `test_guard.py`, `test_raw_store.py` |
| R-RG-08 | Raw and parsed market tables **shall** stay private (MyDrive or local, never git, never shared); published outputs carry derived statistics only (CLV summaries, calibration, skill scores). | 6 | `markets/store.py` (paths), `.gitignore` | `test_store.py` (path guard) |

## New proposals (extensions found while building)

| ID | Requirement | Why | Module | Test |
|---|---|---|---|---|
| new-MK-10 | All times **shall** be stored as UTC with microsecond precision; US-Eastern is used only for date matching and weekly windows, computed with `zoneinfo` ("America/New_York"), never fixed offsets. | Kalshi/Polymarket dates are Eastern, ESPN is UTC (design § 5.2); DST shifts break fixed offsets | `markets/timeutil.py` | `test_timeutil.py` |
| new-MK-11 | Odds conversions **shall** keep the American integer as received and derive decimal and implied probability from it; exchange rows derive American from probability. | Odds API notes rounding in decimal before 2022-09-18 (design § 3.2) | `markets/odds.py` | `test_odds.py` |
| new-MK-12 | Rows **shall** be de-duplicated on the C-14 key (game, source, book, market, phase, snapshot label, side, team/player, line, snapshot time). | One ESPN/CBBD response yields open and close with the same fetch time | `markets/store.py`, `markets/contracts.py` | `test_store.py` |
| new-MK-13 | A CBBD spread that is null while the total is present **shall** be flagged `possible_pickem`, not read as "no line". | CBBD maps 0 to null (design § 1.1 notes) | `markets/sources/cbbd.py` | `test_parse_cbbd.py` |
| new-MK-14 | Integer lines **shall** be marked `line_is_integer`, and their fair probability is P(cover \| no push). | Push possible on whole-number lines | `markets/models.py`, `markets/parse.py` | `test_parse_cbbd.py` |
| new-MK-15 | Margin removal with booksum ≤ 1 **shall** fall back to multiplicative and set `booksum_le_1`; π is always stored. | Exchange mids and stale books (design § 3.3) | `markets/devig.py` | `test_devig.py` |
| new-MK-16 | Every snapshot table write **should** carry a `schema_version`; a schema change bumps it and adds a migration note. | Parquet files outlive code versions | `markets/models.py` | `test_models.py` |
| new-MK-17 | The default fair-probability method **should** be chosen by an NCAAB log-loss and Brier comparison on 2021-22 to 2025-26 moneylines before results are published. | No study compares methods on NCAAB (design § 3.3) | (analysis, later) | pending |
| new-MK-18 | The collector **should** alert when weekly completeness is below 95% for two weeks in a row, when an MSU game lacks a close from any enabled source, or when a source's unmatched share exceeds 2%. | Design § 4.3 | `markets/checks.py` | `test_checks.py` (completeness maths); alerts pending |

## Open questions for Aldemir (one line each; all already in design § 0)

- Register a free CBBD key (decision 1); the CBBD module stays disabled until `CBBD_API_KEY` is set and `cbbd.enabled: true`.
- ESPN option (i) schedule only, (ii) schedule and odds, or (iii) none (decision 2).
- Kalshi terms (decision 5) and Polymarket terms plus identity-field stripping (decision 6).
- Collector host: always-on Mac or a small cloud VM (decision 7).
- Tiered cross-source tolerances vs the single 0.5-point rule (decision 8).
