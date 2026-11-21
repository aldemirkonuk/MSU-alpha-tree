# Data-source assessment: Public-ESPN-API, Sports-Reference, Massey, KenPom API, EvanMiya

Prepared 18 Oct 2026 for a private, non-commercial research project on Michigan State men's basketball (NCAA D-I). I opened every page cited here, either directly or through a fetch tool. If I could not open a page, or a claim rests on secondhand text, I mark it **unverified**. This is a reading of published terms, not legal advice.

---

## 1. pseudo-r/Public-ESPN-API

### What it is
- Mainly **documentation of ESPN's undocumented JSON endpoints**. The README says: "This is documentation for ESPN's undocumented public API. I am not affiliated with ESPN."
- It also ships **reference code**: a Python `ESPNClient` (`espn_service/clients/espn_client.py`), a Django REST/Celery ingestion service (`espn_service/`), and an NHL service (`nhl_service/`). It is **not a pip-installable client library** and there are no GitHub releases.
- It holds machine-generated catalogs built from ESPN's own WADL files (`sports.core.api.espn.com/v2/application.wadl` and `/v3/...`). Counts are 412 v2 and 97 v3 routes (`docs/core-endpoints.md`, `docs/data/core-endpoints.json`), plus 51 recorded live probes (`docs/data/live-probes.json`).

### License, activity, popularity
| Item | Value |
|---|---|
| License | MIT ("Copyright (c) 2026 Public-ESPN-API contributors") |
| Last commit | **2026-09-30** ("docs: clarify project scope and remove app promotions") |
| Recent activity | 5 commits on 2026-09-30 (endpoint audit, scoreboard-range workaround, PostgreSQL CI); earlier bursts 2026-07-04, 2026-04-07, 2026-03-02 to 03-26. History starts 2023-05-07. Single main author (Joseph Wilson). |
| Stars / forks / watchers | 663 / 81 / 25, as rendered on the GitHub page on 18 Oct 2026 |
| Open issues / PRs | 1 / 1 (#22, which the 2026-09-30 audit says was integrated manually) |
| CI | GitHub Actions + Codecov. The audit reports 200 ESPN tests passed and about 85.65% coverage. |

### Men's college basketball (`basketball/mens-college-basketball`): what it documents
| Data | Endpoint documented | Where |
|---|---|---|
| Scoreboard | `site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?dates=YYYYMMDD&groups=50&limit=500` | README, basketball.md |
| Game summary (box, PBP, win prob, odds, officials, venue) | `.../summary?event={id}` | basketball.md, college_sports.md |
| CDN game package | `cdn.espn.com/core/{sport}/game?xhr=1&gameId={id}` (also boxscore, playbyplay, matchup) | README, basketball.md (examples use `nba`) |
| Play-by-play (Core) | `sports.core.api.espn.com/v2/.../events/{id}/competitions/{id}/plays`, plus `/plays/{play}/personnel` | basketball.md, core-endpoints.md |
| Win probability | `.../competitions/{id}/probabilities` | README, core-endpoints.md |
| Odds / predictor / ATS | `.../competitions/{id}/odds`, `/predictor`, `/powerindex`; `seasons/{y}/types/{t}/teams/{id}/ats`, `/odds-records`; `seasons/{y}/futures` | README "Betting & Odds" |
| Officials | `.../competitions/{id}/officials` | basketball.md |
| Rosters | Site `teams/{id}/roster`; Core `competitors/{id}/roster` | basketball.md, core-endpoints.md |
| Athletes | Core `athletes`, `athletes/{id}`, `/statistics`, `/statisticslog`, `/eventlog`; Common v3 `site.web.api.espn.com/apis/common/v3/sports/basketball/mens-college-basketball/athletes/{id}/{overview,stats,gamelog,splits}` (stated to work for NCAAM) | README, basketball.md |
| Team / competitor stats | Core `competitors/{id}/statistics`, `competitions/{id}/statistics`; Site `teams/{id}/leaders`, `statistics` | core-endpoints.md, basketball.md |
| Rankings | Site `.../rankings` (AP and Coaches); Core `rankings` | college_sports.md |
| BPI / power index | Core `seasons/{y}/powerindex`, `/powerindex/leaders`, `/powerindex/{teamId}` | basketball.md, college_sports.md |
| Bracketology | `sports.core.api.espn.com/v2/tournament/22/seasons/{y}/bracketology` | basketball.md |
| Venues, seasons, calendar, groups, coaches, recruiting | Core `venues`, `seasons`, `calendar`, `groups`, `coaches/{id}`, `recruiting` | basketball.md, README |
| Standings | `site.api.espn.com/apis/v2/...` (the `/apis/site/v2/` path returns a stub) | README |

### Spot-check (18 Oct 2026)
Test game: MSU at Michigan, 2026-03-08, ESPN event 401825568. MSU's ESPN team id is 127, confirmed by `teams/127/schedule?season=2026`, which returned "Michigan State Spartans" with 32 events. I made about 15 requests, spaced out.

| Claim in repo | Result |
|---|---|
| `summary?event=` returns full game data | **Confirmed.** HTTP 200. Keys include `boxscore`, `plays` (492), `winprobability` (488), `pickcenter` (DraftKings −10.5, O/U 152.5), `gameInfo` (3 officials, Crisler Center, attendance 12,707). Play objects include `coordinate` {x,y}, `participants`, `wallclock`, `shootingPlay`. |
| Core `.../plays` | **Confirmed.** 200, count 492. Items add `probability`, `personnel`, `alternativeText`. |
| Core `.../probabilities` | **Confirmed.** 200, count 488, with `homeWinPercentage`, `awayWinPercentage`, `tiePercentage`, `play` ref. |
| Core `.../officials` | **Confirmed.** 200, 3 officials with position "Referee". |
| Core `.../odds` | **Confirmed.** 200, 1 provider (DraftKings, "MICH -10.5"). |
| `seasons/{y}/powerindex` (BPI) | **Partly confirmed.** The list returned only 25 teams even with `limit=500`, with pageCount 1 and lastUpdated 2026-04-07. The per-team route `/powerindex/127` worked (BPI 18.7, rank 13th; fields include bpi, bpioffense, bpidefense, sor, chance-of-round values). The docs do not mention the 25-team cap on the list. |
| `groups=50&limit=500` is needed for the full slate (12 vs 36 events on 20260120) | **Confirmed exactly:** 12 vs 36. |
| Site `rankings` = "AP Poll + USA Today Poll" | Returned "AP Top 25" and "Coaches Poll" (label drift only). |
| basketball.md example `scoreboard?dates=20250320-20250323` (date range) | **Fails.** HTTP 400 `{"code":400,"message":"Failed to get events endpoint."}`. The README documents this range regression for MLB/NFL (issue #23), but the NCAAM example was not updated. |
| CDN `cdn.espn.com/core/mens-college-basketball/game?xhr=1&gameId=` | **Confirmed.** 200, `gamepackageJSON` with plays, winprobability, boxscore, pickcenter, gameInfo. |
| Venues, roster | 200 (venues count 1000; roster of 15 with height, weight, experience, injuries) |

### Quality rating
- **Completeness: high for the endpoint surface.** The WADL-derived catalog is far more complete than any hand-written list. NCAAM-specific pages are thin, though: most basketball examples use the NBA, and per-sport tables mix in irrelevant routes (casinos, circuits, manufacturers).
- **Accuracy: good, with gaps.** 8 of 10 checks matched. One example is broken (the date range), and one quirk is undocumented (the BPI list cap). The repo itself warns that "A route appearing in WADL does not guarantee public support", and its live probes cover NFL/NBA/MLB/NHL/EPL/CFB, **not NCAAM**.
- **Examples: plentiful curl examples.** Few NCAAM response schemas; `docs/response_schemas.md` is general.
- **Maintenance: active** (dated audit on 2026-09-30, CI, tests). It depends on one maintainer.
- **Overall: a good reference map. It is not a data product and has no stability guarantee.**

### Comparison with existing libraries (all use the same ESPN endpoints)
- **hoopR** (R; CRAN 3.1.0, published 2026-08-25; GitHub last commit 2026-10-18; MIT). It has about 70 `espn_mbb_*` wrappers, including `espn_mbb_game_all`, `espn_mbb_game_play`, `espn_mbb_game_probabilities`, `espn_mbb_game_odds`, `espn_mbb_game_official_detail`, `espn_mbb_game_play_personnel`, `espn_mbb_powerindex`, `espn_mbb_rankings`, `espn_mbb_venues`, `espn_mbb_team_season_statistics`, `espn_mbb_player_eventlog_v2`, and `espn_mbb_game_propbets`.
  - It also has **pre-built bulk PBP releases**: `load_mbb_pbp()` covers 2006–2026 (README), sourced from ESPN through `sportsdataverse/hoopR-mbb-data`.
  - Other functions: `ncaa_mbb_*`, `load_ncaa_mbb_lineups`, `torvik_ncaa_results`, and authenticated `kp_*` KenPom scrapers (R/kp.R: "Authenticated scrapers for kenpom.com").
  - hoopR already covers nearly every NCAAM endpoint the repo documents.
- **sportsdataverse-py** (Python; PyPI 0.1.4, uploaded 2026-09-01): Python counterpart with an `mbb` module.
- **CBBpy** (Python; PyPI 2.1.2, 2025-01-20; last commit 2025-01-20; Apache-2.0): "game ID, as far as CBBpy is concerned, is a valid **ESPN** game ID". It provides game info (including referees), box score, PBP, and season/date-range pulls. It uses ESPN, not Sports-Reference, and it is the least recently maintained of the three.
- **Net:** the repo adds endpoint discovery (WADL catalog, parameter lists, Core `$ref`/`.pvt` quirk notes) on top of hoopR, sportsdataverse-py and CBBpy. It adds no new data access.

### Terms
- **ESPN's site footer "Terms of Use" links to `https://disneytermsofuse.com/english/`** (Disney Terms of Use, "Last Updated: May 24, 2024"; covers products "branded Disney, ABC, ESPN ...").
  - The licence is granted "for your personal, noncommercial use only ... with no right to reproduce, distribute ... or transform any Disney Product, including in connection with any use, creation, development, modification, prompting, fine-tuning, training, testing, benchmarking or validation of any artificial intelligence or machine learning tool ..." (the clause defines this as "AI Tool").
  - Restriction B.x prohibits users to "access, monitor, copy or extract the Disney Products using a robot, spider, script, or other automated means, including, for the avoidance of doubt, for the purposes of creating or developing any AI Tool, data mining or web scraping or otherwise compiling, building, creating or contributing to any collection of data, data set or database ..." (exception for public search engines only).
  - B.viii prohibits commercial or business use "whether or not for profit".
- ESPN's `www.espn.com/robots.txt` disallows `*/boxscore?` and `*/playbyplay?` for all agents and blocks named AI crawlers (GPTBot, anthropic-ai, CCBot, Google-Extended, and others). The API hosts' own robots files were not checked (unverified).
- **What the repo says about terms:** the README says "Use responsibly and follow ESPN's terms of service". PROJECT_SCOPE.md says:
  - "An endpoint being reachable without authentication does not establish permission to automate requests, scrape, store, publish, or redistribute its responses."
  - "The repository's software license applies only to contributions that its authors are entitled to license. It does not grant rights to third-party APIs, datasets ..."

### Verdict
- **Useful for:** a field dictionary and endpoint map. It shows which fields exist for a given game:
  - shot x/y coordinates
  - per-play win probability
  - officials and per-play personnel
  - book odds
  - BPI components
  - Core `$ref` structure and paging quirks (`groups=50`, `.pvt`, the date-range 400).

  That helps when designing schemas or mapping hoopR/CBBpy columns to their sources.
- **Does not change:** the legal position. Using the repo's client, hoopR or CBBpy to pull ESPN JSON is still automated access to a Disney product. Disney's terms bar automated extraction for building data sets or databases, and bar ML/AI training or validation. Under those terms, any scripted ESPN collection is a **terms risk regardless of which wrapper is used**. Non-commercial status reduces business exposure but is not an exception in the text. The lower-risk path is to read ESPN pages manually, or to get permission or a licensed feed. The project would have to accept any residual risk explicitly.

---

## 2. Sports-Reference (sports-reference.com/cbb)

### Terms of Use (`/termsofuse.html`, "Last Updated: May 19, 2023")
- **Guiding principle (Sec. 5):** "sharing, using, modifying, repackaging, or publishing data found on individual SRL webpages is welcomed, whether for commercial or non-commercial purposes", with credit to SRL, and it "must not violate any express restrictions set forth in this Section 5, especially the restrictions set forth in subparts 5(i) and 5(j)". The rendered list is not lettered, so which bullets are (i) and (j) is **unverified**.
- **Automated access / data mining:** "without our express written permission, use any automated means to access or use the Site, including scripts, bots, scrapers, data miners, or similar software, in a manner that adversely impacts site performance or access".
- **Competing databases:** prohibits using Content "(i) to create any database, archive, or other data store that competes with or constitutes a material substitute for the services or data stores offered on the Site or by the Site's Data Providers or (ii) to provide any service that competes with ..."
- **AI/ML (exact text):** "copy or use any material or Content from the Site, including without limitation any statistics, data, text, graphics, or images, for purposes of training, fine-tuning, prompting, or instructing artificial intelligence models or technologies in any manner, including without limitation for purposes of (i) generating answers, text, scores, statistics, notes, graphics, images, or any other output; or (ii) supporting machine learning methods used to predict, classify, label, or score inputs into the models".
- **Does the AI/ML restriction apply regardless of collection method?** Yes, on its wording. It restricts "copy or use any material or Content" and is not limited to automated access, so it covers manual copy-paste, the SHARE tool, and CSV export equally. The automated-access bullet is a separate restriction, and it applies only where access "adversely impacts site performance or access". Note the scope of clause (ii): it reaches any ML model that predicts, classifies, labels or scores, not just generative AI.
- **Manual copy-paste / CSV for personal research:** the Terms contain **no clause that names copy-paste or CSV export**.
  - The welcomed-use principle above plus the Sharing page cover this. `/sharing.html` describes the SHARE link to "slice and dice any data table on the site and re-use it elsewhere" and says "You are free to use this data anywhere, we would just ask that you include the citation".
  - So: manual copy or export for **non-ML personal research** (descriptive stats, charts) appears permitted with attribution. Using that data **as input to train or run an ML model is not**, absent written permission.
  - The "Get table as CSV" menu item is rendered by JavaScript and did not appear in the fetched HTML. Its exact label is **unverified**.
- **Data Use page (`/data_use.html`):**
  - Repeats the clauses and summarises: "you should not create websites or tools based on data you scrape ... or use our data to train generative artificial intelligence models without our permission."
  - Notes: "copyright law is clear that facts cannot be copyrighted, so you are free to reuse facts found on this site in accordance with copyright laws."
  - Custom datasets cost a minimum of $5,000.

### Bot-traffic policy and the 429 page
- **`/bot-traffic.html`** (Oct 26, 2022; updated May 29, 2024):
  - Blocks "FBref and Stathead sites more often than ten requests in a minute" and "our other sites more often than twenty requests in a minute. This is regardless of bot type and construction and pages accessed. If you violate this rule your session will be in jail for up to a day."
  - No API: "As part of our agreements with them we can not provide the data available as a download on our site."
- **`/429.html`** (older copy, footer ©2000–2023): lists "You accessed more than thirty pages in less than a minute" and says "we block traffic that we think is from a bot for an hour". These numbers are inconsistent with the bot page; treat the bot page (20/min, up to a day) as current.
- **robots.txt:** disallows GPTBot entirely, plus `/cbb/boxscores/index.cgi?*`, `/cbb/players/*/splits*`, `/cbb/req/`, `/cbb/short/`, `/cbb/nocdn/`.

### Stathead
- Stathead is carved out of the SR "Site" definition and governed by its own terms (`/stathead/termsofuse.html`, "Last Updated: November 25, 2020").
- Those terms repeat the same automated-access, competing-database and "limited, personal ... license" language.
- **The fetched Stathead terms contain no AI/ML clause** (0 matches for "artificial", "machine learning", "intelligence").
- **Does Stathead export change the terms?** It grants no extra right to redistribute or build a database, and the bot limit is tighter (10/min). The absence of an AI clause is a gap in an older document, not a grant. The data are the same SR or third-party-licensed data (the bot page says data providers bar downloads). Treat Stathead exports under the SR AI/ML restriction unless SR confirms otherwise in writing. Stathead pricing was not checked.

### Python wrappers
| Package | Status |
|---|---|
| **sportsipy** (roclark) | Last PyPI release 0.6.0 on **2021-01-07**; last commit 2022-03-20. Open issue **#807 "IMPORTANT: Repo no longer maintained"** (Nov 18, 2024). 90 open issues, including NCAAB parsing bugs: **#774** "NCAAB Boxscore and Boxscores returning blank for valid inputs" (Jan 2023), **#757** NCAAB Boxscore winner/loser fields not populating (Nov 2022), **#745** NCAAB height returns None (Aug 2022), and #781 "Did sports reference completely change their site?". **Not usable.** |
| **basketball-reference-scraper** (vishaalagartha) | PyPI 2.0.0 on 2024-03-16; last commit 2024-03-15. **NBA only** (basketball-reference.com). Throttles itself to SR's 20 req/min. Not applicable to CBB. |
| CBB-specific | No maintained SR-CBB scraper was found. **CBBpy uses ESPN, not SR.** hoopR's college sources are ESPN, stats.ncaa.org, KenPom and Torvik, not SR. |

### Verdict
SR/CBB is fine for **manual lookup and cited, non-ML descriptive use**. Do not scrape it, and do not feed SR-derived data (copied, exported or Stathead) into any ML or prediction model without written permission from SRL.

---

## 3. Massey Ratings (college basketball)

### masseyratings.com terms
- Direct fetches of the home page, `/cb/compare.htm`, `/about.php` and others returned **403 (Cloudflare challenge)**.
- `robots.txt` (fetched) disallows `/cgi-bin/`, `/data/` and **`/scores.php*`**.
- `/info.php` (Copyright and Terms sections) was read through a fetch tool that returned excerpts, not the full page:
  - "Copyright © 2026 Massey Ratings, LLC"
  - "Massey Ratings LLC grants you a non-exclusive, non-transferable, limited right to directly view and link to the Website."
  - "Unauthorized reproduction, in whole or in part, in any form or medium, is strictly prohibited."
  - AI/ML: "Use of this website's content to train, fine-tune, or develop artificial intelligence, machine learning models, or large language models is expressly prohibited without prior written consent."
  - "You may view the Content solely for your personal, non-commercial use."
  - No explicit scraping clause.

  Because the text came through a summarising tool, **treat the exact wording as unverified** until you check it in a browser.
- `/cf/aboutcomp.htm` (football comparison, revised 2006) describes the comparison as ordinal ranks from roughly 100 systems, sorted by consensus, included with the system owners' permission. No licence statement. The CB version of the page could not be fetched (unverified).

### Kaggle March Machine Learning Mania 2026
Read in a browser on the Data and Rules tabs.
- **MMasseyOrdinals.csv** (Data Section 4, "Public Rankings"): "weekly team rankings (men's teams only) for dozens of top rating systems - Pomeroy, Sagarin, RPI, ESPN, etc., since the 2003 season". Columns:
  - `Season`
  - `RankingDayNum` (0–133; "the first day that it is appropriate to use the rankings"; 133 = final pre-tournament)
  - `SystemName` (usually a 3-letter code)
  - `TeamID`
  - `OrdinalRank`

  The description says "The information was gathered by Kenneth Massey and provided on his rankings page." The exact system list and the last season included were not enumerated (**unverified**; presumably through 2026).
- **Licence / rules:** the Data page metadata shows "Attribution 4.0 International (CC BY 4.0)". Rules section 7 "DATA ACCESS AND USE" says "Open Source - CC-BY 4.0". The General Rules say:
  - "You may access and use the Competition Data for any purpose, whether commercial or non-commercial, including for participating in the Competition and on Kaggle.com forums, and for academic research and education."
  - However, the "Data Security" clause says: "You agree not to transmit, duplicate, publish, redistribute or otherwise provide or make available the Competition Data to any party not participating in the Competition."

  The two clauses conflict on redistribution, so **use it internally and do not re-share the file**.
- Downloading requires a Kaggle login and accepting the rules.
- The CC BY grant is Kaggle's and the sponsor's. Whether it overrides the system owners' rights in the underlying ranks is untested, which is another reason to keep use internal and cited.

### Standalone Kaggle dataset `masseyratings/rankings`
**It exists.** Read through the Kaggle public API.
| Item | Value |
|---|---|
| Title | "College Football/Basketball/Baseball Rankings" |
| Owner / creator | `masseyratings` / "Masseycre", apparently Kenneth Massey's account (not independently verified) |
| Licence | **"Unknown"** |
| Last updated | 2022-02-12 (v5) |
| CB files | cb2001–cb2021 (`cb/cb2001.csv` … `cb/cb2021-partial.csv`, plus `cb2020.csv`, `cb2021.csv`) |
| Fields | sportyear, team id, team name, system code, system name, date (yyyymmdd), ordinal rank |
| Description | "I have compiled weekly rankings of college teams, and am making the archived data public ... please reference masseyratings.com in your research." |

Also found: `aadhafun/massey-ncaa-ratings-2025`, a third-party upload (Apache 2.0 label, 19.5 KB, 2025-03-05). Its provenance is doubtful; avoid it.

### github.com/Carrigan/mncaa
- A Python library that downloads Massey **game-score** CSVs, not rankings. It requests `masseyratings.com/scores.php?s=cb{year}&sub=11590...` for 2000–2013 and builds game lists.
- GPL-2.0. **Last commit 2014-03-18. Abandoned.**
- Its URL path is now disallowed by robots.txt. Do not use it.

### Verdict: lawful ways to use Massey composite rankings
1. **Kaggle MMasseyOrdinals.csv** (2003–present): best option. Use it under the competition rules for internal academic research, cite Kenneth Massey and Kaggle, and do not redistribute.
2. **`masseyratings/rankings`** on Kaggle (2001–2021): published by Massey's account with a request to cite him, but licence "Unknown". Use it with attribution, internally.
3. **Live site:** view manually only. No scraping. Massey's copyright notice bars reproduction and AI/ML use without written consent, so for anything beyond 1–2, especially current-season composite feeds, **email Massey for written permission**.

---

## 4. KenPom API and EvanMiya (short)

### KenPom API
- **Docs** (`/api-documentation.php`, via fetch tool): `GET https://kenpom.com/api.php?endpoint=<name>` with `Authorization: Bearer <key>`. An unauthenticated call returned HTTP 401 (verified).
- **Endpoints:** `ratings` (AdjEM, AdjOE/DE, tempo, luck, SOS, APL…), `archive` (by date or preseason), `four-factors`, `pointdist`, `height` (incl. experience, bench, continuity), `misc-stats`, `fanmatch` (daily game predictions: HomePred, VisitorPred, HomeWP, PredTempo, ThrillScore), `conf-ratings`, `program-ratings`, `teams` (coach, arena), `conferences`.
- **Team-level only:** no player stats and no play-by-play.
- **Price:** `/register-api.php` shows **$145.00/year** "for 12 months of API & kenpom.com access", with "all sales are final". **No free tier or trial is mentioned.** The user's description of it as "free" is **unverified**: it may reflect an existing paid subscription, or a promotion I could not see.
- **Rate limits:** no numbers published. API terms reserve the right to "throttle, rate-limit, suspend, or terminate access for excessive or abusive use".
- **API terms** (`/terms-api.php`, no effective date):
  - Permitted: "personal, non-commercial purposes", and explicitly "research, model building, and other hobby-related endeavors", "academic study".
  - Prohibited: making API data available on "any public-facing website, application, or database", redistributing data or credentials, bulk extraction "beyond rate limits", web apps, and commercial use.
  - Attribution is required for "Any analysis, visualization, model, or other derivative work".
  - AI/ML and caching are not mentioned.
- **Site terms** (`/terms.php`): no automated access; downloads for "personal and non-commercial use only"; "You cannot share your password".
- **Implication:**
  - The API is the sanctioned route for KenPom data in this project's models.
  - hoopR's `kp_*` site scrapers (which log in) should not be used instead.
  - Keep the data private and attribute kenpom.com.

### EvanMiya
Read in a browser at `evanmiya.com/subscribe` on 18 Oct 2026.
| Tier | Price | Includes |
|---|---|---|
| **Free** | $0 ("free forever", no card) | Full team ratings, player ratings for all D1, advanced player metrics, historical ratings back to 2009 |
| **Basic** | $2.50/mo ($30 billed yearly) | Free tier plus game predictions with Vegas odds, full transfer portal rankings, team chemistry and lineup breakdowns, lineup ratings across D1, **Export data to CSV** |
| Premium | $15/mo ($179.99/yr) | Player skill projections and grades, lineup grades and optimization, matchup previews, keys to victory, injury line adjustments, and more |
| Front Office Suite | Contact | NIL values, big board, and similar |

The monthly prices are list prices; the yearly toggle claims "Save 50%". No public API was found (unverified). The Terms (Google Doc linked from the site footer) say:
- "You may print or download to a local hard disk extracts for your personal and non-commercial use only".
- No distribution or storage "in any other website or other form of electronic retrieval system" without permission.
- No automated access "in a manner that adversely impacts site performance or access".
- "THIS IS AN INDIVIDUAL SUBSCRIPTION".
- No AI/ML clause.

CSV export, needed for any bulk pull, requires **Basic**. The free tier can only be viewed or transcribed manually.

---

## Summary table
| Source | Automated pull allowed? | ML/model use allowed? | Recommended use |
|---|---|---|---|
| ESPN (via Public-ESPN-API / hoopR / CBBpy) | No (Disney ToU B.x) | No (AI Tool clause) | Endpoint/field reference; manual reading; permission or licensed feed for anything else |
| Sports-Reference CBB / Stathead | Only if not impacting performance (≤20/min; Stathead ≤10/min) | **No**, any collection method (SR ToU) | Manual, cited, non-ML lookups |
| Massey (site) | No reproduction | No without written consent | View only; ask permission |
| Massey via Kaggle MMasseyOrdinals | n/a (download after accepting rules) | Yes: "any purpose ... academic research" | Primary composite-rank source; do not redistribute |
| KenPom API ($145/yr) | Yes, within rate limits | Yes: "research, model building" | Team-efficiency features; private use plus attribution |
| EvanMiya | No automation; CSV on Basic | Personal non-commercial; no AI clause | Free tier manual; Basic for CSV |

---

## Sources
- https://github.com/pseudo-r/Public-ESPN-API (repo page; cloned 18 Oct 2026: README.md, PROJECT_SCOPE.md, LICENSE, docs/audit-2026-09-30.md, docs/sports/basketball.md, docs/sports/college_sports.md, docs/core-endpoints.md)
- https://github.com/pseudo-r/Public-ESPN-API/issues/23 (cited from the README; not opened separately)
- ESPN endpoints spot-checked:
  - https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event=401825568
  - https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/events/401825568/competitions/401825568/plays
  - .../probabilities, .../officials, .../odds
  - https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/seasons/2026/powerindex and /powerindex/127
  - https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/rankings, /scoreboard, /teams/127/roster, /teams/127/schedule?season=2026
  - https://sports.core.api.espn.com/v2/sports/basketball/leagues/mens-college-basketball/venues
  - https://cdn.espn.com/core/mens-college-basketball/game?xhr=1&gameId=401825568
- https://www.espn.com/espn/news/story?page=terms (footer links to Disney ToU)
- https://disneytermsofuse.com/english/
- https://www.espn.com/robots.txt
- https://hoopr.sportsdataverse.org/reference/index.html ; https://cran.r-project.org/web/packages/hoopR/index.html ; https://github.com/sportsdataverse/hoopR (cloned)
- https://pypi.org/project/sportsdataverse/ ; https://pypi.org/project/CBBpy/ ; https://github.com/dcstats/CBBpy (cloned)
- https://www.sports-reference.com/termsofuse.html
- https://www.sports-reference.com/bot-traffic.html
- https://www.sports-reference.com/429.html
- https://www.sports-reference.com/data_use.html
- https://www.sports-reference.com/sharing.html
- https://www.sports-reference.com/stathead/termsofuse.html
- https://www.sports-reference.com/robots.txt
- https://github.com/roclark/sportsipy (cloned) ; https://github.com/roclark/sportsipy/issues ; https://pypi.org/project/sportsipy/
- https://github.com/vishaalagartha/basketball_reference_scraper (cloned) ; https://pypi.org/project/basketball-reference-scraper/
- https://masseyratings.com/info.php (via fetch tool) ; https://masseyratings.com/ (via fetch tool) ; https://masseyratings.com/robots.txt ; https://masseyratings.com/cf/aboutcomp.htm ; masseyratings.com/cb/compare.htm (403, unverified)
- https://www.kaggle.com/competitions/march-machine-learning-mania-2026/data ; https://www.kaggle.com/competitions/march-machine-learning-mania-2026/rules
- https://www.kaggle.com/datasets/masseyratings/rankings (via Kaggle public API: /api/v1/datasets/view/masseyratings/rankings and /datasets/list/...)
- https://www.kaggle.com/datasets/aadhafun/massey-ncaa-ratings-2025 (via Kaggle API listing)
- https://github.com/Carrigan/mncaa (cloned)
- https://kenpom.com/api-documentation.php ; https://kenpom.com/register-api.php ; https://kenpom.com/terms-api.php ; https://kenpom.com/terms.php (all via fetch tool; direct curl got 403) ; https://kenpom.com/api.php (401 unauthenticated)
- https://evanmiya.com/subscribe ; EvanMiya Terms of Use: https://docs.google.com/document/d/1jbGeWCSgl0-ApK_929RT2D3ldPGHYUVSbipV8EvZ9_c
