"""Load config/markets.yaml and enforce the source gates (R-MK-08)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[3]
DEFAULT_PATH = REPO / "config" / "markets.yaml"


class SourceDisabled(RuntimeError):
    """Raised when code tries to use a source that is not enabled in config."""


@dataclass
class MarketsConfig:
    data: dict[str, Any]

    @classmethod
    def load(cls, path: str | Path | None = None) -> "MarketsConfig":
        with open(path or DEFAULT_PATH, encoding="utf-8") as fh:
            return cls(yaml.safe_load(fh))

    def source(self, name: str) -> dict[str, Any]:
        try:
            return self.data["sources"][name]
        except KeyError:
            raise KeyError(f"unknown source {name!r}") from None

    def is_enabled(self, name: str) -> bool:
        return bool(self.source(name).get("enabled", False))

    def require_enabled(self, name: str) -> dict[str, Any]:
        """Return the source block, or raise SourceDisabled with the pending decision."""
        src = self.source(name)
        if not src.get("enabled", False):
            raise SourceDisabled(f"source {name!r} is disabled: {src.get('decision', 'no decision recorded')}")
        decision = str(src.get("decision", ""))
        if decision.startswith(("pending", "blocked")):
            raise SourceDisabled(f"source {name!r} is enabled but its decision is not recorded: {decision}")
        return src

    def credential(self, name: str) -> str | None:
        """Credentials come only from the environment (R-RG-07)."""
        env = self.source(name).get("key_env")
        return os.environ.get(env) if env else None

    def storage_root(self) -> Path:
        root = os.environ.get("MSU_MARKETS_ROOT") or self.data["storage"]["root"]
        return Path(root).expanduser()

    def results_dir(self) -> Path:
        return REPO / self.data["storage"]["results_dir"]

    def section(self, name: str) -> dict[str, Any]:
        return self.data[name]
