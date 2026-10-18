"""new-MK-11: American odds kept as received; decimal and probability derived."""
import math

import pytest

from msu_alpha.markets import odds


def test_minus_110_pair_booksum_and_hold():
    p = odds.american_to_prob(-110)
    assert math.isclose(p, 110 / 210)
    assert math.isclose(odds.booksum([p, p]), 1.047619, abs_tol=1e-6)
    assert math.isclose(odds.hold([p, p]), 0.045455, abs_tol=1e-6)


@pytest.mark.parametrize("a", [-1000, -175, -110, -100, 100, 150, 450, 2500])
def test_round_trips(a):
    d = odds.american_to_decimal(a)
    assert math.isclose(1 / d, odds.american_to_prob(a))
    # -100 and +100 are the same price (decimal 2.0, p = 0.5); the canonical form is +100 / -100 respectively
    assert odds.decimal_to_american(d) == (100 if abs(a) == 100 else a)
    assert odds.prob_to_american(odds.american_to_prob(a)) == (-100 if abs(a) == 100 else a)


def test_even_and_blanks():
    assert odds.parse_american("EVEN") == 100
    assert odds.parse_american("+150") == 150
    assert odds.parse_american(" ") is None
    assert odds.parse_american(None) is None


@pytest.mark.parametrize("bad", [-99, 0, 50, 99.5])
def test_invalid_american_refused(bad):
    with pytest.raises(ValueError):
        odds.american_to_decimal(bad)
