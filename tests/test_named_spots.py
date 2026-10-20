"""Spec checks for config/named_spots.yaml (fast grid; the full 0.05 m check is tools/specgen/named_spots/check.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "specgen" / "named_spots"))
from check import entry_checks, partition_checks  # noqa: E402
from spotlib import load  # noqa: E402

DOC, SPOTS = load()


def test_every_expr_passes_whitelist_and_ids_unique():
    ids = [e["id"] for e in DOC["entries"]]
    assert len(ids) == len(set(ids))
    assert sum(1 for s in SPOTS.values() if s.code) > 400


def test_anchors_probes_and_mirrors():
    assert dict(entry_checks(DOC, SPOTS)) == {}


def test_court_region_is_an_exact_partition():
    part = partition_checks(DOC, SPOTS, 0.25)
    for name in ("zone_scheme:court_region", "zone_scheme:nba_basic", "zone_scheme:ctg", "zone_scheme:pbpstats"):
        assert part[name]["covered"] == part[name]["points"], name
        assert part[name]["overlaps"] == 0, name


def test_edge_rules():
    region = [s for s in SPOTS.values() if s.d["layer"] == "zone_scheme:court_region"]

    def lab(x, y):
        out = [l for s in region for l in s.labels(x, y)]
        assert len(out) == 1, (x, y, out)
        return out[0]

    assert lab(6.6008, 0.0) == "long_mid_baseline_right"  # on the corner line is a two
    assert lab(6.61, 0.0) == "corner_three_right"
    assert lab(0.0, 1.27) == "restricted_area"  # arc line is inside the RA
    assert lab(0.0, 12.700) != "backcourt"  # division line's near edge is frontcourt
    assert lab(0.0, 12.71) == "backcourt"
    assert lab(7.62, 5.0) == "out_of_bounds"  # boundary lines are out
    assert lab(-5.3, 5.3) == "wing_three_left"
    assert region[0].labels(float("nan"), 1.0) == ["unknown"]


def test_missing_context_is_none_not_false():
    rel = next(s for s in SPOTS.values() if s.ctx and s.code)
    assert rel.inside(1.0, 5.0) is None
