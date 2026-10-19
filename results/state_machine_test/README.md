# State machine and K09 tables: test on the UConn and Louisville games

Date: 2026-10-19. Aldemir's request: "Start the clock map and state machine specs: schema/tables/clock_map.yaml, state_transitions, state_segments and config/state_machine.yaml, tested on the UConn and Louisville games."

Status: proposal. The requirements session approves (inbox 010). Nothing in `src/` changed.

## What was built

| File | Content |
| --- | --- |
| `config/state_machine.yaml` | 32 game-state dimensions (team-neutral; stored as segment, clock map or derived), 27 typed transitions T00–T26 with rule references, allowed flow states and the dimensions each may change, the CBBD play-by-play mapping, the ordering fixes and inferred transitions the data needs, and 11 integrity rules (SEG, TRN, CLK). |
| `schema/tables/clock_map.yaml` | Video time ↔ game clock ↔ shot clock ↔ UTC per stretch, integer deciseconds, status running/stopped/cut/off/unknown, stated error. |
| `schema/tables/state_transitions.yaml` | One typed row per game-state change: deterministic ID, effective and observed frames per sensor, all clocks, flow from/to, changes, `known_at_utc`, `supersedes_id`. Append-only. |
| `schema/tables/state_segments.yaml` | One row per dimension per half-open validity interval, keyed by frame (video passes) or by period, game clock and order (pbp_only). |
| `tools/specgen/k09_tables/gen_k09.py` | Generates the three table specs. |
| `tools/state/k09_fold.py` | Types CBBD play-by-play into transitions, folds them into segments, builds both clock maps and runs every check. |
| `tests/state/test_state_machine.py` | 17 tests on the config, the specs and a synthetic game that contains every ordering fault measured below. No private data. |
| `summary.json` | Counts per game (this folder). The transitions, segments and clock maps themselves are in private storage (`~/MSU-Alpha-3-private/processed/<game_id>/pbp_only/<state_version>/`), because they are built from licensed CBBD rows. |

Inputs: CBBD `/plays/game` for both games (Louisville pulled 19 Oct, one call, 978 calls left), CBBD game records for final scores, and the scorebug samples read from the two videos on 18 Oct (one every 60 s of video).

## Results

| Check | UConn 401856571 (UConn home, 67-63) | Louisville 401856531 (MSU home, 77-69) |
| --- | --- | --- |
| Play-by-play rows | 470 | 492 |
| Transitions (of which inferred) | 507 (91) | 516 (99) |
| Segments | 1,932 | 2,032 |
| Untyped transitions (TRN-01) | 0 | 0 |
| Segment overlaps, gaps, zero-length, boundaries without one transition (SEG-01..04) | 0 | 0 |
| State rebuilt from segments vs the walk's own state, every transition × dimension (N-MD-01 acceptance) | 0 of 15,641 cells differ | 0 of 14,844 cells differ |
| Final score equals the game record | yes | yes |
| Possessions per half, home / away (R-IV-15: differ by ≤ 1) | 30/31, 33/32 | 34/35, 33/33 |
| Lineup built from substitution rows equals CBBD onFloor at every instant start | yes | yes |
| Transition IDs reproducible across runs | yes | yes |
| Remaining breaks | 2 | 5 |

Remaining breaks, each a real gap in the play-by-play, not a spec or code fault:

- **Substitutions during live play (2 per game).** Four players change while the ball is live and no dead-ball row exists at that second (UConn 1st half 6:20, 2nd half 13:07; Louisville 10:00, 0:16). The whistle or out-of-bounds that allowed them is missing from CBBD.
- **Louisville 2nd half 7:12–6:41 (3 breaks).** MSU makes two free throws, then shoots and rebounds again with no Louisville possession recorded in between. A Louisville turnover is missing; the possession count is one short there.

## Scorebug (blind) vs play-by-play fold

The blind OCR reads of the scorebug were compared with the fold at the same game-clock reading.

| Field | UConn strict | UConn within ±1 s | Louisville strict | Louisville within ±1 s |
| --- | --- | --- | --- | --- |
| Score | 55/68 | 68/68 | 60/72 | 71/72 |
| Team fouls | 60/67 | 67/67 | 61/70 | 66/70 |
| Timeouts left | 61/67 | 66/67 | 66/69 | 69/69 |

"Strict" compares with the state after every event at that clock reading. The ±1 s window is needed because CBBD gives whole seconds while the bug shows tenths under 60 s, and because a foul and its free throws share one clock reading while the clock is stopped. Both broadcasts stop the team-foul number at 10, so fouls are compared capped at 10. Left unexplained: one UConn timeout count, one Louisville score read and four Louisville team-foul reads (MSU 3 in the fold vs 2 on the bug from 1st half 6:18 to 5:18 and at 2nd half 16:16). They go to review as open measured disagreements.

## Clock map

- **From the scorebug samples (video ↔ game clock):** with one anchor every 60 s, 60 of 67 UConn stretches and 57 of 71 Louisville stretches mix running and stopped clock. The map cannot place the stops inside them. The video holds about 2,476 s of stopped clock per game (video time minus clock time). No stretch inside a period skipped game clock, so these condensed replays cut stopped time (half time, timeouts, replays) but not running time. **A usable map needs OCR at 1–2 Hz plus the play-by-play stoppages.** The spec supports that; the 60 s samples only test it.
- **Game clock ↔ UTC from CBBD wallclock:** 96 (UConn) and 87 (Louisville) rows carry a wallclock earlier than one already seen, by up to 227 s. The fold uses the running maximum and stores the correction as `utc_err_s`. Raw wallclock must never be joined to in-game prices directly.

## What the data forced into the spec (measured 19 Oct)

1. **Row order inside one second is unreliable (ORD-03).** Free throws are listed 2 of 2 before 1 of 2, substitutions come before the whistle that allowed them, and End Game comes before the last rebound and End Period. Rows are sorted by score total (post-event scores never decrease), then by event logic. 165 and 169 rows moved.
2. **Challenge outcome.** CBBD's playType says "Stands" for both challenges, while the text says "Overturned … retains its timeout". The text is used and the disagreement is logged.
3. **Team rebounds without a player** are either a credit (during free throws or a dead ball) or the ball going out of bounds after a try (T13).
4. **A fouled missed try is not a field-goal attempt.** A 2- or 3-shot trip with no shot row is a shooting foul, not a bonus.
5. **T00 (game record opened)** and **T26 (timeout or review ends)** were added to the engineer's T01–T24. Without T26 a timeout has no exit. **S4** (frontcourt control, split unknown) was added for passes without video.
6. **Inferred transitions are marked** (`dq = inferred`): the throw-in that restarts play (T15), timeout exits (T26), half time (T21) and the second-half alternating-possession start (T01).

## Not done here

- No video pass yet: `effective_frame`, `observed_frame_*`, the shot clock and the S3/S4a/b/c split need the tracking and OCR pipeline.
- `state_frame` and `state_second` are not regenerated from these segments yet (dated notes in their specs say how).
- Found while checking: `config/invariants.yaml` still has `restricted_area_radius_m: 1.22`, while K25 decided the edge-correct 1.270 m. Sent to the requirements session (inbox 010), not changed here.

Run: `python tools/state/k09_fold.py` (needs PyYAML and pyarrow, and the private inputs). Tests: `python -m pytest tests/state`.
