# Odds and Prediction-Market Data for NCAAB Benchmarking (MSU / Big Ten, 2021-22 to 2025-26)

Compiled 2026-10-17. Each claim comes from a page or API response opened during this research unless it is marked **(unverified)**. Live API probes (ESPN core API, Kalshi, Polymarket, CollegeBasketballData OpenAPI spec) were run on 2026-10-17 and are labeled **[probed]**.

---

## 0. Summary

- **Free closing lines for all five seasons exist.** There are two independent free routes. (1) The ESPN core odds API has a spread and total for every completed MSU game in 2021-22 through 2025-26, plus explicit `open`/`close` objects from 2022-23 onward [probed]. (2) The CollegeBasketballData.com `/lines` endpoint (free key) returns `spread`, `spreadOpen`, `overUnder`, `overUnderOpen` and both moneylines for each provider, and it can filter by conference [probed: spec].
- **The best paid source for timestamped lines is The Odds API historical endpoint.** NCAAB featured markets (ML, spread, total) go back to 2020-11-16, in 5–10 minute snapshots. First-half lines and player props exist only from **2023-05-03**, so they cover 2023-24 onward. Plans cost $30–$119 a month, and one month is enough for a one-off backfill.
- **No free first-half archive exists for 2021-22 or 2022-23.** SBRO gives second-half lines for 2021-22 only. Kalshi and Polymarket list 1H markets from 2025-26 onward.
- **College-basketball player props have essentially no public archive** before The Odds API's May 2023 additional markets. We have to collect them ourselves going forward.
- **Prediction markets have NCAAB game markets only from 2025-26.** Kalshi `KXNCAAMBGAME` has 5,280 settled events, the oldest from 2025-11-03. Polymarket's `cbb` series starts late Oct 2025 with moneyline, spreads and totals. Both serve price history free through public read APIs [probed]. Kalshi and Polymarket also list 1H/2H, team-total and race-to markets.
- **Michigan access:** trading sports contracts from Michigan is currently blocked or paused on Kalshi (court injunction), Robinhood (agreement with the state), Polymarket US and Novig (geo-excluded). Reading the public market data does not require an account.

---

## 1. Historical sportsbook odds sources

Legend: ML = moneyline, SPR = spread, TOT = total, 1H/2H = half lines, TT = team totals, PP = player props, LIVE = in-game.

| # | Source | Markets | Seasons | Granularity | Format | Cost | Terms / research use |
|---|---|---|---|---|---|---|---|
| 1 | **Sportsbook Reviews Online (SBRO)** NCAAB archive | ML, SPR, TOT (open and close), **2H line**, half scores | 2007-08 to 2021-22. The archive "will not be updated." | Open + close only, single consensus-style line | .xlsx for 2007-08 to 2020-21; **2021-22 is an HTML table only**, and some rows are misaligned | Free | Site "Terms" page not reviewed **(unverified)** |
| 2 | **The Odds API** (historical) | Featured: ML (h2h), SPR, TOT. Additional: `h2h_h1`, `spreads_h1`, `totals_h1`, `team_totals`(+h1/h2), alternates, NCAAB player props (`player_points`, `player_rebounds`, `player_assists`, `player_threes`, PRA, etc.) | `basketball_ncaab` from **2020-11-16**. Featured markets from 2020-06-06; additional markets (props, halves) only from **2023-05-03** | Snapshots every 10 min until Sep 2022, then every 5 min. Multiple books, regions us/us2/uk/eu/au | JSON REST | Historical needs a paid plan: 20K credits $30/mo, 100K $59, 5M $119, 15M $249. Cost is 10 credits per region per market (featured) and 10 per region per market **per event** (additional) | Terms explicitly allow research papers, ML model training and indefinite storage; no resale or redistribution as a raw feed |
| 3 | **SportsDataIO** | Pre-game, in-game and period odds (incl. 1H), line-movement endpoints, "with resulting" variants | Not stated **(unverified)** | Line movement (timestamped) | JSON/XML API | Paid, price not published; free trial covers only the UEFA Champions League; historical via "SportsDataIO Replay" or sales | Commercial license **(unverified)** |
| 4 | **OddsJam / OpticOdds** | Claims 100+ books incl. college basketball; OpticOdds historical archive with millisecond timestamps | "Several years" for major leagues; per-league depth on request | Tick-level price changes | REST + bulk export | Enterprise; directory estimates $1,000+/mo for OddsJam **(unverified)** | Contract |
| 5 | **SportsGameOdds** | NCAAB listed on all plans; `includeOpenCloseOdds` returns open/close per book | Depth not stated | Open/close + snapshots | JSON API | Free 2,500 objects/mo (no historical stated); Rookie $99/mo; **Pro $299/mo includes historical** | ToS not reviewed **(unverified)** |
| 6 | **Unabated** | Live odds + "Unabated Line"; college basketball only on Concierge Advanced | Historical not mentioned | Streaming | REST/SSE | Concierge $799/mo (no CBB); **Concierge Advanced $2,999/mo** (incl. CBB); per third-party directory | Contract |
| 7 | **Action Network / Action Labs** (successor bundle to Sports Insights / Bet Labs) | Odds comparison across 60+ books, "Systems" backtesting on historical game data, prop tool | Date range not stated | Web tool | Web UI, no bulk export found | Subscription, price not stated **(unverified)** | Personal use **(unverified)** |
| 8 | **Covers.com** | Futures archive (national championship odds) confirmed; game-level CBB line history not confirmed | Not stated | Web pages | HTML | Free | Scraping terms **(unverified)** |
| 9 | **KillerSports / SDQL** | SDQL query language over historical lines/results; NCAAB DB fields such as line, total, 1H line **(unverified, site is JS-only)** | **(unverified)** | Closing line per game **(unverified)** | Web query output | Free web queries **(unverified)** | **(unverified)** |
| 10 | **Kaggle** | `zachht/wnba-odds-history`: "Global, NBA, college, and WNBA basketball odds," scraped every 7 min since **2025-08-24**, CC0. `oliviersportsdata/datasets-road-to-march-madness`: tiny NCAAB closing-ML sample, CC BY-NC. `scottfree/sports-lines`: 2017-era pro and college lines, CC0 | See left | 7-min scrape (zachht) | CSV | Free | CC0 / CC BY-NC as listed |
| 11 | **BigDataBall** | CBB team and player datasets; marketing copy mentions opening and closing betting odds | **2022-23 to 2025-26** historical | Open/close **(column list unverified)** | Excel | **$30 per season dataset**, bundle discounts 5–15%, 20% member discount | Personal-use license **(unverified)** |
| 12 | **OddsPortal** | NCAAB results with closing odds from many books **(unverified: robots disallowed fetch)** | **(unverified)** | Open/close per book **(unverified)** | HTML only | Free | Scraping disallowed by robots.txt |
| 13 | **ESPN core API / hoopR `espn_mbb_betting()`** | SPR, TOT, ML per provider; `open`/`close`/`current` objects; separate "Live Odds" providers in recent seasons | **[probed] MSU completed games with a spread: 34/34 (21-22), 31/31 (22-23), 33/33 (23-24), 33/33 (24-25), 32/32 (25-26). `open`/`close` present from 2022-23** (30/31, 32/33, 33/33, 32/32); 2021-22 has only current/close values from ~13 providers (Caesars, DraftKings, MGM, consensus...) | Open + close (+ live provider snapshot) | JSON (undocumented) | Free | Undocumented public API; personal/research use at own risk |
| 14 | **CollegeBasketballData.com (CBBD) `/lines`** | `spread`, `spreadOpen`, `overUnder`, `overUnderOpen`, `homeMoneyline`, `awayMoneyline` per provider; filters `season`, `team`, `conference`, date range; up to 3,000 games per call | Season depth **(unverified; requires key)** | Open + close | JSON REST | Free key; optional Patreon tiers $1–$10/mo (call quotas not published) | API usage terms on Patreon **(unverified)** |
| 15 | **cbbdata (Torvik) / toRvik** | No betting lines. Has T-Rank game predictions, day-by-day T-Rank and KenPom rating archives, schedules | Predictor back to 2014-15 | Daily ratings | R API | Free key (KenPom archive needs a KenPom subscription) | MIT (package) |
| 16 | **Massey Ratings data** | Scores only (no lines); fixed-width and Matlab CSV exports | **(unverified)** | Per game | TXT/CSV | Free | As-is; cite MasseyRatings.com |
| 17 | **The Prediction Tracker** | Per-game computer predictions plus **opening line and updated line** (seen on the 2026-04-06 MICH-UConn row) | Season CSVs **2003-04 to 2025-26** | Open + "updated" (≈ near-close) | CSV | Free | **(unverified)**; Cloudflare-protected |
| 18 | **TeamRankings spread-movement pages** | Spread history from 2–3 books with ET timestamps, open/high/low/last, total | Pages exist for 2023-24 to 2025-26 games | Timestamped intraday | HTML | Free view (BetIQ paid for tools) | Scraping terms **(unverified)** |
| 19 | **OddsPapi** | Claims free historical odds and player props | Depth not stated | **(unverified)** | API | Free tier claimed, limits unpublished | **(unverified)** |
| 20 | **Betfair Historical Data** | Exchange prices (Basic = last traded price at 1-min; Advanced/Pro finer) | NCAAB coverage **(unverified)**; US liquidity on NCAAB is thin **(unverified)** | 1-min (Basic) to tick (Pro) **(unverified)** | JSON stream files | Basic free; Advanced/Pro paid per package (prices unverified) | Betfair account required |

**Not useful for this need:** Princeton DSS "Historical Sports Odds Database" (oddswarehouse.com). It has NBA, NFL, MLB, NHL and soccer but **no NCAAB**, and it is campus-login only.

---

## 2. Prediction markets and exchanges

### Kalshi (CFTC-regulated DCM)
- **NCAAB contracts [probed: `/series?category=Sports`]:**
  - Game winner `KXNCAAMBGAME`; `KXNCAAMBSPREAD`; `KXNCAAMBTOTAL`.
  - 1H winner/spread/total (`KXNCAAMB1H`, `KXNCAAMB1HSPREAD`, `KXNCAAMB1HTOTAL`); 2H equivalents; 1H/2H team totals; `KXNCAAMBTEAMTOTAL`; winning margin; overtime.
  - Race-to-10/25/50 points; first team to make a three; same-game parlays.
  - Season and futures: Big Ten regular-season champion and top finishers, Big Ten tournament, all conference tournaments, AP poll, KenPom rank markets, win totals, Naismith/COTY.
  - March Madness: champion `KXMARMAD`, round reach, seeds, region, upsets, Most Outstanding Player.
- **Depth [probed]:** `KXNCAAMBGAME` has **5,280 settled events, the oldest 2025-11-03**. 60 event tickers contain "MSU", which also matches other schools' codes. Spread, total, 1H spread and 1H total each have more than 200 settled events in 2025-26. Kalshi also ran March 2025 tournament game markets through Robinhood (Covers, Mar 2025), but they are not under this series ticker **(unverified which ticker)**.
- **Data access:** free public REST API.
  - Live and recent data: `/markets/{ticker}/candlesticks` (1-min, 1-h and 1-day OHLC with bid/ask, volume and open interest) and `/markets/trades`.
  - Settled before the cutoff (currently 2026-08-18): `/historical/markets`, `/historical/markets/{ticker}/candlesticks`, `/historical/trades`.
  - I pulled hourly candles for `KXNCAAMBGAME-26MAR27MSUCONN-MSU` without authentication [probed]. The unauthenticated rate limit is low (HTTP 429 seen); authenticated tiers are token-based.
- **Michigan:**
  - Ingham County Circuit Court issued a TRO on 2026-06-29, followed by a preliminary injunction (reported 2026-09-02). Kalshi must geofence Michigan residents and anyone physically in the state from **sports** contracts, with fines of up to $500K/day.
  - Robinhood, which routes Kalshi contracts, agreed to stop new MI sports positions and close existing ones by 2026-10-09.
  - Federal preemption is still before the Sixth Circuit, and a SCOTUS case is likely given the circuit split.

### Polymarket
- **NCAAB contracts [probed: Gamma API]:**
  - Game series `cbb` (series_id 10470) starts **2025-10-29**. Each game event carries a moneyline, several spread markets (e.g. "Kentucky −5.5/−4.5/−3.5") and several O/U totals. MSU games are present (e.g. `cbb-uk-mst-2025-11-18`: ML volume ≈ $50K, spread −5.5 ≈ $86K).
  - Futures/props under `ncaab` (series 39): conference regular-season champions (Big Ten 2025-26 ≈ $83K volume), Final Four qualifiers, seed-upset props, and a 2024 tournament event.
  - **No game-level markets before 2025-26** [probed: zero `cbb` events in the 2024-25 window].
- **Data access:** free, no authentication.
  - `clob.polymarket.com/prices-history`: 1-minute fidelity when `startTs`/`endTs` are passed. I got 6,002 points for the MSU–UK moneyline [probed]. `interval=all` returned empty for this resolved market.
  - `data-api.polymarket.com/trades` returns trade-level data.
  - The Gamma `/events` offset pagination fails past about 2,100 events; use date windows or `/events/keyset`.
- **Michigan:** Polymarket US relaunched via a CFTC-approved app (Dec 2025). A state availability list updated 2026-10-16 lists **MI as excluded** (with NV, AZ, IL, MT, OH; MD listed inconsistently).

### Other venues
| Venue | NCAAB? | Data downloadable? | Michigan |
|---|---|---|---|
| **Robinhood Prediction Markets** (Kalshi-cleared) | Yes: game pages for MSU/UM 2025-26 | No separate archive; use Kalshi API | Sports contracts paused in MI (Sept 2026 agreement) |
| **Novig** (DCM since June 2026; relaunched 2026-08-04) | Sports-only exchange; CBB coverage implied by promos (e.g. "Michigan State vs. Purdue") **(unverified)** | No public API found | **Excluded** (AZ, MI, NV) |
| **ProphetX** (CFTC-regulated per affiliate review) | Yes: college basketball listed; ML, spreads, totals, props, live | No public data API found **(unverified)** | Review says 49 states, NV excluded. MI status **(unverified)**; treat as at risk given state enforcement |
| **Sporttrade** | Exited US sportsbook operations May 2026; DCM/DCO application filed Feb 2026, pending | No | Was never in MI |
| **DraftKings Predictions / FanDuel Predicts** | Sports contracts mainly in non-sportsbook states; CBB not confirmed | No | Sports contracts unlikely in MI (legal-sportsbook state) **(unverified)** |
| **Betfair Exchange** | Lists US college basketball **(unverified)** | Historical files (Basic free) | Not available to US customers |
| **Prediction Hunt API** (aggregator) | Cross-platform matched events, 6 platforms | Free 1,000 req/mo; paid Dev tier (price not shown) | n/a |

**Legal note (inference, not legal advice):** the Michigan orders target *offering or trading* sports contracts to people in Michigan. Pulling public, unauthenticated market data for research is a different activity. Do not open or trade positions from Michigan, and do not use VPNs to get around geofences.

---

## 3. Public models to learn from

| Model | Method (paraphrased) | Code / data public? | Accuracy vs closing line |
|---|---|---|---|
| **KenPom** | Adjusted offensive and defensive efficiency per 100 possessions, opponent-adjusted additively against the national average on each game date. AdjEM = AdjO − AdjD. Win probability comes directly from the predicted margin with a flat ~3.75-pt home edge (2014 methodology update); mild recency weighting. | Ratings and FanMatch predictions behind a ~$20/yr subscription (third-party figure); `kenpompy` (GPL-3) scrapes FanMatch and ratings back to 1999 with a login | 2010 calibration post only (e.g. 96%+ bucket went 194–5). **No published comparison to the closing line** |
| **Bart Torvik (T-Rank)** | Efficiency-based like KenPom, with game-recency decay (full weight for 40 days, declining ~1%/day to 60% weight at 80 days). Barthag win probability; game predictions with expected points and possessions. | Free site; `cbbdata`/`toRvik` R APIs (MIT) expose game predictions (back to 2014-15), day-by-day rating archives and four factors | None published |
| **Haslametrics** | Play-by-play based: shot frequency, shot proximity and conversion by zone, steal and offensive-rebound effects, per possession. Strips data after a game is "#AnalyticallyFinal" (decided). Momentum = last 4–8 games vs season. Ranking by All-Play %. | Free site, no download | None published |
| **EvanMiya** | Bayesian Performance Rating: Bayesian RAPM with box-score-based priors (weights set by cross-validation) plus preseason priors from history, recruiting and transfers. Feeds team ratings, lineup and injury-adjusted game predictions. | Site partly paid **(unverified)**; method described on blog | None published |
| **ESPN BPI** | Opponent-, pace-, venue- and travel-adjusted margin model with simulations **(method page fetch returned empty; unverified)**. | Ratings via `cbbdata::cbd_bpi_ratings()`; ESPN "predictor" win probability in `espn_mbb_betting()` | None published |
| **FiveThirtyEight → Silver Bulletin** | Tournament model: 50% own Bayesian SBCB ratings, 50% composite of KenPom, Sonny Moore, BPI, Massey and the committee S-curve. Injury and travel-distance adjustments; in-tournament updating; recalibrated on 250K+ historical games. | 538 per-day tournament forecast CSVs (e.g. 2018 on datahub, round-by-round probabilities); current SB tables paywalled | None published (bracket only) |
| **Massey** | Least-squares rating family; composite of 100+ systems | Score data free; composite page **(unverified)** | Tracked on Prediction Tracker |
| **Sagarin** | "Predictor" (margin-based with diminishing returns for blowouts) plus win/loss-only "Elo chess"; Bayesian start-of-season prior. In USA Today 1985–2023. | Methods not disclosed; current publication status **(unverified)** | Tracked historically on Prediction Tracker **(unverified)** |
| **The Prediction Tracker** | Aggregates many systems (Massey, Moore, Dokter, TeamRankings, etc.) plus a "Computer Adjusted Line" | Season CSVs 2003-04 to 2025-26 with opening/updated lines | It is the reference scoreboard for MAE and ATS vs the opening line. **Exact metrics not retrieved (page Cloudflare-blocked)** |
| **ncaahoopR** (Benz) | In-game win probability from play-by-play; optionally uses the ESPN pregame spread as a prior (`include_spread`) | Open source (R) | n/a; good template for live win probability anchored to the market |
| **Open GitHub NCAAB spread/total projects** | GitHub search API was blocked from this session. `alphapy` (NCAAB tutorial) and `agileai/model-aggregator` showed up in web search. | Public | None with audited CLV found **(unverified)** |

**Takeaway:** none of the major public raters publishes accuracy against closing lines. We have to run that benchmark ourselves using items 13, 14 and 17 from section 1.

---

## 4. Evidence on market efficiency, evaluation and sizing

**NCAAB spreads are close to efficient overall.**
- Wolfers (2006, *AER*; 44,120 D-I games 1989–2005): the spread is an unbiased forecast, favorites covered 50.01%, and errors are roughly normal with SD ≈ **10.9 pts**. The one anomaly: favorites by more than 12 covered only 48.4%, which he read as possible point shaving.
- Bernhardt & Heston (2006 working paper) and Borghesi, Paul & Weinbach (2010, *J. Prediction Markets*) argue the asymmetry is structural. Late-game clock management, bench depth, and bookmakers shading lines toward public preferences (favorites, overs) break the symmetry assumption.
- **Implication:** model the margin distribution conditional on spread size, rather than assuming Normal(spread, 11).

**Tournament market.** Hickman (2020, *J. Econ. & Finance*; 1996–2019 NCAA tournament) finds the market is efficient with little seed-based bias. ACC teams underperform the spread, especially in the opening round.

**Moneylines show a favorite-longshot bias.** Berkowitz, Depken & Gandar (2017, *QREF*) find a persistent favorite-longshot bias in college basketball and football moneylines. Heavy favorites roughly break even, so after vig the market is efficient. **Implication:** de-vig with a method that accounts for longshot bias (power or Shin), not plain normalization.

**Totals.** Paul & Weinbach found over-bias in college football and arena football totals (2005). Francisco & Moore (2018) find it had corrected by 2003–2015. NCAAB evidence is mainly the "just-under" asymmetry in Borghesi et al. (2010), consistent with books shading totals upward.

**Bookmaker behavior.** Levitt (2004, *Economic Journal*): bookmakers forecast better than bettors and deliberately shade prices to exploit bettor biases, rather than balancing their books.

**Line movement and the close.** Simon (2024, *Management Science*; MLB, 3,681 games, 4 books): lines tend to overreact, and changes are negatively autocorrelated. Forecasts do not consistently improve toward start time, so weak-form efficiency is rejected. This is a caveat to treating the close as truth. No NCAAB equivalent was found.

**First-half markets and player props.** **No peer-reviewed NCAAB studies were found.** Industry sources treat them as lower-limit, softer markets **(unverified)**. Ramesh et al. (2019, arXiv) report positive returns across NFL, NBA, NCAAF, NCAAB and WNBA using a nonparametric win-probability model, but this is not peer-reviewed and does not use a closing-line benchmark. Qureshi & Zaman (2021, arXiv) show NBA moneyline inefficiency during COVID, with no comparable effect in other sports.

**CLV as the evaluation standard.**
- Industry consensus (Pinnacle and Buchdahl writing; SharpAPI and OddsPapi CLV tooling) treats beating the de-vigged closing price as the best short-sample proxy for edge. The Pinnacle article could not be fetched, so this is **(unverified)**.
- Academic support is indirect: Levitt (2004), plus the efficiency results above showing the close is near-unbiased.
- Hubáček & Šír (2020, arXiv) show a model can profit while being *less* accurate than the market if it is decorrelated from it. Report both accuracy and market-relative metrics.
- **Recommended scorecard:**
  - log-loss and Brier of our win probability vs the de-vigged closing probability (skill score);
  - margin MAE and RMSE vs the closing spread;
  - average CLV in cents/points for simulated entries at a fixed time (e.g. T−6h);
  - ATS/O-U record with Wilson CIs, used as a secondary check only.

**De-vigging methods** (all implemented in the R `implied` package; Python `shin` also exists):
- **multiplicative / basic:** divide by the booksum;
- **additive:** subtract equal margin;
- **power:** a single exponent makes the probabilities sum to 1, which shrinks longshots more;
- **Shin (1992/93):** an insider-trading model that also estimates the insider fraction z;
- **balanced-book** (Fingleton & Waldron 1999), **odds-ratio** (Cheung 2015), **WPO** (Buchdahl), **JSD**.

The `implied` author says no method is universally best, so test on our own data. Štrumbelj (2014, *IJF*) is the standard reference finding Shin better calibrated than basic normalization; the abstract was not opened, so this is **(unverified)**. For two-way NCAAB spread and total markets, the methods differ only slightly. For moneylines with heavy favorites, power or Shin matters.

**Kelly sizing.**
- "Optimal Betting Under Parameter Uncertainty: Improving the Kelly Criterion" (INFORMS, DOI 10.1287/deca.2013.0271; authors Baker & McHale, 2013, *Decision Analysis* **(authors/journal unverified, inferred from DOI)**): shrink Kelly stakes when probabilities are estimated. Shrunken Kelly beat raw Kelly in simulations and tennis data.
- Metel (2017, arXiv): accounting for estimation error raises returns.
- Uhrín et al. (2021, arXiv; horse racing, basketball, soccer): risk controls are needed in practice, and **adaptive fractional Kelly** performed well across settings.
- **Use:** quarter-Kelly or less, with per-day exposure caps.

---

## 5. Recommended data plan (cheapest path)

### (a) Closing spreads, totals and moneylines, MSU + all Big Ten games, 2021-22 to 2025-26
1. **Primary (free):** CBBD `/lines?season=YYYY&conference=B1G` for each season. It returns open and close spread, total and moneyline per provider, joined to CBBD game IDs that match its play-by-play and box data. This is about 1,650 Big Ten-involved games in total (14 teams before 2024-25, 18 after; rough estimate). Register a free key.
2. **Cross-check (free):** ESPN core odds API (`/events/{id}/competitions/{id}/odds`), confirmed complete for MSU in all five seasons. Use its explicit `open`/`close` from 2022-23 onward; for 2021-22 take the "consensus" provider plus the books.
3. **Third check (free):** SBRO 2021-22 HTML table (open and close spread and total, ML, 2H) and Prediction Tracker season CSVs (opening and updated line for every D-I game 2003–2026). The Prediction Tracker files also give ready-made computer-rating baselines.
4. **Timestamped close (optional paid, one month):** The Odds API **100K plan ($59)**. Request a historical snapshot at each tip time minus about 5 minutes: 3 markets × 1 region (us) = 30 credits per tip slot. About 1,650 Big Ten games needs roughly 50K credits, which fits in one month. The **5M plan ($119)** would cover all of D-I. This gives a true multi-book close with timestamps for CLV, and Pinnacle via the `eu` region **(unverified for NCAAB)**.

### (b) First-half lines
- **2023-24 to 2025-26:** The Odds API historical *event-odds* endpoint (`spreads_h1`, `totals_h1`, `h2h_h1`). Cost is 10 credits per region per market per event, so 3 markets for about 1,000 Big Ten games is roughly 30K credits on the same paid month. Books' NCAAB 1H coverage is not guaranteed **(unverified)**.
- **2021-22:** only SBRO **2H** lines. **2022-23:** no public 1H archive found. Accept the gap or test SportsDataIO Replay or BigDataBall ($30/season, 2022-23+, 1H columns unverified).
- **2025-26:** Kalshi `KXNCAAMB1HSPREAD` / `1HTOTAL` / `1H` and Polymarket game events (free) as a market-implied 1H benchmark.

### (c) Player props
- **No archive before May 2023.** For 2023-24 to 2025-26, The Odds API event-odds endpoint with `player_points`, `player_rebounds`, `player_assists` and `player_threes` (US books only). This is expensive per event; limit it to MSU games, about 100 games × 4 markets × 10 credits ≈ 4K credits. Expect sparse coverage for non-marquee games **(unverified)**.
- **Start collecting now:** daily Odds API props snapshots for MSU and Big Ten games. The free 500-credit tier is too small, so use the $30 plan.

### (d) Live / in-game lines going forward
- **No affordable historical live archive exists.** SportsDataIO in-game line movement and OpticOdds are paid or enterprise.
- **Start collecting now (free):**
  - poll ESPN "Live Odds" providers (DraftKings / ESPN BET – Live Odds appear in 2024-25 and 2025-26);
  - record Kalshi 1-min candles and trades for in-play `KXNCAAMBGAME` / spread / total markets;
  - record Polymarket 1-min `prices-history` for in-play markets.
- **Paid upgrade:** The Odds API live polling at 1–5 min.

### (e) Prediction-market prices going forward
- **Free and complete via API:**
  - Kalshi: series `KXNCAAMBGAME`, `KXNCAAMBSPREAD`, `KXNCAAMBTOTAL`, 1H/2H markets, `KXNCAAMBBIG10REG`, `KXNCAABBIG10`, `KXMARMAD*`. Use the `/historical/*` endpoints once markets are past the cutoff.
  - Polymarket: `cbb` series 10470 and `ncaab` series 39 via Gamma, plus CLOB `prices-history`.
- Backfill 2025-26 now. Neither venue has NCAAB game markets before 2025-26, so 2021-22 to 2024-25 benchmarks must come from sportsbooks.
- **Collector cadence:** hourly snapshots from market open, 1-min from T−3h through the final whistle. Store bid, ask, last and volume, not just the mid.

### Must start collecting ourselves now (no archive exists)
1. Player props (all seasons before 2023-05 are gone; after that, only paid snapshots).
2. Live and in-game lines from sportsbooks.
3. Order-book depth and bid/ask on Kalshi and Polymarket (candles keep OHLC, not full depth).
4. 1H lines for Big Ten games from multiple books with timestamps (only The Odds API has them from 2023).
5. Exchange markets (ProphetX, Novig) have no public historical API. Snapshot them only if accessible and lawful, and not from inside Michigan.

### Source count
- **Free or freemium (14):** SBRO, ESPN core API/hoopR, CBBD `/lines`, Prediction Tracker, TeamRankings pages, Covers, KillerSports/SDQL, OddsPortal, Kaggle datasets, Massey (scores), cbbdata/Torvik (predictions), Kalshi API, Polymarket API, Betfair Basic.
- **Paid (9):** The Odds API, SportsDataIO, OddsJam/OpticOdds, SportsGameOdds (historical on Pro), Unabated, Action Network/Action Labs, BigDataBall, Betfair Advanced/Pro, Prediction Hunt Dev tier.

---

## Sources opened

**Odds data**
- https://www.sportsbookreviewsonline.com/scoresoddsarchives/ncaabasketball/ncaabasketballoddsarchives.htm
- https://www.sportsbookreviewsonline.com/scoresoddsarchives/ncaa-basketball-2021-22
- https://the-odds-api.com/historical-odds-data/
- https://the-odds-api.com/
- https://the-odds-api.com/sports-odds-data/ncaa-basketball-odds.html
- https://the-odds-api.com/sports-odds-data/betting-markets.html
- https://the-odds-api.com/terms-and-conditions.html
- https://sportsdata.io/developers/api-documentation/ncaa-basketball
- https://opticodds.com/historical-odds
- https://sportsapis.dev/apis/odds-jam
- https://sportsapis.dev/apis/unabated
- https://sportsgameodds.com/use-cases/historical-odds-data-api
- https://sportsgameodds.com/pricing
- https://www.actionnetwork.com/ncaab/odds
- https://www.actionnetwork.com/press/introducing-action-labs
- https://www.covers.com/sport/basketball/ncaab/odds
- https://www.covers.com/sportsoddshistory/
- https://www.covers.com/sportsoddshistory/cbb-main/
- https://www.bigdataball.com/datasets/ncaa/cbb-data/historical/
- https://dss.princeton.edu/catalog/resource6741
- https://api.collegebasketballdata.com/ (and /api-docs.json spec)
- https://collegebasketballdata.com/api-tiers
- https://cdn.collegefootballdata.com/Gumroad/CBB%20Starter%20Pack/CBBD%20Starter%20Pack%20-%20Data%20Files%20Guide.pdf
- https://search.r-project.org/CRAN/refmans/hoopR/html/espn_mbb_betting.html
- https://search.r-project.org/CRAN/refmans/hoopR/html/espn_nba_betting.html
- https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/{id}/competitions/{id}/odds (probed)
- https://www.teamrankings.com/ncaa-basketball/matchup/sun-devils-jayhawks-2025-01-08/spread-movement
- https://www.kaggle.com/api/v1/datasets/list (search API) and dataset view pages for zachht/wnba-odds-history, scottfree/sports-lines, oliviersportsdata/datasets-road-to-march-madness
- https://masseyratings.com/scorehelp.htm
- https://github.com/betfair/historic-data-workbook
- https://apis.io/plans/betfair/betfair-plans-pricing/
- https://oddspapi.io/us
- https://docs.sharpapi.io/en/api-reference/historical-clv/
- https://www.thepredictiontracker.com/basketball.php
- https://www.thepredictiontracker.com/predbb.html

**Prediction markets and legal status**
- https://docs.kalshi.com/getting_started/historical_data
- https://docs.kalshi.com/api-reference/market/get-market-candlesticks
- https://docs.kalshi.com/getting_started/rate_limits
- https://api.elections.kalshi.com/trade-api/v2/ (series, events, historical/cutoff, historical/markets, candlesticks; probed)
- https://docs.polymarket.com/developers/CLOB/timeseries
- https://docs.polymarket.com/developers/gamma-markets-api/get-markets
- https://gamma-api.polymarket.com/ (sports, events; probed), https://clob.polymarket.com/prices-history (probed), https://data-api.polymarket.com/trades (probed)
- https://prediction.com/blog/polymarket-kalshi-historical-data
- https://docs.delphina.ai/sandbox/ncaa-basketball.md
- https://www.covers.com/industry/kalshi-march-madness-prediction-markets-surpass-200-million-march-24-2025
- https://www.covers.com/industry/kalshi-football-season-sports-betting-spreads-totals-props-august-18-2025
- https://spectrumlocalnews.com/mi/michigan/news/2026/06/30/michigan-blocks-sports-betting-kalshi
- https://spectrumlocalnews.com/mi/michigan/news/2026/09/02/michigan-judge-blocks-kalshi
- https://www.gaming.net/michigan-court-orders-kalshi-to-halt-sports-contracts/
- https://cdcgaming.com/michigan-robinhood-pulls-sports-event-contracts-as-court-cases-continue/
- https://frontofficesports.com/article/polymarket-returns-to-the-u-s-after-nearly-four-years/
- https://next.io/prediction-markets/polymarket/legal/
- https://sbcamericas.com/2026/08/04/novig-prediction-markets-relaunch/
- https://www.gambling.com/us/prediction-markets/reviews/prophetx
- https://www.actionnetwork.com/online-sports-betting/reviews/sporttrade
- https://www.gambling.com/us/news/sporttrade-exits-us-sports-betting-market-in-pivot-to-prediction-markets
- https://www.legalsportsreport.com/prediction-markets/draftkings-predictions-vs-fanduel-predicts/

**Models**
- https://kenpom.com/blog/ratings-methodology/
- https://kenpom.com/blog/prediction-tracker/
- https://kenpompy.readthedocs.io/
- https://www.covers.com/ncaab/what-are-torvik-ratings
- https://www.torvik.dev/
- https://cbbdata.aweatherman.com/reference/index.html
- https://github.com/andreweatherman/cbbdata/
- https://haslametrics.com/ and https://haslametrics.com/about.php
- https://blog.evanmiya.com/p/bayesian-performance-rating
- https://www.natesilver.net/p/2025-march-madness-ncaa-tournament-predictions
- https://datahub.io/fivethirtyeight/march-madness-predictions-2018
- https://en.wikipedia.org/wiki/Jeff_Sagarin
- https://github.com/lbenz730/ncaahoopR
- https://codefixsolution.com/best-college-basketball-prediction-sites/ (vendor page; numbers not used)

**Efficiency, CLV, de-vig, Kelly**
- https://www.stat.berkeley.edu/~aldous/157/Papers/PointShaving.pdf (Wolfers 2006)
- https://news.illinois.edu/researchers-dispute-study-pointing-to-college-basketball-point-shaving/
- https://ideas.repec.org/a/buc/jpredm/v4y2010i2p15-22.html (Borghesi, Paul & Weinbach 2010)
- https://verso.uidaho.edu/esploro/outputs/journalArticle/Efficiency-in-the-madness-examining-the/996651783101851 (Hickman 2020)
- https://ideas.repec.org/a/spr/jecfin/v44y2020i3d10.1007_s12197-020-09507-7.html
- https://ideas.repec.org/a/eee/quaeco/v63y2017icp233-239.html (Berkowitz, Depken & Gandar 2017)
- https://ideas.repec.org/a/spr/jecfin/v42y2018i4d10.1007_s12197-018-9437-y.html (Francisco & Moore 2018)
- https://ideas.repec.org/a/spr/jecfin/v29y2005i3p385-390.html (Woodland & Woodland 2005)
- https://ideas.repec.org/a/sae/jospec/v22y2021i3p251-273.html (Cox et al. 2021, CFB)
- https://ideas.repec.org/a/ecj/econjl/v114y2004i495p223-246.html (Levitt 2004)
- https://ideas.repec.org/a/inm/ormnsc/v70y2024i12p8583-8611.html (Simon 2024)
- https://arxiv.org/abs/1910.08858 (Ramesh et al. 2019)
- https://arxiv.org/abs/2109.07581 (Qureshi & Zaman 2021)
- https://arxiv.org/abs/2010.12508 (Hubáček & Šír 2020)
- https://arxiv.org/abs/2107.08827 (Uhrín et al. 2021)
- https://arxiv.org/abs/1701.02814 (Metel 2017)
- https://pubsonline.informs.org/doi/fpi/10.1287/deca.2013.0271 (Kelly under parameter uncertainty)
- https://arxiv.org/abs/1211.4000 (Szalkowski & Nelson 2012)
- https://arxiv.org/abs/1412.0248 (Lopez & Matthews 2014)
- https://search.r-project.org/CRAN/refmans/implied/html/implied_probabilities.html
- https://www.r-bloggers.com/the-probabilities-implied-by-bookmaker-odds-introducing-the-implied-package/
- https://www.fri.uni-lj.si/en/node/1957 (Štrumbelj 2014 JSE citation)
- https://gametheorypicks.substack.com/p/what-is-closing-line-value

**Attempted, could not open:** OddsPortal (robots), KillerSports (JS-only), Pinnacle CLV article, ESPN BPI explainer (empty), 538 methodology (redirect), Betfair historic portal (JS), Štrumbelj IJF abstract, Kaggle web search UI.
