# K09 research: where game state is stored (2026-10-18)

Status: research for Aldemir's decision on conflict K09 (`docs/requirements_review/synthesis.md` section 2; `conflicts_ab.md` row K09, "Pending research"). Nothing here changes the live doc; the requirement text in section 8 is a proposal.
Benchmark: `tools/benchmarks/k09_state_storage.py` (synthetic data only, no game, video or licensed data). Web text was read as data; every URL listed in section 3 was opened on 2026-10-18 unless marked "(unverified)".

## 1. Question

Where does the game state (period, clocks, score, team fouls and bonus, timeouts, possession and chance, ball control, lineups, flow state, with source, confidence and quality flags) live as stored truth, and how do frame-level users get it?

The question matters because of four project needs:

- every frame and every incident must be dissectable and re-weightable (N-CX-10, `conflicts_ab.md`);
- corrections must not overwrite raw readings and must reach everything that used the old value (R-SR-15, N-SY-02, N-SY-05);
- each game runs twice, blind and anchored, and the field-by-field gap is the CV error estimate (R-SR-13);
- the same state vocabulary must work for games with no video (`pbp_only`, R-SY-06, R-PE-08, N-MD-02).

## 2. Options

| | A: segments are the truth | B: per-frame table is the truth |
|---|---|---|
| Stored | `state_transitions` (one typed row per rule-defined change, `config/state_machine.yaml`), `state_segments` (one row per dimension per validity interval, team-neutral), clock segments (`clock_map`, R-MD-08) | `state_frame`: 102 columns (`schema/tables/state_frame.yaml`) on each of ~155,000 frames per game per pass |
| Per-frame state | as-of view (join frames to segments) | the stored rows |
| `flow_state` (S0-S11) | one dimension of `state_segments` | one more column |
| Live doc / synthesis | synthesis recommendation (N-MD-01, N-SY-01, R-MD-01 rewrite) | live doc R-MD-01, R-SR-06; dictionary `state_frame` |

### 2.1 What `state_frame` holds (measured from the YAML, 2026-10-18)

The 102 columns are not one kind of thing. By their own `as_of` tag:

| Kind | Count | Examples | Changes |
|---|---|---|---|
| `by_pass` game state | 71 | clocks, score, fouls, bonus, timeouts, possession, chance, ball control, handler, lineup, provenance companions | ~1,300 change points per game (measured below) |
| `at_frame` per-frame observations | 25 | `ball_x_m`, `ball_y_m`, `ball_z_m`, `ball_visible`, `camera_shot_type`, `replay_flag`, `court_mapping_conf`, `coverage_score` | every frame |
| keys and static | 6 | `game_id`, `season`, `game_type`, `video_id`, `frame_index`, `pass` | never |

The 25 `at_frame` columns already have their own per-frame tables (`frames`, `ball_states`; both keyed by `video_id, frame_index`). In B they are stored twice. In A they must stay per-frame. They cannot be segments. One finding follows: the synthesis' proposed R-SR-06 text (line 762) puts "ball x, y and height" into `state_segments`. That is wrong for a quantity that changes every frame. Section 8 corrects it.

The game clock and the shot clock are not piecewise constant. While running they fall by 1/29.97 s per frame. Under A they are stored as piecewise-linear clock segments (anchor value, running flag, status), which is what R-MD-08's `clock_map` already asks for. The value at a frame is computed, not copied.

## 3. Sources: what the professional systems and the storage patterns say

### 3.1 Sports tracking and event data

| Source (opened) | What it shows | Bearing on K09 |
|---|---|---|
| SportVU NBA logs, parser `Moment.py`: https://raw.githubusercontent.com/linouk23/NBA-Player-Movements/master/Moment.py and `Event.py` (same repo) | Each "moment" (tracking frame) carries quarter, game clock and shot clock, then ball and player positions. Moments are grouped under PBP events. No score, fouls, lineup or timeouts per moment. (Sampling rate 25 Hz is general knowledge, not shown in the file: unverified.) | Per-frame data carries a **narrow** clock stamp plus positions. The rest of the state lives on events. |
| Second Spectrum position JSONL as read by floodlight: https://raw.githubusercontent.com/floodlight-sports/floodlight/main/floodlight/io/secondspectrum.py ; docs https://floodlight.readthedocs.io/en/latest/modules/io/secondspectrum.html ; `Code` class https://raw.githubusercontent.com/floodlight-sports/floodlight/main/floodlight/core/code.py | Each JSONL line has `frameIdx`, `period`, ball and player `xyz`, `live` (ball alive/dead) and `lastTouch` (team). floodlight turns `live` and `lastTouch` into per-frame `Code` arrays and provides `find_sequences` to turn them into intervals. Second Spectrum "markings" (possessions, chances) are separate, and floodlight does not parse them. | Even the best per-frame feed stamps only 2-3 state fields per frame. Higher-level state comes as separate interval products (markings). |
| Cleaning the Glass on NBA Hawk-Eye data, possessions: https://docs.cleaningtheglass.com/pro/data-sets/possessions ; chances: https://docs.cleaningtheglass.com/pro/data-sets/chances | Possessions and chances are **intervals**: `start_he_frame` / `end_he_frame`, start and end wall clock, game clock and shot clock. State at the start is stored on the interval (`start_score_home`, `start_score_away`, `offense_players`, `defense_players`), along with typed start and end causes (`chance_start_type`, `chance_outcome`). A chance has no substitution inside it. | The closest public basketball analogue to option A. State is stored as typed intervals keyed to tracking frames, not copied onto each frame. |
| StatsBomb open data, event file 3788741 (downloaded raw from https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/3788741.json, 3,803 events) | Every event carries `index`, `period`, `timestamp`, `possession` (counter), `possession_team`, `play_pattern`. | State is stamped at **event** grain (thousands of rows), not at frame grain. |
| kloppy domain model: https://raw.githubusercontent.com/PySport/kloppy/master/kloppy/domain/models/common.py (`DataRecord`, `BallState`); concepts page https://kloppy.pysport.org/user-guide/concepts/tracking-data/ | One base record for events and frames with a small state stamp: `period`, `timestamp`, `ball_owning_team`, `ball_state` (alive/dead). | The open-source standard keeps the per-record stamp to about four fields. |
| NBA stats PlayByPlayV3 (nba_api doc): https://raw.githubusercontent.com/swar/nba_api/master/docs/nba_api/stats/endpoints/playbyplayv3.md | Each action has `actionNumber`, `clock`, `period`, `scoreHome`, `scoreAway`, plus who and what. | State is carried on events. |
| pbpstats enhanced PBP item: https://raw.githubusercontent.com/dblackrun/pbpstats/master/pbpstats/resources/enhanced_pbp/enhanced_pbp_item.py | `current_players`, `score_margin`, `lineup_ids` and `fouls_to_give` are derived by walking `previous_event` / `next_event`. | Event sourcing in practice: lineup, score and foul state are folded from the event chain, not stored per row. |
| Sportradar daily change log: https://developer.sportradar.com/basketball/docs/nba-ig-daily-change-log ; removed events: https://developer.sportradar.com/basketball/reference/global-basketball-sport-events-removed | Play-by-play gets "corrections to existing play records". Consumers should pull the changed IDs, re-fetch and "compare the new data with your stored records and update them". Removed events carry `replaced_by`. | The provider sends late corrections; the consumer must diff and rebuild. A small, keyed truth makes the diff and rebuild cheap and exact. |
| SoccerNet Game State Reconstruction: https://arxiv.org/abs/2404.11335 ; https://github.com/SoccerNet/sn-gamestate | "Game state" here means each athlete's pitch position, role, team and jersey per frame (metric GS-HOTA). | A different meaning of "game state": per-frame observations. It maps to our `player_positions` / `ball_states`, not to the rules state. It supports keeping per-frame observations per frame. |
| Hawk-Eye, Second Spectrum and Opta internal storage models | Not public. Searches for Opta F24 event versioning (`last_modified`, `version`) found nothing citable. Second Spectrum's own schema docs need a contract. | (unverified): nothing public says how they store state internally. |

What the public systems have in common:

1. Per-frame records carry a narrow stamp: period, clock(s), ball alive/dead and team in control.
2. Events carry the state at the event: score, possession counter, play pattern.
3. Possessions and chances are typed intervals keyed to frame numbers.
4. Corrections arrive later as revised records, and the consumer rebuilds.

No source I could open stores a ~100-column game state on every tracking frame as the primary record.

### 3.2 Storage and modelling patterns

| Source (opened) | What it says | Bearing |
|---|---|---|
| Fowler, Event Sourcing: https://martinfowler.com/eaaDev/EventSourcing.html | State can be discarded and rebuilt by replaying the log. Temporal queries replay up to a point. Retroactive fixes reverse and replay the affected events, and out-of-order arrivals are handled the same way. Snapshots avoid full replays. | `state_transitions` is the log. `state_segments` and a materialised per-frame table are snapshots that can be rebuilt. |
| Kimball, SCD type 2: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/type-2/ | A new row per change, with effective and expiration dates and a current flag; facts store the version that was active. | `state_segments` is SCD2 keyed by frame and game clock instead of dates. |
| Kimball, periodic snapshot fact table: https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/periodic-snapshot-fact-table/ | One row per period even when nothing happened ("uniformly dense"). | `state_frame` is a periodic snapshot at a 1/29.97 s period: useful for consumers, but derived. |
| Bitemporal modelling: https://en.wikipedia.org/wiki/Bitemporal_modeling | Two timelines: when a fact was true and when it was recorded. Erroneous data is never discarded, so both "as it actually was" and "as recorded then" can be rebuilt. SQL:2011 has constructs for it. | Our effective frame/clock vs `known_at_utc` (N-MD-04). Corrections are new versions, not overwrites (R-SR-15). |
| PostgreSQL range types: https://www.postgresql.org/docs/current/rangetypes.html | Half-open `[)` intervals; containment `@>`; GiST indexes; an exclusion constraint (`EXCLUDE USING GIST (room WITH =, during WITH &&)`) rejects overlapping ranges. | The integrity rule for segments: per (game, pass, dimension), half-open, no overlap, no gap. |
| kdb+/q `aj` (as-of join): https://code.kx.com/q/ref/aj/ | The standard trades-to-quotes join: for each row, the latest matching row at or before its time. Equality columns first, time last; sorted, attributed tables; on the order of 1-2 million records per second. | The finance tick world stores quotes as change events and joins as-of. It does not stamp the prevailing quote onto every trade as stored truth. |
| DuckDB AsOf join guide: https://duckdb.org/docs/current/guides/sql_features/asof_join.html ; blog: https://duckdb.org/2023/09/15/asof-joins-fuzzy-temporal-lookups.html | `ASOF JOIN ... ON a.t >= b.t` returns at most one match per left row. The blog measures AsOf against IEJoin and a LEAD-built state join: AsOf was 0.425 s vs 3.5 s (IEJoin) vs 192 s (state join) on a 5M-row build side; with a probe side ~10× smaller the state join was fastest (0.065 s) and AsOf close (0.077 s). | Our engine for the as-of view: fast, and correct without hand-written interval logic. |
| Parquet encodings: https://parquet.apache.org/docs/file-format/data-pages/encodings/ | Dictionary encoding plus an RLE/bit-packing hybrid exists "to more efficiently store repeated values". | Explains why B's repeated per-frame state compresses well on disk (measured below), so storage alone does not decide K09. |
| Timescale hypertables: https://www.tigerdata.com/docs/use-timescale/latest/hypertables | Time-chunked partitions; chunk-level indexes. The page gives no wide-vs-narrow modelling guidance. | Partition by game and pass (already planned, R-EN-07). No modelling evidence either way. |

## 4. Benchmark

### 4.1 Method

- Script: `tools/benchmarks/k09_state_storage.py`. It reads only `schema/tables/state_frame.yaml`, to take the exact 102 column names and order.
- Run: `python tools/benchmarks/k09_state_storage.py --out <scratch> --reps 5 --seed {7,11,23}` on an Apple M3 Pro (18 GB), Python 3.12.1, DuckDB 1.5.6, pyarrow 26.0.0, numpy 2.5.4. Times are medians of 5 repetitions on tables loaded into DuckDB memory, unless "parquet" is stated.
- Synthetic game: 155,000 frames at 30000/1001 fps, two 1,200 s halves, a condensed-replay shape (dead balls short, halftime ~3 min), and media timeouts at the first dead ball after 16/12/8/4. Live stretches contain passes (handler changes), tries, makes (the clock keeps running except in the last 59.9 s of period 2), misses, rebounds (offensive: shot clock 20 s and a new chance; defensive: 30 s and a new possession) and steals. Dead balls contain fouls (bonus free throws from the 7th team foul, two from the 10th), violations, timeouts, substitutions and the arrow. That gives 1,423-1,425 typed transitions per game across 30 dimensions and 2 clocks.
- Option A: `state_transitions`, long `state_segments` (dimension, value, from_frame, to_frame, src, conf, dq, opened_by), `clock_segments` (anchor in deciseconds, running, status). Clock values use integer arithmetic (`k*10010 // 30000` deciseconds after k frames), so the view and the reference agree exactly.
- Option B: the full `state_frame` (102 columns + `flow_state` = 103) built **independently** in numpy by forward fill, written to Parquet.
- Shared per-frame tables (both options need them): `frames` (broadcast state), `ball_states`, and `detections` (~1.66 M boxes, 6-14 per frame).
- A view: a "runs" table (one row per change point of any dimension, wide and typed; about 1,300 rows), then one `ASOF JOIN` of frames to runs, plus `frames` and `ball_states`. It emits the same 103 columns.
- Correctness: `EXCEPT ALL` in both directions between the A view and B, over all 155,000 rows and 103 columns, before and after the correction.

### 4.2 Results (three seeds: 7 / 11 / 23)

Sizes per game per pass (zstd Parquet unless stated):

| Item | Seed 7 | Seed 11 | Seed 23 |
|---|---|---|---|
| Transitions / segment rows / clock segments / change points (runs) | 1,425 / 5,990 / 760 / 1,299 | 1,424 / 5,891 / 778 / 1,262 | 1,423 / 6,135 / 812 / 1,283 |
| **A stored truth** (transitions + segments + clock segments) | 90.0 KB | 89.2 KB | 91.3 KB |
| **B `state_frame`** (103 columns) | 3.08 MB (snappy 4.19 MB) | 2.91 MB (4.01 MB) | 3.01 MB (4.12 MB) |
| B without the 25 per-frame CV columns (state part only) | 1.20 MB | 1.20 MB | 1.20 MB |
| A view materialised to Parquet (the hybrid's derived table) | 2.55 MB | 2.36 MB | 2.46 MB |
| Shared `frames` + `ball_states` | 3.18 MB | 3.01 MB | 3.11 MB |
| Shared `detections` | 35.9 MB | 35.9 MB | 35.9 MB |
| B in pandas memory | 205 MB | 205 MB | 205 MB |

Queries (milliseconds, medians):

| Query | B table | A view | A segments / interval-native |
|---|---|---|---|
| Q1 state at one arbitrary frame (mean of 200) | 1.47 / 1.49 / 1.39 | 7.71 / 7.65 / 8.39 | 0.33 / 0.34 / 0.35 (long rows + clock formula) |
| Q2 all frames with offense in the bonus and shot clock < 5 s | 0.80 / 0.84 / 0.81 (from Parquet: 1.87 / 2.34 / 2.27) | 7.62 / 7.88 / 7.63 | 0.69 / 0.75 / 0.77 (closed-form first frame < 5.0 s per run) |
| Q3 join 1.66 M detections to state, filter margin ±5 and shot clock < 10, group by ball control | 2.26 / 3.75 / 2.45 | 17.5 / 19.3 / 16.1 (ASOF join to runs) | - |
| Q5 blind vs anchored diff of `ball_control_state` (boundaries jittered ±6 frames) | 7.79 / 9.76 / 7.50 (per-frame) | - | 2.57 / 2.41 / 2.67 (interval overlap) |

Q2 gave identical answers under all four methods (count, first and last frame): 160 / 1,483 / 1,051 frames. Q3 gave identical groups under both. Q5 gave identical differing-frame counts under both: 2,489 / 2,387 / 2,472.

Build, rebuild and correction (seconds):

| Step | Seed 7 | Seed 11 | Seed 23 |
|---|---|---|---|
| Build runs from segments | 0.058 | 0.061 | 0.059 |
| Materialise the full 103-column per-frame view to Parquet | 0.243 | 0.252 | 0.245 |
| Rewrite B Parquet (no change) | 0.178 | 0.186 | 0.186 |
| Rebuild B from transitions in numpy | 1.06 | 1.00 | 1.00 |
| **Correction: one first-half foul re-attributed** (clock 6:05 / 7:11 / 7:12 left, the first foul at or after minute 12) | | | |
| A: append correction + superseding transition, rebuild only period-1 team-foul segments, write | 0.0146 (22 rows replaced) | 0.0131 (19) | 0.0146 (22) |
| A hybrid: also regenerate the materialised per-frame table | 0.313 | 0.313 | 0.301 |
| B: patch the window and rewrite the Parquet file | 0.180 | 0.177 | 0.177 |
| B: frames whose values change / value cells touched | 31,909 / 159,545 | 33,550 / 167,750 | 32,819 / 164,095 |
| B: UPDATE in a mutable DuckDB table (two UPDATEs) | 0.0017 | 0.0018 | 0.0019 |

Correctness (rows differing, A view vs B, both directions): **0 / 0 on all three seeds, before and after the correction**, over 155,000 rows × 103 columns.

### 4.3 What the numbers mean

- **Speed does not decide K09.** At one game, every option answers in milliseconds and rebuilds in well under a second. B is faster for frame lookups and frame joins: 5× on Q1 and 7× on Q3. A's interval-native queries are as fast as B or faster (Q2, Q5). A materialised per-frame table removes B's speed advantage, because the per-frame table can be regenerated from segments in 0.25-0.31 s per game per pass.
- **Storage does not decide K09 either.** The A truth is ~33× smaller than B (90 KB vs 3.0 MB per game per pass), or ~13× against B's state-only part. But Parquet's dictionary and RLE encoding makes B small in absolute terms: about 0.2 GB for 35 games × 2 passes. Detections (36 MB per game) dwarf both. Memory is another matter: B in pandas is 205 MB per game per pass because of the per-row lists (`players_on_floor`, `invariant_breaks`).
- **Correctness under correction decides it.** A correction changes 19-22 segment rows in A, and their provenance travels with them. In B the same correction touches 32,000-34,000 frames. My own B patch was wrong twice before it matched. The first version updated values and bonus but missed `fouls_src`, `fouls_conf` and `fouls_dq` on the corrected frames, plus the row-level `confidence`. The second version missed that, when the corrected foul moves away from the home team, frames from the foul to that team's next foul (509 frames, seed 11) must fall back to the provenance of the segment open before the correction. Getting this right in B means re-deriving segment logic inside the patch. That is the drift-between-copies failure the data engineer predicted (`perspective_data_engineer.md` K6). In A it cannot arise, because each value and its provenance are stored once.
- **The synthesis count is understated.** The synthesis' "about 1,000 segment rows" should read ~1,300 change points, ~6,000 long segment rows (30 dimensions) and ~800 clock segments per game per pass. The two high-churn dimensions are `ball_handler_player_id` (~970 segments) and `flow_state` (~970).

## 5. Failure modes and how each option behaves

| Failure mode | A (segments truth) | B (per-frame truth) | Hybrid handling (recommended) |
|---|---|---|---|
| Official correction (Rule 5-12 clock, 2-9.13 scorebook, review overturn; synthetic: foul re-attributed) | Append a correction plus a superseding transition; rebuild only the dimension's segments inside the window (N-SY-05). The changed frame range is known exactly from the old vs new segments. | Patch 30k+ frames per dimension, including provenance and row confidence. Easy to get partly wrong (section 4.3). Every derived per-frame copy must be found. | As A, then regenerate the materialised table (0.3 s) under a new content hash. Incidents whose frames fall in the changed range are re-scored (N-CX-10). |
| Late or changed PBP (re-pull differs, N-SY-02; Sportradar-style "corrections to existing play records") | New `pbp_versions` row; the anchored pass's affected transitions get new versions; the segment diff gives the exact frames affected. | Whole anchored `state_frame` rebuilt and diffed row by row. | As A; the diff is computed on segments (Q5: 2.5 ms vs 8-10 ms per dimension, identical result). |
| Scorebug lag (measured 1.50-2.60 s, median 1.933 s, `results/w3_intake/README.md`) | A transition has an effective frame (the make frame from CV) and an observed frame (scorebug change). The segment opens at the effective frame. Lag is a column on the transition, not 58 wrong frames. | Each frame must hold the back-dated score; the per-frame OCR read differs from the stored state on ~58 frames per score. Without a separate observation table this is lost. | As A; raw OCR stays in `scoreboard_ocr` (write-once), and lag statistics come from transitions (K02). |
| Replays and cuts in condensed video (Principle 7; cut map R-VI-02) | Replays open no transitions; replay frames get the carried state through the as-of view and are marked by `frames.replay_flag`. Cuts make clock segments break: `clock_map` gives one segment per running stretch per video file. | Each replay frame must carry copied state with `dq = carried`; each cut must be handled in the per-frame fill. | As A. Invariant: no transition's effective frame is a replay frame. |
| Games or stretches with no video (`pbp_only`, R-SY-06, R-PE-08) | Segments keyed by game clock (`valid_from_gc`, `valid_to_gc`) work without frames. | No frames means no rows: B cannot represent the state. A second model would be needed. | As A: one vocabulary for all D-I games. |
| Two passes, blind and anchored (R-SR-13) | `pass` is in the segment key. The diff is an interval overlap (exact and cheaper, Q5). | Two full copies of 155k × 103, diffed by row. | As A; the materialised table is per pass, regenerated. |
| Gaps and overlaps in segments (a new failure class A introduces) | Must be checked: per (game, pass, dimension), half-open `[from, to)` intervals tile `[0, n_frames)` with no gap and no overlap (PostgreSQL's exclusion-constraint idea; checked with `LEAD` in DuckDB). | Not applicable. | Invariant N-IV-xx (section 8). |
| Several changes in one frame | Needs an `order_index` within a frame. Zero-length segments are dropped (the benchmark's builder does this). | The last write wins silently. | `state_transitions.order_index`; a test of same-frame ordering. |
| High-frequency quantities stored as segments by mistake (ball x, y, z; camera shot type) | One segment per frame: the worst of both worlds. | Natural. | Rule: `at_frame` observations stay in `frames`, `ball_states`, `player_positions`; only rule state goes to segments (fixes the synthesis' R-SR-06 text). |
| Analysts and ML need a dense per-frame table (N-CX-10 contributions per frame; feature tables) | Has to join every time (Q3 7× slower than B). | Natural. | The materialised per-frame table, regenerated deterministically and keyed by `state_version`; contributions reference `(video_id, frame_index, state_version)`. |

## 6. N-CX-10 (dissect and re-weight every frame and incident)

N-CX-10 asks that per-parameter contributions be stored per frame and per incident, so that changing a weight re-scores without re-running the pipeline. State storage affects it in two ways:

1. Contributions need fixed, versioned inputs. If state were edited in place (B with UPDATE), a stored contribution could no longer be traced to the state it was computed on. With segments as truth plus a versioned, regenerated per-frame table, each contribution row carries `state_version` (the content hash of the segments, transitions and code). The inputs of any old score can be rebuilt exactly.
2. A state correction must say which incidents to re-score. With segments, the changed frame range is the symmetric difference of old and new segments: a few rows, computed in milliseconds. Only incidents overlapping that range are re-scored. Re-weighting itself never touches state.

Option A as a hybrid therefore supports N-CX-10 better than B. B gives dense rows but no version boundary and no cheap blast radius.

## 7. Recommendation

**Hybrid, with segments as the only stored truth: "A + a deterministic materialised per-frame table".**

1. Stored truth (append-only, versioned per game, pass and `state_version`):
   - `state_transitions`: typed (T01-T24 and subtypes, `config/state_machine.yaml`), with effective frame, order index, observed frame, all four clocks, rule reference, sources, `known_at_utc` and `supersedes_id`.
   - `state_segments`: per dimension, team-neutral, half-open validity intervals on frame and game clock, with value, src, conf, dq and `opened_by_transition_id`.
   - `clock_map` (R-MD-08): piecewise-linear game and shot clock.
2. Per-frame observations stay per frame: `frames`, `ball_states`, `player_positions`, `detections`. Never segments, never copied into a state table.
3. Derived and never edited:
   - `state_frame`: a materialised as-of view, regenerated from (1) and (2) after any change of (1), stored under its `state_version`, and byte-reproducible.
   - `state_second`.
   - The full global stamp on exports.

The 5 strongest reasons:

1. **One place per fact makes corrections correct.** One correction changed 19-22 segment rows in A but 32,000-34,000 frames × 5 value cells plus provenance in B. My own B patch needed two fixes (missed provenance and row confidence; then 509 frames of fallback provenance) before it matched. A's view matched B with 0 differing rows over 155,000 × 103 cells on 3 seeds, before and after.
2. **This is how the public basketball and sports data are shaped.** NBA Hawk-Eye-based possessions and chances are frame-keyed intervals with state at the start (Cleaning the Glass). Per-frame feeds carry only a narrow stamp: SportVU has quarter and clocks; Second Spectrum has `live` and `lastTouch`; kloppy has period, ball state and owning team. Events carry the rest (StatsBomb, NBA PBP v3). pbpstats folds lineups, score and fouls from the event chain. Providers correct later and expect consumers to diff and rebuild (Sportradar).
3. **It is the only option that works without video and across passes.** `pbp_only` games have no frames, so B cannot hold their state. Segments keyed by game clock can. Blind vs anchored diffs on segments are exact and cheaper (identical counts; 2.5 ms vs 8-10 ms).
4. **Bitemporal and event-sourced patterns give auditability and no leakage.** The transitions log is the event log (Fowler). Segments are SCD2 rows (Kimball). `known_at_utc` and supersession give "as it was" vs "as recorded then" (bitemporal), which N-MD-04's leakage test needs. In-place per-frame edits lose that history.
5. **The hybrid removes B's one real advantage at negligible cost.** Dense per-frame access is 5-7× faster from a table (Q1, Q3). The hybrid regenerates that table from segments in 0.25-0.31 s per game per pass. N-CX-10 contributions key to `(frame, state_version)`, and the changed frame range after a correction comes free from the segment diff.

What A costs, stated honestly:

- An as-of view is slower for ad-hoc per-frame work than a table. The materialised table solves this.
- A new integrity class appears (gaps, overlaps, same-frame ordering). Invariants and tests cover it.
- The per-frame CV quantities must be kept out of segments.
- Writers need a fold (transitions → segments) instead of a forward fill. The benchmark's `build_segments` is about 40 lines.

## 8. Proposed requirement text (for the live doc; Aldemir approves)

**R-MD-01 (rewrite; Shall).**
Text: Every stored row carries the key stamp: `game_id`, `pass`, `state_version` (or the stage output key), and either (`video_id`, `frame_index`) or (`period`, `game_clock_s`, `order_index`). The state stamp (all other fields of `schema/global_metadata.yaml`: clocks, score, fouls and bonus, timeouts, possession and chance, ball control, lineup, flow state) is obtained by an as-of join to `state_segments` and `clock_map`. It is materialised only in derived tables (`state_frame`, `state_second`) and in exports, which are regenerated, never edited. Fields that cannot exist hold an explicit value ("off"), never null.
Acceptance: for a random 1% sample of rows of every table, the joined state equals the materialised `state_frame` / `state_second` of the same `state_version` (100%); no stored table other than `state_segments`, `clock_map` and `state_transitions` holds a copy of a state field (schema check); regenerating `state_frame` twice from the same inputs gives byte-identical Parquet.

**R-SR-06 (tighten; Shall).**
Text: Ball state per frame: control state (team A ball, team B ball, contested, in flight, throw-in pending, dead), ball handler and `ring_contact` on each try, stored as dimensions of `state_segments`. Ball x, y and height (m), `ball_visible` and `ball_inferred` are per-frame observations stored in `ball_states`, never as segments. The per-frame ball state is the as-of view joining both.
Acceptance: tests of R-MD-02 (control), R-BL-02 (handler), R-BL-01 (position) and R-MB-07 (ring contact) pass; the view equals segments plus `ball_states` on 100% of frames; 0 per-frame position columns in `state_segments`.

**N-MD-01 (rewrite; Shall, P0).**
Text: Game state is stored once, as half-open validity intervals `[from, to)` per (game, pass, dimension, `state_version`) in `state_segments` (value, src, conf, dq, `opened_by_transition_id`; keyed by frame for video passes and by game clock for `pbp_only`), plus `clock_map` for the piecewise-linear game and shot clocks. Within a (game, pass, dimension, version), segments neither overlap nor leave gaps over the covered range. Per-frame (`state_frame`) and per-second (`state_second`) state are derived by an as-of join and regenerated deterministically after any change. Each corrected segment carries the correction's provenance.
Acceptance: the view equals the reference per-frame build on 100% of frames and columns of games 1-2 (benchmark: 0 of 155,000 × 103 differ on 3 synthetic seeds); 0 gaps and 0 overlaps per dimension; a correction rebuilds only the segments of the affected dimensions inside its window, and the regenerated `state_frame` equals a full rebuild (0 differing rows).

**N-MD-02 (tighten; Shall, P0).**
Text: All stored state is team-neutral (by `team_id`, or home/away): score, team fouls, bonus, timeouts by length, challenge, team in possession and arrow. MSU-relative fields (`*_msu`, `*_opp`, `team_in_possession ∈ {msu, opponent}`) exist only in derived tables and exports, mapped from `games` (MSU's `team_id`).
Acceptance: a `pbp_only` non-MSU D-I game runs end to end with 0 nulls in team-relative state; for MSU games the derived MSU-relative fields equal the team-neutral ones under the mapping on 100% of frames.

**N-SY-01 (tighten; Shall, P0).**
Text: Every game-state change is one typed transition in `state_transitions` (type from `config/state_machine.yaml`, T01-T24 and subtypes, each with its rule reference and allowed from → to pairs). Each transition records the effective frame and `order_index` within the frame, the observed frame per source (OCR, PBP, CV, so that scorebug lag is stored, not hidden), all four clocks, the trigger event, the sources that observed it, `known_at_utc`, and `supersedes_id` for corrections. Rows are append-only. The analyst flow state (S0-S11; S4 split into primary transition, early offense and half-court, with source CV for the split) is a dimension of `state_segments`, so per-frame `flow_state` comes from the view. A disallowed transition is an invariant break. Replay frames never open a transition.
Acceptance: 0 untyped transitions; every segment boundary references exactly one transition; disallowed transitions = 0 on gold-v1 or each explained in review; 0 transitions with an effective frame inside a replay; transition count per type reported per game; for each corrected transition the superseded row is still readable (count of superseded = count of corrections).

Related changes (no new IDs; for the same decision):

- **N-IV-01**: add three integrity invariants on `state_segments`: (a) no overlap; (b) no gap; (c) zero-length segments are not stored. Severity: quarantine.
- **N-SY-05**: the acceptance gains "the regenerated `state_frame` after the correction equals a full rebuild (0 rows differ)" and "the frame range reported as changed equals the symmetric difference of old and new segments".
- **N-CX-10**: contributions are keyed by (`video_id`, `frame_index` or `incident_id`, `state_version`). After a state correction, only incidents overlapping the changed frame range are re-scored.

## 9. Schema implications (proposals; add-only)

| File | Change |
|---|---|
| new `schema/tables/state_segments.yaml` | PK (`game_id`, `pass`, `state_version`, `dimension`, `from_frame`), with `from_gc` used for `pbp_only`. Columns: `to_frame`, `from_gc`, `to_gc`, `period`, `value` (string) with `value_type`, or typed `value_int`/`value_str`/`value_float`, `src`, `conf`, `dq`, `opened_by_transition_id`, `correction_id` (null ok). Grain: one row per dimension per validity interval. ~6,000 rows per game per pass. |
| new `schema/tables/state_transitions.yaml` | PK (`game_id`, `pass`, `transition_id`). Columns: `effective_frame`, `order_index`, `observed_frame_ocr`, `observed_frame_pbp`, `observed_frame_cv`, `video_ts_ms`, `period`, `game_clock_s`, `shot_clock_s`, `shot_clock_status`, `est_utc`, `est_utc_err_s`, `ttype`, `rule_ref`, `changes` (dimension → value), `sources`, `known_at_utc`, `supersedes_id`. ~1,400 rows per game per pass. |
| `clock_map` (R-MD-08, already proposed) | Add `clock ∈ {game, shot}`, `anchor_ds` (int, deciseconds), `running`, `status`. Integer decisecond arithmetic, so views are exactly reproducible. |
| `schema/tables/state_frame.yaml` | Dated note: `status: derived (materialised view)`; add `state_version`; the 25 `at_frame` columns are joined from `frames` / `ball_states` at materialisation and are not separate truth; `correction_ids` comes from segments. Never edited in place. |
| `schema/tables/state_second.yaml` | Dated note: derived from segments (for `pbp_only` keyed by game clock); add `state_version`. |
| `schema/global_metadata.yaml` | Dated note: split into `key_stamp` (stored on every row) and `state_stamp` (view and exports only); state fields named team-neutrally with MSU-relative aliases in views (N-MD-02). |
| `schema/tables/state_corrections.yaml` | Dated note: add `state_transitions` and `state_segments` to `target_table`; corrections target transitions, never frames. |
| `config/invariants.yaml` | Dated note: `evaluated_on` per invariant (transitions, segments or frames) (N-IV-01); add the 3 segment-integrity invariants. |
| new `config/state_machine.yaml` | T01-T24 with rule refs, allowed from → to, and dimensions changed (data engineer section 1.2, ESPN analyst S0-S11). |

Decision line for Aldemir (K09): **approve the hybrid?** Stored truth = `state_transitions` + `state_segments` + `clock_map` (team-neutral, append-only, versioned). Per-frame observations stay in `frames` / `ball_states` / `player_positions`. `state_frame` and `state_second` are materialised views, regenerated deterministically and never edited.

## 10. Sources opened (2026-10-18)

Repo and scratch: `docs/requirements_review/synthesis.md` (K09, N-MD-01..05, N-SY-01/02/05, R-MD-01 and R-SR-06 proposals), `perspective_data_engineer.md` (sections 1.1, 1.2, K6, normalisation, new-MD-E2, new-SY-E1/E5), `perspective_espn_analyst.md` (section 1.1, new-SR-A6), `perspective_team_data_scientist.md` (grep of state items), `conflicts_ab.md` (K09 row, N-CX-10), `docs/data/dictionary_state.md` (sections 1, `state_frame`, `state_second`, `state_corrections`, 7), `schema/tables/state_frame.yaml` (all 102 columns parsed), `schema/tables/frames.yaml`, `ball_states.yaml` and `detections.yaml` (grain and keys), `schema/global_metadata.yaml`, `config/invariants.yaml` (header and constants), `results/w3_intake/README.md` (frame counts, lag), and the live-doc export `msu-basketball-cv-master-requirements-brainstorm-v0.md` ("State record and invariants", R-MD-01, R-MD-08) and `requirement_ids.md`.

Web: the URLs in sections 3.1 and 3.2. Pages whose content could not be read: https://floodlight.readthedocs.io (no per-frame statement; the source code was read instead), https://kloppy.pysport.org/user-guide/concepts/ (landing page only), https://github.com/statsbomb/open-data/blob/master/doc/Open%20Data%20Events%20v4.0.0.pdf (PDF not rendered; raw event JSON used instead), https://developer.shottracker.com/broadcast.html (404).
