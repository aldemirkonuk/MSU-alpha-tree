from common import *

TABLES = []
R = {"O": "runner / pipeline"}

G = "Simulation and prediction"
TABLES.append(T("simulation_runs", G, "one row per simulation batch for one fixture", ["sim_id"], [
    C("sim_id", "string", None, "'<game_id>:<level>:<as_of>:<seed>'", False, "Simulation key.", R, ["R-PE-12"]),
    game_id(), run_id(),
    C("level", "enum[L0, L1, L2, L3, L4]", None, "enum", False, "Engine level.", R, ["R-PE-10"]),
    utc("as_of_utc", "As-of time of every input (must be before tip for pre-game runs).", req=["R-PE-12", "R-CX-09"], asof="SNAPSHOT"),
    C("n_sims", "int32", "games", ">= 10000", False, "Simulated games.", R, ["R-PR-01"]),
    C("seed", "int64", None, "any", False, "Random seed.", R, ["R-PE-12", "R-EN-02"]),
    C("model_versions", "map<string,string>", None, "component -> version", False, "Versions of each component (outcome, rebound, time, FT, rotation, end-game).", R, ["R-PE-12"]),
    C("input_hashes", "map<string,string>", None, "input -> sha256", False, "Hashes of inputs (pre-game card, ratings, lineups).", R, ["R-PE-12", "R-RR-01"]),
    C("pregame_card_sha256", "string", None, "64 hex", True, "Pre-game card used.", R, ["R-CX-18"]),
    C("param_uncertainty", "enum[posterior_draws, bootstrap_draws, none]", None, "enum", False, "How parameter uncertainty was carried.", R, ["R-PE-09"]),
    C("uses_market_input", "bool", None, "true/false", False, "Variant with line movement as a feature (R-MK-08 keeps both variants apart).", R, ["R-MK-08"]),
    C("uses_video_features", "bool", None, "true/false", False, "L4 video features plugged in through the fixed interface.", R, ["R-PE-11"]),
    C("replay_check_exact", "bool", None, "true/false", True, "Replayed real game reproduced score and possession count exactly.", R, ["R-PE-01"]),
], ["R-PR-01", "R-PE-09", "R-PE-10", "R-PE-11", "R-PE-12", "R-MK-08"], "SNAPSHOT"))

TABLES.append(T("predictions", G, "one row per predicted quantity x fixture x model variant x horizon", ["prediction_id"], [
    C("prediction_id", "string", None, "'<sim_id>:<target>:<team_or_player>'", False, "Prediction key.", R, ["R-MK-07"]),
    game_id(), C("sim_id", "string", None, "simulation_runs key", True, "Simulation (null for non-simulated baselines).", R, ["R-PE-12"]),
    C("target", "enum[win_prob, margin, total, win_prob_1h, margin_1h, total_1h, window5_margin, team_total, player_points, player_rebounds, player_assists, live_win_prob]", None, "enum", False, "Quantity predicted.", R, ["R-PR-02", "R-PR-06", "R-PR-07", "R-PR-11"]),
    C("window_id", "int8", None, "[0, 11]", True, "5-minute window ID for window targets.", R, ["R-PR-06", "R-MD-13"]),
    team_id(null=True, req=["R-PR-02"]), player_id(null=True, req=["R-PR-07"]),
    C("point_value", "float64", "probability or points", "per target", False, "Point estimate (probability for win targets, points otherwise).", R, ["R-PR-02"]),
    C("quantiles", "map<string,float64>", "points", "q05..q95", True, "Distribution quantiles (margins, totals, props).", R, ["R-PR-02", "R-PR-05"]),
    C("interval95", "list<float64>", "per target", "[lo, hi]", True, "95% interval including parameter and simulation uncertainty.", R, ["R-PR-02", "R-PE-09"]),
    C("model_family", "enum[ratings_baseline_kenpom, ratings_baseline_torvik, closing_line_baseline, engine]", None, "enum", False, "Model family (baselines to beat, R-PR-03).", R, ["R-PR-03"]),
    C("level", "enum[L0, L1, L2, L3, L4, none]", None, "enum", False, "Engine level.", R, ["R-PE-10"]),
    C("horizon", "enum[t-24h, t-1h, live]", None, "enum", False, "Freeze horizon.", R, ["R-CX-18", "R-PR-09"]),
    utc("made_at_utc", "When the prediction was made and frozen (before the market snapshot it is compared with).", req=["R-MK-07"], asof="SNAPSHOT"),
    C("frozen_sha256", "string", None, "64 hex", False, "Hash at freeze time.", R, ["R-MK-07"]),
    C("compared_snapshot_key", "string", None, "market_snapshots dedup key", True, "Market snapshot compared with.", {"MK": "SnapshotRow.dedup_key()"}, ["R-MK-05", "R-MK-06"]),
    C("edge", "float64", "probability", "[-1, 1]", True, "Our probability minus the fair market probability.", R, ["R-MK-05"]),
    C("clv", "float64", "probability", "[-1, 1]", True, "Closing-line value: our pre-game probability vs closing fair probability.", R, ["R-MK-06"]),
    C("outcome_value", "float64", "per target", "per target", True, "Realised value (post-game).", R, ["R-PR-05"], asof="POST_GAME"),
    C("log_loss", "float64", "nats", ">= 0", True, "Log loss (post-game).", R, ["R-PR-05", "R-PE-10"], asof="POST_GAME"),
    C("crps", "float64", "points", ">= 0", True, "CRPS for margins and totals (post-game).", R, ["R-PR-05"], asof="POST_GAME"),
    C("pit", "float64", None, "[0, 1]", True, "PIT value (post-game).", R, ["R-PR-05"], asof="POST_GAME"),
    C("is_holdout_2025_26", "bool", None, "true/false", False, "Held-out 2025-26 game, scored once per model family.", R, ["R-PR-04"]),
], ["R-PR-02", "R-PR-03", "R-PR-04", "R-PR-05", "R-PR-06", "R-PR-07", "R-MK-05", "R-MK-06", "R-MK-07"], "SNAPSHOT", stamps=True,
    notes=["Evaluation columns (outcome_value, log_loss, crps, pit) are POST_GAME and are filled only after the game; the prediction itself is frozen at made_at_utc."]))

G = "Runs, errors and review"
TABLES.append(T("run_records", G, "one row per runner run (mirror of run_record.json)", ["run_id"], [
    run_id(),
    C("task_id", "string", None, "coord/tasks id", False, "Task.", R, ["R-RR-01"]),
    C("requirement_ids", "list<string>", None, "R-* IDs", False, "Requirements tested.", R, ["R-RR-01"]),
    C("git_commit", "string", None, "40 hex", False, "Code commit.", R, ["R-RR-01", "R-EN-02"]),
    C("model_versions", "map<string,string>", None, "name -> version@hash", True, "Model versions with hashes.", R, ["R-RR-01"]),
    C("config_hashes", "map<string,string>", None, "file -> sha256", False, "Config versions with hashes.", R, ["R-RR-01", "R-EN-06"]),
    C("input_hashes", "map<string,string>", None, "file -> sha256", False, "Input file hashes.", R, ["R-RR-01"]),
    C("seed", "int64", None, "any", True, "Seed.", R, ["R-RR-01", "R-EN-02"]),
    C("gpu_type", "enum[none, L4, T4, G4, A100, other]", None, "enum", False, "GPU type.", R, ["R-RR-01", "R-CS-01", "R-CS-10"]),
    C("gpu_hours", "float32", "h", ">= 0", False, "GPU-hours.", R, ["R-RR-01", "R-CS-01"]),
    C("compute_units", "float32", "units", ">= 0", False, "Compute units spent.", R, ["R-RR-01", "R-CS-01", "R-CS-02"]),
    utc("start_utc", "Start.", req=["R-RR-01"], asof="RUN"), utc("end_utc", "End.", req=["R-RR-01"], asof="RUN"),
    C("status", "enum[pass, fail, partial, aborted]", None, "enum", False, "Overall status.", R, ["R-RR-02"]),
    C("storage_raw_gb", "float32", "GB", ">= 0", True, "Raw storage per game touched.", R, ["R-CS-05"]),
    C("storage_processed_mb", "float32", "MB", ">= 0", True, "Processed storage written.", R, ["R-CS-05"]),
    C("game_ids", "list<string>", None, "ESPN IDs", True, "Games processed.", R, ["R-FD-02"]),
    C("discrepancy_counts", "map<string,int32>", "count", "per class", True, "Scoreboard discrepancy counts per class (R-SB-04).", R, ["R-SB-04"]),
], ["R-RR-01", "R-RR-02", "R-CS-01", "R-CS-05", "R-EN-02"], "RUN", prov=False,
    storage="repo: results/<task>/run_record.json (counts and metrics only); large artefacts on Drive"))

TABLES.append(T("run_requirement_results", G, "one row per run x requirement x metric (x slice)", ["run_id", "requirement_id", "metric", "slice_key"], [
    run_id(),
    C("requirement_id", "string", None, "R-* ID", False, "Requirement tested.", R, ["R-RR-02"]),
    C("metric", "string", None, "metric name", False, "Metric.", R, ["R-RR-02"]),
    C("slice_key", "string", None, "'all' or 'dim=value'", False, "Slice (camera shot type, arena, jersey pairing, orientation, height px, occlusion, period, ball state, lighting).", R, ["R-RR-03", "R-RR-04"]),
    C("target", "float64", "metric unit", "per metric", True, "Target from config (planner-owned).", R, ["R-RR-02", "R-RR-07"]),
    C("value", "float64", "metric unit", "per metric", True, "Measured value.", R, ["R-RR-02"]),
    C("result", "enum[pass, fail, not_testable, pass_weak_slice]", None, "enum", False, "Result ('not testable' when no gold sample, never 'pass').", R, ["R-RR-02", "R-RR-04"]),
    C("n", "int32", "count", ">= 0", False, "Sample size.", R, ["R-RR-02"]),
    C("ci95_lo", "float64", "metric unit", "per metric", True, "95% interval low (bootstrap by game).", R, ["R-RR-02", "R-VA-06"]),
    C("ci95_hi", "float64", "metric unit", "per metric", True, "95% interval high.", R, ["R-RR-02", "R-VA-06"]),
    C("delta_vs_previous", "float64", "metric points", "per metric", True, "Delta vs previous run on the same gold set.", R, ["R-RR-06"]),
], ["R-RR-02", "R-RR-04", "R-RR-06", "R-VA-06"], "RUN", prov=False, storage="repo: results/<task>/ (metrics only)"))

TABLES.append(T("error_catalogue", G, "one append-only row per failed case across all runs", ["error_id"], [
    C("error_id", "string", None, "'<run_id>:<n>'", False, "Key.", R, ["R-RR-05"]),
    run_id(),
    C("requirement_id", "string", None, "R-* ID", False, "Requirement.", R, ["R-RR-05"]),
    game_id(), video_sha(True), frame_index(null=True), video_ts(null=True),
    C("gold_label", "string", None, "serialised label", False, "Gold label.", R, ["R-RR-05"]),
    C("prediction", "string", None, "serialised prediction", False, "Model output.", R, ["R-RR-05"]),
    C("slice_values", "map<string,string>", None, "slice dim -> value", False, "Slice values.", R, ["R-RR-03", "R-RR-05"]),
    C("model_version", "string", None, "version", False, "Model version.", R, ["R-RR-05"]),
    C("cause", "enum[data, label, model, threshold, upstream_gate, compute, unassigned]", None, "enum (R-RR-03 fixed list)", False, "Cause.", R, ["R-RR-03"]),
    C("worst_case_rank", "int16", None, "[1, 20]", True, "Rank among the run's 20 worst cases.", R, ["R-RR-03"]),
    C("clip_link", "string", None, "private Drive path", True, "Clip link (private).", R, ["R-RR-03"]),
    C("fix_verified", "bool", None, "true/false", False, "Fix verified (outputs kept until then).", R, ["R-RR-08"]),
], ["R-RR-03", "R-RR-05", "R-RR-08"], "RUN", prov=False))

TABLES.append(T("review_queue", G, "one row per flagged item waiting for human review", ["item_id"], [
    C("item_id", "string", None, "'<game_id>:rv:<n>'", False, "Key.", R, ["R-HR-02"]),
    game_id(), video_sha(), video_ts("center_ts_ms"),
    C("clip_window_s", "list<float32>", "s", "[-3, +3]", False, "Clip window around the moment.", R, ["R-HR-02"]),
    C("trigger", "enum[low_identity_confidence, ball_lost_or_scramble, player_count_not_10, scoreboard_pbp_disagree, set_match_low_or_unmatched, coverage_or_matchup_unclear, scoreboard_flag, gold_failed_case, imputation_gap]", None, "enum", False, "Flag trigger (six R-HR-01 triggers + scoreboard flags, failed gold cases, imputation gaps).", R, ["R-HR-01", "R-DT-11", "R-SB-02"]),
    C("target_table", "string", None, "table name", False, "Table whose value is reviewed.", R, ["R-HR-02"]),
    C("target_key", "string", None, "PK of the reviewed row", False, "Row reviewed.", R, ["R-HR-02"]),
    C("model_guess", "string", None, "serialised value", True, "Model's guess, prefilled.", R, ["R-HR-02"]),
    C("priority", "float32", None, ">= 0", False, "Expected gain = uncertainty x downstream impact; failed gold cases first.", R, ["R-HR-03"]),
    C("status", "enum[open, labelled, skipped, expired]", None, "enum", False, "Status.", R, ["R-HR-04"]),
    C("budget_week", "string", None, "ISO week", False, "Review-budget week.", R, ["R-HR-04"]),
], ["R-HR-01", "R-HR-02", "R-HR-03", "R-HR-04"], "LABEL", prov=False))

TABLES.append(T("review_labels", G, "one row per human label (append-only; corrections are new rows)", ["label_id"], [
    C("label_id", "string", None, "'<item_id>:<n>'", False, "Key.", R, ["R-HR-05"]),
    C("item_id", "string", None, "review_queue key", True, "Item (null for gold-set labelling outside the queue).", R, ["R-HR-05"]),
    game_id(),
    C("label_type", "string", None, "e.g. identity, ball_state, control_state, event, set, coverage, transition_class, scoreboard_answer", False, "Kind of label.", R, ["R-HR-08"]),
    C("target_table", "string", None, "table", False, "Table labelled.", R, ["R-HR-05"]),
    C("target_key", "string", None, "row key", False, "Row labelled.", R, ["R-HR-05"]),
    C("value", "string", None, "serialised", False, "Label value.", {"M": "Aldemir"}, ["R-HR-05"]),
    C("action", "enum[confirm, correct]", None, "enum", False, "One-click confirm or correct.", {"M": "Aldemir"}, ["R-HR-02"]),
    C("labeller", "string", None, "name", False, "Who.", {"M": "Aldemir"}, ["R-HR-05", "R-HR-12"]),
    utc("labelled_at_utc", "When.", req=["R-HR-05"], asof="LABEL"),
    C("model_version", "string", None, "version", True, "Model version shown.", R, ["R-HR-05"]),
    C("tool", "string", None, "tool@version (CVAT, Label Studio, FiftyOne, Roboflow)", False, "Labelling tool and version.", R, ["R-HR-05", "R-HR-11"]),
    C("is_repeat_blind", "bool", None, "true/false", False, "Re-shown blind (5% consistency check).", R, ["R-HR-06"]),
    C("agrees_with_previous", "bool", None, "true/false", True, "Agreement with the earlier label on a repeat.", R, ["R-HR-06"]),
    C("prelabel_by", "string", None, "session name", True, "Pre-labelling session (gold-v1).", R, ["R-HR-12"]),
    C("gold_set", "string", None, "e.g. gold-v1", True, "Gold set membership (frozen, never trained on).", R, ["R-HR-07", "R-VA-01"]),
    C("reason", "string", None, "free text", True, "Reason for a correction.", {"M": "Aldemir"}, ["R-SR-15", "R-SB-02"]),
], ["R-HR-05", "R-HR-06", "R-HR-07", "R-HR-08", "R-HR-12", "R-VA-01"], "LABEL", prov=False))

TABLES.append(T("quarantine_rows", G, "one row per row that failed a data contract", ["table_name", "rule_id", "row_hash", "first_seen_utc"], [
    C("table_name", "string", None, "table", False, "Table the row was meant for.", R, ["R-DQ-03"]),
    C("rule_id", "string", None, "contract rule ID (C-*, DQ-*, IV-*)", False, "Rule broken.", R, ["R-DQ-02", "R-DQ-03", "R-MK-21"]),
    C("row_hash", "string", None, "sha256 of row_json", False, "Row hash.", R, ["R-DQ-03"]),
    C("row_json", "string", None, "JSON", False, "The row as received.", R, ["R-DQ-03"]),
    C("raw_ref", "string", None, "raw sha256", True, "Raw pull.", R, ["R-DQ-05"]),
    utc("first_seen_utc", "First seen.", req=["R-DQ-03"], asof="RUN"),
    C("resolved_by", "string", None, "name", True, "Who released or fixed it (Aldemir, with reason).", {"M": "Aldemir"}, ["R-DQ-03"]),
    utc("resolved_utc", "When.", null=True, req=["R-DQ-03"], asof="RUN"),
    C("resolution", "string", None, "free text", True, "Resolution.", {"M": "Aldemir"}, ["R-DQ-03"]),
], ["R-DQ-02", "R-DQ-03", "R-MK-21"], "RUN", prov=False,
    notes=["Same shape as markets QuarantineRow (src/msu_alpha/markets/models.py) plus table_name; nothing in quarantine reaches a model."]))

TABLES.append(T("raw_pulls", G, "one row per external request or file pull (manifest), written before parsing", ["sha256", "fetched_at_utc"], [
    utc("fetched_at_utc", "UTC fetch time (us).", req=["R-DQ-05", "R-MK-13"], asof="RUN"),
    C("source", "string", None, "source code", False, "Source.", R, ["R-DQ-05", "R-RG-08"]),
    C("method", "enum[GET, POST, FILE]", None, "enum", False, "HTTP method or file copy.", R, ["R-MK-12"]),
    C("endpoint", "string", None, "path template", False, "Endpoint or file name.", R, ["R-DQ-05"]),
    C("url", "string", None, "URL without credentials", True, "URL (credentials stripped).", R, ["R-MK-23"]),
    C("status", "int16", None, "HTTP status", True, "Status.", R, ["R-MK-13"]),
    C("headers", "map<string,string>", None, "quota headers", True, "Selected headers (quota).", R, ["R-MK-11", "R-DS-13"]),
    C("sha256", "string", None, "64 hex", False, "Body hash.", R, ["R-DQ-05"]),
    C("byte_length", "int64", "bytes", ">= 0", False, "Size.", R, ["R-MK-13"]),
    C("body_path", "string", None, "private path", False, "Where the raw body is stored (private).", R, ["R-DQ-05", "R-RG-11"]),
    C("collector_version", "string", None, "version", False, "Collector or loader version.", R, ["R-MK-13"]),
    run_id(),
    C("job_id", "string", None, "job", False, "Job.", R, ["R-MK-13"]),
    C("call_budget_counter", "int32", "calls", ">= 0", True, "Running count of calls to this source this month (CBBD 1,000/month shared with CFBD).", R, ["R-DS-13", "R-MK-11"]),
], ["R-DQ-05", "R-MK-13", "R-DS-13", "R-RG-08"], "RUN", prov=False,
    notes=["Same fields as markets ManifestEntry (src/msu_alpha/markets/models.py) plus a call-budget counter; used for every source, not only markets."]))
