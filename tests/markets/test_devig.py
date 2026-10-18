"""R-MK-04, new-MK-15: fair probabilities sum to 1 for every method; published examples reproduced."""
import math
import random

import pytest

from msu_alpha.markets import devig, odds

METHODS = ["multiplicative", "additive", "power", "shin", "odds_ratio"]


@pytest.mark.parametrize("method", METHODS)
@pytest.mark.parametrize("n", [2, 3])
def test_sum_to_one_on_random_books(method, n):
    rng = random.Random(f"{method}-{n}")
    for _ in range(300):
        booksum = rng.uniform(0.95, 1.30)
        w = [rng.uniform(0.15, 1.0) for _ in range(n)]
        implied = [booksum * x / sum(w) for x in w]
        if any(not 0 < r < 1 for r in implied):
            continue
        res = devig.devig(implied, method)
        assert math.isclose(sum(res.probs), 1.0, abs_tol=1e-9)
        assert (devig.FLAG_BOOKSUM_LE_1 in res.flags) == (sum(implied) <= 1.0)


def test_shin_readme_example():
    # mberk/shin README: decimal odds [2.6, 2.4, 4.3] -> [0.373, 0.405, 0.222]
    res = devig.devig([1 / 2.6, 1 / 2.4, 1 / 4.3], "shin")
    assert [round(p, 3) for p in res.probs] == [0.373, 0.405, 0.222]


def test_design_example_kentucky_msu():
    # design 3.3: UK -175 / MSU +150 -> 0.614 mult, 0.618 additive/Shin, 0.620 power
    implied = [odds.american_to_prob(-175), odds.american_to_prob(150)]
    assert round(devig.devig(implied, "multiplicative").probs[0], 3) == 0.614
    assert round(devig.devig(implied, "additive").probs[0], 3) == 0.618
    assert round(devig.devig(implied, "shin").probs[0], 3) == 0.618
    assert round(devig.devig(implied, "power").probs[0], 3) == 0.620


def test_shin_equals_additive_for_two_way():
    rng = random.Random(7)
    for _ in range(200):
        a = rng.uniform(0.2, 0.8)
        b = rng.uniform(1.0, 1.15) - a
        if not 0 < b < 1:
            continue
        s, ad = devig.devig([a, b], "shin"), devig.devig([a, b], "additive")
        assert all(math.isclose(x, y, abs_tol=1e-9) for x, y in zip(s.probs, ad.probs))


def test_symmetric_prices_give_half():
    p = odds.american_to_prob(-110)
    for m in METHODS:
        assert all(math.isclose(x, 0.5) for x in devig.devig([p, p], m).probs)


def test_booksum_exactly_one_and_below():
    assert devig.devig([0.4, 0.6], "power").flags == [devig.FLAG_BOOKSUM_LE_1]
    res = devig.devig([0.47, 0.49], "shin")
    assert devig.FLAG_BOOKSUM_LE_1 in res.flags and "shin_fallback_multiplicative" in res.flags
    assert math.isclose(sum(res.probs), 1.0, abs_tol=1e-9)


def test_one_outcome_refused():
    with pytest.raises(ValueError):
        devig.devig([0.6], "power")
