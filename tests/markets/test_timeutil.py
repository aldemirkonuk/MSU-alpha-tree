"""new-MK-10: UTC storage; US-Eastern only for dates and weeks, DST-aware."""
from datetime import date

import pytest

from msu_alpha.markets.timeutil import eastern_date, eastern_week_start, iso_utc, parse_utc


def test_espn_utc_tip_is_previous_eastern_date():
    # MSU-UConn: ESPN 2026-03-28T01:55Z is 27 Mar in US-Eastern (Kalshi 26MAR27, Polymarket 2026-03-27)
    assert eastern_date(parse_utc("2026-03-28T01:55Z")) == date(2026, 3, 27)


def test_dst_aware_not_fixed_offset():
    # DST ends 2026-11-01 06:00 UTC. 2026-11-02T04:30Z is 23:30 EST on 1 Nov;
    # a fixed UTC-4 offset would wrongly give 2 Nov.
    assert eastern_date(parse_utc("2026-11-02T04:30:00Z")) == date(2026, 11, 1)


def test_week_starts_monday_eastern():
    # Sunday 2026-03-29 23:30 EDT (03:30Z Monday) belongs to the week of Monday 23 Mar
    assert eastern_week_start(parse_utc("2026-03-30T03:30:00Z")) == date(2026, 3, 23)


def test_naive_refused_and_iso_has_microseconds():
    with pytest.raises(ValueError):
        parse_utc("2026-03-28T01:55:00")
    assert iso_utc(parse_utc("2026-03-28T01:55:00+00:00")) == "2026-03-28T01:55:00.000000Z"
