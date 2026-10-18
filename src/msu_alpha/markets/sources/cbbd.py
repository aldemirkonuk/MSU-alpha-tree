"""CollegeBasketballData.com parsers (design 1.1; OpenAPI 1.30.1 schemas GameInfo, GameLines, GameLineInfo).

Bridge to ESPN: /games `sourceId` = ESPN event ID; /teams `sourceId` = ESPN team ID.
CBBD keeps one value per game x provider (current/close plus open) with no timestamp, so rows carry
snapshot_label open_reported / close_reported (or sweep before tip) and observed_post_event for finished games.

Known quirks handled here:
- A pick'em spread of 0 comes back as null (JavaScript truthiness in the CBBD service): spread null with a
  total present -> no spread row, and the total rows get flag C-09 `possible_pickem` (new-MK-13).
- Spread sign is unverified for CBBD; it is read as the home team's line (negative = home favoured) and the
  XS-4 moneyline-vs-spread check will expose a flipped convention on the first keyed pull.
- CBBD gives no prices for spreads and totals, so those rows have implied probability null (no de-vig).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import Game, Market, Side, SnapshotLabel, SnapshotRow, Source
from ..odds import parse_american
from ..timeutil import parse_utc

FINAL = {"final", "completed"}


def team_map(teams: list[dict[str, Any]]) -> dict[str, str]:
    """CBBD team id -> ESPN team id (from /teams sourceId)."""
    return {str(t["id"]): str(t["sourceId"]) for t in teams if t.get("sourceId") not in (None, "")}


def game_map(games: list[dict[str, Any]], teams: dict[str, str]) -> tuple[dict[str, Game], list[str]]:
    """CBBD game id -> Game keyed on the ESPN event ID. Returns (map, CBBD ids with no usable sourceId)."""
    out: dict[str, Game] = {}
    missing: list[str] = []
    for g in games:
        sid = g.get("sourceId")
        home, away = teams.get(str(g.get("homeTeamId"))), teams.get(str(g.get("awayTeamId")))
        if sid in (None, "") or not home or not away or not g.get("startDate"):
            missing.append(str(g.get("id")))
            continue
        out[str(g["id"])] = Game(
            game_id=str(sid), season=int(g["season"]), home_team_id=home, away_team_id=away,
            scheduled_tip_utc=parse_utc(g["startDate"]), neutral_site=bool(g.get("neutralSite")),
            conference_game=bool(g.get("conferenceGame")), status=str(g.get("status") or "scheduled").lower(),
            home_score=_int(g.get("homePoints")), away_score=_int(g.get("awayPoints")),
        )
    return out, missing


def parse_lines(lines: list[dict[str, Any]], games: dict[str, Game], teams: dict[str, str],
                fetched_at: datetime, raw_ref: str) -> list[SnapshotRow]:
    rows: list[SnapshotRow] = []
    for gl in lines:
        cbbd_id = str(gl["gameId"])
        game = games.get(cbbd_id)
        home = teams.get(str(gl.get("homeTeamId")))
        away = teams.get(str(gl.get("awayTeamId")))
        finished = game is not None and (game.status in FINAL or game.home_score is not None)
        for info in gl.get("lines") or []:
            book = str(info.get("provider") or "unknown")
            base = dict(source=Source.CBBD, book=book, snapshot_time_utc=parse_utc(fetched_at),
                        fetched_at_utc=parse_utc(fetched_at), season=int(gl["season"]),
                        source_event_id=cbbd_id, raw_ref=raw_ref, game_id=game.game_id if game else None,
                        observed_post_event=finished)
            current = SnapshotLabel.CLOSE_REPORTED if finished else SnapshotLabel.SWEEP
            for label, spread, total in (
                (current, info.get("spread"), info.get("overUnder")),
                (SnapshotLabel.OPEN_REPORTED, info.get("spreadOpen"), info.get("overUnderOpen")),
            ):
                if spread is not None and home and away:
                    s = float(spread)
                    rows.append(SnapshotRow(**base, market=Market.SPREAD, side=Side.TEAM, team_id=home,
                                            line=s, snapshot_label=label))
                    rows.append(SnapshotRow(**base, market=Market.SPREAD, side=Side.TEAM, team_id=away,
                                            line=-s if s != 0 else 0.0, snapshot_label=label))
                if total is not None:
                    t = float(total)
                    for side in (Side.OVER, Side.UNDER):
                        r = SnapshotRow(**base, market=Market.TOTAL, side=side, line=t, snapshot_label=label)
                        if spread is None:
                            r.flag("C-09")
                            r.flag("possible_pickem")
                        rows.append(r)
            hm, am = parse_american(info.get("homeMoneyline")), parse_american(info.get("awayMoneyline"))
            if hm is not None and am is not None and home and away:
                rows.append(SnapshotRow(**base, market=Market.MONEYLINE, side=Side.TEAM, team_id=home,
                                        price_american=hm, snapshot_label=current))
                rows.append(SnapshotRow(**base, market=Market.MONEYLINE, side=Side.TEAM, team_id=away,
                                        price_american=am, snapshot_label=current))
    return rows


def _int(x: Any) -> int | None:
    try:
        return None if x is None else int(x)
    except (TypeError, ValueError):
        return None
