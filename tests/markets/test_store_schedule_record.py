"""R-MK-03 + R-RG-08 (Parquet store outside the repo), R-MK-05 (schedule), R-MK-09 (counts-only run record),
new-MK-16 (schema_version)."""
from datetime import timedelta

import pytest

from msu_alpha.markets import SCHEMA_VERSION
from msu_alpha.markets.config import REPO, MarketsConfig
from msu_alpha.markets.models import SNAPSHOT_COLUMNS, Game, Market, Side, SnapshotLabel, SnapshotRow, Source
from msu_alpha.markets.run_record import RunRecord
from msu_alpha.markets.schedule import plan_jobs
from msu_alpha.markets.store import PrivatePathError, QuarantineStore, SnapshotStore, snapshot_schema
from msu_alpha.markets.timeutil import parse_utc

pa = pytest.importorskip("pyarrow")

T0 = parse_utc("2026-02-01T18:00:00.123456Z")


def row(**kw):
    base = dict(source=Source.CBBD, book="ESPN BET", market=Market.SPREAD, side=Side.TEAM, snapshot_time_utc=T0,
                fetched_at_utc=T0, season=2026, source_event_id="e1", raw_ref="r", game_id="401860050",
                team_id="127", line=-3.5, snapshot_label=SnapshotLabel.CLOSE)
    base.update(kw)
    return SnapshotRow(**base)


def test_schema_covers_every_model_column():
    assert set(snapshot_schema().names) == set(SNAPSHOT_COLUMNS)
    assert row().schema_version == SCHEMA_VERSION


def test_parquet_round_trip_with_utc_micros_and_dedup(tmp_path):
    store = SnapshotStore(tmp_path)
    r = row(dq_flags=["xsrc_gt_0p5"])
    paths = store.write([r, row(dq_flags=["xsrc_gt_0p5"]), row(team_id="130", line=3.5)], run_id="run1")
    assert len(paths) == 1 and "source=cbbd/season=2026/month=2026-02" in paths[0].as_posix()
    t = pa.parquet.read_table(paths[0]) if hasattr(pa, "parquet") else __import__("pyarrow.parquet").parquet.read_table(paths[0])
    assert t.num_rows == 2
    assert str(t.schema.field("snapshot_time_utc").type) == "timestamp[us, tz=UTC]"
    assert t.column("snapshot_time_utc")[0].as_py() == T0
    assert store.write([row()], run_id="run1") == []          # same row again: skipped (idempotent)
    again = store.write([row(line=-4.0)], run_id="run1")      # new row, same run id
    assert again[0] != paths[0]                               # never overwrites an existing file


def test_store_refuses_repo_paths():
    with pytest.raises(PrivatePathError):
        SnapshotStore(REPO / "data" / "markets")
    with pytest.raises(PrivatePathError):
        QuarantineStore(REPO)


def test_plan_jobs_scope_and_inplay():
    cfg = MarketsConfig.load().section("schedule")
    tip = parse_utc("2026-02-01T19:00:00Z")
    games = [Game("1", 2026, "127", "130", tip),                 # MSU game
             Game("2", 2026, "2509", "356", tip),                # Purdue-Illinois (Big Ten, not MSU)
             Game("3", 2026, "999", "998", tip),                 # outside scope
             Game("4", 2026, "127", "96", tip, status="postponed")]
    jobs = plan_jobs(games, big_ten_team_ids={"127", "130", "2509", "356"}, schedule_cfg=cfg)
    by_game = {g: [j for j in jobs if j.game_id == g] for g in "1234"}
    assert not by_game["3"] and not by_game["4"]
    labels2 = {j.label for j in by_game["2"]}
    assert labels2 == {"t-24h", "t-1h", "close", "gameday"}
    t24 = next(j for j in by_game["2"] if j.label == "t-24h")
    assert t24.run_at_utc == tip - timedelta(seconds=86400)
    inplay = [j for j in by_game["1"] if j.label == "inplay_1m"]
    assert inplay[0].run_at_utc == tip - timedelta(seconds=10800)
    assert inplay[-1].run_at_utc <= tip + timedelta(seconds=7800 + 3600)
    assert len(inplay) == (10800 + 7800 + 3600) // 60 + 1
    assert all(j.kind == "exchanges" for j in inplay)


def test_run_record_counts_only(tmp_path):
    rec = RunRecord("r1")
    rec.rows_by_source["cbbd"] += 12
    rec.quarantined_by_rule["C-03"] += 2
    path = rec.write(tmp_path)
    assert path.parent.name.startswith("markets_") and path.exists()
    bad = RunRecord("r2", notes=[])
    bad.completeness.append({"price_american": -110})
    with pytest.raises(ValueError):
        bad.write(tmp_path)
