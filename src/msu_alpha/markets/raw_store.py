"""Raw store: every response saved before parsing (design section 3.1, R-MK-02).

Layout under the storage root:
  raw/{source}/{endpoint}/{YYYY}/{MM}/{DD}/{fetched_at}_{sha256[:12]}.json.gz
  raw/{source}/manifest/{YYYY-MM-DD}.jsonl
Bodies are never modified, except the Polymarket identity-field redaction, which is listed in the manifest.
"""
from __future__ import annotations

import gzip
import hashlib
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from . import COLLECTOR_VERSION
from .models import ManifestEntry
from .store import ensure_private
from .timeutil import iso_utc, parse_utc

SECRET_QUERY_KEYS = {"apikey", "api_key", "key", "token", "access_token"}
KEPT_HEADERS = {
    "x-calllimit-remaining", "x-requests-remaining", "x-requests-used", "x-requests-last",
    "cache-control", "retry-after", "content-type", "date", "etag", "last-modified",
}


def strip_credentials(url: str) -> str:
    """Remove credential query parameters (R-RG-07)."""
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in SECRET_QUERY_KEYS]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def redact_identity(body: bytes, fields: list[str]) -> tuple[bytes, list[str]]:
    """Drop identity fields of private individuals from a JSON body (Polymarket trades, design 3.1)."""
    if not fields:
        return body, []
    try:
        doc = json.loads(body)
    except ValueError:
        return body, []
    removed: set[str] = set()
    targets = set(fields)

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            out = {}
            for k, v in node.items():
                if k in targets:
                    removed.add(k)
                    continue
                out[k] = walk(v)
            return out
        if isinstance(node, list):
            return [walk(x) for x in node]
        return node

    cleaned = walk(doc)
    if not removed:
        return body, []
    return json.dumps(cleaned, separators=(",", ":"), ensure_ascii=False).encode("utf-8"), sorted(removed)


class RawStore:
    def __init__(self, root: str | Path, run_id: str):
        self.root = ensure_private(Path(root))      # raw bodies are private, never inside the git repo
        self.run_id = run_id

    def save(
        self,
        *,
        source: str,
        endpoint: str,
        method: str,
        url: str,
        status: int,
        headers: dict[str, str],
        body: bytes,
        fetched_at: datetime,
        job_id: str = "",
        request_body: bytes | None = None,
        redact_fields: list[str] | None = None,
    ) -> ManifestEntry:
        sha_received = hashlib.sha256(body).hexdigest()    # hash of the body exactly as received
        body, removed = redact_identity(body, redact_fields or [])
        sha = hashlib.sha256(body).hexdigest()             # hash of the stored (possibly redacted) body
        ts = parse_utc(fetched_at)
        stamp = iso_utc(ts).replace(":", "").replace("-", "")
        rel = Path("raw", source, endpoint, f"{ts:%Y}", f"{ts:%m}", f"{ts:%d}", f"{stamp}_{sha[:12]}.json.gz")
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wb") as fh:
            fh.write(body)
        entry = ManifestEntry(
            fetched_at_utc=iso_utc(ts),
            source=source,
            method=method.upper(),
            endpoint=endpoint,
            url=strip_credentials(url),
            status=status,
            headers={k.lower(): v for k, v in headers.items() if k.lower() in KEPT_HEADERS},
            sha256=sha,
            byte_length=len(body),
            body_path=rel.as_posix(),
            collector_version=COLLECTOR_VERSION,
            run_id=self.run_id,
            job_id=job_id,
            request_body=request_body.decode("utf-8", "replace") if request_body else None,
            redacted_fields=removed,
            sha256_received=sha_received,
        )
        manifest = self.root / "raw" / source / "manifest" / f"{ts:%Y-%m-%d}.jsonl"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
        return entry

    def load(self, entry: ManifestEntry) -> bytes:
        with gzip.open(self.root / entry.body_path, "rb") as fh:
            return fh.read()
