# College Basketball Data Sources: Catalog for the MSU Men's Basketball Research Project

Compiled 18 Oct 2026. Every source below was checked live on that date unless marked **unverified**. Prices are as currently listed. "Verified" means I opened the page, API response or document myself. A search snippet alone never counts as verification.

**Scope:** NCAA Division I men's basketball, with Michigan State (Big Ten) as the target team. ESPN team id for MSU is `127`. MSU's Torvik name is `Michigan St.`.

**Status on 18 Oct 2026:** The 2026-27 season (season id "2027") is in preseason. KenPom shows "2027 Pomeroy College Basketball Ratings" with every team 0-0. Torvik's `trank.php` redirects to `trankpre.php`, its preseason page. The last completed season is 2025-26 ("2026").

---

## 0. Quick summary table

| # | Source | Cost (Oct 2026) | Access | Seasons (verified) | Finest granularity | Research-use terms (short) |
|---|---|---|---|---|---|---|
| 1 | KenPom | Web $24.95/yr. API $145/yr (includes web) | Web (subscriber pages), official API, kenpompy/hoopR/cbbdata scrapers | Ratings from 1999. Height from 2007. Continuity from 2008. Refs from 2016 | Team-season, team-game (FanMatch, box scores), player-season and player-game | Web: no bots or scrapers without permission; fair use with citation. API: personal/non-commercial use, explicitly incl. academic study and model building; no public redistribution |
| 2 | Bart Torvik / T-Rank | Free | Web plus undocumented CSV/JSON files; cbbdata R API | 2008 to present (CSV for 2008 confirmed) | Team-season, team-game, player-season, player-game | No terms page found. Site says "Compiled by Bart Torvik from publicly available data." |
| 3 | EvanMiya | Free / Basic $2.50 mo ($30/yr) / Premium $15 mo ($179.99/yr) / Front Office Suite (contact) | Web; CSV export on Basic | Historical ratings back to 2009 | Player-season (BPR), lineup (2-5 man), team-season, game predictions | ToS: no automated access that harms the site; fair use with citation; no redistribution |
| 4 | Haslametrics | Free (voluntary Venmo) | Web only | 2014-15 to 2026-27 | Team-season (PBP-derived) | About page: data "free of charge and can be used as desired"; cite with a link |
| 5 | ESPN BPI and ESPN hidden APIs | Free (undocumented) | JSON APIs: site.api, sports.core.api | PBP/shots via hoopR: 2006+ (2003 also for shots; 2004-05 gap) | Play (with x,y), in-game WP per play, odds per provider, officials | Disney ToU bans robots/scrapers and data-set compilation; unofficial API, no SLA |
| 6 | NCAA (stats.ncaa.org, ncaa.com NET) | Free | Web (stats.ncaa.org blocks this environment: HTTP 403); ncaa.com NET page; henrygd/ncaa-api wrapper | NET since 2018-19; stats.ncaa.org PBP 2010+, shot locations 2019+ (per hoopR docs) | Team, player, game, PBP | Official source; terms **unverified** (site unreachable here) |
| 7 | Sports-Reference CBB | Free web; Stathead "as low as $9/month"; custom datasets ≥$1,000 | Web (20 req/min bot limit) | Box scores searchable 2010-11 onward | Team-season, player-season, game box | No scrapers that degrade the site; **no AI/ML training or prediction use without permission** |
| 8 | CBBD (CollegeBasketballData.com) | Free key; Patreon Tier 1+ $1, Tier 2+ $5, Tier 3+ $10 per month | REST API (OpenAPI v1.30.1), Python `cbbd` 1.30.1 (9 Oct 2026), CSV exporter, Starter Pack | Box/season stats 2002-03+; PBP 2005-06+; shot distribution 2013-14+; substitutions/lineups 2023-24+ | Play, substitution, lineup, game, player, season | Commercial and research use allowed; caching, model training and derived outputs allowed; no raw-data redistribution or mirroring; scraping prohibited |
| 9 | hoopR / sportsdataverse | Free (MIT) | R package (CRAN 3.1.0, 25 Aug 2026); prebuilt release files | ESPN 2006+; NCAA-engine data 2010+ (shots 2019+) | Play, shot, possession, lineup stint, RAPM | Package is MIT; underlying ESPN/NCAA terms still apply |
| 10 | CBBpy | Free (Apache-2.0) | Python scraper of ESPN | Any ESPN game | Game info (incl. referees), box, PBP with shot_x/shot_y | Same ESPN-terms caveat; last release 2.1.2 (20 Jan 2025) |
| 11 | cbbdata (R) | Free API key | R package to a Flask API | Torvik plus KenPom (KenPom needs your own subscription) | Same as Torvik and KenPom | Updated every 15 min in season; KenPom access tied to your subscription email |
| 12 | Synergy Sports (Sportradar) | Not listed (team, media and B2B licensing) | Synergy Basketball app/video; Synergy APIs for media/fantasy | **Unverified** | Possession and play type, video | All D-I teams use Synergy (Sportradar blog); no individual or academic offer found |
| 13 | ShotQuality | ShotQuality Bets **closed to new sign-ups**; B2B pivot | Web/API (existing members), B2B | **Unverified** | Shot-level expected value | Now aimed at "sportsbooks, syndicates, and prediction markets" |
| 14 | Hoop-Math | **Unverified** (site unreachable; upstream 502) | Web | Unknown | Team/player shot splits | n/a |
| 15 | Massey Ratings | Free web; "Export" menu item | Web (Cloudflare) | cb2026 listed | Team-season ratings, composite of many systems | Proprietary; no copying or redistribution; **no AI/ML training without consent** |
| 16 | The Prediction Tracker | Free | Web with CSV season files | NCAA basketball 2003-04 to 2025-26 | Game predictions for many systems | No terms seen |
| 17 | Sportradar NCAAMB API v8 | B2B; free trial via Marketplace; pricing not public | REST, push feeds | "Seasons" endpoint (range **unverified**) | PBP (Full-coverage games incl. Big Ten), box, NET/RPI, transfer portal | B2B service; terms per contract |
| 18 | Second Spectrum / Hawk-Eye / ShotTracker tracking | Not public | Team-licensed | n/a | Player/ball tracking | No public college tracking feed found |
| 19 | Recruiting: 247Sports, On3/Rivals | Free web (premium content paid) | Web | 247 Composite 2026 class (408 players) checked; On3 "Rivals Industry" 2026 checked | Player (recruit) | CBS ToU bans scraping and data mining; On3 terms **unverified** (403) |
| 20 | Transfer portal: On3, CBBD `/recruiting/portal`, Sportradar, Torvik | Free / API | Web, API | On3 2026 portal; CBBD historical | Player-transfer event | As per each source |
| 21 | NBA Draft Combine (nba.com/stats) | Free | Web; `stats.nba.com` endpoints (`nba_api`) | 2000-01 to 2026-27 selectable | Player measurement | NBA ToU: stats for news or "private, non-commercial purposes" only |
| 22 | Referee data: ESPN officials, KenPom Ref Ratings, hoopR `load_mbb_officials` | Free / KenPom subscription | API, web | ESPN per game; KenPom from 2016 | Game-official | As per source |
| 23 | The Odds API | Free 500 credits/mo (no historical); $30/$59/$119/$249 per month | REST API | NCAAB historical from 2020-11-16 | Odds snapshot (5-10 min) by bookmaker | Storage, research and ML allowed; no resale as a raw feed |
| 24 | SBRO (sportsbookreviewsonline) | Free | XLSX downloads | 2007-08 to 2021-22 (no longer updated) | Game: open/close spreads and totals, ML, 2H lines | No archive-specific terms shown |
| 25 | Kalshi | Free public market data API | REST | 111 NCAAMB / March Madness series listed | Market price, trades, candlesticks | Kalshi API terms (not reviewed in depth) |
| 26 | Polymarket | Free public API | Gamma API (events), CLOB `prices-history` | CBB game moneylines from 2025-26 season; March Madness | Price time series (1-min fidelity) | Not reviewed in depth |

---

## 1. Source-by-source detail

### 1.1 KenPom (kenpom.com)

- **URL:** https://kenpom.com/ (API: https://kenpom.com/register-api.php)
- **Cost:** Web subscription $24.95 for 12 months. API $145.00 per year, including web access. "All sales are final." Gift subscriptions are sold separately.
- **Access:**
  - The home ratings table is free.
  - Everything else needs a subscriber login: `stats.php`, `playerstats.php`, `height.php`, `fanmatch.php`, `officials.php` and the rest. I confirmed that `height.php`, `playerstats.php` and `fanmatch.php` return "available to subscribers only."
  - Official API endpoints: `ratings` (ratings, SOS, tempo, possession length), `archive` (historical and preseason ratings), `four-factors`, `pointdist`, `height` (height and experience), `misc-stats`, `fanmatch` (archived game predictions), `conf-ratings`, `program-ratings`, `teams`, `conferences`.
  - Third-party scrapers that need your own subscription: `kenpompy` (Python, v0.5.0, 2 Nov 2025, GPL-3), hoopR's KenPom functions, and cbbdata's `cbd_kenpom_ratings` and `cbd_kenpom_ratings_archive`.
- **Seasons (from kenpompy docs):** Pomeroy ratings, efficiency, four factors, point distribution and team stats from 1999. Possession-length data from 2010. Height/experience from 2007, with continuity from 2008. Player stats from 2004. Officials from 2016. Arenas from 2010. KPOY from 2011. Team and coach history since 1997 (tour page).
- **Granularity:** team-season, conference-season, team-game (schedule with predictions, box scores, win-probability charts), player-season, player-game (game-by-game breakdowns, "minutes matrix"), official-season.
- **Parameters:**
  - **Public table columns now shown:** Rk, Team, Conf, W-L, NetRtg, ORtg, DRtg, AdjT, Luck, SOS NetRtg/ORtg/DRtg, NCSOS NetRtg. The glossary still describes the older Pyth (exponent 11.5) and AdjO/AdjD naming.
  - **Definitions (glossary):**
    - AdjO/AdjD: points scored or allowed per 100 possessions vs an average D-I team.
    - AdjT: possessions per 40 minutes vs average pace.
    - Luck: actual win% minus the win% implied by game-by-game efficiencies.
    - Possessions: FGA − OR + TO + 0.475×FTA.
  - **Team page help:**
    - Four factors on offense and defense: eFG%, TO%, OR%, FTRate.
    - Blk%, Stl%.
    - SOS (average adjusted efficiency of opposing offenses and defenses).
    - Bench Minutes: share of minutes by non-starters.
    - Effective Height, Average Height (minutes-weighted), Experience (minutes-weighted class, Fr = 0).
    - Height by position and points by position.
  - **Player stats (team page help and Individual Stats Primer):** G, %Min, ORtg (Dean Oliver), %Poss, %Shots, eFG%, TS%, OR%, DR%, ARate, TORate, %Blocks (Blk%), %Stls, FC/40, FD/40, FTRate, plus splits. Conference-only stats, stats vs top-50/100 opponents, player history and biography.
  - **Other pages in the navigation:**
    - Point Distribution: share of points from FT, 2P and 3P.
    - Height/Experience, including Continuity (kenpompy docs).
    - Misc. Team Stats.
    - FanMatch: daily predictions with predicted score and win probability, plus daily MAE of the predicted margin and total, bias, favourites' actual vs expected record, and "lines of the night."
    - Game attributes: Excitement, Tension, Dominance, ComeBack, FanMatch, Upsets, Busts.
    - Ref Ratings, Home Court Ratings, Jump Ball Ratings, Arena Capacity, D-I stats trends, program ratings, KPOY and game MVP.
    - Team page lineup usage and depth chart.
- **Terms:**
  - The web ToU prohibits "any automated means to access or use the Web Site" (scripts, bots, scrapers, data miners) without written permission.
  - It also prohibits redistribution beyond personal non-commercial extracts and building a competing database.
  - Fair use with citation is "acceptable and encouraged."
  - The API terms permit personal, non-commercial use, explicitly including "academic study" and model building, with attribution. They forbid public display, redistribution or bulk extraction beyond rate limits.
  - **Implication:** for an automated pipeline, the $145 API is the compliant route. Scraping the $24.95 web subscription with kenpompy technically breaches the web ToU.
- **Reliability/independence:** This is the de facto industry reference. It is used by the NCAA committee's team sheets and by media. Methodology is proprietary but described at a high level. It is independent of the NCAA. The EvanMiya 2026 test (Section 4) has it roughly tied for best game-spread accuracy over 2023-26.

### 1.2 Bart Torvik / T-Rank (barttorvik.com)

- **URL:** https://barttorvik.com/trank.php (preseason page: `trankpre.php`)
- **Cost:** Free. Ad and donation supported.
- **Access:**
  - HTML pages sit behind a simple JS check. A cookie `js_verified=true` is set after a POST.
  - Static data files are directly downloadable. All of these were fetched successfully on 18 Oct 2026:
    - `https://barttorvik.com/{YEAR}_team_results.csv` and `.json`: 45 columns. Rank, team, conf, record, adjoe, oe Rank, adjde, de Rank, barthag, proj. W/L, projected conference W/L, Con Rec., sos, ncsos, consos, Proj. SOS (overall, non-con, conference), elite SOS, elite noncon SOS, Opp OE/DE, Opp Proj. OE/DE, Con Adj OE/DE, Qual O, Qual D, Qual Barthag, Qual Games, FUN, ConPF, ConPA, ConPoss, ConOE, ConDE, ConSOSRemain, Conf Win%, WAB, WAB Rk, Fun Rk, adjt. The 2008 file also works.
    - `https://barttorvik.com/{YEAR}_fffinal.csv`: team four factors and shooting, offense and defense with ranks. eFG%, FTR, OR%, DR%, TO%, 3P%, 2P%, FT%, 3P rate, assist rate.
    - `https://barttorvik.com/getadvstats.php?year={YEAR}&csv=1`: player-season advanced stats. The CSV has no header row; there were 4,977 player rows for 2026. Columns are positional; see the cbbdata/toRvik docs for mapping.
    - `https://barttorvik.com/{YEAR}_super_sked.csv`: every game with T-Rank pre-game projection, win probabilities, result, tempo and both teams' ratings.
  - R: `cbbdata` (free key) wraps Torvik. It covers year-end and daily ratings archive, team factors, player game logs, season and splits, game box and four factors, schedules, game and season predictions and simulations, tournament results, team sheets, resumes and NET archive.
- **Seasons:** 2008 to present. The game-stat page lists 2008 through 2026.
- **Granularity:** team-season (with date-range and opponent-quality slicing via `trankslice.php`, Q-Rank and H-Rank), team-game, player-season, player-game (box page shows per-player game advanced stats), daily rating snapshots ("T-Rank Time Machine").
- **Parameters:**
  - **Team table:** AdjOE, AdjDE, Barthag, EFG%, EFGD%, TOR, TORD, ORB, DRB, FTR, FTRD, 2P%, 2P%D, 3P%, 3P%D, 3PR, 3PRD, Adj T., WAB.
  - **Team page:**
    - Shooting and stylistic stats: 3P rate, assist rate, block%, adjusted tempo.
    - "Fun Stuff": Qual. Eff., Last-10 Eff.
    - Expected SOS and committee resume metrics: Q1-A, Q1-Q4 records.
    - Game log: WAB, AdjO, AdjD, EFF, eFG%, TO%, OR%, FTR, 2P, 3P, G-Sc, +/-, PPP.
  - **Player stats:**
    - Ratings and rates: O-Rating, Usage, eFG%, TS%, TOV rate, O-Reb%, D-Reb%, FT rate, Foul/40, FT%, 2P%, 3P%, FTA/2PA/3PA, Assist%, Steal%, Block%, Min%, Height.
    - Value metrics: **PORPAGATU!**, **D-PORPAG**, Adj. D-Rtg, BPM/OBPM/DBPM (plus "Old" versions), **Role**, Pick (draft-pick probability), **RecruiT-Rank**.
    - Shot types: Dunks, 3P/100 poss., Rim attempts/makes/%, Mid attempts/made/%.
  - **Game box (`box.php`):** per player Min, ORtg, Usg, eFG, TS%, OR%, DR%, A%, TO%, Stl%, Blk%, Dunk, Rim, Mid, 2Pt, 3Pt, FT, Ast, TO, Stl, Blk, OR, DR, PF, BPM, OBPM, DBPM, NET, Pts, and game possessions.
  - **Team play-type and shot-type table (`teampbp.php`):** Dunks, Close Twos, Farther Twos, Threes, with share and FG% on offense and defense. This is Torvik's "style" data. It covers shot types, not Synergy-style play types.
  - **"GameScript":** the site menu has "Implied T-Rank: T-Rank derived from +/- GameScripts" (`implied-trank.php`). That is game-flow margin data. The exact definition of a GameScript is **unverified**.
  - **Other pages:** transfer lists (`playerstat.php?xvalue=trans`), coaching moves, tournament and conference simulations (`tourneycast`, `concast`), T-Rankings for NET forecast (`net4cast`), team sheets, bubble guide, resume compare, Elo rank.
- **Terms:** No ToS page was found. Pages carry "Compiled by Bart Torvik from publicly available data." Treat the data as free for research with attribution. Throttle requests. Redistribution terms are **unverified**.
- **Reliability:** Long-running (2008+) and transparent about inputs. It is cross-linked with KenPom and widely used in media. It is roughly one step behind KenPom and EvanMiya on 2023-26 spread MAE (EvanMiya test). It is a one-person operation, so endpoints are undocumented and can change.

### 1.3 EvanMiya (evanmiya.com)

- **URL:** https://evanmiya.com/ (plans: https://evanmiya.com/subscribe; methodology: https://evanmiya.com/how-it-works)
- **Cost:** Free $0. Basic $2.50/month or $30/year. Premium $15/month or $179.99/year. Front Office Suite by contact.
- **Free tier:** team ratings, player ratings and advanced player metrics, historical ratings back to 2009.
- **Basic adds:** game predictions with Vegas odds, full transfer-portal rankings, lineup ratings and chemistry, **CSV export**.
- **Premium adds:** lineup grades and optimisation, Keys to Victory, injury reports and line adjustments.
- **Front Office Suite adds:** NIL value for every D-I player and a custom big board.
- **Access:** Web only (Next.js). CSV export starts at Basic. No API found.
- **Granularity:** player-season, 2-, 3-, 4- and 5-man lineups (opponent-adjusted), team-season, game predictions, preseason projections. The homepage shows a 2025-26 lineup sample and 2026-27 preseason rankings.
- **Parameters:**
  - **BPR (Bayesian Performance Rating)** with OBPR and DBPR. Inputs are advanced box score, play-by-play on-court data and historical information. It adjusts for teammates and opponents on the floor.
  - Team O-Rate, D-Rate, net, roster strength.
  - Lineup observed efficiency, margin and possessions.
  - Player projections: projected 3P%, playmaking score, rebound%.
  - "Indispensability" ranking. Conference strength.
- **Terms (Google Doc linked in footer):**
  - Fair use with citation is "acceptable and encouraged."
  - Copying large portions of subscriber content is prohibited.
  - Redistribution is prohibited except personal, non-commercial local extracts.
  - Automated access that "adversely impacts site performance" is prohibited without written permission.
- **Reliability:** It is used by college staff (testimonials) and is independent. The site's own 2026 study (conflict of interest) puts it on par with KenPom for game prediction over 2023-26. The BPR math is not fully public; the blog describes it.

### 1.4 Haslametrics (haslametrics.com)

- **URL:** https://haslametrics.com/ (About: https://haslametrics.com/about.php)
- **Cost:** Free. Voluntary Venmo support; the operator is a for-profit LLC.
- **Access:** Web tables only.
- **Seasons:** time-dependent and time-independent ratings 2014-15 to 2026-27. Ratings usually appear in late November. Time-independent ratings are published only after the season.
- **Granularity:** team-season (with automated team capsules).
- **Parameters:**
  - **Offense and Defense summaries:** Eff, FTAR, FT%, FGAR, FG%, 3PAR, 3P%, MRAR, MR%, NPAR, NP% (near-proximity), PPSt, PPSC, SCC%, %3PA, %MRA, %NPA, Prox (shot proximity).
  - **Records summary:** results vs rank bands 1-50 through 301+, CQ1-CQ4, Home, Away, Neutral.
  - **Fingerprint:** Pace, Mom, MomO, MomD (momentum), Con, ConR (consistency), SOS, PTF, RQ, AFH, RPI, ASR, Rk1/Rk7/Rk30/RkPS.
  - **Performance:** Lst5WL, Lst5Perf, LastPerf, BestPosPerf, WorstNegPerf, AP% (all-play percentage).
- **Methodology:**
  - Built from play-by-play logs, available for more than 90% of games; box score extrapolation fills the rest.
  - Models shot frequency, shot proximity and accuracy by area, and how steals and offensive rebounds affect shot selection.
  - **Garbage time is removed:** data is cut once a game is decided.
  - Explicitly rejects the four-factor regression approach.
  - Preseason baselines are used since 2020-21.
- **Terms:** The site says its data is free of charge and can be used as desired. Cite it with a link back. Logos and names are NCAA property.
- **Reliability:** Independent and methodologically distinct, being shot-location and garbage-time aware. No published historical game-prediction logs exist; EvanMiya excluded it from its test for that reason.

### 1.5 ESPN BPI and ESPN APIs

- **URLs:**
  - BPI web page: https://www.espn.com/mens-college-basketball/bpi (JS-rendered; I could not read it as text).
  - APIs: `site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/...` and `sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/...`
  - Community documentation: https://github.com/pseudo-r/Public-ESPN-API
- **Cost:** Free, unauthenticated and undocumented.
- **Endpoints verified on 18 Oct 2026 (MSU vs Arkansas, event 401826785, 2025-11-09):**
  - **`summary?event={id}`** returns `boxscore`, `plays` (509), `winprobability` (507 entries, `homeWinPercentage` keyed by `playId`), `pickcenter`, `odds`, `againstTheSpread`, `gameInfo` (venue, attendance, **officials**), `leaders`, `broadcasts`.
    - Play fields: id, sequenceNumber, type (id/text), text, scores, period, clock, scoringPlay, scoreValue, team, participants (athlete ids), wallclock, shootingPlay, **coordinate {x,y}**, pointsAttempted.
    - Team box fields: FG/3P/FT made-attempted and %, total/off/def rebounds, assists, steals, blocks, turnovers (incl. team), technical and flagrant fouls, turnoverPoints, fastBreakPoints, pointsInPaint, fouls, largestLead.
    - Player box fields: minutes, points, FG, 3P, FT, rebounds (off/def), assists, turnovers, steals, blocks, fouls.
  - **Core `.../competitions/{id}/odds`:** per provider (here "ESPN BET"): spread, overUnder, over/under odds, moneylines, and **open/close/current** spread and moneyline in American, decimal and fraction formats.
  - **Core `.../competitions/{id}/predictor`:** matchupquality, rawgamescore, teampredwinpct, teampredmov, opponentpredwinpct, gameProjection, teamChanceLoss, teamChanceTie.
  - **Core `.../competitions/{id}/probabilities`:** per-play home/away/tie win%.
  - **Core `.../competitions/{id}/officials`:** official id, name, position, order.
  - **Core `.../seasons/{yr}/powerindex[/teamId]`** (BPI), 58 stats:
    - Ratings: bpi, bpioffense, bpidefense (and ranks), 7-day rank change.
    - Resume: sor, sorrank, sospast, sosoutofconfpast, sosremrank, top50bpiwins/losses, qualitywinpct.
    - Projections: projtotalwins/losses, projconfwins/losses, chancewinconfortie, projectedtournamentseed, chances for R32, S16, E8, F4, final and champion.
    - Definition: "expected point margin per 70 possessions vs an average opponent on a neutral court; BPI = BPI OFF + BPI DEF."
- **Seasons:** ESPN PBP and shots via hoopR's data repo cover 2006 to present; shots also 2003, with 2004-05 a documented gap.
- **Terms:**
  - The Disney ToU forbids extracting content "using a robot, spider, script, or other automated means... data mining or web scraping or otherwise compiling... any collection of data, data set or database."
  - The APIs are "not officially supported and may change without notice" (pseudo-r).
  - Legally this is the weakest footing of the free sources, even though it is universally used by open-source packages.
- **Reliability:** The PBP/shot feed is the broadest free play-level data. Coordinates are on ESPN's own grid; one sample showed x=27, y=25 for a 3-point attempt, so normalise them. BPI is a strong predictive model built in-house.

### 1.6 NCAA: stats.ncaa.org, NET, ncaa.com

- **URLs:**
  - https://stats.ncaa.org/
  - NET: https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings
  - Explainer: https://www.ncaa.com/news/basketball-men/article/2022-12-05/college-basketballs-net-rankings-explained
- **Access:**
  - stats.ncaa.org returned **HTTP 403 (Akamai "Access Denied")** to this environment, including `robots.txt`. Its current contents and terms are **unverified** from here.
  - hoopR's NCAA engine documentation states that stats.ncaa.org play-by-play is parsed for 2010+ and that **shot-location data was not published before 2019**.
  - ncaa.com pages load. The open-source `henrygd/ncaa-api` (MIT) wraps ncaa.com JSON: scoreboard, game box, PBP, team and individual stats, rankings, standings, brackets. It has a 5 req/s public demo and can be self-hosted.
- **NET page columns:** Rank, School, Record, Conf, Road, Neutral, Home, Non-Div I, Prev, Quad 1-4. Labelled "Through Games Apr. 06 2026."
- **NET definition (ncaa.com explainer, updated May 2025):**
  - Since 2020-21 it has two components: Team Value Index (results-based, rewards beating good teams, especially away) and adjusted net efficiency (per 100 possessions, opponent- and site-adjusted).
  - Game date and order are not used.
  - Built with Google Cloud. It replaced the RPI in 2018-19.
- **Quadrants:**
  - Q1: Home 1-30, Neutral 1-50, Away 1-75.
  - Q2: 31-75 / 51-100 / 76-135.
  - Q3: 76-160 / 101-200 / 135-240.
  - Q4: the rest.
- **Archives:** daily NET is available via cbbdata `cbd_net_archive()` and Sportradar's NET/RPI rankings endpoint.
- **Reliability:** Official, and the only source for committee-facing metrics. The TVI formula is not public.

### 1.7 Sports-Reference College Basketball (sports-reference.com/cbb)

- **URL:** https://www.sports-reference.com/cbb/ (data use: https://www.sports-reference.com/data_use.html; bots: https://www.sports-reference.com/bot-traffic.html)
- **Cost:** Free web. Stathead "as low as $9/month" with a free first month. Custom datasets cost at least $1,000 per request.
- **Access:** HTML tables (with CSV export in the browser). Bots are limited to **20 requests/minute**; exceeding it gets the session "in jail" for up to a day.
- **Seasons:** Box scores searchable 2010-11 to present. Women's data from 1987-88. Earliest men's season is **unverified**.
- **Fields (parsed from the 2026 pages):**
  - **School ratings:** AP rank, W, L, PTS/G, Opp PTS/G, MOV, SOS, SRS (OSRS, DSRS, SRS), adjusted ORtg, DRtg, NRtg.
  - **Advanced school stats:** G, W-L, SRS, SOS, conference/home/away records, pace, ORtg, FTr, 3PAr, TS%, TRB%, AST%, STL%, BLK%, eFG%, TOV%, ORB%, FT/FGA.
  - **Team page:** roster (class, pos, height, weight, hometown, high school, **RSCI** rank); team and opponent totals and per game; player per game, totals, per 40, per 100 possessions (with ORtg and DRtg); conference-only splits.
  - **Player advanced:** PER, TS%, 3PAr, FTr, PProd, ORB%, DRB%, TRB%, AST%, STL%, BLK%, TOV%, USG%, OWS, DWS, WS, WS/40, OBPM, DBPM, BPM.
- **Terms:**
  - Facts may be reused.
  - No bots that adversely affect performance.
  - No competing databases.
  - **Explicitly no use of site content "to train, fine-tune, prompt, or instruct AI models" or to support ML that predicts, classifies or scores, without permission.**
  - This makes SR unsuitable as an ML training source for this project without written permission.
- **Reliability:** Very clean historical box data, mirrored from official stats. Independent.

### 1.8 CBBD: CollegeBasketballData.com

- **URLs:**
  - https://collegebasketballdata.com/
  - API docs: https://api.collegebasketballdata.com/ (OpenAPI JSON: `/api-docs.json`, v1.30.1, MIT)
  - Tiers: https://collegebasketballdata.com/api-tiers
  - Terms: https://collegebasketballdata.com/terms
- **Cost:** Free API key, plus Patreon tiers:
  - Tier 1+ $1/mo: chart export, ad-free.
  - Tier 2+ $5/mo: full Team Metrics and Shooting Profile explorers, `stats/team/leaderboard`.
  - Tier 3+ $10/mo: priority support.
  - The live `/scoreboard` needs Tier 1+.
  - Numeric monthly call quotas are not listed on the site (they are on Patreon) and are **unverified**. Football and basketball share one quota.
- **Access:** REST with bearer key. Python `cbbd` 1.30.1 (released 9 Oct 2026). Web CSV exporter. "Starter Pack" of 119 historical CSVs and 16 notebooks through 2025-26.
- **Coverage (documented):** season and box-score statistics 2002-03+; play-by-play 2005-06+; shot distribution 2013-14+; substitutions and lineups 2023-24+. Game data is updated "within minutes after game completion."
- **Endpoints (from OpenAPI):**
  - `/games`, `/games/teams`, `/games/players`, `/games/media`
  - `/plays/game|player|team|date|tournament`, `/plays/types`
  - `/substitutions/game|player|team`
  - `/lineups/team`, `/lineups/game`
  - `/lines`, `/lines/providers`
  - `/ratings/adjusted|srs|elo`, `/rankings`
  - `/stats/team/season`, `/stats/team/shooting/season`, `/stats/player/season`, `/stats/player/shooting/season`, `/stats/team/leaderboard`
  - `/recruiting/players|teams|portal`
  - `/draft/picks|teams|positions`
  - `/teams`, `/teams/roster`, `/teams/directory`, `/teams/{id}/season/{season}/overview`
  - `/conferences`, `/conferences/history`, `/venues`, `/scoreboard`
- **Key schemas:**
  - **PlayInfo:** gameId, season, period, clock, secondsRemaining, scores, **homeWinProbability**, playType, scoringPlay, shootingPlay, scoreValue, wallclock, playText, participants, **onFloor**, shotInfo.
  - **ShotInfo:** shooter, made, range, assisted, assistedBy, location.
  - **LineupStats:** athletes, totalSeconds, pace, offense/defense/net rating, team and opponent unit stats (possessions, points, TS, four factors...).
  - **GameLineInfo:** provider, spread, overUnder, home/away moneyline, spreadOpen, overUnderOpen.
  - **PlayerSeasonStats:** games, starts, minutes, usage, offensive/defensive/net rating, **PORPAG**, eFG, TS, AST/TO, FTr, ORB%, **winShares**.
  - **GameInfo:** home/away Elo start and end, **excitement**, attendance, venue, seeds.
  - **Transfer:** origin, destination, eligibility, yearsRemaining, stars, rating.
  - **Recruit:** heightInches, weightPounds, stars, rating, ranking, committedTo.
  - **PlayerSubstitution:** subIn, subOut.
- **Terms:**
  - "Commercial use is permitted."
  - Research, caching, backtesting, model training and selling derived outputs are allowed.
  - Prohibited: publishing raw data as a standalone dataset or bulk download, mirroring, proxying, exposing your key, presenting the data as official, and scraping or excessive polling.
  - Attribution is appreciated but not required.
- **Reliability:** A solo project (Rad Sports Analytics LLC; also runs CollegeFootballData). Code is open source. It labels the data "unofficial" and does not name upstream sources. Plays, lineups and lines look like they derive from public feeds, but that is **unverified**. Best-licensed free API in this list.

### 1.9 hoopR (R) / sportsdataverse (Python)

- **URL:** https://hoopr.sportsdataverse.org/ (CRAN v3.1.0, published 25 Aug 2026, MIT). Python `sportsdataverse` 0.1.4 (1 Sep 2026).
- **What it provides:**
  - **ESPN-based `load_mbb_*`:** pbp, team_box, player_box, schedule, rosters, player/team stats, standings, game_rosters, **officials**, player_core, **shots** (coordinate_x/y and raw).
  - **`espn_mbb_*` live functions:** incl. betting, odds, officials, win probabilities, prop bets.
  - **`fox_mbb_*`** functions.
  - **Crosswalks** linking ESPN, KenPom, Torvik and Fox IDs. Very useful for joining sources.
  - **New NCAA engine (`load_ncaa_mbb_*`)**, built from stats.ncaa.org PBP:
    - pbp with reconstructed 5-man lineups, possession numbering and shot context (transition, paint, second chance).
    - shots: 2019+.
    - lineup stints.
    - 10-man **matchup_stints**.
    - **possessions**, with lineups, points, and assist, transition and garbage-time flags.
    - **within-team RAPM** and **league-wide RAPM** (D-I gated by Torvik).
    - advanced player/team box: rim/mid/3, transition vs half-court, assisted vs unassisted.
    - Most NCAA-engine datasets start in 2010.
  - KenPom scraping for subscribers.
- **Terms:** Package MIT. Underlying source terms apply (ESPN ToU; NCAA **unverified**).
- **Reliability:** Actively maintained and community-validated. It is the easiest way to get free possession and lineup data back to 2010. The derived RAPM is this pipeline's own model.

### 1.10 CBBpy (Python)

- **URL:** https://pypi.org/project/CBBpy/ (v2.1.2, 20 Jan 2025, Apache-2.0)
- Scrapes ESPN for D-I men's and women's games.
- `get_game_info`: teams, scores, records, rankings, date, venue, attendance, TV, **referees**.
- `get_game_boxscore`.
- `get_game_pbp`: play type, shooter, assist, **shot_x/shot_y**.
- Bulk functions by season, range, team or conference.
- The latest release is about 21 months old. Check that it still works before relying on it.

### 1.11 cbbdata (R)

- **URL:** https://cbbdata.aweatherman.com/ (MIT; v0.3.0.9000 development; replaces `toRvik`)
- Free API key via `cbd_create_account`.
- Updated every 15 minutes during the season.
- 46 functions: Torvik ratings (year-end and daily archive), team/conference factors, player game/season/splits, game box/factors/stats, schedules, predictions and simulations, tournament results, committee team sheets, resume database; plus `cbd_all_metrics()` (T-Rank, WAB, KenPom, BPI, SOR/SOS, NET), `cbd_net_archive()` (daily NET), `cbd_ap_rankings()`, `cbd_add_net_quad()`.
- KenPom data needs your own subscription with a matching email.
- Current maintenance status beyond the docs is **unverified**: GitHub was not reachable from this environment.

### 1.12 Synergy Sports (Sportradar)

- **URLs:**
  - https://synergysports.com/ (generic marketing page, no CBB details)
  - Sportradar blogs: https://sportradar.com/content-hub/blog/7-things-you-can-do-with-synergy-basketball-apis/?lang=en-us and https://sportradar.com/content-hub/blog/tap-into-the-data-that-runs-college-basketballs-biggest-tournament/?lang=en-us
- **What it provides:**
  - Tracks "every possession, player movement, and play type" for the NBA, **Division I college**, and top international leagues.
  - Example play types: pick-and-roll, transition, spot-up, isolation, off-ball screens.
  - Shot coordinates, 5-man lineup performance, video breakdowns.
- **Access:** "All NCAA Division I teams use Synergy Basketball" (Sportradar). Programmatic API access is offered to "media outlets and fantasy operators."
- **Price:** Not listed.
- **Individual or academic licensing:** none found (**unverified**).
- **Practical route:** if the project works with MSU's basketball staff, play-type data would come through the team's existing licence and its terms. I have not verified whether that permits research use.

### 1.13 ShotQuality

- **URLs:** https://shotquality.com/ (B2B) and https://www.shotqualitybets.com/pricing
- **Status:**
  - The consumer product "is no longer accepting new sign-ups or subscription purchases." Existing members can still sign in.
  - The company positions itself for "sportsbooks, syndicates, and prediction markets," using computer vision and spatial modelling across NBA, NFL, MLB, NCAA and tennis.
  - Tools still listed: NCAAM regression stats, trends, player analysis, pregame projections, an API with documentation.
- Prices and seasons: **unverified**.
- Not a realistic small-budget option today.

### 1.14 Hoop-Math

- **URL:** https://www.hoop-math.com/
- **Unverified.** WebFetch was blocked by robots rules. Direct connection failed with an upstream 502 on 18 Oct 2026, and the Wayback lookup was rate-limited or blocked.
- Historically it offered shot-type splits (at rim, 2-pt jumpers, 3s), % assisted, and transition vs half-court. Current status and seasons are unknown.
- Torvik's shot-type data (Section 1.2) and hoopR's NCAA engine (Section 1.9) cover the same ground.

### 1.15 Massey Ratings

- **URL:** https://masseyratings.com/cb/ncaa-d1/ratings (terms: https://masseyratings.com/info.php)
- Free web with an "Export" menu item. Cloudflare-protected, and the table is JS-loaded, so I could not read its columns. Columns and the composite page (`compare.htm`) are **unverified**.
- The menu lists `cb2026`.
- **Terms:**
  - All content is proprietary.
  - No copying, distribution or commercial use without written consent.
  - "Use of this website's content to train, fine-tune, or develop artificial intelligence" models is prohibited without consent.
- The composite ranking (many systems' ranks side by side) is valuable for comparison but legally restricted.

### 1.16 The Prediction Tracker

- **URL:** https://www.thepredictiontracker.com/basketball.php
- Free CSV season files: NCAA basketball 2003-04 to 2025-26; NBA 2004-05 to 2025-26.
- The results pages (`ncaabbresults.php`) are behind Cloudflare and could not be read. The list of systems tracked and the accuracy columns are **unverified** here. Historically they included % correct, ATS, MAE and bias for dozens of systems.
- This is the main public long-run archive of many systems' game predictions. Use it to benchmark your own model.

### 1.17 Sportradar NCAA Men's Basketball API (v8)

- **URL:** https://developer.sportradar.com/basketball/reference/ncaamb-overview
- **Feeds:**
  - Schedules (season and daily), game boxscore, summary and **play-by-play**.
  - League hierarchy, teams, team and player profiles, **Transfer Portal**.
  - Standings, seasonal statistics, leaders, awards.
  - AP, USA Today, **NET and RPI** rankings.
  - Tournaments, daily change log, daily transfers.
  - Push events and statistics. "Live event positional data" is listed with no detail.
- **Coverage:** "Full" live PBP for games with reliable broadcasts that include listed conferences (Big Ten included). Otherwise "Extended Boxscore."
- **Access:** B2B with authentication. Free trial via Marketplace. Pricing not public.
- Historical season range: **unverified**.
- Reliable and official-grade, but overkill for a small budget beyond a trial.

### 1.18 Player tracking in college: Second Spectrum, Hawk-Eye, ShotTracker

- I found no public college-basketball tracking data feed (**unverified absence**).
- ShotTracker (article published 17 Mar 2025, updated Nov 2025) reports more than 50 NCAA men's and women's programs as partners. Big Ten partners include Indiana and Purdue. Data goes to teams. Researcher access is not mentioned.
- The NCAA tournament replay system found in coverage is DVSport HD video replay (2015). It is not Hawk-Eye tracking.
- Synergy claims to track "player movement" for D-I (team-licensed).
- **Conclusion:** tracking data is not available for this project except via an MSU staff partnership. The project's own computer-vision pipeline from game footage is the realistic substitute.

### 1.19 Recruiting data

- **247Sports Composite** (https://247sports.com/season/2026-basketball/compositerecruitrankings/):
  - Fields: rank, player, position, Ht/Wt, composite rating (decimal, e.g. 1.0000), high school (city/state), commitment. 408 players in the 2026 class.
  - Terms (CBS Interactive ToU): no "unauthorized spidering, 'scraping,' data mining or harvesting of Content."
- **On3 / Rivals** (https://www.on3.com/rivals/rankings/industry-player/basketball/2026/):
  - Branded "Rivals Industry" on On3, consistent with On3's acquisition of Rivals. The acquisition itself is not stated on the page; date **unverified**.
  - Fields: rank, player, school, position, Ht/Wt, stars plus numeric rating (e.g. 99.25), national, position and state ranks, commitment, status (Committed/Signed/Enrolled), **NIL valuation**.
  - On3 terms returned 403 (**unverified**).
- **Packaged alternatives:** CBBD `/recruiting/players` and `/recruiting/teams` (composite ratings, stars, ranking, height/weight); Torvik **RecruiT-Rank** (player stat); Sports-Reference roster **RSCI** rank.

### 1.20 Transfer portal data

- **On3 Transfer Portal Wire** (https://www.on3.com/transfer-portal/wire/basketball/), 2026:
  - Fields: player, position, Ht/Wt, class, status (Entered, Committed, Expected, Enrolled, Withdrawn) with date, Transfer Portal and HS star ratings, last→new school, NIL column. No stats.
- **CBBD `/recruiting/portal`:** historical. Fields: origin, destination, eligibility, years remaining, stars, rating. Filters by source and destination team or conference.
- **Sportradar:** Transfer Portal and Daily Transfers endpoints.
- **Torvik:** transfer player lists with stats (`playerstat.php?xvalue=trans`) and coaching moves.
- **EvanMiya:** full transfer rankings on Basic.
- **Verbal Commits:** the page returned only a shell; **unverified**.

### 1.21 NBA Draft Combine measurements

- **URL:** https://www.nba.com/stats/draft/combine-anthro. Seasons 2000-01 to 2026-27 are selectable.
- **Endpoints** (documented in `swar/nba_api`; my direct calls to stats.nba.com timed out here):
  - `draftcombineplayeranthro`: HEIGHT_WO_SHOES, HEIGHT_W_SHOES, WEIGHT, WINGSPAN, STANDING_REACH, BODY_FAT_PCT, HAND_LENGTH, HAND_WIDTH.
  - `draftcombinedrillresults`: STANDING_VERTICAL_LEAP, MAX_VERTICAL_LEAP, LANE_AGILITY_TIME, MODIFIED_LANE_AGILITY_TIME, THREE_QUARTER_SPRINT, BENCH_PRESS.
  - Spot-up and non-stationary shooting endpoints also exist (**unverified** here).
- **Terms (nba.com ToU §9):** statistics only for "legitimate news reporting or private, non-commercial purposes"; no use in products featuring a regularly updated stats database without consent.
- **Relevance:** useful only for MSU players who attend the combine. It provides physical priors (wingspan, reach) that no college source has.

### 1.22 Referee data

- **ESPN:** officials per game (name, id, position, order) via `summary` and core `/officials`. Bulk via hoopR `load_mbb_officials()` and CBBpy `get_game_info`.
- **KenPom Ref Ratings** (`officials.php`, subscriber, 2016+).
  - Per a Bless Your Chart write-up: "Ken Pomeroy introduced ratings for officials in 2017"; an official's rating averages the Thrill Score of their top 50 games. It also notes that public officiating data is "rarely aggregated."
  - The exact KenPom fields are **unverified**.
- No dedicated college referee-stats website was found. Basketball-Reference referee pages are NBA-only.
- To build referee features (fouls, FTA, pace, home/away foul differential by crew), join ESPN officials to PBP yourself.

### 1.23 The Odds API

- **URLs:** https://the-odds-api.com/ (historical: https://the-odds-api.com/historical-odds-data/; terms: https://the-odds-api.com/terms-and-conditions.html)
- **Plans:**

  | Plan | Price | Credits per month | Historical |
  |---|---|---|---|
  | Starter | Free | 500 | No |
  | START 20K | $30/mo | 20,000 | Yes |
  | START 100K | $59/mo | 100,000 | Yes |
  | START 5M | $119/mo | 5M | Yes |
  | START 15M | $249/mo | 15M | Yes |

- **NCAAB:** sport key `basketball_ncaab`. Historical data starts **2020-11-16**.
- **Historical details:**
  - Featured markets (h2h, spreads, totals): 10-minute snapshots, 5-minute from Sep 2022.
  - Additional markets (props, period markets): from 3 May 2023.
  - Cost: **10 credits per region per market** per historical call. Event-level calls cost the same per event.
- **Terms:**
  - Storing indefinitely is allowed, as is use "in research papers," derived values and "to train statistical and machine learning models."
  - Prohibited: reselling or redistributing as a raw data feed.
  - Attribution optional.
- **Cost estimate (mine):** about 2 snapshots/day × 150 days × 3 markets × 1 region × 10 credits ≈ 9,000 credits per season. Six seasons (2020-21 to 2025-26) ≈ 54K credits, so **one month of START 100K ($59)** backfills NCAAB open-ish and close-ish lines. This is an estimate, not a quote.

### 1.24 SBRO (Sportsbook Reviews Online) archive

- **URL:** https://www.sportsbookreviewsonline.com/scoresoddsarchives/ncaabasketball/ncaabasketballoddsarchives.htm
- Free XLSX for 2007-08 to 2020-21; 2021-22 is a web page.
- Contents: moneylines, 2nd-half lines, opening and closing spreads and totals, scores.
- **"Will not be updated."** Column layout **unverified** (not shown on the index page).
- Combine with The Odds API from 2020-21 for a 2007-2026 closing-line history. Team names need manual mapping.

### 1.25 Kalshi

- **API:** `https://api.elections.kalshi.com/trade-api/v2/` (public market data). Historical docs: https://docs.kalshi.com/getting_started/historical_data
- **111 men's CBB and March Madness series** listed on 18 Oct 2026. Examples:
  - Game markets: `KXNCAAMBGAME` (game winner), `KXNCAAMBSPREAD`, `KXNCAAMBTOTAL`, 1H/2H spread, total and winner, team totals, race to 10/25/50, first 3PT, overtime, win margin, same-game parlay.
  - Big Ten: `KXNCAAMBBIG10REG` (regular-season champion), `KXNCAAMBBIG10` (tournament).
  - Rankings and awards: AP rank markets, **`KXNCAAMBKENPOMRANK` and `KXNCAAMBKENPOMTOP` (markets on KenPom ratings)**, Naismith, coach of the year, next coach.
  - Tournament: seeds, round, upsets.
- 4 open `KXNCAAMBGAME` markets at check time (preseason).
- **Historical:** settled markets, candlesticks and trades move to `/historical/*` endpoints after rolling cutoffs (`GET /historical/cutoff`). How far back the data goes is not stated.

### 1.26 Polymarket

- **APIs:** Gamma `https://gamma-api.polymarket.com` and CLOB `https://clob.polymarket.com/prices-history` (docs: https://docs.polymarket.com/developers/CLOB/timeseries)
- **Sports registry:**
  - `cbb` "College Basketball": series 10470; resolution source ncaa.com.
  - `ncaab` "March Madness": series 39.
  - `cwbb`: women's.
- Sample `cbb` events are 2025-26 regular-season game moneylines (e.g. Delaware vs Bucknell, 3 Nov 2025). Volumes are small (about $100 to $1,000 in the samples).
- `prices-history` needs no auth. Parameters: market (asset id), startTs/endTs, interval (1m to max), fidelity (minutes). Returns `{t, p}`.
- **Use:** a market-implied win-probability benchmark. Liquidity on mid-major games is thin.

---

## 2. The common core: parameters provided by most sources

Abbreviations: KP = KenPom, T = Torvik, EM = EvanMiya, H = Haslametrics, E = ESPN (BPI and APIs), N = NCAA (stats.ncaa.org/NET), SR = Sports-Reference, CB = CBBD, hR = hoopR (ESPN and NCAA engine), SpR = Sportradar, Syn = Synergy.

| Parameter | Provided by | Notes on definitional differences |
|---|---|---|
| Wins/losses, scores, schedule, venue | KP, T, EM, H, E, N, SR, CB, hR, CBBpy, SpR | Universal. Use ESPN game id as the join key; hoopR crosswalks map it to KP and T names |
| Adjusted offensive efficiency (pts/100 poss vs avg D) | KP (ORtg/AdjO), T (AdjOE), EM (O-Rate), H (Off. Eff), E (BPI OFF, a margin not an efficiency), SR (adj. ORtg), CB (`/ratings/adjusted`), N (inside NET, unpublished) | Different adjustments for recency, garbage time (H removes it) and preseason priors. Scales differ (BPI is per 70 poss) |
| Adjusted defensive efficiency | Same as above | Same caveats |
| Net rating / overall power (margin vs average) | KP (NetRtg), T (Barthag = win prob vs avg), EM (net), E (BPI), SR (NRtg, SRS), CB (net, SRS, Elo), Massey, H (rank) | Barthag is a probability; the others are point margins |
| Tempo / pace (poss per 40) | KP (AdjT), T (Adj T.), SR (pace), CB (pace), H (Pace), E (derivable) | KP and T are opponent-adjusted; SR and CB are raw |
| Four factors, offense and defense (eFG%, TO%, OR%/DR%, FTRate) | KP, T, SR (advanced school), CB (`fourFactors`), hR (box), Torvik game logs | FTRate is FTA/FGA everywhere checked |
| Shooting splits (2P%, 3P%, FT%, 3P rate) | KP, T, H, SR, CB, E (box), hR | |
| Strength of schedule | KP, T (several variants), E (SOS past/remaining), SR, H, CB (via ratings), N (quadrant records) | KP and T use opponent adjusted efficiency; SR uses SRS |
| Player usage (%Poss/USG%) | KP, T, SR, CB (`usage`) | KP and T: possession-ended share; SR: Hollinger-style USG% |
| Player offensive rating (ORtg, Dean Oliver) | KP, T, SR (per-100 table), CB | Same base formula; implementations differ slightly |
| Player rate stats (eFG, TS, OR%, DR%, Ast%/ARate, TO%, Blk%, Stl%, FTRate, fouls/40) | KP, T, SR, CB (subset) | |
| Box plus-minus (BPM/OBPM/DBPM) | T, SR | Different BPM fits |
| Win probability per game (pre-game) | KP (FanMatch), T (super_sked), E (predictor), EM (paid), CB (via Elo), Kalshi/Polymarket (market) | |
| In-game win probability per play | E, CB (`homeWinProbability`), KP (charts only) | CB likely mirrors ESPN (**unverified**) |
| Play-by-play events | E, CB, hR, CBBpy, N, SpR | NCAA-engine PBP is parsed from stats.ncaa.org; ESPN is a separate feed |
| Shot coordinates | E (x,y), CB (`shotInfo.location`), hR (ESPN 2006+, NCAA 2019+), CBBpy, Syn | Normalise each coordinate system |
| Lineups / on-floor players | CB (`onFloor`, lineups 2023-24+), hR NCAA engine (2010+), EM (paid), KP (lineup usage), Syn | |
| Betting lines (spread, total, ML; open/close) | CB (`/lines` with open), E (odds with open/close), Odds API, SBRO, EM (paid), SpR (odds products, **unverified**) | |
| Officials per game | E, hR, CBBpy, KP (ratings) | |
| Recruiting rating / stars | 247, On3/Rivals, CB, T (RecruiT-Rank), SR (RSCI) | CB uses a composite; T converts to a numeric rank |
| Transfer portal events | On3, CB, SpR, T, EM | |
| NET rank and quadrant record | N, T (team sheets, resume), cbbdata, SpR, E (BPI page shows SOR, not NET) | |
| Height / class / experience | KP (minutes-weighted), T (height), SR (roster), CB (recruit height), E (roster) | |

---

## 3. Valuable parameters unique to one source

| Parameter | Source | Why it matters for MSU research |
|---|---|---|
| **Continuity** (share of minutes returning), **Effective Height**, **Bench Minutes**, minutes-weighted **Experience** | KenPom | Roster-construction features, especially after the transfer portal |
| **Luck** (actual minus expected win%) | KenPom | Regression-to-mean signal for close games |
| **FanMatch archive** (daily predicted scores plus daily MAE and bias) and **ThrillScore / Excitement / Tension / Dominance / ComeBack** | KenPom (API `fanmatch`) | Benchmark predictions and game-flow descriptors |
| **Point Distribution** (share of points from FT, 2P, 3P), **Home Court Ratings**, **Jump Ball Ratings**, **possession length** | KenPom | MSU style identity; arena effects (Breslin) |
| **Ref Ratings** | KenPom | The only aggregated official rating found |
| **Barthag**, **WAB** (wins above bubble), **Qual O/D** (efficiency vs tournament-quality teams), **FUN**, **elite SOS** | Torvik | Resume and selection modelling |
| **PORPAGATU!**, **D-PORPAG**, **Role**, NBA **Pick** probability | Torvik | Player value per game; draft projection |
| **Player Dunks / Rim / Mid attempts and makes per game** | Torvik (also in hoopR NCAA engine) | Free shot-zone profile per player |
| **Implied T-Rank from +/- GameScripts**, **T-Rank Time Machine** (point-in-time ratings) | Torvik | Avoids look-ahead leakage in backtests |
| **BPR / OBPR / DBPR** (Bayesian, PBP plus box), **indispensability**, opponent-adjusted **2-5 man lineup ratings**, **NIL value** | EvanMiya | The best public player-impact metric; lineup-level analysis |
| **Garbage-time-filtered efficiency**, **Momentum (Mom, MomO, MomD)**, **Consistency (Con)**, shot **Proximity (Prox)**, **all-play % (AP%)** | Haslametrics | Variance and trend features others lack |
| **SOR** (strength of record), **matchup quality**, **projected seed** and **round-advance chances**, **game score** | ESPN BPI | Committee-style resume and tournament odds |
| **Team Value Index** (inside NET) and **official quadrant records** | NCAA | Selection-relevant ground truth |
| **Within-team and league-wide RAPM**, **possession table with garbage-time and transition flags**, **10-man matchup stints** | hoopR NCAA engine | Free, possession-level, back to 2010 |
| **Substitution events** (subIn/subOut), per-game **Elo start/end**, **excitement**, broadcast/media | CBBD | Clean lineup reconstruction 2023-24+ |
| **Play types** (PnR ball handler, spot-up, post-up, isolation, transition, off-screen...) | Synergy | The only true play-type source; team-licensed |
| **Shot quality / expected points per shot** | ShotQuality | Closed to new consumer subscribers |
| **Wingspan, standing reach, hand length/width, body fat, lane agility, sprint, verticals** | NBA Combine | Physical attributes absent from college data |
| **Recruit NIL valuation** | On3 | Market value of roster |
| **Prediction-market prices on games and on KenPom rankings** (`KXNCAAMBKENPOMRANK`) | Kalshi | Market-implied probabilities; tick-level |
| **Multi-system game prediction archive (2003-04+)** | The Prediction Tracker | Benchmark many systems at once |
| **Composite ranks across many systems** | Massey | Consensus rank (licence restricts AI use) |

---

## 4. Recommended ingestion order (small budget)

The ordering logic: (a) legal clarity for research and ML use, (b) breadth per unit of effort, (c) a join key early on, (d) paid sources only where they add something unique.

### Free tier (do these first)

1. **ESPN data via hoopR prebuilt releases** (`load_mbb_schedule`, `load_mbb_pbp`, `load_mbb_shots`, `load_mbb_team_box`, `load_mbb_player_box`, `load_mbb_officials`, `load_mbb_rosters`), 2006 to 2026.
   - Use the **ESPN game id as the master key** and hoopR's **crosswalks** (ESPN↔KenPom↔Torvik↔Fox).
   - Use the prebuilt files rather than hitting ESPN yourself; that limits ToU exposure.
2. **Torvik static files**, 2008 to 2026: `{YEAR}_team_results.csv`, `{YEAR}_fffinal.csv`, `getadvstats.php?year=&csv=1`, `{YEAR}_super_sked.csv`. Optionally go through **cbbdata** (free key) for the daily ratings archive (point-in-time features) and player game logs. Throttle to a few requests per minute.
3. **CBBD free API key** (Python `cbbd`):
   - `/games`, `/games/teams`, `/games/players`, `/plays/team` (MSU), `/substitutions/team`, `/lineups/team` (2023-24+), `/lines` (spread/total/ML with opens), `/ratings/adjusted|srs|elo`, `/recruiting/players|portal`, `/draft/picks`.
   - These have the clearest licence for model training. Cache everything.
4. **hoopR NCAA-engine releases** (`load_ncaa_mbb_possessions`, `_lineups`, `_matchup_stints`, `_rapm`, `_player_box`, `_shots` 2019+). These give possession-level and lineup data back to 2010 for free. Validate them against CBBD lineups for 2023-26.
5. **NCAA NET:** current table from ncaa.com, history via `cbd_net_archive()`. Add quadrants with `cbd_add_net_quad()`.
6. **ESPN BPI and predictor snapshots:** pull `powerindex` and the `predictor`/`odds` for MSU games during the season. These are point-in-time, so start collecting now (season 2027 begins in November). Low volume, personal research use.
7. **Betting history:** SBRO XLSX (2007-08 to 2021-22) plus ESPN core `odds` (open/close per provider) and CBBD `/lines`.
8. **Prediction markets:** Kalshi `KXNCAAMBGAME`/`SPREAD`/`TOTAL` plus `KXNCAAMBBIG10REG`; Polymarket `cbb` series with `prices-history`. Start logging this season.
9. **Haslametrics** (season tables; free and "use as desired") and **The Prediction Tracker** CSVs, for features and benchmarks.
10. **Recruiting and transfer:** take these from CBBD first. Use 247 and On3 pages manually only (their ToU bars scraping).
11. **NBA Combine** (via `nba_api`), only for MSU alumni who attended. Non-commercial.
12. **Sports-Reference:** manual cross-checks only. Its terms forbid ML use without permission. Email them if you want to use it in modelling.

### Paid tier (in priority order, about $210 for year one)

1. **KenPom API, $145/yr.** The API ToS explicitly allows academic and model-building use. It gives ratings archive, four factors, height/continuity/bench, point distribution and the FanMatch archive since 1999. If only manual browsing is needed, the **$24.95 web subscription** suffices, but automated scraping of it breaches the web ToU.
2. **EvanMiya Basic, $30/yr.** Lineup ratings, game predictions with Vegas odds, full portal rankings, **CSV export**. BPR is free; Basic unlocks export.
3. **The Odds API START 100K, $59 for one month.** Backfill NCAAB historical spreads, totals and ML since 2020-11-16 (estimate in Section 1.23), then downgrade to free or cancel. Use START 20K ($30/mo) during the season for live capture if needed.
4. **CBBD Patreon Tier 2+, $5/mo,** only if the free quota runs out (quotas **unverified**) or you need the leaderboard endpoint.

**Do not buy for now:**

- **Synergy:** no individual licence. Ask MSU staff whether the team licence permits research use.
- **Sportradar:** B2B. A free trial is fine for schema exploration.
- **ShotQuality:** closed to new consumers.
- **Stathead:** SR's ML restriction still applies.
- **EvanMiya Premium:** only if lineup optimisation tools matter.

---

## 5. Academic and quasi-academic work on rating-system accuracy (college basketball)

Peer-reviewed. Metadata was verified via Crossref or Semantic Scholar; the content source for each is noted.

1. **Barrow, D., Drayer, I., Elliott, P., Gaut, G., & Osting, B. (2013).** Ranking rankings: an empirical comparison of the predictive power of sports ranking methods. *Journal of Quantitative Analysis in Sports*, 9(2), 187-202. https://doi.org/10.1515/jqas-2013-0013
   - Eight ranking methods, each in win/loss and score-differential versions.
   - Data: 22 NCAA D-I basketball seasons plus NBA, MLB and NCAAF. 20-fold cross-validation, then Friedman and Nemenyi tests.
   - Methods differ significantly. For NCAAB and NCAAF, **score-differential versions are usually more predictive**.
   - (Abstract via RePEc. The best NCAAB method is not named in the abstract.)
2. **Kvam, P., & Sokol, J. S. (2006).** A logistic regression/Markov chain model for NCAA basketball. *Naval Research Logistics*, 53(8), 788-803. https://doi.org/10.1002/nav.20170
   - Introduces LRMC.
   - Reported as "significantly more successful than... tournament seedings, the AP and ESPN/USA Today polls, the RPI, and the Sagarin and Massey ratings" over 6 seasons (Semantic Scholar TLDR; full text not opened).
   - LRMC is still published for 2026: https://www2.isye.gatech.edu/~jsokol/lrmc/
3. **Brown, M., & Sokol, J. (2010).** An improved LRMC method for NCAA basketball prediction. *JQAS*, 6(3). https://doi.org/10.2202/1559-0410.1202
   - Metadata verified. Content **unverified**.
4. **Lopez, M. J., & Matthews, G. J. (2015).** Building an NCAA men's basketball predictive model and quantifying its success. *JQAS*, 11(1). https://doi.org/10.1515/jqas-2014-0058 (arXiv:1412.0248)
   - Logistic regression **combining Las Vegas point spreads with possession-based efficiency metrics** won the 2014 Kaggle contest on log loss, against about 400 entries.
   - Simulations show at most about a 12% chance of winning even under optimistic assumptions. Luck dominates tournament contests.
5. **Yuan, L.-H., Liu, A., Yeh, A., Kaufman, A., Reece, A., Bull, P., Franks, A., Wang, S., Illushin, D., & Bornn, L. (2015).** A mixture-of-modelers approach to forecasting NCAA tournament outcomes. *JQAS*, 11(1). https://doi.org/10.1515/jqas-2014-0056
   - Highlights difficulties of public data (TLDR via Semantic Scholar).
6. **Glickman, M. E., & Sonas, J. (2015).** Introduction to the NCAA men's basketball prediction methods issue. *JQAS*, 11(1), 1-3. https://doi.org/10.1515/jqas-2015-0013
   - Special-issue overview of the Kaggle "March Machine Learning Mania" methods. Metadata verified only.
7. **Zimmermann, A., Moorthy, S., & Shi, Z. (2013).** Predicting college basketball match outcomes using machine learning techniques: some results and lessons learned. arXiv:1310.3607.
   - "Attributes seem to be more important than models." Also reports an apparent upper limit to predictive quality.
8. **Carlin, B. P.** "Improved NCAA basketball tournament modeling via point spread and team strength information," reprinted in *Anthology of Statistics in Sports* (SIAM, 2005), ch. 18. https://doi.org/10.1137/1.9780898718386.ch18
   - Metadata verified only.
9. Market-efficiency context (metadata verified only):
   - Colquitt, Godwin & Caudill (2001), *J. Business Finance & Accounting*, https://doi.org/10.1111/1468-5957.00372
   - Hickman (2020), "Efficiency in the madness?", *J. Economics and Finance*, https://doi.org/10.1007/s12197-020-09507-7

Non-peer-reviewed but directly relevant:

- **Miyakawa, E. (6 Oct 2026).** "Which CBB supercomputer should you trust?" https://blog.evanmiya.com/p/which-cbb-supercomputer-should-you
  - Data: about 17,000 games, 2023-24 to 2025-26.
  - On game spreads, **EvanMiya ≈ KenPom** (EvanMiya slightly better RMSE, KenPom slightly better MAE), with **Torvik slightly behind**. Models explain about 41% of spread variance in 2025-26.
  - A blend of 45% EvanMiya, 35% KenPom and 20% Torvik beat every single model.
  - Haslametrics was excluded because it has no prediction logs. **The author runs one of the compared systems, so there is a conflict of interest.**
- **Ezekowitz, J. (2013).** "The RPI is Not the Real Predictive Indicator," Harvard Sports Analysis Collective. https://harvardsportsanalysis.wordpress.com/2013/02/19/rpi-prediction/
  - Over the 2007-2012 tournaments, the RPI was worse than Pomeroy's ratings and a survival model at picking Final Four teams and champions.
- **The Prediction Tracker** (Section 1.16) remains the best public multi-system accuracy archive. Its result tables could not be read here (**unverified**).

**Gap:** I found no peer-reviewed paper that compares the current public systems (KenPom, Torvik, EvanMiya, BPI, NET, Haslametrics) on a common out-of-sample game set. That comparison is a feasible, publishable side analysis for this project using the free archives above (Torvik super_sked, KenPom FanMatch via API, ESPN predictor, Prediction Tracker CSVs, market lines).

---

## 6. Things I could not verify

- stats.ncaa.org contents and terms (403 from this environment).
- Hoop-Math status (unreachable).
- Massey column list and composite page (Cloudflare).
- Prediction Tracker result tables (Cloudflare).
- On3 terms (403).
- Verbal Commits.
- CBBD numeric call quotas per tier.
- Synergy and Sportradar pricing.
- ShotQuality prices and seasons.
- Exact definition of Torvik "GameScripts."
- KenPom Ref Ratings fields.
- Sports-Reference men's earliest season.
- cbbdata and hoopR GitHub activity (GitHub API blocked here; CRAN and PyPI dates were verified instead).
- Whether CBBD plays and lines derive from ESPN.

---

## Sources

- https://kenpom.com/
- https://kenpom.com/register-kenpom.php
- https://kenpom.com/register-api.php
- https://kenpom.com/terms.php
- https://kenpom.com/terms-api.php
- https://kenpom.com/tour.php
- https://kenpom.com/blog/ratings-glossary/
- https://kenpom.com/blog/help-with-team-page/
- https://kenpom.com/blog/individual-stats-primer/
- https://kenpom.com/height.php
- https://kenpom.com/playerstats.php
- https://kenpom.com/fanmatch.php
- https://kenpompy.readthedocs.io/en/latest/
- https://github.com/j-andrews7/kenpompy
- https://pypi.org/pypi/kenpompy/json
- https://barttorvik.com/trank.php?year=2026
- https://barttorvik.com/2026_team_results.csv
- https://barttorvik.com/2026_team_results.json
- https://barttorvik.com/2008_team_results.csv
- https://barttorvik.com/2026_fffinal.csv
- https://barttorvik.com/getadvstats.php?year=2026&csv=1
- https://barttorvik.com/2026_super_sked.csv
- https://barttorvik.com/teampbp.php?year=2026&sort=1
- https://barttorvik.com/playerstat.php?year=2026
- https://barttorvik.com/gamestat.php?year=2026
- https://barttorvik.com/teamstats.php?year=2026&sort=2
- https://barttorvik.com/team.php?team=Michigan+St.&year=2026
- https://barttorvik.com/box.php?muid=DukeMichigan+St.12-6&year=2026
- https://barttorvik.com/implied-trank.php
- https://cbbdata.aweatherman.com/
- https://cbbdata.aweatherman.com/reference/index.html
- https://evanmiya.com/
- https://evanmiya.com/subscribe
- https://evanmiya.com/how-it-works
- https://docs.google.com/document/d/1jbGeWCSgl0-ApK_929RT2D3ldPGHYUVSbipV8EvZ9_c/edit?usp=sharing
- https://blog.evanmiya.com/p/which-cbb-supercomputer-should-you
- https://haslametrics.com/
- https://haslametrics.com/about.php
- https://www.espn.com/mens-college-basketball/bpi
- https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/127/schedule?season=2026
- https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event=401826785
- https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/401826785/competitions/401826785/odds
- https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/401826785/competitions/401826785/predictor
- https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/401826785/competitions/401826785/probabilities
- https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/401826785/competitions/401826785/officials
- https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/2026/powerindex/127
- https://github.com/pseudo-r/Public-ESPN-API
- https://disneytermsofuse.com/english/
- https://stats.ncaa.org/
- https://www.ncaa.com/rankings/basketball-men/d1/ncaa-mens-basketball-net-rankings
- https://www.ncaa.com/news/basketball-men/article/2022-12-05/college-basketballs-net-rankings-explained
- https://github.com/henrygd/ncaa-api
- https://www.sports-reference.com/cbb/
- https://www.sports-reference.com/data_use.html
- https://www.sports-reference.com/bot-traffic.html
- https://www.sports-reference.com/cbb/seasons/men/2026-ratings.html
- https://www.sports-reference.com/cbb/seasons/men/2026-advanced-school-stats.html
- https://www.sports-reference.com/cbb/schools/michigan-state/men/2026.html
- https://collegebasketballdata.com/
- https://collegebasketballdata.com/api-tiers
- https://collegebasketballdata.com/terms
- https://collegebasketballdata.com/college-basketball-api
- https://collegebasketballdata.com/about
- https://api.collegebasketballdata.com/
- https://api.collegebasketballdata.com/api-docs.json
- https://pypi.org/pypi/cbbd/json
- https://cran.r-project.org/web/packages/hoopR/index.html
- https://hoopr.sportsdataverse.org/reference/index.html
- https://hoopr.sportsdataverse.org/reference/load_mbb_pbp.html
- https://hoopr.sportsdataverse.org/reference/load_ncaa_mbb_lineups.html
- https://pypi.org/pypi/sportsdataverse/json
- https://pypi.org/project/CBBpy/
- https://github.com/lbenz730/ncaahoopR
- https://synergysports.com/
- https://sportradar.com/content-hub/blog/7-things-you-can-do-with-synergy-basketball-apis/?lang=en-us
- https://sportradar.com/content-hub/blog/tap-into-the-data-that-runs-college-basketballs-biggest-tournament/?lang=en-us
- https://shotquality.com/
- https://www.shotqualitybets.com/
- https://www.shotqualitybets.com/pricing
- https://www.hoop-math.com/ (unreachable)
- https://masseyratings.com/cb/ncaa-d1/ratings
- https://masseyratings.com/info.php
- https://www.thepredictiontracker.com/basketball.php
- https://developer.sportradar.com/basketball/reference/ncaamb-overview
- https://developer.sportradar.com/getting-started/docs/get-started
- https://shottracker.com/shottracker-expands-innovation-partnerships-across-big-12-and-ncaa-basketball/
- https://www.cbsnews.com/amp/texas/news/officials-cheer-new-hd-replay-system-for-ncaa-tournament
- https://247sports.com/season/2026-basketball/compositerecruitrankings/
- https://247sports.com/Article/247Sports-Terms-of-Use-104943/
- https://legalterms.cbsinteractive.com/terms-of-use
- https://www.on3.com/rivals/rankings/industry-player/basketball/2026/
- https://www.on3.com/transfer-portal/wire/basketball/
- https://verbalcommits.com/transfers/2026
- https://www.nba.com/stats/draft/combine-anthro
- https://www.nba.com/termsofuse
- https://raw.githubusercontent.com/swar/nba_api/master/docs/nba_api/stats/endpoints/draftcombineplayeranthro.md
- https://raw.githubusercontent.com/swar/nba_api/master/docs/nba_api/stats/endpoints/draftcombinedrillresults.md
- https://blessyourchart.substack.com/p/acc-refs
- https://the-odds-api.com/
- https://the-odds-api.com/historical-odds-data/
- https://the-odds-api.com/sports-odds-data/sports-apis.html
- https://the-odds-api.com/terms-and-conditions.html
- https://www.sportsbookreviewsonline.com/scoresoddsarchives/ncaabasketball/ncaabasketballoddsarchives.htm
- https://api.elections.kalshi.com/trade-api/v2/series?category=Sports
- https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNCAAMBGAME&status=open
- https://docs.kalshi.com/getting_started/historical_data
- https://gamma-api.polymarket.com/sports
- https://gamma-api.polymarket.com/tags/slug/ncaab
- https://gamma-api.polymarket.com/events?series_id=10470&limit=2
- https://docs.polymarket.com/developers/CLOB/timeseries
- https://ideas.repec.org/a/bpj/jqsprt/v9y2013i2p187-202n7.html
- https://doi.org/10.1515/jqas-2013-0013
- https://doi.org/10.1002/nav.20170
- https://doi.org/10.2202/1559-0410.1202
- https://arxiv.org/abs/1412.0248
- https://doi.org/10.1515/jqas-2014-0058
- https://doi.org/10.1515/jqas-2014-0056
- https://doi.org/10.1515/jqas-2015-0013
- https://arxiv.org/abs/1310.3607
- https://doi.org/10.1137/1.9780898718386.ch18
- https://doi.org/10.1111/1468-5957.00372
- https://doi.org/10.1007/s12197-020-09507-7
- https://www.mdpi.com/2078-2489/13/5/232
- https://www2.isye.gatech.edu/~jsokol/lrmc/
- https://harvardsportsanalysis.wordpress.com/2013/02/19/rpi-prediction/
- https://api.crossref.org/works/ (metadata lookups for the DOIs above)
- https://api.semanticscholar.org/graph/v1/paper/ (abstract/TLDR lookups)
