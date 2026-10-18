# Neutral-site proximity, crowd share and time zones

Job C, item 2 of `coord/prompts/002-claude-code-taxonomy-and-markets.md`. Written 2026-10-17 for MSU Alpha 3. This document answers one question: when neither team is at home, does the team whose campus is closer to the venue do better than expected, by how much, and how should we test it?

**Units.** Kilometres, hours and points throughout. Where a source reports miles, its figure appears in brackets and was converted at 1 mi = 1.609344 km.
- **Storage vs display.** Distances are stored in metres (`d_team_m`) and shown in km for readability. Time-zone shift is stored in seconds (`tz_shift_s = 3,600 × hours`) and shown in hours for readability. This follows the project rule (metres, seconds); the km and h shown in tables are display units only.
- **COOPER travel term in our units.** COOPER's native form is 5·m^(1/3) Elo with m in miles and about 28.5 Elo per point. In km this is **0.1497·d_km^(1/3) points** (5/28.5 × 1.609344^(−1/3)).

**Revision note (fixer pass on the 2026-10-18 verifier findings).** Corrections in this pass: the bottom line no longer says every source agrees; the size range is unified at 0 to about 1.3 points (COOPER form); several source descriptions were corrected against the opened sources (van Bommel FT% units, Yi full model, StatsByWill scope, Samford Big Ten clause, Oberhofer p-values, Ponzo ranges, Rishe distance sign); Clay et al. figures without any opened source are marked UNSOURCED; §9.1 opponent origins now use home-arena Wikidata items (Appendix A) and the computing script is saved in the repo; §2.4 (conference tournaments and early-season events) and operational rules for §8 were added.

**Sourcing.** Every claim carries the URL that was opened during the research for this task; all of them are listed in [Sources](#sources). "**Unverified**" means one of three things: the primary page could not be opened, the figure came only from a search-result snippet, or it came from a secondary summary. Those marks are kept wherever the claim appears.

**Related repo items.**
- `docs/requirements.md`:
  - match-context fields "Home, away or neutral; venue, city, capacity, attendance" and "Days of rest, travel distance and time zones crossed, for both teams";
  - "Travel and schedule" (flight time and distance, time zones crossed, bus vs flight);
  - "Crowd loudness as a possible home-crowd measure" and "Crowd loudness curve";
  - the small-sample rule ("below a minimum count, a result is shown as descriptive only");
  - hypothesis **H10** ("Travel distance and time zones crossed lower first-half efficiency").
- `docs/research/odds_markets_research.md`: free closing lines from the ESPN core odds API and the CBBD `/lines` endpoint, used in the test plan in §8.

---

## Contents

1. [Bottom line](#1-bottom-line)
2. [Evidence: proximity and margin at neutral sites](#2-evidence-proximity-and-margin-at-neutral-sites) (§2.4: conference tournaments and early-season events)
3. [Effect estimates: points per 100 km and per log-distance](#3-effect-estimates-points-per-100-km-and-per-log-distance)
4. [How crowd share is estimated](#4-how-crowd-share-is-estimated)
5. [Time-zone effects](#5-time-zone-effects)
6. [How rating systems and the betting market adjust](#6-how-rating-systems-and-the-betting-market-adjust)
7. [Venue and campus coordinates, and the distance method](#7-venue-and-campus-coordinates-and-the-distance-method)
8. [Proposed model for our data](#8-proposed-model-for-our-data)
9. [MSU neutral-site games 2022-23 to 2025-26, and Big Ten tournament venues](#9-msu-neutral-site-games-2022-23-to-2025-26-and-big-ten-tournament-venues)
10. [Proposed hypotheses (new IDs)](#10-proposed-hypotheses-new-ids)
11. [Open questions and gaps](#11-open-questions-and-gaps)
12. [Sources](#sources)
13. [Appendix A: entity coordinates](#appendix-a-entity-coordinates)
14. [Additions 2026-10-18](#additions-2026-10-18) (gap-filler pass: body-clock tip time; NBA distance and direction studies; Big Ten ticket rules; the 2021 Indiana tournament; the home-advantage decline; fan-base proxies; true home games inside tournaments; new-9 to new-11)

---

## 1. Bottom line

1. **The direction in raw data is mostly consistent, but the effect is small, its size is disputed, and several controlled studies find nothing.**
   - Raw comparisons and most raw or seed-adjusted tournament studies point the same way (the closer team does better): News & Observer splits, Ward & Davenhall, Carter 2017, Clay et al. (unverified figures).
   - Studies with stronger controls find small, non-significant or team-specific effects:
     - Delbianco et al. 2026 (rugby sevens): the pooled effect disappears once team and opponent fixed effects are added;
     - Beckmann 2021 (Bundesliga): the distance contribution is insignificant in recent seasons;
     - Horlick et al. 2023 (UNC undergraduate study; 2019 and 2022 NCAA tournaments, seed gap ≤ 7): with team quality controlled, travel "has little to no effect on the outcome";
     - Yi 2017 (A-10): travel distance is not significant in the full model;
     - Williams 2025: no relation between miles travelled and tournament lines (a null result about lines, not about outcomes);
     - Oberhofer et al.: the goal-difference effect at the mean distance is not significant (p = 0.116), and the fitted quadratic turns over at about 450-481 km;
     - Ward & Davenhall: distance alone ranks last by AIC.
   - **Size: about 0 to 1.3 points** for the gap between the two teams under the COOPER form (largest MSU-game value 1.34 points, §9.1). This range is **model-implied** (COOPER/SBCB curves); no verified empirical points estimate exists for college neutral sites. The FiveThirtyEight figures of +2 points or more are **unverified** (snippet only). The same range is used in §3 and §8.
   - Rating systems that model it use a concave curve: the Silver Bulletin COOPER model uses 5·m^(1/3) Elo, with m in miles and about 28.5 Elo per point (= 0.1497·d_km^(1/3) points).
   - Silver's model pages state that the travel effect has shrunk (no estimate or sample published); Beckmann 2021 reports a similar decline in the Bundesliga. The decline is **untested in college basketball** (new-7).
2. **Seeding confounds raw win rates.**
   - The NCAA adopted the "pod" system in 2002 "to keep teams closer to home" (Pitt News / News & Observer, 16 Mar 2008; Source 11). The current NCAA.org explainer (Corbin McGuire, 12 Mar 2025; Source 50) says teams "are placed as close to home as possible"; it does not mention pods or 2002. Strong teams therefore get the short trips.
   - So raw splits mostly measure team quality. One example: teams within 161 km (100 mi) of the site won 77% of games (News & Observer, 2008).
   - Only studies that control for seed, rating or the spread are informative, and they find small or null effects:
     - Ward & Davenhall (2006): adding the distance gap improves AIC by only 2.5.
     - Horlick et al. (2023): no effect in close-seed games (undergraduate; 2019 and 2022 only).
   - The TeamRankings (2012) cover split (55% vs 43%, n = 71 / 39) is **consistent with zero**: the 95% CI for each rate is about ±12 to ±16 percentage points. It is not counted as evidence of an effect.
3. **Inference (not a college-basketball finding): at these distances the likely channel is crowd share, not fatigue.**
   - Evidence from soccer (Ponzo & Scoppa's same-stadium derbies) and the NBA (Ganz & Allsop's attendance-cap instrument, in arenas of at most a few thousand fans) suggests crowd share rather than fatigue.
   - No college-basketball study separates the channels. The referee route is contested: Ganz & Allsop found no foul effect. new-3 and new-4 test this.
   - Kilometres would then stand in for how many of each team's fans attend, and possibly for the referees' response to them.
   - Time-zone shift is a separate channel, with the strongest evidence for eastward travel, mostly from the NFL and from NBA home teams returning east (§5); evidence for teams at neutral sites is thin.
4. **Whether the betting market prices it is untested; it may price most of it.**
   - No study was found that tests proximity against spread residuals at college-basketball neutral sites while controlling for team quality. That is a genuine gap.
   - One undergraduate study (Williams 2025; n = 327 games) found no relation between miles travelled and tournament lines. This is a null result; the author's conclusion that the market "fully accounts" for travel is an efficient-market assumption, not a finding that lines absorb distance.
   - Coleman 2017 and Fodor & Krieger 2014 report travel and jet-lag inefficiencies in football lines (abstracts only). Nichols 2014 finds a bias (bettors under-estimate the home score) but no profitable out-of-sample strategy, so it is mixed evidence, not evidence of exploitable under-pricing.
   - Status for the beliefs register: **partly priced, residual unknown, testable with play-by-play plus closing lines.**
5. **MSU's own data is far too small to estimate the effect.**
   - MSU has about 9 neutral-site games per season (35 games listed as neutral over the four seasons 2022-23 to 2025-26, of which one, Rutgers at Madison Square Garden, is an ESPN-coded Rutgers home game; §9).
   - Plan: fit the effect on every Division I neutral-site game, then apply the fitted curve to MSU, and report MSU-only results as descriptive under the small-sample rule.

---

## 2. Evidence: proximity and margin at neutral sites

### 2.1 NCAA men's tournament (most relevant)

| Study | Design and sample | Distance measure | Finding | Controls for quality? | Status |
|---|---|---|---|---|---|
| **Carter, K. E. (2017).** "Relative Home-Court Advantage: The Impact of Travel on Team Production When One Team is Closer than its Opponent to a Neutral Game Site." *Managerial and Decision Economics* 38(1): 76-91. doi:10.1002/mde.2742 | NCAA men's tournament; binary logit for wins, OLS for margin | Relative distance to the neutral site | The "relative home team" out-produces its opponent. When it travels **much** less than the opponent, closeness relates positively to winning and to margin of victory. | Unknown (abstract only; full text paywalled). Not counted among quality-controlled studies. | Peer-reviewed. Abstract confirmed via IDEAS/RePEc, Crossref and Semantic Scholar. Full text is paywalled, so the effect size in points and the distance threshold are **unverified**. |
| **Clay, Bro & Clay (2015).** "Geospatial Determinants of Game Outcomes in NCAA Men's Basketball." *Int. J. of Sport and Society* 4(4). doi:10.18848/2152-7857/cgp/v04i04/64015 | 1,648 tournament games (3,296 team performances), 1985-86 to 2010-11; sample confirmed on the publisher page | Over 241 km (150 mi) from home region (binary); time zones | Odds ratio 0.644 (33.6% lower odds of winning) beyond 241 km, per a Winthrop Intelligence search snippet (reported by the verifier, not seen in this pass) and the GitHub literature review (33.6% only; it dates the paper 2014); **unverified**. A snippet of the same PDF seen in this pass says eastward time-zone travel "significantly reduces the odds of winning", with no figure. The odds ratio "about 0.861" for eastward travel and "elevation and temperature not significant" are **UNSOURCED** (no opened page contains them) and are withdrawn until the full text is read. | Seed (per the earlier draft; not confirmed) | Peer-reviewed, in a low-impact journal. Sample confirmed on the publisher page; all effect sizes unverified. |
| **Ward & Davenhall (2006),** ArcUser (Esri) | Logit over 64-team-era games since 1985; about 35,000 team-to-location distance records; Euclidean distance | Distance and distance gap | AIC: seed gap + RPI gap = 2906.06; adding the distance gap = 2903.57 (the best model). Distance alone ranks last. The authors suggest distance may move margin more than win/loss. | Seed, RPI | Opened. Not peer-reviewed. Weak evidence for a small effect. |
| **TeamRankings, "Stat Geek Idol" (Michael Lopez, 17 Mar 2012)** | 323 tournament games, 2007-2011 | Not stated in the post | Both teams within 805 km (500 mi): favourites won 76% and covered 55% (n = 71). Both teams 1,609 km (1,000 mi) or farther: favourites won 59% and covered 43% (n = 39). Longer trips went with higher underdog 3P% and lower favourite 2P% and 3P% (lowess). "Midweek" (Tuesday, Thursday and Friday games vs Saturday/Sunday and championship games) had 24.5 vs 23.0 turnovers per game (p < 0.05). | Spread (cover rates) | Opened via curl. Blog post. The cover split is consistent with zero: 95% CI about ±12 pp (n = 71) and ±16 pp (n = 39). |
| **News & Observer (J. P. Giglio) via Pitt News, 16 Mar 2008** | 12 tournaments | Distance | Win rates: within 161 km (100 mi) 77%; about 402 km (250 mi) 69%; 805 km (500 mi) or more 46.5%. The closer team won about 51% before pods (1996-2001) and about two-thirds after 2002. First-round upsets: 53 before pods, 41 after. | **No**, so the splits are confounded with seed | Opened. Descriptive only. |
| **Williams, T. (2025).** "From Tip to Take Off: The impact of team travel on Over/Under and Point Spread Betting in the NCAA Tournament." Allegheny College senior project | 327 tournament games, 2008-2012 | Distance travelled; time zones crossed | No significant link between distance and the spread or total. One weak link: −2.99 points of total score per time zone crossed. The author concludes the lines "fully" account for travel; that is an efficient-market reading of a null result, not a test showing lines absorb distance. | n/a (it tests the lines) | Opened (repository abstract). Undergraduate work. |
| **Horlick, Miller, Webb & Bruss (2023),** "Does how far you've come determine how far you'll go? An Analysis of Travel Distance within the NCAA Tournament." UNC Office for Undergraduate Research abstract (adviser J. Jensen) | 2019 and 2022 NCAA tournaments, games with a seed difference of 7 or less; binary logistic regression | Travel distance | With team quality controlled, travel distance "has little to no effect on the outcome of the game"; the model predicted 59.1% of outcomes. **Evidence against.** | Yes (team quality; details not seen) | Opened (abstract only). Undergraduate; small sample (two tournaments); sample size not stated. |
| **FiveThirtyEight, "In Tournament, There's No Place Like Close to Home"** | Tournament games; distance-based bonus or penalty | Distance | About −1 point for a 2,414 km (1,500 mi) trip and about +2 points when playing 161 km (100 mi) from home; rarely above 3-4 points, maximum about 6. The closer team went 73-25 when at least 1,609 km (1,000 mi) closer. | Ratings | **Unverified**: snippet only. The page redirects to abcnews.com and the archive was unreachable. |
| **RotoWire (2026)**, travel-distance table | 2026 field; haversine from campus to venue | Distance | MSU 457 km (284 mi) to Buffalo vs North Dakota State 1,477 km (918 mi), an edge of 1,020 km (634 mi). The article itself calls the edge contextual, not predictive. | n/a | Opened. Used only to cross-check our distances: we compute 460 km and 1,481 km. |
| **arXiv:1412.0248** (NCAA model paper) | n/a | Campus-to-site distance | Lists the distance as available tournament data; no estimates. | n/a | Opened. |

A blog post on Punk Rock Operations Research (2009, opened) makes the same point about seed and distance confounding and comments on the AIC comparison.

### 2.2 Other college-basketball evidence on venue and crowd

- **Harville & Smith (1994),** *The American Statistician* 48: 22-28 (citation confirmed via Crossref).
  - Home vs neutral court: **4.68 ± 0.28 points**, from 1,678 Division I games in 1991-92. The figure comes from Magel & Unruh (2013, *Open J. Statistics*), which was opened.
  - Per Magel & Unruh, Harville & Smith found "no positive or negative relationship between a strong home court advantage and the performance of the team", i.e. the size of a team's home advantage is unrelated to team quality. (An earlier draft said "team-to-team variation was small"; that wording is not in any opened source and is withdrawn.)
  - This is the classic baseline that treats a neutral court as zero.
- **van Bommel, Bornn, Chow-White & Gao (2021),** "Home Sweet Home," *J. Sports Analytics* 7(1); arXiv:1909.04817 (opened).
  - Sample: over 100,000 NCAA games across all divisions and both genders, 2011-12 to 2015-16, including **23,856 neutral-site games**.
  - About 76% of the home-away gap in 3FG% and 65% of the gap in FG% lies between home and neutral. Playing neutral rather than away helps only a little.
  - FT% is 1.1% lower for away teams than for neutral teams, and only 0.2% higher for home teams than for neutral teams. These are **relative** changes (difference divided by the overall mean of the statistic, as defined in §3 of the paper), not percentage points. The paper adds that "neutral D1 teams actually have a higher FT% than home teams" (§3, insight 4). This weakens the crowd-pressure-on-free-throws idea behind new-4.
  - **Referee bias toward the home team grows with attendance** (matched on RPI).
  - Division I neutral-site games draw notably higher attendance than other games.
- **Beney (Dec 2025), Beyond the Score** (Substack, CBBD data; opened).
  - Home teams won 68.7% of 12,465 Division I games, 2017-18 to 2024-25: about +6.4 points after controlling for KenPom rating and a neutral flag.
  - **Each 1,000 fans adds about 0.48 points** toward the home team (r = 0.26), with diminishing returns in large arenas.
  - In 2020-21, home teams won 68.1% of on-campus games vs 76.9% in other seasons.
  - Not peer-reviewed; the figures are internally inconsistent (our reading, not the author's: 68.7% overall is below both the 68.1% and 76.9% subsets; 2020 is said to be excluded but is used as a comparison; KenPom is the control in the margin model and Elo difference in the attendance model; KenPom ratings are season-ending). The 76.9% includes D-I teams hosting non-D-I opponents, which the author says "likely" inflates it (footnote 4). The author publishes no correction.
- **Samford Center for Sports Analytics (Black, 1 Apr 2021)** (opened).
  - 19,285 Division I regular-season games, 2017-2021, excluding neutral-site and tournament games.
  - Home win percentage fell by almost 5 percentage points in 2020-21, and visiting-team fouls fell 4.8% (significant).
  - The Big Ten was the only Power 5 conference without a statistically significant decline in **visiting-team fouls** in 2020-21 (the clause is about fouls, not home win percentage).
  - Not peer-reviewed.
- **Yi (The Sport Journal, 2017)** (opened): 246 Atlantic 10 conference games in 2005-06. Travel distance lowers away efficiency when tested alone, but is **not significant** once crowd density (home-court atmosphere) is included; only crowd density survives in the full model. Small sample. This supports the crowd channel over distance.
- **StatsByWill (Will Warren, Substack, 7 Jul 2023), "Neutral-site games: a problem for everyone but the players"** (opened). Descriptive only.
  - Non-conference games (all levels), 2018-2023: neutral-site offense scored 100.7 points per 100 possessions vs 101.1 in home and away non-conference games. The offensive-rebound rate was slightly lower at neutral sites. (The high-major filter applies only to a separate shooting comparison.)
  - Maui Invitational events actually held in Maui (2017, 2018, 2019, 2022): 108.3 points per 100 possessions.
  - "Announced about 3,500, actual about 2,034" for a November neutral-site game: **author's illustrative estimate, no data source**.
  - "The two teams' fans might constitute about 70% of that number if not more": **author's illustrative estimate, no data source**.

### 2.3 Evidence from other sports (mechanism and functional form)

| Study | Setting and n | What it says about proximity | Status |
|---|---|---|---|
| **Oberhofer, Philippovich & Winner (2010),** *J. Economic Psychology* 31(2): 200-211 (working paper 2008-16 opened) | 6,389 Bundesliga away games, 1986-87 to 2006-07; mean distance 368 km, maximum 805 km | Goals conceded rise with distance: +0.019 goals per 100 km at the mean (p = 0.067). Goal difference: −0.022 goals per 100 km at the mean (**p = 0.116, not significant**; median −0.023, p = 0.102; Model B not significant at the mean) and −0.051 at 220 km (p = 0.015). The **implied vertex of the quadratic fit** is at 450-481 km for goal difference (Model B, Model A) and 416-490 km for goals conceded; beyond it the fitted marginal effect changes sign. This is a derived critical value, not an observed peak. No effect on goals scored. (Working paper Table 3.) | Peer-reviewed |
| **Beckmann (2021),** *German J. Exercise and Sport Research*, doi:10.1007/s12662-021-00787-7 (opened) | 17,376 Bundesliga matches, 1964-2020 | The distance effect **saturates around 100 km**. It made up about half of home advantage before about 1990 and is insignificant now. Home advantage exists even at about 0 km. | Peer-reviewed |
| **Van Damme & Baert (2019),** IZA DP 12143 (opened) | 2,012 Champions League and Europa League matches | Altitude matters: each 100 m of altitude difference adds 1.1 percentage points to home win probability. Beckmann summarises this paper as finding no geographic-distance effect. | Working paper |
| **Ponzo & Scoppa (2018),** *J. Sports Economics* 19(4): 562-582 (CSEF WP 376 opened) | Serie A 1991-2013, 7,398 matches, including 128 same-stadium derbies | With travel and familiarity removed, **crowd share alone** gives about 15-16 percentage points of win probability in the derby-only model (Table 4; 15-18 across the Table 6 joint specifications), vs about 23 in normal matches (Table 3) and about 25 in the joint model (24-27 across Table 6 specifications). The derby goal-difference effect is about 0.44 goals, "almost significant at the 5 percent level", from only 128 derby matches. Referee sanctions favour the home team. | Peer-reviewed. The best evidence that crowd share is the main channel (soccer, not basketball). |
| **Kneafsey & Müller (2018),** *IJPAS* 18(6): 892-905 (opened) | Over 3,500 Gaelic football and hurling matches, 2009-2018 | Favourite's win probability is 0.8-0.9 at home, about 0.7 at neutral venues and under 0.6 away. Neutral venues are chosen to equalise travel. | Peer-reviewed |
| **Delbianco, Fioravanti, Tohmé & Trombetta (2026),** arXiv:2608.16312 (opened) | 2,672 rugby sevens matches, 2016-2025, with no formal home team | The pooled proximity effect **disappears once team and opponent fixed effects are added**. Distance gradients are team-specific, partly through east-west jet lag. | Preprint. The main methods warning: proximity is confounded with team composition and scheduling. |
| **Fioravanti, Delbianco & Tohmé (2023),** arXiv:2308.06279 (opened) | Argentine football, over 20 years; away fans banned for over 10 years | The away-fan ban helped the top 5 clubs in its first two years. Empty stadiums turned home advantage into a disadvantage for most teams. | Preprint |
| **Ganz & Allsop (2021),** AEI WP 2021-10 (opened) | 946 NBA games, 2020-21, using capacity limits as an instrument | Home margin was +2.13 points with fans vs +0.39 without. **+1.17 (fixed effects) to +1.38 (fixed effects with instrument) points per 1,000 fans**, in arenas holding at most a few thousand fans. No significant effect on fouls. | Working paper with a strong design |
| **Leota et al. (2022),** *Front. Physiol.* 13:892681 (PMC9245584 opened) | 11,481 NBA games, 2011-12 to 2020-21 | See §5. | Peer-reviewed |
| **Yoost (2009),** *The Sport Journal* (opened) | 47 BCS bowl games, 1999-2008 | The closer team went 25-22 straight up and 26-21 against the spread (24-17 after dropping negligible-distance games). No significance tests. | Weak |
| **Mochales Cuesta et al. (2024),** systematic review, *JFMK* 9(4):192 (PMC11503446 opened) | 39 studies of elite basketball (the results section says 40; NBA/WNBA count given as both 24 and 25), **none on the NCAA** | Travel distance mattered for home advantage only in US studies. The crowd effect was larger in Europe. The **direction of time-zone effects is inconsistent** across included studies: the abstract says eastward travellers tend to do better, while Leota 2022 (as summarised in the review's own Table 2) finds eastward jet lag hurts home teams. | Review; internally inconsistent counts |

**What this implies for the functional form.**
- The effect is concave or saturating in distance:
  - cube root (COOPER);
  - "growing at a diminishing rate" (Nichols 2014);
  - saturating near 100 km (Beckmann);
  - an implied quadratic vertex at about 450-481 km (Oberhofer; derived from the fit, and the mean-distance effect is not significant).
- So model a concave form, not a linear points-per-km term. Candidates: d^(1/3), log(1 + d/d0), or a restricted spline.
- Proximity estimates are fragile to team composition (rugby sevens), so team or team-season fixed effects are required.

### 2.4 Conference tournaments and early-season events

Job C asks about both. **Both are literature gaps**: no opened source measures a proximity effect in either setting, in the Big Ten or elsewhere.

**Searches run in this pass (2026-10-17/18) and outcomes:**

| Search | Outcome |
|---|---|
| "conference tournament" proximity / home advantage, ACC tournament Greensboro, North Carolina schools win rate (extended web search) | No measured study. Hits were venue histories (Wikipedia ACC tournament pages; FanSided site list), regular-season home-edge analyses (Samford 2020 Power 5; mudvilleanalytics ACC home-road splits) and model pages that treat every conference-tournament round as neutral (TeamRankings ACC bracket). |
| College basketball conference tournament played in a team's home city, advantage study (extended web search) | No study of conference tournaments. Related: a 2024 NIT study (ResearchGate; not opened) about seeding-based true home games; a Butler undergraduate thesis (403 when opened). |
| "conference tournament" "home city"/"host city" with *Journal of Sports Economics* / *JQAS* (web search) | Nothing on conference tournaments. The search surfaced the Winthrop Intelligence PDF (Clay et al. summary), still blocked when opened. |
| Early-season multi-team events, neutral site, ATS, closer team (extended web search) | No analysis of November events against the spread; only VSiN and Action Network season or conference-tournament betting "trends" (not opened, not used). |
| ACC tournament out-of-state experiment (NC Sports Network, David Glenn; opened) | Venue history only: Greensboro has hosted 29 times; 10 of 19 ACC tournaments in 2005-24 were in North Carolina. No performance data. |

**What we have instead.**
- Conference tournaments: the Big Ten venue and distance tables in §9.3; the ACC venue history above; ESPN and CBBD flag these games as neutral, with `conferenceGame` true.
- Early-season events: StatsByWill descriptives (§2.2), with the attendance figures being the author's illustration; MSU's own November events in §9.1 (Champions Classic, Phil Knight, Acrisure, Maui, Fort Myers).
- **Natural experiments to exploit:** ACC tournaments in Greensboro vs out of state (2005-24 split above); Big East at Madison Square Garden (St. John's is in New York City; distance not computed); Big Ten 2024 Minneapolis and 2028 Las Vegas (new-8). These are listed in §11 as gaps to fill with our own data.

---

## 3. Effect estimates: points per 100 km and per log-distance

None of the opened sources gives a clean, peer-reviewed points-per-km figure for basketball neutral sites. The usable numbers:

| Source | Native form | Converted to our units |
|---|---|---|
| **COOPER 2025-26** (Silver Bulletin, opened) | Travel factor = 5·m^(1/3) Elo, m = the visiting team's miles from campus; 1 point ≈ 28.5 Elo (men). In km: 0.1497·d_km^(1/3) points | One team's trip: 50 km 0.55; 100 km 0.69; 200 km 0.88; 300 km 1.00; 500 km 1.19; 1,000 km 1.50; 2,000 km 1.89; 4,000 km 2.38; 7,000 km 2.86 points. Marginal value: about 0.11 points per 100 km near 300 km, and about 0.05 points per 100 km near 1,000 km. |
| **SBCB 2024-25** (Silver Bulletin, opened) | 8·m^(1/3) Elo; 1 point ≈ 27 Elo | 100 km 1.17; 500 km 2.01; 1,000 km 2.53; 2,000 km 3.19 points (about 1.6 times COOPER) |
| **FiveThirtyEight** | About +2 points at 161 km (100 mi); about −1 point at 2,414 km (1,500 mi) | **Unverified** (snippet only) |
| **Oberhofer et al.** (soccer) | −0.022 goals of goal difference per 100 km at the mean distance (368 km) (**p = 0.116 at the mean; Model B not significant**) | Not convertible to basketball points |
| **Ganz & Allsop** (NBA) | +1.17 to +1.38 points per 1,000 home fans | A crowd-size slope, not distance. It feeds the crowd-share model in §4. |
| **Beney** (college; Substack) | +0.48 points per 1,000 fans | Not peer-reviewed |

**Per log-distance (our derivation, not a published number).**
- Under the cube-root form, the points P(d) satisfy dP/d(ln d) = P/3. So the slope per unit of log-distance is one third of the current value.
- With COOPER weights, the slope is about 0.23 points per unit ln(d) at 100 km, 0.33 at 300 km and 0.50 at 1,000 km.
- **Doubling** a trip adds 26% (2^(1/3) − 1) of the current value: 100 → 200 km +0.18 points; 500 → 1,000 km +0.31; 1,000 → 2,000 km +0.39.
- For a log(1 + d/d0) fit on our data: about **0.52 points per unit of log(1 + d/100 km)** (about **0.42 per unit of ln d**), from our least-squares fit to the COOPER curve over 100-3,000 km on a 200-point log grid (recomputed in this pass). This replaces an earlier "0.3-0.4", which was an arithmetic error. Use it as a prior, not a target.

**Caution about these conversions.**
- COOPER documents its travel term for **home games**: the factor is added to the home team's team-specific home rating.
- SBCB says travel "also matters in neutral site games". Neither page says the neutral-site formula is "own factor minus opponent factor".
- The "COOPER-form edge" in §9 assumes that form, so treat it as a prior to test.
- The gap between two teams' trips works out to **about 0 to 1.3 points** under the COOPER form (largest MSU-game value 1.34 points, §9.1), and to well under 1 point for most Big Ten tournament pairings. This is the single range used in §1, §3 and §8; nothing verified supports values above it (the FiveThirtyEight +2 is unverified).

---

## 4. How crowd share is estimated

No opened source measures neutral-site crowd composition directly in college basketball. There are six usable approaches.

1. **Primary ticket allocations.**
   - NCAA men's tournament: the committee "allocates a pre-arranged number of game tickets to participating schools, regardless of the school's geographical location or national ranking", in equal quantity and quality for every school (Illinois Athletics ticket page, opened via curl).
   - UCLA's undated page (apparently 2011, Tampa) gives **350 tickets per participant** for the then "Second and Third Round". The current figure is not confirmed.
   - Because the primary allocation is equal, **differences in crowd share come from the public and secondary market**, where distance and fan-base size decide.
2. **Secondary-market buyer location.**
   - 2019 Final Four, Minneapolis (StubHub via CBS Sports, 4 Apr 2019): buyers from Minnesota 24%, Texas 15%, **Michigan 8%** (MSU was playing), Virginia 6%, Illinois 4%, Alabama 4%.
   - 2026 Final Four, Indianapolis (SeatGeek via Yahoo/Forbes, 1 Apr 2026):
     - **Illinois 40%**, Indiana 10%, Michigan 7%.
     - Illinois's arena is 182 km from Indianapolis. Michigan, a No. 1 seed, was also playing, from 344 km.
     - TickPick: Illinois and Arizona fans together made up almost 40% of purchases.
   - Academic use: Rishe, Reese & Boyle (2015, *IJSF* 10: 357-374, opened) used the distance from the event to each buyer's ZIP code in bowl-game resale data.
     - Buyers from the Los Angeles area paid markups **88 percentage points lower** (Model 2B, LOCAL).
     - **Michigan buyers at the 2014 Rose Bowl (MSU) paid markups 147-160 percentage points higher** (Models 2B and 2C; TicketCity subsample, n = 377 transactions across both bowls; **21 Michigan buyers**, 32% of TicketCity's 65 Rose Bowl transactions).
     - Distance slope (Model 2C, DIST): markups **increase** by about 3 percentage points per 100 mi farther the buyer lives from Pasadena, i.e. about **+1.9 pp per 100 km** (coefficient 0.00029 per mile, p = 0.0001). Note the sign: among people who did buy, those from farther away paid more. This is a willingness-to-pay gradient, not distance decay in how many fans attend, so it does **not** calibrate the decay term of the gravity model in §8; it does warn that a buyer-price proxy would move the opposite way to a turnout proxy.
     - They cite Rishe, Mondello & Boyle (2014, *Sport Marketing Quarterly* 23: 148-160): resale behaviour at the 2013 tournament regionals depended on team quality and **the school's proximity to the host site**. That finding is secondhand and **unverified**.
   - Caveat: buyer state is not fan identity, and one platform is not the whole market.
3. **Distance-decay ("gravity") proxy.** This is what we would compute. See §8 for the formula.
   - Each fan base's expected turnout is w_i = S_i · f(d_i). S_i is the fan-base size, d_i the great-circle distance from the team's home arena to the venue, and f = exp(−d/d0) or d^(−β).
   - Crowd share for team A = w_A / (w_A + w_B + w_local).
   - d0 or β is estimated inside the model by profile likelihood (§8); published buyer-state shares serve only as an external check, not for calibration. COOPER's travel term is effectively a reduced form of this model.
   - Sources for S_i:
     - (a) Facebook-likes share by ZIP code, as in the NYT Upshot maps. The 2014 football article (opened) used "each team's share of Facebook 'likes' in a ZIP code" with smoothing, and found that likes "show broadly similar patterns to polls". Facebook also published a 2013 county-level March Madness map (68 teams, 3,140 counties; Deadspin, opened). This data is no longer publicly exposed.
     - (b) Alumni counts. MSU reports over 576,000 living alumni: **unverified** (snippet only; the MSU licensing page returned 404).
     - (c) Enrolment and home attendance.
4. **Time zones and day of week.**
   - These lower travelling-fan turnout and add a circadian effect for players (§5).
   - TeamRankings (2012) found more "midweek" turnovers and more midweek Unders, where midweek means Tuesday, Thursday and Friday games vs Saturday/Sunday and championship games: 110 of 204 midweek games went Under, while 59 of 98 weekend games went Over.
5. **Observed attendance and its composition.**
   - The ESPN `attendance` field and the CBBD `attendance` field give total size (both checked).
   - Measuring the share requires video or audio. This connects to the requirements items "Crowd loudness as a possible home-crowd measure" and "Crowd loudness curve". Proposed operational definitions (our proposals, to be validated):
     - **Crowd colour share (video).** Frames: broadcast frames where the stands occupy at least 20% of the image, detected as pixels outside the projected court polygon (28.65 m × 15.24 m, from the court homography) and outside the bench and baseline areas within 2 m of the court edge. Region of interest: those seat-region pixels. Rule: a pixel counts for team X if its hue is within ±15° of team X's primary colour (HSV hue, 0-360°), saturation ≥ 0.35 and value ≥ 0.25. Crowd share_X = count_X / (count_A + count_B), averaged over at least 30 qualifying frames sampled at ≥ 10 s spacing across the game. Teams whose primary hues are within 30° of each other are excluded (ambiguous).
     - **Noise response (audio).** For each made basket or made free throw by team X: mean A-weighted sound level LAeq (dB, broadcast audio, uncalibrated, so only within-game differences are used) over 0 to 5 s after the event, minus LAeq over the 10 s before it. Noise asymmetry = mean response to team A's events − mean response to team B's events, in dB. Free throws and field goals reported separately; events within 10 s of a timeout or period end excluded.
     - **Run.** An unanswered scoring spurt of ≥ 8 points by one team within ≤ 180 s of game clock; run response = LAeq over the run's last 10 s minus LAeq over the 10 s before the run started.
     - **Chant asymmetry** is not operationalised here (it needs speech or chant classification); left as an open item.
   - Evidence that crowd effects work through referees: van Bommel et al. (bias grows with attendance) and Ponzo & Scoppa (sanctions). Ganz & Allsop found no foul effect in the NBA, so this channel is contested.
   - Free throws: van Bommel et al. find neutral D1 teams shoot slightly *better* from the line than home teams, so a crowd effect on FT% is weakly supported at best (see new-4).
6. **Rating-system conventions** (§6) are a cheap proxy.
   - KenPom applies half the home advantage in "semi-neutral" games: **unverified**.
   - ESPN BPI uses the difference in distance travelled and notes that the closer team "will tend to have an advantage in the rooting of the crowd".

---

## 5. Time-zone effects

| Source | Setting | Finding | Status |
|---|---|---|---|
| **Leota et al. (2022),** *Front. Physiol.* 13:892681 | 11,481 NBA games, 2011-12 to 2020-21 | Eastward jet lag for **home** teams just back from a trip cost −1.29 points of margin (p = 0.015) and −6.03 percentage points of win rate (**marginal, p = 0.051**; the abstract calls it marginal), with a dose-response by hours of shift. **No effect on away teams** (game outcome p > 0.136; margin p > 0.294). Distance was not modelled; halves were not studied. Because the effect is for home teams only, the case for an eastward effect on teams **at a neutral site** rests mainly on the unverified Clay et al. snippet and on football evidence. | Peer-reviewed, opened |
| **Nichols (2014),** *J. Sports Economics* 15(1): 78-96 | NFL 1981-2004 | A visitor crossing at least one time zone eastward raises the home team's win probability, growing with distance at a diminishing rate. Bettors under-estimate the home score, but there is no profitable out-of-sample strategy. | Peer-reviewed (abstract opened) |
| **Fodor & Krieger (2014),** *J. Gambling, Business and Economics* 8(1): 41-52 | NFL 2005-2010 | Closing lines do not reflect jet lag. Betting against jet-lagged teams was "markedly profitable" and significant. No ROI figure given. | Peer-reviewed (abstract opened) |
| **Coleman (2017),** *J. Sports Economics* 18(4): 388-425 | College football | The market is "an inaccurate and inefficient processor of travel effects", most consistently for late-season underdogs facing a 1 h time deficit. Sample size not shown. | Peer-reviewed (abstract opened) |
| **Clay, Bro & Clay (2015)** | NCAA tournament, 1985-2011 | Eastward time-zone travel "significantly reduces the odds of winning" (Winthrop Intelligence snippet only). The earlier "odds ratio about 0.861" is **UNSOURCED** and withdrawn. | **Unverified** (snippet; full text and Winthrop PDF not readable) |
| **Williams (2025)** | NCAA tournament lines, 2008-2012 | −2.99 points of total per time zone crossed; no link with the spread | Undergraduate, opened |
| **Delbianco et al. (2026)** | Rugby sevens | Team-specific distance gradients, partly through east-west jet lag | Preprint, opened |

**Computation.**
- tz_shift_s = venue UTC offset − home-arena UTC offset **on the game date** (evaluated at local noon at the venue), in seconds, using IANA zone names so daylight saving time is handled. Positive means the team travelled east. Tables show tz_shift_h = tz_shift_s / 3,600. Implemented in `docs/research/neutral_site_proximity_assets/compute_distances.py`.
- America/Phoenix has no DST, and Pacific/Honolulu has no DST.

**MSU exposure (§9).**
- Almost all of MSU's neutral-site games are within ±1 h; the exceptions are West Coast and Maui events (−3 to −5 h, westward).
- Opponents from the West travelling east to MSU's NCAA and Big Ten sites took +2 to +3 h eastward shifts: USC 2023, Oregon 2025, New Mexico 2025, UCLA 2026.

**Relation to H10.**
- Requirements H10 states that "Travel distance and time zones crossed lower first-half efficiency".
- The neutral-site version would separate the two channels: distance (via crowd share) and eastward shift (circadian).
- Proposed as new-5 in §10, as an extension of H10, not a replacement. new-5's first-half focus comes from H10, not from Leota et al. (who did not study halves).

---

## 6. How rating systems and the betting market adjust

| System | How it handles location | Status |
|---|---|---|
| **Silver Bulletin COOPER (2025-26)** | Margin-based, Elo-like, with team-specific home-court ratings and a travel factor of 5·m^(1/3) Elo (m = the visitor's miles); 1 point ≈ 28.5 Elo; in km, 0.1497·d_km^(1/3) points. Purdue's home court is worth about 2 points above the Division I average. The travel effect was "much larger up through the 1980s". The 2026 bracket model blends 5/8 COOPER with 3/8 KenPom and accounts for "injuries, travel distance". | Opened |
| **SBCB (2024-25)** | Travel 8·m^(1/3) Elo; 1 point ≈ 27 Elo. "Travel distance also matters in neutral site games", and "the effect of travel distance is gradually becoming smaller". Altitude schools (Utah, Colorado) have larger home advantage. Home ratings carry over fully between seasons. | Opened |
| **FiveThirtyEight (2017)** | "ratings are also adjusted for travel distance"; no magnitude given (Poynter summary). | Opened (secondary) |
| **ESPN BPI** | "accounts for team strength, opponent strength and game site", days of rest, "difference in distance traveled from home and high-altitude effects". Distance is "especially useful for neutral-site games … the closer team will tend to have an advantage in the rooting of the crowd" (ESPN Stats & Info, 8 Nov 2016). No weights published. | Opened |
| **KenPom** | Snippets say neutral games where the listed home team still gets an edge are marked with a lowercase "n", with "half of the stated home court advantage" applied in "semi-neutral" games. Another snippet says the point-spread home-court method "doesn't include a travel component" (the Hawaii example). Team-specific home-court advantage uses home-foul advantage and elevation. `docs/research/odds_markets_research.md` records a flat home edge of about 3.75 points (2014 methodology update). | **Unverified**: kenpom.com returned 403 to WebFetch and a Cloudflare page to curl |
| **Bart Torvik T-Rank** | Home games adjust each team's AdjOE and AdjDE by 1.4%. A neutral court is the baseline, and **no proximity term** is described. Recency weighting: games in the last 40 days count 100%, declining 1% per day to 60% at 80 days. | Opened (T-Rank FAQ; undated) |
| **Betting market** | No direct study of proximity residuals controlling for quality in NCAA basketball. Williams 2025 found no relationship between travel and tournament lines (n = 327; undergraduate); this is a null result, not evidence that lines absorb distance. Coleman 2017 and Fodor & Krieger 2014 report travel and jet-lag inefficiencies in football lines (abstracts only); Nichols 2014 is mixed evidence (a bias, but not exploitable out of sample). The TeamRankings cover split (55% vs 43%) is consistent with zero. No sportsbook source describing a "proximity adjustment" was found. | **Belief status: probably partly priced; the residual is untested** |

Covers' explainer on Torvik ratings (opened) gives no location detail, which confirms the gap.

**Consequence for benchmarks.** Ratings that include travel (COOPER, BPI) and ratings that do not (Torvik; probably KenPom) give different expectations at neutral sites. We should test against both kinds and against the closing spread. A proximity effect that survives the closing line is the only kind with market value.

---

## 7. Venue and campus coordinates, and the distance method

### 7.1 Coordinate sources

| Source | What it gives | Coordinates? | Notes |
|---|---|---|---|
| **Wikidata P625** (coordinate location), via `wbgetentities` | Coordinates for arenas, venues and universities, with stable QIDs | **Yes** | Worked for all 73 entities queried in the first pass and all 58 entities in this pass. **Recommended primary source.** The entities, QIDs, coordinates and IANA zones used for §9.1 and §9.3 are listed in **Appendix A** and in `docs/research/neutral_site_proximity_assets/entities.tsv`. |
| **Wikipedia MediaWiki API**, `prop=coordinates` | Page coordinates and Wikidata QIDs | Yes | Returns at most 10 coordinates per request by default. Pass `colimit=max` or fall back to Wikidata. |
| **ESPN site API** (scoreboard, summary) | `venue.id` (e.g. KeyBank Center = "1848"), `fullName`, city and state, `neutralSite: true`, `attendance` (MSU vs NDSU, 19 Mar 2026: 17,182) | No | Join key only |
| **ESPN core API** `/venues/{id}` | Name, city, state, indoor and grass flags | **No latitude or longitude** | Geocode via Wikidata |
| **CBBD** (College Basketball Data API v1.30.1, OpenAPI spec) | `GET /venues` returns `VenueInfo {id, sourceId, name, city, state, country}`. `GameInfo` includes `neutralSite`, `conferenceGame`, `tournament`, `attendance`, `venueId`, `venue`, `city`, `state`, Elo start and end. `TeamInfo` includes `currentVenueId` and `currentVenue`. | **No** | Needs an API key. The free tier of about 1,000 calls per month is **unverified** (snippet). |
| **NCAA.org bracketing explainer** (12 Mar 2025) | "Teams are placed as close to home as possible to maximize fan accessibility". A team cannot play in a facility where it has played more than three games in a season, or where it is the host. Opening Round in Dayton or Wichita. | No | Explains the seed and distance confound |
| **NBC Sports Boston** (18 Mar 2026) | 2027-2028 NCAA sites by round; Final Fours for 2029 (Indianapolis), 2030 (Arlington) and 2031 (Atlanta) | No | The article misspells Dayton as "Daytona" |
| **Kaggle March Machine Learning Mania**, `Cities` / `MGameCities` | Game-to-city mapping | No | **Unverified**: the data page did not render |
| **Wikipedia season pages** (`{{CBB schedule entry}}` templates) | `neutral=yes`, `site_stadium`, `site_cityst`, `attend`, `gamename` | No | Good cross-check; §9 was built from it |

**Pitfall: "campus" points.**
- University items can sit kilometres from the arena.
- MSU's Wikidata item (Q270222: 42.70186, −84.48216) is 3.0 km from the Breslin Center (Q2924511: 42.728227, −84.492396).
- The Wikipedia infobox point (42.725, −84.48) is 1.1 km from Breslin.
- **Rule:** use each team's **home arena** item as its origin and store the QID. As of this pass, §9.1 and §9.3 use home-arena items for every team (Appendix A). Arena moves are dated: Baylor's 2023-12-16 origin is the Ferrell Center (Foster Pavilion, "completed in 2024", replaced it; Wikipedia Foster Pavilion page, Source 67); UConn's origin is Gampel Pavilion although UConn also plays at the XL Center in Hartford (about 35 km away; not computed).

### 7.2 Distance method (canonical: WGS84 geodesic; check: haversine)

- **Canonical: geodesic distance on the WGS84 ellipsoid** (Vincenty inverse formula; the script falls back to haversine if Vincenty fails to converge, which happens only for near-antipodal points). All tables in §9 use it. An earlier draft called haversine "primary" while the tables used Vincenty; this pass makes the geodesic canonical.
- **Script:** `docs/research/neutral_site_proximity_assets/compute_distances.py` (standard library only; input `entities.tsv`, built by `resolve_qids.py` from `entities_seed.tsv`; output saved as `compute_distances_output.txt`). Run with `python3 -I compute_distances.py entities.tsv`. The coordinator may move these files to a scripts area.
- **Check: haversine** on a sphere with mean radius R = 6,371.0088 km:

  ```
  h = sin²((φ2 − φ1)/2) + cos φ1 · cos φ2 · sin²((λ2 − λ1)/2)
  d_km = 2 · R · asin(√h)
  ```

- **Haversine vs geodesic.**
  - The measured difference on MSU routes is ≤ 0.3%. Examples: T-Mobile Arena 2,720.4 km haversine vs 2,726.3 km geodesic; United Center 278.1 vs 278.7 km. The script prints both.
  - That difference is negligible next to the uncertainty in the effect.
  - `geographiclib` and `pyproj` are not installed, so Vincenty is implemented in the script directly.
- **Fields per team per game:** `d_team_m`, `d_opp_m`, `d_diff_m = d_opp_m − d_team_m`, `tz_shift_team_s`, `tz_shift_opp_s` (displayed as km and h), plus the venue QID, origin QID and their coordinates.
- **Limits of great-circle distance.**
  - It stands in for both fan travel cost and team fatigue.
  - How the team travelled (bus vs charter) is in no public feed. Requirements keeps "bus vs flight" as a separate field.
  - Road distance or drive time would be a better fan-cost proxy for short trips under about 500 km. That is an open option, not proposed now.

---

## 8. Proposed model for our data

**Design rule.** Fit on every Division I neutral-site game, stratified by event type, then apply the fitted curve to MSU. MSU-only results are descriptive (small-sample rule in `docs/requirements.md`).

**Data.**
- Games: CBBD (`neutralSite`, `venueId`, `tournament`, `attendance`), cross-checked against the ESPN `neutralSite` flag and `homeAway` field.
- Coordinates: Wikidata P625 for venues and home arenas.
- Closing spreads: ESPN core odds API or CBBD `/lines`, per `docs/research/odds_markets_research.md`.
- Pre-game ratings: Torvik (no travel term) and, where available, a travel-inclusive rating.

**Outcome.** For team A vs team B at a neutral venue:

- y₁ = margin_A + closing_spread_A, i.e. the margin against the line (the spread is negative for the favourite). This is the market test.
- y₂ = margin_A − rating-implied neutral margin_A, i.e. the margin against a rating model. This is the rating test.

**Main specification.**

```
y = β · [f(d_B) − f(d_A)]
  + γ_E · [max(tz_B, 0) − max(tz_A, 0)]   # eastward shift, hours
  + γ_W · [min(tz_B, 0) − min(tz_A, 0)]   # westward shift, hours
  + δ_stratum                              # NCAA / conference tournament / early-season event / other (rules below)
  + u_team-season(A) − u_team-season(B)    # team-season effects
  + ε
```

**Stratum and flag rules (runnable on CBBD and ESPN fields; thresholds to be varied in a sensitivity analysis).**
- **NCAA:** CBBD `tournament` equals the NCAA men's tournament value (First Four included as its own sub-stratum).
- **Conference tournament:** CBBD `conferenceGame` true AND `neutralSite` true AND the game date falls in the postseason window (on or after the first day of that conference's tournament, i.e. after the conference's last regular-season game date).
- **Early-season event:** `neutralSite` true AND `conferenceGame` false AND game date before 1 January of the season AND not NCAA/NIT/CBI.
- **Other:** every remaining neutral-site game (e.g. December showcases, NIT and other postseason events).
- **Designated home flag:** ESPN `neutralSite` false despite a venue that is not the listed home team's home arena (Appendix A or CBBD `currentVenueId`), OR ESPN/CBBD `neutralSite` true with d_team < 50 km while d_opp > 150 km. Flagged games are run with and without.
- **Sensitivity:** repeat the fit with the early-season cut-off at 1 December and 15 January, and the designated-home thresholds at 25/100 km and 100/300 km.

**The distance curve f.**
- Fit three forms and compare by out-of-sample log-loss and margin RMSE:
  - f(d) = d^(1/3), the COOPER form, with COOPER's 5/28.5 points per mi^(1/3) (0.1497 points per km^(1/3)) as the prior;
  - f(d) = log(1 + d/d0), with d0 = 100 km and a prior slope of about 0.52 points per unit (§3);
  - a restricted cubic spline with knots at 100, 300, 800 and 2,000 km.
- Report the implied points at 100, 300, 500, 1,000 and 2,000 km, plus the slope per 100 km at 300 km.

**Crowd-share variant (mechanism test).**
- Replace f(d) with modelled crowd share:

  ```
  s_A = S_A · exp(−d_A/d0) / (S_A · exp(−d_A/d0) + S_B · exp(−d_B/d0) + L)
  ```

  - S = fan-base size proxy (home attendance or enrolment).
  - L = a local-neutral constant.
  - d0 is treated as a **prior range of 150-600 km** and **estimated inside the model by profile likelihood on y₁** (grid over d0, refit the rest, keep the likelihood profile and its 95% interval).
  - The 2019 and 2026 Final Four buyer-state shares are used only as an **external check**, not for calibration: two events give a handful of points, buyer state is not fan identity (§4), and Final Fours are unlike first-round, conference-tournament or November games. Rishe et al.'s positive price-distance slope (§4) is not a turnout measure and is not used.
- Then regress y on (s_A − s_B) × attendance / 1,000. For scale only, two outside figures exist, and neither transfers directly to college neutral sites:
  - Beney: 0.48 points per 1,000 fans (**descriptive, non-peer-reviewed**; r = 0.26; internally inconsistent figures, §2.2);
  - Ganz & Allsop: 1.17-1.38 points per 1,000 fans (**valid only at low attendance**, NBA 2020-21 capacity caps of at most a few thousand fans; not extrapolable to crowds of 10,000-20,000).

**Referee-channel outcomes.** Free-throw attempt differential and personal-foul differential per 100 possessions, against the same terms (new-3).

**Controls and checks.**
- Days of rest.
- Altitude of the venue minus altitude of the home arena (Van Damme & Baert; SBCB).
- Hawaii and Alaska events treated as their own stratum, because the distances are extreme and both teams travel far.
- Designated-home "neutral" games flagged by the rule above (e.g. Rutgers at Madison Square Garden, 2023-02-04, which ESPN codes as a Rutgers home game) and run with and without.
- A season interaction, to test the decline (new-7).

**Pre-registered expectations (priors from §3).**
- β implies about 0 to 1.3 points across the observed range of gaps, and under about 1 point for a typical gap of a few hundred km (§3).
- The closing-line residual is near zero.
- Any residual is largest in early-season events, where lines are set with less information and crowds are small. This is a guess to test, not a finding.

**Big Ten natural experiment.**
- The tournament moves from Indianapolis in 2027 to Las Vegas in 2028.
- That flips which members are closest: USC 365 km, UCLA 374 km, Oregon 1,108 km and Washington 1,411 km from T-Mobile Arena, vs MSU 2,726 km.
- This gives a within-conference before-and-after test (new-8).

---

## 9. MSU neutral-site games 2022-23 to 2025-26, and Big Ten tournament venues

### 9.1 MSU neutral-site games with computed distances

Games are those marked `neutral=yes` on the Wikipedia MSU season pages.

**How the table was computed** (recomputed in this pass; script `docs/research/neutral_site_proximity_assets/compute_distances.py`, output `compute_distances_output.txt`).
- Coordinates: Wikidata P625 for the venues and for **every team's home arena** (Appendix A). The first draft used university items for opponents; the change moves opponent distances by at most about 11 km (Memphis) and changes no edge by more than 0.01 points.
- Distances: WGS84 geodesic (Vincenty), in km.
- tz shift: venue UTC offset minus home-arena UTC offset at local noon on the game date (positive = east), stored in seconds and shown in hours.
- COOPER-form edge to MSU = 0.1497·[d_opp_km^(1/3) − d_MSU_km^(1/3)] points (= 5·[(d_opp in mi)^(1/3) − (d_MSU in mi)^(1/3)] / 28.5). The neutral-site form is **our assumption** (§3).
- Designated home: checked against the ESPN scoreboard API (`neutralSite`, `homeAway`) in this pass.

**Caveats.**
- "Rutgers at MSG" (Big Ten Super Saturday, 2023-02-04): Wikipedia lists it as neutral, but **ESPN codes it `neutralSite: false` with Rutgers as the home team** (event 401484931). It is a designated-home game.
- The two Oakland games at Little Caesars Arena: ESPN codes both `neutralSite: true` (Oakland listed home in 2024, MSU in 2025). Whether either was a designated home game for ticketing or crowd purposes is **unverified**.
- 2025-11-27 vs North Carolina: the ESPN summary (event 401817267) gives **74-58** (halves 33-28 and 41-30), matching Wikipedia. A verifier reported that the msuspartans.com recap headline says 72-58; that page was not re-opened in this pass, and the ESPN box score is taken as official.
- The Gonzaga game was played on the USS Abraham Lincoln in San Diego; its coordinates use NAS North Island.

| Date | Event | Venue | Opponent (origin arena) | d_MSU (km) | d_opp (km) | d_opp − d_MSU (km) | MSU tz (h) | Opp tz (h) | COOPER-form edge to MSU (pts) | Result (MSU–Opp) | designated_home? |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2022-11-11 | Armed Forces Classic | USS Abraham Lincoln, San Diego (NAS North Island point) | Gonzaga (McCarthey Athletic Center) | 3,069 | 1,662 | −1,407 | −3 | 0 | −0.40 | 63-64 | No |
| 2022-11-15 | Champions Classic | Gainbridge Fieldhouse | Kentucky (Rupp Arena) | 357 | 238 | −119 | 0 | 0 | −0.13 | 86-77 | No |
| 2022-11-24 | Phil Knight Inv. QF | Moda Center | Alabama (Coleman Coliseum) | 3,042 | 3,288 | +246 | −3 | −2 | +0.06 | 70-81 | No |
| 2022-11-25 | PKI consolation | Veterans Memorial Coliseum, Portland | Oregon (Matthew Knight Arena) | 3,042 | 168 | −2,874 | −3 | 0 | −1.34 | 74-70 | No |
| 2023-02-04 | B1G Super Saturday | Madison Square Garden | Rutgers (Jersey Mike's Arena) | 900 | 45 | −855 | 0 | 0 | −0.91 | 55-61 | **Yes** (ESPN neutralSite=false; Rutgers home) |
| 2023-03-10 | B1G Tourn QF | United Center | Ohio State (Value City Arena) | 279 | 443 | +165 | −1 | −1 | +0.16 | 58-68 | No |
| 2023-03-17 | NCAA R64 | Nationwide Arena | USC (Galen Center) | 331 | 3,187 | +2,856 | 0 | +3 | +1.17 | 72-62 | No |
| 2023-03-19 | NCAA R32 | Nationwide Arena | Marquette (Fiserv Forum) | 331 | 534 | +203 | 0 | +1 | +0.18 | 69-60 | No |
| 2023-03-23 | NCAA S16 | Madison Square Garden | Kansas State (Bramlage Coliseum) | 900 | 1,933 | +1,033 | 0 | +1 | +0.42 | 93-98 | No |
| 2023-11-14 | Champions Classic | United Center | Duke (Cameron Indoor Stadium) | 279 | 999 | +720 | −1 | −1 | +0.52 | 65-74 | No |
| 2023-11-23 | Acrisure Classic | Acrisure Arena | Arizona (McKale Center) | 2,938 | 532 | −2,406 | −3 | −1 | −0.93 | 68-74 | No |
| 2023-12-16 | Motor City Inv. | Little Caesars Arena | Baylor (Ferrell Center) | 126 | 1,728 | +1,602 | 0 | +1 | +1.05 | 88-64 | No (ESPN neutralSite=true; MSU listed home) |
| 2024-03-14 | B1G Tourn R2 | Target Center | Minnesota (Williams Arena) | 749 | 4 | −745 | −1 | 0 | −1.13 | 77-67 | No |
| 2024-03-15 | B1G Tourn QF | Target Center | Purdue (Mackey Arena) | 749 | 725 | −24 | −1 | −1 | −0.01 | 62-67 | No |
| 2024-03-21 | NCAA R64 | Spectrum Center | Mississippi State (Humphrey Coliseum) | 891 | 757 | −133 | 0 | +1 | −0.08 | 69-51 | No |
| 2024-03-23 | NCAA R32 | Spectrum Center | North Carolina (Dean Smith Center) | 891 | 179 | −712 | 0 | 0 | −0.60 | 69-85 | No |
| 2024-11-12 | Champions Classic | State Farm Arena | Kansas (Allen Fieldhouse) | 996 | 1,131 | +135 | 0 | +1 | +0.06 | 69-77 | No |
| 2024-11-25 | Maui QF | Lahaina Civic Center | Colorado (CU Events Center) | 7,030 | 5,288 | −1,742 | −5 | −3 | −0.26 | 72-56 | No |
| 2024-11-26 | Maui SF | Lahaina Civic Center | Memphis (FedExForum) | 7,030 | 6,620 | −410 | −5 | −4 | −0.06 | 63-71 | No |
| 2024-11-27 | Maui 3rd | Lahaina Civic Center | North Carolina (Dean Smith Center) | 7,030 | 7,597 | +567 | −5 | −5 | +0.08 | 94-91 | No |
| 2024-12-17 | Detroit neutral | Little Caesars Arena | Oakland (Athletics Center O'rena) | 126 | 39 | −86 | 0 | 0 | −0.24 | 77-58 | Unverified (ESPN neutralSite=true; Oakland listed home) |
| 2025-03-14 | B1G Tourn QF | Gainbridge Fieldhouse | Oregon (Matthew Knight Arena) | 357 | 3,073 | +2,716 | 0 | +3 | +1.11 | 74-64 | No |
| 2025-03-15 | B1G Tourn SF | Gainbridge Fieldhouse | Wisconsin (Kohl Center) | 357 | 456 | +99 | 0 | +1 | +0.09 | 74-77 | No |
| 2025-03-21 | NCAA R64 | Rocket Arena | Bryant (Chace Athletic Center) | 269 | 845 | +576 | 0 | 0 | +0.45 | 87-62 | No |
| 2025-03-23 | NCAA R32 | Rocket Arena | New Mexico (The Pit) | 269 | 2,287 | +2,017 | 0 | +2 | +1.01 | 71-63 | No |
| 2025-03-28 | NCAA S16 | State Farm Arena | Ole Miss (The Sandy and John Black Pavilion at Ole Miss) | 996 | 479 | −517 | 0 | +1 | −0.32 | 73-70 | No |
| 2025-03-30 | NCAA E8 | State Farm Arena | Auburn (Neville Arena) | 996 | 164 | −832 | 0 | +1 | −0.68 | 64-70 | No |
| 2025-11-18 | Champions Classic | Madison Square Garden | Kentucky (Rupp Arena) | 900 | 953 | +53 | 0 | 0 | +0.03 | 83-66 | No |
| 2025-11-25 | Fort Myers Tip-Off | Suncoast Credit Union Arena | East Carolina (Minges Coliseum) | 1,811 | 1,092 | −719 | 0 | 0 | −0.28 | 89-56 | No |
| 2025-11-27 | Fort Myers Tip-Off | Suncoast Credit Union Arena | North Carolina (Dean Smith Center) | 1,811 | 1,072 | −739 | 0 | 0 | −0.29 | 74-58 | No |
| 2025-12-20 | Motown Showdown | Little Caesars Arena | Oakland (Athletics Center O'rena) | 126 | 39 | −86 | 0 | 0 | −0.24 | 79-70 | Unverified (ESPN neutralSite=true; MSU listed home) |
| 2026-03-13 | B1G Tourn QF | United Center | UCLA (Pauley Pavilion) | 279 | 2,822 | +2,543 | −1 | +2 | +1.14 | 84-88 | No |
| 2026-03-19 | NCAA R64 | KeyBank Center | North Dakota State (Scheels Center) | 460 | 1,481 | +1,021 | 0 | +1 | +0.55 | 92-67 | No |
| 2026-03-21 | NCAA R32 | KeyBank Center | Louisville (KFC Yum! Center) | 460 | 775 | +316 | 0 | 0 | +0.22 | 77-69 | No |
| 2026-03-27 | NCAA S16 | Capital One Arena | UConn (Harry A. Gampel Pavilion) | 760 | 518 | −242 | 0 | 0 | −0.16 | 63-67 | No |

**Descriptive observations** (n = 35; no inference):
- Attendance ranges from 2,400 (Maui, Lahaina Civic Center) to 19,624 (Madison Square Garden, Sweet 16, 2023). Not affected by the designated-home flags.
- MSU record by sign of the COOPER-form edge (descriptive only, quality not controlled):
  - all 35 games: edge > 0, 10-7 (mean margin +5.2); edge < 0, 10-8 (mean margin +4.7);
  - without the three flagged games (Rutgers at MSG; both Oakland games at Little Caesars Arena), n = 32: edge > 0, 10-7 (+5.2); edge < 0, 8-7 (+4.2).
  - No pattern is visible at this sample size, as expected.
- MSU's first-weekend NCAA sites were 269-460 km away in 2023, 2025 and 2026, against opponents 534-3,187 km away.
- In later rounds the edge flips against MSU: the 2025 Sweet 16 and Elite Eight in Atlanta, and the 2026 Sweet 16 in Washington. Higher-seeded or southern opponents were placed nearer.

### 9.2 Future MSU-relevant venues (distance from the Breslin Center)

- **First Four** (Dayton, UD Arena): 333 km.
- **2027:**
  - Final Four at Ford Field: 126 km.
  - First and second rounds: Pittsburgh 453; Louisville 508; Minneapolis 749; Charlotte 891; Omaha 961; Fort Worth 1,583; Spokane 2,624; Sacramento 3,138 km.
  - Regionals: New York 900; Kansas City 940; San Antonio 1,933; Los Angeles 3,081 km.
- **2028:**
  - First and second rounds: Columbus 331; Des Moines 764; Brooklyn 904; Birmingham 1,042; Tulsa 1,228; Orlando 1,599; Salt Lake City 2,280; Seattle 2,995 km.
  - Regionals: Detroit (Little Caesars Arena) 126; Raleigh 915; Dallas 1,544; San Francisco 3,243 km.
  - Final Four at Las Vegas (Allegiant Stadium): 2,727 km.

### 9.3 Big Ten tournament venues

**Host history** (Wikipedia "Big Ten men's basketball tournament", read via the MediaWiki API):

| Years | Host |
|---|---|
| 1998-2001 | Chicago (United Center) |
| 2002-2007 | Alternated between Chicago and Indianapolis (Conseco/Bankers Life, now Gainbridge Fieldhouse) |
| 2008-2012 | Indianapolis |
| 2013-2016 | Alternated between Chicago and Indianapolis |
| 2017 | Washington DC (Verizon, now Capital One, Center) |
| 2018 | Madison Square Garden, a week early |
| 2019 | Chicago (United Center) |
| 2020 | Indianapolis (Bankers Life, now Gainbridge, Fieldhouse); cancelled after the first round (COVID) |
| 2021 | Indianapolis (Lucas Oil Stadium; moved from Chicago, COVID) |
| 2022 | Indianapolis (Gainbridge Fieldhouse) |
| 2023 | Chicago |
| **2024** | **Minneapolis (Target Center), the first time there** |
| **2025** | **Indianapolis (Gainbridge Fieldhouse)** |
| **2026** | **Chicago (United Center)** |
| **2027** | **Indianapolis (Gainbridge Fieldhouse)** |
| **2028** | **Las Vegas (T-Mobile Arena), the first time there** |

The 2025-28 sites come from a Big Ten announcement of 31 Jul 2024, as cited on Wikipedia. The bigten.org page returned 404, so they are confirmed only via Wikipedia.

**Distances from each school's home arena** (Wikidata P625, QIDs in Appendix A; WGS84 geodesic; km; recomputed in this pass with identical results):

| School (home arena) | Chicago, United Center (2026) | Indianapolis, Gainbridge (2025, 2027) | Las Vegas, T-Mobile (2028) | Minneapolis, Target Center (2024) |
|---|---|---|---|---|
| Illinois (State Farm Center) | 204 | 182 | 2,395 | 682 |
| Indiana (Simon Skjodt Assembly Hall) | 315 | 72 | 2,541 | 852 |
| Iowa (Carver-Hawkeye Arena) | 323 | 502 | 2,133 | 394 |
| Maryland (Xfinity Center) | 965 | 798 | 3,369 | 1,504 |
| Michigan (Crisler Center) | 328 | 344 | 2,783 | 826 |
| **Michigan State (Breslin Center)** | **279** | **357** | **2,726** | **749** |
| Minnesota (Williams Arena) | 566 | 821 | 2,095 | 4 |
| Nebraska (Pinnacle Bank Arena) | 765 | 905 | 1,691 | 541 |
| Northwestern (Welsh-Ryan Arena) | 21 | 287 | 2,457 | 555 |
| Ohio State (Value City Arena) | 443 | 269 | 2,839 | 1,006 |
| Oregon (Matthew Knight Arena) | 2,875 | 3,073 | 1,108 | 2,358 |
| Penn State (Bryce Jordan Center) | 830 | 715 | 3,274 | 1,339 |
| Purdue (Mackey Arena) | 173 | 99 | 2,508 | 725 |
| Rutgers (Jersey Mike's Arena) | 1,119 | 1,001 | 3,564 | 1,615 |
| UCLA (Pauley Pavilion) | 2,822 | 2,929 | 374 | 2,465 |
| USC (Galen Center) | 2,810 | 2,917 | 365 | 2,456 |
| Washington (Hec Edmundson Pavilion) | 2,790 | 3,012 | 1,411 | 2,242 |
| Wisconsin (Kohl Center) | 194 | 456 | 2,335 | 376 |

**MSU's distance rank among the 18 schools:**
- Chicago: 5th.
- Indianapolis: 7th.
- Minneapolis: 8th.
- Las Vegas: 13th.

No opened source measures proximity effects in the Big Ten tournament specifically, or in any other conference tournament (searches in §2.4).

---

## 10. Proposed hypotheses (new IDs)

JEV hypotheses keep the last numbers, so these IDs are provisional for the requirements session to renumber. Every one follows the rule: fit on all Division I neutral-site games, then apply to MSU.

| ID | Statement | Measure | Data | PBP only, or video? | Priced by the market? |
|---|---|---|---|---|---|
| new-1 | At neutral sites, the team closer to the venue beats the closing spread by a concave function of the distance gap | Margin against the line regressed on f(d_opp) − f(d_team), with f = d^(1/3) or log(1 + d/100 km); team-season effects; NCAA, conference-tournament and early-season-event strata | CBBD games + Wikidata coordinates + closing lines | PBP and box score only | Unknown. Williams 2025 found no relation between travel and lines (a null, not proof of pricing); residual untested |
| new-2 | The same gap predicts margin against a neutral rating model | Margin − rating-implied neutral margin (Torvik; COOPER where available) | As new-1, plus ratings | PBP only | Rating systems differ: COOPER and BPI include travel, Torvik does not |
| new-3 | Proximity raises the closer team's free-throw-attempt and foul differential (the referee channel) | (FTA_team − FTA_opp) and (PF_opp − PF_team) per 100 possessions vs distance gap and attendance | PBP | PBP only | Unknown |
| new-4 | The opponent's free-throw % falls when the modelled crowd share against it is large | Opponent FT% vs gravity-model crowd share (§8), or vs video crowd colour share (§4 item 5) | PBP + attendance + coordinates | PBP only; crowd share is better measured from video or audio | Unknown. Prior is weak: van Bommel et al. find away FT% only 1.1% lower (relative) than neutral, and neutral D1 teams shoot better than home teams |
| new-5 | An eastward time-zone shift of ≥ 3,600 s (1 h) for one team lowers its first-half efficiency at neutral sites, with distance held fixed (extends H10; the first-half focus is from H10) | First-half points per possession vs eastward shift (tz_shift_s, shown in h) | PBP + IANA zones | PBP only | Football: Coleman 2017 and Fodor & Krieger 2014 report mispricing; Nichols 2014 mixed. College basketball unknown. Basketball support is thin: Leota's effect is for home teams only (p = 0.051 for wins) and the Clay figure is unverified |
| new-6 | Crowd-noise asymmetry at neutral sites follows the modelled crowd share | Noise asymmetry in dB (LAeq 0-5 s after each made basket or free throw minus the 10 s before; run = ≥ 8 unanswered points within ≤ 180 s), team A minus team B, vs gravity-model share and vs video colour share (definitions in §4 item 5) | Broadcast audio and video | Video or audio needed | n/a |
| new-7 | The proximity effect has shrunk over time | Distance gap × season interaction, 2002-2026 | CBBD + historical lines | PBP only | n/a |
| new-8 | In Big Ten tournaments the closer team beats the spread, and the 2028 Las Vegas site moves the edge to the West Coast members | Margin against the line by distance rank, 2024 Minneapolis, 2025 and 2027 Indianapolis, 2026 Chicago, 2028 Las Vegas | Lines + coordinates | PBP only | Unknown |

**Power note.**
- MSU has about 9 neutral-site games per season.
- van Bommel et al. counted 23,856 neutral-site games across all NCAA divisions and both genders over five seasons. The Division I men's count per season can be read from CBBD.
- Estimate effects league-wide and treat the MSU fit as descriptive.

---

## 11. Open questions and gaps

**Sources we could not read in full:**
- **Carter (2017):** effect size in points and the distance threshold (Wiley paywall).
- **Clay et al. (2015):** coefficients. The 33.6% (odds ratio 0.644) figure is from a snippet and a GitHub review (which dates the paper 2014) and is unverified. The 0.861 odds ratio and the elevation/temperature claims are UNSOURCED and withdrawn. The Winthrop Intelligence PDF (canr.msu.edu) still returns a bot page.
- **Horlick et al. (2023):** only the abstract; sample size and coefficients not seen.
- **FiveThirtyEight tournament-travel article and its methodology:** the page redirects to ABC; values come from snippets only.
- **KenPom:** the semi-neutral rule and home-court posts were blocked (403 and Cloudflare).

**Gaps in the literature and data:**
- **Peer-reviewed tests of proximity against spread residuals at college-basketball neutral sites:** none found. new-1 would fill this gap.
- **Crowd composition at neutral college games:** never measured directly; only buyer-state shares from resale platforms.
- **Current NCAA ticket allotment per school:** only the 350-ticket figure from about 2011 (UCLA page).
- **Kaggle `MGameCities` schema:** not confirmed.
- **Conference tournaments (any league) and early-season multi-team events:** no opened study measures proximity effects in either (§2.4). Both are gaps to fill with our own data (ACC Greensboro vs out-of-state; Big Ten 2024 and 2028; November events).
- **Empirical points estimate at college neutral sites:** none verified; the 0-1.3 point range is model-implied.
- **Chant asymmetry:** not operationalised (§4 item 5).

**Checks to do before the test:**
- **Designated home teams:** done for MSU in this pass (Rutgers at MSG is an ESPN home game for Rutgers; both Oakland games are ESPN-neutral). League-wide, apply the §8 rule.
- **Opponent origins:** done for MSU games and Big Ten schools (Appendix A). League-wide, use CBBD `currentVenueId` mapped to Wikidata arena items, with dated arena moves.
- **§9.2 future venues:** distances are from the first pass; their QIDs are not yet listed in Appendix A.

**Decisions for Aldemir and the requirements session:**
- **Distance metric:** great-circle distance vs driving distance or time for fan cost on short trips; whether bus vs charter can be sourced.
- **Benchmark:** which rating to treat as the "neutral expectation", one with a travel term (COOPER/BPI) or one without (Torvik). Also whether to require a closing-line residual before anything is called an edge.
- **Video crowd share:** whether to build a crowd-share measure from video (clothing colour in wide shots) or audio (new-6), given the requirements items on crowd loudness.

---

## Sources

All URLs below were opened during the research for this task, except where marked **unverified** or listed under "blocked". Some Crossref query URLs were recorded in truncated form in the research notes and are reproduced as recorded.

1. https://www.teamrankings.com/blog/ncaa-basketball/and-albuquerque-is-where-the-effect-of-travel-distance-on-ncaa-tournament-play-stat-geek-idol (via curl; WebFetch returned 403). 323 games 2007-11; cover splits; shooting by distance; midweek turnovers and totals.
2. https://ideas.repec.org/a/wly/mgtdec/v38y2017i1p76-91.html. Carter 2017 citation and abstract.
3. https://api.crossref.org/works/10.1002/mde.2742. Carter abstract.
4. https://api.semanticscholar.org/graph/v1/paper/DOI:10.1002/mde.2742. Carter metadata; no open PDF.
5. https://cgscholar.com/publishers/articles/geospatial-determinants-of-game-outcomes-in-ncaa-mens-basketball-vol-4-issue-4-2015-fe4bbeca-985b-4c5c-bf31-bca3d751244a. Clay et al. sample.
6. https://api.crossref.org/works?query.bibliographic=Geospatial+Determinants... (query string truncated in the research notes). Clay, Bro, Clay; IJSS 2015; DOI.
7. https://github.com/SamuelSchlesinger/march-madness-2026/blob/main/literature-review/index.md. Secondary summary of Clay et al.; used only as an **unverified** pointer.
8. https://esri.com/news/arcuser/1006/spatial-madness2of2.html. Ward & Davenhall, part 2.
9. https://www.esri.com/news/arcuser/1006/spatial-madness1of2.html. Ward & Davenhall, part 1.
10. https://punkrockor.com/2009/03/19/does-distance-matter-in-the-ncaa-tournament/. Seed and distance confounding.
11. https://pittnews.com/article/24578/archives/traveling-distance-hurts-teams-chances. News & Observer descriptive splits; before and after pods.
12. https://dspace.allegheny.edu/entities/publication/9c5c4a25-1ddf-448d-9aae-887f20e61155. Williams 2025.
13. https://www.rotowire.com/cbasketball/article/ncaa-tournament-travel-distances-108250. 2026 haversine table.
14. https://www.natesilver.net/p/sbcb-methodology. SBCB travel term.
15. https://www.natesilver.net/p/introducing-cooper-silver-bulletins. COOPER travel term.
16. https://www.natesilver.net/p/2026-march-madness-ncaa-tournament-predictions. 5/8 COOPER + 3/8 KenPom; travel distance.
17. https://www.poynter.org/news/nate-silvers-sober-data-driven-guide-march-madness. FiveThirtyEight 2017 travel adjustment.
18. https://www.espn.com/blog/statsinfo/post/_/id/125994/bpi-and-strength-of-record-what-are-they-and-how-are-they-derived. BPI site, rest, distance and altitude.
19. http://adamcwisports.blogspot.com/p/every-possession-counts.html. T-Rank FAQ.
20. https://www.covers.com/ncaab/what-are-torvik-ratings. No location detail.
21. https://statsbywill.substack.com/p/neutral-site-games-a-problem-for. Neutral-site efficiency; crowd anecdotes.
22. https://arxiv.org/pdf/1909.04817. van Bommel et al. 2021.
23. https://file.scirp.org/Html/2-1240217_35927.htm. Magel & Unruh 2013, reporting Harville & Smith 4.68 ± 0.28 points.
24. https://api.crossref.org/works?query.bibliographic=The+Home-Court+Advantage+How+Large... (query string truncated in the research notes). Harville & Smith 1994 citation.
25. https://thesportjournal.org/article/the-home-court-advantage-evidence-from-mens-college-basketball/. Yi 2017.
26. https://beyondthescoresports.substack.com/p/breaking-down-home-court-advantage. Beney 2025.
27. https://www.samford.edu/sports-analytics/fans/2021/Did-Minimal-Crowds-in-2020-2021-Impact-College-Basketball-Home-Team-Performance. Samford 2021.
28. https://www.aei.org/wp-content/uploads/2021/07/Ganz-Allsop-All-star-fans-WP.pdf. Ganz & Allsop 2021.
29. https://pmc.ncbi.nlm.nih.gov/articles/PMC9245584/. Leota et al. 2022.
30. https://pmc.ncbi.nlm.nih.gov/articles/PMC11503446/. Mochales Cuesta et al. 2024 review.
31. https://www2.uibk.ac.at/downloads/c4041030/wpaper/2008-16.pdf. Oberhofer et al.
32. https://www.th-owl.de/elsa/download/6898/6899/Beckmann2021_Article_StatisticalInfluenceOfTravelli.pdf. Beckmann 2021.
33. https://repec.iza.org/dp12143.pdf. Van Damme & Baert 2019.
34. https://www.csef.it/WP/wp376.pdf. Ponzo & Scoppa.
35. https://muellerstefan.net/papers/ijpas_kneafsey_mueller.pdf. Kneafsey & Müller 2018.
36. https://arxiv.org/abs/2608.16312. Delbianco et al. 2026, rugby sevens.
37. https://arxiv.org/abs/2308.06279. Fioravanti et al. 2023, Argentine away-fan ban.
38. https://ideas.repec.org/a/sae/jospec/v15y2014i1p78-96.html. Nichols 2014.
39. https://ircommons.uwf.edu/esploro/outputs/journalArticle/Does-jet-lag-create-a-profitable/99380090335306600. Fodor & Krieger 2014.
40. https://scholars.unf.edu/en/publications/team-travel-effects-and-the-college-football-betting-market/. Coleman 2017.
41. https://digitalcommons.unf.edu/unf_faculty_publications/1874. Coleman 2017 citation.
42. https://thesportjournal.org/article/geographical-effects-on-college-bowl-games/. Yoost 2009.
43. https://csl.tamu.edu/Portals/0/CottonBowlDocs/Secondary-Market-Behavior-During-College-Footballs-Postseason.pdf. Rishe, Reese & Boyle 2015.
44. https://fightingillini.com/sports/2022/3/3/2022-ncaa-basketball-tournament (via curl). NCAA equal ticket allotment.
45. https://uclabruins.com/ucla-bruins-tickets-77. 350 tickets per participant (undated).
46. https://www.cbssports.com/college-basketball/news/2019-march-madness-texas-tech-may-have-the-most-fans-at-final-four-ticket-data-indicates. StubHub buyer states, 2019 Final Four.
47. https://sports.yahoo.com/articles/much-men-final-four-tickets-103603211.html. SeatGeek buyer states, 2026 Final Four.
48. https://deadspin.com/facebook-data-give-us-the-best-fandom-map-of-the-ncaa-t-456782281/. 2013 Facebook March Madness map.
49. https://internet.psych.wisc.edu/wp-content/uploads/532-Master/532-UnitPages/Unit-14/NYT_NCAA-Football_Facebook_2014.pdf. NYT Upshot Facebook-likes method.
50. http://www.ncaa.org/media-center-building-the-brackets-a-deep-dive-on-the-ncaa-tournament-selection-and-seeding-process/. NCAA bracketing principles.
51. https://www.nbcsportsboston.com/ncaa/ncaab/march-madness-host-sites-future-final-four-mens/776832/. 2027-2028 NCAA sites; Final Fours 2029-2031.
52. https://en.wikipedia.org/w/api.php?action=parse&page=Big_Ten_men%27s_basketball_tournament&prop=wikitext. Big Ten tournament host history and 2025-28 sites.
53. https://en.wikipedia.org/w/api.php (parse of the 2022-23, 2023-24, 2024-25 and 2025-26 "Michigan State Spartans men's basketball team" pages). MSU neutral-site games.
54. https://en.wikipedia.org/w/api.php?action=query&prop=coordinates|pageprops. Wikipedia coordinates and QIDs; 10-coordinate default limit.
55. https://www.wikidata.org/w/api.php?action=wbgetentities (73 QIDs). P625 coordinates.
56. https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=20260319. ESPN venue id, `neutralSite`.
57. https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event=401856483. ESPN attendance 17,182.
58. https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/venues/1848. ESPN venue record without coordinates.
59. https://api.collegebasketballdata.com/api-docs.json. CBBD schema.
60. https://arxiv.org/pdf/1412.0248. NCAA model paper listing campus-to-site distance.
61. https://our.unc.edu/abstract/horlick-does-how-far-youve-come/. Horlick, Miller, Webb & Bruss 2023, UNC undergraduate abstract; 2019 and 2022 tournaments, seed gap ≤ 7; travel "has little to no effect". Evidence against.
62. https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=20230204&groups=50&limit=400 (and the same endpoint for 20231216, 20241217, 20251220, 20221111, 20221115, 20231114). ESPN `neutralSite` and `homeAway` for MSU games; Rutgers at MSG coded `neutralSite: false`.
63. https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event=401817267. MSU 74, North Carolina 58 (halves 33-28, 41-30), 2025-11-27.
64. https://en.wikipedia.org/w/api.php?action=query&prop=pageprops (titles in `entities_seed.tsv`) and https://www.wikidata.org/w/api.php?action=wbgetentities (58 QIDs in Appendix A). Re-run in this pass by `resolve_qids.py`.
65. https://ncsportsnetwork.com/acc-tournament-d-c-visit-concludes-20-year-out-of-state-experiment/. ACC tournament venue history (David Glenn); no performance data.
66. https://en.wikipedia.org/w/api.php?action=parse&page=Big_Ten_men%27s_basketball_tournament&prop=wikitext. Re-opened in this pass: United Center 2019; Gainbridge 2020 and 2022; Lucas Oil Stadium 2021; 2020 cancelled after the first round.

67. https://en.wikipedia.org/w/api.php?action=query&prop=extracts&titles=Foster_Pavilion. Foster Pavilion completed in 2024, replacing the Ferrell Center.

Re-opened in this pass to check the verifier's findings: Sources 1 (author, date, midweek definition), 11 (2002 pods), 12, 21, 22 (§3 insight 4), 23, 25, 26, 27, 29, 30, 31 (Table 3), 34, 43 (Table 4, DIST), 50 and 7.

**Opened but blocked or empty (not used for claims):**
- Wiley mde.2742 (403).
- ResearchGate (403).
- kenpom.com blog pages (403 / Cloudflare).
- fivethirtyeight.com (redirects to abcnews.com).
- web.archive.org (blocked).
- msuspartans.com NCAA ticket FAQ (JavaScript-only body).
- licensing.msu.edu (404).
- ibj.com (paywall).
- forbes.com (403).
- Kaggle March Machine Learning Mania data page (empty).
- bigten.org 2025-28 release (404).
- sagarin.com (expired certificate).
- winthropintelligence.com (404), and its canr.msu.edu PDF copy (bot page; re-tried in this pass, still a bot page). A search snippet of that PDF says "reduces the odds of winning to 0.644, or 33.6% less" (reported by the verifier) and that eastward time-zone travel "significantly reduces the odds of winning" (seen in this pass); both snippet-only.
- digitalcommons.butler.edu undergraduate thesis (403).
- journals.sagepub.com (403).

**Claims kept with an "unverified" mark** (snippet-only or secondhand):
- KenPom half home-court advantage in "semi-neutral" games, and the "no travel component" note.
- FiveThirtyEight +2 points at 161 km / −1 point at 2,414 km, and the 73-25 record.
- Clay et al. 33.6% (odds ratio 0.644). The odds ratio 0.861 and "elevation and temperature not significant" are not merely unverified but **UNSOURCED** and withdrawn.
- CBBD free tier of about 1,000 calls per month.
- MSU 576,000 living alumni.
- Rishe, Mondello & Boyle 2014 tournament-proximity finding.
- Kaggle `MGameCities` schema.
- Designated home status of the two Oakland games at Little Caesars Arena (both ESPN-neutral). Rutgers at MSG is resolved: ESPN codes it as a Rutgers home game.

**Repo files created in this pass:**
- `docs/research/neutral_site_proximity_assets/entities_seed.tsv`: Wikipedia titles, roles and IANA zones.
- `docs/research/neutral_site_proximity_assets/resolve_qids.py`: title → QID → P625.
- `docs/research/neutral_site_proximity_assets/entities.tsv`: resolved QIDs and coordinates (Appendix A).
- `docs/research/neutral_site_proximity_assets/compute_distances.py` and `compute_distances_output.txt`: §9.1 and §9.3 tables.

**Internal repo references:**
- `docs/requirements.md`: match-context, travel and crowd-loudness items; small-sample rule; H10.
- `docs/research/odds_markets_research.md`: closing-line sources; KenPom home-edge note.
- `coord/prompts/002-claude-code-taxonomy-and-markets.md`: Job C.

---

## Appendix A: entity coordinates

Wikidata P625 coordinates resolved in this pass (Source 64) by `docs/research/neutral_site_proximity_assets/resolve_qids.py`; machine-readable copy in `entities.tsv`. "venue" = neutral site in §9.1 or §9.3; "home arena" = origin used for that team. All 58 entities returned coordinates. The USS Abraham Lincoln (2022 Armed Forces Classic) is represented by NAS North Island.

| Entity (Wikipedia title) | Role | QID | Latitude (°) | Longitude (°) | IANA time zone |
|---|---|---|---|---|---|
| Breslin Center | home arena: Michigan State | Q2924511 | 42.72823 | -84.49240 | America/Detroit |
| Naval Air Station North Island | venue:Armed Forces Classic 2022 (proxy for USS Abraham Lincoln) | Q1800390 | 32.69917 | -117.21528 | America/Los_Angeles |
| Gainbridge Fieldhouse | venue | Q545007 | 39.76389 | -86.15556 | America/Indiana/Indianapolis |
| Moda Center | venue | Q1347442 | 45.53167 | -122.66667 | America/Los_Angeles |
| Veterans Memorial Coliseum (Portland, Oregon) | venue | Q549437 | 45.53222 | -122.66944 | America/Los_Angeles |
| Madison Square Garden | venue | Q186125 | 40.75050 | -73.99345 | America/New_York |
| United Center | venue | Q639975 | 41.88056 | -87.67417 | America/Chicago |
| Nationwide Arena | venue | Q166503 | 39.96928 | -83.00611 | America/New_York |
| Acrisure Arena | venue | Q65052659 | 33.77917 | -116.33889 | America/Los_Angeles |
| Little Caesars Arena | venue | Q18154984 | 42.34120 | -83.05490 | America/Detroit |
| Target Center | venue | Q282675 | 44.97944 | -93.27611 | America/Chicago |
| Spectrum Center (arena) | venue | Q983870 | 35.22500 | -80.83917 | America/New_York |
| State Farm Arena | venue | Q1123297 | 33.75722 | -84.39639 | America/New_York |
| Lahaina Civic Center | venue | Q15241279 | 20.90499 | -156.68385 | Pacific/Honolulu |
| Rocket Arena | venue | Q387157 | 41.49639 | -81.68806 | America/New_York |
| Suncoast Credit Union Arena | venue | Q28127717 | 26.54780 | -81.88690 | America/New_York |
| KeyBank Center | venue | Q1110789 | 42.87500 | -78.87639 | America/New_York |
| Capital One Arena | venue | Q223240 | 38.89806 | -77.02083 | America/New_York |
| T-Mobile Arena | venue | Q3338973 | 36.10292 | -115.17836 | America/Los_Angeles |
| McCarthey Athletic Center | home arena: Gonzaga | Q6800179 | 47.66530 | -117.39900 | America/Los_Angeles |
| Rupp Arena | home arena: Kentucky | Q842965 | 38.04944 | -84.50278 | America/New_York |
| Coleman Coliseum | home arena: Alabama | Q5142988 | 33.20290 | -87.53970 | America/Chicago |
| Matthew Knight Arena | home arena: Oregon | Q14709065 | 44.04500 | -123.06600 | America/Los_Angeles |
| Jersey Mike's Arena | home arena: Rutgers | Q6686804 | 40.52528 | -74.44111 | America/New_York |
| Value City Arena | home arena: Ohio State | Q783033 | 40.00750 | -83.02510 | America/New_York |
| Galen Center | home arena: USC | Q3094568 | 34.02130 | -118.28000 | America/Los_Angeles |
| Fiserv Forum | home arena: Marquette | Q20372160 | 43.04510 | -87.91820 | America/Chicago |
| Bramlage Coliseum | home arena: Kansas State | Q2923640 | 39.20036 | -96.59383 | America/Chicago |
| Cameron Indoor Stadium | home arena: Duke | Q2934766 | 35.99753 | -78.94231 | America/New_York |
| McKale Center | home arena: Arizona | Q3303672 | 32.23030 | -110.94600 | America/Phoenix |
| Ferrell Center | home arena: Baylor (to Jan 2024) | Q5445295 | 31.54793 | -97.10567 | America/Chicago |
| Williams Arena | home arena: Minnesota | Q8020979 | 44.97694 | -93.22833 | America/Chicago |
| Mackey Arena | home arena: Purdue | Q6724456 | 40.43330 | -86.91610 | America/Indiana/Indianapolis |
| Humphrey Coliseum | home arena: Mississippi State | Q5941342 | 33.46167 | -88.79444 | America/Chicago |
| Dean Smith Center | home arena: North Carolina | Q3020664 | 35.89972 | -79.04389 | America/New_York |
| Allen Fieldhouse | home arena: Kansas | Q2837888 | 38.95431 | -95.25239 | America/Chicago |
| CU Events Center | home arena: Colorado | Q5168058 | 40.00464 | -105.26058 | America/Denver |
| FedExForum | home arena: Memphis | Q641212 | 35.13833 | -90.05056 | America/Chicago |
| Athletics Center O'rena | home arena: Oakland | Q4813778 | 42.67400 | -83.21320 | America/Detroit |
| Kohl Center | home arena: Wisconsin | Q1578408 | 43.06942 | -89.39697 | America/Chicago |
| Chace Athletic Center | home arena: Bryant | Q5066064 | 41.92100 | -71.53960 | America/New_York |
| The Pit (arena) | home arena: New Mexico | Q7757281 | 35.06700 | -106.63200 | America/Denver |
| The Sandy and John Black Pavilion at Ole Miss | home arena: Ole Miss | Q21196637 | 34.36316 | -89.53545 | America/Chicago |
| Neville Arena | home arena: Auburn | Q4819242 | 32.60250 | -85.49300 | America/Chicago |
| Minges Coliseum | home arena: East Carolina | Q8020980 | 35.59740 | -77.36720 | America/New_York |
| Pauley Pavilion | home arena: UCLA | Q1126193 | 34.07020 | -118.44700 | America/Los_Angeles |
| Scheels Center | home arena: North Dakota State | Q4918378 | 46.90040 | -96.79900 | America/Chicago |
| KFC Yum! Center | home arena: Louisville | Q10516134 | 38.25750 | -85.75389 | America/New_York |
| Harry A. Gampel Pavilion | home arena: UConn (campus; UConn also uses XL Center) | Q5666781 | 41.80530 | -72.25420 | America/New_York |
| State Farm Center | home arena: Illinois | Q2867017 | 40.09630 | -88.23600 | America/Chicago |
| Simon Skjodt Assembly Hall | home arena: Indiana | Q4808661 | 39.18083 | -86.52222 | America/Indiana/Indianapolis |
| Carver–Hawkeye Arena | home arena: Iowa | Q5047562 | 41.66361 | -91.55444 | America/Chicago |
| Xfinity Center (College Park, Maryland) | home arena: Maryland | Q2985114 | 38.99542 | -76.94156 | America/New_York |
| Crisler Center | home arena: Michigan | Q3091213 | 42.26504 | -83.74677 | America/Detroit |
| Pinnacle Bank Arena | home arena: Nebraska | Q7196282 | 40.81778 | -96.71333 | America/Chicago |
| Welsh-Ryan Arena | home arena: Northwestern | Q7981834 | 42.06690 | -87.69280 | America/Chicago |
| Bryce Jordan Center | home arena: Penn State | Q2927191 | 40.80890 | -77.85580 | America/New_York |
| Hec Edmundson Pavilion | home arena: Washington | Q4708490 | 47.65200 | -122.30200 | America/Los_Angeles |


---

## Additions 2026-10-18

Gap-filler pass. Each item below closes a gap left by the sections above, adds model fields or hypotheses, and lists the sources opened in this pass (numbered 68 onwards, continuing the [Sources](#sources) list; see "Sources for the additions" at the end). Every claim below cites a source opened in this pass; "unverified" keeps the meaning defined at the top of this document. Units: km, hours and points for display; the new model fields are stored in seconds (and metres), following the project rule.

### A. Body-clock tip time (circadian phase at tip-off), not only the size of the time-zone shift

**Why it matters.** §5 and the §8 model use only the signed hours of shift (`tz_shift_s`). The strongest circadian evidence that bears on betting markets is about **what time the game is on each team's body clock**, not about how far the team moved.

**Evidence for (peer-reviewed first).**
- **Smith, Efron, Mah & Malhotra (2013),** *SLEEP* 36(12): 1999-2001, doi 10.5665/sleep.3248 (PubMed abstract and PMC full text opened; Sources 68-69).
  - Design: NFL games between West Coast (WC) and East Coast (EC) teams, 1970-2011. Evening games are those starting after 20:00 Eastern (window 20:00 to midnight); controls are 13:00 Eastern starts between the same matchups.
  - Evening games (n = 106; 17 EC vs 6 WC teams; four pushes removed): **WC teams beat the spread in 70, EC teams in 36 (66%)**, by **5.26 ± 1.33 points** against the spread. The ± is not labelled, but 5.26 / 1.33 = 3.95 equals the reported t, so it is a standard error. One-sample t = 3.95, P < 0.0001; the two sub-periods 1970-1994 (64 games) and 1995-2011 (42 games) give P = 0.009 and P = 0.006.
  - Day games (n = 293): WC 143, EC 150 against the spread (49%), **0.16 ± 0.80 points**. Evening vs day: χ² = 9.29, P = 0.002.
  - Regression covariates (year, home advantage, game time, spread): time trend and home advantage not significant.
  - Mechanism (assumed, not measured): athletic performance peaks in the late afternoon of the body clock; an evening Eastern kick-off is about 17:00 on a WC body clock. The authors list no melatonin, temperature or sleep data as a limitation.
- **Smith, Guilleminault & Efron (1997),** *SLEEP* 20(5): 362-365 (PubMed abstract opened; Source 71). Monday Night Football, 1970-1994, start times 21:00 EST: WC teams win more often (p < 0.01) and beat the Las Vegas spread (p < 0.01); the advantage "enhances home-field advantage for WC teams and essentially eliminates" it for EC teams. Sample size not stated in the abstract.
- **Özdalyan, Çene, Gümüş & Açıkgöz (2024),** *Chronobiology International* 41(5): 599-608, doi 10.1080/07420528.2024.2325641 (PubMed abstract opened; full text 403; ScienceDaily release opened; Sources 75-76). 25,016 NBA regular-season games, 2000-2021 (24,985 used for comparisons). Teams were grouped by whether their "internal" time zone was the same as, ahead of, or behind the local zone. **Home** teams whose body clock was ahead of local time (just back from the east) won most; teams behind local time won least. For **away** teams, being synchronised with local time was best, and the authors attribute away-team results more to travel fatigue than to phase. Release figures: Pacific home vs Eastern visitor 63.5% home wins; Eastern home vs Pacific visitor 55.0%. Limitations stated: team travel schedules unknown (a rule-based adaptation model was used) and **no control for team quality**.

**Evidence against or limiting.**
- Smith 2013 is an NFL study with one game a week, so travel and rest differ from college tournament play; the circadian phase was assumed, not measured; the sample ends in 2011.
- Leota 2022 (§5) finds no effect for **away** teams in the NBA; Özdalyan 2024 likewise says away-team results look more like fatigue than circadian phase. Neither studied the time of tip-off relative to the body clock directly.
- No search in this pass found a replication of Smith 2013 after 2011 or a college-basketball study of tip time against body clock.

**Market status.** Smith 1997 and 2013 are direct evidence that the closing spread did **not** price the body-clock effect in NFL night games up to 2011. The result has been public since 1997 and was widely publicised in 2013 (AASM release, Source 70), so it may be priced now. College basketball: **unknown**.

**Why it applies to our setting.** NCAA first-weekend sessions span roughly 12:15 to 22:10 Eastern. In 2025 the first-round tips ran from 11:15 CT (12:15 ET) to 21:10 CT (22:10 ET) on both days (Source 77). Examples from that schedule (body-clock times are our arithmetic from each school's home zone):
- MSU vs Bryant, 21:00 CT (22:00 ET), Rocket Arena: both teams on Eastern clocks, so 22:00 for both (no contrast).
- UC San Diego vs Michigan, 21:00 CT: about 19:00 on the UCSD (Pacific) clock and 22:00 on Michigan's.
- Liberty vs Oregon, 21:10 CT: about 22:10 on Liberty's (Eastern) clock and 19:10 on Oregon's.
- Vanderbilt vs Saint Mary's, 14:15 CT: about 12:15 on the Saint Mary's (Pacific) clock.
So the same venue and the same `tz_shift_s` can put a team at very different body-clock times depending on the session. That **within-site variation across sessions** is what lets the model separate body-clock time from shift size.

**New model fields (add to §8).**
- `tip_utc`: tip-off time in UTC (ESPN `date` field; check against the CBBD `startDate`).
- `tip_home_local_s` for each team: seconds after local midnight at tip-off, in the IANA zone of the team's home arena (handles DST; America/Phoenix and Pacific/Honolulu have none). Shown as hh:mm.
- `late_clock_s` = max(0, `tip_home_local_s` − 75,600) (time past 21:00 on the body clock) and `early_clock_s` = max(0, 43,200 − `tip_home_local_s`) (time before 12:00). The 21:00 and 12:00 thresholds are priors, to be varied at 20:00/22:00 and 11:00/13:00.
- Added terms in the main specification, alongside γ_E and γ_W:

  ```
  + γ_L · [late_clock_s(B) − late_clock_s(A)] / 3,600
  + γ_M · [early_clock_s(B) − early_clock_s(A)] / 3,600
  ```

  Positive γ_L means a team playing later on its body clock does worse. γ_L and γ_E are correlated (eastward travellers in late sessions), so the identification rests on session-to-session variation within the same venue and on day games as the control, exactly as in Smith 2013.
- **new-5 is split by session** (new-5 itself is unchanged; the split adds new-9 and new-10, table in item H): new-9 for late sessions (`tip_home_local_s` ≥ 75,600 for one team only), new-10 for early sessions (≤ 43,200).

### B. Basketball travel distance and direction studies beyond Leota 2022

| Source | Setting | Finding (effect sizes as reported) | What it adds to §3, γ_E and γ_W |
|---|---|---|---|
| **Charest, Samuels, Bastien, Lawson & Grandner (2021),** *J Clin Sleep Med* 17(11): 2269-2274, doi 10.5664/jcsm.9446 (PubMed abstract and PMC8636381 full text opened; Sources 72-74) | 3,005 NBA back-to-back games in two cities, seasons 2013-2020; mixed-effects logistic regression (lme4) with travel direction, distance band (0-500, 501-1,000, 1,001-1,500, > 1,500 km), team quality (season win %) and season | Win likelihood: Away-Home 54.4% (95% CI 54.4-54.5), Away-Away 39.2% (37.2-41.2), Home-Away 36.8% (36.7-36.8). **Returning home, each additional 500 km lowered the chance of winning by about 4% (P = .038)**; the paper does not say whether this is absolute or relative, and reports no coefficient or odds ratio. Distance was **not** significant for Away-Away (P = .373) or Home-Away (P = .308). Excluding Away-Home, **eastward travel beat westward (P = .024)** but did not differ from same-zone travel (P = .091 in the abstract, .094 in the results). Raw win rates: eastward 44.51%, westward 40.83%. Time-zone mix: 1,956 same-zone, 491 east and 555 west by one zone, 3 by two zones. | A per-km prior only for the return-home leg: about −0.8% win probability per 100 km if the 4% per 500 km is read as linear and absolute (our arithmetic; the paper does not say). It does **not** support a distance effect for teams playing away, the closest analogue to a neutral site. On direction it runs **against** Leota (eastward hurts home teams) and the Özdalyan release ("traveling to the east decreases the performance"). |
| **Özdalyan et al. (2024)** (item A) | 25,016 NBA games | Home teams with body clock ahead of local time do best; away teams do best when synchronised; no quality control | Supports a westward-return benefit for **home** teams, not a rule for neutral-site teams |

**Bearing on the direction contradiction (§2.3, Mochales Cuesta).** The three NBA studies disagree because they condition on different things:
- Leota: home teams just back from a trip, by shift direction.
- Charest: the second game of a back-to-back, with the Away-Home sequence removed.
- Özdalyan: phase relative to local time, split by home and away.

A direction effect at a neutral site therefore cannot be read off any of them. Our γ_E and γ_W should keep **wide, sign-agnostic priors** (centred on 0, not on Leota's −1.29 points), and the body-clock terms of item A should carry the circadian hypothesis instead.

**Market status.** None of these papers tests betting lines. Unknown.

### C. Conference-tournament ticket allocation (crowd-share inputs for the conference-tournament stratum)

What the opened sources say about the **Big Ten** tournament:
- **Per-school cap and reallocation (2005).** A Big Ten spokesperson (Robin Jentes) said each school "could request up to 1,000 tickets", and tickets left by schools that requested fewer or did not sell theirs were "distributed among schools that request more". **Illinois received 2,400** for the 2005 tournament in Chicago, more than twice the cap, which shows the reallocation in action (Daily Illini, 2 Mar 2005; Source 78).
  - The same article gives the 2005 **NCAA** allotment per school: 350 tickets for the first and second rounds, 1,250 per game for the regionals and 4,500 for the Final Four. This dates the 350 figure in §4 back to at least 2005, so it is not only the UCLA page of about 2011.
  - Illinois split its allotment 25% to students, most of the rest to donors and season-ticket holders, and about 5% to "institutional advancement".
- **Equal seating levels; location by conference rule (2012-13).** "All Big Ten schools receive an equal share of seating levels at the United Center", and **"the location of Indiana's allotment is determined by the Big Ten Conference rotation"**. IU sold its block to season-ticket holders by priority points: the top 400 point totals could buy lower or club level (US$325, limit 2), everyone else upper level (US$240, limit 4). Single-session tickets went on Ticketmaster (IU Athletics, 12 Nov 2012; Source 79). Correction to the task brief: this page says **rotation**, not standings.
- **Standings-based location (2025-26, women's tournament).** Wisconsin's notice for the 2026 Big Ten **women's** tournament (Gainbridge Fieldhouse, 4-8 Mar 2026): "All-session seat locations will be assigned to teams by the conference standings in mid-February"; orders allocated by annual giving level, then priority points (Source 80). The current **men's** rule (rotation vs standings) was not found.
- **Student tickets and declined allotments (2010).** Each school was allotted 75 discounted student all-session tickets (US$50 vs US$165), and Purdue was expected to receive the tickets reserved for Iowa and Penn State, "who declined to purchase their allotted share" (Minnesota Daily, 28 Jan 2010; Source 81). The same article quotes a Minnesota spokesman on the 2008 Indianapolis tournament: against Indiana it "was packed with Indiana people" (Bloomington is about an hour from Indianapolis). That is an anecdote, not data.
- **2021 cap.** The 2021 tournament moved from Chicago to Lucas Oil Stadium (Indianapolis) with **up to 8,000 fans**, tickets sold through each school's ticket office (Hammer and Rails, 4 Mar 2021; Source 82). Illinois received "a limited number" of all-session tickets for top donors, and the conference allocated **50 student tickets** per school; everyone else bought single sessions from Lucas Oil Stadium and Ticketmaster (Illinois Athletics, 4 Mar 2021; Source 83).
- **Unverified:** an Iowa allotment of 750 tickets in 2017, of which 250 were sold (Cedar Rapids Gazette snippet; the page returned HTTP 429).

**What this changes in the gravity model (§4 item 3, §8).**
- The primary allocation is **nominally equal but reallocated by demand**: unsold or declined allotments flow to high-demand schools. Demand rises with fan-base size and falls with distance, so the reallocation is itself a proximity channel, before the public and resale market add more.
- Proposed decomposition for a conference-tournament session: expected seats for team i = min(request_i, cap) + reallocated_i + public_i, where public_i follows the gravity form S_i·f(d_i). The fixed part (cap) puts a floor under far teams' crowd share, and the reallocation and public parts scale with S_i and d_i.
- **L (local neutral) and S (fan-base size)** should be estimated per event type: in the conference-tournament stratum a large share of seats sits in school blocks (all-session), while NCAA sessions are mostly public.
- Block location (rotation or standings) decides where each school's fans sit, which matters for the **video** crowd-colour measure (§4 item 5): lower-bowl blocks dominate broadcast frames.
- Data needed per year: cap, actual allotments, returns. These are not public; school ticket-office notices give fragments only. Treat the allocation as a latent variable.

### D. The 2021 men's tournament in Indiana, and the capped 2020-21 conference tournaments, as a natural experiment

**Facts (opened sources).**
- The NCAA announced on 4 Jan 2021 that the whole tournament would be played in the Indianapolis area and central Indiana. Sites: Lucas Oil Stadium (two courts), Hinkle Fieldhouse, Bankers Life (now Gainbridge) Fieldhouse, Indiana Farmers Coliseum, Simon Skjodt Assembly Hall (Bloomington) and Mackey Arena (West Lafayette) (Wikipedia, read via the MediaWiki API; Source 86).
- On 19 Feb 2021 the NCAA allowed **up to 25% capacity**, and that figure **included** participants, essential staff and family members of players and coaches (AP via WSBT; Inside Indiana Business; Sources 84-85). Indiana University capped Assembly Hall at 500, with some seats for vaccinated local medical workers (Source 84).
- **Actual attendance** (NCAA attendance summary; Source 87): 173,592 over 65 reported games, **2,671 per game**. Examples:
  - First Four: 232 and 287 at Assembly Hall, 1,035 and 1,292 at Mackey.
  - First round: Assembly Hall 424-454, Hinkle about 1,000-1,070, Farmers Coliseum 873-986, Bankers Life 2,157-3,528, Lucas Oil 5,764-6,596.
  - Regional finals 6,166-7,519; national semifinals 8,131; final 7,923.
  - For comparison, the 2019 tournament averaged 19,132 per **session** (36 sessions, 688,753). Sessions usually hold two games in the early rounds, so the two averages are not on the same footing; the drop in crowd per game is still roughly an order of magnitude.
- **No pods**: "Unlike past tournaments, teams are not grouped as pods" (bracket note, Source 86). **Artificial crowd noise** was used at all venues (Wikipedia, citing Sports Video Group; the SVG page was not opened).
- The 2021 Big Ten tournament was capped at 8,000 at Lucas Oil Stadium (item C).

**Why it identifies something the rest of the data cannot.**
1. **Seeding no longer allocates distance.** Every team travelled to Indiana, so `d_team` depended only on campus location, not on seed or on the committee's "as close to home as possible" rule (§1 item 2). The main confounder of the raw tournament studies is switched off.
2. **Crowd share was close to zero**, and capped seats went largely to families and staff. So any distance effect in 2021 is the **fatigue and circadian** channel alone (plus whatever crowd share families provide).
3. **Contrast:** β(2021) vs β(other years) estimates how much of the usual proximity effect is crowd (§1 item 3 is an inference with no college-basketball test so far).

**Limits.**
- **Power.** About 66 games (67, minus the VCU-Oregon no-contest; Source 86). Illustrative arithmetic, with assumed inputs: if the margin-against-the-line residual SD is about 10 points and the SD of the COOPER-form gap across games is about 0.5 points (both assumptions, to be computed from our data), SE(β) ≈ 10 / (0.5 × √66) ≈ 2.5 COOPER units. 2021 alone cannot tell β = 0 from β = 1.
- **Remedy:** pool a "low-crowd" stratum: the 2021 NCAA tournament, the 2020-21 conference tournaments (capacity caps vary; the Big Ten's was 8,000) and 2020-21 neutral-site early-season events, with CBBD `attendance` as the crowd measure. Then estimate β × low-crowd as an interaction (new-11).
- Bubble conditions (all teams in Indianapolis hotels, the Indiana Convention Center as the main practice site) also removed between-round travel, which is not true in normal years.
- 2021 lines were set knowing there were no crowds, so a market test of the crowd channel compares 2021 residuals with normal-year residuals rather than expecting a 2021 edge.
- Broadcast audio from 2021 is contaminated by artificial crowd noise, so it must be **excluded** from new-6.

**What a quick look at our parsed brackets shows** (descriptive; script and output in item G): men's top-4 seeds won 12 of 16 first-round games in 2021 (mean margin +13.3) vs 129 of 144 in 2015-2025 excluding 2021 (+15.9), and 7 of 12 second-round games (+0.3) vs 95 of 129 (+5.8). The 2021 second-round figure is suggestive, but n = 12 and the SE is 4.4 points, so it is noise-level evidence only. Without pods, top seeds also lost their usual short trips, so this does not isolate crowd from distance.

### E. The decline of college-basketball home advantage (evidence for new-7, and a pace confounder)

| Source | Finding | Status |
|---|---|---|
| **Karl (2018/2020),** arXiv 1806.08059, "Avoiding Bias Due to Nonrandom Scheduling When Modeling Trends in Home-Field Advantage" (abstract and PDF opened; Source 88) | Intraconference Division I men's games, 2000-2017, neutral-site games excluded; conference-season HFA estimates fitted with a random-coefficient trend model. **Men's college basketball HFA trend −0.074 points per season (95% CI −0.097 to −0.051; p = 3e-7), a decline of 1.332 points over the 18 seasons, 45% of the 2017 estimate of 2.969 points (95% CI 2.661-3.276).** Women: −0.049 per season (−0.882 points, 31%). College football: −0.102 (p = 0.053). NBA slopes not significant. The Big 12 had among the largest scoring HFAs and the Ivy League among the smallest. Margins are in **points**, not per possession; pace is not discussed. | Preprint (not peer-reviewed); opened |
| **CBS Sports (Cobb, 22 Jan 2021)** (Source 89) | Home teams won 64.3% of Division I games in 1996-97 (first KenPom season) and 57.3% in 2020-21 to date (pandemic crowds), "the lowest figure since KenPom began tracking" | Secondary, opened (citing kenpom.com/trends.php, not opened) |
| **KenPom blog (Feb 2015), "?p=146"** | Snippet: conference home teams win "about 2.5 percent" fewer games than 15 years earlier; "every change of five possessions in pace" goes with about 1.6% in home winning percentage, explaining "a little over half" of the change. Whether the 1.6% slope is estimated on college data or borrowed from the NBA is **ambiguous** in the snippet | **Unverified**: kenpom.com (blog and `wp-json/wp/v2/posts/146`) returned 403 / Cloudflare to WebFetch and curl in this pass |
| **Rush the Court, 5 Jan 2018** (Source 90) | Cites a KenPom summer study that "home teams are increasingly losing out on their foul advantage" | Secondary, opened |

**Implications for new-7 and §8.**
- There is now a quantified, college-specific decline in **regular-season** home advantage (Karl: about −0.07 points per season), not only Silver's unquantified statements. It is still not a test of the **proximity** effect at neutral sites.
- **Pace confounder.** A points-based margin scales with possessions. College tempo changes across seasons, so a season interaction on margin in points could show a "decline" that is only fewer possessions. Fit new-7 (and, as a robustness check, new-1 and new-2) on **margin per 100 possessions**: y_100 = 100 · y / poss, with poss the mean of the two teams' possession estimates from the play-by-play (or the usual box-score estimate FGA − OREB + TO + 0.475·FTA; the coefficient is a common convention whose source was not opened in this pass, so treat it as unverified). Report both the points and the per-100 versions.
- **Sharper prediction.** If the proximity effect works through the same crowd and referee channels as home advantage, β_t should fall **in proportion** to the season's home advantage, i.e. β_t / HCA_t constant. Test: interact the distance gap with a season-level HCA estimate (from that season's non-neutral games, per 100 possessions) instead of a linear season trend.

### F. Fan-base size (S_i) proxies that are still available

The gravity crowd-share model needs S_i, and ideally a spatially varying S_i(x) (fans of team i living near venue x). Options, in order of usefulness:

1. **Radio affiliate networks (spatial).** Cooper & Davis (2019), "Fandom on the Air: Assessing Regional Identity through College Football Radio Networks", *Northeastern Geographer* 11: 1-29 (record and PDF opened; Source 91). They geocoded each Power 5 school's football radio affiliates (studio locations, as points; AM and FM not distinguished) from the schools' athletics websites, using 2015 data.
   - Findings: 38 of 67 teams (57%) show **"state saturation"**: coverage closely follows the home state's borders. State borders "still meaningfully shape" fandom geography.
   - Counts: **Michigan State 31 affiliates and Michigan 32**, both state saturation; Ohio State 43; Penn State 53; Purdue 24; Northwestern 1 (a single station).
   - **Use:** S_i(x) ∝ the number of team i's basketball affiliates within a radius of the venue (radii 100/200/400 km as a sensitivity), or a kernel-weighted count. Basketball networks must be collected from current school pages; football counts are a fallback. Limitation: the points are studios, not signal coverage, and affiliate counts partly reflect commercial deals.
2. **Google Trends by DMA (spatial, relative).** Trends values are normalised: each point is divided by total searches for that region and time, then scaled 0-100; Trends uses a **sample** of searches, adds noise, and shows low-volume terms as 0 (Google Trends help; Source 92). Values are therefore comparable **only within one request**. **Use:** request both teams (as Topics) together for the venue's DMA over an off-season window (e.g. 1 Jun to 31 Aug), and use the ratio as S_A(x)/S_B(x). A documented precedent for DMA-level Trends as a fandom measure is the FiveThirtyEight NFL-fandom dataset (5-year search shares by DMA; Source 93), which is journalism, not peer-reviewed. Limits: spikes around events (use off-season windows); small DMAs return 0.
3. **IPEDS completions (scalar).** NCES IPEDS collects the number of awards conferred by each institution and year, by award level and field (Source 94). The cumulative count of bachelor's degrees over about 40 years is a reproducible alumni-stock proxy, replacing the unverified "576,000 living alumni" for MSU. It has no geography.
4. Already in the document: buyer-state shares (§4 item 2), home attendance and enrolment (§4 item 3c). Facebook likes are no longer available.

**Recommendation.** Fit the crowd-share variant with S_i(x) from (1) or (2), and compare with the scalar S_i from (3) and home attendance. A better fit for the spatial version would itself be evidence for the crowd channel. None of these needs resale buyer data.

### G. True home games inside tournaments as a calibration contrast (the d ≈ 0 end of f(d))

**Why.** The proximity effect is bounded above by a full home advantage under tournament conditions (short rest, equal ticket rules, late sessions). The 0 to 1.3 point range in §1 and §3 is model-implied; a tournament home-court figure anchors the top of the scale.

**1. NIT (men).** Phillips, Caudill & Mixon (2015), "Tournament Seeding Efficiency and Home Court Advantage: College Basketball's National Invitation Tournament", *International Journal of Statistics and Probability* 4(3), from p. 101 (6-page PDF), doi 10.5539/ijsp.v4n3p101 (page and PDF opened; Source 95).
- Sample: the first three NIT rounds, played on the higher seed's home court, 2006-2014; **n = 260 games**.
- Margin model (OLS, robust t in parentheses): ScoreDiff = **1.392 (4.66) + 2.007 (1.70) × SeedDiff**, R² = 0.074. The authors read the intercept as home advantage: **about 1.4 points** for two equally seeded teams.
- Win model: P(higher seed wins) = 0.569 (10.52) + 0.048 (3.88) × SeedDiff. They compare with an NCAA tournament intercept of 0.535 (Schwertman et al. 1996), so the excess over 0.5 is about twice as large in the NIT.
- Caveats: SeedDiff is never 0 in the sample (mean 3.28, SD 2.09), so the intercept is an extrapolation and depends on the linear seed form. The paper is small and in a low-profile journal.
- Read against the regular-season figures (Karl 2017: 2.97 points; Harville & Smith 4.68 points, §2.2), a **tournament home edge of roughly 1.4 to 3 points** brackets f(d ≈ 0). The COOPER-form maximum gap of 1.34 points in §9.1 sits at or below that bracket, which is consistent.

**2. NCAA women's tournament, top-16 seeds hosting rounds 1-2 (2015 onwards).** Computed in this pass from Wikipedia brackets (2008-2019, 2021-2025, both sexes; host lists read from the same pages). Script: `docs/research/neutral_site_proximity_assets/tournament_host_records.py`; output: `tournament_host_records_output.txt` (Source 96). In four cases a top-4 seed did not host: Louisville 2015, Michigan State 2016, Stanford 2017 and South Carolina 2019. "Top-seed margin" means the margin of the seed-1-to-4 team against a seed 5-16 opponent.

| Round | Group | n | Top-seed W-L | Mean margin (SE), points |
|---|---|---|---|---|
| R1 | Women 2015-25 excl. 2021, top-4 seed **hosting** | 140 | 140-0 | +29.9 (1.5) |
| R1 | Women 2021, all games neutral (San Antonio) | 16 | 15-1 | +26.5 (3.9) |
| R1 | Women 2008-14 (pre-assigned sites, some hosts) | 112 | 111-1 | +24.9 (1.3) |
| R1 | Men 2015-25 excl. 2021, neutral pods | 144 | 129-15 | +15.9 (1.1) |
| R2 | Women 2015-25 excl. 2021, top-4 seed **hosting** | 140 | 107-33 | +10.8 (1.4) |
| R2 | Women 2021, neutral | 15 | 10-5 | +8.7 (4.8) |
| R2 | Women 2008-14 | 111 | 79-32 | +9.0 (1.5) |
| R2 | Men 2015-25 excl. 2021, neutral pods | 129 | 95-34 | +5.8 (1.1) |

Reading:
- Within the women's tournament, hosting vs the 2021 neutral year differs by about +3 points in each round, but the 2021 SEs are 4-5 points, so the contrast is **uninformative**.
- The women's 2008-14 comparison is confounded by growing concentration of talent at the top over time.
- Men vs women is not a valid contrast (different upset rates).
- The informative version of this design needs **closing lines** for women's tournament games, to compare margin against the line for hosts with neutral-site games of the same seed lines. Whether CBBD or ESPN carry women's lines was not checked.
- Attendance context: 2024 first and second rounds drew a record 292,456 (Butler Collegian, 1 Apr 2025; Source 97). A published host-record or against-the-spread analysis was not found.

**Use in §8.** Add a calibration stratum, "tournament home game" (NIT rounds 1-3; women's rounds 1-2 hosts; any NCAA game in a team's own arena, such as Dayton in the First Four). Estimate its home effect with the same outcome definitions, and constrain f so that f(gap) at the largest neutral-site gaps does not exceed the tournament home effect.

### H. Hypotheses added in this pass (provisional IDs, continuing from new-8)

| ID | Statement | Measure | Data | PBP only, or video? | Priced by the market? |
|---|---|---|---|---|---|
| new-9 | **Late session (splits new-5).** At neutral sites, the team for which tip-off falls later on its body clock (home-zone local time ≥ 21:00) does worse against the closing spread than its opponent, beyond the shift-size terms | Margin against the line on [late_clock_s(B) − late_clock_s(A)] / 3,600, with γ_E/γ_W, distance gap and team-season effects; first half separately (H10) | ESPN/CBBD tip times + IANA zones + closing lines | PBP only | NFL: not priced up to 2011 (Smith 1997, 2013); may be priced since publication. College basketball: unknown |
| new-10 | **Early session (splits new-5).** A team playing before 12:00 on its body clock (West Coast teams in noon Eastern tips) does worse, especially in the first half | First-half and full-game margin against the line on [early_clock_s(B) − early_clock_s(A)] / 3,600 | As new-9 | PBP only | Unknown; no study found |
| new-11 | **Crowd vs fatigue.** The distance-gap effect is smaller when crowds are absent or capped (2021 NCAA tournament, 2020-21 capped conference tournaments and events) than in normal years | Interaction β × low-crowd stratum (CBBD attendance; 2021 has no pods, so distance is not set by seed); margin against the line and per 100 possessions | CBBD games and attendance + coordinates + closing lines | PBP only | Unknown. Lines in 2021 were set knowing there were no crowds, so the test is the difference in residuals between strata |

**Revisions to existing entries (proposed, for the requirements session).**
- new-5: keep as stated, but report it by session (late, afternoon, early) and add the body-clock terms of item A as controls.
- new-7: fit on margin per 100 possessions, and test β_t / HCA_t constant (item E).
- new-8: add the allocation facts of item C (cap, reallocation, block location) as covariates where they can be sourced.

### I. Still missing after this pass

- **Smith 2013 after 2011** and any **college-basketball** body-clock study: none found.
- **Özdalyan 2024 full text** (Taylor & Francis returned 403): the effect sizes by group and the models are unseen; only the abstract and press-release percentages are used.
- **Charest 2021:** no odds ratio or per-km coefficient is published; whether the "4% per 500 km" is absolute or relative is unclear in the paper itself.
- **Current Big Ten men's allocation rule** (rotation vs standings; cap per school; return deadlines): not found; bigten.org pages returned 404. The Iowa 2017 figures (750 allotted, 250 sold) remain unverified.
- **KenPom home-advantage posts** (`?p=146`, trends page): still blocked, so the pace slope is unverified and its sample (college or NBA) unclear.
- **2020-21 conference-tournament capacity caps** other than the Big Ten's: not collected; take them from CBBD attendance.
- **Women's tournament closing lines** and a published host-advantage analysis: not found.
- **Basketball radio affiliate lists** for Big Ten schools: to collect; Cooper & Davis cover football (2015).
- **Coordinates for the 2021 Indiana venues** (Hinkle, Farmers Coliseum, Lucas Oil, Mackey, Assembly Hall): the Wikidata QIDs are in Source 86 (Q3785713, Q14688354, Q867160, Q6724456, Q4808661), but they are not yet resolved in `entities.tsv`.

### Sources for the additions

68. https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=24293776&rettype=abstract&retmode=text. Smith, Efron, Mah & Malhotra 2013, *SLEEP* abstract (PubMed web pages showed a cookie wall; E-utilities used).
69. https://pmc.ncbi.nlm.nih.gov/articles/PMC3825451/. Smith et al. 2013 full text: counts, 5.26 ± 1.33, t = 3.95, χ² = 9.29.
70. https://aasm.org/circadian-timing-may-give-edge-to-west-coast-nfl-teams-in-night-games/. AASM press release, 27 Nov 2013.
71. https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=9381059&rettype=abstract&retmode=text. Smith, Guilleminault & Efron 1997, *SLEEP* abstract.
72. https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=34170248&rettype=abstract&retmode=text. Charest et al. 2021 abstract.
73. https://pmc.ncbi.nlm.nih.gov/articles/PMC8636381/. Charest et al. 2021 full text: n = 3,005, lme4, P values, raw east/west win rates.
74. https://experts.arizona.edu/en/publications/impacts-of-travel-distance-and-travel-direction-on-back-to-back-g/. Charest et al. bibliographic record.
75. https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=38689400&rettype=abstract&retmode=text. Özdalyan et al. 2024 abstract.
76. https://sciencedaily.com/releases/2024/05/240501091642.htm. Özdalyan et al. press release: 63.5% vs 55.0%, limitations.
77. https://www.si.com/college/iowa-state/basketball/ncaa-tournament-start-times-channel-information-for-all-first-round-games-01jpgr59k55m. 2025 first-round tip times (CT).
78. https://dailyillini.com/news/2005/03/02/tourney-tickets-hard-to-come-by/. Big Ten 1,000-ticket cap, reallocation; Illinois 2,400; NCAA 350/1,250/4,500.
79. https://iuhoosiers.com/news/2012/11/12/How_IU_s_Big_Ten_Tournament_Tickets_Are_Allocated (via curl; WebFetch returned only the title). Equal seating levels; location by conference rotation.
80. https://uwbadgers.com/sports/2015/08/21/GEN_20140101657 (via curl). 2026 Big Ten women's tournament: seat locations by standings.
81. https://mndaily.com/?p=239086 (via curl). 2010 student allotment of 75; Iowa and Penn State declined allotments; the 2008 anecdote.
82. https://www.hammerandrails.com/2021/3/4/22313224/big-ten-announces-limited-fan-capacity-for-big-ten-tournament (via curl; WebFetch 403). 2021 cap of 8,000 at Lucas Oil Stadium.
83. https://fightingillini.com/news/2021/3/4/mens-basketball-big-ten-tournament-ticket-information-for-illinois (via curl). 2021 Illinois allocation; 50 student tickets.
84. https://wsbt.com/news/nation-world/ncaa-allows-limited-fan-attendance-at-mens-tournament-games-02-19-2021 (via curl). AP, 19 Feb 2021: 25% including participants, staff and families; Assembly Hall 500.
85. https://www.insideindianabusiness.com/story/43378974/ncaa-allowing-limited-fans-for-march-madness (via curl). Same announcement; "attendance levels could vary by venue".
86. https://en.wikipedia.org/w/api.php?action=parse&page=2021_NCAA_Division_I_men%27s_basketball_tournament&prop=wikitext. 2021 venues and QIDs, the 4 Jan announcement, no pods, artificial crowd noise, VCU-Oregon no-contest.
87. http://fs.ncaa.org/Docs/stats/m_basketball_RB/2022/Attend.pdf. NCAA 2021 attendance summary: per-game attendance by site; annual tournament attendance.
88. https://arxiv.org/abs/1806.08059 and https://arxiv.org/pdf/1806.08059. Karl, HFA trends (Table 4; §3.3.1).
89. https://www.cbssports.com/college-basketball/news/how-the-home-court-advantage-in-college-basketball-is-shrinking-this-season-due-to-fewer-fans-at-games. Home win % of 64.3% (1996-97) vs 57.3% (2020-21).
90. https://rushthecourt.net/tag/friday-figures/. Secondary pointer to KenPom's foul-advantage study.
91. https://trace.tennessee.edu/utk_geogpubs/27/ and https://trace.tennessee.edu/bitstreams/ce3b042d-a302-4311-aafa-987e53228599/download. Cooper & Davis 2019, record and PDF (Table 1, methods).
92. https://support.google.com/trends/answer/4365533?hl=en. Google Trends normalisation, sampling and noise.
93. https://github.com/fivethirtyeight/data/blob/master/nfl-fandom/README.md and https://github.com/fivethirtyeight/data/tree/master/nfl-fandom. DMA-level Trends fandom dataset.
94. https://nces.ed.gov/ipeds/survey-components/7. IPEDS Completions component.
95. https://ccsenet.org/journal/index.php/ijsp/article/view/47409 and https://ccsenet.org/journal/index.php/ijsp/article/download/47409/27390. Phillips, Caudill & Mixon 2015 (Tables 1 and 3).
96. https://en.wikipedia.org/w/api.php?action=parse&page={YEAR}_NCAA_Division_I_{women's|men's}_basketball_tournament&prop=wikitext, for 2008-2019 and 2021-2025. Brackets and host lists parsed by `tournament_host_records.py`.
97. https://thebutlercollegian.com/2025/04/ot-womens-home-court-advantage-in-march-madness/. Record 2024 first- and second-round attendance (292,456).

**Opened but blocked in this pass (not used for claims):**
- kenpom.com `blog/?p=146` and `blog/wp-json/wp/v2/posts/146`: 403 / Cloudflare.
- tandfonline.com (Özdalyan full text): 403.
- WTHR and Sports Travel Magazine (2021 capacity): 403.
- thegazette.com: 429.
- bigten.org articles: 404.
- sportico.com: redirected to a paid-access gateway, not followed.
- fivethirtyeight.com: redirects to abcnews.com.
- pubmed.ncbi.nlm.nih.gov web pages: cookie wall, so the E-utilities API was used instead.
