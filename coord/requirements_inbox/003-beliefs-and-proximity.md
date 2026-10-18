# Requirements inbox 003 · Beliefs register and neutral-site proximity

From: Job C research (prompt `coord/prompts/002-claude-code-taxonomy-and-markets.md`). To: requirements session. Status: research output, not yet agreed with Aldemir.
Sources and evidence: `docs/research/beliefs_register.md` (beliefs, new-1 to new-59) and `docs/research/neutral_site_proximity.md` §10 (proximity, its own new-1 to new-8). Verdicts below are the corrected ones of 2026-10-18.
Action: decide which proposals enter the hypothesis registry and assign final numbers. JEV hypotheses H1-H10 keep their numbers; all IDs here are provisional.

Units: m, cm, s, °, m/s, m/s². Court positions as r (m) and θ (degrees from the right baseline at the rim centre). Data tiers: **PBP** = play-by-play with box scores, schedules and closing lines where stated; **Video** = broadcast tracking; **OCR** = scoreboard reading of game and shot clocks; **Markets** = prediction-market price history.

Shared definitions (register, "How to read"): run = net ≥ 8 points for one team within a rolling 120 s; scoring streak = consecutive points with no opponent points (points and s); closest-defender distance = shooter to nearest defender at release (m); closeout speed = peak defender speed toward the catcher in the 1.0 s after the catch, defender starting ≥ 3.0 m away (m/s); transition = every stored definition reported separately (`transition_full.md` §5); first defender back = time (s) until the first defender reaches r ≤ 6.75 m of his rim or crosses midcourt (14.33 m from his baseline); speed bands per `load_thresholds.md` §9 (high-speed > 5.0 m/s, sprint > 5.83 m/s; accelerations ±2.0 m/s², exploratory).

## Existing hypotheses that get evidence

- **H8 (jersey colour):** evidence attached from belief H4; verdict not supported for winning (one women's NCAA study); men's and foul effects untested. Optional new-46 below.
- **H10 (travel and time zones):** keep wording; pre-register direction (westward for evening tips, eastward for early tips lowers first-half points per 100 possessions), measured per km and per time zone (belief G1). Proximity new-5 extends it.

## Beliefs: one line per proposed hypothesis (statement · measure · data needed)

- **new-1** (A1 hot hand, mixed): Make probability after 2+ makes differs from after 2+ misses, conditional on shot difficulty (expect ≤ 2 pp) · make-probability difference (pp), difficulty from release r (m), closest-defender distance (m), shot clock (s), shot type · Video + PBP.
- **new-2** (A1): After a make the same shooter's next attempt has larger r and a smaller closest-defender distance than after a miss · Δr (m), Δ closest-defender distance (m) · Video + PBP.
- **new-3** (A1): Opponents call a timeout within 120 s more often after 2+ consecutive MSU makes by one player · timeout probability (pp) within 120 s · PBP.
- **new-4** (B1 momentum, mixed leaning not): Longest streaks and runs in Big Ten games match an anti-persistent random-walk null with team strengths · longest streak (points, s) and run counts vs simulated null · PBP.
- **new-5** (B1): A media timeout during an opponent run cuts the running team's scoring over the next 180 s vs matched uninterrupted runs · net points in 180 s · PBP.
- **new-6** (B1): In-play prediction-market prices overreact to runs and partly reverse within 300 s of game time · price change minus model-implied change (pp) · PBP + Markets.
- **new-7** (B2 timeouts stop runs, mixed): Opponent called timeouts during MSU runs do not reduce MSU's net points over the next 180 s vs matched runs without a timeout · net points in 180 s · PBP.
- **new-8** (B2): MSU after-timeout possessions (first possession after a called non-media timeout, ball in play within 5 s of the restart) score more PPP than its average half-court possession · PPP · PBP + Video set labels.
- **new-9** (A2 make-or-miss, supported descriptively; causal reading untested): Shot-making residual explains more of MSU game margin than shot-quality margin · variance share of margin (points) · Video + PBP.
- **new-10** (A2): Closing spreads do not over-react to a team's 3P% in its previous 3 games · ATS residual (points) on prior-3-game 3P% residual · PBP + lines.
- **new-11** (A5 icing, not supported): In the last 60 s of games within 3 points, FT% after an opposing timeout equals FT% with no timeout (shooter-adjusted) · FT% difference (pp) · PBP.
- **new-12** (C1 opening tip, weakly supported, tiny): Tip winner's final margin exceeds the closing spread by < 1 point on average (Big Ten) · margin minus spread (points) · PBP + lines.
- **new-13** (C1): Race-to and first-team-to-score markets underprice the tip winner when one jumper has a reach advantage (standing reach ≥ 8 cm, or peak hand height at the tip ≥ 10 cm higher) · tip-win rate vs implied probability (pp); tip direction θ (°) · PBP + roster data or Video + Markets.
- **new-14** (A3 live by the three, mixed): SD of (margin minus closing spread) is larger when the underdog's 3PA rate is in the top quartile · SD (points) · PBP + lines.
- **new-15** (A3): Big Ten high-3PA underdogs cover at the same rate as other underdogs · cover rate (pp) · PBP + lines.
- **new-16** (A4 FT choking, supported, small): Big Ten FT% in the last 30 s of games within 3 points is 2-5 pp below the shooter's season FT% · shooter-adjusted FT% difference (pp) · PBP.
- **new-17** (C2 rebounding battle, mixed): Raw rebound count adds nothing to MSU results once eFG% and turnover margins are controlled; ORB% margin adds some · incremental R² / log-loss · PBP.
- **new-18** (C2): Each extra MSU player crashing (≥ 1.5 m toward the rim within 1.0 s of release) raises MSU ORB% and changes opponent transition PPP under every stored transition definition, plus MSU first-defender-back time · ORB% (pp), opponent PPP per definition, first-defender-back time (s) · Video + PBP.
- **new-19** (C3 two-foul benching, mixed): An MSU starter who stays in with two first-half fouls fouls at a lower rate per 40 min than with 0-1 fouls and fouls out no more often than a benched starter · fouls per 40 min, foul-out rate · PBP.
- **new-20** (C3): Benching a two-foul starter for the rest of the first half lowers MSU first-half net points vs matched cases where he stays · net points · PBP.
- **new-21** (C4 foul up 3, mixed): Fouling when up 3 with ≤ 10 s on the game clock yields a higher overtime-adjusted win rate than defending, gap depending on shot clock · win rate (pp, OT = 50/50) by game-clock × shot-clock cell (s) · PBP + OCR.
- **new-22** (B3 down one at half, not supported): Teams trailing by 1-2 at half do not beat the second-half line more often than teams leading by 1-2 · second-half ATS rate (pp) · PBP + second-half lines.
- **new-23** (F2 make-up calls, mixed): In MSU games the next foul is more likely on MSU as the opponent-minus-MSU foul gap grows (first halves) · next-foul probability per foul of gap · PBP (MSU subgroup of new-32).
- **new-24** (B4 no lead is safe, not supported): Big Ten comeback rates from (lead, time) states match a random walk with a restoring force · calibration of win probability by lead (points) and time (s) · PBP.
- **new-25** (C5 two-for-one, plausible): Teams gaining the ball with 35-45 s left in a half and shooting ≤ 10.0 s after gaining it (shot clock ≥ 20 s) outscore teams holding for the last shot · net points to end of half · PBP + OCR.
- **new-26** (D1 in-game fatigue, mixed): An MSU player's difficulty-adjusted make probability declines with stint sprint distance above 5.83 m/s · make probability per 10 m of sprint distance · Video + PBP.
- **new-27** (E1 HCA about 3 points, supported on average; fortress not supported): MSU HCA per 100 possessions equals the D-I average once shrunk toward it (2021-22 on) · HCA (points per 100 possessions) · PBP.
- **new-28** (E2 HCA declining, supported): D-I HCA per 100 possessions has declined since 2010 after pace adjustment, mainly through free-throw rate · HCA trend per season, four-factor split · PBP.
- **new-29** (E3 HCA front-loaded, untested in NCAA): More than half the full-game HCA accrues in the first 600 s · cumulative home margin per 100 possessions by 240 s segment · PBP.
- **new-30** (E4 crowds cause HCA, supported partially): Each extra 1,000 spectators raises home margin per 100 possessions, mainly via the visitor foul rate (2019-20 vs 2020-21) · points per 100 possessions per 1,000 spectators · PBP + attendance.
- **new-31** (F1 referee home bias, supported): Discretionary turnovers are called more against visitors than non-discretionary ones, more so with attendance · home-minus-away rate per 100 possessions by attendance band · PBP + attendance + crews.
- **new-32** (F2): Next non-intentional foul is more likely on team A as team B's foul lead grows, controlling score, time and foul tendency · next-foul probability · PBP.
- **new-33** (F3 star treatment, mixed): For drives (start r ≥ 6.0 m, r falls ≥ 3.0 m within ≤ 3.0 s, end r ≤ 1.5 m) the foul-call rate is higher for the top-usage player, adjusting for video-labelled contact type (inside/outside r = 1.22 m) · call rate (pp) · Video + PBP.
- **new-34** (F4 refs favour trailing team, mixed): Before the final 120 s, discretionary turnovers and non-shooting fouls are called more on the leading team · call rate per 100 possessions by margin bucket · PBP.
- **new-35** (G1 travel, mixed): Visitors on the second game of a road trip without returning home do worse against expectation than on the first game · points per 100 possessions vs expectation · PBP + schedule + coordinates.
- **new-36** (G2 rest, mixed): Teams on 1 day of rest facing a 3+ day opponent lose ≥ 1 point per 100 possessions vs expectation, mostly in the second half; video add-on: MSU second-half distance per minute above 5.0 m/s (and 5.83 m/s) falls · points per 100 possessions; m/min · PBP + schedule; Video for load.
- **new-37** (E5 altitude, mixed): Each extra 1,000 m of elevation difference adds to home margin per 100 possessions, concentrated in the last 480 s of each half · points per 100 possessions per 1,000 m · PBP + venue elevation (m).
- **new-38** (E7 senior night, untested): Home teams in their final regular-season home game do not beat expectation by more than 1 point · margin minus spread (points) · PBP + lines + schedule.
- **new-39** (G3 conference-tournament fatigue, not supported on indirect evidence; fatigue itself untested): Conference-tournament games in the preceding 5 days do not predict NCAA first-game margin vs the spread · ATS residual (points) per game played · PBP + lines + schedule.
- **new-40** (G4 byes, untested): Bye teams facing opponents who played the day before meet expectation over the game but trail it in the first 600 s · margin vs expectation, full game and first 600 s · PBP + lines.
- **new-41** (H1 revenge, untested in basketball): In same-season rematches the team that lost the first meeting has a positive margin-minus-spread residual · ATS residual (points) · PBP + lines.
- **new-42** (H1): Any rematch effect appears in the first 240 s of each half · margin in first 240 s vs expectation · PBP + lines.
- **new-43** (H2 letdown, untested in basketball): After a one-possession or overtime game, next-game ATS residual is negative · ATS residual (points) · PBP + lines.
- **new-44** (H2 look-ahead): ATS residual is negative when the next opponent is ranked and the current one unranked · ATS residual (points) · PBP + lines + polls.
- **new-45** (H3 rivalry, mixed): Rivalry games have larger variance of margin minus spread than matched conference games; underdog mean ATS residual not above zero · SD and mean of ATS residual (points) · PBP + lines + rivalry list.
- **new-46** (H4 jersey colour → H8): With venue fixed, team fouls per 100 possessions do not differ by uniform darkness · fouls per 100 possessions · PBP + one video frame per game.
- **new-47** (E6 domes, not supported for midfield): Tournament shooting residuals do not differ between midfield domes and arenas; corner domes lower 3P% · FT%, 2P%, 3P% minus season average (pp), opponent-adjusted · PBP + venue metadata.
- **new-48** (E6 backdrops, mixed): FT% differs by basket end when one end's backdrop is an active student section (≥ 50% of backdrop area within ±15° of the shooter's line through the backboard, ≤ 10 m behind the baseline, visible motion or signage) · FT% difference by end (pp), shooter fixed · PBP if shot end known; otherwise Video.
- **new-49** (H5 defense wins championships, not supported): With total rating fixed, a defense-heavy profile does not predict a positive tournament ATS residual · ATS residual (points) · PBP + ratings + lines.
- **new-50** (H5): Game-to-game variance of defensive PPP is lower than of offensive PPP (D-I and MSU) · variance ratio · PBP.
- **new-51** (H6 experience, mixed): Top-5 prior-tournament-minutes difference predicts a positive tournament ATS residual, especially from the Sweet 16; class year does not · ATS residual per minute of difference · box scores + lines.
- **new-52** (H7 veteran coaches, mixed): A coach's prior-years PAKE predicts his next tournament's ATS residual after shrinkage · ATS residual (points) per PAKE unit · ratings + lines.
- **new-53** (H8 hot team entering March, supported and priced): Late-season form predicts tournament margin beyond season ratings but not ATS · margin and ATS residual on last-30-day minus season efficiency · PBP + ratings + lines.
- **new-54** (I1 favourite-longshot bias, supported): Post-2021 NCAAB moneylines still show a favourite-longshot bias · return by implied-probability bin (%) · moneylines + results.
- **new-55** (I4 public teams, mixed): Ranked or nationally televised teams have a negative mean ATS residual, spread band controlled · ATS residual (points) · lines + polls + TV metadata.
- **new-56** (I5 overreaction, untested for NCAAB): ATS residual in game t is negatively related to that in game t-1 · autocorrelation of ATS residuals · lines + scores.
- **new-57** (I2 big favourites, mixed): Underdogs of more than 12 points cover more than 50% in 2021-2026 D-I data · cover rate (pp) · lines + scores.
- **new-58** (H9 never bet against Izzo, supported vs seed and ratings; untested vs market): MSU under Izzo has a positive mean tournament ATS residual (n = 88 games, 61-27 per MSU Athletics; descriptive, SE about 5.3 pp) · cover rate and mean ATS residual with bootstrap CI · lines.
- **new-59** (H9): MSU's tournament efficiency margin exceeds its season-adjusted margin, concentrated on defense or rebounding · efficiency margin per 100 possessions; video closest-defender distance (m) · PBP; Video for contest distance.

## Neutral-site proximity (`neutral_site_proximity.md` §10)

These IDs restart at new-1 in that file and overlap with the beliefs IDs above; the requirements session should renumber them (for example as new-60 to new-67). Details, priors and sources are in that file.

- **prox new-1:** At neutral sites the team closer to the venue beats the closing spread by a concave function of the distance gap · margin against the line on f(d_opp) − f(d_team), f = d^(1/3) or log(1 + d/100 km) · PBP + coordinates + lines.
- **prox new-2:** The same gap predicts margin against a neutral rating model · margin minus rating-implied neutral margin · PBP + ratings.
- **prox new-3:** Proximity raises the closer team's FTA and foul differential (referee channel) · FTA and PF differential per 100 possessions vs distance gap and attendance · PBP.
- **prox new-4:** Opponent FT% falls when the modelled crowd share against it is large · FT% (pp) vs gravity-model or video colour-share crowd share · PBP + attendance + coordinates; Video or audio for crowd share.
- **prox new-5:** An eastward time-zone shift of ≥ 3,600 s lowers first-half efficiency at neutral sites, distance fixed (extends H10) · first-half PPP vs shift (s) · PBP + time zones.
- **prox new-6:** Crowd-noise asymmetry follows modelled crowd share · noise asymmetry (dB) after scores vs crowd share · broadcast audio and Video.
- **prox new-7:** The proximity effect has shrunk over time · distance gap × season interaction, 2002-2026 · PBP + historical lines.
- **prox new-8:** In Big Ten tournaments the closer team beats the spread; the 2028 Las Vegas site moves the edge to West Coast members · ATS by distance rank per venue year · lines + coordinates.

## Open questions for Aldemir (one line each)

- No market belief can be tested on MSU games alone (one season gives a cover-rate SE of about 8.5 pp); confirm that market hypotheses are fitted on pooled D-I data with MSU as a subgroup.
- Which closing-line source and seasons (2021-2026 legal-market lines) should the market tests use?
- Should the curated rivalry list (new-45) be hand-made (e.g. MSU-Michigan) or data-driven?
- Is a licensed public-betting-share feed in scope for new-55, or do we test with volume proxies only?

---

## Addendum 2026-10-18 (second pass: gap-filling additions to both research docs)

Appended, not rewritten: the lines above stay as they were. This section brings the summary up to date with the "Additions 2026-10-18" sections of `docs/research/beliefs_register.md` (new beliefs E8 and F5, added evidence for A1, A2, B2, E1/E2/E4, G1/H10 and H4/H8; hypotheses new-60 to new-63) and of `docs/research/neutral_site_proximity.md` (items A-H; proximity new-9 to new-11). Every source and every "unverified" mark is in those two files. Data tiers as above; **Market** here means closing lines and prediction-market prices together.

### Changes to lines above (read these as superseding the earlier wording)

- **H10 (travel and time zones):** do **not** pre-register one direction. Large NBA studies disagree (Leota 2022: eastward jet lag hurts *home* teams, −1.29 points, away teams unaffected; McHill & Chinoy: westward hurts *away* teams; Charest 2021: eastward beats westward on back-to-backs; Özdalyan 2024: no team-strength control). Proposed wording: estimate home and away effects separately, two-sided tests for east and west, days since the shift (1 h recovered per day), tip time on each team's body clock as its own term, ratings and rest controlled.
- **new-1 (hot hand, video FG):** restate as an **estimate with a confidence interval and a pre-declared equivalence bound** (e.g. "the 90% CI excludes +5 pp"), not a significance test. Power: four seasons of MSU and opponents (about 13,000-14,000 attempt pairs) gives a minimum detectable difference of about 2.5 pp at streak length 1 and about 3.4 pp at 2+ vs 2+, so "at most 2 pp" cannot be separated from zero. Per-player hot-hand results only inside a hierarchical model (per-player minimum detectable effect 15-30 pp).
- **new-9 (make-or-miss):** align the expected-points model with the NBA ESQ/EFG+ and qSQ/qSI split (inputs: r m, θ °, closest and second-closest defender distance m, shooter speed m/s at release, catch-and-shoot vs pull-up, shot clock s). NBA-precedented, new for NCAA.
- **new-7 (timeouts):** design confirmed by three matched NBA studies (effects near zero or slightly negative) and two small peer-reviewed NCAA pre/post studies (Mace 1992, Roane 2004); add a Mace-style 180 s replication arm. Verdict stays mixed.
- **H8 / new-46 (jersey colour):** verdict for fouls changes from "untested" to **mixed** (NHL 52,098 games: dark jerseys about +2 penalty minutes per game; one Chinese basketball league study supportive; soccer nulls once home/away is conditioned). Design: same team, same venue, different colourway, game importance controlled. Still not supported for winning.
- **new-27 / new-28 (HCA):** peer-reviewed baseline added (Jamieson 2010 meta-analysis: basketball home win proportion .629, k = 12; short seasons and playoff games higher). Karl (arXiv, not peer-reviewed) gives a D-I men's HCA decline of −0.074 points per season 2000-2017 (95% CI −0.097 to −0.051); fit new-28 per 100 possessions because pace confounds a points trend.
- **prox new-5:** keep, but report by session (late, afternoon, early) with the body-clock terms as controls; split into prox new-9 and new-10 below.
- **prox new-7:** fit on margin per 100 possessions and test whether the proximity effect falls in proportion to that season's HCA (β_t / HCA_t constant), not only a linear season trend.
- **prox new-8:** add Big Ten ticket-allocation facts (cap per school, reallocation of unsold allotments, block location by rotation or standings) as covariates where they can be sourced.
- **Renumbering:** the earlier suggestion of new-60 to new-67 for the proximity IDs now collides with register new-60 to new-63. Proposed instead: prox new-1 to new-11 become **new-64 to new-74** in order. new-60 is the tournament stratum of prox new-1 and new-2; if merged, keep the proximity IDs and drop new-60.

### New proposed hypotheses (statement · measure · data needed)

- **new-60** (E8 tournament proximity, mixed; market: partly priced, residual untested): In NCAA tournament games 2002-2026, the team closer to the venue beats both the rating-implied neutral margin and the closing spread by an amount increasing in f(d_opp) − f(d_team), f = d^(1/3), seed and rating difference controlled · margin minus neutral expectation and ATS residual (points) · PBP + coordinates + ratings + Market (lines).
- **new-61** (F5 referee crew, supported for fouls, untested for totals; market: unknown, depends on whether crews are public before close): A crew's prior-season fouls above average predicts game FTA strongly and total points minus the closing total weakly (null expected) · FTA per game; total minus closing total (points) per crew-FAA SD · PBP + crew names + Market (closing totals).
- **new-62** (A1 hot hand at the line; market: not studied): Across all D-I free throws, within-trip P(make | previous FT made) − P(make | previous FT missed) is positive, shooter random effects, Miller-Sanjurjo correction by permutation within shooter-game · difference (pp); one D-I season detects about 0.9 pp · PBP only.
- **new-63** (E1/E2 HCA by game importance; market: average HCA priced, split unstudied): HCA per 100 possessions is larger in February-March conference games than in November-December games, rating-adjusted margins and pace controlled · HCA (points per 100 possessions) by period · PBP only.
- **prox new-9** (body clock, late session; market: NFL not priced up to 2011, college unknown): At neutral sites, the team whose tip falls later on its home-zone clock (≥ 21:00) does worse against the closing spread, beyond shift-size terms, first half separately · margin against the line per 3,600 s of late-clock difference · PBP + tip times + IANA zones + Market (lines).
- **prox new-10** (body clock, early session; market: unknown): A team tipping before 12:00 on its home-zone clock does worse, especially in the first half · first-half and full-game margin against the line per 3,600 s of early-clock difference · PBP + tip times + Market (lines).
- **prox new-11** (crowd vs fatigue; market: unknown, compare residuals across strata): The distance-gap effect is smaller in low-crowd games (2021 NCAA tournament with no pods and about 2,671 fans per game; capped 2020-21 conference tournaments and events) than in normal years · interaction of distance gap × low-crowd stratum, per 100 possessions and against the line · PBP + attendance + coordinates + Market (lines).

### Does the market price each belief? (one line each, from the register summary table)

- Priced or largely priced: E1 HCA average, E2 HCA decline, G3 conference-tournament fatigue, H8 hot team entering March, I3 home underdogs.
- Partly priced: E5 altitude, G1 travel and time zones, G2 rest (NCAA about 0.45 point shading), E8 tournament proximity (residual untested), C2 rebounding (embedded in ratings).
- Mispriced but small or not exploitable: I1 favourite-longshot bias, I2 big favourites (mild), I6 totals to the over (weak evidence), A1 and B1 between-game streaks (bettors over-bet, closing prices near unbiased; pre-game momentum moves reversed by outcomes).
- Props: C1 first-team-to-score priced near 50-50, ignoring jump-ball skill (practitioner source only).
- Unknown or not studied: A2 recency of 3P%, A3 variance, A4, A5, B2, B3, C3-C6, D1, E3 first-half pricing, E4 (NCAA), E6, E7, F2-F5, G4, H1-H7, H9 vs market, I4 price effect, I5.
- In-play pricing of any in-game belief (hot hand, runs, timeouts, fouls): **no study found**; our 2025-26 Polymarket and Kalshi price history would be the first test (new-6, new-13).

### Open questions for Aldemir (one line each, new in this pass)

- Merge new-60 into prox new-1/new-2 (tournament stratum), or keep it as a separate tournament-only hypothesis?
- Accept the renumbering prox new-1..new-11 → new-64..new-74, or assign final numbers in another order?
- For H10, accept two-sided, home/away-separate pre-registration instead of a fixed direction?
- For new-1, which equivalence bound (e.g. +3 pp or +5 pp) counts as "no meaningful hot hand"?
- Neutral expectation for proximity tests: a rating with a travel term (COOPER, BPI) or without (Torvik), and must every claimed edge also show a closing-line residual?
- Distance metric for fans: great-circle (WGS84 geodesic) only, or also driving time for short trips?
- Should we build a video crowd-share measure (clothing colour in wide shots) or an audio one (prox new-6), and exclude 2021 audio (artificial crowd noise)?
- Include the 2020-21 low-crowd games as their own stratum (prox new-11), or drop the season from the main fits?
- Are NCAA officiating crews published before tip? If not, new-61 can only be an in-play or FTA test, not a pre-game market test; who checks?
- Scoreboard OCR for the shot clock is needed for new-21 and new-25; is it in scope for the first build?
- Should women's tournament games (top-16 hosts) be collected as a home-advantage calibration stratum, given that women's closing lines are not yet sourced?
- Minimum count for the small-sample rule (`docs/requirements.md`): what n makes an MSU-only result more than descriptive (MSU has about 9 neutral-site games and about 35 games per season)?

### Gaps still open (for planning, not decisions)

- No peer-reviewed NCAA study for: in-game FG hot hand; regular-season rest, travel or time zones; revenge, letdown, look-ahead, rivalry ATS; men's jersey colour; senior night; byes; proximity against spread residuals at neutral sites; crew assignment against closing totals; college body-clock tip times.
- Key primaries not read (figures marked unverified in the docs): KenPom blog posts (Cloudflare; some read via web.archive.org), GVT 1985 and several SSRN, ScienceDirect, SAGE, T&F and MDPI full texts (403), Carter 2017, Clay et al. 2015 coefficients, Özdalyan 2024 full text, McCartney tip study (404), Winthrop 2014 PDF.
- Most market evidence uses 1996-2007 offshore lines; every market hypothesis needs replication on 2021-2026 legal-market lines, pooled across D-I with MSU as a subgroup.
- Current Big Ten men's ticket rule (rotation vs standings, cap, returns) and the current NCAA per-school allotment (last confirmed 350 for rounds 1-2, 2005) are not confirmed.
