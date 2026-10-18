"""Odds conversions (design section 3.2). American odds are stored as received; decimal and
probability are derived from them. Exchange rows derive American odds from probability.
"""
from __future__ import annotations

import math


def american_to_decimal(a: int | float) -> float:
    a = float(a)
    if -100 < a < 100:
        raise ValueError(f"American odds must be <= -100 or >= +100, got {a}")
    return 1.0 + a / 100.0 if a > 0 else 1.0 + 100.0 / abs(a)


def american_to_prob(a: int | float) -> float:
    a = float(a)
    if -100 < a < 100:
        raise ValueError(f"American odds must be <= -100 or >= +100, got {a}")
    return abs(a) / (abs(a) + 100.0) if a < 0 else 100.0 / (a + 100.0)


def decimal_to_prob(d: float) -> float:
    if d <= 1.0:
        raise ValueError(f"decimal odds must be > 1, got {d}")
    return 1.0 / d


def prob_to_decimal(p: float) -> float:
    _check_prob(p)
    return 1.0 / p


def prob_to_american(p: float) -> int:
    """p >= 0.5 -> -100p/(1-p); else +100(1-p)/p, rounded to the nearest integer."""
    _check_prob(p)
    value = -100.0 * p / (1.0 - p) if p >= 0.5 else 100.0 * (1.0 - p) / p
    return int(round(value))


def decimal_to_american(d: float) -> int:
    if d <= 1.0:
        raise ValueError(f"decimal odds must be > 1, got {d}")
    return int(round((d - 1.0) * 100.0)) if d >= 2.0 else int(round(-100.0 / (d - 1.0)))


def parse_american(token: str | int | float | None) -> int | None:
    """Parse American odds, including 'EVEN' (+100). Returns None for blanks; raises on junk."""
    if token is None:
        return None
    if isinstance(token, (int, float)):
        if isinstance(token, float) and math.isnan(token):
            return None
        return int(token)
    t = token.strip().upper()
    if t in ("", "NL", "NA", "N/A", "-"):
        return None
    if t in ("EVEN", "EV"):
        return 100
    return int(float(t.replace("+", "")))


def booksum(probs: list[float]) -> float:
    return float(sum(probs))


def overround(probs: list[float]) -> float:
    return booksum(probs) - 1.0


def hold(probs: list[float]) -> float:
    pi = booksum(probs)
    return (pi - 1.0) / pi


def _check_prob(p: float) -> None:
    if not 0.0 < p < 1.0:
        raise ValueError(f"probability must be in (0, 1), got {p}")
