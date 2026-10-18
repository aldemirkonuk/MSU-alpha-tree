"""Row and group contracts C-01 to C-16 (design section 4.2; R-DQ-01).

Fail closed: a QUARANTINE rule moves the row to quarantine with its rule ID; it is never dropped silently.
FLAG rules only add the rule ID to row.dq_flags.
"""
from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass

from .models import Game, Market, Phase, SnapshotRow, Source

EXCHANGES = {Source.KALSHI, Source.POLYMARKET, Source.POLYMARKET_US}

QUARANTINE = {"C-01", "C-02", "C-03", "C-04", "C-05", "C-06", "C-07", "C-10", "C-11", "C-13", "C-14"}


@dataclass
class Violation:
    rule_id: str
    detail: str

    @property
    def quarantines(self) -> bool:
        return self.rule_id in QUARANTINE


def check_row(row: SnapshotRow, game: Game | None = None) -> list[Violation]:
    """Single-row contracts. `game` (with tip time) is needed for C-13."""
    v: list[Violation] = []
    a = row.price_american
    if a is not None and not (-100000 < a <= -100 or 100 <= a < 100000):
        v.append(Violation("C-01", f"price_american out of range: {a}"))
    if row.price_decimal is not None and not row.price_decimal > 1.0:
        v.append(Violation("C-02", f"price_decimal <= 1: {row.price_decimal}"))
    if row.implied_prob is not None and not 0.0 < row.implied_prob < 1.0:
        v.append(Violation("C-02", f"implied_prob outside (0, 1): {row.implied_prob}"))
    if row.line is not None:
        if row.market.is_spread:
            if not (_half_step(row.line) and -60.0 <= row.line <= 60.0):
                v.append(Violation("C-05", f"spread not a multiple of 0.5 in [-60, 60]: {row.line}"))
            if row.source == Source.ESPN and abs(row.line) > 50.0:
                v.append(Violation("C-07", f"ESPN spread |x| > 50 (price in point field): {row.line}"))
        elif row.market in (Market.TOTAL,) and not (_half_step(row.line) and 90.0 <= row.line <= 200.0):
            v.append(Violation("C-05", f"total not a multiple of 0.5 in [90, 200]: {row.line}"))
    if "live" in row.book.lower() and row.market_phase != Phase.LIVE:
        row.market_phase = Phase.LIVE
        row.flag("C-08")
    if row.source in EXCHANGES:
        for name in ("bid", "ask", "last"):
            x = getattr(row, name)
            if x is not None and not 0.0 <= x <= 1.0:
                v.append(Violation("C-11", f"exchange {name} outside [0, 1]: {x}"))
        if row.bid is not None and row.ask is not None:
            if row.bid > row.ask:
                v.append(Violation("C-11", f"bid {row.bid} > ask {row.ask}"))
            elif row.ask - row.bid > 0.20:
                row.flag("wide_spread")
            elif row.source == Source.POLYMARKET and row.ask - row.bid > 0.10:
                row.flag("display_is_last")
    if game is not None and row.market_phase == Phase.PREGAME:
        tip = game.tip_utc
        if not row.observed_post_event:
            if row.snapshot_time_utc > tip:
                v.append(Violation("C-13", f"pregame snapshot after tip: {row.snapshot_time_utc} > {tip}"))
        elif row.source_time_utc is not None and row.source_time_utc > tip:
            v.append(Violation("C-13", f"post-event report with source time after tip: {row.source_time_utc}"))
    return v


def check_group(rows: list[SnapshotRow]) -> list[Violation]:
    """Contracts on one complementary set (same event, book, market, line, snapshot)."""
    v: list[Violation] = []
    if not rows:
        return v
    r0 = rows[0]
    if r0.booksum is not None:
        lo, hi = (0.95, 1.10) if r0.source in EXCHANGES else (0.98, 1.25)
        if not lo <= r0.booksum <= hi:
            v.append(Violation("C-03", f"booksum {r0.booksum:.4f} outside [{lo}, {hi}]"))
        if r0.source == Source.ODDSAPI and not 1.00 <= r0.booksum <= 1.15:
            for r in rows:
                r.flag("C-03-oddsapi")
    for attr in ("fair_prob_power", "fair_prob_shin", "fair_prob_mult"):
        vals = [getattr(r, attr) for r in rows]
        if all(x is not None for x in vals) and not math.isclose(sum(vals), 1.0, abs_tol=1e-9):
            v.append(Violation("C-04", f"{attr} sums to {sum(vals)!r}"))
    if r0.market.is_spread and len(rows) == 2 and all(r.line is not None for r in rows):
        if not math.isclose(rows[0].line + rows[1].line, 0.0, abs_tol=1e-9):
            v.append(Violation("C-06", f"spread sides do not sum to 0: {rows[0].line}, {rows[1].line}"))
    if r0.market.is_total and len({r.line for r in rows}) > 1:
        v.append(Violation("C-06", "over and under on different lines"))
    return v


def find_duplicates(rows: list[SnapshotRow]) -> list[SnapshotRow]:
    """C-14: rows whose dedup key was already seen (the later copies)."""
    seen: set[tuple] = set()
    dups = []
    for r in rows:
        k = r.dedup_key()
        if k in seen:
            dups.append(r)
        else:
            seen.add(k)
    return dups


def flag_jumps(rows: list[SnapshotRow], window_s: float = 900.0, spread_pts: float = 3.0,
               total_pts: float = 4.0, prob: float = 0.15) -> int:
    """C-16: flag (never drop) moves between snapshots less than window_s apart. Returns rows flagged."""
    series: dict[tuple, list[SnapshotRow]] = defaultdict(list)
    for r in rows:
        series[(r.game_id, r.source.value, r.book, r.market.value, r.side.value, r.team_id, r.player_id)].append(r)
    n = 0
    for seq in series.values():
        seq.sort(key=lambda r: r.snapshot_time_utc)
        for prev, cur in zip(seq, seq[1:]):
            if (cur.snapshot_time_utc - prev.snapshot_time_utc).total_seconds() >= window_s:
                continue
            jump = False
            if prev.line is not None and cur.line is not None:
                limit = spread_pts if cur.market.is_spread else total_pts if cur.market.is_total else None
                jump = limit is not None and abs(cur.line - prev.line) > limit
            pa, pb = prev.fair_prob_mult or prev.implied_prob, cur.fair_prob_mult or cur.implied_prob
            if pa is not None and pb is not None and abs(pb - pa) > prob:
                jump = True
            if jump:
                cur.flag("C-16")
                n += 1
    return n


def _half_step(x: float) -> bool:
    return math.isclose((x * 2) % 1, 0.0, abs_tol=1e-9) or math.isclose((x * 2) % 1, 1.0, abs_tol=1e-9)


# Not implemented yet (need a live source first): C-10 (SBRO tokens, with the SBRO parser),
# C-12 (exchange ladders monotone), C-15 (stale lines), C-17 (settlement vs ESPN final).
