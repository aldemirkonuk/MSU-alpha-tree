# Game ontology and requirements coverage audit

Written 2026-10-18 for prompt 003 (coverage audit). Status: **proposal** for the requirements session; nothing here changes the live doc. Machine-readable twin: `config/game_ontology.yaml` (same IDs, generated from one source). Inbox: `coord/requirements_inbox/007-game-ontology-gaps.md`.

**Goal (Aldemir):** requirements so complete that every part of a basketball game is configured, with each aspect categorised. This file lists every aspect of a college basketball game as a tree of leaf concepts, maps each leaf to the requirement IDs, tables, columns, vocabularies and rule-book articles that cover it today, and proposes a requirement for every leaf that is only partly covered or not covered.

## How to read this

- **Inputs read:** the live requirements export of 18 Oct (518 IDs in 43 families, `requirements_main.md`, `requirement_ids.md`, `hypothesis_candidates.md`); the 2026-27 NCAA Men's Rules Book, Case Book, 2025-26 rules changes and 2026-27 post-clinic interpretations (`docs/rules/`, text from `pdftotext -layout`); `docs/taxonomy/*.md`; `docs/research/*.md`; `docs/data/*.md`; `schema/tables/*.yaml` (104 tables); `schema/global_metadata.yaml`; `config/*.yaml`.
- **Rule references** use Rule-Section.Article of the 2026-27 book (e.g. 2-11.6.d.1); `App.` is an appendix (App. III officiating guidelines, App. VIII signals).
- **Vocabulary codes:** `OFF.F<n>` offense taxonomy, `DEF.F<n>` defense taxonomy, `MS` motion starts, `TR.ST`/`TR.PH`/`TR.RO` transition start types, phases and roles, enum names from `schema/global_metadata.yaml`, and `config/vocabulary_map.yaml`.
- **Tables** are `<table>.<column>` from `schema/tables/*.yaml`; `player_card.<field>` is the W1 card template.
- **Status:** **covered** = a requirement names the concept and a table/column stores it (with its vocabulary); **partial** = one of the two is missing or incomplete (e.g. enum lacks values the rules book defines), or only a repo proposal not yet in the live doc covers it (e.g. `new-IV-22` in `config/invariants.yaml`); **missing** = no requirement and no store.
- **Proposed IDs** `new-<FAMILY>-n` continue after the IDs already proposed in the repo (new-IV-01..34, new-PC-1..5, new-FD-1, new-DS-1, new-SY-1, new-MK-10..18). The requirements session renumbers. One new family is proposed: **R-RL (rules layer)**, because no existing family owns the versioned rules edition that court constants (R-CG), invariants (R-IV), shot-clock rules (R-MD-06, R-SY-09) and timeout allotments all read from.
- **Validation:** every requirement ID cited exists in the export; every `<table>.<column>` exists in the schema; all 518 requirement IDs and all 104 tables map to at least one leaf (reverse index at the end).

## 1. Coverage statistics

| Domain | Leaves | Covered | Partial | Missing | Covered % |
| --- | ---: | ---: | ---: | ---: | ---: |
| A. Game structure and rules | 122 | 86 | 30 | 6 | 70% |
| B. Court, equipment and venue | 40 | 25 | 9 | 6 | 62% |
| C. Participants | 39 | 32 | 7 | 0 | 82% |
| D. Game state | 48 | 43 | 3 | 2 | 90% |
| E. Individual actions | 66 | 47 | 14 | 5 | 71% |
| F. Group tactics: offence | 48 | 43 | 5 | 0 | 90% |
| G. Group tactics: defence | 33 | 30 | 2 | 1 | 91% |
| H. Outcomes and value | 34 | 31 | 3 | 0 | 91% |
| I. Physical and load | 17 | 14 | 2 | 1 | 82% |
| J. Context | 29 | 23 | 4 | 2 | 79% |
| K. Coaching and decisions | 19 | 18 | 1 | 0 | 95% |
| L. Media and video | 41 | 37 | 3 | 1 | 90% |
| M. Data, quality and governance | 40 | 36 | 4 | 0 | 90% |
| **All** | **576** | **465** | **87** | **24** | **81%** |

Gaps: 111 leaves are partial or missing. They get **93 proposed new requirements**; 21 gaps are closed (fully or in part) by proposals already in the repo, mainly the 34 `new-IV` invariants in `config/invariants.yaml` that the live doc has not adopted yet.

Proposed new requirements per family:

| Family | Proposed | Family | Proposed |
| --- | ---: | --- | ---: |
| R-AU | 2 | R-ID | 1 |
| R-BL | 1 | R-MB | 1 |
| R-CC | 4 | R-MD | 5 |
| R-CD | 1 | R-MK | 1 |
| R-CG | 1 | R-OS | 1 |
| R-CH | 1 | R-PC | 2 |
| R-CX | 8 | R-PL | 4 |
| R-DF | 5 | R-RF | 12 |
| R-DQ | 1 | R-RL | 1 |
| R-DS | 1 | R-SR | 5 |
| R-DT | 2 | R-ST | 8 |
| R-EV | 13 | R-SY | 2 |
| R-FD | 4 | R-VI | 3 |
| R-HR | 1 | R-VL | 2 |

Tier split: 30 Shall, 63 Should.

## 2. Key findings

1. **Every one of the 518 requirement IDs and all 104 tables map to at least one leaf**, so nothing in the live doc is orphaned; the gaps are aspects of the game that no requirement names yet.
2. **Rule-book mismatches.** The 9 foul types include `intentional`, which the 2026-27 book does not have (deliberate fouls are common fouls or Flagrant 1, Rule 4-15.2.c.1.d); the turnover list lacks the over-and-back backcourt violation (9-12) and the elbows violation (9-13); `shot_clock_resets.cause` has 6 values against 33 rule causes; the official-signal enum has 10 of about 50 Appendix VIII signals.
3. **Rules are not versioned.** Constants are spread across `config/court_ncaa_men.yaml` (still `verified: false`), `config/invariants.yaml` and requirement text, with no rules edition per game; older 35 s-era games and the 2025-26 and 2026-27 changes need one (proposed R-RL family).
4. **Court config is incomplete:** no line width, centre circle, lane-space marks, backboard, ring diameter, coaching box or 28-ft marks, though out-of-bounds, lane occupancy, jump-ball formations and bank shots depend on them.
5. **34 invariants already proposed** (`new-IV-01..34`) would close 11 partial leaves here once the live doc adopts them (more are cited in leaf notes as support for covered leaves).
6. **Lowest coverage: court/equipment/venue (B, 62%), rules (A, 70%) and individual actions (E, 71%).** In E: fakes, contest form, landing space, jumps, slides and backpedals, named cuts, finish subtypes, footwork and gather are not stored.
7. **Officials' mechanics** (rotations, primary coverage areas, calling distance, full signal list, visible counts) are almost absent, although the 2026-27 points of emphasis are about them.
8. **Tactics are well covered** (offence 90%, defence 91% covered) because the taxonomy files are wired into `set_instances`, `screens`, `scheme_states`; the remaining gaps are screener arrival, PnR spacing tags, paint touches, ball movement, pick-up point and lob protection.

## 3. Top 15 gaps

| Rank | Leaf | Proposed | Why it matters |
| ---: | --- | --- | --- |
| 1 | A.06.17 Foul contact mechanism (signal type) | new-RF-5 | Every foul is stored by class only; the contact mechanism (hand-check, hold, push, block, illegal screen, landing space ...) that physicality questions and the 2026-27 points of emphasis need is not captured anywhere. |
| 2 | A.01.10 Rules edition in force per game | new-RL-1 | Rule constants live in three files (court config, invariants config, requirement text) with no edition key; 35 s-era games, the 2025-26 challenge and 2026-27 appeals need per-season rules or checks will misfire on older games. |
| 3 | A.06.11 'Intentional' foul label vs the rules book | new-RF-3 | The live doc's 9 foul types include `intentional`, a class the 2026-27 rules book does not have; foul counts by type will not reconcile with the rules or the box score. |
| 4 | A.03.06 No-reset situations | new-SY-2 | Shot-clock reset causes are 6 coarse values while the rules (and config/invariants.yaml) list 33; no-reset stoppages are not recorded, so R-SY-09 cannot check most stoppages. |
| 5 | B.01.02 Boundary lines and the out-of-bounds plane | new-CG-1 | Court config lacks line widths, centre circle, lane spaces, backboard, ring diameter, 28-ft marks; out-of-bounds, lane occupancy, jump-ball formation and bank shots depend on them, and R-CG-01 still fails (verified: false). |
| 6 | A.06.06 Blocking vs charging and the restricted area | new-RF-1 | Block/charge calls do not store restricted-area status or whether the defender was a secondary defender; a central officiating and defensive-value question. |
| 7 | E.04.05 Contest form (hand up, high/low hand, contest height) | new-EV-11 | Shot contest is only a distance; hand up vs not and hand-to-ball distance drive shot quality more than distance alone. |
| 8 | E.02.06 Fakes (shot fake, pass fake, jab step) | new-EV-7 | Shot fakes, pass fakes and jab steps are absent from the event model; they are among the most common creation actions and defender-discipline measures. |
| 9 | A.04.12 Frontcourt and backcourt status of team control | new-SR-3 | Frontcourt status is not stored; backcourt violations, the 10-second count and the shot-clock 30 s backcourt rules cannot be checked. |
| 10 | A.08.07 Backcourt violation (over and back) | new-EV-3 | Over-and-back backcourt violations have no turnover code (only 10-second), so turnover types will not reconcile with PBP. |
| 11 | A.09.02 Player who caused the ball out of bounds | new-BL-1 | Out-of-bounds plays do not store who touched the ball last; needed for coach's-challenge modelling, turnover credit and R-SY-10 matching. |
| 12 | H.04.06 Defensive value per player (stops, contests, deterrence) | new-VL-2 | Defensive value is credited mostly through steals, blocks and matchups; contests, rotations and rim deterrence have no credit rule. |
| 13 | D.07.04 Lineup composition (size, positions, shooting) | new-MD-5 | Lineup composition (size, shooters, handlers) is not a feature anywhere, yet every lineup, matchup and engine level needs it. |
| 14 | G.01.04 Pick-up point | new-DF-3 | Where the defence picks up the ball (full, three-quarter, half court) is not measured; it defines pressure and press usage. |
| 15 | M.01.06 Source definition register (each source's own definitions) | new-DS-2 | Each source's own definitions (possession, assist, fast break, shot zone) are not stored as data, so cross-source checks cannot explain disagreements. |

## 4. Ontology tree

Domains and groups with their leaves (status in brackets: C covered, P partial, M missing).

```
A GAME STRUCTURE AND RULES
    A.01 Game, periods and result
        A.01.01 Team's own basket and direction of play [C]
        A.01.02 Halves (2 x 20:00) [C]
        A.01.03 End of period and try in flight [C]
        A.01.04 Intermissions (half time, before extra periods) [P]
        A.01.05 Extra periods (overtime) [C]
        A.01.06 Final result and winner [C]
        A.01.07 Forfeit and no contest [P]
        A.01.08 Interrupted or suspended game [M]
        A.01.09 Game type, season type and round [C]
        A.01.10 Rules edition in force per game [P]
    A.02 Game clock
        A.02.01 Game clock value and display [C]
        A.02.02 Game clock start triggers [P]
        A.02.03 Game clock stop events [C]
        A.02.04 Minimum time off on a touch (0.3 s) and tap-only rule [P]
        A.02.05 Timing mistakes and corrections [C]
        A.02.06 Video time to game clock map [C]
    A.03 Shot clock
        A.03.01 Shot clock value and status [C]
        A.03.02 Shot clock start [C]
        A.03.03 Reset to 30 s [C]
        A.03.04 Reset to 20 s flat (offensive rebound after ring contact) [C]
        A.03.05 Reset to max(20, remaining) [C]
        A.03.06 No-reset situations [P]
        A.03.07 Shot clock off and reactivation [C]
        A.03.08 Shot-clock violation and horn vs release [C]
        A.03.09 Single working shot clock [C]
    A.04 Control, possession and jump balls
        A.04.01 Player control and team control [C]
        A.04.02 Possession (our definition) [C]
        A.04.03 Chance [C]
        A.04.04 Possession counts under each source's definition [P]
        A.04.05 Opening and overtime jump balls [C]
        A.04.06 Held ball [C]
        A.04.07 Alternating-possession arrow [C]
        A.04.08 Jump-ball violations [P]
        A.04.09 Live ball and dead ball [C]
        A.04.10 Point of interruption [C]
        A.04.11 Inadvertent whistle [C]
        A.04.12 Frontcourt and backcourt status of team control [P]
        A.04.13 10-second backcourt count [P]
        A.04.14 Closely guarded 5-second count [P]
        A.04.15 Three seconds in the lane [P]
    A.05 Scoring
        A.05.01 Two- and three-point field goals [C]
        A.05.02 Free-throw point [C]
        A.05.03 Goaltending and basket interference awards [C]
        A.05.04 Illegal assistance in scoring or blocking [P]
        A.05.05 Goal in the wrong basket [P]
        A.05.06 Score corrections and correctable errors [C]
    A.06 Fouls and penalties
        A.06.01 Common personal foul (non-shooting) [C]
        A.06.02 Shooting foul [C]
        A.06.03 Player-control foul [C]
        A.06.04 Team-control foul [C]
        A.06.05 Loose-ball foul [C]
        A.06.06 Blocking vs charging and the restricted area [P]
        A.06.07 Double and simultaneous personal fouls [C]
        A.06.08 Multiple, false double and false multiple fouls [P]
        A.06.09 Flagrant 1 [C]
        A.06.10 Flagrant 2 and ejection [C]
        A.06.11 'Intentional' foul label vs the rules book [P]
        A.06.12 Technical foul Class A [C]
        A.06.13 Technical foul Class B [C]
        A.06.14 Administrative technical [P]
        A.06.15 Fouls by bench personnel and coaches [C]
        A.06.16 Contact dead-ball technical [C]
        A.06.17 Foul contact mechanism (signal type) [P]
        A.06.18 Team fouls, bonus and double bonus [C]
        A.06.19 Disqualification (5 fouls, 3 Flagrant 1) [C]
        A.06.20 Ejection [P]
        A.06.21 Fighting and suspensions [M]
        A.06.22 Flopping (faking being fouled) [M]
        A.06.23 Take foul and clear-path fouls in transition [C]
        A.06.24 Deliberate end-game fouling [C]
    A.07 Free throws
        A.07.01 Free-throw award type [C]
        A.07.02 Who attempts (shooter selection) [C]
        A.07.03 Lane positions [C]
        A.07.04 Free-throw requirements (10 s, behind the line) [C]
        A.07.05 Free-throw violations [C]
        A.07.06 What follows the last free throw [C]
        A.07.07 Free-throw state machine [C]
        A.07.08 Substitutions around free throws [P]
    A.08 Violations
        A.08.01 Traveling (incl. pre-dribble and split-step travel) [C]
        A.08.02 Illegal dribble (double dribble, palming/carrying) [C]
        A.08.03 Kicking and fisting the ball [C]
        A.08.04 Ball through the basket from below [C]
        A.08.05 Ball and player out of bounds [C]
        A.08.06 Throw-in violations [P]
        A.08.07 Backcourt violation (over and back) [P]
        A.08.08 Shot-clock violation [C]
        A.08.09 Five-second closely guarded and ten-second backcourt [C]
        A.08.10 Three-second lane violation [C]
        A.08.11 Excessive swinging of elbows [M]
        A.08.12 Basket interference and goaltending [C]
        A.08.13 Free-throw lane violations [C]
    A.09 Out of bounds and throw-ins
        A.09.01 Ball out of bounds detection [C]
        A.09.02 Player who caused the ball out of bounds [P]
        A.09.03 Throw-in spot [C]
        A.09.04 Throw-in requirements and 5-second count [C]
        A.09.05 Throw-in formations and first pass [C]
        A.09.06 Bench personnel assisting a player out of bounds [M]
    A.10 Timeouts and stoppages
        A.10.01 Team timeouts by length (30/60/75 s) [C]
        A.10.02 Media timeouts and media format [C]
        A.10.03 Timeout request and caller [C]
        A.10.04 Timeouts not granted [P]
        A.10.05 Excessive timeout and halftime carry loss [C]
        A.10.06 Injury, blood and official stoppages [C]
        A.10.07 Timeout duration (actual vs allotted) [C]
    A.11 Substitutions and lineups
        A.11.01 Starting lineup [C]
        A.11.02 Substitution procedure and timing [C]
        A.11.03 Late-game substitution restriction [P]
        A.11.04 Disqualified-player replacement (20 s) [P]
        A.11.05 Substitution reason [C]
        A.11.06 PBP substitution timing errors [C]
    A.12 Officials' mechanics and signals
        A.12.01 Crew size and roles (referee, umpires, crew chief) [C]
        A.12.02 Court position: lead, trail, centre [C]
        A.12.03 Rotations of the crew [M]
        A.12.04 Calling official, primary coverage area and whistle distance [P]
        A.12.05 Signals (Appendix VIII full list) [P]
        A.12.06 Whistles [C]
        A.12.07 Visible counts (5 s, 10 s, throw-in) [P]
    A.13 Instant replay, challenges and appeals
        A.13.01 Voluntary and mandatory reviews [C]
        A.13.02 Coach's challenge [C]
        A.13.03 Appeals [C]
        A.13.04 Review duration and game effect [C]
        A.13.05 First-half flagrant reviewed after half time [C]
B COURT, EQUIPMENT AND VENUE
    B.01 Court geometry and markings
        B.01.01 Court dimensions (28.65 m x 15.24 m) [C]
        B.01.02 Boundary lines and the out-of-bounds plane [P]
        B.01.03 Centre circle [P]
        B.01.04 Division line and half-court distance [C]
        B.01.05 Free-throw lane, line and lane spaces [P]
        B.01.06 Three-point line (6.75 m, 6.60 m corners) [C]
        B.01.07 Restricted-area arc (1.22 m) [C]
        B.01.08 Coaching box [M]
        B.01.09 28-ft throw-in marks and designated spots [P]
        B.01.10 Backboard and basket geometry [P]
        B.01.11 Coordinate frame and mirroring [C]
        B.01.12 Named spots and landmarks [C]
        B.01.13 Undefined spots (short corner, one pass away) [P]
        B.01.14 Sectors, rings, rays and grid [C]
        B.01.15 Post zones (low, high) and cut-off checks [C]
        B.01.16 Court constants verification status [P]
    B.02 Equipment and displays
        B.02.01 Ball specification [C]
        B.02.02 Game ball model per game [M]
        B.02.03 Scoreboard and game-clock display [C]
        B.02.04 Shot-clock displays [C]
        B.02.05 Possession indicator [C]
        B.02.06 Red light / LED and horn [C]
        B.02.07 Team benches and scorers' table side [M]
        B.02.08 Uniform colours and numbers [C]
        B.02.09 Supplemental apparel, headbands, sleeves [C]
        B.02.10 Player equipment (goggles, masks, braces) [P]
        B.02.11 Court logos and floor graphics [C]
        B.02.12 Rim type and stiffness [M]
    B.03 Cameras and broadcast geometry
        B.03.01 Main-camera side and height per arena [C]
        B.03.02 Camera pan, tilt, zoom and focal length [C]
        B.03.03 Homography and lens distortion [C]
        B.03.04 Other fixed camera positions [P]
        B.03.05 Floor template and glare zones [C]
    B.04 Arena and venue context
        B.04.01 Venue identity, coordinates, elevation, time zone [C]
        B.04.02 Capacity and attendance [C]
        B.04.03 Floor colour, backdrop behind each basket, lighting [C]
        B.04.04 Student-section location [M]
        B.04.05 Court placement (dome midfield / corner, standard arena) [M]
        B.04.06 Neutral site [C]
        B.04.07 Arena music and noise rules [C]
C PARTICIPANTS
    C.01 Players
        C.01.01 Player identity and IDs [C]
        C.01.02 Roster per season [C]
        C.01.03 Jersey number history [C]
        C.01.04 Listed position and played position [C]
        C.01.05 Body (height, weight, wingspan, reach, hands) [C]
        C.01.06 Age, class, eligibility [C]
        C.01.07 Origin (hometown, schools, AAU) [C]
        C.01.08 Laterality (shooting, dribble, finishing hand, drive side) [C]
        C.01.09 Athletic profile from tracking [C]
        C.01.10 Combine and athletic test results [C]
        C.01.11 Recruiting and rankings [C]
        C.01.12 Transfer history [C]
        C.01.13 International and pro background [C]
        C.01.14 NIL valuation (public estimates) [P]
        C.01.15 Role and usage cluster [C]
        C.01.16 Development and career minutes [C]
        C.01.17 Captain [P]
        C.01.18 Availability and public injury status [C]
        C.01.19 Excluded attributes (race, faces, private health) [C]
        C.01.20 Per-game appearance [C]
        C.01.21 Shooting block (sector x ring, shrunk) [C]
        C.01.22 Playmaking and ball security block [C]
        C.01.23 Prior-level physicality [C]
    C.02 Coaches and bench personnel
        C.02.01 Head coach card [C]
        C.02.02 Assistant coaches and staff roles [C]
        C.02.03 Bench personnel list per game [P]
        C.02.04 Athletic trainers and medical staff on the floor [C]
        C.02.05 Sideline behaviour [C]
    C.03 Officials
        C.03.01 Official identity and crew per game [C]
        C.03.02 Official tendencies as of date [C]
        C.03.03 Official experience and assignment level [P]
    C.04 Table officials
        C.04.01 Official scorer and the scorebook authority [P]
        C.04.02 Timer and game-clock operation errors [C]
        C.04.03 Shot-clock operator errors [C]
        C.04.04 Home stat crew bias [P]
    C.05 Crowd and arena personnel
        C.05.01 Crowd size and share of capacity [C]
        C.05.02 Crowd loudness [C]
        C.05.03 Crowd allegiance share (neutral sites) [P]
        C.05.04 Band, cheer, mascots and staff on the floor [C]
D GAME STATE
    D.01 Score state
        D.01.01 Score and margin every frame [C]
        D.01.02 Score-change events [C]
        D.01.03 Lead changes and ties [P]
        D.01.04 Runs (points in last 2, 4, 6 min) [C]
        D.01.05 Run events (start, end, size) [P]
        D.01.06 Scoring droughts [M]
    D.02 Clock and phase state
        D.02.01 Period, game clock, shot clock, clock running [C]
        D.02.02 Phase stamps (5-min window, media segment, last 4 min, clutch) [C]
        D.02.03 Time-and-score windows (two-for-one, foul to extend, last shot) [C]
        D.02.04 Garbage time [P]
    D.03 Possession state
        D.03.01 Team in possession, possession and chance IDs [C]
        D.03.02 Phase (half court, transition, throw-in, FT, jump, timeout, review) [C]
        D.03.03 Seconds since change of control [C]
        D.03.04 Possession start type [C]
        D.03.05 Live-time split by control state [C]
    D.04 Ball state
        D.04.01 Ball-control state (6 states) [C]
        D.04.02 Ball handler [C]
        D.04.03 Ball position x, y, height [C]
        D.04.04 Ball action state (held, dribbled, passed, shot, loose, OOB, dead) [C]
        D.04.05 Try in flight and ring contact [C]
        D.04.06 Ball visibility and inference [C]
    D.05 Foul state
        D.05.01 Team fouls and bonus state [C]
        D.05.02 Personal fouls per player [C]
        D.05.03 Fouls to give [C]
        D.05.04 Foul trouble flags [C]
        D.05.05 Technical and flagrant counts toward disqualification [C]
    D.06 Timeout, challenge and review state
        D.06.01 Timeouts left by type [C]
        D.06.02 Coach's challenge available [C]
        D.06.03 Media-timeout slot state [C]
        D.06.04 Stoppage kind and review in progress [C]
    D.07 Lineup state
        D.07.01 Players on floor and lineup keys [C]
        D.07.02 Minutes together this season [C]
        D.07.03 Stint length and continuous minutes [C]
        D.07.04 Lineup composition (size, positions, shooting) [M]
        D.07.05 Matchups and mismatches on the floor [C]
    D.08 Restart and dead-ball state
        D.08.01 Dead-ball reason and restart type and spot [C]
        D.08.02 Free-throw state [C]
    D.09 Momentum, situation and win probability
        D.09.01 Pre-possession win probability [C]
        D.09.02 Expected points of current possession [C]
        D.09.03 Belief state (system as viewer) [C]
        D.09.04 Previous possession result [C]
        D.09.05 Defensive scheme state [C]
        D.09.06 Offensive set in progress [C]
        D.09.07 Coach quiz and belief consistency [C]
    D.10 Spatial and visibility state
        D.10.01 Relative geometry and spacing [C]
        D.10.02 Players visible, missing and imputed [C]
        D.10.03 Data-quality flag and source per value [C]
        D.10.04 Blind vs anchored pass [C]
E INDIVIDUAL ACTIONS
    E.01 Locomotion and footwork
        E.01.01 Stand, walk, jog, run, sprint [C]
        E.01.02 Defensive slide, backpedal and crossover run [P]
        E.01.03 Jumps (takeoff, height, purpose) [P]
        E.01.04 Stops, pivots, first step and plant foot [P]
        E.01.05 Gather and pre-dribble / split-step travel cues [M]
        E.01.06 Change of direction [P]
        E.01.07 Falls and players on the floor [C]
        E.01.08 Landing space of jump shooters [M]
    E.02 Ball handling
        E.02.01 Touches, touch time and hand [C]
        E.02.02 Dribble count and dribble hand [C]
        E.02.03 Dribble moves (crossover, between legs, behind back, hesitation, spin, retreat) [C]
        E.02.04 Other dribble moves (in-and-out, push/speed, pound, snatch-back, half spin) [P]
        E.02.05 Drives [C]
        E.02.06 Fakes (shot fake, pass fake, jab step) [M]
        E.02.07 Time of possession per player [C]
        E.02.08 Ball pressure on the handler [C]
    E.03 Passing
        E.03.01 Pass types (11 + unseen) [C]
        E.03.02 Pass metrics (speed, distance, angle, lane openness) [C]
        E.03.03 Pass outcome (completed, deflected, intercepted, thrown away) [C]
        E.03.04 Pass chain (assist, hockey assist, potential assist, screen assist) [C]
        E.03.05 Receiver's first action [C]
        E.03.06 Pass delivery (one/two hands, off the dribble, no-look) [M]
        E.03.07 Throw-in passes [P]
        E.03.08 Lobs and alley-oops [C]
    E.04 Shooting
        E.04.01 Shot type [C]
        E.04.02 Layup and finish subtypes [P]
        E.04.03 Shot location (release x, y, r, theta, zones) [C]
        E.04.04 Contest (closest defender, closing speed) [C]
        E.04.05 Contest form (hand up, high/low hand, contest height) [P]
        E.04.06 Release attributes (height, time, arc, entry angle) [C]
        E.04.07 Shot context (dribbles before, touch time, shot clock, off a screen) [C]
        E.04.08 Rim outcome, bank shot, block, and-one [C]
        E.04.09 Assisted vs self-created [C]
        E.04.10 Shot quality [C]
        E.04.11 End-of-period heaves [C]
        E.04.12 Shooter's footwork into the shot [P]
    E.05 Rebounding
        E.05.01 Offensive and defensive rebounds, team rebounds [C]
        E.05.02 Contested, long/short, tip-outs [C]
        E.05.03 Box-outs [C]
        E.05.04 Crashers and leakers [C]
        E.05.05 Rebound positioning at the release [P]
    E.06 Screening (individual)
        E.06.01 Setting a screen [C]
        E.06.02 Screen geometry (angle, contact distance, duration) [C]
        E.06.03 Screener's action after (roll, pop, slip, short roll, ghost) [C]
        E.06.04 Illegal (moving) screens [P]
    E.07 Cuts and off-ball movement
        E.07.01 Cut types (basket, backdoor, flare, curl, straight, shallow) [C]
        E.07.02 Named cuts (UCLA, Iverson, zipper, flash, V-cut, L-cut, shuffle, rip, Euro) [P]
        E.07.03 Relocate, lift, drift, rim run, corner sprint [C]
        E.07.04 Off-ball gravity [C]
    E.08 Post play
        E.08.01 Post touches and entries [C]
        E.08.02 Seal and post positioning [C]
        E.08.03 Post moves (drop step, hook, up-and-under, face-up, spin) [C]
        E.08.04 Post dislodging and hook-and-hold [P]
    E.09 On-ball and individual defence
        E.09.01 Defensive stance and distance to the handler [C]
        E.09.02 Containment and blow-bys [C]
        E.09.03 Closeouts (distance, speed, type) [C]
        E.09.04 Contests [C]
        E.09.05 Steals, deflections, blocks, charges drawn, loose balls [C]
        E.09.06 Off-ball denial posture [P]
        E.09.07 Reaction time and anticipation [C]
        E.09.08 Verticality and hands up [C]
    E.10 Free-throw routine
        E.10.01 Routine time and dribbles [C]
        E.10.02 Arc consistency [C]
    E.11 Communication and gestures
        E.11.01 Defensive communication proxies [C]
        E.11.02 Play-call signals by players [C]
        E.11.03 Player gestures toward officials and opponents (taunting, celebration) [M]
F GROUP TACTICS: OFFENCE
    F.01 Transition offence (OFF.F1)
        F.01.01 Transition start, end and class (state rule) [C]
        F.01.02 Every analyst transition definition side by side [C]
        F.01.03 Outlet and advance [C]
        F.01.04 Lane filling and roles (handler, rim runner, wings, trailer, leak-out) [C]
        F.01.05 Numbers advantage (2v1, 3v2, 4v3) [C]
        F.01.06 Push after makes and free throws [C]
        F.01.07 Passed-up breaks and pull-backs [C]
        F.01.08 Named breaks (incl. MSU/Izzo) [C]
    F.02 Early offence (OFF.F2)
        F.02.01 Drag and double drag ('77') [C]
        F.02.02 Pistol / 21 [C]
        F.02.03 Trailer actions and early post [C]
        F.02.04 Flow into the half court [C]
    F.03 Half-court alignments and motion starts (OFF.F3, MS)
        F.03.01 Alignment snapshot and family match [C]
        F.03.02 Named starts (Horns, 1-4, box, stack, 5-out, ...) [C]
    F.04 Continuity and motion systems (OFF.F4)
        F.04.01 System label per possession and per game [P]
        F.04.02 Rule-based motion reads [C]
    F.05 Ball-screen offence (OFF.F5)
        F.05.01 Screen location and angle [C]
        F.05.02 Screener pre-action (how the screener arrives) [P]
        F.05.03 Screener action after and handler read [C]
        F.05.04 Off-ball spacing tags during the PnR [P]
        F.05.05 Double ball screens (Spain, Detroit, stack, step-up) [C]
    F.06 Handoffs (OFF.F6)
        F.06.01 Handoff, fake handoff, keep [C]
    F.07 Post offence (OFF.F7)
        F.07.01 Post entries, splits, high-low, duck-in [C]
    F.08 Off-ball screens (OFF.F8.1, F8.3)
        F.08.01 Down, flare, back, cross, stagger, pin-down, elevator, hammer [C]
        F.08.02 Screen-use reads (curl, fade, straight, reject) [C]
    F.09 Isolation and spread (OFF.F9, F10)
        F.09.01 Isolation and clear-outs [C]
        F.09.02 Drive-and-kick and paint touches [P]
    F.10 Zone and press offence (OFF.F11, F12)
        F.10.01 Zone offence actions [C]
        F.10.02 Press break [C]
    F.11 Special situations (OFF.F13)
        F.11.01 After timeout (ATO) [C]
        F.11.02 BLOB and SLOB [C]
        F.11.03 End of half and end of game [C]
        F.11.04 Late clock [C]
        F.11.05 Free-throw alignments [C]
        F.11.06 Jump-ball plays [C]
        F.11.07 Delay and clock-kill [C]
        F.11.08 Two-for-one and last shot [C]
    F.12 Offensive rebounding and spacing systems (OFF.F14, F15)
        F.12.01 Crash vs get-back policy [C]
        F.12.02 Spacing systems (4-out, 5-out, dunker spot) [C]
    F.13 Recognition infrastructure and labels
        F.13.01 Set templates, match, timeline, phases [C]
        F.13.02 Counters and broken plays [C]
        F.13.03 Unmatched chances and new-set clustering [C]
        F.13.04 Template status and role-based templates [C]
        F.13.05 Name collisions and secondary vocabularies [C]
        F.13.06 Synergy-style outcome labels [C]
        F.13.07 MSU addendum and playbook library [C]
        F.13.08 Team style measures [C]
        F.13.09 Ball movement (passes per chance, reversals, side changes) [P]
G GROUP TACTICS: DEFENCE
    G.01 Man principles and on-ball rules (DEF.F1, F2)
        G.01.01 Man philosophy (help-first, pressure, directional, switching, pack line) [C]
        G.01.02 MSU documented principles [C]
        G.01.03 Force direction and ball pressure [C]
        G.01.04 Pick-up point [M]
    G.02 Screen coverages (DEF.F3, F4, F5)
        G.02.01 Ball-screen coverage (4 coarse, 13+ fine, drop depth) [C]
        G.02.02 Handoff coverage [C]
        G.02.03 Off-ball screen coverage [C]
    G.03 Post defence (DEF.F6)
        G.03.01 Post positioning (front, three-quarter, behind) [C]
        G.03.02 Post doubles and rotations [C]
        G.03.03 Lob protection [P]
    G.04 Help, rotation and closeouts (DEF.F7)
        G.04.01 Help position per defender per second [C]
        G.04.02 Rim protector [C]
        G.04.03 Roller coverage and help actions (tag, stunt, dig, step-and-release) [C]
        G.04.04 Rotations and reaction delay [C]
        G.04.05 Closeouts [C]
    G.05 Zones, presses and junk (DEF.F8, F9, F10)
        G.05.01 Man vs zone discrimination and named zones [C]
        G.05.02 Presses (full and half court, named, policies) [C]
        G.05.03 Junk defences (box-and-1, triangle-and-2) [C]
    G.06 Scheme changes and policies (DEF.F11)
        G.06.01 Scheme change events and triggers [C]
        G.06.02 Scheme policy by context [C]
    G.07 Transition defence (DEF.F12)
        G.07.01 Get-back clocks, ball stopper, defenders back [C]
        G.07.02 Cross-matches and recoveries [C]
    G.08 Defensive rebounding (DEF.F13)
        G.08.01 Box-outs and crash numbers [C]
    G.09 Special situations and fouling strategy (DEF.F14, F15)
        G.09.01 Inbound (BLOB/SLOB) defence [C]
        G.09.02 End-game defence and foul-up-3 [C]
        G.09.03 Foul-trouble effect on defensive aggressiveness [P]
    G.10 Matchups, communication and outcome labels (DEF.F16, F17, F18)
        G.10.01 Matchup per defender per second [C]
        G.10.02 Switch mismatches [C]
        G.10.03 Shell shape [C]
        G.10.04 Communication vocabulary as behaviours [C]
        G.10.05 Defensive play-type outcome labels [C]
        G.10.06 Per-second label hierarchy [C]
        G.10.07 MSU's own defence measured the same way [C]
H OUTCOMES AND VALUE
    H.01 Possession and chance outcomes
        H.01.01 Possession end type and points [C]
        H.01.02 Chance outcomes (11-outcome multinomial) [C]
        H.01.03 Second-chance points and putbacks [C]
        H.01.04 Turnover types and costs [C]
    H.02 Team efficiency and box-score outcomes
        H.02.01 Box score (team and player) [C]
        H.02.02 Four factors, pace, efficiency (as of date) [C]
        H.02.03 Fast-break, paint, off-turnover points [C]
        H.02.04 Bench points and starter/bench split [P]
    H.03 Expected value
        H.03.01 Possession value at 10 Hz [C]
        H.03.02 Pass, shot and turnover parts of value [C]
        H.03.03 Value change per action and credit [C]
        H.03.04 Shot quality [C]
        H.03.05 Shot-making (points above shot quality) [P]
        H.03.06 Decision quality [C]
        H.03.07 Value of fouls drawn, offensive rebounds, turnovers [C]
        H.03.08 Configuration and set value [C]
        H.03.09 Neural sequence outcome model [C]
    H.04 Player and lineup value
        H.04.01 Off-ball value (gravity, screens) [C]
        H.04.02 Player vs player [C]
        H.04.03 Shrunk player estimates [C]
        H.04.04 Pair and lineup effects (RAPM-style) [C]
        H.04.05 Public impact metrics (BPM, PORPAG, RAPM, etc.) [C]
        H.04.06 Defensive value per player (stops, contests, deterrence) [P]
        H.04.07 Passing network and movement coordination [C]
    H.05 Probabilities and predictions
        H.05.01 Pre-game win probability, margin, total [C]
        H.05.02 In-game win probability [C]
        H.05.03 5-minute window predictions [C]
        H.05.04 Player prop distributions [C]
        H.05.05 Calibration and scoring [C]
        H.05.06 Edge and closing-line value [C]
        H.05.07 Possession-engine components [C]
        H.05.08 Baselines, walk-forward and sample rules [C]
    H.06 Pressure, clutch and surprise
        H.06.01 Pressure performance [C]
        H.06.02 Surprise per event [C]
I PHYSICAL AND LOAD
    I.01 Kinematics
        I.01.01 Velocity, acceleration, heading [C]
        I.01.02 Tracked point and filter [C]
        I.01.03 Physics limits [C]
    I.02 Load
        I.02.01 Distance and time by 0.1 m/s speed bin [C]
        I.02.02 Acceleration and deceleration efforts [C]
        I.02.03 Top speed (p95 and 1 s peak) [C]
        I.02.04 Load denominators (live, minutes played, on-court) [C]
        I.02.05 Coverage-corrected load and exclusions [C]
        I.02.06 Jump load (count and height per minute) [P]
        I.02.07 Direction-weighted load (lateral and backward running) [M]
        I.02.08 Contact load (screens set and absorbed, box-outs, post contact) [P]
    I.03 Fatigue, minutes and recovery
        I.03.01 Minutes played and continuous minutes [C]
        I.03.02 Within-game decline [C]
        I.03.03 Recovery after stoppages [C]
        I.03.04 Relative speed (v_ref) and interpretation thresholds [C]
        I.03.05 Season load trend vs availability [C]
        I.03.06 Calibration of physical measures [C]
J CONTEXT
    J.01 Schedule, travel and rest
        J.01.01 Tip time (local, UTC), day of week [C]
        J.01.02 Days of rest and games in 7 and 14 days [C]
        J.01.03 Travel distance, time zones, mode [C]
        J.01.04 Road-trip structure [M]
        J.01.05 Tip time on each team's body clock [P]
        J.01.06 Weather [C]
        J.01.07 Academic calendar [C]
    J.02 Venue, crowd and officials
        J.02.01 Home, away, neutral and proximity [C]
        J.02.02 Attendance and crowd [C]
        J.02.03 Altitude difference [C]
        J.02.04 Referee crew features as of date [C]
        J.02.05 Jersey pairing and contrast [C]
    J.03 Teams, people and form
        J.03.01 Availability, minutes limits, continuity [C]
        J.03.02 Ratings and rankings as of date (KenPom, Torvik, NET, AP) [C]
        J.03.03 Opponent recent form [P]
        J.03.04 Coach head-to-head and prior meetings [C]
        J.03.05 Opponent baselines and scouting [C]
    J.04 Stakes and calendar position
        J.04.01 Stakes stamp (conference, tournament, seeds, rivalry, national TV) [C]
        J.04.02 Standings and seeding at stake [C]
        J.04.03 Season phase and game number [P]
    J.05 Markets
        J.05.01 Closing lines (spread, total, moneyline) [C]
        J.05.02 Snapshot schedule (open, 24 h, 1 h, close, 1H, props) [C]
        J.05.03 Prediction-market prices [C]
        J.05.04 Fair probabilities (de-vig) [C]
        J.05.05 Line movement as a feature (separate model variant) [C]
        J.05.06 Public betting share [M]
    J.06 Beliefs and pre-game card
        J.06.01 Beliefs register and hypothesis candidates [P]
        J.06.02 Pre-game card (24 h and 1 h) [C]
        J.06.03 Feature registry and causal classes [C]
K COACHING AND DECISIONS
    K.01 Coach decisions
        K.01.01 Play calls (set called, source) [C]
        K.01.02 Substitution and rotation patterns [C]
        K.01.03 Timeout timing vs runs; timeouts left at half end [C]
        K.01.04 Challenge decisions [C]
        K.01.05 End-game fouling, two-for-one, last-shot holds [C]
        K.01.06 Starting lineup and matchup assignment [C]
        K.01.07 Scheme adjustments and halftime changes [C]
        K.01.08 Tempo choice (push vs pull back) [C]
        K.01.09 Foul-trouble management (sitting a player) [C]
        K.01.10 Press and zone usage decisions [C]
        K.01.11 Icing the free-throw shooter [P]
        K.01.12 Minutes limits and rest management [C]
        K.01.13 Coach reactions and sideline behaviour [C]
        K.01.14 Coach card system tags [C]
        K.01.15 Opposing coaches' records [C]
    K.02 Player decisions
        K.02.01 Shoot, pass, drive choice and decision quality [C]
        K.02.02 Decision latency [C]
        K.02.03 After-error behaviour [C]
        K.02.04 Shot selection by shot clock and zone [C]
L MEDIA AND VIDEO
    L.01 Video files and timeline
        L.01.01 Capture standard and best-quality download [C]
        L.01.02 Intake report [C]
        L.01.03 File hash and immutability [C]
        L.01.04 Timeline mapping (VFR, interlacing) [C]
        L.01.05 Download provenance and platform terms [C]
        L.01.06 Processing resolution and hardware decode [C]
    L.02 Broadcast picture
        L.02.01 Camera shot type (9 classes) [C]
        L.02.02 Finer camera views (reverse angle, baseline, under-basket, skycam, iso) [P]
        L.02.03 Replays and slow motion [C]
        L.02.04 Coverage score and usable possessions [C]
        L.02.05 Graphics mask (scorebug, lower thirds, wipes) [C]
        L.02.06 Commercial breaks and studio segments [C]
        L.02.07 Broadcast replays as secondary evidence [P]
    L.03 Scorebug and on-screen graphics
        L.03.01 Scorebug templates per network [C]
        L.03.02 Scorebug OCR fields [C]
        L.03.03 Scorebug lag vs arena board [C]
        L.03.04 Stat graphics and lower thirds as weak labels [M]
    L.04 Audio and commentary
        L.04.01 Whistles [C]
        L.04.02 Buzzers and horns [P]
        L.04.03 Crowd loudness and music flag [C]
        L.04.04 Commentary transcript and weak labels [C]
        L.04.05 Audio-video alignment [C]
        L.04.06 Broadcast network and crew [C]
    L.05 Visual outputs
        L.05.01 Broadcast plus top-down replay in sync [C]
        L.05.02 Traceable numbers with n and interval [C]
        L.05.03 Overlays, boards, palette [C]
        L.05.04 Narration from state [C]
    L.06 Perception from video
        L.06.01 Person detection and person filter [C]
        L.06.02 Team label per detection [C]
        L.06.03 Persistent tracks, track quality and gaps [C]
        L.06.04 Frame-exit memory and off-screen estimates [C]
        L.06.05 Ground point at the feet [C]
        L.06.06 Player identity (lineup-constrained, jersey numbers, orientations) [C]
        L.06.07 Identity re-confirmation and restoration [C]
        L.06.08 Identity confusions and per-player accuracy [C]
        L.06.09 Synthetic kit images (team colour only) [C]
        L.06.10 Ball detection, holder and event times [C]
        L.06.11 Make or miss and made-basket fusion [C]
        L.06.12 Short-horizon position forecasts [C]
        L.06.13 Public tracking-set sanity checks and source comparison [C]
        L.06.14 Officials and non-players detected separately [C]
M DATA, QUALITY AND GOVERNANCE
    M.01 Sources and licences
        M.01.01 Source register and use class [C]
        M.01.02 Licence register (datasets, models, libraries) [C]
        M.01.03 Secrets and keys outside the repo [C]
        M.01.04 Rate limits, call logs and caching [C]
        M.01.05 Point-in-time ratings only [C]
        M.01.06 Source definition register (each source's own definitions) [P]
    M.02 Provenance and lineage
        M.02.01 Raw copy before parsing [C]
        M.02.02 Lineage to raw rows and transform version [C]
        M.02.03 Model version, source, confidence on every value [C]
        M.02.04 ID crosswalk [C]
        M.02.05 As-of rules and leakage tests [C]
        M.02.06 Event model (one row per event, chains, unmatched stream) [C]
    M.03 Quality checks
        M.03.01 Data contracts and quarantine [C]
        M.03.02 Invariants on the state record [C]
        M.03.03 Accounting identities and completeness [C]
        M.03.04 Cross-source checks [C]
        M.03.05 Drift checks [C]
        M.03.06 Known-bias register [P]
        M.03.07 Independent re-derivation [C]
        M.03.08 Scoreboard discrepancy classes and answers [C]
        M.03.09 Ontology coverage check [P]
    M.04 Review, labels and validation
        M.04.01 Flag triggers and review queue [C]
        M.04.02 Labels with provenance and consistency [C]
        M.04.03 Gold sets frozen [C]
        M.04.04 Gates and robustness [C]
        M.04.05 Metrics and intervals (HOTA, bootstrap by game, multiple testing) [C]
        M.04.06 External consultant (JEV) log [P]
    M.05 Runs, errors and compute
        M.05.01 Run records and requirement results [C]
        M.05.02 Error catalogue and failure analysis [C]
        M.05.03 Compute and storage accounting [C]
        M.05.04 Reproducibility, resumable chunks, versioned outputs [C]
    M.06 Governance and coordination
        M.06.01 Schemas, units in names, thresholds in config [C]
        M.06.02 Registry versioning and change log [C]
        M.06.03 Vocabulary map [C]
        M.06.04 Rights gate, privacy and footage control [C]
        M.06.05 Read-only market collection [C]
        M.06.06 Board, protocol, user inputs, freeze [C]
        M.06.07 Hypothesis protocol [C]
        M.06.08 Taxonomy detection signatures [C]
        M.06.09 Pitch package [C]
```

## 5. Coverage matrix (per leaf)

Gap column: proposed ID(s) for partial and missing leaves (details in section 6), or an existing repo proposal.

### A. Game structure and rules

Everything the 2026-27 NCAA men's rules book defines about how a game is organised, timed, scored, penalised, restarted, officiated and reviewed.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A.01.01 | Team's own basket and direction of play *(note: new-IV-21 (change of baskets) is proposed in config/invariants.yaml.)* | 1-1.2, 1-1.3 | R-CG-06 | state_frame.basket_attacked, frames.homography |  | covered |  |
| A.01.02 | Halves (2 x 20:00) | 5-6.1 | R-IV-16 R-SR-01 R-MD-01 | state_frame.period, state_frame.game_clock_s |  | covered |  |
| A.01.03 | End of period and try in flight *(note: Invariant wording proposed as new-IV-23.)* | 5-7, 5-1.5, 6-6.1 | R-MB-06 | shots.release_before_horn, made_basket_events.release_vs_horn, made_basket_events.release_game_clock_s |  | covered |  |
| A.01.04 | Intermissions (half time, before extra periods) — Half-time intermission and the 1-minute intermission before each extra period; start, end and length. | 5-8, 5-9 | R-PL-04 | state_second.phase, state_frame.stoppage_kind |  | partial | new-SR-1 |
| A.01.05 | Extra periods (overtime) *(note: Team-foul carry-over into extra periods is proposed as new-IV-20.)* | 5-9.1 to 5-9.4 | R-IV-16 R-IV-10 R-EV-14 | games.overtime_periods, jump_balls.kind, state_frame.period |  | covered |  |
| A.01.06 | Final result and winner | 5-2, 2-9.13 | R-FD-01 R-IV-04 R-IV-15 R-DQ-06 | games.home_score, games.away_score, games.home_period_points, team_box.points |  | covered |  |
| A.01.07 | Forfeit and no contest — A forfeit (2-0 unless 30 min played, then the score stands) or a no contest ends a game abnormally. | 5-3 |  | games.status |  | partial | existing: new-IV-30; new-FD-2 |
| A.01.08 | Interrupted or suspended game — A game interrupted by events beyond the officials' control and resumed or terminated later. | 5-4 |  |  |  | missing | new-FD-3 |
| A.01.09 | Game type, season type and round |  | R-MD-14 R-CX-15 R-FD-01 | games.game_type, games.season_type, games.tournament_round, games.home_seed |  | covered |  |
| A.01.10 | Rules edition in force per game — Which rules edition (season) and which competition-specific rules apply to a game, e.g. 35 s vs 30 s shot clock, 2025-26 coach's challenge, 2026-27 appeals and logo rules. *(note: R-TR-18 only mentions the shot-clock era for transition thresholds.)* | Preface; Rules changes 2025-26 and 2026-27 | R-TR-18 |  |  | partial | new-RL-1 |
| A.02.01 | Game clock value and display | 1-18.2, 5-10 | R-SR-01 R-SY-01 R-MD-01 | state_frame.game_clock_s, scoreboard_ocr.game_clock_parsed_s |  | covered |  |
| A.02.02 | Game clock start triggers — The clock starts when a throw-in is legally touched inbounds, a jump ball is legally tapped, or a missed live free throw is touched. | 5-10.1 to 5-10.3 | R-IV-05 R-SR-01 | state_frame.clock_running, restarts.video_ts_ms_live |  | partial | new-SR-2 |
| A.02.03 | Game clock stop events | 5-11, 2-10.12 | R-IV-05 R-IV-06 R-SR-01 | state_frame.clock_running, state_frame.live_ball |  | covered |  |
| A.02.04 | Minimum time off on a touch (0.3 s) and tap-only rule — In the last 59.9 s at least 0.3 s comes off on a touch followed by a stop; with 0.3 s or less only a tap can score. | 5-10.2.d, 5-10.3.d, 5-1.19 |  | shots.release_before_horn |  | partial | existing: new-IV-22 |
| A.02.05 | Timing mistakes and corrections *(note: Statute 'within the half' is proposed as new-IV-27.)* | 5-12, 2-12 | R-IV-05 R-SB-01 R-SR-04 | reviews.review_kind, reviews.game_clock_before_s, reviews.game_clock_after_s |  | covered |  |
| A.02.06 | Video time to game clock map |  | R-MD-08 R-SY-02 | events.sync_residual_s, state_frame.video_ts_ms, state_frame.clock_inferred |  | covered |  |
| A.03.01 | Shot clock value and status | 2-11.1, 1-19 | R-SR-01 R-SY-01 | state_frame.shot_clock_s, state_frame.shot_clock_status |  | covered |  |
| A.03.02 | Shot clock start *(note: Also proposed as new-IV-01.)* | 2-11.5 | R-MD-06 R-IV-07 | chances.start_shot_clock_s, chances.shot_clock_start_rule |  | covered |  |
| A.03.03 | Reset to 30 s | 2-11.6.b | R-MD-06 R-SY-08 R-SY-09 R-IV-07 | shot_clock_resets.value_after_s, shot_clock_resets.rule_citation |  | covered |  |
| A.03.04 | Reset to 20 s flat (offensive rebound after ring contact) | 2-11.6.d.1 to d.9 | R-MD-06 R-SY-09 R-MB-07 R-IV-07 | shot_clock_resets.rule_expected_after_s, chances.shot_clock_start_s |  | covered |  |
| A.03.05 | Reset to max(20, remaining) | 2-11.6.c | R-MD-06 R-IV-07 | shot_clock_resets.value_after_s, shot_clock_resets.rule_match |  | covered |  |
| A.03.06 | No-reset situations — Unexpired time continues: ball out of bounds off the defence, injury, end of timeout, arrow to team in control, technical on the team in control, etc. *(note: shot_clock_resets.cause has 6 coarse values; config/invariants.yaml shot_clock_reset_table has 33 causes.)* | 2-11.6.a.1 to a.9 | R-SY-08 R-SY-09 | shot_clock_resets.cause |  | partial | new-SY-2 |
| A.03.07 | Shot clock off and reactivation *(note: Also new-IV-05.)* | 2-11.2, 2-11.8 | R-MD-06 R-IV-07 | state_frame.shot_clock_status, shot_clock_resets.after_class |  | covered |  |
| A.03.08 | Shot-clock violation and horn vs release *(note: Also new-IV-06.)* | 9-11, 2-11.3 | R-EV-10 R-MB-06 | turnovers.turnover_type, made_basket_events.release_shot_clock_s |  | covered |  |
| A.03.09 | Single working shot clock | 1-19 (2025-26 change) | R-IV-07 | scoreboard_ocr.display |  | covered |  |
| A.04.01 | Player control and team control | 4-9 | R-MD-02 R-SR-06 | state_frame.ball_control_state, ball_control_state.state | global_metadata.ball_control_state | covered |  |
| A.04.02 | Possession (our definition) |  | R-MD-04 R-SY-04 R-SY-06 | possessions.possession_id, possessions.start_type_code, possessions.end_type | TR.ST | covered |  |
| A.04.03 | Chance |  | R-MD-04 R-SY-05 R-PE-02 | chances.chance_number, chances.start_cause, chances.end_type, chances.outcome_code |  | covered |  |
| A.04.04 | Possession counts under each source's definition — KenPom/Torvik formula possessions, CBBD and hoopR NCAA-engine possession numbers and Synergy-style chances stored side by side with ours. |  | R-IV-15 | possessions.poss_num_ncaa, team_box.possessions_source |  | partial | new-SY-3 |
| A.04.05 | Opening and overtime jump balls | 6-2 | R-EV-14 R-DT-15 | jump_balls.kind, jump_balls.tip_winner_team_id, jump_balls.tip_direction_deg |  | covered |  |
| A.04.06 | Held ball | 6-4.2 | R-RF-07 R-IV-08 R-DT-15 | jump_balls.held_ball_player_ids, events.event_family |  | covered |  |
| A.04.07 | Alternating-possession arrow *(note: Arrow rules proposed as new-IV-19.)* | 6-3, 6-4 | R-MD-12 R-SY-01 R-SR-05 | state_frame.possession_arrow, restarts.arrow_before, restarts.arrow_after |  | covered |  |
| A.04.08 | Jump-ball violations — Tossing official's toss, non-jumpers entering the circle early, jumper catching the tossed ball, etc. | 9-8 |  | jump_balls.kind |  | partial | new-EV-1 |
| A.04.09 | Live ball and dead ball | 6-1, 6-5, 6-6 | R-SR-01 R-MD-05 | state_frame.live_ball, restarts.dead_ball_reason |  | covered |  |
| A.04.10 | Point of interruption | 4-28, 7-5 | R-SR-08 | restarts.restart_type |  | covered |  |
| A.04.11 | Inadvertent whistle | 4-20 | R-SR-08 | restarts.dead_ball_reason, whistles.link_type |  | covered |  |
| A.04.12 | Frontcourt and backcourt status of team control — Whether the team in control has established the ball in its frontcourt (ball and both feet), basis of backcourt rules. | 4-23, 9-12 | R-IV-14 | player_positions.court_half |  | partial | new-SR-3 |
| A.04.13 | 10-second backcourt count — Team must bring the ball into its frontcourt within 10 s. | 9-10 | R-IV-14 | turnovers.turnover_type |  | partial | new-SR-4 |
| A.04.14 | Closely guarded 5-second count — A frontcourt player holding the ball, guarded within 1.83 m, may not hold it for 5 s. | 9-14, 4-17.2 | R-EV-10 | turnovers.turnover_type, touches.pressure_m |  | partial | existing: new-IV-15; new-SR-5 |
| A.04.15 | Three seconds in the lane — No offensive player stays in the frontcourt lane > 3 s while his team controls the ball. | 9-9 | R-EV-10 | turnovers.turnover_type, player_positions.x_m |  | partial | existing: new-IV-17; new-ST-1 |
| A.05.01 | Two- and three-point field goals | 5-1, 1-7 | R-IV-12 R-EV-07 R-MB-04 | shots.value_attempted, shots.is_three_by_geometry |  | covered |  |
| A.05.02 | Free-throw point | 5-1.3, 8 | R-IV-04 | free_throws.made, score_events.delta_points |  | covered |  |
| A.05.03 | Goaltending and basket interference awards *(note: Award rules proposed as new-IV-24.)* | 9-15, 9-15.2 (2025-26 change) | R-MB-05 | made_basket_events.edge_case |  | covered |  |
| A.05.04 | Illegal assistance in scoring or blocking — Lifting or assisting a teammate to score or block awards the try's points or a violation. | 9-16 |  | made_basket_events.edge_case |  | partial | existing: new-IV-24 |
| A.05.05 | Goal in the wrong basket — A ball accidentally put in the opponent's basket counts for the opponent (credited to its captain); deliberately is a violation. | 5-1.2 | R-MB-05 | score_events.event_kind |  | partial | new-MB-1 |
| A.05.06 | Score corrections and correctable errors | 2-12, 2-9.13 | R-SB-01 R-SB-02 R-SR-02 | reviews.review_kind, score_events.review_id, state_corrections.corrected_value |  | covered |  |
| A.06.01 | Common personal foul (non-shooting) | 4-15.2.a, 10-1 | R-RF-03 R-SR-03 | fouls.foul_type, fouls.foul_subtype |  | covered |  |
| A.06.02 | Shooting foul | 4-1, 4-8, 10-1 Penalty | R-RF-03 R-SR-09 | fouls.foul_type, fouls.shot_value_fouled, fouls.ft_awarded |  | covered |  |
| A.06.03 | Player-control foul | 4-15.2.a.1 | R-SR-03 | fouls.foul_subtype, foul_state.player_control_fouls |  | covered |  |
| A.06.04 | Team-control foul | 4-15.2.a.2 | R-SR-03 | fouls.foul_subtype, foul_state.team_control_fouls |  | covered |  |
| A.06.05 | Loose-ball foul | 4-15.2.a.3, 4-24 | R-SR-03 R-RF-03 | fouls.foul_type, foul_state.loose_ball_fouls |  | covered |  |
| A.06.06 | Blocking vs charging and the restricted area — Block/charge adjudication, legal guarding position, secondary defender in the restricted area. *(note: foul_subtype has no `blocking` value; the restricted-area status of the secondary defender is not stored.)* | 4-5, 4-7, 4-17, 4-31, 4-36 | R-EV-09 R-RF-04 | defensive_events.type, fouls.foul_subtype, official_positions.signal_pose |  | partial | new-RF-1 |
| A.06.07 | Double and simultaneous personal fouls *(note: Penalty proposed as new-IV-32.)* | 4-15.2.b, 10-1 | R-SR-03 | fouls.foul_subtype, foul_state.double_simultaneous_fouls |  | covered |  |
| A.06.08 | Multiple, false double and false multiple fouls — Two or more teammates foul one opponent; separate fouls with time between them. | 4-15, 8-8, 8-9, 10-1 Penalty b | R-SR-09 | free_throws.award_type |  | partial | new-RF-2 |
| A.06.09 | Flagrant 1 | 4-15.2.c.1 | R-RF-03 R-SR-03 | fouls.foul_type, foul_state.flagrant1_fouls, foul_state.flagrant1_player_cum |  | covered |  |
| A.06.10 | Flagrant 2 and ejection | 4-15.2.c.2, 4-14 | R-RF-03 R-SR-03 | fouls.foul_type, player_box.ejected, foul_state.flagrant2_fouls |  | covered |  |
| A.06.11 | 'Intentional' foul label vs the rules book — The live doc's 9 foul types include `intentional`; the 2026-27 rules book has no intentional-foul class (deliberate fouls are common fouls or Flagrant 1). | 4-15 | R-RF-03 | fouls.foul_type, fouls.is_end_game_intentional |  | partial | new-RF-3 |
| A.06.12 | Technical foul Class A | 10-3 | R-SR-03 R-RF-03 | fouls.foul_subtype, foul_state.technical_class_a |  | covered |  |
| A.06.13 | Technical foul Class B | 10-4 | R-SR-03 | fouls.foul_subtype, foul_state.technical_class_b |  | covered |  |
| A.06.14 | Administrative technical — Technical for administrative infractions (roster, timeouts, noise); 1 or 2 FTs. | 10-2 | R-SR-03 | foul_state.technical_admin, free_throws.award_type |  | partial | new-RF-4 |
| A.06.15 | Fouls by bench personnel and coaches | 10-3, 10-4, 4-4 | R-RF-03 R-CC-03 | fouls.offender_type, bench_events.event_type |  | covered |  |
| A.06.16 | Contact dead-ball technical | 10-3 | R-SR-03 | fouls.foul_subtype |  | covered |  |
| A.06.17 | Foul contact mechanism (signal type) — How the foul was committed: holding, pushing/charging, hand-check, illegal use of hands, blocking, tripping, hit to the head, chucking, pinning, dislodging, verticality, landing space, illegal screen, elbow. *(note: R-RF-04 (Should) reads only 6 signals; no column stores the contact mechanism of a foul.)* | App. VIII signals; App. III; 4-18, 4-19, 4-35, 4-39, 10-1.4 | R-RF-04 | official_positions.signal_pose |  | partial | new-RF-5 |
| A.06.18 | Team fouls, bonus and double bonus | 8-2, 4-26 | R-MD-07 R-SR-03 R-IV-09 | state_frame.team_fouls_msu, state_frame.bonus_state, foul_state.bonus_reached_clock_s |  | covered |  |
| A.06.19 | Disqualification (5 fouls, 3 Flagrant 1) *(note: Full rule proposed as new-IV-11.)* | 4-12, 10-1 | R-IV-03 R-MD-16 | foul_state.disqualified, fouls.fouled_out |  | covered |  |
| A.06.20 | Ejection — Removal for Flagrant 2, two Class A technicals, or other combinations; head-coach ejections. | 4-14, 10-3, 10-4 | R-RF-03 | player_box.ejected, events.event_family |  | partial | existing: new-IV-11 |
| A.06.21 | Fighting and suspensions — Fighting, suspensions and failure to serve them (2025-26 change). | 10-5, 10-14 Penalty, 10-15.10 |  |  |  | missing | new-RF-6 |
| A.06.22 | Flopping (faking being fouled) — Warning, then Class B technical; Class A when confirmed by replay. | 10-3.1.d, App. III (o), 11-2 |  |  |  | missing | new-RF-7 |
| A.06.23 | Take foul and clear-path fouls in transition |  | R-TR-25 | fouls.is_take_foul_candidate, fouls.clear_path, fouls.fouler_dist_to_ball_m |  | covered |  |
| A.06.24 | Deliberate end-game fouling |  | R-PE-07 R-SR-11 | fouls.is_end_game_intentional, state_second.foul_to_extend_window |  | covered |  |
| A.07.01 | Free-throw award type *(note: Award table in config/invariants.yaml; new-IV-07/08.)* | 8-1, 8-2, 10-1 Penalty | R-SR-09 R-RF-03 | free_throws.award_type, free_throws.attempts_n |  | covered |  |
| A.07.02 | Who attempts (shooter selection) | 8-3 | R-SR-09 | free_throws.shooter_selection, free_throws.shooter_player_id |  | covered |  |
| A.07.03 | Lane positions *(note: Space order proposed as new-IV-29.)* | 8-4 | R-DT-13 R-IV-11 | free_throws.lane_occupant_ids, free_throws.lane_def_count, free_throws.lane_expected_empty |  | covered |  |
| A.07.04 | Free-throw requirements (10 s, behind the line) *(note: new-IV-10.)* | 8-5, 9-1 | R-SR-09 R-PL-08 | free_throws.release_latency_s, free_throws.video_ts_ms_disposal |  | covered |  |
| A.07.05 | Free-throw violations | 9-1 | R-IV-11 | free_throws.violation, free_throws.violation_team, free_throws.result |  | covered |  |
| A.07.06 | What follows the last free throw *(note: new-IV-09.)* | 8-6, 8-7 | R-SR-09 R-IV-08 | free_throws.ball_after |  | covered |  |
| A.07.07 | Free-throw state machine |  | R-SR-09 | state_second.ft_state, free_throws.predicted_at_whistle, free_throws.prediction_correct |  | covered |  |
| A.07.08 | Substitutions around free throws — Entry rules during multiple free throws. | 3-6, 8-3 | R-IV-03 | substitutions.during_dead_ball |  | partial | existing: new-IV-25 |
| A.08.01 | Traveling (incl. pre-dribble and split-step travel) | 9-5, 4-27, 4-22, Points of Emphasis 5 | R-EV-10 R-DT-16 | turnovers.turnover_type |  | covered |  |
| A.08.02 | Illegal dribble (double dribble, palming/carrying) | 9-7, 4-13 | R-EV-10 | turnovers.turnover_type |  | covered |  |
| A.08.03 | Kicking and fisting the ball | 9-6 | R-SY-08 R-MD-06 | restarts.violation_code, shot_clock_resets.cause |  | covered |  |
| A.08.04 | Ball through the basket from below | 9-6 | R-MB-05 | made_basket_events.edge_case |  | covered |  |
| A.08.05 | Ball and player out of bounds | 9-2, 9-3, 7-1 | R-EV-10 R-BL-07 | turnovers.turnover_type, ball_states.out_of_bounds_event |  | covered |  |
| A.08.06 | Throw-in violations — Thrower: 5 s, leaving the spot, stepping on the court; defender: crossing the boundary plane. | 9-4 | R-DT-14 | restarts.throw_in_count_s, restarts.violation_code |  | partial | new-EV-2 |
| A.08.07 | Backcourt violation (over and back) — Team in control returns the ball to its backcourt after frontcourt status. *(note: turnover_type has ten_second_backcourt but no over-and-back value.)* | 9-12 | R-IV-14 | turnovers.turnover_type |  | partial | new-EV-3 |
| A.08.08 | Shot-clock violation | 9-11 | R-EV-10 | turnovers.turnover_type |  | covered |  |
| A.08.09 | Five-second closely guarded and ten-second backcourt | 9-10, 9-14 | R-EV-10 | turnovers.turnover_type |  | covered |  |
| A.08.10 | Three-second lane violation | 9-9 | R-EV-10 | turnovers.turnover_type |  | covered |  |
| A.08.11 | Excessive swinging of elbows — Violation (not a foul without contact). | 9-13 |  |  |  | missing | new-EV-4 |
| A.08.12 | Basket interference and goaltending | 9-15 | R-MB-05 R-EV-16 | made_basket_events.edge_case, coaches_challenges.play_type |  | covered |  |
| A.08.13 | Free-throw lane violations | 9-1 | R-IV-11 | free_throws.violation |  | covered |  |
| A.09.01 | Ball out of bounds detection | 7-1 | R-BL-07 | ball_states.out_of_bounds_event |  | covered |  |
| A.09.02 | Player who caused the ball out of bounds — Last player to touch the ball before it went out (or the player out of bounds). | 7-2 | R-EV-16 | coaches_challenges.play_type |  | partial | new-BL-1 |
| A.09.03 | Throw-in spot *(note: Boundary wording question open in dictionary_state.md item 7.)* | 7-3, 7-4, 7-5; 7-3.2.b (2025-26) | R-DT-19 R-SR-08 R-MD-03 | restarts.throw_in_spot, restarts.spot_x_m, restarts.spot_y_m |  | covered |  |
| A.09.04 | Throw-in requirements and 5-second count *(note: new-IV-16.)* | 7-6 | R-DT-14 | restarts.throw_in_count_s |  | covered |  |
| A.09.05 | Throw-in formations and first pass |  | R-DT-14 R-ST-23 | restarts.thrower_player_id, configuration_snapshots.alignment_code | OFF.F13.2 OFF.F13.3 | covered |  |
| A.09.06 | Bench personnel assisting a player out of bounds — Bench personnel physically assisting a player with the ball (2025-26). | 7-1.1 (2025-26) |  | bench_events.event_type |  | missing | new-CC-1 |
| A.10.01 | Team timeouts by length (30/60/75 s) *(note: Allotment by format proposed as new-IV-12.)* | 5-13, 5-14 | R-SR-04 R-MD-07 R-IV-10 | state_frame.to30_left_msu, state_frame.to60_left_msu, state_frame.to75_left_msu, timeouts.timeout_type |  | covered |  |
| A.10.02 | Media timeouts and media format *(note: Rules detail in new-IV-13.)* | 5-14.10 | R-MD-13 R-SR-04 R-EV-15 | timeouts.media_slot, timeouts.media_format, timeouts.became_media |  | covered |  |
| A.10.03 | Timeout request and caller | 5-13, 5-14 | R-EV-15 R-CC-02 | timeouts.called_by, timeouts.requesting_player_id, timeouts.game_clock_s |  | covered |  |
| A.10.04 | Timeouts not granted — Opponents of the throw-in team after the throw-in starts; without player control; before the opening jump; last-2-minute review rule. | 5-15 |  | timeouts.charged |  | partial | existing: new-IV-28 |
| A.10.05 | Excessive timeout and halftime carry loss | 5-17, 5-14.10 | R-SR-04 R-IV-10 | timeouts.timeout_type, timeouts.halftime_carry_loss |  | covered |  |
| A.10.06 | Injury, blood and official stoppages | 5-16, 3-5 | R-EV-11 R-TR-19 | timeouts.timeout_type, state_frame.stoppage_kind, possessions.stoppage_events |  | covered |  |
| A.10.07 | Timeout duration (actual vs allotted) | 5-14.4 | R-PL-04 | timeouts.duration_s, timeouts.shortened |  | covered |  |
| A.11.01 | Starting lineup | 3-4 | R-SY-03 R-FD-05 | player_box.starter, lineup_stints.lineup_key |  | covered |  |
| A.11.02 | Substitution procedure and timing | 3-5, 3-6 | R-SY-03 R-IV-03 R-EV-11 | substitutions.during_dead_ball, substitutions.player_in_id, substitutions.player_out_id |  | covered |  |
| A.11.03 | Late-game substitution restriction — No substitutions while the clock is stopped after a made FG in the last 59.9 s except as permitted. | 3-6 |  | substitutions.during_dead_ball |  | partial | existing: new-IV-26 |
| A.11.04 | Disqualified-player replacement (20 s) — Replacement within 20 s of notification. | 4-12.5, 10-2 |  | substitutions.reason_inferred |  | partial | existing: new-IV-11 |
| A.11.05 | Substitution reason |  | R-CC-03 R-PE-06 | substitutions.reason_inferred |  | covered |  |
| A.11.06 | PBP substitution timing errors |  | R-DQ-09 R-SY-03 | substitutions.timing_error_flag, substitutions.source_timing |  | covered |  |
| A.12.01 | Crew size and roles (referee, umpires, crew chief) | 2-1 | R-FD-08 R-IV-02 | game_officials.is_crew_chief, game_officials.listed_order |  | covered |  |
| A.12.02 | Court position: lead, trail, centre | App. III; three-person mechanics | R-DT-12 R-SR-07 | official_positions.role, official_positions.x_fc_m |  | covered |  |
| A.12.03 | Rotations of the crew — Lead rotations to the strong side and position switches after foul reports. | Points of Emphasis 1 (three-person system) |  | official_positions.role |  | missing | new-RF-8 |
| A.12.04 | Calling official, primary coverage area and whistle distance — Who blew the whistle, whether the play was in his primary area, his distance to the play. | Points of Emphasis 2 (whistle discipline), 8 (team officiating) | R-RF-05 | fouls.calling_official_id, fouls.calling_official_role |  | partial | new-RF-9 |
| A.12.05 | Signals (Appendix VIII full list) — Clock, timeout, violation, foul-type, information and scoring signals (about 50). *(note: signal_pose has 10 values; App. VIII lists about 50 signals.)* | App. VIII | R-RF-04 | official_positions.signal_pose | App.VIII | partial | new-RF-10 |
| A.12.06 | Whistles |  | R-RF-01 R-RF-02 | whistles.video_ts_ms, whistles.linked_event_id |  | covered |  |
| A.12.07 | Visible counts (5 s, 10 s, throw-in) — Officials' visible counts. | App. VIII (visible count) | R-DT-14 | restarts.throw_in_count_s |  | partial | new-RF-11 |
| A.13.01 | Voluntary and mandatory reviews | 11-2, 11-3 | R-RF-07 R-SR-04 | reviews.review_kind, reviews.subject, reviews.outcome |  | covered |  |
| A.13.02 | Coach's challenge *(note: Detail in new-IV-14.)* | 11-4 (2025-26), 2-9.19 (2026-27) | R-EV-16 R-SR-04 | coaches_challenges.play_type, coaches_challenges.outcome, coaches_challenges.timeout_charged |  | covered |  |
| A.13.03 | Appeals | 11-5 (2026-27), A.R. 11-32 | R-SR-04 | reviews.review_kind, timeouts.timeout_type |  | covered |  |
| A.13.04 | Review duration and game effect |  | R-SR-04 R-TR-19 | reviews.video_ts_ms_start, reviews.video_ts_ms_end, reviews.score_delta_msu, reviews.possession_after |  | covered |  |
| A.13.05 | First-half flagrant reviewed after half time | A.R. 11-32, 11-2.1.d.2 | R-IV-09 | reviews.subject, foul_state.bucket_id |  | covered |  |

### B. Court, equipment and venue

The physical game: court geometry and markings, basket and ball, clocks and displays, uniforms, cameras and the arena.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| B.01.01 | Court dimensions (28.65 m x 15.24 m) | 1-2 | R-CG-01 | config/court_ncaa_men.yaml |  | covered |  |
| B.01.02 | Boundary lines and the out-of-bounds plane — Boundary lines (5.08 cm wide) are out of bounds; their width decides close out-of-bounds calls. | 1-3, 4-6 | R-CG-01 R-BL-07 | config/court_ncaa_men.yaml |  | partial | new-CG-1 |
| B.01.03 | Centre circle — 1.83 m radius circle for jump balls; non-jumpers stay outside. | 1-4, 6-2 | R-DT-15 | jump_balls.circle_formation |  | partial | (see B.01.02 proposal) |
| B.01.04 | Division line and half-court distance | 1-5 | R-CG-01 | config/court_ncaa_men.yaml, player_positions.court_half |  | covered |  |
| B.01.05 | Free-throw lane, line and lane spaces — Lane 3.66 m wide; FT line 4.19 m from rim centre; lane-space marks for FT positions. *(note: Lane width and FT line in config; lane-space marks missing (see B.01.02).)* | 1-6, 8-4 | R-CG-01 R-DT-13 | config/court_ncaa_men.yaml, free_throws.lane_occupant_ids |  | partial | (see B.01.02 proposal) |
| B.01.06 | Three-point line (6.75 m, 6.60 m corners) | 1-7 | R-CG-01 R-IV-12 | config/court_ncaa_men.yaml |  | covered |  |
| B.01.07 | Restricted-area arc (1.22 m) | 1-8, 4-31 | R-CG-01 | config/court_ncaa_men.yaml |  | covered |  |
| B.01.08 | Coaching box — Area where the head coach may stand. | 1-9 |  |  |  | missing | new-CC-2 |
| B.01.09 | 28-ft throw-in marks and designated spots — Sideline marks 8.53 m from the end line; end-line spots 0.91 m outside the lane. *(note: Live doc says 'Add to config'; not in config yet.)* | 7-3.2.b (2025-26), 7-6.8 | R-DT-19 R-SR-08 | restarts.throw_in_spot |  | partial | (see B.01.02 proposal) |
| B.01.10 | Backboard and basket geometry — Backboard face 1.22 m inside the end line, 1.83 x 1.07 m; ring 3.05 m high, 0.4572 m inner diameter, centre 1.60 m from the end line. *(note: Rim height and centre in config; backboard and ring diameter missing.)* | 1-10, 1-13, 1-14, 1-15 | R-CG-01 R-CG-11 R-MB-01 | config/court_ncaa_men.yaml |  | partial | (see B.01.02 proposal) |
| B.01.11 | Coordinate frame and mirroring |  | R-CG-02 R-CG-08 | player_positions.x_m, player_positions.theta_deg |  | covered |  |
| B.01.12 | Named spots and landmarks |  | R-CG-05 R-MD-10 | player_positions.spot, player_positions.landmark | config/vocabulary_map.yaml | covered |  |
| B.01.13 | Undefined spots (short corner, one pass away) — Terms still 'to be defined from film'. |  | R-MD-10 | config/vocabulary_map.yaml |  | partial | new-MD-1 |
| B.01.14 | Sectors, rings, rays and grid |  | R-CG-05 | player_positions.sector_15deg, player_positions.ring_0p5m |  | covered |  |
| B.01.15 | Post zones (low, high) and cut-off checks |  | R-CG-05 R-CG-09 | player_positions.post_zone |  | covered |  |
| B.01.16 | Court constants verification status — config/court_ncaa_men.yaml says verified: false. |  | R-CG-01 | config/court_ncaa_men.yaml |  | partial | (Aldemir sign-off) |
| B.02.01 | Ball specification | 1-16 | R-BL-01 | ball_states.size_check_pass, config/court_ncaa_men.yaml |  | covered |  |
| B.02.02 | Game ball model per game — Ball manufacturer/model in use (affects bounce and shooting feel). | 1-16 |  |  |  | missing | new-FD-4 |
| B.02.03 | Scoreboard and game-clock display | 1-18 | R-SY-01 R-SR-01 | scoreboard_ocr.display, scoreboard_ocr.game_clock_raw |  | covered |  |
| B.02.04 | Shot-clock displays | 1-19 | R-SY-01 R-IV-07 | scoreboard_ocr.shot_clock_raw, scoreboard_ocr.display |  | covered |  |
| B.02.05 | Possession indicator | 1-20 | R-SY-01 R-MD-12 | scoreboard_ocr.arrow_raw |  | covered |  |
| B.02.06 | Red light / LED and horn | 1-18, 5-7 | R-MB-06 | made_basket_events.release_vs_horn, audio_seconds.buzzer_present |  | covered |  |
| B.02.07 | Team benches and scorers' table side — Which side each bench and the table are on; needed for the second-half arrow and bench filtering. | 1-21, 6-3 |  |  |  | missing | new-FD-5 |
| B.02.08 | Uniform colours and numbers | 1-22 | R-CX-07 R-FD-03 R-DT-18 | games.home_jersey_colour, games.away_jersey_colour, jersey_history.jersey_number |  | covered |  |
| B.02.09 | Supplemental apparel, headbands, sleeves | 1-23, 1-24 | R-ID-12 | appearance_cards.sleeves, appearance_cards.headband |  | covered |  |
| B.02.10 | Player equipment (goggles, masks, braces) — Protective equipment visible on video. | 1-26 | R-ID-12 | appearance_cards.tape |  | partial | new-ID-1 |
| B.02.11 | Court logos and floor graphics | 1-17.6 (2026-27) | R-CG-10 | venues.floor_template_id |  | covered |  |
| B.02.12 | Rim type and stiffness — Rim make and stiffness by arena (context list mentions 'rim type'). | 1-15 |  |  |  | missing | new-CX-1 |
| B.03.01 | Main-camera side and height per arena |  | R-VI-13 R-FD-11 | venues.main_camera_side, venues.main_camera_height_m, venues.zoom_range_seen |  | covered |  |
| B.03.02 | Camera pan, tilt, zoom and focal length |  | R-DT-09 | frames.camera_pan_deg, frames.camera_tilt_deg, frames.focal_px |  | covered |  |
| B.03.03 | Homography and lens distortion |  | R-CG-03 R-VA-02 | frames.homography, frames.distortion_k, frames.mapping_conf |  | covered |  |
| B.03.04 | Other fixed camera positions — Baseline, under-basket, reverse angle, rail, robotic, skycam positions. |  | R-SR-10 | state_frame.reverse_angle |  | partial | new-VI-1 |
| B.03.05 | Floor template and glare zones |  | R-CG-10 | venues.floor_template_id |  | covered |  |
| B.04.01 | Venue identity, coordinates, elevation, time zone |  | R-FD-11 R-CX-16 | venues.lat_deg, venues.lon_deg, venues.elevation_m, venues.tz |  | covered |  |
| B.04.02 | Capacity and attendance |  | R-CX-04 | venues.capacity, games.attendance |  | covered |  |
| B.04.03 | Floor colour, backdrop behind each basket, lighting |  | R-CX-12 | venues.floor_colour, venues.backdrop_behind_baskets, venues.lighting_level |  | covered |  |
| B.04.04 | Student-section location — Which basket end has the student section (free throws by end). |  |  |  |  | missing | new-CX-2 |
| B.04.05 | Court placement (dome midfield / corner, standard arena) — Tournament dome courts change the shooting background. |  |  |  |  | missing | new-CX-3 |
| B.04.06 | Neutral site |  | R-MD-14 R-CX-04 R-CX-14 | games.neutral_site, team_game_context.proximity_home_flag |  | covered |  |
| B.04.07 | Arena music and noise rules | 10-2.8.a (2025-26) | R-AU-04 | audio_seconds.music_flag |  | covered |  |

### C. Participants

Everyone on or around the floor: players, coaches and bench, officials, table crew, crowd and arena staff.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C.01.01 | Player identity and IDs |  | R-PC-01 R-DS-05 | players.player_id, players.broadcast_name, id_crosswalk.source_key |  | covered |  |
| C.01.02 | Roster per season |  | R-FD-03 | rosters.player_id, rosters.season |  | covered |  |
| C.01.03 | Jersey number history |  | R-FD-03 R-ID-04 | jersey_history.jersey_number, jersey_history.valid_from |  | covered |  |
| C.01.04 | Listed position and played position |  | R-PC-01 | rosters.listed_position, player_card.listed_vs_played_position |  | covered |  |
| C.01.05 | Body (height, weight, wingspan, reach, hands) |  | R-PC-04 R-FD-04 R-DQ-09 | rosters.listed_height_cm, player_card.wingspan_cm, player_card.standing_reach_cm |  | covered |  |
| C.01.06 | Age, class, eligibility |  | R-PC-01 | players.birth_date, player_game_context.age_at_tip_years, rosters.class_year |  | covered |  |
| C.01.07 | Origin (hometown, schools, AAU) |  | R-PC-02 R-PC-03 | player_card.hometown_lat, player_card.aau_program, player_game_context.dist_hometown_to_venue_km |  | covered |  |
| C.01.08 | Laterality (shooting, dribble, finishing hand, drive side) |  | R-PC-11 | players.shooting_hand, player_card.dominant_dribble_hand, player_card.finishing_hand_left_share |  | covered |  |
| C.01.09 | Athletic profile from tracking |  | R-PC-05 | player_card.trk_top_speed_ms_max, player_card.trk_lateral_slide_ms, player_card.trk_cod_time_s |  | covered |  |
| C.01.10 | Combine and athletic test results |  | R-FD-04 R-PC-04 | player_card.max_vertical_cm, player_card.lane_agility_s |  | covered |  |
| C.01.11 | Recruiting and rankings |  | R-PC-13 R-FD-12 | player_card.recruit_rank_nat_247c, ratings_snapshots.rank |  | covered |  |
| C.01.12 | Transfer history |  | R-FD-12 R-PC-02 | rosters.transfer_origin_team_id, player_card.transfer_events |  | covered |  |
| C.01.13 | International and pro background |  | R-PC-16 | player_card.fiba_youth_events, player_card.pro_leagues |  | covered |  |
| C.01.14 | NIL valuation (public estimates) — On the player card template; no requirement names it. |  |  | player_card.nil_valuation_usd |  | partial | new-PC-6 |
| C.01.15 | Role and usage cluster |  | R-PC-10 | player_card.role_cluster_own, player_card.usage_pct |  | covered |  |
| C.01.16 | Development and career minutes |  | R-PC-12 | player_card.career_d1_minutes, profile_snapshots.metric_code |  | covered |  |
| C.01.17 | Captain — Designated captain(s). | 3-3 |  | player_card.captain_flag |  | partial | new-PC-7 |
| C.01.18 | Availability and public injury status |  | R-FD-05 R-CX-08 R-RG-06 | availability.status, availability.reason_public |  | covered |  |
| C.01.19 | Excluded attributes (race, faces, private health) |  | R-PC-15 R-ID-10 |  |  | covered |  |
| C.01.20 | Per-game appearance |  | R-ID-12 | appearance_cards.shoes |  | covered |  |
| C.01.21 | Shooting block (sector x ring, shrunk) |  | R-PC-06 | player_shooting_sector_ring.rate_shrunk, player_shooting_sector_ring.prior_code |  | covered |  |
| C.01.22 | Playmaking and ball security block |  | R-PC-07 | profile_snapshots.metric_code, player_card.ast_pct, player_card.tov_pct |  | covered |  |
| C.01.23 | Prior-level physicality |  | R-PC-09 | profile_snapshots.metric_code |  | covered |  |
| C.02.01 | Head coach card |  | R-CC-01 | coaches.coach_id, coaches.career_wins_asof, coaches.system_offense_codes |  | covered |  |
| C.02.02 | Assistant coaches and staff roles |  | R-CC-01 | coaches.role |  | covered |  |
| C.02.03 | Bench personnel list per game — Team members, managers, trainers, ops staff on the bench (bench-personnel rule). | 4-3, 4-4 | R-DT-02 | bench_events.actor_type |  | partial | new-CC-3 |
| C.02.04 | Athletic trainers and medical staff on the floor |  | R-DT-17 R-EV-11 | detections.person_class |  | covered |  |
| C.02.05 | Sideline behaviour |  | R-CC-04 R-CC-03 | bench_events.event_type |  | covered |  |
| C.03.01 | Official identity and crew per game |  | R-FD-08 R-DQ-01 | officials.official_id, game_officials.official_id |  | covered |  |
| C.03.02 | Official tendencies as of date |  | R-RF-06 R-CX-06 | profile_snapshots.metric_code |  | covered |  |
| C.03.03 | Official experience and assignment level — Seasons, games worked, conferences, postseason assignments. |  | R-RF-06 | officials.first_season_seen |  | partial | new-RF-12 |
| C.04.01 | Official scorer and the scorebook authority — Scorebook wins unresolved discrepancies. | 2-9, 2-9.13 | R-DQ-09 | scoreboard_flags.review_answer |  | partial | existing: new-IV-33 |
| C.04.02 | Timer and game-clock operation errors | 2-10, 5-12 | R-SB-01 | scoreboard_flags.flag_type |  | covered |  |
| C.04.03 | Shot-clock operator errors | 2-11 | R-SB-01 R-SY-09 | scoreboard_flags.flag_type, shot_clock_resets.rule_match |  | covered |  |
| C.04.04 | Home stat crew bias — Home scorekeepers credit more assists, blocks and steals. |  | R-DQ-09 |  |  | partial | new-DQ-1 |
| C.05.01 | Crowd size and share of capacity |  | R-CX-04 | games.attendance |  | covered |  |
| C.05.02 | Crowd loudness |  | R-AU-03 | audio_seconds.loudness_rel_db |  | covered |  |
| C.05.03 | Crowd allegiance share (neutral sites) — Share of fans supporting each team. |  | R-CX-17 R-CX-14 | team_game_context.proximity_home_flag |  | partial | new-CX-4 |
| C.05.04 | Band, cheer, mascots and staff on the floor |  | R-DT-17 R-DT-02 | detections.person_class |  | covered |  |

### D. Game state

What is true at any instant: score, clocks, possession, ball, fouls, timeouts, lineups, situation, momentum, beliefs and data quality.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| D.01.01 | Score and margin every frame |  | R-SR-02 R-MD-01 | state_frame.score_msu, state_frame.score_opp, state_frame.margin |  | covered |  |
| D.01.02 | Score-change events |  | R-SR-02 R-IV-04 | score_events.delta_points, score_events.event_kind |  | covered |  |
| D.01.03 | Lead changes and ties |  | R-MD-17 | state_second.lead_changes |  | partial | new-MD-2 |
| D.01.04 | Runs (points in last 2, 4, 6 min) |  | R-MD-17 R-EV-13 | state_second.run_msu_2min, state_second.run_opp_2min |  | covered |  |
| D.01.05 | Run events (start, end, size) — A run = net >= 8 points for one team within 120 s (beliefs register definition). |  | R-CH-08 |  |  | partial | new-EV-5 |
| D.01.06 | Scoring droughts — Time since each team's last field goal and last point. |  |  |  |  | missing | new-MD-3 |
| D.02.01 | Period, game clock, shot clock, clock running |  | R-SR-01 | state_frame.period, state_frame.game_clock_s, state_frame.shot_clock_s, state_frame.clock_running |  | covered |  |
| D.02.02 | Phase stamps (5-min window, media segment, last 4 min, clutch) |  | R-MD-13 | state_second.five_min_window_id, state_second.media_segment_id, state_second.clutch_flag, state_second.last4_flag |  | covered |  |
| D.02.03 | Time-and-score windows (two-for-one, foul to extend, last shot) |  | R-SR-11 | state_second.two_for_one_window, state_second.foul_to_extend_window, state_second.last_shot_window |  | covered |  |
| D.02.04 | Garbage time — Possessions whose outcome cannot change the result; sources define it differently. |  |  | possessions.is_garbage_time_source |  | partial | new-MD-4 |
| D.03.01 | Team in possession, possession and chance IDs |  | R-SR-05 R-MD-04 | state_frame.team_in_possession, state_frame.possession_id, state_frame.chance_id, state_frame.chance_number |  | covered |  |
| D.03.02 | Phase (half court, transition, throw-in, FT, jump, timeout, review) |  | R-SR-05 R-GU-01 | state_second.phase, belief_states.phase |  | covered |  |
| D.03.03 | Seconds since change of control |  | R-SR-05 R-TR-01 | state_second.secs_since_control_change |  | covered |  |
| D.03.04 | Possession start type |  | R-SY-04 R-PE-01 | possessions.start_type_code | TR.ST | covered |  |
| D.03.05 | Live-time split by control state |  | R-MD-05 | state_second.share_msu_ball, state_second.share_contested |  | covered |  |
| D.04.01 | Ball-control state (6 states) |  | R-MD-02 R-SR-06 | state_frame.ball_control_state | global_metadata.ball_control_state | covered |  |
| D.04.02 | Ball handler |  | R-BL-02 R-SR-06 | state_frame.ball_handler_player_id, ball_states.holder_id |  | covered |  |
| D.04.03 | Ball position x, y, height |  | R-BL-01 R-SR-06 R-CG-11 | state_frame.ball_x_m, state_frame.ball_z_m, ball_states.ball_height_m |  | covered |  |
| D.04.04 | Ball action state (held, dribbled, passed, shot, loose, OOB, dead) |  | R-BL-03 | ball_states.ball_state |  | covered |  |
| D.04.05 | Try in flight and ring contact |  | R-SR-06 R-MB-07 | state_frame.try_in_flight, state_frame.ring_contact_this_try |  | covered |  |
| D.04.06 | Ball visibility and inference |  | R-SR-06 R-MD-19 | state_frame.ball_visible, state_frame.ball_inferred |  | covered |  |
| D.05.01 | Team fouls and bonus state |  | R-MD-07 R-SR-03 | state_frame.team_fouls_msu, state_frame.msu_bonus_state |  | covered |  |
| D.05.02 | Personal fouls per player |  | R-SR-03 R-MD-16 | foul_state.personal_fouls_player_cum |  | covered |  |
| D.05.03 | Fouls to give |  | R-SR-03 | state_second.fouls_to_give_msu |  | covered |  |
| D.05.04 | Foul trouble flags |  | R-MD-16 R-SR-11 | state_second.foul_trouble_msu, foul_state.foul_trouble |  | covered |  |
| D.05.05 | Technical and flagrant counts toward disqualification |  | R-SR-03 | foul_state.technical_class_a, foul_state.flagrant1_player_cum |  | covered |  |
| D.06.01 | Timeouts left by type |  | R-SR-04 R-MD-07 | state_frame.to30_left_msu, state_frame.timeouts_msu |  | covered |  |
| D.06.02 | Coach's challenge available |  | R-SR-04 | state_frame.challenge_available_msu |  | covered |  |
| D.06.03 | Media-timeout slot state |  | R-SR-04 R-MD-13 | timeouts.media_slot, state_second.media_segment_id |  | covered |  |
| D.06.04 | Stoppage kind and review in progress |  | R-SR-04 | state_frame.stoppage_kind |  | covered |  |
| D.07.01 | Players on floor and lineup keys |  | R-SY-03 R-MD-15 R-IV-01 | state_frame.players_on_floor, lineup_stints.lineup_key, lineup_stints.opponent_lineup_key |  | covered |  |
| D.07.02 | Minutes together this season |  | R-MD-15 | lineup_stints.season_seconds_together_before |  | covered |  |
| D.07.03 | Stint length and continuous minutes |  | R-SR-07 R-PL-03 | lineup_stints.duration_s, accel_efforts.continuous_minutes_at_start |  | covered |  |
| D.07.04 | Lineup composition (size, positions, shooting) — Number of bigs, mean and max height, number of 3-point shooters, ball handlers on the floor. |  |  |  |  | missing | new-MD-5 |
| D.07.05 | Matchups and mismatches on the floor |  | R-DF-01 R-DF-09 | defensive_matchups.attacker_id, defensive_matchups.mismatch_height_cm |  | covered |  |
| D.08.01 | Dead-ball reason and restart type and spot |  | R-SR-08 | restarts.dead_ball_reason, restarts.restart_type, restarts.throw_in_spot |  | covered |  |
| D.08.02 | Free-throw state |  | R-SR-09 | state_second.ft_state, state_second.ft_attempt_k |  | covered |  |
| D.09.01 | Pre-possession win probability |  | R-MD-17 R-PR-11 | possessions.pre_win_prob, events.home_win_prob_source |  | covered |  |
| D.09.02 | Expected points of current possession |  | R-SR-12 R-VL-01 | state_second.xpts_possession, possession_value.value_xpts |  | covered |  |
| D.09.03 | Belief state (system as viewer) |  | R-GU-01 R-GU-02 | belief_states.top3_sets, belief_states.next_action_probs, events.surprise_nats |  | covered |  |
| D.09.04 | Previous possession result |  | R-EV-13 | possessions.previous_possession_result |  | covered |  |
| D.09.05 | Defensive scheme state |  | R-DF-04 R-MD-01 | state_frame.defense_scheme_state, scheme_states.l1_base_scheme_code | DEF.F18.1 | covered |  |
| D.09.06 | Offensive set in progress |  | R-ST-05 R-ST-07 R-GU-01 | set_instances.set_code, belief_states.top3_sets | OFF.F1-F18 MS | covered |  |
| D.09.07 | Coach quiz and belief consistency |  | R-GU-03 R-GU-06 | coach_quiz.correct, belief_states.rule_violations |  | covered |  |
| D.10.01 | Relative geometry and spacing |  | R-CG-07 | frame_geometry.spacing_mean_m, frame_geometry.hull_area_m2, frame_geometry.driving_cone_deg |  | covered |  |
| D.10.02 | Players visible, missing and imputed |  | R-DT-05 R-DT-07 | player_positions.observed, player_positions.region95_semi_axes_m |  | covered |  |
| D.10.03 | Data-quality flag and source per value |  | R-MD-19 R-SR-15 R-MD-09 | state_frame.score_src, state_frame.ball_conf, state_frame.invariant_breaks |  | covered |  |
| D.10.04 | Blind vs anchored pass |  | R-SR-13 | state_frame.game_clock_src |  | covered |  |

### E. Individual actions

What one player does: moving, handling, passing, shooting, rebounding, screening, cutting, posting, defending, fouling, free throws, communication.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E.01.01 | Stand, walk, jog, run, sprint |  | R-ST-01 R-PL-11 | movement_primitives.primitive_type, load_stint_bins.speed_bin_lo_mps |  | covered |  |
| E.01.02 | Defensive slide, backpedal and crossover run — Lateral and backward movement patterns (lateral slide speed is on the card). |  | R-PC-05 | player_card.trk_lateral_slide_ms |  | partial | new-ST-2 |
| E.01.03 | Jumps (takeoff, height, purpose) — Jumps for shots, rebounds, blocks, contests; one- or two-foot takeoff. |  | R-CG-11 R-DT-10 | player_positions.airborne, player_positions.jump_height_m |  | partial | new-PL-1 |
| E.01.04 | Stops, pivots, first step and plant foot — Jump stop, stride stop, pivot foot, first-step direction. | 4-22, 4-27, 9-5 | R-DT-16 |  |  | partial | new-DT-1 |
| E.01.05 | Gather and pre-dribble / split-step travel cues — Gather step and foot sequence before the first dribble (2026-27 point of emphasis). | 9-5, Points of Emphasis 5 |  |  |  | missing | new-DT-2 |
| E.01.06 | Change of direction — Direction changes > 45 degrees at speed, with time to re-accelerate. |  | R-PC-05 | player_card.trk_cod_time_s |  | partial | new-PL-2 |
| E.01.07 | Falls and players on the floor |  | R-DT-01 R-DT-10 | player_positions.stance |  | covered |  |
| E.01.08 | Landing space of jump shooters — Defender entering the shooter's landing space (2026-27 point of emphasis). | Points of Emphasis 7; App. VIII 'landing space' |  |  |  | missing | new-DF-1 |
| E.02.01 | Touches, touch time and hand |  | R-EV-04 | touches.touch_time_s, touches.hand, touches.dribbles |  | covered |  |
| E.02.02 | Dribble count and dribble hand |  | R-BL-06 R-EV-04 | dribbles.hand, touches.dribbles |  | covered |  |
| E.02.03 | Dribble moves (crossover, between legs, behind back, hesitation, spin, retreat) |  | R-EV-05 | dribbles.move_type |  | covered |  |
| E.02.04 | Other dribble moves (in-and-out, push/speed, pound, snatch-back, half spin) |  | R-EV-05 | dribbles.move_type |  | partial | new-EV-6 |
| E.02.05 | Drives |  | R-EV-06 | drives.depth_gain_m, drives.direction, drives.result |  | covered |  |
| E.02.06 | Fakes (shot fake, pass fake, jab step) — Deceptive moves and whether the defender bit. |  |  |  |  | missing | new-EV-7 |
| E.02.07 | Time of possession per player |  | R-PC-10 | touches.touch_time_s |  | covered |  |
| E.02.08 | Ball pressure on the handler |  | R-CO-01 | touches.pressure_m |  | covered |  |
| E.03.01 | Pass types (11 + unseen) |  | R-EV-02 | passes.pass_type |  | covered |  |
| E.03.02 | Pass metrics (speed, distance, angle, lane openness) |  | R-EV-02 R-CG-07 | passes.speed_mps, passes.distance_m, passes.angle_change_deg, passes.lane_openness_m |  | covered |  |
| E.03.03 | Pass outcome (completed, deflected, intercepted, thrown away) |  | R-EV-02 | passes.outcome |  | covered |  |
| E.03.04 | Pass chain (assist, hockey assist, potential assist, screen assist) |  | R-EV-03 | passes.chain_role, passes.is_official_assist, screens.is_screen_assist |  | covered |  |
| E.03.05 | Receiver's first action |  | R-EV-02 | passes.receiver_first_action |  | covered |  |
| E.03.06 | Pass delivery (one/two hands, off the dribble, no-look) |  |  |  |  | missing | new-EV-8 |
| E.03.07 | Throw-in passes — First pass of a throw-in. |  | R-DT-14 | restarts.thrower_player_id |  | partial | new-EV-9 |
| E.03.08 | Lobs and alley-oops |  | R-ST-26 | passes.pass_type, shots.shot_type_code |  | covered |  |
| E.04.01 | Shot type |  | R-EV-07 | shots.shot_type_code |  | covered |  |
| E.04.02 | Layup and finish subtypes — Reverse, Euro step, finger roll, scoop, up-and-under, power, off one or two feet. |  | R-EV-07 | shots.layup_hand |  | partial | new-EV-10 |
| E.04.03 | Shot location (release x, y, r, theta, zones) |  | R-EV-07 R-CG-05 R-SY-07 | shots.release_r_m, shots.release_theta_deg, shots.release_sector_15deg, shots.ncaa_shot_zone |  | covered |  |
| E.04.04 | Contest (closest defender, closing speed) |  | R-EV-07 R-VL-04 | shots.contest_distance_m, shots.closing_speed_mps, shots.closest_defender_id |  | covered |  |
| E.04.05 | Contest form (hand up, high/low hand, contest height) — Whether and how the defender's hand contests the release. |  | R-PL-07 |  |  | partial | new-EV-11 |
| E.04.06 | Release attributes (height, time, arc, entry angle) |  | R-PL-07 R-CG-11 | shots.release_height_m, shots.release_time_s, shots.arc_deg, shots.entry_angle_deg |  | covered |  |
| E.04.07 | Shot context (dribbles before, touch time, shot clock, off a screen) |  | R-EV-07 | shots.dribbles_before, shots.touch_time_before_s, shots.shot_clock_s |  | covered |  |
| E.04.08 | Rim outcome, bank shot, block, and-one |  | R-BL-08 R-EV-07 R-MB-07 | shots.rim_outcome, shots.bank, shots.blocked, shots.and_one |  | covered |  |
| E.04.09 | Assisted vs self-created |  | R-EV-03 R-EV-07 | shots.assisted_official, shots.assister_video_id |  | covered |  |
| E.04.10 | Shot quality |  | R-VL-04 | shots.shot_quality_xpts |  | covered |  |
| E.04.11 | End-of-period heaves |  | R-MB-06 | shots.is_heave |  | covered |  |
| E.04.12 | Shooter's footwork into the shot — 1-2 step, hop, turnaround, fade, spin-off. |  |  | shots.shot_type_code |  | partial | new-EV-12 |
| E.05.01 | Offensive and defensive rebounds, team rebounds |  | R-EV-08 | rebounds.off_def, rebounds.is_team_rebound |  | covered |  |
| E.05.02 | Contested, long/short, tip-outs |  | R-EV-08 | rebounds.contested, rebounds.long_short, rebounds.tip_out |  | covered |  |
| E.05.03 | Box-outs |  | R-EV-08 R-DT-16 | box_outs.boxer_id, box_outs.result |  | covered |  |
| E.05.04 | Crashers and leakers |  | R-EV-08 | rebounds.crashers_off, rebounds.crashers_def, rebounds.leaker_ids |  | covered |  |
| E.05.05 | Rebound positioning at the release — Each player's position and inside position (goal side of an opponent) when the shot is released. |  |  | configuration_snapshots.trigger |  | partial | new-EV-13 |
| E.06.01 | Setting a screen |  | R-ST-02 R-ST-17 | screens.screener_id, screens.strict_rule_fired, screens.loose_rule_fired |  | covered |  |
| E.06.02 | Screen geometry (angle, contact distance, duration) |  | R-CG-07 R-ST-02 | screens.screen_angle_deg, screens.contact_distance_m, screens.duration_s |  | covered |  |
| E.06.03 | Screener's action after (roll, pop, slip, short roll, ghost) |  | R-ST-18 | screens.screener_action_after | OFF.F5.4 | covered |  |
| E.06.04 | Illegal (moving) screens — Offensive fouls for illegal screens. | 4-35, App. III (screening) |  | fouls.foul_subtype |  | partial | (see A.06.17 contact-type proposal) |
| E.07.01 | Cut types (basket, backdoor, flare, curl, straight, shallow) |  | R-ST-01 | movement_primitives.primitive_type |  | covered |  |
| E.07.02 | Named cuts (UCLA, Iverson, zipper, flash, V-cut, L-cut, shuffle, rip, Euro) — The cut vocabulary of OFF.F8.2 not in the primitive list. |  | R-ST-01 R-ST-04 | movement_primitives.primitive_type | OFF.F8.2 | partial | new-ST-3 |
| E.07.03 | Relocate, lift, drift, rim run, corner sprint |  | R-ST-01 | movement_primitives.primitive_type |  | covered |  |
| E.07.04 | Off-ball gravity |  | R-VL-06 | value_credits.defender_displacement_m |  | covered |  |
| E.08.01 | Post touches and entries |  | R-DF-07 | post_touches.post_zone, post_touches.entry_pass_id |  | covered |  |
| E.08.02 | Seal and post positioning |  | R-ST-01 | post_touches.seal |  | covered |  |
| E.08.03 | Post moves (drop step, hook, up-and-under, face-up, spin) |  | R-ST-04 | post_touches.post_move_code | OFF.F7 | covered |  |
| E.08.04 | Post dislodging and hook-and-hold — Illegal post contact (2026-27 point of emphasis 4). | Points of Emphasis 4; App. VIII |  |  |  | partial | (see A.06.17 contact-type proposal) |
| E.09.01 | Defensive stance and distance to the handler |  | R-DT-10 R-CO-01 | player_positions.stance, touches.pressure_m |  | covered |  |
| E.09.02 | Containment and blow-bys |  | R-EV-06 | drives.defender_reaction |  | covered |  |
| E.09.03 | Closeouts (distance, speed, type) |  | R-DF-08 R-ST-01 | reaction_events.closeout_distance_m, reaction_events.closeout_speed_mps |  | covered |  |
| E.09.04 | Contests |  | R-EV-09 | defensive_events.type |  | covered |  |
| E.09.05 | Steals, deflections, blocks, charges drawn, loose balls |  | R-EV-09 | defensive_events.type, defensive_events.recovered_by_team_id |  | covered |  |
| E.09.06 | Off-ball denial posture — Denying a passing lane (hand and foot in the lane). |  | R-DF-02 | defensive_matchups.in_gap |  | partial | new-DF-2 |
| E.09.07 | Reaction time and anticipation |  | R-CO-02 R-CO-03 | reaction_events.latency_s |  | covered |  |
| E.09.08 | Verticality and hands up | 4-39 | R-DT-10 | player_positions.hands_up |  | covered |  |
| E.10.01 | Routine time and dribbles |  | R-PL-08 R-SR-09 | free_throws.release_latency_s, player_card.trk_ft_routine_s, player_card.trk_ft_dribbles |  | covered |  |
| E.10.02 | Arc consistency |  | R-PL-08 | player_card.trk_ft_arc_deg_sd |  | covered |  |
| E.11.01 | Defensive communication proxies |  | R-CO-08 | screens.coverage_fine_code |  | covered |  |
| E.11.02 | Play-call signals by players |  | R-AU-02 R-EV-15 | play_calls.call_source, play_calls.call_text |  | covered |  |
| E.11.03 | Player gestures toward officials and opponents (taunting, celebration) — Unsporting acts that risk Class A technicals. | 10-3 |  |  |  | missing | new-CC-4 |

### F. Group tactics: offence

Team offensive structures from docs/taxonomy/offense_full.md (OFF.F1-F18), motion_starts.md (MS.*) and transition_full.md (TR.*).

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| F.01.01 | Transition start, end and class (state rule) |  | R-TR-08 R-TR-09 R-TR-05 R-TR-10 R-TR-02 | transition_phases.transition_class, possessions.transition_class, transition_phases.seconds_to_defense_set | TR.ST | covered |  |
| F.01.02 | Every analyst transition definition side by side |  | R-TR-11 R-TR-18 R-TR-27 R-TR-17 R-TR-28 | transition_phases.tr_synergy_like, transition_phases.tr_hoopmath_10s, transition_phases.tr_fastscout_10s |  | covered |  |
| F.01.03 | Outlet and advance |  | R-TR-13 R-TR-20 | transition_phases.phase_times | OFF.F1.1 TR.PH | covered |  |
| F.01.04 | Lane filling and roles (handler, rim runner, wings, trailer, leak-out) |  | R-TR-04 R-TR-15 | transition_roles.lane, transition_roles.role_synergy | OFF.F1.2 OFF.F1.3 TR.RO | covered |  |
| F.01.05 | Numbers advantage (2v1, 3v2, 4v3) |  | R-TR-03 R-TR-22 | transition_numbers.numbers_label, transition_numbers.advantage | OFF.F1.5 | covered |  |
| F.01.06 | Push after makes and free throws |  | R-TR-14 R-TR-21 R-TR-23 | transition_phases.pushed, transition_phases.t_inbound_release_ms |  | covered |  |
| F.01.07 | Passed-up breaks and pull-backs |  | R-TR-16 R-TR-24 R-TR-26 R-TR-06 | transition_phases.passed_up_reason, transition_phases.value_at_stake_xpts |  | covered |  |
| F.01.08 | Named breaks (incl. MSU/Izzo) |  | R-ST-04 R-ST-05 | set_instances.family_code | OFF.F1.4 | covered |  |
| F.02.01 | Drag and double drag ('77') |  | R-ST-18 | actions.action_code | OFF.F2.1 | covered |  |
| F.02.02 | Pistol / 21 |  | R-ST-04 R-ST-05 | set_instances.set_code | OFF.F2.2 | covered |  |
| F.02.03 | Trailer actions and early post |  | R-TR-13 R-ST-04 | transition_phases.phase_times, set_instances.set_code | OFF.F2.3 OFF.F2.4 | covered |  |
| F.02.04 | Flow into the half court |  | R-TR-13 R-TR-20 | transition_phases.phase_times | OFF.F2.5 | covered |  |
| F.03.01 | Alignment snapshot and family match |  | R-ST-19 R-ST-21 | configuration_snapshots.alignment_code, set_instances.alignment_code | MS OFF.F3.1 | covered |  |
| F.03.02 | Named starts (Horns, 1-4, box, stack, 5-out, ...) |  | R-ST-04 R-ST-05 R-ST-21 | set_instances.set_code | MS OFF.F3.2 OFF.F3.3 OFF.F3.4 | covered |  |
| F.04.01 | System label per possession and per game — Whether a team is running a continuity (flex, shuffle, swing, Princeton, triangle, blocker-mover) and how many cycles. |  | R-ST-04 R-ST-25 | set_instances.family_code | OFF.F4.1 OFF.F4.2 | partial | new-ST-4 |
| F.04.02 | Rule-based motion reads |  | R-ST-06 R-ST-18 | set_instances.action_sequence | OFF.F4.2 | covered |  |
| F.05.01 | Screen location and angle |  | R-ST-02 R-CG-07 | screens.spot, screens.screen_angle_deg | OFF.F5.1 OFF.F5.2 | covered |  |
| F.05.02 | Screener pre-action (how the screener arrives) — Sprint, flip, re-screen, ghost approach, step-up, Ram (screen-the-screener). |  | R-ST-18 | screens.screen_kind | OFF.F5.3 | partial | new-ST-5 |
| F.05.03 | Screener action after and handler read |  | R-ST-18 | screens.screener_action_after, screens.handler_read | OFF.F5.4 OFF.F5.5 | covered |  |
| F.05.04 | Off-ball spacing tags during the PnR — Corner fill, slot, dunker, lift, shake. |  | R-ST-03 | configuration_snapshots.players | OFF.F5.6 | partial | new-ST-6 |
| F.05.05 | Double ball screens (Spain, Detroit, stack, step-up) |  | R-ST-18 | screens.screen_kind | OFF.F5.7 | covered |  |
| F.06.01 | Handoff, fake handoff, keep |  | R-ST-18 | screens.screen_kind, actions.action_code | OFF.F6 | covered |  |
| F.07.01 | Post entries, splits, high-low, duck-in |  | R-ST-04 R-DF-07 | post_touches.post_move_code, post_touches.result | OFF.F7 | covered |  |
| F.08.01 | Down, flare, back, cross, stagger, pin-down, elevator, hammer |  | R-ST-02 R-ST-18 | screens.screen_kind, screens.offense_code | OFF.F8.1 | covered |  |
| F.08.02 | Screen-use reads (curl, fade, straight, reject) |  | R-ST-18 | screens.handler_read | OFF.F8.3 | covered |  |
| F.09.01 | Isolation and clear-outs |  | R-ST-04 R-ST-05 | set_instances.set_code, set_instances.synergy_outcome_code | OFF.F9 | covered |  |
| F.09.02 | Drive-and-kick and paint touches — Paint touches per chance and kick-outs. |  | R-EV-06 R-TR-20 | drives.result | OFF.F10 | partial | new-ST-7 |
| F.10.01 | Zone offence actions |  | R-ST-24 | actions.action_code | OFF.F11 | covered |  |
| F.10.02 | Press break |  | R-ST-24 | actions.action_code, set_instances.set_code | OFF.F12 | covered |  |
| F.11.01 | After timeout (ATO) |  | R-EV-15 R-CH-06 | play_calls.after_timeout, possessions.after_timeout, timeouts.ato_set_instance_id | OFF.F13.1 | covered |  |
| F.11.02 | BLOB and SLOB |  | R-SY-04 R-DT-14 | possessions.inbound_type, set_instances.situation | OFF.F13.2 OFF.F13.3 | covered |  |
| F.11.03 | End of half and end of game |  | R-ST-23 R-PE-07 | set_instances.situation | OFF.F13.4 | covered |  |
| F.11.04 | Late clock |  | R-ST-05 | set_instances.situation, shots.shot_clock_s | OFF.F13.5 | covered |  |
| F.11.05 | Free-throw alignments |  | R-DT-13 | free_throws.lane_occupant_ids | OFF.F13.6 | covered |  |
| F.11.06 | Jump-ball plays |  | R-EV-14 | jump_balls.circle_formation | OFF.F13.7 | covered |  |
| F.11.07 | Delay and clock-kill |  | R-PE-07 R-SR-11 | set_instances.situation | OFF.F13.8 | covered |  |
| F.11.08 | Two-for-one and last shot |  | R-SR-11 R-PE-07 | state_second.two_for_one_window, state_second.last_shot_window |  | covered |  |
| F.12.01 | Crash vs get-back policy |  | R-EV-08 | rebounds.crashers_off, rebounds.leaker_ids | OFF.F14 | covered |  |
| F.12.02 | Spacing systems (4-out, 5-out, dunker spot) |  | R-CG-07 R-ST-18 | frame_geometry.spacing_mean_m, configuration_snapshots.alignment_code | OFF.F15 | covered |  |
| F.13.01 | Set templates, match, timeline, phases |  | R-ST-04 R-ST-05 R-ST-07 R-ST-08 R-ST-13 | set_instances.match_confidence, set_instance_phases.phase_name, set_instances.classifier_probs |  | covered |  |
| F.13.02 | Counters and broken plays |  | R-ST-05 | set_instances.departure_step, set_instances.counter_code |  | covered |  |
| F.13.03 | Unmatched chances and new-set clustering |  | R-ST-09 | set_instances.unmatched_cluster_id |  | covered |  |
| F.13.04 | Template status and role-based templates |  | R-ST-11 R-ST-12 | set_instances.template_version |  | covered |  |
| F.13.05 | Name collisions and secondary vocabularies |  | R-ST-22 R-ST-15 | set_instances.set_code | OFF.F16 | covered |  |
| F.13.06 | Synergy-style outcome labels |  | R-TR-11 | set_instances.synergy_outcome_code | OFF.F17 | covered |  |
| F.13.07 | MSU addendum and playbook library |  | R-ST-14 R-ST-10 | profile_snapshots.metric_code | OFF.F18 | covered |  |
| F.13.08 | Team style measures |  | R-ST-25 | profile_snapshots.metric_code |  | covered |  |
| F.13.09 | Ball movement (passes per chance, reversals, side changes) — How much the ball moves before the shot: passes, ball reversals (ball crosses x = 0 from one wing to the other) and side changes per chance. |  | R-ST-24 R-ST-25 | passes.pass_id, chances.chance_id |  | partial | new-ST-8 |

### G. Group tactics: defence

Team defensive structures from docs/taxonomy/defense_full.md (DEF.F1-F18).

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| G.01.01 | Man philosophy (help-first, pressure, directional, switching, pack line) |  | R-DF-04 | scheme_states.l1_base_scheme_code | DEF.F1 | covered |  |
| G.01.02 | MSU documented principles |  | R-DF-21 | scheme_states.msu_principle_flags | DEF.F1.6 | covered |  |
| G.01.03 | Force direction and ball pressure |  | R-DF-04 | scheme_states.l4_force_dir, scheme_states.l4_pressure_m | DEF.F2 | covered |  |
| G.01.04 | Pick-up point — Where the defence first pressures the ball (full, three-quarter, half court, top of the key). |  |  |  |  | missing | new-DF-3 |
| G.02.01 | Ball-screen coverage (4 coarse, 13+ fine, drop depth) |  | R-DF-06 R-DF-16 R-ST-20 | screens.coverage_coarse, screens.coverage_fine_code, screens.drop_depth_m | DEF.F3 | covered |  |
| G.02.02 | Handoff coverage |  | R-DF-06 | screens.coverage_fine_code | DEF.F4 | covered |  |
| G.02.03 | Off-ball screen coverage |  | R-DF-07 | screens.coverage_fine_code | DEF.F5 | covered |  |
| G.03.01 | Post positioning (front, three-quarter, behind) |  | R-DF-07 | post_touches.post_defense | DEF.F6.1 | covered |  |
| G.03.02 | Post doubles and rotations |  | R-DF-07 | post_touches.double_team | DEF.F6.3 DEF.F6.4 | covered |  |
| G.03.03 | Lob protection — Weak-side help against lobs over a fronting defender. |  | R-ST-26 |  | DEF.F6.5 | partial | new-DF-4 |
| G.04.01 | Help position per defender per second |  | R-DF-02 | defensive_matchups.dist_to_ball_m, defensive_matchups.in_gap | DEF.F7.1 | covered |  |
| G.04.02 | Rim protector |  | R-DF-03 | scheme_states.rim_protector_id, defensive_matchups.is_rim_protector |  | covered |  |
| G.04.03 | Roller coverage and help actions (tag, stunt, dig, step-and-release) |  | R-DF-15 | scheme_states.l3_help_actions | DEF.F7.2 DEF.F7.3 | covered |  |
| G.04.04 | Rotations and reaction delay |  | R-DF-08 R-CH-05 | reaction_events.latency_s | DEF.F7.4 | covered |  |
| G.04.05 | Closeouts |  | R-DF-08 | reaction_events.closeout_distance_m | DEF.F7.5 | covered |  |
| G.05.01 | Man vs zone discrimination and named zones |  | R-DF-04 R-DF-17 | scheme_states.zone_family_probs | DEF.F8 | covered |  |
| G.05.02 | Presses (full and half court, named, policies) |  | R-DF-12 R-DF-18 | scheme_states.press_code | DEF.F9 | covered |  |
| G.05.03 | Junk defences (box-and-1, triangle-and-2) |  | R-DF-04 | scheme_states.l1_base_scheme_code | DEF.F10 | covered |  |
| G.06.01 | Scheme change events and triggers |  | R-DF-05 R-DF-19 | scheme_changes.trigger_type, scheme_changes.scheme_before, scheme_changes.scheme_after | DEF.F11 | covered |  |
| G.06.02 | Scheme policy by context |  | R-DF-14 | profile_snapshots.metric_code | DEF.F11.4 | covered |  |
| G.07.01 | Get-back clocks, ball stopper, defenders back |  | R-DF-10 R-DF-20 R-TR-12 | transition_phases.defenders_back_at_2_3_4s, transition_phases.ball_stopper_id, transition_phases.last_back_id | DEF.F12 | covered |  |
| G.07.02 | Cross-matches and recoveries |  | R-DF-10 R-TR-12 | transition_phases.def_phase_times |  | covered |  |
| G.08.01 | Box-outs and crash numbers |  | R-EV-08 R-PC-08 | box_outs.result, rebounds.crashers_def | DEF.F13 | covered |  |
| G.09.01 | Inbound (BLOB/SLOB) defence |  | R-DF-19 | scheme_states.l0_phase | DEF.F14 | covered |  |
| G.09.02 | End-game defence and foul-up-3 |  | R-PE-07 | fouls.is_end_game_intentional | DEF.F14 DEF.F15 | covered |  |
| G.09.03 | Foul-trouble effect on defensive aggressiveness — How a defender in foul trouble changes distance, contests and help. |  | R-MD-16 | foul_state.foul_trouble | DEF.F15 | partial | new-DF-5 |
| G.10.01 | Matchup per defender per second |  | R-DF-01 | defensive_matchups.attacker_id, defensive_matchups.matchup_prob | DEF.F18.3 | covered |  |
| G.10.02 | Switch mismatches |  | R-DF-09 | defensive_matchups.mismatch_height_cm, defensive_matchups.mismatch_speed_mps |  | covered |  |
| G.10.03 | Shell shape |  | R-DF-11 | scheme_states.shell_centroid_xy_m, scheme_states.shell_area_m2 |  | covered |  |
| G.10.04 | Communication vocabulary as behaviours |  | R-CO-08 | screens.coverage_fine_code | DEF.F16 | covered |  |
| G.10.05 | Defensive play-type outcome labels |  | R-TR-11 | set_instances.synergy_outcome_code | DEF.F17 | covered |  |
| G.10.06 | Per-second label hierarchy |  | R-DF-04 | scheme_states.l0_phase, scheme_states.l1_base_scheme_code, scheme_states.l2_active_coverages | DEF.F18.1 | covered |  |
| G.10.07 | MSU's own defence measured the same way |  | R-DF-13 | scheme_states.is_msu_defending |  | covered |  |

### H. Outcomes and value

What happened and what it was worth: possession and chance outcomes, efficiency, expected points, shot and decision quality, player and lineup value, win probability, market-relative value.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H.01.01 | Possession end type and points |  | R-SY-04 R-DQ-06 | possessions.end_type, possessions.points |  | covered |  |
| H.01.02 | Chance outcomes (11-outcome multinomial) |  | R-PE-02 R-SY-05 | chances.outcome_code, chances.points |  | covered |  |
| H.01.03 | Second-chance points and putbacks |  | R-SY-05 | chances.second_chance_points, chances.is_putback |  | covered |  |
| H.01.04 | Turnover types and costs |  | R-EV-10 R-VL-11 | turnovers.turnover_type, turnovers.cost_xpts |  | covered |  |
| H.02.01 | Box score (team and player) |  | R-IV-15 R-DQ-06 | team_box.points, player_box.points |  | covered |  |
| H.02.02 | Four factors, pace, efficiency (as of date) |  | R-OS-01 | profile_snapshots.metric_code, ratings_snapshots.metric_code |  | covered |  |
| H.02.03 | Fast-break, paint, off-turnover points |  | R-TR-27 | team_box.fast_break_points, team_box.points_in_paint, team_box.points_off_turnovers |  | covered |  |
| H.02.04 | Bench points and starter/bench split |  |  | player_box.starter, player_box.points |  | partial | new-OS-1 |
| H.03.01 | Possession value at 10 Hz |  | R-VL-01 R-SR-12 | possession_value.value_xpts |  | covered |  |
| H.03.02 | Pass, shot and turnover parts of value |  | R-VL-03 | possession_value.p_shot_part, possession_value.p_pass_part, possession_value.p_turnover_part |  | covered |  |
| H.03.03 | Value change per action and credit |  | R-VL-02 R-VL-09 | value_credits.value_delta_xpts, value_credits.credit_role |  | covered |  |
| H.03.04 | Shot quality |  | R-VL-04 | shots.shot_quality_xpts |  | covered |  |
| H.03.05 | Shot-making (points above shot quality) — Actual minus expected points per shooter. |  | R-VL-04 R-VL-12 | shots.shot_quality_xpts |  | partial | new-VL-1 |
| H.03.06 | Decision quality |  | R-VL-05 | passes.decision_quality_xpts |  | covered |  |
| H.03.07 | Value of fouls drawn, offensive rebounds, turnovers |  | R-VL-10 R-VL-11 | fouls.value_of_foul_drawn, rebounds.value_xpts, turnovers.cost_xpts |  | covered |  |
| H.03.08 | Configuration and set value |  | R-VL-08 R-ST-08 | set_instances.value_start, set_instance_phases.value_at_boundary |  | covered |  |
| H.03.09 | Neural sequence outcome model |  | R-VL-13 | possession_value.outcome_probs |  | covered |  |
| H.04.01 | Off-ball value (gravity, screens) |  | R-VL-06 | value_credits.defender_displacement_m |  | covered |  |
| H.04.02 | Player vs player |  | R-VL-07 | defensive_matchups.attacker_id, value_credits.credit_role |  | covered |  |
| H.04.03 | Shrunk player estimates |  | R-VL-12 | profile_snapshots.ci95 |  | covered |  |
| H.04.04 | Pair and lineup effects (RAPM-style) |  | R-CH-01 | lineup_stints.points_for, lineup_stints.points_against |  | covered |  |
| H.04.05 | Public impact metrics (BPM, PORPAG, RAPM, etc.) |  | R-DS-03 R-DS-10 | player_card.bpm, player_card.porpag, ratings_snapshots.metric_code |  | covered |  |
| H.04.06 | Defensive value per player (stops, contests, deterrence) — Defensive credit beyond steals and blocks: contests, rim deterrence, help value. |  | R-VL-07 R-VL-02 | value_credits.credit_role |  | partial | new-VL-2 |
| H.04.07 | Passing network and movement coordination |  | R-CH-02 R-CH-03 R-CH-04 | passes.passer_id, passes.receiver_id, screens.screener_handler_timing_s |  | covered |  |
| H.05.01 | Pre-game win probability, margin, total |  | R-PR-01 R-PR-02 | predictions.target, predictions.point_value, predictions.quantiles |  | covered |  |
| H.05.02 | In-game win probability |  | R-PR-11 R-MD-17 | possessions.pre_win_prob |  | covered |  |
| H.05.03 | 5-minute window predictions |  | R-PR-06 | predictions.window_id |  | covered |  |
| H.05.04 | Player prop distributions |  | R-PR-07 | predictions.player_id |  | covered |  |
| H.05.05 | Calibration and scoring |  | R-PR-05 R-PE-10 | predictions.log_loss, predictions.crps, predictions.pit |  | covered |  |
| H.05.06 | Edge and closing-line value |  | R-MK-05 R-MK-06 R-MK-09 | predictions.edge, predictions.clv, predictions.paper_stake_frac |  | covered |  |
| H.05.07 | Possession-engine components |  | R-PE-03 R-PE-04 R-PE-05 R-PE-08 R-PE-09 R-PE-11 R-PE-12 R-PE-13 | simulation_runs.level, simulation_runs.param_uncertainty, simulation_runs.component_diagnostics |  | covered |  |
| H.05.08 | Baselines, walk-forward and sample rules |  | R-PR-03 R-PR-04 R-PR-08 R-PR-09 R-PR-10 | predictions.is_holdout_2025_26, predictions.priced_events_in_market |  | covered |  |
| H.06.01 | Pressure performance |  | R-CO-04 | state_second.clutch_flag, shots.shot_quality_xpts |  | covered |  |
| H.06.02 | Surprise per event |  | R-GU-02 | events.surprise_nats |  | covered |  |

### I. Physical and load

Kinematics and workload from tracking: speed, acceleration, jumps, distance, fatigue and minutes.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| I.01.01 | Velocity, acceleration, heading |  | R-DT-08 R-SR-07 | player_positions.speed_mps, player_positions.accel_mps2, player_positions.heading_deg |  | covered |  |
| I.01.02 | Tracked point and filter |  | R-PL-10 | load_stint_bins.tracked_point, load_stint_bins.filter_name, player_positions.tracked_point |  | covered |  |
| I.01.03 | Physics limits |  | R-IV-13 | state_frame.invariant_breaks |  | covered |  |
| I.02.01 | Distance and time by 0.1 m/s speed bin |  | R-PL-09 R-PL-01 R-PL-11 | load_stint_bins.time_s, load_stint_bins.distance_m |  | covered |  |
| I.02.02 | Acceleration and deceleration efforts |  | R-PL-02 R-PL-12 | accel_efforts.peak_mps2, accel_efforts.band |  | covered |  |
| I.02.03 | Top speed (p95 and 1 s peak) |  | R-PL-03 R-PC-05 | player_card.trk_top_speed_ms_p95 |  | covered |  |
| I.02.04 | Load denominators (live, minutes played, on-court) |  | R-PL-15 | load_stint_bins.stint_live_time_s, load_stint_bins.stint_minutes_played |  | covered |  |
| I.02.05 | Coverage-corrected load and exclusions |  | R-PL-05 R-PL-14 | load_stint_bins.observed_frac, load_stint_bins.excluded_low_coverage |  | covered |  |
| I.02.06 | Jump load (count and height per minute) |  | R-CG-11 | player_positions.jump_height_m |  | partial | (see E.01.03 jumps proposal) |
| I.02.07 | Direction-weighted load (lateral and backward running) — Speed-only distance under-ranks defensive load (C82). |  |  |  |  | missing | new-PL-3 |
| I.02.08 | Contact load (screens set and absorbed, box-outs, post contact) |  | R-DT-16 | box_outs.contact_duration_s, screens.contact_distance_m |  | partial | new-PL-4 |
| I.03.01 | Minutes played and continuous minutes |  | R-PL-03 R-PE-06 | player_box.minutes, accel_efforts.continuous_minutes_at_start, player_card.max_continuous_min |  | covered |  |
| I.03.02 | Within-game decline |  | R-PL-03 R-CO-07 | accel_efforts.period, load_stint_bins.period |  | covered |  |
| I.03.03 | Recovery after stoppages |  | R-PL-04 | timeouts.duration_s |  | covered |  |
| I.03.04 | Relative speed (v_ref) and interpretation thresholds |  | R-PL-16 R-PL-17 | profile_snapshots.metric_code |  | covered |  |
| I.03.05 | Season load trend vs availability |  | R-PL-06 | availability.status, profile_snapshots.metric_code |  | covered |  |
| I.03.06 | Calibration of physical measures |  | R-PL-13 | run_requirement_results.metric |  | covered |  |

### J. Context

Everything outside the play: schedule, travel, rest, venue, crowd, referees, availability, rankings, markets, stakes, beliefs.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| J.01.01 | Tip time (local, UTC), day of week |  | R-MD-18 R-CX-13 | games.tip_local, games.tip_scheduled_utc |  | covered |  |
| J.01.02 | Days of rest and games in 7 and 14 days |  | R-CX-05 R-MD-18 | team_game_context.days_rest, team_game_context.games_last_7d |  | covered |  |
| J.01.03 | Travel distance, time zones, mode |  | R-CX-05 | team_game_context.travel_from_prev_km, team_game_context.time_zones_crossed, team_game_context.travel_mode |  | covered |  |
| J.01.04 | Road-trip structure — Game index within a road trip; returning home between games (C35). |  |  |  |  | missing | new-CX-5 |
| J.01.05 | Tip time on each team's body clock — Local tip time expressed in each team's home time zone (C72, C73). |  | R-CX-13 | games.tip_scheduled_utc, teams.campus_tz |  | partial | new-CX-6 |
| J.01.06 | Weather |  | R-CX-10 | team_game_context.weather_summary |  | covered |  |
| J.01.07 | Academic calendar |  | R-CX-13 | team_game_context.academic_flags |  | covered |  |
| J.02.01 | Home, away, neutral and proximity |  | R-CX-04 R-CX-14 | team_game_context.side, team_game_context.campus_to_venue_km |  | covered |  |
| J.02.02 | Attendance and crowd |  | R-CX-04 R-CX-17 | games.attendance, teams.enrollment |  | covered |  |
| J.02.03 | Altitude difference |  | R-CX-16 | team_game_context.altitude_diff_m |  | covered |  |
| J.02.04 | Referee crew features as of date |  | R-CX-06 R-RF-06 | game_officials.official_id, profile_snapshots.metric_code |  | covered |  |
| J.02.05 | Jersey pairing and contrast |  | R-CX-07 | games.jersey_contrast_de |  | covered |  |
| J.03.01 | Availability, minutes limits, continuity |  | R-CX-08 R-FD-05 | availability.status, team_game_context.returning_minutes_frac |  | covered |  |
| J.03.02 | Ratings and rankings as of date (KenPom, Torvik, NET, AP) |  | R-FD-06 R-DS-04 | ratings_snapshots.system, ratings_snapshots.value, ratings_snapshots.rank |  | covered |  |
| J.03.03 | Opponent recent form — Last game result and margin, overtime last game, streak. |  | R-OS-01 |  |  | partial | new-CX-7 |
| J.03.04 | Coach head-to-head and prior meetings |  | R-CC-05 R-CX-19 | profile_snapshots.metric_code |  | covered |  |
| J.03.05 | Opponent baselines and scouting |  | R-OS-01 R-OS-02 R-OS-05 R-OS-03 | profile_snapshots.metric_code |  | covered |  |
| J.04.01 | Stakes stamp (conference, tournament, seeds, rivalry, national TV) |  | R-CX-15 R-CX-11 | team_game_context.stakes_codes, team_game_context.is_rivalry |  | covered |  |
| J.04.02 | Standings and seeding at stake |  | R-CX-11 | team_game_context.stakes_codes |  | covered |  |
| J.04.03 | Season phase and game number — Game number in season, conference game number. |  | R-MD-14 | games.game_type |  | partial | new-CX-8 |
| J.05.01 | Closing lines (spread, total, moneyline) |  | R-MK-01 R-MK-14 R-MK-17 R-MK-26 R-MK-27 R-MK-28 R-MK-29 | market_snapshots.line, market_snapshots.price_american, lines_odds_snapshots, market_snapshots.line_is_integer |  | covered |  |
| J.05.02 | Snapshot schedule (open, 24 h, 1 h, close, 1H, props) |  | R-MK-02 R-MK-16 R-MK-10 R-MK-25 R-MK-33 | market_snapshots.snapshot_label, market_snapshots.market_phase |  | covered |  |
| J.05.03 | Prediction-market prices |  | R-MK-03 | market_snapshots.bid, market_snapshots.ask, market_snapshots.last, prediction_market_prices |  | covered |  |
| J.05.04 | Fair probabilities (de-vig) |  | R-MK-04 R-MK-15 R-MK-30 R-MK-32 | market_snapshots.fair_prob_power, market_snapshots.fair_prob_shin |  | covered |  |
| J.05.05 | Line movement as a feature (separate model variant) |  | R-MK-08 | simulation_runs.uses_market_input |  | covered |  |
| J.05.06 | Public betting share — Mentioned in the context list; no source chosen. |  |  |  |  | missing | new-MK-19 |
| J.06.01 | Beliefs register and hypothesis candidates — Common beliefs (hot hand, momentum, timeouts, icing, tip value) turned into testable candidates C1-C82. |  | R-HY-01 R-HY-02 | hypothesis_results.hypothesis_id |  | partial | (Aldemir: register candidates) |
| J.06.02 | Pre-game card (24 h and 1 h) |  | R-CX-18 R-CX-09 | pregame_cards.horizon, pregame_cards.card_sha256 |  | covered |  |
| J.06.03 | Feature registry and causal classes |  | R-CX-01 R-CX-02 R-CX-03 | pregame_cards.context_feature_values |  | covered |  |

### K. Coaching and decisions

Choices coaches and players make and how they are measured.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| K.01.01 | Play calls (set called, source) |  | R-EV-15 R-AU-02 R-CH-06 | play_calls.mapped_set_code, play_calls.call_source |  | covered |  |
| K.01.02 | Substitution and rotation patterns |  | R-CH-06 R-PE-06 | substitutions.reason_inferred, lineup_stints.duration_s |  | covered |  |
| K.01.03 | Timeout timing vs runs; timeouts left at half end |  | R-CC-02 R-EV-15 | timeouts.game_clock_s, timeouts.left_after_msu |  | covered |  |
| K.01.04 | Challenge decisions |  | R-EV-16 | coaches_challenges.play_type, coaches_challenges.outcome |  | covered |  |
| K.01.05 | End-game fouling, two-for-one, last-shot holds |  | R-PE-07 | fouls.is_end_game_intentional, state_second.two_for_one_window |  | covered |  |
| K.01.06 | Starting lineup and matchup assignment |  | R-OS-04 R-DF-01 | player_box.starter, defensive_matchups.attacker_id |  | covered |  |
| K.01.07 | Scheme adjustments and halftime changes |  | R-DF-05 R-DF-19 R-CH-06 | scheme_changes.trigger_type |  | covered |  |
| K.01.08 | Tempo choice (push vs pull back) |  | R-TR-16 R-TR-24 | transition_phases.pushed, transition_phases.passed_up_category |  | covered |  |
| K.01.09 | Foul-trouble management (sitting a player) |  | R-PE-06 R-CC-03 | substitutions.reason_inferred |  | covered |  |
| K.01.10 | Press and zone usage decisions |  | R-DF-14 R-DF-18 | scheme_states.press_code |  | covered |  |
| K.01.11 | Icing the free-throw shooter — Timeout called right before an opponent's free throws (C11). |  |  | timeouts.game_clock_s, free_throws.ft_sequence_id |  | partial | new-CH-1 |
| K.01.12 | Minutes limits and rest management |  | R-CX-08 | availability.minutes_limit_note |  | covered |  |
| K.01.13 | Coach reactions and sideline behaviour |  | R-CC-03 R-CC-04 | bench_events.event_type |  | covered |  |
| K.01.14 | Coach card system tags |  | R-CC-01 | coaches.system_offense_codes, coaches.system_defense_codes |  | covered |  |
| K.01.15 | Opposing coaches' records |  | R-CH-07 | coaches.coach_id, profile_snapshots.metric_code |  | covered |  |
| K.02.01 | Shoot, pass, drive choice and decision quality |  | R-VL-05 R-GU-01 | passes.decision_quality_xpts, belief_states.next_action_probs |  | covered |  |
| K.02.02 | Decision latency |  | R-CO-01 R-CO-06 | touches.decision_latency_s |  | covered |  |
| K.02.03 | After-error behaviour |  | R-CO-05 | profile_snapshots.metric_code |  | covered |  |
| K.02.04 | Shot selection by shot clock and zone |  | R-PC-11 | shots.shot_clock_s, shots.release_sector_15deg |  | covered |  |

### L. Media and video

Video files, broadcast camera shots, graphics and scorebug, replays, audio and commentary, and our visual outputs.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| L.01.01 | Capture standard and best-quality download |  | R-VI-01 R-VI-14 | video_files.width_px, video_files.fps_nominal, video_files.bitrate_kbps |  | covered |  |
| L.01.02 | Intake report |  | R-VI-02 | video_files.intake_dropped_frames, video_files.intake_frozen_frames, video_files.intake_pass |  | covered |  |
| L.01.03 | File hash and immutability |  | R-FD-09 R-VI-09 | video_files.video_id, video_files.size_bytes |  | covered |  |
| L.01.04 | Timeline mapping (VFR, interlacing) |  | R-VI-12 | frames.pts_raw, frames.is_duplicate_of_prev, video_files.interlaced |  | covered |  |
| L.01.05 | Download provenance and platform terms |  | R-RG-10 | video_files.download_tool, video_files.platform_terms_note |  | covered |  |
| L.01.06 | Processing resolution and hardware decode |  | R-VI-15 R-VI-16 | run_records.processing_resolution |  | covered |  |
| L.02.01 | Camera shot type (9 classes) |  | R-VI-03 R-MD-11 R-SR-10 | frames.camera_shot_type, state_frame.camera_shot_type | global_metadata.camera_shot_type | covered |  |
| L.02.02 | Finer camera views (reverse angle, baseline, under-basket, skycam, iso) |  | R-SR-10 | state_frame.reverse_angle |  | partial | new-VI-2 |
| L.02.03 | Replays and slow motion |  | R-VI-04 | frames.is_replay, frames.replay_segment_id |  | covered |  |
| L.02.04 | Coverage score and usable possessions |  | R-VI-05 R-VI-06 | frames.coverage_score, possessions.usable_flag, possessions.coverage_mean |  | covered |  |
| L.02.05 | Graphics mask (scorebug, lower thirds, wipes) |  | R-VI-07 | frames.graphics_mask_ref, detections.inside_graphics_mask |  | covered |  |
| L.02.06 | Commercial breaks and studio segments |  | R-VI-03 | frames.camera_shot_type |  | covered |  |
| L.02.07 | Broadcast replays as secondary evidence — Replays show events (fouls, out of bounds, blocks) the live camera missed; kept out of tracking but usable as labelled evidence. |  | R-VI-04 | events.from_replay_frame, frames.replay_segment_id |  | partial | new-VI-3 |
| L.03.01 | Scorebug templates per network |  | R-VI-11 R-MD-20 | scoreboard_ocr.scorebug_template_id, games.graphics_package_id |  | covered |  |
| L.03.02 | Scorebug OCR fields |  | R-SY-01 R-SR-15 | scoreboard_ocr.game_clock_raw, scoreboard_ocr.score_home_raw, scoreboard_ocr.timeouts_home_raw |  | covered |  |
| L.03.03 | Scorebug lag vs arena board |  | R-SB-01 R-SB-03 | score_events.board_lag_s, scoreboard_flags.flag_type |  | covered |  |
| L.03.04 | Stat graphics and lower thirds as weak labels — On-screen graphics announcing fouls, timeouts, player stats or set names. |  | R-VI-07 |  |  | missing | new-AU-1 |
| L.04.01 | Whistles |  | R-RF-01 R-RF-02 | whistles.video_ts_ms, whistles.masked_by_crowd |  | covered |  |
| L.04.02 | Buzzers and horns — Period-end and shot-clock horns, substitution horns. |  | R-MB-06 | audio_seconds.buzzer_present |  | partial | new-AU-2 |
| L.04.03 | Crowd loudness and music flag |  | R-AU-03 R-AU-04 | audio_seconds.loudness_rel_db, audio_seconds.music_flag |  | covered |  |
| L.04.04 | Commentary transcript and weak labels |  | R-AU-01 R-AU-02 | commentary_segments.text, commentary_segments.mentions |  | covered |  |
| L.04.05 | Audio-video alignment |  | R-VI-08 | video_files.audio_offset_ms |  | covered |  |
| L.04.06 | Broadcast network and crew |  | R-MD-20 R-FD-01 | games.broadcast_network, games.broadcast_crew |  | covered |  |
| L.05.01 | Broadcast plus top-down replay in sync |  | R-VZ-01 R-VZ-04 |  |  | covered |  |
| L.05.02 | Traceable numbers with n and interval |  | R-VZ-02 R-VZ-03 |  |  | covered |  |
| L.05.03 | Overlays, boards, palette |  | R-VZ-05 R-VZ-06 R-VZ-07 |  |  | covered |  |
| L.05.04 | Narration from state |  | R-GU-04 | belief_states.narration |  | covered |  |
| L.06.01 | Person detection and person filter |  | R-DT-01 R-DT-02 R-DT-17 | detections.person_class, detections.bbox_px |  | covered |  |
| L.06.02 | Team label per detection |  | R-DT-03 R-CX-07 | detections.team_label, detections.team_label_conf |  | covered |  |
| L.06.03 | Persistent tracks, track quality and gaps |  | R-DT-04 R-DT-11 | tracks.track_id, tracks.quality_mean, tracks.gaps_over_1s |  | covered |  |
| L.06.04 | Frame-exit memory and off-screen estimates |  | R-DT-06 R-DT-07 | track_exits.exit_side, track_exits.exit_speed_mps, player_positions.region95_semi_axes_m |  | covered |  |
| L.06.05 | Ground point at the feet |  | R-CG-04 | detections.foot_point_px |  | covered |  |
| L.06.06 | Player identity (lineup-constrained, jersey numbers, orientations) |  | R-ID-01 R-ID-02 R-ID-03 R-ID-04 R-ID-05 R-ID-08 R-ID-09 | tracks.player_id, tracks.jersey_number_voted, detections.orientation_slice |  | covered |  |
| L.06.07 | Identity re-confirmation and restoration |  | R-ID-06 R-ID-07 R-ID-13 | tracks.restored_after, tracks.id_switches_corrected |  | covered |  |
| L.06.08 | Identity confusions and per-player accuracy |  | R-ID-11 R-ID-14 | identity_confusions.n_confusions |  | covered |  |
| L.06.09 | Synthetic kit images (team colour only) |  | R-ID-15 |  |  | covered |  |
| L.06.10 | Ball detection, holder and event times |  | R-BL-01 R-BL-02 R-BL-04 | ball_states.image_xy_px, passes.release_ts_ms, passes.catch_ts_ms |  | covered |  |
| L.06.11 | Make or miss and made-basket fusion |  | R-BL-05 R-MB-01 R-MB-02 R-MB-03 R-MB-04 | made_basket_events.decision, made_basket_events.cue1_present |  | covered |  |
| L.06.12 | Short-horizon position forecasts |  | R-TR-07 R-GU-05 | position_forecasts.forecast_1s_xy_m, position_forecasts.error_1s_m |  | covered |  |
| L.06.13 | Public tracking-set sanity checks and source comparison |  | R-GT-05 R-VI-10 | run_requirement_results.source_tier |  | covered |  |
| L.06.14 | Officials and non-players detected separately |  | R-DT-12 R-DT-02 | official_positions.observed |  | covered |  |

### M. Data, quality and governance

Sources, licences, provenance, contracts, invariants, review, errors, versioning, rights and coordination.

| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M.01.01 | Source register and use class |  | R-DS-01 R-DS-10 R-DS-02 R-DS-06 R-DS-08 R-DS-09 R-DS-12 R-DS-14 R-DS-15 R-DS-07 | source_register.use_class, source_register.terms_url |  | covered |  |
| M.01.02 | Licence register (datasets, models, libraries) |  | R-RG-03 R-RG-04 R-RG-05 | source_register.permission_status |  | covered |  |
| M.01.03 | Secrets and keys outside the repo |  | R-DS-11 R-DS-13 R-MK-23 R-RG-11 |  |  | covered |  |
| M.01.04 | Rate limits, call logs and caching |  | R-DS-13 R-RG-08 R-MK-11 | raw_pulls.call_budget_counter, source_register.rate_limit |  | covered |  |
| M.01.05 | Point-in-time ratings only |  | R-DS-04 | ratings_snapshots.is_point_in_time |  | covered |  |
| M.01.06 | Source definition register (each source's own definitions) — Each provider's definition of possession, assist, transition, shot zones, fast-break points, minutes. |  | R-TR-11 |  |  | partial | new-DS-2 |
| M.02.01 | Raw copy before parsing |  | R-DQ-05 R-MK-13 | raw_pulls.sha256, raw_pulls.body_path |  | covered |  |
| M.02.02 | Lineage to raw rows and transform version |  | R-DQ-04 R-EN-04 | state_corrections.correction_id, registry_change_log.changed_by |  | covered |  |
| M.02.03 | Model version, source, confidence on every value |  | R-MD-09 R-SR-15 | events.matched_event_id |  | covered |  |
| M.02.04 | ID crosswalk |  | R-DS-05 R-MK-18 R-FD-02 | id_crosswalk.source_key, id_crosswalk.match_confidence |  | covered |  |
| M.02.05 | As-of rules and leakage tests |  | R-CX-09 R-PC-14 R-FD-07 R-MK-07 | pregame_cards.frozen_at_utc |  | covered |  |
| M.02.06 | Event model (one row per event, chains, unmatched stream) |  | R-EV-01 R-EV-12 R-SR-14 R-SY-02 | events.event_family, events.chain_index, cv_events_unmatched.unmatched_reason |  | covered |  |
| M.03.01 | Data contracts and quarantine |  | R-DQ-02 R-DQ-03 R-MK-21 R-MK-20 | quarantine_rows.rule_id |  | covered |  |
| M.03.02 | Invariants on the state record *(note: 34 further invariants (new-IV-01..34) are proposed in config/invariants.yaml and listed in the gap table where they close a leaf.)* |  | R-IV-01 R-IV-04 R-IV-07 | scoreboard_flags.invariant_id, config/invariants.yaml |  | covered |  |
| M.03.03 | Accounting identities and completeness |  | R-DQ-06 R-DQ-07 R-EN-03 R-VA-03 | dq_reports.check, dq_reports.value |  | covered |  |
| M.03.04 | Cross-source checks |  | R-DQ-01 R-MK-22 R-SY-10 | dq_reports.check |  | covered |  |
| M.03.05 | Drift checks |  | R-DQ-08 | dq_reports.check |  | covered |  |
| M.03.06 | Known-bias register |  | R-DQ-09 |  |  | partial | (see C.04.04 bias-register proposal) |
| M.03.07 | Independent re-derivation |  | R-DQ-10 | dq_reports.check |  | covered |  |
| M.03.08 | Scoreboard discrepancy classes and answers |  | R-SB-01 R-SB-02 R-SB-04 | scoreboard_flags.flag_type, scoreboard_flags.review_answer |  | covered |  |
| M.03.09 | Ontology coverage check — Every ontology leaf maps to requirement IDs, tables and vocabularies, re-run when the doc or schema changes. |  | R-CD-02 | config/game_ontology.yaml |  | partial | new-CD-1 |
| M.04.01 | Flag triggers and review queue |  | R-HR-01 R-HR-02 R-HR-03 R-HR-04 R-HR-08 R-HR-09 R-HR-11 | review_queue.trigger, review_queue.priority |  | covered |  |
| M.04.02 | Labels with provenance and consistency |  | R-HR-05 R-HR-06 R-HR-10 | review_labels.labeller, review_labels.is_repeat_blind |  | covered |  |
| M.04.03 | Gold sets frozen |  | R-HR-07 R-HR-12 R-VA-01 | review_labels.gold_set |  | covered |  |
| M.04.04 | Gates and robustness |  | R-GT-01 R-GT-02 R-GT-03 R-GT-04 | run_requirement_results.gate, run_requirement_results.robustness_variant |  | covered |  |
| M.04.05 | Metrics and intervals (HOTA, bootstrap by game, multiple testing) |  | R-VA-04 R-VA-05 R-VA-06 R-VA-07 R-VA-08 R-VA-09 | run_requirement_results.ci95_lo |  | covered |  |
| M.04.06 | External consultant (JEV) log — Outside verdicts, never read by the pipeline. |  | R-HY-07 |  |  | partial | new-HR-1 |
| M.05.01 | Run records and requirement results |  | R-RR-01 R-RR-02 R-RR-04 R-RR-06 R-RR-07 R-RR-08 R-RR-09 | run_records.run_id, run_requirement_results.result |  | covered |  |
| M.05.02 | Error catalogue and failure analysis |  | R-RR-03 R-RR-05 | error_catalogue.cause, error_catalogue.slice_values |  | covered |  |
| M.05.03 | Compute and storage accounting |  | R-CS-01 R-CS-02 R-CS-05 R-CS-03 R-CS-04 R-CS-06 R-CS-07 R-CS-08 R-CS-09 R-CS-10 | run_records.gpu_hours, run_records.storage_raw_gb |  | covered |  |
| M.05.04 | Reproducibility, resumable chunks, versioned outputs |  | R-EN-02 R-EN-05 R-EN-07 | run_records.seed, run_records.chunks_done |  | covered |  |
| M.06.01 | Schemas, units in names, thresholds in config |  | R-EN-01 R-EN-06 R-MK-31 | schema/global_metadata.yaml |  | covered |  |
| M.06.02 | Registry versioning and change log |  | R-FD-10 | registry_change_log.old_value, registry_change_log.reason |  | covered |  |
| M.06.03 | Vocabulary map |  | R-MD-10 R-ST-15 R-ST-22 | config/vocabulary_map.yaml |  | covered |  |
| M.06.04 | Rights gate, privacy and footage control |  | R-RG-01 R-RG-02 R-RG-06 R-RG-11 R-MK-24 R-RG-09 |  |  | covered |  |
| M.06.05 | Read-only market collection |  | R-RG-07 R-MK-12 R-MK-19 | config/markets.yaml |  | covered |  |
| M.06.06 | Board, protocol, user inputs, freeze |  | R-CD-01 R-CD-03 R-CD-04 R-CD-05 R-EN-08 |  |  | covered |  |
| M.06.07 | Hypothesis protocol |  | R-HY-01 R-HY-03 R-HY-04 R-HY-05 R-HY-06 | hypothesis_results.decision, config/hypotheses.yaml |  | covered |  |
| M.06.08 | Taxonomy detection signatures |  | R-ST-16 |  | OFF DEF MS | covered |  |
| M.06.09 | Pitch package |  | R-PT-01 |  |  | covered |  |

## 6. Gap list: proposed new requirements

One row per proposal. Units: m, s, degrees, m/s. Priority 1 = needed before the first processed games are trusted; 2 = needed for the value and tactics layers; 3 = completeness.

| Proposed ID | Tier | Leaf | Requirement | Acceptance criterion | Table / vocabulary change | Priority |
| --- | --- | --- | --- | --- | --- | ---: |
| new-SR-1 | Shall | A.01.04 Intermissions (half time, before extra periods) | Record each intermission (half time and before every extra period) as a stoppage row with start and end video time, duration and the teams' return time to the floor. | Intermission duration within +/- 2 s of the scoreboard countdown or the video cut times on 100% of processed games; every game has exactly 1 + n_OT intermission rows. | timeouts: allow timeout_type = intermission (or a new `intermissions` table: game_id, kind, start_ts_ms, end_ts_ms, duration_s). | 3 |
| new-FD-2 | Shall | A.01.07 Forfeit and no contest | Game registry status distinguishes forfeited, no-contest and suspended games, with the playing time completed (s) and the rule applied. | games.status takes values final, forfeit, no_contest, suspended, postponed, canceled; for every non-final game the completed playing time is stored in s (+/- 1 s) and the game is excluded from engine training unless status = final. | games.status enum: add forfeit, no_contest, suspended; new column games.playing_time_completed_s (s). | 3 |
| new-FD-3 | Should | A.01.08 Interrupted or suspended game | Record interruptions longer than 300 s (floor, lighting, clock failure, emergencies) with cause, game clock at interruption and resumption date-time. | Each interruption row carries game_clock_s (0.1 s), period, cause from a fixed list and resumption UTC; possessions spanning an interruption are flagged and excluded from tempo statistics. | New stoppage cause `interruption` in state_frame.stoppage_kind; new columns games.interrupted (bool), games.resumed_utc. | 3 |
| new-RL-1 | Shall | A.01.10 Rules edition in force per game | Every game row carries a rules_edition_id that points to a versioned rules configuration (config/rules_ncaa_men_<season>.yaml) holding every rule-derived constant (clock lengths, shot-clock values, foul limits, timeout allotments, court marks, challenge rules) with its rule citation; every check and simulation reads constants from that edition only. | 100% of games have a rules_edition_id; a test changes one constant in a copy of the edition and every dependent check changes result; 0 rule constants hard-coded in code (grep test). | New config files config/rules_ncaa_men_<season>.yaml (merge of court_ncaa_men.yaml constants and invariants.yaml constants); new column games.rules_edition_id. | 1 |
| new-SR-2 | Shall | A.02.02 Game clock start triggers | Store for every clock start the trigger (throw-in touch, jump-ball tap, free-throw touch, period start) and the delay between the trigger frame and the first frame the clock is seen running. | Trigger correct on >= 95% of clock starts in gold-v1 (proposal); median start delay reported per game in s; delays > 1.0 s flagged as timing-mistake candidates (Rule 5-12). | New columns restarts.clock_start_trigger (enum) and restarts.clock_start_delay_s (s). | 2 |
| new-SY-2 | Shall | A.03.06 No-reset situations | Shot-clock reset and no-reset events use the full cause list of the rules (every 2-11.6.a/b/c/d article and 2-11.2 off) as their cause vocabulary, including no-reset stoppages, so every stoppage with a live shot clock has a recorded expected value. | shot_clock_resets.cause takes one of the 33 causes in config/invariants.yaml shot_clock_reset_table; >= 95% of stoppages with the shot clock on carry a cause; rule_match computed on 100% of them. | shot_clock_resets.cause enum := shot_clock_reset_table causes (keep the 6 coarse values as cause_coarse). | 1 |
| new-SY-3 | Shall | A.04.04 Possession counts under each source's definition | Store per team per game the possession count under every source definition in use (ours, FGA - ORB + TO + 0.475 x FTA, Torvik, CBBD, hoopR NCAA engine, Synergy-style chances), with each source's definition text, and report the differences. | All definitions present for 100% of games with PBP; our count within +/- 2 of the formula estimate in >= 95% of games (proposal); every difference > 3 listed for review. | New table `possession_counts` (game_id, team_id, definition_code, count, definition_ref) or columns on team_box. | 2 |
| new-EV-1 | Should | A.04.08 Jump-ball violations | Record jump-ball violations (who, which article) and re-jumps on every jump ball. | Every jump ball has violation = none or a 9-8 article; re-jumps stored as kind = rejump; 100% agreement with PBP where PBP logs the violation. | New column jump_balls.violation_code (Rule 9-8 article or none). | 3 |
| new-SR-3 | Shall | A.04.12 Frontcourt and backcourt status of team control | State every frame whether the team in control has frontcourt status, with the frame it was established and the player and ball positions that established it. | Frontcourt-status changes within +/- 0.2 s of gold on >= 95% of possessions (proposal); ball and feet positions from tracking with mapping error <= 0.30 m median. | New columns state_frame.frontcourt_status (bool) and state_frame.frontcourt_established_ts_ms. | 2 |
| new-SR-4 | Shall | A.04.13 10-second backcourt count | Store a running 10-second backcourt count per frame from the start of team control in the backcourt (reset rules per 9-10), and the time each possession reaches the frontcourt. | Backcourt count within +/- 0.2 s of a hand-timed count on >= 95% of possessions (proposal); every 10-second violation in PBP has a count >= 10.0 s. | New column state_frame.backcourt_count_s (s, 0.1 s); possessions.frontcourt_entry_s (s since control). | 2 |
| new-SR-5 | Should | A.04.14 Closely guarded 5-second count | Store the closely-guarded count per touch: seconds the holder spends holding (not dribbling) in the frontcourt with the same defender within 1.83 m. | Count within +/- 0.3 s of a hand-timed count on >= 90% of 100 labelled touches (proposal); guard distance from tracking (m). | New column touches.closely_guarded_hold_s (s). | 3 |
| new-ST-1 | Should | A.04.15 Three seconds in the lane | Store continuous lane time per offensive player (s) and the longest stay per chance, as a measure of post pressure and of 3-second risk. | Lane time recomputes from player positions (lane = \|x\| <= 1.83 m, y <= 5.79 m from the end line) within 0.1 s; every PBP 3-second violation shows a stay >= 3.0 s. | New column chances.max_lane_stay_s and per-player aggregate in profile_snapshots. | 3 |
| new-MB-1 | Should | A.05.05 Goal in the wrong basket | Label own-basket goals as an edge case of made-basket detection, with the team credited and the player who touched it last. | Edge case present in the MB test set; credited team equals PBP on 100% of cases. | made_basket_events.edge_case: add wrong_basket_goal; score_events.event_kind value own_basket. | 3 |
| new-RF-1 | Shall | A.06.06 Blocking vs charging and the restricted area | Every block or charge call stores the defender's feet position relative to the restricted-area arc (inside, on, outside; distance in m), whether he was a secondary defender, his time set before contact (s) and the call. | RA status from tracking with arc distance error <= 0.15 m on 100 labelled calls (proposal); call equals PBP on 100% of PBP-coded charges. | fouls.foul_subtype add blocking; new columns fouls.defender_ra_dist_m (m), fouls.secondary_defender (bool), fouls.defender_set_time_s (s). | 1 |
| new-RF-2 | Should | A.06.08 Multiple, false double and false multiple fouls | Foul subtype vocabulary includes multiple, false double and false multiple fouls, linked to their free-throw sequences. | Subtype present on every such foul; free-throw attempts per sequence equal the award table on 100% of cases. | fouls.foul_subtype add multiple, false_double, false_multiple. | 3 |
| new-RF-3 | Shall | A.06.11 'Intentional' foul label vs the rules book | Foul types follow the 2026-27 rules book classes; the legacy label `intentional` is kept only as a source mapping: deliberate end-game fouls are stored as common fouls with is_end_game_intentional = true, and away-from-ball clock fouls as flagrant_1. | 0 rows with foul_type = intentional after mapping; the mapping table covers 100% of source foul labels; counts per class equal the box score. | fouls.foul_type enum: drop `intentional` (keep in a source-label map in config/vocabulary_map.yaml); keep is_end_game_intentional. | 1 |
| new-RF-4 | Should | A.06.14 Administrative technical | fouls rows distinguish administrative technicals with the 10-2 article that applied. | foul_subtype = administrative_technical with a 10-2 article on 100% of such fouls; FT count equals the award table. | fouls.foul_subtype add administrative_technical; new column fouls.rule_article. | 3 |
| new-RF-5 | Shall | A.06.17 Foul contact mechanism (signal type) | Every foul stores its contact mechanism from the Appendix VIII foul-signal list (holding, pushing, hand-check, illegal use of hands, blocking, player/team control, tripping, hit to head, excessive contact, chucking, pinning a defender, dislodging with knee or lower body, vertical-cylinder violation, landing space, illegal screen), from the official's signal or video, with source. | Mechanism present (or `unseen`) on 100% of fouls; agrees with labelled gold on >= 80% of 300 fouls (proposal). | New column fouls.contact_type (enum from App. VIII); official_positions.signal_pose enum extended to App. VIII. | 1 |
| new-RF-6 | Should | A.06.21 Fighting and suspensions | Record fighting incidents and the suspensions that follow (player, games suspended, games served) in the player availability log. | Every PBP or public fighting report has a row; availability.status = out with reason `suspension` for each suspended game. | availability.status add `suspended`; events.event_family value `fight`. | 3 |
| new-RF-7 | Should | A.06.22 Flopping (faking being fouled) | Record flopping warnings and technicals, and label suspected flops on review (player, time, contact seen yes/no). | All PBP-logged flop technicals present; suspected flops reviewed with kappa >= 0.6 between labellers (proposal). | fouls.foul_subtype add flop_technical; new event family `flop_warning`. | 3 |
| new-EV-2 | Should | A.08.06 Throw-in violations | Throw-in violations stored by article (5-second, spot, stepping on court, carrying onto court, defender breaking the plane) with the team and time. | Article present on 100% of PBP throw-in violations; defender plane breaks seen on video stored with the defender ID. | turnovers.turnover_type add throw_in_violation; restarts.violation_code uses 9-4 article strings. | 3 |
| new-EV-3 | Shall | A.08.07 Backcourt violation (over and back) | Turnover vocabulary includes the backcourt (over-and-back) violation, separate from the 10-second violation, linked to the frontcourt status that preceded it. | Backcourt turnovers equal PBP counts on 100% of games; each has a frontcourt_established time before it. | turnovers.turnover_type add backcourt_over_and_back. | 2 |
| new-EV-4 | Should | A.08.11 Excessive swinging of elbows | Turnover vocabulary includes the elbows violation. | Elbow violations equal PBP counts on 100% of games. | turnovers.turnover_type add elbows. | 3 |
| new-BL-1 | Shall | A.09.02 Player who caused the ball out of bounds | Every out-of-bounds event stores the last player to touch the ball (or the player who was out of bounds), the touch frame and the team awarded the ball, with the call on the floor. | Team awarded equals PBP on 100%; last toucher correct on >= 90% of 200 labelled out-of-bounds plays (proposal). | New columns on ball_states (out_of_bounds_event rows) or a new `out_of_bounds_events` table: last_touch_player_id, last_touch_frame, awarded_team_id. | 2 |
| new-CC-1 | Should | A.09.06 Bench personnel assisting a player out of bounds | Bench events include bench personnel physically assisting a player near the boundary, linked to any resulting technical. | Every such technical in PBP has a bench_events row. | bench_events.event_type add bench_assist_out_of_bounds. | 3 |
| new-RF-8 | Should | A.12.03 Rotations of the crew | Detect each officials' rotation and post-foul switch as an event (time, officials involved, from and to roles). | >= 85% of rotations found within +/- 1.0 s on 100 labelled rotations (proposal). | New event family `official_rotation` in events, from official_positions role changes. | 3 |
| new-RF-9 | Should | A.12.04 Calling official, primary coverage area and whistle distance | Each call stores the calling official's distance to the contact point (m), his angle to the play (degrees) and whether the play was in his primary coverage area by the crew's positions. | Distance from tracking within 0.5 m of gold on 100 calls; primary-area flag agrees with a referee-expert label on >= 80% (proposal). | New columns fouls.official_dist_m (m), fouls.official_angle_deg (degrees), fouls.in_primary_area (bool). | 3 |
| new-RF-10 | Should | A.12.05 Signals (Appendix VIII full list) | Signal vocabulary covers every Appendix VIII signal (start/stop clock, timeouts, every violation and foul signal, shot-clock reset, no score, tipped ball, counts, 3-point attempt and success, free-throw counts, replay, challenge, flopping). | Every App. VIII signal has a code; signal recognition >= 80% on 300 labelled signals (as R-RF-04); unseen signals coded `unseen`. | official_positions.signal_pose enum := App. VIII list (config/vocabulary_map.yaml section `signals`). | 2 |
| new-RF-11 | Should | A.12.07 Visible counts (5 s, 10 s, throw-in) | Record the start of each official's visible count (throw-in, closely guarded, backcourt) from the signal or from the rule trigger, so counts can be compared with our own clocks. | Count start within +/- 0.3 s of a hand label on >= 80% of 100 labelled counts (proposal). | New column official_positions.count_active (enum none, five, ten). | 3 |
| new-CG-1 | Shall | B.01.02 Boundary lines and the out-of-bounds plane | Court config holds every line width and mark of Rule 1 with its citation: boundary lines 0.0508 m, centre circle radius 1.83 m, lane space marks and neutral zones, coaching box, backboard face 1.22 m from the end line, backboard 1.83 m x 1.07 m, ring inner diameter 0.4572 m, 28-ft throw-in marks (8.53 m), designated-spot width 0.91 m. | Each constant present with a rule citation and `verified: true`; geometry unit tests reproduce each mark within 0.01 m. | Add keys to config/court_ncaa_men.yaml (line_width_m, centre_circle_radius_m, lane_space_marks_m, backboard_face_from_end_line_m, backboard_width_m, backboard_height_m, ring_inner_diameter_m, throw_in_mark_from_end_line_m, coaching_box_m). | 1 |
| new-CC-2 | Should | B.01.08 Coaching box | Measure head-coach position relative to the coaching box when visible (inside, outside, distance in m) as part of sideline behaviour. | Box geometry in config; position flag agrees with labels on >= 80% of 100 visible clips (proposal). | bench_events: new columns x_m, y_m, in_coaching_box; config key coaching_box_m. | 3 |
| new-MD-1 | Shall | B.01.13 Undefined spots (short corner, one pass away) | Short corner, one pass away, help side, two-side, tag and the remaining coaching terms get measured definitions in the vocabulary map (short corner provisional r 4.0-5.5 m, theta <= 15 degrees), before P3. | Every term used in a template or taxonomy resolves to an entry with numbers in m and degrees; 0 entries still say 'to be defined'. | config/vocabulary_map.yaml: add the definitions; geometry.spot() returns short_corner. | 2 |
| new-FD-4 | Should | B.02.02 Game ball model per game | Game registry records the game-ball manufacturer and model where public. | Field filled or 'not public' for 100% of games. | New column games.ball_model. | 3 |
| new-FD-5 | Shall | B.02.07 Team benches and scorers' table side | Game registry stores each team's bench side and the scorers' table side relative to the main camera (near or far sideline, left or right end). | Filled for 100% of processed games before tracking; bench-side detections agree with it on >= 99% of frames. | New columns games.home_bench_end, games.table_sideline (near/far), venues.table_sideline_default. | 2 |
| new-ID-1 | Should | B.02.10 Player equipment (goggles, masks, braces) | Appearance card records protective equipment (face mask, goggles, knee brace, ankle brace) as re-identification cues; no health inference is drawn from it. | Field present on every card; used only as an ID tie-breaker (ablation per R-ID-13). | New column appearance_cards.protective_equipment. | 3 |
| new-CX-1 | Should | B.02.12 Rim type and stiffness | Arena registry stores the rim type where known, for shooting-by-arena tests. | Field filled or 'unknown' for every venue. | New column venues.rim_type. | 3 |
| new-VI-1 | Should | B.03.04 Other fixed camera positions | Camera registry lists each arena's secondary camera positions (reverse angle, baseline, under-basket, high end-zone, rail, skycam) with approximate court position in m, so non-main frames can be mapped later. | Registry row per camera seen; positions within 2 m of a hand estimate (proposal). | New table `arena_cameras` (venue_id, camera_kind, x_m, y_m, z_m, seen_first_game). | 3 |
| new-CX-2 | Should | B.04.04 Student-section location | Arena registry stores the student-section end(s) and the opposing-fan section, per game when it changes. | Filled for every venue processed; used by end-of-floor shooting tests (C48). | New column venues.student_section_end (+ games override). | 3 |
| new-CX-3 | Should | B.04.05 Court placement (dome midfield / corner, standard arena) | Venue rows state whether the court is in a standard arena, a dome at midfield or a dome in a corner, and the seat distance behind each basket (m). | Field filled for every NCAA-tournament venue; distance within 5 m of published plans. | New columns venues.court_placement (enum), venues.backdrop_distance_m. | 3 |
| new-PC-6 | Should | C.01.14 NIL valuation (public estimates) | NIL valuations, if kept, are public estimates only, tagged with source, date and kind (estimate vs reported), never used as a model input until a hypothesis registers them. | Every NIL value carries source, date and kind; 0 model feature registries list NIL without a registered hypothesis. | None (columns exist on the card); add a CX-01 registry entry `exploratory`. | 3 |
| new-PC-7 | Should | C.01.17 Captain | Captain designation stored per player-season with source. | Filled or 'unknown' for every rostered player. | None (player_card.captain_flag exists); add to R-PC-01 identity block. | 3 |
| new-CC-3 | Should | C.02.03 Bench personnel list per game | Per game, store the bench personnel roles present (head coach, assistants, trainers, managers) as counts, for technical attribution and bench filtering; no names beyond public staff lists. | Count per role per game filled from the box score or broadcast where available; 'unknown' otherwise. | New table `bench_personnel` (game_id, team_id, role, count, source). | 3 |
| new-RF-12 | Should | C.03.03 Official experience and assignment level | Official cards hold games worked per season, conferences worked and postseason assignments as of each game date, from PBP across D-I. | Recomputes from PBP officials lists; no data after the game date used. | profile_snapshots metric codes `ref_games_season`, `ref_conferences`, `ref_postseason`. | 3 |
| new-DQ-1 | Shall | C.04.04 Home stat crew bias | The known-bias register is a table with one row per bias (description, affected field, direction, correction or flag, evidence source), and every affected field carries the flag. | Register has >= 4 rows (listed heights, home assists/blocks/steals, shot-location entry, substitution timing); 100% of affected columns reference a register row. | New table `bias_register` (bias_id, field, direction, correction, evidence); dq_reports.check values reference it. | 2 |
| new-CX-4 | Should | C.05.03 Crowd allegiance share (neutral sites) | Estimate each team's crowd share at neutral sites from distance, enrollment and travelling-support history, with an interval. | Estimate with 80% interval for every neutral-site game; validated against audio asymmetry where audio exists (C69). | New column team_game_context.crowd_share_est (0-1). | 3 |
| new-MD-2 | Should | D.01.03 Lead changes and ties | Score state also counts ties (times tied) and the largest lead per team as of each second. | Recomputes from score_events; final values equal team_box.largest_lead and the PBP 'times tied' where published. | New columns state_second.times_tied, state_second.largest_lead_msu, largest_lead_opp. | 3 |
| new-EV-5 | Shall | D.01.05 Run events (start, end, size) | Run events stored with start time, end time, points for and against and the event that ended them, under the register definition (net >= 8 in a rolling 120 s) and a strict variant (unanswered >= 8-0). | Runs recompute identically from score_events; every run has an ending cause (timeout, score, period end); counts per game reported. | New table `runs` (game_id, run_id, team_id, start_ts, end_ts, pts_for, pts_against, definition_code, ended_by_event_id). | 2 |
| new-MD-3 | Should | D.01.06 Scoring droughts | Seconds since each team's last field goal and last point, every second of game clock. | Recomputes from score_events within 0.1 s; resets correctly at period start (flagged as carried). | New columns state_second.secs_since_fg_msu/opp, secs_since_point_msu/opp (s). | 3 |
| new-MD-4 | Should | D.02.04 Garbage time | Garbage-time flag per possession under named definitions (source flag; our win-probability rule: pre-possession WP > 0.98 or < 0.02 with <= 300 s left; CTG-like margin-time rule), stored side by side. | All definitions present on every possession; share of garbage-time possessions per definition reported per game. | New column possessions.garbage_time_flags (map definition -> bool). | 3 |
| new-MD-5 | Should | D.07.04 Lineup composition (size, positions, shooting) | Lineup composition features per stint: mean and max listed height (cm), count of players by listed position, count of players with >= 33% 3P on >= 50 attempts as of date, number of primary ball handlers; for both teams and their differences. | Recomputes from rosters and as-of profiles; no data after the game date used. | New columns on lineup_stints: mean_height_cm, max_height_cm, n_bigs, n_shooters_asof, height_diff_cm. | 2 |
| new-ST-2 | Shall | E.01.02 Defensive slide, backpedal and crossover run | Movement primitives include defensive slide (velocity within 45 degrees of the torso's lateral axis), backpedal (velocity within 45 degrees opposite to torso facing) and crossover run, each with speed (m/s) and duration (s). | F1 >= 0.80 per primitive on >= 50 labelled instances (proposal); torso facing error <= 20 degrees median (R-DT-10). | movement_primitives.primitive_type add slide, backpedal, crossover_run; uses player_positions.torso_facing_deg. | 2 |
| new-PL-1 | Should | E.01.03 Jumps (takeoff, height, purpose) | Jump events per player: takeoff and landing frames, takeoff foot (one/two), purpose (shot, rebound, block, contest, tip, other) and jump height (m) once 3D works; counts per minute. | Jump detection recall >= 90% on 200 labelled jumps (proposal); jump height error <= 0.10 m on hand-measured jumps once R-CG-11 passes. | New table `jumps` (game_id, player_id, takeoff_ts_ms, landing_ts_ms, takeoff_foot, purpose, height_m). | 2 |
| new-DT-1 | Should | E.01.04 Stops, pivots, first step and plant foot | Footwork events (R-DT-16) are stored in a table with the pivot foot, stop type and first-step direction (degrees relative to the basket), linked to the touch. | Precision >= 80% on 200 labelled events (as R-DT-16); pivot foot correct >= 85% (proposal). | New table `footwork_events` (game_id, player_id, touch_id, ts_ms, kind, foot, direction_deg). | 3 |
| new-DT-2 | Should | E.01.05 Gather and pre-dribble / split-step travel cues | Record the foot sequence from catch to first dribble (gather, pivot lifted before release?) so travel calls and non-calls can be counted. | Foot-sequence labels agree with gold on >= 80% of 200 labelled starts (proposal); flagged only, never called by us. | Column footwork_events.pre_dribble_violation_suspected (bool). | 3 |
| new-PL-2 | Should | E.01.06 Change of direction | Change-of-direction events: heading change >= 45 degrees within 0.5 s at entry speed >= 3.0 m/s, with exit speed and time to regain 90% of entry speed (s). | Recomputes from smoothed tracks; count per minute reported with coverage (R-PL-05). | New table or accel_efforts kind = cod (heading_change_deg, entry_speed_mps, exit_speed_mps, recovery_s). | 3 |
| new-DF-1 | Should | E.01.08 Landing space of jump shooters | For every jump shot, the closest defender's distance to the shooter's landing point (m) at landing, and a flag when < 0.5 m. | Distance recomputes from tracks; landing point within 0.3 m of gold on 100 shots (proposal). | New columns shots.landing_def_dist_m (m), shots.landing_space_flag. | 3 |
| new-EV-6 | Should | E.02.04 Other dribble moves (in-and-out, push/speed, pound, snatch-back, half spin) | Dribble-move vocabulary adds in-and-out, push (speed) dribble, pound/control dribble, snatch-back and half spin. | >= 75% correct on 300 labelled moves including the new classes (as R-EV-05). | dribbles.move_type add in_and_out, push, pound, snatch_back, half_spin. | 3 |
| new-EV-7 | Shall | E.02.06 Fakes (shot fake, pass fake, jab step) | Fake events: shot fake (ball raised >= 0.3 m toward shooting pocket without release), pass fake and jab step (lead foot moves >= 0.3 m and returns within 0.6 s), each with the on-ball defender's reaction (left feet / lifted / no reaction) and the value change after. | Recall >= 80% and precision >= 80% on 200 labelled fakes (proposal); defender reaction correct >= 80%. | New event family `fake` in events; new table `fakes` (game_id, fake_id, touch_id, kind, ts_ms, defender_id, defender_reaction, value_delta). | 2 |
| new-EV-8 | Should | E.03.06 Pass delivery (one/two hands, off the dribble, no-look) | Pass delivery attributes: one- or two-handed, off the dribble vs from a hold, no-look (head yaw > 45 degrees from the pass direction at release). | >= 80% correct on 300 labelled passes where the passer is >= the readable size (R-ID-05). | New columns passes.hands (one/two), passes.off_dribble (bool), passes.no_look (bool). | 3 |
| new-EV-9 | Shall | E.03.07 Throw-in passes | Every throw-in pass is a passes row flagged is_throw_in, linked to its restart, so inbound passing and pressure are measured like other passes. | 100% of throw-ins with a visible release have a passes row with is_throw_in = true. | New columns passes.is_throw_in (bool), passes.restart_id. | 2 |
| new-EV-10 | Should | E.04.02 Layup and finish subtypes | Finish subtype per layup or dunk: reverse, Euro step, finger roll, scoop, up-and-under, power (two-foot), off one foot, with the finishing hand. | >= 75% correct on 300 labelled finishes (proposal). | New column shots.finish_subtype (enum). | 3 |
| new-EV-11 | Shall | E.04.05 Contest form (hand up, high/low hand, contest height) | Each shot stores the contest form from pose: hand up (yes/no), contest hand height relative to the release point (m), hand-to-ball distance at release (m), and whether the defender left his feet. | Hand-up label correct >= 85% on 300 labelled shots; hand-to-ball distance within 0.3 m where both are visible (proposal). | New columns shots.contest_hand_up, shots.contest_hand_height_m, shots.hand_to_ball_m, shots.contest_airborne. | 1 |
| new-EV-12 | Should | E.04.12 Shooter's footwork into the shot | Jump-shot footwork per shot: 1-2 step, hop, turnaround, fade, spin, sidestep, step-back (already a type), from pose. | >= 75% correct on 300 labelled jumpers (proposal). | New column shots.footwork (enum). | 3 |
| new-EV-13 | Should | E.05.05 Rebound positioning at the release | At every missed-shot release, store each player's distance to the rim (m) and whether he holds inside position on his nearest opponent; and at the rebound, the ball's landing distance (m) and angle (degrees). | Recomputes from configuration snapshots at trigger = shot_release; rebound landing point within 0.5 m on 100 labelled misses (proposal). | rebounds: new columns landing_r_m, landing_theta_deg; configuration_snapshots trigger shot_release used. | 2 |
| new-ST-3 | Shall | E.07.02 Named cuts (UCLA, Iverson, zipper, flash, V-cut, L-cut, shuffle, rip, Euro) | Movement-primitive cut vocabulary equals the OFF.F8.2 cut list (UCLA, Iverson, zipper, flash, V-cut, L-cut, shuffle, rip, Euro, dive, back cut) with one geometric signature each (m, degrees, s, m/s). | Every OFF.F8.2 cut has a primitive code and signature; F1 >= 0.80 per cut on >= 50 labelled instances (proposal). | movement_primitives.primitive_type enum := OFF.F8.2 cut codes. | 2 |
| new-DF-2 | Should | E.09.06 Off-ball denial posture | Per defender-second, a denial flag: defender within 1.5 m of his man, inside the passer-receiver line by >= 0.3 m, with torso facing the ball side. | Agrees with labels on >= 80% of 300 labelled defender-seconds (proposal). | New column defensive_matchups.deny_posture (bool). | 3 |
| new-CC-4 | Should | E.11.03 Player gestures toward officials and opponents (taunting, celebration) | Log player gestures seen on broadcast (complaint to an official, taunt, celebration) with player, time and any technical that follows. | Every PBP technical has a linked gesture row or 'unseen'; labels agree >= 80% on 100 clips (proposal). | bench_events.actor_type add on_court_player (rename the table's scope to `conduct_events` later). | 3 |
| new-ST-4 | Should | F.04.01 System label per possession and per game | For continuity and rule-based systems, store the system label per chance and the number of completed pattern cycles (a cycle = the template's action sequence repeated after a reversal), plus each team's system share per game. | System label agrees with Aldemir's labels on >= 80% of 100 chances (proposal); cycle counts recompute from the action sequence. | New columns set_instances.system_code, set_instances.cycles_completed. | 3 |
| new-ST-5 | Shall | F.05.02 Screener pre-action (how the screener arrives) | Every ball screen stores the screener's arrival (OFF.F5.3 code: walk-up, sprint, flip, re-screen, Ram/after receiving a screen, from the corner, from the dunker spot) with arrival speed (m/s). | Arrival code present on 100% of ball screens; >= 80% correct on 200 labelled screens (proposal). | New columns screens.screener_arrival_code (OFF.F5.3), screens.screener_arrival_speed_mps. | 2 |
| new-ST-6 | Should | F.05.04 Off-ball spacing tags during the PnR | Each ball screen stores the spacing tags of the three off-ball attackers (OFF.F5.6 codes) from the configuration snapshot at the screen moment. | Tags recompute from the snapshot; >= 80% agreement with labels (proposal). | New column screens.spacing_tags (list of OFF.F5.6 codes). | 3 |
| new-ST-7 | Should | F.09.02 Drive-and-kick and paint touches | Count paint touches per chance (ball inside the lane, \|x\| <= 1.83 m and y <= 5.79 m from the end line, by catch or dribble) and the time of the first one, for half-court as well as transition. | Recomputes from ball_states; first paint touch within +/- 0.2 s of gold (proposal). | New columns chances.paint_touches, chances.first_paint_touch_s. | 2 |
| new-ST-8 | Should | F.13.09 Ball movement (passes per chance, reversals, side changes) | Per chance, store passes before the shot, ball reversals (ball x changes sign with \|x\| >= 3.0 m on both sides within one chance) and the time from first frontcourt catch to shot, for half-court offence as well as press break. | Counts recompute from passes and ball_states; reversal count agrees with labels on >= 90% of 200 chances (proposal). | New columns chances.n_passes, chances.n_reversals, chances.frontcourt_to_shot_s. | 2 |
| new-DF-3 | Shall | G.01.04 Pick-up point | Per possession, the pick-up point: the ball-handler's distance from his attacked rim (m) when an on-ball defender first stays within 1.83 m of him for >= 1.0 s, and the pick-up class (full, three-quarter, half court, top of key). | Recomputes from tracks; class agrees with labels on >= 85% of 200 possessions (proposal). | New columns possessions.pickup_dist_m (m), possessions.pickup_class. | 2 |
| new-DF-4 | Should | G.03.03 Lob protection | When the post is fronted, store whether a weak-side defender is within 2.0 m of the rim line to protect the lob, and the outcome of lob attempts. | Flag recomputes from tracks; lob outcomes equal shot/turnover records. | New column post_touches.lob_help_present (bool). | 3 |
| new-DF-5 | Should | G.09.03 Foul-trouble effect on defensive aggressiveness | For each player-stint, compare on-ball distance (m), contest distance (m) and help frequency with and without foul trouble, within player. | Estimate with 95% interval per player with >= 30 possessions in each state (else descriptive). | profile_snapshots metric codes `def_aggr_foul_trouble_delta_*`. | 3 |
| new-OS-1 | Should | H.02.04 Bench points and starter/bench split | Team profiles include bench points, bench minutes share and starters' minutes share per game and as of date. | Recomputes from player_box; equals published box-score bench points where given. | profile_snapshots metric codes bench_points, bench_minutes_share. | 3 |
| new-VL-1 | Shall | H.03.05 Shot-making (points above shot quality) | Shot-making per shooter: actual points minus shot-quality expected points per attempt, shrunk toward the position-group prior, with n and 95% interval, as of each game date. | Interval on every value; shooters with < 50 attempts reported as shrunk-only; out-of-sample correlation of shot-making between season halves reported. | profile_snapshots metric code shot_making_pts_per_fga. | 2 |
| new-VL-2 | Shall | H.04.06 Defensive value per player (stops, contests, deterrence) | Defensive value credits per player: on-ball defender and help defender credited with the possession-value change they cause (contest, rotation, deflection, rim deterrence = shots not taken within 2.0 m when he is the rim protector), summed per 100 defensive possessions with interval. | Credits sum to the chance's value change on defence (bookkeeping test); interval on every player value; n >= 100 possessions to rank. | value_credits.credit_role add contest, rotation, deterrence; profile_snapshots metric def_value_per100. | 2 |
| new-PL-3 | Should | I.02.07 Direction-weighted load (lateral and backward running) | Store time and distance per stint split by movement direction relative to torso facing (forward, lateral, backward, in 45-degree sectors) alongside the speed bins. | Direction split recomputes from player_positions torso_facing_deg; reported only where pose coverage >= 70% of the stint. | New columns load_stint_bins.dir_sector (forward/lateral/backward) or a sibling table `load_direction_bins`. | 3 |
| new-PL-4 | Should | I.02.08 Contact load (screens set and absorbed, box-outs, post contact) | Per player-game, count contact events (screens set, screens absorbed, box-out contacts, post contacts, charges taken) per minute played. | Counts recompute from screens, box_outs, post_touches and defensive_events; reported with coverage. | profile_snapshots metric contact_events_per_min. | 3 |
| new-CX-5 | Should | J.01.04 Road-trip structure | Each team-game carries its road-trip index (1st, 2nd, ... game away without returning home) and the days since leaving campus. | Recomputes from the schedule and venues; 100% of games filled. | New columns team_game_context.road_trip_index, days_since_left_home. | 3 |
| new-CX-6 | Should | J.01.05 Tip time on each team's body clock | Each team-game stores tip time on the team's home body clock (h, from campus time zone) and days since the last time-zone shift. | Recomputes from UTC tip and campus tz with zoneinfo; 100% filled. | New columns team_game_context.tip_body_clock_h, days_since_tz_shift. | 3 |
| new-CX-7 | Should | J.03.03 Opponent recent form | Each team-game carries the previous game's result, margin vs spread, overtime flag and current win/loss streak, as of tip. | Recomputes from games; no post-tip data (leakage test passes). | New columns team_game_context.prev_margin, prev_ats_residual, prev_overtime, streak. | 3 |
| new-CX-8 | Should | J.04.03 Season phase and game number | Each team-game carries its game number in the season and in conference play. | Recomputes from the schedule; 100% filled. | New columns team_game_context.game_num_season, game_num_conf. | 3 |
| new-MK-19 | Should | J.05.06 Public betting share | Public betting share (tickets and money, where a free public source exists) stored per market snapshot with source, used only in the market-input model variant. | Source logged in the source register before collection; 0 values in the market-free variant. | New columns market_snapshots.public_ticket_share, public_money_share. | 3 |
| new-CH-1 | Should | K.01.11 Icing the free-throw shooter | Link every timeout called between a foul and the first free throw of its sequence to that sequence (icing flag, caller team). | Flag recomputes from timeouts and free_throws ordering; 100% of such timeouts flagged. | New column free_throws.preceded_by_timeout_id. | 3 |
| new-VI-2 | Should | L.02.02 Finer camera views (reverse angle, baseline, under-basket, skycam, iso) | Camera-view sub-class for non-main frames (reverse angle, baseline/under-basket, high end, skycam, rail, handheld iso, bench, crowd), as a second label beside the 9 shot types. | >= 90% correct on 500 labelled non-main frames (proposal); the 9-class label is unchanged. | New column frames.camera_view (enum); config vocabulary `camera_views`. | 3 |
| new-VI-3 | Should | L.02.07 Broadcast replays as secondary evidence | Replay segments are linked to the live event they replay (time offset, event_id) so a reviewer or a labeller can use them as evidence; no event, position or count is ever created from a replay frame. | >= 90% of replay segments linked to an event on 3 games (proposal); 0 events with from_replay_frame = true counted in any statistic. | New columns frames.replay_of_event_id, frames.replay_offset_s. | 3 |
| new-AU-1 | Should | L.03.04 Stat graphics and lower thirds as weak labels | Read broadcast stat graphics (player fouls, team fouls, timeouts left, player stat lines) as weak labels with time and confidence, never as truth, and compare them with the state record. | Graphic text read with >= 95% character accuracy on 200 labelled graphics (proposal); every disagreement with the state record logged. | New table `broadcast_graphics` (video_id, start_ts_ms, end_ts_ms, kind, text, parsed_json, conf). | 3 |
| new-AU-2 | Should | L.04.02 Buzzers and horns | Detect horns and buzzers from audio with kind (period end, shot clock, substitution/timeout horn) and time, linked to the clock state. | Recall >= 90% and timing within +/- 0.1 s on 200 labelled horns (proposal). | New table `horns` (video_id, ts_ms, kind, linked_event_id) or audio_seconds.buzzer_kind. | 3 |
| new-DS-2 | Shall | M.01.06 Source definition register (each source's own definitions) | For every source field we ingest that encodes a definition (possession, chance, assist, block, transition/fast break, shot zone, garbage time, minutes), the source's own definition text, URL and date are stored and linked to the column that carries it. | 100% of source-derived definitional columns link to a definition row; definitions re-checked each season (R-DS-01). | New table `source_definitions` (source, field, definition_text, url, checked_on) referenced by docs/data/source_field_map.md. | 2 |
| new-CD-1 | Shall | M.03.09 Ontology coverage check | config/game_ontology.yaml is kept in step with the live requirements and schema: a check script fails when a leaf cites an unknown requirement ID or column, or when a requirement or table is referenced by no leaf. | Script exits 0 on the current repo; run in repository tests (R-EN-08); the coverage statistics in docs/data/game_ontology_coverage.md are regenerated by it. | New script scripts/check_ontology.py; config/game_ontology.yaml (proposal written 2026-10-18). | 2 |
| new-HR-1 | Shall | M.04.06 External consultant (JEV) log | JEV consultations (J1-J9) are logged in a private table outside the pipeline's read path (question ID, items sent, options shown, JEV answer, model version), and an automated test proves no pipeline module reads it. | Log row per consultation with exact model version; import-graph test shows 0 pipeline reads of the JEV log. | New private table `jev_log` (not in schema/tables read path); test in tests/. | 3 |

### Gaps closed by proposals already in the repo

| Leaf | Existing proposal or cross-reference | Note |
| --- | --- | --- |
| A.01.07 Forfeit and no contest | new-IV-30 | Invariant exists only as a proposal; games.status has no forfeit / no_contest values. |
| A.02.04 Minimum time off on a touch (0.3 s) and tap-only rule | new-IV-22 | Proposed invariant; needs adoption in the live doc. |
| A.04.14 Closely guarded 5-second count | new-IV-15 | Invariant proposed; still needs a per-touch count column. |
| A.04.15 Three seconds in the lane | new-IV-17 | Invariant proposed. |
| A.05.04 Illegal assistance in scoring or blocking | new-IV-24 |  |
| A.06.20 Ejection | new-IV-11 | Ejection combinations proposed; no requirement names an ejection record with cause. |
| A.07.08 Substitutions around free throws | new-IV-25 |  |
| A.10.04 Timeouts not granted | new-IV-28 |  |
| A.11.03 Late-game substitution restriction | new-IV-26 |  |
| A.11.04 Disqualified-player replacement (20 s) | new-IV-11 | Constant disqualified_replace_s exists; no measured replacement time column. |
| B.01.03 Centre circle | (see B.01.02 proposal) | Covered by the court-constants proposal under B.01.02. |
| B.01.05 Free-throw lane, line and lane spaces | (see B.01.02 proposal) |  |
| B.01.09 28-ft throw-in marks and designated spots | (see B.01.02 proposal) |  |
| B.01.10 Backboard and basket geometry | (see B.01.02 proposal) |  |
| B.01.16 Court constants verification status | (Aldemir sign-off) | Live doc says every constant matches the 2026-27 book; the file still needs `verified: true` and rule citations (R-CG-01 fails today). |
| C.04.01 Official scorer and the scorebook authority | new-IV-33 |  |
| E.06.04 Illegal (moving) screens | (see A.06.17 contact-type proposal) | Illegal screen becomes a contact type; also add screens.illegal_called (bool) linking to the foul. |
| E.08.04 Post dislodging and hook-and-hold | (see A.06.17 contact-type proposal) |  |
| I.02.06 Jump load (count and height per minute) | (see E.01.03 jumps proposal) |  |
| J.06.01 Beliefs register and hypothesis candidates | (Aldemir: register candidates) | 82 candidates await registration (live doc 'Hypothesis candidates' tab); no new requirement needed. |
| M.03.06 Known-bias register | (see C.04.04 bias-register proposal) |  |

## 7. Reverse index: requirement ID → leaves

| Family | ID → leaves |
| --- | --- |
| R-RR | 01: M.05.01; 02: M.05.01; 03: M.05.02; 04: M.05.01; 05: M.05.02; 06: M.05.01; 07: M.05.01; 08: M.05.01; 09: M.05.01 |
| R-DQ | 01: C.03.01, M.03.04; 02: M.03.01; 03: M.03.01; 04: M.02.02; 05: M.02.01; 06: A.01.06, H.01.01, H.02.01, M.03.03; 07: M.03.03; 08: M.03.05; 09: A.11.06, C.01.05, C.04.01, C.04.04, M.03.06; 10: M.03.07 |
| R-DS | 01: M.01.01; 02: M.01.01; 03: H.04.05; 04: J.03.02, M.01.05; 05: C.01.01, M.02.04; 06: M.01.01; 07: M.01.01; 08: M.01.01; 09: M.01.01; 10: H.04.05, M.01.01; 11: M.01.03; 12: M.01.01; 13: M.01.03, M.01.04; 14: M.01.01; 15: M.01.01 |
| R-RG | 11: M.01.03, M.06.04; 01: M.06.04; 02: M.06.04; 03: M.01.02; 04: M.01.02; 05: M.01.02; 06: C.01.18, M.06.04; 07: M.06.05; 08: M.01.04; 09: M.06.04; 10: L.01.05 |
| R-FD | 01: A.01.06, A.01.09, L.04.06; 02: M.02.04; 03: B.02.08, C.01.02, C.01.03; 04: C.01.05, C.01.10; 05: A.11.01, C.01.18, J.03.01; 06: J.03.02; 07: M.02.05; 08: A.12.01, C.03.01; 09: L.01.03; 10: M.06.02; 11: B.03.01, B.04.01; 12: C.01.11, C.01.12 |
| R-PC | 01: C.01.01, C.01.04, C.01.06; 02: C.01.07, C.01.12; 03: C.01.07; 04: C.01.05, C.01.10; 05: C.01.09, E.01.02, E.01.06, I.02.03; 06: C.01.21; 07: C.01.22; 08: G.08.01; 09: C.01.23; 10: C.01.15, E.02.07; 11: C.01.08, K.02.04; 12: C.01.16; 13: C.01.11; 14: M.02.05; 15: C.01.19; 16: C.01.13 |
| R-MD | 01: A.01.02, A.02.01, D.01.01, D.09.05; 02: A.04.01, D.04.01; 03: A.09.03; 04: A.04.02, A.04.03, D.03.01; 05: A.04.09, D.03.05; 06: A.03.02, A.03.03, A.03.04, A.03.05, A.03.07, A.08.03; 07: A.06.18, A.10.01, D.05.01, D.06.01; 08: A.02.06; 09: D.10.03, M.02.03; 10: B.01.12, B.01.13, M.06.03; 11: L.02.01; 12: A.04.07, B.02.05; 13: A.10.02, D.02.02, D.06.03; 14: A.01.09, B.04.06, J.04.03; 15: D.07.01, D.07.02; 16: A.06.19, D.05.02, D.05.04, G.09.03; 17: D.01.03, D.01.04, D.09.01, H.05.02; 18: J.01.01, J.01.02; 19: D.04.06, D.10.03; 20: L.03.01, L.04.06 |
| R-ID | 01: L.06.06; 02: L.06.06; 03: L.06.06; 04: C.01.03, L.06.06; 05: L.06.06; 06: L.06.07; 07: L.06.07; 08: L.06.06; 09: L.06.06; 10: C.01.19; 11: L.06.08; 12: B.02.09, B.02.10, C.01.20; 13: L.06.07; 14: L.06.08; 15: L.06.09 |
| R-VI | 01: L.01.01; 02: L.01.02; 03: L.02.01, L.02.06; 04: L.02.03, L.02.07; 05: L.02.04; 06: L.02.04; 07: L.02.05, L.03.04; 08: L.04.05; 09: L.01.03; 10: L.06.13; 11: L.03.01; 12: L.01.04; 13: B.03.01; 14: L.01.01; 15: L.01.06; 16: L.01.06 |
| R-CG | 01: B.01.01, B.01.02, B.01.04, B.01.05, B.01.06, B.01.07, B.01.10, B.01.16; 02: B.01.11; 03: B.03.03; 04: L.06.05; 05: B.01.12, B.01.14, B.01.15, E.04.03; 06: A.01.01; 07: D.10.01, E.03.02, E.06.02, F.05.01, F.12.02; 08: B.01.11; 09: B.01.15; 10: B.02.11, B.03.05; 11: B.01.10, D.04.03, E.01.03, E.04.06, I.02.06 |
| R-DT | 01: E.01.07, L.06.01; 02: C.02.03, C.05.04, L.06.01, L.06.14; 03: L.06.02; 04: L.06.03; 05: D.10.02; 06: L.06.04; 07: D.10.02, L.06.04; 08: I.01.01; 09: B.03.02; 10: E.01.03, E.01.07, E.09.01, E.09.08; 11: L.06.03; 12: A.12.02, L.06.14; 13: A.07.03, B.01.05, F.11.05; 14: A.08.06, A.09.04, A.09.05, A.12.07, E.03.07, F.11.02; 15: A.04.05, A.04.06, B.01.03; 16: A.08.01, E.01.04, E.05.03, I.02.08; 17: C.02.04, C.05.04, L.06.01; 18: B.02.08; 19: A.09.03, B.01.09 |
| R-BL | 01: B.02.01, D.04.03, L.06.10; 02: D.04.02, L.06.10; 03: D.04.04; 04: L.06.10; 05: L.06.11; 06: E.02.02; 07: A.08.05, A.09.01, B.01.02; 08: E.04.08 |
| R-GT | 01: M.04.04; 02: M.04.04; 03: M.04.04; 04: M.04.04; 05: L.06.13 |
| R-SY | 01: A.02.01, A.03.01, A.04.07, B.02.03, B.02.04, B.02.05, L.03.02; 02: A.02.06, M.02.06; 03: A.11.01, A.11.02, A.11.06, D.07.01; 04: A.04.02, D.03.04, F.11.02, H.01.01; 05: A.04.03, H.01.02, H.01.03; 06: A.04.02; 07: E.04.03; 08: A.03.03, A.03.06, A.08.03; 09: A.03.03, A.03.04, A.03.06, C.04.03; 10: M.03.04 |
| R-TR | 01: D.03.03; 02: F.01.01; 03: F.01.05; 04: F.01.04; 05: F.01.01; 06: F.01.07; 07: L.06.12; 08: F.01.01; 09: F.01.01; 10: F.01.01; 11: F.01.02, F.13.06, G.10.05, M.01.06; 12: G.07.01, G.07.02; 13: F.01.03, F.02.03, F.02.04; 14: F.01.06; 15: F.01.04; 16: F.01.07, K.01.08; 17: F.01.02; 18: A.01.10, F.01.02; 19: A.10.06, A.13.04; 20: F.01.03, F.02.04, F.09.02; 21: F.01.06; 22: F.01.05; 23: F.01.06; 24: F.01.07, K.01.08; 25: A.06.23; 26: F.01.07; 27: F.01.02, H.02.03; 28: F.01.02 |
| R-EV | 01: M.02.06; 02: E.03.01, E.03.02, E.03.03, E.03.05; 03: E.03.04, E.04.09; 04: E.02.01, E.02.02; 05: E.02.03, E.02.04; 06: E.02.05, E.09.02, F.09.02; 07: A.05.01, E.04.01, E.04.02, E.04.03, E.04.04, E.04.07, E.04.08, E.04.09; 08: E.05.01, E.05.02, E.05.03, E.05.04, F.12.01, G.08.01; 09: A.06.06, E.09.04, E.09.05; 10: A.03.08, A.04.14, A.04.15, A.08.01, A.08.02, A.08.05, A.08.08, A.08.09, A.08.10, H.01.04; 11: A.10.06, A.11.02, C.02.04; 12: M.02.06; 13: D.01.04, D.09.04; 14: A.01.05, A.04.05, F.11.06; 15: A.10.02, A.10.03, E.11.02, F.11.01, K.01.01, K.01.03; 16: A.08.12, A.09.02, A.13.02, K.01.04 |
| R-AU | 04: B.04.07, L.04.03; 01: L.04.04; 02: E.11.02, K.01.01, L.04.04; 03: C.05.02, L.04.03 |
| R-RF | 01: A.12.06, L.04.01; 02: A.12.06, L.04.01; 03: A.06.01, A.06.02, A.06.05, A.06.09, A.06.10, A.06.11, A.06.12, A.06.15, A.06.20, A.07.01; 04: A.06.06, A.06.17, A.12.05; 05: A.12.04; 06: C.03.02, C.03.03, J.02.04; 07: A.04.06, A.13.01 |
| R-ST | 01: E.01.01, E.07.01, E.07.02, E.07.03, E.08.02, E.09.03; 02: E.06.01, E.06.02, F.05.01, F.08.01; 03: F.05.04; 04: E.07.02, E.08.03, F.01.08, F.02.02, F.02.03, F.03.02, F.04.01, F.07.01, F.09.01, F.13.01; 05: D.09.06, F.01.08, F.02.02, F.03.02, F.09.01, F.11.04, F.13.01, F.13.02; 06: F.04.02; 07: D.09.06, F.13.01; 08: F.13.01, H.03.08; 09: F.13.03; 10: F.13.07; 11: F.13.04; 12: F.13.04; 13: F.13.01; 14: F.13.07; 15: F.13.05, M.06.03; 16: M.06.08; 17: E.06.01; 18: E.06.03, F.02.01, F.04.02, F.05.02, F.05.03, F.05.05, F.06.01, F.08.01, F.08.02, F.12.02; 19: F.03.01; 20: G.02.01; 21: F.03.01, F.03.02; 22: F.13.05, M.06.03; 23: A.09.05, F.11.03; 24: F.10.01, F.10.02, F.13.09; 25: F.04.01, F.13.08, F.13.09; 26: E.03.08, G.03.03 |
| R-DF | 01: D.07.05, G.10.01, K.01.06; 02: E.09.06, G.04.01; 03: G.04.02; 04: D.09.05, G.01.01, G.01.03, G.05.01, G.05.03, G.10.06; 05: G.06.01, K.01.07; 06: G.02.01, G.02.02; 07: E.08.01, F.07.01, G.02.03, G.03.01, G.03.02; 08: E.09.03, G.04.04, G.04.05; 09: D.07.05, G.10.02; 10: G.07.01, G.07.02; 11: G.10.03; 12: G.05.02; 13: G.10.07; 14: G.06.02, K.01.10; 15: G.04.03; 16: G.02.01; 17: G.05.01; 18: G.05.02, K.01.10; 19: G.06.01, G.09.01, K.01.07; 20: G.07.01; 21: G.01.02 |
| R-VL | 01: D.09.02, H.03.01; 02: H.03.03, H.04.06; 03: H.03.02; 04: E.04.04, E.04.10, H.03.04, H.03.05; 05: H.03.06, K.02.01; 06: E.07.04, H.04.01; 07: H.04.02, H.04.06; 08: H.03.08; 09: H.03.03; 10: H.03.07; 11: H.01.04, H.03.07; 12: H.03.05, H.04.03; 13: H.03.09 |
| R-CH | 01: H.04.04; 02: H.04.07; 03: H.04.07; 04: H.04.07; 05: G.04.04; 06: F.11.01, K.01.01, K.01.02, K.01.07; 07: K.01.15; 08: D.01.05 |
| R-CC | 01: C.02.01, C.02.02, K.01.14; 02: A.10.03, K.01.03; 03: A.06.15, A.11.05, C.02.05, K.01.09, K.01.13; 04: C.02.05, K.01.13; 05: J.03.04 |
| R-GU | 01: D.03.02, D.09.03, D.09.06, K.02.01; 02: D.09.03, H.06.02; 03: D.09.07; 04: L.05.04; 05: L.06.12; 06: D.09.07 |
| R-SR | 01: A.01.02, A.02.01, A.02.02, A.02.03, A.03.01, A.04.09, B.02.03, D.02.01; 02: A.05.06, D.01.01, D.01.02; 03: A.06.01, A.06.03, A.06.04, A.06.05, A.06.07, A.06.09, A.06.10, A.06.12, A.06.13, A.06.14, A.06.16, A.06.18, D.05.01, D.05.02, D.05.03, D.05.05; 04: A.02.05, A.10.01, A.10.02, A.10.05, A.13.01, A.13.02, A.13.03, A.13.04, D.06.01, D.06.02, D.06.03, D.06.04; 05: A.04.07, D.03.01, D.03.02, D.03.03; 06: A.04.01, D.04.01, D.04.02, D.04.03, D.04.05, D.04.06; 07: A.12.02, D.07.03, I.01.01; 08: A.04.10, A.04.11, A.09.03, B.01.09, D.08.01; 09: A.06.02, A.06.08, A.07.01, A.07.02, A.07.04, A.07.06, A.07.07, D.08.02, E.10.01; 10: B.03.04, L.02.01, L.02.02; 11: A.06.24, D.02.03, D.05.04, F.11.07, F.11.08; 12: D.09.02, H.03.01; 13: D.10.04; 14: M.02.06; 15: D.10.03, L.03.02, M.02.03 |
| R-IV | 01: D.07.01, M.03.02; 02: A.12.01; 03: A.06.19, A.07.08, A.11.02; 04: A.01.06, A.05.02, D.01.02, M.03.02; 05: A.02.02, A.02.03, A.02.05; 06: A.02.03; 07: A.03.02, A.03.03, A.03.04, A.03.05, A.03.07, A.03.09, B.02.04, M.03.02; 08: A.04.06, A.07.06; 09: A.06.18, A.13.05; 10: A.01.05, A.10.01, A.10.05; 11: A.07.03, A.07.05, A.08.13; 12: A.05.01, B.01.06; 13: I.01.03; 14: A.04.12, A.04.13, A.08.07; 15: A.01.06, A.04.04, H.02.01; 16: A.01.02, A.01.05 |
| R-SB | 01: A.02.05, A.05.06, C.04.02, C.04.03, L.03.03, M.03.08; 02: A.05.06, M.03.08; 03: L.03.03; 04: M.03.08 |
| R-MB | 01: B.01.10, L.06.11; 02: L.06.11; 03: L.06.11; 04: A.05.01, L.06.11; 05: A.05.03, A.05.05, A.08.04, A.08.12; 06: A.01.03, A.03.08, B.02.06, E.04.11, L.04.02; 07: A.03.04, D.04.05, E.04.08 |
| R-CX | 01: J.06.03; 02: J.06.03; 03: J.06.03; 04: B.04.02, B.04.06, C.05.01, J.02.01, J.02.02; 05: J.01.02, J.01.03; 06: C.03.02, J.02.04; 07: B.02.08, J.02.05, L.06.02; 08: C.01.18, J.03.01, K.01.12; 09: J.06.02, M.02.05; 10: J.01.06; 11: J.04.01, J.04.02; 12: B.04.03; 13: J.01.01, J.01.05, J.01.07; 14: B.04.06, C.05.03, J.02.01; 15: A.01.09, J.04.01; 16: B.04.01, J.02.03; 17: C.05.03, J.02.02; 18: J.06.02; 19: J.03.04 |
| R-PL | 01: I.02.01; 02: I.02.02; 03: D.07.03, I.02.03, I.03.01, I.03.02; 04: A.01.04, A.10.07, I.03.03; 05: I.02.05; 06: I.03.05; 07: E.04.05, E.04.06; 08: A.07.04, E.10.01, E.10.02; 09: I.02.01; 10: I.01.02; 11: E.01.01, I.02.01; 12: I.02.02; 13: I.03.06; 14: I.02.05; 15: I.02.04; 16: I.03.04; 17: I.03.04 |
| R-CO | 01: E.02.08, E.09.01, K.02.02; 02: E.09.07; 03: E.09.07; 04: H.06.01; 05: K.02.03; 06: K.02.02; 07: I.03.02; 08: E.11.01, G.10.04 |
| R-OS | 01: H.02.02, J.03.03, J.03.05; 02: J.03.05; 03: J.03.05; 04: K.01.06; 05: J.03.05 |
| R-EN | 01: M.06.01; 02: M.05.04; 03: M.03.03; 04: M.02.02; 05: M.05.04; 06: M.06.01; 07: M.05.04; 08: M.06.06 |
| R-CD | 01: M.06.06; 02: M.03.09; 03: M.06.06; 04: M.06.06; 05: M.06.06 |
| R-PR | 01: H.05.01; 02: H.05.01; 03: H.05.08; 04: H.05.08; 05: H.05.05; 06: H.05.03; 07: H.05.04; 08: H.05.08; 09: H.05.08; 10: H.05.08; 11: D.09.01, H.05.02 |
| R-PE | 01: D.03.04; 02: A.04.03, H.01.02; 03: H.05.07; 04: H.05.07; 05: H.05.07; 06: A.11.05, I.03.01, K.01.02, K.01.09; 07: A.06.24, F.11.03, F.11.07, F.11.08, G.09.02, K.01.05; 08: H.05.07; 09: H.05.07; 10: H.05.05; 11: H.05.07; 12: H.05.07; 13: H.05.07 |
| R-MK | 01: J.05.01; 02: J.05.02; 03: J.05.03; 04: J.05.04; 05: H.05.06; 06: H.05.06; 07: M.02.05; 08: J.05.05; 09: H.05.06; 10: J.05.02; 11: M.01.04; 12: M.06.05; 13: M.02.01; 14: J.05.01; 15: J.05.04; 16: J.05.02; 17: J.05.01; 18: M.02.04; 19: M.06.05; 20: M.03.01; 21: M.03.01; 22: M.03.04; 23: M.01.03; 24: M.06.04; 25: J.05.02; 26: J.05.01; 27: J.05.01; 28: J.05.01; 29: J.05.01; 30: J.05.04; 31: M.06.01; 32: J.05.04; 33: J.05.02 |
| R-HR | 01: M.04.01; 02: M.04.01; 03: M.04.01; 04: M.04.01; 05: M.04.02; 06: M.04.02; 07: M.04.03; 08: M.04.01; 09: M.04.01; 10: M.04.02; 11: M.04.01; 12: M.04.03 |
| R-VZ | 01: L.05.01; 02: L.05.02; 03: L.05.02; 04: L.05.01; 05: L.05.03; 06: L.05.03; 07: L.05.03 |
| R-CS | 01: M.05.03; 02: M.05.03; 03: M.05.03; 04: M.05.03; 05: M.05.03; 06: M.05.03; 07: M.05.03; 08: M.05.03; 09: M.05.03; 10: M.05.03 |
| R-VA | 01: M.04.03; 02: B.03.03; 03: M.03.03; 04: M.04.05; 05: M.04.05; 06: M.04.05; 07: M.04.05; 08: M.04.05; 09: M.04.05 |
| R-HY | 01: J.06.01, M.06.07; 02: J.06.01; 03: M.06.07; 04: M.06.07; 05: M.06.07; 06: M.06.07; 07: M.04.06 |
| R-PT | 01: M.06.09 |

## 8. Open questions for Aldemir

- New family R-RL (rules layer) for a versioned rules edition per game: accept, or fold it into R-IV / R-CG?
- Drop `intentional` from the foul types and map it to rulebook classes (common foul + end-game flag, or Flagrant 1)?
- Rule 7-3.2.b boundary for throw-in spots: the 2025-26 change text (FT line extended) or the 2026-27 book text (imaginary line to the end-line corner)? (also open in docs/data/dictionary_state.md item 7)
- Adopt the 34 proposed invariants new-IV-01..34 into the live doc (they close 14 leaves here)?
- Add the missing Rule 1 marks to config/court_ncaa_men.yaml and then mark it `verified: true`?
- Officials' mechanics (rotations, primary coverage areas, calling distance, full signal list): label now or after gate G7?
- Fakes (shot fake, pass fake, jab step) and contest form (hand up, hand-to-ball distance) as Shall, given pose quality at broadcast distance is not yet measured?
- Bench side and scorers'-table side per game: you fill them from the broadcast at intake, or detected automatically?
- Conduct events (flopping, taunting, player gestures) and fighting/suspensions: in scope?
- NIL valuations on the player card: keep as public estimates (exploratory only) or drop?
- Public betting share for the market-input model variant: look for a free source, or out of scope?
- Context extras (ball model, rim type, court placement in domes, student-section end, crowd allegiance share): collect, or leave as Should with 'unknown'?
