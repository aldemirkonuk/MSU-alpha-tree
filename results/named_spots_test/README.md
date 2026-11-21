# Named-spot dictionary tests

Every test number on `docs/data/named_spots.md` is read from a file in this folder, and every file here is written by a command in the repo. Run the commands from the repo root with the test Python. `gen_doc.py` refuses to build the page from a `check_summary.json` or `proptest_summary.json` that was made from other rules than the YAML now holds (they carry `rules_sha256`, the hash of the YAML without its journal).

| File | Command | What it holds |
|---|---|---|
| `check_summary.json` | `python tools/specgen/named_spots/check.py --step 0.05 --write-summary` (about 1 minute) | Probes: every entry with an exact rule has at least one executed probe; counts of static, context and value probes; 0 failures. Lints: 0 findings. Thin regions: every region thinner than its boundary buffer is on the probability-only list. Partitions on the 0.05 m grid of 231,401 points: court_region covers every point; the crosswalks cover exactly the in-bounds floor (175,070 points); 0 overlaps in every scheme. |
| `proptest_summary.json` | `python tools/specgen/named_spots/proptest.py --write-summary` (several minutes) | Seeded property tests, full run: cases per property and the failed properties (none). The script exits non-zero on any failure. |
| `speed.json` | `python tools/specgen/named_spots/bench.py --write-summary` | Time to evaluate every exact rule for 10 players and the ball, per frame (median and 95th percentile), with the date and a note on the machine load. |
| `cbbd_summary.json` | `python tools/specgen/named_spots/cbbd_check.py "<private>/data/licensed/cbbd/2026-10-19/plays/*.json" "<private>/data/licensed/cbbd/2026-10-18/03_plays_game.json" --out results/named_spots_test/cbbd_summary.json` | Aggregates only, from 34 licensed CBBD game files that stay in the private folder: located MSU 2025-26 field-goal attempts, labels per scheme, two-vs-three agreement, how far the disagreeing shots are from the three-point line (count, count within 0.05 m, farthest), and how far above-the-break threes are behind the arc. |
| `proptest_0.3.2.txt` | old `proptest.py` of version 0.3.2 (kept as history) | The stored output of the first property test. It lists 24 kinds of hit; 22 (`nan_ctx:*`) were false alarms of that script, which set `bx` to NaN on entries that use `by` only. The script was rewritten in 0.3.4 (audit finding NS-06) and this file is no longer quoted. |

Checks that need no stored file:

- `python -m pytest tests/test_named_spots.py tests/test_geometry.py`: the probes and lints, a 0.25 m partition grid, a reduced property test, broken copies of the dictionary that must fail, and the comparison of the stored page and picture with fresh ones.
- `python tools/specgen/named_spots/gen_doc.py --check` and `python tools/specgen/named_spots/gen_svg.py --check`: fail when `docs/data/named_spots.md` or `docs/data/named_spots_court.svg` differs from a fresh one.

Notes:

- The scenario runs made for version 0.1.0 (man-to-man, zones, presses, restarts) were done in a session scratchpad and are not in the repo. Their counts are no longer quoted. Since 0.3.4 every ball-relative entry is tested by its own probes with a stored context (`probe_ctx`), which `check.py` runs.
- CBBD lateral orientation (2026-10-20): checked on UConn video frames about 1.3 s before four made baskets (private audit file). All four shooters stand on the side opposite to the first transform, so CBBD's y axis points to the attacker's left; `cbbd_check.py` negates it. Only left and right labels change.
