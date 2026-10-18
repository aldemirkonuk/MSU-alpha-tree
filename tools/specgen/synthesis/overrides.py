# Hand-merged verdicts for IDs touched by two or more inputs, or by a cross-perspective conflict.
# Keys: v = verdict, tier, text, acc, by = drivers (Q quality review, A ESPN analyst, E data engineer,
# S team data scientist, R rules layer config/vocab + court constants, G gap closures round 2, I inbox 007 / invariants),
# k = conflict IDs, into = merge target, split = child IDs, note.
O = {}
def o(i, v, text, acc, by, k=(), tier=None, into=None, split=None, note=None):
    O[i] = dict(v=v, text=text, acc=acc, by=list(by), k=list(k), tier=tier, into=into, split=split, note=note)

o('R-RR-03', 'split',
  'R-RR-03a Shall: every Shall fail and Should miss has a failure analysis with error rate per slice: the 9 named technical slices plus 6 game-situation slices (transition vs half-court, after timeout, shot clock <= 5 s at the event, last 240 s of a half, media segment, camera shot type during the event) and a confusion matrix. R-RR-03b Shall: the same file lists the 20 worst cases (frame index, clip link), one cause from the fixed list {data, label, model, threshold, upstream gate, compute} and the next fix with expected gain in metric points.',
  '100% of failed IDs have both parts; every slice shows n; slices with n < 50 are listed, not flagged; a linter checks the cause value is in the fixed list (count of invalid causes = 0).',
  'QA')
o('R-DQ-01', 'tighten',
  'Shall: every external field with a second source is cross-checked per game and written as one row per (game, field, source pair) to dq_cross_source with tolerance and result: final score and every official box counting stat per player and team (official box vs ESPN vs CBBD) exact; jersey numbers exact; officials exact after crosswalk; lines <= 0.5 points (R-MK-22a); each disagreement resolved (value chosen, reason logged) or flagged.',
  '100% of two-source fields of processed games checked; 0 disagreements left neither resolved nor flagged; tolerances read from config; disagreement rate per field per season reported (%).',
  'QEA')
o('R-DQ-02', 'tighten',
  'Shall: contracts are generated from schema/tables/*.yaml (type, unit, range, nullable, enum, PK uniqueness, FK existence) and run on every write; ranges include positions inside the court + 1.0 m, game clock 0-1200 s per half and 0-300 s per extra period, shot clock 0-30 s; physical limits are not restated here but read from the one config key physics.* shared with R-IV-13, R-EN-03 and R-DT-08 (see conflict K01).',
  '104 of 104 specs produce a contract; CI fails on a spec without type, unit (or "none") and range; 0 writes bypass the checker; one seeded out-of-range row per rule is rejected (100%); a unit test fails if any check hard-codes a limit.',
  'QES', k=['K01'])
o('R-DQ-06', 'split',
  'R-DQ-06a Shall: per game, sum of possession points = final score per team; FGA = FGM + missed FG per team and player. R-DQ-06b Shall: team minutes = 200 + 25 per extra period. R-DQ-06c Shall: every chance ends in exactly one terminal event from the config list {made FG (and-one closes after its free throw), last free throw made, defensive rebound (including team and dead-ball rebounds as the scorer records them), turnover, offensive rebound after ring contact (opens the next chance), shot-clock reset inside the possession (defensive foul or kicked ball, max(20, left)), held ball with arrow throw-in, period end}.',
  'a, b: 100% of games pass or go to quarantine with the failing identity named; c: 0 chances with zero or two terminal events per game.',
  'QEA', k=['K08'])
o('R-DQ-08', 'tighten',
  'Shall: for each key field (list in config, R-EN-06) the per-game distribution is reported as quantiles from game 1; the population stability index against the running baseline (10 quantile bins, initial value, to calibrate) gives a drift verdict only once >= 10 games of the same source tier exist; PSI > 0.25 (proposal) raises a drift flag.',
  'Games 1-10: quantiles only (0 PSI verdicts); from game 11: a seeded shifted game raises the flag and an unchanged replay of a baseline game does not.',
  'QE', k=['K17'])
o('R-FD-08', 'rewrite',
  'Shall: officials per game: the two or three on-court officials (Rule 2-1.1.a) with name, crew position (referee, umpire), crew-chief flag, source and as-of UTC; mid-game replacements logged with game clock; a missing name is "unknown", never guessed.',
  '100% of processed games list 2 or 3 officials (3 expected in D-I) or a flagged unknown, cross-checked under R-DQ-01.',
  'QAR')
o('R-PC-05', 'tighten',
  'Shall: athletic block per player from our tracking: top speed (m/s, 95th percentile of 1-s smoothed speed, not the single maximum), peak acceleration and deceleration (m/s², only where the propagated sigma passes the K03 gate), lateral slide speed (m/s), change-of-direction time (s), jump height (m, only after R-CG-11 passes +/- 0.05 m on 50 hand-measured jumps); each with n (efforts), games, covered minutes and a 95% interval; only stints with >= 70% on-camera time (K13) across >= 3 games; else "provisional" or empty.',
  '100% of values carry n and interval; top speed within the measured tracking speed error of a reference (radar or hand-timed sprint) on >= 20 efforts (tolerance from R-PL-13); empty when the gates fail.',
  'QS', k=['K03', 'K13'])
o('R-PC-06', 'split',
  'R-PC-06a Shall: shooting block per player: make rates by sector and ring, catch-and-shoot vs pull-up (R-EV-07 definitions), rim, mid-range, three, free throws; each a beta-binomial posterior with the prior fitted on the D-I population for that sector x ring x shot type, stored with n, posterior mean and 80% interval. R-PC-06b Should (hypothesis, registered under R-HY): free-throw % improves the three-point prior.',
  'a: for 20 random player-zones the posterior recomputes from stored counts and prior parameters within 1e-6; 100% of rates carry prior and n; b: pre-registered test with log-loss change on held-out games.',
  'QS')
o('R-PC-07', 'rewrite',
  'Shall: playmaking block per player: assist rate, potential assists (R-EV-03 definition), hockey assists, turnover rate by type, and three measured pass fields replacing "pass difficulty": pass distance (m), lane openness (m, nearest defender to the pass line) and receiver nearest-defender distance at the catch (m); each with n.',
  'Recomputation equals stored values (0 differences); assist and turnover rates from official PBP within 0.5 percentage points of the box (initial value, to calibrate); the three pass fields filled on >= 90% of passes with both players mapped; 0 free-text "difficulty" columns.',
  'QS')
o('R-PC-11', 'tighten',
  'Shall: every tendency (drive direction, finishing hand, shot-clock use, pass-or-shoot by zone, help frequency) stores n, as-of date and a shrunk estimate; the display hides a tendency below its reliability n (n70 from the reliability study new-VA-S3) and, until that study exists, below n = 30 events.',
  '100% of tendency rows carry n, as_of and shrunk value; the display layer shows 0 tendencies below the threshold.',
  'QAS', k=['K12'])
o('R-MD-13', 'split',
  'R-MD-13a Shall: 5-min window ID, a last-240-s flag (named late_240, used for the under-4 media segment and late-game slices) and the single clutch flag from config (<= 300 s left in the second half or any extra period and margin <= 5 points) per record. R-MD-13b Shall: media-timeout segment ID following Rule 5-14.10 and the game\'s media format (16/12/8/4 or 15/10/5 marks; a team timeout, review or challenge within 30 s before a mark becomes the media timeout, 5-14.10.e; first second-half team timeout takes media length, 5-14.10.d); boundaries from the observed media timeouts, not from the marks.',
  'a: recomputation from the clock equals stored values (0 differences); b: media timeout times agree between video, scorebug and PBP on 100% of pilot games and segment boundaries match PBP media timeouts in >= 95% of segments (initial value, to calibrate).',
  'QAR', k=['K06'])
o('R-MD-16', 'tighten',
  'Shall: per player per record: personal fouls so far and a foul-trouble label from a config table of (fouls, period, seconds left) cut-offs; default table (proposal): 2 in the first half; 3 with > 600 s left in the second half; 4 with <= 600 s left or in an extra period; the legacy 2/4 rule kept as a named alternative; plus seconds on the bench since entering foul trouble and re-entry time.',
  'Counts equal PBP at 100% of fouls; labels recompute from the config table (0 differences); on-screen foul graphics read as weak labels (new-VI-7) agree on >= 95% of graphics read.',
  'QA', k=['K10'])
o('R-MD-17', 'rewrite',
  'Shall: score state: margin, lead changes, times tied, largest lead per team; runs stored under three named config definitions, never merged: (a) unanswered points since the opponent\'s last point; (b) broadcast run "a-b" = the window ending now and starting right after a score by either team that maximises the running team\'s net points, displayed only when net >= the config threshold (default 8, K05); (c) register run = net >= 8 points in a rolling 120 s of game clock (beliefs register B1/B2), the primary definition for hypotheses; plus pre-possession win probability from a model trained only on data dated before the game (as-of), with model version.',
  'All three recompute from score_events within 0 points; (b) matches on-screen run graphics on >= 90% of graphics read (weak label); the leakage test (new-VA-S2) passes for the WP column.',
  'ASG', k=['K05'])
o('R-VI-01', 'split',
  'R-VI-01a Shall: native >= 1080p without rescaling (lower: tier 2 in the registry). R-VI-01b Shall: constant frame rate at the source\'s own rate; 29.97 fps is the expected and fully supported case (1080p60 does not exist for the 2025-26 condensed replays); 59.94 fps is used when a source offers it; every timing requirement states its tolerance in frames at the file\'s rate. R-VI-01c Shall: original audio track kept.',
  'a: probe height >= 1080 px or tier-2 tag; b: frame-interval spread < 1 ms; fps listed in the intake report; 0 Shall failures caused only by 29.97 fps; c: audio stream present with duration within 0.1 s of video.',
  'QEAS')
o('R-VI-02', 'tighten',
  'Shall: intake report per file: length vs expected, dropped and frozen frames, letterboxing, overlays, edit type (full broadcast, condensed replay, highlights), the cut map of video stretches vs game-clock ranges (stored in the cut-map table of new-VI-E1) with every removed dead-ball span typed (timeout, media timeout, free-throw routine, review, half time) and flagged not_in_footage, and the live-play share in main wide.',
  'Both pilot games: cut map covers 100% of the 2,400 s of game clock; every game-clock discontinuity >= 1 s found against a hand check; frozen live-play segments listed (Louisville 2.3 s at 2,302.6 s); 0 removed spans imputed as "nothing happened".',
  'EA')
o('R-CG-08', 'rewrite',
  'Shall: every position row stores x, y to 0.01 m and its 1-sigma uncertainty position_sigma_m (m) from the court mapping and the ground-point estimate; reports round to 0.1 m and show only values with sigma <= 0.5 m (others marked low confidence).',
  'On gold-v1 hand-labelled ground points per court zone: the stated 68% interval covers 60-76% and the 95% region covers 90-98%.',
  'ES')
o('R-DT-07', 'tighten',
  'Shall: off-screen position estimate per missing player stored at 10 Hz (not per frame) during live play, with a 95% region whose empirical coverage on re-appearing players is 90-98%; downstream models take it only through an is_imputed flag, never as observed.',
  '10 Hz rows for 100% of missing player-seconds of live play; coverage computed on >= 500 re-appearances is 90-98%.',
  'ES', k=['K15'])
o('R-DT-08', 'split',
  'R-DT-08a Shall: velocity (m/s) and heading (degrees) per player from smoothed positions of a named body point (pelvis_floor or ankle_mid), filter and window named in config (R-PL-10), each with a propagated 1-sigma column. R-DT-08b Should: acceleration (m/s²) over windows >= 0.5 s with propagated sigma, released for analysis only where the K03 resolvability gate passes; jerk is not computed.',
  'a: hand-timed runs (R-PL-13) give speed bias <= 0.3 m/s and SD <= 0.5 m/s on >= 20 runs; filter named and sigma present on 100% of rows; b: stationary players show acceleration noise below 2.0 m/s² in >= 95% of seconds before release; 0 jerk columns.',
  'QES', k=['K01', 'K03'])
o('R-DT-12', 'rewrite',
  'Shall: officials tracked with role (lead, trail, centre in three-person crews; lead and trail in two-person crews, Rule 2-1.1.a) per second with role confidence and floor position (m), and at 10 Hz in the 2 s around each whistle; role changes stored as rotation events.',
  'Role correct in >= 90% of 200 labelled seconds (proposal; 95% target after the CCA manual check), reported by crew size; position within 1.0 m of gold when on the main camera.',
  'QAR', k=['K24'])
o('R-BL-04', 'tighten',
  'Shall: pass start and end, shot release and catch stored as frame index plus video_ts_ms, with the frame period (0.033 s at 29.97 fps) as stated resolution.',
  '100% of rows carry a frame index; times within +/- 2 frames of the hand label on >= 90% of 300 labelled events per type (share initial value, to calibrate).',
  'ES', k=['K07'])
o('R-SY-01', 'tighten',
  'Shall: scoreboard fields (game clock, shot clock, score, period, team fouls, timeouts, arrow) read on every frame around value changes and at >= 2 fps otherwise; tenths read when the game clock is below 60 s (Rule 1-18.2); each field stores its change time and lag-model correction (new-SY-E4); the "POSS" marker writes only to the arrow column, never to ball possession; gaps filled from clock_map with status (observed, interpolated, unknown).',
  'Game clock exact >= 99%, shot clock exact >= 98%, other fields >= 99% of scorebug-visible readings (initial values, to calibrate); score = PBP at 100% of scoring events; game clock known (observed or interpolated) on 100% of live main-camera frames; a unit test proves POSS never writes to a possession column.',
  'QEA', k=['K02'])
o('R-SY-04', 'tighten',
  'Shall: possession table: start, end, outcome, points, length (s) and three label sets: tempo class (primary, early, half-court; from R-TR-09), start type (after make, after made last FT, after defensive rebound, after turnover, after held ball/arrow, period start) and multi-label situation flags (ATO with calling team, after media timeout, SLOB, BLOB, end of period = start with <= 35 s left, shot clock off).',
  'Possession points = final score in 100% of games; tempo and start type each >= 90% correct (proposal); every possession has >= 1 flag set or "none"; counts per flag per game reported.',
  'QA', k=['K14'])
o('R-TR-05', 'merge-into',
  'Superseded by R-TR-09 (reported class, state-based) and R-TR-18 (the clock-based class is kept only as the named flag clock_class_7_14).',
  'Lint: 0 output columns called transition_class without a definition suffix; tests as R-TR-09 and R-TR-18.',
  'QA', into='R-TR-09')
o('R-TR-06', 'merge-into',
  'Superseded by R-TR-26 (value of each break state per second), computed from the R-VL-01 value layers.',
  'As R-TR-26.', 'AS', into='R-TR-26')
o('R-TR-11', 'merge-into',
  'Superseded by R-TR-18 (same rule, fuller list of definitions, never merged).',
  'As R-TR-18.', 'QA', into='R-TR-18')
o('R-EV-07', 'tighten',
  'Shall: each shot stores release r (m) and theta (degrees); shot family (catch-and-shoot = 0 dribbles and touch <= 2.0 s; pull-up = >= 1 dribble; post-up; putback <= 2.0 s after an offensive rebound; transition flag per R-TR-09); shot type from the coach and broadcast vocabulary (catch-and-shoot, pull-up, step-back, side-step, floater/runner, hook, layup, dunk, tip-in, putback, alley-oop, fadeaway, bank); dribbles and touch time (s); nearest defender distance (m) and angle (degrees; in front = within +/- 45 degrees of the shooter-rim line) at catch and release; second-nearest defender distance; closing speed of the nearest defender over the 0.5 s before release (m/s); shooter speed and heading at gather; shot and game clock; result incl. rim outcome; assisted flag and assister from PBP.',
  'All fields on >= 90% of shots with shooter and nearest defender mapped (sigma <= 0.5 m); contest fields are "unknown" when the shooter or nearest defender is not mapped with sigma <= 0.5 m at release, never imputed; unknown share per game in the run record (%); models use an explicit unknown level; shot type >= 85% agreement with coach labels on 300 shots (proposal); assisted flag = PBP on 100% of made FGs.',
  'AS', k=['K22'], note='absorbs new-DF-S3')
o('R-EV-16', 'rewrite',
  'Shall: coach\'s challenge record per Rule 11-4 and 2-9.19: challenging coach, challengeable type (out of bounds at any time; basket interference or goaltending and secondary-defender restricted-area calls only before the last 2:00 of regulation, 11-4.1.a-c), timeout used (30 s or full), review duration (s), outcome (stands or overturned), timeout charged or retained, second challenge earned; officials\' own reviews (11-2, 11-3) logged separately in R-RF-07 with trigger and duration.',
  'Every challenge in PBP or on the broadcast has a row (100%); fields equal PBP where coded; duration within +/- 2 s of video when visible; every record passes the challenge invariant (new-IV-14).',
  'QAR')
o('R-RF-03', 'rewrite',
  'Shall: foul record with class from config/vocab/fouls.yaml (2026-27 classes: personal common, player-control, team-control, double, simultaneous, multiple, Flagrant 1, Flagrant 2, Class A, Class B, administrative and contact dead-ball technicals; no "intentional": legacy labels map per legacy_label_map, deliberate end-game fouls = common + is_end_game_deliberate or Flagrant 1 away from the ball, 4-15.2.c.1.d); shooting / non-shooting and and-one as context flags; fouler, fouled, location r (m) and theta (degrees), shot clock, team-foul count and whether the foul put the opponent in the bonus or double bonus; free throws awarded.',
  '100% of fouls carry a class from the config list (0 outside it); type and players equal PBP where coded; bonus-trigger flag recomputes from team fouls (0 differences).',
  'QAR', k=['K27'], note='absorbs inbox 007 new-RF-3')
o('R-RF-06', 'tighten',
  'Shall: crew and per-official tendency tables as of each game date, pace-adjusted: fouls per 100 possessions, FTA per FGA, home-away foul split, call-type mix, reviews per game; each shrunk toward the D-I mean weighted by games worked, with n games and interval.',
  'Posterior recomputes from stored counts (0 differences); every published value shows n games and interval; values with n < 10 games flagged.',
  'AS')
o('R-ST-08', 'tighten',
  'Shall: per phase: execution speed (cutter speed m/s, screen-to-cut delay s, catch-to-action time s), spacing (m), hull area (m²), defensive reaction delay (s) and value at the boundary, the last taken only from a validated value layer (R-VL-01); null, not a placeholder, until it passes.',
  'Recomputation from tracks equals stored values; screen-to-cut delay and catch-to-action time within +/- 80 ms of hand timing on >= 80% of 100 phases (share initial value, to calibrate); value column null until the R-VL-01 layer gate passes.',
  'QS')
o('R-ST-12', 'rewrite',
  'Shall: templates are defined by role (handler, screener, roller or popper, spacer, cutter, post), never by player name or ID, so any season\'s roster matches.',
  'On the first 2026-27 footage the template match rate is within 10 points of the 2025-26 rate (proposal); 0 templates reference a player ID.',
  'QA')
o('R-DF-06', 'rewrite',
  'Shall: ball-screen coverage per screen in the R-DF-16 two-level form: coarse class (contain/drop, show/hedge, two-on-ball, switch) always; fine coverage (13 taxonomy F3 classes) stored when the fine classifier has passed its validation gate (>= 75% on >= 300 labelled screens from >= 5 games), else fine = unknown; published outputs show the fine label only where its per-screen confidence >= 0.8.',
  'Coarse >= 85% agreement with coach labels on >= 200 screens from >= 5 games for first release (initial value; R-DF-16 target 90% by season end); fine >= 75% on the gate set; 0 published fine labels with confidence < 0.8.',
  'QAS', k=['K04'])
o('R-DF-07', 'split',
  'R-DF-07a Shall: off-ball screen coverage per screen. R-DF-07b Shall: post defense (front, three-quarter, behind) per post touch, plus double-teams: where the double comes from (top, baseline, strong-side wing, weak side), trigger (on catch, first dribble, turn), time from catch to double (s) and the rotation behind it; double = 2 defenders within 1.5 m of the holder for >= 0.5 s.',
  'a: >= 80% correct on gold (proposal); b: post position >= 80% and double-team label >= 85% agreement on 100 post touches (proposal).',
  'QA')
o('R-DF-19', 'tighten',
  'Shall: scheme-change triggers stored with each change as features: timeout after a run, "not working" (opponent PPP over the first 10 half-court possessions, stored with n and interval), inbound-only scheme, score and clock state, rim-protector foul trouble, opponent hot shooter (new-DF-A6), opponent lineup change, after a timeout; each change stores possessions elapsed since its trigger; no report states that a trigger caused a change without the registered identification design of new-HY-S1.',
  'Every scheme_changes row has a trigger code or "none found"; lag in possessions recomputes (0 differences); 0 causal claims without a design field.',
  'AS')
o('R-VL-01', 'rewrite',
  'Shall: possession value in three layers stored side by side with a coverage flag per possession-second: (1) PBP-state value every second for every D-I game (score, time, start type, shot clock, fouls); (2) location value when ball and shooter are mapped; (3) full-tracking value at 10 Hz only when >= 8 players and the ball are mapped, and only after gates G1-G4 pass on two games; a layer is used in reports only if it beats the layer below.',
  'Each layer calibrated on held-out games (10-bin ECE <= 0.03 on the points-per-possession scale); each higher layer beats the one below on held-out log loss of the terminal outcome; gate record shows G1-G4 pass before the first 10 Hz row.',
  'ES', k=['K20'], note='absorbs new-VL-S4')
o('R-VL-04', 'rewrite',
  'Shall: shot quality per shot in two stored versions: (i) shooter-agnostic xFG and xPts for a league-average D-I shooter from the R-EV-07 fields (location-only layer from D-I PBP shot locations; contest-aware layer from tracked shots), used for shot-making residuals; (ii) shooter-adjusted xPts adding the shooter prior, used for prediction.',
  'Held-out games: contest-aware layer improves log loss over location-only by >= 1% with 10-bin ECE <= 0.02; contest coefficient has the expected sign with 95% interval excluding 0; mean predicted vs actual within 0.02 points per shot over >= 1,000 shots and within 0.05 per shot type with >= 200 shots.',
  'AS', k=['K11'])
o('R-VL-05', 'tighten',
  'Shall: decision quality = value of the option taken minus the expected value of the passing options at that moment (Cervone "shot satisfaction"), computed only when all passing options are mapped (>= 8 players); per player with n and 95% interval.',
  '100% of values carry an interval; values with n < 100 decisions are descriptive; on 100 decisions rated by Aldemir the sign agrees in >= 75% (initial value, to calibrate).',
  'QS')
o('R-CH-06', 'tighten',
  'Shall: coach record: first set after each timeout and its value; substitution patterns; half-time adjustment = change from the last 600 s of the first half to the first 300 s of the second half in set mix, coverage mix, pace and PPP, with n possessions. Timeout timing vs runs moves to R-CC-02.',
  'Computed for 100% of processed games; first ATO set label agrees with gold >= 85% (initial value, to calibrate); marked descriptive when n is below the R-VA-05 rule.',
  'QA')
o('R-CC-03', 'tighten',
  'Shall: reactions measured from data: player pulled at the first dead ball after his turnover or defensive breakdown, and within 60 s of game clock (both windows stored; 30 s kept as a sensitivity view); technical fouls; scheme or lineup change after an opponent run; every pull rate compared with the player\'s substitution hazard in matched moments without the trigger (same period, minutes into the stint, foul count).',
  'Recomputes from substitutions (0 differences with PBP times); report gives observed vs expected pull rate with 95% interval per window.',
  'QAS', k=['K21'])
o('R-GU-03', 'loosen',
  'Shall: from the third processed game on (not a data dependency for games 1-2), coach quiz at random paused moments ("who guards X, which set, which defense, what happens next") scored against Aldemir\'s answers.',
  'Score per question type per game and model version; pass mark per type set by Aldemir (needs decision), e.g. "who guards X" >= 90% to match R-DF-01.',
  'QE')
o('R-SR-04', 'rewrite',
  'Shall: timeout and review state: game media format; timeouts left per team by length (30 and 60 s in the media format; 75 and 30 s otherwise), caller of each; actual media slot of each media timeout per Rule 5-14.10 (16/12/8/4 or 15/10/5 marks; 30-s pre-mark conversion; first second-half team timeout takes media length; A.R. 5-33); coach\'s challenge left (Rule 11-4); monitor review in progress.',
  'Matches the PBP timeout list (100%); media slots match PBP media timeouts in >= 95% (initial value, to calibrate); the timeout and media invariants (R-IV-10, new-IV-13) pass on 100% of pilot games.',
  'QAR')
o('R-SR-07', 'rewrite',
  'Shall: personnel: the 10 players on court with identity confidence, x, y (m), speed (m/s), acceleration (m/s², after the K03 gate); stint length (s); positions of the two or three officials (Rule 2-1.1.a; crew size from game_officials); stored in player_positions, lineup_stints and official_positions (as-of views of state_segments).',
  'Identity as R-ID-01; positions as R-CG-03; official position rows per visible second equal crew size.',
  'QAR')
o('R-SR-11', 'tighten',
  'Shall (promoted from Should): game situation every second as named flags with thresholds in config: two-for-one window (33-45 s, proposal), last-shot hold, foul-to-extend (trailing, <= 60 s, margin 1-9), foul-up-3 cell (game clock x shot clock), shot clock off, fouls to give per team, bonus status of both teams, foul-trouble flags read from the R-MD-16 table.',
  'Flags recompute from state (0 differences); constants live in config (lint: 0 hard-coded); counts per flag per game reported.',
  'QA', tier='Shall', k=['K10'])
o('R-IV-02', 'rewrite',
  'Shall: two or three officials on court (Rule 2-1.1.a); three expected in D-I; two-official games set in the games registry; a crew-size change mid-game is logged.',
  'Invariant reads constants.officials_on_court_allowed = [2, 3]; 0 unreviewed breaks per game.',
  'QAR')
o('R-IV-10', 'rewrite',
  'Shall: timeouts left never go below 0 and never go up except at the start of an extra period; allotment per media format: >= 3 media timeouts per half -> three 30-s and one 60-s per team per game, at most two 30-s carried into the second half, one extra 30-s per extra period (5-14.10.a, b, f); fewer than 3 media timeouts or none -> four 75-s and two 30-s, one extra 75-s per extra period (5-14.8, 5-14.9).',
  '0 unreviewed breaks; passes on 100% of pilot games.',
  'QAI', note='absorbs new-IV-12')
o('R-IV-13', 'rewrite',
  'Shall: physics checks on filtered tracks from the shared config key physics.*: hard speed limit 10.0 m/s over >= 0.3 s windows (break); soft speed limit 9.0 m/s (review flag for identity swaps); |acceleration| <= 12 m/s² over >= 0.5 s windows (flag only), tightened to 8.0 m/s² once the measured acceleration sigma is <= 1.0 m/s²; ball handler within 1.5 m of the ball while in control; one ball position per frame; every player and ball position inside the court + 1.0 m and ball height within its physical range. Breaks are flags, not quarantines, until calibrated.',
  'False-break rate <= 1 per 1,000 player-seconds on hand-checked clips; 0 unreviewed breaks per game; one key read by R-DQ-02, R-EN-03 and R-DT-08 (unit test).',
  'QESI', k=['K01'], note='absorbs new-IV-34')
o('R-SB-03', 'tighten',
  'Shall: measure the scorebug lag after made baskets for every game and every scorebug field (distribution in s); the make-detection window starts at 4.0 s (measured lag 1.50-2.60 s, n = 10) and is re-set after each game to the per-field 99th percentile + 1.0 s, never below 3.0 s and never above 15 s.',
  '>= 99% of matched makes fall inside the window; 0 makes missed for window reasons on the pilot games; window and lag quantiles per field in the run record.',
  'EAS', k=['K02'])
o('R-MB-04', 'rewrite',
  'Shall: make frame within +/- 2 frames of the hand label at the file\'s frame rate (+/- 0.067 s at 29.97 fps; +/- 0.033 s at 59.94 fps) on >= 95% of makes, and within +/- 1 frame on >= 80% (stretch, initial value); 2 vs 3 agreement with PBP >= 99%.',
  'Measured on all makes of game 1 and game 2 against a hand label that is itself +/- 1 frame.',
  'QEAS', k=['K07'])
o('R-PL-01', 'loosen',
  'Should: distance per minute and per possession by the R-PL-11 primary bands; the walk/jog/run/sprint 2.0/4.0/5.5 m/s placeholder is kept only as a view on R-PL-09 bins.',
  'Total distance on a synthetic track within 3% (proposal).',
  'QS', tier='Should')
o('R-PL-03', 'tighten',
  'Shall: within-game decline of top speed (95th percentile, m/s) and acceleration (after the K03 gate) by period and by continuous minutes on the floor, estimated within player with possession type (transition, half-court, dead) and score state as covariates, beside the raw decline.',
  'Every decline estimate carries a 95% interval; >= 5 min of floor time per period; covariate model reported beside the raw decline.',
  'QS', k=['K03'])
o('R-PL-07', 'loosen',
  'Should: shot physics (release height, arc and entry angle in 3-D, release point vs the defender\'s hand) is research-only until R-CG-11 passes +/- 0.05 m; release time (catch to release) moves to R-EV-07 as a Shall field.',
  'After R-CG-11: arc and entry angle within 3 degrees on >= 90% of 100 shots (initial value, to calibrate); release time within +/- 0.05 s on >= 90% of 100 shots.',
  'QS')
o('R-CO-02', 'rewrite',
  'Shall: defensive reaction time = pass release or cut start to the defender\'s movement onset, detected by change-point on velocity direction and magnitude (no acceleration-threshold onset), stored with its uncertainty (>= +/- 1 frame plus filter delay, expected 0.10-0.15 s); per-player values are distributions with n >= 50 events; single events are never shown as a player\'s reaction time.',
  'Onset within +/- 0.10 s of hand labels on >= 80% of 100 labelled reactions on game 1; uncertainty column on 100% of rows.',
  'QES', k=['K03', 'K16'])
o('R-CO-04', 'rewrite',
  'Shall: pressure performance: decision and shot quality in three separate slices: contest <= 1.2 m, shot clock <= 5 s, and the single config clutch flag (R-MD-13a); each shrunk toward the player\'s own non-pressure performance and the population pressure effect, with n.',
  'One clutch constant in config referenced by every module (lint: 0 second definitions); interval and n on every number.',
  'QAS', k=['K06'])
o('R-EN-02', 'tighten',
  'Shall: reproducible runs, determinism stated per stage: bitwise for CPU transforms; GPU inference within declared tolerances (positions +/- 0.01 m, scores +/- 1e-4).',
  'Re-run of game 1: 0 differences in CPU stages; GPU stages within tolerance.',
  'QE')
o('R-RG-02', 'tighten',
  'Shall: rights gate before any MSU pitch or public output: only numbers, drawings on our top-down court and cleared clips; no broadcast frames or audio; clips referenced by game_id and video time only; checklist signed by Aldemir.',
  'Signed checklist on file before P8; checklist line "no broadcast pixels" ticked for 100% of outputs; an automated scan of published files finds 0 embedded video frames.',
  'QA')
o('R-PR-11', 'tighten',
  'Should: live in-game win probability refreshed within 10 s (95th percentile) of each scoreboard change; calibrated overall and for the last 240 s separately; no swing > 0.25 without a score, turnover or foul event; never published before R-PR-09 passes.',
  'ECE <= 0.03 overall and <= 0.05 in the last 240 s on held-out games; 95th-percentile latency <= 10 s; sanity-rule violations = 0.',
  'QA', k=['K06'])
o('R-PE-07', 'tighten',
  'Shall: end-game policies fitted from PBP plus scorebug shot clock and stored per decision cell (game clock x shot clock x margin): fouling when trailing, fouling up 3, two-for-one, last-shot holds, timeout use including the head coach\'s live-ball timeout in the last 2:00 (5-11.3, 5-14.1.a exception).',
  'In >= 90% of cells with n >= 30 the simulated rate lies inside the game-resampled 95% interval of the D-I rate (initial value, to calibrate); cells with n < 30 pooled with a stated prior.',
  'QA')
o('R-HR-02', 'tighten',
  'Shall: review item: clip with event-type windows from config (shot 3 s before / 2 s after, ball screen 4 / 3, transition from secure catch to first shot, foul 3 / 3, default 3 / 3; reviewer can extend), top-down view beside it, model guess prefilled, one-click confirm or correct.',
  'Config windows used for 100% of items; median time per item <= 20 s (initial value, to calibrate).',
  'QA')
o('R-VZ-06', 'split',
  'Split into one Should per view, each with a render test: matchup board, heat maps, passing network, layered win probability with run shading, filters, clip export, foul tracker, timeouts left, shot chart by sector and ring, lineup plus-minus with n.',
  'Each view renders from the state tables of a pilot game; every number linked to frames (R-VZ-02).',
  'QA')
o('R-CS-09', 'rewrite',
  'Shall: storage plan per season from measured sizes: 1.82-1.97 GB per 1080p 29.97 fps condensed replay (2.81-2.92 Mb/s, measured) and processed GB per game per version measured on game 1; Drive use stays under 80% of plan capacity; the 4K estimates move to the plan file.',
  'Measured size logged for 100% of files; plan updated after game 1; Drive use < 80%.',
  'QE')
o('R-PT-01', 'tighten',
  'Shall: pitch package: walk-forward results of engine levels L1-L3 against closing lines (CLV, log loss, intervals, n), plus one fully processed MSU game showing what video adds, including its half-time packet and post-game notes (new-VZ-A1, new-VZ-A2), every number linked to frames and reconciling with the official box.',
  'Sign-off on file; 100% of counting stats equal the official box.',
  'QA')
# single-source or conflict-driven extras
o('R-PL-12', 'tighten',
  'Shall: acceleration and deceleration bands +/- 2.0 and +/- 3.0 m/s², gated separately, computed over >= 0.5 s windows with propagated sigma; band counts reported only where the acceleration sigma is <= 0.5 m/s² (else "unresolved", counted); nothing above 4 m/s² reported; jerk and PlayerLoad not reported.',
  'Resolvable share of player-time reported per game (%); 0 band counts from unresolved segments.',
  'EQ', k=['K03'])
o('R-PL-02', 'merge-into',
  'Superseded by R-PL-12 (+/- 2.0 and +/- 3.0 m/s², gated); the 2.5 m/s² threshold is kept as a view.',
  'As R-PL-12.', 'Q', into='R-PL-12', k=['K03'])
o('R-PL-05', 'tighten',
  'Shall: coverage-corrected load: every load number states the share (%) of the player\'s floor time observed on the main camera; the coverage threshold is one config key shared with R-PL-14 (default 0.70).',
  '0 load rows without coverage %; 0 rows under the shared threshold unflagged.',
  'QE', k=['K13'])
o('R-PL-14', 'tighten',
  'Shall: stints with less on-court time detected than the shared coverage key (default 70%, same key as R-PL-05) are left out of load summaries.',
  '0 summaries include stints below the key.', 'Q', k=['K13'])
o('R-EN-03', 'tighten',
  'Shall: automatic checks per stage: possessions vs PBP, score vs official, no player in two places, no player faster than the hard speed limit of the shared physics key (R-IV-13).',
  '0 unreviewed failures per stage; the speed check reads physics.speed_hard_mps (unit test).',
  'S', k=['K01'])
o('R-SY-08', 'rewrite',
  'Shall: shot-clock reset and no-reset events read from the scoreboard: time, value before, value after (s) and cause from the full list in config/vocab/shot_clock_resets.yaml (41 causes, Rule 2-11 plus 5-10.3, 9-11, 2-11.8, 2-11.9; supersedes the 33-cause table in config/invariants.yaml), including no-reset stoppages.',
  '>= 98% of resets found; >= 95% causes correct (proposal); every stoppage with a live shot clock has a reset or no-reset row.',
  'QRI', k=['K18'], note='absorbs inbox 007 new-SY-2')
o('R-SY-05', 'rewrite',
  'Shall: chance table: chance number, start cause, start shot clock (s), time used (s), end type from the R-DQ-06c terminal list (made shot, missed shot with defensive rebound, missed shot with offensive rebound, shot-clock reset by defensive foul or kicked ball, turnover, held ball, period end).',
  'Offensive rebounds per game = PBP; every chance has exactly one end type (0 exceptions); end types reconcile with R-DQ-06c.',
  'QE', k=['K08'])
o('R-DF-16', 'tighten',
  'Shall: two-level ball-screen coverage: 4 coarse classes (contain/drop, show/hedge, two-on-ball, switch) always, then the fine coverage when the K04 gate passes; drop depth in sourced bands (high 0.6-1.83 m, standard 1.83-3.05 m, deep > 3.05 m) measured 0.3 s after the screen moment.',
  'Coarse >= 85% (first release) rising to >= 90% by season end, fine >= 75% on the gate set (>= 300 screens, >= 5 games); depth within 0.5 m of gold on 100 screens (initial value, to calibrate).',
  'AS', k=['K04'])
o('R-EV-13', 'tighten',
  'Shall: sequence features: previous possession result; net points over the last 120, 240 and 360 s of game clock as numeric features (not called runs); run flags only from the R-MD-17 definitions; first set after a timeout.',
  'One run vocabulary in config; features recompute from score_events (0 differences).',
  'A', k=['K05'])
o('R-CC-02', 'tighten',
  'Shall: timeout behaviour: timeouts vs opponent runs (R-MD-17 register definition): lag from the run reaching its threshold to the timeout (game-clock s and possessions), whether a media timeout was due within 60 s, timeouts left at the under-4 media timeout and at the end of each half.',
  'Recomputes from timeouts, media slots and score_events for 100% of games (0 differences).',
  'A', k=['K05'])
o('R-CH-08', 'tighten',
  'Should: runs and momentum use the R-MD-17 run definitions and are tested against the state model under a pre-registered hypothesis (beliefs register new-4, new-5, new-7) with a registered identification design (new-HY-S1).',
  'Test registered under R-HY-01 before results are read; design field filled.',
  'AS', k=['K05'])
o('R-SR-06', 'tighten',
  'Shall: ball state: control state (team A ball, team B ball, contested, in flight, throw-in pending, dead), ball handler, ball x, y and height (m), ball_visible, ring_contact on each try; stored as dimensions of state_segments (per-frame values are an as-of view).',
  'Tests of R-MD-02 (control state), R-BL-02 (handler), R-BL-01 (position) and R-MB-07 (ring contact); view equals segments on 100% of frames.',
  'QE', k=['K09'])
o('R-MD-01', 'rewrite',
  'Shall: every row carries the key stamp (game_id, pass, stage output key, and either (video_id, frame_index) or (period, game_clock_s, order_index)); the state stamp of schema/global_metadata.yaml (clocks, score, fouls, control, lineup) comes from an as-of join to state_segments and is materialised only in views and exports.',
  'For a random 1% sample of rows, joined state equals the materialised view (100%); no stored table except state_segments holds a copy of global state fields.',
  'E', k=['K09'])
o('R-DS-05', 'tighten',
  'Shall: one bitemporal crosswalk (valid_from, valid_to, recorded_at) for games, teams, players, venues, officials and coaches across ESPN, CBBD (play, sub and lineup athlete IDs are CBBD IDs), NCAA engine, Torvik, KenPom and EvanMiya name strings.',
  '100% of PBP athlete IDs of in-scope games resolve to an ESPN athlete ID or a local x- ID; 0 many-to-one mappings within a validity period.',
  'E', note='absorbs new-DS-1 (dictionary_games.md)')
o('R-EV-10', 'rewrite',
  'Shall: turnover type per turnover from config/vocab/violations_turnovers.yaml, mapping 1:1 to the 2026-27 violations and PBP codes, adding backcourt over-and-back (9-12) and elbows (9-13) to the 11 listed.',
  'Count = PBP; type = PBP where coded; 0 PBP turnover codes without a mapping.',
  'QRI', note='absorbs inbox 007 new-EV-3, new-EV-4')
o('R-RG-11', 'tighten',
  'Shall: the public-repo line is enforced in code: every row writer (video, processed, markets raw and parsed, review clips) uses one shared private-root guard; a pre-commit hook blocks .parquet, video and row-level CSV under the repo except whitelisted registry files. Markets RawStore already calls ensure_private (fixed 2026-10-18, test_engineer_review_fixes.py).',
  'Writing under the repo raises in a unit test for every writer; committing a .parquet or a 1 MB CSV under results/ fails the hook.',
  'E', note='absorbs new-RG-E1; markets part resolved')
o('R-MK-27', 'rewrite',
  'Shall: rows de-duplicated on (game, source_event_id, source, book, market, phase, snapshot label, side, team/player, line, snapshot time); CBBD reported open/close of finished games keyed on the scheduled tip so re-pulls are idempotent; the store skips keys already present in the partition (idempotent across runs). RESOLVED in code 2026-10-18 (models.py dedup_key, sources/cbbd.py, store.py; tests/markets/test_engineer_review_fixes.py).',
  'Two unmatched games with equal totals in one fetch both survive; re-pulling a finished season adds 0 rows; ingesting the same raw twice adds 0 rows (regression tests pass).',
  'E', note='absorbs new-MK-E1, new-MK-E2; resolved')
o('R-MK-13', 'tighten',
  'Shall: every response written raw (gzip, as received) with one manifest line before parsing, recording sha256_received (before any redaction) and sha256 of the stored body; the raw root is guarded as private. RESOLVED in code 2026-10-18 (raw_store.py, models.py ManifestEntry.sha256_received).',
  'Unit test: redacted body gives two different hashes, both in the manifest; writing raw under the repo raises (passes).',
  'E', note='resolved')
o('R-EN-07', 'rewrite',
  'Shall: processed outputs are Parquet under processed/<table>/stage=<s>/key=<output_key>/game_id=<id>/pass=<p>/ with _manifest.json (rows, sha256, schema_version, input keys) and a per-game _current pointer; versions side by side.',
  'Manifest on 100% of partitions; current pointer resolves for every processed table and game; a change to one stage writes new keys only for that stage and its descendants (test change).',
  'E', note='absorbs new-EN-E4')
o('R-IV-05', 'tighten',
  'Shall: game clock never goes up within a period except as a logged correction (Rule 5-12) with old and new values and the affected window.',
  'Every upward step has a state_corrections row (Louisville 4:06 -> 4:07 is one); 0 unlogged upward steps.',
  'E')

o('R-MD-08', 'rewrite',
  'Shall: the video <-> game clock <-> shot clock <-> UTC map is stored as piecewise segments in a clock_map table, one per running-clock stretch per video file and pass (video_id, start/end frame, start/end video_ts_ms, period, game clock at both ends, rate, shot clock at start and status, UTC estimate with source and error, residuals); monotonic inside each running-clock stretch; UTC from PBP wall clock only where it is monotone over >= 3 consecutive plays, elsewhere interpolated with a stated error.',
  'Over live main-camera frames with a legible clock: median |OCR - map| <= 0.1 s and 99th percentile <= 0.5 s; 100% of live frames in exactly one segment; game clock non-increasing within a segment (0 exceptions); non-monotone wall-clock stretches flagged with an error bound (s) per segment.',
  'E', note='absorbs new-MD-E1, new-SY-E6')
o('R-EN-01', 'tighten',
  'Shall: one versioned schema per table, units in column names; all specs in one YAML dialect generated from one source, with semver per table; a validator checks names, PK, FK targets, units, ranges, licence class, as-of rule and requirement IDs.',
  '104 of 104 specs pass in CI; a spec citing an unknown requirement ID fails; 0 specs in the second dialect.',
  'E', note='absorbs new-EN-E5')
o('R-EV-06', 'tighten',
  'Shall: drive: start point, direction (baseline or middle, left or right), depth reached (m), result; a drive is a dribble move gaining >= 3 m toward the rim (proposal); defender reaction = at drive start and at paint arrival the first help defender (ID), help arrival time (s), help distance (m), the kick-out target and its nearest-defender distance at the catch (m).',
  'Drives found >= 90% and direction correct >= 95% (proposal); help fields filled on >= 80% of drives with >= 8 players mapped.',
  'S', k=['K16'], note='absorbs new-EV-S1')
