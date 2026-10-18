# Data lives in Google Drive

Nothing in this folder is committed except this file. Video and processed data are kept in one Drive folder:

| Drive path | Contents |
| --- | --- |
| `raw_video/<season>/<date>_<opponent>_<source>.mp4` | Original recordings; never edited or overwritten |
| `registry/` | Games, rosters, player cards, availability log |
| `processed/<game_id>/<version>/` | Tracks, events, features as Parquet |
| `labels/` | Review corrections with who, when and model version |
| `models/<name>/<version>/` | Checkpoints and their evaluation reports |
| `reports/` | Per-game and per-season outputs |

Size estimate: about 5.4 GB per 2-hour 1080p game.
