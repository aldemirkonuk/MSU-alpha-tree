"""Snapshot planning (design section 2; R-MK-05).

Turns a game list into dated jobs: T-24 h, T-1 h and close for every MSU and Big Ten game, a game-day
sweep for first-half lines and props, and 1-minute prediction-market jobs for every MSU game from
T-10,800 s to final + 3,600 s. Pure planning: nothing here calls a source.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import Game
from .timeutil import eastern_date, iso_utc

MSU_TEAM_ID = "127"   # ESPN team ID for Michigan State
GAMEDAY_OFFSET_S = -10800


@dataclass(frozen=True)
class Job:
    job_id: str
    game_id: str
    label: str            # t-24h | t-1h | close | gameday | inplay_1m
    kind: str             # books | exchanges
    run_at_utc: datetime


def involves(game: Game, team_ids: set[str]) -> bool:
    return game.home_team_id in team_ids or game.away_team_id in team_ids


def plan_jobs(games: list[Game], big_ten_team_ids: set[str], schedule_cfg: dict,
              now: datetime | None = None, final_utc: dict[str, datetime] | None = None) -> list[Job]:
    offsets: dict[str, int] = schedule_cfg["offsets_s"]
    inplay = schedule_cfg["inplay"]
    final_utc = final_utc or {}
    scope = big_ten_team_ids | {MSU_TEAM_ID}
    jobs: list[Job] = []
    for g in games:
        if g.status in ("postponed", "canceled", "cancelled") or not involves(g, scope):
            continue
        tip = g.scheduled_tip_utc
        for label, off in offsets.items():
            jobs.append(Job(f"{g.game_id}:{label}", g.game_id, label, "books", tip + timedelta(seconds=off)))
        day = eastern_date(tip)   # first-half lines and props are posted on game day: sweep at T - 10,800 s
        jobs.append(Job(f"{g.game_id}:gameday:{day.isoformat()}", g.game_id, "gameday", "books",
                        tip + timedelta(seconds=GAMEDAY_OFFSET_S)))
        if involves(g, {MSU_TEAM_ID}):
            start = tip + timedelta(seconds=int(inplay["start_s"]))
            end = final_utc.get(g.game_id) or tip + timedelta(seconds=int(inplay["est_game_length_s"]))
            end = end + timedelta(seconds=int(inplay["end_after_final_s"]))
            t = start
            step = timedelta(seconds=int(inplay["interval_s"]))
            while t <= end:
                jobs.append(Job(f"{g.game_id}:inplay:{iso_utc(t)}", g.game_id, "inplay_1m", "exchanges", t))
                t += step
    if now is not None:
        jobs = [j for j in jobs if j.run_at_utc >= now]
    return sorted(jobs, key=lambda j: (j.run_at_utc, j.job_id))
