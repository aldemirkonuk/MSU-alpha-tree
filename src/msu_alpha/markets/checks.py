"""Cross-source checks and weekly completeness (design sections 4.1 and 4.3; R-DQ-05).

Thresholds are the initial values in config/markets.yaml until calibration (design decision 8).
"""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from .models import Game, Market, SnapshotLabel, SnapshotRow
from .timeutil import eastern_week_start

CLOSE_LABELS = {SnapshotLabel.CLOSE, SnapshotLabel.CLOSE_REPORTED}


@dataclass
class CrossSourceFinding:
    game_id: str
    market: str
    team_id: str | None
    values: dict[str, float]          # source -> consensus line
    max_diff: float


def _consensus(rows: list[SnapshotRow], market: Market) -> dict[tuple, dict[str, float]]:
    """(game_id, team_id or side) -> {source: median close line}, ignoring rows flagged XS-2."""
    acc: dict[tuple, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r.market != market or r.snapshot_label not in CLOSE_LABELS or r.line is None or r.game_id is None:
            continue
        if "XS-2" in r.dq_flags:
            continue
        acc[(r.game_id, r.team_id or r.side.value)][r.source.value].append(r.line)
    return {k: {s: statistics.median(v) for s, v in d.items()} for k, d in acc.items()}


def cross_source_flags(rows: list[SnapshotRow], market: Market = Market.SPREAD,
                       threshold: float = 0.5, flag: str = "xsrc_gt_0p5") -> list[CrossSourceFinding]:
    """The required 0.5-point rule: flag every close row of a game where source consensus lines differ by more."""
    findings = []
    for (game_id, side), by_src in _consensus(rows, market).items():
        if len(by_src) < 2:
            continue
        diff = max(by_src.values()) - min(by_src.values())
        if diff > threshold + 1e-9:
            findings.append(CrossSourceFinding(game_id, market.value, side, dict(by_src), diff))
    bad = {(f.game_id, f.team_id) for f in findings}
    for r in rows:
        if r.market == market and r.snapshot_label in CLOSE_LABELS and (r.game_id, r.team_id or r.side.value) in bad:
            r.flag(flag)
    return findings


def flag_book_outliers(rows: list[SnapshotRow], spread_pts: float = 1.5, total_pts: float = 2.0) -> int:
    """XS-2: one book vs the cross-book median of the same source, game, market, side and snapshot."""
    groups: dict[tuple, list[SnapshotRow]] = defaultdict(list)
    for r in rows:
        if r.line is not None and (r.market.is_spread or r.market.is_total):
            groups[(r.game_id, r.source.value, r.market.value, r.side.value, r.team_id,
                    r.snapshot_label.value, r.snapshot_time_utc)].append(r)
    n = 0
    for grp in groups.values():
        if len(grp) < 3:
            continue
        med = statistics.median(r.line for r in grp)
        limit = spread_pts if grp[0].market.is_spread else total_pts
        for r in grp:
            if abs(r.line - med) > limit:
                r.flag("XS-2")
                n += 1
    return n


def normal_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def flag_moneyline_vs_spread(rows: list[SnapshotRow], sigma: float = 10.9, tol: float = 0.06) -> int:
    """XS-4: same book and snapshot, |fair P(win) - Phi(-line / sigma)| > tol (line from the team's view)."""
    ml: dict[tuple, SnapshotRow] = {}
    sp: dict[tuple, SnapshotRow] = {}
    for r in rows:
        key = (r.game_id, r.source.value, r.book, r.snapshot_label.value, r.snapshot_time_utc, r.team_id)
        if r.market == Market.MONEYLINE and r.team_id:
            ml[key] = r
        elif r.market == Market.SPREAD and r.team_id and r.line is not None:
            sp[key] = r
    n = 0
    for key, m in ml.items():
        s = sp.get(key)
        p = m.fair_prob_power if m.fair_prob_power is not None else m.fair_prob_mult
        if s is None or p is None:
            continue
        if abs(p - normal_cdf(-s.line / sigma)) > tol:
            m.flag("XS-4")
            s.flag("XS-4")
            n += 1
    return n


@dataclass
class WeeklyCompleteness:
    week_start: date
    source: str
    market: str
    scheduled: int
    with_close: int

    @property
    def share(self) -> float:
        return self.with_close / self.scheduled if self.scheduled else float("nan")


def weekly_completeness(games: list[Game], rows: list[SnapshotRow], source: str,
                        market: Market = Market.SPREAD) -> list[WeeklyCompleteness]:
    """Share of scheduled games (by US-Eastern week) with at least one valid close for one source and market."""
    have = {r.game_id for r in rows
            if r.source.value == source and r.market == market and r.snapshot_label in CLOSE_LABELS and r.game_id}
    weeks: dict[date, list[Game]] = defaultdict(list)
    for g in games:
        if g.status not in ("postponed", "canceled", "cancelled"):
            weeks[eastern_week_start(g.scheduled_tip_utc)].append(g)
    return [WeeklyCompleteness(w, source, market.value, len(gs), sum(g.game_id in have for g in gs))
            for w, gs in sorted(weeks.items())]
