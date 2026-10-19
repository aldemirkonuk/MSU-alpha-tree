# Requirements inbox 010 · State machine, clock map and K09 tables

From: Mac session (msu-colab), 2026-10-19, Aldemir's request "Start the clock map and state machine specs ... tested on the UConn and Louisville games". To: requirements session. Status: proposal (add-only; nothing in the live doc was edited).

## What exists

- `config/state_machine.yaml`: 32 dimensions, transitions T00–T26 (T00 game record opened and T26 timeout/review ends are new; T25 broadcast observability added), flow states S0–S11 plus S4 (split unknown), CBBD mapping, ordering fixes, inferred transitions, integrity rules SEG/TRN/CLK.
- `schema/tables/clock_map.yaml`, `state_transitions.yaml`, `state_segments.yaml` (generator `tools/specgen/k09_tables/gen_k09.py`).
- `tools/state/k09_fold.py` and `tests/state/` (17 tests; 126 pass in the repo).
- Results on both pilot games: `results/state_machine_test/README.md`. 0 untyped transitions, 0 segment integrity breaks, the view equals the reference on 15,641 and 14,844 cells, final scores and per-half possession balance hold, and the blind scorebug agrees on score 68/68 and 71/72 within ±1 s. The 2 + 5 remaining breaks are gaps in CBBD play-by-play.

## Proposed changes to requirements

| Proposal | Tier | Text | Acceptance |
| --- | --- | --- | --- |
| new-SY-10 | Shall | Play-by-play rows inside one game-clock second are ordered by the canonical rule in `config/state_machine.yaml` (ORD-03: score total, then event logic), never by source order. | On both pilot games: 0 free-throw trips out of order, the lineup equals CBBD onFloor at every instant start, and the fold has 0 breaks other than documented PBP gaps. |
| new-SY-11 | Shall | Transitions the play-by-play implies but does not record (throw-in completed T15, timeout ends T26, half time T21, second-half AP start T01) are written with `dq = inferred`, never left out. | Every flow-state change in a pbp_only pass is explained by a typed transition; inferred share reported per game (pilot: 18–19%). |
| new-MD-20 | Shall | The clock map is built from OCR anchors at ≥ 1 Hz (not 60 s samples) plus play-by-play stoppages; a stretch never spans a video cut. | ≥ 95% of video seconds inside a period classified running or stopped (pilot at 60 s: 4–14%); clock error ≤ 0.5 s on 95% of anchors held out. |
| new-SB-05 | Should | The scorebug team-foul display caps at 10; comparisons and OCR checks cap the fold at 10. | No team-foul disagreement above 10 is flagged. |
| R-SB-03 (tighten) | Shall | Scorebug vs play-by-play comparisons use a ±1 s game-clock window (whole-second PBP clock; stopped-clock instants). | Disagreements outside the window go to review with the nearest change distance (pilot: 6 open). |

## Questions

1. Approve T00, T26 and the S4 flow state as additions to the engineer's T01–T24 and the analyst's S0–S11?
2. `config/invariants.yaml` has `restricted_area_radius_m: 1.22`; K25 decided 1.270 m (edge-correct). Update the constant?
3. CBBD challenge rows: playType "Stands" with text "Overturned" on both pilot challenges. Report to CBBD, or only log?
