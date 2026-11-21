# Requirement taxonomy (first pass, 11 Nov 2026, export rev 563)

831 ids in 10 top categories and 60 second-level categories (59 hold ids; products/movement-fingerprint waits for goal 9). A third level exists only under basketball/events (8 categories).
Each id has exactly one home: the `category` field of register.jsonl. Codes in brackets are the short codes used in parts/*.psv.

## Find any requirement in two steps

Step 1: pick the top category by the question you are asking. Step 2: pick the second level by its noun.

| Question | Top category |
| --- | --- |
| How do we decide, record, test claims, stay legal? | governance |
| Where does outside data come from, and what reference records do we keep? | data |
| What do we see in the video (people, ball, court, sound)? | perception |
| What is the official game situation at each instant? | state |
| What happened on the court, and how was it played? | basketball |
| What is it worth, and who wins? | value |
| What do betting and prediction markets say? | markets |
| What do people see and use? | products |
| How is it built, stored, run and monitored? | platform |
| How do we know it is right (truth sets, review, metrics)? | evaluation |

## The tree (count of ids per category)

- **governance (44)**: how the project decides and is allowed to work
  - requirement-rules [GOV.REQ] (3): source of truth, traceability checks, who may change targets
  - phases-and-freeze [GOV.PHS] (2): phase gates, the build freeze, live-after-offline rules
  - run-records [GOV.RUN] (10): run records, failure analysis, regression fixtures
  - hypotheses [GOV.HYP] (12): pre-registration, result rows, identification designs, side studies
  - coordination [GOV.COO] (4): shared board, verbatim inputs, messages between sessions
  - rights-privacy-ethics [GOV.RGT] (13): footage rights, licences, privacy exclusions, public-repo line, no betting
- **data (90)**: outside data and the reference records built from it
  - sources [DAT.SRC] (19): source register, use class, terms, keys, quotas, raw pulls
  - registries [DAT.REG] (16): games, rosters, officials, venues, availability, crosswalks
  - player-and-coach-cards [DAT.CRD] (28): card blocks frozen per game date, pre-game card, shooting surfaces
  - record-metadata [DAT.MET] (8): key stamp, time stamps, provenance and quality flags on every row
  - rules-and-constants [DAT.RUL] (5): rules edition per game, court constants and their citations
  - quality [DAT.QA] (14): contracts, quarantine, cross-source checks, drift, bias register, sanity ranges
- **perception (82)**: from broadcast pixels and sound to tracked objects
  - video [PER.VID] (22): capture and download standard, intake, shot type, replays, coverage
  - court-mapping [PER.GEO] (10): coordinate frame, camera-to-court mapping, camera registry, position error
  - detection-and-tracking [PER.DET] (16): people, teams, tracks, off-screen estimates, kinematics with sigma
  - identity [PER.IDN] (17): player ids, jersey numbers, appearance cues, no-face rules (baseline 3)
  - ball [PER.BAL] (8): ball position, holder, state, rim contact, 3-D arc
  - pose [PER.POS] (1): body pose per player (goal 9 adds here)
  - audio-and-commentary [PER.AUD] (8): audio alignment, transcripts, crowd, horns, music
- **state (130)**: the official game situation at every instant (baseline 4)
  - clocks-and-alignment [STA.TIM] (8): clock map, shot-clock values and resets, PBP-to-video sync, ordering
  - possessions-and-chances [STA.POS] (7): possession and chance ids and tables
  - state-record [STA.REC] (45): stored state fields, segments, transitions, corrections, flags
  - invariants [STA.INV] (51): rule checks run on the state
  - scoreboard-and-made-baskets [STA.SCO] (19): scorebug reading, lag, discrepancies, made-basket verification
- **basketball (267)**: what happened on the court and how it was played
  - events [BBL.EVT] (33), third level: shots (4), passes (7), ball-handling (6), rebounds (2), defensive-events (2), turnovers-and-violations (2), stoppages-and-timeouts (5), sequences-and-runs (3), plus 2 at the top
  - vocabulary-and-spots [BBL.SPT] (7): named spots, vocabulary map, broadcast phrases, name spaces (baseline 1)
  - actions [BBL.ACT] (18): movement primitives, screens, cuts, drives, footwork (baseline 2)
  - sets-and-plays [BBL.SET] (18): templates, set matching, set timelines, playbooks
  - defence [BBL.DEF] (28): schemes, coverages, help, presses
  - matchups-and-mismatches [BBL.MAT] (9): who guards whom, mismatch state, hunting
  - transition [BBL.TRN] (29): transition clocks, numbers, roles, get-back, definitions
  - possession-starts-and-restarts [BBL.PST] (23): start records, sides, throw-ins, jump balls, free-throw formations
  - officials-and-fouls [BBL.REF] (22): whistles, fouls, signals, crews, conduct
  - lineups-and-chemistry [BBL.LIN] (8): lineup ids and effects, pairs, passing networks, bench
  - coaches-and-bench [BBL.COA] (15): coach records, timeouts, reactions, bench events
  - game-context [BBL.CTX] (25): venue, travel, schedule, stakes, crowd, closeness, garbage time
  - physical-load [BBL.PHY] (21): speed bands, accelerations, load, decline, recovery
  - decisions-and-cognition [BBL.COG] (11): decision latency, reaction time, pressure, routines
- **value (51)**: what possessions and players are worth, and who wins
  - possession-value-and-credit [VAL.EPV] (19): value layers, action credit, player value
  - shot-quality [VAL.SQ] (2): shooter-agnostic and shooter-adjusted shot value, residuals
  - belief-state [VAL.BEL] (4): the running belief, surprise, anticipation
  - possession-engine [VAL.ENG] (13): the simulator and its sub-models
  - win-probability-layers [VAL.WP] (13): game, half, window and matchup probabilities, calibration
- **markets (37)**
  - data-and-fair-prices [MKT.DAT] (30): collection, storage, matching, de-vig, cross-source checks
  - benchmarks-and-edge [MKT.BEN] (7): edge, closing-line value, frozen predictions, staking on paper
- **products (45)**: what people see and use (baseline 5)
  - views [PRD.VIS] (22): views catalogue, synced video, view rows, live panel
  - analyst-studio [PRD.STU] (11): the editing canvas, inspector, drafts, bench
  - opponent-scouting [PRD.SCT] (8): opponent baselines, packets, spot plans, assignment forecasts
  - reports-and-pitch [PRD.REP] (4): half-time packet, post-game notes, published-number gate, pitch
  - movement-fingerprint [PRD.FPR] (0): placeholder for goal 9 rows (proposed in gaps.md)
- **platform (43)**: how it is built, stored, run and monitored
  - engineering-standards [PLT.ENG] (8): schemas, CI, environment, atomic writes, config-only thresholds
  - lineage-and-reproducibility [PLT.LIN] (11): content-addressed stages, deterministic ids, lineage, PBP versions
  - storage-compute-and-cost [PLT.STO] (15): Parquet layout, Drive, GPU budget, cost model
  - query-layer [PLT.QRY] (2): SQL views by grain (baseline 6)
  - registries [PLT.REG] (2): parameter and feature registries (metric registry missing, see gaps)
  - operations-and-monitoring [PLT.OPS] (5): orchestration, observability, latency, model monitoring
- **evaluation (42)**: how we know it is right
  - gold-and-labelling [EVL.GLD] (13): gold sets, labelling tool, agreement, timing gold (baseline 7)
  - human-review [EVL.HIL] (6): flags, review items, queue, budget, JEV log
  - validation-methods [EVL.VAL] (18): metrics, intervals, multiple testing, held-out games, leakage tests
  - vision-gates [EVL.GAT] (5): gate rules G1-G8 (thresholds live in the gate table)

## Tie-break rules (keep the cut mutually exclusive)

1. File by the thing the row produces or constrains, not by the section it came from or the tool it uses.
2. A rule about one data source goes to data/sources; a rule for all data or outputs goes to governance/rights-privacy-ethics.
3. A detector of a basketball concept goes to basketball/*; perception/* holds only generic objects (people, ball, court, sound, video).
4. Whistles, fouls and officials go to basketball/officials-and-fouls, even when detected from audio.
5. Made-basket detection goes to state/scoreboard-and-made-baskets (it moves the score).
6. Any value or probability model goes to value/*; testing a specific analytic stays with that analytic; general methods go to evaluation/validation-methods.
7. A registered hypothesis or study goes to governance/hypotheses.
8. A field stamped on every record goes to data/record-metadata; a per-instant game fact goes to state/state-record.

## Why this cut is better than the 40 sections

- The 40 sections mix three cuts: pipeline stage, inbox batch (sections 21, 22) and decision date (section 22), so one topic sits in up to six places (team fouls: sections 08 and 19; leakage: 07, 08, 23, 37; get-back: 13 and 16).
- Section names hide content: "Sync and events" holds 26 transition rows; "Value and scoring" holds 14 coach rows; "Detection and tracking" holds ball, gates, restarts and video rows.
- Six sections hold no ids at all (00, 01, 02, 06, 34) or one (39), while section 19 holds 90.
- The new tree answers one question per top category, so a newcomer needs one choice to reach the right shelf and one more to reach the row.
- Every baseline maps onto one or two second-level categories (1 vocabulary-and-spots, 2 actions, 3 identity, 4 state, 5 views and studio, 6 platform, 7 gold-and-labelling, 8 governance), so a baseline review reads one shelf.
- Duplicates become visible: rows with the same home and the same noun are the first place to look for redundancy.
- The tree has room for the future without new top levels: goal 9 goes to products/movement-fingerprint and perception/pose; live operation to platform/operations-and-monitoring.

## Old section to new categories (ids per target)

| Old section | ids | New homes |
| --- | --- | --- |
| 03 Run records and failure analysis | 12 | governance/run-records 9; requirement-rules 1; coordination 1; platform/operations 1 |
| 04 Data proof and quality | 20 | data/quality 13; lineage 1; sources 1; possessions 1; invariants 1; run-records 1; scoreboard 1; reports 1 |
| 05 Data sources and parameter catalog | 20 | data/sources 17; registries 1; hypotheses 1; rights 1 |
| 07 Foundation data and metadata layer | 44 | player-and-coach-cards 25; registries 13; sources 1; state-record 1; hypotheses 1; rights 1; identity 1; scouting 1 |
| 08 Global metadata on every record | 35 | state-record 16; record-metadata 7; vocabulary-and-spots 3; clocks 2; lineups 2; game-context 2; possessions 1; video 1; registries 1 |
| 09 Player identity and appearance layer | 16 | identity 15; gold-and-labelling 1 |
| 10 Video ingest and quality | 19 | video 15; audio 1; lineage 1; scoreboard 1; court-mapping 1 |
| 11 Court geometry, defined as math | 13 | court-mapping 7; rules-and-constants 3; vocabulary-and-spots 2; ball 1 |
| 12 Detection and tracking | 46 | detection-and-tracking 14; possession-starts 7; ball 6; vision-gates 5; actions 3; video 3; court-mapping 2; scoreboard 2; pose 1; events 1; identity 1; storage 1 |
| 13 Sync and events | 47 | transition 26; possessions 5; state-record 4; clocks 3; scoreboard 2; validation 2; possession-value 2; lineage 1; invariants 1; detection 1 |
| 14 Event taxonomy | 54 | officials-and-fouls 21; events 30 (all third levels); possession-starts 3; actions 1; audio 1 (2 more events rows sit at the top of events) |
| 15 Actions and playbook recognition | 38 | sets-and-plays 18; actions 12; vocabulary-and-spots 2; state-record 1; gold 1; events 2; matchups 1; possession-starts 1 |
| 16 Defensive structure | 33 | defence 28; transition 3; matchups 2 |
| 17 Value and scoring | 39 | possession-value 16; coaches-and-bench 14; lineups 5; shot-quality 2; hypotheses 1; cards 1 |
| 18 Game understanding | 6 | belief-state 4; validation 1; views 1 |
| 19 State record and invariants | 90 | invariants 49; state-record 22; scoreboard 13; clocks 3; rules-and-constants 2; possession-value 1 |
| 20 Possession start, sides and mismatches | 24 | possession-starts 12; matchups 6; events/passes 2; actions 2; scouting 1; game-context 1 |
| 21 Data platform, capture, products, Studio | 32 | analyst-studio 11; lineage 4; video 3; engineering 2; views 2; query-layer 1; operations 1; registries 1; detection 1; state-record 1; storage 1; gold 1; scouting 1; validation 1; rights 1 |
| 22 Measurement methods (20 Oct) | 6 | cards 1; audio 1; officials 1; ball 1; gold 1; cognition 1 |
| 23 Context features | 29 | game-context 22; platform/registries 2; win-probability 1; validation 1; record-metadata 1; cards 1; coaches 1 |
| 24 Physical load and shot physics | 23 | physical-load 21; cognition 1; validation 1 |
| 25 Behavioural and cognitive measures | 9 | decisions-and-cognition 9 |
| 26 Broadcast audio and commentary | 5 | audio-and-commentary 5 |
| 27 Opponent scouting layer | 6 | opponent-scouting 5; lineups 1 |
| 28 Engineering and data standards | 21 | engineering 6; lineage 4; coordination 3; operations 2; requirement-rules 2; quality 1; storage 1; query-layer 1; phases 1 |
| 29 Rights, licenses and ethics | 10 | rights-privacy-ethics 10 |
| 30 Layered prediction and market benchmarks | 15 | win-probability 12; validation 1; markets/benchmarks 1; phases 1 |
| 31 Possession engine | 13 | possession-engine 13 |
| 32 Odds and prediction-market data | 36 | markets/data 30; markets/benchmarks 6 |
| 33 Human-in-the-loop flagging and labelling | 13 | gold-and-labelling 7; human-review 6 |
| 35 Visualization layer | 21 | views 19; reports-and-pitch 2 |
| 36 Compute and storage | 12 | storage-compute-and-cost 12 |
| 37 Validation and evaluation | 15 | validation 11; gold 2; hypotheses 1; operations 1 |
| 38 Hypothesis registry | 8 | hypotheses 8 |
| 39 Open questions and decisions | 1 | reports-and-pitch 1 |
| 00, 01, 02, 06, 34 | 0 | No ids. Their normative prose (format rules, phase-gate table, JEV rules) is proposed as ids in gaps.md. |
