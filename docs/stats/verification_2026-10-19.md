# Stat verification pass, 19 Oct 2026

Aldemir: "focus on stats part verification, and 450 formulas and how depth can we go?". Scope: every metric in `config/metrics.yaml` whose formula was not confirmed (verified = false 340, partial 105, harvest_only 5). Method: 8 verifier agents (one per category batch) opened sources and checked each formula, then 1 skeptic tried to refute every promotion to `true`. Results merged into the registry (version 0.2.0); no formula was overwritten, corrections are in `formula_fix_2026_10_19`.

## How deep verification can go

| Level | Meaning | Reached now |
| --- | --- | --- |
| L0 | nothing confirmed | 21 |
| L1 | definition matches an opened authoritative source | 142 |
| L2 | formula confirmed by two independent sources or the publisher example | 23 |
| L3 | plus units, range and edge cases checked (or internal maths checked) | 232 |
| L4 | numeric reproduction of a published value from published inputs | 24 |
| L5 | property checks (identities, bounds) on a worked example | 8 |

What limits depth: box and play-by-play stats can reach L4 once we recompute them on CBBD data and compare with a published value (the next step, needs no new data). Tracking stats stop at L3 until tracking exists; then L4 means matching hand-labelled gold-v1. Proprietary ratings (KenPom, EvanMiya, Synergy) stop at reference_only: we store the published number.

## Outcome

| Before → after | Count |
| --- | --- |
| false → internal | 206 |
| false → partial | 84 |
| partial → partial | 65 |
| false → reference_only | 30 |
| partial → true | 18 |
| false → true | 16 |
| partial → reference_only | 11 |
| partial → internal | 11 |
| harvest_only → partial | 5 |
| false → false | 4 |

Promotions to true: 35; the skeptic refuted 1 (M-COACH-092), kept as partial. Formulas found wrong: 43 (24 with a proposed fix). Unit problems: 30.

## Proposed formula fixes (need approval before they replace the formula)

| ID | Name | Issue | Proposed formula |
| --- | --- | --- | --- |
| M-TEFF-011 | Adjusted tempo | The multiplicative replica is inferred: Torvik only says 'same basic process'. The registry's recency weights w(d) are listed as our parameters, but Torvik publishes his (40/80 days, 60% floor), so use those for a Torvik-style replica. KenPom's form is unknown, and Torvik says he does not know exact | Store the published AdjT. For the replica: Poss_g = mean(team, opp) of FGA-ORB+TOV+0.475*FTA; RawT_g = 40*Poss_g/(game_minutes); AdjT_g = RawT_g*(avgT/OppAdjT); AdjT = sum w_g*AdjT_g / sum w_g, where w_g = 1 for age<=40 d, 1-0.01*(age-40) for 40<age<=80, and 0.6 after (Torvik's published recency). I |
| M-TEFF-014 | Offense-versus-defense control share (tempo and four factors) | The registry formula b_O/(b_O+b_D) is wrong. KenPom explicitly measures the share of predicted-value variance contributed by each term, which differs from the coefficient ratio whenever offensive and defensive season values have different spreads. The registry also omits the site term. | Fit stat_game = a + alpha*off_season(O, excluding g) + beta*def_season(D, excluding g) + gamma*site (use a logit link for percentage stats; KenPom fits shot level for FT%). Then control_O = Var(alpha*off) / (Var(alpha*off) + Var(beta*def)), with variances taken across the fitted sample's offensive a |
| M-TEFF-026 | Projected PPP from play-type mix | L5 identity check fails variant (a): with Freq_pt = n_pt/N and same-span PPP_pt = pts_pt/n_pt, sum_pt Freq_pt*PPP_pt = pts/N = actual PPP exactly, so comparing (a) with actual PPP is always zero. Only a baseline PPP (D-I average or prior/shrunk own) makes the comparison informative. The source gives | Projected_PPP = sum_pt Freq_pt * PPP_pt(baseline), where baseline is the D-I average or the team's own shrunk/prior-span PPP_pt, never the same-span raw PPP_pt. |
| M-FOUL-101 | Free-throw routine time and arc consistency | Unit bug: as written, routine_s is a difference of millisecond timestamps, so it is in ms, not s. The rim height of 3.048 m is correct. The dribble count is not in the formula. | routine_s = (video_ts_ms_release - video_ts_ms_disposal) / 1000; entry_angle_deg = atan(/dz/dxy/) of the fitted parabola at z = 3.048 m (10 ft x 0.3048), descending branch; arc_sd = sample SD of entry_angle_deg. |
| M-FOUL-116 | Foul-trouble value cost | Unit mismatch: M-FOUL-119 deltas are in m, percent and fouls per 100, so they cannot be added to points without a conversion model. The ESPN TrueHoop analogue was not opened in this pass. | cost = (on_rate - repl_rate) [points/min] * minutes_sat + sum_k beta_k * delta_k (M-FOUL-119) * passive_minutes, where beta_k converts each passivity delta (m, percent, fouls/100) into points per minute via a fitted model. |
| M-MKT-012 | Specific margin per outcome | Reproduced the vignette: booksum 1.021186 and wpo p = 0.2310/0.2632/0.5058. The package's specific_margins equal r_i/p_i - 1 (0.03057, 0.02683, 0.01396 exactly), not r_i - p_i. Our absolute form gives 0.00706 for every outcome (= M/n under wpo). The identity sum(r_i - p_i) = booksum - 1 holds but is | m_i = r_i / p_i(method) - 1 (implied's specific margin); identity sum_i p_i m_i = sum_i r_i - 1. Keep r_i - p_i as a named absolute variant. |
| M-TRAT-013 | Availability-adjusted team rating (injury / ineligibility adjustment) | The stated 'our version' subtracts only the absent players' rating x share and ignores the rating of the players who take the redistributed minutes. It overstates the loss whenever the replacements have a nonzero rating. Use the full-minus-available form above. The BPI 2012 weighting concept is conf | Delta_i = 5 * [ sum_p share_p(full) * R_p - sum_p share_p(avail) * R_p ], where share(avail) gives the absent players 0 and redistributes their minutes by the depth rule (both share vectors sum to 1). This equals 5 * sum_{p absent} share_p * R_p only when the replacements are rated 0, which the curr |
| M-TRAT-040 | Team-sheet rank averages (Resume average, Quality average) | Reproduced on 476 published rows: the nan-skipping mean of {KPI, SOR, WAB} matches RESUME AVG (max error 0.033 = rounding), and the nan-skipping mean of {BPI, KP, SAG, TRK} matches QUALITY AVG (max error 0.033). The registry's bracketed optional members are right in spirit, but SAG belongs in the Qu | ResumeAvg = mean over AVAILABLE of {KPI rank, SOR rank, WAB rank}; QualityAvg = mean over AVAILABLE of {BPI rank, KenPom rank, Sagarin rank, T-Rank rank}; rounded to 0.1. Availability by season in the data: WAB and TRK from 2025, SAG through 2023, neither in 2024 (2024 QualityAvg = mean(BPI, KP)). |
| M-IMP-012 | Lineup average opponent BPR (opposition quality faced) | Scale check on the local exports: the possession-weighted mean of lineup avg_opp_bpr is 1.23. The D-I mean of possession-weighted per-player BPR is 1.15, and 5x that would be 5.77. The export is therefore on the per-player mean scale. Set the registry switch to mean_per_player (sum/5), not sum. | AvgOppBPR_g = sum_poss (sum_{opp 5} BPR_j / 5) / n_poss, i.e. scale = mean_per_player |
| M-IMP-022 | Box Plus/Minus 2.0 (BPM, OBPM, DBPM) | Coefficients match BR exactly. L4 publisher example reproduces: pos const at 2.3 = (3-2.3)(-0.818/2) = -0.29; role const at 1 = -2.774; raw 15.6 - 8.0 team adj = +7.6 BPM; VORP (7.6+2.0) x 0.70 = 6.7. Missing piece: BR's PTS term uses team-context-adjusted points (LeBron 34.9 adjusted to 30.4 per 10 | RawBPM = 0.860 * PTS_adj + ... where PTS_adj = PTS + c_team * TSA (team-context adjustment: add a constant points per adjusted shot attempt, per BR); all other terms as in the registry. |
| M-IMP-063 | Expected possession value (EPV) per instant | The core is confirmed by two sources. The registry's decomposition omits that C is indexed at the next macro-transition time. The foul/FT extension is ours. L5 property to test once fitted: E[nu_t - nu_{t+}] = 0 (martingale) and nu at the end equals the realised points. | nu_t = sum_c E[X / C_{delta_t} = c] * P(C_{delta_t} = c / F_t), where C_{delta_t} is the coarsened state at the next macro-transition time delta_t (Theorem 2.1), not C at time t. |
| M-PASS-013 | Possessions plus assists family (Synergy) | %Ast and %Poss are confirmed by the publisher formula. PP(P+A) is defined only in words, so (PTS+AST_PTS)/PA is our reading. Poss_ours as written (possession end_event_id) undercounts Synergy Poss: a miss, offensive rebound and putback is 2 Synergy plays but 1 team possession. | PA = Poss + Ast; %Ast = 100*Ast/PA; %Poss = 100*Poss/PA; PP(P+A) = (PTS + AST_PTS)/PA (our reading). Poss_ours counts the player's PLAYS ending in an FGA, a non-technical FT trip, or a turnover. Each offensive rebound starts a new play, so it is not a count of team possession end events. |
| M-PASS-044 | Decision quality | The shot-satisfaction formula is confirmed from the paper and matches R-VL-05. The expectation must be the pass-conditional EPV, a probability-weighted mean. The schema column passes.decision_quality_xpts (minus the best option) carries regret semantics: a naming mismatch. | DQ = V(taken) - E[V / a pass happens], with E weighted by the model's pass-transition probabilities P(M_j / pass), not an unweighted mean of options. Regret = max_o V(o) - V(taken) and best_option_rate stay as our extensions. |
| M-SPACE-026 | Space occupation gain (SOG) | The printed Eq.7 has no '- Q_i(t)' term, which our formula adds. Eq.8/9 and 1.5 m/s are verified. | Printed: G_i(t) = (1/w) * sum_{t'=t+1}^{t+w+1} Q_i(t'). Our '- Q_i(t)' is an interpretation of 'difference'. If we keep it, use the mean over the w+1 terms ((1/(w+1)) * sum) minus Q_i(t), and label it ours. |
| M-SPACE-033 | Gravity (R-VL-06): ghost-displacement gravity | The clipped projections of one unit vector onto 5 directions can sum to more than 1, so the credits would exceed dev_d and break the R-VL-02 sum identity. Normalise the weights. | w_di = c_di / sum_k c_di (c_di = clip(projection of the unit displacement onto the direction to i, 0, 1)); renormalise so that sum_i w_di = 1 when any c > 0, or 0 otherwise. |
| M-SPACE-056 | Lineup balance flag (our rule; EvanMiya design reference) | Use the exact conversion for the height threshold. | height_max <= 1.9304 m (6 ft 4 in = 76 in x 0.0254) |
| M-TRN-035 | Numbers-advantage duration | The hard-coded 0.1 assumes 10 Hz. Use the actual frame dt. | adv_s = sum_t 1[advantage_t] * dt_t (dt_t = frame interval); the span variant t_adv_end - t_adv_start is stored separately |
| M-PHYS-070 | Dunk base features | The two-foot case is missing from our formula, and the distance must be horizontal (2D). | hang = t_land - t_takeoff; vertical = z_midhip(peak) - z_midhip(takeoff); takeoff_dist = //(x,y)_toe - (x,y)_rim// using the jumping-foot big toe, or the midpoint of both big toes for a two-foot takeoff |
| M-PROF-046 | Points by position (team) | The registry describes the KenPom variant as height ordering per stint. KenPom actually uses season-level cumulative-minute quintiles by height, so the variant text needs correcting. | KenPom variant: sort players by listed height ascending; cumulative minute shares cut at 20/40/60/80% of team minutes assign (split) each player's minutes to PG..C; PosPts_k = sum_i pts_i * frac_i,k / team points. Our primary (per-stint slot from M-PROF-024) can stay as a separate variant. |
| M-PROF-060 | Team age (minutes-weighted) | The MP-weighting is confirmed numerically. The registry's variant reference date (1 January) is wrong: SR uses 31 January and integer ages. | SR variant: age_i = floor(years from birth_date to 31 January of the season), team_age = sum_i age_i*MP_i / sum_i MP_i. The primary (exact age at tip, MP-weighted over prior games) is fine. |
| M-SHOOT-029 | Torvik four-zone shooting splits (dunks, close twos, farther twos, threes) | L5 check on local Shooting Splits.csv (1085 rows): close + farther + threes shares sum to 99.9-100.1, but adding dunks gives 100.5-119.0 (mean 107). Dunks are therefore nested inside close twos. L4: THREES SHARE equals KenPom-Barttorvik 3PTR and THREES FG% equals 3PT% on the rows checked (Akron 45.1 | share_z = 100 * FGA_z / FGA and FG%_z = 100 * FGM_z / FGA_z, where the zones are {close twos (rim: layups + tips + dunks), farther twos, threes}, which sum to 100. Dunks are a SUBSET of close twos (share_dunks = 100 * dunk FGA / FGA), not a fourth disjoint zone. |
| M-SHOOT-050 | Three-point variance (game-to-game) | 'margin - closing_spread' is only right if the spread is stored as an expected margin. In the usual quoted sign convention it must be margin + spread. Pin the sign convention in market_snapshots. | SD_g(3 * 3PM_g); and SD_g(margin_g + closing_spread_g) when the spread is in bookmaker sign (favourite negative), equivalently SD_g(margin_g - expected_margin_g) with expected_margin = -closing_spread, by 3PA-share quartile |
| M-REB-065 | Rebound value (expected points, PBP chance-number values) | As written, a DREB adds 'V_pbp of the chance the rebound starts' plus 'V_pbp of the new possession', and for a DREB these are the same chance, so it is double counted. Also, no baseline is subtracted, so the value is not marginal. | VAL_reb = V_after - E[V / miss, chance_number, start_cause], where V_after = V_pbp(new chance) from the rebounding team's view (ORB: V of second chance; DREB: V of new possession) and E[V / miss] = P(ORB) * V_orb_chance - P(DREB) * V_new_poss, all in offence-team sign |
| M-COACH-085 | Coach tournament record and round-reach rates | Checked against the local Coach Results.csv: WIN% = W/GAMES holds on all 332 rows. But Izzo has F4 = 4 over R64 = 16 appearances (25%) while the file shows F4% 88.60%, and CHAMP = 0 with CHAMP% 35.50%. Mark Few has 2 F4s and 97.6%. These columns look like model-based probabilities, not observed rate | WIN% = W / GAMES (confirmed). F4% and CHAMP% in the source are NOT F4/appearances or CHAMP/appearances. Store them as source values, and compute our own F4_rate = 100 * F4 / R64 and CHAMP_rate = 100 * CHAMP / R64 under distinct names. |

## Formula wrong, no fix yet

| ID | Name | Issue |
| --- | --- | --- |
| M-DEF-121 | Adjusted individual defensive rating (T-Rank) | T-Rank formula unpublished; archive page not opened this session. |
| M-DEF-122 | Defensive PRPG (D-PRPG) | Formula unpublished. |
| M-DEF-123 | Adjusted team defensive efficiency with player on court (EvanMiya) | EvanMiya method not published. |
| M-SIT-030 | Adjusted kill shots (made, conceded, margin) and run-profile category | Kill-shot rule confirmed (10+ unanswered points), but the stored formula does not state the run definition; add it. EvanMiya defines 'Strong' as teams with the largest gap between kill shots made and conceded, not as a quadrant. Our quadrant rule for Strong and the median cut lines are ours. The Poi |
| M-SIT-071 | Dominance | A search result attributed to KenPom describes dominance as the winner's average predicted margin during the game, with all attributes computed from a WP model that assumes equal teams. If so, the strength term mu_pre x seconds_left / 2400 would not be part of KenPom's version (predicted final margi |
| M-SIT-097 | Senior night flag | senior_min_share says 'prior-season-to-date minutes'; it should almost certainly be current-season minutes to date (before game g) to match 'team minutes to date'. Correct to sum(season-to-date minutes before g of seniors) / team minutes to date. |
| M-MKT-108 | ESPN odds average score | The field exists but is undefined; the unit is an assumption. Store raw. |
| M-MKT-109 | Cleaning the Glass Spread Diff | Out of NCAA scope; undefined. |
| M-MKT-112 | NIL value estimate (player labour market) | Unpublished method; nothing confirmed this session. |
| M-TRAT-011 | Opponent-strength sensitivity (EvanMiya Opponent Adjust) and ceiling/floor tier | The registry unit (points per 100 per point of opponent rating) is contradicted by the export: values are capped at +/-99.0099, so EvanMiya publishes a scaled or percentile-like index, not a raw slope. Estimation and the game-term form (OSA) are ours and unverified. The ceiling/floor tier is an info |
| M-TRAT-012 | Pace sensitivity (EvanMiya Pace Adjust) | No source defines Pace Adjust; the residual-on-pace slope reading and the GPA game form are ours. The export is a bounded +/-99 index, so the registry's slope unit is wrong for the stored value. Treat as reference_only. |
| M-IMP-033 | EvanMiya MVP score | The inputs g(Indispensability, BPR, Box BPR) are a guess. Only the column header was seen. Store the published value. |
| M-IMP-059 | kPOY rating (KenPom Player of the Year) | Could not open the KenPom POY post this session. Store the published value only. |
| M-PASS-016 | EvanMiya Playmaking skill score | The blog does not name a 'Playmaking' composite; it suggests a manual screen (top Assist Rate with Turnovers grade C- or better). The composite rests on site tooltips only. |
| M-PASS-017 | Lineup assist rate, EvanMiya (external) | The sum rule is inferred from a column name only. The unit 'percent (sum)' is unconfirmed. |
| M-PHYS-095 | Handedness (shooting hand) | No open source records handedness. 'As recorded' has no feed behind it, and the computed rule is not yet specified. |
| M-SHOOT-018 | EvanMiya Scoring Volume (projected per-possession scoring) | Opened pages confirm 'per possession' as wording only. The scale and the lineup mean are not confirmed. The unit stays unverified until values are inspected. |
| M-SHOOT-064 | ESPN opaque shooting indices (Shooting Efficiency, Scoring Efficiency) | Unpublished; store the value as is and do not model on it. |
| M-SHOOT-067 | ESPN Brick Index | A web search found no ESPN 'Brick Index'; it is not in the hoopR ESPN team-stats columns. The existence of the stat is unconfirmed. Drop it or mark it pending until it is observed in a payload. |

## Unit problems

| ID | Name | Issue |
| --- | --- | --- |
| M-FOUL-101 | Free-throw routine time and arc consistency | Unit bug: as written, routine_s is a difference of millisecond timestamps, so it is in ms, not s. The rim height of 3.048 m is correct. The dribble count is not in the formula. |
| M-FOUL-116 | Foul-trouble value cost | Unit mismatch: M-FOUL-119 deltas are in m, percent and fouls per 100, so they cannot be added to points without a conversion model. The ESPN TrueHoop analogue was not opened in this pass. |
| M-MKT-036 | Reverse line movement flag | Definition confirmed; thresholds ours. rlm_delta for moneylines should be in probability points (de-vigged), not American cents, to obey the units rule. The SharpAPI page was not opened this session. |
| M-MKT-041 | Public bet (ticket) share | The formula gives 0-1; multiply by 100 to meet the percent rule. The outside definition is unconfirmed. |
| M-MKT-106 | External pregame win probability (BPI, EvanMiya, ESPN odds) | All three are proprietary; store published values only. |
| M-MKT-108 | ESPN odds average score | The field exists but is undefined; the unit is an assumption. Store raw. |
| M-MKT-109 | Cleaning the Glass Spread Diff | Out of NCAA scope; undefined. |
| M-MKT-110 | Public bracket pick share | Formula gives 0-1, so multiply by 100. The source is unidentified. |
| M-MKT-120 | Player minutes projection and uncertainty | The unit 'minutes (60 s)' breaks the seconds rule: store seconds (0 to 2400 + 300 x OT). Unconditional mean P_play x mu_min is correct. |
| M-TRAT-011 | Opponent-strength sensitivity (EvanMiya Opponent Adjust) and ceiling/floor tier | The registry unit (points per 100 per point of opponent rating) is contradicted by the export: values are capped at +/-99.0099, so EvanMiya publishes a scaled or percentile-like index, not a raw slope. Estimation and the game-term form (OSA) are ours and unver |
| M-TRAT-012 | Pace sensitivity (EvanMiya Pace Adjust) | No source defines Pace Adjust; the residual-on-pace slope reading and the GPA game form are ours. The export is a bounded +/-99 index, so the registry's slope unit is wrong for the stored value. Treat as reference_only. |
| M-IMP-017 | Teammate chemistry and weighted chemistry | Our formula is an interaction contrast and the math is sound. The unit text says 'points per possession' while the margins elsewhere are per 100: pick per 100. WeightedChem = Chem x shared possessions then carries points-per-100 x poss, so divide by 100 to get |
| M-PASS-017 | Lineup assist rate, EvanMiya (external) | The sum rule is inferred from a column name only. The unit 'percent (sum)' is unconfirmed. |
| M-PASS-020 | Passer Rating (Taylor) | The transcription matches the source, including the parenthesis placement (-log(2.5)*(X - 5.6)). Unconfirmed: the LOG base (Excel LOG is base 10), the units of every term, and non-3 creation (ratio to load or to ast). The source gives no worked example. |
| M-SPACE-054 | Lineup positional balance (EvanMiya) | The scale is unpublished. |
| M-SPACE-055 | Lineup offensive-role balance (EvanMiya) | The scale is unpublished. |
| M-TRN-027 | Tempo class share (primary / early / half-court) | The formula yields a fraction 0-1 but the unit is percent: multiply by 100. The class boundaries are ours. |
| M-TRN-028 | Push rate by start type | Applied to Hoop-Math MSU 2023-24 the proxy gives DREB 15.8/(15.8+21.5) = 42.4%, opp score 6.0/41.9 = 14.3%, steal 4.6/7.3 = 63.0%. All speed and time thresholds are ours (R-CX-29). The formula returns a ratio, so multiply by 100 for percent. |
| M-TRN-040 | Transition turnover rate | The turnover split is confirmed. The denominator (transition possessions) and the window cut are ours. The formula needs *100 for percent. |
| M-TRN-048 | Get-back speed (retreat speed) | peak_share is a ratio. Multiply by 100 if stored as percent and document that it can exceed 100. |
| M-TRN-054 | Transition cross-matches | The unit field lists cm but the formula outputs m (gap_m). Align the unit to m per the 19 Oct decision. |
| M-TRN-067 | Numbers-margin label flip rate | The formula yields a fraction. Multiply by 100 for percent. |
| M-PHYS-039 | Sprint-back effort rate | The dot product with the unit vector to the own basket correctly gives closing speed. The 6.0 m/s threshold is ours. The formula gives a fraction, so multiply by 100. |
| M-SHOOT-018 | EvanMiya Scoring Volume (projected per-possession scoring) | Opened pages confirm 'per possession' as wording only. The scale and the lineup mean are not confirmed. The unit stays unverified until values are inspected. |
| M-SHOOT-064 | ESPN opaque shooting indices (Shooting Efficiency, Scoring Efficiency) | Unpublished; store the value as is and do not model on it. |
| M-SHOOT-067 | ESPN Brick Index | A web search found no ESPN 'Brick Index'; it is not in the hoopR ESPN team-stats columns. The existence of the stat is unconfirmed. Drop it or mark it pending until it is observed in a payload. |
| M-SHOOT-069 | Rim finishing by hand (left / right / two-hand) | Shrinkage mixes scales: in 100*(FGM_h + a*p_rim)/(FGA_h + a), p_rim must be a 0-1 proportion, not the percent value of M-SHOOT shrunk rim FG%. State this explicitly. |
| M-REB-061 | Rebound secure height (high-point rebounding) | AIR_SHARE is a 0-1 fraction but the unit is listed as m. Give it its own unit. |
| M-COACH-069 | Play-call mix and diversity (set-family shares and entropy) | share_f and matched_share are computed as 0-1 fractions while the unit says percent. Multiply by 100 or change the unit. |
| M-COACH-085 | Coach tournament record and round-reach rates | Checked against the local Coach Results.csv: WIN% = W/GAMES holds on all 332 rows. But Izzo has F4 = 4 over R64 = 16 appearances (25%) while the file shows F4% 88.60%, and CHAMP = 0 with CHAMP% 35.50%. Mark Few has 2 F4s and 97.6%. These columns look like mode |

## Still not confirmed (false)

| ID | Name | Issue |
| --- | --- | --- |
| M-TEFF-014 | Offense-versus-defense control share (tempo and four factors) | The registry formula b_O/(b_O+b_D) is wrong. KenPom explicitly measures the share of predicted-value variance contributed by each term, which differs from the coefficient ratio whenever offensive and defensive season values have different spreads. The registry also omits the site term. |
| M-MKT-012 | Specific margin per outcome | Reproduced the vignette: booksum 1.021186 and wpo p = 0.2310/0.2632/0.5058. The package's specific_margins equal r_i/p_i - 1 (0.03057, 0.02683, 0.01396 exactly), not r_i - p_i. Our absolute form gives 0.00706 for every outcome (= M/n under wpo). The identity sum(r_i - p_i) = booksum - 1 holds but is |
| M-SHOOT-067 | ESPN Brick Index | A web search found no ESPN 'Brick Index'; it is not in the hoopR ESPN team-stats columns. The existence of the stat is unconfirmed. Drop it or mark it pending until it is observed in a payload. |
| M-COACH-085 | Coach tournament record and round-reach rates | Checked against the local Coach Results.csv: WIN% = W/GAMES holds on all 332 rows. But Izzo has F4 = 4 over R64 = 16 appearances (25%) while the file shows F4% 88.60%, and CHAMP = 0 with CHAMP% 35.50%. Mark Few has 2 F4s and 97.6%. These columns look like model-based probabilities, not observed rate |

## Reference only (proprietary)

M-DEF-121, M-DEF-122, M-DEF-123, M-TEFF-011, M-FOUL-131, M-SIT-075, M-MKT-084, M-MKT-106, M-MKT-108, M-MKT-109, M-MKT-112, M-TRAT-011, M-TRAT-012, M-TRAT-023, M-TRAT-038, M-TRAT-039, M-IMP-029, M-IMP-033, M-IMP-034, M-IMP-035, M-IMP-036, M-IMP-038, M-IMP-039, M-IMP-040, M-IMP-041, M-IMP-059, M-IMP-060, M-PASS-016, M-PASS-017, M-SPACE-054, M-SPACE-055, M-SQ-028, M-TOV-049b, M-PROF-018, M-PROF-028, M-PROF-036, M-PROF-084, M-SHOOT-018, M-SHOOT-019, M-SHOOT-063, M-SHOOT-064

## Every metric

| ID | Name | Before | After | Depth | Depth possible |
| --- | --- | --- | --- | --- | --- |
| M-COACH-016 | After-timeout defensive efficiency and ATO net | false | internal | L3 | L4 if a published ATO defensive PPP is found (e.g. Synergy, which is proprietary) |
| M-COACH-017 | ATO value vs baseline (timeout factor, season-relative) | false | partial | L1 | L3 with a matched baseline; L4 against the Benz PAE figures if the NCAA PBP is replicated |
| M-COACH-030 | Timeout-followed-by-scheme-change rate | false | internal | L3 | L4 needs labelled scheme changes |
| M-COACH-035 | Challenge eligibility state and challenge lost by delay | false | partial | L3 | L3. The delay rule needs the NCAA rulebook text. |
| M-COACH-045 | Substitution network metrics (clustering, starter out-degree centrality, vulnerability) | partial | partial | L1 | L3 with the full paper (DOI 10.1080/02640414.2023.2189216) for the exact definitions |
| M-COACH-048 | Rotation optimality gap (minutes-weighted lineup quality vs best available) | false | internal | L3 | L3 |
| M-COACH-066 | End-game decision regret (win probability lost vs model-best action) | false | internal | L3 | L4 if KenPom foul-up-3 study tables can be opened (KenPom returned 403 and the archive was blocked this session) |
| M-COACH-068 | Technical free-throw shooter selection quality | false | internal | L3 | L3 |
| M-COACH-069 | Play-call mix and diversity (set-family shares and entropy) | false | internal | L3 | L3 |
| M-COACH-070 | Counter usage rate | false | internal | L3 | L3 |
| M-COACH-071 | Set disruption rate | false | internal | L3 | L3 |
| M-COACH-072 | In-game repeat-set decay | false | internal | L3 | L3 |
| M-COACH-073 | Set recognition speed (defense) and machine recognition latency | false | internal | L3 | L4 needs labelled clips |
| M-COACH-074 | Matchup hunting rate, forced-switch rate and hunt avoidance | false | internal | L3 | L3 |
| M-COACH-084 | PAKE (performance against KenPom/T-Rank expectations) and PAKE + PASE | partial | partial | L1 | L4 by recomputing Izzo's PAKE 8.8 from historic T-Rank ratings with Barthag log5 (needs historical ratings) |
| M-COACH-085 | Coach tournament record and round-reach rates | false | false | L5 | L5 reached for WIN%. F4% and CHAMP% need the source's definition. |
| M-COACH-092 | Head-coach conference win-loss record (regular-season conference games; conference tournament separate) | partial | partial | L4 | L5 by computing from game rows and reconciling to the source totals |
| M-COACH-093 | Head-coach record vs ranked opponents (AP Top 25 at game time) | partial | partial | L1 | L4 with the local AP Poll Data.csv plus game rows against an SR 'vs ranked' split |
| M-COACH-094 | Head-to-head record vs a specific opposing head coach | partial | true | L4 | L4 reached |
| M-DEF-012 | Opponent shooting by distance band / zone | partial | partial | L3 | L4 if an open NCAA team page publishes opponent FG% by distance band with box totals (e.g. CBBD/hoop-math style); NBA 5-ft bands reproducible from nba.com stats |
| M-DEF-027 | Block retention rate | false | internal | L3 | L3 max (no public standard); validate event labels against video sample |
| M-DEF-029 | Block/charge call outcomes | false | partial | L1 | L4 with NCAA PBP that distinguishes blocking vs charging fouls (currently only NBA PBP via pbpstats does) |
| M-DEF-031 | Defender set time before contact | false | internal | L3 | L3; validation against officials' block/charge calls needs pose tracking and call labels |
| M-DEF-032 | Contested shots (hustle) | partial | partial | L1 | L4 for NBA by recomputing contests from tracking vs nba.com hustle/tracking pages; NCAA none without tracking |
| M-DEF-034 | Contest rate | false | internal | L3 | L3; L4 only for NBA by dividing hustle contests by opponent FGA on court |
| M-DEF-038 | Closeout distance and speed | false | internal | L3 | L3 |
| M-DEF-039 | Closeout arrival margin | false | internal | L3 | L3 |
| M-DEF-040 | Controlled closeout rate | false | internal | L3 | L3 |
| M-DEF-041 | Closeout overrun (blow-by after closeout) rate | false | internal | L3 | L3 |
| M-DEF-042 | Landing-space encroachment rate | false | internal | L3 | L3 (pose tracking needed) |
| M-DEF-045 | Normal FG% of shooters defended | false | partial | L1 | L4 for NBA: recompute NORMAL_FG_PCT for one defender from shooters' season FG% and defended attempts via nba.com API |
| M-DEF-047 | Rim defended field-goal percentage | partial | partial | L1 | L4 for NBA vs nba.com DFG% at rim if the rim-defender rule is matched; NCAA none |
| M-DEF-048 | Rim deterrence (rim attempts deterred) | partial | partial | L2 | L4 if a public page lists a defender's rim FGA faced per 100 and league average |
| M-DEF-051 | Rim protector distance to ball | false | internal | L3 | L3 |
| M-DEF-055 | Ghost defence value gap | false | partial | L1 | L3 with a trained ghost model on tracking; no public numeric output for basketball |
| M-DEF-059 | Assignment confusion seconds | false | internal | L3 | L3 |
| M-DEF-060 | Matchup time and share | partial | partial | L1 | L4 for NBA by comparing to boxscorematchupsv3 values if raw tracking existed; NCAA none |
| M-DEF-062 | Counterpoints (points allowed per 100 matched possessions) | false | partial | L1 | L3 with tracking; no public NCAA values |
| M-DEF-064 | Deterrent factor and shot-volume suppression ratio | partial | partial | L1 | L4 for NBA by recomputing from matchup FGA, partial possessions and season FGA/possession |
| M-DEF-068 | Matchup difficulty | false | partial | L1 | L3 (concept only; BBall Index values are proprietary) |
| M-DEF-070 | Mismatch hunting share (targeted defender) | false | internal | L3 | L3 |
| M-DEF-071 | Defensive switches | false | partial | L1 | L3 |
| M-DEF-072 | Switch mismatch size and exposure | false | internal | L3 | L3 |
| M-DEF-074 | Help defense field goals (help FGA/FGM/FG%) | false | partial | L1 | L3 |
| M-DEF-077 | Spatial pressure (dominant-region) | partial | partial | L1 | L3 (original Taki paper not opened) |
| M-DEF-078 | Containment rate | false | internal | L3 | L3 |
| M-DEF-079 | Blow-by rate | false | internal | L3 | L3 |
| M-DEF-080 | Defensive pick-up point | false | internal | L3 | L3 |
| M-DEF-081 | Force-direction compliance | false | internal | L3 | L3 |
| M-DEF-083 | Distance to man, goal-side and in-gap shares | false | internal | L3 | L3 |
| M-DEF-084 | Gap integrity rate | false | internal | L3 | L3 |
| M-DEF-085 | Denial rate | false | internal | L3 | L3 |
| M-DEF-087 | Ball-watching index | false | internal | L3 | L3 (needs reliable torso orientation) |
| M-DEF-089 | Shell reaction lag | false | internal | L3 | L3 |
| M-DEF-092 | Help arrival depth | false | internal | L3 | L3 |
| M-DEF-093 | Help on-time rate | false | internal | L3 | L3 |
| M-DEF-094 | Help cost (helper's man open seconds) | false | internal | L3 | L3 |
| M-DEF-095 | Rotation chain length | false | internal | L3 | L3 |
| M-DEF-096 | Rotation chain completion time | false | internal | L3 | L3 |
| M-DEF-098 | Stunt-and-recover rate | false | internal | L3 | L3 |
| M-DEF-099 | Tag rate on the roll | false | internal | L3 | L3 |
| M-DEF-100 | Defensive reaction latency | false | internal | L3 | L3 |
| M-DEF-101 | Defensive anticipation rate | false | internal | L3 | L3 |
| M-DEF-104 | Drop depth | false | internal | L3 | L3 |
| M-DEF-105 | Drop depth discipline | false | internal | L3 | L3 |
| M-DEF-106 | Off-ball screen coverage mix and outcome | false | internal | L3 | L3 |
| M-DEF-107 | Post defense technique mix and outcome | false | internal | L3 | L3 |
| M-DEF-108 | Lob over the front | false | internal | L3 | L3 |
| M-DEF-109 | Communication gestures per 100 ball screens | false | internal | L2 | L3 once a gesture_events table and validated classifier exist |
| M-DEF-113 | Scheme-change lag and effect | false | internal | L3 | L3 |
| M-DEF-114 | Foul-trouble defensive change | false | internal | L3 | L3 |
| M-DEF-115 | Pressure before and after the bonus | false | internal | L3 | L3 |
| M-DEF-116 | Fouler distance to ball | false | internal | L3 | L3 |
| M-DEF-121 | Adjusted individual defensive rating (T-Rank) | false | reference_only | L0 | L0 (unpublished) |
| M-DEF-122 | Defensive PRPG (D-PRPG) | false | reference_only | L0 | L0 (unpublished) |
| M-DEF-123 | Adjusted team defensive efficiency with player on court (EvanMiya) | false | reference_only | L0 | L0 (proprietary) |
| M-DEF-125 | Defensive Box Plus/Minus (DBPM) | partial | true | L4 | L4 (L5 identity checked); NCAA coefficients would need a college-calibrated BPM |
| M-DEF-129 | Dunk defensive contest | partial | partial | L1 | L1 (functional form unpublished) |
| M-DEF-130 | Shot-clock pressure forced (opponent shot clock at release) | partial | partial | L3 | L4 if an open NCAA page publishes opponent shot-clock splits |
| M-DEF-131 | Opponent efficiency by shot-clock band (defensive view) and clock-pressure value | partial | partial | L5 | L5 |
| M-DEF-132 | Zone-family split: frequency and PPP allowed by named zone | partial | partial | L3 | L3 |
| M-DEF-133 | Junk / combination defence usage, PPP allowed and star suppression | partial | partial | L3 | L3 |
| M-DEF-134 | Post-entry denial and fronting rate | partial | partial | L3 | L3 |
| M-FOUL-002 | Fouls committed per 40 minutes | false | true | L4 | L5: sum over players of PF equals team PF on the box, with team PF per 40 = 40*PF/(MP/5). |
| M-FOUL-003 | Fouls per 100 defensive possessions (Foul%) | false | internal | L3 | L5 after PBP: summing on-court player PF over a lineup's possessions reproduces the lineup's team PF per 100. |
| M-FOUL-005 | Fouls drawn per 40 minutes | false | partial | L1 | L4 needs KenPom player FD/40 values (subscriber). Direct PFD after PBP where the fouled player is named reaches L3. |
| M-FOUL-017 | Points per possession in bonus | false | internal | L3 | L5 after PBP: possession-weighted bonus and non-bonus PPP recombine to overall PPP. |
| M-FOUL-056 | Time of first foul | false | internal | L3 | L5 after PBP: t_first <= every later foul time and < the game length (2400 + 300*OT). |
| M-FOUL-059 | Contest-without-foul rate | false | internal | L3 | L3 to L5 after tracking (shooting fouls on contests <= contests). |
| M-FOUL-067 | Lineup projected free-throw percentage | false | internal | L3 | L4 only if EvanMiya publishes the lineup FT value. Otherwise L5: weights sum to 1 and the result lies between the min and max player p_hat. |
| M-FOUL-074 | Opponent free-throw luck (actual minus expected) | false | internal | L3 | L5 after PBP: summed over a season, E[OppFTLuck] is about 0 across D-I if p_hat is calibrated. |
| M-FOUL-086 | Free-throw points per trip | false | internal | L3 | L5 after PBP: trips x FTPT = FTM. |
| M-FOUL-087 | Free-throw points per shooting foul drawn | false | internal | L3 | L5 after PBP. |
| M-FOUL-092 | Expected points of a one-and-one | false | partial | L4 | L4 for the base form. The Markov variant needs PBP (OROFT and the continuation value) to reach L3. |
| M-FOUL-098 | Value of a drawn foul | false | internal | L3 | L3 after PBP and a possession-value model. L5: DFV decomposes exactly into stored per-term contributions. |
| M-FOUL-099 | Free-throw percentage under pressure | false | internal | L3 | L3 after PBP. Literature comparison (pressure FT studies) not opened. |
| M-FOUL-100 | Icing effect | false | internal | L3 | L3 after PBP (timeouts between foul and first FT). External icing studies not opened in this pass. |
| M-FOUL-101 | Free-throw routine time and arc consistency | false | internal | L2 | L3 after tracking once the units are fixed. |
| M-FOUL-113 | Continuation and-one rate | false | internal | L3 | L3 after tracking. |
| M-FOUL-115 | Minutes lost to foul trouble | false | internal | L3 | L3 after PBP. |
| M-FOUL-116 | Foul-trouble value cost | false | internal | L2 | L3 after PBP and tracking, once the passive term is converted to points. |
| M-FOUL-117 | Foul rate by current foul count (player-revealed restraint) | false | partial | L1 | L4: reproduce KenPom first-half PF/40 for starters (0 fouls 2.66, 1 foul 2.34, 2 fouls 1.71) on multi-season D-I PBP from 2010. |
| M-FOUL-118 | Foul-trouble playing-time curve (coach-revealed) | false | partial | L1 | L4: reproduce KenPom points (for example, 17 min left in the first half: 0 fouls benched 4%, 1 foul benched 12%) on D-I PBP since 2009-10. |
| M-FOUL-119 | Defensive passivity in foul trouble | false | internal | L3 | L3 after tracking. |
| M-FOUL-120 | Defensive pressure before vs after the bonus | false | internal | L3 | L3 after tracking. |
| M-FOUL-127 | Crew fouls-above-average sum | false | internal | L3 | L3 after officials and PBP data (licence caveat). |
| M-FOUL-128 | Crew effect on totals | false | internal | L3 | L3 with market_snapshots closing totals and officials data. |
| M-FOUL-131 | Referee rating (KenPom Thrill Score) | false | reference_only | L1 | L1. Thrill Score is a proprietary KenPom FanMatch value, so the rating cannot be reproduced without it. Store the published value. |
| M-FOUL-138 | Contact-to-whistle rate (review only) | false | internal | L3 | L3 after tracking. |
| M-FOUL-139 | Star whistle rate | false | internal | L3 | L3 after tracking. |
| M-FOUL-140 | Next-foul probability given foul differential (make-up calls) | false | partial | L1 | L3 after D-I PBP fouls. |
| M-FOUL-141 | Leading-team foul rate | false | partial | L1 | L3 after PBP. |
| M-FOUL-144 | Discretionary turnover gap (home vs away) | false | partial | L1 | L3 after PBP turnover-type parsing. |
| M-FOUL-154 | Contact keypoint distance | false | internal | L3 | L3 after pose tracking. |
| M-FOUL-155 | Hand-check duration | false | internal | L3 | L3 after pose tracking. |
| M-FOUL-156 | Holding deceleration | false | internal | L3 | L3 after tracking. |
| M-FOUL-157 | Push displacement | false | internal | L3 | L3 after tracking. |
| M-FOUL-158 | Fouler speed at contact | false | internal | L3 | L3 after tracking. |
| M-FOUL-159 | Flop head angular speed | false | internal | L3 | L3 after pose tracking. |
| M-FOUL-160 | Dead-ball contact lag | false | internal | L3 | L3 after tracking and audio whistle detection. |
| M-IMP-004 | Opponent-adjusted on/off splits (EvanMiya) | false | partial | L1 | L4 once our replica runs on a season with an EvanMiya export: compare our AdjOnOff to the published splits (the export is reference data, not a model input). |
| M-IMP-005 | Luck-adjusted on/off and plus-minus | false | partial | L2 | L3 with a check that adjusted and raw points agree in expectation over a season (needs pbp with FT shooter ids). |
| M-IMP-011 | Lineup opponent-adjusted efficiency margin | partial | partial | L1 | L4 against EvanMiya_Lineups adj_team_eff_margin for the same season, once our BPR replica exists. |
| M-IMP-012 | Lineup average opponent BPR (opposition quality faced) | partial | partial | L3 | L4 once our computation runs on a season that matches an EvanMiya lineup export. |
| M-IMP-013 | Lineup predicted efficiency (prior plus observed) | partial | partial | L3 | L4 against pred_adj_team_eff_margin in EvanMiya_Lineups, once the prior terms are fitted. |
| M-IMP-016 | Lineup and pair RAPM with informed priors | partial | partial | L1 | L3 after the lambda CV and held-out evaluation on our pbp. |
| M-IMP-017 | Teammate chemistry and weighted chemistry | false | internal | L3 | L3; EvanMiya chemistry stays reference_only. |
| M-IMP-019 | Regularized adjusted plus-minus (RAPM) | partial | true | L3 | L4 if a public NCAA RAPM (e.g. hoop-explorer) is reproduced on the same games; L5 property already checked: the closed form equals the numerical minimiser. |
| M-IMP-022 | Box Plus/Minus 2.0 (BPM, OBPM, DBPM) | partial | partial | L4 | L4 for NBA; college-specific coefficients need the Sports-Reference CBB BPM page (404) or Torvik's GBPM documentation. |
| M-IMP-029 | Box BPR (Box OBPR, Box DBPR) | partial | reference_only | L1 | L1; weights unpublished. Our own box prior (BPM-style fit to our RAPM) would be internal. |
| M-IMP-030 | On-court impact beyond the box (BPR minus Box BPR) | false | internal | L3 | L3 |
| M-IMP-031 | BPR change (recent trend) | partial | internal | L3 | L3 |
| M-IMP-032 | Indispensability score | false | partial | L1 | L3 internal once our minutes model and BPR replica exist; EvanMiya's value stays reference_only. |
| M-IMP-033 | EvanMiya MVP score | partial | reference_only | L0 | L0-L1; proprietary. |
| M-IMP-034 | Real Plus-Minus (RPM, ORPM, DRPM) | partial | reference_only | L2 | L2; proprietary. |
| M-IMP-035 | Estimated Plus-Minus (EPM) | partial | reference_only | L1 | L1; proprietary. |
| M-IMP-036 | LEBRON (O-LEBRON, D-LEBRON) | partial | reference_only | L1 | L1; proprietary. |
| M-IMP-038 | RAPTOR (box, on/off, total, predator, WAR) | partial | reference_only | L1 | L5 identity check (total = offense + defense; offense = box + on/off) if the RAPTOR CSV is reachable (raw file returned 404 this session). |
| M-IMP-039 | Player Impact Plus-Minus (PIPM) and PIPM Wins Added | false | reference_only | L1 | L1; coefficients are only in images. |
| M-IMP-040 | Synergy Player Impact (SPI) and Wins Added | partial | reference_only | L1 | L1 for SPI; our WinsAdded instance (M-IMP-070) is computable. |
| M-IMP-041 | Synergy Stat Total (SST) | false | reference_only | L1 | L1; proprietary composite. |
| M-IMP-046 | Fantasy points | partial | partial | L1 | L4 by reproducing NBA_FANTASY_PTS from stats.nba.com box totals (endpoint did not respond to a direct request this session). |
| M-IMP-047 | Win Score and PAWS (Berri) | partial | partial | L1 | L3 once D-I position averages per 40 are computed from our own data. |
| M-IMP-059 | kPOY rating (KenPom Player of the Year) | false | reference_only | L0 | L0-L1; KenPom states the formula is unpublished by design (page 403 and archive blocked this session). |
| M-IMP-060 | T-Rank POY score | false | reference_only | L1 | L1; unpublished. |
| M-IMP-061 | G-Score (Torvik single-game Barthag) | partial | partial | L3 | L4 by reproducing a Torvik G-Score from one game's PPP and the opponent's as-of AdjOE/AdjDE (Torvik site behind a browser check). |
| M-IMP-063 | Expected possession value (EPV) per instant | partial | partial | L2 | L3 for the PBP-state layer now; the tracking layers need ball/player tracking (tracking_broadcast); the L5 martingale check needs a fitted model. |
| M-IMP-069 | Points over expectation (play-type) | false | partial | L1 | L3 internal with our play-type labels and xPPP baseline (video tier); the Synergy baseline needs a Synergy licence. |
| M-IMP-070 | Wins added from a per-100 rating (generic conversion) | partial | true | L3 | L4 if a published Wins Added (Synergy or LEBRON) is reproduced from its rating, possessions and the league points-per-win. |
| M-IMP-072 | Portability / scalability (offensive value as teammate quality rises) | partial | partial | L1 | L3 internal for the slope model once stint data and as-of OBPR exist. |
| M-IMP-074 | Player winning percentage and individual offensive/defensive win-loss record (Oliver) | partial | partial | L1 | L2 if Basketball on Paper (or a second source with the decision allocation) is opened; L5 identities already hold. |
| M-MKT-012 | Specific margin per outcome | false | false | L4 | L5 reached for the identity; L4 done against the implied vignette numbers. |
| M-MKT-036 | Reverse line movement flag | false | partial | L1 | L1: no outside numeric threshold exists; ticket-share data needs a licensed source. |
| M-MKT-037 | Move-on-air flag | false | internal | L2 | L2: own definition; no glossary page was reachable. |
| M-MKT-038 | Key number crossing | false | internal | L3 | L3 |
| M-MKT-041 | Public bet (ticket) share | false | internal | L3 | L1 if a licensed provider's definition is opened. |
| M-MKT-042 | Public money (handle) share and ticket-money divergence | false | internal | L3 | L1 if a licensed provider definition is opened. |
| M-MKT-059 | Market-implied power ratings and home-court advantage | false | partial | L1 | L2 by opening the Lowery PDF for its exact objective; L4 by reproducing a published market rating (e.g. cfbnumbers) from closing spreads. |
| M-MKT-066 | Favourite-longshot bias (realised vs implied by price band) | false | partial | L1 | L2 with an academic FLB paper using price bands; the calibration slope stays our construction. |
| M-MKT-068 | Model cover/over probability | false | true | L3 | L4 by reproducing a published cover rate band from Wolfers' Normal(spread, 10.9) model. |
| M-MKT-069 | Expected value per unit stake | false | true | L3 | L3 |
| M-MKT-083 | Middle opportunity width | false | true | L4 | L4 |
| M-MKT-084 | Best-bet confidence score (EvanMiya) | false | reference_only | L1 | L1 |
| M-MKT-085 | Market vs model in-game win-probability divergence | false | internal | L3 | L3 |
| M-MKT-086 | Market run overreaction | false | internal | L2 | L3 once the run rule is reconciled with M-SIT-030. |
| M-MKT-103 | Conference standings normal-score error | false | partial | L1 | L1: EvanMiya gives no formula. |
| M-MKT-106 | External pregame win probability (BPI, EvanMiya, ESPN odds) | false | reference_only | L1 | L1 |
| M-MKT-108 | ESPN odds average score | false | reference_only | L1 | L1 |
| M-MKT-109 | Cleaning the Glass Spread Diff | false | reference_only | L1 | L1 if CTG's /stats/guide/league_summary page (linked, not opened) defines it. |
| M-MKT-110 | Public bracket pick share | false | internal | L2 | L1 once the archive's original publisher is identified. |
| M-MKT-111 | Bracket pool value (leverage vs public) | false | internal | L3 | L3 |
| M-MKT-112 | NIL value estimate (player labour market) | false | reference_only | L0 | L1 by re-opening the EvanMiya NIL post (not opened this session). |
| M-MKT-115 | Halftime market adjustment (posted 2H line vs pre-game-implied 2H line) | false | internal | L3 | L3 |
| M-MKT-117 | Second-half and live closing-line value | false | internal | L2 | L3 |
| M-MKT-118 | Model vs live spread and total (in-game margin/total edge) | false | internal | L3 | L3 |
| M-MKT-120 | Player minutes projection and uncertainty | false | internal | L3 | L3 |
| M-MKT-121 | Player stat projected distribution (overdispersed count model) | false | partial | L2 | L4 when fitted to D-I box scores and tested by PIT. |
| M-MKT-122 | Prop over probability, fair prop probability and prop edge/EV | false | true | L3 | L4 once prop quotes are bought. |
| M-MKT-123 | Prop closing-line value | false | internal | L2 | L3 |
| M-MKT-126 | Player-stat vs team-outcome correlation matrix | false | partial | L2 | L3 |
| M-MKT-127 | Correlation-adjusted parlay probability and same-game-parlay pricing gap | false | partial | L3 | L3 |
| M-MKT-129 | Situational market-bias regression (ATS residual on spot features) | false | partial | L1 | L2 |
| M-MKT-131 | Market age and time to tip at snapshot | false | internal | L3 | L3 |
| M-MKT-133 | Limit-weighted line movement | false | internal | L2 | L3 once limit data is available. |
| M-PASS-013 | Possessions plus assists family (Synergy) | partial | partial | L1 | L4 if a Synergy export with Poss, Ast, PTS and PP(P+A) for one player is available (licence). Then PP(P+A) and %Ast can be reproduced. |
| M-PASS-014 | Pick-and-roll ball handler efficiency including passes | false | partial | L1 | L4 with a Synergy PnR BH export that has passing possessions (licence); L3 internally once the T1/T2 windows are fixed. |
| M-PASS-015 | Pure Point Rating | false | true | L2 | L4 if an open page lists a player's PPR with his AST, TOV, MP and team/league pace (old BBR pages, the Latvian-Estonian league site table plus box totals). |
| M-PASS-016 | EvanMiya Playmaking skill score | false | reference_only | L1 | L1 max: EvanMiya proprietary; store published grade/percentile |
| M-PASS-017 | Lineup assist rate, EvanMiya (external) | false | reference_only | L1 | L1 max (proprietary); reading the CSV values could test the sum hypothesis against member assist rates (L4-like check) if player assist rates are also exported |
| M-PASS-020 | Passer Rating (Taylor) | partial | partial | L1 | L4 if Taylor's published Passer Rating for an NBA player and the player's inputs are found (Thinking Basketball / Backpicks tables). Requires settling the Layup |
| M-PASS-038 | Paint touch to kick-out value | false | internal | L3 | L3 max (invented); L5 by checking spot labels vs the two-constant geometric test on tracked passes |
| M-PASS-044 | Decision quality | partial | partial | L2 | L4 not possible (no open EPV values for our games); L5 on our data: satisfaction = -regret only when the expectation equals the best option, so test both on a w |
| M-PASS-046 | Decision value per second of touch | false | internal | L3 | L3 max; compare against EPVA per touch (Cervone Eq.19) as a related check once EPV exists |
| M-PASS-047 | Open options at catch | false | internal | L3 | L3 max |
| M-PASS-049 | Advantage kept rate and advantage chain length | false | internal | L3 | L3 max |
| M-PASS-051 | Handler read correctness (ball screens) | false | internal | L3 | L3 max (coach-defined optimal read table) |
| M-PASS-064 | Hesitation dribble share | false | internal | L3 | L3 max |
| M-PASS-070 | Drive passing outcome | partial | true | L4 | L4 reached; L5: DRIVE_AST <= DRIVE_PASSES <= DRIVES holds by construction |
| M-PASS-071 | Drive turnover and foul outcome | partial | true | L4 | L4 reached |
| M-PASS-079 | Flow centrality and restricted flow centrality | partial | partial | L1 | L2 if Fewell supplementary tables are opened; L4 not possible (no NBA playoff sequence data public) |
| M-PASS-080 | Ball-movement entropy (player and team) | partial | partial | L1 | L2 needs the Fewell equation images or a second source; L5: 0 <= H_i <= log_b(n destinations) |
| M-PASS-081 | Uphill/downhill flux | false | partial | L1 | L2 needs Fewell Eq. 2 (image); L5 identity checked |
| M-PASS-085 | Matchup assists and potential assists allowed | partial | partial | L1 | L4 if NBA boxscorematchupsv3 values for one game can be pulled and compared with our assignment rule (NBA data only) |
| M-PASS-086 | Lineup assist capacity (sum of member shrunk AST% priors, ours) | false | internal | L3 | L3 max |
| M-PASS-087 | Pass delivery and release height | false | internal | L3 | L3 max (schema gap first) |
| M-PASS-088 | Extra-pass opportunities, extra passes made and extra-pass rate | partial | partial | L1 | L2/L4 only on NBA SportVU 2015-16 (public) by re-running Supola's pipeline; on our data L3 |
| M-PASS-089 | Extra-pass value gained | partial | internal | L3 | L3; L5 bound: each term of XP_value_expected > pm.xp_value_margin_xpts, so XP_value_expected > margin * XP_made |
| M-PASS-090 | Missed extra pass (overlooked better option) | partial | internal | L3 | L3; L5 identity made + missed + other = opportunities testable on data |
| M-PASS-091 | Good shot passed up (audit) | false | internal | L3 | L3 |
| M-PASS-092 | Bad shot taken (audit) | false | internal | L3 | L3 |
| M-PASS-093 | Shoot/pass decision ledger (good-to-great matrix) | false | internal | L3 | L5 once data exist: shares sum to 100 |
| M-PHYS-005 | Inactivity filter (inactive moments dropped from team movement series) | false | partial | L1 | L2 if Metulini's full text gives the thresholds. |
| M-PHYS-007 | Time on court components: live time, stoppage time, total time; live/stoppage ratio | partial | partial | L1 | L3. Requires tracking with live-ball state. |
| M-PHYS-011 | Schedule and travel fatigue context | partial | partial | L1 | L4: reproduce the haversine against a known airport-to-airport distance. |
| M-PHYS-012 | Acute:chronic workload ratio (rolling averages) | partial | true | L3 | L4 with our own daily load series against a published example (none open). |
| M-PHYS-013 | Exponentially weighted load (EWMA) and EWMA acute:chronic ratio | partial | true | L3 | L4 with a worked series (none published). |
| M-PHYS-036 | Sprint frequency interval | false | internal | L3 | L4 with tracking data. |
| M-PHYS-039 | Sprint-back effort rate | false | internal | L3 | L4 with tracking data. |
| M-PHYS-040 | Team average velocity | false | partial | L1 | L3. L4 not possible for the NCAA. |
| M-PHYS-045 | First-step burst on drives (speed gained; peak acceleration exploratory) | false | internal | L3 | L4 with tracking data. |
| M-PHYS-046 | Closeout deceleration peak | false | internal | L3 | L4 with tracking data. |
| M-PHYS-047 | Acceleration and deceleration distance | false | internal | L3 | L4 with tracking data. |
| M-PHYS-054 | Repeated acceleration bouts | partial | partial | L1 | L2 if the Mara et al. original is opened. |
| M-PHYS-055 | Effort recovery time | false | internal | L3 | L4 with tracking data. |
| M-PHYS-070 | Dunk base features | partial | partial | L1 | L1. Requires pro skeletal tracking. |
| M-PHYS-075 | Equivalent distance and equivalent distance index | partial | partial | L1 | L2 if di Prampero is opened. |
| M-PHYS-076 | High metabolic load distance (HMLD) | false | partial | L1 | L2 with a source for P_thr (commonly 25.5 W/kg, unconfirmed here). |
| M-PHYS-086 | Fatigue-adjusted efficiency | false | internal | L3 | L3. The beta estimate needs validation. |
| M-PHYS-090 | Combine athletic tests | partial | true | L3 | L3 |
| M-PHYS-091 | Team average height (minutes-weighted) | partial | true | L5 | L4 needs an open KenPom or Torvik team value with rosters and minutes (KenPom is blocked). |
| M-PHYS-092 | Team effective height | partial | true | L5 | L4 if an open published value plus roster minutes become available. |
| M-PHYS-093 | Height by position (KenPom method) | false | true | L3 | L4 blocked (KenPom behind Cloudflare and a paywall). |
| M-PHYS-094 | Lineup average height | false | internal | L3 | L3. EvanMiya lineup pages are paywalled. |
| M-PHYS-095 | Handedness (shooting hand) | false | internal | L0 | L3 once a laterality rule from tracked shots (share of release hand over n >= k shots) is specified. |
| M-PLAY-023 | Play-type points and points share | false | partial | L3 | L5: the shares must sum to 100 and PTS_pt must sum to total chance points, checkable once chances exist. L4 against the NBA SynergyPlayTypes PTS column for NBA  |
| M-PLAY-027 | Play-type points added vs baseline | false | partial | L2 | L3. L4 not possible (CTG values are behind a paywall). |
| M-PLAY-029 | Play-type mix diversity | false | internal | L3 | L5 property check: H_n is in [0,1], and H_n = 1 iff all 11 frequencies are equal. |
| M-PLAY-050 | Screen angle quality | false | internal | L3 | L3. Torso orientation on broadcast tracking is noisy, so validation needs labelled clips. |
| M-PLAY-051 | Screen contact rate | false | internal | L3 | L4 with a labelled contact set. |
| M-PLAY-053 | Screener separation after screen | false | internal | L3 | L4 with tracking data. |
| M-PLAY-055 | Action value change | false | internal | L3 | L5: credits across participants must sum to dV for each action. |
| M-PLAY-063 | Set completion and counter rate | false | internal | L3 | L5: completed + departed sum to all runs. |
| M-PROF-018 | Projected skill rates (usage-adjusted, opponent-tier projections) | false | reference_only | L1 | External: L1 only (proprietary DLM). Our variant: L3 once the hierarchical model is built and backtested on 2+ seasons of box data. |
| M-PROF-024 | Position minutes distribution (share of minutes at PG/SG/SF/PF/C) | false | partial | L1 | L4 against Basketball-Reference pct_1..pct_5 for NBA players if the BR ordering method is sourced (it is not documented on the page) |
| M-PROF-027 | Tracked floor-position profile (listed vs played position) | false | internal | L3 | L3; needs tracking player_positions |
| M-PROF-028 | Torvik role label | false | reference_only | L0 | L1 once the Torvik player page or the FAQ describing the role label is opened (the Wayback snapshot was not opened this pass) |
| M-PROF-036 | Offensive archetype (BBall Index style) | false | reference_only | L1 | L1 for BBall Index (proprietary); our argmax of soft membership is internal L3 once M-PROF-037 exists |
| M-PROF-039 | Player similarity (comps) | false | internal | L3 | L3; backtest whether comps predict next-season stats |
| M-PROF-040 | Decision-style vector (first action after the catch) | false | internal | L3 | L3; needs tracking of the receiver's first action |
| M-PROF-041 | Dribble tempo | false | internal | L3 | L3; needs dribble timestamps from tracking |
| M-PROF-042 | Shooting hand | false | internal | L3 | L3; validate against the published shooting hand |
| M-PROF-043 | Drive hand / direction bias | false | internal | L3 | L3; needs drive tracking |
| M-PROF-046 | Points by position (team) | false | partial | L1 | L4 against KenPom 'points by position' (subscription) if the KenPom variant is implemented exactly |
| M-PROF-047 | Bench minutes share and bench production (team) | false | partial | L1 | L3 to L4 against KenPom 'Bench Minutes' (subscription) once the KenPom variant is added |
| M-PROF-048 | Rotation depth and minutes concentration (team) | false | internal | L3 | L5 (property checks are trivial; worked example below) |
| M-PROF-049 | Rotation tier and minutes rank | false | internal | L3 | L3 |
| M-PROF-054 | Minutes volatility (game-to-game) | false | internal | L3 | L3 |
| M-PROF-056 | Recent form index | false | internal | L3 | L3 to L4: backtest whether form_z predicts the next-k rate beyond the baseline |
| M-PROF-057 | Role change point | false | internal | L3 | L3; opening Adams and MacKay 2007 (BOCPD) would bring it to L1 for the method |
| M-PROF-058 | Defensive assignment versatility | false | internal | L3 | L3; needs matchup probabilities from tracking |
| M-PROF-060 | Team age (minutes-weighted) | false | partial | L4 | L4 (done for the Sports Reference variant) |
| M-PROF-064 | Minutes continuity (team) | false | partial | L1 | L4 against KenPom team continuity (subscription), or the Butler 2010 value of 93.2% if 2009 and 2010 player minutes are rebuilt |
| M-PROF-066 | Class cohort share of elite players | false | partial | L1 | L2 if EvanMiya states the ranking rating; L4 if the class counts are read from the chart |
| M-PROF-079 | Average opponent rating faced (strength of competition) | false | partial | L1 | L3 for our version once lineup stints and ratings exist; L4 against EvanMiya 'Avg Opp BPR' once 2026-27 games are played and the column is populated |
| M-PROF-083 | Positional NIL premium | false | partial | L4 | L4 (published example reproduced within rounding) |
| M-PROF-084 | Draft prospect rank and probability | false | reference_only | L0 | L1 once a draft board page (for example ESPN or The Athletic big board) is opened and stored with its as-of date |
| M-PROF-091 | Weekly conference and national awards (in-season) | false | internal | L3 | L4: count the conference weekly-award releases for a player and match the release's own count (for example 'sixth') |
| M-REB-013 | Rebound margin | false | true | L4 | L4 reached |
| M-REB-021 | Four Factors rebounding contribution | false | partial | L1 | L3 after the regression fit, with a walk-forward check |
| M-REB-042 | Box-out success rate | false | partial | L1 | L3 on labelled box-out tracking |
| M-REB-043 | Box-out team-win rate and box-out rebounds | false | partial | L1 | L4 if NBA hustle box-out values can be reproduced from tracking (not available for NCAA) |
| M-REB-044 | Target rebound denial | false | internal | L3 | L5 (DENIAL equals the M-REB-042 outcome_based variant) |
| M-REB-045 | Box-out contact duration | false | internal | L3 | L4 needs hand-timed clips |
| M-REB-053 | Rebounds over expected | false | partial | L1 | L5 (sum over players of Pos_p = 1 per miss excluding team rebounds, so the sum of ROE over all 10 players is minus the number of team rebounds) |
| M-REB-055 | Inside-position count at release | false | internal | L3 | L4 needs hand-labelled frames |
| M-REB-057 | Crash vs retreat decision value | false | internal | L3 | L4 if a published crash-value number can be reproduced |
| M-REB-058 | Rebound arrival time | false | internal | L3 | L4 needs labelled clips |
| M-REB-059 | Time to secure the rebound | false | internal | L3 | L4 needs labelled clips |
| M-REB-060 | Tip-out rate | false | partial | L1 | L3 once tipper_id exists |
| M-REB-061 | Rebound secure height (high-point rebounding) | false | internal | L3 | L4 needs ball-height calibration |
| M-REB-062 | Gang rebounding and defensive crash count | false | internal | L3 | L4 needs labelled clips |
| M-REB-063 | Rebounder jam / tag rate (anti-outlet) | false | internal | L3 | L4 needs labelled clips |
| M-REB-065 | Rebound value (expected points, PBP chance-number values) | false | internal | L3 | L5 (the expected value over rebound outcomes is 0 when VAL = V_after - E[V / miss]) |
| M-REB-067 | Rebounder distance at release | false | internal | L3 | L4 needs labelled clips |
| M-REB-068 | Rebound value (expected points, tracking) | false | internal | L3 | L5 (rebounder credits plus other value_credits sum to the possession value change) |
| M-SHOOT-018 | EvanMiya Scoring Volume (projected per-possession scoring) | false | reference_only | L1 | L1. EvanMiya is proprietary, so the published value is stored. The scale can be pinned from values in the local EvanMiya export if a column ever appears. |
| M-SHOOT-019 | EvanMiya projected shooting skill (2PT%, 3PT%, FT%) | false | reference_only | L1 | L1. Proprietary DLM projections; we store the published value. |
| M-SHOOT-020 | Shot-type attempt share (2PA and 3PA share of FGA) | false | true | L5 | L5 reached |
| M-SHOOT-021 | Shooting skill posterior by zone and context (beta-binomial) | false | true | L3 | L5 by a calibration check on held-out attempts (posterior intervals cover at the nominal rate), with our own PBP. |
| M-SHOOT-029 | Torvik four-zone shooting splits (dunks, close twos, farther twos, threes) | false | partial | L5 | L5 reached on the local export. L4 against the live barttorvik page needs a JS-rendered fetch. |
| M-SHOOT-049 | Heat index (recent shooting above expectation) | false | partial | L1 | L3 once xFG exists. Calibration (mean heat about 0 over the league) is an L5 check. |
| M-SHOOT-050 | Three-point variance (game-to-game) | false | internal | L3 | L4 by back-testing against stored closing lines |
| M-SHOOT-052 | Three-point proficiency (Ben Taylor) | false | partial | L1 | L2 if Thinking Basketball publishes the volume basis |
| M-SHOOT-053 | League-adjusted shooting indexes (FG+, 2P+, 3P+, eFG+, TS+, FT+, FTr+, 3PAr+) | false | true | L4 | L5 by checking that the FGA-weighted mean index over the league is about 100 |
| M-SHOOT-054 | Shooting points added (FG Add, TS Add) | false | true | L4 | L5 (league sum of FG Add is about 0) |
| M-SHOOT-055 | Threshold points | false | partial | L1 | L1; BR does not publish threshold points per player, so no L4 |
| M-SHOOT-058 | Share of team shots taken (%Shots) | false | true | L3 | L4 against a KenPom player page (subscription) or an NBA %FGA value with on-court team FGA |
| M-SHOOT-063 | EvanMiya Keys to Victory shooting targets | false | reference_only | L1 | L1 for the targets. The hit flag is our own computation and reaches L3. |
| M-SHOOT-064 | ESPN opaque shooting indices (Shooting Efficiency, Scoring Efficiency) | false | reference_only | L1 | L1 |
| M-SHOOT-067 | ESPN Brick Index | false | false | L0 | L1 only if the field is seen in an ESPN API payload |
| M-SHOOT-069 | Rim finishing by hand (left / right / two-hand) | false | internal | L3 | L5 (sum_h FGA_h + unknown = rim FGA) on labelled tracking data |
| M-SHOOT-070 | Dominant-hand vs off-hand finishing gap and off-hand avoidance | false | internal | L3 | L4 needs a hand-labelled clip sample |
| M-SHOOT-071 | Gather-hand split (gather hand x finishing hand) | false | internal | L3 | L5 (cell counts sum to the labelled total) |
| M-SHOOT-072 | Off-hand dribble share | false | internal | L3 | L5 (context shares are consistent with the overall share) |
| M-SHOOT-074 | Short-range non-rim twos (1-3 m band) by finish class | false | internal | L3 | L5 (class shares sum to 100) |
| M-SHOOT-076 | Longest make streak and longest miss streak (with chance baseline) | false | internal | L3 | L5 (the permutation percentile is uniform under simulated i.i.d. shooters) |
| M-SHOOT-077 | Slump and cold-streak detection (rolling eFG z-score and lower CUSUM) | false | partial | L1 | L3/L5 once xFG exists (simulated i.i.d. shooters should give z about N(0,1) and the CUSUM false-alarm rate should match h) |
| M-SIT-012 | Close-game record | false | internal | L3 | L4 if a Torvik or KenPom close-game record (with its stated threshold) can be opened and our W_k/L_k reproduced from game scores; barttorvik.com served only a b |
| M-SIT-014 | Late-game wins gained (from the 5:00 mark) | harvest_only | partial | L0 | L2 with access to the KenPom blog (kenpom.com returned 403 and the Wayback URL is blocked this session); L4 only with KenPom's own WP model, which is proprietar |
| M-SIT-016 | Max deficit overcome and largest blown lead | harvest_only | partial | L0 | L4: compare with ESPN 'Largest Lead' on a matchup page for both teams (the loser's largest lead equals BL), once KenPom is reachable for the definition. |
| M-SIT-017 | Lead changes and times tied | partial | internal | L3 | L4 if a public lead-change / times-tied count is found (NBA box scores show these; for NCAA the ESPN matchup page shows only Largest Lead) and reproduced from P |
| M-SIT-021 | Lead-deficit window | harvest_only | partial | L0 | L2 with KenPom page access (blocked this session); L4 with ESPN largest-lead values for both teams. |
| M-SIT-030 | Adjusted kill shots (made, conceded, margin) and run-profile category | false | partial | L1 | L1 maximum: EvanMiya's adjustment model and profile cut lines are unpublished, so values can only be stored as a reference. |
| M-SIT-057 | Benchmark closed-form win-probability models | partial | partial | L1 | L2 by opening Stern (1994, JASA) directly; Falk's link and time unit could be settled by refitting on NBA data (L4 would need Falk's published predictions). |
| M-SIT-059 | Swing-play count | false | partial | L1 | L1: the WPA definition is confirmed; the 0.10 threshold has no source and stays a registered parameter. |
| M-SIT-065 | Counterfactual leverage (NBA Leverage) total and categories | partial | partial | L1 | L1 maximum: the NBA/AWS exact formula and credit weights (xFG%, Defensive Pressure Score) are unpublished; NBA tracking needed for credit splitting. |
| M-SIT-067 | Game stakes leverage (Daycast and Tourney Thrill Quotient) | false | internal | L2 | L1 for Torvik T3Q (reference_only) if a Torvik page defining it is found; our Leverage stays internal. |
| M-SIT-070 | Tension | false | partial | L0 | L2 if the KenPom game-attribute page can be opened (403 this session); L4 not possible because the KenPom WP model is proprietary. |
| M-SIT-071 | Dominance | false | partial | L0 | L2 with KenPom page access (403 this session). |
| M-SIT-074 | Upset score | harvest_only | partial | L0 | L2 with KenPom page access (blocked); L4 only with KenPom pre-game probabilities. |
| M-SIT-075 | Pre-game watchability (FanMatch Thrill Score, Torvik TTQ, game quality score) | false | reference_only | L1 | L1: both KenPom FanMatch Thrill Score and Torvik TTQ/GQS weights are unpublished. |
| M-SIT-080 | Team-specific home-court advantage | harvest_only | partial | L0 | L2 with the KenPom HCA posts (403 this session); L4 by reproducing a KenPom team HCA from game margins and ratings. |
| M-SIT-085 | Opening tip and jump-ball value | false | internal | L3 | L3: no published NCAA opening-tip value was opened; an estimate is possible from our own PBP. |
| M-SIT-097 | Senior night flag | false | internal | L3 | L3: a project heuristic; no study found. |
| M-SPACE-006 | Spacing graph metrics (total spacing, minimum spanning tree weight, centrality) | false | partial | L1 | L2 if the Tsiakalos full PDF gives formulas; L5 identities checked here |
| M-SPACE-008 | Open teammates at decision points | false | internal | L3 | L3 |
| M-SPACE-009 | Driving cone width | false | internal | L3 | L3 |
| M-SPACE-010 | Paint clutter on drive | false | internal | L3 | L3 |
| M-SPACE-013 | Floor balance (strong side vs weak side) | false | internal | L3 | L3 |
| M-SPACE-014 | Corner occupancy rate | false | internal | L3 | L3; L5 occ_both <= occ_any |
| M-SPACE-015 | Crowding episodes (spacing violations) | false | internal | L3 | L3 |
| M-SPACE-016 | Same-spot occupancy seconds | false | internal | L3 | L3 |
| M-SPACE-017 | Off-ball location-state shares | partial | internal | L3 | L3 |
| M-SPACE-025 | Off-ball scoring opportunity (OBSO / BIMOS) | partial | partial | L1 | L2 with Spearman (2018) primary PDF; L4 only on NBA SportVU 2015-16 public data |
| M-SPACE-026 | Space occupation gain (SOG) | partial | partial | L1 | L2 with a second implementation; basketball port L3 |
| M-SPACE-027 | Space generation gain (SGG) | partial | partial | L1 | L2 with a second source |
| M-SPACE-029 | NBA-style gravity (pressure above expected) | false | partial | L1 | L1 max (NBA/AWS model proprietary) |
| M-SPACE-030 | Gravity by situation (on/off ball x perimeter/interior) | partial | partial | L1 | L1 (G is ours) |
| M-SPACE-033 | Gravity (R-VL-06): ghost-displacement gravity | partial | internal | L3 | L5 once data exist: credits per defender sum to dev_d |
| M-SPACE-036 | Defender attention share | false | internal | L3 | L5 reached on synthetic frame (shares sum to 1.0) |
| M-SPACE-037 | SportVU off-ball defender closeness (gravity score, legacy) | partial | partial | L1 | L1 (no formula published) |
| M-SPACE-038 | Shooting gravity surface | false | partial | L1 | L1 (Patton transform unpublished) |
| M-SPACE-039 | Weak-side tag reliance | false | internal | L3 | L3 |
| M-SPACE-042 | High-speed off-ball distance | false | internal | L3 | L3 |
| M-SPACE-043 | Off-ball stationary share | false | internal | L3 | L3 |
| M-SPACE-045 | Cut value added | false | internal | L3 | L5 on data: split shares sum to dV within 1e-6 (R-VL-02) |
| M-SPACE-046 | Cutter found rate | false | internal | L3 | L3 |
| M-SPACE-047 | Cut separation at cut end | false | internal | L3 | L3 |
| M-SPACE-048 | Backdoor timing on torso turn | false | internal | L3 | L3 |
| M-SPACE-052 | Screen assist rate | false | internal | L3 | L3 |
| M-SPACE-053 | Screen user separation gain | false | internal | L3 | L3 |
| M-SPACE-054 | Lineup positional balance (EvanMiya) | false | reference_only | L1 | L1 |
| M-SPACE-055 | Lineup offensive-role balance (EvanMiya) | false | reference_only | L1 | L1 |
| M-SPACE-056 | Lineup balance flag (our rule; EvanMiya design reference) | partial | internal | L3 | L3 |
| M-SQ-008 | Shot-location source disagreement | false | internal | L3 | L4 once filmed games give video release points that can be compared with ESPN/NCAA shot charts for the same shots (needs broadcast tracking and ESPN shot-locati |
| M-SQ-017 | Rim-and-three rate | false | partial | L1 | L4 if CTG team rim-rate and three-rate frequencies (subscription) or an open team shot-zone page are reproduced from shot-level counts |
| M-SQ-018 | Shot-diet diversity (entropy) and Spread% | false | partial | L1 | L3 with a simulation check of the rarefaction estimator; L4 is not possible because Goldsberry's 1,284-cell grid is not published |
| M-SQ-025 | Point distribution by zone | false | partial | L2 | L4 on an open team shot-zone page (for example CTG or Synergy, licensed) using the same zone edges |
| M-SQ-027 | Shot context share (transition, putback, after timeout, half-court) | false | partial | L1 | L3 once possessions.is_transition and putback flags are built; L4 against Synergy play-type frequencies needs a licence |
| M-SQ-028 | EvanMiya projected 3P% and scoring-volume projections (external) | false | reference_only | L1 | L1 only; the EvanMiya model is proprietary (DLM per statistic) and we can only store the published value |
| M-SQ-057 | Contest quality score | false | internal | L3 | L3 to L4: refit the weights by logistic regression on filmed-game outcomes and compare with Franks-style log-odds-by-distance curves (needs broadcast tracking o |
| M-SQ-064 | Opponent shot quality allowed and shot-quality differential | false | internal | L3 | L4 if a licensed Synergy defensive SSQ (shot quality allowed) is compared with our def_xPts per shot |
| M-SQ-065 | Shot difficulty | false | partial | L1 | L1 to L2: the NBA xFG model is proprietary, so only the mapping can be checked; our own 1 - xFG_loc is internal L3 |
| M-SQ-075 | Forced shot rate | false | internal | L3 | L3; later a tracking shot-clock feed (or a reliable PBP shot-clock reconstruction) allows calibration of the 5 s cut and the quantile |
| M-SQ-076 | Heat shot-selection drift (hot-hand selection) | false | true | L2 | L3 to L4: replicate the sign of the heat coefficient on NCAA PBP plus our xFG model (needs a calibrated xfg_loc) |
| M-TEFF-011 | Adjusted tempo | partial | reference_only | L1 | L4 only against a published AdjT, and only if a replica reproduces KenPom or Torvik tempo within about 0.5 poss/40 across D-I. That needs a full D-I box pull (C |
| M-TEFF-014 | Offense-versus-defense control share (tempo and four factors) | false | false | L1 | L4: reproduce KenPom's published offense shares (for example eFG-related 3P% 83%, 2P% 50%, TO% 49%, OR% 73%, FTR 36%, PPP 64%, APL 86%) on one season of D-I gam |
| M-TEFF-015 | Expected game possessions (pre-game tempo projection) | partial | partial | L1 | L4 against Torvik's game-page projected tempo, using as-of AdjT for both teams plus the D-I average from a T-Rank snapshot (open site, but the as-of snapshot mu |
| M-TEFF-020 | Net rating (raw efficiency margin) | partial | true | L4 | L5 already holds: with averaged possessions, NetRtg = 100*(PTS-OppPTS)/Poss. The game-averaged variant needs per-game possession data to compare. |
| M-TEFF-023 | Scoring-possession share (Floor%, counted) and Team Play% (Oliver, per play) | partial | partial | L1 | L4 if a site publishes team Play% (none found). Counted Floor% can reach L5 after PBP (shares of possession point bins sum to 1). |
| M-TEFF-026 | Projected PPP from play-type mix | false | partial | L1 | L3 internal after tracking. Variant (b) needs a Synergy licence (D-I play-type PPP), which is licence-blocked. |
| M-TEFF-032 | Four-factor composite and factor weights | partial | partial | L1 | L3 after the D-I box pull (z-scores need D-I means and SDs; fitted weights from a NetRtg regression). |
| M-TEFF-033 | Adjusted four factors (opponent and venue adjusted) | partial | partial | L1 | L4 against Torvik's published adjusted four-factor values for one team, given the D-I box pull, opponent season averages and his home/road deltas (not published |
| M-TEFF-037 | Game-level opponent-adjusted efficiency | partial | partial | L1 | L4 against Torvik game-level adjusted efficiencies (shown on T-Rank game pages), using archived as-of AdjOE/AdjDE snapshots. |
| M-TEFF-038 | Expected game efficiency and score (pre-game projection) | false | partial | L1 | L4 against Torvik or KenPom game predictions (score and total) for a set of games, given archived as-of ratings. |
| M-TEFF-044 | Scoring margin and per-game stat differentials | partial | partial | L4 | L4 for the ESPN differentials once one ESPN row is checked against the box (the page needs a JS render or a human). |
| M-TEFF-050 | Per-possession points standard deviation (scoring variance) | partial | internal | L3 | L5 after PBP: check that the bin form equals the direct SD on real possessions and that the SE matches a bootstrap SE. |
| M-TEFF-051 | Implied game-level SD of points scored, game total and margin (from possession variance) | partial | partial | L3 | L5 after PBP and the D-I box pull: compare the implied SD with observed game-to-game SD (phi). NBA Stern data already shows non-additivity. |
| M-TEFF-052 | Four-factor differentials (team minus opponent, per game and per season) | partial | partial | L5 | L5 reached on season totals. Per-game L4 needs SR box score pages per game. |
| M-TEFF-053 | Four factors won (count per game) and factors-won versus win rate | partial | partial | L1 | L3 to L5 after the D-I box pull: check that P(win/K) is monotone in K and that the factor-won shares are consistent with the pooled table. |
| M-TOV-009 | Player turnover rate (per used possession) | partial | true | L4 | L4 to L5 with the KenPom Oliver-possession variant if the Basketball on Paper individual-possession formula is sourced |
| M-TOV-011 | Turnover margin | partial | true | L4 | L4 (done); L5 is trivial (the margin sums to 0 over both teams of a game) |
| M-TOV-015 | Non-steal turnover percentage | false | partial | L1 | L2 if KenPom's 'Offense vs. Defense: Non-steal turnovers' post is retrieved (the Wayback snapshot was missing on 19 Oct); L4 then from team box totals |
| M-TOV-016 | Live-ball and dead-ball turnovers (counts, rates, share) | partial | partial | L1 | L4 against pbpstats LiveBallTurnovers and DeadBallTurnovers outputs for NBA games (open API), or Hoopsalytics college splits |
| M-TOV-020 | Unforced (self-inflicted) turnover rate | false | internal | L3 | L3; L4 not possible (no public unforced-turnover stat); validate against manual video tags |
| M-TOV-023 | Turnover cost (expected points) | false | partial | L1 | L3 to L4 once possession_value (EPV) is fitted on tracking; property check: cost equals the EPV drop for the offence plus the opponent's starting value |
| M-TOV-025 | Expected turnovers and turnovers over expected | false | partial | L1 | L3 to L4 after the turnover hazard model is fitted; calibration check sum xTOV ≈ sum TOV over a season (L5) |
| M-TOV-026 | Leverage-weighted turnover cost | false | partial | L1 | L3 to L5 once the win-probability model exists; identity: sum of WPA over all events of a game = final outcome - pregame WP |
| M-TOV-027 | Deflections | partial | partial | L2 | L4 against NBA hustle deflections for NBA games only (no NCAA public source) |
| M-TOV-028 | Deflection rate per interceptable pass | false | internal | L3 | L3; needs pass trajectories and defender windows from tracking |
| M-TOV-029 | Pass interception window | false | partial | L1 | L3 once the motion-model parameters (vmax, amax) are calibrated on tracking; L4 not possible (no published pass windows) |
| M-TOV-030 | Bad-pass and interception rate (passer) | false | internal | L3 | L4 partly: bad-pass turnovers per pass against pbpstats BadPassTurnovers for NBA (passes need tracking) |
| M-TOV-031 | Loose balls recovered | partial | partial | L2 | L4 against NBA hustle OFF/DEF loose balls for NBA games |
| M-TOV-032 | Loose-ball (50/50) win rate and scrambles | false | internal | L3 | L3 to L4: NBA hustle data gives recoveries but not contested loose-ball segments; tracking is needed |
| M-TOV-034 | Forced turnovers credited to defender (takeaways) | false | partial | L1 | L3 to L4 partly: steals and charges against box and NBA hustle; held-ball and forced parts need tracking or video tags |
| M-TOV-036 | Steal attempts and gamble success | false | internal | L3 | L3; needs a steal_attempt event type from tracking or video |
| M-TOV-037 | Steal and takeaway value credit | false | internal | L3 | L5 once value_credits exist: check that credits over defenders sum to -cost_xpts per turnover |
| M-TOV-040 | Turnover rate by pressure band and press | false | internal | L3 | L3; needs pressure_m and scheme states from tracking |
| M-TOV-041 | Turnover rate by shot-clock band and shot-clock violations | false | internal | L3 | L3 to L4: the shot-clock-violation count can be checked against NCAA PBP team-turnover rows |
| M-TOV-042 | Turnovers per touch, per dribble and per drive | false | internal | L3 | L3 to L4 for NBA: turnovers per touch against NBA tracking touches (public tracking pages) |
| M-TOV-043 | Turnover location distribution | false | internal | L3 | L3; PBP has no turnover location, so tracking is needed |
| M-TOV-047 | Suspected travels (pivot lift) | false | internal | L3 | L3; needs pose tracking (ankle keypoints) and validation against called travels |
| M-TOV-049b | EvanMiya projected lineup TO/STL | false | reference_only | L1 | L1; the aggregation is proprietary |
| M-TOV-050 | Home-steals advantage | partial | true | L4 | L4 (done); L5: home and road margins summed over all teams cancel league-wide |
| M-TRAT-011 | Opponent-strength sensitivity (EvanMiya Opponent Adjust) and ceiling/floor tier | partial | reference_only | L1 | L1 only for the published value (EvanMiya estimation is unpublished). Our own gamma slope (residual on opponent strength) can reach L3 as an internal metric onc |
| M-TRAT-012 | Pace sensitivity (EvanMiya Pace Adjust) | partial | reference_only | L0 | L1 if EvanMiya publishes a definition; our delta slope can reach L3 as an internal metric from box/pbp residuals and expected pace. |
| M-TRAT-013 | Availability-adjusted team rating (injury / ineligibility adjustment) | false | partial | L1 | L3 internal for our roster-delta (needs our BPR replica and the availability table); EvanMiya injury rank stays reference_only. |
| M-TRAT-018 | Roster-sum team rating (team strength from player ratings and minutes) | partial | partial | L3 | L4 once our BPR replica and counted possessions exist: compare 5 x minutes-weighted player rating with our team AdjEM per game date. |
| M-TRAT-020 | Roster talent (minutes-weighted recruiting rank) | partial | partial | L1 | L1; L4 only if Torvik's TALENT column can be reproduced from recruiting ranks and minutes (needs the composite rank feed, e.g. 247 composite, licence check). |
| M-TRAT-023 | Other published team rating systems (catalogue) | false | reference_only | L0 | L1 per system if each publisher's methodology page is opened (TeamRankings, 538, Z-rating, RPPF); values are stored as published. |
| M-TRAT-024 | Consensus ordinal rank (composite of many systems) | false | internal | L3 | L4 if a published consensus (Massey composite) is reachable to compare against; masseyratings.com returned 403 in this session. |
| M-TRAT-031 | Remaining and projected strength of schedule | partial | internal | L3 | L1 for the ESPN variant if its BPI glossary text defining REM SOS is reachable; T-Rank Proj SOS needs barttorvik.com/sos.php (blocked by a browser check). |
| M-TRAT-032 | Conference-only ratings and conference schedule strength | false | partial | L1 | L4 by reproducing Torvik conference-only AdjOE/AdjDE for one team from game data (needs Torvik conference-only output; site behind a browser check). |
| M-TRAT-035 | Wins Above Bubble (WAB) and per-game win worth | partial | true | L3 | L4 by reproducing Torvik or NCAA WAB for one team from schedule and NET ratings (needs a NET-based win-probability model and NET ranks, which are public). |
| M-TRAT-038 | NCAA Evaluation Tool (NET) and Team Value Index | false | reference_only | L1 | L1; NET weights are unpublished, so store the published NET rank. |
| M-TRAT-039 | Kevin Pauga Index (KPI) | partial | reference_only | L1 | L1; the per-game value function is proprietary. |
| M-TRAT-040 | Team-sheet rank averages (Resume average, Quality average) | false | true | L4 | L4 reached; L5 would add a check that each average lies between the min and max of its components (holds by construction). |
| M-TRAT-052 | Game prediction residual (bust) and performance against expectation | partial | partial | L0 | L3 internal for residual and bust (arithmetic). PAKE and PASE reach L4 only if KenPom pre-game win probabilities and seed-based expectations for each tournament |
| M-TRAT-053 | Poll rank, points and votes (AP, Coaches) | partial | true | L4 | L5: total points across all ranked and receiving-votes teams = 325 x number of voters (sum of 1..25); checkable on a full AP release. |
| M-TRAT-068 | Game flow descriptors (excitement, tension, dominance) | partial | partial | L0 | L3 internal for our definitions; the KenPom descriptions need the blog page (403 and archive blocked this session) or a cached copy. |
| M-TRAT-074 | Opponent style profile vector (as-of team style features) | partial | partial | L1 | L3 internal (feature math); validating the zone/press proxies against scheme_states needs our video. |
| M-TRAT-075 | Opponent style class (named binary splits and data-driven clusters) | partial | internal | L3 | L3; scheme-based classes need video for validation. |
| M-TRAT-076 | Efficiency and pace versus opponent style class | partial | partial | L1 | L3 internal; out-of-sample evaluation of split effects needs several seasons of pbp. |
| M-TRAT-077 | Style sensitivity slopes (residual regression on opponent style features) | partial | internal | L3 | L3; production use requires a rolling-origin out-of-sample gain over M-TRAT-058. |
| M-TRAT-078 | Performance against similar opponents (k-nearest-neighbour record and matchup effect) | partial | true | L5 | L5 reached for Kong; Hoegh's posterior values (rho = 0.167) can be compared once our NNME fit exists. |
| M-TRN-009 | Early-shot premium (eFG 0-10 s minus 11-30 s) by start type | false | partial | L4 | L4 now. L5 needs our own PBP possessions table, so the 0-10 s and 11-30 s shares can be reproduced per team and matched to Hoop-Math within rounding. |
| M-TRN-021 | Seconds to first shot | false | internal | L3 | L4 needs tracking or broadcast-derived event timestamps with a hand-timed validation set. |
| M-TRN-026 | Transition phase timestamp vector | false | internal | L3 | L4 with a manually labelled phase-timing set. |
| M-TRN-027 | Tempo class share (primary / early / half-court) | false | internal | L3 | L5 once class labels exist: the shares must sum to 100. |
| M-TRN-028 | Push rate by start type | false | partial | L3 | L4 for the PBP proxy against our own computed shares. The tracking definition needs tracking data. |
| M-TRN-030 | Outlet time | false | internal | L3 | L4 with event-labelled tracking data. |
| M-TRN-032 | Advance mode and hit-ahead passes | false | internal | L3 | L4 with tracking data. |
| M-TRN-034 | Numbers-advantage opportunities by configuration | false | partial | L1 | L3 with a labelled numbers set. No public numeric benchmark. |
| M-TRN-035 | Numbers-advantage duration | false | internal | L3 | L4 with tracking data. |
| M-TRN-036 | Points per possession by numbers label | false | internal | L3 | L5: the possession-weighted mean of PPP_cfg over all configurations must equal overall PPP. |
| M-TRN-038 | Passed-up break rate (declined / denied / failed) | false | partial | L1 | L3 internal. No outside formula exists. |
| M-TRN-039 | Value of break state (xPts per 0.1 s) | false | partial | L1 | L3 with a calibration check (reliability curve) on held-out games. |
| M-TRN-040 | Transition turnover rate | false | partial | L1 | L3. L4 needs an open page that publishes transition TOV% (none found). |
| M-TRN-044 | Seconds to defense set and last man back | false | partial | L1 | L3 with tracking data. |
| M-TRN-045 | Get-back clocks (protect the rim, stop the ball, back past the arc) | false | partial | L1 | L3 with tracking data. |
| M-TRN-046 | Get-back onset and late get-back flag (per defender) | false | internal | L3 | L4 with tracking data. |
| M-TRN-047 | Time to get back per defender | false | internal | L3 | L4 with tracking data. |
| M-TRN-048 | Get-back speed (retreat speed) | false | internal | L3 | L4 with tracking data. |
| M-TRN-052 | Floor balance at release (safeties) | false | partial | L1 | L3 with tracking data. |
| M-TRN-053 | Unguarded-shooter seconds and time to match up | false | internal | L3 | L4 with tracking data. |
| M-TRN-054 | Transition cross-matches | false | internal | L3 | L4 with tracking matchup data. |
| M-TRN-062 | Leak-outs | false | internal | L3 | L4 with tracking data. |
| M-TRN-063 | Run-outs (manual label) | false | internal | L3 | L3. This is a manual-label count. |
| M-TRN-066 | Game possessions and predicted possessions (tempo context) | false | true | L4 | L5: a check that team and opponent possessions match within 1-2% per game. |
| M-TRN-067 | Numbers-margin label flip rate | false | internal | L3 | L3. This is a sensitivity diagnostic. |
