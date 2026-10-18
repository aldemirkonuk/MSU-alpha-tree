# Requirements synthesis: three perspectives, one proposal set

Date: 2026-10-18. Status: PROPOSAL ONLY. Add-only file. Nothing in the live requirements doc, `config/`, `schema/` or `src/` was edited; the requirements session decides. Machine-readable twin: `docs/requirements_review/proposals_consolidated.yaml` (validated with `yaml.safe_load`). Inbox note: `coord/requirements_inbox/008-requirements-improvement.md`.

Aldemir asked to think from an ESPN analyst's, a data engineer's and an NBA team data scientist's point of view (Think: game flow under the rules; Understand: how teams react; Analyze: how each role moves) and to synthesize how each perspective adjusts the requirements. This file merges those three panel reviews with the quality review of all 518 IDs, the round-2 ontology gap closures, the rules vocabularies and every earlier repo proposal into one verdict per existing ID, one de-duplicated `N-<FAMILY>-nn` series of new requirements, a rules-exact game-flow spine and a minimum build for the first two games.

## 0. Counts

| Item | Count |
| --- | ---: |
| Existing IDs given one merged verdict | 518 |
| verdict: keep | 308 |
| verdict: tighten | 133 |
| verdict: loosen | 6 |
| verdict: rewrite | 44 |
| verdict: split | 15 |
| verdict: merge-into | 12 |
| verdict: drop | 0 |
| Raw new-requirement proposals read (inbox 007: 93, round 2: 71, invariants: 34, analyst: 28, engineer: 35, scientist: 19, dictionaries and rules files: 10) | 290 |
| absorbed into an existing ID (no new ID needed) | 17 |
| merged into the N-series | 273 |
| New requirements after de-duplication (N-series) | 198 (P0 56, P1 84, P2 58) |
| Markets proposals already in the live doc (inbox 006 markets, mapped) | 22 |
| Cross-input conflicts resolved (each a decision for Aldemir) | 29 |
| Further open decisions, de-duplicated across the six inputs | 45 |

Verdicts per existing family (keep / tighten / loosen / rewrite / split / merge-into):

| Family | Area | IDs | keep | tighten | loosen | rewrite | split | merge-into |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R-RR | Run records and failure analysis | 9 | 6 | 2 | 0 | 0 | 1 | 0 |
| R-DQ | Data proof and quality | 10 | 5 | 4 | 0 | 0 | 1 | 0 |
| R-DS | Data sources | 15 | 10 | 3 | 0 | 1 | 1 | 0 |
| R-RG | Rights, licences and ethics | 11 | 9 | 2 | 0 | 0 | 0 | 0 |
| R-FD | Foundation data | 12 | 4 | 6 | 0 | 2 | 0 | 0 |
| R-PC | Player cards | 16 | 6 | 8 | 0 | 1 | 1 | 0 |
| R-MD | Global metadata | 20 | 11 | 3 | 0 | 4 | 1 | 1 |
| R-ID | Player identity | 15 | 14 | 1 | 0 | 0 | 0 | 0 |
| R-VI | Video ingest | 16 | 11 | 4 | 0 | 0 | 1 | 0 |
| R-CG | Court geometry | 11 | 7 | 2 | 0 | 2 | 0 | 0 |
| R-DT | Detection and tracking | 19 | 13 | 2 | 0 | 2 | 2 | 0 |
| R-BL | Ball | 8 | 6 | 2 | 0 | 0 | 0 | 0 |
| R-GT | Vision gates | 5 | 5 | 0 | 0 | 0 | 0 | 0 |
| R-SY | Sync and possessions | 10 | 5 | 3 | 0 | 2 | 0 | 0 |
| R-TR | Transition | 28 | 15 | 6 | 0 | 1 | 1 | 5 |
| R-EV | Events | 16 | 8 | 5 | 0 | 2 | 1 | 0 |
| R-AU | Audio | 4 | 2 | 2 | 0 | 0 | 0 | 0 |
| R-RF | Referees and whistles | 7 | 4 | 2 | 0 | 1 | 0 | 0 |
| R-ST | Actions and sets | 26 | 19 | 5 | 0 | 2 | 0 | 0 |
| R-DF | Defensive structure | 21 | 11 | 6 | 1 | 1 | 1 | 1 |
| R-VL | Value | 13 | 3 | 6 | 1 | 2 | 0 | 1 |
| R-CH | Chemistry and coaches | 8 | 3 | 5 | 0 | 0 | 0 | 0 |
| R-CC | Coach cards | 5 | 3 | 2 | 0 | 0 | 0 | 0 |
| R-GU | Game understanding | 6 | 1 | 3 | 2 | 0 | 0 | 0 |
| R-SR | State record | 15 | 7 | 3 | 0 | 4 | 1 | 0 |
| R-IV | Invariants | 16 | 5 | 2 | 0 | 9 | 0 | 0 |
| R-SB | Scoreboard and scorer errors | 4 | 1 | 3 | 0 | 0 | 0 | 0 |
| R-MB | Made-basket detection | 7 | 5 | 1 | 0 | 1 | 0 | 0 |
| R-CX | Context features | 19 | 11 | 6 | 0 | 0 | 0 | 2 |
| R-PL | Physical load | 17 | 6 | 8 | 2 | 0 | 0 | 1 |
| R-CO | Cognition | 8 | 3 | 2 | 0 | 3 | 0 | 0 |
| R-OS | Opponent scouting | 5 | 5 | 0 | 0 | 0 | 0 | 0 |
| R-EN | Engineering | 8 | 3 | 4 | 0 | 1 | 0 | 0 |
| R-CD | Coordination | 5 | 4 | 1 | 0 | 0 | 0 | 0 |
| R-PR | Prediction | 11 | 7 | 3 | 0 | 0 | 1 | 0 |
| R-PE | Possession engine | 13 | 9 | 4 | 0 | 0 | 0 | 0 |
| R-MK | Markets | 33 | 25 | 5 | 0 | 1 | 1 | 1 |
| R-HR | Human review | 12 | 11 | 1 | 0 | 0 | 0 | 0 |
| R-VZ | Visualization | 7 | 5 | 1 | 0 | 0 | 1 | 0 |
| R-CS | Compute and storage | 10 | 7 | 2 | 0 | 1 | 0 | 0 |
| R-VA | Validation | 9 | 6 | 2 | 0 | 1 | 0 | 0 |
| R-HY | Hypotheses | 7 | 7 | 0 | 0 | 0 | 0 | 0 |
| R-PT | Pitch | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| **All** | | **518** | **308** | **133** | **6** | **44** | **15** | **12** |

New requirements per family and priority:

| Family | P0 | P1 | P2 | Total |
| --- | ---: | ---: | ---: | ---: |
| N-AU | 0 | 1 | 1 | 2 |
| N-BL | 0 | 1 | 0 | 1 |
| N-CC | 0 | 2 | 4 | 6 |
| N-CD | 0 | 1 | 0 | 1 |
| N-CG | 1 | 1 | 0 | 2 |
| N-CH | 0 | 2 | 0 | 2 |
| N-CO | 0 | 0 | 1 | 1 |
| N-CS | 1 | 1 | 0 | 2 |
| N-CX | 0 | 2 | 7 | 9 |
| N-DF | 0 | 6 | 4 | 10 |
| N-DQ | 4 | 2 | 1 | 7 |
| N-DS | 0 | 1 | 0 | 1 |
| N-DT | 1 | 0 | 2 | 3 |
| N-EN | 4 | 3 | 0 | 7 |
| N-EV | 0 | 5 | 8 | 13 |
| N-FD | 2 | 0 | 4 | 6 |
| N-HR | 0 | 1 | 0 | 1 |
| N-HY | 0 | 1 | 0 | 1 |
| N-ID | 0 | 0 | 1 | 1 |
| N-IV | 26 | 7 | 0 | 33 |
| N-MB | 0 | 1 | 0 | 1 |
| N-MD | 5 | 7 | 0 | 12 |
| N-MK | 0 | 0 | 1 | 1 |
| N-OS | 0 | 1 | 0 | 1 |
| N-PC | 0 | 2 | 4 | 6 |
| N-PL | 0 | 1 | 4 | 5 |
| N-PR | 0 | 2 | 0 | 2 |
| N-RF | 0 | 5 | 9 | 14 |
| N-RL | 2 | 0 | 0 | 2 |
| N-RR | 1 | 0 | 0 | 1 |
| N-SR | 0 | 4 | 0 | 4 |
| N-ST | 0 | 9 | 3 | 12 |
| N-SY | 5 | 2 | 0 | 7 |
| N-VA | 2 | 4 | 0 | 6 |
| N-VI | 2 | 3 | 1 | 6 |
| N-VL | 0 | 2 | 3 | 5 |
| N-VZ | 0 | 4 | 0 | 4 |
| **All** | **56** | **84** | **58** | **198** |

Method. A script parsed every input table (quality review section 4: 181 rows; engineer verdicts: 92; analyst: 48 changed IDs; scientist: 43; new-requirement tables of the three panels; inbox 007 from `config/game_ontology.yaml` gaps; round-2 requirements; `config/invariants.yaml`), then: (1) one verdict per ID: the single changing input's verdict where only one input touched it, a hand-merged verdict for the 61 IDs touched by two or more inputs and for every ID in a conflict; quality-review rows without a verdict word were classed by their rewrite (pointer -> merge-into, a/b/c -> split, new text with CONF/CORR/STALE/UNIT/FEAS -> rewrite, acceptance only -> tighten, trace-only -> keep). (2) Round-2 requirements that "refine" an inbox-007 ID were merged with it; perspective proposals were merged where they ask for the same product; proposals that restate an existing ID were absorbed into that ID's merged verdict. (3) N-IDs were assigned per family in priority order. Every old proposal ID is in the id_map.

## 1. How each perspective adjusts the requirements

### 1.1 Think: game flow under the 2026-27 rules

All three panels drew the same state machine from the rules book (Rules 2-11, 4-9, 5-7 to 5-14, 6-1 to 6-6, 7, 8, 9, 11). They differ in what they need from it:

- **Data engineer**: state is a product of independent dimensions (ball live/dead, game clock, shot clock, team control, try in flight, restart pending, stoppage, period phase, counts). A throw-in is live with both clocks stopped for up to 5 s (6-1.2.b vs 5-10.2.a), so one "ball state" column is wrong. Each dimension changes a few hundred times a game while there are 155,000-162,000 frames, so state should be stored once per transition (N-MD-01, N-SY-01) and stamped with four clocks (N-MD-03). Condensed replays make video time discontinuous (UConn: 86.5 min of video for 134.4 min tip-to-final), so the clock map is a table (R-MD-08) and the cut map another (N-VI-01).
- **ESPN analyst**: the run of show (tip, media timeouts at 16/12/8/4 or 15/10/5, bonus at the 7th and 10th team foul, last 2:00 challenge rules, last 59.9 s clock stop, shot clock off, extra periods) decides what the stats desk must have ready; the flow state S0-S11 becomes a dimension of the same transition log (N-SY-01), and late-game situation flags become Shall (R-SR-11).
- **Team data scientist**: a possession or chance boundary in the wrong place moves points between start types and corrupts every model label; the chance terminal list (R-DQ-06c, K08) and the full 41-cause shot-clock vocabulary (R-SY-08, K18) are model inputs, not bookkeeping.

Requirements that follow: the rules layer (N-RL-01, N-RL-02), the invariants (N-IV-01 to N-IV-33), the typed transitions (N-SY-01), the clock map (R-MD-08), the chance definition (R-DQ-06, R-SY-05) and the spine in section 6, which traces every transition to detection, timing and analysis requirements.

### 1.2 Understand: how teams react

- **Data engineer**: almost every reaction is a pair of rows in different tables linked by time (timeout -> first set; screen -> coverage within t0 + 2.0 s). Joins need one time base, a declared window per pair and explicit "not observed" rows, so a reaction cut out of a condensed replay is not counted as "no reaction" (R-VI-02, N-VI-02).
- **ESPN analyst**: adjustments land at dead balls, often two or three possessions after the trigger; lags must be stored in possessions (R-DF-19). New products: run stoppers (N-EV-05), timeout purpose (N-CC-02), foul-trouble decisions (N-CC-01), hot-shooter response (N-DF-04), zone recognition lag (N-ST-08), mismatch hunting (N-ST-07), end-of-clock possessions (N-ST-09), get-back onset (N-DF-05).
- **Team data scientist**: teams react when things go badly, so naive before/after comparisons measure regression to the mean (beliefs register B2). Every reaction needs a matched baseline (N-CH-02) and every causal claim a registered design (N-HY-01).

### 1.3 Analyze: how each role moves, and what broadcast video can measure

- Reference speeds: NCAA D-I peaks 7.04 +/- 0.39 m/s (guards), 6.63 +/- 0.52 (forwards), 6.23 +/- 0.33 (centres) (Stone et al. 2022, via `docs/research/load_thresholds.md`).
- The engineer's noise-floor table is the decisive input: at position error 0.3 m a 0.5 s window gives speed noise 0.54 m/s and acceleration noise 8.39 m/s²; at the R-PL-13 target of 0.5 m, 0.90 m/s and 13.98 m/s². Speed bands are resolvable with 1 s windows; acceleration bands (+/- 2.0 / 3.0 m/s²), a 1 m/s² onset and jerk are not. This drives K01 and K03 and the uncertainty columns (N-DT-01), the resolvability gate (N-PL-01) and the change-point onset (R-CO-02).
- The analyst and scientist add what the camera hides: weak-side help, tag defenders and far corners are off-frame exactly when they matter (missing not at random), so contest fields are "unknown" rather than imputed (R-EV-07), off-screen estimates are flagged (R-DT-07) and the broadcast error budget decides what is estimable (N-VA-06).
- Timing: one frame is 33.4 ms at 29.97 fps; the made-basket frame can be fixed to about +/- 1 frame by hand; the scorebug lags the net by 1.50-2.60 s (median 1.933 s, n = 10). Hence R-MB-04, R-BL-04, R-SB-03 and N-SY-04.

### 1.4 Synthesize: six adjustments the three perspectives share

1. **Measure in the footage we have**: tolerances in frames at 29.97 fps (R-VI-01, R-MB-04, R-BL-04); scorebug window from measured lag (R-SB-03).
2. **Store state once, typed by the rules**: transitions and segments, team-neutral, with views for per-frame and MSU-relative use (K09).
3. **Uncertainty travels with every number**: position and kinematic sigma, resolvability gates, n and interval, reliability before display (K03, K12).
4. **One definition per word**: runs, clutch, transition class, coverage levels, foul trouble, chance, garbage time, all in config (K05, K06, K04, K10, K08, K28).
5. **Reconcile with the official record**: cross-source rows, end-of-game reconciliation, published-number gate, stat corrections propagated (N-DQ-04, N-DQ-05, N-SY-02).
6. **Reactions need baselines; pipelines need idempotency**: reaction catalogue with matched baselines and designs; content-addressed outputs, deterministic IDs and versioned sources.

## 2. Conflicts between inputs and recommended resolutions

Each conflict is also a one-line decision for Aldemir (section 9 and inbox 008).

### K01 Physical limits for speed and acceleration

Affected: R-DQ-02, R-DT-08, R-EN-03, R-IV-13.

- live doc: speed <= 10 m/s (R-DQ-02, R-EN-03); speed <= 10 m/s and acceleration <= 12 m/s² frame to frame (R-IV-13); R-DT-08 flags > 10 m/s²
- data engineer: 10 m/s over >= 0.3 s windows and 12 m/s² over >= 0.5 s windows on filtered tracks; flags, not quarantines; frame-to-frame limits fire on noise
- team data scientist: 9.0 m/s and 8.0 m/s² over >= 0.2 s windows from one shared key; D-I peaks are 6.2-7.0 m/s, so 10 m/s lets identity swaps through
- quality review: one limit in config (R-EN-06); R-DT-08 and R-IV-13 disagree
- **Recommended**: One key physics.* in config read by R-DQ-02, R-IV-13, R-EN-03 and R-DT-08: hard speed limit 10.0 m/s over >= 0.3 s windows (break); soft speed limit 9.0 m/s (review flag for identity swaps); acceleration 12 m/s² over >= 0.5 s windows (flag only), tightened to 8.0 m/s² once measured acceleration sigma <= 1.0 m/s²; court bounds + 1.0 m in the same key.
- **Why**: At sigma 0.3-0.5 m a 0.2-0.5 s window gives speed noise 0.5-0.9 m/s and acceleration noise 8-14 m/s² (engineer section 3.3), so 9.0 m/s / 8.0 m/s² on short windows would fire on true 7 m/s sprints; the soft flag keeps the scientist's identity-swap check without false breaks.
- **Decision**: Approve physics key: speed 10.0 m/s hard + 9.0 m/s soft flag (>= 0.3 s windows), acceleration 12 m/s² over >= 0.5 s, to 8.0 m/s² after sigma <= 1.0 m/s²?

### K02 Scorebug make-detection window

Affected: N-SY-04, R-SB-03, R-SY-01.

- live doc: window starts at 15 s, reset from measured lag
- data engineer: start 4 s (measured 1.50-2.60 s, n = 10), re-estimated per game and per field
- ESPN analyst: start 5 s, then per game p99 + 1 s
- team data scientist: start 4.0 s, then p99 + 0.5 s
- **Recommended**: Start 4.0 s; after each game re-set per field to p99 + 1.0 s, bounded to [3.0, 15] s; lag-corrected times feed state (new-SY-E4).
- **Why**: 15 s is six times the measured maximum and pairs the wrong basket in fast exchanges; with only n = 10 measured lags the larger +1.0 s margin is safer than +0.5 s.
- **Decision**: Set the scorebug window to 4.0 s initial, then per-field p99 + 1.0 s (3-15 s bounds)?

### K03 Acceleration bands and onsets vs the broadcast noise floor

Affected: N-PL-01, N-RF-14, R-CO-02, R-DT-08, R-PC-05, R-PL-02, R-PL-03, R-PL-12.

- live doc: bands +/- 2.0 / +/- 3.0 m/s² (R-PL-12), 2.5 m/s² (R-PL-02), onset at 1 m/s² change (R-CO-02), jerk (R-DT-08)
- data engineer: at the R-PL-13 target sigma 0.5 m acceleration noise is 14 m/s² (0.5 s window) or 2.3 m/s² (1.0 s); report bands only where sigma <= 0.5 m/s²; onset by change-point; no jerk
- team data scientist: acceleration over >= 0.2 s windows; jerk not computed; reaction times only as distributions with n >= 50
- ESPN analyst: broadcast cannot give reliable accelerations above about 3 m/s²; contact candidates use deceleration >= 3 m/s² (review only)
- quality review: acceleration and jerk need their own gate (load_thresholds.md sec. 1.6, RMSE up to 4.17 m/s²)
- **Recommended**: Keep the sourced bands but gate them: acceleration computed over >= 0.5 s windows with propagated sigma; band counts and accelerations reported only where sigma <= 0.5 m/s², else "unresolved" (counted); onsets by change-point on velocity; no jerk; the 0.2 s window is not used for acceleration; new-RF-A15 deceleration trigger only where resolvable.
- **Why**: A band that the measurement cannot resolve produces confident noise; the gate keeps the requirement and makes the resolvable share itself a reported number.
- **Decision**: Adopt the resolvability gate (sigma <= 0.5 m/s², >= 0.5 s windows, change-point onsets, no jerk)?

### K04 Ball-screen coverage granularity (4 coarse vs 13 fine)

Affected: N-DF-06, R-DF-06, R-DF-16.

- live doc: R-DF-06: the 13 taxonomy coverages; R-DF-16: two levels, coarse >= 90%, fine >= 80%
- ESPN analyst: publish the 4 coarse classes; fine only at confidence >= 0.8; coarse >= 85%, fine >= 70% on 200 screens
- team data scientist: coarse always; fine only after the fine classifier passes >= 75% on >= 300 screens from >= 5 games (NBA reference used 4 classes on full tracking)
- quality review: R-DF-16 is the keeper; R-DF-06 cites it
- **Recommended**: Store both levels; coarse always (>= 85% on >= 200 screens from >= 5 games at first release, rising to R-DF-16's 90% by season end); fine stored only after the fine gate (>= 75%, >= 300 screens, >= 5 games) and published only per screen at confidence >= 0.8.
- **Why**: The two gates are complementary: the scientist's is a model-level validation, the analyst's a per-screen display rule; a hedge called a drop on air is the costliest error.
- **Decision**: Approve coverage gates: coarse 85% then 90%; fine 75% on 300 screens/5 games; publish fine only at confidence >= 0.8?

### K05 Run definitions

Affected: N-EV-05, R-CC-02, R-CH-08, R-EV-13, R-MD-17.

- live doc: R-MD-17 "current run (points in the last 2 min each team)"; R-EV-13 "runs over 2, 4 and 6 min"
- ESPN analyst: three definitions never merged: unanswered; broadcast "a-b" shown at net >= 6; register net >= 8 in 120 s
- data engineer, team data scientist: register definition net >= 8 in a rolling 120 s (beliefs register B1/B2)
- ontology audit / gap closures: register plus strict unanswered >= 8-0; open question: which is primary
- **Recommended**: Three named definitions in config (unanswered, broadcast a-b, register), never merged; register is primary for hypotheses; broadcast display threshold default net >= 8 (6 kept as a config alternative); the 2/4/6-min net points stay numeric features, not "runs".
- **Why**: One word must have one definition per use; the register definition is the one the evidence (B1/B2) uses; >= 8 for display avoids calling 6-0 stretches "runs" and matches the register threshold.
- **Decision**: Primary run = register (net >= 8 in 120 s); broadcast display threshold 8 or 6?

### K06 Clutch and late-game window

Affected: R-CO-04, R-MD-13, R-PR-11, R-RR-03.

- live doc: R-MD-13 clutch = <= 5 min left and margin <= 5; R-CO-04 = last 4 min and margin <= 5
- ESPN analyst: one config clutch (<= 300 s, margin <= 5); last 240 s used for WP calibration and failure slices
- team data scientist: shrink pressure performance; no window preference
- quality review: one clutch definition in config
- **Recommended**: One clutch key: <= 300 s left in the second half or any extra period and margin <= 5 points; a separately named late_240 flag (last 240 s, the under-4 media segment) for slices and WP calibration; no third definition.
- **Why**: Two different "clutch" numbers for the same player would be published otherwise; 300 s / 5 points is the common public definition, 240 s is a broadcast segment, not clutch.
- **Decision**: Clutch = <= 300 s and margin <= 5 (late_240 kept as a separate flag)?

### K07 Made-basket frame tolerance at 29.97 fps

Affected: R-BL-04, R-MB-04.

- live doc: +/- 3 frames (+/- 0.05 s at 60 fps)
- data engineer, ESPN analyst: +/- 2 frames at 29.97 fps (+/- 0.067 s); +/- 3 at 60 fps
- team data scientist: +/- 1 frame at the file rate
- quality review: needs a share of makes
- **Recommended**: +/- 2 frames on >= 95% of makes, +/- 1 frame on >= 80% as a stretch; tolerances in frames at the file's rate; event times (R-BL-04) +/- 2 frames on >= 90% of 300 labels per type.
- **Why**: The hand label itself is +/- 1 frame (made_basket_lag.md), so +/- 1 frame for every make cannot be verified; 1080p60 does not exist for the pilot footage.
- **Decision**: Make frame +/- 2 frames on 95% (and +/- 1 frame on 80% as stretch)?

### K08 Chance boundaries and terminal events

Affected: R-DQ-06, R-MD-04, R-MD-06, R-SY-05.

- live doc: R-DQ-06 "rebounds + turnovers close every chance"; R-SY-05 end types shot, foul drawn, reset, turnover; R-MD-06 shot-clock start value per chance
- quality review: terminal list incl. foul or kicked-ball reset and period end
- data engineer: terminal list incl. foul with FTs or throw-in, held ball, period end
- ESPN analyst: made FG, final FT, turnover, defensive rebound incl. team and dead-ball rebounds
- **Recommended**: A chance is one shot-clock run inside a possession: a new chance starts after an offensive rebound off the ring and after any shot-clock reset inside the possession (defensive foul or kicked ball, max(20, left)); terminal list as R-DQ-06c (made FG with and-one closing after the FT, last FT made, defensive rebound incl. team and dead-ball rebounds, turnover, offensive rebound, shot-clock reset, held ball, period end).
- **Why**: R-MD-06 already defines the start value per chance, which only works if resets open chances; team and dead-ball rebounds are where possession counts drift from the box.
- **Decision**: Confirm: a shot-clock reset inside a possession (defensive foul, kicked ball) opens a new chance?

### K09 Where game state is stored (per frame vs segments) and the flow state

Affected: N-MD-01, N-SY-01, R-MD-01, R-SR-06.

- live doc: every frame and row carries all global metadata fields (R-MD-01); state_frame stamps 102 columns per frame
- data engineer: state_segments with validity intervals; per-frame and per-second state as views; typed transitions
- ESPN analyst: one flow_state per frame (S0-S11) with allowed transitions
- **Recommended**: Store state once as state_segments per dimension, opened by typed transitions (state_transitions, config/state_machine.yaml); flow_state is one dimension; state_frame and the per-row global stamp become as-of views.
- **Why**: About 1,000 segment rows replace 155,000 x 102 copied cells per game per pass; a correction is made in one place; the analyst still gets flow_state per frame through the view.
- **Decision**: Approve state_segments + state_transitions as stored truth, state_frame as a view?

### K10 Foul-trouble thresholds

Affected: N-CC-01, N-DF-03, R-MD-16, R-SR-11.

- live doc: R-SR-11: 2 in the first half, 4 in the second; R-MD-16: no cut-offs
- ESPN analyst: 2 in H1; 3 with > 600 s left in H2; 4 in H2/OT
- team data scientist: 2 in H1, 4 in H2
- quality review: one config table
- **Recommended**: One config table; default 2 (H1) / 3 (H2 with > 600 s left) / 4 (H2 <= 600 s and OT); the 2/4 rule kept as a named alternative so both can be reported.
- **Why**: The three-tier rule matches how benches talk about a third foul early in the second half; keeping 2/4 as a named view preserves comparability.
- **Decision**: Foul-trouble default 2/3/4 (analyst) or 2/4, or a coach-supplied MSU rule?

### K11 Shot quality with or without the shooter

Affected: N-VL-01, R-VL-04.

- ESPN analyst: xPts from location, contest, type and shooter prior; calibrated within 0.02 points per shot
- team data scientist: shooter-agnostic (league-average D-I shooter), layered location-only and contest-aware
- gap closures: shot-making residual = points minus xPts
- **Recommended**: Store both: shooter-agnostic xFG/xPts (shot quality, base of the shot-making residual) and shooter-adjusted xPts (prediction); both calibration criteria apply.
- **Why**: Shot-making cannot be separated from shot quality if the shooter is inside the quality model; prediction still needs the shooter.
- **Decision**: Approve two stored shot-quality versions (agnostic for quality, adjusted for prediction)?

### K12 Minimum n before a player tendency is shown

Affected: N-PC-02, N-VA-04, R-PC-11.

- quality review: cells with n < 30 descriptive only
- ESPN analyst: display suppresses n < 20 events
- team data scientist: reliability study gives the n where split-half reliability reaches 0.70 (n70); hide below
- **Recommended**: Use n70 from the reliability study per metric once it exists; until then n >= 30.
- **Why**: A data-driven threshold per metric beats one number; 30 is the more conservative of the two fixed values while n70 is unknown.
- **Decision**: Display threshold: n70 per metric, n >= 30 until measured?

### K13 Coverage threshold for load (60% vs 70%)

Affected: N-PL-04, R-PC-05, R-PL-05, R-PL-14.

- live doc: flag at 60% (R-PL-05) vs exclusion at 70% (R-PL-14)
- team data scientist: >= 70% on-camera time for the athletic block
- gap closures: >= 70% pose coverage for direction-weighted load
- **Recommended**: One config key, default 0.70, read by R-PL-05, R-PL-14, R-PC-05 and new-PL-7.
- **Why**: Two thresholds for the same coverage produce rows that are flagged but still summarised.
- **Decision**: Single coverage key at 0.70?

### K14 Possession type: exclusive labels vs multi-label flags

Affected: R-SY-04.

- quality review: two exclusive labels: tempo class and start type
- ESPN analyst: multi-label flags (ATO and SLOB at once), plus after media timeout, end of period, shot clock off
- **Recommended**: Three label sets: tempo class (exclusive), start type (exclusive) and situation flags (multi-label).
- **Why**: Both are right for different questions; an ATO SLOB possession needs two flags, while PPP by start type needs exclusive labels.
- **Decision**: Approve tempo + start type (exclusive) + situation flags (multi-label)?

### K15 Off-screen estimates per frame vs 10 Hz

Affected: R-DT-07.

- live doc: per missing player per frame
- data engineer: 10 Hz, per-frame imputation triples the largest table for no information
- team data scientist: coverage of the 95% region 90-98%; used only through a flag
- **Recommended**: Store at 10 Hz with a calibrated 95% region and an is_imputed flag.
- **Why**: Per-frame imputation adds rows, not information; calibration is what makes the estimate usable.
- **Decision**: Off-screen estimates at 10 Hz (not per frame)?

### K16 Reaction onset method and tolerance

Affected: N-DF-05, R-CO-02, R-EV-06.

- live doc: onset at an acceleration change > 1 m/s²
- quality review: +/- 80 ms on >= 80% of 200 events, after the acceleration gate
- data engineer: change-point on velocity, +/- 0.10 s on >= 80% of 100 labels; 1 m/s² is below the noise floor
- team data scientist: distributions with n >= 50; effective resolution 0.10-0.15 s
- ESPN analyst: get-back onset = velocity toward own rim > 2.0 m/s (new-DF-A8)
- **Recommended**: Change-point onset on velocity; tolerance +/- 0.10 s (3 frames) on >= 80% of 100 labels; per-player values only as distributions with n >= 50; velocity thresholds (2.0 m/s) are allowed because speed is resolvable.
- **Why**: +/- 80 ms is finer than one frame plus filter delay at 29.97 fps; velocity is measurable where acceleration is not.
- **Decision**: Reaction onset by change-point, +/- 0.10 s on 80% of 100 labels?

### K17 Drift check timing

Affected: N-VA-05, R-DQ-08.

- quality review: PSI > 0.25 with 10 quantile bins from now
- data engineer: PSI on one or two games is noise; verdict only from game 11
- team data scientist: model monitoring alerts at rolling 10-game ECE > 0.05 or PSI > 0.25
- **Recommended**: Quantiles from game 1; PSI verdicts and model alerts from game 11 (>= 10 games of the same source tier).
- **Why**: All three agree on PSI > 0.25; only the start differs, and a baseline of fewer than 10 games is not a baseline.
- **Decision**: Start drift verdicts at game 11?

### K18 Shot-clock reset cause list (33 vs 41)

Affected: R-SY-08, R-SY-09.

- config/invariants.yaml: 33 causes in shot_clock_reset_table
- rules layer (config/vocab/shot_clock_resets.yaml): 41 causes; 8 new_vs_invariants found re-reading Rule 2-11, 5-10.3, 9-11, 2-11.8/9
- team data scientist: mentions 38 cause rows
- **Recommended**: Adopt the 41-cause vocabulary as the single list (ids reuse the 33 exactly) and add the 8 new causes to config/invariants.yaml.
- **Why**: The vocab file is a strict superset with rule citations and pages; one list is needed by R-SY-08, R-SY-09 and the invariants.
- **Decision**: Adopt the 41-cause shot-clock list (add 8 causes to invariants.yaml)?

### K19 Short corner and help-spot definitions

Affected: N-MD-07.

- ontology audit (inbox 007): short corner provisional r 4.0-5.5 m, theta <= 15 degrees
- gap closures round 2: 3.5 < |x| <= 6.0 m, y <= 1.50 m (attacked-rim frame)
- **Recommended**: Adopt the round-2 box definition (it refines 007) provisionally, and confirm on MSU film before P3.
- **Why**: The x/y box follows how coaches mark the short corner along the baseline; the r/theta version clips players standing near the lane.
- **Decision**: Short corner = 3.5 < |x| <= 6.0 m, y <= 1.50 m, or define from MSU film first?

### K20 Value model start (now vs gated vs layered)

Affected: R-GU-01, R-VL-01.

- live doc: possession value at 10 Hz from the 10-player state
- data engineer: start 10 Hz value only after gates G1-G4 pass on two games; PBP value until then
- team data scientist: three layers (PBP state, location, full tracking) side by side; a layer used only if it beats the one below
- **Recommended**: Layers stored side by side from the start (layer 1 needs no video); layer 3 (10 Hz) only after G1-G4 pass on two games.
- **Why**: The positions are compatible: the gate decides when layer 3 starts, the layers decide whether it is used.
- **Decision**: Approve layered value with the G1-G4 gate on layer 3?

### K21 Pulled-player window (R-CC-03)

Affected: R-CC-03.

- live doc: pulled within 30 s of his turnover
- ESPN analyst: first dead ball or within 60 s (substitutions only at dead balls)
- team data scientist: compare with matched substitution hazard
- **Recommended**: Store first-dead-ball and 60 s windows (30 s as a sensitivity view) and always report against the matched baseline.
- **Why**: Substitutions happen only at dead balls (Rule 3-6), so 30 s misses legitimate hooks; without a baseline the rate means nothing.
- **Decision**: Pulled-player windows = first dead ball and 60 s, with matched baseline?

### K22 Contest distance classes

Affected: N-EV-03, R-CO-04, R-EV-07.

- gap closures: NBA "tight" edge 3.5 ft (1.07 m) or the 1.83 m saturation edge only? (open question)
- team data scientist: bins 0-0.6, 0.6-1.2, 1.2-1.8, > 1.8 m
- live doc: pressure slice contest <= 1.2 m (R-CO-04)
- **Recommended**: Store contest distance continuously; reporting bins 0-0.6, 0.6-1.2, 1.2-1.83, > 1.83 m (the last edge = rules closely-guarded distance and the Franks et al. saturation point); R-CO-04 pressure = <= 1.2 m (bins 1+2).
- **Why**: Continuous storage keeps every definition available; the bins align with R-CO-04 and the 1.83 m saturation edge.
- **Decision**: Contest bins 0-0.6 / 0.6-1.2 / 1.2-1.83 / > 1.83 m?

### K23 Latency target vs offline batch

Affected: N-EN-04, N-EN-07, N-VZ-01.

- ESPN analyst: tier-1 outputs <= 300 s after a segment, half-time packet within 600 s
- data engineer: pipeline sized for two games: DAG file and a runner, no orchestration server
- **Recommended**: Pilot is offline: latency is measured and logged per output (new-EN-A1 as Should) but not a gate; revisit after game 3.
- **Why**: Real-time delivery would force orchestration the engineer advises against for two games; measuring latency now keeps the option open.
- **Decision**: Is the half-time deadline a pilot goal, or offline-only this season?

### K24 Officials' role sampling

Affected: N-RF-08, N-RF-09, R-DT-12.

- quality review: role per frame, >= 95% of seconds
- ESPN analyst: role per second, >= 90% on 200 labelled seconds, position within 1.0 m
- data engineer: 1-5 Hz is enough
- rules layer: open question: per frame or only at whistles; CCA manual not available
- **Recommended**: Role per second (1 Hz) plus 10 Hz in the 2 s around each whistle; target 90% now, 95% after the CCA manual check.
- **Why**: Officials move slowly; whistle moments are where distance and angle matter.
- **Decision**: Officials' roles at 1 Hz plus 10 Hz around whistles?

### K25 Court constants: book edges vs config values

Affected: N-CG-01, N-CG-02, R-CG-01.

- config/court_ncaa_men.yaml, geometry.spot(): restricted area r <= 1.22 m; division line 12.73 m
- court constants check: restricted area membership r <= 1.270 m (outer edge, Rule 4-31); frontcourt y < 12.700 m (line is backcourt, 9-12); FT line is the far edge 4.191 m
- **Recommended**: Adopt the edge-correct values for rule tests (block/charge, frontcourt, lane) and keep the rounded values only as spot labels; store exact values (6.7501, 1.6002, 3.048).
- **Why**: The book measures each distance to a named edge; rule tests near a line need the exact edge.
- **Decision**: Adopt exact edge-correct court constants (1.270 m restricted area, 12.700 m frontcourt) and lift verified: false?

### K26 Throw-in spot rule 7-3.2.b wording

Affected: N-IV-15, R-DT-19, R-SR-08.

- 2025-26 rules change summary: free-throw line extended to both sidelines
- 2026-27 book text: garbled ("free-line extended"); diagram (pdf 85) shows the FT line extended
- inbox 006/007, rules layer, court constants check: adopt the diagram reading; elbow-to-corner reading obsolete
- **Recommended**: Adopt the FT-line-extended reading (diagram, pdf 85) for new-IV-18 and the restart vocabulary.
- **Why**: All three rules inputs agree once the diagram is read; the text is a typo.
- **Decision**: Adopt the FT-line-extended reading of Rule 7-3.2.b?

### K27 "Shooting" as a foul class vs a context flag

Affected: R-RF-03, R-SR-03.

- quality review: type list includes "shooting"
- rules layer (fouls.yaml): the book has no shooting class; open question
- ESPN analyst: store shooting / non-shooting as a property of the foul
- **Recommended**: Shooting and and-one are context flags on personal (common) and flagrant fouls; the class list follows the book.
- **Why**: Keeps the class list identical to the rules while preserving the free-throw logic.
- **Decision**: Store "shooting" as a context flag, not a foul class?

### K28 Garbage-time definition

Affected: N-MD-10.

- inbox 007: source flag; WP > 0.98 or < 0.02 with <= 300 s left; CTG-like rule
- gap closures: CTG thresholds adapted to the last 12:00 of the second half; open question
- dictionary: source flags stored, never used to drop rows
- **Recommended**: Store all three side by side; never drop rows; the WP rule is primary for our analyses because it adapts to 40-minute games.
- **Why**: The CTG thresholds were set for 48-minute NBA games.
- **Decision**: Garbage time: WP rule primary, CTG-adapted and source flags kept as views?

### K29 Numbering collisions between proposal rounds

Affected: all new-* proposals.

- gap closures: rules agent may issue the same new-SR/RF/EV/DT/BL numbers
- panel: persona letters A/E/S avoid clashes
- **Recommended**: Renumber everything into one N-<FAMILY>-nn series (this file); old IDs stay in the id_map.
- **Why**: One series, one map, nothing lost.
- **Decision**: Adopt the N-<FAMILY>-nn renumbering?

## 3. The 15 most important changes

| # | Change | IDs | What | Driven by |
| ---: | --- | --- | --- | --- |
| 1 | Clock map as a table | R-MD-08 | Video, game clock, shot clock and UTC aligned in piecewise segments with stated residuals; every timing metric and every market join runs through it. | data engineer (+ analyst, scientist on timing) |
| 2 | Typed rules state machine with a flow state | N-SY-01, N-IV-01 | Every state change is one typed transition (T01-T24) with its rule reference and allowed from/to pairs; invariants run on transitions, not on 155,000 frames. | data engineer, ESPN analyst |
| 3 | State stored once | N-MD-01, R-MD-01, R-SR-06, N-MD-02 | state_segments per dimension, team-neutral; per-frame state and the global stamp become views, so a correction is made in one place. | data engineer |
| 4 | Rules layer and rule corrections | N-RL-01, N-RL-02, R-IV-02, R-IV-10, R-RF-03, R-SY-08, N-CG-01 | Rules edition per game; two or three officials; media-format timeouts; 2026-27 foul classes without "intentional"; 41 shot-clock causes; edge-correct court constants. | rules layer, quality review, ESPN analyst |
| 5 | One chance definition | R-DQ-06, R-SY-05, R-MD-06 | Fixed terminal-event list; a shot-clock reset inside a possession opens a new chance; team and dead-ball rebounds counted as the scorer records them. | quality review, data engineer, ESPN analyst |
| 6 | Scorebug timing | R-SB-03, N-SY-04, R-SY-01 | Window 4.0 s (not 15 s), per-field lag model, lag-corrected state times; POSS is the arrow, never possession. | all three |
| 7 | Timing in frames at 29.97 fps | R-VI-01, R-MB-04, R-BL-04 | The footage that exists is 29.97 fps; every tolerance restated in frames; make frame +/- 2 frames on 95%. | all three, quality review |
| 8 | One physics key | R-IV-13, R-DQ-02, R-EN-03, R-DT-08 | Speed 10.0 m/s hard and 9.0 m/s soft over >= 0.3 s; acceleration 12 m/s² over >= 0.5 s, to 8.0 after calibration; checks on filtered tracks. | data engineer, team data scientist |
| 9 | Uncertainty travels with every kinematic value | N-DT-01, R-CG-08, R-PL-12, N-PL-01, R-CO-02 | Sigma columns; bands and onsets reported only where resolvable; change-point onsets; no jerk. | data engineer, team data scientist |
| 10 | Ball-screen coverage gates | R-DF-06, R-DF-16, N-DF-06 | Coarse always; fine only after its validation gate and at confidence >= 0.8; coverage-by-outcome table. | ESPN analyst, team data scientist |
| 11 | One vocabulary per word | R-MD-17, N-EV-05, R-MD-13, R-CO-04, R-MD-16, N-MD-11 | Runs (three named definitions), clutch (one key), foul trouble (config table), broadcast phrases for every label. | ESPN analyst (+ all) |
| 12 | Layered value and shot quality | R-VL-01, R-VL-04, N-VL-01, R-EV-07 | PBP, location and tracking layers side by side; shooter-agnostic and shooter-adjusted shot quality; contest unknown rather than imputed. | team data scientist, ESPN analyst |
| 13 | Reactions with baselines and designs | N-CH-02, N-HY-01, R-DF-19, R-CC-03 | Every reaction linked to its trigger with latency in s and possessions and a matched baseline; no causal claim without a registered design. | team data scientist, ESPN analyst |
| 14 | Idempotent, replayable lake | N-EN-01, N-EN-03, R-EN-07, N-SY-02, N-VI-01, N-VI-02 | Content-addressed stage outputs, deterministic IDs, PBP and box versions with diffs, cut map of condensed replays, per-frame stage mask. | data engineer |
| 15 | Numbers that reconcile | N-DQ-05, R-DQ-01, N-DQ-04, N-VA-01, N-VA-02 | Published-number gate against the official box; end-of-game reconciliation; timing gold set; held-out games registered before any fit. | ESPN analyst, data engineer, team data scientist |

## 4. Existing IDs: merged verdicts

Every one of the 518 IDs has a full record (verdict, proposed tier and text, acceptance, units, drivers, conflicts, priority) in `proposals_consolidated.yaml` under `existing_verdicts`. Below: every ID whose verdict is not keep, then the kept IDs per family.

### R-RR Run records and failure analysis

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-RR-01 | tighten | Run record adds config hash, stage output keys of every input and output, and the DAG node per stage. (Shall) | Re-running a run record's inputs reproduces the output keys of all deterministic stages (100%); GPU stages within the R-EN-02 tolerance. (%) | data_engineer |  |
| R-RR-02 | tighten | For every requirement tested in a run, the run record holds one result row with: requirement ID, metric, target, pass/fail/not-testable, sample size (count), and a 95% interval from a bootstrap resampled by game (1,000 resamples, initial value, to calibrate). (Shall) | 100% of tested IDs have all six fields; an ID with no gold sample is "not testable", never "pass". (%) | quality_review |  |
| R-RR-03 | split | R-RR-03a Shall: every Shall fail and Should miss has a failure analysis with error rate per slice: the 9 named technical slices plus 6 game-situation slices (transition vs half-court, after timeout, shot clock <= 5 s at the event, last 240 s of a half, media segment, camera shot type during the event) and a confusion matrix. R-RR-03b Shall: the same file lists the 20 worst cases (frame index, clip link), one cause from the fixed list {data, label, model, threshold, upstream gate, compute} and the next fix with expected gain in metric points. (mixed) | 100% of failed IDs have both parts; every slice shows n; slices with n < 50 are listed, not flagged; a linter checks the cause value is in the fixed list (count of invalid causes = 0). (%) | quality_review, espn_analyst | K06 |

### R-DQ Data proof and quality

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-DQ-01 | tighten | Every external field with a second source is cross-checked per game and written as one row per (game, field, source pair) to dq_cross_source with tolerance and result: final score and every official box counting stat per player and team (official box vs ESPN vs CBBD) exact; jersey numbers exact; officials exact after crosswalk; lines <= 0.5 points (R-MK-22a); each disagreement resolved (value chosen, reason logged) or flagged. (Shall) | 100% of two-source fields of processed games checked; 0 disagreements left neither resolved nor flagged; tolerances read from config; disagreement rate per field per season reported (%). (%) | quality_review, data_engineer, espn_analyst |  |
| R-DQ-02 | tighten | Contracts are generated from schema/tables/*.yaml (type, unit, range, nullable, enum, PK uniqueness, FK existence) and run on every write; ranges include positions inside the court + 1.0 m, game clock 0-1200 s per half and 0-300 s per extra period, shot clock 0-30 s; physical limits are not restated here but read from the one config key physics.* shared with R-IV-13, R-EN-03 and R-DT-08 (see conflict K01). (Shall) | 104 of 104 specs produce a contract; CI fails on a spec without type, unit (or "none") and range; 0 writes bypass the checker; one seeded out-of-range row per rule is rejected (100%); a unit test fails if any check hard-codes a limit. (%) | quality_review, data_engineer, team_data_scientist | K01 |
| R-DQ-04 | tighten | Lineage at two levels: partition-level manifest (input output-keys, code and config hashes) for every table; row-level source_ref only for event and registry rows, not per-frame rows. (Shall) | For any row, the manifest chain resolves to raw pulls or the video hash in ≤ 5 hops; per-frame tables carry no per-row lineage string. (count) | data_engineer |  |
| R-DQ-06 | split | R-DQ-06a Shall: per game, sum of possession points = final score per team; FGA = FGM + missed FG per team and player. R-DQ-06b Shall: team minutes = 200 + 25 per extra period. R-DQ-06c Shall: every chance ends in exactly one terminal event from the config list {made FG (and-one closes after its free throw), last free throw made, defensive rebound (including team and dead-ball rebounds as the scorer records them), turnover, offensive rebound after ring contact (opens the next chance), shot-clock reset inside the possession (defensive foul or kicked ball, max(20, left)), held ball with arrow throw-in, period end}. (mixed) | a, b: 100% of games pass or go to quarantine with the failing identity named; c: 0 chances with zero or two terminal events per game. (%) | quality_review, data_engineer, espn_analyst | K08 |
| R-DQ-08 | tighten | For each key field (list in config, R-EN-06) the per-game distribution is reported as quantiles from game 1; the population stability index against the running baseline (10 quantile bins, initial value, to calibrate) gives a drift verdict only once >= 10 games of the same source tier exist; PSI > 0.25 (proposal) raises a drift flag. (Shall) | Games 1-10: quantiles only (0 PSI verdicts); from game 11: a seeded shifted game raises the flag and an unchanged replay of a baseline game does not. (PSI) | quality_review, data_engineer | K17 |

### R-DS Data sources

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-DS-03 | tighten | Free sources are ingested before any paid source, in the listed order (hoopR releases, Torvik, CBBD, hoopR NCAA engine, NET, BPI snapshots, line history, prediction markets, Haslametrics, Prediction Tracker, recruiting and transfers via CBBD, Combine); the first pull of each passes R-DQ-02. (Shall) | Source register first-pull dates are in the listed order; 100% of first pulls pass R-DQ-02; 0 paid pulls before the last free one. (%) | quality_review |  |
| R-DS-04 | tighten | Backtests use point-in-time ratings only (Torvik Time Machine or daily archive, KenPom archive), with snapshot date strictly before the game date; end-of-season ratings are never used. (Shall) | 0 backtest rows with rating snapshot date >= game date. (count) | quality_review |  |
| R-DS-05 | tighten | One bitemporal crosswalk (valid_from, valid_to, recorded_at) for games, teams, players, venues, officials and coaches across ESPN, CBBD (play, sub and lineup athlete IDs are CBBD IDs), NCAA engine, Torvik, KenPom and EvanMiya name strings. (Shall) absorbs new-DS-1 (dictionary_games.md) | 100% of PBP athlete IDs of in-scope games resolve to an ESPN athlete ID or a local x- ID; 0 many-to-one mappings within a validity period. (count) | data_engineer |  |
| R-DS-10 | rewrite | Each source is tagged with one use class: model input allowed, reference only, or blocked until permission, as listed in docs/research/data_sources_catalog.md; Kaggle Massey Ordinals are model input only if the catalog licence check allows it (Massey site terms forbid AI/ML training without consent). (Shall) | 0 model features trace to a source not tagged "model input allowed". (count) | quality_review |  |
| R-DS-13 | split | R-DS-13a Shall: The CBBD key is stored only in the Mac keychain or a private .env outside the repo. R-DS-13b Shall: every CBBD call is logged and cached; monthly calls stay <= 1,000 (free-tier quota shared with College Football Data); identical calls are served from cache. R-DS-13c Should: bulk endpoints (by date or season) are used instead of per-game calls. (mixed) | a: 0 key matches in repo history; b: monthly calls <= 1,000 and 0 repeated identical calls; c: share of calls that are per-game <= 10% (initial value, to calibrate). (count/month) | quality_review |  |

### R-RG Rights, licences and ethics

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-RG-11 | tighten | The public-repo line is enforced in code: every row writer (video, processed, markets raw and parsed, review clips) uses one shared private-root guard; a pre-commit hook blocks .parquet, video and row-level CSV under the repo except whitelisted registry files. Markets RawStore already calls ensure_private (fixed 2026-10-18, test_engineer_review_fixes.py). (Shall) absorbs new-RG-E1; markets part resolved | Writing under the repo raises in a unit test for every writer; committing a .parquet or a 1 MB CSV under results/ fails the hook. (count) | data_engineer |  |
| R-RG-02 | tighten | Rights gate before any MSU pitch or public output: only numbers, drawings on our top-down court and cleared clips; no broadcast frames or audio; clips referenced by game_id and video time only; checklist signed by Aldemir. (Shall) | Signed checklist on file before P8; checklist line "no broadcast pixels" ticked for 100% of outputs; an automated scan of published files finds 0 embedded video frames. (count) | quality_review, espn_analyst |  |

### R-FD Foundation data

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-FD-01 | tighten | One games-registry row per game, written before any video of it is processed, with every field of schema/tables/games.yaml. (Shall) | 100% of games with footage have a row; 0 nulls in game_id, date, site, opponent, both jersey colours, footage path, fps, resolution; row timestamp < first processing timestamp. (%; count) | quality_review |  |
| R-FD-02 | tighten | ESPN game ID is the game-level join key; within a game, rows join on (game_id, source, source key) or on (video_id, frame_index); no join on names or times without the crosswalk or clock_map. (Shall) | Lint over transforms: 0 joins on team or player names; every game row has its CBBD game ID or a recorded "none". (count) | data_engineer |  |
| R-FD-03 | rewrite | Roster registry per player per season for MSU and every opponent with footage, with jersey-number history and the dates each number applied (without the status note "(today registry/rosters.csv has 29 rows, so this fails)"; move that note to the run record.) (Shall) | 0 PBP players without a roster row; 0 number mismatches against the broadcast on 3 games. (count) | quality_review |  |
| R-FD-05 | tighten | Availability log per player per game with status at tip (available, out, questionable or game-time decision, minutes restriction, suspended), the as-of UTC time and source of each status, reconciled after the game with 'did not play' from the box. (Shall) | Every rostered player has a status row per game with source and as-of ≤ tip; post-game reconciliation with the box on 100% of games. (count; min) | espn_analyst |  |
| R-FD-06 | tighten | For each game, opponent and team ratings (KenPom or Torvik) are taken from the latest snapshot dated on or before the day before tip (local date); a missing snapshot falls back to the nearest earlier one, flagged with its date. (Shall) | 0 rating rows dated on or after the tip date; every fallback row flagged with its snapshot date. (count) | quality_review |  |
| R-FD-08 | rewrite | Officials per game: the two or three on-court officials (Rule 2-1.1.a) with name, crew position (referee, umpire), crew-chief flag, source and as-of UTC; mid-game replacements logged with game clock; a missing name is "unknown", never guessed. (Shall) | 100% of processed games list 2 or 3 officials (3 expected in D-I) or a flagged unknown, cross-checked under R-DQ-01. (count) | quality_review, espn_analyst, rules_layer |  |
| R-FD-09 | tighten | Video specs live in video_files (one game, several files); the registry row lists video_ids. (Shall) | Both first games: hash, fps (30000/1001), resolution, codec, duration, edit type present. (count) | data_engineer |  |
| R-FD-11 | tighten | Arena registry (one row per venue): venue ID, capacity, altitude (m), coordinates, floor template ID, main-camera side; R-VI-13 (camera registry) and R-CX-04 (venue context) read from it instead of restating fields. (Should) | Every game links to an arena row; 0 venue fields stored twice. (count) | quality_review |  |

### R-PC Player cards

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-PC-03 | tighten | Great-circle distance (km) from hometown coordinates to campus and to each venue, per player. (Shall) | Recomputed haversine distance equals the stored one within 1 km (initial value, to calibrate) on 100% of rows. (km) | quality_review |  |
| R-PC-05 | tighten | Athletic block per player from our tracking: top speed (m/s, 95th percentile of 1-s smoothed speed, not the single maximum), peak acceleration and deceleration (m/s², only where the propagated sigma passes the K03 gate), lateral slide speed (m/s), change-of-direction time (s), jump height (m, only after R-CG-11 passes +/- 0.05 m on 50 hand-measured jumps); each with n (efforts), games, covered minutes and a 95% interval; only stints with >= 70% on-camera time (K13) across >= 3 games; else "provisional" or empty. (Shall) | 100% of values carry n and interval; top speed within the measured tracking speed error of a reference (radar or hand-timed sprint) on >= 20 efforts (tolerance from R-PL-13); empty when the gates fail. (%; m/s) | quality_review, team_data_scientist | K03, K13 |
| R-PC-06 | split | R-PC-06a Shall: shooting block per player: make rates by sector and ring, catch-and-shoot vs pull-up (R-EV-07 definitions), rim, mid-range, three, free throws; each a beta-binomial posterior with the prior fitted on the D-I population for that sector x ring x shot type, stored with n, posterior mean and 80% interval. R-PC-06b Should (hypothesis, registered under R-HY): free-throw % improves the three-point prior. (mixed) | a: for 20 random player-zones the posterior recomputes from stored counts and prior parameters within 1e-6; 100% of rates carry prior and n; b: pre-registered test with log-loss change on held-out games. (%) | quality_review, team_data_scientist |  |
| R-PC-07 | rewrite | Playmaking block per player: assist rate, potential assists (R-EV-03 definition), hockey assists, turnover rate by type, and three measured pass fields replacing "pass difficulty": pass distance (m), lane openness (m, nearest defender to the pass line) and receiver nearest-defender distance at the catch (m); each with n. (Shall) | Recomputation equals stored values (0 differences); assist and turnover rates from official PBP within 0.5 percentage points of the box (initial value, to calibrate); the three pass fields filled on >= 90% of passes with both players mapped; 0 free-text "difficulty" columns. (count; pp) | quality_review, team_data_scientist |  |
| R-PC-08 | tighten | Rebounding and defense: offensive and defensive rebound rates, box-out rate, matchup points allowed, steal, block and foul rates (matchup points allowed only for matchups with >= 30 possessions.) (Shall) | Recomputation equals stored values; rebound, steal, block and foul rates agree with box-score-derived rates within 0.5 pp (initial value, to calibrate). (count) | quality_review |  |
| R-PC-09 | tighten | Prior-level physicality: foul rate, free-throw rate allowed and offensive-rebound rate of the player's previous school and conference, as a measured stand-in for "how physical" his background was (Shall) | Recomputed from prior-level PBP equals stored values; source season and team recorded on 100% of values. (count) | quality_review |  |
| R-PC-10 | tighten | Role clusters are soft memberships fitted on the D-I population where PBP features allow, with bootstrap stability (adjusted Rand index ≥ 0.80 over 200 game-level resamples); unstable clusters are not shown. (Shall) | stability reported per cluster per season. (%) | team_data_scientist |  |
| R-PC-11 | tighten | Every tendency (drive direction, finishing hand, shot-clock use, pass-or-shoot by zone, help frequency) stores n, as-of date and a shrunk estimate; the display hides a tendency below its reliability n (n70 from the reliability study N-VA-04) and, until that study exists, below n = 30 events. (Shall) | 100% of tendency rows carry n, as_of and shrunk value; the display layer shows 0 tendencies below the threshold. (count) | quality_review, espn_analyst, team_data_scientist | K12 |
| R-PC-12 | tighten | Development block: season-over-season and within-season change per stat (units per season) with a 95% interval, and career D-I minutes (min). (Shall) | 100% of trend values carry an interval; career minutes equal the sum of box-score minutes (0 min difference). (%) | quality_review |  |
| R-PC-16 | tighten | International and pro background per player (FIBA youth events, pro leagues, games played), with source and date. (Should) | For MSU players, 100% of fields filled or marked "not public" after a documented search. (count) | quality_review |  |

### R-MD Global metadata

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-MD-01 | rewrite | Every row carries the key stamp (game_id, pass, stage output key, and either (video_id, frame_index) or (period, game_clock_s, order_index)); the state stamp of schema/global_metadata.yaml (clocks, score, fouls, control, lineup) comes from an as-of join to state_segments and is materialised only in views and exports. (Shall) | For a random 1% sample of rows, joined state equals the materialised view (100%); no stored table except state_segments holds a copy of global state fields. (count) | data_engineer | K09 |
| R-MD-02 | tighten | Ball-control state per frame, one of the 6 states (naming the six states (MSU control, opponent control, contested, in flight, inbound pending, dead) and the vocabulary file.) (Shall) | >= 95% frames correct and >= 90% of state changes within ±0.2 s of gold-v1 (proposal). (%) | quality_review |  |
| R-MD-07 | rewrite | Team fouls per half and bonus state (bonus at the 7th team foul, double bonus at the 10th; counts reset only at the start of the second half; extra periods continue the second-half count, Rule 5-9.4), and timeouts left per team. (Shall) | Equal to PBP-derived values at 100% of fouls and timeouts. (%) | quality_review |  |
| R-MD-08 | rewrite | The video <-> game clock <-> shot clock <-> UTC map is stored as piecewise segments in a clock_map table, one per running-clock stretch per video file and pass (video_id, start/end frame, start/end video_ts_ms, period, game clock at both ends, rate, shot clock at start and status, UTC estimate with source and error, residuals); monotonic inside each running-clock stretch; UTC from PBP wall clock only where it is monotone over >= 3 consecutive plays, elsewhere interpolated with a stated error. (Shall) absorbs new-MD-E1, new-SY-E6 | Over live main-camera frames with a legible clock: median \|OCR - map\| <= 0.1 s and 99th percentile <= 0.5 s; 100% of live frames in exactly one segment; game clock non-increasing within a segment (0 exceptions); non-monotone wall-clock stretches flagged with an error bound (s) per segment. (count; s) | data_engineer |  |
| R-MD-11 | merge-into R-VI-03 | Mark as a pointer: "Superseded by R-VI-03 (shot type) and R-VI-05 (coverage); kept for the metadata list." (Should) | Covered by R-VI-03 and R-VI-05 tests. (%) | quality_review |  |
| R-MD-13 | split | R-MD-13a Shall: 5-min window ID, a last-240-s flag (named late_240, used for the under-4 media segment and late-game slices) and the single clutch flag from config (<= 300 s left in the second half or any extra period and margin <= 5 points) per record. R-MD-13b Shall: media-timeout segment ID following Rule 5-14.10 and the game's media format (16/12/8/4 or 15/10/5 marks; a team timeout, review or challenge within 30 s before a mark becomes the media timeout, 5-14.10.e; first second-half team timeout takes media length, 5-14.10.d); boundaries from the observed media timeouts, not from the marks. (mixed) | a: recomputation from the clock equals stored values (0 differences); b: media timeout times agree between video, scorebug and PBP on 100% of pilot games and segment boundaries match PBP media timeouts in >= 95% of segments (initial value, to calibrate). (count; %) | quality_review, espn_analyst, rules_layer | K06 |
| R-MD-16 | tighten | Per player per record: personal fouls so far and a foul-trouble label from a config table of (fouls, period, seconds left) cut-offs; default table (proposal): 2 in the first half; 3 with > 600 s left in the second half; 4 with <= 600 s left or in an extra period; the legacy 2/4 rule kept as a named alternative; plus seconds on the bench since entering foul trouble and re-entry time. (Shall) | Counts equal PBP at 100% of fouls; labels recompute from the config table (0 differences); on-screen foul graphics read as weak labels (N-VI-05) agree on >= 95% of graphics read. (count) | quality_review, espn_analyst | K10 |
| R-MD-17 | rewrite | Score state: margin, lead changes, times tied, largest lead per team; runs stored under three named config definitions, never merged: (a) unanswered points since the opponent's last point; (b) broadcast run "a-b" = the window ending now and starting right after a score by either team that maximises the running team's net points, displayed only when net >= the config threshold (default 8, K05); (c) register run = net >= 8 points in a rolling 120 s of game clock (beliefs register B1/B2), the primary definition for hypotheses; plus pre-possession win probability from a model trained only on data dated before the game (as-of), with model version. (Shall) | All three recompute from score_events within 0 points; (b) matches on-screen run graphics on >= 90% of graphics read (weak label); the leakage test (N-VA-03) passes for the WP column. (count) | espn_analyst, team_data_scientist, gap_closures_round2 | K05 |
| R-MD-18 | tighten | Event rows carry est_utc and est_utc_err_s (from clock_map), not only game-level UTC. (Shall) | ≥ 95% of PBP events of games with PBP wall clock carry est_utc with err ≤ 30 s. (count) | data_engineer |  |

### R-ID Player identity

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-ID-15 | tighten | Synthetic kit and lighting images (named generator, version logged) are tested for team-assignment only, after the P1 baseline passes, never for identity. (Should) | Kept only if team-assignment accuracy on real gold frames rises by >= 0.5 points (initial value, to calibrate, matching R-ID-13). (pp) | quality_review |  |

### R-VI Video ingest

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-VI-01 | split | R-VI-01a Shall: native >= 1080p without rescaling (lower: tier 2 in the registry). R-VI-01b Shall: constant frame rate at the source's own rate; 29.97 fps is the expected and fully supported case (1080p60 does not exist for the 2025-26 condensed replays); 59.94 fps is used when a source offers it; every timing requirement states its tolerance in frames at the file's rate. R-VI-01c Shall: original audio track kept. (mixed) | a: probe height >= 1080 px or tier-2 tag; b: frame-interval spread < 1 ms; fps listed in the intake report; 0 Shall failures caused only by 29.97 fps; c: audio stream present with duration within 0.1 s of video. (count; ms) | quality_review, data_engineer, espn_analyst, team_data_scientist |  |
| R-VI-02 | tighten | Intake report per file: length vs expected, dropped and frozen frames, letterboxing, overlays, edit type (full broadcast, condensed replay, highlights), the cut map of video stretches vs game-clock ranges (stored in the cut-map table of N-VI-01) with every removed dead-ball span typed (timeout, media timeout, free-throw routine, review, half time) and flagged not_in_footage, and the live-play share in main wide. (Shall) | Both pilot games: cut map covers 100% of the 2,400 s of game clock; every game-clock discontinuity >= 1 s found against a hand check; frozen live-play segments listed (Louisville 2.3 s at 2,302.6 s); 0 removed spans imputed as "nothing happened". (% frames) | data_engineer, espn_analyst |  |
| R-VI-06 | tighten | Usable-possession flag = coverage score (R-VI-05) >= a threshold in config (initial value 0.6, to calibrate on 3 games), and the share of usable possessions per game. (Shall) | Report on 100% of games; on gold-v1, possessions flagged usable have tracking recall >= the R-DT target (to calibrate). (%) | quality_review |  |
| R-VI-13 | tighten | Camera registry per arena: main-camera side, approximate height, zoom range seen (main-camera side read from R-FD-11.) (Shall) | Calibration error per arena meets R-CG-03. (m) | quality_review |  |
| R-VI-16 | tighten | Video decoded on the GPU hardware decoder (AV1, VP9 or H.264) at >= 4x real time for 1080p60 (initial value, to calibrate); CPU decode only for unsupported codecs, logged. (Shall) | Decode fps logged per run; >= 4x real time on the target GPU; 0 unlogged CPU fallbacks. (fps) | quality_review |  |

### R-CG Court geometry

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-CG-01 | rewrite | Court constants in config/court_ncaa_men.yaml verified against the current NCAA men's rulebook, each with its rule citation, and verified: true (without "(today the file says verified: false, so this fails)".) (Shall) | 100% of constants cite a 2026-27 rule; file marked verified by Aldemir. (count; flag) | quality_review | K25 |
| R-CG-04 | tighten | Player ground point taken at the feet, not the box centre (Shall) | Foot-point ground error on gold-v1: median <= 0.30 m and p90 <= 0.60 m (initial values from R-CG-03, to calibrate); airborne frames flagged 100%. (m) | quality_review |  |
| R-CG-07 | tighten | Relative geometry every frame: ball-handler frame, defender–attacker relation, passing-lane distance, driving cone, spacing, hull area (list each relative-geometry quantity with its unit in config so each has its own unit test.) (Shall) | Each of the 6 quantities within 0.01 m / 0.1° / 0.01 m² of hand calculation. (m; degrees) | quality_review |  |
| R-CG-08 | rewrite | Every position row stores x, y to 0.01 m and its 1-sigma uncertainty position_sigma_m (m) from the court mapping and the ground-point estimate; reports round to 0.1 m and show only values with sigma <= 0.5 m (others marked low confidence). (Shall) | On gold-v1 hand-labelled ground points per court zone: the stated 68% interval covers 60-76% and the 95% region covers 90-98%. (count) | data_engineer, team_data_scientist |  |

### R-DT Detection and tracking

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-DT-07 | tighten | Off-screen position estimate per missing player stored at 10 Hz (not per frame) during live play, with a 95% region whose empirical coverage on re-appearing players is 90-98%; downstream models take it only through an is_imputed flag, never as observed. (Shall) | 10 Hz rows for 100% of missing player-seconds of live play; coverage computed on >= 500 re-appearances is 90-98%. (m; %) | data_engineer, team_data_scientist | K15 |
| R-DT-08 | split | R-DT-08a Shall: velocity (m/s) and heading (degrees) per player from smoothed positions of a named body point (pelvis_floor or ankle_mid), filter and window named in config (R-PL-10), each with a propagated 1-sigma column. R-DT-08b Should: acceleration (m/s²) over windows >= 0.5 s with propagated sigma, released for analysis only where the K03 resolvability gate passes; jerk is not computed. (mixed) | a: hand-timed runs (R-PL-13) give speed bias <= 0.3 m/s and SD <= 0.5 m/s on >= 20 runs; filter named and sigma present on 100% of rows; b: stationary players show acceleration noise below 2.0 m/s² in >= 95% of seconds before release; 0 jerk columns. (m/s) | quality_review, data_engineer, team_data_scientist | K01, K03 |
| R-DT-12 | rewrite | Officials tracked with role (lead, trail, centre in three-person crews; lead and trail in two-person crews, Rule 2-1.1.a) per second with role confidence and floor position (m), and at 10 Hz in the 2 s around each whistle; role changes stored as rotation events. (Shall) | Role correct in >= 90% of 200 labelled seconds (proposal; 95% target after the CCA manual check), reported by crew size; position within 1.0 m of gold when on the main camera. (%) | quality_review, espn_analyst, rules_layer | K24 |
| R-DT-14 | split | R-DT-14a Shall: throw-in event while the ball is out of bounds: side, half, team, after-timeout flag, first-pass target. R-DT-14b Shall: 5-second throw-in count (Rule 7-6.6) from the official's hand-off to release. R-DT-14c Shall: formation label (stack, box, line, diamond, other). (mixed) | a: >= 95% of throw-ins found, attributes >= 95% correct; b: count within ±0.5 s of gold in >= 90% (initial value, to calibrate); c: formation correct >= 85% (proposal). (%; s) | quality_review |  |
| R-DT-15 | tighten | Jump balls and held balls as events with formation: the two jumpers (IDs) and the positions of the other eight players at the toss (m). (Shall) | 100% matched to PBP; jumper IDs correct in >= 95% (initial value, to calibrate). (%) | quality_review |  |
| R-DT-19 | rewrite | Throw-in spot after fouls and violations in the frontcourt: below the free-throw line extended → nearest spot under the basket; above it → the 28 ft (8.53 m) mark (rule 7-3.2.b) (with "the 8.53 m mark (28 ft in the rules)" so the stored unit is metric.) (Shall) | >= 95% (proposal). (%) | quality_review | K26 |

### R-BL Ball

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-BL-04 | tighten | Pass start and end, shot release and catch stored as frame index plus video_ts_ms, with the frame period (0.033 s at 29.97 fps) as stated resolution. (Shall) | 100% of rows carry a frame index; times within +/- 2 frames of the hand label on >= 90% of 300 labelled events per type (share initial value, to calibrate). (%) | data_engineer, team_data_scientist | K07 |
| R-BL-05 | tighten | Make or miss per shot from rim, net and ball. (Shall) | Agreement with PBP after sync >= 99.5% (initial value, to calibrate); 100% of disagreements flagged for review (R-MB double verification). (%; count) | quality_review |  |

### R-SY Sync and possessions

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-SY-01 | tighten | Scoreboard fields (game clock, shot clock, score, period, team fouls, timeouts, arrow) read on every frame around value changes and at >= 2 fps otherwise; tenths read when the game clock is below 60 s (Rule 1-18.2); each field stores its change time and lag-model correction (N-SY-04); the "POSS" marker writes only to the arrow column, never to ball possession; gaps filled from clock_map with status (observed, interpolated, unknown). (Shall) | Game clock exact >= 99%, shot clock exact >= 98%, other fields >= 99% of scorebug-visible readings (initial values, to calibrate); score = PBP at 100% of scoring events; game clock known (observed or interpolated) on 100% of live main-camera frames; a unit test proves POSS never writes to a possession column. (%) | quality_review, data_engineer, espn_analyst | K02 |
| R-SY-02 | tighten | Every PBP event mapped to a video time with an interval (start, end) and method; order within a second from CBBD id. (Shall) | Median abs error ≤ 1.0 s and 95th percentile ≤ 3.0 s against 100 hand-labelled events on game 1. (%) | data_engineer |  |
| R-SY-04 | tighten | Possession table: start, end, outcome, points, length (s) and three label sets: tempo class (primary, early, half-court; from R-TR-09), start type (after make, after made last FT, after defensive rebound, after turnover, after held ball/arrow, period start) and multi-label situation flags (ATO with calling team, after media timeout, SLOB, BLOB, end of period = start with <= 35 s left, shot clock off). (Shall) | Possession points = final score in 100% of games; tempo and start type each >= 90% correct (proposal); every possession has >= 1 flag set or "none"; counts per flag per game reported. (%) | quality_review, espn_analyst | K14 |
| R-SY-05 | rewrite | Chance table: chance number, start cause, start shot clock (s), time used (s), end type from the R-DQ-06c terminal list (made shot, missed shot with defensive rebound, missed shot with offensive rebound, shot-clock reset by defensive foul or kicked ball, turnover, held ball, period end). (Shall) | Offensive rebounds per game = PBP; every chance has exactly one end type (0 exceptions); end types reconcile with R-DQ-06c. (count) | quality_review, data_engineer | K08 |
| R-SY-08 | rewrite | Shot-clock reset and no-reset events read from the scoreboard: time, value before, value after (s) and cause from the full list in config/vocab/shot_clock_resets.yaml (41 causes, Rule 2-11 plus 5-10.3, 9-11, 2-11.8, 2-11.9; supersedes the 33-cause table in config/invariants.yaml), including no-reset stoppages. (Shall) absorbs inbox 007 new-SY-2 | >= 98% of resets found; >= 95% causes correct (proposal); every stoppage with a live shot clock has a reset or no-reset row. (%) | quality_review, rules_layer, inbox007_or_invariants | K18 |

### R-TR Transition

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-TR-01 | rewrite | Transition clock per frame: seconds since the transition start of R-TR-08; it ends at the end of R-TR-08. (Shall) | Start within ±0.2 s of gold in >= 95% of changes (proposal). (%) | quality_review |  |
| R-TR-05 | merge-into R-TR-09 | Superseded by R-TR-09 (reported class, state-based) and R-TR-18 (the clock-based class is kept only as the named flag clock_class_7_14). (Shall) | Lint: 0 output columns called transition_class without a definition suffix; tests as R-TR-09 and R-TR-18. (%) | quality_review, espn_analyst |  |
| R-TR-06 | merge-into R-TR-26 | Superseded by R-TR-26 (value of each break state per second), computed from the R-VL-01 value layers. (Shall) | As R-TR-26. (points) | espn_analyst, team_data_scientist |  |
| R-TR-08 | tighten | Transition start: secure control after a defensive rebound, steal, live-ball turnover or blocked shot recovered; after a made basket only when the inbound is thrown before the defense is set. End: the first of a shot, a foul, a dead ball, or "defense set" = all 10 players in the half-court and every attacker with a defender within 2.0 m on the goal side for 1 s (proposal) (Shall) | Start and end within ±0.5 s of Aldemir's labels in >= 90% of 200 possessions (share initial value, to calibrate). (%) | quality_review |  |
| R-TR-10 | tighten | Seconds to defense set, per possession and per defender (who was last back) (Shall) | Equal to recomputation from R-TR-08 (0 differences); last-back defender correct in >= 90% of possessions vs gold (initial value, to calibrate). (count) | quality_review |  |
| R-TR-11 | merge-into R-TR-18 | Superseded by R-TR-18 (same rule, fuller list of definitions, never merged). (Shall) | As R-TR-18. (count) | quality_review, espn_analyst |  |
| R-TR-12 | split | R-TR-12a Shall: time to get back per defender (s) and who stops the ball (ID). R-TR-12b Shall: rim protector, matchups found, cross-matches and recoveries (IDs, labels). (mixed) | Each element >= 90% agreement with Aldemir's labels (proposal); times within ±0.5 s. (%) | quality_review |  |
| R-TR-13 | merge-into R-TR-20 | Merge into R-TR-20 (same phase timestamps, fuller list); keep trailer arrival and drag screen as R-TR-20 phases. (Shall) | As R-TR-20. (s) | quality_review |  |
| R-TR-14 | merge-into R-TR-23 | Merge into R-TR-23 (pushes after makes and free throws, reported separately). (Shall) | Inbound, first-pass and crossing times within ±0.3 s of gold in >= 90% (initial value, to calibrate). (count) | quality_review |  |
| R-TR-16 | tighten | Opportunity vs choice: possessions where a numbers advantage existed at the secure moment, and whether the team pushed or pulled back (Shall) | Opportunity flag agrees with Aldemir's labels in >= 90% of 200 possessions (initial value, to calibrate). (count) | quality_review |  |
| R-TR-17 | tighten | Per game, transition share (%) and points per possession from PBP clock definitions compared with our state definition; a gap > 10 percentage points in share (initial value, to calibrate) goes to review. (Shall) | 100% of games have the comparison; 100% of gaps above the threshold have a review entry. (%) | quality_review |  |
| R-TR-20 | tighten | Phase timestamps as elapsed time and as shot-clock reading: start, outlet catch, half-court crossing, scoring zone, inside the arc, paint touch, numbers advantage start and end, first action, first shot, pull-back, first half-court action, defense set (our rule and a CTG-like rule) (Shall) | Each phase time within ±0.3 s of gold in >= 90% of breaks (share initial value, to calibrate). (%) | quality_review |  |
| R-TR-25 | tighten | Breaks stopped by a foul: time, ball position, fouler's distance to the ball, whether a clear path existed; take-foul candidates counted per team per game (Shall) | 100% of foul-stopped breaks link to a PBP foul; clear-path flag agrees with gold in >= 90% (initial value, to calibrate). (%) | quality_review |  |

### R-EV Events

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-EV-03 | tighten | Potential assist = completed pass whose receiver attempts a field goal or draws a shooting foul with ≤ 1 dribble and ≤ 2.0 s after the catch [H, to calibrate]. Hockey assist as already defined. (Shall) | rule recomputes from passes and shots on 100% of rows. (%) | team_data_scientist |  |
| R-EV-06 | tighten | Drive: start point, direction (baseline or middle, left or right), depth reached (m), result; a drive is a dribble move gaining >= 3 m toward the rim (proposal); defender reaction = at drive start and at paint arrival the first help defender (ID), help arrival time (s), help distance (m), the kick-out target and its nearest-defender distance at the catch (m). (Shall) absorbs new-EV-S1 | Drives found >= 90% and direction correct >= 95% (proposal); help fields filled on >= 80% of drives with >= 8 players mapped. (%) | team_data_scientist | K16 |
| R-EV-07 | tighten | Each shot stores release r (m) and theta (degrees); shot family (catch-and-shoot = 0 dribbles and touch <= 2.0 s; pull-up = >= 1 dribble; post-up; putback <= 2.0 s after an offensive rebound; transition flag per R-TR-09); shot type from the coach and broadcast vocabulary (catch-and-shoot, pull-up, step-back, side-step, floater/runner, hook, layup, dunk, tip-in, putback, alley-oop, fadeaway, bank); dribbles and touch time (s); nearest defender distance (m) and angle (degrees; in front = within +/- 45 degrees of the shooter-rim line) at catch and release; second-nearest defender distance; closing speed of the nearest defender over the 0.5 s before release (m/s); shooter speed and heading at gather; shot and game clock; result incl. rim outcome; assisted flag and assister from PBP. (Shall) absorbs new-DF-S3 | All fields on >= 90% of shots with shooter and nearest defender mapped (sigma <= 0.5 m); contest fields are "unknown" when the shooter or nearest defender is not mapped with sigma <= 0.5 m at release, never imputed; unknown share per game in the run record (%); models use an explicit unknown level; shot type >= 85% agreement with coach labels on 300 shots (proposal); assisted flag = PBP on 100% of made FGs. (%) | espn_analyst, team_data_scientist | K22 |
| R-EV-08 | tighten | For every missed try: positions of all 10 players at release and at rim contact, ball landing point (r, θ) when visible, box-outs, and who secured it; enough to compute positioning, hustle and conversion [L4]. (Shall) | fields filled on ≥ 80% of rebounds where ≥ 8 players are on camera. (%) | team_data_scientist |  |
| R-EV-10 | rewrite | Turnover type per turnover from config/vocab/violations_turnovers.yaml, mapping 1:1 to the 2026-27 violations and PBP codes, adding backcourt over-and-back (9-12) and elbows (9-13) to the 11 listed. (Shall) absorbs inbox 007 new-EV-3, new-EV-4 | Count = PBP; type = PBP where coded; 0 PBP turnover codes without a mapping. (count; %) | quality_review, rules_layer, inbox007_or_invariants |  |
| R-EV-13 | tighten | Sequence features: previous possession result; net points over the last 120, 240 and 360 s of game clock as numeric features (not called runs); run flags only from the R-MD-17 definitions; first set after a timeout. (Shall) | One run vocabulary in config; features recompute from score_events (0 differences). (count) | espn_analyst | K05 |
| R-EV-15 | split | R-EV-15a Shall: timeout record: caller, type, game and shot clock (s), ball state, score run in the prior 120 s, lineup changes. R-EV-15b Shall: post-timeout outcome: set called, points on next possession, defensive scheme change. (mixed) | a: 100% of PBP timeouts recorded, fields equal PBP where coded; b: set and scheme labels agree with gold >= 85% (initial value, to calibrate). (count) | quality_review |  |
| R-EV-16 | rewrite | Coach's challenge record per Rule 11-4 and 2-9.19: challenging coach, challengeable type (out of bounds at any time; basket interference or goaltending and secondary-defender restricted-area calls only before the last 2:00 of regulation, 11-4.1.a-c), timeout used (30 s or full), review duration (s), outcome (stands or overturned), timeout charged or retained, second challenge earned; officials' own reviews (11-2, 11-3) logged separately in R-RF-07 with trigger and duration. (Shall) | Every challenge in PBP or on the broadcast has a row (100%); fields equal PBP where coded; duration within +/- 2 s of video when visible; every record passes the challenge invariant (N-IV-13). (count) | quality_review, espn_analyst, rules_layer |  |

### R-AU Audio

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-AU-04 | tighten | Arena music and noise during dead balls (now allowed by rule) flagged, so crowd-loudness measures are not mistaken for crowd reaction (Should) | On 100 labelled dead-ball stretches, flag precision and recall >= 90% (initial value, to calibrate). (%) | quality_review |  |
| R-AU-01 | tighten | Commentary transcript, time-aligned (Should) | WER <= 20% on a 10-min sample per source (initial value, to calibrate). (%) | quality_review |  |

### R-RF Referees and whistles

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-RF-03 | rewrite | Foul record with class from config/vocab/fouls.yaml (2026-27 classes: personal common, player-control, team-control, double, simultaneous, multiple, Flagrant 1, Flagrant 2, Class A, Class B, administrative and contact dead-ball technicals; no "intentional": legacy labels map per legacy_label_map, deliberate end-game fouls = common + is_end_game_deliberate or Flagrant 1 away from the ball, 4-15.2.c.1.d); shooting / non-shooting and and-one as context flags; fouler, fouled, location r (m) and theta (degrees), shot clock, team-foul count and whether the foul put the opponent in the bonus or double bonus; free throws awarded. (Shall) absorbs inbox 007 new-RF-3 | 100% of fouls carry a class from the config list (0 outside it); type and players equal PBP where coded; bonus-trigger flag recomputes from team fouls (0 differences). (%) | quality_review, espn_analyst, rules_layer | K27 |
| R-RF-06 | tighten | Crew and per-official tendency tables as of each game date, pace-adjusted: fouls per 100 possessions, FTA per FGA, home-away foul split, call-type mix, reviews per game; each shrunk toward the D-I mean weighted by games worked, with n games and interval. (Shall) | Posterior recomputes from stored counts (0 differences); every published value shows n games and interval; values with n < 10 games flagged. (count) | espn_analyst, team_data_scientist |  |
| R-RF-07 | tighten | Video reviews (type, trigger, duration s, outcome) logged per game; held balls and arrow uses are covered by R-MD-12 and R-EV-14. (Shall) | Review log equals PBP/broadcast list for 100% of games. (count) | quality_review |  |

### R-ST Actions and sets

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-ST-02 | rewrite | Actions built from primitives in relation; on-ball screens use the strict and loose rules of R-ST-17 (one definition, not a third). (Shall) | Screens (strict rule): precision >= 90%, recall >= 85% on gold (proposal). (%) | quality_review |  |
| R-ST-05 | tighten | Set match per chance outputs the coaching name (namespaced per R-ST-22) and its broadcast phrase (N-MD-11), with calibrated confidence. (Shall) | Top-1 family agreement with coach labels ≥ 80% and top-3 ≥ 95% on 300 MSU chances (proposal); confidence ECE ≤ 0.05. (%) | espn_analyst |  |
| R-ST-08 | tighten | Per phase: execution speed (cutter speed m/s, screen-to-cut delay s, catch-to-action time s), spacing (m), hull area (m²), defensive reaction delay (s) and value at the boundary, the last taken only from a validated value layer (R-VL-01); null, not a placeholder, until it passes. (Shall) | Recomputation from tracks equals stored values; screen-to-cut delay and catch-to-action time within +/- 80 ms of hand timing on >= 80% of 100 phases (share initial value, to calibrate); value column null until the R-VL-01 layer gate passes. (count) | quality_review, team_data_scientist |  |
| R-ST-10 | tighten | Labelled set sample: per family, ≥ 50 instances from ≥ 5 different games for evaluation, split by game (no game in both train and test). (Shall) | split file lists game IDs. (count) | team_data_scientist |  |
| R-ST-12 | rewrite | Templates are defined by role (handler, screener, roller or popper, spacer, cutter, post), never by player name or ID, so any season's roster matches. (Shall) | On the first 2026-27 footage the template match rate is within 10 points of the 2025-26 rate (proposal); 0 templates reference a player ID. (pp) | quality_review, espn_analyst |  |
| R-ST-19 | tighten | Alignment snapshot when the handler first slows below 2 m/s with the ball inside y = 9 m (or at the first pass after crossing half-court), matched to all alignment families (including 3-out 2-in, two-guard front, triangle, 2-1-2 and 1-3-1, post-entry, wing dribble entry, elbow entry, 4-out 1-in, 1-4 low); a possession can be "start matched, continuation unknown" (Shall) | Accepted matches agree with gold alignment labels in >= 85% of possessions (initial value, to calibrate); acceptance rule mean error < 1.8 m and margin > 0.4 m (proposal). (m) | quality_review |  |
| R-ST-23 | tighten | Special-situation rules layer: ball at the inbounder's disposal, first legal touch, burned inbound, clock audit in the last 60 s, end-of-game inbound bucket by time left (Shall) | Each special-situation event within ±0.2 s of gold in >= 90% (share initial value, to calibrate). (%) | quality_review |  |

### R-DF Defensive structure

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-DF-01 | tighten | Matchup per defender per second as a posterior probability over the five attackers, from a model in which a defender's expected position is a weighted mix of his attacker, the ball and the rim [L2]; stored as top-1 and probability. (Shall) | top-1 agrees with hand labels on ≥ 85% of 300 defender-seconds sampled across ≥ 5 games; probabilities calibrated (ECE ≤ 0.05). (%) | team_data_scientist |  |
| R-DF-03 | tighten | Rim protector per second (the "player C" under the rim) and his distance to the ball (Shall) | Recomputes from tracks; rim protector ID agrees with gold in >= 90% of seconds (initial value, to calibrate). (%) | quality_review |  |
| R-DF-04 | loosen | Scheme state per second where ≥ 8 players are mapped; otherwise per possession phase (transition, half-court) with the scheme carried and flagged carried. (Shall) | share of seconds with observed vs carried scheme reported per game. (%) | team_data_scientist |  |
| R-DF-06 | rewrite | Ball-screen coverage per screen in the R-DF-16 two-level form: coarse class (contain/drop, show/hedge, two-on-ball, switch) always; fine coverage (13 taxonomy F3 classes) stored when the fine classifier has passed its validation gate (>= 75% on >= 300 labelled screens from >= 5 games), else fine = unknown; published outputs show the fine label only where its per-screen confidence >= 0.8. (Shall) | Coarse >= 85% agreement with coach labels on >= 200 screens from >= 5 games for first release (initial value; R-DF-16 target 90% by season end); fine >= 75% on the gate set; 0 published fine labels with confidence < 0.8. (%) | quality_review, espn_analyst, team_data_scientist | K04 |
| R-DF-07 | split | R-DF-07a Shall: off-ball screen coverage per screen. R-DF-07b Shall: post defense (front, three-quarter, behind) per post touch, plus double-teams: where the double comes from (top, baseline, strong-side wing, weak side), trigger (on catch, first dribble, turn), time from catch to double (s) and the rotation behind it; double = 2 defenders within 1.5 m of the holder for >= 0.5 s. (mixed) | a: >= 80% correct on gold (proposal); b: post position >= 80% and double-team label >= 85% agreement on 100 post touches (proposal). (%) | quality_review, espn_analyst |  |
| R-DF-08 | tighten | Rotation measures: reaction delay after each pass, closeout distance and speed (Shall) | Delay within ±80 ms of hand-timed gold in >= 80% of 200 passes (share initial value, to calibrate); closeout distance within 0.3 m and speed within 0.3 m/s (initial values, to calibrate). (ms) | quality_review |  |
| R-DF-10 | merge-into R-DF-20 | Merge with R-TR-12 and R-DF-20 (transition defense); keep R-DF-20 as the field list. (Shall) | As R-DF-20 and R-TR-12. (%) | quality_review |  |
| R-DF-16 | tighten | Two-level ball-screen coverage: 4 coarse classes (contain/drop, show/hedge, two-on-ball, switch) always, then the fine coverage when the K04 gate passes; drop depth in sourced bands (high 0.6-1.83 m, standard 1.83-3.05 m, deep > 3.05 m) measured 0.3 s after the screen moment. (Shall) | Coarse >= 85% (first release) rising to >= 90% by season end, fine >= 75% on the gate set (>= 300 screens, >= 5 games); depth within 0.5 m of gold on 100 screens (initial value, to calibrate). (%) | espn_analyst, team_data_scientist | K04 |
| R-DF-19 | tighten | Scheme-change triggers stored with each change as features: timeout after a run, "not working" (opponent PPP over the first 10 half-court possessions, stored with n and interval), inbound-only scheme, score and clock state, rim-protector foul trouble, opponent hot shooter (N-DF-04), opponent lineup change, after a timeout; each change stores possessions elapsed since its trigger; no report states that a trigger caused a change without the registered identification design of N-HY-01. (Shall) | Every scheme_changes row has a trigger code or "none found"; lag in possessions recomputes (0 differences); 0 causal claims without a design field. (count) | espn_analyst, team_data_scientist |  |
| R-DF-20 | tighten | Get-back clocks kept as separate fields: first defender at r ≤ 1.5 m of his rim, at r ≤ 2.5 m, and first defender back past r 6.75 m or half-court; plus ball stopped, defenders back at 2, 3 and 4 s, transition wall, swap of a mismatched defender (Shall) | Each field present per possession; get-back times within ±0.5 s of gold in >= 90% (initial value, to calibrate). (count) | quality_review |  |

### R-VL Value

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-VL-01 | rewrite | Possession value in three layers stored side by side with a coverage flag per possession-second: (1) PBP-state value every second for every D-I game (score, time, start type, shot clock, fouls); (2) location value when ball and shooter are mapped; (3) full-tracking value at 10 Hz only when >= 8 players and the ball are mapped, and only after gates G1-G4 pass on two games; a layer is used in reports only if it beats the layer below. (Shall) absorbs new-VL-S4 | Each layer calibrated on held-out games (10-bin ECE <= 0.03 on the points-per-possession scale); each higher layer beats the one below on held-out log loss of the terminal outcome; gate record shows G1-G4 pass before the first 10 Hz row. (points) | data_engineer, team_data_scientist | K20 |
| R-VL-02 | tighten | Value change per action credited by a written rule, and credits for each action sum to the value change within 1e-6. (Shall) | test on all rows of value_credits. (points) | team_data_scientist |  |
| R-VL-04 | rewrite | Shot quality per shot in two stored versions: (i) shooter-agnostic xFG and xPts for a league-average D-I shooter from the R-EV-07 fields (location-only layer from D-I PBP shot locations; contest-aware layer from tracked shots), used for shot-making residuals; (ii) shooter-adjusted xPts adding the shooter prior, used for prediction. (Shall) | Held-out games: contest-aware layer improves log loss over location-only by >= 1% with 10-bin ECE <= 0.02; contest coefficient has the expected sign with 95% interval excluding 0; mean predicted vs actual within 0.02 points per shot over >= 1,000 shots and within 0.05 per shot type with >= 200 shots. (points; log loss) | espn_analyst, team_data_scientist | K11 |
| R-VL-05 | tighten | Decision quality = value of the option taken minus the expected value of the passing options at that moment (Cervone "shot satisfaction"), computed only when all passing options are mapped (>= 8 players); per player with n and 95% interval. (Shall) | 100% of values carry an interval; values with n < 100 decisions are descriptive; on 100 decisions rated by Aldemir the sign agrees in >= 75% (initial value, to calibrate). (%) | quality_review, team_data_scientist |  |
| R-VL-06 | tighten | Gravity = displacement of defenders from their expected (ghost) position given the offensive configuration (N-DF-10), not raw distance. (Shall) | ghost model passes its own validation first. (%) | team_data_scientist |  |
| R-VL-07 | tighten | Matchup points created and allowed are shrunk toward position-group priors with possessions matched as weight; shown only above the R-VA-05 minimum count. (Shall) | values without a 95% interval: 0 (count) | team_data_scientist |  |
| R-VL-09 | merge-into R-VL-02 | Merge into R-VL-02 (same bookkeeping identity); keep the named roles (scorer, assister, hockey-assist passer, screener, gravity player) as R-VL-02 fields. (Shall) | As R-VL-02. (points) | quality_review |  |
| R-VL-10 | tighten | Value of a drawn foul: free-throw points plus the change in the next possessions (bonus, foul trouble) (Shall) | Recomputes from events; mean drawn-foul value per type calibrated within ±0.05 points per decile as R-VL-01. (count) | quality_review |  |
| R-VL-12 | tighten | Every player-level estimate states its prior (population, position group), the effective sample size and the shrinkage factor. (Shall) | three fields present on every row of player-level outputs. (RMSE) | team_data_scientist |  |
| R-VL-13 | loosen | The neural sequence model is optional (Should stays); it may be trained on our own tracks only; pre-training on research-only public tracking makes the model research-only (R-RG-04). (Should) | model card states training data licence. (log loss) | team_data_scientist |  |

### R-CH Chemistry and coaches

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-CH-01 | tighten | Lineup and pair effects: ridge (RAPM) with informed priors from box and PBP data, penalty chosen by cross-validation over whole games, accuracy reported on held-out games against a prior-only baseline [L10]. (Shall) | held-out RMSE of stint margin per 100 possessions beats the prior-only model. (%; RMSE) | team_data_scientist |  |
| R-CH-03 | tighten | Movement coordination per pair: lag and relative phase of movements; cut timing after a screen (Shall) | Recomputes from tracks; cut timing after a screen within ±80 ms of hand timing on 100 cuts in >= 80% (initial value, to calibrate). (count) | quality_review |  |
| R-CH-04 | tighten | Screener–handler timing on ball screens and handoffs (Shall) | Within ±80 ms in >= 80% of 200 screens (share initial value, to calibrate). (ms) | quality_review |  |
| R-CH-06 | tighten | Coach record: first set after each timeout and its value; substitution patterns; half-time adjustment = change from the last 600 s of the first half to the first 300 s of the second half in set mix, coverage mix, pace and PPP, with n possessions. Timeout timing vs runs moves to R-CC-02. (Shall) | Computed for 100% of processed games; first ATO set label agrees with gold >= 85% (initial value, to calibrate); marked descriptive when n is below the R-VA-05 rule. (count) | quality_review, espn_analyst |  |
| R-CH-08 | tighten | Runs and momentum use the R-MD-17 run definitions and are tested against the state model under a pre-registered hypothesis (beliefs register new-4, new-5, new-7) with a registered identification design (N-HY-01). (Should) | Test registered under R-HY-01 before results are read; design field filled. (count) | espn_analyst, team_data_scientist | K05 |

### R-CC Coach cards

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-CC-02 | tighten | Timeout behaviour: timeouts vs opponent runs (R-MD-17 register definition): lag from the run reaching its threshold to the timeout (game-clock s and possessions), whether a media timeout was due within 60 s, timeouts left at the under-4 media timeout and at the end of each half. (Shall) | Recomputes from timeouts, media slots and score_events for 100% of games (0 differences). (count) | espn_analyst | K05 |
| R-CC-03 | tighten | Reactions measured from data: player pulled at the first dead ball after his turnover or defensive breakdown, and within 60 s of game clock (both windows stored; 30 s kept as a sensitivity view); technical fouls; scheme or lineup change after an opponent run; every pull rate compared with the player's substitution hazard in matched moments without the trigger (same period, minutes into the stint, foul count). (Shall) | Recomputes from substitutions (0 differences with PBP times); report gives observed vs expected pull rate with 95% interval per window. (count) | quality_review, espn_analyst, team_data_scientist | K21 |

### R-GU Game understanding

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-GU-01 | loosen | Belief state starts after R-VL-01. (Shall) | Same gating. (count) | data_engineer | K20 |
| R-GU-02 | tighten | Surprise per event: how unlikely the belief state found what happened (negative log probability), the measurable version of prediction error (Shall) | In each of 10 probability bins, observed frequency within ±5 points of the bin mean (initial value, to calibrate). (pp) | quality_review |  |
| R-GU-03 | loosen | From the third processed game on (not a data dependency for games 1-2), coach quiz at random paused moments ("who guards X, which set, which defense, what happens next") scored against Aldemir's answers. (Shall) | Score per question type per game and model version; pass mark per type set by Aldemir (needs decision), e.g. "who guards X" >= 90% to match R-DF-01. (%) | quality_review, data_engineer |  |
| R-GU-04 | tighten | Narration uses only vocabulary-map terms and broadcast phrases (N-MD-11); every numeric claim carries n; unmeasured words ('momentum', 'wanted it more', 'clutch gene') are banned unless defined in config. (Shall) | Automated lint passes on 100% of sentences; analyst or coach review of 50 sentences ≥ 90% 'acceptable'. (count) | espn_analyst |  |
| R-GU-05 | tighten | Anticipation: predicted pass target 1 s before release, scored against chance (Should) | Accuracy above the nearest-teammate baseline with a game-resampled 95% interval excluding 0. (pp) | quality_review |  |

### R-SR State record

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-SR-03 | split | R-SR-03a Shall: personal fouls per player and team fouls per half (second-half count continues through extra periods, Rule 5-9.4). R-SR-03b Shall: foul type from the same list as R-RF-03. R-SR-03c Shall: bonus state (none, one-and-one from the 7th, double from the 10th) and fouls to give. Exception text: "Player-control fouls, and team-control fouls that are not loose-ball fouls, award no free throws; loose-ball team-control fouls are bonus-eligible (8-2.1, 10-1 Penalty c)." (mixed) | Counts equal the box score per half; bonus state equals PBP at 100% of fouls. (count) | quality_review | K27 |
| R-SR-04 | rewrite | Timeout and review state: game media format; timeouts left per team by length (30 and 60 s in the media format; 75 and 30 s otherwise), caller of each; actual media slot of each media timeout per Rule 5-14.10 (16/12/8/4 or 15/10/5 marks; 30-s pre-mark conversion; first second-half team timeout takes media length; A.R. 5-33); coach's challenge left (Rule 11-4); monitor review in progress. (Shall) | Matches the PBP timeout list (100%); media slots match PBP media timeouts in >= 95% (initial value, to calibrate); the timeout and media invariants (R-IV-10, N-IV-12) pass on 100% of pilot games. (count) | quality_review, espn_analyst, rules_layer |  |
| R-SR-05 | tighten | Possession state: team, possession ID, chance ID, phase (half court, transition, throw-in, free throw, jump ball, timeout, review), seconds since change of control, alternating-possession arrow. (with phase values aligned to R-TR-09 (primary, early, half-court) plus throw-in, free throw, jump ball, timeout, review, dead.) (Shall) | Possession counts within ±1 between teams per half (R-IV-15); phase agrees with R-TR-09 on transition seconds. (count) | quality_review |  |
| R-SR-06 | tighten | Ball state: control state (team A ball, team B ball, contested, in flight, throw-in pending, dead), ball handler, ball x, y and height (m), ball_visible, ring_contact on each try; stored as dimensions of state_segments (per-frame values are an as-of view). (Shall) | Tests of R-MD-02 (control state), R-BL-02 (handler), R-BL-01 (position) and R-MB-07 (ring contact); view equals segments on 100% of frames. (%) | quality_review, data_engineer | K09 |
| R-SR-07 | rewrite | Personnel: the 10 players on court with identity confidence, x, y (m), speed (m/s), acceleration (m/s², after the K03 gate); stint length (s); positions of the two or three officials (Rule 2-1.1.a; crew size from game_officials); stored in player_positions, lineup_stints and official_positions (as-of views of state_segments). (Shall) | Identity as R-ID-01; positions as R-CG-03; official position rows per visible second equal crew size. (%) | quality_review, espn_analyst, rules_layer |  |
| R-SR-08 | rewrite | Restart state: dead-ball reason, restart type and spot (throw-in under the basket or at the 28-foot mark per Rule 7-3.2.b as changed in 2025-26, sideline, backcourt; free throws; held ball by arrow). (with "the 8.53 m mark (28 ft)".) (Shall) | Order matches PBP 100%; spot class as R-DT-19. (count) | quality_review | K26 |
| R-SR-09 | rewrite | Free-throw state machine as written, with award types per the 2026-27 rules: shooting 2 or 3, and-one 1, one-and-one, double bonus 2, Class A technical 2, Class B technical 1, administrative technical 1 (2 for 10-2.6 and 10-2.7), Flagrant 1 and 2: 2 plus ball. (Shall) | 100% of PBP free throws matched; "free throw coming" prediction precision and recall >= 95% (initial value, to calibrate). (count; %) | quality_review |  |
| R-SR-11 | tighten | Game situation every second as named flags with thresholds in config: two-for-one window (33-45 s, proposal), last-shot hold, foul-to-extend (trailing, <= 60 s, margin 1-9), foul-up-3 cell (game clock x shot clock), shot clock off, fouls to give per team, bonus status of both teams, foul-trouble flags read from the R-MD-16 table. (Shall) | Flags recompute from state (0 differences); constants live in config (lint: 0 hard-coded); counts per flag per game reported. (count) | quality_review, espn_analyst | K10 |

### R-IV Invariants

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-IV-01 | rewrite | Exactly 5 players per team on court during live play; each player on one team; jersey numbers unique per team. (rule references 1-1.1, 3-2.1, 3-2.2, 10-2.6, 1-22.7.b.2, 1-22.7.b.5, 10-2.3.a, 3-6; exception: a team may continue with fewer than five (3-2.2).) (Shall) | Every break goes to identity review; 0 unreviewed breaks per game. (count) | quality_review |  |
| R-IV-02 | rewrite | Two or three officials on court (Rule 2-1.1.a); three expected in D-I; two-official games set in the games registry; a crew-size change mid-game is logged. (Shall) | Invariant reads constants.officials_on_court_allowed = [2, 3]; 0 unreviewed breaks per game. (count) | quality_review, espn_analyst, rules_layer |  |
| R-IV-03 | rewrite | Substitutions only during dead balls; a player with 5 fouls never re-enters. ("5 fouls" means personal plus Class A technical fouls; also three Flagrant 1 fouls disqualify (4-12.1). Rules 3-6.1, 3-6.2, 4-12.1, 4-12.5, 2-8.3, 4-14.2.e, 10-1 Penalty.) (Shall) | 0 unreviewed breaks. (count) | quality_review |  |
| R-IV-04 | rewrite | Each score change is +1, +2 or +3; a free throw is +1; final scoreboard = play-by-play sum = box score. (add own-basket credit (2 points to the opponent, no player credit, 5-1.4.a); rules 5-1.2-5-1.4, 5-1.13, 9-15 Penalty, 2-9.13, 2-9.17.) (Shall) | 0 unreviewed breaks. (count) | quality_review |  |
| R-IV-05 | tighten | Game clock never goes up within a period except as a logged correction (Rule 5-12) with old and new values and the affected window. (Shall) | Every upward step has a state_corrections row (Louisville 4:06 -> 4:07 is one); 0 unlogged upward steps. (count) | data_engineer |  |
| R-IV-08 | rewrite | After a made field goal or a made last free throw, the other team gets the ball; after a defensive rebound or turnover, control switches; jump ball only at the start of the game and extra periods, later held balls follow the arrow, which flips after each use. (with: "made last free throw for a personal foul"; "the second half starts with an arrow throw-in at the division line (6-3.6)"; rules 6-2.1, 6-3.2, 6-3.4, 6-3.6, 6-4.1, 7-3.1.c, 7-4.6.a, 8-6.1, 8-7, 4-9.3.) (Shall) | 0 unreviewed breaks. (count) | quality_review |  |
| R-IV-09 | rewrite | Team fouls never go down within a half except logged corrections; reset only at the start of the second half (extra periods continue it, 5-9.4); bonus at the 7th, double bonus at the 10th. Rules 8-2.1-8-2.3, 10-1 Penalty c, d.3, 2-9.11, 5-9.4, 5-7.6; A.R. 11-32. (Shall) | 0 unreviewed breaks. (count) | quality_review |  |
| R-IV-10 | rewrite | Timeouts left never go below 0 and never go up except at the start of an extra period; allotment per media format: >= 3 media timeouts per half -> three 30-s and one 60-s per team per game, at most two 30-s carried into the second half, one extra 30-s per extra period (5-14.10.a, b, f); fewer than 3 media timeouts or none -> four 75-s and two 30-s, one extra 75-s per extra period (5-14.8, 5-14.9). (Shall) absorbs new-IV-12 | 0 unreviewed breaks; passes on 100% of pilot games. (count) | quality_review, espn_analyst, inbox007_or_invariants |  |
| R-IV-11 | rewrite | During free throws the game clock does not run; at most 6 players on the lane (4 opponents, 2 teammates of the shooter); the lowest lane spaces stay empty; the number of attempts matches the award. (rules 8-4.4, 8-4.4.a, 8-4.5, 8-4.8, 8-5.1, 8-5.2, 9-1.1, 5-10.2.c, 10-1 Penalty b-e.) (Shall) | 0 unreviewed breaks. (count) | quality_review |  |
| R-IV-13 | rewrite | Physics checks on filtered tracks from the shared config key physics.*: hard speed limit 10.0 m/s over >= 0.3 s windows (break); soft speed limit 9.0 m/s (review flag for identity swaps); \|acceleration\| <= 12 m/s² over >= 0.5 s windows (flag only), tightened to 8.0 m/s² once the measured acceleration sigma is <= 1.0 m/s²; ball handler within 1.5 m of the ball while in control; one ball position per frame; every player and ball position inside the court + 1.0 m and ball height within its physical range. Breaks are flags, not quarantines, until calibrated. (Shall) absorbs new-IV-34 | False-break rate <= 1 per 1,000 player-seconds on hand-checked clips; 0 unreviewed breaks per game; one key read by R-DQ-02, R-EN-03 and R-DT-08 (unit test). (count) | quality_review, data_engineer, team_data_scientist, inbox007_or_invariants | K01 |
| R-IV-14 | tighten | 10-second backcourt count; no return to the backcourt with team control. (consider Shall once frontcourt status (N-MD-06) is stored.) (Should) | 0 unreviewed breaks. (count) | quality_review |  |

### R-SB Scoreboard and scorer errors

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-SB-01 | tighten | Detect these discrepancy types: (a) score change with no make seen (camera on court); (b) make seen with no score change inside the lag window; (c) wrong value (CV 3, board +2); (d) wrong team; (e) double count; (f) late update beyond the window; (g) game clock not started or stopped; (h) shot clock not reset or reset wrong; (i) later correction (board changes during a review or timeout); (j) broadcast scorebug lagging the arena board. (type (j) scorebug lag measured by R-SB-03.) (Shall) | 100% of seeded types (a)-(i) detected; type (j) lag distribution reported per game; false-flag rate on a clean game <= 1 per half (initial value, to calibrate). (%) | quality_review |  |
| R-SB-03 | tighten | Measure the scorebug lag after made baskets for every game and every scorebug field (distribution in s); the make-detection window starts at 4.0 s (measured lag 1.50-2.60 s, n = 10) and is re-set after each game to the per-field 99th percentile + 1.0 s, never below 3.0 s and never above 15 s. (Shall) | >= 99% of matched makes fall inside the window; 0 makes missed for window reasons on the pilot games; window and lag quantiles per field in the run record. (count) | data_engineer, espn_analyst, team_data_scientist | K02 |
| R-SB-04 | tighten | Per-game counts of each discrepancy class in the run record; a game with more than 3 unresolved flags stays out of engine training until reviewed. (Shall) | 0 games with > 3 unresolved flags in any training manifest. (count) | quality_review |  |

### R-MB Made-basket detection

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-MB-01 | tighten | Confirmed make = scoreboard or play-by-play AND at least one vision cue; vision-only make (blind pass) = both vision cues; anything else is flagged. Each make stores every cue with its frame and confidence. (Shall) | 100% of makes store every cue with frame and confidence; fused results meet R-MB-02/03/04 on gold-v1 and the 3 test games. (%) | quality_review |  |
| R-MB-04 | rewrite | Make frame within +/- 2 frames of the hand label at the file's frame rate (+/- 0.067 s at 29.97 fps; +/- 0.033 s at 59.94 fps) on >= 95% of makes, and within +/- 1 frame on >= 80% (stretch, initial value); 2 vs 3 agreement with PBP >= 99%. (Shall) | Measured on all makes of game 1 and game 2 against a hand label that is itself +/- 1 frame. (%) | quality_review, data_engineer, espn_analyst, team_data_scientist | K07 |

### R-CX Context features

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-CX-02 | tighten | Feature weights are learned per layer; the prior for each causal class is written in the model spec (fixed external features: normal prior centred on 0 with SD set in config, initial value, to calibrate). (Shall) | 100% of model specs list the prior per feature class; 0 equal-weight defaults. (count) | quality_review |  |
| R-CX-04 | tighten | Venue: home, away or neutral, arena, attendance, share of capacity, altitude (capacity and altitude read from the R-FD-11 arena registry.) (Shall) | 100% of games filled or flagged. (count) | quality_review |  |
| R-CX-05 | tighten | Travel: great-circle distance, time zones crossed, travel mode, days of rest, games in the last 7 and 14 days (Shall) | Distance within 1 km of haversine recomputation; rest days and games in 7/14 days equal schedule recomputation (initial tolerance, to calibrate). (km) | quality_review |  |
| R-CX-14 | tighten | Campus-to-venue distance for both teams, their difference, and a "proximity home" flag at neutral sites (the closer team, when the difference exceeds 300 km, proposal) (distances themselves come from R-MD-14 (campus-to-venue for both teams); this row adds the difference and the proximity flag (300 km, proposal).) (Shall) | Distances within 1 km of recomputation; flag equals rule on 100% of neutral-site games. (km) | quality_review |  |
| R-CX-15 | merge-into R-MD-14 | Merge into R-MD-14 (game context stamp lists the same fields). (Shall) | As R-MD-14. (count) | quality_review |  |
| R-CX-16 | tighten | Altitude difference between each team's campus and the venue (Should) | Equals venue altitude minus campus altitude from the arena registry within 1 m. (m) | quality_review |  |
| R-CX-18 | tighten | Pre-game card adds a T−900 s snapshot with announced starters and availability updates when public. (Shall) | Snapshot row exists for 100% of games, or a 'not public' flag. (count) | espn_analyst |  |
| R-CX-19 | merge-into R-CC-05 | Merge into R-CC-05 (head-to-head history). (Should) | As R-CC-05. (count) | quality_review |  |

### R-PL Physical load

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-PL-01 | loosen | Distance per minute and per possession by the R-PL-11 primary bands; the walk/jog/run/sprint 2.0/4.0/5.5 m/s placeholder is kept only as a view on R-PL-09 bins. (Should) | Total distance on a synthetic track within 3% (proposal). (%) | quality_review, team_data_scientist |  |
| R-PL-02 | merge-into R-PL-12 | Superseded by R-PL-12 (+/- 2.0 and +/- 3.0 m/s², gated); the 2.5 m/s² threshold is kept as a view. (Shall) | As R-PL-12. (count) | quality_review | K03 |
| R-PL-03 | tighten | Within-game decline of top speed (95th percentile, m/s) and acceleration (after the K03 gate) by period and by continuous minutes on the floor, estimated within player with possession type (transition, half-court, dead) and score state as covariates, beside the raw decline. (Shall) | Every decline estimate carries a 95% interval; >= 5 min of floor time per period; covariate model reported beside the raw decline. (%) | quality_review, team_data_scientist | K03 |
| R-PL-04 | tighten | Recovery after timeouts, media timeouts and halftime = % change in 95th-percentile speed and in high-speed distance per minute in the 120 s after the stoppage vs the 120 s before (windows initial values, to calibrate). (Shall) | Recomputes from PL-09 storage; every value carries n and interval. (count) | quality_review |  |
| R-PL-05 | tighten | Coverage-corrected load: every load number states the share (%) of the player's floor time observed on the main camera; the coverage threshold is one config key shared with R-PL-14 (default 0.70). (Shall) | 0 load rows without coverage %; 0 rows under the shared threshold unflagged. (count) | quality_review, data_engineer | K13 |
| R-PL-06 | tighten | Season load trend per player linked to availability (Should) | Trend per player with interval and n games; linked availability rows present for 100% of games. (count) | quality_review |  |
| R-PL-07 | loosen | Shot physics (release height, arc and entry angle in 3-D, release point vs the defender's hand) is research-only until R-CG-11 passes +/- 0.05 m; release time (catch to release) moves to R-EV-07 as a Shall field. (Should) | After R-CG-11: arc and entry angle within 3 degrees on >= 90% of 100 shots (initial value, to calibrate); release time within +/- 0.05 s on >= 90% of 100 shots. (s) | quality_review, team_data_scientist |  |
| R-PL-08 | tighten | Free-throw routine time and arc consistency, and their shift with crowd and game state (Should) | Routine time within ±0.2 s of hand timing on 50 free throws (initial value, to calibrate). (count) | quality_review |  |
| R-PL-12 | tighten | Acceleration and deceleration bands +/- 2.0 and +/- 3.0 m/s², gated separately, computed over >= 0.5 s windows with propagated sigma; band counts reported only where the acceleration sigma is <= 0.5 m/s² (else "unresolved", counted); nothing above 4 m/s² reported; jerk and PlayerLoad not reported. (Shall) | Resolvable share of player-time reported per game (%); 0 band counts from unresolved segments. (m/s; m/s²; count) | data_engineer, quality_review | K03 |
| R-PL-14 | tighten | Stints with less on-court time detected than the shared coverage key (default 70%, same key as R-PL-05) are left out of load summaries. (Shall) | 0 summaries include stints below the key. (count) | quality_review | K13 |
| R-PL-16 | tighten | Relative speed view against each player's match reference speed (median of his top-3 game peaks), stored for research; provisional until ≥ 5 games with ≥ 70% coverage (Should) | Reference speed CV across games <= 5% (initial value, to calibrate) for players with >= 5 games at >= 70% coverage. (%) | quality_review |  |

### R-CO Cognition

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-CO-01 | tighten | Decision latency: catch to first action (pass, shot, drive), by pressure (nearest-defender distance band) and shot clock (Shall) | Within ±80 ms of hand timing in >= 80% of 200 catches (share initial value, to calibrate); frame-rate uncertainty from R-CO-06 reported. (ms) | quality_review |  |
| R-CO-02 | rewrite | Defensive reaction time = pass release or cut start to the defender's movement onset, detected by change-point on velocity direction and magnitude (no acceleration-threshold onset), stored with its uncertainty (>= +/- 1 frame plus filter delay, expected 0.10-0.15 s); per-player values are distributions with n >= 50 events; single events are never shown as a player's reaction time. (Shall) | Onset within +/- 0.10 s of hand labels on >= 80% of 100 labelled reactions on game 1; uncertainty column on 100% of rows. (ms) | quality_review, data_engineer, team_data_scientist | K03, K16 |
| R-CO-03 | tighten | Anticipation: defender onsets before the pass release (negative latency), and their outcomes (Shall) | Recomputes from R-CO-02; pre-moved onsets agree with gold in >= 80% of 100 cases (initial value, to calibrate). (count) | quality_review |  |
| R-CO-04 | rewrite | Pressure performance: decision and shot quality in three separate slices: contest <= 1.2 m, shot clock <= 5 s, and the single config clutch flag (R-MD-13a); each shrunk toward the player's own non-pressure performance and the population pressure effect, with n. (Shall) | One clutch constant in config referenced by every module (lint: 0 second definitions); interval and n on every number. (count) | quality_review, espn_analyst, team_data_scientist | K06, K22 |
| R-CO-08 | rewrite | Communication proxies: clean vs late switches, two defenders on one attacker (clean vs late switches move to R-CH-05; "two defenders on one attacker" stays here) (Should) | >= 85% (proposal). (%) | quality_review |  |

### R-EN Engineering

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-EN-01 | tighten | One versioned schema per table, units in column names; all specs in one YAML dialect generated from one source, with semver per table; a validator checks names, PK, FK targets, units, ranges, licence class, as-of rule and requirement IDs. (Shall) absorbs new-EN-E5 | 104 of 104 specs pass in CI; a spec citing an unknown requirement ID fails; 0 specs in the second dialect. (count) | data_engineer |  |
| R-EN-02 | tighten | Reproducible runs, determinism stated per stage: bitwise for CPU transforms; GPU inference within declared tolerances (positions +/- 0.01 m, scores +/- 1e-4). (Shall) | Re-run of game 1: 0 differences in CPU stages; GPU stages within tolerance. (count) | quality_review, data_engineer |  |
| R-EN-03 | tighten | Automatic checks per stage: possessions vs PBP, score vs official, no player in two places, no player faster than the hard speed limit of the shared physics key (R-IV-13). (Shall) | 0 unreviewed failures per stage; the speed check reads physics.speed_hard_mps (unit test). (count) | team_data_scientist | K01 |
| R-EN-05 | tighten | Chunks are (video_id, keyframe-aligned frame range of about 60 s); outputs written atomically (temp + rename) with a completion marker; a chunk with a marker is never recomputed. (Shall) | Kill test: 20 random interruptions on game 1 give byte-identical outputs to an uninterrupted run. (count) | data_engineer |  |
| R-EN-07 | rewrite | Processed outputs are Parquet under processed/<table>/stage=<s>/key=<output_key>/game_id=<id>/pass=<p>/ with _manifest.json (rows, sha256, schema_version, input keys) and a per-game _current pointer; versions side by side. (Shall) absorbs new-EN-E4 | Manifest on 100% of partitions; current pointer resolves for every processed table and game; a change to one stage writes new keys only for that stage and its descendants (test change). (count) | data_engineer |  |

### R-CD Coordination

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-CD-03 | tighten | docs/user_inputs.md keeps Aldemir's inputs verbatim, append-only (Shall) | Git history shows no deleted or changed lines in docs/user_inputs.md (diff contains only additions). (count) | quality_review |  |

### R-PR Prediction

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-PR-05 | split | R-PR-05a Shall: win probabilities have 10-bin ECE <= 0.03 (proposal). R-PR-05b Shall: margin and total distributions have a PIT histogram consistent with uniform and CRPS reported against the R-PR-03 baselines. (mixed) | a: ECE <= 0.03 on walk-forward and held-out games; b: PIT chi-square test p >= 0.05 (initial value, to calibrate) and CRPS no worse than the ratings baseline. (ECE; CRPS) | quality_review |  |
| R-PR-06 | tighten | 5-minute windows scored against a pace-scaled random-walk baseline (window margin variance = game variance × 5/40) (Shall) | Engine log loss lower than the baseline on held-out windows, game-resampled 95% interval of the difference excluding 0. (log loss) | quality_review |  |
| R-PR-07 | tighten | Matchup layer: distributions of player points, rebounds, assists (Shall) | Over/under log loss vs de-vigged prop lines reported with n and interval; no edge claim below R-PR-08 sample rule. (log loss) | quality_review |  |
| R-PR-11 | tighten | Live in-game win probability refreshed within 10 s (95th percentile) of each scoreboard change; calibrated overall and for the last 240 s separately; no swing > 0.25 without a score, turnover or foul event; never published before R-PR-09 passes. (Should) | ECE <= 0.03 overall and <= 0.05 in the last 240 s on held-out games; 95th-percentile latency <= 10 s; sanity-rule violations = 0. (s; ECE) | quality_review, espn_analyst | K06 |

### R-PE Possession engine

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-PE-04 | tighten | Time model: per-second hazard of the chance ending, by start type, shot clock and game state (Shall) | Simulated possessions per game within ±1.5 of actual on average; two-sample KS p >= 0.05 on possession lengths (initial value, to calibrate). (count; p) | quality_review |  |
| R-PE-05 | tighten | Free-throw model: per shooter, shrunk toward position group (Shall) | Predicted vs actual make rate within ±1 point per decile on held-out free throws (as R-PE-02). (pp) | quality_review |  |
| R-PE-07 | tighten | End-game policies fitted from PBP plus scorebug shot clock and stored per decision cell (game clock x shot clock x margin): fouling when trailing, fouling up 3, two-for-one, last-shot holds, timeout use including the head coach's live-ball timeout in the last 2:00 (5-11.3, 5-14.1.a exception). (Shall) | In >= 90% of cells with n >= 30 the simulated rate lies inside the game-resampled 95% interval of the D-I rate (initial value, to calibrate); cells with n < 30 pooled with a stated prior. (%) | quality_review, espn_analyst |  |
| R-PE-11 | tighten | Video features enter the engine only after a walk-forward comparison on the same held-out games shows the engine with video features beats it without (log loss and CRPS, R-PE-10 rule). (Shall) | engine code runs at L3 and L4 unchanged: pass (pass/fail) | team_data_scientist |  |

### R-MK Markets

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-MK-03 | tighten | In-game prediction-market prices are joined to game state through clock_map.est_utc; a join is made only when the UTC error is ≤ 30 s. (Shall) | ≥ 90% of in-game 1-minute prices of an MSU game with PBP wall clock joined. (%) | data_engineer |  |
| R-MK-10 | merge-into R-MK-02 | Merge with R-MK-02; the approval note "(P0m approved; job B of prompt 002)" moves to the decision log. (Shall) | As R-MK-02. (%) | quality_review |  |
| R-MK-13 | tighten | Every response written raw (gzip, as received) with one manifest line before parsing, recording sha256_received (before any redaction) and sha256 of the stored body; the raw root is guarded as private. RESOLVED in code 2026-10-18 (raw_store.py, models.py ManifestEntry.sha256_received). (Shall) resolved | Unit test: redacted body gives two different hashes, both in the manifest; writing raw under the repo raises (passes). (pass/fail) | data_engineer |  |
| R-MK-22 | split | R-MK-22a Shall: cross-source line differences > 0.5 points flagged xsrc_gt_0p5. R-MK-22b Should: tiered rules XS-1..XS-4 run with thresholds from config until calibrated. (mixed) | a: 100% of seeded > 0.5 differences flagged; b: XS rules run on every pull. (%) | quality_review |  |
| R-MK-27 | rewrite | Rows de-duplicated on (game, source_event_id, source, book, market, phase, snapshot label, side, team/player, line, snapshot time); CBBD reported open/close of finished games keyed on the scheduled tip so re-pulls are idempotent; the store skips keys already present in the partition (idempotent across runs). RESOLVED in code 2026-10-18 (models.py dedup_key, sources/cbbd.py, store.py; tests/markets/test_engineer_review_fixes.py). (Shall) absorbs new-MK-E1, new-MK-E2; resolved | Two unmatched games with equal totals in one fetch both survive; re-pulling a finished season adds 0 rows; ingesting the same raw twice adds 0 rows (regression tests pass). (count) | data_engineer |  |
| R-MK-31 | tighten | schema_version also written to Parquet key-value metadata; readers refuse unknown major versions. (Should) | Reader test with a future version fails loudly. (count) | data_engineer |  |
| R-MK-32 | tighten | The default fair-probability method is chosen by an NCAAB log-loss and Brier comparison on 2021-22 to 2025-26 moneylines before any result is published. (Should) | Comparison table on file before any result is published; chosen method has the lowest log loss (ties by Brier). (log loss; Brier) | quality_review |  |
| R-MK-33 | tighten | Alert when weekly completeness < 95% two weeks running, an MSU game lacks a close from any enabled source, or a source's unmatched share > 2%. (Should) | Each of the three conditions raises an alert on a seeded case. (count) | quality_review |  |

### R-HR Human review

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-HR-02 | tighten | Review item: clip with event-type windows from config (shot 3 s before / 2 s after, ball screen 4 / 3, transition from secure catch to first shot, foul 3 / 3, default 3 / 3; reviewer can extend), top-down view beside it, model guess prefilled, one-click confirm or correct. (Shall) | Config windows used for 100% of items; median time per item <= 20 s (initial value, to calibrate). (s) | quality_review, espn_analyst |  |

### R-VZ Visualization

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-VZ-06 | split | Split into one Should per view, each with a render test: matchup board, heat maps, passing network, layered win probability with run shading, filters, clip export, foul tracker, timeouts left, shot chart by sector and ring, lineup plus-minus with n. (mixed) | Each view renders from the state tables of a pilot game; every number linked to frames (R-VZ-02). (count) | quality_review, espn_analyst |  |
| R-VZ-07 | tighten | One visual standard: metric labels only, one palette, text contrast >= 4.5:1 (WCAG 2.1 AA), layout usable at 375 px width. (Should) | Style check passes on every view. (count) | quality_review |  |

### R-CS Compute and storage

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-CS-04 | tighten | Full frame rate on main-wide live play; other shot types get only shot-type classification and OCR at ≤ 5 fps; replay frames get shot-type only. (Shall) | Frame-stage mask present for 100% of frames; accuracy loss of any sampling measured before adoption. (pp) | data_engineer |  |
| R-CS-07 | tighten | Training checkpoints saved to Drive at least every 15 min (Shall) | Largest gap between consecutive checkpoint timestamps in each training run <= 15 min. (min) | quality_review |  |
| R-CS-09 | rewrite | Storage plan per season from measured sizes: 1.82-1.97 GB per 1080p 29.97 fps condensed replay (2.81-2.92 Mb/s, measured) and processed GB per game per version measured on game 1; Drive use stays under 80% of plan capacity; the 4K estimates move to the plan file. (Shall) | Measured size logged for 100% of files; plan updated after game 1; Drive use < 80%. (count; %) | quality_review, data_engineer |  |

### R-VA Validation

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-VA-02 | rewrite | Court mapping error reported in metres. (Shall) | 0 reports in other units. (count) | quality_review |  |
| R-VA-05 | tighten | The minimum-count rule uses game-clustered standard errors, and for player-level splits the shrunk posterior's interval; the 1.1 points-per-chance spread is replaced by the value measured on our data after the first 5 games. (Shall) | reported numbers without n or descriptive flag: 0 (count) | team_data_scientist |  |
| R-VA-09 | tighten | Regression check: each model version re-runs every gold test of its phase and earlier phases (with tolerance: a drop of more than 1 point (initial value, to calibrate) or below the target blocks the release.) (Shall) | 0 releases with a drop above tolerance. (count) | quality_review |  |

### R-PT Pitch

| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |
| --- | --- | --- | --- | --- | --- |
| R-PT-01 | tighten | Pitch package: walk-forward results of engine levels L1-L3 against closing lines (CLV, log loss, intervals, n), plus one fully processed MSU game showing what video adds, including its half-time packet and post-game notes (N-VZ-01, N-VZ-02), every number linked to frames and reconciling with the official box. (Shall) | Sign-off on file; 100% of counting stats equal the official box. (count) | quality_review, espn_analyst |  |

### Kept as written

| Family | Kept IDs |
| --- | --- |
| R-RR | 04, 05, 06, 07, 08, 09 |
| R-DQ | 03, 05, 07, 09, 10 |
| R-DS | 01, 02, 06, 07, 08, 09, 11, 12, 14, 15 |
| R-RG | 01, 03, 04, 05, 06, 07, 08, 09, 10 |
| R-FD | 04, 07, 10, 12 |
| R-PC | 01, 02, 04, 13, 14, 15 |
| R-MD | 03, 04, 05, 06, 09, 10, 12, 14, 15, 19, 20 |
| R-ID | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14 |
| R-VI | 03, 04, 05, 07, 08, 09, 10, 11, 12, 14, 15 |
| R-CG | 02, 03, 05, 06, 09, 10, 11 |
| R-DT | 01, 02, 03, 04, 05, 06, 09, 10, 11, 13, 16, 17, 18 |
| R-BL | 01, 02, 03, 06, 07, 08 |
| R-GT | 01, 02, 03, 04, 05 |
| R-SY | 03, 06, 07, 09, 10 |
| R-TR | 02, 03, 04, 07, 09, 15, 18, 19, 21, 22, 23, 24, 26, 27, 28 |
| R-EV | 01, 02, 04, 05, 09, 11, 12, 14 |
| R-AU | 02, 03 |
| R-RF | 01, 02, 04, 05 |
| R-ST | 01, 03, 04, 06, 07, 09, 11, 13, 14, 15, 16, 17, 18, 20, 21, 22, 24, 25, 26 |
| R-DF | 02, 05, 09, 11, 12, 13, 14, 15, 17, 18, 21 |
| R-VL | 03, 08, 11 |
| R-CH | 02, 05, 07 |
| R-CC | 01, 04, 05 |
| R-GU | 06 |
| R-SR | 01, 02, 10, 12, 13, 14, 15 |
| R-IV | 06, 07, 12, 15, 16 |
| R-SB | 02 |
| R-MB | 02, 03, 05, 06, 07 |
| R-CX | 01, 03, 06, 07, 08, 09, 10, 11, 12, 13, 17 |
| R-PL | 09, 10, 11, 13, 15, 17 |
| R-CO | 05, 06, 07 |
| R-OS | 01, 02, 03, 04, 05 |
| R-EN | 04, 06, 08 |
| R-CD | 01, 02, 04, 05 |
| R-PR | 01, 02, 03, 04, 08, 09, 10 |
| R-PE | 01, 02, 03, 06, 08, 09, 10, 12, 13 |
| R-MK | 01, 02, 04, 05, 06, 07, 08, 09, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 28, 29, 30 |
| R-HR | 01, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12 |
| R-VZ | 01, 02, 03, 04, 05 |
| R-CS | 01, 02, 03, 05, 06, 08, 10 |
| R-VA | 01, 03, 04, 06, 07, 08 |
| R-HY | 01, 02, 03, 04, 05, 06, 07 |
| R-PT | none |

Explicit keeps by the data engineer (reviewed and judged right): R-RR-02, R-RR-03, R-RR-05, R-RR-06, R-RR-08, R-RR-09, R-DQ-03, R-DQ-05, R-DQ-07, R-DQ-09, R-DQ-10, R-DS-13, R-FD-10, R-MD-02, R-MD-04, R-MD-06, R-MD-09, R-MD-12, R-MD-13, R-MD-17, R-MD-19, R-VI-09, R-DT-11, R-VI-12, R-VI-14, R-VI-15, R-VI-16, R-SY-06, R-SY-08, R-SY-10, R-TR-22, R-SR-01, R-SR-13, R-SR-15, R-PL-05, R-PL-09, R-PL-13, R-CO-06, R-EN-03, R-EN-04, R-EN-06, R-EN-08, R-MK-14, R-MK-17, R-MK-21, R-MK-25, R-HR-05, R-HR-07, R-CS-02, R-CS-05, R-VA-03, R-VA-06.

## 5. New requirements: one N-series

Columns: tier, priority (P0 first two games, P1 this season, P2 later), text, acceptance with units, where it lands, ontology leaves (`config/game_ontology.yaml`), who wants it, and the old proposal IDs merged into it. Full records with leaf names, sources and related existing IDs are in the YAML.

### N-AU

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-AU-01 | Should | P1 | Horns are detected from audio with kind (period end, shot clock, substitution/timeout, other) and onset time to 10 ms, linked to the clock state. | Recall >= 90% and onset within +/- 0.10 s on 200 labelled horns (proposal). | audio_seconds.buzzer_kind; audio_seconds.buzzer_onset_ms; audio_seconds.crowd_reaction_db | L.04.02 | gap_closures_round2, ontology_audit_inbox007 | new-AU-3, new-AU-2 |
| N-AU-02 | Should | P2 | Crowd reactions are stored per second as the excess loudness (dB) over the trailing 10-s median when >= 6 dB and not a horn or commentary peak. | Reaction seconds agree with labels on >= 80% of 200 labelled seconds (proposal); used by C.05.03 crowd-share validation. | audio_seconds.buzzer_kind; audio_seconds.buzzer_onset_ms; audio_seconds.crowd_reaction_db | L.04.02 | gap_closures_round2 | new-AU-4 |
### N-BL

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-BL-01 | Shall | P1 | Every out-of-bounds throw-in row stores the Rule 7-2 cause, the player who caused it, the touch time, the exit point (m) and whether our team-level reading agrees with the call on the floor. | Awarded team equals PBP on 100% of rows; last toucher correct on >= 90% of 200 labelled out-of-bounds plays (proposal); exit point within 0.30 m of a hand-mapped point on 50 plays; every 'simultaneous_touch' row resolves to an arrow throw-in in PBP. | restarts.oob_cause; restarts.oob_last_touch_player_id; restarts.oob_last_touch_ts_ms; restarts.oob_exit_x_fc_m; restarts.oob_exit_y_fc_m; restarts.oob_call_agrees | A.09.02 | gap_closures_round2, ontology_audit_inbox007 | new-BL-2, new-BL-1 |
### N-CC

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-CC-01 | Shall | P1 | Foul-trouble decision log: For every player entering foul trouble (R-MD-16): time of the foul, whether he sat at the next dead ball, seconds and possessions sat, re-entry time and situation, fouls committed after re-entry, net points with him on and off. | Rows for 100% of foul-trouble entries; recomputes from fouls and substitutions. | foul_trouble_decisions | K.01.09, D.05.04 | espn_analyst | new-CC-A5 |
| N-CC-02 | Shall | P1 | Timeout purpose: Each timeout carries a purpose code: stop a run, ATO set, rest, ice a free-throw shooter, end-game management, advance-situation set, injury, challenge; inferred from context with a confidence, never from audio alone. Rule type (30, 60, 75 s, media conversion) stored with it. | Every timeout has a purpose code; purpose agrees with a coach label on ≥ 80% of 100 timeouts (proposal). | timeouts.purpose, .purpose_conf | A.10.03, K.01.03 | espn_analyst | new-CC-A6 |
| N-CC-03 | Should | P2 | Bench events include bench personnel physically assisting a player near the boundary, linked to any resulting technical. | Every such technical in PBP has a bench_events row. | bench_events.event_type add bench_assist_out_of_bounds. | A.09.06 | ontology_audit_inbox007 | new-CC-1 |
| N-CC-04 | Should | P2 | When the head coach is visible on the main camera, store his floor position (m) each second and an out_of_coaching_box event for every continuous stay of >= 3.0 s outside the Rule 1-9 box, with duration (s) and maximum distance outside (m). | Position within 0.50 m median of hand-mapped points on 50 frames; in/out label agrees with labels on >= 90% of 100 clips (proposal); box geometry read from the court config (no hard-coded constant). | bench_events.x_fc_m; bench_events.y_fc_m; bench_events.in_coaching_box; bench_events.dist_outside_box_m; bench_events.duration_s | B.01.08 | gap_closures_round2, ontology_audit_inbox007, data_engineer | new-CC-5, new-CC-2 |
| N-CC-05 | Should | P2 | Each team-game stores bench personnel counts by role (head coach, assistants, trainers, managers, other staff, uniformed non-playing players) with the basis of the count. | Filled or 'unknown' for 100% of processed team-games; video-based counts within +/- 1 person of a hand count on 20 games (proposal). | team_game_context.bench_personnel_counts; team_game_context.bench_personnel_source | C.02.03 | gap_closures_round2, ontology_audit_inbox007 | new-CC-6, new-CC-3 |
| N-CC-06 | Should | P2 | Conduct gestures (complaint to an official, taunt/stand-over, pointing at an opponent, crowd incitement, celebration) by on-court players are logged from pose with player, target, time and any technical foul within 10 s. | Every PBP technical foul on a player has a linked gesture row or 'not_visible'; labels agree >= 80% on 100 clips (proposal); no face keypoints used. | bench_events.actor_on_court; bench_events.gesture_code; bench_events.target_type; bench_events.target_id; bench_events.followed_by_technical_event_id | E.11.03 | gap_closures_round2, ontology_audit_inbox007, rules_layer | new-CC-7, new-CC-4 |
### N-CD

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-CD-01 | Shall | P1 | A repository check validates the game ontology against the live requirement IDs, inbox proposals, schema tables, proposed column changes and vocabularies, and regenerates the coverage statistics. | Script exits 0 on the current repo; runs in repository tests (R-EN-08); coverage numbers in docs/data/game_ontology_coverage.md equal its output. | see docs/data/gap_closures_round2.md | M.03.09 | gap_closures_round2, ontology_audit_inbox007 | new-CD-2, new-CD-1 |
### N-CG

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-CG-01 | Shall | P0 | Court config holds every line width and mark of Rule 1 with its citation: boundary lines 0.0508 m, centre circle radius 1.83 m, lane space marks and neutral zones, coaching box, backboard face 1.22 m from the end line, backboard 1.83 m x 1.07 m, ring inner diameter 0.4572 m, 28-ft throw-in marks (8.53 m), designated-spot width 0.91 m. | Each constant present with a rule citation and verified: true; geometry unit tests reproduce each mark within 0.01 m. | Add keys to config/court_ncaa_men.yaml (line_width_m, centre_circle_radius_m, lane_space_marks_m, backboard_face_from_end_line_m, backboard_width_m, backboard_height_m, ring_inner_diameter_m, throw_in_mark_from_end_line_m, coaching_box_m). | B.01.02 | ontology_audit_inbox007, quality_review, rules_layer | new-CG-1 |
| N-CG-02 | Shall | P1 | The restricted-area membership test uses the outer edge of the arc, r <= 1.270 m (1.2192 m inner radius + 0.0508 m line), with straight segments to the backboard face at y = -0.381 m; the frontcourt test uses the near edge of the division line (y < 12.700 m in the attacked-rim frame). | Unit tests: feet at r = 1.25 m return inside the restricted area; a foot at y = 12.71 m returns backcourt. | config/vocab/court_constants_proposed.yaml; src/msu_alpha/geometry.py | B.01.07, B.01.04, A.06.06 | rules_layer | new-CG-2 |
### N-CH

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-CH-01 | Should | P1 | Every free-throw sequence links any timeout called between the foul and the first attempt, with the calling team (icing flag). | Recomputes from timeouts and free_throws ordering; 100% of such timeouts linked. | free_throws.preceded_by_timeout_id; free_throws.icing_team | K.01.11 | gap_closures_round2, ontology_audit_inbox007 | new-CH-2, new-CH-1 |
| N-CH-02 | Shall | P1 | Reaction catalogue: one row per detected reaction (trigger from the panel list: made basket, long rebound, live-ball turnover, bonus reached, timeout, ball screen, post entry, drive, skip pass, zone look, press, foul trouble, end of clock, scoring run, lineup composition change, hot shooter), response type (counter-substitution, scheme change, set family, tempo change, none), team, latency in s and possessions, plus for each trigger type the baseline rate of the same response in matched moments without the trigger. | Every scheme change, timeout and substitution linked to the nearest preceding trigger or "none"; every lineup composition change (R-MD-12 classes) has a response row; baseline rates per team-season with 95% intervals. | reaction_events (trigger, response, lag_s, lag_poss, baseline_rate); lineup_responses view | G.06.01, K.01.07, K.01.02, D.07.04 | team_data_scientist, espn_analyst | new-CH-S1, new-CH-A2 |
### N-CO

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-CO-01 | Should | P2 | Defensive communication gestures (assignment point, switch call, help call by arm) are logged before screens and drives as proxies of communication, and their rate per 100 ball screens is reported with the coverage outcome. | Gesture labels agree >= 75% on 200 labelled screens (proposal); rate reported only with pose coverage >= 70% of the window. | bench_events.actor_on_court; bench_events.gesture_code; bench_events.target_type; bench_events.target_id; bench_events.followed_by_technical_event_id | E.11.03 | gap_closures_round2 | new-CO-1 |
### N-CS

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-CS-01 | Shall | P0 | Each stage logs throughput (frames/s, GPU-s per 1,000 frames, rows/s) and output size (MB per table per game) into the run record. | Present for every stage of games 1-2; per-game cost model updated from them. | run_records.stage_metrics | M.05.03 | data_engineer | new-CS-E1 |
| N-CS-02 | Shall | P1 | Before any reprocessing, compute its cost from the DAG (affected stages × games × measured cost) and require sign-off above 2 compute units. | Cost estimate logged for 100% of re-runs; estimate within ±30% of actual. | run_records.estimated_units, actual_units | M.05.03 | data_engineer | new-CS-E2 |
### N-CX

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-CX-01 | Should | P1 | Each team-game carries the previous game's margin, margin against the closing spread, overtime flag and the current signed streak, as of tip. | Recomputes from games and closing lines; leakage test shows no post-tip data; 100% filled after each team's first game. | team_game_context.prev_margin; team_game_context.prev_ats_residual; team_game_context.prev_overtime; team_game_context.streak | J.03.03 | gap_closures_round2, ontology_audit_inbox007 | new-CX-15, new-CX-7 |
| N-CX-02 | Should | P1 | Each team-game carries its season game number, conference game number and season phase. | Recomputes from the schedule; 100% filled; exhibitions get no number. | team_game_context.game_num_season; team_game_context.game_num_conf; team_game_context.season_phase | J.04.03 | gap_closures_round2, ontology_audit_inbox007, data_engineer | new-CX-16, new-CX-8 |
| N-CX-03 | Should | P2 | Venues store the rim model where public and a rim-liveliness proxy: median rebound distance (m) of ring-contact misses, with its sample size, as of each game date. | rim_model filled or 'unknown' for every venue; proxy reported only with n >= 100 and a 95% interval; computed from games before the as-of date only. | venues.rim_model; venues.rim_rebound_dist_median_m; venues.rim_rebound_n | B.02.12 | gap_closures_round2, ontology_audit_inbox007 | new-CX-9, new-CX-1 |
| N-CX-04 | Should | P2 | Venues store the home student-section location (override per game) with source, and every shot and free throw is flagged when taken toward it. | Filled for 100% of processed venues; flags recompute from attacked basket per half on 100% of rows; used by the end-of-floor shooting test (C48). | games.student_section_fc; venues.student_section_fc; free_throws.facing_student_section; shots.facing_student_section | B.04.04 | gap_closures_round2, ontology_audit_inbox007 | new-CX-10, new-CX-2 |
| N-CX-05 | Should | P2 | Venue rows store court placement and the backdrop distance behind each basket (m). | Filled for every NCAA-tournament and neutral venue processed; distances within 5 m of published plans where plans exist. | venues.court_placement; venues.backdrop_distance_x_pos_m; venues.backdrop_distance_x_neg_m | B.04.05 | gap_closures_round2, ontology_audit_inbox007 | new-CX-11, new-CX-3 |
| N-CX-06 | Should | P2 | For every neutral-site game, estimate each team's crowd share with an 80% interval and measure the crowd's reaction to each team's made baskets from audio (dB), so the estimate can be validated. | Estimate with interval on 100% of neutral-site games; audio reaction measured where audio exists; rank correlation between share and reaction asymmetry reported on >= 30 games (C69). | team_game_context.crowd_share_est; team_game_context.crowd_share_ci80; team_game_context.audio_make_reaction_db | C.05.03 | gap_closures_round2, ontology_audit_inbox007 | new-CX-12, new-CX-4 |
| N-CX-07 | Should | P2 | Each team-game stores its road-trip index and days since the team's last home game. | Recomputes from games; 100% filled; leakage test passes (no future games read). | team_game_context.road_trip_index; team_game_context.days_since_last_home_game | J.01.04 | gap_closures_round2, ontology_audit_inbox007 | new-CX-13, new-CX-5 |
| N-CX-08 | Should | P2 | Each team-game stores the tip time on the team's campus clock (h) and days since its last game in another time zone. | Recomputes with zoneinfo from UTC tip and campus tz on 100% of games; daylight-saving transitions covered by unit tests. | team_game_context.tip_body_clock_h; team_game_context.days_since_tz_shift | J.01.05 | gap_closures_round2, ontology_audit_inbox007 | new-CX-14, new-CX-6 |
| N-CX-09 | Should | P2 | Storyline and fact register: Pre-game facts (streaks, milestones, records, head-to-head, coach wins) each with source, as-of time and the query that verifies it. | 0 facts without a source and as-of; every fact re-verified at T−3,600 s. | storyline_facts | J.03.04, J.06.02 | espn_analyst | new-CX-A9 |
### N-DF

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-DF-01 | Should | P1 | Per defender-second, store a denial flag (man one pass away, within 1.50 m, inside the lane at 55-95% of the ball->man segment, offset <= 0.60 m, hand in lane when visible) with the lane offset (m). | Agrees with labels on >= 80% of 300 labelled defender-seconds (proposal). | defensive_matchups.deny_posture; defensive_matchups.deny_lane_offset_m; defensive_matchups.deny_hand_in_lane | E.09.06 | gap_closures_round2, ontology_audit_inbox007 | new-DF-7, new-DF-2 |
| N-DF-02 | Shall | P1 | Each possession stores the defensive pick-up point: time, the handler's distance from the attacked rim (m), class (full, three-quarter, half court, top of key, none, frontcourt start; edges 18.71/14.00/9.50 m) and the picking-up defender, using the 1.83 m for >= 1.0 s rule. | Recomputes from tracks; class agrees with labels on >= 85% of 200 possessions (proposal); pickup_y within 1.0 m of a hand-marked point on 50 possessions. | possessions.pickup_ts_ms; possessions.pickup_y_m; possessions.pickup_class; possessions.pickup_defender_id; possessions.pickup_handler_speed_mps | G.01.04 | gap_closures_round2, ontology_audit_inbox007, espn_analyst, team_data_scientist | new-DF-8, new-DF-3 |
| N-DF-03 | Should | P1 | Per player-season, report the in-foul-trouble minus normal difference in on-ball distance (m), contest rate, contest distance (m), help share and fouls per 100 possessions, matched on half and margin band, with 95% intervals. | Interval reported for players with >= 30 defensive possessions in each state; descriptive only below that. | see docs/data/gap_closures_round2.md | G.09.03 | gap_closures_round2, ontology_audit_inbox007, espn_analyst, team_data_scientist | new-DF-10, new-DF-5 |
| N-DF-04 | Shall | P1 | Hot-shooter response: When an opponent shooter makes ≥ 2 straight field goals or ≥ 3 threes in a half (config, proposal), measure the defense on his next 5 catches: distance at catch (m), denial or top-lock rate, defender change, help kept off him; and the possessions until the change. | Recomputes from tracks; reported per trigger with n; triggers listed per game. | hot_shooter_responses | G.06.01, G.10.01 | espn_analyst | new-DF-A6 |
| N-DF-05 | Shall | P1 | Get-back onset per defender: After each change of possession, each defender's onset time (s): first moment his velocity toward his own rim exceeds 2.0 m/s; plus a "late get-back" flag when onset > 1.5 s while the ball is advanced (proposal thresholds). | Onset recomputes from tracks; flag agrees with coach labels on ≥ 80% of 100 cases; off-screen defenders marked estimated (R-DT-07). | transition_defense.onset_s, .late_flag, .estimated | G.07.01, F.01.05 | espn_analyst | new-DF-A8 |
| N-DF-06 | Shall | P1 | Ball-screen coverage outcome table: per screen, coarse and fine coverage, handler action (pull-up, drive, pass to roller, pass to perimeter, reject, reset), chance result and points; coverage effect estimated with adjustment for handler, screener, location (r, θ) and shot clock. | Table complete for 100% of detected screens; effect estimates with game-clustered 95% intervals. | screens (outcome columns) | G.02.01, F.05.03 | team_data_scientist | new-DF-S1 |
| N-DF-07 | Should | P2 | For every jump shot, store the shooter's landing point, drift (m), the nearest defender's foot distance to the landing point at landing (m) and an encroachment flag; the flag never creates a foul. | Landing point within 0.30 m of gold on 100 labelled jump shots (proposal); encroachment flag agrees with labels >= 85%; 0 fouls created from it. | shots.landing_x_m; shots.landing_y_m; shots.landing_drift_m; shots.landing_def_dist_m; shots.landing_space_encroached | E.01.08 | gap_closures_round2, ontology_audit_inbox007 | new-DF-6, new-DF-1 |
| N-DF-08 | Should | P2 | When a post is fronted, store whether weak-side lob help is present (within 2.0 m of the rim->post line or 2.5 m of the rim), the helper, and every lob over the front (apex >= 3.35 m, receiver r <= 2.0 m) with its result. | Fronted flag agrees with labels >= 85% on 100 post possessions; lob outcomes equal shot/turnover records on 100% (proposal). | passes.apex_height_m; passes.is_lob_over_front; post_touches.fronted; post_touches.lob_help_present; post_touches.lob_help_defender_id | G.03.03 | gap_closures_round2, ontology_audit_inbox007 | new-DF-9, new-DF-4 |
| N-DF-09 | Should | P2 | Pressure before and after the bonus: Within a half, compare on-ball distance (m), contest distance (m), reach-in and steal attempts per possession before and after the defending team's 7th and 10th team fouls. | Estimates with n and 95% interval per team per game; pooled per season. | team_half_pressure | G.09.03, D.05.01 | espn_analyst | new-DF-A7 |
| N-DF-10 | Should | P2 | Ghost defence: a model of where an average defender would stand given the 5 attackers and the ball, trained on population tracks we hold; per defender-second, deviation from the ghost (m) and the value change associated [L12][L2]. | Ghost model out-of-sample position error reported; deviations only where σ ≤ 0.5 m. | defensive_matchups.ghost_dev_m | G.04.01, E.07.04 | team_data_scientist | new-DF-S2 |
### N-DQ

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-DQ-01 | Shall | P0 | Invariant breaks are counted per invariant per 1,000 live-play frames (and per 100 transitions) per game and pass, with alarm thresholds in config. | Rates in every run record; a rate above its threshold blocks the game from training (R-SB-04 style). | run_requirement_results (metric = break_rate) | M.03.02, M.05.01 | data_engineer | new-DQ-E1 |
| N-DQ-02 | Shall | P0 | Game 1 (UConn) outputs are frozen as a regression fixture; any later run whose row counts change by > 1% or whose key metrics change beyond tolerance raises a review item. | Fixture exists after the first full run; regression check runs on every stage change. | results/fixtures/401856571/ (counts and metrics only; rows stay private) | M.03.07, M.04.03 | data_engineer | new-DQ-E2 |
| N-DQ-03 | Shall | P0 | Event-volume sanity: per game, CV event counts are compared with PBP-implied ranges (e.g. passes per half-court chance 1.5-6.0, dribbles per touch 0-15, screens per chance 0-4; proposals) and out-of-range games are flagged. | Ranges in config; flags in the run record for 100% of processed games. | dq_reports | M.03.03 | data_engineer | new-DQ-E3 |
| N-DQ-04 | Shall | P0 | At game end, final score, team fouls per half, player fouls and timeouts in our state record are reconciled to the official record; each disagreement becomes a correction whose source is the official record. | After reconciliation the four counts equal the official record on 100% of processed games; every applied correction links to a scoreboard flag or review. | games.official_record_reconciled | C.04.01 | gap_closures_round2 | new-DQ-2 |
| N-DQ-05 | Shall | P1 | Published-number gate: Every number that leaves the lab (pitch, staff sheet, any public output) passes an automated check: counting stats equal the official box (0 tolerance), derived stats recompute from the official box within display rounding, each number carries its definition ID, n and source, and the top 5 claims of each document are signed off by a reviewer. | 100% of published numbers pass; an audit of 50 random published numbers per month finds 0 unreconciled values. | published_numbers (doc_id, number_id, value, definition_id, n, source, reconciled, reviewer) | L.05.02, H.02.01, M.03.04 | espn_analyst | new-DQ-A2 |
| N-DQ-06 | Shall | P1 | A known-bias register lists each known source bias (listed heights, home-crew assists, blocks and steals, shot-location entry, substitution timing) with affected field, direction, measured size, correction or flag and evidence, and every affected column references its register row. | Register has >= 5 rows; 100% of affected columns in schema/tables reference a row; register validated by the ontology check. | venues.crew_assist_gap; venues.crew_block_gap; venues.crew_steal_gap; shots.assist_official_vs_video | C.04.04, M.03.06 | gap_closures_round2, rules_layer, ontology_audit_inbox007 | new-DQ-3, new-DQ-1 |
| N-DQ-07 | Should | P2 | Per venue, measure the home stat crew's assist, block and steal gap against video-derived events, with a 95% interval, and flag venues whose gap interval excludes 0. | Gap reported for every venue with >= 150 made FGs with a visible prior pass; video assist rule fixed before measuring; intervals by bootstrap over games. | venues.crew_assist_gap; venues.crew_block_gap; venues.crew_steal_gap; shots.assist_official_vs_video | C.04.04, M.03.06 | gap_closures_round2, rules_layer | new-DQ-4 |
### N-DS

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-DS-01 | Shall | P1 | A source-definition register holds, per source field that encodes a definition, the source's own definition (paraphrased), URL, verified flag, check date, the columns carrying it and its difference from our definition. | 100% of source-derived definitional columns link to a register row; every row re-checked each season (R-DS-01); seeded from source_field_map.md sections 4 and V with >= 15 rows. | see docs/data/gap_closures_round2.md | M.01.06 | gap_closures_round2, ontology_audit_inbox007 | new-DS-3, new-DS-2 |
### N-DT

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-DT-01 | Shall | P0 | Every position, speed, acceleration and heading value carries a propagated 1-sigma (position_sigma_m, speed_sigma_mps, accel_sigma_mps2, heading_sigma_deg) from mapping confidence, detection and the named filter; bias and SD measured on hand-timed runs and gold positions (R-PL-13) are propagated by simulation into every reported load and athletic interval. | Sigma present on 100% of rows; 68% intervals cover 60-76% of hand-measured values per court zone; every load and athletic metric shows an interval that includes measurement error. | player_positions.position_sigma_m, speed_sigma_mps, accel_sigma_mps2, heading_sigma_deg; load_stint_bins, accel_efforts, profile_snapshots intervals | I.01.01, I.03.06, L.06.05 | data_engineer, team_data_scientist | new-DT-E1, new-PL-S1 |
| N-DT-02 | Should | P2 | Each touch stores stop type, pivot foot, first-step kind and direction (degrees from the player->rim vector) and gather step count from pose. | Precision >= 80% on 200 labelled touches (as R-DT-16); pivot foot correct >= 85%; direction within 20 degrees median (proposal). | touches.stop_type; touches.pivot_foot; touches.first_step_kind; touches.first_step_dir_deg; touches.gather_steps; touches.pre_dribble_lift_suspected | E.01.04, E.01.05 | gap_closures_round2, ontology_audit_inbox007 | new-DT-3, new-DT-1 |
| N-DT-03 | Should | P2 | Each touch that starts a dribble from a hold flags a suspected pivot lift before the ball leaves the hand, as a count of possible travels; it never creates a violation row. | Flag agrees with frame-by-frame gold on >= 80% of 200 labelled starts (proposal); 0 turnovers or violations created from the flag. | touches.stop_type; touches.pivot_foot; touches.first_step_kind; touches.first_step_dir_deg; touches.gather_steps; touches.pre_dribble_lift_suspected | E.01.04, E.01.05 | gap_closures_round2, ontology_audit_inbox007, rules_layer | new-DT-4, new-DT-2 |
### N-EN

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-EN-01 | Shall | P0 | Stage outputs are content-addressed: output_key = sha256(stage name, code version, config hash, sorted input keys); a stage whose key exists is skipped. | Second run of the full pipeline on game 1 with unchanged inputs writes 0 new files and takes < 5% of the first run's wall time. | new table stage_outputs (output_key, stage, inputs, code_version, config_hash, created_utc, rows, bytes) | M.05.04 | data_engineer | new-EN-E1 |
| N-EN-02 | Shall | P0 | All writers write to a temp path and rename atomically; JSONL and manifest appends are one file per run, never appended across runs. | Kill test (R-EN-05) passes; no partial lines in any JSONL after 20 interruptions. | all writers incl. markets/store.py, markets/raw_store.py | M.05.04 | data_engineer | new-EN-E2 |
| N-EN-03 | Shall | P0 | IDs are deterministic: PBP events <game_id>:<source>:<source_play_id>; CV events hash(stage output key, kind, video_id, start frame, primary track). | Two runs with identical inputs give identical IDs (100%); changing a non-upstream stage leaves IDs unchanged. | all *_id columns of event tables | M.02.06, M.05.04 | data_engineer | new-EN-E3 |
| N-EN-04 | Should | P0 | The pipeline DAG (stages, inputs, outputs, versions) is declared in one config file and run by a small runner on Colab or the Mac; no orchestration server. | DAG passes a cycle check; the runner executes game 1 end to end from the file. | config/pipeline.yaml | M.05.04 | data_engineer | new-EN-E8 |
| N-EN-05 | Should | P1 | Provide DuckDB views over the lake for the 10 most common queries (possessions per game, chances by start type, player speed bins, shot chart, lineup stints, foul state, transitions by type). | Each query runs in < 5 s over two games on a laptop. | sql/views/*.sql | M.06.01 | data_engineer | new-EN-E6 |
| N-EN-06 | Shall | P1 | Schema evolution: adding a nullable column is minor; renaming, retyping or changing grain is major and needs a migration script and note; readers refuse unknown majors. | A test reader rejects a major bump; every major bump has a migration file. | schema_version as semver; schema/migrations/ | M.06.01, M.06.02 | data_engineer | new-EN-E7 |
| N-EN-07 | Should | P1 | Latency budget per output tier: Tier 1 (PBP plus scorebug: score, runs, fouls, four factors) ≤ 300 s after a video segment is available; tier 2 (tracking: transition, coverages, sets) ≤ 3,600 s per half; measured and logged per run. | Latency logged per output; met on ≥ 2 of the 3 pilot games or the gap and cause reported. | run_record.json latency fields | M.05.03, L.05.04 | espn_analyst | new-EN-A1 |
### N-EV

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-EV-01 | Should | P1 | Throw-in violations stored by article (5-second, spot, stepping on court, carrying onto court, defender breaking the plane) with the team and time. | Article present on 100% of PBP throw-in violations; defender plane breaks seen on video stored with the defender ID. | turnovers.turnover_type add throw_in_violation; restarts.violation_code uses 9-4 article strings. | A.08.06 | ontology_audit_inbox007, rules_layer | new-EV-2 |
| N-EV-02 | Shall | P1 | Every throw-in with a visible release creates a passes row flagged as a throw-in and linked to its restart, with whether the thrower was guarded within 1.83 m. | 100% of throw-ins with a visible release have exactly one is_throw_in pass; thrower equals restarts.thrower_player_id on 100%. | passes.is_throw_in; passes.restart_id; passes.defender_on_thrower | E.03.07 | gap_closures_round2, ontology_audit_inbox007, rules_layer | new-EV-18, new-EV-9 |
| N-EV-03 | Shall | P1 | Each field-goal attempt stores the closest defender's contest form from pose: hand up, contesting hand, minimum hand-to-ball distance (m), hand height relative to the ball (m), contest angle (degrees), vision interference, airborne, arrival time (s) and a contest class (none, late, soft, tight <= 1.07 m, smothered, block attempt). | Hand-up correct >= 85% on 300 labelled shots; hand-to-ball within 0.30 m median where both are visible in 3-D; class agreement >= 80%; image-scaled rows flagged and reported separately (proposal). | shots.contest_hand_up; shots.contest_hand_side; shots.hand_to_ball_m; shots.hand_height_rel_ball_m; shots.contest_angle_deg; shots.vision_interference; shots.contest_airborne; shots.contest_arrival_s; shots.contest_class; shots.contest_geometry_basis | E.04.05 | gap_closures_round2, ontology_audit_inbox007, data_engineer | new-EV-20, new-EV-11 |
| N-EV-04 | Should | P1 | Every missed-shot rebound stores the landing point (r in m, theta in degrees), the count of each team's players holding inside position at release (0.30 m / 1.0 m rule) and the rebounder's distance at release. | Recomputes from the shot_release snapshot; landing point within 0.50 m on 100 labelled misses (proposal). | rebounds.landing_r_m; rebounds.landing_theta_deg; rebounds.n_inside_off; rebounds.n_inside_def; rebounds.rebounder_dist_at_release_m | E.05.05 | gap_closures_round2, ontology_audit_inbox007, data_engineer, espn_analyst | new-EV-22, new-EV-13 |
| N-EV-05 | Shall | P1 | Runs are stored as rows under each R-MD-17 definition (unanswered, broadcast a-b, register net >= 8 in 120 s of game clock), with start and end score events, points for and against, timeouts during, the event that ended the run (called timeout and which team, media timeout, opponent score, foul, period end), possessions and game-clock seconds from start to stop, and what changed at the stop (lineup, scheme, set) linked to substitutions and scheme_changes. | Every run has exactly one end row; recomputes from score_events and events (0 differences); changes link to scheme_changes and substitutions where present. | new table runs (run_id, definition, start_s, end_s, for_pts, against_pts, ended_by, changes) | D.01.05, K.01.03, G.06.01 | espn_analyst, gap_closures_round2, ontology_audit_inbox007 | new-EV-A14, new-MD-9, new-EV-5 |
| N-EV-06 | Should | P2 | Record jump-ball violations (who, which article) and re-jumps on every jump ball. | Every jump ball has violation = none or a 9-8 article; re-jumps stored as kind = rejump; 100% agreement with PBP where PBP logs the violation. | New column jump_balls.violation_code (Rule 9-8 article or none). | A.04.08 | ontology_audit_inbox007, rules_layer | new-EV-1 |
| N-EV-07 | Should | P2 | The dribble-move vocabulary adds in-and-out, push, pound, snatch-back and half spin, each with the measured signature in the action vocabulary. | >= 75% correct on 300 labelled moves including >= 30 of each new class (as R-EV-05). | see docs/data/gap_closures_round2.md | E.02.04 | gap_closures_round2, ontology_audit_inbox007 | new-EV-14, new-EV-6 |
| N-EV-08 | Shall | P2 | Fake events (shot fake, jump fake, pass fake, jab step, rocker step, head/shoulder fake) are detected with the measured signatures in the action vocabulary and stored with touch, player, time and direction. | Recall >= 80% and precision >= 80% on 200 labelled fakes, per kind with >= 30 examples (proposal); head/shoulder fakes reported separately. | see docs/data/gap_closures_round2.md | E.02.06 | gap_closures_round2, ontology_audit_inbox007 | new-EV-15, new-EV-7 |
| N-EV-09 | Should | P2 | Each fake stores the on-ball defender's reaction (left feet, rose, shifted, closed out, none), its latency (s), the next action within 1.5 s and the value change after 1.0 s. | Reaction class correct >= 80% on 200 labelled fakes; latency within +/- 2 frames; value change recomputes from possession_value. | see docs/data/gap_closures_round2.md | E.02.06 | gap_closures_round2 | new-EV-16 |
| N-EV-10 | Should | P2 | Each pass stores hands, delivery (from hold, off the dribble, one-touch), release height (m) and a torso-based no-look flag (angle > 60 degrees), without face keypoints. | >= 80% correct on 300 labelled passes where the passer is at readable size (R-ID-05); release height within 0.20 m once R-CG-11 passes. | passes.hands; passes.delivery; passes.release_height_m; passes.torso_to_pass_angle_deg; passes.no_look_torso | E.03.06 | gap_closures_round2, ontology_audit_inbox007 | new-EV-17, new-EV-8 |
| N-EV-11 | Should | P2 | Each layup or dunk attempt stores a finish subtype (standard, reverse, Euro step, finger roll, scoop, up-and-under, power two-foot, hop step, runner, tip, one/two-hand dunk, alley-oop) from the measured signatures. | >= 75% correct on 300 labelled finishes, >= 20 per class where available (proposal). | shots.finish_subtype | E.04.02 | gap_closures_round2, ontology_audit_inbox007 | new-EV-19, new-EV-10 |
| N-EV-12 | Should | P2 | Each jump shot stores the shooter's footwork class from the measured foot-contact order, body rotation and release-time pelvis velocity. | >= 75% correct on 300 labelled jumpers (proposal); step_back agrees with shots.shot_type_code = step_back on >= 95%. | shots.footwork | E.04.12 | gap_closures_round2, ontology_audit_inbox007 | new-EV-21, new-EV-12 |
| N-EV-13 | Should | P2 | Hustle events: Per player per game: deflections, loose balls recovered, charges drawn, contested rebounds, box-outs, screen assists, with each event linked to video, under named definitions (ours, and the NBA hustle-stats definitions as a labelled reference, unverified). | Counts recompute from event rows; ≥ 85% agreement with labels on 100 events per type (proposal). | hustle_events | E.09.05, E.05.03, I.02.08 | espn_analyst | new-EV-A15 |
### N-FD

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-FD-01 | Shall | P0 | The games registry gains cbbd_game_id, video_ids, scorebug_left_team_id (team order on the bug), media_format (16/12/8/4 or 15/10/5) and pbp_status. | Filled for both first games (Louisville CBBD ID resolved or "none"); scorebug order matches W3 (UConn file: MSU left; Louisville file: Louisville left). | games / registry/games.csv | A.01.09, L.03.01, A.10.02 | data_engineer | new-FD-E1 |
| N-FD-02 | Shall | P0 | Each game stores the home bench end and the home team's first-half attacked basket in the full-court frame before tracking runs; tracking verifies both. | Filled for 100% of processed games before tracking; bench-person detections fall on the declared end on >= 99% of main-camera frames where bench persons are visible; first-half basket agrees with the first made field goal on 100% of games. | games.home_bench_end_fc; games.home_attacks_first_half_fc; venues.home_bench_end_default_fc | B.02.07 | gap_closures_round2, ontology_audit_inbox007 | new-FD-7, new-FD-5 |
| N-FD-03 | Shall | P2 | Game registry status distinguishes forfeited, no-contest and suspended games, with the playing time completed (s) and the rule applied. | games.status takes values final, forfeit, no_contest, suspended, postponed, canceled; for every non-final game the completed playing time is stored in s (+/- 1 s) and the game is excluded from engine training unless status = final. | games.status enum: add forfeit, no_contest, suspended; new column games.playing_time_completed_s (s). | A.01.07 | ontology_audit_inbox007 | new-FD-2 |
| N-FD-04 | Should | P2 | Record interruptions longer than 300 s (floor, lighting, clock failure, emergencies) with cause, game clock at interruption and resumption date-time. | Each interruption row carries game_clock_s (0.1 s), period, cause from a fixed list and resumption UTC; possessions spanning an interruption are flagged and excluded from tempo statistics. | New stoppage cause interruption in state_frame.stoppage_kind; new columns games.interrupted (bool), games.resumed_utc. | A.01.08 | ontology_audit_inbox007 | new-FD-3 |
| N-FD-05 | Should | P2 | Source game-flow descriptors kept on the registry row (CBBD excitement; KenPom excitement/tension/dominance if the API is bought), post-game only. | Stored with source and as-of = post-game; 0 pre-game features read them (leakage lint). | games.excitement_cbbd | A.01.06 | data_dictionaries_inbox006 | new-FD-1 |
| N-FD-06 | Should | P2 | Each game row stores the game-ball manufacturer and model with its public source, or 'not_public'. | Filled (value or 'not_public') for 100% of registered games; every non-'not_public' value has a URL and checked date. | games.ball_model; games.ball_model_source | B.02.02 | gap_closures_round2, ontology_audit_inbox007 | new-FD-6, new-FD-4 |
### N-HR

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-HR-01 | Shall | P1 | Every JEV consultation is logged privately (question ID, hash of items sent, options shown, answer, exact model version, time), and an automated test proves no pipeline module reads the log. | One row per consultation; import-graph and path-grep test shows 0 references from src/ to the JEV log path. | see docs/data/gap_closures_round2.md | M.04.06 | gap_closures_round2, ontology_audit_inbox007 | new-HR-2, new-HR-1 |
### N-HY

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-HY-01 | Shall | P1 | Any claim that a reaction (timeout, scheme change, substitution, press) changed outcomes uses a registered identification design: natural experiment (media timeouts set by the clock, as in beliefs B1), matching on score, time, run size and lineups, or a regression-discontinuity on rule thresholds (bonus at the 7th foul); pre/post comparisons are never reported as effects; sensitivity to unmeasured confounding stated (Γ). | Hypothesis row names the design and Γ; reviewer check fails rows without them. | hypothesis_results.design, hypothesis_results.gamma | M.06.07, J.06.01, G.06.01 | team_data_scientist | new-HY-S1 |
### N-ID

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-ID-01 | Should | P2 | Appearance cards list visible protective equipment per player-game as an identity tie-breaker only; no load, availability or injury model reads the field. | Field present on 100% of cards ('none' allowed); item-level agreement >= 85% on 100 labelled player-games (proposal); an import/feature-registry test shows 0 non-ID consumers. | appearance_cards.protective_equipment | B.02.10 | gap_closures_round2, ontology_audit_inbox007 | new-ID-2, new-ID-1 |
### N-IV

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-IV-01 | Shall | P0 | Invariants run on state_transitions and state_segments (event level); frame-level checks are limited to physics and court bounds. | Full invariant check < 60 s per game per pass on a laptop. | config/invariants.yaml (evaluated_on field) | M.03.02 | data_engineer | new-IV-E1 |
| N-IV-02 | Shall | P0 | Shot-clock full value is 30 s and it starts only when a throw-in is legally touched inbounds, a team gains initial control after a jump ball or an unsuccessful try, or team control changes. | 0 unreviewed breaks per game on both pilot games; scope per_frame; on break: human_review | config/invariants.yaml; tables: state_frame, restarts | A.03.02, M.03.02 | invariants_rules | new-IV-01 |
| N-IV-03 | Shall | P0 | After an offensive rebound in the frontcourt off a try (or pass or deflection) that touched the ring or flange, the shot clock shows exactly 20 s, even if more or less time remained. | 0 unreviewed breaks per game on both pilot games; scope per_reset; on break: human_review | config/invariants.yaml; tables: restarts, state_frame, shots | A.03.04 | invariants_rules | new-IV-02 |
| N-IV-04 | Shall | P0 | Defensive foul or kicked/fisted ball with a frontcourt throw-in (before any ring contact): shot clock = max(20, time remaining). | 0 unreviewed breaks per game on both pilot games; scope per_reset; on break: human_review | config/invariants.yaml; tables: restarts | A.03.05 | invariants_rules | new-IV-03 |
| N-IV-05 | Shall | P0 | No-reset situations keep the unexpired shot-clock time (ball out of bounds off the defence, injury, end of a timeout, arrow favours the team in control, inadvertent whistle with control, technical on the team in control, etc.). | 0 unreviewed breaks per game on both pilot games; scope per_restart; on break: human_review | config/invariants.yaml; tables: restarts | A.03.06 | invariants_rules | new-IV-04 |
| N-IV-06 | Shall | P0 | When on, the shot clock never shows more than the game clock; it is turned off when a reset would exceed the game clock, and reactivated at 20 s for 2-11.6.d situations. | 0 unreviewed breaks per game on both pilot games; scope per_frame; on break: flag | config/invariants.yaml; tables: state_frame | A.03.07 | invariants_rules | new-IV-05 |
| N-IV-07 | Shall | P0 | A shot-clock violation requires that the try was not released before the horn, or was released and then did not touch the ring or flange or enter the basket. | 0 unreviewed breaks per game on both pilot games; scope per_event; on break: human_review | config/invariants.yaml; tables: events, made_basket_events, shots | A.03.08 | invariants_rules, data_engineer | new-IV-06 |
| N-IV-08 | Shall | P0 | Free-throw award matches the foul and the team-foul count: common foul before the 7th team foul -> no free throws (throw-in); 7th-9th -> one-and-one; 10th+ -> two; player-control and non-loose-ball team-control fouls -> no free throws; loose-ball team-control fouls are bonus-eligible. | 0 unreviewed breaks per game on both pilot games; scope per_foul; on break: human_review | config/invariants.yaml; tables: free_throws, foul_state, events | A.07.01, A.06.18 | invariants_rules | new-IV-07 |
| N-IV-09 | Shall | P0 | Shooting-foul awards: made try -> 1 (and-one); missed 2-point try -> 2; missed 3-point try -> 3; flagrant -> 2 plus the ball; Class A technical -> 2; Class B technical -> 1; administrative technical -> 1 (2 for 10-2.6 and 10-2.7); technical free throws by one designated player. | 0 unreviewed breaks per game on both pilot games; scope per_ft_sequence; on break: human_review | config/invariants.yaml; tables: free_throws | A.07.01, A.06.02 | invariants_rules | new-IV-08 |
| N-IV-10 | Shall | P0 | What follows the last free throw: missed last FT for a personal foul -> ball live (rebound); made -> opponent throw-in from the end line; technical -> point of interruption; flagrant -> shooting team throw-in at the designated spot. | 0 unreviewed breaks per game on both pilot games; scope per_ft_sequence; on break: human_review | config/invariants.yaml; tables: free_throws, restarts, state_frame | A.07.06 | invariants_rules | new-IV-09 |
| N-IV-11 | Shall | P0 | Disqualification: a player is disqualified at the 5th foul (personal + Class A technical) or the 3rd Flagrant 1; ejected for a Flagrant 2, two Class A technicals, one Class A + two Class B, or three Class B technicals; must be replaced within 20 s. | 0 unreviewed breaks per game on both pilot games; scope per_foul; on break: human_review | config/invariants.yaml; tables: foul_state, state_frame, timeouts | A.06.19, A.06.20, A.11.04 | invariants_rules | new-IV-11 |
| N-IV-12 | Shall | P0 | Media timeouts (16/12/8/4 or 15/10/5 format): at most one per mark per half, taken at the first dead ball at or after the mark; a timeout, review or challenge creating a dead ball within 30 s before a mark becomes that media timeout; the first team timeout of the second half takes the media length; a missed mark is taken at the next dead ball and the following mark only after the clock has properly started (A.R. 5-33). | 0 unreviewed breaks per game on both pilot games; scope per_half; on break: flag | config/invariants.yaml; tables: timeouts | A.10.02 | invariants_rules, espn_analyst | new-IV-13 |
| N-IV-13 | Shall | P0 | Coach's challenge: one per team per game; a second only after the first is overturned; a legal timeout is needed; an unsuccessful challenge costs that timeout; only out of bounds (any time), goaltending/basket interference and restricted-area calls (until the last two minutes of regulation). | 0 unreviewed breaks per game on both pilot games; scope per_review; on break: flag | config/invariants.yaml; tables: reviews, timeouts | A.13.02 | invariants_rules, quality_review | new-IV-14 |
| N-IV-14 | Shall | P0 | Throw-in: released within 5 s of disposal; designated spot 3 ft wide; after a score the thrower may run the end line. | 0 unreviewed breaks per game on both pilot games; scope per_restart; on break: flag | config/invariants.yaml; tables: restarts | A.09.04 | invariants_rules, data_engineer | new-IV-16 |
| N-IV-15 | Shall | P0 | Throw-in spot after a frontcourt stoppage with the offence keeping the ball: end line 3 ft outside the lane line or the sideline 28-ft mark (Rule 7-3.2.b as changed in 2025-26); defence-caused out of bounds: spot where the ball went out. | 0 unreviewed breaks per game on both pilot games; scope per_restart; on break: flag | config/invariants.yaml; tables: restarts | A.09.03 | invariants_rules | new-IV-18 |
| N-IV-16 | Shall | P0 | Possession arrow: set to the team that did not gain control of the opening jump; flips each time an alternating-possession throw-in ends; reversed in direction (not in team) at half time; the second half starts with the arrow team at the division line opposite the scorers' table. | 0 unreviewed breaks per game on both pilot games; scope per_game; on break: human_review | config/invariants.yaml; tables: restarts, state_frame | A.04.07 | invariants_rules | new-IV-19 |
| N-IV-17 | Shall | P0 | Extra periods: 5 min each, no change of baskets, 1-minute intermission, started by a jump ball; team fouls carry from the second half. | 0 unreviewed breaks per game on both pilot games; scope per_period; on break: human_review | config/invariants.yaml; tables: state_frame, restarts, foul_state | A.01.05 | invariants_rules | new-IV-20 |
| N-IV-18 | Shall | P0 | Teams change baskets at half time. | 0 unreviewed breaks per game on both pilot games; scope per_game; on break: human_review | config/invariants.yaml; tables: state_frame | A.01.01 | invariants_rules | new-IV-21 |
| N-IV-19 | Shall | P0 | Game clock shows tenths under one minute; in the last 59.9 s at least 0.3 s comes off on any legal touch followed by an immediate stop; with 0.3 s or less on the game or shot clock at a throw-in or free throw, a score can only come from a tap. | 0 unreviewed breaks per game on both pilot games; scope per_event; on break: human_review | config/invariants.yaml; tables: state_frame, made_basket_events, scoreboard_ocr | A.02.04 | invariants_rules | new-IV-22 |
| N-IV-20 | Shall | P0 | A goal at the end of a period counts only if the try was released before the game clock read zeros (red light / horn when the clock is not visible); a try in flight ends the period when the try ends. | 0 unreviewed breaks per game on both pilot games; scope per_make; on break: human_review | config/invariants.yaml; tables: made_basket_events, reviews | A.01.03 | invariants_rules, data_engineer | new-IV-23 |
| N-IV-21 | Shall | P0 | Points without the ball going through: goaltending or basket interference by the defence awards 1 (free throw, plus Class B technical), 2 or 3; a violation at a team's own basket awards no points; illegal assistance to block a try awards the try's points. | 0 unreviewed breaks per game on both pilot games; scope per_event; on break: human_review | config/invariants.yaml; tables: score_events, made_basket_events | A.05.03, A.05.04 | invariants_rules | new-IV-24 |
| N-IV-22 | Shall | P0 | Timing corrections are made within the half (or extra period) of the mistake and never carried over; shot-clock corrections only within the same shot-clock period. | 0 unreviewed breaks per game on both pilot games; scope per_review; on break: flag | config/invariants.yaml; tables: reviews, state_corrections | A.02.05 | invariants_rules | new-IV-27 |
| N-IV-23 | Shall | P0 | No timeout is granted to the opponents of the throw-in team after the throw-in starts, during an interrupted dribble, or (except at a dead ball) without player control by the requesting team; none before the opening jump ends; none in the last two minutes until review results are reported (except a challenge timeout). | 0 unreviewed breaks per game on both pilot games; scope per_timeout; on break: flag | config/invariants.yaml; tables: timeouts, state_frame | A.10.04 | invariants_rules | new-IV-28 |
| N-IV-24 | Shall | P0 | A score change on the board happens only while the ball is dead after a goal or free throw, during a review or timeout correction, or for a goal released before the horn; never in the middle of live play without a goal. | 0 unreviewed breaks per game on both pilot games; scope per_event; on break: human_review | config/invariants.yaml; tables: score_events, state_frame | A.05.06, D.01.02 | invariants_rules | new-IV-31 |
| N-IV-25 | Shall | P0 | Double and simultaneous personal fouls award no free throws (both charged; team fouls count); play resumes at the point of interruption, unless exactly one of the fouls is flagrant. | 0 unreviewed breaks per game on both pilot games; scope per_foul; on break: flag | config/invariants.yaml; tables: free_throws, foul_state, restarts | A.06.07 | invariants_rules | new-IV-32 |
| N-IV-26 | Should | P0 | Officials' scorebook authority: when sources disagree and the discrepancy is unresolved, the official scorebook (as published in PBP and the box score) wins over the arena board, which wins over the broadcast scorebug. | 0 unreviewed breaks per game on both pilot games; scope per_game; on break: human_review | config/invariants.yaml; tables: score_events, scoreboard_flags, state_corrections | C.04.01 | invariants_rules | new-IV-33 |
| N-IV-27 | Shall | P1 | Free-thrower releases within 10 s of disposal; lane players may not enter early; the shooter stays behind the line and in the semicircle until the ball touches the ring, flange or backboard. | 0 unreviewed breaks per game on both pilot games; scope per_ft_attempt; on break: flag | config/invariants.yaml; tables: free_throws | A.07.04 | invariants_rules | new-IV-10 |
| N-IV-28 | Shall | P1 | Closely guarded: a frontcourt player holding (not dribbling) the ball, guarded within 6 ft (1.83 m) by the same opponent, may not hold it for 5 s. | 0 unreviewed breaks per game on both pilot games; scope per_touch; on break: flag | config/invariants.yaml; tables: events, tracks | A.04.14 | invariants_rules | new-IV-15 |
| N-IV-29 | Should | P1 | Three seconds in the lane: no offensive player stays in the frontcourt lane more than 3 consecutive seconds while his team controls the ball (not during a throw-in; count suspended on a move to shoot). | 0 unreviewed breaks per game on both pilot games; scope per_frame; on break: flag | config/invariants.yaml; tables: tracks, state_frame | A.04.15 | invariants_rules | new-IV-17 |
| N-IV-30 | Shall | P1 | Free-throw substitutions: an entering player may not replace the free-thrower; during multiple free throws for personal fouls, substitutes enter only before the final attempt (or after it is made); for technical or flagrant free throws, before the first or after the last. | 0 unreviewed breaks per game on both pilot games; scope per_ft_sequence; on break: flag | config/invariants.yaml; tables: free_throws, events | A.07.08 | invariants_rules, data_engineer | new-IV-25 |
| N-IV-31 | Shall | P1 | No substitutions while the clock is stopped after a made field goal in the last 59.9 s of the second half or an extra period, except those the rules permit; a withdrawn player re-enters only after the clock has properly started. | 0 unreviewed breaks per game on both pilot games; scope per_event; on break: flag | config/invariants.yaml; tables: events, state_frame | A.11.03 | invariants_rules, data_engineer | new-IV-26 |
| N-IV-32 | Shall | P1 | Lane spaces for free throws: first space above each block for opponents of the shooter, second for teammates, third for opponents; no teammate in the spaces nearest the basket. | 0 unreviewed breaks per game on both pilot games; scope per_ft_attempt; on break: flag | config/invariants.yaml; tables: free_throws | A.07.03 | invariants_rules | new-IV-29 |
| N-IV-33 | Shall | P1 | Score of a forfeited game is recorded 2-0 unless 30 minutes of playing time were completed (then the score stands); a team with a single player forfeits unless both can still win. | 0 unreviewed breaks per game on both pilot games; scope per_game; on break: quarantine | config/invariants.yaml; tables: games, score_events | A.01.07 | invariants_rules, data_engineer | new-IV-30 |
### N-MB

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-MB-01 | Should | P1 | Label own-basket goals as an edge case of made-basket detection, with the team credited and the player who touched it last. | Edge case present in the MB test set; credited team equals PBP on 100% of cases. | made_basket_events.edge_case: add wrong_basket_goal; score_events.event_kind value own_basket. | A.05.05 | ontology_audit_inbox007 | new-MB-1 |
### N-MD

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-MD-01 | Shall | P0 | Store game state as validity intervals per dimension and pass; per-frame and per-second state are views. | View regenerated from segments equals the stored per-frame values of the current state_frame spec on 100% of frames of game 1. | new table state_segments (game_id, pass, dimension, value, valid_from_ts_ms, valid_to_ts_ms, valid_from_gc, valid_to_gc, period, source, conf, dq, opened_by_transition_id) | D.02.01, D.04.01, D.10.03, M.06.01 | data_engineer | new-MD-E2 |
| N-MD-02 | Shall | P0 | Store team-relative state by team_id (or home/away); MSU-relative columns exist only in views. | A PBP-only non-MSU D-I game runs end to end with 0 nulls in team-relative state. | global_metadata.yaml (score_team_a/b by team_id), views *_msu | D.01.01, D.03.01, M.06.01 | data_engineer | new-MD-E3 |
| N-MD-03 | Shall | P0 | Every event row carries four time stamps: video_ts_ms (null for pbp_only), period + game_clock_s, shot_clock_s with status, est_utc with est_utc_err_s. | ≥ 99% of video-pass events have all four (UTC may carry a large error); 100% have period and game clock. | all event tables | A.02.06, M.02.06, J.05.03 | data_engineer | new-MD-E4 |
| N-MD-04 | Shall | P0 | Rows that can be revised (PBP, OCR, reviews, crosswalk) carry known_at_utc (when the value was first available) in addition to the instant they describe. | Leakage test: a feature at in-game instant t or pre-game cutoff C uses only rows with known_at_utc ≤ the matching UTC; 0 violations on games 1-2. | provenance block | M.02.05, M.02.02 | data_engineer | new-MD-E5 |
| N-MD-05 | Should | P0 | Score state carries times tied and each team's largest lead as of each second, with lead changes counted only when the leader differs from the last leader. | End-of-game values equal ESPN leadChanges and team_box.largest_lead on 100% of games where published (differences logged with the source's definition). | state_second.times_tied; state_second.largest_lead_msu; state_second.largest_lead_opp | D.01.03 | gap_closures_round2, ontology_audit_inbox007 | new-MD-8, new-MD-2 |
| N-MD-06 | Shall | P1 | Store per frame the team in control's frontcourt status, the frame it was established and the clause that established it (ball-floor contact, ball-player contact, dribbler both feet and ball, holder both feet, inherited in the air), with a 'uncertain' state when the deciding foot or ball point is within 0.10 m of the division-line edge. | Status-change time within +/- 0.20 s of gold on >= 95% of 200 labelled backcourt-to-frontcourt crossings (proposal); 'uncertain' <= 5% of crossing frames; every PBP backcourt or 10-second violation shows a status sequence consistent with it (frontcourt -> backcourt, or backcourt for >= 10.0 s of the count). | state_frame.frontcourt_status; state_frame.frontcourt_established_ts_ms; state_frame.frontcourt_basis; possessions.frontcourt_entry_s | A.04.12 | gap_closures_round2, ontology_audit_inbox007, quality_review, rules_layer | new-MD-6, new-SR-3 |
| N-MD-07 | Shall | P1 | Short corner, one pass away, help position and tag are defined in metres and degrees (values above) in the vocabulary map, and geometry.spot() returns short_corner; passes_away, help_position and the screen tag are stored per frame, second or screen. | 0 vocabulary entries say 'to be defined'; spot() unit tests on 20 hand-placed points pass; passes_away agrees with coach labels on >= 85% of 300 player-frames and tag with labels on >= 80% of 100 ball screens (proposal). | player_positions.passes_away; defensive_matchups.help_position; screens.tag_defender_id; screens.tag_contact_s | B.01.13 | gap_closures_round2, rules_layer, ontology_audit_inbox007 | new-MD-7, new-MD-1 |
| N-MD-08 | Should | P1 | Every second carries game-clock seconds since each team's last made field goal and last point, carried across period breaks. | Recomputes from score_events within 0.1 s; values carried across half time are flagged; drought counts (>= 240 s) per game reported. | state_second.secs_since_fg_msu; state_second.secs_since_fg_opp; state_second.secs_since_point_msu; state_second.secs_since_point_opp | D.01.06 | gap_closures_round2, ontology_audit_inbox007 | new-MD-10, new-MD-3 |
| N-MD-09 | Should | P1 | Each lineup stint stores composition descriptors for its five players (mean, max and min listed height in cm, height difference to the opponent unit, listed-position counts, bigs, shooters and ball handlers as of the game date, mean class year, archetype). | Filled on 100% of stints with five known players; recomputes from rosters and as-of snapshots; leakage test shows 0 post-tip inputs. | lineup_stints.mean_height_cm; lineup_stints.max_height_cm; lineup_stints.min_height_cm; lineup_stints.height_diff_cm; lineup_stints.n_listed_g; lineup_stints.n_listed_f; lineup_stints.n_listed_c; lineup_stints.n_bigs; lineup_stints.n_shooters_asof; lineup_stints.n_ball_handlers_asof; lineup_stints.mean_class_year; lineup_stints.archetype | D.07.04 | gap_closures_round2, ontology_audit_inbox007, espn_analyst | new-MD-12, new-MD-5 |
| N-MD-10 | Should | P1 | Each possession stores garbage-time flags side by side under three named definitions: the source flag (hoopR NCAA is_garbage_time and others), the CTG-adapted margin/time/starters rule (last 12:00 of the second half), and the win-probability rule (pre-possession WP > 0.98 or < 0.02 with <= 300 s left); no row is ever dropped by any of them. | All three flags present (or null with reason) on 100% of possessions; 0 rows dropped; share of possessions flagged per definition per game reported (%). | possessions.is_garbage_time_source, garbage_time_ctg_adapted, garbage_time_wp | D.02.04 | gap_closures_round2, data_dictionaries_inbox006, ontology_audit_inbox007 | new-MD-11, new-SY-1, new-MD-4 |
| N-MD-11 | Shall | P1 | Broadcast vocabulary layer: Every analytic label shown to people has, in config/vocabulary_map.yaml, a coach term, a broadcast phrase of ≤ 4 words (e.g. ICE → "forcing him baseline"), and a list of banned or ambiguous synonyms. | 100% of labels used in outputs have all three; a coach or analyst review of 50 phrases rates ≥ 90% "acceptable on air". | config/vocabulary_map.yaml fields coach_term, broadcast_phrase, avoid | M.06.03, L.05.04, F.13.05 | espn_analyst | new-MD-A6 |
| N-MD-12 | Shall | P1 | Decision-point snapshots: at each decision point of §1.4 (secure, inbound release, first frontcourt catch, screen moment, catch, drive start, post entry, release, rim contact, dead ball), store the 10 positions with σ, ball, both clocks, score, fouls, timeouts, lineups and the coverage score. | Snapshot count per possession recomputes from events; ≥ 95% of decision points have a row. | configuration_snapshots (extend with decision_point_type) | F.03.01, D.10.01 | team_data_scientist | new-MD-S1 |
### N-MK

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-MK-01 | Should | P2 | Public ticket and money shares are stored per market snapshot only from a source registered in the source register with terms checked, and only the market-input model variant may read them. | Source register row with terms URL and permission status exists before the first value; 0 values read by the market-free variant (import test). | market_snapshots.public_ticket_share; market_snapshots.public_money_share; market_snapshots.public_share_source | J.05.06 | gap_closures_round2, ontology_audit_inbox007, data_engineer | new-MK-20, new-MK-19 |
### N-OS

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-OS-01 | Should | P1 | Team box rows store bench points and bench minutes share, and team profiles report them as of each date with bench net rating per 100 possessions. | Recomputes from player_box; equals published bench points where a source gives them; minutes total check (200 + 25 per OT) passes. | team_box.bench_points; team_box.bench_minutes_share | H.02.04 | gap_closures_round2, ontology_audit_inbox007 | new-OS-2, new-OS-1 |
### N-PC

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-PC-01 | Should | P1 | Store shooting hand (L/R) per player from release pose with the number of clear releases seen, and use it as an identity tie-breaker (R-ID-13). | Value only with n >= 10 clear releases; agrees with film labels for 100% of MSU players with n >= 10. | players.shooting_hand, shooting_hand_n | C.01.08, L.06.06 | data_dictionaries_inbox006 | new-PC-4 |
| N-PC-02 | Shall | P1 | Every player-card metric displays n, reliability (N-VA-04), posterior interval and a D-I population percentile when a population source exists; metrics with only MSU-game data are labelled "MSU games only". | Fields present on 100% of displayed card metrics. | profile_snapshots | H.04.03, C.01.21 | team_data_scientist | new-PC-S1 |
| N-PC-03 | Should | P2 | Store roster status per player-season (scholarship, walk-on, preferred walk-on, manager-turned-player, unknown) with source. | Filled or "unknown" for 100% of MSU players; every non-unknown value has a source and date. | players.roster_status (dictionary_players.md) | C.01.02 | data_dictionaries_inbox006 | new-PC-2 |
| N-PC-04 | Should | P2 | Store shoe size (US men's) where published, for a CV foot-size scale check. (low value (about 0% public); candidate to drop) | Field present; filled or "not public" (expected ~0% public). | players.shoe_size_us (dictionary_players.md) | C.01.05 | data_dictionaries_inbox006 | new-PC-3 |
| N-PC-05 | Should | P2 | Rosters store each player's season captain designation with source, and player-game context the game captain where visible. | Filled ('unknown' allowed) for 100% of rostered players; every 'season_captain' has a source URL. | rosters.captain; rosters.captain_source; player_game_context.game_captain | C.01.17 | gap_closures_round2, data_dictionaries_inbox006, ontology_audit_inbox007, data_engineer | new-PC-9, new-PC-1, new-PC-7 |
| N-PC-06 | Should | P2 | NIL values on player cards carry source URL, publication date and kind (estimate/reported) and are excluded from every model feature set until a registered hypothesis names them. (keep only if Aldemir keeps NIL at all (decision)) | 100% of non-null NIL values have all three fields; feature-registry test shows 0 model inputs using NIL without a registered hypothesis ID. | player_card_template.nil_source; player_card_template.nil_as_of_date; player_card_template.nil_kind | C.01.14 | gap_closures_round2, data_dictionaries_inbox006, ontology_audit_inbox007 | new-PC-8, new-PC-5, new-PC-6 |
### N-PL

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-PL-01 | Shall | P1 | Kinematic bands, efforts and onsets are reported only where the propagated sigma is ≤ half the band width (speed) or ≤ 0.5 m/s² (acceleration); elsewhere they are "unresolved" and counted. | Resolvable share per player-game in every load report. | load_stint_bins, accel_efforts (resolvable flag) | I.02.01, I.02.02, I.03.06 | data_engineer | new-PL-E1 |
| N-PL-02 | Should | P2 | Jumps are stored as movement primitives with flight time (s), flight-time height (m), takeoff pattern and purpose, and player profiles report jumps and high jumps (>= 0.40 m) per minute played. | Jump recall >= 90% and precision >= 90% on 200 labelled jumps (proposal); flight time within +/- 2 frames of gold; height reported only where 3-D foot heights pass R-CG-11, error <= 0.10 m on hand-measured jumps. | movement_primitives.flight_time_s; movement_primitives.jump_height_m; movement_primitives.takeoff_pattern; movement_primitives.jump_purpose | E.01.03, I.02.06 | gap_closures_round2, ontology_audit_inbox007 | new-PL-5, new-PL-1 |
| N-PL-03 | Should | P2 | Changes of direction (>= 45 degrees within 0.5 s at entry speed >= 3.0 m/s) are stored with heading change, entry and exit speed (m/s) and recovery time (s), split at 90 degrees. | Recomputes from smoothed tracks; count per minute reported with coverage (R-PL-05); detection agrees with labels on >= 85% of 100 labelled cuts (proposal). | movement_primitives.heading_change_deg; movement_primitives.entry_speed_mps; movement_primitives.exit_speed_mps; movement_primitives.recovery_s | E.01.06 | gap_closures_round2, ontology_audit_inbox007, data_engineer, espn_analyst, team_data_scientist | new-PL-6, new-PL-2 |
| N-PL-04 | Should | P2 | Load stint bins split time (s) and distance (m) into forward, lateral and backward movement relative to torso facing, reported only where pose coverage is >= 70% of the stint. | Direction split sums to the bin totals within 1%; recomputes from player_positions; low-coverage stints flagged and excluded from rankings. | load_stint_bins.time_forward_s; load_stint_bins.time_lateral_s; load_stint_bins.time_backward_s; load_stint_bins.dist_forward_m; load_stint_bins.dist_lateral_m; load_stint_bins.dist_backward_m; load_stint_bins.dir_pose_coverage | I.02.07 | gap_closures_round2, ontology_audit_inbox007 | new-PL-7, new-PL-3 |
| N-PL-05 | Should | P2 | Per player-game, count contact events (screens set and absorbed at <= 0.30 m, box-out contacts >= 0.30 s, post contacts >= 1.0 s, charges, floor dives) per minute played, with coverage. | Counts recompute from source tables; reported only for games with tracking coverage >= 70% of the player's minutes. | see docs/data/gap_closures_round2.md | I.02.08 | gap_closures_round2, ontology_audit_inbox007 | new-PL-8, new-PL-4 |
### N-PR

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-PR-01 | Should | P1 | Leverage and swing plays: Per possession, the leverage (expected change in win probability given the state) and per play the realised change; the 5 largest swing plays per game listed with clip references. | Recomputes from wp_live; top-5 list per game; leverage calibrated with the WP model (R-PR-11). | possessions.leverage, swing_plays | H.05.02, D.09.01 | espn_analyst | new-PR-A1 |
| N-PR-02 | Should | P1 | Prediction drivers: Each pre-game prediction lists its top 3 drivers in points of margin (e.g. rating gap, home court, rest, availability), summing with the remainder to the predicted margin. | Drivers plus remainder equal the predicted margin within 0.1 points on 100% of predictions. | predictions.drivers | H.05.01 | espn_analyst | new-PR-A2 |
### N-RF

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-RF-01 | Shall | P1 | Every block or charge call stores the defender's feet position relative to the restricted-area arc (inside, on, outside; distance in m), whether he was a secondary defender, his time set before contact (s) and the call. | RA status from tracking with arc distance error <= 0.15 m on 100 labelled calls (proposal); call equals PBP on 100% of PBP-coded charges. | fouls.foul_subtype add blocking; new columns fouls.defender_ra_dist_m (m), fouls.secondary_defender (bool), fouls.defender_set_time_s (s). | A.06.06 | ontology_audit_inbox007, espn_analyst, rules_layer | new-RF-1 |
| N-RF-02 | Should | P1 | Foul subtype vocabulary includes multiple, false double and false multiple fouls, linked to their free-throw sequences. | Subtype present on every such foul; free-throw attempts per sequence equal the award table on 100% of cases. | fouls.foul_subtype add multiple, false_double, false_multiple. | A.06.08 | ontology_audit_inbox007, rules_layer | new-RF-2 |
| N-RF-03 | Should | P1 | fouls rows distinguish administrative technicals with the 10-2 article that applied. | foul_subtype = administrative_technical with a 10-2 article on 100% of such fouls; FT count equals the award table. | fouls.foul_subtype add administrative_technical; new column fouls.rule_article. | A.06.14 | ontology_audit_inbox007, rules_layer | new-RF-4 |
| N-RF-04 | Shall | P1 | Every foul stores its contact mechanism from the Appendix VIII foul-signal list (holding, pushing, hand-check, illegal use of hands, blocking, player/team control, tripping, hit to head, excessive contact, chucking, pinning a defender, dislodging with knee or lower body, vertical-cylinder violation, landing space, illegal screen), from the official's signal or video, with source. | Mechanism present (or unseen) on 100% of fouls; agrees with labelled gold on >= 80% of 300 fouls (proposal). | New column fouls.contact_type (enum from App. VIII); official_positions.signal_pose enum extended to App. VIII. | A.06.17 | ontology_audit_inbox007, rules_layer | new-RF-5 |
| N-RF-05 | Should | P1 | Signal vocabulary covers every Appendix VIII signal (start/stop clock, timeouts, every violation and foul signal, shot-clock reset, no score, tipped ball, counts, 3-point attempt and success, free-throw counts, replay, challenge, flopping). | Every App. VIII signal has a code; signal recognition >= 80% on 300 labelled signals (as R-RF-04); unseen signals coded unseen. | official_positions.signal_pose enum := App. VIII list (config/vocabulary_map.yaml section signals). | A.12.05 | ontology_audit_inbox007, rules_layer | new-RF-10 |
| N-RF-06 | Should | P2 | Record fighting incidents and the suspensions that follow (player, games suspended, games served) in the player availability log. | Every PBP or public fighting report has a row; availability.status = out with reason suspension for each suspended game. | availability.status add suspended; events.event_family value fight. | A.06.21 | ontology_audit_inbox007, rules_layer | new-RF-6 |
| N-RF-07 | Should | P2 | Record flopping warnings and technicals, and label suspected flops on review (player, time, contact seen yes/no). | All PBP-logged flop technicals present; suspected flops reviewed with kappa >= 0.6 between labellers (proposal). | fouls.foul_subtype add flop_technical; new event family flop_warning. | A.06.22 | ontology_audit_inbox007, rules_layer | new-RF-7 |
| N-RF-08 | Should | P2 | Detect each officials' rotation and post-foul switch as an event (time, officials involved, from and to roles). | >= 85% of rotations found within +/- 1.0 s on 100 labelled rotations (proposal). | New event family official_rotation in events, from official_positions role changes. | A.12.03 | ontology_audit_inbox007, data_engineer, rules_layer | new-RF-8 |
| N-RF-09 | Should | P2 | Each call stores the calling official's distance to the contact point (m), his angle to the play (degrees) and whether the play was in his primary coverage area by the crew's positions. | Distance from tracking within 0.5 m of gold on 100 calls; primary-area flag agrees with a referee-expert label on >= 80% (proposal). | New columns fouls.official_dist_m (m), fouls.official_angle_deg (degrees), fouls.in_primary_area (bool). | A.12.04 | ontology_audit_inbox007, espn_analyst, rules_layer, team_data_scientist | new-RF-9 |
| N-RF-10 | Should | P2 | Record the start of each official's visible count (throw-in, closely guarded, backcourt) from the signal or from the rule trigger, so counts can be compared with our own clocks. | Count start within +/- 0.3 s of a hand label on >= 80% of 100 labelled counts (proposal). | New column official_positions.count_active (enum none, five, ten). | A.12.07 | ontology_audit_inbox007, rules_layer | new-RF-11 |
| N-RF-11 | Should | P2 | Official profile snapshots hold games worked this season and in total, seasons seen, conferences worked and postseason games, as of each game date, from D-I PBP officials lists. | Recomputes from game_officials; leakage test shows 0 games on or after the as-of date counted; values equal a hand count for 5 officials. | see docs/data/gap_closures_round2.md | C.03.03 | gap_closures_round2, ontology_audit_inbox007, data_engineer | new-RF-13, new-RF-12 |
| N-RF-12 | Shall | P2 | Whistle latency: For each whistle with a visible contact or violation frame, the time from that frame to the whistle (from audio, R-RF-01) and to the official's signal (pose), with the calling official's role. | Latency within ±0.1 s of a hand label on 100 calls; distribution per crew per game. | fouls.contact_frame, .whistle_latency_s, .signal_latency_s | A.12.06, L.04.01 | espn_analyst | new-RF-A13 |
| N-RF-13 | Should | P2 | Calls by official role and area: Per crew and per official, calls split by the caller's role (lead, trail, centre) and by court area (r, θ sectors), as of date, with n. | Recomputes from fouls and official_positions; values with n < 30 calls flagged. | official_call_map | A.12.04, C.03.02 | espn_analyst | new-RF-A14 |
| N-RF-14 | Should | P2 | Unwhistled contact candidates (review only): Flag plays with contact-like signatures (two opponents within 0.3 m with an abrupt deceleration ≥ 3 m/s² of the ball handler or shooter, proposal) and no whistle within 1.0 s; they enter the review queue only and are never published as "missed calls"; a reviewer labels contact seen yes or no. | Flags reviewed with a label; published outputs contain 0 "missed call" claims (lint). | contact_candidates (review-only, private) | A.12.04, M.04.01 | espn_analyst | new-RF-A15 |
### N-RL

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-RL-01 | Shall | P0 | Every game row carries a rules_edition_id that points to a versioned rules configuration (config/rules_ncaa_men_<season>.yaml) holding every rule-derived constant (clock lengths, shot-clock values, foul limits, timeout allotments, court marks, challenge rules) with its rule citation; every check and simulation reads constants from that edition only. | 100% of games have a rules_edition_id; a test changes one constant in a copy of the edition and every dependent check changes result; 0 rule constants hard-coded in code (grep test). | New config files config/rules_ncaa_men_<season>.yaml (merge of court_ncaa_men.yaml constants and invariants.yaml constants); new column games.rules_edition_id. | A.01.10 | ontology_audit_inbox007, espn_analyst, quality_review, rules_layer | new-RL-1 |
| N-RL-02 | Shall | P0 | The rules edition of a game is the record of config/vocab/rules_edition.yaml whose season window (1 July - 30 June, our convention) contains the local tip date; a game outside every window gets rules_edition_id = unknown and every rule-derived check is skipped and flagged. | 100% of registered games carry an edition or "unknown"; a 2014-15 game resolves to the 35-s-shot-clock edition or "unknown", never to 2026-27; unit test on boundary dates. | games.rules_edition_id; config/vocab/rules_edition.yaml | A.01.10 | rules_layer | new-RL-2 |
### N-RR

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-RR-01 | Should | P0 | Every stage writes structured JSON-lines logs (stage, game, chunk, counters, warnings); the run record aggregates them. | Logs present for 100% of stages; a failed chunk is findable from the run record in one lookup. | private logs/<run_id>/ | M.05.01 | data_engineer | new-RR-E1 |
### N-SR

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-SR-01 | Shall | P1 | Record each intermission (half time and before every extra period) as a stoppage row with start and end video time, duration and the teams' return time to the floor. | Intermission duration within +/- 2 s of the scoreboard countdown or the video cut times on 100% of processed games; every game has exactly 1 + n_OT intermission rows. | timeouts: allow timeout_type = intermission (or a new intermissions table: game_id, kind, start_ts_ms, end_ts_ms, duration_s). | A.01.04 | ontology_audit_inbox007 | new-SR-1 |
| N-SR-02 | Shall | P1 | Store for every clock start the trigger (throw-in touch, jump-ball tap, free-throw touch, period start) and the delay between the trigger frame and the first frame the clock is seen running. | Trigger correct on >= 95% of clock starts in gold-v1 (proposal); median start delay reported per game in s; delays > 1.0 s flagged as timing-mistake candidates (Rule 5-12). | New columns restarts.clock_start_trigger (enum) and restarts.clock_start_delay_s (s). | A.02.02 | ontology_audit_inbox007 | new-SR-2 |
| N-SR-03 | Shall | P1 | Store a running 10-second backcourt count per frame from the start of team control in the backcourt (reset rules per 9-10), and the time each possession reaches the frontcourt. | Backcourt count within +/- 0.2 s of a hand-timed count on >= 95% of possessions (proposal); every 10-second violation in PBP has a count >= 10.0 s. | New column state_frame.backcourt_count_s (s, 0.1 s); possessions.frontcourt_entry_s (s since control). | A.04.13 | ontology_audit_inbox007, espn_analyst, rules_layer | new-SR-4 |
| N-SR-04 | Should | P1 | Store the closely-guarded count per touch: seconds the holder spends holding (not dribbling) in the frontcourt with the same defender within 1.83 m. | Count within +/- 0.3 s of a hand-timed count on >= 90% of 100 labelled touches (proposal); guard distance from tracking (m). | New column touches.closely_guarded_hold_s (s). | A.04.14 | ontology_audit_inbox007 | new-SR-5 |
### N-ST

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-ST-01 | Should | P1 | Store continuous lane time per offensive player (s) and the longest stay per chance, as a measure of post pressure and of 3-second risk. | Lane time recomputes from player positions (lane = \|x\| <= 1.83 m, y <= 5.79 m from the end line) within 0.1 s; every PBP 3-second violation shows a stay >= 3.0 s. | New column chances.max_lane_stay_s and per-player aggregate in profile_snapshots. | A.04.15 | ontology_audit_inbox007, rules_layer | new-ST-1 |
| N-ST-02 | Shall | P1 | The movement-primitive cut vocabulary covers every OFF.F8.2 path cut (UCLA, Iverson, zipper, flash, V, L, shuffle, flex, I, banana, pop-out, thru, 45, weak-side baseline, dive) with one geometric signature each; sequence labels (give-and-go, blind pig, delayed, stampede) are tags on top of primitives. | Every OFF.F8.2 cut has a code and a signature with numbers; F1 >= 0.80 per cut on >= 50 labelled instances (proposal). | see docs/data/gap_closures_round2.md | E.07.02 | gap_closures_round2, ontology_audit_inbox007, data_engineer | new-ST-10, new-ST-3 |
| N-ST-03 | Shall | P1 | Every ball screen stores the screener's arrival code (OFF.F5.3) and arrival speed (m/s, mean over the last 1.0 s). | Code present on 100% of ball screens; >= 80% correct on 200 labelled screens (proposal). | screens.screener_arrival_code; screens.screener_arrival_speed_mps | F.05.02 | gap_closures_round2, ontology_audit_inbox007 | new-ST-12, new-ST-5 |
| N-ST-04 | Should | P1 | Each ball screen stores the OFF.F5.6 spacing tags of the off-ball attackers at the screen moment. | Tags recompute from the snapshot; >= 80% agreement with labels on 200 screens (proposal). | screens.spacing_tags | F.05.04 | gap_closures_round2, ontology_audit_inbox007, espn_analyst | new-ST-13, new-ST-6 |
| N-ST-05 | Should | P1 | Each chance stores paint touches (catch or dribble inside \|x\| <= 1.83 m, y <= 4.19 m) and the time to the first one. | Recomputes from touches/dribbles; first paint touch within +/- 0.20 s of gold (proposal). | chances.paint_touches; chances.first_paint_touch_s | F.09.02 | gap_closures_round2, ontology_audit_inbox007 | new-ST-14, new-ST-7 |
| N-ST-06 | Should | P1 | Each chance stores passes, ball reversals (sign change of x with \|x\| >= 3.0 m both sides) and time from the first frontcourt catch to the shot. | Counts recompute; reversal count agrees with labels on >= 90% of 200 chances (proposal). | chances.n_passes; chances.n_reversals; chances.frontcourt_to_shot_s | F.13.09 | gap_closures_round2, ontology_audit_inbox007, data_engineer | new-ST-15, new-ST-8 |
| N-ST-07 | Shall | P1 | Mismatch hunting: Per ball screen and isolation, whether the offense targeted a specific defender (screener's defender chosen by the offense, re-screen until the switch, clear-out after a switch); per defender per game, the share of the opponent's ball screens he defended and the PPP allowed. | Hunted flag agrees with coach labels on ≥ 80% of 200 actions (proposal); shares recompute from tracks. | ball_screens.hunted_defender_id, defender_game.hunted_share | D.07.05, G.10.02 | espn_analyst | new-ST-A9 |
| N-ST-08 | Shall | P1 | Zone recognition lag: After a defensive scheme change to zone (R-DF-05), the possessions and seconds until the offense runs a zone alignment or zone set (R-ST-24), and the PPP before and after recognition. | Recomputes from scheme_changes and set_instances; reported per change with n. | scheme_changes.offense_recognition_poss, .offense_recognition_s | G.05.01, F.10.01, G.06.01 | espn_analyst | new-ST-A10 |
| N-ST-09 | Shall | P1 | End-of-clock possessions: Possessions whose first shot or turnover comes with shot clock ≤ 7 s, and end-of-period possessions (start ≤ 35 s left), store: the action used (bailout ball screen, isolation, set), the shooter, shot quality (R-VL-04), result. | 100% of qualifying possessions recorded; counts per team per game; descriptive when n is below R-VA-05. | possessions.late_clock_flag, late_clock_action | F.11.04, F.11.03, D.02.03 | espn_analyst | new-ST-A11 |
| N-ST-10 | Shall | P2 | Movement primitives include forward run, defensive slide, crossover run and backpedal, classified from heading minus torso facing (45/135-degree edges) with ankle-crossing for crossover runs, each with mean and peak speed (m/s) and duration (s). | F1 >= 0.80 per class on >= 50 labelled segments each (proposal); torso-facing error <= 20 degrees median (R-DT-10); segments shorter than 0.40 s never stored. | movement_primitives.dir_rel_torso_deg | E.01.02 | gap_closures_round2, ontology_audit_inbox007 | new-ST-9, new-ST-2 |
| N-ST-11 | Should | P2 | Continuity and rule-based system chances store the system code and completed cycles, and team-games report system share of half-court chances. | System label agrees with Aldemir's labels on >= 80% of 100 chances (proposal); cycles recompute from the action sequence. | set_instances.system_code; set_instances.cycles_completed | F.04.01 | gap_closures_round2, ontology_audit_inbox007 | new-ST-11, new-ST-4 |
| N-ST-12 | Should | P2 | Unsupervised action dictionary (possession sketches, [L13]) learned from our tracks beside the role templates, used to find recurring structures the templates miss and to audit template matches. | Dictionary versioned; share of chances whose sketch cluster disagrees with the template match reported per game. | movement_primitives, set_instances | F.13.03 | team_data_scientist | new-ST-S1 |
### N-SY

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-SY-01 | Shall | P0 | Log every game-state change as one typed transition of the rules state machine (config/state_machine.yaml: T01-T24 and subtypes, each with its rule reference and the allowed from -> to pairs), with all four clocks, trigger event and the sources that observed it; the analyst flow state (S0-S11, S4 split into primary transition, early offense, half-court) is a dimension of state_segments, so per-frame flow_state is a view; a disallowed transition is an invariant break. | 0 untyped transitions; every state_segments boundary references one transition; disallowed transitions = 0 on gold-v1 or each explained in review; transition count per type reported per game. | new table state_transitions; new config/state_machine.yaml; state_segments.dimension = flow_state (view state_frame.flow_state) | A.04.09, D.03.02, D.08.01, M.03.02 | data_engineer, espn_analyst | new-SY-E1, new-SR-A6 |
| N-SY-02 | Shall | P0 | Every pull of PBP and of the official box score is stored as a version with a content hash; a diff (plays added, removed, changed; box stats re-credited with old and new value) is computed; downstream tables and published outputs that used a changed value are rebuilt and marked; the official box is re-pulled weekly for processed games. | Re-pull with no change -> 0 rebuilt tables; an injected change -> only dependent tables rebuilt (test); 100% of box diffs logged; dependent outputs re-run within 7 days. | new tables pbp_versions (game_id, source, pull_id, sha256, n_plays, n_added, n_removed, n_changed, known_at_utc) and stat_corrections (game_id, player_id, stat, old, new, seen_utc, source) | M.02.01, A.05.06, M.03.04 | data_engineer, espn_analyst | new-SY-E2, new-DQ-A3 |
| N-SY-03 | Shall | P0 | Events in the same game-clock second carry an explicit order_index and order_source (cbbd_id, video, inferred). | No two events share (game_id, pass, period, game_clock_s, order_index). | events.order_index, events.order_source | M.02.06, D.01.02 | data_engineer | new-SY-E3 |
| N-SY-04 | Shall | P0 | Estimate scorebug lag per game and per field (score, game clock start/stop, shot clock reset, fouls, timeouts) from events whose true time is seen on video, and use lag-corrected times for state while keeping raw read times. | >= 10 events per field per game; lag median and IQR in the run record; after correction the score-change time is within +/- 0.5 s of the ball-through-net frame on >= 95% of makes (raw lag 1.50-2.60 s measured); state uses corrected times on 100% of OCR-sourced changes. | scoreboard_ocr.read_ts_ms (raw); new view scorebug_lag (game_id, field, n, p50_s, p90_s, p95_s); corrected *_time_s columns | L.03.03, L.03.02 | data_engineer, espn_analyst | new-SY-E4, new-SY-A5 |
| N-SY-05 | Shall | P0 | A clock or score correction (5-12, 2-9.13, review) produces a correction event with old value, new value and the affected window; only state segments inside the window are rebuilt. | Louisville 4:06 → 4:07 produces exactly one correction and rebuilds only segments after it. | state_corrections + state_transitions (T18) | A.02.05, A.05.06 | data_engineer | new-SY-E5 |
| N-SY-06 | Shall | P1 | Substitution times from video: Each substitution's time is the dead ball in which the player checked in, read from video (players leaving and entering), replacing the PBP time when they differ; the difference is stored. | Lineups agree with video on ≥ 98% of possessions of the pilot games; every PBP-video difference > 0 s logged. | substitutions.video_time_s, .pbp_time_s, .diff_s | A.11.02, A.11.06, D.07.01 | espn_analyst | new-SY-A4 |
| N-SY-07 | Shall | P1 | Store per team per game the possession count under every source definition in use (ours, FGA - ORB + TO + 0.475 x FTA, Torvik, CBBD, hoopR NCAA engine, Synergy-style chances), with each source's definition text, and report the differences. | All definitions present for 100% of games with PBP; our count within +/- 2 of the formula estimate in >= 95% of games (proposal); every difference > 3 listed for review. | New table possession_counts (game_id, team_id, definition_code, count, definition_ref) or columns on team_box. | A.04.04 | ontology_audit_inbox007 | new-SY-3 |
### N-VA

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-VA-01 | Shall | P0 | A timing gold set on game 1: 100 hand-labelled instants (net frames, whistles, throw-in touches, clock starts, releases) used to measure every latency and alignment error in this review. | 100 labels, each with frame index and labeller; all latency metrics in the run record cite it. | review_labels (label_kind = timing) | M.04.03, A.02.06, L.06.11 | data_engineer | new-VA-E1 |
| N-VA-02 | Shall | P0 | A held-out game list per season is registered before any model is fitted: ≥ 20% of games with footage, chosen by game (not possession), stratified by home/away and opponent tier; no hyperparameter, threshold or template is tuned on them. | Register file with date and hash exists before the first fit; every run record lists whether held-out games were touched (must be "no" except final evaluation). | registry/holdout_games.csv (new), run_records.holdout_touched | H.05.08, M.04.04 | team_data_scientist | new-VA-S1 |
| N-VA-03 | Shall | P1 | Temporal leakage test for every model: features for time t use only data with timestamp ≤ t (frames, events, ratings); smoothing filters used as features are causal (no centred windows); a test perturbs all data after t and requires identical predictions at t. | Test passes for 100% of model features; failing features listed in the run record. | run_requirement_results | M.02.05 | team_data_scientist | new-VA-S2 |
| N-VA-04 | Shall | P1 | Reliability per player-level metric: split-half (odd vs even games) correlation across players, and the n (events) at which reliability reaches 0.70; player-level displays hide metrics below that n. | Table with reliability and n70 per metric per season. | dq_reports (metric_reliability section) | H.04.03, M.04.05 | team_data_scientist | new-VA-S3 |
| N-VA-05 | Shall | P1 | Model monitoring: after each new game, calibration (10-bin ECE) and input drift (PSI per feature, R-DQ-08) are recomputed for every deployed model; alert when rolling 10-game ECE > 0.05 or any key feature PSI > 0.25. | Alert log per game; zero silent model updates. | run_records, dq_reports | M.03.05, H.05.05 | team_data_scientist | new-VA-S4 |
| N-VA-06 | Shall | P1 | Broadcast error budget: each derived metric is recomputed on simulated degradations (position noise σ = 0.3, 0.5, 1.0 m; 30 fps; weak-side players dropped as in our coverage maps) using licence-compatible full tracking or our own best frames; metrics that move > 10% at our measured σ are labelled "not estimable from broadcast". | Report with the change (%) per metric per degradation. | docs/ report + dq_reports | I.03.06, L.02.04, M.04.04 | team_data_scientist | new-VA-S5 |
### N-VI

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-VI-01 | Shall | P0 | Each video file has a cut map: video stretches with the game-clock range they cover and the cut type (commercial, timeout trim, half time trim, replay insert). | Covers 100% of game clock for both first games; stretches of live play never overlap in game clock. | new table video_segments | L.01.02, L.02.06, A.02.06 | data_engineer | new-VI-E1 |
| N-VI-02 | Shall | P0 | Store per frame which pipeline stages ran (bitmask), so "not processed" differs from "nothing found". | 100% of frames carry the mask; a detection count of 0 with the detector bit unset is never read as "no players". | frames.stage_mask | L.02.04, M.05.03 | data_engineer | new-VI-E2 |
| N-VI-03 | Should | P1 | Every frame carries a camera-view label (main high side, reverse angle, baseline low, end high, backboard, rail, skycam, handheld iso, bench, crowd, studio, graphic) from the recovered camera centre where mapping resolves and from an image classifier otherwise; the 9-class shot type is unchanged. | >= 90% correct on 500 labelled non-main frames (proposal); camera-centre rules unit-tested on the registered cameras. | frames.camera_view | L.02.02 | gap_closures_round2, ontology_audit_inbox007 | new-VI-5, new-VI-2 |
| N-VI-04 | Should | P1 | Replay segments are linked to the live event they replay with the time offset (s) and camera view, as evidence for reviewers and labellers only. | >= 90% of replay segments linked on 3 games (proposal); 0 statistics computed from rows with events.from_replay_frame = true. | frames.replay_of_event_id; frames.replay_offset_s | L.02.07 | gap_closures_round2, ontology_audit_inbox007, espn_analyst | new-VI-6, new-VI-3 |
| N-VI-05 | Should | P1 | Broadcast stat graphics are read as weak labels (kind, text, parsed fields, subject player, confidence) in the score-reading table and every disagreement with the state record raises a flag; graphics never overwrite state. | >= 95% character accuracy on 200 labelled graphics (proposal); 100% of disagreements logged as scoreboard_flags. | scoreboard_ocr.graphic_kind; scoreboard_ocr.graphic_text_raw; scoreboard_ocr.graphic_parsed_json; scoreboard_ocr.graphic_subject_player_id | L.03.04 | gap_closures_round2, ontology_audit_inbox007, espn_analyst | new-VI-7, new-AU-1 |
| N-VI-06 | Should | P2 | Each venue row lists its secondary cameras with view kind and estimated 3-D centre (m), from frames whose court mapping resolves, so non-main frames can be mapped later. | Every registered camera has >= 20 supporting frames; centre within 2.0 m of a hand estimate from seating charts or broadcast stills for >= 90% of cameras (proposal). | venues.secondary_cameras | B.03.04 | gap_closures_round2, ontology_audit_inbox007 | new-VI-4, new-VI-1 |
### N-VL

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-VL-01 | Shall | P1 | Each shot stores its shot-making residual (points minus shooter-agnostic expected points of R-VL-04) and, when the ball trajectory is available, a trajectory-based make probability (entry angle, depth, left-right) to reduce variance; shooter profiles report the shrunk residual per attempt with n and a 95% interval as of each date. | Residual stored for 100% of shots with xPts; per-shooter estimate shrunk toward the position-group prior with n and interval; trajectory make probability calibrated (10-bin ECE <= 0.05) on held-out games before use. | shots.shot_making_residual, shots.p_make_traj; profile_snapshots | H.03.05 | gap_closures_round2, team_data_scientist, ontology_audit_inbox007, espn_analyst | new-VL-3, new-VL-S1, new-VL-1 |
| N-VL-02 | Should | P1 | Crash vs retreat decision per attacker at each missed-shot release: crashed (moved toward the rim ≥ 1.0 m in 1.0 s) or retreated, with the ORB probability gained and the transition-defence cost (opponent value after a DREB) [L5]. | Decision label agrees with hand labels on ≥ 85% of 200 cases; value fields filled when ≥ 8 players are mapped. | rebounds, transition_phases | F.12.01, E.05.04 | team_data_scientist | new-VL-S3 |
| N-VL-03 | Shall | P2 | Defensive value credits go to on-ball and help defenders for contests, rotations, rim deterrence, closeouts, ball pressure, denial, box-outs and charges, each with its counterfactual basis, summed per 100 defensive possessions with an interval. | Credits for every chance sum to its defensive value change within 0.01 xpts (bookkeeping test); interval on every player value; players ranked only with n >= 100 defensive possessions. | shots.rim_defender_id; value_credits.counterfactual_basis | H.04.06 | gap_closures_round2, ontology_audit_inbox007 | new-VL-4, new-VL-2 |
| N-VL-04 | Should | P2 | Each shot stores its rim defender (within 1.52 m of the rim and of the shooter at release), and player profiles report rim field-goal percentage allowed and rim attempts deterred per 100 possessions. | Rim defender agrees with labels on >= 90% of 100 rim attempts (proposal); rim_dfg_pct reported with n and 95% interval. | shots.rim_defender_id; value_credits.counterfactual_basis | H.04.06 | gap_closures_round2 | new-VL-5 |
| N-VL-05 | Shall | P2 | Rebound decomposition for every missed try: positioning (rebound probability per player from positions at rim contact), hustle (change from release to rim contact), conversion (secured given position) [L4]. | Probabilities sum to 1 per miss within 1e-6; calibrated ECE ≤ 0.05 on held-out games. | rebounds (new columns), value_credits | E.05.05, H.03.07, E.05.03 | team_data_scientist | new-VL-S2 |
### N-VZ

| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| N-VZ-01 | Should | P1 | Half-time packet: One page per team: score, four factors, runs, foul trouble, bonus and timeouts, set and coverage mix, top 3 possessions by value change with clip references, each number linked to frames. | Produced within 600 s after the first-half video is available on the 3 pilot games (proposal); 100% of counting stats equal the official half-time box. | results/<game_id>/halftime_packet | L.05.02, M.06.09 | espn_analyst | new-VZ-A1 |
| N-VZ-02 | Should | P1 | Post-game notes sheet: Ten notes per game, each a one-sentence finding with its number, n, definition and clip reference; ranked by value change and novelty. | Produced within 3,600 s after the full video is available (proposal); passes N-DQ-05. | results/<game_id>/postgame_notes | L.05.02, L.05.04 | espn_analyst | new-VZ-A2 |
| N-VZ-03 | Shall | P1 | Clip index: Every event, action and possession row carries clip in and out times (video s), a key frame (screen moment, help moment, release), and links to replay segments of the same play (N-VI-04). | 100% of event rows have clip times; an audit of 100 pulled clips finds the event in ≥ 95%. | clip_index (row_ref, in_s, out_s, key_frame, replay_ids) | L.05.01, L.02.07 | espn_analyst | new-VZ-A3 |
| N-VZ-04 | Should | P1 | Telestrator freeze-frame: For any possession and moment, a top-down diagram of all 10 players and the ball, with arrows of the next 2 s of movement and labels from the broadcast vocabulary layer. | Renders from the state tables for any frame of a processed game; positions match the state within 0.1 m. | viz template freeze_frame | L.05.01, L.05.03 | espn_analyst | new-VZ-A4 |

### 5.x Proposals absorbed into existing IDs

| Old proposal | Absorbed into | Note |
| --- | --- | --- |
| new-DF-S3 | R-EV-07 | contest unknown, never imputed |
| new-DS-1 | R-DS-05 | player-level, bitemporal crosswalk |
| new-EN-E4 | R-EN-07 | partition layout with manifests and current pointer |
| new-EN-E5 | R-EN-01 | one dialect and validator |
| new-EV-3 | R-EV-10 | backcourt over-and-back added to the turnover list |
| new-EV-4 | R-EV-10 | elbows added to the turnover list |
| new-EV-S1 | R-EV-06 | help timing on drives |
| new-IV-12 | R-IV-10 | timeout allotment per media format |
| new-IV-34 | R-IV-13 | court and ball-height bounds join the shared physics key |
| new-MD-E1 | R-MD-08 | clock_map becomes the R-MD-08 rewrite |
| new-MK-E1 | R-MK-27 | RESOLVED in code 2026-10-18 (dedup_key includes source_event_id; CBBD reported rows keyed on scheduled tip); regression tests in tests/markets/test_engineer_review_fixes.py |
| new-MK-E2 | R-MK-27 | RESOLVED in code 2026-10-18 (store skips keys already present: idempotent across runs) |
| new-RF-3 | R-RF-03 | R-RF-03 rewrite carries the 2026-27 foul classes and the legacy "intentional" mapping |
| new-RG-E1 | R-RG-11 | shared private-root guard and pre-commit hook; markets RawStore part fixed 2026-10-18 |
| new-SY-2 | R-SY-08 | full shot-clock cause list (41 causes, config/vocab/shot_clock_resets.yaml) |
| new-SY-E6 | R-MD-08 | UTC from monotone wall clock only |
| new-VL-S4 | R-VL-01 | value layers stored side by side |

## 6. Game-flow spine

The rules-exact state machine of a game and a possession (data engineer T01-T24 and the analyst's S0-S11, rule numbers from the 2026-27 book as verified in `config/invariants.yaml` and `config/vocab/*.yaml`). For each transition, the requirements that detect it, time it and analyse it. T00 is the observability dimension (the broadcast director decides whether we see anything at all).

| T | From -> to | Trigger | Rule | Clocks | Detection | Timing | Analysis |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T00 | any -> observed / not observed | camera cut, replay, graphics, condensed-replay edit | none (broadcast director) | video time stops being linear in game clock | N-VI-03, R-VI-03, R-VI-04, R-VI-05 | N-VI-01, N-VI-02, R-MD-08 | N-VA-06, R-PL-05, R-VI-06 |
| T01 | S0 pre-period / S1 jump ball -> S6 loose ball (no team control) | toss leaves the official's hand; legal tap | 6-1.2.a, 6-2, 6-3, 5-10.2.b | GC starts on the legal tap; SC off until control | N-EV-06, R-DT-15, R-EV-14 | N-SR-02, R-MD-08, R-SR-01 | N-IV-16, R-EV-14, R-MD-12 |
| T02 | S6 no control -> S3/S4 team control | player gains control after a jump ball or a try | 4-9, 2-11.5.b, 5-10.3.b | SC starts (30, or 20 flat after ring contact) | R-BL-02, R-MD-02, R-SR-06 | N-IV-02, R-MD-06, R-SY-08 | R-MD-04, R-SR-05, R-SY-04 |
| T03 | S3/S4 team A control -> S3 team B control (live) | steal, defensive rebound, loose-ball recovery | 2-11.6.b.1, 2-11.6.b.4, 4-9 | SC to 30 on control; GC runs | R-BL-02, R-EV-08, R-EV-09, R-EV-10 | N-SY-01, N-SY-03, R-SY-08 | N-DF-05, R-TR-08, R-TR-09, R-TR-22, R-TR-26, R-VL-01 |
| T03a | S3 backcourt control -> S4 frontcourt control | ball and both feet of the dribbler (or holder) in the frontcourt | 9-10, 9-12.1-3 | GC and SC run; 10-s count stops | N-MD-06, N-SR-03 | N-IV-02, N-SR-03 | N-DF-02, R-ST-19, R-TR-20 |
| T03b | S4a primary transition -> S4b early offense -> S4c half-court | 3 defenders back; defense set (all 10 in the half-court, every attacker guarded within 2.0 m goal-side for 1 s) | project definition (R-TR-08/09), no rule | GC and SC run | R-DF-20, R-TR-08, R-TR-12 | R-TR-01, R-TR-20 | N-ST-08, R-ST-05, R-TR-09, R-TR-18, R-TR-24 |
| T04 | S4 team control -> S5 try in flight | release of a try (the try starts with the shooting motion) | 5-1.10, 6-6.1, 4-9.4 | GC and SC keep running; ball stays live through a whistle until the try ends | N-EV-03, R-BL-04, R-EV-07 | N-IV-07, R-BL-04, R-MB-06 | N-MD-12, N-VL-01, N-VL-02, R-CO-01, R-EV-07, R-VL-04 |
| T05 | S5 try in flight -> S7 dead (made goal) -> S2 throw-in | ball passes through the basket | 6-5.1.a, 5-1, 5-11.9, 2-10.12 | GC keeps running except in the last 59.9 s of the 2nd half and OT; SC to 30 on the opponent's inbound touch | N-MB-01, R-BL-05, R-MB-01, R-MB-02, R-MB-03 | N-IV-19, N-IV-24, N-SY-04, R-MB-04, R-SB-03 | N-EV-05, R-DF-18, R-MD-17, R-SR-02, R-TR-23 |
| T06 | S5 try in flight (ring contact) -> S4 offensive control: new chance, same possession | offensive rebound after ring or flange contact | 2-11.6.d.1 | SC flat 20 s whatever was left | N-EV-04, R-EV-08, R-MB-07 | N-IV-03, R-SY-08, R-SY-09 | N-VL-05, R-DQ-06, R-SY-05, R-VL-01 |
| T07 | S5 try in flight (no ring contact) -> S4 offensive control: same chance | airball rebounded by the offense | 2-11 (no reset listed), 9-11 | SC continues; violation if it expires | R-BL-08, R-MB-07 | N-IV-05, N-IV-07 | R-DQ-06, R-SY-05 |
| T08 | S5 try in flight / S6 loose -> S3 defensive control | defensive rebound (incl. team and dead-ball rebounds as recorded) | 2-11.6.b.4, 4-30.1 | SC 30 | N-EV-04, R-EV-08 | N-SY-03, R-SY-08 | N-VL-02, N-VL-05, R-DQ-06, R-TR-08 |
| T09 | S3-S6 live -> S7 dead (foul) | whistle for a foul | 5-11.1.a, 6-5.1.d (6-6.1 if a try is in flight), 4-15, 10-1 | GC and SC stop; SC per the reset table | N-RF-04, N-RF-05, R-RF-01, R-RF-02, R-RF-03, R-RF-04 | N-RF-12, R-MD-08, R-SR-01 | N-CC-01, N-CG-02, N-IV-11, N-IV-25, N-RF-01, R-MD-07, R-MD-16, R-SR-03 |
| T10 | S7 dead (foul) -> S8 free-throw sequence | foul with a free-throw award (shooting, 7th team foul one-and-one, 10th double bonus, technical, flagrant) | 8-2.1, 8-2.2, 10-1 Penalty, 10-3, 10-4 | GC stopped through the free throws | R-DT-13, R-SR-09 | N-IV-08, N-IV-09, N-IV-27, N-IV-32 | N-CH-01, N-IV-30, R-SR-09 |
| T11 | S7 dead (foul or violation) -> S2 throw-in pending | common foul before the bonus, player-control foul, violation, out of bounds | 10-1 Penalty a, 7-3.2, 7-2, 9-x | SC 30 (backcourt or change of control) or max(20, left) (defensive foul or kicked ball, frontcourt) | N-BL-01, R-DT-14, R-DT-19, R-SR-08 | N-IV-04, N-IV-15, R-SY-08 | N-EV-02, R-DQ-06, R-SY-04 |
| T12 | S8 FT k of n -> S8 FT k+1 / S6 live rebound / S2 throw-in | each attempt result | 8-5, 8-6, 8-7, 5-10.2.c | GC starts only when a missed last FT is legally touched | R-SR-09 | N-IV-10, N-SR-02 | R-DQ-06, R-SY-05 |
| T13 | S3/S4 live -> S7 dead (violation) -> S2 throw-in | travel, illegal dribble, 3 s, 5 s closely guarded, 10 s backcourt, backcourt, kicked ball, out of bounds, elbows | 6-5.1.g, 9-3 to 9-14, 7-1, 7-2 | GC and SC stop; SC per the reset table | N-BL-01, N-DT-03, N-EV-01, N-MD-06, N-SR-03, N-SR-04, N-ST-01, R-EV-10 | N-IV-28, N-IV-29, R-SY-08 | N-ST-09, R-DQ-06, R-VL-11 |
| T14 | S3-S6 live -> S7 dead (held ball) -> S2 arrow throw-in | held ball | 6-5.1.c, 6-3, 6-4 | SC per arrow: no reset / 30 / 20 (2-11.6.a.4, b.3, d.4); arrow flips when the AP throw-in ends | R-DT-15, R-EV-14 | N-IV-05, R-SY-08 | N-IV-16, R-MD-12 |
| T15 | S2 throw-in pending -> S3/S4 live, clocks running | ball at the thrower's disposal, then legal touch inbounds | 6-1.2.b, 7-6.6, 5-10.2.a, 5-10.3.a, 5-10.2.d | GC and SC start on the touch; >= 0.3 s off in the last 59.9 s | N-EV-02, R-DT-14 | N-IV-02, N-IV-14, N-IV-19, N-SR-02 | N-DF-02, R-DF-18, R-MD-03, R-TR-21 |
| T16 | S7 any dead ball (or live with control, last 2:00 for the head coach) -> S9 timeout (team or media) | request granted, or first dead ball at or after a media mark | 5-11.3, 5-11.4, 5-14, 5-14.10.c-e | stopped; timeouts left decrease; SC no reset (2-11.6.a.3) | R-EV-11, R-EV-15 | N-IV-12, N-IV-23, R-IV-10, R-MD-13, R-SR-04 | N-CC-02, N-CH-02, N-HY-01, R-CC-02, R-CH-06, R-SY-04 |
| T17 | S3-S9 -> S10 review / coach's challenge | official review or challenge | 11-2, 11-3, 11-4, 5-15.1.e | frozen; may correct score, clock, possession; failed challenge costs the timeout | R-EV-16, R-RF-07 | N-IV-13, N-IV-22 | N-SY-05, R-EV-16 |
| T18 | any state value -> corrected value | timing or scoring correction | 5-12.1-5, 2-9.13, 11 | GC may go up (Louisville 4:06 -> 4:07, measured); never carried across halves | N-SY-05, R-SB-01, R-SB-02 | N-IV-22, R-IV-05 | N-DQ-04, N-SY-02 |
| T19 | SC on / off -> SC off / on at 20 | game clock below a shot-clock period; 2-11.6.d situation | 2-11.2, 2-11.8 | SC display blank; reactivated at 20 s | R-SY-01 | N-IV-06 | N-ST-09, R-PE-07, R-SR-11 |
| T20 | S3-S6 live -> S11 end of period | game clock reaches 0.0 (try in flight completes) | 5-7, 5-11.2.a, 5-1.19 | GC 0.0; tap-only rule at <= 0.3 s | N-AU-01, R-SY-01 | N-IV-19, N-IV-20, R-MB-06 | N-ST-09, R-PE-07, R-SR-11 |
| T21 | S11 end of period -> S0 intermission -> next period | half time; 1-minute intermission before each extra period | 5-8, 5-9, 6-3.6 | team fouls reset at the 2nd half only; extra periods continue them; baskets change at half only | N-SR-01 | N-IV-17, N-IV-18, R-IV-09 | N-VZ-01, R-CH-06 |
| T22 | S7 dead (clock stopped) -> S7 dead (new lineup) | substitute beckoned | 3-6, N-IV-30, N-IV-31 | none | N-SY-06, R-EV-11 | N-IV-30, N-IV-31 | N-CC-01, N-CH-02, N-MD-09, R-CC-03, R-MD-15 |
| T23 | S3-S6 live -> S7 dead (injury, blood, official stoppage) | official suspends play | 5-11.2.b, 5-11.6-5-11.8 | stopped; SC no reset (2-11.6.a.2) | R-EV-11 | N-IV-05 | N-FD-04 |
| T24 | S11 last period -> final / forfeit | last period ends with a winner | 5-6, N-IV-33 | none | N-FD-03, R-FD-01 | N-IV-33 | N-DQ-04, R-DQ-01, R-DQ-06 |

Decision points inside the flow (where a team reacts), and the requirements that capture each decision:

| Decision point | Decider | Window | Requirements |
| --- | --- | --- | --- |
| Push or pull back after a change of control | ball handler, team rule | 0-3 s after the secure | N-DF-05, R-TR-16, R-TR-24, R-TR-26 |
| Inbound fast after a make; press or not | inbounder, defensive coach | 0-3 s after the net; pre-planned | N-DF-02, R-DF-12, R-DF-18, R-TR-21, R-TR-23 |
| Set call | coach or point guard | dead ball or half-court crossing | N-MD-11, R-ST-05, R-ST-07 |
| Ball-screen coverage and handler read | X-big, X-ball; handler | t0 - 1.0 s to t0 + 2.0 s | N-DF-06, N-ST-07, R-DF-06, R-DF-16, R-ST-17, R-ST-20 |
| Catch: shoot, pass, drive, hold | receiver | 0.2-3 s per touch | N-MD-12, R-CO-01, R-VL-05 |
| Help or stay on a drive or skip | help defender, low man | 0.2-1.5 s after the trigger (calibrate) | R-CO-02, R-DF-08, R-EV-06 |
| Double the post | defensive plan | 0-1.5 s after the post catch | N-DF-08, R-DF-07 |
| Crash or get back at the release | all 10 players | at release to rim contact | N-EV-04, N-VL-02, R-EV-08 |
| Foul or not late (take foul, foul up 3, foul to extend) | defender, coach | last 60 s | R-PE-07, R-SR-11, R-TR-25 |
| Timeout or challenge | head coach | any dead ball; live in the last 2:00 | N-CC-02, R-CC-02, R-EV-16 |
| Substitution, foul-trouble sit | head coach | next dead ball | N-CC-01, N-SY-06, R-CC-03 |
| Scheme change (zone, press, switch) | defensive coach | next dead ball, 1-3 possessions after the trigger | N-CH-02, N-DF-04, N-HY-01, N-ST-08, R-DF-19 |
| End of clock: hold, two-for-one, last shot | coach, handler | 33-45 s window; SC <= 7 s | N-ST-09, R-PE-07, R-SR-11 |
| Whistle or play on | calling official | contact to whistle < 1 s (unverified) | N-RF-09, N-RF-12, R-DT-12 |

Coverage check: every transition has at least one detection, one timing and one analysis requirement; the spine cites 168 distinct IDs (89 existing, 79 N-IDs).

## 7. Minimum build for the first two games (P0 only)

Games: UConn 401856571 (5,188 s, 155,492 frames) and Louisville 401856531 (5,394 s, 161,653 frames), both VP9 1920x1080 at 29.97 fps constant, condensed replays (`results/w3_intake/`).

**Reconciliation with the engineer's 43-table recommendation.** The engineer's 43 (40 existing specs + `clock_map`, `state_transitions`, `state_segments`; markets counted once) is kept. Four small tables from his own "what is missing" list are added because P0 requirements write to them: `video_segments` (N-VI-01), `pbp_versions` and `stat_corrections` (N-SY-02, which also carries the analyst's stat corrections), `stage_outputs` (N-EN-01). `frames.stage_mask` (N-VI-02) is a column. The analyst and scientist P0 additions change columns, not tables (possession situation flags, contest unknown, sigma columns). Everything else stays a proposal until the gates it depends on pass.

| Area | Tables |
| --- | --- |
| registry | games, teams, players, rosters, jersey_history, id_crosswalk, venues, game_officials |
| video | video_files, frames (+stage_mask), video_segments (new: cut map) |
| sync | scoreboard_ocr, clock_map (new), pbp_versions (new), stat_corrections (new) |
| state | state_transitions (new), state_segments (new: state_frame becomes a view), state_second (view-able), state_corrections (proposal) |
| events | events (+order_index), substitutions, lineup_stints, possessions, chances, score_events, shot_clock_resets, timeouts, restarts, free_throws, fouls, shots, rebounds, turnovers, made_basket_events |
| quality | scoreboard_flags, raw_pulls, quarantine_rows, run_records, run_requirement_results |
| vision | detections, tracks, player_positions (+sigma columns), ball_states |
| review | review_queue, review_labels (+timing gold) |
| engineering | stage_outputs (new: content-address registry) |
| markets | market tables (already coded) (code) |

Deferred (specs stay, no build): belief_states, coach_quiz, position_forecasts, possession_value (layer 3), value_credits, predictions, simulation_runs, profile_snapshots, player_shooting_sector_ring, commentary_segments, appearance_cards, bench_events, scheme_states, scheme_changes, set_instances, set_instance_phases, play_calls, configuration_snapshots, movement_primitives, actions, screens, drives, dribbles, reaction_events, defensive_matchups, defensive_events, frame_geometry, post_touches, box_outs, accel_efforts, load_stint_bins, transition_numbers, transition_roles, official_positions, whistles, audio_seconds, identity_confusions, hypothesis_results, pregame_cards, runs, fakes, source_definitions.

P0 requirements, new (56): N-CG-01, N-CS-01, N-DQ-01, N-DQ-02, N-DQ-03, N-DQ-04, N-DT-01, N-EN-01, N-EN-02, N-EN-03, N-EN-04, N-FD-01, N-FD-02, N-IV-01, N-IV-02, N-IV-03, N-IV-04, N-IV-05, N-IV-06, N-IV-07, N-IV-08, N-IV-09, N-IV-10, N-IV-11, N-IV-12, N-IV-13, N-IV-14, N-IV-15, N-IV-16, N-IV-17, N-IV-18, N-IV-19, N-IV-20, N-IV-21, N-IV-22, N-IV-23, N-IV-24, N-IV-25, N-IV-26, N-MD-01, N-MD-02, N-MD-03, N-MD-04, N-MD-05, N-RL-01, N-RL-02, N-RR-01, N-SY-01, N-SY-02, N-SY-03, N-SY-04, N-SY-05, N-VA-01, N-VA-02, N-VI-01, N-VI-02.

P0 requirements, existing (222, merged verdict applies): R-RR 01, 02, 03, 04, 05, 06, 07, 08; R-DQ 01, 02, 03, 04, 05, 06, 07, 09, 10; R-DS 01, 02, 04, 05, 06, 10, 11, 13, 14, 15; R-RG 11, 01, 02, 03, 04, 05, 06, 07, 08, 09, 10; R-FD 01, 02, 03, 05, 08, 09, 10; R-MD 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 12, 13, 15, 16, 17, 18, 19; R-ID 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11; R-VI 01, 02, 03, 04, 05, 06, 07, 09, 11, 12, 13, 14, 15, 16; R-CG 01, 02, 03, 04, 05, 06, 07, 08; R-DT 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 14, 15, 17, 19; R-BL 01, 02, 03, 04, 05, 06, 07; R-GT 01, 02, 03, 04, 05; R-SY 01, 02, 03, 04, 05, 06, 08, 09, 10; R-EV 01, 03, 07, 08, 09, 10, 11, 12, 14, 15, 16; R-RF 01, 02, 03, 07; R-SR 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 13, 14, 15; R-IV 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16; R-SB 01, 02, 03, 04; R-MB 01, 02, 03, 04, 05, 06, 07; R-PL 13; R-EN 01, 02, 03, 04, 05, 06, 07, 08; R-CD 01, 02, 03, 04, 05; R-HR 01, 02, 03, 04, 05, 06, 07, 08, 12; R-CS 01, 02, 04, 05, 06, 09, 10; R-VA 01, 02, 03, 04, 05, 06, 09.

Build order (each step testable on game 1 before game 2):

1. Registry and rules: games registry fields (N-FD-01, N-FD-02), rules edition (N-RL-01, N-RL-02), court constants (N-CG-01), crosswalk (R-DS-05).
2. Lake mechanics: content addressing, atomic writes, deterministic IDs, DAG runner, run logs (N-EN-01, N-EN-02, N-EN-03, N-EN-04, N-RR-01).
3. Video intake and cut map (R-VI-01, R-VI-02, N-VI-01, N-VI-02); scorebug OCR (R-SY-01) with lag model (N-SY-04, R-SB-03).
4. PBP versions and ordering (N-SY-02, N-SY-03); clock map (R-MD-08); timing gold set of 100 instants (N-VA-01).
5. State: transitions and segments (N-SY-01, N-MD-01), team-neutral stamps (N-MD-02), four clocks and known_at (N-MD-03, N-MD-04), invariants on transitions (N-IV-01 and the rules invariants).
6. Events from PBP plus scoreboard: possessions, chances (R-DQ-06, R-SY-05), shot-clock resets (R-SY-08), fouls, free throws, timeouts, restarts, made baskets (R-MB-*), discrepancy flags (R-SB-*), end-of-game reconciliation (N-DQ-04).
7. Vision: detections, tracks, identity within the PBP lineup (R-ID-03), positions with sigma (R-CG-08, N-DT-01), ball states; physics key (R-IV-13).
8. Quality: invariant break rates (N-DQ-01), event-volume sanity (N-DQ-03), game-1 regression fixture (N-DQ-02), throughput and size per stage (N-CS-01), held-out register (N-VA-02).

## 8. Code findings already resolved

The engineer's markets findings M1-M5 are fixed in `src/msu_alpha/markets/` with regression tests in `tests/markets/test_engineer_review_fixes.py` (uncommitted working-tree changes on 2026-10-18). They are recorded as resolved in R-MK-27, R-MK-13 and R-RG-11; the matching proposals (new-MK-E1, new-MK-E2, new-RG-E1) are absorbed, not renumbered.

| # | File | Finding | Status | Requirement |
| --- | --- | --- | --- | --- |
| M1 | src/msu_alpha/markets/models.py | dedup_key without source_event_id | resolved 2026-10-18 | R-MK-27 |
| M2 | src/msu_alpha/markets/sources/cbbd.py | CBBD reported open/close stamped with fetch time | resolved 2026-10-18 (finished games keyed on scheduled tip) | R-MK-27 |
| M3 | src/msu_alpha/markets/store.py | de-duplication per batch only | resolved 2026-10-18 (existing keys skipped across runs) | R-MK-27 |
| M4 | src/msu_alpha/markets/raw_store.py | RawStore did not call ensure_private | resolved 2026-10-18 | R-RG-11 |
| M5 | src/msu_alpha/markets/raw_store.py, models.py | sha256 computed after redaction | resolved 2026-10-18 (sha256_received added) | R-MK-13 |
| M6 | src/msu_alpha/markets/store.py, raw_store.py | JSONL appends without atomic rename | open | N-EN-02 |
| M7 | src/msu_alpha/markets/store.py | read() without partition pruning | open (performance only) | none |
| M8 | src/msu_alpha/markets/models.py | schema_version not in Parquet metadata | open | R-MK-31 |

## 9. Decisions for Aldemir

Conflict decisions first (K01-K29), then the open questions of the six inputs, de-duplicated (D01-D45). Recommendation in brackets.

- **K01** Approve physics key: speed 10.0 m/s hard + 9.0 m/s soft flag (>= 0.3 s windows), acceleration 12 m/s² over >= 0.5 s, to 8.0 m/s² after sigma <= 1.0 m/s²? [see section 2] (conflict K01)
- **K02** Set the scorebug window to 4.0 s initial, then per-field p99 + 1.0 s (3-15 s bounds)? [see section 2] (conflict K02)
- **K03** Adopt the resolvability gate (sigma <= 0.5 m/s², >= 0.5 s windows, change-point onsets, no jerk)? [see section 2] (conflict K03)
- **K04** Approve coverage gates: coarse 85% then 90%; fine 75% on 300 screens/5 games; publish fine only at confidence >= 0.8? [see section 2] (conflict K04)
- **K05** Primary run = register (net >= 8 in 120 s); broadcast display threshold 8 or 6? [see section 2] (conflict K05)
- **K06** Clutch = <= 300 s and margin <= 5 (late_240 kept as a separate flag)? [see section 2] (conflict K06)
- **K07** Make frame +/- 2 frames on 95% (and +/- 1 frame on 80% as stretch)? [see section 2] (conflict K07)
- **K08** Confirm: a shot-clock reset inside a possession (defensive foul, kicked ball) opens a new chance? [see section 2] (conflict K08)
- **K09** Approve state_segments + state_transitions as stored truth, state_frame as a view? [see section 2] (conflict K09)
- **K10** Foul-trouble default 2/3/4 (analyst) or 2/4, or a coach-supplied MSU rule? [see section 2] (conflict K10)
- **K11** Approve two stored shot-quality versions (agnostic for quality, adjusted for prediction)? [see section 2] (conflict K11)
- **K12** Display threshold: n70 per metric, n >= 30 until measured? [see section 2] (conflict K12)
- **K13** Single coverage key at 0.70? [see section 2] (conflict K13)
- **K14** Approve tempo + start type (exclusive) + situation flags (multi-label)? [see section 2] (conflict K14)
- **K15** Off-screen estimates at 10 Hz (not per frame)? [see section 2] (conflict K15)
- **K16** Reaction onset by change-point, +/- 0.10 s on 80% of 100 labels? [see section 2] (conflict K16)
- **K17** Start drift verdicts at game 11? [see section 2] (conflict K17)
- **K18** Adopt the 41-cause shot-clock list (add 8 causes to invariants.yaml)? [see section 2] (conflict K18)
- **K19** Short corner = 3.5 < |x| <= 6.0 m, y <= 1.50 m, or define from MSU film first? [see section 2] (conflict K19)
- **K20** Approve layered value with the G1-G4 gate on layer 3? [see section 2] (conflict K20)
- **K21** Pulled-player windows = first dead ball and 60 s, with matched baseline? [see section 2] (conflict K21)
- **K22** Contest bins 0-0.6 / 0.6-1.2 / 1.2-1.83 / > 1.83 m? [see section 2] (conflict K22)
- **K23** Is the half-time deadline a pilot goal, or offline-only this season? [see section 2] (conflict K23)
- **K24** Officials' roles at 1 Hz plus 10 Hz around whistles? [see section 2] (conflict K24)
- **K25** Adopt exact edge-correct court constants (1.270 m restricted area, 12.700 m frontcourt) and lift verified: false? [see section 2] (conflict K25)
- **K26** Adopt the FT-line-extended reading of Rule 7-3.2.b? [see section 2] (conflict K26)
- **K27** Store "shooting" as a context flag, not a foul class? [see section 2] (conflict K27)
- **K28** Garbage time: WP rule primary, CTG-adapted and source flags kept as views? [see section 2] (conflict K28)
- **K29** Adopt the N-<FAMILY>-nn renumbering? [see section 2] (conflict K29)
- **D01** Adopt the 13 rule-number corrections and the 34 proposed invariants of config/invariants.yaml (renumbered N-IV-02..N-IV-33; two absorbed into R-IV-10 and R-IV-13) into the live doc? [yes] (inbox 006 Q10, inbox 007, quality review C22)
- **D02** Adopt the new family R-RL (rules edition per game) and drop the foul type "intentional"? [yes] (inbox 006 Q11, inbox 007 Q1-Q2, fouls.yaml)
- **D03** Confirm R-IV-02 / R-FD-08 / R-DT-12 / R-SR-07: two or three officials (three expected in D-I)? [yes] (inbox 006 Q12, quality review C1, all three perspectives)
- **D04** Approve the first build of the engineer's 43 tables (incl. new clock_map, state_transitions, state_segments) plus video_segments, pbp_versions, stat_corrections and stage_outputs, and defer the other specs until their gates pass? [yes] (data engineer 4.1)
- **D05** Approve the extra state_corrections table and one pass enum {blind, anchored, pbp_only, none}? [yes] (inbox 006 Q14, data engineer V4)
- **D06** Approve the global-metadata additions (pass, video_id, shot_clock_status, per-team bonus, timeouts by length, challenge state, arrow, reverse_angle), stored team-neutral with MSU views? [yes, team-neutral] (inbox 006 Q15, data engineer new-MD-E3)
- **D07** One player key: player_id (ESPN athlete ID, local x- IDs) or W1's player_uid? [player_id] (inbox 006 Q6)
- **D08** Use class of Torvik, NBA combine and EvanMiya values: model input or reference only? [decide per source in data_sources_catalog.md] (inbox 006 Q2)
- **D09** Kaggle March Madness archive (contains KenPom/Torvik columns): reference only, private copy only? [reference only, private] (inbox 006 Q3)
- **D10** hoopR ESPN-based prebuilt files: model input or reference only (ESPN terms)? [reference only until terms checked] (inbox 006 Q4)
- **D11** Kaggle Massey Ordinals: model input or reference only (Massey terms forbid AI/ML training without consent)? [reference only until permission (R-DS-12)] (quality review C13 (R-DS-10))
- **D12** Record your 18 Oct chat approval of the KenPom (Parse.bot) tool in R-DS-14 and its licence class (reference only?) [record, reference only] (inbox 006 Q1)
- **D13** Keep the ESPN-pulled registry/*.csv in the public repo or rebuild from CBBD; drop headshot_url (no-face rule)? [rebuild from CBBD; drop headshot_url] (inbox 006 Q5, data engineer risk 6)
- **D14** Store player birth date, or only age at tip? [age at tip only] (inbox 006 Q16)
- **D15** Approve registry columns cbbd_game_id, video_ids, video hash, fps, resolution, codec, length, scorebug_left_team_id, media_format, pbp_status, bench end and first-half basket? [yes] (inbox 006 Q8, data engineer new-FD-E1, gap closures new-FD-7)
- **D16** Bench side and scorers' table side per game: filled by you at intake or detected automatically? [filled at intake, verified by tracking] (inbox 007)
- **D17** Approve tier changes: R-SB-04 and R-SR-11 to Shall, R-PL-01 to Should, R-IV-14 to Shall once frontcourt status is stored? [yes] (quality review 3.5, ESPN analyst)
- **D18** Pass marks for the coach quiz per question type (R-GU-03), e.g. "who guards X" >= 90%? [set after game 3] (quality review (needs_decision))
- **D19** Approve the held-out game register (>= 20% of footage games, chosen by game, stratified by home/away and opponent tier) before any fit? [yes] (team data scientist new-VA-S1)
- **D20** Officials' mechanics (rotations, primary areas, calling distance, full signal list): label now or after gate G7, and obtain the CCA Men's Officials Manual first? [after G7; obtain the manual] (inbox 007, officials_mechanics.yaml)
- **D21** Staff sheets: show official names next to crew tendencies, or crew IDs only; keep unwhistled-contact candidates review-only and private? [crew IDs on shared sheets; candidates private] (ESPN analyst Q2, new-RF-A15)
- **D22** Conduct events (flopping, taunting, gestures toward officials, fighting and suspensions): in scope, and private only or publishable? [in scope as private labels; not published] (inbox 007, gap closures)
- **D23** Fakes and contest form from pose as Shall now, or Should until pose quality at broadcast distance is measured? [Should until measured] (inbox 007)
- **D24** NIL valuations on player cards: keep as public estimates (exploratory only) or drop? [keep, never a model input] (inbox 007, gap closures, dictionary_players)
- **D25** Public betting share: look for a free terms-compliant source, accept a paid one, or drop the leaf? [drop until a free source is registered] (inbox 007, gap closures)
- **D26** Context extras (ball model, rim type and liveliness proxy, dome placement, student-section end, crowd share): collect, or Should with "unknown"? [Should with unknown] (inbox 007, gap closures)
- **D27** Pick-up point class edges 18.71 / 14.00 / 9.50 m: the staff's notion of full / three-quarter / half court? [confirm with staff] (gap closures)
- **D28** Lineup "big" rule: listed C, or listed F >= 206 cm (listed heights run high)? [listed C or F >= 206 cm, flagged] (gap closures)
- **D29** Fakes, runs and source definitions as new tables, or as event-family rows in events? [runs and source_definitions as tables; fakes as events rows] (gap closures)
- **D30** Disqualified-player replacement: 20 s (RB 4-12.5) or 15 s (DIF p 2)? [20 s (rules book wins), flag DIF] (rules_edition.yaml)
- **D31** Rules-edition season window 1 July - 30 June acceptable (no effective date printed)? [yes] (rules_edition.yaml)
- **D32** Obtain the 2025-26 rules book to confirm the derived 2025-26 edition record? [yes] (rules_edition.yaml)
- **D33** Which edge of the 2-in 28-ft mark is the 28 ft measured to? [check on a measured court] (restarts.yaml, court_constants_check.md)
- **D34** Confirm the lane-space layout on a full-resolution diagram or a measured court before P3? [yes] (court_constants_check.md)
- **D35** Add restart_type values throw_in_where_ball_went_out and division_line_after_review to restarts? [yes] (restarts.yaml)
- **D36** Count a shooter-team FT lane violation on the last free throw as a turnover (possession lost)? [yes, typed separately] (violations_turnovers.yaml)
- **D37** Was the "shot clock near expiration" signal in the 2025-26 book (affects the 2025-26 edition)? [check with the 2025-26 book (D32)] (signals.yaml)
- **D38** Is a coach available to rate 50 broadcast phrases and 100 timeout purposes? [ask staff] (ESPN analyst Q5)
- **D39** Markets: ESPN option (i) schedule only, (ii) schedule and odds, (iii) none? [decide] (inbox 006 markets)
- **D40** Markets: Kalshi and Polymarket terms (incl. identity-field stripping): enable or keep disabled? [keep disabled until terms checked] (inbox 006 markets)
- **D41** Markets: collector host (always-on Mac or small cloud VM)? [decide] (inbox 006 markets)
- **D42** Markets: tiered cross-source tolerances XS-1..XS-4 vs the single 0.5-point rule (R-MK-22 split)? [split: 0.5 Shall, tiers Should] (inbox 006 markets, quality review C21)
- **D43** Send the written permission requests (Sports-Reference, Massey; Synergy via staff) for R-DS-08 / R-DS-12? [yes] (quality review (needs_decision))
- **D44** Record the MSU film agreement status for R-RG-09? [record] (quality review (needs_decision))
- **D45** Actions (not decisions): start Google Drive for desktop; rotate the CBBD and Parse keys that appeared in chat. [do] (inbox 006 Q17-Q18)

## 10. Sources opened for this synthesis (2026-10-18)

Repo: `docs/requirements_review/quality_review.md`, `acceptance_tests.yaml`, `perspective_espn_analyst.md`, `perspective_data_engineer.md`, `perspective_team_data_scientist.md`; `docs/data/gap_closures_round2.md`, `docs/data/court_constants_check.md`, `docs/data/dictionary_games.md` and `dictionary_players.md` (proposal lines only); `schema/tables_proposed_changes.yaml`; `config/vocab/*.yaml` (headers, requirements lists, open questions); `config/game_ontology.yaml` (leaves and gaps = inbox 007 proposals); `config/invariants.yaml` (new-IV statements, corrections); `coord/requirements_inbox/006-data-dictionary-and-first-games.md`, `006-markets-requirements.md`, `007-game-ontology-gaps.md`; `src/msu_alpha/markets/` working-tree diff and `tests/markets/test_engineer_review_fixes.py`. Scratchpad: `brief_panel.md`, `brief_improve.md`, `brief_003.md`, `live_doc2/requirement_ids.md` (518 IDs). No web pages, APIs or data providers were called for this synthesis; rule numbers are cited as verified in the inputs.
