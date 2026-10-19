# Live game state: what we always know while a game is on

Status: proposal (2026-10-19). One page listing every value the system holds at every instant of a game, where it comes
from and what changes it. It is the per-frame view of the K09 stored truth: dimensions of `state_segments` and
`clock_map` (types and rules in `config/state_machine.yaml`), per-frame observations, and values derived from them.
Stored state is home/away (N-MD-02); the MSU-relative names analysts read (score_msu, margin, MSU ball) are views.

Legend. **Stored**: segment = `state_segments` dimension; clock = `clock_map`; obs = per-frame observation table;
derived = computed in the view, never stored; fixed = set before tip. **Source**: OCR = scorebug, PBP = play-by-play,
CV = tracking, audio, reg = registry/pre-game card. **Changes on**: the transition types (T00–T26) or event.

## 1. Keys and provenance (on every row)

| Field | Values / unit | Stored | Source | Changes on |
| --- | --- | --- | --- | --- |
| game_id | ESPN event ID | key | reg | never |
| pass | blind, anchored, pbp_only | key | pipeline | per run |
| state_version | content hash | key | pipeline | any correction |
| video_id, frame_index | file ID, frame | key | video | every frame (29.97 fps = 33.37 ms) |
| rules_edition | e.g. NCAA-M 2026-27 | fixed | reg (R-RL) | never in a game |
| src, conf, dq per group | sensor; 0–1; observed / inferred / carried / imputed / quarantined | segment | all | with the value |

## 2. Time (four clocks, kept apart)

| Field | Values / unit | Stored | Source | Changes on |
| --- | --- | --- | --- | --- |
| period, period_phase | 1, 2, 3+ (OT); pregame / period / intermission / final | segment | OCR, PBP | T01, T20, T21, T24 |
| game_clock_s | 0–1200 s (OT 300), tenths under 60 s | clock | OCR, PBP | runs at 1.0 s/s while running |
| game_clock_running | running, stopped | segment | OCR, CV | T01, T05 (last 59.9 s), T09, T13–T15, T20, T23 |
| shot_clock_s | 0–30 s | clock | OCR, CV | resets per 2-11.6 (30, 20, or no reset; 41 causes) |
| shot_clock_status | running, stopped, off | segment | OCR | T19; off when the game clock is below a full shot clock |
| video_ts_ms | ms | obs | video | every frame; jumps at replay cuts |
| est_utc (± error) | UTC | clock | PBP wallclock (monotone-fixed), recordings | via the clock map; joins to live prices |
| media segment, 5-min window | U16 / U12 / U8 / U4; 0–5 … 35–40 | derived | clocks | game clock marks (5-14.10) |

## 3. Score

| Field | Values / unit | Stored | Source | Changes on |
| --- | --- | --- | --- | --- |
| score_home, score_away | points | segment | OCR, PBP | T05, T12, T17/T18 corrections |
| margin (MSU view) | points | derived | | any score change |
| current run | net points in the last 120 s; a run when net ≥ 8 (K05) | derived | | score changes |
| lead changes, ties, largest lead each | counts, points | derived | | score changes |
| close-game measure | largest margin so far, kept under 5–6 (N-MD-13) | derived | | score changes |

## 4. Possession and the ball

| Field | Values / unit | Stored | Source | Changes on |
| --- | --- | --- | --- | --- |
| possession_team | home, away, none | segment | PBP, CV | T01, T03, T05, T08, T11–T14, T20 |
| possession_seq, chance_seq, chance number | counts | segment | PBP, CV | new possession; new chance on offensive rebound or reset (K08) |
| team_control | home, away, none (none during a try, jump ball, loose ball) | segment | CV, PBP | T02–T08, T15 |
| ball_status | live, dead | segment | CV, PBP | whistles, makes, period end, restarts |
| try_in_flight | none, in flight, touched the ring | segment | CV | T04–T08 |
| flow_state | S0–S11; S4 split into primary transition, early, half-court | segment | PBP coarse, CV fine | every transition |
| restart_pending | none, jump ball, throw-in (side, spot, team, cause), free throw (k of n, award) | segment | PBP, CV | T10–T15 |
| stoppage | none, foul, violation, held ball, timeout (team/media), review, challenge, injury, period end | segment | PBP, OCR, CV | T09, T13–T17, T20, T23, T26 |
| arrow | home, away, none | segment | OCR, PBP | T02, T14 (flips when the AP throw-in ends) |
| basket_attacked_home | left, right of the main camera | segment | CV | T21 (half time only) |
| ball position, handler | x, y, height m; player | obs | CV | every frame |
| transition numbers | attackers ahead vs defenders back | derived | CV | 10 Hz (R-TR-22) |

## 5. Counts the rules run on

| Field | Values / unit | Stored | Source | Changes on |
| --- | --- | --- | --- | --- |
| team_fouls_home, team_fouls_away | count per half (OT extends half 2) | segment | PBP, OCR | T09; reset at period 2 |
| bonus each team | none, one-and-one (7th foul), double bonus (10th) | derived | | team fouls |
| player_fouls per player | 0–5 (out at 5) | segment | PBP | T09 |
| foul trouble flags | 2 in the first 900 s, 3 with > 600 s left in half 2, 4 with ≤ 600 s and OT (K10) | derived | | fouls, clock |
| timeouts_left each (by length) | count (3 × 30 s + 1 × 60 s in the media format; 2 × 30 s carry into half 2) | segment | PBP, OCR | T16, T17, T21 |
| challenge_available each | yes / no | segment | PBP | T17 |

## 6. Personnel

| Field | Values / unit | Stored | Source | Changes on |
| --- | --- | --- | --- | --- |
| lineup_home, lineup_away | 5 player IDs each | segment | PBP substitution rows, CV identity | T22 |
| identity confidence per tracked player | 0–1 | obs | CV | every frame |
| stint length per player | s on court since last entry | derived | | clock, T22 |
| player positions | x, y m; r/θ from the attacked rim | obs | CV | every frame (10 Hz off-screen estimates with a 95% region) |
| officials' positions | x, y m | obs | CV | 1 Hz, 10 Hz around whistles (K24) |

## 7. Situation (derived, recomputed at every change)

| Field | Definition |
| --- | --- |
| win probability (MSU) | possession engine on the current state; pre-game model blended with live state |
| leverage | change in win probability between the best and worst outcome of the next possession |
| clutch | ≤ 300 s left in half 2 or OT and margin ≤ 5; the last-240 s flag also kept (K06) |
| garbage time | win-probability rule; CTG-adapted rule kept as a view (K28) |
| end-of-period windows | two-for-one (33–45 s left), foul to extend (last 60 s), last shot |
| shot clock vs game clock | shot clock off when the game clock is below a full shot clock |
| expected points of this possession | possession value at this instant (EPV) |

## 8. Tactics (from tracking; each label with a confidence)

| Field | Values |
| --- | --- |
| offense set in progress | top 3 candidates from the taxonomy, with phase |
| defense scheme state | man, 2-3, 3-2, 1-3-1, match-up, press, junk; smoothed per second |
| coverage on the current ball screen | 4 coarse classes, 13 fine after the gate (K04) |
| matchups | who guards whom each second; help position |

## 9. Observability (what we can actually see)

| Field | Values |
| --- | --- |
| camera_shot_type | main wide, close-up, replay, slow motion, crowd, bench, studio, commercial, graphic |
| scorebug_visible | yes / no (absent in 16.9% of sampled frames in the pilot games) |
| replay flag | replay frames never change game state |
| coverage score | share of the 10 players and the ball in view |
| tracking quality | per player per second |

## 10. Fixed for the game (known before tip)

| Field | Source |
| --- | --- |
| game type, round, seeds, rivalry | reg (R-CX-15) |
| venue, home / away / neutral, campus-to-venue distances | reg (R-CX-14) |
| rest days, travel distance and time zones | reg (R-CX-05) |
| officials' crew (crew ID) | reg (R-RF-06) |
| rosters and player cards (frozen at tip) | reg (R-PC-14) |
| pre-game card: our prediction, ratings, closing line | reg (R-CX-18, R-MK) |
| timeout format (media or not) | reg; sets the timeout counts above |

## Rules that hold for every field

- Every value carries its source, confidence and data-quality flag. A value that cannot exist is "off" or "none", never empty.
- In-game features use only what was known at that instant (`known_at_utc`); anchored values (built with full play-by-play) are for training and review, never live.
- Replays and graphics never change game state.
- Corrections write a new state version; the old one stays readable.
