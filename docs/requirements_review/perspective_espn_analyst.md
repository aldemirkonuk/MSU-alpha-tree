# Perspective review: ESPN college basketball analyst and stats producer

Date: 2026-10-18. Status: **proposal only.** Nothing here edits the live requirements doc, the repo's existing files or any config; the requirements session decides. Add-only file.

Persona: a senior college basketball studio analyst and broadcast stats producer (game breakdowns, telestrator segments, BPI and matchup predictor, win-probability graphics, on-air stat accuracy, storylines). Two extra seats at the table: **the coach on the bench** (what decision did I just make, and did the numbers see it?) and **the official** (what did I have to rule on, from where, and was the rule applied as written?).

What this perspective cares about, in order:

1. **Credible numbers.** Every number on air reconciles with the official box or carries its definition, n and source. One wrong rebound total costs more trust than ten good insights earn.
2. **Correct vocabulary.** Sets, actions and coverages named the way coaches name them ("Horns flare", "ICE", "hard hedge", "drop", "peel switch"), with one definition per word.
3. **Why a possession worked or failed**, in a sentence a fan and a coach both accept, backed by a clip.
4. **In-game narrative**: runs, foul trouble, timeouts, adjustments after timeouts and at half-time, the late-game decision tree.
5. **Timeliness**: the half-time window (about 15 min, Rule 5-7 intermission, length not checked here) and the post-game window.

Conventions used below: metres, seconds, m/s, m/s², degrees. Rule numbers are from `docs/rules/PRMBB_RulesBook.pdf` (2026-27, August 2026) as quoted in `config/invariants.yaml` or read in the extracted text (`scratchpad/rules.txt`, pdftotext of the same PDF) unless another rules file is named. Numbers tagged **[ANALYST HEURISTIC]** are this persona's working conventions, not sourced; they are proposals to be calibrated. New requirement IDs use the persona letter A: `new-<FAMILY>-A<n>`, numbered after the highest `new-<FAMILY>-n` already proposed in the repo (inbox 007, `docs/data/game_ontology_coverage.md`, `config/invariants.yaml`; checked 2026-10-18: e.g. EV 13, RF 12, SR 5, ST 8, DF 5, MD 5, DQ 1, IV 34, CC 4, CH 1, SY 3, CX 8, VI 3; families with none start at A1).

## Summary

- Verdicts on the 518 live IDs (43 families): **keep 470, tighten 35, loosen 3, rewrite 8, drop 2** (table 4.1).
- New requirements: **28** (`new-*-A*`, section 5).
- The ten most important changes are in section 8; the ten most valuable outputs in section 6; the ten biggest risks in section 7.

---

## 1. THINK: how the game flows under the 2026-27 rules

### 1.1 The possession state machine

A possession, in this project's definition, ends only when the other team gains control; an offensive rebound starts a new chance inside the same possession (brief 003, R-MD-04). Broadcast language mostly agrees, except that a broadcast "possession" graphic usually counts trips, and team rebounds after a missed final free throw are where the counts drift.

States (one per frame; the proposed `flow_state` column in new-SR-A6):

| # | State | Entered by | Left by | Governing rules | Game clock | Shot clock | Running counts |
|---|---|---|---|---|---|---|---|
| S0 | Pre-period / intermission | End of period (5-7), pre-game | Jump ball (game, extra period) or throw-in (2nd half, arrow) | 5-7, 5-9, 6-2.1, 6-3 | stopped | off | intermission timer |
| S1 | Jump ball | Start of game and each extra period | Legal tap → S3/S4 or loose ball S6; violation → S2 | 6-2.1, 6-2.2; violations 9-8 | starts on legal tap (5-10.2.b) | starts on initial control (2-11.5.b) | none |
| S2 | Throw-in pending | Made FG or final FT (other team's ball), violation, OOB, foul before the bonus, held ball by arrow, timeout | Ball legally touched inbounds → S3/S4; 5-s violation → S2 (other team) | 7-3.2.b spots (below FT line extended → nearest spot under the basket; above → 28-ft mark, 8.53 m); 7-6.6, 9-4.1.d (5 s) | stopped, except it keeps running after a made FG, apart from the last 59.9 s of the 2nd half and extra periods (5-11.9, 2-10.12) | starts on inbound touch (2-11.5.a); value from the reset table (2-11.6) | 5-s throw-in count |
| S3 | Live, team control in the backcourt | Inbound catch, defensive rebound, steal | Frontcourt status → S4; turnover/violation → S2; foul → S7/S8; timeout → S9 | 9-10 (10-s backcourt), 9-12 (backcourt violation), 4-9 control | running | running | 10-s count (visible) |
| S4 | Live, team control in the frontcourt | Ball and both feet of the holder in the frontcourt (frontcourt status) | Try released → S5; turnover → S2 or S3 (other team, live); foul → S7/S8; held ball → S2 by arrow | 9-9 (3 s in lane), 9-14 (closely guarded 5 s at 1.83 m), 9-12 | running | running | 3-s per attacker in the lane; 5-s closely guarded while holding |
| S4a | ... analyst phase: primary transition | Secure control after a miss, steal or (fast) inbound | Fewer attackers ahead than defenders back, or defense set | R-TR-08/09 (project definition, not a rule) | running | running | numbers state 10 Hz (R-TR-22) |
| S4b | ... early offense | 3 defenders back, defense not set | defense set (R-TR-08) | project definition | running | running | — |
| S4c | ... half-court | defense set | try, turnover, foul | project definition | running | running | — |
| S5 | Try in flight | Release (the try starts with the shooting motion, 5-1.10) | Make → S7 (dead, scored); miss with ring contact → S6; airball → S6 (no ring) | 5-1, 9-15 (BI/GT) | running | running; a reset value depends on ring contact (2-11.6.d.1 vs no reset for airballs, R-MB-07) | — |
| S6 | Loose ball / rebound | Miss, tip, deflection | Control by one team → S3/S4 (same team after ring contact: shot clock flat 20 s, 2-11.6.d.1; other team: 30 s, 2-11.6.b.4); held ball → S2 by arrow | 4-9, 6-3, 6-4 | running | started again on control (2-11.5.b) | — |
| S7 | Dead ball | Whistle (foul, violation, OOB, held ball, injury, timeout request granted, review), made FG/FT, period end | Throw-in (S2), free throws (S8), timeout (S9), review (S10), period end (S11) | 6-5; substitutions only here (3-6); media timeouts at the first dead ball at or after the marks (5-14.10.c) | stopped (except after a made FG, see S2) | per 2-11.6 (no reset list 2-11.6.a) | — |
| S8 | Free-throw sequence | Foul with award (10-1 Penalty; one-and-one from the 7th team foul, two from the 10th, 8-2.1, 8-2.2) | Last attempt made → S2 (other team); missed and touched by the ring → S6 live; technical/flagrant plus ball → S2 | 8-4 (lane spaces, max 6 players), 8-5.1.a (10 s), 8-6, 8-7; 2-11.6.d.1 also after a missed live FT | stopped (starts when a missed live FT is legally touched, 5-10.2.c) | off until control after the last miss | 10-s FT count |
| S9 | Timeout | Called (30, 60 or 75 s by format), media, injury | Horn → S2/S8 | 5-14.1 (who may request; head coach during live play only in the last 2 min of the 2nd half and extra periods, 5-11.3 and 5-14.1.a exception), 5-14.4 (lengths), 5-14.8–10 (formats) | stopped | stopped (no reset after a timeout, 2-11.6.a.3) | timeout timer, 15-s warning horn (5-14.5) |
| S10 | Review / challenge | Officials' review (11-2, 11-3) or coach's challenge (11-4: out of bounds any time; BI/GT and secondary-defender restricted area until the last 2 min of regulation; needs a legal timeout; success keeps the timeout and earns a second, final challenge) | Ruling → S2/S7/S8 with clocks corrected | 11-2, 11-3, 11-4, 5-14.1.e, 5-15.1.e (no timeouts during a last-2-min review except the challenge) | stopped, may be reset | may be reset | — |
| S11 | End of period | Horn at 0.0 (5-7) | Intermission S0, or extra period of 300 s (5-9, jump ball 6-2.1; team fouls carry, 5-9.4) | 5-7, 5-9 | 0.0 | off | — |

Clock rules that decide flow:

- Game clock never runs in S0, S2 (except after a made FG outside the last 59.9 s), S7–S11. Tenths shown below 60 s (1-18.2); at least 0.3 s runs off on any touch-and-stop in the last 59.9 s (5-10.2.d); a tap is the only legal score with 0.3 s or less (5-1.19).
- Shot clock is turned off when the game clock shows less than a shot-clock period (2-11.2), and comes back at 20 s in the 2-11.6.d cases (2-11.8). The full reset table (33 causes) is in `config/invariants.yaml`; the 20-s flat reset after an offensive rebound off the ring is the one most often wrong on air.
- Team fouls are per half; bonus at the 7th team foul (one-and-one), double bonus at the 10th (8-2.1, 8-2.2); extra periods extend the second half (5-9.4). Foul-out at 5 (4-12.1).

### 1.2 The game state machine (the producer's run-of-show)

| Segment | Rule | What changes for flow | What the stats desk must have ready |
|---|---|---|---|
| Tip | 6-2.1 | First possession; arrow set to the team that lost the tip (6-3) | Starters, tip winner, arrow |
| Under-16, 12, 8, 4 media timeouts (or 15, 10, 5) | 5-14.10.c | First dead ball at or after the mark; a team timeout, review or challenge within 30 s before the mark becomes the media (5-14.10.e); a foul that kills the ball at the mark: timeout first, free throws after (5-14.11) | Segment splits, run status, foul counts, bonus, timeouts left |
| Team fouls 7 and 10 | 8-2.1, 8-2.2 | Bonus, double bonus | Bonus graphic; fouls to give |
| Half-time | 5-7 | Team fouls reset; arrow decides the 2nd-half possession (6-3) | Half-time packet (new-VZ-A1) |
| First team timeout of the 2nd half | 5-14.10.d | Becomes a media timeout | — |
| Last 2:00 of the 2nd half and extra periods | 5-11.3, 5-14.1.a exception, 11-2, 11-4.1.b-c | Head coach may call a live-ball timeout; BI/GT and secondary-defender RA reviewed by officials without a challenge; voluntary immediate reviews | End-game situation flags (R-SR-11 tighten), timeouts by length, challenge state |
| Last 59.9 s | 5-11.9, 2-10.12, 5-10.2.d | Clock stops after a made FG; 0.3-s minimum | Clock-read in tenths; foul-to-extend, foul-up-3 cells |
| Shot clock off | 2-11.2, 2-11.8 | Last-shot holds | Hold flag (R-SR-11) |
| Extra period | 5-9 | 300 s, jump ball, one extra timeout (30 s in the media format, 75 s otherwise; 5-14.10.f, 5-14.8.d) | OT timeouts, carry-over fouls |

### 1.3 Where the flow is decided (decision points)

| Decision point | Who decides | When (s, relative to the trigger) | Options | What the data must capture |
|---|---|---|---|---|
| Push or pull back after a defensive rebound or steal | Ball handler, by team rule | 0–3 s after the secure catch | push, outlet ahead, pull back | Numbers state at the secure moment, decision, value at stake (R-TR-16, R-TR-24, R-TR-26) |
| Inbound fast after a make | Inbounder and coach philosophy (Izzo pushes off makes, transition_full 9.1) | 0–3 s after the ball through the net | quick inbound, set up | Inbound release time, defense not set (R-TR-14, R-TR-21) |
| Press or not | Defensive coach, often after makes or free throws | Pre-planned, signalled at the dead ball | full-court, ¾, half-court trap, none | Press template and set-up time vs inbound lag (R-DF-18) |
| Set call | Offensive coach (signal or verbal) or point guard | Dead ball or crossing half-court | named set, motion, early offense | Set name, first action time (R-ST-05, R-ST-07) |
| Ball-screen coverage | Pre-game plan per screener and location; called by the big | Coverage visible 1 s before to 2 s after the screen moment (defense_full F3.0) | drop, at the level, hedge, blitz, switch, ICE, under | Two-level coverage (R-DF-16), screen moment (R-ST-20) |
| Handler read on the screen | Ball handler | 0–1.5 s after the screen moment | reject, use, split, snake, pull-up, pocket pass, skip | Action and outcome; decision latency (R-CO-01) |
| Help or stay | Help defender | Starts at the drive or the pass, expected 0.5–1.5 s lag (defense_full F11.6, heuristic) | help, stunt, stay, rotate | Reaction delay (R-DF-08, R-CO-02) |
| Double the post | Defensive coach plan, triggered on catch or dribble | 0–1.5 s after the post catch [ANALYST HEURISTIC] | front, ¾, behind, double from top/baseline | R-DF-07 tightened |
| Whistle or play on | Calling official in whose primary area the play is | Contact to whistle typically well under 1 s [ANALYST HEURISTIC, unverified] | foul, violation, no call | Whistle time, contact frame, official role and distance (new-RF-A13, new-RF-9) |
| Block or charge | Calling official; reviewable restricted-area check (11-4.1.c) | At contact | block, charge, no call | Restricted-area position of the secondary defender (new-RF-1) |
| Timeout | Head coach or player of the team in control | At a dead ball; live ball only for players, or the head coach in the last 2 min | 30, 60, 75 s; challenge | Purpose (new-CC-A6), timing vs runs (R-CC-02) |
| Substitution in foul trouble | Head coach | Next dead ball after the 2nd foul in the 1st half | sit, stay | new-CC-A5 |
| Two-for-one, last shot | Coach and handler | 33–45 s left in a half (config, proposal) | quick shot, hold | R-SR-11 flags |
| Foul up 3, foul to extend | Coach | Last 10–60 s (config) | foul, defend | R-PE-07 cells |
| Challenge | Head coach, in the same interaction as the timeout (11-4.1.e) | Before the next live ball | challenge, no challenge | R-EV-16 tightened |

---

## 2. UNDERSTAND: how teams react to actions

Response speeds are in seconds (s) or possessions. "Sourced" values cite the repo document that cites the evidence; everything else is **[ANALYST HEURISTIC]**, a working convention to calibrate on our film. "Detect" names the requirement IDs (existing or new) that must capture both the trigger and the response.

| Trigger | Typical offensive response | Typical defensive response | Bench / official | How fast | Detect |
|---|---|---|---|---|---|
| Made basket (by us) | Opponent: quick inbound to beat the set defense, or walk it up | Get back; press after makes for pressing teams; match up in transition | Clock keeps running except the last 59.9 s (5-11.9) | Inbound release 1–4 s after the ball goes through the net [HEURISTIC]; press set-up must beat the inbound lag (R-DF-18) | R-TR-14, R-TR-21, R-DF-18 |
| Miss with a long rebound | Push: outlet, lanes filled, rim runner (MSU rule) | Stop the ball, protect the rim, find shooters; "jog back" exposure | — | Secure to half-court crossing about 2–4 s in primary breaks [HEURISTIC; transition_full 3 anchors] | R-TR-01..04, R-TR-12, new-DF-A8 |
| Live-ball turnover (steal) | Run out immediately; leak-outs | Sprint back; take-foul candidates (R-TR-25) | Official trails the play | 0–2 s to first advance pass [HEURISTIC] | R-TR-08, R-TR-25 |
| Opponent reaches the bonus (7th team foul) | Attack the rim, draw contact; post feeds | Less hand-checking, fewer reach-ins, more zone or containment | Bench: foul trouble and fouls to give become live | Change visible within 1–3 possessions [HEURISTIC] | R-SR-03, new-DF-A7 |
| Called timeout | ATO set (often a named special), lineup change | Scheme change or special coverage on the ATO target | Coach: timeout type; media conversion | Effect on the first possession after the restart (beliefs register new-8 definition: restart within 5 s) | R-EV-15, new-CC-A6 |
| Ball screen | Handler reads coverage: reject, use, split, snake, pocket pass to the roller, pull-up; spacers lift, drift, shake | Coverage per plan (drop, hedge, blitz, switch, ICE); tag the roller; low man rotation | Officials watch moving and illegal screens | Coverage resolves from 1.0 s before to 2.0 s after the screen moment (defense_full F3.0); tag within 1.2 s for high drop (F3.1) | R-ST-17, R-ST-20, R-DF-16, new-ST-6 |
| Post entry | Post seals, works one side; cutters off the post; re-post | Front, ¾, behind; double from top, baseline or the passer; rotate behind | Officials watch post contact (hand-check, displacement) | Double arrives 0.5–1.5 s after the catch [HEURISTIC] | R-DF-07 tightened |
| Drive | Kick to corner, dump to dunker, drift; finish | Help from the low man or the nail; stunt; closeout chain | Block/charge decision at the restricted area (4-31; reviewable via 11-4.1.c until the last 2 min) | Help onset 0.5–1.5 s after the drive starts [HEURISTIC, defense_full F11.6 lag] | R-EV-06, R-DF-08, R-CO-02 |
| Skip pass | Catch-and-shoot or attack the closeout | Closeout: sprint-stop (≥ 4 m/s then < 1 m/s within 0.4 s), choppy, fly-by (defense_full F7.5) | — | Ball in flight 0.6–1.0 s across 12–15 m [HEURISTIC] | R-DF-08, R-EV-02 |
| Zone look | Zone offense: alignment change (odd vs even front), high-post flash, short corner, skip, overload | Zone holds; match-up rules | Bench: call a zone set | Offense recognition 1–3 possessions [HEURISTIC] | R-DF-17, R-ST-24, new-ST-A10 |
| Press | Press break alignment, middle flash, reversal, attack after the trap | Trap, rotate, fall back into the zone press | 10-s backcourt count (9-10) | Trap arrives 1–2 s after the first inbound catch [HEURISTIC] | R-DF-12, R-DF-18, R-ST-24, new-SR-4 |
| Foul trouble (starter) | Hunt the foul-troubled defender in pick-and-roll and post-ups | Hide him on the weakest scorer; zone | Coach: sit or stay (beliefs register C3: Izzo sits two-foul starters more than most) | Next dead ball | R-MD-16, new-CC-A5, new-ST-A9, new-DF-5 |
| End of shot clock (≤ 7 s, no advantage) | Bailout ball screen or isolation for the best creator | Switch everything, no help, contest | Shot-clock operator; horn adjudication by review | Last 5–7 s [HEURISTIC] | new-ST-A11, R-MB-06 |
| End of half / game clock | Two-for-one; last shot; foul to extend | Foul up 3; switch everything | Head coach live-ball timeout in the last 2 min (5-11.3); reviews (11-2) | 33–45 s two-for-one window (config, proposal); last 10–60 s fouling | R-SR-11, R-PE-07 |
| Opponent scoring run | Timeout, lineup change, slow the pace, go inside | Scheme change (zone, press, switch) | Coach: wait for the media timeout or call one | Timeout within 1–3 possessions of an 8-0 run [HEURISTIC]; evidence that timeouts stop runs is mixed (beliefs register B2) | R-MD-17 rewrite, R-CC-02, new-EV-A14 |
| Lineup change (opponent goes small or big) | Hunt the mismatch (post the small, drag the big into ball screens) | Switch more vs small; drop vs big | Coach: counter-substitution | 1–3 possessions [HEURISTIC] | R-MD-15, new-CH-A2, new-ST-A9 |
| Opponent hot shooter (≥ 2 straight makes or ≥ 3 threes in a half) | Run him off screens again | Top-lock, deny, switch a better defender onto him, no help off him | Bench call at the next dead ball | 0–3 possessions [HEURISTIC]; the hot hand itself is "mixed" (beliefs register A1) | new-DF-A6 |

Notes from the bench and the whistle:

- **Coach:** most adjustments are made at dead balls (timeouts, media timeouts, free throws, substitutions). A model that attributes a scheme change to the last live-ball event is usually wrong; the trigger is often two or three possessions earlier and the change lands at the next dead ball. Store the lag in possessions (R-DF-19 tightened).
- **Official:** the crew rotates after fouls and works lead, trail and centre positions; who had the play, and from what distance and angle, determines whether a call can be fairly second-guessed. The 2026-27 points of emphasis on mechanics (cited for R-IV-02 in `config/invariants.yaml`) make this a current topic. Our outputs describe what happened and where the official stood; they do not grade officials (new-RF-A15).

---

## 3. ANALYZE: how each of them moves

Speeds from the NCAA D-I men's Kinexon study (Stone et al. 2022, cited in `docs/research/load_thresholds.md` item 5): peaks of guards 7.04 ± 0.39, forwards 6.63 ± 0.52, centres 6.23 ± 0.33 m/s; distance above 5.0 m/s is typically only 2–4 m per minute (same document). Defense signatures from `docs/taxonomy/defense_full.md` F3 and F7.5. Other numbers are **[ANALYST HEURISTIC]**.

| Role | Movement signature that matters | Typical values | Must measure | Sample rate and accuracy needed | Broadcast video (1080p, 29.97 fps) can / cannot |
|---|---|---|---|---|---|
| Ball handler | Pace into the screen, angle of attack, snake, rejection, hesitation, first step, pull-up stop | Pace 3–5 m/s into a screen [HEURISTIC]; peak about 7 m/s (guards) | Speed, heading change (°) at the screen moment, distance from the screener at the screen moment (m), dribble count | 10 Hz state; position ≤ 0.5 m (R-PL-13); heading ±15° | Can: always on camera. Cannot: hand and dribble detail on wide shots; reliable acceleration (load_thresholds item 6) |
| Screener | Arrival (walk-up, sprint, flip), screen angle, contact, then roll, short roll, pop, slip, ghost | Strict screen: ≤ 0.3 m/s for ≥ 0.5 s within 1.2 m of the user's path (R-ST-17) | Screen angle (°), set duration (s), separation created (m), screen moment (R-ST-20) | 10 Hz; position ≤ 0.3 m to tell strict from loose | Can: usually on camera near the ball. Cannot: contact legality (illegal screen) except on replays |
| Roller / popper | Roll depth and lane, pop spot (mid-range or arc), short-roll catch point | Roll 4–6 m/s [HEURISTIC] | Path, catch r and θ, time from screen to catch (s) | 10 Hz | Can: mostly. Cannot: when the camera follows the handler away from the roll |
| Spacer / shooter | Lift, drift, shake, relocate, corner fill; feet set at catch | Relocation 1–3 m after a drive [HEURISTIC] | Spot at catch, feet-set time before the catch (s), closeout distance faced (m) | 10 Hz; spot accuracy ≤ 0.5 m (three-point line: 6.75 m, corners 6.60 m) | Can: on wide shots. Cannot: weak-side corners on tight shots (R-VI-05 coverage) |
| Cutter | Backdoor, flare, curl, flash; V-cut and L-cut set-ups | Cut 4–6 m/s; change of direction ≥ 45° within 0.5 s at ≥ 3 m/s entry (new-PL-2) | Cut type, entry and exit speed, separation at the catch | 10 Hz | Can: mostly. Cannot: cuts that start off-screen |
| Post | Seal, duck-in, re-post, back-down, turn | Seal hold ≥ 1 s [HEURISTIC]; 3 s in the lane (9-9) | Lane time (s), seal side, catch r | 10 Hz; lane boundary ±0.3 m | Can: on wide shots. Cannot: contact force |
| Rim protector | Drop depth, help from the weak side, verticality, contest | Drop depth bands 0.6–1.83, 1.83–3.05, > 3.05 m (R-DF-16); r ≤ 2.5 m when back | Depth (m) 0.3 s after the screen moment, distance to rim, contest distance | 10 Hz | Can: on camera with the ball. Cannot: jump height (needs 3D, R-CG-11) |
| On-ball defender | Stance, slide, over/under/through the screen, ICE body angle | Slide 2–4 m/s [HEURISTIC]; pick-up point and pressure distance ≤ 1.83 m (new-DF-3) | Distance to handler, side (forcing direction), path class at the screen | 10 Hz; position ≤ 0.3 m for path class | Can: yes. Cannot: hand activity |
| Help defender | Gap, stunt, rotate, recover; closeout | Closeout ≥ 4 m/s then < 1 m/s within 0.4 s, end 0.6–1.0 m (defense_full F7.5) | Reaction delay (s), path, closeout speed and end distance | 10 Hz; timing ±1 frame (33 ms) | Can: when in frame. **Cannot: weak-side help on tight or ball-following shots: the biggest defensive blind spot** |
| Tag / low man | Bump the roller, then recover to the corner | Tag within 1.5 m of the roller by 1.2 s after the screen moment (defense_full F3.1) | Tag time, recovery time | 10 Hz | Often half out of frame on side ball screens |
| Rebounder | Box-out contact, crash path, leak-out | Crash 3–5 m/s [HEURISTIC] | Position at release (new-EV-13), box-out, crash or leak | 10 Hz | Can: mostly. Cannot: who boxed whom on a tight shot |
| Official, lead | End-line position, moves with the ball side | Mostly walking and jogging [HEURISTIC, unverified] | Role, position, distance and angle to the contact (new-RF-9) | 1–2 Hz enough for role; 10 Hz for distance at the call | Partly visible; often cut out of frame under the basket |
| Official, trail | Near the sideline at the top of the play | — | Role, position | 1–2 Hz | Usually visible on the far sideline |
| Official, centre | Opposite the trail, free-throw line extended area | — | Role, position | 1–2 Hz | Often on the camera side, under the camera; partly out of frame |
| Coach and bench | Standing, signalling sets, calling timeouts, coaching-box position | — | Timeout requests (from PBP and scorebug), substitutions, bench visibility | Event level | Rarely shown; only on cutaways (R-CC-04 stays a Should) |

What broadcast video gives and does not give (measured where possible):

- **Frame timing**: 29.97 fps constant on the two pilot games (inbox 006), so one frame is 33.4 ms; every timing carries ±1 frame (R-CO-06). 1080p60 does not exist for these replays.
- **Scorebug**: present in 77.4% of sampled frames, on 93 of 95 wide shots and 0 of 17 replays; the "POSS" marker is the alternating-possession arrow; score change lags the ball through the net by 1.50–2.60 s (mean 1.963 s, median 1.933 s, first 10 UConn makes) plus 0.30 s for the digit change (inbox 006). The arena shot clock can reset on rim contact before the make.
- **Condensed replays** remove commercials and some dead-ball time: huddles, timeouts and some free-throw routines may be absent; the intake must say which (R-VI-02 tightened).
- **Coverage**: the main camera follows the ball; weak-side players and the rim protector on a side ball screen can be out of frame. Defensive measures need the off-screen estimate (R-DT-07) and the coverage share on every number (R-PL-05 style).
- **Cannot**: forces and contact legality, hand activity on wide shots, jump heights without 3D, reliable accelerations above about 3 m/s² (load_thresholds item 6), the bench, and what the coach said.

Tracking needs, summarised for this perspective: state at **10 Hz** (computed from 29.97 fps), positions **≤ 0.5 m** overall and **≤ 0.3 m** for path-class and lane-time decisions, timings **±1 frame**, identities **≥ 99%** on published numbers (R-ID targets), and every per-player number with its **observed-time share**.

---

## 4. SYNTHESIZE: what changes in the existing requirements

### 4.1 Counts per family

| Family | IDs | keep | tighten | loosen | rewrite | drop |
|---|---|---|---|---|---|---|
| R-RR | 9 | 8 | 1 | 0 | 0 | 0 |
| R-DQ | 10 | 8 | 2 | 0 | 0 | 0 |
| R-DS | 15 | 15 | 0 | 0 | 0 | 0 |
| R-RG | 11 | 10 | 1 | 0 | 0 | 0 |
| R-FD | 12 | 10 | 2 | 0 | 0 | 0 |
| R-PC | 16 | 15 | 1 | 0 | 0 | 0 |
| R-MD | 20 | 17 | 2 | 0 | 1 | 0 |
| R-ID | 15 | 15 | 0 | 0 | 0 | 0 |
| R-VI | 16 | 14 | 1 | 1 | 0 | 0 |
| R-CG | 11 | 11 | 0 | 0 | 0 | 0 |
| R-DT | 19 | 18 | 1 | 0 | 0 | 0 |
| R-BL | 8 | 8 | 0 | 0 | 0 | 0 |
| R-GT | 5 | 5 | 0 | 0 | 0 | 0 |
| R-SY | 10 | 8 | 2 | 0 | 0 | 0 |
| R-TR | 28 | 25 | 0 | 0 | 1 | 2 |
| R-EV | 16 | 13 | 3 | 0 | 0 | 0 |
| R-AU | 4 | 4 | 0 | 0 | 0 | 0 |
| R-RF | 7 | 5 | 2 | 0 | 0 | 0 |
| R-ST | 26 | 24 | 1 | 0 | 1 | 0 |
| R-DF | 21 | 18 | 2 | 0 | 1 | 0 |
| R-VL | 13 | 12 | 1 | 0 | 0 | 0 |
| R-CH | 8 | 6 | 2 | 0 | 0 | 0 |
| R-CC | 5 | 3 | 1 | 1 | 0 | 0 |
| R-GU | 6 | 5 | 1 | 0 | 0 | 0 |
| R-SR | 15 | 12 | 2 | 1 | 0 | 0 |
| R-IV | 16 | 14 | 0 | 0 | 2 | 0 |
| R-SB | 4 | 3 | 1 | 0 | 0 | 0 |
| R-MB | 7 | 6 | 0 | 0 | 1 | 0 |
| R-CX | 19 | 18 | 1 | 0 | 0 | 0 |
| R-PL | 17 | 17 | 0 | 0 | 0 | 0 |
| R-CO | 8 | 7 | 0 | 0 | 1 | 0 |
| R-OS | 5 | 5 | 0 | 0 | 0 | 0 |
| R-EN | 8 | 8 | 0 | 0 | 0 | 0 |
| R-CD | 5 | 5 | 0 | 0 | 0 | 0 |
| R-PR | 11 | 10 | 1 | 0 | 0 | 0 |
| R-PE | 13 | 12 | 1 | 0 | 0 | 0 |
| R-MK | 33 | 33 | 0 | 0 | 0 | 0 |
| R-HR | 12 | 11 | 1 | 0 | 0 | 0 |
| R-VZ | 7 | 6 | 1 | 0 | 0 | 0 |
| R-CS | 10 | 10 | 0 | 0 | 0 | 0 |
| R-VA | 9 | 9 | 0 | 0 | 0 | 0 |
| R-HY | 7 | 7 | 0 | 0 | 0 | 0 |
| R-PT | 1 | 0 | 1 | 0 | 0 | 0 |
| **Total** | **518** | **470** | **35** | **3** | **8** | **2** |

### 4.2 Changed IDs (tighten, loosen, rewrite, drop)

Each row: verdict, proposed new text, acceptance criterion, where it lands, and why this perspective needs it. Rule numbers are 2026-27 NCAA men's rules book unless named otherwise.

#### R-RR

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-RR-03 | tighten | Failure analysis slices also include game situation: transition vs half-court, after timeout (ATO), shot clock ≤ 5 s at the event, last 240 s of a half, media segment, and the camera shot type during the event. | Every Shall-fail report has the 6 situation slices with n per slice; slices with n < 50 are listed, not flagged. | results/<run>/failure_analysis.parquet: slice_situation columns | The errors that reach air cluster in end-of-clock, ATO and late-game plays, exactly the clips we show. |

#### R-DQ

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-DQ-01 | tighten | Cross-source check adds the official final box score (scorer's book via the NCAA stats site where its terms allow, unverified) against the ESPN and CBBD boxes, per player and per team, for every counting stat. | 100% of processed games have a cross-source row per counting stat; any difference > 0 creates a dq_cross_source row with both values and sources. | dq_cross_source (game_id, stat, source_a, source_b, value_a, value_b) | A number that differs from the official box by one rebound is the number that gets corrected on air. |
| R-DQ-06 | tighten | Accounting identities per game: possession points = final score; team minutes = 200 + 25 per extra period; FGA = makes + misses; every chance closes with a made FG, a final free throw, a turnover, or a defensive rebound including team and dead-ball rebounds as the official scorer records them. | Identities hold on 100% of games, or the game goes to quarantine with the failing identity named. | dq_identities (game_id, identity, lhs, rhs, pass) | Team and dead-ball rebounds are where possession counts and broadcast rebound margins disagree. |

#### R-RG

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-RG-02 | tighten | Rights gate: public or pitch outputs carry no broadcast frames or audio; clips are referenced by game_id and video time only; drawings go on our top-down court, never over broadcast video, unless the rights holder clears it in writing. | Rights checklist line 'no broadcast pixels' ticked for 100% of outputs; an automated scan of published files finds 0 embedded video frames. | coord/rights_checklist.md; outputs manifest | A network's clip is the network's; a telestrated frame without clearance is the fastest way to lose access. |

#### R-FD

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-FD-05 | tighten | Availability log per player per game with status at tip (available, out, questionable or game-time decision, minutes restriction, suspended), the as-of UTC time and source of each status, reconciled after the game with 'did not play' from the box. | Every rostered player has a status row per game with source and as-of ≤ tip; post-game reconciliation with the box on 100% of games. | availability_log.status, .as_of_utc, .source, .dnp_reconciled | Pre-game numbers are wrong if they assume a player who was ruled out 40 minutes before tip. |
| R-FD-08 | tighten | Referee crew per game: each official's name, crew position (referee or umpire), crew-chief flag, source and as-of time; mid-game replacements logged with game clock. | 100% of processed games list 2 or 3 officials from ≥ 1 source, cross-checked under R-DQ-01. | game_officials (game_id, official_id, crew_position, is_crew_chief, source, as_of_utc) | Crew context (foul rate, review use) is a standard pre-game note; it must name the right people. |

#### R-PC

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-PC-11 | tighten | Every tendency (drive direction, finishing hand, shot-clock use, pass-or-shoot by zone, help frequency) carries n, the as-of date and a shrunk estimate; display suppresses tendencies with n < 20 events (proposal). | 100% of tendency rows carry n and as_of; the display layer shows none with n < 20. | player_card.tendencies (value, n, as_of, shrunk_value) | 'He goes left 80% of the time' on 5 drives is how analysts get burned. |

#### R-MD

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-MD-13 | tighten | Media segments follow the game's actual media format (16-12-8-4 or 15-10-5 marks, Rule 5-14.10.c), the conversion of a team timeout, review or challenge within 30 s before a mark (5-14.10.e) and of the first team timeout of the second half (5-14.10.d); segment boundaries come from the observed media timeout times, not from the marks. | Media timeout times agree between video, scorebug and PBP on 100% of pilot games; segment IDs recompute from timeouts. | games.media_format; timeouts.became_media; state_second.media_segment_id | 'Under-12 media' is how a broadcast and a bench count the half; the segment must be the one that actually happened. |
| R-MD-16 | tighten | Foul-trouble state per player using config thresholds (default analyst convention: 2 PF in the first half; 3 PF with more than 600 s left in the second half; 4 PF in the second half or an extra period; proposal), plus seconds on the bench since entering foul trouble and the re-entry time. | Recomputes from fouls and substitutions; matches on-screen foul graphics on ≥ 95% of graphics read (weak label, new-AU-1). | state_second.foul_trouble_flag; player_stints.foul_trouble_at_exit | Foul trouble is the first bench decision the analyst has to explain; the definition must be stated, not assumed. |
| R-MD-17 | rewrite | Score state: margin, lead changes, ties, largest lead per team; runs stored three ways, never merged: (a) unanswered points since the opponent's last point; (b) broadcast run 'a–b' = the window ending at the current moment and starting right after a score by either team that maximises the running team's net points, shown only when the net is ≥ 6 (proposal); (c) register run = net ≥ 8 points in a rolling 120 s (beliefs register B1); plus pre-possession win probability once PR exists. | All three recompute from score_events within 0 points; (b) matches on-screen run graphics on ≥ 90% of graphics read (weak label, new-AU-1). | state_second.run_unanswered_pts, run_bcast_for, run_bcast_against, run_bcast_start_s, run_register_flag | '12-2 run' is the most-used in-game stat on TV and has no written definition anywhere in the doc. |

#### R-VI

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-VI-01 | loosen | Capture standard: native ≥ 1080p, constant frame rate; 29.97 fps is the accepted archive standard (1080p60 does not exist for the 2025-26 replays, inbox 006); 59.94 fps used when a source offers it; original audio kept, no rescaling. | Intake shows CFR and ≥ 1080 lines on 100% of files; every frame-based target states the fps it assumes. | video_intake.fps, .height_px | A Shall that the available footage cannot meet is a Shall nobody follows. |
| R-VI-02 | tighten | Intake report adds edit-cut detection for condensed replays: every game-clock discontinuity and every removed dead-ball span (timeout, media timeout, free-throw routine, review, halftime), with game clock before and after and the inferred type; such spans are flagged not_in_footage. | All game-clock discontinuities ≥ 1 s found on the 2 pilot games against a hand check; 0 spans imputed as 'nothing happened'. | video_intake.edit_cuts (start_video_s, gc_before_s, gc_after_s, cut_type) | Condensed replays cut the timeouts and huddles; the ATO and substitution logic must know what it did not see. |

#### R-DT

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-DT-12 | tighten | Officials tracked with role (lead, trail, centre) per second with confidence and floor position in metres; role changes stored as rotation events; two-person crews supported. | Role accuracy ≥ 90% on 200 labelled seconds (proposal); position within 1.0 m of gold when on the main camera. | official_positions.role, .role_conf, .x_m, .y_m; official_rotations | Who had the call is the first question after a controversial whistle. |

#### R-SY

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-SY-01 | tighten | Scoreboard reading every second of live play also stores each field's change time and the lag model per field; the 'POSS' marker is the alternating-possession arrow, never ball possession; tenths are read when the game clock is below 60 s (Rule 1-18.2). | Field accuracy ≥ 99.5% on scorebug-visible seconds of the pilot games; a test proves POSS never writes to a possession column. | scorebug_reads (field, value, change_video_s, lag_s) | End-of-half clock reads decide two-for-ones, fouls to give and buzzer-beaters: the moments that get replayed. |
| R-SY-04 | tighten | Possession types are multi-label flags (a possession can be ATO and SLOB at once), adding: after media timeout, after called timeout (which team), end of period (start ≤ 35 s left), shot clock off, after made free throw. | Every possession has ≥ 1 flag; flags recompute from events; counts per flag per game reported. | possessions.type_flags (array of enum) | ATO and SLOB efficiency is a coach's report card; a single-type field forces a false choice. |

#### R-TR

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-TR-05 | rewrite | The clock-based transition class (from R-TR-01 thresholds) is kept only as one named definition inside R-TR-18; the reported class is R-TR-09 (state-based). | No output column called transition_class without a definition suffix (lint check). | possessions.tr_class_<definition> | Two Shall classes that disagree will produce two different transition numbers in the same graphic. |
| R-TR-06 | drop | Merged into R-TR-26 (value of each break state per second). | n/a: R-TR-26 carries the per-second value. | n/a | Duplicate requirement; one owner per number. |
| R-TR-11 | drop | Merged into R-TR-18 (its definition list is a superset). | n/a: R-TR-18 carries every definition. | n/a | Duplicate requirement; one owner per number. |

#### R-EV

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-EV-07 | tighten | Shot type vocabulary includes the coach and broadcast terms: catch-and-shoot, pull-up, step-back, side-step, floater or runner, hook, layup, dunk, tip-in, putback, alley-oop, fadeaway, bank; plus the assisted flag and assister from PBP. | ≥ 85% shot-type agreement with coach labels on 300 shots (proposal); assisted flag equals PBP on 100% of made FGs. | shots.shot_type, .assisted, .assister_id | 'Pull-up three off a drop' is the sentence; the vocabulary has to contain its words. |
| R-EV-13 | tighten | Sequence features use the R-MD-17 run definitions; the 2-, 4- and 6-min net points stay as numeric features, not as 'runs'. | One run vocabulary in config; features recompute from score_events. | possessions.prev_result, .net_120s, .net_240s, .net_360s | One word, one definition. |
| R-EV-16 | tighten | Challenge record per Rule 11-4: challengeable type (out of bounds any time; basket interference or goaltending and secondary-defender restricted area only until the last 2 min of regulation, 11-4.1.a-c), timeout used (30 s or full), review duration (s), outcome (stands or overturned), timeout charged or retained, second challenge earned; officials' own reviews (11-2, 11-3) logged separately with trigger and duration. | Every review in PBP or on the broadcast has a row; duration within ±2 s of video when visible. | reviews (game_id, kind, initiator, rule_ref, start_video_s, duration_s, outcome, timeout_charged) | Challenges are new; every one becomes a segment, and the rule limits change in the last 2 min. |

#### R-RF

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-RF-03 | tighten | Foul types follow the 2026-27 classes (no 'intentional'; deliberate end-game fouls stored as common or Flagrant 1 with a deliberate_endgame tag, new-RF-3); each foul stores shooting or non-shooting, and-one, and whether it put the opponent in the bonus or double bonus. | 100% of fouls carry a class from the config list; bonus-trigger flag recomputes from team fouls. | fouls.foul_class, .shooting, .and_one, .bonus_trigger | 'That's the seventh, they're in the bonus' is called live; we must get the count right. |
| R-RF-06 | tighten | Crew and per-official tendency tables, pace-adjusted: fouls per 100 possessions, FTA per FGA, home-away foul split, call-type mix, reviews per game, with n games and as-of date, shrunk toward the D-I mean. | Recomputes from PBP; every published value shows n games; values with n < 10 games flagged. | official_tendencies (official_id, as_of, metric, value, n_games, shrunk_value) | Raw fouls per game punish crews that work fast games. |

#### R-ST

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-ST-05 | tighten | Set match per chance outputs the coaching name (namespaced per R-ST-22) and its broadcast phrase (new-MD-A6), with calibrated confidence. | Top-1 family agreement with coach labels ≥ 80% and top-3 ≥ 95% on 300 MSU chances (proposal); confidence ECE ≤ 0.05. | set_instances.set_name, .broadcast_phrase, .conf | The set name is the hook of every breakdown segment; a wrong name in front of a coach ends the segment's credibility. |
| R-ST-12 | rewrite | Templates are defined by role (handler, screener, roller or popper, spacer, cutter, post), never by a named player, so any season's roster matches. | On the first 2026-27 footage the template match rate is within 10 points of the 2025-26 rate. | templates.roles | The current text names two departed players; requirements should not age. |

#### R-DF

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-DF-06 | rewrite | Ball-screen coverage per screen is reported as the R-DF-16 two-level label; published outputs use the 4 coarse classes; a fine coverage (taxonomy F3 list) is shown only with confidence ≥ 0.8. | Coarse agreement ≥ 85% with coach labels on 200 screens; fine agreement ≥ 70% where shown (proposal). | ball_screens.coverage_coarse, .coverage_fine, .coverage_conf | Calling a hedge a drop on air is the error coaches remember; publish only what is reliable. |
| R-DF-07 | tighten | Post defense adds double-teams: where the double comes from (top, baseline, strong-side wing, weak side), trigger (on catch, on first dribble, on turn), time from catch to double (s), and the rotation behind it. | Double = 2 defenders within 1.5 m of the post holder for ≥ 0.5 s; ≥ 85% agreement with labels on 100 post touches (proposal). | post_touches.double_from, .double_trigger, .double_time_s | 'They're bringing the double off the passer' is a core adjustment segment. |
| R-DF-19 | tighten | Scheme-change triggers add foul trouble of the rim protector, an opponent hot shooter (new-DF-A6), an opponent lineup change, and after a timeout; each change stores possessions elapsed since its trigger. | Every scheme_change row has a trigger code or 'none found'; the lag in possessions recomputes. | scheme_changes.trigger, .lag_possessions | Adjustments are the story of the second half; the trigger is the 'why'. |

#### R-VL

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-VL-04 | tighten | Shot quality per shot as expected points per attempt from location, contest, type, shooter prior. | Mean predicted vs actual within 0.02 points per shot over ≥ 1,000 shots, and within 0.05 for each shot type with ≥ 200 shots. | shots.xpts | A shot-quality number that is not calibrated will be contradicted by the box score on the first night. |

#### R-CH

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-CH-06 | tighten | Halftime adjustment measured as the change from the last 600 s of the first half to the first 300 s of the second half in set mix, coverage mix, pace and PPP, with n possessions. | Computed for 100% of processed games; marked descriptive when n is below the R-VA-05 rule. | coach_halftime_changes | 'What did they change at the half?' is asked every game. |
| R-CH-08 | tighten | Runs and momentum use the R-MD-17 run definitions and are tested against the state model under a pre-registered hypothesis (beliefs register new-4, new-5, new-7). | Test registered under R-HY-01 before results are read. | hypotheses.yaml entries | 'Momentum' must be a tested claim, not a caption. |

#### R-CC

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-CC-02 | tighten | Timeout behaviour adds: time from the opponent run reaching the threshold to the timeout (game-clock s and possessions), whether a media timeout was due within 60 s, timeouts left at the under-4 media and at the final horn. | Recomputes from timeouts, media slots and score_events for 100% of games. | timeouts.run_lag_s, .run_lag_poss, .media_due_60s; team_game.timeouts_left_u4, .timeouts_left_final | 'He's saving it for the media' is a real bench decision and a recurring talking point. |
| R-CC-03 | loosen | Reactions: player pulled at the first substitution opportunity (first dead ball) after his turnover or defensive breakdown, or within 60 s of game clock; both windows stored. | Recomputes from substitutions; both windows reported. | coach_reactions.window | Substitutions happen only at dead balls (Rule 3-6); 30 s of clock misses legitimate hooks. |

#### R-GU

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-GU-04 | tighten | Narration uses only vocabulary-map terms and broadcast phrases (new-MD-A6); every numeric claim carries n; unmeasured words ('momentum', 'wanted it more', 'clutch gene') are banned unless defined in config. | Automated lint passes on 100% of sentences; analyst or coach review of 50 sentences ≥ 90% 'acceptable'. | narration lint config | Generated text goes straight to people who will quote it. |

#### R-SR

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-SR-04 | tighten | Timeout and review state adds the game's media format, the actual media slot of each media timeout (with conversions under 5-14.10.d-e), timeouts left by length (30 and 60 s in the media format; 75 and 30 s otherwise) and challenge state. | Proposed invariants new-IV-12 and new-IV-13 pass on 100% of pilot games. | state_second.timeouts_left_30/60/75, .challenge_left, .media_slot | 'Two timeouts left, one full' is said on every late-game broadcast. |
| R-SR-07 | loosen | Personnel: the 10 players with identity confidence, x, y, speed, acceleration, stint length; the 2 or 3 officials' positions (Rule 2-1.1.a). | Crew size per game from game_officials; position rows equal crew size per second when visible. | state_frame.officials | Rule allows two-person crews; a hard 3 creates false invariant breaks. |
| R-SR-11 | tighten | Game situation every second as named flags with thresholds in config, promoted from Should to Shall: two-for-one window (33–45 s), last-shot hold, foul-to-extend (trailing, ≤ 60 s, margin 1–9), foul-up-3 cell (game clock × shot clock), shot clock off, fouls to give per team, foul-trouble flags. | Flags recompute from state; constants live in config/invariants.yaml; counts per flag per game. | state_second.situation_flags | These are the late-game decisions coaches make and analysts explain (beliefs register C4, C5). |

#### R-IV

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-IV-02 | rewrite | Two or three officials on court (three expected in D-I); a crew-size change mid-game is logged (Rule 2-1.1.a). | Invariant uses constants.officials_on_court_allowed = [2, 3]. | config/invariants.yaml | Matches the rule and inbox 006 question 12. |
| R-IV-10 | rewrite | Timeouts left never go below 0 and never go up except at the start of an extra period; format per game: media format with ≥ 3 media timeouts per half → three 30-s and one 60-s per team per game, at most two 30-s carried into the second half, one extra 30-s per extra period (5-14.10.a, b, f); fewer than 3 media or no media → four 75-s and two 30-s, one extra 75-s per extra period (5-14.8, 5-14.9). | Proposed invariant new-IV-12 passes on 100% of pilot games. | config/invariants.yaml | Current text gives a 75-s timeout per extra period, which is wrong for televised games. |

#### R-SB

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-SB-03 | tighten | Initial make-detection window set to 5 s (measured scorebug lag 1.50–2.60 s, mean 1.963 s, inbox 006), then reset per game to the measured 99th percentile + 1 s. | Lag distribution stored per game; window recomputed per game; 0 makes missed for window reasons on the pilot games. | score_events.board_lag_s; config window | A 15 s window pairs the wrong basket in a fast exchange. |

#### R-MB

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-MB-04 | rewrite | Make frame within ±2 frames at 29.97 fps (±0.067 s) or ±3 frames at 59.94 fps (±0.05 s) of the hand label; 2 vs 3 agreement with PBP ≥ 99%. | As stated, per fps. | made_baskets.make_frame | Targets must be in frames of the footage we have (inbox 006 question 7). |

#### R-CX

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-CX-18 | tighten | Pre-game card adds a T−900 s snapshot with announced starters and availability updates when public. | Snapshot row exists for 100% of games, or a 'not public' flag. | pregame_card.snapshot_label | Starting lineups change the matchup notes 15 minutes before tip. |

#### R-CO

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-CO-04 | rewrite | Pressure performance uses the single config clutch definition (R-MD-13: ≤ 300 s left, margin ≤ 5) as one slice and contest ≤ 1.2 m and shot clock ≤ 5 s as separate slices; no other 'late game' rule. | One clutch constant in config, referenced by every module (lint check). | config clutch constant | Two clutch definitions produce two different clutch numbers. |

#### R-PR

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-PR-11 | tighten | Live in-game win probability refreshed within 10 s of each scoreboard change; calibrated overall and for the last 240 s separately; no swing > 0.25 without a score, turnover or foul event; never published before R-PR-09 passes. | ECE ≤ 0.03 overall and ≤ 0.05 in the last 240 s on held-out games; sanity rule violations = 0. | wp_live (game_id, video_s, wp, event_id) | A win-probability graphic that jumps without a play is mocked within minutes. |

#### R-PE

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-PE-07 | tighten | End-game policies stored per decision cell (game clock × shot clock × margin), including fouling up 3, the head coach's live-ball timeout in the last 2 min (Rule 5-11.3, 5-14.1.a exception) and the two-for-one; fitted from PBP plus scorebug shot clock. | Cells with n ≥ 30 fitted, others pooled with a stated prior. | endgame_policy_cells | End-game coaching decisions are graded on air every night. |

#### R-HR

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-HR-02 | tighten | Review item clip windows by event type in config: shot 3 s before / 2 s after, ball screen 4 / 3, transition from the secure catch to the first shot, foul 3 / 3, default 3 / 3; reviewer can extend. | Config windows used for 100% of items. | config/review_windows.yaml | A ball screen read starts before the screen; a fixed 3 s window cuts the set-up. |

#### R-VZ

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-VZ-06 | tighten | Should set adds the broadcast-standard graphics: win-probability chart with run shading, foul tracker, timeouts left, shot chart by sector and ring, lineup plus-minus with n. | Each graphic renders from the state tables of a pilot game, every number linked (R-VZ-02). | viz templates | These are the graphics producers ask for first. |

#### R-PT

| ID | Verdict | Proposed text | Acceptance | Lands in | Why (analyst, coach, official) |
|---|---|---|---|---|---|
| R-PT-01 | tighten | Pitch package adds a half-time packet and a post-game notes sheet for the processed game (new-VZ-A1, new-VZ-A2), each number linked to frames and reconciling with the official box. | Both documents exist for the pitch game; 100% of counting stats equal the official box. | results/pitch/ | Staff judge a product by the sheet they would actually use at half-time. |

### 4.3 Kept IDs, per family

Every ID not listed in 4.2 is **keep** as written in the live doc.

| Family | Kept IDs | Why keep |
|---|---|---|
| R-RR | 01, 02, 04, 05, 06, 07, 08, 09 | Run records are invisible on air but are how a wrong number is traced back; keep. |
| R-DQ | 02, 03, 04, 05, 07, 08, 09, 10 | Credibility rests here; the rest are right as written. |
| R-DS | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15 | Source terms and as-of discipline are the analyst's own rules; keep. |
| R-RG | 11, 01, 03, 04, 05, 06, 07, 08, 09, 10 | Rights and privacy are non-negotiable; keep. |
| R-FD | 01, 02, 03, 04, 06, 07, 09, 10, 11, 12 | Registry fields are what a stats producer pre-loads; keep. |
| R-PC | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 12, 13, 14, 15, 16 | Player cards are the bio graphics; keep with the n discipline. |
| R-MD | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 14, 15, 18, 19, 20 | Metadata is what makes every clip searchable; keep. |
| R-ID | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15 | Identity is the single biggest on-air risk; the IDs as written are right. |
| R-VI | 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16 | Video handling is sound. |
| R-CG | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11 | Court geometry is correct and needed for shot charts; keep. |
| R-DT | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 13, 14, 15, 16, 17, 18, 19 | Detection list is complete for the analyst's needs. |
| R-BL | 01, 02, 03, 04, 05, 06, 07, 08 | Ball state is complete. |
| R-GT | 01, 02, 03, 04, 05 | Gates are the right brake. |
| R-SY | 02, 03, 05, 06, 07, 08, 09, 10 | Sync to PBP and the scorebug is the backbone of every number. |
| R-TR | 01, 02, 03, 04, 07, 08, 09, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28 | Transition is over-specified rather than under; only merges proposed. |
| R-EV | 01, 02, 03, 04, 05, 06, 08, 09, 10, 11, 12, 14, 15 | Event rows are what clips are cut from; keep. |
| R-AU | 04, 01, 02, 03 | Audio as weak labels only is right. |
| R-RF | 01, 02, 04, 05, 07 | Officials' data is sensitive; keep the measured, non-judging framing. |
| R-ST | 01, 02, 03, 04, 06, 07, 08, 09, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26 | Set vocabulary is close to how coaches talk; keep. |
| R-DF | 01, 02, 03, 04, 05, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21 | Defense measures match the coverages coaches name; keep. |
| R-VL | 01, 02, 03, 05, 06, 07, 08, 09, 10, 11, 12, 13 | Value framework is right; keep. |
| R-CH | 01, 02, 03, 04, 05, 07 | Chemistry and coach records are storyline fuel; keep. |
| R-CC | 01, 04, 05 | Coach cards are a pre-game staple; keep. |
| R-GU | 01, 02, 03, 05, 06 | Belief state is the engine behind narration; keep. |
| R-SR | 01, 02, 03, 05, 06, 08, 09, 10, 12, 13, 14, 15 | State record is what a stats producer watches live; keep. |
| R-IV | 01, 03, 04, 05, 06, 07, 08, 09, 11, 12, 13, 14, 15, 16 | Invariants are the on-air sanity checks; keep. |
| R-SB | 01, 02, 04 | Scoreboard discrepancy handling is exactly how a stats desk works. |
| R-MB | 01, 02, 03, 05, 06, 07 | Make detection is the base of everything; keep. |
| R-CX | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 19 | Context features feed the pre-game card; keep. |
| R-PL | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17 | Load measures are useful but secondary for broadcast; keep as written. |
| R-CO | 01, 02, 03, 05, 06, 07, 08 | Cognition measures are research; keep. |
| R-OS | 01, 02, 03, 04, 05 | Opponent scouting from data sources is the right split; keep. |
| R-EN | 01, 02, 03, 04, 05, 06, 07, 08 | Engineering hygiene; keep. |
| R-CD | 01, 02, 03, 04, 05 | Coordination; keep. |
| R-PR | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10 | Prediction layer is the BPI-like product; keep. |
| R-PE | 01, 02, 03, 04, 05, 06, 08, 09, 10, 11, 12, 13 | Engine; keep. |
| R-MK | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33 | Markets are not the analyst's remit; no objections, keep. |
| R-HR | 01, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12 | Review loop is how labels get trusted; keep. |
| R-VZ | 01, 02, 03, 04, 05, 07 | Every number linked to frames is the analyst's first rule; keep. |
| R-CS | 01, 02, 03, 04, 05, 06, 07, 08, 09, 10 | Compute; keep. |
| R-VA | 01, 02, 03, 04, 05, 06, 07, 08, 09 | Validation rules are what makes numbers survive scrutiny; keep. |
| R-HY | 01, 02, 03, 04, 05, 06, 07 | Pre-registration protects narratives from cherry-picking; keep. |
| R-PT | none | Pitch; tightened only. |

---

## 5. New requirements from this perspective

Numbered after the highest repo proposal per family (see the conventions above). Thresholds marked (proposal) are starting values for calibration.

| ID | Tier | Requirement | Acceptance criterion | Lands in | Why this perspective needs it |
|---|---|---|---|---|---|
| new-DQ-A2 | Shall | **Published-number gate.** Every number that leaves the lab (pitch, staff sheet, any public output) passes an automated check: counting stats equal the official box (0 tolerance), derived stats recompute from the official box within display rounding, each number carries its definition ID, n and source, and the top 5 claims of each document are signed off by a reviewer. | 100% of published numbers pass; an audit of 50 random published numbers per month finds 0 unreconciled values. | `published_numbers` (doc_id, number_id, value, definition_id, n, source, reconciled, reviewer) | The stats desk rule: if it is not reconciled, it does not go on air. |
| new-DQ-A3 | Shall | **Official stat corrections.** Box-score changes posted after the final (assists, rebounds, blocks re-credited by the scorer) are captured with old value, new value, source and time seen; every output that used the old value is re-run and marked. | Weekly re-pull of the official box for processed games; 100% of diffs logged; dependent outputs re-run within 7 days. | `stat_corrections` (game_id, player_id, stat, old, new, seen_utc, source) | Post-game corrections are routine; a season total built on uncorrected boxes drifts. |
| new-MD-A6 | Shall | **Broadcast vocabulary layer.** Every analytic label shown to people has, in `config/vocabulary_map.yaml`, a coach term, a broadcast phrase of ≤ 4 words (e.g. ICE → "forcing him baseline"), and a list of banned or ambiguous synonyms. | 100% of labels used in outputs have all three; a coach or analyst review of 50 phrases rates ≥ 90% "acceptable on air". | `config/vocabulary_map.yaml` fields `coach_term`, `broadcast_phrase`, `avoid` | Correct words in plain language are the whole job on a telestrator segment. |
| new-SR-A6 | Shall | **Flow-state machine.** One `flow_state` per frame from the states S0–S11 of section 1.1 (with S4 split into transition, early, half-court), and every state change checked against the allowed-transition table with its rule reference; a disallowed change is an invariant break. | 100% of frames carry a state; disallowed transitions = 0 on gold-v1 or each is explained in review. | `state_frame.flow_state`; allowed transitions in `config/invariants.yaml` | Every downstream number (pace, ATO, transition share) depends on knowing which state the game is in; the rules give the legal moves. |
| new-SY-A4 | Shall | **Substitution times from video.** Each substitution's time is the dead ball in which the player checked in, read from video (players leaving and entering), replacing the PBP time when they differ; the difference is stored. | Lineups agree with video on ≥ 98% of possessions of the pilot games; every PBP-video difference > 0 s logged. | `substitutions.video_time_s`, `.pbp_time_s`, `.diff_s` | Lineup plus-minus on air is wrong whenever PBP logs a sub late (R-DQ-09 known bias). |
| new-SY-A5 | Shall | **Per-field scorebug latency correction.** Event times derived from the scorebug (score, clocks, fouls, timeouts) are back-dated with a per-field, per-game lag model fitted on events whose true time is seen on video. | After correction, the scorebug score-change time is within ±0.5 s of the ball-through-net frame on ≥ 95% of makes (measured raw lag 1.50–2.60 s, inbox 006). | `scorebug_lag_model` (game_id, field, median_s, p95_s); corrected `*_time_s` columns | Every "with X seconds left" sentence depends on the right time. |
| new-EV-A14 | Shall | **Run-stopper record.** For every run (R-MD-17 definitions), what ended it: called timeout (which team), media timeout, opponent score, foul, period end; the possessions and game-clock seconds from the run start to the stop; what changed at the stop (lineup, scheme, set). | Every run has an end row; changes link to `scheme_changes` and `substitutions`; recomputes from events. | `runs` (run_id, def, start_s, end_s, for_pts, against_pts, ended_by, changes) | "What stopped the run" is the second sentence after "12-2 run". |
| new-EV-A15 | Should | **Hustle events.** Per player per game: deflections, loose balls recovered, charges drawn, contested rebounds, box-outs, screen assists, with each event linked to video, under named definitions (ours, and the NBA hustle-stats definitions as a labelled reference, unverified). | Counts recompute from event rows; ≥ 85% agreement with labels on 100 events per type (proposal). | `hustle_events` | Hustle stats are a staple for role players who do not score. |
| new-CC-A5 | Shall | **Foul-trouble decision log.** For every player entering foul trouble (R-MD-16): time of the foul, whether he sat at the next dead ball, seconds and possessions sat, re-entry time and situation, fouls committed after re-entry, net points with him on and off. | Rows for 100% of foul-trouble entries; recomputes from fouls and substitutions. | `foul_trouble_decisions` | Benching a two-foul starter is the most-discussed bench decision (beliefs register C3: Izzo sits them more than most). |
| new-CC-A6 | Shall | **Timeout purpose.** Each timeout carries a purpose code: stop a run, ATO set, rest, ice a free-throw shooter, end-game management, advance-situation set, injury, challenge; inferred from context with a confidence, never from audio alone. Rule type (30, 60, 75 s, media conversion) stored with it. | Every timeout has a purpose code; purpose agrees with a coach label on ≥ 80% of 100 timeouts (proposal). | `timeouts.purpose`, `.purpose_conf` | Analysts grade timeouts by purpose; "wasted timeout" is a common critique that needs a definition. |
| new-CH-A2 | Shall | **Lineup-change response.** When one team changes its lineup composition class (e.g. from two bigs to one), store the other team's response: counter-substitution, scheme change or none, and the lag in possessions and seconds. | Rows for 100% of composition changes (new-MD-5 classes); recomputes from substitutions and scheme changes. | `lineup_responses` | "They went small, and the answer was..." is a standard adjustment segment. |
| new-ST-A9 | Shall | **Mismatch hunting.** Per ball screen and isolation, whether the offense targeted a specific defender (screener's defender chosen by the offense, re-screen until the switch, clear-out after a switch); per defender per game, the share of the opponent's ball screens he defended and the PPP allowed. | Hunted flag agrees with coach labels on ≥ 80% of 200 actions (proposal); shares recompute from tracks. | `ball_screens.hunted_defender_id`, `defender_game.hunted_share` | "They're hunting him in the pick-and-roll" needs a number behind it. |
| new-ST-A10 | Shall | **Zone recognition lag.** After a defensive scheme change to zone (R-DF-05), the possessions and seconds until the offense runs a zone alignment or zone set (R-ST-24), and the PPP before and after recognition. | Recomputes from `scheme_changes` and `set_instances`; reported per change with n. | `scheme_changes.offense_recognition_poss`, `.offense_recognition_s` | Zone changes win or lose a stretch based on how fast the offense adapts. |
| new-ST-A11 | Shall | **End-of-clock possessions.** Possessions whose first shot or turnover comes with shot clock ≤ 7 s, and end-of-period possessions (start ≤ 35 s left), store: the action used (bailout ball screen, isolation, set), the shooter, shot quality (R-VL-04), result. | 100% of qualifying possessions recorded; counts per team per game; descriptive when n is below R-VA-05. | `possessions.late_clock_flag`, `late_clock_action` | Late-clock creation separates good offenses from lucky ones and is graded every night. |
| new-DF-A6 | Shall | **Hot-shooter response.** When an opponent shooter makes ≥ 2 straight field goals or ≥ 3 threes in a half (config, proposal), measure the defense on his next 5 catches: distance at catch (m), denial or top-lock rate, defender change, help kept off him; and the possessions until the change. | Recomputes from tracks; reported per trigger with n; triggers listed per game. | `hot_shooter_responses` | "Somebody has to find him" is said live; the data should show whether anyone did. |
| new-DF-A7 | Should | **Pressure before and after the bonus.** Within a half, compare on-ball distance (m), contest distance (m), reach-in and steal attempts per possession before and after the defending team's 7th and 10th team fouls. | Estimates with n and 95% interval per team per game; pooled per season. | `team_half_pressure` | Coaches tell players to stop reaching once in the penalty; this checks if they do. |
| new-DF-A8 | Shall | **Get-back onset per defender.** After each change of possession, each defender's onset time (s): first moment his velocity toward his own rim exceeds 2.0 m/s; plus a "late get-back" flag when onset > 1.5 s while the ball is advanced (proposal thresholds). | Onset recomputes from tracks; flag agrees with coach labels on ≥ 80% of 100 cases; off-screen defenders marked estimated (R-DT-07). | `transition_defense.onset_s`, `.late_flag`, `.estimated` | The "watch him jog back" clip is the most common transition-defense teaching moment. |
| new-RF-A13 | Shall | **Whistle latency.** For each whistle with a visible contact or violation frame, the time from that frame to the whistle (from audio, R-RF-01) and to the official's signal (pose), with the calling official's role. | Latency within ±0.1 s of a hand label on 100 calls; distribution per crew per game. | `fouls.contact_frame`, `.whistle_latency_s`, `.signal_latency_s` | Officials talk about patience and "seeing the whole play"; latency is the measurable part. |
| new-RF-A14 | Should | **Calls by official role and area.** Per crew and per official, calls split by the caller's role (lead, trail, centre) and by court area (r, θ sectors), as of date, with n. | Recomputes from `fouls` and `official_positions`; values with n < 30 calls flagged. | `official_call_map` | Explains crew patterns without judging calls. |
| new-RF-A15 | Should | **Unwhistled contact candidates (review only).** Flag plays with contact-like signatures (two opponents within 0.3 m with an abrupt deceleration ≥ 3 m/s² of the ball handler or shooter, proposal) and no whistle within 1.0 s; they enter the review queue only and are never published as "missed calls"; a reviewer labels contact seen yes or no. | Flags reviewed with a label; published outputs contain 0 "missed call" claims (lint). | `contact_candidates` (review-only, private) | Crew consistency studies need the denominator of uncalled contact; publishing it as officiating grades would be wrong and unfair. |
| new-VZ-A1 | Should | **Half-time packet.** One page per team: score, four factors, runs, foul trouble, bonus and timeouts, set and coverage mix, top 3 possessions by value change with clip references, each number linked to frames. | Produced within 600 s after the first-half video is available on the 3 pilot games (proposal); 100% of counting stats equal the official half-time box. | `results/<game_id>/halftime_packet` | Half-time is the analyst's main deadline; it proves the system is usable, not just accurate. |
| new-VZ-A2 | Should | **Post-game notes sheet.** Ten notes per game, each a one-sentence finding with its number, n, definition and clip reference; ranked by value change and novelty. | Produced within 3,600 s after the full video is available (proposal); passes new-DQ-A2. | `results/<game_id>/postgame_notes` | The notes sheet is what producers, writers and staff actually read. |
| new-VZ-A3 | Shall | **Clip index.** Every event, action and possession row carries clip in and out times (video s), a key frame (screen moment, help moment, release), and links to replay segments of the same play (new-VI-3). | 100% of event rows have clip times; an audit of 100 pulled clips finds the event in ≥ 95%. | `clip_index` (row_ref, in_s, out_s, key_frame, replay_ids) | "Show me" is the first thing a coach says to any number. |
| new-VZ-A4 | Should | **Telestrator freeze-frame.** For any possession and moment, a top-down diagram of all 10 players and the ball, with arrows of the next 2 s of movement and labels from the broadcast vocabulary layer. | Renders from the state tables for any frame of a processed game; positions match the state within 0.1 m. | viz template `freeze_frame` | The top-down still is the rights-safe replacement for drawing on broadcast video (R-RG-02 tightened). |
| new-PR-A1 | Should | **Leverage and swing plays.** Per possession, the leverage (expected change in win probability given the state) and per play the realised change; the 5 largest swing plays per game listed with clip references. | Recomputes from `wp_live`; top-5 list per game; leverage calibrated with the WP model (R-PR-11). | `possessions.leverage`, `swing_plays` | "Biggest play of the game" segments need a number, not a feeling. |
| new-PR-A2 | Should | **Prediction drivers.** Each pre-game prediction lists its top 3 drivers in points of margin (e.g. rating gap, home court, rest, availability), summing with the remainder to the predicted margin. | Drivers plus remainder equal the predicted margin within 0.1 points on 100% of predictions. | `predictions.drivers` | A matchup predictor nobody can explain will not be quoted. |
| new-EN-A1 | Should | **Latency budget per output tier.** Tier 1 (PBP plus scorebug: score, runs, fouls, four factors) ≤ 300 s after a video segment is available; tier 2 (tracking: transition, coverages, sets) ≤ 3,600 s per half; measured and logged per run. | Latency logged per output; met on ≥ 2 of the 3 pilot games or the gap and cause reported. | `run_record.json` latency fields | Numbers that arrive after the segment airs are only research. |
| new-CX-A9 | Should | **Storyline and fact register.** Pre-game facts (streaks, milestones, records, head-to-head, coach wins) each with source, as-of time and the query that verifies it. | 0 facts without a source and as-of; every fact re-verified at T−3,600 s. | `storyline_facts` | Storylines are the most quoted and the least checked numbers on a broadcast. |

Count: **28 new requirements** (17 Shall, 11 Should).

---

## 6. The 10 most valuable outputs of the whole project (this perspective)

1. **A possession log that reconciles with the official box**: possessions, chances, types as multi-label flags (ATO, SLOB, BLOB, transition by named definition), lineups corrected from video (R-SY-04, R-SY-06, new-SY-A4, new-DQ-A2).
2. **Ball-screen coverage and set identification in coach vocabulary**, each with a clip and a confidence (R-DF-16, R-ST-05, new-MD-A6, new-VZ-A3).
3. **Transition both ways**: who ran, who got back and when, passed-up breaks with the value at stake (R-TR-09, R-TR-24, R-TR-26, new-DF-A8).
4. **Calibrated win probability with leverage and swing plays** (R-PR-11, new-PR-A1).
5. **Run tracker and run stoppers**: three named run definitions, what ended each run, what changed (R-MD-17, new-EV-A14, R-CC-02).
6. **Adjustment log**: scheme changes with triggers and lags, hot-shooter responses, mismatch hunting, zone recognition, half-time changes (R-DF-19, new-DF-A6, new-ST-A9, new-ST-A10, R-CH-06).
7. **Foul and officials context, without grading officials**: bonus and foul trouble every second, foul-trouble decisions, crew tendencies pace-adjusted (R-SR-03, new-CC-A5, R-RF-06, new-RF-A14).
8. **Shot quality vs shot making per player**, calibrated (R-VL-04, new-VL-1).
9. **Half-time packet and post-game notes**, every number linked to frames (new-VZ-A1, new-VZ-A2).
10. **Pre-game matchup card**: prediction with drivers, availability as of tip, storylines with sources (R-CX-18, new-PR-A2, new-CX-A9).

## 7. The 10 biggest risks (this perspective)

1. **Wrong player identity on a published number** (jersey misread, back-turned, same-number pairs): one public error discredits the product (R-ID-*).
2. **Possession and lineup counts that disagree with the box** because of PBP substitution timing, team and dead-ball rebounds, or condensed-replay cuts (R-DQ-06, new-SY-A4, R-VI-02).
3. **Wrong vocabulary**: a hedge called a drop, a "run" with no definition, two clutch definitions; coaches stop listening (R-DF-06, R-MD-17, R-CO-04, new-MD-A6).
4. **Off-ball blind spots**: weak-side help and tag defenders out of frame bias every defensive number toward "nobody helped" (R-VI-05, R-DT-07).
5. **Clock and scorebug timing** in the last 60 s: lag of about 2 s, tenths, shot clock off and on (2-11.2, 2-11.8); end-game analysis lives here (R-SY-01, new-SY-A5).
6. **Small samples presented as tendencies** and narrative words ("momentum") without tests (R-VA-05, R-PC-11, R-GU-04).
7. **Rights**: broadcast clips or frames in public material (R-RG-01, R-RG-02).
8. **Officials' data read as grading officials**: reputational and unfair without the official's view; keep review-only (new-RF-A15).
9. **Rule-edition drift**: timeout formats, challenge limits and throw-in spots changed in 2025-26; invariants written for an older edition throw false breaks (R-IV-10 rewrite, new-RL-1).
10. **Latency**: if tracking-level outputs take days, the product is a research archive, not a game tool (new-EN-A1).

## 8. The 10 most important requirement changes (this perspective)

1. **new-DQ-A2 Published-number gate**: nothing leaves without reconciling with the official box.
2. **R-MD-17 rewrite**: three named run definitions (unanswered, broadcast "a–b", register net ≥ 8 in 120 s), never merged.
3. **R-IV-10 rewrite**: timeout format per 5-14.8–10; one extra 30-s timeout per extra period in televised games, not 75 s.
4. **R-DF-06 rewrite**: publish coverages at the coarse level; fine labels only at confidence ≥ 0.8.
5. **new-SR-A6 Flow-state machine** with allowed transitions tied to rule numbers.
6. **R-SR-11 tighten (Should → Shall)**: late-game situation flags (two-for-one, foul-up-3, foul to extend, shot clock off, fouls to give).
7. **new-SY-A4 Substitution times from video**: lineups that agree with what happened.
8. **new-VZ-A3 Clip index** on every event row: "show me" for every number.
9. **new-MD-A6 Broadcast vocabulary layer**: coach term, broadcast phrase, banned synonyms.
10. **R-VI-01 loosen and R-MB-04 rewrite**: frame targets stated for the 29.97 fps footage that actually exists.

## 9. Open questions for Aldemir (one line each)

1. Is a half-time deadline (600 s after the first-half video is available) a goal for the pilot, or is the project offline-only this season?
2. May the staff-facing sheets show official names next to crew tendencies, or crew IDs only?
3. Which broadcast run threshold should the "a–b" run use for display: net ≥ 6 (proposal) or ≥ 8 (register)?
4. Should foul-trouble thresholds follow the analyst convention in R-MD-16 (2 / 3 before 10:00 of the 2nd half / 4) or a coach-supplied rule for MSU?
5. Is a coach available to rate 50 broadcast phrases (new-MD-A6) and 100 timeout purposes (new-CC-A6)?

## Sources opened for this review

Repo (read 2026-10-18):
- `scratchpad/brief_panel.md`, `brief_improve.md`, `brief_003.md` (task briefs).
- `scratchpad/live_doc2/requirement_ids.md` (518 IDs) and `changes_since_1038.md`.
- `coord/requirements_inbox/006-data-dictionary-and-first-games.md` (pilot footage specs, scorebug lag, decisions list).
- `docs/data/game_ontology_coverage.md` and inbox 007 proposals (`new-*` IDs and highest numbers).
- `config/invariants.yaml` (constants, shot-clock reset table, free-throw awards, rule references).
- `docs/research/beliefs_register.md` (B1, B2, C3, C4, C5, summary table).
- `docs/research/transition_full.md` (sections 3.4, 4).
- `docs/research/load_thresholds.md` (items 5–8; Stone 2022 NCAA speeds as cited there).
- `docs/taxonomy/defense_full.md` (F3 ball-screen coverages, F7.5 closeouts, F11.6 scheme-change detection).

Rules (read 2026-10-18):
- `docs/rules/PRMBB_RulesBook.pdf` 2026-27, via the pdftotext copy `scratchpad/rules.txt`: 2-11 (shot-clock operator, 2-11.1–2-11.6), 5-10 (starting clocks), 5-11.2–5-11.4, 5-14 (timeouts, Arts. 1–13), 6-2 (jump ball), 11-4 (coach's challenge), 5-15.1.e; other rule numbers as cited in `config/invariants.yaml`.
- `docs/rules/2025-26PRMBB_RulesChanges.pdf` (pdftotext): proposals 1–10 (one shot clock, continuous motion, 7-3.2.b throw-in spots, 9-15.2 hands on ring, 10-2.8.a music, coach's challenge).

No web pages were opened for this review. Values tagged [ANALYST HEURISTIC] are unverified working conventions; values attributed to studies are as cited in the repo documents named above (not re-opened here).
