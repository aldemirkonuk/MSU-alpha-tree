# Perspective review: NBA front-office data scientist

Date: 2026-10-18. Status: PROPOSAL ONLY. Nothing here edits the live requirements doc, `config/`, `schema/` or any earlier file (add-only rule, brief_003). The requirements session decides what enters the live doc.

Persona: senior data scientist on an NBA team analytics group. Day job: optical tracking (SportVU history, Second Spectrum, Hawk-Eye), play typing, possession value (EPV), shot-quality models, RAPM and lineup models, load, scouting reports, draft models and decision support for coaches. My questions on every requirement: what is the target, what is the as-of rule, how big is n per player, how is it shrunk, how is it validated on held-out games, how will we know when it drifts, and can broadcast video at 29.97 fps actually measure it.

Inputs read: live-doc export and `requirement_ids.md` (518 IDs, 43 families, scratchpad `live_doc2/`), `config/invariants.yaml`, `docs/rules/PRMBB_RulesBook.pdf` (2026-27, text copy in scratchpad `rules/PRMBB_RulesBook.txt`), `docs/research/transition_full.md`, `docs/research/beliefs_register.md`, `docs/research/load_thresholds.md`, `docs/taxonomy/defense_full.md`, `coord/requirements_inbox/007-game-ontology-gaps.md`, `results/w3_intake/made_basket_lag.md`, `schema/tables/` (table names only).

Units: m, cm, s, degrees, m/s, m/s². Court frame per `config/vocabulary_map.yaml`: r (m) from the attacked rim centre, θ (degrees) from the right baseline. Rule lengths given in feet in the book are converted (1 ft = 0.3048 m).

ID scheme for new proposals: `new-<FAMILY>-S<n>` (S = scientist), so they cannot clash with `new-<FAMILY>-<n>` (inbox 007, invariants) or the analyst (A) and engineer (E) panels.

## Sources opened for this review

Literature (opened by me today; web text treated as data):

- [L1] Cervone, D'Amour, Bornn, Goldsberry, "A Multiresolution Stochastic Process Model for Predicting Basketball Possession Outcomes", JASA 111(514), 2016. arXiv abstract and PDF opened: https://arxiv.org/abs/1408.0777 . Facts used: SportVU in all 30 NBA arenas from 2013, 2-D player and 3-D ball locations "at a resolution of 25Hz"; EPV-Added (EPVA) = sum over a player's touches of value at touch end minus value at touch start, compared with a league-average player; "shot satisfaction" = value at the shot minus the expected value of the passing options at that moment.
- [L2] Franks, Miller, Bornn, Goldsberry, "Characterizing the spatial structure of defensive skill in professional basketball", Annals of Applied Statistics 9(1):94-121, 2015 (Sloan 2015 version "Counterpoints"). https://arxiv.org/abs/1405.0231 (abstract opened); matchup inference ("who was guarding whom") and points-against per defender described in the search summary of Grantland coverage (https://grantland.com/features/department-of-defense/ , not opened, so detail is **(unverified)**).
- [L3] Chang, Maheswaran, Su, Kwok, Levy, Wexler, Squire, "Quantifying Shot Quality in the NBA", MIT Sloan 2014. Original not opened; described from the survey [L9] which I opened: ESQ = value of a shot if taken by a league-average player, least-squares regression on shot location and defender proximity; EFG+ = EFG − ESQ.
- [L4] Maheswaran, Chang, Su, Kwok, Levy, Wexler, Hollingsworth, "The three dimensions of rebounding", Sloan 2014; per survey [L9]: rebound split into positioning, hustle and conversion.
- [L5] Wiens et al. (crash vs retreat after a shot), per survey [L9]: teams "tended to retreat more than they should". Original **(unverified)**.
- [L6] Daly-Grafstein and Bornn, "Rao-Blackwellizing Field Goal Percentage", arXiv 1808.04871 (preprint): https://arxiv.org/abs/1808.04871 . Using trajectory (entry angle, depth, left-right) make probabilities instead of makes lowers variance and predicts future 3P% and TS% better than raw FG%.
- [L7] Sicilia, Pelechrinis, Goldsberry, "DeepHoops", arXiv 1902.08081 (working paper): https://arxiv.org/abs/1902.08081 . Probability of each terminal action at each moment from preceding player and ball locations; reported well calibrated.
- [L8] DeepSportradar-v1 (Van Zandycke et al., ACM MMSports 2022), arXiv 2208.08190: https://arxiv.org/abs/2208.08190 . Basketball tasks: ball 3-D localisation from a single calibrated image, camera calibration, player instance segmentation, re-identification.
- [L9] Gudmundsson and Horton, "Spatio-Temporal Analysis of Team Sports — A Survey", arXiv 1602.06994 (PDF opened, text extracted): https://arxiv.org/pdf/1602.06994 .
- [L10] Sill, "Improved NBA Adjusted +/- Using Regularization and Out-of-Sample Testing", Sloan 2010; Sloan abstract via search: ridge regularisation "nearly doubles" APM accuracy measured out of sample. https://www.sloansportsconference.com/research-papers/improved-nba-adjusted-using-regularization-and-out-of-sample-testing (search summary only).
- [L11] McIntyre, Brooks, Guttag, Wiens, "Recognizing and Analyzing Ball Screen Defense in the NBA", Sloan 2016: classifier on SportVU labels each ball screen over / under / switch / trap; 270,823 screens over four seasons (Sloan abstract via search; the KDD talk says five seasons and > 300,000; accuracy figure not seen). https://www.sloansportsconference.com/research-papers/recognizing-and-analyzing-ball-screen-defense-in-the-nba
- [L12] Le, Carr, Yue, Lucey, "Data-Driven Ghosting using Deep Imitation Learning", Sloan 2017: league-average "ghost" defenders generated from tracking, compared with actual defence by expected-goal value (soccer). https://studios.disneyresearch.com/2017/03/03/data-driven-ghosting-using-deep-imitation-learning/ (listing via search).
- [L13] Miller and Bornn, "Possession Sketches: Mapping NBA Strategies", Sloan 2017: dictionary of short spatially registered actions, LDA-style model groups possessions by offensive structure. https://www.sloansportsconference.com/research-papers/possession-sketches-mapping-nba-strategies (abstract via search).
- [L14] ESPN, 9 Mar 2023, "NBA to use Hawk-Eye tracking system": Hawk-Eye (Sony) replaces Second Spectrum's single-point "center of mass" tracking from 2023-24 with pose tracking. https://www.espn.com/nba/story/_/id/35818363/nba-use-hawk-eye-tracking-system-follow-players-ball . Camera count, joint count, frame rate and accuracy are **not** in the article; the persona brief's "cm accuracy" for pro tracking is therefore **(unverified)** here.

Repo evidence reused (already cited there): NCAA D-I men's peak game speeds guards 7.04 ± 0.39, forwards 6.63 ± 0.52, centres 6.23 ± 0.33 m/s (`docs/research/load_thresholds.md`, line 25, Kinexon, 10 players); Hoop-Math and Inpredictable start-type evidence (`transition_full.md` §6); timeout and run evidence (`beliefs_register.md` B1, B2); scheme-switch triggers and lags (`defense_full.md` F11); measured scorebug lag (`results/w3_intake/made_basket_lag.md`).

---

## 1. THINK: game flow under the 2026-27 NCAA men's rules

### 1.1 Why a data scientist cares about the state machine

Every model I would build (possession value, shot quality, lineup effects, reaction effects) is conditioned on the game state. If the state machine is wrong, labels are wrong, and errors look like signal. The two most dangerous errors are (a) a possession or chance boundary in the wrong place (it moves points between start types and corrupts PPP by start type), and (b) a clock value inferred wrongly (it corrupts shot-clock features, the strongest late-clock covariate in shot quality).

### 1.2 Possession state machine

States are those of R-MD-02 / R-SR-05 / R-SR-06 (ball control: team A, team B, contested, in flight, throw-in pending, dead). Our possession rule: a possession ends only when the other team gains control (brief_003; R-MD-04). A chance ends at a shot that hits the ring and is rebounded by the offence (new chance, same possession).

| From | Event | To | Governing rule (2026-27 book) | Clocks |
|---|---|---|---|---|
| Dead (period start) | Toss leaves official's hand | Jump ball, no team control | 6-1.2.a, 6-2.2; no team control during a jump ball 4-9.4.a | Game clock starts on a legal touch of the toss 5-10.2.b; shot clock starts on initial control 5-10.3.b |
| Jump ball | Player secures control | Team control (possession 1); arrow set to the other team | 6-3.4 | Shot clock 30 s |
| Dead | Ball at disposal of thrower-in | Throw-in pending (team control for the thrower's team) | 6-1.2.b; 4-9.2.c | Game and shot clocks stopped; 5-s throw-in count 7-6.6, 9-4.1.d |
| Throw-in pending | Legal touch inbounds after release | Live, team control | 5-10.2.a, 5-10.3.a | Game clock starts; shot clock starts (value per 2-11.6 cause table in `config/invariants.yaml`) |
| Live, team control in backcourt | Ball reaches frontcourt | Frontcourt control | 9-10 (10-s count), 9-12 (backcourt) | 10-s backcourt count; game and shot clocks run |
| Live, frontcourt | Holding with defender within 1.83 m | Closely guarded count | 4-17.2, 9-14 | 5-s count (holding only) |
| Live | Try leaves the hand | In flight, no team control | 4-9.3, 4-9.4.c | Clocks run; a whistle does not kill the ball until the try ends 6-6.1 |
| In flight | Goal made | Dead; opponent throw-in from end line | 6-5.1.a; R-IV-08 | Game clock keeps running except ≤ 59.9 s in the 2nd half / extra periods (2-10.12, 5-11.9); shot clock to 30 on next control 2-11.6.b.1 |
| In flight | Miss touches the ring, rebound secured by defence | Change of possession | 4-30.1; 2-11.6.b.4 | Shot clock 30 |
| In flight | Miss touches the ring, offence secures | New chance, same possession | 2-11.6.d.1 | Shot clock flat 20 s whatever was left |
| In flight | Air ball, offence secures | Same chance continues | no reset (try did not touch the ring) | Shot clock keeps running (R-MB-07) |
| Live | Whistle: foul | Dead; free throws or throw-in by bonus state | 5-11.1.a; 8-2.1, 8-2.2; 10-1 Penalty | Clocks stop; shot clock per 2-11.6.b.5 / c.1 / a.5 |
| Live | Whistle: violation | Dead; opponent throw-in | 5-11.1.c; 7-3 | Shot clock 30 (change of control) or per cause |
| Live | Held ball | Dead; arrow throw-in | 6-4.1.a, 6-4.2; arrow flips 6-3.2 | Shot clock per 2-11.6.a.4 / b.3 / d.4 |
| Dead | Ball at disposal of free-thrower | Free-throw sequence | 6-1.2.c; 8-1 ... 8-7 | Clocks stopped; 10-s release 8-5.1.a; lane at most 6 players 8-4.4 |
| FT (last, missed, ring) | Legal touch on court | Live rebound | 5-10.2.c | Game clock starts; shot clock on control (20 if offence, 30 if defence) |
| Live or dead | Timeout granted | Dead | 5-11.3, 5-11.4; player request when live; coach request when live only in the last 2:00 of the 2nd half and extra periods 5-11.3 | 30 s / 60 s / 75 s by format (5-14.4, 5-14.8 ... 5-14.10) |
| Dead at or after media mark | First dead ball at or after 16:00, 12:00, 8:00, 4:00 (or 15/10/5 format) | Media timeout | 5-14.10.c, 5-14.10.e (a dead ball created ≤ 30 s before a mark by a timeout, review or challenge becomes the media timeout) | Dead ball stoppage |
| Live | Time expires | End of period (try in flight completes) | 5-7.2, 5-7.3 | Red light / zeros decide 5-7.2.a |
| End of 2nd half, tied | — | Extra period, 300 s, no change of baskets, jump ball | 5-9.2, 5-9.3, 6-2.1 | Each extra period extends the 2nd half for team fouls 5-9.4 |
| Half time | — | 2nd half starts by arrow throw-in at the division line | 6-3.6 | Team fouls reset (per half) |

Additional states the engine must carry: coach's challenge and monitor review (Rule 11-2 ... 11-4), injury and blood stoppages (5-11.2.b, 5-11.8), correctable error and timing-mistake appeals (5-11.5, 5-12).

### 1.3 Clocks that run, and when

- Game clock: runs only in live play (R-IV-05); starts on a legal touch (5-10.2); after a made field goal keeps running except in the last 59.9 s of the 2nd half and extra periods (5-11.9). Minimum 0.3 s off on a touch in the last 59.9 s (5-10.2.d).
- Shot clock: 30 s on change of control; 20 s flat after offensive control following ring contact (2-11.6.d); max(20, remaining) after defensive fouls or kicked balls with a frontcourt throw-in (2-11.6.c); off when the game clock is below a shot-clock period, reactivated at 20 s in 2-11.6.d cases (2-11.2, 2-11.8). All 38 cause rows are in `config/invariants.yaml` `shot_clock_reset_table`.
- Counts that officials run (not displayed): 10-s backcourt (9-10), 5-s closely guarded (9-14), 5-s throw-in (7-6.6), 10-s free throw (8-5.1.a), 3-s lane (9-9.2, not during throw-in control 9-9.2.a).
- Timeout and intermission clocks: 30/60/75 s timeouts; one-minute intermission before each extra period (5-9.2).

### 1.4 Where the flow is decided (decision points)

These are the moments my models condition on. Each should be a stored snapshot (see new-MD-S1).

1. Secure of a defensive rebound, steal or loose ball: push or pull back (TR-16, TR-24).
2. Inbound after a make or made last FT: press or not; push or walk up (TR-14, DF-18).
3. Half-court crossing and first frontcourt catch: alignment and set call (ST-19).
4. Every ball screen at the screen moment (ST-20): coverage choice (DF-16), handler read.
5. Every catch: catch-and-shoot, drive, pass or hold (CO-01).
6. Drive start and paint arrival: help or stay; kick-out target.
7. Post entry: double or play straight (DF-07).
8. Shot release: crash or retreat for all five attackers, box out for all five defenders (EV-08, new-VL-S3).
9. Foul situations late: foul to stop the clock, foul up 3, foul to give (PE-07, SR-11).
10. Dead balls: substitution, timeout, scheme change (CH-06, DF-19).
11. End of clock: last-shot hold, two-for-one window (`two_for_one_window_s: [33, 45]`, proposal).

---

## 2. UNDERSTAND: how teams react to actions

The table lists the main triggers, typical responses, how fast they happen, and what to store. "Latency" is my working expectation [HEURISTIC] unless a source is named. For every reaction the data-science point is the same: a reaction effect is only measurable against what would have happened without the reaction. Naive before/after comparisons are biased because teams react when things go badly (regression to the mean; `beliefs_register.md` B2: > 95% of EuroLeague timeouts called during a negative run; NBA matched estimate ATT −0.35 points over the next minute, Gibbs, Elmore and Fosdick).

| Trigger | Offensive response | Defensive response | Latency | What to store / how to estimate |
|---|---|---|---|---|
| Made basket | Inbound fast and push (Izzo) or walk up into a set | Press after makes (team policy), match up, get back | Inbound release 2-5 s after the make; push decided by the first pass (≤ 2 s after inbound) | Inbound lag, half-court crossing time (TR-14, TR-21); press P(press given make) vs base rate (`defense_full.md` F11.4) |
| Miss / long rebound | Outlet and run; leak-outs | Crash vs get back; first defender to the rim | Secure → outlet 0.5-1.5 s; first defender at r ≤ 1.5 m within 3-4 s (DF-20) | Crash/retreat per player at release (new-VL-S3, after [L5]); numbers state 10 Hz (TR-22) |
| Live-ball turnover | Immediate attack; best start type (steal 0-10 s eFG 62.3% vs 50.9% after DREB, Hoop-Math 2023-24, `transition_full.md` §6.2) | Sprint back, stop the ball, take foul | 0-3 s | Start type and numbers advantage at secure; take-foul candidates (TR-25) |
| Foul puts opponent in the bonus (7th, 10th team foul) | Attack the rim, seek contact | Less physical on-ball, more zone or drop; avoid reach-ins | Next possession | Foul rate and contest distance before vs after the bonus, within team (matched on time and score) |
| Timeout (called) | ATO set; lineup change | Scheme change (box-and-1, zone) | Effect on the next possession (ATO); scheme change on the restart | Timeout record (EV-15); estimate with matched runs, never pre/post (new-HY-S1) |
| Ball screen | Handler reads coverage: reject, split, snake, pocket pass, pull-up | Coverage (drop, hedge, ice, switch, blitz; DF-16); low man tags the roller | Coverage visible 0.3 s after the screen moment (DF-16); low-man tag 0.5-1.0 s | Coverage × outcome table (new-DF-S1), cf. [L11] |
| Post entry | Post move, kick-out, re-post | Front / three-quarter / behind (DF-07); double from the passer or baseline | Double arrives 0.5-1.5 s after the catch | Post touches; double time; kick-out openness |
| Drive | Kick to the open spot, dump to the dunker spot | Help from the low man or nail; stunt and recover | Help onset 0.3-0.8 s after drive start | Drive start, help arrival time and distance (new-EV-S1) |
| Skip pass | Catch-and-shoot or attack the closeout | Closeout: speed, distance, contest at release | Closeout 0.8-1.5 s | Closeout distance and speed (DF-08), contest at release |
| Zone look | Overload, flash the high post, short corner, zone screens | Zone rotations; match-up rules | Recognition by the 1st-2nd pass (offence) | Scheme state (DF-04) and offence alignment change after detection |
| Press | Press break: middle flash, sideline outlet, reversal | Trap at the sideline / half-court, fall-back | Fall-back 4-8 s after inbound | Press set-up time vs inbound lag (DF-18) |
| Foul trouble (2 in H1, 4 in H2) | Attack the player in foul trouble | Protect: switch matchup, zone, passive coverage | Next dead ball for subs; immediate for coverage aggression | Within-player comparison (inbox 007 new-DF-5); Izzo near the bottom of the D-I 2-foul usage list (`defense_full.md` F11.4) |
| End of clock (shot clock ≤ 5 s; game clock ≤ 35-45 s) | Iso or high ball screen; two-for-one | Switch everything (`defense_full.md` F11 shot-clock trigger) | Shot clock 10 ± 2 s change-point | Late-clock flag in shot quality; switch rate by shot clock |
| Scoring run (net ≥ 8 in 120 s, shared definition) | Coach timeout, lineup change | Scheme change | Timeout usually within 1-2 possessions of the run threshold | Runs are near random (`beliefs_register.md` B1); reaction effect only by matched design |
| Lineup change | New sets suited to personnel | Matchup re-assignment; scheme change for a lineup (Baylor 1-3-1 with Omier, F11.4) | Next live ball | P(scheme given on-court five); RAPM pair effects (CH-01) |
| Opponent hot shooter | Keep feeding him | Top-lock, switch matchup, trap, deny | 1-3 possessions | Defender distance to that shooter vs his baseline; hot hand itself weak (beliefs A1) |

What a front office actually extracts from this table is a **reaction catalogue** (new-CH-S1): trigger, response, latency in s and possessions, and a baseline hazard of the same response without the trigger. That is what turns "they always go zone after a timeout" from a scouting impression into a number with an interval.

---

## 3. ANALYZE: how each of them moves

### 3.1 What pro tracking gives vs what broadcast video gives

| Property | NBA optical tracking | Our broadcast video (measured where stated) |
|---|---|---|
| Rate | 25 Hz players and ball (SportVU, [L1]); Hawk-Eye pose from 2023-24 [L14], rate not published in the source I opened | 29.97 fps constant (UConn file, `made_basket_lag.md`); 1 frame = 0.033 s |
| Coverage | All 10 players and the ball, every frame, fixed cameras | Main wide camera follows the ball; off-screen players in transition and weak side; replays, close-ups and ad breaks (R-VI-03, R-VI-04) |
| Position accuracy | Not stated in sources opened (**(unverified)** "cm") | Target ≤ 0.5 m (R-PL-13); not yet measured |
| Body | Hawk-Eye pose (hands, limbs) [L14] | 2-D pose from one view; depth ambiguous; occlusion in the paint |
| Ball height | 3-D ball [L1] | 3-D from a single calibrated image is possible with the known ball size [L8], untested on our feed |
| Scoreboard | Official data feed | Scorebug lags the make by 1.96 s mean (1.50-2.60 s, n = 10, digit change start; `made_basket_lag.md`) |
| Sample | ~1,230 games a season | ~13 MSU games with footage plus opponents' games only vs MSU (R-OS-05) |

Consequence I want written into the requirements: every derived metric must state which of these limits it depends on, and a metric whose value moves more than 10% when position noise of 0.5 m or frame rate of 30 fps is simulated is "not estimable from broadcast" (new-VA-S5).

### 3.2 Movement signatures by role

Numbers marked [S] are sourced in the repo or literature listed above; [H] are my heuristic starting values for calibration on our data.

| Role | Movement signature that matters | Typical values | Measure, rate and accuracy needed | Broadcast feasibility | Metric that captures his value |
|---|---|---|---|---|---|
| Ball handler | Speed with the ball, change of direction, first-step burst, stop-and-pop deceleration, angle of attack on the screen | Peak game speed guards 7.04 ± 0.39 m/s [S]; COD heading change ≥ 45° within 0.5 s (inbox 007 new-PL-2) [H]; decel to pull-up −3 to −4 m/s² [H] | Position ≤ 0.3 m, ≥ 10 Hz after smoothing; heading ± 10° | Good when on the main camera (ball-following) | EPVA per touch [L1]; shot satisfaction [L1]; turnover cost (VL-11) |
| Screener | Arrival speed, set time, angle of the screen relative to the handler's path, contact, re-screen | Strict screen: screener ≤ 0.3 m/s for ≥ 0.5 s within 1.2 m of the user's path (ST-17) [S, repo]; angle 0-180° to the defender's path [H] | Body orientation ± 20°; contact from pose | Medium: stacks and occlusion | Screen assists; points per chance on his screens vs expected (VL-09) |
| Roller / popper | Roll speed, depth of roll, separation from the tagger at catch, pop distance to the arc | Roll 3-5 m/s [H]; pop to r ≥ 6.75 m in 1.0-1.5 s [H] | Position ≤ 0.5 m | Medium | Roll-man PPP vs coverage (new-DF-S1) |
| Spacer / shooter | Relocation after a drive (lift, drift), distance to the nearest defender at catch and at release, catch-to-release time | Contest bins 0-0.6, 0.6-1.2, 1.2-1.8, > 1.8 m [H, cf. NBA tracking 0-2/2-4/4-6/6+ ft]; catch-and-shoot touch ≤ 2 s and 0 dribbles [H] | Position ≤ 0.3 m for the shooter and the nearest defender at release; release time ± 1 frame | Good on the ball side; corners at the far sideline are often cut | Shot-making above expected (inbox 007 new-VL-1, [L3] EFG+), gravity (VL-06) |
| Cutter | Cut start, speed, angle to the rim, timing after a screen or a defender's head turn | 4-6 m/s [H]; cut onset within 0.5 s of the defender's ball-watch [H] | 10 Hz, ≤ 0.5 m | Weak side often off-screen | Points created per cut; passes received open |
| Post | Seal position (r, θ), duration of the seal, catch location, moves | Seal at r 1.5-3.5 m [H]; 3-s lane limit (9-9.2) [S] | Pose (torso, arms), position ≤ 0.3 m | Good (near the ball) but occluded | Post-up PPP; double-team draw rate |
| Rim protector | Distance to the rim when the ball enters the paint; vertical contest; deterrence | First back at r ≤ 1.5 m (DF-20) [S, repo]; restricted area 1.22 m (4-31) [S] | Position ≤ 0.3 m; jump timing | Good when the play is at the rim | Rim deterrence (shots not taken), FG% allowed at the rim vs expected [L2] |
| On-ball defender | Distance to handler, pickup point, slide speed, contest at release, recovery after the screen | Closely guarded 1.83 m (4-17.2) [S]; pickup point (inbox 007 new-DF-3); lateral slide 2.5-4 m/s [H] | Position and torso orientation | Good | Matchup points allowed shrunk [L2]; contest quality |
| Help defender | Gap position, help onset after a drive, recovery and closeout | Help onset 0.3-0.8 s [H]; closeout 0.8-1.5 s [H] | 10 Hz, ≤ 0.5 m | Weak-side defenders often off-screen | Rotation delay (DF-08); ghost deviation (new-DF-S2, [L12]) |
| Tag / low man | Tag the roller, then recover to the corner | Tag arrives within 0.5-1.0 s of the roll [H] | Position at the screen moment + 1 s | Medium | Roll PPP allowed; corner 3 allowed |
| Rebounder | Position at rim contact, box-out, crash speed | Positioning, hustle, conversion [L4] | Positions at release and at rim contact; ball landing point | Medium (crowded paint) | Rebound decomposition (new-VL-S2) |
| Officials (lead, trail, centre) | Coverage area, distance and angle to the call, rotations | Three officials (2-1.1.a; R-IV-02); calling distance and angle (inbox 007 new-RF-9) | Position ≤ 1 m | Often off-screen | Not a team metric; context for foul-rate models (RF-06) |
| Coaches and bench | Timeout and substitution timing; scheme calls | Coach live-ball timeout only in the last 2:00 (5-11.3) [S] | PBP and dead-ball video | PBP strong | Reaction catalogue (new-CH-S1), ATO PPP |

---

## 4. SYNTHESIZE: how this perspective adjusts the requirements

### 4.1 Verdict method and counts

I reviewed all 518 IDs. 43 carry an explicit change below (plus R-PC-11, listed as an explicit keep). Every other ID is **keep** (no data-science objection, or outside my remit). Counts per family (keep / tighten / loosen / rewrite / drop):

| Family | IDs | keep | tighten | loosen | rewrite | drop |
|---|---|---|---|---|---|---|
| R-RR | 9 | 9 | 0 | 0 | 0 | 0 |
| R-DQ | 10 | 9 | 1 | 0 | 0 | 0 |
| R-DS | 15 | 15 | 0 | 0 | 0 | 0 |
| R-RG | 11 | 11 | 0 | 0 | 0 | 0 |
| R-FD | 12 | 12 | 0 | 0 | 0 | 0 |
| R-PC | 16 | 12 | 4 | 0 | 0 | 0 |
| R-MD | 20 | 19 | 1 | 0 | 0 | 0 |
| R-ID | 15 | 15 | 0 | 0 | 0 | 0 |
| R-VI | 16 | 15 | 0 | 1 | 0 | 0 |
| R-CG | 11 | 10 | 0 | 0 | 1 | 0 |
| R-DT | 19 | 17 | 1 | 0 | 1 | 0 |
| R-BL | 8 | 7 | 1 | 0 | 0 | 0 |
| R-GT | 5 | 5 | 0 | 0 | 0 | 0 |
| R-SY | 10 | 10 | 0 | 0 | 0 | 0 |
| R-TR | 28 | 27 | 0 | 0 | 0 | 1 |
| R-EV | 16 | 13 | 3 | 0 | 0 | 0 |
| R-AU | 4 | 4 | 0 | 0 | 0 | 0 |
| R-RF | 7 | 6 | 1 | 0 | 0 | 0 |
| R-ST | 26 | 24 | 2 | 0 | 0 | 0 |
| R-DF | 21 | 17 | 2 | 1 | 1 | 0 |
| R-VL | 13 | 5 | 5 | 1 | 2 | 0 |
| R-CH | 8 | 7 | 1 | 0 | 0 | 0 |
| R-CC | 5 | 4 | 1 | 0 | 0 | 0 |
| R-GU | 6 | 6 | 0 | 0 | 0 | 0 |
| R-SR | 15 | 15 | 0 | 0 | 0 | 0 |
| R-IV | 16 | 15 | 1 | 0 | 0 | 0 |
| R-SB | 4 | 3 | 1 | 0 | 0 | 0 |
| R-MB | 7 | 6 | 1 | 0 | 0 | 0 |
| R-CX | 19 | 19 | 0 | 0 | 0 | 0 |
| R-PL | 17 | 14 | 1 | 2 | 0 | 0 |
| R-CO | 8 | 6 | 2 | 0 | 0 | 0 |
| R-OS | 5 | 5 | 0 | 0 | 0 | 0 |
| R-EN | 8 | 7 | 1 | 0 | 0 | 0 |
| R-CD | 5 | 5 | 0 | 0 | 0 | 0 |
| R-PR | 11 | 11 | 0 | 0 | 0 | 0 |
| R-PE | 13 | 12 | 1 | 0 | 0 | 0 |
| R-MK | 33 | 33 | 0 | 0 | 0 | 0 |
| R-HR | 12 | 12 | 0 | 0 | 0 | 0 |
| R-VZ | 7 | 7 | 0 | 0 | 0 | 0 |
| R-CS | 10 | 10 | 0 | 0 | 0 | 0 |
| R-VA | 9 | 8 | 1 | 0 | 0 | 0 |
| R-HY | 7 | 7 | 0 | 0 | 0 | 0 |
| R-PT | 1 | 1 | 0 | 0 | 0 | 0 |
| **Total** | **518** | **475** | **32** | **5** | **5** | **1** |

Keeps I want to name because they are already right by front-office standards: R-RR-02 (game-level bootstrap), R-DS-04 and R-FD-06/07 (point-in-time ratings), R-CX-02/03/09 (shrinkage, out-of-sample tests with FDR, no leakage), R-PR-03/04/05 (beat the ratings model and the close, walk-forward, calibration), R-PE-08/09/10 (population-first fitting, parameter uncertainty, levels kept only if they beat the level below), R-VA-06/07/08, R-HY-01..05, R-HR-07 (frozen gold), R-TR-11/18 (definitions never merged), R-MK-07 (prediction frozen before the market snapshot).

### 4.2 Changes to existing IDs

Format: ID · verdict · proposed text · acceptance · lands in · why.

**R-DQ-02 · tighten.** Physical limits come from one config key shared with R-IV-13 and R-EN-03: player speed ≤ 9.0 m/s, |acceleration| ≤ 8.0 m/s² over windows ≥ 0.2 s; positions inside the court ± 1.0 m. Acceptance: one key `physics.*` in `config/invariants.yaml` read by all three checks; a unit test fails if any check hard-codes a limit. Lands: `config/invariants.yaml` constants.physics. Why: D-I peak game speeds are 6.2-7.0 m/s [S]; a 10 m/s / 12 m/s² limit lets most identity swaps through. Three requirements with three different limits will drift.

**R-PC-05 · tighten.** Athletic block values are reported only from stints with ≥ 70% on-camera time (R-PL-14) across ≥ 3 games; top speed = 95th percentile of 1-s smoothed speed, not the single maximum; jump height only after R-CG-11 passes ± 0.05 m on 50 hand-measured jumps. Acceptance: card shows n games, covered minutes and the value's SD; empty when the gates fail. Lands: `profile_snapshots`, `players`. Why: single maxima are dominated by tracking spikes.

**R-PC-06 · tighten.** Every shooting rate is a beta-binomial posterior with the prior fit on the D-I population for that sector × ring × shot type (PBP shot locations where available), stored with n, posterior mean and 80% interval; catch-and-shoot and pull-up use the definitions in R-EV-07. Acceptance: for 20 random player-zones the posterior recomputes from stored counts and prior parameters within 1e-6. Lands: `player_shooting_sector_ring`. Why: a 6.75 m three for a 40-attempt player is mostly prior.

**R-PC-07 · tighten.** "Pass difficulty" is replaced by measured fields: pass distance (m), lane openness (m, nearest defender to the pass line), receiver's nearest-defender distance at catch (m). Potential assist as defined in R-EV-03. Acceptance: no free-text "difficulty" column; all three fields filled on ≥ 90% of passes with both players mapped. Lands: `passes`.

**R-PC-10 · tighten.** Role clusters are soft memberships fitted on the D-I population where PBP features allow, with bootstrap stability (adjusted Rand index ≥ 0.80 over 200 game-level resamples); unstable clusters are not shown. Acceptance: stability reported per cluster per season. Lands: `profile_snapshots.role_cluster_*`.

**R-PC-11 · keep** (listed because drive direction and finishing hand need n: shown with n per R-VA-05).

**R-MD-17 · tighten.** Pre-possession win probability comes from a model whose training data end before the game's date (as-of), stored with model version. Acceptance: leakage test new-VA-S2 passes for the WP column. Lands: `state_second.wp_pre`.

**R-VI-01 · loosen.** Capture standard: native resolution ≥ 1080p at the source's own constant frame rate; 29.97 fps is the expected case and fully supported; 60 fps is used when the source offers it. Every timing requirement states its tolerance in frames at the file's rate. Acceptance: intake report lists fps; no Shall fails only because the file is 29.97 fps. Why: both audited files are 29.97 fps (`made_basket_lag.md`); a "60 preferred" Shall invites silent failures.

**R-CG-08 · rewrite.** Every position row stores x, y to 0.01 m and its 1-σ uncertainty (m) from the court mapping and the ground-point estimate; reports round to 0.1 m and show only values with σ ≤ 0.5 m (others marked low confidence). Acceptance: σ calibrated so that 90-98% of hand-labelled ground points fall inside the 95% region on gold-v1. Lands: `player_positions.pos_sigma_m`, `frame_geometry`. Why: storing to 1 cm without an error bar invites false precision; contest-distance bins are 0.6 m wide.

**R-DT-07 · tighten.** Off-screen position estimates carry a 95% region whose empirical coverage on re-appearing players is 90-98%; models that use positions take the off-screen estimate only through a flag and never as observed. Acceptance: coverage computed on ≥ 500 re-appearances. Lands: `track_exits`, `player_positions.is_imputed`.

**R-DT-08 · rewrite.** Velocity, acceleration and heading per player from smoothed positions, with the filter and window named (R-PL-10); acceleration computed over ≥ 0.2 s windows; jerk not computed. Acceptance: hand-timed runs (R-PL-13) give speed bias ≤ 0.3 m/s and SD ≤ 0.5 m/s. Why: R-PL-12 already says jerk is not measurable from video; R-DT-08 still asks for it.

**R-BL-04 · tighten.** Shot release, pass release and catch times within ± 2 frames of the hand label on 300 labelled events per type. Acceptance as stated. Why: catch-to-release time is a shot-quality feature; it needs a tolerance.

**R-EV-03 · tighten.** Potential assist = completed pass whose receiver attempts a field goal or draws a shooting foul with ≤ 1 dribble and ≤ 2.0 s after the catch [H, to calibrate]. Hockey assist as already defined. Acceptance: rule recomputes from `passes` and `shots` on 100% of rows. Lands: `passes.is_potential_assist`.

**R-EV-07 · tighten.** Each shot stores: release r, θ; shot family (catch-and-shoot = 0 dribbles and touch ≤ 2.0 s; pull-up = ≥ 1 dribble; post-up; putback ≤ 2.0 s after an offensive rebound; transition flag per R-TR-09); dribbles and touch time; nearest defender distance (m) and angle (degrees, defender in front = within ± 45° of the shooter-to-rim line) at release and at catch; second-nearest defender distance; closing speed of the nearest defender over the 0.5 s before release (m/s); shooter speed and heading at gather; shot clock and game clock. Acceptance: all fields on ≥ 90% of shots with shooter and nearest defender mapped (σ ≤ 0.5 m); missing values marked, never imputed for the contest. Lands: `shots`. Why: these are the features that carry shot quality in the pro literature [L3][L1]; without fixed definitions catch-and-shoot rates cannot be compared across seasons.

**R-EV-08 · tighten.** For every missed try: positions of all 10 players at release and at rim contact, ball landing point (r, θ) when visible, box-outs, and who secured it; enough to compute positioning, hustle and conversion [L4]. Acceptance: fields filled on ≥ 80% of rebounds where ≥ 8 players are on camera. Lands: `rebounds`, `box_outs`.

**R-RF-06 · tighten.** Crew tendencies are shrunk toward the D-I mean with the number of games each official worked as weight; reported with n games and interval. Acceptance: posterior recomputes from stored counts. Why: a referee with 12 games has a noisy foul rate.

**R-ST-08 · tighten.** "Value at the boundary" comes only from the validated value layer (new-VL-S4); until that passes, the field is null, not a placeholder.

**R-ST-10 · tighten.** Labelled set sample: per family, ≥ 50 instances from ≥ 5 different games for evaluation, split by game (no game in both train and test). Acceptance: split file lists game IDs. Why: 30-50 possessions from 1-2 games measures memorisation of one game plan.

**R-DF-01 · tighten.** Matchup per defender per second as a posterior probability over the five attackers, from a model in which a defender's expected position is a weighted mix of his attacker, the ball and the rim [L2]; stored as top-1 and probability. Acceptance: top-1 agrees with hand labels on ≥ 85% of 300 defender-seconds sampled across ≥ 5 games; probabilities calibrated (ECE ≤ 0.05).

**R-DF-04 · loosen.** Scheme state per second where ≥ 8 players are mapped; otherwise per possession phase (transition, half-court) with the scheme carried and flagged `carried`. Acceptance: share of seconds with observed vs carried scheme reported per game. Why: per-second labels on frames where the weak side is off-screen are guesses.

**R-DF-06 · rewrite.** Ball-screen coverage per screen in two levels (R-DF-16): coarse class (contain/drop, show/hedge, two-on-ball, switch) always; fine coverage (13 classes) only when the coarse class is confident and the fine classifier passes ≥ 75% accuracy on ≥ 300 labelled screens from ≥ 5 games; otherwise fine = unknown. Acceptance: coarse ≥ 85% accuracy on the same set. Why: the NBA reference classifier [L11] used four classes on full tracking; 13 classes on broadcast is not realistic at first.

**R-DF-19 · tighten.** Scheme-change triggers are stored as features; the "not working" trigger (opponent PPP over the first 10 half-court possessions) is stored with its n and interval, and no report states that a trigger caused a change without the matched comparison in new-HY-S1. Why: PPP over 10 possessions has a standard error near 0.35 points [H].

**R-VL-01 · rewrite.** Possession value in layers (new-VL-S4): (1) PBP-state value every second for every D-I game (score, time, start type, shot clock, fouls); (2) location value when the ball and shooter are mapped; (3) full-tracking value at 10 Hz only when ≥ 8 players and the ball are mapped. Each layer stored with its coverage flag. Acceptance: each layer calibrated on held-out games (10-bin ECE ≤ 0.03 points per possession scale) and each higher layer beats the one below on held-out log loss of the terminal outcome. Lands: `possession_value`. Why: a single 10 Hz model trained on frames the camera chose to show is biased (missing not at random); layers make the video's added value measurable.

**R-VL-02 · tighten.** Value change per action credited by a written rule, and credits for each action sum to the value change within 1e-6. Acceptance: test on all rows of `value_credits`.

**R-VL-04 · rewrite.** Shot quality = probability of make and expected points for a league-average D-I shooter (shooter identity excluded, after [L3] ESQ) from the R-EV-07 fields, trained on population data in two layers: location-only from D-I PBP shot locations, contest-aware from our tracked shots. Acceptance: on held-out games, contest-aware layer improves log loss over location-only by ≥ 1% and has 10-bin ECE ≤ 0.02; the contest coefficient has the expected sign with 95% interval excluding 0. Lands: `shots.xfg_loc`, `shots.xfg_track`, `shots.xpts_*`. Why: without a shooter-agnostic layer, shot-making and shot quality cannot be separated (inbox 007 new-VL-1 depends on this).

**R-VL-05 · tighten.** Decision quality is computed only when all passing options are mapped (≥ 8 players), as value of the option taken minus the expected value of the passing options (Cervone's "shot satisfaction" [L1]); reported per player with n and interval. Acceptance: n per player shown; values with n < 100 decisions are descriptive.

**R-VL-06 · tighten.** Gravity = displacement of defenders from their expected (ghost) position given the offensive configuration (new-DF-S2), not raw distance. Acceptance: ghost model passes its own validation first.

**R-VL-07 · tighten.** Matchup points created and allowed are shrunk toward position-group priors with possessions matched as weight; shown only above the R-VA-05 minimum count.

**R-VL-12 · tighten.** Every player-level estimate states its prior (population, position group), the effective sample size and the shrinkage factor. Acceptance: three fields present on every row of player-level outputs.

**R-VL-13 · loosen.** The neural sequence model is optional (Should stays); it may be trained on our own tracks only; pre-training on research-only public tracking makes the model research-only (R-RG-04). Acceptance: model card states training data licence.

**R-CH-01 · tighten.** Lineup and pair effects: ridge (RAPM) with informed priors from box and PBP data, penalty chosen by cross-validation over whole games, accuracy reported on held-out games against a prior-only baseline [L10]. Acceptance: held-out RMSE of stint margin per 100 possessions beats the prior-only model.

**R-CC-03 · tighten.** "Player pulled within 30 s of his turnover" is compared with that player's substitution hazard in matched moments without a turnover (same period, minutes into the stint, foul count). Acceptance: report gives observed vs expected pull rate with interval.

**R-IV-13 · tighten.** Physics limits from the shared key (see R-DQ-02): speed ≤ 9.0 m/s, |acceleration| ≤ 8.0 m/s² over ≥ 0.2 s windows; ball handler within 1.5 m of the ball while in control.

**R-SB-03 · tighten.** Start window 4.0 s, not 15 s, re-estimated after each game as the 99th percentile of measured lags + 0.5 s. Acceptance: window value logged per game. Why: 10 of 10 measured lags were 1.50-2.60 s.

**R-MB-04 · tighten.** Make frame within ± 1 frame at the file's frame rate (± 0.033 s at 29.97 fps) of the hand label. Why: the audit could fix the make to ± 1 frame (`made_basket_lag.md`); "± 3 frames at 60 fps" no longer describes our files.

**R-PL-01 · loosen.** Becomes a Should view on R-PL-09 bins (already superseded by R-PL-11).

**R-PL-03 · tighten.** Within-game decline is estimated within player with possession type (transition, half-court, dead) and score state as covariates, because sprint share depends on how many transition possessions occurred. Acceptance: model with covariates reported beside the raw decline.

**R-PL-07 · loosen.** Shot physics (release height, arc, entry angle) is research-only until R-CG-11 passes ± 0.05 m; release time (catch to release) stays a Shall inside R-EV-07.

**R-CO-02 · tighten.** Reaction times are reported as per-player distributions with n ≥ 50 events, with effective resolution stated (frame 0.033 s plus smoothing lag, expected 0.10-0.15 s [H]); single events are never shown as a player's reaction time.

**R-CO-04 · tighten.** Pressure performance is shrunk toward the player's own non-pressure performance and the population pressure effect; n shown.

**R-EN-03 · tighten.** "No player faster than 10 m/s" reads the shared physics key (9.0 m/s).

**R-PE-11 · tighten.** Video features enter the engine only after a walk-forward comparison on the same held-out games shows the engine with video features beats it without (log loss and CRPS, R-PE-10 rule).

**R-VA-05 · tighten.** The minimum-count rule uses game-clustered standard errors, and for player-level splits the shrunk posterior's interval; the 1.1 points-per-chance spread is replaced by the value measured on our data after the first 5 games.

**R-TR-06 · drop.** Covered by R-TR-26 (value of each break state) and R-VL-01 layers; two requirements for the same number invite two implementations.

### 4.3 New requirements

| ID | Tier | Requirement | Acceptance (units) | Lands in | Why this persona needs it |
|---|---|---|---|---|---|
| new-VA-S1 | Shall | A held-out game list per season is registered before any model is fitted: ≥ 20% of games with footage, chosen by game (not possession), stratified by home/away and opponent tier; no hyperparameter, threshold or template is tuned on them. | Register file with date and hash exists before the first fit; every run record lists whether held-out games were touched (must be "no" except final evaluation). | `registry/holdout_games.csv` (new), `run_records.holdout_touched` | Holdout-game validation is the only honest check with ~13 MSU games. |
| new-VA-S2 | Shall | Temporal leakage test for every model: features for time t use only data with timestamp ≤ t (frames, events, ratings); smoothing filters used as features are causal (no centred windows); a test perturbs all data after t and requires identical predictions at t. | Test passes for 100% of model features; failing features listed in the run record. | `run_requirement_results` | Centred smoothing and end-of-game aggregates are the most common hidden leaks. |
| new-VA-S3 | Shall | Reliability per player-level metric: split-half (odd vs even games) correlation across players, and the n (events) at which reliability reaches 0.70; player-level displays hide metrics below that n. | Table with reliability and n70 per metric per season. | `dq_reports` (metric_reliability section) | Tells coaches which numbers mean something for a player this season. |
| new-VA-S4 | Shall | Model monitoring: after each new game, calibration (10-bin ECE) and input drift (PSI per feature, R-DQ-08) are recomputed for every deployed model; alert when rolling 10-game ECE > 0.05 or any key feature PSI > 0.25. | Alert log per game; zero silent model updates. | `run_records`, `dq_reports` | Camera, arena and opponent change every game; models degrade quietly. |
| new-VA-S5 | Shall | Broadcast error budget: each derived metric is recomputed on simulated degradations (position noise σ = 0.3, 0.5, 1.0 m; 30 fps; weak-side players dropped as in our coverage maps) using licence-compatible full tracking or our own best frames; metrics that move > 10% at our measured σ are labelled "not estimable from broadcast". | Report with the change (%) per metric per degradation. | `docs/` report + `dq_reports` | Separates what college broadcast can estimate from what only pro tracking can. |
| new-VL-S1 | Shall | Shot-making vs shot quality kept apart: per shooter, points minus xPts (R-VL-04, shooter-agnostic) and, when ball trajectory is available, a trajectory-based make probability per shot to reduce variance [L6]. | Stored per shot; per shooter shrunk with n (complements inbox 007 new-VL-1). | `shots.p_make_traj`, `profile_snapshots` | Raw FG% over 13 games is mostly noise. |
| new-VL-S2 | Shall | Rebound decomposition for every missed try: positioning (rebound probability per player from positions at rim contact), hustle (change from release to rim contact), conversion (secured given position) [L4]. | Probabilities sum to 1 per miss within 1e-6; calibrated ECE ≤ 0.05 on held-out games. | `rebounds` (new columns), `value_credits` | Box-score rebounds credit the finisher, not the box-out. |
| new-VL-S3 | Should | Crash vs retreat decision per attacker at each missed-shot release: crashed (moved toward the rim ≥ 1.0 m in 1.0 s) or retreated, with the ORB probability gained and the transition-defence cost (opponent value after a DREB) [L5]. | Decision label agrees with hand labels on ≥ 85% of 200 cases; value fields filled when ≥ 8 players are mapped. | `rebounds`, `transition_phases` | Directly answers Izzo's "crash the glass" question with its cost. |
| new-VL-S4 | Shall | Value layers stored side by side (PBP state, location, full tracking) with the coverage flag for each possession-second, so the video's added value is measured as the improvement of each layer over the one below on held-out games. | Log-loss and ECE per layer per season; a layer that does not beat the one below is not used in reports. | `possession_value.layer`, `possession_value.coverage_flag` | Makes R-VL-01 testable and the pitch claim ("what video adds", R-PT-01) honest. |
| new-DF-S1 | Shall | Ball-screen coverage outcome table: per screen, coarse and fine coverage, handler action (pull-up, drive, pass to roller, pass to perimeter, reject, reset), chance result and points; coverage effect estimated with adjustment for handler, screener, location (r, θ) and shot clock. | Table complete for 100% of detected screens; effect estimates with game-clustered 95% intervals. | `screens` (outcome columns) | Coverage-by-outcome is the most used scouting table in the NBA [L11]. |
| new-DF-S2 | Should | Ghost defence: a model of where an average defender would stand given the 5 attackers and the ball, trained on population tracks we hold; per defender-second, deviation from the ghost (m) and the value change associated [L12][L2]. | Ghost model out-of-sample position error reported; deviations only where σ ≤ 0.5 m. | `defensive_matchups.ghost_dev_m` | Turns "he was out of position" into a counterfactual number. |
| new-DF-S3 | Shall | Contest fields are "unknown" when the shooter or nearest defender is not mapped with σ ≤ 0.5 m at release; the share unknown is reported per game and models are fitted with an explicit unknown level, never with imputed contest. | Unknown share per game in the run record. | `shots.contest_known` | Imputing contest from off-screen estimates makes shot quality circular. |
| new-CH-S1 | Shall | Reaction catalogue: one row per detected reaction (trigger from §2's list, response type, team, latency in s and possessions) plus, for each trigger type, the baseline rate of the same response in matched moments without the trigger. | Every scheme change, timeout and substitution linked to the nearest preceding trigger (or "none"); baseline rates per team-season. | `reaction_events` | "How teams react" is the core of the brief; without baselines it is anecdote. |
| new-HY-S1 | Shall | Any claim that a reaction (timeout, scheme change, substitution, press) changed outcomes uses a registered identification design: natural experiment (media timeouts set by the clock, as in beliefs B1), matching on score, time, run size and lineups, or a regression-discontinuity on rule thresholds (bonus at the 7th foul); pre/post comparisons are never reported as effects; sensitivity to unmeasured confounding stated (Γ). | Hypothesis row names the design and Γ; reviewer check fails rows without them. | `hypothesis_results.design`, `hypothesis_results.gamma` | Timeouts are called when things go badly; naive estimates are biased (beliefs B2). |
| new-MD-S1 | Shall | Decision-point snapshots: at each decision point of §1.4 (secure, inbound release, first frontcourt catch, screen moment, catch, drive start, post entry, release, rim contact, dead ball), store the 10 positions with σ, ball, both clocks, score, fouls, timeouts, lineups and the coverage score. | Snapshot count per possession recomputes from events; ≥ 95% of decision points have a row. | `configuration_snapshots` (extend with decision_point_type) | Gives every model the same, auditable conditioning set. |
| new-EV-S1 | Shall | Drive response record: at drive start and at paint arrival, the first help defender (ID), help arrival time (s), help distance (m), the kick-out target and its nearest-defender distance at the catch (m). | Fields filled on ≥ 80% of drives with ≥ 8 players mapped. | `drives` | Help timing is the main defensive reaction to the most common action. |
| new-PL-S1 | Shall | Measurement error carried into every speed- and acceleration-derived metric: bias and SD from hand-timed runs and gold positions (R-PL-13), propagated by simulation into the reported interval. | Every load and athletic metric shows an interval that includes measurement error. | `load_stint_bins`, `accel_efforts`, `profile_snapshots` | Coaches will act on a "top speed down 0.4 m/s" that may be noise. |
| new-ST-S1 | Should | Unsupervised action dictionary (possession sketches, [L13]) learned from our tracks beside the role templates, used to find recurring structures the templates miss and to audit template matches. | Dictionary versioned; share of chances whose sketch cluster disagrees with the template match reported per game. | `movement_primitives`, `set_instances` | Templates written by people miss what opponents actually run. |
| new-PC-S1 | Shall | Every player-card metric displays n, reliability (new-VA-S3), posterior interval and a D-I population percentile when a population source exists; metrics with only MSU-game data are labelled "MSU games only". | Fields present on 100% of displayed card metrics. | `profile_snapshots` | Prevents opponent cards built on 1-2 games against MSU from looking like season truths. |

New requirements: 19 (16 Shall, 3 Should).

---

## 5. The 10 most valuable outputs of the project (this persona's ranking)

1. **Population PBP possession and chance tables with rule-validated clocks for all D-I games** (R-SY-06, R-SY-08/09, R-IV-07). Large n; every other model sits on it.
2. **Walk-forward, calibrated pre-game engine against the closing line** (R-PE, R-PR-03..05, R-MK-06). The one result with enough games to be decisive.
3. **Layered shot-quality model with shooter-agnostic xPts and shrunk shot-making** (R-VL-04 rewrite, new-VL-S1, inbox 007 new-VL-1).
4. **Ball-screen coverage recognition and coverage-by-outcome table for MSU and opponents** (R-DF-16, new-DF-S1).
5. **Transition state machine with numbers state and value at stake** (R-TR-08/09/22/26). MSU's identity; measurable from broadcast because the camera follows the ball.
6. **Reaction catalogue with baselines and causal estimates** (new-CH-S1, new-HY-S1).
7. **Matchup and help-defence measures** (R-DF-01 tightened, new-EV-S1, new-DF-S2).
8. **Rebound decomposition and crash-vs-retreat value** (new-VL-S2, new-VL-S3).
9. **Lineup and pair effects (RAPM with priors) for all of D-I from PBP** (R-CH-01).
10. **Broadcast error budget: what college video can and cannot estimate** (new-VA-S5). Useful to MSU and publishable.

## 6. The 10 biggest risks

1. **Missing-not-at-random coverage.** The broadcast camera follows the ball, so weak-side players and transition defenders are missing exactly when they matter; value and defence models fit on visible frames are biased. Mitigation: coverage flags, layers (new-VL-S4), unknown levels (new-DF-S3).
2. **Small samples.** About 13 MSU games with footage, and opponents only in their games against MSU (R-OS-05); player-level splits will be noise. Mitigation: population priors, shrinkage, reliability gates (new-VA-S3, new-PC-S1).
3. **Leakage.** End-of-season ratings, centred smoothing, post-game aggregates in pre-game cards. Mitigation: R-CX-09, new-VA-S2, R-CX-18 frozen cards.
4. **Position error vs contest bins.** σ of 0.5-1.0 m is the size of a contest bin; contest effects may wash out. Mitigation: R-CG-08 rewrite, new-VA-S5.
5. **Timing resolution.** 0.033 s frames plus smoothing lag make reaction-time metrics coarse. Mitigation: R-CO-02 tightened, distributions only.
6. **Label noise and single labeller.** Sets and coverages labelled by one person; gold small. Mitigation: R-HR-06 blind repeats, R-HR-10 second labeller, game-split evaluation (R-ST-10).
7. **Confounded reaction effects.** Timeouts and scheme changes follow bad runs; regression to the mean fakes effects. Mitigation: new-HY-S1.
8. **Domain shift from pro models.** NBA-trained detectors, value models and coverage classifiers meet a 30 s clock, a 6.75 m arc, more zone and different camera packages. Mitigation: fine-tune on our labels; validate on held-out college games only.
9. **Licence contamination.** Research-only tracking data used for pre-training makes downstream models research-only. Mitigation: R-RG-04, R-VL-13 loosened with model cards.
10. **Forking paths.** Hundreds of features, definitions and splits. Mitigation: R-HY-01 registration, R-VA-07 corrections, null results reported (R-VA-08).

Also material: identity errors propagate straight into player credits (R-ID-03/09 gate everything in VL), and scorebug-based state is offset by ~2 s (R-SB-03 tightened).

## 7. The 10 most important requirement changes (this persona)

1. R-VL-04 rewrite: shooter-agnostic, layered shot quality with defined contest features.
2. R-VL-01 rewrite + new-VL-S4: value in layers with coverage flags; video must beat PBP on held-out games.
3. new-VA-S1: held-out game register before any fit.
4. new-VA-S2: temporal leakage test (causal filters).
5. R-EV-07 tighten: fixed catch-and-shoot / pull-up / contest definitions.
6. R-CG-08 rewrite + new-DF-S3: position uncertainty stored; contest unknown rather than imputed.
7. R-DF-06 rewrite: coarse coverage first, fine only when validated.
8. new-HY-S1: identification design required for any reaction effect.
9. new-CH-S1: reaction catalogue with baseline rates.
10. new-VA-S5: broadcast error budget deciding what is estimable.
