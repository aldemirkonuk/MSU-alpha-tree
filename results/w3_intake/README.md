# W3 intake: first two game videos (prompt 003, items 4, 5, 7)

Date: 2026-10-18. Private research use only. No video, audio or frames are in this folder or anywhere in the repo.
Videos staged at `~/MSU-Alpha-3-private/raw_video/2025-26/`; final home `MyDrive/MSU-Alpha-3/raw_video/2025-26/` (the main session moves them).
Files were not re-encoded or modified after download; all checks read the files only.

Files here
- `video_manifest.csv`: hash, specs, source URL, channel, dates, Drive path (R-FD-09, R-VI-01, R-VI-02, R-VI-14, R-RG-10).
- `intake_check.csv`: per-file intake check (R-VI-02).
- `scorebug_summary.md`: scorebug audit counts (R-SB, R-MB).
- `made_basket_lag.md`: lag from ball-through-net to scorebug change, first 10 made field goals of the UConn game (R-SB-03, R-MB-04).
- `registry/games.csv`: footage_source and footage_path filled for games 401856571 and 401856531 (nothing else changed).

## Manifest (both files)

| | UConn (401856571) | Louisville (401856531) |
|---|---|---|
| file | 2026-03-27_uconn_youtube.webm | 2026-03-21_louisville_youtube.webm |
| SHA-256 | 16fe4160009abacac871578315370989bf569345f1da5d9bd569c66738fdb2fa | 59cd8a3c54504dac1be10fe8039d4dd1d62f4602bb7df7baa71937ebec3cfe2d |
| size | 1,819,111,381 B | 1,971,033,035 B |
| video | VP9 Profile 0, 1920x1080, yuv420p, BT.709 SDR | same |
| frame rate | 29.97 (30000/1001), constant | same |
| frames | 155,492 | 161,653 |
| duration | 5188.25 s (86.5 min) | 5393.82 s (89.9 min) |
| audio | Opus 48 kHz stereo | same |
| overall bitrate | 2.81 Mb/s | 2.92 Mb/s |
| YouTube | Vm0FqeGo-8g, channel March Madness, uploaded 2026-04-17 | Ze8frxZxNyk, channel March Madness, uploaded 2026-04-12 |
| format | 614 (VP9 1080p HLS) + 251 (Opus), merged to webm, no re-encode | same |
| yt-dlp | 2026.08.19, downloaded 2026-10-18 | same |

Constant frame rate was checked on every video packet timestamp of each file: only 33 ms and 34 ms steps (1 ms rounding of 33.37 ms), no gap over 50 ms.
1080p60 does not exist for these uploads: every listed video format tops out at 1080p, 30 fps. R-VI-01 is met at its accepted 30 fps level, not the preferred 60 fps.

## Intake findings (R-VI-02)
- Both uploads are condensed official replays, not full broadcasts: commercials removed (0 of 177 sampled frames show commercials), halftime cut to about 3 min, timeouts kept only as short huddle or bench shots.
- No live play appears cut: the game clock never ran down more than the video time between consecutive scorebug samples (68 and 72 checks). Both full 40-minute games are present.
- UConn: video 86.5 min against 134.4 min tip to final in the play-by-play wall clock; 1st half 37.1 min of video, 2nd half 44.4 min.
- Louisville: 89.9 min; 1st half about 32.6 min, 2nd half about 51 min.
- Dropped or frozen frames: no timestamp gaps in either file. UConn: no freezes of 2 s or more. Louisville: 4 freezes; 3 are static "game summary" graphics (normal), 1 is a 2.3 s frozen overhead-camera feed during live 2nd-half play (video 2302.6-2304.9 s), which is a source problem, not a download problem.
- Black: no black segment of 0.3 s or more (UConn frame 0 is black).
- Letterboxing: none (1920x1080 active picture).
- Overlays: CBS / March Madness scorebug along the bottom (x 124, y 946, w 1676, h 84), stat and record straps directly above it, a different break bug, a compact corner bug, sponsor lower-thirds, a "connected cam" logo on the overhead camera, full-screen graphics.

## Scorebug audit (177 sampled frames, 1 per 60 s)
- Full in-game bug in 77.4% of samples, any bug in 83.1%; never in replays (0 of 17); in 93 of 95 main wide shots.
- Field availability over all samples: score 81.9%, period 81.4%, game clock 79.7%, shot clock 71.8%, team fouls 77.4%, bonus label 77.4%, timeouts left 77.4% (4 bars per team), alternating-possession arrow 77.4%.
- Timeout bars matched every team timeout in the UConn play-by-play, including a coach's challenge that restored a timeout.
- "POSS" in the bug is the alternating-possession arrow, not ball possession.

## Made-basket lag (UConn, first 10 made field goals)
Lags in s (ball through the net to scorebug digit change start): 1.965, 2.035, 1.901, 2.068, 1.831, 1.671, 2.331, 1.498, 2.604, 1.721. Mean 1.963 s, median 1.933 s, SD 0.324 s, range 1.498-2.604 s. All 10 makes were shown live with the rim and net in view; the rim stays sharp at 29.97 fps, the ball is motion-blurred for 1-2 frames.

## Problems and open points
1. 60 fps is not available for these games; anything tuned for 60 fps (R-MB-04's +/-3 frames = +/-0.05 s) has only 1.5 frames of tolerance at 30 fps.
2. yt-dlp ran without a JavaScript runtime and warned that some formats may be missing. All 1080p formats (VP9, AV1, H.264) were listed, so nothing above 1080p is likely, but it was not checked with a JS runtime.
3. The registry has no columns for hash or fps (R-FD-09 asks for them in the registry row). They are only in `video_manifest.csv` for now.
4. Condensed replays drop commercials and most of timeouts and halftime, so timing work that needs broadcast wall clock (for example dead-ball durations or real timeout lengths) cannot use video time.
5. Louisville has a 2.3 s frozen camera feed in live play and a 1 s game clock correction (4:06 then 4:07). Both are flagged for review.
6. The arena shot clock above the backboard resets at ring contact, sometimes before the ball goes through (2 of 9 makes measured), so it cannot stand in for the make frame.
