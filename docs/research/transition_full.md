# Transition: the whole transition game, in both directions

Research document for MSU Alpha 3, Job D of `coord/prompts/002-claude-code-taxonomy-and-markets.md`. Written 2026-10-17.

It covers everything that happens while the ball changes ends, in both directions: defense to offense (the break, early offense, flow into the half-court) and offense to defense (getting back, stopping the ball, matching up, cross-matching). It adds to `docs/taxonomy/offense_full.md` (F1 primary transition, F2 secondary/early offense) and `docs/taxonomy/defense_full.md` (F12 transition defense). It does not replace them. Where those files already hold a rule, this file cites it as **[REPO]** and only adds what the new sources say.

**The core rule of this document.** Analysts do not agree on what "transition" means. This file never folds their definitions into one. Every definition is kept as its own row, with its own unit, time cutoff and state cutoff (§5), and the suggested data model stores one field per definition for every possession (§5.4). Aldemir's earlier state-based definition (the repo `PHASE` rule) is kept as one view among many.

**Tags used throughout:**

- **[V#], [E#], [P#], [C#], [M#]**: a source that a researcher opened during this task. Every key resolves to a URL in the Sources section at the end. V = vendors and analyst definitions; E = efficiency and evidence articles and data; P = peer-reviewed and conference papers; C = coaching sources; M = Michigan State and Big Ten sources.
- **unverified**: the claim was seen only in a search-engine summary, or the page could not be opened. Do not rely on it until someone opens the page.
- **[HEURISTIC]**: a threshold proposed for a tracking signature. No source states it. Calibrate it on MSU film before use.
- **[REPO]**: a value already in `offense_full.md` or `defense_full.md`, repeated for comparison.
- **[calc]**: a number a researcher computed in this task from tables they opened (method stated where it appears). These are descriptive, mostly cross-team correlations, not causal estimates.
- **[derived], [X-derived]** (e.g. [C25-derived], [C38-derived], [C8-derived], [REPO-derived]): a number the researcher computed from court geometry, or from text or a diagram in source X (or the repo), that the source does not state as a threshold. Treat it as [HEURISTIC] for calibration.
- **[REPO/HEURISTIC]**: a rule that combines a repo value with a researcher-proposed threshold; calibrate it like [HEURISTIC].
- **Source status of P keys**: the P list mixes peer-reviewed journal articles, conference papers (SSAC/Sloan), preprints (arXiv) and abstract-only records. Each P key carries a status in the Sources table (journal / conference / preprint / abstract only / other); §10 weighs evidence by that status.

Fixer pass 2026-10-18: verifier findings were applied on this date (definition of Hoop-Math transition, season of the Lakers numbers, quote attribution, snapshot dates, overlapping state bins, split variant fields, and others). New sources opened on 2026-10-18 are marked "(opened 2026-10-18)" in the Sources section.

---

## Contents

1. Scope and notation
2. Glossary of transition terms (both directions), with aliases and measurable signatures
3. Phase model with timestamps (offense: outlet to flow; defense: get back to cross-match)
4. Player roles in the break
5. Analyst definitions side by side (never merged)
6. Start-type taxonomy with points-per-possession evidence
7. Pushing after made baskets and made free throws
8. Passed-up breaks: opportunities not taken, and how to detect them
9. Coaching systems (MSU first, Big Ten, named breaks) and defensive transition rules
10. Evidence summary
11. Comparing tracking-based labels with play-by-play, game by game
12. Open questions
- Sources

---

## 1. Scope and notation

### 1.1 Scope

In scope:

- **Offensive transition** (defense to offense): possession gain, outlet, advance, primary break, secondary break, early offense, flow into the half-court, pull-back.
- **Defensive transition** (offense to defense): the crash-or-retreat decision at the shot, getting back, protecting the basket, stopping the ball, matching up, cross-matching, switching back.
- **Start types**: defensive rebound, live-ball turnover, dead-ball turnover, made field goal, made free throw (and the others a data provider lists).
- **The evidence base**: efficiency of transition, efficiency by start type and by seconds into the possession, the offensive-rebounding versus getting-back trade-off, transition share versus winning.

Out of scope here: speed-band thresholds for "sprint" (Job E, `docs/research/load_thresholds.md`) and press offense or press defense as half-court schemes (`offense_full.md` F12, `defense_full.md` F9). Press and transition overlap; the overlap is noted where it matters.

### 1.2 Units and court frame

- Units: metres, seconds, degrees, m/s. Any source value given in imperial units was converted at 0.3048 m per foot by the researcher who opened it. No imperial values appear in this file.
- Court positions use the project frame in `config/vocabulary_map.yaml`: the origin is the centre of the **attacked** rim projected to the floor; **r** is the distance from it in metres; **θ** is in degrees from the right baseline, measured at the rim centre (0° = right baseline, 90° = straight up the floor, 180° = left baseline). Helper coordinates, as in `offense_full.md`: x = r·cos θ (across the court), y = r·sin θ (toward half-court).
- When a measurement sits near the team's own (defended) rim, such as a rebound or an outlet, this file says **own-rim frame**: the same convention, centred on the defended rim.

### 1.3 NCAA men's court constants used in the signatures

All values come from the 2025-26 NCAA Men's Basketball Rules Book [C16], converted to metres.

| Constant | Value | Notes |
|---|---|---|
| Court | 28.65 m × 15.24 m | Sidelines at \|x\| = 7.62 m |
| Rim centre to end line | 1.60 m | Backboard face 1.22 m from the end line + 0.152 m to the ring's inner edge + 0.229 m ring radius [C16]. `offense_full.md` uses 1.575 m [REPO]; the 2.5 cm difference does not change any signature |
| Free-throw line | y = 4.19 m (r = 4.19 m, θ = 90°) | Matches `nail` in `vocabulary_map.yaml` |
| Half-court (division) line | y = 12.73 m: r = 12.73 m at θ = 90°; at a sideline r = 14.83 m, θ = 59.1° (mirror 120.9°) | Measured to the centre of the line |
| The team's own rim | y = 25.45 m | Rim to rim |
| CTG "scoring zone" line | y = 10.29 m (r = 10.29 m at θ = 90°) | 2.44 m past half-court [V18] |
| Three-point line | r = 6.75 m at the top, 6.60 m in the corners | |
| Free-throw line extended meets the arc | r = 6.75 m, θ = 38.4° (mirror 141.6°), \|x\| = 5.29 m | The FIBA "wing" spot: "where the 3-point arc meets the free throw line extended" [C1] |
| Lane | \|x\| ≤ 1.83 m | 3.66 m wide |
| Shot clock | 30 s; reset to 30 s on a change of team control; 20 s after an offensive rebound that hits the ring | [C16]; `offense_full.md` `CLOCK` [REPO] |
| Backcourt count | 10 s; starts on player control after a rebound | [C16] |

### 1.4 Time anchors (names used in every section)

| Symbol | Meaning |
|---|---|
| t0 | Possession gain. Defensive rebound: first two-hand control. Steal: the new offense's first possession touch, as CTG anchors live-ball turnovers [V18]. After a make or a free throw: the inbounder's first touch (with "ball through the net" stored separately for push measures, §7) |
| t_rel | Shot release (for the crash-or-retreat decision) |
| t_outlet | Catch of the first pass after a defensive rebound |
| t_cross_half | Ball crosses y = 12.73 m |
| t_scoring_zone | Ball enters y ≤ 10.29 m (CTG anchor [V18]) |
| t_three_zone, t_paint | Ball first inside r ≤ 6.75 m; first paint touch (CTG has both [V18]) |
| t_first_shot | First field-goal attempt or shooting foul |
| t_defense_set | Defense judged set. Two definitions are kept: **repo** = all 5 defenders behind the ball at r < 9 m for ≥ 1 s [REPO]; **CTG-like** = 5 defenders back, or 4 back with low average speed, at frontcourt entry [V18]. CTG publishes no numeric thresholds for "reasonably ahead" or "low speed" [V18] |

### 1.5 Source-status reconciliation

Five researchers worked in parallel, and some of them could open a page that others could not. The status used in this file is the best one any researcher reached:

| Item | Status in this file | Detail |
|---|---|---|
| FastScout definition | **Verified** [V14][V14a] | One researcher opened the Hudl support article in a browser (rendered). A later WebFetch of V14 returned only "Loading / CSS Error" (JavaScript-rendered page), so V14 is not reproducible by fetch. On 2026-10-18 the fixer opened a static Wayback copy of the original FastModel article (snapshot 12 Dec 2024) [V14a], which confirms the core rule, the stoppage list, the possession-start list (including "Made Basket … (except in cases of an and-one)" and the same exception after a made final FT) and the possession-end list |
| Hoop-Math definition | **Verified** via the creator's article [V5], a contemporaneous user [V6] and archived Hoop-Math pages [V7][V8][V10]. Rule as printed on the pages: "Transition shots are defined as occuring within the first 10 seconds of a possession after a steal, defensive rebound, or opponent score" [V8]; the leaderboard says "after a steal, rebound, or made basket by the opponent" [V10]. Dead-ball-TO starts are tabulated separately [V7] but are not part of Hoop-Math transition [V6][V8] (re-checked 2026-10-18) | hoop-math.com itself does not resolve in DNS (checked 2026-10-17). Hoop-Math stopped updating in November 2024 [V12] |
| Hoop-Math "with the ball live the whole time" clause | **Unverified** | Seen only in a search snippet of an MGoBlog post behind a bot check. Treat it as a Michigan-blog variant (live ball, DREB start), not Hoop-Math's site-wide rule |
| NCAA "Fast Break Points" definition | **Verified** [V22] | One researcher opened the NCAA Statisticians' Manual 2025-26; another had not found it |
| NBA scorer's fast-break rule ("within 6 s of a defensive rebound") | **Unverified as an official rule** | A 2013 journalist's claim [E11]; no NBA rulebook text was found |
| FiveThirtyEight 2015 college Synergy numbers | **Verified** via an archived copy [E3] | The live URL redirects to ABC News |
| Harvard Sports Analysis 2017 college crash study (repo `[O85]`) | **Verified** via an archived copy [E26] | The live page returned HTTP 500 to three researchers |
| MSU 31–0 fast-break points vs Maryland (2026-01-24) | **Verified** [M5] | One researcher opened the CBS game page; another saw it only in a search result |
| Synergy's own glossary wording | **Unverified** | Login-gated; the definition comes from Nylon Calculus [V1] |
| Direction of the MDET vs crash/retreat link in Wiens et al. Fig. 11 | **Unresolved** | The paper's text and its stated hypothesis disagree (§10.4) [P1] |

---

## 2. Glossary of transition terms (both directions)

Each entry gives the definition(s) found, aliases, and a measurable signature. Signatures use the attacked-rim frame unless marked "own-rim frame". Shared variables: `v` = speed (m/s); `v_y` = velocity along y (negative = moving toward the attacked rim); `y_ball` = ball's y. Counts `A_play`, `D_back`, `D_even`, `D_behind` are defined in §3.4 (mutually exclusive bins, [HEURISTIC]).

**Geometry of "between" (used by several signatures) [HEURISTIC].** A defender is **between attacker P and the attacked rim** if he has y < y_P and lies within 1.5 m of the straight segment from P to the rim centre, or inside the triangle formed by P and the two rim-side lane corners (x = ±1.83 m, y = 0). A defender is **between the ball and shooter S** if he lies within 1.5 m of the ball-to-S segment, or within 3.0 m of S. Store both variants (segment and triangle) until calibrated.

### 2.1 Umbrella terms

**Transition offense (offensive transition)**
- Definition: converting from defense to offense after gaining possession [C1]; a family of strategies that aim to score quickly after gaining possession [C19]. Hudl InStat's 2022 glossary places "transition offense" *between* the fast break and the set half-court offense [V16]; Spanish and Portuguese research uses "transition" in the same narrow sense, as the "second wave" after an unfinished counterattack, ball never stopped [V48]. These narrow meanings conflict with Synergy, where the fast break *is* transition [V1]. Keep both meanings (§5).
- Aliases: offensive transition, the break, running, open floor, open court, fast break (loosely), counterattack (European literature).
- Signature: the window t0 → t_defense_set, plus every analyst flag in §5.4. Continuous measures: t_cross_half − t0; t_scoring_zone − t0; ball speed to the scoring zone (distance to y = 10.29 m ÷ time, m/s, as CTG's `ball_speed_to_scoring_zone` [V18]); t_paint − t0; t_first_shot − t0.

**Transition defense (defensive transition)**
- Definition: converting from offense to defense [C1], after a made or missed shot or a live-ball turnover, to prevent the opponent's transition offense [C3]. Components in coaching order: protect the basket, stop the ball, match up [C3][C4].
- Aliases: getting back, floor balance, retreat, recovery.
- Signature: crash and retreat counts at t_rel (§2.5), then t_protect, t_stop, t_matched and MDET (§3.3), plus CTG-style `defenders_back`, `defenders_even` and `avg_defender_speed` at frontcourt entry [V18].

**Fast break**
- Definitions (kept apart):
  - FIBA terminology: after a defensive rebound, steal or made shot, the team "pushes the ball toward the other basket as fast as possible" to catch the opponent off guard [C1].
  - FIBA box score: points scored "quickly (max. 8 seconds)" before the opponent's half-court defense is set [V23].
  - NCAA box score: points "scored on a quick counterattack following a change of possession before the offense or defense is set", no time cutoff [V22].
  - Conte et al. 2017: a possession lasting < 8 s [P2]. Matulaitis & Bietkis 2021: a primary or secondary break that finishes within 5 s [P12]. Bourgeais et al. 2024 (preprint, arXiv:2404.01909v1, "PREPRINT VERSION – March, 2024"; sample 12 games of the 2019 FIBA World Cup): a 6 s window, because 9 of 10 fast breaks last under 6 s (a figure from Cárdenas et al. 2015 as cited by Bourgeais), noting the value is FIBA-specific and probably not right for a 30 s clock [P4].
  - Doc Rivers ties it to numbers, not time: "Fast break to me, is if you can create numbers" [E11].
- Aliases: break, transition, counterattack, run-out (informal, see below).
- Signature: store each variant separately: first FGA or foul ≤ 5.0 / 6.0 / 8.0 / 10.0 s after t0, each with and without "before t_defense_set"; plus a numbers flag (A_play > D_back at t_cross_half).

**Primary break**
- Definition: the first phase, against an outnumbered defense, generally within the first 2–3 s after gaining possession [C2][C19]. FIBA: involves "only a few players from each team" [C1]. Conte's coding by attackers versus defenders actively involved: 1v0, 1v1, 2v1, 2v2, 3v1, 3v2, 3v3, 4v2 [P2]. Trninić typology (Croatian school, via Jeličić 2021): the end zone involves ≤ 2 defenders (1:0, 2:1, 3:1, 1:1, 2:2, 3:2) [P27]. Roy Williams' operational rule: ≤ 2 defenders back means score within ≤ 2 passes [C15][C23].
- Conflict to keep: Conte and Trninić count equal numbers (2v2, 3v3) as primary because few players are involved [P2][P27]; coaching sources tie the primary break to a numbers advantage [C2][E11]. Store both a typology label and an advantage flag.
- Aliases: primary transition, first wave, numbers break, traditional fast break.
- Signature [HEURISTIC]: at t_cross_half, `prim_conte` = configuration (A_play v D_back) in Conte's primary list (1v0, 1v1, 2v1, 2v2, 3v1, 3v2, 3v3, 4v2) [P2] (earlier wording "A_play ≤ 3, or A_play = 4 with D_back ≤ 2" kept as `prim_conte_loose`); `prim_trninic` = ≤ 2 defenders in the end zone [P27]; separately, `roy_williams_window` = D_back ≤ 2 at t_cross_half, and `passes_to_shot` ≤ 2.

**Secondary break**
- Definition: runs after the defense has sprinted back and stopped the primary, but before it is fully set; more structured than the primary [C19][C20]. FIBA: involves "most of the players from each team" [C1]. Conte: 4v3, 4v4, 5v4 [P2]. Trninić: 3–4 defenders in the end zone (3:3, 4:3, 5:3, 5:4) [P27]. Roy Williams: run it when more than 2 defenders are back, with ≥ 3 passes unless there is a layup, side to side, and the ball into the post [C15]. NBC Sports' glossary: "secondary transition" is when the break starts but includes another action (quick PnR, drag, quick post, screen for a cutter), later in the shot clock [V43].
- Aliases: secondary, secondary transition, numbered secondary, "the secondary".
- Signature: three named fields, each stored separately (the same fields are used in §3.4):
  - `sec_conte` = numbers configuration (A_play v D_back at t_cross_half) ∈ {4v3, 4v4, 5v4}, Conte's own secondary configurations [P2].
  - `sec_trninic` = 3 or 4 defenders in the end zone (Trninić 3:3, 4:3, 5:3, 5:4) [P27].
  - `sec_heuristic` [HEURISTIC] = A_play ≥ 4 and D_back ≥ A_play − 1, after the primary window and before t_defense_set or a named set. (This rule excludes 5v3, which `sec_trninic` includes; keep both.)
  - Markers: wings in the corners (r 6.60–7.3 m, θ ≤ 12° or ≥ 168°), a trailer at r 6.5–8.5 m, θ 70–110° [REPO], a duck-in at the ball-side block.

**Early offense**
- Definition: high-tempo offense that punishes the defense before it retreats, inside the **first 8 s** of the attack (Purrà), using simple actions and screens: empty-side and step-up PnR, high and top PnR, transition PnR variants (veer, 5-out, flare, Spain, double drag "77", inverted, guard-guard, iso), screen away, pin-down and corner exit, handoff options (flip, handback, give, Miami, stagger away), secondary break (Delay, post iso), Argentina [C10]. Trninić: early offense is 5v5 where the positional phase is shorter than the transition phase [P27]. HoopTactics' three phases: Early Push (ball in the offensive operating area within 2–4 s), Early Flow, Continuity [C29]. Hollinger described D'Antoni's "7 seconds or less" as mostly drag screens and quick early-clock plays rather than pure fast breaks [C35].
- Aliases: early, early action, early O, quick-hitters, transition PnR, "7 seconds or less".
- Signature: the first actions (SCREEN, DHO, CUT, as defined in `offense_full.md` §0.2 [REPO]) within t0 + 8.0 s, and separately within t0 + 15.0 s (the Jeličić sample cap [P27]); label each action with its time since t0 and since t_cross_half.

**Flow (flow into the half-court)**
- Definition: moving from the break into the half-court offense without stopping or resetting. "Flow immediately into this setup when changing ends" (Lakers, Prada) [C27]. HoopTactics moves to Flow "as soon as" the push yields no good shot [C29]. Izzo's 2010 clinic break flows into the flex continuity [M18].
- Aliases: flow, flow offense, flow into motion, "no pause".
- Signature: from the end of the secondary to the first half-court action, no interval ≥ 1.0 s with ball speed < 0.5 m/s [REPO]; the ball does not return to y > 9.0 m; the first half-court action starts ≤ 2.0 s after the last transition action [HEURISTIC].

### 2.2 Mechanics of the break

**Push**
- Definition: the ball-handler, or the player who gets the steal or rebound, advances the ball quickly; "you must decide who will push the ball" [C22]. Pushing after made field goals and made free throws is a stated Pacers trait [C17]. Roy Williams: get the ball out of the net as fast as possible; wings release as soon as the ball is scored [C23]. Izzo: "Go hard, go fast but be under control" [M1].
- Aliases: push it, push the pace, run, speed dribble, bust out.
- Signature [HEURISTIC]: after a DREB or steal, handler speed ≥ 4.0 m/s sustained ≥ 1.5 s in the backcourt and t_cross_half − t0 ≤ 4.0 s [REPO uses ≤ 4 s for the speed-dribble advance]. After a make or a free throw, see §7.

**Run-out**
- Definition: no formal definition was found in any glossary or provider documentation (two searches). It appears to be informal for a breakaway, often after a steal or long rebound (**unverified**).
- Aliases: runout, breakaway, coast-to-coast (one player).
- Proposed signature [HEURISTIC]: start type live-ball turnover or a long rebound (rebound at r ≥ 6.0 m from the shooter's rim), plus at least one attacker with no defender between him and the attacked rim (geometry defined in the §2 intro: no defender with y < y_attacker within 1.5 m of the attacker-to-rim segment, or inside the attacker/lane-corner triangle; store both) at any time ≤ t0 + 3.0 s.

**Leak-out**
- Definition: a player slips ahead of the defense during the change of possession. Corey Brewer challenges the shot, then "takes a direct step in the opposite direction" once he sees the rebound being secured [C6]. "Leak-out man" is a Synergy transition role [V1]. In the 2019-20 Lakers' break, Davis "immediately leaks out to get behind the defense" after closing out [C27].
- Efficiency: EuroLeague 2018-19, "hit-aheads / leak-outs" averaged 1.47 PPP, the highest transition sub-type (EuroLeague analysis via Eurohoops; data provider not named; Synergy is credited only for the 10% transition share) [E4]. Brewer had 28.1% of his offensive possessions in transition (Synergy) [C6].
- Aliases: leaking, release, early release, cherry-pick (if he leaves before the shot or rebound).
- Signature [HEURISTIC]: a player of the team about to gain possession reaches v_y ≤ −3.0 m/s with onset ≤ t0 + 0.5 s and is the first attacker across y = 12.73 m. Sub-types: **early leak** = onset before t0; **cherry-pick** = onset before t_rel, or the player never contested the shot. Store his y minus the deepest defender's y at t_cross_half.

**Outlet**
- Definition: (1) the pass after a defensive rebound that starts the break; (2) the player who stays in the backcourt to receive it [C1]. Usually an air pass; a long outlet is a "touchdown pass" [C13]. Roy Williams: outlet to the ball side, "because it's faster" [C15]. In MSU's progressive drill the rebounder outlets to a teammate coming from the sideline [C28].
- Outlet spots (own-rim frame): ball-side wing in line with the elbow, outside the arc ("outside the three-point line in a direct path from the free throw elbow" [C21]), roughly r_own 6.75–8.5 m, θ_own 30–45° (mirror 135–150°) [derived]; middle outlet \|x\| < 1.83 m, y_own 6–10 m [REPO]; long outlet: two separate fields, `long_outlet_zone` = catch at y ≤ 10.29 m in the attacking frame [HEURISTIC, derived] and `long_outlet_len15` = first pass length ≥ 15 m [HEURISTIC] (the version used in §9.3). Hoiberg's outlet receiver catches with his "butt to the sideline" above the free-throw line extended [C25].
- Aliases: outlet pass, first pass, kick-ahead (if long), touchdown pass.
- Signature: first PASS after a DREB, from the rebounder. Store delay (t_release − t0; repo: ≤ 1.5 s [REPO]), length (m), receiver spot (r_own, θ_own), ball side (same sign of x as the rebound), and CTG's `outlet_height` = catch distance from the non-attacking baseline (midcourt = 14.33 m) [V18].

**Advance (pass vs dribble)**
- Definition: how the ball reaches the frontcourt. Coaching consensus: "the ball moves faster using the pass than with dribbling" [C22]. Izzo prefers diagonal dribbling; straight-line dribbling caused turnovers [M1].
- Measured shares: Conte, elite Italian games: 73.9% of fast breaks advanced by dribble, 26.1% by pass; 72.1% through the centre zone [P2]. Cárdenas et al. 2015: elite teams used ≤ 2 passes in 96.4% of fast breaks, and success rose when the initial action was a pass [P3].
- Aliases: hit-ahead, pitch-ahead, headman, pass-ahead; speed dribble, push.
- Signature: `advance_mode` = "pass" if the ball is in flight when it crosses y = 12.73 m, or if the forward pass with the most negative Δy (Δy ≤ −8 m; negative = toward the attacked rim, §2 intro) happens before the crossing; otherwise "dribble" [REPO/HEURISTIC]. Store passes from t0 to the first FGA, dribble heading off the court's long axis (MSU diagonal rule: 20–45° over ≥ 10 m [REPO]), and the lane at the crossing (§2.2, lane filling).

**Hit-ahead / pitch-ahead / headman**
- Definition: a forward pass ahead of the handler to a teammate in front [C22][C17]. The MSU rule is to pass before the timeline or go to the secondary [M17].
- Signature: PASS with Δy ≤ −8 m made before the passer crosses y = 12.73 m, or within 1.5 s after [REPO]. `passed_before_timeline` = forward pass while the handler is at y > 12.73 m [M17].

**Rim run (rim runner)**
- Definition: "a big who runs in fastbreak/transition from her/his defensive rim to the offensive one", also "Rim-Rim Run" or "Basket-Basket Cut" [C1]; a big runs "the length of the floor once his team has possession" [C7]. Roy Williams: one big sprints to the front of the rim on makes and misses [C23]. MSU, in Michigan assistant Kyle Church's words: "the first big down puts pressure on the rim" [M13].
- Aliases: rim runner, rim-to-rim, basket-to-basket, sprint the middle.
- Signature: two named variants, stored separately. `rim_run_repo` [REPO]: a big's speed ≥ 5.5 m/s for ≥ 2 s and the path ends at r < 2.5 m before the ball reaches y < 7 m (`offense_full.md` F1, rim runner; used again in §9.3 "First big"). `rim_run_path` [HEURISTIC]: path starts at r_own ≤ 4.0 m and ends at r ≤ 2.5 m; path length ≥ 20 m; mean \|x\| ≤ 3.0 m; arrival before the ball reaches r < 6.75 m or within 1.0 s after.
- Calibration warning: the repo threshold "≥ 5.5 m/s for ≥ 2 s" [REPO] may be too strict. Mean per-quarter peak speeds of elite U18 players were 5.2–5.5 m/s (LPS, 20 Hz, 94 players, 13 games) [P28]. NCAA D-I men's game maximum speeds (Kinexon IMU, 20 Hz, 27 games of 2020-21, one team) were guards 7.04 ± 0.39, forwards 6.63 ± 0.52, centres 6.23 ± 0.33 m/s; the paper says 10 players but its position split lists 4 + 3 + 4, and its Methods give speed in mph while Table 3 is in m/s (Stone et al. 2022, re-opened 2026-10-18) [P41]. A centre peaking at 6.23 m/s would need 88% of his game maximum for 2 s to meet the repo rule. Prefer a threshold relative to each player's own peak (see also `docs/research/load_thresholds.md`).

**Lane filling (sideline lanes, lane-line lanes, middle lane)**
- Definition: "a fast break in which players … run up the court in the right lane, the middle lane, and the left lane" [C1]; wings run just inside the sidelines to give the dribbler space [C18]; Roy Williams: lanes as wide as possible [C15], wings "flying down the sidelines to the corners" [C23]. Five-lane / five-out breaks keep the middle open for the drive [C38]. The Carolina break keeps the handler in the middle third, wings on the sidelines and bigs in the inner lanes [C30].
- Aliases: run the lanes, fill the lanes, get wide, touch the sideline.
- Signature [HEURISTIC], measured while the player is between y = 22 m and y = 6 m (this is the canonical `wing_lane` signature; §4 uses it, and the different window in §9.3 is stored as the named variant `msu_wing_lane_v2`): **sideline lane** 5.3 ≤ \|x\| ≤ 7.62 m (outside the free-throw-line-extended/arc meeting point); **lane-line lane** 1.83 ≤ \|x\| < 5.3 m; **middle lane** \|x\| < 1.83 m. A five-bin alternative uses equal 3.05 m bins across 15.24 m [C38-derived]. Store the lane at t_cross_half, lane stability (\|dx/dt\| < 1 m/s before y < 12.73 m [REPO]), the count of occupied lanes, a middle-open flag, and lateral spread = max(x) − min(x) of attackers ahead of the ball (CTG's `team_y_spread` is the same idea on CTG's axes [V18]).

**Trailer (first and second trailer)**
- Definition: "an offensive player, usually a center or a power forward, who trails the first wave" [C1]; the last player down, who goes to the opposite elbow [C11]. CTG Pro's `trailer` role: more than about 1.5 s behind the ball, or set a drag screen [V19]. MSU wants a shooting 4 or 5 trailer for a pitch-back three [M17][REPO].
- Efficiency: EuroLeague 2018-19: trailers were the only transition role no more efficient than the average half-court possession (EuroLeague analysis via Eurohoops; provider not named) [E4].
- Aliases: trail, trail big, first/second trailer, 4-man trail.
- Signature [HEURISTIC]: order attackers by the time each crosses y = 12.73 m; first trailer = 4th across, second trailer = 5th across. Store delay = t(trailer crosses) − t(ball crosses), arrival spot (top/slot r 6.5–8.5 m, θ 70–110° [REPO], or the opposite elbow at r 4.57 m, θ 66.4° / 113.6°), and actions (drag, trailer three, reversal, high-low).

**Drag and double drag**
- Definition: drag = "an on-ball screen set traditionally in transition for the ball handler in order to make her/him dribble towards the middle"; double drag = "a two person staggered on-ball screen" [C1]. Hoiberg's trailer sets the drag "at, or just inside, the 3-point arc", then rolls [C25]. Double drag is "77"; the first screener is about one body length higher than the second, and the second often pops [C8].
- Aliases: drag screen, transition ball screen, "7"; double drag, "77", double stagger ball screen; drag flare, drag slip, drag veer, inverted drag [REPO].
- Signature: drag = ball SCREEN whose screener had v_y ≤ −3.0 m/s in the 1.5 s before contact [REPO], screen point at r 6.0–7.5 m [C25-derived], within 8 s of t0 [REPO]. Double drag = two ball screens on the same handler ≤ 1.5 s apart, both at r ≥ 6.0 m, screener positions 0.7–1.5 m apart along the handler's path [C8-derived]. Record roll (r < 3 m within 1.5 s), pop (r ≥ 6.75 m) or slip.

**Transition three / pitch-back three**
- Definition: a three inside any transition flag. The trailer pitch-back three is a named MSU option [M17].
- College numbers: transition threes made 35.8% (2014) and 35.5% (2019); threes were 27% of transition FGA in 2010 and 35% in 2023-24 (Synergy via Hoop Vision) [E2]. Hoop-Math: threes within 10 s of an opponent score went in 32% (30% within 5 s), D-I 2011-12 [V5].
- Signature: FGA at r ≥ 6.75 m (≥ 6.60 m in the corners) inside any transition flag; record the shooter's role.

**Pull back / reset**
- Definition: stop the break and pull the ball out to run the half-court offense when no good shot exists: "pull it out and run your normal offense" [C26]. A FastModel note to the same effect was seen only in a search summary (**unverified**).
- Aliases: pull it out, back it out, reset, flatten out, get into offense.
- Signature [HEURISTIC]: after t_scoring_zone, the ball moves away from the rim (Δy ≥ +2.0 m within 3.0 s), or the handler holds at r ≥ 7.5 m with v < 1.5 m/s for ≥ 1.5 s; with no FGA, foul or paint touch in that window; followed by a set call or an ALIGN template [REPO]. Store `pulled_back`, t_pull − t0 and the numbers state at t_pull (feeds §8).

**Numbers advantages (2-on-1, 3-on-2, 4-on-3, 5-on-4)**
- Teaching rules [C28][C4]:
  - 2v1 offense: attack the hoop first with an in-and-out dribble, pass second, no jumpers. 2v1 defense: get "as low as the lowest offensive player", give up the jumper, gap the passing lane.
  - 3v2 offense: the top handler does not go past the free-throw line and stays above for the reverse pass. 3v2 defense: stack the two defenders; the top one stops the ball, the bottom one takes the first pass, the top one drops to the paint.
  - 4v3 / 5v4 offense: run the lanes and sidelines, keep spacing, drive and dish or kick. Defense: stop the layup, communicate, box out.
- Success rates by situation (EuroBasket 2001 and Greek A1, 50 games): 1v0 90.9%, 4v2 80%, 3v1 79.4% [P20].
- Aliases: odd-man rush, numbers, outnumbered break, even break.
- Signature: A_play v D_back at t_cross_half, t_scoring_zone and t_first_shot, plus the full time series at 10 Hz (§3.4).

**Banana cut (wing curl on the break)**
- Already in `offense_full.md` F1.5: wing path curvature > 0.15 m⁻¹ with the final heading toward the rim [REPO]. No new source was opened.

### 2.3 Defensive transition terms

**Crash and retreat at the shot (Wiens et al. 2013)**
- Aliases: crash or get back, crash-and-retreat, glass or floor balance, send N to the glass, "crash vs. leak".
- Definition, from NBA SportVU tracking [P1]: at shot release, **PI** = attackers within 2.44 m of the basket; **PO** = attackers beyond 10.06 m; **NPC / NPR** = "neutral" players starting 2.44–10.06 m away who move ≥ 1.52 m toward / away from the basket before the rebound. Crash Index **CI = PI + NPC**; Retreat Index **RI = PO + NPR**. The reaction window (release to rebound) averaged 2.22 s (SD 0.65 s) on missed jumpers from ≥ 4.57 m.
- CTG Pro measures the same decision: the window from shot release until the ball first reaches the rim, `did_position_for_off_reb`, and `movement_direction` ∈ {towards_rim, stationary, getting_back, out_of_bounds, on_ground} [V21]; the next possession carries `num_crashers_on_team` and `num_watchers_on_team` [V18]. Maheswaran et al. 2014 define the crash phase as release until the ball is nearest the rim centre [P25].
- Signature: compute PI, PO, NPC, NPR, CI and RI at every missed FGA over t_rel → rebound; store the reaction time.

**Get back / sprint back**
- Definition: after a miss or turnover, players retreat instead of crashing; the first two steps matter most [C4]. Holtmann: perimeter players retreat "on the shot" [C24].
- Aliases: getting back, retreat, sprint back, floor balance, "back".
- Signature: per player, retreat onset = first time speed toward the own rim ≥ 2.0 m/s after t_rel (or after t0 for turnovers) [HEURISTIC]; reaction delay (s); mean speed over the first 10 m of retreat; peak speed as a share of the player's own peak; whether he was behind the ball at t_cross_half; CTG's `is_back_before_ball_crosses_scoring_zone` [V19].

**Safety (two meanings)**
- Defensive safety: "at least one guard, instead of rebounding, should stay back beyond the three-point arc"; if the safety drives, a second guard takes over [C4]. In rebound-tag roles the safety is the first player back, often the shooter, and denies the long pass [C5]. Izzo: send 4 to the glass, the PG gets back [M20][REPO].
- Offensive "safety" (FIBA terminology): "the offensive player at the top of the circle" [C1].
- Aliases: safety, back man, "one back", deep man (defensive); top man (offensive, FIBA sense).
- Keep two tags. Defensive safety signatures, stored as two named variants: `safety_repo` [REPO] = at t_rel + 1.0 s, players of the shooting team with r > 7 m moving away from the attacked rim at ≥ 2 m/s (`defense_full.md` F12 "One back (safety)"; same rule in §9.8); `safety_wide` [HEURISTIC] = at t_rel + 1.0 s, a player of the shooting team at r ≥ 6.75 m moving toward his own end at ≥ 2.0 m/s, or already at y ≥ 9.0 m. Store count (0, 1, 2) and identity for each.

**Protect the basket (first back)**
- Definition: the first player back runs to the rim, steps out one step, protects the basket and forces at least one pass [C4]; protecting the basket is generally the most important component, ideally by the taller defender [C3]. Holtmann's "Full Back" protects the paint [C24].
- Aliases: first back, Full Back, rim protector, deep man, "basket".
- Signature: t_protect = first time any defender has r ≤ 2.5 m of his own (attacked) rim after t0. Store t_protect − t0, who, whether t_protect < t_cross_half, and his r at t_cross_half (repo: ≤ 2.5 m [REPO]).

**Stop the ball**
- Definition: "the second player back should stop the ball, no matter where it is", even past half-court [C4]; stop it as soon as possible, or at least slow the handler, and stay in front [C3]. Holtmann's "Half Back" pressures the ball and keeps it on one side [C24]. In a 3v2 the top defender calls "ball, ball, ball!" [C4].
- Aliases: stop ball, ball stopper, pick up the ball, turn the ball. "Build a wall" was not found in any opened source (**unverified**).
- Signature: first defender within 2.0 m of the handler **and** between the handler and the rim (y_def < y_handler); stopped = handler speed < 3.0 m/s within 1.5 s of that contact [REPO]. Store t_stop − t0, pickup y (y > 12.73 m = picked up in the backcourt), the defender's order back, and whether the handler is turned to a side (\|x\| ≥ 3.0 m after the pickup) [HEURISTIC].

**Match up (matchup on the fly)**
- Definition: the remaining defenders turn and backpedal, match the nearest attackers, three-point shooters first [C3]; sprint back with vision and find the shooters; youth teams sprint to the paint first, then match [C4].
- Aliases: match, find your man, pick up, sprint to the paint then match.
- Signature [HEURISTIC]: t_matched = first time every attacker has a defender within 2.5 m (perimeter) or 1.5 m (r < 3 m) for ≥ 1.0 s. Store t_matched − t0 and unguarded-shooter time (seconds an attacker at r ≥ 6.75 m has no defender within 3.0 m before t_matched). MDET (§3.3) is a published summary measure (NBA 2011-12, SSAC conference paper; mean 2.76 m on stops vs 2.94 m on scores, 10,915 possessions; an association, not a validation) [P1]; it has not been validated for college.

**Cross-match (two senses)**
- Aliases: crossmatch, cross-matching, scramble switch, pick up the nearest, mismatch in transition, matchup on the fly (transition sense); planned cross-match (half-court sense). These aliases are common coaching usage; only "cross-matching" itself was seen in an opened source [C9].
- Transition sense: defenders pick up whoever they can and accept mismatches, then correct. Holtmann: "There are no player assignments in transition"; switch back only after the ball has been stopped [C24]. Hoopstudent describes switching areas, e.g. X4 and X3 swapping so the rim protector stays in the lane [C3]. Ralph Miller's "Automatic Pickup" is the opposite rule: each defender takes the player he was matched with before the change of possession, which causes mismatches, so everyone must guard every position [C43].
- Half-court sense: NBA writers also use "cross-matching" for a deliberate half-court assignment of a defender to an opponent of a different size [C9].
- Store `transition_crossmatch` and `planned_crossmatch` separately.
- Signature: at t_stop or t_defense_set, compute matchups by a transition-specific assignment (nearest attacker, Hungarian, stable ≥ 1.0 s). Franks et al. 2015 restricted their matchup model to moments with all players in the offensive half because defenders are not yet guarding anyone while the ball comes up court [P10], so half-court matchup models should not be used during transition. Cross-match = assignment ≠ the home assignment (modal over previous settled possessions) [REPO]; automatic pickup = assignment equals the pre-change pairing [C43]. Store count, height gap (cm, from the roster), time to switch back (repo: a SWITCH without a screen within 6 s of SET_DEF [REPO]) and whether the offense attacks the mismatch within 6 s.

**Jam / tag the rebounder**
- Aliases: jam, tag, bump, pressure the rebounder, slow the outlet.
- Definition: the nearest player pressures the defensive rebounder to slow the outlet [C4]. Tagging: bump your man from behind when the shot goes up, get to his high side, then release and sprint back the moment the opponent secures the rebound; post-rebound roles are ball stopper, middle stopper, sideline denier, weak-side denier, safety; crash only with a 50/50 chance at the ball [C5].
- Signature: a defender (former attacker) within 1.5 m of the rebounder for ≥ 0.5 s after t0 [REPO]; outlet delay is the outcome. Store which defender takes the middle (\|x\| < 1.83 m), the sidelines, and the deep spot.

**Cover two**
- In transition, one defender covers both the ball and the man sprinting to the rim with an agreed split [REPO]; the 3v2 stack is related [C4]. Signature: one defender within ±1 m of equidistant between the ball and the rim runner [REPO].

**Start types: transition after makes vs misses vs turnovers**
- Definition: the event that gives the new offense the ball. Full class list, sub-types and which analyst splits each one: §6.1. Efficiency by start type: §6.2–6.3.
- Aliases: off makes / off misses / off live-ball turnovers; live-ball vs dead-ball (turnovers); after a score / after a stop; "off the glass" (after a DREB); after made FT. Inpredictable's and pbpstats' own labels: "after made shot", "after DREB", "after TO"; `OffMadeFG`, `OffFTMake`, live-ball TO, dead ball [V35][V41]. CTG Pro: `fgm`, `ftm`, `steal`, `fg_dreb`, `ft_dreb` and others [V20].
- Signature: `start_type` = the event type of the play-by-play event that ends the previous possession (made FG, made final FT, DREB of a FG or FT miss, steal, dead-ball TO, other), with t0 taken from tracking per §1.4; store `live_ball` = true for steals and DREBs, false otherwise; and keep the provider-specific class (for example Inpredictable's grouping of dead-ball TOs with made shots [V35]) as separate columns.

Aliases for crash/retreat, safety, jam and cross-match above are common coaching usage gathered by the researchers; except where a source key is attached, they are vocabulary, not sourced claims.

### 2.4 State variables used by several definitions

- **CTG Pro** [V18]: `defenders_back` (defenders "reasonably ahead of the ball" when it enters the frontcourt during a possession touch; on a pass ahead into the scoring zone, defenders inside the zone count as back); `defenders_even`; `avg_defender_speed` at frontcourt entry; `is_defense_back` (5 back, or 4 back with low average speed); `num_players_below_ft_extended` for each team at chance start; `halfcourt_start_frame` (when the chance stops being transition).
- **Repo**: defense set = all 5 defenders behind the ball at r < 9 m for ≥ 1 s [REPO].
- **Metulini band** [P5][P6]: team centroid (mean x of the 5 players, along the court) within ±4 m of the half-court line = "transition" state.
- **Franks gate** [P10]: half-court = all 10 players in the offensive half.
- **Proposal** [HEURISTIC]: "even" = \|y_def − y_ball\| ≤ m, "back" = y_def < y_ball − m, with m = 1.5 m by default and a sensitivity run at 0.5 / 1.0 / 1.5 m (§3.4); "low average speed" < 2.0 m/s. CTG's thresholds are not published.

---

## 3. Phase model with timestamps

### 3.1 Offensive phases (defense to offense)

The phase names come from coaching sources; the start and end timestamps are tracking definitions built on CTG's anchors [V18] and are [HEURISTIC] unless a source is given. Phases overlap (early offense overlaps the secondary break), so each phase gets its own start and end time rather than a single exclusive label.

| Phase | Definition (sources) | Start timestamp | End timestamp | Published durations |
|---|---|---|---|---|
| **Possession gain** | Control established | t0 (§1.4) | — | NCAA backcourt count starts on control after a rebound [C16] |
| **Outlet** | First pass after a DREB [C1]; ball side [C15] | t0 | t_outlet (catch) | Repo: release ≤ 1.5 s after the DREB [REPO]. Numbered break: 0–1.5 s [REPO] |
| **Advance** | Ball moved up court by pass or dribble [C22][P2] | t_outlet (or t0 with no outlet) | t_cross_half; CTG also uses t_scoring_zone [V18] | Elite Italian: 73.9% by dribble [P2]. HoopTactics target: ball in the operating area within 2–4 s [C29] |
| **Primary break** | Attack against an outnumbered or few-player defense, generally within 2–3 s of possession [C2][C19] | First t with A_play > D_back and the ball at y ≤ 12.73 m, or a breakaway | Numbers advantage gone (A_play ≤ D_back for ≥ 0.5 s), or first shot | Fotinakis et al. 2002 (EuroBasket 1999), as cited by Jeličić [P27]: primary realised mainly at 3–9 s. **Conflict, kept unresolved:** the coaching window (2–3 s [C2][C19]) and the EuroBasket 1999 window (3–9 s, as cited by [P27]) disagree; store both as separate time flags, `prim_time_coaching_2_3s` (first shot or numbers advantage within t0 + 3.0 s) and `prim_time_fotinakis_3_9s` (3.0 ≤ t − t0 ≤ 9.0 s). 88.7% of elite fast breaks finished in the primary [P3]; 85.1% (elite) and 80.1% (sub-elite) of Italian fast breaks were primary [P2] |
| **Secondary break** | Follows when the defense stops the primary; more structure [C19][C20] | End of the primary | t_defense_set, or the start of a named half-court set | Fotinakis (as cited by [P27]): secondary at 6–12 s |
| **Early offense** | Punish the defense before it sets, first 8 s [C10] | t0 | t0 + 8.0 s (Purrà), or the first half-court set call; t0 + 15.0 s variant [P27] | Matulaitis & Bietkis code "transition" as started and finished within 5–8 s [P12] |
| **Flow** | Continue into the half-court offense without stopping [C27][C29] | End of the secondary | First half-court action | — |
| **Pull back / reset** | Abandon the break [C26] | Ball retreats after reaching the frontcourt (§2.2) | Set call / first half-court action | — |

Other published durations for the whole break:

- About 70% of fast breaks lasted 4–6 s; about three quarters of set offenses lasted 13–18 s (1999 Junior World Championship, 21 games) [P19].
- 9 of 10 fast breaks last under 6 s (Cárdenas et al. 2015, as cited by Bourgeais et al.) [P4].
- NBA 2011 playoffs: winners with a moderate lead (the source's "moderate advantage" = leading by 4–10 points) ran fast breaks of 3.96 ± 1.38 s versus 4.73 ± 1.61 s for losers (t(89) = 2.46, p = 0.02; 4,207 possessions, 25 games) [P24].
- A k-means split of NBA 2019-20 possession durations found a "fast" cluster of 0–8 s (mean 4.99 ± 2.65 s; 1,141 games) [P18].
- Beijing 2008 mean durations of men's 3.89 s and women's 4.42 s (p = .002) appeared only in search snippets (**unverified**); the abstract confirms 294 fast breaks from 30 games and sex differences in duration [P26].
- Inpredictable's NBA possession efficiency peaks in a "fast break zone" of 4–6 s, then drops sharply [V33].

### 3.2 Event timestamps to store for every possession

`t0`, `t_outlet`, `t_cross_half`, `t_scoring_zone` (y ≤ 10.29 m), `t_three_zone` (r ≤ 6.75 m), `t_paint`, `t_adv_start`, `t_adv_end`, `t_first_action` (first SCREEN, DHO or CUT), `t_first_shot`, `t_pull`, `t_flow_entry`, `t_defense_set` (both definitions), and the shot-clock reading at each. For comparison with CTG, also store its equivalents: `ball_seconds_to_scoring_zone`, `ball_seconds_to_three_point_zone`, `ball_seconds_to_paint`, `scoring_zone_shot_clock`, `ball_in_paint_shot_clock`, and the transition end per player (where a runner stops, sharply changes direction, or the offense first runs an action) [V18][V19].

Store **both** the elapsed time since t0 and the shot-clock reading. They differ after shot-clock resets (20 s after an offensive rebound that hits the ring [C16]), and several definitions use one or the other (§5).

### 3.3 Defensive phases (offense to defense)

| Phase | Definition (sources) | Start | End / timestamp | Measures |
|---|---|---|---|---|
| **Crash-or-retreat decision** | At the shot, each player crashes, holds or retreats [P1][V21] | t_rel | Rebound control (or ball at the rim for CTG's window [V21]) | PI, PO, NPC, NPR, CI, RI; reaction window mean 2.22 s (SD 0.65 s) [P1] |
| **Tag / jam** | Bump on the high side; jam the rebounder to delay the outlet [C5][C4] | t_rel | Release at the opponent's rebound | Jam duration; outlet delay |
| **Get back** | Sprint back; first two steps matter [C4] | t_rel (perimeter players retreat on the shot [C24]) or the change of possession | Each player's arrival behind the ball | Retreat onsets, speeds; `defenders_back` at frontcourt entry [V18] |
| **Protect the basket** | First back to the rim [C4][C3] | Change of possession | t_protect (first defender at r ≤ 2.5 m) | t_protect − t0 |
| **Stop the ball** | Second back picks up the ball [C4][C24] | Change of possession | t_stop | t_stop − t0, pickup y |
| **Match up** | Remaining defenders match, shooters first [C3][C4] | t_stop | t_matched | t_matched − t0; unguarded-shooter seconds |
| **Early threat neutralisation (MDET)** | In the first 5 s of the opponent's possession after a DREB, for each attacker who enters his threat range (75th percentile of his own shot distances, modes about 4.57 m and 7.01 m), take the distance to the nearest defender at that moment; MDET = the maximum [P1] | t0 (opponent DREB) | t0 + 5.0 s | MDET (m) |
| **Cross-match and switch back** | Accept mismatches, switch back after the ball is stopped [C24] | t_matched | t_switch_back (repo: SWITCH without a screen within 6 s of SET_DEF [REPO]) | Count, size gap, duration |
| **Defense set** | Half-court defense established | — | t_defense_set (both definitions, §1.4) | Time from t0 |

### 3.4 Numbers-state engine (per 0.1 s) [HEURISTIC, aligned with CTG and Conte]

Definitions in the attacked-rim frame:

All bins below are [HEURISTIC] until calibrated on MSU film. CTG publishes the concepts "back" and "even" but no numeric margins [V18]; the margins are ours. The bins are **mutually exclusive** and use the **same margin m** for attackers and defenders, so the engine does not lean toward reporting an advantage. Default m = 1.5 m.

- `D_back(t)` = defenders with y < y_ball − m (ahead of the ball, toward the attacked rim; CTG concept "back" [V18]).
- `D_even(t)` = defenders with \|y − y_ball\| ≤ m (CTG concept "even" [V18]).
- `D_behind(t)` = defenders with y > y_ball + m (beaten, behind the ball).
- `A_play(t)` = attackers (including the handler) with y ≤ y_ball + m (level with or ahead of the ball), and y ≤ 15.73 m (half-court + 3.0 m). The matching attacker bins `A_ahead` (y < y_ball − m), `A_even` (\|y − y_ball\| ≤ m) and `A_behind` (y > y_ball + m) are stored too, so a stricter count A_ahead + handler can be compared with D_back on equal terms.
- **Sensitivity version:** compute every count and every derived label (advantage, `tr_roy_williams_window`, the Conte and Trninić labels, the §8 passed-up flags) at m = 0.5, 1.0 and 1.5 m, and report per game how often the label flips between margins. Earlier drafts used y < y_ball − 0.5 m for D_back and \|y − y_ball\| ≤ 1.5 m for D_even, which overlapped (a defender at y_ball − 1.0 m counted as both); that version is withdrawn.
- Players out of frame: last known position plus velocity extrapolation of ≤ 1.0 s, flagged "estimated". This meets the requirement "tracked plus frame-exit players" in `docs/requirements.md` ("Transition clock").

Labels: numbers label "A_play v D_back" (e.g. "3v2"); advantage = A_play − D_back ≥ 1; Conte typology: primary (`prim_conte`) if the configuration is one of Conte's primary ones (1v0, 1v1, 2v1, 2v2, 3v1, 3v2, 3v3, 4v2), secondary (`sec_conte`) if it is 4v3, 4v4 or 5v4 [P2]; Trninić typology (`sec_trninic`, `tr_trninic_type`) from the defender count in the end zone (≤ 2 primary; 3–4 secondary, i.e. 3:3, 4:3, 5:3, 5:4) [P27]; `sec_heuristic` as in §2.1 [HEURISTIC]. Configurations outside a typology's list (e.g. 5v3 for Conte) are stored as "unlisted", not forced into a class. These are the same named fields as in §2.1.

Events: `t_adv_start` = first t with an advantage; `t_adv_end` = first t after which A_play ≤ D_back for ≥ 0.5 s; advantage duration (s).

Value of the break at each second (the requirement "Value of the break at each second"): fit P(score | numbers label, seconds since t0, ball y, start type) on MSU and opponent possessions. Hoop Vision's finding gives the expected shape: transition's value falls as the advantage shrinks [E1].

---

## 4. Player roles in the break

Two vocabularies exist and both are stored: Synergy's roles (leak-out man, ball-handler, left/right wing, trailer [V1]) and CTG Pro's `transition_role` values [V19]. The user's list (ball-handler, rim runner, wings, leak-out, trailer) is covered by both.

| Role | Definition (sources) | Published efficiency | Signature [HEURISTIC unless marked] |
|---|---|---|---|
| **Ball-handler** | The player bringing the ball up; a Synergy role [V1]. CTG `primary_initiator`: threw a long pass upcourt, or held the ball longest before the scoring zone [V19] | EuroLeague 2018-19: 1.05 PPP (EuroLeague analysis via Eurohoops; provider not named) [E4] | Player in possession (or the last passer, if the ball is in flight) at t_cross_half. Store advance mode, speed, dribble heading |
| **Rim runner** | Big who runs rim to rim [C1][C7][C23]. CTG splits `rim_runner_ahead` (ran down the middle, in front of or close to the ball, and got close to the basket), `rim_runner_trailer` (same, but crossed the scoring zone within about 1.5 s of the ball without being mostly ahead) and `rim_runner_other` [V19] | Not published | §2.2 rim-run signature; CTG split by arrival relative to the ball |
| **Wings (left / right)** | Lane runners down the sidelines toward the corners [C23][C15][C18]. Synergy "left/right wing" [V1]; CTG `left_wing_runner`, `right_wing_runner`, `middle_to_left_runner`, `middle_to_right_runner` [V19]. MSU 2025-26 pre-season: Fort on the right, Carr on the left [M3] | EuroLeague "wing runners": 1.22 PPP (EuroLeague analysis via Eurohoops; provider not named) [E4] | Non-ball attackers meeting the canonical `wing_lane` signature of §2.2 (sideline lane 5.3 ≤ \|x\| ≤ 7.62 m while y goes from 22 m to 6 m); corner arrival r 6.60–7.3 m, θ ≤ 12° or ≥ 168° within 5 s of t0 [REPO]; left/right by the sign of x |
| **Leak-out** | Releases early [C6][V1][C27] | EuroLeague "hit-ahead / leak-out": 1.47 PPP, the highest sub-type (EuroLeague analysis via Eurohoops; provider not named) [E4] | §2.2 leak-out signature |
| **Trailer (1st, 2nd)** | Behind the first wave, usually bigs [C1][C11]; CTG `trailer`: > about 1.5 s behind the ball, or set a drag [V19] | The only EuroLeague role not above the average half-court possession [E4] | §2.2 trailer signature |
| **Outlet passer / rebounder or stealer** | Who started the break (requirement example: Jeremy Fears Jr. securing the rebound) | — | DREB or steal player; outlet passer and receiver |

Store `role_by_player` per break, using both vocabularies, and each player's CTG-style fields: start area (below the free-throw line extended, between it and the arc extended, beyond the arc extended), seconds and speed to the scoring zone, rank across teammates, and "back before the ball crosses the scoring zone" for defenders [V19].

Role-level efficiency evidence is EuroLeague only [E4]. No public NCAA split by transition role was found.

---
## 5. Analyst definitions side by side (never merged)

The definitions below count different things: some count possessions, others plays, chances, shots or points; some classify by how the possession **started**, others by how it **ended**; some use a clock cutoff, others the state of the defense, others a position on the floor. One possession can be "transition" under one definition and half-court under another. Example: after a defensive rebound, the first shot at 7 s is Hoop-Math transition; an offensive rebound and putback at 12 s makes the possession end too late for FastScout; and Synergy starts a new possession at the offensive rebound and files the putback under its offensive-rebound play type (`OffRebound` in the NBA.com Synergy play-type codes [V45]), not under Transition and not as a generic half-court play [V4][V45], while CTG's play-by-play context keeps a putback inside transition [V17]. (The NBA.com display name for `OffRebound`, reported by the verifier as "Putbacks", was not re-opened here.) [V1][V5][V14][V17]

Clock conversions: on the NCAA 30 s clock, "first 10 s of the shot clock" means the shot clock reads ≥ 20 s. On a 24 s clock, "shot clock > 14" means elapsed < 10 s, and "17 s remaining" means 7 s elapsed [P14][P17].

### 5.1 Vendors, analysts and official box scores

| # | Owner | Unit counted | Start events | Time cutoff | State cutoff | Exclusions / notes | Known efficiency | Status |
|---|---|---|---|---|---|---|---|---|
| D1 | **Synergy Sports** (play type "Transition") | Play/possession; an offensive rebound starts a new Synergy possession [V4] | Any change of possession | **None**: "There's no time cutoff that makes a possession a halfcourt possession rather than a transition possession" [V1] | Possession-ending event (shot, turnover, shooting foul) before the defense is set, judged by a video logger [V1] | If the defense recovers and sets first, the play is re-logged (e.g. as Misc) [V1]. Roles: leak-out man, ball-handler, left/right wing, trailer [V1][V2]. `Transition` is one value of the Synergy API play-type enum [V3] | NCAA 1.040 PPP, NBA 1.103 (2017 article, season not stated) [V1]. NBA.com (Synergy) 2024-25: 1.127 PPP [calc, V25] (another researcher's calc: 1.128), team frequency 15.3–24.3%, mean 18.6%; 2025-26: 1.136 PPP, mean 18.5% [calc, V26]; 2023-24: 1.136 PPP, 17.17% [calc, V25 variant] | Definition via Nylon Calculus [V1]. Synergy's own glossary is login-gated (**unverified** wording) |
| D2 | **Hoop-Math** (Jeff Haley, college play-by-play) | **Initial** FGA of a possession (team pages); "% of total FGA" on leaderboards [V9] | DREB, steal, opponent score [V8][V10]. Dead-ball-TO starts are tabulated separately on team pages from 2011-12 [V7] but are **not** part of Hoop-Math transition [V6][V8]. VU Hoops (2014): Hoop-Math's splits "do[es] not include possessions starting off dead ball turnovers or recovered blocks" [V6] | **0–10 s** from the possession start: "initial shots in the first 10 seconds after a defensive rebound" [V5]; VU Hoops paraphrase: "only INITIAL shots within the first 10 seconds of the shot clock count" [V6] | None (time only) | Putbacks (shots ≤ 4 s after an offensive rebound) excluded [V6][V7]. Possessions whose first event is a defensive foul excluded [V7] | D-I 2013-14 eFG of initial shots 0–10 s: steal 62.93%, DREB 53.42%, opponent score 49.78%; after 10 s all about 47% [V6]. 2022-23 transition 54.6% vs 49.7% [V13] | Verified [V5][V6][V7][V8][V10]. Site offline since late 2024 [V12] |
| D2b | MGoBlog variant of Hoop-Math | Shots | DREB | ≤ 10 s | Ball live the whole time | Reports "% Opp" (share of a player's DREBs that lead to fast-break FGA or drawn shooting fouls) | — | **Unverified** (search snippet only) |
| D3 | **FastScout** (FastModel, now Hudl) | Possession | Any change of control: tip-off, made basket (except and-one), DREB, turnover, after a made final FT, after a missed final FT + DREB, out of bounds, violation, jump ball, period start, after a stoppage [V14] | Possession **ends in the first 10 s of the shot clock** [V14] | Not after a stoppage of play | Stoppages: substitution, foul, timeout, ejection, out of bounds, blood rule, equipment malfunction, injury, court clean-up. A possession starting after any stoppage can never be transition, even a quick inbound [V14][V14a] | None published | Verified [V14] (browser read) and [V14a] (static Wayback copy of the FastModel article, snapshot 12 Dec 2024, opened 2026-10-18, which confirms the full start, end and stoppage lists, including the and-one exception after a made basket and after a made final FT) |
| D4 | **Hudl InStat** ("Transitions (TS)") | FGA | Change from defense to offense | FGA "within 4-8 seconds" | "before the defense has had a chance to move into position" [V15] | From July 2024 a shot can carry Transition together with another play type such as Cut; reports and API keep the legacy one-type rule [V15]. The 2022 glossary says transition offense sits between the fast break and the set offense, and the "Cut" type also includes fast breaks [V16], so a pure fast-break layup may be filed as Cut | None published | Verified [V15][V16]. Whether shots under 4 s count is not stated (§12) |
| D5 | **Cleaning the Glass, play-by-play site** | Play context (per play); frequency per possession | Published splits: after steals, after live-ball DREBs [V17]. Two researchers read the page as not counting made baskets as a transition start [V17] | None | "as the teams are switching sides of the court and all 5 defenders are not back and set in a normal guarding position" [V17] | Transition starts at the possession start and ends only when the defense is set, so a putback after a transition miss counts as transition [V17]. Metrics: frequency, efficiency, STL Freq, Reb Freq, Pts+/Poss = (team pts per transition-start possession − an average team's pts per non-transition possession) × frequency [V17] | League averages paywalled (**unverified**) | Verified [V17] |
| D6 | **Cleaning the Glass Pro** (Hawk-Eye tracking, NBA) | Chance (a stretch without a stoppage) | **Opportunity** = "the first chance of a possession where it was not a sideline or baseline out of bounds, it was not after a timeout, and it was not an immediate turnover in the backcourt" [V18]. Start types: jump_ball, fgm, ftm, steal, fg_dreb, fg_dreb_block, fg_oreb, ft_dreb, ft_oreb, baseline/sideline/backcourt inbounds [V20] | None; records seconds to the scoring zone, three-point zone and paint [V18] | `is_transition` = the chance "ended with the initial transition advantage still going"; `is_defense_back` = 5 back, or 4 back with low average speed [V18] | `halfcourt_start_frame` marks the end of transition [V18]. `chance_context` values include transition, press, backcourt_turnover (explicitly not transition) and putback [V20] | Not public | Verified [V18][V19][V20][V21] |
| D7 | **NCAA box score** ("Fast Break Points") | Points | Any change of possession | None | "Points scored on a quick counterattack following a change of possession before the offense or defense is set" [V22] | Since 2020-21, counts when the fast-break FGA is made, and FTs from a shooting foul on it. Bonus FTs from a non-shooting foul to stop or during a break do **not** count [V22] | Box score only | Verified [V22] |
| D8 | **FIBA box score** ("Fast-break points") | Points | Turnover, DREB or made FG | **≤ 8 s** | "before their opponents have set their half-court defense" [V23] | Allowed after an offensive rebound if the defense is still not set. FTs from a foul immediately on the rebound do not count (Example 7); the FT from a foul on the outlet receiver to stop the break **does** count (Example 8) [V23]. So FIBA and the NCAA disagree on stop-the-break FTs | Box score only | Verified [V23] |
| D9 | **NBA.com** ("Fast Break Points") | Points | Not stated | Not stated | Not stated: "points scored by a player or team while on a fast break" [V24] | NBA.com notes an offensive rebound does not create another possession [V24]. The 6 s "official" claim is a journalist's [E11] | Box score | Verified [V24]; scorer's rule **unverified** |
| D10 | **NBA.com / SportVU-era definition** (as quoted by Inpredictable) | Possession | Change of possession | None | Possession-ending event before the defense sets | — | PPP after live-ball TOs 1.21 (2015-16, "this season"; implied league average, not labelled as such in the source) [V38] | Secondary source [V38] |
| D11 | **Second Spectrum** | — | — | — | — | No public transition definition found; NBA.com transition stats are "provided by Synergy" [V27] | — | **Unverified** (nothing published) |
| D12 | **KenPom** | Average possession length (APL), seconds, offense and defense | — | — | — | Not a transition stat. Covers the full possession including offensive rebounds; not adjusted for competition [V28]. The offense explains 86% of the variance in possession length (2010–2015) [V29] | Top 30 offenses 17.6 s vs bottom 30 18.4 s (national 18.1 s, 2012-13) [V30] | Verified [V28][V29][V30] |
| D13 | **Bart Torvik / toRvik** | Points | As NCAA | As NCAA | As NCAA | Only the official `fast_brk_pts`, `fast_brk_fgm`, `fast_brk_fga`, `fast_brk_fg_pct` in game box scores from 2019 [V31] | — | Verified [V31]; barttorvik.com team pages were not checked for a split (bot check) |
| D14 | **CBBD / ESPN play-by-play** | Play | Derive from the previous play | Any rule must be derived; `secondsRemaining` is an integer (1 s resolution) | — | No transition flag on plays; `fastBreakPoints` exists only in box-score schemas [V32] | — | Verified [V32] |
| D15 | **VU Hoops method** (ESPN play-by-play, 2014) | All actions | Made basket, missed basket, steal/recovered block, dead-ball TO | **≤ 10 s** from the change of possession | None | Noise from late-game intentional fouls and steals off inbounds or presses [V6] | Villanova 2013-14 ORtg (points per possession): transition 1.14 vs half-court 1.13 [V6] | Verified [V6] |
| D16 | **Stats by Will** | Shots | Not from a dead ball or out-of-bounds play | Any FGA in the first 10 s of the shot clock (some use 7–8 s) [V4] | — | — | — | Verified [V4] |
| D17 | **Inpredictable** (NBA play-by-play) | Possession by start type | After made shot (dead-ball TOs grouped here since 2015), after DREB, after live-ball TO [V35] | Not a label; efficiency peaks in a "fast break zone" of 4–6 s [V33] | — | Technical FTs excluded [V34] | §6.3 | Verified |
| D18 | **pbpstats** (NBA play-by-play) | Possession by start type | Live-ball TO, dead ball, made FG, missed FG by shot zone, FT make, FT miss [V41] | Not a label | — | An offensive rebound does not start a new possession [V41] | §6.3 | Verified (computed from the API) |
| D19 | **ShotTracker** (sensor tracking) | Possession | — | — | — | Definition not published | Transition share of possessions: NCAA men 17.7%, NCAA women 19.8%, high-school boys 22.5%, girls 24.9% [V42] | Shares verified [V42]; definition **unverified** |
| D20 | **NBA.com "first 6 s of the shot clock"** (analyst proxy) | Shots | — | Shot in the first 6 s of the shot clock | — | — | League eFG about 60% in the first 6 s vs about 50% after (2016-17) [E8]; 60.0% vs 53.1% (middle 12 s) vs 43.9% (last 6 s), 2019-20 (season inferred from article context; Second Spectrum tracking) [E9] | Verified [E8][E9] |
| D21 | **NBA.com shot dashboard bins** | FGA | — | Shot clock 24–22, 22–18 "Very Early", 18–15 "Early", 15–7, 7–4, 4–0 [V49] | — | — | §10.2 | Verified [V49] |
| D22 | **82games** (2003-04) | Possessions by time used | — | 0–10 s used = "quick" [E7] | — | Bundles transition with quick half-court shots | §10.2 | Verified [E7] |

### 5.2 Research definitions

| # | Paper | Type | Rule | Status |
|---|---|---|---|---|
| R1 | Conte et al. 2017, *Biology of Sport* (Italian leagues) | Time + configuration | Fast break = possession < 8 s; phases initiation, advance, completion; primary vs secondary by player configuration; equal numbers vs superiority [P2] | Verified [P2] |
| R2 | Matulaitis & Bietkis 2021, *IJERPH* (EuroLeague) | Time + state | Fast break: primary or secondary, finishing ≤ 5 s; transition: started and finished within 5–8 s, shot before the half-court defense is set [P12] | Verified [P12] |
| R3 | Cárdenas et al. 2015 / Bourgeais et al. 2024 | Time | 9 of 10 fast breaks < 6 s (Cárdenas et al. 2015 as cited by Bourgeais); 6 s window separates fast breaks (FIBA 24 s clock only) [P3][P4] | Verified [P4] (preprint, arXiv, 12 games, FIBA World Cup 2019); Cárdenas abstract only [P3] |
| R4 | Tavares & Gomes 2003 | Descriptive | About 70% of fast breaks last 4–6 s [P19] | Abstract [P19] |
| R5 | Skinner 2012, *PLoS ONE* | Time | Shots in the first 7 s of the shot clock flagged as fast break and shown separately [P13] | Verified [P13] |
| R6 | Goldman & Rao 2011 (Sloan) | Time | Possessions used within the first 7 s = fast breaks (removed); half-court offense modelled from 17 s remaining [P14] | Verified [P14] |
| R7 | Goldman & Rao 2013 (Sloan) | Time | Excludes "fast-breaks (shot clock > 14)" = elapsed < 10 s on a 24 s clock [P17] | Verified [P17] |
| R8 | Zhang et al. 2025, *PLoS ONE* | Data-driven | "Fast" possessions 0–8 s (k-means) [P18] | Verified [P18] |
| R9 | Metulini 2017; Facchinetti, Metulini & Zuccolotto 2019 (sensor tracking) | Spatial state | Transition = team centroid (mean x of the 5 tracked players) within ±4 m of the half-court line; a new action starts only when the centroid crosses the whole band. Frames with ≠ 5 players, free throws and dead time (all 5 below about 2.5–2.8 m/s for ≥ 2.5 s) removed [P5][P6] | Verified [P5][P6] |
| R10 | Franks et al. 2015, *Annals of Applied Statistics* | Spatial gate | Half-court = all players in the offensive half; matchup model used only on possessions ≥ 5 s in the half-court [P10] | Verified [P10] |
| R11 | Wiens et al. 2013 (SSAC) | Time window | Early-threat window = first 5 s after a DREB; effects vanish beyond about 15 s [P1] | Verified [P1] |
| R12 | Pastrana-Brincones et al. 2021, *Front. Sports Act. Living* (Spanish/Portuguese school) | Phase | Three attack forms: counterattack (fast break), transition ("second wave", ball never stopped), positional attack. Transitions about 7–12% of possessions (as cited) [V48] | Verified [V48] |
| R13 | Trninić typology, via Jeličić 2021 | Defender count | Primary: ≤ 2 defenders in the end zone; secondary: 3–4; early offense: 5v5 with a short positional phase [P27] | Verified [P27] |

### 5.3 Coaching and repo definitions

| # | Owner | Rule | Source |
|---|---|---|---|
| K1 | Coaching phase view | Primary ≈ first 2–3 s after possession [C2][C19]; early offense = first 8 s [C10]; secondary follows the stopped primary [C20] | [C2][C10][C19][C20] |
| K2 | Roy Williams (UNC) | ≤ 2 defenders back → score in ≤ 2 passes; more → secondary with ≥ 3 passes unless a layup [C15][C23] | [C15][C23] |
| K3 | Paul Westhead's "System" (LMU) | Shot < 7 s after a DREB; < 3 s after a make [C33] | [C33] |
| K4 | D'Antoni Suns "7 Seconds or Less" | "get a shot off in seven seconds or less" [C36] | [C36][C35] |
| K5 | HoopTactics | Early Push: ball in the operating area within 2–4 s, else Flow [C29] | [C29] |
| K6 | Scouting4U | Transition begins the moment a team gains the ball, before the defense sets; no time cutoff; second-chance possessions separate [V44] | [V44] |
| K7 | Repo `PHASE` (Aldemir's earlier state-based view) | Transition from possession start until 7 of 10 players are past half-court or 8 s elapse; early = 4–12 s; Synergy-style "defense set" = all 5 defenders behind the ball at r < 9 m for ≥ 1 s [REPO] | `offense_full.md` §0.2 |

### 5.4 Suggested storage: one field per definition, per possession and per chance

```
t0, start_type, after_stoppage, shot_clock_at_t0
tr_synergy_like          # terminal event before t_defense_set (no clock)
tr_ctg_pbp               # possession starts with a transition event; lasts until defense set; putbacks inside count
tr_ctg_pro_opportunity   # first chance; not after SLOB/BLOB/timeout/immediate backcourt TO
tr_ctg_pro_is_transition # chance ends with the initial advantage still going
tr_hoopmath_10s          # initial FGA <= 10.0 s after t0; start in {DREB, steal, opp score} [V8][V10]; putbacks excluded
tr_hoopmath_10s_plus_dbto # same, but start in {DREB, steal, opp score, dead-ball TO}; NOT Hoop-Math transition, for comparison with the separate dead-ball-TO row [V7]
tr_mgoblog_live_dreb     # (unverified variant) shot <= 10.0 s after DREB, no dead ball between
tr_fastscout_10s         # possession ENDS with shot clock >= 20 s (reading, not elapsed time), and not after a stoppage [V14][V14a];
                         #   after an OREB the NCAA clock resets to 20 s, so a post-OREB end can never qualify; store elapsed-time twin below
tr_fastscout_10s_elapsed # comparison only: possession ends <= 10.0 s after t0, not after a stoppage
tr_instat_strict_4_8s    # 4.0 <= t_FGA - t0 <= 8.0 s, defense not in position
tr_instat_0_8s           # t_FGA - t0 <= 8.0 s, defense not in position
                         #   neither is "the" InStat flag until Hudl confirms whether shots < 4 s count (§12 Q2) [V15]
tr_ncaa_fbp              # official box flag (CBBD fastBreakPoints, per game)
tr_fiba_fbp_8s           # points <= 8.0 s after t0 before defense set; stop-the-break FTs counted
tr_nba_6s_clock          # FGA with shot-clock reading >= 24.0 s on the NCAA 30 s clock (no post-OREB shot can qualify: reset is 20 s)
tr_nba_6s_elapsed        # FGA with t_FGA - t0 <= 6.0 s
tr_vuhoops_10s           # any action <= 10.0 s from the change of possession
tr_conte_8s, tr_matulaitis_5s, tr_matulaitis_5_8s, tr_bourgeais_6s, tr_skinner_7s, tr_goldman_rao_10s
tr_metulini_band_s       # seconds the team centroid spends with |y - 12.73| <= 4 m
tr_franks_halfcourt_t    # first time all 10 players are in the offensive half
tr_roy_williams_window   # D_back <= 2 at t_cross_half
tr_trninic_type          # primary | secondary | early, from defender count in the end zone
prim_conte, prim_conte_loose, prim_trninic, sec_conte, sec_trninic, sec_heuristic   # §2.1 / §3.4 named typology fields
prim_time_coaching_2_3s, prim_time_fotinakis_3_9s                                   # §3.1 conflicting primary windows
numbers_margin_m         # 0.5 | 1.0 | 1.5 m: every numbers-based field is stored at each margin (§3.4 sensitivity)
tr_repo_phase            # current repo PHASE label
phase_times              # §3.2 timestamps
numbers_state(t)         # A_play, A_ahead, A_even, A_behind, D_back, D_even, D_behind at 10 Hz (§3.4), per margin m
```

Keep both possession-level and chance-level versions, because KenPom and pbpstats keep offensive rebounds inside one possession while Synergy starts a new one [V28][V41][V4].

---

## 6. Start-type taxonomy, with points-per-possession evidence

### 6.1 Classes

| Class | Definition | Sub-types to keep | Who splits it |
|---|---|---|---|
| **DREB** (after a missed FG) | Defensive rebound of a missed field goal | By miss zone (rim, short mid-range, long mid-range, arc three, corner three) [V41]; blocked-shot rebound (`fg_dreb_block`) [V20]; long rebound (r ≥ 6.0 m from the shooter's rim) [HEURISTIC] | Hoop-Math, Inpredictable, pbpstats, CTG |
| **DREB after a missed FT** | Defensive rebound of a missed final free throw | `ft_dreb` [V20] | pbpstats ("FT miss"), CTG, FastScout |
| **Live-ball turnover** | Steal or loose-ball recovery; the ball stays live | Steal location y; stealer already ahead of the defense | Hoop-Math ("steal"), Inpredictable ("after TO", live only since 2015 [V35]), pbpstats, CTG |
| **Dead-ball turnover** | Violation, out of bounds, offensive foul; inbound follows | Inbound location (baseline, sideline, backcourt) [V20] | Hoop-Math (tabulated separately from 2011-12 [V7], outside its transition definition [V6][V8]), pbpstats; Inpredictable groups it with made shots [V35]; FastScout excludes it from transition (stoppage) [V14] |
| **Made FG** | Opponent field goal made; inbound from the end line | Inbound delay; inbounder; press present | Hoop-Math ("opponent score"), Inpredictable, pbpstats, CTG (`fgm`), FastScout (except and-one) |
| **Made FT** | Opponent's final free throw made | Same as made FG | pbpstats ("FT make"), CTG (`ftm`), FastScout. Whether Hoop-Math's "opponent score" includes made FTs is not stated (**unverified**) |
| **Offensive-rebound chance** | Not a new possession in KenPom or pbpstats; a new one in Synergy | Shot-clock reset to 20 s [C16] | CTG (`fg_oreb`, `ft_oreb`) |
| **Other** | Jump ball, period start, after timeout, inbounds after a stoppage | — | CTG, FastScout |

### 6.2 NCAA evidence

**Hoop-Math, initial shots, D-I 2013-14** (aggregate, as reported by VU Hoops [V6]):

| Start, window | % of initial FGA | % at rim | Rim FG% | % 3PA | 3P% | eFG% |
|---|---|---|---|---|---|---|
| Opponent score, 0–10 s | 5.70% | 36.37% | 60.41% | 41.37% | 31.84% | 49.78% |
| Rebound, 0–10 s | 12.78% | 45.11% | 60.80% | 35.17% | 35.36% | 53.42% |
| Steal, 0–10 s | 6.61% | 66.55% | 70.17% | 20.64% | 36.73% | 62.93% |
| Opponent score, 11–35 s | 39.37% | 28.98% | 55.61% | 36.27% | 34.68% | 47.42% |
| Rebound, 11–35 s | 21.70% | 29.93% | 55.67% | 35.37% | 34.27% | 47.17% |
| Steal, 11–35 s | 2.55% | 29.21% | 55.23% | 35.30% | 35.72% | 47.31% |

Aggregate transition shots that season: 21.43% of shots, 48.79% at the rim, rim FG% 64.11%, eFG 55.11%; half-court: 78.57%, 33.94% at the rim, 57.53%, 48.53% [V6].

**Hoop-Math database averages, 2011-12** (35 s clock) [V7]: eFG of initial shots 0–10 s after a DREB 53%, after a steal 62%, after an opponent score 49%, after a dead-ball TO 51%; at 11–35 s: 47%, 46%, 47%, 46%. Haley's own article gives 53% vs 47% after DREBs, transition rim FG about 64%, 63% of initial shots ≤ 10 s after steals at the rim and 22% threes [V5].

**Hoop-Math, D-I 2023-24 through 19 Mar 2024 (pre-tournament snapshot)** (30 s clock; unweighted league means of team values from the archived transition-defense leaderboard [V10], whose page reads "Last updated: Tue Mar 19 01:50:48 2024", so these are **not** full-season values) [calc, V10]. Team count: the page lists **362** teams; the means below were recomputed by the fixer on 2026-10-18 over all 362. The first draft used 359 teams, most likely the subset that could be name-matched to Torvik T-Rank [E31] for the correlations in §10.4 (n = 359 there; the draft did not record why 3 teams dropped, so this reason is the fixer's inference); the 359-team means differed by ≤ 0.1 percentage point (e.g. DREB 0–10 s 16.76% vs 16.78%).

| Start | 0–10 s share of initial FGA | 0–10 s eFG | 11–30 s share | 11–30 s eFG | Early premium |
|---|---|---|---|---|---|
| DREB | 16.78% | 50.85% | 19.17% | 47.88% | +3.0 |
| Opponent score | 5.08% | 57.65% | 40.40% | 48.16% | +9.5 |
| Steal | 4.29% | 62.31% | 2.35% | 48.26% | +14.1 |
| All transition | 26.15% of initial FGA (22.66% of all FGA) | 54.02% | — | non-transition 48.84% | +5.2 |

Push rates conditional on start type (2023-24 through 19 Mar 2024, pre-tournament snapshot, mean of team rates, 362 teams): 46.69% of post-DREB initial shots came within 10 s, but only 11.18% of post-make initial shots [calc, V10].

**Villanova 2013-14** (ESPN play-by-play, all actions ≤ 10 s, ORtg in points per possession) [V6]:

| Category | FGA | eFG% | 3P share | Rim share | ORtg |
|---|---|---|---|---|---|
| Transition overall | 457 | 59.19% | 43.76% | 42.23% | 1.14 |
| Half-court overall | 1381 | 51.81% | 44.32% | 29.25% | 1.13 |
| After makes | 67 | 64.18% | 65.67% | 23.88% | 1.22 |
| After misses | 181 | 58.29% | 46.41% | 38.67% | 1.05 |
| After steals / recovered blocks | 152 | 59.54% | 29.61% | 61.84% | 1.27 |
| After dead-ball TOs | 48 | 57.29% | 45.83% | 25.00% | 1.09 |

**Michigan State 2023-24** (Hoop-Math team page, offense; page "Last updated: Wed Apr 10 21:11:52 2024", i.e. final season) [V8]: rebound 0–10 s = 15.8% of initial attempts at 57.2% eFG; rebound 11–30 s 21.5% at 44.3%; opponent score 0–10 s 6.0% at 60.3%; opponent score 11–30 s 35.9% at 49.0%; steal 0–10 s 4.6% at 75.3%; steal 11–30 s 2.7% at 45.9%; all transition 26.5% of initial attempts at 61.1% eFG, 47.8% of shots at the rim (69.0% FG).

**Gap:** no D-I-wide **PPP** by start type (steal vs DREB vs make vs FT) was found in any opened source. It has to be computed, for example from CBBD play-by-play [V32].

### 6.3 NBA evidence (play-by-play)

| Season | After made shot | After DREB | After turnover | Source |
|---|---|---|---|---|
| 2011-12 → 2014-15 | 0.98–1.01 PPP, 17.9–18.5 s | 1.04–1.06, 12.5–12.8 s | 1.11–1.13, 12.2–12.5 s (live + dead) | Inpredictable [V34] |
| 2014-15 | 46.6% of possessions, 17.9 s, 1.00 | 36.1%, 12.5 s, 1.04 | 15.0%, 12.2 s, 1.12 | Inpredictable [V33] |
| 2015-16 | — | — | Live-ball TO possessions 9.7 s; PPP 1.21 "this season" (implied league average; not labelled as such in the source) | Inpredictable [V38] |
| 2019-20 | 1.06 / 1.07 | 1.10 / 1.125 (rim miss 1.15, mid-range 1.11, three 1.11) | Live 1.25 / 1.28; dead ≈ made | Inpredictable / pbpstats via NBA Underground [V39] |
| 2025-26 | 55%, 17.0 s, 1.10 (includes dead-ball TOs) | 34%, 11.1 s, 1.15 | Live only: 8%, 8.3 s, 1.31 | Inpredictable [V36] |

**pbpstats, NBA 2024-25** (computed from the API; an offensive rebound does not start a new possession) [V41]:

| Start type | Possessions | PPP | Seconds per possession |
|---|---|---|---|
| All | 243,787 | 1.148 | 14.61 |
| Live-ball turnover | 19,712 | **1.323** | 8.36 |
| Missed FG at the rim | 8,386 | 1.195 | 9.67 |
| Missed FG, all | 74,353 | 1.165 | 10.84 |
| Missed short mid-range | 14,962 | 1.166 | 10.63 |
| Missed long mid-range | 6,449 | 1.165 | 11.45 |
| Missed arc three | 28,997 | 1.149 | 11.47 |
| Missed corner three | 9,500 | 1.148 | 11.34 |
| Missed FT | 4,716 | 1.125 | 15.00 |
| Made FG | 87,437 | 1.119 | 17.77 |
| **Made FT** | 20,683 | **1.118** | 16.56 |
| Dead ball | 23,686 | 1.118 | 16.23 |

Live-ball turnovers were 57.4% of all turnovers in that season [V41].

Time to shot by start type, NBA 2025-26: all shots 11.6 s at 53.2% eFG; after a made shot 15.2 s (50.9%); after a DREB 9.7 s (54.1%); after an OREB 3.2 s (55.4%); after a TO 6.9 s (63.0%) [V37].

Other start-type evidence:

- A live-ball turnover start adds about +17 points per 100 possessions over the league-average offense; a DREB of a missed two is worth more than one of a missed three [V40].
- 2018-19 playoffs: Houston offensive rating 129 after Golden State live-ball TOs vs 109 after dead-ball TOs (points per 100 possessions; ≈ 1.29 vs 1.09 points per possession; baseline ORtg 113.8 on 579 possessions, which the source converts to 1.138); opponent possessions after Toronto live-ball TOs lasted 7.3 s vs 15.2 s after dead-ball TOs; points cluster in the first 2–5 s after a live-ball TO; an inbound after a dead ball typically takes 2–8 s [E14].
- Synergy's shot-quality model includes the start of the possession: live-ball-turnover starts yield better looks [E37] (no effect sizes published).

### 6.4 Start-event shares in fast-break research

| Study | DREB (Gerani); rebound, type not specified (Conte, Cárdenas)¹ | Steal / interception | Throw-in / other | Sample |
|---|---|---|---|---|
| Conte et al. 2017 (Italy) | 39.6% elite, 43.8% sub-elite (source label "Rebound") | 55.4% elite, 53.4% sub-elite | 5.0% throw-in (elite) | 398 fast breaks, 30 games [P2] |
| Cárdenas et al. 2015 (Spain, elite) | 46.7% ("started after a rebound") | 27.8% interception, 18.6% steal | — | Abstract [P3] |
| Gerani et al. 2004 (EuroBasket 2001, Greek A1) | 56% ("defensive rebound") | 41% | — | 50 games [P20] |

¹ Conte's table and the Cárdenas abstract say "Rebound", not "defensive rebound", and do not state the rebound type, so only the Gerani value is a DREB share as stated.

---

## 7. Pushing after made baskets and made free throws

### 7.1 How each definition treats pushes after a score

| Definition | After a made FG | After a made FT |
|---|---|---|
| Synergy (D1) | Can be transition if the defense is not set [V1] | Same |
| Hoop-Math (D2) | "Opponent score" start, initial shot ≤ 10 s [V5][V6][V8] | Not stated whether included (**unverified**) |
| FastScout (D3) | Counts: a made basket (except an and-one) starts a possession; transition if it ends ≤ 10 s into the shot clock [V14][V14a] | Counts: a made final FT (except an and-one FT) starts a possession [V14][V14a] |
| CTG play-by-play (D5) | Not a published transition split [V17] | Not split |
| CTG Pro (D6) | `fgm` start type; `sec_between_previous_chance_end_and_inbounds` [V18][V20] | `ftm` start type [V20] |
| FIBA box (D8) | A made FG is a listed change of possession [V23] | Not listed |
| Inpredictable (D17) | "After made shot" (with dead-ball TOs) [V35] | Not split |
| pbpstats (D18) | `OffMadeFG` [V41] | `OffFTMake` [V41] |

### 7.2 Evidence

- **NBA baseline.** Possessions after a make are the slowest and least efficient type: 2025-26, 17.0 s and 1.10 PPP vs 1.15 after a DREB and 1.31 after a live-ball TO [V36]. After made shots the inbound gives the defense time to set, "preventing fast break opportunities" [V33].
- **NBA after made free throws.** pbpstats 2024-25: 1.118 PPP at 16.56 s per possession after a made FT, almost identical to after a made FG (1.119, 17.77 s) and after a dead ball (1.118, 16.23 s) [V41]. This is a start-type split, not a measure of pushing.
- **NCAA premium for pushing after a make (Hoop-Math).** 2023-24 through 19 Mar 2024 (pre-tournament snapshot, 362 teams): initial shots ≤ 10 s after an opponent score had eFG 57.65% vs 48.16% at 11–30 s (+9.5 points), but only 11.18% of post-make initial shots came that early [calc, V10]. 2013-14: 49.78% vs 47.42% [V6]. 2011-12: 49% vs 47% [V7]. Selection effects (teams push after a make mainly when numbers favour them) make these upper bounds on the value of always pushing [E1].
- **Villanova 2013-14**: transition after makes 1.22 ORtg on 67 FGA, with 65.67% threes [V6].
- **Michigan State 2023-24**: 6.0% of initial attempts came ≤ 10 s after an opponent score, at 60.3% eFG [V8, final, updated 10 Apr 2024]; league means 5.08% and 57.65% are from the 19 Mar 2024 snapshot [calc, V10], so this comparison mixes a final team page with a pre-tournament league snapshot. Opponents pushed after MSU scores on only 8.3% of their post-score initial shots, 4.0 / (4.0 + 44.2) [V8] (8.1% in the 19 Mar snapshot, 3.9 / (3.9 + 44.2) [V10]).
- **Gap.** No public study isolates **pushing** after made free throws, at any level, and no college start-type split for made FTs was found. Our tracking can fill this.

### 7.3 Coaching rules for pushing after a score

- Westhead's System: shot < 3 s after a make, immediate inbound [C33].
- Roy Williams: get the ball out of the net as quickly as possible; ball to the PG; wings release as soon as the ball is scored; one big sprints to the front of the rim on makes and misses [C23].
- Carolina break: a designated post inbounds; the other post rim-runs for the long pass [C30]. Coach's Clipboard secondary after a make: O3 takes the ball out of the net, inbounds to O1 and trails; inbound immediately [C31].
- Pacers 2024-25: push off made field goals and made free throws [C17]. Breakthrough Basketball's Pacers blueprint: the player nearest the ball inbounds at once to a moving handler; target one layup off made baskets per quarter [E34] (its PPP figures are unsourced and not used).
- Hoiberg (Nebraska, Jan 2026): "I thought we got the ball up the floor even after a couple of Oregon makes" [M32]. Laso (Real Madrid): create transition after being scored on and after DREBs [C39].
- MSU: the UM Hoops writer's own narration says Izzo's teams push the ball at any time, "off of makes or misses" [M13]; Michigan assistant Kyle Church, scouting MSU: "the wings are sprinting down the wings" and "the first big down puts pressure on the rim" [M13]; "When the ball goes in, it seems like the ball's already getting taken out of bounds by their bigs" (Danny Wolf; the 247Sports page is undated and previews a Friday-night Michigan–MSU game, so "Feb 2025" is inferred (page undated)) [M34]; MSU scored quickly after Oakland made shots (Dec 2018) [M7]; MSU pushes after every opponent possession and runs the set if there is no early score (2016) [M8]. In 2006-07 Izzo did the opposite: run off misses, less off makes, then walk, then "crawl after misses" and no push after makes, because of a thin backcourt [M2].
- A preview saying MSU's PG sprints up the floor even after made baskets was seen only in a search summary (**unverified**). The NCAA rule letting the inbounder run the baseline after a made basket was also seen only in a search summary and must be confirmed in the rulebook (**unverified**).

### 7.4 Signatures [HEURISTIC]

For every made-FG and made-FT start:

- `t_net` = ball passes through the net (or the final FT drops); `t_inbound_release`; `t_inbound_catch` (= t0 here).
- `inbound_delay` = t_inbound_release − t_net (repo quick inbound: ≤ 2.0 s [REPO]; CTG equivalent `sec_between_previous_chance_end_and_inbounds` [V18]).
- Inbounder identity and height (repo: tallest-player heuristic [REPO]); first-pass type and length.
- `t_cross_half − t_inbound_catch`; handler speed in the backcourt; `ball_speed_to_scoring_zone`.
- Numbers state at t_cross_half (§3.4).
- `press_present` = ≥ 2 defenders at y > 12.73 m (the offense's backcourt) at the inbound [REPO-derived, treat as HEURISTIC]; trap = 2 defenders within 1.5 m of the handler.
- `push_after_make` [HEURISTIC]: inbound_delay ≤ 2.0 s **and** t_cross_half − t_net ≤ 5.0 s. Report the rate split by made FG vs made FT, and the share meeting Westhead's < 3 s shot target [C33].

---

## 8. Passed-up breaks: opportunities not taken

### 8.1 Why this needs its own measure

- **Selection bias.** Synergy transition counts only plays that end in a shot, turnover or foul before the defense sets; breaks that are pulled back become half-court plays, which biases transition PPP upward [E1]. Teams that rarely run post high transition PPP (Bo Ryan's last six Wisconsin seasons: 4.7 transition plays per game at 1.17 PPP) [E1].
- **Diminishing returns.** Transition's edge shrinks as the offense's advantage shrinks [E1]. So the marginal break is worth less than the average break, and a passed-up break is not automatically an error.
- **The cleanest public template** is CTG Pro's split between **opportunity** (every eligible first chance) and **outcome** (`is_transition`, the advantage survived to the end) [V18]. An opportunity that ends without `is_transition` is a candidate passed-up break.
- **Base rates.** D-I 2023-24 through 19 Mar 2024 (pre-tournament snapshot, 362 teams): 46.69% of post-DREB initial shots came within 10 s, but only 11.18% of post-make ones [calc, V10]. MSU's opponents pushed on only 39.0% of their post-DREB initial shots in the 19 Mar snapshot, 14.2 / (14.2 + 22.2), the 6th lowest of 362 teams [calc, V10]; on the final team page the rate is 39.2%, 14.1 / (14.1 + 21.9) [calc, V8] (no league ranking exists for the final values).

### 8.2 Opportunity rules (store each one separately)

| Flag | Rule | Source |
|---|---|---|
| `opp_ctg_eligible` | First chance; not after a sideline or baseline out of bounds; not after a timeout; not an immediate backcourt turnover | [V18] |
| `opp_numbers_t1` | At t0 + 1.0 s (or the outlet catch), A_potential − D_back ≥ 1, where A_potential = attackers who could reach y ≤ 12.73 m before the deepest defender, using current velocity and each player's own peak speed | [HEURISTIC] |
| `opp_roy_williams` | D_back ≤ 2 when the ball crosses half-court | [C15][C23] |
| `opp_numbers_goal` | Any second ≤ 6 s with a 2v1, 3v1, 3v2 or 3v3 situation (HoopTactics goals: 2v1 → layup; 3v1 → make it a 2v1; 3v2 → open jumper plus putback; 3v3 → make it a 3v2) | [C29] |
| `opp_live_start` | Start type is a live-ball TO or a DREB (highest-value starts, §6) | [V41][V36] |

### 8.3 Passed-up conditions (store which one fired)

Given any opportunity flag, a break is **passed up** if any of these held [HEURISTIC]:

1. **Slow crossing**: the ball crossed y = 12.73 m after t0 + 6.0 s.
2. **Slow backcourt**: handler speed stayed < 3.0 m/s for ≥ 2.0 s in the backcourt.
3. **Held ball**: ball speed < 1.0 m/s for ≥ 1.0 s before t_cross_half.
4. **Pull-back with an advantage**: `pulled_back` (§2.2) while A_play > D_back.
5. **Ignored runner**: an attacker was ahead of all defenders with no defender within 3.0 m, and no forward pass was made to him within 1.0 s.
6. **Reset above the arc** [HEURISTIC; no source key, the earlier label "systems-research rule" matched no source and is withdrawn]: the handler reset (pull-back signature, §2.2) at r ≥ 7.5 m while all 5 defenders had y < y_handler.
7. **Stalled push** [HEURISTIC]: t_cross_half − t0 ≤ 4.0 s (the §2.2 push threshold), then `pulled_back` = true (§2.2 signature), with no FGA, shooting foul or paint touch between t_cross_half and t_pull.

### 8.4 Separate "declined" from "denied" and from context

| Category | Meaning | Signature / source |
|---|---|---|
| **Declined** | The offense had the advantage and chose not to use it | Conditions 1–7 with no defensive cause below |
| **Denied** | The defense took the break away | Outlet jammed (a defender within 1.5 m of the rebounder ≥ 0.5 s [REPO]); press present at the inbound; early wing denial (MSU's 2021 exhibition vs a pressing, denying GVSU produced only 6 first-half fast-break points [M1]) |
| **Failed** | The offense pushed and lost the ball | Turnover before t_defense_set |
| Context codes (attach, do not judge) | Personnel, depth, fatigue, fouls (MSU slowed after halftime in Feb 2015 for foul trouble [M9]; 2006-07 thin backcourt [M2]; a coach may call off the push for fatigue or personnel [C29]); score and clock state; on-court PG ("as fast as our point guard wants to play" [M27]); opponent press or crash (Illinois forces opponents to crash rather than run [M24]) | Game state, lineup, minutes, fouls |

Decision rules used by coaches are kept as separate per-possession columns (P1–P13 in §9.5), so a pull-back can be checked against the rule the team claims to follow, not against one universal "should have pushed" label.

### 8.5 Validation plan

- Hand-label about 30 breaks per definition on MSU film (pushed, declined, denied). One soccer study reached AUC 0.912 with 27 labelled counter-attacks (tested on the other half, 33 counters) [P9]; whether that transfers to basketball broadcast tracking is untested, so treat 30 labels per definition as a pilot size and grow it until the confidence interval of the agreement statistic (§11.3) is acceptable.
- Report `passed_up` counts per game with the value at stake: the fitted break value (§3.4) at the moment the opportunity began.

---
## 9. Coaching systems and defensive transition rules

Thresholds in the "signature" columns are [HEURISTIC] unless a source is named. Where a source gives no number, none is invented.

### 9.1 Michigan State under Tom Izzo: philosophy

- Motto "Defend, Rebound and Run", which NBC traces to Izzo's first seasons [M6].
- "Go hard, go fast but be under control" (Nov 2021) [M1].
- "Our fastbreak is where we're at our best" (Jan 2024, 92–61 vs Penn State, 20 fast-break points, 24 points off turnovers) [M12].
- "Our defense gets our running game going" (Dec 2023; 41 fast-break points in two games; 21 forced turnovers produced 22 points vs Baylor) [M11].
- "the best fast breaking team I've seen here since I've started" (Mar 2008, 103–74 vs Indiana, 22 fast-break points) [M10].
- "We can play fast at times, when we do we're a better team"; on Nairn, "Speed kills" (Feb 2015) [M9].
- Fears "is starting to really push the ball" (Mar 2025) [M6].
- "Fast break wins" as an Izzo phrase was **not found** in any opened source.

### 9.2 How much MSU ran, by season

| Season | Run level | Evidence | Source |
|---|---|---|---|
| 2006-07 | Pulled back on purpose | Run off misses, less off makes; then walk after both; by mid-December "crawl after misses" and no push after makes. Thin backcourt, injuries, fatigue. 13–2 non-conference, 67.7 ppg. Izzo then returned to running: "That is the way I'm gonna coach from now on" | [M2] |
| 2007-08 | High | Best fast-breaking team of his tenure (quote above) | [M10] |
| 2014-15 | Mixed | Nairn sparked the first-half break vs Ohio State; MSU slowed after halftime for foul trouble, which Izzo called "the best thing to do" | [M9] |
| 2015-16 | High | Pushes after every opponent possession (miss, make, turnover); set offense if no early score | [M8] |
| 2018-19 | Very high | 47 fast-break points vs Oakland; quick scores after Oakland makes; "They are the fastest team that I've played against" (Kampe). 15.2 fast-break points per game | [M7][M1] |
| 2019-20 → 2020-21 | Declining | 13.5 then 11.1 fast-break points per game (9.5 in conference). "Last year, we walked the ball up the court" | [M1] |
| 2021-22 | Revamped | 38 fast-break points vs Ferris State and 22 vs GVSU in exhibitions; "I want to run this year"; diagonal dribbling preferred | [M1] |
| 2023-24 | High, more full-court pressure | Quotes above. More baseline-to-baseline pressure than in recent seasons (**unverified**, search summary only) | [M11][M12] |
| 2024-25 | High | Pushes "off of makes or misses" (UM Hoops writer's narration); Church: "They just run so fast, all five of them", "the wings are sprinting down the wings", "the first big down puts pressure on the rim"; "as disciplined as any team I've ever seen" at getting off the floor; led the Big Ten in fast-break points [M13]. 16.73 fast-break points per game, No. 4 nationally (Mar 8 2025) [M35]. 16-1 when the game exceeded 68 possessions, 5-4 otherwise (date Feb 2025 inferred; page undated; descriptive, pace is endogenous) [M34] | [M13][M35][M34] |
| 2025-26 | Selective but lethal | 16.4 fast-break points per game, 11th nationally, 1st in the Big Ten; the same releases also print 16.2 / 12th [M14][M36]. Adjusted tempo slow: T-Rank 66.2 possessions per game, 247th [M15]; KenPom 266th (Feb 26 2026) [M16]. OR% 37.8 (10th); opponent OR% 22.4 (1st) [M15]. Transition FG% 68.9%, "100th percentile" (CBB Analytics via Spartan Avenue, Mar 2026) [M4]. 31–0 fast-break points vs Maryland, Jan 24 2026 [M5]. Synergy through Jan 5 2026: Michigan 25.7 transition points per game, 7.8 more than "No. 2 Michigan State", so MSU ≈ 17.9 (derived) [M23]. Synergy, first 3 games: nearly 20% of points in transition at 1.149 PPP (single-researcher read; the on3 page returned HTTP 403 to WebFetch and curl on re-check, 2026-10-18; re-open in a browser and save a copy) [M33] | [M4][M5][M14][M15][M16][M23][M33][M36] |

**Takeaway for measurement.** MSU is not a high-tempo team by possession count, yet it leads the Big Ten in fast-break points while crashing the glass hard. Pace, transition share and transition yield are separate quantities; store each one separately.

### 9.3 The MSU break: rules, roles and drills

| Element | Rule (source) | Signature [HEURISTIC] |
|---|---|---|
| Push trigger | Push after makes, misses and turnovers; run the set if there is no early score [M8][M13][M7] | Share of made-FG starts with the ball across y = 12.73 m within 5 s of the inbound, vs DREB starts |
| Outlet | Progressive drill: the rebounder outlets (make or miss) to a teammate coming from the sideline [C28]. 2024 practice on long outlets from guards to bigs running the middle (Detroit Free Press, **unverified**) | Receiver at \|x\| ≥ 5 m within 1.5 s of the DREB [HEURISTIC]; long outlet = `long_outlet_len15` (first pass ≥ 15 m) [HEURISTIC], stored next to `long_outlet_zone` (§2.2) |
| Dribble path | Diagonal preferred; straight-line dribbling blamed for turnovers [M1] | Dribble heading 20–45° off the long axis over ≥ 10 m [REPO] |
| Wings | Dedicated lane runners, wide [M1]; Church: "the wings are sprinting down the wings" [M13]; 2025-26: Fort right, Carr left (pre-season) [M3] | Canonical: `wing_lane` (§2.2). Named variant `msu_wing_lane_v2` [HEURISTIC]: wing \|x\| ≥ 6 m while y drops from 12 m to 3 m. Corner arrival r 6.60–7.3 m, θ ≤ 12° or ≥ 168° [REPO] |
| First big | Church: "the first big down puts pressure on the rim" [M13] | `rim_run_repo` (§2.2): first big at r < 2.5 m before the ball reaches y < 7 m [REPO]; compare with `rim_run_path` (§2.2) [HEURISTIC] |
| Trailer | Shooting 4 or 5 trails for a pitch-back three; the guard must pass before the timeline or the team goes to the secondary ("Coach Izzo early transition look", FastModel 2020) [M17] | Pitch-back at r 6.75–8.5 m, θ 70–110°, ≤ 8 s; `passed_before_timeline` |
| Break concept (2010 clinic) | 3- and 5-man break: stay wide, attack the middle with the dribble, look for post touches, the wing screens away on the opposite side, then flow into the flex continuity [M18] | Middle-third drive (\|x\| < 2.5 m) in the first 8 s; weak-side screen-away ≤ 8 s; flex-style baseline cross screen ≤ 15 s |
| Secondary | DHO plus weak-side down screen [REPO] | `offense_full.md` F2 |
| Drills | Progressive transition drill 2v1 → 3v2 → 4v3 → 5v4 → 5v5, 15–20 min, scored [C28][M19]; War (5v5 rebounding, one ball) into the break [M20][M21]; Dummy War into Break; 5-on-0 Break; War into Live Break [M22] | Practice video: labelled clips of numbers situations |
| 2v1 / 3v2 rules | 2v1: attack the rim, in-and-out dribble, pass second, no jumpers. 3v2: top handler does not pass the FT line [C28] | 3v2: handler y > 4.19 m at the pass |

No primary Izzo clinic handout with lane numbers was found. MSU break rules come from the State News, a FastModel diagram, coaching-site drill write-ups, a 2010 DVD description and opponent scouting; treat lane assignments as observed tendencies, not official rules.

### 9.4 MSU transition defense and the glass

- Send 4 to the offensive glass; the PG gets back. Rebounding is "Hit, Find and Fetch": the low man wins the first contact, two hands, catch above the head (John Zall's MSU defensive playbook) [M20].
- War: 5v5 one-ball drill built on hit-find-fetch rather than the traditional box-out; MSU's total rebounding % ranks ranged from 1st (2008-09, 2009-10) to 49th (2010-11) [M21].
- Drill rules: 1v2, stay "as low as the lowest offensive player" and concede the jumper; 3v2, stack top and low, the low defender takes the first pass and the top defender drops low; 4v3 and 5v4, stop the layup, communicate, box out [C28].
- 2025-26 outcome: MSU crashes (OR% 37.8, 10th) and allows the fewest offensive rebounds in the country (opponent OR% 22.4, 1st) [M15].
- 2023-24 (Hoop-Math): opponents took 21.3% of initial FGA in transition at 49.0% eFG [V8, final] (21.2% in the 19 Mar snapshot [V10]); league means 26.15% and 54.02% are from the 19 Mar 2024 pre-tournament snapshot [calc, V10]. Opponents pushed on 39.2% of post-DREB initial shots on the final page [calc, V8] and 39.0% in the snapshot, 6th lowest of 362 [calc, V10].
- A Spartan Avenue writer's view before UConn (Mar 2026): opponents would need to send at least four players back immediately to control MSU's pace (opinion) [M4].

### 9.5 How teams decide to push or pull back (decision rules, one column each)

| # | Rule | Who / source | Measurable form |
|---|---|---|---|
| P1 | Defender count: ≤ 2 back → score in ≤ 2 passes; otherwise secondary | Roy Williams [C15][C23]; Trninić primary/secondary split [P27] | D_back at t_cross_half; passes to the shot |
| P2 | Numbers goals: 2v1 → layup; 3v1 → make a 2v1; 3v2 → open jumper plus putback; 3v3 → make a 3v2; on a breakaway, the trailer and safety stay at or behind half | HoopTactics [C29] | A_play − D_back each second |
| P3 | Time to the operating area: 2–4 s, else flow | HoopTactics [C29] | t(ball at y ≤ 8 m) − t0 |
| P4 | Pass before the timeline, or secondary | MSU [M17] | `passed_before_timeline` |
| P5 | 3v2 handler stop line: the top handler does not pass the FT line or elbow | MSU drill [C28]; Carolina [C30] | Handler y > 4.19 m at decision time |
| P6 | Don't force; flow ("Be quick, but never hurry"; "under control") | [C30][M1] | Transition turnovers and contested early shots vs flow entries |
| P7 | Start-type selectivity: push only after steals, only after scores, or only at certain times | Coach's Clipboard [C30]; Westhead runs on everything [C33] | Push rate by start type |
| P8 | Personnel, depth, fatigue, fouls | MSU 2006-07 and 2015 [M2][M9]; HoopTactics [C29] | Push rate vs lineup, minutes, fouls |
| P9 | The point guard sets the pace | McCollum, Iowa 2025-26 [M27] | Push rate by on-court PG |
| P10 | "Smart pace": get into actions early, don't force early shots; "rather not shoot early … if we're not completely open" | Hoiberg [M32]; McCaffery [M25] | Early-clock shot rate vs nearest-defender distance on those shots |
| P11 | Diminishing returns: transition is worth most when the starting advantage is large; log stalled pushes too | Hoop Vision [E1] | PPP by numbers at t_cross_half |
| P12 | Opponent pressure, press, glass | GVSU press slowed MSU [M1]; Illinois forces opponents to crash [M24] | Push rate vs opponent press rate and crash count |
| P13 | Pass count: ≤ 2 passes in 96.4% of elite fast breaks; 88.7% finished in the primary | Cárdenas et al. 2015 [P3] | Passes per fast break |

### 9.6 Big Ten programs

| Program (coach) | Offensive transition | Defensive transition / glass | Key numbers | Source |
|---|---|---|---|---|
| **Michigan State (Izzo)** | §9.1–9.3 | Send 4, PG back | §9.2 | [M13][M15][M14] |
| **Michigan (Dusty May)** | "Free-flowing", "more like jazz"; players expected not to walk the ball up; few set plays | 2024-25: 4th-worst Big Ten transition defense (Synergy) [M13] | 2025-26: 14.4 s average offensive possession (5th in D-I); 75.3 possessions per game (4th); 25.7 transition points per game (Synergy), 1st in the Big Ten | [M23][M13] |
| **Illinois (Underwood)** | Few transition points by choice: 6.14 fast-break points per game (353rd) | "Send the house" to the glass on nearly every shot; on a three-point attempt the shooter is first back and the other 4 crash [C4][M24] | 2025-26: allowed 7.5 transition points per game in 8 high-major games (about 329th of 361); OR% 39.9 (11th) | [M24][C4] |
| **Iowa (McCaffery to 2025; McCollum from 2025-26)** | McCaffery: "I want to continue to run", but "rather not shoot early … if we're not completely open" (2018) [M25]. 2023-24: 14.85 fast-break points per game (1st in the Big Ten, 12th nationally); 74.3 possessions per 40 min [M26]; the only Big Ten team over 20 transition points per game in Synergy history [M23]. McCollum: "we play as fast as our point guard wants to play" [M27] | — | 2025-26 Iowa 11.6 transition possessions per 100 at 1.56 PPP (**unverified**: search summary only) | [M25][M26][M23][M27] |
| **Purdue (Painter)** | Slow, half-court; ball screens for Braden Smith. "You can't turn the ball over, take bad shots and let them play in transition" [M28] | Transition defense through ball security: 2025-26 turnover rate 11.8% in Big Ten play (best) [M29] | Adjusted tempo 223rd or lower every year since 2018 (as of Nov 2021) [M30]; KenPom 295th (Feb 2026) [M16] | [M28][M29][M30][M16] |
| **Indiana (DeVries, 2025-)** | Pre-season talk of pace; in practice half-court and three-heavy | — | 2025-26: 7.25 fast-break points per game (324th); KenPom tempo 249th of 365 | [M31] |
| **Nebraska (Hoiberg)** | "Smart pace"; pushes, including after some opponent makes; drag-screen break (§9.7) | — | Jan 2026: KenPom tempo 184th; fast-break points 10–0 vs Oregon | [M32][C25] |
| **Wisconsin (Gard; Bo Ryan historically)** | Bo Ryan's last six seasons: 4.7 transition plays per game, the fewest of any coach, at 1.17 PPP | Gard: getting the defense set first (**unverified**, page body did not load) | — | [E1] |
| UCLA, Oregon, USC, Ohio State, Maryland, Rutgers, Minnesota, Northwestern, Penn State, Washington | Not researched to source standard (gap) | — | — | — |

Pattern worth testing on MSU's opponents: Illinois trades transition offense for offensive rebounds and still suppresses opponents' breaks; MSU crashes 4 and also runs; Purdue protects through ball security. Log each opponent's strategy in the per-game report (§11).

### 9.7 Named transition systems (offense)

| System | Lanes, triggers, time targets (source) | Signature |
|---|---|---|
| **Numbered break** (Westhead lineage, per HoopStudent) | After a make, 5 inbounds; after a DREB, 5 outlets to 1. 1 breaks past the backcourt three-point line ball side and takes up to 3 dribbles; 2 and 3 sprint the sidelines to the corners (3 may cut to the post); 4 runs parallel to 1 in the opposite slot or rim-runs; 5 trails to the ball-side post or perimeter. Options: 2 three, 3 corner three, 3 post cut, 4 slot shot, 4 rim run; then secondary variants [C14]. HoopStudent credits Westhead with popularising it as "The System" [C14] | Within 6 s: attackers in opposite corners, one big at r < 3 m, the handler at the slot (θ 60–80° or 100–120°). Repo timing: outlet 0–1.5 s, wings in corners 2–5 s, trailer 4–6 s [REPO] |
| **Secondary numbered break after a make** (Coach's Clipboard, Oct 2014) | O3 inbounds to O1 and trails; O1 speed-dribbles; O2 wide to the right corner; O4 to the top of the arc in line with the left lane line; O5 rim-runs for the long pass, then the left block. Options: seam drive; corner pass; lob to O5; the "4-cut"; trailer three. After a miss, the non-rebounding post rim-runs. Inbound immediately; doubles as a press breaker [C31] | Inbound delay ≤ 2 s; corner + rim + top-of-arc occupancy |
| **Carolina primary break** | O1 receives at the ball-side slot or wing and attacks the middle third (on steals, the sideline, because middle passes get intercepted); O2 and O3 to the sideline-corner lanes (if two fill one lane, the first back-screens the second); first big down rim-runs; trailing big to the weak-side slot; after makes a designated post inbounds and the other rim-runs; 3v2 PG stops at the FT line or elbow; "Be quick, but never hurry"; some teams push only after steals or only after scores [C30] | Lane occupancy; first-big rim run; handler stop at y ≈ 4.19 m |
| **Roy Williams / UNC** | Outlet ball side; catch on the run; lanes as wide as possible; both bigs run rim to rim and the trailing big looks to hit the other; ≤ 2 defenders → ≤ 2 passes; > 2 → secondary with ≥ 3 passes unless a layup, side to side, shoulder-to-hip cuts, ball into the post; "play" the full 28.65 m [C15]. Six keys: practice fast; ball out of the net ASAP; ball to the PG; wings release on the score; shoot within ≤ 2 passes with ≤ 2 defenders; trailing big runs while the other sprints to the front of the rim [C23] | `roy_williams_window`; passes to shot; big-to-big pass within 6 s with the receiver at r < 3 m |
| **Kansas Break** (Roy Williams at Kansas) | "a half-court offense run from the full-court", used when 4–5 defenders are back; 2 and 3 fill the lanes for open threes; first big posts opposite, second fills the top; back screens for a lob on the reversal; posts loop inside to rebound [C32] | D_back ≥ 4 at t_cross_half followed by a reversal and back screen on the top big |
| **Westhead's System** (LMU, Denver) | Runs on every change of possession; shot < 7 s after a DREB and < 3 s after a make; paired with a full-court press, at times conceding easy shots [C33]. Grinnell added waves of five substitutes; LMU beat Michigan 149–115 in 1990 [C34] | Share of made-FG starts with a shot ≤ 3.0 s after the inbound; DREB starts with a shot ≤ 7.0 s |
| **Tarkanian's Runnin' Rebels** (UNLV) | Pressing defense forced turnovers that fuelled the run; 109 ppg in 1976-77 [C42] | Live-ball TO share; transition after steals |
| **D'Antoni / Nash "Seven Seconds or Less"** (Phoenix 2004–08) | "get a shot off in seven seconds or less"; fastest pace; drag screens for Nash and Stoudemire; 114.5 offensive rating, 62–20 in 2004-05 [C36]. Hollinger: more drag screens and quick early-clock plays than running [C35] | Drag screen ≤ 8 s; shot ≤ 7 s |
| **Hoiberg drag-screen break** (Iowa State, Bulls, Nebraska) | After a DREB: O2 and O3 wide to the corners; O4 rim-runs to the left block; O5 rebounds, outlets to O1 and trails; O1 catches with his "butt to the sideline" above the FT line extended; O5 sets the drag at or just inside the arc and rolls; hi-lo reads; second-wave DHO [C25] | Outlet receiver at \|x\| ≥ 6 m, y_own ≈ 4–7 m, facing the sideline; drag at r 6.5–7.5 m by the rebounder ≤ 8 s |
| **Euro early offense** (Purrà) | 8 s window; empty-side PnR with Tag&Go, Pop, Gator; step-up; high/top PnR; Veer, 5-Out, Flare, Spain, double drag "77", inverted, guard-guard, Iso; screen away; pin-down and corner exit; Flip, Handback, Give, Miami, Stagger Away; Delay and post iso; Argentina [C10] | `early_offense_action` within 8 s and 15 s |
| **EURO Transition Offense (Lithuania)** | Lanes: wings outside, ball lane, bigs' lane. After a make: 1 outlet, 2 and 3 wings, 4 inbounds and is the second trailer, 5 first trailer. Pitch ahead to a wing; 1 runs through to the weak-side corner; 5 sets a wing ball screen; reversal to 4 = into the offense [C37] | Wing ball screen by the first trailer ≤ 8 s |
| **Five-Out Five-Lane Break** | Get the outlet out of the "dead zone"; keep the middle open; pitch ahead to any advantage; ball-side dribble push to the FT lane extended; corner player pushes through to the weak side; end in a side, wing or spread ball screen [C38] | Middle-open flag; 5 occupied lanes |
| **Dribble-drive motion** (Walberg AASAA 1997 → Calipari, Memphis 2005-06, Kentucky title 2012) [C40] | Off the break: O5 on the opposite block, O2 and O4 deep in the corners; O1 drives first; little screening [C41]. A transition-specific Walberg rulebook was not found | First 8 s: corners filled at r 6.60–7.3 m, big at the opposite block (r < 2.5 m), middle drive |
| **Three-lane vs five-lane** | Three-lane: ball in the middle, runners just inside the sidelines [C18]. Five-lane: every player in a lane, middle open [C38]. A named "two-lane break" was not found | `lane_occupancy_at_halfcourt` |
| **"Run without running"** (2019-20 Lakers) | Running to the right places beats running often; first wave = wings to set three-point spots; second wave = Davis leads or trails as drag screener while the other big rim-runs; LeBron's pitch-ahead passes. Numbers are for the **2018-19** Lakers, not 2019-20: nearly 19% of possessions in transition (3rd), 37.1% of DREBs became transition sequences (2nd) (CTG, via Prada, article of 2 July 2020; re-opened 2026-10-18) [C27]; the 2019-20 "run without running" approach is described qualitatively, with no 2019-20 transition share given [C27] | Wing arrival spots; second-wave drag |

### 9.8 Defensive transition rules (each a separate measurable item)

| Rule | Definition (source) | Signature [HEURISTIC] |
|---|---|---|
| **Safety (1 back)** | One guard stays beyond the arc rather than rebounding; if he drives, another guard takes over; everyone else sprints back; first two steps matter most [C4] | `safety_repo`: at t_rel + 1.0 s, count shooting-team players at r > 7 m moving away from the attacked rim at ≥ 2 m/s [REPO: `defense_full.md` F12 "One back (safety)"]; the wider variant `safety_wide` (§2.3) is [HEURISTIC] |
| **Two guards back** | Vs teams that run every time: 3 bigs crash, 2 guards retreat to the half-court line either side of the centre circle; the ball-side guard picks up the dribbler, the other drops to the paint [C4]. Pack line: 2 guards back on every shot [REPO] | Two players at y 11–14 m, \|x\| ≤ 4 m at the opponent's DREB |
| **Shooter back first** (Underwood) | On a three-point attempt the shooter is first back, the other 4 crash [C4][C5] | First retreating player = the 3PA shooter |
| **Full Back / Half Back** (Holtmann, BCAM) | On the shot, perimeter players retreat as Full Back (protects the paint) and Half Back (pressures the ball, keeps it on one side); the first big runs to the lane and pushes the Full Back out; weak-side help to the strong side; the trail big fills the gap; "no player assignments in transition"; switch back only after the ball is stopped [C24] | Deepest defender at r ≤ 2.5 m before the ball crosses half; second defender within 2 m of the handler with sign(x) of the handler constant |
| **Protect the basket first** | First back sprints to the rim, steps out, forces a pass; the longest defender preferred [C4][C3] | t_protect − t0 |
| **Stop the ball (second back)** | Wherever the ball is, even past half [C4][C3] | t_stop, pickup y |
| **Sprint back with vision / match shooters** | Watch the shooters while sprinting; "Who has ball? Who is back?" [C4][C3] | Head orientation is not available from tracking; proxy [HEURISTIC] = a defender within 1.5 m of the ball-to-shooter segment, or within 3.0 m of the shooter, for an attacker at r ≥ 6.75 m (geometry in the §2 intro) |
| **Matchup on the fly / cross-match** | Turn, backpedal, take the nearest attacker; shooters first; match sizes where possible; call switches when a mismatch matters [C3] | §2.3 cross-match signature |
| **Automatic Pickup** (Ralph Miller) | Guard whoever you were matched with before the change of possession [C43] | Pairing at t_defense_set = pre-change pairing |
| **Tag and transition roles** | On a shot each crasher tags his man on the high side; on the opponent's rebound release at once to a role: ball stopper, middle stopper, sideline denier, weak-side denier, safety; crash only with a 50/50 chance [C5] | Crasher on the high side at the rebound; role by position 1.5 s after the opponent's DREB |
| **Jam the rebounder** | Nearest player pressures the rebounder to delay the outlet [C4] | Defender within 1.5 m of the rebounder ≥ 0.5 s; outlet delay |
| **2v1** | As low as the lowest attacker; fake and recover; concede the jumper; gap the lane [C4][C28] | Defender r ≤ attacker's minimum r |
| **3v2** | Stack top and bottom; top stops the ball and calls "ball, ball, ball!"; bottom takes the first pass; top drops to the paint [C4][C28] | Two defenders aligned on x within 1.5 m at different y |
| **Post-press "fixing it"** | After a broken press, regain matchups; never give up the layup in a 2v1 [C44] | Time from the press break (ball across y = 12.73 m) to t_matched |
| **No man's land** | No defender should still be in the backcourt when the ball crosses the defense's own three-point line (rule cited on a blog) [E13] | `no_mans_land` = count of defenders with y_own > 12.73 m (the defense's backcourt, i.e. beyond the division line from the rim they defend) at the first frame the ball has r ≤ 6.75 m (≤ 6.60 m in the corners) from that rim. Stricter variant `no_mans_land_arc` = count of defenders with r_own > 6.75 m (> 6.60 m in the corners) at the same frame; stored separately |

### 9.9 Pressing after makes and free throws

- VCU "Havoc" (Shaka Smart): full-court for 40 minutes with the double fist, and a diamond when small; trap just past half near the sideline and in the corners, avoid the middle; 2012-13 turnover rate 29.3% [C45]. Clinic notes: each trap has 2 trappers, 2 interceptors and 1 goaltender; goals are live-ball turnovers, disrupted tempo and fatigue [C44]. VCU picking up full-court on made baskets was seen only in a search summary (**unverified**).
- Westhead, Grinnell and Tarkanian tied constant full-court pressure to the running game [C33][C34][C42].
- Signature: press = ≥ 2 defenders at y > 12.73 m at the inbound after a make or FT; trap = 2 defenders within 1.5 m of the handler; fall-back event as in `defense_full.md` F9 [REPO].

### 9.10 Get-back conventions by program

| Convention | Who | Source |
|---|---|---|
| 1 back (PG), 4 crash | MSU (Izzo) | [M20] |
| Shooter back on three-point attempts, 4 crash ("send the house") | Illinois (Underwood) | [C4][M24] |
| 2 guards back, 3 crash | Vs teams that run every possession; pack-line lineage | [C4][REPO] |
| Full Back + Half Back, roles rather than assignments | Holtmann | [C24] |
| Crash 4 if small and quick or the post plays high; keep guards back if the bigs rebound slowly | Coach's Clipboard | [C5] |
| Everyone except the rim protector races back | Stan Van Gundy's Magic | [E32] |
| 3, 4 or all 5 to the glass (NBA 2025-26 trend; details paywalled) | NBA | [E32][E15] |
| "Send 3 to the glass and 2 back based on PPP" (no sample given) | Timberwolves analysis (Triano notes) | [E24] |

---

## 10. Evidence summary

Every number below is tagged with its definition (§5). Numbers from different definitions are not interchangeable. Evidence strength follows the source status in the Sources section: peer-reviewed journal articles first, then conference papers (SSAC/Sloan), then preprints and abstract-only records, then blogs, vendor pages and [calc] cross-team correlations. Most transition evidence opened here is in the last three groups.

### 10.1 Transition shows higher per-possession value in every source opened (selection-biased)

The gap is near zero in one source: Villanova 2013-14, transition 1.14 vs half-court 1.13 points per possession, a difference of about 0.01 [V6] (§6.2). See the selection caveat below the table.

| Context | Transition / early | Half-court / late | Definition, sample | Source |
|---|---|---|---|---|
| NCAA D-I since 2010 | 1.04 points per play | 0.87; about 98% of team-seasons better in transition | Synergy-style plays | [E1] |
| NCAA D-I 2014-15 | 1.03 PPP | 0.88 overall; late clock (≤ 4 s) 0.71 on < 4% of plays | Synergy, 351 teams | [E3] |
| NCAA (2017 article) | 1.040 PPP | — | Synergy | [V1] |
| NCAA D-I 2023-24 | eFG 55.04% (mean of teams) | 49.59%; 94.2% of teams better in transition | Hoop-Math, 362 teams | [calc, V9] |
| NCAA D-I 2022-23 | 54.55% (Breakthrough: 54.6%) | 49.74% (49.7%); 92.3% better | Hoop-Math, 363 teams | [calc, V11][V13] |
| NCAA D-I 2014–2016 | 54.2% | 50.2%; transition about a quarter of shot opportunities | Hoop-Math (first 10 s) | [E26] |
| NCAA late clock since 2010 | — | 0.70 PPP, 36% eFG (< 4 s on the shot or game clock) | Plays | [E1] |
| NCAA transition share | Men 17.7% of possessions | — | ShotTracker (definition unpublished) | [V42] |
| NBA 2024-25 | 1.127–1.128 PPP; mean frequency 18.6% | — | Synergy (NBA.com) | [calc, V25] |
| NBA 2019-20 | 1.23 PPP (15% of possessions) | 1.07 | Not stated (Timberwolves analysis) | [E24] |
| NBA 2017-18 | 1.126 (after live-ball rebounds) | 0.926 | Source not stated (Nate Duncan article; CTG cited only for frequency and defensive rating) | [E18] |
| EuroLeague 2018-19 | 1.19 PPP, 10% of possessions; roles: hit-ahead/leak-out 1.47, wings 1.22, ball-handler 1.05, trailers not above the half-court average | — | Synergy for the 10% share only; role PPPs are "EuroLeague's analysis" via Eurohoops (provider not named) | [E4] |
| ABA League | 11% of possessions, 1.14 PPP [E6]; 11.6%, 1.14 vs 0.93 half-court (Oct 2020) [E5] | — | Synergy | [E5][E6] |
| Inside NBA transition | Paint touch 1.38 PPP vs 0.92 without | — | Triano notes | [E24] |
| NBA transition share, other reports | Average team about 15% of offense in transition (Jan 2022) [V47]; Heat 23.4% through 30 Oct 2025 (Synergy) vs 16.5% in 2024-25 (source not stated) [V46] | — | Synergy (V47 and the Heat 23.4%); not stated (Heat 16.5%) | [V46][V47] |

**Selection caveat.** Pulled-back breaks are counted as half-court, and teams push mostly when ahead in numbers, so every transition premium overstates the value of a policy of always pushing [E1].

### 10.2 Value falls with time used

- NBA 2024-25 eFG by shot clock left (all teams summed): 24–22 s 64.3%; 22–18 s 61.0%; 18–15 s 55.9%; 15–7 s 54.3%; 7–4 s 50.8%; 4–0 s 42.3% [calc, V49]. Since 2018 the NBA resets to 14 s after an offensive rebound, so putbacks fall in the middle bins.
- NBA 2019-20 (season inferred from article context; Second Spectrum tracking): eFG 60.0% in the first 6 s, 53.1% in the middle 12 s, 43.9% in the last 6 s; points per attempt in the first 6 s: 2PA 1.26, 3PA 1.11 [E9]. NBA 2016-17: about 60% vs about 50% [E8]. Boston 2015-16: 59% in the first 6 s vs 40% in the last 6 s [E10]. "Shots in the first 6 seconds of the clock are worth 33% more than shots in the last 6 seconds" (Triano) [E24].
- NBA 2003-04, points per 100 possessions by time used: 0–10 s 112.3; 11–15 s 102.3; 16–20 s 100.6; 21+ s 91.8 [E7].
- NCAA: after a DREB, first-10-s initial shots 53% vs 47% eFG (2011-12) [V5] and 50.85% vs 47.88% (2023-24 through 19 Mar 2024, pre-tournament snapshot, 362 teams) [calc, V10]. Michigan: 52.0% in the first 10 s vs 44.9% for possessions of ≥ 11 s (Hoop-Math data, cited by Bleacher Report; the researchers' notes disagree on whether the season was 2011-12 or 2012-13); 13 of the top 30 offenses shot better early in all three shot categories, none better late in all three [V30].
- Optimal-stopping research: NBA teams under-shoot early in the clock; an optimal policy would add about 0.05 points per possession (Skinner 2012, 4,720 games) [P13]. Goldman & Rao 2017: lineups capture about 84% of the gain of a dynamic threshold, with deviations toward impatience (too many early shots) [P15]. Continuation value and the reservation threshold both fall from 14 s to 0 s left [P16]. The two papers disagree on the direction of the error but agree that value declines with time used.
- **Team level vs shot level disagree.** NBA 2025-26: correlation between a team's average possession length and its PPP is +0.25 (+0.34 after makes, +0.43 after DREBs, 0.00 after live TOs) [V36]. Across teams, slower teams are not less efficient; the early-shot premium is a within-team, shot-level effect.

### 10.3 Transition share vs winning (team level)

NCAA D-I [calc: Hoop-Math leaderboards V9, V11 joined to Torvik T-Rank E31; Pearson r across teams]:

| Pair | 2022-23 (n = 358) | 2023-24 (n = 362) |
|---|---|---|
| Transition share vs win% | 0.133 | 0.153 |
| Transition share vs adjusted tempo | 0.799 | 0.794 |
| Transition eFG vs AdjOE | 0.404 | 0.529 |
| Non-transition eFG vs AdjOE | 0.634 | 0.680 |
| Transition eFG vs win% | — | 0.494 |
| Adjusted tempo vs win% | 0.050 | −0.025 |

Tempo vs win% across Torvik seasons: r = 0.052 (2023), −0.025 (2024), −0.017 (2025), 0.038 (2026), n = 362–365 [calc, E31]. 2023-24 transition share ranged from 12.3% (Virginia) to 33.8% (Western Kentucky), mean 23.06%, SD 3.58 [calc, V9].

NBA [calc: NBA.com Synergy transition V25 joined to team advanced stats V50; n = 30 teams per season; 95% CIs by Fisher z, computed by the fixer 2026-10-18]: offensive transition frequency vs win% −0.021 (−0.38 to 0.34) (2023-24) and 0.032 (−0.33 to 0.39) (2024-25); transition PPP vs ORtg 0.548 (0.23 to 0.76) and 0.751 (0.54 to 0.87); **opponent** transition PPP vs DRtg 0.709 (0.47 to 0.85) and 0.613 (0.32 to 0.80); opponent transition frequency vs net rating −0.563 (−0.77 to −0.25) (2024-25). With n = 30, each interval is wide.

NCAA allowing transition (2023-24; V10 is the 19 Mar 2024 pre-tournament snapshot) [calc, V10 × E31]: opponents' transition share vs AdjDE r = 0.382; opponent transition eFG vs AdjDE r = 0.438; opponents' transition share vs win% r = −0.392. (n = 359 joined teams, as in §10.4; approximate 95% CIs by Fisher z: 0.29 to 0.47, 0.35 to 0.52, −0.48 to −0.30.)

Tempo and upsets (Harvard Sports Analysis Collective blog, not peer-reviewed): the first post analysed every first- and second-round NCAA tournament game from 2004 to 2009 that could produce an upset, excluding 1 v 16 and 2 v 15 games, n = 144; the 35 upsets averaged a tempo of 67.77 possessions vs 64.93 in games the underdog lost (≈ 2.8 possessions) [E40]. The follow-up post confirms n = 144 and concludes that "successful NCAA Tournament underdogs simply play at a faster tempo"; the author's reply in its comments puts the gap at "only by 3 possessions a game on average" (author's comment reply, not the post body) [E27]. Small, dated, associational sample.

Peer-reviewed winning links are mixed: fast-break points did not separate winners from losers at EuroBasket Women 2017 (effect sizes −0.17 to −0.27, "unclear"; 40 games) [P21], but did in a Philippine university league (unbalanced games t(73) = 3.61, p < 0.01; 56 games) [P22]. Cárdenas et al. found winners and losers similar in fast-break use, efficacy and points [P3].

Tempo and upsets: see the paragraph above (n = 144, 2004–2009 first and second rounds [E40]; the ≈ 3-possession figure is the author's comment reply in [E27]).

**Reading.** How **often** a team runs is almost unrelated to winning (NCAA r = 0.13–0.15, n ≈ 360; NBA r ≈ 0, n = 30); how **well** it converts transition is moderately related; how often and how well it **allows** transition is among the stronger correlates of defensive rating in these data (NCAA r = 0.38–0.44, n = 359; NBA r = 0.61–0.71, n = 30 per season, 95% CIs as wide as 0.32–0.80). All of this is correlational and cross-sectional.

### 10.4 Offensive rebounding vs getting back

**Wiens, Balakrishnan, Brooks & Guttag 2013** (SSAC conference paper, not a journal article; SportVU, 233 NBA games, 2011-12, 25 Hz) [P1]:

- 6,521 missed jump shots from ≥ 4.57 m; RI > CI on 42% of them, CI > RI on 32%.
- Net value of a missed shot (pts per possession; OREB rate in brackets):

| RI \ CI | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| 0 | −0.83 (0.21) | −0.49 (0.27) | −0.22 (0.34) | −0.12 (0.40) |
| 1 | −0.69 (0.15) | −0.53 (0.21) | −0.45 (0.29) | −0.09 (0.36) |
| 2 | −0.76 (0.11) | −0.62 (0.19) | −0.46 (0.27) | −0.36 (0.31) |
| 3 | −0.97 (0.08) | −0.85 (0.15) | −0.40 (0.28) | — |
| 4 | −1.08 (0.04) | −0.50 (0.12) | — | — |

- Average missed shot −0.549. Moving one player from retreat to crash in the most common case (CI 1 / RI 2 → CI 2 / RI 1) gains +0.17 points per missed jumper, about +4 points per game at 25 missed jumpers. Getting back early can cut the OREB probability by more than half [P1]. The authors call this an association, not causation.
- The defensive benefit of retreating is transient: its odds ratio is largest for opponent possessions of 0–2 s and decays by about 12 s.
- **MDET**: mean 2.76 m on stops vs 2.94 m on scores (Kolmogorov–Smirnov p < 0.01; 10,915 continuous post-DREB possessions < 15 s); 1.83 → 3.66 m ≈ +0.06 points per possession allowed, about 1.5 points per game; no effect beyond 15 s.
- **Unresolved**: the text on Fig. 11 says MDET "tends to increase with an increase in RI and decrease with an increase in CI", yet calls this agreement with the hypothesis that crashing worsens neutralisation. Read literally, that is backwards; the effect is small either way (about 0.2 m across the range). Check the figure before citing a direction.
- Authors' conclusion (NBA 2011-12, 233 games, associational, SSAC conference paper, not a journal article; not replicated in college data; the "+4 points per game" figure is an extrapolation from 25 missed jumpers per game): crashing usually beats the head start from getting back; once the opponent rebounds, early threat neutralisation matters more than merely getting back.

Other NBA evidence:

| Evidence | Finding | Source |
|---|---|---|
| Top-5 OREB teams, 2008-09 to 2012-13 (25 team-seasons) | Average transition-defense ranks about 13th–17th; Pacers 2012-13 4th in OREB and best transition defense (11.5% opponent transition frequency, 1.03 PPP allowed) | [E12] |
| OREB% vs opponent transition off DREBs | r = 0.44 over seven earlier seasons, 0.14 over the last three (to 2017-18) | [E18] |
| 2022-23 | OREB vs transition points allowed "essentially zero"; first-shot half-court possession 0.97 vs 1.13 after an OREB | [E19] |
| 2015-16 | Top-5 OREB teams about league average in transition defense; top-5 "chase" teams about 19th–20th; threes within 5 s of an OREB hit about 39% (SportVU) | [E20] |
| Quadrant tally 2015-16 | High OREB / bad 28, high / good 23, low / bad 21, low / good 18 | [E21] |
| Hand-tracked LAL and OKC 2019-20 (277 rebounds) | With 3 players far from the rim at the rebound, the Lakers allowed a fast break 56% of the time; ≥ 3 near the basket → 3.2 times as likely to defend transition well; Danny Green vs Terrance Ferguson net about −1 point per 100 missed shots | [E17] |
| Team scatter 2018-19 | Fast-break points allowed vs second-chance points scored, R² = 0.22 | [E13] |
| 2025-26 crash rates | Teams with OREB% > 30%: 1 (2020-21), 5 (2021-22), 20 (2025-26 as of Dec 8). PHX, POR, BOS (heavy crashers) rank 3rd, 5th and 6th in (lowest) opponent transition frequency **after DREBs** (as of 9 Dec 2025), not in overall opponent transition frequency | [E15] |
| Regression (season inferred 2025-26) | +1% OREB% → −0.6 transition points allowed per 100 raw; sign flips with controls (+0.28); no n or SE | [E22] |
| [calc] NBA.com 2023-24, 2024-25 | r(OREB%, opponent transition frequency) +0.407 and +0.298; r(OREB%, opponent transition PPP) +0.241 and −0.148; r(OREB%, net rating) 0.061 and 0.055 | [V25][V50] |
| Mechanism claim | Crashing forces opponents to fight for the board instead of leaking out (Mazzulla); Celtics track an internal crash rate | [E16] |
| League ORB% trend | 27.0 (2011-12) → 22.2 (2020-21, low) → 26.0 (2025-26) (Basketball-Reference) | [E30] |
| Situational logic | Crashing is worth more when trailing late and at the end of quarters; selection confounds the correlations (qualitative) | [E23] |
| Blog EV model | Crashing on 3PA has negative return (assumption-driven) | [E13] |

NCAA evidence:

| Evidence | Finding | Source |
|---|---|---|
| Harvard Sports Analysis 2017 (Hoop-Math 2014–2016, GAM) | Better defensive rebounding → less opponent transition; crash aggressiveness shows an **inverted U**: teams that retreat and teams that crash hard both allow fewer opponent transition chances than moderate crashers (about +1 percentage point); "aggression may be the best option" | [E26] |
| UM Hoops 2013 (all D-I 2012-13) | OR% vs opponent transition PPP: R² < 0.03; Michigan about +3 transition points allowed per game against about +1.5 second-chance points | [E25] |
| KenPom 2015 | National OR% fell 9 seasons in a row, 34.0% (2006) → 31.1% (2015); "dogmatic focus on preventing transition is not worth the tradeoff for a team that can reliably get second chances"; the offense controls 73% of OR% | [E28] |
| KenPom 3-point rebounds (2011-12, 1,164 rebounds) | OR% on missed threes: corner 33%, elbow extended 34%, upper wing 25%, top 27%; weak side gets 38–48% of long rebounds | [E29] |
| [calc] Hoop-Math 2023-24 (19 Mar 2024 pre-tournament snapshot) × Torvik, n = 359 | r(own OR%, opponent push rate after DREB) = 0.033 (95% CI about −0.07 to 0.14); bottom OR% quartile 46.4% opponent push rate vs top quartile 47.0%. r(OR%, AdjDE) = −0.257 (2023), −0.266 (2024), −0.345 (2025), −0.416 (2026) | [V10][E31] |
| D-I average OR% | 28.5 (2023) → 29.0 → 29.8 → 30.6 (2026) | [E31] |

**Synthesis.** In the NBA, crashing teams allow somewhat more transition frequency (r ≈ +0.3 to +0.4) but not clearly worse transition PPP, and Wiens' net values (one NBA season, SSAC conference paper, associational) favour crashing with 2 or more. In the NCAA, the public cross-team data opened here (two blogs [E25][E26] and one [calc] correlation, r = 0.033, 95% CI about −0.07 to 0.14, n = 359) show no clear linear cost in opponent push rate; one blog finds a small non-linear cost for moderate crashers (about +1 percentage point) [E26]. The 2013 blog measured opponent transition PPP (R² < 0.03) [E25]; no calculation of OR% vs opponent transition eFG was made in this task. No peer-reviewed NCAA study was found. OR% goes with better defense and winning, partly because it reflects talent and size [E28]. The useful split is "crash on the shot" vs "neutralise threats in the first 5 s after the opponent's DREB", not one crash-or-get-back decision.

### 10.5 Fast-break performance research (notational)

- Italy, 398 fast breaks: success 63.5% (elite) and 59.7% (sub-elite). Finishing in the lane was the only predictor of success: OR 4.90 (95% CI 2.31–10.40) elite, 3.39 (1.44–7.95) sub-elite. Break type (primary vs secondary) and numbers (advantage vs equal) did not predict success [P2].
- Spain, elite: ≤ 2 passes in 96.4%; 88.7% finished in the primary; pass-first raised success [P3].
- EuroBasket 2001 and Greek A1 (50 games): 63% baskets, 9% fouls drawn, 19% misses, 9% errors [P20].
- EuroLeague 2017-18 (240 games, 38,640 possession ends): fast-break 2-point FGs 78.2% efficient (score or foul); fast break vs not, Mann–Whitney effect size 0.64 [P12].
- Women's international ball tracking: a fast-break cluster (mean about 3.8 s) scored 60%; fastest 10 clusters 30% vs slowest 10 at 19% [P23].

### 10.6 Tracking-based detection research

- **No peer-reviewed paper was found that detects fast breaks from league-grade optical tracking in men's basketball and reports accuracy against human labels.**
- Sensor rule systems: the ±4 m centroid band [P5][P6]; validation covered only active/inactive time on one game (best AUC 0.8329 at a 2.57 m/s speed threshold, 2 s window) [P6].
- Scripted drill classification: a linear SVM reached 97.9% on 96 practice repetitions, including 17 of 17 fast breaks (too small and scripted to generalise) [P7].
- Unsupervised HMM event detection on NBA tracking (ball screen, drive, post-up; no transition event) is a template for a "break in progress" state [P8].
- Broadcast cue: camera pan estimated from compressed-video motion vectors was used to annotate fast breaks (no accuracy on the abstract page) [P11]. Useful when players leave the frame.
- Soccer: semi-supervised counter-attack detection AUC 0.912 from 27 labelled counters [P9]; a GNN study found end-to-end speed, angle to goal and angle to ball the top features of counter success [P33]; countering within 15 s of a regain: goals 12.4% vs 8.0%, shots 35.1% vs 10.6% [P29]; counterattacks OR 7.10 (3.53–14.27) for a scoring chance vs combinative attacks [P30]; counterattacks beat elaborate attacks only against an imbalanced defense, OR 1.64 (1.03–2.61) [P32]; rest defense averaged 3.70 defenders vs 2.01 attackers, success judged within 12 s of the ball loss [P31]. Lesson: always condition on the defense's state.

### 10.7 Michigan State numbers

| Item | 2022-23 | 2023-24 | 2024-25 | 2025-26 | Source |
|---|---|---|---|---|---|
| Record | 21-13 (approx., from win%) | 20-15 (approx.) | 30-7 | 27-8 | [M15][M37] |
| AdjOE / AdjDE | 114.4 / 96.4 | 113.3 (55) / 93.5 (9) | 117.3 (35) / 92.3 (6) | 123.2 (26) / 96.2 (14) | [M15] |
| Adjusted tempo (rank) | 64.6 | 65.4 (300) | 67.6 (175) | 66.2 (247) | [M15] |
| OR% (rank) / opponent OR% (rank) | 27.6 / — | 29.8 (140) / 28.5 (150) | 35.3 (29) / 24.7 (9) | 37.8 (10) / 22.4 (1) | [M15] |
| Hoop-Math transition share / transition eFG / non-transition eFG | 20.0% / 57.3% / 50.3% | 23.0% (177th of 362) / 61.1% (15th) / 48.8% | Not available (Hoop-Math stopped Nov 2024) | Not available | [V9][V11][V12] |
| Fast-break points per game | — | — | 16.73, No. 4 [M35]; 15.8, 5th (no source given) [M38] | 16.4, No. 11 (also printed 16.2 / No. 12) | [M35][M36][M38] |
| Rebound margin | — | — | +9.3 (No. 4) | +12.0 to +12.2 (No. 3) | [M35][M36] |

MSU's half-court eFG has been near or below the D-I average (48.8% in 2023-24, 50.3% in 2022-23), which makes transition a disproportionate share of its offensive value [V9][V11].

---

## 11. Comparing tracking-based labels with play-by-play, game by game

### 11.1 What play-by-play can and cannot give

- CBBD (ESPN) plays carry `clock` (string) and `secondsRemaining` (integer), so any timing rule has **1 s resolution**. Plays have no transition flag; box scores carry `fastBreakPoints` [V32]. `wallclock` may be finer but was not checked.
- toRvik exposes the official `fast_brk_pts`, `fast_brk_fgm`, `fast_brk_fga` per game from 2019 [V31].
- The official NCAA rule is state-based with no time cutoff, and excludes bonus FTs from a non-shooting foul to stop a break [V22]. FIBA's rule uses ≤ 8 s and includes stop-the-break FTs [V23]. So official fast-break points are a judgement, not a reproducible rule.
- A play-by-play transition rule must be derived from the time between the possession-start event and the shot, as VU Hoops did (any action ≤ 10 s from the change of possession, ESPN play-by-play, 33 of 34 Villanova games, with noise from intentional fouls and inbound steals) [V6].
- Possession conventions differ: an offensive rebound continues the possession for KenPom and pbpstats but starts a new one for Synergy [V28][V41][V4].

### 11.2 Per-game procedure

1. **Align** tracking time to the game clock and to every play-by-play event (already required in `docs/requirements.md`, "Alignment").
2. **Segment** possessions and chances from play-by-play and from tracking separately; report the count difference per game (expected sources of difference: offensive-rebound chances, end-of-period heaves, and possessions after stoppages).
3. **Compute play-by-play-only labels** for each possession: `tr_hoopmath_10s` (initial FGA ≤ 10 s after a DREB, steal or opponent score; dead-ball-TO starts are **not** Hoop-Math transition; putbacks ≤ 4 s after an OREB excluded) [V6][V7][V8][V10], plus the comparison field `tr_hoopmath_10s_plus_dbto`; `tr_fastscout_10s` (possession ends with ≥ 20 s on the shot clock, not after a stoppage) [V14][V14a]; `tr_vuhoops_10s` [V6]; `tr_nba_6s_clock` and `tr_nba_6s_elapsed` [E8] (the CBBD play fields listed in §11.1 are game-clock fields, so the shot-clock version must be reconstructed from the game clock and the 30 s / 20 s resets unless a feed carries the shot clock); `tr_fiba_fbp_8s` with the "defense set" condition left out (play-by-play cannot see it).
4. **Compute tracking labels** for the same possessions: every field in §5.4, including the state-based ones (`tr_synergy_like`, `tr_ctg_pro_is_transition`, `tr_fiba_fbp_8s` with the defense-set test).
5. **Points reconciliation**: tracking-derived fast-break points under (a) the NCAA rule [V22] (state-based, stop-the-break bonus FTs excluded) and (b) the FIBA rule [V23], against the official box `fastBreakPoints` [V32][V31].
6. **Timing reconciliation**: tracking first-shot time vs play-by-play first-shot time (expect a 0–1 s difference from integer seconds); share of possessions whose label flips at the 10 s boundary because of rounding.
7. **Report** one table per game (below) plus a season roll-up with the distribution of differences.

### 11.3 Per-game report template

| Definition | Unit | Count (tracking) | Count (play-by-play) | Agreement | Points (tracking) | Points (official box) |
|---|---|---|---|---|---|---|
| Official fast-break points (NCAA) | Points | — | — | — | NCAA-rule estimate | `fastBreakPoints` |
| FIBA-rule fast-break points | Points | ≤ 8 s + defense not set | ≤ 8 s only | — | — | — |
| Hoop-Math | Initial FGA | — | — | — | — | — |
| FastScout | Possessions | — | — | — | — | — |
| VU Hoops 10 s | Actions | — | — | — | — | — |
| NBA 6 s (clock reading ≥ 24 s; elapsed ≤ 6 s) | FGA | — | — | — | — | — |
| Synergy-like / CTG Pro / repo PHASE | Possessions / chances | Tracking only | n/a | n/a | — | — |
| Passed-up breaks (§8) | Opportunities | Tracking only | n/a | n/a | Value at stake | n/a |

"Agreement" for a shared unit: percent agreement and Cohen's kappa on the possession-level flag [HEURISTIC choice of statistic]. Add opponent strategy notes from §9.6 (press rate, crash count, push rate after makes).

### 11.4 Known reasons the numbers will differ

- Clock resolution (1 s in play-by-play vs 0.04–0.1 s in tracking).
- Shot clock vs elapsed time after resets (20 s after an OREB that hits the ring [C16]).
- Scorer judgement in official fast-break points (no time cutoff in the NCAA rule [V22]).
- Rule differences on stop-the-break free throws (NCAA excludes, FIBA includes) [V22][V23].
- Possession conventions (OREB inside one possession or not) [V28][V41][V4].
- Players out of frame in broadcast video (§3.4 estimated positions); flag possessions where the numbers state relied on estimates.

---

## 12. Open questions (one line each, for Aldemir)

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
14. Which numbers-state margin (0.5, 1.0 or 1.5 m, §3.4) becomes the reporting default once the label-flip rates are known?
15. Which secondary-break field (`sec_conte`, `sec_trninic`, `sec_heuristic`) and which primary-break time window (2–3 s coaching vs 3–9 s Fotinakis) feed MSU reports?
16. For NBA-style 6 s and FastScout 10 s rules on the NCAA clock, is the shot-clock reading or the elapsed time since t0 the reporting version (both stored)?

---
## Sources

Every source below was opened by a researcher during this task (2026-10-17), via WebFetch, curl, PDF text extraction or a browser; entries marked "opened 2026-10-18" or "re-opened 2026-10-18" were opened by the fixer during the verification pass. "What it confirmed" summarises what the claims in this file rely on.

### V. Vendors, analyst definitions, official manuals and statistics pages

| Key | URL | What it confirmed |
|---|---|---|
| V1 | https://fansided.com/2017/09/08/nylon-calculus-understanding-synergy-play-type-data/ | Synergy transition = defense not set, no time cutoff; recovered-defense rule (Misc); roles leak-out, ball-handler, left/right wing, trailer; NBA 1.103 / NCAA 1.040 PPP |
| V2 | https://github.com/sejaldua/synergy-scouting-app | Repeats the Synergy definition and roles |
| V3 | https://developer.sportradar.com/basketball/reference/synergy-basketball-faqs | Synergy play-type enum includes `Transition` |
| V4 | https://statsbywill.substack.com/p/what-we-talk-about-when-we-talk-about | 10 s shot-clock definition, no dead-ball starts; Synergy counts offensive rebounds as new possessions |
| V5 | https://www.burntorangenation.com/2012/7/2/3132616/five-statistical-tidbits-college-basketball-Louisville-Florida-Xavier-Kansas-Texas | Hoop-Math creator: initial shots by start type and seconds since start; 53% vs 47% eFG after DREBs; rim about 64%; steal shot mix; threes after an opponent score 32% / 30% (D-I 2011-12). Two researchers opened it; two others got HTTP 403 |
| V6 | https://www.vuhoops.com/2014/4/10/5597406/breaking-down-transition-basketball | Hoop-Math rule (initial shots ≤ 10 s; putbacks ≤ 4 s excluded); D-I 2013-14 splits; VU Hoops 10 s play-by-play method; Villanova 2013-14 ORtg by start type |
| V7 | https://web.archive.org/web/20250208231117/http://hoop-math.com/data.php | Hoop-Math definitions (archived): dead-ball-TO starts tabulated as a separate row from 2011-12 (outside the transition aggregate); defensive-foul starts excluded; 2011-12 database averages |
| V8 | https://web.archive.org/web/20250419151632/http://hoop-math.com/MichiganSt.2024.php | MSU 2023-24 offensive and defensive transition splits; page "Last updated: Wed Apr 10 21:11:52 2024"; definition "within the first 10 seconds of a possession after a steal, defensive rebound, or opponent score" (re-opened by curl of the `id_` snapshot, 2026-10-18) |
| V9 | https://web.archive.org/web/20240915065210/https://hoop-math.com/leader_o2024.php | 2023-24 transition share and eFG for all teams |
| V10 | https://web.archive.org/web/20240319072319id_/https://hoop-math.com/leader_td2024.php | 2023-24 transition defense by start type, 362 teams; page "Last updated: Tue Mar 19 01:50:48 2024" (pre-tournament snapshot); definition "after a steal, rebound, or made basket by the opponent" (re-opened and re-parsed 2026-10-18) |
| V11 | https://web.archive.org/web/20231206050010id_/https://www.hoop-math.com/leader_o2023.php | 2022-23 leaderboard |
| V12 | https://web.archive.org/web/20241216170652/http://hoop-math.com/ | Hoop-Math stopped updating in November 2024 |
| V13 | https://www.breakthroughbasketball.com/coaching/transition-stats-hoopmath | Hoop-Math 2022-23: 54.6% vs 49.7% eFG |
| V14 | https://support.hudl.com/s/article/half-court-vs-transition-stats?language=en_US | FastScout definition, stoppage list, possession start and end lists (read in a browser by one researcher; WebFetch returns only "Loading / CSS Error", so not reproducible by fetch) |
| V14a | https://web.archive.org/web/20241212013621/https://support.fastmodelsports.com/support/solutions/articles/9000236895-half-court-vs-transition-stats | Static Wayback copy (12 Dec 2024) of the original FastModel article "Half-Court vs. Transition Stats": transition = "any possession ending in the first 10 seconds of the shot-clock that is not after a stoppage of play"; stoppage list; possession-start list incl. made basket and made final FT "except in cases of an and-one"; possession-end list (opened 2026-10-18) |
| V15 | https://instatglossary.hudl.com/basketball/events/play-types/transitions/ | Hudl InStat: FGA within 4–8 s before the defense is in position; July 2024 combined-play-type change |
| V16 | https://static.hudl.com/craft/support/glossaries/Hudl-Instat-Basketball-Glossary_2022-11-23.pdf | InStat 2022: transition offense between fast break and set offense; Cut includes fast breaks |
| V17 | https://cleaningtheglass.com/stats/guide/league_context | CTG play contexts; transition until the defense is set; putbacks inside count; STL/Reb Freq; Pts+/Poss formula |
| V18 | https://docs.cleaningtheglass.com/pro/data-sets/transition-opportunities | CTG Pro opportunity rule, `is_transition`, scoring zone 2.44 m past half, defenders back/even, `is_defense_back`, timing, outlet, crash/watch, spread, inbound-delay fields |
| V19 | https://docs.cleaningtheglass.com/pro/data-sets/transition-opportunities-player | CTG `transition_role` values; player timing and start-area fields |
| V20 | https://docs.cleaningtheglass.com/pro/data-sets/chances | Chance start types; `chance_context` list |
| V21 | https://docs.cleaningtheglass.com/pro/data-sets/after-shot-positioning | Crash window; `did_position_for_off_reb`; `movement_direction` |
| V22 | http://fs.ncaa.org.s3.amazonaws.com/Docs/stats/Stats_Manuals/Basketball.pdf | NCAA Statisticians' Manual 2025-26: Fast Break Points definition and FT rules |
| V23 | https://assets.fiba.basketball/image/upload/documents-corporate-fiba-statisticians-manual-2024.pdf | FIBA fast-break points: max 8 s, defense not set; after OREB; Examples 7 and 8 |
| V24 | https://www.nba.com/stats/help/glossary | NBA Fast Break Points (circular); offensive rebound does not create a possession |
| V25 | https://www.nba.com/stats/teams/transition?SeasonYear=2024-25&TypeGrouping=offensive | NBA Synergy transition 2024-25 (and the defensive and 2023-24 variants of the same page); league PPP and frequency [calc] |
| V26 | https://www.nba.com/stats/teams/transition?SeasonYear=2025-26&TypeGrouping=offensive | NBA Synergy transition 2025-26 [calc] |
| V27 | https://www.nba.com/stats/players/transition | Transition play type "provided by Synergy" |
| V28 | https://kenpom.com/blog/behold-average-possession-length/ | KenPom APL definition; defensive APL vs defense |
| V29 | https://kenpom.com/blog/offense-vs-defense-average-possession-length/ | Offense explains 86% of APL variance |
| V30 | https://bleacherreport.com/articles/1715228-kem-pomeroys-new-stat-affirms-that-quick-offense-is-good-offense | APL 17.6 vs 18.4 s; national 18.1 s; Michigan first-10-s eFG 52.0% vs 44.9% |
| V31 | https://www.torvik.dev/reference/bart_game_box.php (and https://torvik.dev/articles/introduction.php) | toRvik box-score fast-break fields from 2019 |
| V32 | https://api.collegebasketballdata.com/api-docs.json | CBBD PlayInfo/ShotInfo fields; integer seconds; no transition flag; `fastBreakPoints` in box schemas |
| V33 | https://www.inpredictable.com/2015/03/team-pace-and-efficiency-by-possession.html | NBA 2014-15 PPP and seconds by start type; 4–6 s "fast break zone" |
| V34 | https://www.inpredictable.com/2015/04/detailed-per-possession-statistics-now.html | NBA 2011-12 to 2014-15 start-type table; technical FTs excluded |
| V35 | https://inpredictable.com/2015/11/live-ball-vs-dead-ball-turnovers.html | Live-ball TOs most efficient; dead-ball TOs grouped with made shots from then on (values only in images) |
| V36 | https://stats.inpredictable.com/nba/ssnTeamPoss.php | NBA 2025-26 start-type shares, seconds, PPP; team-level correlations |
| V37 | https://stats.inpredictable.com/nba/ssnTeamShot.php | NBA 2025-26 time to shot and eFG by start type |
| V38 | https://www.inpredictable.com/2016/01/san-antonios-stinginess-in-transition.html | NBA.com SportVU-era definition (quoted); live-ball TO possessions 9.7 s; league 1.21 PPP |
| V39 | https://thenbaunderground.com/analytics/not-all-possessions-are-created-equal | 2019-20 PPP by start type (Inpredictable and pbpstats) |
| V40 | https://thef5.substack.com/p/start-to-finish | Live-ball TO start about +17 per 100; DREB of missed two > missed three |
| V41 | https://api.pbpstats.com/get-totals/nba?Season=2024-25&SeasonType=Regular%20Season&Type=Team | NBA 2024-25 PPP and seconds by start type (with StartType variants) [calc]; live-ball TO share 57.4% |
| V42 | https://shottracker.com/blog-high-school-basketball-vs-ncaa-pace-of-play/ | Transition share by level (definition unpublished) |
| V43 | https://www.nbcsports.com/nba/news/nba-glossary-what-is-secondary-transition-fastbreak-james-harden-russell-westbrook-video | "Secondary transition" usage |
| V44 | https://basketball.scouting4u.com/blog/possession-analysis-101-transition-half-court-second-chance | State-based definition; vendor PPP rules of thumb |
| V45 | https://search.r-project.org/CRAN/refmans/hoopR/html/nba_synergyplaytypes.html | NBA Synergy play-type codes: Isolation, Transition, PRBallHandler, PRRollman, Postup, Spotup, Handoff, Cut, OffScreen, OffRebound, Misc (no definitions; re-opened 2026-10-18) |
| V46 | https://www.nba.com/news/10-numbers-know-first-10-days-2025-26 | Heat transition frequency 23.4% through 30 Oct 2025 (Synergy); 16.5% in 2024-25 (source not stated) |
| V47 | https://theboxandone.substack.com/p/understanding-analytics-why-finishing | NBA average team about 15% of offense in transition |
| V48 | https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2021.739308/pdf | Counterattack vs transition ("second wave") vs positional attack; transitions 7–12% |
| V49 | https://www.nba.com/stats/teams/shots-shotclock?Season=2024-25&SeasonType=Regular+Season | NBA eFG by shot-clock bin [calc] |
| V50 | https://www.nba.com/stats/teams/advanced?Season=2024-25&SeasonType=Regular+Season | NBA team W-L, ratings, OREB%, pace (and 2023-24) for correlations [calc] |
| V51 | https://blog.hoopsalytics.com/basketball-analytics-transition-vs-half-court-offense/ | Vendor half-court/transition tags; no definitions (weak, not used for claims) |
| V52 | https://coachhoops.substack.com/p/synergy-and-why-you-need-it | Synergy tags transition per possession (weak, not used for claims) |

### E. Efficiency and evidence articles and data

| Key | URL | What it confirmed |
|---|---|---|
| E1 | https://hoopvision.substack.com/p/should-offenses-play-faster | NCAA 1.04 vs 0.87 since 2010; late clock 0.70 PPP, 36% eFG; selection bias; Bo Ryan 4.7 per game at 1.17 PPP; diminishing returns |
| E2 | https://hoopvision.substack.com/p/the-transition-three | Transition 3P% 35.8% / 35.5%; three share 27% → 35% |
| E3 | https://web.archive.org/web/20200925053800/https://fivethirtyeight.com/features/a-shot-clock-by-shot-clock-guide-to-duke-vs-wisconsin/ | D-I 2014-15 Synergy: 0.88 overall, 1.03 transition, 0.71 late clock |
| E4 | https://eurohoops.net/en/euroleague/810717/euroleague-stats-review-transition-scoring | EuroLeague 2018-19 transition 10% (Synergy), 1.19 PPP; role PPP ("EuroLeague's analysis", provider not named) |
| E5 | https://www.aba-liga.com/news/43917 | ABA League (Synergy): 11.6% transition, 1.14 vs 0.93 PPP |
| E6 | https://www.aba-liga.com/news/42974 | ABA League (Synergy): 11% transition, 1.14 PPP |
| E7 | https://www.82games.com/clock.htm | NBA 2003-04 points per 100 by time used |
| E8 | https://nba.com/news/one-team-one-stat-lakers-rough-transition | NBA eFG about 60% first 6 s vs about 50% after (2016-17) |
| E9 | https://www.nba.com/news/schuhmann-film-study-raptors-defense | NBA 2019-20 eFG 60.0 / 53.1 / 43.9% by shot-clock window; 2PA 1.26 / 3PA 1.11 early |
| E10 | https://www.nba.com/news/one-team-one-stat-boston-celtics-early-shot-clock | Boston 2015-16 eFG 59% first 6 s vs 40% last 6 s |
| E11 | https://www.nbcsportsboston.com/nba/boston-celtics/celtics-speeding-things-up-without-rondo/358935/ | Journalist's 6 s "official" claim; Doc Rivers numbers quote |
| E12 | https://grantland.com/the-triangle/party-crashers-debunking-the-myths-of-offensive-rebounding-and-transition-defense/ | Pacers 2012-13; top-5 OREB teams' transition-defense ranks |
| E13 | https://squared2020.com/2019/11/18/offensive-crashing/ | R² 0.22; rebound distances; illustrative crash EV model; "no man's land" rule |
| E14 | https://squared2020.com/2019/05/21/transitioning-turnovers-case-study-of-golden-state-and-toronto/ | Live vs dead TO offensive ratings (129 vs 109 per 100; baseline 113.8 on 579 possessions) and possession lengths; 2–5 s window; dead-ball inbound 2–8 s |
| E15 | https://www.nba.com/news/the-athletic-nba-teams-are-crashing-boards-like-never-before-a-call-to-new-zealand-got-things-started | 2025-26 crash rates and transition-defense ranks |
| E16 | https://www.bostonsportsjournal.com/2023/12/02/nba-notebook-joe-mazzullas-celtics-using-offensive-rebounding-to-help-their-defense | Mazzulla crash mechanism; internal crash rate |
| E17 | https://fansided.com/2020/06/08/nylon-calculus-crash-the-glass-or-get-back-on-defense/ | Hand-tracked LAL/OKC zone study |
| E18 | https://nateduncannba.com/podcast-episodes/offensive-rebounding-transition-defense-evolving-tradeoff/ | OREB vs opponent transition r 0.44 → 0.14; 2017-18 transition 1.126 vs 0.926 (PPP source not stated; CTG cited only for frequency and defensive rating) |
| E19 | https://www.thescore.com/nba/news/2536613 | 2022-23 "essentially zero" correlation; 0.97 vs 1.13 PPP |
| E20 | https://www.espn.com/nba/story/_/id/14505051/transition-defense-left-offensive-rebounds-cutting-room-floor | 2015-16 OREB low; chase-team ranks; threes after OREB about 39% |
| E21 | https://www.cbssports.com/nba/news/examining-the-acceptance-and-abandoment-crashing-the-glass-on-offense/ | Opponent transition PPP trend; quadrant tally |
| E22 | https://spencertyson.substack.com/p/turnover-suppression-offensive-rebounding | OLS coefficients changing sign with controls |
| E23 | https://travispchen.com/thoughts-on-crashing/ | Situational crash logic (qualitative) |
| E24 | https://basketballimmersion.com/wp-content/uploads/2021/10/Jay-Triano-Incorporating-Analytics-into-your-Basketball-Offense.pdf | Timberwolves 2019-20: transition 1.23 vs 1.07; first 6 s +33%; paint-touch PPP; 3 crash / 2 back |
| E25 | https://umhoops.com/2013/09/26/does-offensive-rebounding-affect-transition-defense/ | D-I 2012-13 OR% vs opponent transition (R² < 0.03) |
| E26 | https://web.archive.org/web/20190907122306/http://harvardsportsanalysis.org/2017/01/college-basketball-teams-may-want-to-aggresively-crash-the-offensive-glass/ | 2014–16 eFG 54.2% vs 50.2%; inverted-U crash finding |
| E27 | https://web.archive.org/web/20200925145051/http://harvardsportsanalysis.org/2010/02/ncaa-tourney-upsets-continued-do-close-games-have-a-higher-tempo/ | Follow-up post: n = 144; "successful NCAA Tournament underdogs simply play at a faster tempo"; ≈ 3-possession gap only in the author's comment reply (re-opened 2026-10-18) |
| E28 | https://kenpom.com/blog/offense-vs-defense-rebounding/ | OR% decline 34.0 → 31.1; 73% offensive control; "dogmatic focus" quote |
| E29 | https://kenpom.com/blog/charting-3point-rebounds/ | OR% by three-point location; long-rebound sides |
| E30 | https://www.basketball-reference.com/leagues/NBA_stats_per_game.html | NBA league pace and ORB% by season |
| E31 | https://barttorvik.com/trank.php?year=2023 (also year=2024, 2025, 2026) | Full D-I T-Rank tables for correlations; D-I average OR% |
| E32 | https://www.truehoop.com/p/the-new-way-to-get-offensive-rebounds | Van Gundy's Magic raced back; 2025-26 teams sending 3–5 (paywalled detail) |
| E33 | https://windmill.substack.com/p/getting-back | Getting-back context, floor balance (background only) |
| E34 | https://www.breakthroughbasketball.com/offense/pacers-uncomfortable-pace | Coaching rules for pushing after makes (its PPP figures unsourced, not used) |
| E35 | https://collegehoopsanalytics.substack.com/p/deconstructing-the-correlation-between | Qualitative: pace alone does not correlate with winning (no coefficients; background only) |
| E36 | https://www.coachesclipboard.net/newsletters/CCNewsLetter08122026.html | Unattributed claims (not used; unverified) |
| E37 | https://sportradar.com/content-hub/blog/explaining-synergy-shot-quality/?lang=en-us | Synergy shot-quality factors incl. shot clock and possession start |
| E38 | https://hardscreenherald.substack.com/p/shot-quality-in-high-definition-the | Public shot-quality model uses seconds into possession and start type (no numbers) |
| E40 | https://web.archive.org/web/20200928021059/http://harvardsportsanalysis.org/2010/02/putting-theories-to-the-test-does-slow-tempo-aid-ncaa-tournament-upsets/ | Ezekowitz & Cohen, 11 Feb 2010 (HSAC blog): first- and second-round games 2004–2009 that could produce an upset, 1 v 16 and 2 v 15 excluded, n = 144; 35 upsets at 67.77 vs 64.93 tempo (opened 2026-10-18) |
| E39 | https://johngasaway.com/2016/01/06/the-new-clocks-making-conference-games-faster-and-therefore-higher-scoring/ | NCAA 30 s clock: 69.5 vs 64.1 possessions per 40 min (early sample; background) |

### P. Papers: peer-reviewed journal articles, conference papers, preprints and abstract-only records

The P key does not by itself mean peer-reviewed. The Status column says what was read: journal (peer-reviewed), conference, preprint, abstract only, or other. §10 weighs evidence by this status.

| Key | Status | URL | What it confirmed |
|---|---|---|---|
| P1 | conference (SSAC) | https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc220807a3_SSAC13%20-%20To%20Crash%20or%20Not%20To%20Crash.pdf (landing page https://www.sloansportsconference.com/research-papers/to-crash-or-not-to-crash) | Wiens et al. 2013: PI/PO/NPC/NPR, CI/RI, net-gain table, +0.17, MDET, 2.22 s reaction time |
| P2 | journal | https://pmc.ncbi.nlm.nih.gov/articles/PMC5424458/ (abstract pages https://www.termedia.pl/Determinants-of-the-effectiveness-of-fast-break-actions-in-elite-and-sub-elite-Italian-men-s-basketball-games,78,29207,0,1.html and the ,1,1.html variant) | Conte et al. 2017: < 8 s; phases; primary/secondary; start shares; success rates; lane-completion ORs |
| P3 | abstract only (journal) | https://hrcak.srce.hr/en/150548 (and https://hrcak.srce.hr/clanak/221527) | Cárdenas et al. 2015 abstract: starts, ≤ 2 passes 96.4%, primary 88.7%, pass-first |
| P4 | preprint (arXiv) | https://arxiv.org/pdf/2404.01909 (and https://arxiv.org/html/2404.01909, https://arxiv.org/abs/2404.01909) | Bourgeais et al. 2024, v1 "PREPRINT VERSION – March, 2024", 12 games of the 2019 FIBA World Cup: 6 s window; 9 of 10 fast breaks < 6 s (citing Cárdenas et al. 2015) |
| P5 | preprint (arXiv version read) | https://arxiv.org/pdf/1806.10412 (abstract https://arxiv.org/abs/1806.10412) | Metulini: ±4 m centroid band; filtering thresholds |
| P6 | preprint (arXiv version read) | https://arxiv.org/pdf/1906.11720 (abstract https://arxiv.org/abs/1906.11720v1) | Facchinetti et al. 2019: band rule; AUC 0.8329 |
| P7 | conference/workshop paper | https://vbn.aau.dk/ws/files/267528400/IntentifyingBasketballPlaysDAPSdef.pdf | Sangüesa et al. 2017: 96 plays, 17 fast breaks, 97.9% SVM |
| P8 | conference (NESSIS slides/paper) | https://www.nessis.org/nessis17/Keshri_adj.pdf | Keshri et al.: HMM event detection (no transition event) |
| P9 | journal | https://pmc.ncbi.nlm.nih.gov/articles/PMC8595941/ | Fassmeyer et al. 2021: soccer counter-attack detection AUC 0.912 |
| P10 | journal (arXiv version read) | https://arxiv.org/pdf/1405.0231 | Franks et al. 2015: half-court-only matchup model |
| P11 | conference (abstract page only) | https://collaborate.princeton.edu/en/publications/rapid-estimation-of-camera-motion-from-compressed-video-with-appl/ | Tan et al. 2000: camera-motion annotation incl. fast breaks |
| P12 | journal | https://pmc.ncbi.nlm.nih.gov/articles/PMC7908613/ | Matulaitis & Bietkis 2021: fast break ≤ 5 s, transition 5–8 s; 78.2%; effect sizes |
| P13 | journal (arXiv version read) | https://arxiv.org/pdf/1107.5793 (and https://arxiv.org/abs/1107.5793, https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0030776) | Skinner 2012: first-7-s fast-break rule; +0.05 points per possession |
| P14 | conference (Sloan; third-party copy) | https://www.readkong.com/page/allocative-and-dynamic-ef-ciency-in-nba-decision-making-8064211 | Goldman & Rao 2011: 7 s fast-break exclusion; half-court from 17 s remaining |
| P15 | abstract only (journal) | https://ideas.repec.org/a/eee/jeborg/v136y2017icp107-124.html | Goldman & Rao 2017 abstract: 84%; impatience |
| P16 | preprint (arXiv) | https://arxiv.org/pdf/1512.05652 | Skinner & Goldman 2015: continuation value and threshold 14 → 0 s; Wiens summary |
| P17 | conference (SSAC) | https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc220807a7_SSAC13%20-%20Live%20by%20the%20Three%2C%20Die%20by%20the%20Three%20The%20Price%20of%20Risk%20in%20the%20NBA.pdf (landing page https://www.sloansportsconference.com/research-papers/live-by-the-three-die-by-the-three) | Goldman & Rao 2013: "fast-breaks (shot clock > 14)" exclusion |
| P18 | journal | https://pmc.ncbi.nlm.nih.gov/articles/PMC12068714/ | Zhang et al. 2025: 0–8 s "fast" cluster |
| P19 | abstract only | https://sponet.de/sponet/Record/4008300 | Tavares & Gomes 2003: 70% of fast breaks 4–6 s; fast break 25.4% of attacks |
| P20 | abstract only | https://lida.sport-iat.de/dbb/Record/4011293 | Gerani et al. 2004: outcomes, origins, situation success rates |
| P21 | journal | https://pmc.ncbi.nlm.nih.gov/articles/PMC6026830/ | Conte & Lukonaitiene 2018: fast-break points winners vs losers, effect sizes |
| P22 | journal | https://mjssm.me/clanci/MJSSM_September_2021_Raval.pdf | Raval & Pagaduan 2021: fast-break points discriminate winners |
| P23 | journal | https://pmc.ncbi.nlm.nih.gov/articles/PMC9584368/ | Yu et al. 2022: fast-break cluster 3.8 s, 60% scoring |
| P24 | abstract only | https://www.sponet.de/sponet/Record/4040915?lng=en | Courel et al. 2014: fast breaks 3.96 vs 4.73 s |
| P25 | conference (SSAC) | https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc22080625_2014_SSAC_The-Three-Dimensions-Of-Rebounding.pdf (landing page https://www.sloansportsconference.com/research-papers/the-three-dimensions-of-rebounding) | Maheswaran et al. 2014: crash phase release → ball nearest the rim |
| P26 | abstract only | https://archives.rpd-online.com/article/view/673.html | Refoyo et al. 2009 abstract: 294 fast breaks, 30 Olympic games, sex differences |
| P27 | journal | https://sportspa.ftos.untz.ba/index.php/sportspa/article/download/222/209/208 | Jeličić 2021: Trninić typology; Fotinakis primary 3–9 s, secondary 6–12 s; ≤ 15 s criterion |
| P28 | journal | https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/ | U18 EuroLeague LPS: per-quarter peak speeds 5.2–5.5 m/s; 94 players, 13 games |
| P29 | abstract only | https://lida.sport-iat.de/dfb/Record/4047515 | Hobbs et al. 2018 (soccer): counters < 15 s, 12.4% vs 8.0% goals |
| P30 | journal | https://pmc.ncbi.nlm.nih.gov/articles/PMC6751314 | González-Rodenas et al. 2019: counterattack OR 7.10 |
| P31 | journal | https://www.jssm.org/jssm-22-707.xml-Fulltext | Forcher et al. 2023: rest defense 3.70 vs 2.01; 12 s window |
| P32 | abstract only | https://lida.sport-iat.de/dfb/Record/4018266?lng=en | Tenga et al. 2010: OR 1.64 vs imbalanced defense |
| P33 | preprint (arXiv abstract) | https://arxiv.org/abs/2411.17450 | Bekkers & Sahasrabudhe: GNN counterattack features |
| P34 | journal | https://pmc.ncbi.nlm.nih.gov/articles/PMC12121881/ | Amatria Jiménez et al. 2025: possession-duration bins (background) |
| P35 | other (talk slides) | https://statmath.wu.ac.at/research/talks/resources/2018_04_Zuccolotto_Manisera_basketball_data_science.pdf | Shot-clock pressure in the last 1–2 s (background) |
| P36 | abstract only (preprint) | https://arxiv.org/abs/1902.08081 | DeepHoops abstract (no transition statement; negative check) |
| P37 | journal | https://pmc.ncbi.nlm.nih.gov/articles/PMC6231352/ | J Hum Kinet 2018: no operational fast-break definition (negative check) |
| P38 | other (high-school paper) | https://wsb.wharton.upenn.edu/wp-content/uploads/2025/05/defensive-motor-index-pratik-wharton-paper-1.pdf | High-school paper; no operational transition definition (not usable) |
| P39 | abstract only | https://reference-global.com/article/10.2478/ijcss-2025-0005 | Schmid et al. 2025 GNN shot quality abstract (no transition features; negative check) |
| P40 | abstract only (preprint) | https://arxiv.org/abs/1408.0777 | EPV paper abstract (no time-in-possession numbers; negative check) |
| P41 | journal | https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full | Stone et al. 2022: NCAA D-I men, Kinexon IMU 20 Hz, 27 games of 2020-21; max speed C 6.23 ± 0.33, F 6.63 ± 0.52, G 7.04 ± 0.39 m/s (Table 3); "10 players" but 4 + 3 + 4 by position; Methods give mph (opened 2026-10-18) |

### C. Coaching terms, systems and rules

| Key | URL | What it confirmed |
|---|---|---|
| C1 | https://assets.fiba.basketball/image/upload/documents-corporate-regional-offices-europe-programs-fiba-europe-coaching-certificate-fiba-europe-basketball-terminology.pdf | FIBA Europe terminology: transition, fast break, filling the lanes, outlet, primary/secondary, rim runner, safety (offensive), drag, double drag, trailer, wing spot |
| C2 | https://hoopstudent.com/basketball-fast-break/ | Primary within 2–3 s; secondary after the primary is stopped |
| C3 | https://hoopstudent.com/transition-defense/ | Protect the basket, stop the ball, match up; switching areas |
| C4 | https://www.coachesclipboard.net/TransitionDefense.html | Safety; two guards back; jam; shooter back (Underwood); first back to the rim; second back stops the ball; 2v1 and 3v2 rules |
| C5 | https://www.coachesclipboard.net/offensive-rebounding-and-transtion-defense.html | Tagging on the high side; post-rebound roles; 50/50 rule; how many crash |
| C6 | https://www.cbssports.com/nba/news/the-art-of-the-leak-out-starring-corey-brewer | Leak-out timing; Brewer 28.1% transition share |
| C7 | https://grantland.com/the-triangle/how-kenneth-faried-outplays-andrew-bynum/?print=1 | Rim-runner description |
| C8 | https://slappinglass.substack.com/p/double-drag-screens-a-primer | Drag and double drag ("77") geometry |
| C9 | https://www.thescore.com/nba/news/2772064 | Half-court sense of cross-matching |
| C10 | https://pere.substack.com/p/1-early-offense | Early offense first 8 s; Euro early-offense actions |
| C11 | https://www.coachesclipboard.net/SecondaryBreak.html | Secondary roles; trailer to the opposite elbow |
| C12 | https://www.drillsandplays.com/en/playbooks/6956-notes-clinic-jota-cuspinera-transition-offense-defense-defensive-recovery-defensive-adjustments/show_all_steps | Cuspinera drill from mismatches (thin; background) |
| C13 | https://hoopstudent.com/basketball-outlet-pass/ | Outlet pass; touchdown pass |
| C14 | https://hoopstudent.com/numbered-fast-break/ | Numbered break lanes, options, Westhead credit |
| C15 | https://coachingtoolbox.net/blog/roy-williams-on-transition-offense | Roy Williams rules |
| C16 | https://www.naia.org/wp-content/uploads/2026/05/2025-26_Men-s_Basketball_Rules_Book-BR26.pdf | NCAA 2025-26 men's rules: court, ring, three-point line, lane, division line, shot clock 30/20, 10 s count |
| C17 | https://www.theringer.com/2025/06/16/nba/indiana-pacers-nba-finals-2025-seven-seconds-or-less-suns-mike-dantoni-offense | Pacers push off made FGs and FTs; hit-ahead |
| C18 | https://specialolympicswisconsin.org/wp-content/uploads/2024/10/Basketball-Fast-Break.pdf | Fill lanes just inside the sidelines; PG down the middle |
| C19 | https://hoopstudent.com/transition-offense/ | Transition offense; primary (2–3 s) and secondary |
| C20 | https://hoopstudent.com/basketball-secondary-break/ | Secondary begins after the primary is stopped |
| C21 | https://www.active.com/basketball/articles/defensive-rebounding-a | Outlet receiver in line with the FT elbow outside the arc |
| C22 | https://www.mensbasketballhoopscoop.com/basketball-team-shooting-drills-for-coaches-players/8/ | Pass faster than dribble; decide who pushes |
| C23 | https://www.mensbasketballhoopscoop.com/roy-williams-transition-offense/ | Roy Williams six keys; secondary sets |
| C24 | https://playbank.fastmodelsports.com/library/basketball/fastdraw/92338/play-BCAM--Chris-Holtmann--Transition-Defense | Holtmann Full Back / Half Back; no assignments in transition |
| C25 | https://www.coachesclipboard.net/HoibergTransition-DragScreen.html | Hoiberg drag break |
| C26 | https://www.mensbasketballhoopscoop.com/simple-basketball-plays-secondary-break/ | Secondary off makes or misses; "pull it out and run your normal offense" |
| C27 | https://mikeprada.substack.com/p/how-to-run-without-running?open=false | Prada, 2 July 2020: 2019-20 Lakers waves and flow (qualitative); 2018-19 Lakers nearly 19% of possessions in transition (3rd) and 37.1% of DREBs became transition sequences (2nd), per CTG (re-opened 2026-10-18) |
| C28 | https://www.coachesclipboard.net/MSUTransitionDrill.html | MSU progressive drill; 2v1–5v4 offensive and defensive rules |
| C29 | https://hooptactics.net/premium/offense/earlyoffense/earlyphases.php | Early Push 2–4 s, Flow, Continuity; numbers goals; calling off the push |
| C30 | https://www.coachesclipboard.net/TransitionOffense.html | Carolina primary break; start-type selectivity; "Be quick, but never hurry" |
| C31 | https://coachesclipboard.net/newsletters/CCNewsLetter10012014.html | Secondary numbered break after a make; the 4-cut |
| C32 | https://www.espn.com/ncb/2003/0121/1496444.html | Kansas Break |
| C33 | https://www.espn.com/ncb/2003/0312/1522592.html | Westhead's System: < 7 s after DREB, < 3 s after a make |
| C34 | https://en.wikipedia.org/wiki/Run_and_gun_(basketball) | Westhead < 7 s; Grinnell waves; LMU 149–115 |
| C35 | https://www.si.com/nba/2012/11/12/mike-dantoni-lakers | Hollinger on 7SOL as drag screens and early-clock plays |
| C36 | https://www.thescore.com/news/1969570 | "get a shot off in seven seconds or less"; 114.5 rating; 62–20 |
| C37 | https://playbank.fastmodelsports.com/library/basketball/fastdraw/170232/play-EURO-Transition-Offense | EURO (Lithuania) transition roles |
| C38 | https://playbank.fastmodelsports.com/library/basketball/fastdraw/191715/play-Five-Out--Five-Lane-Break | Five-lane break principles |
| C39 | https://www.eurohoops.net/en/euroleague/1659994/pablo-laso-explains-his-transition-offense-first-of-all-you-need-good-defense/amp/ | Laso: defense first; push after being scored on and after DREBs |
| C40 | https://en.wikipedia.org/wiki/Dribble_drive_motion | Walberg AASAA 1997; Memphis; Kentucky 2012 |
| C41 | https://www.coachesclipboard.net/DribbleDriveMotionOffenseMore.html | DDM off-the-break alignment |
| C42 | https://en.wikipedia.org/wiki/Jerry_Tarkanian | Press-fuelled run; 109 ppg in 1976-77 |
| C43 | https://www.physicaleducationupdate.com/public/888.cfm | Ralph Miller's Automatic Pickup rule |
| C44 | https://www.mensbasketballhoopscoop.com/?p=18679 | Shaka Smart Havoc notes; "fixing it" |
| C45 | https://www.si.com/college/2013/02/11/vcu-press | VCU 40-minute press; traps; 29.3% turnover rate |
| C46 | https://www.coachesclipboard.net/newsletters/CCNewsLetter01152016RED.html | MSU drill summary (background) |
| C47 | https://www.physicaleducationupdate.com/public/522.cfm | Izzo rebound-to-break drill (scoring rules contradict each other; background) |

### M. Michigan State and Big Ten

| Key | URL | What it confirmed |
|---|---|---|
| M1 | https://statenews.com/article/2021/11/msu-basketball-2021-fast-break-revamped | "Go hard, go fast but be under control"; diagonal dribble; fast-break points 2018-21; GVSU press; "walked the ball up the court" |
| M2 | https://statenews.com/article/2007/01/revving_it_up | 2006-07 slowdown and reasons |
| M3 | https://spartanavenue.com/michigan-state-basketball-may-have-most-explosive-fast-break-duo-in-tom-izzo-era-01k1bmkp0r53 | 2025-26 lanes: Fort right, Carr left |
| M4 | https://spartanavenue.com/the-biggest-key-to-beating-uconn-is-always-in-tom-izzo-s-gameplan-01kmkajksep6 | MSU transition FG% 68.9% (CBB Analytics); four-back opinion |
| M5 | https://www.cbssports.com/college-basketball/gametracker/preview/NCAAB_20260124_MD@MICHST | MSU 91–48 Maryland; fast-break points 31–0 |
| M6 | https://www.nbcsports.com/mens-college-basketball/news/march-madness-2025-tom-izzo-michigan-state-on-verge-of-their-ninth-final-four | "Defend, Rebound and Run"; Fears pushing |
| M7 | https://www.cbssports.com/college-basketball/news/cassius-winston-led-no-10-michigan-st-beats-oakland-99-69 | 47 fast-break points; quick scores after makes; "fastest team" |
| M8 | https://spartanavenue.com/2016/05/01/michigan-state-basketball-basics-steady-philosophy/ | MSU pushes after every opponent possession |
| M9 | https://statenews.com/article/2015/02/transitiongamestrongformsu | "Speed kills"; slowdown for foul trouble |
| M10 | https://statenews.com/article/2008/03/spartans_torch_indiana_103-74 | "best fast breaking team I've seen here" |
| M11 | https://sportsnaut.com/college-basketball/transition-boosted-michigan-state-out-to-stop-streaking-stony-brook | "Our defense gets our running game going" |
| M12 | https://impact89fm.org/121010/sports/halls-career-high-pushes-msu-past-penn-state/ | "Our fastbreak is where we're at our best" |
| M13 | https://umhoops.com/2025/02/20/familiar-formula-michigan-preps-for-classic-michigan-state-test/ | Church's scout of MSU (verbatim: "the wings are sprinting down the wings", "the first big down puts pressure on the rim", "They just run so fast, all five of them"); writer's narration: "off of makes or misses"; MSU led the Big Ten in fast-break points; Michigan's transition-defense rank (re-opened 2026-10-18) |
| M14 | https://www.wilx.com/2026/03/08/no-8-michigan-state-basketball-looks-win-rematch-against-no-3-michigan/ | MSU 16.4 fast-break points per game (also 16.2 / 12th) |
| M15 | https://barttorvik.com/team.php?team=Michigan+St.&year=2026 (also year=2024 and year=2025) | MSU T-Rank efficiency, tempo, OR%, TO%, ranks |
| M16 | https://casinobeats.com/2026/02/26/michigan-state-vs-purdue-cbb-odds-predictions-picks-for-thursday-february-26/ | KenPom tempo: Purdue 295th, MSU 266th |
| M17 | https://playbank.fastmodelsports.com/library/basketball/fastdraw/363514/play-MSU-Transition | "Coach Izzo early transition look": trailer pitch-back; pass before the timeline |
| M18 | https://onlinestore.coachingtoolbox.net/product/all-access-michigan-state-basketball-practice-with-tom-izzo/ | Izzo 2010 break concept into the flex |
| M19 | https://coachingtoolbox.net/basketball-drills/basketball-drills-tom-izzo-transition.html | Izzo transition drill 2v1 → 5v5 |
| M20 | https://coachingtoolbox.net/?p=14678 | Zall's MSU defensive playbook: hit-find-fetch; send 4, PG back |
| M21 | https://grantland.com/the-triangle/war-tom-izzo-michigan-state-spartans-rebounding/ | War drill; rebounding ranks |
| M22 | https://www.mensbasketballhoopscoop.com/?p=23659 | Izzo open-practice break drills |
| M23 | https://umhoops.com/2026/01/05/inside-michigans-13-0-start-the-blueprint-behind-the-dominance/ | Michigan 14.4 s, 75.3 possessions, 25.7 transition points (7.8 more than MSU); Iowa history |
| M24 | https://www.si.com/college/illinois/basketball/secret-illinois-basketball-elite-transition-defense | Illinois "send the house"; transition numbers |
| M25 | https://hawkfanatic.com/?p=34285 | McCaffery quotes |
| M26 | https://hawkeyesports.com/news/2024/04/19/iowa-mbb-2023-24-final-notes | Iowa 2023-24 fast-break points and pace |
| M27 | https://www.kcrg.com/2025/10/15/mccollum-sets-measured-expectations-1st-season-iowas-head-coach | McCollum on pace |
| M28 | https://www.si.com/college/purdue/basketball/keeping-iowa-out-of-transition-a-big-key-for-purdue-coach-matt-painter-says | Painter quote |
| M29 | https://www.insidethehall.com/2026/01/27/what-to-expect-iu-basketball-hosts-purdue/ | Purdue 2025-26 turnover rate |
| M30 | https://www.actionnetwork.com/ncaab/college-basketball-odds-picks-betting-wright-state-vs-purdue-tuesday-november-16 | Purdue tempo history |
| M31 | https://www.si.com/college/indiana/basketball/indiana-basketball-one-critical-shift-2026-27 | Indiana 2025-26 fast-break points and tempo |
| M32 | https://hurrdatsports.com/hailvarsity/mens-basketball/pace-a-difference-in-nebraska-mens-basketball-win-over-oregon/ | Hoiberg "smart pace"; pushed after makes; tempo rank |
| M33 | https://www.on3.com/teams/kentucky-wildcats/news/kentucky-better-prepared-handle-michigan-state-transition-offense/ | MSU 2025-26 Synergy: about 20% of points in transition at 1.149 PPP (first 3 games); single-researcher read, HTTP 403 on re-check 2026-10-18 |
| M34 | https://247sports.com/college/michigan/article/michigan-bracing-for-michigan-states-elite-transition-offense-ive-never-seen-anything-like-it-245982783/ | MSU > 15 fast-break points; 16-1 above 68 possessions; Wolf quote; page undated, previews a Friday-night game (re-opened 2026-10-18) |
| M35 | https://msuspartans.com/news/2025/3/8/mens-basketball-no-8-michigan-state-hosts-no-17-michigan-on-sunday-for-senior-day-at-the-breslin-center | MSU 2024-25: 16.73 fast-break points per game, No. 4; rebound margin |
| M36 | https://msuspartans.com/news/2026/3/7/mens-basketball-no-8-michigan-state-closes-out-regular-season-with-top-10-matchup-faces-no-3-michigan-on-sunday-afternoon | MSU 2025-26: 16.4 fast-break points per game, No. 11; rebound margin |
| M37 | https://www.sports-reference.com/cbb/schools/michigan-state/men/2025.html | MSU 2024-25 record and per-game stats |
| M38 | https://spartanavenue.com/3-key-advantages-michigan-state-basketball-has-over-auburn-in-the-elite-8-01jqjsbydr04 | MSU 15.8 fast-break points per game, 5th (no source given) |

### Also opened (context or negative checks; no claim in this file rests on them alone)

- https://developer.sportradar.com/basketball/reference/synergy-basketball-overview (no transition definition)
- https://docs.cleaningtheglass.com/pro/data-sets/ ; https://docs.cleaningtheglass.com/ ; https://docs.cleaningtheglass.com/pro/data-sets/shots (CTG docs index and shot fields; no transition field on shots)
- https://cleaningtheglass.com/stats/league/context (only the 2026-27 preseason visible; not used)
- https://www.nba.com/stats/help/faq (no transition definition)
- https://api.collegebasketballdata.com/docs (docs landing)
- https://blog.hoopsalytics.com/live-ball-turnovers-vs-dead-ball-turnovers/ (reproduces Inpredictable's chart; values not in text)
- https://fansided.com/2018/06/28/second-spectrum-redesigning-nba/ ; https://en.wikipedia.org/wiki/Player_tracking_(NBA) (no Second Spectrum transition definition)
- https://shottracker.com/?p=2562 ; https://developer.shottracker.com/basketball/event.html ; https://developer.shottracker.com/docs/basketball/event/fields (no transition field)
- https://en.wikipedia.org/wiki/Basketball_scorekeeping (no fast-break rule)
- https://arxiv.org/abs/2305.13032 (four-factors decomposition abstract)
- https://instatglossary.hudl.com/basketball/ (InStat glossary index)
- https://coachingtoolbox.net/category/transitionconversion-drills/page/3 (Izzo drill posting, 2014)
- https://spartanavenue.com/jeremy-fears-jr-has-drastically-improved-his-athleticism-this-offseason-per-tom-izzo-01k5w1mv14kp ; https://spartanavenue.com/3-reasons-michigan-state-is-going-to-beat-uconn-to-advance-to-the-elite-8-01kmrd0e3sdr ; https://www.insidethehall.com/?p=121207 ; https://www.si.com/college/iowa/basketball/two-keys-iowa-hawkeyes-victory-ole-miss ; https://hawkeyestate.substack.com/p/punch-counterpunch (qualitative only)

### Attempted but not opened (claims depending only on these are marked unverified)

- https://support.synergysports.com/support/solutions/articles/77000565960--common-terms-definitions (login)
- https://support.fastmodelsports.com/support/solutions/articles/9000236895 (redirect to a Hudl 404 for three researchers; the Hudl article itself was opened as V14)
- hoop-math.com (DNS failure; archived copies used instead)
- https://mgoblog.com/comment/1893716 (bot check)
- barttorvik.com via curl (JS check; browser views used for M15 and E31)
- https://www.mdpi.com/2076-3417/16/20/10083 (403)
- https://link.springer.com/article/10.1007/s10618-021-00763-7 (login; Bauer & Anzer 2021)
- https://www.nature.com/articles/s41598-025-98877-1 (login)
- https://ddd.uab.cat/record/62688 (bot protection; Refoyo et al. 2009 full text)
- https://hrcak.srce.hr/file/221527 (HTTP 418; Cárdenas full PDF)
- https://fivethirtyeight.com/features/the-best-way-to-derail-an-nba-offense-make-it-waste-time/ (redirect)
- http://www.sloansportsconference.com/wp-content/uploads/2018/02/2008.pdf (404; Hobbs et al. full paper)
- https://kenpom.com/blog/the-possession/ and KenPom team pages (403)
- Breakthrough Basketball Westhead and Carolina pages (403); Detroit Free Press 2023 and 2024 (403 or search summary only); on3 Maize & Blue preview (403); Harvard Sports Analysis live pages (HTTP 500); hoopstudent primary-break and drag-screen pages (500); CTG stats-guide play_context (500); detroitbadboys (403); nba.com/heat feature (empty); humankinetics excerpt (not served); revistas.usp.br (redirect loop); chusmateoacademy PDF (DNS); NCAA.com 2018 pace article (empty); stats.nba.com API (timeout); ResearchGate (403); journals.ekb.eg (refused); academia.edu Liu et al. 2004 (403)


---

## Additions 2026-10-18

Gap-filler pass, written 2026-10-18. Everything below adds to the sections named in each heading and does not replace them. New sources carry keys **[GF1]–[GF33]**, listed in "Sources for the additions" at the end of this section. All were opened on 2026-10-18. The GF prefix keeps them from colliding with the V/E/P/C/M keys above. **[calc-GF]** marks numbers this pass computed from opened data, with the method stated next to them. The rules above still apply: definitions are never merged, units are metric, and court positions are in the attacked-rim frame (y = distance toward the attacked rim, half-court line at y = 12.73 m, §3.4).

### A1. Stopped by foul: take fouls as a defensive-transition tactic, start type and outcome (adds to §3.3, §8.4, §9.8, §11)

**NBA rule, from 2022-23** [GF1][GF2]:

- **Transition take foul:** "an intentional foul committed by a defender to deprive the offensive team of a fast-break opportunity". A take foul is one where the defender does not make a play on the ball [GF1].
- **Transition scoring opportunity:** after a change of possession, "the offensive team is continuously advancing the ball while it has an advantage based on the speed of the play", the position of the defenders, or both [GF1]. The full sentence is longer than the quote limit, so the defender-position clause is paraphrased here. The brief's wording ("continuously advancing the ball with an advantage based on speed, defender position, or both") is a paraphrase of this sentence, not a quote.
- **Penalty:** one free throw, which any player on the floor may take, plus possession for the offense. The defender gets a common personal foul. Before the rule, a take foul cost only a personal foul and a side out, unless the team was in the bonus [GF1][GF2].
- **Exemptions:** the last two minutes of the fourth quarter and of any overtime [GF1][GF2].
- **Scope:** the penalty still applies to a foul made immediately after a change of possession, before the offense can advance. It also applies to a foul on an offensive player without the ball. It does not apply to a shooting foul or to a legitimate play on the ball, though a clear-path foul may still apply [GF1][GF2].
- **Origin:** the Competition Committee reviewed a similar experimental G League rule in use since 2018-19. No G League figures are published on either page [GF1][GF2].

**NBA clear-path foul (Rule 12-B, Section I), a stricter geometric definition** [GF3]. A clear-path foul requires all of the following:

- the foul is on an offensive player "during his team's transition scoring opportunity";
- the ball is ahead of the tip of the centre circle in the backcourt;
- no defender is ahead of the offensive player who has the scoring opportunity;
- that player controls the ball, or a pass to him has been released;
- the foul deprives the offense of the opportunity.

The penalty is two free throws plus possession [GF3]. The page carries 2026-27 navigation links and does not contain the words "take foul". The take-foul text was therefore taken from the league releases [GF1][GF2], not from the rule book.

**Two new measurable break definitions (stored separately; never merged with §5):**

| Field | Rule | Source |
|---|---|---|
| `tr_nba_tso` | From the change of possession t0, the ball advances toward the attacked rim without stopping. Proposed test [HEURISTIC]: ball velocity along y toward the rim ≥ 1.0 m/s in every 0.5 s window. There must also be an advantage from speed or position: A_play − D_back ≥ 1 (§3.4), or the handler's speed is ≥ 1.0 m/s above the deepest defender's retreat speed [HEURISTIC]. The flag ends at the first window that fails | Concept [GF1]; thresholds [HEURISTIC] |
| `tr_nba_clear_path` | Ball at y < 12.73 + 1.83 = 14.56 m (ahead of the tip of the backcourt circle; NCAA and NBA centre-circle radius 1.83 m). No defender has a smaller y than the attacker with the opportunity. That attacker holds the ball, or a pass to him is in the air | [GF3]; geometry [derived] |

**Evidence on cost and frequency (NBA)** [GF4]. Zach Kram, *The Ringer*, 10 Nov 2022:

| Measure | Value | Notes |
|---|---|---|
| Take fouls, 2017-18 | 0.32 per game, both teams combined | Kevin Pelton count; end-of-game intentional fouls excluded |
| Take fouls, 2021-22 | 1.4 per game | Up 332% in four seasons |
| Transition take fouls, first three weeks of 2022-23 | 0.33 per game | October 0.37; November so far 0.27 |
| Estimated cost of one transition take foul | about 1.89 points | 1.08 PPP after non-shooting fouls in 2021-22, plus 0.81 points from the free throw |
| Fast-break points per game, first three weeks of 2022-23 | 14.4 | vs 13.1 at the same point averaged over the previous 10 seasons (NBA Advanced Stats) |
| Transition efficiency, early 2022-23 | 1.26 points per play | Highest in the CTG database |

The URL in the brief (…/23450356/…) returned HTTP 404. The article was opened at the …/23450776/… URL [GF4].

**NCAA rule.** No NCAA transition take-foul rule was found.

- No NCAA committee or PROP item on take fouls turned up in searches covering 2022–2026. Absence is not proven, because NCAA news pages redirected or returned empty bodies.
- An ordinary foul to stop a break is a common foul: a side out, or bonus free throws once the team is in the bonus. It becomes Flagrant 1 (two free throws plus possession) only when the official judges it so.
- The NCAA Flagrant 1 examples, as quoted on an officiating forum in Jan 2012 [GF5], include "Pushing or holding a player from behind to prevent a score". They also include contact "that is not a legitimate attempt to play the ball or player" when it is designed to stop the clock or keep it from starting.
- The 2025-26 NCAA men's rule book PDF (hosted on naia.org) was larger than the 10 MB fetch limit and could not be opened. The **current wording is unverified**.
- FIBA's unsportsmanlike-foul criterion for stopping a fast break (contact from behind or the side with no defender between the attacker and the basket) was seen only in a search summary (**unverified**).
- Box-score treatment is unchanged from D7/D8 [V22][V23]: NCAA official fast-break points exclude bonus free throws from a non-shooting foul that stops a break; FIBA counts the free throw from a foul on the outlet receiver.

**NCAA frequency estimate from play-by-play** [calc-GF; ESPN public play-by-play, parser in A5].

A **take-foul candidate** is the first defensive foul in a possession that meets all of these conditions:

- the possession started live: steal, player or team DREB after a missed FG, or DREB after a missed FT;
- the foul came 1–4 s after the start (t0);
- no FGA came before the foul, and none at the same clock second;
- no free throw followed at the foul's clock second, so it was a side out and not in the bonus;
- the foul was not in the last 120 s of the second half or of an overtime.

Play-by-play cannot show whether the defender played the ball, so this is a **superset of take fouls on the side-out branch** (it includes reach-ins and hand-checks) and **misses take fouls in the bonus**. Results:

| Season | Good games | Candidates per game (both teams) | Variant 0–4 s, no FT | Variant 0–4 s, any | Variant 0–6 s, no FT |
|---|---|---|---|---|---|
| 2025-26 | 6,142 | **0.86** | 2.21 | 4.38 | 2.57 |
| 2024-25 | 5,437 | **0.94** | 2.35 | 4.37 | 2.74 |

- The 0 s windows include fouls charged at the same clock second as the rebound (rebounding and loose-ball fouls), so they overstate the count. The 1–4 s figure is the preferred one.
- Points after a 2025-26 candidate: **1.083 PPP** (n = 5,291). Live-start possessions without a candidate: 1.116 PPP (n = 350,395). Live-start possessions whose first FGA came 1–6 s after t0: **1.441 PPP** (n = 81,668). 2024-25: 1.044 / 1.089 / 1.414.
- Descriptive comparison only: fouls are selected on situations, so these PPP gaps are not the causal value of a foul. Read naively, a side-out foul in college costs about 1.08 points instead of the about 1.44 that an early-shot break produces, and NCAA rules add no free throw. That is the incentive gap the NBA closed in 2022-23.
- By start type, 2025-26 candidates followed: player DREB 3,565, steal 1,454, FT DREB 175, team DREB 97.
- The 2024-25 and 2025-26 NCAA rates of about 0.9 per game sit between the NBA's 0.32 (2017-18) and 1.4 (2021-22) [GF4]. The units differ (candidates vs counted take fouls), so they are not directly comparable.

**Labelling changes (proposed; each stored as its own value, nothing merged):**

- **§3.3 new defensive phase "Foul to stop".**
  - Definition: a non-shooting defensive foul while `tr_nba_tso` or any §8.2 opportunity flag is active, before the first FGA.
  - Timestamp `t_foul_stop`. Measures: t_foul_stop − t0; the ball's y at the foul; distance from the fouler to the ball (> 1.0 m = no play on the ball [HEURISTIC]); whether the fouled player had the ball.
- **§8.4 new category "Fouled (stopped by foul)", separate from Declined, Denied and Failed.**
  - Subtypes: `foul_take_candidate` (no play on the ball, tracking proxy above); `foul_side_out` (not in the bonus); `foul_bonus_fts`; `foul_flagrant1`.
  - The value at stake is V(state at t_foul_stop) minus the realised value of the possession after the foul (§A2).
- **§9.8 new rule "Take the foul when beaten".**
  - Signature: `foul_take_candidate` while A_play − D_back ≥ 1 or `tr_nba_clear_path` = true.
  - Report per team and game: count, share of opportunities ended this way, and the fouler (role and foul count).
- **§11 per-game report.**
  - New row "Breaks stopped by foul": tracking count; play-by-play count of take-foul candidates (rule above); agreement.
  - Point reconciliation: NCAA official fast-break points exclude bonus free throws from these fouls [V22]; FIBA-rule points include the outlet-foul free throw [V23].
  - §11.4 new reason: league rules differ. NBA from 2022-23: 1 FT + possession, exempt in the last 2 min of Q4/OT. NBA clear path: 2 FT + possession. NCAA: common foul (side out or bonus FTs) unless ruled Flagrant 1. So NBA take-foul rates and costs must not be carried over to MSU.

### A2. Possession-value models (EPV / POINTWISE) for valuing break states and passed-up breaks (adds to §3.4, §8.5)

**The framework** [GF6][GF7]. Cervone, D'Amour, Bornn and Goldsberry, "A Multiresolution Stochastic Process Model for Predicting Basketball Possession Outcomes", *JASA* 111(514), 2016, DOI 10.1080/01621459.2016.1141685; arXiv:1408.0777 v1 4 Aug 2014, v3 25 Feb 2016. The brief spelled the fourth author "Goldsner"; arXiv lists Kirk Goldsberry [GF6].

- **EPV:** ν_t = E[X | F_t], the expected points (X ∈ {0, 2, 3}) of the possession given its tracking history up to time t. It is a martingale, so it changes only through on-court actions.
- **Model structure:** a coarsened semi-Markov chain over states made of ball-carrier × 7 court regions × "defended" (a defender within 1.52 m). Macrotransitions (four pass types, shot, turnover) are competing-risk hazards with spatial effects, plus a logistic shot model. Microtransitions (player movement) are modelled per player. Players are linked by a hierarchical conditional-autoregressive prior.
- **Key result (Theorem 2.1):** ν_t = Σ_c E[X | C_δt = c] P(C_δt = c | F_t).
- **Data:** STATS SportVU, 25 Hz, NBA 2013-14, 461 players, 10% held out.
- **Compute:** microtransition fits took up to about 18 h per player on 461 processors. Entry models used about 30.4 million rows, about 24 h per event type with 120 GB of RAM [GF7].
- **Validation:** out-of-sample log-likelihood of the transition models only. The true EPV curve is never observed [GF7].
- **Decision metrics:**
  - EPV-added (EPVA) = Σ(ν_te − ν_ts^r(ℓ)) per game against a league-average-player baseline. Top 2013-14: Durant +3.26 per game, James +2.96.
  - Shot satisfaction = the value of the shot minus the value of the best pass option at that moment [GF7].
- **Limitations stated by the authors:** pre-set plays violate the semi-Markov assumption; rebounds use constant team probabilities; turnover types are not separated [GF7].

**Critical limit for this project: the published EPV excludes transition and fouls.**

- POINTWISE (SSAC 2014, NBA 2012-13, 13 SportVU arenas) states: "For simplicity, in the analyses that follow, we focus on half-court possessions and ignore fouls" [GF8].
- The JASA version restricts to "possessions that do not include fouls" [GF7].
- So no published EPV value exists for numbers states, break phases or take fouls (A1). The framework transfers; the fitted numbers do not.
- DeepHoops (Sicilia, Pelechrinis and Goldsberry, arXiv:1902.08081, working paper, 2019) adds fouls as terminal actions in a deep-learning possession-value model. Its abstract does not say whether transition is covered [GF9].

**How to apply it to §3.4 and §8.** All steps below are [HEURISTIC] design choices built on the framework of [GF7].

1. **Break state.** At each 0.1 s, the state is: numbers label (A_play v D_back, or the advantage class +2 / +1 / even / −1); ball zone (backcourt y > 12.73 m; frontcourt outside the arc; inside the arc; paint); seconds since t0 (0–2, 2–4, 4–6, 6–8, 8–10, > 10 s); start type (A5 classes); handler speed class. Fouls (A1) and the half-court entry are terminal or absorbing states. This is unlike POINTWISE, which drops them.
2. **Coarsened chain.** Fit transition probabilities between states and to the end states (made 2, made 3, FT trip, turnover, half-court reset) by counting on MSU and opponent tracking. Rao-Blackwellise as in [GF7] once hazard models exist.
3. **Value function.** V(s) = expected points from state s. "Half-court reset" is valued at the team's own half-court PPP, which keeps the selection bias of §8.1 out of V.
4. **Shrinkage.** Shrink each V(s) toward the D-I start-type prior from A5 (for example steal 1.234 PPP, player DREB 1.087, made FG 1.050, 2025-26). The minimum count per state is set by the sample-size rule in A6.
5. **Passed-up break, value at stake (§8.5).** Stake = V_push(s) − V_pull(s). Here V_push is the value from s when the next action is a forward pass or a push dribble, and V_pull is the value when the next action is a pull-back (§2.2). Both are estimated in the same state bin, which is the analogue of EPVA and shot satisfaction. Report the stake beside each `passed_up` flag, so a pull-back with V_push − V_pull ≤ 0 is never called a mistake.
6. **Take foul (A1).** Stake = V(s at t_foul_stop) − realised points after the foul.

### A3. Shot-clock rule changes as natural experiments (adds to §5 clock conversions, §10.2, §10.7, §11.4)

**Rule timeline:**

- **2015 postseason trial.** NIT, CBI and CIT (75 games) used a 30 s clock and a wider restricted area. Pace rose by about 2 possessions per 40 min over expectation, adjusted efficiency by +0.6 points per 100, and adjusted scoring by about 2.4 points per game above the usual gap (Ken Pomeroy, republished 2 Apr 2015) [GF10].
- **2015-16.** The NCAA shot clock went from 35 s to 30 s [GF11].
- **2019-20.** The clock resets to 20 s "after a field goal attempt hits the rim and the offensive team rebounds the ball in the frontcourt". In the same season the D-I men's three-point line moved to the international distance, **6.75 m** (PROP, 5 Jun 2019) [GF14]. So **2019-20 has two simultaneous rule changes**, and the season was cut short in March 2020.

**Season-level effects** [calc-GF]:

| Season | D-I mean AdjT (T-Rank, possessions per 40 min) [GF13] | Derived mean possession length, 2400 / (2 × AdjT) (s) | Hoop-Math: transition share of all FGA, mean of teams [GF15] | Transition eFG / non-transition eFG (mean of teams) | Premium (pp) | Teams | MSU AdjT | MSU transition share / eFG |
|---|---|---|---|---|---|---|---|---|
| 2011-12 | 65.09 | 18.44 | 20.48% | 54.97 / 47.72 | 7.25 | 345 | 64.7 | 23.3% / 59.1% |
| 2012-13 | 64.60 | 18.58 | 20.71% | 54.58 / 47.34 | 7.24 | 347 | 63.1 | 23.9% / 56.8% |
| 2013-14 | 64.61 | 18.57 | 21.29% | 55.08 / 48.48 | 6.60 | 351 | 64.3 | 28.3% / 60.9% |
| 2014-15 (35 s) | 64.32 | 18.66 | 20.43% | 54.77 / 47.93 | 6.84 | 351 | 63.3 | 24.6% / 60.4% |
| **2015-16 (30 s)** | **68.20** | **17.60** | **20.91%** | 55.24 / 48.72 | 6.52 | 351 | 66.7 | 23.9% / 60.6% |
| 2016-17 | 68.12 | 17.62 | 20.75% | 55.69 / 49.45 | 6.24 | 351 | 66.8 | 23.9% / 60.3% |
| 2017-18 | 68.21 | 17.59 | 20.64% | 56.13 / 49.98 | 6.15 | 351 | 66.8 | 23.4% / 61.6% |
| 2018-19 | 67.66 | 17.74 | 22.17% | 55.38 / 49.73 | 5.65 | 353 | 67.1 | 28.6% / 63.0% |
| **2019-20 (20 s reset, 6.75 m arc)** | **68.30** | **17.57** | **23.40%** | 53.79 / 48.84 | 4.95 | 353 | 69.3 | 28.9% / 52.6% (see note) |
| 2020-21 | 68.16 | 17.61 | 23.56% | 54.12 / 49.24 | 4.88 | 347 | 68.4 | 24.8% / 49.1% |
| 2021-22 | 67.14 | 17.87 | 22.76% | 54.31 / 49.21 | 5.10 | 358 | 67.6 | 25.2% / 56.2% |
| 2022-23 | 67.13 | 17.88 | 22.42% | 54.55 / 49.74 | 4.81 | 363 | 64.6 | 20.0% / 57.3% |
| 2023-24 | 67.62 | 17.75 | 23.06% | 55.04 / 49.59 | 5.45 | 362 | 65.4 | 23.0% / 61.1% |
| 2024-25 | 67.50 | 17.78 | — (Hoop-Math stopped) | — | — | — | 67.6 | — |
| 2025-26 | 67.42 | 17.80 | — | — | — | — | 66.2 | — |

**Method.**

- AdjT is the unweighted mean of the last column of `barttorvik.com/{year}_team_results.csv` over all listed teams (345–365 teams). Torvik's year is the year the season ends.
- The MSU AdjT values match [M15] for 2023-24 (65.4), 2024-25 (67.6) and 2025-26 (66.2).
- The derived possession length assumes both teams share 2,400 s of game time and ignores dead time between possessions. It is a proxy, not KenPom's APL.
- Hoop-Math values are unweighted means of team rows on the archived offense leaderboards (column "%shots in Transition" and the two eFG columns). Snapshot "Last updated" stamps: 13 Dec 2013 (2011-12), 14 Dec 2013 (2012-13), 10 Nov 2014, 7 Apr 2015, 10 Jul 2016, 4 Apr 2017, 3 Apr 2018, 9 Apr 2019, **14 Mar 2020** (season cut short), 6 Apr 2021, 6 Apr 2022, 5 Apr 2023 and 10 Apr 2024.
- MSU's 2022-23 and 2023-24 rows match the earlier §10.7 values [V9][V11].
- MSU's 2019-20 row shows the same eFG (52.6%) for transition and non-transition. That is a likely leaderboard artefact; check it on the archived team page before use.

**Cross-checks on the 35 s → 30 s change:**

- NCAA statistics through mid-March 2016 [GF11]: possessions per game 65.78 → 69.93 (+6.3%); points per possession 1.0282 → 1.0439; 3PA per team per game +10% (to 20.5).
- KenPom-based team data [GF12]: 64.4 → 68.2 possessions, "the highest since 2002".
- These agree with the T-Rank means above (+3.88 possessions per 40 min, +6.0%).
- The brief's KenPom APL figures (18.4 s → 17 s, and tempo 64.8 → 70) were **not opened**: kenpom.com returned 403. They stay **unverified**. The derived proxy (18.66 s → 17.60 s) is consistent with them.

**What the changes did to transition** (descriptive, single change points, no control group):

1. **35 s → 30 s.** Tempo rose 6.0%, but Hoop-Math's transition share of FGA rose only +0.48 pp (20.43% → 20.91%). The extra possessions came from shorter **half-court** possessions, not from more breaks. The transition eFG premium was unchanged (6.84 → 6.52 pp).
2. **2019-20 (20 s reset and 6.75 m arc).** Tempo +0.64 possessions; transition share +1.23 pp (22.17% → 23.40%). The share had already risen +1.53 pp in 2018-19 with no clock change. The 2019-20 change cannot be separated from the arc move or from the shortened season. From 2019-20 the premium settled at about 4.8–5.5 pp, down from about 6.2–7.2 pp before.
3. **Three-point shooting in transition.** Synergy NCAA data (Hoop Vision) show transition threes rising from 27% of transition FGA (2009-10) to 35% (2023-24, as of Feb 2024), with 3P% at about 35% in both years (35.8% in 2014, 35.5% in 2019) [GF20]. Era comparisons of transition eFG therefore mix shot mix with efficiency.

**Consequences for clock-based definitions (§5.1, §11):**

- **Hoop-Math (D2) and VU Hoops (D15)** time from the possession start, so their meaning does not change across clock eras. Their base rates do (table above). Always compare MSU with the **same-season** D-I distribution (percentile or z-score), never with raw shares from another era.
- **FastScout (D3), "first 10 s of the shot clock".** On the 35 s clock that is a reading ≥ 25 s; on the 30 s clock, ≥ 20 s. From 2019-20, a chance after an offensive rebound that hits the rim starts at a reading of 20 s. Under a reading-based rule, such a chance can never be "in the first 10 s"; under an elapsed-time rule (≤ 10 s after the reset) it can. Keep both versions (§12 Q16). For seasons before 2015-16, store the 35 s reading thresholds.
- **NBA 6 s proxy (D20):** a reading ≥ 24 s on the 30 s clock, ≥ 29 s on the 35 s clock.
- **§11.4 new reason:** cross-season comparisons for MSU (for example 2013-14, 28.3% share, vs 2023-24, 23.0%) span two rule eras. Use season-relative ranks: 14th of 351 vs 177th of 362 [calc-GF; ranks of team share values on the leaderboards].

### A4. Transition definitions used by current NCAA data providers (adds rows D23–D27 to §5.1)

| # | Owner | Unit counted | Start events | Time cutoff | State cutoff | Exclusions / notes | Known efficiency | Status |
|---|---|---|---|---|---|---|---|---|
| D23 | **CBB Analytics** (cbbanalytics.com, Canova Analytics) | **Chance**: an offensive rebound extends the possession but starts a new chance. PPP is "typically 10-20% higher" than points per chance [GF17] | Possession and chance start types from play-by-play. 20–30% of turnovers typed as live ("dribbling", "ballhandling", "badpass", "lostball") still stop the clock, which cuts start-type accuracy by 1–5% [GF17] | **Not published.** Classification "combines the fast break tag from the play-by-play data with our own analysis of possession length" [GF17] | None stated | Three mutually exclusive chance classes: half court / transition / putback (putback = chance after an OREB). Metrics TR FREQ, TR PPC, TR PTS, 2P% in TR, 2PA in TR, HC PPC, PB PPC [GF16]. "Jailbreak steal" = a steal that led to a transition bucket at the rim within 4 s [GF16]. Shot clock estimated from event times: about 3 s lag after a made basket, 0–2 s after rebounds, kicked balls not tracked; most estimates within 0–2 s of film [GF17]. Data: Genius Sports LiveStats only; games tagged in StatCrew or PrestoStats have no play-by-play-derived stats [GF17] | Not public | Glossary and FAQ verified (browser, 2026-10-18). Fast-break cutoff **unverified** |
| D24 | **ShotQuality** | Shot (play type attached to each shot) | Not stated | Not stated | "A play type describes the events before the shooting motion begins"; transition defenses are "less organized … without defined matchups" [GF18] | Transition is a feature of the shot-make model ("up to 100 variables"). Location data built in-house "using computer vision and AI" [GF18] | Jump shots 2015–2023: transition 36% vs non-transition 34% (NCAAM); 34% vs 32% (NCAAW); 37% vs 36% (NBA) [GF18] | Definition **unverified** (not published) |
| D25 | **EvanMiya** | — | — | — | — | No public transition metric or definition on evanmiya.com or in the blog archive [GF19] | — | **Unverified** (nothing published) |
| D26 | **Synergy, NCAA** | As D1 | As D1 | As D1 (none) | As D1 | Hoop Vision uses Synergy NCAA data for transition three-point rates (A3) [GF20] | Transition threes 27% → 35% of transition FGA (2010 → 2024); 3P% about 35% [GF20] | Framework as D1 [V1]; NCAA logging wording login-gated (**unverified**) |
| D27 | **Official box via ESPN** (`fastBreakPoints` in the public site API box score) | Points | As D7 | As D7 | As D7 | Same scorer's tag as D7 and D13. CBB Analytics: "Game taggers do not tag fast breaks consistently" [GF17]. Reachable without a key at `site.api.espn.com/.../summary?event={id}` [GF21] | MSU 2025-26 in 33 parsed games: 15.6 per game (official season releases: 16.4 / 16.2 [M14][M36]) [calc-GF] | Verified [GF21] |

**Correction to [M4] (§9.2, 2025-26 row).** Re-opened 2026-10-18 [GF32]. The Spartan Avenue sentence "Michigan State is in the 100th percentile in terms of transition field goal percentage at an astounding 68.9%" carries **no source**. The article credits CBBanalytics.com only in the preceding paragraph, about UConn's half-court defense (37.8%). Attributing the 68.9% to CBB Analytics is therefore an inference. If it is CBB Analytics, it is FG% on **transition chances**, classified by the D23 rule (scorer's tag plus possession length), which is not Hoop-Math's 10 s rule. Mark the provenance of 68.9% as **unverified** until it is read from a CBB Analytics MSU page, which requires a login.

### A5. NCAA Division I points per possession by start type (closes the §6.2 gap)

**Possession-parsing tools checked:**

| Tool | Data | Possession logic | Status |
|---|---|---|---|
| ncaahoopR (Benz) | ESPN play-by-play | `get_pbp_game(..., extra_parse = TRUE)` will "attempt possesion parsing" [sic]; start rules not documented in the README; fields include `secs_remaining`, `play_length` [GF22] | Rules **undocumented** |
| bigballR (Flancer) | stats.ncaa.org | Lineups and player stats; no possession rules in the README; the README says site changes left the package "unable to perform previous functions" and there will be "no additional updates" [GF23] | Unmaintained |
| CollegeBasketballData (CBBD) | ESPN-derived | `PlayInfo` has no possession id, start-type or transition field (checked in the saved OpenAPI spec [V32]); free API key required [GF24] | Not usable without a key (no account created) |
| pbpstats | NBA only | [V41] | Not applicable |

None documents NCAA start rules, so this pass wrote its own parser for ESPN's public play-by-play (`site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={id}`; game list from the `scoreboard?groups=50` endpoint, completed games, 1 Nov – 10 Apr) [GF21].

**Parser rules** [calc-GF], applied in sequence order:

1. A possession belongs to the team whose ownership events (FGA, FTA, offensive rebound, turnover) follow. Substitutions, timeouts and fouls do not change possession.
2. A new possession starts at:
   - a **steal** (`steal`, t0 = steal time);
   - a **defensive rebound** after a missed FG (`dreb_fg`; the `_team` suffix when credited to the team) or after a missed FT (`dreb_ft`);
   - a **dead-ball team rebound** credited to the non-shooting team (`*_dead`; dead-ball rebounds credited to the shooting team between free throws are ignored);
   - the first ownership event after a **made FG** (`made_fg`), a **made last FT** (`made_ft`), a **turnover with no steal** (`dead_to`) or the **start of a period** (`period_start`).
   For these starts, t0 is the time of the ending event (the made basket, made FT or turnover), not the later inbound. Free throws by the scoring team at the same clock second (and-ones) stay in the scoring team's possession.
3. Free throws from a technical foul are excluded, as Inpredictable does [V34].
4. Offensive rebounds stay inside the possession (KenPom/pbpstats convention [V28][V41]).
5. Game QA: a game is kept ("good") when each team's parsed points are 0–3 below its official score and the two teams' possession counts differ by ≤ 4. Kept: 6,142 of 6,275 parsed games in 2025-26 (6,300 listed); 5,437 of 6,135 in 2024-25 (6,292 listed).
6. "Early shot" = first FGA ≤ 10 s after t0, a Hoop-Math-like timing (not Hoop-Math's exact rule, which counts initial FGA only and has its own start set).

**Checks.**

- 2025-26: D-I PPP 1.079; 69.3 possessions per team-game.
- MSU's parsed 2025-26 OR% (38.2) and opponent OR% (22.0) match T-Rank (37.8 / 22.4) [M15].
- Fast-break points per game match independent reports for Illinois (5.6 vs 6.14 [M24]) and Indiana (7.2 vs 7.25 [M31]).

**D-I men, 2025-26** (6,142 games; possessions starting in the last 60 s of a period excluded; n = 799,213; mean 1.087 PPP) [calc-GF]:

| Start | n | Share of possessions | PPP | 95% CI ± | First FGA ≤ 10 s (share of possessions with an FGA) | PPP, early-shot possessions | PPP, other possessions |
|---|---|---|---|---|---|---|---|
| Steal (live-ball TO) | 78,037 | 9.8% | **1.245** | 0.008 | 65.9% | 1.519 | 0.969 |
| DREB of missed FG, player | 231,347 | 28.9% | **1.103** | 0.005 | 52.3% | 1.333 | 0.955 |
| DREB of missed FG, team or dead ball | 20,790 | 2.6% | 1.042 | 0.016 | 11.1% | 1.276 | 1.022 |
| DREB of missed FT (all) | 29,805 | 3.7% | 1.061 | 0.013 | 19.1% | 1.303 | 1.023 |
| Turnover without a steal (dead-ball proxy) | 57,311 | 7.2% | **1.076** | 0.010 | 14.7% | 1.383 | 1.037 |
| Made FG | 284,001 | 35.5% | **1.049** | 0.004 | 7.2% | 1.291 | 1.035 |
| Made FT (last) | 82,399 | 10.3% | **1.060** | 0.008 | 10.4% | 1.340 | 1.037 |
| Period start | 12,651 | 1.6% | 1.052 | 0.020 | 8.5% | 1.379 | 1.028 |
| Unclassified | 2,872 | 0.4% | 0.924 | 0.040 | — | — | — |

**D-I men, 2024-25** (5,437 games; same exclusion; n = 704,204; mean 1.064):

| Start | Steal | DREB FG, player | DREB FG, team/dead | DREB FT | Dead-ball TO proxy | Made FG | Made FT | Period start |
|---|---|---|---|---|---|---|---|---|
| PPP | 1.214 | 1.077 | 1.031 | 1.033 | 1.048 | 1.030 | 1.039 | 1.029 |
| Early-shot rate | 65.5% | 51.9% | 11.0% | 19.0% | 14.2% | 6.8% | 10.3% | 9.0% |

**Reading the tables:**

- Steal starts are worth about +0.14 PPP more than player-DREB starts and about +0.20 more than made-FG starts, in both seasons. Player-DREB starts beat made-FG starts by about +0.05.
- Dead-ball turnover starts score like made-basket starts, not like steals. This supports keeping live and dead turnovers as separate classes (§6.1).
- Team and dead-ball DREBs score below player DREBs (1.042 vs 1.103), which is consistent with the stoppage killing the break.
- Within every start type, possessions with an early shot score far more (about 1.29–1.52) than the rest (about 0.95–1.04). This split is **selection-biased** in the same way as §8.1, because pushes that fail to get an early shot fall into "other". It is not the causal value of pushing.
- Including the last 60 s of periods changes PPP by ≤ 0.06 (full table: steal 1.234, player DREB 1.087, made FG 1.050, made FT 1.060).
- The CI half-width is 1.96 × SD / √n, with the SD of possession points about 1.17 (all possessions) and about 1.20 (early-shot possessions).

**Caveats:**

1. ESPN does not type turnovers, so "turnover without a steal" includes some live-ball losses with no steal credited. CBB Analytics reports the opposite error too: 20–30% of live-typed turnovers stop the clock [GF17].
2. Game-clock resolution is 1 s, except tenths in the final minute.
3. t0 for made-basket starts is the basket time; the inbound adds about 3 s by CBB Analytics' estimate [GF17].
4. 2024-25 kept fewer games (87%) than 2025-26 (98%), most likely from ESPN feed gaps (not investigated).
5. The scripts (`parse.py`, `analyze.py`, `extra.py`, `bigten.py`) live in this session's scratchpad (`…/pbpwork/`), which is not durable. Add them to the repo when building starts, if Aldemir wants the numbers reproducible.

**Older public references for comparison:**

- APBRmetrics forum table (Mike G, 4 Oct 2011; league and season not stated, method linked to an off-site thread) [GF25], points per 100 possessions by possession start: steal 126.8; non-steal turnover 111.6; DREB after a missed 2 112.5; DREB after a missed 3 107.3; FT made 108.4; 2P FG made 107.0; 3P FG made 106.9; start of quarter 104.7; FT missed with DREB 103.2; average 110.4. The same thread quotes a separate study ("if a play starts with a steal … from 0.83 to 1.04"). This is the source of the "126.8" in the brief.
- TeamRankings, 16 NCAA tournament games: live-ball TO 1.28 PPP vs dead-ball TO 0.97 vs non-turnover 1.02. Seen only in a search summary (page 403): **unverified**.

### A6. Expected points by numbers advantage: logged as an evidence gap (adds to §3.4, §8.2, §10.5)

**What sources give:**

| Evidence | Measure | Value | Status |
|---|---|---|---|
| Gerani et al. 2004: EuroBasket 2001 + Greek A1 2001-02, 50 games (congress abstract; same record as [P20], re-opened) [GF26] | Scoring rate (basket) by situation | 1v0 90.9%; 4v2 80%; 3v1 79.4%; **3v2 75.3%**; **1v1 73.5%**; **2v1 73.2%**. Frequency: 4v3 13.6%, 1v1 13.2%, 1v0 11.6%, 3v2 10.9%, 3v3 10.4%. No counts given | Abstract only; adds 3v2, 1v1, 2v1 and the frequencies to the three rates already in §2.2 |
| Conte et al. 2017, Italy, 398 fast breaks [P2] (Table 3 re-opened) | Success by numerical superiority vs equal numbers [calc-GF: P(success \| class) = overall success × share of successes in that class ÷ share of all breaks in that class] | Elite: superiority 68.7% vs equal 56.4%. Sub-elite: 62.0% vs 56.7%. Superiority OR 1.70 (0.98–2.96), p = 0.060 elite; 1.25 (0.68–2.30) sub-elite; not significant in multivariate models | Journal |
| Hoopsalytics blog, San Francisco 2021-22 (Coach Bill, 18 Nov 2022) [GF27] | Points per transition vs set possession (manually charted) | 1.27 vs 1.16; no numbers breakdown; sample not stated | Vendor blog (weak) |
| Refoyo et al. 2009 (Beijing 2008, 294 fast breaks) and Tavares & Gomes 2003 (1999 junior worlds, 21 games) [GF33] | Result vs duration, area and opposition; "1x1" the most used structure | No success or PPP by attacker–defender count in the abstracts | Abstracts only |

**Not found:** points per possession by attacker–defender count (2v1, 3v2, 4v3, even) in NCAA or NBA data. CTG and Synergy do not publish such splits openly. The coaching rules of thumb (2v1 ≈ 1.5 PPP, 3v2 ≈ 1.2) remain **unsourced** and must not be used as thresholds. A calculator page claiming 1.15–1.20 PPP for fast breaks vs about 1.07 half-court was seen only in a search summary (**unverified**, no source given).

**Plan to estimate it from MSU tracking** [HEURISTIC]:

1. **Unit.** Every possession with an opportunity flag (§8.2). Record the numbers label at t_cross_half and at t_first_shot, plus the maximum advantage reached.
2. **Classes.** Collapse to advantage classes (≥ +2, +1, even, ≤ −1). Keep the full labels (2v1, 3v2, …) as sub-rows.
3. **Sample size.** With SD ≈ 1.20 points per early possession [calc-GF, A5], a ±0.10 PPP 95% CI needs n ≈ (1.96 × 1.20 / 0.10)² ≈ **553** possessions per class. ±0.20 needs about 138. One MSU season of tracking will not reach ±0.10 for rare classes, so pool MSU and opponent possessions (both directions). Shrink each class toward the start-type prior (A5) with a hierarchical model. Report CIs, never point values alone.
4. **Outcomes.** PPP; P(FGA at the rim); P(turnover); P(stopped by foul) (A1). Fit P(score | advantage class, seconds since t0, start type) as the §3.4 "fitted break value" and as the V(s) inputs of A2.

### A7. Transition profiles for the remaining Big Ten programs (adds to §9.6; covers all 18 for comparison)

**Season 2025-26, all completed games in the ESPN D-I feed** (including the postseason; "good" games only, A5 QA). Sources: ESPN public play-by-play and box scores [GF21], T-Rank AdjT [GF13]. All values [calc-GF].

**Columns:**

- *FBP/G*: official fast-break points per game, for and against.
- *OR%*: ORB / (ORB + opponent DRB).
- *Early-shot rate*: share of possessions with an FGA whose first FGA came ≤ 10 s after t0.
- *Push after DREB / after make*: the same rate, restricted to possessions starting from a player DREB, or from a made FG or made last FT. "Off" is the team's own rate; "allowed" is its opponents'.
- *Steal starts, own / opp*: share of the team's possessions that began with its own steal / share of the opponents' possessions that began with a steal (the team's live-ball turnovers).
- *Take-foul candidates*: A1 rule; "committed" = by this team's defense.

| Team | G | AdjT (rank of 365) | Poss/G | FBP/G for / against | OR% / opp OR% | PPP off / def | Early-shot rate (off) | Push after DREB, off / allowed | Push after make, off / allowed | Steal starts, own / opp | Take-foul candidates committed / drawn per G |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Illinois | 37 | 65.4 (289) | 66.0 | 5.6 / 7.9 | 39.2 / 26.7 | 1.260 / 1.044 | 22.8% | 39.4 / 53.1 | 7.6 / 9.4 | 5.6 / 8.3 | 0.30 / 0.27 |
| Indiana | 32 | 66.3 (244) | 66.8 | 7.2 / 7.7 | 26.9 / 29.3 | 1.169 / 1.076 | 22.6% | 45.0 / 47.7 | 5.9 / 7.4 | 7.0 / 8.2 | 0.47 / 0.38 |
| Iowa | 37 | 62.5 (363) | 62.8 | 7.2 / 6.1 | 30.2 / 29.2 | 1.185 / 1.053 | 17.9% | 27.6 / 45.9 | 4.6 / 7.1 | 10.9 / 8.1 | 0.38 / 0.30 |
| **Maryland** | 33 | 66.5 (237) | 66.8 | 6.1 / 11.6 | 33.8 / 29.1 | 1.041 / 1.143 | 25.5% | 50.1 / 49.8 | 6.8 / 11.5 | 7.1 / 9.5 | 0.48 / 0.55 |
| Michigan | 37 | 71.1 (21) | 70.9 | 11.9 / 5.4 | 34.9 / 27.8 | 1.231 / 0.972 | 37.1% | 62.0 / 50.5 | 14.4 / 8.3 | 8.0 / 8.9 | 0.24 / 0.70 |
| Michigan State | 33 | 66.2 (251) | 66.8 | 15.6 / 9.0 | 38.2 / 22.0 | 1.180 / 1.004 | 31.3% | 49.3 / 39.9 | 16.0 / 7.3 | 7.6 / 10.2 | 0.52 / 0.45 |
| **Minnesota** | 33 | 62.6 (362) | 63.3 | 7.7 / 5.5 | 26.8 / 29.5 | 1.095 / 1.072 | 22.5% | 43.8 / 36.8 | 3.0 / 5.0 | 10.0 / 8.7 | 0.42 / 0.48 |
| Nebraska | 35 | 66.6 (227) | 67.2 | 6.2 / 5.3 | 26.7 / 27.4 | 1.144 / 0.981 | 27.7% | 44.6 / 36.8 | 8.0 / 8.7 | 10.6 / 7.6 | 0.26 / 0.37 |
| **Northwestern** | 34 | 65.2 (297) | 65.1 | 11.4 / 7.6 | 28.1 / 34.7 | 1.122 / 1.106 | 25.2% | 55.2 / 44.6 | 6.3 / 6.1 | 8.9 / 7.4 | 0.24 / 0.24 |
| **Ohio State** | 32 | 66.1 (252) | 66.8 | 6.7 / 7.1 | 30.7 / 29.9 | 1.190 / 1.086 | 25.3% | 51.2 / 45.6 | 7.4 / 8.2 | 6.9 / 8.2 | 0.41 / 0.44 |
| **Oregon** | 31 | 66.0 (260) | 66.7 | 7.0 / 10.3 | 32.5 / 32.3 | 1.052 / 1.108 | 24.0% | 35.3 / 44.4 | 9.8 / 9.3 | 9.1 / 10.4 | 0.61 / 0.42 |
| **Penn State** | 32 | 67.6 (173) | 66.8 | 10.9 / 9.8 | 25.9 / 31.1 | 1.101 / 1.186 | 27.8% | 57.2 / 45.8 | 8.6 / 7.8 | 10.4 / 8.7 | 0.62 / 0.22 |
| Purdue | 38 | 64.4 (328) | 64.8 | 7.5 / 6.4 | 36.3 / 26.7 | 1.259 / 1.092 | 23.4% | 48.1 / 47.3 | 3.1 / 7.1 | 8.4 / 8.1 | 0.37 / 0.42 |
| **Rutgers** | 34 | 67.0 (208) | 67.4 | 10.7 / 10.5 | 29.7 / 32.8 | 1.046 / 1.122 | 25.1% | 50.7 / 45.8 | 7.5 / 8.2 | 9.0 / 8.3 | 0.18 / 0.38 |
| **UCLA** | 36 | 64.9 (312) | 65.8 | 9.0 / 7.9 | 31.0 / 33.3 | 1.171 / 1.074 | 24.1% | 44.2 / 45.8 | 6.2 / 9.6 | 10.1 / 7.3 | 0.25 / 0.44 |
| **USC** | 31 | 70.8 (24) | 71.3 | 10.1 / 10.3 | 33.5 / 31.5 | 1.095 / 1.090 | 29.9% | 52.0 / 50.6 | 11.2 / 8.5 | 8.9 / 10.2 | 0.61 / 0.52 |
| **Washington** | 32 | 67.1 (201) | 68.4 | 10.8 / 7.3 | 34.6 / 28.6 | 1.124 / 1.074 | 28.1% | 53.1 / 49.6 | 9.1 / 7.7 | 8.4 / 8.3 | 0.22 / 0.53 |
| Wisconsin | 35 | 68.8 (104) | 69.5 | 10.7 / 8.8 | 29.1 / 28.2 | 1.193 / 1.101 | 27.3% | 51.0 / 54.0 | 7.8 / 8.8 | 8.0 / 6.7 | 0.23 / 0.51 |

Bold = the ten programs that §9.6 marked as not researched. D-I 2025-26 references for the same definitions, all possessions as in this table [calc-GF, A5]: early-shot rate after a player DREB 52.3%; after a made FG or made last FT combined 9.8% (made FG alone 7.9%, made FT alone 15.9%); steal starts 9.7% of possessions.

**Patterns for the per-game report (§11.3).** Descriptive, one season; each item is a test target, not a conclusion.

- **MSU is the conference's push-after-make outlier.** Its offense took the first shot within 10 s after 16.0% of opponents' made baskets and FTs. That is about 1.6 times the D-I rate for the same definition (9.8%) and above Michigan (14.4%), despite a slow AdjT (251st). It also has the conference's lowest opponent OR% (22.0%), and its opponents pushed after only 39.9% of their DREBs; only Minnesota and Nebraska (36.8%) allowed fewer. This matches the §9.4 "send 4, PG back" description with a strong get-back.
- **Teams that rarely push after makes:** Minnesota pushed only 3.0% itself and allowed 5.0% (the conference low); Purdue pushed 3.1% and allowed 7.1%; Iowa pushed 4.6%.
- **Transition-vulnerable defenses** (high allowed push rate or opponent fast-break points): Maryland (11.6 opponent FBP/G; 11.5% allowed push after makes; 9.5% of opponent possessions started with a Maryland live-ball turnover), Oregon (10.3 opponent FBP/G; 10.4% opponent steal starts), USC (10.3), Rutgers (10.5), Penn State (9.8; def PPP 1.186, the conference's worst).
- **Running teams among the ten:** USC (AdjT 24th, early-shot rate 29.9%, push after make 11.2%); Northwestern (11.4 FBP/G, 55.2% push after DREB); Penn State (57.2% push after DREB, 10.4% own steal starts); Washington (10.8 FBP/G, 53.1% push after DREB).
- **Glass vs get-back trade-off:** Washington (OR% 34.6) and USC (33.5) crash and still push. Northwestern (opp OR% 34.7) and UCLA (33.3) give up the most offensive rebounds of the ten.
- **Take-foul candidates committed:** highest for Penn State (0.62 per game), USC (0.61), Oregon (0.61) and MSU (0.52); lowest Rutgers (0.18). Because of the A1 limits, this measures "early side-out fouls on live starts", not proven take fouls.

**Qualitative notes, sourced** (only where a page was opened):

- **Ohio State (Jake Diebler).** Pre-season 2025-26: "It's important for us to play with more pace and more versatility and in less called sets, more free-flowing concepts" [GF28]. As interim coach in 2023-24: "Part of playing with pace is everybody has to get out and run, too". Ohio State scored 5.8 fast-break points per game before the Michigan game (333rd of 362), and 9.3 per game in Diebler's first four games [GF29]. The 2025-26 data above show only a middling push profile (25.3% early-shot rate; 6.7 FBP/G).
- **Rutgers (Steve Pikiell), 2023-24 context.** "The quicker you shoot the ball, the more you're on defense" (Nov 2023). Rutgers' offensive APL fell to 15.6 s (45th) through five games, from 17.5 s (162nd) in 2022-23 (KenPom, as reported) [GF30].
- **Maryland (Buzz Williams, first season 2025-26).** On guard Myles Rice: "His speed changes our team, whether we're trying to play fast or not". In the 7 Nov 2025 loss, Georgetown's full-court press and transition built an 11-0 start [GF31]. This fits Maryland's high allowed push-after-make rate above.
- **UCLA, Oregon, USC, Minnesota, Northwestern, Penn State, Washington:** no 2025-26 coach statement on transition was opened to source standard in this pass. Their profiles rest on the computed table only (**gap**). A USC quote ("He's going to force us to run more", Musselman) appeared only in a search summary (**unverified**).

### A8. Cross-references: where the main sections should point to these additions

| Section | Add |
|---|---|
| §3.3 | Phase "Foul to stop" (A1) |
| §3.4 | Shrink the fitted break value toward the A5 start-type PPP; build V(s) as in A2; sample-size rule from A6; `tr_nba_tso` and `tr_nba_clear_path` (A1) |
| §5.1 | Rows D23–D27 (A4). Clock-era note for D2, D3, D20 (A3) |
| §6.2 | The "Gap" line is now closed by A5 (computed D-I PPP by start type, 2024-25 and 2025-26) |
| §8.4 | Category "Fouled (stopped by foul)" (A1) |
| §8.5 | "Value at stake" = V_push(s) − V_pull(s) (A2) |
| §9.2 / [M4] | Provenance of 68.9% downgraded to unverified (A4 correction) |
| §9.6 | Full 18-team table (A7); the "not researched" row is now covered by computed data, with qualitative gaps listed |
| §9.8 | Rule "Take the foul when beaten" (A1) |
| §10.7 | Era-relative ranks for MSU transition share (A3) |
| §11.3 / §11.4 | Row "Breaks stopped by foul"; NBA vs NCAA foul rules; shot-clock eras (A1, A3) |
| §12 | New open questions: (17) Which take-foul proxy (distance from the ball, timing window) defines `foul_take_candidate` in tracking? (18) Should the custom ESPN parser (A5) go into the repo as the reference play-by-play possession builder? (19) Seasons before 2015-16: store 35 s shot-clock thresholds for FastScout and the NBA 6 s proxy, or exclude those seasons from clock-based labels? |

### Sources for the additions (all opened 2026-10-18)

| Key | URL | What it confirmed |
|---|---|---|
| GF1 | https://pr.nba.com/transition-take-foul-nba-play-in-tournament-approval | Take-foul definition; "transition scoring opportunity" wording; penalty; last-2-minute exemption; G League experiment since 2018-19 |
| GF2 | https://www.nba.com/news/nba-board-of-governors-approves-heightened-penalty-for-transition-take-foul | Same rule, effective 2022-23; scope (immediately after a change, off-ball, shooting foul excluded) |
| GF3 | https://official.nba.com/rule-no-12-fouls-and-penalties/ | Clear-path conditions (ball ahead of the tip of the backcourt circle, no defender ahead, control or pass released); 2 FT + possession; no take-foul text on the page |
| GF4 | https://www.theringer.com/nba/2022/11/10/23450776/nba-take-fouls | 1.89 points per take foul (1.08 + 0.81); 0.32 (2017-18), 1.4 (2021-22), 0.33 (early 2022-23) take fouls per game; 14.4 vs 13.1 fast-break points per game; 1.26 points per transition play (CTG). The brief's …/23450356/… URL returned 404 |
| GF5 | https://forum.officiating.com/818222-post11.html | NCAA Flagrant 1 definition and examples as quoted on 30 Jan 2012 (current wording unverified) |
| GF6 | https://arxiv.org/abs/1408.0777 | Cervone, D'Amour, Bornn, Goldsberry; JASA 111(514), 2016; DOI 10.1080/01621459.2016.1141685; versions |
| GF7 | https://ar5iv.labs.arxiv.org/html/1408.0777 | EPV definition, multiresolution model, Theorem 2.1, data (2013-14, 25 Hz, 461 players), foul exclusion, compute, EPVA and shot satisfaction, limitations |
| GF8 | https://code.garrettmills.dev/Archives/papers-we-love_papers-we-love/raw/branch/main/sports_analytics/2014-ssac-pointwise-predicting-points-and-valuing-decisions-in-real-time.pdf | POINTWISE (SSAC 2014): "we focus on half-court possessions and ignore fouls"; 2012-13 data from 13 arenas (PDF text extracted with pdftotext) |
| GF9 | https://arxiv.org/abs/1902.08081 | DeepHoops (Sicilia, Pelechrinis, Goldsberry), working paper 2019; terminal actions include fouls |
| GF10 | https://deadspin.com/how-has-the-ncaas-new-30-sec-shot-clock-worked-this-pos-1695275647/ | Pomeroy on the 2015 NIT/CBI/CIT 30 s trial: 75 games, about +2 possessions per 40 min, +0.6 per 100 |
| GF11 | https://www.cbssports.com/college-basketball/news/rule-changes-have-made-college-basketball-fun-to-watch-once-again | 2014-15 vs 2015-16 (to mid-March 2016): possessions per game 65.78 → 69.93; PPP 1.0282 → 1.0439; 35 → 30 s |
| GF12 | http://www.r-bloggers.com/2018/11/ncaa-basketball-clustering-conferences | KenPom team data: 64.4 → 68.2 possessions (2015 → 2016), highest since 2002 |
| GF13 | https://barttorvik.com/2016_team_results.csv (same pattern for 2010–2026) | AdjT for every D-I team by season; means computed [calc-GF] |
| GF14 | https://www.si.com/college/2019/06/05/mens-college-basketball-three-point-line-moved-international-distance | 20 s reset after a rim-touching FGA and offensive rebound; arc moved to the international distance (6.75 m) for 2019-20 |
| GF15 | Hoop-Math offense leaderboards (Wayback; fetched with the `id_` flag): http://web.archive.org/web/20250712025357/http://hoop-math.com/leader_o2012.php ; …/20250713174911/…leader_o2013.php ; …/20250720225855/http://www.hoop-math.com/leader_o2014.php ; …/20250804095341/…leader_o2015.php ; …/20250804085446/…leader_o2016.php ; …/20250817090430/…leader_o2017.php ; …/20250713164201/…leader_o2018.php ; …/20250825051802/https://hoop-math.com/leader_o2019.php ; …/20251112143641/https://hoop-math.com/leader_o2020.php ; …/20250716074141/http://www.hoop-math.com/leader_o2021.php ; …/20250621043356/http://www.hoop-math.com/leader_o2022.php ; …/20250809205326/…leader_o2023.php ; …/20240915065210/https://hoop-math.com/leader_o2024.php | Team transition share of FGA and transition / non-transition eFG, 2011-12 to 2023-24; "Last updated" stamps as listed in A3 |
| GF16 | https://cbbanalytics.com/resources/glossary | Chance classes half court / transition / putback; TR FREQ, TR PPC, 2P% in TR; Jailbreak steals (≤ 4 s, rim) |
| GF17 | https://cbbanalytics.com/resources/faq | Chances vs possessions; LiveStats source; start-type accuracy limits; shot-clock estimation; transition = fast-break tag combined with possession-length analysis |
| GF18 | https://shotqualitybets.com/stats-explained | ShotQuality play types incl. Transition; jump-shot % transition vs not; up to 100 variables; in-house CV location data |
| GF19 | https://evanmiya.com/ ; https://blog.evanmiya.com/archive | No transition metric or definition published (negative check) |
| GF20 | https://hoopvision.substack.com/p/the-transition-three | Synergy NCAA: transition 3PA share 27% (2010) → 35% (Feb 2024); 3P% about 35% |
| GF21 | https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event=401827219 (and the `scoreboard?dates=YYYYMMDD&groups=50&limit=500` endpoint) | Public play-by-play and box score (incl. `fastBreakPoints`) used for A1, A5 and A7 [calc-GF] |
| GF22 | https://github.com/lbenz730/ncaahoopR | ESPN play-by-play scraper; `extra_parse` "attempt possesion parsing" [sic]; rules not documented |
| GF23 | https://github.com/jflancer/bigballR | stats.ncaa.org scraper; no longer maintained |
| GF24 | https://api.collegebasketballdata.com/docs | CBBD requires a free API key (not created) |
| GF25 | https://apbr.org/metrics/viewtopic.php?p=2259 | Points per 100 possessions by possession start (Mike G, 2011; league and season not stated) |
| GF26 | https://lida.sport-iat.de/twm/Record/4011293?lng=en | Gerani et al. 2004 abstract: success and frequency by numbers situation (same record as P20) |
| GF27 | https://blog.hoopsalytics.com/?p=357 | San Francisco 2021-22: 1.27 transition vs 1.16 set PPP; charting method |
| GF28 | https://pressprosmagazine.com/2025/10/25/diebler-counting-on-experience-to-play-fast-raise-the-bar/ | Diebler pace quote (Oct 2025) |
| GF29 | https://elevenwarriors.com/ohio-state-basketball/2024/03/145882/behind-turnover-creation-fast-pace-ohio-state-finds-22-2-edge-in-fastbreak-points-during-dominant-win-over-michigan | Ohio State fast-break points per game 5.8 (333rd) vs 9.3 under interim Diebler; quotes |
| GF30 | https://guardenstate.substack.com/p/why-the-fast-break-may-set-rutgers-apart | Rutgers 2023-24 APL 15.6 s vs 17.5 s; Pikiell quote |
| GF31 | https://dbknews.com/2025/11/07/maryland-mens-basketball-score-recap-result-georgetown | Buzz Williams quote; Georgetown press and transition 11-0 start |
| GF32 | https://spartanavenue.com/the-biggest-key-to-beating-uconn-is-always-in-tom-izzo-s-gameplan-01kmkajksep6 | Re-opened: the 68.9% sentence has no source attribution (A4 correction) |
| GF33 | https://archives.rpd-online.com/article/view/673.html ; https://lida.sport-iat.de/dbb/Record/4008300 | Refoyo et al. 2009 and Tavares & Gomes 2003 abstracts (no numbers-specific success rates) |

Also re-opened in this pass: [P2] https://pmc.ncbi.nlm.nih.gov/articles/PMC5424458/ (Table 3 and regression for superiority vs equal numbers).

**Attempted but not opened in this pass** (claims that depend only on these are marked unverified):

- https://www.theringer.com/nba/2022/11/10/23450356/nba-take-fouls (404; the correct URL was opened as GF4)
- 2025-26 NCAA men's rule book PDF at naia.org (over the 10 MB fetch limit)
- https://kenpom.com/blog/wp-json/wp/v2/posts/271 and other KenPom pages (403)
- https://www.tandfonline.com/doi/full/10.1080/01621459.2016.1141685 (403; arXiv used)
- https://www.teamrankings.com/blog/ncaa-basketball/turnovers-do-you-want-them-dead-or-live-stat-geek-idol (403)
- https://www.researchgate.net/publication/233526016_Analysis_of_fast_breaks_in_basketball (403)
- https://blog.hoopsalytics.com/tracking-fast-break-effectiveness/ (404; ?p=357 opened instead)
- https://www.aol.com/articles/heres-why-ohio-state-men-095622687.html (404)
- https://usctrojans.com/news/2025/12/21/... (body truncated, no quote recovered)
- https://www.ncaa.org/news/2020/6/4/video-review-to-help-officials-is-approved-in-men-s-basketball (empty body)
- cbbanalytics.com/glossary (404; the glossary lives at /resources/glossary)

> Note 2026-10-18: the play-by-play scripts used for the college numbers in "Additions 2026-10-18" are saved in `docs/research/transition_full_assets/pbp_scripts/`.
