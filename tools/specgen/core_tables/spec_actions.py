from common import *

TABLES = []
CV = {"O": "computed by us (tracking + ball)"}
OFFV = "docs/taxonomy/offense_full.md F1-F18 (OFF.F<n>[.<sub>]) and docs/taxonomy/motion_starts.md items (MS.<id>)"
DEFV = "docs/taxonomy/defense_full.md F1-F18 (DEF.F<n>[.<sub>])"
TRV = "docs/research/transition_full.md (TR.PH.* phases 3.1/3.3, TR.RO.* roles 4, TR.ST.* start types 6.1, definition fields 5.4)"

def evk(n="event_id", null=True):
    return C(n, "string", None, "events key", null, "Matching row in events.", {"O": "events"}, ["R-EV-01", "R-EV-12"])

def key(n, prefix, req):
    return C(n, "string", None, f"'<game_id>:{prefix}:<n>'", False, "Row key.", CV, req)

G = "Ball actions and player events"
TABLES.append(T("passes", G, "one row per pass (completed or not)", ["game_id", "pass_id"], [
    game_id(), key("pass_id", "pass", ["R-EV-02"]), evk(), possession_id(), chance_id(), team_id(),
    player_id("passer_id", "Passer.", req=["R-EV-02"]),
    player_id("receiver_id", "Intended or actual receiver.", null=True, req=["R-EV-02"]),
    video_ts("release_ts_ms"), frame_index("release_frame", null=True),
    video_ts("catch_ts_ms", null=True), frame_index("catch_frame", null=True),
    *pos("start_", req=["R-EV-02"], what="the ball at release"),
    *pos("end_", req=["R-EV-02"], what="the ball at catch or end"),
    C("pass_type", "enum[chest, bounce, overhead, lob, skip, kick_out, outlet, entry, post_entry, handoff, tap, unseen]", None, "enum (11 types + unseen, R-EV-02)", False, "Pass type ('unseen' when hidden by a cut).", CV, ["R-EV-02"]),
    C("outcome", "enum[completed, intercepted, deflected_completed, deflected_out, thrown_away, unseen]", None, "enum", False, "Outcome.", CV, ["R-EV-02", "R-EV-09"]),
    C("distance_m", "float32", "m", "[0, 30]", True, "Pass distance.", CV, ["R-EV-02"]),
    C("speed_mps", "float32", "m/s", "[0, 25]", True, "Mean ball speed.", CV, ["R-EV-02"]),
    C("flight_time_s", "float32", "s", "[0, 3]", True, "Release to catch.", CV, ["R-BL-04"]),
    C("angle_change_deg", "float32", "degrees", "[0, 180]", True, "Change of ball direction versus the previous pass or dribble.", CV, ["R-EV-02"]),
    C("lane_openness_m", "float32", "m", "[0, 15]", True, "Nearest defender's perpendicular distance from the passer-receiver line.", CV, ["R-EV-02", "R-CG-07"]),
    C("lane_angle_at_passer_deg", "float32", "degrees", "[0, 180]", True, "Angle at the passer between the lane and the nearest defender.", CV, ["R-CG-07"]),
    C("receiver_first_action", "enum[shoot, drive, pass, hold, turnover, none]", None, "enum", True, "Receiver's first action.", CV, ["R-EV-02"]),
    C("chain_role", "enum[assist, hockey_assist, third_pass_back, potential_assist, none]", None, "enum", False, "Pass-chain role by our video rule (hockey assist = completed pass to the assister in the same chance with no shot or turnover between).", CV, ["R-EV-03", "R-VL-09"]),
    C("is_official_assist", "bool", None, "true/false", True, "PBP credits this pass as the assist (kept separate).", {"C": "shotInfo.assistedBy", "HN": "assist_player", "E": "participants"}, ["R-EV-03"]),
    C("decision_quality_xpts", "float32", "expected points", "[-3, 3]", True, "Value of the option taken minus the best open option.", {"O": "VL"}, ["R-VL-05"]),
    C("value_delta", "float32", "expected points", "[-4, 4]", True, "Possession value change across the pass.", {"O": "VL"}, ["R-VL-02", "R-VL-03"]),
], ["R-EV-02", "R-EV-03", "R-BL-04", "R-VL-03", "R-CH-02"], "IN_GAME", stamps=True,
    fks=[("game_id", "games.game_id"), ("passer_id", "players.player_id"), ("receiver_id", "players.player_id")]))

TABLES.append(T("touches", G, "one row per touch (catch or gain of control to release or loss)", ["game_id", "touch_id"], [
    game_id(), key("touch_id", "touch", ["R-EV-04"]), possession_id(), chance_id(), team_id(), player_id(req=["R-EV-04"]),
    video_ts("start_ts_ms"), video_ts("end_ts_ms"),
    C("touch_time_s", "float32", "s", "[0, 30]", False, "Catch to release.", CV, ["R-EV-04", "R-CO-01"]),
    C("dribbles", "int8", "count", "[0, 60]", True, "Dribbles in the touch.", CV, ["R-BL-06", "R-EV-04"]),
    C("dribbles_partial", "bool", None, "true/false", False, "Count partial (occlusion).", CV, ["R-BL-06"]),
    C("hand", "enum[left, right, both, unknown]", None, "enum", True, "Dominant dribble hand during the touch.", CV, ["R-EV-04", "R-PC-11"]),
    C("start_how", "enum[catch, rebound, steal, loose_ball, inbound_receive, jump_ball_tip]", None, "enum", False, "How control started.", CV, ["R-EV-04"]),
    C("end_how", "enum[pass, shot, turnover, foul_drawn, held_ball, dead_ball, handoff]", None, "enum", False, "How it ended.", CV, ["R-EV-04"]),
    *pos("catch_", req=["R-EV-04"], what="the player at the catch"),
    C("pressure_m", "float32", "m", "[0, 15]", True, "Nearest defender distance at the catch.", CV, ["R-CO-01", "R-CO-04"]),
    C("decision_latency_s", "float32", "s", "[0, 30]", True, "Catch to first action (pass, shot, drive), +- one frame (R-CO-06).", CV, ["R-CO-01", "R-CO-06"]),
    C("touch_index_in_possession", "int8", None, "[1, 60]", False, "Touch order within the possession.", CV, ["R-EV-04"]),
], ["R-EV-04", "R-BL-06", "R-CO-01", "R-PC-10"], "IN_GAME", stamps=True,
    fks=[("game_id", "games.game_id"), ("player_id", "players.player_id")]))

TABLES.append(T("dribbles", G, "one row per dribble (bounce), with the move type when it is a move", ["game_id", "dribble_id"], [
    game_id(), key("dribble_id", "drb", ["R-EV-05"]),
    C("touch_id", "string", None, "touches key", False, "Touch.", CV, ["R-EV-04"]),
    player_id(req=["R-EV-05"]), video_ts(),
    C("hand", "enum[left, right, unknown]", None, "enum", False, "Hand.", CV, ["R-EV-04"]),
    C("move_type", "enum[plain, crossover, between_legs, behind_back, hesitation, spin, retreat, unresolved]", None, "enum", False, "Dribble move (6 types + plain + unresolved, R-EV-05).", CV, ["R-EV-05"]),
    *pos(req=["R-EV-05"], what="the ball bounce"),
], ["R-EV-05", "R-BL-06"], "IN_GAME", stamps=True, fks=[("touch_id", "touches.touch_id")]))

TABLES.append(T("drives", G, "one row per drive (dribble move gaining >= 3 m toward the rim, proposal)", ["game_id", "drive_id"], [
    game_id(), key("drive_id", "drv", ["R-EV-06"]),
    C("touch_id", "string", None, "touches key", False, "Touch.", CV, ["R-EV-06"]),
    possession_id(), chance_id(), player_id(req=["R-EV-06"]),
    video_ts("start_ts_ms"), video_ts("end_ts_ms"),
    *pos("start_", req=["R-EV-06"], what="the driver at the drive start"),
    *pos("end_", req=["R-EV-06"], what="the driver at the drive end (depth reached)"),
    C("depth_gain_m", "float32", "m", "[3, 25]", False, "r gained toward the rim.", CV, ["R-EV-06"]),
    C("direction", "enum[baseline, middle]", None, "enum", False, "Baseline or middle.", CV, ["R-EV-06", "R-PC-11"]),
    C("hand_side", "enum[left, right]", None, "enum", False, "Drive to the driver's left or right.", CV, ["R-EV-06", "R-PC-11"]),
    player_id("primary_defender_id", "On-ball defender at the start.", null=True, req=["R-EV-06"]),
    C("defender_reaction", "enum[contained, beaten, fouled, stripped, unknown]", None, "enum", True, "On-ball defender reaction.", CV, ["R-EV-06", "R-DF-02"]),
    player_id("help_defender_id", "First help defender.", null=True, req=["R-EV-06", "R-DF-02"]),
    C("help_arrival_s", "float32", "s", "[0, 5]", True, "Drive start to help arrival within 1.5 m.", CV, ["R-DF-08"]),
    C("result", "enum[shot, kick_out_pass, dump_off_pass, other_pass, foul_drawn, turnover, reset]", None, "enum", False, "Result.", CV, ["R-EV-06"]),
    C("value_delta", "float32", "expected points", "[-4, 4]", True, "Value change across the drive.", {"O": "VL"}, ["R-VL-02"]),
], ["R-EV-06", "R-PC-11", "R-DF-02"], "IN_GAME", stamps=True, fks=[("touch_id", "touches.touch_id")]))

TABLES.append(T("defensive_events", G, "one row per defensive event (steal, deflection, block, charge drawn, loose ball, contest)", ["game_id", "def_event_id"], [
    game_id(), key("def_event_id", "def", ["R-EV-09"]), evk(), possession_id(), chance_id(),
    C("type", "enum[steal, deflection, block_kept_in, block_out_of_bounds, charge_drawn, loose_ball_recovery, contest, forced_turnover]", None, "enum", False, "Type.", {"O": "video", "E": "type.text 'Steal'/'Block Shot'", "HN": "event_type", "C": "playType"}, ["R-EV-09"]),
    player_id("defender_id", "Defender credited.", req=["R-EV-09"]),
    player_id("offensive_player_id", "Offensive player involved.", null=True, req=["R-EV-09"]),
    video_ts(), *pos(req=["R-EV-09"], what="the event"),
    C("linked_id", "string", None, "shots / passes / turnovers key", True, "Linked shot, pass or turnover.", CV, ["R-EV-09"]),
    C("in_pbp", "bool", None, "true/false", False, "Event exists in PBP (deflections and contests never do).", CV, ["R-EV-09", "R-SY-10"]),
    C("loose_ball_players", "int8", "players", "[0, 10]", True, "Players within 2 m of a loose ball (>= 4 = scramble, HR trigger).", CV, ["R-EV-09", "R-HR-01"]),
    team_id("recovered_by_team_id", "Team that recovered a loose ball.", null=True, req=["R-EV-09"]),
], ["R-EV-09", "R-DF-08", "R-PC-08"], "IN_GAME", stamps=True))

G = "Actions, sets and defensive structure"
TABLES.append(T("movement_primitives", G, "one row per movement primitive of one player", ["game_id", "primitive_id"], [
    game_id(), key("primitive_id", "prim", ["R-ST-01"]), possession_id(), player_id(req=["R-ST-01"]), team_id(),
    C("primitive_type", "enum[stand, walk, jog, sprint, cut_basket, cut_backdoor, cut_flare, cut_curl, cut_straight, cut_shallow, set_screen, use_screen, seal, relocate, lift, drift, rim_run, corner_sprint, closeout, recover]", None, "enum", False, "Primitive (R-ST-01 list).", CV, ["R-ST-01"], vocab=OFFV + " section 0.2 primitives"),
    video_ts("start_ts_ms"), video_ts("end_ts_ms"),
    *pos("start_", req=["R-ST-01"], what="the player at start"),
    *pos("end_", req=["R-ST-01"], what="the player at end"),
    C("path_shape", "enum[straight, curved]", None, "enum", False, "Path shape.", CV, ["R-ST-01"]),
    C("curvature_per_m", "float32", "1/m", "[0, 5]", True, "Mean path curvature.", CV, ["R-ST-01"]),
    C("mean_speed_mps", "float32", "m/s", "[0, 10]", False, "Mean speed.", CV, ["R-ST-01"]),
    C("peak_speed_mps", "float32", "m/s", "[0, 10]", False, "Peak speed.", CV, ["R-ST-01"]),
    C("duration_s", "float32", "s", "[0.1, 30]", False, "Duration.", CV, ["R-ST-01"]),
    C("dir_rel_basket_deg", "float32", "degrees", "[-180, 180]", True, "Direction relative to the basket.", CV, ["R-ST-01"]),
    C("dir_rel_ball_deg", "float32", "degrees", "[-180, 180]", True, "Direction relative to the ball.", CV, ["R-ST-01"]),
], ["R-ST-01", "R-ST-16"], "IN_GAME", stamps=True))

TABLES.append(T("screens", G, "one row per screen (on-ball, off-ball, handoff), with offense and defense labels at one screen moment", ["game_id", "screen_id"], [
    game_id(), key("screen_id", "scr", ["R-ST-02", "R-ST-17"]), possession_id(), chance_id(), team_id(),
    player_id("screener_id", "Screener.", req=["R-ST-02"]),
    player_id("user_id", "Player using the screen (handler or cutter).", req=["R-ST-02"]),
    player_id("screener_defender_id", "Screener's defender.", null=True, req=["R-DF-06"]),
    player_id("user_defender_id", "User's defender.", null=True, req=["R-DF-06"]),
    C("screen_kind", "enum[on_ball, off_ball, handoff, fake_handoff, double, stagger, flare, back, down, cross, pin_down, other]", None, "enum", False, "Kind.", CV, ["R-ST-02", "R-ST-18"], vocab=OFFV + " F5, F6, F8"),
    C("offense_code", "string", None, "OFF.F5.* / OFF.F6.* / OFF.F8.*", True, "Offense taxonomy code (location x angle x screener action x read).", CV, ["R-ST-04", "R-ST-18"], vocab=OFFV),
    video_ts("screen_moment_ts_ms"),
    frame_index("screen_moment_frame", null=True),
    *pos(req=["R-ST-02"], what="the screener at the screen moment"),
    C("screen_angle_deg", "float32", "degrees", "[0, 180]", True, "Screen angle relative to the user's path.", CV, ["R-CG-07"]),
    C("contact_distance_m", "float32", "m", "[0, 3]", True, "Min screener-to-user's-defender distance.", CV, ["R-CG-07", "R-ST-20"]),
    C("duration_s", "float32", "s", "[0, 5]", True, "Screener stationary duration.", CV, ["R-ST-17"]),
    C("screener_speed_mps", "float32", "m/s", "[0, 10]", True, "Screener speed during the screen.", CV, ["R-ST-17"]),
    C("strict_rule_fired", "bool", None, "true/false", False, "Strict rule: screener <= 0.3 m/s for >= 0.5 s within 1.2 m of the user's path (reports use strict).", CV, ["R-ST-17"]),
    C("loose_rule_fired", "bool", None, "true/false", False, "Loose rule: < 0.6 m/s for >= 0.3 s.", CV, ["R-ST-17"]),
    C("screener_action_after", "enum[roll, short_roll, pop_mid, pop_arc, slip, ghost, replace, seal, none]", None, "enum", True, "Screener action after.", CV, ["R-ST-18"], vocab=OFFV + " F5.4"),
    C("handler_read", "enum[use, reject, split, snake, retreat, pass_out, none]", None, "enum", True, "User's read.", CV, ["R-ST-02"], vocab=OFFV + " F5.5"),
    C("coverage_coarse", "enum[containment, show, two_on_ball, exchange, directional, unknown]", None, "enum (4 coarse + directional, R-DF-16)", True, "Coarse coverage class.", CV, ["R-DF-16", "R-DF-06"], vocab=DEFV + " F3.1-F3.5"),
    C("coverage_fine_code", "string", None, "DEF.F3.* or DEF.F4.* or DEF.F5.*", True, "Fine coverage (13 ball-screen coverages; DHO and off-ball coverages).", CV, ["R-DF-06", "R-DF-07"], vocab=DEFV),
    C("drop_depth_m", "float32", "m", "[-3, 8]", True, "Big defender depth vs the screen line 0.3 s after the screen moment.", CV, ["R-DF-16"]),
    C("drop_band", "enum[high, standard, deep, not_drop]", None, "enum (0.6-1.83, 1.83-3.05, > 3.05 m)", True, "Drop band.", CV, ["R-DF-16"]),
    C("is_screen_assist", "bool", None, "true/false", False, "Screen led directly to a made shot.", CV, ["R-EV-03"]),
    C("screener_handler_timing_s", "float32", "s", "[-3, 3]", True, "Handler arrival minus screener set time.", CV, ["R-CH-04"]),
    C("value_delta", "float32", "expected points", "[-4, 4]", True, "Value change across the screen.", {"O": "VL"}, ["R-VL-06"]),
], ["R-ST-02", "R-ST-17", "R-ST-20", "R-DF-06", "R-DF-07", "R-DF-16", "R-CH-04"], "IN_GAME", stamps=True))

TABLES.append(T("actions", G, "one row per multi-player action (two or more primitives in relation)", ["game_id", "action_id"], [
    game_id(), key("action_id", "act", ["R-ST-02"]), possession_id(), chance_id(), team_id(),
    C("action_code", "string", None, "OFF.F* code (e.g. OFF.F5 pick-and-roll, OFF.F6 handoff, OFF.F8 off-ball screen, OFF.F7 post entry)", False, "Action type from the offense taxonomy.", CV, ["R-ST-02", "R-ST-18"], vocab=OFFV),
    C("participants", "list<struct<player_id:string, role:string>>", None, "2-5 players", False, "Players and roles (handler, screener, cutter, passer, receiver).", CV, ["R-ST-02", "R-ST-12"]),
    C("primitive_ids", "list<string>", None, "movement_primitives keys", False, "Primitives composing the action.", CV, ["R-ST-02"]),
    C("screen_id", "string", None, "screens key", True, "Screen if the action has one.", CV, ["R-ST-20"]),
    video_ts("start_ts_ms"), video_ts("end_ts_ms"),
    C("configuration_snapshot_id", "string", None, "configuration_snapshots key", True, "All-10 configuration at the action start.", CV, ["R-ST-03"]),
    conf(),
    C("value_delta", "float32", "expected points", "[-4, 4]", True, "Value change across the action.", {"O": "VL"}, ["R-VL-02"]),
], ["R-ST-02", "R-ST-03", "R-ST-18", "R-ST-24"], "IN_GAME", stamps=True))

TABLES.append(T("post_touches", G, "one row per post touch (catch in a post zone)", ["game_id", "post_id"], [
    game_id(), key("post_id", "post", ["R-DF-07"]),
    C("touch_id", "string", None, "touches key", False, "Touch.", CV, ["R-DF-07"]),
    player_id(req=["R-DF-07"]),
    C("post_zone", "enum[low_post, high_post]", None, "enum", False, "Zone (geometry.post_zone).", CV, ["R-CG-05"]),
    C("entry_pass_id", "string", None, "passes key", True, "Entry pass.", CV, ["R-EV-02"]),
    C("seal", "bool", None, "true/false", True, "Sealed before the catch.", CV, ["R-ST-01"]),
    player_id("defender_id", "Post defender.", null=True, req=["R-DF-07"]),
    C("post_defense", "enum[front, three_quarter_high, three_quarter_low, behind, unknown]", None, "enum", True, "Post defense position (DEF.F6.1).", CV, ["R-DF-07"], vocab=DEFV + " F6.1-F6.2"),
    C("double_team", "enum[none, top, baseline, passer, big_to_big]", None, "enum", True, "Double-team origin (DEF.F6.3).", CV, ["R-DF-07"], vocab=DEFV + " F6.3"),
    C("post_move_code", "string", None, "OFF.F7.*", True, "Post move.", CV, ["R-ST-04"], vocab=OFFV + " F7"),
    C("result", "enum[shot, pass_out, foul_drawn, turnover, reset]", None, "enum", False, "Result.", CV, ["R-DF-07"]),
], ["R-DF-07", "R-ST-04"], "IN_GAME", stamps=True))

TABLES.append(T("play_calls", G, "one row per observed or inferred play call (set called)", ["game_id", "call_id"], [
    game_id(), key("call_id", "call", ["R-EV-15"]), team_id(),
    video_ts(),
    C("call_source", "enum[coach_signal_video, player_signal_video, verbal_audio, commentary, inferred_from_set_match, coach_tag]", None, "enum", False, "Evidence for the call.", {"O": "video, audio, set matcher", "M": "coach tag"}, ["R-EV-15", "R-AU-02", "R-TR-28"]),
    C("call_text", "string", None, "free text", True, "Call name as heard or seen.", {"O": "ASR / label"}, ["R-AU-02"]),
    C("mapped_set_code", "string", None, "OFF.F* / MS.* code", True, "Taxonomy item the call maps to (vocabulary map).", CV, ["R-ST-04", "R-ST-15"], vocab=OFFV),
    C("set_id", "string", None, "set_instances key", True, "Set instance that followed.", CV, ["R-ST-05"]),
    C("after_timeout", "bool", None, "true/false", False, "First call after a timeout.", CV, ["R-EV-15", "R-CH-06"]),
    C("is_weak_label", "bool", None, "true", False, "Calls from commentary or signals are weak labels, never truth (R-AU-02).", CV, ["R-AU-02"]),
    conf(),
], ["R-EV-15", "R-AU-02", "R-CH-06"], "IN_GAME", stamps=True))

TABLES.append(T("set_instances", G, "one row per chance x matched or unmatched set", ["game_id", "set_id"], [
    game_id(), key("set_id", "set", ["R-ST-05"]), possession_id(), chance_id(False), team_id(),
    C("family_code", "string", None, "OFF.F1..OFF.F18", True, "Set family.", CV, ["R-ST-04"], vocab=OFFV),
    C("set_code", "string", None, "OFF.F*.* / MS.* / namespaced (MSU., zone., blob., press.)", True, "Named set (namespaced on collision, R-ST-22).", CV, ["R-ST-04", "R-ST-22"], vocab=OFFV),
    C("alignment_code", "string", None, "OFF.F3.1 alignment codes", True, "Alignment at the alignment moment (R-ST-19).", CV, ["R-ST-19"], vocab=OFFV + " F3"),
    C("compositional_name", "string", None, "e.g. 'Horns -> Iverson -> side PnR'", False, "Name built from parts, matched or not.", CV, ["R-ST-06"]),
    C("action_sequence", "list<string>", None, "actions keys in order", False, "Full action sequence.", CV, ["R-ST-06"]),
    C("match_confidence", "float32", None, "[0, 1]", True, "Template match confidence.", CV, ["R-ST-05"]),
    C("departure_step", "int8", None, "[0, 20]", True, "Template step where play left the template.", CV, ["R-ST-05"]),
    C("counter_code", "string", None, "taxonomy counter", True, "Counter used.", CV, ["R-ST-05"]),
    C("start_matched_continuation_unknown", "bool", None, "true/false", False, "Start matched, continuation unknown.", CV, ["R-ST-19"]),
    C("unmatched_cluster_id", "int32", None, ">= 0", True, "Cluster for unmatched chances (candidate new set).", CV, ["R-ST-09"]),
    C("template_version", "string", None, "template file hash", True, "Template version used.", CV, ["R-ST-11"]),
    C("mirrored", "bool", None, "true/false", False, "Matched on the mirrored template.", CV, ["R-ST-04"]),
    C("situation", "enum[half_court, ato, blob, slob, end_of_half, end_of_game, late_clock, press_break, zone_offense, transition_flow]", None, "enum", False, "Special situation layer (OFF.F13).", CV, ["R-ST-23", "R-ST-24"], vocab=OFFV + " F13"),
    video_ts("t0_ts_ms"), video_ts("end_ts_ms"),
    game_clock("t0_game_clock_s"), shot_clock("t0_shot_clock_s"),
    C("value_start", "float32", "expected points", "[0, 4]", True, "Value at t0.", {"O": "VL"}, ["R-VL-08"]),
    C("points", "int8", "points", "[0, 6]", True, "Points scored in the chance.", CV, ["R-VL-08"]),
    C("synergy_outcome_code", "string", None, "OFF.F17 play-type label", True, "Synergy-style outcome label.", CV, ["R-ST-05"], vocab=OFFV + " F17"),
], ["R-ST-04", "R-ST-05", "R-ST-06", "R-ST-07", "R-ST-09", "R-ST-19", "R-ST-22"], "IN_GAME", stamps=True))

TABLES.append(T("set_instance_phases", G, "one row per set instance x phase", ["game_id", "set_id", "phase_index"], [
    game_id(), C("set_id", "string", None, "set_instances key", False, "Set.", CV, ["R-ST-07"]),
    C("phase_index", "int8", None, "[0, 20]", False, "Phase order.", CV, ["R-ST-07"]),
    C("phase_name", "string", None, "template phase name", False, "Phase.", CV, ["R-ST-07"]),
    video_ts("start_ts_ms"), video_ts("end_ts_ms"),
    game_clock("start_game_clock_s"), shot_clock("start_shot_clock_s"),
    C("cutter_speed_mps", "float32", "m/s", "[0, 10]", True, "Cutter speed.", CV, ["R-ST-08"]),
    C("screen_to_cut_delay_s", "float32", "s", "[0, 5]", True, "Screen set to cut start.", CV, ["R-ST-08"]),
    C("catch_to_action_s", "float32", "s", "[0, 10]", True, "Catch to next action.", CV, ["R-ST-08"]),
    C("spacing_mean_m", "float32", "m", "[0, 20]", True, "Mean pairwise distance of the four off-ball attackers.", CV, ["R-ST-08", "R-CG-07"]),
    C("hull_area_m2", "float32", "m^2", "[0, 220]", True, "Convex hull area of the offense.", CV, ["R-ST-08"]),
    C("def_reaction_delay_s", "float32", "s", "[0, 3]", True, "Defensive reaction delay.", CV, ["R-ST-08", "R-CO-02"]),
    C("value_at_boundary", "float32", "expected points", "[0, 4]", True, "Value at the phase boundary.", {"O": "VL"}, ["R-ST-08"]),
], ["R-ST-07", "R-ST-08"], "IN_GAME", stamps=True))

TABLES.append(T("configuration_snapshots", G, "one row per configuration snapshot (all 10 players at a trigger moment)", ["game_id", "snapshot_id"], [
    game_id(), key("snapshot_id", "cfg", ["R-ST-03"]), possession_id(),
    C("trigger", "enum[action_start, alignment_moment, set_t0, possession_start, shot_release]", None, "enum", False, "What triggered it (alignment moment = handler first < 2 m/s with the ball inside y = 9 m, or first pass after crossing).", CV, ["R-ST-03", "R-ST-19"]),
    video_ts(),
    C("players", "list<struct<player_id:string, team_id:string, x_m:float32, y_m:float32, r_m:float32, theta_deg:float32, spot:string, role:string>>", "m; degrees", "10 entries", False, "All 10 positions, spots and roles.", CV, ["R-ST-03"]),
    C("alignment_code", "string", None, "OFF.F3 codes", True, "Alignment matched.", CV, ["R-ST-19"], vocab=OFFV + " F3"),
], ["R-ST-03", "R-ST-19"], "IN_GAME", stamps=True))

TABLES.append(T("scheme_states", G, "one row per defending team per second of live play (label hierarchy DEF.F18.1)", ["game_id", "team_id", "second_index"], [
    game_id(), team_id(defn="Defending team."),
    C("second_index", "int32", "s", ">= 0", False, "Whole seconds of video time (video_ts_ms // 1000).", CV, ["R-DF-04"]),
    possession_id(),
    C("l0_phase", "enum[dead_ball, inbound_blob, inbound_slob, inbound_backcourt, press, transition, half_court_set, ft]", None, "enum", False, "L0 phase.", CV, ["R-DF-04"], vocab=DEFV + " F18.1"),
    C("l1_base_scheme_code", "string", None, "man:DEF.F1.* / zone:DEF.F8.* / matchup_zone / junk:DEF.F10.* / press:DEF.F9.* / unsettled", False, "Base scheme.", CV, ["R-DF-04", "R-DF-12"], vocab=DEFV),
    C("l1_conf", "float32", None, "[0, 1]", False, "Posterior of the L1 label.", CV, ["R-DF-04"]),
    C("zone_family_probs", "map<string,float32>", "probability", "each [0, 1], sum <= 1", True, "Borderline zone cases: both probabilities (e.g. 3-2 vs 1-2-2).", CV, ["R-DF-17"]),
    C("l2_active_coverages", "list<string>", None, "DEF.F3/F4/F5/F6 codes", True, "Active coverages this second.", CV, ["R-DF-06", "R-DF-07"], vocab=DEFV),
    C("l3_help_actions", "list<string>", None, "tag, stunt, dig, sink, rotate, x_out, scram, peel, closeout:<type>", True, "Help actions.", CV, ["R-DF-02", "R-DF-15"], vocab=DEFV + " F7"),
    C("l4_pressure_m", "float32", "m", "[0, 10]", True, "On-ball defender distance.", CV, ["R-DF-04"]),
    C("l4_force_dir", "enum[baseline, middle, sideline, none]", None, "enum", True, "Force direction.", CV, ["R-DF-04"], vocab=DEFV + " F2"),
    C("l4_contained", "bool", None, "true/false", True, "Ball contained.", CV, ["R-DF-04"]),
    player_id("rim_protector_id", "Defender nearest the rim ('player C').", null=True, req=["R-DF-03"]),
    C("rim_protector_ball_dist_m", "float32", "m", "[0, 30]", True, "Rim protector's distance to the ball.", CV, ["R-DF-03"]),
    C("shell_centroid_xy_m", "list<float32>", "m", "x, y", True, "Defensive shell centroid.", CV, ["R-DF-11"]),
    C("shell_spread_m", "float32", "m", "[0, 15]", True, "Shell spread (mean distance to centroid).", CV, ["R-DF-11"]),
    C("shell_area_m2", "float32", "m^2", "[0, 220]", True, "Covered area (hull).", CV, ["R-DF-11"]),
    C("press_code", "string", None, "DEF.F9.* or none", True, "Named press when pressing.", CV, ["R-DF-12", "R-DF-18"], vocab=DEFV + " F9"),
    C("is_msu_defending", "bool", None, "true/false", False, "MSU is the defending team (R-DF-13).", CV, ["R-DF-13"]),
], ["R-DF-04", "R-DF-03", "R-DF-11", "R-DF-12", "R-DF-13", "R-DF-17"], "IN_GAME", stamps=True))

TABLES.append(T("scheme_changes", G, "one row per defensive scheme change", ["game_id", "change_id"], [
    game_id(), key("change_id", "sch", ["R-DF-05"]), team_id(defn="Defending team."),
    video_ts("t_trigger_ms"), video_ts("t_switch_complete_ms", null=True),
    C("trigger_type", "enum[timeout_after_run, not_working, inbound_only, score_clock_state, high_post_catch, post_catch, nth_pass, ball_screen, dho, shot_clock_le_10, ball_crossing_half, halftime, unknown]", None, "enum", False, "Trigger (R-DF-19 list plus DEF.F11.6 triggers).", CV, ["R-DF-05", "R-DF-19"], vocab=DEFV + " F11"),
    C("scheme_before", "string", None, "L1 code", False, "Scheme before.", CV, ["R-DF-05"]),
    C("scheme_after", "string", None, "L1 code", False, "Scheme after.", CV, ["R-DF-05"]),
    C("lag_s", "float32", "s", "[0, 30]", True, "Trigger to switch complete.", CV, ["R-DF-05"]),
    C("opp_ppp_before", "float32", "points/possession", "[0, 3]", True, "Opponent PPP over the previous 10 half-court possessions ('not working').", CV, ["R-DF-19"]),
    C("margin", "int16", "points", "[-80, 80]", True, "Defending team's margin.", CV, ["R-DF-19"]),
], ["R-DF-05", "R-DF-14", "R-DF-19"], "IN_GAME", stamps=True))

TABLES.append(T("defensive_matchups", G, "one row per defender per second of live play (per-possession matchup = aggregation view)", ["game_id", "second_index", "defender_id"], [
    game_id(), C("second_index", "int32", "s", ">= 0", False, "Whole seconds of video time.", CV, ["R-DF-01"]), possession_id(),
    player_id("defender_id", "Defender.", req=["R-DF-01"]),
    player_id("attacker_id", "Attacker guarded (canonical guarding point + HMM, DEF.F18.3).", null=True, req=["R-DF-01"]),
    C("matchup_prob", "float32", "probability", "[0, 1]", True, "Posterior of the assignment.", CV, ["R-DF-01"]),
    C("dist_to_man_m", "float32", "m", "[0, 30]", True, "Distance to own man.", CV, ["R-DF-02"]),
    C("dist_to_ball_m", "float32", "m", "[0, 30]", True, "Distance to the ball.", CV, ["R-DF-02"]),
    C("goal_side", "bool", None, "true/false", True, "Between his man and the rim.", CV, ["R-CG-07", "R-TR-08"]),
    C("in_gap", "bool", None, "true/false", True, "In the gap (help position).", CV, ["R-DF-02"]),
    C("is_on_ball", "bool", None, "true/false", False, "Guarding the ball.", CV, ["R-DF-15"]),
    C("is_rim_protector", "bool", None, "true/false", False, "Rim protector this second.", CV, ["R-DF-03"]),
    C("assignment_entropy", "float32", "nats", "[0, 1.61]", True, "Entropy of the assignment distribution.", CV, ["R-DF-01"]),
    C("switched_this_second", "bool", None, "true/false", False, "Assignment changed this second.", CV, ["R-CH-05"]),
    C("mismatch_height_cm", "float32", "cm", "[-60, 60]", True, "Defender minus attacker listed height on a switch.", CV, ["R-DF-09"]),
    C("mismatch_speed_mps", "float32", "m/s", "[-5, 5]", True, "Top-speed difference on a switch.", CV, ["R-DF-09"]),
], ["R-DF-01", "R-DF-02", "R-DF-03", "R-DF-09", "R-OS-04", "R-VL-07"], "IN_GAME", stamps=True))

TABLES.append(T("frame_geometry", G, "one row per frame with a team in control (relative geometry)", ["video_id", "frame_index"], [
    video_sha(), frame_index(), game_id(),
    player_id("handler_id", "Ball handler (null when no one controls the ball; geometry 'none').", null=True, req=["R-CG-07"]),
    C("handler_frame", "list<struct<player_id:string, dist_m:float32, bearing_deg:float32>>", "m; degrees", "9 entries", True, "Every other player's distance and bearing from the handler (0 deg = toward the basket).", CV, ["R-CG-07"]),
    C("driving_cone_deg", "float32", "degrees", "[0, 180]", True, "Angular width of the open cone handler-to-rim.", CV, ["R-CG-07"]),
    C("passing_lanes", "list<struct<receiver_id:string, perp_dist_m:float32, angle_deg:float32>>", "m; degrees", "4 entries", True, "Nearest defender distance from each lane.", CV, ["R-CG-07"]),
    C("spacing_mean_m", "float32", "m", "[0, 20]", True, "Mean pairwise distance of the four off-ball attackers.", CV, ["R-CG-07"]),
    C("hull_area_m2", "float32", "m^2", "[0, 220]", True, "Offense convex hull area.", CV, ["R-CG-07"]),
    C("attacker_nearest_def_m", "list<float32>", "m", "5 entries", True, "Each attacker's distance to the nearest defender.", CV, ["R-CG-07"]),
    C("strong_side_sign", "int8", None, "-1, 0, 1", True, "Sign of the ball's x.", CV, ["R-CG-07"]),
], ["R-CG-07"], "IN_GAME", stamps=True))

G = "Transition"
TABLES.append(T("transition_phases", G, "one row per possession (chance-level twin rows carry chance_id) with every phase timestamp and every transition definition side by side", ["game_id", "possession_id", "chance_id_or_0"], [
    game_id(), possession_id(False),
    C("chance_id_or_0", "int32", None, ">= 0", False, "0 = possession-level row; else chance-level row (R-TR-18 per possession and per chance).", CV, ["R-TR-18"]),
    team_id(defn="Team on offense."),
    C("start_type_code", "string", None, "TR.ST.* (transition_full.md 6.1)", False, "Start type.", CV, ["R-TR-08"], vocab=TRV),
    C("after_stoppage", "bool", None, "true/false", False, "Possession follows a stoppage (FastScout rule).", CV, ["R-TR-19"]),
    C("shot_clock_at_t0_s", "float32", "s", "[0, 30]", True, "Shot clock at t0.", CV, ["R-TR-20"]),
    video_ts("t0_ms", null=True, defn="t0: possession gain (transition_full.md 1.4)."),
    C("t_net_ms", "int64", "ms", "video time", True, "Ball through the net (made-basket anchor, PBP anchor).", CV, ["R-TR-21"]),
    C("t_inbound_release_ms", "int64", "ms", "video time", True, "Inbound release after a make.", CV, ["R-TR-21", "R-TR-14"]),
    C("t_inbound_catch_ms", "int64", "ms", "video time", True, "Inbound catch.", CV, ["R-TR-21", "R-TR-14"]),
    C("phase_times", "map<string,struct<elapsed_s:float32, shot_clock_s:float32>>", "s", "keys: t_outlet, t_cross_half, t_scoring_zone, t_three_zone, t_paint, t_adv_start, t_adv_end, t_first_action, t_first_shot, t_pull, t_flow_entry, t_trailer_arrival, t_drag_screen, t_defense_set_repo, t_defense_set_ctg", True,
      "Every phase timestamp as elapsed time since t0 and as shot-clock reading ('none' = key absent).", CV, ["R-TR-13", "R-TR-20", "R-TR-02"], vocab=TRV),
    C("def_phase_times", "map<string,float32>", "s since t0", "keys: t_protect (first defender r <= 2.5 m), t_first_def_r1p5, t_first_back_past_6p75, t_stop, t_matched, t_switch_back", True, "Defensive-transition timestamps (get back, protect, stop the ball, match up).", CV, ["R-TR-12", "R-DF-20", "R-DF-10"], vocab=TRV + " 3.3"),
    C("defenders_back_at_2_3_4s", "list<int8>", "players", "3 entries each [0, 5]", True, "Defenders back at 2, 3, 4 s.", CV, ["R-DF-20", "R-DF-10"]),
    player_id("ball_stopper_id", "Defender who stopped the ball.", null=True, req=["R-TR-12", "R-DF-10"]),
    player_id("last_back_id", "Last defender back (defense set).", null=True, req=["R-TR-10"]),
    C("seconds_to_defense_set", "float32", "s", "[0, 30]", True, "t0 to defense set (our rule).", CV, ["R-TR-10"]),
    C("numbers_at_t0", "string", None, "e.g. '3v2'", True, "Numbers label at the secure moment (1.0 m margin).", CV, ["R-TR-16", "R-TR-03"]),
    C("transition_class", "enum[primary, early, half_court, uncertain]", None, "enum", True, "Our state class (R-TR-09).", CV, ["R-TR-09", "R-TR-05"]),
    C("tr_state_repo", "bool", None, "true/false", True, "Our state definition (R-TR-08).", CV, ["R-TR-08", "R-TR-18"]),
    C("tr_synergy_like", "bool", None, "true/false", True, "Terminal event before defense set (no clock).", CV, ["R-TR-18"], vocab=TRV + " 5.4"),
    C("tr_ctg_pbp", "bool", None, "true/false", True, "Cleaning the Glass play-by-play style.", CV, ["R-TR-18"]),
    C("tr_ctg_pro_opportunity", "bool", None, "true/false", True, "CTG Pro opportunity.", CV, ["R-TR-18"]),
    C("tr_ctg_pro_is_transition", "bool", None, "true/false", True, "CTG Pro transition.", CV, ["R-TR-18"]),
    C("tr_hoopmath_10s", "bool", None, "true/false", True, "Hoop-Math: first FGA <= 10 s after DREB, steal or opponent score.", CV, ["R-TR-18", "R-TR-11"]),
    C("tr_fastscout_10s", "bool", None, "true/false", True, "FastScout: possession ends with shot clock >= 20 s, not after a stoppage.", CV, ["R-TR-18"]),
    C("tr_fastscout_10s_elapsed", "bool", None, "true/false", True, "FastScout elapsed-time twin.", CV, ["R-TR-18"]),
    C("tr_instat_strict_4_8s", "bool", None, "true/false", True, "InStat 4-8 s.", CV, ["R-TR-18"]),
    C("tr_instat_0_8s", "bool", None, "true/false", True, "InStat 0-8 s.", CV, ["R-TR-18"]),
    C("tr_ncaa_fbp", "bool", None, "true/false", True, "NCAA fast-break points flag.", {"C": "points.fastBreak (game level)", "O": "PBP rule"}, ["R-TR-18", "R-TR-27"]),
    C("tr_fiba_fbp_8s", "bool", None, "true/false", True, "FIBA 8 s fast-break points.", CV, ["R-TR-18"]),
    C("tr_nba_6s_clock", "bool", None, "true/false", True, "NBA-style 6 s on the shot clock (analyst proxy).", CV, ["R-TR-18"]),
    C("tr_nba_6s_elapsed", "bool", None, "true/false", True, "NBA-style 6 s elapsed.", CV, ["R-TR-18"]),
    C("tr_vuhoops_10s", "bool", None, "true/false", True, "VU Hoops 10 s.", CV, ["R-TR-18"]),
    C("tr_ncaa_engine", "bool", None, "true/false", True, "hoopR NCAA engine is_transition / is_fastbreak (source flags).", {"HN": "is_transition, is_fastbreak"}, ["R-TR-18", "R-TR-17"]),
    C("tr_research_windows", "map<string,bool>", None, "keys w5, w6, w7, w8, w10 s", True, "Research windows.", CV, ["R-TR-18"]),
    C("tr_typology", "map<string,string>", None, "keys prim_conte, sec_conte, tr_trninic_type, prim_time_coaching_2_3s, prim_time_fotinakis_3_9s, sec_heuristic, tr_roy_williams_window", True, "Named typology fields (transition_full.md 2.1, 3.4).", CV, ["R-TR-18"], vocab=TRV),
    C("pushed", "bool", None, "true/false", True, "Team pushed (vs pulled back).", CV, ["R-TR-16", "R-TR-14"]),
    C("push_after", "enum[made_fg, made_ft, miss, turnover, not_applicable]", None, "enum", True, "Pushes after makes and made free throws reported separately.", CV, ["R-TR-23", "R-TR-14"]),
    C("end_of_period_flag", "bool", None, "true/false", False, "Starts with <= 60 s left (excluded from reports by default).", CV, ["R-TR-23"]),
    C("opportunity_rules_fired", "list<string>", None, "opportunity rule IDs (transition_full.md 8.2)", True, "Opportunity rules that fired.", CV, ["R-TR-24", "R-TR-16"], vocab=TRV + " 8.2"),
    C("passed_up_reason", "enum[slow_crossing, held_ball, pull_back_with_advantage, ignored_runner, reset, stalled_push, none]", None, "enum", True, "Passed-up reason.", CV, ["R-TR-24"]),
    C("passed_up_category", "enum[declined, denied, failed, stopped_by_foul, not_passed_up]", None, "enum", True, "Category (a pull-back is never 'declined' by default).", CV, ["R-TR-24"]),
    C("context_codes", "list<string>", None, "fatigue, fouls, game_state, press", True, "Context codes, so a pull-back is never counted as declined by default.", CV, ["R-TR-24"]),
    C("foul_id_stopping", "string", None, "fouls key", True, "Foul that stopped the break.", CV, ["R-TR-25"]),
    C("value_at_stake_xpts", "float32", "expected points", "[0, 3]", True, "Value of the break state at the opportunity (shrunk to start-type priors).", {"O": "VL"}, ["R-TR-26", "R-TR-06"]),
], ["R-TR-02", "R-TR-05", "R-TR-08", "R-TR-09", "R-TR-10", "R-TR-11", "R-TR-12", "R-TR-13", "R-TR-14", "R-TR-16", "R-TR-17", "R-TR-18", "R-TR-20", "R-TR-21", "R-TR-23", "R-TR-24", "R-TR-25", "R-TR-26", "R-DF-10", "R-DF-20"], "IN_GAME", stamps=True,
    notes=["One flag per definition, never merged (R-TR-18). Clock rules use the shot-clock era of each game (35 s to 2014-15, 30 s after).",
           "PBP-only rows (every D-I game, R-TR-17) fill only clock-based flags; state-based fields stay null."]))

TABLES.append(T("transition_numbers", G, "one row per 0.1 s x margin during transition (numbers state engine)", ["game_id", "ts_ds", "margin_m"], [
    game_id(), possession_id(),
    C("ts_ds", "int64", "0.1 s", "video time in tenths of a second", False, "Video time in deciseconds.", CV, ["R-TR-22"]),
    C("margin_m", "float32", "m", "{0.5, 1.0, 1.5}", False, "Margin used for the bins (reports use 1.0).", CV, ["R-TR-22"]),
    C("a_play", "int8", "players", "[0, 5]", False, "Attackers level with or ahead of the ball.", CV, ["R-TR-03", "R-TR-22"]),
    C("a_ahead", "int8", "players", "[0, 5]", False, "Attackers ahead.", CV, ["R-TR-22"]),
    C("a_even", "int8", "players", "[0, 5]", False, "Attackers level.", CV, ["R-TR-22"]),
    C("a_behind", "int8", "players", "[0, 5]", False, "Attackers behind.", CV, ["R-TR-22"]),
    C("d_back", "int8", "players", "[0, 5]", False, "Defenders back (between ball and rim).", CV, ["R-TR-03", "R-TR-22"]),
    C("d_even", "int8", "players", "[0, 5]", False, "Defenders level.", CV, ["R-TR-22"]),
    C("d_behind", "int8", "players", "[0, 5]", False, "Defenders beaten.", CV, ["R-TR-22"]),
    C("numbers_label", "string", None, "'<a_play>v<d_back>'", False, "Label, e.g. 3v2.", CV, ["R-TR-03"]),
    C("advantage", "bool", None, "true/false", False, "a_play - d_back >= 1.", CV, ["R-TR-03"]),
    C("uncertain", "bool", None, "true/false", False, "An off-screen player with a weak estimate makes the label uncertain.", CV, ["R-TR-03"]),
    C("ball_y_m", "float32", "m", "[-2.6, 28.05]", True, "Ball y.", CV, ["R-TR-26"]),
    C("handler_speed_mps", "float32", "m/s", "[0, 10]", True, "Handler speed.", CV, ["R-TR-26"]),
    C("value_xpts", "float32", "expected points", "[0, 3]", True, "Value of this break state.", {"O": "VL"}, ["R-TR-06", "R-TR-26"]),
], ["R-TR-03", "R-TR-06", "R-TR-22", "R-TR-26"], "IN_GAME", stamps=True))

TABLES.append(T("transition_roles", G, "one row per possession x player in a break (both directions)", ["game_id", "possession_id", "player_id"], [
    game_id(), possession_id(False), player_id(req=["R-TR-15"]), team_id(),
    C("side_of_ball", "enum[offense, defense]", None, "enum", False, "Offense or defense in the break.", CV, ["R-TR-12"]),
    C("role_synergy", "enum[ball_handler, leak_out, left_wing, right_wing, trailer, none]", None, "enum", True, "Synergy role vocabulary.", CV, ["R-TR-15"], vocab=TRV + " 4"),
    C("role_ctg", "enum[primary_initiator, rim_runner_ahead, rim_runner_trailer, rim_runner_other, left_wing_runner, right_wing_runner, middle_to_left_runner, middle_to_right_runner, trailer, none]", None, "enum", True, "CTG Pro role vocabulary.", CV, ["R-TR-15"], vocab=TRV + " 4"),
    C("lane", "enum[left, middle, right, trailer, none]", None, "enum", True, "Lane filled.", CV, ["R-TR-04"]),
    C("is_initiator", "bool", None, "true/false", False, "Started the break (rebounder, stealer, outlet).", CV, ["R-TR-04"]),
    C("start_area", "enum[below_ft_line_ext, ft_to_arc_ext, beyond_arc_ext]", None, "enum", True, "CTG start area.", CV, ["R-TR-15"]),
    C("seconds_to_scoring_zone", "float32", "s", "[0, 30]", True, "Seconds to y <= 10.29 m.", CV, ["R-TR-04", "R-TR-20"]),
    C("speed_to_scoring_zone_mps", "float32", "m/s", "[0, 10]", True, "Mean speed to the scoring zone.", CV, ["R-TR-04"]),
    C("arrival_rank", "int8", None, "[1, 5]", True, "Arrival order among teammates.", CV, ["R-TR-04"]),
    C("back_before_scoring_zone", "bool", None, "true/false", True, "Defenders: back before the ball reached the scoring zone.", CV, ["R-TR-12", "R-DF-10"]),
], ["R-TR-04", "R-TR-12", "R-TR-15"], "IN_GAME", stamps=True))

G = "Value, load and understanding"
TABLES.append(T("possession_value", G, "one row per 0.1 s of live play (possession value per instant)", ["game_id", "ts_ds"], [
    game_id(), C("ts_ds", "int64", "0.1 s", "video time in tenths", False, "Video time (deciseconds).", CV, ["R-VL-01"]),
    possession_id(), chance_id(), team_id(defn="Team in possession."),
    C("value_xpts", "float32", "expected points", "[0, 4]", False, "Expected points of the current possession from the 10-player state, handler frame, shot clock and metadata.", {"O": "VL model"}, ["R-VL-01", "R-SR-12"]),
    C("p_shot_part", "float32", "expected points", "[0, 4]", True, "Shot component.", {"O": "VL model"}, ["R-VL-03"]),
    C("p_pass_part", "float32", "expected points", "[0, 4]", True, "Pass component.", {"O": "VL model"}, ["R-VL-03"]),
    C("p_turnover_part", "float32", "expected points", "[-4, 0]", True, "Turnover component.", {"O": "VL model"}, ["R-VL-03"]),
    C("outcome_probs", "map<string,float32>", "probability", "PE-02 outcome codes, sum = 1", True, "Outcome probabilities (neural sequence model, R-VL-13).", {"O": "VL model"}, ["R-VL-13", "R-PE-11"]),
    C("calibration_bin", "int8", None, "[0, 19]", True, "Calibration bin used in reports.", {"O": "VL"}, ["R-TR-06"]),
], ["R-VL-01", "R-VL-03", "R-VL-13", "R-SR-12", "R-TR-06"], "IN_GAME", stamps=True))

TABLES.append(T("value_credits", G, "one row per event or action x credited player", ["game_id", "credit_id"], [
    game_id(), key("credit_id", "cr", ["R-VL-02"]),
    C("source_id", "string", None, "events / actions / passes / screens key", False, "What earned the credit.", CV, ["R-VL-02"]),
    player_id(req=["R-VL-02"]), team_id(),
    C("credit_role", "enum[scorer, assister, hockey_assister, screener, gravity, passer, driver, rebounder, on_ball_defender, help_defender, other]", None, "enum", False, "Role.", CV, ["R-VL-09", "R-VL-06", "R-VL-07"]),
    C("value_delta_xpts", "float32", "expected points", "[-4, 4]", False, "Credited value change.", {"O": "VL"}, ["R-VL-02"]),
    C("share", "float32", None, "[0, 1]", False, "Share of the action's value change.", {"O": "VL"}, ["R-VL-09"]),
    C("defender_displacement_m", "float32", "m", "[0, 10]", True, "Gravity: defender displacement caused.", CV, ["R-VL-06"]),
], ["R-VL-02", "R-VL-06", "R-VL-07", "R-VL-09", "R-VL-12"], "IN_GAME", stamps=True))

TABLES.append(T("load_stint_bins", G, "one row per player x stint x 0.1 m/s speed bin", ["game_id", "player_id", "stint_num", "speed_bin_lo_mps"], [
    game_id(), player_id(req=["R-PL-09"]), team_id(),
    C("stint_num", "int16", None, ">= 1", False, "Player stint (continuous floor time).", CV, ["R-PL-09"]),
    C("speed_bin_lo_mps", "float32", "m/s", "0.0, 0.1, ..., 9.9", False, "Lower edge of the 0.1 m/s bin.", CV, ["R-PL-09"]),
    C("time_s", "float32", "s", "[0, 1200]", False, "Observed time in the bin.", CV, ["R-PL-09"]),
    C("distance_m", "float32", "m", "[0, 6000]", False, "Distance in the bin.", CV, ["R-PL-09", "R-PL-01"]),
    C("stint_live_time_s", "float32", "s", "[0, 2700]", False, "Live time in the stint (denominator 1).", CV, ["R-PL-15"]),
    C("stint_minutes_played", "float32", "min", "[0, 45]", False, "Minutes played (headline denominator).", CV, ["R-PL-15"]),
    C("stint_on_court_time_s", "float32", "s", "[0, 4000]", False, "Total on-court time including dead balls.", CV, ["R-PL-15"]),
    C("observed_frac", "float32", None, "[0, 1]", False, "Share of on-court time observed on the main camera.", CV, ["R-PL-05"]),
    C("excluded_low_coverage", "bool", None, "true/false", False, "Stint < 70% detected; left out of load summaries.", CV, ["R-PL-14"]),
    C("tracked_point", "enum[pelvis_floor, ankle_mid]", None, "enum", False, "Tracked point.", CV, ["R-PL-10"]),
    C("filter_name", "string", None, "filter + window", False, "Filter.", CV, ["R-PL-10"]),
    C("fps", "float32", "frames/s", "[25, 60]", False, "Frame rate of the feed.", CV, ["R-PL-13", "R-CO-06"]),
    C("period", "int8", None, "[1, 9]", False, "Period of the stint start.", CV, ["R-PL-03"]),
], ["R-PL-01", "R-PL-03", "R-PL-05", "R-PL-09", "R-PL-10", "R-PL-11", "R-PL-14", "R-PL-15"], "IN_GAME",
    notes=["Every band scheme (R-PL-01 placeholder, R-PL-11 primary bands: stand-walk < 2.0, jog 2.0-4.0, run 4.0-5.0, high-speed 5.0-5.83, sprint > 5.83 m/s) is a view on these bins, so changing a band never means reprocessing video."]))

TABLES.append(T("accel_efforts", G, "one row per acceleration or deceleration effort", ["game_id", "player_id", "effort_id"], [
    game_id(), player_id(req=["R-PL-09"]), key("effort_id", "acc", ["R-PL-09"]),
    C("stint_num", "int16", None, ">= 1", False, "Stint.", CV, ["R-PL-09"]),
    video_ts("start_ts_ms"),
    C("sign", "enum[acceleration, deceleration]", None, "enum", False, "Acceleration or deceleration (gated separately).", CV, ["R-PL-12"]),
    C("peak_mps2", "float32", "m/s^2", "[-4, 4] reported; up to +-12 stored", False, "Peak (nothing above 4 m/s^2 reported).", CV, ["R-PL-02", "R-PL-12"]),
    C("duration_s", "float32", "s", "[0.1, 5]", False, "Duration.", CV, ["R-PL-09"]),
    C("start_speed_mps", "float32", "m/s", "[0, 10]", False, "Start speed.", CV, ["R-PL-09"]),
    C("band", "enum[ge_2p0, ge_3p0]", None, "enum", False, "Band (+-2.0, +-3.0 m/s^2).", CV, ["R-PL-12"]),
    C("continuous_minutes_at_start", "float32", "min", "[0, 45]", True, "Continuous minutes on the floor at the effort start.", CV, ["R-PL-03", "R-CO-07"]),
    C("period", "int8", None, "[1, 9]", False, "Period.", CV, ["R-PL-03"]),
], ["R-PL-02", "R-PL-03", "R-PL-09", "R-PL-12"], "IN_GAME"))

TABLES.append(T("belief_states", G, "one row per second of live play (the system as a viewer)", ["game_id", "second_index"], [
    game_id(), C("second_index", "int32", "s", ">= 0", False, "Whole seconds of video time.", CV, ["R-GU-01"]),
    team_id("ball_team_id", "Who has the ball.", null=True, req=["R-GU-01"]),
    C("phase", "enum[transition, early, half_court, dead]", None, "enum", False, "Phase.", CV, ["R-GU-01"]),
    C("top3_sets", "list<struct<set_code:string, prob:float32>>", "probability", "3 entries", True, "Top 3 candidate sets.", CV, ["R-GU-01"], vocab=OFFV),
    C("defense_scheme_code", "string", None, "L1 code", True, "Defensive scheme.", CV, ["R-GU-01"], vocab=DEFV),
    C("next_action_probs", "map<string,float32>", "probability", "pass, shot, drive, turnover", True, "Next-action probabilities.", CV, ["R-GU-01", "R-GU-05"]),
    C("value_xpts", "float32", "expected points", "[0, 4]", True, "Possession value.", {"O": "VL"}, ["R-GU-01"]),
    C("rule_violations", "list<string>", None, "R-IV rule IDs", True, "Rule-consistency violations logged this second.", CV, ["R-GU-06"]),
    C("narration", "string", None, "free text", True, "Narration written only from the structured state (never an input).", CV, ["R-GU-04"]),
], ["R-GU-01", "R-GU-04", "R-GU-05", "R-GU-06"], "IN_GAME", stamps=True))

G = "Bench, audio and appearance"
TABLES.append(T("bench_events", G, "one row per bench or coach event", ["game_id", "bench_id"], [
    game_id(), key("bench_id", "bench", ["R-CC-04"]), team_id(),
    C("actor_type", "enum[head_coach, assistant, bench_player, staff]", None, "enum", False, "Actor.", CV, ["R-CC-04"]),
    C("actor_id", "string", None, "coach_id or player_id", True, "Actor ID.", CV, ["R-CC-04"]),
    video_ts(),
    C("event_type", "enum[standing, gesturing, talking_to_official, technical_foul, player_pulled_after_error, celebration, timeout_request, challenge_signal, other]", None, "enum", False, "Event.", {"O": "video", "M": "label"}, ["R-CC-03", "R-CC-04"]),
    C("visible_on_broadcast", "bool", None, "true", False, "Logged only when the broadcast shows it.", CV, ["R-CC-04"]),
    evk("linked_event_id"),
], ["R-CC-03", "R-CC-04"], "IN_GAME", stamps=True))

TABLES.append(T("audio_seconds", G, "one row per second of video audio", ["video_id", "second_index"], [
    video_sha(), game_id(), C("second_index", "int32", "s", ">= 0", False, "Second.", {"O": "audio"}, ["R-AU-03"]),
    C("loudness_rel_db", "float32", "dB", "[-40, 40]", True, "Crowd loudness relative to the game median.", {"O": "audio"}, ["R-AU-03"]),
    C("music_flag", "bool", None, "true/false", True, "Arena music during a dead ball (now allowed by rule).", {"O": "audio"}, ["R-AU-04"]),
    C("whistle_present", "bool", None, "true/false", True, "Whistle in this second.", {"O": "audio"}, ["R-RF-01"]),
    C("buzzer_present", "bool", None, "true/false", True, "Horn or buzzer in this second.", {"O": "audio"}, ["R-SR-01"]),
    C("commentary_active", "bool", None, "true/false", True, "Commentary speech present.", {"O": "audio"}, ["R-AU-01"]),
], ["R-AU-03", "R-AU-04", "R-VI-08"], "IN_GAME"))

TABLES.append(T("commentary_segments", G, "one row per transcribed commentary segment (private store)", ["video_id", "segment_id"], [
    video_sha(), game_id(), C("segment_id", "int32", None, ">= 1", False, "Segment.", {"O": "ASR"}, ["R-AU-01"]),
    video_ts("start_ts_ms"), video_ts("end_ts_ms"),
    C("text", "string", None, "free text", False, "Transcript (private; never published).", {"O": "ASR"}, ["R-AU-01", "R-RG-01"]),
    C("mentions", "list<struct<kind:string, value:string, code:string>>", None, "kind in set, defense, player, call", True, "Set, defense, player and call names mentioned, mapped to codes as weak labels.", {"O": "NLP"}, ["R-AU-02"]),
], ["R-AU-01", "R-AU-02"], "IN_GAME"))

TABLES.append(T("appearance_cards", G, "one row per player x game (appearance at tip)", ["game_id", "player_id"], [
    game_id(), player_id(req=["R-ID-12"]), team_id(),
    C("shoes", "string", None, "colour/description", True, "Shoes.", {"O": "video", "M": "confirmed"}, ["R-ID-12"]),
    C("sleeves", "string", None, "none/left/right/both + colour", True, "Arm sleeves.", {"O": "video"}, ["R-ID-12"]),
    C("leg_sleeves", "string", None, "description", True, "Leg sleeves.", {"O": "video"}, ["R-ID-12"]),
    C("headband", "string", None, "description", True, "Headband.", {"O": "video"}, ["R-ID-12"]),
    C("tape", "string", None, "description", True, "Visible tape.", {"O": "video"}, ["R-ID-12"]),
    C("undershirt", "string", None, "description", True, "Undershirt.", {"O": "video"}, ["R-ID-12"]),
    C("jersey_font_id", "string", None, "font registry key", True, "Jersey font (team-season registry).", {"O": "video"}, ["R-DT-18"]),
], ["R-ID-12", "R-ID-13", "R-DT-18"], "IN_GAME",
    notes=["No face data, no face embeddings (R-ID-10, R-PC-15)."]))
