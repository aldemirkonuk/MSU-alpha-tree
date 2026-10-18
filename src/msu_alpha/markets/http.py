"""The one read-only HTTP client (design section 6; R-MK-01, R-RG-07).

- Refuses any (host, method, path) not in sources.registry.ENDPOINTS.
- Refuses any source not enabled in config/markets.yaml with a recorded decision.
- Callers may not pass Authorization or POLY_* headers; the CBBD bearer and the Odds API key are
  added here from environment variables and stripped from everything stored.
- Per-host minimum interval, jittered exponential backoff, Retry-After honoured.
- Every response (any status) is written to the raw store before it is returned.
"""
from __future__ import annotations

import random
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlencode, urlsplit

from .config import MarketsConfig
from .models import ManifestEntry
from .raw_store import RawStore
from .sources.registry import Endpoint, find_endpoint
from .timeutil import utc_now


class RequestRefused(PermissionError):
    """Raised before any network activity when a request breaks the read-only rules."""


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes


Transport = Callable[[str, str, dict[str, str], bytes | None, float], Response]

RETRY_STATUSES = {429, 500, 502, 503, 504}


def urllib_transport(method: str, url: str, headers: dict[str, str], body: bytes | None, timeout: float) -> Response:
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return Response(r.status, dict(r.headers.items()), r.read())
    except urllib.error.HTTPError as e:
        return Response(e.code, dict(e.headers.items()) if e.headers else {}, e.read() or b"")


def check_request(url: str, method: str, headers: dict[str, str] | None) -> Endpoint:
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise RequestRefused(f"only https is allowed: {url}")
    ep = find_endpoint(parts.hostname or "", method, parts.path)
    if ep is None:
        raise RequestRefused(f"not on the read-only allowlist: {method} {parts.hostname}{parts.path}")
    for name in (headers or {}):
        low = name.lower()
        if low.startswith("poly_") or low.startswith("poly-"):
            raise RequestRefused(f"POLY_* headers are refused: {name}")
        if low in ("authorization", "cookie", "x-api-key", "kalshi-access-key"):
            raise RequestRefused(f"credential headers may not be passed by callers: {name}")
    return ep


class ReadOnlyClient:
    def __init__(
        self,
        config: MarketsConfig,
        raw_store: RawStore,
        transport: Transport = urllib_transport,
        sleep: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.config = config
        self.raw_store = raw_store
        self.transport = transport
        self.sleep = sleep
        self.clock = clock
        self._last_call: dict[str, float] = {}
        self.http = config.section("http")

    def get(self, url: str, params: dict[str, str] | None = None, job_id: str = "",
            headers: dict[str, str] | None = None) -> tuple[ManifestEntry, Response]:
        return self.request("GET", url, params=params, job_id=job_id, headers=headers)

    def request(self, method: str, url: str, params: dict[str, str] | None = None, body: bytes | None = None,
                job_id: str = "", headers: dict[str, str] | None = None) -> tuple[ManifestEntry, Response]:
        method = method.upper()
        ep = check_request(url, method, headers)
        src = self.config.require_enabled(ep.source)
        send_headers = {"User-Agent": self.http["user_agent"], "Accept": "application/json", **(headers or {})}
        query = dict(params or {})
        if ep.credential == "bearer":
            key = self.config.credential(ep.source)
            if not key:
                raise RequestRefused(f"{ep.source}: environment variable {src.get('key_env')} is not set")
            send_headers["Authorization"] = f"Bearer {key}"
        elif ep.credential == "query:apiKey":
            key = self.config.credential(ep.source)
            if not key:
                raise RequestRefused(f"{ep.source}: environment variable {src.get('key_env')} is not set")
            query["apiKey"] = key
        full_url = url + ("?" + urlencode(query) if query else "")
        host = urlsplit(url).hostname or ""
        min_interval = float(src.get("min_interval_s", 1.0))
        resp = self._send_with_retries(method, full_url, send_headers, body, host, min_interval)
        entry = self.raw_store.save(
            source=ep.source, endpoint=ep.name, method=method, url=full_url, status=resp.status,
            headers=resp.headers, body=resp.body, fetched_at=utc_now(), job_id=job_id, request_body=body,
            redact_fields=list(src.get("redact_fields", [])),
        )
        return entry, resp

    def _throttle(self, host: str, min_interval: float) -> None:
        last = self._last_call.get(host)
        if last is not None:
            wait = min_interval - (self.clock() - last)
            if wait > 0:
                self.sleep(wait)
        self._last_call[host] = self.clock()

    def _send_with_retries(self, method: str, url: str, headers: dict[str, str], body: bytes | None,
                           host: str, min_interval: float) -> Response:
        retries = int(self.http["max_retries"])
        base, cap = float(self.http["backoff_base_s"]), float(self.http["backoff_max_s"])
        resp = Response(0, {}, b"")
        for attempt in range(retries + 1):
            self._throttle(host, min_interval)
            resp = self.transport(method, url, headers, body, float(self.http["timeout_s"]))
            if resp.status not in RETRY_STATUSES or attempt == retries:
                return resp
            retry_after = {k.lower(): v for k, v in resp.headers.items()}.get("retry-after")
            if retry_after and retry_after.strip().isdigit():
                delay = min(cap, float(retry_after))
            else:
                delay = min(cap, base * (2 ** attempt)) * (0.5 + random.random() / 2)
            self.sleep(delay)
        return resp
