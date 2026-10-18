from core import D, L, G, X

# ======================================================================== H
D("H", "Outcomes and value", "What happened and what it was worth: possession and chance outcomes, efficiency, expected points, shot and decision quality, player and lineup value, win probability, market-relative value.")

D("H.01", "Possession and chance outcomes", "")
L("H.01.01", "Possession end type and points", "", req="R-SY-04 R-DQ-06", t="possessions.end_type possessions.points", s="C")
L("H.01.02", "Chance outcomes (11-outcome multinomial)", "", req="R-PE-02 R-SY-05", t="chances.outcome_code chances.points", s="C")
L("H.01.03", "Second-chance points and putbacks", "", req="R-SY-05", t="chances.second_chance_points chances.is_putback", s="C")
L("H.01.04", "Turnover types and costs", "", req="R-EV-10 R-VL-11", t="turnovers.turnover_type turnovers.cost_xpts", s="C")

D("H.02", "Team efficiency and box-score outcomes", "")
L("H.02.01", "Box score (team and player)", "", req="R-IV-15 R-DQ-06", t="team_box.points player_box.points", s="C")
L("H.02.02", "Four factors, pace, efficiency (as of date)", "", req="R-OS-01", t="profile_snapshots.metric_code ratings_snapshots.metric_code", s="C")
L("H.02.03", "Fast-break, paint, off-turnover points", "", req="R-TR-27", t="team_box.fast_break_points team_box.points_in_paint team_box.points_off_turnovers", s="C")
L("H.02.04", "Bench points and starter/bench split", "", req="", t="player_box.starter player_box.points", s="P",
  gap=G("OS", "Should", "Team profiles include bench points, bench minutes share and starters' minutes share per game and as of date.",
        "Recomputes from player_box; equals published box-score bench points where given.", "profile_snapshots metric codes bench_points, bench_minutes_share.", prio=3))

D("H.03", "Expected value", "")
L("H.03.01", "Possession value at 10 Hz", "", req="R-VL-01 R-SR-12", t="possession_value.value_xpts", s="C")
L("H.03.02", "Pass, shot and turnover parts of value", "", req="R-VL-03", t="possession_value.p_shot_part possession_value.p_pass_part possession_value.p_turnover_part", s="C")
L("H.03.03", "Value change per action and credit", "", req="R-VL-02 R-VL-09", t="value_credits.value_delta_xpts value_credits.credit_role", s="C")
L("H.03.04", "Shot quality", "", req="R-VL-04", t="shots.shot_quality_xpts", s="C")
L("H.03.05", "Shot-making (points above shot quality)", "Actual minus expected points per shooter.", req="R-VL-04 R-VL-12", t="shots.shot_quality_xpts", s="P",
  gap=G("VL", "Shall", "Shot-making per shooter: actual points minus shot-quality expected points per attempt, shrunk toward the position-group prior, with n and 95% interval, as of each game date.",
        "Interval on every value; shooters with < 50 attempts reported as shrunk-only; out-of-sample correlation of shot-making between season halves reported.", "profile_snapshots metric code shot_making_pts_per_fga.", prio=2))
L("H.03.06", "Decision quality", "", req="R-VL-05", t="passes.decision_quality_xpts", s="C")
L("H.03.07", "Value of fouls drawn, offensive rebounds, turnovers", "", req="R-VL-10 R-VL-11", t="fouls.value_of_foul_drawn rebounds.value_xpts turnovers.cost_xpts", s="C")
L("H.03.08", "Configuration and set value", "", req="R-VL-08 R-ST-08", t="set_instances.value_start set_instance_phases.value_at_boundary", s="C")
L("H.03.09", "Neural sequence outcome model", "", req="R-VL-13", t="possession_value.outcome_probs", s="C")

D("H.04", "Player and lineup value", "")
L("H.04.01", "Off-ball value (gravity, screens)", "", req="R-VL-06", t="value_credits.defender_displacement_m", s="C")
L("H.04.02", "Player vs player", "", req="R-VL-07", t="defensive_matchups.attacker_id value_credits.credit_role", s="C")
L("H.04.03", "Shrunk player estimates", "", req="R-VL-12", t="profile_snapshots.ci95", s="C")
L("H.04.04", "Pair and lineup effects (RAPM-style)", "", req="R-CH-01", t="lineup_stints.points_for lineup_stints.points_against", s="C")
L("H.04.05", "Public impact metrics (BPM, PORPAG, RAPM, etc.)", "", req="R-DS-03 R-DS-10", t="player_card.bpm player_card.porpag ratings_snapshots.metric_code", s="C")
L("H.04.06", "Defensive value per player (stops, contests, deterrence)", "Defensive credit beyond steals and blocks: contests, rim deterrence, help value.", req="R-VL-07 R-VL-02", t="value_credits.credit_role", s="P",
  gap=G("VL", "Shall", "Defensive value credits per player: on-ball defender and help defender credited with the possession-value change they cause (contest, rotation, deflection, rim deterrence = shots not taken within 2.0 m when he is the rim protector), summed per 100 defensive possessions with interval.",
        "Credits sum to the chance's value change on defence (bookkeeping test); interval on every player value; n >= 100 possessions to rank.", "value_credits.credit_role add contest, rotation, deterrence; profile_snapshots metric def_value_per100.", prio=2))

D("H.05", "Probabilities and predictions", "")
L("H.05.01", "Pre-game win probability, margin, total", "", req="R-PR-01 R-PR-02", t="predictions.target predictions.point_value predictions.quantiles", s="C")
L("H.05.02", "In-game win probability", "", req="R-PR-11 R-MD-17", t="possessions.pre_win_prob", s="C")
L("H.05.03", "5-minute window predictions", "", req="R-PR-06", t="predictions.window_id", s="C")
L("H.05.04", "Player prop distributions", "", req="R-PR-07", t="predictions.player_id", s="C")
L("H.05.05", "Calibration and scoring", "", req="R-PR-05 R-PE-10", t="predictions.log_loss predictions.crps predictions.pit", s="C")
L("H.05.06", "Edge and closing-line value", "", req="R-MK-05 R-MK-06", t="predictions.edge predictions.clv", s="C")

D("H.06", "Pressure, clutch and surprise", "")
L("H.06.01", "Pressure performance", "", req="R-CO-04", t="state_second.clutch_flag shots.shot_quality_xpts", s="C")
L("H.06.02", "Surprise per event", "", req="R-GU-02", t="events.surprise_nats", s="C")

# ======================================================================== I
D("I", "Physical and load", "Kinematics and workload from tracking: speed, acceleration, jumps, distance, fatigue and minutes.")

D("I.01", "Kinematics", "")
L("I.01.01", "Velocity, acceleration, heading", "", req="R-DT-08 R-SR-07", t="player_positions.speed_mps player_positions.accel_mps2 player_positions.heading_deg", s="C")
L("I.01.02", "Tracked point and filter", "", req="R-PL-10", t="load_stint_bins.tracked_point load_stint_bins.filter_name player_positions.tracked_point", s="C")
L("I.01.03", "Physics limits", "", req="R-IV-13", t="state_frame.invariant_breaks", s="C")

D("I.02", "Load", "")
L("I.02.01", "Distance and time by 0.1 m/s speed bin", "", req="R-PL-09 R-PL-01 R-PL-11", t="load_stint_bins.time_s load_stint_bins.distance_m", s="C")
L("I.02.02", "Acceleration and deceleration efforts", "", req="R-PL-02 R-PL-12", t="accel_efforts.peak_mps2 accel_efforts.band", s="C")
L("I.02.03", "Top speed (p95 and 1 s peak)", "", req="R-PL-03 R-PC-05", t="player_card.trk_top_speed_ms_p95", s="C")
L("I.02.04", "Load denominators (live, minutes played, on-court)", "", req="R-PL-15", t="load_stint_bins.stint_live_time_s load_stint_bins.stint_minutes_played", s="C")
L("I.02.05", "Coverage-corrected load and exclusions", "", req="R-PL-05 R-PL-14", t="load_stint_bins.observed_frac load_stint_bins.excluded_low_coverage", s="C")
L("I.02.06", "Jump load (count and height per minute)", "", req="R-CG-11", t="player_positions.jump_height_m", s="P",
  gap=X("(see E.01.03 jumps proposal)"))
L("I.02.07", "Direction-weighted load (lateral and backward running)", "Speed-only distance under-ranks defensive load (C82).", req="", t="", s="M",
  gap=G("PL", "Should", "Store time and distance per stint split by movement direction relative to torso facing (forward, lateral, backward, in 45-degree sectors) alongside the speed bins.",
        "Direction split recomputes from player_positions torso_facing_deg; reported only where pose coverage >= 70% of the stint.", "New columns load_stint_bins.dir_sector (forward/lateral/backward) or a sibling table `load_direction_bins`.", prio=3))
L("I.02.08", "Contact load (screens set and absorbed, box-outs, post contact)", "", req="R-DT-16", t="box_outs.contact_duration_s screens.contact_distance_m", s="P",
  gap=G("PL", "Should", "Per player-game, count contact events (screens set, screens absorbed, box-out contacts, post contacts, charges taken) per minute played.",
        "Counts recompute from screens, box_outs, post_touches and defensive_events; reported with coverage.", "profile_snapshots metric contact_events_per_min.", prio=3))

D("I.03", "Fatigue, minutes and recovery", "")
L("I.03.01", "Minutes played and continuous minutes", "", req="R-PL-03 R-PE-06", t="player_box.minutes accel_efforts.continuous_minutes_at_start player_card.max_continuous_min", s="C")
L("I.03.02", "Within-game decline", "", req="R-PL-03 R-CO-07", t="accel_efforts.period load_stint_bins.period", s="C")
L("I.03.03", "Recovery after stoppages", "", req="R-PL-04", t="timeouts.duration_s", s="C")
L("I.03.04", "Relative speed (v_ref) and interpretation thresholds", "", req="R-PL-16 R-PL-17", t="profile_snapshots.metric_code", s="C")
L("I.03.05", "Season load trend vs availability", "", req="R-PL-06", t="availability.status profile_snapshots.metric_code", s="C")
L("I.03.06", "Calibration of physical measures", "", req="R-PL-13", t="run_requirement_results.metric", s="C")

# ======================================================================== J
D("J", "Context", "Everything outside the play: schedule, travel, rest, venue, crowd, referees, availability, rankings, markets, stakes, beliefs.")

D("J.01", "Schedule, travel and rest", "")
L("J.01.01", "Tip time (local, UTC), day of week", "", req="R-MD-18 R-CX-13", t="games.tip_local games.tip_scheduled_utc", s="C")
L("J.01.02", "Days of rest and games in 7 and 14 days", "", req="R-CX-05 R-MD-18", t="team_game_context.days_rest team_game_context.games_last_7d", s="C")
L("J.01.03", "Travel distance, time zones, mode", "", req="R-CX-05", t="team_game_context.travel_from_prev_km team_game_context.time_zones_crossed team_game_context.travel_mode", s="C")
L("J.01.04", "Road-trip structure", "Game index within a road trip; returning home between games (C35).", req="", t="", s="M",
  gap=G("CX", "Should", "Each team-game carries its road-trip index (1st, 2nd, ... game away without returning home) and the days since leaving campus.",
        "Recomputes from the schedule and venues; 100% of games filled.", "New columns team_game_context.road_trip_index, days_since_left_home.", prio=3))
L("J.01.05", "Tip time on each team's body clock", "Local tip time expressed in each team's home time zone (C72, C73).", req="R-CX-13", t="games.tip_scheduled_utc teams.campus_tz", s="P",
  gap=G("CX", "Should", "Each team-game stores tip time on the team's home body clock (h, from campus time zone) and days since the last time-zone shift.",
        "Recomputes from UTC tip and campus tz with zoneinfo; 100% filled.", "New columns team_game_context.tip_body_clock_h, days_since_tz_shift.", prio=3))
L("J.01.06", "Weather", "", req="R-CX-10", t="team_game_context.weather_summary", s="C")
L("J.01.07", "Academic calendar", "", req="R-CX-13", t="team_game_context.academic_flags", s="C")

D("J.02", "Venue, crowd and officials", "")
L("J.02.01", "Home, away, neutral and proximity", "", req="R-CX-04 R-CX-14", t="team_game_context.side team_game_context.campus_to_venue_km", s="C")
L("J.02.02", "Attendance and crowd", "", req="R-CX-04 R-CX-17", t="games.attendance teams.enrollment", s="C")
L("J.02.03", "Altitude difference", "", req="R-CX-16", t="team_game_context.altitude_diff_m", s="C")
L("J.02.04", "Referee crew features as of date", "", req="R-CX-06 R-RF-06", t="game_officials.official_id profile_snapshots.metric_code", s="C")
L("J.02.05", "Jersey pairing and contrast", "", req="R-CX-07", t="games.jersey_contrast_de", s="C")

D("J.03", "Teams, people and form", "")
L("J.03.01", "Availability, minutes limits, continuity", "", req="R-CX-08 R-FD-05", t="availability.status team_game_context.returning_minutes_frac", s="C")
L("J.03.02", "Ratings and rankings as of date (KenPom, Torvik, NET, AP)", "", req="R-FD-06 R-DS-04", t="ratings_snapshots.system ratings_snapshots.value ratings_snapshots.rank", s="C")
L("J.03.03", "Opponent recent form", "Last game result and margin, overtime last game, streak.", req="R-OS-01", t="", s="P",
  gap=G("CX", "Should", "Each team-game carries the previous game's result, margin vs spread, overtime flag and current win/loss streak, as of tip.",
        "Recomputes from games; no post-tip data (leakage test passes).", "New columns team_game_context.prev_margin, prev_ats_residual, prev_overtime, streak.", prio=3))
L("J.03.04", "Coach head-to-head and prior meetings", "", req="R-CC-05 R-CX-19", t="profile_snapshots.metric_code", s="C")
L("J.03.05", "Opponent baselines and scouting", "", req="R-OS-01 R-OS-02 R-OS-05", t="profile_snapshots.metric_code", s="C")

D("J.04", "Stakes and calendar position", "")
L("J.04.01", "Stakes stamp (conference, tournament, seeds, rivalry, national TV)", "", req="R-CX-15 R-CX-11", t="team_game_context.stakes_codes team_game_context.is_rivalry", s="C")
L("J.04.02", "Standings and seeding at stake", "", req="R-CX-11", t="team_game_context.stakes_codes", s="C")
L("J.04.03", "Season phase and game number", "Game number in season, conference game number.", req="R-MD-14", t="games.game_type", s="P",
  gap=G("CX", "Should", "Each team-game carries its game number in the season and in conference play.", "Recomputes from the schedule; 100% filled.", "New columns team_game_context.game_num_season, game_num_conf.", prio=3))

D("J.05", "Markets", "")
L("J.05.01", "Closing lines (spread, total, moneyline)", "", req="R-MK-01 R-MK-14", t="market_snapshots.line market_snapshots.price_american", s="C")
L("J.05.02", "Snapshot schedule (open, 24 h, 1 h, close, 1H, props)", "", req="R-MK-02 R-MK-16", t="market_snapshots.snapshot_label market_snapshots.market_phase", s="C")
L("J.05.03", "Prediction-market prices", "", req="R-MK-03", t="market_snapshots.bid market_snapshots.ask market_snapshots.last", s="C")
L("J.05.04", "Fair probabilities (de-vig)", "", req="R-MK-04 R-MK-15 R-MK-30", t="market_snapshots.fair_prob_power market_snapshots.fair_prob_shin", s="C")
L("J.05.05", "Line movement as a feature (separate model variant)", "", req="R-MK-08", t="simulation_runs.uses_market_input", s="C")
L("J.05.06", "Public betting share", "Mentioned in the context list; no source chosen.", req="", t="", s="M",
  gap=G("MK", "Should", "Public betting share (tickets and money, where a free public source exists) stored per market snapshot with source, used only in the market-input model variant.",
        "Source logged in the source register before collection; 0 values in the market-free variant.", "New columns market_snapshots.public_ticket_share, public_money_share.", prio=3))

D("J.06", "Beliefs and pre-game card", "")
L("J.06.01", "Beliefs register and hypothesis candidates", "Common beliefs (hot hand, momentum, timeouts, icing, tip value) turned into testable candidates C1-C82.", req="R-HY-01 R-HY-02", t="hypothesis_results.hypothesis_id", s="P",
  gap=X("(Aldemir: register candidates)", note="82 candidates await registration (live doc 'Hypothesis candidates' tab); no new requirement needed."))
L("J.06.02", "Pre-game card (24 h and 1 h)", "", req="R-CX-18 R-CX-09", t="pregame_cards.horizon pregame_cards.card_sha256", s="C")
L("J.06.03", "Feature registry and causal classes", "", req="R-CX-01 R-CX-02 R-CX-03", t="pregame_cards.context_feature_values", s="C")

# ======================================================================== K
D("K", "Coaching and decisions", "Choices coaches and players make and how they are measured.")
D("K.01", "Coach decisions", "")
L("K.01.01", "Play calls (set called, source)", "", req="R-EV-15 R-AU-02 R-CH-06", t="play_calls.mapped_set_code play_calls.call_source", s="C")
L("K.01.02", "Substitution and rotation patterns", "", req="R-CH-06 R-PE-06", t="substitutions.reason_inferred lineup_stints.duration_s", s="C")
L("K.01.03", "Timeout timing vs runs; timeouts left at half end", "", req="R-CC-02 R-EV-15", t="timeouts.game_clock_s timeouts.left_after_msu", s="C")
L("K.01.04", "Challenge decisions", "", req="R-EV-16", t="coaches_challenges.play_type coaches_challenges.outcome", s="C")
L("K.01.05", "End-game fouling, two-for-one, last-shot holds", "", req="R-PE-07", t="fouls.is_end_game_intentional state_second.two_for_one_window", s="C")
L("K.01.06", "Starting lineup and matchup assignment", "", req="R-OS-04 R-DF-01", t="player_box.starter defensive_matchups.attacker_id", s="C")
L("K.01.07", "Scheme adjustments and halftime changes", "", req="R-DF-05 R-DF-19 R-CH-06", t="scheme_changes.trigger_type", s="C")
L("K.01.08", "Tempo choice (push vs pull back)", "", req="R-TR-16 R-TR-24", t="transition_phases.pushed transition_phases.passed_up_category", s="C")
L("K.01.09", "Foul-trouble management (sitting a player)", "", req="R-PE-06 R-CC-03", t="substitutions.reason_inferred", s="C")
L("K.01.10", "Press and zone usage decisions", "", req="R-DF-14 R-DF-18", t="scheme_states.press_code", s="C")
L("K.01.11", "Icing the free-throw shooter", "Timeout called right before an opponent's free throws (C11).", req="", t="timeouts.game_clock_s free_throws.ft_sequence_id", s="P",
  gap=G("CH", "Should", "Link every timeout called between a foul and the first free throw of its sequence to that sequence (icing flag, caller team).",
        "Flag recomputes from timeouts and free_throws ordering; 100% of such timeouts flagged.", "New column free_throws.preceded_by_timeout_id.", prio=3))
L("K.01.12", "Minutes limits and rest management", "", req="R-CX-08", t="availability.minutes_limit_note", s="C")
L("K.01.13", "Coach reactions and sideline behaviour", "", req="R-CC-03 R-CC-04", t="bench_events.event_type", s="C")
L("K.01.14", "Coach card system tags", "", req="R-CC-01", t="coaches.system_offense_codes coaches.system_defense_codes", s="C")

D("K.02", "Player decisions", "")
L("K.02.01", "Shoot, pass, drive choice and decision quality", "", req="R-VL-05 R-GU-01", t="passes.decision_quality_xpts belief_states.next_action_probs", s="C")
L("K.02.02", "Decision latency", "", req="R-CO-01 R-CO-06", t="touches.decision_latency_s", s="C")
L("K.02.03", "After-error behaviour", "", req="R-CO-05", t="profile_snapshots.metric_code", s="C")
L("K.02.04", "Shot selection by shot clock and zone", "", req="R-PC-11", t="shots.shot_clock_s shots.release_sector_15deg", s="C")
