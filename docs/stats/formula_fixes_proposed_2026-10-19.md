# Proposed formula fixes, for approval (19 Oct 2026)

35 fixes from the two verification passes (24 from the 450-formula pass, 11 from the 1,115 depth pass). None is applied: the registry keeps the current formula and holds the proposal in `formula_fix_2026_10_19`. On approval, the proposal becomes the formula and the old one moves to `formula_before_2026_10_19`.

Numbers (F01-F35) are for approving by number.

## coaching

### F01 · M-COACH-085 · Coach tournament record and round-reach rates

- Current: WIN% = W / GAMES; F4% = F4 / appearances; CHAMP% = CHAMP / appearances.
- Proposed: WIN% = W / GAMES (confirmed). F4% and CHAMP% in the source are NOT F4/appearances or CHAMP/appearances. Store them as source values, and compute our own F4_rate = 100 * F4 / R64 and CHAMP_rate = 100 * CHAMP / R64 under distinct names.
- Why: Checked against the local Coach Results.csv: WIN% = W/GAMES holds on all 332 rows. But Izzo has F4 = 4 over R64 = 16 appearances (25%) while the file shows F4% 88.60%, and CHAMP = 0 with CHAMP% 35.50%. Mark Few has 2 F4s and 97.6%. These columns look like model-based probabilities, not observed rates.
- Found in: 450-formula pass; status now: false

## defense

### F02 · M-DEF-037 · Proximal FG% and shot proximity shares

- Current: PFG% = 100 * FGM_prox / FGA_prox; share_r = 100 * count(shots with dist(d, shooter) <= r) / opp shots on court, r in {0.3048, 0.9144, 1.524} m
- Proposed: PFG% = 100 * FGM_prox / FGA_prox with prox = dist(d, shooter) <= 1.524 m at release (source); other radii flagged as project extensions
- Why: The source uses one radius (5 ft = 1.524 m). The 1 ft and 3 ft radii are ours.
- Found in: 1,115 depth pass; status now: partial

### F03 · M-DEF-069 · Defensive versatility index

- Current: H = - sum_{pos in G,F,C} p_pos ln p_pos, p_pos = matched time on attackers of that listed position / total matched time; DVI = 100 * H / ln 3 (normalised 0-100) or raw 100 * H (max 100 * ln 3 = 109.9)
- Proposed: DVI = 100 * H, H = -sum_{pos in PG,SG,SF,PF,C} p_pos ln p_pos (source); keep the 3-class normalised variant as a project extension
- Why: The source uses 5 positions; the registry uses 3 (G, F, C) and adds a normalised form (ours).
- Found in: 1,115 depth pass; status now: partial

## fouls_ft

### F04 · M-FOUL-101 · Free-throw routine time and arc consistency

- Current: routine_s = video_ts_ms_release - video_ts_ms_disposal; entry_angle_deg = angle below horizontal of the fitted trajectory at rim-plane crossing (z = 3.048 m); arc_sd = SD(entry_angle_deg over attempts)
- Proposed: routine_s = (video_ts_ms_release - video_ts_ms_disposal) / 1000; entry_angle_deg = atan(/dz/dxy/) of the fitted parabola at z = 3.048 m (10 ft x 0.3048), descending branch; arc_sd = sample SD of entry_angle_deg.
- Why: Unit bug: as written, routine_s is a difference of millisecond timestamps, so it is in ms, not s. The rim height of 3.048 m is correct. The dribble count is not in the formula.
- Found in: 450-formula pass; status now: internal

### F05 · M-FOUL-116 · Foul-trouble value cost

- Current: cost = (on-court value rate - replacement value rate) * minutes sat in foul trouble + passive-play delta (M-FOUL-119)
- Proposed: cost = (on_rate - repl_rate) [points/min] * minutes_sat + sum_k beta_k * delta_k (M-FOUL-119) * passive_minutes, where beta_k converts each passivity delta (m, percent, fouls/100) into points per minute via a fitted model.
- Why: Unit mismatch: M-FOUL-119 deltas are in m, percent and fouls per 100, so they cannot be added to points without a conversion model. The ESPN TrueHoop analogue was not opened in this pass.
- Found in: 450-formula pass; status now: internal

### F06 · M-FOUL-053 · Block/charge restricted-area status

- Current: ra_dist_m = min distance from defender foot points to the RA polyline (semicircle r = 1.2192 m to the inner line edge + straight segments to the backboard face); call stats = count by (call, inside/on/outside, secondary)
- Proposed: ra_dist_m = signed min distance from defender foot points to the RA boundary = outer edge of the arc line (semicircle r = 1.2192 + 0.0508 = 1.2700 m from basket centre, straight segments to the backboard face); inside if any foot point is within or on the boundary
- Why: Using the inner edge (1.2192 m) misclassifies feet on the line unless 'on' is treated as inside.
- Found in: 1,115 depth pass; status now: partial

### F07 · M-FOUL-102 · Free-throw command

- Current: C = 1 / sqrt(1 + (mu_m / s)^2 + (sigma_m / s)^2), s = command_length_unit (registry constant, default 0.0254 m = 1 inch; unit used recorded with the value); mu_m = mean landing distance from bullseye, sigma_m = SD of that distance
- Proposed: C = 1 / (1 + sqrt((mu_m / s)^2 + (sigma_m / s)^2)), s = command_length_unit (registry, default 0.0254 m)
- Why: Registry formula puts the 1 inside the square root (1/sqrt(1+mu^2+sigma^2)); source has 1 + sqrt(mu^2+sigma^2). Contradicted, so downgraded.
- Found in: 1,115 depth pass; status now: false

## impact

### F08 · M-IMP-012 · Lineup average opponent BPR (opposition quality faced)

- Current: AvgOppBPR_g = sum_poss sum_{opp 5} BPR_j / n_poss, BPR_j = ratings_snapshots.value[system=evanmiya;metric_code=bpr] as of the day before each game. Registry switch scale = sum (default) / mean_per_player (= sum/5), to be set to whichever matches the EvanMiya avg_opp_bpr scale once checked against the export values.
- Proposed: AvgOppBPR_g = sum_poss (sum_{opp 5} BPR_j / 5) / n_poss, i.e. scale = mean_per_player
- Why: Scale check on the local exports: the possession-weighted mean of lineup avg_opp_bpr is 1.23. The D-I mean of possession-weighted per-player BPR is 1.15, and 5x that would be 5.77. The export is therefore on the per-player mean scale. Set the registry switch to mean_per_player (sum/5), not sum.
- Found in: 450-formula pass; status now: partial

### F09 · M-IMP-022 · Box Plus/Minus 2.0 (BPM, OBPM, DBPM)

- Current: RawBPM = sum_k c_k * stat_k_per100 + pos_const(pos) + role_const(role). Position-interpolated coefficients (c(pos) = c(1) + (pos-1)/4*(c(5)-c(1))): TO -0.964, ORB 0.613->0.181, DRB 0.116->0.181, STL 1.369->1.008, BLK 1.327->0.703, AST 0.580->1.034 (values as printed); single-valued: PTS 0.860, 3PM 0.389, PF -0.367. Role-interpolated (creator 1 -> receiver 5): FGA -0.560 -> -0.780, FTA = 0.44 x FGA coefficient. pos_const: PG -0.818, linear to 0 at SF (pos 3), 0 at SF and C; role_const: creator -2.774, neutral 0, receiver +2.774. OBPM uses its own set: PTS 0.605, 3PM 0.477, AST 0.476, TO -0.579 -> -0.882, ORB 0.606 -> 0.422, DRB -0.112 -> 0.103, STL 0.177 -> 0.294, BLK 0.725 -> 0.097, PF -0.43
- Proposed: RawBPM = 0.860 * PTS_adj + ... where PTS_adj = PTS + c_team * TSA (team-context adjustment: add a constant points per adjusted shot attempt, per BR); all other terms as in the registry.
- Why: Coefficients match BR exactly. L4 publisher example reproduces: pos const at 2.3 = (3-2.3)(-0.818/2) = -0.29; role const at 1 = -2.774; raw 15.6 - 8.0 team adj = +7.6 BPM; VORP (7.6+2.0) x 0.70 = 6.7. Missing piece: BR's PTS term uses team-context-adjusted points (LeBron 34.9 adjusted to 30.4 per 100), and the registry uses raw PTS. BR does not fully specify how c_team is derived. The coefficients are NBA-fitted.
- Found in: 450-formula pass; status now: partial

### F10 · M-IMP-063 · Expected possession value (EPV) per instant

- Current: nu_t = E[X / F_t] = sum_c E[X / C = c] * P(C = c / F_t), X in {0, 2, 3} (Cervone et al.: possessions with fouls are excluded); our layer extends X to {0, 1, 2, 3, 4} by modelling fouls and free throws (our extension). Our implementation: possession_value.value_xpts = sum_a P(terminal action a / state_t) * E[pts / a, state_t] with p_shot_part, p_pass_part, p_turnover_part stored. DeepHoops (verified wording, abstract): per-moment probabilities of terminal actions (field-goal attempt, turnover, foul, ...) each associated with an expected point value, combined into expected points; the exact DeepHoops expression is unverified. Three layers (R-VL-01): PBP-state value every second for all D-I gam
- Proposed: nu_t = sum_c E[X / C_{delta_t} = c] * P(C_{delta_t} = c / F_t), where C_{delta_t} is the coarsened state at the next macro-transition time delta_t (Theorem 2.1), not C at time t.
- Why: The core is confirmed by two sources. The registry's decomposition omits that C is indexed at the next macro-transition time. The foul/FT extension is ours. L5 property to test once fitted: E[nu_t - nu_{t+}] = 0 (martingale) and nu at the end equals the realised points.
- Found in: 450-formula pass; status now: partial

## market

### F11 · M-MKT-012 · Specific margin per outcome

- Current: m_i = r_i - p_i(method); sum_i m_i = pi - 1.
- Proposed: m_i = r_i / p_i(method) - 1 (implied's specific margin); identity sum_i p_i m_i = sum_i r_i - 1. Keep r_i - p_i as a named absolute variant.
- Why: Reproduced the vignette: booksum 1.021186 and wpo p = 0.2310/0.2632/0.5058. The package's specific_margins equal r_i/p_i - 1 (0.03057, 0.02683, 0.01396 exactly), not r_i - p_i. Our absolute form gives 0.00706 for every outcome (= M/n under wpo). The identity sum(r_i - p_i) = booksum - 1 holds but is not the published quantity.
- Found in: 450-formula pass; status now: false

### F12 · M-MKT-031 · Teaser-adjusted line

- Current: dog: line + t; favourite: line - t (t fixed per teaser product).
- Proposed: teased line_team = line_team + t for both sides (signed line, negative = favourite): favourite -3.5 + 6 = +2.5, dog +3.5 + 6 = +9.5
- Why: 'favourite: line - t' moves the favourite line the wrong way in our signed convention
- Found in: 1,115 depth pass; status now: partial

## physical

### F13 · M-PHYS-070 · Dunk base features

- Current: hang = t_land - t_takeoff; vertical = z_hip(peak) - z_hip(takeoff); takeoff_dist = /p_toe - p_rim/ (attacked-rim frame x_m/y_m is appropriate here: location relative to the rim)
- Proposed: hang = t_land - t_takeoff; vertical = z_midhip(peak) - z_midhip(takeoff); takeoff_dist = //(x,y)_toe - (x,y)_rim// using the jumping-foot big toe, or the midpoint of both big toes for a two-foot takeoff
- Why: The two-foot case is missing from our formula, and the distance must be horizontal (2D).
- Found in: 450-formula pass; status now: partial

### F14 · M-PHYS-078 · PlayerLoad and accelerometer load family (wearable)

- Current: PL = sum_t sqrt((da_x)^2 + (da_y)^2 + (da_z)^2) / 100; PL/min = PL / min; PL2D omits z; jerk modulus = /a_t - a_{t-1}/ / dt
- Proposed: PL = sum_t sqrt(((da_x)^2 + (da_y)^2 + (da_z)^2) / 100)
- Why: Published form puts /100 inside the square root (= /10 outside); registry /100 outside is 10x too small.
- Found in: 1,115 depth pass; status now: partial

## player_profile

### F15 · M-PROF-046 · Points by position (team)

- Current: Slot assignment from M-PROF-024 (ordering source registered; KenPom-style height ordering as a variant); PosPts_k = points scored by players in slot k / team points.
- Proposed: KenPom variant: sort players by listed height ascending; cumulative minute shares cut at 20/40/60/80% of team minutes assign (split) each player's minutes to PG..C; PosPts_k = sum_i pts_i * frac_i,k / team points. Our primary (per-stint slot from M-PROF-024) can stay as a separate variant.
- Why: The registry describes the KenPom variant as height ordering per stint. KenPom actually uses season-level cumulative-minute quintiles by height, so the variant text needs correcting.
- Found in: 450-formula pass; status now: partial

### F16 · M-PROF-060 · Team age (minutes-weighted)

- Current: age_i = (games.tip_scheduled_utc - players.birth_date) in years at the target game's tip (SR-style 1 January reference date as a variant); team_age = sum_i(age_i * MP_i) / sum_i MP_i over games before the tip.
- Proposed: SR variant: age_i = floor(years from birth_date to 31 January of the season), team_age = sum_i age_i*MP_i / sum_i MP_i. The primary (exact age at tip, MP-weighted over prior games) is fine.
- Why: The MP-weighting is confirmed numerically. The registry's variant reference date (1 January) is wrong: SR uses 31 January and integer ages.
- Found in: 450-formula pass; status now: partial

## playmaking

### F17 · M-PASS-013 · Possessions plus assists family (Synergy)

- Current: PA = Poss + Ast (inferred); %Ast = 100 * Ast / PA; %Poss = 100 * Poss / PA (verified, Synergy glossary); PP(P+A) = (PTS + AST_PTS) / PA (inferred, unverified); Poss_ours = count of possessions whose end_event_id has events.player_id_1 = player and events.event_type_code in (field-goal attempt, free-throw trip, turnover); AST_PTS = sum(shots.value_attempted where shots.made and assister_official_id = player)
- Proposed: PA = Poss + Ast; %Ast = 100*Ast/PA; %Poss = 100*Poss/PA; PP(P+A) = (PTS + AST_PTS)/PA (our reading). Poss_ours counts the player's PLAYS ending in an FGA, a non-technical FT trip, or a turnover. Each offensive rebound starts a new play, so it is not a count of team possession end events.
- Why: %Ast and %Poss are confirmed by the publisher formula. PP(P+A) is defined only in words, so (PTS+AST_PTS)/PA is our reading. Poss_ours as written (possession end_event_id) undercounts Synergy Poss: a miss, offensive rebound and putback is 2 Synergy plays but 1 team possession.
- Found in: 450-formula pass; status now: partial

### F18 · M-PASS-044 · Decision quality

- Current: DQ = V(option taken) - E[V(passing options)] (R-VL-05, ours); shot satisfaction (Cervone et al. 2014, Sec. 5.4) = mean over a player's shot attempts of (EPV at the shot - EPV conditioned on a pass in the next instant), per shot; regret = max_o V(o) - V(chosen) (our extension); best_option_rate = 100 * count(chosen = argmax_o V(o)) / decisions (our extension)
- Proposed: DQ = V(taken) - E[V / a pass happens], with E weighted by the model's pass-transition probabilities P(M_j / pass), not an unweighted mean of options. Regret = max_o V(o) - V(taken) and best_option_rate stay as our extensions.
- Why: The shot-satisfaction formula is confirmed from the paper and matches R-VL-05. The expectation must be the pass-conditional EPV, a probability-weighted mean. The schema column passes.decision_quality_xpts (minus the best option) carries regret semantics: a naming mismatch.
- Found in: 450-formula pass; status now: partial

## rebounding

### F19 · M-REB-065 · Rebound value (expected points, PBP chance-number values)

- Current: VAL_reb = rebounds.value_xpts = V_pbp(chance_number, start_cause) of the chance the rebound starts, where V_pbp = mean points of chances with that chance_number and start_cause over games strictly before the target; DREB: + V_pbp of the new possession for the rebounding team (offence sign convention: value for the team now on offence)
- Proposed: VAL_reb = V_after - E[V / miss, chance_number, start_cause], where V_after = V_pbp(new chance) from the rebounding team's view (ORB: V of second chance; DREB: V of new possession) and E[V / miss] = P(ORB) * V_orb_chance - P(DREB) * V_new_poss, all in offence-team sign
- Why: As written, a DREB adds 'V_pbp of the chance the rebound starts' plus 'V_pbp of the new possession', and for a DREB these are the same chance, so it is double counted. Also, no baseline is subtracted, so the value is not marginal.
- Found in: 450-formula pass; status now: internal

### F20 · M-REB-038 · Long-rebound share

- Current: LONG_SHARE = 100 * count(rebounds.loc_r_m >= long_rebound_r_m) / count(rebounds), long_rebound_r_m = 6.0 (registry)
- Proposed: LONG_SHARE = 100 * count(loc_r_m >= 3.048) / count(rebounds) (Opta 10 ft); keep 6.0 m only as a named variant
- Why: Registry threshold 6.0 m (19.7 ft) does not match the opened source (10 ft = 3.048 m).
- Found in: 1,115 depth pass; status now: partial

## shooting

### F21 · M-SHOOT-029 · Torvik four-zone shooting splits (dunks, close twos, farther twos, threes)

- Current: external; share_z = FGA_z / FGA (source FAQ: 'share of attempts'); FG%_z = FGM_z / FGA_z
- Proposed: share_z = 100 * FGA_z / FGA and FG%_z = 100 * FGM_z / FGA_z, where the zones are {close twos (rim: layups + tips + dunks), farther twos, threes}, which sum to 100. Dunks are a SUBSET of close twos (share_dunks = 100 * dunk FGA / FGA), not a fourth disjoint zone.
- Why: L5 check on local Shooting Splits.csv (1085 rows): close + farther + threes shares sum to 99.9-100.1, but adding dunks gives 100.5-119.0 (mean 107). Dunks are therefore nested inside close twos. L4: THREES SHARE equals KenPom-Barttorvik 3PTR and THREES FG% equals 3PT% on the rows checked (Akron 45.1/38.5, Alabama 53.7/35.8, Arizona, Arkansas, BYU). The registry must not treat the four as a partition.
- Found in: 450-formula pass; status now: partial

### F22 · M-SHOOT-050 · Three-point variance (game-to-game)

- Current: SD_g(3 * 3PM_g); and SD_g(margin_g - closing_spread_g) by 3PA-share quartile; closing_spread from market_snapshots where market = spread and snapshot_label IN (close, close_reported)
- Proposed: SD_g(3 * 3PM_g); and SD_g(margin_g + closing_spread_g) when the spread is in bookmaker sign (favourite negative), equivalently SD_g(margin_g - expected_margin_g) with expected_margin = -closing_spread, by 3PA-share quartile
- Why: 'margin - closing_spread' is only right if the spread is stored as an expected margin. In the usual quoted sign convention it must be margin + spread. Pin the sign convention in market_snapshots.
- Found in: 450-formula pass; status now: internal

### F23 · M-SHOOT-032 · Catch-and-shoot shooting (FG%, points)

- Current: C&S FG% = 100 * FGM_cs / FGA_cs; C&S points = sum of points on C&S shots; cs = dribbles_before <= cs_max_dribbles (default 0) AND touch_time_before_s <= cs_max_touch_s (default 2.0 s); touch_time_before_s = catch to release, dribbles included
- Proposed: cs = shot_type is jump shot AND release_r_m > 3.048 AND dribbles_before = 0 AND touch_time_before_s <= 2.0
- Why: The registry rule omits the NBA restrictions to jump shots and > 10 ft (3.048 m).
- Found in: 1,115 depth pass; status now: partial

### F24 · M-SHOOT-033 · Pull-up shooting (FG%, points)

- Current: PU FG% = 100 * FGM_pu / FGA_pu; PU points = sum of points on pull-up shots; pu = dribbles_before >= pu_min_dribbles (default 1)
- Proposed: pu = shot_type is jump shot AND release_r_m > 3.048 AND dribbles_before >= 1
- Why: The jump-shot and > 10 ft restriction is missing.
- Found in: 1,115 depth pass; status now: partial

## situational

### F25 · M-SIT-052 · Garbage-time flag (three side-by-side definitions) and share

- Current: GT_src = cummax_over_possessions_in_game(any_k(/m/ >= M_k and t_elapsed >= T_reg - W_k) and starters_on_combined <= 3), (M,W) = {(25,600),(20,300),(15,120)}; GT_ctg = cummax_over_possessions_in_game(period = 2 and (/m/ >= 25 and 540 < clock <= 720 or /m/ >= 20 and 360 < clock <= 540 or /m/ >= 10 and clock <= 360) and starters_on_combined <= 2); GT_wp = (WP > 0.98 or WP < 0.02) and clock <= 300 (WP from M-SIT-055); starters = players in the first lineup_stints row per team (start_period = 1, stint_num = 1); share_d = sum GT_d / possessions.
- Proposed: GT_ctg = per-possession condition (period = 2 and (/m/ >= 25 and 540 < clock <= 720 or /m/ >= 20 and 360 < clock <= 540 or /m/ >= 10 and clock <= 360) and starters_on_combined <= 2), without cummax (CTG resets when the conditions fail)
- Why: The CTG variant wrongly uses cummax, but CTG un-flags when the margin drops below the threshold.
- Found in: 1,115 depth pass; status now: partial

## spacing_offball

### F26 · M-SPACE-026 · Space occupation gain (SOG)

- Current: Our reading of Fernandez-Bornn Eq. 7 (window [t+1, t+w+1], divided by w; text: "mean difference of quality"): G_i(t) = (1/w) * sum_{t'=t+1..t+w+1} Q_i(t') - Q_i(t). Q_i = value-weighted owned space (dominant region x space value from model space_value_surface). Eq. 8: SOG_i(t) = G_i(t) if G_i(t) >= eps else 0. Eq. 9: SOL_i(t) = -G_i(t) if G_i(t) <= -eps else 0 (positive magnitude). Active occupation if the player moves toward the space at speed > 1.5 m/s, else passive. Defaults: w = 1.0 s (ours; paper default w = 3.0 s), eps = 0.01 (ours; paper value not given).
- Proposed: Printed: G_i(t) = (1/w) * sum_{t'=t+1}^{t+w+1} Q_i(t'). Our '- Q_i(t)' is an interpretation of 'difference'. If we keep it, use the mean over the w+1 terms ((1/(w+1)) * sum) minus Q_i(t), and label it ours.
- Why: The printed Eq.7 has no '- Q_i(t)' term, which our formula adds. Eq.8/9 and 1.5 m/s are verified.
- Found in: 450-formula pass; status now: partial

### F27 · M-SPACE-033 · Gravity (R-VL-06): ghost-displacement gravity

- Current: Per defender-second (R-DF-31): dev_d(s) = defensive_matchups.ghost_dev_m = //p_d(s) - ghost_d(s)//, ghost_d = defensive_matchups.ghost_xy_m from the registered ghost-defender model given the 5 attackers and ball. Attribution: Grav_ghost_i(s) = sum_d w_di(s) * dev_d(s), w_di = share of the displacement vector pointing toward i (projection, clipped to [0,1]). Per-event aggregation output: value_credits.defender_displacement_m (event x credited player).
- Proposed: w_di = c_di / sum_k c_di (c_di = clip(projection of the unit displacement onto the direction to i, 0, 1)); renormalise so that sum_i w_di = 1 when any c > 0, or 0 otherwise.
- Why: The clipped projections of one unit vector onto 5 directions can sum to more than 1, so the credits would exceed dev_d and break the R-VL-02 sum identity. Normalise the weights.
- Found in: 450-formula pass; status now: internal

### F28 · M-SPACE-056 · Lineup balance flag (our rule; EvanMiya design reference)

- Current: flag = 1[pos_sd < q05(pos_sd) OR role_mean > q95(role_mean) OR role_sd outside [q05, q95] OR height_max <= 1.93 m OR height_mean < q05(height_mean)], quantiles over prior-season lineups with off_poss >= 50, fit only on completed earlier seasons and stored as registry bounds. color_adj_O (lineup adjusted offense) is used only as the outcome to validate the flag, not as a penalty.
- Proposed: height_max <= 1.9304 m (6 ft 4 in = 76 in x 0.0254)
- Why: Use the exact conversion for the height threshold.
- Found in: 450-formula pass; status now: internal

### F29 · M-SPACE-028 · Run (cut) timing value

- Current: V_scenario(xi) = max_t (1/w) * sum_{k=1..w} V_frame(t + k), where the cutter's actual run path is time-shifted unchanged by xi frames while all other players' real tracks stay fixed; V_frame = the M-SPACE-025 OBSO value from the registered space-value model; V_timing = V_scenario(0) - max_{xi != 0} V_scenario(xi); our default xi in [-0.5 s, +0.5 s] in 0.1 s steps, w = 1.0 s.
- Proposed: V_frame = mean wUPPCF over the receiver's simultaneous-arrival region (or label OBSO variant as MSU); xi>0 inserts bridging segment at mean velocity of the preceding 1 s
- Why: Paper's V_frame is wUPPCF over the simultaneous-arrival region (CRSV), explicitly not OBSO; delayed starts insert a bridging segment at mean pre-initiation velocity rather than shifting the path unchanged.
- Found in: 1,115 depth pass; status now: partial

## team_efficiency

### F30 · M-TEFF-011 · Adjusted tempo

- Current: External (proprietary; no published formula). Replica (inferred from Torvik AdjOE structure via the author comment 'same basic process', not published): iterate AdjT_g = RawT_g * (avgT / OppAdjT); AdjT = recency-weighted mean of AdjT_g; recency weights w(d) and convergence tol 0.01 are our registry parameters.
- Proposed: Store the published AdjT. For the replica: Poss_g = mean(team, opp) of FGA-ORB+TOV+0.475*FTA; RawT_g = 40*Poss_g/(game_minutes); AdjT_g = RawT_g*(avgT/OppAdjT); AdjT = sum w_g*AdjT_g / sum w_g, where w_g = 1 for age<=40 d, 1-0.01*(age-40) for 40<age<=80, and 0.6 after (Torvik's published recency). Iterate to convergence.
- Why: The multiplicative replica is inferred: Torvik only says 'same basic process'. The registry's recency weights w(d) are listed as our parameters, but Torvik publishes his (40/80 days, 60% floor), so use those for a Torvik-style replica. KenPom's form is unknown, and Torvik says he does not know exactly how KenPom calculates it.
- Found in: 450-formula pass; status now: reference_only

### F31 · M-TEFF-014 · Offense-versus-defense control share (tempo and four factors)

- Current: Fit stat_game(off team O vs def team D) = a + b_O * ability_off(O) + b_D * ability_def(D) over D-I games; control_O = b_O / (b_O + b_D); ability_off(O) = mean of the stat in O's offensive games before this game (prior-games-only) or leave-one-game-out season mean; ability_def(D) likewise over D's defensive games; the fitted game never enters its own regressors.
- Proposed: Fit stat_game = a + alpha*off_season(O, excluding g) + beta*def_season(D, excluding g) + gamma*site (use a logit link for percentage stats; KenPom fits shot level for FT%). Then control_O = Var(alpha*off) / (Var(alpha*off) + Var(beta*def)), with variances taken across the fitted sample's offensive and defensive season values. Report HCA = gamma.
- Why: The registry formula b_O/(b_O+b_D) is wrong. KenPom explicitly measures the share of predicted-value variance contributed by each term, which differs from the coefficient ratio whenever offensive and defensive season values have different spreads. The registry also omits the site term.
- Found in: 450-formula pass; status now: false

### F32 · M-TEFF-026 · Projected PPP from play-type mix

- Current: (a) Own projection: Projected_PPP = sum_pt Freq_pt * PPP_pt with Freq_pt and PPP_pt from chances.set_id and chances.points (after_tracking). (b) D-I-baseline (mix-only) variant: sum_pt Freq_pt * PPP_pt(D-I) needs external:synergy (licensed; data_tier external_only, computable_now external, licence-blocked).
- Proposed: Projected_PPP = sum_pt Freq_pt * PPP_pt(baseline), where baseline is the D-I average or the team's own shrunk/prior-span PPP_pt, never the same-span raw PPP_pt.
- Why: L5 identity check fails variant (a): with Freq_pt = n_pt/N and same-span PPP_pt = pts_pt/n_pt, sum_pt Freq_pt*PPP_pt = pts/N = actual PPP exactly, so comparing (a) with actual PPP is always zero. Only a baseline PPP (D-I average or prior/shrunk own) makes the comparison informative. The source gives no formula.
- Found in: 450-formula pass; status now: partial

## team_ratings

### F33 · M-TRAT-013 · Availability-adjusted team rating (injury / ineligibility adjustment)

- Current: InjAdj = predicted_margin(healthy) - predicted_margin(available roster); EvanMiya: rating recomputed without injured players' BPR x minutes. Our version: Delta_i = sum_{p unavailable} BPR_p * min_share_p * 5 (per 100 possessions) with minutes redistributed to the next players by depth (registry rule); BPI 2012: w_game = 1 - k * (MPG_missing / minutes per slot) for games missing key players (k unpublished).
- Proposed: Delta_i = 5 * [ sum_p share_p(full) * R_p - sum_p share_p(avail) * R_p ], where share(avail) gives the absent players 0 and redistributes their minutes by the depth rule (both share vectors sum to 1). This equals 5 * sum_{p absent} share_p * R_p only when the replacements are rated 0, which the current formula assumes implicitly.
- Why: The stated 'our version' subtracts only the absent players' rating x share and ignores the rating of the players who take the redistributed minutes. It overstates the loss whenever the replacements have a nonzero rating. Use the full-minus-available form above. The BPI 2012 weighting concept is confirmed, but k and the linear form are not. EvanMiya's method (rank_inj column in the export) is unpublished.
- Found in: 450-formula pass; status now: partial

### F34 · M-TRAT-040 · Team-sheet rank averages (Resume average, Quality average)

- Current: ResumeAvg = mean(KPI_rank, SOR_rank[, WAB_rank]); QualityAvg = mean(BPI_rank, KP_rank, TRK_rank[, SAG_rank]).
- Proposed: ResumeAvg = mean over AVAILABLE of {KPI rank, SOR rank, WAB rank}; QualityAvg = mean over AVAILABLE of {BPI rank, KenPom rank, Sagarin rank, T-Rank rank}; rounded to 0.1. Availability by season in the data: WAB and TRK from 2025, SAG through 2023, neither in 2024 (2024 QualityAvg = mean(BPI, KP)).
- Why: Reproduced on 476 published rows: the nan-skipping mean of {KPI, SOR, WAB} matches RESUME AVG (max error 0.033 = rounding), and the nan-skipping mean of {BPI, KP, SAG, TRK} matches QUALITY AVG (max error 0.033). The registry's bracketed optional members are right in spirit, but SAG belongs in the Quality list in the years it exists, not as an optional add-on. Write the rule as 'mean of the systems available that season'.
- Found in: 450-formula pass; status now: true

## transition

### F35 · M-TRN-035 · Numbers-advantage duration

- Current: adv_s = sum_t 1[advantage_t] * 0.1 over the possession; or t_adv_end - t_adv_start
- Proposed: adv_s = sum_t 1[advantage_t] * dt_t (dt_t = frame interval); the span variant t_adv_end - t_adv_start is stored separately
- Why: The hard-coded 0.1 assumes 10 Hz. Use the actual frame dt.
- Found in: 450-formula pass; status now: internal

## Approval

Aldemir, 19 Oct 2026: "approved all". All 35 fixes (F01-F35) applied in registry version 0.6.0; each old formula is kept in `formula_before_2026_10_19` with a `formula_change` record (date, approver, fix ID, reason).
