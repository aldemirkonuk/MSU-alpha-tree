# L4 round 4 and unit fixes (19 Oct 2026)

Aldemir: "Reproduce the 80 box and play-by-play stats that have an L4 recipe, then fix the 108 unit and range issues."

Data: CBBD MSU 2025-26 (35 games; play-by-play for 34, UNC excluded), KenPom and Torvik 2026 (365 teams). Match rates only; data stays private. Registry version 0.5.0.

## Recipe results

| Check | Matches | Rate | Max abs. diff |
| --- | --- | --- | --- |
| M-TRAT-002 competition rank of KenPom adj_em vs published rank (exact) | 355/365 | 97.3% | 1 |
| M-TRAT-002 KenPom adj_em: published rank inside the tie group of the displayed (rounded) value | 365/365 | 100.0% | 0 |
| M-TRAT-002 competition rank of KenPom adj_oe vs published adj_oe_rank (exact) | 210/365 | 57.5% | 5 |
| M-TRAT-002 KenPom adj_oe: published rank inside the tie group of the displayed (rounded) value | 365/365 | 100.0% | 0 |
| M-TRAT-002 competition rank of KenPom adj_de vs published adj_de_rank (exact) | 200/365 | 54.8% | 6 |
| M-TRAT-002 KenPom adj_de: published rank inside the tie group of the displayed (rounded) value | 365/365 | 100.0% | 0 |
| M-TRAT-002 competition rank of KenPom adj_t vs published adj_t_rank (exact) | 97/365 | 26.6% | 10 |
| M-TRAT-002 KenPom adj_t: published rank inside the tie group of the displayed (rounded) value | 365/365 | 100.0% | 0 |
| M-TRAT-002 competition rank of Torvik barthag vs published rank (exact) | 365/365 | 100.0% | 0 |
| M-TRAT-002 competition rank of Torvik adjoe vs published oe Rank (exact) | 365/365 | 100.0% | 0 |
| M-TRAT-002 competition rank of Torvik adjde vs published de Rank (exact) | 365/365 | 100.0% | 0 |
| M-TRAT-043 W-L from CBBD games vs Torvik record (both numbers) | 1/1 | 100.0% | 0 |
| M-TRAT-043 W-L from CBBD games vs KenPom w_l (both numbers) | 1/1 | 100.0% | 0 |
| M-TRAT-044/069 conference win % (regular-season STD games) vs Torvik Conf Win% | 1/1 | 100.0% | 0.0 |
| M-SIT-079 home + away + neutral wins sum to the Torvik record wins | 1/1 | 100.0% | 0 |
| M-TRAT-028 SOS: mean opponent KenPom AdjEM (all games) vs KenPom sos_adj_em (within 0.5) | 0/1 | 0.0% | 1.1234 |
| M-TRAT-030 NCSOS: mean non-conference opponent KenPom AdjEM vs KenPom ncsos_adj_em (within 0.5) | 0/1 | 0.0% | 6.9729 |
| M-TRAT-028 SOS-O: mean opponent KenPom AdjOE vs sos_adj_oe (within 0.3) | 0/1 | 0.0% | 0.5229 |
| M-TRAT-028 SOS-D: mean opponent KenPom AdjDE vs sos_adj_de (within 0.3) | 0/1 | 0.0% | 0.5543 |
| M-TRAT-030 NCSOS: mean regular-season non-conference opponent AdjEM vs ncsos_adj_em (within 0.5) | 0/1 | 0.0% | 4.4118 |
| M-SHOOT-017 / M-FOUL-095 team points per 100 possessions = CBBD rating | 70/70 | 100.0% | 0.05 |
| M-DEF-002 opponent points per 100 own possessions = opponent row rating | 70/70 | 100.0% | 0.05 |
| M-PHYS-006 / M-PROF-004 player minutes sum = 5 x game length (within 2 min) | 35/35 | 100.0% | 0 |
| M-PROF-005 Min% sums to 500 (within 5) | 35/35 | 100.0% | 0.0 |
| M-PROF-010 sum of player box points = team box (team rebounds excluded where noted) | 35/35 | 100.0% | 0 |
| M-PROF-010 sum of player box assists = team box (team rebounds excluded where noted) | 35/35 | 100.0% | 0 |
| M-PROF-010 sum of player box steals = team box (team rebounds excluded where noted) | 35/35 | 100.0% | 0 |
| M-PROF-010 sum of player box blocks = team box (team rebounds excluded where noted) | 35/35 | 100.0% | 0 |
| M-PROF-010 sum of player box defensive rebounds = team box (team rebounds excluded where noted) | 34/35 | 97.1% | 4 |
| M-PROF-010 sum of player box FGA = team box (team rebounds excluded where noted) | 35/35 | 100.0% | 0 |
| M-PROF-010 sum of player box 3PA = team box (team rebounds excluded where noted) | 35/35 | 100.0% | 0 |
| M-PROF-010 sum of player turnovers + team turnovers = team box turnovers | 35/35 | 100.0% | 0 |
| M-SIT-001 max elapsed game seconds from PBP = game length | 34/34 | 100.0% | 0 |
| M-SHOOT-027 / M-SHOOT-025 zone partition: rim + jumper + three = FGA (box) | 68/68 | 100.0% | 0 |
| M-SQ-040 three zone made/attempted = box 3PM/3PA | 68/68 | 100.0% | 0 |
| M-SQ-040 / M-SHOOT-024 two-point zones (rim + jumper) FG% = box 2P% | 68/68 | 100.0% | 0.0486 |
| M-SQ-010 3PA rate from PBP = from box | 68/68 | 100.0% | 0.0 |
| M-SHOOT-001 sum of scoreValue over scoring plays = box points | 68/68 | 100.0% | 0 |
| M-SHOOT-031 / M-SQ-023 / M-DEF-013 assisted made FG (PBP flag) = box assists (within 1) | 63/68 | 92.7% | 3 |
| M-PASS-009 points off assisted + unassisted makes + FT points = box points | 68/68 | 100.0% | 0 |
| M-SHOOT-062 heave + non-heave FGA = box FGA (partition) | 68/68 | 100.0% | 0 |
| M-SHOOT-047 / M-SQ-026 own shots blocked (opponent block rows) = opponent box blocks | 68/68 | 100.0% | 0 |
| M-IMP-001 / M-IMP-009 sum of MSU players' plus-minus = 5 x MSU margin | 31/34 | 91.2% | 31 |
| M-IMP-008 stint points (home + away) = box points of both teams | 34/34 | 100.0% | 0 |
| M-IMP-008 sum of MSU on-court seconds = 5 x game seconds (within 60 s) | 32/34 | 94.1% | 1885 |
| M-PHYS-008 / M-PROF-050 / M-PROF-004 stint-sum minutes from PBP onFloor vs box minutes (within 1) | 357/386 | 92.5% | 7.6833 |
| M-PROF-001 games played: box minutes > 0 agrees with presence in PBP onFloor | 386/386 | 100.0% | 0 |
| M-IMP-062 last homeWinProbability equals the result (WPA telescopes to result - opening WP) | 10/25 | 40.0% | 0.098 |

Market accuracy of the median CBBD closing spread on MSU games (computed, no published value): n = 35, MAE 9.04, RMSE 11.08, R² 0.533, mean home error -0.59 points.

## Outcome for the 80

- Raised: 18 to L4 and 18 to L5 (identities and partitions on real data).
- Reached nothing new (5): KenPom SOS and NCSOS are not plain means of opponent ratings (KenPom's own method); the play-by-play assisted flag under-counts team assists by about 1 per game (92.6% within 1).
- Recorded without reproduction: the Oliver ORtg components (79% within 2 of CBBD, variant undocumented), CBBD and KenPom possessions and luck, Torvik Qual Games, our opponent-adjusted replica (needs all D-I games), ejections (none in 396 player-games), and the market accuracy metrics (no published value).
- Data faults found: CBBD onFloor sometimes lacks 5 players per team (3 of 34 games break the plus-minus identity; stint minutes within 1 min for 92.5% of player-games); CBBD's win-probability series often ends at 0.99 instead of 0/1, so the result must be appended before summing WPA.

## The 108 unit and range fixes

| Kind | Count | Example |
| --- | --- | --- |
| 0-1 fraction stored as percent: x100 | 33 | M-FOUL-090 free-throw % by attempt position |
| Range must be signed (margins, differences, residuals, WP changes) | about 60 | M-TEFF-025 efficiency over expectation |
| Range per component (mixed outputs) | 8 | M-SQ-001 shot location x, y, r, theta |
| Height cm to m | 2 | M-TRAT-021, M-PROF-045 |
| Feet to metres inside a model | 1 | M-DEF-067 |
| KenPom luck is a win-fraction difference, not percent | 1 | M-TRAT-049 |
| Wrong or unverified unit text (BPI per 70, seconds with no seconds term, plays vs half-court possessions, unknown EvanMiya unit, currency) | 7 | M-TRAT-014, M-PASS-037, M-PLAY-039 |
| Formula scale bug (Min% entered as percent gives ~220 points per game) | 1 | M-IMP-056 PRPG |

Old values are kept in `unit_before_2026_10_19` and `value_range_before_unit_fix`; every fix has `unit_fix_2026_10_19` and a dated note. km is now registered as an allowed unit for travel and geography distances above 1 km; court and movement distances stay in metres.

## Registry depth now

| Depth | Metrics |
| --- | --- |
| L0 | 35 |
| L1 | 585 |
| L2 | 135 |
| L3 | 665 |
| L4 | 137 |
| L5 | 34 |
