# Player data dictionary (W1, prompt 003)

Written 2026-10-18 by the W1 agent for prompt 003 (`coord/prompts/003-data-dictionary-and-first-games.md`). Status: **proposal**; the requirements session approves it.

Scope: every player attribute MSU Alpha 3 could use, defined once, with where it can actually be found for NCAA Division I men's players. The card itself is one row per player per snapshot date (R-PC-14, R-FD-04). The column order of the empty template is `docs/data/templates/player_card_template.csv` (303 columns). Per-game, per-stint and per-frame player values belong to the game tables in W2 (`docs/data/dictionary_games.md`); this file defines them only where a card summarises them.

The filled sample cards for MSU's 2026-27 roster are private (`~/MSU-Alpha-3-private/data/licensed/players/msu_2026-27_cards.csv`, synced to MyDrive/MSU-Alpha-3/data/licensed/players/). No player values are in this repo file except where a single public value illustrates a measurement bias (section 20).

---

## 0. Conventions

### 0.1 Units and types
- Lengths in **cm** (2 decimals) for body measurements; distances between places in **km**; court positions in **m**; times in **s**; speeds in **m/s**; accelerations in **m/s²**; angles in **degrees**; mass in **kg** (2 decimals). Never feet, inches or pounds in a stored value. The original string is kept in the `*_raw` column (e.g. `height_listed_raw` = `6-7`).
- Conversions: 1 in = 2.54 cm exactly; 1 lb = 0.45359237 kg exactly. A `6-7.5` string means 6 ft 7.5 in.
- Types: `str`, `int`, `float`, `date` (ISO `YYYY-MM-DD`), `datetime` (UTC ISO), `bool` (stored `1`/`0`), `enum`, `list` (`; `-separated in the CSV, JSON in Parquet).
- Empty cell = unknown. **Never** fill a guess. Imputed values (if ever allowed) go into separate `*_imputed` columns, never into the measured column.

### 0.2 Licence classes (from `docs/research/data_sources_catalog.md`)
| Code | Meaning | Sources in this class |
| --- | --- | --- |
| **MI** | Model input allowed | CBBD (terms allow caching, model training, derived outputs; no raw redistribution); KenPom **official API** if subscribed (personal/non-commercial incl. model building); OpenStreetMap/Nominatim geocodes (ODbL, attribution); our own computed values (OWN) |
| **MI-p** | Model input allowed, **provisional** (no terms found or terms ambiguous; Aldemir confirms) | Torvik/T-Rank (no terms page; "compiled from publicly available data"); NBA.com combine data used privately (NBA ToU: "private, non-commercial purposes"); EvanMiya exports (ToS: fair use with citation, no redistribution) |
| **RO** | Reference only: may be shown, used for cross-checks (R-DQ-01) and to validate; **never** a model feature | ESPN (data already pulled; Disney ToU bans robots), hoopR files of ESPN origin, Sports-Reference (explicit ban on AI/ML use), 247Sports (CBS ToU bans scraping and data mining), On3/Rivals (terms unverified, 403), Massey, KenPom **web** pages, school athletics sites (terms not reviewed), news articles, the Kaggle archive until each file's licence is checked |
| **OWN** | Computed by us from our video and from MI play-by-play | Tracking, laterality, CV appearance, our role clusters. Inherits the private-research restriction on broadcast video (R-RG-01) |

A field's licence class is the class of the source that actually filled it on that row (`*_licence` companion or block licence column). The same field can be MI on one row (CBBD) and RO on another (school site).

### 0.3 Source codes and priority
`CBBD` CollegeBasketballData API · `SCH` school roster and bio pages · `TVK` Torvik · `KPA` KenPom API · `KPW` KenPom web · `EM` EvanMiya · `ESPN` ESPN data already pulled (no new requests) · `hR` hoopR prebuilt release files · `NBA` NBA Draft Combine (nba.com/stats) · `247`, `ON3`, `RIV` (Rivals, now inside On3), `ESPNR` (ESPN recruiting rankings, read second-hand only) · `SR` Sports-Reference · `USAB` USA Basketball / FIBA · `CONF` conference availability reports · `NEWS` press · `OSM` OpenStreetMap Nominatim · `KAG` Kaggle March Madness archive · `OWN` our pipeline.

Priority rule: the first listed source that has the value fills the field; the second fills `*_check` (R-DQ-01). Where an MI source exists it outranks an RO source for any value that may enter a model.

### 0.4 As-of rules (R-PC-14, R-CX-09, R-CX-18)
| Code | Rule |
| --- | --- |
| **STATIC** | Fixed fact (birth date, birthplace). Usable for any game once recorded. |
| **SNAP** | Value as published on the pull date. A game may use it only if `*_as_of` ≤ tip − 24 h (the R-CX-18 24 h card) or ≤ tip − 1 h for the 1 h card. Re-pulled at least weekly in season; old snapshots kept. |
| **EVENT** | Valid from the event date (combine date, commit date, transfer date) onward. |
| **PRIOR** | Final value of a completed season; usable from the first game of the next season. |
| **CUM** | Cumulative to date: computed only from games with tip < target tip (R-FD-07). |
| **POST** | Known only after the game; never a pre-game input. |

### 0.5 Companion columns
External values carry provenance either per field or per block (R-FD-04, R-PC-14, R-DQ-04):
- `*_source`: source code plus URL or endpoint, and the pull date.
- `*_as_of`: the date the value was true or published (see 0.4).
- `*_licence`: MI, MI-p, RO or OWN (0.2).
- `*_check`: the second source's value when it disagrees, or `match: <source>`.
- `*_raw`: the original string before unit conversion.

Per-field companions in the template (type `str` or `date`; same meaning as above): `espn_athlete_id_source`, `cbbd_athlete_id_source`, `broadcast_name_source`, `jersey_number_source`, `jersey_history_source`, `listed_position_source`, `class_year_source`, `eligibility_source`, `birth_date_source`, `birth_date_check`, `captain_source`, `roster_status_source`, `hometown_source`, `hometown_geocode_source`, `birthplace_source`, `high_school_source`, `aau_source`, `previous_colleges_source`, `height_listed_source`, `height_listed_as_of`, `weight_listed_source`, `weight_listed_as_of`, `wingspan_source`, `wingspan_as_of`, `wingspan_licence`, `standing_reach_source`, `hand_source`, `shoe_size_source`, `body_fat_source`, `recruit_stars_source`, `offers_source`, `nil_valuation_source`, `nil_valuation_as_of`, `nil_source`. Fields without their own companion inherit the block companions below.

Block-level companions (one set covers every field in the block): `stats_source`, `stats_licence`, `stats_as_of` (season counting stats); `rate_stats_source`, `rate_stats_licence` (rates, zones); `impact_source`, `impact_licence`, `impact_as_of`; `recruiting_source`, `recruiting_as_of`, `recruiting_licence`; `measured_source`, `measured_event`, `measured_date`, `measured_licence` (combine/camp anthropometrics); `athletic_test_source`, `athletic_test_date`; `laterality_source`, `laterality_as_of`; `transfer_source`, `transfer_as_of`; `role_source`; `intl_source`; `cv_appearance_source`, `cv_appearance_as_of`; `trk_as_of`.

### 0.6 Coverage estimates: how they were made
- **[T]** Torvik 2025-26 player CSV (`getadvstats.php?year=2026&csv=1`, pulled 2026-10-18, 4,977 player-seasons, kept in the scratchpad only): share of rows with a non-empty value. Results: height 100%, jersey number 100%, role 100%, hometown 99.9%, birth date 99.7%, recruiting rating 22.2% of all rows and 27.1% of rows with ≥ 40% of minutes (n = 2,284), non-US hometown 17.9%.
- **[M]** The MSU 2026-27 sample (n = 15) filled for this task.
- **[S]** Structural count: events per year divided by about 5,000 D-I players per season ([T] row count).
- **[J]** Judgement, low confidence; to be replaced by a measured share once CBBD and other pulls exist.

### 0.7 Requirement IDs
IDs are cited exactly as in the live doc export of 18 Oct (`requirement_ids.md`). Fields that serve no existing ID carry a proposed `new-PC-n` with the reason.

---

## 1. Meta (8 fields)

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `card_id` | Unique key of this card row: `<team>-<season>-<slug>-<card_as_of>` | str | | OWN | 100% | OWN | — | R-PC-14 |
| `team_espn_id` | Team ID; ESPN ID is the join key (MSU = 127) | int | | registry | 100% | OWN | STATIC | R-FD-02 |
| `team_name` | Team display name | str | | registry | 100% | OWN | STATIC | R-FD-03 |
| `season` | Season label `YYYY-YY` (2026-27). CBBD/Torvik/KenPom label it by the end year (2027) | str | Off-by-one season labels between sources | OWN | 100% | OWN | STATIC | R-FD-03 |
| `card_as_of` | Snapshot date the card is valid for; a game uses the latest card with `card_as_of` ≤ tip − 24 h | date | | OWN | 100% | OWN | SNAP | R-PC-14, R-CX-18 |
| `card_built_utc` | When the row was built | datetime | | OWN | 100% | OWN | — | R-FD-10, R-DQ-04 |
| `card_version` | Card schema version | str | | OWN | 100% | OWN | — | R-FD-10 |
| `card_built_by` | Session or script that built the row | str | | OWN | 100% | OWN | — | R-FD-10 |

## 2. Identity (39 fields)

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `player_uid` | Our stable player key across seasons and schools | str | Must survive transfers and name changes | OWN (crosswalk) | 100% once built | OWN | STATIC | R-PC-01, R-FD-03 |
| `espn_athlete_id` | ESPN athlete ID | int | Some athletes get a second ID after a transfer (unverified) | ESPN files already pulled → registry/rosters.csv → hR rosters | ~100% of players who appear in an ESPN box [J]; [M] 10/15 (the 5 newcomers are not yet in the registry pull) | RO (as a value); usable as a join key | STATIC | R-PC-01, R-FD-02 |
| `cbbd_athlete_id` | CBBD `athleteId` (roster `id`, `sourceId`) | int | `sourceId` appears to be ESPN's ID (unverified) | CBBD `/teams/roster` | ~100% [J] | MI | STATIC | R-PC-01 |
| `torvik_name`, `torvik_team` | Name and team string exactly as Torvik writes them (e.g. `Cameron Ward`, `Michigan St.`) | str | Name variants (nicknames, Jr.) break joins | TVK | 100% of players with minutes [T] | MI-p | SNAP | R-PC-01 |
| `kenpom_name` | Name as on KenPom player pages | str | | KPA (not KPW scraping) | ~100% of players with minutes [J] | MI (API) | SNAP | R-PC-01 |
| `evanmiya_name` | Name as in EvanMiya exports (`name` column of EvanMiya_Players.csv) | str | | EM | ~100% of players with possessions [J] | MI-p | SNAP | R-PC-01 |
| `school_roster_player_id`, `school_roster_url` | Sidearm roster-player ID and bio URL | int, str | IDs change every season (MSU's 2026-27 IDs are 178xx) | SCH | ~100% (nearly all D-I sites run Sidearm or similar) [J] | RO | SNAP | R-PC-01, R-DQ-01 |
| `first_name`, `last_name`, `name_suffix`, `display_name` | Name parts; suffix such as `Jr.` split out | str | | SCH → CBBD → ESPN | 100% | RO/MI by source | SNAP | R-PC-01 |
| `broadcast_name` | Name as the broadcast says and shows it (graphics and audio), with pronunciation if given | str | Differs from the roster (e.g. "Cam" vs "Cameron") | OWN (from video) → school pronunciation guide | [J] < 30% of school sites give pronunciation | OWN | SNAP | R-PC-01 |
| `jersey_number`, `jersey_number_as_of` | Number worn in the season of the card | str (keeps `0` vs `00`) | Numbers change between seasons and sometimes mid-season | SCH → CBBD → ESPN | 100% [T] | RO/MI | SNAP | R-PC-01, R-FD-03, R-ID-04 |
| `jersey_history` | Ordered list `season team #number (from date to date)` | list | Mid-season changes are rare and rarely documented | registry → CBBD (`jersey`, `startSeason`, `endSeason`) → TVK (`num`) → SCH | 100% for D-I seasons [T] | MI/RO | EVENT | R-FD-03, R-PC-01, R-ID-04, R-ID-08 |
| `listed_position`, `listed_position_long` | School's position label (G, F, C, G/F...) | enum | Coarse and coach-chosen; not what the player does (see `role_*`) | SCH → CBBD → ESPN | 100% | RO/MI | SNAP | R-PC-01 |
| `class_year_listed` | Academic class as listed (`Fr.`, `So.`, `Jr.`, `Sr.`, `Gr.`, with `R-` for redshirt) | enum | Academic class ≠ eligibility year after COVID year, redshirts, JUCO years | SCH → TVK (`yr`) | 100% [T] | RO/MI-p | SNAP | R-PC-01 |
| `redshirt_flag` | 1 if the listed class has an `R-` prefix | bool | Only the school's label; medical redshirts may not show | SCH | 100% | RO | SNAP | R-PC-01 |
| `eligibility_seasons_used`, `eligibility_seasons_remaining` | Seasons of NCAA competition used and remaining after this season | int, 0–5 | Waivers and rule changes make this uncertain; schools rarely publish it | CBBD `/recruiting/portal` (`eligibility`, `yearsRemaining`, transfers only) → NEWS | [J] < 20% explicit | MI/RO | EVENT | R-PC-01 |
| `birth_date` | Date of birth | date | Some sources disagree (see section 20); two sources required before use | SCH bio → CBBD `dateOfBirth` → TVK (last column) | 99.7% [T]; [M] 14/15 | RO (SCH), MI (CBBD), MI-p (TVK) | STATIC | R-PC-01 |
| `age_at_card_as_of_years` | Age in years at `card_as_of` (days / 365.2425); per game, age at tip is computed in the game table | float, 16–30 | | OWN from `birth_date` | as `birth_date` | OWN | STATIC | R-PC-01 |
| `captain_flag` | Team captain this season | bool | Schools announce captains late or not at all | SCH (Sidearm `isCaptain`, bio text) | [J] ~50% of teams publish | RO | SNAP | new-PC-1 (leadership context; no ID covers it) |
| `roster_status` | Scholarship, walk-on, preferred walk-on, manager-turned-player, or unknown | enum | Rarely stated; "walk-on" in a bio can be historic | SCH bio → NEWS | [J] < 30% | RO | SNAP | new-PC-2 (minutes priors differ for walk-ons) |

## 3. Origin (24 fields)

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `hometown_raw` | Hometown string as published (e.g. `Springfield, N.J.`) | str | "Hometown" is self-reported and may be a suburb, the high-school city or a birthplace; sources disagree (section 20) | SCH → CBBD `hometown.city/state/country` → TVK | 99.9% [T] | RO/MI | SNAP | R-PC-02 |
| `hometown_city`, `hometown_region`, `hometown_country_iso2` | Parsed city, state/province/region, ISO 3166-1 alpha-2 country | str | | parsed from raw; CBBD gives fields | 99.9% [T]; non-US 17.9% [T] | as raw | SNAP | R-PC-02, R-PC-16 |
| `hometown_lat`, `hometown_lon` | City-centroid coordinates, WGS84 | float, degrees | Centroid ≠ home; ambiguous names (two Springfield Townships in NJ) | CBBD `hometown.latitude/longitude` → OSM geocode | ~100% when hometown known | MI | SNAP | R-PC-02, R-PC-03 |
| `hometown_geocode_confidence` | high / medium / low with the reason | enum + text | | OWN | — | OWN | SNAP | R-PC-02, R-DQ-09 |
| `hometown_check` | Second source's hometown when different | str | | TVK, CBBD | — | — | SNAP | R-DQ-01 |
| `birthplace_raw` | Place of birth as published in the bio | str | Not the same as hometown; used only for identity checks, never as a proxy for anything else | SCH bio | [M] 13/15 | RO | STATIC | R-PC-02 |
| `high_school_final` | High school or academy listed on the roster (usually the last one) | str | Rosters list one school; many players moved | SCH → CBBD recruit `school` | ~100% for US players [J] | RO/MI | STATIC | R-PC-02 |
| `high_schools_all` | Every high school in order with years | list | Bios are the only full source | SCH bio → 247 profile (school list) | [J] ~70% via bios | RO | STATIC | R-PC-02 |
| `prep_school` | Prep or national academy (e.g. Link Academy, La Lumiere) | str | "Prep" vs "high school" is not used consistently | SCH bio | [M] 6/15 | RO | STATIC | R-PC-02 |
| `aau_program`, `aau_circuit` | Grassroots club and shoe-company circuit (Nike EYBL, adidas 3SSB, Under Armour UAA) | str, enum | Players switch programs; bios name the last or best-known | SCH bio → 247/ON3 profiles → NEWS | [M] 7/15 program, 5/15 circuit | RO | STATIC | R-PC-02 |
| `previous_colleges` | Earlier colleges in order with seasons (incl. JUCO, D-II, NAIA) | list | Roster field `previousSchool` may list only the last one | SCH bio → CBBD `/recruiting/portal` → TVK transfer lists | 100% when a player transferred; ~35–45% of D-I rotation players are transfers [J] | RO/MI | EVENT | R-PC-02, R-FD-12 |
| `juco_flag` | Played at a junior college | bool | | SCH bio | as above | RO | STATIC | R-PC-02, R-PC-09 |
| `dist_hometown_to_campus_km` | Great-circle distance from hometown centroid to the team's arena | float, km, 0–20,000 | Centroid error a few km; meaningless for players who moved | OWN from lat/lon (haversine, R = 6371.0088 km) | as lat/lon | OWN | SNAP | R-PC-03 |
| `dist_hometown_to_campus_method` | Method text | str | | OWN | | OWN | | R-PC-03, R-DQ-04 |
| (game table) `dist_hometown_to_venue_km` | Hometown to each game venue; lives in the player-game table (W2) | float, km | | OWN | | OWN | STATIC per venue | R-PC-03 |

## 4. Body (43 fields)

All body values are stored in cm/kg with the raw string kept. **Listed** and **measured** values are separate fields and are never merged (R-DQ-09).

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `height_listed_raw`, `height_listed_cm` | Roster height | float, cm, 160–235 | **Runs high**: rosters round up and often list in shoes; the one MSU player measured at the 2026 combine is listed 5.08 cm taller than his barefoot height (section 20). Sources differ by 1 in for 4 of 9 MSU returners (section 20) | SCH → CBBD `height` (in) → TVK `ht` → ESPN | 100% [T] | RO/MI/MI-p | SNAP | R-PC-04, R-DQ-09 |
| `height_listed_check` | Second source's height or `match` | str | | TVK, CBBD | | | SNAP | R-DQ-01 |
| `weight_listed_raw`, `weight_listed_kg` | Roster weight | float, kg, 60–160 | Rarely updated during a season; rounded to 5 lb on many sites | SCH → CBBD `weight` (lb) → ESPN | ~95% [J] (Torvik has no weight; ESPN registry has it for every MSU row) | RO/MI | SNAP | R-PC-04 |
| `height_wo_shoes_raw`, `height_wo_shoes_cm` | Measured standing height barefoot | float, cm | Gold standard; only at the NBA combine, G League Elite camp and some USA Basketball events | NBA `HEIGHT_WO_SHOES` → 247 "Verified Results" (copy of NBA) → NEWS | ~1–1.5% of D-I players per season [S]: about 73 combine invitees in 2026, not all from D-I; [M] 1/15 | MI-p (NBA) / RO (copies) | EVENT | R-PC-04 |
| `height_w_shoes_cm` | Measured height in shoes | float, cm | NBA stopped publishing in-shoe heights in recent years (unverified); USA Basketball/Hoop Summit lists heights in shoes | NBA `HEIGHT_W_SHOES` (older years) → Hoop Summit lists | < 1% [S] | MI-p/RO | EVENT | R-PC-04 |
| `weight_measured_kg` | Weight on the combine scale | float, kg | | NBA `WEIGHT` | as barefoot height | MI-p | EVENT | R-PC-04 |
| `wingspan_raw`, `wingspan_cm` | Fingertip-to-fingertip arm span | float, cm, 150–250 | "Reported" wingspans in bios and scouting text are not measurements and disagree (MSU: 2 of 5 bio wingspans conflict with 247 scouting text by 7.6 cm and 2.5 cm) | NBA `WINGSPAN` → camp lists (Hoop Summit, adidas Eurocamp via DraftExpress) → SCH bio text → 247 scouting text | measured ~1–2% [S]; reported in bios [M] 5/15, nationally [J] 10–20% | MI-p (NBA) / RO | EVENT | R-PC-04 |
| `wingspan_kind` | `measured` (named event, date) or `reported` (bio or scouting text) | enum | Only `measured` may enter a model | OWN | | OWN | | R-PC-04, R-DQ-09 |
| `wingspan_minus_height_cm` | Wingspan − height | float, cm, −10 to +30 | Must use measured barefoot height with measured wingspan; with listed height it is biased low | OWN | as wingspan | OWN | EVENT | R-PC-04 |
| `wingspan_minus_height_basis` | Which heights/wingspans were used | str | | OWN | | OWN | | R-PC-04, R-DQ-04 |
| `standing_reach_raw`, `standing_reach_cm` | Standing reach, one arm up, flat-footed | float, cm, 200–300 | Measurement protocol differs between events | NBA `STANDING_REACH` → Hoop Summit / Eurocamp lists | ~1–2% [S]; [M] 1/15 | MI-p/RO | EVENT | R-PC-04 |
| `hand_length_cm`, `hand_width_cm` | Wrist crease to tip of middle finger; thumb tip to little-finger tip spread | float, cm, 15–30 | Only the NBA combine publishes these | NBA `HAND_LENGTH`, `HAND_WIDTH` | ~1% [S]; [M] 1/15 | MI-p | EVENT | R-PC-04 |
| `shoe_size_us` | US men's shoe size | float | Never published for college players | none | ≈ 0% | — | EVENT | new-PC-3 (CV foot-size scale check; low value) |
| `body_fat_pct` | Body-fat percentage | float, % | Combine only; method (skinfold) varies. Treated as health-adjacent: store only if published by the NBA | NBA `BODY_FAT_PCT` | ~1% [S] | MI-p | EVENT | R-PC-04 (extension) |
| `standing_vertical_cm`, `max_vertical_cm` | No-step and max (running) vertical jump | float, cm, 40–120 | Combine and camp protocols differ; self-reported numbers are worthless | NBA `STANDING_VERTICAL_LEAP`, `MAX_VERTICAL_LEAP` | ~1% [S]; [M] 1/15 | MI-p | EVENT | R-PC-05 (prior for R-CG-11 jump height) |
| `lane_agility_s` | Pro lane agility drill time | float, s, 9–13 | | NBA `LANE_AGILITY_TIME` | ~1% [S] | MI-p | EVENT | R-PC-05 |
| `shuttle_run_s` | Lane shuttle time | float, s, 2.5–3.8 | | NBA (`MODIFIED_LANE_AGILITY_TIME` in the API is a different drill; 247 shows "Shuttle run") | ~1% [S] | MI-p | EVENT | R-PC-05 |
| `three_quarter_sprint_s` | 3/4-court sprint (about 22.9 m) | float, s, 2.9–3.8 | Hand vs electronic timing | NBA `THREE_QUARTER_SPRINT` | ~1% [S] | MI-p | EVENT | R-PC-05 (prior for R-PL top speed) |
| `bench_press_reps` | Reps at 185 lb | int | Dropped from recent combines (unverified) | NBA `BENCH_PRESS` | < 1% | MI-p | EVENT | R-PC-05 |

## 5. Laterality (10 fields, all computed by us)

No public source publishes handedness for college players. All values come from our video (OWN) and are reported with their n.

| Field | Definition | Type, unit, range | Bias / caveat | Sources | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `shooting_hand`, `shooting_hand_n` | Hand that releases jump shots and free throws (`L`/`R`), from release pose; n = shots seen | enum, int | Needs ≥ 10 clear releases; one-hand floaters excluded | OWN (pose at release) | MSU and filmed opponents only | OWN | CUM | R-PC-11 (proposal: also new-PC-4 for shooting hand as an ID tie-breaker, R-ID-13) |
| `dominant_dribble_hand`, `dribble_hand_left_share` | Share of live-dribble frames with the ball in the left hand | enum, float 0–1 | Defender side changes hand use; report by court side | OWN | as above | OWN | CUM | R-PC-11 |
| `finishing_hand_left_share`, `finishing_n` | Share of rim attempts released with the left hand | float 0–1, int | | OWN | as above | OWN | CUM | R-PC-11 |
| `drive_left_share`, `drive_n` | Share of drives going to the driver's left | float 0–1, int | Drive definition from the taxonomy (docs/taxonomy) | OWN | as above | OWN | CUM | R-PC-11 |
| `laterality_source`, `laterality_as_of` | Model version and last game included | str, date | | OWN | | OWN | CUM | R-DQ-04 |

## 6. Recruiting (26 fields)

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `hs_class_year` | High-school graduating class | int | Reclassification moves it a year | CBBD `/recruiting/players` (`year`) → 247 → SCH bio | ~100% of recruited players [J] | MI/RO | STATIC | R-PC-13 |
| `recruit_stars` | Star rating (2–5) | int | Services disagree; bios say "consensus four-star" | CBBD `stars` → 247 Composite → SCH bio | ~22% of D-I players have a recruiting rating [T] | MI/RO | EVENT (final class ranking) | R-PC-13, R-FD-12 |
| `recruit_rank_nat_247c`, `recruit_rank_pos_247c`, `recruit_rank_state_247c`, `recruit_rating_247c` | 247Sports Composite national, position and state rank, and composite rating (0.0000–1.0000) | int, int, int, float | Ranks move until the class closes; keep the final one plus the date | 247 (manual read only) → CBBD (`ranking`, `rating`) | ~400 ranked per class (408 in 2026, catalog) | RO (247) / MI (CBBD) | EVENT | R-PC-13 |
| `recruit_rank_nat_247`, `recruit_rank_nat_on3`, `recruit_rank_nat_rivals`, `recruit_rank_nat_espn` | Each service's own national rank | int | Each service ranks a different number of players (ESPN 100, Rivals 150, On3 and 247 more) | SCH bio (quotes them) → service sites | top ~100–300 per class | RO | EVENT | R-PC-13 |
| `recruit_rank_pos_other` | Other services' position and state ranks as text | str | | SCH bio | | RO | EVENT | R-PC-13 |
| `rsci_rank` | RSCI consensus rank | int | | SR roster | top 100 per class | RO | EVENT | R-PC-13 |
| `recruit_rating_cbbd` | CBBD recruit `rating` | float | Composite source not documented | CBBD | ~22% [T, by analogy] | MI | EVENT | R-PC-13 |
| `recruit_rating_torvik` | Torvik "Rec Rank" numeric recruiting rating | float, 0–100 | Torvik converts ranks to a scale; method unverified | TVK | 22.2% [T] | MI-p | EVENT | R-PC-13 |
| `mcdonalds_aa_flag` | Selected for the McDonald's All American Game | bool | Nominee ≠ selection (all four MSU 2026 freshmen were nominees; two were selected per bios) | SCH bio → NEWS | ~24 per year [S] | RO | EVENT | R-PC-13 |
| `commit_date`, `signed_date` | Public commitment and signing dates | date | | 247 timeline → NEWS | ~100% for ranked recruits | RO | EVENT | R-PC-13 |
| `offers_list` | Scholarship offers reported | list | Self-reported, inflated, unverifiable | 247/ON3 offer lists | ranked recruits only | RO | EVENT | R-PC-13 (low value) |
| `draft_board_rank`, `draft_board_source`, `draft_board_as_of` | Rank on a public NBA draft board (ESPN, The Athletic, NBADraft.net) and Torvik "Pick" probability | int / float | Boards change weekly | TVK `pick` → NEWS boards | [T] 1.1% have a Torvik pick value | MI-p/RO | SNAP | R-PC-13 |

## 7. Transfer history (8 fields)

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `transfer_count` | Number of college-to-college moves before this season (JUCO→D-I counts) | int, 0–5 | | CBBD `/recruiting/portal` → SCH bio → TVK transfer list | 100% derivable | MI/RO | EVENT | R-PC-02, R-FD-12 |
| `transfer_events` | Ordered list `year: from -> to` | list | Portal "entered" ≠ transferred; keep only completed moves | CBBD (`origin`, `destination`, `year`) → On3 wire → SCH bio | 100% of transfers | MI/RO | EVENT | R-PC-02, R-FD-12 |
| `last_transfer_from`, `last_transfer_year` | Most recent previous school and move year | str, int | | as above | | | EVENT | R-PC-09 (previous school's physicality), R-FD-12 |
| `portal_stars`, `portal_rating` | Transfer-portal star rating and rating | int, float | Each service rates differently | CBBD (`stars`, `rating`) → On3 | portal entrants only | MI/RO | EVENT | R-PC-13 |

## 8. NIL (6 fields)

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `nil_valuation_usd` | Published NIL valuation | float, USD | On3 "NIL Valuation" is On3's model estimate, not money paid; actual deal and revenue-share amounts are almost never public | ON3 (could not be opened, 403) → EM Front Office Suite (paid) | [J] < 10% of D-I players (top recruits and stars); [M] 0/15 found | RO | SNAP | new-PC-5 (roster economics context; no ID covers NIL) |
| `nil_valuation_kind` | `model_estimate`, `reported_deal`, `public_record` | enum | | OWN | | OWN | | new-PC-5 |
| `nil_deals_public` | Publicly announced brand deals (names only) | list | Self-promotional; incomplete | NEWS, school NIL store | [J] | RO | EVENT | new-PC-5 |

Note: private social media is excluded (R-PC-15); a deal seen only on a player's social account is not recorded.

## 9. Season stats (61 fields on the card; full per-game lines live in W2 tables)

One block per completed season, the last D-I season before the card date (PRIOR); in-season cards hold the cumulative season to date (CUM). Counting stats come from box scores; rates come from a source that counts possessions.

**Possession definitions.** Ours: a possession ends only when the other team gains control; an offensive rebound starts a new chance inside the same possession. Box-score possession estimates (KenPom, Torvik, Sports-Reference: FGA − ORB + TO + c·FTA) also do not start a new possession on an offensive rebound, so they agree with ours in principle; the free-throw coefficient differs (KenPom 0.475, others about 0.44; both **unverified** here). Per-100 values from sources use their own estimate; ours use counted possessions from play-by-play (W2).

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `stats_season`, `stats_team` | Season and team of the block (a transfer's last season is at the old school) | str | | | | | PRIOR/CUM | R-PC-12 |
| `g`, `gs`, `min_total`, `min_pg` | Games, starts, minutes, minutes per game | int, int, float min, float min | Starts are scorekeeper data | CBBD `/stats/player/season` → TVK → SCH | 100% of players who played [T] | MI/MI-p/RO | PRIOR/CUM | R-PC-10, R-PC-12, R-CX-08 |
| `pts_pg`, `trb_pg`, `orb_pg`, `drb_pg`, `ast_pg`, `stl_pg`, `blk_pg`, `tov_pg`, `pf_pg` | Per-game box stats | float | Home scorekeepers credit more assists, blocks and steals (R-DQ-09) | CBBD → TVK → SCH | 100% | as above | PRIOR/CUM | R-PC-06..08 |
| `pts_total`, `trb_total`, `ast_total`, `stl_total`, `blk_total` | Season totals | int | | CBBD → SCH | 100% | | PRIOR/CUM | R-PC-07, R-PC-08 |
| `fgm`, `fga`, `fg2m`, `fg2a`, `fg3m`, `fg3a`, `ftm`, `fta` | Field goals, twos, threes, free throws made and attempted | int | | CBBD → TVK → SCH | 100% | | PRIOR/CUM | R-PC-06, R-PE-05 |
| `pts_per40`, `trb_per40`, `ast_per40` | Per 40 minutes = total ÷ minutes × 40 | float | Noisy below ~200 minutes; shrink (R-PC-06) | OWN from totals; SR per-40 table (RO) | 100% derivable | OWN | PRIOR/CUM | R-PC-06..08 |
| `pts_per100`, `trb_per100`, `ast_per100` | Per 100 team possessions while on court | float | Depends on the possession estimate (above) | OWN from counted possessions → SR per-100 (RO) | 100% derivable once lineups exist (CBBD 2023-24+) | OWN | PRIOR/CUM | R-PC-06..08 |
| `min_pct` | Share of team minutes played | float, % | | TVK `Min_per` → KPA `%Min` | 100% [T] | MI-p/MI | PRIOR/CUM | R-PC-10, R-CX-08 (returning minutes) |
| `efg_pct`, `ts_pct` | Effective FG% and true shooting % | float, % | TS uses a 0.44 FTA factor at most sources | TVK → CBBD → KPA | 100% | | PRIOR/CUM | R-PC-06 |
| `orb_pct`, `drb_pct` | Share of available offensive/defensive rebounds grabbed while on court | float, % | | TVK → KPA → CBBD (`offensiveReboundPct`) | 100% | | PRIOR/CUM | R-PC-08 |
| `ast_pct`, `tov_pct`, `ast_tov` | Assist rate, turnover rate per possession used, assists per turnover | float | Assist rate formulas differ (KenPom ARate vs SR AST%) | TVK → KPA → CBBD | 100% | | PRIOR/CUM | R-PC-07 |
| `blk_pct`, `stl_pct` | Block and steal rates | float, % | Scorekeeper bias | TVK → KPA | 100% | | PRIOR/CUM | R-PC-08 |
| `ftr`, `fg3a_rate` | FTA ÷ FGA; 3PA ÷ FGA | float | | TVK → CBBD | 100% | | PRIOR/CUM | R-PC-06, R-PC-11 |
| `fc_per40`, `fd_per40` | Fouls committed and drawn per 40 minutes | float | Fouls drawn need play-by-play attribution | KPA (`FC/40`, `FD/40`) → TVK (`pfr`, definition unverified) → CBBD fouls/min | 100% | MI/MI-p | PRIOR/CUM | R-PC-08, R-MD-16, R-PE-06 |
| `rim_fgm`, `rim_fga`, `mid_fgm`, `mid_fga`, `dunk_fgm`, `dunk_fga` | Shots by zone as the source defines them (Torvik: rim, mid-range two, dunks) | int | Zone comes from scorer shot type or charted location, not tracked position | TVK → CBBD `/stats/player/shooting/season` (dunks, layups, tip-ins, 2pt jumpers, 3pt jumpers, assisted %) → hR NCAA shot locations (2019+) | ~100% from 2013-14 (CBBD shot distribution) | MI-p/MI | PRIOR/CUM | R-PC-06 |
| `corner3_fgm`, `corner3_fga` | Corner three (θ ≤ 12° or ≥ 168°, r ≥ 6.60 m per config/vocabulary_map.yaml) | int | Needs x/y; manual shot charting errs by about a metre (R-DQ-09) | OWN from video → ESPN/hR shot x,y (RO) | MSU games only for OWN | OWN/RO | CUM | R-PC-06 |
| `rate_stats_source`, `rate_stats_licence` | Block provenance for rates and zones | str | | | | | | R-PC-14 |
| (W2 table) `player_shooting_sector_ring` | Makes and attempts by 15° sector × 0.5 m ring (`sector_15deg`, `ring_0p5m` from src/msu_alpha/geometry.py), catch-and-shoot vs off-dribble, each rate shrunk toward a prior with its n | table | | OWN | MSU and filmed opponents | OWN | CUM | R-PC-06 |

## 10. Impact metrics (19 fields)

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `ortg`, `drtg` | Dean Oliver individual offensive rating (points produced per 100 possessions used) and defensive rating | float, 60–160 | Unstable at low usage (one MSU walk-on shows ORtg 265 on 1% of minutes) | KPA → TVK → CBBD `offensiveRating`, `defensiveRating` | 100% of players with minutes | MI/MI-p | PRIOR/CUM | R-PC-10 |
| `usage_pct` | Share of team possessions used while on court | float, %, 5–40 | KenPom/Torvik %Poss vs SR USG% (Hollinger) differ | KPA → TVK → CBBD `usage` | 100% | | PRIOR/CUM | R-PC-10 |
| `porpag`, `dporpag` | Torvik points over replacement per adjusted game (offense, defense) | float | Torvik-specific | TVK → CBBD `PORPAG` | 100% [T] | MI-p/MI | PRIOR/CUM | R-PC-10 |
| `bpm`, `obpm`, `dbpm` | Box plus-minus (Torvik implementation) | float | Box-based; position assumptions | TVK | 100% [T] | MI-p | PRIOR/CUM | R-PC-10 |
| `bpr`, `obpr`, `dbpr`, `box_bpr` | EvanMiya Bayesian Performance Rating (total, offense, defense) and its box-only part | float | Method not fully public; preseason priors included | EM (export columns `bpr`, `obpr`, `dbpr`, `box_bpr`) | ~100% of D-I players with possessions [J] | MI-p | SNAP (EM updates daily) | R-PC-10 |
| `rapm_within`, `rapm_league` | Regularised adjusted plus-minus, within team and league-wide | float | Needs lineups; noisy within a season | hR (NCAA-engine lineups, gated by Torvik per catalog) → OWN from CBBD lineups (2023-24+) | D-I from 2010 via hR | RO (hR) / OWN | PRIOR/CUM | R-PC-10 |
| `win_shares` | Win shares (total; per 40 in CBBD) | float | | CBBD `winShares` → SR (RO) | 100% | MI | PRIOR/CUM | R-PC-10 |
| `onoff_net_rtg` | Team net rating with the player on minus off, per 100 possessions | float | Small samples; teammate collinearity | OWN from CBBD `/lineups` | 2023-24+ | OWN | CUM | R-PC-10, R-MD-15 |
| `impact_source`, `impact_licence`, `impact_as_of` | Block provenance | str, date | | | | | | R-PC-14 |

## 11. Role, minutes load, fouls and development (16 fields)

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `role_torvik` | Torvik role label (Pure PG, Scoring PG, Combo G, Wing G, Wing F, Stretch 4, PF/C, C) | enum | Box-stat clustering; tiny samples mislabel | TVK | 100% [T] | MI-p | PRIOR | R-PC-10 |
| `role_cluster_own` | Our data-driven role cluster from tracking and PBP (R-PC-10), plus transition role (R-TR-15) in W2 | enum | | OWN | MSU and filmed opponents | OWN | CUM | R-PC-10, R-TR-15, R-ST-12 |
| `listed_vs_played_position` | Listed position vs the spot the player mostly occupies (from tracking) | str | | OWN | | OWN | CUM | R-PC-10 |
| `minutes_last7d`, `minutes_last14d`, `games_last7d` | Minutes and games in the 7 and 14 days before the card date | float min, int | | OWN from CBBD box/PBP | 100% | OWN | CUM | R-CX-05, R-PL-06 |
| `avg_stint_min`, `max_continuous_min` | Mean stint length and longest continuous stint this season | float, min | Substitution timing errors in PBP (R-DQ-09) | OWN from CBBD `/substitutions` (2023-24+) | 2023-24+ | OWN | CUM | R-PE-06, R-PL-03, R-CO-07 |
| `fouls_per_game`, `foul_outs`, `foul_trouble_min_lost` | Personal fouls per game, games fouled out, minutes lost to foul-trouble benching (estimate) | float, int, float min | Benching cause is inferred | CBBD box and substitutions → OWN | 100% / 2023-24+ | MI/OWN | CUM | R-MD-16, R-PE-06 |
| `career_d1_games`, `career_d1_minutes`, `seasons_d1` | D-I career counts before the card date | int, float min, int | JUCO and non-D-I years excluded by definition | CBBD season stats summed → TVK | 100% for 2002-03+ (CBBD) | MI | CUM | R-PC-12 |
| `seasons_in_program` | Completed seasons in this program before the current one ("years in Izzo's system") | int | Redshirt and injury years count as in program | SCH bio + roster history | 100% | RO/OWN | PRIOR | R-FD-12 |
| `role_source` | Block provenance | str | | | | | | R-PC-14 |

Foul type mix (shooting, personal, offensive, loose-ball, technical, flagrant) per player is a W2 table from play-by-play (R-RF-03).

## 12. Availability and public injury reports (9 fields)

Health data: only what a school, conference or reputable outlet has published (R-RG-06, R-PC-15). We record availability and a coarse reason category, not medical detail.

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `availability_status` | `available`, `game_time_decision`, `out`, `suspended`, `redshirt`, `unknown` for the next game | enum | Many schools disclose nothing; absence of a report ≠ available | CONF reports (Big 12 and ACC require basketball reports from 2025-26; Big Ten basketball requirement **not found**) → SCH game notes → NEWS | Big 12 + ACC teams ~100% for conference games; others [J] < 30% | RO | SNAP (night before and 90 min before tip in the Big 12) | R-FD-05, R-CX-08 |
| `availability_status_as_of`, `availability_source` | Report time and source | datetime, str | | | | | SNAP | R-FD-05, R-CX-09 |
| `games_missed_last_season` | Team games the player did not play last season, or `all` | int / `all` | DNP-coach's decision vs unavailable are hard to tell apart | OWN from CBBD box (games played vs team games) + SCH bio | 100% derivable | OWN/RO | PRIOR | R-FD-05, R-PL-06 |
| `games_missed_reason_category` | `injury`, `illness`, `personal`, `suspension`, `coach_decision`, `redshirt`, `unknown` | enum | Only public statements; no diagnosis stored | SCH bio → NEWS | [J] | RO | PRIOR | R-FD-05 |
| `season_missed_flag` | Missed the whole previous season | bool | | as above | | RO | PRIOR | R-FD-05, R-PC-12 |
| `medical_redshirt_flag` | Granted a medical hardship waiver (publicly reported) | bool | Waivers often granted silently | NEWS → SCH | [J] | RO | EVENT | R-FD-05 |
| `availability_note_public` | One-line public summary with the source, no medical detail beyond what was published | str | | SCH, NEWS | | RO | EVENT | R-FD-05, R-RG-06 |
| `minutes_limit_public` | A publicly stated minutes restriction | float, min | Rarely stated | NEWS (coach press conference) | [J] < 5% | RO | SNAP | R-CX-08 |

Aldemir's own availability notes are private and live in a separate private table (R-RG-06), never on this card.

## 13. International, USA Basketball and camps (6 fields)

| Field | Definition | Type, unit, range | Bias / caveat | Sources (priority) | D-I coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fiba_youth_events` | FIBA youth events played (event, year, result) | list | | USAB/FIBA → SCH bio | [J] 5–10% | RO | EVENT | R-PC-16 |
| `usab_events` | USA Basketball teams and minicamps | list | | USAB → SCH bio | [J] | RO | EVENT | R-PC-16 |
| `pro_leagues` | Professional leagues played before college | list | | NEWS → SCH | rare | RO | EVENT | R-PC-16 |
| `hoop_summit_flag` | Played in the Nike Hoop Summit | bool | Hoop Summit publishes in-shoe measurements for its rosters (2014 list seen) | NEWS → SCH | ~24 per year [S] | RO | EVENT | R-PC-16, R-PC-04 |
| `camps_attended` | Elite camps (NBPA Top 100, adidas Eurocamp, Pangos, Nike Skills Academies) | list | Camps rarely publish measurements | SCH bio → NEWS | [J] 5–10% | RO | EVENT | R-PC-04 (where measurements may exist), R-PC-13 |
| `intl_source` | Block provenance | str | | | | | | R-PC-14 |

## 14. Tracking-derived fields — **computed by us** (20 fields)

Every field here is computed by our pipeline from video; none exists in any public college source (catalog: no public college tracking feed). Season values are summaries of per-game tables (W2). Each value states coverage (R-PL-05) and is left empty for stints below the R-PL-14 coverage gate.

| Field | Definition | Type, unit, range | Bias / caveat | Source | Coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `trk_top_speed_ms_max`, `trk_top_speed_ms_p95` | Highest and 95th-percentile speed of the tracked point (pelvis projection or ankle midpoint) | float, m/s, 0–10 | Filter-dependent; > 10 m/s is an error (R-EN-03) | **computed by us** | filmed games | OWN | CUM | R-PC-05, R-PL-03, R-PL-10 |
| `trk_accel_efforts_per40`, `trk_decel_efforts_per40` | Efforts beyond ±2.0 and ±3.0 m/s² per 40 min (bands per R-PL-12) | float | Nothing above 4 m/s² reported | **computed by us** | | OWN | CUM | R-PC-05, R-PL-02, R-PL-12 |
| `trk_dist_per_min_m`, `trk_hsr_dist_per_min_m`, `trk_sprint_count_per40` | Distance per minute played; high-speed (5.0–5.83 m/s) distance; sprints (> 5.83 m/s, ≥ 1 s) | float m/min, int | Three denominators stored in W2 (R-PL-15) | **computed by us** | | OWN | CUM | R-PL-01, R-PL-09, R-PL-11, R-PL-15 |
| `trk_lateral_slide_ms` | Peak lateral speed in defensive slides | float, m/s | Needs pose to know facing | **computed by us** | | OWN | CUM | R-PC-05 |
| `trk_cod_time_s` | Change-of-direction time (decel to re-accel) | float, s | | **computed by us** | | OWN | CUM | R-PC-05 |
| `trk_jump_height_cm_max` | Highest jump (after R-CG-11 3D) | float, cm | Monocular height error | **computed by us** | | OWN | CUM | R-PC-05 |
| `trk_release_height_m`, `trk_catch_to_release_s` | Shot release height and catch-to-release time | float m, s | | **computed by us** | | OWN | CUM | R-PL-07 |
| `trk_ft_routine_s`, `trk_ft_dribbles`, `trk_ft_arc_deg_sd` | Free-throw routine time (ball in hand from official to release), dribble count, standard deviation of arc entry angle | float s, int, float ° | Routine start depends on camera view of the official's bounce pass | **computed by us** | | OWN | CUM | R-PL-08 |
| `trk_decision_latency_s` | Median catch-to-first-action time | float, s | | **computed by us** | | OWN | CUM | R-CO-01 |
| `trk_height_px_signature` | Height in pixels normalised by camera scale, used as an identity tie-breaker | float | Kept only if it helps (R-ID-13) | **computed by us** | | OWN | CUM | R-ID-13 |
| `trk_coverage_share`, `trk_games_n`, `trk_as_of` | Share of floor time observed on the main camera; games used; last game included | float 0–1, int, date | | **computed by us** | | OWN | CUM | R-PL-05, R-PL-14 |

## 15. CV appearance for re-identification (7 fields; no faces)

Per-game appearance is filled at tip (R-ID-12) in a W2 per-game table; the card keeps the season's default. Jersey colours are team-level (R-CX-07, W2 games table).

| Field | Definition | Type, unit, range | Bias / caveat | Source | Coverage | Licence | As-of | Req IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `cv_shoe_colour_default` | Dominant shoe colour(s) as a named colour plus sRGB hex | str | Players change shoes between games and halves | **computed by us** from video; confirmed per game | filmed games | OWN | CUM | R-ID-12 |
| `cv_sleeve_default` | Arm or leg sleeve (`none`, `left_arm`, `right_arm`, `left_leg`, `right_leg`, colour) | str | | **computed by us** | | OWN | CUM | R-ID-12 |
| `cv_headband_default` | Headband (`none` or colour) | str | | **computed by us** | | OWN | CUM | R-ID-12 |
| `cv_tape_default` | Visible tape (fingers, wrist, ankle) | str | | **computed by us** | | OWN | CUM | R-ID-12 |
| `cv_socks_default` | Sock height and colour | str | | **computed by us** | | OWN | CUM | R-ID-12 |
| `cv_appearance_as_of`, `cv_appearance_source` | Last game seen; model version | date, str | | | | OWN | CUM | R-ID-12, R-DQ-04 |

Excluded from CV appearance by design: face, skin tone (a race proxy), hair as an identity feature, tattoos (identifying body marks; excluded pending Aldemir's decision), gait as a biometric template (movement signature is allowed only as an R-ID-13 tie-breaker and is not stored on the card).

## 16. Notes

| Field | Definition | Type | Req IDs |
| --- | --- | --- | --- |
| `card_notes` | Free text: conflicts between sources, conversions, caveats | str | R-DQ-09, R-PC-14 |

## 17. Excluded by design (R-PC-15)

Not collected, not derived, not inferred: race, ethnicity or any proxy (including hometown demographic make-up, skin tone, names used as a proxy), face images or embeddings (R-ID-10), private health information (diagnoses, medications, medical records; only publicly reported availability is kept), private social media, family details from bios (parents' names, siblings), religion, academic records (GPA, major is not stored either), and contact data. Bios contain family and personal facts; the card copies only basketball-relevant fields.

---

## 18. Where college players' body measurements are published (research, 18 Oct 2026)

| Source | What it publishes | Measured or listed | How often for D-I players | Access and terms | Verified |
| --- | --- | --- | --- | --- | --- |
| **School roster pages** (Sidearm sites, e.g. msuspartans.com) | Listed height (ft-in) and weight (lb) for every player; bios sometimes add wingspan in prose ("Has a 6-11 wingspan") | **Listed**; protocol unknown, usually rounded up; bio wingspans are anecdotal | Height ~100%, weight ~95% [J]; bio wingspans [M] 5/15 | Public; site terms not reviewed → RO. CBBD `/teams/roster` carries the same listed height/weight with MI terms | Opened MSU 2026-27 roster and all 15 bios |
| **NBA Draft Combine** (nba.com/stats/draft/combine-anthro; API `draftcombineplayeranthro`, `draftcombinedrillresults`) | Height without shoes (and with shoes in older years), weight, wingspan, standing reach, body-fat %, hand length and width; standing and max vertical, lane agility, modified lane agility, 3/4-court sprint, bench press | **Measured** by the NBA | ~73 invitees in 2026 plus G League Elite camp standouts; ~1–1.5% of D-I players per season [S]. MSU 2026-27: 1 of 15 (2026 combine) | NBA ToU: private, non-commercial → MI-p. The nba.com page renders no data without JavaScript; direct `stats.nba.com` calls timed out from this Mac | Opened nba.com page (selector 2000-01 to 2026-27, no rows rendered), nba.com 2026 combine overview (measures hand length and width, barefoot height, body fat, standing reach, weight, wingspan; tests no-step and max vertical, lane agility, 3/4 sprint, shuttle), nba_api endpoint docs (column names) |
| **247Sports player profiles** | "Verified Results" block (copies combine numbers with event and date, e.g. NBA Draft Combine 05/14/26 incl. hand length/width, verticals, agility, shuttle, sprint); listed Ht/Wt; scouting text with wingspan and reach estimates | Verified block = measured (copied); scouting text = reported | Verified results only for combine/camp attendees; scouting wingspans for ranked recruits [J] | CBS ToU bans scraping and data mining → RO, manual reading only | Opened 4 profiles (Fears, Taylor, Jervis, Medlock) |
| **Nike Hoop Summit** (USA and World teams) | Height in shoes, weight, wingspan, standing reach | Measured by USA Basketball (heights in shoes) | ~24 players a year, most become D-I or pro [S] | Published via NBADraft.net/DraftExpress articles → RO | Opened NBADraft.net 2014 Hoop Summit list ("Official Measurements from USA Basketball (heights are in shoes)"). 2026 list **not found** |
| **adidas Eurocamp, NBPA Top 100 Camp, Nike/adidas grassroots events** | Occasionally barefoot height, wingspan, reach (DraftExpress posts) | Measured, protocol varies | Sporadic; no complete list found for 2025 or 2026 | DraftExpress articles returned 404; search found only secondary mentions → **unverified** | Not verified |
| **On3 / Rivals, ESPN recruiting** | Listed Ht/Wt for recruits; On3 NIL valuation | Listed | Ranked recruits | On3 returned 403; ESPN pages not used (ESPN terms) → RO, **unverified** | Not opened |
| **CBBD** `/teams/roster`, `/recruiting/players`, `/draft/picks` | Height (in), weight (lb), hometown with coordinates, date of birth (roster); heightInches, weightPounds (recruits); height, weight (draft picks) | Listed | Roster ~100% [J]; recruits ~22% | MI | Opened the OpenAPI spec (v1.30.1) only; no data calls made |
| **Torvik** | Height (`ht`), hometown, birth date, recruiting rating, jersey number, role | Listed | 100%/99.9%/99.7%/22% [T] | MI-p | Pulled the 2025-26 CSV once |
| **KenPom** | Player height on team pages; team effective height and average height (minutes-weighted) | Listed | 100% of players with minutes | API MI; web RO (no scrapers) | Not opened (catalog only) |

**Conclusions.** (1) For nearly every D-I player the only body data is the listed height and weight. (2) Measured anthropometrics exist only for combine invitees and a few elite-camp or Hoop Summit players, so for MSU's typical opponent no measured wingspan, reach or hand size exists. (3) Bio and scouting wingspans are useful as reference but disagree with each other and are never treated as measurements.

## 19. Fields almost never public for college players, and the defensible proxy

| Field | Public availability | Defensible proxy | Notes |
| --- | --- | --- | --- |
| `shoe_size_us` | ≈ 0% | **none** | Foot length from video is not reliable at broadcast resolution |
| `hand_length_cm`, `hand_width_cm` | ≈ 1% (combine only) | **none** for a player value. A population prior (combine regression on height and wingspan) may be stored only as `*_imputed` with its prediction interval, never as a measurement | |
| `body_fat_pct` | ≈ 1% (combine) | **none** | Health-adjacent; do not estimate from video |
| `height_wo_shoes_cm` | ≈ 1–1.5% | Listed height minus a bias correction fitted on players who have both (combine vs listed), stored as `*_imputed`; or height from our tracking (`trk_height_px_signature` with court scale) once validated | The MSU sample shows a +5.08 cm listed-height excess for the one measured player; one point is not a correction |
| `wingspan_cm` (measured) | ≈ 1–2% | Reported bio/scouting wingspan (RO, `wingspan_kind = reported`); arm span from pose keypoints at court scale (research only, error unknown) | |
| `standing_reach_cm` | ≈ 1–2% | Regression on height and wingspan from combine data (`*_imputed`) | |
| `standing_vertical_cm`, `max_vertical_cm` | ≈ 1% | `trk_jump_height_cm_max` (computed by us, after R-CG-11) | Self-reported verticals are not used |
| `lane_agility_s`, `shuttle_run_s`, `three_quarter_sprint_s`, `bench_press_reps` | ≈ 1% | `trk_top_speed_ms_*`, `trk_cod_time_s`, `trk_accel_efforts_per40` (computed by us); none for strength | |
| `shooting_hand`, drive and finishing laterality | 0% as data (visible on video) | Computed by us from video | |
| `nil_valuation_usd` (actual money) | ≈ 0% actual; On3 estimates for top players | On3 valuation as `model_estimate` (RO) | |
| `eligibility_seasons_remaining` | Rarely explicit | Count of D-I seasons played from CBBD plus class label; flag uncertain | Waivers and rule changes |
| Medical detail | Not collected by design | **none** | Only public availability (section 12) |

## 20. MSU 2026-27 sample cards (private file) — summary

- Roster source: msuspartans.com 2026-27 roster page (Sidearm Nuxt data), 15 players: #0 Avent, #1 Fears Jr., #2 Teng, #3 Ward, #6 Scott, #7 Medlock Jr., #8 Glenn, #10 Taylor, #20 Watkins, #25 Jervis, #34 Bonke, #35 McCulloch, #40 B. Walton, #43 C. Walton, #55 Carr. Bios opened for all 15 (Watkins has no bio text yet).
- File: `~/MSU-Alpha-3-private/data/licensed/players/msu_2026-27_cards.csv`, 16 lines (header + 15), 303 columns, 191 columns filled for at least one player.
- Cross-source conflicts found (kept in `*_check` and `card_notes`):
  - Birth date: one player differs between school bio and Torvik by 15 days.
  - Hometown: one player differs (school vs Torvik, neighbouring towns).
  - Listed height: 4 of 9 returners differ by 1 in (2.54 cm) between the 2026-27 school roster and Torvik's 2025-26 height.
  - Wingspan: 2 of 5 bio wingspans disagree with 247 scouting text (by 2.5 cm and 7.6 cm).
  - Games played: one transfer's games differ by 1 between school bio and Torvik.
  - Listed vs measured height: the one combine-measured player is listed 5.08 cm taller than his barefoot height.
- Registry note: `registry/rosters.csv` labels by ESPN season (`2026` = 2025-26) but includes a 2026 freshman under `2026`, so the registry `season` label needs checking (open question).

## 21. Open questions for Aldemir

1. Torvik, NBA combine and EvanMiya values: may they be model inputs (MI-p → MI), or reference only?
2. School athletics sites: treat listed height/weight/hometown as reference only (use CBBD for model input), or accept school sites as MI?
3. Tattoos and hairstyle: keep excluded from CV re-identification, or allow as appearance tie-breakers (never faces)?
4. Gait or movement signature for re-ID (R-ID-13): allowed as a computed tie-breaker that is never stored on the card?
5. Big Ten basketball availability reports: none found for 2025-26; should we log Big 12/ACC opponents' reports when we play them?
6. NIL: record On3 valuations (model estimates, RO) or skip NIL entirely?
7. Imputed body values (barefoot height, reach, hand size from regressions): allowed as model priors in `*_imputed` columns, or never?
8. `registry/rosters.csv` season label: a 2026 freshman appears under season `2026` alongside 2025-26 players; confirm what the label means before using it for jersey history.
9. CBBD calls for the card (roster, recruiting, portal): spend about 5 of the 50-call budget so cards get MI values for height, weight, birth date and hometown coordinates?
10. Should the card store birth date, or only age at tip (same information, less personal)?

## 22. Sources opened for this file (18 Oct 2026)

- https://msuspartans.com/sports/mens-basketball/roster (2026-27 roster; fetched with curl, Nuxt data parsed)
- https://msuspartans.com/sports/mens-basketball/roster/anton-bonke/17820 and the 14 other bio pages listed in the private card file (`school_roster_url`)
- https://www.nba.com/stats/draft/combine-anthro
- https://www.nba.com/news/nba-draft-combine-overview-2026
- https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/draftcombineplayeranthro.md
- https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/draftcombinedrillresults.md
- https://247sports.com/player/jeremy-fears-46099301/
- https://247sports.com/player/ethan-taylor-46142904/
- https://247sports.com/player/jasiah-jervis-46146430/
- https://247sports.com/player/carlos-medlock-jr-46158375/
- https://www.nbadraft.net/?p=88153 (2014 Hoop Summit measurements)
- https://www.nbadraft.net/2026-nba-draft-combine-measurements-winners-and-losers/
- https://www.babcockhoops.com/post/2026-nba-draft-combine-measurements-height-weight-wingspan-and-standing-reach (no values rendered)
- https://www.wilx.com/2026/08/14/former-michigan-state-manager-matthew-watkins-earns-chance-suit-up-spartans/
- https://www.cbssports.com/college-football/news/big-12-to-mandate-player-availability-reports-for-football-basketball-starting-in-2025-26
- https://api.collegebasketballdata.com/api-docs.json (OpenAPI spec v1.30.1; no data endpoints called)
- https://barttorvik.com/getadvstats.php?year=2026&csv=1 (one pull, kept outside the repo)
- https://nominatim.openstreetmap.org/search (15 geocodes: 14 hometowns and the Breslin Center)

Attempted, not usable: https://www.draftexpress.com/article/2016-Nike-Hoop-Summit-USA-Junior-National-Select-Team-Measurements-5428/ and the 2015 equivalent (404); https://www.on3.com/pro/news/2026-nba-draft-winners-losers-from-combine-measurements-notable-numbers/ (403); `stats.nba.com/stats/draftcombineplayeranthro` (timed out).

Seen only in search results (not opened, **unverified**): pr.nba.com 2026 combine invitee list; State News headline that Matthew Watkins earned a walk-on spot; Rotowire notes on Anton Bonke withdrawing from the 2026 draft and on Kaleb Glenn and the portal; CBS/WILX reports on Kaleb Glenn's 2025 injury; Spartan Avenue and Zagsblog on Bonke's commitment.

---

## Verification note 2026-10-18

Added after the first real CBBD responses were read (`/teams/roster` 2026 and 2027, `/games/players`, `/recruiting/players` 2026, `/recruiting/portal` 2026, `/draft/picks`); evidence in `docs/data/source_field_map.md`, section "Verified against real responses (2026-10-18)". The field tables above stay as written; these are the changes.

| Field | Change |
|---|---|
| `cbbd_athlete_id` | Gotcha "`sourceId` appears to be ESPN's ID (unverified)" → **verified**: roster `sourceId` and box `athleteSourceId` are ESPN athlete ids (11/11 against `registry/rosters.csv`). `cbbd_athlete_id` = roster `id` = `athleteId` in box, play, substitution and lineup rows |
| `espn_athlete_id` | Add source: CBBD roster `sourceId` (MI as a join key). With it, coverage on the MSU sample is 15/15 (was 10/15) |
| `birth_date` | CBBD `dateOfBirth` was **null on all 30** MSU roster rows (2025-26, 2026-27); drop CBBD from the source chain until a non-null value is seen |
| `hometown_city`, `hometown_country_iso2`, `hometown_lat/lon` | CBBD `hometown.country` null on all 30 roster and 4 recruit rows; lat/lon filled on 29/30 (city centroids). `countyFips` present; still not stored |
| `height_listed_raw/cm`, `weight_listed_raw/kg` | CBBD roster `height` = **integer inches**, `weight` = **integer pounds** (verified); values equal the school roster on 15/15 for 2026-27. Keep the CBBD values in separate `cbbd_roster_*` columns (private card file, added 2026-10-18) so the listed-height bias check keeps two sources |
| `listed_position` | CBBD roster gives `Guard` / `Forward` / `Center` (long form) and was **null for 5 of 15** newcomers; box rows give `G` / `F` / `C`; recruits give finer codes (`PG`, `SG`, `PF`, `C`) |
| `class_year_listed`, `eligibility_*` | CBBD `startSeason` is the first season **with the current team** (transfers reset it), so it cannot derive class year. Portal `yearsRemaining` was null |
| `hs_class_year`, `recruit_stars`, `recruit_rating_cbbd` | CBBD `/recruiting/players`: `year`, `stars`, `rating` (0–1 scale) confirmed. **`athleteId` is null** on all 4 recruits, so the join to the roster is by name + team + year |
| new column `recruit_rank_nat_cbbd` | CBBD recruit `ranking` is a national rank that **does not equal** the 247 Composite rank recorded from school bios for the same players; keep it in its own column, source unnamed by CBBD |
| new columns `recruit_height_*_cbbd`, `recruit_weight_*_cbbd` | CBBD `heightInches`/`weightPounds` are recruiting-time values; they differ from the current roster by up to 2 in and 22 lb on the MSU sample. Keep them separate from listed values (they also show growth between recruitment and enrolment) |
| `portal_stars`, `portal_rating`, `transfer_events` | CBBD portal: `stars`, `rating` (0–1), `origin`, `destination` (CBBD team ids), `eligibility` (`Immediate` seen), `year` = portal cycle. No height, weight or athlete id |
| `min_total`, `min_pg` (from CBBD box) | CBBD box `minutes` is whole minutes per game; season minutes summed from it carry up to ±0.5 min per game of rounding |
| `draft_*` (if filled from CBBD) | `/draft/picks` `height` = inches, `weight` = pounds; `athleteId` null on older picks |

The private card file `~/MSU-Alpha-3-private/data/licensed/players/msu_2026-27_cards.csv` was filled from these responses on 2026-10-18 (backup kept next to it); the new columns are listed in the main session's report, not here.
