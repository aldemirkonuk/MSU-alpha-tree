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


def test_chain_purity_counts_foreign_boxes_by_kind():
    """Review round 2 (ATK-03, RV-23): purity of the clean chains is measured against the truth ids."""
    from types import SimpleNamespace as NS
    src = np.array([0, 0, 0, 0, 1, 1, 7, -1, 3, 3, 3, 5, 5])
    d = NS(src=src)
    team = np.array([0] * 7 + [1] * 7)
    chains = [NS(kind="group", dets=np.arange(0, 8)),      # player 0 x 4, teammate 1 x 2, opponent 7, an official
              NS(kind="root", dets=np.arange(8, 11)),      # pure
              NS(kind="amb", dets=np.arange(11, 13))]      # amb segments are not counted
    label = np.full(len(src), -1)
    label[[0, 1, 4, 7]] = 0                                 # two right labels, one on the teammate, one on the official
    pu = metrics.chain_purity(d, chains, team, label)
    assert pu == {"clean_chains": 2, "clean_chain_boxes": 11, "impure_clean_chains": 1, "impure_minority_boxes": 4,
                  "impure_teammate_boxes": 2, "impure_opponent_boxes": 1, "impure_non_player_boxes": 1, "impure_labelled_boxes": 2}


def test_swap_mechanism_separates_a_foreign_box_from_a_wrong_chain():
    """impure_chain: the run's chain also holds boxes of the labelled player (right label, foreign box). A chain that is
    wrong as a whole is not counted (evidence model or lineup)."""
    from types import SimpleNamespace as NS
    n = 40
    src = np.r_[np.zeros(30, int), np.ones(10, int)]        # chain 0: player 0 for 30 frames, then teammate 1 for 10
    d = NS(src=np.r_[src, np.full(n, 2)], frame=np.r_[np.arange(n), np.arange(n)])
    det_chain = np.r_[np.zeros(n, int), np.ones(n, int)]    # chain 1: player 2 throughout
    team = np.array([0] * 7 + [1] * 7)
    cand = np.ones((n, 14), dtype=bool)
    flags = {k: np.zeros(2 * n, dtype=bool) for k in ("overlap_unflagged", "colour_run", "jersey_trunc", "jersey_repeat")}
    label = np.r_[np.zeros(n, int), np.full(n, -1)]          # chain 0 labelled 0 on every box: 10 foreign boxes
    assert metrics.swap_mechanisms(d, label, cand, team, flags, 0.04, 0, det_chain) == {"other": 1, "impure_chain": 1}
    label = np.r_[np.full(n, -1), np.full(n, 3)]             # chain 1 (pure, player 2) labelled 3: a wrong chain
    assert metrics.swap_mechanisms(d, label, cand, team, flags, 0.04, 0, det_chain) == {"other": 1}
    assert metrics.swap_mechanisms(d, label, cand, team, flags, 0.04, 0) == {"other": 1}  # without chains: no attribution
