# Registry

- `games.csv`: every Michigan State game 2021-22 to 2025-26 from ESPN's public API (179 games), newest first. Big Ten tournament games appear as `regular` in ESPN; the `notes` column names them. `footage_source` and `footage_path` are filled as video is collected.
- `rosters.csv`: **incomplete**. ESPN's roster endpoint does not return full historical rosters (2025-26 is missing Carson Cooper, for example). Rosters will be rebuilt from per-game box scores (task to come).

Rebuild: `PYTHONPATH=src python -m msu_alpha.data.espn_registry --out registry`
