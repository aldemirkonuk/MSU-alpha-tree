"""Margin removal (design section 3.3).

Notation: implied r_i = 1/o_i, pi = sum(r_i). Every method returns p_i with sum(p_i) = 1.
- multiplicative: p_i = r_i / pi
- additive:       p_i = r_i - (pi - 1)/n          (equals Shin for n = 2)
- power:          p_i = r_i^k, sum(r_i^k) = 1
- Shin:           p_i(z) = [sqrt(z^2 + 4(1-z) r_i^2/pi) - z] / [2(1-z)], sum(p_i(z)) = 1
- odds ratio:     p_i = r_i / (c + r_i - c r_i),  sum = 1
When pi <= 1 (exchange mids, stale books), power and odds ratio solve on the widened bracket,
Shin falls back to multiplicative, and the result carries the booksum_le_1 flag.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

SUM_TOL = 1e-9
FLAG_BOOKSUM_LE_1 = "booksum_le_1"


@dataclass
class DevigResult:
    method: str
    probs: list[float]
    booksum: float
    param: float | None = None          # k (power), z (Shin), c (odds ratio)
    flags: list[str] = field(default_factory=list)


def _validate(implied: list[float]) -> float:
    if len(implied) < 2:
        raise ValueError("margin removal needs at least two complementary outcomes")
    for r in implied:
        if not 0.0 < r < 1.0:
            raise ValueError(f"implied probability must be in (0, 1), got {r}")
    return float(sum(implied))


def _bisect(f: Callable[[float], float], lo: float, hi: float, iters: int = 300) -> float:
    """Root of a monotone f on [lo, hi]; f(lo) and f(hi) must have opposite signs."""
    flo, fhi = f(lo), f(hi)
    if flo == 0.0:
        return lo
    if fhi == 0.0:
        return hi
    if (flo > 0) == (fhi > 0):
        raise ValueError("root not bracketed")
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if fm == 0.0 or (hi - lo) < 1e-16:
            return mid
        if (fm > 0) == (flo > 0):
            lo, flo = mid, fm
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _renormalise(probs: list[float]) -> list[float]:
    s = sum(probs)
    return [p / s for p in probs]


def multiplicative(implied: list[float]) -> DevigResult:
    pi = _validate(implied)
    flags = [FLAG_BOOKSUM_LE_1] if pi <= 1.0 else []
    return DevigResult("multiplicative", [r / pi for r in implied], pi, None, flags)


def additive(implied: list[float]) -> DevigResult:
    pi = _validate(implied)
    n = len(implied)
    probs = [r - (pi - 1.0) / n for r in implied]
    flags = [FLAG_BOOKSUM_LE_1] if pi <= 1.0 else []
    if any(p <= 0.0 for p in probs):
        flags.append("additive_nonpositive")
    return DevigResult("additive", probs, pi, None, flags)


def power(implied: list[float]) -> DevigResult:
    pi = _validate(implied)
    if math.isclose(pi, 1.0, abs_tol=1e-15):
        return DevigResult("power", list(implied), pi, 1.0, [FLAG_BOOKSUM_LE_1])
    f = lambda k: sum(r ** k for r in implied) - 1.0
    if pi > 1.0:
        hi = 2.0
        while f(hi) > 0.0:
            hi *= 2.0
            if hi > 1e6:
                raise ValueError("power method: no root found")
        k = _bisect(f, 1.0, hi)
        flags: list[str] = []
    else:
        k = _bisect(f, 1e-12, 1.0)      # widened bracket: sum(r^k) -> n > 1 as k -> 0
        flags = [FLAG_BOOKSUM_LE_1]
    probs = _renormalise([r ** k for r in implied])
    return DevigResult("power", probs, pi, k, flags)


def _shin_probs(implied: list[float], pi: float, z: float) -> list[float]:
    return [(math.sqrt(z * z + 4.0 * (1.0 - z) * r * r / pi) - z) / (2.0 * (1.0 - z)) for r in implied]


def shin(implied: list[float]) -> DevigResult:
    pi = _validate(implied)
    if pi <= 1.0:
        res = multiplicative(implied)
        return DevigResult("shin", res.probs, pi, None, [FLAG_BOOKSUM_LE_1, "shin_fallback_multiplicative"])
    f = lambda z: sum(_shin_probs(implied, pi, z)) - 1.0
    z = _bisect(f, 0.0, 1.0 - 1e-12)
    probs = _renormalise(_shin_probs(implied, pi, z))
    return DevigResult("shin", probs, pi, z, [])


def odds_ratio(implied: list[float]) -> DevigResult:
    pi = _validate(implied)
    g = lambda c: [r / (c + r - c * r) for r in implied]
    f = lambda c: sum(g(c)) - 1.0
    if math.isclose(pi, 1.0, abs_tol=1e-15):
        return DevigResult("odds_ratio", list(implied), pi, 1.0, [FLAG_BOOKSUM_LE_1])
    if pi > 1.0:
        hi = 2.0
        while f(hi) > 0.0:
            hi *= 2.0
            if hi > 1e9:
                raise ValueError("odds ratio method: no root found")
        c, flags = _bisect(f, 1.0, hi), []
    else:
        c, flags = _bisect(f, 1e-12, 1.0), [FLAG_BOOKSUM_LE_1]
    return DevigResult("odds_ratio", _renormalise(g(c)), pi, c, flags)


METHODS: dict[str, Callable[[list[float]], DevigResult]] = {
    "multiplicative": multiplicative,
    "additive": additive,
    "power": power,
    "shin": shin,
    "odds_ratio": odds_ratio,
}


def devig(implied: list[float], method: str) -> DevigResult:
    try:
        fn = METHODS[method]
    except KeyError:
        raise ValueError(f"unknown method {method!r}; choose from {sorted(METHODS)}") from None
    res = fn(implied)
    if not math.isclose(sum(res.probs), 1.0, abs_tol=SUM_TOL):
        raise ArithmeticError(f"{method}: fair probabilities sum to {sum(res.probs)!r}, not 1")
    return res
