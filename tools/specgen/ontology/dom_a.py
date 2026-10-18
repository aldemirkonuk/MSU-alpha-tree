from core import D, L, G, X

D("A", "Game structure and rules", "Everything the 2026-27 NCAA men's rules book defines about how a game is organised, timed, scored, penalised, restarted, officiated and reviewed.")

# ---------------------------------------------------------------- A.01 Game and periods
D("A.01", "Game, periods and result", "Game objective, periods, intermissions, extra periods, result and abnormal endings (Rules 1-1, 5-2 to 5-9).")
L("A.01.01", "Team's own basket and direction of play", "Each team attacks its own basket; first-half baskets are those farthest from the team bench; teams change baskets at half time.",
  r="1-1.2, 1-1.3", req="R-CG-06", t="state_frame.basket_attacked frames.homography", s="C",
  note="new-IV-21 (change of baskets) is proposed in config/invariants.yaml.")
L("A.01.02", "Halves (2 x 20:00)", "Regulation is two halves of 1200 s; game clock counts down from 20:00.",
  r="5-6.1", req="R-IV-16 R-SR-01 R-MD-01", t="state_frame.period state_frame.game_clock_s", s="C")
L("A.01.03", "End of period and try in flight", "A period ends when the clock reads zero (red light or horn); a goal counts only if the try was released before; a try in flight ends the period when the try ends.",
  r="5-7, 5-1.5, 6-6.1", req="R-MB-06", t="shots.release_before_horn made_basket_events.release_vs_horn made_basket_events.release_game_clock_s", s="C",
  note="Invariant wording proposed as new-IV-23.")
L("A.01.04", "Intermissions (half time, before extra periods)", "Half-time intermission and the 1-minute intermission before each extra period; start, end and length.",
  r="5-8, 5-9", req="R-PL-04", t="state_second.phase state_frame.stoppage_kind", s="P",
  gap=G("SR", "Shall", "Record each intermission (half time and before every extra period) as a stoppage row with start and end video time, duration and the teams' return time to the floor.",
        "Intermission duration within +/- 2 s of the scoreboard countdown or the video cut times on 100% of processed games; every game has exactly 1 + n_OT intermission rows.",
        "timeouts: allow timeout_type = intermission (or a new `intermissions` table: game_id, kind, start_ts_ms, end_ts_ms, duration_s).", prio=3))
L("A.01.05", "Extra periods (overtime)", "Each extra period is 5:00, starts with a jump ball, keeps the second-half baskets and team-foul counts.",
  r="5-9.1 to 5-9.4", req="R-IV-16 R-IV-10 R-EV-14", t="games.overtime_periods jump_balls.kind state_frame.period", s="C",
  note="Team-foul carry-over into extra periods is proposed as new-IV-20.")
L("A.01.06", "Final result and winner", "Final score, winner and score by half; the official scorebook is authoritative.",
  r="5-2, 2-9.13", req="R-FD-01 R-IV-04 R-IV-15 R-DQ-06", t="games.home_score games.away_score games.home_period_points team_box.points", s="C")
L("A.01.07", "Forfeit and no contest", "A forfeit (2-0 unless 30 min played, then the score stands) or a no contest ends a game abnormally.",
  r="5-3", req="", t="games.status", s="P",
  gap=X("new-IV-30", note="Invariant exists only as a proposal; games.status has no forfeit / no_contest values."),
  gap2=G("FD", "Shall", "Game registry status distinguishes forfeited, no-contest and suspended games, with the playing time completed (s) and the rule applied.",
         "games.status takes values final, forfeit, no_contest, suspended, postponed, canceled; for every non-final game the completed playing time is stored in s (+/- 1 s) and the game is excluded from engine training unless status = final.",
         "games.status enum: add forfeit, no_contest, suspended; new column games.playing_time_completed_s (s).", prio=3))
L("A.01.08", "Interrupted or suspended game", "A game interrupted by events beyond the officials' control and resumed or terminated later.",
  r="5-4", req="", t="", s="M",
  gap=G("FD", "Should", "Record interruptions longer than 300 s (floor, lighting, clock failure, emergencies) with cause, game clock at interruption and resumption date-time.",
        "Each interruption row carries game_clock_s (0.1 s), period, cause from a fixed list and resumption UTC; possessions spanning an interruption are flagged and excluded from tempo statistics.",
        "New stoppage cause `interruption` in state_frame.stoppage_kind; new columns games.interrupted (bool), games.resumed_utc.", prio=3))
L("A.01.09", "Game type, season type and round", "Exhibition, non-conference, conference, conference tournament, NCAA tournament (round, seeds), NIT and others.",
  req="R-MD-14 R-CX-15 R-FD-01", t="games.game_type games.season_type games.tournament_round games.home_seed", s="C")
L("A.01.10", "Rules edition in force per game", "Which rules edition (season) and which competition-specific rules apply to a game, e.g. 35 s vs 30 s shot clock, 2025-26 coach's challenge, 2026-27 appeals and logo rules.",
  r="Preface; Rules changes 2025-26 and 2026-27", req="R-TR-18", t="", s="P",
  note="R-TR-18 only mentions the shot-clock era for transition thresholds.",
  gap=G("RL", "Shall", "Every game row carries a rules_edition_id that points to a versioned rules configuration (config/rules_ncaa_men_<season>.yaml) holding every rule-derived constant (clock lengths, shot-clock values, foul limits, timeout allotments, court marks, challenge rules) with its rule citation; every check and simulation reads constants from that edition only.",
        "100% of games have a rules_edition_id; a test changes one constant in a copy of the edition and every dependent check changes result; 0 rule constants hard-coded in code (grep test).",
        "New config files config/rules_ncaa_men_<season>.yaml (merge of court_ncaa_men.yaml constants and invariants.yaml constants); new column games.rules_edition_id.", prio=1))

# ---------------------------------------------------------------- A.02 Game clock
D("A.02", "Game clock", "Starting, stopping, displaying and correcting the game clock (Rules 1-18, 5-10 to 5-12).")
L("A.02.01", "Game clock value and display", "Seconds remaining in the period; tenths shown under 60 s.",
  r="1-18.2, 5-10", req="R-SR-01 R-SY-01 R-MD-01", t="state_frame.game_clock_s scoreboard_ocr.game_clock_parsed_s", s="C")
L("A.02.02", "Game clock start triggers", "The clock starts when a throw-in is legally touched inbounds, a jump ball is legally tapped, or a missed live free throw is touched.",
  r="5-10.1 to 5-10.3", req="R-IV-05 R-SR-01", t="state_frame.clock_running restarts.video_ts_ms_live", s="P",
  gap=G("SR", "Shall", "Store for every clock start the trigger (throw-in touch, jump-ball tap, free-throw touch, period start) and the delay between the trigger frame and the first frame the clock is seen running.",
        "Trigger correct on >= 95% of clock starts in gold-v1 (proposal); median start delay reported per game in s; delays > 1.0 s flagged as timing-mistake candidates (Rule 5-12).",
        "New columns restarts.clock_start_trigger (enum) and restarts.clock_start_delay_s (s).", prio=2))
L("A.02.03", "Game clock stop events", "The clock stops on whistles, at period end and after a made field goal in the last 59.9 s of the second half and extra periods.",
  r="5-11, 2-10.12", req="R-IV-05 R-IV-06 R-SR-01", t="state_frame.clock_running state_frame.live_ball", s="C")
L("A.02.04", "Minimum time off on a touch (0.3 s) and tap-only rule", "In the last 59.9 s at least 0.3 s comes off on a touch followed by a stop; with 0.3 s or less only a tap can score.",
  r="5-10.2.d, 5-10.3.d, 5-1.19", req="", t="shots.release_before_horn", s="P",
  gap=X("new-IV-22", note="Proposed invariant; needs adoption in the live doc."))
L("A.02.05", "Timing mistakes and corrections", "Corrections of the game clock by the officials within the same half using a replay or a timer's record.",
  r="5-12, 2-12", req="R-IV-05 R-SB-01 R-SR-04", t="reviews.review_kind reviews.game_clock_before_s reviews.game_clock_after_s", s="C",
  note="Statute 'within the half' is proposed as new-IV-27.")
L("A.02.06", "Video time to game clock map", "Monotonic mapping between video timestamps and game clock inside each running stretch.",
  req="R-MD-08 R-SY-02", t="events.sync_residual_s state_frame.video_ts_ms state_frame.clock_inferred", s="C")

# ---------------------------------------------------------------- A.03 Shot clock
D("A.03", "Shot clock", "Shot-clock periods, starts, resets, turning off and violations (Rules 1-19, 2-11, 9-11).")
L("A.03.01", "Shot clock value and status", "Seconds remaining (or off) every frame.",
  r="2-11.1, 1-19", req="R-SR-01 R-SY-01", t="state_frame.shot_clock_s state_frame.shot_clock_status", s="C")
L("A.03.02", "Shot clock start", "Starts when a throw-in is touched inbounds, on initial control after a jump ball or a missed try, or on change of team control.",
  r="2-11.5", req="R-MD-06 R-IV-07", t="chances.start_shot_clock_s chances.shot_clock_start_rule", s="C", note="Also proposed as new-IV-01.")
L("A.03.03", "Reset to 30 s", "Change of team control and the other 2-11.6.b situations.",
  r="2-11.6.b", req="R-MD-06 R-SY-08 R-SY-09 R-IV-07", t="shot_clock_resets.value_after_s shot_clock_resets.rule_citation", s="C")
L("A.03.04", "Reset to 20 s flat (offensive rebound after ring contact)", "Offence gains control in its frontcourt after a try that touched the ring: exactly 20 s.",
  r="2-11.6.d.1 to d.9", req="R-MD-06 R-SY-09 R-MB-07 R-IV-07", t="shot_clock_resets.rule_expected_after_s chances.shot_clock_start_s", s="C")
L("A.03.05", "Reset to max(20, remaining)", "Defensive foul or kicked/fisted ball with a frontcourt throw-in before ring contact.",
  r="2-11.6.c", req="R-MD-06 R-IV-07", t="shot_clock_resets.value_after_s shot_clock_resets.rule_match", s="C")
L("A.03.06", "No-reset situations", "Unexpired time continues: ball out of bounds off the defence, injury, end of timeout, arrow to team in control, technical on the team in control, etc.",
  r="2-11.6.a.1 to a.9", req="R-SY-08 R-SY-09", t="shot_clock_resets.cause", s="P",
  note="shot_clock_resets.cause has 6 coarse values; config/invariants.yaml shot_clock_reset_table has 33 causes.",
  gap=G("SY", "Shall", "Shot-clock reset and no-reset events use the full cause list of the rules (every 2-11.6.a/b/c/d article and 2-11.2 off) as their cause vocabulary, including no-reset stoppages, so every stoppage with a live shot clock has a recorded expected value.",
        "shot_clock_resets.cause takes one of the 33 causes in config/invariants.yaml shot_clock_reset_table; >= 95% of stoppages with the shot clock on carry a cause; rule_match computed on 100% of them.",
        "shot_clock_resets.cause enum := shot_clock_reset_table causes (keep the 6 coarse values as cause_coarse).", prio=1))
L("A.03.07", "Shot clock off and reactivation", "Shot clock turned off when the game clock is below a shot-clock period; reactivated at 20 s in 2-11.6.d cases.",
  r="2-11.2, 2-11.8", req="R-MD-06 R-IV-07", t="state_frame.shot_clock_status shot_clock_resets.after_class", s="C", note="Also new-IV-05.")
L("A.03.08", "Shot-clock violation and horn vs release", "Violation unless the try was released before the horn and then touched the ring or entered the basket.",
  r="9-11, 2-11.3", req="R-EV-10 R-MB-06", t="turnovers.turnover_type made_basket_events.release_shot_clock_s", s="C", note="Also new-IV-06.")
L("A.03.09", "Single working shot clock", "One working shot clock is allowed when the other fails (2025-26).",
  r="1-19 (2025-26 change)", req="R-IV-07", t="scoreboard_ocr.display", s="C")

# ---------------------------------------------------------------- A.04 Control, possession, alternating possession
D("A.04", "Control, possession and jump balls", "Player and team control, our possession and chance units, jump balls, held balls and the alternating-possession arrow (Rules 4-9, 6-2 to 6-4).")
L("A.04.01", "Player control and team control", "A player holds or dribbles a live ball; team control continues through passes and ends on a try, loss or opponent control.",
  r="4-9", req="R-MD-02 R-SR-06", t="state_frame.ball_control_state ball_control_state.state", v="global_metadata.ball_control_state", s="C")
L("A.04.02", "Possession (our definition)", "A possession ends only when the other team gains control; offensive rebounds stay inside it.",
  req="R-MD-04 R-SY-04 R-SY-06", t="possessions.possession_id possessions.start_type_code possessions.end_type", v="TR.ST", s="C")
L("A.04.03", "Chance", "A new chance starts at each offensive rebound or shot-clock reset inside a possession.",
  req="R-MD-04 R-SY-05 R-PE-02", t="chances.chance_number chances.start_cause chances.end_type chances.outcome_code", s="C")
L("A.04.04", "Possession counts under each source's definition", "KenPom/Torvik formula possessions, CBBD and hoopR NCAA-engine possession numbers and Synergy-style chances stored side by side with ours.",
  req="R-IV-15", t="possessions.poss_num_ncaa team_box.possessions_source", s="P",
  gap=G("SY", "Shall", "Store per team per game the possession count under every source definition in use (ours, FGA - ORB + TO + 0.475 x FTA, Torvik, CBBD, hoopR NCAA engine, Synergy-style chances), with each source's definition text, and report the differences.",
        "All definitions present for 100% of games with PBP; our count within +/- 2 of the formula estimate in >= 95% of games (proposal); every difference > 3 listed for review.",
        "New table `possession_counts` (game_id, team_id, definition_code, count, definition_ref) or columns on team_box.", prio=2))
L("A.04.05", "Opening and overtime jump balls", "Jump ball at the centre circle starts the game and each extra period.",
  r="6-2", req="R-EV-14 R-DT-15", t="jump_balls.kind jump_balls.tip_winner_team_id jump_balls.tip_direction_deg", s="C")
L("A.04.06", "Held ball", "Simultaneous possession by opponents; resolved by the arrow after the opening tip.",
  r="6-4.2", req="R-RF-07 R-IV-08 R-DT-15", t="jump_balls.held_ball_player_ids events.event_family", s="C")
L("A.04.07", "Alternating-possession arrow", "Arrow set after the opening jump, flips after each alternating-possession throw-in ends; direction reverses at half time.",
  r="6-3, 6-4", req="R-MD-12 R-SY-01 R-SR-05", t="state_frame.possession_arrow restarts.arrow_before restarts.arrow_after", s="C", note="Arrow rules proposed as new-IV-19.")
L("A.04.08", "Jump-ball violations", "Tossing official's toss, non-jumpers entering the circle early, jumper catching the tossed ball, etc.",
  r="9-8", req="", t="jump_balls.kind", s="P",
  gap=G("EV", "Should", "Record jump-ball violations (who, which article) and re-jumps on every jump ball.",
        "Every jump ball has violation = none or a 9-8 article; re-jumps stored as kind = rejump; 100% agreement with PBP where PBP logs the violation.",
        "New column jump_balls.violation_code (Rule 9-8 article or none).", prio=3))
L("A.04.09", "Live ball and dead ball", "When the ball becomes live (jump, throw-in, free throw) and dead (goal, whistle, period end).",
  r="6-1, 6-5, 6-6", req="R-SR-01 R-MD-05", t="state_frame.live_ball restarts.dead_ball_reason", s="C")
L("A.04.10", "Point of interruption", "Play resumes where it was interrupted (e.g. double foul, inadvertent whistle).",
  r="4-28, 7-5", req="R-SR-08", t="restarts.restart_type", s="C")
L("A.04.11", "Inadvertent whistle", "An official sounds the whistle in error.",
  r="4-20", req="R-SR-08", t="restarts.dead_ball_reason whistles.link_type", s="C")
L("A.04.12", "Frontcourt and backcourt status of team control", "Whether the team in control has established the ball in its frontcourt (ball and both feet), basis of backcourt rules.",
  r="4-23, 9-12", req="R-IV-14", t="player_positions.court_half", s="P",
  gap=G("SR", "Shall", "State every frame whether the team in control has frontcourt status, with the frame it was established and the player and ball positions that established it.",
        "Frontcourt-status changes within +/- 0.2 s of gold on >= 95% of possessions (proposal); ball and feet positions from tracking with mapping error <= 0.30 m median.",
        "New columns state_frame.frontcourt_status (bool) and state_frame.frontcourt_established_ts_ms.", prio=2))
L("A.04.13", "10-second backcourt count", "Team must bring the ball into its frontcourt within 10 s.",
  r="9-10", req="R-IV-14", t="turnovers.turnover_type", s="P",
  gap=G("SR", "Shall", "Store a running 10-second backcourt count per frame from the start of team control in the backcourt (reset rules per 9-10), and the time each possession reaches the frontcourt.",
        "Backcourt count within +/- 0.2 s of a hand-timed count on >= 95% of possessions (proposal); every 10-second violation in PBP has a count >= 10.0 s.",
        "New column state_frame.backcourt_count_s (s, 0.1 s); possessions.frontcourt_entry_s (s since control).", prio=2))
L("A.04.14", "Closely guarded 5-second count", "A frontcourt player holding the ball, guarded within 1.83 m, may not hold it for 5 s.",
  r="9-14, 4-17.2", req="R-EV-10", t="turnovers.turnover_type touches.pressure_m", s="P",
  gap=X("new-IV-15", note="Invariant proposed; still needs a per-touch count column."),
  gap2=G("SR", "Should", "Store the closely-guarded count per touch: seconds the holder spends holding (not dribbling) in the frontcourt with the same defender within 1.83 m.",
         "Count within +/- 0.3 s of a hand-timed count on >= 90% of 100 labelled touches (proposal); guard distance from tracking (m).",
         "New column touches.closely_guarded_hold_s (s).", prio=3))
L("A.04.15", "Three seconds in the lane", "No offensive player stays in the frontcourt lane > 3 s while his team controls the ball.",
  r="9-9", req="R-EV-10", t="turnovers.turnover_type player_positions.x_m", s="P",
  gap=X("new-IV-17", note="Invariant proposed."),
  gap2=G("ST", "Should", "Store continuous lane time per offensive player (s) and the longest stay per chance, as a measure of post pressure and of 3-second risk.",
         "Lane time recomputes from player positions (lane = |x| <= 1.83 m, y <= 5.79 m from the end line) within 0.1 s; every PBP 3-second violation shows a stay >= 3.0 s.",
         "New column chances.max_lane_stay_s and per-player aggregate in profile_snapshots.", prio=3))

# ---------------------------------------------------------------- A.05 Scoring
D("A.05", "Scoring", "How points are scored, awarded or cancelled (Rules 5-1, 9-6, 9-15, 9-16).")
L("A.05.01", "Two- and three-point field goals", "Value of a goal from the shooter's last floor contact relative to the 6.75 m arc (6.60 m corners).",
  r="5-1, 1-7", req="R-IV-12 R-EV-07 R-MB-04", t="shots.value_attempted shots.is_three_by_geometry", s="C")
L("A.05.02", "Free-throw point", "A successful free throw scores 1.",
  r="5-1.3, 8", req="R-IV-04", t="free_throws.made score_events.delta_points", s="C")
L("A.05.03", "Goaltending and basket interference awards", "Points awarded without the ball going through; violations at a team's own basket award none; hand on ring is basket interference (2025-26).",
  r="9-15, 9-15.2 (2025-26 change)", req="R-MB-05", t="made_basket_events.edge_case", s="C", note="Award rules proposed as new-IV-24.")
L("A.05.04", "Illegal assistance in scoring or blocking", "Lifting or assisting a teammate to score or block awards the try's points or a violation.",
  r="9-16", req="", t="made_basket_events.edge_case", s="P", gap=X("new-IV-24"))
L("A.05.05", "Goal in the wrong basket", "A ball accidentally put in the opponent's basket counts for the opponent (credited to its captain); deliberately is a violation.",
  r="5-1.2", req="R-MB-05", t="score_events.event_kind", s="P",
  gap=G("MB", "Should", "Label own-basket goals as an edge case of made-basket detection, with the team credited and the player who touched it last.",
        "Edge case present in the MB test set; credited team equals PBP on 100% of cases.",
        "made_basket_events.edge_case: add wrong_basket_goal; score_events.event_kind value own_basket.", prio=3))
L("A.05.06", "Score corrections and correctable errors", "Scorer mistakes corrected later in the game, with the time limits of 2-12.",
  r="2-12, 2-9.13", req="R-SB-01 R-SB-02 R-SR-02", t="reviews.review_kind score_events.review_id state_corrections.corrected_value", s="C")

# ---------------------------------------------------------------- A.06 Fouls and penalties
D("A.06", "Fouls and penalties", "Every foul class of Rule 4-15 and Rule 10, the bonus, disqualification and ejection, and the contact types officials signal.")
L("A.06.01", "Common personal foul (non-shooting)", "Personal foul that is not flagrant, double, multiple or simultaneous.",
  r="4-15.2.a, 10-1", req="R-RF-03 R-SR-03", t="fouls.foul_type fouls.foul_subtype", s="C")
L("A.06.02", "Shooting foul", "Foul on a player in the act of shooting; award by try value and result.",
  r="4-1, 4-8, 10-1 Penalty", req="R-RF-03 R-SR-09", t="fouls.foul_type fouls.shot_value_fouled fouls.ft_awarded", s="C")
L("A.06.03", "Player-control foul", "Common foul by the player in control or an airborne shooter (no free throws).",
  r="4-15.2.a.1", req="R-SR-03", t="fouls.foul_subtype foul_state.player_control_fouls", s="C")
L("A.06.04", "Team-control foul", "Common foul by a player of the team in control (no free throws unless loose-ball).",
  r="4-15.2.a.2", req="R-SR-03", t="fouls.foul_subtype foul_state.team_control_fouls", s="C")
L("A.06.05", "Loose-ball foul", "Common foul when no team is in control.",
  r="4-15.2.a.3, 4-24", req="R-SR-03 R-RF-03", t="fouls.foul_type foul_state.loose_ball_fouls", s="C")
L("A.06.06", "Blocking vs charging and the restricted area", "Block/charge adjudication, legal guarding position, secondary defender in the restricted area.",
  r="4-5, 4-7, 4-17, 4-31, 4-36", req="R-EV-09 R-RF-04", t="defensive_events.type fouls.foul_subtype official_positions.signal_pose", s="P",
  note="foul_subtype has no `blocking` value; the restricted-area status of the secondary defender is not stored.",
  gap=G("RF", "Shall", "Every block or charge call stores the defender's feet position relative to the restricted-area arc (inside, on, outside; distance in m), whether he was a secondary defender, his time set before contact (s) and the call.",
        "RA status from tracking with arc distance error <= 0.15 m on 100 labelled calls (proposal); call equals PBP on 100% of PBP-coded charges.",
        "fouls.foul_subtype add blocking; new columns fouls.defender_ra_dist_m (m), fouls.secondary_defender (bool), fouls.defender_set_time_s (s).", prio=1))
L("A.06.07", "Double and simultaneous personal fouls", "Two opponents foul each other at about the same time; no free throws.",
  r="4-15.2.b, 10-1", req="R-SR-03", t="fouls.foul_subtype foul_state.double_simultaneous_fouls", s="C", note="Penalty proposed as new-IV-32.")
L("A.06.08", "Multiple, false double and false multiple fouls", "Two or more teammates foul one opponent; separate fouls with time between them.",
  r="4-15, 8-8, 8-9, 10-1 Penalty b", req="R-SR-09", t="free_throws.award_type", s="P",
  gap=G("RF", "Should", "Foul subtype vocabulary includes multiple, false double and false multiple fouls, linked to their free-throw sequences.",
        "Subtype present on every such foul; free-throw attempts per sequence equal the award table on 100% of cases.",
        "fouls.foul_subtype add multiple, false_double, false_multiple.", prio=3))
L("A.06.09", "Flagrant 1", "Excessive or unnecessary contact, including deliberate fouls away from the ball to stop the clock; 2 FTs plus the ball.",
  r="4-15.2.c.1", req="R-RF-03 R-SR-03", t="fouls.foul_type foul_state.flagrant1_fouls foul_state.flagrant1_player_cum", s="C")
L("A.06.10", "Flagrant 2 and ejection", "Excessive and severe contact; 2 FTs, ball, ejection.",
  r="4-15.2.c.2, 4-14", req="R-RF-03 R-SR-03", t="fouls.foul_type player_box.ejected foul_state.flagrant2_fouls", s="C")
L("A.06.11", "'Intentional' foul label vs the rules book", "The live doc's 9 foul types include `intentional`; the 2026-27 rules book has no intentional-foul class (deliberate fouls are common fouls or Flagrant 1).",
  r="4-15", req="R-RF-03", t="fouls.foul_type fouls.is_end_game_intentional", s="P",
  gap=G("RF", "Shall", "Foul types follow the 2026-27 rules book classes; the legacy label `intentional` is kept only as a source mapping: deliberate end-game fouls are stored as common fouls with is_end_game_intentional = true, and away-from-ball clock fouls as flagrant_1.",
        "0 rows with foul_type = intentional after mapping; the mapping table covers 100% of source foul labels; counts per class equal the box score.",
        "fouls.foul_type enum: drop `intentional` (keep in a source-label map in config/vocabulary_map.yaml); keep is_end_game_intentional.", prio=1))
L("A.06.12", "Technical foul Class A", "Unsporting technical; 2 FTs; counts toward the team fouls and toward disqualification.",
  r="10-3", req="R-SR-03 R-RF-03", t="fouls.foul_subtype foul_state.technical_class_a", s="C")
L("A.06.13", "Technical foul Class B", "Minor technical (e.g. hanging on the ring); 1 FT; not a team foul.",
  r="10-4", req="R-SR-03", t="fouls.foul_subtype foul_state.technical_class_b", s="C")
L("A.06.14", "Administrative technical", "Technical for administrative infractions (roster, timeouts, noise); 1 or 2 FTs.",
  r="10-2", req="R-SR-03", t="foul_state.technical_admin free_throws.award_type", s="P",
  gap=G("RF", "Should", "fouls rows distinguish administrative technicals with the 10-2 article that applied.",
        "foul_subtype = administrative_technical with a 10-2 article on 100% of such fouls; FT count equals the award table.",
        "fouls.foul_subtype add administrative_technical; new column fouls.rule_article.", prio=3))
L("A.06.15", "Fouls by bench personnel and coaches", "Fouls charged to the bench, head coach or assistants.",
  r="10-3, 10-4, 4-4", req="R-RF-03 R-CC-03", t="fouls.offender_type bench_events.event_type", s="C")
L("A.06.16", "Contact dead-ball technical", "Contact during a dead ball (unless flagrant).",
  r="10-3", req="R-SR-03", t="fouls.foul_subtype", s="C")
L("A.06.17", "Foul contact mechanism (signal type)", "How the foul was committed: holding, pushing/charging, hand-check, illegal use of hands, blocking, tripping, hit to the head, chucking, pinning, dislodging, verticality, landing space, illegal screen, elbow.",
  r="App. VIII signals; App. III; 4-18, 4-19, 4-35, 4-39, 10-1.4", req="R-RF-04", t="official_positions.signal_pose", s="P",
  note="R-RF-04 (Should) reads only 6 signals; no column stores the contact mechanism of a foul.",
  gap=G("RF", "Shall", "Every foul stores its contact mechanism from the Appendix VIII foul-signal list (holding, pushing, hand-check, illegal use of hands, blocking, player/team control, tripping, hit to head, excessive contact, chucking, pinning a defender, dislodging with knee or lower body, vertical-cylinder violation, landing space, illegal screen), from the official's signal or video, with source.",
        "Mechanism present (or `unseen`) on 100% of fouls; agrees with labelled gold on >= 80% of 300 fouls (proposal).",
        "New column fouls.contact_type (enum from App. VIII); official_positions.signal_pose enum extended to App. VIII.", prio=1))
L("A.06.18", "Team fouls, bonus and double bonus", "Team fouls per half; one-and-one from the 7th, two shots from the 10th.",
  r="8-2, 4-26", req="R-MD-07 R-SR-03 R-IV-09", t="state_frame.team_fouls_msu state_frame.bonus_state foul_state.bonus_reached_clock_s", s="C")
L("A.06.19", "Disqualification (5 fouls, 3 Flagrant 1)", "Disqualified at the 5th personal + Class A foul or 3rd Flagrant 1; replaced within 20 s.",
  r="4-12, 10-1", req="R-IV-03 R-MD-16", t="foul_state.disqualified fouls.fouled_out", s="C", note="Full rule proposed as new-IV-11.")
L("A.06.20", "Ejection", "Removal for Flagrant 2, two Class A technicals, or other combinations; head-coach ejections.",
  r="4-14, 10-3, 10-4", req="R-RF-03", t="player_box.ejected events.event_family", s="P",
  gap=X("new-IV-11", note="Ejection combinations proposed; no requirement names an ejection record with cause."))
L("A.06.21", "Fighting and suspensions", "Fighting, suspensions and failure to serve them (2025-26 change).",
  r="10-5, 10-14 Penalty, 10-15.10", req="", t="", s="M",
  gap=G("RF", "Should", "Record fighting incidents and the suspensions that follow (player, games suspended, games served) in the player availability log.",
        "Every PBP or public fighting report has a row; availability.status = out with reason `suspension` for each suspended game.",
        "availability.status add `suspended`; events.event_family value `fight`.", prio=3))
L("A.06.22", "Flopping (faking being fouled)", "Warning, then Class B technical; Class A when confirmed by replay.",
  r="10-3.1.d, App. III (o), 11-2", req="", t="", s="M",
  gap=G("RF", "Should", "Record flopping warnings and technicals, and label suspected flops on review (player, time, contact seen yes/no).",
        "All PBP-logged flop technicals present; suspected flops reviewed with kappa >= 0.6 between labellers (proposal).",
        "fouls.foul_subtype add flop_technical; new event family `flop_warning`.", prio=3))
L("A.06.23", "Take foul and clear-path fouls in transition", "Fouls that stop a break; the NCAA has no clear-path rule, so they are common or flagrant by contact.",
  req="R-TR-25", t="fouls.is_take_foul_candidate fouls.clear_path fouls.fouler_dist_to_ball_m", s="C")
L("A.06.24", "Deliberate end-game fouling", "Fouling to stop the clock when trailing late.",
  req="R-PE-07 R-SR-11", t="fouls.is_end_game_intentional state_second.foul_to_extend_window", s="C")

# ---------------------------------------------------------------- A.07 Free throws
D("A.07", "Free throws", "Awards, shooters, lane positions, requirements, violations and what follows (Rule 8, 9-1).")
L("A.07.01", "Free-throw award type", "Number of attempts and ball after, from the foul class and team-foul count.",
  r="8-1, 8-2, 10-1 Penalty", req="R-SR-09 R-RF-03", t="free_throws.award_type free_throws.attempts_n", s="C", note="Award table in config/invariants.yaml; new-IV-07/08.")
L("A.07.02", "Who attempts (shooter selection)", "Offended player, substitute, opponent's choice for injured player, any player for technicals.",
  r="8-3", req="R-SR-09", t="free_throws.shooter_selection free_throws.shooter_player_id", s="C")
L("A.07.03", "Lane positions", "Up to 6 lane players (4 defence, 2 offence); first spaces for the opponents; lowest spaces empty.",
  r="8-4", req="R-DT-13 R-IV-11", t="free_throws.lane_occupant_ids free_throws.lane_def_count free_throws.lane_expected_empty", s="C", note="Space order proposed as new-IV-29.")
L("A.07.04", "Free-throw requirements (10 s, behind the line)", "Release within 10 s of disposal; shooter behind the line until the ball touches the ring.",
  r="8-5, 9-1", req="R-SR-09 R-PL-08", t="free_throws.release_latency_s free_throws.video_ts_ms_disposal", s="C", note="new-IV-10.")
L("A.07.05", "Free-throw violations", "Shooter, teammate or opponent violations; disconcertion; cancellation or re-shoot.",
  r="9-1", req="R-IV-11", t="free_throws.violation free_throws.violation_team free_throws.result", s="C")
L("A.07.06", "What follows the last free throw", "Live rebound, opponent throw-in, point of interruption or shooting-team throw-in.",
  r="8-6, 8-7", req="R-SR-09 R-IV-08", t="free_throws.ball_after", s="C", note="new-IV-09.")
L("A.07.07", "Free-throw state machine", "ft_pending -> lane_set -> attempt k of n -> result -> next state; prediction at the whistle.",
  req="R-SR-09", t="state_second.ft_state free_throws.predicted_at_whistle free_throws.prediction_correct", s="C")
L("A.07.08", "Substitutions around free throws", "Entry rules during multiple free throws.",
  r="3-6, 8-3", req="R-IV-03", t="substitutions.during_dead_ball", s="P", gap=X("new-IV-25"))

# ---------------------------------------------------------------- A.08 Violations
D("A.08", "Violations", "Every Rule 9 violation as a turnover, restart or cancellation.")
L("A.08.01", "Traveling (incl. pre-dribble and split-step travel)", "Illegal foot movement holding the ball; 2026-27 point of emphasis on pre-dribble and split-step travels.",
  r="9-5, 4-27, 4-22, Points of Emphasis 5", req="R-EV-10 R-DT-16", t="turnovers.turnover_type", s="C")
L("A.08.02", "Illegal dribble (double dribble, palming/carrying)", "Second dribble after ending one; carrying is an illegal dribble.",
  r="9-7, 4-13", req="R-EV-10", t="turnovers.turnover_type", s="C")
L("A.08.03", "Kicking and fisting the ball", "Intentional kick or fist; usually a defensive violation with a shot-clock rule.",
  r="9-6", req="R-SY-08 R-MD-06", t="restarts.violation_code shot_clock_resets.cause", s="C")
L("A.08.04", "Ball through the basket from below", "Violation; cancels any score.",
  r="9-6", req="R-MB-05", t="made_basket_events.edge_case", s="C")
L("A.08.05", "Ball and player out of bounds", "Ball or player touching out of bounds.",
  r="9-2, 9-3, 7-1", req="R-EV-10 R-BL-07", t="turnovers.turnover_type ball_states.out_of_bounds_event", s="C")
L("A.08.06", "Throw-in violations", "Thrower: 5 s, leaving the spot, stepping on the court; defender: crossing the boundary plane.",
  r="9-4", req="R-DT-14", t="restarts.throw_in_count_s restarts.violation_code", s="P",
  gap=G("EV", "Should", "Throw-in violations stored by article (5-second, spot, stepping on court, carrying onto court, defender breaking the plane) with the team and time.",
        "Article present on 100% of PBP throw-in violations; defender plane breaks seen on video stored with the defender ID.",
        "turnovers.turnover_type add throw_in_violation; restarts.violation_code uses 9-4 article strings.", prio=3))
L("A.08.07", "Backcourt violation (over and back)", "Team in control returns the ball to its backcourt after frontcourt status.",
  r="9-12", req="R-IV-14", t="turnovers.turnover_type", s="P",
  note="turnover_type has ten_second_backcourt but no over-and-back value.",
  gap=G("EV", "Shall", "Turnover vocabulary includes the backcourt (over-and-back) violation, separate from the 10-second violation, linked to the frontcourt status that preceded it.",
        "Backcourt turnovers equal PBP counts on 100% of games; each has a frontcourt_established time before it.",
        "turnovers.turnover_type add backcourt_over_and_back.", prio=2))
L("A.08.08", "Shot-clock violation", "Team fails to try for goal within the shot-clock period.",
  r="9-11", req="R-EV-10", t="turnovers.turnover_type", s="C")
L("A.08.09", "Five-second closely guarded and ten-second backcourt", "Count violations.",
  r="9-10, 9-14", req="R-EV-10", t="turnovers.turnover_type", s="C")
L("A.08.10", "Three-second lane violation", "Offensive player in the lane > 3 s.",
  r="9-9", req="R-EV-10", t="turnovers.turnover_type", s="C")
L("A.08.11", "Excessive swinging of elbows", "Violation (not a foul without contact).",
  r="9-13", req="", t="", s="M",
  gap=G("EV", "Should", "Turnover vocabulary includes the elbows violation.",
        "Elbow violations equal PBP counts on 100% of games.", "turnovers.turnover_type add elbows.", prio=3))
L("A.08.12", "Basket interference and goaltending", "Touching the ball on or above the cylinder, or the ring/backboard (hand on ring now BI).",
  r="9-15", req="R-MB-05 R-EV-16", t="made_basket_events.edge_case coaches_challenges.play_type", s="C")
L("A.08.13", "Free-throw lane violations", "Covered under free throws.", r="9-1", req="R-IV-11", t="free_throws.violation", s="C")

# ---------------------------------------------------------------- A.09 Throw-ins
D("A.09", "Out of bounds and throw-ins", "Ball out of bounds, who caused it, spots and throw-in requirements (Rule 7).")
L("A.09.01", "Ball out of bounds detection", "The ball touches a player out of bounds or the floor or objects outside the boundary.",
  r="7-1", req="R-BL-07", t="ball_states.out_of_bounds_event", s="C")
L("A.09.02", "Player who caused the ball out of bounds", "Last player to touch the ball before it went out (or the player out of bounds).",
  r="7-2", req="R-EV-16", t="coaches_challenges.play_type", s="P",
  gap=G("BL", "Shall", "Every out-of-bounds event stores the last player to touch the ball (or the player who was out of bounds), the touch frame and the team awarded the ball, with the call on the floor.",
        "Team awarded equals PBP on 100%; last toucher correct on >= 90% of 200 labelled out-of-bounds plays (proposal).",
        "New columns on ball_states (out_of_bounds_event rows) or a new `out_of_bounds_events` table: last_touch_player_id, last_touch_frame, awarded_team_id.", prio=2))
L("A.09.03", "Throw-in spot", "Designated spot nearest the violation; under the basket below the FT line extended, 28-ft mark above it; end line runnable after a score.",
  r="7-3, 7-4, 7-5; 7-3.2.b (2025-26)", req="R-DT-19 R-SR-08 R-MD-03", t="restarts.throw_in_spot restarts.spot_x_m restarts.spot_y_m", s="C", note="Boundary wording question open in dictionary_state.md item 7.")
L("A.09.04", "Throw-in requirements and 5-second count", "Release within 5 s; designated spot 0.91 m wide.",
  r="7-6", req="R-DT-14", t="restarts.throw_in_count_s", s="C", note="new-IV-16.")
L("A.09.05", "Throw-in formations and first pass", "Stack, box, line, diamond formations; first-pass target.",
  req="R-DT-14 R-ST-23", t="restarts.thrower_player_id configuration_snapshots.alignment_code", v="OFF.F13.2 OFF.F13.3", s="C")
L("A.09.06", "Bench personnel assisting a player out of bounds", "Bench personnel physically assisting a player with the ball (2025-26).",
  r="7-1.1 (2025-26)", req="", t="bench_events.event_type", s="M",
  gap=G("CC", "Should", "Bench events include bench personnel physically assisting a player near the boundary, linked to any resulting technical.",
        "Every such technical in PBP has a bench_events row.", "bench_events.event_type add bench_assist_out_of_bounds.", prio=3))

# ---------------------------------------------------------------- A.10 Timeouts and stoppages
D("A.10", "Timeouts and stoppages", "Team, media, injury and excessive timeouts and the media format (Rules 5-13 to 5-17).")
L("A.10.01", "Team timeouts by length (30/60/75 s)", "Timeouts left per team by type.",
  r="5-13, 5-14", req="R-SR-04 R-MD-07 R-IV-10", t="state_frame.to30_left_msu state_frame.to60_left_msu state_frame.to75_left_msu timeouts.timeout_type", s="C", note="Allotment by format proposed as new-IV-12.")
L("A.10.02", "Media timeouts and media format", "First dead ball at or after 16/12/8/4 (or 15/10/5) minute marks; per-game media format.",
  r="5-14.10", req="R-MD-13 R-SR-04 R-EV-15", t="timeouts.media_slot timeouts.media_format timeouts.became_media", s="C", note="Rules detail in new-IV-13.")
L("A.10.03", "Timeout request and caller", "Head coach or player in control requests; team, player, game and shot clock at the call.",
  r="5-13, 5-14", req="R-EV-15 R-CC-02", t="timeouts.called_by timeouts.requesting_player_id timeouts.game_clock_s", s="C")
L("A.10.04", "Timeouts not granted", "Opponents of the throw-in team after the throw-in starts; without player control; before the opening jump; last-2-minute review rule.",
  r="5-15", req="", t="timeouts.charged", s="P", gap=X("new-IV-28"))
L("A.10.05", "Excessive timeout and halftime carry loss", "Excessive timeout penalty; 30 s timeouts carried into the second half limited to 2.",
  r="5-17, 5-14.10", req="R-SR-04 R-IV-10", t="timeouts.timeout_type timeouts.halftime_carry_loss", s="C")
L("A.10.06", "Injury, blood and official stoppages", "Stoppages for injury, blood, equipment and officials; charged or not.",
  r="5-16, 3-5", req="R-EV-11 R-TR-19", t="timeouts.timeout_type state_frame.stoppage_kind possessions.stoppage_events", s="C")
L("A.10.07", "Timeout duration (actual vs allotted)", "Real length of each stoppage, shortened timeouts.",
  r="5-14.4", req="R-PL-04", t="timeouts.duration_s timeouts.shortened", s="C")

# ---------------------------------------------------------------- A.11 Substitutions and lineups
D("A.11", "Substitutions and lineups", "Starting lineups, substitution procedure and restrictions (Rule 3).")
L("A.11.01", "Starting lineup", "Five starters per team listed before the game.", r="3-4", req="R-SY-03 R-FD-05", t="player_box.starter lineup_stints.lineup_key", s="C")
L("A.11.02", "Substitution procedure and timing", "Substitutes enter during dead balls when beckoned.", r="3-5, 3-6", req="R-SY-03 R-IV-03 R-EV-11", t="substitutions.during_dead_ball substitutions.player_in_id substitutions.player_out_id", s="C")
L("A.11.03", "Late-game substitution restriction", "No substitutions while the clock is stopped after a made FG in the last 59.9 s except as permitted.",
  r="3-6", req="", t="substitutions.during_dead_ball", s="P", gap=X("new-IV-26"))
L("A.11.04", "Disqualified-player replacement (20 s)", "Replacement within 20 s of notification.",
  r="4-12.5, 10-2", req="", t="substitutions.reason_inferred", s="P", gap=X("new-IV-11", note="Constant disqualified_replace_s exists; no measured replacement time column."))
L("A.11.05", "Substitution reason", "Rotation, foul trouble, fouled out, injury, after error, blowout, end-game specialist.",
  req="R-CC-03 R-PE-06", t="substitutions.reason_inferred", s="C")
L("A.11.06", "PBP substitution timing errors", "Known bias: PBP substitution times can be wrong.", req="R-DQ-09 R-SY-03", t="substitutions.timing_error_flag substitutions.source_timing", s="C")

# ---------------------------------------------------------------- A.12 Officials' mechanics and signals
D("A.12", "Officials' mechanics and signals", "Crew, positions, rotations, coverage areas, whistles and signals (Rule 2, Appendix III, Appendix VIII).")
L("A.12.01", "Crew size and roles (referee, umpires, crew chief)", "Two or three officials; the referee is crew chief.", r="2-1", req="R-FD-08 R-IV-02", t="game_officials.is_crew_chief game_officials.listed_order", s="C")
L("A.12.02", "Court position: lead, trail, centre", "Each official's floor position and mechanics role every frame.", r="App. III; three-person mechanics", req="R-DT-12 R-SR-07", t="official_positions.role official_positions.x_fc_m", s="C")
L("A.12.03", "Rotations of the crew", "Lead rotations to the strong side and position switches after foul reports.", r="Points of Emphasis 1 (three-person system)", req="", t="official_positions.role", s="M",
  gap=G("RF", "Should", "Detect each officials' rotation and post-foul switch as an event (time, officials involved, from and to roles).",
        ">= 85% of rotations found within +/- 1.0 s on 100 labelled rotations (proposal).", "New event family `official_rotation` in events, from official_positions role changes.", prio=3))
L("A.12.04", "Calling official, primary coverage area and whistle distance", "Who blew the whistle, whether the play was in his primary area, his distance to the play.",
  r="Points of Emphasis 2 (whistle discipline), 8 (team officiating)", req="R-RF-05", t="fouls.calling_official_id fouls.calling_official_role", s="P",
  gap=G("RF", "Should", "Each call stores the calling official's distance to the contact point (m), his angle to the play (degrees) and whether the play was in his primary coverage area by the crew's positions.",
        "Distance from tracking within 0.5 m of gold on 100 calls; primary-area flag agrees with a referee-expert label on >= 80% (proposal).",
        "New columns fouls.official_dist_m (m), fouls.official_angle_deg (degrees), fouls.in_primary_area (bool).", prio=3))
L("A.12.05", "Signals (Appendix VIII full list)", "Clock, timeout, violation, foul-type, information and scoring signals (about 50).",
  r="App. VIII", req="R-RF-04", t="official_positions.signal_pose", v="App.VIII", s="P",
  note="signal_pose has 10 values; App. VIII lists about 50 signals.",
  gap=G("RF", "Should", "Signal vocabulary covers every Appendix VIII signal (start/stop clock, timeouts, every violation and foul signal, shot-clock reset, no score, tipped ball, counts, 3-point attempt and success, free-throw counts, replay, challenge, flopping).",
        "Every App. VIII signal has a code; signal recognition >= 80% on 300 labelled signals (as R-RF-04); unseen signals coded `unseen`.",
        "official_positions.signal_pose enum := App. VIII list (config/vocabulary_map.yaml section `signals`).", prio=2))
L("A.12.06", "Whistles", "Whistle times from audio and their link to calls.", req="R-RF-01 R-RF-02", t="whistles.video_ts_ms whistles.linked_event_id", s="C")
L("A.12.07", "Visible counts (5 s, 10 s, throw-in)", "Officials' visible counts.", r="App. VIII (visible count)", req="R-DT-14", t="restarts.throw_in_count_s", s="P",
  gap=G("RF", "Should", "Record the start of each official's visible count (throw-in, closely guarded, backcourt) from the signal or from the rule trigger, so counts can be compared with our own clocks.",
        "Count start within +/- 0.3 s of a hand label on >= 80% of 100 labelled counts (proposal).", "New column official_positions.count_active (enum none, five, ten).", prio=3))

# ---------------------------------------------------------------- A.13 Replay and challenge
D("A.13", "Instant replay, challenges and appeals", "Reviews (voluntary, mandatory), coach's challenge and appeals (Rule 11).")
L("A.13.01", "Voluntary and mandatory reviews", "Monitor reviews by officials, with subject and outcome.", r="11-2, 11-3", req="R-RF-07 R-SR-04", t="reviews.review_kind reviews.subject reviews.outcome", s="C")
L("A.13.02", "Coach's challenge", "One per game, a second if successful; out of bounds, BI/goaltending, restricted area; costs a timeout if unsuccessful.", r="11-4 (2025-26), 2-9.19 (2026-27)", req="R-EV-16 R-SR-04", t="coaches_challenges.play_type coaches_challenges.outcome coaches_challenges.timeout_charged", s="C", note="Detail in new-IV-14.")
L("A.13.03", "Appeals", "Coach's appeal for a review (e.g. unobserved flagrant), timeout charged if not upheld.", r="11-5 (2026-27), A.R. 11-32", req="R-SR-04", t="reviews.review_kind timeouts.timeout_type", s="C")
L("A.13.04", "Review duration and game effect", "Stoppage length, clock and score changes, possession after.", req="R-SR-04 R-TR-19", t="reviews.video_ts_ms_start reviews.video_ts_ms_end reviews.score_delta_msu reviews.possession_after", s="C")
L("A.13.05", "First-half flagrant reviewed after half time", "Counts toward first-half fouls; second half starts with the offended team.", r="A.R. 11-32, 11-2.1.d.2", req="R-IV-09", t="reviews.subject foul_state.bucket_id", s="C")
