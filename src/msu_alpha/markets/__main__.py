"""Command line: `python -m msu_alpha.markets status` shows which sources may run and why not.

Collection commands are added per source once its decision (design section 0) is recorded.
"""
from __future__ import annotations

import argparse
import sys

from .config import MarketsConfig


def status(cfg: MarketsConfig) -> int:
    for name, src in cfg.data["sources"].items():
        state = "ENABLED" if src.get("enabled") else "disabled"
        key = src.get("key_env")
        key_note = f" key {key}: {'set' if cfg.credential(name) else 'not set'}" if key else ""
        print(f"{name:12s} {state:9s}{key_note} | {src.get('decision', '')}")
    print(f"storage root: {cfg.storage_root()}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m msu_alpha.markets")
    p.add_argument("command", choices=["status"])
    p.add_argument("--config", default=None)
    args = p.parse_args(argv)
    return status(MarketsConfig.load(args.config))


if __name__ == "__main__":
    sys.exit(main())
