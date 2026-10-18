"""The read-only endpoint allowlist (design section 6): exact (host, method, path pattern) per source.

Anything not listed here is refused by markets.http before a request leaves the machine.
Paths come from design sections 1.1-1.6. Only GET is allowed, except the Polymarket CLOB batch
reads that the docs define as POST.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Endpoint:
    source: str
    name: str
    host: str
    method: str
    path: str                 # regex, anchored at both ends
    credential: str | None = None   # "bearer" (CBBD) or "query:apiKey" (The Odds API)

    def matches(self, host: str, method: str, path: str) -> bool:
        return host == self.host and method == self.method and re.fullmatch(self.path, path) is not None


_SEG = r"[A-Za-z0-9._~-]+"
_ESPN_LEAGUE = r"/v2/sports/basketball/leagues/mens-college-basketball"
_ESPN_SITE = r"/apis/site/v2/sports/basketball/mens-college-basketball"
_ODDS_SPORT = r"/v4/sports/basketball_ncaab"
_ODDS_HIST = r"/v4/historical/sports/basketball_ncaab"
_KALSHI = r"/trade-api/v2"

CBBD_HOST = "api.collegebasketballdata.com"

ENDPOINTS: tuple[Endpoint, ...] = (
    # CollegeBasketballData.com (design 1.1): free key, bearer auth
    Endpoint("cbbd", "games", CBBD_HOST, "GET", r"/games", "bearer"),
    Endpoint("cbbd", "lines", CBBD_HOST, "GET", r"/lines", "bearer"),
    Endpoint("cbbd", "lines_providers", CBBD_HOST, "GET", r"/lines/providers", "bearer"),
    Endpoint("cbbd", "teams", CBBD_HOST, "GET", r"/teams", "bearer"),
    # ESPN (design 1.2): gated by decision 2
    Endpoint("espn", "scoreboard", "site.api.espn.com", "GET", _ESPN_SITE + r"/scoreboard"),
    Endpoint("espn", "team_schedule", "site.api.espn.com", "GET", _ESPN_SITE + r"/teams/\d+/schedule"),
    Endpoint("espn", "event_odds", "sports.core.api.espn.com", "GET",
             _ESPN_LEAGUE + r"/events/\d+/competitions/\d+/odds(/\d+)?"),
    Endpoint("espn", "odds_history", "sports.core.api.espn.com", "GET",
             _ESPN_LEAGUE + r"/events/\d+/competitions/\d+/odds/\d+/history/[012](/movement)?"),
    Endpoint("espn", "providers", "sports.core.api.espn.com", "GET", _ESPN_LEAGUE + r"/providers(/\d+)?"),
    # The Odds API (design 1.4): paid; disabled until Aldemir approves a plan
    Endpoint("oddsapi", "events", "api.the-odds-api.com", "GET", _ODDS_SPORT + r"/events/?", "query:apiKey"),
    Endpoint("oddsapi", "odds", "api.the-odds-api.com", "GET", _ODDS_SPORT + r"/odds/?", "query:apiKey"),
    Endpoint("oddsapi", "event_odds", "api.the-odds-api.com", "GET",
             _ODDS_SPORT + r"/events/[0-9a-f]{32}/odds/?", "query:apiKey"),
    Endpoint("oddsapi", "event_markets", "api.the-odds-api.com", "GET",
             _ODDS_SPORT + r"/events/[0-9a-f]{32}/markets/?", "query:apiKey"),
    Endpoint("oddsapi", "scores", "api.the-odds-api.com", "GET", _ODDS_SPORT + r"/scores/?", "query:apiKey"),
    Endpoint("oddsapi", "participants", "api.the-odds-api.com", "GET", _ODDS_SPORT + r"/participants/?", "query:apiKey"),
    Endpoint("oddsapi", "hist_odds", "api.the-odds-api.com", "GET", _ODDS_HIST + r"/odds/?", "query:apiKey"),
    Endpoint("oddsapi", "hist_events", "api.the-odds-api.com", "GET", _ODDS_HIST + r"/events/?", "query:apiKey"),
    Endpoint("oddsapi", "hist_event_odds", "api.the-odds-api.com", "GET",
             _ODDS_HIST + r"/events/[0-9a-f]{32}/odds/?", "query:apiKey"),
    # Kalshi public market data (design 1.5): blocked pending decision 5
    Endpoint("kalshi", "series", "external-api.kalshi.com", "GET", _KALSHI + r"/series(/" + _SEG + r")?"),
    Endpoint("kalshi", "events", "external-api.kalshi.com", "GET", _KALSHI + r"/events(/" + _SEG + r")?"),
    Endpoint("kalshi", "markets", "external-api.kalshi.com", "GET", _KALSHI + r"/markets(/" + _SEG + r")?"),
    Endpoint("kalshi", "trades", "external-api.kalshi.com", "GET", _KALSHI + r"/markets/trades"),
    Endpoint("kalshi", "orderbook", "external-api.kalshi.com", "GET", _KALSHI + r"/markets/" + _SEG + r"/orderbook"),
    Endpoint("kalshi", "candles", "external-api.kalshi.com", "GET",
             _KALSHI + r"/series/" + _SEG + r"/(markets|events)/" + _SEG + r"/candlesticks"),
    Endpoint("kalshi", "batch_candles", "external-api.kalshi.com", "GET", _KALSHI + r"/markets/candlesticks"),
    Endpoint("kalshi", "hist_cutoff", "external-api.kalshi.com", "GET", _KALSHI + r"/historical/cutoff"),
    Endpoint("kalshi", "hist_markets", "external-api.kalshi.com", "GET", _KALSHI + r"/historical/markets(/" + _SEG + r"/candlesticks)?"),
    Endpoint("kalshi", "hist_trades", "external-api.kalshi.com", "GET", _KALSHI + r"/historical/trades"),
    # Polymarket (design 1.6): blocked pending decision 6
    Endpoint("polymarket", "events_keyset", "gamma-api.polymarket.com", "GET", r"/events/keyset"),
    Endpoint("polymarket", "event_slug", "gamma-api.polymarket.com", "GET", r"/events/slug/" + _SEG),
    Endpoint("polymarket", "teams", "gamma-api.polymarket.com", "GET", r"/teams"),
    Endpoint("polymarket", "sports", "gamma-api.polymarket.com", "GET", r"/sports(/market-types)?"),
    Endpoint("polymarket", "series", "gamma-api.polymarket.com", "GET", r"/series"),
    Endpoint("polymarket", "prices_history", "data-api.polymarket.com", "GET", r"/v2/prices-history"),
    Endpoint("polymarket", "data_v2", "data-api.polymarket.com", "GET",
             r"/v2/(trades|tokens|resolutions|oi|live-volume|status)"),
    Endpoint("polymarket", "book", "clob.polymarket.com", "GET", r"/(book|midpoint|spread|last-trade-price)"),
    Endpoint("polymarket", "batch_reads", "clob.polymarket.com", "POST",
             r"/(books|midpoints|spreads|last-trades-prices|batch-prices-history)"),
)

# Strings that must never appear in the markets package (design section 6); checked by tests/markets/test_guard.py.
FORBIDDEN_MARKERS: tuple[str, ...] = (
    "/portfolio", "/orders", "/order/", "/account", "/auth/", "/balance-allowance",
    "wss://external-api-ws.kalshi.com", "api.polymarket.us", "SecureClient", "py_clob_client",
)


def find_endpoint(host: str, method: str, path: str) -> Endpoint | None:
    for ep in ENDPOINTS:
        if ep.matches(host, method.upper(), path):
            return ep
    return None


def sources() -> set[str]:
    return {ep.source for ep in ENDPOINTS}
