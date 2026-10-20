# L4 reproduction on CBBD data, MSU 2025-26 (19 Oct 2026)

Aldemir: "recompute the box and PBP stats on CBBD data for MSU 2025-26 and compare with published values (L4), and fix the 30 unit problems".

Data: CBBD per-game team box (35 games, both teams = 70 rows) and player box (MSU players, about 300 rows) pulled 18 Oct, and the full play-by-play of all 35 games (33 pulled 19 Oct; 945 calls left). Published values are CBBD's own computed fields in the same rows. All data stays private (`~/MSU-Alpha-3-private/processed/stats_l4/`); this page shows match rates only. Registry: version 0.3.0.

## Results

| Check | Matches | Rate | Mean abs. diff | Max abs. diff |
| --- | --- | --- | --- | --- |
| M-TEFF-002 (c_FT=0.475, registry default) | 36/70 | 51.4% | 1.129 | 4.35 |
| M-TEFF-002 (c_FT=0.44) | 40/70 | 57.1% | 1.07 | 3.8 |
| M-TEFF-010 pace (two-team mean, c_FT=0.44, per 40) | 8/70 | 11.4% | 0.839 | 2.5 |
| M-TEFF-018 ORtg (on published possessions) | 70/70 | 100.0% | 0.028 | 0.05 |
| M-SHOOT-011 eFG% | 70/70 | 100.0% | 0.024 | 0.05 |
| M-TEFF-031 FTA rate (FTA/FGA) | 70/70 | 100.0% | 0.023 | 0.049 |
| M-TOV-006 TOV% (per published possession) | 70/70 | 100.0% | 0.025 | 0.048 |
| M-REB-007 ORB% Oliver: ORB/(ORB+Opp DRB) | 2/70 | 2.9% | 6.799 | 16.9 |
| CBBD ORB% variant: ORB/(own ORB+DRB) | 70/70 | 100.0% | 0.024 | 0.05 |
| M-SHOOT-012 TS% (k=0.475, registry default) | 0/70 | 0.0% | 0.56 | 1.175 |
| M-SHOOT-012 TS% (k=0.44) | 70/70 | 100.0% | 0.025 | 0.049 |
| M-IMP-044 Game Score (team) | 70/70 | 100.0% | 0.0 | 0.0 |
| M-SHOOT-004 FG% (published at 1 dp or whole number) | 70/70 | 100.0% | 0.003 | 0.057 |
| M-SHOOT-007 2P% | 70/70 | 100.0% | 0.025 | 0.049 |
| M-SHOOT-010 3P% (published at 1 dp or whole number) | 70/70 | 100.0% | 0.003 | 0.043 |
| M-TEFF-010 pace from published possessions (two-team mean per 40) | 70/70 | 100.0% | 0.002 | 0.044 |
| M-SHOOT-005/006 2PM, 2PA = FG - 3P | 70/70 | 100.0% | 0.0 | 0 |
| Team rebounds identity ORB + DRB = TRB | 70/70 | 100.0% | 0.0 | 0 |
| Points identity 2*2PM + 3*3PM + FTM = PTS | 70/70 | 100.0% | 0.0 | 0 |
| M-SHOOT-011 eFG% (player) | 338/338 | 100.0% | 0.012 | 0.05 |
| M-SHOOT-012 TS% (player, k=0.44) | 340/340 | 100.0% | 0.016 | 0.05 |
| M-TEFF-031 FTA rate (player) | 338/338 | 100.0% | 0.008 | 0.046 |
| M-REB-010 ORB% (player, Oliver) | 121/307 | 39.4% | 20.018 | 96.951 |
| CBBD player ORB% variant: ORB / own total rebounds | 307/307 | 100.0% | 0.007 | 0.05 |
| M-PROF-013 USG% (box, 0.44) | 305/305 | 100.0% | 0.025 | 0.05 |
| M-IMP-044 Game Score (player) | 396/396 | 100.0% | 0.0 | 0.0 |
| M-PASS-005 AST/TO | 210/210 | 100.0% | 0.004 | 0.05 |
| M-IMP-049 ORtg (Oliver, BR form), within 0.15 | 44/300 | 14.7% | 1.399 | 12.173 |
| M-IMP-049 ORtg (Oliver, BR form), within 2.0 | 238/300 | 79.3% | 1.399 | 12.173 |
| M-DEF-120 DRtg (Oliver, BR form) | 305/305 | 100.0% | 0.024 | 0.05 |
| M-SHOOT-003 FGA from PBP | 68/70 | 97.1% | 1.571 | 55 |
| M-SHOOT-002 FGM from PBP | 68/70 | 97.1% | 0.6 | 21 |
| M-SHOOT-009 3PA from PBP | 68/70 | 97.1% | 0.657 | 23 |
| M-SHOOT-008 3PM from PBP | 68/70 | 97.1% | 0.114 | 4 |
| FTA from PBP | 68/70 | 97.1% | 0.486 | 17 |
| FTM from PBP | 68/70 | 97.1% | 0.343 | 12 |
| Assists from PBP (assisted made FG) | 46/70 | 65.7% | 0.657 | 9 |
| ORB from PBP (incl. team) | 68/70 | 97.1% | 0.343 | 12 |
| DRB from PBP (incl. team) | 68/70 | 97.1% | 0.514 | 18 |
| Turnovers from PBP | 68/70 | 97.1% | 0.229 | 8 |
| M-TEFF-001 counted possessions vs CBBD possessions (|diff| <= 2) | 57/70 | 81.4% | 2.171 | 32 |
| M-TEFF-001 counted possessions vs CBBD possessions (exact) | 18/70 | 25.7% | 2.171 | 32 |
| M-TRN-016 points off turnovers (fold) vs official | 43/70 | 61.4% | 3.357 | 22 |

Tolerances: percentages and ratings ±0.05 (CBBD rounds to 1 dp), Oliver ratings ±0.15 (and ±2.0 shown separately), counts exact, possessions ±1 or ±2 as labelled.

## What it shows

- **Reproduced exactly (L4):** ORtg (M-TEFF-018), eFG% (M-SHOOT-011, team and player), FTA rate (M-TEFF-031), TOV% (M-TOV-006), pace (M-TEFF-010, from possessions), TS% with k = 0.44 (M-SHOOT-012), Game Score (M-IMP-044, exact to the decimal), FG%, 2P%, 3P% (M-SHOOT-004/007/010), usage (M-PROF-013), AST/TO (M-PASS-005), Oliver individual DRtg (M-DEF-120, 305/305), and the shot counts from play-by-play (M-SHOOT-002/003/008/009, 68/70).
- **CBBD uses different definitions in four places** (recorded on each metric; never map these CBBD fields to our IDs):
  - team `offensiveReboundPct` = ORB / own total rebounds (not Oliver's ORB / (ORB + opponent DRB));
  - player `offensiveReboundPct` = the player's ORB / his own total rebounds;
  - `trueShooting` uses k = 0.44 (NBA) where our default is 0.475 (college convention); both are registry variants;
  - `possessions` matches no standard estimator (best 24/70 exact), so CBBD possessions are an undocumented source definition (M-TEFF-004).
- **Close but not exact:** Oliver ORtg (M-IMP-049): 79% within 2 points, median difference 0.1; CBBD's exact variant is undocumented. Kept partial.
- **Source defect:** the UNC game (27 Nov 2025, CBBD game 210070) has play-by-play that credits every shot to one team; it causes all of the 2/70 play-by-play misses.
- **Play-by-play derived:** counted possessions vs CBBD possessions 81% within 2; points off turnovers vs the official box 61% within 2 (mean difference about 3 points; the official window rule needs confirming).

## Limit found in the state fold

The play-by-play state fold was tuned on 2 games. Across all 35 games it still runs, but logs more breaks, mostly lineup bookkeeping and missing dead-ball rows in CBBD (counts over 35 games):

- IV onFloor at an instant start differs from the substitution-row lineup: 469
- IV lineup not 5 players after a substitution group: 133
- IV shot by the team without the ball: 117
- IV single free throw before the bonus with no shot (technical not typed?): 79
- TRN-03 T22 during live play (dead ball missing from PBP): 63
- IV defensive rebound by the team with the ball: 51
- TRN-03 T12 from S2: 49
- IV offensive rebound by the team without the ball: 35
- TRN-03 T08 from S2: 17
- TRN-03 T06 from S2: 12

This affects only the play-by-play-derived checks (counted possessions, points off turnovers); the box-score reproductions do not use the fold.

## The 30 unit fixes

Old units are kept in `unit_before_2026_10_19`; formula changes are in `formula_fix_2026_10_19`; every fix has a dated note.

| Kind | Metrics | Fix |
| --- | --- | --- |
| Fraction stored as percent | M-MKT-041, M-MKT-110, M-TRN-027, M-TRN-028, M-TRN-040, M-TRN-067, M-PHYS-039, M-COACH-069, M-REB-061 | x100, unit percent, range 0-100 |
| Ratio that can exceed 100% | M-TRN-048 | x100, documented as able to exceed 100 |
| Milliseconds read as seconds | M-FOUL-101 | divide by 1000 |
| Minutes instead of seconds | M-MKT-120 | seconds, range 0 to 2400 + 300 per OT |
| cm listed, m computed | M-TRN-054 | unit m |
| Per possession vs per 100 | M-IMP-017 | points per 100 possessions |
| American cents vs probability | M-MKT-036 | de-vigged probability points |
| Percent used as a proportion in shrinkage | M-SHOOT-069 | p_rim as 0-1, result x100 |
| Adding incompatible units | M-FOUL-116 | sum of z-scores (or a fitted points model) |
| Publisher index, scale unpublished | M-MKT-106, M-MKT-108, M-MKT-109, M-SPACE-054, M-SPACE-055, M-SHOOT-064, M-SHOOT-018, M-PASS-017, M-PASS-020 | stored as published, never modelled on its scale |
| Bounded EvanMiya index, not a slope | M-TRAT-011, M-TRAT-012 | index ±99.01, reference only |
| Stat not found in any payload | M-SHOOT-067 | pending, not computed |
| Source file percentages wrong | M-COACH-085 | compute percentages from the counts |
