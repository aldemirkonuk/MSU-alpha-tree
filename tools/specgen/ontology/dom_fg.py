from core import D, L, G, X

# ======================================================================== F
D("F", "Group tactics: offence", "Team offensive structures from docs/taxonomy/offense_full.md (OFF.F1-F18), motion_starts.md (MS.*) and transition_full.md (TR.*).")

D("F.01", "Transition offence (OFF.F1)", "Primary break, both directions handled with G.12.")
L("F.01.01", "Transition start, end and class (state rule)", "", req="R-TR-08 R-TR-09 R-TR-05", t="transition_phases.transition_class possessions.transition_class", v="TR.ST", s="C")
L("F.01.02", "Every analyst transition definition side by side", "", req="R-TR-11 R-TR-18 R-TR-27", t="transition_phases.tr_synergy_like transition_phases.tr_hoopmath_10s transition_phases.tr_fastscout_10s", s="C")
L("F.01.03", "Outlet and advance", "", req="R-TR-13 R-TR-20", t="transition_phases.phase_times", v="OFF.F1.1 TR.PH", s="C")
L("F.01.04", "Lane filling and roles (handler, rim runner, wings, trailer, leak-out)", "", req="R-TR-04 R-TR-15", t="transition_roles.lane transition_roles.role_synergy", v="OFF.F1.2 OFF.F1.3 TR.RO", s="C")
L("F.01.05", "Numbers advantage (2v1, 3v2, 4v3)", "", req="R-TR-03 R-TR-22", t="transition_numbers.numbers_label transition_numbers.advantage", v="OFF.F1.5", s="C")
L("F.01.06", "Push after makes and free throws", "", req="R-TR-14 R-TR-21 R-TR-23", t="transition_phases.pushed transition_phases.t_inbound_release_ms", s="C")
L("F.01.07", "Passed-up breaks and pull-backs", "", req="R-TR-16 R-TR-24 R-TR-26", t="transition_phases.passed_up_reason transition_phases.value_at_stake_xpts", s="C")
L("F.01.08", "Named breaks (incl. MSU/Izzo)", "", req="R-ST-04 R-ST-05", t="set_instances.family_code", v="OFF.F1.4", s="C")

D("F.02", "Early offence (OFF.F2)", "")
L("F.02.01", "Drag and double drag ('77')", "", req="R-ST-18", t="actions.action_code", v="OFF.F2.1", s="C")
L("F.02.02", "Pistol / 21", "", req="R-ST-04 R-ST-05", t="set_instances.set_code", v="OFF.F2.2", s="C")
L("F.02.03", "Trailer actions and early post", "", req="R-TR-13 R-ST-04", t="transition_phases.phase_times set_instances.set_code", v="OFF.F2.3 OFF.F2.4", s="C")
L("F.02.04", "Flow into the half court", "", req="R-TR-13 R-TR-20", t="transition_phases.phase_times", v="OFF.F2.5", s="C")

D("F.03", "Half-court alignments and motion starts (OFF.F3, MS)", "")
L("F.03.01", "Alignment snapshot and family match", "", req="R-ST-19 R-ST-21", t="configuration_snapshots.alignment_code set_instances.alignment_code", v="MS OFF.F3.1", s="C")
L("F.03.02", "Named starts (Horns, 1-4, box, stack, 5-out, ...)", "", req="R-ST-04 R-ST-05 R-ST-21", t="set_instances.set_code", v="MS OFF.F3.2 OFF.F3.3 OFF.F3.4", s="C")

D("F.04", "Continuity and motion systems (OFF.F4)", "")
L("F.04.01", "System label per possession and per game", "Whether a team is running a continuity (flex, shuffle, swing, Princeton, triangle, blocker-mover) and how many cycles.", req="R-ST-04 R-ST-25", t="set_instances.family_code", v="OFF.F4.1 OFF.F4.2", s="P",
  gap=G("ST", "Should", "For continuity and rule-based systems, store the system label per chance and the number of completed pattern cycles (a cycle = the template's action sequence repeated after a reversal), plus each team's system share per game.",
        "System label agrees with Aldemir's labels on >= 80% of 100 chances (proposal); cycle counts recompute from the action sequence.", "New columns set_instances.system_code, set_instances.cycles_completed.", prio=3))
L("F.04.02", "Rule-based motion reads", "Read-and-react, 5-out motion rules (cut after pass, fill, etc.).", req="R-ST-06 R-ST-18", t="set_instances.action_sequence", v="OFF.F4.2", s="C")

D("F.05", "Ball-screen offence (OFF.F5)", "Location x angle x screener arrival x screener action x handler read.")
L("F.05.01", "Screen location and angle", "", req="R-ST-02 R-CG-07", t="screens.spot screens.screen_angle_deg", v="OFF.F5.1 OFF.F5.2", s="C")
L("F.05.02", "Screener pre-action (how the screener arrives)", "Sprint, flip, re-screen, ghost approach, step-up, Ram (screen-the-screener).", req="R-ST-18", t="screens.screen_kind", v="OFF.F5.3", s="P",
  gap=G("ST", "Shall", "Every ball screen stores the screener's arrival (OFF.F5.3 code: walk-up, sprint, flip, re-screen, Ram/after receiving a screen, from the corner, from the dunker spot) with arrival speed (m/s).",
        "Arrival code present on 100% of ball screens; >= 80% correct on 200 labelled screens (proposal).", "New columns screens.screener_arrival_code (OFF.F5.3), screens.screener_arrival_speed_mps.", prio=2))
L("F.05.03", "Screener action after and handler read", "", req="R-ST-18", t="screens.screener_action_after screens.handler_read", v="OFF.F5.4 OFF.F5.5", s="C")
L("F.05.04", "Off-ball spacing tags during the PnR", "Corner fill, slot, dunker, lift, shake.", req="R-ST-03", t="configuration_snapshots.players", v="OFF.F5.6", s="P",
  gap=G("ST", "Should", "Each ball screen stores the spacing tags of the three off-ball attackers (OFF.F5.6 codes) from the configuration snapshot at the screen moment.",
        "Tags recompute from the snapshot; >= 80% agreement with labels (proposal).", "New column screens.spacing_tags (list of OFF.F5.6 codes).", prio=3))
L("F.05.05", "Double ball screens (Spain, Detroit, stack, step-up)", "", req="R-ST-18", t="screens.screen_kind", v="OFF.F5.7", s="C")

D("F.06", "Handoffs (OFF.F6)", "")
L("F.06.01", "Handoff, fake handoff, keep", "", req="R-ST-18", t="screens.screen_kind actions.action_code", v="OFF.F6", s="C")

D("F.07", "Post offence (OFF.F7)", "")
L("F.07.01", "Post entries, splits, high-low, duck-in", "", req="R-ST-04 R-DF-07", t="post_touches.post_move_code post_touches.result", v="OFF.F7", s="C")

D("F.08", "Off-ball screens (OFF.F8.1, F8.3)", "")
L("F.08.01", "Down, flare, back, cross, stagger, pin-down, elevator, hammer", "", req="R-ST-02 R-ST-18", t="screens.screen_kind screens.offense_code", v="OFF.F8.1", s="C")
L("F.08.02", "Screen-use reads (curl, fade, straight, reject)", "", req="R-ST-18", t="screens.handler_read", v="OFF.F8.3", s="C")

D("F.09", "Isolation and spread (OFF.F9, F10)", "")
L("F.09.01", "Isolation and clear-outs", "", req="R-ST-04 R-ST-05", t="set_instances.set_code set_instances.synergy_outcome_code", v="OFF.F9", s="C")
L("F.09.02", "Drive-and-kick and paint touches", "Paint touches per chance and kick-outs.", req="R-EV-06 R-TR-20", t="drives.result", v="OFF.F10", s="P",
  gap=G("ST", "Should", "Count paint touches per chance (ball inside the lane, |x| <= 1.83 m and y <= 5.79 m from the end line, by catch or dribble) and the time of the first one, for half-court as well as transition.",
        "Recomputes from ball_states; first paint touch within +/- 0.2 s of gold (proposal).", "New columns chances.paint_touches, chances.first_paint_touch_s.", prio=2))

D("F.10", "Zone and press offence (OFF.F11, F12)", "")
L("F.10.01", "Zone offence actions", "", req="R-ST-24", t="actions.action_code", v="OFF.F11", s="C")
L("F.10.02", "Press break", "", req="R-ST-24", t="actions.action_code set_instances.set_code", v="OFF.F12", s="C")

D("F.11", "Special situations (OFF.F13)", "")
L("F.11.01", "After timeout (ATO)", "", req="R-EV-15 R-CH-06", t="play_calls.after_timeout possessions.after_timeout timeouts.ato_set_instance_id", v="OFF.F13.1", s="C")
L("F.11.02", "BLOB and SLOB", "", req="R-SY-04 R-DT-14", t="possessions.inbound_type set_instances.situation", v="OFF.F13.2 OFF.F13.3", s="C")
L("F.11.03", "End of half and end of game", "", req="R-ST-23 R-PE-07", t="set_instances.situation", v="OFF.F13.4", s="C")
L("F.11.04", "Late clock", "", req="R-ST-05", t="set_instances.situation shots.shot_clock_s", v="OFF.F13.5", s="C")
L("F.11.05", "Free-throw alignments", "", req="R-DT-13", t="free_throws.lane_occupant_ids", v="OFF.F13.6", s="C")
L("F.11.06", "Jump-ball plays", "", req="R-EV-14", t="jump_balls.circle_formation", v="OFF.F13.7", s="C")
L("F.11.07", "Delay and clock-kill", "", req="R-PE-07 R-SR-11", t="set_instances.situation", v="OFF.F13.8", s="C")
L("F.11.08", "Two-for-one and last shot", "", req="R-SR-11 R-PE-07", t="state_second.two_for_one_window state_second.last_shot_window", s="C")

D("F.12", "Offensive rebounding and spacing systems (OFF.F14, F15)", "")
L("F.12.01", "Crash vs get-back policy", "", req="R-EV-08", t="rebounds.crashers_off rebounds.leaker_ids", v="OFF.F14", s="C")
L("F.12.02", "Spacing systems (4-out, 5-out, dunker spot)", "", req="R-CG-07 R-ST-18", t="frame_geometry.spacing_mean_m configuration_snapshots.alignment_code", v="OFF.F15", s="C")

D("F.13", "Recognition infrastructure and labels", "")
L("F.13.01", "Set templates, match, timeline, phases", "", req="R-ST-04 R-ST-05 R-ST-07 R-ST-08", t="set_instances.match_confidence set_instance_phases.phase_name", s="C")
L("F.13.02", "Counters and broken plays", "", req="R-ST-05", t="set_instances.departure_step set_instances.counter_code", s="C")
L("F.13.03", "Unmatched chances and new-set clustering", "", req="R-ST-09", t="set_instances.unmatched_cluster_id", s="C")
L("F.13.04", "Template status and role-based templates", "", req="R-ST-11 R-ST-12", t="set_instances.template_version", s="C")
L("F.13.05", "Name collisions and secondary vocabularies", "", req="R-ST-22 R-ST-15", t="set_instances.set_code", v="OFF.F16", s="C")
L("F.13.06", "Synergy-style outcome labels", "", req="R-TR-11", t="set_instances.synergy_outcome_code", v="OFF.F17", s="C")
L("F.13.07", "MSU addendum and playbook library", "", req="R-ST-14 R-ST-10", t="profile_snapshots.metric_code", v="OFF.F18", s="C")
L("F.13.08", "Team style measures", "", req="R-ST-25", t="profile_snapshots.metric_code", s="C")

# ======================================================================== G
D("G", "Group tactics: defence", "Team defensive structures from docs/taxonomy/defense_full.md (DEF.F1-F18).")

D("G.01", "Man principles and on-ball rules (DEF.F1, F2)", "")
L("G.01.01", "Man philosophy (help-first, pressure, directional, switching, pack line)", "", req="R-DF-04", t="scheme_states.l1_base_scheme_code", v="DEF.F1", s="C")
L("G.01.02", "MSU documented principles", "", req="R-DF-21", t="scheme_states.msu_principle_flags", v="DEF.F1.6", s="C")
L("G.01.03", "Force direction and ball pressure", "", req="R-DF-04", t="scheme_states.l4_force_dir scheme_states.l4_pressure_m", v="DEF.F2", s="C")
L("G.01.04", "Pick-up point", "Where the defence first pressures the ball (full, three-quarter, half court, top of the key).", req="", t="", s="M",
  gap=G("DF", "Shall", "Per possession, the pick-up point: the ball-handler's distance from his attacked rim (m) when an on-ball defender first stays within 1.83 m of him for >= 1.0 s, and the pick-up class (full, three-quarter, half court, top of key).",
        "Recomputes from tracks; class agrees with labels on >= 85% of 200 possessions (proposal).", "New columns possessions.pickup_dist_m (m), possessions.pickup_class.", prio=2))

D("G.02", "Screen coverages (DEF.F3, F4, F5)", "")
L("G.02.01", "Ball-screen coverage (4 coarse, 13+ fine, drop depth)", "", req="R-DF-06 R-DF-16 R-ST-20", t="screens.coverage_coarse screens.coverage_fine_code screens.drop_depth_m", v="DEF.F3", s="C")
L("G.02.02", "Handoff coverage", "", req="R-DF-06", t="screens.coverage_fine_code", v="DEF.F4", s="C")
L("G.02.03", "Off-ball screen coverage", "", req="R-DF-07", t="screens.coverage_fine_code", v="DEF.F5", s="C")

D("G.03", "Post defence (DEF.F6)", "")
L("G.03.01", "Post positioning (front, three-quarter, behind)", "", req="R-DF-07", t="post_touches.post_defense", v="DEF.F6.1", s="C")
L("G.03.02", "Post doubles and rotations", "", req="R-DF-07", t="post_touches.double_team", v="DEF.F6.3 DEF.F6.4", s="C")
L("G.03.03", "Lob protection", "Weak-side help against lobs over a fronting defender.", req="R-ST-26", t="", v="DEF.F6.5", s="P",
  gap=G("DF", "Should", "When the post is fronted, store whether a weak-side defender is within 2.0 m of the rim line to protect the lob, and the outcome of lob attempts.",
        "Flag recomputes from tracks; lob outcomes equal shot/turnover records.", "New column post_touches.lob_help_present (bool).", prio=3))

D("G.04", "Help, rotation and closeouts (DEF.F7)", "")
L("G.04.01", "Help position per defender per second", "", req="R-DF-02", t="defensive_matchups.dist_to_ball_m defensive_matchups.in_gap", v="DEF.F7.1", s="C")
L("G.04.02", "Rim protector", "", req="R-DF-03", t="scheme_states.rim_protector_id defensive_matchups.is_rim_protector", s="C")
L("G.04.03", "Roller coverage and help actions (tag, stunt, dig, step-and-release)", "", req="R-DF-15", t="scheme_states.l3_help_actions", v="DEF.F7.2 DEF.F7.3", s="C")
L("G.04.04", "Rotations and reaction delay", "", req="R-DF-08 R-CH-05", t="reaction_events.latency_s", v="DEF.F7.4", s="C")
L("G.04.05", "Closeouts", "", req="R-DF-08", t="reaction_events.closeout_distance_m", v="DEF.F7.5", s="C")

D("G.05", "Zones, presses and junk (DEF.F8, F9, F10)", "")
L("G.05.01", "Man vs zone discrimination and named zones", "", req="R-DF-04 R-DF-17", t="scheme_states.zone_family_probs", v="DEF.F8", s="C")
L("G.05.02", "Presses (full and half court, named, policies)", "", req="R-DF-12 R-DF-18", t="scheme_states.press_code", v="DEF.F9", s="C")
L("G.05.03", "Junk defences (box-and-1, triangle-and-2)", "", req="R-DF-04", t="scheme_states.l1_base_scheme_code", v="DEF.F10", s="C")

D("G.06", "Scheme changes and policies (DEF.F11)", "")
L("G.06.01", "Scheme change events and triggers", "", req="R-DF-05 R-DF-19", t="scheme_changes.trigger_type scheme_changes.scheme_before scheme_changes.scheme_after", v="DEF.F11", s="C")
L("G.06.02", "Scheme policy by context", "", req="R-DF-14", t="profile_snapshots.metric_code", v="DEF.F11.4", s="C")

D("G.07", "Transition defence (DEF.F12)", "")
L("G.07.01", "Get-back clocks, ball stopper, defenders back", "", req="R-DF-10 R-DF-20 R-TR-12", t="transition_phases.defenders_back_at_2_3_4s transition_phases.ball_stopper_id transition_phases.last_back_id", v="DEF.F12", s="C")
L("G.07.02", "Cross-matches and recoveries", "", req="R-DF-10 R-TR-12", t="transition_phases.def_phase_times", s="C")

D("G.08", "Defensive rebounding (DEF.F13)", "")
L("G.08.01", "Box-outs and crash numbers", "", req="R-EV-08 R-PC-08", t="box_outs.result rebounds.crashers_def", v="DEF.F13", s="C")

D("G.09", "Special situations and fouling strategy (DEF.F14, F15)", "")
L("G.09.01", "Inbound (BLOB/SLOB) defence", "", req="R-DF-19", t="scheme_states.l0_phase", v="DEF.F14", s="C")
L("G.09.02", "End-game defence and foul-up-3", "", req="R-PE-07", t="fouls.is_end_game_intentional", v="DEF.F14 DEF.F15", s="C")
L("G.09.03", "Foul-trouble effect on defensive aggressiveness", "How a defender in foul trouble changes distance, contests and help.", req="R-MD-16", t="foul_state.foul_trouble", v="DEF.F15", s="P",
  gap=G("DF", "Should", "For each player-stint, compare on-ball distance (m), contest distance (m) and help frequency with and without foul trouble, within player.",
        "Estimate with 95% interval per player with >= 30 possessions in each state (else descriptive).", "profile_snapshots metric codes `def_aggr_foul_trouble_delta_*`.", prio=3))

D("G.10", "Matchups, communication and outcome labels (DEF.F16, F17, F18)", "")
L("G.10.01", "Matchup per defender per second", "", req="R-DF-01", t="defensive_matchups.attacker_id defensive_matchups.matchup_prob", v="DEF.F18.3", s="C")
L("G.10.02", "Switch mismatches", "", req="R-DF-09", t="defensive_matchups.mismatch_height_cm defensive_matchups.mismatch_speed_mps", s="C")
L("G.10.03", "Shell shape", "", req="R-DF-11", t="scheme_states.shell_centroid_xy_m scheme_states.shell_area_m2", s="C")
L("G.10.04", "Communication vocabulary as behaviours", "", req="R-CO-08", t="screens.coverage_fine_code", v="DEF.F16", s="C")
L("G.10.05", "Defensive play-type outcome labels", "", req="R-TR-11", t="set_instances.synergy_outcome_code", v="DEF.F17", s="C")
L("G.10.06", "Per-second label hierarchy", "", req="R-DF-04", t="scheme_states.l0_phase scheme_states.l1_base_scheme_code scheme_states.l2_active_coverages", v="DEF.F18.1", s="C")
L("G.10.07", "MSU's own defence measured the same way", "", req="R-DF-13", t="scheme_states.is_msu_defending", s="C")
