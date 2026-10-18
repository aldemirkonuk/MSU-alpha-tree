"""Shared helpers for the W2 core data dictionary generator (scratchpad only, not repo code)."""
from __future__ import annotations

SRC = {
    "C": "CBBD",
    "E": "ESPN files already pulled",
    "HE": "hoopR ESPN releases",
    "HN": "hoopR NCAA engine",
    "T": "Torvik",
    "K": "KenPom",
    "KG": "Kaggle archive",
    "EM": "EvanMiya exports",
    "MK": "markets collector",
    "O": "computed by us",
    "M": "manual (Aldemir)",
    "R": "rulebook / config",
}

# Licence class per source (docs/research/data_sources_catalog.md, R-DS-02, R-DS-10, R-DS-14, R-RG-11).
LIC = {
    "C": "model input allowed",
    "HE": "model input allowed (hoopR release; R-DS-02 allowed channel)",
    "HN": "model input allowed (hoopR release)",
    "E": "reference only (ESPN direct; R-DS-02)",
    "T": "model input allowed, provisional (no Torvik terms page found; Aldemir to confirm)",
    "K": "blocked until the KenPom API is bought (R-DS-14); then model input allowed",
    "KG": "reference only until the archive licence is checked (contains KenPom/Torvik-derived columns)",
    "EM": "reference only (EvanMiya terms: no redistribution; R-DS-10)",
    "MK": "per source, docs/markets/collector_design.md section 6",
    "O": "own (model input allowed; inherits the strictest class of its inputs)",
    "M": "private (Aldemir's input; R-RG-06)",
    "R": "own (public rule text)",
}

ASOF = {
    "STATIC": "Entity attribute versioned by valid_from/valid_to; a model for a game at tip T uses the version with valid_from <= T.",
    "PRE_TIP": "Known before tip (schedule, venue, assignment); usable pre-game once its known_at_utc is before the cutoff (R-CX-09).",
    "SNAPSHOT": "Carries its own as-of time; usable only when that time is before the cutoff (tip minus horizon; R-CX-09, R-MK-07, R-PC-14).",
    "DAY_BEFORE": "Value as of the US-Eastern day before tip (R-FD-06, R-DS-04); missing -> nearest earlier snapshot, flagged with its date.",
    "IN_GAME": "Known at in-game instant t (video_ts_ms / game clock); live models may use it from t on; pre-game models only as aggregates of earlier games.",
    "POST_GAME": "Known only after the final horn; a feature only for games that tip after this game ended (R-FD-07).",
    "RUN": "Run or audit metadata; never a model feature.",
    "LABEL": "Human label; gold or training target, never an inference-time input (R-HR-07).",
}


def C(name, typ, unit, rng, null, defn, src=None, req=None, lic=None, asof=None, vocab=None):
    return {
        "name": name, "type": typ, "unit": unit, "range": rng, "nullable": null,
        "definition": defn, "src": src or {"O": "computed"}, "req": req, "lic": lic,
        "asof": asof, "vocab": vocab,
    }


def T(name, group, grain, pk, cols, reqs, asof, fks=None, notes=None, stamps=False, prov=True,
      storage="private: MyDrive/MSU-Alpha-3/processed/<game_id>/<version>/<table>.parquet (R-EN-07)",
      view_of=None, filter_=None):
    return {
        "name": name, "group": group, "grain": grain, "pk": pk, "cols": cols, "reqs": reqs,
        "asof": asof, "fks": fks or [], "notes": notes or [], "stamps": stamps, "prov": prov,
        "storage": storage, "view_of": view_of, "filter": filter_,
    }


# ---------- common columns ----------

def game_id(req=None):
    return C("game_id", "string", None, "ESPN event ID (digits)", False,
             "ESPN game (event) ID, the one join key across video, play-by-play, markets and context.",
             {"E": "header.id / event.id", "HE": "game_id", "HN": "espn_game_id",
              "C": "games.sourceId (ESPN event ID per collector_design.md 1.1; verify on first keyed call)",
              "T": "via hoopR mbb_schedule_crosswalk.bart_muid", "K": "via mbb_schedule_crosswalk.kp_game_id",
              "MK": "SnapshotRow.game_id", "O": "registry/games.csv game_id"},
             req or ["R-FD-02"])


def team_id(name="team_id", defn="ESPN team ID of the team this row belongs to.", null=False, req=None):
    return C(name, "string", None, "ESPN team ID (digits); MSU = 127", null, defn,
             {"E": "team.id", "HE": "team_id / home_team_id / away_team_id", "HN": "*_espn_team_id",
              "C": "teamId -> teams.sourceId (ESPN team ID)", "T": "team name via hoopR mbb_team_crosswalk.bart_team",
              "K": "team name via mbb_team_crosswalk.kp_team", "KG": "TEAM / TeamName via crosswalk",
              "EM": "team via crosswalk", "O": "id_crosswalk"},
             req or ["R-FD-02", "R-DS-05"])


def player_id(name="player_id", defn="ESPN athlete ID; local ID 'x-<team_id>-<season>-<n>' when ESPN has none.", null=False, req=None):
    return C(name, "string", None, "ESPN athlete ID or local x- ID", null, defn,
             {"E": "athlete.id / participants[].athlete.id", "HE": "athlete_id_1 / participants_0_athlete_id",
              "HN": "player_*_id via mbb_player_crosswalk", "C": "athleteId -> players.sourceId (assumed ESPN, verify)",
              "O": "identity pipeline (track -> player)"},
             req or ["R-FD-03", "R-PC-01", "new-DS-1"])


def season(req=None):
    return C("season", "int16", "year", "[2003, 2035]", False,
             "Season named by its ending year (2026 = 2025-26), as ESPN and CBBD do.",
             {"E": "season.year", "HE": "season", "HN": "season", "C": "season", "T": "year in file name",
              "K": "Season", "KG": "YEAR / Season"}, req or ["R-FD-01"])


def period(req=None):
    return C("period", "int8", None, "[1, 9]", False,
             "Period number: 1 = first half, 2 = second half, 3+ = overtime 1, 2, ...",
             {"E": "period.number", "HE": "period_number", "HN": "period (halves; quarters only in non-men data)",
              "C": "period", "O": "scoreboard OCR"}, req or ["R-MD-01", "R-IV-16"])


def game_clock(name="game_clock_s", defn="Game clock: seconds remaining in the period.", null=False, req=None):
    return C(name, "float32", "s", "[0, 1200] halves; [0, 300] overtime", null, defn,
             {"E": "clock.displayValue (mm:ss -> s)", "HE": "start_quarter_seconds_remaining / clock_display_value",
              "HN": "clock (mm:ss) / sec_left", "C": "secondsRemaining (integer s) / clock", "O": "scoreboard OCR, R-MD-08 map"},
             req or ["R-MD-01", "R-DQ-02", "R-SR-01"])


def shot_clock(name="shot_clock_s", null=True, req=None):
    return C(name, "float32", "s", "[0, 30]", null,
             "Shot clock reading in seconds; null only when shot_clock_state = off (R-MD-01 explicit off).",
             {"O": "scoreboard OCR (state_frame) or reconstructed per R-MD-06"}, req or ["R-MD-01", "R-MD-06", "R-DQ-02"])


def video_ts(name="video_ts_ms", null=False, defn="Milliseconds from the first frame's presentation time in the original file (original PTS kept for VFR, R-VI-12).", req=None):
    return C(name, "int64", "ms", "[0, 3.6e7]", null, defn, {"O": "decoder PTS"}, req or ["R-MD-01", "R-VI-12"])


def frame_index(name="frame_index", null=False, req=None):
    return C(name, "int32", None, "[0, 2.2e6]", null,
             "0-based index of the decoded frame in the original file.", {"O": "decoder"}, req or ["R-MD-01"])


def video_sha(null=False):
    return C("video_id", "string", None, "64 hex chars", null,
             "Video file ID = SHA-256 of the original file (one game can have several files; same key as video_id in the state-record tables) (R-FD-09).", {"O": "hash of the Drive file"},
             ["R-FD-09", "R-VI-09"])


def possession_id(null=True, req=None):
    return C("possession_id", "int32", None, "[1, 200] per game", null,
             "Possession number within the game under OUR rule: a possession ends only when the other team gains control.",
             {"O": "possessions table", "HN": "poss_num (source definition, kept in possessions.poss_num_ncaa)"},
             req or ["R-MD-04", "R-SY-04"])


def chance_id(null=True, req=None):
    return C("chance_id", "int32", None, "[1, 300] per game", null,
             "Chance number within the game; a new chance starts at each offensive rebound or shot-clock reset inside a possession.",
             {"O": "chances table"}, req or ["R-MD-04", "R-SY-05"])


def run_id(null=False):
    return C("run_id", "string", None, "'<UTC yyyymmddThhmmssZ>-<task_id>'", null,
             "Pipeline run that produced the row (run_records).", {"O": "runner"}, ["R-RR-01", "R-EN-04"])


def utc(name, defn, null=False, req=None, src=None, asof=None):
    return C(name, "timestamp[us, UTC]", "UTC", "2000-01-01 .. 2040-01-01", null, defn, src, req or ["R-MK-25"], asof=asof)


def conf(name="confidence", defn="Model or source confidence for this value.", null=False, req=None):
    return C(name, "float32", None, "[0, 1]", null, defn, {"O": "model output; official data = 1.0"}, req or ["R-MD-09"])


PROV = [
    C("source", "enum[cbbd, espn, hoopr_espn, hoopr_ncaa, torvik, kenpom, kaggle, evanmiya, markets, cv, ocr, audio, pbp_fused, manual, rules, computed]",
      None, "enum", False, "Source that produced this row (every value carries its source, R-MD-09; any source can be swapped later).",
      {"O": "set by the loader or pipeline"}, ["R-MD-09", "R-SR-15", "R-DS-10"], asof="RUN"),
    C("source_ref", "string", None, "'<raw sha256>#<json pointer or row number>'", True,
      "Pointer to the raw pull or upstream rows this row came from (lineage).", {"O": "raw store manifest"},
      ["R-DQ-04", "R-DQ-05"], asof="RUN"),
    utc("pulled_at_utc", "UTC time the raw source was pulled, or the time the row was computed.", req=["R-DQ-05", "R-MK-25"], asof="RUN"),
    C("transform_version", "string", None, "git commit (7-40 hex) + transform name", False,
      "Code version that produced the row.", {"O": "git"}, ["R-DQ-04", "R-EN-04", "R-RR-01"], asof="RUN"),
    C("model_version", "string", None, "free text, e.g. 'det-yolo11x@a1b2c3'", True,
      "Model version for model outputs; null for loaded official data.", {"O": "model registry"}, ["R-MD-09", "R-EN-04"], asof="RUN"),
    C("confidence", "float32", None, "[0, 1]", False, "Confidence of the row's main value; official data carries 1.0.",
      {"O": "model output or 1.0"}, ["R-MD-09"], asof="RUN"),
    C("dq_flag", "enum[observed, inferred, carried, imputed, quarantined]", None, "enum", False,
      "Data-quality flag of the row's main value.", {"O": "pipeline"}, ["R-MD-19", "R-DQ-03"], asof="RUN"),
    C("pass", "enum[blind, anchored, none]", None, "enum", False,
      "Blind = produced without play-by-play; anchored = play-by-play used; none = not a vision output.",
      {"O": "pipeline"}, ["R-SR-13", "R-SR-15"], asof="RUN"),
    C("licence_class", "enum[model_input_allowed, reference_only, blocked, own, private]", None, "enum", False,
      "Licence class of this row, from its source (data_sources_catalog.md); reference_only and blocked rows never reach a model.",
      {"O": "from source"}, ["R-DS-10", "R-RG-04", "R-RG-11"], asof="RUN"),
    C("schema_version", "int16", None, "[1, 999]", False, "Version of this table's schema at write time.",
      {"O": "schema/tables/<table>.yaml"}, ["R-EN-01", "R-MK-31"], asof="RUN"),
]


ZONE_VOCAB = "geometry.spot() labels (src/msu_alpha/geometry.py): restricted_area, paint, mid_range_{left,right}, corner_three_{left,right}, wing_three_{left,right}, slot_three_{left,right}, top_three"


def pos(prefix="", req=None, null=True, what="the player", src=None):
    p = prefix
    r = req or ["R-CG-05", "R-EV-01", "R-CG-08"]
    s = src or {"O": "court mapping (geometry.describe)"}
    return [
        C(f"{p}x_m", "float32", "m", "[-8.62, 8.62] (court half-width 7.62 m +- 1 m, R-DQ-02)", null, f"x of {what} in the attacked-rim frame (origin under the attacked rim centre, x along the baseline, + to the attacker's right), stored to 1 cm.", s, r),
        C(f"{p}y_m", "float32", "m", "[-2.60, 28.05]", null, f"y of {what} (from the baseline toward half-court; rim centre at y = 0, baseline at y = -1.60).", s, r),
        C(f"{p}r_m", "float32", "m", "[0, 30]", null, f"Distance of {what} from the attacked rim centre, sqrt(x^2 + y^2).", s, r),
        C(f"{p}theta_deg", "float32", "degrees", "[-180, 180]; on court in front of the rim [0, 180]", null, f"Angle of {what} from the right baseline at the rim centre, atan2(y, x).", s, r + ["R-CG-02"]),
        C(f"{p}spot", "string", None, "geometry.spot() label", null, f"Named spot of {what}.", s, r, vocab=ZONE_VOCAB),
        C(f"{p}sector_15deg", "int8", None, "[0, 11]", null, f"15-degree angle sector index of {what} (geometry.sector).", s, r),
        C(f"{p}ring_0p5m", "int8", None, "[0, 60]", null, f"0.5 m distance-ring index of {what} (geometry.ring).", s, r),
    ]


def ts_block(prefix="", null=False, req=None):
    p = prefix
    return [
        video_ts(f"{p}video_ts_ms", null=null, req=req),
        frame_index(f"{p}frame_index", null=True, req=req),
        C(f"{p}period", "int8", None, "[1, 9]", null, "Period (1, 2 halves; 3+ overtime).", {"E": "period.number", "HE": "period_number", "HN": "period", "C": "period", "O": "state_frame"}, req or ["R-MD-01"]),
        game_clock(f"{p}game_clock_s", null=null, req=req),
        shot_clock(f"{p}shot_clock_s", req=req),
    ]
