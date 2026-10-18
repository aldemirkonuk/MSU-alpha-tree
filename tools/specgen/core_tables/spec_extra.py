"""Second pass: tables and columns added after the requirement-coverage check."""
from common import *
import spec_registry, spec_pbp, spec_cv, spec_actions, spec_ops

ALL = spec_registry.TABLES + spec_pbp.TABLES + spec_cv.TABLES + spec_actions.TABLES + spec_ops.TABLES
BY = {t["name"]: t for t in ALL}
CV = {"O": "computed by us"}
R = {"O": "runner / pipeline"}
TABLES = []


def add_reqs(name, *reqs):
    for r in reqs:
        if r not in BY[name]["reqs"]:
            BY[name]["reqs"].append(r)


def add_cols(name, *cols):
    BY[name]["cols"].extend(cols)


add_reqs("ball_states", "R-BL-07")
add_cols("ball_states", C("out_of_bounds_event", "bool", None, "true/false", False, "Ball crossed a boundary this frame (starts inbound pending).", CV, ["R-BL-07", "R-MD-03"]))
add_reqs("tracks", "R-ID-07", "R-ID-09")
add_cols("tracks",
         C("restored_after", "enum[none, camera_cut, replay, timeout, substitution]", None, "enum", True, "Identity restored after this interruption.", CV, ["R-ID-07"]),
         C("agrees_with_pbp_lineup", "bool", None, "true/false", True, "Assigned identity is in the PBP lineup for the possession.", CV, ["R-ID-09", "R-ID-03"]))
add_reqs("transition_numbers", "R-TR-01")
add_cols("transition_numbers", C("seconds_since_t0", "float32", "s", "[0, 60]", True, "Transition clock: seconds since the change of possession (secure catch, or inbound release after a make).", CV, ["R-TR-01"]))
add_reqs("scheme_states", "R-DF-21")
add_cols("scheme_states", C("msu_principle_flags", "list<string>", None, "high_post_flash_denial, jump_to_ball, stack_3v2_rule, transition_defense_flag", True, "MSU-specific principle checks that fired this second.", CV, ["R-DF-21"], vocab="docs/taxonomy/defense_full.md F1.6"))
add_reqs("set_instances", "R-ST-13")
add_cols("set_instances", C("classifier_probs", "map<string,float32>", "probability", "set code -> prob", True, "Learned sequence classifier output kept beside the template match.", CV, ["R-ST-13"]))
add_reqs("simulation_runs", "R-PE-05", "R-PE-08", "R-PE-13")
add_cols("simulation_runs", C("component_diagnostics", "map<string,float64>", "points", "outcome_mix, rebounds, time, free_throws, rotations", True, "Contribution of each engine step to the simulated-vs-actual margin miss (post-game).", R, ["R-PE-13"], asof="POST_GAME"))
add_reqs("predictions", "R-MK-09", "R-PR-08", "R-PR-10")
add_cols("predictions",
         C("paper_stake_frac", "float32", "fraction of bankroll", "[0, 0.25 x Kelly], capped", True, "Paper staking only (no bets, R-RG-07).", R, ["R-MK-09", "R-RG-07"]),
         C("priced_events_in_market", "int32", "count", ">= 0", True, "Priced events in this market so far (no edge claim under 200 unless pre-registered).", R, ["R-PR-08"]))
add_reqs("run_records", "R-MK-20", "R-EN-05", "R-VI-15", "R-CS-04")
add_cols("run_records",
         C("chunks_done", "list<string>", None, "chunk IDs", True, "Finished chunks (resumable processing).", R, ["R-EN-05"]),
         C("processing_resolution", "string", None, "e.g. 'detect 1280x720; crops native'", True, "Two-resolution processing used.", R, ["R-VI-15"]),
         C("frame_policy", "string", None, "free text", True, "Frame policy (full rate on main-camera live play).", R, ["R-CS-04"]))
add_reqs("run_requirement_results", "R-VA-02", "R-VA-03", "R-VA-04", "R-VA-05", "R-VA-09", "R-GT-01", "R-GT-02", "R-GT-04", "R-HR-09")
add_cols("run_requirement_results",
         C("gate", "enum[G1, G2, G3, G4, G5, G6, G7, G8, none]", None, "enum", False, "Vision gate tested.", R, ["R-GT-04"]),
         C("source_tier", "enum[youtube_below_1080p, youtube_1080p, b1g_plus, other]", None, "enum", True, "Footage tier.", R, ["R-GT-03"]),
         C("robustness_variant", "enum[none, dropped_1pct, low_bitrate, brightness_minus20, brightness_plus20]", None, "enum", False, "Robustness re-test.", R, ["R-GT-02"]),
         C("hold_game", "bool", None, "true/false", False, "Unseen hold game from a different arena.", R, ["R-GT-01"]),
         C("descriptive_only", "bool", None, "true/false", False, "95% interval half-width above the minimum-count rule.", R, ["R-VA-05", "R-VZ-03"]))
add_reqs("review_labels", "R-HR-10", "R-ST-10")
add_reqs("load_stint_bins", "R-PL-04")

G = "Profiles, quality and research"
TABLES.append(T("profile_snapshots", G, "one row per entity x metric x as-of date (team, coach, player, pair or lineup profiles from games before that date)", ["entity_type", "entity_id", "metric_code", "as_of_date"], [
    C("entity_type", "enum[team, coach, player, pair, lineup, opponent_vs_msu_set]", None, "enum", False, "Entity profiled.", CV, ["R-FD-07"]),
    C("entity_id", "string", None, "team_id / coach_id / player_id / 'p1-p2' / lineup_key", False, "Entity.", CV, ["R-FD-07"]),
    season(),
    C("metric_code", "string", None, "registry of profile metrics (pace, four factors, shot profile by sector and ring, set frequency per OFF code, scheme frequency per DEF code, rotation depth, timeout timing vs runs, timeouts left at half end, first set after timeout value, halftime changes, h2h record, prior-meeting sets and schemes, playbook frequency, template-match share, ball-screen concentration, time to first shot, scheme policy by context, pair coordination lag, passing network observed vs expected, clean vs late switches, after-error behaviour, communication proxies, season load trend, match reference speed)", False,
      "Profile metric.", CV, ["R-FD-07", "R-OS-01", "R-OS-02", "R-CC-02", "R-CC-05", "R-CH-02", "R-CH-03", "R-CH-05", "R-CH-06", "R-CH-07", "R-CH-08", "R-ST-14", "R-ST-25", "R-DF-14", "R-CO-05", "R-CO-07", "R-CO-08", "R-PL-06", "R-PL-16", "R-CX-19", "R-OS-03"]),
    C("value", "float64", "per metric", "per metric", False, "Value.", CV, ["R-FD-07"]),
    C("n", "int32", "count", ">= 0", False, "Sample size behind the value.", CV, ["R-VA-05", "R-VZ-03"]),
    C("ci95", "list<float64>", "per metric", "[lo, hi]", True, "95% interval (bootstrap by game).", CV, ["R-VA-06"]),
    C("as_of_date", "date", None, "date", False, "Profile uses only games before this date.", CV, ["R-FD-07", "R-CX-09"]),
    C("games_used", "int16", "games", ">= 0", False, "Games used.", CV, ["R-FD-07"]),
    C("prior_season_fallback", "bool", None, "true/false", False, "Season opener: prior season used, flagged.", CV, ["R-FD-07"]),
    C("source_basis", "enum[pbp, video, mixed, ratings]", None, "enum", False, "Opponent depth comes from data sources; our video covers opponents only against MSU.", CV, ["R-OS-05"]),
], ["R-FD-07", "R-OS-01", "R-OS-02", "R-CC-02", "R-CC-05", "R-CH-02", "R-CH-03", "R-CH-07", "R-ST-14", "R-ST-25", "R-CX-19"], "SNAPSHOT",
    notes=["Recomputing a profile from a truncated game list must give identical values (R-FD-07 test)."]))

TABLES.append(T("position_forecasts", G, "one row per player per second (short-horizon forecast)", ["game_id", "second_index", "player_id"], [
    game_id(), C("second_index", "int32", "s", ">= 0", False, "Second of video time.", CV, ["R-TR-07"]), player_id(req=["R-TR-07"]),
    C("forecast_1s_xy_m", "list<float32>", "m", "x, y", True, "Forecast position 1 s ahead.", CV, ["R-TR-07"]),
    C("forecast_2s_xy_m", "list<float32>", "m", "x, y", True, "Forecast position 2 s ahead.", CV, ["R-TR-07"]),
    C("error_1s_m", "float32", "m", "[0, 30]", True, "Realised error at 1 s (filled later).", CV, ["R-TR-07"]),
    C("error_2s_m", "float32", "m", "[0, 30]", True, "Realised error at 2 s.", CV, ["R-TR-07"]),
], ["R-TR-07", "R-GU-05"], "IN_GAME", stamps=True))

TABLES.append(T("reaction_events", G, "one row per defender x trigger (pass release or cut start)", ["game_id", "reaction_id"], [
    game_id(), C("reaction_id", "string", None, "'<game_id>:rx:<n>'", False, "Key.", CV, ["R-CO-02"]),
    player_id("defender_id", "Defender.", req=["R-CO-02"]),
    C("trigger_id", "string", None, "passes / movement_primitives key", False, "Trigger.", CV, ["R-CO-02"]),
    C("trigger_type", "enum[pass_release, cut_start, drive_start, screen_moment]", None, "enum", False, "Trigger type.", CV, ["R-CO-02"]),
    C("latency_s", "float32", "s", "[-1.5, 3]", True, "Onset (acceleration change > 1 m/s^2 toward the new threat, proposal) minus trigger; negative = anticipation.", CV, ["R-CO-02", "R-CO-03", "R-DF-08"]),
    C("frame_uncertainty_s", "float32", "s", "1/fps", False, "Timing resolution (one frame).", CV, ["R-CO-06"]),
    C("outcome", "enum[deflection, steal, contest, recovered, beaten, none]", None, "enum", True, "Outcome.", CV, ["R-CO-03"]),
    C("closeout_distance_m", "float32", "m", "[0, 15]", True, "Closeout distance.", CV, ["R-DF-08"]),
    C("closeout_speed_mps", "float32", "m/s", "[0, 10]", True, "Closeout speed.", CV, ["R-DF-08"]),
], ["R-CO-02", "R-CO-03", "R-CO-06", "R-DF-08"], "IN_GAME", stamps=True))

TABLES.append(T("identity_confusions", G, "one row per game x pair of players mixed up", ["game_id", "player_a_id", "player_b_id", "run_id"], [
    game_id(), run_id(),
    player_id("player_a_id", "First player.", req=["R-ID-11"]), player_id("player_b_id", "Second player.", req=["R-ID-11"]),
    C("n_confusions", "int32", "count", ">= 0", False, "Times mixed up.", CV, ["R-ID-11"]),
    C("player_frames", "int32", "frames", ">= 0", False, "Player-frames at risk.", CV, ["R-ID-11", "R-ID-14"]),
], ["R-ID-11", "R-ID-14"], "RUN", prov=False))

TABLES.append(T("dq_reports", G, "one row per game x table x field x check", ["game_id", "table_name", "field", "check"], [
    game_id(),
    C("table_name", "string", None, "table", False, "Table.", CV, ["R-DQ-07"]),
    C("field", "string", None, "column or '*'", False, "Field.", CV, ["R-DQ-07"]),
    C("check", "enum[completeness, psi_drift, accounting_identity, cross_source, stage_check, re_derivation]", None, "enum", False, "Check.", CV, ["R-DQ-07", "R-DQ-08", "R-DQ-06", "R-DQ-01", "R-EN-03", "R-DQ-10"]),
    C("value", "float64", "share / PSI / count", "per check", False, "Result (fill share; PSI; mismatches).", CV, ["R-DQ-07", "R-DQ-08"]),
    C("flag", "bool", None, "true/false", False, "Fill < 95%, PSI > 0.25, or identity broken (proposals).", CV, ["R-DQ-07", "R-DQ-08"]),
    C("note", "string", None, "free text", True, "Logged reason.", CV, ["R-DQ-06"]),
], ["R-DQ-01", "R-DQ-06", "R-DQ-07", "R-DQ-08", "R-DQ-10", "R-EN-03", "R-VA-03"], "RUN", prov=False))

TABLES.append(T("coach_quiz", G, "one row per quiz question at a paused moment", ["game_id", "quiz_id"], [
    game_id(), C("quiz_id", "string", None, "'<game_id>:q:<n>'", False, "Key.", CV, ["R-GU-03"]), video_ts(),
    C("question", "enum[who_guards_x, which_set, which_defense, what_happens_next]", None, "enum", False, "Question.", CV, ["R-GU-03"]),
    C("system_answer", "string", None, "serialised", False, "System answer from belief_states.", CV, ["R-GU-03"]),
    C("aldemir_answer", "string", None, "serialised", True, "Aldemir's answer.", {"M": "Aldemir"}, ["R-GU-03"]),
    C("correct", "bool", None, "true/false", True, "Agreement.", CV, ["R-GU-03"]),
], ["R-GU-03"], "LABEL", prov=False))

TABLES.append(T("hypothesis_results", G, "one row per hypothesis test", ["hypothesis_id", "test_date"], [
    C("hypothesis_id", "string", None, "H<n>[a] / alias JEV-<n>", False, "Hypothesis (config/hypotheses.yaml).", R, ["R-HY-05", "R-HY-07"]),
    C("test_date", "date", None, "date", False, "Date tested.", R, ["R-HY-05"]),
    C("estimate", "float64", "per metric", "per metric", True, "Estimate.", R, ["R-HY-05"]),
    C("ci95", "list<float64>", "per metric", "[lo, hi]", True, "Interval.", R, ["R-HY-05"]),
    C("p_adjusted", "float64", None, "[0, 1]", True, "Adjusted p (Holm within family; BH across exploratory).", R, ["R-HY-05", "R-VA-07"]),
    C("n", "int32", "count", ">= 0", False, "Sample size (set by Aldemir beforehand).", R, ["R-HY-02"]),
    C("achieved_power", "float32", None, "[0, 1]", True, "Achieved power.", R, ["R-HY-02"]),
    C("data_version", "string", None, "version", False, "Data version.", R, ["R-HY-05"]),
    C("decision", "enum[supported, not_supported, inconclusive]", None, "enum", False, "Decision (null results reported in the same format).", R, ["R-HY-05", "R-VA-08"]),
    C("exploratory", "bool", None, "true/false", False, "Exploratory (promoted only after held-out confirmation).", R, ["R-HY-04"]),
], ["R-HY-01", "R-HY-02", "R-HY-04", "R-HY-05", "R-VA-07", "R-VA-08"], "RUN", prov=False,
    storage="repo allowed (derived statistics only): results/hypotheses/"))

TABLES.append(T("source_register", G, "one row per data source x check date", ["source", "checked_on"], [
    C("source", "string", None, "source code", False, "Source.", R, ["R-DS-01"]),
    C("checked_on", "date", None, "date", False, "Date terms and access re-checked (each season).", R, ["R-DS-01"]),
    C("cost", "string", None, "free text", True, "Cost.", R, ["R-DS-01", "R-DS-07"]),
    C("access", "string", None, "free text", True, "Access method.", R, ["R-DS-01"]),
    C("seasons", "string", None, "range", True, "Seasons.", R, ["R-DS-01"]),
    C("granularity", "string", None, "free text", True, "Finest granularity.", R, ["R-DS-01"]),
    C("use_class", "enum[model_input_allowed, reference_only, blocked_until_permission]", None, "enum", False, "Use class.", R, ["R-DS-10", "R-DS-02"]),
    C("terms_url", "string", None, "URL", True, "Terms page.", R, ["R-RG-08", "R-RG-03"]),
    C("rate_limit", "string", None, "free text", True, "Rate limit / quota.", R, ["R-RG-08", "R-DS-13"]),
    C("permission_status", "string", None, "free text", True, "Permission requests and replies.", R, ["R-DS-12"]),
], ["R-DS-01", "R-DS-02", "R-DS-10", "R-DS-12", "R-RG-03", "R-RG-08"], "RUN", prov=False,
    storage="repo allowed (no data): mirrors docs/research/data_sources_catalog.md"))

G2 = "Player-game links (requested by W1)"
TABLES.append(T("player_game_context", G2, "one row per player x game (game-specific values the W1 card does not hold)", ["game_id", "player_id"], [
    game_id(), player_id(req=["R-PC-01", "R-PC-03"]), team_id(),
    C("age_at_tip_years", "float32", "years", "[16, 30]", True, "Age at tip ((tip date - birth date) / 365.2425); from class when birth date is not public (flagged).", CV, ["R-PC-01"]),
    C("dist_hometown_to_venue_km", "float32", "km", "[0, 20000]", True, "Great-circle distance from the player's hometown (W1 card coordinates) to the venue.", CV, ["R-PC-03"]),
    C("dist_hometown_to_campus_km", "float32", "km", "[0, 20000]", True, "Hometown to campus (repeated from the card for joins).", CV, ["R-PC-03"]),
    C("card_snapshot_ref", "string", None, "player_cards key (W1)", True, "Card snapshot valid at this tip (R-PC-14).", CV, ["R-PC-14"]),
    C("jersey_number", "string", None, "'0'..'99', '00'", True, "Number worn in this game (jersey_history).", CV, ["R-FD-03", "R-ID-04"]),
    C("is_starter", "bool", None, "true/false", True, "Started.", {"C": "players[].starter", "HE": "starter"}, ["R-SY-03"]),
    C("minutes_limit_known", "bool", None, "true/false", True, "A public minutes limit was known before tip.", {"M": "availability"}, ["R-CX-08"]),
], ["R-PC-01", "R-PC-03", "R-PC-14"], "PRE_TIP",
    fks=[("game_id", "games.game_id"), ("player_id", "players.player_id")]))

TABLES.append(T("player_shooting_sector_ring", G2, "one row per player x as-of date x sector x ring x shot context", ["player_id", "as_of_date", "sector_15deg", "ring_0p5m", "shot_context"], [
    player_id(req=["R-PC-06"]), season(),
    C("as_of_date", "date", None, "date", False, "Uses only shots before this date.", CV, ["R-PC-14", "R-FD-07"]),
    C("sector_15deg", "int8", None, "[0, 11]", False, "15-degree sector (geometry.sector).", CV, ["R-PC-06", "R-CG-05"]),
    C("ring_0p5m", "int8", None, "[0, 60]", False, "0.5 m ring (geometry.ring).", CV, ["R-PC-06", "R-CG-05"]),
    C("shot_context", "enum[all, catch_and_shoot, off_dribble]", None, "enum", False, "Shot context.", CV, ["R-PC-06"]),
    C("fga", "int16", "count", ">= 0", False, "Attempts.", {"O": "shots", "HN": "shot_x/shot_y (2019+)", "HE": "coordinate_x/y"}, ["R-PC-06"]),
    C("fgm", "int16", "count", ">= 0", False, "Makes.", {"O": "shots"}, ["R-PC-06"]),
    C("rate_shrunk", "float32", "probability", "[0, 1]", True, "Make rate shrunk toward the prior (prior stated in prior_code).", CV, ["R-PC-06", "R-VL-12"]),
    C("prior_code", "string", None, "prior name + version", True, "Shrinkage prior.", CV, ["R-PC-06"]),
    C("location_source", "enum[video, espn, cbbd, ncaa, mixed]", None, "enum", False, "Where the locations came from (manual entry error, R-DQ-09).", CV, ["R-DQ-09", "R-SY-07"]),
], ["R-PC-06", "R-PC-14", "R-VL-12"], "SNAPSHOT"))
