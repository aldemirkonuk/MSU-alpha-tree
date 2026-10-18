"""Finish parsed rows: derive prices, group complementary outcomes, remove the margin, run contracts.

Source parsers (sources/*.py) return SnapshotRow objects with the price as received; finalise()
does everything that is the same for every source (design 3.2-3.3, 4.2).
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from . import devig as dv
from . import odds
from .contracts import EXCHANGES, Violation, check_group, check_row, find_duplicates
from .models import Game, QuarantineRow, SnapshotRow
from .timeutil import iso_utc, utc_now


@dataclass
class FinaliseResult:
    rows: list[SnapshotRow] = field(default_factory=list)
    quarantine: list[QuarantineRow] = field(default_factory=list)
    violations: dict[str, int] = field(default_factory=dict)


def derive_prices(row: SnapshotRow) -> None:
    """American as received -> decimal and implied (books); mid probability -> American (exchanges)."""
    if row.source in EXCHANGES:
        if row.implied_prob is None and row.bid is not None and row.ask is not None:
            row.implied_prob = (row.bid + row.ask) / 2.0
        if row.implied_prob is not None and 0.0 < row.implied_prob < 1.0:
            row.price_decimal = odds.prob_to_decimal(row.implied_prob)
            row.price_american = odds.prob_to_american(row.implied_prob)
        return
    if row.price_american is not None:
        row.price_decimal = odds.american_to_decimal(row.price_american)
        row.implied_prob = odds.american_to_prob(row.price_american)


def apply_devig(group: list[SnapshotRow], methods: list[str]) -> None:
    implied = [r.implied_prob for r in group]
    if len(group) < 2 or any(p is None or not 0.0 < p < 1.0 for p in implied):
        return                                  # one-sided or incomplete: implied only, fair stays null
    pi = sum(implied)
    for r in group:
        r.booksum = pi
    for method in methods:
        res = dv.devig(implied, method)
        for r, p in zip(group, res.probs):
            if method == "power":
                r.fair_prob_power, r.power_k = p, res.param
            elif method == "shin":
                r.fair_prob_shin, r.shin_z = p, res.param
            elif method == "multiplicative":
                r.fair_prob_mult = p
            for f in res.flags:
                r.flag(f)


def finalise(rows: list[SnapshotRow], games: dict[str, Game] | None = None,
             methods: tuple[str, ...] = ("power", "shin", "multiplicative")) -> FinaliseResult:
    games = games or {}
    out = FinaliseResult()
    now = iso_utc(utc_now())

    def quarantine(row: SnapshotRow, v: Violation) -> None:
        out.quarantine.append(QuarantineRow(v.rule_id, row.to_record(), row.raw_ref, now))
        out.violations[v.rule_id] = out.violations.get(v.rule_id, 0) + 1

    for r in rows:
        if r.game_id is None:
            r.flag("unmatched")
        derive_prices(r)

    groups: dict[tuple, list[SnapshotRow]] = defaultdict(list)
    for r in rows:
        groups[r.group_key()].append(r)

    dup_ids = {id(r) for r in find_duplicates(rows)}
    for grp in groups.values():
        apply_devig(grp, list(methods))
        bad: set[int] = set()
        for v in check_group(grp):
            if v.quarantines:
                for r in grp:
                    quarantine(r, v)
                    bad.add(id(r))
        for r in grp:
            if id(r) in bad:
                continue
            if id(r) in dup_ids:
                quarantine(r, Violation("C-14", "duplicate of an earlier row"))
                continue
            row_v = [v for v in check_row(r, games.get(r.game_id or "")) if v.quarantines]
            if row_v:
                for v in row_v:
                    quarantine(r, v)
                continue
            out.rows.append(r)
    return out
