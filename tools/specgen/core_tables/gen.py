"""Render the W2 core data dictionary (markdown) and schema/tables/*.yaml proposals."""
from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from common import ASOF, LIC, PROV, SRC  # noqa: E402
import spec_registry, spec_pbp, spec_cv, spec_actions, spec_ops, spec_extra  # noqa: E402

REPO = Path("/Users/aldemirkonuk/Projects/MSU-Alpha-3")
SCR = Path(__file__).parent
REQ_FILE = SCR.parent / "live_doc" / "requirement_ids.md"
OUT_YAML = Path(sys.argv[1]) if len(sys.argv) > 1 else SCR / "out" / "schema" / "tables"
OUT_MD = Path(sys.argv[2]) if len(sys.argv) > 2 else SCR / "out" / "dictionary_games.md"

TABLES = spec_registry.TABLES + spec_pbp.TABLES + spec_cv.TABLES + spec_actions.TABLES + spec_ops.TABLES + spec_extra.TABLES
EXTERNAL = ["C", "E", "HE", "HN", "T", "K", "KG", "EM"]
SHORT = {"C": "MI", "HE": "MI", "HN": "MI", "T": "MI*", "K": "BL", "KG": "RO*", "EM": "RO", "E": "RO", "MK": "MK", "O": "OWN", "M": "PRIV", "R": "OWN"}
STATE_TABLES = ["free_throws", "timeouts", "reviews", "restarts", "foul_state", "score_events", "state_frame", "state_second",
                "scoreboard_ocr", "scoreboard_flags", "made_basket_events", "cv_events_unmatched"]

known = set(re.findall(r"^- (R-[A-Z]{2}-\d{2}) ", REQ_FILE.read_text(), re.M))
used, unknown, newids = set(), set(), set()


def check_reqs(reqs):
    for r in reqs:
        if r.startswith("new-"):
            newids.add(r)
        elif r in known:
            used.add(r)
        else:
            unknown.add(r)


def lic_text(src, override=None):
    if override:
        return override
    classes = {}
    for k in src:
        classes.setdefault(LIC[k], []).append(SRC[k])
    return "; ".join(f"{', '.join(v)}: {c}" for c, v in classes.items())


def lic_short(src):
    groups = {}
    for k in src:
        groups.setdefault(SHORT[k], []).append(k)
    return "; ".join(f"{c} ({','.join(v)})" for c, v in groups.items())


def full_cols(t):
    cols = list(t["cols"])
    if t["prov"] and not t["view_of"]:
        names = {c["name"] for c in cols}
        cols += [copy.deepcopy(c) for c in PROV if c["name"] not in names]
    return cols


def yaml_for(t):
    cols = full_cols(t)
    d = {
        "name": t["name"], "status": "proposed",
        "proposed_by": "W2 core-tables agent, prompt 003 (2026-10-18); approval by the requirements session",
        "group": t["group"], "grain": t["grain"], "primary_key": t["pk"],
        "foreign_keys": [{"columns": [c.strip() for c in f[0].split(",")], "references": f[1]} for f in t["fks"]],
        "storage": t["storage"],
        "as_of_default": {"rule": t["asof"], "text": ASOF[t["asof"]]},
        "requirements": t["reqs"],
    }
    if t["stamps"]:
        d["stamps"] = {"file": "schema/global_metadata.yaml", "fields": "all", "requirement": "R-MD-01",
                       "note": "Every row also carries every global_metadata field; columns named here take precedence."}
    if t["view_of"]:
        d["view_of"] = t["view_of"]
        d["filter"] = t["filter"]
        d["columns_ref"] = "identical to market_snapshots (SnapshotRow in src/msu_alpha/markets/models.py)"
    if t["notes"]:
        d["notes"] = t["notes"]
    d["columns"] = {}
    for c in cols:
        check_reqs(c["req"] or t["reqs"])
        src = c["src"]
        sources = {SRC[k]: "none" for k in EXTERNAL}
        for k, v in src.items():
            sources[SRC[k]] = v if v else "see definition"
        asof = c["asof"] or t["asof"]
        e = {"type": c["type"], "unit": c["unit"], "range": c["range"], "nullable": c["nullable"],
             "definition": c["definition"], "sources": sources, "licence": lic_text(src, c["lic"]),
             "as_of": f"{asof}: {ASOF[asof]}", "requirements": c["req"] or t["reqs"]}
        if c["vocab"]:
            e["vocabulary"] = c["vocab"]
        d["columns"][c["name"]] = e
    check_reqs(t["reqs"])
    return d


def md_esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ") if s is not None else ""


COMMON_MD = {"game_id": "join key, see 2.1", "season": "E/HE/HN/C season; T file year; K Season; KG YEAR", "team_id": "ESPN team ID; other sources via id_crosswalk (2.1)", "player_id": "ESPN athlete ID; others via id_crosswalk (2.1)", "video_id": "hash of the original file", "run_id": "runner"}
PROV_NAMES = {c["name"] for c in PROV}


def md_table(t):
    cols = [c for c in full_cols(t) if not (t["prov"] and c["name"] in PROV_NAMES and c in PROV)]
    cols = [c for c in full_cols(t) if not (t["prov"] and not t["view_of"] and c["name"] in PROV_NAMES)] or cols
    out = [f"### `{t['name']}`", ""]
    out.append(f"- **Grain:** {t['grain']}")
    out.append(f"- **Primary key:** {', '.join('`'+k+'`' for k in t['pk'])}")
    if t["fks"]:
        out.append("- **Foreign keys:** " + "; ".join(f"`{f[0]}` -> `{f[1]}`" for f in t["fks"]))
    out.append(f"- **As-of (default):** `{t['asof']}`. {ASOF[t['asof']]}")
    out.append(f"- **Storage:** {t['storage']}")
    out.append(f"- **Requirements:** {', '.join(t['reqs'])}")
    if t["stamps"]:
        out.append("- **Stamps:** every row also carries all fields of `schema/global_metadata.yaml` (R-MD-01).")
    if t["view_of"]:
        out.append(f"- **View of:** `{t['view_of']}` where {t['filter']}. Columns: identical to `market_snapshots`.")
    for n in t["notes"]:
        out.append(f"- {n}")
    if t["prov"] and not t["view_of"]:
        out.append("- **Plus** the provenance block of section 2.7 (`source`, `source_ref`, `pulled_at_utc`, `transform_version`, `model_version`, `confidence`, `dq_flag`, `pass`, `licence_class`, `schema_version`); it is listed in full in the YAML file.")
    out.append(f"- **Schema file:** `schema/tables/{t['name']}.yaml`")
    out.append("")
    if cols:
        out.append("| Column | Type | Unit | Range | Null | Definition | Sources | Licence | As-of | Req |")
        out.append("|---|---|---|---|---|---|---|---|---|---|")
        for c in cols:
            src = "; ".join(f"{k}: {v}" if v else k for k, v in c["src"].items())
            if c["name"] in COMMON_MD and len(c["src"]) > 2:
                src = COMMON_MD[c["name"]]
            defn = c["definition"] + (f" Vocabulary: {c['vocab']}." if c["vocab"] else "")
            out.append("| " + " | ".join(md_esc(x) for x in [
                f"`{c['name']}`", c["type"], c["unit"] or "-", c["range"], "yes" if c["nullable"] else "no", defn, src,
                lic_short(c["src"]) if not c["lic"] else c["lic"], c["asof"] or t["asof"], ", ".join(c["req"] or t["reqs"])]) + " |")
        out.append("")
    return "\n".join(out)


ER = """```mermaid
erDiagram
    games ||--o{ team_game_context : "2 per game"
    games }o--|| venues : "played at"
    games }o--o{ teams : "home and away"
    games ||--o{ game_officials : crew
    game_officials }o--|| officials : is
    games ||--o{ availability : "per player"
    games ||--o{ team_box : box
    games ||--o{ player_box : box
    games ||--o{ pregame_cards : "frozen at t-24h and t-1h"
    games ||--o{ market_snapshots : "lines and prices"
    teams ||--o{ rosters : "per season"
    players ||--o{ rosters : "per season"
    players ||--o{ jersey_history : numbers
    teams ||--o{ coaches : staff
    teams ||--o{ ratings_snapshots : "as of date"
    games ||--o{ video_files : footage
    video_files ||--o{ frames : decoded
    frames ||--o{ detections : boxes
    detections }o--o| tracks : "belongs to"
    tracks }o--o| players : identity
    frames ||--o{ player_positions : "10 per frame"
    frames ||--o{ official_positions : "3 per frame"
    frames ||--|| ball_states : ball
    frames ||--o| frame_geometry : geometry
    games ||--o{ ball_control_state : segments
    games ||--o{ possessions : has
    possessions ||--|{ chances : contains
    chances ||--o{ events : "event chain"
    events ||--o| shots : detail
    events ||--o| fouls : detail
    events ||--o| turnovers : detail
    events ||--o| rebounds : detail
    events ||--o| substitutions : detail
    events ||--o| jump_balls : detail
    events ||--o| coaches_challenges : detail
    rebounds ||--o{ box_outs : "box-outs"
    chances ||--o{ passes : passes
    chances ||--o{ touches : touches
    touches ||--o{ dribbles : dribbles
    touches ||--o| drives : drive
    chances ||--o{ screens : screens
    chances ||--o| set_instances : set
    set_instances ||--o{ set_instance_phases : phases
    games ||--o{ scheme_states : "per second"
    games ||--o{ defensive_matchups : "per second"
    possessions ||--o{ transition_phases : transition
    possessions ||--o{ transition_roles : roles
    games ||--o{ possession_value : "10 Hz"
    games ||--o{ lineup_stints : stints
    games ||--o{ shot_clock_resets : resets
    games ||--o{ whistles : audio
    games ||--o{ simulation_runs : simulated
    simulation_runs ||--o{ predictions : produces
    run_records ||--o{ run_requirement_results : results
    run_records ||--o{ error_catalogue : failures
    review_queue ||--o{ review_labels : labels
```"""


def md_doc():
    groups = []
    for t in TABLES:
        if t["group"] not in groups:
            groups.append(t["group"])
    lines = [
        "# Game and stats data dictionary: core tables",
        "",
        "Status: **proposal** (prompt 003, workflow W2 items 1, 2 and 4; written 2026-10-18 by the W2 core-tables agent). The requirements session approves or changes it. Machine-readable twins: `schema/tables/<table>.yaml` (one file per table, `status: proposed`).",
        "",
        "Scope: every table the project produces or ingests about a game, except the state-record tables of W2 item 5 (`" + "`, `".join(STATE_TABLES) + "`), which another agent defines and which this file references by name only, and the player-attribute card (`player_cards`, W1, `docs/data/dictionary_players.md`). The source-by-source field map is `docs/data/source_field_map.md` (another agent).",
        "",
        "Nothing here contains data. Sources were read from documentation and file headers only (CBBD OpenAPI v1.30.1, hoopR reference pages, local Kaggle and EvanMiya CSV header rows, key names of the ESPN files already pulled); no API call to CBBD, ESPN or KenPom was made for this file.",
        "",
        "## 1. Overview",
        "",
        f"{len(TABLES)} tables in {len(groups)} groups. The ER diagram shows the main joins; every table also joins to `games` through `game_id`.",
        "",
        ER,
        "",
        "| Group | Tables |",
        "|---|---|",
    ]
    for g in groups:
        lines.append(f"| {g} | " + ", ".join(f"`{t['name']}`" for t in TABLES if t["group"] == g) + " |")
    lines += ["", "State-record tables (defined elsewhere, referenced here): " + ", ".join(f"`{s}`" for s in STATE_TABLES) + ".", ""]
    lines += [
        "## 2. Key conventions",
        "",
        "### 2.1 IDs",
        "",
        "- `game_id`: the ESPN event ID as a string (e.g. `401856571`). It is the one join key across video, play-by-play, markets and context (R-FD-02). Other sources map to it through `id_crosswalk`: CBBD `games.sourceId` (ESPN event ID per docs/markets/collector_design.md 1.1, to verify on the first keyed call), hoopR NCAA `espn_game_id`, hoopR `mbb_schedule_crosswalk` (`bart_muid`, `kp_game_id`), markets `SnapshotRow.game_id`.",
        "- `team_id`: ESPN team ID string (MSU = `127`). Torvik and KenPom names (e.g. Torvik `Michigan St.`), CBBD integer IDs, Kaggle `TEAM NO`/`TEAM ID` and EvanMiya team strings map through `id_crosswalk` (R-DS-05, R-MK-18).",
        "- `player_id`: ESPN athlete ID string; players without one get a local ID `x-<team_id>-<season>-<n>`. CBBD athlete IDs, NCAA engine IDs and name strings map through `id_crosswalk` (proposed new-DS-1).",
        "- `venue_id`, `official_id`, `coach_id`: ESPN IDs where ESPN has them, else local `v-`, `o-`, `c-` slugs.",
        "- Event-level keys are strings scoped by game: `<game_id>:<source or kind>:<n>` (e.g. `event_id`, `shot_id`, `foul_id`). `possession_id` and `chance_id` are integers counted within a game; the global key is (`game_id`, id).",
        "- Video: a file is identified by `video_id` = SHA-256 of the original file (R-FD-09; the state-record tables use the same `video_id`); a frame by (`video_id`, `frame_index`); a track by (`run_id`, `video_id`, `track_id`).",
        "- `run_id`: `<UTC yyyymmddThhmmssZ>-<task_id>`; every model output links to its run (R-RR-01, R-EN-04).",
        "",
        "### 2.2 Time bases",
        "",
        "| Name | Unit | Definition |",
        "|---|---|---|",
        "| `video_ts_ms` | ms (int64) | Time from the first frame's presentation timestamp of the ORIGINAL file; for variable-frame-rate files the original PTS is kept in `frames.pts_raw` (R-VI-12). |",
        "| `frame_index` | int | 0-based decoded frame index of the original file. |",
        "| `ts_ds` | 0.1 s (int64) | `video_ts_ms // 100`, used by 10 Hz tables (`possession_value`, `transition_numbers`). |",
        "| `second_index` | s (int) | `video_ts_ms // 1000`, used by 1 Hz tables (`scheme_states`, `defensive_matchups`, `belief_states`, `audio_seconds`). |",
        "| `period` | int | 1 = first half, 2 = second half, 3+ = overtime 1, 2, ... (halves start at 20:00, overtimes at 5:00, R-IV-16). |",
        "| `game_clock_s` | s, 0.1 resolution | Seconds REMAINING in the period: [0, 1200] in halves, [0, 300] in overtime (R-DQ-02). Source strings `mm:ss` are converted. |",
        "| `shot_clock_s` | s, 0.1 resolution | Seconds remaining on the shot clock, [0, 30]; null only when the shot clock is off, and the state then says `off` explicitly (R-MD-01). |",
        "| `*_utc` | timestamp[us, UTC] | All wall-clock times in UTC with microsecond precision; US-Eastern only for date matching through zoneinfo `America/New_York` (R-MK-25). Local tip time is derived from the venue time zone. |",
        "| `as_of_date` | date | Date a rating or card describes (point-in-time; R-DS-04). |",
        "",
        "The video-to-clock map (R-MD-08) lives in the state-record tables (`state_frame`, `state_second`); every table here that carries both video time and game clock takes the clock from that map.",
        "",
        "### 2.3 Court frame and positions",
        "",
        "- Attacked-rim frame (R-CG-02, `src/msu_alpha/geometry.py`): origin on the floor under the centre of the rim being attacked; x along the baseline, positive to the attacker's right; y from the baseline toward half-court (baseline at y = -1.60 m, half-court at y = 12.73 m). r = sqrt(x^2 + y^2) in metres; theta = atan2(y, x) in degrees, 0 = right baseline, 90 = top of the key, 180 = left baseline. The other half is mirrored. Positions are stored to 1 cm (R-CG-08).",
        "- Derived labels recompute from x, y with `geometry.describe()`: `spot` (restricted_area, paint, mid_range_*, corner_three_*, wing_three_*, slot_three_*, top_three), `post_zone` (low_post, high_post, none), `landmark` (elbow, nail, block within 0.9 m), `sector_15deg` (0-11), `ring_0p5m`. Court constants: `config/court_ncaa_men.yaml`; term meanings: `config/vocabulary_map.yaml`.",
        "- `player_positions` also keeps an unmirrored full-court frame (`x_fc_m`, `y_fc_m`, origin at centre court) so no information is lost by mirroring.",
        "",
        "### 2.4 Controlled vocabularies (taxonomy-valued columns hold codes, not free text)",
        "",
        "| Prefix | Source file | Meaning |",
        "|---|---|---|",
        "| `OFF.F<n>[.<sub>]` | `docs/taxonomy/offense_full.md` | Offense families F1-F18 and their numbered sub-sections (e.g. `OFF.F5.4` screener post-action, `OFF.F13.2` BLOB, `OFF.F17` Synergy play types). |",
        "| `MS.<id>` | `docs/taxonomy/motion_starts.md` | Named motion starts and entries (e.g. `MS.H01` Elbow Punch Stagger / 'Spartan'). |",
        "| `DEF.F<n>[.<sub>]` | `docs/taxonomy/defense_full.md` | Defense families F1-F18 (e.g. `DEF.F3.1` containment ball-screen coverages, `DEF.F8.1` 2-3 zone, `DEF.F18.1` per-second label hierarchy). |",
        "| `TR.PH.*`, `TR.RO.*`, `TR.ST.*` | `docs/research/transition_full.md` | Transition phases (3.1 offensive, 3.3 defensive), roles (4), start types (6.1); definition fields as in 5.4. |",
        "| namespaces `MSU.`, `zone.`, `blob.`, `press.`, `def.` | R-ST-22 | Prefix for colliding names (e.g. 'Chicago' the action vs the zone set). |",
        "| geometry labels | `src/msu_alpha/geometry.py` | Shot zones and spots (`spot`), post zones, landmarks, sectors, rings. |",
        "| enums of `schema/global_metadata.yaml` | that file | `game_type`, `ball_control_state` (6), `camera_shot_type` (9), `bonus_state`, `inbound_side`. |",
        "",
        "### 2.5 Licence classes and source codes",
        "",
        "| Code | Source | Licence class (data_sources_catalog.md, R-DS-02, R-DS-10, R-DS-14, R-RG-11) |",
        "|---|---|---|",
    ]
    for k, v in SRC.items():
        lines.append(f"| {k} | {v} | {SHORT[k]}: {LIC[k]} |")
    lines += [
        "",
        "Short classes in the column tables: MI = model input allowed; MI* = model input, provisional (Torvik: no terms page found); RO = reference only; RO* = reference only until the licence is checked (Kaggle archive); BL = blocked until permission or purchase (KenPom until the official API); OWN = computed by us (inherits the strictest class of its inputs); PRIV = Aldemir's private input; MK = per market source (collector_design.md section 6). A row's own `licence_class` column carries the class of the source that filled it, so mixed-source columns are filtered row by row; reference-only and blocked rows never reach a model.",
        "",
        "In the Sources column, only sources that have the field are listed; every other source has none. The YAML files list all seven external sources explicitly (`none` where absent).",
        "",
        "### 2.6 As-of rules",
        "",
        "| Code | Rule |",
        "|---|---|",
    ]
    for k, v in ASOF.items():
        lines.append(f"| `{k}` | {v} |")
    lines += [
        "",
        "Cutoff for a pre-game feature = tip minus the horizon of the pre-game card (24 h or 1 h, R-CX-18). A table's default rule applies to every column unless the column names its own.",
        "",
        "### 2.7 Naming rules",
        "",
        "- snake_case; table names plural nouns; one row per grain stated at the top of each table.",
        "- Units in column names (R-EN-01): `_m`, `_cm`, `_kg`, `_s`, `_ms`, `_deg`, `_mps`, `_mps2`, `_km`, `_px`, `_hz`, `_db`; probabilities `_prob` in [0, 1]; shares `_frac` in [0, 1]; expected points `_xpts`. No feet or inches in stored values; the original string goes in a `*_source` or `*_raw` column (e.g. `listed_height_source`, `dist_ncaa_source`).",
        "- Every key ends in `_id` (the same names the state-record tables use: `events.event_id`, `shots.shot_id`, `frames.(video_id, frame_index)`); booleans read as statements (`is_`, `has_`, or a past participle such as `made`, `blocked`); enums are lower snake values; taxonomy codes end in `_code` or `_codes`.",
        "- Every non-view table ends with the provenance block: `source`, `source_ref`, `pulled_at_utc`, `transform_version`, `model_version`, `confidence`, `dq_flag` (observed, inferred, carried, imputed, quarantined), `pass` (blind, anchored, none), `licence_class`, `schema_version` (R-MD-09, R-MD-19, R-SR-13, R-DQ-04, R-EN-01).",
        "- Rows from different sources for the same thing are separate rows tagged by `source` (any source can be swapped later); fused values carry `source = pbp_fused` or `cv` with lineage in `source_ref`.",
        "- Storage: processed tables as Parquet under `MyDrive/MSU-Alpha-3/processed/<game_id>/<version>/` (R-EN-07); nothing with rows goes into the public repo (R-RG-11). The repo holds only these specs and `schema/tables/*.yaml`.",
        "",
        "### 2.8 Possession and chance definitions",
        "",
        "Ours (R-MD-04): a possession ends only when the other team gains control; an offensive rebound, or a shot-clock reset inside the possession, starts a new chance in the same possession. Each source's own definition is stored next to ours, never merged; see the notes of `possessions`.",
        "",
        "### 2.9 Provenance block (last columns of every non-view table)",
        "",
        "| Column | Type | Range | Null | Definition | Req |",
        "|---|---|---|---|---|---|",
    ] + [f"| `{c['name']}` | {md_esc(c['type'])} | {md_esc(c['range'])} | {'yes' if c['nullable'] else 'no'} | {md_esc(c['definition'])} | {', '.join(c['req'])} |" for c in PROV] + [
        "",
        "## 3. Tables",
        "",
    ]
    for g in groups:
        lines.append(f"## {g}")
        lines.append("")
        for t in TABLES:
            if t["group"] == g:
                lines.append(md_table(t))
                lines.append("")
    lines += [Path(SCR / "tail.md").read_text()]
    return "\n".join(lines)


def main():
    OUT_YAML.mkdir(parents=True, exist_ok=True)
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    names = [t["name"] for t in TABLES]
    assert len(names) == len(set(names)), "duplicate table"
    for t in TABLES:
        cn = [c["name"] for c in full_cols(t)]
        dup = {n for n in cn if cn.count(n) > 1}
        assert not dup, (t["name"], dup)
        d = yaml_for(t)
        p = OUT_YAML / f"{t['name']}.yaml"
        header = f"# Proposed schema for table '{t['name']}' (status: proposed). Generated from docs/data/dictionary_games.md, 2026-10-18.\n"
        p.write_text(header + yaml.safe_dump(d, sort_keys=False, allow_unicode=True, width=120))
    OUT_MD.write_text(md_doc() + "\n")
    print("tables", len(TABLES), "columns", sum(len(full_cols(t)) for t in TABLES))
    print("unknown req IDs:", sorted(unknown))
    print("new IDs:", sorted(newids))
    fams = sorted({r[:4] for r in known})
    usedf = sorted({r[:4] for r in used})
    print("families with no use:", [f for f in fams if f not in usedf])
    print("known IDs unused:", len(known - used))
    print(" ".join(sorted(known - used)))


if __name__ == "__main__":
    main()
