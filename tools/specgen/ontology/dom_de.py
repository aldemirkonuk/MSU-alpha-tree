from core import D, L, G, X

# ======================================================================== D
D("D", "Game state", "What is true at any instant: score, clocks, possession, ball, fouls, timeouts, lineups, situation, momentum, beliefs and data quality.")

D("D.01", "Score state", "Score, margin and scoring flow.")
L("D.01.01", "Score and margin every frame", "", req="R-SR-02 R-MD-01", t="state_frame.score_msu state_frame.score_opp state_frame.margin", s="C")
L("D.01.02", "Score-change events", "", req="R-SR-02 R-IV-04", t="score_events.delta_points score_events.event_kind", s="C")
L("D.01.03", "Lead changes and ties", "", req="R-MD-17", t="state_second.lead_changes", s="P",
  gap=G("MD", "Should", "Score state also counts ties (times tied) and the largest lead per team as of each second.",
        "Recomputes from score_events; final values equal team_box.largest_lead and the PBP 'times tied' where published.", "New columns state_second.times_tied, state_second.largest_lead_msu, largest_lead_opp.", prio=3))
L("D.01.04", "Runs (points in last 2, 4, 6 min)", "", req="R-MD-17 R-EV-13", t="state_second.run_msu_2min state_second.run_opp_2min", s="C")
L("D.01.05", "Run events (start, end, size)", "A run = net >= 8 points for one team within 120 s (beliefs register definition).", req="R-CH-08", t="", s="P",
  gap=G("EV", "Shall", "Run events stored with start time, end time, points for and against and the event that ended them, under the register definition (net >= 8 in a rolling 120 s) and a strict variant (unanswered >= 8-0).",
        "Runs recompute identically from score_events; every run has an ending cause (timeout, score, period end); counts per game reported.", "New table `runs` (game_id, run_id, team_id, start_ts, end_ts, pts_for, pts_against, definition_code, ended_by_event_id).", prio=2))
L("D.01.06", "Scoring droughts", "Time since each team's last field goal and last point.", req="", t="", s="M",
  gap=G("MD", "Should", "Seconds since each team's last field goal and last point, every second of game clock.",
        "Recomputes from score_events within 0.1 s; resets correctly at period start (flagged as carried).", "New columns state_second.secs_since_fg_msu/opp, secs_since_point_msu/opp (s).", prio=3))

D("D.02", "Clock and phase state", "Period, clocks, phase stamps and time-and-score windows.")
L("D.02.01", "Period, game clock, shot clock, clock running", "", req="R-SR-01", t="state_frame.period state_frame.game_clock_s state_frame.shot_clock_s state_frame.clock_running", s="C")
L("D.02.02", "Phase stamps (5-min window, media segment, last 4 min, clutch)", "", req="R-MD-13", t="state_second.five_min_window_id state_second.media_segment_id state_second.clutch_flag state_second.last4_flag", s="C")
L("D.02.03", "Time-and-score windows (two-for-one, foul to extend, last shot)", "", req="R-SR-11", t="state_second.two_for_one_window state_second.foul_to_extend_window state_second.last_shot_window", s="C")
L("D.02.04", "Garbage time", "Possessions whose outcome cannot change the result; sources define it differently.", req="", t="possessions.is_garbage_time_source", s="P",
  gap=G("MD", "Should", "Garbage-time flag per possession under named definitions (source flag; our win-probability rule: pre-possession WP > 0.98 or < 0.02 with <= 300 s left; CTG-like margin-time rule), stored side by side.",
        "All definitions present on every possession; share of garbage-time possessions per definition reported per game.", "New column possessions.garbage_time_flags (map definition -> bool).", prio=3))

D("D.03", "Possession state", "Who has the ball and in what phase.")
L("D.03.01", "Team in possession, possession and chance IDs", "", req="R-SR-05 R-MD-04", t="state_frame.team_in_possession state_frame.possession_id state_frame.chance_id state_frame.chance_number", s="C")
L("D.03.02", "Phase (half court, transition, throw-in, FT, jump, timeout, review)", "", req="R-SR-05 R-GU-01", t="state_second.phase belief_states.phase", s="C")
L("D.03.03", "Seconds since change of control", "", req="R-SR-05 R-TR-01", t="state_second.secs_since_control_change", s="C")
L("D.03.04", "Possession start type", "After make, DREB, steal, dead-ball TO, FT, period start, held ball.", req="R-SY-04 R-PE-01", t="possessions.start_type_code", v="TR.ST", s="C")
L("D.03.05", "Live-time split by control state", "MSU, opponent, contested, in flight, inbound pending, dead.", req="R-MD-05", t="state_second.share_msu_ball state_second.share_contested", s="C")

D("D.04", "Ball state", "Where the ball is and what it is doing.")
L("D.04.01", "Ball-control state (6 states)", "", req="R-MD-02 R-SR-06", t="state_frame.ball_control_state", v="global_metadata.ball_control_state", s="C")
L("D.04.02", "Ball handler", "", req="R-BL-02 R-SR-06", t="state_frame.ball_handler_player_id ball_states.holder_id", s="C")
L("D.04.03", "Ball position x, y, height", "", req="R-BL-01 R-SR-06 R-CG-11", t="state_frame.ball_x_m state_frame.ball_z_m ball_states.ball_height_m", s="C")
L("D.04.04", "Ball action state (held, dribbled, passed, shot, loose, OOB, dead)", "", req="R-BL-03", t="ball_states.ball_state", s="C")
L("D.04.05", "Try in flight and ring contact", "", req="R-SR-06 R-MB-07", t="state_frame.try_in_flight state_frame.ring_contact_this_try", s="C")
L("D.04.06", "Ball visibility and inference", "", req="R-SR-06 R-MD-19", t="state_frame.ball_visible state_frame.ball_inferred", s="C")

D("D.05", "Foul state", "Team and personal fouls, bonus, foul trouble.")
L("D.05.01", "Team fouls and bonus state", "", req="R-MD-07 R-SR-03", t="state_frame.team_fouls_msu state_frame.msu_bonus_state", s="C")
L("D.05.02", "Personal fouls per player", "", req="R-SR-03 R-MD-16", t="foul_state.personal_fouls_player_cum", s="C")
L("D.05.03", "Fouls to give", "", req="R-SR-03", t="state_second.fouls_to_give_msu", s="C")
L("D.05.04", "Foul trouble flags", "", req="R-MD-16 R-SR-11", t="state_second.foul_trouble_msu foul_state.foul_trouble", s="C")
L("D.05.05", "Technical and flagrant counts toward disqualification", "", req="R-SR-03", t="foul_state.technical_class_a foul_state.flagrant1_player_cum", s="C")

D("D.06", "Timeout, challenge and review state", "")
L("D.06.01", "Timeouts left by type", "", req="R-SR-04 R-MD-07", t="state_frame.to30_left_msu state_frame.timeouts_msu", s="C")
L("D.06.02", "Coach's challenge available", "", req="R-SR-04", t="state_frame.challenge_available_msu", s="C")
L("D.06.03", "Media-timeout slot state", "Which marks have been used.", req="R-SR-04 R-MD-13", t="timeouts.media_slot state_second.media_segment_id", s="C")
L("D.06.04", "Stoppage kind and review in progress", "", req="R-SR-04", t="state_frame.stoppage_kind", s="C")

D("D.07", "Lineup state", "The ten players and their composition.")
L("D.07.01", "Players on floor and lineup keys", "", req="R-SY-03 R-MD-15 R-IV-01", t="state_frame.players_on_floor lineup_stints.lineup_key lineup_stints.opponent_lineup_key", s="C")
L("D.07.02", "Minutes together this season", "", req="R-MD-15", t="lineup_stints.season_seconds_together_before", s="C")
L("D.07.03", "Stint length and continuous minutes", "", req="R-SR-07 R-PL-03", t="lineup_stints.duration_s accel_efforts.continuous_minutes_at_start", s="C")
L("D.07.04", "Lineup composition (size, positions, shooting)", "Number of bigs, mean and max height, number of 3-point shooters, ball handlers on the floor.", req="", t="", s="M",
  gap=G("MD", "Should", "Lineup composition features per stint: mean and max listed height (cm), count of players by listed position, count of players with >= 33% 3P on >= 50 attempts as of date, number of primary ball handlers; for both teams and their differences.",
        "Recomputes from rosters and as-of profiles; no data after the game date used.", "New columns on lineup_stints: mean_height_cm, max_height_cm, n_bigs, n_shooters_asof, height_diff_cm.", prio=2))
L("D.07.05", "Matchups and mismatches on the floor", "", req="R-DF-01 R-DF-09", t="defensive_matchups.attacker_id defensive_matchups.mismatch_height_cm", s="C")

D("D.08", "Restart and dead-ball state", "")
L("D.08.01", "Dead-ball reason and restart type and spot", "", req="R-SR-08", t="restarts.dead_ball_reason restarts.restart_type restarts.throw_in_spot", s="C")
L("D.08.02", "Free-throw state", "", req="R-SR-09", t="state_second.ft_state state_second.ft_attempt_k", s="C")

D("D.09", "Momentum, situation and win probability", "")
L("D.09.01", "Pre-possession win probability", "", req="R-MD-17 R-PR-11", t="possessions.pre_win_prob events.home_win_prob_source", s="C")
L("D.09.02", "Expected points of current possession", "", req="R-SR-12 R-VL-01", t="state_second.xpts_possession possession_value.value_xpts", s="C")
L("D.09.03", "Belief state (system as viewer)", "", req="R-GU-01 R-GU-02", t="belief_states.top3_sets belief_states.next_action_probs events.surprise_nats", s="C")
L("D.09.04", "Previous possession result", "", req="R-EV-13", t="possessions.previous_possession_result", s="C")
L("D.09.05", "Defensive scheme state", "", req="R-DF-04 R-MD-01", t="state_frame.defense_scheme_state scheme_states.l1_base_scheme_code", v="DEF.F18.1", s="C")
L("D.09.06", "Offensive set in progress", "", req="R-ST-05 R-ST-07 R-GU-01", t="set_instances.set_code belief_states.top3_sets", v="OFF.F1-F18 MS", s="C")

D("D.10", "Spatial and visibility state", "")
L("D.10.01", "Relative geometry and spacing", "", req="R-CG-07", t="frame_geometry.spacing_mean_m frame_geometry.hull_area_m2 frame_geometry.driving_cone_deg", s="C")
L("D.10.02", "Players visible, missing and imputed", "", req="R-DT-05 R-DT-07", t="player_positions.observed player_positions.region95_semi_axes_m", s="C")
L("D.10.03", "Data-quality flag and source per value", "", req="R-MD-19 R-SR-15 R-MD-09", t="state_frame.score_src state_frame.ball_conf state_frame.invariant_breaks", s="C")
L("D.10.04", "Blind vs anchored pass", "", req="R-SR-13", t="state_frame.game_clock_src", s="C")

# ======================================================================== E
D("E", "Individual actions", "What one player does: moving, handling, passing, shooting, rebounding, screening, cutting, posting, defending, fouling, free throws, communication.")

D("E.01", "Locomotion and footwork", "")
L("E.01.01", "Stand, walk, jog, run, sprint", "Speed-band primitives.", req="R-ST-01 R-PL-11", t="movement_primitives.primitive_type load_stint_bins.speed_bin_lo_mps", s="C")
L("E.01.02", "Defensive slide, backpedal and crossover run", "Lateral and backward movement patterns (lateral slide speed is on the card).", req="R-PC-05", t="player_card.trk_lateral_slide_ms", s="P",
  gap=G("ST", "Shall", "Movement primitives include defensive slide (velocity within 45 degrees of the torso's lateral axis), backpedal (velocity within 45 degrees opposite to torso facing) and crossover run, each with speed (m/s) and duration (s).",
        "F1 >= 0.80 per primitive on >= 50 labelled instances (proposal); torso facing error <= 20 degrees median (R-DT-10).", "movement_primitives.primitive_type add slide, backpedal, crossover_run; uses player_positions.torso_facing_deg.", prio=2))
L("E.01.03", "Jumps (takeoff, height, purpose)", "Jumps for shots, rebounds, blocks, contests; one- or two-foot takeoff.", req="R-CG-11 R-DT-10", t="player_positions.airborne player_positions.jump_height_m", s="P",
  gap=G("PL", "Should", "Jump events per player: takeoff and landing frames, takeoff foot (one/two), purpose (shot, rebound, block, contest, tip, other) and jump height (m) once 3D works; counts per minute.",
        "Jump detection recall >= 90% on 200 labelled jumps (proposal); jump height error <= 0.10 m on hand-measured jumps once R-CG-11 passes.", "New table `jumps` (game_id, player_id, takeoff_ts_ms, landing_ts_ms, takeoff_foot, purpose, height_m).", prio=2))
L("E.01.04", "Stops, pivots, first step and plant foot", "Jump stop, stride stop, pivot foot, first-step direction.", r="4-22, 4-27, 9-5", req="R-DT-16", t="", s="P",
  gap=G("DT", "Should", "Footwork events (R-DT-16) are stored in a table with the pivot foot, stop type and first-step direction (degrees relative to the basket), linked to the touch.",
        "Precision >= 80% on 200 labelled events (as R-DT-16); pivot foot correct >= 85% (proposal).", "New table `footwork_events` (game_id, player_id, touch_id, ts_ms, kind, foot, direction_deg).", prio=3))
L("E.01.05", "Gather and pre-dribble / split-step travel cues", "Gather step and foot sequence before the first dribble (2026-27 point of emphasis).", r="9-5, Points of Emphasis 5", req="", t="", s="M",
  gap=G("DT", "Should", "Record the foot sequence from catch to first dribble (gather, pivot lifted before release?) so travel calls and non-calls can be counted.",
        "Foot-sequence labels agree with gold on >= 80% of 200 labelled starts (proposal); flagged only, never called by us.", "Column footwork_events.pre_dribble_violation_suspected (bool).", prio=3))
L("E.01.06", "Change of direction", "Direction changes > 45 degrees at speed, with time to re-accelerate.", req="R-PC-05", t="player_card.trk_cod_time_s", s="P",
  gap=G("PL", "Should", "Change-of-direction events: heading change >= 45 degrees within 0.5 s at entry speed >= 3.0 m/s, with exit speed and time to regain 90% of entry speed (s).",
        "Recomputes from smoothed tracks; count per minute reported with coverage (R-PL-05).", "New table or accel_efforts kind = cod (heading_change_deg, entry_speed_mps, exit_speed_mps, recovery_s).", prio=3))
L("E.01.07", "Falls and players on the floor", "", req="R-DT-01 R-DT-10", t="player_positions.stance", s="C")
L("E.01.08", "Landing space of jump shooters", "Defender entering the shooter's landing space (2026-27 point of emphasis).", r="Points of Emphasis 7; App. VIII 'landing space'", req="", t="", s="M",
  gap=G("DF", "Should", "For every jump shot, the closest defender's distance to the shooter's landing point (m) at landing, and a flag when < 0.5 m.",
        "Distance recomputes from tracks; landing point within 0.3 m of gold on 100 shots (proposal).", "New columns shots.landing_def_dist_m (m), shots.landing_space_flag.", prio=3))

D("E.02", "Ball handling", "")
L("E.02.01", "Touches, touch time and hand", "", req="R-EV-04", t="touches.touch_time_s touches.hand touches.dribbles", s="C")
L("E.02.02", "Dribble count and dribble hand", "", req="R-BL-06 R-EV-04", t="dribbles.hand touches.dribbles", s="C")
L("E.02.03", "Dribble moves (crossover, between legs, behind back, hesitation, spin, retreat)", "", req="R-EV-05", t="dribbles.move_type", s="C")
L("E.02.04", "Other dribble moves (in-and-out, push/speed, pound, snatch-back, half spin)", "", req="R-EV-05", t="dribbles.move_type", s="P",
  gap=G("EV", "Should", "Dribble-move vocabulary adds in-and-out, push (speed) dribble, pound/control dribble, snatch-back and half spin.",
        ">= 75% correct on 300 labelled moves including the new classes (as R-EV-05).", "dribbles.move_type add in_and_out, push, pound, snatch_back, half_spin.", prio=3))
L("E.02.05", "Drives", "Dribble move gaining >= 3 m toward the rim.", req="R-EV-06", t="drives.depth_gain_m drives.direction drives.result", s="C")
L("E.02.06", "Fakes (shot fake, pass fake, jab step)", "Deceptive moves and whether the defender bit.", req="", t="", s="M",
  gap=G("EV", "Shall", "Fake events: shot fake (ball raised >= 0.3 m toward shooting pocket without release), pass fake and jab step (lead foot moves >= 0.3 m and returns within 0.6 s), each with the on-ball defender's reaction (left feet / lifted / no reaction) and the value change after.",
        "Recall >= 80% and precision >= 80% on 200 labelled fakes (proposal); defender reaction correct >= 80%.", "New event family `fake` in events; new table `fakes` (game_id, fake_id, touch_id, kind, ts_ms, defender_id, defender_reaction, value_delta).", prio=2))
L("E.02.07", "Time of possession per player", "", req="R-PC-10", t="touches.touch_time_s", s="C")
L("E.02.08", "Ball pressure on the handler", "Nearest-defender distance during the touch.", req="R-CO-01", t="touches.pressure_m", s="C")

D("E.03", "Passing", "")
L("E.03.01", "Pass types (11 + unseen)", "", req="R-EV-02", t="passes.pass_type", s="C")
L("E.03.02", "Pass metrics (speed, distance, angle, lane openness)", "", req="R-EV-02 R-CG-07", t="passes.speed_mps passes.distance_m passes.angle_change_deg passes.lane_openness_m", s="C")
L("E.03.03", "Pass outcome (completed, deflected, intercepted, thrown away)", "", req="R-EV-02", t="passes.outcome", s="C")
L("E.03.04", "Pass chain (assist, hockey assist, potential assist, screen assist)", "", req="R-EV-03", t="passes.chain_role passes.is_official_assist screens.is_screen_assist", s="C")
L("E.03.05", "Receiver's first action", "", req="R-EV-02", t="passes.receiver_first_action", s="C")
L("E.03.06", "Pass delivery (one/two hands, off the dribble, no-look)", "", req="", t="", s="M",
  gap=G("EV", "Should", "Pass delivery attributes: one- or two-handed, off the dribble vs from a hold, no-look (head yaw > 45 degrees from the pass direction at release).",
        ">= 80% correct on 300 labelled passes where the passer is >= the readable size (R-ID-05).", "New columns passes.hands (one/two), passes.off_dribble (bool), passes.no_look (bool).", prio=3))
L("E.03.07", "Throw-in passes", "First pass of a throw-in.", req="R-DT-14", t="restarts.thrower_player_id", s="P",
  gap=G("EV", "Shall", "Every throw-in pass is a passes row flagged is_throw_in, linked to its restart, so inbound passing and pressure are measured like other passes.",
        "100% of throw-ins with a visible release have a passes row with is_throw_in = true.", "New columns passes.is_throw_in (bool), passes.restart_id.", prio=2))
L("E.03.08", "Lobs and alley-oops", "", req="R-ST-26", t="passes.pass_type shots.shot_type_code", s="C")

D("E.04", "Shooting", "")
L("E.04.01", "Shot type", "Catch-and-shoot, pull-up, step-back, floater, layup, dunk, alley-oop, hook, tip-in, putback, post move, fadeaway.", req="R-EV-07", t="shots.shot_type_code", s="C")
L("E.04.02", "Layup and finish subtypes", "Reverse, Euro step, finger roll, scoop, up-and-under, power, off one or two feet.", req="R-EV-07", t="shots.layup_hand", s="P",
  gap=G("EV", "Should", "Finish subtype per layup or dunk: reverse, Euro step, finger roll, scoop, up-and-under, power (two-foot), off one foot, with the finishing hand.",
        ">= 75% correct on 300 labelled finishes (proposal).", "New column shots.finish_subtype (enum).", prio=3))
L("E.04.03", "Shot location (release x, y, r, theta, zones)", "", req="R-EV-07 R-CG-05 R-SY-07", t="shots.release_r_m shots.release_theta_deg shots.release_sector_15deg shots.ncaa_shot_zone", s="C")
L("E.04.04", "Contest (closest defender, closing speed)", "", req="R-EV-07 R-VL-04", t="shots.contest_distance_m shots.closing_speed_mps shots.closest_defender_id", s="C")
L("E.04.05", "Contest form (hand up, high/low hand, contest height)", "Whether and how the defender's hand contests the release.", req="R-PL-07", t="", s="P",
  gap=G("EV", "Shall", "Each shot stores the contest form from pose: hand up (yes/no), contest hand height relative to the release point (m), hand-to-ball distance at release (m), and whether the defender left his feet.",
        "Hand-up label correct >= 85% on 300 labelled shots; hand-to-ball distance within 0.3 m where both are visible (proposal).", "New columns shots.contest_hand_up, shots.contest_hand_height_m, shots.hand_to_ball_m, shots.contest_airborne.", prio=1))
L("E.04.06", "Release attributes (height, time, arc, entry angle)", "", req="R-PL-07 R-CG-11", t="shots.release_height_m shots.release_time_s shots.arc_deg shots.entry_angle_deg", s="C")
L("E.04.07", "Shot context (dribbles before, touch time, shot clock, off a screen)", "", req="R-EV-07", t="shots.dribbles_before shots.touch_time_before_s shots.shot_clock_s", s="C")
L("E.04.08", "Rim outcome, bank shot, block, and-one", "", req="R-BL-08 R-EV-07 R-MB-07", t="shots.rim_outcome shots.bank shots.blocked shots.and_one", s="C")
L("E.04.09", "Assisted vs self-created", "", req="R-EV-03 R-EV-07", t="shots.assisted_official shots.assister_video_id", s="C")
L("E.04.10", "Shot quality", "", req="R-VL-04", t="shots.shot_quality_xpts", s="C")
L("E.04.11", "End-of-period heaves", "", req="R-MB-06", t="shots.is_heave", s="C")
L("E.04.12", "Shooter's footwork into the shot", "1-2 step, hop, turnaround, fade, spin-off.", req="", t="shots.shot_type_code", s="P",
  gap=G("EV", "Should", "Jump-shot footwork per shot: 1-2 step, hop, turnaround, fade, spin, sidestep, step-back (already a type), from pose.",
        ">= 75% correct on 300 labelled jumpers (proposal).", "New column shots.footwork (enum).", prio=3))

D("E.05", "Rebounding", "")
L("E.05.01", "Offensive and defensive rebounds, team rebounds", "", req="R-EV-08", t="rebounds.off_def rebounds.is_team_rebound", s="C")
L("E.05.02", "Contested, long/short, tip-outs", "", req="R-EV-08", t="rebounds.contested rebounds.long_short rebounds.tip_out", s="C")
L("E.05.03", "Box-outs", "", req="R-EV-08 R-DT-16", t="box_outs.boxer_id box_outs.result", s="C")
L("E.05.04", "Crashers and leakers", "", req="R-EV-08", t="rebounds.crashers_off rebounds.crashers_def rebounds.leaker_ids", s="C")
L("E.05.05", "Rebound positioning at the release", "Each player's position and inside position (goal side of an opponent) when the shot is released.", req="", t="configuration_snapshots.trigger", s="P",
  gap=G("EV", "Should", "At every missed-shot release, store each player's distance to the rim (m) and whether he holds inside position on his nearest opponent; and at the rebound, the ball's landing distance (m) and angle (degrees).",
        "Recomputes from configuration snapshots at trigger = shot_release; rebound landing point within 0.5 m on 100 labelled misses (proposal).", "rebounds: new columns landing_r_m, landing_theta_deg; configuration_snapshots trigger shot_release used.", prio=2))

D("E.06", "Screening (individual)", "")
L("E.06.01", "Setting a screen", "Screener stationary with contact; strict and loose rules.", req="R-ST-02 R-ST-17", t="screens.screener_id screens.strict_rule_fired screens.loose_rule_fired", s="C")
L("E.06.02", "Screen geometry (angle, contact distance, duration)", "", req="R-CG-07 R-ST-02", t="screens.screen_angle_deg screens.contact_distance_m screens.duration_s", s="C")
L("E.06.03", "Screener's action after (roll, pop, slip, short roll, ghost)", "", req="R-ST-18", t="screens.screener_action_after", v="OFF.F5.4", s="C")
L("E.06.04", "Illegal (moving) screens", "Offensive fouls for illegal screens.", r="4-35, App. III (screening)", req="", t="fouls.foul_subtype", s="P",
  gap=X("(see A.06.17 contact-type proposal)", note="Illegal screen becomes a contact type; also add screens.illegal_called (bool) linking to the foul."))

D("E.07", "Cuts and off-ball movement", "")
L("E.07.01", "Cut types (basket, backdoor, flare, curl, straight, shallow)", "", req="R-ST-01", t="movement_primitives.primitive_type", s="C")
L("E.07.02", "Named cuts (UCLA, Iverson, zipper, flash, V-cut, L-cut, shuffle, rip, Euro)", "The cut vocabulary of OFF.F8.2 not in the primitive list.", req="R-ST-01 R-ST-04", t="movement_primitives.primitive_type", v="OFF.F8.2", s="P",
  gap=G("ST", "Shall", "Movement-primitive cut vocabulary equals the OFF.F8.2 cut list (UCLA, Iverson, zipper, flash, V-cut, L-cut, shuffle, rip, Euro, dive, back cut) with one geometric signature each (m, degrees, s, m/s).",
        "Every OFF.F8.2 cut has a primitive code and signature; F1 >= 0.80 per cut on >= 50 labelled instances (proposal).", "movement_primitives.primitive_type enum := OFF.F8.2 cut codes.", prio=2))
L("E.07.03", "Relocate, lift, drift, rim run, corner sprint", "", req="R-ST-01", t="movement_primitives.primitive_type", s="C")
L("E.07.04", "Off-ball gravity", "Defender displacement caused by a player.", req="R-VL-06", t="value_credits.defender_displacement_m", s="C")

D("E.08", "Post play", "")
L("E.08.01", "Post touches and entries", "", req="R-DF-07", t="post_touches.post_zone post_touches.entry_pass_id", s="C")
L("E.08.02", "Seal and post positioning", "", req="R-ST-01", t="post_touches.seal", s="C")
L("E.08.03", "Post moves (drop step, hook, up-and-under, face-up, spin)", "", req="R-ST-04", t="post_touches.post_move_code", v="OFF.F7", s="C")
L("E.08.04", "Post dislodging and hook-and-hold", "Illegal post contact (2026-27 point of emphasis 4).", r="Points of Emphasis 4; App. VIII", req="", t="", s="P",
  gap=X("(see A.06.17 contact-type proposal)"))

D("E.09", "On-ball and individual defence", "")
L("E.09.01", "Defensive stance and distance to the handler", "", req="R-DT-10 R-CO-01", t="player_positions.stance touches.pressure_m", s="C")
L("E.09.02", "Containment and blow-bys", "", req="R-EV-06", t="drives.defender_reaction", s="C")
L("E.09.03", "Closeouts (distance, speed, type)", "", req="R-DF-08 R-ST-01", t="reaction_events.closeout_distance_m reaction_events.closeout_speed_mps", s="C")
L("E.09.04", "Contests", "", req="R-EV-09", t="defensive_events.type", s="C")
L("E.09.05", "Steals, deflections, blocks, charges drawn, loose balls", "", req="R-EV-09", t="defensive_events.type defensive_events.recovered_by_team_id", s="C")
L("E.09.06", "Off-ball denial posture", "Denying a passing lane (hand and foot in the lane).", req="R-DF-02", t="defensive_matchups.in_gap", s="P",
  gap=G("DF", "Should", "Per defender-second, a denial flag: defender within 1.5 m of his man, inside the passer-receiver line by >= 0.3 m, with torso facing the ball side.",
        "Agrees with labels on >= 80% of 300 labelled defender-seconds (proposal).", "New column defensive_matchups.deny_posture (bool).", prio=3))
L("E.09.07", "Reaction time and anticipation", "", req="R-CO-02 R-CO-03", t="reaction_events.latency_s", s="C")
L("E.09.08", "Verticality and hands up", "", r="4-39", req="R-DT-10", t="player_positions.hands_up", s="C")

D("E.10", "Free-throw routine", "")
L("E.10.01", "Routine time and dribbles", "", req="R-PL-08 R-SR-09", t="free_throws.release_latency_s player_card.trk_ft_routine_s player_card.trk_ft_dribbles", s="C")
L("E.10.02", "Arc consistency", "", req="R-PL-08", t="player_card.trk_ft_arc_deg_sd", s="C")

D("E.11", "Communication and gestures", "")
L("E.11.01", "Defensive communication proxies", "Clean vs late switches, two defenders on one attacker.", req="R-CO-08", t="screens.coverage_fine_code", s="C")
L("E.11.02", "Play-call signals by players", "Point guard hand or verbal signals calling a set.", req="R-AU-02 R-EV-15", t="play_calls.call_source play_calls.call_text", s="C")
L("E.11.03", "Player gestures toward officials and opponents (taunting, celebration)", "Unsporting acts that risk Class A technicals.", r="10-3", req="", t="", s="M",
  gap=G("CC", "Should", "Log player gestures seen on broadcast (complaint to an official, taunt, celebration) with player, time and any technical that follows.",
        "Every PBP technical has a linked gesture row or 'unseen'; labels agree >= 80% on 100 clips (proposal).", "bench_events.actor_type add on_court_player (rename the table's scope to `conduct_events` later).", prio=3))
