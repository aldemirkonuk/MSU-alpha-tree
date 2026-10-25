"""Metric definitions of config/identity_pack.yaml checked on hand-made sequences."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "identity"))

import idlib  # noqa: E402
import metrics  # noqa: E402

H = idlib.HOLD


def toy(labels_a, labels_b, official=None):
    """Two true players (0, 1) seen every frame; optional official detections (src -1)."""
    F = len(labels_a)
    fr, src, lab = [], [], []
    for f in range(F):
        fr += [f, f]
        src += [0, 1]
        lab += [labels_a[f], labels_b[f]]
        if official is not None:
            fr.append(f)
            src.append(-1)
            lab.append(official[f])
    n = len(fr)
    z = np.zeros(n)
    d = idlib.Dets(1.0, F, np.array(fr), np.zeros((n, 2)), np.array(src), z.astype(bool), z.astype(int) - 1,
                   z.astype(int) - 1, None, None, None, np.zeros(F, bool), np.zeros((F, 2)))
    in_fov = np.ones((F, 2), dtype=bool)
    return d, np.array(lab), in_fov


def test_perfect_labels():
    d, lab, fov = toy([0] * 10, [1] * 10)
    m = metrics.identity_metrics(d, lab, fov, 1.0)
    assert m["swap_events"] == 0 and m["idsw"] == 0
    assert m["idf1"] == pytest.approx(1.0) and m["hota"] == pytest.approx(1.0) and m["coverage"] == 1.0


def test_a_swap_is_two_switches_and_two_swap_events():
    d, lab, fov = toy([0] * 5 + [1] * 5, [1] * 5 + [0] * 5)
    m = metrics.identity_metrics(d, lab, fov, 1.0)
    assert m["idsw"] == 2
    assert m["swap_events"] == 2
    assert m["wrong_label_frames"] == 10
    assert m["idf1"] == pytest.approx(0.5)


def test_hold_is_not_a_switch_but_costs_recall():
    d, lab, fov = toy([0, 0, H, H, 0, 0], [1, H, H, 1, 1, 1])
    m = metrics.identity_metrics(d, lab, fov, 1.0)
    assert m["idsw"] == 0 and m["swap_events"] == 0
    assert m["idr"] == pytest.approx(8 / 12) and m["idp"] == pytest.approx(1.0)
    assert m["coverage"] == pytest.approx(8 / 12)


def test_label_on_official_is_a_swap_event():
    d, lab, fov = toy([0] * 4, [1] * 4, official=[H, 0, H, H])
    m = metrics.identity_metrics(d, lab, fov, 1.0)
    assert m["swap_events"] == 1 and m["labels_on_officials"] == 1


def test_hota_assa_on_a_split_track():
    # player 0: label 0 for 6 frames then HOLD for 4; AssA = 6 / (10 + 6 - 6) for every TP
    d, lab, fov = toy([0] * 6 + [H] * 4, [1] * 10)
    m = metrics.identity_metrics(d, lab, fov, 1.0)
    deta = 16 / 20
    assa = (6 * (6 / 10) + 10 * 1.0) / 16
    assert m["deta"] == pytest.approx(deta) and m["assa"] == pytest.approx(assa)
    assert m["hota"] == pytest.approx(np.sqrt(deta * assa))


def test_true_crossings_need_a_bearing_flip():
    F = 40
    pos = np.full((F, 2, 2), np.nan)
    pos[:, 0, 0] = np.linspace(0, 4, F)
    pos[:, 0, 1] = 0.0
    pos[:, 1, 0] = np.linspace(4, 0, F)
    pos[:, 1, 1] = 0.3
    assert len(metrics.true_crossings(pos, 0.1)) == 1  # they pass each other
    pos[:, 1, 0] = np.linspace(0.5, 4.5, F)  # side by side, no flip
    assert metrics.true_crossings(pos, 0.1) == []


def test_invariant_breaks():
    d, lab, fov = toy([0] * 3, [0, 1, 1])
    cand = np.ones((3, 2), dtype=bool)
    assert metrics.invariant_breaks(d, lab, cand)["inv1_duplicates"] == 1
    cand[:, 1] = False
    assert metrics.invariant_breaks(d, lab, cand)["inv3_outside_lineup"] == 2


def test_inv2_and_calibration():
    d, lab, fov = toy([0, 0, 0], [1, 1, 0])
    team = np.array([0, 0])
    cand = np.ones((3, 2), dtype=bool)
    assert metrics.invariant_breaks(d, lab, cand, team)["inv2_over_five"] == 0
    post = np.array([0.999, 0.999, 0.9999, 0.9999, 0.996, 0.996])
    cal = metrics.calibration(d, lab, post)
    assert sum(b["labels"] for b in cal) == 6 and sum(b["wrong"] for b in cal) == 1
