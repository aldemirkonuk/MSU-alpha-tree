"""R-MK-02, R-RG-07: raw body first, manifest line, credentials stripped, redaction recorded."""
import gzip
import hashlib
import json

from msu_alpha.markets.raw_store import RawStore, redact_identity, strip_credentials
from msu_alpha.markets.timeutil import parse_utc


def test_strip_credentials():
    url = "https://api.the-odds-api.com/v4/sports/basketball_ncaab/odds?regions=us&apiKey=SECRET&markets=h2h"
    out = strip_credentials(url)
    assert "SECRET" not in out and "apiKey" not in out and "regions=us" in out and "markets=h2h" in out


def test_body_saved_exactly_with_manifest(tmp_path):
    store = RawStore(tmp_path, run_id="r1")
    body = b'{"a": 1, "b": [1, 2]}'
    e = store.save(source="cbbd", endpoint="lines", method="get", url="https://api.collegebasketballdata.com/lines?season=2026",
                   status=200, headers={"Content-Type": "application/json", "Set-Cookie": "x"}, body=body,
                   fetched_at=parse_utc("2026-10-18T12:00:00.123456Z"), job_id="j1")
    assert store.load(e) == body
    assert e.sha256 == hashlib.sha256(body).hexdigest() and e.byte_length == len(body)
    assert e.fetched_at_utc == "2026-10-18T12:00:00.123456Z"
    assert "set-cookie" not in e.headers and e.headers["content-type"] == "application/json"
    manifest = (tmp_path / "raw/cbbd/manifest/2026-10-18.jsonl").read_text().splitlines()
    assert json.loads(manifest[0])["body_path"] == e.body_path
    assert e.body_path.endswith(".json.gz") and e.body_path.startswith("raw/cbbd/lines/2026/10/18/")
    with gzip.open(tmp_path / e.body_path) as fh:
        assert fh.read() == body


def test_polymarket_identity_redaction_is_listed(tmp_path):
    body = json.dumps([{"price": 0.6, "proxyWallet": "0xabc", "pseudonym": "x", "asset": "t1"}]).encode()
    cleaned, removed = redact_identity(body, ["proxyWallet", "pseudonym", "bio"])
    assert removed == ["proxyWallet", "pseudonym"]
    assert json.loads(cleaned) == [{"price": 0.6, "asset": "t1"}]
    e = RawStore(tmp_path, "r").save(source="polymarket", endpoint="data_v2", method="GET",
                                     url="https://data-api.polymarket.com/v2/trades", status=200, headers={},
                                     body=body, fetched_at=parse_utc("2026-10-18T00:00:00Z"),
                                     redact_fields=["proxyWallet", "pseudonym"])
    assert e.redacted_fields == ["proxyWallet", "pseudonym"]


def test_redaction_leaves_unrelated_bodies_untouched():
    body = b'{"x": 1}'
    assert redact_identity(body, ["bio"]) == (body, [])
