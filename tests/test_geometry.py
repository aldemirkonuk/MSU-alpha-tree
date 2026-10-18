import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from msu_alpha.geometry import Court, elbow, is_three, polar, ring, sector, spot  # noqa: E402

COURT = Court.load()


def test_elbow_is_about_66_degrees_not_45():
    r, theta = polar(*elbow(COURT, "right"))
    assert math.isclose(r, 4.57, abs_tol=0.01)
    assert math.isclose(theta, 66.4, abs_tol=0.1)
    _, theta_left = polar(*elbow(COURT, "left"))
    assert math.isclose(theta_left, 113.6, abs_tol=0.1)


def test_corner_meets_arc_near_12_degrees():
    assert math.isclose(COURT.corner_theta_deg, 12.1, abs_tol=0.2)


def test_spots():
    assert spot(0.0, 0.5, COURT) == "restricted_area"
    assert spot(0.0, 3.0, COURT) == "paint"
    assert spot(6.7, 0.5, COURT) == "corner_three_right"
    assert spot(-6.7, 0.5, COURT) == "corner_three_left"
    w = 7.0 / math.sqrt(2)
    assert spot(w, w, COURT) == "wing_three_right"
    assert spot(0.0, 7.2, COURT) == "top_three"
    assert spot(3.0, 3.0, COURT) == "mid_range_right"


def test_three_point_line():
    assert not is_three(6.5, 0.5, COURT)
    assert is_three(6.65, 0.5, COURT)
    assert not is_three(0.0, 6.7, COURT)
    assert is_three(0.0, 6.8, COURT)


def test_bins():
    assert sector(44.9) == 2
    assert sector(45.0) == 3
    assert sector(180.0) == 11
    assert ring(4.57) == 9
