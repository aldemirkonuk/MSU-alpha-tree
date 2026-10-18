"""Generate schema/tables/<table>.yaml and the table sections of docs/data/dictionary_state.md
for the state-record tables (prompt 003, W2 item 5). One spec, two outputs, so they never drift.
Run: python3 -I gen_state.py <repo_root> <md_fragment_out>
"""
import sys, pathlib, yaml

REPO = pathlib.Path(sys.argv[1])
FRAG = pathlib.Path(sys.argv[2])
DATE = "2026-10-18"

# ---------------------------------------------------------------- vocabularies
SRC_ENUM = ["OCR", "PBP", "CV", "manual", "derived"]
DQ_ENUM = ["observed", "inferred", "carried", "imputed", "quarantined"]
PASS_ENUM = ["blind", "anchored"]
PASS3_ENUM = ["blind", "anchored", "pbp_only"]
TEAM_ENUM = ["msu", "opponent"]
TEAM3_ENUM = ["msu", "opponent", "none"]
BONUS_ENUM = ["none", "bonus", "double_bonus"]
PBP_PROVIDER = ["cbbd", "espn_pulled", "hoopr_espn", "hoopr_ncaa", "none"]
LIC_ENUM = ["computed_by_us", "model_input_allowed", "reference_only"]

L_US = "computed_by_us"
L_ROW = "ROW"
L_REG = "REG"

A_FRAME = "at_frame"
A_PASS = "by_pass"
A_POST = "post_game"
A_REVIEW = "post_review"
A_REG = "pre_game"

S_OCR = "OCR"
S_PBP = "PBP"
S_CV = "CV"
S_DER = "derived"
S_FUSE = "fused"

LEGEND = {
    "licence": {
        "computed_by_us": "Computed by this project from privately held broadcast video (OCR, CV), audio, manual labels or our own pipeline. Private research use; model input allowed internally; never published raw (video is private research use only).",
        "model_input_allowed": "Value taken from CollegeBasketballData (CBBD): research and commercial use allowed per docs/research/data_sources_catalog.md row 8.",
        "reference_only": "Value taken from ESPN data already pulled, hoopR ESPN prebuilt files, or hoopR NCAA-engine files: ESPN terms bar automated collection and data-set compilation; NCAA terms unverified. Reference and cross-check only until Aldemir decides otherwise.",
        "ROW": "Licence depends on the row's pbp_provider and is stored in the row's licence_class column (cbbd -> model_input_allowed; espn_pulled, hoopr_espn, hoopr_ncaa -> reference_only).",
        "REG": "Inherits the games registry entry (dictionary_games.md).",
    },
    "as_of": {
        "at_frame": "Known at the video instant the row describes; usable as an in-game feature at that instant.",
        "by_pass": "Blind pass: at_frame. Anchored pass: post_game (it uses PBP, which is only complete after the game). Anchored values are for training and for describing past games, never in-game features (Principle 6).",
        "post_game": "Known only after the game (PBP published, full video processed).",
        "post_review": "Known at reviewed_utc of the review that set it.",
        "pre_game": "Known before tip (registry).",
        "n/a": "Key or processing metadata.",
    },
    "source": {
        "OCR": "Parsed scoreboard readings (scoreboard_ocr).",
        "CV": "Our detection, tracking, ball, rim and lane models (dictionary_games.md frames, tracks).",
        "PBP": "Anchored pass only: CBBD plays, or ESPN play-by-play already pulled / hoopR load_mbb_pbp; exact provider field names in docs/data/source_field_map.md.",
        "fused": "Fusion of OCR, CV and, in the anchored pass, PBP; authority order official scorebook (PBP, box score) > arena scoreboard > broadcast scorebug (Rule 2-9.13).",
        "derived": "Computed from other columns of the same table by the rule in the definition.",
        "pipeline": "Written by the processing pipeline (keys, versions, lineage).",
        "manual review": "Human reviewer through the review queue (R-HR-02, R-HR-05).",
    },
}

def C(name, typ, definition, unit=None, rng=None, src=None, lic=None, asof=None, req=None,
      gm=False, null=False, values=None, proposed=False):
    return dict(name=name, type=typ, unit=unit, range=rng, values=values, definition=definition,
                source=src, licence=lic, as_of=asof, requirements=req or [], global_metadata=gm,
                nullable=null, proposed_global_addition=proposed)


def prov(prefix, req, what, asof=A_PASS):
    """Provenance companions for a state field group (R-SR-15, R-MD-09, R-MD-19)."""
    return [
        C(f"{prefix}_src", "enum", f"Source of the {what} value(s) in this row.", values=SRC_ENUM,
          src="pipeline", lic=L_US, asof=asof, req=["R-SR-15", "R-MD-09"] + req),
        C(f"{prefix}_conf", "float", f"Confidence of the {what} value(s); PBP-sourced values carry 1.0 (R-MD-09).",
          unit="0-1", rng=[0, 1], src="pipeline", lic=L_US, asof=asof, req=["R-SR-15", "R-MD-09"] + req),
        C(f"{prefix}_dq", "enum", f"Data-quality flag of the {what} value(s).", values=DQ_ENUM,
          src="pipeline", lic=L_US, asof=asof, req=["R-SR-15", "R-MD-19"] + req),
    ]


def lineage(asof=A_PASS):
    return [
        C("model_version", "string", "Pipeline and model versions that produced the row (semver string per stage, joined).",
          src="pipeline", lic=L_US, asof=asof, req=["R-MD-09", "R-EN-04", "R-DQ-04"], gm=True),
        C("source", "string", "Row-level source summary, e.g. 'fused:OCR+CV' or 'PBP:cbbd'. Field-level sources are in the *_src columns.",
          src="pipeline", lic=L_US, asof=asof, req=["R-MD-09", "R-SR-15"], gm=True),
        C("confidence", "float", "Row-level confidence: minimum of the field confidences used in the row.", unit="0-1", rng=[0, 1],
          src="pipeline", lic=L_US, asof=asof, req=["R-MD-09", "R-SR-15"], gm=True),
        C("created_utc", "timestamp", "UTC time the row was written. Rows are never updated in place; a new version is a new pipeline version (R-EN-07).",
          unit="UTC", src="pipeline", lic=L_US, asof="n/a (processing metadata)", req=["R-DQ-04", "R-EN-07"]),
    ]


def pbp_lineage():
    return [
        C("pbp_provider", "enum", "Provider of the PBP row this record was matched to or built from; 'none' in the blind pass.",
          values=PBP_PROVIDER, src="pipeline", lic=L_US, asof=A_POST, req=["R-DQ-01", "R-DQ-04", "R-SR-15"]),
        C("pbp_event_id", "string", "Key of the matched row in the events table (dictionary_games.md), which keeps the provider's own play ID.",
          src=S_PBP, lic=L_ROW, asof=A_POST, req=["R-SY-02", "R-SY-10"], null=True),
        C("licence_class", "enum", "Licence class of the PBP-derived values in this row (computed_by_us when no PBP value is used).",
          values=LIC_ENUM, src="pipeline from pbp_provider", lic=L_US, asof="n/a", req=["R-DQ-04"]),
    ]


GAME = C("game_id", "string", "ESPN game ID; the one join key across sources (FK games.game_id).",
         src="registry/games.csv", lic=L_REG, asof=A_REG, req=["R-MD-01"], gm=True)
PASS = C("pass", "enum", "Processing pass: blind uses no PBP; anchored uses PBP. The per-game diff of the two is the CV error estimate (R-SR-13).",
         values=PASS_ENUM, src="pipeline", lic=L_US, asof="n/a", req=["R-SR-13", "R-SR-15"], proposed=True)
PASS3 = C("pass", "enum", "blind, anchored, or pbp_only (games or stretches with no video, built from PBP alone for the possession engine, R-SY-06, R-PE-08).",
          values=PASS3_ENUM, src="pipeline", lic=L_US, asof="n/a", req=["R-SR-13", "R-SR-15", "R-SY-06", "R-PE-08"], proposed=True)
PERIOD = C("period", "int", "1 = first half, 2 = second half, 3+ = extra periods (each an extension of the second half, Rule 5-9.4).",
           rng=[1, 12], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-01", "R-IV-16"], gm=True)
CLOCK = C("game_clock_s", "float", "Game clock remaining in the period. 0.1 s resolution (board shows tenths under 60 s, Rule 1-18.2; whole seconds above).",
          unit="s", rng=[0, 1200], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-01", "R-IV-05"], gm=True)
VTS = C("video_ts_ms", "int", "Presentation time of the frame from the start of the video file.", unit="ms", rng=[0, None],
        src="video decode (frames table)", lic=L_US, asof=A_FRAME, req=["R-MD-01", "R-MD-08"], gm=True)

TABLES = []


def T(**kw):
    TABLES.append(kw)


# ================================================================ state_frame
T(table="state_frame",
  grain="one row per decoded video frame per pass (blind, anchored) of a game video",
  primary_key=["game_id", "video_id", "frame_index", "pass"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["video_id", "frame_index"], "references": "frames.(video_id, frame_index)"},
                {"columns": ["possession_id"], "references": "possessions.possession_id"},
                {"columns": ["chance_id"], "references": "chances.chance_id"},
                {"columns": ["last_score_event_id"], "references": "score_events.score_event_id"}],
  requirements=["R-SR-01", "R-SR-02", "R-SR-03", "R-SR-04", "R-SR-05", "R-SR-06", "R-SR-10", "R-SR-13", "R-SR-15",
                "R-MD-01", "R-MD-02", "R-MD-04", "R-MD-07", "R-MD-08", "R-MD-12", "R-MD-19", "R-IV-01..16"],
  notes=["Carries every field of schema/global_metadata.yaml under its exact name (R-MD-01); fields that cannot exist hold an explicit status (shot_clock_status = off), never a silent null.",
         "Field-level provenance: each state group has <group>_src, <group>_conf, <group>_dq companions. When one field of a group has a different source (e.g. game clock interpolated while score is read), the group companions describe the weakest field and the field-specific flag (clock_inferred, ball_inferred) says which.",
         "Replay frames (replay_flag = true) keep the last live state, dq = carried; no state change is ever taken from a replay frame (Principle 7, R-VI-04).",
         "Storage: Parquet under processed/<game_id>/<version>/ (R-EN-07), outside the repo; ~430k frames per pass for a 2-hour 60 fps video."],
  columns=[
      GAME,
      C("season", "string", "Season label as in the registry (e.g. '2026-27').", src="registry/games.csv", lic=L_REG, asof=A_REG, req=["R-MD-01"], gm=True),
      C("game_type", "enum", "As in global metadata.", values=["exhibition", "non_conference", "big_ten", "big_ten_tournament", "ncaa_tournament"],
        src="registry/games.csv", lic=L_REG, asof=A_REG, req=["R-MD-01", "R-MD-14"], gm=True),
      C("video_id", "string", "ID of the video file (one game can have several files); FK to the video files / frames tables in dictionary_games.md.",
        src="video registry", lic=L_US, asof=A_FRAME, req=["R-VI-01", "R-MD-01"], proposed=True),
      C("frame_index", "int", "0-based decoded frame number within video_id.", rng=[0, None], src="video decode", lic=L_US, asof=A_FRAME, req=["R-MD-01"], gm=True),
      VTS, PASS,
      # clock
      PERIOD,
      CLOCK,
      C("clock_running", "bool", "Game clock is running in this frame (from successive readings; Rule 5-10 start and 5-11 stop events).",
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-01", "R-IV-05", "R-IV-06"]),
      C("clock_inferred", "bool", "Game clock not read in this frame (scorebug hidden, replay, ad break); value interpolated from the last reading.",
        src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-01"]),
      C("shot_clock_status", "enum", "on = shot clock running or stopped with a value; off = turned off because the game clock shows less than a shot-clock period (Rule 2-11.2) or between periods; unknown = not readable and not inferable.",
        values=["on", "off", "unknown"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-01", "R-MD-01", "R-IV-07"], proposed=True),
      C("shot_clock_s", "float", "Shot clock value. Null only when shot_clock_status is off or unknown (status carries the explicit value, R-MD-01). Tenths optional under 5 s (Rule 1-19.2).",
        unit="s", rng=[0, 30], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-01", "R-IV-07", "R-MD-06"], gm=True, null=True),
      C("live_ball", "bool", "Ball is live (Rule 6-1) vs dead (Rule 6-5). Live from the toss leaving the official's hand / disposal of the thrower-in or free-thrower.",
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-01", "R-MD-05"]),
      *prov("period", ["R-SR-01"], "period"),
      *prov("game_clock", ["R-SR-01"], "game clock"),
      *prov("shot_clock", ["R-SR-01"], "shot clock"),
      *prov("live_ball", ["R-SR-01"], "live/dead"),
      # score
      C("score_msu", "int", "MSU points.", unit="points", rng=[0, 250], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-02", "R-IV-04"], gm=True),
      C("score_opp", "int", "Opponent points.", unit="points", rng=[0, 250], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-02", "R-IV-04"], gm=True),
      C("margin", "int", "score_msu - score_opp.", unit="points", rng=[-250, 250], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-02", "R-MD-17"], gm=True),
      C("last_score_event_id", "string", "Most recent score_events row at or before this frame.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-02"], null=True),
      *prov("score", ["R-SR-02"], "score"),
      # fouls
      C("team_fouls_msu", "int", "MSU team fouls in the current half (personal incl. player-control + Class A technicals, Rule 8-2.3). Extra periods continue the second-half count (Rule 5-9.4).",
        unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-MD-07", "R-IV-09"], gm=True),
      C("team_fouls_opp", "int", "Opponent team fouls, same definition.", unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS,
        req=["R-SR-03", "R-MD-07", "R-IV-09"], gm=True),
      C("bonus_state", "enum", "Global field kept as defined. Proposed reading (dated note): the bonus that a common foul by the defending team would award now, i.e. from the side of team_in_possession; none when no team control. Team-specific values are in msu_bonus_state / opp_bonus_state.",
        values=BONUS_ENUM, src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-MD-07"], gm=True),
      C("msu_bonus_state", "enum", "MSU shoots bonus free throws: bonus when team_fouls_opp >= 7, double_bonus when >= 10 (Rule 8-2.1, 8-2.2).",
        values=BONUS_ENUM, src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-SR-11"], proposed=True),
      C("opp_bonus_state", "enum", "Opponent shoots bonus free throws: from team_fouls_msu with the same thresholds.",
        values=BONUS_ENUM, src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-SR-11"], proposed=True),
      *prov("fouls", ["R-SR-03"], "team-foul and bonus"),
      # timeouts & reviews
      C("timeouts_msu", "int", "MSU charged timeouts left, all lengths together (global field).", unit="count", rng=[0, 12],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10", "R-MD-07"], gm=True),
      C("timeouts_opp", "int", "Opponent charged timeouts left, all lengths.", unit="count", rng=[0, 12], src=S_FUSE, lic=L_US, asof=A_PASS,
        req=["R-SR-04", "R-IV-10", "R-MD-07"], gm=True),
      C("to30_left_msu", "int", "MSU 30-second timeouts left (media format: 3 per game, max 2 carried into the second half, +1 per extra period; Rule 5-14.10).",
        unit="count", rng=[0, 12], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"], proposed=True),
      C("to60_left_msu", "int", "MSU 60-second timeouts left (media format: 1 per game; Rule 5-14.10.b).", unit="count", rng=[0, 1],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"], proposed=True),
      C("to75_left_msu", "int", "MSU 75-second timeouts left (non-media formats: 4 per game, +1 per extra period; Rule 5-14.8, 5-14.9).",
        unit="count", rng=[0, 12], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"], proposed=True),
      C("to30_left_opp", "int", "Opponent 30-second timeouts left.", unit="count", rng=[0, 12], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"], proposed=True),
      C("to60_left_opp", "int", "Opponent 60-second timeouts left.", unit="count", rng=[0, 1], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"], proposed=True),
      C("to75_left_opp", "int", "Opponent 75-second timeouts left.", unit="count", rng=[0, 12], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"], proposed=True),
      C("challenge_available_msu", "bool", "MSU head coach may still use a coach's challenge (one per game; a second only after an overturned first; needs a legal timeout; Rule 11-4.1.d-e).",
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"], proposed=True),
      C("challenge_available_opp", "bool", "Same for the opponent.", src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"], proposed=True),
      C("stoppage_kind", "enum", "What the current dead ball is, if any.", values=["none", "team_timeout", "media_timeout", "review", "injury", "intermission", "other_dead"],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-SR-05"]),
      *prov("timeouts", ["R-SR-04"], "timeout, challenge and stoppage"),
      # possession
      C("team_in_possession", "enum", "Team with team control (Rule 4-9.2), or none (jump ball, try in flight, rebound tap, dead ball; Rule 4-9.4).",
        values=TEAM3_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-05", "R-MD-04"], gm=True),
      C("possession_id", "int", "Our possession (ends only when the other team gains control); FK possessions.", rng=[0, None], src=S_FUSE, lic=L_US, asof=A_PASS,
        req=["R-SR-05", "R-MD-04"], gm=True, null=True),
      C("chance_id", "int", "Chance inside the possession (an offensive rebound starts a new chance); FK chances.", rng=[0, None], src=S_FUSE, lic=L_US, asof=A_PASS,
        req=["R-SR-05", "R-MD-04"], gm=True, null=True),
      C("chance_number", "int", "1 for the first chance of a possession, 2 after the first offensive rebound, ...", rng=[1, 20], src=S_FUSE, lic=L_US, asof=A_PASS,
        req=["R-SR-05", "R-SY-05"], gm=True, null=True),
      C("possession_arrow", "enum", "Team the alternating-possession arrow favours; none before the opening tip is controlled (Rule 6-3.4).",
        values=TEAM3_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-05", "R-MD-12"], proposed=True),
      *prov("possession", ["R-SR-05"], "possession, chance and arrow"),
      # ball
      C("ball_control_state", "enum", "Global six-state label.", values=["msu_ball", "opponent_ball", "contested", "in_flight", "inbound_pending", "dead"],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-06", "R-MD-02"], gm=True),
      C("ball_handler_player_id", "string", "Roster ID of the player in control (Rule 4-9.1); null when no player control.", src=S_CV + "; PBP for anchored identity",
        lic=L_US, asof=A_PASS, req=["R-SR-06", "R-BL-02"], null=True),
      C("ball_x_m", "float", "Ball x in the attacked-rim frame (src/msu_alpha/geometry.py: origin on the floor under the centre of the attacked rim; x across the court).",
        unit="m", rng=[-8.62, 8.62], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-06", "R-BL-01"], null=True),
      C("ball_y_m", "float", "Ball y in the attacked-rim frame (toward half court positive).", unit="m", rng=[-2.6, 28.05], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-06", "R-BL-01"], null=True),
      C("ball_z_m", "float", "Ball centre height above the floor.", unit="m", rng=[0, 15], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-06"], null=True),
      C("ball_r_m", "float", "Distance of the ball's floor projection from the attacked rim centre.", unit="m", rng=[0, 30], src=S_DER, lic=L_US, asof=A_FRAME, req=["R-SR-06"], null=True),
      C("ball_theta_deg", "float", "Angle from the right baseline at the rim centre (vocabulary_map.yaml).", unit="degrees", rng=[0, 360], src=S_DER, lic=L_US, asof=A_FRAME, req=["R-SR-06"], null=True),
      C("ball_visible", "bool", "Ball detected in this frame.", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-06"]),
      C("ball_inferred", "bool", "Ball position is last-known or interpolated (not visible).", src="pipeline", lic=L_US, asof=A_FRAME, req=["R-SR-06"]),
      C("try_in_flight", "bool", "A try for goal is in flight (released, not yet ended; Rule 5-1.12).", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-06", "R-IV-07"]),
      C("ring_contact_this_try", "enum", "For the current or just-ended try: did it touch the ring or flange (needed for 20 s reset, Rule 2-11.6.d.1).",
        values=["yes", "no", "unknown", "none"], src=S_CV + "; inferred from shot-clock reset", lic=L_US, asof=A_PASS, req=["R-SR-06", "R-MB-07", "R-IV-07"]),
      C("inbound_side", "enum", "Side of a pending throw-in.", values=["sideline", "baseline", "none"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-MD-03", "R-SR-08"], gm=True),
      C("basket_attacked", "enum", "Basket attacked by team_in_possession in court-fixed terms.", values=["north", "south"], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-MD-01"], gm=True),
      C("players_on_floor", "list[string]", "The 10 roster IDs on court: positions 0-4 MSU, 5-9 opponent, each sorted by roster ID.", src="PBP substitutions + CV identity",
        lic=L_US, asof=A_PASS, req=["R-SR-07", "R-SY-03", "R-IV-01"], gm=True),
      *prov("ball", ["R-SR-06"], "ball state and position", asof=A_FRAME),
      *prov("players", ["R-SR-07"], "players-on-floor"),
      # broadcast
      C("camera_shot_type", "enum", "Global enum. Mapping of R-SR-10 words: tight -> close_up; ad break -> commercial; bench or crowd -> bench / crowd. reverse_angle proposed as an added value (dated note).",
        values=["main_wide", "close_up", "replay", "slow_motion", "crowd", "bench", "studio", "commercial", "graphic"], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-10", "R-VI-03"], gm=True),
      C("reverse_angle", "bool", "Live shot from a non-main camera angle (R-SR-10 'reverse angle').", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-10"], proposed=True),
      C("replay_flag", "bool", "Frame belongs to a broadcast replay or slow-motion segment.", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-10", "R-VI-04"]),
      C("court_visible_frac", "float", "Fraction of the court floor area in view.", unit="0-1", rng=[0, 1], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-10", "R-VI-05"]),
      C("court_mapping_conf", "float", "Confidence of the image-to-court homography.", unit="0-1", rng=[0, 1], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-10"]),
      C("scorebug_visible", "bool", "Broadcast scorebug detected.", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-10", "R-SY-01"]),
      C("coverage_score", "float", "Global coverage score (R-VI-05 formula).", unit="0-1", rng=[0, 1], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-VI-05", "R-MD-11"], gm=True),
      C("defense_scheme_state", "string", "Global field, label from the defense taxonomy; owned by the defense layer, stamped here.", src="DF layer", lic=L_US, asof=A_PASS, req=["R-MD-01"], gm=True, null=True),
      C("defense_scheme_confidence", "float", "Global field.", unit="0-1", rng=[0, 1], src="DF layer", lic=L_US, asof=A_PASS, req=["R-MD-01"], gm=True, null=True),
      *prov("broadcast", ["R-SR-10"], "broadcast-state", asof=A_FRAME),
      # checks
      C("invariant_breaks", "list[string]", "IDs from config/invariants.yaml broken at this frame (empty list when none).", src="invariant checker", lic=L_US, asof=A_PASS, req=["R-IV-01..16", "R-HR-01"]),
      C("flag_ids", "list[string]", "scoreboard_flags rows raised at this frame.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SB-01"]),
      C("correction_ids", "list[string]", "state_corrections rows that change a value of this frame (raw values stay as written).", src="review", lic=L_US, asof=A_REVIEW, req=["R-SR-15"]),
      *lineage(),
  ])

# ================================================================ state_second
T(table="state_second",
  grain="one row per second per pass: per second of video for blind and anchored passes (time_base = video_s); per game-clock second for pbp_only (time_base = game_clock_s)",
  primary_key=["game_id", "pass", "time_base", "t_index"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["possession_id"], "references": "possessions.possession_id"},
                {"columns": ["chance_id"], "references": "chances.chance_id"},
                {"columns": ["ft_sequence_id"], "references": "free_throws.ft_sequence_id"}],
  requirements=["R-SR-05", "R-SR-09", "R-SR-11", "R-SR-12", "R-SR-13", "R-MD-05", "R-MD-13", "R-MD-16", "R-MD-17", "R-PE-01", "R-PE-04", "R-PE-07"],
  notes=["Video-second rows summarise the 60 (or 30) state_frame rows of that second: state at the first frame plus shares over the second.",
         "pbp_only rows let the possession engine (R-PE-01, R-PE-08) use the same state vocabulary for all D-I games without video; dead-ball time is invisible there, so live shares are null.",
         "Window thresholds (two-for-one, foul to extend, last shot, clutch) are proposals stored in config/invariants.yaml constants, never hard-coded (R-EN-06)."],
  columns=[
      GAME, PASS3,
      C("time_base", "enum", "video_s (t_index = whole seconds from video start, per video_id) or game_clock_s (t_index = elapsed game seconds since tip, pbp_only).",
        values=["video_s", "game_clock_s"], src="pipeline", lic=L_US, asof="n/a", req=["R-SR-05"]),
      C("t_index", "int", "Second index in the chosen time base.", unit="s", rng=[0, None], src="pipeline", lic=L_US, asof="n/a", req=["R-SR-05"]),
      C("video_id", "string", "Video file for video_s rows; null for pbp_only.", src="video registry", lic=L_US, asof=A_FRAME, req=["R-MD-01"], null=True),
      C("video_ts_ms_start", "int", "Video time of the first frame of the second; null for pbp_only.", unit="ms", rng=[0, None], src="video decode", lic=L_US, asof=A_FRAME, req=["R-MD-08"], null=True),
      PERIOD, CLOCK,
      C("clock_running_share", "float", "Share of the second with the game clock running.", unit="0-1", rng=[0, 1], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-01", "R-MD-05"], null=True),
      C("shot_clock_status", "enum", "As in state_frame, at the first frame.", values=["on", "off", "unknown"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-01"]),
      C("shot_clock_s", "float", "As in state_frame, at the first frame; null when status off/unknown.", unit="s", rng=[0, 30], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-01", "R-PE-04"], null=True),
      C("score_msu", "int", "MSU points at the start of the second.", unit="points", rng=[0, 250], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-02"]),
      C("score_opp", "int", "Opponent points at the start of the second.", unit="points", rng=[0, 250], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-02"]),
      C("margin", "int", "score_msu - score_opp.", unit="points", rng=[-250, 250], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-11", "R-MD-17"]),
      C("team_in_possession", "enum", "At the start of the second.", values=TEAM3_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-05"]),
      C("possession_id", "int", "FK possessions.", rng=[0, None], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-05", "R-MD-04"], null=True),
      C("chance_id", "int", "FK chances.", rng=[0, None], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-05"], null=True),
      C("chance_number", "int", "Chance number in the possession.", rng=[1, 20], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-05"], null=True),
      C("phase", "enum", "Game phase (R-SR-05): half_court, transition (R-TR-08 definition), throw_in, free_throw, jump_ball, timeout, review, other_dead, intermission.",
        values=["half_court", "transition", "throw_in", "free_throw", "jump_ball", "timeout", "review", "other_dead", "intermission"],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-05", "R-TR-08"]),
      C("secs_since_control_change", "float", "Game-clock seconds since team_in_possession last changed (live time only).", unit="s", rng=[0, 1200],
        src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-05", "R-PE-04"], null=True),
      C("possession_arrow", "enum", "Arrow at the start of the second.", values=TEAM3_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-05", "R-MD-12"]),
      C("share_msu_ball", "float", "Share of the second in state msu_ball (R-MD-05 split; the six shares sum to 1).", unit="0-1", rng=[0, 1], src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-05"], null=True),
      C("share_opponent_ball", "float", "Share in opponent_ball.", unit="0-1", rng=[0, 1], src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-05"], null=True),
      C("share_contested", "float", "Share in contested.", unit="0-1", rng=[0, 1], src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-05"], null=True),
      C("share_in_flight", "float", "Share in in_flight.", unit="0-1", rng=[0, 1], src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-05"], null=True),
      C("share_inbound_pending", "float", "Share in inbound_pending.", unit="0-1", rng=[0, 1], src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-05"], null=True),
      C("share_dead", "float", "Share in dead.", unit="0-1", rng=[0, 1], src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-05"], null=True),
      C("ft_state", "enum", "Free-throw state machine (R-SR-09): none, ft_pending (award known, lane not set), lane_set, attempt (ball at shooter's disposal to release), ft_result (attempt ended, another follows), ft_live_rebound (last attempt missed for a personal foul, ball live).",
        values=["none", "ft_pending", "lane_set", "attempt", "ft_result", "ft_live_rebound"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-09", "R-IV-11"]),
      C("ft_sequence_id", "string", "Current free-throw sequence (FK free_throws.ft_sequence_id).", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-09"], null=True),
      C("ft_attempt_k", "int", "Attempt number within the sequence.", rng=[1, 3], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-09"], null=True),
      C("ft_attempts_n", "int", "Attempts awarded in the sequence (one-and-one counts 2, conditional).", rng=[1, 3], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-09"], null=True),
      C("ft_predicted", "bool", "At the most recent whistle the system predicted 'free throw coming' (from foul type, shooting act and team-foul count).",
        src="state model", lic=L_US, asof=A_FRAME, req=["R-SR-09"], null=True),
      C("ft_pred_prob", "float", "Probability behind ft_predicted.", unit="0-1", rng=[0, 1], src="state model", lic=L_US, asof=A_FRAME, req=["R-SR-09"], null=True),
      C("team_fouls_msu", "int", "MSU team fouls this half (OT continues the second half).", unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-SR-11"]),
      C("team_fouls_opp", "int", "Opponent team fouls this half.", unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-SR-11"]),
      C("msu_bonus_state", "enum", "As in state_frame.", values=BONUS_ENUM, src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-SR-11"]),
      C("opp_bonus_state", "enum", "As in state_frame.", values=BONUS_ENUM, src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-SR-11"]),
      C("fouls_to_give_msu", "int", "Fouls MSU can commit before the opponent is in the bonus: max(0, 6 - team_fouls_msu).", unit="count", rng=[0, 6], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-PE-07"]),
      C("fouls_to_give_opp", "int", "max(0, 6 - team_fouls_opp).", unit="count", rng=[0, 6], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-PE-07"]),
      C("timeouts_msu", "int", "MSU charged timeouts left.", unit="count", rng=[0, 12], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("timeouts_opp", "int", "Opponent charged timeouts left.", unit="count", rng=[0, 12], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("media_segment_id", "string", "Media-timeout segment: H<half>-S<k>, k = number of media timeouts already taken this half (S0 = from 20:00 to the first). Extra periods: OT<n>. Boundaries are the media timeouts actually taken (first dead ball at or after 16:00, 12:00, 8:00, 4:00; Rule 5-14.10.c, A.R. 5-33).",
        src=S_DER + " + timeouts", lic=L_US, asof=A_PASS, req=["R-SR-03", "R-SR-04", "R-MD-13"]),
      C("ten_min_bucket_id", "string", "Analysis bucket H1-A (20:00-10:00), H1-B, H2-A, H2-B, OT<n>. NCAA men play halves; these are analysis buckets only (R-SR-03).",
        src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("five_min_window_id", "string", "H<half>-W<1..4>, OT<n> (R-MD-13).", src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-13"]),
      C("last4_flag", "bool", "Game clock <= 240 s in period >= 2.", src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-13"]),
      C("clutch_flag", "bool", "<= 300 s left in period >= 2 and |margin| <= 5 (R-MD-13).", src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-13"]),
      C("two_for_one_window", "bool", "Team gains or holds control with the game clock inside config window two_for_one_window_s (proposal [33, 45] s) of any period.", src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-11", "R-PE-07"]),
      C("foul_to_extend_window", "bool", "Trailing team on defence, period >= 2, game clock <= config foul_to_extend_clock_s (proposal 60 s), deficit within config foul_to_extend_margin (proposal 1-9).",
        src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-11", "R-PE-07"]),
      C("last_shot_window", "bool", "Team in control and the shot clock is off (game clock below a shot-clock period) or game clock <= shot clock.", src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-11", "R-PE-07"]),
      C("foul_trouble_msu", "list[string]", "MSU players in foul trouble: >= 2 personal fouls in the first half, >= 4 in the second half or extra periods (R-SR-11 proposal; config).",
        src=S_DER + " + foul_state", lic=L_US, asof=A_PASS, req=["R-SR-11", "R-MD-16", "R-PE-06"]),
      C("foul_trouble_opp", "list[string]", "Same for opponent players.", src=S_DER + " + foul_state", lic=L_US, asof=A_PASS, req=["R-SR-11", "R-MD-16", "R-PE-06"]),
      C("lead_changes", "int", "Lead changes so far in the game.", unit="count", rng=[0, 100], src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-17"]),
      C("run_msu_2min", "int", "MSU points in the last 120 game-clock seconds.", unit="points", rng=[0, 40], src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-17"]),
      C("run_opp_2min", "int", "Opponent points in the last 120 game-clock seconds.", unit="points", rng=[0, 40], src=S_DER, lic=L_US, asof=A_PASS, req=["R-MD-17"]),
      C("xpts_possession", "float", "Expected points of the current possession (value owned by the possession_value table, R-SR-12; stamped here).", unit="points", rng=[0, 6],
        src="value layer", lic=L_US, asof=A_PASS, req=["R-SR-12"], null=True),
      *prov("clock", ["R-SR-01"], "clock"),
      *prov("possession", ["R-SR-05"], "possession and phase"),
      *prov("fouls", ["R-SR-03"], "foul and bonus"),
      *prov("ft", ["R-SR-09"], "free-throw state"),
      C("invariant_breaks", "list[string]", "Invariant IDs broken in this second.", src="invariant checker", lic=L_US, asof=A_PASS, req=["R-IV-01..16"]),
      *lineage(),
  ])

# ================================================================ score_events
T(table="score_events",
  grain="one row per change of either team's score per pass, including official and scorer corrections as their own rows",
  primary_key=["score_event_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["made_basket_event_id"], "references": "made_basket_events.make_id"},
                {"columns": ["free_throw_id"], "references": "free_throws.free_throw_id"},
                {"columns": ["shot_id"], "references": "shots.shot_id"},
                {"columns": ["pbp_event_id"], "references": "events.event_id"},
                {"columns": ["review_id"], "references": "reviews.review_id"}],
  requirements=["R-SR-02", "R-IV-04", "R-SB-01", "R-SB-03", "R-MB-01", "R-DQ-06"],
  notes=["Sum of delta_points per team equals the final score of the box score (R-IV-04, R-DQ-06).",
         "A correction (board fixed during a timeout or review) is a row with event_kind official_correction or scorer_correction and a signed delta; the earlier wrong row is never edited."],
  columns=[
      C("score_event_id", "string", "game_id + pass + seq.", src="pipeline", lic=L_US, asof="n/a", req=["R-SR-02"]),
      GAME, PASS,
      C("seq", "int", "Order of the score change in the game for this pass.", rng=[1, 400], src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-02"]),
      PERIOD, CLOCK,
      C("video_ts_ms", "int", "Video time of the make (ball through the net) or of the board change for awarded points / corrections.", unit="ms", rng=[0, None],
        src=S_CV + "; OCR", lic=L_US, asof=A_FRAME, req=["R-SR-02", "R-SB-03"], null=True),
      C("frame_index", "int", "Frame of video_ts_ms.", rng=[0, None], src="video decode", lic=L_US, asof=A_FRAME, req=["R-SR-02"], null=True),
      C("team", "enum", "Team credited with the points.", values=TEAM_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-02"]),
      C("delta_points", "int", "Signed change: +1, +2, +3 for scores; negative only for corrections.", unit="points", rng=[-3, 3], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-02", "R-IV-04"]),
      C("event_kind", "enum", "field_goal, free_throw, awarded_goaltending, awarded_basket_interference (Rule 9-15 penalty), own_basket_credit (ball into own basket counts 2 for the opponent, Rule 5-1.4.a), illegal_assistance_award (Rule 9-16.1.c), official_correction, scorer_correction.",
        values=["field_goal", "free_throw", "awarded_goaltending", "awarded_basket_interference", "own_basket_credit", "illegal_assistance_award", "official_correction", "scorer_correction"],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-02", "R-IV-04", "R-MB-05"]),
      C("score_msu_after", "int", "MSU score after the event.", unit="points", rng=[0, 250], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-02"]),
      C("score_opp_after", "int", "Opponent score after the event.", unit="points", rng=[0, 250], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-02"]),
      C("scorer_player_id", "string", "Credited player; null for own-basket credit (not credited to a player, Rule 5-1.4.a) and corrections.", src=S_PBP + "; CV identity in blind pass",
        lic=L_ROW, asof=A_PASS, req=["R-SR-02"], null=True),
      C("made_basket_event_id", "string", "FK made_basket_events for field goals.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-MB-01"], null=True),
      C("free_throw_id", "string", "FK free_throws for free throws.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-09"], null=True),
      C("shot_id", "string", "FK shots (dictionary_games.md).", src="pipeline", lic=L_US, asof=A_PASS, req=["R-EV-07"], null=True),
      C("review_id", "string", "FK reviews when the event comes from or was changed by a review.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SB-01"], null=True),
      C("seen_ocr", "bool", "Board score change observed.", src=S_OCR, lic=L_US, asof=A_FRAME, req=["R-SB-01"]),
      C("seen_cv", "bool", "Vision make cue present (made_basket_events).", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SB-01", "R-MB-01"]),
      C("seen_pbp", "bool", "PBP scoring play matched (anchored pass).", src=S_PBP, lic=L_ROW, asof=A_POST, req=["R-SB-01"]),
      C("ocr_change_video_ts_ms", "int", "Video time the board score changed.", unit="ms", rng=[0, None], src=S_OCR, lic=L_US, asof=A_FRAME, req=["R-SB-03"], null=True),
      C("board_lag_s", "float", "ocr_change_video_ts_ms minus make video time; the per-game distribution is the lag table (R-SB-03).", unit="s", rng=[-5, 120],
        src=S_DER, lic=L_US, asof=A_FRAME, req=["R-SB-03"], null=True),
      C("flag_ids", "list[string]", "scoreboard_flags raised for this event.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SB-01"]),
      *prov("score", ["R-SR-02"], "score event"),
      *pbp_lineage(),
      *lineage(),
  ])

# ================================================================ foul_state
T(table="foul_state",
  grain="one row per game, pass, team, subject (team or one player) and bucket (half, period, ten_minute, media_segment, game)",
  primary_key=["game_id", "pass", "team", "subject_id", "bucket_type", "bucket_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["subject_id"], "references": "rosters.player_id (when not '_team')"}],
  requirements=["R-SR-03", "R-SR-11", "R-IV-03", "R-IV-09", "R-MD-07", "R-MD-16", "R-RF-03", "R-PE-06", "R-PE-07"],
  notes=["Team rows: subject_id = '_team'. Player rows: personal fouls per player per bucket (R-SR-03 'personal fouls per player').",
         "bucket_type 'half' is the rule bucket (team fouls and bonus; H2 includes extra periods, Rule 5-9.4). 'period' splits extra periods out for analysis. 'ten_minute' and 'media_segment' are analysis buckets only.",
         "Individual fouls live in the fouls table (dictionary_games.md); this table is the state roll-up and must recompute from it (R-SR-11 test)."],
  columns=[
      GAME, PASS3,
      C("team", "enum", "Team that committed the fouls.", values=TEAM_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("subject_id", "string", "'_team' for the team row, else roster player ID.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-03", "R-MD-16"]),
      C("bucket_type", "enum", "half, period, ten_minute, media_segment, game.", values=["half", "period", "ten_minute", "media_segment", "game"], src="pipeline", lic=L_US, asof="n/a", req=["R-SR-03"]),
      C("bucket_id", "string", "H1, H2 (incl. OT) | P1, P2, OT1.. | H1-A, H1-B, H2-A, H2-B, OT<n> | H<h>-S<k>, OT<n> | G.", src="pipeline", lic=L_US, asof="n/a", req=["R-SR-03", "R-MD-13"]),
      C("bucket_start_clock_s", "float", "Game clock at bucket start (media segments: clock when the media timeout was taken).", unit="s", rng=[0, 1200], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("bucket_end_clock_s", "float", "Game clock at bucket end.", unit="s", rng=[0, 1200], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("team_fouls_start", "int", "Team-foul total at bucket start (half rule count).", unit="count", rng=[0, 60], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-IV-09"]),
      C("team_fouls_end", "int", "Team-foul total at bucket end.", unit="count", rng=[0, 60], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-IV-09"]),
      C("fouls_team_total", "int", "Fouls in the bucket that count toward the team-foul total: personal (incl. player-control) + Class A technical (Rule 8-2.3).", unit="count", rng=[0, 60],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-IV-09"]),
      C("personal_fouls", "int", "All personal fouls (Rule 4-15.2).", unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("shooting_fouls", "int", "Personal fouls on a player in the act of shooting.", unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-RF-03"]),
      C("common_nonshooting_fouls", "int", "Common fouls not on a shooter and not player/team-control.", unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("player_control_fouls", "int", "Player-control fouls (offensive, Rule 4-15.2.a.1).", unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("team_control_fouls", "int", "Team-control fouls that are not loose-ball fouls (Rule 4-15.2.a.2).", unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("loose_ball_fouls", "int", "Loose-ball fouls (Rule 4-15.2.a.3; on an offensive player also team-control but bonus-eligible).", unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("flagrant1_fouls", "int", "Flagrant 1 personal fouls.", unit="count", rng=[0, 10], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("flagrant2_fouls", "int", "Flagrant 2 personal fouls.", unit="count", rng=[0, 10], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("double_simultaneous_fouls", "int", "Fouls that are part of a double or simultaneous foul (no free throws, Rule 10-1 Penalty f).", unit="count", rng=[0, 20], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("technical_class_a", "int", "Class A technical fouls (count toward team fouls and disqualification).", unit="count", rng=[0, 10], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("technical_class_b", "int", "Class B technical fouls (no team-foul count; 1 free throw).", unit="count", rng=[0, 10], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("technical_admin", "int", "Administrative technical fouls (no team-foul count).", unit="count", rng=[0, 10], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("bonus_reached_clock_s", "float", "Game clock when this team's 7th team foul of the half put the opponent in the bonus (half buckets only).", unit="s", rng=[0, 1200],
        src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-MD-07"], null=True),
      C("double_bonus_reached_clock_s", "float", "Game clock of the 10th team foul of the half.", unit="s", rng=[0, 1200], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-MD-07"], null=True),
      C("fouls_to_give_start", "int", "max(0, 6 - team_fouls_start).", unit="count", rng=[0, 6], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("fta_conceded", "int", "Free-throw attempts awarded to the opponent from these fouls.", unit="count", rng=[0, 80], src=S_DER + " + free_throws", lic=L_US, asof=A_PASS, req=["R-SR-03", "R-SR-09"]),
      C("ft_points_conceded", "int", "Opponent free-throw points from these fouls.", unit="points", rng=[0, 80], src=S_DER + " + free_throws", lic=L_US, asof=A_PASS, req=["R-SR-03"]),
      C("personal_fouls_player_cum", "int", "Player rows: personal + Class A technical fouls so far in the game at bucket end (disqualification at 5, Rule 4-12.1).", unit="count", rng=[0, 5],
        src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-MD-16", "R-IV-03"], null=True),
      C("flagrant1_player_cum", "int", "Player rows: Flagrant 1 fouls so far (disqualification at 3, Rule 4-12.1).", unit="count", rng=[0, 3], src=S_DER, lic=L_US, asof=A_PASS, req=["R-IV-03"], null=True),
      C("disqualified", "bool", "Player rows: player disqualified or ejected by bucket end.", src=S_DER, lic=L_US, asof=A_PASS, req=["R-IV-03"], null=True),
      C("foul_trouble", "bool", "Player rows: in foul trouble at bucket end (R-SR-11 thresholds in config).", src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-11", "R-MD-16"], null=True),
      C("box_score_match", "bool", "Half and game buckets: counts equal the box score (R-SR-03 test).", src="cross-check", lic=L_US, asof=A_POST, req=["R-SR-03", "R-DQ-06"], null=True),
      *prov("fouls", ["R-SR-03"], "foul count"),
      *pbp_lineage(),
      *lineage(),
  ])

# ================================================================ free_throws
FT_AWARD = ["shooting_2", "shooting_3", "and_one", "one_and_one", "double_bonus", "flagrant1", "flagrant2",
            "technical_class_a", "technical_class_b", "technical_admin_1", "technical_admin_2",
            "multiple_foul", "substitute_ft"]
T(table="free_throws",
  grain="one row per free-throw attempt (including attempts cancelled by a violation and a one-and-one second attempt not taken) per pass",
  primary_key=["free_throw_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["foul_id"], "references": "fouls.foul_id"},
                {"columns": ["pbp_event_id"], "references": "events.event_id"},
                {"columns": ["score_event_id"], "references": "score_events.score_event_id"}],
  requirements=["R-SR-09", "R-IV-11", "R-PE-05", "R-RF-03", "R-SR-03"],
  notes=["ft_sequence_id groups the attempts of one award; for false double / multiple fouls each foul has its own sequence (Rule 10-1 Penalty g).",
         "award_type follows Rule 10-1 Penalty b-e, 8-2, 10-2, 10-3, 10-4. The live doc's 'technical 2' is refined: Class A = 2, Class B = 1, administrative = 1 (2 for Rule 10-2.6 and 10-2.7).",
         "One-and-one: attempts_n = 2 with second_attempt_conditional = true; the second row exists with result not_attempted when the first misses (makes accounting complete)."],
  columns=[
      C("free_throw_id", "string", "game_id + pass + ft_sequence_id + attempt_k.", src="pipeline", lic=L_US, asof="n/a", req=["R-SR-09"]),
      GAME, PASS,
      C("ft_sequence_id", "string", "One free-throw award (one foul's penalty).", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-09"]),
      C("attempt_k", "int", "Attempt number within the sequence.", rng=[1, 3], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-09", "R-IV-11"]),
      C("attempts_n", "int", "Attempts in the award (1, 2 or 3; one-and-one = 2 conditional). Name as in source_field_map.md 2.10 (hoopR NCAA ft_attempts).", rng=[1, 3], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-09", "R-IV-11"]),
      C("second_attempt_conditional", "bool", "True for one_and_one (second only if the first is made, Rule 8-2.1).", src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-09"]),
      C("award_type", "enum", "Why the free throws were awarded (see notes).", values=FT_AWARD, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-09", "R-IV-11"]),
      C("rule_ref", "string", "Rule that sets the award, e.g. '10-1 Penalty d.1'.", src="config/invariants.yaml mapping", lic=L_US, asof=A_PASS, req=["R-SR-09"]),
      C("ball_after", "enum", "What follows the last attempt: live (missed last FT for a personal foul, Rule 8-7), throw_in_opponent (made last FT, Rule 7-3.1.c), throw_in_shooting_team (flagrant, Rule 8-6.1.c), point_of_interruption (technical, Rule 8-6.1.b), next_sequence.",
        values=["live", "throw_in_opponent", "throw_in_shooting_team", "point_of_interruption", "next_sequence", "dead_other"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-09", "R-IV-08"]),
      C("team", "enum", "Shooting team.", values=TEAM_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-09"]),
      C("shooter_player_id", "string", "Player attempting (source_field_map.md 2.10 calls it shooter_id).", src=S_PBP + "; CV identity in blind pass", lic=L_ROW, asof=A_PASS, req=["R-SR-09", "R-PE-05"]),
      C("shooter_selection", "enum", "offended_player, substitute_for_offended (Rule 8-3.2), opponent_coach_choice (injured, Rule 8-3.3), designated_any (technical, Rule 8-3.4).",
        values=["offended_player", "substitute_for_offended", "opponent_coach_choice", "own_coach_choice", "designated_any"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-09"]),
      C("foul_id", "string", "FK fouls (dictionary_games.md).", src="pipeline", lic=L_US, asof=A_PASS, req=["R-RF-03"], null=True),
      C("fouling_player_id", "string", "Player charged with the foul (null for bench or team technicals).", src=S_PBP, lic=L_ROW, asof=A_PASS, req=["R-RF-03"], null=True),
      PERIOD, CLOCK,
      C("team_fouls_defence_at_foul", "int", "Fouling team's team-foul total including this foul.", unit="count", rng=[0, 60], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-03", "R-SR-09"]),
      C("video_ts_ms_disposal", "int", "Ball placed at the shooter's disposal (attempt starts, Rule 8-1.3).", unit="ms", rng=[0, None], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-09"], null=True),
      C("video_ts_ms_release", "int", "Ball released.", unit="ms", rng=[0, None], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-09"], null=True),
      C("release_latency_s", "float", "Release minus disposal; must be <= 10 s (Rule 8-5.1.a).", unit="s", rng=[0, 30], src=S_DER, lic=L_US, asof=A_FRAME, req=["R-IV-11"], null=True),
      C("result", "enum", "made, missed, cancelled_violation (shooting team violated, Rule 9-1 Penalty a), substitute_awarded (opponent violation on a miss, Penalty b.2), not_attempted (one-and-one second after a miss).",
        values=["made", "missed", "cancelled_violation", "substitute_awarded", "not_attempted"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-09"]),
      C("made", "bool", "result == 'made' (convenience column named as in source_field_map.md 2.10).", src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-09", "R-PE-05"]),
      C("ring_contact", "enum", "Attempt touched ring or flange (a free throw must, Rule 8-5.1.a).", values=["yes", "no", "unknown"], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-MB-07"]),
      C("lane_def_count", "int", "Opponents of the shooter in marked lane spaces (max 4, Rule 8-4.4).", unit="count", rng=[0, 4], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-09", "R-IV-11"], null=True),
      C("lane_off_count", "int", "Teammates of the shooter in marked lane spaces (max 2).", unit="count", rng=[0, 2], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-09", "R-IV-11"], null=True),
      C("lane_occupant_ids", "list[string]", "Roster IDs by lane space, ordered L1..L4 left then R1..R4 right from the basket out; empty string for an empty space.", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-09"]),
      C("lane_expected_empty", "bool", "Lane players not expected: ball dead regardless of result (Rule 8-4.8), double foul with one flagrant (10-1 Penalty f), or resumption of play (Rule 4-32).",
        src=S_DER, lic=L_US, asof=A_PASS, req=["R-IV-11"]),
      C("violation", "enum", "Free-throw violation code (Rule 9-1.1.a-l) or none.",
        values=["none", "a_10s", "b_fake", "c_line", "d_semicircle", "e_lane_early", "f_disconcert", "g_behind_line", "h_lane_plane", "i_foot_beyond", "j_too_many", "k_block_space_empty", "l_teammate_low_space"],
        src=S_CV + "; PBP", lic=L_US, asof=A_PASS, req=["R-IV-11"]),
      C("violation_team", "enum", "Team that violated.", values=TEAM3_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-IV-11"]),
      C("predicted_at_whistle", "bool", "The state model predicted 'free throws coming' at the foul whistle (R-SR-09).", src="state model", lic=L_US, asof=A_FRAME, req=["R-SR-09"], null=True),
      C("predicted_award_type", "enum", "Predicted award type at the whistle.", values=FT_AWARD + ["none"], src="state model", lic=L_US, asof=A_FRAME, req=["R-SR-09"], null=True),
      C("prediction_correct", "bool", "Prediction matched the actual award.", src=S_DER, lic=L_US, asof=A_POST, req=["R-SR-09"], null=True),
      C("lane_formation_confirmed", "bool", "Lane formation seen in video confirmed the free-throw state before disposal.", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-09"], null=True),
      C("score_event_id", "string", "FK score_events when made.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-02"], null=True),
      *prov("ft", ["R-SR-09"], "free-throw"),
      *pbp_lineage(),
      *lineage(),
  ])

# ================================================================ timeouts
T(table="timeouts",
  grain="one row per stoppage that is a timeout: team-charged, media, injury-charged, appeal- or challenge-charged, excessive; one row per (game, pass, timeout_seq)",
  primary_key=["timeout_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["review_id"], "references": "reviews.review_id"},
                {"columns": ["pbp_event_id"], "references": "events.event_id"}],
  requirements=["R-SR-04", "R-IV-10", "R-MD-07", "R-MD-13", "R-PE-07"],
  notes=["Media format per game (media_format) decides the allotment: at_least_3_media (Rule 5-14.10: three 30 s + one 60 s; at most two 30 s carried into the second half; +1 x 30 s per extra period), fewer_than_3_media (5-14.9) or no_media (5-14.8: four 75 s + two 30 s; +1 x 75 s per extra period).",
         "Read from PBP where available; the live doc says the format depends on the media agreement per game."],
  columns=[
      C("timeout_id", "string", "game_id + pass + timeout_seq.", src="pipeline", lic=L_US, asof="n/a", req=["R-SR-04"]),
      GAME, PASS3,
      C("timeout_seq", "int", "Order in the game.", rng=[1, 60], src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      PERIOD, CLOCK,
      C("video_ts_ms_start", "int", "Video time the timeout starts (official signals).", unit="ms", rng=[0, None], src=S_CV + "; OCR", lic=L_US, asof=A_FRAME, req=["R-SR-04"], null=True),
      C("video_ts_ms_end", "int", "Video time play resumes (ball live).", unit="ms", rng=[0, None], src=S_CV + "; OCR", lic=L_US, asof=A_FRAME, req=["R-SR-04"], null=True),
      C("duration_s", "float", "Real time of the stoppage.", unit="s", rng=[0, 1200], src=S_DER, lic=L_US, asof=A_FRAME, req=["R-SR-04"], null=True),
      C("media_format", "enum", "Game's timeout format.", values=["at_least_3_media", "fewer_than_3_media", "no_media", "unknown"], src="PBP + registry broadcast", lic=L_US, asof=A_REG, req=["R-SR-04", "R-IV-10"]),
      C("media_marks", "enum", "Media marks in use.", values=["16_12_8_4", "15_10_5", "agreement_other", "none"], src="PBP + OCR", lic=L_US, asof=A_REG, req=["R-SR-04", "R-MD-13"]),
      C("timeout_type", "enum", "team_30, team_60, team_75, media, injury_charged, appeal_charged (Rule 11-5), challenge (Rule 11-4), excessive (Rule 5-17), official_stoppage (not charged). Name as in source_field_map.md 2.12; its coarse values map: short -> team_30, full -> team_60 or team_75 by media_format, media/OfficialTVTimeOut -> media, official -> official_stoppage.",
        values=["team_30", "team_60", "team_75", "media", "injury_charged", "appeal_charged", "challenge", "excessive", "official_stoppage"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("team", "enum", "Team that called or is charged; none for media and official stoppages.", values=TEAM3_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("called_by", "enum", "Who requested it.", values=["head_coach", "player", "official", "media", "unknown"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("requesting_player_id", "string", "Player who requested, when a player did.", src=S_PBP + "; CV", lic=L_ROW, asof=A_PASS, req=["R-SR-04"], null=True),
      C("charged", "bool", "Charged to the team (false for media, official stoppages, successful challenges, injury rules of Rule 5-16).", src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"]),
      C("became_media", "bool", "Team timeout converted into the media timeout (first dead ball at or after a mark, within 30 s before a mark, or first team timeout of the second half; Rule 5-14.10.d-e).",
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-MD-13"]),
      C("media_slot", "string", "H<half>-<mark> (e.g. H1-16, H2-4), H2-first_team, OT<n>-first, or none.", src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-MD-13"]),
      C("mark_clock_s", "float", "Game-clock value of the media mark this timeout serves (960, 720, 480, 240 for 16/12/8/4).", unit="s", rng=[0, 1200], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-04"], null=True),
      C("first_dead_ball_after_mark", "bool", "Media timeout taken at the first dead ball at or after its mark (Rule 5-14.10.c).", src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"], null=True),
      C("shortened", "bool", "Timeout shortened by the requesting team (Rule 5-14.14).", src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("left_after_msu", "int", "MSU charged timeouts left after this row (all lengths).", unit="count", rng=[0, 12], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"]),
      C("left_after_opp", "int", "Opponent charged timeouts left after this row.", unit="count", rng=[0, 12], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"]),
      C("halftime_carry_loss", "int", "30 s timeouts lost at half because only two carry over (Rule 5-14.10.a.1); recorded on a synthetic row at period 2 start.", unit="count", rng=[0, 3], src=S_DER, lic=L_US, asof=A_PASS, req=["R-IV-10"], null=True),
      C("ato_set_instance_id", "string", "After-timeout set started at the next live ball (link to sets layer).", src="ST layer", lic=L_US, asof=A_PASS, req=["R-SR-08"], null=True),
      C("review_id", "string", "Linked review for challenge or appeal timeouts.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-04"], null=True),
      *prov("timeouts", ["R-SR-04"], "timeout"),
      *pbp_lineage(),
      *lineage(),
  ])

# ================================================================ reviews
T(table="reviews",
  grain="one row per instant-replay review, coach's challenge, appeal or correctable-error / timing correction per pass",
  primary_key=["review_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["timeout_id"], "references": "timeouts.timeout_id"},
                {"columns": ["pbp_event_id"], "references": "events.event_id"}],
  requirements=["R-SR-04", "R-RF-07", "R-SB-01", "R-SB-02", "R-MB-05", "R-IV-05", "R-IV-12"],
  notes=["Broadcast replays shown during a review are flagged in state_frame.replay_flag; this table records the officials' review itself.",
         "Rule 2-9.19 (new in the 2026-27 post-clinic interpretations, 15 Oct 2026) makes the scorer record coach's challenges."],
  columns=[
      C("review_id", "string", "game_id + pass + review_seq.", src="pipeline", lic=L_US, asof="n/a", req=["R-SR-04"]),
      GAME, PASS3,
      C("review_seq", "int", "Order in the game.", rng=[1, 40], src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      PERIOD,
      C("game_clock_at_stop_s", "float", "Game clock when play stopped for the review.", unit="s", rng=[0, 1200], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("video_ts_ms_start", "int", "Review starts.", unit="ms", rng=[0, None], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-04"], null=True),
      C("video_ts_ms_end", "int", "Review result signalled.", unit="ms", rng=[0, None], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-04"], null=True),
      C("review_kind", "enum", "voluntary (Rule 11-2), mandatory (11-3), coach_challenge (11-4), appeal (11-5), correctable_error (2-12), timing_correction (5-12).",
        values=["voluntary", "mandatory", "coach_challenge", "appeal", "correctable_error", "timing_correction"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-RF-07"]),
      C("subject", "enum", "What is reviewed.",
        values=["two_vs_three", "scoring_mistake", "shot_clock_release", "goaltending_basket_interference", "out_of_bounds", "restricted_area", "flagrant_severity",
                "foul_attribution", "game_clock_time", "shot_clock_time", "end_of_period_try", "end_of_period_foul", "ft_shooter", "wrong_basket", "fight", "other"],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-MB-05"]),
      C("rule_ref", "string", "Rule article allowing the review (e.g. '11-2.1.b.1').", src="config", lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("requested_by", "enum", "Who started it.", values=["official", "head_coach_msu", "head_coach_opp", "table"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("call_on_floor", "string", "Original call in plain words.", src=S_PBP + "; CV/manual", lic=L_ROW, asof=A_PASS, req=["R-SR-04"], null=True),
      C("outcome", "enum", "confirmed, overturned, stands (no indisputable evidence, Rule 11-1.1), corrected (clock or score changed).",
        values=["confirmed", "overturned", "stands", "corrected"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("challenge_number", "int", "1 or 2 for coach's challenges (second only after a successful first, Rule 11-4.1.d).", rng=[1, 2], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"], null=True),
      C("timeout_charged", "bool", "A timeout was charged (unsuccessful challenge or appeal, Rule 11-4.1.h, 11-5.1).", src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04", "R-IV-10"]),
      C("timeout_id", "string", "FK timeouts.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-04"], null=True),
      C("game_clock_before_s", "float", "Game clock before the review.", unit="s", rng=[0, 1200], src=S_OCR, lic=L_US, asof=A_FRAME, req=["R-IV-05"], null=True),
      C("game_clock_after_s", "float", "Game clock after (a correction may move it up, flagged official_clock_correction).", unit="s", rng=[0, 1200], src=S_OCR, lic=L_US, asof=A_FRAME, req=["R-IV-05"], null=True),
      C("shot_clock_before_s", "float", "Shot clock before.", unit="s", rng=[0, 30], src=S_OCR, lic=L_US, asof=A_FRAME, req=["R-IV-07"], null=True),
      C("shot_clock_after_s", "float", "Shot clock after.", unit="s", rng=[0, 30], src=S_OCR, lic=L_US, asof=A_FRAME, req=["R-IV-07"], null=True),
      C("score_delta_msu", "int", "Change to MSU score from the review.", unit="points", rng=[-3, 3], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SB-01"]),
      C("score_delta_opp", "int", "Change to the opponent score.", unit="points", rng=[-3, 3], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SB-01"]),
      C("possession_after", "enum", "Team awarded the ball after the review.", values=TEAM3_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-04"]),
      C("arrow_used", "bool", "Possession decided by the arrow (e.g. reversed goaltending with no team control, Rule 11-2.1.b.6.a).", src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-MD-12"]),
      *prov("review", ["R-SR-04"], "review"),
      *pbp_lineage(),
      *lineage(),
  ])

# ================================================================ restarts
T(table="restarts",
  grain="one row per transition from dead ball to live ball (and each period start) per pass",
  primary_key=["restart_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["possession_id"], "references": "possessions.possession_id"},
                {"columns": ["pbp_event_id"], "references": "events.event_id"}],
  requirements=["R-SR-08", "R-MD-03", "R-MD-12", "R-IV-07", "R-IV-08", "R-SY-08", "R-SY-09"],
  notes=["Throw-in spot after a frontcourt stoppage: end line 3 ft (0.91 m) outside the lane line, or the 28-foot (8.53 m) mark on the sideline, per Rule 7-3.2.b as changed in 2025-26 (proposal 6 of the 2025-26 changes says below vs above the free-throw line extended; the 2026-27 book text describes an imaginary line from the end-line/sideline corner to the free-throw line extended; see open questions).",
         "The shot-clock value set at the restart is checked against config/invariants.yaml (R-SY-09)."],
  columns=[
      C("restart_id", "string", "game_id + pass + restart_seq.", src="pipeline", lic=L_US, asof="n/a", req=["R-SR-08"]),
      GAME, PASS3,
      C("restart_seq", "int", "Order in the game.", rng=[1, 600], src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-08"]),
      PERIOD, CLOCK,
      C("video_ts_ms_dead", "int", "Ball became dead.", unit="ms", rng=[0, None], src=S_CV + "; audio whistle", lic=L_US, asof=A_FRAME, req=["R-SR-08", "R-RF-01"], null=True),
      C("video_ts_ms_live", "int", "Ball became live (disposal of thrower-in / free-thrower, toss).", unit="ms", rng=[0, None], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-08"], null=True),
      C("dead_duration_s", "float", "Real-time length of the dead ball.", unit="s", rng=[0, 3600], src=S_DER, lic=L_US, asof=A_FRAME, req=["R-SR-08"], null=True),
      C("dead_ball_reason", "enum", "Why the ball became dead (Rule 6-5.1).",
        values=["period_start", "made_fg", "made_last_ft", "ft_followed_by_ft", "personal_foul", "technical_foul", "double_foul", "violation_out_of_bounds", "violation_travel",
                "violation_other", "shot_clock_violation", "held_ball", "ball_lodged", "timeout", "injury_blood", "review", "inadvertent_whistle", "period_end", "other"],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-08"]),
      C("violation_code", "string", "Rule 9 section of the violation when dead_ball_reason is a violation (e.g. '9-5' travel, '9-10' backcourt 10 s, '9-14' closely guarded).", src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-08"], null=True),
      C("restart_type", "enum", "How play resumed (Rule 6-5.2).",
        values=["jump_ball", "throw_in_end_line_after_score", "throw_in_designated_spot", "throw_in_alternating_possession", "throw_in_point_of_interruption", "free_throw", "second_half_ap_division_line"],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-08", "R-IV-08"]),
      C("throw_in_spot", "enum", "Spot class.", values=["end_line_runnable", "end_line_3ft_outside_lane", "sideline_28ft_mark", "sideline_spot", "end_line_spot", "backcourt_spot", "division_line_opposite_table", "none"],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-08", "R-MD-03"]),
      C("spot_x_m", "float", "Throw-in spot x (attacked-rim frame of the throw-in team).", unit="m", rng=[-8.62, 8.62], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-08"], null=True),
      C("spot_y_m", "float", "Throw-in spot y.", unit="m", rng=[-2.6, 28.05], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-08"], null=True),
      C("court_half", "enum", "Front or back court of the throw-in team.", values=["front", "back", "none"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-MD-03"]),
      C("inbound_side", "enum", "Global field.", values=["sideline", "baseline", "none"], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-MD-03"], gm=True),
      C("restart_team", "enum", "Team putting the ball in play.", values=TEAM3_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-SR-08", "R-IV-08"]),
      C("thrower_player_id", "string", "Thrower-in or free-thrower.", src=S_CV + "; PBP", lic=L_US, asof=A_PASS, req=["R-SR-08"], null=True),
      C("arrow_before", "enum", "Arrow before the restart.", values=TEAM3_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-MD-12"]),
      C("arrow_after", "enum", "Arrow after (flips when an alternating-possession throw-in ends, Rule 6-3.2).", values=TEAM3_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-MD-12", "R-IV-08"]),
      C("shot_clock_before_s", "float", "Shot clock at the dead ball.", unit="s", rng=[0, 30], src=S_OCR, lic=L_US, asof=A_FRAME, req=["R-SY-08"], null=True),
      C("shot_clock_set_s", "float", "Shot clock shown at the restart (30, 20, unexpired or off).", unit="s", rng=[0, 30], src=S_OCR, lic=L_US, asof=A_FRAME, req=["R-SY-08", "R-IV-07"], null=True),
      C("shot_clock_expected_s", "float", "Value required by the rule for this reason (config/invariants.yaml shot_clock_reset_table).", unit="s", rng=[0, 30], src=S_DER, lic=L_US, asof=A_PASS, req=["R-SY-09", "R-IV-07"], null=True),
      C("shot_clock_rule_ref", "string", "Rule 2-11.6 clause applied (e.g. '2-11.6.c.1').", src="config", lic=L_US, asof=A_PASS, req=["R-SY-09"], null=True),
      C("throw_in_count_s", "float", "Disposal to release (<= 5 s, Rule 7-6.6).", unit="s", rng=[0, 10], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-08"], null=True),
      C("after_timeout", "bool", "First live ball after a timeout (ATO).", src=S_DER, lic=L_US, asof=A_PASS, req=["R-SR-08"]),
      C("possession_id", "int", "Possession the restart belongs to.", rng=[0, None], src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-MD-04"], null=True),
      *prov("restart", ["R-SR-08"], "restart"),
      *pbp_lineage(),
      *lineage(),
  ])

# ================================================================ scoreboard_ocr
T(table="scoreboard_ocr",
  grain="one row per OCR reading of one scoreboard display in one sampled frame (raw readings, immutable, pass-independent)",
  primary_key=["reading_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["video_id", "frame_index"], "references": "frames.(video_id, frame_index)"}],
  requirements=["R-SY-01", "R-SR-01", "R-SR-02", "R-SR-15", "R-SB-01", "R-SB-03", "R-MD-08", "R-MD-20", "R-DQ-05"],
  notes=["Immutable: written once, never updated or deleted; a re-read by a new OCR model is a new row with a new ocr_model_version. Corrections live in state_corrections and scoreboard_flags (R-SR-15).",
         "Home/away as printed on the display; mapping to msu/opponent happens downstream via games (MSU side), so a raw row never depends on our interpretation.",
         "Sampling: every frame where the scorebug is visible is the target (R-SY-01 asks every second of live play as the minimum)."],
  columns=[
      C("reading_id", "string", "game_id + video_id + frame_index + display + ocr_model_version.", src="pipeline", lic=L_US, asof="n/a", req=["R-SR-15"]),
      GAME,
      C("video_id", "string", "Video file.", src="video registry", lic=L_US, asof=A_FRAME, req=["R-SY-01"]),
      C("frame_index", "int", "Frame read.", rng=[0, None], src="video decode", lic=L_US, asof=A_FRAME, req=["R-SY-01"]),
      VTS,
      C("display", "enum", "Which display was read.", values=["broadcast_scorebug", "arena_scoreboard", "shot_clock_unit", "scorer_table_led"], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SY-01", "R-SB-01"]),
      C("scorebug_template_id", "string", "Broadcast graphics package template (R-MD-20).", src="OCR template registry", lic=L_US, asof=A_FRAME, req=["R-MD-20"], null=True),
      C("bbox_x_px", "int", "Display box left.", unit="px", rng=[0, 7680], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SY-01"]),
      C("bbox_y_px", "int", "Display box top.", unit="px", rng=[0, 4320], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SY-01"]),
      C("bbox_w_px", "int", "Display box width.", unit="px", rng=[1, 7680], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SY-01"]),
      C("bbox_h_px", "int", "Display box height.", unit="px", rng=[1, 4320], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SY-01"]),
      C("period_raw", "string", "Text as read (e.g. '1st', '2ND', 'OT', 'HALF').", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-01"], null=True),
      C("game_clock_raw", "string", "Text as read (e.g. '12:34', '45.6').", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-01"], null=True),
      C("shot_clock_raw", "string", "Text as read; blank display recorded as ''.", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-01"], null=True),
      C("score_home_raw", "string", "Home score text.", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-02"], null=True),
      C("score_away_raw", "string", "Away score text.", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-02"], null=True),
      C("team_fouls_home_raw", "string", "Home team fouls text.", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-03"], null=True),
      C("team_fouls_away_raw", "string", "Away team fouls text.", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-03"], null=True),
      C("bonus_home_raw", "string", "Home bonus indicator text ('BONUS', 'BONUS+', 'DBL BONUS', '').", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-03"], null=True),
      C("bonus_away_raw", "string", "Away bonus indicator text.", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-03"], null=True),
      C("timeouts_home_raw", "string", "Home timeouts text or pip count.", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-04"], null=True),
      C("timeouts_away_raw", "string", "Away timeouts text or pip count.", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-04"], null=True),
      C("arrow_raw", "string", "Possession-arrow indicator as read ('home', 'away', '').", src="OCR", lic=L_US, asof=A_FRAME, req=["R-MD-12"], null=True),
      C("period_parsed", "int", "Parsed period.", rng=[1, 12], src="OCR parser", lic=L_US, asof=A_FRAME, req=["R-SR-01"], null=True),
      C("game_clock_parsed_s", "float", "Parsed game clock.", unit="s", rng=[0, 1200], src="OCR parser", lic=L_US, asof=A_FRAME, req=["R-SR-01"], null=True),
      C("shot_clock_parsed_s", "float", "Parsed shot clock (null when blank).", unit="s", rng=[0, 30], src="OCR parser", lic=L_US, asof=A_FRAME, req=["R-SR-01"], null=True),
      C("score_home_parsed", "int", "Parsed home score.", unit="points", rng=[0, 250], src="OCR parser", lic=L_US, asof=A_FRAME, req=["R-SR-02"], null=True),
      C("score_away_parsed", "int", "Parsed away score.", unit="points", rng=[0, 250], src="OCR parser", lic=L_US, asof=A_FRAME, req=["R-SR-02"], null=True),
      C("team_fouls_home_parsed", "int", "Parsed.", unit="count", rng=[0, 60], src="OCR parser", lic=L_US, asof=A_FRAME, req=["R-SR-03"], null=True),
      C("team_fouls_away_parsed", "int", "Parsed.", unit="count", rng=[0, 60], src="OCR parser", lic=L_US, asof=A_FRAME, req=["R-SR-03"], null=True),
      C("timeouts_home_parsed", "int", "Parsed.", unit="count", rng=[0, 12], src="OCR parser", lic=L_US, asof=A_FRAME, req=["R-SR-04"], null=True),
      C("timeouts_away_parsed", "int", "Parsed.", unit="count", rng=[0, 12], src="OCR parser", lic=L_US, asof=A_FRAME, req=["R-SR-04"], null=True),
      C("field_conf_json", "string", "JSON map field -> OCR confidence (0-1) for every parsed field.", src="OCR", lic=L_US, asof=A_FRAME, req=["R-SR-15", "R-MD-09"]),
      C("ocr_model_version", "string", "OCR model and template version.", src="pipeline", lic=L_US, asof="n/a", req=["R-MD-09"]),
      C("crop_sha256", "string", "SHA-256 of the cropped display image (crop stored privately, never in the repo), so a reading can be audited.", src="pipeline", lic=L_US, asof="n/a", req=["R-DQ-04", "R-DQ-05"]),
      C("created_utc", "timestamp", "Write time (write-once).", unit="UTC", src="pipeline", lic=L_US, asof="n/a", req=["R-SR-15"]),
  ])

# ================================================================ scoreboard_flags
T(table="scoreboard_flags",
  grain="one row per discrepancy or invariant break raised in a game pass; review answer fields are filled once (append-only versions)",
  primary_key=["flag_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["score_event_id"], "references": "score_events.score_event_id"},
                {"columns": ["make_id"], "references": "made_basket_events.make_id"},
                {"columns": ["restart_id"], "references": "restarts.restart_id"},
                {"columns": ["pbp_event_id"], "references": "events.event_id"}],
  requirements=["R-SB-01", "R-SB-02", "R-SB-03", "R-SB-04", "R-IV-01..16", "R-HR-01", "R-HR-05", "R-DQ-03"],
  notes=["Holds the R-SB-01 types (a)-(j) and every invariant break from config/invariants.yaml (flag_type = invariant_break, invariant_id set), so one review queue serves both.",
         "No flag is left without review_answer before the game enters training (R-SB-02); more than 3 unresolved flags keep the game out of engine training (R-SB-04)."],
  columns=[
      C("flag_id", "string", "game_id + pass + flag_seq.", src="pipeline", lic=L_US, asof="n/a", req=["R-SB-01"]),
      GAME, PASS3,
      C("flag_seq", "int", "Order raised.", rng=[1, 100000], src="pipeline", lic=L_US, asof=A_PASS, req=["R-SB-01"]),
      C("flag_type", "enum", "R-SB-01 types a-j or invariant_break.",
        values=["a_score_change_no_make_seen", "b_make_seen_no_score_change", "c_wrong_value", "d_wrong_team", "e_double_count", "f_late_update", "g_game_clock_not_started_or_stopped",
                "h_shot_clock_not_reset_or_wrong", "i_later_correction", "j_scorebug_lag", "invariant_break"], src="checker", lic=L_US, asof=A_PASS, req=["R-SB-01"]),
      C("invariant_id", "string", "ID from config/invariants.yaml (R-IV-nn or new-IV-nn) for invariant breaks.", src="checker", lic=L_US, asof=A_PASS, req=["R-IV-01..16"], null=True),
      PERIOD, CLOCK,
      C("video_ts_ms_start", "int", "Start of the evidence window.", unit="ms", rng=[0, None], src="checker", lic=L_US, asof=A_FRAME, req=["R-SB-01"], null=True),
      C("video_ts_ms_end", "int", "End of the evidence window.", unit="ms", rng=[0, None], src="checker", lic=L_US, asof=A_FRAME, req=["R-SB-01"], null=True),
      C("team", "enum", "Team concerned.", values=TEAM3_ENUM, src="checker", lic=L_US, asof=A_PASS, req=["R-SB-01"]),
      C("field", "string", "State field concerned (e.g. 'score_msu', 'shot_clock_s').", src="checker", lic=L_US, asof=A_PASS, req=["R-SB-01"]),
      C("expected_value", "string", "Value the rule or the other sensor implies.", src="checker", lic=L_US, asof=A_PASS, req=["R-SB-01"], null=True),
      C("observed_value", "string", "Value read.", src="checker", lic=L_US, asof=A_PASS, req=["R-SB-01"], null=True),
      C("lag_s", "float", "Board change minus event time (types f, j).", unit="s", rng=[-5, 600], src="checker", lic=L_US, asof=A_FRAME, req=["R-SB-03"], null=True),
      C("window_s", "float", "Detection window used (starts at 15 s, then reset from the measured lag; R-SB-03).", unit="s", rng=[0, 120], src="config", lic=L_US, asof=A_PASS, req=["R-SB-03"]),
      C("not_seen", "bool", "Camera off court at the moment: logged, not a break (R-SB-01 exception).", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SB-01"]),
      C("score_event_id", "string", "Linked score event.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SB-01"], null=True),
      C("make_id", "string", "Linked make.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-MB-01"], null=True),
      C("restart_id", "string", "Linked restart (shot-clock flags).", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SY-09"], null=True),
      C("reading_ids", "list[string]", "scoreboard_ocr readings used as evidence.", src="pipeline", lic=L_US, asof=A_FRAME, req=["R-SB-01"]),
      C("action", "enum", "Action from config/invariants.yaml.", values=["flag", "quarantine", "human_review"], src="config", lic=L_US, asof=A_PASS, req=["R-HR-01", "R-DQ-03"]),
      C("priority", "float", "Queue priority (model uncertainty x downstream impact, R-HR-03).", unit="score", rng=[0, None], src="queue", lic=L_US, asof=A_PASS, req=["R-HR-03"], null=True),
      C("review_answer", "enum", "R-SB-02 answer.", values=["scoreboard_malfunction", "scorebug_lag", "official_correction", "cv_miss", "cv_false_positive", "pbp_error", "unresolved"],
        src="manual review", lic=L_US, asof=A_REVIEW, req=["R-SB-02"], null=True),
      C("corrected_value", "string", "Corrected value (raw values elsewhere stay as written).", src="manual review", lic=L_US, asof=A_REVIEW, req=["R-SB-02", "R-SR-15"], null=True),
      C("reviewer", "string", "Who answered (R-HR-05).", src="manual review", lic=L_US, asof=A_REVIEW, req=["R-SB-02", "R-HR-05"], null=True),
      C("reviewed_utc", "timestamp", "When answered.", unit="UTC", src="manual review", lic=L_US, asof=A_REVIEW, req=["R-SB-02", "R-HR-05"], null=True),
      C("review_reason", "string", "Reason in words.", src="manual review", lic=L_US, asof=A_REVIEW, req=["R-SB-02"], null=True),
      C("status", "enum", "open or answered.", values=["open", "answered"], src="pipeline", lic=L_US, asof=A_REVIEW, req=["R-SB-02", "R-SB-04"]),
      *pbp_lineage(),
      *lineage(),
  ])

# ================================================================ made_basket_events
CUE = lambda n, what, src, req: [
    C(f"cue{n}_present", "bool", f"Cue {n}: {what}.", src=src, lic=L_US if "PBP" not in src else L_ROW, asof=A_FRAME if "PBP" not in src else A_POST, req=req),
    C(f"cue{n}_frame", "int", f"Frame of cue {n}.", rng=[0, None], src=src, lic=L_US, asof=A_FRAME, req=req, null=True),
    C(f"cue{n}_conf", "float", f"Confidence of cue {n}.", unit="0-1", rng=[0, 1], src=src, lic=L_US, asof=A_FRAME, req=req, null=True),
]
T(table="made_basket_events",
  grain="one row per candidate made basket (confirmed, vision-only, flagged or rejected) per pass, with every cue",
  primary_key=["make_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["shot_id"], "references": "shots.shot_id"},
                {"columns": ["score_event_id"], "references": "score_events.score_event_id"},
                {"columns": ["review_id"], "references": "reviews.review_id"}],
  requirements=["R-MB-01", "R-MB-02", "R-MB-03", "R-MB-04", "R-MB-05", "R-MB-06", "R-MB-07", "R-SB-01", "R-BL-05", "R-IV-04", "R-IV-12"],
  notes=["Decision rule (R-MB-01): confirmed = (cue 3 or cue 4) and (cue 1 or cue 2); vision_only (blind pass) = cue 1 and cue 2; not_seen_confirmed = camera cut, confirmed by cues 3 and 4; anything else flagged. Cue 5 is context, never decisive.",
         "Rim geometry: rim height 3.05 m, inner diameter 45.72 cm (18 in, Rule 1-14/1-15; check against config/court_ncaa_men.yaml)."],
  columns=[
      C("make_id", "string", "game_id + pass + make_seq.", src="pipeline", lic=L_US, asof="n/a", req=["R-MB-01"]),
      GAME, PASS,
      PERIOD, CLOCK,
      C("video_ts_ms_make", "int", "Video time the ball passes down through the ring plane (the make frame).", unit="ms", rng=[0, None], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-MB-01", "R-MB-04"], null=True),
      C("frame_index_make", "int", "Make frame.", rng=[0, None], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-MB-04"], null=True),
      C("team", "enum", "Team credited.", values=TEAM_ENUM, src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-MB-01"]),
      C("shooter_player_id", "string", "Shooter.", src=S_CV + "; PBP", lic=L_US, asof=A_PASS, req=["R-MB-01"], null=True),
      C("shot_id", "string", "FK shots.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-EV-07"], null=True),
      C("points_cv", "int", "2 or 3 from the shooter's last floor contact vs the arc (6.75 m; 6.60 m corners; Rule 1-7.1, 5-1.5).", unit="points", rng=[2, 3], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-IV-12", "R-MB-04"], null=True),
      C("points_board", "int", "Score change on the board.", unit="points", rng=[1, 3], src=S_OCR, lic=L_US, asof=A_FRAME, req=["R-MB-04"], null=True),
      C("points_pbp", "int", "PBP score value.", unit="points", rng=[1, 3], src=S_PBP, lic=L_ROW, asof=A_POST, req=["R-MB-04"], null=True),
      *CUE(1, "ball passes downward through the rim cylinder", S_CV, ["R-MB-01"]),
      *CUE(2, "net moves sharply and the ball is seen in or below the net", S_CV, ["R-MB-01"]),
      *CUE(3, "board score changes inside the lag window", S_OCR, ["R-MB-01", "R-SB-03"]),
      C("cue3_lag_s", "float", "Board change minus make time.", unit="s", rng=[-5, 120], src=S_DER, lic=L_US, asof=A_FRAME, req=["R-SB-03"], null=True),
      *CUE(4, "PBP made shot at the matching game-clock second", S_PBP, ["R-MB-01"]),
      C("cue5_clock_stop", "bool", "Context: clock stopped after the make with <= 59.9 s left in period >= 2 (Rule 2-10.12).", src=S_OCR, lic=L_US, asof=A_FRAME, req=["R-MB-01", "R-IV-06"], null=True),
      C("cue5_baseline_inbound", "bool", "Context: the other team inbounds from the end line.", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-MB-01"], null=True),
      C("cue5_crowd_audio_conf", "float", "Context: crowd-audio make cue (never decisive).", unit="0-1", rng=[0, 1], src="audio", lic=L_US, asof=A_FRAME, req=["R-MB-01"], null=True),
      C("decision", "enum", "Outcome of the decision rule.", values=["confirmed", "vision_only", "not_seen_confirmed", "flagged", "rejected"], src="decision rule", lic=L_US, asof=A_PASS, req=["R-MB-01", "R-MB-02", "R-MB-03"]),
      C("edge_case", "enum", "R-MB-05 edge case, or none.",
        values=["none", "goaltending_awarded", "basket_interference_awarded", "basket_interference_cancelled", "waved_off_foul_before_try", "waved_off_offensive_foul", "waved_off_shot_clock",
                "waved_off_period_horn", "ball_stuck_on_rim", "ball_up_through_net", "in_and_out", "tip_in", "putback", "dunk", "alley_oop", "and_one", "review_reversal"],
        src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-MB-05"]),
      C("rim_visible", "bool", "Rim in view at the make frame.", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-MB-03"]),
      C("net_sharp", "bool", "Net region sharp enough (no motion blur) at the frame rate used.", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-MB-03"]),
      C("release_frame", "int", "Shot release frame.", rng=[0, None], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-MB-06"], null=True),
      C("release_game_clock_s", "float", "Game clock at release.", unit="s", rng=[0, 1200], src=S_FUSE, lic=L_US, asof=A_FRAME, req=["R-MB-06"], null=True),
      C("release_shot_clock_s", "float", "Shot clock at release.", unit="s", rng=[0, 30], src=S_FUSE, lic=L_US, asof=A_FRAME, req=["R-MB-06"], null=True),
      C("release_vs_horn", "enum", "Release before the period or shot-clock horn (zeros; Rule 5-7.2.a, 11-1.2, 11-1.3).", values=["before", "after", "not_applicable", "clock_not_visible"],
        src=S_FUSE, lic=L_US, asof=A_FRAME, req=["R-MB-06"]),
      C("and_one_pending", "bool", "Foul on the make: a free throw follows.", src=S_FUSE, lic=L_US, asof=A_PASS, req=["R-MB-05"]),
      C("review_id", "string", "Review that confirmed or changed the make.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-MB-05"], null=True),
      C("score_event_id", "string", "FK score_events.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-SR-02"], null=True),
      C("flag_ids", "list[string]", "Flags raised.", src="pipeline", lic=L_US, asof=A_PASS, req=["R-MB-01", "R-SB-01"]),
      *pbp_lineage(),
      *lineage(),
  ])

# ================================================================ cv_events_unmatched
T(table="cv_events_unmatched",
  grain="one row per CV-detected event that has no matching PBP event (anchored pass), kept forever as its own stream",
  primary_key=["cv_event_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["event_id"], "references": "events.event_id (the same event in the core events table)"},
                {"columns": ["nearest_pbp_event_id"], "references": "events.event_id"}],
  requirements=["R-SR-14", "R-SY-10", "R-EV-09", "R-EV-01"],
  notes=["Every CV event in the blind pass is unmatched by construction; this table is written in the anchored pass, where matching is possible. Blind-pass events live in events with pass = blind.",
         "Never zero rows for a full game without a written reason (R-SR-14 test): the reason goes into the run record."],
  columns=[
      C("cv_event_id", "string", "game_id + 'anchored' + seq.", src="pipeline", lic=L_US, asof="n/a", req=["R-SR-14"]),
      GAME,
      C("event_id", "string", "Same event's row in the core events table.", src="pipeline", lic=L_US, asof=A_FRAME, req=["R-EV-01"]),
      C("event_type", "enum", "Type of event.",
        values=["deflection", "screen", "hand_off", "tip", "box_out", "closeout", "help_rotation", "loose_ball_recovery", "contest", "drive", "pass", "shot_unlogged", "foul_unlogged",
                "turnover_unlogged", "rebound_unlogged", "substitution_unlogged", "timeout_unlogged", "other"], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-14", "R-SY-10"]),
      PERIOD, CLOCK,
      C("video_ts_ms_start", "int", "Event start.", unit="ms", rng=[0, None], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-14"]),
      C("video_ts_ms_end", "int", "Event end.", unit="ms", rng=[0, None], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-14"]),
      C("team", "enum", "Team performing the event.", values=TEAM3_ENUM, src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-14"]),
      C("player_ids", "list[string]", "Players involved (actor first).", src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-14"]),
      C("x_m", "float", "Location x (attacked-rim frame).", unit="m", rng=[-8.62, 8.62], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-EV-01"], null=True),
      C("y_m", "float", "Location y.", unit="m", rng=[-2.6, 28.05], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-EV-01"], null=True),
      C("r_m", "float", "Distance from the attacked rim.", unit="m", rng=[0, 30], src=S_DER, lic=L_US, asof=A_FRAME, req=["R-EV-01"], null=True),
      C("theta_deg", "float", "Angle from the right baseline at the rim centre.", unit="degrees", rng=[0, 360], src=S_DER, lic=L_US, asof=A_FRAME, req=["R-EV-01"], null=True),
      C("confidence", "float", "Detector confidence.", unit="0-1", rng=[0, 1], src=S_CV, lic=L_US, asof=A_FRAME, req=["R-SR-14", "R-MD-09"], gm=True),
      C("nearest_pbp_event_id", "string", "Closest PBP event in game time (for audit).", src=S_PBP, lic=L_ROW, asof=A_POST, req=["R-SY-10"], null=True),
      C("nearest_pbp_dt_s", "float", "Game-clock gap to it.", unit="s", rng=[0, 1200], src=S_DER, lic=L_US, asof=A_POST, req=["R-SY-10"], null=True),
      C("unmatched_reason", "enum", "Why there is no match.",
        values=["type_not_logged_by_pbp", "pbp_missing_event", "outside_time_window", "identity_mismatch", "possible_false_positive", "unknown"], src="matcher", lic=L_US, asof=A_POST, req=["R-SR-14", "R-SY-10"]),
      C("review_status", "enum", "Review state.", values=["not_queued", "queued", "confirmed_real", "false_positive"], src="manual review", lic=L_US, asof=A_REVIEW, req=["R-HR-01"]),
      C("model_version", "string", "Detector versions.", src="pipeline", lic=L_US, asof="n/a", req=["R-MD-09"], gm=True),
      C("created_utc", "timestamp", "Write time.", unit="UTC", src="pipeline", lic=L_US, asof="n/a", req=["R-DQ-04"]),
  ])

# ================================================================ state_corrections (proposed addition)
T(table="state_corrections",
  grain="one row per corrected value of any state table (append-only; raw rows are never edited)",
  primary_key=["correction_id"],
  foreign_keys=[{"columns": ["game_id"], "references": "games.game_id"},
                {"columns": ["flag_id"], "references": "scoreboard_flags.flag_id"}],
  requirements=["R-SR-15", "R-SB-02", "R-HR-05", "R-DQ-04"],
  notes=["Proposed addition (not in the prompt's list): R-SR-15 needs 'corrections in a separate column with reviewer and reason'; one long table keeps every state table's raw columns untouched and gives one audit trail.",
         "Readers apply corrections as an overlay: corrected view = raw row + latest correction per (table, row_key, field)."],
  columns=[
      C("correction_id", "string", "game_id + seq.", src="pipeline", lic=L_US, asof="n/a", req=["R-SR-15"]),
      GAME,
      C("target_table", "enum", "Table corrected.", values=["state_frame", "state_second", "score_events", "foul_state", "free_throws", "timeouts", "reviews", "restarts", "made_basket_events", "cv_events_unmatched"],
        src="review", lic=L_US, asof=A_REVIEW, req=["R-SR-15"]),
      C("target_row_key", "string", "Primary key of the corrected row (JSON for composite keys); for frame ranges the first and last key.", src="review", lic=L_US, asof=A_REVIEW, req=["R-SR-15"]),
      C("target_range_end_key", "string", "Last row key when one correction covers a range of frames or seconds.", src="review", lic=L_US, asof=A_REVIEW, req=["R-SR-15"], null=True),
      C("field", "string", "Column corrected.", src="review", lic=L_US, asof=A_REVIEW, req=["R-SR-15"]),
      C("raw_value", "string", "Value as written (copied for audit).", src="review", lic=L_US, asof=A_REVIEW, req=["R-SR-15"]),
      C("corrected_value", "string", "New value.", src="review", lic=L_US, asof=A_REVIEW, req=["R-SR-15"]),
      C("correction_source", "enum", "Basis of the correction.", values=["manual", "PBP", "OCR", "CV", "official_record"], src="review", lic=L_US, asof=A_REVIEW, req=["R-SR-15"]),
      C("flag_id", "string", "Flag that triggered it.", src="review", lic=L_US, asof=A_REVIEW, req=["R-SB-02"], null=True),
      C("review_answer", "enum", "R-SB-02 answer.", values=["scoreboard_malfunction", "scorebug_lag", "official_correction", "cv_miss", "cv_false_positive", "pbp_error", "unresolved"],
        src="review", lic=L_US, asof=A_REVIEW, req=["R-SB-02"], null=True),
      C("reviewer", "string", "Who.", src="review", lic=L_US, asof=A_REVIEW, req=["R-HR-05"]),
      C("reviewed_utc", "timestamp", "When.", unit="UTC", src="review", lic=L_US, asof=A_REVIEW, req=["R-HR-05"]),
      C("reason", "string", "Why, in words.", src="review", lic=L_US, asof=A_REVIEW, req=["R-SR-15"]),
      C("tool_version", "string", "Review tool version (R-HR-05).", src="review", lic=L_US, asof=A_REVIEW, req=["R-HR-05"]),
      C("supersedes_correction_id", "string", "Earlier correction this one replaces.", src="review", lic=L_US, asof=A_REVIEW, req=["R-SR-15"], null=True),
  ])


# ---------------------------------------------------------------- emit
def clean(d):
    return {k: v for k, v in d.items() if v not in (None, [], False) or k in ("nullable",)}


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


md = []
for t in TABLES:
    names = [c["name"] for c in t["columns"]]
    dupes = {n for n in names if names.count(n) > 1}
    assert not dupes, (t["table"], dupes)
    for k in t["primary_key"]:
        assert k in names, (t["table"], k)
    doc = {
        "table": t["table"],
        "status": "proposed",
        "version": "0.1.0",
        "date": DATE,
        "owner": "prompt 003 W2 item 5 (state record and invariants)",
        "dictionary": "docs/data/dictionary_state.md#" + t["table"],
        "grain": t["grain"],
        "primary_key": t["primary_key"],
        "foreign_keys": t["foreign_keys"],
        "requirements": t["requirements"],
        "storage": "Parquet, processed/<game_id>/<version>/" + t["table"] + ".parquet (private Drive, never the repo; R-EN-07)",
        "notes": t["notes"],
        "legend": LEGEND,
        "columns": [clean(c) for c in t["columns"]],
    }
    out = REPO / "schema" / "tables" / f"{t['table']}.yaml"
    header = (f"# Proposed schema ({DATE}) for table {t['table']}. Status: proposed; the requirements session approves.\n"
              "# Generated from one spec together with docs/data/dictionary_state.md so the two never drift.\n"
              "# Field names of schema/global_metadata.yaml are used unchanged (global_metadata: true);\n"
              "# proposed_global_addition: true marks fields proposed for global_metadata.yaml (see the dated note in the dictionary).\n")
    out.write_text(header + yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=200))
    yaml.safe_load(out.read_text())  # validate

    md.append(f"### {t['table']}\n")
    md.append(f"- **Grain:** {t['grain']}.")
    md.append(f"- **Primary key:** `{', '.join(t['primary_key'])}`")
    fks = "; ".join(f"`{', '.join(f['columns'])}` -> {f['references']}" for f in t["foreign_keys"])
    md.append(f"- **Foreign keys:** {fks}")
    md.append(f"- **Requirements:** {', '.join(t['requirements'])}")
    md.append(f"- **Schema file:** `schema/tables/{t['table']}.yaml` (status: proposed)")
    for n in t["notes"]:
        md.append(f"- {n}")
    md.append("")
    md.append("| Column | Type | Unit | Range / values | Definition | Source | Licence | As-of | Requirement IDs |")
    md.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for c in t["columns"]:
        rng = ""
        if c["values"]:
            rng = ", ".join(c["values"])
        elif c["range"]:
            lo, hi = c["range"]
            rng = f"{lo if lo is not None else '-inf'} to {hi if hi is not None else 'open'}"
        name = f"`{c['name']}`"
        if c["global_metadata"]:
            name += " (G)"
        if c["proposed_global_addition"]:
            name += " (P)"
        if c["nullable"]:
            name += " (null ok)"
        md.append("| " + " | ".join(esc(x) for x in [name, c["type"], c["unit"] or "", rng, c["definition"], c["source"] or "", c["licence"] or "",
                                                     c["as_of"] or "", ", ".join(c["requirements"])]) + " |")
    md.append("")

FRAG.write_text("\n".join(md))
print("tables:", len(TABLES), "columns:", sum(len(t["columns"]) for t in TABLES))
