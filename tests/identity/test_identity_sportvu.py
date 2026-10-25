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
