# Requirements inbox 004 · Transition: definitions side by side, phase timestamps, pushes after scores, passed-up breaks

From: research session (Job D of `coord/prompts/002-claude-code-taxonomy-and-markets.md`). To: requirements session. Status: proposal from research, not yet agreed with Aldemir.
Source document (full evidence, every URL): `docs/research/transition_full.md`, revised after a source-verification pass on 2026-10-18. Section numbers below (§) refer to that file.
Action: consider adding the items below to the live requirements doc under the transition requirements. Nothing here changes `docs/requirements.md` directly.

Units throughout: metres, seconds, degrees, m/s; court positions as r (m) and θ (degrees from the right baseline at the rim centre), per `config/vocabulary_map.yaml`.

**Core rule.** Analysts disagree on what "transition" means. Never merge their definitions: store one field per definition, per possession and per chance, each with its own time and state cutoffs (§5). Aldemir's earlier state-based rule (repo `PHASE`) is one of these fields.

---

## 1. New measurable items (one line each)

### 1a. One flag per analyst definition (§5.4)

- `tr_synergy_like`: possession ends (shot, turnover, shooting foul) before t_defense_set; no clock cutoff (Synergy, via Nylon Calculus).
- `tr_ctg_pbp`: possession starts with a transition event and stays transition until the defense is set; putbacks inside count (Cleaning the Glass, play-by-play site).
- `tr_ctg_pro_opportunity`: first chance of a possession, not after a sideline/baseline out of bounds, a timeout or an immediate backcourt turnover (CTG Pro).
- `tr_ctg_pro_is_transition`: chance ends with the initial transition advantage still going (CTG Pro).
- `tr_hoopmath_10s`: initial FGA ≤ 10.0 s after a DREB, steal or opponent score; putbacks (≤ 4 s after an OREB) excluded (Hoop-Math). Dead-ball-TO starts are NOT Hoop-Math transition.
- `tr_hoopmath_10s_plus_dbto`: same plus dead-ball-TO starts; comparison only (Hoop-Math tabulates that row separately).
- `tr_mgoblog_live_dreb`: shot ≤ 10.0 s after a DREB with the ball live throughout (unverified variant; search snippet only).
- `tr_fastscout_10s`: possession ends with the shot clock reading ≥ 20 s and did not start after a stoppage (FastScout / Hudl).
- `tr_fastscout_10s_elapsed`: possession ends ≤ 10.0 s after t0, not after a stoppage (comparison twin; differs after the 20 s offensive-rebound reset).
- `tr_instat_strict_4_8s`: 4.0 ≤ t_FGA − t0 ≤ 8.0 s, defense not in position (Hudl InStat, strict reading).
- `tr_instat_0_8s`: t_FGA − t0 ≤ 8.0 s, defense not in position (Hudl InStat, inclusive reading).
- `tr_ncaa_fbp`: official NCAA box-score fast-break points (state-based, no time cutoff; stop-the-break bonus FTs excluded).
- `tr_fiba_fbp_8s`: points ≤ 8.0 s after t0 before the defense is set; stop-the-break FTs counted (FIBA rule).
- `tr_nba_6s_clock`: FGA with the shot clock reading ≥ 24.0 s on the NCAA 30 s clock.
- `tr_nba_6s_elapsed`: FGA with t_FGA − t0 ≤ 6.0 s.
- `tr_vuhoops_10s`: any action ≤ 10.0 s from the change of possession (VU Hoops play-by-play method).
- `tr_conte_8s`, `tr_matulaitis_5s`, `tr_matulaitis_5_8s`, `tr_bourgeais_6s`, `tr_skinner_7s`, `tr_goldman_rao_10s`: research time windows (8, 5, 5–8, 6, 7, 10 s).
- `tr_metulini_band_s`: seconds the team centroid spends with \|y − 12.73\| ≤ 4 m.
- `tr_franks_halfcourt_t`: first time all 10 players are in the offensive half.
- `tr_roy_williams_window`: D_back ≤ 2 when the ball crosses half-court.
- `tr_trninic_type`: primary / secondary / early from the defender count in the end zone.
- `prim_conte`, `prim_conte_loose`, `prim_trninic`, `sec_conte`, `sec_trninic`, `sec_heuristic`: named primary/secondary typology fields (§2.1, §3.4).
- `prim_time_coaching_2_3s`, `prim_time_fotinakis_3_9s`: the two conflicting primary-break time windows (§3.1).
- `tr_repo_phase`: the current repo `PHASE` label.

### 1b. Phase timestamps (§3.2), stored as elapsed time since t0 and as the shot-clock reading

- `t0` (possession gain; anchor rule per start type, §1.4).
- `t_outlet` (catch of the first pass after a DREB).
- `t_cross_half` (ball crosses y = 12.73 m).
- `t_scoring_zone` (ball first at y ≤ 10.29 m).
- `t_three_zone` (ball first at r ≤ 6.75 m).
- `t_paint` (first paint touch).
- `t_adv_start`, `t_adv_end` (numbers advantage begins / ends).
- `t_first_action` (first SCREEN, DHO or CUT).
- `t_first_shot` (first FGA or shooting foul).
- `t_pull` (pull-back / reset).
- `t_flow_entry` (first half-court action after the break).
- `t_defense_set`, two versions (repo rule; CTG-like rule).
- CTG-comparison fields: `ball_seconds_to_scoring_zone`, `ball_seconds_to_three_point_zone`, `ball_seconds_to_paint`, `scoring_zone_shot_clock`, `ball_in_paint_shot_clock`.

### 1c. Numbers state (§3.4)

- `numbers_state(t)` at 10 Hz: A_play, A_ahead, A_even, A_behind, D_back, D_even, D_behind, each at margins m = 0.5, 1.0 and 1.5 m.
- Per game: the share of possessions whose numbers label flips between margins.

### 1d. Player roles (§4)

- `role_by_player` per break, in both vocabularies: Synergy (leak-out man, ball-handler, left/right wing, trailer) and CTG Pro `transition_role`.
- Per player: start area, seconds and speed to the scoring zone, rank among teammates, lane at t_cross_half (canonical `wing_lane`), and "back before the ball crosses the scoring zone" for defenders.

### 1e. Pushes after made baskets and made free throws (§7.4)

- `t_net` (ball through the net, or final FT drops), `t_inbound_release`, `t_inbound_catch`.
- `inbound_delay` = t_inbound_release − t_net.
- Inbounder identity and height; first-pass type and length.
- `t_cross_half − t_inbound_catch`; handler backcourt speed; `ball_speed_to_scoring_zone`.
- Numbers state at t_cross_half.
- `press_present`, `trap`.
- `push_after_make`, reported separately for made FG and made FT, with the share meeting Westhead's < 3 s shot target.

### 1f. Passed-up breaks (§8)

- Opportunity flags, stored separately: `opp_ctg_eligible`, `opp_numbers_t1`, `opp_roy_williams`, `opp_numbers_goal`, `opp_live_start`.
- Passed-up condition that fired (1–7): slow crossing, slow backcourt, held ball, pull-back with an advantage, ignored runner, reset above the arc, stalled push.
- Category: declined / denied / failed, plus context codes (personnel, fatigue, fouls, game state, on-court PG, opponent press or crash).
- `passed_up` count per game, with the value at stake (the fitted break value when the opportunity began).

### 1g. Defensive transition (§2.3, §3.3, §9.8)

- Crash/retreat at the shot: PI, PO, NPC, NPR, CI, RI, and the reaction window (t_rel → rebound).
- Per-player retreat: onset, delay, speed over the first 10 m, peak as a share of the player's own peak.
- `safety_repo` and `safety_wide` (count and identity).
- `t_protect` (first defender at r ≤ 2.5 m).
- `t_stop` (ball stopped), with pickup y.
- `t_matched`; unguarded-shooter seconds.
- MDET (first 5 s after the opponent's DREB).
- `transition_crossmatch` and `planned_crossmatch`: count, height gap (cm), time to switch back (`t_switch_back`).
- Jam/tag duration and outlet delay.
- `no_mans_land` and `no_mans_land_arc`.
- Two-guards-back, shooter-back-first, Full Back / Half Back, 2v1 and 3v2 alignment flags.

### 1h. Per-game comparison with play-by-play (§11)

- One table per game with each play-by-play-computable definition (Hoop-Math, FastScout, VU Hoops, NBA 6 s, FIBA 8 s without the defense-set test): tracking count, play-by-play count, percent agreement and Cohen's kappa.
- Fast-break points under the NCAA rule and under the FIBA rule, against the official box `fastBreakPoints`.
- Possession and chance counts from tracking vs play-by-play, with the difference explained.
- Share of labels that flip at the 10 s boundary because play-by-play has 1 s resolution.

## 2. Suggested definitions and their status

All thresholds below are [HEURISTIC] (proposed by research, not stated by any source) unless a source or [REPO] is named. Calibrate them on MSU film before use.

| Item | Suggested definition | Status |
|---|---|---|
| Numbers bins | D_back: y < y_ball − m. D_even: \|y − y_ball\| ≤ m. D_behind: y > y_ball + m. Attackers use the same margin. m = 1.5 m by default, with sensitivity runs at 0.5 and 1.0 m | [HEURISTIC]; CTG publishes the concepts, not the numbers |
| "Between" geometry | No defender with y < y_P within 1.5 m of the P-to-rim segment, or inside the triangle from P to the lane corners (x = ±1.83 m, y = 0); shooter proxy: a defender within 1.5 m of the ball-to-shooter segment, or within 3.0 m of the shooter | [HEURISTIC] |
| Push (DREB/steal) | Handler ≥ 4.0 m/s for ≥ 1.5 s in the backcourt, and t_cross_half − t0 ≤ 4.0 s | [HEURISTIC]; the 4 s comes from [REPO] |
| Push after a make | inbound_delay ≤ 2.0 s and t_cross_half − t_net ≤ 5.0 s | [HEURISTIC]; the 2.0 s comes from [REPO] |
| Rim run | `rim_run_repo`: ≥ 5.5 m/s for ≥ 2 s, ending at r < 2.5 m before the ball reaches y < 7 m [REPO]. `rim_run_path`: path from r_own ≤ 4.0 m to r ≤ 2.5 m, length ≥ 20 m, mean \|x\| ≤ 3.0 m [HEURISTIC]. NCAA D-I centres peak at about 6.23 m/s (Stone et al. 2022), so the repo speed rule may be too strict | Both kept |
| Wing lane | `wing_lane`: 5.3 ≤ \|x\| ≤ 7.62 m while y runs from 22 m to 6 m (canonical). `msu_wing_lane_v2`: \|x\| ≥ 6 m while y runs from 12 m to 3 m | [HEURISTIC] |
| Long outlet | `long_outlet_zone`: catch at y ≤ 10.29 m. `long_outlet_len15`: pass length ≥ 15 m | [HEURISTIC] |
| Pull-back | After t_scoring_zone, Δy ≥ +2.0 m within 3.0 s, or the handler holds at r ≥ 7.5 m with v < 1.5 m/s for ≥ 1.5 s; no FGA, foul or paint touch in that window | [HEURISTIC] |
| Stalled push | t_cross_half − t0 ≤ 4.0 s, then `pulled_back`, with no FGA, foul or paint touch before t_pull | [HEURISTIC] |
| Safety | `safety_repo`: r > 7 m, moving away at ≥ 2 m/s, at t_rel + 1.0 s [REPO]. `safety_wide`: r ≥ 6.75 m, moving toward the own end at ≥ 2.0 m/s, or y ≥ 9.0 m [HEURISTIC] | Both kept |
| No man's land | Count of defenders with y_own > 12.73 m at the first frame the ball has r ≤ 6.75 m (≤ 6.60 m in the corners); stricter variant uses r_own > 6.75 m | Rule from a blog (squared2020); geometry [HEURISTIC] |
| Matched | Every attacker has a defender within 2.5 m (perimeter) or 1.5 m (r < 3 m) for ≥ 1.0 s | [HEURISTIC] |
| Ball stopped | First defender within 2.0 m of the handler with y_def < y_handler; handler speed < 3.0 m/s within 1.5 s | [REPO] |
| Defense set | Repo: all 5 defenders behind the ball at r < 9 m for ≥ 1 s. CTG-like: 5 back, or 4 back with low average speed (< 2.0 m/s proposed) at frontcourt entry | Repo rule [REPO]; CTG-like threshold [HEURISTIC] |
| Agreement statistic | Percent agreement and Cohen's kappa per possession-level flag; about 30 hand labels per definition as a pilot, grown until the CI is acceptable | [HEURISTIC] choice |

## 3. Evidence notes worth carrying into requirements

- Hoop-Math transition = initial shot ≤ 10 s after a steal, DREB or opponent score. D-I 2023-24 (snapshot of 19 Mar 2024, 362 teams): transition eFG 54.02% vs non-transition 48.84%; post-DREB push rate 46.69% vs post-make 11.18%.
- Every source opened shows higher per-possession value for transition, but the comparisons are selection-biased: pulled-back breaks count as half-court. Villanova 2013-14 showed almost no gap (1.14 vs 1.13 PPP).
- No public study isolates pushing after made free throws at any level. Our tracking can fill this gap.
- No peer-reviewed paper detects fast breaks from optical tracking in men's basketball with accuracy reported against human labels.

## 4. Open questions for Aldemir (one line each; copied from §12)

1. Hoop-Math, FastScout and InStat are now verified from opened pages; do we still keep the planning-chat wording (e.g. "ball live the whole time") as an extra, separately flagged variant?
2. For InStat, do shots under 4 s count as transition, or only 4–8 s? The glossary does not say (both `tr_instat_strict_4_8s` and `tr_instat_0_8s` are stored until Hudl answers).
3. Should a primary-break opportunity use Roy Williams' ≤ 2 defenders back, Trninić's ≤ 2 defenders in the end zone, Conte's configuration rule, or all three as separate flags?
4. For pushes after a make or a made FT, is the clock started at the ball through the net, the inbound release, or the inbound catch (store all three, but which is primary for reports)?
5. Do we use the Wiens MDET threat range per player (75th percentile of his own shot distances, which needs shot history) or a fixed r for college players?
6. Lane bins: five equal 3.05 m bins, or bins tied to court lines (lane edge \|x\| = 1.83 m, FT-line-extended/arc point \|x\| = 5.29 m)?
7. How do we label a pull-back caused by fatigue, fouls or game state (context code) so it is never counted as a "declined" break by default?
8. Rim-run speed: replace the repo's ≥ 5.5 m/s for ≥ 2 s with a share of each player's own peak (Job E), or keep both?
9. "Defense set": keep the repo rule and a CTG-like rule side by side, and which one feeds `tr_synergy_like`?
10. Possession unit for MSU reports: KenPom/pbpstats style (OREB inside the possession) or Synergy style (new possession), or both columns everywhere?
11. Which Big Ten opponents should get full transition profiles next (UCLA, Oregon, USC, Ohio State, Maryland and others were not researched)?
12. Do we buy or request Synergy or CTG data for a label check, or rely on official box fast-break points and play-by-play only?
13. Should the NCAA rulebook's after-make inbound rules (running the baseline) be confirmed before the push-after-make signature is fixed?
14. Which numbers-state margin (0.5, 1.0 or 1.5 m) becomes the reporting default once the label-flip rates are known?
15. Which secondary-break field (`sec_conte`, `sec_trninic`, `sec_heuristic`) and which primary-break time window (2–3 s coaching vs 3–9 s Fotinakis) feed MSU reports?
16. For NBA-style 6 s and FastScout 10 s rules on the NCAA clock, is the shot-clock reading or the elapsed time since t0 the reporting version (both stored)?

---

## Update 2026-10-18 (second pass): research gaps reconciled, additions A1–A8, new items

Added by: requirements-inbox pass, 2026-10-18. This section adds to the text above and does not replace it. It covers two things. First, the research-gap reports that the five Job D researchers filed, checked against the final state of `docs/research/transition_full.md`, which includes the source-verification pass (§1.5) and the "Additions 2026-10-18" (A1–A8). Second, the measurable items and open questions those additions create. Section numbers (§, A) refer to `docs/research/transition_full.md`. Source keys in brackets ([V…], [GF…], [E…]) point to that file's source tables, where every URL is listed.

**Re-checked in this pass** (opened 2026-10-18 by this pass; quotes kept under the limit):

| Claim | URL opened in this pass | Result |
|---|---|---|
| FastScout rule | https://web.archive.org/web/20241212013621id_/https://support.fastmodelsports.com/support/solutions/articles/9000236895-half-court-vs-transition-stats (curl, static Wayback copy of 12 Dec 2024) | Confirmed: "any possession ending in the first 10 seconds of the shot-clock that is not after a stoppage of play". The stoppage list is substitution, foul, timeout, ejection, out of bounds, blood rule, equipment malfunction, injury and court clean-up. Made basket and made last FT start a possession "except in cases of an and-one" |
| Hoop-Math rule | https://web.archive.org/web/20250419151632id_/http://hoop-math.com/MichiganSt.2024.php (curl) | Confirmed: initial shots "within the first 10 seconds of a possession after a steal, defensive rebound, or opponent score". The page has **no** "ball live the whole time" clause |
| Hudl InStat rule | https://instatglossary.hudl.com/basketball/events/play-types/transitions/ | Confirmed: shot "within 4-8 seconds" before the defense can move into position. Shots under 4 s are not addressed |
| Synergy rule (secondary source) | https://fansided.com/2017/09/08/nylon-calculus-understanding-synergy-play-type-data/ | Confirmed: no time cutoff, defense not set, a recovered defense is logged as the next action. Roles: leak-out man, ball-handler, left wing, right wing, trailer |
| NCAA fast-break points | http://fs.ncaa.org.s3.amazonaws.com/Docs/stats/Stats_Manuals/Basketball.pdf (curl, PDF text) | Confirmed: "Points scored on a quick counterattack following a change of possession before the offense or defense is set". The 2020-21 FT rule is there too: bonus FTs from a non-shooting foul to stop a break do not count |

`web.archive.org` blocks the WebFetch tool, so the two archived pages were fetched with curl and read as text. The Synergy and InStat pages were read through WebFetch.

### U1. Status of each reported research gap (final file vs the gap reports)

The researchers filed their gap reports before the verification pass and the A-additions, so several of them are now closed. The requirements session should use the "Now" column.

| Reported gap | Now | What it means for requirements |
|---|---|---|
| FastScout 10 s rule rests only on search summaries (Hudl 404) | **Closed.** Verified from the Wayback copy [V14a], re-opened in this pass | `tr_fastscout_10s` is firm. The stoppage test needs a **stoppage-event log** (substitution, foul, timeout, out of bounds, review, injury) per possession. Without it the flag cannot be computed from tracking alone |
| Hoop-Math 10 s confirmed only through the creator's 2012 article; hoop-math.com DNS failure | **Closed.** Verified from archived team and leaderboard pages [V7][V8][V10], re-opened in this pass | `tr_hoopmath_10s` is firm: initial FGA, starts limited to steal, DREB or opponent score, dead-ball TO excluded |
| "Ball live the whole time" clause | **Still unverified** (MGoBlog snippet behind a bot check) | Keep `tr_mgoblog_live_dreb` as a separately flagged variant. It is not Hoop-Math's rule. Never report it as Hoop-Math |
| Synergy glossary behind a login; subtype rules not public | **Still unverified** (wording); framework verified via Nylon Calculus [V1] | `tr_synergy_like` stays an approximation. Its defense-set test is ours (repo or CTG-like), not Synergy's (see Q9 above) |
| NCAA manual fast-break definition not found | **Closed.** Verified [V22], re-opened in this pass | `tr_ncaa_fbp` is firm. Box-score reconciliation must drop bonus FTs from stop-the-break fouls |
| NBA "6 s after a DREB" rule | **Still unverified** as an official rule (journalist [E11]) | Keep `tr_nba_6s_*` labelled "analyst proxy", never "NBA official" |
| FiveThirtyEight D-I 0.88 vs 1.03 | **Closed.** Archived copy [E3], opened by the fixer | Usable as a 2014-15 (35 s clock) reference only. See era note A3 |
| Harvard crash study [O85] HTTP 500 | **Closed.** Archived copy [E26], opened by the fixer | Correlational evidence only |
| No D-I PPP split by start event | **Closed.** Computed from ESPN play-by-play (A5; 2024-25 and 2025-26, about 0.7–0.8 million possessions per season) | Use the A5 start-type PPP as priors (steal 1.245, player DREB 1.103, made FG 1.049, made last FT 1.060, dead-ball-TO proxy 1.076; 2025-26, last 60 s of periods excluded) |
| No college data on possessions after made free throws | **Partly closed.** A5 gives made-last-FT starts 1.060 PPP, with 10.4% of possessions that reach an FGA taking the first one ≤ 10 s | Report made FG and made FT pushes separately (already in 1e). See finding F1 below on end-of-period contamination |
| Thresholds for lane width, defense set, trailer order, drag timing, cross-match, pull-back, run-out | **Still none published** | All stay [HEURISTIC]; calibrate on MSU film. "Run-out" has no formal definition anywhere: store it only as a coach-tagged label, never as a computed one |
| CTG league averages, Torvik pages, KenPom blog and APL, Second Spectrum | **Still blocked or unpublished** | Not needed for any computed flag. KenPom APL stays unverified; A3 uses a derived proxy (2400 / (2 × AdjT)) |
| No tracking-based fast-break detection paper validated against human labels (men's basketball) | **Still none** | Our hand-label pilot (§11, about 30 labels per definition) is the first validation. Budget for it |
| Wiens et al. Fig. 11 direction (crash/retreat vs MDET) | **Unresolved** | Do not hard-code a sign; fit it on our data |
| Brazil, Moselhy, U14, Refoyo 2009, IJPAS, MDPI 2025 fast-break studies | **Abstract or snippet only** | Context only. No threshold rests on them |
| Senior elite peak speed 20–24.5 km/h (5.6–6.8 m/s) | **Unverified** | Do not use it as a threshold. Use Stone et al. 2022 (D-I centres about 6.23 m/s) and each player's own peak (Job E) |
| Big Ten coverage thin (Purdue, Indiana, Wisconsin, UCLA; nine programs not researched) | **Partly closed.** A7 gives computed 2025-26 profiles for all 18 teams; qualitative coach statements still missing for UCLA, Oregon, USC, Minnesota, Northwestern, Penn State and Washington | Profiles are usable as numbers only. Coach-intent fields for those seven stay empty |
| MSU unverified scouting items (Free Press 2023 pressure, 2024 long outlets, PG sprints after makes, Fears minutes, Iowa 11.6 / 100 at 1.56 PPP, VCU pressing on makes, NCAA baseline-run rule) | **Still unverified** | Treat them as hypotheses for film checks, not as inputs |
| MSU 68.9% transition FG% (Spartan Avenue) | **Downgraded to unverified** (A4 correction; no source in the article) | Never quote it in reports |
| MSU 2024-25 and 2025-26 vendor transition splits | **Still missing** (Hoop-Math stopped Nov 2024; Synergy and KenPom paywalled) | Our play-by-play rules (A5, A7) and tracking are the only MSU source for those seasons |
| Note from the transition_full.md §12 Q1 wording ("Hoop-Math, FastScout and InStat are now verified") | **Correct** for the base rules after the verification pass | The InStat under-4 s question (Q2 above) is still open |

### U2. Findings from this pass worth carrying into requirements

- **F1. End-of-period possessions inflate the push-after-make rates** [calc, this pass, on the A5/A7 parsed 2025-26 possessions. The start-type split below uses all parsed games, and its 15.9% and 10.4% match the A7 and A5 figures. The Big Ten and D-I push rates use the A5 good-game filter]. Share of possessions after a made last FT whose first FGA came ≤ 10 s after t0: 15.9% with all possessions, 10.4% with the last 60 s of each period excluded, 62.6% inside the last 60 s (n = 7,233; intentional-foul endgames). After made FGs: 7.9% all, 7.2% excluding, 28.3% inside. After player DREBs the window hardly matters (52.3% / 52.4% / 51.8%). The A7 table includes end-of-period possessions; A5 excludes them. **MSU is still the Big Ten outlier with the last 60 s excluded**: push after a made FG or FT is 14.8% on offense (16.0% with all possessions), against 7.9% for D-I (9.8% with all possessions), so about 1.9 times the D-I rate. MSU allowed 4.9% (7.3% with all possessions). Michigan is next at 13.2%. Minnesota (1.0%), Purdue (1.6%) and Iowa (2.6%) push least. **Requirement:** every push-after-make and push-after-FT measure carries an `end_of_period` flag (possession starts with ≤ 60 s left in a period, game clock), and reports exclude those possessions by default.
- **F2. The t0 anchor differs between data sources.** `docs/requirements.md` (Transition clock) counts "from the catch". The A5 play-by-play parser anchors made-basket, made-FT and dead-ball-TO starts at the ending event (ball through the net), and CBB Analytics estimates about 3 s of inbound lag after a made basket [GF17]. Tracking can store all of them (1e: `t_net`, `t_inbound_release`, `t_inbound_catch`; 1b: `t0`, `t_outlet`). The §11 tracking-vs-play-by-play comparison must use the play-by-play anchor (`t_net`) for those starts, or the 10 s labels will disagree for timing reasons alone.
- **F3. The parser that made A5 and A7 is not in the repo.** The scripts (`parse.py`, `analyze.py`, `extra.py`, `bigten.py`) and the parsed possession files sit in a session temp directory (`/private/tmp/claude-501/-Users-aldemirkonuk-Projects-MSU-Alpha-3/78a04f2f-8cdc-419f-aeaf-2b5acdc69ad8/pbpwork/`), not in the scratchpad named in A5. macOS clears temp directories, so they will be lost unless they are copied (see new Q18).

### U3. New measurable items (one line each; signal and units)

From A1 (breaks stopped by foul):

- `tr_nba_tso`: transition scoring opportunity, true while the ball's velocity toward the attacked rim is ≥ 1.0 m/s in every 0.5 s window since t0 and A_play − D_back ≥ 1, or the handler's speed exceeds the deepest defender's retreat speed by ≥ 1.0 m/s (s of duration; thresholds [HEURISTIC]).
- `tr_nba_clear_path`: boolean; ball at y < 14.56 m (ahead of the tip of the backcourt circle, radius 1.83 m), no defender with smaller y than the attacker, who holds the ball or has a pass in the air.
- `t_foul_stop`: game-clock and shot-clock time (s) of a non-shooting defensive foul while `tr_nba_tso` or any §8.2 opportunity flag is active, before the first FGA.
- `foul_stop_ball_y` (m), `foul_stop_fouler_ball_dist` (m; > 1.0 m = no play on the ball [HEURISTIC]), `foul_stop_on_ball` (boolean), `t_foul_stop − t0` (s).
- `foul_category`: Fouled (stopped by foul), a fourth class next to Declined / Denied / Failed, with subtypes `foul_take_candidate`, `foul_side_out`, `foul_bonus_fts`, `foul_flagrant1`.
- `take_foul_when_beaten`: count per team per game of `foul_take_candidate` while A_play − D_back ≥ 1 or `tr_nba_clear_path`; share of opportunities ended this way; fouler role and foul count.
- `pbp_take_foul_candidates`: play-by-play count per game (A1 rule: first defensive foul 1–4 s after a live start, no FGA before it, no FT at that second, not in the last 120 s of the second half or OT). D-I reference 0.86 (2025-26) and 0.94 (2024-25) per game, both teams.

From A2 (possession value):

- `break_state(t)` at 10 Hz: numbers class (≥ +2, +1, even, ≤ −1), ball zone (backcourt y > 12.73 m; frontcourt outside the arc; inside the arc; paint), seconds since t0 bin (0–2, 2–4, 4–6, 6–8, 8–10, > 10 s), start type, handler speed class.
- `V_state`: fitted expected points (points per possession) for each break state, shrunk toward the A5 start-type PPP.
- `stake_passed_up`: V_push(s) − V_pull(s) (points) attached to every `passed_up` flag. A pull-back with stake ≤ 0 is never called a mistake.
- `stake_foul_stop`: V(state at t_foul_stop) − realised points after the foul (points).

From A3 (shot-clock eras):

- `clock_era`: 35 s (to 2014-15), 30 s (2015-16 to 2018-19), 30 s with the 20 s offensive-rebound reset and the 6.75 m arc (from 2019-20); stored per game.
- `tr_fastscout_10s` and `tr_nba_6s_clock` thresholds by era: reading ≥ 25 s (35 s clock) or ≥ 20 s (30 s clock); NBA proxy ≥ 29 s or ≥ 24 s.
- `season_pct_transition_share`, `season_pct_transition_efg`: MSU's percentile or z-score within the same season's D-I distribution (dimensionless). Never compare raw shares across eras.

From A4 and A5 (providers and play-by-play):

- `ext_cbba_chance_class`: CBB Analytics chance label (half court / transition / putback), stored as an external label only when available; its cutoff is unpublished, so we never compute it.
- `ext_espn_fbp`: official `fastBreakPoints` from the ESPN box (points per game), for the §11 reconciliation (MSU 2025-26: 15.6 per game in 33 parsed games vs 16.4 / 16.2 in season releases).
- `pbp_start_type`: steal, player DREB of a missed FG, team or dead-ball DREB, DREB of a missed FT, turnover without a steal (dead-ball proxy), made FG, made last FT, period start.
- `pbp_early10`: first FGA ≤ 10 s after the play-by-play t0 (boolean; 1 s clock resolution), with PPP split early vs other per start type.
- `end_of_period`: possession starts with ≤ 60 s left in a period (F1).
- `inbound_lag_pbp`: tracking `t_inbound_catch − t_net` (s), to calibrate the about 3 s lag that CBB Analytics assumes.

From A6 (value by numbers advantage):

- `adv_class_at_cross_half`, `adv_class_at_first_shot`, `adv_class_max` (≥ +2, +1, even, ≤ −1, with full labels such as 2v1 and 3v2 as sub-rows).
- `ppp_by_adv_class` with 95% CI (points per possession). About 553 possessions per class give ±0.10 and about 138 give ±0.20. Pool MSU and opponents; report CIs, never point values alone.
- Outcomes per class: P(FGA at r ≤ 1.22 m, the restricted-area radius), P(turnover), P(stopped by foul).

### U4. Suggested definitions to add (each kept separate; nothing merged)

| Field | Definition | Owner / status |
|---|---|---|
| `tr_nba_tso` | Continuous advance from t0 with an advantage from speed or position (thresholds in U3) | NBA rule concept [GF1][GF2]; thresholds [HEURISTIC] |
| `tr_nba_clear_path` | Ball ahead of the tip of the backcourt circle (y < 14.56 m), no defender ahead of the attacker, attacker holds the ball or a pass is released | NBA Rule 12-B [GF3]; geometry derived |
| `foul_take_candidate` (tracking) | Non-shooting defensive foul during an opportunity, fouler > 1.0 m from the ball, before the first FGA | [HEURISTIC]; no NCAA take-foul rule found |
| `pbp_take_foul_candidate` | A1 play-by-play rule (U3) | [calc-GF]; superset of take fouls on the side-out branch, misses fouls in the bonus |
| `pbp_early10` | First FGA ≤ 10 s after the play-by-play t0, all start types | Hoop-Math-like timing, **not** Hoop-Math (that rule counts initial FGA only, from steal, DREB or opponent score) |
| `ext_cbba_chance_class` | Scorer's fast-break tag plus CBB Analytics' own possession-length analysis | CBB Analytics [GF16][GF17]; cutoff unpublished |
| ShotQuality, EvanMiya, Second Spectrum | No public definition; record "not published" and do not invent one | [GF18][GF19][V27] |
| Repo state-based view (`tr_repo_phase`) | Unchanged; one field among the others | [REPO] |

### U5. New open questions for Aldemir (one line each; continues the numbering above)

17. Which tracking proxy defines `foul_take_candidate` (fouler-to-ball distance > 1.0 m, and which time window after t0)?
18. Should the ESPN play-by-play parser (A5) and its parsed files be copied into the repo now, before the temp directory is cleared, as the reference possession builder?
19. For seasons before 2015-16, do we store 35 s shot-clock thresholds for FastScout and the NBA 6 s proxy, or exclude those seasons from clock-based labels?
20. Do push-after-make and push-after-FT reports exclude possessions that start in the last 60 s of a period by default (F1), and is 60 s the right window?
21. Which t0 is the reporting default for made-basket starts: `t_net` (matches play-by-play), `t_inbound_release`, or `t_inbound_catch` (the requirements doc's "from the catch")?
22. Should a CollegeBasketballData API key be requested? It is free but needs an account, which only you can create.
23. Can you download the 2025-26 NCAA men's rule book PDF (over the 10 MB fetch limit) so the baseline-run and Flagrant 1 wording can be confirmed?
24. Is a CBB Analytics or Synergy subscription worth it for a one-off label check of our transition flags against a vendor (ties to Q12)?
25. Should run-out be dropped as a computed label and kept only as a coach-tagged label, since no formal definition exists?
26. Which seven Big Ten programs without coach statements (UCLA, Oregon, USC, Minnesota, Northwestern, Penn State, Washington) need qualitative research before their profiles are used?
27. Should MSU's 2019-20 Hoop-Math row (same 52.6% eFG in transition and non-transition, likely an artefact) be checked on the archived team page or dropped from trend charts?
