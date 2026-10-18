"""Time handling: everything stored in UTC (microseconds); US-Eastern only for date matching and weeks."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

UTC = timezone.utc
EASTERN = ZoneInfo("America/New_York")


def utc_now() -> datetime:
    return datetime.now(UTC)


def parse_utc(value: str | datetime) -> datetime:
    """Parse an ISO-8601 string (Z or offset) to an aware UTC datetime. Naive input is refused."""
    if isinstance(value, datetime):
        dt = value
    else:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError(f"naive datetime refused (no time zone): {value!r}")
    return dt.astimezone(UTC)


def iso_utc(dt: datetime) -> str:
    """UTC ISO string with microseconds, e.g. 2026-03-28T01:55:00.000000Z."""
    return parse_utc(dt).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def eastern_date(dt: datetime) -> date:
    return parse_utc(dt).astimezone(EASTERN).date()


def eastern_week_start(dt: datetime) -> date:
    """Monday of the US-Eastern week containing dt (weeks run Monday 00:00 to Sunday 23:59 Eastern)."""
    d = eastern_date(dt)
    return d - timedelta(days=d.weekday())


def seconds_between(a: datetime, b: datetime) -> float:
    return (parse_utc(b) - parse_utc(a)).total_seconds()
