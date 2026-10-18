"""Regression tests for the four defects found by the data-engineer review (2026-10-18)."""
import hashlib
import json

import pytest

from msu_alpha.markets.config import REPO
from msu_alpha.markets.models import Market, Side, SnapshotLabel, SnapshotRow, Source
from msu_alpha.markets.parse import finalise
from msu_alpha.markets.raw_store import RawStore
from msu_alpha.markets.sources import cbbd
from msu_alpha.markets.store import PrivatePathError, SnapshotStore
from msu_alpha.markets.timeutil import parse_utc

T0 = parse_utc("2026-02-01T18:00:00Z")


def total_row(event_id, side):
    return SnapshotRow(source=Source.CBBD, book="ESPN BET", market=Market.TOTAL, side=side, snapshot_time_utc=T0,
                       fetched_at_utc=T0, season=2026, source_event_id=event_id, raw_ref="r", game_id=None,
                       line=140.0, snapshot_label=SnapshotLabel.SWEEP)


def test_unmatched_events_with_same_line_do_not_collide():
    rows = [total_row("e1", Side.OVER), total_row("e1", Side.UNDER),
            total_row("e2", Side.OVER), total_row("e2", Side.UNDER)]
    res = finalise(rows)
    assert res.quarantine == [] and len(res.rows) == 4


TEAMS = [{"id": 1, "sourceId": "127"}, {"id": 2, "sourceId": "96"}]
GAMES = [{"id": 9001, "sourceId": "401825481", "season": 2026, "startDate": "2025-11-19T02:00:00.000Z",
          "status": "final", "homeTeamId": 2, "awayTeamId": 1, "homePoints": 77, "awayPoints": 83}]
LINES = [{"gameId": 9001, "season": 2026, "homeTeamId": 2, "awayTeamId": 1,
          "lines": [{"provider": "ESPN BET", "spread": -3.5, "overUnder": 151.5, "homeMoneyline": -175,
                     "awayMoneyline": 150, "spreadOpen": -2.5, "overUnderOpen": 149.0}]}]


def test_cbbd_reported_rows_are_idempotent_across_pulls(tmp_path):
    teams = cbbd.team_map(TEAMS)
    games, _ = cbbd.game_map(GAMES, teams)
    pull1 = cbbd.parse_lines(LINES, games, teams, parse_utc("2026-10-18T12:00:00Z"), "a")
    pull2 = cbbd.parse_lines(LINES, games, teams, parse_utc("2026-10-19T12:00:00Z"), "b")
    assert {r.dedup_key() for r in pull1} == {r.dedup_key() for r in pull2}
    assert all(r.snapshot_time_utc == parse_utc("2025-11-19T02:00:00Z") for r in pull1)


def test_store_dedup_holds_across_runs(tmp_path):
    pytest.importorskip("pyarrow")
    store = SnapshotStore(tmp_path)
    rows = [total_row("e1", Side.OVER), total_row("e1", Side.UNDER)]
    first = store.write(rows, run_id="r1")
    second = store.write([total_row("e1", Side.OVER), total_row("e1", Side.UNDER)], run_id="r2")
    assert len(first) == 1 and second == []
    import pyarrow.parquet as pq
    assert sum(pq.read_table(p).num_rows for p in first) == 2


def test_raw_store_refuses_repo_and_keeps_received_hash(tmp_path):
    with pytest.raises(PrivatePathError):
        RawStore(REPO / "data", "r")
    body = json.dumps([{"price": 0.6, "proxyWallet": "0xabc"}]).encode()
    e = RawStore(tmp_path, "r").save(source="polymarket", endpoint="data_v2", method="GET",
                                     url="https://data-api.polymarket.com/v2/trades", status=200, headers={},
                                     body=body, fetched_at=T0, redact_fields=["proxyWallet"])
    assert e.sha256_received == hashlib.sha256(body).hexdigest()
    assert e.sha256 != e.sha256_received and e.redacted_fields == ["proxyWallet"]
