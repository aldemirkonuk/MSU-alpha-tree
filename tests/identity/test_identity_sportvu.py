"""SportVU smoke test of the identity harness (skips when the private truth cache is absent).

Four minutes of the first cached SportVU game at sigma_p 0.15 m, cue profile good: the reference assigner of the spec must
emit no wrong label (live or offline), and a standard tracker on the same detections must produce swaps (the
harness can make the problem it claims to solve).
"""
from __future__ import annotations

import sys
import zlib
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "identity"))

import harness  # noqa: E402
import idlib  # noqa: E402
import metrics  # noqa: E402
import sportvu_truth  # noqa: E402
from obsmodel import observe, profile  # noqa: E402

_CACHED = sorted(p.stem for p in sportvu_truth.CACHE.glob("*.npz"))
GAME = _CACHED[0] if _CACHED else ""
pytestmark = pytest.mark.skipif(not GAME,
                                reason="private SportVU truth cache not built (tools/specgen/identity/sportvu_truth.py)")


@pytest.fixture(scope="module")
def scene():
    tr = sportvu_truth.load(GAME, max_minutes=4)
    rng = np.random.default_rng(zlib.crc32(f"{GAME}|good|0.15|1".encode()))
    return tr, observe(tr, profile("good"), 0.15, rng)


def test_full_config_has_no_swaps(scene):
    tr, (d, g, info) = scene
    res = idlib.run(d, g, dict(idlib.SPEC["harness"]["configs"]["full"]), 0.15)
    for mode in ("live", "offline"):
        m = metrics.identity_metrics(d, res[mode].label, info["in_fov"], d.dt)
        assert m["swap_events"] == 0, (mode, m["confusion_pairs"])
        assert m["coverage"] > 0.2
        assert metrics.invariant_breaks(d, res[mode].label, g.cand) == {"inv1_duplicates": 0, "inv3_outside_lineup": 0}


def test_naive_tracker_swaps(scene):
    tr, (d, g, info) = scene
    res = idlib.run(d, g, dict(idlib.SPEC["harness"]["configs"]["naive_tracker"]), 0.15)
    m = metrics.identity_metrics(d, res["offline"].label, info["in_fov"], d.dt)
    assert m["swap_events"] > 0


@pytest.fixture(scope="module")
def scene_seed2():
    """The second random draw of the same game at sigma_p 0.30 m, 15 min (review round 2, RV-11)."""
    tr = sportvu_truth.load(GAME, max_minutes=15)
    rng = np.random.default_rng(zlib.crc32(f"{GAME}|good|0.3|2".encode()))
    return tr, observe(tr, profile("good"), 0.3, rng)


def test_full_config_has_no_swaps_seed2(scene_seed2):
    """RV-11 found 1 offline swap event (4 boxes of a foreign teammate at a chain edge) on this draw with the 0.1.1 rules.
    The purity rules of review round 2 (RV-22 to RV-25) remove it; the xfail mark set by RV-11 is gone. The clean chains
    of this slice hold no box of a second person that carries a label."""
    tr, (d, g, info) = scene_seed2
    res = idlib.run(d, g, dict(idlib.SPEC["harness"]["configs"]["full"]), 0.3)
    for mode in ("live", "offline"):
        m = metrics.identity_metrics(d, res[mode].label, info["in_fov"], d.dt)
        assert m["swap_events"] == 0, (mode, m["wrong_label_frames"])
        pu = metrics.chain_purity(d, res[mode].chains, g.team, res[mode].label)
        assert pu["impure_labelled_boxes"] == 0 and pu["impure_teammate_boxes"] == 0, (mode, pu)


def test_harness_rows_carry_exposure_mechanisms_and_cue_stats():
    """RV-11, RV-20: one harness job (1 min) -> rows with the label count and mechanisms; the summary with exposure and
    rate bounds; the cue statistics of the profile."""
    rows, private, _, cue = harness.job((GAME, "hard", 0.3, 1, ["full"], 1.0))
    assert {r["mode"] for r in rows} == {"live", "offline"}
    for r in rows:
        assert r["game"].startswith("G") and GAME not in str(r)  # game codes only
        assert r["labels"] >= 0 and isinstance(r["swap_mechanism"], dict) and "labels_on_bystanders" in r
    s = harness.aggregate(rows)
    e = next(x for x in s if x["mode"] == "offline")["exposure"]
    # 95 % Poisson bound: at zero swap events it is -ln(0.05) = 2.996 per minute of play (the 0.1.1 rules had one event
    # in this minute, so the old floor of 3.0 x 40 encoded a swap; the purity rules of review round 2 leave none)
    assert e["game_runs"] == 1 and abs(e["play_minutes"] - 1.0) < 0.01 and e["upper_per_game"] >= 2.99 * 40
    for r in rows:
        assert {"impure_clean_chains", "impure_minority_boxes", "impure_labelled_boxes", "clean_chains"} <= set(r)
    assert e["labelled_player_hours"] <= 10 / 60 + 1e-9
    assert cue["game"].startswith("G") and 0 < cue["app_rank1_teammates"] <= 1 and set(cue["pbp_rows"]) == {"rows", "late", "missing", "wrong_player"}
    c = harness.aggregate_cue_stats([cue])
    assert c[0]["profile"] == "hard" and c[0]["runs"] == 1
