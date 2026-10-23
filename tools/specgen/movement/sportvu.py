"""Load 2015-16 NBA SportVU logs (validation tier V1b/V2) into movement-grammar Tracks.

The data lives in the private folder (~/MSU-Alpha-3-private/data/research/sportvu_2015_16/json),
never in the repo. SportVU: 25 Hz, feet, origin at a court corner, x along the 94 ft length,
y across the 50 ft width, ball z in feet. We convert to metres, resample to 29.97 fps and put each
possession-like chunk in the attacked-rim frame (rim 5.25 ft = 1.6002 m from the end line, the same
set-back as NCAA). NBA court lines differ (arc 23.75 ft); named-spot labels on NBA data must use an
NBA court profile, so this loader only provides positions.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from mvlib import DT, Track

FT = 0.3048
RIM_FROM_END_FT = 5.25
SV_DT = 0.04


def load_game(path):
    return json.loads(Path(path).read_text())


def unique_moments(game):
    """All moments of a game, de-duplicated by (period, game clock) and sorted in time."""
    seen, out = set(), []
    for ev in game["events"]:
        for m in ev["moments"]:
            key = (m[0], round(m[2], 2))
            if key in seen:
                continue
            seen.add(key)
            out.append(m)
    out.sort(key=lambda m: (m[0], -m[2]))
    return out


def chunks(moments, min_s=6.0):
    """Split into continuous stretches (same period, game clock steps of ~0.04 s, 10 players + ball)."""
    cur, out = [], []
    for m in moments:
        ok = len(m[5]) == 11
        if cur and (m[0] != cur[-1][0] or abs((cur[-1][2] - m[2]) - SV_DT) > 0.02 or not ok):
            if len(cur) * SV_DT >= min_s:
                out.append(cur)
            cur = []
        if ok:
            cur.append(m)
    if len(cur) * SV_DT >= min_s:
        out.append(cur)
    return out


def half_of(period):
    """Teams switch ends at half time and keep the second-half ends in overtime."""
    return 1 if period <= 2 else 2


def team_ends(moments, min_votes=200):
    """Which end each team attacks in each half, from half-court sets.

    In a settled half-court set all ten players are in one half; the defenders stand between the
    attackers and the rim, so the team with the larger mean distance to that end's rim is the
    offense attacking that end. Votes over every such moment of a half give
    {(half, team_id): 'x0' | 'x94'}; a half with fewer than min_votes settled moments is left out.
    Uses tracking only (no play-by-play), so it works on any SportVU game.
    """
    votes = {}
    for m in moments:
        if len(m[5]) != 11:
            continue
        pl = m[5][1:]
        xs = np.array([p[2] for p in pl])
        if np.all(xs > 47.0):
            end, rim_x = "x94", 94.0 - RIM_FROM_END_FT
        elif np.all(xs < 47.0):
            end, rim_x = "x0", RIM_FROM_END_FT
        else:
            continue
        teams = {}
        for p in pl:
            teams.setdefault(p[0], []).append(np.hypot(p[2] - rim_x, p[3] - 25.0))
        if len(teams) != 2:
            continue
        (ta, da), (tb, db) = teams.items()
        off = ta if np.mean(da) > np.mean(db) else tb
        key = (half_of(m[0]), off, end)
        votes[key] = votes.get(key, 0) + 1
    out = {}
    for h in (1, 2):
        for t in {k[1] for k in votes if k[0] == h}:
            v94, v0 = votes.get((h, t, "x94"), 0), votes.get((h, t, "x0"), 0)
            if v94 + v0 >= min_votes:
                out[(h, t)] = "x94" if v94 > v0 else "x0"
    return out


def to_tracks(chunk, sigma_p=0.0, ends=None):
    """One continuous stretch -> (tracks, offense_team_id, meta) in the attacked-rim frame.

    Without `ends`: offense = the team of the player nearest the ball most often; attacked basket =
    the end the ball spends most time nearer to (the original rule; it disagrees with the
    play-by-play scoring end in about a quarter of chunks, mostly transition stretches).
    With `ends` from team_ends(): attacked basket = the end the ball spends most time nearer to,
    and offense = the team that attacks that end in this half. Positions are resampled from 25 Hz
    to 29.97 fps (linear).
    """
    T = len(chunk)
    t_src = np.arange(T) * SV_DT
    n = int((t_src[-1]) / DT) + 1
    t_dst = np.arange(n) * DT
    ids = [(e[0], e[1]) for e in chunk[0][5]]
    arr = {}
    for k, (tid, pid) in enumerate(ids):
        xs = np.array([m[5][k][2] for m in chunk])
        ys = np.array([m[5][k][3] for m in chunk])
        same = all(m[5][k][1] == pid for m in chunk)
        if not same:
            return None
        arr[(tid, pid)] = (xs, ys)
    bz = np.array([m[5][0][4] for m in chunk])
    bx, by = arr[ids[0]]
    # offense: team of nearest player to the ball, majority vote
    votes = {}
    for i in range(T):
        best, bd = None, 1e9
        for (tid, pid) in ids[1:]:
            d = (arr[(tid, pid)][0][i] - bx[i]) ** 2 + (arr[(tid, pid)][1][i] - by[i]) ** 2
            if d < bd:
                best, bd = tid, d
        votes[best] = votes.get(best, 0) + 1
    off = max(votes, key=votes.get)
    right_end = np.mean(bx > 47.0) > 0.5  # attacked basket at x = 94 ft end
    frame_rule = "nearest_player"
    if ends:
        h = half_of(chunk[0][0])
        end = "x94" if right_end else "x0"
        owner = [t for (hh, t), e in ends.items() if hh == h and e == end]
        if len(owner) == 1:
            off, frame_rule = owner[0], "team_ends"
    tracks = []
    for (tid, pid) in ids:
        xs, ys = arr[(tid, pid)]
        if right_end:
            fx = (94.0 - RIM_FROM_END_FT - xs) * FT  # distance from rim along the length -> our y
            fy = (ys - 25.0) * FT  # across -> our x (attacker's right when facing the x=94 rim is y<25? see sign below)
            X, Y = -fy, fx
        else:
            fx = (xs - RIM_FROM_END_FT) * FT
            fy = (ys - 25.0) * FT
            X, Y = fy, fx
        X = np.interp(t_dst, t_src, X)
        Y = np.interp(t_dst, t_src, Y)
        role = "ball" if tid == -1 else "player"
        oid = "ball" if tid == -1 else f"{tid}_{pid}"
        team = "O" if tid == off else ("B" if tid == -1 else "D")
        z = np.interp(t_dst, t_src, bz) * FT if tid == -1 else None
        tracks.append(Track(oid, X, Y, np.full(n, max(sigma_p, 0.05)), team=team, role=role, z=z))
    meta = {"period": chunk[0][0], "clock_start": chunk[0][2], "clock_end": chunk[-1][2], "offense_team": off,
            "attacked_end": "x94" if right_end else "x0", "frame_rule": frame_rule,
            "ball_z_ft": np.interp(t_dst, t_src, bz)}
    return tracks, off, meta
