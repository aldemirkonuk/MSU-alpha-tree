# Play-by-play scripts behind transition_full.md "Additions 2026-10-18"

Copied from the research session's scratch folder on 2026-10-18 so the college numbers in the Additions section can be reproduced. The raw ESPN play-by-play downloads (about 400 MB) were not kept; `fetch.py` and `ids.py` re-download them from ESPN's public endpoints.

- `ids.py`: lists Division I game IDs per season.
- `fetch.py`, `run.py`: download game summaries and play-by-play.
- `parse.py`: turns play-by-play into possessions with start type and elapsed time.
- `analyze.py`, `bigten.py`, `extra.py`: league, Big Ten and MSU tables used in the Additions section.

Run them from one working folder: they read and write relative files (ids_<season>.json, poss_<season>*.jsonl, box_<season>*.jsonl). bigten.py also needs a team CSV path passed in.

> Warning 2026-10-18: `coord/BOARD.md` records that ESPN's terms forbid automated collection, and that project data should come from hoopR prebuilt releases and CBBD instead. These scripts called ESPN's public endpoints for about 11,500 games during research. Do not re-run them against ESPN; port `parse.py`/`analyze.py` to hoopR prebuilt play-by-play files or CBBD before reusing them. The college numbers in transition_full.md "Additions 2026-10-18" should be treated as provisional until reproduced from an allowed source. Decision for Aldemir.
