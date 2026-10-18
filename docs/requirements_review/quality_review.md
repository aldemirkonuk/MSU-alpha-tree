# Requirements quality review (518 IDs)

Status: PROPOSAL, 2026-10-18. Requirements improvement pass. The live requirements doc is owned by the requirements session and was not edited; every rewrite below is a proposal that keeps its ID. Companion file: `docs/requirements_review/acceptance_tests.yaml` (one machine-readable acceptance test per ID, all 518).

Inputs read: live doc export of 18 Oct 2026 (`msu-basketball-cv-master-requirements-brainstorm-v0.md`, `requirement_ids.md`: 518 IDs, 43 families; byte-identical to the 10:38 export), `config/invariants.yaml` (including its `corrections:` list), `config/game_ontology.yaml` (576 leaves), `schema/tables/*.yaml` (104 tables), `docs/data/game_ontology_coverage.md`, `docs/research/load_thresholds.md`, `docs/research/transition_full.md`, `docs/research/data_sources_catalog.md`.

## 1. Method

Lens: ISO/IEC/IEEE 29148 characteristics of a single requirement (necessary, unambiguous, complete, singular, feasible, verifiable, correct, conforming) and of the set (consistent, non-redundant, traceable). The project's own format rules (doc section "Requirement format") were used as the conformance standard: one tier word (Shall or Should), a Test cell with a number, metric units, every row feeds a layer.

Steps:

1. A script parsed all requirement tables of the export (four table layouts: 454 rows ID/Tier/Product/Unit/Exceptions/Test/Source, 26 State-record rows with a Requirement column, 22 market-collector rows with a Runner ID column, 16 invariant rows with Check/On break/Rule). All 518 IDs were found once; no duplicate ID rows; no column mismatches.
2. A script built traceability: for each ID, the `schema/tables/*.yaml` files that list it in `requirements:` (declared) or anywhere in the file (column level), the `config/game_ontology.yaml` leaves that cite it, and whether `config/invariants.yaml` cites it. ID ranges such as `R-IV-01..16` were expanded.
3. Every row was read by hand (product, unit, exceptions, test, source) and judged against the lens. Issues were coded (table below). A row was scored **verifiable** when its Test cell has a pass value that can fail (a number with unit, a count of 0, or a named unit-test file); "recomputes", "reported", "present" and "measured" without a pass value were scored not verifiable, except for pure bookkeeping identities where an exact recomputation is the right test.
4. A TF-IDF similarity pass over all product texts (pairs with cosine > 0.35, 47 pairs) was used only to find duplicate candidates; each candidate was then judged by reading.
5. Rule-based rows were checked against the `corrections:` list in `config/invariants.yaml` (rule numbers verified there against the 2026-27 NCAA Men's Rules Book) and the rule-book gaps in `docs/data/game_ontology_coverage.md`.
6. Every problem row got a proposed rewrite (same ID, tier, text, acceptance criterion with units; split into ID-a/ID-b/ID-c when not singular) and a reason. Numbers: thresholds already in the live doc keep "(proposal)"; a number added here is marked "(initial value, to calibrate)" unless a repo research file supports it, in which case the file is cited.

Issue codes:

| Code | Meaning |
| --- | --- |
| NV | not verifiable: test has no measurable pass value, or only checks determinism ("recomputes") or presence |
| AMB | ambiguous: undefined term, vague word or unstated tolerance |
| NS | not singular: several requirements in one row |
| TIER | tier questionable |
| TR | traceability gap: no table/column in schema/tables carries it (process rules traced to files) |
| CONF | conflicts with another ID, the rules book or a config/invariants.yaml correction |
| CORR | rule reference or statement corrected in config/invariants.yaml |
| DUP | duplicate or overlap with another ID |
| UNIT | non-metric unit in requirement text |
| STALE | status or change-history text inside the requirement |
| FEAS | feasibility doubt against cited research |

## 2. Summary

- 518 IDs reviewed; **181 (35%) have at least one issue**; 337 need no change.
- Issues by type: NV 63, DUP 36, CONF 29, AMB 28, TR 28, NS 22, CORR 9, STALE 4, FEAS 3, TIER 3, UNIT 2.
- Verifiable as written: 455 of 518 (88%). Every ID now has an acceptance entry; 467 are ready, 36 need a value set (mostly a share of cases inside a stated tolerance), 15 need a decision by Aldemir.
- Traceability: every ID maps to at least one ontology leaf. 394 IDs are declared in some table's `requirements:` list; 97 more are cited only at column level; 27 are cited by no table (section 3.3).

| Family | Area | IDs | Shall | % verifiable | % with issues | Issue types | No table | Tests not ready |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| R-RR | Run records and failure analysis | 9 | 8 | 100 | 33 | AMB 1, NS 1, TR 1 | 1 | 0 |
| R-DQ | Data proof and quality | 10 | 9 | 100 | 40 | AMB 3, CORR 1, NS 1 | 0 | 0 |
| R-DS | Data sources | 15 | 11 | 93 | 40 | DUP 3, NS 2, NV 1, AMB 1, CONF 1 | 0 | 3 |
| R-RG | Rights, licences and ethics | 11 | 10 | 100 | 9 | TR 1 | 1 | 1 |
| R-FD | Foundation data | 12 | 10 | 100 | 42 | AMB 2, DUP 2, STALE 1, CONF 1 | 0 | 0 |
| R-PC | Player cards | 16 | 15 | 50 | 56 | NV 8, TR 2, NS 1 | 2 | 2 |
| R-MD | Global metadata | 20 | 18 | 95 | 25 | AMB 3, CONF 2, DUP 1, NV 1, NS 1 | 0 | 1 |
| R-ID | Player identity | 15 | 11 | 100 | 13 | DUP 1, TR 1, AMB 1 | 1 | 0 |
| R-VI | Video ingest | 16 | 14 | 88 | 25 | NV 2, NS 1, DUP 1, TR 1 | 1 | 2 |
| R-CG | Court geometry | 11 | 8 | 91 | 27 | STALE 1, TR 1, NV 1, NS 1 | 1 | 1 |
| R-DT | Detection and tracking | 19 | 17 | 95 | 26 | NS 2, FEAS 1, CONF 1, NV 1, AMB 1, UNIT 1 | 0 | 2 |
| R-BL | Ball | 8 | 7 | 100 | 12 | AMB 1 | 0 | 1 |
| R-GT | Vision gates | 5 | 4 | 100 | 20 | TR 1 | 1 | 0 |
| R-SY | Sync and possessions | 10 | 9 | 90 | 40 | CONF 2, NS 1, AMB 1, NV 1 | 0 | 0 |
| R-TR | Transition | 28 | 26 | 79 | 43 | NV 6, DUP 4, CONF 2, AMB 2, NS 1 | 0 | 6 |
| R-EV | Events | 16 | 15 | 100 | 19 | CONF 2, NS 1 | 0 | 0 |
| R-AU | Audio | 4 | 0 | 50 | 50 | NV 2 | 0 | 2 |
| R-RF | Referees and whistles | 7 | 5 | 100 | 29 | CONF 1, NS 1, DUP 1 | 0 | 0 |
| R-ST | Actions and sets | 26 | 22 | 88 | 19 | NV 3, CONF 1, AMB 1 | 0 | 2 |
| R-DF | Defensive structure | 21 | 20 | 86 | 29 | NV 3, DUP 2, NS 1 | 0 | 2 |
| R-VL | Value | 13 | 12 | 85 | 23 | NV 2, DUP 1 | 0 | 0 |
| R-CH | Chemistry and coaches | 8 | 7 | 62 | 50 | NV 3, DUP 2 | 0 | 1 |
| R-CC | Coach cards | 5 | 4 | 80 | 40 | NV 1, DUP 1 | 0 | 0 |
| R-GU | Game understanding | 6 | 4 | 83 | 50 | AMB 2, NV 1 | 0 | 3 |
| R-SR | State record | 15 | 13 | 80 | 67 | CONF 6, NV 3, DUP 3, NS 1, TR 1, UNIT 1 | 0 | 1 |
| R-IV | Invariants | 16 | 15 | 100 | 62 | CORR 8, CONF 4, TIER 1 | 0 | 1 |
| R-SB | Scoreboard and scorer errors | 4 | 3 | 75 | 50 | NS 1, NV 1, TIER 1 | 0 | 1 |
| R-MB | Made-basket detection | 7 | 7 | 71 | 29 | NV 2 | 0 | 1 |
| R-CX | Context features | 19 | 12 | 84 | 53 | DUP 5, TR 3, NV 3, AMB 1 | 3 | 0 |
| R-PL | Physical load | 17 | 12 | 71 | 59 | NV 5, CONF 4, AMB 2 | 0 | 6 |
| R-CO | Cognition | 8 | 6 | 62 | 62 | NV 3, FEAS 2, CONF 1, DUP 1 | 0 | 2 |
| R-OS | Opponent scouting | 5 | 3 | 100 | 0 | - | 0 | 0 |
| R-EN | Engineering | 8 | 7 | 100 | 12 | AMB 1 | 0 | 1 |
| R-CD | Coordination | 5 | 5 | 80 | 100 | TR 5, NV 1 | 5 | 0 |
| R-PR | Prediction | 11 | 9 | 82 | 36 | NV 2, AMB 2, NS 1 | 0 | 2 |
| R-PE | Possession engine | 13 | 12 | 77 | 23 | NV 3 | 0 | 2 |
| R-MK | Markets | 33 | 29 | 94 | 21 | DUP 3, NS 2, NV 2, TR 2, STALE 1, CONF 1, TIER 1 | 2 | 3 |
| R-HR | Human review | 12 | 10 | 92 | 8 | NV 1 | 0 | 1 |
| R-VZ | Visualization | 7 | 4 | 100 | 100 | TR 7, DUP 2, NS 1, AMB 1 | 7 | 0 |
| R-CS | Compute and storage | 10 | 9 | 90 | 30 | DUP 1, NV 1, NS 1, AMB 1 | 0 | 0 |
| R-VA | Validation | 9 | 9 | 100 | 44 | DUP 2, STALE 1, AMB 1 | 0 | 1 |
| R-HY | Hypotheses | 7 | 6 | 100 | 14 | TR 1 | 1 | 0 |
| R-PT | Pitch | 1 | 1 | 100 | 100 | TR 1 | 1 | 0 |
| **All** | | **518** | **438** | **88** | **35** | | **27** | **51** |

Shall counts include the one row whose tier cell reads "Shall / Should" (R-MK-22).

## 3. Set-level findings

### 3.1 Duplicates and overlaps (non-redundant)

Each group states the same product or rule more than once. Proposal: keep one row as the rule ("keeper"), turn the others into cross-references or merge them (add-only: the old rows stay, marked superseded by ID, per the doc's own add-only rule).

| # | IDs | What repeats | Proposed keeper |
| ---: | --- | --- | --- |
| D1 | R-CX-09, R-DS-04, R-FD-06, R-PC-14, R-CX-06, R-CX-18, R-OS-01 | No pre-game value may be dated at or after tip (leakage) | R-CX-09 as the one leakage rule; the others name their data and cite it |
| D2 | R-DS-02, R-DS-10, R-DS-14 | Restricted sources are never model inputs | R-DS-10 (use classes); R-DS-02 is its list, R-DS-14 a case |
| D3 | R-CC-05, R-CH-07, R-CX-19 | Head-to-head and prior-meeting history | R-CC-05 |
| D4 | R-MD-14, R-CX-15 (and distances in R-CX-14, R-CX-05) | Game context stamp: conference, round, seeds, neutral site, campus-to-venue distance | R-MD-14 |
| D5 | R-FD-11, R-CX-04, R-VI-13 | Arena fields (capacity, altitude, main-camera side) | R-FD-11 (arena registry) |
| D6 | R-TR-11, R-TR-18 | Parallel transition definitions per possession | R-TR-18 (fuller list) |
| D7 | R-TR-13, R-TR-20 | Break phase timestamps | R-TR-20 |
| D8 | R-TR-14, R-TR-23 | Pushing after makes and free throws | R-TR-23 |
| D9 | R-TR-12, R-DF-10, R-DF-20 | Transition defence: defenders back, who stops the ball, cross-matches | R-DF-20 (field list) with R-TR-12 for timing |
| D10 | R-VL-02, R-VL-09 | Credits in a chance sum to its value change | R-VL-02 |
| D11 | R-VL-01, R-SR-12 | Possession expected value (10 Hz vs 1 Hz) | R-VL-01; R-SR-12 is its 1 Hz view |
| D12 | R-VI-03, R-MD-11, R-SR-10 | Camera shot type per frame | R-VI-03 |
| D13 | R-MD-02, R-BL-01, R-BL-02, R-SR-06 | Ball control state, holder, position | R-MD-02 / R-BL rows; R-SR-06 lists the state columns |
| D14 | R-MK-02, R-MK-10, R-MK-16 (and R-MK-03) | Snapshot schedule and weekly coverage | R-MK-16 (spec) with R-MK-02 (coverage test) |
| D15 | R-MK-04, R-MK-15 | De-vig methods, probabilities sum to 1 | R-MK-15 |
| D16 | R-RR-01, R-CS-01 | GPU type, GPU-hours and units per run | R-RR-01 |
| D17 | R-HY-05, R-VA-08 | Result row for every tested hypothesis, nulls included | R-HY-05 |
| D18 | R-VA-05, R-VL-08, R-VZ-03 | Every number carries n and interval | R-VA-05 |
| D19 | R-EN-04, R-MD-09, R-VZ-02 | Every output traceable to frames, model version, confidence | R-EN-04 |
| D20 | R-CH-05, R-CO-08 | Clean vs late switches | R-CH-05 |
| D21 | R-CH-06, R-CC-02 | Timeout timing vs opponent runs | R-CC-02 |
| D22 | R-EN-03, R-VA-03 | Automatic official-record checks per game | R-EN-03 |
| D23 | R-DF-06, R-DF-16 | Ball-screen coverage label (one-level vs two-level) | R-DF-16 |
| D24 | R-ID-03, R-ID-09 | Identity limited to the PBP lineup | Keep both: constraint per frame (R-ID-03) vs outcome per possession (R-ID-09) |
| D25 | R-RF-07, R-MD-12, R-EV-14, R-EV-16, R-SR-04 | Held balls, arrow, reviews and challenges | R-MD-12 (arrow), R-EV-14 (jump balls), R-EV-16 (challenges); R-RF-07 keeps video reviews only |

### 3.2 Conflicts (consistent, correct)

| # | IDs | Conflict | Evidence | Proposed resolution |
| ---: | --- | --- | --- | --- |
| C1 | R-FD-08, R-DT-12, R-SR-07 vs R-IV-02 correction | "3 names" / "3 referees" / lead-trail-centre assume three officials; two or three are legal | config/invariants.yaml corrections (R-IV-02), Rule 2-1.1.a | Two or three officials everywhere; crew size in the games registry |
| C2 | R-RF-03 (9 foul types), R-SR-03 (different list) | "Intentional" is not a 2026-27 foul class; the two lists differ | docs/data/game_ontology_coverage.md gap 3 (new-RF-3), Rule 4-15.2.c.1.d | One foul-type list from the rules book, used by both rows |
| C3 | R-MD-07, R-SR-03, R-IV-09 | Team-foul reset for extra periods left to "config" | config/invariants.yaml corrections (R-SR-03 / R-MD-07, R-IV-09), Rule 5-9.4 | Reset only at the start of the second half; extra periods continue the count |
| C4 | R-IV-10 | "One extra 75-second timeout per extra period" is wrong in the media format | config/invariants.yaml corrections (R-IV-10), Rule 5-14.10.f, 5-14.10.a.1 | One 30 s timeout per extra period in the media format; carry-over cap of two |
| C5 | R-MD-13, R-SR-04 | Media-timeout slots miss the 15/10/5 marks and the 30 s pre-mark rule | config/invariants.yaml corrections (R-SR-04), Rule 5-14.10.c-e | Use the full Rule 5-14.10 definition in both rows |
| C6 | R-SR-09 | "Technical 2" for all technicals | config/invariants.yaml corrections (R-SR-09), 10-3/10-4 Penalty | Class A 2, Class B 1, administrative 1 (2 for 10-2.6/10-2.7) |
| C7 | R-ST-02 vs R-ST-17 | Three screen definitions (0.5 m/s, 0.3 s, 1.0 m vs strict 0.3 m/s, 0.5 s, 1.2 m vs loose 0.6 m/s, 0.3 s) | doc text | R-ST-17 rules only; R-ST-02 cites them |
| C8 | R-TR-01 vs R-TR-08 | Transition clock ends at "first shot or all 10 in the half-court" vs "defense set" rule | doc text; docs/research/transition_full.md sec. 1.4 keeps both defense-set definitions as named variants | One transition clock defined by R-TR-08 |
| C9 | R-TR-05 vs R-TR-09 | Transition class from the clock (7 s / 14 s) vs from the state | doc text; transition_full.md keeps clock windows as separate flags | R-TR-09 is the class; the clock version becomes one flag of R-TR-18 |
| C10 | R-PL-01, R-PL-02 vs R-PL-11, R-PL-12 | Speed bands 2.0/4.0/5.5 vs 2.0/4.0/5.0/5.83 m/s; acceleration 2.5 vs ±2.0/±3.0 m/s² | docs/research/load_thresholds.md sec. 1.2-1.4, 1.8 | R-PL-11/12 primary; R-PL-01/02 kept as views (R-PL-11 already says so) |
| C11 | R-DT-08 vs R-PL-12; R-DT-08 vs R-IV-13 | DT-08 outputs jerk, PL-12 says jerk is not measurable from video; DT-08 flags > 10 m/s², IV-13 allows 12 m/s² | load_thresholds.md sec. 1.6 (broadcast acceleration RMSE up to 4.17 m/s²) | Jerk and acceleration released only after the PL-12 gate; one physical limit in config |
| C12 | R-PL-05 vs R-PL-14 | Coverage flag at 60% vs exclusion at 70% | doc text | One coverage key in config with two named uses, or one value |
| C13 | R-DS-10 vs R-DS-02 | "Kaggle Massey" is model input allowed; Massey terms forbid AI/ML training without consent | docs/research/data_sources_catalog.md row 15 | Aldemir decides; until then treat Kaggle Massey Ordinals as reference only |
| C14 | R-DQ-06, R-SY-05, R-SY-08 | Chance end types: "rebounds + turnovers close every chance" vs "shot, foul drawn, reset, turnover" vs 6 reset causes; rules list 33 causes | game_ontology_coverage.md gap 4 (new-SY-2); config/invariants.yaml reset table | One chance end-type list and the full reset-cause list in config |
| C15 | R-EV-16 vs new-IV-14 | Exception "last 2 min and overtime: no challenge" vs out-of-bounds challenges at any time | config/invariants.yaml new-IV-14 (Rule 11, 2-9.19) | Follow new-IV-14 |
| C16 | R-EV-10 | Turnover types lack backcourt over-and-back (9-12) and elbows (9-13) | game_ontology_coverage.md gap 10 (new-EV-3) | Add both types |
| C17 | R-MD-13 vs R-CO-04 | Clutch = ≤ 5 min and margin ≤ 5 vs pressure = last 4 min and margin ≤ 5 | doc text | One clutch definition in config |
| C18 | R-SR-11 vs R-MD-16 | Foul-trouble cut-offs hard-coded (2 in first half, 4 in second) vs a label without cut-offs | doc text; R-EN-06 (no hard-coded thresholds) | One config table of cut-offs |
| C19 | R-SR-05 vs R-GU-01 vs R-TR-09 | Three phase vocabularies (half court/transition/... vs transition/early/half-court/dead vs primary/early/half-court) | doc text | One phase vocabulary in config/vocabulary_map.yaml |
| C20 | R-MK-12..R-MK-33 Runner ID column | Runner IDs reuse live IDs with other meanings (R-DQ-01, R-DQ-05, R-RG-07, R-RG-08, R-MK-01..09) | doc text | Prefix runner IDs (runner-DQ-01) |
| C21 | R-MK-22 | Tier cell "Shall / Should" | doc "Requirement format": one tier per row | Split into R-MK-22a (Shall) and R-MK-22b (Should) |
| C22 | R-IV-01, R-IV-03, R-IV-04, R-IV-08, R-IV-11 | Rule references wrong or imprecise | config/invariants.yaml corrections | Adopt the corrected references |
| C23 | Whole set | No rules edition per game: 35 s era (to 2014-15) and the 2025-26/2026-27 changes are hard-coded in requirement text | game_ontology_coverage.md gap 2 (new-RL-1) | Rules constants keyed by season in config; requirement text cites the key |

### 3.3 Orphans (traceable)

Every ID maps to at least one ontology leaf, so none is orphaned at the ontology level. At table level:

- **27 IDs are cited by no table in `schema/tables/`.** Expected (process or file-traced, 13): R-CD-01..05, R-RG-02, R-RR-09, R-HY-03, R-PT-01, R-CG-01 (config file), R-VZ-02, R-VZ-03 (UI twins of data rules), R-MK-32 (analysis). Real storage gaps (14): R-PC-05 (athletic block), R-PC-16 (international background), R-ID-15 (synthetic-image ablation), R-GT-05 (public-set sanity check), R-VI-16 (decode speed), R-CX-01 (feature registry), R-CX-02 (priors per feature class), R-CX-03 (feature test results), R-MK-33 (alerts), R-VZ-01, R-VZ-04..07 (views; need a view-to-table map). Proposal: `run_records` columns for R-ID-15, R-GT-05, R-VI-16; a `feature_registry` table for R-CX-01..03; player-card columns for R-PC-05 and R-PC-16.
- **A further 97 IDs are cited only at column level** (in a column's notes, not in the table's `requirements:` list); 394 are declared. Proposal: the schema generator adds column-level IDs to `requirements:` so one lookup answers "which table carries this ID".
- R-SR-07 names tables `positions` and `stints`, which do not exist (the schema has `player_positions` and `lineup_stints`).

### 3.4 Families missing acceptance tests

Families where many rows cannot fail as written (share verifiable in brackets): R-PC player cards (50%), R-AU audio (50%), R-CH chemistry (62%), R-CO cognition (62%), R-MB made baskets (71%), R-PL physical load (71%), R-SB scoreboard errors (75%), R-PE engine (77%), R-TR transition (79%). The common pattern is "Recomputes", "Interval reported" or "Report per game": these check determinism or presence, not correctness. Each such row gets a correctness test against gold, hand timing or the box score in section 4, with the share marked "(initial value, to calibrate)" where no source supports a number.

A second pattern is a tolerance without a share ("within ±80 ms of hand timing", "within ±0.3 s of gold"): R-CO-01, R-CO-02, R-CH-04, R-DF-08, R-TR-08, R-TR-20, R-ST-23, R-MB-04, R-PL-07. These are "needs_value" in `acceptance_tests.yaml`.

R-OS is the only family with no issue. R-MK-32 and R-MK-33 say "pending" in the Test cell.

### 3.5 Other set-level notes

- **Status text inside requirements** (R-FD-03, R-CG-01, R-VA-02, R-MK-10): "today ... so this fails", "rewording approved 18 Oct", "P0m approved". These go stale; the pass/fail state belongs in run records (R-RR-02) and the history in the decision log.
- **Feet in requirement text** (R-DT-19, R-SR-08: "28 ft"): keep the metric value as the requirement and the feet only as a source string, per the doc's units rule.
- **Tier sanity:** Shall 437, Should 80, mixed 1. Two Should rows act as gates and should be Shall (R-SB-04 keeps games out of training; R-IV-14 is a rules invariant held back only because frontcourt status is not stored). No Shall row was found that should be Should.
- **Proposal numbers:** 128 rows in the live doc carry "(proposal)" numbers. This review adds no unsupported number without "(initial value, to calibrate)"; the supported ones cite docs/research/load_thresholds.md (speed and acceleration bands, broadcast error) and config/invariants.yaml (rules constants).


## 4. Per-family findings and proposed rewrites

Only rows with an issue are listed. "Same text" means the product text stays as in the live doc and only the test or a cited detail changes. Every row (including rows with no issue) has an entry in `acceptance_tests.yaml`.

### R-RR: Run records and failure analysis (9 IDs, 3 with issues)

No change needed: R-RR-01, R-RR-04, R-RR-05, R-RR-06, R-RR-07, R-RR-08.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-RR-02 | Shall | AMB | Shall: For every requirement tested in a run, the run record holds one result row with: requirement ID, metric, target, pass/fail/not-testable, sample size (count), and a 95% interval from a bootstrap resampled by game (1,000 resamples, initial value, to calibrate). | 100% of tested IDs have all six fields; an ID with no gold sample is "not testable", never "pass". | Test says "all six fields" but the product lists five; resample count unstated. |
| R-RR-03 | Shall | NS | R-RR-03a Shall: every Shall fail and Should miss has a failure_analysis.md with error rate per slice (the 9 named slices) and a confusion matrix. R-RR-03b Shall: the same file lists the 20 worst cases (frame index, clip link), one cause from the fixed list {data, label, model, threshold, upstream gate, compute} and a proposed next fix with expected gain in metric points. | 100% of failed IDs have both parts; a linter checks the cause value is in the fixed list. | Two separable deliverables (diagnostics vs triage); the cause list can be checked by machine. |
| R-RR-09 | Should | TR | No text change; process output in coord/BOARD.md. | 0 weeks with runs lacking a digest. | No table; file-traced. |

### R-DQ: Data proof and quality (10 IDs, 4 with issues)

No change needed: R-DQ-03, R-DQ-04, R-DQ-05, R-DQ-07, R-DQ-09, R-DQ-10.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-DQ-01 | Shall | AMB | Shall: Every external field available from two or more sources (at least: final score ESPN vs NCAA; lines CBBD vs ESPN vs SBRO; roster numbers ESPN vs school site; officials ESPN vs conference release) is cross-checked per game; the disagreement rate per field per season is reported, and each disagreement is resolved (value chosen, reason logged) or flagged. | 100% of two-source fields reported; 0 disagreements left neither resolved nor flagged; tolerance: exact match for scores, rosters, officials; line tolerance 0.5 points (initial value, to calibrate). | "Disagreement" undefined for numeric fields such as lines; a tolerance is needed. |
| R-DQ-02 | Shall | AMB | Shall: Each table has a contract file (types, units, allowed ranges, unique keys, foreign keys to registry IDs), including at least: player and ball x, y inside the court plus 1 m margin; player speed <= 10 m/s; shot clock 0-30 s; game clock 0-1200 s in a half and 0-300 s in an extra period; every file is validated on write and each failure logged with the broken rule. | 100% of writes validated; seeded out-of-range rows (one per rule) are all rejected. | Game clock range 0-1200 s is right for halves but extra periods are 0-300 s (Rule 5-6.1, 5-9.3 per config/invariants.yaml constants); add a seeded negative test. |
| R-DQ-06 | Shall | CORR, NS | R-DQ-06a Shall: per game, sum of possession points = final score per team, and FGA = FGM + missed FG per team and player. R-DQ-06b Shall: per game, team minutes = 200 + 25 per extra period. R-DQ-06c Shall: every chance ends in exactly one terminal event from {made FG, made last FT, defensive rebound, turnover, offensive rebound (opens a new chance), foul or kicked-ball reset, period end}. | 100% of games pass each identity or carry a logged reason. | "Rebounds + turnovers close every chance" is wrong: chances also end on made baskets, shot-clock resets after fouls and period ends (see the chance definition in the doc and R-SY-09/R-MD-06). |
| R-DQ-08 | Shall | AMB | Shall: For each key field (list in config, R-EN-06), the per-game distribution is compared with the running baseline of earlier games by the population stability index using 10 quantile bins (initial value, to calibrate); PSI > 0.25 (proposal) raises a drift flag. | Seeded shifted game raises the flag; unchanged replay of a baseline game does not. | "Key field" and binning undefined; PSI depends on bins. |

### R-DS: Data sources (15 IDs, 6 with issues)

No change needed: R-DS-01, R-DS-05, R-DS-06, R-DS-07, R-DS-08, R-DS-09, R-DS-11, R-DS-12, R-DS-15.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-DS-02 | Shall | DUP | No text change; add "see R-DS-10 for the use class tag" so the two are read as one rule. | 0 model inputs trace to a reference-only or blocked source. | Same rule as R-DS-10 (use classes) and R-DS-14; keep R-DS-10 as the rule and R-DS-02 as its list of restricted sources, or mark one superseded. |
| R-DS-03 | Shall | NS, NV | Shall: Free sources are ingested before any paid source, in the listed order (hoopR releases, Torvik, CBBD, hoopR NCAA engine, NET, BPI snapshots, line history, prediction markets, Haslametrics, Prediction Tracker, recruiting and transfers via CBBD, Combine); the first pull of each passes R-DQ-02. | Source register first-pull dates are in the listed order; 100% of first pulls pass R-DQ-02; 0 paid pulls before the last free one. | The order is a requirement but nothing checks it. |
| R-DS-04 | Shall | DUP, AMB | Shall: Backtests use point-in-time ratings only (Torvik Time Machine or daily archive, KenPom archive), with snapshot date strictly before the game date; end-of-season ratings are never used. | 0 backtest rows with rating snapshot date >= game date. | Overlaps R-FD-06; "leakage test passes" undefined. |
| R-DS-10 | Shall | CONF | Shall: Each source is tagged with one use class: model input allowed, reference only, or blocked until permission, as listed in docs/research/data_sources_catalog.md; Kaggle Massey Ordinals are model input only if the catalog licence check allows it (Massey site terms forbid AI/ML training without consent). | 0 model features trace to a source not tagged "model input allowed". | Lists "Kaggle Massey" as model input allowed while R-DS-02 restricts Massey and docs/research/data_sources_catalog.md row 15 says Massey terms forbid AI/ML training without consent; needs a decision. |
| R-DS-13 | Shall | NS | R-DS-13a Shall: The CBBD key is stored only in the Mac keychain or a private .env outside the repo. R-DS-13b Shall: every CBBD call is logged and cached; monthly calls stay <= 1,000 (free-tier quota shared with College Football Data); identical calls are served from cache. R-DS-13c Should: bulk endpoints (by date or season) are used instead of per-game calls. | a: 0 key matches in repo history; b: monthly calls <= 1,000 and 0 repeated identical calls; c: share of calls that are per-game <= 10% (initial value, to calibrate). | Three requirements of different kinds (secret, quota, efficiency) in one row; the "preferred" clause is Should-level. |
| R-DS-14 | Shall | DUP | No text change; add "case of R-DS-02". | 0 project files trace to the scraper. | Special case of R-DS-02/R-DS-10; keep but cross-reference. |

### R-RG: Rights, licences and ethics (11 IDs, 1 with issues)

No change needed: R-RG-11, R-RG-01, R-RG-03, R-RG-04, R-RG-05, R-RG-06, R-RG-07, R-RG-08, R-RG-09, R-RG-10.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-RG-02 | Shall | TR | No text change. | Signed checklist on file before P8. | No table; file-traced. |

### R-FD: Foundation data (12 IDs, 5 with issues)

No change needed: R-FD-02, R-FD-04, R-FD-05, R-FD-07, R-FD-09, R-FD-10, R-FD-12.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-FD-01 | Shall | AMB | Shall: One games-registry row per game, written before any video of it is processed, with every field of schema/tables/games.yaml. | 100% of games with footage have a row; 0 nulls in game_id, date, site, opponent, both jersey colours, footage path, fps, resolution; row timestamp < first processing timestamp. | "Every field listed above" points at prose; name the schema file and test the "before processing" order. |
| R-FD-03 | Shall | STALE | Same text without the status note "(today registry/rosters.csv has 29 rows, so this fails)"; move that note to the run record. | 0 PBP players without a roster row; 0 number mismatches against the broadcast on 3 games. | A status statement in a requirement goes stale; status belongs in run records (R-RR-02). |
| R-FD-06 | Shall | AMB, DUP | Shall: For each game, opponent and team ratings (KenPom or Torvik) are taken from the latest snapshot dated on or before the day before tip (local date); a missing snapshot falls back to the nearest earlier one, flagged with its date. | 0 rating rows dated on or after the tip date; every fallback row flagged with its snapshot date. | Product says "day before tip" but the test checks only "before tip"; overlaps R-DS-04. |
| R-FD-08 | Shall | CONF | Shall: Officials per game: the two or three on-court officials (Rule 2-1.1.a) with role where the source gives it; a missing name is "unknown", never guessed. | 100% of past games have 2 or 3 names (3 expected in D-I) or a flagged unknown. | "3 names" conflicts with the R-IV-02 correction in config/invariants.yaml (two or three officials are legal). |
| R-FD-11 | Should | DUP | Should: Arena registry (one row per venue): venue ID, capacity, altitude (m), coordinates, floor template ID, main-camera side; R-VI-13 (camera registry) and R-CX-04 (venue context) read from it instead of restating fields. | Every game links to an arena row; 0 venue fields stored twice. | Capacity and altitude also in R-CX-04; main-camera side also in R-VI-13. |

### R-PC: Player cards (16 IDs, 9 with issues)

No change needed: R-PC-01, R-PC-02, R-PC-04, R-PC-10, R-PC-13, R-PC-14, R-PC-15.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-PC-03 | Shall | NV | Shall: Great-circle distance (km) from hometown coordinates to campus and to each venue, per player. | Recomputed haversine distance equals the stored one within 1 km (initial value, to calibrate) on 100% of rows. | "Recomputed from coordinates" has no tolerance or method. |
| R-PC-05 | Shall | NV, TR | Shall: Athletic block per player from our tracking: top speed (m/s), peak acceleration and deceleration (m/s²), lateral slide speed on defense (m/s), change-of-direction time (s), jump height (m, after R-CG-11); each with n (efforts) and a 95% interval; marked "provisional" under 3 games. | 100% of values carry n and interval; top speed within ± measured tracking speed error of a reference (radar or hand-timed sprint) on >= 20 efforts; the tolerance comes from the R-PL calibration (docs/research/load_thresholds.md section 10). | Only reporting is tested, not accuracy; docs/research/load_thresholds.md shows broadcast speed RMSE 0.34-2.38 m/s, so accuracy must be measured before use. No table declares it. |
| R-PC-06 | Shall | NS | R-PC-06a Shall: shooting block per player: make rates by sector and ring, catch-and-shoot vs off the dribble, rim, mid-range, three, free throws; each rate shrunk toward a stated prior and stored with n. R-PC-06b Should (hypothesis): free-throw % improves the three-point prior; tested under R-HY rules. | a: 100% of rates carry prior and n; b: pre-registered test with log-loss change on held-out games. | A hypothesis test ("FT% as a prior, tested") is embedded in a product requirement. |
| R-PC-07 | Shall | NV | Shall: Playmaking block per player: assist rate, potential assists, hockey assists, pass difficulty, turnover rate by type, each with n. | Recomputation from events equals the stored values (0 differences); assist and turnover rates from official PBP agree with the box score within 0.5 percentage points (initial value, to calibrate). | "Recomputes" checks determinism only, not correctness. |
| R-PC-08 | Shall | NV | Same text; matchup points allowed only for matchups with >= 30 possessions. | Recomputation equals stored values; rebound, steal, block and foul rates agree with box-score-derived rates within 0.5 pp (initial value, to calibrate). | "Recomputes" lacks a correctness check. |
| R-PC-09 | Shall | NV | Same text. | Recomputed from prior-level PBP equals stored values; source season and team recorded on 100% of values. | Test lacks a pass condition. |
| R-PC-11 | Shall | NV | Same text; every cell stores n; cells with n < 30 are descriptive only. | Recomputation equals stored values; 100% of cells carry n. | "Recomputes" has no pass condition. |
| R-PC-12 | Shall | NV | Shall: Development block: season-over-season and within-season change per stat (units per season) with a 95% interval, and career D-I minutes (min). | 100% of trend values carry an interval; career minutes equal the sum of box-score minutes (0 min difference). | "Trend with interval" is not a pass/fail test. |
| R-PC-16 | Should | NV, TR | Should: International and pro background per player (FIBA youth events, pro leagues, games played), with source and date. | For MSU players, 100% of fields filled or marked "not public" after a documented search. | "Filled where public" cannot fail; no table carries it. |

### R-MD: Global metadata (20 IDs, 5 with issues)

No change needed: R-MD-01, R-MD-03, R-MD-04, R-MD-05, R-MD-06, R-MD-08, R-MD-09, R-MD-10, R-MD-12, R-MD-14, R-MD-15, R-MD-17, R-MD-18, R-MD-19, R-MD-20.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-MD-02 | Shall | AMB | Same text, naming the six states (MSU control, opponent control, contested, in flight, inbound pending, dead) and the vocabulary file. | >= 95% frames correct and >= 90% of state changes within ±0.2 s of gold-v1 (proposal). | "The 6 states" is defined only implicitly (R-MD-05 lists them). |
| R-MD-07 | Shall | CONF, AMB | Shall: Team fouls per half and bonus state (bonus at the 7th team foul, double bonus at the 10th; counts reset only at the start of the second half; extra periods continue the second-half count, Rule 5-9.4), and timeouts left per team. | Equal to PBP-derived values at 100% of fouls and timeouts. | "Overtime counts follow the rulebook entry in config" is resolved by the R-SR-03/R-MD-07 correction in config/invariants.yaml: no reset for extra periods. |
| R-MD-11 | Should | DUP, NV | Mark as a pointer: "Superseded by R-VI-03 (shot type) and R-VI-05 (coverage); kept for the metadata list." | Covered by R-VI-03 and R-VI-05 tests. | Same product as R-VI-03/R-VI-05; "See R-VI rows" is not a test. |
| R-MD-13 | Shall | NS, CONF | R-MD-13a Shall: 5-min window ID, last-4-min flag and clutch flag (<= 300 s left in the second half or an extra period, margin <= 5 points) per record. R-MD-13b Shall: media-timeout segment ID following Rule 5-14.10 (16/12/8/4-minute marks or the 15/10/5 alternative; a dead ball within 30 s before a mark counts; first team timeout of the second half takes the media length). | a: recomputation from clock equals stored values; b: segment boundaries match PBP media timeouts in >= 95% of segments (initial value, to calibrate). | Four stamps in one row; media rules are incomplete per the R-SR-04 correction in config/invariants.yaml; "≤ 5 min left" should name halves and extra periods. |
| R-MD-16 | Shall | AMB | Shall: Per player per record: personal fouls so far and a foul-trouble label from a config table of (fouls, period, seconds left) cut-offs (initial values, to calibrate). | Counts equal PBP at 100% of fouls; labels recompute from the config table. | "Label" has no definition; cut-offs must be in config to be testable. |

### R-ID: Player identity (15 IDs, 2 with issues)

No change needed: R-ID-01, R-ID-02, R-ID-03, R-ID-04, R-ID-05, R-ID-06, R-ID-07, R-ID-08, R-ID-10, R-ID-11, R-ID-12, R-ID-13, R-ID-14.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-ID-09 | Shall | DUP | No text change; note: R-ID-03 enforces the constraint per frame, R-ID-09 measures the outcome per possession. | >= 99% of possessions (proposal). | Overlaps R-ID-03; keep both but state the split. |
| R-ID-15 | Should | TR, AMB | Should: Synthetic kit and lighting images (named generator, version logged) are tested for team-assignment only, after the P1 baseline passes, never for identity. | Kept only if team-assignment accuracy on real gold frames rises by >= 0.5 points (initial value, to calibrate, matching R-ID-13). | "Robustness" is vague and "rises" has no minimum; no table records the ablation (use run_records). |

### R-VI: Video ingest (16 IDs, 4 with issues)

No change needed: R-VI-02, R-VI-03, R-VI-04, R-VI-05, R-VI-07, R-VI-08, R-VI-09, R-VI-10, R-VI-11, R-VI-12, R-VI-14, R-VI-15.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-VI-01 | Shall | NS | R-VI-01a Shall: capture at native >= 1080p without rescaling (lower: "tier 2" in the registry). R-VI-01b Shall: constant frame rate, 60 fps preferred, 30 fps accepted. R-VI-01c Shall: original audio track kept. | a: probe height >= 1080 px or tier-2 tag; b: frame-interval spread < 1 ms; c: audio stream present and same duration within 0.1 s. | Three checks with different tests in one row; audio is untested. |
| R-VI-06 | Shall | NV | Shall: Usable-possession flag = coverage score (R-VI-05) >= a threshold in config (initial value 0.6, to calibrate on 3 games), and the share of usable possessions per game. | Report on 100% of games; on gold-v1, possessions flagged usable have tracking recall >= the R-DT target (to calibrate). | No threshold is named so the flag cannot be checked. |
| R-VI-13 | Shall | DUP | Same text; main-camera side read from R-FD-11. | Calibration error per arena meets R-CG-03. | Main-camera side duplicated in R-FD-11. |
| R-VI-16 | Shall | NV, TR | Shall: Video decoded on the GPU hardware decoder (AV1, VP9 or H.264) at >= 4x real time for 1080p60 (initial value, to calibrate); CPU decode only for unsupported codecs, logged. | Decode fps logged per run; >= 4x real time on the target GPU; 0 unlogged CPU fallbacks. | "Decode speed logged" cannot fail; no table records it (run_records). |

### R-CG: Court geometry (11 IDs, 3 with issues)

No change needed: R-CG-02, R-CG-03, R-CG-05, R-CG-06, R-CG-08, R-CG-09, R-CG-10, R-CG-11.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-CG-01 | Shall | STALE, TR | Same text without "(today the file says verified: false, so this fails)". | 100% of constants cite a 2026-27 rule; file marked verified by Aldemir. | Status note will go stale; belongs in run records. The constants live in config/court_ncaa_men.yaml (a config file, not a table), which also lacks line widths, centre circle, lane spaces, backboard and ring (new-CG-1). |
| R-CG-04 | Shall | NV | Same text. | Foot-point ground error on gold-v1: median <= 0.30 m and p90 <= 0.60 m (initial values from R-CG-03, to calibrate); airborne frames flagged 100%. | Test says error is measured but sets no pass value. |
| R-CG-07 | Shall | NS | No text change; list each relative-geometry quantity with its unit in config so each has its own unit test. | Each of the 6 quantities within 0.01 m / 0.1° / 0.01 m² of hand calculation. | Six quantities bundled; acceptable as one test file but each needs a case. |

### R-DT: Detection and tracking (19 IDs, 5 with issues)

No change needed: R-DT-01, R-DT-02, R-DT-03, R-DT-04, R-DT-05, R-DT-06, R-DT-07, R-DT-09, R-DT-10, R-DT-11, R-DT-13, R-DT-16, R-DT-17, R-DT-18.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-DT-08 | Shall | FEAS, NS | R-DT-08a Shall: velocity (m/s) and heading (degrees) per player per frame from smoothed positions of a named body point (pelvis_floor or ankle_mid), filter named in config. R-DT-08b Should: acceleration (m/s²) and jerk (m/s³), released only after the stationary noise-floor and in-motion checks of docs/research/load_thresholds.md section 10 pass. | a: speed RMSE <= 0.3 m/s (proposal) on >= 20 hand-timed sprints and synthetic tracks, reported with the measured value; b: stationary players show acceleration noise below the lowest reported band (2.0 m/s², load_thresholds.md) in >= 95% of seconds. | docs/research/load_thresholds.md sec. 1.6 reports best single-feed broadcast speed RMSE 0.34 m/s and acceleration RMSE up to 4.17 m/s², so 0.3 m/s may be infeasible and acceleration/jerk need their own gate; tracked point unnamed. |
| R-DT-12 | Shall | CONF | Shall: Officials tracked per frame with role: lead, trail and centre in three-person crews; lead and trail in two-person crews (Rule 2-1.1.a). | Role correct in >= 95% of seconds (proposal), reported by crew size. | Assumes three officials; R-IV-02 correction (config/invariants.yaml) allows two. |
| R-DT-14 | Shall | NS, NV | R-DT-14a Shall: throw-in event while the ball is out of bounds: side, half, team, after-timeout flag, first-pass target. R-DT-14b Shall: 5-second throw-in count (Rule 7-6.6) from the official's hand-off to release. R-DT-14c Shall: formation label (stack, box, line, diamond, other). | a: >= 95% of throw-ins found, attributes >= 95% correct; b: count within ±0.5 s of gold in >= 90% (initial value, to calibrate); c: formation correct >= 85% (proposal). | Seven attributes with only two tested; the 5-second count has no test. |
| R-DT-15 | Shall | AMB | Shall: Jump balls and held balls as events with formation: the two jumpers (IDs) and the positions of the other eight players at the toss (m). | 100% matched to PBP; jumper IDs correct in >= 95% (initial value, to calibrate). | "As fixed formations" does not say what is stored. |
| R-DT-19 | Shall | UNIT | Same text with "the 8.53 m mark (28 ft in the rules)" so the stored unit is metric. | >= 95% (proposal). | Units rule: metric in the requirement, feet only as the source string. |

### R-BL: Ball (8 IDs, 1 with issues)

No change needed: R-BL-01, R-BL-02, R-BL-03, R-BL-04, R-BL-06, R-BL-07, R-BL-08.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-BL-05 | Shall | AMB | Shall: Make or miss per shot from rim, net and ball. | Agreement with PBP after sync >= 99.5% (initial value, to calibrate); 100% of disagreements flagged for review (R-MB double verification). | "100% agreement; disagreements flagged" is self-contradictory. |

### R-GT: Vision gates (5 IDs, 1 with issues)

No change needed: R-GT-01, R-GT-02, R-GT-03, R-GT-04.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-GT-05 | Should | TR | No text change; results stored in run_records with dataset name and licence. | Report lists our score and the published baseline for each set. | No table carries it. |

### R-SY: Sync and possessions (10 IDs, 4 with issues)

No change needed: R-SY-02, R-SY-03, R-SY-06, R-SY-07, R-SY-09, R-SY-10.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-SY-01 | Shall | NS | No text change; report accuracy per field (game clock, shot clock, score, period, team fouls, timeouts, arrow). | Game clock exact >= 99%; score = PBP at 100% of scoring events; shot clock exact >= 98% and other fields >= 99% (initial values, to calibrate). | Seven fields read but only two tested. |
| R-SY-04 | Shall | AMB | Shall: Possession table: start, end, outcome, points, length (s), and two separate labels: tempo class (half-court, early, transition; from R-TR-09) and start type (after make, after defensive rebound, after turnover, after free throws, ATO, SLOB, BLOB). | Possession points = final score in 100% of games; each label >= 90% correct (proposal). | The "type" list mixes tempo and start-type categories that are not mutually exclusive (a transition possession is also "after a defensive rebound"). |
| R-SY-05 | Shall | CONF, NV | Shall: Chance table: chance number, start shot clock (s), time used (s), end type from {made shot, missed shot with defensive rebound, missed shot with offensive rebound, foul or kicked-ball reset, turnover, held ball, period end}. | Offensive rebounds per game = PBP; every chance has exactly one end type; chance end types reconcile with R-DQ-06c. | End-type list (shot, foul drawn, reset, turnover) is incomplete versus R-DQ-06 and R-SY-08 causes; test covers only offensive rebounds. |
| R-SY-08 | Shall | CONF | Shall: Shot-clock reset and no-reset events read from the scoreboard: time, value before, value after (s), cause from the full rules list in config/invariants.yaml (33 causes, Rule 2-11), including no-reset stoppages. | >= 98% of resets found; >= 95% causes correct (proposal); every stoppage has a reset or no-reset row. | Six coarse causes against 33 rule causes; no-reset stoppages not recorded (docs/data/game_ontology_coverage.md gap 4, new-SY-2). |

### R-TR: Transition (28 IDs, 12 with issues)

No change needed: R-TR-02, R-TR-03, R-TR-04, R-TR-06, R-TR-07, R-TR-09, R-TR-15, R-TR-18, R-TR-19, R-TR-21, R-TR-22, R-TR-23, R-TR-24, R-TR-26, R-TR-27, R-TR-28.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-TR-01 | Shall | CONF | Shall: Transition clock per frame: seconds since the transition start of R-TR-08; it ends at the end of R-TR-08. | Start within ±0.2 s of gold in >= 95% of changes (proposal). | Defines its own end (first shot or all 10 in the half-court) which differs from the "defense set" end in R-TR-08; two definitions of one clock. |
| R-TR-05 | Shall | CONF, DUP | Superseded by R-TR-09 (state definition) and R-TR-18 (clock flags, including 7 s and 14 s research windows); keep as the clock-based flag "clock_class_7_14" inside R-TR-18. | As R-TR-09 and R-TR-18. | A clock-based class conflicts with the state-based class of R-TR-09; both called "transition class". |
| R-TR-08 | Shall | NV | Same text. | Start and end within ±0.5 s of Aldemir's labels in >= 90% of 200 possessions (share initial value, to calibrate). | Tolerance given but not the share of possessions that must meet it. |
| R-TR-10 | Shall | NV | Same text. | Equal to recomputation from R-TR-08 (0 differences); last-back defender correct in >= 90% of possessions vs gold (initial value, to calibrate). | "Recomputes" tests determinism, not correctness. |
| R-TR-11 | Shall | DUP | Superseded by R-TR-18 (same rule, fuller list of definitions). | As R-TR-18. | R-TR-18 restates R-TR-11 with more definitions. |
| R-TR-12 | Shall | NS | R-TR-12a Shall: time to get back per defender (s) and who stops the ball (ID). R-TR-12b Shall: rim protector, matchups found, cross-matches and recoveries (IDs, labels). | Each element >= 90% agreement with Aldemir's labels (proposal); times within ±0.5 s. | Six outputs with one agreement number; times need a tolerance. |
| R-TR-13 | Shall | DUP, NV | Merge into R-TR-20 (same phase timestamps, fuller list); keep trailer arrival and drag screen as R-TR-20 phases. | As R-TR-20. | Overlaps R-TR-20; the ±0.3 s tolerance has no share. |
| R-TR-14 | Shall | DUP, NV | Merge into R-TR-23 (pushes after makes and free throws, reported separately). | Inbound, first-pass and crossing times within ±0.3 s of gold in >= 90% (initial value, to calibrate). | R-TR-23 covers the same product; "Recomputes" has no pass value. |
| R-TR-16 | Shall | NV | Same text. | Opportunity flag agrees with Aldemir's labels in >= 90% of 200 possessions (initial value, to calibrate). | "Recomputes" only checks determinism. |
| R-TR-17 | Shall | AMB | Shall: Per game, transition share (%) and points per possession from PBP clock definitions compared with our state definition; a gap > 10 percentage points in share (initial value, to calibrate) goes to review. | 100% of games have the comparison; 100% of gaps above the threshold have a review entry. | "Large gaps" undefined. |
| R-TR-20 | Shall | NV | Same text. | Each phase time within ±0.3 s of gold in >= 90% of breaks (share initial value, to calibrate). | Tolerance without a share. |
| R-TR-25 | Shall | AMB | Same text. | 100% of foul-stopped breaks link to a PBP foul; clear-path flag agrees with gold in >= 90% (initial value, to calibrate). | "Matched" gives no share; the clear-path judgement is untested. |

### R-EV: Events (16 IDs, 3 with issues)

No change needed: R-EV-01, R-EV-02, R-EV-03, R-EV-04, R-EV-05, R-EV-06, R-EV-07, R-EV-08, R-EV-09, R-EV-11, R-EV-12, R-EV-13, R-EV-14.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-EV-10 | Shall | CONF | Shall: Turnover type per turnover from a list that maps 1:1 to the 2026-27 rules violations and PBP codes, adding backcourt over-and-back (Rule 9-12) and elbows (9-13) to the 11 listed. | Count = PBP; type = PBP where coded; 0 PBP turnover codes without a mapping. | The 11 types lack the 9-12 backcourt and 9-13 elbows violations (docs/data/game_ontology_coverage.md gap 10, new-EV-3), so counts by type cannot reconcile. |
| R-EV-15 | Shall | NS | R-EV-15a Shall: timeout record: caller, type, game and shot clock (s), ball state, score run in the prior 120 s, lineup changes. R-EV-15b Shall: post-timeout outcome: set called, points on next possession, defensive scheme change. | a: 100% of PBP timeouts recorded, fields equal PBP where coded; b: set and scheme labels agree with gold >= 85% (initial value, to calibrate). | Mixes PBP facts with video judgements that need their own accuracy test. |
| R-EV-16 | Shall | CONF | Shall: Coach's challenge record (Rule 11, 2-9.19): coach, play type (out of bounds at any time; goaltending or basket interference and restricted-area calls before the last 2 min of regulation), clock, outcome, timeout kept or charged, second challenge earned. | Equal to PBP or broadcast where shown, 100%; every record passes new-IV-14. | The exception "last 2 min and overtime: officials review without a challenge" disagrees with new-IV-14 in config/invariants.yaml (out-of-bounds challenges allowed any time). |

### R-AU: Audio (4 IDs, 2 with issues)

No change needed: R-AU-02, R-AU-03.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-AU-04 | Should | NV | Same text. | On 100 labelled dead-ball stretches, flag precision and recall >= 90% (initial value, to calibrate). | "Flag present" cannot fail. |
| R-AU-01 | Should | NV | Same text. | WER <= 20% on a 10-min sample per source (initial value, to calibrate). | "Measured, reported" cannot fail. |

### R-RF: Referees and whistles (7 IDs, 2 with issues)

No change needed: R-RF-01, R-RF-02, R-RF-04, R-RF-05, R-RF-06.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-RF-03 | Shall | CONF | Shall: Foul record with type from the 2026-27 rules classes (personal common, shooting, player-control, team-control, double, Flagrant 1, Flagrant 2, Class A technical, Class B technical, administrative technical); deliberate fouls stored as common or Flagrant 1 with a "deliberate" flag (Rule 4-15.2.c.1.d). | Type and players equal PBP where coded; 0 types outside the rules classes. | The 9 types include "intentional", which the 2026-27 rules book does not have (docs/data/game_ontology_coverage.md gap 3, new-RF-3). |
| R-RF-07 | Shall | NS, DUP | Shall: Video reviews (type, trigger, duration s, outcome) logged per game; held balls and arrow uses are covered by R-MD-12 and R-EV-14. | Review log equals PBP/broadcast list for 100% of games. | Three products; held balls and arrow are already R-MD-12/R-EV-14; reviews overlap R-SR-04 and R-EV-16. |

### R-ST: Actions and sets (26 IDs, 5 with issues)

No change needed: R-ST-01, R-ST-03, R-ST-04, R-ST-05, R-ST-06, R-ST-07, R-ST-09, R-ST-10, R-ST-11, R-ST-13, R-ST-14, R-ST-15, R-ST-16, R-ST-17, R-ST-18, R-ST-20, R-ST-21, R-ST-22, R-ST-24, R-ST-25, R-ST-26.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-ST-02 | Shall | CONF | Shall: Actions built from primitives in relation; on-ball screens use the strict and loose rules of R-ST-17 (one definition, not a third). | Screens (strict rule): precision >= 90%, recall >= 85% on gold (proposal). | Three screen definitions: R-ST-02 (<0.5 m/s, >=0.3 s, 1.0 m), R-ST-17 strict (<=0.3 m/s, >=0.5 s, 1.2 m) and loose (<0.6 m/s, >=0.3 s). |
| R-ST-08 | Shall | NV | Same text. | Recomputation from tracks equals stored values; screen-to-cut delay and catch-to-action time within ±80 ms of hand timing on 100 phases (tolerance from R-CO-01/R-CH-04). | "Recompute" checks determinism only. |
| R-ST-12 | Shall | AMB | Shall: Templates are defined by role, never by player name, so lineups of later seasons still match. | Match rate on the new season within 10 points of the previous season (proposal); 0 templates reference a player ID. | Names (Kohler, Cooper) tie the requirement to one roster year. |
| R-ST-19 | Shall | NV | Same text. | Accepted matches agree with gold alignment labels in >= 85% of possessions (initial value, to calibrate); acceptance rule mean error < 1.8 m and margin > 0.4 m (proposal). | The "test" is the matcher's acceptance rule, not an accuracy check. |
| R-ST-23 | Shall | NV | Same text. | Each special-situation event within ±0.2 s of gold in >= 90% (share initial value, to calibrate). | Tolerance without a share. |

### R-DF: Defensive structure (21 IDs, 6 with issues)

No change needed: R-DF-01, R-DF-02, R-DF-04, R-DF-05, R-DF-09, R-DF-11, R-DF-12, R-DF-13, R-DF-14, R-DF-15, R-DF-16, R-DF-17, R-DF-18, R-DF-19, R-DF-21.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-DF-03 | Shall | NV | Same text. | Recomputes from tracks; rim protector ID agrees with gold in >= 90% of seconds (initial value, to calibrate). | "Recomputes" only. |
| R-DF-06 | Shall | DUP | No text change; note that R-DF-16 sets the two-level form (4 coarse, then fine) and the drop-depth bands for the same label. | >= 80% (proposal). | R-DF-16 refines the same product with a different test (coarse >= 90%, fine >= 80%). |
| R-DF-07 | Shall | NS | R-DF-07a Shall: off-ball screen coverage per screen. R-DF-07b Shall: post defense (front, three-quarter, behind) per post touch. | Each >= 80% correct on gold (proposal). | Two products in one row. |
| R-DF-08 | Shall | NV | Same text. | Delay within ±80 ms of hand-timed gold in >= 80% of 200 passes (share initial value, to calibrate); closeout distance within 0.3 m and speed within 0.3 m/s (initial values, to calibrate). | Tolerance without share; closeout distance and speed untested. |
| R-DF-10 | Shall | DUP | Merge with R-TR-12 and R-DF-20 (transition defense); keep R-DF-20 as the field list. | As R-DF-20 and R-TR-12. | Three rows describe defenders back, who stops the ball and cross-matches. |
| R-DF-20 | Shall | NV | Same text. | Each field present per possession; get-back times within ±0.5 s of gold in >= 90% (initial value, to calibrate). | Presence only; no accuracy. |

### R-VL: Value (13 IDs, 3 with issues)

No change needed: R-VL-01, R-VL-02, R-VL-03, R-VL-04, R-VL-06, R-VL-07, R-VL-08, R-VL-11, R-VL-12, R-VL-13.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-VL-05 | Shall | NV | Same text. | 100% of values carry a 95% interval; on 100 decisions rated by Aldemir, sign of decision quality agrees in >= 75% (initial value, to calibrate). | "Recomputes; reported with interval" does not validate the measure. |
| R-VL-09 | Shall | DUP | Merge into R-VL-02 (same bookkeeping identity); keep the named roles (scorer, assister, hockey-assist passer, screener, gravity player) as R-VL-02 fields. | As R-VL-02. | Same identity test as R-VL-02. |
| R-VL-10 | Shall | NV | Same text. | Recomputes from events; mean drawn-foul value per type calibrated within ±0.05 points per decile as R-VL-01. | "Recomputes" only. |

### R-CH: Chemistry and coaches (8 IDs, 4 with issues)

No change needed: R-CH-01, R-CH-02, R-CH-05, R-CH-08.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-CH-03 | Shall | NV | Same text. | Recomputes from tracks; cut timing after a screen within ±80 ms of hand timing on 100 cuts in >= 80% (initial value, to calibrate). | "Recomputes" only. |
| R-CH-04 | Shall | NV | Same text. | Within ±80 ms in >= 80% of 200 screens (share initial value, to calibrate). | Tolerance without share. |
| R-CH-06 | Shall | NV, DUP | Same text; timeout timing vs runs is R-CC-02 and is removed here. | Recomputes from events; first ATO set label agrees with gold >= 85% (initial value, to calibrate). | Timeout timing vs runs duplicates R-CC-02; "recomputes" only. |
| R-CH-07 | Shall | DUP | No text change; head-to-head history is R-CC-05 (and prior meetings R-CX-19); cross-reference. | Present for every opponent. | Head-to-head appears in R-CH-07, R-CC-05 and R-CX-19. |

### R-CC: Coach cards (5 IDs, 2 with issues)

No change needed: R-CC-01, R-CC-02, R-CC-04.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-CC-03 | Shall | NV | Same text. | Recomputes; "pulled within 30 s" events match PBP substitution times (0 differences). | "Recomputes" only; low risk. |
| R-CC-05 | Shall | DUP | Keep as the single head-to-head requirement; R-CH-07 and R-CX-19 point to it. | Present for every opponent. | Duplicate group with R-CH-07 and R-CX-19. |

### R-GU: Game understanding (6 IDs, 3 with issues)

No change needed: R-GU-01, R-GU-04, R-GU-06.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-GU-02 | Shall | AMB | Same text. | In each of 10 probability bins, observed frequency within ±5 points of the bin mean (initial value, to calibrate). | "About 20%" is not a threshold. |
| R-GU-03 | Shall | NV | Same text. | Score per question type per game and model version; pass mark per type set by Aldemir (needs decision), e.g. "who guards X" >= 90% to match R-DF-01. | No pass mark; a Shall cannot fail. |
| R-GU-05 | Should | AMB | Same text. | Accuracy above the nearest-teammate baseline with a game-resampled 95% interval excluding 0. | "Beats" has no margin. |

### R-SR: State record (15 IDs, 10 with issues)

No change needed: R-SR-01, R-SR-02, R-SR-13, R-SR-14, R-SR-15.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-SR-03 | Shall | CONF, NS | R-SR-03a Shall: personal fouls per player and team fouls per half (second-half count continues through extra periods, Rule 5-9.4). R-SR-03b Shall: foul type from the same list as R-RF-03. R-SR-03c Shall: bonus state (none, one-and-one from the 7th, double from the 10th) and fouls to give. Exception text: "Player-control fouls, and team-control fouls that are not loose-ball fouls, award no free throws; loose-ball team-control fouls are bonus-eligible (8-2.1, 10-1 Penalty c)." | Counts equal the box score per half; bonus state equals PBP at 100% of fouls. | config/invariants.yaml corrections to R-SR-03 (exception wording, extra periods); foul-type list differs from R-RF-03's 9 types. |
| R-SR-04 | Shall | CONF | Shall: Timeout and review state: timeouts left per team by type, caller, media-timeout slot per Rule 5-14.10 (16/12/8/4 or 15/10/5 marks; 30 s pre-mark rule; first second-half team timeout takes media length; A.R. 5-33), coach's challenge left (Rule 11, from 2025-26), monitor review in progress. | Matches PBP timeout list; media slots match PBP media timeouts in >= 95% (initial value, to calibrate). | config/invariants.yaml R-SR-04 correction adds the alternative marks and rules. |
| R-SR-05 | Shall | CONF | Same text, with phase values aligned to R-TR-09 (primary, early, half-court) plus throw-in, free throw, jump ball, timeout, review, dead. | Possession counts within ±1 between teams per half (R-IV-15); phase agrees with R-TR-09 on transition seconds. | Phase list (half court, transition) differs from the transition classes of R-TR-09 and the belief phases of R-GU-01. |
| R-SR-06 | Shall | NV, DUP | Same text; tests are those of R-MD-02 (control state), R-BL-02 (handler), R-BL-01 (position) and R-MB-07 (ring contact). | As the cited rows. | "Gold-v1 ball labels" has no threshold; fields duplicate R-MD-02/R-BL rows. |
| R-SR-07 | Shall | CONF, NV, TR | Shall: Personnel: the 10 players on court with identity confidence, x, y (m), speed (m/s), acceleration (m/s², after the R-PL-12 gate); stint length (s); positions of the two or three officials (Rule 2-1.1.a). | Identity as R-ID-01; positions as R-CG-03; tables player_positions and lineup_stints. | "3 referees" conflicts with R-IV-02 correction; tables `positions` and `stints` do not exist in schema/tables (player_positions, lineup_stints); "identity accuracy gate" is a pointer. |
| R-SR-08 | Shall | UNIT | Same text with "the 8.53 m mark (28 ft)". | Order matches PBP 100%; spot class as R-DT-19. | Metric units rule. |
| R-SR-09 | Shall | CONF, NV | Shall: Free-throw state machine as written, with award types per the 2026-27 rules: shooting 2 or 3, and-one 1, one-and-one, double bonus 2, Class A technical 2, Class B technical 1, administrative technical 1 (2 for 10-2.6 and 10-2.7), Flagrant 1 and 2: 2 plus ball. | 100% of PBP free throws matched; "free throw coming" prediction precision and recall >= 95% (initial value, to calibrate). | config/invariants.yaml R-SR-09 correction: only Class A technicals award two; prediction accuracy has no target. |
| R-SR-10 | Shall | DUP | No text change; note: shot type is the R-VI-03 classifier. | >= 99% replay recall; main-wide as R-VI-03. | Overlaps R-VI-03/R-VI-04. |
| R-SR-11 | Should | CONF | Same text; foul-trouble flags read from the R-MD-16 config table rather than fixed here. | Recomputation equals stored. | Hard-codes foul-trouble cut-offs (2 in first half, 4 in second) that R-MD-16 leaves to config; one source needed (R-EN-06). |
| R-SR-12 | Should | DUP | No text change; note that the per-second value is a 1 Hz view of R-VL-01 (10 Hz). | As R-VL-01. | Same product as R-VL-01 at a different rate. |

### R-IV: Invariants (16 IDs, 10 with issues)

No change needed: R-IV-05, R-IV-06, R-IV-07, R-IV-12, R-IV-15, R-IV-16.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-IV-01 | Shall | CORR | Same invariant; rule references 1-1.1, 3-2.1, 3-2.2, 10-2.6, 1-22.7.b.2, 1-22.7.b.5, 10-2.3.a, 3-6; exception: a team may continue with fewer than five (3-2.2). | Every break goes to identity review; 0 unreviewed breaks per game. | config/invariants.yaml correction: 3-4 is the pre-game lineup filing. |
| R-IV-02 | Shall | CORR, CONF | Shall: Officials on court: two or three (Rule 2-1.1.a); three expected in D-I games, two-official games set in the games registry. | 0 unreviewed breaks per game. | config/invariants.yaml correction: two-official crews are legal. |
| R-IV-03 | Shall | CORR | Same invariant; "5 fouls" means personal plus Class A technical fouls; also three Flagrant 1 fouls disqualify (4-12.1). Rules 3-6.1, 3-6.2, 4-12.1, 4-12.5, 2-8.3, 4-14.2.e, 10-1 Penalty. | 0 unreviewed breaks. | config/invariants.yaml correction. |
| R-IV-04 | Shall | CORR | Same invariant; add own-basket credit (2 points to the opponent, no player credit, 5-1.4.a); rules 5-1.2-5-1.4, 5-1.13, 9-15 Penalty, 2-9.13, 2-9.17. | 0 unreviewed breaks. | config/invariants.yaml refinement. |
| R-IV-08 | Shall | CORR | Same invariant with: "made last free throw for a personal foul"; "the second half starts with an arrow throw-in at the division line (6-3.6)"; rules 6-2.1, 6-3.2, 6-3.4, 6-3.6, 6-4.1, 7-3.1.c, 7-4.6.a, 8-6.1, 8-7, 4-9.3. | 0 unreviewed breaks. | config/invariants.yaml correction. |
| R-IV-09 | Shall | CORR, CONF | Shall: Team fouls never go down within a half except logged corrections; reset only at the start of the second half (extra periods continue it, 5-9.4); bonus at the 7th, double bonus at the 10th. Rules 8-2.1-8-2.3, 10-1 Penalty c, d.3, 2-9.11, 5-9.4, 5-7.6; A.R. 11-32. | 0 unreviewed breaks. | config/invariants.yaml correction: 2-9.11 is only the scorer's signal; no reset for extra periods. |
| R-IV-10 | Shall | CORR, CONF | Shall: Timeouts left never go up and never below 0, except the extra allotment per extra period (one 30 s timeout in the media format, 5-14.10.f; one 75 s otherwise, 5-14.8.d, 5-14.9.f); at most two 30 s timeouts carry into the second half (5-14.10.a.1). | 0 unreviewed breaks. | config/invariants.yaml correction: televised D-I games use the media format, with no 75 s timeouts. |
| R-IV-11 | Shall | CORR | Same invariant; rules 8-4.4, 8-4.4.a, 8-4.5, 8-4.8, 8-5.1, 8-5.2, 9-1.1, 5-10.2.c, 10-1 Penalty b-e. | 0 unreviewed breaks. | config/invariants.yaml precision. |
| R-IV-13 | Shall | CONF | Shall: Physics: player speed <= 10 m/s and acceleration <= 12 m/s² frame to frame (initial values, to calibrate); ball handler within 1.5 m of the ball while in control; one ball position per frame. | 0 unreviewed breaks. | R-DT-08 flags accelerations above 10 m/s² while R-IV-13 allows 12 m/s²; one limit in config (R-EN-06). |
| R-IV-14 | Should | TIER | Same text; consider Shall once frontcourt status (new-SR-3) is stored. | 0 unreviewed breaks. | A rules invariant at Should; it is Should only because frontcourt status is not stored (docs/data/game_ontology_coverage.md gap 9). |

### R-SB: Scoreboard and scorer errors (4 IDs, 2 with issues)

No change needed: R-SB-02, R-SB-03.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-SB-01 | Shall | NS, NV | Same text; type (j) scorebug lag measured by R-SB-03. | 100% of seeded types (a)-(i) detected; type (j) lag distribution reported per game; false-flag rate on a clean game <= 1 per half (initial value, to calibrate). | Ten detectors, only nine tested; no false-positive bound. |
| R-SB-04 | Should | TIER | Shall: same text. | 0 games with > 3 unresolved flags in any training manifest. | It gates training data like R-DQ-03, so a miss must block; Should is too weak. |

### R-MB: Made-basket detection (7 IDs, 2 with issues)

No change needed: R-MB-02, R-MB-03, R-MB-05, R-MB-06, R-MB-07.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-MB-01 | Shall | NV | Same text. | 100% of makes store every cue with frame and confidence; fused results meet R-MB-02/03/04 on gold-v1 and the 3 test games. | "Gold-v1 plus the 3 test games" names the data, not the pass condition. |
| R-MB-04 | Shall | NV | Same text. | Make frame within ±3 frames of the hand label in >= 95% of makes (share initial value, to calibrate); 2 vs 3 agreement >= 99%. | Frame tolerance without a share. |

### R-CX: Context features (19 IDs, 10 with issues)

No change needed: R-CX-06, R-CX-07, R-CX-08, R-CX-10, R-CX-11, R-CX-12, R-CX-13, R-CX-17, R-CX-18.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-CX-01 | Shall | TR | No text change; add a feature_registry table (or config file) to schema. | 100% of model features in the registry. | No table in schema/tables carries the feature registry. |
| R-CX-02 | Shall | TR, AMB | Shall: Feature weights are learned per layer; the prior for each causal class is written in the model spec (fixed external features: normal prior centred on 0 with SD set in config, initial value, to calibrate). | 100% of model specs list the prior per feature class; 0 equal-weight defaults. | "Strong shrinkage" is vague; no table. |
| R-CX-03 | Shall | TR | No text change; results stored in hypothesis_results. | Feature kept only if q <= 0.10 and walk-forward log loss improves. | No table declared. |
| R-CX-04 | Shall | DUP | Same text; capacity and altitude read from the R-FD-11 arena registry. | 100% of games filled or flagged. | Fields duplicated in R-FD-11. |
| R-CX-05 | Shall | NV | Same text. | Distance within 1 km of haversine recomputation; rest days and games in 7/14 days equal schedule recomputation (initial tolerance, to calibrate). | "Recomputed" without tolerance. |
| R-CX-09 | Shall | DUP | Keep as the single leakage rule for all pre-game data; R-DS-04, R-FD-06, R-PC-14 and R-CX-18 cite it. | 0 rows with as-of >= tip. | Leakage is restated in R-DS-04, R-FD-06, R-PC-14, R-CX-06, R-CX-18, R-OS-01. |
| R-CX-14 | Shall | DUP, NV | Same text; distances themselves come from R-MD-14 (campus-to-venue for both teams); this row adds the difference and the proximity flag (300 km, proposal). | Distances within 1 km of recomputation; flag equals rule on 100% of neutral-site games. | Campus-to-venue distance is also in R-MD-14 and R-CX-05. |
| R-CX-15 | Shall | DUP | Merge into R-MD-14 (game context stamp lists the same fields). | As R-MD-14. | R-MD-14 lists conference, tournament round, seeds and neutral site. |
| R-CX-16 | Should | NV | Same text. | Equals venue altitude minus campus altitude from the arena registry within 1 m. | "Recomputed" without tolerance. |
| R-CX-19 | Should | DUP | Merge into R-CC-05 (head-to-head history). | As R-CC-05. | Duplicate group R-CH-07/R-CC-05/R-CX-19. |

### R-PL: Physical load (17 IDs, 10 with issues)

No change needed: R-PL-09, R-PL-10, R-PL-11, R-PL-12, R-PL-13, R-PL-15, R-PL-17.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-PL-01 | Shall | CONF | Shall: Distance per minute and per possession by the R-PL-11 primary bands (the walk/jog/run/sprint 2.0/4.0/5.5 m/s placeholder kept as a view). | Total distance on a synthetic track within 3% (proposal). | R-PL-11 supersedes these bands (docs/research/load_thresholds.md sec. 1.4: 5.5 m/s is used by no basketball study). |
| R-PL-02 | Shall | CONF | Superseded by R-PL-12 (±2.0 and ±3.0 m/s², gated); 2.5 m/s² kept as a view. | As R-PL-12. | Different threshold from R-PL-12; docs/research/load_thresholds.md sec. 1.3. |
| R-PL-03 | Shall | NV | Same text. | Recomputes; every decline estimate carries a 95% interval; minimum 5 min per period. | "Recomputes; interval reported" weak but acceptable once interval is required. |
| R-PL-04 | Shall | AMB, NV | Shall: Recovery after timeouts, media timeouts and halftime = % change in 95th-percentile speed and in high-speed distance per minute in the 120 s after the stoppage vs the 120 s before (windows initial values, to calibrate). | Recomputes from PL-09 storage; every value carries n and interval. | "Recovery" undefined. |
| R-PL-05 | Shall | CONF | Same text; threshold aligned with R-PL-14 (one coverage threshold in config). | 100% of rows carry coverage; rows below the config threshold flagged. | R-PL-05 flags under 60% coverage while R-PL-14 drops stints under 70%. |
| R-PL-06 | Should | NV | Same text. | Trend per player with interval and n games; linked availability rows present for 100% of games. | "Chart per player" is a deliverable, not a test. |
| R-PL-07 | Should | NV | Same text. | Within ±0.05 s in >= 90% of 100 shots (share initial value, to calibrate); arc and entry angle within 3° (initial value, to calibrate) after R-CG-11. | Tolerance without share; angles untested. |
| R-PL-08 | Should | NV | Same text. | Routine time within ±0.2 s of hand timing on 50 free throws (initial value, to calibrate). | "Recomputes" only. |
| R-PL-14 | Shall | CONF | Same text; same config key as R-PL-05. | 0 summaries include stints below the threshold; coverage stated on every summary. | Threshold differs from R-PL-05. |
| R-PL-16 | Should | AMB | Same text. | Reference speed CV across games <= 5% (initial value, to calibrate) for players with >= 5 games at >= 70% coverage. | "Stable" undefined. |

### R-CO: Cognition (8 IDs, 5 with issues)

No change needed: R-CO-05, R-CO-06, R-CO-07.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-CO-01 | Shall | NV, FEAS | Same text. | Within ±80 ms of hand timing in >= 80% of 200 catches (share initial value, to calibrate); frame-rate uncertainty from R-CO-06 reported. | Tolerance without share; at 30 fps one frame is 33 ms, so ±80 ms is about ±2.4 frames. |
| R-CO-02 | Shall | NV, FEAS | Same text. | Within ±80 ms in >= 80% of 200 events (initial value, to calibrate); onset threshold 1 m/s² only after the R-PL-12 acceleration gate passes. | Onset uses an acceleration change of 1 m/s², below the noise floor reported in docs/research/load_thresholds.md sec. 1.6. |
| R-CO-03 | Shall | NV | Same text. | Recomputes from R-CO-02; pre-moved onsets agree with gold in >= 80% of 100 cases (initial value, to calibrate). | "Recomputes" only. |
| R-CO-04 | Shall | CONF | Shall: Pressure performance: decision and shot quality under contest <= 1.2 m, shot clock <= 5 s, and the clutch window of R-MD-13 (one definition in config). | Interval on every number; clutch cells use the R-MD-13 flag (0 records with a second clutch definition). | R-CO-04 uses "last 4 min with margin <= 5" while R-MD-13 defines clutch as <= 5 min left and margin <= 5. |
| R-CO-08 | Should | DUP | Merge clean-vs-late switches into R-CH-05; keep "two defenders on one attacker" here. | >= 85% (proposal). | Clean vs late switches is also R-CH-05. |

### R-OS: Opponent scouting (5 IDs, 0 with issues)

No change needed: R-OS-01, R-OS-02, R-OS-03, R-OS-04, R-OS-05.

### R-EN: Engineering (8 IDs, 1 with issues)

No change needed: R-EN-01, R-EN-03, R-EN-04, R-EN-05, R-EN-06, R-EN-07, R-EN-08.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-EN-02 | Shall | AMB | Same text. | Re-run of one game: byte-identical for CPU stages; GPU stages within 0.01 m position and 0.01 probability (initial values, to calibrate). | "A stated tolerance" is not stated. |

### R-CD: Coordination (5 IDs, 5 with issues)

Every row has at least one issue.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-CD-01 | Shall | TR | No text change; process requirement traced to coord/BOARD.md, not a table. | 0 session log lines without a board reference. | Process rule with no table (expected). |
| R-CD-02 | Shall | TR | No text change. | Export header revision exists in doc history. | Process rule; file-traced. |
| R-CD-03 | Shall | TR, NV | Same text. | Git history shows no deleted or changed lines in docs/user_inputs.md (diff contains only additions). | "Line count only grows" misses edits that keep the count; process rule. |
| R-CD-04 | Shall | TR | No text change. | 0 running lines during freeze. | Process rule; file-traced. |
| R-CD-05 | Shall | TR | No text change. | 0 unmapped actions. | Process rule; file-traced. |

### R-PR: Prediction (11 IDs, 4 with issues)

No change needed: R-PR-01, R-PR-02, R-PR-03, R-PR-04, R-PR-08, R-PR-09, R-PR-10.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-PR-05 | Shall | NS, NV | R-PR-05a Shall: win probabilities have 10-bin ECE <= 0.03 (proposal). R-PR-05b Shall: margin and total distributions have a PIT histogram consistent with uniform and CRPS reported against the R-PR-03 baselines. | a: ECE <= 0.03 on walk-forward and held-out games; b: PIT chi-square test p >= 0.05 (initial value, to calibrate) and CRPS no worse than the ratings baseline. | "Uniform PIT" has no test statistic; two targets of different kind. |
| R-PR-06 | Shall | AMB | Same text. | Engine log loss lower than the baseline on held-out windows, game-resampled 95% interval of the difference excluding 0. | "Beats" has no margin; use the project's interval rule (R-VA-06). |
| R-PR-07 | Shall | NV | Same text. | Over/under log loss vs de-vigged prop lines reported with n and interval; no edge claim below R-PR-08 sample rule. | "Scored against prop lines" has no pass condition. |
| R-PR-11 | Should | AMB | Same text with latency stated as 95th percentile. | 95th-percentile frame-to-probability latency <= 10 s; calibration as R-PR-05. | "Within 10 s" lacks a percentile. |

### R-PE: Possession engine (13 IDs, 3 with issues)

No change needed: R-PE-01, R-PE-02, R-PE-03, R-PE-06, R-PE-08, R-PE-09, R-PE-10, R-PE-11, R-PE-12, R-PE-13.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-PE-04 | Shall | NV | Same text. | Simulated possessions per game within ±1.5 of actual on average; two-sample KS p >= 0.05 on possession lengths (initial value, to calibrate). | KS test named without a decision threshold. |
| R-PE-05 | Shall | NV | Same text. | Predicted vs actual make rate within ±1 point per decile on held-out free throws (as R-PE-02). | "Calibrated" without a tolerance. |
| R-PE-07 | Shall | NV | Same text. | In >= 90% of score-by-time cells with n >= 30, simulated rate inside the game-resampled 95% interval of the D-I rate (initial value, to calibrate). | "Match" without tolerance. |

### R-MK: Markets (33 IDs, 7 with issues)

No change needed: R-MK-01, R-MK-03, R-MK-05, R-MK-06, R-MK-07, R-MK-08, R-MK-09, R-MK-11, R-MK-12, R-MK-13, R-MK-14, R-MK-15, R-MK-16, R-MK-17, R-MK-18, R-MK-19, R-MK-20, R-MK-23, R-MK-24, R-MK-25, R-MK-26, R-MK-27, R-MK-28, R-MK-29, R-MK-30, R-MK-31.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-MK-02 | Shall | DUP | No text change; R-MK-16 is the implementation spec (exact slots); R-MK-10 is the start date. Cross-reference. | >= 95% weekly. | R-MK-02, R-MK-10 and R-MK-16 state the same collector schedule and coverage test. |
| R-MK-04 | Shall | DUP | No text change; R-MK-15 is the implementation spec. | As R-MK-15. | Same as R-MK-15. |
| R-MK-10 | Shall | DUP, STALE | Merge with R-MK-02; the approval note "(P0m approved; job B of prompt 002)" moves to the decision log. | As R-MK-02. | Same test as R-MK-02; dated approval text in a requirement. |
| R-MK-21 | Shall | CONF | No text change; rename the runner ID column value "R-DQ-01 (runner)" to "runner-DQ-01" so it cannot be read as live R-DQ-01. | test_contracts.py passes. | Runner IDs reuse live IDs with different meanings (R-DQ-01, R-DQ-05, R-RG-07, R-RG-08, R-MK-01..09). |
| R-MK-22 | Shall / Should | NS, TIER | R-MK-22a Shall: cross-source line differences > 0.5 points flagged xsrc_gt_0p5. R-MK-22b Should: tiered rules XS-1..XS-4 run with thresholds from config until calibrated. | a: 100% of seeded > 0.5 differences flagged; b: XS rules run on every pull. | Tier cell "Shall / Should" breaks the one-tier rule of the requirement format. |
| R-MK-32 | Should | NV, TR | Same text. | Comparison table on file before any result is published; chosen method has the lowest log loss (ties by Brier). | Test "pending (analysis)"; no table. |
| R-MK-33 | Should | NV, NS, TR | Same text. | Each of the three conditions raises an alert on a seeded case. | Alerting is pending; three triggers; no table. |

### R-HR: Human review (12 IDs, 1 with issues)

No change needed: R-HR-01, R-HR-03, R-HR-04, R-HR-05, R-HR-06, R-HR-07, R-HR-08, R-HR-09, R-HR-10, R-HR-11, R-HR-12.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-HR-02 | Shall | NV | Same text. | Median time per item measured and shown; <= 20 s (initial value, to calibrate) so the 2 h budget of R-HR-04 covers about 360 items. | "Measured and shown" cannot fail. |

### R-VZ: Visualization (7 IDs, 7 with issues)

Every row has at least one issue.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-VZ-01 | Shall | TR | No text change; views are traced to the tables they read (state_frame, player_positions). | Offset <= 1 frame. | No table names VZ rows (expected for views); add view-to-table map. |
| R-VZ-02 | Shall | TR, DUP | No text change; display-side twin of R-EN-04. | 20 of 20. | Same traceability as R-EN-04 on the UI side. |
| R-VZ-03 | Shall | TR, DUP | No text change; display-side twin of R-VA-05/R-VL-08. | 0. | Duplicate rule at UI level. |
| R-VZ-04 | Shall | TR | No text change. | <= 0.1 m. | No table. |
| R-VZ-05 | Should | TR | No text change. | 0. | No table. |
| R-VZ-06 | Should | NS, TR | Split per view (matchup board, heat maps, passing network, layered win probability, filters, clip export), each Should with a render test. | Each view renders for a processed game. | Six products in one row. |
| R-VZ-07 | Should | AMB, TR | Should: One visual standard: metric labels only, one palette, text contrast >= 4.5:1 (WCAG 2.1 AA), layout usable at 375 px width. | Style check passes on every view. | "Readable" and "contrast checked" have no numbers. |

### R-CS: Compute and storage (10 IDs, 3 with issues)

No change needed: R-CS-02, R-CS-03, R-CS-04, R-CS-05, R-CS-06, R-CS-08, R-CS-10.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-CS-01 | Shall | DUP | No text change; subset of R-RR-01. | 0. | R-RR-01 already requires GPU type, GPU-hours and units. |
| R-CS-07 | Shall | NV | Same text. | Largest gap between consecutive checkpoint timestamps in each training run <= 15 min. | "Timestamps in the run record" does not state the check. |
| R-CS-09 | Shall | NS, AMB | Shall: Storage plan per season from measured file sizes (GB per game by resolution); Drive use stays under 80% of plan capacity. The 4K and 1080p estimates move to the plan file as starting values. | Measured size logged for 100% of files; Drive use < 80%. | Estimates and arithmetic in the requirement text; it is a plan, not a requirement. |

### R-VA: Validation (9 IDs, 4 with issues)

No change needed: R-VA-01, R-VA-04, R-VA-05, R-VA-06, R-VA-07.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-VA-02 | Shall | STALE | Shall: Court mapping error reported in metres. | 0 reports in other units. | Change-history note in the requirement text. |
| R-VA-03 | Shall | DUP | No text change; it is the per-game runner for R-EN-03, R-SY-10, R-SY-07 and R-IV-15. | 0. | Overlaps R-EN-03. |
| R-VA-08 | Shall | DUP | No text change; R-HY-05 is the same rule for the registry. | 0. | Duplicates R-HY-05. |
| R-VA-09 | Shall | AMB | Same text with tolerance: a drop of more than 1 point (initial value, to calibrate) or below the target blocks the release. | 0 releases with a drop above tolerance. | Tolerance unstated here and in the phase-gate rules. |

### R-HY: Hypotheses (7 IDs, 1 with issues)

No change needed: R-HY-01, R-HY-02, R-HY-04, R-HY-05, R-HY-06, R-HY-07.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-HY-03 | Shall | TR | No text change; registry history is config/hypotheses.yaml git history. | 0 edits after test date. | No table; file-traced. |

### R-PT: Pitch (1 IDs, 1 with issues)

Every row has at least one issue.

| ID | Tier | Issue(s) | Proposed rewrite | Acceptance criterion | Reason |
| --- | --- | --- | --- | --- | --- |
| R-PT-01 | Shall | TR | No text change. | Sign-off on file. | No table (deliverable). |

