"""R-DQ-01 (contracts fail closed), R-DQ-05 (cross-source 0.5-point flag), XS-2, XS-4, C-16, completeness."""
from datetime import timedelta

from msu_alpha.markets import checks
from msu_alpha.markets.contracts import check_row, find_duplicates, flag_jumps
from msu_alpha.markets.models import Game, Market, Phase, Side, SnapshotLabel, SnapshotRow, Source
from msu_alpha.markets.parse import finalise
from msu_alpha.markets.timeutil import parse_utc

T0 = parse_utc("2026-02-01T18:00:00Z")
TIP = parse_utc("2026-02-01T19:00:00Z")
GAME = Game("401860050", 2026, "127", "130", TIP)


def row(**kw):
    base = dict(source=Source.CBBD, book="ESPN BET", market=Market.SPREAD, side=Side.TEAM, snapshot_time_utc=T0,
                fetched_at_utc=T0, season=2026, source_event_id="e1", raw_ref="r", game_id="401860050",
                team_id="127", line=-3.5, snapshot_label=SnapshotLabel.CLOSE)
    base.update(kw)
    return SnapshotRow(**base)


def rules(r, game=None):
    return {v.rule_id for v in check_row(r, game)}


def test_row_rules_fire():
    assert "C-01" in rules(row(market=Market.MONEYLINE, line=None, price_american=-50))
    assert "C-05" in rules(row(line=-3.3))
    assert "C-05" in rules(row(market=Market.TOTAL, side=Side.OVER, team_id=None, line=60.0))
    assert "C-07" in rules(row(source=Source.ESPN, line=-110.0))
    assert "C-11" in rules(row(source=Source.KALSHI, market=Market.MONEYLINE, line=None, bid=0.7, ask=0.6))
    assert rules(row()) == set()


def test_live_book_forced_to_live_phase():
    r = row(book="DraftKings Live")
    rules(r)
    assert r.market_phase == Phase.LIVE and "C-08" in r.dq_flags


def test_c13_pregame_after_tip_but_post_event_report_passes():
    late = row(snapshot_time_utc=TIP + timedelta(seconds=60))
    assert "C-13" in rules(late, GAME)
    reported = row(snapshot_time_utc=TIP + timedelta(days=30), observed_post_event=True,
                   snapshot_label=SnapshotLabel.CLOSE_REPORTED)
    assert "C-13" not in rules(reported, GAME)


def test_c14_open_equals_close_from_one_response_is_not_a_duplicate():
    a = row(snapshot_label=SnapshotLabel.OPEN_REPORTED)
    b = row(snapshot_label=SnapshotLabel.CLOSE_REPORTED)
    assert find_duplicates([a, b]) == []
    assert find_duplicates([a, row(snapshot_label=SnapshotLabel.OPEN_REPORTED)]) != []


def test_bad_booksum_group_quarantined_not_dropped():
    a = row(market=Market.MONEYLINE, line=None, price_american=-500)
    b = row(market=Market.MONEYLINE, line=None, team_id="130", price_american=-400)   # booksum 1.63
    res = finalise([a, b], {GAME.game_id: GAME})
    assert res.rows == [] and {q.rule_id for q in res.quarantine} == {"C-03"} and len(res.quarantine) == 2


def test_cross_source_half_point_flag():
    rows = [row(source=Source.CBBD, line=-3.5), row(source=Source.ESPN, book="DraftKings", line=-4.5),
            row(source=Source.CBBD, team_id="130", line=3.5), row(source=Source.ESPN, book="DraftKings", team_id="130", line=4.5)]
    findings = checks.cross_source_flags(rows)
    assert {f.team_id for f in findings} == {"127", "130"} and all(f.max_diff == 1.0 for f in findings)
    assert all("xsrc_gt_0p5" in r.dq_flags for r in rows)
    ok = [row(source=Source.CBBD, line=-3.5), row(source=Source.ESPN, line=-4.0)]
    assert checks.cross_source_flags(ok) == []


def test_book_outlier_xs2():
    rows = [row(book=b, line=l) for b, l in [("A", -4.0), ("B", -4.0), ("C", -4.5), ("D", -11.5)]]
    assert checks.flag_book_outliers(rows) == 1 and "XS-2" in rows[3].dq_flags


def test_moneyline_vs_spread_xs4():
    ml = row(market=Market.MONEYLINE, line=None, fair_prob_power=0.90)
    sp = row(line=-1.0)                       # favoured by 1 point -> Phi(1/10.9) ~ 0.54
    assert checks.flag_moneyline_vs_spread([ml, sp]) == 1 and "XS-4" in ml.dq_flags
    ml2 = row(market=Market.MONEYLINE, line=None, fair_prob_power=0.55)
    assert checks.flag_moneyline_vs_spread([ml2, row(line=-1.0)]) == 0


def test_jump_flag_c16():
    a = row(line=-3.5)
    b = row(line=-8.0, snapshot_time_utc=T0 + timedelta(seconds=300))
    c = row(line=-3.0, snapshot_time_utc=T0 + timedelta(seconds=5000))
    assert flag_jumps([a, b, c]) == 1 and "C-16" in b.dq_flags and "C-16" not in c.dq_flags


def test_weekly_completeness():
    g2 = Game("401860051", 2026, "127", "96", TIP - timedelta(days=2))   # Fri 30 Jan, same Mon-Sun week
    wk = checks.weekly_completeness([GAME, g2], [row()], "cbbd")
    assert len(wk) == 1 and wk[0].scheduled == 2 and wk[0].with_close == 1 and wk[0].share == 0.5
