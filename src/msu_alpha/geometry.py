"""Court geometry in metres, with spots defined as distance and angle from the rim.

Frame: origin on the floor under the centre of the attacked rim.
x runs along the baseline, positive to the attacker's right when facing the basket.
y runs from the baseline toward half-court.
theta is measured in degrees from the right baseline: 0 = right baseline,
90 = straight out to the top of the key, 180 = left baseline.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import yaml

CONFIG = Path(__file__).resolve().parents[2] / "config" / "court_ncaa_men.yaml"


@dataclass(frozen=True)
class Court:
    lane_half_width_m: float
    free_throw_line_m: float
    arc_radius_m: float
    corner_three_m: float
    restricted_radius_m: float
    half_court_m: float

    @classmethod
    def load(cls, path: Path = CONFIG) -> "Court":
        c = yaml.safe_load(path.read_text())
        return cls(
            lane_half_width_m=c["lane_width_m"] / 2,
            free_throw_line_m=c["free_throw_line_from_rim_centre_m"],
            arc_radius_m=c["three_point_arc_radius_m"],
            corner_three_m=c["corner_three_distance_m"],
            restricted_radius_m=c["restricted_area_radius_m"],
            half_court_m=c["half_court_from_rim_centre_m"],
        )

    @property
    def corner_theta_deg(self) -> float:
        """Angle where the straight corner section meets the arc."""
        y = math.sqrt(self.arc_radius_m**2 - self.corner_three_m**2)
        return math.degrees(math.atan2(y, self.corner_three_m))


def polar(x: float, y: float) -> tuple[float, float]:
    """Return (r in metres, theta in degrees) for a court point."""
    return math.hypot(x, y), math.degrees(math.atan2(y, x))


def mirror_theta(theta: float) -> float:
    """Fold the left side onto the right so one rule covers both."""
    return theta if theta <= 90 else 180 - theta


def is_three(x: float, y: float, court: Court) -> bool:
    r, theta = polar(x, y)
    if mirror_theta(theta) <= court.corner_theta_deg:
        return abs(x) >= court.corner_three_m
    return r >= court.arc_radius_m


def spot(x: float, y: float, court: Court) -> str:
    """Label a point. Labels are readable names on top of the math, nothing more."""
    r, theta = polar(x, y)
    t = mirror_theta(theta)
    side = "right" if x >= 0 else "left"
    if r <= court.restricted_radius_m:
        return "restricted_area"
    if abs(x) <= court.lane_half_width_m and y <= court.free_throw_line_m:
        return "paint"
    if is_three(x, y, court):
        if t <= court.corner_theta_deg:
            return f"corner_three_{side}"
        if t <= 60:
            return f"wing_three_{side}"
        if t <= 80:
            return f"slot_three_{side}"
        return "top_three"
    return f"mid_range_{side}"


def sector(theta: float, width_deg: float = 15.0) -> int:
    """Index of the angle sector, 0-based, from the right baseline."""
    return min(int(max(theta, 0.0) // width_deg), int(180 // width_deg) - 1)


def ring(r: float, width_m: float = 0.5) -> int:
    """Index of the distance ring from the rim."""
    return int(r // width_m)


def elbow(court: Court, side: str = "right") -> tuple[float, float]:
    x = court.lane_half_width_m if side == "right" else -court.lane_half_width_m
    return x, court.free_throw_line_m
