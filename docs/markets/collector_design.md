# Market data collector: design (Job B1)

Written 2026-10-18 (UTC) for MSU Alpha 3, Job B1 of `coord/prompts/002-claude-code-taxonomy-and-markets.md`. This document designs a **read-only** collector of sportsbook lines and prediction-market prices. Those prices will later benchmark our own probabilities (see "Layered prediction and market benchmarks" and "Odds and prediction-market data" in `docs/requirements.md`).

How to read this document:
- Every factual claim carries the URL of a page, file or API response that a researcher opened during Job B1 (17–18 Oct 2026). The research notes are in the session scratchpad (`research/job-b1/*.md`).
- **(unverified)** means the claim could not be confirmed from a primary source. The mark is carried through from the notes.
- **[probed]** means one read-only, unauthenticated request to a public endpoint, made during the research.
- **[computed]** means a researcher calculated the value.
- Times are UTC unless stated otherwise. Durations are in seconds (s), with hours (h) or days (d) for readability. Spreads and totals are basketball points (scores), not distances. No length units occur in this topic.
- Nothing here is legal advice.
- No account was created, no key was requested, nothing was bought, and no order, account or trading endpoint was called.

---

## 0. Summary and decisions needed

| Source | Role | Auth | Cost | Research terms | History we can get | Status for B2 |
|---|---|---|---|---|---|---|
| CollegeBasketballData.com (CBBD) `/lines` | Primary bulk open/close lines, 2021-22 onward | Free key (bearer) | $0 (optional Patreon $1–$10/mo) | Research, model training and private archive allowed; no raw redistribution | Lines 2013–present; one value per game × provider, no timestamps | **Needs Aldemir to register a free key** |
| ESPN core odds API | Native ESPN-ID open/close/current per book; live odds | None (undocumented) | $0 | Disney ToU: personal non-commercial use only; automated extraction prohibited | All 177 completed MSU games 2021-22 to 2025-26 have a spread [probed] | **Decision needed** (ToU risk; the Job B text says "only through hoopR's prebuilt releases") |
| Sportsbook Reviews Online (SBRO) | Independent third check, 2021-22 only | None | $0 | All rights reserved; no reproduction without consent | 2007-08 to 2021-22, not updated | **Decision needed** (one-time private fetch) |
| The Odds API | Timestamped multi-book lines, 1H, props, live | API key | Free 500 credits; $30 / $59 / $119 / $249 per month | Storage, research and ML allowed; no redistribution as a data product | Featured from 2020-11-16; 1H and props from 2023-05-03 | **Design and cost only; Aldemir decides on purchase** |
| Kalshi public market data | Exchange prices, 1-min candles, 2025-26 onward | None for market data | $0 | Developer Agreement v1.1 and Data Terms appear to forbid collection, storage and ML use without written consent | NCAAM game markets from 2025-11-03 | **Blocked pending Aldemir's decision on terms** |
| Polymarket (Gamma, CLOB, Data API v2) | Exchange prices, 2025-26 onward | None for reads | $0 | Anti-scraping clause; personal licence; no redistribution | CBB game markets from 2025-26; 1-min history kept ≥ 7 d only | **Can start once decision 6 is recorded** (terms risk + identity-field redaction); module ships with `polymarket.enabled: false` until then |

Decisions for Aldemir (one line each; detail in the sections named):
1. Register a free CBBD key and store it outside git (section 1.1).
2. ESPN: accept the Disney ToU risk for a low-volume private collector, limit ESPN to manual cross-checks, or use only hoopR prebuilt release files (sections 1.2, 6). The scheduler, the weekly completeness denominator and the game-ID join all lean on ESPN schedule reads, so the decision has three concrete options:
   - (i) **schedule reads only**: site `/scoreboard?groups=7` daily plus hourly on game days, and `/teams/127/schedule` daily. On the 2025-26 calendar (156 season days, 122 game days) that is about 156 × 2 + 122 × 24 ≈ 3,240 requests per season [computed], with no odds reads;
   - (ii) schedule reads **and** core `/odds` reads (sections 2.2, 2.4, 2.5);
   - (iii) **no automated ESPN reads.** Fallback schedule source: CBBD `/games` (its `sourceId` is the ESPN event ID, section 1.1; `startDate` gives the tip time), cross-checked against the hoopR prebuilt schedule files `mbb_schedule_{season}.parquet` in the sportsdataverse-data release `espn_mens_college_basketball_schedules` (seasons labelled 2002–2027; last asset written 2026-09-15) ([release](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_mens_college_basketball_schedules), [hoopR load_mbb.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/load_mbb.R)). The prebuilt files are refreshed in batches, so under (iii) tip-time changes are caught only by the daily CBBD call and by each market source's own start time, and the "actual tip" in section 2.2 falls back to the scheduled tip. Sections 2.1, 4.3 and 5 name this fallback.
3. SBRO: approve a one-time private fetch of the 2021-22 page (section 1.3).
4. The Odds API: approve the recommended $269 plan for 2026-27, a cheaper option, or none (section 7).
5. Kalshi: ask Kalshi for written research permission, evaluate Dune's licensed tables, or drop Kalshi (sections 1.5, 6).
6. Polymarket: accept the terms risk for private, rate-limited reads, or email Polymarket first. Also decide whether wallet and profile fields may be stripped before the raw store (sections 1.6, 3.1, 6). Until this is recorded, the Polymarket module ships with `polymarket.enabled: false`, as Kalshi does.
7. Collector host: an always-on Mac (launchd + APScheduler; $0 on existing hardware) or a small cloud VM (e.g. DigitalOcean 1 vCPU / 1 GiB at $6/mo or 1 vCPU / 2 GiB at $12/mo; section 2.6). Colab and GitHub Actions cannot capture 1-minute in-game prices (section 2.6).
8. Cross-source tolerance: keep the single 0.5-point rule, or adopt the tiered tolerances in section 4.1.
9. Default fair-probability method: choose it from our own NCAAB log-loss test (recommended) or fix it to power now (section 3.3).

**Requirement IDs.** The IDs R-MK-01 to R-MK-09, R-DQ-01, R-DQ-05, R-RG-07 and R-RG-08 appear in the Job B prompt, but a grep of `docs/requirements.md` on 17–18 Oct 2026 found none of them. The market requirements exist there only as prose, under "Layered prediction and market benchmarks" and "Odds and prediction-market data". This design therefore follows the Job B1 bullet list section by section. The requirements session should assign the IDs, and a later dated note can map them to the sections below.

**Conflicts with the Job B text, flagged rather than resolved:**
- Job B1 says ESPN odds come "only through hoopR's prebuilt releases", but Job B2 lists ESPN among the free sources to collect now. The research notes did not check whether hoopR's prebuilt release files contain odds **(unverified)**. *Checked 2026-10-18 (fix pass):* hoopR's prebuilt loaders (`load_mbb_*`) read files from the `sportsdataverse/sportsdataverse-data` GitHub releases, not from `hoopR-mbb-data`, whose releases page shows no releases ([hoopR load_mbb.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/load_mbb.R), [hoopR reference index](https://hoopr.sportsdataverse.org/reference/index.html), [hoopR-mbb-data releases](https://github.com/sportsdataverse/hoopR-mbb-data/releases)). No loader or release asset is a betting/odds file: the MBB release `espn_mens_college_basketball_pbp` holds only `play_by_play_{season}` CSV/Parquet/RDS (seasons labelled up to 2026, last asset written 2026-09-19), and the schedules release holds only schedule files ([pbp release](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_mens_college_basketball_pbp), [schedules release](https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_mens_college_basketball_schedules)). The only odds content found is four game-level columns documented for `load_mbb_pbp`: `home_team_spread`, `game_spread` ("signed; positive = home favored"), `home_favorite` and `game_spread_available` ([load_mbb.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/load_mbb.R)). That is one spread per game with no book, no open/close distinction, no timestamp, no moneyline and no total documented, so the prebuilt route can supply at most a single-spread cross-check, not the open/close/multi-book data this design needs. Which book and which moment that spread represents is **unverified** (no data file was downloaded). The conflict therefore stands. hoopR's odds functions (`espn_mbb_betting`, `espn_mbb_game_odds`, `espn_mbb_game_propbets`) call ESPN live ([hoopR espn_mbb_data.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/espn_mbb_data.R), [espn_mbb_event_detail.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/espn_mbb_event_detail.R)).
- Job B2 lists Kalshi among the free sources to collect now. Kalshi's own agreement text appears to forbid this use (section 1.5).
- `docs/requirements.md` says prediction-market prices are "Free, no account needed to read". That is technically true, but it says nothing about the terms of use (sections 1.5, 1.6).

---

## 1. Sources and endpoints

### 1.1 CollegeBasketballData.com (CBBD) `/lines`

**Operator and auth**
- Run by Rad Sports Analytics LLC, which also runs CollegeFootballData.com; one set of terms covers both ([terms](https://collegebasketballdata.com/terms)). One key works for both APIs ([README](https://raw.githubusercontent.com/CFBD/cbb-api/main/README.md)).
- Request a key by email at [collegebasketballdata.com/key](https://collegebasketballdata.com/key). Send it as `Authorization: Bearer <key>` ([authentication](https://api.collegebasketballdata.com/authentication.md)). Keep it server-side and out of git, in an env var such as `CBBD_API_KEY`.
- Without a key, `/lines/providers` returns HTTP 401 with the message "Unauthorized. Use "Bearer <key>"…" [probed: https://api.collegebasketballdata.com/lines/providers].
- OpenAPI spec v1.30.1 ([api-docs.json](https://api.collegebasketballdata.com/api-docs.json)) [probed].

**Endpoints**
- `GET https://api.collegebasketballdata.com/lines`: up to 3,000 games per call, ordered by start date. Optional filters: `season` (ending year, 2026 = 2025-26), `team`, `conference`, `startDateRange`, `endDateRange` ([api-docs.json](https://api.collegebasketballdata.com/api-docs.json), [data availability](https://api.collegebasketballdata.com/data-availability.md), [controller.ts](https://raw.githubusercontent.com/CFBD/cbb-api/main/src/app/lines/controller.ts), [service.ts](https://raw.githubusercontent.com/CFBD/cbb-api/main/src/app/lines/service.ts)).
  - Each row: `gameId` (CBBD's, not ESPN's), `season`, `seasonType`, `startDate`, team IDs and names, conferences, scores, and `lines[]` with `provider`, `spread`, `overUnder`, `homeMoneyline`, `awayMoneyline`, `spreadOpen`, `overUnderOpen`.
- `GET /lines/providers` returns `[{id, name}]`.
- `GET /games` is the ID bridge: `GameInfo.sourceId` is the ESPN game ID ([hoopR cbbd_games.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/cbbd_games.R): "Source (ESPN) game id"; [hoopR CBBD vignette](https://hoopr.sportsdataverse.org/articles/cbbd-college-basketball-data.html)). The cbbd-r README shows `source_id` 401715612, which resolves to an ESPN event ([cbbd-r](https://github.com/CFBD/cbbd-r); [probed: ESPN summary?event=401715612](https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event=401715612)). The spec itself does not document `sourceId`, so **verify on the first keyed call**.

**Rate limits and quota**
- The monthly call quota is shared between CBBD and CFBD ([terms](https://collegebasketballdata.com/terms), [api-tiers](https://collegebasketballdata.com/api-tiers)).
- The tiers page lists prices (Free $0, Tier 1+ $1, Tier 2+ $5, Tier 3+ $10 per month via Patreon) but **no call quotas** ([api-tiers](https://collegebasketballdata.com/api-tiers)).
- The Jan 2025 launch post gives Free 1,000 / Tier 1 5,000 / Tier 2 30,000 / Tier 3 75,000 calls per month; the post says "These tiers and limits are subject to change prior to the 2025 season." It says there is no REST throttling, but Cloudflare can block for ≈ 600 s after bursts ([radsportsanalytics.com](https://radsportsanalytics.com/blog/api-v2-is-now-in-general-availability/)). A "Historical note (reviewed July 14, 2026)" added to the post says the tier list describes the launch period and points readers to the current API tiers page, which lists no numbers ([radsportsanalytics.com](https://radsportsanalytics.com/blog/api-v2-is-now-in-general-availability/), [api-tiers](https://collegebasketballdata.com/api-tiers)). Treat 1,000/month as historical, and read `X-CallLimit-Remaining` on the first keyed call. The cbbd-r README also says 1,000 free calls per month ([cbbd-r](https://github.com/CFBD/cbbd-r)). **Whether these numbers still apply in Oct 2026 is unverified.**
- From the source code ([quotas.ts](https://raw.githubusercontent.com/CFBD/cbb-api/main/src/config/middleware/quotas.ts)):
  - each metered call decrements the quota;
  - at zero the API returns HTTP 429 "Monthly call quota exceeded.";
  - non-2xx responses are refunded;
  - every response carries `X-CallLimit-Remaining`.
  - Only `/lineups/team` has a concurrency cap ([middleware/index.ts](https://raw.githubusercontent.com/CFBD/cbb-api/main/src/config/middleware/index.ts)).
- Error codes: 400, 401, 404, 429 or entitlement, 500 ([usage-and-access](https://api.collegebasketballdata.com/usage-and-access.md)).

**Terms for research** ([terms](https://collegebasketballdata.com/terms))
- Allowed: historical analysis, backtesting, feature engineering, model training, publishing derived outputs, commercial use, and private caching and storage. Data retrieved while access was active may be kept in a private archive after access ends.
- Prohibited: redistributing raw data (datasets, bulk downloads, mirrors, substitute APIs), sharing keys or raw responses, scraping, and multiple accounts used to evade quotas.
- Attribution is recommended, not required.

**History and known defects**
- Betting lines 2013–present. "Provider, opening line, total, and moneyline coverage varies by game. A returned game can have an empty lines list." ([data availability](https://api.collegebasketballdata.com/data-availability.md)).
- Per-season completeness for MSU and Big Ten games, and the provider names, are **unverified** until a key exists.
- The `game_line` table has **no timestamp column**: one close (or latest) value and one open value per game × provider ([db.d.ts](https://raw.githubusercontent.com/CFBD/cbb-api/main/src/config/types/db.d.ts)).
- **Pick'em defect:** the service maps values with JavaScript truthiness, so a spread of 0 comes back as `null` ([service.ts](https://raw.githubusercontent.com/CFBD/cbb-api/main/src/app/lines/service.ts)). Treat `spread is null and overUnder not null` as "possible pick'em; verify against another source".
- Spread sign convention for CBBD is **unverified**. Check on the first call that a home favourite has `spread < 0` and `homeMoneyline < 0`.
- No pagination: the 3,000-row cap truncates silently. Always slice by `conference` or by date windows. One `season=YYYY&conference=B1G` call returns all games involving a Big Ten team. Whether the stored conference string is "B1G" or "Big Ten" is **unverified**; test both ([api-docs.json](https://api.collegebasketballdata.com/api-docs.json)).
- **Inference (unverified):** `line_provider.source_id` suggests CBBD ingests the ESPN odds feed ([db.d.ts](https://raw.githubusercontent.com/CFBD/cbb-api/main/src/config/types/db.d.ts)). If so, CBBD and ESPN are not independent, and a CBBD-vs-ESPN check mostly tests ingestion.
- CBBD gives **no prices on spreads or totals** (no juice). De-vig is possible only for moneylines. Store spread and total prices as unknown, never as an assumed −110.

**Client**
- Python `cbbd` 1.30.1 (2026-10-09, MIT) exists ([PyPI](https://pypi.org/project/cbbd/), [LinesApi.md](https://github.com/CFBD/cbbd-python/blob/main/docs/LinesApi.md)). It deserializes into models and drops the raw body.
- **Proposal:** call the REST endpoints directly so that the exact body and headers can be stored first (section 3.1).

**Call budget**
- Backfill: 5 seasons × 2 calls (`/games` + `/lines`) = 10 calls.
- In season: about 2 calls/day × ~150 days ≈ 300 calls [computed].

### 1.2 ESPN odds (core API; hoopR and sportsdataverse wrappers)

**Status, auth, rate limits**
- The endpoints are undocumented and serve ESPN's own apps. No key is needed [probed]. Community catalogue: [pseudo-r/Public-ESPN-API](https://github.com/pseudo-r/Public-ESPN-API) (MIT). It says the endpoints may change without notice, rate limits are not published, and "public" does not mean permission. See also the [Zuplo guide](https://dev.to/zuplo/unlocking-espns-hidden-api-a-developers-guide-1pp7).
- The claim that ESPN closed its public API in 2014 comes from a search snippet only ([AppDeveloper Magazine](https://appdevelopermagazine.com/The%20World%20Wide%20Leader%20in%20Sports%20Leaves%20Developers%20in%20a%20World%20of%20Hurt%20as%20ESPN%20Closes%20Public%20API/), **not opened, unverified**).
- Core odds responses carry `cache-control: max-age=900, stale-while-revalidate=7200`, so a value can be up to 900 s old. About 700 calls at roughly 4–5 requests/s produced no 429 [probed]. API hosts deny or 403 `robots.txt`, and [www.espn.com/robots.txt](https://www.espn.com/robots.txt) disallows several AI crawlers [probed].

**Terms**
- ESPN falls under the Disney Terms of Use (updated 2024-05-24) ([Disney ToU](https://disneytermsofuse.com/english/)):
  - §2.A: "personal, noncommercial use only";
  - §2.B bans accessing or extracting content "using a robot, spider, script, or other automated means" and "data mining or web scraping".
- Automated collection is against the letter of these terms even for non-commercial research. hoopR's MIT licence does not change the underlying ESPN terms (`docs/research/data_sources_catalog.md`, row 9).

**Endpoints** (base `https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball`; all GET, no auth; [probed])

| Purpose | Path | Notes |
|---|---|---|
| Odds, all providers | `/events/{id}/competitions/{id}/odds?limit=100` | One item per provider. Event ID = competition ID |
| One provider | `/events/{id}/competitions/{id}/odds/{providerId}` | |
| Odds history | `…/odds/{providerId}/history/{0,1,2}` and `/movement?limit=100` | 0 = moneyline, 1 = spread, 2 = total. Timestamped rows only for provider 1002 "teamrankings", 2021-22 and 2022-23 |
| Prop bets | `…/odds/{providerId}/propBets` | 404/500 for completed MSU games. Historical MBB props are not retained; pre-game availability **unverified** |
| Provider registry | `/providers?limit=200` | 67 IDs |
| ESPN model outputs (not market) | `…/probabilities`, `…/predictor` | Do not mix with market prices |

Site API (`https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball`) [probed]:
- `/summary?event={id}`: its `pickcenter` is a reduced copy with fewer providers and, in 2025-26, no open/close. Collect from core `/odds` instead.
- `/scoreboard?dates=YYYYMMDD&groups=50` (all D-I) or `groups=7` (Big Ten): completed games have no odds. Whether MBB scoreboard odds appear pre-game is inferred from the NBA shape **(unverified)** ([probed NBA scoreboard](https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=20261021)).
- `/teams/127/schedule?season={endYear}&seasontype={2|3}`: MSU event IDs (MSU team ID 127).

**Response facts** [probed: core odds for event 401825481 and all MSU games]
- The top-level `spread` is the **home team's** handicap. sportsdataverse-py states the same ([_espn_basketball_pbp.py](https://raw.githubusercontent.com/sportsdataverse/sportsdataverse-py/main/sportsdataverse/_espn_basketball_pbp.py)).
- Each book has `open`, `close` and `current` blocks with American (string), decimal and fraction prices. Team identity comes from `team.$ref` (127 = Michigan State).
- `moneylineWinner` and `spreadWinner` stayed `false` after games ended; never use them as results.

**History, MSU completed games** [probed, [core odds endpoint](https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/401825481/competitions/401825481/odds)]

| Season | Games | With spread | Items with `open` | Items with `close` | Providers |
|---|---|---|---|---|---|
| 2021-22 | 36 | 36 | 0 | 0 | ~14 (Caesars variants, DraftKings, MGM, consensus, teamrankings, accuscore…) |
| 2022-23 | 34 | 34 | 0 | 34 (ESPN BET only) | ~15 |
| 2023-24 | 35 | 35 | 35 | 34 | ~13 |
| 2024-25 | 37 | 37 | 37 | 37 | ESPN BET + its Live Odds provider |
| 2025-26 | 35 | 35 | 35 | 35 | DraftKings (100), ESPN BET (58), Live Odds variants |

- DraftKings became ESPN's sportsbook partner starting December 2025; ESPN BET was to be rebranded theScore Bet by Dec. 1. The article's summary says the deal makes DraftKings ESPN's "official betting site and odds provider" ([BNN Bloomberg](https://www.bnnbloomberg.ca/business/2025/11/06/espn-taps-draftkings-as-sports-betting-partner-after-ending-penn-deal/)). That DraftKings (provider 100) is the book in the MBB core odds feed for 2025-26 comes from our probes [probed].
- **From 2024-25 on, ESPN carries one book per game**, so cross-book checks need other sources.
- League-wide coverage on sampled dates: 42/43 games (2022-01-19), 47/48 (2025-01-15), 138/139 (2026-01-31); Big Ten games 100% [probed].
- Provider names are current labels; "ESPN BET" (58) appears on 2022-23 games. That ESPN relabelled an older ID is an inference **(unverified)**. Key on `provider_id`, not the name.

**Data traps** [probed; scripts `espn_close_check.py`, `espn_probe.py`]
1. In 2022-23, `close.pointSpread` holds a **price**, not a point, on 34/34 MSU ESPN BET items. Use the top-level `spread`/`overUnder` for that season.
2. In 2023-24, 10 of 353 book-rows have `close.pointSpread` ≠ top-level `spread`. Keep both and flag.
3. `open == close` on 90/353 (2023-24), 16/37 (2024-25) and 12/37 (2025-26) rows. Treat these as "open possibly unknown".
4. 2021-22 items have only `current`. That the post-game current equals the close is **unverified**.
5. "… – Live Odds" providers (59, 200) hold an in-game snapshot frozen during the game. Exclude them from closing lines.
6. `accuscore` and `teamrankings` are model providers, not books. Tag provider type in a dimension table.
7. hoopR `espn_mbb_game_odds` parses the price block as open/close ([espn_mbb_event_detail.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/espn_mbb_event_detail.R)). Its doc string says MBB results are "typically empty", which the probes contradict. Parse raw JSON ourselves.

**Free timestamped movement (2021-22, 2022-23):** teamrankings (1002) `/movement` rows such as `{"lineDate":"2021-12-11T03:31Z","line":10.0,…}` [probed]. The spread `line` is a magnitude. Rows are not chronological and repeat, and some fall after tip-off. Sort, de-duplicate and keep `lineDate < tip`. The book behind "teamrankings" is **unverified**.

**Wrappers:** hoopR (MIT, 3.1.0.9000 on GitHub main) ([DESCRIPTION](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/DESCRIPTION)); Python `sportsdataverse` 0.1.4 (MIT) ([PyPI JSON](https://pypi.org/pypi/sportsdataverse/json), [mbb_pbp.py](https://raw.githubusercontent.com/sportsdataverse/sportsdataverse-py/main/sportsdataverse/mbb/mbb_pbp.py)). hoopR's betting helper falls back to core odds when `pickcenter` is empty ([betting helpers](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/espn_basketball_event_betting_helpers.R)).

### 1.3 Sportsbook Reviews Online (SBRO) archive

- Index: [ncaabasketballoddsarchives.htm](https://www.sportsbookreviewsonline.com/scoresoddsarchives/ncaabasketball/ncaabasketballoddsarchives.htm) [curl; WebFetch was refused by user-agent filtering]. It offers moneylines, 2nd-half lines, and opening and closing spreads and totals, and says the archive "will not be updated".
- Seasons: 2007-08 to 2020-21 as `.xlsx`; **2021-22 as an HTML table only** ([2021-22 page](https://www.sportsbookreviewsonline.com/scoresoddsarchives/ncaa-basketball-2021-22/)); nothing later. In our window SBRO covers only 2021-22. The xlsx files were not downloaded.
- Auth none; rate limits none (static files). [robots.txt](https://www.sportsbookreviewsonline.com/robots.txt) disallows only `/go/`.
- Columns: `Date | Rot | VH | Team | 1st | 2nd | Final | Open | Close | ML | 2H`. The xlsx header is the same ([Goldstein 2024, IUSB TR](https://www.cs.iusb.edu/technical_reports/TR-20240429-1_Goldstein.pdf)). 2021-22 has 5,481 games in two rows each; MSU has 36 games [probed, parsed].
- Parsing rules [probed]:
  - In `Open`, `Close` and `2H`, the **smaller number is the spread** (on the favourite's row) and the larger is the total. It is not "visitor = total, home = spread", which is how the IUSB report describes it.
  - `Date` is MMDD with no year.
  - Tokens `pk`, `NL`, `NA`, blanks and corrupted cells (e.g. `.5+03`) go to quarantine.
  - That `ML` is the closing moneyline is **unverified**. Which book or consensus the lines come from is **unverified**.
- Cross-check against ESPN consensus for MSU 2021-22 [probed, `sbro_vs_espn.py`]: every spread difference above 0.5 points, and 4 of 5 total differences, were wrong-game matches on consecutive tournament days. One true disagreement remained (PSU@MSU total 129.5 vs 130.5).
- **Terms:** "You may not use or reproduce any content or materials on our website without our express written consent"; there is no research exception ([terms](https://www.sportsbookreviewsonline.com/terms/)). The archive has been used in research reports ([Goldstein 2024](https://www.cs.iusb.edu/technical_reports/TR-20240429-1_Goldstein.pdf); [Dotan 2020, NBA files](https://escholarship.org/content/qt115957mb/qt115957mb.pdf)).
- **Proposal (pending approval):** one private fetch of the 2021-22 page (about 1.7 MB), used only for internal cross-checks and never republished.

### 1.4 The Odds API (the-odds-api.com): live and historical

Do not confuse it with `theoddsapi.com`, a different provider with different pricing ([theoddsapi.com](https://theoddsapi.com/)). Everything here refers to host `api.the-odds-api.com`.

**Auth:** an `apiKey` query parameter on every request ([v4 guide](https://the-odds-api.com/liveapi/guides/v4/)). Strip it from every stored URL and log. "It is your responsibility to keep your API key private" ([terms](https://the-odds-api.com/terms-and-conditions.html)).

**Endpoints and credit cost per call** ([v4 guide](https://the-odds-api.com/liveapi/guides/v4/))

| Endpoint | Path | Cost |
|---|---|---|
| Sports | `GET /v4/sports/` | Free |
| Events | `GET /v4/sports/basketball_ncaab/events` | Free |
| Odds (featured) | `GET /v4/sports/basketball_ncaab/odds/` (`regions`, `markets`, `oddsFormat`, `eventIds`, `bookmakers`, `commenceTimeFrom/To`, `includeRotationNumbers`, …) | markets × regions |
| Event odds (1H, props, alternates) | `GET /v4/sports/basketball_ncaab/events/{eventId}/odds` | unique markets **returned** × regions |
| Event markets | `GET …/events/{eventId}/markets` | 1 |
| Scores | `GET …/scores/` | 1, or 2 with `daysFrom` |
| Participants | `GET …/participants` | 1 |
| Historical odds | `GET /v4/historical/sports/basketball_ncaab/odds` + `date` | 10 × markets × regions |
| Historical events | `GET /v4/historical/sports/basketball_ncaab/events` + `date` | 1 (0 if empty) |
| Historical event odds | `GET /v4/historical/sports/basketball_ncaab/events/{eventId}/odds` + `date` | 10 × markets returned × regions |
| Historical event markets | `GET …/historical/…/events/{eventId}/markets` | 1 |

- Empty responses cost nothing. With `bookmakers=`, every 10 books count as one region.
- Quota headers on every response: `x-requests-remaining`, `x-requests-used`, `x-requests-last`.
- `/odds` accepts only featured markets (`h2h`, `spreads`, `totals`, `outrights`) and drops completed events. After `commence_time` it serves in-play prices, so a **close must be taken before tip-off**.
- First-half and prop markets work only through event odds, one event per call.
- Historical calls return "the closest snapshot at or before" `date`, wrapped as `{timestamp, previous_timestamp, next_timestamp, data}`.
- Whether historical `/odds` accepts `eventIds`, `bookmakers` and `commenceTimeFrom/To` is **unverified**.
- Event `id` is 32 hex characters. No ESPN ID is provided. `includeSids` returns bookmaker IDs, not ESPN IDs.

**Markets and coverage** ([betting markets](https://the-odds-api.com/sports-odds-data/betting-markets.html), [NCAAB page](https://the-odds-api.com/sports/ncaab-odds.html), [historical data](https://the-odds-api.com/historical-odds-data/), [NCAAB odds data](https://the-odds-api.com/sports-odds-data/ncaa-basketball-odds.html))
- Sport key `basketball_ncaab`. Featured history from **2020-11-16T09:15:00Z**, in 600 s snapshots until Sep 2022 and 300 s after. US bookmaker coverage in 2020 may have been limited **(unverified; none of the four pages cited here says so)**.
- **First-half (`h2h_h1`, `spreads_h1`, `totals_h1` and alternates) and player props (`player_points`, `player_rebounds`, `player_assists`, `player_threes`, `player_points_rebounds_assists`, …): history only from 2023-05-03T05:30:00Z**, i.e. 2023-24 onward. Props are "mainly limited to US sports and US bookmakers".
- The depth of NCAAB 1H and prop coverage by book, especially for non-marquee games, is **unverified**. Quarter keys should be empty for NCAAB, which plays halves (inference).
- Regions ([bookmaker list](https://the-odds-api.com/sports-odds-data/bookmaker-apis.html)):
  - `us`: DraftKings, FanDuel, BetMGM, Caesars (paid only), Fanatics (paid only), BetRivers, Bovada, LowVig and others;
  - `us2`: includes `espnbet` and Hard Rock. The `espnbet` key is now titled "theScore Bet" ("Formerly ESPN Bet"); keep the key, store the title as received;
  - `us_ex`: `kalshi`, `polymarket`, `novig`, `prophetx` and others;
  - `eu`: includes `pinnacle` ("may be delayed");
  - `us_dfs`: indicative only. Exclude it.
- Whether one `bookmakers=` list may mix regions is **unverified**.
- Update intervals ([update intervals](https://the-odds-api.com/sports-odds-data/update-intervals.html)): featured markets 60 s pre-match and 40 s in play; additional markets 60 s; exchanges 20 s / 10 s.

**Rate limit:** "30 requests per second on paid usage plans". 429s can still occur; retry after a couple of seconds ([rate limit](https://the-odds-api.com/guide/rate-limit.html)). The free plan's limit is not stated.

**Plans** ([home](https://the-odds-api.com/), [historical data](https://the-odds-api.com/historical-odds-data/), [FAQ](https://the-odds-api.com/manage/faqs.html), [upgrade/downgrade](https://the-odds-api.com/manage/upgrade-downgrade-cancel-a-subscription.html))
- Starter: free, 500 credits/month, no historical access ("only available on paid usage plans", per the historical-data page and the v4 guide). (The home page's Starter feature list shows "Historical Odds", which conflicts with the historical page and the v4 guide; confirm with the vendor. See section 10, item 4.)
- Paid: 20K $30/mo; 100K $59/mo; 5M $119/mo; 15M $249/mo.
- Upgrades are prorated with credits available immediately. Downgrades take effect at cycle end.
- **Billing ambiguity:** the FAQ says credits reset "on the first of every month", while billing recurs on the subscription day. Rollover of unused credits is not stated. Ask the vendor before buying.

**Terms** ([terms](https://the-odds-api.com/terms-and-conditions.html))
- Permitted: "Storing our data and retaining it indefinitely"; "research papers and analytical dashboards"; training "statistical and machine learning models".
- Prohibited: reselling, repackaging or redistributing the data "as a standalone data product".
- Attribution not required. Payments non-refundable. New South Wales law.

**Status:** design and cost notes only. No account, no purchase and no call until Aldemir decides (Job B2 text). Credit model in section 7.2.

### 1.5 Kalshi public market data

**Hosts** ([api environments](https://docs.kalshi.com/getting_started/api_environments.md))
- Use `https://external-api.kalshi.com/trade-api/v2` (recommended). `https://api.elections.kalshi.com/trade-api/v2` also serves all markets.
- WebSocket needs API-key auth even for public channels, so it is out of scope ([websocket connection](https://docs.kalshi.com/websockets/websocket-connection.md)).

**Auth:** the market-data endpoints declare `security: []`, and the quick start says no authentication headers are required ([quick start](https://docs.kalshi.com/getting_started/quick_start_market_data), [get-markets](https://docs.kalshi.com/api-reference/market/get-markets.md)).

**Endpoints (public)**

| Purpose | Path | Notes |
|---|---|---|
| Series | `GET /series?category=Sports&include_product_metadata=true`, `GET /series/{ticker}` | Fields include `fee_type`, `fee_multiplier` ([series list](https://docs.kalshi.com/api-reference/market/get-series-list.md), [series](https://docs.kalshi.com/api-reference/market/get-series.md)) |
| Events | `GET /events?series_ticker=…&with_nested_markets=true&limit=200` | Cursor pagination; max 200 ([events](https://docs.kalshi.com/api-reference/events/get-events.md), [pagination](https://docs.kalshi.com/getting_started/pagination.md)) |
| Markets | `GET /markets?series_ticker=…` (max 1000), `GET /markets/{ticker}` | ([markets](https://docs.kalshi.com/api-reference/market/get-markets.md)) |
| Trades | `GET /markets/trades?ticker=&min_ts=` | ([trades](https://docs.kalshi.com/api-reference/market/get-trades.md)) |
| Orderbook | `GET /markets/{ticker}/orderbook?depth=` | Bids only; YES bid X = NO ask 1−X ([orderbook](https://docs.kalshi.com/api-reference/market/get-market-orderbook.md)) |
| Candles | `GET /series/{s}/markets/{t}/candlesticks?start_ts&end_ts&period_interval=1\|60\|1440` | ([candlesticks](https://docs.kalshi.com/api-reference/market/get-market-candlesticks.md)) |
| Batch candles | `GET /markets/candlesticks?market_tickers=` (≤ 100 tickers, ≤ 10,000 candles per response) | Historical support **unverified** ([batch](https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks.md)) |
| Event candles | `GET /series/{s}/events/{t}/candlesticks` | Clipped at `adjusted_end_ts`; page from there ([event candles](https://docs.kalshi.com/api-reference/events/get-event-candlesticks.md)) |
| Historical tier | `GET /historical/cutoff`, `/historical/markets?series_ticker=`, `/historical/markets/{t}/candlesticks`, `/historical/trades` | ([historical data](https://docs.kalshi.com/getting_started/historical_data.md), [cutoff](https://docs.kalshi.com/api-reference/historical/get-historical-cutoff-timestamps.md), [hist markets](https://docs.kalshi.com/api-reference/historical/get-historical-markets.md), [hist candles](https://docs.kalshi.com/api-reference/historical/get-historical-market-candlesticks.md), [hist trades](https://docs.kalshi.com/api-reference/historical/get-historical-trades.md)) |

**Never call:** `/portfolio/*`, order endpoints, `/account/*`, `/historical/fills|orders|positions`, FIX or WebSocket ([docs index](https://docs.kalshi.com/llms.txt), [websockets](https://docs.kalshi.com/websockets.md)).

**Rate limits** ([rate limits](https://docs.kalshi.com/getting_started/rate_limits.md))
- Documented only for authenticated users: Basic tier 200 read tokens/s at 10 tokens per request.
- A 429 returns `{"error":"too many requests"}` with no `Retry-After`; apply exponential backoff.
- **No unauthenticated limit is documented.** An earlier session hit 429 unauthenticated (`docs/research/odds_markets_research.md`).
- The probe response carried `cache-control: public, max-age=15` [probed: https://external-api.kalshi.com/trade-api/v2/events?series_ticker=KXNCAAMBGAME&limit=2&with_nested_markets=true].
- **Design:** ≤ 1 request/s per host, jittered backoff (1 s, 2 s, 4 s … max 64 s, ≤ 6 retries), and no re-poll of the same URL within 15 s.

**College basketball markets**
- Men's games: series `KXNCAAMBGAME` (winner; one event per game with two mutually exclusive team markets), `KXNCAAMBSPREAD` and `KXNCAAMBTOTAL` (strike ladders) [probed; [third-party tickers](https://github.com/alexander-bain/bainluck/issues/5023); [Kalshi market-maker list](https://help.kalshi.com/en/articles/13823819-how-to-become-a-market-maker-on-kalshi)].
- 1H/2H, team-total and futures series come from the earlier repo probe only (`docs/research/odds_markets_research.md`) **(unverified in Job B1)**.
- 2026-27 game markets were listed on 2026-10-14 for games on 1–2 Nov 2026 [probed].
- History starts in 2025-26: oldest settled game event 2025-11-03, 5,280 settled events (earlier repo probe; not re-verified). The whole 2025-26 season sits in the historical tier, since the market-settled cutoff was 2026-08-18 on 2026-10-17 (repo; not re-probed).
- Do not parse tickers ([terms page](https://docs.kalshi.com/getting_started/terms.md)). A day number running into a team code has been misread as "1H" ([issue #5023](https://github.com/alexander-bain/bainluck/issues/5023)). Use `series_ticker`, `event_ticker`, `custom_strike.basketball_team` (a team UUID) and `yes_sub_title`.
- `occurrence_datetime` was 08:00 UTC on the game date, which looks like a placeholder, not tip-off (inference) [probed].

**Prices and units**
- All prices are `*_dollars` fixed-point strings "with up to 4 decimal places (e.g., `"0.1200"`)" per the migration page; the candlesticks spec says request fields accept 2–4 decimals and "responses emit up to 6" ([fixed-point migration](https://docs.kalshi.com/getting_started/fixed_point_migration.md), [candlesticks](https://docs.kalshi.com/api-reference/market/get-market-candlesticks.md)). Parse with `Decimal` and do not assume a fixed scale. Counts are `_fp` strings. The legacy integer-cent fields were removed in stages: announced for Market responses on 6 Jan 2026, removed from REST and WebSocket payloads on 12 Mar 2026, and the last remaining legacy fields removed effective 2 Apr 2026 ([changelog](https://docs.kalshi.com/changelog), entries Jan 6, Mar 3/8 and Mar 25 2026).
- Store as strings in raw and parse to Python `Decimal`.
- Candle fields: `end_period_ts`; `yes_bid`/`yes_ask` OHLC; trade `price` OHLC/mean/previous (null with no trade); `volume_fp`; `open_interest_fp`. `include_latest_before_start=true` adds a carry-forward candle ([candlesticks](https://docs.kalshi.com/api-reference/market/get-market-candlesticks.md)). Historical candle field names may differ (`volume` vs `volume_fp`); check them against a real response.
- Fees: a taker fee of $0.07·P·(1−P) per contract applied in the 2021–Apr 2025 sample ([Bürgi, Deng & Whelan](https://www.karlwhelan.com/Papers/Kalshi.pdf); [Allium](https://allium.so/blog/kalshi-fees-why-the-cost-peaks-near-50-cents/)). Current NCAAMB coefficients are **unverified**; the fee schedule PDF returned 429 ([help: fees](https://help.kalshi.com/en/articles/13823805-fees)). Fee rounding: [fee_rounding](https://docs.kalshi.com/getting_started/fee_rounding.md).
- Settlement: a postponement beyond 48 h or a cancellation resolves both markets "to a fair price" [probed]. Store `result`, `expiration_value` and settlement value; never assume 0/1.
- Settlement sources listed: NCAA and ESPN [probed].
- Interpretation: Bürgi et al. (working paper, not peer-reviewed) find a favourite–longshot bias on Kalshi (46,282 contracts; contracts at 10¢ or less lose over 60% on average after fees) ([paper](https://www.karlwhelan.com/Papers/Kalshi.pdf)). Le (2026) (preprint, arXiv): Kalshi sports, 55,637 markets, calibration slopes 0.90–1.10 in the time-to-resolution bins from 0–1 h to 24–48 h, and 1.74 for 1 month or more (Table 4) ([arXiv 2602.19520 HTML](https://arxiv.org/html/2602.19520)). Diercks, Katz & Wright (FEDS working paper) treat the YES price as a risk-neutral probability ([FEDS 2026-010](https://www.federalreserve.gov/econres/feds/files/2026010pap.pdf)).

**Terms (the main blocker; not legal advice)**
- Using the API binds the user to the Kalshi Developer Agreement ([docs home](https://docs.kalshi.com)). The only readable version is **v1.1** (S3 copy, last modified 2023-11-09) ([PDF](https://kalshi-public-docs.s3.amazonaws.com/Kalshi-Developer-Agreement.pdf)):
  - §3: use is "expressly limited to facilitating a members own trading on the Exchange";
  - §3.1 prohibits "Collecting, caching, aggregating, or storing data … except for purposes of facilitating your own trading";
  - §4.1.1: users must be Members;
  - New York law governs.
- Kalshi Data Terms of Use (S3 copy, last modified 2024-09-11): personal non-commercial use only; scraping and compiling databases prohibited; "use of any Kalshi Data … for any machine learning and/or artificial intelligence … is expressly prohibited" ([PDF](https://kalshi-public-docs.s3.amazonaws.com/kalshi-data-terms-of-service.pdf)).
- The live agreement at [kalshi.com/developer-agreement](https://kalshi.com/developer-agreement) returned HTTP 429 behind a bot checkpoint, so whether a newer version differs is **unverified**.
- Academic precedent is not permission: Bürgi et al. "registered with Kalshi" for API access ([paper](https://www.karlwhelan.com/Papers/Kalshi.pdf)), and Diercks et al. write "We begin by scraping trade-level data from Kalshi" ([FEDS 2026-010](https://www.federalreserve.gov/econres/feds/files/2026010pap.pdf), Methodology).
- Alternatives:
  - (a) email Kalshi for written permission (scope: MSU and Big Ten NCAAM markets, private research, no redistribution);
  - (b) Dune's curated Kalshi tables, hourly, "partner data"; licence and cost **unverified** ([Dune](https://docs.dune.com/data-catalog/curated/prediction-markets/kalshi/overview));
  - (c) drop Kalshi.
- A proposed CFTC rule (RIN 3038-AF73) would require DCMs to publish time and sales for event contracts ([NPRM](https://www.cftc.gov/media/14276/EventContractsReportingNPRM062526/download)). If adopted, it could create a public tape with different terms.
- **Design rule:** the Kalshi module ships disabled (`enabled: false` in config) until Aldemir records a decision.

### 1.6 Polymarket (Gamma, CLOB, Data API v2); Polymarket US optional

**Hosts and auth** ([API overview](https://docs.polymarket.com/getting-started/api.md), [CLOB OpenAPI](https://docs.polymarket.com/api-spec/clob-openapi.yaml), [Data v2 OpenAPI](https://data-api.polymarket.com/v2/openapi.json))
- Gamma `https://gamma-api.polymarket.com`: discovery and metadata, no auth.
- CLOB `https://clob.polymarket.com`: every read route is `security: []`. Order, cancel, API-key, balance and notification routes require L2 HMAC headers.
- Data API `https://data-api.polymarket.com`: v2 says "Auth: none. All data routes are public." **Data API v1 retires on 2026-10-24** ([migration](https://docs.polymarket.com/migrate/data-api-v1-to-v2.md)). `docs/research/odds_markets_research.md` cites the v1 `/trades` route; use `/v2/trades`.

**Endpoints we need**

| Purpose | Endpoint | Notes |
|---|---|---|
| Discovery | Gamma `GET /events/keyset?series_id=10470&start_time_min=&start_time_max=&limit=100` | Cursor `after_cursor`; `offset` returns 422. The legacy offset `/events` and `/markets` "will be deprecated" ([keyset events](https://docs.polymarket.com/api-reference/events/list-events-keyset-pagination.md), [discover markets](https://docs.polymarket.com/market-data/discover-markets.md), [changelog](https://docs.polymarket.com/changelog/predictions.md)) |
| One game | Gamma `GET /events/slug/{slug}` | ([event by slug](https://docs.polymarket.com/api-reference/events/get-event-by-slug.md)) |
| Companion events (1H, props, more markets) | Gamma `GET /events/keyset?game_id={gameId}` | Same `gameId` across companions ([discover markets](https://docs.polymarket.com/market-data/discover-markets.md)) |
| Markets | Gamma `GET /markets/keyset` (limit ≤ 100) | `closed=any` needs an identifier filter ([keyset markets](https://docs.polymarket.com/api-reference/markets/list-markets-keyset-pagination.md)) |
| Teams, sports, series | Gamma `/teams?league=cbb`, `/sports`, `/sports/market-types`, `/series` | ([teams](https://docs.polymarket.com/api-reference/sports/list-teams.md), [sports](https://docs.polymarket.com/api-reference/sports/get-sports-metadata-information.md), [market types](https://docs.polymarket.com/api-reference/sports/get-valid-sports-market-types.md), [series](https://docs.polymarket.com/api-reference/series/list-series.md)) |
| Price history (replaces the CLOB-hosted route since 2026-09-04) | Data `GET /v2/prices-history?token_id=&start=&end=&bucket_seconds=60` | ([token price history](https://docs.polymarket.com/api-reference/markets/get-a-tokens-price-history.md), [guide](https://docs.polymarket.com/market-data/prices-order-books.md), [changelog, Sep 4 2026 entry](https://docs.polymarket.com/changelog/predictions.md)) |
| Price history (legacy) | CLOB `GET /prices-history?market=&startTs=&endTs=&fidelity=1`; `POST /batch-prices-history` (≤ 20 ids) | ([prices history](https://docs.polymarket.com/api-reference/markets/get-prices-history.md), [batch](https://docs.polymarket.com/api-reference/markets/get-batch-prices-history.md)) |
| Live book | CLOB `GET /book`, `/midpoint`, `/spread`, `/last-trade-price`; batch `POST /books`, `/midpoints`, `/spreads`, `/last-trades-prices` (≤ 500 tokens) | ([order book](https://docs.polymarket.com/api-reference/market-data/get-order-book.md), [CLOB OpenAPI](https://docs.polymarket.com/api-spec/clob-openapi.yaml)) |
| Trades, tokens, resolutions | Data `GET /v2/trades`, `/v2/tokens`, `/v2/resolutions`, `/v2/oi`, `/v2/live-volume`, `/v2/status` | ([Data v2 OpenAPI](https://data-api.polymarket.com/v2/openapi.json), [trades](https://docs.polymarket.com/api-reference/feeds/list-trades.md)) |
| Live stream (optional) | `wss://ws-subscriptions-clob.polymarket.com/ws/market` (public; client sends PING every 10 s) | ([market WS](https://docs.polymarket.com/api-reference/wss/market.md)) |

**Price-history retention (the key constraint)** ([token price history](https://docs.polymarket.com/api-reference/markets/get-a-tokens-price-history.md))
- On `/v2/prices-history`, 3 h and 12 h series are permanent (back to 2022-11-18).
- **1-minute data is kept for at least 7 days, 5-minute for at least 60 and 30-minute for at least 90.** These are floors, not exact horizons.
- Explicit windows cap at 15 days. A sent `bucket_seconds` over an expired window returns an empty page, not a coarser substitute.
- Responses page at ≤ 10,000 points with `next_cursor`. They end with a terminal point, and a resolved market gets a settlement point. "Nothing may assume uniform spacing."
- The CLOB route has no documented retention **(unverified)**. An earlier repo probe got 6,002 one-minute points for an MSU game passing `startTs`/`endTs`, while `interval=all` returned empty (`docs/research/odds_markets_research.md`). Treat CLOB history as a fallback and record coverage per request.
- The page says coverage is "measured per request, never assumed from a table" and that "a 60-second width over days is the one shape that is both slow and, past 7 days, empty". It does not state the reference point explicitly; this design assumes retention is counted back from the **request time** (inference), so a 60 s request whose window *starts* more than 7 d before the request can come back entirely empty, not just short at the start.
- **Design consequence:** 1-minute prices must be captured live, or backfilled while the 60 s window's start is less than 7 days old (section 2.4).

**Rate limits** (Cloudflare, per IP, sliding windows; excess is throttled rather than rejected) ([rate limits](https://docs.polymarket.com/api-reference/rate-limits.md))
- Gamma `/events` 500 req/10 s and `/markets` 300 req/10 s.
- CLOB `/prices-history` 1,000 req/10 s and `/book` 1,500 req/10 s.
- Data `/v2/prices-history` 200 req/10 s; all `/v2` routes 800 req/10 s.
- The rate-limits page describes throttling, not rejection, and does not mention 429 or `Retry-After`. The Data API v2 OpenAPI does: "`429` with `Retry-After` is the busy signal for heavy queries", bursts past a per-client allowance "get the same `429`", and a retryable `503` also carries `Retry-After` ([Data v2 OpenAPI](https://data-api.polymarket.com/v2/openapi.json)). The token-price-history page likewise lists a per-client 429 with `Retry-After` ([token price history](https://docs.polymarket.com/api-reference/markets/get-a-tokens-price-history.md)).
- Design: 1 request/s, honouring `Retry-After` on 429 and 503.

**Game market shape** [probed: [MSU–Kentucky 2025-11-18](https://gamma-api.polymarket.com/events/slug/cbb-uk-mst-2025-11-18)]
- 7 markets: 1 moneyline, 3 spreads, 3 totals. `gameId` 71052, series 10470 `ncaa-cbb`, `teams[]` with `ordering` home/away and `providerId`, `startTime`, `score` ("66-83", away-home), `clobTokenIds` per market.
- **`line` is unsigned**; take the sign from the slug (`spread-away-5pt5`) and the question text.
- Several lines exist per game; store them all, and tag the main line via `spreadsMainLine`/`totalsMainLine` when present.
- `version: v1` uses `clobTokenIds`; v2 markets use `positionIds` ([prices & order books guide](https://docs.polymarket.com/market-data/prices-order-books.md)).
- Listed about 6.4 days before tip. `clearBookOnStart: true`: the book is cleared at tip-off ([markets & events](https://docs.polymarket.com/concepts/markets-events.md)).
- `secondsDelay: 3`, whose meaning is inferred **(unverified)**.
- Volume (n = 1 game probed: cbb-uk-mst-2025-11-18): moneyline about $50K ($49,568); spreads $19–86K ($86,357 on 5.5, the main line; $24,542 on 4.5; $18,818 on 3.5); totals about $1–3K per line ($1,094–$2,798) [probed]. Not a general property until more games are sampled.
- The neutral-site game was labelled with MSU as `home`, unlike ESPN.
- The displayed price is the midpoint, or the last trade if the spread exceeds $0.10 ([prices & orderbook](https://docs.polymarket.com/concepts/prices-orderbook.md)).
- Fees: taker fee = C × feeRate × p × (1−p), sports feeRate 0.05. NCAAB taker fees began 2026-02-18, and the sports rate rose from 0.03 to 0.05 on 2026-07-10 ([fees](https://docs.polymarket.com/trading/fees.md), [changelog](https://docs.polymarket.com/changelog/predictions.md)). These dates are structural breaks for spread and microstructure series.

**No ESPN ID anywhere.** The provider behind `gameId` and `providerId` is not documented **(unverified)**. Polymarket US exposes `event_external_id_sportradar` and says "Do not parse the instrument symbol or slug" ([sports schema](https://docs.polymarket.us/trader-guide/sports-schema.md)).

**History:** CBB game markets exist from 2025-26 only (earlier repo probe, `docs/research/odds_markets_research.md`).
- Free trade-level backfill for 2025-26: the Polymarket-v1 database (on-chain fills, 2022-11-21 to 2026-04-28; 483,663 sports markets in Table 4, which uses the Standard Binary sub-sample; the paper's limitations section says Sports is excluded from that table, contradicting its own Table 4) ([arXiv 2606.04217](https://arxiv.org/html/2606.04217v1)). Dataset licence: CC-BY-4.0 (HF card: "Released under CC-BY-4.0") ([HF card](https://huggingface.co/datasets/TimeSeventeen/Polymarket-v1)). The arXiv paper itself is CC BY-SA 4.0 and states no separate dataset licence ([arXiv abs](https://arxiv.org/abs/2606.04217)). Record "CC-BY-4.0 (HF card); attribution required" in LICENSES.md if adopted.

**Terms (not legal advice)**
- Polymarket.com Terms (effective 2026-08-11) ([tos](https://polymarket.com/tos); [text](https://docs.google.com/document/d/1N4aYlRcqaWCeKMID7vUSWJ1UPMvw_v6SP4cOFN8ZxR4)):
  - prohibit using "data mining tools, robots, crawlers…" to scrape the Site or other Interfaces, and harvesting "for any unauthorized purpose";
  - bar Capital Market Clients and data distributors from using the Data without agreement;
  - grant a personal, revocable licence;
  - Panama law.
- Polymarket US terms (effective 2025-09-25): market data for "personal, non-commercial use"; "Redistribution, resale, scraping, bulk downloads … are prohibited unless expressly licensed"; bots only through authorized APIs ([US terms](https://docs.google.com/document/u/1/d/e/2PACX-1vQ-86JK7kI6jAkpUNEyTCSpkeP_7cZMKhAW0rtti9rjzXqhdqm-27YSrX9Bun8LjQ/pub)).
- Our pattern (one researcher, documented public APIs, polite rates, private storage, no redistribution, derived statistics only) is the lowest-risk use, but it is **not explicitly licensed**.
- **Proposal:** use the international Gamma/CLOB/Data APIs. Keep Polymarket US off by default.

**Polymarket US (optional, off by default):** public gateway `https://gateway.polymarket.us`, no key ([intro](https://docs.polymarket.us/api-reference/introduction.md)). `GET /v1/price-history` returns `longPrice`/`shortPrice` display prices; mid ≈ (longPrice + 1 − shortPrice)/2. Fixed 1-minute profiles cover only the last 1 h or 6 h, or live from T−15 min ([price history](https://docs.polymarket.us/api-reference/price-history/get-price-history.md)). Public price-history: "20 requests/second/IP public limit"; "Cache identical responses for at least 30 seconds" ([price history](https://docs.polymarket.us/api-reference/price-history/get-price-history.md)). The rate-limits page gives 25 req/s as "the Retail API general limit" (authenticated) and states no public limit ([rate limits](https://docs.polymarket.us/api-reference/rate-limits.md)). The two numbers cover different scopes; design to 20 req/s or lower (in practice ≤ 1 req/s, as elsewhere). There is no public trade tape ([market data](https://docs.polymarket.us/trader-guide/market-data.md)).

**Interpretation evidence**
- Le (2026), preprint: Polymarket sports, 31,636 markets, are "near-calibrated", with a mean slope of 1.06 across the bins from 3–6 h to 1 month+ ([arXiv 2602.19520 HTML](https://arxiv.org/html/2602.19520)).
- Cheng, Yang & Zou (2026), preprint, 173 NBA games: single-market arbitrage is rare (7 in-game episodes, median 3.6 s) ([arXiv 2605.00864](https://arxiv.org/abs/2605.00864)).
- Dubach (2026), preprint: sports median effective half-spread 0.0075 probability points (n = 142 sports markets, Table 2); the author built the order-book data by recording the public market WebSocket into one Parquet file per UTC hour ([arXiv 2604.24366](https://arxiv.org/html/2604.24366v1)). Whether Polymarket offers any historical order-book endpoint was not confirmed from Polymarket's docs **(unverified)**; this design assumes it does not and captures books live (section 2.4).
- An SSRN paper reportedly finds sports accuracy comparable to bookmakers, but it could not be opened **(unverified)** ([SSRN 7552098](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7552098)).

### 1.7 Cross-venue sanity check already observed

MSU–Kentucky at tip (2025-11-18T23:30Z):
- ESPN BET close UK −175 / MSU +150 (event 401827221) gives MSU fair 0.380–0.386 depending on method.
- Kalshi mids normalise to UK 0.628 (MSU about 0.372).
- Polymarket's MSU token printed 0.375.
- The three venues agree within about 1.5 percentage points [probed + computed; [Kalshi event](https://api.elections.kalshi.com/trade-api/v2/events/KXNCAAMBGAME-25NOV18MSUUK), [CLOB prices-history](https://clob.polymarket.com/prices-history)].

---

## 2. Snapshot schedule

Notation: T = scheduled tip-off (UTC) from the ESPN schedule (under decision 2 option (iii), from CBBD `/games` `startDate`, cross-checked against the hoopR prebuilt schedule files; section 0). "Every MSU and Big Ten game" means every game with MSU or at least one Big Ten member of that season.
- Measured 2025-26 counts: 424 games, 199 with both teams Big Ten, 35 MSU games, 369 distinct tip times ([ESPN scoreboard, groups=7](https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard)) [probed; `count.py`].
- Peak month in 2025-26: November, with 132 games on 27 game days.

### 2.1 Game discovery (all sources)

| Source | Discovery call | Cadence |
|---|---|---|
| ESPN schedule (target list and tip times) | `/scoreboard?dates=YYYYMMDD&groups=7` and `/teams/127/schedule` | Daily 10:00 UTC; hourly on game days to catch tip-time changes. Needs decision 2 option (i) or (ii); under (iii) the target list and tip times come from the CBBD row below plus the hoopR prebuilt `mbb_schedule_{season}` file (section 0) |
| The Odds API (if bought) | `/events` (free) | Hourly |
| Kalshi (if approved) | `/events?series_ticker=KXNCAAMBGAME` (+ spread, total, 1H series) with nested markets; `/series?min_updated_ts=` for new series | Every 6 h (21,600 s) |
| Polymarket | `/events/keyset?series_id=10470&start_time_min=now−1 d&start_time_max=now+8 d`, then `?game_id=` for companions | Daily 10:00 UTC (06:00 EDT / 05:00 EST; kept in UTC so it does not move with DST); hourly on game days |
| CBBD | `/games` + `/lines?season=&conference=B1G` with a date window | Daily (under decision 2 option (iii), `/games` is the schedule source and its `sourceId` is the ESPN event ID) |

### 2.2 Pre-game snapshots (every MSU and Big Ten game)

| Label | Time | ESPN core odds* | The Odds API** | Kalshi*** | Polymarket |
|---|---|---|---|---|---|
| `open` | First observation after a market appears; label `open_first_seen` when it is our own first sighting | Also store the book's `open` block | `/odds?eventIds=` on first sight; plus 4 league sweeps per day (every 21,600 s) | First candle after `open_time` | First non-empty point after `acceptingOrdersTimestamp` |
| `t-24h` | T − 86,400 s | `/odds` | `/odds?eventIds=<all ids at that tip time>` (one call per tip time) | Orderbook (depth 10) + markets snapshot | `/books` + `/midpoints` batch |
| `t-1h` | T − 3,600 s | same | same | same | same |
| `close` | T − 600 s, T − 300 s, T − 60 s; keep the last valid one before the actual tip (defined below) | same; after the game also store the book's `close` block | same; must run before `commence_time` | same; close = last 1-min candle ending at or before tip | same; close = last observation strictly before `gameStartTime` (book clears at start) |

**Actual tip** (`actual_tip_utc`, seconds UTC): the earlier of (a) the `wallclock` of the first play-by-play event of the game (ESPN PBP `wallclock`; the same column exists in the hoopR prebuilt PBP files ([load_mbb.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/load_mbb.R))) and (b) the first fetch time at which the hourly or close jobs saw `competitions[0].status.type.name` change from `STATUS_SCHEDULED` to `STATUS_IN_PROGRESS` on the site scoreboard ([probed field shape](https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=20260327)). (b) is an upper bound with a resolution equal to the polling interval. If neither is available (decision 2 option (iii)), use the scheduled T and flag `tip_is_scheduled`. The probe showed only a completed game (`name` "STATUS_FINAL", `state` "post"); the names `STATUS_SCHEDULED`/`STATUS_IN_PROGRESS` (and `state` "pre"/"in") are **unverified; confirm on a live game**. Implement (b) as "first fetch where `status.type.state` is no longer the pre-game value".

\* Only if Aldemir approves automated ESPN reads (section 7). ESPN's 900 s edge cache means a T−60 s read can show a value up to 900 s old ([probed headers](https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/401825481/competitions/401825481/odds)), so the ESPN `close` block pulled after the game is the preferred ESPN close.
\** Only if the plan is bought. One `eventIds=` call per tip time costs the same whatever the number of events ([v4 guide](https://the-odds-api.com/liveapi/guides/v4/)).
\*** Only if the terms question is resolved.

CBBD: refresh daily for completed games. Its values carry no timestamps, so they enter the table with `snapshot_label = close_reported` (or `open_reported` for `spreadOpen`/`overUnderOpen`) and `source_time_utc = null`.

Tip times slip: re-plan the T-relative jobs whenever the hourly discovery shows a changed tip. Polymarket `startTime` differed from ESPN by ≈ 600 s on one game [probed; [Polymarket MSU–UConn](https://gamma-api.polymarket.com/events?slug=cbb-mst-uconn-2026-03-27), [ESPN scoreboard 2026-03-27](https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=20260327)].

### 2.3 Game-day first-half lines and player props (MSU and Big Ten games)

| Source | Call | Times |
|---|---|---|
| The Odds API (if bought) | `/events/{id}/odds?markets=h2h_h1,spreads_h1,totals_h1,player_points,player_rebounds,player_assists,player_threes,player_points_rebounds_assists` (only returned markets are charged); optional `/events/{id}/markets` check (1 credit) | 15:00 UTC on game day, T − 3,600 s, close |
| Kalshi (if approved) | 1H series events and markets (`KXNCAAMB1H*`, tickers **unverified in Job B1**) | Same times |
| Polymarket | Companion events via `game_id` (`sportsMarketType` such as `first_half_totals`) | Same times. Regular-season 1H presence is **unverified**; the 2026 tournament reward schedule names 1H markets ([changelog](https://docs.polymarket.com/changelog/predictions.md)) |
| ESPN (if approved) | `…/odds/{providerId}/propBets` | Same times. Pre-game availability **unverified** |

The Odds API notes that more market keys appear closer to tip, so 1H and props are pulled only on game day ([v4 guide](https://the-odds-api.com/liveapi/guides/v4/)).

### 2.4 In-game 1-minute prediction-market prices (every MSU game)

Window (prediction markets and ESPN): T − 10,800 s to final + 1,800 s (about 330 one-minute polls). The Odds API in-play window is shorter: tip to final, about 7,800 s (130 polls), because `/odds` serves in-play prices only after `commence_time` and the pre-tip minutes are already covered by the section 2.2 snapshots ([v4 guide](https://the-odds-api.com/liveapi/guides/v4/)).

| Source | Live capture | Post-game backfill |
|---|---|---|
| Polymarket | Every 60 s: CLOB `POST /midpoints` and `POST /books` for all tokens of the game's events (ML, all spread and total lines, companions). Optional: market WebSocket with 1-minute OHLC of mid, bid, ask and last built locally Two requests per token, because markets are listed about 6.4 d before tip (section 1.6), so a 60 s request from listing would start ≈ 7.4 d before a T + 1 d request and could come back entirely empty: (a) `/v2/prices-history?bucket_seconds=60` over [T − 10,800 s, final + 3,600 s] only, at T + 1 d, retry T + 3 d, **hard deadline 6 d after that window's start** (i.e. T + 6 d − 10,800 s; the 1-minute floor is ≥ 7 d, assumed counted from request time, section 1.6); (b) `bucket_seconds=300` (≥ 60 d retention) from listing to T − 10,800 s, any time within 60 d. Optional, preferred when the host allows: a live `/midpoints` snapshot every 300 s from T − 86,400 s to T − 10,800 s, so the pre-game path does not depend on retention at all. Cross-check with CLOB `prices-history?fidelity=1`. Then `/v2/trades` (identity fields stripped, section 3.1) and `/v2/tokens` for settlement |
| Kalshi (if approved) | Every 60 s: batch candlesticks `period_interval=1` for the game's tickers (≤ 100 per call), plus orderbook depth 10 for the two winner markets and the main spread and total strikes (about 6 markets). That is about 7 requests/min, well under the 1 request/s cap | After settlement, two passes, because game markets open days before tip (2026-27 markets were listed on 2026-10-14 for games on 1–2 Nov, ≈ 18 d ahead [probed], section 1.5): (a) `period_interval=1` over [T − 10,800 s, settlement]: about 22 markets × 330 candles ≈ 7,300 candles, one batch call under the 10,000-candle cap; (b) `period_interval=60` from market open to T − 10,800 s: about 22 × 18 d × 24 ≈ 9,500 candles, near the cap, so split the tickers into two batch calls (strike counts and listing lead **unverified** per game) ([batch](https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks.md)) |
| ESPN Live Odds providers (if approved) | Core `/odds` every 900 s (the edge-cache age); store under `market_phase = live` | none (live values are overwritten) |
| The Odds API (option C only) | `/odds?eventIds=` every 60 s from tip to final (≈ 7,800 s, 130 polls), featured, 1 region | n/a |

Big Ten (non-MSU) games: in-game capture is optional and off by default. Polymarket post-game backfills at 5-minute resolution (≥ 60 d retention) are cheap and can run for every Big Ten game.

### 2.5 Historical backfills (one-off)

| Source | Scope | Calls / cost |
|---|---|---|
| CBBD | `season=2022…2026&conference=B1G`, `/games` + `/lines` | 10 calls |
| ESPN (if approved) | Core `/odds` for every MSU and Big Ten game 2021-22 to 2025-26; teamrankings movement for 2021-22 and 2022-23 | About 2,000 calls at ≤ 1 req/s |
| SBRO (if approved) | One fetch of the 2021-22 page | 1 request |
| Kalshi (if approved) | `/historical/markets?series_ticker=` for game, spread, total and 1H series, then candles (60-min for all, 1-min for MSU) and `/historical/trades` for MSU | Low thousands of calls at ≤ 1 req/s |
| Polymarket | 2025-26: 3 h/12 h bars (permanent), a CLOB `fidelity=1` attempt per MSU token with recorded coverage, and optionally the Polymarket-v1 trade tape (licence decision) | Hundreds of calls |
| The Odds API (if bought) | Section 7.2 | 83K–500K credits |

### 2.6 Where the scheduler runs

| Option | 1-min in-game? | Evidence |
|---|---|---|
| Google Colab | No | At most 12 h per session, idle timeouts, interactive priority ([Colab FAQ](https://research.google.com/colaboratory/faq.html)) |
| GitHub Actions `schedule` | No | Minimum 5 min; can be delayed or dropped; disabled after 60 days of inactivity in public repos ([GitHub docs](https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule)) |
| APScheduler 3.11.3 process (MIT; 4.x still alpha) | Yes | `cron`, `interval` and `date` triggers; persistent job store; `misfire_grace_time`, `coalesce`, `max_instances`; `timezone=UTC` ([PyPI](https://pypi.org/project/APScheduler/), [user guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html)) |
| macOS launchd on an always-on Mac | Yes, as supervisor | Missed `StartCalendarInterval` jobs run on wake, but not if the machine was off ([Apple](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html)) |
| Small cloud VM | Yes | Example: DigitalOcean Basic droplet, 1 vCPU / 1 GiB / 25 GiB SSD $6.00/mo, or 1 vCPU / 2 GiB / 50 GiB SSD $12.00/mo ([DigitalOcean droplet pricing](https://www.digitalocean.com/pricing/droplets), opened 2026-10-18). Other providers not compared |

**Proposal:** one APScheduler `BlockingScheduler` process, kept alive by launchd with `KeepAlive` on an always-on Mac with sleep disabled in season. The daily planner job turns the ESPN schedule into per-game `date` jobs (open checks, t-24h, t-1h, close ×3, game-day 1H/props, in-game interval jobs, post-game backfills), each with explicit job IDs and `replace_existing=True`.

---

## 3. Storage

### 3.1 Raw response first

Every request is written to the raw store **before** any parsing. Bodies are never modified. This is the "bronze" layer pattern: source data as-is plus load metadata, so later layers can be rebuilt without re-fetching ([Databricks medallion](https://www.databricks.com/glossary/medallion-architecture)).

- Path: `MyDrive/MSU-Alpha-3/markets/raw/{source}/{endpoint_slug}/{YYYY}/{MM}/{DD}/{fetched_at_utc_iso}_{sha256[:12]}.json.gz` (or `.html.gz` for SBRO).
- Manifest: one JSON line per response in `raw/{source}/manifest/{YYYY-MM-DD}.jsonl`, with:
  - `fetched_at_utc` (microseconds), `source`, `method`, `endpoint`;
  - the full URL with query, **with any `apiKey` or credential removed**;
  - request body for POST reads (Polymarket batch routes);
  - HTTP status and response headers, including `X-CallLimit-Remaining` (CBBD), `x-requests-remaining/used/last` (The Odds API), `cache-control` (ESPN, Kalshi) and `Retry-After`;
  - `sha256` and byte length of the body, `collector_version`, `run_id`, `job_id`.
- An optional WARC export (ISO 28500) via `warcio` (Apache-2.0) is possible later ([LoC WARC](https://www.loc.gov/preservation/digital/formats/fdd/fdd000236.shtml), [warcio](https://github.com/webrecorder/warcio)). Not needed for v1.
- **Privacy exception (decision for Aldemir):** Polymarket `/v2/trades` rows carry `proxy_wallet`, `name`, `pseudonym`, `bio` and `profile_image` of private individuals ([Data v2 OpenAPI](https://data-api.polymarket.com/v2/openapi.json)). The same applies to the maker/taker addresses in the Polymarket-v1 tape. These have no research value for game benchmarks. Proposal: strip or hash them before the raw write, and record in the manifest that the body was redacted, with the list of removed fields. This is the only permitted departure from "exact body".
- Retention: keep forever. The Odds API and CBBD terms allow private indefinite storage ([Odds API terms](https://the-odds-api.com/terms-and-conditions.html), [CBBD terms](https://collegebasketballdata.com/terms)). Never commit raw responses to git, and never share them.

### 3.2 Parsed snapshot table

Location: `MyDrive/MSU-Alpha-3/markets/snapshots/`, as a Parquet dataset with hive partitions `source=…/season=…/month=…`. Arrow advice: files of about 20 MB–2 GB, fewer than about 10,000 partitions, and a unique `basename_template` (include `run_id`) per write so `part-0.parquet` is never overwritten ([Arrow datasets](https://arrow.apache.org/docs/python/dataset.html)). Timestamps are `TIMESTAMP(MICROS)` with `isAdjustedToUTC = true` ([Parquet logical types](https://parquet.apache.org/docs/file-format/types/logicaltypes/)). Drive sync is slow on many small files **(unverified)**, so write daily batches locally and sync once.

One row = one priced outcome of one market of one book or exchange at one snapshot.

| Column | Type | Required by Job B | Notes |
|---|---|---|---|
| `game_id` | string | yes | **ESPN event ID, the one join key** (e.g. "401825481") |
| `source` | dictionary string | | `cbbd`, `espn`, `sbro`, `oddsapi`, `kalshi`, `polymarket`, `polymarket_us` |
| `book` | dictionary string | yes ("book or exchange") | Sportsbook key, ESPN `provider_id` + name, or `kalshi`/`polymarket`. Provider type (book / consensus / model / exchange / live) lives in a `providers` dimension table |
| `market` | dictionary string | yes | `moneyline`, `spread`, `total`, `moneyline_1h`, `spread_1h`, `total_1h`, `team_total`, `prop_points`, `prop_rebounds`, `prop_assists`, `prop_threes`, `prop_pra`, … |
| `market_phase` | string | | `pregame` / `live` |
| `side` | string | yes | `team` (with `team_id`), `over`, `under`, `yes`, `no` |
| `team_id` | string, nullable | | ESPN team ID. Spreads and moneylines are stored **per team, never as home/away** |
| `player_id` | string, nullable | | ESPN athlete ID for props |
| `line` | decimal(5,1), nullable | yes | Signed from this team's point of view (−2.5 = gives 2.5) |
| `line_is_integer` | bool | | Push possible. Fair probability is then conditional on no push |
| `price_american` | int32, nullable | yes | As received. Exchange rows: derived from probability (p ≥ 0.5 → −100p/(1−p); else +100(1−p)/p) |
| `price_decimal` | float64, nullable | yes | Computed from American when available: d = 1 + A/100 (A > 0) or 1 + 100/\|A\| (A < 0). Keep the source's decimal in `price_decimal_source` when it also sends one |
| `implied_prob` | float64 | yes | 1/d for books. For exchanges, the mid (bid + ask)/2 |
| `booksum` | float64 | | Σ implied over the complementary outcomes of that (game, book, market, line, snapshot) |
| `fair_prob_power` | float64, nullable | yes | Section 3.3 |
| `fair_prob_shin` | float64, nullable | yes | Section 3.3. Equal to additive for two-way markets |
| `fair_prob_mult` | float64, nullable | | Multiplicative baseline |
| `power_k`, `shin_z` | float64, nullable | | Method parameters |
| `bid`, `ask`, `last`, `bid_size`, `ask_size`, `volume`, `open_interest` | decimal / float64, nullable | | Exchanges |
| `snapshot_time_utc` | timestamp[us, UTC] | yes | Our fetch time; for historical pulls, the source's snapshot timestamp (Odds API `timestamp`, Kalshi `end_period_ts`, Polymarket `timestamp`) |
| `source_time_utc` | timestamp[us, UTC], nullable | | Source's own last-change time (Odds API market `last_update`, ESPN teamrankings `lineDate`); null when unknown (CBBD, ESPN open/close, SBRO) |
| `fetched_at_utc` | timestamp[us, UTC] | | From the manifest |
| `snapshot_label` | string | | `open`, `open_first_seen`, `open_reported`, `t-24h`, `t-1h`, `close`, `close_reported`, `gameday`, `sweep`, `inplay_1m`, `movement` |
| `observed_post_event` | bool | | True when the row describes a pre-game value but was fetched after the game (CBBD `open_reported`/`close_reported`, ESPN post-game `open`/`close` blocks). Used by C-13 |
| `source_event_id` | string | | CBBD `gameId`, Odds API `id`, Kalshi `event_ticker`, Polymarket event `id`/`gameId`, SBRO rotation pair |
| `season` | int16 | | Ending year |
| `dq_flags` | list<string> | | Rule IDs from section 4 |
| `raw_ref` | string | | sha256 of the raw body |
| `schema_version` | int16 | | |

Implied probability from American odds A: |A|/(|A| + 100) for A < 0; 100/(A + 100) for A > 0 ([Wikipedia: Odds](https://en.wikipedia.org/wiki/Odds)).
- Booksum π, overround π − 1, hold (π − 1)/π ([Wikipedia: Mathematics of bookmaking](https://en.wikipedia.org/wiki/Mathematics_of_bookmaking), [Matter of Stats](https://www.matterofstats.com/what-is-vig-and-overround)). Example: −110/−110 gives π = 1.0476, overround 4.76%, hold 4.55% [computed].
- Store the American integer as received and compute decimal from it. The Odds API notes that American odds before 2022-09-18 were computed from decimal "may contain rounding errors" ([v4 guide](https://the-odds-api.com/liveapi/guides/v4/)).

Supporting tables (same Drive folder, Parquet):
- `providers(source, provider_id, name, provider_type, valid_from)`;
- `team_xwalk` and `source_event_map` (section 5);
- `match_queue` (section 5.3);
- `quarantine(rule_id, row_json, raw_ref, first_seen_utc, resolved_by, resolved_utc, resolution)` (section 4.2);
- `games(game_id, scheduled_tip_utc, actual_tip_utc, tip_is_scheduled)` (actual tip as defined in section 2.2);
- `completeness_weekly` (section 4.3).

### 3.3 Margin removal (fair probability)

Notation: n outcomes, implied r_i = 1/o_i, π = Σ r_i. Goal: p_i with Σ p_i = 1.

| Method | Formula | Source |
|---|---|---|
| Power | p_i = r_i^k, with k chosen so Σ r_i^k = 1 (root-find k ∈ [1, 50]) | [Clarke 2016](https://ndownloader.figshare.com/files/47535482); [Clarke, Kovalchik & Ingram 2017](https://ndownloader.figshare.com/files/47662879) eq. (7) |
| Shin | p_i(z) = [√(z² + 4(1 − z)·r_i²/π) − z] / [2(1 − z)], with z ∈ [0, 1) chosen so Σ p_i = 1. Closed form for n = 2 | [`shin` source](https://raw.githubusercontent.com/mberk/shin/master/python/shin/__init__.py); CKI 2017 eqs. (4)–(6) |
| Multiplicative (baseline) | p_i = r_i/π | CKI 2017 eq. (2) |
| Additive | p_i = r_i − (π − 1)/n | CKI 2017 eq. (1) |

Facts that shape the design:
- **For two-way markets, Shin gives exactly the additive result** (CKI 2017 Appendix; [shin README](https://www.github.com/mberk/shin); [implied vignette](https://cran.r-project.org/web/packages/implied/vignettes/introduction.html)). Most of our markets are two-way, so keep both columns, but expect them to equal additive there.
- At symmetric prices (−110/−110) every method gives 0.500/0.500. The methods differ only on asymmetric prices: for UK −175 / MSU +150, UK gets 0.614 (multiplicative), 0.618 (additive/Shin) or 0.620 (power) [computed, `devig.py`].
- Evidence: differences between methods are small and dataset-dependent.
  - CKI 2017 Table 4 (peer-reviewed): on ATP tennis (14,925 two-way events) log loss was 0.548 for power, additive and Shin vs 0.550 for multiplicative. Rankings are not uniform: on greyhounds (20,206 races) multiplicative (1.692) beat Shin/additive (1.696) but not power (1.686); on gallops (4,663 races) additive/Shin (1.968) beat power (1.971), with multiplicative last (1.994) ([CKI 2017](https://ndownloader.figshare.com/files/47662879)).
  - Goto et al. 2026 (preprint): Bet365 football log loss 1.00334 (power) vs 1.00372 (multiplicative) (Table 1; the dataset has 90,014 matches across five bookmakers, 2012–2024, and the Bet365-only count is not stated) ([arXiv 2604.17194 HTML](https://arxiv.org/html/2604.17194)).
  - **No study compares the methods on NCAAB.** Run our own log-loss and Brier comparison on the 2021-22 to 2025-26 moneylines before choosing a default.
- Edge cases:
  - π ≤ 1 (exchange mids, stale books): power needs k ≤ 1 and Shin z ≤ 0. Solve on the widened bracket or fall back to multiplicative, set flag `booksum_le_1`, and always log π.
  - One-sided markets (some props): store implied only; fair = null.
  - Integer lines: fair = P(cover | no push).
- Exchanges: use the mid per outcome and normalise across the mutually exclusive outcomes. Also run power and Shin on the (YES_ask, NO_ask) pair for comparability with books; on a binary exchange the "overround" is the bid–ask spread (Polymarket notes, [prices & orderbook](https://docs.polymarket.com/concepts/prices-orderbook.md)). Polymarket `prices-history` returns `{t, p}` without saying whether p is a mid or a last trade, so flag it as indicative ([prices history](https://docs.polymarket.com/api-reference/markets/get-prices-history.md)).
- Solver: `scipy.optimize.brentq` on monotone 1-D brackets, tolerance 1e-12 on the sum [computed]. The published examples were reproduced: shin README [2.6, 2.4, 4.3] → [0.373, 0.405, 0.222], and the CKI 2017 Table 2 power and Shin columns.

---

## 4. Data checks

### 4.1 Cross-source comparison

**Requirement (Job B):** flag differences above 0.5 points between sources.

**Evidence that the single rule over-fires when books differ** [probed + computed, 98 MSU games 2021-22 to 2023-24, ESPN core odds, book providers only]:
- closing spreads across about 10 books differed by more than 0.5 points in 53–61% of games, and by more than 1.0 point in 13–23%;
- totals differed by more than 0.5 in 79–88% of games.
- Per-book mean deviation from the game median ranged from 0.09 (Titanbets) to 0.47 points (Unibet, with three stale-looking outliers such as −11.5 vs a median of −4.0).

**Design:**
- Always compute the 0.5-point flag (`xsrc_gt_0p5`), as required.
- Also apply the tiered rules below. These are a proposal pending Aldemir's approval.

Threshold values in this table are **initial values (before calibration)**.

| Rule ID | Comparison | Flag when (initial value) |
|---|---|---|
| XS-1 | Same book seen through two sources (e.g. DraftKings close in ESPN vs DraftKings in The Odds API at T − 300 s) | \|Δspread\| > 0.5 or \|Δtotal\| > 0.5 points, or \|Δfair p\| > 0.02 |
| XS-2 | One book vs the cross-book median, same source | \|Δspread\| > 1.5 or \|Δtotal\| > 2.0 points. Failing rows are excluded from the consensus |
| XS-3 | Consensus vs consensus across sources (e.g. CBBD median vs ESPN median, SBRO vs ESPN consensus) | > 1.0 point. The 0.5-point flag is also kept |
| XS-4 | Moneyline vs spread, same book | \|fair P(win) − Φ(S/10.9)\| > 0.06 (σ = 10.9 points from Wolfers 2006, 44,120 games ([PDF](https://www.stat.berkeley.edu/~aldous/157/Papers/PointShaving.pdf)); refit σ on our data first) |
| XS-5 | Exchange vs sportsbook, same timestamp | \|p_exchange,mid,norm − median p_book,fair\| > 0.05, or line-equivalent difference > 0.5 points |
| XS-6 | Polymarket internal | ML token prices sum to 1 ± spread; ML vs spread consistent within tolerance (single-market arbitrage is rare: [arXiv 2605.00864](https://arxiv.org/abs/2605.00864)) |

Thresholds are calibrated on 2021-22 to 2023-24 to a flag rate of about 5–10% of rows, then frozen in config. The 5–10% target is a project choice, not evidence. `config/markets.yaml` stores the calibrated values with the calibration date and the data window used; until calibration runs, the initial values above apply. CBBD-vs-ESPN agreement may only reflect a shared upstream (section 1.1).

### 4.2 Contracts (types and ranges)

Tooling: pandera (MIT) ([GitHub](https://github.com/unionai-oss/pandera)). Process: **fail closed**. A failing row goes to `quarantine` with its rule ID and is never dropped silently.

| Rule ID | Check |
|---|---|
| C-01 | `price_american` ∈ (−100000, −100] ∪ [100, 100000]; strings "EVEN"/"PK" parsed explicitly (their presence in ESPN is **unverified**) |
| C-02 | `price_decimal` > 1.0; `implied_prob` ∈ (0, 1) |
| C-03 | Booksum ∈ [0.98, 1.25] for books, [0.95, 1.10] for exchanges (outside → quarantine); additionally flag (not quarantine) `oddsapi` rows with booksum < 1.00 or > 1.15 |
| C-04 | Fair probabilities sum to 1 ± 1e-9 per (game, book, market, line, snapshot) |
| C-05 | Spread is a multiple of 0.5 within [−60, 60]; total is a multiple of 0.5 within [90, 200] (MSU totals observed about 129–150) |
| C-06 | The two sides of a spread sum to 0; Over and Under share one line |
| C-07 | ESPN `close.pointSpread` \|x\| ≤ 50, otherwise "price in point field" (2022-23 defect) |
| C-08 | Provider name contains "Live" → `market_phase = live`, never `close` |
| C-09 | CBBD spread null with `overUnder` present → `possible_pickem` |
| C-10 | SBRO tokens `pk`/`NL`/`NA`/blank/corrupted → quarantine (`pk` → line 0 after review) |
| C-11 | Exchange prices in [0, 1] and on the `price_ranges` step; bid ≤ ask; spread > 0.20 → `wide_spread` (Bürgi et al. drop contracts with a final spread > 20¢ ([paper](https://www.karlwhelan.com/Papers/Kalshi.pdf))); Polymarket spread > 0.10 → `display_is_last` |
| C-12 | Kalshi and Polymarket spread/total ladders monotone in the strike |
| C-13 | For `pregame` rows with `observed_post_event = false`: `snapshot_time_utc` ≤ actual tip. Rows reported after the game (CBBD `open_reported`/`close_reported`, the ESPN post-game `open`/`close` blocks) carry `observed_post_event = true`; for them C-13 checks `source_time_utc` ≤ tip when it is known and is skipped when the source gives no time. teamrankings `lineDate` ≥ tip dropped from pregame |
| C-14 | Uniqueness of (game_id, source, book, market, market_phase, snapshot_label, side, team_id/player_id, line, snapshot_time_utc). `snapshot_label` and `market_phase` are in the key because one ESPN response yields `open`, `close` and current rows (and live/pregame rows) with the same fetch time, and open == close on 90/353, 16/37 and 12/37 rows (section 1.2); likewise CBBD `spreadOpen` = `spread`. `store.py` uses the same dedup key |
| C-15 | Stale: Odds API `snapshot − market.last_update > 1,800 s` pre-game; exchange bid/ask unchanged and volume 0 for > 1,800 s pre-game; Polymarket gaps > 300 s in the last hour before tip |
| C-16 | Jumps between snapshots < 900 s apart: > 3 points spread, > 4 points total, > 0.15 probability. Flag `jump`; exclude only after a manual review recorded in `quarantine.resolved_by` |
| C-17 | Settlement agreement after the game: Kalshi `result` and Polymarket settlement match the ESPN final |

Sources: quality dimensions (accuracy, completeness, consistency) from [ISO/IEC 25012](https://iso25000.com/en/iso-25000-standards/iso-25012); The Odds API `last_update` semantics ([v4 guide](https://the-odds-api.com/liveapi/guides/v4/)); Kalshi candle fields ([candlesticks](https://docs.kalshi.com/api-reference/market/get-market-candlesticks.md)).

### 4.3 Completeness per week

- Week = Monday 00:00 to Sunday 23:59 US-Eastern. Denominator = scheduled games involving MSU or a Big Ten team, from the ESPN scoreboard ([probed](https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard)). Under decision 2 option (iii) the denominator comes from CBBD `/games` (Big Ten filter), cross-checked against the hoopR prebuilt `mbb_schedule_{season}` file (section 0).
- **Target: ≥ 95% of scheduled games** with at least one valid close, per source and market.
- Also report:
  - snapshot completeness (share of open, t-24h, t-1h and close present per game);
  - book completeness (books per game vs the expected list);
  - field completeness (non-null share per column);
  - match rate per source (section 5).
- Alerts: completeness < 95% for 2 consecutive weeks; any MSU game without a close from every source; an unmatched share > 2% for a source.
- Observed baseline: ESPN had odds on 98–99% of D-I games on sampled dates and 100% for MSU and the Big Ten [probed]. Polymarket and Kalshi coverage of minor games is **unverified**.
- Output: `completeness_weekly` table plus a one-line summary per week in the run record (`results/markets_<date>/`).

---

## 5. Matching each source's game to the ESPN game ID

### 5.1 Team crosswalk (static, versioned)

- `team_xwalk(espn_team_id, source, source_team_key, source_team_name, valid_from, valid_to, method, reviewed_by)`. MSU = 127; the ESPN team list has 362 teams ([probed teams](https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/127)).
- Seeds:
  - hoopR 3.1.0 `mbb_team_crosswalk()` (MIT; ESPN ↔ KenPom, Torvik and Fox names, with alias passes) ([reference](https://hoopr.sportsdataverse.org/reference/mbb_team_crosswalk.html), [CRAN](https://cran.r-project.org/web/packages/hoopR/index.html));
  - ncaahoopR `ids`/`dict` (MIT) ([GitHub](https://github.com/lbenz730/ncaahoopR));
  - CBBD team `sourceId` = ESPN team ID ([hoopR cbbd_teams.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/cbbd_teams.R)).
- Normalisation: lowercase, ASCII-fold, strip punctuation, alias map (`state`/`st.` → `st`, `&` → `and`), following hoopR's normalisers and cfbfastR's `norm_key` ([crosswalk_basketball.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/crosswalk_basketball.R), [cfbfastR](https://rdrr.io/cran/cfbfastR/man/load_cfb_teams_crosswalk.html)).
- Fuzzy fallback: RapidFuzz `WRatio` with the default processor (MIT) ([RapidFuzz](https://github.com/rapidfuzz/RapidFuzz)). Auto-accept only if score ≥ 95, the runner-up is ≥ 5 lower, and the team is D-I that season. **Never** auto-accept "State" vs non-"State" pairs (Michigan / Michigan St.) or ambiguous "St." names (St. John's / Saint Joseph's).
- Per-source keys:
  - The Odds API full names with mascot via `/participants` (1 credit per season) ([v4 guide](https://the-odds-api.com/liveapi/guides/v4/));
  - Kalshi `custom_strike.basketball_team` UUID + `yes_sub_title` (never ticker codes; "MSU" collides with other schools) [probed];
  - Polymarket `teams[].id`, `abbreviation`, `providerId` (e.g. "Connecticut Huskies" where ESPN has "UConn Huskies") [probed];
  - SBRO condensed names ("MichiganState", "VaCommonwealth"); hoopR's crosswalk does not include SBRO ([mbb_crosswalk.R](https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/mbb_crosswalk.R)).
- Hand-review every Big Ten team and every Big Ten opponent once per season.

### 5.2 Game matching per source

General rule:
- Map both teams to ESPN team IDs.
- Candidate ESPN games share the **unordered** team pair.
- Compare dates in **US-Eastern**: Kalshi ticker dates and Polymarket `eventDate` are Eastern, while the ESPN `date` is UTC (MSU–UConn: Kalshi `26MAR27`, Polymarket 2026-03-27, ESPN 2026-03-28T01:55Z) [probed].
- **Exactly one candidate → link; anything else → review queue.**
- Assign prices by team ID, never by home/away. Neutral-site home labels differ: for MSU–Kentucky, ESPN and Kalshi list Kentucky as home, but Polymarket lists MSU [probed].

| Source | Native keys | Method | Validation |
|---|---|---|---|
| ESPN | Event ID | Native (event ID = competition ID) | none needed |
| CBBD | `gameId` | `/lines.gameId` → `/games.id` → `sourceId` (verify it is the ESPN ID on the first keyed call) | Home/away ESPN team IDs equal; start time within ±129,600 s (36 h); null `sourceId` → queue |
| SBRO 2021-22 | Date (MMDD), rotation pair, condensed names | Eastern date ± 1 day + both team IDs; neutral (N/N) rows accept either orientation | Final score equals the ESPN final |
| The Odds API | 32-hex `id`, `commence_time`, team names, rotation numbers | Team pair + \|commence − ESPN tip\| ≤ 21,600 s (6 h); store `home_away_swapped` | Rotation numbers vs CBBD/SBRO; `/scores` vs ESPN final. Live vs historical ID stability **unverified**: store both |
| Kalshi | `event_ticker`, team UUIDs | Team pair + Eastern date from the event (title/sub_title date). `occurrence_datetime` is a placeholder | `result` vs ESPN winner |
| Polymarket | Event `id`, `gameId`, slug, `startTime`, `eventDate` | Team pair + \|startTime − ESPN tip\| ≤ 10,800 s (3 h), else Eastern date ± 1 day; `home_away_flipped` flag | `score` (away-home) equals the ESPN final; settlement agrees with winner, margin and total |

Order of the time rules (this replaces any reading of the per-source windows as auto-accept rules):
1. **Candidate search.** The per-source window in the table (CBBD ±129,600 s; The Odds API ≤ 21,600 s; Polymarket ≤ 10,800 s, or Eastern date ± 1 day when the source has no usable time; SBRO and Kalshi Eastern date ± 1 day) only selects candidate ESPN games with the same unordered team pair.
2. **Auto-accept** needs exactly one candidate **and** |Δt| ≤ 5,400 s (90 min) when both sides give a time, or the same Eastern date when one side has no time.
3. **Everything else** goes to `match_queue`: zero candidates → `no_candidate`; more than one → `multiple_candidates`; one candidate with |Δt| > 5,400 s, or a different Eastern date when one side lacks a time → `time_diff_gt_tolerance`.

Example: a Polymarket event 7,200 s from the ESPN tip is a candidate (≤ 10,800 s) but is not auto-accepted (> 5,400 s); it goes to the queue as `time_diff_gt_tolerance`. Polymarket differed by 600 s on one game [probed]. Conference-tournament rematches within days are resolved by the date window; if two candidates remain, the row goes to review. Under decision 2 option (iii), the ESPN-side game list and tip times come from CBBD `/games` (`sourceId` = ESPN event ID) instead of the ESPN schedule.

### 5.3 Mismatch review queue

- `match_queue(source, source_event_id, raw_ref, team_a_raw, team_b_raw, start_raw, candidates_json, reason, first_seen_utc, resolved_espn_game_id, resolved_by, resolved_utc)`.
- Reason codes (union of the source notes): `unknown_team_name` / `team_unmapped`, `no_espn_event` / `no_candidate`, `multiple_candidates`, `time_diff_gt_tolerance`, `espn_postponed_or_canceled`, `source_event_id_changed`, `null_source_id`, `score_mismatch`, `settlement_mismatch`.
- Resolutions write once to `source_event_map(source, source_event_id, espn_game_id, method, confidence, valid_from)`, so each source event is matched only once.
- Unmatched rows stay in the raw store and the snapshot table with `game_id = null` and flag `unmatched`. They are never dropped, and never joined until reviewed.
- Review UI for v1: a small CLI that prints each queue item with its candidates and writes the decision. The human-in-the-loop labelling system in `docs/requirements.md` can take this over later.

---

## 6. Legal and access

Not legal advice. Every point below is a design rule for the code and for its operation.

**Read-only by construction**
- No account, order, trading, portfolio, balance or wallet code anywhere in the repo. No trading credentials stored anywhere.
- The only secrets the collector may ever hold are **read** API keys: the CBBD key (free) and, if bought, The Odds API key. Both live in environment variables or a local secret store, never in git, and are stripped from every stored URL and log.
- A single HTTP client enforces an **allowlist of exact (host, method, path pattern)** pairs:
  - GET only, except the Polymarket CLOB batch reads `POST /batch-prices-history`, `/books`, `/midpoints`, `/spreads` and `/last-trades-prices`, which are listed explicitly;
  - it refuses any request carrying `POLY_*` headers;
  - it refuses an `Authorization` header except the CBBD bearer on the CBBD host.
- A unit test greps the package for forbidden paths and schemes: `/portfolio`, `/orders`, `/order`, `/account`, `/auth/`, `/balance-allowance`, `wss://external-api-ws.kalshi.com`, `api.polymarket.us`, `SecureClient`, `py_clob_client` (sources: [Kalshi docs index](https://docs.kalshi.com/llms.txt), [CLOB OpenAPI](https://docs.polymarket.com/api-spec/clob-openapi.yaml), [Polymarket US intro](https://docs.polymarket.us/api-reference/introduction.md), [Polymarket Python SDK](https://docs.polymarket.com/getting-started/python.md)).
- No order-capable SDK is a dependency. The unified `polymarket-client` ships `SecureClient` trading code alongside public reads ([PyPI](https://pypi.org/pypi/polymarket-client/json), [Python guide](https://docs.polymarket.com/getting-started/python.md)), so the collector uses plain HTTP instead.
- No VPN, proxy or geolocation workaround, ever. If an exchange starts geo-blocking public reads from Michigan, stop and ask Aldemir.

**Michigan status (as of 2026-10-18)**
- `docs/requirements.md` records that Michigan users currently cannot trade sports contracts on Kalshi, Robinhood, Polymarket US or Novig. Sources by platform: Kalshi (KalshiEx LLC) ([Spectrum News 2026-09-02](https://spectrumlocalnews.com/mi/michigan/news/2026/09/02/michigan-judge-blocks-kalshi); the article names only Kalshi); Robinhood ([MGCB release](https://content.govdelivery.com/accounts/MIGCB/bulletins/4293a85)); Polymarket US and Novig **(unverified; from `docs/requirements.md`, no primary source opened)**, consistent with the "Unverified" Polymarket US entry below.
- Kalshi: an Ingham County preliminary injunction, *Nessel v. KalshiEX LLC*, Case No. 26-1087-CZ, signed 2026-09-01 ([order PDF](https://www.michigan.gov/ag/-/media/Project/Websites/AG/releases/2026/September/Kalshi-Preliminary-Injunction-Order-Signed-Sep-1-2026.pdf)).
  - It enjoins offering, facilitating or advertising sports contracts to persons in Michigan, and "Permitting account creation, verification, funding, or maintenance by any person for the purpose of accessing, viewing, trading, or settling internet sports betting".
  - It requires MGCB-licensed geolocation, with a $500,000/day fine.
  - Earlier TRO: [Spectrum News 2026-06-30](https://spectrumlocalnews.com/mi/michigan/news/2026/06/30/michigan-blocks-sports-betting-kalshi), [Legal News](https://legalnews.com/Home/Articles?DataId=1630335).
  - Contempt motion filed 2026-09-29; hearing 2026-11-24 ([DeFi Rate](https://defirate.com/news/michigan-wants-kalshi-held-in-contempt-as-state-crackdown-moves-beyond-trading/)).
- Robinhood: stopped new Michigan sports contracts and was to close positions by 2026-10-09 ([MGCB release](https://content.govdelivery.com/accounts/MIGCB/bulletins/4293a85)).
- Federal context:
  - Sixth Circuit *Schuler/Orgel* (2026-09-25): sports contracts are not swaps; no preemption ([NatLawReview](https://natlawreview.com/article/sixth-circuit-deepens-circuit-split-kalshi-sports-event-contracts-are-not-swaps-and)).
  - E.D. Mich. denied Coinbase's preliminary injunction on 2026-08-06 ([The Block](https://theblock.co/news/regulation/2026-08-07-michigan-judge-denies-coinbase-bid-prediction-markets-411128)).
  - Third Circuit for Kalshi ([opinion](https://www2.ca3.uscourts.gov/opinarch/251922p.pdf)); Ninth Circuit against ([opinion](https://cdn.ca9.uscourts.gov/datastore/opinions/2026/08/28/25-7516.pdf)).
  - SCOTUS No. 26-299 pending, response due 2026-11-09 ([docket](https://www.supremecourt.gov/search.aspx?filename=/docket/docketfiles/html/public/26-299.html)).
  - CFTC NPRM of 2026-10-09 would define sports event contracts as swaps ([Release 9310-26](https://www.cftc.gov/PressRoom/PressReleases/9310-26); [Release 9309-26](https://www.cftc.gov/PressRoom/PressReleases/9309-26)).
  - Re-check all of these before each season.
- Polymarket US in Michigan: contested in secondary sources. [next.io](https://next.io/prediction-markets/polymarket/legal/) lists MI as excluded; [coinstats](https://coinstats.app/prediction-markets/legal/polymarket-mi/) reports no Michigan order and no published state list; [World Casino Directory](https://news.worldcasinodirectory.com/michigan-court-backs-state-authority-over-polymarket-sports-contracts-123238) reports the PI denial. **Unverified.**
- polymarket.com is close-only for US users on the frontend and API ([geoblock](https://docs.polymarket.com/api-reference/geoblock.md)). A read request from Michigan was served with HTTP 200 [probed].

**Reading public data is a separate activity.** The Michigan orders target offering, trading, advertising and account-based access. The research found no order addressing third parties reading public price data. The Kalshi injunction's "accessing, viewing, trading, or settling" clause concerns permitting account creation, verification, funding or maintenance; the collector creates no account and reads only unauthenticated endpoints, so the clause does not obviously apply (not legal advice). Re-check the clause, and any new order, after the 2026-11-24 contempt hearing. That does not by itself make reading lawful, and it is not a substitute for counsel.

**The binding constraints are the providers' own terms** (section 1):

| Source | Terms position | Design response |
|---|---|---|
| CBBD | Research and private archive explicitly allowed | Collect |
| The Odds API | Research, ML and indefinite storage explicitly allowed; no redistribution | Collect once bought; private only |
| ESPN | Personal non-commercial; automated extraction prohibited | Aldemir decides among options (i) schedule reads only, (ii) schedule + odds reads, (iii) no ESPN (section 0, decision 2); until then, no automated ESPN collection beyond what he approves, and the scheduler uses the option (iii) fallback (CBBD `/games` + hoopR prebuilt schedule files) |
| SBRO | All rights reserved; no reproduction without consent | One-time private fetch only if approved |
| Kalshi | Collection, storage and ML use appear prohibited without written consent (v1.1, Data Terms) | Module disabled until Aldemir decides |
| Polymarket | Anti-scraping clause; personal licence; no redistribution | Private, rate-limited, documented-API reads only; record the open question |

**Publication rule for all sources:** raw and parsed market tables stay private in MyDrive. Published outputs carry derived statistics only (CLV summaries, calibration, skill scores), never line or price dumps.

**Proposed LICENSES.md rows** (to be added by Job B2 when a source or package is adopted; this document does not edit LICENSES.md):
- CBBD API: research and commercial use allowed; no raw redistribution.
- ESPN API: Disney ToU; personal non-commercial; automated access prohibited.
- SBRO archive: all rights reserved; private cross-check only.
- The Odds API: commercial API terms; storage, research and ML allowed; no standalone redistribution; pending purchase decision.
- Kalshi API and Data: research use requires written consent (newer version unverified).
- Polymarket: ToU 2026-08-11; personal licence; no scraping or redistribution.
- Polymarket-v1 dataset: CC-BY-4.0 (HF card); attribution required. (The arXiv paper is CC BY-SA 4.0; that licence covers the paper, not the dataset.)
- Plus every package in section 9.

---

## 7. Budget

### 7.1 Monthly cost of each option

| Option | Monthly cost | What it buys | Source |
|---|---|---|---|
| CBBD free key | $0 | Core API and basic CSV export; quota shared with CFBD (1,000 calls/mo in the Jan 2025 launch post, which a 2026-07-14 note marks as launch-period figures; current number **unverified**, read `X-CallLimit-Remaining`). Our need: ~10 backfill calls plus ~60 calls/month | [api-tiers](https://collegebasketballdata.com/api-tiers), [launch post](https://radsportsanalytics.com/blog/api-v2-is-now-in-general-availability/) |
| CBBD Patreon Tier 1+ / 2+ / 3+ | $1 / $5 / $10 | Tier 1+ ($1): chart export, ad-free; Tier 2+ ($5): bookmarks, saved queries, full Team Metrics and Shooting Profile explorers, usage-stats export; Tier 3+ ($10): priority support (Free already has core API and basic CSV export). `/scoreboard` requires Tier 1+ (api-docs.json). **Not needed** for `/lines` | [api-tiers](https://collegebasketballdata.com/api-tiers), [api-docs.json](https://api.collegebasketballdata.com/api-docs.json) |
| ESPN core API | $0 | (Terms decision) | — |
| SBRO | $0 | (Terms decision) | — |
| Kalshi public API | $0 | (Terms decision) | [quick start](https://docs.kalshi.com/getting_started/quick_start_market_data) |
| Dune (Kalshi partner data) | **unverified** | Hourly Kalshi tables | [Dune](https://docs.dune.com/data-catalog/curated/prediction-markets/kalshi/overview) |
| Polymarket APIs | $0 | All reads keyless | [API overview](https://docs.polymarket.com/getting-started/api.md) |
| The Odds API Starter | $0 | 500 credits/mo, no historical (the home page lists "Historical Odds" for Starter; conflict noted in section 1.4). **Not enough** for any Big Ten schedule; covers only MSU featured lines (~108 credits/mo), without Caesars or Fanatics | [home](https://the-odds-api.com/), [historical](https://the-odds-api.com/historical-odds-data/) |
| The Odds API 20K | $30 | Covers the recommended live schedule (scenario B) | [home](https://the-odds-api.com/) |
| The Odds API 100K | $59 | Covers the maximal live schedule (scenario C) or the close-only backfill | [home](https://the-odds-api.com/) |
| The Odds API 5M | $119 | Covers the full backfill (with 2 regions) plus live | [home](https://the-odds-api.com/) |
| The Odds API 15M | $249 | Not needed | [home](https://the-odds-api.com/) |
| Collector host | $0 on an existing always-on Mac; cloud VM e.g. $6/mo (1 vCPU, 1 GiB) or $12/mo (1 vCPU, 2 GiB) | Always-on scheduler | [DigitalOcean droplet pricing](https://www.digitalocean.com/pricing/droplets) |

### 7.2 The Odds API credit model (from the 2025-26 calendar; `cost.py`)

Live 2026-27, credits per month. R = region-equivalents (10 books each).

| Scenario | Settings | Nov (peak) | Dec | Jan | Feb | Mar | Apr | Season | Peak + 25% | Cheapest plan |
|---|---|---|---|---|---|---|---|---|---|---|
| A, minimal | featured R=1; 1H+props R=1; 3 game-day snapshots; 4 sweeps/day | 4,869 | 3,180 | 2,982 | 2,784 | 2,586 | 540 | 16,941 | 6,086 | 20K ($30) |
| **B, recommended** | featured R=2 (US books + Pinnacle + exchanges); 1H+props R=1; 3 snapshots; market checks; daily scores | **7,026** | 4,700 | 4,472 | 4,175 | 3,932 | 1,035 | 25,340 | **8,782** | **20K ($30)** |
| B at R=3 | as B, but featured R=3 (regions `us` + `eu` + `us_ex` requested separately) | 8,727 | 5,912 | 5,678 | 5,303 | 5,030 | 1,455 | 32,105 | 10,908 | 20K ($30) |
| C, maximal | featured R=4; additional R=2 with 12 markets × 4 snapshots; hourly sweeps; 1-min in-game featured polling of MSU games | 29,994 | 22,890 | 23,236 | 20,528 | 20,824 | 9,440 | 126,912 | 37,492 | 100K ($59) |

Formula per month (G games, S distinct tip times, D days, M MSU games): `3R_f·G + 9R_f·S + 3R_f·sweeps·D + snaps·markets·R_a·G + checks·G + 2D + inplay·M·130·3` [computed]. The 130 is the Odds API in-play window, tip to final ≈ 7,800 s at one poll per 60 s (section 2.4), not the 330-poll prediction-market window. If the Odds API poll ran over the full T − 10,800 s to final + 1,800 s window (330 polls), scenario C would be Nov 34,194, season 147,912, peak + 25% 42,742: still inside the 100K plan [computed, `cost.py` with 330].

Scenario B at R=2 assumes one `bookmakers=` list may mix books from `us`, `eu` (Pinnacle) and `us_ex` (exchanges), counting each 10 books as one region; that is **unverified** (section 1.4). If it is not allowed, the R=3 row applies; it still fits the 20K plan at peak + 25% (10,908 credits) [computed]. This question is on the vendor checklist in section 7.3.

One-off backfill since 2021-22 [computed from ESPN counts]:

| Package | R = 1 | R = 2 |
|---|---|---|
| Featured close only (1,588 tip slots × 30) | 47,640 | 95,280 |
| Featured open + t-24h + t-1h + close (open via historical-events binary search, labelled `open_first_seen`) | 218,898 | 416,088 |
| 1H close only (1,173 games, 2023-24 to 2025-26) | 35,190 | 70,380 |
| 1H + props, 8 markets, 3 snapshots | 281,520 | 563,040 |
| **Minimum useful: featured close + 1H close** | **82,830 → 100K plan, $59** | |
| **Full: featured 4 snapshots + 1H/props 3 snapshots** | **500,418 → 5M plan, $119** | 979,128 → 5M |

Props credits are upper bounds, since only returned markets are charged. Wall time for the full backfill is about 29,000 calls at 5 req/s ≈ 5,800 s.

### 7.3 Recommendation (for Aldemir to approve)

1. **Now, $0:** CBBD (free key), Polymarket after decision 6 (live 1-minute capture for MSU games and post-game backfills), and the matching, checks and de-vig pipeline. ESPN, SBRO and Kalshi run only after the decisions in section 0.
2. **The Odds API, recommended: $269 for 2026-27.** One month of the 5M plan ($119), starting late Oct or early Nov 2026, runs the full backfill and November's live collection. Then the 20K plan ($30/mo) from Dec to Apr (5 × $30), cancelled in April. It is the only source of timestamped multi-book closes, 1H lines and props since 2023-24.
   - Cheaper alternatives:
     - live only: 6 × $30 = **$180**;
     - close-only backfill + live: $59 + 5 × $30 = **$209** (if the backfill finishes within one 100K month);
     - backfill only: **$59** or **$119** for one month.
   - Before buying, ask the vendor whether credits reset on the 1st or on the billing day, and whether they roll over ([FAQ](https://the-odds-api.com/manage/faqs.html)). If they reset on the 1st, start near the beginning of a month.
   - Vendor checklist, also before buying: (a) may one `bookmakers=` list mix books from different regions (`us`, `eu`, `us_ex`), and is it billed per 10 books (decides R=2 vs R=3 for scenario B; both fit 20K, section 7.2)? (b) does the free Starter plan include historical odds (home page says yes; historical page and v4 guide say paid only)?
3. Kalshi: $0 if permission is granted. Dune's cost is unverified and would need a quote.

---

## 8. Module layout proposal: `src/msu_alpha/markets/`

The package fits the existing `src/msu_alpha/` (Python ≥ 3.10, `pyyaml` only, pytest in dev; see `pyproject.toml`). Job B2 writes the code; this section is the design only.

```
src/msu_alpha/markets/
  __init__.py
  config.py          # loads config/markets.yaml (proposed): sources enabled/disabled, base URLs,
                     # rate caps, schedule offsets (s), Drive paths, tolerance thresholds
  http.py            # the one read-only client: endpoint allowlist, auth-header guard,
                     # per-host token bucket, jittered exponential backoff, Retry-After,
                     # key stripping; every call goes through raw_store.save() first
  raw_store.py       # gzip body + JSONL manifest (section 3.1); redaction hook for Polymarket identity fields
  odds.py            # American <-> decimal <-> probability conversions, booksum, hold
  devig.py           # multiplicative, additive, power, Shin (n = 2 closed form + general), odds ratio;
                     # π <= 1 and one-sided handling
  schema.py          # snapshot-table schema (pyarrow) + pandera contracts (section 4.2 rule IDs)
  parse.py           # dispatch: raw record -> per-source parser -> snapshot rows -> devig -> contracts
  sources/
    __init__.py
    cbbd.py          # /games, /lines, /lines/providers; pick'em rule; sourceId bridge
    espn.py          # core /odds, /providers, teamrankings /movement, site schedule/scoreboard (gated by config)
    sbro.py          # one-time 2021-22 HTML parser (gated by config)
    oddsapi.py       # /events, /odds, /events/{id}/odds, historical; credit guard on x-requests-remaining
                     # (disabled until Aldemir approves a plan)
    kalshi.py        # series/events/markets/orderbook/candlesticks/historical (disabled until terms decision)
    polymarket.py    # Gamma keyset + companions, CLOB books/midpoints/prices-history, Data v2 prices-history/trades/tokens
  matching.py        # team_xwalk loader, normalisation, RapidFuzz fallback, per-source game matcher,
                     # match_queue + source_event_map writers, review CLI
  checks.py          # cross-source rules XS-1..XS-6, stale/jump rules, weekly completeness
  store.py           # Parquet dataset writer (hive partitions, run_id basenames), quarantine writer;
                     # dedup key = C-14 key (includes market_phase and snapshot_label)
  scheduler.py       # entry point: `python -m msu_alpha.markets.scheduler` (APScheduler BlockingScheduler,
                     # UTC); daily planner turns the ESPN schedule into per-game date jobs; `--once <job>` for tests/backfills
  backfill.py        # one-off backfills (section 2.5), resumable by checkpoint
tests/markets/
  test_devig.py      # sum of fair probabilities = 1 within 1e-9 for every method on random booksum in [0.95, 1.30]
                     # (covers the exchange band) and n in {2, 3}; explicit cases booksum == 1 exactly and
                     # booksum < 1 assert the booksum_le_1 flag and sum(p) = 1 +/- 1e-9 (widened bracket or
                     # multiplicative fallback, section 3.3); Shin == additive for n = 2; reproduce shin README [2.6, 2.4, 4.3] ->
                     # [0.373, 0.405, 0.222] and CKI 2017 Table 2; optional oracle comparison vs penaltyblog and shin
  test_odds.py       # conversions round-trip; -110/-110 -> booksum 1.0476
  test_guard.py      # allowlist refuses non-listed paths/methods, POLY_* and Authorization headers;
                     # grep of the package for forbidden paths (section 6)
  test_parse_*.py    # one per source, on saved raw fixtures (ESPN 401825481 incl. the 2022-23 price-in-point
                     # defect, Polymarket cbb-uk-mst-2025-11-18, Kalshi KXNCAAMBGAME event, SBRO sample rows)
  test_matching.py   # neutral-site flip, Eastern-date vs UTC, conference-tournament adjacent days, State/non-State guard;
                     # Polymarket event 7,200 s from the ESPN tip -> candidate but queued as time_diff_gt_tolerance
  test_checks.py     # each contract rule fires on a crafted bad row and quarantines it; a post-game CBBD
                     # close_reported row (observed_post_event = true, source_time_utc null) passes C-13; ESPN
                     # open == close rows from one response pass C-14
```

Run record: each scheduler run, or the first B2 run, writes `results/markets_<date>/` with counts per source, quota headers seen, contract failures by rule ID, match-queue size and completeness. That directory holds counts only, never prices.

---

## 9. New dependencies and licences

| Package | Use | Version seen | Licence | Source | Status |
|---|---|---|---|---|---|
| httpx | HTTP client (sync + async) | — | **unverified in Job B1** | recommended in the Polymarket notes | Proposed; confirm licence before adoption |
| pyarrow | Parquet writing, schema | — | **unverified in Job B1** | [Arrow datasets](https://arrow.apache.org/docs/python/dataset.html) | Proposed; confirm licence |
| scipy | `brentq` root finding for power, Shin, odds ratio | — | BSD per the methods notes (**no URL opened; unverified**) | — | Proposed; confirm licence |
| APScheduler 3.11.3 | Scheduler | 3.11.3 (2026-06-28) | MIT | [PyPI](https://pypi.org/project/APScheduler/) | Proposed |
| SQLAlchemy | APScheduler persistent job store | — | **unverified in Job B1** | [APScheduler guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) | Optional; or rebuild jobs from the schedule at start-up instead |
| pandera | Contracts | — | MIT | [GitHub](https://github.com/unionai-oss/pandera) | Proposed |
| RapidFuzz | Fuzzy team-name fallback | — | MIT | [GitHub](https://github.com/rapidfuzz/RapidFuzz) | Proposed |
| penaltyblog 1.13.1 | Test oracle for de-vig (dev only) | 1.13.1 (2026-10-05) | MIT | [PyPI](https://pypi.org/project/penaltyblog/), [GitHub](https://github.com/martineastwood/penaltyblog) | Optional, dev |
| shin 0.2.2 | Test oracle for Shin (dev only) | 0.2.2 (2025-10-23) | MIT | [PyPI](https://pypi.org/project/shin/) | Optional, dev |
| warcio | WARC export | — | Apache-2.0 | [GitHub](https://github.com/webrecorder/warcio) | Not in v1 |
| cbbd 1.30.1 | CBBD client | 1.30.1 (2026-10-09) | MIT | [PyPI](https://pypi.org/project/cbbd/) | **Not recommended** (drops the raw body) |
| polymarket-client 0.13.0, py-clob-client(-v2), polymarket-us | Polymarket SDKs | 0.13.0 / 0.34.6 / 1.2.1 / 2.4.1 | MIT | [PyPI JSON](https://pypi.org/pypi/polymarket-client/json), [py-clob-client](https://pypi.org/pypi/py-clob-client/json), [py-clob-client-v2](https://pypi.org/pypi/py-clob-client-v2/json), [polymarket-us](https://pypi.org/pypi/polymarket-us/json) | **Excluded** (ship trading code) |
| goto-conversion 4.0.3 | Alternative de-vig | 4.0.3 | MIT | [PyPI](https://pypi.org/project/goto-conversion/) | Not needed |
| R `implied` 0.5 | De-vig reference | 0.5 | **GPL-3** | [CRAN](https://cran.r-project.org/web/packages/implied/index.html) | Reference only; not a dependency |
| hoopR 3.1.0 (R) | Team crosswalk seed | 3.1.0 (2026-08-25) | MIT | [CRAN](https://cran.r-project.org/web/packages/hoopR/index.html) | Already in LICENSES.md; export its crosswalk once and store the table |
| Polymarket-v1 dataset | 2025-26 trade backfill | — | CC-BY-4.0 (HF card); attribution required (the arXiv paper's CC BY-SA 4.0 covers the paper only) | [arXiv](https://arxiv.org/abs/2606.04217), [HF](https://huggingface.co/datasets/TimeSeventeen/Polymarket-v1) | Optional; adoption decision |

Standard-library pieces (`zoneinfo`, `gzip`, `hashlib`, `json`, `decimal`) need no LICENSES.md entry. Every adopted package gets a LICENSES.md row in Job B2, with its licence re-checked on its own page at adoption.

---

## 10. Open items and unverified points to resolve during B2

1. CBBD (first keyed call): provider names, spread sign, conference string ("B1G" vs "Big Ten"), `sourceId` = ESPN ID, and 2021-22 to 2025-26 completeness for the Big Ten.
2. Whether hoopR's prebuilt release files contain any odds (not checked in Job B1). *Checked in the fix pass (section 0):* no odds files; only four game-level spread columns in the PBP files. Still open: which book and moment that spread is, verified on one downloaded file if Aldemir approves the download.
3. ESPN pre-game prop availability and pre-game MBB scoreboard odds.
4. The Odds API: mixing regions in one `bookmakers=` list; filters on historical `/odds`; live vs historical event-ID stability; NCAAB 1H and prop depth; credit reset and rollover; free-plan rate limit; whether the free Starter plan includes historical odds (home page vs historical page and v4 guide).
5. Kalshi: current Developer Agreement text and fee schedule; unauthenticated rate limit; 1H, team-total and futures tickers; spread/total strike field names; batch candles on historical markets.
6. Polymarket: CLOB `prices-history` retention; regular-season 1H and companion events for CBB; meaning of `secondsDelay`; provenance of `gameId`/`providerId`; whether the sports WebSocket pushes CBB.
7. The licences of httpx, pyarrow, scipy and SQLAlchemy (not opened in Job B1).
8. Requirement IDs R-MK-01 to R-MK-09, R-DQ-01, R-DQ-05, R-RG-07 and R-RG-08: to be defined in `docs/requirements.md` by the requirements session.
9. ESPN MBB in-game status names (`STATUS_IN_PROGRESS`, `state` "in") for the actual-tip rule (section 2.2), and whether Polymarket `/v2/prices-history` retention is counted from request time (section 1.6).

---

## Sources

Every URL below was opened (or probed) by a Job B1 researcher, as recorded in the research notes. Entries marked **(not opened / unverified)** are cited only to show that a claim could not be confirmed.

**CollegeBasketballData.com**
- https://collegebasketballdata.com/terms
- https://collegebasketballdata.com/api-tiers
- https://collegebasketballdata.com/key
- https://collegebasketballdata.com/
- https://collegebasketballdata.com/college-basketball-api
- https://collegebasketballdata.com/exporter
- https://api.collegebasketballdata.com/
- https://api.collegebasketballdata.com/usage-and-access.md
- https://api.collegebasketballdata.com/authentication.md
- https://api.collegebasketballdata.com/data-availability.md
- https://api.collegebasketballdata.com/libraries/python.md
- https://api.collegebasketballdata.com/api-docs.json [probed]
- https://api.collegebasketballdata.com/lines/providers [probed, 401 without key]
- https://radsportsanalytics.com/blog/api-v2-is-now-in-general-availability/
- https://pypi.org/project/cbbd/
- https://github.com/CFBD/cbbd-python
- https://github.com/CFBD/cbbd-python/blob/main/docs/LinesApi.md
- https://github.com/CFBD/cbbd-r
- https://raw.githubusercontent.com/CFBD/cbb-api/main/README.md
- https://raw.githubusercontent.com/CFBD/cbb-api/main/src/app/lines/service.ts
- https://raw.githubusercontent.com/CFBD/cbb-api/main/src/app/lines/controller.ts
- https://raw.githubusercontent.com/CFBD/cbb-api/main/src/config/middleware/quotas.ts
- https://raw.githubusercontent.com/CFBD/cbb-api/main/src/config/middleware/index.ts
- https://raw.githubusercontent.com/CFBD/cbb-api/main/src/config/types/db.d.ts
- https://raw.githubusercontent.com/CFBD/cbb-api/main/src/app/games/scoreboard.ts
- https://cdn.collegefootballdata.com/Gumroad/CBB%20Starter%20Pack/CBBD%20Starter%20Pack%20-%20Data%20Files%20Guide.pdf
- https://hoopr.sportsdataverse.org/articles/cbbd-college-basketball-data.html
- https://rdrr.io/cran/hoopR/man/cbbd_lines.html
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/cbbd_games.R
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/cbbd_lines.R
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/cbbd_teams.R
- https://github.com/aself101/cbb-api

**ESPN and hoopR / sportsdataverse**
- https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/401825481/competitions/401825481/odds [probed; plus all MSU events 2021-22 to 2025-26, history, movement, propBets, providers]
- https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event=401715612 [probed]
- https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard [probed with dates and groups]
- https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=20260327 [probed]
- https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates=20261021 [probed]
- https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/127 [probed]
- https://www.espn.com/robots.txt [probed]
- https://disneytermsofuse.com/english/
- https://github.com/pseudo-r/Public-ESPN-API
- https://dev.to/zuplo/unlocking-espns-hidden-api-a-developers-guide-1pp7
- https://appdevelopermagazine.com/The%20World%20Wide%20Leader%20in%20Sports%20Leaves%20Developers%20in%20a%20World%20of%20Hurt%20as%20ESPN%20Closes%20Public%20API/ **(not opened / unverified; search snippet)**
- https://www.bnnbloomberg.ca/business/2025/11/06/espn-taps-draftkings-as-sports-betting-partner-after-ending-penn-deal/
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/espn_basketball_event_betting_helpers.R
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/espn_mbb_data.R
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/espn_mbb_event_detail.R
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/espn_mbb_futures.R
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/DESCRIPTION
- https://raw.githubusercontent.com/sportsdataverse/sportsdataverse-py/main/sportsdataverse/_espn_basketball_pbp.py
- https://raw.githubusercontent.com/sportsdataverse/sportsdataverse-py/main/sportsdataverse/mbb/mbb_pbp.py
- https://pypi.org/pypi/sportsdataverse/json
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/mbb_crosswalk.R
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/crosswalk_basketball.R
- https://hoopr.sportsdataverse.org/reference/mbb_team_crosswalk.html
- https://hoopr.sportsdataverse.org/reference/espn_mbb_teams.html
- https://ftp.fau.de/cran/web/packages/hoopR/news/news.html
- https://cran.r-project.org/web/packages/hoopR/index.html
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/load_mbb.R (fix pass, 2026-10-18)
- https://hoopr.sportsdataverse.org/reference/index.html (fix pass)
- https://github.com/sportsdataverse/hoopR-mbb-data/releases (fix pass; no releases)
- https://github.com/sportsdataverse/sportsdataverse-data/releases (fix pass; first page)
- https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_mens_college_basketball_pbp (fix pass)
- https://github.com/sportsdataverse/sportsdataverse-data/releases/tag/espn_mens_college_basketball_schedules (fix pass)
- https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=20260327&groups=50 [probed in fix pass; status field shape]

**Sportsbook Reviews Online**
- https://www.sportsbookreviewsonline.com/scoresoddsarchives/ncaabasketball/ncaabasketballoddsarchives.htm [curl]
- https://www.sportsbookreviewsonline.com/scoresoddsarchives/ncaa-basketball-2021-22/ [curl, parsed]
- https://www.sportsbookreviewsonline.com/terms/ [curl]
- https://www.sportsbookreviewsonline.com/robots.txt [curl]
- https://www.cs.iusb.edu/technical_reports/TR-20240429-1_Goldstein.pdf
- https://escholarship.org/content/qt115957mb/qt115957mb.pdf

**The Odds API**
- https://the-odds-api.com/liveapi/guides/v4/
- https://the-odds-api.com/
- https://the-odds-api.com/historical-odds-data/
- https://the-odds-api.com/sports-odds-data/ncaa-basketball-odds.html
- https://the-odds-api.com/sports/ncaab-odds.html
- https://the-odds-api.com/sports-odds-data/betting-markets.html
- https://the-odds-api.com/sports-odds-data/bookmaker-apis.html
- https://the-odds-api.com/sports-odds-data/update-intervals.html
- https://the-odds-api.com/guide/rate-limit.html
- https://the-odds-api.com/terms-and-conditions.html
- https://the-odds-api.com/manage/faqs.html
- https://the-odds-api.com/manage/upgrade-downgrade-cancel-a-subscription.html
- https://github.com/the-odds-api/samples-python
- https://theoddsapi.com/
- https://purduesports.com/news/2025/09/18/big-ten-announces-2025-26-mens-basketball-schedule
- https://www.wilx.com/2025/09/18/michigan-state-mens-basketball-releases-its-2025-26-conference-schedule
- https://en.wikipedia.org/wiki/2026_Big_Ten_men%27s_basketball_tournament

**Kalshi**
- https://docs.kalshi.com
- https://docs.kalshi.com/llms.txt
- https://docs.kalshi.com/getting_started/quick_start_market_data
- https://docs.kalshi.com/getting_started/api_environments.md
- https://docs.kalshi.com/getting_started/rate_limits.md
- https://docs.kalshi.com/getting_started/historical_data.md
- https://docs.kalshi.com/getting_started/terms.md
- https://docs.kalshi.com/getting_started/fee_rounding.md
- https://docs.kalshi.com/getting_started/fixed_point_migration.md
- https://docs.kalshi.com/getting_started/pagination.md
- https://docs.kalshi.com/getting_started/making_your_first_request.md
- https://docs.kalshi.com/api-reference/market/get-market-candlesticks.md
- https://docs.kalshi.com/api-reference/market/batch-get-market-candlesticks.md
- https://docs.kalshi.com/api-reference/events/get-event-candlesticks.md
- https://docs.kalshi.com/api-reference/market/get-markets.md
- https://docs.kalshi.com/api-reference/market/get-market-orderbook.md
- https://docs.kalshi.com/api-reference/market/get-trades.md
- https://docs.kalshi.com/api-reference/market/get-series-list.md
- https://docs.kalshi.com/api-reference/market/get-series.md
- https://docs.kalshi.com/api-reference/events/get-events.md
- https://docs.kalshi.com/api-reference/historical/get-historical-market-candlesticks.md
- https://docs.kalshi.com/api-reference/historical/get-historical-trades.md
- https://docs.kalshi.com/api-reference/historical/get-historical-markets.md
- https://docs.kalshi.com/api-reference/historical/get-historical-cutoff-timestamps.md
- https://docs.kalshi.com/websockets/websocket-connection.md
- https://docs.kalshi.com/websockets.md
- https://docs.kalshi.com/changelog
- https://external-api.kalshi.com/trade-api/v2/events?series_ticker=KXNCAAMBGAME&limit=2&with_nested_markets=true [probed]
- https://api.elections.kalshi.com/trade-api/v2/events/KXNCAAMBGAME-25NOV18MSUUK [probed]
- https://kalshi-public-docs.s3.amazonaws.com/Kalshi-Developer-Agreement.pdf
- https://kalshi-public-docs.s3.amazonaws.com/kalshi-data-terms-of-service.pdf
- https://kalshi.com/developer-agreement **(could not open; HTTP 429)**
- https://help.kalshi.com/en/articles/13823819-how-to-become-a-market-maker-on-kalshi
- https://help.kalshi.com/en/articles/13823805-fees
- https://github.com/alexander-bain/bainluck/issues/5023
- https://www.cftc.gov/sites/default/files/filings/ptc/25/01/ptc01222514045.pdf
- https://www.karlwhelan.com/Papers/Kalshi.pdf
- https://www.federalreserve.gov/econres/feds/files/2026010pap.pdf
- https://allium.so/blog/kalshi-fees-why-the-cost-peaks-near-50-cents/
- https://docs.dune.com/data-catalog/curated/prediction-markets/kalshi/overview
- https://www.cftc.gov/media/14276/EventContractsReportingNPRM062526/download

**Polymarket**
- https://docs.polymarket.com/getting-started/api.md
- https://docs.polymarket.com/getting-started/python.md
- https://docs.polymarket.com/api-reference/rate-limits.md
- https://docs.polymarket.com/api-reference/geoblock.md
- https://docs.polymarket.com/api-reference/markets/get-prices-history.md
- https://docs.polymarket.com/api-reference/markets/get-batch-prices-history.md
- https://docs.polymarket.com/api-reference/markets/get-a-tokens-price-history.md
- https://docs.polymarket.com/market-data/prices-order-books.md
- https://docs.polymarket.com/market-data/discover-markets.md
- https://docs.polymarket.com/concepts/markets-events.md
- https://docs.polymarket.com/concepts/prices-orderbook.md
- https://docs.polymarket.com/migrate/data-api-v1-to-v2.md
- https://docs.polymarket.com/api-reference/events/list-events-keyset-pagination.md
- https://docs.polymarket.com/api-reference/events/get-event-by-slug.md
- https://docs.polymarket.com/api-reference/markets/list-markets-keyset-pagination.md
- https://docs.polymarket.com/api-reference/series/list-series.md
- https://docs.polymarket.com/api-reference/sports/get-sports-metadata-information.md
- https://docs.polymarket.com/api-reference/sports/get-valid-sports-market-types.md
- https://docs.polymarket.com/api-reference/sports/list-teams.md
- https://docs.polymarket.com/api-reference/feeds/list-trades.md
- https://docs.polymarket.com/api-reference/market-data/get-order-book.md
- https://docs.polymarket.com/api-reference/wss/market.md
- https://docs.polymarket.com/api-spec/clob-openapi.yaml
- https://docs.polymarket.com/trading/fees.md
- https://docs.polymarket.com/changelog/predictions.md
- https://data-api.polymarket.com/v2/openapi.json
- https://gamma-api.polymarket.com/events/slug/cbb-uk-mst-2025-11-18 [probed]
- https://gamma-api.polymarket.com/events?slug=cbb-mst-uconn-2026-03-27 [probed]
- https://clob.polymarket.com/prices-history [probed with market, startTs, endTs, fidelity=1]
- https://polymarket.com/tos
- https://docs.google.com/document/d/1N4aYlRcqaWCeKMID7vUSWJ1UPMvw_v6SP4cOFN8ZxR4
- https://docs.polymarket.us/api-reference/introduction.md
- https://docs.polymarket.us/api-reference/rate-limits.md
- https://docs.polymarket.us/api-reference/price-history/get-price-history.md
- https://docs.polymarket.us/trader-guide/sports-schema.md
- https://docs.polymarket.us/trader-guide/market-data.md
- https://docs.google.com/document/u/1/d/e/2PACX-1vQ-86JK7kI6jAkpUNEyTCSpkeP_7cZMKhAW0rtti9rjzXqhdqm-27YSrX9Bun8LjQ/pub
- https://pypi.org/pypi/polymarket-client/json
- https://pypi.org/pypi/py-clob-client/json
- https://pypi.org/pypi/py-clob-client-v2/json
- https://pypi.org/pypi/polymarket-us/json
- https://arxiv.org/abs/2602.19520
- https://arxiv.org/html/2602.19520 (fix pass; Tables 2–4)
- https://arxiv.org/abs/2605.00864
- https://arxiv.org/html/2604.24366v1
- https://arxiv.org/html/2606.04217v1
- https://arxiv.org/abs/2606.04217 (fix pass; paper licence)
- https://huggingface.co/datasets/TimeSeventeen/Polymarket-v1
- https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7552098 **(HTTP 403; unverified)**

**Legal and regulatory context**
- https://spectrumlocalnews.com/mi/michigan/news/2026/09/02/michigan-judge-blocks-kalshi
- https://spectrumlocalnews.com/mi/michigan/news/2026/06/30/michigan-blocks-sports-betting-kalshi
- https://www.michigan.gov/ag/-/media/Project/Websites/AG/releases/2026/September/Kalshi-Preliminary-Injunction-Order-Signed-Sep-1-2026.pdf
- https://legalnews.com/Home/Articles?DataId=1630335
- https://content.govdelivery.com/accounts/MIGCB/bulletins/4293a85
- https://defirate.com/news/michigan-wants-kalshi-held-in-contempt-as-state-crackdown-moves-beyond-trading/
- https://natlawreview.com/article/sixth-circuit-deepens-circuit-split-kalshi-sports-event-contracts-are-not-swaps-and
- https://theblock.co/news/regulation/2026-08-07-michigan-judge-denies-coinbase-bid-prediction-markets-411128
- https://www2.ca3.uscourts.gov/opinarch/251922p.pdf
- https://cdn.ca9.uscourts.gov/datastore/opinions/2026/08/28/25-7516.pdf
- https://www.supremecourt.gov/search.aspx?filename=/docket/docketfiles/html/public/26-299.html
- https://www.cftc.gov/PressRoom/PressReleases/9309-26
- https://www.cftc.gov/PressRoom/PressReleases/9310-26
- https://next.io/prediction-markets/polymarket/legal/
- https://coinstats.app/prediction-markets/legal/polymarket-mi/
- https://news.worldcasinodirectory.com/michigan-court-backs-state-authority-over-polymarket-sports-contracts-123238

**Margin removal, benchmarking, data quality**
- https://ndownloader.figshare.com/files/47662879 (Clarke, Kovalchik & Ingram 2017, full text)
- https://ndownloader.figshare.com/files/47535482 (Clarke 2016)
- https://www.github.com/mberk/shin
- https://raw.githubusercontent.com/mberk/shin/master/python/shin/__init__.py
- https://pypi.org/project/shin/
- https://cran.r-project.org/web/packages/implied/vignettes/introduction.html
- https://cran.r-project.org/web/packages/implied/index.html
- https://pypi.org/project/penaltyblog/
- https://github.com/martineastwood/penaltyblog
- https://pypi.org/project/goto-conversion/
- https://arxiv.org/abs/2604.17194
- https://arxiv.org/html/2604.17194 (fix pass; Table 1)
- https://en.wikipedia.org/wiki/Odds
- https://en.wikipedia.org/wiki/Mathematics_of_bookmaking
- https://www.matterofstats.com/what-is-vig-and-overround
- https://www.stat.berkeley.edu/~aldous/157/Papers/PointShaving.pdf (Wolfers 2006)
- https://iso25000.com/en/iso-25000-standards/iso-25012
- https://github.com/unionai-oss/pandera
- https://github.com/lbenz730/ncaahoopR
- https://rdrr.io/cran/cfbfastR/man/load_cfb_teams_crosswalk.html
- https://github.com/rapidfuzz/RapidFuzz

**Storage and scheduling**
- https://www.databricks.com/glossary/medallion-architecture
- https://www.loc.gov/preservation/digital/formats/fdd/fdd000236.shtml
- https://github.com/webrecorder/warcio
- https://parquet.apache.org/docs/file-format/types/logicaltypes/
- https://arrow.apache.org/docs/python/dataset.html
- https://pypi.org/project/APScheduler/
- https://apscheduler.readthedocs.io/en/3.x/userguide.html
- https://research.google.com/colaboratory/faq.html
- https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#schedule
- https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html
- https://www.digitalocean.com/pricing/droplets (fix pass, 2026-10-18)

**Repo files used for context (not web sources):** `coord/prompts/002-claude-code-taxonomy-and-markets.md`, `docs/research/odds_markets_research.md`, `docs/research/data_sources_catalog.md`, `docs/requirements.md`, `LICENSES.md`, `coord/PROTOCOL.md`, `pyproject.toml`.


---

## Additions 2026-10-18

Gap-fill pass written 2026-10-18 (UTC). It covers eight gaps found in review. Each subsection names the earlier section it extends. The conventions at the top of this document still apply: every URL was opened in this pass unless marked **(unverified)**; **[probed]** means one read-only, unauthenticated request; **[computed]** means a calculation made in this pass. Nothing here is legal advice. No account was created, nothing was bought or downloaded beyond public documentation pages, and no order, account or trading endpoint was called.

### A1. Settlement rules per market (extends sections 1.4–1.6, 3.2, 4.1 C-17/XS-4)

**Why it matters.** The same label ("spread", "1H total") can settle on different scopes in different venues. For example, a second-half line includes overtime at DraftKings but excludes it on Kalshi unless the title says so (both shown below). A line-to-result check, or a market-vs-model benchmark, is only valid when both sides settle on the same scope.

**Kalshi (contract-terms PDFs, linked from each series' `contract_terms_url` [probed: `GET /series/KXNCAAMBSPREAD`, `/series/KXNCAAMBTOTAL`, `/series/KXNCAAMBGAME`, 2026-10-18])**

| Point | BASKETBALLSPREADS (`KXNCAAMBSPREAD`, `KXNCAAMB1HSPREAD`, `KXNCAAMB2HSPREAD`, `KXNCAAMBWINMARGIN`) | BASKETBALLTOTALS (`KXNCAAMBTOTAL`, `KXNCAAMB1HTOTAL`, `KXNCAAMB2HTOTAL`, `KXNCAAMBTEAMTOTAL`, `KXNCAAMB1HTEAMTOTAL`) | BASKETBALLGAMEWIN (`KXNCAAMBGAME`, `KXNCAAMB1H`, `KXNCAAMB2H`) |
|---|---|---|---|
| Overtime | Counts "unless <time period> specifies otherwise"; a half "does not include any officially designated overtime period unless overtime is expressly specified" | "Overtime points are included unless explicitly excluded"; same half rule | Entire game = regulation + OT; same half rule |
| Cancelled before start | Last fair price | Last fair price | Last fair price if not rescheduled to start within 48 h |
| Delay ≤ 48 h / > 48 h | Stays open / last fair price | Stays open / last fair price | Stays open / last fair price for periods not fully completed |
| Abandoned after start, no restart in 48 h | All markets → last fair price, **except** "final game score" (resolves if 40 min played for a collegiate game, or the league declares the result official) and totals already reached | Same text | Full-game markets settle on the official record only if 40 min were played or the league declares the result; otherwise last fair price. A completed half settles on its record |
| Tie | Point differential recorded as 0 | n/a | Without a "Tie" strike, a tied period pays YES and NO **$0.50 each** (relevant to `KXNCAAMB1H`/`2H`) |
| Data unavailable | Wait 24 h, then last fair price | Wait 24 h, then last fair price | Wait 48 h, then last fair price |
| Corrections | "Corrections made afterwards will not affect the value" | Same | Revisions after expiration ignored |
| Latest expiration | 3rd day after the game, 10:00 ET | 3rd day after the game, 10:00 ET | One week after the game, 10:00 ET |
| Source agencies (in order) | League, ESPN, Fox Sports, official broadcaster | Same | League, ESPN, AP, Reuters, Fox Sports, official broadcaster |

Sources: [BASKETBALLSPREADS.pdf](https://assets.kalshi.com/contract_terms/BASKETBALLSPREADS.pdf) (PDF created 2026-10-14), [BASKETBALLTOTALS.pdf](https://assets.kalshi.com/contract_terms/BASKETBALLTOTALS.pdf) (2026-10-14), [BASKETBALLGAMEWIN.pdf](https://assets.kalshi.com/contract_terms/BASKETBALLGAMEWIN.pdf) (2026-09-29). Text extracted locally with `pdftotext`.

- **Ambiguity to flag:** the SPREADS abandoned-game clause exempts only "final game score" from fair-price settlement. Whether a spread contract counts as "final game score" is not stated, so a shortened game could settle spreads at a fair price while the winner market settles on the score **(interpretation; unverified)**.
- **Market-level text** [probed: `GET /events?series_ticker=KXNCAAMBGAME&limit=1&with_nested_markets=true`, event `KXNCAAMBGAME-26NOV02LIBHP`]: `rules_secondary` repeats the 48 h rule ("both markets will resolve to a fair price"). The probe also returned `can_close_early: true`, `early_close_condition` "This market will close and expire after a winner is declared", `latest_expiration_time` 2026-11-04T05:00:00Z for a 2 Nov game, and `settlement_timer_seconds: 45`. Store `rules_primary`, `rules_secondary` and `early_close_condition` per market (they are already in the raw body).
- **Series list resolves the 1H-ticker open item (section 10, item 5)** [probed: `GET /series?category=Sports&tags=Basketball`]: game-level NCAAM series include `KXNCAAMB1H`, `KXNCAAMB1HSPREAD`, `KXNCAAMB1HTOTAL`, `KXNCAAMB1HTEAMTOTAL`, `KXNCAAMB2H`, `KXNCAAMB2HSPREAD`, `KXNCAAMB2HTOTAL`, `KXNCAAMB2HTEAMTOTAL`, `KXNCAAMBTEAMTOTAL`, `KXNCAAMBWINMARGIN`, `KXNCAAMBOT` (overtime), race-to-points series and a `KXNCAAMB1HWINNER` series that uses a different rulebook (ACHIEVEMENTS.pdf; not read). Whether all of these list markets for regular-season Big Ten games is **unverified** (no spread events were open on 2026-10-18).

**Polymarket (market `description` text)** [probed: [cbb-uk-mst-2025-11-18](https://gamma-api.polymarket.com/events/slug/cbb-uk-mst-2025-11-18)]
- Moneyline, spread and total all say "The result will be determined based on the final score including any overtime periods."
- Postponed: "this market will remain open until the game has been completed". No time limit is stated, unlike Kalshi's 48 h.
- "If the game is canceled entirely, with no make-up game, this market will resolve 50-50."
- `resolutionSource`: `https://www.ncaa.com/`.
- Spread wording is in whole points: "win the game by 6 or more points" for −5.5. Total wording: "155 or more points" for O/U 154.5.
- A game abandoned part-way through is not addressed in the text (**unspecified**). The settlement rules of first-half companion markets were not probed **(unverified)**.

**Sportsbooks (house rules)**
- **DraftKings, Massachusetts house rules (implementation date 2025-08-26)** ([PDF](https://massgaming.com/wp-content/uploads/DraftKings-House-Rules-8.18.25.pdf), pp. 8–9, 41–43):
  - "all bets include overtime statistics for settlement purposes", except 3-way moneylines, 4th-quarter player points and similar named exceptions;
  - "Bets on 4th Quarter Markets and 2nd Half Markets include overtime statistics". (Kalshi halves exclude OT unless stated, so 2H lines are not comparable across these venues without a scope column.)
  - Quarter and half markets are void if the period "does not reach its intended, natural, or normal end";
  - A game that is interrupted with **five or more minutes of regulation remaining** and not concluded within two calendar days is void, except for settled outcomes. For 40-minute college regulation this equals the common **35-minute** rule [computed: 40 − 5];
  - A game that does not start within two calendar days of its scheduled date: void;
  - Participation means "entering the Game according to the Game's official box score". A selection that does not participate is void unless the market is labelled "all-in" or similar.
- **Gila River (Arizona) basketball rules** ([page](https://help.playatgila.com/en/general-information/sports-house-rules/basketball-wager-types-and-rules)): "NCAA and WNBA are official after 35 minutes of play". Overtime counts for spread, moneyline and total unless the market says "Regular Time". "Overtime periods are counted in the Second Half score". A prop is cancelled if the player "does not take any part in a game".
- **Peppermill Reno** ([house rules](https://www.peppermillreno.com/gaming/race-sportsbook/house-rules/)): "BASKETBALL (college) – 35 minutes of play"; "Except for soccer, overtime periods are counted in the final score".
- **Caesars, per Action Network:** "Basketball – player must play" ([Action Network](https://www.actionnetwork.com/education/prop-betting-rules-what-happens-if-player-doesnt-play)). FanDuel, BetMGM and Caesars primary basketball rules were not opened **(unverified)**. `legalsportsreport.com/how-to-bet/overtime-rules/` returned HTTP 403.
- **The Odds API publishes no settlement rules.** Each price settles under that bookmaker's house rules, which can vary by state edition (the DraftKings file above is the Massachusetts edition).

**Design addition: a `market_rules` dimension table, plus `rules_id` on every snapshot row**

| Column | Type | Example |
|---|---|---|
| `rules_id` | string (PK) | `kalshi:BASKETBALLSPREADS:2026-10-14` |
| `source`, `book`, `market` | string | `kalshi`, `kalshi`, `spread` |
| `period_scope` | enum | `full_game_incl_ot`, `regulation_only`, `h1`, `h2_incl_ot`, `h2_excl_ot`, `ot_only` |
| `settles_incl_ot` | bool | true |
| `push_possible` | bool | false for half-point lines and Kalshi "above" strikes |
| `not_started_rule` | string | `void_if_not_started_2d` (DK), `fair_price_48h` (Kalshi), `open_until_played_cancel_5050` (Polymarket) |
| `abandoned_rule` | string | `void_if_ge_5min_reg_left_2d` (DK), `fair_price_unless_40min_or_official` (Kalshi), `unspecified` (Polymarket) |
| `min_game_minutes` | int16, nullable | 35 (DK, Gila River, Peppermill, for NCAA); 40 (Kalshi full-game winner) |
| `tie_payout` | string, nullable | `0.50_each_without_tie_strike` (Kalshi GAMEWIN halves) |
| `prop_participation` | string, nullable | `enter_box_score` (DK), `take_any_part` (Gila River) |
| `cancel_payout` | string | `void_refund`, `last_fair_price`, `50_50` |
| `rules_url`, `rules_doc_sha256`, `rules_effective_from`, `observed_utc` | string / timestamp | sha256 of the PDF or text as fetched |

- Keep the rule documents in the raw store (`raw/rules/…`), refetch them monthly, and open a new `rules_id` whenever the sha256 changes.
- **C-17** (settlement agreement): grade every line against the score for its `period_scope`; skip rows whose `cancel_payout` was triggered; and treat a Kalshi settlement value strictly between 0 and 1 as `settled_fair_price`, never as a contract failure.
- **XS-4/XS-5** compare only rows with an equal `period_scope` and `settles_incl_ot`.
- **New rule C-18:** flag every game that went to overtime (from the ESPN or CBBD final), so OT games can be excluded or split in any comparison of half-game with full-game lines.

### A2. Exchange prices through The Odds API `us_ex` region (extends sections 1.4, 1.5, 1.6, 6, 7; decisions 4–6)

**What the vendor documents**
- `us_ex` ("US Exchanges") now lists seven keys: `betopenly`, `kalshi`, `limitless`, `novig`, `polymarket`, `polymarket_us`, `prophetx`. No plan restriction or delay note is attached to any of them ([bookmaker list](https://the-odds-api.com/sports-odds-data/bookmaker-apis.html), opened 2026-10-18). This supersedes the four keys listed in section 1.4.
- Update interval for "Betting exchanges (all markets)": **20 s pre-match, 10 s in-play**. From six hours before start, the pre-match interval "begins decreasing" toward the in-play rate ([update intervals](https://the-odds-api.com/sports-odds-data/update-intervals.html)).
- Lay odds (`h2h_lay`) are documented only for exchanges such as Betfair and Matchbook. `includeBetLimits` "mainly" serves exchanges ([v4 guide](https://the-odds-api.com/liveapi/guides/v4/)). Whether a `kalshi` or `polymarket` price is a best ask, a mid or a last trade is **not documented (unverified)**. The feed gives one price per outcome: no bid/ask pair, depth, volume or open interest.
- Historical data: "Bookmakers, sports, and markets appear in historical data only from when they were added" ([v4 guide](https://the-odds-api.com/liveapi/guides/v4/); [historical data](https://the-odds-api.com/historical-odds-data/)). **The date `kalshi` and `polymarket` were added is not published (unverified)**, so whether the Odds API can backfill 2025-26 exchange prices is unknown. Add it to the vendor checklist (section 7.3).
- **Terms** (last updated **2026-08-31**) ([terms](https://the-odds-api.com/terms-and-conditions.html)):
  - storage, research and ML on "our data" are permitted;
  - "All market data provided via the Service is aggregated from publicly accessible sources";
  - the terms are silent on licences from source operators and on whether customers must also follow source terms.

**Do Kalshi's terms still apply downstream? (not legal advice)**
- The Kalshi Data Terms of Use define "Kalshi Data" as content on the kalshi.com Website and bind the person "accessing the Website" ([Data Terms PDF](https://kalshi-public-docs.s3.amazonaws.com/kalshi-data-terms-of-service.pdf), text extracted locally). An Odds API customer does not access the Website or the Kalshi API, so the Developer Agreement and Data Terms *as contracts* would not obviously bind them.
- The same document asserts that "title and ownership rights in and to the Kalshi Data … remain exclusively with Kalshi and its licensors". The Odds API says it aggregates from "publicly accessible sources", not that it holds a licence. The route therefore removes Kalshi's contract from our side but does not settle Kalshi's ownership claim.
- Kalshi does license its data commercially (a multi-year Fox data partnership, Apr 2026 ([Finance Magnates](https://www.financemagnates.com/fintech/kalshi-sells-prediction-market-data-to-fox-expanding-beyond-trading/))). That suggests it treats price data as a product.
- Polymarket prices via the Odds API carry the same open question under Polymarket's terms (section 1.6).

**Cost and coverage** [computed with the section 7.2 formula]
- Pre-game: scenario B already budgets featured `R=2` "(US books + Pinnacle + exchanges)". Adding the five relevant exchange keys (`kalshi`, `polymarket`, `polymarket_us`, `novig`, `prophetx`) to about 10 US books plus Pinnacle gives about 16 books, still `R=2`. **No change to the $30/month live plan**, provided one `bookmakers=` list may mix regions (vendor checklist item (a)).
- In-game, MSU only: `/odds?eventIds=<id>&markets=h2h,spreads,totals&bookmakers=kalshi,polymarket,polymarket_us,novig,prophetx` costs 3 credits per poll. At one poll per 60 s from tip to final (130 polls) that is 390 credits per game, or 13,650 for 35 MSU games. Assuming at most 9 MSU games in the peak month (not counted): scenario B peak 7,026 + 3,510 = 10,536, and 13,170 with the 25% margin. **Still within the 20K ($30) plan.** Each poll samples a feed that refreshes every 10 s in play, so the series is a 60 s sample, not a 1-minute OHLC.
- What the route cannot give: Kalshi bid/ask/size/volume, Polymarket books, or Polymarket 1-minute history after the fact. XS-5 (exchange vs book at the same timestamp) and C-17 work on one price per outcome. Spread microstructure and the bid–ask "overround" analysis in section 3.3 do not.

**Effect on decisions**
- **Decision 5 (Kalshi), new option (d):** take Kalshi game, spread and total prices only through a paid Odds API plan, keep `kalshi.enabled: false` for direct API reads, and record the residual ownership question. This needs decision 4 (an Odds API plan) and two vendor answers:
  1. Does The Odds API hold licences from Kalshi and Polymarket, and do its terms cover exchange prices the same way as sportsbook prices?
  2. From what date does historical data include `kalshi` and `polymarket` for `basketball_ncaab`?
  Asking Kalshi for written permission (option (a)) is still the only route that settles the ownership question.
- **Decision 6 (Polymarket):** the Odds API route cannot replace direct reads for books and 1-minute capture. It can serve as a fallback price series when the direct module is off or fails.
- **Budget (section 7.3):** unchanged. Exchange coverage rides on the recommended plan at no extra plan cost.

### A3. Open historical Kalshi and Polymarket datasets (extends sections 1.5, 1.6, 2.5, 9)

| Dataset | Content | Coverage | Size / access | Licence | Fit for MSU 2025-26 |
|---|---|---|---|---|---|
| **Jon-Becker/prediction-market-analysis** ([repo](https://github.com/jon-becker/prediction-market-analysis); [schemas](https://github.com/Jon-Becker/prediction-market-analysis/blob/main/docs/SCHEMAS.md)) | Kalshi markets (bid/ask/last in cents, volume, OI, result, open/close times) and Kalshi trades (`trade_id`, `ticker`, `count`, `yes_price`, `taker_side`, `created_time`). Polymarket markets and on-chain `OrderFilled` trades with `maker`/`taker` **addresses** | Archive `data.tar.zst` last modified **2026-02-05 19:28:50 GMT** [probed: HTTP HEAD on https://s3.jbecker.dev/data.tar.zst], so 2025-26 coverage can run at most to early Feb 2026 (inference; the max `created_time` is unverified). Repo created 2025-11-22, last push 2026-10-16 (citation updates) [GitHub API] | One archive, **36,020,641,508 bytes** (≈ 33.5 GiB [computed]; README says "36GiB") [probed HEAD]. No per-series download | Code: **MIT** (LICENSE file, © 2026 Jonathan Becker) [GitHub API]. **The dataset has no stated licence**; MIT covers the code, not Kalshi's or Polymarket's data | Kalshi trades for `KXNCAAMB*` from 2025-11-03 to about 2026-02-05 could rebuild 1-minute last-trade/VWAP series for MSU games in that window. Not the tournament. Bid/ask history is absent (market rows are snapshots at fetch time, `_fetched_at`) |
| Polymarket-v1 (already in section 1.6) | On-chain fills | 2022-11-21 to 2026-04-28 | HF | CC-BY-4.0 (HF card) | Whole 2025-26 season for Polymarket |
| SII-WANGZJ/Polymarket_data ([HF](https://huggingface.co/datasets/SII-WANGZJ/Polymarket_data)) | Polymarket market records (question, tokens, outcome prices, volume, …) | Not stated on the card excerpt read | "1B–10B" rows; train split 6.59B rows | **Not seen (unverified)** | Market metadata only in the excerpt read; not a price tape |
| Allium `common.predictions` ([docs](https://docs.allium.so/historical-data/predictions/kalshi)) | Kalshi trades, markets, events, series, fee changes, hourly candles, daily OI, **order-book snapshots** | Not stated | Commercial; price not stated | Not stated | Possible paid source of Kalshi book history; needs a quote and licence check |
| Dune Kalshi tables ([docs](https://docs.dune.com/data-catalog/curated/prediction-markets/kalshi/overview)) | `market_details`, `market_trades`, `ohlcv_hourly`, `open_interest_hourly`, … | Not stated; "~1 hour" refresh; labelled "Dune (partner data)", source "Off-chain (Kalshi)" | Access tier not stated | Not stated | As in section 1.5 |
| pmxt archive (`archive.pmxt.dev`) | Reported Parquet dumps incl. a `Kalshi/` folder (search snippet only) | — | Connection refused when opened 2026-10-18 | **Unverified** | Unknown |
| Kaggle / Hugging Face Kalshi NCAAB | None found in two searches | — | — | — | — |

- **Kalshi terms still attach (not legal advice).** The Becker Kalshi indexer calls `https://api.elections.kalshi.com/trade-api/v2` (`/markets/{ticker}`, `/markets/trades`) at a 10 req/s client limit ([`src/indexers/kalshi/client.py`](https://github.com/Jon-Becker/prediction-market-analysis/blob/main/src/indexers/kalshi/client.py), read via the GitHub API). That is the same API whose Developer Agreement and Data Terms are the blocker in section 1.5. The Data Terms prohibit "providing archived or cached data sets containing Kalshi Data to another person" without consent, and they prohibit ML use. So using the archive does not avoid the Kalshi question. It moves the question to whether the downstream user is bound, as in A2.
- **Polymarket part:** the trade rows carry wallet addresses. The redaction rule in section 3.1 applies before anything enters the raw store.
- **Recommendation:** treat the Becker archive as decision-5-dependent, like direct Kalshi reads. If Aldemir approves it, download once (36 GB, needs his approval as a large download), filter immediately to `ticker LIKE 'KXNCAAMB%'`, keep only the filtered Parquet plus the archive's sha256 and HTTP headers, and record "dataset licence: none stated; code MIT" in LICENSES.md. The archive's integer-cent schema predates Kalshi's fixed-point migration (section 1.5), so the parser must not share Kalshi's current `*_dollars` parser.

### A4. When information arrives and lines move (extends section 2.2)

**Evidence**
- **Gandar, Dare, Brown & Zuber (1998), *Journal of Finance* 53(1):385–401, NBA point spreads (peer-reviewed).** Abstract: "within-betting period line changes significantly improve the accuracy of betting lines as forecasts of game outcomes". Line changes are "directly and proportionately related to biases in opening lines" and "of sufficient magnitude to remove these biases by the close" ([Crossref record with abstract](https://api.crossref.org/works/10.1111/0022-1082.155346)). Sample size not in the abstract **(unverified)**. Supports keeping both `open` and `close`.
- **Dare, Dennis & Paul (2015), *Finance Research Letters* 13:130–136, NBA player absences (peer-reviewed).** Lines move away from teams with absences. Opening lines show significant errors in games with an absent player. No profitable strategy exists at the close ([IDEAS](https://ideas.repec.org/a/eee/finlet/v13y2015icp130-136.html)). Sample and effect sizes not on the page **(unverified)**. Availability news is a main driver of line moves.
- **Hickman & Metz (2024), *Applied Economics*, NCAA men's basketball, 2009–2022 seasons (peer-reviewed).** Coaching changes, and to a lesser extent player turnover, reduce line accuracy and increase line movement, but "only … for the first few weeks of the season" ([U. Idaho record](https://verso.uidaho.edu/esploro/outputs/journalArticle/How-quickly-do-markets-incorporate-new/996683436201851); DOI 10.1080/00036846.2024.2364077). Sample and effect sizes not on the record page **(unverified)**.
- **Simon (2024), *Management Science* 70(12):8583–8611, 3,681 MLB games, four sportsbooks (peer-reviewed).** Lines "overreact" with negatively autocorrelated changes. Forecasts do not reliably improve toward the start, and "forecasts at weekend day games' start times are significantly worse than forecasts 90 minutes earlier" ([IDEAS](https://ideas.repec.org/a/inm/ormnsc/v70y2024i12p8583-8611.html)). This is the paper the gap list called "a 2025 Management Science paper"; RePEc dates it Dec 2024. It is a reason not to assume the last tick before tip is the best forecast. Keep `t-1h` and the three close times, and test which is most accurate on our data.
- **Glush (2026), Mendeley Data line-movement dataset (not peer-reviewed; CC BY 4.0; 11.7M hourly snapshots, 52 books, 2026-06-29 to 2026-08-03; NCAAB not covered).** Prices sit about 2.2 probability points from their close 3–7 days out, and 0.33 points in the final six hours ([dataset](https://data.mendeley.com/datasets/pdsxx5dgbw/1)). Indicative only: summer sports, not NCAAB.
- No study of intraday NCAAB line-movement timing was found. Our own `open`/`t-24h`/`t-1h`/`close` series will be the first evidence for MSU and Big Ten games.

**Availability reports**
- The Big Ten introduced availability reports "for football and men's and women's basketball in 2023" ([ESPN, 2025-08-13](https://www.espn.com/college-football/story/_/id/45968809/big-12-issue-player-availability-reports-first)). Reports are posted as weekly PDFs on bigten.org (seen only in search results; the report pages returned HTTP 500/402 **(unverified)**).
- **Release time:** one report says a Big Ten report was "released three hours prior to tipoff" and later amended ([SI, 2025-03-01](https://www.si.com/college/indiana/basketball/malik-reneau-not-listed-on-indiana-injury-report-for-washington-game-01jn9p5vxc7s)). That is one game, so the conference's basketball deadline is **unverified**.
- **Comparison:** Big 12 basketball files "the night before each contest and again 90 minutes prior to tipoff" with statuses "available, game-time decision or out" ([CBS Sports, 2025-08-13](https://www.cbssports.com/college-football/news/big-12-to-mandate-player-availability-reports-for-football-basketball-starting-in-2025-26)). Big Ten football requires "submissions two hours before kickoff" (same source).
- RotoWire's use of the report was not found **(unverified)**.

**Design additions (proposal)**
1. **New label `t-avail`** for every Big Ten conference game. It is a pre-game snapshot (same calls as `t-1h`, section 2.2) at **T − 9,000 s**: 30 min after the reported ~T − 10,800 s Big Ten release, and before the Big 12-style T − 5,400 s final report. Keep the offset in `config/markets.yaml` until the Big Ten basketball policy text is found. If Aldemir approves reading the bigten.org report page, a later version can trigger the snapshot 900 s after the report first appears. That is a terms question for bigten.org, which this pass did not check.
   - Odds API cost: one featured call per tip time = 3 markets × R. At R=2 that is 2,214 credits per season over 369 tip times, and at most 792 in November (≤ 132 tip times). Scenario B peak + 25% becomes ≤ 9,773 credits, still within 20K [computed].
   - Polymarket and Kalshi in-game capture already starts at T − 10,800 s for MSU games (section 2.4), so `t-avail` adds nothing there.
2. **Early-season density.** For the first 21 days of each season (Hickman & Metz), add `t-6h` (T − 21,600 s) to the pre-game set, since lines move more then. Cost: same as `t-avail` per tip time, over about 3 weeks.
3. **Join availability to lines.** Store each scraped or manually entered availability status with its first-seen time in a later `availability` table, so a line move can be tested against the report time (Dare et al. 2015 design). Out of scope for B2 unless Aldemir adds it.

### A5. Odds-ratio method (Cheung 2015) and the favourite–longshot bias (extends section 3.3; aligns with sections 8, 9)

**Formula** (R `implied` 0.6.1 source, `or_func`/`or_solvefor` ([implied_probabilities.R](https://github.com/opisthokonta/implied/blob/master/R/implied_probabilities.R), read via the GitHub API); vignette ([implied introduction](https://cran.r-project.org/web/packages/implied/vignettes/introduction.html))):

p_i = r_i / (c + r_i − c·r_i), with c chosen so that Σ p_i = 1 (root-find on c; c > 1 when π > 1, c = 1 when π = 1, c < 1 when π < 1).

Equivalently, the odds ratio c = [r_i/(1 − r_i)] / [p_i/(1 − p_i)] is **the same for every outcome**, so the margin is a constant multiplicative shift in odds space. The vignette credits it to "an article by Keith Cheung", listed as Cheung (2015) *Fixed-odds betting and traditional odds*, via Buchdahl's *Wisdom of the Crowds*. The Cheung article and the Buchdahl PDF could not be opened (no search hit; football-data.co.uk returned HTTP 429) **(unverified)**. penaltyblog implements it as `ImpliedMethod.ODDS_RATIO` ([`penaltyblog/implied/implied.py`](https://github.com/martineastwood/penaltyblog/blob/master/penaltyblog/implied/implied.py), read via the GitHub API), and `implied` is GPL-3, so it serves as a reference only.

Add to the section 3.3 table:

| Method | Formula | Source |
|---|---|---|
| Odds ratio | p_i = r_i/(c + r_i − c r_i), Σ p_i = 1 | `implied` 0.6.1 `or_func`; Cheung (2015) via Buchdahl **(unverified)** |
| Margin weights proportional to odds (`wpo`) | fair o_i = n·o_i/(n − m·o_i), m = π − 1 | `implied` source. **Algebraically identical to additive**: 1/fair o_i = 1/o_i − m/n = r_i − (π − 1)/n [computed]. No separate column needed |

**Test oracle** [computed with `scipy.optimize.brentq`, xtol 1e-14]:

| Prices | π | Odds ratio c | Odds ratio p | Power p | Additive (= Shin, = wpo for n = 2) | Multiplicative |
|---|---|---|---|---|---|---|
| −110 / −110 | 1.047619 | 1.100000 | 0.500000 / 0.500000 | 0.500000 / 0.500000 | 0.500000 / 0.500000 | 0.500000 / 0.500000 |
| UK −175 / MSU +150 | 1.036364 | 1.080123 | 0.618348 / 0.381652 | 0.620257 / 0.379743 | 0.618182 / 0.381818 | 0.614035 / 0.385965 |
| −1000 / +600 | 1.051948 | 1.290994 | 0.885662 / 0.114338 | 0.895342 / 0.104658 | 0.883117 / 0.116883 | 0.864198 / 0.135802 |
| shin README decimals [2.6, 2.4, 4.3] | 1.033840 | 1.053174 | 0.372429 / 0.404131 / 0.223440 | 0.372984 / 0.405107 / 0.221908 | 0.373335 / 0.405387 / 0.221278 (additive; Shin differs for n = 3) | 0.372026 / 0.403028 / 0.224946 |

`test_devig.py` should assert these values to 1e-6 and cross-check against penaltyblog `ODDS_RATIO` (dev dependency, MIT). For −110/−110, c equals π exactly, since p = 0.5 gives c = r/(1 − r) [computed].

**Which methods correct the favourite–longshot bias (FLB)?**
- **Multiplicative: no.** It implicitly assumes no FLB. Goto et al. (2026, preprint) say multiplicative "implicitly assumes β = 1". They estimate FLB in all five bookmakers they studied (fitted power constant β 1.06–1.15, 90,014 football matches 2012–2024) and count Shin, power and their OO-EPC as FLB-correcting ([arXiv 2604.17194](https://arxiv.org/html/2604.17194)).
- **Power, Shin, odds ratio: yes.** Each takes more margin, in probability terms, from the longshot than multiplicative does. In the −1000/+600 row the longshot's fair probability is 0.1358 (multiplicative), 0.1169 (additive/Shin), 0.1143 (odds ratio) and 0.1047 (power) [computed]. This is the FLB direction. The size of the correction is power > odds ratio > additive here.
- **Additive (≡ wpo, ≡ Shin for n = 2): partly.** It removes an equal absolute margin per outcome, which is proportionally more from the longshot. The `implied` vignette says `wpo` applies the margin "in a way that … reflects the favorite-longshot bias".
- **Evidence gap:** the odds-ratio method appears in neither CKI 2017 nor Goto et al. 2026. No peer-reviewed log-loss comparison including it was found. **Add `fair_prob_or` (and `or_c`) to the snapshot schema (section 3.2)**, and include it in the decision-9 NCAAB log-loss/Brier comparison alongside power, Shin/additive and multiplicative. Exchanges show FLB as well (Bürgi et al., section 1.5), so run the same comparison on exchange ask pairs.

### A6. Unattended operation: heartbeat, missed-job alerts, host clock (extends sections 2.4, 2.6, 3.1)

**What fails silently today:** a dead process, a job that misfires past `misfire_grace_time`, a job skipped because a previous run still holds `max_instances`, a Mac asleep or off (launchd does not run jobs missed while powered off, section 2.6), and a drifting clock.

**APScheduler 3.x hooks** ([events module](https://apscheduler.readthedocs.io/en/3.x/modules/events.html), [user guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html))
- `scheduler.add_listener(fn, EVENT_JOB_ERROR | EVENT_JOB_MISSED | EVENT_JOB_MAX_INSTANCES | EVENT_SCHEDULER_SHUTDOWN)`.
  - `EVENT_JOB_MISSED`: "A job's scheduled run did not happen".
  - `EVENT_JOB_MAX_INSTANCES`: the executor rejected a run at the concurrency limit.
  - `JobExecutionEvent` carries `job_id`, `scheduled_run_time`, `exception` and `traceback`.
- With `coalesce=True`, "No misfire events will be sent for the 'bypassed' runs". Because of that, in-game interval jobs must log their own per-minute coverage rather than rely on misfire events.
- The listener writes one JSON line per event to `ops/events/{YYYY-MM-DD}.jsonl` (in the run record) and raises an alert for any event on an MSU-game job.

**Dead man's switch (external, so a dead Mac still produces an alert)**
- Healthchecks.io: each check has a ping URL. A check goes "Late" after its period and "Down" after the grace time, then alerts. `/start` and `/fail` signals measure run time and failures ([docs](https://healthchecks.io/docs/)).
  - Hobbyist plan: "$0 / month", "Monitor 20 jobs", "100 log entries per job" ([pricing](https://healthchecks.io/pricing/)).
  - The software is BSD-3-Clause and can be self-hosted ([GitHub](https://github.com/healthchecks/healthchecks)), but a self-hosted instance on the same Mac defeats the purpose.
  - The hosted service needs an account, so this is a **decision for Aldemir (new decision 10)**. Ping URLs are secrets ("Treat UUIDs and Ping keys as secrets"): store them like API keys, outside git.
- Proposed checks (well under 20):
  1. `scheduler-heartbeat`: a ping every 300 s from an interval job, period 300 s, grace 600 s;
  2. `daily-planner`: cron, 10:00 UTC, grace 1,800 s;
  3. `msu-ingame`: `/start` at T − 10,800 s, a ping each completed minute, success at final + 1,800 s, grace 180 s;
  4. `polymarket-1m-backfill`: one ping per game when the 60 s backfill (section 2.4 (a)) has verified coverage;
  5. `raw-sync`: the daily Drive sync (A7).
- **Deadline watchdog** (in-process, daily): for each game with T + 1 d ≤ now, check the 60 s backfill coverage. Alert at T + 3 d. Escalate (alert repeated hourly) from T + 5 d until the hard deadline T + 6 d − 10,800 s (section 2.4). After that, mark the game `pm_1m_lost` in `completeness_weekly`.

**Host clock**
- macOS syncs time with the `timed` LaunchDaemon (since 10.13) against the server in `/etc/ntp.conf`, normally `time.apple.com`, and uses one server ([Eclectic Light, 2025-05-21](https://eclecticlight.co/2025/05/21/system-time-clocks-and-their-syncing-in-macos/)). The CIS macOS 14 benchmark audits drift with `sntp` and fails beyond **270 s** ([Tenable CIS item](https://www.tenable.com/audits/items/CIS_Apple_macOS_14.0_Sonoma_v1.0.0_L1.audit:921dd44fca8f6805422fcff73632743d)). That limit is far looser than our need.
- This Mac on 2026-10-18 (macOS 26.5.1): `sntp -t 5 time.apple.com` reported **+0.078 s ± 0.034 s** [probed; report-only, clock not changed].
- **Design:**
  - an hourly job runs `sntp -t 5 time.apple.com` (report only, never `-s`, which needs root and changes system settings);
  - it stores `host_clock_offset_s` and its ± in the manifest of every run;
  - alert if |offset| > 1 s (project choice: 1 s is the resolution C-13 and close selection need);
  - add rule C-19: flag snapshot rows fetched while |offset| > 1 s;
  - the manifest already stores response headers, so each server `Date` header (1 s resolution) gives a second, independent offset estimate per request.

### A7. Google Drive limits, sync behaviour and a second copy (extends sections 3.1, 3.2)

**Documented limits**
- Uploads: "Each user can upload and copy 750 GB to Drive within 24 hours". Maximum file size 5 TB ([Workspace limits](https://knowledge.workspace.google.com/admin/drive/storage-and-upload-limits-for-google-workspace?visit_id=639278929749320213-279268071&rd=1); same 750 GB figure in the [Drive API limits](https://developers.google.com/workspace/drive/api/guides/limits), which also lists per-minute API quotas and HTTP 403/429 rate-limit errors).
- Items: up to 500 million items created per user, and **500,000 items directly inside one folder** (My Drive root exempt) (Workspace page). Whether these Workspace figures apply unchanged to a personal Google account is **unverified**.
- **Storage: a personal account gets 15 GB shared across Gmail, Drive and Photos.** Over quota, "You can't upload new files" ([Google One help](https://support.google.com/googleone/answer/9312312)). This is the binding limit for a free account, not the 750 GB/day cap.
- **Drive for desktop:** streamed files "are primarily stored in the cloud". Mirrored files are kept both locally and in the cloud. The help page says nothing about file counts or sync speed ([stream & mirror](https://support.google.com/drive/answer/13401938)). Files that fail to sync go to a local "Lost and Found" folder (`~/Library/Application Support/Google/DriveFS/lost_and_found/<account_token>` on macOS), and "If you disconnect your account, any files stored in your 'Lost and Found' folder are lost" ([fix problems](https://support.google.com/drive/answer/2565956?hl=en&co=GENIE.Platform%3DDesktop)). No Google page found documents behaviour with very many small files, so the "slow on many small files" note in section 3.2 stays **unverified**.

**Volume estimate** [computed; response sizes are assumptions to be measured in B2]
- Files per MSU game, one file per request:
  - Polymarket 2 requests × 330 polls = 660;
  - Kalshi, if enabled, 7 × 330 = 2,310;
  - ESPN live, if approved, about 22;
  - Odds API in-play (option C or A2), 130.
  That is about 0.8k–3.1k files per game, or 28k–110k per season for 35 MSU games, plus roughly 10k pre-game files across 424 Big Ten games.
- At an assumed 2–50 KB per gzipped body this is about 0.1–6 GB per season. That fits 15 GB only if Gmail and Photos leave room. Measure the real size in the first B2 week, and decide on a paid Google One tier if needed (price not checked in this pass).

**Design change (proposal; keeps "raw first, never modified")**
1. **Primary copy on local disk.** `raw_store.py` writes each body and manifest line to a local directory (e.g. `~/msu-alpha-3-data/markets/raw/...`, same layout as section 3.1) and `fsync`s before parsing.
2. **Daily bundle.** At 06:00 UTC, a job packs the previous UTC day per source into one uncompressed `tar` of the existing `.json.gz` members, `raw/{source}/{YYYY}/{MM}/{YYYY-MM-DD}.tar`, plus that day's manifest. Bodies are not altered. It writes `{date}.tar.sha256`. That gives about 7 sources × 156 season days ≈ 1,100 Drive files per season instead of about 100k, and no folder comes near 500,000 items.
3. **Offsite copy.** Copy the bundles and the Parquet layer to `MyDrive/MSU-Alpha-3/markets/`. After Drive for desktop reports the upload, re-read the file through the Drive path, re-hash it, and ping the `raw-sync` check (A6). A mismatch leaves the local copy in place and alerts.
4. **Second local copy on different media.** Time Machine to an external drive (hourly for 24 h, daily for a month, weekly after; [Apple](https://support.apple.com/en-us/104984)). Together with Drive this meets the 3-2-1 rule: "Keep 3 copies … 2 different media types … 1 copy offsite" ([CISA](https://www.cisa.gov/sites/default/files/publications/data_backup_options.pdf)).
5. **Monthly restore test.** Pick a random day, extract the bundle from Drive, verify each member's sha256 against the manifest, and rebuild that day's snapshot rows. Record the result in the run record.

Local raw files are pruned only after both the Drive copy and a Time Machine backup have been verified, and never within 30 days. Pruning is a later B2 decision.

### A8. Paid alternatives to The Odds API (extends section 7)

All prices were read on 2026-10-18. "Vendor" means the vendor's own page; "directory" means sportsapis.dev, a third-party directory with disclosed affiliate links, so treat it as indicative.

| Vendor | NCAAB odds | Historical / timestamped | 1H / props | Published price | Source |
|---|---|---|---|---|---|
| **The Odds API** (baseline) | Yes | Timestamped snapshots (600 s, then 300 s) from 2020-11-16; 1H/props from 2023-05-03 | Yes | $30 / $59 / $119 / $249 per month | Section 1.4 |
| SportsDataIO | Pre-game, alternate (incl. first half) and in-game odds endpoints, with **line-movement** endpoints; "Sportsbook Group" endpoints "Access Required" ([NCAAB docs](https://sportsdata.io/developers/api-documentation/ncaa-basketball)) | History depth not stated; archive ("Vault") via sales | First-half via alternate markets; props not on the page read | Discovery Lab "Odds" $99/mo or $599/yr; Fantasy + Odds $149/mo; 100–1,000 calls/day; **data delayed one day**; "Not licensed for commercial redistribution". The free trial is scrambled data ([getting started](https://sportsdata.io/developers/getting-started)) | Vendor |
| SportsGameOdds | "College Basketball" in all plans | "Historical data" from Pro; the historical page describes **open/close per book** (`includeOpenCloseOdds`), not full movement; depth not stated ([historical](https://sportsgameodds.com/use-cases/historical-odds-data-api)) | Not stated on pages read | Amateur free (2,500 objects, 10 min updates); Rookie $99; **Pro $299** (historical); All-Star custom ([pricing](https://sportsgameodds.com/pricing)) | Vendor |
| OpticOdds | Not stated ("25+ sports and 400+ leagues") | Every price change with millisecond timestamps, REST or bulk export; depth "to when we first started collecting" ([historical](https://opticodds.com/historical-odds)) | Not stated | Contact sales | Vendor |
| Unabated | NCAAB listed in "Concierge Advanced" | No archive described | Not stated | Concierge $799/mo (pro leagues only); **Concierge Advanced $2,999/mo** (incl. college basketball) ([directory](https://sportsapis.dev/apis/unabated), checked Oct 2026) | Directory |
| OddsJam | Claimed | "Historical odds database" referenced; depth unknown | Not stated | Not published; sales form; directory tier "$1,000+/month" ([directory](https://sportsapis.dev/apis/odds-jam)). `oddsjam.com/odds-api` returned HTTP 403 | Directory |
| Sportradar | NCAAB odds coverage not confirmed | Historical odds not documented on the page read | Props list excludes NCAA | Not published; trials via marketplace; directory tier "$1,000+/mo" ([directory](https://sportsapis.dev/apis/sportradar)) | Directory |
| OddsPapi | NCAAB not named | Claims a **free** `/historical-odds` endpoint storing every line move, at most 3 books per call; depth "from our archive ingestion start date" ([vendor blog](https://oddspapi.io/blog/?p=2824)) | Not stated | Free tier with a key; licence terms not stated | Vendor blog (marketing; **unverified**) |
| Action Network PRO | — | No official API or export found; only third-party scrapers (ToS risk) | — | — | Search only **(unverified)** |

**Reading.** No alternative found offers NCAAB 1H and prop history with timestamps at a published price below The Odds API.
- SportsDataIO's $99/month odds tier is the only published-price option with NCAAB line-movement endpoints, but its history depth is unstated and its data arrives a day late. That is fine for backfill and useless for live closes.
- SportsGameOdds' $299 Pro has open/close only.
- OpticOdds, OddsJam, Sportradar and the SportsDataIO archive need sales quotes.
- OddsPapi's free history is the one claim worth a test call if Aldemir wants a $0 cross-check, but it needs a key (an account) and its NCAAB coverage and terms are unknown.

The section 7.3 claim that The Odds API is "the only source" should therefore read: **"the cheapest source found with published prices for timestamped multi-book NCAAB closes, 1H lines and props since 2023-24"**. The $269 recommendation stands. Optional before buying: ask SportsDataIO what NCAAB history depth Discovery Lab includes, and ask OpticOdds for a quote, to confirm nothing cheaper exists.

### A9. New open items (append to section 10)

10. Kalshi: whether a spread contract counts as "final game score" in the abandoned-game clause (A1). Settlement rules of `KXNCAAMB1HWINNER` (ACHIEVEMENTS.pdf). Whether 1H/2H series list for regular-season Big Ten games.
11. Polymarket: rules for abandoned games and for 1H companion markets (A1).
12. FanDuel, BetMGM and Caesars primary basketball house rules (A1).
13. The Odds API: date `kalshi`/`polymarket` entered historical data; whether exchange prices are ask, mid or last; whether the vendor holds exchange licences (A2).
14. Becker archive: max `created_time` for `KXNCAAMB*`; a dataset licence statement from the author (A3).
15. Big Ten men's basketball availability-report deadline from the conference's own policy text (A4).
16. Cheung (2015) and Buchdahl's *Wisdom of the Crowds* PDF: open them and confirm the odds-ratio attribution (A5).
17. Whether the Workspace item limits apply to a personal Google account; real raw volume per game (A7).
18. SportsDataIO NCAAB history depth; OpticOdds quote (A8).

**New decisions for Aldemir (one line each):**
- 10: create a free Healthchecks.io account for external liveness alerts, or accept in-process alerts only (A6).
- 11: approve the 36 GB Becker archive download for a 2025-26 Kalshi NCAAM backfill, subject to decision 5 (A3).
- 12: approve the `t-avail` (T − 9,000 s) and early-season `t-6h` snapshots (A4).
- 13: approve the local-primary + daily-bundle + Time Machine storage change (A7).

### Sources for these additions

All opened 2026-10-18 unless marked.
- Kalshi: https://assets.kalshi.com/contract_terms/BASKETBALLSPREADS.pdf ; https://assets.kalshi.com/contract_terms/BASKETBALLTOTALS.pdf ; https://assets.kalshi.com/contract_terms/BASKETBALLGAMEWIN.pdf ; https://kalshi-public-docs.s3.amazonaws.com/kalshi-data-terms-of-service.pdf ; [probed] https://external-api.kalshi.com/trade-api/v2/series/KXNCAAMBSPREAD , …/series/KXNCAAMBTOTAL , …/series/KXNCAAMBGAME , …/series?category=Sports&tags=Basketball , …/events?series_ticker=KXNCAAMBGAME&limit=1&with_nested_markets=true
- Polymarket: [probed] https://gamma-api.polymarket.com/events/slug/cbb-uk-mst-2025-11-18
- Sportsbook rules: https://massgaming.com/wp-content/uploads/DraftKings-House-Rules-8.18.25.pdf ; https://help.playatgila.com/en/general-information/sports-house-rules/basketball-wager-types-and-rules ; https://www.peppermillreno.com/gaming/race-sportsbook/house-rules/ ; https://www.actionnetwork.com/education/prop-betting-rules-what-happens-if-player-doesnt-play ; https://www.legalsportsreport.com/how-to-bet/overtime-rules/ **(HTTP 403; not read)**
- The Odds API: https://the-odds-api.com/sports-odds-data/bookmaker-apis.html ; https://the-odds-api.com/sports-odds-data/update-intervals.html ; https://the-odds-api.com/terms-and-conditions.html ; https://the-odds-api.com/liveapi/guides/v4/ ; https://the-odds-api.com/historical-odds-data/
- Kalshi data licensing: https://www.financemagnates.com/fintech/kalshi-sells-prediction-market-data-to-fox-expanding-beyond-trading/
- Datasets: https://github.com/jon-becker/prediction-market-analysis (plus GitHub API reads of LICENSE, README.md, docs/SCHEMAS.md, src/indexers/kalshi/client.py, commits) ; [probed HEAD] https://s3.jbecker.dev/data.tar.zst ; https://huggingface.co/datasets/SII-WANGZJ/Polymarket_data ; https://docs.allium.so/historical-data/predictions/kalshi ; https://docs.dune.com/data-catalog/curated/prediction-markets/kalshi/overview ; https://archive.pmxt.dev/ **(connection refused; unverified)**
- Line movement and availability: https://api.crossref.org/works/10.1111/0022-1082.155346 ; https://ideas.repec.org/a/eee/finlet/v13y2015icp130-136.html ; https://verso.uidaho.edu/esploro/outputs/journalArticle/How-quickly-do-markets-incorporate-new/996683436201851 ; https://ideas.repec.org/a/inm/ormnsc/v70y2024i12p8583-8611.html ; https://data.mendeley.com/datasets/pdsxx5dgbw/1 ; https://www.espn.com/college-football/story/_/id/45968809/big-12-issue-player-availability-reports-first ; https://www.si.com/college/indiana/basketball/malik-reneau-not-listed-on-indiana-injury-report-for-washington-game-01jn9p5vxc7s ; https://www.cbssports.com/college-football/news/big-12-to-mandate-player-availability-reports-for-football-basketball-starting-in-2025-26 ; https://bigten.org/sports/2023/11/5/MBB_Reports.aspx **(HTTP 500; unverified)**
- De-vig: https://cran.r-project.org/web/packages/implied/vignettes/introduction.html ; https://github.com/opisthokonta/implied (GitHub API reads of R/implied_probabilities.R and DESCRIPTION) ; https://github.com/martineastwood/penaltyblog (GitHub API read of penaltyblog/implied/implied.py) ; https://arxiv.org/html/2604.17194 ; https://www.football-data.co.uk/The_Wisdom_of_the_Crowd_updated.pdf **(HTTP 429; unverified)**
- Operations: https://apscheduler.readthedocs.io/en/3.x/modules/events.html ; https://apscheduler.readthedocs.io/en/3.x/userguide.html ; https://healthchecks.io/docs/ ; https://healthchecks.io/pricing/ ; https://github.com/healthchecks/healthchecks ; https://eclecticlight.co/2025/05/21/system-time-clocks-and-their-syncing-in-macos/ ; https://www.tenable.com/audits/items/CIS_Apple_macOS_14.0_Sonoma_v1.0.0_L1.audit:921dd44fca8f6805422fcff73632743d ; [probed] `sntp -t 5 time.apple.com`
- Storage: https://knowledge.workspace.google.com/admin/drive/storage-and-upload-limits-for-google-workspace ; https://developers.google.com/workspace/drive/api/guides/limits ; https://support.google.com/googleone/answer/9312312 ; https://support.google.com/drive/answer/13401938 ; https://support.google.com/drive/answer/2565956 ; https://support.apple.com/en-us/104984 ; https://www.cisa.gov/sites/default/files/publications/data_backup_options.pdf
- Vendors: https://sportsdata.io/developers/api-documentation/ncaa-basketball ; https://sportsdata.io/developers/getting-started ; https://sportsgameodds.com/pricing ; https://sportsgameodds.com/use-cases/historical-odds-data-api ; https://opticodds.com/historical-odds ; https://sportsapis.dev/apis/unabated ; https://sportsapis.dev/apis/odds-jam ; https://sportsapis.dev/apis/sportradar ; https://sportsapis.dev/apis/sportsdata-io ; https://oddspapi.io/blog/?p=2824 ; https://oddsjam.com/odds-api **(HTTP 403; not read)**
