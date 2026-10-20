# Depth pass on the 1,115 previously confirmed stats (19 Oct 2026)

Aldemir: "Run a verification pass on the 1,115 confirmed stats that have no depth label yet, and push the box and play-by-play ones to L4."

Method: 10 verifier agents (one per category batch) re-opened sources, checked units, ranges and edge cases, gave each metric a depth label and an L4 recipe; 1 skeptic re-checked 60 labels at L2 or deeper and refuted 7 (those took the skeptic's depth and, if true, became partial). Separately, every MSU play-by-play counting stat was reproduced against the CBBD box. Registry version 0.4.0. No formula or unit was overwritten: fixes are in `formula_fix_2026_10_19`, unit problems in `unit_issue_2026_10_19`.

## Every stat now has a depth label

| Depth | All 1,591 stats | Box and play-by-play (768) |
| --- | --- | --- |
| L0 | 35 | 11 |
| L1 | 594 | 282 |
| L2 | 141 | 64 |
| L3 | 686 | 313 |
| L4 | 119 | 85 |
| L5 | 16 | 13 |

| Verified status | Count |
| --- | --- |
| partial | 637 |
| internal | 480 |
| true | 397 |
| reference_only | 63 |
| false | 14 |

## What changed for the 1,115

| Before → after | Count |
| --- | --- |
| true → partial | 482 |
| true → true | 338 |
| true → internal | 193 |
| internal → internal | 70 |
| true → reference_only | 22 |
| true → false | 10 |

The large move from true to partial is the honest result: most of these had been marked true from a definition seen once, without a second source or a worked example. Partial means the definition is confirmed but part of the formula (a coefficient, a window, a denominator) is our choice or unconfirmed; the note on each metric says which part.

## Play-by-play counting stats reproduced against the box (L4)

| Metric | Check | Result |
| --- | --- | --- |
| M-SHOOT-016 Points (PTS) | play-by-play rows vs CBBD box | Team points from PBP made shots vs box points.total: 68/68; Second-half points from PBP vs box byPeriod[1] (regulation games): 64/64 |
| M-SHOOT-030 Points distribution by source (share of points fro | play-by-play rows vs CBBD box | M-SHOOT-030 points split identity: 2P + 3P + FT points = PTS (shares sum to 1): 68/68 |
| M-PASS-001 Assists | play-by-play rows vs CBBD box | Player assists from PBP (assistedBy) vs box: 368/386 |
| M-TOV-001 Turnovers | play-by-play rows vs CBBD box | Player turnovers from PBP vs box: 386/386 |
| M-TOV-002 Team turnovers (not charged to a player) | play-by-play rows vs CBBD box | Team turnovers (no player) from PBP vs box turnovers.teamTotal: 68/68 |
| M-TOV-003 Steals | play-by-play rows vs CBBD box | Player steals from PBP vs box: 386/386; Team steals from PBP vs box steals: 68/68 |
| M-REB-001 Offensive rebounds (ORB) | play-by-play rows vs CBBD box | Player offensive rebounds from PBP vs box: 386/386 |
| M-REB-002 Defensive rebounds (DRB) | play-by-play rows vs CBBD box | Player defensive rebounds from PBP vs box: 386/386 |
| M-FOUL-001 Personal fouls committed | play-by-play rows vs CBBD box | Player fouls from PBP vs box: 386/386; Team fouls from PBP (personal + technical rows) vs box fouls.total: 67/68 |
| M-FOUL-038 Technical fouls (box total) | play-by-play rows vs CBBD box | Team technical fouls from PBP vs box fouls.technical: 68/68 |
| M-FOUL-063 Free throws made | play-by-play rows vs CBBD box | Player FTM from PBP vs box: 386/386 |
| M-FOUL-065 Free-throw percentage | play-by-play rows vs CBBD box | M-FOUL-065 FT% (player) from FTM/FTA vs box pct: 180/180; M-FOUL-065 FT% from FTM/FTA vs box pct (1 dp or whole number): 67/68 |
| M-DEF-019 Blocks | play-by-play rows vs CBBD box | Player blocks from PBP vs box: 386/386; Team blocks from PBP vs box blocks: 68/68 |

## Box and play-by-play stats not yet at L4, with a recipe

Count: 80.
The verifiers named a published value each of these can be reproduced against. They are the next L4 batch.

| ID | Name | Depth | Recipe |
| --- | --- | --- | --- |
| M-TEFF-001 | Possessions (counted, our definition) | L3 | Compare with CBBD team box possessions (prior run: 57/70 within 2, 18/70 exact). CBBD possessions are an undocumented definition, so this checks agreement only and does not count as L4. |
| M-TEFF-002 | Box-score possession estimate (single team) | L3 | CBBD team box: fieldGoals.attempted - rebounds.offensive + turnovers.total + 0.475*freeThrows.attempted vs possessions. Prior run: 36/70 within 1, so CBBD is undocumented and this is not a pass. Torvik ConPoss matches on |
| M-TEFF-040 | Individual offensive rating (Oliver points produced) | L3 | CBBD player box offensiveRating: prior run 44/300 within 0.15, 238/300 within 2 (median diff 0.1). CBBD's variant is undocumented. |
| M-TEFF-049 | Possession outcome distribution (share of possessions scorin | L3 | Identity sum(possessions.points) = CBBD points.total (needs the counted possession table; not yet run). |
| M-TRAT-002 | Rating rank, percentile and z-score (any system, any compone | L3 | KenPom 2026 adj_em/adj_oe/adj_de and Torvik adjoe/adjde: rank all teams with each tie method and compare to the published rank columns in the private copies (exact match expected for competition rank). |
| M-TRAT-004 | MSU Alpha opponent-adjusted team rating (our replica, dissec | L3 | Compare AdjOE/AdjDE/AdjEM to KenPom 2026 adj_oe/adj_de/adj_em and Torvik adjoe/adjde (RMSE/correlation tolerance, not exact, because the methods differ); inputs are CBBD team box points.total + possessions for both teams |
| M-TRAT-009 | Elo rating, expected score and update | L1 | CBBD games Elo start/end: for each game, take the home/away startElo plus the result and margin, then fit or test K, h and M so the update reproduces the published endElo (exact delta check per game). |
| M-TRAT-030 | Non-conference strength of schedule | L1 | KenPom 2026 ncsos_adj_em and Torvik ncsos: average the opponent ratings over CBBD games with conferenceGame = false (regular season) and compare. This matches only if their definition is mean opponent rating, which was n |
| M-TRAT-042 | Performance against quality opponents (Q-Rank, quality-games | L0 | Torvik 2026 Qual Games (count of games vs the venue-adjusted top 50) is reproducible exactly from CBBD games plus Torvik ranks; Qual O/Qual D/Qual Barthag can then be compared after running T-Rank adjustment on that subs |
| M-TRAT-043 | Won-lost record and winning percentage | L3 | Torvik 2026 record and KenPom 2026 w_l: count wins and losses from CBBD games points per team (status final) and compare exactly; conference record vs Torvik Conf Win%. |
| M-TRAT-044 | Record splits (home, away, neutral, close games, overtime, l | L3 | Conference split: Torvik Conf Win% from CBBD games with conferenceGame = true. Home/away/neutral splits have no published value in the list. |
| M-TRAT-049 | Luck (actual minus expected wins) | L1 | KenPom 2026 luck: compute actual win% from w_l minus expected win% from game-by-game efficiencies (CBBD team box rating and possessions for both teams). This is approximate, because the correlated-gaussian details are un |
| M-TRAT-069 | Conference regular-season championship (outright or shared)  | L3 | conf_pct vs Torvik 2026 Conf Win% (from CBBD games with conferenceGame = true and the regular-season gameType). |
| M-SHOOT-001 | Shot attempt outcome (event atom) | L3 | CBBD PBP: sum scoreValue over scoringPlay rows per team and per shooter; compare to CBBD team box points.total and player box points (exact). |
| M-SHOOT-013 | True shooting attempts (TSA) | L3 | CBBD team box trueShooting and player box trueShootingPct: compute PTS/(2*(FGA + k*FTA)) with k = 0.44 and k = 0.475 and see which reproduces the CBBD value (fixes the coefficient CBBD uses). |
| M-SHOOT-017 | Scoring rate per 100 possessions | L1 | Team-level version: 100*points.total/possessions vs CBBD team box rating (exact). Player on-floor version: CBBD PBP onFloor + possessions; no published value. |
| M-SHOOT-024 | Rim field-goal percentage | L1 | Diagnostic only: CBBD PBP shotInfo.range = 'rim' made/attempted (CBBD's own classification, not 4 ft); no published rim FG% in the list. |
| M-SHOOT-025 | Mid-range field-goal percentage | L1 | CBBD PBP shotInfo.range = 'jumper' (two-point) made/attempted as a diagnostic; identity: rim + mid + 3PA = CBBD team box fieldGoals.attempted. |
| M-SHOOT-027 | Shooting accuracy and frequency by zone (zone splits) | L1 | Identity check: the sum over zones of FGA equals CBBD team box fieldGoals.attempted, and 3-zones equal threePointFieldGoals.attempted (exact). CBBD PBP shotInfo.range gives an alternative partition. |
| M-SHOOT-031 | Unassisted share of made field goals | L1 | CBBD PBP: count made FG with shotInfo.assisted = true per team and compare to CBBD team box assists (published; should match), then %UAST = 100*(1 - assisted/FGM) with FGM vs fieldGoals.made. |
| M-SHOOT-047 | Own shots blocked (blocked attempt rate) | L3 | CBBD PBP: count each team's shots joined to block events and compare to the opponent's CBBD team box blocks (published); player BLKA has no published value. |
| M-SHOOT-056 | Field-goal part of points produced (PProd_FG_Part, FG_Part) | L1 | CBBD player box offensiveRating: compute the full Oliver ORtg (BR ratings page) from player and team box fields (minutes, points, FG/3P/FT made/attempted, assists, turnovers, ORB, team totals) and compare. This is an ind |
| M-SHOOT-057 | Field-goal-ended possessions (FGxPoss) | L1 | Indirect via CBBD player box offensiveRating (full Oliver ORtg reproduction), with Team_ORB% from team ORB and opponent defensive rebounds. |
| M-SHOOT-062 | End-of-period heaves and heave-adjusted shooting | L1 | Identity: heave FGA + non-heave FGA = CBBD team box fieldGoals.attempted, from CBBD PBP location x/y + secondsRemaining. |
| M-SQ-010 | Three-point attempt rate | L3 | CBBD team box: threePointFieldGoals.attempted / fieldGoals.attempted per game; reproduce both from CBBD PBP (count shotInfo.range='three_pointer' and all non-FT shots) and compare with the box |
| M-SQ-023 | Shot creation: assisted and unassisted share by zone | L2 | CBBD PBP: sum shotInfo.assisted over made FG per team vs CBBD team box assists (assisted makes should equal team assists); per zone uses shotInfo.range |
| M-SQ-024 | Points in the paint | L3 | CBBD PBP: sum scoreValue of made FG whose shotInfo.location lies inside the paint rectangle vs CBBD team box points.inPaint. The earlier proxy (2 x made 'rim' shots) matched only 26/68 games within 4, so L4 is not reache |
| M-SQ-026 | Blocked-shot rate (offense) | L2 | CBBD team box: opponent blocks / own fieldGoals.attempted; reproduce the blocks count from CBBD PBP block plays vs the box blocks |
| M-SQ-040 | FG% by zone | L3 | CBBD PBP made/attempted with shotInfo.range='three_pointer' vs team box threePointFieldGoals.pct; rim + jumper (scoreValue 2) vs twoPointFieldGoals.pct |
| M-SQ-041 | FG% by shot type | L3 | CBBD PBP playType counts give the per-type FG%; the sum over the 2P types should equal box twoPointFieldGoals made/attempted less untracked types (no published per-type value in the listed fields) |
| M-PASS-001 | Assists | L3 | CBBD player box assists vs count of PBP shotInfo.assistedBy.id = player on made FG: 368/386 exact (95.3%). Team: PBP assisted made FG vs teamStats.assists 46/68 exact, 61/68 within 1 (CBBD PBP under-flags assists by abou |
| M-PASS-009 | Points off assisted vs unassisted makes | L3 | CBBD PBP: pts_ast + pts_unast (FG) + made FT points = teamStats/opponentStats points.total, 68/68 team-games |
| M-PASS-010 | qAST (expected share of a player's makes assisted) | L3 | CBBD player box offensiveRating through the full Oliver ORtg (component check only) |
| M-PASS-011 | Assist part of scoring possessions and points produced (Oliv | L3 | CBBD player box offensiveRating (component; replica 79% within 2) |
| M-TOV-021 | Opponent points off turnovers | L2 | CBBD offensive team's points.offTurnovers (the opponent row for OppPOT). PBP rule: after each turnover, sum the other team's scoring until its possession ends (defensive rebound by the turnover team, a turnover by the sc |
| M-REB-022 | Offensive-rebound scoring-possession credit (Oliver ORB_Part | L3 | CBBD player box offensiveRating (component only) |
| M-FOUL-048 | Ejections | L3 | CBBD player box ejected (no positive case in MSU 2025-26: 0/396 rows true), so not testable |
| M-FOUL-095 | Expected points conceded by fouling (hack cost) | L3 | PPP_offence = CBBD rating/100 (points/possessions reproduced 70/70 as M-TEFF-018); EP_hack none |
| M-DEF-002 | Defensive points per possession (raw, un-adjusted) | L3 | Team: CBBD opponent row 'rating' (opponent ORtg = our DRtg) on CBBD possessions; season: Torvik ConDE vs ConPA/ConPoss; the PBP possession count vs CBBD possessions. |
| M-DEF-009 | Opponent rim attempt rate allowed | L3 | CBBD play-by-play shotInfo.range = 'rim' counts for opponent shots vs our shot_type_code rim set (agreement check only; CBBD 'rim' is not the paint). |
| M-DEF-010 | Opponent rim field-goal percentage allowed (team) | L3 | CBBD play-by-play shotInfo.range = 'rim' with shotInfo.made for opponent shots (classification agreement). |
| M-DEF-011 | Opponent mid-range attempt rate and FG% allowed | L3 | CBBD play-by-play shotInfo.range = 'jumper' for opponent shots (classification agreement). |
| M-DEF-013 | Opponent assist rate (assisted share of opponent makes) | L3 | CBBD play-by-play shotInfo.assisted on opponent made FG vs the opponent box assists (numerator), then the ratio over fieldGoals.made. |
| M-DEF-014 | Opponent points in the paint | L1 | CBBD team box opponent row points.inPaint (passthrough); a recompute needs shotInfo.location x/y inside the lane. |
| M-TRN-013 | Fast-break points (official box) | L3 | CBBD team box points.fastBreak (passthrough); per 100 via CBBD possessions |
| M-TRN-014 | Share of points from fast breaks | L3 | CBBD team box points.fastBreak / points.total (both published; the ratio itself is not) |
| M-TRN-015 | Fast-break definition agreement (official vs ours) | L3 | CBBD points.fastBreak vs our flagged points (the metric is the gap itself) |
| M-TRN-016 | Points off turnovers | L3 | CBBD team box points.offTurnovers vs the PBP fold over possessions starting with a turnover |
| M-TRN-017 | Share of points off turnovers | L1 | CBBD points.offTurnovers / points.total |
| M-PHYS-006 | Minutes played and games (official) | L3 | CBBD player box minutes summed per team-game vs 5 x game length, game length = 40 + 5 x (number of CBBD team box points.byPeriod entries - 2); tolerance +/- 2 min |
| M-PHYS-008 | Stint length (mean, longest continuous) | L3 | CBBD play-by-play onFloor + period + secondsRemaining: sum of stint_s per player-game / 60 vs CBBD player box minutes, tolerance +/- 1 min |
| M-PHYS-009 | Continuous minutes on court at an instant (fatigue clock) | L3 | CBBD play-by-play onFloor/secondsRemaining/period: cont_s at each exit summed per player-game / 60 vs CBBD player box minutes |
| M-IMP-001 | Raw plus-minus (on-court point differential) | L3 | CBBD play-by-play: sum homeScore/awayScore deltas over plays with the player in onFloor; property check sum_p PM_p = 5 x (points.total - opp points.total) from CBBD team box. No published player +/- in the open list, so  |
| M-IMP-002 | On-court team ratings (offensive, defensive, net rating with | L2 | CBBD play-by-play onFloor + scoreValue with the CBBD lineup possession rule; for a player on floor all game ORtg_on must equal CBBD team box rating; possession-weighted team aggregate vs CBBD team box rating/possessions  |
| M-IMP-003 | On/off differential (net, offense, defense) | L1 | CBBD play-by-play onFloor; identity: on and off possession-weighted ratings recombine to CBBD team box rating for the same games. |
| M-IMP-007 | With-or-without-you (WOWY) splits | L1 | CBBD play-by-play onFloor; identity: possession-weighted mean over all patterns equals CBBD team box rating. |
| M-IMP-008 | Lineup stint (base unit) and 10-player matchup stint | L2 | CBBD play-by-play onFloor + secondsRemaining: sum of stint durations per team = 2400 + 300 x OT; sum of stint points_for = CBBD team box points.total; sum of stint possessions vs CBBD team box possessions (tolerance). |
| M-IMP-009 | Lineup plus-minus | L3 | CBBD play-by-play; identity: sum over all 5-man stints of LPM = team margin from CBBD team box points.total. |
| M-IMP-010 | Lineup raw efficiency (offensive, defensive, net) for k-man  | L2 | CBBD play-by-play onFloor with CBBD lineup possession rule; all-stint aggregate reproduces CBBD team box rating within possession tolerance. |
| M-IMP-015 | Starters vs bench unit split | L2 | CBBD play-by-play onFloor; identity: possessions over k=0..5 sum to team possessions and recombined net equals CBBD team box rating minus opponent rating. |
| M-IMP-027 | Player game NET points (our BPM-to-points distribution; Torv | L3 | Property check: sum_p NET_p = team game margin from CBBD team box points.total (both teams). No published NET in the open list. |
| M-IMP-048 | Points produced and individual possessions (Oliver) | L3 | CBBD player box offensiveRating: apply the CBBD variant to CBBD player box + team box (+ opponent rebounds) inputs and reproduce offensiveRating within 0.1 for players with minutes >= 8. |
| M-IMP-062 | Player win probability added (WPA) and leverage-neutral wins | L2 | CBBD play-by-play homeWinProbability: event deltas credited via shotInfo.shooter/participants; identity sum of all event deltas in a game = final outcome (1/0) - opening homeWinProbability. |
| M-PROF-001 | Games played (GP) | L3 | CBBD player box minutes > 0 per game vs CBBD play-by-play onFloor presence (R-DQ-01 cross-check); no published GP field in the open list. |
| M-PROF-004 | Minutes played (MP) and minutes per game | L3 | CBBD player box minutes: team sum = 5 x (40 + 5 x OT) per game; stint-sum variant from CBBD play-by-play onFloor + secondsRemaining reproduces CBBD player box minutes within ~1 min. |
| M-PROF-005 | Minutes share (Min%, percentage of possible minutes) | L1 | Property: team Min% sums to ~500 using CBBD player box minutes; no published Min% in open list. |
| M-PROF-006 | On-court possessions played | L3 | Sum over players of Poss_off = 5 x team possessions; compare with CBBD team box possessions (tolerance for definition difference). |
| M-PROF-010 | Season counting totals | L3 | Sum CBBD player box points (and assists, steals, blocks, turnovers, rebounds) over a team's players = CBBD team box points.total etc. per game. |
| M-PROF-035 | Shots-at-rim rate | L1 | CBBD play-by-play shotInfo.range = rim count over non-FT shots; denominator count must reproduce CBBD player box fieldGoals.attempted. |
| M-PROF-050 | Stint profile (stint length, longest stint, rest between sti | L3 | CBBD play-by-play onFloor + secondsRemaining: sum of stint lengths / 60 must match CBBD player box minutes. |
| M-PROF-055 | Game-to-game consistency (Game Score spread, floor and ceili | L1 | CBBD player box gameScore: compute GmSc from CBBD player box points, fieldGoals made/attempted, freeThrows, rebounds offensive/defensive, steals, assists, blocks, fouls, turnovers and match gameScore per game. |
| M-PROF-081 | Prior-level physicality | L3 | FTr_allowed = opponent CBBD team box fourFactors.freeThrowRate (FTA/FGA); foul rate from CBBD team box fouls.total and possessions; ORB% not directly reproducible from CBBD four-factor field (different denominator). |
| M-PROF-088 | Points responsible for (PRF, total scoring involvement) | L1 | PTS = CBBD player box points; AST_PTS from CBBD play-by-play shotInfo.assistedBy and scoreValue; count of assisted makes by passer must reproduce CBBD player box assists. |
| M-SIT-001 | Game clock state and time remaining | L3 | CBBD PBP period/secondsRemaining gives max elapsed = CBBD games gameMinutes*60: 33/33 games (run this pass). |
| M-SIT-077 | FUN (record minus expected record; luck) | L1 | Store Torvik FUN (and KenPom luck) as published; not reproducible. |
| M-SIT-079 | Home, away and neutral record and splits | L1 | Partial: CBBD games isHome/neutralSite W split must sum to the Torvik record (already matched in total); no published split in the open list. |
| M-MKT-099 | Spread prediction MAE | L3 | actual margin from CBBD games points |
| M-MKT-100 | Spread prediction RMSE | L3 | actual margin from CBBD games points |
| M-MKT-101 | Variance explained (margin predictions) | L2 | actual margin from CBBD games |
| M-MKT-102 | Home bias of predictions | L1 | CBBD games neutralSite filter |

## Box and play-by-play stats with no published value to reproduce against

590 metrics. These stop at L3 until a source publishes them or a hand-labelled sample exists (gold-v1 for anything needing video). Their recipe field says "none" with the reason.

## Not confirmed (false)

| ID | Name | Issue |
| --- | --- | --- |
| M-FOUL-102 | Free-throw command | Registry formula puts the 1 inside the square root (1/sqrt(1+mu^2+sigma^2)); source has 1 + sqrt(mu^2+sigma^2). Contradicted, so downgraded. |
| M-SIT-038 | Timeout type, context and timing | Not confirmed this session: the rule reference was not reopened and the Benz PDF could not be read. The taxonomy is plausible but unverified. |
| M-SIT-089 | Coarsened possession state | The state definition (7 regions x defended) was not confirmed this session. |
| M-SPACE-034 | Defensive attention drawn on-ball | Only abstract opened; matchup-probability basis not confirmed. Re-open full text. |
| M-SPACE-035 | Defensive attention drawn off-ball | Not confirmed by opened page. |
| M-PHYS-057 | Lateral accelerations | PlayerData source failed to open (SSL error); not re-confirmed. Maths of projection sound. |
| M-PHYS-096 | Offensive player acceleration field | Not confirmed by opened page. |
| M-TOV-039 | P&R ball-handler turnover rate incl. passing | Downgraded: the cited page does not show the formula. Re-source or reclassify as internal. |
| M-TRAT-027 | Team- and site-specific home-court advantage | The KenPom HCA part two page (archive) could not be opened, and the EvanMiya page gives no formula. Neither component was confirmed this session, so this is downgraded from confirmed. |
| M-TRAT-042 | Performance against quality opponents (Q-Rank, quality-games | The definition was not re-confirmed this session (the H-Rank and Qual text was not in the read portion), so this is downgraded. A Torvik L4 path exists. |

## Skeptic refutations (7 of 60 sampled)

| ID | Honest depth | Reason |
| --- | --- | --- |
| M-MKT-093 | L1 | Guo et al. arXiv 1706.04599 (opened, text extracted) gives Platt q=sigma(a z + b) and temperature scaling q=max softmax(z/T), with no bias term, so the formula matches. But it is the only source and no worked example is cited, so it does not meet L2 (two indep |
| M-SIT-001 | L3 | ncaahoopR average_win_prob.R (opened) shows only play_length weighting normalised by max(secs_remaining_absolute) and filter(!wrong_time). It does not show our elapsed_s or game_seconds_left formula, and no published value is reproduced. CBBD secondsRemaining  |
| M-TOV-021 | L2 | NBA glossary (opened): OPP PTS OFF TO = 'points scored by an opposing player or team following a turnover'. hoopR load_ncaa_mbb (opened): is_from_turnover = 'Whether the possession began off a turnover'. The definition is supported, but L4 is not: our formula  |
| M-DEF-014 | L1 | The cited NCAA Statisticians' Manual (opened via curl, 2025-26 edition, 15 pages, text-searched) contains no 'paint' definition at all, so the 'in or over the plane of the paint' support cannot be confirmed there. NBA glossary (opened) gives only 'points score |
| M-TRN-017 | L1 | NBA glossary (opened): %PTS OFF TO = 'percentage of points scored ... on the possession after forcing an opponent turnover', which matches PTS_offTO/PTS. The NCAA Statisticians' Manual (opened, text-searched) has no points-off-turnovers definition, so the seco |
| M-PASS-001 | L3 | NBA glossary (opened): assists are passes that lead directly to a made basket. Sports-Reference (opened): AST = Assists. The primary formula counts assisted made shots from PBP, and that does not reproduce: my count of CBBD made FG with a second participant vs |
| M-PASS-009 | L3 | sportsdataverse mbb_ncaa_stats_agg.py (opened): pts_ast = sum(made*sv*ast) and pts_unast = sum(made*sv*una), with no FG filter, so made FTs fall into pts_unast. This matches our primary form and the sdv variant. No publisher value for assisted or unassisted po |

## Proposed formula fixes (11, need approval)

| ID | Name | Proposed |
| --- | --- | --- |
| M-FOUL-053 | Block/charge restricted-area status | ra_dist_m = signed min distance from defender foot points to the RA boundary = outer edge of the arc line (semicircle r = 1.2192 + 0.0508 = 1.2700 m from basket centre, straight segments to the backboard face); inside if any foot point is within or on the boun |
| M-FOUL-102 | Free-throw command | C = 1 / (1 + sqrt((mu_m / s)^2 + (sigma_m / s)^2)), s = command_length_unit (registry, default 0.0254 m) |
| M-MKT-031 | Teaser-adjusted line | teased line_team = line_team + t for both sides (signed line, negative = favourite): favourite -3.5 + 6 = +2.5, dog +3.5 + 6 = +9.5 |
| M-SIT-052 | Garbage-time flag (three side-by-side definitions) and share | GT_ctg = per-possession condition (period = 2 and (/m/ >= 25 and 540 < clock <= 720 or /m/ >= 20 and 360 < clock <= 540 or /m/ >= 10 and clock <= 360) and starters_on_combined <= 2), without cummax (CTG resets when the conditions fail) |
| M-SPACE-028 | Run (cut) timing value | V_frame = mean wUPPCF over the receiver's simultaneous-arrival region (or label OBSO variant as MSU); xi>0 inserts bridging segment at mean velocity of the preceding 1 s |
| M-PHYS-078 | PlayerLoad and accelerometer load family (wearable) | PL = sum_t sqrt(((da_x)^2 + (da_y)^2 + (da_z)^2) / 100) |
| M-DEF-037 | Proximal FG% and shot proximity shares | PFG% = 100 * FGM_prox / FGA_prox with prox = dist(d, shooter) <= 1.524 m at release (source); other radii flagged as project extensions |
| M-DEF-069 | Defensive versatility index | DVI = 100 * H, H = -sum_{pos in PG,SG,SF,PF,C} p_pos ln p_pos (source); keep the 3-class normalised variant as a project extension |
| M-REB-038 | Long-rebound share | LONG_SHARE = 100 * count(loc_r_m >= 3.048) / count(rebounds) (Opta 10 ft); keep 6.0 m only as a named variant |
| M-SHOOT-032 | Catch-and-shoot shooting (FG%, points) | cs = shot_type is jump shot AND release_r_m > 3.048 AND dribbles_before = 0 AND touch_time_before_s <= 2.0 |
| M-SHOOT-033 | Pull-up shooting (FG%, points) | pu = shot_type is jump shot AND release_r_m > 3.048 AND dribbles_before >= 1 |

## Unit or range issues flagged (108, not yet fixed)

| ID | Name | Issue |
| --- | --- | --- |
| M-FOUL-045 | Foul class mix | formula gives a share 0-1 but unit says percent: use 100 * count_c / count_all |
| M-FOUL-046 | Fouls by contact mechanism | share_m has no x100 while unit is count; store share_m = 100 * count_m / fouls as percent |
| M-FOUL-090 | Free-throw percentage by attempt position | formula made/attempts is 0-1; multiply by 100 to match percent |
| M-FOUL-133 | Calls by official role and court area | multiply by 100 (formula gives 0-1, unit percent) |
| M-FOUL-145 | Call precision | use 100 * CC / (CC + IC) for percent, or set unit probability 0-1 |
| M-FOUL-146 | Call recall | use 100 * CC / (CC + INC) or unit probability 0-1 |
| M-MKT-005 | Booksum (sum of implied probabilities) | value_range should be > 0, normally ~1.00-1.25 (above 1 for a book, below 1 only for arbitrage/stale quotes); '0-1' is wrong |
| M-MKT-009 | Accumulator (parlay) overround | value_range must allow > 100% (fourfold example 107.36%); use >= 0, unbounded above |
| M-MKT-020 | Favourite-longshot correction gap | signed difference: range -1..1 (practically about -0.02..0.02), not 0-1 |
| M-MKT-034 | Fair probability movement | signed probability points: range -1..1 |
| M-MKT-067 | Edge (model minus market fair probability) | signed: -1..1 |
| M-MKT-070 | Closing-line value (probability points) | signed: -1..1 |
| M-MKT-071 | CLV percent (EV at closing fair probability) | signed percent |
| M-MKT-072 | CLV relative percent | signed percent |
| M-MKT-078 | Betting units gained, return on investment (yield) | ROI signed, -100%.. |
| M-MKT-101 | Variance explained (margin predictions) | can be negative |
| M-MKT-116 | Live (in-game) spread, total and team-total lines | points, not 0-1 |
| M-MKT-130 | Posted bet limit (maximum stake) at snapshot | currency of account |
| M-TEFF-004 | Possession-count discrepancy by source definition | rel_diff is signed percent; range should be unbounded signed (typically -10..+10), not 0-100 |
| M-TEFF-008 | Possession balance (team minus opponent possessions) | Range is signed (typically -2..+2 per game), not >= 0 |
| M-TEFF-009 | Shot-volume (extra chances) margin | Margins are signed; range should be unbounded signed |
| M-TEFF-012 | Time on offense and time on defense | share_off = T_off/(T_off+T_def) is 0-1; multiply by 100 for percent |
| M-TEFF-021 | Points per possession by possession start type | 0-100 applies to share_s only; PPP_s is 0 to ~1.5 points per possession |
| M-TEFF-025 | Efficiency over expectation | EOE is signed; range unbounded signed (typically -20..+20) |
| M-TEFF-034 | Four-factor offensive-rating identity and Shapley decomposit | Shapley contributions are signed; range should be signed, not >= 0 |
| M-TEFF-045 | Usable-possession share | count/Poss is 0-1; multiply by 100 for percent |
| M-SIT-003 | Score-state splits (ahead / tied / behind by margin bucket) | ORtg_b is per 100 (0-~200), not 0-100; Delta_b is signed |
| M-SIT-007 | Clutch team efficiency (clutch ORtg, DRtg, net rating, four  | Net is signed |
| M-SIT-009 | Pressure performance (contest, shot clock, clutch slices) | delta is signed |
| M-SIT-032 | Gibbs run (9-point swing in 120 s): run point total, duratio | s(t) and SSD are signed; only r(t) and duration are >= 0 |
| M-SIT-036 | Momentum (net score rate) and momentum trigger | M_w is signed points per second |
| M-SIT-040 | Timeout effect on an opponent run (matched causal estimate) | ATT is signed |
| M-SIT-041 | Post-stoppage and start-of-half efficiency | delta and HT_adj are signed |
| M-SIT-046 | Shot-clock utilisation | U is a 0-1 ratio; x100 for percent |
| M-SIT-058 | Win probability added (WPA) per event, player and team | WPA_e is in [-1, 1]; player and team sums are signed |
| M-SIT-066 | Shift win probability added | y_i in [-1, 1] |
| M-SIT-068 | Game excitement index | GEI is not bounded by 1; range >= 0 (typically 2-15) |
| M-SIT-077 | FUN (record minus expected record; luck) | FUN is signed (-100..100 in percent) |
| M-SIT-081 | Streak and previous-game result | streak and prev_margin are signed |
| M-SIT-083 | Venue geography: altitude difference and neutral-site proxim | alt_diff and d_diff are signed metres / km |
| M-SIT-088 | Within-game intensity decline (late vs early) | decline is a signed ratio; x100 for percent, range signed |
| M-SIT-092 | Rest and schedule-load differential (rest advantage) | Diffs are signed |
| M-SIT-093 | Revenge spot (lost the previous meeting) | prev_margin is signed |
| M-PHYS-003 | Tracking coverage share for load (observed on-court time) | observed_pct = 100 * observed_frac |
| M-PHYS-004 | Kinematic resolvable share | resolvable_pct = 100 * resolvable_share |
| M-PHYS-006 | Minutes played and games (official) | minutes_share_pct = 100 * sum(minutes) / sum(game_minutes) |
| M-COACH-004 | Called timeout absorbed into a media timeout | share = 100 * sum(absorbed)/team timeouts |
| M-COACH-006 | Timeout purpose mix | share_p = 100*count/total |
| M-COACH-009 | Icing timeout rate and free-throw outcome after icing | icing_rate = 100*sum/eligible |
| M-COACH-012 | Share of timeouts called during an opponent run | multiply by 100 |
| M-COACH-020 | Pre/post timeout net score differential (naive) and score di | value_range: SDI and naive are signed (unbounded); only STO_pg >= 0 |
| M-COACH-022 | Timeout value in win probability | range -1..1 (signed WP delta), not 0-1 |
| M-COACH-024 | Timeout-during-run causal effect (matched ATT on integrated  | range is signed (unbounded), not >= 0 |
| M-COACH-025 | Media-timeout interruption effect on the running team (natur | range is not 0-100 |
| M-COACH-027 | Momentum change around a timeout and pre-timeout team state | range is signed, not >= 0 |
| M-COACH-028 | Run-halting timeout (first opponent possession) | rate = 100*mean(halt) |
| M-COACH-029 | Crunch-time half-court FG% after timeout vs no timeout | dFG% = 100*(FGM/FGA after - FGM/FGA none); range -100..100 |
| M-COACH-032 | Challenge success rate (overall and by call type) | CH_success = 100*overturned/(overturned+stands) |
| M-COACH-037 | Substitutions per game and substitution timing | multi_share as percent: x100 |
| M-COACH-041 | Bench minutes share | x100 |
| M-COACH-042 | Bench points and bench points share | bench_pts% x100 |
| M-COACH-046 | Player pull rate after a mistake (vs substitution hazard bas | x100; signed difference vs baseline |
| M-COACH-050 | Foul-trouble benching rate and two-foul first-half participa | rates x100 |
| M-COACH-051 | Foul-trouble option value vs current value (bench now vs kee | signed WP difference range -1..1 |
| M-COACH-055 | Two-for-one attempt rate and execution | TFO_rate x100 |
| M-COACH-057 | End-of-period last-possession share and extra possessions | share x100 |
| M-COACH-060 | Foul-up-3 decision, rate and outcome | win% = 100*(W+0.5*OT)/cases |
| M-COACH-062 | Foul-to-extend when trailing: rate, time-to-foul and optimal | foul_rate x100 |
| M-COACH-065 | End-game policy rates per decision cell | x100 |
| M-COACH-076 | Zone recognition lag (offense) | dPPP range signed |
| M-COACH-077 | Half-time adjustment | range is signed, not 0-100 |
| M-COACH-078 | Reaction catalogue latency and rate | signed range |
| M-COACH-082 | Coach rating prior (BPI / T-Rank coach effect) and coaching- | coach effect range signed |
| M-COACH-087 | Over/under-achievement vs roster talent | resid is signed, not >= 0 |
| M-COACH-088 | Expected transfer improvement (school development effect) | signed range |
| M-COACH-091 | Head-coach overall win-loss record (career, current school,  | W-L% = 100*W/(W+L) (SR prints a 0-1 fraction) |
| M-DEF-067 | Defender shot-efficiency effect | D_n in metres (feet x 0.3048); xi_m = xi_ft / 0.3048; cap at about 1.83 m |
| M-DEF-112 | Press usage and outcome | units: percent (press_rate, TO% = 100 * TO / press possessions); points per possession; drop 's' |
| M-DEF-119 | Stop percentage | The formula gives a fraction 0-1 (used as such inside DRtg); multiply by 100 for percent display |
| M-IMP-045 | Player Impact Estimate (PIE) | Formula yields a fraction; multiply by 100 to store as percent. |
| M-IMP-056 | PORPAGATU! (PRPG!, PORPAG at that usage) | Min_per must enter as a fraction 0-1 (or divide by an extra 100): with Min% = 80 the formula gives ~220 points per game, with 0.80 it gives ~2-6, matching published PRPG scale. |
| M-PROF-014 | CTG usage (free-throw trips, assist-adjusted) | Formula yields a fraction; multiply by 100 for percent. |
| M-PROF-016 | Share of team production while on court (%FGA, %3PA, %PTS, % | Multiply by 100 for percent. |
| M-PROF-045 | Lineup composition descriptors | Heights in metres (listed_height_cm / 100), per project unit rule. |
| M-PROF-065 | Returning minutes (team, preseason) | Formula yields a fraction (team_minutes = total player-minutes); multiply by 100 for percent. |
| M-PROF-080 | Hometown distance (to campus and to venue) | Project rule says metres; store metres (km x 1000) or register km as an allowed distance unit. |
| M-PASS-037 | Passes per chance and ball reversals | count (no seconds term in the formula) |
| M-PASS-043 | Pass option values and pass hazards (EPV macrotransitions) | hazards in 1/s (>= 0, unbounded); probabilities 0-1; values in expected points |
| M-REB-017 | Projected rebounding (EvanMiya) | store EvanMiya's published value as-is with as-of date; unit unknown |
| M-REB-026 | Second-chance possessions and seconds | SC_N in count; SC_SEC in s |
| M-SQ-001 | Shot release location (x, y, r, theta) | value_range per component: x,y signed m; r >= 0 m; theta degrees |
| M-SQ-047 | Spatial shooting effectiveness and Range% | SSE: signed points per shot, unbounded; Range%: percent 0-100 |
| M-SQ-055 | Defender closing speed | value_range: signed m/s |
| M-SQ-063 | Average shot quality (mean xPts or xeFG per FGA) | split value_range: avg_xPts 0-3; xeFG 0-100 percent |
| M-SQ-066 | Shot-making residual (points above expected) | value_range: signed, unbounded |
| M-SQ-070 | Shot satisfaction (SATIS) | value_range: signed |
| M-SQ-073 | Player LPL contribution (PLC) | value_range: signed, unbounded |
| M-SQ-080 | Shooter speed and heading at gather | heading_rel: -180..180 deg |
| M-SQ-081 | Shooter facing and release timing | facing: -180..180 deg |
| M-PLAY-039 | Half-court play efficiency and share | unit: points per 100 half-court possessions (or switch the count to chances to match CTG plays) |
| M-PLAY-044 | Screen pairwise-distance features | f2,f4 signed m/s |
| M-PLAY-052 | Screener-handler timing | signed seconds |
| M-TRAT-014 | ESPN Basketball Power Index (BPI) and its offence/defence co | The 'per 70 possessions' unit and the BPI_100 = BPI*100/70 conversion are not stated on any ESPN page opened this session; ESPN says only 'points above/below average'. The unit is downgraded to unverified. Value range '> |
| M-TRAT-016 | Preseason team rating and projection | The EvanMiya projection blog was not opened this session. The BPI per-70 unit is unverified (see M-TRAT-014). Value range '>= 0' is wrong. |
| M-TRAT-021 | Roster experience and height (minutes-weighted) | store height in metres (inches x 0.0254), not centimetres |
| M-TRAT-049 | Luck (actual minus expected wins) | KenPom luck is a win-fraction difference (about -0.2..+0.2), not percent 0-100; store as fraction |
| M-TREE-013 | Run response tree | split range: stop_rate 0-1; net3 signed points |
| M-TREE-016 | Score-state behaviour tree | give ranges per output: seconds >= 0, percent 0-100, PPP signed |
