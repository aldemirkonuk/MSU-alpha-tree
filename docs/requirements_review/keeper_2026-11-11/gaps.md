# Gaps (first pass, 11 Nov 2026)

Missing requirements, as proposed new ids that continue each family's numbering (no id is reused). "Risk" says whether adding it only writes down content that is already decided (safe) or adds scope (owner). Staff-dependent items stay excluded for now and are not designed around.

## 1. Baseline gaps

| Gap | Baseline | Proposed id | Requirement (short) | Basis | Risk |
| --- | --- | --- | --- | --- | --- |
| G-B1-1 | 1 | R-CG-14 | config/named_spots.yaml is the one source of spot, zone and position labels; every `*_spot` column holds a court\_region label or `unknown` | dictionary status line; named_spots.md items 17, 24; decision 10 | safe |
| G-B1-2 | 1 | R-CG-15 | One single-winner coaching spot per player per frame; `frame_team` (home, away, none) fixes the attacked basket | named_spots.md items 17, 18 | safe |
| G-B1-3 | 1 | R-CG-16 | Label stability: reference point, hysteresis, dwell, airborne and occlusion rules from the dictionary's rules layer | config/named_spots.yaml rules layer | safe |
| G-B1-4 | 1 | R-CG-17 | Crosswalk labels to other providers' shot maps (NBA, CTG, pbpstats, BR) stored beside court\_region | dictionary section 7.1 | safe |
| G-B1-5 | 1 | R-CG-18 | All exact spot rules for 10 players and the ball run within one frame period (measured 1.9 ms vs 33.37 ms) | named_spots.md:1541 | safe |
| G-B1-6 | 1 | extend R-CG-09 | Film-settled list (capture radii, band edges, anchors, sign conventions, display convention) tracked as calibration tasks | named_spots.md section 12 | safe |
| G-B2-1 | 2 | R-EV-30 | Turnover, steal and rebound attribution: official stat rule; steal by default (OD-3); muffed pass on receiver (OD-4); pass-forced only when flagged (OD-5); scramble touch < 1.5 s after rim visit is no control (OD-1); rim-visit radius 0.75 m until MSU ball height (OD-2); deflector and recoverer both stored; labels follow the final ruling | ball_actions.yaml:1650-1754; decisions 23-25 Oct | safe |
| G-B2-2 | 2 | R-ST-39 | Every screen is an atomic tag (on-ball, hand-off, off-ball); combinations (Ram, Spain, screen-the-screener before and after) are derived from the sequence, never tagged; team play names are optional labels | Aldemir 24 Oct | safe |
| G-B2-3 | 2 | R-ST-40 | Post-up record in Synergy style: post touch and seal are separate labels | Aldemir 23 Oct (batch 2) | safe |
| G-B2-4 | 2 | R-DF-32 | At the noisiest tier, post, face-guard, lob and stunt labels abstain and report the abstention | Aldemir 23 Oct (batch 2) | safe |
| G-B2-5 | 2, 3 | R-DT-24 | Crossings carry an id-swap risk flag (`id_swap_risk` in bigs.yaml) that identity reads | Aldemir 23 Oct | safe |
| G-B3-1 | 3 | R-ID-17 | A detection carries a player id only when the posterior reaches the lock threshold; otherwise HOLD with candidates; zero swaps of locked labels; a probable tier exists offline only, flagged, never in stats | identity_pack.yaml:14-19, 325-331 (OD-8) | safe |
| G-B3-2 | 3 | R-ID-18 | Games that feed player-level numbers are ≥ 1080p and ≥ 59.94 fps; below that, team-level numbers or probable-only labels | identity_pack.yaml:21 (OD-9) | safe (the MSU recording agreement stays excluded) |
| G-B3-3 | 3 | R-ID-19 | The live panel shows a locked label or HOLD with candidates, never a provisional or probable label | identity_pack.yaml:409, 474 (OD-10) | safe |
| G-B3-4 | 3 | R-ID-20 | Identity state machine: lock on entry, keep through occlusion, re-confirm after every crossing, release on exit | owner rule 23 Oct; identity_pack.yaml scope | safe |
| G-B3-5 | 3 | reword R-ID-10 | Forbidden cues listed (face, face embedding, skin tone, hair colour and texture, ethnicity, race, health status, tattoos); crops are torso and legs with skin masked | identity_pack.yaml:53-58 | safe |
| G-B4-1 | 4 | R-SR-21 | Every state field states its latency profile: provisional and confirmed source, median and p95 delay | config/live_state/core.yaml profiles | safe |
| G-B4-2 | 4 | R-SR-22 | Every state field has a dropout rule (sensor away: carry, infer from cues, or unknown) | core.yaml CUE\_RECKON and health fields | safe |
| G-B4-3 | 4 | R-SR-23 | config/live_state/*.yaml is the field catalogue (id, source, update timing, latency, dropout, requirement ids) | baseline 4 definition (BOARD:60) | safe |
| G-B4-4 | 4 | R-SY-21 | Measure the live play-by-play feed and the B1G+ stream delay against real time at a live game (measurement only) | Aldemir 11 Nov; core.yaml OQ-LS-1 | safe |
| G-B5-1 | 5 | R-PR-17 | The views catalogue is one file with a schema (view id, audience, grain, metrics by id, refresh, as-of, latency tier, privacy) checked in CI | baseline 5 definition | safe |
| G-B5-2 | 5 | R-PR-18 | The private HTML review tools are catalogued views | review tools in use since 23 Oct | safe |
| G-B5-3 | 5 | R-PR-19 | Every view states who may see it and what it may export (never video or face crops outside the private store) | R-AS-10, R-RG-01 | owner |
| G-B6-1 | 6 | R-MR-01..06 or R-EN-22 | Metric registry (config/metrics.yaml, 1,591 metrics) with id, formula, unit, range, depth, computability; R-EN-18 serves stats through it | config/metrics.yaml cites R-MR-01; new-MR-01..06 in the "Stat catalogue (18 Oct)" tab | owner |
| G-B6-2 | 6 | R-EN-23 | Query-layer access stays private: no row-level result leaves the private store | R-RG-11, public repo | safe |
| G-B7-1 | 7 | R-VA-16 | The gold-v1 game list (3 games plus 1 unseen hold game) is registered with ids and a frozen hash | section 39 answer; R-VA-01 | safe |
| G-B7-2 | 7 | R-HR-15 | A versioned labelling guide per label type (turnover, screen, identity, events) | P0.9 "Labelling guide"; turnover principles 24 Oct | safe |
| G-B7-3 | 7 | R-HR-16 | Labels made by Claude for Aldemir are stored apart, scored against his labels, and never count as gold unless he confirms them | Aldemir 11 Nov; R-HR-12 | owner |
| G-B7-4 | 7 | R-VA-17 | Interim truth sets (gold v0: 202 turnover items, 24 Oct) registered, frozen and kept out of training | review_tool gold\_v0 file | safe |
| G-B8-1 | 8 | R-CD-07 | Freeze-exit checklist: each P0 entry item with owner, evidence and sign-off; only Aldemir lifts the freeze | section 02 table; PROTOCOL.md | safe |
| G-B8-2 | 8 | R-CD-08 | Every freeze exception written in coord/PROTOCOL.md with date and scope (B1G+ downloads in batches 23 Oct; live latency measurement 11 Nov) | PROTOCOL.md has only the 18 Oct exceptions | safe |
| G-B8-3 | 8 | R-EN-24 | Harnesses built under the freeze (tools/state/, tests/state/) are deleted before production code is built | Aldemir 19 Oct (BOARD:47) | safe |
| G-B8-4 | 8 | R-CD-09 | The decision-10 repo change set (named_spots.md section 13) is applied as one change at freeze exit | decision 10, 23 Oct | safe |
| G-B8-5 | all | R-CD-10, R-CD-11 | Give ids to the requirement-format rules (section 01) and to the phase-gate contract (section 02) | existing text without ids | safe |
| G-B8-6 | all | R-HR-17..R-HR-20 | Give ids to the JEV rules of 17 Oct: role (never a pipeline module); blind multiple choice and pinned version; per-type calibration and switch-on at ≥ 80% top-1; JEV-off runs byte-identical, budget cap | section 34 text without ids | safe |
| G-B9-1 | 9 | R-FP-01..R-FP-06 (Should, future) | Fingerprint: pose per locked player in action windows; body-normalised features; position-matched peers from the same broadcasts; robust z-scores and own-game drift; explanation only from the numbers; reliability ICC ≥ 0.6 before adding actions; 1080p60 and locked identity first; no face, race-proxy or health inference; outputs private | docs/data/movement_fingerprint.md sections 4-9 | owner (parked; add as text only) |

## 2. The path after the freeze

| Area | Covered by | Gap and proposed id | Risk |
| --- | --- | --- | --- |
| Build order | Phase table P0-P8 (prose); R-PR-09 (live after P6); R-PE-10 (levels); R-VL-01 (10 Hz after G1-G4) | R-CD-11 phase-gate contract with ids; R-EN-25 first build is the 43 + 4 tables of D04 ("the other specs stay proposed, built when a requirement needs them") | safe |
| Live operation | R-PR-15, R-PR-11, R-VI-23..R-VI-25, R-EN-15, baseline 4 | R-EN-26 game-day run book (start, stop, fallbacks, who is alerted); R-MK-35 collector host per D41 ("Always-on Mac now; move to a small cloud VM if collection uptime falls below 99% over any 2 weeks") | R-MK-35 safe; R-EN-26 owner |
| Monitoring | R-DQ-07, R-DQ-08, R-DQ-18, R-VA-14, R-MK-33, R-CS-06 | Alert routing and response time sit in R-EN-26 | owner |
| Model retraining | R-VA-09 (regression), R-HR-09 (learning curve), R-PR-04 (walk-forward), R-PR-16 (model cards) | R-VA-18 retraining policy: triggers (drift alert, N new gold labels, new season), regression check before promotion, rollback to the previous model card | owner |
| Data licences | R-RG-03..R-RG-05, R-RG-08, R-DS-01, R-DS-10, R-DS-11, R-MK-19, R-MK-24 | R-DS-17: data read from paid sites through Aldemir's own login (decision 11, 23 Oct) is stored privately, tagged with source and licence, never committed, never a model input until its use class is recorded | safe |
| Secrets | R-DS-11, R-DS-13a, R-MK-23, R-EN-20 (per source) | R-RG-12 one project-wide secrets rule (keychain or environment only; never in repo, files, logs or stored URLs; scanner blocks commits) | safe |
| Privacy | R-PC-15, R-RG-06, R-ID-10, R-AS-10, R-RF-21, R-RG-01, R-RG-02, R-RG-11 | R-RG-13 every access path to private video (Drive, private server, tunnel) is owner-only and audited; R-RG-14 retention list for video and player-level outputs with dates and logged deletion | owner |
| Staff-dependent (excluded for now, tracked) | R-DS-08 (Synergy via staff), R-RG-09 (MSU data agreement), R-CC-07 (coach labels for timeout purpose); OD-6 hard vs soft switch; decision 6 and 13 staff words; ShotTracker ids; MSU recording agreement | no design around them; revisit when staff answer | n/a |

## 3. Analytics catalogue (10 player tracks, ball, play-by-play, markets)

Earliest baseline = the first baseline whose completion makes the analytic specifiable end to end ("now" = possible from play-by-play or the scorebug today; vision analytics also need the P1 build). Inputs: PBP = play-by-play; T = 10 tracks with identity; B = ball; P = pose; S = scorebug; A = audio; M = markets; V = value model.

| Family | Analytic | Covered by | Inputs | Earliest |
| --- | --- | --- | --- | --- |
| Shooting | Shot chart by region and spot, shrunk make rates | R-PC-23, R-MM-01, R-PC-06a | PBP coordinates | 1 (now) |
| Shooting | Shot quality, shooter-agnostic and shooter-adjusted | R-VL-04 | PBP; T for contest | 1 / 3 |
| Shooting | Shot-making residual | R-VL-14 | as above | 1 / 3 |
| Shooting | Contest distance, angle, closing speed at release | R-EV-07, R-EV-19 | T, P | 3 |
| Shooting | Catch-and-shoot vs pull-up, dribbles and touch before | R-EV-07, R-EV-04 | T, B | 2 |
| Shooting | Shot-clock profile at release | R-PS-11 | S | 4 (now) |
| Shooting | Release height, arc, entry angle | R-MM-04, R-PL-07 (gated) | 3-D ball | gap until ball height (future) |
| Shooting | Free-throw routine and pressure | R-MM-06 | T, P, A | 3 |
| Shooting | Rim protection: FG% allowed, attempts deterred | R-VL-17 | T | 3 |
| Passing | Assists, potential and hockey assists | R-EV-03, R-PC-07 | T, B, PBP | 2 |
| Passing | Pass type, speed, lane openness, receiver space | R-EV-02 | T, B | 2 |
| Passing | Passing network, observed vs expected | R-CH-02 | passes | 2 |
| Passing | Ball movement and possession path per chance | R-PS-12, R-PS-13, R-ST-32 | B, spots | 2 |
| Passing | Decision quality vs the best open option | R-VL-05 | T, V | 3 + value |
| Passing | Passing-lane model ("passes away") | none (decision 12: later) | T | gap (future) |
| Passing | Gravity from the ghost defence | R-VL-06, R-DF-31 | T | 3 + value |
| Screens | Screen detection and screen moment | R-ST-02, R-ST-17, R-ST-20 | T | 2 |
| Screens | Ball-screen parts (location, angle, arrival, action after, read) | R-ST-29, R-PS-15 | T, B | 2 |
| Screens | Coverage per screen and its outcome | R-DF-16 (survivor), R-DF-27 | T | 2 |
| Screens | Rolls, pops, slips, handoffs | R-ST-18 | T, B | 2 |
| Screens | Atomic screen tags, derived combinations | gap R-ST-39 | T | 2 |
| Screens | Post-ups (touch and seal) | gap R-ST-40 | T, B | 2 |
| Screens | Screener-handler timing | R-CH-04 | T | 2 |
| Off-ball | Cuts by type | R-ST-28 | T | 2 |
| Off-ball | Spacing, hull area, distance to nearest defender | R-CG-07, R-ST-08 | T | 1 + 2 |
| Off-ball | Lift, drift, relocate, rim run, corner sprint | R-ST-01 | T | 2 |
| Off-ball | Lane time and paint touches | R-ST-27, R-ST-31 | T, B | 1 |
| Off-ball | Alignment at initiation and start snapshots | R-ST-19, R-PS-02 | T | 2 |
| Defence | Matchup per defender per second | R-DF-01 | T | 2 + 3 |
| Defence | Help, rim protector, shell shape | R-DF-02, R-DF-03, R-DF-11 | T | 2 |
| Defence | Scheme state, changes and triggers | R-DF-04, R-DF-05, R-DF-19 | T | 2 |
| Defence | Zones and presses | R-DF-12, R-DF-17, R-DF-18 | T | 2 |
| Defence | Closeouts and reaction time | R-DF-08, R-CO-02 | T, B | 2 |
| Defence | Denial and pick-up point | R-DF-22, R-DF-23 | T, spots | 1 + 2 |
| Defence | Mismatch state, cause, exploitation, fix | R-MX-01..R-MX-05, R-ST-33 | T, cards | 3 |
| Defence | Defensive value credits and matchup points | R-VL-16, R-VL-07 | T, V | 3 + value |
| Rebounding | Rebound rates | R-PC-08 | PBP | now |
| Rebounding | Box-outs, crash vs retreat | R-EV-08, R-VL-15 | T | 2 |
| Rebounding | Positioning, hustle, conversion | R-VL-18 | T, B | 2 + value |
| Rebounding | Landing point, long vs short | R-EV-20 | B | 2 |
| Rebounding | Second-chance value by chance number | R-VL-11, H3 | PBP | 4 (now) |
| Transition | Every transition definition side by side | R-TR-18, R-TR-27 | PBP; T | 4 (PBP) / 2 |
| Transition | Numbers advantage and phase times | R-TR-03, R-TR-20, R-TR-22 | T | 2 |
| Transition | Roles and lane fillers | R-TR-04, R-TR-15 | T | 2 + 3 |
| Transition | Get-back clocks, late get-back | R-DF-20, R-DF-26, R-TR-10 | T | 2 |
| Transition | Passed-up breaks and value at stake | R-TR-24, R-TR-26 | T, V | 2 + value |
| Turnovers | Type mapped to 2026-27 codes | R-EV-10 | PBP | now |
| Turnovers | Live-ball attribution and steals | gap R-EV-30 | T, PBP | 2 |
| Turnovers | Cost by type and location | R-VL-11 | V | value |
| Turnovers | Deflections and forced turnovers | R-EV-09, R-EV-29 | T, B | 2 |
| Fouls | Foul record by class with context flags | R-RF-03 | PBP, video | 4 |
| Fouls | Whistles and whistle latency | R-RF-01, R-MM-03, R-RF-19 | A | 4 |
| Fouls | Crew tendencies | R-RF-06, R-RF-18, R-RF-20 | PBP | now |
| Fouls | Value of a drawn foul | R-VL-10 | V | value |
| Fouls | Foul trouble and its effects | R-SR-20, R-CC-06, R-DF-24 | PBP | 4 |
| Fouls | Block or charge position vs the arc | R-RF-08 | T | 1 + 3 |
| Fouls | Home crowd and foul differential | H20 | PBP | now |
| Lineups | Lineup and pair effects | R-CH-01 | PBP lineups | now |
| Lineups | Composition descriptors, bench production | R-MD-29, R-OS-06 | rosters, box | now |
| Lineups | Rotation patterns and pull reactions | R-CH-06, R-PE-06, R-CC-03 | PBP | now |
| Lineups | Substitution times from video | R-SY-16 | video | 3 |
| Lineups | Movement coordination of pairs | R-CH-03 | T | 2 |
| Load | Distance and speed bands per minute | R-PL-01, R-PL-09, R-PL-11 | T | 2 (+ R-PL-13 calibration) |
| Load | Accelerations (gated) | R-PL-12, R-PL-18 | T | 2 |
| Load | Within-game decline, recovery | R-PL-03, R-PL-04 | T | 2 |
| Load | Top-speed segments | R-PL-23 | T | 2 |
| Load | Jumps, changes of direction, contacts | R-PL-19, R-PL-20, R-PL-22 | T, P | 3 (future) |
| Load | Schedule load (rest, travel, density) | R-CX-05, R-CX-26, R-CX-27 | schedule | now |
| Load | Fatigue and decision quality | R-CO-07, H13 | T, V | 2 + value |
| Sets | Set match with calibrated confidence | R-ST-05 | T | 2 |
| Sets | Compositional names and full sequences | R-ST-06 | T | 2 |
| Sets | Set timelines and phase execution | R-ST-07, R-ST-08 | T, S | 2 |
| Sets | New-set discovery and learned dictionary | R-ST-09, R-ST-38 | T | 2 |
| Sets | ATO, BLOB, SLOB, end of clock | R-ST-23, R-ST-35, R-EV-15b | T, S, PBP | 2 + 4 |
| Sets | Zone recognition lag | R-ST-34 | T | 2 |
| Scouting | Opponent normal baselines and packets | R-OS-01, R-OS-07 | PBP | now |
| Scouting | Spot game plan | R-PC-24 | PBP coordinates | 1 |
| Scouting | Assignment and mismatch forecast | R-MX-06 | cards | now |
| Scouting | Opponent sets and schemes (only vs MSU) | R-OS-02, R-OS-05 | T | 2 |
| Scouting | Coach tendencies, head-to-head | R-CH-07, R-CC-05, R-DF-14 | PBP; T | now / 2 |
| Value and WP | Possession value layers and action credit | R-VL-01, R-VL-02 | PBP; T | 4 / 2 + 3 |
| Value and WP | Possession engine L0-L4 | R-PE-01..R-PE-13 | PBP; T for L4 | 4 |
| Value and WP | Win probability per layer, calibrated | R-PR-01..R-PR-06 | engine | 4 |
| Value and WP | Live in-game win probability | R-PR-11 | S, engine | 4 (after P6) |
| Value and WP | Leverage and swing plays | R-MD-33, R-PR-12 | WP | 4 |
| Value and WP | Belief state and surprise | R-GU-01, R-GU-02 | all | value |
| Value and WP | Clutch and pressure performance | R-CO-04 | S, V | 4 |
| Value and WP | Standard box and PBP metrics (four factors, ratings, usage ...) | only through config/metrics.yaml; no requirement | PBP | gap R-MR-01..06 (now) |
| Markets | Closing lines and snapshots | R-MK-01, R-MK-02, R-MK-16 | M | now |
| Markets | Fair probabilities | R-MK-04, R-MK-15, R-MK-30, R-MK-32 | M | now |
| Markets | Edge with sample rule, closing-line value | R-MK-05, R-MK-06, R-PR-08 | M, engine | 4 |
| Markets | Props vs player distributions | R-PR-07 | M, engine | 4 |
| Markets | In-game exchange prices joined to state | R-MK-03, R-VI-25 | M, S | 4 |
| Markets | Market-free vs market-input variants | R-MK-08 | M | 4 |
| Markets | Referee crew and totals; first-half edge | H15, H16 | M, PBP | now |
| Live views | Live state panel (HOLD rule) | R-PR-15, gap R-ID-19 | S, T | 4 |
| Live views | Live WP and run shading | R-PR-11, R-VZ-06d | S, engine | 4 |
| Live views | Foul tracker, timeouts left | R-VZ-06g, R-VZ-06h | S, PBP | 4 |
| Live views | Half-time packet | R-VZ-08 | all | 4 + 5 |
| Live views | Live alerts to staff (foul trouble, hot shooter) | none | S, T | gap; staff-facing, excluded for now |
| Fingerprint | Pose-based movement profile vs peers | gap R-FP-01..06 | T, P, 1080p60 | 9 (parked) |

Excluded by rule, not a gap: injury risk, emotion from faces, anything from skin, hair, race proxies or health status.
