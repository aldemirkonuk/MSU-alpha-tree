"""V0 synthetic tests for the transition / restart detectors (config/movement_grammar/transition.yaml).

Every scenario is built with sim.scenario (minimum-jerk waypoints, white + AR(1) noise at sigma_p 0.3, fixed seeds) in
the attacked-rim frame of the team that has (or gains) the ball. The ball is scripted as holds and straight flights
between players or rims and observed with sigma 0.7 * sigma_p. For each detector there is at least one positive and
one negative scenario; positives check kind, actors, t0 (+-0.3 s) and the confidence range.

Expected t0: hand-derived from the script for ball anchors (holds, passes, throw-ins); for kinematic onsets it is the
same detector run on a low-noise copy of the scenario (sigma_p 0.1, same seed), i.e. the definition applied
to the truth path.
"""

import functools
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "movement"))
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "named_spots"))

import mvlib as mv  # noqa: E402
import sim  # noqa: E402
from detectors import transition as T  # noqa: E402

DT = mv.DT
RIM = (0.0, 0.0)
FAR = (0.0, 25.4508)
SIGMA = 0.3
TOL = 0.3

# --------------------------------------------------------------------------------------
# Scenarios: actors {id: (team, [(t, x, y), ...])}, ball [('hold', t0, t1, id) | ('fly', t0, t1, src, dst)]
# --------------------------------------------------------------------------------------
BREAK_ACTORS = {
    "d1": ("D", [(0, 2.0, 19.0), (1.2, 2.0, 19.0), (6.0, 2.5, 3.0)]),  # shooter, then retreat
    "d2": (
        "D",
        [(0, -3.0, 21.0), (1.0, -3.0, 21.0), (2.0, 1.5, 24.2), (2.6, 1.5, 24.2), (7.5, 0.5, -1.2)],
    ),  # crash, rim
    "d3": ("D", [(0, 5.0, 14.0), (1.0, 5.0, 14.0), (4.5, 3.0, 4.0)]),  # safety
    "d4": ("D", [(0, -6.0, 18.0), (2.5, -6.0, 18.0), (7.5, -4.0, 5.0)]),
    "d5": ("D", [(0, 4.0, 23.0), (3.0, 4.0, 23.0), (8.5, 4.0, 6.0)]),
    "o5": ("O", [(0, -1.5, 23.0), (3.0, -1.5, 23.0), (8.5, -0.5, 8.0)]),  # rebounder, trailer
    "o1": (
        "O",
        [(0, 3.0, 17.0), (1.4, 3.0, 17.0), (2.6, 5.5, 20.5), (3.0, 5.5, 20.5), (6.0, 1.0, 7.0)],
    ),  # outlet, push
    "o2": ("O", [(0, -5.5, 20.0), (2.2, -5.5, 20.0), (6.8, -6.9, 1.0)]),  # left wing -> corner
    "o3": ("O", [(0, 6.0, 16.0), (2.4, 6.0, 16.0), (6.5, 6.9, 1.0)]),  # right wing -> corner
    "o4": ("O", [(0, -0.5, 22.0), (2.2, -0.5, 22.0), (6.5, -0.5, 1.0)]),  # rim runner
}
BREAK_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.0, FAR, "o5"),
    ("hold", 2.0, 2.6, "o5"),
    ("fly", 2.6, 3.0, "o5", "o1"),
    ("hold", 3.0, 6.5, "o1"),
    ("fly", 6.5, 7.0, "o1", "o4"),
    ("hold", 7.0, 7.4, "o4"),
    ("fly", 7.4, 7.8, "o4", RIM),
    ("fly", 7.8, 8.4, RIM, (0.5, -1.0)),
]

SLOW_ACTORS = {
    "d1": ("D", [(0, 2.0, 19.0), (1.5, 2.0, 19.0), (10.5, 2.5, 14.5)]),
    "d2": ("D", [(0, -3.0, 21.0), (3.0, -3.0, 21.0), (11.5, -3.5, 15.5)]),
    "d3": ("D", [(0, 4.0, 21.5), (3.0, 4.0, 21.5), (11.5, 5.0, 16.0)]),
    "d4": ("D", [(0, -5.0, 22.0), (3.0, -5.0, 22.0), (11.5, -5.5, 16.5)]),
    "d5": ("D", [(0, 1.5, 22.0), (3.0, 1.5, 22.0), (11.5, 2.0, 16.0)]),
    "o5": ("O", [(0, -1.5, 23.0), (2.6, -1.5, 23.0), (11.5, -1.0, 17.0)]),
    "o1": ("O", [(0, 3.0, 17.0), (2.5, 3.0, 17.0), (11.5, 4.0, 9.0)]),
    "o2": ("O", [(0, -5.5, 20.0), (2.5, -5.5, 20.0), (11.5, -5.0, 9.0)]),
    "o3": ("O", [(0, 6.0, 16.0), (2.5, 6.0, 16.0), (11.5, 5.5, 8.0)]),
    "o4": ("O", [(0, -1.0, 21.5), (2.5, -1.0, 21.5), (11.5, -2.0, 8.0)]),
}
SLOW_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.0, FAR, "o5"),
    ("hold", 2.0, 12.0, "o5"),
]

LEAK_ACTORS = {
    "d1": ("D", [(0, 2.5, 20.0), (12, 2.5, 20.0)]),
    "d2": ("D", [(0, -3.0, 22.0), (12, -3.0, 22.0)]),
    "d3": ("D", [(0, 5.0, 21.0), (12, 5.0, 21.0)]),
    "d4": (
        "D",
        [(0, -1.5, 14.0), (1.2, -1.5, 14.0), (2.2, 2.0, 12.5), (2.4, 2.0, 12.5), (3.4, -2.5, 16.5), (12, -2.5, 16.5)],
    ),
    "d5": ("D", [(0, 0.0, 23.5), (12, 0.0, 23.5)]),
    "o1": ("O", [(0, -1.0, 18.5), (1.4, -1.0, 18.5), (2.0, 0.0, 18.0), (12, 0.0, 18.0)]),  # steals d1 -> d2
    "o2": ("O", [(0, -4.0, 21.0), (12, -4.0, 21.0)]),
    "o3": ("O", [(0, 3.0, 17.0), (0.8, 3.0, 17.0), (4.8, 1.0, 2.0), (12, 1.0, 2.0)]),  # early leak
    "o4": ("O", [(0, 4.0, 23.0), (12, 4.0, 23.0)]),
    "o5": ("O", [(0, -1.5, 24.5), (12, -1.5, 24.5)]),
}
LEAK_BALL = [
    ("hold", 0, 1.6, "d1"),
    ("fly", 1.6, 2.0, "d1", "o1"),
    ("hold", 2.0, 2.6, "o1"),
    ("fly", 2.6, 3.1, "o1", "o3"),
    ("hold", 3.1, 4.8, "o3"),
    ("fly", 4.8, 5.2, "o3", RIM),
    ("fly", 5.2, 5.8, RIM, (0.0, -1.0)),
]

HELD_ACTORS = dict(LEAK_ACTORS)
HELD_ACTORS["o2"] = ("O", [(0, -4.0, 18.5), (1.0, -4.0, 18.5), (5.0, -3.0, 4.0), (12, -3.0, 4.0)])
HELD_ACTORS["d4"] = ("D", [(0, -5.0, 15.0), (12, -5.0, 15.0)])
HELD_BALL = [("hold", 0, 1.6, "d1"), ("fly", 1.6, 2.0, "d1", "o1"), ("hold", 2.0, 8.0, "o1")]

STEAL2_ACTORS = dict(LEAK_ACTORS)
STEAL2_ACTORS["o3"] = ("O", [(0, 3.0, 17.0), (12, 3.0, 17.0)])
STEAL2_ACTORS["d4"] = ("D", [(0, 0.3, 13.0), (12, 0.3, 13.0)])
STEAL2_BALL = [("hold", 0, 1.6, "d1"), ("fly", 1.6, 2.0, "d1", "o1"), ("hold", 2.0, 8.0, "o1")]


def _drag_actors(double):
    a = dict(BREAK_ACTORS)
    a["o1"] = (
        "O",
        [
            (0, 3.0, 17.0),
            (1.4, 3.0, 17.0),
            (2.6, 5.5, 20.5),
            (3.0, 5.5, 20.5),
            (6.0, 2.0, 9.0),
            (6.9, 2.0, 9.0),
            (8.0, -1.0, 4.5),
        ],
    )
    a["o5"] = ("O", [(0, -1.5, 23.0), (3.0, -1.5, 23.0), (6.6, 2.0, 10.0), (6.8, 2.0, 10.0), (8.2, 0.3, 2.5)])
    if double:
        a["o4"] = ("O", [(0, -0.5, 22.0), (2.2, -0.5, 22.0), (6.2, 1.0, 9.6), (7.0, 1.0, 9.6), (8.6, -6.5, 7.5)])
    else:
        a["o5"] = ("O", [(0, -1.5, 23.0), (3.0, -1.5, 23.0), (6.6, 1.0, 9.6), (6.8, 1.0, 9.6), (8.2, 0.3, 2.5)])
    a["d1"] = ("D", [(0, 2.0, 19.0), (1.2, 2.0, 19.0), (6.0, 3.5, 6.0)])
    a["d2"] = ("D", [(0, -3.0, 21.0), (1.0, -3.0, 21.0), (2.0, 1.5, 24.2), (2.6, 1.5, 24.2), (7.5, -3.0, 2.0)])
    a["d5"] = ("D", [(0, 4.0, 23.0), (3.0, 4.0, 23.0), (8.5, 4.5, 3.0)])
    return a


DRAG_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.0, FAR, "o5"),
    ("hold", 2.0, 2.6, "o5"),
    ("fly", 2.6, 3.0, "o5", "o1"),
    ("hold", 3.0, 9.5, "o1"),
]

PITCH_ACTORS = dict(BREAK_ACTORS)
PITCH_ACTORS["o1"] = (
    "O",
    [(0, -3.0, 17.0), (1.4, -3.0, 17.0), (2.6, -4.0, 21.0), (3.0, -4.0, 21.0), (5.6, 5.5, 5.0), (12, 5.5, 5.0)],
)
PITCH_ACTORS["o5"] = ("O", [(0, -1.5, 23.0), (3.0, -1.5, 23.0), (6.6, 0.3, 7.6), (12, 0.3, 7.6)])
PITCH_ACTORS["o4"] = ("O", [(0, -0.5, 22.0), (2.2, -0.5, 22.0), (6.5, -2.0, 1.0), (12, -2.0, 1.0)])
PITCH_ACTORS["d1"] = ("D", [(0, 2.0, 19.0), (1.2, 2.0, 19.0), (6.0, 2.5, 2.0)])
PITCH_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.0, FAR, "o5"),
    ("hold", 2.0, 2.6, "o5"),
    ("fly", 2.6, 3.0, "o5", "o1"),
    ("hold", 3.0, 7.0, "o1"),
    ("fly", 7.0, 7.4, "o1", "o5"),
    ("hold", 7.4, 9.0, "o5"),
]

MADE_ACTORS = {
    "d1": ("D", [(0, 1.5, 20.0), (2.5, 1.5, 20.0), (9.0, 3.0, 8.0)]),
    "d2": ("D", [(0, -4.5, 21.5), (2.5, -4.5, 21.5), (9.0, -3.0, 6.0)]),
    "d3": ("D", [(0, 5.0, 19.0), (2.5, 5.0, 19.0), (9.0, 4.0, 7.0)]),
    "d4": ("D", [(0, -6.0, 18.0), (2.5, -6.0, 18.0), (9.0, -5.0, 6.0)]),
    "d5": ("D", [(0, 3.0, 23.5), (2.5, 3.0, 23.5), (9.0, 2.0, 4.0)]),
    "o5": (
        "O",
        [
            (0, 1.0, 24.5),
            (1.0, 1.0, 24.5),
            (1.6, 1.0, 27.6),
            (2.25, 1.0, 27.6),
            (3.05, -2.5, 27.6),
            (3.4, -2.5, 27.6),
            (4.4, -1.0, 24.0),
            (10, -1.0, 24.0),
        ],
    ),
    "o1": (
        "O",
        [(0, -3.0, 21.0), (2.0, -3.0, 21.0), (3.3, -3.0, 22.0), (3.6, -3.0, 22.0), (6.6, -1.0, 8.0), (10, -1.0, 8.0)],
    ),
    "o2": ("O", [(0, -5.5, 15.0), (10, -5.5, 15.0)]),
    "o3": ("O", [(0, 5.5, 16.0), (10, 5.5, 16.0)]),
    "o4": ("O", [(0, -4.0, 13.0), (10, -4.0, 13.0)]),
}
MADE_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.2, FAR, "o5"),
    ("hold", 2.2, 3.1, "o5"),
    ("fly", 3.1, 3.5, "o5", "o1"),
    ("hold", 3.5, 8.0, "o1"),
]

HOMERUN_ACTORS = dict(MADE_ACTORS)
HOMERUN_ACTORS["o5"] = ("O", [(0, 1.0, 24.5), (1.0, 1.0, 24.5), (1.6, 1.0, 27.6), (10, 1.0, 27.6)])
HOMERUN_ACTORS["o3"] = ("O", [(0, 5.5, 16.0), (2.0, 5.5, 16.0), (5.4, 0.5, 5.0), (10, 0.5, 5.0)])
HOMERUN_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.2, FAR, "o5"),
    ("hold", 2.2, 5.0, "o5"),
    ("fly", 5.0, 5.8, "o5", "o3"),
    ("hold", 5.8, 8.0, "o3"),
]

PRESS_ACTORS = {
    "o5": ("O", [(0, 2.0, 27.6), (2.2, 2.0, 27.6), (3.2, -1.0, 23.8), (10, -1.0, 23.8)]),  # thrower, steps in
    "o1": (
        "O",
        [(0, 2.0, 20.5), (1.2, 2.0, 20.5), (2.2, 4.0, 23.0), (2.4, 4.0, 23.0), (3.2, 5.8, 24.0), (10, 5.8, 24.0)],
    ),  # trapped
    "o2": ("O", [(0, 6.0, 20.8), (10, 6.0, 20.8)]),
    "o3": (
        "O",
        [(0, -2.0, 20.5), (1.2, -2.0, 20.5), (2.6, -2.6, 17.0), (4.0, -2.6, 17.0), (5.0, 0.5, 19.5), (10, 0.5, 19.5)],
    ),
    "o4": ("O", [(0, -6.0, 20.5), (1.0, -6.0, 20.5), (2.3, -6.5, 14.0), (10, -6.5, 14.0)]),
    "d1": ("D", [(0, 1.3, 26.5), (2.2, 1.3, 26.5), (3.2, 5.3, 24.9), (10, 5.3, 24.9)]),
    "d2": ("D", [(0, 7.0, 22.0), (2.2, 7.0, 22.0), (3.2, 6.3, 24.9), (10, 6.3, 24.9)]),
    "d3": ("D", [(0, -3.0, 21.0), (10, -3.0, 21.0)]),
    "d4": ("D", [(0, 0.0, 16.0), (10, 0.0, 16.0)]),
    "d5": ("D", [(0, 0.0, 8.0), (10, 0.0, 8.0)]),
}
PRESS_BALL = [
    ("hold", 0.5, 2.0, "o5"),
    ("fly", 2.0, 2.4, "o5", "o1"),
    ("hold", 2.4, 4.6, "o1"),
    ("fly", 4.6, 4.9, "o1", "o5"),
    ("hold", 4.9, 5.2, "o5"),
    ("fly", 5.2, 5.5, "o5", "o3"),
    ("hold", 5.5, 7.0, "o3"),
]

PRESSB_ACTORS = {
    "o5": (
        "O",
        [(0, 0.5, 27.6), (2.2, 0.5, 27.6), (3.2, 0.5, 25.5), (8.5, 0.0, 15.0), (10, 0.0, 15.0)],
    ),  # safety behind
    "o1": (
        "O",
        [(0, 2.5, 22.0), (1.5, 2.5, 22.0), (2.2, 2.0, 23.5), (2.4, 2.0, 23.5), (8.5, 1.5, 11.5), (10, 1.5, 11.5)],
    ),
    "o2": ("O", [(0, 5.0, 17.0), (10, 5.0, 17.0)]),
    "o3": ("O", [(0, -4.5, 14.0), (10, -4.5, 14.0)]),
    "o4": ("O", [(0, -1.0, 6.0), (10, -1.0, 6.0)]),
    "d1": ("D", [(0, -0.5, 26.3), (2.4, -0.5, 26.3), (2.9, 2.0, 22.2), (8.5, 1.5, 10.2), (10, 1.5, 10.2)]),
    "d2": ("D", [(0, 5.0, 19.0), (3.0, 5.0, 19.0), (8.0, 3.0, 5.0), (10, 3.0, 5.0)]),
    "d3": ("D", [(0, -4.0, 18.0), (3.0, -4.0, 18.0), (8.0, -3.0, 5.0), (10, -3.0, 5.0)]),
    "d4": ("D", [(0, 0.0, 15.0), (3.0, 0.0, 15.0), (8.0, 0.0, 3.0), (10, 0.0, 3.0)]),
    "d5": ("D", [(0, -1.0, 4.0), (10, -1.0, 4.0)]),
}
PRESSB_BALL = [("hold", 0.5, 2.0, "o5"), ("fly", 2.0, 2.4, "o5", "o1"), ("hold", 2.4, 10.0, "o1")]

BLOB_ACTORS = {
    "o5": ("O", [(0, 2.7, -2.1), (3.2, 2.7, -2.1), (4.0, 1.5, 0.5), (6, 1.5, 0.5)]),
    "o1": (
        "O",
        [(0, 2.2, 4.2), (1.2, 2.2, 4.2), (2.2, 3.6, 6.8), (2.3, 3.6, 6.8), (3.4, 4.2, 2.6), (6, 4.2, 2.6)],
    ),  # V-cut
    "o2": ("O", [(0, -2.2, 4.2), (6, -2.2, 4.2)]),
    "o3": ("O", [(0, 2.2, 1.0), (6, 2.2, 1.0)]),
    "o4": ("O", [(0, -2.2, 1.0), (6, -2.2, 1.0)]),
    "d1": ("D", [(0, 1.3, 3.2), (6, 1.3, 3.2)]),
    "d2": ("D", [(0, -1.5, 3.4), (6, -1.5, 3.4)]),
    "d3": ("D", [(0, 0.9, 0.2), (6, 0.9, 0.2)]),
    "d4": ("D", [(0, -1.4, 0.3), (6, -1.4, 0.3)]),
    "d5": ("D", [(0, 1.6, -1.0), (6, 1.6, -1.0)]),
}
BLOB_BALL = [("hold", 0.5, 3.2, "o5"), ("fly", 3.2, 3.5, "o5", "o1"), ("hold", 3.5, 6.0, "o1")]

BLOBSTACK_ACTORS = dict(BLOB_ACTORS)
BLOBSTACK_ACTORS.update(
    {
        "o1": ("O", [(0, 1.6, 4.6), (6, 1.6, 4.6)]),
        "o2": ("O", [(0, 1.9, 3.4), (6, 1.9, 3.4)]),
        "o3": ("O", [(0, 1.7, 2.2), (6, 1.7, 2.2)]),
        "o4": ("O", [(0, -6.8, 0.5), (6, -6.8, 0.5)]),
        "d1": ("D", [(0, 0.6, 4.0), (6, 0.6, 4.0)]),
        "d2": ("D", [(0, 0.8, 2.6), (6, 0.8, 2.6)]),
        "d3": ("D", [(0, 3.3, 0.0), (6, 3.3, 0.0)]),
        "d4": ("D", [(0, -5.8, 1.0), (6, -5.8, 1.0)]),
    }
)
BLOBSTACK_BALL = [("hold", 0.5, 3.0, "o5"), ("fly", 3.0, 3.3, "o5", "o3"), ("hold", 3.3, 6.0, "o3")]

SLOB_ACTORS = {
    "o5": ("O", [(0, 7.9, 6.9), (6, 7.9, 6.9)]),
    "o1": ("O", [(0, 3.0, 3.0), (6, 3.0, 3.0)]),
    "o2": ("O", [(0, 3.1, 5.0), (1.5, 3.1, 5.0), (2.3, 5.5, 7.5), (6, 5.5, 7.5)]),
    "o3": ("O", [(0, 2.9, 7.0), (6, 2.9, 7.0)]),
    "o4": ("O", [(0, 3.0, 9.0), (6, 3.0, 9.0)]),
    "d1": ("D", [(0, 2.0, 2.4), (6, 2.0, 2.4)]),
    "d2": ("D", [(0, 2.0, 4.6), (6, 2.0, 4.6)]),
    "d3": ("D", [(0, 2.0, 6.8), (6, 2.0, 6.8)]),
    "d4": ("D", [(0, 2.0, 9.4), (6, 2.0, 9.4)]),
    "d5": ("D", [(0, 6.7, 5.4), (6, 6.7, 5.4)]),
}
SLOB_BALL = [("hold", 0.5, 2.3, "o5"), ("fly", 2.3, 2.6, "o5", "o2"), ("hold", 2.6, 6.0, "o2")]

FT_ACTORS = {
    "o1": ("O", [(0, 0.0, 4.8), (6, 0.0, 4.8)]),  # shooter
    "o2": ("O", [(0, 2.3, 2.26), (2.1, 2.3, 2.26), (2.8, 1.0, 1.6), (6, 1.0, 1.6)]),  # crashes in
    "o3": ("O", [(0, -2.3, 2.26), (6, -2.3, 2.26)]),
    "o4": ("O", [(0, 0.3, 7.5), (6, 0.3, 7.5)]),
    "o5": ("O", [(0, -4.5, 7.0), (6, -4.5, 7.0)]),
    "d1": ("D", [(0, 2.3, 1.3), (2.1, 2.3, 1.3), (2.8, 0.9, 0.9), (6, 0.9, 0.9)]),  # boxes out o2
    "d2": ("D", [(0, -2.3, 1.3), (6, -2.3, 1.3)]),
    "d3": ("D", [(0, 2.3, 3.2), (6, 2.3, 3.2)]),
    "d4": ("D", [(0, -2.3, 3.2), (6, -2.3, 3.2)]),
    "d5": ("D", [(0, -3.0, 12.0), (2.2, -3.0, 12.0), (5.0, -2.0, 22.0), (6, -2.0, 22.0)]),  # FT leak
}
FT_BALL = [("hold", 0.3, 2.0, "o1"), ("fly", 2.0, 2.8, "o1", RIM), ("fly", 2.8, 3.2, RIM, (0.0, -1.2))]
FTSTATIC_ACTORS = {k: (tm, [wp[0], (6, wp[0][1], wp[0][2])]) for k, (tm, wp) in FT_ACTORS.items()}

TANDEM_ACTORS = {
    "o1": ("O", [(0, 0.5, 21.0), (1.4, 0.5, 21.0), (5.5, 0.5, 8.0), (10, 0.5, 8.0)]),
    "o2": ("O", [(0, -5.0, 20.0), (1.4, -5.0, 20.0), (5.0, -5.5, 5.0), (10, -5.5, 5.0)]),
    "o3": ("O", [(0, 5.0, 20.0), (1.4, 5.0, 20.0), (5.0, 5.5, 5.0), (10, 5.5, 5.0)]),
    "o4": ("O", [(0, -1.5, 23.5), (10, -1.5, 23.5)]),
    "o5": ("O", [(0, 2.0, 23.5), (10, 2.0, 23.5)]),
    "d1": ("D", [(0, 0.2, 13.0), (1.5, 0.2, 13.0), (5.0, 0.2, 7.5), (10, 0.2, 7.5)]),  # top of the tandem
    "d2": ("D", [(0, -0.3, 6.0), (1.5, -0.3, 6.0), (5.0, -0.2, 2.5), (10, -0.2, 2.5)]),  # bottom
    "d3": ("D", [(0, -3.0, 24.0), (10, -3.0, 24.0)]),
    "d4": ("D", [(0, 3.5, 24.5), (10, 3.5, 24.5)]),
    "d5": ("D", [(0, 0.0, 24.8), (0.5, 0.0, 24.8), (1.0, 0.8, 22.3), (10, 0.8, 22.3)]),  # loses the ball
}
TANDEM_BALL = [
    ("hold", 0, 0.8, "d5"),
    ("fly", 0.8, 1.2, "d5", "o1"),
    ("hold", 1.2, 5.8, "o1"),
    ("fly", 5.8, 6.2, "o1", RIM),
    ("fly", 6.2, 6.8, RIM, (0.0, -1.0)),
]

WALL_ACTORS = {
    "o1": ("O", [(0, 0.0, 21.0), (2.0, 0.0, 21.0), (8.0, 0.0, 11.8), (12, 0.0, 11.8)]),
    "o2": ("O", [(0, -5.0, 21.0), (2.0, -5.0, 21.0), (7.0, -5.5, 8.0), (12, -5.5, 8.0)]),
    "o3": ("O", [(0, 5.0, 21.0), (2.0, 5.0, 21.0), (7.0, 5.5, 8.0), (12, 5.5, 8.0)]),
    "o4": ("O", [(0, -2.0, 23.0), (2.0, -2.0, 23.0), (7.5, -2.5, 5.5), (12, -2.5, 5.5)]),
    "o5": ("O", [(0, 2.0, 23.0), (2.0, 2.0, 23.0), (7.5, 2.5, 5.5), (12, 2.5, 5.5)]),
    "d1": ("D", [(0, -2.6, 11.0), (8.0, -2.6, 11.0), (9.5, -2.0, 4.5), (12, -2.0, 4.5)]),
    "d2": ("D", [(0, 0.0, 10.4), (12, 0.0, 10.4)]),  # loses the ball, stops it
    "d3": ("D", [(0, 2.6, 11.0), (8.0, 2.6, 11.0), (9.5, 2.0, 4.5), (12, 2.0, 4.5)]),
    "d4": ("D", [(0, -0.8, 2.0), (5.5, -0.8, 2.0), (8.5, -4.5, 7.0), (12, -4.5, 7.0)]),
    "d5": ("D", [(0, 0.8, 2.5), (5.5, 0.8, 2.5), (8.5, 4.5, 7.0), (12, 4.5, 7.0)]),
}
WALL_BALL = [("hold", 0.0, 0.6, "d2"), ("fly", 0.6, 1.2, "d2", "o1"), ("hold", 1.2, 12.0, "o1")]

PULL_ACTORS = dict(BREAK_ACTORS)
PULL_ACTORS["o1"] = (
    "O",
    [
        (0, 3.0, 17.0),
        (1.4, 3.0, 17.0),
        (2.6, 5.5, 20.5),
        (3.0, 5.5, 20.5),
        (5.5, 2.0, 8.5),
        (5.6, 2.0, 8.5),
        (6.6, 3.0, 12.0),
        (10, 3.0, 12.0),
    ],
)
PULL_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.0, FAR, "o5"),
    ("hold", 2.0, 2.6, "o5"),
    ("fly", 2.6, 3.0, "o5", "o1"),
    ("hold", 3.0, 10.0, "o1"),
]

JAM_ACTORS = dict(BREAK_ACTORS)
JAM_ACTORS["d2"] = ("D", [(0, -3.0, 21.0), (1.0, -3.0, 21.0), (2.0, -1.0, 22.1), (3.4, -1.0, 22.1), (8.0, 0.3, 1.0)])
JAM_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.0, FAR, "o5"),
    ("hold", 2.0, 3.4, "o5"),
    ("fly", 3.4, 3.8, "o5", "o1"),
    ("hold", 3.8, 7.0, "o1"),
]

HALF_ACTORS = {
    "o1": ("O", [(0, 0.0, 8.5), (10, 0.0, 8.5)]),
    "o2": ("O", [(0, -5.5, 6.0), (10, -5.5, 6.0)]),
    "o3": ("O", [(0, 5.5, 6.0), (10, 5.5, 6.0)]),
    "o4": ("O", [(0, -6.8, 0.5), (10, -6.8, 0.5)]),
    "o5": ("O", [(0, 6.8, 0.5), (10, 6.8, 0.5)]),
    "d1": ("D", [(0, 0.0, 7.2), (10, 0.0, 7.2)]),
    "d2": ("D", [(0, -4.6, 5.0), (10, -4.6, 5.0)]),
    "d3": ("D", [(0, 4.6, 5.0), (10, 4.6, 5.0)]),
    "d4": ("D", [(0, -5.6, 0.8), (10, -5.6, 0.8)]),
    "d5": ("D", [(0, 5.6, 0.8), (10, 5.6, 0.8)]),
}
HALF_BALL = [
    ("hold", 0, 3.0, "o1"),
    ("fly", 3.0, 3.5, "o1", "o2"),
    ("hold", 3.5, 6.0, "o2"),
    ("fly", 6.0, 6.5, "o2", "o1"),
    ("hold", 6.5, 10.0, "o1"),
]

SCENARIOS = {
    "break": (BREAK_ACTORS, BREAK_BALL, 11.0, 1),
    "slow": (SLOW_ACTORS, SLOW_BALL, 12.0, 2),
    "leak": (LEAK_ACTORS, LEAK_BALL, 8.0, 3),
    "held": (HELD_ACTORS, HELD_BALL, 8.0, 4),
    "steal2": (STEAL2_ACTORS, STEAL2_BALL, 8.0, 5),
    "drag": (_drag_actors(True), DRAG_BALL, 10.0, 6),
    "drag1": (_drag_actors(False), DRAG_BALL, 10.0, 7),
    "pitch": (PITCH_ACTORS, PITCH_BALL, 10.0, 8),
    "made": (MADE_ACTORS, MADE_BALL, 9.0, 9),
    "homerun": (HOMERUN_ACTORS, HOMERUN_BALL, 9.0, 10),
    "press": (PRESS_ACTORS, PRESS_BALL, 8.0, 11),
    "pressb": (PRESSB_ACTORS, PRESSB_BALL, 12.0, 12),
    "blob": (BLOB_ACTORS, BLOB_BALL, 6.0, 13),
    "blobstack": (BLOBSTACK_ACTORS, BLOBSTACK_BALL, 6.0, 14),
    "slob": (SLOB_ACTORS, SLOB_BALL, 6.0, 15),
    "ft": (FT_ACTORS, FT_BALL, 6.0, 16),
    "ftstatic": (FTSTATIC_ACTORS, FT_BALL, 6.0, 17),
    "tandem": (TANDEM_ACTORS, TANDEM_BALL, 8.0, 18),
    "wall": (WALL_ACTORS, WALL_BALL, 12.0, 19),
    "pull": (PULL_ACTORS, PULL_BALL, 10.0, 20),
    "jam": (JAM_ACTORS, JAM_BALL, 8.0, 21),
    "half": (HALF_ACTORS, HALF_BALL, 10.0, 22),
}


def build(actors, ball, dur, seed, sigma=SIGMA):
    """sim.scenario for the players plus a scripted, noisy ball track; returns the mvlib Scene."""
    spec = {"actors": {a: {"team": tm, "wp": wp} for a, (tm, wp) in actors.items()}}
    truth, tracks = sim.scenario(spec, dur, sigma, seed)
    n = len(tracks[0].x)
    bx, by = np.full(n, np.nan), np.full(n, np.nan)

    def fr(t):
        return min(n - 1, int(round(t / DT)))

    def pos(s, i):
        return (truth[s][0][i], truth[s][1][i]) if isinstance(s, str) else s

    for ev in ball:
        if ev[0] == "hold":
            _, t0, t1, a = ev
            i0, i1 = fr(t0), fr(t1)
            bx[i0 : i1 + 1], by[i0 : i1 + 1] = truth[a][0][i0 : i1 + 1], truth[a][1][i0 : i1 + 1]
        else:
            _, t0, t1, s, d = ev
            i0, i1 = fr(t0), fr(t1)
            (x0, y0), (x1, y1) = pos(s, i0), pos(d, i1)
            u = np.linspace(0.0, 1.0, i1 - i0 + 1)
            bx[i0 : i1 + 1], by[i0 : i1 + 1] = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
    tr = sim.observe(
        np.nan_to_num(bx), np.nan_to_num(by), sigma * 0.7, np.random.default_rng(seed + 1000), oid="ball", role="ball"
    )
    tr.x[np.isnan(bx)] = np.nan
    tr.y[np.isnan(by)] = np.nan
    return mv.build_scene(tracks + [tr], offense_team="O")


@functools.lru_cache(maxsize=None)
def scene(name):
    a, b, d, s = SCENARIOS[name]
    return build(a, b, d, s)


@functools.lru_cache(maxsize=None)
def oracle(name):
    """The same scenario at sigma_p 0.1: the definition applied to a near-truth path (lower noise keeps the
    chi-square stationarity test meaningful, which a near-zero sigma would make arbitrarily strict)."""
    a, b, d, s = SCENARIOS[name]
    return build(a, b, d, s, sigma=0.1)


@functools.lru_cache(maxsize=None)
def run(det, name, truth=False):
    return tuple(T.DETECTORS[det](oracle(name) if truth else scene(name)))


def match(evs, kind, actors):
    return [e for e in evs if e.kind == kind and all(e.actors.get(k) == v for k, v in actors.items())]


def check(det, name, kind, actors, t0=None, conf=(0.5, 1.0), **attrs):
    """Positive: an event of `kind` with `actors` whose t0 is within TOL of the expected t0 (s, or the oracle's)."""
    evs = match(run(det, name), kind, actors)
    assert (
        evs
    ), f"{det} found no {kind} {actors} in {name}: {[(e.kind, e.actors, round(e.t0 * DT, 2)) for e in run(det, name)]}"
    if t0 is None:
        tev = match(run(det, name, truth=True), kind, actors)
        assert tev, f"oracle found no {kind} {actors} in {name}"
        t0 = tev[0].t0 * DT
    best = min(evs, key=lambda e: abs(e.t0 * DT - t0))
    assert abs(best.t0 * DT - t0) <= TOL, f"{det}: t0 {best.t0 * DT:.2f} vs expected {t0:.2f}"
    assert conf[0] <= best.conf <= conf[1], f"{det}: conf {best.conf:.3f} outside {conf}"
    for k, v in attrs.items():
        assert best.attrs.get(k) == v, f"{det}: attr {k} = {best.attrs.get(k)!r}, expected {v!r}"
    return best


def absent(det, name, kind=None, **actors):
    """Negative: no event (of `kind`, with these actors) at label level (conf >= 0.3) in the scenario."""
    evs = [
        e
        for e in run(det, name)
        if (kind is None or e.kind == kind) and all(e.actors.get(k) == v for k, v in actors.items())
    ]
    evs = [e for e in evs if e.conf >= 0.3]
    assert (
        not evs
    ), f"{det} unexpectedly fired in {name}: {[(e.kind, e.actors, round(e.t0 * DT, 2), round(e.conf, 2)) for e in evs]}"


# --------------------------------------------------------------------------------------
# Spec integrity
# --------------------------------------------------------------------------------------
def test_yaml_items_have_required_fields_and_units():
    req = {
        "id",
        "level",
        "name",
        "aliases",
        "actors",
        "t0",
        "rule",
        "params",
        "min_duration_s",
        "outputs",
        "confidence",
        "noise",
        "conflicts_resolved",
        "sources",
        "status",
    }
    assert T.CFG["family"] == "transition" and T.CFG["version"] == "0.1.4" and str(T.CFG["date"]) == "2026-10-22"
    for it in T.CFG["items"]:
        assert req <= set(it), (it["id"], req - set(it))
        assert it["level"] in ("primitive", "action", "set_component", "rule")
        assert it["status"] in ("canonical", "proposal")
        for k, v in it["params"].items():
            assert "value" in v and "unit" in v, (it["id"], k)


def test_every_detectable_item_has_a_detector_and_needs_data_ones_return_nothing():
    for it in T.CFG["items"]:
        if it["level"] != "rule" or it["id"] in T.DETECTORS:
            assert it["id"] in T.DETECTORS, it["id"]
    assert set(T.NEEDS_DATA) == {
        "jump_ball_release",
        "hold_for_one",
        "jump_ball_tip",
        "take_foul",
        "ato",
        "late_clock",
        "end_of_game",
        "jump_ball_alignment",
    }
    for det in T.NEEDS_DATA:
        assert T.DETECTORS[det](scene("break")) == []
        assert T.DETECTORS[det](scene("half")) == []


def test_params_come_from_yaml_and_overrides_are_checked():
    assert T.PARAMS["rim_run"]["min_path_m"] == 18.0
    assert T.PARAMS["numbers_advantage"]["margin_m"] == 1.0
    with pytest.raises(TypeError):
        T.detect_rim_run(scene("break"), not_a_param=1)
    # a stricter override removes the label
    assert not T.detect_push(scene("break"), min_speed_mps=9.0)


def test_detect_all_returns_every_detector():
    res = T.detect_all(scene("break"))
    assert set(res) == set(T.DETECTORS)
    assert all(isinstance(e, mv.Event) for evs in res.values() for e in evs)


# --------------------------------------------------------------------------------------
# Rules
# --------------------------------------------------------------------------------------
def test_possession_change():
    check("possession_change", "break", "possession_change", {"gainer": "o5", "loser": "d1"}, 2.0, start_type="dreb")
    check("possession_change", "leak", "possession_change", {"gainer": "o1", "loser": "d1"}, 2.0, start_type="steal")
    check("possession_change", "made", "possession_change", {"gainer": "o5"}, 3.5, start_type="made_fg")
    absent("possession_change", "half")


def test_transition_phase():
    ev = check("transition_phase", "break", "transition", {"gainer": "o5"}, 2.0)
    assert ev.attrs["end_reason"] == "settled"
    absent("transition_phase", "half")


def test_early_offense_window():
    check("early_offense_window", "break", "early_offense", {"gainer": "o5"}, end_reason="shot")
    absent("early_offense_window", "half")


def test_numbers_advantage():
    ev = check("numbers_advantage", "tandem", "numbers_advantage", {"gainer": "o1"})
    assert ev.attrs["config"] == "3v2" and ev.attrs["typology"] == "prim_conte"
    absent("numbers_advantage", "slow")


def test_throw_in():
    ev = check(
        "throw_in", "made", "throw_in", {"thrower": "o5", "receiver": "o1"}, 3.1, restart_type="backcourt_endline"
    )
    truth = match(run("throw_in", "made", truth=True), "throw_in", {"thrower": "o5"})[0]
    assert abs(ev.attrs["count_s"] - truth.attrs["count_s"]) <= TOL
    check("throw_in", "blob", "throw_in", {"thrower": "o5", "receiver": "o1"}, 3.2, restart_type="blob")
    absent("throw_in", "break")


# --------------------------------------------------------------------------------------
# Primitives
# --------------------------------------------------------------------------------------
def test_upcourt_run():
    check("upcourt_run", "break", "upcourt_run", {"runner": "o4"})
    check("upcourt_run", "break", "upcourt_run", {"runner": "o2"})
    absent("upcourt_run", "slow")


def test_rim_run():
    ev = check("rim_run", "break", "rim_run", {"runner": "o4"})
    assert ev.attrs["path_m"] >= 18.0 and ev.attrs["first_big_down"]
    absent("rim_run", "slow")
    absent("rim_run", "break", runner="o2")


def test_wing_lane_run():
    check("wing_lane_run", "break", "wing_lane_run", {"runner": "o2"}, lane="sideline", side=-1)
    check("wing_lane_run", "break", "wing_lane_run", {"runner": "o3"}, lane="sideline", side=1)
    absent("wing_lane_run", "slow")
    absent("wing_lane_run", "break", runner="o4")


def test_corner_fill():
    check("corner_fill", "break", "corner_fill", {"runner": "o2"})
    absent("corner_fill", "slow")


def test_middle_lane_run():
    check("middle_lane_run", "break", "middle_lane_run", {"runner": "o4"})
    absent("middle_lane_run", "slow")
    absent("middle_lane_run", "break", runner="o2")


def test_leak_out():
    check("leak_out", "leak", "leak_out", {"runner": "o3"}, sub_type="early_leak")
    absent("leak_out", "break")


def test_trailer():
    check("trailer", "break", "trailer", {"trailer": "o5"}, rank=2)
    absent("trailer", "leak")


def test_outlet_release():
    check("outlet_release", "break", "outlet_release", {"receiver": "o1", "rebounder": "o5"}, caught=True)
    absent("outlet_release", "slow")


def test_push():
    check("push", "break", "push", {"handler": "o1"})
    absent("push", "slow")


def test_diagonal_dribble():
    check("diagonal_dribble", "pitch", "diagonal_dribble", {"handler": "o1"})
    absent("diagonal_dribble", "break")


def test_pull_back():
    check("pull_back", "pull", "pull_back", {"handler": "o1"}, trigger="a")
    absent("pull_back", "break")


def test_retreat():
    check("retreat", "break", "retreat", {"player": "d3"})
    check("retreat", "break", "retreat", {"player": "d1"})
    absent("retreat", "slow")


def test_shot_rebound_decision():
    check(
        "shot_rebound_decision", "break", "shot_rebound_decision", {"player": "d2", "shooter": "d1"}, 1.0, cls="crash"
    )
    check("shot_rebound_decision", "break", "shot_rebound_decision", {"player": "d3"}, 1.0, cls="PO")
    absent("shot_rebound_decision", "leak")


def test_safety():
    check("safety", "break", "safety", {"player": "d3", "shooter": "d1"}, 2.0, variant="repo")
    absent("safety", "slow")


def test_protect_rim():
    check("protect_rim", "break", "protect_rim", {"defender": "d2"})
    absent("protect_rim", "slow")


def test_inbounder_step_in():
    check("inbounder_step_in", "made", "inbounder_step_in", {"thrower": "o5"})
    check("inbounder_step_in", "blob", "inbounder_step_in", {"thrower": "o5"})
    absent("inbounder_step_in", "homerun")


def test_run_endline():
    check("run_endline", "made", "run_endline", {"thrower": "o5"}, after_make=True)
    absent("run_endline", "homerun")


def test_inbound_get_open():
    check("inbound_get_open", "blob", "inbound_get_open", {"player": "o1", "thrower": "o5"}, cls="v_cut", receives=True)
    check("inbound_get_open", "slob", "inbound_get_open", {"player": "o2"}, cls="flash", receives=True)
    absent("inbound_get_open", "slob", player="o4")
    absent("inbound_get_open", "half")


def test_ft_lane_entry():
    check("ft_lane_entry", "ft", "ft_lane_entry", {"player": "o2", "shooter": "o1"}, early_entry_candidate=False)
    absent("ft_lane_entry", "ftstatic")


def test_ft_release_runner():
    check("ft_release_runner", "ft", "ft_release_runner", {"runner": "d5"}, role="ft_leak")
    absent("ft_release_runner", "ftstatic")


def test_press_flash_middle():
    check("press_flash_middle", "press", "press_flash_middle", {"player": "o3"}, middle_catch=True)
    absent("press_flash_middle", "break")


def test_sideline_release():
    check("sideline_release", "press", "sideline_release", {"player": "o4"}, 2.4)
    absent("sideline_release", "pressb")


def test_press_safety():
    check("press_safety", "pressb", "press_safety", {"player": "o5"})
    absent("press_safety", "break")


def test_build_wall():
    check("build_wall", "wall", "build_wall", {})
    absent("build_wall", "break")


def test_sink_to_paint():
    check("sink_to_paint", "wall", "sink_to_paint", {})
    absent("sink_to_paint", "break")


# --------------------------------------------------------------------------------------
# Actions
# --------------------------------------------------------------------------------------
def test_outlet_pass():
    ev = check("outlet_pass", "break", "outlet_pass", {"rebounder": "o5", "receiver": "o1"}, 2.6, quick=True)
    assert ev.attrs["spot"] == "outlet_ballside" and ev.attrs["ctg_compatible"]
    check("outlet_pass", "slow", "dribble_out", {"rebounder": "o5"}, 2.0)
    absent("outlet_pass", "slow", kind="outlet_pass")


def test_hit_ahead():
    check("hit_ahead", "leak", "hit_ahead", {"passer": "o1", "receiver": "o3"}, 2.6, passed_before_timeline=True)
    absent("hit_ahead", "break")


def test_drag_screen():
    check("drag_screen", "drag1", "drag_screen", {"handler": "o1", "screener": "o5"}, screener_action="roll")
    absent("drag_screen", "break")


def test_double_drag():
    check("double_drag", "drag", "double_drag", {"handler": "o1"})
    absent("double_drag", "drag1")


def test_trailer_pitch_back():
    check("trailer_pitch_back", "pitch", "trailer_pitch_back", {"passer": "o1", "trailer": "o5"}, 7.4)
    absent("trailer_pitch_back", "break")


def test_rim_runner_hit():
    check("rim_runner_hit", "break", "rim_runner_hit", {"passer": "o1", "runner": "o4"}, 7.0)
    absent("rim_runner_hit", "slow")


def test_stop_ball():
    check("stop_ball", "wall", "stop_ball", {"handler": "o1", "defender": "d2"})
    absent("stop_ball", "slow")


def test_jam_rebounder():
    check("jam_rebounder", "jam", "jam_rebounder", {"rebounder": "o5", "defender": "d2"}, 2.0)
    absent("jam_rebounder", "break")


def test_matchup():
    check("matchup", "wall", "matchup", {"gainer": "o1"})
    absent("matchup", "break")


def test_tandem_stack():
    check("tandem_stack", "tandem", "tandem_stack", {"top": "d1", "bottom": "d2"})
    absent("tandem_stack", "wall")


def test_run_out():
    # loop 1 (TRN-T09): the stealer o1 stands still and hits the leaker ahead; the run-out is o3 taking it to the rim
    check("run_out", "leak", "run_out", {"handler": "o3"})
    absent("run_out", "leak", handler="o1")
    absent("run_out", "steal2")


def test_screen_the_inbounder():
    check("screen_the_inbounder", "blob", "screen_the_inbounder", {"inbounder": "o5", "screener": "o3"})
    absent("screen_the_inbounder", "slob")


def test_press_trap():
    ev = check("press_trap", "press", "press_trap", {"handler": "o1"})
    assert {ev.actors["defender_1"], ev.actors["defender_2"]} == {"d1", "d2"}
    assert {"trap_backcourt_corner", "backcourt_corner_trap"} & set(ev.attrs["locations"])
    absent("press_trap", "pressb")


def test_trap_breaker_pass():
    check("trap_breaker_pass", "press", "trap_breaker_pass", {"passer": "o1", "receiver": "o5"}, 4.6)
    absent("trap_breaker_pass", "pressb")


def test_press_reversal():
    check("press_reversal", "press", "press_reversal", {"passer": "o1", "receiver": "o5"}, 4.6)
    absent("press_reversal", "pressb")


def test_home_run_inbound():
    check("home_run_inbound", "homerun", "home_run_inbound", {"thrower": "o5", "receiver": "o3"}, 5.0, target=True)
    absent("home_run_inbound", "made")


def test_ft_box_out():
    check("ft_box_out", "ft", "ft_box_out", {"defender": "d1", "attacker": "o2"})
    absent("ft_box_out", "ftstatic")


def test_tag_and_recover():
    check("tag_and_recover", "leak", "tag_and_recover", {"defender": "d4", "leaker": "o3"})
    absent("tag_and_recover", "break")


# --------------------------------------------------------------------------------------
# Set components
# --------------------------------------------------------------------------------------
def test_primary_break():
    check("primary_break", "break", "primary_break", {"gainer": "o5", "shooter": "o4"}, 2.0)
    absent("primary_break", "slow")


def test_secondary_break():
    ev = check("secondary_break", "drag1", "secondary_break", {"gainer": "o5"})
    assert "drag_screen" in ev.attrs["actions"]
    absent("secondary_break", "break")


def test_early_offense_sequence():
    ev = check("early_offense_sequence", "break", "early_offense_sequence", {"gainer": "o5"}, 2.0)
    name = ev.attrs["compositional_name"]
    assert name.startswith("dreb -> outlet(outlet_ballside) -> push -> primary"), name
    assert [s["kind"] for s in ev.attrs["action_sequence"]][:1] and "rim_run" in [
        s["kind"] for s in ev.attrs["action_sequence"]
    ]
    absent("early_offense_sequence", "half")


def test_push_after_make():
    check("push_after_make", "made", "push_after_make", {"inbounder": "o5", "receiver": "o1"}, 1.5)
    absent("push_after_make", "homerun")


def test_passed_up_break():
    check("passed_up_break", "held", "passed_up_break", {"gainer": "o1"}, condition="held_ball", category="declined")
    absent("passed_up_break", "leak")


def test_defensive_transition_scheme():
    check(
        "defensive_transition_scheme",
        "break",
        "defensive_transition_scheme",
        {"shooter": "d1"},
        1.0,
        label="everyone_back",
    )
    absent("defensive_transition_scheme", "leak")


def test_press_active():
    check("press_active", "press", "press_active", {})
    absent("press_active", "break")
    absent("press_active", "half")


def test_press_fall_back():
    check("press_fall_back", "pressb", "press_fall_back", {})
    absent("press_fall_back", "press")


def test_press_break_alignment():
    check("press_break_alignment", "press", "press_break_alignment", {"thrower": "o5"}, 0.5, template="4_across")
    absent("press_break_alignment", "pressb")


def test_blob_alignment():
    check("blob_alignment", "blob", "blob_alignment", {"thrower": "o5"}, 0.5, alignment="box")
    check("blob_alignment", "blobstack", "blob_alignment", {"thrower": "o5"}, 0.5, alignment="stack")
    absent("blob_alignment", "slob")


def test_slob_alignment():
    check("slob_alignment", "slob", "slob_alignment", {"thrower": "o5"}, 0.5, alignment="line")
    absent("slob_alignment", "blob")


def test_ft_alignment():
    ev = check("ft_alignment", "ft", "ft_alignment", {"shooter": "o1"}, 2.0)
    assert ev.attrs["n_lane"] == 6 and ev.attrs["leakers"] == ["d5"]
    absent("ft_alignment", "half")


# --------------------------------------------------------------------------------------
# Loop 1 regressions (changes_loop1 in the YAML). Scenarios marked [tester] are copied from the independent tester's
# scenarios.py (scratchpad test_transition/); every check below failed (or was missing) before loop 1.
# --------------------------------------------------------------------------------------
_MRP_D = {
    "d1": ("D", [(0, 2.0, 19.5), (1.2, 2.0, 19.5), (5.5, 2.0, 6.0), (9, 2.0, 6.0)]),  # shooter (made)
    "d2": ("D", [(0, -3.0, 21.0), (1.2, -3.0, 21.0), (5.5, -3.0, 5.0), (9, -3.0, 5.0)]),
    "d3": ("D", [(0, 5.0, 20.0), (1.2, 5.0, 20.0), (5.5, 4.5, 4.0), (9, 4.5, 4.0)]),
    "d4": ("D", [(0, -5.5, 18.0), (1.2, -5.5, 18.0), (5.5, -5.0, 4.0), (9, -5.0, 4.0)]),
    "d5": ("D", [(0, 0.5, 23.5), (1.5, 0.5, 23.5), (6.5, 0.0, 2.0), (9, 0.0, 2.0)]),
}
NETCATCH_ACTORS = {  # [tester] made_runendline_push: the inbounder catches under the net IN bounds, then steps out
    **_MRP_D,
    "o5": (
        "O",
        [
            (0, 1.0, 24.8),
            (1.0, 1.0, 24.8),
            (1.95, 0.8, 27.4),
            (2.05, 0.8, 27.4),
            (2.95, -2.2, 27.4),
            (3.1, -2.2, 27.4),
            (4.3, -1.5, 24.5),
            (9, -1.5, 24.5),
        ],
    ),
    "o1": (
        "O",
        [(0, -4.0, 18.5), (1.5, -4.0, 18.5), (3.0, -4.5, 23.5), (3.5, -4.5, 23.5), (7.5, -1.0, 8.0), (9, -1.0, 8.0)],
    ),
    "o2": ("O", [(0, -6.0, 15.0), (2.0, -6.0, 15.0), (7.0, -6.9, 1.2), (9, -6.9, 1.2)]),
    "o3": ("O", [(0, 5.5, 16.0), (2.0, 5.5, 16.0), (7.0, 6.9, 1.2), (9, 6.9, 1.2)]),
    "o4": ("O", [(0, -1.0, 22.0), (2.0, -1.0, 22.0), (8.0, -0.5, 5.0), (9, -0.5, 5.0)]),
}
NETCATCH_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.4, "d1", FAR),
    ("fly", 1.4, 1.9, FAR, (0.8, 27.4)),
    ("hold", 2.0, 3.0, "o5"),
    ("fly", 3.0, 3.4, "o5", "o1"),
    ("hold", 3.4, 7.6, "o1"),
    ("fly", 7.6, 7.9, "o1", RIM),
]
OOBPICK_ACTORS = {  # [tester] made_oob_pickup: the ball rests out of bounds, the inbounder walks to it
    **NETCATCH_ACTORS,
    "o5": (
        "O",
        [
            (0, 2.5, 27.6),
            (1.9, 2.5, 27.6),
            (2.4, 0.8, 27.6),
            (2.5, 0.8, 27.6),
            (3.2, -1.8, 27.6),
            (3.35, -1.8, 27.6),
            (4.5, -1.5, 24.5),
            (9, -1.5, 24.5),
        ],
    ),
    "o1": (
        "O",
        [(0, -4.0, 18.5), (1.6, -4.0, 18.5), (3.2, -4.5, 23.5), (3.7, -4.5, 23.5), (7.7, -1.0, 8.0), (9, -1.0, 8.0)],
    ),
}
OOBPICK_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.4, "d1", FAR),
    ("fly", 1.4, 1.9, FAR, (0.8, 27.6)),
    ("fly", 1.9, 2.4, (0.8, 27.6), (0.8, 27.6)),
    ("hold", 2.45, 3.25, "o5"),
    ("fly", 3.25, 3.65, "o5", "o1"),
    ("hold", 3.65, 7.8, "o1"),
    ("fly", 7.8, 8.1, "o1", RIM),
]
DEFLECT_ACTORS = {  # [tester] halfcourt_oreb_deflect: offensive rebound, then a 0.15 s deflection by d2
    "o1": ("O", [(0, 0.0, 8.0), (10, 0.0, 8.0)]),
    "o2": ("O", [(0, -5.5, 5.5), (10, -5.5, 5.5)]),
    "o3": ("O", [(0, 5.5, 5.5), (10, 5.5, 5.5)]),
    "o4": (
        "O",
        [(0, -2.5, 2.0), (1.8, -2.5, 2.0), (2.6, -0.8, 0.9), (4.0, -0.8, 0.9), (5.0, -2.5, 3.0), (10, -2.5, 3.0)],
    ),
    "o5": ("O", [(0, 2.5, 2.0), (10, 2.5, 2.0)]),
    "d1": ("D", [(0, 0.0, 6.8), (10, 0.0, 6.8)]),
    "d2": ("D", [(0, -3.0, 6.5), (5.4, -3.0, 6.5), (5.9, -2.1, 6.9), (6.4, -3.0, 6.5), (10, -3.0, 6.5)]),
    "d3": ("D", [(0, 4.5, 4.8), (10, 4.5, 4.8)]),
    "d4": ("D", [(0, -1.6, 1.2), (10, -1.6, 1.2)]),
    "d5": ("D", [(0, 1.6, 1.2), (10, 1.6, 1.2)]),
}
DEFLECT_BALL = [
    ("hold", 0, 1.5, "o1"),
    ("fly", 1.5, 2.2, "o1", RIM),
    ("fly", 2.2, 2.6, RIM, "o4"),
    ("hold", 2.6, 4.0, "o4"),
    ("fly", 4.0, 4.4, "o4", "o1"),
    ("hold", 4.4, 5.6, "o1"),
    ("fly", 5.6, 5.9, "o1", "d2"),
    ("hold", 5.9, 6.05, "d2"),
    ("fly", 6.05, 6.5, "d2", "o2"),
    ("hold", 6.5, 10.0, "o2"),
]
_DRAG_D2 = {
    "d1": ("D", [(0, 2.0, 18.5), (1.2, 2.0, 18.5), (5.5, 2.5, 7.0), (11.0, 2.5, 7.0)]),
    "d2": (
        "D",
        [(0, -3.0, 21.0), (1.0, -3.0, 21.0), (2.0, -1.5, 24.0), (2.6, -1.5, 24.0), (8.0, -3.5, 3.0), (11, -3.5, 3.0)],
    ),
    "d3": ("D", [(0, 5.0, 15.0), (1.0, 5.0, 15.0), (5.0, 5.5, 2.0), (11.0, 5.5, 2.0)]),
    "d4": ("D", [(0, -5.5, 16.0), (1.0, -5.5, 16.0), (5.0, -5.5, 2.0), (11.0, -5.5, 2.0)]),
    "d5": ("D", [(0, 2.0, 23.0), (2.5, 2.0, 23.0), (8.0, 0.5, 1.5), (11.0, 0.5, 1.5)]),
}
DRAGPOP_ACTORS = {  # [tester] secondary_drag_pop: wings first, the rim runner, the trailer, the handler LAST
    **_DRAG_D2,
    "o5": (
        "O",
        [
            (0, -1.2, 22.8),
            (1.5, -1.2, 22.8),
            (2.0, -1.0, 23.4),
            (2.6, -1.0, 23.4),
            (7.0, 2.1, 8.0),
            (8.0, 2.1, 8.0),
            (9.2, -1.5, 8.6),
            (11.0, -1.5, 8.6),
        ],
    ),
    "o1": (
        "O",
        [
            (0, 3.0, 17.5),
            (1.4, 3.0, 17.5),
            (2.6, 5.6, 20.6),
            (3.1, 5.6, 20.6),
            (7.0, 3.6, 9.4),
            (7.6, 3.2, 8.6),
            (9.5, -0.5, 4.0),
            (11.0, -0.5, 4.0),
        ],
    ),
    "o2": ("O", [(0, -5.0, 19.0), (2.2, -5.0, 19.0), (6.8, -6.9, 1.2), (11.0, -6.9, 1.2)]),
    "o3": ("O", [(0, 5.5, 22.0), (2.3, 5.5, 22.0), (7.0, 6.9, 1.2), (11.0, 6.9, 1.2)]),
    "o4": ("O", [(0, 0.5, 21.5), (2.2, 0.5, 21.5), (6.5, -1.5, 1.5), (11.0, -1.5, 1.5)]),
}
DRAGPOP_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.0, FAR, "o5"),
    ("hold", 2.0, 2.6, "o5"),
    ("fly", 2.6, 3.0, "o5", "o1"),
    ("hold", 3.0, 10.5, "o1"),
]
SHOOTERBACK_ACTORS = {  # [tester] shot_shooter_back: three crash, d2 ends 0.9 m from the rebounder
    "d1": ("D", [(0, 6.0, 18.5), (1.1, 6.0, 18.5), (3.5, 4.5, 10.0), (7.0, 3.5, 5.0)]),
    "d2": ("D", [(0, -1.5, 20.5), (1.0, -1.5, 20.5), (1.9, -0.6, 23.4), (3.2, -0.6, 23.4), (7.0, -0.5, 14.0)]),
    "d3": ("D", [(0, -4.5, 21.0), (1.0, -4.5, 21.0), (2.0, -1.8, 23.8), (7.0, -1.8, 23.8)]),
    "d4": ("D", [(0, 3.5, 21.5), (1.0, 3.5, 21.5), (2.0, 1.6, 24.2), (7.0, 1.6, 24.2)]),
    "d5": ("D", [(0, -6.5, 16.0), (7.0, -6.5, 16.0)]),
    "o5": ("O", [(0, 0.2, 22.0), (1.2, 0.2, 22.0), (1.9, 0.3, 23.0), (3.3, 0.3, 23.0), (7.0, 0.5, 15.0)]),
    "o1": ("O", [(0, 5.0, 17.5), (1.5, 5.0, 17.5), (2.6, 5.6, 20.5), (7.0, 4.0, 12.0)]),
    "o2": ("O", [(0, -2.5, 19.5), (7.0, -2.5, 19.5)]),
    "o3": ("O", [(0, -4.0, 22.0), (7.0, -4.0, 22.0)]),
    "o4": ("O", [(0, 2.5, 22.5), (7.0, 2.5, 22.5)]),
}
SHOOTERBACK_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 1.9, FAR, "o5"),
    ("hold", 1.9, 3.3, "o5"),
    ("fly", 3.3, 3.7, "o5", "o1"),
    ("hold", 3.7, 7.0, "o1"),
]
_DHA = {
    "d2": ("D", [(0, 4.5, 20.0), (2.0, 4.5, 20.0), (7.0, 3.5, 12.0)]),
    "d1": ("D", [(0, -2.0, 19.0), (1.5, -2.0, 19.0), (6.5, -2.0, 5.0)]),
    "d3": ("D", [(0, -5.5, 21.5), (1.0, -5.5, 21.5), (2.0, -3.0, 23.0), (2.3, -3.0, 23.0), (7.0, -4.0, 9.0)]),
    "d4": (
        "D",
        [(0, 3.5, 15.0), (1.3, 3.5, 15.0), (2.3, 3.4, 13.9), (2.6, 3.4, 13.9), (3.6, 0.5, 16.5), (7.0, 0.5, 16.5)],
    ),
    "d5": ("D", [(0, 1.5, 22.0), (1.0, 1.5, 22.0), (1.8, 1.0, 23.8), (7.0, 1.0, 23.8)]),
    "o1": ("O", [(0, -3.0, 17.0), (1.2, -3.0, 17.0), (2.5, -5.5, 20.5), (3.7, -5.5, 20.5), (7.0, -4.0, 12.0)]),
    "o2": ("O", [(0, -5.0, 19.0), (2.5, -5.0, 19.0), (7.0, -6.0, 6.0)]),
    "o4": ("O", [(0, 1.0, 21.0), (2.5, 1.0, 21.0), (7.0, 1.5, 14.0)]),
}
RIMREB_ACTORS = {  # [tester] rim_rebound_outlet: rebound secured 0.7 m from the far rim, quick outlet
    **_DHA,
    "o5": ("O", [(0, -0.6, 23.0), (1.2, -0.6, 23.0), (1.85, 0.2, 24.75), (2.4, 0.2, 24.75), (7.0, 0.0, 14.0)]),
    "o3": ("O", [(0, 5.0, 18.5), (7.0, 5.0, 18.5)]),
}
RIMREB_BALL = [
    ("hold", 0, 1.0, "d2"),
    ("fly", 1.0, 1.5, "d2", FAR),
    ("fly", 1.5, 1.85, FAR, "o5"),
    ("hold", 1.85, 2.3, "o5"),
    ("fly", 2.3, 2.7, "o5", "o1"),
    ("hold", 2.7, 7.0, "o1"),
]
_SB = {
    "d1": ("D", [(0, 1.0, 19.5), (1.8, 1.0, 19.5), (7.0, 0.0, 3.0), (13, 0.0, 3.0)]),
    "d2": ("D", [(0, -5.5, 21.0), (1.8, -5.5, 21.0), (8.0, -4.5, 6.0)]),
    "d3": ("D", [(0, 4.0, 22.5), (2.0, 4.0, 22.5), (8.5, 3.5, 5.0)]),
    "d4": ("D", [(0, -2.0, 24.0), (2.2, -2.0, 24.0), (9.0, -1.5, 4.0)]),
    "d5": ("D", [(0, 3.0, 25.0), (2.5, 3.0, 25.0), (9.0, 2.5, 10.0)]),
    "o2": ("O", [(0, -5.0, 20.0), (2.0, -5.0, 20.0), (7.5, -6.9, 1.2)]),
}
LATESHOT_ACTORS = {  # [tester] runout_pullback_late_shot: run-out, pulled back at 7 s, shot at 11.5 s
    **_SB,
    "o1": (
        "O",
        [
            (0, -1.8, 18.6),
            (1.0, -1.8, 18.6),
            (1.6, -2.5, 20.3),
            (1.8, -2.5, 20.3),
            (6.6, -1.5, 6.6),
            (7.0, -1.5, 6.6),
            (8.2, -2.0, 9.6),
            (13, -2.0, 9.6),
        ],
    ),
    "o3": ("O", [(0, 3.5, 21.5), (2.4, 3.5, 21.5), (9.0, 5.5, 6.0), (13, 5.5, 6.0)]),
    "o4": ("O", [(0, -1.5, 23.5), (2.5, -1.5, 23.5), (10.0, -5.5, 5.5), (13, -5.5, 5.5)]),
    "o5": ("O", [(0, 2.5, 24.0), (2.5, 2.5, 24.0), (10.5, 1.5, 10.0), (13, 1.5, 10.0)]),
}
LATESHOT_BALL = [
    ("hold", 0, 1.4, "d1"),
    ("fly", 1.4, 1.6, "d1", "o1"),
    ("hold", 1.6, 11.5, "o1"),
    ("fly", 11.5, 12.2, "o1", RIM),
    ("fly", 12.2, 12.6, RIM, (0.3, -1.0)),
]
PASSEDUP_ACTORS = {  # [tester] pullback_passed_up: dreb at the far rim, 2v1 forms 2-3 s later, the handler pulls out
    "d1": ("D", [(0, 1.5, 19.0), (1.2, 1.5, 19.0), (6.0, 0.5, 4.0), (11, 0.5, 4.0)]),
    "d2": ("D", [(0, -3.0, 21.0), (1.0, -3.0, 21.0), (2.0, -1.5, 24.0), (3.0, -1.5, 24.0), (11, -2.0, 14.0)]),
    "d3": ("D", [(0, 4.0, 21.5), (2.5, 4.0, 21.5), (11, 3.5, 13.5)]),
    "d4": ("D", [(0, -5.0, 22.0), (2.5, -5.0, 22.0), (11, -4.5, 14.0)]),
    "d5": ("D", [(0, 2.0, 23.5), (2.5, 2.0, 23.5), (11, 1.5, 15.0)]),
    "o5": ("O", [(0, -1.0, 22.5), (1.3, -1.0, 22.5), (2.0, -0.8, 23.4), (2.6, -0.8, 23.4), (11, -0.5, 15.0)]),
    "o1": (
        "O",
        [
            (0, 3.0, 17.0),
            (1.5, 3.0, 17.0),
            (2.6, 5.0, 20.3),
            (3.0, 5.0, 20.3),
            (6.4, 1.5, 8.6),
            (6.6, 1.5, 8.6),
            (7.8, 1.5, 12.0),
            (11, 1.5, 12.0),
        ],
    ),
    "o3": ("O", [(0, -5.0, 19.0), (2.3, -5.0, 19.0), (6.5, -5.5, 6.0), (11, -5.5, 6.0)]),
    "o2": ("O", [(0, 6.0, 15.5), (2.4, 6.0, 15.5), (6.6, 6.5, 4.0), (11, 6.5, 4.0)]),
    "o4": ("O", [(0, -2.0, 21.0), (2.5, -2.0, 21.0), (11, -2.0, 14.5)]),
}
PASSEDUP_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.0, FAR, "o5"),
    ("hold", 2.0, 2.6, "o5"),
    ("fly", 2.6, 3.0, "o5", "o1"),
    ("hold", 3.0, 11.0, "o1"),
]
FTEARLY_ACTORS = {  # [tester] ft_early_boxout: d1 steps 0.8 m in before the release; d1 / d3 stand near the FT path
    "o1": ("O", [(0, 0.0, 4.8), (6, 0.0, 4.8)]),
    "d1": ("D", [(0, 2.3, 1.3), (1.6, 2.3, 1.3), (2.0, 1.5, 1.2), (2.2, 1.5, 1.2), (2.7, 0.9, 0.9), (6, 0.9, 0.9)]),
    "o2": ("O", [(0, 2.3, 2.26), (2.1, 2.3, 2.26), (2.8, 1.4, 1.6), (6, 1.4, 1.6)]),
    "d3": ("D", [(0, 2.3, 3.2), (6, 2.3, 3.2)]),
    "d2": ("D", [(0, -2.3, 1.3), (6, -2.3, 1.3)]),
    "o3": ("O", [(0, -2.3, 2.26), (6, -2.3, 2.26)]),
    "d4": ("D", [(0, -2.3, 3.2), (6, -2.3, 3.2)]),
    "o4": ("O", [(0, 0.0, 7.5), (6, 0.0, 7.5)]),
    "d5": ("D", [(0, 3.0, 12.0), (2.1, 3.0, 12.0), (5.0, 2.0, 22.0), (6, 2.0, 22.0)]),
    "o5": ("O", [(0, -6.5, 6.0), (6, -6.5, 6.0)]),
}
WALLSINK_ACTORS = {  # [tester] wall_and_sink: d5 throws a forward pass from 6.5 m of the far rim, o1 picks it off
    "d5": ("D", [(0, 0.5, 19.0), (0.8, 0.5, 19.0), (4.0, 0.6, 11.6), (10, 0.6, 11.6)]),
    "d1": ("D", [(0, -0.6, 2.0), (10, -0.6, 2.0)]),
    "d2": ("D", [(0, 0.7, 3.0), (10, 0.7, 3.0)]),
    "d3": ("D", [(0, -2.0, 15.0), (1.5, -2.0, 15.0), (4.5, -1.8, 11.3), (10, -1.8, 11.3)]),
    "d4": ("D", [(0, 2.5, 14.5), (1.5, 2.5, 14.5), (4.5, 2.2, 11.0), (10, 2.2, 11.0)]),
    "o1": (
        "O",
        [(0, 0.0, 20.5), (0.4, 0.0, 20.5), (0.9, 0.3, 19.6), (1.5, 0.3, 19.6), (8.0, 0.0, 12.5), (10, 0.0, 12.5)],
    ),
    "o2": ("O", [(0, -5.5, 22.0), (1.5, -5.5, 22.0), (7.0, -6.0, 8.0), (10, -6.0, 8.0)]),
    "o3": ("O", [(0, 5.5, 22.0), (1.5, 5.5, 22.0), (7.0, 6.0, 8.0), (10, 6.0, 8.0)]),
    "o4": ("O", [(0, -2.0, 24.0), (2.0, -2.0, 24.0), (9.0, -2.0, 14.0), (10, -2.0, 14.0)]),
    "o5": ("O", [(0, 2.0, 24.0), (2.0, 2.0, 24.0), (9.0, 2.0, 14.5), (10, 2.0, 14.5)]),
}
WALLSINK_BALL = [("hold", 0, 0.5, "d5"), ("fly", 0.5, 0.9, "d5", "o1"), ("hold", 0.9, 10.0, "o1")]
FAILED_BALL = [
    ("hold", 0, 1.6, "d1"),
    ("fly", 1.6, 2.0, "d1", "o1"),
    ("hold", 2.0, 4.5, "o1"),
    ("fly", 4.5, 4.8, "o1", "d4"),
    ("hold", 4.8, 8.0, "d4"),
]  # the held break is stolen back by d4

SCENARIOS.update(
    {
        "netcatch": (NETCATCH_ACTORS, NETCATCH_BALL, 9.0, 23),
        "oobpick": (OOBPICK_ACTORS, OOBPICK_BALL, 9.0, 24),
        "deflect": (DEFLECT_ACTORS, DEFLECT_BALL, 10.0, 25),
        "dragpop": (DRAGPOP_ACTORS, DRAGPOP_BALL, 11.0, 26),
        "shooterback": (SHOOTERBACK_ACTORS, SHOOTERBACK_BALL, 7.0, 27),
        "rimreb": (RIMREB_ACTORS, RIMREB_BALL, 7.0, 28),
        "lateshot": (LATESHOT_ACTORS, LATESHOT_BALL, 13.0, 29),
        "passedup": (PASSEDUP_ACTORS, PASSEDUP_BALL, 11.0, 30),
        "ftearly": (FTEARLY_ACTORS, FT_BALL, 6.0, 31),
        "wallsink": (WALLSINK_ACTORS, WALLSINK_BALL, 10.0, 32),
        "failed": (HELD_ACTORS, FAILED_BALL, 8.0, 33),
    }
)


def test_loop1_t01_throw_in_after_a_catch_under_the_net():
    check(
        "possession_change",
        "netcatch",
        "possession_change",
        {"gainer": "o5", "loser": "d1"},
        3.45,
        start_type="made_fg",
    )
    ev = check(
        "throw_in",
        "netcatch",
        "throw_in",
        {"thrower": "o5", "receiver": "o1"},
        3.0,
        restart_type="backcourt_endline",
        after_make=True,
    )
    # counted from the step out (y >= FAR_END_Y - oob_tol_m from about 1.66 s), not from the in-bounds catch
    assert 1.5 <= ev.attrs["t_disposal"] * DT <= 2.0 and ev.attrs["count_s"] <= 1.5
    ev = check("run_endline", "netcatch", "run_endline", {"thrower": "o5"}, after_make=True)
    assert 1.5 <= ev.t0 * DT <= 2.3  # disposal = the step out behind the end line (the catch is ~1.7-2.0 s)
    check("push_after_make", "netcatch", "push_after_make", {"inbounder": "o5", "receiver": "o1"})
    check("inbounder_step_in", "netcatch", "inbounder_step_in", {"thrower": "o5"})


def test_loop1_t02_deflection_and_close_players_do_not_take_the_hold():
    absent("possession_change", "deflect")
    for det in ("protect_rim", "early_offense_sequence", "numbers_advantage", "matchup", "transition_phase"):
        absent(det, "deflect")
    assert any(tc[0] == "d2" for tc in T._touches(scene("deflect")))  # the touch is kept as a dropped touch
    # the drag screener standing 0.6 m from the handler never becomes a handler
    absent("drag_screen", "drag", handler="o4")
    absent("drag_screen", "drag", handler="o5")
    # holder hysteresis: the trapped handler keeps the ball at sigma_p 0.5
    a, b, d, s = SCENARIOS["press"]
    sc5 = build(a, b, d, s, sigma=0.5)
    holders = {h for h in T._holders(sc5)[int(2.6 / DT) : int(4.4 / DT)] if h is not None}
    assert holders == {"o1"}, holders
    found = 0
    for seed in range(12, 17):
        tr = [e for e in T.detect_press_trap(build(a, b, d, seed, sigma=0.5)) if e.actors["handler"] == "o1"]
        found += bool(tr) and {tr[0].actors["defender_1"], tr[0].actors["defender_2"]} == {"d1", "d2"}
    assert found >= 4, found


def test_loop1_t03_crasher_touch_keeps_the_rebound_a_dreb():
    for name, shooter in (("shooterback", "d1"), ("dragpop", "d1")):
        check("possession_change", name, "possession_change", {"gainer": "o5", "loser": shooter}, start_type="dreb")
        absent("run_out", name)
        absent("possession_change", name, start_type="steal")
    check("outlet_pass", "dragpop", "outlet_pass", {"rebounder": "o5", "receiver": "o1"}, 2.6)
    absent("outlet_pass", "dragpop", receiver="o3")  # the ball brushing o3 next to the catcher is not a pass


def test_loop1_t04_shot_proxy_uses_the_attacked_rim_and_a_closing_ball():
    check("possession_change", "rimreb", "possession_change", {"gainer": "o5", "loser": "d2"}, 1.85, start_type="dreb")
    check("outlet_pass", "rimreb", "outlet_pass", {"rebounder": "o5", "receiver": "o1"}, 2.3)
    absent("primary_break", "rimreb")
    assert not [s for s in T._shots(scene("rimreb")) if s["team"] == "O"]
    # a defender near the rim under the free throw's path does not take the ball: the FT release proxy survives
    check("ft_alignment", "ftearly", "ft_alignment", {"shooter": "o1"}, 2.0)
    check("ft_box_out", "ftearly", "ft_box_out", {"defender": "d1", "attacker": "o2"})


def test_loop1_t05_pulled_back_run_out_is_not_a_primary_break():
    check("run_out", "lateshot", "run_out", {"handler": "o1"})
    check("pull_back", "lateshot", "pull_back", {"handler": "o1"})
    absent("primary_break", "lateshot")
    check("primary_break", "break", "primary_break", {"gainer": "o5", "shooter": "o4"}, 2.0)


def test_loop1_t06_passed_up_break_after_a_far_rim_rebound():
    check("pull_back", "passedup", "pull_back", {"handler": "o1"}, with_advantage=True)
    ev = check("passed_up_break", "passedup", "passed_up_break", {"gainer": "o5"}, condition="pull_back_with_advantage")
    # d2 stands 0.9 m from the rebounder for 1 s after the rebound: a jam_rebounder by definition, hence 'denied'
    assert ev.attrs["category"] == "denied"
    assert any(j.actors["defender"] == "d2" for j in T.detect_jam_rebounder(scene("passedup")))


def test_loop1_t07_trailer_rank_counts_the_handler():
    check("trailer", "dragpop", "trailer", {"trailer": "o5"}, rank=1, tie_with_handler=False)
    absent("trailer", "dragpop", trailer="o4")  # the rim runner (3rd across) is never promoted
    # a handler crossing within tie_s of the 3rd across: the 3rd keeps trailer_1 (stored as a tie)
    check("trailer", "drag", "trailer", {"trailer": "o4"}, rank=1, tie_with_handler=True)


def test_loop1_t08_forward_pass_steal_is_not_block_to_break():
    ev = check(
        "possession_change", "wallsink", "possession_change", {"gainer": "o1", "loser": "d5"}, 0.95, start_type="steal"
    )
    assert ev.attrs["alt_start_type"] in (None, "block_to_break")
    assert (
        T.PARAMS["possession_change"]["block_shooter_r_m"] == 5.0
        and T.PARAMS["possession_change"]["block_dist_m"] == 1.5
    )


def test_loop1_t09_run_out_needs_the_ball_going_to_the_rim():
    check("run_out", "leak", "run_out", {"handler": "o3"})
    absent("run_out", "leak", handler="o1")
    absent("run_out", "shooterback")


def test_loop1_t11_overrides_reach_the_shared_anchors():
    sc = scene("break")
    assert T.detect_possession_change(sc)
    assert not T.detect_possession_change(sc, hold_r_m=0.05, hold_enter_r_m=0.05)
    assert T.detect_possession_change(sc)  # the defaults are still served from the memo
    assert T.detect_press_trap(scene("press"))
    assert not T.detect_press_trap(scene("press"), trap_m=0.5)
    base = [(e.actors, e.attrs["rank"]) for e in T.detect_trailer(sc)]
    assert base and not T.detect_trailer(sc, window_s=0.5)
    assert len(T.detect_upcourt_run(sc, enter_vy_mps=-9.0)) < len(T.detect_upcourt_run(sc))


def test_loop1_t12_pickup_onset_of_a_resting_ball():
    check("run_endline", "oobpick", "run_endline", {"thrower": "o5"}, 2.45, after_make=True)
    ev = check("throw_in", "oobpick", "throw_in", {"thrower": "o5", "receiver": "o1"}, 3.25)
    assert abs(ev.attrs["count_s"] - 0.8) <= TOL


def test_loop1_t13_wing_lane_confidence_uses_the_lane_line_edge():
    for o in ("o2", "o3"):
        ev = check("wing_lane_run", "break", "wing_lane_run", {"runner": o}, lane="sideline")
        up = match(run("upcourt_run", "break"), "upcourt_run", {"runner": o})[0]
        assert ev.conf >= 0.95 * up.conf and ev.attrs["p_sideline"] > 0.5


def test_loop1_t14_v_peak_shrinkage_and_identity_swap_gate():
    a, b, d, s = SCENARIOS["break"]
    sc = build(a, b, d, s)
    k = sc.k("o4")
    assert T._v_peak(sc, "o4") == pytest.approx(T.FAM["v_peak_default_mps"])
    k.extra.update(position="G", v_peak_games=[6.0, 6.2, 6.4, 6.6, 6.8])
    assert T._v_peak(sc, "o4") == pytest.approx((3 * 7.04 + 5 * 6.4) / 8)
    k.extra["v_peak"] = 5.0
    assert T._v_peak(sc, "o4") == 5.0
    # an identity swap (a 6 m jump inside one segment) acts as a segment edge for q_obj
    sc2 = build(a, b, d, s)
    k2 = sc2.k("o3")
    j = int(9.0 / DT)
    k2.x[j:] += 6.0
    assert T._swap_edge(sc2, "o3")[j] == 0 and T._qobj(sc2, ["o3"], j, j, j + 5) == 0.0
    assert T._qobj(sc2, ["o3"], j - 60, j - 60, j - 50) > 0.5
    assert T.FAM["vbar_short_s"] == T.VS and T.FAM["vbar_long_s"] == T.VL


def test_loop1_t15_min_durations_come_from_the_yaml(monkeypatch):
    a, b, d, s = SCENARIOS["break"]
    for item, det in (("rim_run", "rim_run"), ("push", "push"), ("leak_out", "leak_out"), ("run_out", "run_out")):
        name = "leak" if det in ("leak_out", "run_out") else "break"
        a, b, d, s = SCENARIOS[name]
        assert T.DETECTORS[det](build(a, b, d, s)), det
        monkeypatch.setitem(T.MIN_DUR, item, 30.0)
        assert not T.DETECTORS[det](build(a, b, d, s)), det
        monkeypatch.undo()


def test_loop1_t16_spec_and_code_agree():
    pc = T.PARAMS["possession_change"]
    assert pc["hold_merge_gap_s"] == 0.2 and pc["pass_max_flight_s"] == 3.0
    tw_made = check("throw_in", "made", "throw_in", {"thrower": "o5"}, 3.1)
    tw_blob = check("throw_in", "blob", "throw_in", {"thrower": "o5"}, 3.2)
    assert tw_made.attrs["after_make"] and not tw_blob.attrs["after_make"]
    bl = match(run("blob_alignment", "blob"), "blob_alignment", {"thrower": "o5"})[0]
    assert bl.conf <= tw_blob.conf + 1e-9
    ev = check("passed_up_break", "failed", "passed_up_break", {"gainer": "o1"}, condition="held_ball")
    assert ev.attrs["category"] == "failed"
    assert check("passed_up_break", "held", "passed_up_break", {"gainer": "o1"}).attrs["category"] == "declined"


def test_loop1_t17_ft_early_entry_candidate():
    # the definition on the near-truth copy: d1's 0.8 m step before the release is an early-entry candidate, o2's
    # crash after it is not; the release proxy is no longer late (the hold ends at the onset radius)
    ev = [e for e in run("ft_lane_entry", "ftearly", truth=True) if e.actors["player"] in ("d1", "o2")]
    assert {e.actors["player"]: e.attrs["early_entry_candidate"] for e in ev} == {"d1": True, "o2": False}
    assert abs(T._ft_releases(oracle("ftearly"))[0]["t_ft"] * DT - 2.0) <= 0.1
    assert abs(T._ft_releases(scene("ftearly"))[0]["t_ft"] * DT - 2.0) <= 0.15
    # sigma_move uses the reference MEAN: 3 sigma_move is below 3 sqrt(2) sigma_p
    k = scene("ftearly").k("d1")
    sp = float(np.nanmedian(T._sig_p(k)))
    n_eff = 0.7 / T.PARAMS["ft_lane_entry"]["corr_s"]
    assert np.sqrt(sp**2 / n_eff + sp**2) < np.sqrt(2) * sp
    check("ft_lane_entry", "ftearly", "ft_lane_entry", {"player": "d1"})
    check("ft_lane_entry", "ft", "ft_lane_entry", {"player": "o2", "shooter": "o1"}, early_entry_candidate=False)


def test_loop1_changes_are_recorded_in_the_yaml():
    ch = T.CFG["changes_loop1"]
    assert {c["id"] for c in ch} == {f"TRN-T{i:02d}" for i in range(1, 18)}
    for c in ch:
        assert {"id", "what", "why", "evidence"} <= set(c) and all(
            str(c[k]).strip() for k in ("what", "why", "evidence")
        )


# --------------------------------------------------------------------------------------
# Loop 2 (fix pass 2): the confirmer's still-failing items and pass-1 regressions. Scenarios marked [tester] are
# copied from the independent harness (scratchpad confirm_transition/scenarios.py); seeds and sigmas are the ones the
# confirmer reported failing. Rates over seeds compare against the pass-1 code measured on the same seeds.
# --------------------------------------------------------------------------------------
BREAKAWAY_ACTORS = {  # [tester] steal_breakaway: steal at D's top of key, solo layup at 7.0 s
    "d1": ("D", [(0, 1.0, 19.5), (1.8, 1.0, 19.5), (7.6, 0.8, 2.0)]),
    "d2": ("D", [(0, -5.5, 21.0), (1.8, -5.5, 21.0), (8.0, -4.5, 6.0)]),
    "d3": ("D", [(0, 4.0, 22.5), (2.0, 4.0, 22.5), (8.5, 3.5, 5.0)]),
    "d4": ("D", [(0, -2.0, 24.0), (2.2, -2.0, 24.0), (9.0, -1.5, 4.0)]),
    "d5": ("D", [(0, 3.0, 25.0), (2.5, 3.0, 25.0), (9.0, 2.5, 10.0)]),
    "o1": ("O", [(0, -1.8, 18.6), (1.0, -1.8, 18.6), (1.6, -2.5, 20.3), (1.8, -2.5, 20.3), (7.0, -0.5, 0.9)]),
    "o2": ("O", [(0, -5.0, 20.0), (2.0, -5.0, 20.0), (7.5, -6.9, 1.2)]),
    "o3": ("O", [(0, 3.5, 21.5), (2.4, 3.5, 21.5), (9.0, 4.5, 8.0)]),
    "o4": ("O", [(0, -1.5, 23.5), (2.5, -1.5, 23.5), (9.0, -1.0, 17.0)]),
    "o5": ("O", [(0, 2.5, 24.0), (9.0, 2.5, 24.0)]),
}
BREAKAWAY_BALL = [
    ("hold", 0, 1.4, "d1"),
    ("fly", 1.4, 1.6, "d1", "o1"),
    ("hold", 1.6, 7.0, "o1"),
    ("fly", 7.0, 7.3, "o1", RIM),
    ("fly", 7.3, 7.7, RIM, (0.3, -1.0)),
]
SLOBSTACK_ACTORS = {  # [tester] slob_stack: the thrower stands 0.28 m behind the sideline (x 7.9)
    "o5": ("O", [(0, 7.9, 8.0), (6, 7.9, 8.0)]),
    "o1": ("O", [(0, 4.9, 7.0), (2.3, 4.9, 7.0), (3.3, 5.6, 10.6), (6, 5.6, 10.6)]),
    "o2": ("O", [(0, 5.3, 7.6), (6, 5.3, 7.6)]),
    "o3": ("O", [(0, -3.0, 3.0), (6, -3.0, 3.0)]),
    "o4": ("O", [(0, -1.0, 8.5), (6, -1.0, 8.5)]),
    "d1": ("D", [(0, 4.2, 6.3), (6, 4.2, 6.3)]),
    "d2": ("D", [(0, 6.5, 7.6), (6, 6.5, 7.6)]),
    "d3": ("D", [(0, -2.2, 2.4), (6, -2.2, 2.4)]),
    "d4": ("D", [(0, -0.6, 7.6), (6, -0.6, 7.6)]),
    "d5": ("D", [(0, 0.5, 1.0), (6, 0.5, 1.0)]),
}
SLOBSTACK_BALL = [("hold", 0.4, 3.3, "o5"), ("fly", 3.3, 3.6, "o5", "o1"), ("hold", 3.6, 6.0, "o1")]
TRAP_ACTORS = {  # [tester] press_trap_break: o1 trapped by d1 + d2 from about 2.8 s, breaks it to o3 at 4.0 s
    "o5": ("O", [(0, -1.5, 27.6), (2.0, -1.5, 27.6), (3.0, -1.0, 25.6), (9, -1.0, 25.6)]),
    "o1": ("O", [(0, -6.0, 20.6), (1.0, -6.0, 20.6), (2.4, -5.0, 24.0), (9, -5.0, 24.0)]),
    "o3": ("O", [(0, 0.5, 12.0), (2.0, 0.5, 12.0), (3.9, -0.5, 19.3), (9, -0.5, 19.3)]),
    "o4": ("O", [(0, 6.0, 17.0), (1.0, 6.0, 17.0), (2.2, 6.0, 14.0), (9, 6.0, 14.0)]),
    "o2": ("O", [(0, 3.5, 20.0), (9, 3.5, 20.0)]),
    "d1": (
        "D",
        [(0, -2.4, 26.2), (2.2, -2.4, 26.2), (2.9, -4.2, 24.9), (4.1, -4.2, 24.9), (5.5, -1.8, 21.0), (9, -1.8, 21.0)],
    ),
    "d2": ("D", [(0, -5.5, 19.5), (2.3, -5.5, 19.5), (2.9, -5.9, 23.3), (9, -5.9, 23.3)]),
    "d3": ("D", [(0, 1.0, 22.0), (4.3, 1.0, 22.0), (5.8, 0.3, 20.4), (9, 0.3, 20.4)]),
    "d4": ("D", [(0, 4.0, 16.0), (9, 4.0, 16.0)]),
    "d5": ("D", [(0, 0.0, 6.0), (9, 0.0, 6.0)]),
}
TRAP_BALL = [
    ("hold", 0.3, 2.0, "o5"),
    ("fly", 2.0, 2.4, "o5", "o1"),
    ("hold", 2.4, 4.0, "o1"),
    ("fly", 4.0, 4.25, "o1", "o3"),
    ("hold", 4.25, 9.0, "o3"),
]


def _mirror(actors, ball):
    """x-mirrored copy of a scenario (the harness's _M variants)."""
    a = {k: (tm, [(t, -x, y) for t, x, y in wp]) for k, (tm, wp) in actors.items()}
    b = []
    for ev in ball:
        if ev[0] == "hold":
            b.append(ev)
        else:
            m = [p if isinstance(p, str) else (-p[0], p[1]) for p in ev[3:5]]
            b.append((ev[0], ev[1], ev[2], m[0], m[1]))
    return a, b


@functools.lru_cache(maxsize=None)
def _seeded(name, sigma, seed, mirror=False):
    a, b, d, _ = {
        "netcatch": SCENARIOS["netcatch"],
        "wallsink": SCENARIOS["wallsink"],
        "breakaway": (BREAKAWAY_ACTORS, BREAKAWAY_BALL, 9.0, None),
        "slobstack": (SLOBSTACK_ACTORS, SLOBSTACK_BALL, 6.0, None),
        "trap": (TRAP_ACTORS, TRAP_BALL, 9.0, None),
    }[name]
    if mirror:
        a, b = _mirror(a, b)
    return build(a, b, d, seed, sigma=sigma)


def test_loop2_t12_ball_still_closing_does_not_start_control():
    # the ball dropping from the rim to the inbounder (made_runendline_push, catch at 2.0 s): a merely MOVING ball
    # no longer starts control inside hold_r_m. Pass-1 code: 4 / 10 seeds within 0.3 s at sigma_p 0.2; now 7 / 10.
    ok = sum(
        any(abs(e.t0 * DT - 2.0) <= TOL for e in T.detect_run_endline(_seeded("netcatch", 0.2, sd)))
        for sd in range(101, 111)
    )
    assert ok >= 7, ok
    # the onset rule itself: inside hold_r_m but outside hold_enter_r_m, a ball still closing (or not moving with
    # the player) never starts a hold
    sc = _seeded("netcatch", 0.2, 101)
    h = T._holders(sc)
    k, b = sc.k("o5"), sc.ball
    t = next(i for i in range(sc.n) if h[i] == "o5")
    d = math.hypot(k.x[t] - b.x[t], k.y[t] - b.y[t])
    v = math.hypot(k.vx[t] - b.vx[t], k.vy[t] - b.vy[t])
    pc = T.PARAMS["possession_change"]
    assert d <= pc["hold_enter_r_m"] or v <= pc["hold_core_v_mps"]


def test_loop2_t02_switch_is_backdated_to_when_the_receiver_became_nearer():
    # wall_and_sink: the steal is received 0.63 m from the passer; pass 1 started o1's hold at 1.30 s (switch margin
    # reached late), the truth is 0.95 s
    sc = _seeded("wallsink", 0.2, 101)
    runs = [(o, a * DT) for o, a, _ in T._hold_runs(sc)]
    assert ("o1" in [o for o, _ in runs]) and next(a for o, a in runs if o == "o1") <= 1.1, runs
    ok = sum(
        any(
            e.actors["gainer"] == "o1" and abs(e.t0 * DT - 0.95) <= TOL
            for e in T.detect_possession_change(_seeded("wallsink", 0.3, sd, True))
        )
        for sd in range(101, 111)
    )
    assert ok >= 9, ok  # pass-1 code: 8 / 10


def test_loop2_t04_layup_release_at_the_rim_is_a_shot():
    # steal_breakaway: the handler carries the ball to 0.9 m from the rim and lays it in; the ball then moves away
    # from the rim, which the pass-1 closing test rejected (no shot proxy, no primary_break)
    for sigma, seed in ((0.2, 104), (0.3, 104), (0.5, 108)):
        sc = _seeded("breakaway", sigma, seed)
        shots = [s for s in T._shots(sc) if s["shooter"] == "o1"]
        # release between the scripted release (7.0 s) and the ball reaching the rim (7.3 s)
        assert shots and 6.8 <= shots[0]["t_rel"] * DT <= 7.35, (sigma, seed, shots)
        ev = [e for e in T.detect_primary_break(sc) if e.actors.get("shooter") == "o1" and e.conf >= 0.5]
        assert ev, (sigma, seed)
    # a rebound secured at the rim and moved OUT is still not a shot (the carried-in condition)
    assert not [s for s in T._shots(scene("rimreb")) if s["team"] == "O"]


def test_loop2_t01_sideline_thrower_just_out_of_bounds_at_high_noise():
    # slob_stack mirrored, sigma_p 0.5: the thrower 0.28 m out read in bounds on noise, so t_disposal jumped to
    # 2.1-2.4 s and slob_alignment lost its t0 (pass 1); the sideline test is now noise-aware
    for seed in (106, 108):
        sc = _seeded("slobstack", 0.5, seed, True)
        tw = [e for e in T.detect_throw_in(sc) if e.actors["thrower"] == "o5"]
        assert tw and abs(tw[0].attrs["t_disposal"] * DT - 0.4) <= TOL, seed
        al = [e for e in T.detect_slob_alignment(sc) if abs(e.t0 * DT - 0.4) <= TOL]
        assert al, seed
    # the end lines keep the plain tolerance: the inbounder catching under the net is counted from the step out
    tw = check("throw_in", "netcatch", "throw_in", {"thrower": "o5", "receiver": "o1"}, 3.0)
    assert tw.attrs["t_disposal"] * DT >= 1.5


def test_loop2_t10_trap_entry_on_window_medians_with_a_noise_margin():
    p = T.PARAMS["press_trap"]
    assert p["entry_window_s"] == 0.27 and p["entry_sigma_k"] == 2.0  # loop 3: 1.0 -> 2.0 (test_loop3_t10)
    found = 0
    for seed in range(101, 111):
        for mir in (False, True):
            ev = [
                e
                for e in T.detect_press_trap(_seeded("trap", 0.3, seed, mir))
                if e.actors["handler"] == "o1" and e.conf >= 0.5 and abs(e.t0 * DT - 2.8) <= 0.4
            ]
            found += bool(ev)
    assert found >= 17, found  # pass-1 code: 15 / 20
    # the noise margin shrinks with the noise tier: below 0.15 m at sigma_p 0.1 (k 2.0 since loop 3)
    sc = _seeded("trap", 0.1, 101)
    k1, k2 = sc.k("o1"), sc.k("d1")
    assert float(np.nanmedian(mv.sigma_dist(k1, k2))) * p["entry_sigma_k"] < 0.15
    # negatives: no trap in the second press scenario or the half-court scenario
    absent("press_trap", "pressb")
    absent("press_trap", "half")


def test_loop2_changes_are_recorded_in_the_yaml():
    ch = T.CFG["changes_loop2"]
    ids = {c["id"] for c in ch}
    assert {"TRN-T01", "TRN-T02", "TRN-T04", "TRN-T10", "TRN-T12"} <= ids
    for c in ch:
        assert {"id", "what", "why", "evidence"} <= set(c) and all(
            str(c[k]).strip() for k in ("what", "why", "evidence")
        )


# --------------------------------------------------------------------------------------
# Loop 3 (fix pass 3): catch onset, switch backdate decision, oob z override, trap margin. Scenario copies of the
# harness's pitch_back and dreb_hitahead (the harness seeds and noise are reproduced by build()).
# --------------------------------------------------------------------------------------
_PB_D = {
    "d1": ("D", [(0, 2.0, 18.5), (1.2, 2.0, 18.5), (5.5, 2.5, 7.0), (11.0, 2.5, 7.0)]),
    "d2": ("D", [(0, -3.0, 21.0), (1.0, -3.0, 21.0), (2.0, -1.5, 24.0), (2.6, -1.5, 24.0), (8.0, -3.5, 3.0), (11, -3.5, 3.0)]),
    "d3": ("D", [(0, 5.0, 15.0), (1.0, 5.0, 15.0), (5.0, 5.5, 2.0), (11.0, 5.5, 2.0)]),
    "d4": ("D", [(0, -5.5, 16.0), (1.0, -5.5, 16.0), (5.0, -5.5, 2.0), (11.0, -5.5, 2.0)]),
    "d5": ("D", [(0, 2.0, 23.0), (2.5, 2.0, 23.0), (8.0, 0.5, 1.5), (11.0, 0.5, 1.5)]),
}
PITCHBACK_ACTORS = {  # [harness] pitch_back: trailer o5 catches the pitch-back on the run at 7.6 s
    **_PB_D,
    "o1": ("O", [(0, -3.0, 17.0), (1.4, -3.0, 17.0), (2.6, -5.5, 20.8), (3.1, -5.5, 20.8), (6.2, -5.0, 6.5), (10, -5.0, 6.5)]),
    "o5": ("O", [(0, 1.2, 22.8), (1.5, 1.2, 22.8), (2.0, 1.0, 23.4), (2.6, 1.0, 23.4), (7.0, -0.4, 7.8), (10, -0.4, 7.8)]),
    "o2": ("O", [(0, 5.0, 19.0), (2.2, 5.0, 19.0), (6.8, 6.9, 1.2), (10, 6.9, 1.2)]),
    "o3": ("O", [(0, -5.5, 15.0), (2.3, -5.5, 15.0), (6.2, -6.9, 1.2), (10, -6.9, 1.2)]),
    "o4": ("O", [(0, 0.5, 21.5), (2.2, 0.5, 21.5), (6.5, 1.5, 1.2), (10, 1.5, 1.2)]),
}
PITCHBACK_BALL = [
    ("hold", 0, 1.0, "d1"),
    ("fly", 1.0, 1.5, "d1", FAR),
    ("fly", 1.5, 2.0, FAR, "o5"),
    ("hold", 2.0, 2.6, "o5"),
    ("fly", 2.6, 3.0, "o5", "o1"),
    ("hold", 3.0, 7.2, "o1"),
    ("fly", 7.2, 7.6, "o1", "o5"),
    ("hold", 7.6, 10.0, "o5"),
]
HITAHEAD_ACTORS = {  # [harness] dreb_hitahead: o1 hits the leaker o3 ahead (caught on the run at 4.3 s); the actor
    # order is the harness's (sim draws the noise per actor in order)
    **{k: _DHA[k] for k in ("d2", "d1", "d3", "d4", "d5")},
    "o5": ("O", [(0, -1.2, 22.5), (1.2, -1.2, 22.5), (1.9, -1.0, 23.3), (2.6, -1.0, 23.3), (7.0, -0.5, 11.0)]),
    "o1": _DHA["o1"],
    "o3": ("O", [(0, 5.0, 18.5), (0.8, 5.0, 18.5), (4.4, 2.0, 5.0), (5.0, 1.0, 1.5), (7.0, 1.0, 1.5)]),
    "o2": _DHA["o2"],
    "o4": _DHA["o4"],
}
HITAHEAD_BALL = [
    ("hold", 0, 1.0, "d2"),
    ("fly", 1.0, 1.5, "d2", FAR),
    ("fly", 1.5, 1.9, FAR, "o5"),
    ("hold", 1.9, 2.5, "o5"),
    ("fly", 2.5, 2.9, "o5", "o1"),
    ("hold", 2.9, 3.6, "o1"),
    ("fly", 3.6, 4.3, "o1", "o3"),
    ("hold", 4.3, 4.9, "o3"),
    ("fly", 4.9, 5.2, "o3", RIM),
    ("fly", 5.2, 5.6, RIM, (0.0, -1.0)),
]


@functools.lru_cache(maxsize=None)
def _seeded3(name, sigma, seed, mirror=False):
    a, b, d = {
        "pitchback": (PITCHBACK_ACTORS, PITCHBACK_BALL, 10.0),
        "hitahead": (HITAHEAD_ACTORS, HITAHEAD_BALL, 7.0),
        # harness actor order (dreb_hitahead's, with o5 / o3 replaced in place)
        "rimreb": ({**HITAHEAD_ACTORS, "o5": RIMREB_ACTORS["o5"], "o3": RIMREB_ACTORS["o3"]}, RIMREB_BALL, 7.0),
    }[name]
    if mirror:
        a, b = _mirror(a, b)
    return build(a, b, d, seed, sigma=sigma)


def _first_hold(sc, oid, after_s=0.0):
    return next((a * DT for o, a, _ in T._hold_runs(sc) if o == oid and a * DT >= after_s), None)


def test_loop3_t12_fresh_hold_is_backdated_to_the_ball_arrival():
    # pass 2: a pass caught on the run started control only once the smoothed ball settled (0.35-0.5 s late)
    sc = _seeded3("pitchback", 0.5, 108)
    t = _first_hold(sc, "o5", 5.0)
    assert t is not None and abs(t - 7.6) <= 0.15, t  # pass-2 code: 8.01 s
    assert [e for e in T.detect_trailer_pitch_back(sc) if e.conf >= 0.5 and abs(e.t0 * DT - 7.6) <= TOL]
    t = _first_hold(_seeded3("hitahead", 0.2, 101), "o3")
    assert t is not None and abs(t - 4.3) <= 0.15, t  # pass-2 code: 4.74 s
    # rim guard: the ball at the rim is at rim height, so its XY arrival next to the rebounder is not a catch
    # (without the guard rim_rebound_outlet_M lost possession_change and outlet_pass at seeds 205 / 207)
    for seed in (205, 207):
        ev = [
            e
            for e in T.detect_possession_change(_seeded3("rimreb", 0.5, seed, True))
            if e.actors["gainer"] == "o5" and e.conf >= 0.5
        ]
        assert ev and abs(ev[0].t0 * DT - 1.85) <= TOL, (seed, [e.t0 * DT for e in ev])
    pc = T.PARAMS["possession_change"]
    assert pc["catch_backdate_s"] == 0.4 and pc["catch_backdate_k_s_per_m"] == 2.0 and pc["catch_chain_sigma_k"] == 1.0


def test_loop3_t12_known_limit_ball_smoother_ringing_is_pinned():
    # Known limitation (changes_loop3 TRN-T12-limit): when the smoothed ball rings more than hold_r_m away from a
    # catcher on the run, no XY rule can place the catch. Pinned so a later change to it is deliberate.
    sc = _seeded3("hitahead", 0.3, 205, True)
    assert _first_hold(sc, "o3") is None  # the 0.6 s scripted hold is missed entirely
    k, b = sc.k("o3"), sc.ball
    i0, i1 = int(round(4.3 / DT)), int(round(4.6 / DT))
    assert float(np.nanmin(np.hypot(k.x[i0:i1] - b.x[i0:i1], k.y[i0:i1] - b.y[i0:i1]))) > 1.2
    t = _first_hold(_seeded3("hitahead", 0.2, 110), "o3")  # arrival 1.08 m away: onset 0.54 s late
    assert t is not None and 0.4 <= t - 4.3 <= 0.7, t


def test_loop3_t02_switch_backdate_stays_uncapped():
    # the confirmer's cap (0.3 s, or a stop at the holder's core frames) lost wall_and_sink / spread_back_nearmiss
    # possession changes at sigma_p 0.3 / 0.5 on both seed sets; these runs pin the uncapped backdate
    for sigma, seed in ((0.3, 101), (0.5, 106)):
        for mir in (False, True):
            ev = [
                e
                for e in T.detect_possession_change(_seeded("wallsink", sigma, seed, mir))
                if e.actors["gainer"] == "o1" and abs(e.t0 * DT - 0.95) <= TOL
            ]
            assert ev, (sigma, seed, mir)


def test_loop3_t11_oob_side_noise_z_override_reaches_the_sideline_test():
    sc = _seeded("slobstack", 0.5, 106, True)
    base = [(round(e.conf, 3), e.attrs["t_disposal"]) for e in T.detect_throw_in(sc)]
    over = [(round(e.conf, 3), e.attrs["t_disposal"]) for e in T.detect_throw_in(sc, oob_side_noise_z=0.0)]
    assert base and over and base != over, (base, over)  # pass-2 code: identical (the kwarg was ignored)
    assert [(round(e.conf, 3), e.attrs["t_disposal"]) for e in T.detect_throw_in(sc)] == base  # memo unchanged


def test_loop3_t10_trap_margin_two_sigma():
    found = 0
    for seed in range(101, 111):
        for mir in (False, True):
            ev = [
                e
                for e in T.detect_press_trap(_seeded("trap", 0.5, seed, mir))
                if e.actors["handler"] == "o1" and e.conf >= 0.5 and abs(e.t0 * DT - 2.8) <= 0.4
            ]
            found += bool(ev)
    assert found >= 12, found  # entry_sigma_k 1.0: 11 / 20
    absent("press_trap", "pressb")
    absent("press_trap", "half")


def test_loop3_changes_are_recorded_in_the_yaml():
    ch = T.CFG["changes_loop3"]
    ids = {c["id"] for c in ch}
    assert {"TRN-T12-catch", "TRN-T02-cap", "TRN-T11-oobz", "TRN-T10-k2", "TRN-T12-limit"} <= ids
    for c in ch:
        assert {"id", "what", "why", "evidence"} <= set(c) and all(
            str(c[k]).strip() for k in ("what", "why", "evidence")
        )


# --------------------------------------------------------------------------------------
# Loop 4: synthetic reproductions of the failure modes found on real tracking (no real data here)
# --------------------------------------------------------------------------------------
FY = FAR[1]
L4_FILL = {  # bystanders away from the action
    "o2": ("O", [(0, -6.0, 15.0), (8, -6.0, 15.0)]),
    "o3": ("O", [(0, 6.0, 15.0), (8, 6.0, 15.0)]),
    "o5": ("O", [(0, 0.0, 14.0), (8, 0.0, 14.0)]),
    "d3": ("D", [(0, -5.0, 18.0), (8, -5.0, 18.0)]),
    "d4": ("D", [(0, 5.0, 18.0), (8, 5.0, 18.0)]),
    "d5": ("D", [(0, 0.0, 16.0), (8, 0.0, 16.0)]),
}


def _l4_double(y0):
    """o1 holds 4.5 s at (1.5, y0) while d1 and d2 close to about 1.1 m of him (pair 1.9 m) from 1.6 s."""
    a = {
        **L4_FILL,
        "o1": ("O", [(0, 1.5, y0), (6, 1.5, y0)]),
        "o4": ("O", [(0, -4.0, y0 + 3), (6, -4.0, y0 + 3)]),
        "d1": ("D", [(0, 3.0, y0 + 1.5), (1.0, 3.0, y0 + 1.5), (1.6, 2.5, y0 + 0.6), (6, 2.5, y0 + 0.6)]),
        "d2": ("D", [(0, -0.5, y0 + 2.0), (1.0, -0.5, y0 + 2.0), (1.6, 0.6, y0 + 0.7), (6, 0.6, y0 + 0.7)]),
    }
    return a, [("hold", 0.0, 4.5, "o1"), ("fly", 4.5, 4.8, "o1", "o4"), ("hold", 4.8, 6.0, "o4")]


def test_loop4_trap_only_in_press_territory():
    # TRN-L4-trapzone: on real tracks 153 of 199 'press traps' were two defenders around a handler in the paint and
    # 15 a crowd around a rebounder at the far rim; the same double team is a press trap only in the backcourt
    for y0, want in ((2.0, False), (23.5, False), (20.0, True)):
        a, b = _l4_double(y0)
        got = [
            bool([e for e in T.detect_press_trap(build(a, b, 6.0, s, sigma=0.2)) if e.conf >= 0.5])
            for s in range(101, 106)
        ]
        assert all(g == want for g in got), (y0, got)


def test_loop4_live_ball_backcourt_crowd_is_not_a_press():
    # TRN-L4-press: after a live-ball steal three defenders stand within 1-2 m of the new handler in his backcourt;
    # that is transition defense, not a press (press_active ran at 54 per 48 min on real tracks)
    a = {
        **BREAKAWAY_ACTORS,
        "d1": ("D", [(0, 1.0, 19.5), (6, 1.0, 19.5)]),
        "d2": ("D", [(0, -1.0, 21.5), (6, -1.0, 21.5)]),
        "d3": ("D", [(0, 2.5, 21.0), (6, 2.5, 21.0)]),
        "o1": ("O", [(0, -0.6, 19.0), (6, -0.6, 19.0)]),
    }
    b = [("hold", 0, 1.4, "d1"), ("fly", 1.4, 1.6, "d1", "o1"), ("hold", 1.6, 6.0, "o1")]
    for s in range(101, 106):
        sc = build(a, b, 6.0, s, sigma=0.2)
        assert [e for e in T.detect_possession_change(sc) if e.actors["gainer"] == "o1"]
        assert T.detect_press_active(sc) == [], s
    check("press_active", "press", "press_active", {})  # the inbound press is still found


def _l4_scrum(next_id):
    """d1 shoots at the far rim; the ball bounces over o1 and o4 standing under it (XY 'holds' at rim height), then
    next_id takes it: d2 (shooting team, offensive rebound: no change) or o5 (defensive rebound: a change)."""
    a = {
        **L4_FILL,
        "d1": ("D", [(0, 2.0, FY - 5.0), (8, 2.0, FY - 5.0)]),
        "d2": ("D", [(0, -1.2, FY - 0.5), (8, -1.2, FY - 0.5)]),
        "o1": ("O", [(0, 0.5, FY - 1.0), (8, 0.5, FY - 1.0)]),
        "o4": ("O", [(0, 0.4, FY - 0.5), (8, 0.4, FY - 0.5)]),
        "o5": ("O", [(0, 1.5, FY - 2.5), (8, 1.5, FY - 2.5)]),
    }
    b = [
        ("hold", 0, 1.0, "d1"),
        ("fly", 1.0, 1.5, "d1", FAR),
        ("fly", 1.5, 1.6, FAR, "o1"),
        ("hold", 1.6, 1.9, "o1"),
        ("fly", 1.9, 2.0, "o1", "o4"),
        ("hold", 2.0, 2.3, "o4"),
        ("fly", 2.3, 2.45, "o4", next_id),
        ("hold", 2.45, 5.0, next_id),
    ]
    return a, b


def test_loop4_rim_scrum_is_not_a_change():
    # TRN-L4-rimscrum: missed shot -> defenders under the rim 'hold' the ball at rim height -> the shooting team gets
    # it back (PBP: miss + offensive rebound). With the loop-3 radius (rim_scrum_r_m = rim_touch_r_m) it is a change.
    new = old = 0
    for sigma in (0.2, 0.3):
        for s in range(101, 111):
            sc = build(*_l4_scrum("d2"), 5.0, s, sigma=sigma)
            new += len(T.detect_possession_change(sc))
            old += len(T.detect_possession_change(sc, rim_scrum_r_m=0.6))
    assert new == 0 and old >= 2, (new, old)
    # control: a defensive rebound (the ball goes on to the rebounder's teammate) is still a change
    for s in range(101, 106):
        assert T.detect_possession_change(build(*_l4_scrum("o5"), 5.0, s, sigma=0.2)), s


def test_loop4_contact_misread_is_a_deflection():
    # TRN-L4-sandwich: a defender beside the dribbler takes the XY hold for 1.2 s and gives it straight back
    a = {**BREAKAWAY_ACTORS, "d1": ("D", [(0, 1.0, 15.0), (6, 1.0, 15.0)]), "o1": ("O", [(0, 1.6, 15.2), (6, 1.6, 15.2)])}
    b = [("hold", 0, 2.0, "d1"), ("hold", 2.03, 3.23, "o1"), ("hold", 3.27, 6.0, "d1")]
    for s in range(101, 106):
        sc = build(a, b, 6.0, s, sigma=0.2)
        assert T.detect_possession_change(sc) == [], s
        assert T.detect_possession_change(sc, deflect_max_s=1.0), s  # the loop-4 first-run window kept it
    assert T.PARAMS["possession_change"]["deflect_max_s"] == 1.5


def test_loop4_layup_hold_into_the_rim_leaves_a_shot_gap():
    # TRN-L4-rimfree: the shooter's XY hold runs into the far-rim footprint and the defender under the basket takes
    # the ball on the next frame (no unheld gap): a shot all the same
    a = {
        **BREAKAWAY_ACTORS,
        "d1": ("D", [(0, 3.0, FY - 6.0), (1.0, 3.0, FY - 6.0), (2.1, 0.15, FY - 0.25), (6, 0.15, FY - 0.25)]),
        "o1": ("O", [(0, -0.6, FY - 0.5), (6, -0.6, FY - 0.5)]),
        "o2": ("O", [(0, -3.0, 14.0), (6, -3.0, 14.0)]),
    }
    b = [("hold", 0, 2.1, "d1"), ("hold", 2.13, 2.6, "o1"), ("fly", 2.6, 3.0, "o1", "o2"), ("hold", 3.0, 6.0, "o2")]
    off = {**T.PARAMS["possession_change"], "hold_rim_free": False}
    new = old = 0
    for s in range(101, 111):
        sc = build(a, b, 6.0, s, sigma=0.2)
        new += any(x["shooter"] == "d1" and x["rim"] == "far" and abs(x["t_rel"] * DT - 1.9) <= TOL for x in T._shots(sc))
        old += any(x["shooter"] == "d1" for x in T._shots(sc, off))
    assert new >= 8 and old <= 2, (new, old)


def test_loop4_same_attempt_tip_is_flagged():
    # TRN-L4-tipdup: the ball rolls on the rim, the shooter's teammate holds it 0.6 s 1.2 m from the rim and puts it
    # back up: one attempt for the per-shot reads (crash / safety), two releases for the possession logic
    a = {
        **BREAKAWAY_ACTORS,
        "d1": ("D", [(0, 2.0, FY - 5.0), (8, 2.0, FY - 5.0)]),
        "d2": ("D", [(0, 0.9, FY - 0.8), (8, 0.9, FY - 0.8)]),
        "o1": ("O", [(0, -1.4, FY - 1.0), (8, -1.4, FY - 1.0)]),
        "o2": ("O", [(0, -3.0, 14.0), (8, -3.0, 14.0)]),
    }
    b = [
        ("hold", 0, 1.0, "d1"),
        ("fly", 1.0, 1.5, "d1", FAR),
        ("fly", 1.5, 1.8, FAR, (0.3, FY - 0.2)),
        ("fly", 1.8, 1.9, (0.3, FY - 0.2), "d2"),
        ("hold", 1.9, 2.5, "d2"),
        ("fly", 2.5, 2.6, "d2", FAR),
        ("fly", 2.6, 2.8, FAR, "o1"),
        ("hold", 2.8, 3.1, "o1"),
        ("fly", 3.1, 3.5, "o1", "o2"),
        ("hold", 3.5, 6.0, "o2"),
    ]
    for s in range(101, 106):
        sc = build(a, b, 6.0, s, sigma=0.2)
        sh = [(x["shooter"], x["same_attempt"]) for x in T._shots(sc)]
        assert sh == [("d1", False), ("d2", True)], (s, sh)
        assert len(T._far_shots(sc)) == 1
        off = {**T.PARAMS["possession_change"], "shot_merge_s": 0.0}
        assert not any(x["same_attempt"] for x in T._shots(sc, off))


def test_loop4_loose_ball_pickup_is_not_backdated_to_the_fly_by():
    # confirm-3 NEW-T12-catch-loose-ball-early (adversarial adv_loose_ball_chase): an errant pass rolls past o1 and
    # comes to rest 2.6 m away; o1 runs it down and picks it up at 2.45 s
    a = {
        **BREAKAWAY_ACTORS,
        "o1": ("O", [(0, 3.0, 19.5), (1.8, 3.0, 19.5), (2.6, 4.6, 21.6), (2.7, 4.6, 21.6), (7.0, -0.5, 0.9), (9, -0.5, 0.9)]),
        "o3": ("O", [(0, -3.5, 21.5), (2.4, -3.5, 21.5), (9.0, -4.5, 8.0)]),
        "d3": ("D", [(0, 5.5, 23.8), (2.0, 5.5, 23.8), (8.5, 3.5, 5.0)]),
    }
    b = [
        ("hold", 0, 1.4, "d1"),
        ("fly", 1.4, 2.2, "d1", (4.6, 21.6)),
        ("fly", 2.2, 2.6, (4.6, 21.6), (4.6, 21.6)),
        ("hold", 2.6, 7.0, "o1"),
        ("fly", 7.0, 7.3, "o1", RIM),
    ]
    new = old = 0
    for s in range(101, 111):
        sc = build(a, b, 9.0, s, sigma=0.5)
        for kw, inc in (({}, 1), ({"catch_recede_sigma_k": 99.0}, 0)):
            ev = [e for e in T.detect_possession_change(sc, **kw) if e.actors["gainer"] == "o1"]
            ok = bool(ev) and abs(ev[0].t0 * DT - 2.45) <= TOL
            new, old = (new + ok, old) if inc else (new, old + ok)
    assert new >= 4 and old <= 2, (new, old)


def test_loop4_changes_are_recorded_in_the_yaml():
    ch = T.CFG["changes_loop4"]
    ids = {c["id"] for c in ch}
    assert {
        "TRN-L4-rimtouch",
        "TRN-L4-sandwich",
        "TRN-L4-rimscrum",
        "TRN-L4-press",
        "TRN-L4-trapzone",
        "TRN-L4-rimfree",
        "TRN-L4-tipdup",
        "NEW-T12-catch-rimguard-bypass",
        "NEW-T10-k2-conf-dilution",
        "NEW-T12-catch-loose-ball-early",
    } <= ids
    for c in ch:
        assert {"id", "what", "why", "evidence"} <= set(c) and all(
            str(c[k]).strip() for k in ("what", "why", "evidence")
        )


def test_loop4_rim_catch_rebound_backdate_stops_at_the_rim():
    # confirm-3 NEW-T12-catch-rimguard-bypass (adversarial adv_rim_catch_rebound): the rebounder o5 stands 0.7 m
    # from the far rim under the shot path; the catch backdate must not run into the shot still in flight
    a = {
        **HITAHEAD_ACTORS,
        "o5": ("O", [(0, -0.5, 23.5), (1.2, -0.5, 23.5), (1.65, 0.5, 24.9), (2.8, 0.5, 24.9), (7.0, 0.0, 14.0)]),
    }
    b = [("hold", 0, 1.0, "d2"), ("fly", 1.0, 1.5, "d2", FAR), ("fly", 1.5, 1.7, FAR, "o5"), ("hold", 1.7, 2.8, "o5"),
         ("fly", 2.8, 3.2, "o5", "o1"), ("hold", 3.2, 7.0, "o1")]
    dreb = outlet = 0
    for s in range(101, 111):
        sc = build(a, b, 7.0, s, sigma=0.5)
        ev = [e for e in T.detect_possession_change(sc) if e.actors["gainer"] == "o5"]
        dreb += bool(ev) and ev[0].attrs["start_type"] == "dreb"
        outlet += any(abs(e.t0 * DT - 2.8) <= TOL for e in T.detect_outlet_pass(sc))
    assert dreb >= 9 and outlet >= 9, (dreb, outlet)
