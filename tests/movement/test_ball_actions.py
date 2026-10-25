"""Tests for the ball-actions movement family (config/movement_grammar/ball_actions.yaml,
tools/specgen/movement/detectors/ball_actions.py), validation tier V0 (synthetic, sim.scenario).

Every detector gets at least one positive and one negative scenario at sigma_p = 0.3 m with fixed seeds.
Positives check kind, actors, t0 within +-0.3 s of the scenario truth and conf in the expected range;
negatives check that the item does not fire. Items marked needs_data in the YAML must return [] even on
scenarios whose XY motion looks like the action (they are never guessed from XY).

Scenario conventions: 'rim' and 'spot*' actors are pseudo actors (ball targets only) and are dropped
before build_scene; truth t0 values are the scenario's own event times (flight start = release, flight
end = catch, waypoint start = movement onset).
"""
import sys
from functools import lru_cache
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "movement"))
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "movement" / "detectors"))
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "named_spots"))

import ball_actions as BA  # noqa: E402
import sim  # noqa: E402
from mvlib import DT, build_scene  # noqa: E402

SIGMA = 0.3
TOL_S = 0.3
SEEDS = (1, 2)


# --------------------------------------------------------------------------------------
# Scenario library (attacked-rim frame, metres; times in seconds)
# --------------------------------------------------------------------------------------
def _still(x, y, dur=6.0):
    return [(0.0, x, y), (dur, x, y)]


RIM = {"team": "X", "wp": _still(0.0, 0.0)}

SCENARIOS = {
    # A (right wing) passes cross-court to B (left wing) over C at the top; B catches and shoots a three.
    "pass_cs": dict(dur=4.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(7.0, 3.0)},
        "B": {"team": "O", "wp": _still(-6.0, 4.0)},
        "C": {"team": "O", "wp": _still(0.0, 7.5)},
        "D": {"team": "D", "wp": _still(6.2, 2.5)},
        "E": {"team": "D", "wp": _still(-4.5, 3.5)},
        "rim": RIM},
        "ball": {"held": [(0.0, 1.5, "A"), (2.1, 2.9, "B")], "flights": [(1.5, 2.1, "A", "B"), (2.9, 3.6, "B", "rim")]}}),
    # A holds still at the wing for the whole clip; defender 1.0 m rim-side.
    "hold": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 4.0)},
        "B": {"team": "O", "wp": _still(-6.0, 4.0)},
        "D": {"team": "D", "wp": _still(5.2, 3.4)}},
        "ball": {"held": [(0.0, 4.0, "A")]}}),
    # No ball at all.
    "no_ball": dict(dur=3.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 4.0)},
        "D": {"team": "D", "wp": _still(5.2, 3.4)}}}),
    # Ball resting far from everyone (no control).
    "ball_alone": dict(dur=3.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 4.0)},
        "D": {"team": "D", "wp": _still(5.2, 3.4)},
        "spot": {"team": "X", "wp": _still(-3.0, 9.0)}},
        "ball": {"held": [(0.0, 3.0, "spot")]}}),
    # A catches at the right wing, baseline drive (1.0-2.6 s, 5.4 m), kick-out to the right corner at
    # 2.8 s. D (on-ball) is beaten; H helps from the weak side; F guards C in the corner.
    "drive_kick": dict(dur=4.8, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, 6.0, 5.0), (1.0, 6.0, 5.0), (2.6, 2.4, 1.0), (4.8, 2.4, 1.0)]},
        "B": {"team": "O", "wp": _still(0.0, 7.8)},
        "C": {"team": "O", "wp": _still(7.0, 0.3)},
        "D": {"team": "D", "wp": [(0.0, 5.3, 4.4), (1.0, 5.3, 4.4), (2.6, 4.6, 3.4), (4.8, 4.6, 3.4)]},
        "H": {"team": "D", "wp": [(0.0, -1.0, 2.0), (1.4, -1.0, 2.0), (2.4, 1.5, 1.6), (4.8, 1.5, 1.6)]},
        "F": {"team": "D", "wp": _still(6.3, 1.0)}},
        "ball": {"held": [(0.0, 0.4, "B"), (0.8, 2.8, "A"), (3.3, 4.8, "C")],
                 "flights": [(0.4, 0.8, "B", "A"), (2.8, 3.3, "A", "C")]}}),
    # A catches on the left wing, middle drive (1.4-3.0 s) into the lane, stops and pulls up at 3.4 s.
    "drive_pullup": dict(dur=4.6, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, -6.0, 5.0), (1.4, -6.0, 5.0), (3.0, -1.2, 3.4), (4.6, -1.2, 3.4)]},
        "B": {"team": "O", "wp": _still(-1.0, 8.0)},
        "D": {"team": "D", "wp": [(0.0, -5.2, 4.4), (1.4, -5.2, 4.4), (3.0, -2.4, 3.9), (4.6, -2.4, 3.9)]},
        "rim": RIM},
        "ball": {"held": [(0.0, 0.5, "B"), (0.9, 3.4, "A")],
                 "flights": [(0.5, 0.9, "B", "A"), (3.4, 4.0, "A", "rim")]}}),
    # A walks the ball 3.1 m toward the rim in 4.6 s (peak 1.26 m/s): gain without attack speed, no drive.
    "walk_in": dict(dur=5.0, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, 6.0, 5.5), (0.2, 6.0, 5.5), (4.8, 3.72, 3.41), (5.0, 3.72, 3.41)]},
        "B": {"team": "O", "wp": _still(-6.0, 4.0)},
        "D": {"team": "D", "wp": [(0.0, 5.2, 4.8), (0.2, 5.2, 4.8), (4.8, 3.0, 2.8), (5.0, 3.0, 2.8)]}},
        "ball": {"held": [(0.0, 5.0, "A")]}}),
    # P arrives in the right low post at 0.7 s and seals (0.7-2.0 s) with DP behind him; W enters at 2.0 s; P posts up and
    # kicks out to W at the wing at 4.6 s.
    "post": dict(dur=5.6, spec={"actors": {
        "W": {"team": "O", "wp": _still(6.0, 4.0)},
        "P": {"team": "O", "wp": [(0.0, 3.2, 2.2), (0.7, 2.2, 1.0), (5.6, 2.2, 1.0)]},
        "G": {"team": "O", "wp": _still(-6.5, 5.0)},
        "DP": {"team": "D", "wp": [(0.0, 2.6, 1.4), (0.7, 1.57, 0.50), (5.6, 1.57, 0.50)]},
        "DW": {"team": "D", "wp": _still(5.0, 3.6)}},
        "ball": {"held": [(0.0, 2.0, "W"), (2.4, 4.6, "P"), (5.0, 5.6, "W")],
                 "flights": [(2.0, 2.4, "W", "P"), (4.6, 5.0, "P", "W")]}}),
    # Wing catch with the defender in contact rim-side and the catcher still (not a post-up).
    "wing_catch": dict(dur=4.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(0.0, 8.0)},
        "B": {"team": "O", "wp": _still(5.6, 4.2)},
        "D": {"team": "D", "wp": _still(4.9, 3.6)}},
        "ball": {"held": [(0.0, 1.0, "A"), (1.5, 4.5, "B")], "flights": [(1.0, 1.5, "A", "B")]}}),
    # B (corner) passes to A at the top at 0.6 s; A isolates from 1.0 s with D 1.0 m away, teammates far, and
    # attacks: drive at the rim 3.4-4.6 s (changes_loop1 BA-T5: an isolation must end in an attack).
    "iso": dict(dur=5.4, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, 0.0, 8.0), (3.4, 0.0, 8.0), (4.6, 0.4, 2.2), (5.4, 0.4, 2.2)]},
        "B": {"team": "O", "wp": _still(7.0, 0.5)},
        "C": {"team": "O", "wp": _still(-7.0, 0.5)},
        "D": {"team": "D", "wp": [(0.0, 0.0, 7.0), (3.5, 0.0, 7.0), (4.7, 0.6, 3.2), (5.4, 0.6, 3.2)]},
        "E": {"team": "D", "wp": _still(5.5, 1.5)}},
        "ball": {"held": [(0.0, 0.6, "B"), (1.0, 5.4, "A")], "flights": [(0.6, 1.0, "B", "A")]}}),
    # The author's original 'iso': the handler only holds at the top (no attack) -> not an isolation (BA-T5).
    "iso_hold": dict(dur=4.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(0.0, 8.0)},
        "B": {"team": "O", "wp": _still(7.0, 0.5)},
        "C": {"team": "O", "wp": _still(-7.0, 0.5)},
        "D": {"team": "D", "wp": _still(0.0, 7.0)},
        "E": {"team": "D", "wp": _still(5.5, 1.5)}},
        "ball": {"held": [(0.0, 0.6, "B"), (1.0, 4.5, "A")], "flights": [(0.6, 1.0, "B", "A")]}}),
    # Same, but S comes up to screen next to A (1.0 m) at 2.0 s.
    "screen": dict(dur=4.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(0.0, 8.0)},
        "B": {"team": "O", "wp": _still(7.0, 0.5)},
        "S": {"team": "O", "wp": [(0.0, 2.0, 3.0), (1.0, 2.0, 3.0), (2.0, 0.9, 7.4), (4.5, 0.9, 7.4)]},
        "D": {"team": "D", "wp": _still(0.0, 7.0)}},
        "ball": {"held": [(0.0, 0.6, "B"), (1.0, 4.5, "A")], "flights": [(0.6, 1.0, "B", "A")]}}),
    # A (right wing) lobs to cutter B running at the rim; catch at r ~ 1.1 m while moving fast.
    "lob": dict(dur=3.6, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 5.0)},
        "B": {"team": "O", "wp": [(0.0, -3.4, 5.6), (1.2, -3.4, 5.6), (3.0, 0.6, -0.4), (3.6, 0.6, -0.4)]},
        "D": {"team": "D", "wp": _still(5.3, 4.3)},
        "E": {"team": "D", "wp": _still(-2.6, 4.6)}},
        "ball": {"held": [(0.0, 1.4, "A"), (2.5, 3.6, "B")], "flights": [(1.4, 2.5, "A", "B")]}}),
    # High, slow skip pass (1.2 s) to a stationary corner shooter: long time of flight, no lob target.
    "high_skip": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.5, 4.0)},
        "B": {"team": "O", "wp": _still(-7.0, 0.5)},
        "D": {"team": "D", "wp": _still(5.7, 3.5)}},
        "ball": {"held": [(0.0, 1.2, "A"), (2.4, 4.0, "B")], "flights": [(1.2, 2.4, "A", "B")]}}),
    # A shoots from the wing at 1.5 s; R (defence) rebounds at 2.8 s and outlets to Q at 3.6 s.
    "rebound_outlet": dict(dur=5.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(5.0, 5.0)},
        "B": {"team": "O", "wp": _still(-5.5, 4.0)},
        "R": {"team": "D", "wp": [(0.0, 1.8, 2.2), (2.0, 1.8, 2.2), (2.7, 1.0, 1.5), (5.0, 1.0, 1.5)]},
        "Q": {"team": "D", "wp": _still(-4.0, 12.0)},
        "rim": RIM},
        "ball": {"held": [(0.0, 1.5, "A"), (2.8, 3.6, "R"), (4.2, 5.0, "Q")],
                 "flights": [(1.5, 2.3, "A", "rim"), (2.3, 2.8, "rim", "R"), (3.6, 4.2, "R", "Q")]}}),
    # A passes toward B; defender D steps into the lane and intercepts at 1.9 s.
    "intercept": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 5.0)},
        "B": {"team": "O", "wp": _still(-1.0, 8.5)},
        "D": {"team": "D", "wp": [(0.0, 3.5, 5.0), (1.2, 3.5, 5.0), (1.9, 2.6, 6.8), (3.5, 2.6, 6.8)]}},
        "ball": {"held": [(0.0, 1.5, "A"), (1.9, 3.5, "D")], "flights": [(1.5, 1.9, "A", "D")]}}),
    # D strips A directly (control switches at 2.0 s with D 0.8 m from A, no free ball).
    "strip": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(4.0, 6.0)},
        "B": {"team": "O", "wp": _still(-5.0, 5.0)},
        "D": {"team": "D", "wp": [(0.0, 2.9, 5.4), (1.6, 2.9, 5.4), (2.0, 3.3, 5.6), (2.4, 2.9, 6.6), (3.5, 2.6, 8.0)]}},
        "ball": {"held": [(0.0, 2.0, "A"), (2.0, 3.5, "D")]}}),
    # A fumbles: the ball rolls slowly away (1.5-2.3 s), lies loose, B recovers at 3.6 s.
    "loose": dict(dur=4.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(4.0, 6.0)},
        "B": {"team": "O", "wp": [(0.0, -2.0, 7.5), (2.4, -2.0, 7.5), (3.6, 1.6, 7.6), (4.5, 1.6, 7.6)]},
        "D": {"team": "D", "wp": _still(5.0, 5.2)},
        "spot": {"team": "X", "wp": _still(2.2, 7.6)}},
        "ball": {"held": [(0.0, 1.5, "A"), (2.3, 3.6, "spot"), (3.6, 4.5, "B")],
                 "flights": [(1.5, 2.3, "A", "spot")]}}),
    # Tie-up: A holds; from 1.0 s the ball sits between A and D (both 0.3 m from it).
    "tie_up": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(3.0, 6.0)},
        "D": {"team": "D", "wp": [(0.0, 3.0, 7.6), (0.6, 3.0, 7.6), (1.0, 3.0, 6.6), (3.5, 3.0, 6.6)]},
        "spot": {"team": "X", "wp": _still(3.0, 6.3)}},
        "ball": {"held": [(0.0, 1.0, "A"), (1.0, 3.5, "spot")]}}),
    # B passes to A at the right wing (0.8 s); A dribbles across the top to the left wing (1.5-3.5 s).
    "dribble_rev": dict(dur=4.5, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, 5.0, 7.0), (1.5, 5.0, 7.0), (3.5, -5.0, 7.0), (4.5, -5.0, 7.0)]},
        "B": {"team": "O", "wp": _still(7.0, 0.5)},
        "D": {"team": "D", "wp": [(0.0, 4.4, 6.2), (1.5, 4.4, 6.2), (3.5, -4.4, 6.2), (4.5, -4.4, 6.2)]}},
        "ball": {"held": [(0.0, 0.4, "B"), (0.8, 4.5, "A")], "flights": [(0.4, 0.8, "B", "A")]}}),
    # Swing: A (right wing) to adjacent B (right slot) at 1.5 s.
    "swing": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.5, 3.0)},
        "B": {"team": "O", "wp": _still(3.5, 6.0)},
        "C": {"team": "O", "wp": _still(-6.5, 3.0)},
        "D": {"team": "D", "wp": _still(5.6, 2.6)}},
        "ball": {"held": [(0.0, 1.5, "A"), (2.0, 3.5, "B")], "flights": [(1.5, 2.0, "A", "B")]}}),
    # High-low: H at the right elbow feeds L in the right low post.
    "high_low": dict(dur=3.5, spec={"actors": {
        "H": {"team": "O", "wp": _still(1.8, 4.2)},
        "L": {"team": "O", "wp": _still(2.0, 1.15)},
        "DH": {"team": "D", "wp": _still(1.6, 3.3)},
        "DL": {"team": "D", "wp": _still(1.4, 0.7)}},
        "ball": {"held": [(0.0, 1.5, "H"), (2.0, 3.5, "L")], "flights": [(1.5, 2.0, "H", "L")]}}),
    # Middle drive from the right wing (1.0-2.6 s), dump-off to a left dunker at 2.8 s.
    "dump": dict(dur=4.4, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, 6.0, 4.5), (1.0, 6.0, 4.5), (2.6, 1.5, 2.6), (4.4, 1.5, 2.6)]},
        "B": {"team": "O", "wp": _still(0.0, 7.8)},
        "K": {"team": "O", "wp": _still(-2.2, 0.2)},
        "D": {"team": "D", "wp": [(0.0, 5.3, 3.9), (1.0, 5.3, 3.9), (2.6, 2.4, 3.2), (4.4, 2.4, 3.2)]},
        "DK": {"team": "D", "wp": [(0.0, -1.6, 1.6), (2.0, -1.6, 1.6), (2.7, -0.2, 2.2), (4.4, -0.2, 2.2)]}},
        "ball": {"held": [(0.0, 0.4, "B"), (0.8, 2.8, "A"), (3.2, 4.4, "K")],
                 "flights": [(0.4, 0.8, "B", "A"), (2.8, 3.2, "A", "K")]}}),
    # C -> A (catch 1.2 s), A swings it on one-touch (0.2 s) to B (catch 2.1 s), B shoots at 2.9 s.
    "hockey": dict(dur=4.0, spec={"actors": {
        "C": {"team": "O", "wp": _still(-6.5, 3.0)},
        "A": {"team": "O", "wp": _still(0.0, 7.8)},
        "B": {"team": "O", "wp": _still(6.5, 3.0)},
        "DA": {"team": "D", "wp": _still(0.0, 6.6)},
        "rim": RIM},
        "ball": {"held": [(0.0, 0.5, "C"), (1.2, 1.4, "A"), (2.1, 2.9, "B")],
                 "flights": [(0.5, 1.2, "C", "A"), (1.4, 2.1, "A", "B"), (2.9, 3.6, "B", "rim")]}}),
    # B passes to A (catch 1.0 s); A holds still 2.5 s and shoots at 3.5 s (held jumper).
    "held_shot": dict(dur=4.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(5.5, 5.0)},
        "B": {"team": "O", "wp": _still(-1.0, 8.0)},
        "D": {"team": "D", "wp": _still(4.6, 4.3)},
        "rim": RIM},
        "ball": {"held": [(0.0, 0.6, "B"), (1.0, 3.5, "A")],
                 "flights": [(0.6, 1.0, "B", "A"), (3.5, 4.2, "A", "rim")]}}),
    # Baseline pass from corner to corner that runs under the rim (not a shot).
    "baseline_pass": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.9, 0.0)},
        "B": {"team": "O", "wp": _still(-6.9, 0.0)},
        "D": {"team": "D", "wp": _still(5.9, 0.6)}},
        "ball": {"held": [(0.0, 1.2, "A"), (2.0, 3.5, "B")], "flights": [(1.2, 2.0, "A", "B")]}}),
    # Handoff: B runs past A (closest 0.7 m), control switches at 1.6 s with no flight (not a pass).
    "handoff": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(5.0, 6.5)},
        "B": {"team": "O", "wp": [(0.0, 7.0, 5.0), (0.6, 7.0, 5.0), (1.6, 5.4, 5.6), (2.6, 3.8, 6.2), (3.5, 3.8, 6.2)]},
        "D": {"team": "D", "wp": _still(4.2, 7.6)}},
        "ball": {"held": [(0.0, 1.6, "A"), (1.6, 3.5, "B")]}}),
}


# --------------------------------------------------------------------------------------
# changes_loop1 regression scenarios (from the independent tester's harness, BA-T1..BA-T18)
# --------------------------------------------------------------------------------------
SCENARIOS.update({
    # BA-T1 / BA-T17: swing to the top, straight drive, layup released from r ~1.0 (inside the exit radius).
    "l1_layup": dict(dur=4.0, spec={"actors": {
        "W": {"team": "O", "wp": _still(6.0, 4.5)},
        "A": {"team": "O", "wp": [(0.0, 0.0, 8.2), (1.2, 0.0, 8.2), (2.6, 0.3, 1.0), (4.0, 0.3, 1.0)]},
        "C": {"team": "O", "wp": _still(-6.5, 3.0)},
        "DA": {"team": "D", "wp": [(0.0, 0.6, 7.3), (1.3, 0.6, 7.3), (2.7, 0.9, 2.6), (4.0, 0.9, 2.6)]},
        "H": {"team": "D", "wp": [(0.0, -3.0, 2.0), (1.8, -3.0, 2.0), (2.5, -0.9, 1.3), (4.0, -0.9, 1.3)]},
        "DW": {"team": "D", "wp": _still(5.2, 3.9)},
        "rim": RIM},
        "ball": {"held": [(0.0, 0.6, "W"), (1.0, 2.75, "A")],
                 "flights": [(0.6, 1.0, "W", "A"), (2.75, 3.1, "A", "rim")]}}),
    # BA-T2: closeout baseline drive, drift dump-off under the rim to the weak-side dunker.
    "l1_dump_baseline": dict(dur=4.6, spec={"actors": {
        "T": {"team": "O", "wp": _still(0.5, 8.0)},
        "A": {"team": "O", "wp": [(0.0, 6.4, 3.2), (0.9, 6.4, 3.2), (2.3, 2.4, 0.4), (4.6, 2.4, 0.4)]},
        "K": {"team": "O", "wp": _still(-2.3, 0.3)},
        "C": {"team": "O", "wp": _still(-6.6, 1.0)},
        "DA": {"team": "D", "wp": [(0.0, 2.8, 2.6), (0.2, 2.8, 2.6), (0.8, 5.7, 2.9), (0.95, 5.7, 2.9), (2.4, 3.3, 1.3),
                                   (4.6, 3.3, 1.3)]},
        "DK": {"team": "D", "wp": [(0.0, -1.0, 1.8), (1.3, -1.0, 1.8), (2.0, 2.0, 1.2), (4.6, 2.0, 1.2)]},
        "DT": {"team": "D", "wp": _still(0.5, 6.8)}},
        "ball": {"held": [(0.0, 0.3, "T"), (0.8, 2.5, "A"), (2.85, 4.6, "K")],
                 "flights": [(0.3, 0.8, "T", "A"), (2.5, 2.85, "A", "K")]}}),
    # BA-T7: set wing catch, one side-step dribble (1.8 m), pull-up three 1.05 s after the catch.
    "l1_one_dribble_pullup": dict(dur=4.0, spec={"actors": {
        "P": {"team": "O", "wp": _still(0.3, 8.0)},
        "A": {"team": "O", "wp": [(0.0, 6.3, 3.3), (1.0, 6.3, 3.3), (1.5, 5.0, 4.6), (4.0, 5.0, 4.6)]},
        "DA": {"team": "D", "wp": [(0.0, 5.2, 2.7), (0.6, 5.2, 2.7), (1.0, 5.5, 3.0), (1.6, 4.5, 4.0), (4.0, 4.5, 4.0)]},
        "DP": {"team": "D", "wp": _still(0.3, 7.0)},
        "rim": RIM},
        "ball": {"held": [(0.0, 0.4, "P"), (0.85, 1.9, "A")],
                 "flights": [(0.4, 0.85, "P", "A"), (1.9, 2.6, "A", "rim")]}}),
    # BA-T4 / BA-T6: 18-ft face-up catch at (3.9, 3.9) with the defender 0.85 m away: no post-up, no tie-up.
    "l1_faceup": dict(dur=4.0, spec={"actors": {
        "G": {"team": "O", "wp": _still(0.0, 8.0)},
        "A": {"team": "O", "wp": _still(3.9, 3.9)},
        "C": {"team": "O", "wp": _still(-6.5, 2.0)},
        "DA": {"team": "D", "wp": _still(3.3, 3.3)},
        "DG": {"team": "D", "wp": _still(0.0, 7.0)}},
        "ball": {"held": [(0.0, 0.5, "G"), (0.95, 3.2, "A"), (3.65, 4.0, "G")],
                 "flights": [(0.5, 0.95, "G", "A"), (3.2, 3.65, "A", "G")]}}),
    # BA-T15: corner entry to a sealed post on the block (0.17 m outside the lane), spin into the paint, layup.
    "l1_post_spin": dict(dur=4.6, spec={"actors": {
        "C": {"team": "O", "wp": _still(6.9, 0.4)},
        "P": {"team": "O", "wp": [(0.0, 3.0, 2.0), (0.6, 2.0, 1.15), (3.0, 2.0, 1.15), (3.5, 0.7, 0.5), (4.6, 0.7, 0.5)]},
        "G": {"team": "O", "wp": _still(-1.0, 8.0)},
        "DP": {"team": "D", "wp": [(0.0, 2.4, 2.2), (0.6, 1.35, 1.25), (3.1, 1.35, 1.25), (3.6, 1.2, 1.0), (4.6, 1.2, 1.0)]},
        "DC": {"team": "D", "wp": _still(6.0, 1.2)},
        "rim": RIM},
        "ball": {"held": [(0.0, 1.6, "C"), (2.0, 3.6, "P")],
                 "flights": [(1.6, 2.0, "C", "P"), (3.6, 3.8, "P", "rim")]}}),
    # BA-T13: lob over the top (1.1 s air) to a fast rim cutter who catches on the move.
    "l1_lob_cutter": dict(dur=3.6, spec={"actors": {
        "A": {"team": "O", "wp": _still(-6.0, 5.0)},
        "B": {"team": "O", "wp": [(0.0, 2.5, 6.5), (1.0, 2.5, 6.5), (2.6, 0.9, 1.0), (3.6, 0.9, 1.0)]},
        "DA": {"team": "D", "wp": _still(-5.3, 4.3)},
        "DB": {"team": "D", "wp": [(0.0, 2.2, 5.6), (1.1, 2.2, 5.6), (2.8, 1.0, 2.2), (3.6, 1.0, 2.2)]},
        "rim": RIM},
        "ball": {"held": [(0.0, 1.4, "A"), (2.5, 2.8, "B")],
                 "flights": [(1.4, 2.5, "A", "B"), (2.8, 3.05, "B", "rim")]}}),
    # BA-T9: wing jumper falls short (airball) and a defender grabs it at r 1.7.
    "l1_airball": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.3, 3.5)},
        "B": {"team": "O", "wp": _still(-5.5, 4.0)},
        "DA": {"team": "D", "wp": _still(5.6, 3.0)},
        "D2": {"team": "D", "wp": _still(1.0, 1.4)},
        "rim": RIM},
        "ball": {"held": [(0.0, 1.0, "A"), (1.9, 4.0, "D2")], "flights": [(1.0, 1.9, "A", "D2")]}}),
    # BA-T3: pass deflected by D, ball rolls loose slowly, intended receiver B recovers (no possession change).
    "l1_deflect": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.3, 3.5)},
        "B": {"team": "O", "wp": [(0.0, 0.3, 7.6), (1.6, 0.3, 7.6), (2.4, 2.0, 6.85), (4.0, 2.0, 6.85)]},
        "D": {"team": "D", "wp": [(0.0, 4.2, 5.0), (0.9, 4.2, 5.0), (1.3, 3.5, 5.6), (4.0, 3.5, 5.6)]},
        "DB": {"team": "D", "wp": _still(0.3, 6.6)},
        "spot": {"team": "X", "wp": _still(2.0, 6.6)}},
        "ball": {"held": [(0.0, 1.0, "A"), (2.2, 2.4, "spot"), (2.4, 4.0, "B")],
                 "flights": [(1.0, 1.3, "A", "D"), (1.3, 2.2, "D", "spot")]}}),
    # BA-T12: pass sails out of bounds over the right sideline and the ball rests there.
    "l1_oob": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(5.0, 6.5)},
        "W": {"team": "O", "wp": [(0.0, 6.3, 8.5), (1.0, 6.3, 8.5), (1.8, 6.0, 10.5), (3.5, 6.0, 10.5)]},
        "DA": {"team": "D", "wp": _still(4.3, 5.8)},
        "DW": {"team": "D", "wp": _still(5.8, 7.6)},
        "spot": {"team": "X", "wp": _still(8.6, 9.5)}},
        "ball": {"held": [(0.0, 1.2, "A"), (1.7, 3.5, "spot")], "flights": [(1.2, 1.7, "A", "spot")]}}),
    # BA-T6 (and the rejected BA-T2 far-side rule): missed three, offensive rebound at r 2.4, putback after 0.5 s.
    "l1_putback": dict(dur=4.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(-6.3, 3.5)},
        "B": {"team": "O", "wp": [(0.0, 2.6, 2.2), (1.6, 2.6, 2.2), (2.0, 1.8, 1.6), (4.5, 1.8, 1.6)]},
        "DA": {"team": "D", "wp": _still(-5.6, 3.0)},
        "DB": {"team": "D", "wp": _still(0.9, 0.8)},
        "rim": RIM},
        "ball": {"held": [(0.0, 1.0, "A"), (2.1, 2.6, "B")],
                 "flights": [(1.0, 1.7, "A", "rim"), (1.7, 2.1, "rim", "B"), (2.6, 2.9, "B", "rim")]}}),
    # BA-T4: holder still with an on-ball defender 0.75 m in front for 4 s (ordinary defence, not a tie-up).
    "l1_tight_onball": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(3.0, 6.5)},
        "B": {"team": "O", "wp": _still(-5.0, 4.0)},
        "DA": {"team": "D", "wp": _still(3.0, 5.75)}},
        "ball": {"held": [(0.0, 4.0, "A")]}}),
    # BA-T11: dribble handoff at the slot; the receiver runs past and drives to a layup (no pass).
    "l1_dho": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(3.0, 7.0)},
        "B": {"team": "O", "wp": [(0.0, 6.0, 5.5), (0.4, 6.0, 5.5), (1.2, 3.5, 6.5), (2.6, 0.8, 1.5), (4.0, 0.8, 1.5)]},
        "DB": {"team": "D", "wp": [(0.0, 5.4, 5.0), (0.4, 5.4, 5.0), (1.3, 3.9, 5.7), (2.7, 1.6, 2.6), (4.0, 1.6, 2.6)]},
        "DA": {"team": "D", "wp": _still(2.6, 6.0)},
        "rim": RIM},
        "ball": {"held": [(0.0, 1.2, "A"), (1.2, 2.8, "B")], "flights": [(2.8, 3.1, "B", "rim")]}}),
    # BA-T8: middle drive from the left slot, kick-out to the right-wing three (drive-and-kick, not a reversal).
    "l1_slot_kick": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, -3.5, 6.8), (1.0, -3.5, 6.8), (2.3, -0.5, 2.6), (4.0, -0.5, 2.6)]},
        "W": {"team": "O", "wp": _still(6.4, 3.0)},
        "DA": {"team": "D", "wp": [(0.0, -3.1, 6.0), (1.1, -3.1, 6.0), (2.4, -0.9, 3.6), (4.0, -0.9, 3.6)]},
        "DW": {"team": "D", "wp": [(0.0, 5.6, 2.6), (1.4, 5.6, 2.6), (2.2, 2.4, 1.8), (2.6, 2.4, 1.8), (3.2, 5.0, 2.6),
                                   (4.0, 5.0, 2.6)]},
        "rim": RIM},
        "ball": {"held": [(0.0, 2.4, "A"), (2.85, 3.3, "W")],
                 "flights": [(2.4, 2.85, "A", "W"), (3.3, 3.9, "W", "rim")]}}),
    # BA-T14: pull-up three off a 4 m lateral dribble at the top (dribble onset at 1.0 s).
    "l1_pullup_top": dict(dur=3.6, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, 0.3, 8.5), (1.0, 0.3, 8.5), (2.0, -3.5, 7.0), (3.6, -3.5, 7.0)]},
        "B": {"team": "O", "wp": _still(6.5, 2.0)},
        "DA": {"team": "D", "wp": [(0.0, 0.3, 7.5), (1.1, 0.3, 7.5), (2.1, -2.9, 6.2), (3.6, -2.9, 6.2)]},
        "rim": RIM},
        "ball": {"held": [(0.0, 2.4, "A")], "flights": [(2.4, 3.1, "A", "rim")]}}),
    # BA-T10: closeout defender D lands on the ball for the shooter's last 0.45 s (decoded as a short D touch),
    # then the ball flies at the rim: a contest, the shot is A's.
    "l1_closeout_contest": dict(dur=3.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 4.0)},
        "B": {"team": "O", "wp": _still(-5.0, 4.0)},
        "D": {"team": "D", "wp": [(0.0, 4.6, 3.0), (0.8, 4.6, 3.0), (1.0, 5.6, 3.7), (3.0, 5.6, 3.7)]},
        "rim": RIM},
        "ball": {"held": [(0.0, 1.0, "A"), (1.0, 1.45, "D")], "flights": [(1.45, 2.1, "D", "rim")]}}),
})


# --------------------------------------------------------------------------------------
# changes_loop2 regression scenarios (from the independent tester's harness; loop-2 confirmer failures)
# --------------------------------------------------------------------------------------
SCENARIOS.update({
    # BA-T10b: T -> A swing, A drives from the right wing with DA tight, kicks out to E at the elbow; E's
    # closeout defender DE arrives at the catch and E shoots at 3.3 s (no possession change anywhere).
    "l2_drive_kick_mid": dict(dur=4.4, spec={"actors": {
        "T": {"team": "O", "wp": _still(0.0, 8.0)},
        "A": {"team": "O", "wp": [(0.0, 6.2, 4.0), (1.0, 6.2, 4.0), (2.4, 1.5, 2.4), (4.4, 1.5, 2.4)]},
        "E": {"team": "O", "wp": _still(3.6, 4.2)},
        "DA": {"team": "D", "wp": [(0.0, 5.4, 3.4), (1.1, 5.4, 3.4), (2.5, 2.6, 3.2), (4.4, 2.6, 3.2)]},
        "H": {"team": "D", "wp": [(0.0, -1.5, 2.0), (1.6, -1.5, 2.0), (2.3, 0.6, 2.2), (4.4, 0.6, 2.2)]},
        "DE": {"team": "D", "wp": [(0.0, 3.0, 3.4), (2.5, 3.0, 3.4), (3.1, 3.2, 3.7), (4.4, 3.2, 3.7)]},
        "rim": RIM},
        "ball": {"held": [(0.0, 0.3, "T"), (0.75, 2.5, "A"), (2.85, 3.3, "E")],
                 "flights": [(0.3, 0.75, "T", "A"), (2.5, 2.85, "A", "E"), (3.3, 3.9, "E", "rim")]}}),
    # BA-T10b guard: a real interception (D steps into the skip lane at 1.4 s and runs out with the ball).
    "l2_skip_intercepted": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(-6.3, 3.5)},
        "B": {"team": "O", "wp": _still(6.3, 3.5)},
        "D": {"team": "D", "wp": [(0.0, -1.0, 5.0), (0.9, -1.0, 5.0), (1.4, 0.5, 4.3), (1.5, 0.5, 4.3), (4.0, 1.0, 11.0)]},
        "DA": {"team": "D", "wp": _still(-5.6, 3.0)}},
        "ball": {"held": [(0.0, 1.0, "A"), (1.4, 4.0, "D")], "flights": [(1.0, 1.4, "A", "D")]}}),
    # BA-T14b: transition push from the backcourt after an outlet (slow ramp from rest at 1.0 s), layup.
    "l2_transition_push": dict(dur=5.4, spec={"actors": {
        "R": {"team": "O", "wp": _still(-4.0, 24.0)},
        "A": {"team": "O", "wp": [(0.0, -2.0, 20.0), (1.0, -2.0, 20.0), (4.4, -0.5, 1.0), (5.4, -0.5, 1.0)]},
        "DA": {"team": "D", "wp": [(0.0, 0.0, 15.0), (1.0, 0.0, 15.0), (4.4, 0.8, 1.8), (5.4, 0.8, 1.8)]},
        "rim": RIM},
        "ball": {"held": [(0.0, 0.4, "R"), (0.8, 4.5, "A")],
                 "flights": [(0.4, 0.8, "R", "A"), (4.5, 4.75, "A", "rim")]}}),
    # BA-T4b: tie-up at the end of a drive; from 2.0 s the ball sits between A and D (0.3 m from each).
    "l2_drive_tieup": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, 6.0, 4.5), (0.8, 6.0, 4.5), (1.8, 3.4, 2.4), (4.0, 3.4, 2.4)]},
        "B": {"team": "O", "wp": _still(-5.0, 4.0)},
        "D": {"team": "D", "wp": [(0.0, 5.3, 3.8), (0.8, 5.3, 3.8), (1.7, 3.2, 2.0), (2.0, 3.2, 1.8), (4.0, 3.2, 1.8)]},
        "spot": {"team": "X", "wp": _still(3.3, 2.1)}},
        "ball": {"held": [(0.0, 2.0, "A"), (2.0, 4.0, "spot")]}}),
    # changes_loop3 scenarios (confirm2 adversarial probes and the loop-2 confirmer's harness, same specs).
    # BA-T10c probe P1: D rips the ball from A at 1.5 s, holds 0.6 s with A 1.0 m away, outlets to E at 2.1 s.
    "l3_strip_outlet": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, 6.0, 5.0), (4.0, 6.0, 5.0)]},
        "B": {"team": "O", "wp": _still(-6.0, 4.0)},
        "D": {"team": "D", "wp": [(0.0, 5.2, 4.4), (4.0, 5.2, 4.4)]},
        "E": {"team": "D", "wp": _still(2.0, 10.0)}},
        "ball": {"held": [(0.0, 1.5, "A"), (1.5, 2.1, "D"), (2.5, 4.0, "E")], "flights": [(2.1, 2.5, "D", "E")]}}),
    # BA-T10c probe P2: pick-pocket at 1.6 s, D dribbles up-court with A chasing ~0.8 m behind to the clip end.
    "l3_strip_chased": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, 0.0, 8.0), (1.5, 0.0, 8.0), (4.0, 0.0, 13.0)]},
        "D": {"team": "D", "wp": [(0.0, 0.0, 7.2), (1.5, 0.0, 7.2), (1.6, 0.0, 8.7), (4.0, 0.0, 13.9)]},
        "W": {"team": "O", "wp": _still(6.0, 4.0)},
        "DW": {"team": "D", "wp": _still(5.3, 3.6)}},
        "ball": {"held": [(0.0, 1.5, "A"), (1.6, 4.0, "D")], "flights": []}}),
    # harness S03: hard dribble from 10.5 m to the arc after a catch from T (3.35 m away): not an isolation.
    "l3_arc_attack": dict(dur=4.0, spec={"actors": {
        "T": {"team": "O", "wp": _still(-2.5, 12.0)},
        "A": {"team": "O", "wp": [(0.0, 0.5, 10.5), (1.0, 0.5, 10.5), (2.2, 0.3, 6.9), (4.0, 0.3, 6.9)]},
        "W": {"team": "O", "wp": _still(6.2, 3.8)},
        "DA": {"team": "D", "wp": [(0.0, 0.5, 9.5), (1.0, 0.5, 9.5), (2.3, 0.3, 6.0), (4.0, 0.3, 6.0)]},
        "DW": {"team": "D", "wp": _still(5.4, 3.3)}},
        "ball": {"held": [(0.0, 0.5, "T"), (0.9, 3.0, "A"), (3.45, 4.0, "W")],
                 "flights": [(0.5, 0.9, "T", "A"), (3.0, 3.45, "A", "W")]}}),
    # harness S26: dribble reversal left wing -> right wing across the top, shadowing defender: not an isolation.
    "l3_dribble_reversal": dict(dur=4.6, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, -6.2, 4.6), (1.0, -6.2, 4.6), (2.2, -0.5, 7.8), (3.4, 6.2, 4.6), (4.6, 6.2, 4.6)]},
        "B": {"team": "O", "wp": _still(-6.8, 0.5)},
        "DA": {"team": "D", "wp": [(0.0, -5.5, 4.0), (1.0, -5.5, 4.0), (2.2, -0.5, 6.9), (3.4, 5.5, 4.0), (4.6, 5.5, 4.0)]}},
        "ball": {"held": [(0.0, 4.6, "A")]}}),
    # harness S17: clear-out isolation on the right wing, A holds 2.6 s at rest, baseline drive from 3.5 s.
    "l3_iso_clear": dict(dur=5.4, spec={"actors": {
        "T": {"team": "O", "wp": [(0.0, 0.0, 8.0), (0.9, 0.0, 8.0), (1.8, -6.0, 4.0), (5.4, -6.0, 4.0)]},
        "A": {"team": "O", "wp": [(0.0, 6.0, 4.5), (3.5, 6.0, 4.5), (4.6, 2.6, 0.3), (5.4, 2.6, 0.3)]},
        "C": {"team": "O", "wp": _still(-6.8, 0.5)},
        "DA": {"team": "D", "wp": [(0.0, 5.2, 3.8), (3.6, 5.2, 3.8), (4.7, 3.2, 1.0), (5.4, 3.2, 1.0)]},
        "DT": {"team": "D", "wp": [(0.0, 0.0, 7.0), (0.9, 0.0, 7.0), (1.8, -3.5, 3.5), (5.4, -3.5, 3.5)]},
        "rim": RIM},
        "ball": {"held": [(0.0, 0.4, "T"), (0.85, 4.7, "A")],
                 "flights": [(0.4, 0.85, "T", "A"), (4.7, 4.95, "A", "rim")]}}),
})


def truth_time(name, actor, pred, after=0.0):
    """First time (s) at which the noise-free path of `actor` satisfies pred(x, y)."""
    sc = SCENARIOS[name]
    n = int(round(sc["dur"] / DT)) + 1
    x, y = sim.path(sc["spec"]["actors"][actor]["wp"], n)
    for i in range(int(round(after / DT)), n):
        if pred(x[i], y[i]):
            return i * DT
    raise AssertionError(f"{actor} never satisfies the predicate in {name}")


@lru_cache(maxsize=None)
def scene(name, seed, sigma=SIGMA):
    """Simulated and smoothed scene for one scenario and seed (pseudo actors dropped)."""
    sc = SCENARIOS[name]
    _, tracks = sim.scenario(sc["spec"], sc["dur"], sigma, seed)
    tracks = [t for t in tracks if t.oid != "rim" and not t.oid.startswith("spot")]
    return build_scene(tracks)


@lru_cache(maxsize=None)
def run(item, name, seed):
    return tuple(BA.DETECTORS[item](scene(name, seed)))


def events(item, name, seed, kind=None):
    return [e for e in run(item, name, seed) if kind is None or e.kind == kind]


def _match(item, name, seed, kind, actors, t0_s, conf_lo=0.5, conf_hi=1.0, attrs=None):
    """Exactly-one-matching-event check: kind, actors subset, |t0 - truth| <= 0.3 s, conf range, attrs."""
    evs = events(item, name, seed, kind)
    cand = [e for e in evs if all(e.actors.get(k) == v for k, v in actors.items())]
    assert cand, f"{item}/{name}/seed{seed}: no {kind} with {actors}; got {[(e.actors, e.t0 * DT) for e in evs]}"
    best = min(cand, key=lambda e: abs(e.t0 * DT - t0_s))
    assert abs(best.t0 * DT - t0_s) <= TOL_S + 1e-9, f"t0 {best.t0 * DT:.3f} vs truth {t0_s}"
    assert conf_lo <= best.conf <= conf_hi, f"conf {best.conf:.3f} not in [{conf_lo}, {conf_hi}]"
    for k, v in (attrs or {}).items():
        assert best.attrs.get(k) == v, f"attr {k}={best.attrs.get(k)!r}, expected {v!r}"
    return best


# --------------------------------------------------------------------------------------
# Positive cases: (item, scenario, kind, actors, truth t0 s, conf_lo, conf_hi, attrs)
# --------------------------------------------------------------------------------------
POSITIVE = [
    ("touch", "pass_cs", "touch", {"holder": "B", "team": "offense"}, 2.1, 0.5, 1.0,
     {"start_kind": "pass", "end_kind": "shot"}),
    ("team_possession", "intercept", "team_possession", {"team": "defense"}, 1.9, 0.5, 1.0, None),
    ("ball_flight", "pass_cs", "ball_flight", {"from": "A", "to": "B"}, 1.5, 0.5, 1.0, {"shot": False}),
    ("loose_ball", "loose", "loose_ball", {"last_holder": "A", "recovered_by": "B"}, 2.1, 0.5, 1.0, None),
    ("contested_ball", "tie_up", "contested_ball", {"offense": "A", "defense": "D"}, 1.0, 0.5, 1.0,
     {"held_ball_candidate": True}),
    ("catch", "pass_cs", "catch", {"receiver": "B", "passer": "A"}, 2.1, 0.5, 1.0, {"catch_on_move": False}),
    ("release", "pass_cs", "release", {"holder": "A"}, 1.5, 0.5, 1.0, {"release_kind": "pass"}),
    ("release", "pass_cs", "release", {"holder": "B"}, 2.9, 0.5, 1.0, {"release_kind": "shot"}),
    ("release", "intercept", "release", {"holder": "A"}, 1.5, 0.5, 1.0, {"release_kind": "intercepted"}),
    ("dribble_inferred", "drive_pullup", "dribble_inferred", {"handler": "A"}, 1.4, 0.5, 1.0, None),
    ("dribble_inferred", "drive_kick", "dribble_inferred", {"handler": "A"}, 1.0, 0.5, 1.0, None),
    ("drive", "drive_kick", "drive", {"driver": "A", "defender": "D"}, 1.0, 0.5, 1.0,
     {"subtype": "drive", "nba_drive": True}),
    ("drive", "drive_pullup", "drive", {"driver": "A"}, 1.4, 0.5, 1.0, {"subtype": "drive"}),
    ("drive_direction", "drive_kick", "drive_direction", {"driver": "A"}, 1.0, 0.5, 1.0, {"label": "baseline"}),
    ("drive_direction", "drive_pullup", "drive_direction", {"driver": "A"}, 1.4, 0.5, 1.0, {"label": "middle"}),
    ("drive_depth", "drive_pullup", "drive_depth", {"driver": "A"}, 3.0, 0.5, 1.0, {"label": "floater"}),
    ("drive_depth", "drive_kick", "drive_depth", {"driver": "A"}, 2.6, 0.5, 1.0, {"label": "outside_lane_short"}),
    ("paint_touch", "drive_pullup", "paint_touch", {"holder": "A"},
     truth_time("drive_pullup", "A", lambda x, y: BA.coord("sd_paint_out", x, y) <= 0.0), 0.5, 1.0, {"via": "drive"}),
    ("drive_defender_reaction", "drive_kick", "drive_defender_reaction", {"driver": "A", "defender": "D", "help": "H"},
     1.0, 0.5, 1.0, {"label": "beaten"}),
    ("drive_outcome", "drive_kick", "drive_outcome", {"driver": "A"}, 2.6, 0.5, 1.0, {"label": "kick_out_pass"}),
    ("drive_outcome", "drive_pullup", "drive_outcome", {"driver": "A"}, 3.0, 0.5, 1.0, {"label": "shot"}),
    ("pass", "pass_cs", "pass", {"passer": "A", "receiver": "B"}, 1.5, 0.5, 1.0, {"delivery": "from_hold"}),
    ("pass", "hockey", "pass", {"passer": "A", "receiver": "B"}, 1.4, 0.5, 1.0, {"delivery": "one_touch"}),
    ("pass_incomplete", "intercept", "pass_incomplete", {"passer": "A", "defender": "D"}, 1.5, 0.5, 1.0,
     {"label": "intercepted"}),
    ("lob_pass", "lob", "lob_pass", {"passer": "A", "receiver": "B"}, 1.4, 0.3, 0.8, None),
    ("skip_pass", "pass_cs", "skip_pass", {"passer": "A", "receiver": "B"}, 1.5, 0.5, 1.0, {"skip_true": True}),
    ("swing_pass", "swing", "swing_pass", {"passer": "A", "receiver": "B"}, 1.5, 0.5, 1.0, None),
    ("entry_pass", "post", "entry_pass", {"passer": "W", "receiver": "P"}, 2.0, 0.5, 1.0, {"label": "post_entry"}),
    ("entry_pass", "high_low", "entry_pass", {"passer": "H", "receiver": "L"}, 1.5, 0.5, 1.0, {"label": "high_low"}),
    ("ball_reversal", "pass_cs", "ball_reversal", {"first_passer": "A", "final_receiver": "B"}, 1.5, 0.5, 1.0,
     {"via": "skip"}),
    ("dribble_reversal", "dribble_rev", "dribble_reversal", {"handler": "A"},
     truth_time("dribble_rev", "A", lambda x, y: x < 3.0), 0.5, 1.0, None),
    ("kick_out", "drive_kick", "kick_out", {"passer": "A", "receiver": "C"}, 2.8, 0.5, 1.0,
     {"subtype": "three", "source": "drive", "corner": True}),
    ("kick_out", "post", "kick_out", {"passer": "P", "receiver": "W"}, 4.6, 0.5, 1.0, {"source": "post"}),
    ("dump_off", "dump", "dump_off", {"passer": "A", "receiver": "K"}, 2.8, 0.5, 1.0, {"dunker_spot": True}),
    ("potential_assist", "pass_cs", "potential_assist", {"passer": "A", "receiver": "B"}, 1.5, 0.5, 1.0, None),
    ("hockey_assist", "hockey", "hockey_assist", {"passer": "C", "receiver": "A"}, 0.5, 0.5, 1.0,
     {"hockey_assist_nba": True}),
    ("outlet_pass", "rebound_outlet", "outlet_pass", {"passer": "R", "receiver": "Q"}, 3.6, 0.5, 1.0,
     {"outlet_quick": True}),
    ("post_seal", "post", "post_seal", {"post": "P", "defender": "DP"}, 0.8, 0.5, 1.0, None),
    ("post_up", "post", "post_up", {"post": "P", "defender": "DP", "passer": "W"}, 2.4, 0.5, 1.0,
     {"defense_position": "behind", "end_kind": "pass"}),
    ("isolation", "iso", "isolation", {"handler": "A", "defender": "D"}, 1.0, 0.5, 1.0, None),
    ("shot_release", "pass_cs", "shot_release", {"shooter": "B"}, 2.9, 0.5, 1.0, {"three": True}),
    ("shot_release", "rebound_outlet", "shot_release", {"shooter": "A"}, 1.5, 0.5, 1.0, None),
    ("catch_and_shoot", "pass_cs", "catch_and_shoot", {"shooter": "B"}, 2.9, 0.5, 1.0, {"cs_set": True}),
    ("pull_up", "drive_pullup", "pull_up", {"shooter": "A"}, 3.4, 0.5, 1.0, None),
    ("held_jumper", "held_shot", "held_jumper", {"shooter": "A"}, 3.5, 0.3, 0.7, None),
    ("rebound_control", "rebound_outlet", "rebound", {"rebounder": "R", "shooter": "A"}, 2.8, 0.5, 1.0,
     {"label": "defensive"}),
    ("live_ball_turnover", "intercept", "live_ball_turnover", {"lost_by": "A", "gained_by": "D"}, 1.9, 0.5, 1.0,
     {"label": "interception"}),
    ("live_ball_turnover", "strip", "live_ball_turnover", {"lost_by": "A", "gained_by": "D"}, 2.0, 0.5, 1.0,
     {"label": "strip"}),
]

# (item, scenario, kind or None): the item must not fire (kind None = no event at all).
NEGATIVE = [
    ("touch", "ball_alone", None), ("touch", "no_ball", None),
    ("team_possession", "ball_alone", None),
    ("ball_flight", "hold", None),
    ("loose_ball", "pass_cs", None),
    ("contested_ball", "hold", None),
    ("catch", "hold", None),
    ("release", "hold", None),
    ("dribble_inferred", "pass_cs", None), ("dribble_inferred", "held_shot", None),
    ("drive", "walk_in", None), ("drive", "post", None), ("drive", "dribble_rev", None),
    ("drive_direction", "walk_in", None),
    ("drive_depth", "walk_in", None),
    ("paint_touch", "pass_cs", None),
    ("drive_defender_reaction", "hold", None),
    ("drive_outcome", "walk_in", None),
    ("pass", "handoff", None), ("pass", "hold", None),
    ("pass_incomplete", "pass_cs", None),
    ("lob_pass", "pass_cs", None), ("lob_pass", "high_skip", None),
    ("skip_pass", "swing", None),
    ("swing_pass", "pass_cs", None),
    ("entry_pass", "swing", None),
    ("ball_reversal", "swing", None),
    ("dribble_reversal", "hold", None),
    ("kick_out", "pass_cs", None),
    ("dump_off", "drive_kick", None),
    ("potential_assist", "drive_kick", None),
    ("hockey_assist", "pass_cs", None),
    ("outlet_pass", "pass_cs", None),
    ("post_seal", "wing_catch", None),
    ("post_up", "wing_catch", None),
    ("isolation", "screen", None),
    ("shot_release", "baseline_pass", None), ("shot_release", "drive_kick", None),
    ("catch_and_shoot", "drive_pullup", None), ("catch_and_shoot", "held_shot", None),
    ("pull_up", "pass_cs", None),
    ("held_jumper", "pass_cs", None),
    ("rebound_control", "pass_cs", None),
    ("live_ball_turnover", "pass_cs", None),
]

# Items that need ball z / pose / PBP / restart state: never emitted from XY.
NEEDS_DATA = ["dribble_bounce", "dribble_move_type", "pass_height_type", "throw_in_pass", "violation_turnover",
              "fakes", "footwork"]
NEEDS_DATA_LOOKALIKE = {"dribble_bounce": "drive_pullup", "dribble_move_type": "dribble_rev",
                        "pass_height_type": "lob", "throw_in_pass": "pass_cs", "violation_turnover": "walk_in",
                        "fakes": "held_shot", "footwork": "drive_pullup"}


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("case", POSITIVE, ids=lambda c: f"{c[0]}-{c[1]}-{c[3]}")
def test_positive(case, seed):
    item, name, kind, actors, t0, lo, hi, attrs = case
    _match(item, name, seed, kind, actors, t0, lo, hi, attrs)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("case", NEGATIVE, ids=lambda c: f"{c[0]}-{c[1]}")
def test_negative(case, seed):
    item, name, kind = case
    evs = events(item, name, seed, kind)
    assert not evs, f"{item} fired on {name}: {[(e.kind, e.actors, round(e.t0 * DT, 2), e.attrs.get('label')) for e in evs]}"


@pytest.mark.parametrize("item", NEEDS_DATA)
def test_needs_data_items_return_nothing(item):
    assert BA.STATUS[item] in ("canonical", "proposal")
    spec = next(it for it in BA.DOC["items"] if it["id"] == item)
    assert spec["detectable"] == "needs_data" and spec.get("needs")
    for seed in SEEDS:
        assert BA.DETECTORS[item](scene(NEEDS_DATA_LOOKALIKE[item], seed)) == []
        assert BA.DETECTORS[item](scene("hold", seed)) == []


# --------------------------------------------------------------------------------------
# Structural tests
# --------------------------------------------------------------------------------------
def test_every_detector_has_positive_and_negative_cases():
    pos = {c[0] for c in POSITIVE}
    neg = {c[0] for c in NEGATIVE}
    for item in BA.DETECTORS:
        if item in NEEDS_DATA:
            continue
        assert item in pos, f"{item} has no positive case"
        assert item in neg, f"{item} has no negative case"


def test_yaml_and_detectors_agree():
    ids = {it["id"] for it in BA.DOC["items"]}
    non_rule = {it["id"] for it in BA.DOC["items"] if it["level"] != "rule"}
    assert set(BA.DETECTORS) == non_rule
    assert set(BA.DETECTORS) <= ids
    for it in BA.DOC["items"]:
        assert it["status"] in ("canonical", "proposal")
        assert it["level"] in ("primitive", "action", "set_component", "rule")
        for name, p in (it.get("params") or {}).items():
            assert "value" in p and "unit" in p, (it["id"], name)
        if it["level"] != "rule":
            assert (it["detectable"] == "needs_data") == (it["id"] in NEEDS_DATA), it["id"]


def test_params_override_and_unknown_param():
    sc = scene("drive_kick", 1)
    assert BA.detect_drive(sc)
    assert BA.detect_drive(sc, gain_min_m=20.0) == []  # override reaches the rule
    with pytest.raises(TypeError):
        BA.detect_drive(sc, not_a_param=1.0)


def test_detect_all_runs_on_every_scenario():
    for name in SCENARIOS:
        out = BA.detect_all(scene(name, 1))
        assert set(out) == set(BA.DETECTORS)
        for evs in out.values():
            for e in evs:
                assert 0.0 <= e.conf <= 1.0
                assert e.start <= e.t0 <= max(e.end, e.t0) or e.kind in ("drive_depth", "drive_outcome")


def test_no_ball_gives_no_events():
    out = BA.detect_all(scene("no_ball", 1))
    assert all(not v for v in out.values())


# --------------------------------------------------------------------------------------
# changes_loop1 regression tests (independent tester failures BA-T1..BA-T18; see changes_loop1 in the YAML)
# --------------------------------------------------------------------------------------
LOOP1_POSITIVE = [
    # BA-T1: close finish released inside the exit radius is a shot (and a release, and the drive's outcome)
    ("BA-T1", "shot_release", "l1_layup", "shot_release", {"shooter": "A"}, 2.75, 0.5, 1.0, None),
    # conf may be 0 here: the simulator ends the ball track at the rim frame, so the release sits near a
    # ball segment edge (edge_factor 0); the event itself is what BA-T1 restores
    ("BA-T1", "release", "l1_layup", "release", {"holder": "A"}, 2.75, 0.0, 1.0, {"release_kind": "shot"}),
    ("BA-T1", "drive_outcome", "l1_layup", "drive_outcome", {"driver": "A"}, 2.45, 0.5, 1.0, {"label": "shot"}),
    # BA-T2: dump-off under the rim is a pass, not a shot
    ("BA-T2", "dump_off", "l1_dump_baseline", "dump_off", {"passer": "A", "receiver": "K"}, 2.5, 0.5, 1.0,
     {"dunker_spot": True}),
    ("BA-T2", "drive_outcome", "l1_dump_baseline", "drive_outcome", {"driver": "A"}, 2.15, 0.5, 1.0,
     {"label": "dump_off_pass"}),
    # BA-T3: deflection the offence recovers is one loose ball
    ("BA-T3", "loose_ball", "l1_deflect", "loose_ball", {"last_holder": "A", "recovered_by": "B"}, 1.4, 0.5, 1.0, None),
    # BA-T5: an isolation with an attack (drive) is kept
    ("BA-T5", "isolation", "iso", "isolation", {"handler": "A", "defender": "D"}, 1.0, 0.5, 1.0, {"attack": "drive"}),
    # BA-T6 / rejected far-side rule: a long offensive rebound and putback stay two shots and a rebound
    ("BA-T6", "shot_release", "l1_putback", "shot_release", {"shooter": "A"}, 1.0, 0.5, 1.0, None),
    ("BA-T6", "shot_release", "l1_putback", "shot_release", {"shooter": "B"}, 2.6, 0.5, 1.0, None),
    ("BA-T6", "rebound_control", "l1_putback", "rebound", {"rebounder": "B", "shooter": "A"}, 2.1, 0.5, 1.0,
     {"label": "offensive"}),
    # BA-T7: one-dribble pull-up after a set catch
    ("BA-T7", "pull_up", "l1_one_dribble_pullup", "pull_up", {"shooter": "A"}, 1.9, 0.5, 1.0, None),
    # BA-T8: drive-and-kick still a kick-out
    ("BA-T8", "kick_out", "l1_slot_kick", "kick_out", {"passer": "A", "receiver": "W"}, 2.4, 0.5, 1.0,
     {"subtype": "three", "source": "drive"}),
    # BA-T9: airball is an FGA and a defensive rebound
    ("BA-T9", "shot_release", "l1_airball", "shot_release", {"shooter": "A"}, 1.0, 0.5, 1.0, {"airball": True}),
    ("BA-T9", "rebound_control", "l1_airball", "rebound", {"rebounder": "D2", "shooter": "A"}, 1.9, 0.5, 1.0,
     {"label": "defensive"}),
    # BA-T11: DHO receiver's drive starts at the handoff
    ("BA-T11", "drive", "l1_dho", "drive", {"driver": "B"}, 1.2, 0.5, 1.0, None),
    # BA-T12: a throw-away out of bounds is still an incomplete pass
    ("BA-T12", "pass_incomplete", "l1_oob", "pass_incomplete", {"passer": "A"}, 1.2, 0.5, 1.0,
     {"label": "thrown_away_oob"}),
    # BA-T13: lob to a cutter caught on the move
    ("BA-T13", "lob_pass", "l1_lob_cutter", "lob_pass", {"passer": "A", "receiver": "B"}, 1.4, 0.2, 1.0, None),
]

LOOP1_NEGATIVE = [
    ("BA-T2", "shot_release", "l1_dump_baseline"), ("BA-T2", "rebound_control", "l1_dump_baseline"),
    ("BA-T3", "live_ball_turnover", "l1_deflect"), ("BA-T3", "pass_incomplete", "l1_deflect"),
    ("BA-T4", "contested_ball", "l1_tight_onball"), ("BA-T4", "contested_ball", "l1_faceup"),
    ("BA-T5", "isolation", "iso_hold"), ("BA-T5", "isolation", "l1_layup"),
    ("BA-T6", "post_up", "l1_faceup"), ("BA-T6", "post_up", "l1_putback"),
    ("BA-T6", "pass", "l1_putback"),
    ("BA-T7", "catch_and_shoot", "l1_one_dribble_pullup"),
    ("BA-T8", "ball_reversal", "l1_slot_kick"),
    ("BA-T9", "pass_incomplete", "l1_airball"), ("BA-T9", "live_ball_turnover", "l1_airball"),
    ("BA-T10", "live_ball_turnover", "l1_closeout_contest"),
    ("BA-T11", "pass", "l1_dho"),
    ("BA-T12", "loose_ball", "l1_oob"),
    ("BA-T17", "potential_assist", "l1_layup"),
]


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("case", LOOP1_POSITIVE, ids=lambda c: f"{c[0]}-{c[1]}-{c[2]}-{c[4]}")
def test_loop1_positive(case, seed):
    _, item, name, kind, actors, t0, lo, hi, attrs = case
    _match(item, name, seed, kind, actors, t0, lo, hi, attrs)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("case", LOOP1_NEGATIVE, ids=lambda c: f"{c[0]}-{c[1]}-{c[2]}")
def test_loop1_negative(case, seed):
    _, item, name = case
    evs = events(item, name, seed)
    assert not evs, f"{item} fired on {name}: {[(e.kind, e.actors, round(e.t0 * DT, 2), e.attrs.get('label')) for e in evs]}"


@pytest.mark.parametrize("seed", (2, 3))
def test_loop1_t10_closeout_contact_is_not_a_possession_change(seed):
    """BA-T10: the short defender touch before the shot is recorded as contact and the shot is A's."""
    sc = scene("l1_closeout_contest", seed)
    m = BA._model(sc)
    assert any(c[0] == "D" for c in m.contacts), m.contacts
    shots = BA.DETECTORS["shot_release"](sc)
    assert [e.actors["shooter"] for e in shots] == ["A"]


@pytest.mark.parametrize("seed", SEEDS)
def test_loop1_t14_dribble_onset_at_high_noise(seed):
    """BA-T14: at sigma 0.5 the dribble onset no longer drifts 0.3-0.6 s early (true onset 1.0 s)."""
    evs = BA.DETECTORS["dribble_inferred"](scene("l1_pullup_top", seed, 0.5))
    assert evs, "no dribble_inferred"
    assert abs(evs[0].t0 * DT - 1.1) <= TOL_S + 1e-9, evs[0].t0 * DT


def test_loop1_t15_paint_touch_not_before_entering_the_paint():
    """BA-T15: a post on the block 0.17 m outside the lane rarely 'touches the paint' before the spin
    (0.1.0: 6/20 seeds at sigma 0.3 per the tester; now 5/20, and <= 2 of seeds 1-10 required)."""
    truth = truth_time("l1_post_spin", "P", lambda x, y: BA.coord("sd_paint_out", x, y) <= 0.0, after=2.0)
    early = sum(any(e.t0 * DT < truth - TOL_S for e in BA.DETECTORS["paint_touch"](scene("l1_post_spin", seed)))
                for seed in range(1, 11))
    assert early <= 2, early


@pytest.mark.parametrize("name", ["dump", "l1_dump_baseline"])
def test_loop1_t16_dump_off_is_not_an_entry(name):
    """BA-T16: the driver's dump-off to the dunker is not labelled an entry pass."""
    for seed in SEEDS:
        evs = [e for e in BA.DETECTORS["entry_pass"](scene(name, seed)) if e.actors["passer"] == "A"]
        assert not evs, [(e.actors, e.attrs["label"]) for e in evs]


def test_loop1_t4_tie_up_basis_and_edge_drop():
    """BA-T4: the tie-up is found on the ball-between basis; no contested event starts at a segment edge."""
    for seed in SEEDS:
        evs = BA.DETECTORS["contested_ball"](scene("tie_up", seed))
        assert evs and all(e.attrs["basis"] in ("free_ball", "ball_between") for e in evs)
        assert all(BA.edge_factor(scene("tie_up", seed).ball, e.t0) > 0 for e in evs)


def test_loop1_t18_constants_are_yaml_params():
    """BA-T18: the formerly hard-coded windows are YAML params that reach the rules."""
    expect = {"lob_pass": ["receiver_vr_window_s", "lob_to_rim_r_m"], "drive": ["closeout_closing_window_s"],
              "shot_release": ["closing_window_s"], "catch_and_shoot": ["catch_speed_window_s"],
              "entry_pass": ["post_match_s"], "post_seal": ["seal_strict_r_m"], "isolation": ["max_gap_frames"],
              "touch": ["clip_start_s"], "pass_incomplete": ["heading_frames"]}
    for item, names in expect.items():
        for nm in names:
            assert nm in BA.PARAMS[item], (item, nm)
    # an override reaches the rule: an impossible attack requirement removes the isolation
    assert BA.DETECTORS["isolation"](scene("iso", 1))
    assert BA.DETECTORS["isolation"](scene("iso", 1), catch_drive_exclusion_s=99.0, attack_def_m=0.0,
                                     attack_after_s=-99.0, attack_before_s=-99.0) == []
    note = BA.DOC["items"][[it["id"] for it in BA.DOC["items"]].index("lob_pass")]["params"]["max_conf_xy"]
    assert "multiplier" in str(note.get("note", "")), note


def test_loop1_t18_edge_events_are_tagged():
    """BA-T18: an event with conf 0 at a track segment edge carries attrs.edge_status = 'edge'."""
    n_edge = 0
    for name in ("hold", "pass_cs", "wing_catch"):
        for item, fn in BA.DETECTORS.items():
            for e in fn(scene(name, 1)):
                if e.attrs.get("edge_status") == "edge":
                    n_edge += 1
                    assert e.conf == 0.0
    assert n_edge > 0  # touches at the clip start


def test_changes_loop1_recorded_in_yaml():
    ids = {c["id"] for c in BA.DOC["changes_loop1"]}
    for i in range(1, 19):
        assert any(x.startswith(f"BA-T{i}") for x in ids), f"BA-T{i} missing from changes_loop1"
    for c in BA.DOC["changes_loop1"]:
        assert {"id", "what", "why", "evidence"} <= set(c), c


# --------------------------------------------------------------------------------------
# changes_loop2 regression tests (loop-2 confirmer failures; see changes_loop2 in the YAML). Each fixed-seed
# test uses seeds on which the loop-1 code (0.1.1) failed.
# --------------------------------------------------------------------------------------
def _near(e, t0_s):
    return abs(e.t0 * DT - t0_s) <= TOL_S + 1e-9


@pytest.mark.parametrize("seed", (3, 5))
def test_loop2_t10b_onball_defender_is_not_a_turnover(seed):
    """BA-T10b: at sigma 0.5 a tight on-ball defender decoded as the holder for the last 0.5 s (trailing
    segment at the clip end) is contact, not a strip."""
    sc = scene("l1_tight_onball", seed, 0.5)
    assert not BA.DETECTORS["live_ball_turnover"](sc)
    assert [s.pid for s in BA._model(sc).segs] == ["A"]
    assert any(c[0] == "DA" for c in BA._model(sc).contacts)


@pytest.mark.parametrize("seed", (3, 5, 7, 10))
def test_loop2_t10b_closeout_at_catch_is_the_receivers_shot(seed):
    """BA-T10b: the closeout defender on the ball at E's catch (and DA in contact on the drive) does not take
    possession: the shot is E's and there is no turnover."""
    sc = scene("l2_drive_kick_mid", seed, 0.5)
    assert [e.actors["shooter"] for e in BA.DETECTORS["shot_release"](sc)] == ["E"]
    assert not BA.DETECTORS["live_ball_turnover"](sc)
    assert not BA.DETECTORS["pass_incomplete"](sc)


@pytest.mark.parametrize("sigma", (0.3, 0.5))
def test_loop2_t10b_real_interception_is_kept(sigma):
    """BA-T10b guard: the possession prior does not touch a real interception (the defender runs away with
    the ball, no offensive player stays on it)."""
    for seed in SEEDS:
        evs = BA.DETECTORS["live_ball_turnover"](scene("l2_skip_intercepted", seed, sigma))
        assert any(e.actors == {"lost_by": "A", "gained_by": "D"} for e in evs), evs


@pytest.mark.parametrize("seed", (1, 3, 5, 6, 9))
def test_loop2_t9b_airball_at_high_noise(seed):
    """BA-T9b: the airball class holds at sigma 0.5 (noise-aware direction / r_min / pass-through bounds)."""
    sc = scene("l1_airball", seed, 0.5)
    shots = BA.DETECTORS["shot_release"](sc)
    assert any(e.actors["shooter"] == "A" and e.attrs["airball"] for e in shots), shots
    assert not BA.DETECTORS["pass_incomplete"](sc)
    assert not BA.DETECTORS["live_ball_turnover"](sc)


@pytest.mark.parametrize("seed", (1, 5, 10))
def test_loop2_t14b_drive_onset_after_slow_ramp(seed):
    """BA-T14b: a transition push that ramps up slowly from rest at 1.0 s is not dated 0.3 s late at sigma 0.2."""
    evs = BA.DETECTORS["drive"](scene("l2_transition_push", seed, 0.2))
    assert any(_near(e, 1.0) for e in evs), [round(e.t0 * DT, 2) for e in evs]


@pytest.mark.parametrize("seed", (1, 2, 3, 7, 9, 10))
def test_loop2_t14b_approach_end_time_at_high_noise(seed):
    """BA-T14b: drive_depth / drive_outcome are dated at the end of the approach (2.15 s), not 0.3-0.4 s late,
    at sigma 0.5; the geometric end (depth class position) is unchanged."""
    sc = scene("l1_slot_kick", seed, 0.5)
    dd = BA.DETECTORS["drive_depth"](sc)
    do = BA.DETECTORS["drive_outcome"](sc)
    assert any(_near(e, 2.15) for e in dd), [round(e.t0 * DT, 2) for e in dd]
    assert any(_near(e, 2.15) for e in do), [round(e.t0 * DT, 2) for e in do]
    for d in BA._drives(sc):
        assert d.t0 <= d.te <= d.t1


@pytest.mark.parametrize("sigma,seeds", [(0.2, (3, 5, 6, 9)), (0.3, (2, 5, 6, 9, 10))])
def test_loop2_t4b_tie_up_onset(sigma, seeds):
    """BA-T4b: the tie-up starts where both players come to rest on the ball (truth 2.0 s), not where the
    noisy distance run crosses the margin."""
    for seed in seeds:
        evs = BA.DETECTORS["contested_ball"](scene("l2_drive_tieup", seed, sigma))
        assert any(_near(e, 2.0) for e in evs), (seed, [round(e.t0 * DT, 2) for e in evs])


def test_loop2_t4b_tight_onball_still_negative_at_low_noise():
    """BA-T4b guard: the rest onset does not create contested events on ordinary on-ball defence."""
    for seed in range(1, 6):
        assert not BA.DETECTORS["contested_ball"](scene("l1_tight_onball", seed, 0.2))


@pytest.mark.parametrize("seed", (2, 4, 6, 9))
def test_loop2_t11b_dho_handoff_at_high_noise(seed):
    """BA-T11b: at sigma 0.5 the DHO is an exchange at the closest approach: no pass, and B's drive starts at
    the handoff (1.2 s)."""
    sc = scene("l1_dho", seed, 0.5)
    assert not [e for e in BA.DETECTORS["pass"](sc) if e.actors["passer"] == "A"]
    assert any(e.actors["driver"] == "B" and _near(e, 1.2) for e in BA.DETECTORS["drive"](sc))
    touch_b = [e for e in BA.DETECTORS["touch"](sc) if e.actors["holder"] == "B"]
    assert touch_b and touch_b[0].attrs["start_kind"] == "handoff"


@pytest.mark.parametrize("sigma,seed", [(0.3, 10), (0.5, 10)])
def test_loop2_t3b_deflection_with_adjacent_recovery(sigma, seed):
    """BA-T3b: a deflection whose recoverer's control starts right after the deflector's is contact."""
    assert not BA.DETECTORS["live_ball_turnover"](scene("l1_deflect", seed, sigma))


@pytest.mark.parametrize("seed", (1, 6, 7, 9))
def test_loop2_t18b_rim_finish_release_conf(seed):
    """T18b: a rim-finish shot release takes the shooter's edge factor, so its conf is not 0 next to the
    ball track's end at the rim."""
    rel = [e for e in BA.DETECTORS["release"](scene("l1_layup", seed)) if e.attrs["release_kind"] == "shot"]
    assert rel and all(e.conf > 0.0 for e in rel), [(e.conf, e.attrs.get("edge_status")) for e in rel]


def test_loop2_t6b_post_up_defense_position_alternatives():
    """BA-T6b: post_up carries the defence-position probabilities (point label unchanged)."""
    n = 0
    for seed in SEEDS:
        for e in BA.DETECTORS["post_up"](scene("l1_post_spin", seed)):
            alt = e.attrs["defense_position_alternatives"]
            assert set(alt) == {"behind", "front", "three_quarter"}
            assert abs(sum(alt.values()) - 1.0) <= 0.01
            assert e.attrs["defense_position_status"] in ("ok", "unresolved")
            n += 1
    assert n > 0


def test_loop2_isolation_not_at_clip_start():
    """BA-T10b follow-up: no isolation window starts within touch.clip_start_s of the clip start (no screen
    lookback)."""
    lim = BA._frames(BA.PARAMS["touch"]["clip_start_s"])
    for name, sigma in [("l1_slot_kick", 0.5), ("iso", 0.3), ("l1_layup", 0.5)]:
        for seed in range(1, 6):
            assert all(e.t0 >= lim for e in BA.DETECTORS["isolation"](scene(name, seed, sigma)))


def test_loop2_params_are_yaml_params():
    expect = {"touch": ["possession_prior_frac"], "shot_release": ["airball_noise_k"],
              "drive": ["onset_s2_lag_s", "onset_lag_vr_mps", "onset_s2_lag_sigma_max_m", "end_vr_sigma_ref_m",
                        "end_vr_sigma_slope"],
              "contested_ball": ["onset_still_mps", "onset_still_s", "onset_search_s"],
              "post_up": ["unresolved_margin"]}
    for item, names in expect.items():
        for nm in names:
            assert nm in BA.PARAMS[item], (item, nm)
    # an override reaches the rule: an impossible prior keeps the defender's segment
    sc = scene("l1_tight_onball", 3, 0.5)
    assert [s.pid for s in BA._model(sc).segs] == ["A"]
    assert "DA" in [s.pid for s in BA._model(sc, possession_prior_frac=1.01).segs]


def test_changes_loop2_recorded_in_yaml():
    ids = {c["id"] for c in BA.DOC["changes_loop2"]}
    for tag in ("BA-T10b", "BA-T4b", "BA-T11b", "BA-T14b", "BA-T9b", "BA-T3b", "BA-T6b", "T18b"):
        assert any(x.startswith(tag) for x in ids), f"{tag} missing from changes_loop2"
    for c in BA.DOC["changes_loop2"]:
        assert {"id", "what", "why", "evidence"} <= set(c), c


# --------------------------------------------------------------------------------------
# changes_loop3 regression tests (pass-2 confirmer items and the confirm2 adversarial probes; see
# changes_loop3 in the YAML). Fixed seeds fail on the 0.1.2 (loop-2) code unless noted.
# --------------------------------------------------------------------------------------
def _steal(sc, t0_s):
    return [e for e in BA.DETECTORS["live_ball_turnover"](sc)
            if e.actors == {"lost_by": "A", "gained_by": "D"} and _near(e, t0_s)]


@pytest.mark.parametrize("sigma,seeds", [(0.2, (1, 2, 3)), (0.3, (1, 2, 3)), (0.5, (1, 3, 4))])
def test_loop3_t10c_strip_with_quick_outlet_is_a_steal(sigma, seeds):
    """BA-T10c: a strip where the victim stays within the exit radius is a steal when the stealer's next
    control is a defence teammate's (the outlet), not offensive contact absorbed by the possession prior."""
    for seed in seeds:
        sc = scene("l3_strip_outlet", seed, sigma)
        assert _steal(sc, 1.5), (seed, [(e.actors, round(e.t0 * DT, 2)) for e in
                                        BA.DETECTORS["live_ball_turnover"](sc)])
        assert "D" in [s.pid for s in BA._model(sc).segs]


@pytest.mark.parametrize("sigma,seeds", [(0.2, (2, 3, 4)), (0.3, (2, 3, 6)), (0.5, (2, 6, 7))])
def test_loop3_t10c_pick_pocket_chased_upcourt_is_a_steal(sigma, seeds):
    """BA-T10c: a pick-pocket with the victim chasing ~0.8 m behind to the clip end is a steal: the ball goes
    >= possession_prior_upcourt_m away from the attacked rim over the defender's segment."""
    for seed in seeds:
        sc = scene("l3_strip_chased", seed, sigma)
        assert [e for e in BA.DETECTORS["live_ball_turnover"](sc) if e.actors["gained_by"] == "D"], seed
        assert BA._model(sc).segs[-1].pid == "D"


def test_loop3_t10c_upcourt_guard_is_a_yaml_param():
    """BA-T10c: the up-court guard is a YAML param that reaches the rule (an impossible bound restores the
    loop-2 behaviour on the chased pick-pocket)."""
    assert "possession_prior_upcourt_m" in BA.PARAMS["touch"]
    sc = scene("l3_strip_chased", 2, 0.3)
    assert BA._model(sc).segs[-1].pid == "D"
    assert BA._model(sc, possession_prior_upcourt_m=99.0).segs[-1].pid == "A"


def test_loop3_t10c_closeout_before_an_airball_stays_contact():
    """BA-T10c guard: the next-control-is-defence exemption does not apply when the ball leaves the defence
    segment at the attacked rim (a closeout on the shooter followed by an airball to a defender). Passes on
    0.1.2; fails with the exemption alone (the confirmer's one-line form)."""
    sc = scene("l1_airball", 5, 0.5)
    assert not BA.DETECTORS["live_ball_turnover"](sc)
    assert [e.actors["shooter"] for e in BA.DETECTORS["shot_release"](sc)] == ["A"]
    assert any(e.actors["rebounder"] == "D2" for e in BA.DETECTORS["rebound_control"](sc))


def test_loop3_t3c_deflection_confirmed_after_the_prior():
    """BA-T3c: the team-change confirmation runs again after the possession prior: a short defence segment
    after the deflector's that the prior hands to the recoverer leaves an A-D-B triplet whose D segment is
    the deflection (slow receding ball), not an interception plus a recovery."""
    sc = scene("l1_deflect", 3, 0.5)
    assert not BA.DETECTORS["live_ball_turnover"](sc)
    assert "D" not in [s.pid for s in BA._model(sc).segs]


@pytest.mark.parametrize("name,sigma,seeds", [("l3_arc_attack", 0.5, (5, 8, 10)),
                                              ("l3_dribble_reversal", 0.3, (4,)),
                                              ("l3_dribble_reversal", 0.5, (5,))])
def test_loop3_i1_noise_aware_isolation_gates(name, sigma, seeds):
    """BA-I1: no isolation from a teammate read past teammate_min_m by noise (S03) or from a dribble reversal
    whose noisy r minimum fakes a 1.0 m gain toward the rim (S26; sigma 0.5 seed 5 fails with teammate_noise_k
    alone, which moves the window past the clip-start drop)."""
    for seed in seeds:
        assert not BA.DETECTORS["isolation"](scene(name, seed, sigma)), seed


def test_loop3_i1_true_isolation_kept_at_high_noise():
    """BA-I1 guard: the clear-out isolation is still found at sigma 0.5."""
    for seed in (1, 2, 3):
        evs = BA.DETECTORS["isolation"](scene("l3_iso_clear", seed, 0.5))
        assert any(e.actors["handler"] == "A" for e in evs), seed


@pytest.mark.parametrize("seed", (1, 10))
def test_loop3_t14c_drive_onset_after_long_rest(seed):
    """BA-T14c: after 2.6 s at rest the onset lag allowance does not run on noise (drive at 3.5 s, was 3.17)."""
    evs = [e for e in BA.DETECTORS["drive"](scene("l3_iso_clear", seed)) if e.actors["driver"] == "A"]
    assert any(_near(e, 3.5) for e in evs), [round(e.t0 * DT, 2) for e in evs]


def test_loop3_t4c_contested_noise_status():
    """BA-T4c: contested_ball says when it is noise-limited (sigma_p 0.5 tier), and not at sigma 0.2."""
    lo = [e for seed in (1, 2) for e in BA.DETECTORS["contested_ball"](scene("l2_drive_tieup", seed, 0.2))]
    hi = [e for seed in (1, 2, 4) for e in BA.DETECTORS["contested_ball"](scene("l2_drive_tieup", seed, 0.5))]
    assert lo and all(e.attrs["noise_status"] == "ok" for e in lo)
    assert hi and all(e.attrs["noise_status"] == "noise_limited" for e in hi)
    assert all(e.attrs["pair_sigma_m"] > BA.PARAMS["contested_ball"]["noise_limited_pair_sigma_m"] for e in hi)


def test_loop3_params_are_yaml_params():
    expect = {"touch": ["possession_prior_upcourt_m"], "contested_ball": ["noise_limited_pair_sigma_m"],
              "isolation": ["teammate_noise_k", "attack_gain_noise_k"]}
    for item, names in expect.items():
        for nm in names:
            assert nm in BA.PARAMS[item], (item, nm)
    assert BA.PARAMS["drive"]["onset_lag_vr_mps"] == -0.2
    # an override reaches the rule: k = 0 restores the S03 false isolation
    assert BA.DETECTORS["isolation"](scene("l3_arc_attack", 5, 0.5), teammate_noise_k=0.0, attack_gain_noise_k=0.0)


def test_changes_loop3_recorded_in_yaml():
    ids = {c["id"] for c in BA.DOC["changes_loop3"]}
    for tag in ("BA-T10c", "BA-T3c", "BA-I1", "BA-T14c", "BA-T4c"):
        assert any(x.startswith(tag) for x in ids), f"{tag} missing from changes_loop3"
    for c in BA.DOC["changes_loop3"]:
        assert {"id", "what", "why", "evidence"} <= set(c), c


# --------------------------------------------------------------------------------------
# changes_loop4 regression tests (real SportVU failure modes rebuilt as synthetic scenes; no real data here;
# see changes_loop4 in the YAML). Each fails on the 0.1.3 (loop-3) code unless noted.
# --------------------------------------------------------------------------------------
FAR = BA.spotlib.C["FAR_END_Y"] - BA.spotlib.C["RIM_Y_FROM_END"]  # the far basket in the scene frame
FAR_RIM = {"team": "X", "wp": _still(0.0, FAR)}  # 'spot*' actors are pseudo actors (dropped)


def _far_set(dur=4.0):
    """5-on-5 half-court set at the FAR basket: the D list attacks it, the O list defends goal-side."""
    return {
        "DA": {"team": "D", "wp": _still(5.0, FAR - 4.5, dur)},
        "D2": {"team": "D", "wp": _still(-6.0, FAR - 3.0, dur)},
        "D3": {"team": "D", "wp": _still(0.0, FAR - 7.5, dur)},
        "D4": {"team": "D", "wp": _still(-2.5, FAR - 1.0, dur)},
        "D5": {"team": "D", "wp": _still(6.5, FAR - 0.5, dur)},
        "OA": {"team": "O", "wp": _still(4.4, FAR - 3.8, dur)},
        "O2": {"team": "O", "wp": _still(-5.3, FAR - 2.45, dur)},
        "O3": {"team": "O", "wp": _still(0.0, FAR - 6.4, dur)},
        "O4": {"team": "O", "wp": [(0.0, -1.8, FAR - 0.55), (2.0, -1.8, FAR - 0.55), (2.6, -0.9, FAR - 0.7),
                                   (dur, -0.9, FAR - 0.7)]},
        "O5": {"team": "O", "wp": _still(5.6, FAR - 0.25, dur)},
    }


def _origin_set(dur=4.0):
    """5-on-5 half-court set at the origin basket (O list attacks it), defenders goal-side."""
    return {
        "A": {"team": "O", "wp": _still(4.6, 4.6, dur)},
        "B": {"team": "O", "wp": _still(-6.0, 3.0, dur)},
        "C": {"team": "O", "wp": _still(0.0, 8.0, dur)},
        "E": {"team": "O", "wp": _still(-2.6, 1.2, dur)},
        "F": {"team": "O", "wp": _still(6.8, 0.6, dur)},
        "DA": {"team": "D", "wp": _still(3.9, 3.9, dur)},
        "DB": {"team": "D", "wp": _still(-5.1, 2.6, dur)},
        "DC": {"team": "D", "wp": _still(0.0, 6.9, dur)},
        "DE": {"team": "D", "wp": _still(-1.9, 0.9, dur)},
        "DF": {"team": "D", "wp": _still(5.8, 0.5, dur)},
    }


def _with(base, **over):
    out = dict(base)
    out.update(over)
    return out


def _swap_teams(actors):
    return {k: dict(v, team={"O": "D", "D": "O"}.get(v["team"], v["team"])) for k, v in actors.items()}


SCENARIOS.update({
    # BA-R4b: a jumper by the D list at the far basket (a clock-running clip holds both teams' possessions).
    "l4_far_jumper": dict(dur=4.0, spec={"actors": _with(_far_set(), spotF=FAR_RIM),
                                         "ball": {"held": [(0.0, 1.5, "DA"), (2.8, 4.0, "O4")],
                                                  "flights": [(1.5, 2.4, "DA", "spotF"), (2.4, 2.8, "spotF", "O4")]}}),
    # BA-R4b: the same clip with the lists swapped: the O list attacks the far basket (the loader's offence
    # list is the team nearest the ball most often, which need not attack the origin rim).
    "l4_far_jumper_swapped": dict(dur=4.0, spec={"actors": _swap_teams(_with(_far_set(), spotF=FAR_RIM)),
                                                 "ball": {"held": [(0.0, 1.5, "DA"), (2.8, 4.0, "O4")],
                                                          "flights": [(1.5, 2.4, "DA", "spotF"),
                                                                      (2.4, 2.8, "spotF", "O4")]}}),
    # BA-R4h: the far-basket team passes DA -> D2 with its O-list defender 0.9 m goal-side of the receiver.
    "l4_far_pass_tight": dict(dur=4.0, spec={"actors": _far_set(),
                                             "ball": {"held": [(0.0, 1.5, "DA"), (2.1, 4.0, "D2")],
                                                      "flights": [(1.5, 2.1, "DA", "D2")]}}),
    # BA-R4c: wing jumper off the rim; the shooter's teammate E gathers it 1.25 m from the rim 0.5 s after the rim frame (a slow bounce).
    "l4_teammate_rebound": dict(dur=4.0, spec={"actors": _with(
        _origin_set(), E={"team": "O", "wp": [(0.0, -2.6, 1.2), (2.0, -2.6, 1.2), (2.6, -1.0, 0.75), (4.0, -1.0, 0.75)]},
        rim=RIM),
        "ball": {"held": [(0.0, 1.5, "A"), (2.9, 4.0, "E")],
                 "flights": [(1.5, 2.4, "A", "rim"), (2.4, 2.9, "rim", "E")]}}),
    # BA-R4d: defender DE stands 0.7 m in front of the rim on the shot line; the ball flies over him to the rim
    # (it enters his 1.0 m control radius before it reaches the rim) and he takes the rebound.
    "l4_rebounder_on_line": dict(dur=4.0, spec={"actors": _with(
        _origin_set(), DE={"team": "D", "wp": _still(0.5, 0.5)}, rim=RIM),
        "ball": {"held": [(0.0, 1.5, "A"), (2.6, 4.0, "DE")],
                 "flights": [(1.5, 2.4, "A", "rim"), (2.4, 2.6, "rim", "DE")]}}),
    # BA-R4f: A's jumper is tipped by teammate E under the rim (0.4 s touch) and DE secures the ball.
    "l4_scramble": dict(dur=4.5, spec={"actors": _with(
        _origin_set(4.5), E={"team": "O", "wp": _still(-1.3, 1.0, 4.5)},
        DE={"team": "D", "wp": _still(-2.8, 2.9, 4.5)}, rim=RIM),
        "ball": {"held": [(0.0, 1.5, "A"), (2.9, 3.3, "E"), (3.7, 4.5, "DE")],
                 "flights": [(1.5, 2.4, "A", "rim"), (2.4, 2.9, "rim", "E"), (3.3, 3.7, "E", "DE")]}}),
    # BA-R4i guard (a) (confirm3 N03): on-ball DA glued 0.39 m to A; A's pass is intercepted by D2.
    "l4_glued_then_intercepted": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 5.0)},
        "DA": {"team": "D", "wp": _still(5.7, 4.75)},
        "B": {"team": "O", "wp": _still(0.0, 8.0)},
        "D2": {"team": "D", "wp": [(0.0, 3.0, 6.5), (1.85, 3.0, 6.5), (4.0, 3.5, 12.0)]}},
        "ball": {"held": [(0.0, 1.6, "A"), (1.85, 4.0, "D2")], "flights": [(1.6, 1.85, "A", "D2")]}}),
    # BA-R4i guard (b) (confirm3 N05b): A backs out 5 m under tight pressure; no change of possession.
    "l4_retreat_tight": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": [(0.0, 4.0, 4.5), (1.0, 4.0, 4.5), (2.2, 4.5, 9.5), (4.0, 4.5, 9.5)]},
        "DA": {"team": "D", "wp": [(0.0, 3.85, 4.3), (1.0, 3.85, 4.3), (2.2, 4.35, 9.3), (4.0, 4.35, 9.3)]},
        "B": {"team": "O", "wp": _still(-5.0, 4.0)},
        "DB": {"team": "D", "wp": _still(-4.3, 3.4)}},
        "ball": {"held": [(0.0, 4.0, "A")]}}),
})


@pytest.mark.parametrize("name,sigma,seed", [("l4_far_jumper", 0.2, 1), ("l4_far_jumper", 0.3, 2),
                                              ("l4_far_jumper", 0.5, 3), ("l4_far_jumper_swapped", 0.2, 1),
                                              ("l4_far_jumper_swapped", 0.3, 2), ("l4_far_jumper_swapped", 0.5, 3)])
def test_loop4_r4b_far_basket_jumper(name, sigma, seed):
    """BA-R4b: the goal-side vote gives DA's team the far basket whichever list it is on; its jumper is a shot
    at that basket (release_r from the far rim, attrs.basket 'far') and O4's gather is a defensive rebound.
    The loop-3 code measured every shot against the origin rim and missed it."""
    sc = scene(name, seed, sigma)
    da_off = "DA" in sc.offense
    assert BA._team_rims(sc)[da_off] == (0.0, FAR) and BA._team_rims(sc)[not da_off] == (0.0, 0.0)
    shots = [e for e in BA.DETECTORS["shot_release"](sc) if e.actors["shooter"] == "DA"]
    assert shots and _near(shots[0], 1.5), [(e.actors, round(e.t0 * DT, 2)) for e in shots]
    assert shots[0].attrs["basket"] == "far" and abs(shots[0].attrs["release_r"] - 6.7) <= 1.0
    rebs = BA.DETECTORS["rebound_control"](sc)
    assert any(e.actors["rebounder"] == "O4" and e.attrs["label"] == "defensive" for e in rebs)


def test_loop4_r4b_vote_needs_full_teams():
    """BA-R4b guard: with 2-3 players per side the default (offence list -> origin) holds."""
    for name in ("rebound_outlet", "l4_glued_then_intercepted"):
        assert BA._team_rims(scene(name, 1, 0.5)) == {True: (0.0, 0.0), False: (0.0, FAR)}, name


@pytest.mark.parametrize("sigma,seed", [(0.2, 1), (0.3, 2), (0.5, 3), (0.5, 4)])
def test_loop4_r4h_far_team_pass_stays_with_the_far_team(sigma, seed):
    """BA-R4h: in the far-basket team's frontcourt the possession prior favours that team: DA -> D2 is DA's pass
    to D2 (the loop-3 prior handed both controls to their goal-side O-list defenders, OA -> O2), with no
    turnover or incomplete pass."""
    sc = scene("l4_far_pass_tight", seed, sigma)
    assert [s.pid for s in BA._model(sc).segs] == ["DA", "D2"]
    assert any(e.actors.get("passer") == "DA" and e.actors.get("receiver") == "D2" for e in BA.DETECTORS["pass"](sc))
    assert not BA.DETECTORS["live_ball_turnover"](sc)
    assert not BA.DETECTORS["pass_incomplete"](sc)


@pytest.mark.parametrize("sigma,seed", [(0.2, 1), (0.3, 2), (0.5, 2)])
def test_loop4_r4c_teammate_rebound_is_not_an_alley_oop(sigma, seed):
    """BA-R4c: a teammate who gathers the miss 0.5 s after the rim frame (his 1.0 m control run starts ~0.1 s after it) took an offensive rebound; the shot is
    kept (the loop-3 alley-oop guard dropped it: his control starts inside oop_window_s at r <= 1.5 m). Seeds
    1-10 pass 10 / 10 / 8 at sigma 0.2 / 0.3 / 0.5 (0.1.3: 1 / 2 / 3)."""
    sc = scene("l4_teammate_rebound", seed, sigma)
    shots = [e for e in BA.DETECTORS["shot_release"](sc) if e.actors["shooter"] == "A"]
    assert shots and _near(shots[0], 1.5)
    assert any(e.actors["rebounder"] == "E" and e.attrs["label"] == "offensive"
               for e in BA.DETECTORS["rebound_control"](sc))


@pytest.mark.parametrize("sigma,seed", [(0.2, 1), (0.3, 2), (0.5, 1), (0.5, 4)])
def test_loop4_r4d_rebounder_on_the_shot_line(sigma, seed):
    """BA-R4d: the rim-reach search follows the ball into the rebounder's control while it keeps flight speed.
    Seeds 1-10 pass 10 / 9 / 7 at sigma 0.2 / 0.3 / 0.5 (0.1.3: 0 / 0 / 1); at 0.5 the smoothed speed near
    the rim sometimes drops below flight speed first."""
    sc = scene("l4_rebounder_on_line", seed, sigma)
    shots = [e for e in BA.DETECTORS["shot_release"](sc) if e.actors["shooter"] == "A"]
    assert shots and _near(shots[0], 1.5)
    assert not BA.DETECTORS["live_ball_turnover"](sc)
    assert any(e.actors["rebounder"] == "DE" for e in BA.DETECTORS["rebound_control"](sc))


@pytest.mark.parametrize("sigma,seed", [(0.2, 1), (0.3, 2), (0.5, 1), (0.5, 3)])
def test_loop4_r4f_scramble_touch_is_not_a_turnover(sigma, seed):
    """BA-R4f: losing a short tip touch under the rim to the defence is a rebound battle, not a live-ball
    turnover, and the tip is not an incomplete pass. Seeds 1-10 pass 10 / 8 / 8 (0.1.3: 0 / 0 / 0); the
    failures decode E's touch past secure_min_s."""
    sc = scene("l4_scramble", seed, sigma)
    assert [e.actors["shooter"] for e in BA.DETECTORS["shot_release"](sc)][:1] == ["A"]
    assert not BA.DETECTORS["live_ball_turnover"](sc)
    assert not BA.DETECTORS["pass_incomplete"](sc)


def test_loop4_r4f_real_steal_kept():
    """BA-R4f guard: a strip with no shot before it is still a steal."""
    assert _steal(scene("l3_strip_outlet", 1, 0.3), 1.5)


@pytest.mark.parametrize("sigma,seed", [(0.3, 1), (0.5, 1), (0.5, 4)])
def test_loop4_r4i_glued_defender_then_interception(sigma, seed):
    """BA-R4i guard (a) (loop-3 open item): the on-ball defender's contact segment before an intercepted pass
    stays contact; the interception by D2 is found (0.5 seed 4 fails on 0.1.3). The confirmer's harness
    (N03, mirrored, 20 runs) reads 18 / 18 / 15 found at 0.2 / 0.3 / 0.5 (0.1.3: 18 / 18 / 12)."""
    sc = scene("l4_glued_then_intercepted", seed, sigma)
    lbt = BA.DETECTORS["live_ball_turnover"](sc)
    assert [e.actors for e in lbt] == [{"lost_by": "A", "gained_by": "D2"}], [(e.actors, e.t0) for e in lbt]
    if sigma < 0.5:  # at 0.5 the release can decode as a short loose phase (loose_recovery, no pass item)
        assert any(e.actors["defender"] == "D2" for e in BA.DETECTORS["pass_incomplete"](sc))


@pytest.mark.parametrize("sigma,seed", [(0.2, 9), (0.3, 8), (0.5, 3), (0.5, 10)])
def test_loop4_r4i_back_out_dribble_is_not_a_strip(sigma, seed):
    """BA-R4i guard (b) (loop-3 open item): a 5 m back-out dribble with the defender glued rim-side gives no
    strip / re-strip pair (each listed seed gives one on 0.1.3)."""
    assert not BA.DETECTORS["live_ball_turnover"](scene("l4_retreat_tight", seed, sigma))


def test_loop4_params_are_yaml_params():
    expect = {"touch": ["rim_goalside_min_s", "rim_goalside_min_players", "possession_prior_frontcourt_r_m",
                        "possession_prior_lead_m", "possession_prior_lead_s"],
              "shot_release": ["oop_catch_lag_s", "rim_reach_ext_s"],
              "rebound_control": ["scramble_window_s", "secure_min_s"]}
    for item, names in expect.items():
        for nm in names:
            assert nm in BA.PARAMS[item], (item, nm)
    # an override reaches the rule: no lag allowance restores the alley-oop reading of the teammate rebound
    sc = scene("l4_teammate_rebound", 1, 0.2)
    assert not [e for e in BA.DETECTORS["shot_release"](sc, oop_catch_lag_s=1.0) if e.actors["shooter"] == "A"]


def test_changes_loop4_recorded_in_yaml():
    ids = {c["id"] for c in BA.DOC["changes_loop4"]}
    for tag in ("BA-R4b", "BA-R4c", "BA-R4d", "BA-R4f", "BA-R4h", "BA-R4i"):
        assert any(x.startswith(tag) for x in ids), f"{tag} missing from changes_loop4"
    for c in BA.DOC["changes_loop4"]:
        assert {"id", "what", "why", "evidence"} <= set(c), c


# --------------------------------------------------------------------------------------
# changes_loop5: turnovers under the NCAA official-statistics rules (rule ba_turnover_rules, TO-* ids). Synthetic
# scenes only: the MSU gold turnover set and the SportVU play-by-play used for the audit stay private.
# Each check runs at sigma_p 0.2 / 0.3 / 0.5 on listed seeds; docstrings give seeds 1-10 pass counts.
# --------------------------------------------------------------------------------------
SCENARIOS.update({
    # TO-C1 (no control): the ball comes off the rim (no shot release in the clip) to A, who touches it 0.7 s and
    # loses it to D: a rebound battle after a rim visit -> abstention rim_visit_scramble, no live-ball turnover.
    "l5_rim_scramble": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(1.2, 1.0)},
        "B": {"team": "O", "wp": _still(-5.0, 4.0)},
        "D": {"team": "D", "wp": [(0.0, 3.6, 3.5), (1.2, 3.6, 3.5), (1.8, 3.0, 2.6), (3.5, 3.0, 2.6)]},
        "DB": {"team": "D", "wp": _still(-4.3, 3.5)},
        "spotR": {"team": "X", "wp": _still(0.0, 0.0)}},
        "ball": {"held": [(0.0, 0.4, "spotR"), (0.7, 1.4, "A"), (1.8, 3.5, "D")],
                 "flights": [(0.4, 0.7, "spotR", "A"), (1.4, 1.8, "A", "D")]}}),
    # TO-C1 (control assumed): the same rebound, A secures it for 1.9 s, then his pass is intercepted by D.
    "l5_rim_secured": dict(dur=4.2, spec={"actors": {
        "A": {"team": "O", "wp": _still(1.2, 1.0, 4.2)},
        "B": {"team": "O", "wp": _still(-5.0, 4.0, 4.2)},
        "D": {"team": "D", "wp": [(0.0, -2.0, 2.0), (2.2, -2.0, 2.0), (2.9, -2.2, 2.7), (4.2, -2.2, 2.7)]},
        "DB": {"team": "D", "wp": _still(-4.3, 3.5, 4.2)},
        "spotR": {"team": "X", "wp": _still(0.0, 0.0, 4.2)}},
        "ball": {"held": [(0.0, 0.4, "spotR"), (0.7, 2.6, "A"), (3.0, 4.2, "D")],
                 "flights": [(0.4, 0.7, "spotR", "A"), (2.6, 3.0, "A", "D")]}}),
    # TO-C2: D intercepts and the clip ends 0.3 s later (whistle / out of bounds?): not shown to be secured.
    "l5_dead_unsecured": dict(dur=2.25, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 5.0)},
        "B": {"team": "O", "wp": _still(-1.0, 8.5)},
        "D": {"team": "D", "wp": [(0.0, 3.5, 5.0), (1.2, 3.5, 5.0), (1.9, 2.6, 6.8), (3.5, 2.6, 6.8)]}},
        "ball": {"held": [(0.0, 1.5, "A"), (1.9, 2.25, "D")], "flights": [(1.5, 1.9, "A", "D")]}}),
    # TO-D1: a pass across the lane under the basket passes over the rim (XY) and D picks it up: try or pass off
    # the rim cannot be told apart without ball z -> abstention rim_visit.
    "l5_pass_over_rim": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(-4.0, 0.3)},
        "B": {"team": "O", "wp": _still(4.6, 0.5)},
        "D": {"team": "D", "wp": [(0.0, 2.6, 2.0), (1.0, 2.6, 2.0), (1.8, 2.5, 0.5), (3.5, 2.5, 0.5)]},
        "DA": {"team": "D", "wp": _still(-3.3, 0.9)}},
        "ball": {"held": [(0.0, 1.5, "A"), (2.0, 3.5, "D")], "flights": [(1.5, 2.0, "A", "D")]}}),
    # TO-D1 guard: the same pass 3.2 m up the lane, D moves into it: an interception (turnover + steal).
    "l5_pass_across_lane": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(-4.0, 3.3)},
        "B": {"team": "O", "wp": _still(4.6, 3.5)},
        "D": {"team": "D", "wp": [(0.0, 2.6, 5.2), (1.0, 2.6, 5.2), (1.8, 2.5, 3.5), (3.5, 2.5, 3.5)]},
        "DA": {"team": "D", "wp": _still(-3.3, 2.7)}},
        "ball": {"held": [(0.0, 1.5, "A"), (2.0, 3.5, "D")], "flights": [(1.5, 2.0, "A", "D")]}}),
    # TO-S1: overthrown pass straight to a defender standing still: turnover, no steal (SM 6 A.R.4(b)).
    "l5_errant_pass": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 5.0)},
        "B": {"team": "O", "wp": _still(-1.0, 8.5)},
        "D": {"team": "D", "wp": _still(2.6, 6.8)}},
        "ball": {"held": [(0.0, 1.5, "A"), (1.9, 3.5, "D")], "flights": [(1.5, 1.9, "A", "D")]}}),
    # TO-S1: D1 bats A's pass (0.3 s touch), the ball rolls loose and D2 recovers: steal to the deflector D1
    # (clean deflection, SM 6 A.R.5(a)); deflector and recoverer recorded separately.
    "l5_bat_to_teammate": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 4.0)},
        "B": {"team": "O", "wp": _still(0.0, 7.5)},
        "D1": {"team": "D", "wp": _still(4.0, 5.0)},
        "D2": {"team": "D", "wp": [(0.0, 0.5, 10.0), (1.4, 0.5, 10.0), (2.5, 3.4, 7.9), (4.0, 3.4, 7.9)]},
        "spotB": {"team": "X", "wp": _still(4.6, 6.4)},
        "spot": {"team": "X", "wp": _still(3.6, 7.6)}},
        "ball": {"held": [(0.0, 1.0, "A"), (2.4, 2.5, "spot"), (2.5, 4.0, "D2")],
                 "flights": [(1.0, 1.2, "A", "D1"), (1.2, 1.6, "D1", "spotB"), (1.6, 2.4, "spotB", "spot")]}}),
    # TO-S1: the pass flies past D1 with a slight tip (11 deg turn, full speed) and D2 cuts in to intercept: steal
    # to the recoverer D2 (SM 6 A.R.5(b)).
    "l5_slight_tip": dict(dur=3.5, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 4.0)},
        "B": {"team": "O", "wp": _still(-5.5, 8.3)},
        "D1": {"team": "D", "wp": _still(2.5, 5.7)},
        "D2": {"team": "D", "wp": [(0.0, -2.0, 9.5), (0.9, -2.0, 9.5), (1.75, -0.87, 7.47), (3.5, -0.87, 7.47)]},
        "spotT": {"team": "X", "wp": _still(2.5, 5.31)}},
        "ball": {"held": [(0.0, 1.0, "A"), (1.75, 3.5, "D2")],
                 "flights": [(1.0, 1.3, "A", "spotT"), (1.3, 1.75, "spotT", "D2")]}}),
    # TO-S1: D, 0.8 m from A, knocks the ball loose; it rolls to D2: steal to D (knocked loose, SM 6(c)).
    "l5_knocked_loose": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(4.0, 6.0)},
        "B": {"team": "O", "wp": _still(-5.0, 4.0)},
        "D": {"team": "D", "wp": _still(3.4, 5.5)},
        "D2": {"team": "D", "wp": [(0.0, 0.0, 9.5), (1.8, 0.0, 9.5), (2.9, 1.9, 8.5), (4.0, 1.9, 8.5)]},
        "spot": {"team": "X", "wp": _still(2.2, 8.3)}},
        "ball": {"held": [(0.0, 1.5, "A"), (2.7, 2.95, "spot"), (2.95, 4.0, "D2")],
                 "flights": [(1.5, 2.7, "A", "spot")]}}),
    # TO-S1: the same fumble with no defender near the ball: turnover, no steal (unforced, SM 6 A.R.7).
    "l5_fumble_unforced": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(4.0, 6.0)},
        "B": {"team": "O", "wp": _still(-5.0, 4.0)},
        "D": {"team": "D", "wp": _still(5.5, 3.2)},
        "D2": {"team": "D", "wp": [(0.0, 0.0, 9.5), (1.8, 0.0, 9.5), (2.9, 1.9, 8.5), (4.0, 1.9, 8.5)]},
        "spot": {"team": "X", "wp": _still(2.2, 8.3)}},
        "ball": {"held": [(0.0, 1.5, "A"), (2.7, 2.95, "spot"), (2.95, 4.0, "D2")],
                 "flights": [(1.5, 2.7, "A", "spot")]}}),
    # TO-K1: B muffs A's pass (0.35 s touch), the ball rolls to D: charged to the receiver B (SM 6 A.R.4(d)).
    "l5_muff": dict(dur=4.0, spec={"actors": {
        "A": {"team": "O", "wp": _still(6.0, 5.0)},
        "B": {"team": "O", "wp": _still(2.0, 7.5)},
        "D": {"team": "D", "wp": [(0.0, -1.0, 10.8), (1.8, -1.0, 10.8), (2.8, 0.6, 9.4), (4.0, 0.6, 9.4)]},
        "spot": {"team": "X", "wp": _still(0.9, 9.1)}},
        "ball": {"held": [(0.0, 1.0, "A"), (1.4, 1.75, "B"), (2.7, 2.85, "spot"), (2.85, 4.0, "D")],
                 "flights": [(1.0, 1.4, "A", "B"), (1.75, 2.7, "B", "spot")]}}),
    # TO-T1: sideline throw-in (T out of bounds) intercepted by D: turnover on the inbounder + steal (A.R.17(a)).
    "l5_throw_in_side": dict(dur=3.0, spec={"actors": {
        "T": {"team": "O", "wp": _still(8.3, 6.0)},
        "B": {"team": "O", "wp": _still(4.0, 8.0)},
        "D": {"team": "D", "wp": [(0.0, 5.0, 5.6), (0.7, 5.0, 5.6), (1.3, 5.9, 6.9), (3.0, 5.9, 6.9)]}},
        "ball": {"held": [(0.0, 1.0, "T"), (1.35, 3.0, "D")], "flights": [(1.0, 1.35, "T", "D")]}}),
    # TO-T1 + TO-D1: baseline throw-in whose path crosses the rim (XY): a throw-in is never a try, so the
    # interception is a turnover, not a rim_visit abstention.
    "l5_throw_in_baseline": dict(dur=3.0, spec={"actors": {
        "T": {"team": "O", "wp": _still(-0.3, -2.4)},
        "B": {"team": "O", "wp": _still(0.6, 3.8)},
        "D": {"team": "D", "wp": [(0.0, 1.6, 3.0), (0.7, 1.6, 3.0), (1.3, 0.4, 2.3), (3.0, 0.4, 2.3)]}},
        "ball": {"held": [(0.0, 1.0, "T"), (1.4, 3.0, "D")], "flights": [(1.0, 1.4, "T", "D")]}}),
    # TO-H1 guard: a tie-up on a rebound (nobody had control after the shot): no held-ball abstention.
    "l5_rebound_tieup": dict(dur=4.0, spec={"actors": {
        "S": {"team": "O", "wp": _still(5.0, 5.0)},
        "A": {"team": "O", "wp": [(0.0, 2.5, 3.0), (1.2, 2.5, 3.0), (1.8, 1.5, 1.15), (4.0, 1.5, 1.15)]},
        "D": {"team": "D", "wp": [(0.0, 0.5, 2.5), (1.2, 0.5, 2.5), (1.8, 1.5, 1.85), (4.0, 1.5, 1.85)]},
        "DS": {"team": "D", "wp": _still(4.3, 4.4)},
        "rim": RIM, "spot": {"team": "X", "wp": _still(1.5, 1.5)}},
        "ball": {"held": [(0.0, 0.5, "S"), (1.8, 4.0, "spot")],
                 "flights": [(0.5, 1.4, "S", "rim"), (1.4, 1.8, "rim", "spot")]}}),
})


def _lbt(sc, **kw):
    return BA.DETECTORS["live_ball_turnover"](sc, **kw)


def _abst(sc, reason=None):
    return [e for e in BA.DETECTORS["turnover_abstention"](sc) if reason is None or e.attrs["reason"] == reason]


def _fresh(name, seed, sigma):
    """An uncached scene (tests that set scene.game_clock must not touch the lru_cache'd scene)."""
    sc = SCENARIOS[name]
    _, tracks = sim.scenario(sc["spec"], sc["dur"], sigma, seed)
    return build_scene([t for t in tracks if t.oid != "rim" and not t.oid.startswith("spot")])


def _one(evs, **actors):
    return [e for e in evs if all(e.actors.get(k) == v for k, v in actors.items())]


def _chk_rim_scramble(sc):
    return not _lbt(sc) and bool(_one(_abst(sc, "rim_visit_scramble"), lost_by="A", gained_by="D"))


def _chk_rim_secured(sc):
    return bool(_one(_lbt(sc), lost_by="A", gained_by="D")) and not _abst(sc, "rim_visit_scramble")


def _chk_dead_unsecured(sc):
    return not _lbt(sc) and bool(_one(_abst(sc, "dead_before_secured"), lost_by="A", gained_by="D"))


def _chk_pass_over_rim(sc):
    return not _lbt(sc) and bool(_one(_abst(sc, "rim_visit"), lost_by="A", gained_by="D"))


def _chk_pass_across_lane(sc):
    e = _one(_lbt(sc), lost_by="A", gained_by="D")
    return bool(e) and e[0].attrs["steal_to"] == "D" and not _abst(sc)


def _chk_errant_pass(sc):
    e = _one(_lbt(sc), lost_by="A", gained_by="D")
    return bool(e) and e[0].attrs["steal_to"] is None and e[0].attrs["steal_basis"] == "errant_pass_no_steal"


def _chk_interception_steal(sc):
    e = _one(_lbt(sc), lost_by="A", gained_by="D")
    return bool(e) and e[0].attrs["steal_to"] == "D" and e[0].attrs["steal_basis"] == "interception"


def _chk_bat_to_teammate(sc):
    e = _one(_lbt(sc), lost_by="A", gained_by="D2")
    return bool(e) and e[0].attrs["deflector"] == "D1" and e[0].attrs["recoverer"] == "D2" \
        and e[0].attrs["steal_to"] == "D1" and len(_lbt(sc)) == 1


def _chk_slight_tip(sc):
    e = _one(_lbt(sc), lost_by="A", gained_by="D2")
    return bool(e) and e[0].attrs["steal_to"] == "D2" and len(_lbt(sc)) == 1


def _chk_knocked_loose(sc):
    e = _one(_lbt(sc), lost_by="A", gained_by="D2")
    return bool(e) and e[0].attrs["deflector"] == "D" and e[0].attrs["steal_to"] == "D"


def _chk_fumble_unforced(sc):
    e = _one(_lbt(sc), lost_by="A", gained_by="D2")
    return bool(e) and e[0].attrs["steal_to"] is None and e[0].attrs["steal_basis"] == "unforced_no_steal"


def _chk_muff(sc):
    e = _one(_lbt(sc), lost_by="B", gained_by="D")
    return bool(e) and e[0].attrs["charged_to"] == "B" and e[0].attrs["charged_basis"] == "receiver_muff" \
        and e[0].attrs["alt_charged"] == "A"


def _chk_strip_take_away(sc):
    e = _one(_lbt(sc), lost_by="A", gained_by="D")
    return bool(e) and e[0].attrs["steal_to"] == "D" and e[0].attrs["steal_basis"] == "take_away" \
        and e[0].attrs["charged_to"] == "A"


def _chk_throw_in(sc):
    e = _one(_lbt(sc), lost_by="T", gained_by="D")
    return bool(e) and e[0].attrs["throw_in"] is True and e[0].attrs["steal_to"] == "D" and not _abst(sc)


def _chk_held_ball(sc):
    return bool(_one(_abst(sc, "held_ball_arrow"), lost_by="A", gained_by="D")) and not _lbt(sc)


def _chk_rebound_tieup(sc):
    return not _abst(sc, "held_ball_arrow") and not _lbt(sc)


def _chk_no_turnover_deflection(sc):
    return not _lbt(sc) and not _abst(sc)


L5_CHECKS = {
    "l5_rim_scramble": _chk_rim_scramble, "l5_rim_secured": _chk_rim_secured,
    "l5_dead_unsecured": _chk_dead_unsecured, "l5_pass_over_rim": _chk_pass_over_rim,
    "l5_pass_across_lane": _chk_pass_across_lane, "l5_errant_pass": _chk_errant_pass,
    "intercept": _chk_interception_steal, "l5_bat_to_teammate": _chk_bat_to_teammate,
    "l5_slight_tip": _chk_slight_tip, "l5_knocked_loose": _chk_knocked_loose,
    "l5_fumble_unforced": _chk_fumble_unforced, "l5_muff": _chk_muff, "strip": _chk_strip_take_away,
    "l5_throw_in_side": _chk_throw_in, "l5_throw_in_baseline": _chk_throw_in,
    "tie_up": _chk_held_ball, "l2_drive_tieup": _chk_held_ball, "l5_rebound_tieup": _chk_rebound_tieup,
    "l1_deflect": _chk_no_turnover_deflection, "loose": _chk_no_turnover_deflection,
}

# Seeds 1-10 pass counts at sigma_p 0.2 / 0.3 / 0.5 (changes_loop5 evidence); each test runs three passing seeds
# per tier. Scenes below 7 / 10 at 0.5 are noise-limited there (contested_ball tie-ups: BA-T4c).
L5_RATES = {
    "l5_rim_scramble": (10, 10, 9), "l5_rim_secured": (10, 10, 10), "l5_dead_unsecured": (10, 10, 10),
    "l5_pass_over_rim": (10, 10, 9), "l5_pass_across_lane": (10, 10, 10), "l5_errant_pass": (10, 10, 7),
    "intercept": (10, 10, 10), "l5_bat_to_teammate": (9, 7, 7), "l5_slight_tip": (10, 10, 10),
    "l5_knocked_loose": (8, 8, 7), "l5_fumble_unforced": (9, 9, 9), "l5_muff": (10, 8, 6), "strip": (10, 9, 7),
    "l5_throw_in_side": (10, 10, 10), "l5_throw_in_baseline": (10, 10, 9), "tie_up": (9, 10, 4),
    "l2_drive_tieup": (10, 8, 3), "l5_rebound_tieup": (10, 10, 10), "l1_deflect": (10, 10, 10), "loose": (10, 10, 10),
}
L5_SEEDS = {
    "l5_rim_scramble": ((1, 2, 3), (1, 2, 3), (1, 2, 3)), "l5_rim_secured": ((1, 2, 3), (1, 2, 3), (1, 2, 3)),
    "l5_dead_unsecured": ((1, 2, 3), (1, 2, 3), (1, 2, 3)), "l5_pass_over_rim": ((1, 2, 3), (1, 2, 3), (1, 2, 3)),
    "l5_pass_across_lane": ((1, 2, 3), (1, 2, 3), (1, 2, 3)), "l5_errant_pass": ((1, 2, 3), (1, 2, 3), (1, 3, 4)),
    "intercept": ((1, 2, 3), (1, 2, 3), (1, 2, 3)), "l5_bat_to_teammate": ((1, 2, 3), (1, 2, 4), (1, 2, 4)),
    "l5_slight_tip": ((1, 2, 3), (1, 2, 3), (1, 2, 3)), "l5_knocked_loose": ((1, 3, 4), (1, 3, 4), (1, 4, 5)),
    "l5_fumble_unforced": ((1, 2, 3), (1, 2, 3), (1, 2, 3)), "l5_muff": ((1, 2, 3), (1, 2, 3), (1, 2, 3)),
    "strip": ((1, 2, 3), (1, 2, 3), (1, 2, 5)), "l5_throw_in_side": ((1, 2, 3), (1, 2, 3), (1, 2, 3)),
    "l5_throw_in_baseline": ((1, 2, 3), (1, 2, 3), (1, 2, 3)), "tie_up": ((1, 2, 3), (1, 2, 3), (1, 2, 7)),
    "l2_drive_tieup": ((1, 2, 3), (1, 2, 4), (1, 2, 4)), "l5_rebound_tieup": ((1, 2, 3), (1, 2, 3), (1, 2, 3)),
    "l1_deflect": ((1, 2, 3), (1, 2, 3), (1, 2, 3)), "loose": ((1, 2, 3), (1, 2, 3), (1, 2, 3)),
}
L5_CASES = [(name, sg, seed) for name, tiers in L5_SEEDS.items() for sg, seeds in zip((0.2, 0.3, 0.5), tiers)
            for seed in seeds]


@pytest.mark.parametrize("name,sigma,seed", L5_CASES, ids=lambda v: str(v))
def test_loop5_turnover_rules(name, sigma, seed):
    """changes_loop5: one check per NCAA rule scene (see L5_CHECKS and the scene comments): control gates
    (TO-C1 rim_scramble / rim_secured, TO-C2 dead_unsecured), no try (TO-D1 pass_over_rim / pass_across_lane,
    throw_in_baseline), steal credit (TO-S1 strip, intercept, errant_pass, bat_to_teammate, slight_tip,
    knocked_loose, fumble_unforced), charged player (TO-K1 muff), throw-in (TO-T1), held ball (TO-H1 tie_up,
    l2_drive_tieup; rebound_tieup = no control), deflection / fumble the offence keeps (l1_deflect, loose)."""
    sc = scene(name, seed, sigma)
    ok = L5_CHECKS[name](sc)
    assert ok, (name, sigma, seed, [(e.kind, e.actors, e.attrs.get("label"), e.attrs.get("reason"),
                                     e.attrs.get("steal_to"), e.attrs.get("steal_basis"))
                                    for e in _lbt(sc) + _abst(sc)])


def _clocked(name, seed, sigma, clock_at_0):
    sc = _fresh(name, seed, sigma)
    sc.game_clock = BA.np.maximum(clock_at_0 - BA.np.arange(sc.n) * DT, 0.0)
    return sc


@pytest.mark.parametrize("sigma,seed", [(0.2, 1), (0.3, 1), (0.3, 2), (0.5, 1)])
def test_loop5_end_of_period(sigma, seed):
    """TO-E1 (SM 4 Art.1 exception): D strips A at 2.0 s. With the game clock expiring at 1.9 s it is no turnover
    (and no abstention); with 10 s left it is one; without a clock the event says the check needs one."""
    assert not _lbt(_clocked("strip", seed, sigma, 1.9)) and not _abst(_clocked("strip", seed, sigma, 1.9))
    e = _one(_lbt(_clocked("strip", seed, sigma, 10.0)), lost_by="A", gained_by="D")
    assert e and e[0].attrs["period_end_check"] == "ok"
    e = _one(_lbt(_fresh("strip", seed, sigma)), lost_by="A", gained_by="D")
    assert e and e[0].attrs["period_end_check"] == "needs_game_clock"


def test_loop5_duplicates_merge():
    """TO-M1 (Aldemir R7): two counted same-direction changes within dedupe_window_s are one loss; a decided
    turnover replaces an abstention of the same loss; opposite directions or a wider gap are kept apart."""
    from types import SimpleNamespace as NS
    w = BA.PARAMS["live_ball_turnover"]["dedupe_window_s"]

    def rec(dec, off, t):
        return NS(decision=dec, L=NS(off=off), G=NS(a=int(round(t / DT))), merged=[])
    a, b = rec("turnover", True, 1.0), rec("turnover", True, 1.0 + w / 2)
    assert BA._merge_duplicates([a, b], w) == [a] and a.merged == [b.G.a]
    a, b = rec("abstain", True, 1.0), rec("turnover", True, 1.5)
    assert BA._merge_duplicates([a, b], w) == [b] and b.merged == [a.G.a]
    a, b = rec("turnover", True, 1.0), rec("turnover", False, 1.5)
    assert BA._merge_duplicates([a, b], w) == [a, b]
    a, b = rec("turnover", True, 1.0), rec("turnover", True, 1.0 + 2 * w)
    assert BA._merge_duplicates([a, b], w) == [a, b]
    a, n, b = rec("turnover", True, 1.0), rec("no_turnover", False, 1.2), rec("turnover", True, 1.5)
    assert BA._merge_duplicates([a, n, b], w) == [a, n]


# PBP reconciliation hook (reconcile_turnovers): synthetic PBP rows on synthetic scenes (t = seconds from the clip
# start, team = the scene list of the team charged).
def _rec(name, rows, seed=1, sigma=0.3):
    return BA.reconcile_turnovers(scene(name, seed, sigma), rows)


def test_loop5_reconcile_offensive_foul_charged_to_fouler():
    """TO-F1 (SM 4 A.R.19(e)/(f), 6 A.R.9): an offensive foul is a dead-ball turnover on the fouler with no steal,
    also when the fouler is off the ball (B's illegal screen while A holds the ball)."""
    for fouler in ("A", "B"):
        out = _rec("hold", [{"t": 2.0, "type": "turnover", "team": "offense", "player": fouler,
                             "turnover_type": "offensive_foul"},
                            {"t": 2.0, "type": "foul", "team": "offense", "player": fouler, "offensive": True}])
        assert [(r["charged_to"], r["fouler"], r["steal_to"], r["live"], r["rule"]) for r in out["turnovers"]] == \
            [(fouler, fouler, None, False, "offensive_foul")]


@pytest.mark.parametrize("sigma,seed", [(0.2, 1), (0.3, 1), (0.5, 1)])
def test_loop5_reconcile_pass_forced_charge(sigma, seed):
    """TO-F1 (SM 4 A.R.21): B charges 0.3 s after catching A's pass; flagged as forced by the pass, the turnover
    is the passer's; unflagged it stays the fouler's and the catch is reported for review."""
    row = {"t": 2.4, "type": "turnover", "team": "offense", "player": "B", "turnover_type": "offensive_foul"}
    foul = {"t": 2.4, "type": "foul", "team": "offense", "player": "B", "offensive": True}
    out = _rec("pass_cs", [row, dict(foul, forced_by_pass=True)], seed, sigma)["turnovers"]
    assert [(r["charged_to"], r["fouler"], r["rule"]) for r in out] == [("A", "B", "pass_forced_charge")]
    out = _rec("pass_cs", [row, foul], seed, sigma)["turnovers"]
    assert [(r["charged_to"], r.get("needs_review"), r.get("passer")) for r in out] == \
        [("B", "pass_forced_charge?", "A")]


@pytest.mark.parametrize("sigma,seed", [(0.2, 1), (0.3, 1), (0.3, 2)])
def test_loop5_reconcile_held_ball_arrow(sigma, seed):
    """TO-H1 (SM 4 A.R.10): A, in control, is tied up by D. Arrow to the defence: turnover on A, steal to D; arrow
    to the offence: nothing; no held-ball abstention (rebound tie-up): nothing either way."""
    out = _rec("tie_up", [{"t": 1.3, "type": "held_ball", "arrow_team": "defense"}], seed, sigma)
    assert [(r["charged_to"], r["steal_to"], r["live"], r["rule"]) for r in out["turnovers"]] == \
        [("A", "D", False, "held_ball_arrow_to_defence")]
    out = _rec("tie_up", [{"t": 1.3, "type": "held_ball", "arrow_team": "offense"}], seed, sigma)
    assert not out["turnovers"] and out["dropped"][0][1] == "held_ball_arrow_to_controlling_team"
    out = _rec("l5_rebound_tieup", [{"t": 2.0, "type": "held_ball", "arrow_team": "defense"}], seed, sigma)
    assert not out["turnovers"] and out["dropped"][0][1] == "held_ball_without_control"


def test_loop5_reconcile_review_duplicates_period_end():
    """TO-R1: a review that overturns the call removes the PBP row and the tracking turnover; upheld keeps one
    record (both sources). TO-M1: one turnover logged twice is one. TO-E1: a PBP-only turnover at the period end
    (the clock expired with the team in control) is dropped."""
    row = {"t": 2.1, "type": "turnover", "team": "offense", "player": "A"}
    out = _rec("strip", [row, {"t": 30.0, "type": "review", "outcome": "overturned"}])
    assert not out["turnovers"] and {d[1] for d in out["dropped"]} == {"final_ruling_overturned"}
    out = _rec("strip", [row, {"t": 30.0, "type": "review", "outcome": "upheld"}])
    assert [(r["source"], r["charged_to"], r["steal_to"]) for r in out["turnovers"]] == [("both", "A", "D")]
    out = _rec("hold", [{"t": 1.0, "type": "turnover", "team": "offense", "player": "A"},
                        {"t": 2.0, "type": "turnover", "team": "offense", "player": "A"}])
    assert len(out["turnovers"]) == 1 and out["dropped"][0][1] == "duplicate"
    out = _rec("hold", [{"t": 3.8, "type": "turnover", "team": "offense", "player": "A"},
                        {"t": 4.0, "type": "period_end"}])
    assert not out["turnovers"] and out["dropped"][0][1] == "end_of_period"


@pytest.mark.parametrize("sigma,seed", [(0.2, 1), (0.3, 1), (0.5, 1)])
def test_loop5_reconcile_abstention_resolved_by_pbp(sigma, seed):
    """An abstention (rim_visit: try or pass off the rim) becomes a turnover only when PBP lists one; tracking-only
    turnovers are kept as blind records."""
    out = _rec("l5_pass_over_rim", [{"t": 2.0, "type": "turnover", "team": "offense", "player": "A"}], seed, sigma)
    assert [(r["source"], r["charged_to"], r["live"]) for r in out["turnovers"]] == [("abstention+pbp", "A", True)]
    assert not _rec("l5_pass_over_rim", [], seed, sigma)["turnovers"]
    assert [r["source"] for r in _rec("strip", [], seed, sigma)["turnovers"]] == ["tracking"]


def test_loop5_params_are_yaml_params():
    expect = {"live_ball_turnover": ["rim_visit_r_m", "rim_visit_pad_s", "gain_secure_min_s", "deflect_touch_max_s",
                                     "deflect_recover_max_s", "tip_max_turn_deg", "intercept_move_min_m",
                                     "intercept_move_window_s", "knock_reach_m", "knock_window_s", "muff_max_s",
                                     "period_end_eps_s", "dedupe_window_s", "held_prior_max_gap_s", "held_prior_min_s"],
              "ba_turnover_rules": ["match_window_s", "review_window_s", "dup_window_s", "foul_link_s",
                                    "pass_forced_charge_s", "period_end_eps_s"]}
    for item, names in expect.items():
        assert set(names) == set(BA.PARAMS[item]), item
    # overrides reach the rules: a zero rim-visit radius turns the pass over the rim back into a turnover
    sc = scene("l5_pass_over_rim", 1, 0.3)
    assert not _lbt(sc) and _one(_lbt(sc, rim_visit_r_m=0.0), lost_by="A", gained_by="D")
    assert _one(BA.DETECTORS["turnover_abstention"](sc), lost_by="A")
    assert not [e for e in BA.DETECTORS["turnover_abstention"](sc, rim_visit_r_m=0.0) if e.attrs["reason"] == "rim_visit"]


def test_changes_loop5_recorded_in_yaml():
    ids = {c["id"] for c in BA.DOC["changes_loop5"]}
    for tag in ("TO-C1", "TO-C2", "TO-D1", "TO-E1", "TO-S1", "TO-K1", "TO-T1", "TO-H1", "TO-F1", "TO-R1", "TO-M1"):
        assert any(x.startswith(tag) for x in ids), f"{tag} missing from changes_loop5"
    for c in BA.DOC["changes_loop5"]:
        assert {"id", "what", "why", "evidence"} <= set(c), c


L5_POSITIVE = [
    ("turnover_abstention", "l5_pass_over_rim", "turnover_abstention", {"lost_by": "A", "gained_by": "D"}, 2.0, 0.5,
     1.0, {"reason": "rim_visit", "label": "interception"}),
    ("live_ball_turnover", "l5_throw_in_side", "live_ball_turnover", {"lost_by": "T", "gained_by": "D"}, 1.35, 0.5,
     1.0, {"throw_in": True, "steal_to": "D"}),
]
L5_NEGATIVE = [
    ("turnover_abstention", "pass_cs", None), ("turnover_abstention", "intercept", None),
    ("live_ball_turnover", "l5_pass_over_rim", None), ("live_ball_turnover", "l5_rim_scramble", None),
]
POSITIVE.extend(L5_POSITIVE)  # read at run time by test_every_detector_has_positive_and_negative_cases
NEGATIVE.extend(L5_NEGATIVE)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("case", L5_POSITIVE, ids=lambda c: f"{c[0]}-{c[1]}")
def test_loop5_positive(case, seed):
    test_positive(case, seed)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("case", L5_NEGATIVE, ids=lambda c: f"{c[0]}-{c[1]}")
def test_loop5_negative(case, seed):
    test_negative(case, seed)


def test_loop6_hidden_dribble_measurement_recorded():
    """changes_loop6 BA-L6-01: the hidden-dribble priors were measured on SportVU ball z and kept (no parameter change)."""
    assert BA.DOC["version"] == "0.1.6"
    ch = {c["id"].split()[0]: c for c in BA.DOC["changes_loop6"]}
    assert set(ch) == {"BA-L6-01"} and all(ch["BA-L6-01"][k] for k in ("what", "why", "evidence"))
    items = {it["id"]: it for it in BA.DOC["items"]}
    assert items["catch_and_shoot"]["params"]["p_hidden_dribble_short"]["value"] == 0.05
    assert items["catch_and_shoot"]["params"]["p_hidden_dribble_long"]["value"] == 0.2
    assert "BA-L6-01" in items["held_jumper"]["params"]["p_hidden_dribble"]["note"]
    assert BA.DOC["open_after_loop6"]
