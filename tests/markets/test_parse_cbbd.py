"""CBBD parser on a SYNTHETIC fixture shaped like the OpenAPI 1.30.1 schemas (GameInfo, GameLines, GameLineInfo).
No real CBBD response exists yet (no key); replace with a saved raw body after the first keyed call.
new-MK-13 (pick'em null), new-MK-14 (integer lines), R-MK-03/04 via finalise().
"""
import math

from msu_alpha.markets.models import Market, SnapshotLabel
from msu_alpha.markets.parse import finalise
from msu_alpha.markets.sources import cbbd
from msu_alpha.markets.timeutil import parse_utc

TEAMS = [{"id": 1, "sourceId": "127", "school": "Michigan State"},
         {"id": 2, "sourceId": "96", "school": "Kentucky"},
         {"id": 3, "sourceId": "130", "school": "Michigan"}]
GAMES = [
    {"id": 9001, "sourceId": "401825481", "season": 2026, "startDate": "2025-11-19T02:00:00.000Z",
     "neutralSite": True, "conferenceGame": False, "status": "final", "homeTeamId": 2, "awayTeamId": 1,
     "homePoints": 77, "awayPoints": 83},
    {"id": 9002, "sourceId": "401860050", "season": 2026, "startDate": "2026-02-01T19:00:00.000Z",
     "neutralSite": False, "conferenceGame": True, "status": "final", "homeTeamId": 1, "awayTeamId": 3,
     "homePoints": 70, "awayPoints": 70},
    {"id": 9003, "sourceId": None, "season": 2026, "startDate": "2026-02-02T19:00:00.000Z",
     "homeTeamId": 1, "awayTeamId": 3},
]
LINES = [
    {"gameId": 9001, "season": 2026, "seasonType": "regular", "startDate": "2025-11-19T02:00:00.000Z",
     "homeTeamId": 2, "homeTeam": "Kentucky", "awayTeamId": 1, "awayTeam": "Michigan State",
     "lines": [{"provider": "ESPN BET", "spread": -3.5, "overUnder": 151.5, "homeMoneyline": -175,
                "awayMoneyline": 150, "spreadOpen": -2.5, "overUnderOpen": 149.0}]},
    {"gameId": 9002, "season": 2026, "seasonType": "regular", "startDate": "2026-02-01T19:00:00.000Z",
     "homeTeamId": 1, "homeTeam": "Michigan State", "awayTeamId": 3, "awayTeam": "Michigan",
     "lines": [{"provider": "ESPN BET", "spread": None, "overUnder": 140.0, "homeMoneyline": -110,
                "awayMoneyline": -110, "spreadOpen": None, "overUnderOpen": None}]},
    {"gameId": 9003, "season": 2026, "homeTeamId": 1, "awayTeamId": 3,
     "lines": [{"provider": "ESPN BET", "spread": -5.0, "overUnder": 141.0}]},
]
FETCHED = parse_utc("2026-10-18T12:00:00Z")


def _parse():
    teams = cbbd.team_map(TEAMS)
    games, missing = cbbd.game_map(GAMES, teams)
    return games, missing, cbbd.parse_lines(LINES, games, teams, FETCHED, raw_ref="sha-test")


def test_bridge_to_espn_ids():
    games, missing, _ = _parse()
    assert games["9001"].game_id == "401825481" and games["9001"].home_team_id == "96"
    assert missing == ["9003"]


def test_spreads_per_team_never_home_away():
    _, _, rows = _parse()
    close = [r for r in rows if r.source_event_id == "9001" and r.market == Market.SPREAD
             and r.snapshot_label == SnapshotLabel.CLOSE_REPORTED]
    assert {(r.team_id, r.line) for r in close} == {("96", -3.5), ("127", 3.5)}
    assert all(r.observed_post_event for r in close)
    opens = [r for r in rows if r.source_event_id == "9001" and r.snapshot_label == SnapshotLabel.OPEN_REPORTED]
    assert {r.line for r in opens if r.market == Market.TOTAL} == {149.0}


def test_null_spread_with_total_is_possible_pickem():
    _, _, rows = _parse()
    g2 = [r for r in rows if r.source_event_id == "9002"]
    assert not [r for r in g2 if r.market == Market.SPREAD]
    totals = [r for r in g2 if r.market == Market.TOTAL]
    assert totals and all("possible_pickem" in r.dq_flags for r in totals)
    assert all(r.line_is_integer for r in totals)


def test_unmatched_game_kept_with_null_id():
    _, _, rows = _parse()
    g3 = [r for r in rows if r.source_event_id == "9003"]
    assert g3 and all(r.game_id is None for r in g3)


def test_finalise_devigs_moneylines_and_keeps_unmatched_flagged():
    games, _, rows = _parse()
    by_espn = {g.game_id: g for g in games.values()}
    res = finalise(rows, by_espn)
    assert res.quarantine == []
    ml = [r for r in res.rows if r.source_event_id == "9001" and r.market == Market.MONEYLINE]
    assert len(ml) == 2
    assert math.isclose(sum(r.fair_prob_power for r in ml), 1.0, abs_tol=1e-9)
    assert math.isclose(sum(r.fair_prob_shin for r in ml), 1.0, abs_tol=1e-9)
    uk = next(r for r in ml if r.team_id == "96")
    assert round(uk.fair_prob_power, 3) == 0.620 and round(uk.fair_prob_shin, 3) == 0.618
    assert all("unmatched" in r.dq_flags for r in res.rows if r.game_id is None)
    spreads = [r for r in res.rows if r.market == Market.SPREAD]
    assert all(r.fair_prob_power is None for r in spreads)     # CBBD gives no spread prices
