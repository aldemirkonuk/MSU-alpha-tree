"""Generate the K09 stored-truth table specs: clock_map, state_transitions, state_segments.

K09 (approved 2026-10-18): game state is stored once as typed transitions, per-dimension validity
segments and a piecewise-linear clock map; state_frame and state_second are rebuilt from them.
Design: docs/requirements_review/k09_state_storage_research.md sections 7-9; types and dimensions:
config/state_machine.yaml. Run from the repo root: python tools/specgen/k09_tables/gen_k09.py
"""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
DATE = "2026-10-19"
OWNER = "Mac session (msu-colab), Aldemir's request 19 Oct (clock map and state machine specs)"
LIC_OWN = "computed by us: own (model input allowed; inherits the strictest class of its inputs)"
AS_OF = {
    "IN_GAME": "IN_GAME: known at the instant the row describes (blind pass); usable as an in-game feature from that instant on.",
    "BY_PASS": ("BY_PASS: blind pass = known at the instant (in-game feature allowed); anchored and pbp_only passes = "
                "post_game (they use complete play-by-play), for training and describing past games, never in-game features."),
    "KEY": "KEY: identifier; no as-of restriction.",
}
SRC_DERIVED = {"computed by us": "fold of state_transitions (tools/state/k09_fold.py)"}
SRC_PBP = {"CBBD": "/plays/game rows (playType, period, secondsRemaining, homeScore, awayScore, onFloor, wallclock)",
           "computed by us": "pbp_only fold"}
SRC_OCR = {"computed by us": "scorebug OCR (scoreboard_ocr) and CV"}


def col(type_, definition, *, unit=None, range_=None, nullable=False, sources=None, as_of="BY_PASS", req=(), **extra):
    c = {"type": type_, "unit": unit, "range": range_, "nullable": nullable, "definition": definition,
         "sources": sources or SRC_DERIVED, "licence": LIC_OWN, "as_of": AS_OF[as_of], "requirements": list(req)}
    c.update(extra)
    return c


KEYS = {
    "game_id": col("string", "ESPN game (event) ID, the join key across video, play-by-play, markets and context.",
                   range_="ESPN event ID (digits)", sources={"computed by us": "registry/games.csv game_id"}, as_of="KEY",
                   req=["R-FD-02", "R-MD-01"]),
    "pass": col("enum", "Processing pass: blind (video only), anchored (video plus play-by-play) or pbp_only (no video).",
                range_="blind | anchored | pbp_only", as_of="KEY", req=["R-MD-01", "R-VA-12"]),
    "state_version": col("string", "Version of the state build: content hash of the inputs and config that produced the rows. "
                         "A correction writes a new version; old versions stay readable.",
                         range_="sv-<12 hex>", as_of="KEY", req=["R-MD-01", "N-SY-05"]),
    "video_id": col("string", "Video file ID (video_files.video_id). Null for the pbp_only pass.", nullable=True,
                    as_of="KEY", req=["R-MD-01"]),
}

COMMON = {
    "status": "proposed",
    "version": "0.1.0",
    "date": DATE,
    "owner": OWNER,
    "decision": "K09 hybrid (docs/requirements_review/conflicts_ab.md; k09_state_storage_research.md)",
    "storage": "Parquet, processed/<game_id>/<pass>/<state_version>/<table>.parquet (private, never the repo; R-EN-07)",
}

CLOCK_MAP = {
    "table": "clock_map",
    **COMMON,
    "grain": ("one row per clock (game, shot) per piecewise-linear stretch of one video (or of the pbp_only game-clock "
              "axis) per pass and state_version"),
    "primary_key": ["game_id", "pass", "state_version", "clock", "from_video_ms", "period", "from_gc_ds"],
    "primary_key_note": "Video passes are unique on from_video_ms; pbp_only rows have no video (from_video_ms = -1) and are unique on (period, from_gc_ds).",
    "foreign_keys": [
        {"columns": ["game_id"], "references": "games.game_id"},
        {"columns": ["video_id"], "references": "video_files.video_id"},
        {"columns": ["game_id", "pass", "opened_by_transition_id"], "references": "state_transitions.(game_id, pass, transition_id)"},
    ],
    "requirements": ["R-MD-08", "new-MD-E1", "N-MD-01", "R-SB-03", "R-SY-01", "R-MK-03", "R-MK-16"],
    "notes": [
        "Maps video time to game clock and shot clock, and game clock to UTC, per game, with a stated error. Every timing number and every join to play-by-play or in-game prices goes through it (engineer review 4.7 risk 1).",
        "Integer decisecond arithmetic: value(t) = anchor_ds - rate * (t - from_video_ms) / 100 while running, anchor_ds while stopped. Views reproduce exactly (K09 section 9).",
        "Condensed replays cut stopped time and sometimes running time. A stretch ends at every cut (status cut), so no linear map crosses a cut.",
        "UTC: utc_at_from is set only from sources with a real clock (PBP wallclock after the monotone fix, our own recordings' capture time). CBBD wallclock steps backwards 57-66 times per game (measured 19 Oct), so raw wallclock is never used directly.",
        "Stored truth with state_transitions and state_segments; state_frame and state_second read game_clock_s and shot_clock_s from here.",
    ],
    "columns": {
        **KEYS,
        "clock": col("enum", "Which clock the row maps.", range_="game | shot", as_of="KEY", req=["R-MD-08"]),
        "period": col("int", "Period the stretch belongs to (1-2 regulation, 3+ extra periods).", range_="1..9",
                      sources=SRC_OCR | SRC_PBP, req=["R-SR-01"]),
        "from_video_ms": col("int64", "Start of the stretch in video time (inclusive). -1 for pbp_only rows.", unit="ms",
                             range_="-1 or >= 0", as_of="KEY", req=["R-MD-08"]),
        "to_video_ms": col("int64", "End of the stretch in video time (exclusive). -1 for pbp_only rows.", unit="ms",
                           range_="-1 or > from_video_ms", req=["R-MD-08"]),
        "from_gc_ds": col("int32", "Game clock at the start of the stretch, deciseconds remaining in the period.", unit="ds",
                          range_="0..12000", req=["R-MD-08"]),
        "to_gc_ds": col("int32", "Game clock at the end of the stretch, deciseconds remaining in the period.", unit="ds",
                        range_="0..12000", req=["R-MD-08"]),
        "anchor_ds": col("int32", "Clock value at from_video_ms (game clock remaining, or shot clock), deciseconds.", unit="ds",
                         range_="0..12000 (game), 0..300 (shot)", sources=SRC_OCR, req=["R-MD-08"]),
        "running": col("bool", "True when the clock runs through the stretch at rate 1.0.", sources=SRC_OCR, req=["R-MD-08"]),
        "status": col("enum", "Stretch class: running (clock and video advance together), stopped (video advances, clock does not), "
                      "cut (the video skips game time; no map across it), off (shot clock off, 2-11.2), unknown (no anchors).",
                      range_="running | stopped | cut | off | unknown", sources=SRC_OCR, req=["R-MD-08", "R-SB-03"]),
        "rate": col("float32", "Clock seconds per video second inside the stretch: 1.0 running, 0.0 stopped. Stored measured value; CLK-02 checks it.",
                    unit="s/s", range_="0..1.05", sources=SRC_OCR, req=["R-MD-08"]),
        "n_anchors": col("int16", "Number of OCR or PBP anchors inside the stretch.", unit="count", range_=">= 0", req=["R-MD-08"]),
        "err_ds": col("int16", "Stated error of the mapped value inside the stretch (95% bound), deciseconds.", unit="ds",
                      range_=">= 0", req=["R-MD-08", "R-SY-01"]),
        "utc_at_from": col("timestamp[us, UTC]", "UTC at the start of the stretch, from a monotone-fixed real clock; null when no source.",
                           unit="UTC", nullable=True, sources=SRC_PBP, req=["R-MK-03", "R-MK-16"]),
        "utc_err_s": col("float32", "95% error of utc_at_from.", unit="s", range_=">= 0", nullable=True, req=["R-MK-16"]),
        "src": col("enum", "Source of the anchors.", range_="ocr | pbp | cv | manual | interpolated", req=["R-MD-19"]),
        "conf": col("float32", "Confidence 0-1 of the stretch class and values.", range_="0..1", req=["R-MD-09"]),
        "dq": col("enum", "Data-quality flag (R-MD-19).", range_="observed | inferred | carried | imputed | quarantined", req=["R-MD-19"]),
        "opened_by_transition_id": col("string", "Transition that opened the stretch (clock start or stop, period start, correction); null for a cut or an anchor-only boundary.",
                                       nullable=True, req=["N-SY-01"]),
    },
}

STATE_TRANSITIONS = {
    "table": "state_transitions",
    **COMMON,
    "grain": "one row per typed game-state change per game, pass and state_version (append-only)",
    "primary_key": ["game_id", "pass", "transition_id"],
    "foreign_keys": [
        {"columns": ["game_id"], "references": "games.game_id"},
        {"columns": ["video_id", "effective_frame"], "references": "frames.(video_id, frame_index)"},
        {"columns": ["game_id", "pass", "supersedes_id"], "references": "state_transitions.(game_id, pass, transition_id)"},
        {"columns": ["source_event_id"], "references": "events.event_id (or the PBP row id for pbp_only)"},
    ],
    "requirements": ["N-SY-01", "N-SY-05", "R-MD-01", "N-MD-01", "N-MD-02", "R-SR-01..15", "R-IV-01..16", "N-IV-01", "R-SB-03"],
    "notes": [
        "Types, allowed flow-state moves and the dimensions each type may change: config/state_machine.yaml (T01-T25). An untyped row, or a row that changes a dimension its type does not list, is an invariant break (TRN-01, TRN-02).",
        "Append-only. A data correction writes a new row with supersedes_id and a new state_version; the superseded row stays readable (TRN-05). An officials' correction during the game is its own type, T18.",
        "Effective vs observed: effective_frame is when the change happened on court; observed_frame_* is when each sensor saw it, so scorebug lag is stored, not hidden (engineer review T05: median 1.933 s).",
        "changes holds the new value of every dimension the row changes, team-neutral (home/away, N-MD-02). Segment rows are folded from it.",
        "Replay frames never open a transition (TRN-04).",
        "About 1,400 rows per game per video pass (K09 benchmark); the pbp_only pass writes about 900-1,000 (measured on the two pilot games).",
    ],
    "columns": {
        **KEYS,
        "transition_id": col("string", "Deterministic ID: hash of (game_id, pass, ttype, period, game_clock_ds, order_index, source_event_id). The same inputs always give the same ID (new-EN-E3).",
                             range_="tr-<16 hex>", as_of="KEY", req=["N-SY-01", "new-EN-E3"]),
        "ttype": col("enum", "Transition type from config/state_machine.yaml.", range_="T01..T25", req=["N-SY-01"]),
        "subtype": col("string", "Subtype from the type's subtypes list (e.g. T16 to30, T05 three).", nullable=True, req=["N-SY-01"]),
        "effective_frame": col("int32", "Frame of the change on court. Null for pbp_only.", unit="frame", range_=">= 0",
                               nullable=True, req=["N-SY-01"]),
        "order_index": col("int16", "Order among transitions at the same instant (frame or game clock).", unit="count",
                           range_=">= 0", req=["N-SY-01"]),
        "observed_frame_ocr": col("int32", "Frame at which the scorebug showed the change; null if not shown.", unit="frame",
                                  nullable=True, sources=SRC_OCR, req=["R-SB-03"]),
        "observed_frame_pbp": col("int32", "Frame matched to the PBP row (anchored pass); null otherwise.", unit="frame",
                                  nullable=True, req=["R-SY-04"]),
        "observed_frame_cv": col("int32", "Frame at which CV detected the trigger; null if not detected.", unit="frame",
                                 nullable=True, req=["R-DT-01"]),
        "video_ts_ms": col("int64", "Video time of effective_frame. Null for pbp_only.", unit="ms", nullable=True, req=["R-MD-01"]),
        "period": col("int8", "Period of the change.", range_="1..9", sources=SRC_PBP | SRC_OCR, req=["R-SR-01"]),
        "game_clock_ds": col("int32", "Game clock remaining at the change, deciseconds.", unit="ds", range_="0..12000",
                             sources=SRC_PBP | SRC_OCR, req=["R-SR-01", "R-MD-08"]),
        "shot_clock_ds": col("int16", "Shot clock at the change, deciseconds; null when off or unknown.", unit="ds",
                             range_="0..300", nullable=True, sources=SRC_OCR, req=["R-MD-06"]),
        "shot_clock_status": col("enum", "Shot clock status at the change.", range_="running | stopped | off | unknown",
                                 sources=SRC_OCR, req=["R-MD-06"]),
        "est_utc": col("timestamp[us, UTC]", "Estimated UTC of the change (through clock_map); null if unknown.", unit="UTC",
                       nullable=True, sources=SRC_PBP, req=["R-MK-16"]),
        "est_utc_err_s": col("float32", "95% error of est_utc.", unit="s", nullable=True, req=["R-MK-16"]),
        "flow_from": col("enum", "Flow state before the change.", range_="S0..S11, S4a, S4b, S4c, unknown", req=["N-SY-01", "new-SR-A6"]),
        "flow_to": col("enum", "Flow state after the change.", range_="S0..S11, S4a, S4b, S4c, final, unknown", req=["N-SY-01"]),
        "team": col("enum", "Team the transition is credited to (team-neutral).", range_="home | away | none", req=["N-MD-02"]),
        "player_ids": col("list<string>", "Players involved (shooter, fouler, substitutes in and out).", nullable=True,
                          sources=SRC_PBP, req=["R-EV-01"]),
        "rule_ref": col("string", "Rule reference of the type (copied from config/state_machine.yaml at write time).", req=["N-SY-01"]),
        "changes": col("map<string, string>", "New value of each changed dimension (dimension name -> value string).",
                       req=["N-SY-01", "N-MD-01"]),
        "sources": col("list<enum>", "Sensors that observed the change.", range_="ocr | pbp | cv | audio | manual", req=["N-SY-01"]),
        "source_event_id": col("string", "Source row: PBP play id (CBBD id) or events.event_id.", nullable=True, sources=SRC_PBP,
                               req=["R-SY-04"]),
        "conf": col("float32", "Confidence 0-1 of the type and time.", range_="0..1", req=["R-MD-09"]),
        "dq": col("enum", "Data-quality flag.", range_="observed | inferred | carried | imputed | quarantined", req=["R-MD-19"]),
        "known_at_utc": col("timestamp[us, UTC]", "When this row could have been known (blind pass: est_utc plus processing; anchored/pbp_only: the PBP pull time). Used by the leakage test (N-MD-04).",
                            unit="UTC", req=["N-MD-04", "R-VA-12"]),
        "supersedes_id": col("string", "transition_id this row corrects; null for originals.", nullable=True, req=["N-SY-05"]),
        "correction_id": col("string", "state_corrections row that caused the supersession; null for originals.", nullable=True,
                             req=["N-SY-05"]),
    },
}

STATE_SEGMENTS = {
    "table": "state_segments",
    **COMMON,
    "grain": "one row per game-state dimension per validity interval [from, to) per game, pass and state_version",
    "primary_key": ["game_id", "pass", "state_version", "dimension", "dim_key", "from_period", "from_gc_ds", "from_order"],
    "primary_key_note": ("Video passes also carry from_frame/to_frame (a unique alternative key with dimension and dim_key); "
                         "pbp_only rows key on game clock only. dim_key is '' except for family dimensions (player_fouls: player_id)."),
    "foreign_keys": [
        {"columns": ["game_id"], "references": "games.game_id"},
        {"columns": ["game_id", "pass", "opened_by_transition_id"], "references": "state_transitions.(game_id, pass, transition_id)"},
        {"columns": ["correction_id"], "references": "state_corrections.correction_id"},
    ],
    "requirements": ["N-MD-01", "N-MD-02", "R-MD-01", "R-SR-06", "N-IV-01", "N-SY-05", "R-MD-19"],
    "notes": [
        "The only stored copy of game state (with clock_map). state_frame and state_second are as-of joins of this table, regenerated after any change, never edited (R-MD-01 rewrite).",
        "Dimensions and their value types: config/state_machine.yaml dimensions (stored: segment). Derived dimensions (bonus) are never stored.",
        "Per-frame observations (ball x/y/height, player positions, detections) are never segments; they stay in ball_states, player_positions, detections (R-SR-06).",
        "Integrity SEG-01..04: no overlap, no gap, no zero-length segment, every boundary opened by exactly one transition.",
        "Ordering inside one game-clock instant: from_order is the order_index of the opening transition, so segments are totally ordered by (from_period, -from_gc_ds, from_order).",
        "The last segment of each dimension ends at the end of the covered range (to_* = end of the game or video).",
    ],
    "columns": {
        **KEYS,
        "dimension": col("enum", "Dimension name from config/state_machine.yaml.", as_of="KEY", req=["N-MD-01"]),
        "dim_key": col("string", "Key inside a family dimension (player_id for player_fouls); '' otherwise.", as_of="KEY", req=["N-MD-01"]),
        "value": col("string", "Value as a string, parsed per value_type.", req=["N-MD-01"]),
        "value_type": col("enum", "Parse of value.", range_="int | enum | bool | list | float", req=["N-MD-01"]),
        "from_frame": col("int32", "First frame of the interval (inclusive). Null for pbp_only.", unit="frame", nullable=True, req=["N-MD-01"]),
        "to_frame": col("int32", "End frame (exclusive). Null for pbp_only.", unit="frame", nullable=True, req=["N-MD-01"]),
        "from_period": col("int8", "Period at the start of the interval.", range_="0..9", req=["N-MD-01"]),
        "from_gc_ds": col("int32", "Game clock at the start, deciseconds remaining.", unit="ds", range_="0..12000", req=["N-MD-01"]),
        "from_order": col("int16", "order_index of the opening transition at that instant.", range_=">= 0", req=["N-MD-01"]),
        "to_period": col("int8", "Period at the end of the interval.", range_="0..9", req=["N-MD-01"]),
        "to_gc_ds": col("int32", "Game clock at the end, deciseconds remaining.", unit="ds", range_="0..12000", req=["N-MD-01"]),
        "to_order": col("int16", "order_index of the closing transition (the next segment's from_order).", range_=">= 0", req=["N-MD-01"]),
        "src": col("enum", "Source of the value.", range_="ocr | pbp | cv | manual | rule", req=["R-MD-19"]),
        "conf": col("float32", "Confidence 0-1.", range_="0..1", req=["R-MD-09"]),
        "dq": col("enum", "Data-quality flag.", range_="observed | inferred | carried | imputed | quarantined", req=["R-MD-19"]),
        "opened_by_transition_id": col("string", "Transition that opened the interval (SEG-04).", req=["N-SY-01", "N-IV-01"]),
        "correction_id": col("string", "Correction that produced this interval; null for originals.", nullable=True, req=["N-SY-05"]),
    },
}


def write(spec):
    out = ROOT / "schema" / "tables" / f"{spec['table']}.yaml"
    header = (f"# Proposed schema ({DATE}) for table {spec['table']}. Status: proposed; the requirements session approves.\n"
              "# K09 stored truth (hybrid): state_transitions + state_segments + clock_map. Generated by\n"
              "# tools/specgen/k09_tables/gen_k09.py; types and dimensions in config/state_machine.yaml.\n")
    out.write_text(header + yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=200))
    return out


if __name__ == "__main__":
    for s in (CLOCK_MAP, STATE_TRANSITIONS, STATE_SEGMENTS):
        print(write(s))
