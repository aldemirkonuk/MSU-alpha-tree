from core import D, L, G, X, EXT

# ---------------- L.06 Perception from video (how the game is observed)
D("L.06", "Perception from video", "Detection, team assignment, tracking, identity, ball events and made-basket fusion: how each on-court entity becomes data.")
L("L.06.01", "Person detection and person filter", "", req="R-DT-01 R-DT-02 R-DT-17", t="detections.person_class detections.bbox_px", s="C")
L("L.06.02", "Team label per detection", "", req="R-DT-03 R-CX-07", t="detections.team_label detections.team_label_conf", s="C")
L("L.06.03", "Persistent tracks, track quality and gaps", "", req="R-DT-04 R-DT-11", t="tracks.track_id tracks.quality_mean tracks.gaps_over_1s", s="C")
L("L.06.04", "Frame-exit memory and off-screen estimates", "", req="R-DT-06 R-DT-07", t="track_exits.exit_side track_exits.exit_speed_mps player_positions.region95_semi_axes_m", s="C")
L("L.06.05", "Ground point at the feet", "", req="R-CG-04", t="detections.foot_point_px", s="C")
L("L.06.06", "Player identity (lineup-constrained, jersey numbers, orientations)", "", req="R-ID-01 R-ID-02 R-ID-03 R-ID-04 R-ID-05 R-ID-08 R-ID-09", t="tracks.player_id tracks.jersey_number_voted detections.orientation_slice", s="C")
L("L.06.07", "Identity re-confirmation and restoration", "", req="R-ID-06 R-ID-07 R-ID-13", t="tracks.restored_after tracks.id_switches_corrected", s="C")
L("L.06.08", "Identity confusions and per-player accuracy", "", req="R-ID-11 R-ID-14", t="identity_confusions.n_confusions", s="C")
L("L.06.09", "Synthetic kit images (team colour only)", "", req="R-ID-15", t="", s="C")
L("L.06.10", "Ball detection, holder and event times", "", req="R-BL-01 R-BL-02 R-BL-04", t="ball_states.image_xy_px passes.release_ts_ms passes.catch_ts_ms", s="C")
L("L.06.11", "Make or miss and made-basket fusion", "", req="R-BL-05 R-MB-01 R-MB-02 R-MB-03 R-MB-04", t="made_basket_events.decision made_basket_events.cue1_present", s="C")
L("L.06.12", "Short-horizon position forecasts", "", req="R-TR-07 R-GU-05", t="position_forecasts.forecast_1s_xy_m position_forecasts.error_1s_m", s="C")
L("L.06.13", "Public tracking-set sanity checks and source comparison", "", req="R-GT-05 R-VI-10", t="run_requirement_results.source_tier", s="C")
L("L.06.14", "Officials and non-players detected separately", "", req="R-DT-12 R-DT-02", t="official_positions.observed", s="C")

# ---------------- extra leaves elsewhere
L("C.01.21", "Shooting block (sector x ring, shrunk)", "", req="R-PC-06", t="player_shooting_sector_ring.rate_shrunk player_shooting_sector_ring.prior_code", s="C")
L("C.01.22", "Playmaking and ball security block", "", req="R-PC-07", t="profile_snapshots.metric_code player_card.ast_pct player_card.tov_pct", s="C")
L("C.01.23", "Prior-level physicality", "", req="R-PC-09", t="profile_snapshots.metric_code", s="C")
L("H.04.07", "Passing network and movement coordination", "Observed vs expected passes per pair, lag and phase of movements, screener-handler timing.", req="R-CH-02 R-CH-03 R-CH-04", t="passes.passer_id passes.receiver_id screens.screener_handler_timing_s", s="C")
L("H.05.07", "Possession-engine components", "Rebound, time, free-throw, rotation models, population-first fitting, uncertainty, levels, video interface, logging, diagnostics.",
  req="R-PE-03 R-PE-04 R-PE-05 R-PE-08 R-PE-09 R-PE-11 R-PE-12 R-PE-13", t="simulation_runs.level simulation_runs.param_uncertainty simulation_runs.component_diagnostics", s="C")
L("H.05.08", "Baselines, walk-forward and sample rules", "", req="R-PR-03 R-PR-04 R-PR-08 R-PR-09 R-PR-10", t="predictions.is_holdout_2025_26 predictions.priced_events_in_market", s="C")
L("K.01.15", "Opposing coaches' records", "", req="R-CH-07", t="coaches.coach_id profile_snapshots.metric_code", s="C")
L("D.09.07", "Coach quiz and belief consistency", "System answers at paused moments; rule consistency of the belief.", req="R-GU-03 R-GU-06", t="coach_quiz.correct belief_states.rule_violations", s="C")
L("M.02.06", "Event model (one row per event, chains, unmatched stream)", "", req="R-EV-01 R-EV-12 R-SR-14 R-SY-02", t="events.event_family events.chain_index cv_events_unmatched.unmatched_reason", s="C")
L("M.06.09", "Pitch package", "", req="R-PT-01", t="", s="C")

# ---------------- extensions of existing leaves
EXT("F.01.01", req="R-TR-10 R-TR-02", t="transition_phases.seconds_to_defense_set")
EXT("F.01.07", req="R-TR-06")
EXT("F.01.02", req="R-TR-17 R-TR-28")
EXT("F.13.01", req="R-ST-13", t="set_instances.classifier_probs")
EXT("J.03.05", req="R-OS-03")
EXT("J.05.01", req="R-MK-17 R-MK-26 R-MK-27 R-MK-28 R-MK-29", t="lines_odds_snapshots market_snapshots.line_is_integer")
EXT("J.05.02", req="R-MK-10 R-MK-25 R-MK-33")
EXT("J.05.03", t="prediction_market_prices")
EXT("J.05.04", req="R-MK-32")
EXT("H.05.06", req="R-MK-09", t="predictions.paper_stake_frac")
EXT("M.01.01", req="R-DS-06 R-DS-08 R-DS-09 R-DS-12 R-DS-14 R-DS-15 R-DS-07")
EXT("M.03.01", req="R-MK-20")
EXT("M.03.03", req="R-EN-03 R-VA-03")
EXT("M.04.01", req="R-HR-08 R-HR-09 R-HR-11")
EXT("M.04.05", req="R-VA-08 R-VA-09")
EXT("M.05.01", req="R-RR-07 R-RR-08 R-RR-09")
EXT("M.05.03", req="R-CS-03 R-CS-04 R-CS-06 R-CS-07 R-CS-08 R-CS-09 R-CS-10")
EXT("M.06.04", req="R-RG-09")
EXT("M.06.06", req="R-EN-08")
EXT("M.06.07", req="R-HY-06")
EXT("M.02.04", req="R-FD-02")

L("F.13.09", "Ball movement (passes per chance, reversals, side changes)", "How much the ball moves before the shot: passes, ball reversals (ball crosses x = 0 from one wing to the other) and side changes per chance.",
  req="R-ST-24 R-ST-25", t="passes.pass_id chances.chance_id", s="P",
  gap=G("ST", "Should", "Per chance, store passes before the shot, ball reversals (ball x changes sign with |x| >= 3.0 m on both sides within one chance) and the time from first frontcourt catch to shot, for half-court offence as well as press break.",
        "Counts recompute from passes and ball_states; reversal count agrees with labels on >= 90% of 200 chances (proposal).", "New columns chances.n_passes, chances.n_reversals, chances.frontcourt_to_shot_s.", prio=2))
L("L.02.07", "Broadcast replays as secondary evidence", "Replays show events (fouls, out of bounds, blocks) the live camera missed; kept out of tracking but usable as labelled evidence.",
  req="R-VI-04", t="events.from_replay_frame frames.replay_segment_id", s="P",
  gap=G("VI", "Should", "Replay segments are linked to the live event they replay (time offset, event_id) so a reviewer or a labeller can use them as evidence; no event, position or count is ever created from a replay frame.",
        ">= 90% of replay segments linked to an event on 3 games (proposal); 0 events with from_replay_frame = true counted in any statistic.", "New columns frames.replay_of_event_id, frames.replay_offset_s.", prio=3))
