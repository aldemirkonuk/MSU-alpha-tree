# Scorebug audit, one frame per 60 s (W3 item 7)

Counts only. Frames and the per-frame table stay private (`_audit/<game>/frames/`, `_audit/<game>/scorebug_samples.csv`).
Requirements: R-SB-01..04, R-MB-01, R-SR (state fields read from the scorebug).
Sampling: one frame at video time 0, 60, 120 ... s (UConn 87 frames, Louisville 90 frames). Each frame was looked at, with a full-resolution crop of the bug band.

## Shot types

| shot type | UConn (87) | Louisville (90) | total (177) |
|---|---|---|---|
| main_wide | 41 | 54 | 95 |
| tight | 16 | 21 | 37 |
| crowd_or_bench | 16 | 5 | 21 |
| replay | 10 | 7 | 17 |
| graphic | 3 | 3 | 6 |
| ad_break (break bumper with break bug) | 1 | 0 | 1 |

No commercial content appeared in any sample (both uploads are condensed; see README).

## Scorebug visibility

| | UConn | Louisville | total |
|---|---|---|---|
| full in-game bug | 67 (77.0%) | 70 (77.8%) | 137 (77.4%) |
| break bug (score, period, clock text only) | 4 | 2 | 6 |
| compact corner bug (score, period, clock only) | 0 | 1 | 1 |
| partial or mid-animation | 1 | 2 | 3 |
| none | 15 | 15 | 30 (16.9%) |
| any bug | 72 (82.8%) | 75 (83.3%) | 147 (83.1%) |

By shot type, any bug visible: main_wide 93 of 95 (the 2 misses: bug replaced by a sponsor or promo lower-third during a free throw / dead ball); tight 31 of 37; crowd_or_bench 20 of 21; replay 0 of 17; graphic 2 of 6; ad_break 1 of 1.

## Field availability (share of all 177 samples; value legible when present)

| field | UConn | Louisville | total | notes |
|---|---|---|---|---|
| score (both teams) | 70 | 75 | 145 (81.9%) | also in break and compact bugs |
| period | 70 | 74 | 144 (81.4%) | "1ST", "2ND", "HALFTIME", "FINAL" |
| game clock | 69 | 72 | 141 (79.7%) | m:ss; tenths shown under 1:00 |
| shot clock value | 62 | 65 | 127 (71.8%) | full bug only; slot blank (10 samples) when game clock < shot clock; shown red with tenths under 5 s |
| team fouls | 67 | 70 | 137 (77.4%) | "FOULS: n", "10+" after 10 |
| bonus label | 67 | 70 | 137 (77.4%) | slot shown in full bug; "BONUS" appears in a team's panel once the opponent has 6 fouls, "BONUS+" at 9 (the next foul brings the bonus); "1 SHOT", "2 SHOTS", "1-AND-1" replace it during free throws |
| timeouts left | 67 | 70 | 137 (77.4%) | 4 bars under each team name, read by pixel brightness; 1 sample unreadable (team-name animation) |
| alternating-possession arrow ("POSS") | 67 | 70 | 137 (77.4%) | it is the arrow, not ball possession (checked: arrow on one team while the other team had the ball) |
| team names / seeds | 72 | 75 | 147 | |

Timeout bars checked against the play-by-play timeouts for the UConn game: every bar change matched a team timeout (1st half MSU 11:58, UConn 2:01; 2nd half UConn 1:50, MSU 0:41, 0:32, 0:04, UConn 0:04). During the UConn coach's challenge (2nd half 11:11) the bar dropped by one and came back after the challenge succeeded, as the play-by-play says ("retains its timeout").

## Scorebug boxes (pixels, x, y, w, h in the 1920x1080 frame)

| variant | box | games |
|---|---|---|
| full in-game bug | 124, 946, 1676, 84 | both, same position in every main sample |
| score digit boxes (used for change detection) | MSU 625, 950, 80, 76; right team 1122, 950, 80, 76 | UConn file |
| break bug | about 120, 900, 1680, 130 | both |
| compact corner bug | about 126, 705, 318, 279 | Louisville |

Team order: UConn file has MSU on the left; Louisville file has Louisville on the left (the higher seed / home-designated team on the right, so the left/right mapping must be stored per game).

## Flags for R-SB review
- Louisville: game clock read 4:06 at video 4260 s and 4:07 at 4380 s (clock went up 1 s between samples): official clock correction or review; flag type (i).
- Stat and record straps sit directly above the bug in 21 of 177 samples, and sponsor/promo lower-thirds replaced the bug twice in live play: an OCR reader must check the box position and template, not only the region.
