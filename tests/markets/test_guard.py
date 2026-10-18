"""R-MK-01, R-RG-07: read-only by construction; credentials only from env and never stored."""
import copy
import json
from pathlib import Path

import pytest

from msu_alpha.markets import http
from msu_alpha.markets.config import MarketsConfig, SourceDisabled
from msu_alpha.markets.http import ReadOnlyClient, RequestRefused, Response, check_request
from msu_alpha.markets.raw_store import RawStore
from msu_alpha.markets.sources.registry import FORBIDDEN_MARKERS

PKG = Path(http.__file__).resolve().parent


@pytest.mark.parametrize("method,url", [
    ("GET", "https://external-api.kalshi.com/trade-api/v2/portfolio/balance"),
    ("POST", "https://external-api.kalshi.com/trade-api/v2/portfolio/orders"),
    ("GET", "https://clob.polymarket.com/orders"),
    ("POST", "https://clob.polymarket.com/order"),
    ("DELETE", "https://api.collegebasketballdata.com/lines"),
    ("POST", "https://api.collegebasketballdata.com/lines"),
    ("GET", "https://api.polymarket.us/v1/markets"),
    ("GET", "http://api.collegebasketballdata.com/lines"),
    ("GET", "https://evil.example.com/lines"),
])
def test_allowlist_refuses(method, url):
    with pytest.raises(RequestRefused):
        check_request(url, method, {})


@pytest.mark.parametrize("method,url", [
    ("GET", "https://api.collegebasketballdata.com/lines"),
    ("GET", "https://external-api.kalshi.com/trade-api/v2/series/KXNCAAMBGAME/markets/ABC-1/candlesticks"),
    ("GET", "https://gamma-api.polymarket.com/events/slug/cbb-uk-mst-2025-11-18"),
    ("GET", "https://data-api.polymarket.com/v2/prices-history"),
    ("POST", "https://clob.polymarket.com/batch-prices-history"),
    ("GET", "https://api.the-odds-api.com/v4/sports/basketball_ncaab/events/0123456789abcdef0123456789abcdef/odds"),
])
def test_allowlist_accepts_documented_reads(method, url):
    assert check_request(url, method, {}) is not None


@pytest.mark.parametrize("header", ["POLY_API_KEY", "poly-signature", "Authorization", "Cookie", "KALSHI-ACCESS-KEY"])
def test_caller_credential_headers_refused(header):
    with pytest.raises(RequestRefused):
        check_request("https://api.collegebasketballdata.com/lines", "GET", {header: "x"})


def test_package_has_no_trading_code():
    hits = []
    for py in PKG.rglob("*.py"):
        if py.name == "registry.py":
            continue                       # the registry defines the forbidden list itself
        text = py.read_text(encoding="utf-8")
        hits += [(py.name, m) for m in FORBIDDEN_MARKERS if m in text]
    assert hits == []


def _cfg(enable_cbbd: bool) -> MarketsConfig:
    cfg = MarketsConfig.load()
    data = copy.deepcopy(cfg.data)
    if enable_cbbd:
        data["sources"]["cbbd"]["enabled"] = True
        data["sources"]["cbbd"]["decision"] = "recorded: test only"
    data["sources"]["cbbd"]["min_interval_s"] = 0
    return MarketsConfig(data)


def test_disabled_source_refused_before_network(tmp_path):
    calls = []
    client = ReadOnlyClient(_cfg(False), RawStore(tmp_path, "t"), transport=lambda *a: calls.append(a))
    with pytest.raises(SourceDisabled):
        client.get("https://api.collegebasketballdata.com/lines")
    assert calls == []


def test_bearer_added_from_env_and_never_stored(tmp_path, monkeypatch):
    monkeypatch.setenv("CBBD_API_KEY", "secret-test-key")
    seen = {}

    def transport(method, url, headers, body, timeout):
        seen["headers"] = headers
        return Response(200, {"X-CallLimit-Remaining": "999"}, b"[]")

    client = ReadOnlyClient(_cfg(True), RawStore(tmp_path, "t"), transport=transport, sleep=lambda s: None)
    entry, resp = client.get("https://api.collegebasketballdata.com/lines", params={"season": "2026"})
    assert seen["headers"]["Authorization"] == "Bearer secret-test-key"
    stored = "".join(p.read_text() for p in tmp_path.rglob("*.jsonl"))
    assert "secret-test-key" not in stored
    assert json.loads(stored.splitlines()[0])["headers"]["x-calllimit-remaining"] == "999"


def test_missing_key_refused(tmp_path, monkeypatch):
    monkeypatch.delenv("CBBD_API_KEY", raising=False)
    client = ReadOnlyClient(_cfg(True), RawStore(tmp_path, "t"), transport=lambda *a: None)
    with pytest.raises(RequestRefused):
        client.get("https://api.collegebasketballdata.com/lines")


def test_retry_after_honoured_and_every_attempt_bounded(tmp_path, monkeypatch):
    monkeypatch.setenv("CBBD_API_KEY", "k")
    responses = [Response(429, {"Retry-After": "7"}, b"slow down"), Response(200, {}, b"[]")]
    sleeps = []
    client = ReadOnlyClient(_cfg(True), RawStore(tmp_path, "t"),
                            transport=lambda *a: responses.pop(0), sleep=sleeps.append)
    entry, resp = client.get("https://api.collegebasketballdata.com/lines")
    assert resp.status == 200 and 7.0 in sleeps
