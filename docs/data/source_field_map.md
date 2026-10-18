# Source field map (proposal)

Prepared 18 Oct 2026 for prompt 003, workflow W2 (items 3, 4 and 5). Status: **proposal** for the requirements session. Column names follow `schema/global_metadata.yaml`; any other column name here is a proposed name and gives way to `docs/data/dictionary_games.md` once that file exists.

How this was built:
- **CBBD:** read from the public OpenAPI spec (v1.30.1), the public `data-availability.md` and `usage-and-access.md` pages, and the public API source code on GitHub. **No keyed call was made**, so every CBBD value is "per spec" until the verification calls in section 5 run.
- **ESPN data already pulled:** read from `registry/games.csv`, `registry/rosters.csv`, `src/msu_alpha/data/espn_registry.py`, and the Job D files in `/private/tmp/.../pbpwork/` (scripts read in full; `poss_*.jsonl`, `box_*.jsonl` and `ids_*.json` inspected for keys, types and value counts only). No ESPN request was made and no ESPN row is copied here.
- **hoopR:** read from the hoopR reference pages and the hoopR R source (roxygen column tables). No data files were downloaded.
- **Torvik and KenPom:** taken from `docs/research/data_sources_catalog.md` (checked live on 18 Oct by that author) and from the column headers of the local Kaggle archive. barttorvik.com and kenpom.com were not opened, and the connected KenPom tool was not called.
- **Kaggle archive and EvanMiya exports:** header lines only, plus year ranges and row counts. No rows were copied.

Anything not confirmed from an opened page or a local file is marked **(unverified)**.

Units rule: metres, centimetres, kilograms, seconds, degrees. Feet, inches and pounds from a source are converted, and the original goes in a `*_source` column.

---

## 0. Licence classes used in this file

Classes are those named in R-DS-10: **model input allowed**, **reference only**, **blocked until permission**. The terms evidence is in `docs/research/data_sources_catalog.md` (cited as "catalog §x").

| Source | Class | Basis | Note |
|---|---|---|---|
| CBBD API (CollegeBasketballData.com) | Model input allowed | R-DS-10; catalog §1.8: research, caching and model training allowed; no raw redistribution | Raw responses stay private (R-RG-11, R-DQ-05) |
| ESPN data already pulled (`registry/*.csv`, Job D `pbpwork/` files) | Reference only | BOARD 2026-10-18T13:45Z ("ESPN terms: reference only, never model input"); R-DS-02; catalog §1.5 (Disney ToU) | Job D files must move to `MyDrive/MSU-Alpha-3/data/quarantine/espn_pbp_jobD/` (BOARD ask) |
| hoopR prebuilt ESPN releases (`load_mbb_*`) | Model input allowed per R-DS-10 ("hoopR releases"), **with a caveat** | Catalog §1.9: the package is MIT, but "underlying ESPN/NCAA terms still apply" | **Decision needed:** R-DS-10 and the ESPN-terms note pull in opposite directions for ESPN-derived release files |
| hoopR NCAA engine releases (`load_ncaa_mbb_*`, from stats.ncaa.org) | Model input allowed | R-DS-06 ("both allow this use") | stats.ncaa.org terms **(unverified)** (catalog §1.6, HTTP 403) |
| Torvik static files / cbbdata | Model input allowed **(provisional)** | Catalog §1.2: no terms page found; "Compiled by Bart Torvik from publicly available data" | Not named in R-DS-10. **Decision needed** |
| KenPom official API ($145/yr, not bought) | Model input allowed | R-DS-10, R-DS-11; catalog §1.1 (API terms allow academic study and model building) | Not available today |
| KenPom web / connected Parse.bot tool | Blocked | R-DS-14; catalog §1.1 (web ToU bans scrapers) | Not used |
| Kaggle March Madness archive (local `archive-3/`, `archive/`) | Reference only **(provisional)** | R-RG-11 lists Kaggle files as licensed/private. This archive is a community compilation that includes KenPom-web, Torvik and EvanMiya columns; its Kaggle licence was not checked | Not the "Kaggle Massey" competition data named in R-DS-10 (inference) |
| EvanMiya exports (local `data/EvanMiya_*.csv`) | Reference only | R-DS-10 ("EvanMiya free tier"); catalog §1.3 (personal, non-commercial local extracts; no redistribution) | Whether Basic-tier CSV may feed models is **(unverified)** |

---

## 1. Sources

### 1.1 CBBD (CollegeBasketballData.com API)

| Item | Value |
|---|---|
| Access | REST, `https://api.collegebasketballdata.com`, OpenAPI v1.30.1 (MIT), 40 GET endpoints, 66 component schemas ([api-docs.json](https://api.collegebasketballdata.com/api-docs.json)) |
| Auth | HTTP bearer key on every endpoint (`securitySchemes.apiKey: {type: http, scheme: bearer}`). Key kept outside the repo (R-DS-13) |
| Quota | Free tier 1,000 calls/month, **shared with CFBD** (R-DS-13; Jan 2025 launch post). The current number is **(unverified)**: the tiers page lists none and a 14 Jul 2026 note calls the launch figures historical. Read `X-CallLimit-Remaining` on the first call. HTTP 429 "Monthly call quota exceeded." at zero; Cloudflare may block for about 600 s after bursts (all from `docs/markets/collector_design.md` §1.1) |
| Entitlements | `/scoreboard` needs Patreon Tier 1+; `/stats/team/leaderboard` needs Tier 2+ (spec descriptions) |
| Licence class | Model input allowed |
| Seasons | `season` = ending year (2026 = 2025-26) ([data-availability.md](https://api.collegebasketballdata.com/data-availability.md)) |
| Coverage ([data-availability.md](https://api.collegebasketballdata.com/data-availability.md)) | Games/scores 1949+; team box 2003+ (broad from 2005); player box 2003+ (broad from 2005); PBP **2003 (18 games) and 2006+**, none in 2004–05; team/player shooting breakdowns 2003, 2006+; **shot coordinates 2019+** ("many shots have no location"); **substitutions 2024+** (2023-24; also 212 games in 2013, none 2014–2023); **lineups 2024+**; in-game win probability 2003, 2006+; possessions 2003, 2006+; SRS and Elo 1950+; adjusted efficiency 2014+; rosters 2003+; season overviews 2014+; portal 2021+; AP 1949+; Coaches 2003+; recruits 2007+; team recruiting 2003+; draft 2001+; lines 2013+; broadcasts 2011+; leaderboard 2015+ |
| Time resolution | Game clock: `secondsRemaining` integer (1 s) plus `clock` string (format **unverified**); `wallclock` date-time per play (nullable). Substitutions: integer seconds remaining plus period. No shot clock |
| Upstream | CBBD does not name its upstream. Play-type names in its code (`MadeFreeThrow`, `Lost Ball Turnover`, `JumpShot`, `LayUpShot`, `DunkShot`, `TipShot`, `Block Shot`, `Defensive Rebound`, `Offensive Rebound`) are ESPN's names, so CBBD plays probably derive from ESPN **(inference, unverified)**. If so, a CBBD-vs-ESPN check mostly tests ingestion (same point as collector_design §1.1 for lines) |

**Known quirks** (spec, source code and collector_design §1.1):
1. `gameId`, `teamId` and `athleteId` are CBBD's own IDs. `sourceId` (games, plays `gameSourceId`, teams, roster players) and `athleteSourceId` are probably ESPN IDs (hoopR `cbbd_games.R` says "Source (ESPN) game id"). The spec does not document this, so verify on the first call.
2. No pagination. `/games`, `/games/teams`, `/games/media` and `/lines` cap at 3,000 rows; `/games/players` caps at **1,000 games**. Truncation is silent, so slice by team, conference or date.
3. Most filters take a team **name** string (`team=`), not an ID. The exact MSU string ("Michigan State"?) and the conference string ("B1G" or "Big Ten") are **(unverified)**.
4. `season` is typed `integer` on some endpoints and `number(double)` on others. Harmless, but keep it in mind.
5. `onFloor` on plays is computed server-side from substitution time ranges. Elapsed seconds = `1200 − secondsRemaining` (period 1), `2400 − …` (period 2), `2400 + (period − 2)×300 − …` (OT), and the range must contain that second (`plays/service.ts`). So it is only as good as the substitution feed (R-DQ-09: PBP substitution timing errors), it has 1 s resolution, and a play at the exact second of a substitution can list either player **(inference)**. Empty before 2024.
6. `shotInfo.range` is derived from text, not location: `free_throw` if the play type contains "free"; `three_pointer` if the type or text contains "three"/"three point"; `rim` if the type contains layup, dunk or tip; else `jumper` (`plays/service.ts`). `assisted` = text contains "assisted by" or "assists".
7. `shotInfo.location {x, y}`: units, origin and orientation are **undocumented**. The values are passed through from the stored columns `shotLocationX/Y`.
8. Lineup `possessions` is an event count, not a box formula (see section 4). Lineup TS% uses 0.44×FTA.
9. `/lines` has no timestamps, no juice on spreads or totals, and an unverified spread sign. A game can have an empty `lines[]` (collector_design §1.1).
10. `/ratings/adjusted`, `/ratings/srs` and `/ratings/elo` take only `season`, so they are **season-level values, not point-in-time** (R-DS-04). Point-in-time CBBD values are `/games.homeTeamEloStart/awayTeamEloStart` (pre-game) and `/rankings` (weekly, `pollDate`).
11. Catalog §1.8 says "PBP 2005-06+" and "shot distribution 2013-14+". The CBBD data-availability page opened on 18 Oct 2026 says PBP 2003 (18 games) and 2006+, shooting breakdowns 2003 and 2006+, and coordinates 2019+. Note dated 2026-10-18: use the data-availability page.

**Endpoint and field list.** These are the response fields per endpoint from the spec. `[]` = array, `?` = nullable, `n` = number(double), `i` = integer(int32), `s` = string, `b` = boolean, `dt` = date-time. Fields shared by every `/plays/*` endpoint are listed once.

| Endpoint | Parameters (req = required) | Response fields |
|---|---|---|
| `GET /games` | `startDateRange` dt, `endDateRange` dt, `team` s, `conference` s, `season` i, `seasonType` {postseason, preseason, regular}, `status` {scheduled, in_progress, final, postponed, cancelled}, `tournament` s | id i; sourceId s; seasonLabel s; season i; seasonType enum; startDate dt; startTimeTbd b; neutralSite b; conferenceGame b; gameType s?; tournament s?; gameNotes s?; status enum; attendance i?; homeTeamId i; homeTeam s; homeConferenceId i?; homeConference s?; homeSeed i?; homePoints i?; homePeriodPoints[] i?; homeWinner b?; homeTeamEloStart i?; homeTeamEloEnd i?; the same 11 for away; excitement n?; venueId i?; venue s?; city s?; state s? |
| `GET /games/media` | as /games minus status | gameId, season, seasonLabel, seasonType, tournament?, startDate, startTimeTbd, home/away TeamId, Team, Conference?, neutralSite, conferenceGame, gameType?, notes?, broadcasts[] {broadcastName s, broadcastType s} |
| `GET /games/teams` | as /games/media | gameId, season, seasonLabel, seasonType, tournament?, startDate, startTimeTbd, teamId, team, conference?, teamSeed?, opponentId, opponent, opponentConference?, opponentSeed?, neutralSite, isHome, conferenceGame, gameType?, notes?, gameMinutes n?, pace n?; `teamStats` and `opponentStats` each: fieldGoals / twoPointFieldGoals / threePointFieldGoals / freeThrows {pct, attempted, made}, rebounds {total, defensive, offensive}, turnovers {teamTotal, total}, fouls {flagrant, technical, total}, points {fastBreak, offTurnovers, inPaint, byPeriod[], largestLead, total}, fourFactors {freeThrowRate, offensiveReboundPct, turnoverRatio, effectiveFieldGoalPct}, assists, blocks, steals, possessions, rating, trueShooting, gameScore (all n?) |
| `GET /games/players` (≤ 1,000 games) | as /games/media | game header as /games/teams plus gamePace n?; players[]: athleteId i, athleteSourceId s, name s, position s, starter b?, ejected b?, minutes, points, turnovers, fouls, assists, steals, blocks, usage, offensiveRating, defensiveRating, netRating, effectiveFieldGoalPct, trueShootingPct, gameScore, assistsTurnoverRatio, freeThrowRate, offensiveReboundPct (n?), fieldGoals / twoPointFieldGoals / threePointFieldGoals / freeThrows {pct, attempted, made}, rebounds {total, defensive, offensive} |
| `GET /scoreboard` (Tier 1+) | `conference` s | id, startDate, startTimeTbd, tv?, neutralSite, conferenceGame, status, period i?, clock s?, venue?, city?, state?, homeTeam/awayTeam {id, name, location?, conference?, conferenceAbbreviation?, points?, lineScores[]?}, betting {spread?, overUnder?, homeMoneyline?, awayMoneyline?} |
| `GET /plays/game/{gameId}` | gameId i (req), `shootingPlaysOnly` b | **Play:** id i; sourceId s; gameId i; gameSourceId s; gameStartDate dt; season n; seasonType enum; gameType s; tournament s?; playType s; isHomeTeam b?; teamId i?; team s?; conference s?; teamSeed n?; opponentId i?; opponent s?; opponentConference s?; opponentSeed n?; period i; clock s; secondsRemaining i; homeScore i; awayScore i; homeWinProbability n?; scoringPlay b?; shootingPlay b?; scoreValue n?; wallclock dt?; playText s?; participants[] {name s, id i}; onFloor[] {team s, name s, id i}; shotInfo? {shooter {name?, id?}, made b?, range {rim, jumper, three_pointer, free_throw}?, assisted b?, assistedBy {name?, id?}, location {x n?, y n?}} |
| `GET /plays/player/{playerId}` | playerId i (req), `season` i (req), `shootingPlaysOnly` | Play |
| `GET /plays/team` | `season` i (req), `team` s (req), `shootingPlaysOnly` | Play |
| `GET /plays/date` | `date` (req, YYYY-MM-DD), `shootingPlaysOnly`, `utcOffset` n | Play |
| `GET /plays/tournament` | `tournament` s (req, e.g. NCAA, NIT), `season` n (req), `shootingPlaysOnly` | Play |
| `GET /plays/types` | none | id i, name s (the play-type vocabulary) |
| `GET /substitutions/game/{gameId}` | gameId (req) | gameId i; startDate dt; teamId i; team s; conference s?; athleteId i; athlete s; position s?; opponentId i; opponent s; opponentConference s?; subIn {opponentPoints i, teamPoints i, secondsRemaining i, period i}; subOut {same four} |
| `GET /substitutions/player/{playerId}` | playerId (req), `season` (req) | same |
| `GET /substitutions/team` | `season` (req), `team` (req) | same |
| `GET /lineups/game/{gameId}` | gameId (req) | teamId i; team s; conference s; idHash s (athlete IDs joined with "-", per source code); athletes[] {name, id}; totalSeconds n; pace n; offenseRating n; defenseRating n; netRating n; `teamStats` and `opponentStats` each: possessions, points, blocks, assists, steals, turnovers, defensiveRebounds, offensiveRebounds i; trueShooting n; fieldGoals / twoPointers / threePointers / freeThrows {made, attempted, pct}; twoPointers.jumpers / layups / dunks / tipIns {made, attempted, pct}; fourFactors {freeThrowRate, offensiveReboundPct, turnoverRatio, effectiveFieldGoalPct} |
| `GET /lineups/team` | `season` (req), `team` (req), `startDateRange`, `endDateRange` | same as /lineups/game |
| `GET /lines` (≤ 3,000 games) | `season`, `team`, `conference`, `startDateRange`, `endDateRange` | gameId i; season i; seasonType; startDate dt; homeTeamId; homeTeam; homeConference?; homeScore n?; awayTeamId; awayTeam; awayConference?; awayScore n?; lines[] {provider s, spread n?, overUnder n?, homeMoneyline n?, awayMoneyline n?, spreadOpen n?, overUnderOpen n?} |
| `GET /lines/providers` | none | id i, name s |
| `GET /ratings/adjusted` | `season` i, `team`, `conference` | season, teamId, team, conference, offensiveRating n, defensiveRating n, netRating n, rankings {net, defense, offense} |
| `GET /ratings/srs` | `season`, `team`, `conference` | season, teamId, team, conference, rating n |
| `GET /ratings/elo` | `season`, `team`, `conference` | season, teamId, team, conference, elo i? ("latest ending Elo", data-availability) |
| `GET /rankings` | `season`, `seasonType`, `week` i, `pollType` {ap, coaches}, `team`, `conference` | season, seasonType, week i, pollDate dt?, pollType s, teamId n, team, conference?, ranking n?, points n?, firstPlaceVotes n? |
| `GET /stats/team/season` | `season` n (req if no team), `seasonType`, `team`, `conference`, `startDateRange`, `endDateRange` | season, seasonLabel, teamId, team, conference?, games i, wins, losses, totalMinutes?, pace?, teamStats and opponentStats (as /games/teams without byPeriod, largestLead, gameScore) |
| `GET /stats/team/shooting/season` | `season` (req), `seasonType`, `team` or `conference` (one req), date range | season, teamId, team, conference?, trackedShots i, assistedPct, freeThrowRate, dunks / layups / twoPointJumpers / threePointJumpers {made, attempted, pct, assistedPct, assisted}, tipIns {made, attempted, pct}, freeThrows {made, attempted, pct}, attemptsBreakdown {threePointJumpers, twoPointJumpers, tipIns, layups, dunks} |
| `GET /stats/player/season` | `season` n (req), `seasonType`, `team`, `conference`, date range | season, seasonLabel, teamId, team, conference?, athleteId, athleteSourceId, name, position, games, starts, minutes, points?, turnovers?, fouls?, assists?, steals?, blocks?, usage?, offensiveRating?, defensiveRating?, netRating?, PORPAG?, effectiveFieldGoalPct?, trueShootingPct?, assistsTurnoverRatio?, freeThrowRate?, offensiveReboundPct?, fieldGoals / twoPointFieldGoals / threePointFieldGoals / freeThrows {pct, attempted, made}, rebounds {total, defensive, offensive}, winShares {totalPer40, total, defensive, offensive} |
| `GET /stats/player/shooting/season` | as team shooting | as team shooting plus athleteId, athleteName |
| `GET /stats/team/leaderboard` (Tier 2+) | `season`, `team`, `conference` | record, summary {totalMinutes, trackedShots, pace, rawNetRating}, team/opponent stats incl. points {fastBreak, offTurnovers, inPaint}, possessions, turnovers {technical, team, total}, shotProfile {atRim, dunk, layup, tipIn, twoPointJumper, threePointJumper, freeThrows, distribution {threeRate, jumperRate, midrangeRate}}, adjustedEfficiency {offensiveRating, defensiveRating, netRating, rankings} |
| `GET /teams` | `conference`, `season` | id i, sourceId s, school, mascot?, abbreviation?, displayName?, shortDisplayName?, primaryColor?, secondaryColor?, currentVenueId i?, currentVenue?, currentCity?, currentState?, conferenceId i?, conference?, logos[]? |
| `GET /teams/directory` | `season` (req) | season, seasonLabel, teams[] {id, sourceId?, school, mascot?, abbreviation?, displayName?, shortDisplayName?, conferenceId}, conferences[] {id, name, abbreviation} |
| `GET /teams/roster` | `season` (req), `team` | teamId, teamSourceId, team, conference?, season, players[] {id i, sourceId s, name, firstName?, lastName?, jersey?, position?, height n? (unit **unverified**), weight n? (unit **unverified**), hometown {city?, state?, country?, latitude?, longitude?, countyFips?}, dateOfBirth date?, startSeason, endSeason} |
| `GET /teams/{teamId}/season/{season}/overview` | teamId (req), season (req) | formatVersion {1, 2}; record {overall, conference: games, wins, losses, unresolved; complete; unknown…Games}; ratings {polls.ap/coaches {state, date, week, seasonType, rank}, srs, elo, adjusted {offense, defense, net: value, rank; population}}; efficiency {offense/defense: boxScore{…}, points, possessions, rawRating, four factors; pace, paceGames, coverage}; shooting.buckets[] {key {at_rim, two_point_jumper, three_point_jumper, unknown}, attempts, made, attemptPct, fieldGoalPct}; players.rows[] {athleteId, name, position, onRoster, hasStats, games, minutes, points, …, usagePct, trueShootingPct, seasonStats{…, advanced{winShares, porpag, ratings}}}; schedule.games[] {id, opponentId, opponent, startDate, calendarDate, location {home, away, neutral}, status, seasonType, gameType, eligibility {counted, exhibition, unknown}, conferenceGame, teamPoints, opponentPoints, result, venue}; sources {notes[], latestFinalStartDate, leaderboardUpdatedAt} |
| `GET /venues` | none | id n, sourceId s?, name s, city s?, state s?, country s? (**no capacity, coordinates or elevation**) |
| `GET /conferences` | none | id, sourceId, name, abbreviation, shortName |
| `GET /conferences/history` | `conference` | id, sourceId, name, abbreviation, shortName, teams[] {id, sourceId, school, mascot?, startSeason, endSeason?} |
| `GET /recruiting/players` | `year` i, `team`, `conference`, `position` | id, sourceId?, athleteId i?, year i, name, position?, schoolId?, school? (high school), hometown {city, state, country, latitude, longitude, countyFips}?, committedTo {id, name, conference}?, heightInches n?, weightPounds i?, stars i, rating n, ranking i? |
| `GET /recruiting/teams` | `year`, `team`, `conference` | teamId, team, conference?, year, ranking i, rating n |
| `GET /recruiting/portal` | `year` n, `sourceTeam`, `destinationTeam`, `sourceConference`, `destinationConference`, `position` | id, sourceId, year, firstName, lastName, position, origin {id, name, conference}?, destination {id, name, conference}?, eligibility {Withdrawn, TBD, PendingAppeal, SittingOne, Immediate}?, yearsRemaining i?, stars i?, rating n? |
| `GET /draft/picks` | `year`, `draftTeam`, `sourceTeam`, `position` | athleteId i?, sourceTeamId?, sourceTeamLocation?, sourceTeamName?, sourceTeamLeagueAffiliation?, sourceTeamCollegeId?, draftTeamId, draftTeam, year, overall, round, pick, name, overallRank?, positionRank?, height n? (unit **unverified**), weight i? (unit **unverified**) |
| `GET /draft/teams` | none | id, sourceId, location, name, displayName, abbreviation |
| `GET /draft/positions` | none | name, abbreviation |

Counts: 40 endpoints, 720 distinct response field paths (1,405 counting repeats across endpoints). Endpoints in the requested families: games 4 (+ scoreboard), plays 6, substitutions 3, lineups 2, lines 2, ratings 3, rankings 1, players 2 (+ roster), recruiting 3, teams 4, venues 1, conferences 2, draft 3, stats 5.

### 1.2 ESPN data already pulled (reference only; no new ESPN requests)

| Item | Value |
|---|---|
| Access | Local files only. Origin: ESPN site API (`site.api.espn.com/.../mens-college-basketball/...`) pulled on 17–18 Oct 2026 |
| Auth / quota | None / none. **No re-pull** (BOARD; Job D scripts carry a do-not-rerun warning) |
| Licence class | Reference only, never model input |
| Coverage | `registry/games.csv`: 179 MSU games, 2021-22 to 2025-26. `registry/rosters.csv`: 29 rows, incomplete (registry README). Job D: seasons 2025 and 2026 (2024-25, 2025-26), all D-I games found on the daily scoreboards Nov 1–Apr 10; 6,300 game IDs in `ids_2026.json`; **12,410 games** with possession rows; 1,712,830 possession rows; 25,184 team-box rows |
| Time resolution | Possession start `t0` = elapsed seconds in the period; **all 1,712,830 values are whole seconds**, so the parsed ESPN game clock has 1 s resolution in these pulls (observed). `registry/games.csv` `date_utc` to the minute |
| What is NOT on disk | The raw ESPN `summary` JSON (plays, win probability, officials, odds, player box) was parsed in memory and **not stored**. Only derived possessions and team-box strings exist |

Field lists:
- **`registry/games.csv`** (built by `espn_registry.py` from `teams/127/schedule`): `game_id` (ESPN event id), `season` (ending year), `season_type` (regular, postseason; the Big Ten tournament shows as regular, see notes), `date_utc` (ISO, minute), `site` (home, away, neutral from `neutralSite`/`homeAway`), `venue` (fullName), `city`, `opponent` (displayName), `opponent_id` (ESPN team id), `msu_score`, `opp_score`, `result` (W/L), `attendance`, `broadcast` (media shortName joined "; "), `notes` (headline), `status` (e.g. STATUS_FINAL), `footage_source`, `footage_path` (ours).
- **`registry/rosters.csv`** (from `teams/127/roster?season=`): `season`, `espn_id`, `name`, `jersey`, `position` (G/F/C), `height_cm` (ESPN inches × 2.54, 0.1 cm), `weight_kg` (ESPN lb × 0.45359237, 0.1 kg), `class` (experience displayValue), `hometown` (birthPlace displayText, e.g. "City, ST"; note this is **birthplace**, not necessarily hometown), `headshot_url` (face image URL; under the no-face-data rule, do not fetch it).
- **Job D `poss_{season}[_shard].jsonl`** (one row per possession, built by `parse.py`): `gid` (ESPN event id, string), `team` (ESPN team id with the ball), `period` (int; 1–2 halves, 3+ OT), `start` (enum: period_start, made_fg, made_ft, steal, dead_to, dreb_fg, dreb_ft, dreb_fg_team, dreb_ft_team, dreb_fg_dead, dreb_ft_dead, dreb_fg_unrec, dreb_ft_unrec, unknown), `t0` (elapsed s in period at start), `pts` (points in the possession), `n_fga`, `first_fga_t`, `last_fga_t` (elapsed s), `oreb` (offensive rebounds inside the possession), `end` (`to` or null), `foul_t` (elapsed s of the first defensive foul), `foul_type` (only `PersonalFoul` occurs in 241,309 rows; technicals are routed elsewhere), `foul_after_fga_same_t` (bool), `ft_at_foul` (bool, optional).
- **Job D `box_{season}[_shard].jsonl`** (one row per team-game): `gid`, `date` (YYYY-MM-DD scoreboard date), `team` (ESPN id), `name`, `score` (string), `fbp` (fast-break points), `n_plays` (number of PBP rows in the feed), `season_type` (2 regular, 3 post), `stats` (all strings): `fieldGoalsMade-fieldGoalsAttempted`, `fieldGoalPct`, `threePointFieldGoalsMade-threePointFieldGoalsAttempted`, `threePointFieldGoalPct`, `freeThrowsMade-freeThrowsAttempted`, `freeThrowPct`, `totalRebounds`, `offensiveRebounds`, `defensiveRebounds`, `assists`, `steals`, `blocks`, `turnovers`, `teamTurnovers`, `totalTurnovers`, `technicalFouls`, `totalTechnicalFouls`, `flagrantFouls`, `turnoverPoints`, `fastBreakPoints`, `pointsInPaint`, `fouls`, `largestLead`, and (78% of rows) `leadChanges`, `leadPercentage`.
- **Job D `ids_{season}.json`**: `{event_id: {date, teams: [[team_id, location, conferenceId, homeAway] ×2], season_type}}`; `good_{season}.json` = list of event IDs that passed Job D's quality filter.
- **ESPN summary play fields** (used by `parse.py` and listed in catalog §1.5; not stored): `id`, `sequenceNumber`, `type {id, text}`, `text`, `awayScore`/`homeScore`, `period.number`, `clock.displayValue`, `scoringPlay`, `scoreValue`, `team.id`, `participants[].athlete.id`, `wallclock`, `shootingPlay`, `coordinate {x, y}`, `pointsAttempted`. Type texts referenced in the code: `Substitution`, `OfficialTVTimeOut`, `ShortTimeOut`, `RegularTimeOut`, `FullTimeOut`, `End Period`, `End Game`, `PersonalFoul`, `Flagrant Foul`, `Technical Foul`, `Steal`, `*Turnover`, `Defensive Rebound`, `Offensive Rebound`, `Dead Ball Rebound`, `Jumpball`, plus shot types.

### 1.3 hoopR prebuilt release files

| Item | Value |
|---|---|
| Access | Prebuilt files on GitHub releases (`sportsdataverse/sportsdataverse-data`, `.rds`/`.parquet`/`.csv.gz`), loaded by `load_mbb_*` (ESPN engine) and `load_ncaa_mbb_*` (NCAA engine). hoopR 3.1.0 CRAN (25 Aug 2026), docs 3.1.0.9000 |
| Auth / quota | None. GitHub download limits only |
| Licence class | ESPN engine: model input allowed per R-DS-10, with the ESPN-terms caveat (decision needed). NCAA engine: model input allowed (R-DS-06), stats.ncaa.org terms **(unverified)** |
| Coverage | ESPN PBP 2006+; shots 2003 and 2006+ (catalog §1.9); schedules 2002–2027 (`espn_mens_college_basketball_schedules` release, last written 2026-09-15; collector_design §0). NCAA engine 2010+ "with no gaps"; NCAA shots **2019+** ("stats.ncaa.org did not publish shot-location data before then") |
| Time resolution | ESPN: `clock_display_value` string; `start_*_seconds_remaining` integer; `end_*_seconds_remaining` numeric. NCAA: `clock` MM:SS, `game_seconds` integer (elapsed from tip), `event_length` and `poss_length` integer seconds. Neither has a shot clock |
| Doc quirks | The ESPN pbp table text describes quarters ("1-4 for quarters; 5+ for OT"), copied from the shared NBA/WNBA schema; men's college is halves (Rule 5-6.1: "two halves of 20 minutes"). The NCAA engine pages say "1-2 halves pre-2016, 1-4 quarters 2016+", which matches women's, not men's, basketball. Verify the period numbering in the files **(unverified)**. The schedule example prints 83 columns; the documented table has 74 |

ESPN-engine column lists (documented on [load_mbb_pbp](https://hoopR.sportsdataverse.org/reference/load_mbb_pbp.html) and in `R/load_mbb.R`, `R/hoopR_schemas.R`):
- **`load_mbb_pbp`** (56 documented): id, sequence_number, type_id, type_text, text, away_score, home_score, period_number, period_display_value, clock_display_value, scoring_play, score_value, team_id, participants_0_athlete_id, participants_1_athlete_id, wallclock, shooting_play, season, season_type, away/home_team_id, _name, _mascot, _abbrev, _name_alt, home_team_spread, game_spread, home_favorite, game_spread_available, game_id, qtr, time, clock_minutes, clock_seconds, half, game_half, lag_qtr, lead_qtr, lag_game_half, lead_game_half, start_quarter_seconds_remaining, start_half_seconds_remaining, start_game_seconds_remaining, game_play_number, end_quarter_seconds_remaining, end_half_seconds_remaining, end_game_seconds_remaining, period, coordinate_x, coordinate_y, media_id, score_source ('rebuilt' or 'espn').
- **`load_mbb_team_box`** (40): team_id, team_uid, team_slug, team_location, team_name, team_abbreviation, team_display_name, team_short_display_name, team_color, team_alternate_color, team_logo, field_goals_made_field_goals_attempted, field_goal_pct, three_point_field_goals_made_three_point_field_goals_attempted, three_point_field_goal_pct, free_throws_made_free_throws_attempted, free_throw_pct, total_rebounds, offensive_rebounds, defensive_rebounds, assists, steals, blocks, turnovers, team_turnovers, total_turnovers, technical_fouls, total_technical_fouls, flagrant_fouls, fouls, largest_lead, home_away, opponent_id, opponent_name, opponent_mascot, opponent_abbrev, game_id, season, season_type, game_date.
- **`load_mbb_player_box`** (`espn_mbb_game_all_player_schema`, about 55): game_id, season, season_type, game_date, game_date_time, athlete_id, athlete_display_name, team_id, team_name, team_location, team_short_display_name, minutes, field_goals_made/attempted, three_point_field_goals_made/attempted, free_throws_made/attempted, offensive_rebounds, defensive_rebounds, rebounds, assists, steals, blocks, turnovers, fouls, points, starter, ejected, did_not_play, active, athlete_jersey, athlete_short_name, athlete_headshot_href, athlete_position_name, athlete_position_abbreviation, team display and colour fields, home_away, team_winner, team_score, opponent_team_id, _name, _location, _display_name, _abbreviation, _logo, _color, _alternate_color, opponent_team_score.
- **`load_mbb_schedule`** (74 documented): id, uid, date, attendance, time_valid, neutral_site, conference_competition, (play_by_play_available), recent, start_date, (broadcast, broadcast_market, broadcast_name, highlights), notes_type, notes_headline, type_id, type_abbreviation, venue_id, venue_full_name, venue_address_city, venue_address_state, **venue_capacity**, venue_indoor, status_clock, status_display_clock, status_period, status_type_*, format_regulation_periods, home_/away_ id, uid, location, name, abbreviation, display_name, short_display_name, color, alternate_color, is_active, venue_id, logo, conference_id, score, winner, game_id, season, season_type, status_type_alt_detail, groups_id, groups_name, groups_short_name, groups_is_conference, tournament_id, game_date_time, game_date, PBP, team_box, player_box.
- **`load_mbb_shots`** (20): game_id, season, period_number, clock_display_value, team_id, athlete_id_1 (shooter), athlete_id_2 (assister or fouler), type_id, type_text, scoring_play, score_value, coordinate_x, coordinate_y, coordinate_x_raw, coordinate_y_raw, athlete_name_1, athlete_name_2, team_name, team_mascot, team_abbrev.
- **Game rosters** (`espn_mbb_game_rosters` schema; per-game, so it gives jersey-number history): athlete_id, first/last/full name, weight (lb), display_weight, height (inches), display_height ('6-2'), age, date_of_birth, birth_place_city/state/country, jersey, hand_type, hand_abbreviation, hand_display_value, position_*, experience_years, experience_display_value, draft_*, starter, did_not_play, ejected, team_*, game_id, home_away.
- Other loaders without column tables on the page: rosters, player/team season stats (long), standings, **officials** (per-game officials), player_core.

ESPN coordinate convention (from `R/espn_mbb_data.R`): raw `x` = feet across the court (0–50, rim centre at 25); raw `y` = feet from the rim centre toward half court (half-court line at 41.75). hoopR forces free throws to (25, 13.75). Its transformed `coordinate_x = ±(y_raw − 41.75)`, `coordinate_y = ±(x_raw − 25)`, with the sign flipped for the home team (origin at mid-court, feet). **Use the raw values.**

NCAA-engine column lists ([load_ncaa_mbb_lineups](https://hoopR.sportsdataverse.org/reference/load_ncaa_mbb_lineups.html) page, one page for all loaders):
- **`load_ncaa_mbb_pbp`** (about 110): game_date, home, away, period, clock, game_time, game_seconds, home_score, away_score, event_team, event_description, player_1, player_2, event_type (e.g. 'made Layup', 'won Jumpball'), event_result, shot_value, event_length, **poss_num, poss_team, poss_length, is_transition**, home_1..5, away_1..5 (+ `_player_id`, `_clean_name`), status (row QA flag), **is_garbage_time**, sub_deviate, contest_id, home/away/event_team/poss_team `_ncaa_team_id` and `_espn_team_id`, player_1_id/_clean_name, player_2_id/_clean_name, **espn_game_id**, is_fastbreak, is_from_turnover, is_paint, is_second_chance, assist_player, **ft_number, ft_attempts, foul_class, is_shooting_foul, is_looseball_foul, is_one_and_one, is_flagrant, foul_tech_class, ft_awarded, turnover_type, is_team_turnover, timeout_type, challenge_outcome**, season.
- **`load_ncaa_mbb_shots`** (19, 2019+): season, team_id (holds the team name), shooter_id, shot_x, shot_y (units **undocumented**), dist_ft, shot_zone ('abovebreak3', 'rim', …), shot_type, made, point_value, period, sec_left, source, contest_id, ncaa_team_id, espn_team_id, shooter_player_id, shooter_clean_name, espn_game_id.
- **`load_ncaa_mbb_lineups`** (one row per lineup stint, about 70): lineup_key, date, location_type, team, team_year, opponent, lineup_id, start_min, end_min, duration_mins, player_1..5, players_in, players_out, start/end_scored, start/end_allowed, start/end_diff, player_count_error, poss, pts, plus_minus, fga, fgm, rima, rimm, rim_ast, mida, midm, mid_ast, fg2a, fg2m, tpa, tpm, tp_ast, fta, ftm, orb, drb, to, stl, blk, ast, foul, the same with `opp_`, stint_num, contest_id, season.
- **`load_ncaa_mbb_matchup_stints`** (10-man, about 31): contest_id, season, game_date, home, away, game_stint_num, period, start_seconds, end_seconds, duration_seconds, matchup_key, home/away_lineup_key, home/away_lineup, start/end_home/away_score, n_events, n_possessions, home_pts, away_pts, home_1..5, away_1..5.
- **`load_ncaa_mbb_possessions`** (about 56): game_date, home, away, period, poss_num, poss_team, home_1..5, away_1..5, home_score, away_score, pts, is_assisted, is_transition, is_garbage_time, start_event_type, first_shot_time, first_shot_type, last_event_time, last_event_type, contest_id, team IDs (ncaa/espn), lineup player ids and clean names, espn_game_id, season.
- **RAPM** (within-team: team, player_code, rapm_off, rapm_def, rapm_net, team_off_poss, num_players, season, player_id, team_id, person_id; league: season, player_id, person_id, player, team, orapm, drapm, rapm_net, off_poss, def_poss, estimand). **Player box** (mins, o_poss, pts, orb, drb, ast, stl, blk, tov, pf, ts_pct, efg_pct, fg/tp/ft made-attempted-pct, rim/mid/pback made-attempted-pct, blk_rim, …).
- **Crosswalks:** `mbb_team_crosswalk` (season, espn_team_id, espn_*, fox_*, **bart_team**, bart_conf, **kp_team**, kp_conf, yahoo_*, match confidences, match_method); `mbb_player_crosswalk` (ESPN↔Fox only; "KenPom and Torvik have no per-player data for MBB, so neither source is joined"); `mbb_schedule_crosswalk` (espn_game_id ↔ **bart_muid**, kp_game_id only with a KenPom login, which we will not use). These are built live, not prebuilt; the page examples failed on 18 Oct because Torvik returned HTML.

### 1.4 Torvik (barttorvik.com; via static files or cbbdata)

| Item | Value |
|---|---|
| Access | Static CSV/JSON files (catalog §1.2): `{YEAR}_team_results.csv/.json` (45 columns), `{YEAR}_fffinal.csv`, `getadvstats.php?year=&csv=1` (player-season, **no header row**, positional), `{YEAR}_super_sked.csv` (every game with pre-game projection). cbbdata R API (free key) for the daily ratings archive and game logs |
| Auth / quota | None for files; cbbdata needs a free key. Throttle to a few requests a minute (catalog §4) |
| Licence class | Model input allowed (provisional, see section 0) |
| Coverage | 2008 to present |
| Time resolution | Team-season (current to the fetch date), team-game, player-season, player-game, daily snapshots ("T-Rank Time Machine", cbbdata `cbd_torvik_ratings_archive`; toRvik-data `ratings_archive_{date}.csv`) |
| Fields (catalog §1.2) | Team: AdjOE, AdjDE, Barthag, adjt, WAB, eFG/eFGD, TOR/TORD, ORB/DRB, FTR/FTRD, 2P%/2P%D, 3P%/3P%D, 3PR/3PRD, SOS variants, Qual O/D, FUN, Con stats. Player: O-Rating, Usage, eFG, TS, TOV/OR/DR rates, FT rate, Foul/40, FT/2P/3P %, FTA/2PA/3PA, Ast/Stl/Blk %, Min%, Height, PORPAGATU!, D-PORPAG, Adj D-Rtg, BPM/OBPM/DBPM, Role, Pick, RecruiT-Rank, Dunks, Rim and Mid attempts/makes. Game box: Min, ORtg, Usg, eFG, TS, rates, Dunk, Rim, Mid, 2Pt, 3Pt, FT, Ast, TO, Stl, Blk, OR, DR, PF, BPM, NET, Pts, game possessions. `teampbp.php`: Dunks, Close Twos, Farther Twos, Threes (share and FG%, offense and defense) |
| Gap | `getadvstats` positional column mapping: the catalog points to the cbbdata/toRvik docs, but the cbbdata reference pages I opened list no columns and the toRvik R files I opened do not name them. **(Unverified)** |

### 1.5 KenPom

| Item | Value |
|---|---|
| Access | Official API ($145/yr, not bought) or web subscription. The connected "KenPom API" tool is a Parse.bot scraper and is **not used** (R-DS-14). Not called for this file |
| Auth / quota | API key (R-DS-11). The rate limit is not documented in the repo **(unverified)** |
| Licence class | API: model input allowed. Web/tool: blocked. KenPom-derived columns in the Kaggle archive: reference only |
| Coverage (catalog §1.1, from kenpompy docs) | Ratings, four factors, point distribution 1999+; height/experience 2007+; continuity 2008+; possession length 2010+; player stats 2004+; officials 2016+; arenas 2010+ |
| Time resolution | Season-to-date; `archive` endpoint gives historical and preseason ratings by date (point-in-time, R-DS-04); `fanmatch` gives pre-game predictions per game |
| API endpoints (catalog §1.1) | `ratings` (ratings, SOS, tempo, possession length), `archive`, `four-factors`, `pointdist`, `height`, `misc-stats`, `fanmatch`, `conf-ratings`, `program-ratings`, `teams`, `conferences`. The API response field names were not opened **(unverified)** |
| Field names seen locally (Kaggle `archive/INT _ KenPom _ *.csv` headers, 1999–2026) | Season, TeamName, Tempo, AdjTempo, OE, AdjOE, DE, AdjDE, AdjEM (+ Rank*); Raw/Adjusted Tempo and Efficiency; **Avg Possession Length (Offense/Defense)**; eFGPct, TOPct, ORPct, FTRate (offense and defense files); OffFT, Off2PtFG, Off3PtFG, DefFT, Def2PtFG, Def3PtFG (point distribution); FG2Pct, FG3Pct, FTPct, BlockPct, Opp*, FG3Rate, ARate, StlRate, NSTRate, DFP; AvgHeight, CenterHeight, PFHeight, SFHeight, SGHeight, PGHeight, EffectiveHeight, Experience, Bench, *Pts, *OR, *DR by position (2007–2026); Summary (Pre-Tournament) with Seed |

### 1.6 Kaggle March Madness archive (local, reference only, provisional)

Location: `~/Desktop/UnicornProjects/NCAA2026_mArchMadness/archive-3/` and `archive/`. Header lines only.

| File | Grain | Seasons (YEAR column) | Columns (summary) |
|---|---|---|---|
| `KenPom Barttorvik.csv` | team-season (tournament teams) | 2008–2026, no 2020 | YEAR, CONF, CONF ID, QUAD NO/ID, TEAM NO, TEAM ID, TEAM, SEED, ROUND, K TEMPO, KADJ T, K OFF, KADJ O, K DEF, KADJ D, KADJ EM (+ ranks), BADJ EM/O/D, BARTHAG, GAMES, W, L, WIN%, EFG%, EFG%D, FTR, FTRD, TOV%, TOV%D, OREB%, DREB%, OP OREB%, OP DREB%, RAW T, 2PT%, 2PT%D, 3PT%, 3PT%D, BLK%, BLKED%, AST%, OP AST%, 2PTR, 3PTR, 2PTRD, 3PTRD, BADJ T, AVG HGT, EFF HGT, EXP, TALENT, FT%, OP FT%, PPPO, PPPD, ELITE SOS, WAB (+ ranks) |
| `Barttorvik Home / Away / Neutral / Away-Neutral.csv` | team-season by site | 2008+ | Same Torvik block as above |
| `Shooting Splits.csv` | team-season | 2010–2026, no 2020 | DUNKS, CLOSE TWOS, FARTHER TWOS, THREES: FG%, SHARE, FG%D, D SHARE (+ ranks) |
| `EvanMiya.csv` | team-season | 2011–2026 | O RATE, D RATE, RELATIVE RATING, OPPONENT ADJUST, PACE ADJUST, TRUE TEMPO, INJURY RANK, HOME RANK, ROSTER RANK, KILLSHOTS (+ ranks) |
| `KenPom Preseason.csv` | team-season | | PRESEASON KADJ EM/O/D/T (+ ranks, changes) |
| `Resumes.csv`, `Teamsheet Ranks.csv` | team-season | | NET RPI, RESUME, WAB RANK, ELO, B POWER, Q1–Q4 W/L, BID TYPE; NET, KPI, SOR, BPI, KP, SAG, TRK, quadrant records |
| `Tournament Locations.csv` | team-game (tournament) | 2008–2025 | COLLEGE/GAME CITY, STATE, LATITUDE, LONGITUDE, TIME ZONE (+ value, DST), DIRECTION, LATITUDE/LONGITUDE DIFF, TIME ZONES CROSSED, DISTANCE (KM), DISTANCE (MI) |
| `Tournament Matchups.csv`, `Tournament Simulation.csv`, `Seed Results.csv`, `Upset *`, `Coach Results.csv`, `Conference *` | various | | Tournament results and aggregates |
| `538 Ratings`, `AP Poll Data`, `Heat Check *`, `RPPF *`, `TeamRankings *`, `Z Rating *`, `Public Picks` | team-season | | Other rating systems and public picks |
| `HalfScoring.csv` | team | | GAME/H1/H2 PF, PA, PD |
| `game-logs/{Team}.csv` (69 teams) | team-game, 2025-11-04 to 2026-03-14 | 2025-26 | team, opponent, team_rank, opp_rank, opp_off_rank, opp_def_rank, date, venue, result, t_score_t/o, score_t/o, t_rating_t/o, rating_t/o, t_poss_t/o, poss_t/o, color_rating_t/o. Origin probably an EvanMiya game-log export, judging by the `color_*` columns **(inference, unverified)** |
| `archive/INT _ KenPom _ *.csv`, `DEV _ March Madness.csv`, `REF _ *.csv` | team-season | 1999–2026 | KenPom columns (section 1.5); REF files map conference and ESPN team names |

Team keys: `TEAM NO`, `TEAM ID` are archive-internal; joins go by team name through `REF _ NCAAM Conference and ESPN Team Name Mapping.csv` (`Mapped ESPN Team Name`), then to the ESPN ID through the hoopR team crosswalk.

### 1.7 EvanMiya exports (local, reference only)

Location: `~/Desktop/UnicornProjects/NCAA2026_mArchMadness/data/`. Single snapshot exported mid-March 2026 (file times 17–18 Mar 2026; the files carry no pull-date column). `EvanMiya_Lineups.year` = 2025 for all 762 rows; EvanMiya probably labels a season by its start year (2025 = 2025-26) **(inference, unverified)**.

| File | Grain | Columns |
|---|---|---|
| `EvanMiya_Players.csv` (3,152 rows) | player-season | rank, name, team, obpr, dbpr, bpr, poss, box_obpr, box_dbpr, box_bpr, adj_team_off_eff, adj_team_def_eff, adj_team_eff_margin, plus_minus, players, color_O, color_D, color_Diff |
| `EvanMiya_Teams.csv` (365) | team-season | rank, team, tooltip_team, obpr, dbpr, bpr, opponent_adjust, pace_adjust, off_rank, def_rank, tempo, tempo_rank, rank_inj, home_rank, roster_rank, runs_per_game, runs_conceded_per_game, runs_margin, runs_total, runs_conceded_total, wins, losses, color_*, tooltip_* |
| `EvanMiya_Lineups.csv` (762) | lineup-season | lineup, team, adj_team_off_eff, adj_team_def_eff, adj_team_eff_margin, pred_adj_team_eff_margin, off_poss, def_poss, plus_minus, avg_opp_bpr, team_off_eff, team_def_eff, team_eff_margin, color_* (pred_O/D, height_mean, recruit_rating_mean, games_exp_mean, game_usage_mean, two/three/ft_pct_weighted_mean, oreb/dreb_pct_sum, assist_rate_sum, TO_sum, STL_sum, blk_pct_sum, PF_sum, scoring_mean, position/role raw sd and mean, adj_O/Diff/D, post_O/Diff/D), p_id_string_1..5, year |
| `EvanMiya_TourneySim.csv` | team | team, team2, seed, r32, s16, e8, f4, f2, champ, color_* |
| `injuries.csv` (67) | player | team, player, position, status, injury_type, earliest_return_round, play_probability_r64..champ, notes. Origin not stated in the file; public reports only (R-RG-06) **(unverified)** |
| `matchups.csv`, `narratives.csv`, `social_signals.csv` | | Hand-made inputs of the earlier project; not data sources |

---

## 2. Crosswalk: canonical field × source

Abbreviations: **CB** = CBBD, **E** = ESPN data already pulled, **hE** = hoopR ESPN engine, **hN** = hoopR NCAA engine, **T** = Torvik, **KP** = KenPom (API / Kaggle columns), **KG** = Kaggle archive, **EM** = EvanMiya exports. "—" = not available. Every row also carries `source`, `pull_date`, `licence_class` (prompt rule; R-SR-15 for state fields).

Common transforms used below:
- **id→ESPN**: map a CBBD ID to the ESPN ID via the CBBD `sourceId` (verify, call 2/9), or the hoopR crosswalk for Torvik/KenPom names.
- **clock**: `game_clock_s` = seconds **remaining** in the period (0–1200 in a half, 0–300 in OT; R-DQ-02). From "MM:SS" or "SS.s": m×60 + s. From elapsed `t`: `period_length − t`.
- **ft→m** ×0.3048; **in→cm** ×2.54; **lb→kg** ×0.45359237.
- **season**: sources use the ending year (2026); our `season` is a string. Proposed format "2025-26"; `global_metadata.yaml` does not fix the format.
- **side**: `score_msu`/`score_opp` from home/away scores using MSU's side in that game; `margin = score_msu − score_opp`.

### 2.1 games

| Canonical | Type, unit | CB | E | hE | hN | T / KP / KG / EM | Transform |
|---|---|---|---|---|---|---|---|
| `game_id` | string (ESPN event id) | `/games.sourceId`; plays `gameSourceId` | `games.csv game_id`; Job D `gid` | `game_id` (int) | `espn_game_id` | T: `bart_muid` via `mbb_schedule_crosswalk`; KP: `kp_game_id` (needs login; not used); KG/EM: none (match by date and team pair) | cast to string; the one join key (R-FD-02) |
| `cbbd_game_id` | int | `/games.id`, `gameId` everywhere | — | — | — | — | kept for CBBD calls |
| `ncaa_contest_id` | string | — | — | — | `contest_id` | — | |
| `season` | string | `season` (ending year) | `season` | `season` | `season` | T/KP/KG: YEAR/Season; EM: `year` (start year?) | season transform; EM +1 **(unverified)** |
| `game_type` | enum (global_metadata) | `seasonType`, `conferenceGame`, `tournament`, `gameNotes`, `gameType` | `season_type` + `notes` (Big Ten tournament shows as regular) | `season_type`, `conference_competition`, `notes_headline`, `tournament_id` | — | KG: ROUND (tournament) | rule: exhibition (CB overview `eligibility=exhibition`) / ncaa_tournament (`tournament`=NCAA) / big_ten_tournament (notes) / big_ten (conferenceGame) / non_conference |
| `tip_time_utc` | timestamp UTC | `startDate` (+`startTimeTbd`) | `date_utc` | `game_date_time` | `game_date` (date only, MM/DD/YYYY) | T: date only | CB time zone **(unverified)**, assume UTC "Z" |
| `site` | enum home/away/neutral (MSU view) | `neutralSite`, `homeTeamId` | `site` | `neutral_site`, `home_id` | `location_type` (lineups) | KG Tournament Locations | |
| `home_team_id`, `away_team_id` | string ESPN | `homeTeamId`/`awayTeamId` → id→ESPN | MSU 127 + `opponent_id` | `home_id`, `away_id` | `home_espn_team_id`, `away_espn_team_id` | | |
| `home_score_final`, `away_score_final` | int points | `homePoints`, `awayPoints` | `msu_score`, `opp_score`; Job D box `score` | `home_score`, `away_score` (schedule) | last `home_score` | | side |
| `period_points_home[]`, `_away[]` | list[int] | `homePeriodPoints[]`; `/games/teams teamStats.points.byPeriod[]` | — | — | — | | |
| `n_periods` | int (2 + OT) | `len(homePeriodPoints)` | — | `status_period` | max `period` | | |
| `attendance` | int | `attendance` | `attendance` | `attendance` | — | | |
| `venue_id` | string | `venueId` (CBBD id) | — (name only) | `venue_id` (ESPN) | — | | see venues |
| `broadcast` | string | `/games/media broadcasts[].broadcastName`, `.broadcastType` | `broadcast` | `broadcast_name`, `broadcast_market` | — | | |
| `neutral_site`, `conference_game` | bool | `neutralSite`, `conferenceGame` | `site=='neutral'` | `neutral_site`, `conference_competition` | — | | |
| `status` | enum | `status` | `status` (STATUS_FINAL) | `status_type_name` | — | | map to scheduled/final/… |
| `seed_home`, `seed_away` | int | `homeSeed`, `awaySeed` | — | — | — | KG `SEED` | |
| `elo_pre_home/away`, `elo_post_*` | int | `homeTeamEloStart/End`, `away…` | — | — | — | | pre-game value = as-of before tip |
| `excitement` | float | `excitement` (subset) | — | — | — | KP game attributes (API fanmatch? **unverified**) | |
| `officials` | list | — | not stored (in summary `gameInfo`) | `load_mbb_officials` (columns **unverified**) | — | KP Ref Ratings (web) | FK to referees table (R-FD-08) |
| `pregame_win_prob_home` | float 0–1 | — | — | — | — | T `super_sked`; KP `fanmatch` | as-of before tip |
| `n_pbp_rows` | int | count of /plays | Job D box `n_plays` | count | count | | completeness (R-DQ-07) |

### 2.2 teams

| Canonical | Type | CB | E | hE | hN | T / KP / KG / EM | Transform |
|---|---|---|---|---|---|---|---|
| `team_id` | string ESPN | `/teams.sourceId` | `opponent_id`, Job D `team` | `team_id` | `*_espn_team_id` | crosswalk `espn_team_id` | |
| `cbbd_team_id` | int | `id`, `teamId` | — | — | — | — | |
| `ncaa_team_id` | string | — | — | — | `*_ncaa_team_id` | — | |
| `school`, `mascot`, `abbreviation`, `display_name` | string | `school`, `mascot`, `abbreviation`, `displayName`, `shortDisplayName` | `opponent` (displayName) | `team_location`, `team_name`, `team_abbreviation`, `team_display_name` | `home`/`away`/`event_team` names | T `bart_team` ("Michigan St."); KP `kp_team`/TeamName; KG TEAM (+ REF mapping); EM `team` | names never used as keys; only through crosswalk (R-DS-05) |
| `conference` | string | `conference` (abbr), `conferenceId`; `/conferences/history` for membership by season | Job D ids `conferenceId` | `*_conference_id` | — | T conf; KP conf; KG CONF, CONF ID | per season |
| `home_venue_id` | | `currentVenueId` | — | `home_venue_id` | — | | |
| `colors` | hex | `primaryColor`, `secondaryColor` | — | `team_color`, `team_alternate_color` | — | | display only |

### 2.3 venues

| Canonical | Type, unit | CB | E | hE | hN | KG / other | Transform |
|---|---|---|---|---|---|---|---|
| `venue_id` | string | `/venues.id` (+`sourceId`, maybe ESPN **unverified**) | — | `venue_id` (ESPN) | — | | ESPN venue id proposed as key |
| `venue_name` | string | `name` | `venue` | `venue_full_name` | — | | |
| `city`, `state`, `country` | string | `city`, `state`, `country` | `city` | `venue_address_city`, `_state` | — | KG `GAME CITY/STATE` | |
| `latitude_deg`, `longitude_deg` | degrees | — | — | — | — | KG Tournament Locations `GAME LATITUDE/LONGITUDE` (tournament sites only) | otherwise geocode (computed by us) |
| `capacity` | int seats | — | — | `venue_capacity` | — | KP Arena Capacity (web; blocked) | |
| `indoor` | bool | — | — | `venue_indoor` | — | | |
| `elevation_m` | m | — | — | — | — | — | computed by us (R-FD-11) |
| `main_camera_side`, `floor_template_id` | enum | — | — | — | — | — | manual from video (R-FD-11) |
| `distance_from_campus_km` | km | — | — | — | — | KG `DISTANCE (KM)` (tournament) | computed by us from coordinates |

### 2.4 players (identity and attributes; full detail in `dictionary_players.md`, W1)

| Canonical | Type, unit | CB | E | hE | hN | T / KP / KG / EM | Transform |
|---|---|---|---|---|---|---|---|
| `player_id` | string ESPN athlete id | roster `players[].sourceId`; `/games/players athleteSourceId`; `/stats/player/season athleteSourceId` | `rosters.csv espn_id` | `athlete_id` | — (stats.ncaa.org ids `player_*_id`) | EM `p_id_string_*` (EvanMiya ids **unverified**); T/KP: names only ("no per-player crosswalk") | CB sourceId = ESPN **(verify, call 8/9)** |
| `cbbd_athlete_id` | int | `id`, `athleteId` | — | — | — | — | |
| `ncaa_player_id` | string | — | — | — | `player_1_id`, `shooter_player_id`, `home_k_player_id` | — | name match to ESPN (no published crosswalk) |
| `name`, `first_name`, `last_name` | string | `name`, `firstName`, `lastName` | `name` | `full_name`, `first_name`, `last_name` | `*_clean_name` | EM `name`; T player | |
| `height_cm` (+`height_source`) | cm | roster `height` (unit **unverified**, probably in) ×2.54; recruit `heightInches` ×2.54; draft `height` (unit **unverified**) | `height_cm` | game roster `height` (in) ×2.54, `display_height` ('6-2') | — | T `Height` (format **unverified**); KP team avg heights (in **unverified**) | listed heights run high (R-DQ-09) |
| `weight_kg` (+`weight_source`) | kg | roster `weight` (unit **unverified**, probably lb); recruit `weightPounds` ×0.45359237 | `weight_kg` | `weight` (lb) | — | — | |
| `date_of_birth` | date | roster `dateOfBirth` | — | `date_of_birth`, `age` | — | — | |
| `hometown_city/state/country`, `hometown_lat/lon` | string; degrees | roster and recruit `hometown.{city,state,country,latitude,longitude,countyFips}` | `hometown` (= ESPN birthPlace) | `birth_place_city/state/country` (birthplace) | — | — | keep birthplace and hometown as separate fields; countyFips not stored (proxy risk; brief: no demographic proxies) |
| `position` | enum | `position` | `position` | `position_abbreviation` | — | EM `color_position_raw_*` (lineup level) | |
| `shooting_hand` | enum | — | — | `hand_type`/`hand_abbreviation` (likely empty for NCAA **unverified**) | — | — | otherwise from video (computed by us) |
| `class_year` | enum | derive from `startSeason`/`endSeason` | `class` | `experience_years`, `experience_display_value` | — | KG `EXP` (team) | |
| `draft_year/round/pick` | int | `/draft/picks year, round, pick, overall` | — | `draft_year`, `draft_round`, `draft_selection` | — | T `Pick` (probability) | |

### 2.5 rosters (player × team × season, with jersey history)

| Canonical | Type | CB | E | hE | hN | Other | Transform |
|---|---|---|---|---|---|---|---|
| `team_id`, `season`, `player_id` | keys | `/teams/roster teamSourceId`, `season`, `players[].sourceId` | `season`, `espn_id` | per game: `team_id`, `athlete_id` | lineup names | | |
| `jersey` (+`valid_from_game_id`) | string | `players[].jersey` (season level) | `jersey` (season) | `jersey` / `athlete_jersey` **per game** | — | | per-game ESPN rosters give jersey history (R-FD-03) |
| `starter` | bool per game | `/games/players starter` | — | `starter` | first lineup of the game | | |
| `did_not_play`, `ejected`, `active` | bool per game | `ejected` | — | `did_not_play`, `ejected`, `active` | — | `data/injuries.csv status` (reference) | availability log (R-FD-05) |
| `minutes` | s | `minutes` ×60 | — | `minutes` ×60 | `mins` ×60 | | team minutes = 200 (+25/OT) check (R-DQ-06) |

### 2.6 events (play-by-play)

| Canonical | Type, unit | CB | E | hE | hN | Transform |
|---|---|---|---|---|---|---|
| `event_id` | string | `id` (CBBD) and `sourceId` (ESPN play id **unverified**) | — (not stored) | `id`, `sequence_number`, `game_play_number` | row order (no id) | keep source ids; our own `event_id` |
| `period` | int | `period` | Job D `period` | `period_number` (doc says quarters, see quirks) | `period` (doc quirk) | 1, 2 = halves; 3+ = OT |
| `game_clock_s` | float s, resolution 0.1 (ours) | `secondsRemaining` (int, 1 s); `clock` string | `t0` elapsed (int) | `clock_display_value`; `start_half_seconds_remaining` | `clock` MM:SS; `game_seconds` elapsed | clock transform; source resolution 1 s |
| `wallclock_utc` | timestamp | `wallclock` | — | `wallclock` | — | helps align video (R-SR-01) |
| `event_type` | enum (our vocabulary) | `playType` (vocabulary from `/plays/types`) | type text (code constants) | `type_text`, `type_id` | `event_type`, `event_result` | map table needed per source |
| `event_text` | string | `playText` | — | `text` | `event_description` | |
| `team_id` | string ESPN | `teamId` → id→ESPN; `isHomeTeam` | Job D `team` | `team_id` | `event_team_espn_team_id` | |
| `player_1_id`, `player_2_id` | string | `participants[0..1].id` (order **unverified**) | — | `participants_0/1_athlete_id`, `athlete_id_1/2` | `player_1_id`, `player_2_id` | |
| `score_home_after`, `score_away_after` → `score_msu`, `score_opp`, `margin` | int points | `homeScore`, `awayScore` | — | `home_score`, `away_score`, `score_source` | `home_score`, `away_score` | side |
| `scoring_play`, `score_value`, `shooting_play` | bool, int | `scoringPlay`, `scoreValue`, `shootingPlay` | — | `scoring_play`, `score_value`, `shooting_play` | `shot_value`, `event_result` | |
| `home_win_prob` | float 0–1 | `homeWinProbability` | not stored | — (`espn_mbb_wp` live only) | — | |
| `players_on_floor` | list[string] ×10 | `onFloor[]` (2024+, derived from substitutions) | — | — | `home_1..5`, `away_1..5` (+ ids), `status`, `sub_deviate` | names/ids → ESPN ids |
| `possession_id` | int | — | Job D possession rows (row order per `gid`) | — | `poss_num` | see section 4 |
| `team_in_possession` | enum | — | Job D `team` | — | `poss_team_espn_team_id` | msu / opponent / none |
| `chance_id`, `chance_number` | int | — | `oreb` + 1 per possession (implicit) | — | `is_second_chance` (flag only) | derived by us |
| `is_transition`, `is_fastbreak`, `is_from_turnover`, `is_second_chance`, `is_paint`, `is_garbage_time` | bool | — | Job D `start` (steal, dreb, …) | — | as named | reference labels; ours is R-TR-08 |
| `turnover_type` | enum | `playType` (e.g. `Lost Ball Turnover`) | — | `type_text` | `turnover_type`, `is_team_turnover` | |
| `rebound_type` | enum off/def/team/dead-ball | `playType` (`Offensive Rebound`, `Defensive Rebound`, …) | Job D `start` dreb_*_team, dreb_*_dead | `type_text` (`Dead Ball Rebound` etc.) | `event_type` | |
| `jump_ball` | event | `playType` (name **unverified**) | `Jumpball` (code constant) | `type_text` | `event_type` 'won Jumpball' | R-EV-14 |
| `challenge_outcome` | enum | — | — | — | `challenge_outcome` | R-EV-16 |

### 2.7 substitutions

| Canonical | Type | CB | E | hE | hN | Transform |
|---|---|---|---|---|---|---|
| one row per sub event: `game_id`, `team_id`, `player_id`, `direction` (in/out), `period`, `game_clock_s`, `score_team`, `score_opp` | | `/substitutions/*`: one row **per stint** with `subIn {period, secondsRemaining, teamPoints, opponentPoints}` and `subOut {…}`, `athleteId`, `teamId`, `opponentId` | ESPN feed has `Substitution` plays (skipped by parse.py; not stored) | `type_text == 'Substitution'` rows **(unverified that hoopR keeps them)** | lineups `players_in`, `players_out`, `start_min`; pbp `sub_deviate` | split each CB row into an in event and an out event; 1 s resolution; R-DQ-09 timing errors |

### 2.8 lineups (stints)

| Canonical | Type, unit | CB | hN | EM | Transform |
|---|---|---|---|---|---|
| `lineup_key` | string | `idHash` (CBBD athlete ids joined "-") | `lineup_key`, `lineup_id` | `lineup` string, `p_id_string_1..5` | sorted ESPN ids joined |
| `player_ids[5]` | list | `athletes[] {id, name}` | `player_1..5` | `p_id_string_*` | |
| `stint_start/end_s` | s elapsed | — (game/season aggregates only) | `start_min`, `end_min` ×60; matchup `start_seconds`, `end_seconds` | — | |
| `seconds_on_court` | s | `totalSeconds` | `duration_mins` ×60; `duration_seconds` | — | |
| `possessions`, `opp_possessions` | count | `teamStats.possessions`, `opponentStats.possessions` (event count) | `poss`, `opp_poss`; matchup `n_possessions` | `off_poss`, `def_poss` | definitions differ (section 4) |
| `points`, `opp_points`, `plus_minus` | points | `teamStats.points`, `opponentStats.points` | `pts`, `opp_pts`, `plus_minus` | `plus_minus` | |
| `off_rating`, `def_rating`, `net_rating` | pts/100 poss | `offenseRating`, `defenseRating`, `netRating` | derive | `team_off_eff`, `team_def_eff`; adjusted `adj_team_*` | |
| shot mix per lineup | counts | `twoPointers.jumpers/layups/dunks/tipIns`, `threePointers` | `rima`, `mida`, `tpa`, `*_ast` | — | |

### 2.9 shots (field-goal attempts)

| Canonical | Type, unit | CB | E | hE | hN | T / KG | Transform |
|---|---|---|---|---|---|---|---|
| `event_id`, `game_id`, `team_id`, `shooter_id` | keys | play id; `shotInfo.shooter.id` | — | `athlete_id_1` | `shooter_player_id` | | |
| `made` | bool | `shotInfo.made` | Job D `pts` (aggregate) | `scoring_play` | `made` | | |
| `point_value` | int 2/3 | `scoreValue`; `range == three_pointer` | — | `score_value` | `point_value` | | |
| `shot_family` | enum (rim, mid, three; plus dunk, layup, tip, jumper) | `range` (text-derived); `playType` (JumpShot, LayUpShot, DunkShot, TipShot) | — | `type_text` | `shot_zone`, `shot_type`, `is_paint` | T Dunks/Rim/Mid (aggregates); KG Shooting Splits (team-season) | map to our families |
| `assisted`, `assister_id` | bool, id | `assisted`, `assistedBy.id` | — | `athlete_id_2` (makes) | `assist_player`; possessions `is_assisted` | | |
| `x_m`, `y_m` (rim-centre frame, geometry.py) | m | `location.x`, `.y` (units/origin **unverified**; 2019+) | coordinates not stored | `coordinate_x_raw`, `coordinate_y_raw` (ft) | `shot_x`, `shot_y` (units **unverified**; 2019+), `dist_ft` | | ESPN raw: x_m = s·(x_raw − 25)·0.3048, y_m = y_raw·0.3048; s = ±1 for the attacker's right (sign **unverified**); FTs are fixed by hoopR, so drop them; check r against `dist_ft`×0.3048 for NCAA |
| `r_m`, `theta_deg`, `spot`, `post_zone`, `landmark`, `sector`, `ring` | m, degrees, enums | — | — | — | — | | computed by `geometry.describe(x, y)` |
| `shot_distance_m` | m | — | — | from raw | `dist_ft` ×0.3048 | | |
| `blocked`, `blocker_id` | bool | `playType == 'Block Shot'` row | — | `type_text` | `blk` (aggregates); event rows | | |
| `shot_clock_at_release_s` | s | — | — | — | — | | **video only** |

### 2.10 free throws (one row per attempt)

| Canonical | Type | CB | E | hE | hN | Transform |
|---|---|---|---|---|---|---|
| `ft_sequence_id` | string | — | — | — | (contest, foul event) | derived by linking FTs to the foul |
| `attempt_k`, `attempts_n` | int | in `playText` only (wording **unverified**) | — | `text` | `ft_number`, `ft_attempts`, `ft_awarded` | parse text for CB/hE |
| `made` | bool | `scoringPlay` on `MadeFreeThrow` rows (missed FTs appear to share the type name **(inference)**) | — | `scoring_play` | `event_result` | |
| `award_type` | enum (shooting 2/3, and-one, one-and-one, double bonus, technical, flagrant) | infer from foul + team-foul count | — | infer | `is_shooting_foul`, `is_one_and_one`, `foul_class`, `is_flagrant`, `foul_tech_class` | R-SR-09 |
| `shooter_id` | id | `shotInfo.shooter` (range `free_throw`) | — | `participants_0_athlete_id` | `player_1_id` | |
| `lane_occupants` | list | — | — | — | — | video only |

### 2.11 fouls and whistles

| Canonical | Type | CB | E | hE | hN | T / KP | Transform |
|---|---|---|---|---|---|---|---|
| `foul_type` | enum (R-SR-03) | `playType` (PersonalFoul / Technical Foul / Flagrant Foul names **unverified**) + `playText` | Job D `foul_type` (only `PersonalFoul` captured) | `type_text`, `text` | `foul_class`, `is_shooting_foul`, `is_looseball_foul`, `is_flagrant`, `foul_tech_class` | | offensive / player-control fouls: text or the paired turnover **(unverified)** |
| `fouler_id`, `fouled_id` | id | `participants[]` | — | `participants_0/1` | `player_1`, `player_2` | | |
| `team_fouls_msu`, `team_fouls_opp` (per half) | int | count | count | count | count | | reset at half (Rule 8-2) |
| `bonus_state` | enum | — | — | — | `is_one_and_one` (implies bonus) | | from team-foul count: 7th = one-and-one, 10th = double bonus (Rule 8-2.1, 8-2.2) |
| box totals: fouls, technical, flagrant | int | `teamStats.fouls.{total,technical,flagrant}`; player `fouls` | box `fouls`, `technicalFouls`, `totalTechnicalFouls`, `flagrantFouls` | team/player box | player box `pf`; lineups `foul` | T Foul/40; KP FC/40, FD/40 (web) | |

### 2.12 timeouts

| Canonical | Type | CB | E | hE | hN | Transform |
|---|---|---|---|---|---|---|
| `timeout_type` | enum full, short (30 s), media, official | `playType` (vocabulary **unverified**, see call 4) | `OfficialTVTimeOut`, `ShortTimeOut`, `RegularTimeOut`, `FullTimeOut` (code constants) | `type_text` | `timeout_type` ('short', 'full'), `event_type` | `OfficialTVTimeOut` → media **(inference)** |
| `calling_team_id` | id | `teamId` | — | `team_id` | `event_team` | |
| `game_clock_s` at call | s | `secondsRemaining` | — | clock | `clock` | |
| `timeouts_msu`, `timeouts_opp` (remaining) | int | — | — | — | — | derived from the rules (Rule 5-13, 5-14) |
| media slot (16:00/12:00/8:00/4:00) | enum | — | — | — | — | derived (R-SR-04) |

### 2.13 lines (detail in `docs/markets/collector_design.md` §6)

| Canonical | CB `/lines` | hE pbp | Other |
|---|---|---|---|
| `book` | `lines[].provider` | — | |
| `spread_home` | `spread` (sign **unverified**) | `home_team_spread`, `game_spread` (positive = home favoured), `home_favorite` | KG none |
| `total` | `overUnder` | — | |
| `ml_home`, `ml_away` (American) | `homeMoneyline`, `awayMoneyline` | — | |
| `spread_open`, `total_open` | `spreadOpen`, `overUnderOpen` | — | |
| `snapshot_label`, `source_time_utc` | `close_reported` / `open_reported`, null time (collector_design) | snapshot unknown | |

### 2.14 ratings snapshots (as of a date)

| Canonical | Unit | CB | T | KP | KG | EM | As-of note |
|---|---|---|---|---|---|---|---|
| `rating_system`, `as_of_date` | | season-level (no date) | daily archive / Time Machine; super_sked pre-game | `archive` (by date); preseason | season-end and "Pre-Tournament" | export date (file time only) | R-DS-04: only dated values in backtests |
| `adj_off`, `adj_def`, `adj_net` | pts/100 poss | `/ratings/adjusted offensiveRating, defensiveRating, netRating` (2014+) | `adjoe`, `adjde` | AdjOE, AdjDE, AdjEM | KADJ O/D/EM, BADJ O/D/EM | O RATE, D RATE, RELATIVE RATING; obpr/dbpr/bpr | |
| `tempo_adj`, `tempo_raw` | poss/40 min | `pace` (raw) | `adjt` | AdjTempo, Tempo | KADJ T, BADJ T, RAW T | tempo, TRUE TEMPO | |
| `barthag` | probability | — | `barthag` | — | BARTHAG | — | |
| `srs`, `elo` | points | `/ratings/srs rating`, `/ratings/elo elo` (season end); `/games` Elo start (pre-game) | — | — | ELO (Resumes) | — | Elo start is point-in-time |
| `poll_rank` | int | `/rankings ranking` (week, pollDate) | — | — | AP RANK | — | weekly |
| `wab`, `sos` | | — | WAB, sos variants | SOS | WAB, ELITE SOS | — | |
| `avg_possession_length_s` | s | — | — | Avg Possession Length (Offense/Defense) | via INT KenPom files | — | |
| player impact | | `/stats/player/season PORPAG, winShares, usage, offensiveRating` | PORPAGATU!, BPM, Role | ORtg, %Poss (web) | — | bpr, obpr, dbpr | |

### 2.15 recruiting and transfers

| Canonical | Type, unit | CB | T | KG | EM |
|---|---|---|---|---|---|
| `recruit_year` | int | `/recruiting/players year` | — | — | — |
| `stars`, `rating`, `ranking` | int, 0–1, int | `stars`, `rating`, `ranking` | RecruiT-Rank (player season) | TALENT (team) | `color_recruit_rating_mean` (lineup) |
| `high_school` | string | `school`, `schoolId` | — | — | — |
| `committed_to_team_id` | id | `committedTo.id` → id→ESPN | — | — | — |
| `height_cm`, `weight_kg` | cm, kg | `heightInches` ×2.54, `weightPounds` ×0.45359237 | — | — | — |
| `hometown_*` | | `hometown.*` | — | — | — |
| `team_recruit_rank`, `team_recruit_rating` | | `/recruiting/teams ranking, rating` | — | — | — |
| transfer: `origin_team_id`, `destination_team_id`, `eligibility`, `years_remaining`, `portal_year` | | `/recruiting/portal origin, destination, eligibility, yearsRemaining, year, stars, rating` | transfer lists (web) | — | — |

---

## 3. State fields by source

Time resolution is in brackets. "Derived" means computable from that source's events but not given directly.

| State field | CBBD | ESPN pulled (reference) | hoopR ESPN | hoopR NCAA engine | Torvik / KenPom / Kaggle / EvanMiya |
|---|---|---|---|---|---|
| Game clock | `secondsRemaining` int [1 s]; `clock` string (tenths below 1:00? **unverified**) | `t0` [1 s observed on 1.71 M rows] | `clock_display_value`, `*_seconds_remaining` [1 s **(unverified)**] | `clock` MM:SS, `game_seconds` [1 s] | none |
| Shot clock | **none** | none | none | none | none (KP avg possession length only, season) |
| Wall clock | `wallclock` [s, nullable] | not stored | `wallclock` | none | none |
| Score after each event | yes [event] | possession `pts` only | yes [event], `score_source` | yes [event] | none |
| Substitutions | yes, 2024+ (2013: 212 games) [1 s] | in feed, not stored | `Substitution` rows **(unverified)** | reconstructed stints 2010+ [1 s], `sub_deviate`, `player_count_error` | none |
| Players on floor (10) | `onFloor` per play, 2024+ | none | none | `home_1..5`, `away_1..5` per event, 2010+ | EM lineups (season aggregate) |
| Foul events | yes, via `playType` and text [event] | first defensive foul time per possession | yes | yes [event] | none |
| Foul type detail | coarse: personal / technical / flagrant names, shooting only in text | `PersonalFoul` only | coarse (as ESPN) | `foul_class`, shooting, loose-ball, flagrant, technical subclass | none |
| Team fouls per half / bonus | derived | derived (partial) | derived | derived; `is_one_and_one` flag | none |
| Free-throw sequence (k of n) | text only | none | text only | `ft_number`, `ft_attempts`, `ft_awarded` | none |
| FT award type | inferred | none | inferred | flags (shooting, one-and-one, flagrant, technical) | none |
| Timeouts (type, team) | `playType` [event] (vocabulary call 4) | `OfficialTVTimeOut`, `ShortTimeOut`, `RegularTimeOut`, `FullTimeOut` in feed, not stored | `type_text` | `timeout_type` short/full | none |
| Timeouts remaining | derived | — | derived | derived | none |
| Media timeout | `playType` if ESPN's `OfficialTVTimeOut` is kept **(unverified)** | in feed | `type_text` | not distinguished **(unverified)** | none |
| Coach's challenge / review | none known | none known | none known | `challenge_outcome` | none |
| Jump ball / arrow | jump-ball play type **(unverified)**; arrow derived | `Jumpball` in feed | `type_text` | 'won Jumpball' | KP Jump Ball Ratings (web, blocked) |
| Possession / team in control | none (lineup event counts only) | Job D derived possessions | none | `poss_num`, `poss_team`, `poss_length` [1 s] | none |
| Chance (OREB count) | derived | `oreb` per possession | derived | `is_second_chance` | none |
| Transition / garbage time | none | Job D start types (steal, dreb) | none | `is_transition`, `is_fastbreak`, `is_from_turnover`, `is_garbage_time` | Haslametrics removes garbage time (not in scope) |
| Shot coordinates | `location {x, y}` 2019+, many missing, units **unverified** | not stored | raw ft, 2006+ (2003) | `shot_x/shot_y`, `dist_ft`, `shot_zone`, 2019+ | aggregates only (Torvik rim/mid; KG shooting splits) |
| Shot type | `range` (text-derived), `playType` | none | `type_text` | `shot_type`, `shot_zone`, `is_paint` | aggregates |
| Assists | `assisted`, `assistedBy` | none | `athlete_id_2` | `assist_player` | aggregates |
| Win probability | `homeWinProbability` per play | not stored | live function only | none | pre-game: T super_sked, KP fanmatch |
| Officials | none | not stored | `load_mbb_officials` per game | none | KP Ref Ratings (web) |
| Ejections | `ejected` (player box) | none | `ejected` | none | none |
| Ball position, player positions, ball control, restarts, lane occupants | **none in any source**: video only (R-SR-06, R-SR-07, R-SR-08) | | | | |

Conclusion for R-SR and R-SB: no source gives shot clock, sub-second game clock, timeouts remaining, ball state or positions. Those come from scoreboard OCR and CV. PBP sources anchor score, fouls, substitutions, free throws and timeouts at 1 s resolution. Only the hoopR NCAA engine labels foul subtypes and free-throw sequences directly.

---

## 4. Possession and chance definitions by source

**Ours** (R-MD-04; live doc "a possession ends only when the other team gains control; every offensive rebound or shot-clock reset starts a new chance inside it"; R-SY-05): a possession runs from one team gaining control until the other team gains control. Chances are shot-clock cycles inside it, starting at 30 s, or 20 s after an offensive rebound off the ring (Rule 2-11.6.d.1). End of period closes the possession.

| Source | Possession definition | Chance definition | Difference from ours |
|---|---|---|---|
| CBBD, game and season level | Stored `possessions` per team-game; the formula is not in the public service code **(unverified)**. Pace = 40 × (poss + opp_poss) / (2 × gameMinutes); rating = 100 × points / possessions (`games/service.ts`) | none | If it is a box estimate (FGA − ORB + TO + k·FTA), it does not split a possession at an offensive rebound, so it is close to ours on average, but it is not event-exact |
| CBBD, lineup level | **Event count**: plays by the lineup's team of type `Lost Ball Turnover` or `Defensive Rebound`, or any scoring play that is not `MadeFreeThrow`; the same with `<>` for the opponent (`lineups/service.ts`) | none | Counts only one turnover type, counts the team's own defensive rebounds (which end the *opponent's* possession), and skips FT-only possessions. As written it is not a possession-end count by our definition **(reading of the code; intent unverified)**. Do not use CBBD lineup possessions as a denominator without re-deriving |
| ESPN feed | No possession field | none | n/a |
| ESPN pulled, Job D `parse.py` (reference only) | New possession on: steal (stealing team), turnover (the team that lost it, then `dead_to` pending for the other), defensive rebound including team and dead-ball rebounds, the other team's first event after a made FG or made last FT, period start. Offensive rebound **does not** start a new possession (`oreb += 1`). Technical-foul FTs excluded; jump balls ignored | implicit: chances = `oreb` + 1 | Matches ours on the offensive-rebound rule. Start times are back-dated to the previous make or turnover. No held-ball or arrow handling; foul-only resets (kicked ball, 20 s reset after a foul) are not chances. Unrecognised starts are `unknown` (5,794 of 1.71 M rows) |
| hoopR ESPN | No possession field | none | n/a |
| hoopR NCAA engine | `poss_num`/`poss_team` by event; possession table with `start_event_type`, `first_shot_time`, `last_event_type`; `is_second_chance` = "possession followed an offensive rebound" | flag only | Whether `poss_num` increments on an offensive rebound is **(unverified)**; the wording suggests it does not (matches ours). Verify on one game against CBBD PBP |
| Torvik | Game possessions shown on `box.php`; tempo = possessions per 40 min. Formula **(unverified)** | none | Box estimate, OREB subtracted |
| KenPom | Possessions = FGA − OR + TO + 0.475 × FTA (glossary, catalog §1.1); AdjT = possessions per 40 min; "Avg Possession Length" (offense and defense, seconds) from PBP, definition **(unverified)** | none | Box estimate; −OR means an offensive rebound does not add a possession (consistent with ours in total) |
| Kaggle archive | Inherits KenPom (`K TEMPO`, `KADJ T`) and Torvik (`RAW T`, `BADJ T`, `PPPO`, `PPPD` = points per possession) | none | as KenPom/Torvik |
| EvanMiya | `poss`, `off_poss`, `def_poss` from PBP on-court data (catalog §1.3); definition **(unverified)** | none | unknown |

Check to run once data is in (R-DQ-06, R-MD-04): per game, our event-derived possessions vs KenPom formula vs hoopR `poss_num` vs Job D count; expected within ±2 per team. Our chances − possessions should equal live-ball offensive rebounds plus other resets.

---

## 5. Verification calls for the main session (CBBD key; 19 calls)

Rules: one call each; cache the raw body and headers privately (R-DQ-05); log `X-CallLimit-Remaining` from the first response; never commit bodies. Season 2026 = 2025-26. The MSU team string is assumed to be `Michigan State` (call 1 confirms it). `{G}` = the CBBD `id` of ESPN game 401856571 (UConn, NCAA East Sweet 16, 2026-03-28), taken from call 2's response (no extra call).

| # | Call | Confirms |
|---|---|---|
| 1 | `GET /teams?conference=B1G&season=2026` | Key works for basketball; quota header; conference string ("B1G" vs "Big Ten"); MSU `school` string; `sourceId` = ESPN team id (MSU = 127) |
| 2 | `GET /games?season=2026&team=Michigan State` | `sourceId` = ESPN event id (match all 2025-26 rows of `registry/games.csv`); `startDate` time zone; `gameType`/`tournament`/`gameNotes` vocabulary (Big Ten tournament, NCAA); `homePeriodPoints` length for OT games; Elo start/end; `venueId`; row count vs registry |
| 3 | `GET /plays/game/{G}` | `playType` names in practice (fouls, timeouts, FT, jump ball, substitution); `clock` string format and tenths; `secondsRemaining` int; `period` numbering for halves; `onFloor` filled (10 players); `participants` order; FT text ("1 of 2" wording); `shotInfo.location` units, origin and orientation (compare a known three to 6.75 m, i.e. 22.15 ft); `wallclock` filled; `sourceId` = ESPN play id |
| 4 | `GET /plays/types` | Full play-type vocabulary: foul subtypes, timeout types (incl. official/media), jump ball, review/challenge, dead-ball rebound |
| 5 | `GET /substitutions/game/{G}` | One row per stint (subIn/subOut); both teams; first-half starters' subIn at 1200 s; the sum of stint seconds = 200 min per team |
| 6 | `GET /lineups/game/{G}` | `idHash` format; `totalSeconds` per team = 2,400 (+300/OT); lineup `possessions` vs our count (section 4 quirk) |
| 7 | `GET /games/teams?season=2026&team=Michigan State` | `possessions`, `rating`, `pace`, `gameScore` values vs KenPom formula; `points.byPeriod`; `largestLead`; team-box parity with the ESPN box strings (reference) |
| 8 | `GET /games/players?season=2026&team=Michigan State` | `athleteSourceId` = ESPN athlete id (vs `registry/rosters.csv espn_id`); `minutes` unit; `starter`, `ejected` filled |
| 9 | `GET /teams/roster?season=2026&team=Michigan State` | `height`/`weight` units (inches/lb?); `sourceId` = ESPN id; `jersey`; `hometown` lat/lon filled; `dateOfBirth` coverage; fills the players missing from `rosters.csv` (e.g. Carson Cooper) |
| 10 | `GET /teams/roster?season=2027&team=Michigan State` | Preseason 2026-27 roster available now (W1 cards) |
| 11 | `GET /lines?season=2026&team=Michigan State` | Providers present; spread sign (home favourite < 0?); `spreadOpen` coverage; `gameId` = /games `id` |
| 12 | `GET /lines/providers` | Provider list (collector_design C-rules) |
| 13 | `GET /ratings/adjusted?season=2026&team=Michigan State` | One row per season, no date: confirms not point-in-time (R-DS-04) |
| 14 | `GET /rankings?season=2026&team=Michigan State` | Weekly rows with `pollDate` (point-in-time poll rank) |
| 15 | `GET /recruiting/players?year=2026&team=Michigan State` | `heightInches`/`weightPounds` present; `athleteId` links to roster `id`; rating scale (0–1?); hometown coordinates |
| 16 | `GET /recruiting/portal?year=2026&destinationTeam=Michigan State` | `year` = portal cycle semantics; `eligibility` values; origin/destination ids |
| 17 | `GET /venues` | Field set really lacks capacity, coordinates and elevation; `sourceId` = ESPN venue id; Breslin Center row |
| 18 | `GET /draft/picks?sourceTeam=Michigan State` | `height` unit; `athleteId` link; college association coverage |
| 19 | `GET /plays/team?season=2026&team=Michigan State&shootingPlaysOnly=true` | Share of MSU shots with `location` in a full season (coordinate coverage); `range` distribution; payload size for planning bulk pulls (R-DS-13) |

Total 19 of the 50-call prompt budget.

---

## 6. Gaps and decisions

Gaps (no source fills them):
1. **Shot clock** at any resolution, and game clock below 1 s: only scoreboard OCR or video (R-SR-01).
2. **Timeouts remaining, team fouls/bonus state, media-timeout slot, arrow**: derived from events plus rules; no source states them.
3. **Coach's challenge / review**: only the hoopR NCAA engine (`challenge_outcome`); CBBD/ESPN support unknown (call 4).
4. **Free-throw sequence and award type**: explicit only in the hoopR NCAA engine; CBBD/ESPN need text parsing.
5. **Foul subtypes** (offensive, player-control, shooting): explicit only in the NCAA engine.
6. **Venue coordinates, elevation, camera side**: no source except Kaggle tournament sites; capacity only in hoopR schedules.
7. **Point-in-time ratings in CBBD**: only Elo start and polls. Adjusted/SRS/Elo endpoints are season-level, so use Torvik daily archive or the KenPom API archive (R-DS-04, R-FD-06).
8. **Lineups before 2023-24**: CBBD has none (2014–2023); only the hoopR NCAA engine (2010+, stats.ncaa.org terms unverified).
9. **ESPN pulled files** keep no raw plays, so they cannot serve the events table even as reference. Only possession summaries and team box strings exist.
10. **Units not documented** for CBBD roster/draft height and weight, CBBD `shotInfo.location`, NCAA `shot_x/shot_y`, Torvik player height.
11. **Torvik `getadvstats`** positional columns are not mapped (no header; docs opened lacked names).
12. **EvanMiya exports** carry no pull date; the `game-logs/` origin is inferred.
13. **CBBD lineup possessions** use an event count that does not match a possession-end definition (section 4).
14. **hoopR docs** describe quarters for men's PBP (copied schema); verify period numbering in the files.

Decisions for Aldemir (one line each):
- D1. hoopR ESPN-engine release files: model input (R-DS-10 "hoopR releases") or reference only (ESPN terms, BOARD 13:45Z)?
- D2. Torvik files: confirm "model input allowed" despite no published terms page.
- D3. Kaggle March Madness archive (`archive-3/`, `archive/`): reference only (it contains KenPom-web columns), private Drive copy only?
- D4. `registry/games.csv` and `rosters.csv` are ESPN pulls in the public repo. Keep them as identifiers and facts only, or rebuild them from CBBD `/games` and `/teams/roster` after calls 2 and 9?
- D5. `rosters.csv` keeps `headshot_url` (a face image link); drop the column, given the no-face-data rule?

---

## 7. Sources opened (18 Oct 2026)

URLs opened (each fetched successfully unless noted):
- https://api.collegebasketballdata.com/api-docs.json (OpenAPI 1.30.1; saved privately to the scratchpad)
- https://api.collegebasketballdata.com/data-availability.md
- https://api.collegebasketballdata.com/usage-and-access.md
- https://api.github.com/repos/CFBD/cbb-api/git/trees/main?recursive=1
- https://raw.githubusercontent.com/CFBD/cbb-api/main/src/app/lineups/service.ts
- https://raw.githubusercontent.com/CFBD/cbb-api/main/src/app/plays/service.ts
- https://raw.githubusercontent.com/CFBD/cbb-api/main/src/app/substitutions/service.ts
- https://raw.githubusercontent.com/CFBD/cbb-api/main/src/app/games/service.ts
- https://hoopr.sportsdataverse.org/reference/load_mbb_pbp.html (the `load_mbb_team_box`, `load_mbb_player_box`, `load_mbb_schedule`, `load_mbb_shots` pages are redirect stubs to it; the `load_ncaa_mbb_pbp` and `load_ncaa_mbb_possessions` stubs redirect to `load_ncaa_mbb_lineups`)
- https://hoopR.sportsdataverse.org/reference/index.html
- https://hoopR.sportsdataverse.org/reference/load_ncaa_mbb_lineups.html
- https://hoopR.sportsdataverse.org/reference/espn_mbb_game_all.html
- https://hoopR.sportsdataverse.org/reference/espn_mbb_game_player_box.html
- https://hoopR.sportsdataverse.org/reference/mbb_team_crosswalk.html
- https://hoopR.sportsdataverse.org/reference/mbb_player_crosswalk.html
- https://hoopR.sportsdataverse.org/reference/mbb_schedule_crosswalk.html
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/load_mbb.R
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/espn_mbb_data.R
- https://raw.githubusercontent.com/sportsdataverse/hoopR/main/R/hoopR_schemas.R
- https://cbbdata.aweatherman.com/reference/cbd_torvik_player_season.html, cbd_torvik_game_box.html, cbd_torvik_player_game.html, cbd_torvik_ratings_archive.html, cbd_torvik_game_stats.html (opened; no column lists)
- https://api.github.com/repos/andreweatherman/toRvik/contents/R and raw `R/bart_player_season.R`, `bart_player_game.R`, `bart_game_box.R`, `bart_season_schedule.R`, `bart_archive.R` (opened; no column names)

Not opened: barttorvik.com, kenpom.com, any ESPN endpoint, any keyed CBBD endpoint. Torvik and KenPom facts come from `docs/research/data_sources_catalog.md`.

Local files read: `docs/research/data_sources_catalog.md`, `docs/markets/collector_design.md` (CBBD sections), `docs/research/espn_sr_massey_access.md` (opening), `schema/global_metadata.yaml`, `config/vocabulary_map.yaml`, `config/court_ncaa_men.yaml`, `src/msu_alpha/geometry.py`, `registry/*.csv` (headers), `registry/README.md`, `src/msu_alpha/data/espn_registry.py`, `coord/prompts/003-…md`, `coord/BOARD.md`, the live requirement exports (scratchpad), `docs/rules/PRMBB_RulesBook.pdf` (Rule 5-6, 5-13, 8-2 via pdftotext; parent rule numbers inferred from the table of contents), Job D `parse.py`, `run.py`, `fetch.py`, `ids.py`, `extra.py`, `analyze.py` (head) and key/type/value-count summaries of `poss_*.jsonl`, `box_*.jsonl`, `ids_2026.json`, `good_2026.json`; header lines of every CSV in the Kaggle `archive-3/`, `archive-3/game-logs/Duke.csv`, `archive/` and `data/`.

---

## Verified against real responses (2026-10-18)

Added 18 Oct 2026 (prompt 003 verification). Sections 0–7 above stay as written; where they disagree with this section, **this section wins** for CBBD and for the KenPom tool output.

What was read: the 20 CBBD responses pulled today by the main session with a free key (21 calls; `X-CallLimit-Remaining` fell from 999 to 979 of 1,000), cached privately under `~/MSU-Alpha-3-private/data/licensed/cbbd/2026-10-18/`, and 4 responses from the connected KenPom (Parse.bot) tool, cached under `.../licensed/kenpom/2026-10-18/` (Aldemir approved the tool's use in chat on 2026-10-18; licence class **reference only** pending his decision). **No API call was made for this section.** Every figure below is a field name, a type, a range, a count or a check result. No data rows are copied; ranges are given only to fix units and scales.

Type codes as in section 1.1: `i` integer, `n` float, `s` string, `b` boolean, `dt` ISO date-time string, `?` = null seen, `[]` = array. "n=" is the number of rows looked at.

### V.1 Calls and what each one settled

| # | File (private) | Call | Rows | Settles |
|---|---|---|---|---|
| 1 | `01_teams_b1g` | `/teams?conference=B1G&season=2026` | **0** (empty list, HTTP 200, no error) | `B1G` is not a valid conference value; the filter fails silently |
| 20 | `20_teams_bigten` | `/teams?conference=Big Ten&season=2026` | 18 | Conference string is **`Big Ten`** (conferenceId 10); MSU CBBD team id **169**, `sourceId` **127** |
| 2 | `02_games_msu` | `/games?season=2026&team=Michigan State` | 35 | `sourceId` = ESPN event id; time zone; tournament vocabulary |
| 3 | `03_plays_game` | `/plays/game/372596` | 470 | CBBD game 372596 = ESPN 401856571 (UConn); clock, play types, participants order, coordinates |
| 4 | `04_plays_types` | `/plays/types` | 35 | Play-type vocabulary |
| 5 | `05_subs_game` | `/substitutions/game/372596` | 86 | Stint grain, 1 s resolution |
| 6 | `06_lineups_game` | `/lineups/game/372596` | 28 | Lineup grain, `idHash`, possession count |
| 7 | `07_games_teams` | `/games/teams?season=2026&team=Michigan State` | 35 | Box possessions, rating, pace |
| 8 | `08_games_players` | `/games/players?...` | 35 games, 396 player rows | `athleteSourceId` = ESPN, minutes unit |
| 9, 10 | `09_roster_2026`, `10_roster_2027` | `/teams/roster` | 15 + 15 players | height/weight units, `dateOfBirth`, `startSeason` meaning |
| 11, 12 | `11_lines`, `12_line_providers` | `/lines`, `/lines/providers` | 35 games, 69 lines; 6 providers | Spread sign |
| 13 | `13_ratings_adj` | `/ratings/adjusted?season=2026&team=Michigan State` | 1 | Season-level, no date; rank fields |
| 14 | `14_rankings` | `/rankings?season=2026&team=Michigan State` | 41 | Weekly poll rows with `pollDate` |
| 15, 16 | `15_recruit_2026`, `16_portal_2026` | `/recruiting/players`, `/recruiting/portal` | 4, 1 | Recruiting and portal fields |
| 17 | `17_venues` | `/venues` | 989 | No capacity, coordinates or elevation |
| 18 | `18_draft` | `/draft/picks?sourceTeam=Michigan State` | 20 | Draft height/weight units |
| 19 | `19_plays_team_shooting` | `/plays/team?season=2026&team=Michigan State&shootingPlaysOnly=true` | 5,368 plays, 35 games | Coordinate coverage and frame over a season |

### V.2 Field lists per endpoint (observed)

**`/teams`** (n=18): id i; sourceId s (ESPN team id, 3–4 digits); school s; mascot s; abbreviation s; displayName s; shortDisplayName s; primaryColor s (6 hex, no `#`); secondaryColor s; currentVenueId i (all 18 exist in `/venues`); currentVenue s; currentCity s; currentState s (2 letters); conferenceId i; conference s (`Big Ten`, full name, not an abbreviation); logos[] s (16 URLs per team). All non-null.

**`/games`** (n=35): id i (CBBD, 6 digits); sourceId s (ESPN event id, 9 digits); seasonLabel s (`20252026`); season i (2026); seasonType s {regular, postseason}; tournament s? (only `NCAA` seen; null on Big Ten tournament and early-season events); startDate dt (UTC, `...Z`, millisecond format); startTimeTbd b; neutralSite b; conferenceGame b; gameType s {`STD`, `TRNMNT`}; status s (`final`); gameNotes s? (event headline, e.g. Big Ten Tournament round, NCAA region and round, MTE names; 7 of 35 filled); attendance i (0–19,445; one game has 0, read 0 as unknown); homeTeamId / awayTeamId i (CBBD); homeTeam / awayTeam s; homeConferenceId / awayConferenceId i; homeConference / awayConference s (full names: `Big Ten`, `Big East`, `ACC`, `SEC`, `American`, `Mountain West`, `MAC`, `Ivy`, `Horizon`, `Patriot`, `Summit`); homeSeed / awaySeed i? (NCAA games only); homePoints / awayPoints i; homePeriodPoints[] / awayPeriodPoints[] i (length 2, or 3 with one OT); homeWinner / awayWinner b; homeTeamEloStart / EloEnd, away… i (all 35 filled, range about 1,300–2,400); excitement n? (26 of 35 filled, range **1.1–11.1**); venueId i (all exist in `/venues`); venue s; city s; state s. **Not returned:** teams' ESPN ids (only CBBD ids; map through `/teams` sourceId).

**`/games/teams`** (n=35, one row per MSU game): gameId, season, seasonLabel, seasonType, tournament?, startDate, startTimeTbd, teamId, team, conference, teamSeed?, opponentId, opponent, opponentConference, opponentSeed?, neutralSite, isHome, conferenceGame, gameType, notes?, gameMinutes i (40 or 45), pace n (59.5–83). `teamStats` / `opponentStats`: possessions **i** (59–83), assists, steals, blocks i; trueShooting n (% scale, 40.8–72); rating n (points per 100 possessions, 72.9–144.4); gameScore n; points {total, byPeriod[], largestLead, fastBreak, inPaint, offTurnovers} i; fieldGoals / twoPointFieldGoals / threePointFieldGoals / freeThrows {made i, attempted i, pct n on a **0–100** scale}; turnovers {total, teamTotal} i; rebounds {offensive, defensive, total} i; fouls {total, technical, flagrant} i; fourFactors {effectiveFieldGoalPct, freeThrowRate, turnoverRatio, offensiveReboundPct} n, **all on a 0–100 (percent) scale** (turnoverRatio 5.6–33.3). No nulls seen.

**`/games/players`** (n=35 games, 396 player rows): game header as `/games/teams` plus gamePace n; players[]: athleteId i (CBBD), athleteSourceId s (ESPN athlete id, 7 digits), name s, position s {G, F, C}, starter b, ejected b (all false), **minutes i** (whole minutes, 1–43; per game they sum to exactly 200 or 225, so they are rounded to fit), points, turnovers, fouls, assists, steals, blocks i; gameScore n; offensiveRating n? (0–274.7), defensiveRating n?, netRating n?, usage n? (0–38.9, %), effectiveFieldGoalPct n? (0–150), trueShootingPct n? (0–150), assistsTurnoverRatio n?, freeThrowRate n? (0–450), offensiveReboundPct n? (0–100); fieldGoals / twoPointFieldGoals / threePointFieldGoals / freeThrows {made, attempted, pct 0–100}; rebounds {offensive, defensive, total}. Rate fields are null for a quarter of rows (low minutes) and exceed 100 on tiny samples.

**`/plays/game/{id}`** (n=470) and **`/plays/team`** (n=5,368 shooting plays): gameId i; gameSourceId s; gameStartDate dt; season i; seasonType s; gameType s; tournament s?; id i (CBBD; contiguous within a game; **sorting by `id` gives chronological order**; file order and ESPN `sourceId` order differ inside the same second); sourceId s (18 digits = ESPN game id + 9 digits, the ESPN play id form); playType s; isHomeTeam b?; teamId i?; team s?; conference s?; teamSeed i?; opponentId i?; opponent s?; opponentConference s?; opponentSeed i?; homeScore i; awayScore i; homeWinProbability n? (**null for every play in 9 of 35 games**, including all 3 NCAA tournament games); period i (1, 2; 3 = OT seen in 2 games); clock s (`M:SS` or `MM:SS`; **no tenths, also under one minute**); secondsRemaining i (0–1200; equals the clock string in 470 of 470); scoringPlay b; shootingPlay b; scoreValue i (0–3); wallclock dt (filled on every play in both files; whole seconds; **not monotonic** in play order); playText s (may contain a newline); participants[] {id i, name s} (0–2 entries); onFloor[] {id i, name s, team s}; shotInfo? {shooter {id, name}, made b, range s {rim, jumper, three_pointer, free_throw}, assisted b, assistedBy {id?, name?}, location {x n?, y n?}}. Team fields are null on 14 of 470 plays (TV timeouts, period/game end, one jump ball).

**`/plays/types`** (n=35): id i, name s. Names (31 distinct): Block Shot; Coach's Challenge (Overturned); Coach's Challenge (Stands); Dead Ball Rebound; Defensive Rebound; DunkShot; End Game; End Period; Foul Turnover; Free Throw 1 of 1; JumpShot; Jumpball; LayUpShot; LayupShot; Lost Ball Turnover; MadeFreeThrow; Not Available; Offensive Charge; Offensive Rebound; OfficialTVTimeOut; PersonalFoul; RegularJumpShot; RegularTimeOut; ShortTimeOut; Shot; Steal; Substitution; Technical Foul; Three Point Jump Shot; Three Pointer; TipShot. Four names appear twice under different ids (JumpShot, LayUpShot, DunkShot, TipShot: a 5xx id and a 20xxx id). The 5xx ids (e.g. 519 PersonalFoul, 540 MadeFreeThrow, 558 JumpShot) follow ESPN's play-type numbering, which supports the "CBBD plays come from ESPN" inference in section 1.1 (still an inference). **No `Flagrant Foul` and no `FullTimeOut` type exists**, although team boxes carry flagrant counts.

**`/substitutions/game/{id}`** (n=86): gameId i; startDate dt; teamId i; team s; conference s; athleteId i (CBBD); athlete s; position s {G, F, C}; opponentId i; opponent s; opponentConference s; subIn / subOut {period i, secondsRemaining i, teamPoints i, opponentPoints i}. No ESPN ids.

**`/lineups/game/{id}`** (n=28, both teams): teamId i; team s; conference s; idHash s; athletes[5] {id i, name s}; totalSeconds i (4–1,053); pace n (0–300); offenseRating n?, defenseRating n?, netRating n? (null when a side had 0 possessions; range up to ±200–300 on short lineups); teamStats / opponentStats {points, possessions, assists, steals, turnovers, blocks, defensiveRebounds, offensiveRebounds i; trueShooting n?; fieldGoals, freeThrows, twoPointers {+ tipIns, dunks, layups, jumpers}, threePointers {made, attempted, pct 0–100}; fourFactors {effectiveFieldGoalPct, turnoverRatio (**0–1 scale here**, unlike `/games/teams`), offensiveReboundPct, freeThrowRate}}.

**`/lines`** (n=35 games, 69 provider lines): gameId i (= `/games` id, 35 of 35); season i; seasonType s; startDate dt; homeTeamId i; homeTeam s; homeConference s; homeScore i; awayTeamId i; awayTeam s; awayConference s; awayScore i; lines[] (1–3 per game) {provider s (only Bovada, Draft Kings, ESPN BET appear for these games), spread n (−30.5 to +22.5), overUnder n, homeMoneyline i? / awayMoneyline i? (null on 25 of 69 lines; magnitudes up to 100,000), spreadOpen n (69 of 69 filled; equal to spread on 25), overUnderOpen n? (1 null)}. Still no timestamps and no spread or total prices.

**`/lines/providers`** (n=6): id i, name s: Bovada, Draft Kings, ESPN BET, consensus, numberfire, teamrankings.

**`/ratings/adjusted`** (n=1): season i; teamId i; team s; conference s; offensiveRating n; defensiveRating n; netRating n; rankings {offense, defense, net} i. **No date, week or as-of field.**

**`/rankings`** (n=41): season i; seasonType s {regular, postseason}; week i (1–20); pollDate dt (22 distinct dates from mid-October to the postseason); pollType s (**`AP Top 25`, `Coaches Poll`**, not the `ap`/`coaches` parameter values); teamId **i** (spec says number); team s; conference s; ranking i; points i; firstPlaceVotes i.

**`/recruiting/players`** (n=4): id i; sourceId s (8 digits; not an ESPN athlete id; probably the recruiting service's id, **unverified**); position s {PG, SG, PF, C} (finer than roster positions); schoolId i; school s (high school or academy); hometown {city s, state s, country **null on all**, latitude n, longitude n, countyFips s}; committedTo {id i (CBBD team id), name s, conference s}; **athleteId null on all 4** (no link to the roster or box ids; join by name plus team and year); year i; name s; heightInches i (71–84); weightPounds i (165–244); stars i (all 4); rating n (about 0.97–0.99 on this sample, a 0–1 composite-style scale); ranking i (national rank; **does not match the 247Sports Composite rank** recorded from the school bios for the same players, so the upstream ranking is unnamed).

**`/recruiting/portal`** (n=1): id i; sourceId s (8 digits); year i (portal cycle, 2026 = spring 2026 entry); firstName s; lastName s; position s; origin {id i, name s, conference s}; destination {id i, name s, conference s}; stars i; rating n (0–1 scale); eligibility s (`Immediate` seen); **yearsRemaining null**. No height, weight or athlete id.

**`/teams/roster`** (n=1 team per season; 15 players in each of 2026 and 2027): teamId i; teamSourceId s (`127`); team s; conference s; season i; players[]: id i (CBBD athlete id, = `athleteId` elsewhere), sourceId s (ESPN athlete id), name s, firstName s, lastName s (suffix such as `Jr.` stays in lastName), jersey s, position s {`Guard`, `Forward`, `Center`} (long form; **null for 5 of 15 newcomers** in the 2027 roster), **height i = inches** (70–86), **weight i = pounds** (178–266), hometown {city s, state s, country **null on all 30**, latitude n? , longitude n?, countyFips s?} (lat/lon filled on 29 of 30), **dateOfBirth null on all 30**, startSeason i, endSeason i. `startSeason` is the first season **with this team** (a transfer who arrived for 2025-26 shows 2026), not the first college season.

**`/venues`** (n=989): id i; sourceId s (up to 5 digits; ESPN venue id **(unverified)**: no ESPN venue id is stored locally to compare); name s; city s? (12 null); state s? (68 null; up to 14 chars for non-US regions); country s? (30 null; **full country name**, e.g. `United States`, not ISO codes). **No capacity, coordinates, elevation, time zone or indoor flag.**

**`/draft/picks`** (n=20): athleteId i? (11 of 20 null: older picks have no CBBD athlete); draftTeamId i; draftTeam s; sourceTeamId i (a draft-side team id, different from the CBBD college team id); sourceTeamLocation s; sourceTeamName s; sourceTeamLeagueAffiliation null; sourceTeamCollegeId i (= CBBD team id 169); year i (2001–2025); overall i; round i; pick i; name s; overallRank i; positionRank i; **height i = inches** (73–83); **weight i = pounds** (178–270); position s.

### V.3 Checks run on the responses

| Check | Result |
|---|---|
| `/games.sourceId` vs `registry/games.csv` 2025-26 `game_id` | 35 of 35 match; no game missing on either side |
| Final scores vs registry | 35 of 35 equal |
| `startDate` vs registry `date_utc` | 35 of 35 equal to the minute, so `startDate` is **UTC** |
| CBBD game 372596 | `sourceId` / `gameSourceId` = **401856571** (UConn, 2026-03-28) |
| `/teams.sourceId` vs registry `opponent_id` (Big Ten opponents) | 21 of 21 match; MSU = 127 |
| Roster `sourceId` vs `registry/rosters.csv espn_id` | 11 of 15 present in the registry, all 11 match; the 4 others are absent from the registry, not conflicting |
| Box `athleteSourceId` ⊆ roster `sourceId` | yes (14 of 14) |
| Plays/subs/lineups athlete `id` ⊆ roster `id` (MSU) | 9 of 9 MSU players on the floor in game 372596 |
| Roster height × 2.54 vs registry `height_cm` | 11 of 11 equal (inches confirmed); weight × 0.45359237 vs `weight_kg`: 10 of 11 equal, 1 differs by 10 lb |
| 2027 roster height/weight vs school roster (private cards) | 15 of 15 equal on both |
| Clock string vs `secondsRemaining` | 470 of 470 equal |
| Spread sign vs moneyline (lines with both moneylines, n=44) | spread < 0 when the home moneyline is the shorter price on 42 of 43 non-tied lines; 1 tied (−105/−105); 1 inconsistent (one book's late spread +1.5 with home −145, opened −2.5). Over 69 lines, spread + final home margin averages −0.28. **Spread is the home team's line, negative = home favoured.** MSU favoured by moneyline and by its own signed spread: 33 lines agree |
| Substitution stint seconds per team | 12,000 s for each team = 5 × 2,400 s. 5 + 5 stints start at 20:00 of period 1; 10 stints run through half-time (not split at the period break); 152 `Substitution` plays = 2 × (86 stints − 10 game-start stints) |
| Lineup `totalSeconds` per team | 2,400 s for each team |
| `idHash` | = CBBD athlete ids sorted ascending (numeric) and joined with `-`; 28 of 28 |
| Lineup possessions vs `/games/teams` possessions (game 372596) | Lineup sums 59 and 58 vs box 64 and 63: the lineup event count runs about 8% low, as section 4 predicted from the code |
| `/games/teams` possessions formula | Integers; team ≠ opponent in 27 of 35 games. Not reproduced by FGA − ORB + TOV + k·FTA (difference −2.8 to +3.8 with k = 0.44; −3.5 to +2.75 with k = 0.475). `rating` = 100 × points / possessions (35 of 35); `pace` = mean(team, opponent possessions) × 40 / gameMinutes |
| A rough event-based count by our definition on game 372596 (scratch script, not a validated engine) | about 68 possessions per team, above both CBBD figures. Treat as a pointer only; settle with the real possession builder |
| `onFloor` | exactly 10 players on 470 of 470 plays in game 372596; on 5,295 of 5,368 (98.6%) season shooting plays; the rest have 0, 1, 2, 5, 8, 9 or 11 entries |
| `participants` order | [0] = the actor (shooter, rebounder, fouler, stealer, blocker, turnover, player entering); [1] = assister on assisted makes. Substitution plays carry 1 participant; the text names both players |
| Free throws | type `MadeFreeThrow` is used for **made and missed** free throws; the text carries `makes/misses free throw k of n`. Free-throw shot locations are null on 1,327 of 1,335 |
| Foul text | `PersonalFoul` text is only `Foul on <name>` (33 of 33); no shooting, offensive or loose-ball subtype in text. `Offensive Charge`, `Foul Turnover` and `Technical Foul` exist as types |
| Turnover subtype | `Lost Ball Turnover` is a catch-all; the subtype (e.g. bad pass, shot clock) is only in the text |
| Coach's challenge | Present as play types (`Coach's Challenge (Stands)` seen once in game 372596) |
| Shot coordinates: frame | see V.4 |
| KenPom `get_ratings` 2024–2026 | 362–365 teams per season; MSU W-L sums to 35 games in 2026, the same count as CBBD `/games` through its last game (Sweet 16) → **season-end snapshot** |

### V.4 Shot coordinates (CBBD `shotInfo.location`): units and frame

Evidence: 110 located shots in game 372596 and 3,801 in MSU's 2025-26 season file.

- **Units: tenths of a foot, full-court frame.** x runs along the court length, 0–940 (94 ft); y runs across, 0–500 (50 ft); y = 250 is the long axis. Observed x 18.8–921.2, y 10–495.
- **Quantised to a 1% grid:** every x is a multiple of 9.4 (3,801 of 3,801) and every y a multiple of 5 (3,801 of 3,801). Effective resolution 0.94 ft × 0.5 ft (0.287 m along the court, 0.152 m across). The source very likely charts shots as percentages of court length and width **(inference)**.
- **Rim centres at x = 52.5 and x = 887.5, y = 250** (5.25 ft = 1.60 m from each baseline, matching `config/court_ncaa_men.yaml`). Distance from that rim vs the "N-foot" figure in the play text: median difference −0.04 ft, 10th–90th percentile −0.55 to +0.41 ft (n = 2,102 shots). Three-pointers: shortest 21.62 ft, 1 of 1,585 below the 21.65 ft corner distance (by 0.03 ft, within the grid step); median 24.4 ft. `rim` shots: median 3.3 ft, max 11.0 ft.
- **Basket attacked:** constant within each team-period (136 of 136 team-periods use one end only); teams switch ends at half-time; which end a team attacks first **varies by game**, so derive it from the shots, never from home/away.
- **Coverage:** 94.0% of field-goal attempts carry a location (240 of 4,033 null); free throws almost never do.
- **Still open:** which sideline is y = 0 (needed for the sign of `x_m`, attacker's right vs left). Settle with one game against video or one known corner three.

Transform to the `geometry.py` frame (metres, origin under the attacked rim, `y_m` toward half-court, `x_m` positive to the attacker's right), with `s = ±1` for the unresolved sideline:
- attacking the x = 52.5 rim: `y_m = (x − 52.5) × 0.03048`, `x_m = s × (y − 250) × 0.03048`
- attacking the x = 887.5 rim: `y_m = (887.5 − x) × 0.03048`, `x_m = −s × (y − 250) × 0.03048`

`r_m` and `mirror_theta` do not depend on `s`; left/right labels (`theta_deg` above 90) do. This differs from the ESPN raw convention described in section 1.3 (half-court feet); CBBD is not a pass-through of those raw values.

### V.5 Possession and chance definitions implied by the responses

| CBBD output | What the data shows | Use |
|---|---|---|
| `/games/teams` `possessions` | Integer per team-game; team and opponent usually differ by 1–3; within about ±4 of the FGA − ORB + TOV + 0.44·FTA estimate but not equal to it, so it is probably a PBP-derived count **(inference)**. An offensive rebound does not obviously add a possession (it sits near the box estimate, which subtracts ORB) | Store as `possessions_source`; never as our count |
| `/lineups/*` `possessions` | Event count (section 4); 8% below the game value in game 372596 | Do not use as a denominator |
| Chances | No CBBD field | Derived by us from offensive rebounds and resets |

### V.6 Corrections (documentation said → reality)

| # | Where | Doc said | Reality (2026-10-18 responses) |
|---|---|---|---|
| 1 | §1.1 quirk 3, §5 call 1 | Conference string "B1G" or "Big Ten" (unverified) | **`Big Ten`**; `B1G` returns an empty list with HTTP 200. Conference values are full names (`Big East`, `Mountain West`, …) |
| 2 | §1.1 quirk 1 | `sourceId` probably ESPN | **Confirmed** for games (35/35), teams (21/21 plus MSU 127), roster players (11/11) and box `athleteSourceId`. Play `sourceId` has the ESPN play-id form. Venue `sourceId` still unverified |
| 3 | §1.1 quirk 1; dictionary `C: athleteId -> players.sourceId` | Plays/substitutions/lineups carry ESPN ids | They carry **only CBBD athlete ids**. Map through `/teams/roster` (`id` → `sourceId`) per team-season, which needs one roster call per opponent team-season |
| 4 | §1.1 Time resolution, §3 | `clock` format unverified; tenths below 1:00? | `M:SS` / `MM:SS`, **whole seconds everywhere**, also under one minute; `secondsRemaining` integer and identical |
| 5 | §1.1 quirk 7, §2.9 | Location units, origin, orientation undocumented | **Tenths of a foot, full-court 940 × 500 frame, 1% grid, rims at x = 52.5 / 887.5, y = 250** (V.4); sideline orientation still open |
| 6 | §1.1 quirk 9, §2.13 | Spread sign unverified | **Home line; negative = home favoured** (42 of 43 non-tied lines agree with the moneyline) |
| 7 | §1.1 coverage | Substitutions 2024+ | Confirmed for 2025-26: one row **per stint**, stints run through half-time, 1 s resolution, both teams, stint seconds sum to 5 × 2,400 per team |
| 8 | §2.8 | `/lineups/game` gives lineup rows | Per-game aggregates per unique five-man unit (28 units in a game), **no start/end times**; stint times exist only through `/substitutions` |
| 9 | §2.4, §2.5 | Roster height/weight units unverified (probably in/lb) | **Inches and pounds, integers**; values equal the ESPN registry and the school roster |
| 10 | §2.4 | `date_of_birth` from roster `dateOfBirth` | **Null on all 30 roster rows** (2026, 2027); CBBD is not a usable birth-date source for this team |
| 11 | §2.4 | `class_year` derivable from `startSeason`/`endSeason` | `startSeason` = first season **with the current team**; transfers reset it, so class year cannot be derived from it |
| 12 | §2.4, §2.15 | `hometown.country` | Null on all 30 roster and all 4 recruit rows; lat/lon are filled (city centroid). `countyFips` present (not stored, per section 2.4) |
| 13 | §2.15 | Recruit `athleteId` links to roster `id` | **Null on all 4 recruits**; join by name, team and year. Recruit `ranking` is not the 247 Composite rank; upstream unnamed. Recruit height/weight are recruiting-time values and differ from the roster (e.g. up to 2 in and 22 lb) |
| 14 | §2.15 | Portal: `yearsRemaining`, `eligibility` | `yearsRemaining` null; `eligibility` filled (`Immediate`); `year` = portal cycle |
| 15 | §2.3, §6 gap 6 | `/venues`: no capacity, coordinates, elevation | **Confirmed** (fields: id, sourceId, name, city, state, country). `country` is a full name, not ISO; 68 of 989 have no state |
| 16 | §1.1 quirk 10, §2.14 | `/ratings/adjusted` season-level | **Confirmed**: one row, no date field. Its `rankings` block returned 1/1/1 for a team-filtered call although that team was not first in all three in other season-end ratings, so the ranks appear to be computed **within the filtered result set (inference)**. Pull unfiltered (all teams) before storing any CBBD rank |
| 17 | §1.1 endpoint table, `/rankings` | `pollType` {ap, coaches}; teamId n | Response values are `AP Top 25` and `Coaches Poll`; `teamId` integer. `pollDate` filled on all 41 rows (point-in-time usable) |
| 18 | §1.1 endpoint table, `/games/players` | `minutes` n | **Whole minutes (integer)**, rounded so the team sums to 200 or 225 per game; `minutes_s = minutes × 60` has ±30 s error per player |
| 19 | §2.1 / dictionary `excitement_cbbd` | Range 0–10 (unverified) | Observed 1.1–11.1; null on 9 of 35 games. Treat as open-ended ≥ 0 |
| 20 | §1.1 endpoint table, `/games` | `tournament` holds the event name | Only `NCAA` seen. The Big Ten tournament has `tournament` null, `seasonType` = regular, `gameType` = `TRNMNT`, and the round only in `gameNotes`. MTEs also use `TRNMNT`. The `game_type` rule in §2.1 should key on `gameNotes` + `gameType`, not on `tournament` alone |
| 21 | §2.6, §2.10 | Missed FTs "appear to share" the `MadeFreeThrow` type (inference) | **Confirmed**: made and missed FTs share it; `shotInfo.made` or the text tells them apart; `k of n` is in the text |
| 22 | §2.11, §3 | Foul type names (PersonalFoul / Technical Foul / Flagrant Foul) unverified | `PersonalFoul`, `Technical Foul`, `Offensive Charge`, `Foul Turnover` exist; **no `Flagrant Foul` type**. Shooting vs non-shooting must be inferred from the following free throws |
| 23 | §2.12, §3 | Timeout vocabulary unverified | `OfficialTVTimeOut` (team null; = media timeout), `ShortTimeOut`, `RegularTimeOut`; no `FullTimeOut` |
| 24 | §3, §6 gap 3 | Coach's challenge: none known in CBBD | `Coach's Challenge (Stands)` and `(Overturned)` are play types |
| 25 | §2.6 | `event_id` order | Use CBBD `id` for order (chronological); ESPN `sourceId` order is not chronological inside a second; `wallclock` is not monotonic |
| 26 | §3 | `homeWinProbability` per play | Null for whole games in 9 of 35 (all 3 NCAA tournament games among them) |
| 27 | §1.1 endpoint table, `/lineups` | fourFactors as in `/games/teams` | `turnoverRatio` is on a 0–1 scale in `/lineups` but 0–100 in `/games/teams`; all other percentages are 0–100 |
| 28 | §1.1 quota | Free tier 1,000 calls/month (unverified) | `x-calllimit-remaining` header present; 999 → 979 after 21 calls, so the free tier is 1,000 per month on this key |
| 29 | §1.5 KenPom tool | Not used; fields from documentation only | Used once on 2026-10-18 with Aldemir's approval (V.7). Class stays reference only until he decides; R-DS-14 still lists the web/tool route as blocked, so that line needs his explicit update |

### V.7 KenPom via the Parse.bot tool (reference only)

- Endpoints the tool exposes: `get_ratings` (season), `get_ratings_by_conference` (only BE, ACC, B10, B12, SEC), `search_teams`, `search_coaches`. Seasons 2024–2026 only.
- `get_ratings` response: `{status s, data {year s, ratings[] {rank, team, conference, w_l, adj_em, adj_oe, adj_oe_rank, adj_de, adj_de_rank, adj_t, adj_t_rank, luck, luck_rank, sos_adj_em, sos_adj_em_rank, sos_adj_oe, sos_adj_oe_rank, sos_adj_de, sos_adj_de_rank, ncsos_adj_em, ncsos_adj_em_rank}}}`. **Every value is a string**, including signed numbers (`+…`, luck as `+.0xx`); parse to float/int on load. 362, 364 and 365 teams for 2024, 2025, 2026. Team names are KenPom spellings (e.g. `Michigan St.`); conference codes are KenPom's (`B10`, `B12`, `A10`, `AE`, …), unlike CBBD's full names. No possession-length, four-factor or height fields in this tool.
- `search_coaches`: `{status, data {query, results[] s}}`, names only.
- **As-of: there is no date field.** The 2026 file's W-L counts every game through the end of MSU's season, so it is a **season-end snapshot** (inference from the record; the tool gives no timestamp).
- **Consequence:** these values **cannot be pre-game inputs** for any game of the same season without leakage (R-DS-04, R-CX-09). In `ratings_snapshots` they go in with `snapshot_kind = end_of_season`, `is_point_in_time = false`, `as_of_date` = the pull date (flagged), `licence_class` = reference only. They are usable only as (a) a prior for the **following** season (2026 values before the 2026-27 opener) and (b) a cross-check of our own season-end numbers. Point-in-time KenPom needs the official API `archive` endpoint (section 1.5).

### V.8 Unverified points now resolved, and what stays open

Resolved by the responses: conference string; `sourceId` = ESPN for games, teams, players (and play-id form); `startDate` time zone (UTC); clock format and resolution; `period` numbering (1, 2, 3 = OT); `onFloor` filled; `participants` order; FT wording; missed-FT type; shot-location units, origin, grid and basket-side rule; `wallclock` filled; spread sign; `spreadOpen` coverage; `/lines.gameId` = `/games.id`; providers list; substitution grain and resolution; lineup grain, `idHash`, totalSeconds and the low lineup possession count; box `minutes` unit; roster and draft height/weight units; `dateOfBirth` coverage (none); `startSeason` meaning; recruit fields and the missing `athleteId`; portal fields; venue field set; adjusted ratings season-level; rankings point-in-time; quota header; KenPom tool fields and season-end status.

Still open:
1. Which sideline is y = 0 in CBBD shot coordinates (left/right labels). One game against video settles it.
2. The exact `/games/teams` possession formula (not reproduced; within ±4 of the box estimate).
3. Venue `sourceId` = ESPN venue id (no ESPN venue id stored locally; check against a hoopR schedule file).
4. Whether `/ratings/adjusted` ranks are within-filter ranks (one unfiltered call would settle it).
5. Upstream of recruit `ranking`/`rating` and of the recruit `sourceId` (not 247 Composite rank; service not named).
6. Whether ESPN BET's inconsistent line (spread vs moneyline) is a stale-moneyline artefact; the `/lines` rows still carry no timestamps.
7. Play-by-play upstream (ESPN) is still an inference, now with stronger support (ESPN-form play ids and type ids).
8. `homeWinProbability` gaps: why 9 games have none (tournament and some regular-season games).
9. Coverage beyond 2025-26 MSU games (other teams, earlier seasons) is unmeasured; the figures above are one team-season.
10. KenPom licence class: Aldemir's decision (R-DS-14 vs the 2026-10-18 chat approval).
