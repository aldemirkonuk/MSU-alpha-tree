"""SportVU 2015-16 game -> identity-harness Truth (true ids known), cached as .npz in the private folder.

Native 25 Hz, absolute court frame in metres (x along the 94 ft length, y across). Moments are
de-duplicated by wall clock (not by game clock as sportvu.unique_moments does: that collapses every
dead ball to one frame and breaks the sequence into 0.04 s pieces) and sorted by wall clock; every
wall-clock jump > dead_gap_s and every period change is a gap (a camera cut for the harness).
Uses load_game from tools/specgen/movement/sportvu.py.
The cache holds derived positions of licensed-unknown data: it is written only under
~/MSU-Alpha-3-private, never in the repo.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "movement"))
sys.path.insert(0, str(HERE))

from idlib import P  # noqa: E402
from obsmodel import Truth  # noqa: E402

FT = 0.3048
SV_DT = 0.04
TELEPORT_M = 1.0  # m in one 0.04 s frame (25 m/s): not a human movement
PRIVATE = Path.home() / "MSU-Alpha-3-private"
DATA = PRIVATE / "data" / "research" / "sportvu_2015_16" / "json"
CACHE = PRIVATE / "work" / "identity_harness_2026-10-25" / "cache"
REPO = HERE.parents[2]


def _guard(path: Path):
    if Path(path).resolve().is_relative_to(REPO):
        raise SystemExit(f"refusing to write derived SportVU data inside the repo: {path}")


def build(json_path, cache_dir=CACHE):
    from mvlib import DT as _  # noqa: F401  (import check: movement tools importable)
    from sportvu import load_game

    game = load_game(json_path)
    gid = str(game.get("gameid", Path(json_path).stem))
    roster, team_ids = {}, []
    for ev in game["events"]:
        for side in ("visitor", "home"):
            tm = ev[side]
            if tm["teamid"] not in team_ids:
                team_ids.append(tm["teamid"])
            for p in tm["players"]:
                roster.setdefault(p["playerid"], (tm["teamid"], p.get("jersey", ""), p.get("position", "")))
    pids = sorted(roster, key=lambda k: (team_ids.index(roster[k][0]), k))
    pidx = {p: i for i, p in enumerate(pids)}
    seen = {}
    for ev in game["events"]:
        for m in ev["moments"]:
            if len(m[5]) == 11:
                seen.setdefault(m[1], m)
    moms = [seen[k] for k in sorted(seen)]
    del game
    F, N = len(moms), len(pids)
    pos = np.full((F, N, 2), np.nan, dtype=np.float32)
    ball = np.zeros((F, 2), dtype=np.float32)
    wall = np.zeros(F)
    period = np.zeros(F, dtype=np.int16)
    clock = np.zeros(F, dtype=np.float32)
    for f, m in enumerate(moms):
        period[f], wall[f], clock[f] = m[0], m[1], m[2]
        ball[f] = (m[5][0][2] * FT, m[5][0][3] * FT)
        for e in m[5][1:]:
            i = pidx.get(e[1])
            if i is not None:
                pos[f, i] = (e[2] * FT, e[3] * FT)
    gap = np.zeros(F, dtype=bool)
    gap[0] = True
    gap[1:] = (np.diff(period) != 0) | (np.abs(np.diff(wall) / 1000.0 - SV_DT) > P["dead_gap_s"] - SV_DT)
    # SportVU's own id artefacts: at some substitutions the source re-assigns ids without a wall-clock gap
    # (players 'teleport' between frames). The on-court set changing, or any player moving > teleport_m in one
    # frame, is treated as a gap (a cut), so the harness never scores the source's own swaps.
    on = ~np.isnan(pos[:, :, 0])
    step = np.nanmax(np.hypot(*(np.diff(pos, axis=0)).transpose(2, 0, 1)), axis=1)
    gap[1:] |= (on[1:] != on[:-1]).any(1) | (np.nan_to_num(step) > TELEPORT_M)
    team = np.array([team_ids.index(roster[p][0]) for p in pids], dtype=np.int8)
    jersey = np.array([str(roster[p][1]) for p in pids])
    position = np.array([str(roster[p][2]) for p in pids])
    cache_dir = Path(cache_dir)
    _guard(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = cache_dir / f"{gid}.npz"
    np.savez_compressed(out, pos=pos, ball=ball, gap=gap, team=team, jersey=jersey, position=position, pid=np.array(pids),
                        period=period, clock=clock)
    return out


def load(gid, cache_dir=CACHE, max_minutes=0.0):
    z = np.load(Path(cache_dir) / f"{gid}.npz")
    F = z["pos"].shape[0]
    if max_minutes:
        F = min(F, int(max_minutes * 60 / SV_DT))
    pos = z["pos"][:F].astype(float)
    tr = Truth(SV_DT, pos, z["team"].astype(int), [str(j) for j in z["jersey"]], [str(p) for p in z["position"]],
               z["ball"][:F].astype(float), z["gap"][:F].copy(), {"game": gid, "n_frames": F})
    return tr


if __name__ == "__main__":
    for p in sys.argv[1:] or sorted(DATA.glob("*.json")):
        print(build(p))
