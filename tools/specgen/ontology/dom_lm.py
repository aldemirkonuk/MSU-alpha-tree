from core import D, L, G, X

# ======================================================================== L
D("L", "Media and video", "Video files, broadcast camera shots, graphics and scorebug, replays, audio and commentary, and our visual outputs.")

D("L.01", "Video files and timeline", "")
L("L.01.01", "Capture standard and best-quality download", "", req="R-VI-01 R-VI-14", t="video_files.width_px video_files.fps_nominal video_files.bitrate_kbps", s="C")
L("L.01.02", "Intake report", "", req="R-VI-02", t="video_files.intake_dropped_frames video_files.intake_frozen_frames video_files.intake_pass", s="C")
L("L.01.03", "File hash and immutability", "", req="R-FD-09 R-VI-09", t="video_files.video_id video_files.size_bytes", s="C")
L("L.01.04", "Timeline mapping (VFR, interlacing)", "", req="R-VI-12", t="frames.pts_raw frames.is_duplicate_of_prev video_files.interlaced", s="C")
L("L.01.05", "Download provenance and platform terms", "", req="R-RG-10", t="video_files.download_tool video_files.platform_terms_note", s="C")
L("L.01.06", "Processing resolution and hardware decode", "", req="R-VI-15 R-VI-16", t="run_records.processing_resolution", s="C")

D("L.02", "Broadcast picture", "")
L("L.02.01", "Camera shot type (9 classes)", "", req="R-VI-03 R-MD-11 R-SR-10", t="frames.camera_shot_type state_frame.camera_shot_type", v="global_metadata.camera_shot_type", s="C")
L("L.02.02", "Finer camera views (reverse angle, baseline, under-basket, skycam, iso)", "", req="R-SR-10", t="state_frame.reverse_angle", s="P",
  gap=G("VI", "Should", "Camera-view sub-class for non-main frames (reverse angle, baseline/under-basket, high end, skycam, rail, handheld iso, bench, crowd), as a second label beside the 9 shot types.",
        ">= 90% correct on 500 labelled non-main frames (proposal); the 9-class label is unchanged.", "New column frames.camera_view (enum); config vocabulary `camera_views`.", prio=3))
L("L.02.03", "Replays and slow motion", "", req="R-VI-04", t="frames.is_replay frames.replay_segment_id", s="C")
L("L.02.04", "Coverage score and usable possessions", "", req="R-VI-05 R-VI-06", t="frames.coverage_score possessions.usable_flag possessions.coverage_mean", s="C")
L("L.02.05", "Graphics mask (scorebug, lower thirds, wipes)", "", req="R-VI-07", t="frames.graphics_mask_ref detections.inside_graphics_mask", s="C")
L("L.02.06", "Commercial breaks and studio segments", "", req="R-VI-03", t="frames.camera_shot_type", s="C")

D("L.03", "Scorebug and on-screen graphics", "")
L("L.03.01", "Scorebug templates per network", "", req="R-VI-11 R-MD-20", t="scoreboard_ocr.scorebug_template_id games.graphics_package_id", s="C")
L("L.03.02", "Scorebug OCR fields", "", req="R-SY-01 R-SR-15", t="scoreboard_ocr.game_clock_raw scoreboard_ocr.score_home_raw scoreboard_ocr.timeouts_home_raw", s="C")
L("L.03.03", "Scorebug lag vs arena board", "", req="R-SB-01 R-SB-03", t="score_events.board_lag_s scoreboard_flags.flag_type", s="C")
L("L.03.04", "Stat graphics and lower thirds as weak labels", "On-screen graphics announcing fouls, timeouts, player stats or set names.", req="R-VI-07", t="", s="M",
  gap=G("AU", "Should", "Read broadcast stat graphics (player fouls, team fouls, timeouts left, player stat lines) as weak labels with time and confidence, never as truth, and compare them with the state record.",
        "Graphic text read with >= 95% character accuracy on 200 labelled graphics (proposal); every disagreement with the state record logged.", "New table `broadcast_graphics` (video_id, start_ts_ms, end_ts_ms, kind, text, parsed_json, conf).", prio=3))

D("L.04", "Audio and commentary", "")
L("L.04.01", "Whistles", "", req="R-RF-01 R-RF-02", t="whistles.video_ts_ms whistles.masked_by_crowd", s="C")
L("L.04.02", "Buzzers and horns", "Period-end and shot-clock horns, substitution horns.", req="R-MB-06", t="audio_seconds.buzzer_present", s="P",
  gap=G("AU", "Should", "Detect horns and buzzers from audio with kind (period end, shot clock, substitution/timeout horn) and time, linked to the clock state.",
        "Recall >= 90% and timing within +/- 0.1 s on 200 labelled horns (proposal).", "New table `horns` (video_id, ts_ms, kind, linked_event_id) or audio_seconds.buzzer_kind.", prio=3))
L("L.04.03", "Crowd loudness and music flag", "", req="R-AU-03 R-AU-04", t="audio_seconds.loudness_rel_db audio_seconds.music_flag", s="C")
L("L.04.04", "Commentary transcript and weak labels", "", req="R-AU-01 R-AU-02", t="commentary_segments.text commentary_segments.mentions", s="C")
L("L.04.05", "Audio-video alignment", "", req="R-VI-08", t="video_files.audio_offset_ms", s="C")
L("L.04.06", "Broadcast network and crew", "", req="R-MD-20 R-FD-01", t="games.broadcast_network games.broadcast_crew", s="C")

D("L.05", "Visual outputs", "")
L("L.05.01", "Broadcast plus top-down replay in sync", "", req="R-VZ-01 R-VZ-04", t="", s="C")
L("L.05.02", "Traceable numbers with n and interval", "", req="R-VZ-02 R-VZ-03", t="", s="C")
L("L.05.03", "Overlays, boards, palette", "", req="R-VZ-05 R-VZ-06 R-VZ-07", t="", s="C")
L("L.05.04", "Narration from state", "", req="R-GU-04", t="belief_states.narration", s="C")

# ======================================================================== M
D("M", "Data, quality and governance", "Sources, licences, provenance, contracts, invariants, review, errors, versioning, rights and coordination.")

D("M.01", "Sources and licences", "")
L("M.01.01", "Source register and use class", "", req="R-DS-01 R-DS-10 R-DS-02", t="source_register.use_class source_register.terms_url", s="C")
L("M.01.02", "Licence register (datasets, models, libraries)", "", req="R-RG-03 R-RG-04 R-RG-05", t="source_register.permission_status", s="C")
L("M.01.03", "Secrets and keys outside the repo", "", req="R-DS-11 R-DS-13 R-MK-23 R-RG-11", t="", s="C")
L("M.01.04", "Rate limits, call logs and caching", "", req="R-DS-13 R-RG-08 R-MK-11", t="raw_pulls.call_budget_counter source_register.rate_limit", s="C")
L("M.01.05", "Point-in-time ratings only", "", req="R-DS-04", t="ratings_snapshots.is_point_in_time", s="C")
L("M.01.06", "Source definition register (each source's own definitions)", "Each provider's definition of possession, assist, transition, shot zones, fast-break points, minutes.", req="R-TR-11", t="", s="P",
  gap=G("DS", "Shall", "For every source field we ingest that encodes a definition (possession, chance, assist, block, transition/fast break, shot zone, garbage time, minutes), the source's own definition text, URL and date are stored and linked to the column that carries it.",
        "100% of source-derived definitional columns link to a definition row; definitions re-checked each season (R-DS-01).", "New table `source_definitions` (source, field, definition_text, url, checked_on) referenced by docs/data/source_field_map.md.", prio=2))

D("M.02", "Provenance and lineage", "")
L("M.02.01", "Raw copy before parsing", "", req="R-DQ-05 R-MK-13", t="raw_pulls.sha256 raw_pulls.body_path", s="C")
L("M.02.02", "Lineage to raw rows and transform version", "", req="R-DQ-04 R-EN-04", t="state_corrections.correction_id registry_change_log.changed_by", s="C")
L("M.02.03", "Model version, source, confidence on every value", "", req="R-MD-09 R-SR-15", t="events.matched_event_id", s="C")
L("M.02.04", "ID crosswalk", "", req="R-DS-05 R-MK-18", t="id_crosswalk.source_key id_crosswalk.match_confidence", s="C")
L("M.02.05", "As-of rules and leakage tests", "", req="R-CX-09 R-PC-14 R-FD-07 R-MK-07", t="pregame_cards.frozen_at_utc", s="C")

D("M.03", "Quality checks", "")
L("M.03.01", "Data contracts and quarantine", "", req="R-DQ-02 R-DQ-03 R-MK-21", t="quarantine_rows.rule_id", s="C")
L("M.03.02", "Invariants on the state record", "", req="R-IV-01 R-IV-04 R-IV-07", t="scoreboard_flags.invariant_id config/invariants.yaml", s="C",
  note="34 further invariants (new-IV-01..34) are proposed in config/invariants.yaml and listed in the gap table where they close a leaf.")
L("M.03.03", "Accounting identities and completeness", "", req="R-DQ-06 R-DQ-07", t="dq_reports.check dq_reports.value", s="C")
L("M.03.04", "Cross-source checks", "", req="R-DQ-01 R-MK-22 R-SY-10", t="dq_reports.check", s="C")
L("M.03.05", "Drift checks", "", req="R-DQ-08", t="dq_reports.check", s="C")
L("M.03.06", "Known-bias register", "", req="R-DQ-09", t="", s="P", gap=X("(see C.04.04 bias-register proposal)"))
L("M.03.07", "Independent re-derivation", "", req="R-DQ-10", t="dq_reports.check", s="C")
L("M.03.08", "Scoreboard discrepancy classes and answers", "", req="R-SB-01 R-SB-02 R-SB-04", t="scoreboard_flags.flag_type scoreboard_flags.review_answer", s="C")
L("M.03.09", "Ontology coverage check", "Every ontology leaf maps to requirement IDs, tables and vocabularies, re-run when the doc or schema changes.", req="R-CD-02", t="config/game_ontology.yaml", s="P",
  gap=G("CD", "Shall", "config/game_ontology.yaml is kept in step with the live requirements and schema: a check script fails when a leaf cites an unknown requirement ID or column, or when a requirement or table is referenced by no leaf.",
        "Script exits 0 on the current repo; run in repository tests (R-EN-08); the coverage statistics in docs/data/game_ontology_coverage.md are regenerated by it.", "New script scripts/check_ontology.py; config/game_ontology.yaml (proposal written 2026-10-18).", prio=2))

D("M.04", "Review, labels and validation", "")
L("M.04.01", "Flag triggers and review queue", "", req="R-HR-01 R-HR-02 R-HR-03 R-HR-04", t="review_queue.trigger review_queue.priority", s="C")
L("M.04.02", "Labels with provenance and consistency", "", req="R-HR-05 R-HR-06 R-HR-10", t="review_labels.labeller review_labels.is_repeat_blind", s="C")
L("M.04.03", "Gold sets frozen", "", req="R-HR-07 R-HR-12 R-VA-01", t="review_labels.gold_set", s="C")
L("M.04.04", "Gates and robustness", "", req="R-GT-01 R-GT-02 R-GT-03 R-GT-04", t="run_requirement_results.gate run_requirement_results.robustness_variant", s="C")
L("M.04.05", "Metrics and intervals (HOTA, bootstrap by game, multiple testing)", "", req="R-VA-04 R-VA-05 R-VA-06 R-VA-07", t="run_requirement_results.ci95_lo", s="C")
L("M.04.06", "External consultant (JEV) log", "Outside verdicts, never read by the pipeline.", req="R-HY-07", t="", s="P",
  gap=G("HR", "Shall", "JEV consultations (J1-J9) are logged in a private table outside the pipeline's read path (question ID, items sent, options shown, JEV answer, model version), and an automated test proves no pipeline module reads it.",
        "Log row per consultation with exact model version; import-graph test shows 0 pipeline reads of the JEV log.", "New private table `jev_log` (not in schema/tables read path); test in tests/.", prio=3))

D("M.05", "Runs, errors and compute", "")
L("M.05.01", "Run records and requirement results", "", req="R-RR-01 R-RR-02 R-RR-04 R-RR-06", t="run_records.run_id run_requirement_results.result", s="C")
L("M.05.02", "Error catalogue and failure analysis", "", req="R-RR-03 R-RR-05", t="error_catalogue.cause error_catalogue.slice_values", s="C")
L("M.05.03", "Compute and storage accounting", "", req="R-CS-01 R-CS-02 R-CS-05", t="run_records.gpu_hours run_records.storage_raw_gb", s="C")
L("M.05.04", "Reproducibility, resumable chunks, versioned outputs", "", req="R-EN-02 R-EN-05 R-EN-07", t="run_records.seed run_records.chunks_done", s="C")

D("M.06", "Governance and coordination", "")
L("M.06.01", "Schemas, units in names, thresholds in config", "", req="R-EN-01 R-EN-06 R-MK-31", t="schema/global_metadata.yaml", s="C")
L("M.06.02", "Registry versioning and change log", "", req="R-FD-10", t="registry_change_log.old_value registry_change_log.reason", s="C")
L("M.06.03", "Vocabulary map", "", req="R-MD-10 R-ST-15 R-ST-22", t="config/vocabulary_map.yaml", s="C")
L("M.06.04", "Rights gate, privacy and footage control", "", req="R-RG-01 R-RG-02 R-RG-06 R-RG-11 R-MK-24", t="", s="C")
L("M.06.05", "Read-only market collection", "", req="R-RG-07 R-MK-12 R-MK-19", t="config/markets.yaml", s="C")
L("M.06.06", "Board, protocol, user inputs, freeze", "", req="R-CD-01 R-CD-03 R-CD-04 R-CD-05", t="", s="C")
L("M.06.07", "Hypothesis protocol", "", req="R-HY-01 R-HY-03 R-HY-04 R-HY-05", t="hypothesis_results.decision config/hypotheses.yaml", s="C")
L("M.06.08", "Taxonomy detection signatures", "", req="R-ST-16", t="", v="OFF DEF MS", s="C")
