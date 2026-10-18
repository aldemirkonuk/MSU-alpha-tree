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


# Post zones and landmarks. Proposals, to be checked against where players actually stand.
LOW_POST_MAX_ABS_X_M = 2.6
LOW_POST_MAX_Y_M = 2.0
HIGH_POST_MAX_ABS_X_M = 2.6
HIGH_POST_Y_RANGE_M = (3.4, 5.2)
LANDMARK_RADIUS_M = 0.9


def post_zone(x: float, y: float, court: Court) -> str:
    """'low_post', 'high_post' or 'none'."""
    if court.lane_half_width_m * 0.5 <= abs(x) <= LOW_POST_MAX_ABS_X_M and y <= LOW_POST_MAX_Y_M:
        return "low_post"
    lo, hi = HIGH_POST_Y_RANGE_M
    if abs(x) <= HIGH_POST_MAX_ABS_X_M and lo <= y <= hi:
        return "high_post"
    return "none"


def landmark(x: float, y: float, court: Court) -> str:
    """Nearest named landmark within LANDMARK_RADIUS_M, else 'none'."""
    marks = {
        "elbow_right": elbow(court, "right"),
        "elbow_left": elbow(court, "left"),
        "nail": (0.0, court.free_throw_line_m),
        "block_right": (court.lane_half_width_m, 0.9),
        "block_left": (-court.lane_half_width_m, 0.9),
    }
    best, dist = "none", LANDMARK_RADIUS_M
    for name, (mx, my) in marks.items():
        d = math.hypot(x - mx, y - my)
        if d <= dist:
            best, dist = name, d
    return best


def describe(x: float, y: float, court: Court) -> dict:
    """Full position descriptor for one player in one frame.

    Every player, every frame: Cartesian position, distance and angle from the rim,
    side, shooting spot, post zone, nearest landmark, angle sector and distance ring.
    """
    r, theta = polar(x, y)
    return {
        "x_m": round(x, 2),
        "y_m": round(y, 2),
        "r_m": round(r, 2),
        "theta_deg": round(theta, 1),
        "side": "right" if x >= 0 else "left",
        "spot": spot(x, y, court),
        "post_zone": post_zone(x, y, court),
        "landmark": landmark(x, y, court),
        "sector_15deg": sector(theta),
        "ring_0p5m": ring(r),
    }
