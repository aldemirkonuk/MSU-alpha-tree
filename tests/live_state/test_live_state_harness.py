"""Real-data smoke test of the replay harness (skipped when the private scorebug reads are absent) and checks of the
published aggregates (results/live_state_test/harness.json)."""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "specgen" / "live_state"))
import fuse  # noqa: E402
import harness  # noqa: E402
import lslib  # noqa: E402
import measure_real as mr  # noqa: E402

RESULT = REPO / "results" / "live_state_test" / "harness.json"
PRIVATE = mr.STATE.exists() and (mr.PRIV_OUT / "game_codes.json").exists()


@pytest.mark.skipif(not PRIVATE, reason="private scorebug reads not on this machine")
def test_one_game_replay_keeps_every_promise():
    spec = fuse.Spec()
    codes = json.loads((mr.PRIV_OUT / "game_codes.json").read_text())
    key = sorted(codes, key=codes.get)[0]
    d = harness._prepare_worker((key, codes[key]))
    assert d["code"] == "B01" and len(d["S"]) >= 600
    lengths = [b[0] - a[0] - 1 for a, b in zip(d["S"], d["S"][1:]) if a[1] == b[1] and b[0] - a[0] >= 2]
    hidden = harness.hide(d["S"], lengths, spec.P["extra_hidden_share"], random.Random(0))
    assert 0.14 * len(d["S"]) <= len(hidden) <= 0.25 * len(d["S"])
    A, per_game = Counter(), Counter()
    for cfg in harness.configs(spec.P):
        harness.run_one(spec, d, hidden, cfg, random.Random(1), A, per_game)
    tree = harness.nest(A)
    rows = [{"game": "B01", "config": c["name"], "inferred_clock_s": per_game[c["name"], "n"],
             "inferred_within_tolerance": per_game[c["name"], "within"] / max(1, per_game[c["name"], "n"])} for c in harness.configs(spec.P)]
    summary = harness.summarise(tree, rows, spec.P)
    v = harness.verdicts(summary, spec.P)
    assert v["ACC-LS-H2"]["pass"], v["ACC-LS-H2"]["violations"]      # no null, no unlogged rise or fall, no false observed
    assert v["ACC-LS-H3"]["pass"], v["ACC-LS-H3"]["returns"]
    none = summary["cues_0.0_0.0_0.0"]
    assert none["clock_by_grade"]["inferred"]["n"] > 100
    assert none["clock_by_grade"]["inferred"]["within_tolerance"] >= spec.P["clock_inferred_promise"]
    assert all(g in ("inferred", "carried", "unknown") for g in none["clock_by_grade"])   # a hidden second is never observed
    assert set(none["by_grade"]["score_total"]) <= {"carried", "unknown"}


def test_published_results_pass_every_check_and_hold_aggregates_only():
    out = json.loads(RESULT.read_text())
    core = lslib.load_core()
    assert out["pack_version"] == core["version"] and out["games"] >= 30 and out["seeds"] == fuse.Spec().P["seeds"]
    assert all(x["pass"] for x in out["verdicts"].values()), {k: x["pass"] for k, x in out["verdicts"].items()}
    assert all(r["game"].startswith("B") and len(r["game"]) == 3 for r in out["per_game"])
    text = RESULT.read_text() + (RESULT.parent / "README.md").read_text()
    assert "MichiganState" not in text and "cbbd" not in text.lower() and "/Users/" not in text
    P = fuse.Spec().P
    for k, val in out["limits_used"].items():
        assert P[k] == val, f"harness.json was made with {k} = {val}; the YAML now says {P[k]} - run harness.py again"


def test_numbers_quoted_in_the_yaml_equal_harness_json():
    out = json.loads(RESULT.read_text())
    yaml_text = (lslib.PACK_DIR / "fields_scoreboard.yaml").read_text() + lslib.CORE.read_text()
    for name, sentence in harness.quoted_evidence(out).items():
        assert sentence in yaml_text, f"{name}: the YAML no longer quotes harness.json ({sentence})"


def test_the_harness_configs_come_from_core_yaml():
    P = fuse.Spec().P
    names = [c["name"] for c in harness.configs(P)]
    assert len(names) == len(set(names)) == len(P["cue_configs"]) + len(P["feed_delay_sweep_s"]) - 1 + len(P["shot_slot_configs"])
    assert names[0] == "cues_0.0_0.0_0.0"                           # the run with no cue and no feed is the baseline
