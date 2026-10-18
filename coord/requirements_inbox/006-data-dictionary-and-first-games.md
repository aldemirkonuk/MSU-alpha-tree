# Requirements inbox 006 · Data dictionaries and first games (prompt 003)

Written 2026-10-18 by the Mac session (msu-colab). Everything below is a proposal for the requirements session; nothing in the live doc was edited. (Note: an earlier, unrelated file `006-markets-requirements.md` also uses number 006.)

## What was produced (repo, add-only)

| Workflow | Output | Size |
|---|---|---|
| W1 | `docs/data/dictionary_players.md`, `docs/data/templates/player_card_template.csv` | 303 fields in 16 families; proposals new-PC-1..5 |
| W1 | MSU 2026-27 cards (private, `MSU-Alpha-3-private/data/licensed/players/msu_2026-27_cards.csv`) | 15 players; 191 of 303 columns filled for at least one player, plus CBBD roster/recruit/portal columns |
| W2 | `docs/data/dictionary_games.md`, `schema/tables/*.yaml` (91 core tables) | 2,368 columns; 452 of 518 requirement IDs cited; proposals new-DS-1, new-SY-1, new-FD-1 |
| W2.5 | `docs/data/dictionary_state.md`, 13 state tables in `schema/tables/`, `config/invariants.yaml` | R-IV-01..16 + new-IV-01..34; 13 rule-number corrections |
| W2 | `docs/data/source_field_map.md` | CBBD 40 endpoints / 720 fields; ESPN files, hoopR, Torvik, KenPom, Kaggle, EvanMiya; verified section with 29 corrections |
| Goal | `docs/data/game_ontology_coverage.md`, `config/game_ontology.yaml`, inbox 007 | 576 leaf concepts in 13 domains: 465 covered, 87 partial, 24 missing; 93 proposed requirements incl. a new family R-RL (rules layer) |
| W3 | `results/w3_intake/` (manifest, intake check, scorebug summary, made-basket lag; no images) and `registry/games.csv` footage cells for 401856571 and 401856531 | 2 games |
| Tools | `tools/specgen/` (generators for all of the above) | specs only |

## Verification calls made (within budget)

- CBBD: 21 calls of 50 (key stored in the macOS keychain, service `CBBD_API_KEY`; 979 of 1,000 left this month). Raw responses private.
- KenPom tool (Parse.bot): 4 calls of 30, approved by Aldemir in chat on 18 Oct. Season-end tables only (2024-2026), all strings, no as-of date → reference/prior only, never a same-season pre-game input.
- ESPN: no new requests. The Job D files were copied to private quarantine with a "reference only, never model input" README.

Key verified facts (detail in `source_field_map.md`, "Verified against real responses"): CBBD `sourceId` = ESPN ID for games, teams and players; play/sub/lineup athlete IDs are CBBD IDs (roster lookup needed); conference string is "Big Ten" ("B1G" returns nothing); spread = home line, negative = home favoured (42/43 agree with moneyline); clock whole seconds only; shot x/y in tenths of a foot on a full court (rims at x 52.5/887.5) → convert to metres; venues carry no coordinates, capacity or elevation; roster heights in inches/pounds; no source gives the shot clock or timeouts remaining (scoreboard reading needed).

## First games (W3)

| Game | File | Spec | Length | Notes |
|---|---|---|---|---|
| 2026-03-27 UConn 67-63 MSU (Sweet 16) | `2026-03-27_uconn_youtube.webm` | VP9 1920×1080, constant 29.97 fps, Opus 48 kHz, 1.82 GB | 5,188 s | Official March Madness channel; condensed replay (no commercials), full 40 min of play |
| 2026-03-21 MSU 77-69 Louisville (2nd round) | `2026-03-21_louisville_youtube.webm` | same, 1.97 GB | 5,394 s | One real 2.3 s freeze of the overhead camera at video 2,302.6 s |

- 1080p60 does not exist for these games (max 1080p ~30 fps).
- Scorebug (177 samples, one per 60 s): full scorebug in 77.4% of frames, 93 of 95 wide game shots, 0 of 17 replays; fields shown: score, period, game clock, shot clock, team fouls, bonus, timeouts left (bars), and a "POSS" marker that is the alternating-possession arrow, not ball possession.
- Made-basket lag (first 10 UConn makes): net → scorebug change 1.50-2.60 s, mean 1.963 s, median 1.933 s; the digit change takes 0.30 s more. The arena shot clock can reset on rim contact before the make.
- Files are staged privately in `~/MSU-Alpha-3-private/raw_video/2025-26/`; Google Drive for desktop was not running, so the move to `MyDrive/MSU-Alpha-3/raw_video/2025-26/` is pending.

## Decisions needed from Aldemir (one line each)

1. R-DS-14 still lists the KenPom tool as blocked; record your chat approval (and its licence class: reference only?).
2. Torvik, NBA combine and EvanMiya values: model input or reference only?
3. Kaggle March Madness archive (contains KenPom/Torvik columns): reference only, private copy only?
4. hoopR ESPN-based prebuilt files: model input or reference only (ESPN terms)?
5. Keep the ESPN-pulled `registry/*.csv` in the public repo, or rebuild them from CBBD? Drop `headshot_url` (no-face rule)?
6. One player key: `player_id` (ESPN athlete ID) or W1's `player_uid`?
7. Accept 30 fps footage and restate R-MB-04 in frames at 30 fps (±0.05 s ≈ ±1.5 frames)?
8. Add hash, fps, resolution, codec and length columns to `registry/games.csv` (R-FD-09)?
9. Shrink the R-SB-03 scoreboard-lag window from 15 s (all 10 measured lags < 2.7 s)?
10. Adopt the 13 rule-number corrections and new-IV-01..34 in `config/invariants.yaml`?
11. Adopt the new family R-RL (rules edition per game) and drop the foul type `intentional` (not a 2026-27 class)?
12. Change R-IV-02 to "two or three officials (three expected in D-I)"?
13. Which wording of Rule 7-3.2.b (2025-26 change summary vs 2026-27 book) should the throw-in check follow?
14. Approve the extra `state_corrections` table and a third pass value `pbp_only`?
15. Approve the proposed global-metadata additions (pass, video_id, shot_clock_status, per-team bonus, timeouts by length, challenge state, possession_arrow, reverse_angle)?
16. Store birth date on player cards, or only age at tip?
17. Start Google Drive for desktop so the videos and private data can be moved into MyDrive/MSU-Alpha-3/.
18. Rotate the CBBD and Parse keys (both appeared in chat in plain text).

Further one-line questions are at the end of each dictionary file and in inbox 007.
