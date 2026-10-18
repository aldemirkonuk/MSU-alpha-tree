# Made-basket scorebug lag, first game (W3 item 7)

Game: ESPN 401856571 (UConn 67, MSU 63, 2026-03-27). File: `2026-03-27_uconn_youtube.webm`, 1920x1080, 29.97 fps constant.
First 10 made field goals per the CBBD play-by-play (game 372596). Per-make rows with video times are in the private file `_audit/uconn/made_basket_lag.csv` (not in the repo).
Requirements: R-SB-03, R-MB-01, R-MB-04.

Method
- Through-the-net time: frames stepped one by one (0.0334 s) on a crop around the rim; time of the first frame with the ball centre below the ring plane.
- Scorebug change time: first frame where the changed team's score digits differ from the previous frame (pixel difference on the digit box); "settled" = last frame of the digit animation.
- Timing resolution: 1 frame = 0.033 s for both cues.

| make | points | camera | lag to digit change start (s) | lag to digit settled (s) | confidence |
|---|---|---|---|---|---|
| 1 | 2 | main_wide | 1.965 | 2.265 | high |
| 2 | 3 | main_wide | 2.035 | 2.335 | high |
| 3 | 2 | main_wide | 1.901 | 2.168 | high |
| 4 | 3 | main_wide | 2.068 | 2.368 | high |
| 5 | 2 (dunk) | main_wide | 1.831 | 2.131 | medium |
| 6 | 2 (dunk) | main_wide | 1.671 | 1.971 | medium |
| 7 | 3 | main_wide | 2.331 | 2.631 | high |
| 8 | 2 | main_wide | 1.498 | 1.798 | high |
| 9 | 3 | main_wide | 2.604 | 2.905 | medium |
| 10 | 3 | main_wide | 1.721 | 2.021 | high |

Summary (lag to digit change start, n = 10): mean 1.963 s, median 1.933 s, SD 0.324 s, min 1.498 s, max 2.604 s.
Lag to digit settled: mean 2.259 s, median 2.216 s. The digit animation lasts 9-10 frames (0.27-0.30 s) every time.

Other numbers
- All 10 makes were shown live in the main wide camera with the scorebug on screen and the rim and net in view: 10 of 10.
- Rim and net at 29.97 fps: rim edge sharp in 10 of 10; the ball is motion-blurred for 1-2 frames as it passes the ring in most makes; on 2 dunks the hand and arm hide the ball for 1-2 frames; on 1 make (9) the rim is small and the ball blurred inside the net. The ball crosses the ring plane within 1-2 frames, so the make frame can be fixed to about +/-1 frame (+/-0.033 s); R-MB-04 asks +/-0.05 s.
- Arena shot clock (visible above the backboard) reset to 30 relative to the through-the-net frame: -0.97 to +0.47 s (9 makes measured). In 2 makes it reset while the ball was still bouncing or rolling on the ring (before the ball went through), so the arena shot-clock reset marks ring contact, not the make.
- Proposed lag window for R-SB-03 from this sample: 1.5-2.7 s observed, so the starting 15 s window is very generous; a 4 s window would hold all 10.
