from core import D, L, G, X

# ======================================================================== B
D("B", "Court, equipment and venue", "The physical game: court geometry and markings, basket and ball, clocks and displays, uniforms, cameras and the arena.")

D("B.01", "Court geometry and markings", "Dimensions and markings of Rule 1 and the project's metric frame (config/court_ncaa_men.yaml, src/msu_alpha/geometry.py).")
L("B.01.01", "Court dimensions (28.65 m x 15.24 m)", "Sidelines 94 ft, end lines 50 ft, inside edges.", r="1-2", req="R-CG-01", t="config/court_ncaa_men.yaml", s="C")
L("B.01.02", "Boundary lines and the out-of-bounds plane", "Boundary lines (5.08 cm wide) are out of bounds; their width decides close out-of-bounds calls.",
  r="1-3, 4-6", req="R-CG-01 R-BL-07", t="config/court_ncaa_men.yaml", s="P",
  gap=G("CG", "Shall", "Court config holds every line width and mark of Rule 1 with its citation: boundary lines 0.0508 m, centre circle radius 1.83 m, lane space marks and neutral zones, coaching box, backboard face 1.22 m from the end line, backboard 1.83 m x 1.07 m, ring inner diameter 0.4572 m, 28-ft throw-in marks (8.53 m), designated-spot width 0.91 m.",
        "Each constant present with a rule citation and `verified: true`; geometry unit tests reproduce each mark within 0.01 m.",
        "Add keys to config/court_ncaa_men.yaml (line_width_m, centre_circle_radius_m, lane_space_marks_m, backboard_face_from_end_line_m, backboard_width_m, backboard_height_m, ring_inner_diameter_m, throw_in_mark_from_end_line_m, coaching_box_m).", prio=1))
L("B.01.03", "Centre circle", "1.83 m radius circle for jump balls; non-jumpers stay outside.", r="1-4, 6-2", req="R-DT-15", t="jump_balls.circle_formation", s="P",
  gap=X("(see B.01.02 proposal)", note="Covered by the court-constants proposal under B.01.02."))
L("B.01.04", "Division line and half-court distance", "Division line 12.73 m from the rim centre; frontcourt and backcourt.", r="1-5", req="R-CG-01", t="config/court_ncaa_men.yaml player_positions.court_half", s="C")
L("B.01.05", "Free-throw lane, line and lane spaces", "Lane 3.66 m wide; FT line 4.19 m from rim centre; lane-space marks for FT positions.",
  r="1-6, 8-4", req="R-CG-01 R-DT-13", t="config/court_ncaa_men.yaml free_throws.lane_occupant_ids", s="P",
  note="Lane width and FT line in config; lane-space marks missing (see B.01.02).", gap=X("(see B.01.02 proposal)"))
L("B.01.06", "Three-point line (6.75 m, 6.60 m corners)", "Arc and straight corner sections.", r="1-7", req="R-CG-01 R-IV-12", t="config/court_ncaa_men.yaml", s="C")
L("B.01.07", "Restricted-area arc (1.22 m)", "Arc for the secondary-defender charge rule.", r="1-8, 4-31", req="R-CG-01", t="config/court_ncaa_men.yaml", s="C")
L("B.01.08", "Coaching box", "Area where the head coach may stand.", r="1-9", req="", t="", s="M",
  gap=G("CC", "Should", "Measure head-coach position relative to the coaching box when visible (inside, outside, distance in m) as part of sideline behaviour.",
        "Box geometry in config; position flag agrees with labels on >= 80% of 100 visible clips (proposal).",
        "bench_events: new columns x_m, y_m, in_coaching_box; config key coaching_box_m.", prio=3))
L("B.01.09", "28-ft throw-in marks and designated spots", "Sideline marks 8.53 m from the end line; end-line spots 0.91 m outside the lane.",
  r="7-3.2.b (2025-26), 7-6.8", req="R-DT-19 R-SR-08", t="restarts.throw_in_spot", s="P", note="Live doc says 'Add to config'; not in config yet.", gap=X("(see B.01.02 proposal)"))
L("B.01.10", "Backboard and basket geometry", "Backboard face 1.22 m inside the end line, 1.83 x 1.07 m; ring 3.05 m high, 0.4572 m inner diameter, centre 1.60 m from the end line.",
  r="1-10, 1-13, 1-14, 1-15", req="R-CG-01 R-CG-11 R-MB-01", t="config/court_ncaa_men.yaml", s="P", note="Rim height and centre in config; backboard and ring diameter missing.", gap=X("(see B.01.02 proposal)"))
L("B.01.11", "Coordinate frame and mirroring", "Origin under the attacked rim, x along the baseline, theta from the right baseline, other half mirrored.", req="R-CG-02 R-CG-08", t="player_positions.x_m player_positions.theta_deg", s="C")
L("B.01.12", "Named spots and landmarks", "Corner, wing, slot, top, elbow, block, nail, dunker spot, restricted area, paint.", req="R-CG-05 R-MD-10", t="player_positions.spot player_positions.landmark", v="config/vocabulary_map.yaml", s="C")
L("B.01.13", "Undefined spots (short corner, one pass away)", "Terms still 'to be defined from film'.", req="R-MD-10", t="config/vocabulary_map.yaml", s="P",
  gap=G("MD", "Shall", "Short corner, one pass away, help side, two-side, tag and the remaining coaching terms get measured definitions in the vocabulary map (short corner provisional r 4.0-5.5 m, theta <= 15 degrees), before P3.",
        "Every term used in a template or taxonomy resolves to an entry with numbers in m and degrees; 0 entries still say 'to be defined'.",
        "config/vocabulary_map.yaml: add the definitions; geometry.spot() returns short_corner.", prio=2))
L("B.01.14", "Sectors, rings, rays and grid", "15-degree sectors, 0.5 m rings, named rays, 0.25 m grid.", req="R-CG-05", t="player_positions.sector_15deg player_positions.ring_0p5m", s="C")
L("B.01.15", "Post zones (low, high) and cut-off checks", "Post-zone boundaries checked against film.", req="R-CG-05 R-CG-09", t="player_positions.post_zone", s="C")
L("B.01.16", "Court constants verification status", "config/court_ncaa_men.yaml says verified: false.", req="R-CG-01", t="config/court_ncaa_men.yaml", s="P",
  gap=X("(Aldemir sign-off)", note="Live doc says every constant matches the 2026-27 book; the file still needs `verified: true` and rule citations (R-CG-01 fails today)."))

D("B.02", "Equipment and displays", "Ball, scoreboard, shot clocks, possession indicator, benches and table, uniforms and apparel (Rule 1-16 to 1-26).")
L("B.02.01", "Ball specification", "Size, weight and colour; 0.24 m diameter used for the size check.", r="1-16", req="R-BL-01", t="ball_states.size_check_pass config/court_ncaa_men.yaml", s="C")
L("B.02.02", "Game ball model per game", "Ball manufacturer/model in use (affects bounce and shooting feel).", r="1-16", req="", t="", s="M",
  gap=G("FD", "Should", "Game registry records the game-ball manufacturer and model where public.", "Field filled or 'not public' for 100% of games.", "New column games.ball_model.", prio=3))
L("B.02.03", "Scoreboard and game-clock display", "Arena scoreboard; tenths under one minute.", r="1-18", req="R-SY-01 R-SR-01", t="scoreboard_ocr.display scoreboard_ocr.game_clock_raw", s="C")
L("B.02.04", "Shot-clock displays", "Shot-clock units over each basket; optional tenths under 5 s.", r="1-19", req="R-SY-01 R-IV-07", t="scoreboard_ocr.shot_clock_raw scoreboard_ocr.display", s="C")
L("B.02.05", "Possession indicator", "Alternating-possession arrow display.", r="1-20", req="R-SY-01 R-MD-12", t="scoreboard_ocr.arrow_raw", s="C")
L("B.02.06", "Red light / LED and horn", "End-of-period signal used for buzzer beaters.", r="1-18, 5-7", req="R-MB-06", t="made_basket_events.release_vs_horn audio_seconds.buzzer_present", s="C")
L("B.02.07", "Team benches and scorers' table side", "Which side each bench and the table are on; needed for the second-half arrow and bench filtering.",
  r="1-21, 6-3", req="", t="", s="M",
  gap=G("FD", "Shall", "Game registry stores each team's bench side and the scorers' table side relative to the main camera (near or far sideline, left or right end).",
        "Filled for 100% of processed games before tracking; bench-side detections agree with it on >= 99% of frames.",
        "New columns games.home_bench_end, games.table_sideline (near/far), venues.table_sideline_default.", prio=2))
L("B.02.08", "Uniform colours and numbers", "Jersey colours, number legibility, font.", r="1-22", req="R-CX-07 R-FD-03 R-DT-18", t="games.home_jersey_colour games.away_jersey_colour jersey_history.jersey_number", s="C")
L("B.02.09", "Supplemental apparel, headbands, sleeves", "Sleeves, tights, headbands (up to 4 in from 2025-26).", r="1-23, 1-24", req="R-ID-12", t="appearance_cards.sleeves appearance_cards.headband", s="C")
L("B.02.10", "Player equipment (goggles, masks, braces)", "Protective equipment visible on video.", r="1-26", req="R-ID-12", t="appearance_cards.tape", s="P",
  gap=G("ID", "Should", "Appearance card records protective equipment (face mask, goggles, knee brace, ankle brace) as re-identification cues; no health inference is drawn from it.",
        "Field present on every card; used only as an ID tie-breaker (ablation per R-ID-13).", "New column appearance_cards.protective_equipment.", prio=3))
L("B.02.11", "Court logos and floor graphics", "Logos (two 10 ft x 10 ft boxes; end-line advertising from 2026-27).", r="1-17.6 (2026-27)", req="R-CG-10", t="venues.floor_template_id", s="C")
L("B.02.12", "Rim type and stiffness", "Rim make and stiffness by arena (context list mentions 'rim type').", r="1-15", req="", t="", s="M",
  gap=G("CX", "Should", "Arena registry stores the rim type where known, for shooting-by-arena tests.", "Field filled or 'unknown' for every venue.", "New column venues.rim_type.", prio=3))

D("B.03", "Cameras and broadcast geometry", "Main camera and other camera positions as seen on broadcast.")
L("B.03.01", "Main-camera side and height per arena", "Camera registry per arena.", req="R-VI-13 R-FD-11", t="venues.main_camera_side venues.main_camera_height_m venues.zoom_range_seen", s="C")
L("B.03.02", "Camera pan, tilt, zoom and focal length", "Per frame.", req="R-DT-09", t="frames.camera_pan_deg frames.camera_tilt_deg frames.focal_px", s="C")
L("B.03.03", "Homography and lens distortion", "Camera-to-court mapping per main-camera frame.", req="R-CG-03 R-VA-02", t="frames.homography frames.distortion_k frames.mapping_conf", s="C")
L("B.03.04", "Other fixed camera positions", "Baseline, under-basket, reverse angle, rail, robotic, skycam positions.", req="R-SR-10", t="state_frame.reverse_angle", s="P",
  gap=G("VI", "Should", "Camera registry lists each arena's secondary camera positions (reverse angle, baseline, under-basket, high end-zone, rail, skycam) with approximate court position in m, so non-main frames can be mapped later.",
        "Registry row per camera seen; positions within 2 m of a hand estimate (proposal).", "New table `arena_cameras` (venue_id, camera_kind, x_m, y_m, z_m, seen_first_game).", prio=3))
L("B.03.05", "Floor template and glare zones", "Per-arena floor template.", req="R-CG-10", t="venues.floor_template_id", s="C")

D("B.04", "Arena and venue context", "Venue identity, size, environment and layout.")
L("B.04.01", "Venue identity, coordinates, elevation, time zone", "", req="R-FD-11 R-CX-16", t="venues.lat_deg venues.lon_deg venues.elevation_m venues.tz", s="C")
L("B.04.02", "Capacity and attendance", "", req="R-CX-04", t="venues.capacity games.attendance", s="C")
L("B.04.03", "Floor colour, backdrop behind each basket, lighting", "", req="R-CX-12", t="venues.floor_colour venues.backdrop_behind_baskets venues.lighting_level", s="C")
L("B.04.04", "Student-section location", "Which basket end has the student section (free throws by end).", req="", t="", s="M",
  gap=G("CX", "Should", "Arena registry stores the student-section end(s) and the opposing-fan section, per game when it changes.",
        "Filled for every venue processed; used by end-of-floor shooting tests (C48).", "New column venues.student_section_end (+ games override).", prio=3))
L("B.04.05", "Court placement (dome midfield / corner, standard arena)", "Tournament dome courts change the shooting background.", req="", t="", s="M",
  gap=G("CX", "Should", "Venue rows state whether the court is in a standard arena, a dome at midfield or a dome in a corner, and the seat distance behind each basket (m).",
        "Field filled for every NCAA-tournament venue; distance within 5 m of published plans.", "New columns venues.court_placement (enum), venues.backdrop_distance_m.", prio=3))
L("B.04.06", "Neutral site", "", req="R-MD-14 R-CX-04 R-CX-14", t="games.neutral_site team_game_context.proximity_home_flag", s="C")
L("B.04.07", "Arena music and noise rules", "Music allowed during dead balls (2025-26).", r="10-2.8.a (2025-26)", req="R-AU-04", t="audio_seconds.music_flag", s="C")

# ======================================================================== C
D("C", "Participants", "Everyone on or around the floor: players, coaches and bench, officials, table crew, crowd and arena staff.")

D("C.01", "Players", "Identity, body, origin, skills and status of each player (player card, rosters).")
L("C.01.01", "Player identity and IDs", "ESPN, CBBD, NCAA IDs, names as broadcast says them.", req="R-PC-01 R-DS-05", t="players.player_id players.broadcast_name id_crosswalk.source_key", s="C")
L("C.01.02", "Roster per season", "", req="R-FD-03", t="rosters.player_id rosters.season", s="C")
L("C.01.03", "Jersey number history", "", req="R-FD-03 R-ID-04", t="jersey_history.jersey_number jersey_history.valid_from", s="C")
L("C.01.04", "Listed position and played position", "", req="R-PC-01", t="rosters.listed_position player_card.listed_vs_played_position", s="C")
L("C.01.05", "Body (height, weight, wingspan, reach, hands)", "Listed vs measured with source.", req="R-PC-04 R-FD-04 R-DQ-09", t="rosters.listed_height_cm player_card.wingspan_cm player_card.standing_reach_cm", s="C")
L("C.01.06", "Age, class, eligibility", "", req="R-PC-01", t="players.birth_date player_game_context.age_at_tip_years rosters.class_year", s="C")
L("C.01.07", "Origin (hometown, schools, AAU)", "", req="R-PC-02 R-PC-03", t="player_card.hometown_lat player_card.aau_program player_game_context.dist_hometown_to_venue_km", s="C")
L("C.01.08", "Laterality (shooting, dribble, finishing hand, drive side)", "", req="R-PC-11", t="players.shooting_hand player_card.dominant_dribble_hand player_card.finishing_hand_left_share", s="C")
L("C.01.09", "Athletic profile from tracking", "Top speed, acceleration, lateral slide, change of direction, jump height.", req="R-PC-05", t="player_card.trk_top_speed_ms_max player_card.trk_lateral_slide_ms player_card.trk_cod_time_s", s="C")
L("C.01.10", "Combine and athletic test results", "Standing/max vertical, lane agility, shuttle, sprint (where published).", req="R-FD-04 R-PC-04", t="player_card.max_vertical_cm player_card.lane_agility_s", s="C")
L("C.01.11", "Recruiting and rankings", "", req="R-PC-13 R-FD-12", t="player_card.recruit_rank_nat_247c ratings_snapshots.rank", s="C")
L("C.01.12", "Transfer history", "", req="R-FD-12 R-PC-02", t="rosters.transfer_origin_team_id player_card.transfer_events", s="C")
L("C.01.13", "International and pro background", "", req="R-PC-16", t="player_card.fiba_youth_events player_card.pro_leagues", s="C")
L("C.01.14", "NIL valuation (public estimates)", "On the player card template; no requirement names it.", req="", t="player_card.nil_valuation_usd", s="P",
  gap=G("PC", "Should", "NIL valuations, if kept, are public estimates only, tagged with source, date and kind (estimate vs reported), never used as a model input until a hypothesis registers them.",
        "Every NIL value carries source, date and kind; 0 model feature registries list NIL without a registered hypothesis.", "None (columns exist on the card); add a CX-01 registry entry `exploratory`.", prio=3))
L("C.01.15", "Role and usage cluster", "", req="R-PC-10", t="player_card.role_cluster_own player_card.usage_pct", s="C")
L("C.01.16", "Development and career minutes", "", req="R-PC-12", t="player_card.career_d1_minutes profile_snapshots.metric_code", s="C")
L("C.01.17", "Captain", "Designated captain(s).", r="3-3", req="", t="player_card.captain_flag", s="P",
  gap=G("PC", "Should", "Captain designation stored per player-season with source.", "Filled or 'unknown' for every rostered player.", "None (player_card.captain_flag exists); add to R-PC-01 identity block.", prio=3))
L("C.01.18", "Availability and public injury status", "", req="R-FD-05 R-CX-08 R-RG-06", t="availability.status availability.reason_public", s="C")
L("C.01.19", "Excluded attributes (race, faces, private health)", "", req="R-PC-15 R-ID-10", t="", s="C")
L("C.01.20", "Per-game appearance", "Shoes, sleeves, headband, tape.", req="R-ID-12", t="appearance_cards.shoes", s="C")

D("C.02", "Coaches and bench personnel", "Head coaches, assistants, bench players, trainers and staff.")
L("C.02.01", "Head coach card", "Tenure, record, system tags.", req="R-CC-01", t="coaches.coach_id coaches.career_wins_asof coaches.system_offense_codes", s="C")
L("C.02.02", "Assistant coaches and staff roles", "", req="R-CC-01", t="coaches.role", s="C")
L("C.02.03", "Bench personnel list per game", "Team members, managers, trainers, ops staff on the bench (bench-personnel rule).", r="4-3, 4-4", req="R-DT-02", t="bench_events.actor_type", s="P",
  gap=G("CC", "Should", "Per game, store the bench personnel roles present (head coach, assistants, trainers, managers) as counts, for technical attribution and bench filtering; no names beyond public staff lists.",
        "Count per role per game filled from the box score or broadcast where available; 'unknown' otherwise.", "New table `bench_personnel` (game_id, team_id, role, count, source).", prio=3))
L("C.02.04", "Athletic trainers and medical staff on the floor", "Entry of trainers signals injury stoppages.", req="R-DT-17 R-EV-11", t="detections.person_class", s="C")
L("C.02.05", "Sideline behaviour", "Standing, gesturing, talking to officials.", req="R-CC-04 R-CC-03", t="bench_events.event_type", s="C")

D("C.03", "Officials", "The game's referees.")
L("C.03.01", "Official identity and crew per game", "", req="R-FD-08 R-DQ-01", t="officials.official_id game_officials.official_id", s="C")
L("C.03.02", "Official tendencies as of date", "Fouls per 40, home-away split, call mix.", req="R-RF-06 R-CX-06", t="profile_snapshots.metric_code", s="C")
L("C.03.03", "Official experience and assignment level", "Seasons, games worked, conferences, postseason assignments.", req="R-RF-06", t="officials.first_season_seen", s="P",
  gap=G("RF", "Should", "Official cards hold games worked per season, conferences worked and postseason assignments as of each game date, from PBP across D-I.",
        "Recomputes from PBP officials lists; no data after the game date used.", "profile_snapshots metric codes `ref_games_season`, `ref_conferences`, `ref_postseason`.", prio=3))

D("C.04", "Table officials", "Scorer, timer, shot-clock operator (Rule 2-9 to 2-11).")
L("C.04.01", "Official scorer and the scorebook authority", "Scorebook wins unresolved discrepancies.", r="2-9, 2-9.13", req="R-DQ-09", t="scoreboard_flags.review_answer", s="P", gap=X("new-IV-33"))
L("C.04.02", "Timer and game-clock operation errors", "Late starts and stops.", r="2-10, 5-12", req="R-SB-01", t="scoreboard_flags.flag_type", s="C")
L("C.04.03", "Shot-clock operator errors", "Wrong or missing resets.", r="2-11", req="R-SB-01 R-SY-09", t="scoreboard_flags.flag_type shot_clock_resets.rule_match", s="C")
L("C.04.04", "Home stat crew bias", "Home scorekeepers credit more assists, blocks and steals.", req="R-DQ-09", t="", s="P",
  gap=G("DQ", "Shall", "The known-bias register is a table with one row per bias (description, affected field, direction, correction or flag, evidence source), and every affected field carries the flag.",
        "Register has >= 4 rows (listed heights, home assists/blocks/steals, shot-location entry, substitution timing); 100% of affected columns reference a register row.",
        "New table `bias_register` (bias_id, field, direction, correction, evidence); dq_reports.check values reference it.", prio=2))

D("C.05", "Crowd and arena personnel", "Spectators, bands, cheer, mascots and game staff.")
L("C.05.01", "Crowd size and share of capacity", "", req="R-CX-04", t="games.attendance", s="C")
L("C.05.02", "Crowd loudness", "", req="R-AU-03", t="audio_seconds.loudness_rel_db", s="C")
L("C.05.03", "Crowd allegiance share (neutral sites)", "Share of fans supporting each team.", req="R-CX-17 R-CX-14", t="team_game_context.proximity_home_flag", s="P",
  gap=G("CX", "Should", "Estimate each team's crowd share at neutral sites from distance, enrollment and travelling-support history, with an interval.",
        "Estimate with 80% interval for every neutral-site game; validated against audio asymmetry where audio exists (C69).", "New column team_game_context.crowd_share_est (0-1).", prio=3))
L("C.05.04", "Band, cheer, mascots and staff on the floor", "Excluded from player counts.", req="R-DT-17 R-DT-02", t="detections.person_class", s="C")
