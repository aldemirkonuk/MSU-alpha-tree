"""R-MK-08: every source ships disabled; enabling needs a recorded decision; keys from env only."""
import copy

import pytest

from msu_alpha.markets.config import MarketsConfig, SourceDisabled
from msu_alpha.markets.sources.registry import sources


def test_all_sources_ship_disabled():
    cfg = MarketsConfig.load()
    for name in cfg.data["sources"]:
        assert cfg.is_enabled(name) is False, name


def test_every_registry_source_has_a_config_block():
    cfg = MarketsConfig.load()
    assert sources() <= set(cfg.data["sources"])


def test_enabled_without_recorded_decision_is_refused():
    data = copy.deepcopy(MarketsConfig.load().data)
    data["sources"]["kalshi"]["enabled"] = True        # decision still says "blocked: ..."
    with pytest.raises(SourceDisabled):
        MarketsConfig(data).require_enabled("kalshi")


def test_no_credentials_in_config_file():
    from msu_alpha.markets.config import DEFAULT_PATH
    text = DEFAULT_PATH.read_text(encoding="utf-8")
    assert "key_env" in text
    for marker in ("pmx_", "Bearer ", "apiKey="):
        assert marker not in text


def test_storage_root_is_outside_repo(monkeypatch):
    from msu_alpha.markets.config import REPO
    monkeypatch.delenv("MSU_MARKETS_ROOT", raising=False)
    root = MarketsConfig.load().storage_root().resolve()
    assert REPO not in root.parents and root != REPO
