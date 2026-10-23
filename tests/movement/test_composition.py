"""Synthetic (V0) tests for the composition family: config/movement_grammar/composition.yaml and
tools/specgen/movement/detectors/composition.py.

Every scenario is built with sim.scenario at sigma_p = 0.3 m and a fixed seed. Positions are in the
attacked-rim frame (metres). Truth times are computed from the noise-free paths with the same spec
definition the detector uses (closest approach, crossing frame, ...), and each detector is checked for
kind, actors, t0 within +-0.3 s and conf in (0, 1].
"""
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "movement"))
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "named_spots"))

import mvlib  # noqa: E402
import sim  # noqa: E402
from detectors import composition as C  # noqa: E402

DT = mvlib.DT
SIG = 0.3
TOL = 0.3  # s


# --------------------------------------------------------------------------------------
# Scenario helpers
# --------------------------------------------------------------------------------------
HORNS = {"o1": (0.0, 7.6), "o2": (1.8, 4.2), "o3": (-1.8, 4.2), "o4": (6.7, 0.3), "o5": (-6.7, 0.3)}


def actors(paths):
    """paths: {id: [(t, x, y), ...]} or {id: (x, y)} (static) -> sim actor spec (offense team 'O')."""
    out = {}
    for k, v in paths.items():
        wp = [(0.0, v[0], v[1])] if isinstance(v, tuple) else v
        out[k] = {"team": "O", "wp": wp}
    return out


MAX_PEAK_MPS = 8.0  # loop 1 F17: no scenario may ask a player for more than an 8 m/s sprint


def peak_speeds(spec):
    """Minimum-jerk peak speed (1.875 x distance / time) of every waypoint segment -> [(actor, t0, t1, peak)]."""
    out = []
    for aid, a in spec["actors"].items():
        for (t0, x0, y0), (t1, x1, y1) in zip(a["wp"], a["wp"][1:]):
            if t1 > t0:
                out.append((aid, t0, t1, 1.875 * float(np.hypot(x1 - x0, y1 - y0)) / (t1 - t0)))
    return out


def assert_feasible(spec):
    bad = [z for z in peak_speeds(spec) if z[3] > MAX_PEAK_MPS + 1e-9]
    assert not bad, f"infeasible segments (actor, t0, t1, peak m/s): {bad}"


def scene_of(spec, dur, seed=1, sigma=None):
    assert_feasible(spec)
    truth, tracks = sim.scenario(spec, dur, sigma_p=SIG if sigma is None else sigma, seed=seed)
    return truth, mvlib.build_scene(tracks)


def f(t):
    return int(round(t / DT))


def t_closest(truth, a, b, t0, t1):
    """Truth time of the minimum a-b distance inside [t0, t1] s."""
    ia, ib = f(t0), f(t1)
    d = np.hypot(truth[a][0][ia:ib + 1] - truth[b][0][ia:ib + 1], truth[a][1][ia:ib + 1] - truth[b][1][ia:ib + 1])
    return (ia + int(np.argmin(d))) * DT


def one(evs, kind=None):
    evs = [e for e in evs if kind is None or e.kind == kind]
    assert evs, "expected an event"
    return max(evs, key=lambda e: e.conf)


def check(e, kind, t_true, actors_sub=None):
    assert e.kind == kind
    assert abs(e.t0 * DT - t_true) <= TOL, f"t0 {e.t0 * DT:.2f} vs truth {t_true:.2f}"
    assert 0.0 < e.conf <= 1.0
    for k, v in (actors_sub or {}).items():
        assert e.actors.get(k) == v, f"actor {k}: {e.actors.get(k)} != {v}"


def horns_pnr(roll=True, screen=True, spain_s2=False, dur=8.0):
    """Horns: handler o1 arrives at the top, o2 steps up and screens at 2.5 s, o1 dribbles right past him at 3.0 s,
    o2 rolls at 3.6 s (or holds)."""
    p = {k: v for k, v in HORNS.items()}
    p["o1"] = [(0.0, 0.0, 11.0), (1.2, 0.0, 7.6), (3.0, 0.0, 7.6), (4.2, 3.5, 6.0)] if screen else [(0.0, 0.0, 11.0), (1.2, 0.0, 7.6)]
    if screen:
        o2 = [(0.0, 1.8, 4.2), (1.6, 1.8, 4.2), (2.5, 0.8, 7.2)]
        o2 += [(3.6, 0.8, 7.2), (5.1, 0.3, 1.0)] if roll else []
        p["o2"] = o2
    if spain_s2:
        p["o3"] = [(0.0, -1.8, 4.2), (1.5, -1.8, 4.2), (2.8, 0.9, 4.5)]
    spec = {"actors": actors(p), "ball": {"held": [(0.0, dur, "o1")]}}
    return spec, dur


# --------------------------------------------------------------------------------------
# Library-level checks (matcher fixes, YAML contract)
# --------------------------------------------------------------------------------------
def test_yaml_contract():
    """Every item has the required fields; detectable items are in DETECTORS; needs_data items return []."""
    need = ["id", "level", "name", "aliases", "actors", "t0", "rule", "params", "min_duration_s", "outputs",
            "confidence", "noise_notes", "conflicts_resolved", "sources", "status"]
    assert C.DOC["version"] == "0.8.0" and C.DOC["date"] == "2026-10-23" and C.DOC["family"] == "composition"
    for ch in (C.DOC["changes_loop1"] + C.DOC["changes_loop2"] + C.DOC["changes_loop4"] + C.DOC["changes_loop5"]
               + C.DOC["changes_loop6"] + C.DOC["changes_loop7"] + C.DOC["changes_loop8"]):  # change logs: one entry per item (+ version)
        assert {"id", "what", "why", "evidence"} <= set(ch), ch
    assert {c["id"].split("-")[0] for c in C.DOC["changes_loop7"]} >= {"C1", "C3", "C7", "C9", "version"}
    assert "provisional" in next(c for c in C.DOC["changes_loop7"] if c["id"] == "C9-overfit-caveat")["why"]
    assert {c["id"].split("-")[0] for c in C.DOC["changes_loop8"]} >= {"C1", "C3", "C7", "version"}
    assert {c["id"].split("-")[0] for c in C.DOC["changes_loop5"]} >= {f"C{i}" for i in range(1, 9)}
    assert {c["id"].split("-")[0] for c in C.DOC["changes_loop6"]} >= {"C1", "C2", "C3", "C4", "C7", "C8"}
    assert {c["id"].split("-")[0] for c in C.DOC["changes_loop1"]} >= {f"F{i}" for i in range(1, 18)}
    assert {c["id"].split("-")[0] for c in C.DOC["changes_loop2"]} >= {f"R{i}" for i in range(1, 6)}
    assert {c["id"].split("-")[0] for c in C.DOC["changes_loop4"]} >= {f"L{i}" for i in range(1, 12)}
    for iid, it in C.ITEMS.items():
        for k in need:
            assert k in it, (iid, k)
        assert it["level"] in ("primitive", "action", "set_component", "rule")
        assert it["status"] in ("canonical", "proposal")
        assert it.get("detector") or it.get("implemented_by"), iid  # R-ST-16: signature or implementation
        if it.get("detector"):
            assert iid in C.DETECTORS
        if it.get("needs_data"):
            assert C.DETECTORS[iid].__name__ == "_needs_data"
    assert len(C.TEMPLATES) >= 12
    names = [t["namespace"] + t["id"] for t in C.TEMPLATES]
    assert len(names) == len(set(names))  # R-ST-22: no duplicate names


def _fake(kind, actors_, t, p=0.8, end=None):
    return mvlib.Event(kind, actors_, t, t, end if end is not None else t, p, {})


def _flat_scene(n=400):
    spec = {"actors": actors({k: v for k, v in HORNS.items()})}
    return scene_of(spec, n * DT, seed=3)[1]


T4 = {"id": "t4", "name": "T4", "namespace": "test.", "alignments": "any", "_groups": {},
      "steps": [{"id": f"s{i}", "kind": "PASS", "roles": {"passer": f"r{i}", "receiver": f"r{i + 1}"}, "window_s": [0.0, 2.0]}
                for i in range(4)]}


def test_matcher_floor_rejects_half_deleted():
    """Skeptic CE-R09/R11: with 2 of 4 required steps missing the template is never accepted (floor 75 %)."""
    sc = _flat_scene()
    ids = ["o1", "o2", "o3", "o4", "o5"]
    full = [_fake("PASS", {"passer": ids[i], "receiver": ids[i + 1]}, 30 + 30 * i) for i in range(4)]
    half = full[:2]
    res, _ = C.score_templates(sc, full, None, templates=[T4])
    assert res[0]["accepted"] and res[0]["frac_required"] == 1.0
    res, _ = C.score_templates(sc, half, None, templates=[T4])
    assert res[0]["frac_required"] == 0.5 and not res[0]["accepted"]
    three = full[:3]
    res, _ = C.score_templates(sc, three, None, templates=[T4])
    assert res[0]["frac_required"] == 0.75 and res[0]["c_hat"] <= C.PRM["probability"]["c_null"]


def test_matcher_long_window_insertions():
    """Skeptic CE-R09: ball events outside the matched span cost nothing; inside, the cost is capped."""
    sc = _flat_scene()
    ids = ["o1", "o2", "o3", "o4", "o5"]
    full = [_fake("PASS", {"passer": ids[i], "receiver": ids[i + 1]}, 100 + 30 * i) for i in range(4)]
    base = C.match_template(sc, T4, full)["c_hat"]
    extra = [_fake("DHO", {"giver": "o1", "receiver": "o2"}, t) for t in (5, 15, 25, 300, 320, 340)]
    longer = C.match_template(sc, T4, sorted(full + extra, key=lambda e: e.t0))["c_hat"]
    assert abs(longer - base) < 1e-9
    inside = [_fake("DHO", {"giver": "o1", "receiver": "o2"}, t) for t in range(105, 190, 10)]
    r = C.match_template(sc, T4, sorted(full + inside, key=lambda e: e.t0))
    assert r["c_ins"] <= C.PRM["matcher"]["ins_cap_frac"] * r["W"] + 1e-9
    assert r["frac_required"] == 1.0


def test_single_normalisation_and_length_prior():
    """Ranking and acceptance use the same C_hat; a template that explains more matched steps wins at equal quality."""
    sc = _flat_scene()
    ids = ["o1", "o2", "o3", "o4", "o5"]
    full = [_fake("PASS", {"passer": ids[i], "receiver": ids[i + 1]}, 100 + 30 * i) for i in range(4)]
    T2 = dict(T4, id="t2", steps=T4["steps"][:2])
    res, _ = C.score_templates(sc, full, None, templates=[T2, T4])
    assert res[0]["template"] == "t4"
    for r in res:
        assert abs(r["c_hat"] - r["C"] / r["W"]) < 1e-9


def test_role_binding_tracker_swap():
    """One re-binding is allowed when the tracker reports an id swap (cost swap_rebind_cost)."""
    sc = _flat_scene()
    chain = [("o1", "o2", 100), ("o2", "o3", 130), ("o3", "o4", 160), ("o4", "o5", 190)]
    sw = {"o3": "o4", "o4": "o3"}
    lat = [_fake("PASS", {"passer": sw.get(a, a) if t >= 150 else a, "receiver": sw.get(b, b) if t >= 150 else b}, t)
           for a, b, t in chain]
    plain = C.match_template(sc, T4, lat)
    fixed = C.match_template(sc, T4, lat, swaps=[(150, "o3", "o4")])
    assert plain["frac_required"] < 1.0
    assert fixed["frac_required"] == 1.0 and fixed.get("swap") == (150, "o3", "o4")
    assert fixed["C"] < plain["C"]


def test_counter_suppresses_departure():
    """A listed counter (slip on the Horns PnR read) costs <= 0.5, sets counter_code and is not a departure."""
    sc = _flat_scene()
    T = next(t for t in C.TEMPLATES if t["id"] == "horns_pnr")
    lat = [_fake("SCR.on", {"screener": "o2", "user": "o1"}, 100, end=115), _fake("SLIP", {"screener": "o2"}, 100, end=130)]
    res, _ = C.score_templates(sc, lat, None, templates=[T])
    r = res[0]
    assert [pp.get("counter") for sid, i, pp in r["path"] if i is not None] == [None, "slip"]
    assert C.departure(r, lat) is None


# --------------------------------------------------------------------------------------
# ALIGN, windows, resets
# --------------------------------------------------------------------------------------
def _true_snap(truth, code="horns", t_lo=0.0, t_hi=3.0):
    """Spec rule on truth: earliest frame whose mean slot error is within 0.1 m of the minimum."""
    Q = np.array([[pp[0], pp[1]] for pp in next(a for a in C.ALIGNMENTS if a["code"] == code)["positions"]])
    errs = []
    for i in range(f(t_lo), f(t_hi)):
        P = np.array([[truth[o][0][i], truth[o][1][i]] for o in ["o1", "o2", "o3", "o4", "o5"]])
        D = np.hypot(P[:, None, 0] - Q[None, :, 0], P[:, None, 1] - Q[None, :, 1])
        errs.append(min(D[np.arange(5), pp].mean() for pp in C.PERMS))
    errs = np.array(errs)
    return (f(t_lo) + int(np.flatnonzero(errs <= errs.min() + 0.1)[0])) * DT


def test_align_snapshot_positive():
    spec, dur = horns_pnr(screen=False, dur=4.0)
    truth, sc = scene_of(spec, dur, seed=11)
    e = one(C.detect_align_snapshot(sc))
    trig = e.attrs["trigger_f"] * DT
    check(e, "align", _true_snap(truth, "horns", max(0, trig - 0.5), trig + 1.0), {"top": "o1"})
    assert e.attrs["code"] == "horns" and e.attrs["accepted"]
    assert e.attrs["probs_top3"][0][0] == "horns"


def test_align_snapshot_negative_backcourt_and_free():
    spec = {"actors": actors({"o1": (0.0, 16.0), "o2": (3.0, 18.0), "o3": (-3.0, 18.0), "o4": (5.0, 20.0), "o5": (-5.0, 20.0)}),
            "ball": {"held": [(0.0, 3.0, "o1")]}}
    _, sc = scene_of(spec, 3.0, seed=12)
    assert C.detect_align_snapshot(sc) == []
    # scattered positions: probabilities still emitted, but not accepted
    spec = {"actors": actors({"o1": (0.0, 7.6), "o2": (3.0, 2.0), "o3": (-4.0, 6.0), "o4": (0.5, 3.0), "o5": (-6.0, 1.5)}),
            "ball": {"held": [(0.0, 3.0, "o1")]}}
    _, sc = scene_of(spec, 3.0, seed=13)
    e = one(C.detect_align_snapshot(sc))
    assert not e.attrs["accepted"] and len(e.attrs["probs_top3"]) == 3


def test_set_window_positive_negative():
    spec, dur = horns_pnr(dur=6.0)
    truth, sc = scene_of(spec, dur, seed=21)
    e = one([w for w in C.detect_set_window(sc) if w.attrs["segment_kind"] == "halfcourt"])
    al = one(C.detect_align_snapshot(sc))
    trig = al.attrs["trigger_f"] * DT
    check(e, "set_window", _true_snap(truth, "horns", max(0, trig - 0.5), trig + 1.0))
    assert e.attrs["close_reason"] == "clip_end"
    spec = {"actors": actors({"o1": (0.0, 16.0), "o2": (3.0, 18.0), "o3": (-3.0, 18.0), "o4": (5.0, 20.0), "o5": (-5.0, 20.0)}),
            "ball": {"held": [(0.0, 3.0, "o1")]}}
    _, sc = scene_of(spec, 3.0, seed=22)
    assert C.detect_set_window(sc) == []


RESET_ACTIONS_END = 5.2  # s: the last action (o2's relocation after the roll) ends here


def reset_scene(reset=True):
    """Action phase (ball screen + roll + cuts) until RESET_ACTIONS_END, then everybody settles in 5-out after a
    retreat dribble; a new action starts at 8.0 s. Negative: actions keep coming every ~1.2 s. Retimed in loop 1
    (F17) so no segment needs more than an 8 m/s sprint."""
    p = {"o1": [(0.0, 0.0, 11.0), (1.0, 0.0, 7.6), (1.6, 0.0, 7.6), (2.6, 3.5, 6.0), (3.5, 3.5, 6.0), (4.5, 1.0, 9.0)],
         "o2": [(0.0, 1.8, 4.2), (0.8, 0.8, 7.2), (2.1, 0.8, 7.2), (3.5, 0.5, 1.5), (RESET_ACTIONS_END, -5.3, 5.3)],
         "o3": [(0.0, -1.8, 4.2), (1.9, -1.8, 4.2), (3.7, 5.3, 5.3)],
         "o4": (6.8, 0.4), "o5": [(0.0, -6.8, 0.4)]}
    if reset:
        p["o5"] = [(0.0, -6.8, 0.4), (8.0, -6.8, 0.4), (9.7, -1.0, 4.5)]
    else:
        p["o5"] = [(0.0, -6.8, 0.4), (4.0, -6.8, 0.4), (5.7, -1.0, 4.5), (6.3, -1.0, 4.5), (7.8, -6.0, 1.0)]
        p["o4"] = [(0.0, 6.8, 0.4), (5.0, 6.8, 0.4), (6.5, 1.5, 3.5), (7.0, 1.5, 3.5), (8.2, 6.0, 4.0)]
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 10.0, "o1")]}}
    return spec, 10.0


def test_reset_positive():
    spec, dur = reset_scene(True)
    truth, sc = scene_of(spec, dur, seed=31)
    e = one(C.detect_reset(sc))
    # truth: the last action (o2's relocation cut) ends at RESET_ACTIONS_END; quiet must hold quiet_s after it
    acts = [x for x in C.primitives(sc) if x.kind.split(".")[0] in C.ACTION_KINDS and x.t0 * DT < 6.0]
    t_true = RESET_ACTIONS_END + C.PRM["reset"]["quiet_s"]
    check(e, "reset", t_true, {"handler": "o1"})
    assert e.attrs["trigger"] in ("re_align", "retreat_dribble") and acts


def test_reset_negative():
    spec, dur = reset_scene(False)
    _, sc = scene_of(spec, dur, seed=32)
    assert [e for e in C.detect_reset(sc) if 4.0 < e.t0 * DT < 8.7] == []


# --------------------------------------------------------------------------------------
# Set components
# --------------------------------------------------------------------------------------
ONE_FOUR = {"o1": (0.0, 7.6), "o2": (1.8, 4.2), "o3": (-1.8, 4.2), "o4": (6.0, 5.0), "o5": (-6.0, 5.0)}


def test_iverson():
    p = dict(ONE_FOUR)
    p["o4"] = [(0.0, 6.0, 5.0), (2.0, 6.0, 5.0), (5.0, -4.0, 5.2)]
    truth, sc = scene_of({"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0, seed=41)
    e = one(C.detect_iverson(sc))
    check(e, "iverson", t_closest(truth, "o4", "o2", 2.0, 5.0), {"cutter": "o4", "screener": "o2"})
    q = dict(ONE_FOUR)
    q["o2"], q["o3"] = (2.0, 0.9), (-2.0, 0.9)  # no elbow players: no screen evidence
    q["o4"] = p["o4"]
    _, sc = scene_of({"actors": actors(q), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0, seed=42)
    assert C.detect_iverson(sc) == []


def test_zipper():
    p = {"o1": (-5.3, 5.3), "o2": [(0.0, 1.83, 0.9), (2.0, 1.83, 0.9), (3.8, 2.6, 7.0)], "o3": (2.1, 3.4),
         "o4": (6.8, 0.4), "o5": (-6.8, 0.4)}
    truth, sc = scene_of({"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0, seed=51)
    e = one(C.detect_zipper(sc))
    check(e, "zipper", t_closest(truth, "o2", "o3", 2.0, 3.8), {"cutter": "o2", "screener": "o3"})
    p["o3"] = (-2.1, 3.4)
    _, sc = scene_of({"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0, seed=52)
    assert C.detect_zipper(sc) == []


def chicago_scene(dho=True):
    p = {"o1": (-5.3, 5.3), "o2": (5.6, 2.6), "o3": (-1.8, 1.0),
         "o4": [(0.0, 6.7, 0.3), (2.0, 6.7, 0.3), (3.6, 4.7, 6.2), (4.2, 3.1, 7.2), (5.2, 4.5, 3.5)],
         "o5": [(0.0, 2.6, 7.6), (4.4, 2.6, 7.6), (5.4, 0.5, 7.8)]}
    if dho:
        ball = {"held": [(0.0, 4.2, "o5"), (4.2, 7.0, "o4")]}
    else:
        p["o5"] = [(0.0, -1.0, 8.0)]
        ball = {"held": [(0.0, 3.6, "o5"), (4.2, 7.0, "o4")], "flights": [(3.6, 4.2, "o5", "o4")]}
    return {"actors": actors(p), "ball": ball}, 7.0


def test_chicago():
    spec, dur = chicago_scene(True)
    truth, sc = scene_of(spec, dur, seed=63)
    e = one(C.detect_chicago(sc))
    check(e, "chicago", t_closest(truth, "o4", "o2", 2.0, 3.6), {"user": "o4", "screener": "o2", "giver": "o5"})
    spec, dur = chicago_scene(False)
    _, sc = scene_of(spec, dur, seed=62)
    assert C.detect_chicago(sc) == []


def test_spain():
    spec, dur = horns_pnr(roll=True, spain_s2=True)
    truth, sc = scene_of(spec, dur, seed=71)
    e = one(C.detect_spain(sc))
    check(e, "spain", t_closest(truth, "o1", "o2", 2.8, 4.2), {"handler": "o1", "screener": "o2", "back_screener": "o3"})
    assert e.attrs["evidence_mode"] == "proxy"
    spec, dur = horns_pnr(roll=True, spain_s2=False)
    _, sc = scene_of(spec, dur, seed=72)
    assert C.detect_spain(sc) == []


def elevator_scene(close=True):
    s1 = [(0.0, -0.6, 4.5)] + ([(2.85, -0.6, 4.5), (3.25, -0.25, 4.5)] if close else [])
    s2 = [(0.0, 0.6, 4.5)] + ([(2.85, 0.6, 4.5), (3.25, 0.25, 4.5)] if close else [])
    p = {"o1": (-5.3, 5.3), "o2": s1, "o3": s2, "o4": [(0.0, 0.0, 0.5), (1.9, 0.0, 0.5), (3.55, 0.0, 7.5)], "o5": (6.8, 0.4)}
    return {"actors": actors(p), "ball": {"held": [(0.0, 5.0, "o1")]}}, 5.0


def _cross_time(truth, u, y, t0, t1):
    ys = truth[u][1][f(t0):f(t1) + 1]
    return (f(t0) + int(np.flatnonzero(ys >= y)[0])) * DT


def test_elevator():
    spec, dur = elevator_scene(True)
    truth, sc = scene_of(spec, dur, seed=81)
    e = one(C.detect_elevator(sc))
    check(e, "elevator", _cross_time(truth, "o4", 4.5, 1.9, 3.55), {"user": "o4"})
    assert {e.actors["screener_1"], e.actors["screener_2"]} == {"o2", "o3"}
    spec, dur = elevator_scene(False)
    _, sc = scene_of(spec, dur, seed=82)
    assert C.detect_elevator(sc) == []


def floppy_scene(under=True):
    start = (0.9, 0.3) if under else (3.6, 2.6)
    p = {"o1": (0.0, 7.6), "o2": (2.2, 1.5), "o3": (-2.2, 1.5), "o5": (-0.9, 0.3),
         "o4": [(0.0, *start), (2.0, *start), (3.6, 5.5, 5.0)]}
    return {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0


def _move_onset(truth, o, t0, t1, v=1.0):
    x, y = truth[o]
    i0, i1 = f(t0), f(t1)
    sp = np.hypot(np.diff(x[i0:i1 + 1]), np.diff(y[i0:i1 + 1])) / DT
    return (i0 + int(np.flatnonzero(sp > v)[0])) * DT


def test_floppy():
    spec, dur = floppy_scene(True)
    truth, sc = scene_of(spec, dur, seed=91)
    e = one(C.detect_floppy(sc))
    check(e, "floppy", _move_onset(truth, "o4", 1.5, 3.5), {"shooter": "o4", "screener": "o2"})
    assert e.attrs["side_choice"] == "single"
    spec, dur = floppy_scene(False)
    _, sc = scene_of(spec, dur, seed=92)
    assert [x for x in C.detect_floppy(sc) if x.actors["shooter"] == "o4"] == []


def hammer_scene(baseline=True):
    end = (2.0, 0.5) if baseline else (0.5, 3.0)
    p = {"o1": [(0.0, 5.5, 4.5), (2.0, 5.5, 4.5), (3.25, *end)], "o2": (6.8, 0.4), "o3": (-4.4, 2.4),
         "o4": (0.0, 7.6), "o5": [(0.0, -2.5, 4.0), (2.25, -2.5, 4.0), (3.6, -6.8, 0.4)]}
    return {"actors": actors(p), "ball": {"held": [(0.0, 5.0, "o1")]}}, 5.0


def _r_cross(truth, o, r, t0, t1):
    x, y = truth[o]
    rr = np.hypot(x[f(t0):f(t1) + 1], y[f(t0):f(t1) + 1])
    return (f(t0) + int(np.flatnonzero(rr < r)[0])) * DT


def test_hammer():
    spec, dur = hammer_scene(True)
    truth, sc = scene_of(spec, dur, seed=101)
    e = one(C.detect_hammer(sc))
    check(e, "hammer", _r_cross(truth, "o1", 3.05, 2.0, 3.25), {"driver": "o1", "shooter": "o5", "screener": "o3"})
    spec, dur = hammer_scene(False)
    _, sc = scene_of(spec, dur, seed=102)
    assert C.detect_hammer(sc) == []


def pistol_scene(big_top=True):
    p = {"o1": [(0.0, 0.5, 11.0), (2.0, 3.0, 8.0), (2.6, 3.0, 8.0), (3.8, 6.0, 4.5)],
         "o2": [(0.0, 6.7, 0.4), (1.8, 4.2, 7.0)],
         "o3": (-6.8, 0.4), "o4": (-5.3, 5.3), "o5": (0.0, 7.3) if big_top else (0.0, 2.0)}
    return {"actors": actors(p), "ball": {"held": [(0.0, 5.0, "o1")]}}, 5.0


def test_pistol():
    spec, dur = pistol_scene(True)
    truth, sc = scene_of(spec, dur, seed=111)
    e = one(C.detect_pistol(sc))
    check(e, "pistol", t_closest(truth, "o1", "o2", 2.6, 3.8), {"handler": "o1", "wing": "o2", "big": "o5"})
    spec, dur = pistol_scene(False)
    _, sc = scene_of(spec, dur, seed=112)
    assert C.detect_pistol(sc) == []


def drag_scene(fast=True):
    """Trailer o5 sprints down the floor and screens the handler (who has stopped at r 7 m) while still running."""
    o5 = [(0.0, 1.5, 16.0), (0.3, 1.5, 16.0), (4.0, 0.6, 1.5)] if fast else [(0.0, 1.5, 9.0), (0.3, 1.5, 9.0), (4.0, 0.6, 1.5)]
    p = {"o1": [(0.0, 0.0, 14.0), (2.3, 0.2, 7.0), (3.0, 0.2, 7.0), (4.0, -2.5, 6.0)], "o5": o5,
         "o2": [(0.0, 5.0, 14.0), (3.3, 6.8, 0.4)], "o3": [(0.0, -5.0, 14.0), (3.3, -6.8, 0.4)], "o4": [(0.0, -2.0, 16.0), (4.0, -5.3, 5.3)]}
    return {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0


def test_drag():
    spec, dur = drag_scene(True)
    truth, sc = scene_of(spec, dur, seed=121)
    e = one(C.detect_drag(sc))
    check(e, "drag", t_closest(truth, "o5", "o1", 1.5, 3.5), {"handler": "o1", "screener": "o5"})
    assert e.attrs["read"] == "roll"
    spec, dur = drag_scene(False)
    _, sc = scene_of(spec, dur, seed=122)
    assert C.detect_drag(sc) == []


def test_pnr_location():
    spec, dur = horns_pnr(dur=6.0)
    truth, sc = scene_of(spec, dur, seed=131)
    e = one(C.detect_pnr_location(sc))
    check(e, "pnr_location", t_closest(truth, "o1", "o2", 2.8, 4.2), {"screener": "o2", "handler": "o1"})
    assert e.attrs["location"] == "top"
    spec, dur = horns_pnr(screen=False, dur=6.0)
    _, sc = scene_of(spec, dur, seed=132)
    assert C.detect_pnr_location(sc) == []


def stagger_scene(two=True):
    p = {"o1": (-5.3, 5.3), "o2": (2.8, 2.5), "o3": (4.0, 5.0) if two else (-2.0, 1.0), "o5": (-6.8, 0.4),
         "o4": [(0.0, 2.0, 0.5), (2.0, 2.0, 0.5), (4.0, 5.5, 6.5)]}
    return {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0


def test_stagger():
    spec, dur = stagger_scene(True)
    truth, sc = scene_of(spec, dur, seed=141)
    e = one(C.detect_stagger(sc))
    check(e, "stagger", t_closest(truth, "o4", "o2", 2.0, 4.0), {"user": "o4", "screener_1": "o2", "screener_2": "o3"})
    spec, dur = stagger_scene(False)
    _, sc = scene_of(spec, dur, seed=142)
    assert C.detect_stagger(sc) == []


def get_scene(dho=True):
    p = {"o1": [(0.0, 0.0, 7.6), (2.4, 0.0, 7.6), (3.5, 3.0, 7.3)], "o2": (3.5, 7.0), "o3": (-5.3, 5.3),
         "o4": (6.8, 0.4), "o5": (-6.8, 0.4)}
    if dho:
        ball = {"held": [(0.0, 2.0, "o1"), (2.4, 3.6, "o2"), (3.6, 6.0, "o1")], "flights": [(2.0, 2.4, "o1", "o2")]}
    else:
        p["o1"] = [(0.0, 0.0, 7.6), (2.4, 0.0, 7.6), (3.5, -3.0, 7.3)]
        ball = {"held": [(0.0, 2.0, "o1"), (2.4, 3.6, "o2"), (4.0, 6.0, "o1")],
                "flights": [(2.0, 2.4, "o1", "o2"), (3.6, 4.0, "o2", "o1")]}
    return {"actors": actors(p), "ball": ball}, 6.0


def test_get_dho_chain():
    spec, dur = get_scene(True)
    truth, sc = scene_of(spec, dur, seed=151)
    e = one(C.detect_get_dho_chain(sc), "get")
    check(e, "get", 2.0, {"passer": "o1", "receiver": "o2"})
    spec, dur = get_scene(False)
    _, sc = scene_of(spec, dur, seed=152)
    assert C.detect_get_dho_chain(sc) == []


def ucla_scene(screen=True):
    p = {"o1": [(0.0, 3.5, 7.0), (2.3, 3.5, 7.0), (4.0, 1.5, 0.8)], "o2": (6.3, 3.5), "o3": (-3.5, 7.0),
         "o4": (-6.3, 3.5), "o5": [(0.0, 0.0, 4.2), (1.0, 0.0, 4.2), (1.8, 2.2, 3.8)] if screen else (-2.5, 3.8)}
    ball = {"held": [(0.0, 2.0, "o1"), (2.4, 6.0, "o2")], "flights": [(2.0, 2.4, "o1", "o2")]}
    return {"actors": actors(p), "ball": ball}, 6.0


def test_ucla():
    spec, dur = ucla_scene(True)
    truth, sc = scene_of(spec, dur, seed=161)
    e = one(C.detect_ucla(sc))
    check(e, "ucla", t_closest(truth, "o1", "o5", 2.3, 4.0), {"cutter": "o1", "screener": "o5", "receiver": "o2"})
    spec, dur = ucla_scene(False)
    _, sc = scene_of(spec, dur, seed=162)
    assert C.detect_ucla(sc) == []


def flex_paths(t0=0.0, side=1, low=True):
    """One flex cycle with the ball on `side`: weak corner cutter o4 -> ball-side block past o5, then o3 down-screens o5."""
    s = side
    y_path = 0.6 if low else 3.0
    return {"o4": [(t0, -s * 6.7, 0.3), (t0 + 1.65, -s * 6.7, 0.3), (t0 + 3.6, s * 1.5, 0.8)],
            "o5": [(t0, -s * 2.0, y_path), (t0 + 3.15, -s * 2.0, y_path), (t0 + 4.6, -s * 3.0, 6.5)],
            "o3": (-s * 2.4, 3.0)}


def flex_scene(low=True):
    p = {"o1": (5.5, 4.5), "o2": (6.8, 0.4)}
    p.update(flex_paths(0.0, 1, low))
    return {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0


def test_flex():
    spec, dur = flex_scene(True)
    truth, sc = scene_of(spec, dur, seed=171)
    e = one(C.detect_flex(sc))
    check(e, "flex", t_closest(truth, "o4", "o5", 1.65, 3.6), {"cutter": "o4", "screener": "o5", "sts_screener": "o3"})
    spec, dur = flex_scene(False)
    _, sc = scene_of(spec, dur, seed=172)
    assert C.detect_flex(sc) == []


def ram_scene(quick=True):
    t_bs = 3.3 if quick else 5.6
    p = {"o4": (-1.0, 5.0), "o5": [(0.0, -2.0, 1.0), (1.25, -2.0, 1.0), (2.7, -0.6, 7.0)],
         "o1": [(0.0, 1.5, 8.0), (t_bs, 1.5, 8.0), (t_bs + 1.15, -3.0, 6.5)], "o2": (6.8, 0.4), "o3": (-6.8, 0.4)}
    return {"actors": actors(p), "ball": {"held": [(0.0, 8.0, "o1")]}}, 8.0


def test_ram():
    spec, dur = ram_scene(True)
    truth, sc = scene_of(spec, dur, seed=181)
    e = one(C.detect_ram(sc))
    check(e, "ram", t_closest(truth, "o5", "o4", 1.25, 2.7), {"ram_screener": "o4", "big": "o5", "handler": "o1"})
    spec, dur = ram_scene(False)
    _, sc = scene_of(spec, dur, seed=182)
    assert C.detect_ram(sc) == []


# --------------------------------------------------------------------------------------
# Special classes
# --------------------------------------------------------------------------------------
def test_iso():
    p = {"o1": [(0.0, 5.5, 4.5)], "o2": (-5.3, 5.3), "o3": (-6.8, 0.4), "o4": (0.0, 7.8), "o5": (6.8, 0.4)}
    ball = {"held": [(0.0, 1.0, "o4"), (1.4, 6.0, "o1")], "flights": [(1.0, 1.4, "o4", "o1")]}
    truth, sc = scene_of({"actors": actors(p), "ball": ball}, 6.0, seed=191)
    e = one(C.detect_iso(sc))
    check(e, "iso", 1.4, {"handler": "o1"})
    spec, dur = horns_pnr(dur=6.0)
    _, sc = scene_of(spec, dur, seed=192)
    assert C.detect_iso(sc) == []


def continuity_scene(complete=True):
    """Two flex cycles with a pass reversal (o1 right wing -> o2 top -> o5 left slot) between them (loop 1 F17: the
    old version 'dribbled' o1 11 m in 0.8 s). Cycle 1: o4 left corner -> right block past o5, o5 up past o3 (STS).
    Cycle 2: o4 right corner -> left block past o3, o3 up past o1 (STS). complete=False drops cycle 2's STS."""
    p = {"o1": [(0.0, 5.5, 4.5), (6.0, 5.5, 4.5), (7.6, 2.6, 3.2)], "o2": (0.0, 7.8),
         "o4": [(0.0, -6.7, 0.3), (1.6, -6.7, 0.3), (3.6, 1.5, 0.8), (4.0, 1.5, 0.8), (5.6, 6.7, 0.3), (7.4, 6.7, 0.3), (9.4, -1.5, 0.8)],
         "o5": [(0.0, -2.0, 0.6), (3.0, -2.0, 0.6), (4.6, -3.0, 6.5)],
         "o3": [(0.0, -2.4, 3.0), (5.0, -2.4, 3.0), (6.6, 2.0, 0.6)] + ([(9.0, 2.0, 0.6), (10.6, 3.0, 6.5)] if complete else [])}
    ball = {"held": [(0.0, 4.4, "o1"), (4.8, 5.6, "o2"), (6.0, 12.0, "o5")],
            "flights": [(4.4, 4.8, "o1", "o2"), (5.6, 6.0, "o2", "o5")]}
    return {"actors": actors(p), "ball": ball}, 12.0


def test_continuity():
    spec, dur = continuity_scene(True)
    truth, sc = scene_of(spec, dur, seed=201)
    e = one(C.detect_continuity(sc))
    check(e, "continuity", t_closest(truth, "o4", "o5", 1.6, 3.6), {"cutter_1": "o4"})
    assert e.attrs["cycle_count"] >= 2
    spec, dur = continuity_scene(False)
    _, sc = scene_of(spec, dur, seed=203)
    assert C.detect_continuity(sc) == []
    spec, dur = flex_scene(True)
    _, sc = scene_of(spec, dur, seed=202)
    assert C.detect_continuity(sc) == []


def motion_scene(active=True):
    """5-out: repeated off-ball down screens and cuts every ~1.5 s for 10 s, no ball screens."""
    p = {"o1": (0.0, 7.6), "o2": (5.3, 5.3), "o3": (-5.3, 5.3)}
    if active:
        p["o4"] = [(0.0, 6.8, 0.4), (1.0, 6.8, 0.4), (2.2, 2.4, 3.0), (3.0, 2.4, 3.0), (4.2, 6.6, 1.0), (5.5, 6.6, 1.0),
                   (6.7, 2.4, 3.0), (7.5, 2.4, 3.0), (8.7, 6.6, 1.0)]
        p["o5"] = [(0.0, -6.8, 0.4), (1.8, -6.8, 0.4), (3.0, -2.4, 3.0), (3.8, -2.4, 3.0), (5.0, -6.6, 1.0), (6.2, -6.6, 1.0),
                   (7.4, -2.4, 3.0), (8.2, -2.4, 3.0), (9.4, -6.6, 1.0)]
        p["o2"] = [(0.0, 5.3, 5.3), (2.6, 5.3, 5.3), (3.7, 2.8, 1.5), (5.0, 5.3, 5.3), (7.0, 5.3, 5.3), (8.1, 2.8, 1.5), (9.4, 5.3, 5.3)]
        p["o3"] = [(0.0, -5.3, 5.3), (4.0, -5.3, 5.3), (5.1, -2.8, 1.5), (6.4, -5.3, 5.3), (8.6, -5.3, 5.3), (9.7, -2.8, 1.5), (11.0, -5.3, 5.3)]
    else:
        p["o4"], p["o5"] = (6.8, 0.4), (-6.8, 0.4)
    return {"actors": actors(p), "ball": {"held": [(0.0, 12.0, "o1")]}}, 12.0


def test_motion():
    spec, dur = motion_scene(True)
    truth, sc = scene_of(spec, dur, seed=211)
    e = one(C.detect_motion(sc))
    first = min(x.t0 for x in C.build_lattice(sc) if x.kind == "CUT" or (x.kind.startswith("SCR.") and x.kind != "SCR.on"))
    check(e, "motion", _move_onset(truth, "o4", 0.5, 2.2))
    assert e.attrs["rate_per_10s"] >= 3.0 and first == e.t0
    spec, dur = motion_scene(False)
    _, sc = scene_of(spec, dur, seed=212)
    assert C.detect_motion(sc) == []


def test_style_measures():
    spec, dur = horns_pnr(dur=6.0)
    truth, sc = scene_of(spec, dur, seed=221)
    e = one(C.detect_style_measures(sc))
    al = one(C.detect_align_snapshot(sc))
    trig = al.attrs["trigger_f"] * DT
    check(e, "style", _true_snap(truth, "horns", max(0, trig - 0.5), trig + 1.0))
    assert e.attrs["per_10s"]["ball_screens"] > 0
    spec = {"actors": actors({"o1": (0.0, 16.0), "o2": (3.0, 18.0), "o3": (-3.0, 18.0), "o4": (5.0, 20.0), "o5": (-5.0, 20.0)}),
            "ball": {"held": [(0.0, 3.0, "o1")]}}
    _, sc = scene_of(spec, 3.0, seed=222)
    assert C.detect_style_measures(sc) == []


# --------------------------------------------------------------------------------------
# Sets, departures, naming, segmentation, live belief, storage
# --------------------------------------------------------------------------------------
def test_set_match_horns_pnr():
    spec, dur = horns_pnr(dur=7.0)
    truth, sc = scene_of(spec, dur, seed=231)
    e = one(C.detect_set_match(sc), "set")
    check(e, "set", t_closest(truth, "o1", "o2", 2.8, 4.2), {"s1": "o2", "handler": "o1"})
    assert e.attrs["set_code"] == "gen.horns_pnr" and e.attrs["P"] >= 0.4
    assert len(e.attrs["top_k"]) >= 2 and e.attrs["path"][0][1] is not None
    spec, dur = horns_pnr(screen=False, dur=7.0)
    _, sc = scene_of(spec, dur, seed=232)
    assert C.detect_set_match(sc) == []


def test_set_match_mirrored():
    spec, dur = horns_pnr(dur=7.0)
    for a in spec["actors"].values():
        a["wp"] = [(t, -x, y) for t, x, y in a["wp"]]
    truth, sc = scene_of(spec, dur, seed=233)
    e = one(C.detect_set_match(sc), "set")
    check(e, "set", t_closest(truth, "o1", "o2", 2.8, 4.2), {"s1": "o2"})
    assert e.attrs["set_code"] == "gen.horns_pnr"


def test_departure():
    spec, dur = horns_pnr(roll=False, dur=7.0)
    truth, sc = scene_of(spec, dur, seed=241)
    e = one(C.detect_departure(sc))
    assert e.attrs["template"] == "horns_pnr" and e.attrs["step"] == "read" and e.attrs["deleted"]
    # departure step deleted -> t0 = end of the last matched step (the screen event's window end)
    t_scr = t_closest(truth, "o1", "o2", 2.8, 4.2)
    assert e.kind == "departure" and t_scr - TOL <= e.t0 * DT <= t_scr + 1.0 and 0.0 < e.conf <= 1.0
    assert e.actors.get("s1") == "o2"
    spec, dur = horns_pnr(roll=True, dur=7.0)
    _, sc = scene_of(spec, dur, seed=242)
    assert [x for x in C.detect_departure(sc) if x.attrs["template"] == "horns_pnr"] == []


def test_compositional_name_and_storage():
    spec, dur = horns_pnr(dur=7.0)
    truth, sc = scene_of(spec, dur, seed=251)
    e = one(C.detect_compositional_name(sc))
    w = one([x for x in C.detect_set_window(sc) if x.attrs["segment_kind"] == "halfcourt"])
    assert e.kind == "name" and e.t0 == w.t0 and 0.0 < e.conf <= 1.0
    assert e.attrs["name"].startswith("Horns PnR"), e.attrs["name"]
    assert e.attrs["primary_name_kind"] in ("set", "probable_set")
    row = e.attrs["row"]
    assert row["set_code"] == "gen.horns_pnr"
    lat = [x for x in C.build_lattice(sc) if x.kind != "align" and w.start <= x.t0 <= w.end]
    assert row["action_sequence"] == list(range(len(lat)))  # every action kept, spacer and insertions included
    assert row["sequence_string"].startswith("ALIGN(horns)|")
    assert len(e.attrs["name"].split(" -> ")) <= 1 + C.PRM["compositional_name"]["max_tokens"] + 1
    # determinism: same lattice -> same string
    again = C.compositional_name(sc, lat)
    assert again == C.compositional_name(sc, lat)
    spec = {"actors": actors({"o1": (0.0, 16.0), "o2": (3.0, 18.0), "o3": (-3.0, 18.0), "o4": (5.0, 20.0), "o5": (-5.0, 20.0)}),
            "ball": {"held": [(0.0, 3.0, "o1")]}}
    _, sc = scene_of(spec, 3.0, seed=252)
    assert C.detect_compositional_name(sc) == []


def test_compositional_name_free_chunks():
    """No template accepted: the name is compositional ('Free -> ...' or alignment -> chunks), max 4 tokens."""
    # (the stagger_scene path is feasible: 6.6 m in 2.0 s)
    spec, dur = stagger_scene(True)
    _, sc = scene_of(spec, dur, seed=253)
    lat = [x for x in C.build_lattice(sc) if x.kind != "align"]
    name, toks, cost = C.compositional_name(sc, lat)
    assert name.startswith("Free -> ") and "Stagger" in name and "stagger" in toks


def test_segmentation():
    spec, dur = horns_pnr(dur=7.0)
    truth, sc = scene_of(spec, dur, seed=261)
    segs = C.detect_segments(sc)
    e = one([s for s in segs if s.attrs["set_code"] == "gen.horns_pnr"])
    check(e, "segment", t_closest(truth, "o1", "o2", 2.8, 4.2), {"s1": "o2"})
    spec = {"actors": actors({"o1": (0.0, 16.0), "o2": (3.0, 18.0), "o3": (-3.0, 18.0), "o4": (5.0, 20.0), "o5": (-5.0, 20.0)}),
            "ball": {"held": [(0.0, 3.0, "o1")]}}
    _, sc = scene_of(spec, 3.0, seed=262)
    assert C.detect_segments(sc) == []


def test_live_belief_commit():
    spec, dur = horns_pnr(dur=9.0)
    truth, sc = scene_of(spec, dur, seed=271)
    e = one(C.detect_live_belief(sc))
    # the read (ROLL) is confirmed 2.0 s after the screen moment; commit needs P >= 0.8 held 1.0 s
    t_scr = t_closest(truth, "o1", "o2", 2.8, 4.2)
    p = C.PRM["live_belief"]
    check(e, "commit", t_scr + p["confirm_delay_s"]["ROLL"] + p["commit_hold_s"], {"s1": "o2"})
    assert e.attrs["set_code"] == "gen.horns_pnr" and e.attrs["revisions"][0]["reason"] == "new_evidence"
    spec, dur = horns_pnr(screen=False, dur=9.0)
    _, sc = scene_of(spec, dur, seed=272)
    assert C.detect_live_belief(sc) == []


@pytest.mark.parametrize("iid", [i for i, it in C.ITEMS.items() if it.get("needs_data")])
def test_needs_data_items_return_empty(iid):
    spec, dur = horns_pnr(dur=6.0)
    _, sc = scene_of(spec, dur, seed=281)
    assert C.DETECTORS[iid](sc) == []


def test_detect_all_runs():
    spec, dur = horns_pnr(dur=7.0)
    _, sc = scene_of(spec, dur, seed=291)
    out = C.detect_all(sc)
    assert set(out) == set(C.DETECTORS)
    for evs in out.values():
        for e in evs:
            assert isinstance(e, mvlib.Event) and 0.0 <= e.conf <= 1.0 and e.start <= e.end


# --------------------------------------------------------------------------------------
# Loop 1 regressions: one block per failure of the independent tester's report (F1 .. F17). Scenarios marked
# 'tester' are copies of the tester's harness scenarios (scratchpad movement/test_composition/scenarios.py).
# --------------------------------------------------------------------------------------
SEEDS3 = (1000, 1001, 1002)


def _mirror(spec):
    out = {"actors": {k: dict(v, wp=[(t, -x, y) for t, x, y in v["wp"]]) for k, v in spec["actors"].items()}}
    if "ball" in spec:
        out["ball"] = spec["ball"]
    return out


def test_f17_all_author_scenarios_feasible():
    """F17: every author scenario keeps each minimum-jerk segment at or below an 8 m/s sprint (scene_of asserts it
    too); the old continuity 'dribble' (11 m in 0.8 s, 25.8 m/s) is gone."""
    builders = [horns_pnr(), horns_pnr(spain_s2=True), reset_scene(True), reset_scene(False), chicago_scene(True),
                chicago_scene(False), elevator_scene(True), floppy_scene(True), hammer_scene(True), pistol_scene(),
                drag_scene(True), drag_scene(False), stagger_scene(), get_scene(True), get_scene(False), ucla_scene(),
                flex_scene(), ram_scene(True), ram_scene(False), motion_scene(True), continuity_scene(True)]
    for spec, _ in builders:
        assert max(z[3] for z in peak_speeds(spec)) <= MAX_PEAK_MPS + 1e-9
    assert peak_speeds({"actors": actors({"o1": [(4.6, 5.5, 4.5), (5.4, -5.5, 4.5)]})})[0][3] > 25.0  # the old path


def _iverson_tester(cut):
    p = {"o1": (0.0, 7.6), "o2": (1.8, 4.2), "o3": (-1.8, 4.2), "o5": (-6.8, 0.4), "o4": cut}
    return {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0


def test_f1_iverson_fast_sprint():
    """F1 (high): a 7.5-8 m/s wing-to-wing cut crosses the middle 6 m in 0.80-0.87 s; duration_s now starts at 0.6 s.
    Tester 'iverson_fast_sprint' (and its mirror) was 0/10 at sigma 0.2 / 0.3."""
    assert C.PRM["iverson"]["duration_s"][0] == 0.6 and C.ITEMS["iverson"]["min_duration_s"] == 0.6
    spec, dur = _iverson_tester([(0.0, 6.2, 4.8), (1.5, 6.2, 4.8), (4.35, -5.8, 5.4)])  # tester: 4.3 s (8.05 m/s peak)
    for sp in (spec, _mirror(spec)):
        for seed in SEEDS3:
            truth, sc = scene_of(sp, dur, seed=seed)
            e = one(C.detect_iverson(sc))
            check(e, "iverson", t_closest(truth, "o4", "o2", 1.5, 4.35), {"cutter": "o4", "screener": "o2"})
            assert e.attrs["duration_s"] < 1.0
    # near-miss: over the top of the key (y 7) is still rejected by the crossing band
    spec, dur = _iverson_tester([(0.0, 6.0, 7.0), (1.5, 6.0, 7.0), (4.5, -6.0, 7.2)])
    for seed in SEEDS3:
        assert C.detect_iverson(scene_of(spec, dur, seed=seed)[1]) == []


def _drag_tester(kind):
    o1 = [(0.0, 0.0, 15.0), (2.3, 0.0, 8.0), (3.2, 0.0, 8.0), (4.2, -3.0, 6.2)]
    o5 = {"stop": [(0.0, 0.5, 17.5), (2.6, -0.8, 7.3), (3.6, -0.8, 7.3), (5.1, -0.3, 1.5)],
          "rolling": [(0.0, 0.5, 18.0), (3.3, -0.8, 7.2), (4.9, -0.3, 1.2)],
          "halfcourt": [(0.0, -1.5, 3.0), (1.5, -1.5, 3.0), (3.0, -0.8, 7.3), (3.6, -0.8, 7.3), (5.1, -0.3, 1.5)]}[kind]
    p = {"o1": o1, "o5": o5, "o2": [(0.0, 5.0, 14.0), (4.0, 6.8, 0.4)], "o3": [(0.0, -5.0, 14.0), (4.0, -6.8, 0.4)],
         "o4": [(0.0, 2.0, 16.0), (4.0, 5.3, 5.3)]}
    return {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0


def test_f2_drag_legal_and_rolling():
    """F2 (high): a legal drag (trailer stops 0.6 s) and a rolling drag were 0/10 under the v_y <= -3 m/s rule; the
    trailer-run test finds them, one event per pair (the earlier run-past contact is merged), and a half-court
    step-up screen is still not a drag."""
    assert "max_vy_mps" not in C.PRM["drag"] and C.PRM["drag"]["screen_r_m"] == [6.0, 9.0]
    for kind in ("stop", "rolling"):
        spec, dur = _drag_tester(kind)
        for seed in SEEDS3:
            truth, sc = scene_of(spec, dur, seed=seed)
            evs = [e for e in C.detect_drag(sc) if e.actors["handler"] == "o1" and e.actors["screener"] == "o5"]
            assert len(evs) == 1, [(e.t0 * DT, e.actors) for e in evs]
            check(evs[0], "drag", t_closest(truth, "o5", "o1", 2.5, 4.2))
            assert evs[0].attrs["drop_m"] >= C.PRM["drag"]["min_drop_m"]
    spec, dur = _drag_tester("halfcourt")
    for seed in SEEDS3:
        assert C.detect_drag(scene_of(spec, dur, seed=seed)[1]) == []


def _spain_tester(s2_path=None, s2_static=None, defense=False):
    p = {"o1": [(0.0, 0.0, 11.0), (1.2, 0.0, 7.6), (3.0, 0.0, 7.6), (4.2, 3.5, 6.0)],
         "o2": [(0.0, 1.8, 4.2), (1.6, 1.8, 4.2), (2.5, 0.8, 7.2), (3.6, 0.8, 7.2), (5.3, 0.3, 1.0)],
         "o3": s2_path if s2_static is None else s2_static, "o4": (6.7, 0.3), "o5": (-6.7, 0.3)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 8.0, "o1")]}}
    if defense:  # X2 guards o2, follows the roll and is held by o3's back screen at ~4.1 s
        spec["actors"]["x2"] = {"team": "D", "wp": [(0.0, 1.5, 3.5), (1.6, 1.5, 3.5), (2.5, 0.8, 6.4), (3.6, 0.8, 6.4),
                                                   (4.1, 0.6, 5.0), (5.0, 0.6, 4.7)]}
    return spec, 8.0


def test_f3_spain_static_post_is_not_a_back_screen():
    """F3 (high): a teammate standing at (1.4, 4.6) the whole possession was labelled Spain 10/10; s2 must arrive."""
    spec, dur = _spain_tester(s2_static=(1.4, 4.6))
    for seed in SEEDS3:
        assert C.detect_spain(scene_of(spec, dur, seed=seed)[1]) == []
    spec, dur = _spain_tester(s2_path=[(0.0, -5.3, 5.3), (2.0, -5.3, 5.3), (3.5, 0.9, 5.0)])
    for seed in SEEDS3:
        truth, sc = scene_of(spec, dur, seed=seed)
        e = one(C.detect_spain(sc))
        check(e, "spain", t_closest(truth, "o1", "o2", 2.8, 4.2), {"back_screener": "o3"})
        assert e.attrs["evidence_mode"] == "proxy"


def test_f3_contacts_conf_uses_gating_distance():
    """F3: _contacts computes its contact probability with the same contact_m that gates (proxy 1.5 m), so a
    1.35 m pass is a likely contact (it used to be scored against 1.2 m)."""
    spec = {"actors": actors({"o1": [(0.0, -3.0, 4.0), (1.0, -3.0, 4.0), (3.0, 3.0, 4.0)], "o2": (0.0, 5.35),
                              "o3": (6.8, 0.4), "o4": (-6.8, 0.4), "o5": (0.0, 9.0)})}
    _, sc = scene_of(spec, 4.0, seed=5, sigma=0.05)
    c = C._contacts(sc, "o1", 0, sc.n - 1, {"contact_m": 1.5})
    assert c and c[0][0] == "o2" and c[0][2] > 0.5
    assert C._contacts(sc, "o1", 0, sc.n - 1, {"contact_m": 1.2}) == []


def _dho_tester(kind):
    if kind == "chain":
        p = {"o1": [(0.0, 0.0, 8.0), (1.5, 2.4, 7.6), (2.5, 1.0, 6.0)], "o2": [(0.0, 3.4, 5.0), (1.2, 3.0, 7.2), (2.0, 3.6, 7.6), (3.2, 5.6, 5.6)],
             "o3": [(0.0, 6.8, 0.4), (2.6, 6.4, 3.0), (3.6, 5.8, 5.0), (4.6, 4.0, 6.4)], "o4": (-5.3, 5.3), "o5": (-6.8, 0.4)}
        ball = {"held": [(0.0, 1.6, "o1"), (1.6, 3.6, "o2"), (3.6, 6.0, "o3")]}
    else:  # DHO on the right, then a pass to the left and an unrelated DHO there
        p = {"o1": [(0.0, 0.0, 8.0), (1.5, 2.4, 7.6), (2.5, 1.0, 6.0)], "o2": [(0.0, 3.4, 5.0), (1.2, 3.0, 7.2), (2.0, 3.6, 7.6)],
             "o4": [(0.0, -5.3, 5.3), (2.6, -5.3, 5.3), (3.6, -4.2, 7.0), (4.3, -4.0, 7.0)],
             "o5": [(0.0, -6.8, 0.4), (2.4, -6.8, 0.4), (4.1, -4.8, 6.6), (5.0, -3.0, 6.8)], "o3": (6.8, 0.4)}
        ball = {"held": [(0.0, 1.6, "o1"), (1.6, 2.4, "o2"), (3.0, 4.3, "o4"), (4.3, 6.0, "o5")], "flights": [(2.4, 3.0, "o2", "o4")]}
    return {"actors": actors(p), "ball": ball}, 6.0


def test_f4_dho_chain_needs_continuity():
    """F4 (medium): two unrelated DHOs within 5 s were a dho_chain 10/10; the receiver of DHO k must give DHO k+1."""
    spec, dur = _dho_tester("indep")
    for seed in SEEDS3:
        assert [e for e in C.detect_get_dho_chain(scene_of(spec, dur, seed=seed)[1]) if e.kind == "dho_chain"] == []
    spec, dur = _dho_tester("chain")
    for seed in SEEDS3:
        e = one(C.detect_get_dho_chain(scene_of(spec, dur, seed=seed)[1]), "dho_chain")
        check(e, "dho_chain", 1.6, {"giver_1": "o1", "giver_2": "o2", "receiver": "o3"})
        assert e.attrs["chain_length"] == 2


def _stagger_tester():
    p = {"o1": (-5.3, 5.3), "o2": (2.2, 1.6), "o3": (3.4, 4.2), "o5": (4.6, 6.6),
         "o4": [(0.0, 1.0, 0.0), (1.5, 1.0, 0.0), (4.0, 5.8, 8.2)]}
    return {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0


def test_f5_f14_triple_stagger_once_and_not_a_flare():
    """F5 (medium): a triple stagger was also emitted as its 2-screen suffix (precision 0.50). F14 (low): its exit
    was labelled 'flare' from the ball angle; flare is now geometric."""
    spec, dur = _stagger_tester()
    for sp in (spec, _mirror(spec)):
        for seed in SEEDS3:
            truth, sc = scene_of(sp, dur, seed=seed)
            evs = [e for e in C.detect_stagger(sc) if e.actors["user"] == "o4"]
            assert len(evs) == 1, [e.actors for e in evs]
            check(evs[0], "stagger", t_closest(truth, "o4", "o2", 1.5, 4.0), {"screener_1": "o2", "screener_2": "o3"})
            assert evs[0].attrs["triple"] and evs[0].attrs["exit"] != "flare"


def test_f14_flare_geometry():
    """F14: a user who turns outward along the baseline off a screener is a flare; one who runs straight up is not."""
    flare = {"o4": [(0.0, 0.5, 0.6), (1.0, 0.5, 0.6), (2.0, 1.4, 3.2), (3.4, 6.6, 1.2)], "o2": (1.9, 3.5),
             "o1": (-5.3, 5.3), "o3": (-6.8, 0.4), "o5": (0.0, 8.0)}
    up = dict(flare, o4=[(0.0, 1.9, 0.5), (1.0, 1.9, 0.5), (2.6, 2.1, 6.2)])
    for paths, want in ((flare, True), (up, False)):
        _, sc = scene_of({"actors": actors(paths), "ball": {"held": [(0.0, 4.0, "o1")]}}, 4.0, seed=7, sigma=0.1)
        kinds = {e.kind for e in C.primitives(sc) if e.actors.get("user") == "o4" and e.actors.get("screener") == "o2"}
        assert kinds, "expected a screen"
        assert ("SCR.flare" in kinds) == want, kinds


def test_f6_flex_corner_start_behind_the_line():
    """F6 (medium): the weak-corner start used one frame; a cutter standing 0.1-0.3 m behind the corner line flipped
    inside on noise. Any frame of corner_lookback_s now counts (tester 'flex_fast', corner at x = 6.7)."""
    p = {"o1": (5.5, 4.5), "o2": (6.8, 0.4), "o4": [(0.0, -6.7, 0.3), (1.4, -6.7, 0.3), (3.4, 1.6, 0.7)],
         "o5": [(0.0, -2.0, 0.6), (3.0, -2.0, 0.6), (4.6, -2.8, 6.8)], "o3": (-2.3, 3.2)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}
    hits = 0
    for seed in range(1000, 1006):
        truth, sc = scene_of(spec, 6.0, seed=seed)
        evs = [e for e in C.detect_flex(sc) if e.actors["cutter"] == "o4"]
        hits += bool(evs)
    assert hits >= 5  # 10/10 at sigma 0.2 and 8/10 at 0.3 in the tester's sweep after the fix
    assert C.PRM["flex"]["corner_lookback_s"] == 0.5


def _shot_tester(kind):
    p = {"o1": [(0.0, 0.0, 11.0), (1.2, 0.0, 7.6), (3.0, 0.0, 7.6), (4.2, 3.5, 6.0)],
         "o2": [(0.0, 1.8, 4.2), (1.6, 1.8, 4.2), (2.5, 0.8, 7.2), (3.6, 0.8, 7.2), (5.3, 0.3, 1.0)],
         "o3": (-1.8, 4.2), "o4": (6.7, 0.3), "o5": (-6.7, 0.3)}
    if kind == "shot":
        spec = {"actors": actors(p), "ball": {"held": [(0.0, 5.0, "o1")], "flights": [(5.0, 6.0, "o1", "xr")]}}
        spec["actors"]["xr"] = {"team": "D", "wp": [(0.0, 0.0, 0.2)]}
        return spec, 8.0
    if kind == "passes":  # ball reversal top -> wing -> top -> other wing in 1-4 high, no screens
        p = {"o1": (0.0, 7.6), "o2": (1.8, 4.2), "o3": (-1.8, 4.2), "o4": (6.0, 5.0), "o5": (-6.0, 5.0)}
        ball = {"held": [(0.0, 2.0, "o1"), (2.6, 3.6, "o4"), (4.2, 5.2, "o1"), (5.8, 8.0, "o5")],
                "flights": [(2.0, 2.6, "o1", "o4"), (3.6, 4.2, "o4", "o1"), (5.2, 5.8, "o1", "o5")]}
        return {"actors": actors(p), "ball": ball}, 8.0
    return {"actors": actors(p), "ball": {"held": [(0.0, 8.0, "o1")]}}, 8.0


def test_f7_shot_past_roller_closes_window():
    """F7 (medium): the roller under the rim 'held' the arriving shot, so the shot proxy failed (clip_end 8/10).
    The catch rule and the shot grace close the window with shot_proxy; the ball in flight is nobody's."""
    spec, dur = _shot_tester("shot")
    for seed in SEEDS3:
        _, sc = scene_of(spec, dur, seed=seed)
        w = one([x for x in C.detect_set_window(sc) if x.attrs["segment_kind"] == "halfcourt"])
        assert w.attrs["close_reason"] == "shot_proxy", w.attrs
        assert 5.0 <= w.end * DT <= 6.1
        H = C._H(sc)
        assert all(H[t] != "o2" for t in range(f(5.3), f(5.9)))  # flight past the roller is not a catch


def test_f8_window_conf_not_zero_at_clip_edge():
    """F8 (medium): a window opening at clip frame 0 had conf 0 (edge factor of the boundary frame), which zeroed
    the 'name' and 'style' confs. The edge factor is now read at the window midpoint."""
    spec, dur = _shot_tester("passes")
    _, sc = scene_of(spec, dur, seed=1000)
    w = one(C.detect_set_window(sc))
    assert w.start == 0 and w.conf > 0.5
    assert one(C.detect_style_measures(sc)).conf > 0.5
    assert one(C.detect_compositional_name(sc)).conf > 0.0


def test_f9_dho_with_long_air_time_on_short_travel():
    """F9 (medium): at sigma 0.5 the holder flicker pushes a hand-off's air time past 0.3 s and the transfer was
    dropped (travel < 1 m: not a PASS either). A short-travel transfer with a close gap stays a DHO up to
    dho_max_air_short_travel_s, the air time lowering its conf; a long one is still neither."""
    p = {"o1": (2.0, 7.5), "o2": (2.8, 7.5), "o3": (-5.3, 5.3), "o4": (6.8, 0.4), "o5": (-6.8, 0.4)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 2.0, "o1"), (2.0, 4.0, "o2")]}}
    lp = C.PRM["event_lattice"]
    for gap_f, want in ((14, True), (25, False)):  # 0.47 s and 0.83 s of holder flicker around the hand-off
        _, sc = scene_of(spec, 4.0, seed=3, sigma=0.1)
        H = np.array([None] * sc.n, dtype=object)
        H[:f(2.0) - gap_f // 2] = "o1"
        H[f(2.0) + gap_f - gap_f // 2:] = "o2"
        C._cache(sc)["holder"] = H
        ev, _ = C._transfer_events(sc, lp)
        d = [e for e in ev if e.kind == "DHO"]
        assert bool(d) == want and not [e for e in ev if e.kind == "PASS"]
        if want:
            assert lp["dho_max_air_s"] < d[0].attrs["air_s"] <= lp["dho_max_air_short_travel_s"]
            assert d[0].attrs["travel_m"] < lp["pass_min_flight_m"] and 0.0 < d[0].conf < lp["p_dho"]


def test_f9_chicago_handoff_at_high_noise():
    """F9 (medium), actual cause: at sigma_p 0.5 smoother lag inflates the smoothed giver-receiver gap at the
    hand-off (true 0.64 m reads 1.4-1.9 m) past dho_max_gap_m, so the DHO and the Chicago vanished (tester: 4/10 and
    1/10 mirrored). Short-travel transfers get the noise-widened gap gate (dho_gap_noise_k x sigma_dist). Tester
    scenario 'chicago_dribble_handoff'; seeds 1000, 1001, 1003 failed before."""
    p = {"o1": (-5.3, 5.3), "o2": (5.6, 2.6), "o3": (-1.8, 1.0),
         "o4": [(0.0, 6.7, 0.3), (2.0, 6.7, 0.3), (3.6, 4.7, 6.2), (4.2, 3.1, 7.2), (5.2, 4.5, 3.5)],
         "o5": [(0.0, 0.0, 7.8), (3.4, 0.0, 7.8), (4.2, 2.6, 7.6), (5.2, 0.5, 7.8)]}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 4.2, "o5"), (4.2, 7.5, "o4")]}}
    for seed in (1000, 1001, 1003):
        truth, sc = scene_of(spec, 7.5, seed=seed, sigma=0.5)
        d = [e for e in C.primitives(sc) if e.kind == "DHO" and e.actors == {"giver": "o5", "receiver": "o4"}]
        assert d and d[0].attrs["gap_m"] > C.PRM["event_lattice"]["dho_max_gap_m"]
        e = one(C.detect_chicago(sc))
        check(e, "chicago", t_closest(truth, "o4", "o2", 2.0, 3.6), {"user": "o4", "screener": "o2", "giver": "o5"})


def test_f10_calibration_tables_and_application():
    """F10 (medium): component confs are calibrated per kind and noise band (isotonic, V0 sim); raw conf is kept."""
    tabs = C.PRM["calibration"]["tables"]
    kinds = {"iverson", "zipper", "chicago", "spain", "elevator", "floppy", "hammer", "pistol", "drag", "stagger", "get",
             "dho_chain", "ucla", "flex", "ram"}
    assert kinds <= set(tabs)
    for k in kinds:
        for band in ("low", "mid", "high"):
            kn = tabs[k][band]
            xs, ys = [z[0] for z in kn], [z[1] for z in kn]
            assert xs == sorted(xs) and ys == sorted(ys) and all(0.0 < y < 1.0 for y in ys)
    assert C.calibrate("drag", 0.97, "high") < C.calibrate("drag", 0.99, "mid")  # sigma 0.5 drags are less reliable
    assert C.calibrate("not_a_kind", 0.42, "low") == 0.42
    assert C.fit_isotonic([(0.2, 0), (0.3, 0), (0.8, 1), (0.9, 1)]) == [[0.25, 0.25], [0.85, 0.75]]
    assert len(C.fit_isotonic([(0.5 + i / 100, 1) for i in range(20)])) == 1  # all-correct = one block
    assert C.PRM["spain"]["proxy_conf_factor"] == 0.96
    spec, dur = stagger_scene(True)
    _, sc = scene_of(spec, dur, seed=141)
    e = one(C.detect_stagger(sc))
    assert e.attrs["calibration_band"] == "mid" and e.conf == C.calibrate("stagger", e.attrs["conf_raw"], "mid")
    assert C.sigma_band(scene_of(spec, dur, seed=141, sigma=0.5)[1]) == "high"


def test_f11_pnr_location_probabilities():
    """F11 (low): location from the median screener position, with label probabilities and top-2 alternatives."""
    spec, dur = horns_pnr(dur=6.0)
    _, sc = scene_of(spec, dur, seed=131)
    e = one(C.detect_pnr_location(sc))
    probs = dict(e.attrs["location_probs"])
    assert abs(sum(probs.values()) - 1.0) < 1e-9 and e.attrs["location"] == "top" and probs["top"] >= 0.5
    assert e.attrs["location_alternatives"][0] == e.attrs["location_probs"][0][0]
    assert C.detect_pnr_location(sc)[0].attrs["location_probs"] == e.attrs["location_probs"]  # deterministic


def test_f12_min_duration_swap_window_prefilter_single_source():
    """F12 (low): min_duration_s is enforced; a swap with a long ambiguity window does not re-bind; the exact
    prefilter returns the all-deleted path; duplicated parameters are gone."""
    short = mvlib.Event("stagger", {"user": "o1"}, 10, 10, 12, 0.9, {})
    assert C._dedup([short]) == []
    sc = _flat_scene()
    chain = [("o1", "o2", 100), ("o2", "o3", 130), ("o3", "o4", 160), ("o4", "o5", 190)]
    sw = {"o3": "o4", "o4": "o3"}
    lat = [_fake("PASS", {"passer": sw.get(a, a) if t >= 150 else a, "receiver": sw.get(b, b) if t >= 150 else b}, t)
           for a, b, t in chain]
    ok = C.match_template(sc, T4, lat, swaps=[(150, "o3", "o4", 0.5)])
    late = C.match_template(sc, T4, lat, swaps=[(150, "o3", "o4", C.PRM["role_binding"]["swap_window_s"] + 1.0)])
    assert ok.get("swap") and not late.get("swap") and late["frac_required"] < 1.0
    r = C.match_template(sc, T4, [_fake("CUT", {"cutter": "o1"}, 50)])
    assert r.get("prefiltered") and r["frac_required"] == 0.0 and abs(r["C"] - 4 * C.PRM["matcher"]["w_required"]) < 1e-9
    assert not C.match_template(sc, T4, lat).get("prefiltered")
    assert C.ITEMS["time_base"]["params"] == {} and C.ITEMS["template_format"]["params"] == {}
    assert "binding_disagree_cost" not in C.PRM["role_binding"] and "max_bindings_per_template" not in C.PRM["role_binding"]
    assert "p_display" not in C.PRM["name_precedence"] and "p_probable" not in C.PRM["name_precedence"]
    assert C.name_precedence({"accepted": True, "P": C.PRM["probability"]["p_display"]}, 1.0) == "set"


def test_f13_constants_live_in_the_yaml(monkeypatch):
    """F13 (low): former hard-coded constants are read from the YAML (changing a parameter changes behaviour)."""
    need = {"event_lattice": ["stat_logistic_width", "scr_dir_half_s", "on_ball_frames", "contact_bridge_frames", "cross_dx_ratio",
                              "cross_max_y_m", "flare_min_turn_deg", "drive_backtrack_vr_mps", "catch_max_ball_mps", "hold_cert_frames"],
            "mirror": ["dead_band_m"], "spain": ["matchup_lookback_s", "react_window_s", "arrive_min_m", "arrive_from_s"],
            "ucla": ["catch_within_s", "cut_lead_s"], "flex": ["sts_dir_window_s", "corner_lookback_s"], "stagger": ["exit_after_s"],
            "iso": ["clear_out_after_s"], "motion": ["conf_scale"], "reset": ["handler_window_s"], "zipper": ["block_lookback_s"]}
    for iid, keys in need.items():
        for k in keys:
            assert k in C.PRM[iid], (iid, k)
    spec = {"actors": actors({"o1": (0.5, 7.6), "o2": (3.0, 3.0), "o3": (-3.0, 3.0), "o4": (6.0, 1.0), "o5": (-6.0, 1.0)}),
            "ball": {"held": [(0.0, 2.0, "o1")]}}
    _, sc = scene_of(spec, 2.0, seed=9, sigma=0.05)
    assert C._ball_side(sc, 30) == 0  # |x_ball| 0.5 < 0.9
    monkeypatch.setitem(C.PRM["mirror"], "dead_band_m", 0.2)
    assert C._ball_side(sc, 30) == 1


def test_f15_spain_defender_mode_at_low_noise():
    """F15 (low): the defender reaction was read at the minimum distance, late in the stuck phase, so defender mode
    never fired at sigma 0.05. Pre / post mean velocities around the in-contact frames now find the hold."""
    spec, dur = _spain_tester(s2_path=[(0.0, -1.8, 4.2), (1.5, -1.8, 4.2), (2.8, 0.9, 5.0)], defense=True)
    for seed in SEEDS3:
        for sigma in (0.05, 0.3):
            e = one(C.detect_spain(scene_of(spec, dur, seed=seed, sigma=sigma)[1]))
            assert e.attrs["evidence_mode"] == "defender" and e.actors["back_screener"] == "o3"


def test_f16_no_reset_when_the_team_stands_after_a_pnr():
    """F16 (low): after a PnR (roller at the rim, handler at r 6.9 m) the team stood still and a re-ALIGN fired a
    reset, adding a 'Free' window 9/10. A re-ALIGN now needs the ball back out or pulled away from the rim."""
    spec, dur = _shot_tester("none")
    for seed in SEEDS3:
        _, sc = scene_of(spec, dur, seed=seed, sigma=0.2)
        assert C.detect_reset(sc) == []
        assert len([w for w in C.detect_set_window(sc) if w.attrs["segment_kind"] == "halfcourt"]) == 1


# --------------------------------------------------------------------------------------
# Loop 2 regression tests (confirmer verdict on loop 1: R1 regression, R2 / R5 still failing, R3 / R4 drag)
# --------------------------------------------------------------------------------------
def _pistol_dho_tester():
    """The tester's pistol_dho path: o1 hands off to the wing o2 at 3.0 s; o2 keeps running up past the hand-off."""
    p = {"o1": [(0.0, 0.5, 11.0), (2.2, 3.8, 7.6), (3.0, 4.0, 7.0)],
         "o2": [(0.0, 6.7, 0.4), (1.4, 6.7, 0.4), (3.0, 5.0, 6.6), (3.8, 4.4, 8.4)],
         "o3": (-6.8, 0.4), "o4": (-5.3, 5.3), "o5": (0.0, 7.4)}
    return {"actors": actors(p), "ball": {"held": [(0.0, 3.0, "o1"), (3.0, 5.0, "o2")]}}, 5.0


def test_r1_pistol_dho_action_at_the_giver(monkeypatch):
    """R1 (loop 1 regression): the DHO receiver sits at r 8.5-8.7 m at t0 (past action_r_m's 8.5 m), so pistol_dho fell
    to 5/10 at sigma 0.3. The action is measured at the giver; these seeds were misses and are found now, and
    measuring at the receiver loses them again."""
    assert C.PRM["pistol"]["dho_location_actor"] == "giver" and C.PRM["pistol"]["action_r_m"] == [6.5, 8.5]
    spec, dur = _pistol_dho_tester()
    scenes = [scene_of(spec, dur, seed=seed) for seed in (1001, 1006, 1009)]
    for _, sc in scenes:
        e = one(C.detect_pistol(sc))
        check(e, "pistol", 3.0, {"handler": "o1", "wing": "o2", "big": "o5"})
        assert e.attrs["action_kind"] == "dho"
    monkeypatch.setitem(C.PRM["pistol"], "dho_location_actor", "receiver")
    assert sum(bool(C.detect_pistol(sc)) for _, sc in scenes) == 0


def test_r3_drag_handler_holds_the_ball():
    """R3 (loop 1 side effect): at sigma 0.5 the holder flickered to the trailer while the two passed within 0.2 m, and
    drag fired with the roles swapped (screener = ball handler) on a legal drag and on a half-court step-up screen.
    The handler must out-hold the screener over +- holder_window_s."""
    assert C.PRM["drag"]["holder_window_s"] == 1.0
    for kind, seed in (("stop", 1008), ("halfcourt", 1003)):
        spec, dur = _drag_tester(kind)
        _, sc = scene_of(spec, dur, seed=seed, sigma=0.5)
        assert [e for e in C.detect_drag(sc) if e.actors["screener"] == "o1"] == []
    spec, dur = _drag_tester("stop")
    truth, sc = scene_of(spec, dur, seed=1008, sigma=0.5)
    check(one(C.detect_drag(sc)), "drag", t_closest(truth, "o5", "o1", 2.5, 4.2), {"handler": "o1", "screener": "o5"})


def test_r4_drag_split_keeps_the_screen_not_the_run_past(monkeypatch):
    """R4: the trailer passes the handler ~1 s before the screen; both approaches form one contact interval whose
    global minimum was the run-past (t0 0.2-1.0 s early). The interval is split at noise-significant minima and the
    pair merge keeps the last approach."""
    d = np.array([2.0, 1.0, 0.42, 0.6, 0.96, 0.8, 0.65, 0.9, 1.5])
    assert C._distance_minima(d, 0, 8, 0.24) == [2, 6]
    assert C._distance_minima(d, 0, 8, 0.6) == [2]  # rise below the threshold: one approach
    assert C._distance_minima(np.array([1.0, 0.5, 0.52, 0.49, 0.51, 1.0]), 0, 5, 0.2) == [3]  # noise wobble: no split
    spec, dur = _drag_tester("rolling")
    spec = _mirror(spec)
    truth, sc = scene_of(spec, dur, seed=1003, sigma=0.5)
    t_true = t_closest(truth, "o5", "o1", 2.5, 4.2)
    check(one(C.detect_drag(sc)), "drag", t_true, {"handler": "o1", "screener": "o5"})
    monkeypatch.setitem(C.PRM["drag"], "split_rise_min_m", 99.0)  # no split: the run-past wins
    assert abs(one(C.detect_drag(sc)).t0 * DT - t_true) > TOL


def _pnr_side_tester():
    p = {"o1": [(0.0, 5.5, 6.5), (2.5, 5.5, 6.5), (3.8, 2.8, 4.5)], "o2": [(0.0, 2.0, 1.0), (1.0, 2.0, 1.0), (2.4, 4.8, 5.4)],
         "o3": (-6.8, 0.4), "o4": (-5.3, 5.3), "o5": (6.8, 0.4)}
    return {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}, 6.0


def test_r2_pnr_location_alternative_at_high_noise(monkeypatch):
    """R2: a side PnR 0.2-0.35 m from the side / slot boundary read 'slot' at p 0.91 with no 'side' alternative at
    sigma 0.5: the 0.6 s median errs 1.2-1.7 x sigma_track. With the per-band inflation the truth is an alternative;
    without it, it is not."""
    assert C.PRM["pnr_location"]["loc_sigma_inflation"] == {"low": 1.2, "mid": 1.3, "high": 1.7}
    spec, dur = _pnr_side_tester()
    _, sc = scene_of(spec, dur, seed=1008, sigma=0.5)
    assert C.sigma_band(sc) == "high"
    e = one(C.detect_pnr_location(sc))
    assert e.attrs["location"] == "slot" and "side" in e.attrs["location_alternatives"]
    assert abs(sum(dict(e.attrs["location_probs"]).values()) - 1.0) < 1e-9
    monkeypatch.setitem(C.PRM["pnr_location"], "loc_sigma_inflation", {"low": 1.0, "mid": 1.0, "high": 1.0})
    assert "side" not in one(C.detect_pnr_location(sc)).attrs["location_alternatives"]


def test_r5_known_limits_are_recorded():
    """R5: the sigma 0.5 recall limits loops 1-2 did not change are recorded in sim_validation (not hidden)."""
    kl = C.DOC["sim_validation"]["known_limits_sigma_0_5"]
    for k in ("elevator", "live_belief", "departure", "set_match", "floppy", "ucla", "pnr_location", "continuity"):
        assert 0.0 <= kl[k]["R"] <= 1.0 and 0.0 <= kl[k]["P"] <= 1.0


# --------------------------------------------------------------------------------------
# Loop 4: failure modes found on real tracking (SportVU 2015-16), rebuilt as synthetic scenes
# --------------------------------------------------------------------------------------
def _with_defense(spec, dfn):
    """Add defenders {id: (x, y) | [(t, x, y), ...]} (team 'D') to a scene spec."""
    for k, v in dfn.items():
        spec["actors"][k] = {"team": "D", "wp": [(0.0, v[0], v[1])] if isinstance(v, tuple) else v}
    return spec


def _shift_y(spec, dy):
    """Translate every waypoint of a spec by dy metres along y (away from the rim for dy > 0)."""
    out = {"actors": {k: dict(a, wp=[(t, x, y + dy) for t, x, y in a["wp"]]) for k, a in spec["actors"].items()}}
    if "ball" in spec:
        out["ball"] = spec["ball"]
    return out


def _steal_scene():
    """Offense possession (o1 at the top, 0-4 s), d1 steals and dribbles away (4.4-8.0 s), offense back (8.5-13 s)."""
    p = {"o1": [(0.0, 0.0, 8.0), (4.0, 0.5, 7.6), (8.5, 0.5, 8.0), (13.0, 0.0, 7.6)], "o2": (5.3, 5.3), "o3": (-5.3, 5.3),
         "o4": (6.6, 0.6), "o5": [(0.0, -6.6, 0.6), (6.0, -6.6, 0.6), (9.0, -3.0, 2.0), (10.5, -6.6, 0.6)]}
    d = {"d1": [(0.0, 0.0, 6.6), (4.0, 0.3, 6.6), (4.4, 0.4, 7.4), (6.2, 0.0, 12.0), (8.0, 0.4, 8.6), (13.0, 0.0, 6.6)],
         "d2": (4.4, 4.6), "d3": (-4.4, 4.6), "d4": (5.6, 1.0), "d5": (-5.6, 1.0)}
    ball = {"held": [(0.0, 4.0, "o1"), (4.4, 8.0, "d1"), (8.5, 13.0, "o1")], "flights": [(4.0, 4.4, "o1", "d1"), (8.0, 8.5, "d1", "o1")]}
    return _with_defense({"actors": actors(p), "ball": ball}, d), 13.0


def test_l1_l2_possession_split():
    """L1/L2: a clock-running stretch holds possessions of both teams; while a defender holds the ball there is no
    offensive holder, the clip is cut there, and detectors run per offense span (events come back in clip frames)."""
    spec, dur = _steal_scene()
    for seed in SEEDS3:
        _, sc = scene_of(spec, dur, seed=seed, sigma=0.15)
        H = C._H(sc)
        assert all(H[f(t)] is None for t in (5.0, 6.0, 7.0))  # d1 holds: no offensive holder (L1)
        spans = C.possession_spans(sc)
        assert len(spans) == 2 and spans[0][1] * DT < 5.0 and spans[1][0] * DT > 7.0, spans
        res = C.detect_all(sc)
        for w in res["set_window"]:
            assert not (w.start * DT < 6.0 < w.end * DT), (w.start * DT, w.end * DT)  # no window across the steal
    spec, dur = horns_pnr()
    _, sc = scene_of(_with_defense(spec, {"d1": (0.0, 6.4), "d2": (1.6, 3.4)}), dur, seed=5)
    assert C.possession_spans(sc) == [(0, sc.n - 1)]  # a single possession runs unchanged


def test_l3_offense_retreat_yields_no_window():
    """L3: the offense itself carries the ball back over half court (SportVU: a stretch whose attacked end belongs to
    the other team) - no set window; with the retreat rule disabled the same scene opens a half-court window."""
    p = {"o1": [(0.0, 0.0, 8.0), (2.0, 0.0, 10.0), (5.0, 0.0, 20.0)], "o2": [(0.0, 5.3, 5.3), (0.5, 5.3, 5.3), (2.0, 2.0, 2.0)],
         "o3": (-5.3, 5.3), "o4": (6.6, 0.6), "o5": (-6.6, 0.6)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}
    for seed in SEEDS3:
        _, sc = scene_of(spec, 6.0, seed=seed)
        assert C.detect_set_window(sc) == []
        assert C.detect_set_window(sc, retreat_holder_s=-1.0)  # the scene is a window without L3


def test_l4_l5_iso_needs_a_half_court_attacking_hold():
    """L4/L5: a post-up hold (catch inside post_max_r_m) and a hold 3 m behind the arc are not isolations; the same
    clear-out with the handler on the wing (test_iso) is one."""
    base = {"o2": (-5.3, 5.3), "o3": (-6.8, 0.4), "o4": (0.0, 7.8), "o5": (-3.0, 8.0)}
    ball = {"held": [(0.0, 1.0, "o4"), (1.4, 6.0, "o1")], "flights": [(1.0, 1.4, "o4", "o1")]}
    for spot, prm in (((3.0, 1.5), {"post_max_r_m": 0.0}), ((4.0, 9.0), {"attack_max_d3_m": 99.0})):
        spec = {"actors": actors(dict(base, o1=[(0.0, *spot)])), "ball": ball}
        for seed in SEEDS3:
            _, sc = scene_of(spec, 6.0, seed=seed)
            assert C.detect_iso(sc) == []
            assert [e.actors["handler"] for e in C.detect_iso(sc, **prm)] == ["o1"]  # only the loop-4 gate rejects it


def _sprint_in_screen():
    """The screener sprints in from the wing and plants only as the handler comes off (SportVU: screener speed
    2-4 m/s until the handler's closest approach, 0.3-0.6 m/s for 0.3-0.5 s after it, then rolls)."""
    p = {"o1": [(0.0, -1.5, 8.0), (2.0, -1.5, 8.0), (3.4, 3.0, 6.2)],
         "o2": [(0.0, 4.5, 6.0), (1.2, 4.5, 6.0), (2.55, 0.6, 7.6), (3.1, 0.6, 7.6), (4.6, 0.6, 2.0)],
         "o3": (-5.3, 5.3), "o4": (6.6, 0.6), "o5": (-6.6, 0.6)}
    return {"actors": actors(p), "ball": {"held": [(0.0, 5.0, "o1")]}}, 5.0


def test_l6_l8_screener_planting_as_the_handler_passes():
    """L6/L8: precise tracking (sigma 0.1-0.15 m) of a screener who plants late: P(set) uses the physical speed bound
    and the set window may end after the closest approach; without both the ball screen is missed."""
    spec, dur = _sprint_in_screen()
    old = {"scr_set_max_mps": 0.0, "scr_set_lookahead_s": 0.0}
    for sig in (0.1, 0.15, 0.3):
        for seed in SEEDS3:
            _, sc = scene_of(spec, dur, seed=seed, sigma=sig)
            ons = [e for e in C.primitives(sc) if e.kind == "SCR.on"]
            assert [(e.actors["screener"], e.actors["user"]) for e in ons] == [("o2", "o1")], (sig, seed)
    for seed in SEEDS3:
        _, sc = scene_of(spec, dur, seed=seed, sigma=0.1)
        assert not [e for e in C.primitives(sc, **old) if e.kind == "SCR.on"]  # loop-3 rule: missed


def test_l7_ball_screen_only_in_the_half_court_away_from_the_rim():
    """L7: the horns ball screen moved 13 m back (backcourt bring-up traffic) or 5.5 m toward the rim (a rebound
    scrum) is no on-ball screen; in place it is one."""
    spec, dur = horns_pnr()
    for dy, want in ((0.0, 1), (13.0, 0), (-5.5, 0)):
        for seed in SEEDS3:
            _, sc = scene_of(_shift_y(spec, dy), dur, seed=seed)
            ons = [e for e in C.primitives(sc) if e.kind == "SCR.on" and e.actors == {"screener": "o2", "user": "o1"}]
            assert len(ons) == want, (dy, seed, len(ons))


def test_l9_motion_counts_half_court_actions_only():
    """L9: four players sprinting up the floor register as CUTs; with one half-court cut later the clip used to read
    as 'motion' (actions over first-to-last action span); only actions inside half-court windows count now."""
    p = {"o1": [(0.0, 0.0, 22.0), (7.0, 0.0, 8.0)], "o2": [(0.0, 4.0, 24.0), (6.6, 5.3, 5.3)],
         "o3": [(0.0, -4.0, 24.0), (6.8, -5.3, 5.3)], "o4": [(0.0, 3.0, 26.0), (7.0, 6.6, 0.6)],
         "o5": [(0.0, -3.0, 26.0), (7.0, -6.6, 0.6), (14.0, -6.6, 0.6), (15.2, -1.5, 1.0), (16.0, -1.5, 1.0)]}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 17.0, "o1")]}}
    for seed in SEEDS3:
        _, sc = scene_of(spec, 17.0, seed=seed)
        cuts = [e for e in C.build_lattice(sc) if e.kind == "CUT"]
        assert len(cuts) >= 4  # the bring-up sprints are cuts in the lattice
        assert C.detect_motion(sc) == []
    spec, dur = motion_scene(True)
    _, sc = scene_of(spec, dur, seed=211)
    assert len(C.detect_motion(sc)) == 1  # real half-court motion still is


def test_l10_no_dho_at_the_rim_and_no_backcourt_chain():
    """L10: two attackers trading the ball under the rim (tip / rebound scrum) make no DHO; the dho_chain scene of F4
    moved 13 m back into the backcourt (outlet / inbound hand-offs) is no set-component chain."""
    p = {"o4": [(0.0, 0.8, 0.8), (3.0, 0.6, 1.0)], "o5": [(0.0, -0.8, 1.0), (3.0, -0.6, 0.9)], "o1": (0.0, 7.6),
         "o2": (5.3, 5.3), "o3": (-5.3, 5.3)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 1.0, "o4"), (1.1, 2.0, "o5"), (2.1, 3.0, "o4")],
                                         "flights": [(1.0, 1.1, "o4", "o5"), (2.0, 2.1, "o5", "o4")]}}
    for seed in SEEDS3:
        _, sc = scene_of(spec, 3.0, seed=seed)
        assert not [e for e in C.primitives(sc) if e.kind == "DHO"]
        assert [e for e in C.primitives(sc, dho_min_r_m=0.0) if e.kind == "DHO"]  # without L10 they are DHOs
    spec, dur = _dho_tester("chain")
    for seed in SEEDS3:
        assert not [e for e in C.detect_get_dho_chain(scene_of(_shift_y(spec, 13.0), dur, seed=seed)[1]) if e.kind == "dho_chain"]


# --------------------------------------------------------------------------------------
# Loop 5: noise robustness and finishing items (SportVU 2015-16 failure modes rebuilt as synthetic scenes)
# --------------------------------------------------------------------------------------
def _iso_dribble(hold, sigma, seed, amp=0.55, hz=1.6):
    """Wing ISO: o1 catches at 1.4 s, holds `hold` s while dribbling (the ball 0.3-0.9 m from him, as SportVU dribbles
    are), then passes back to o4. sim puts a held ball exactly on the holder, so the dribble offset is added to the
    observed ball track."""
    t1 = 1.4 + hold
    p = {"o1": [(0.0, 5.5, 7.0), (1.4, 5.5, 7.0), (1.4 + 0.6 * hold, 4.6, 6.4), (t1, 5.0, 6.8), (t1 + 1.0, 5.0, 6.8)],
         "o2": (-5.3, 5.3), "o3": (-6.8, 0.4), "o4": (0.0, 7.8), "o5": (-3.0, 8.0)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 1.0, "o4"), (1.4, t1, "o1"), (t1 + 0.4, t1 + 1.0, "o4")],
                                         "flights": [(1.0, 1.4, "o4", "o1"), (t1, t1 + 0.4, "o1", "o4")]}}
    assert_feasible(spec)
    _, tracks = sim.scenario(spec, t1 + 1.0, sigma_p=sigma, seed=seed)
    b = [t for t in tracks if t.oid == "ball"][0]
    a, z = f(1.4), f(t1)
    ph = 2 * np.pi * hz * np.arange(a, z + 1) * DT
    b.x[a:z + 1] += amp * (0.6 + 0.4 * np.sin(ph))
    b.y[a:z + 1] += -0.25 * amp * np.cos(ph)
    return mvlib.build_scene(tracks)


def test_c1_iso_short_dribbled_hold_under_noise():
    """C1: a 3.3 s dribbled ISO hold at sigma_p 0.5 - the hard HOLD_R holder drops catch / release frames and the hold
    falls under min_hold_s; the hold hysteresis (hold_ext_k x sigma_dist) keeps it. A 2.7 s hold stays no ISO."""
    for seed in (1003, 1005, 1008, 1009):
        sc = _iso_dribble(3.3, 0.5, seed)
        assert [e.actors["handler"] for e in C.detect_iso(sc)] == ["o1"], seed
        assert C.detect_iso(sc, hold_ext_k=0.0) == []  # loop-4 hold: lost
    for seed in SEEDS3:
        for sig in (0.3, 0.5):
            assert [e.actors["handler"] for e in C.detect_iso(_iso_dribble(3.3, sig, seed))] == ["o1"]
            assert C.detect_iso(_iso_dribble(2.7, sig, seed)) == []


def _wide_pnr(defense=True, off=1.3):
    """o1 dribbles straight across the top past o2, who stands `off` m above his path; o1's defender x1 trails him
    on the top side and runs into o2 (the screen's real contact)."""
    p = {"o1": [(0.0, -3.0, 8.0), (1.0, -3.0, 8.0), (3.0, 3.5, 8.0), (4.0, 3.5, 8.0)], "o2": (0.0, 8.0 + off),
         "o3": (-6.8, 0.4), "o4": (6.8, 0.4), "o5": (-5.3, 5.3)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 4.0, "o1")]}}
    if defense:
        spec = _with_defense(spec, {"x1": [(0.0, -3.0, 8.9), (1.0, -3.0, 8.9), (1.9, -0.9, 8.9), (2.3, -0.5, 8.9),
                                           (3.3, 2.5, 8.3), (4.0, 3.0, 8.3)]})
    return spec, 4.0


def test_c2_ball_screen_noise_widened_contact_needs_the_defender():
    """C2: noise moves the handler-screener minimum distance across scr_contact_m; a ball-screen contact may come from
    the widened gate scr_contact_m + scr_on_contact_k x sigma_dist, but only when the handler's defender meets the
    screener. Without the defender (or without the widening) the 1.3 m pass is no screen."""
    for sig, seed in ((0.3, 1000), (0.3, 1001), (0.3, 1005), (0.5, 1000), (0.5, 1005)):
        _, sc = scene_of(*_wide_pnr(True), seed=seed, sigma=sig)
        on = lambda **kw: [e for e in C.primitives(sc, **kw) if e.kind == "SCR.on" and e.actors == {"screener": "o2", "user": "o1"}]  # noqa: E731
        assert len(on()) == 1, (sig, seed)
        assert on(scr_on_contact_k=0.0) == []  # loop-4 gate: missed
        assert [e.actors for e in C.detect_pnr_location(sc)] == [{"screener": "o2", "handler": "o1"}]
        _, sc0 = scene_of(*_wide_pnr(False), seed=seed, sigma=sig)
        assert not [e for e in C.primitives(sc0) if e.kind == "SCR.on"]  # no defender: no widened screen


def _putback(rim=True, seed=1000):
    """o5 holds the ball (offensive rebound at the rim, or on the left wing), passes out to o1, who shoots at 2.3 s."""
    o5 = (0.6, 0.8) if rim else (-5.5, 2.0)
    p = {"o5": o5, "o1": (5.0, 5.5), "o2": (-5.3, 5.3), "o3": (-6.8, 0.4), "o4": (0.0, 7.8)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 0.8, "o5"), (1.1, 2.3, "o1")], "flights": [(0.8, 1.1, "o5", "o1")]}}
    _, tracks = sim.scenario(spec, 3.2, sigma_p=SIG, seed=seed)
    b = [t for t in tracks if t.oid == "ball"][0]
    a, z = f(2.3), f(2.9)
    b.x[a:] = np.concatenate([np.linspace(5.0, 0.0, z - a + 1), np.zeros(len(b.x) - z - 1)])
    b.y[a:] = np.concatenate([np.linspace(5.5, 0.0, z - a + 1), np.zeros(len(b.y) - z - 1)])
    return mvlib.build_scene(tracks)


def test_c3_putback_window_is_no_set():
    """C3: a short half-court window opened right after the ball was at the rim (putback / tip scramble) is no set
    window; the same pass-and-shot from the wing still is one."""
    for seed in SEEDS3:
        assert C.detect_set_window(_putback(True, seed)) == []
        assert [w.attrs["segment_kind"] for w in C.detect_set_window(_putback(True, seed), scramble_max_s=0.0)] == ["halfcourt"]
        assert [w.attrs["close_reason"] for w in C.detect_set_window(_putback(False, seed))] == ["shot_proxy"]


def _flicker_scene(seed, gap=0.7):
    """o1 and o2 stand gap m apart at the top; the ball moves 0.55 m toward o2 (the holder switches), rests almost
    midway (0.06 m nearer o2) and goes back: two attackers trading the nearest-attacker label without a hand-off."""
    p = {"o1": (-gap / 2, 7.0), "o2": (gap / 2, 7.0), "o3": (-6.8, 0.4), "o4": (6.8, 0.4), "o5": (-5.3, 5.3)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 4.0, "o1")]}}
    truth, tracks = sim.scenario(spec, 4.0, sigma_p=0.05, seed=seed)
    b = [t for t in tracks if t.oid == "ball"][0]
    xs = np.interp(np.arange(len(b.x)) * DT, [0.0, 1.0, 1.3, 1.6, 1.9, 2.6, 2.9, 4.0],
                   [-gap / 2, -gap / 2, 0.2, 0.2, 0.03, 0.03, -gap / 2, -gap / 2])
    b.x = xs + (b.x - truth["ball"][0])
    return mvlib.build_scene(tracks)


def test_c4_dho_chain_needs_a_ball_supported_holder_change():
    """C4: A -> B -> A 'hand-back' made of holder flicker (the ball never clearly with B) is no DHO chain; the F4 chain
    scene still is one."""
    for seed in SEEDS3:
        sc = _flicker_scene(seed)
        assert len([e for e in C.primitives(sc) if e.kind == "DHO"]) == 2  # both label changes read as DHOs
        assert not [e for e in C.detect_get_dho_chain(sc) if e.kind == "dho_chain"]
        assert [e for e in C.detect_get_dho_chain(sc, chain_min_lead_m=-9.0) if e.kind == "dho_chain"]  # loop 4: a chain
    spec, dur = _dho_tester("chain")
    for seed in SEEDS3:
        assert [e for e in C.detect_get_dho_chain(scene_of(spec, dur, seed=seed)[1]) if e.kind == "dho_chain"]


def test_c5_motion_from_cuts_family_events():
    """C5: detect_all(scene, cuts=...) builds motion from the cuts family's cut events; the proxy CUT stays the
    fallback (cuts=None), and with no real cuts the off-ball screens alone are no motion."""
    from detectors import cuts as CU
    spec, dur = motion_scene(True)
    for seed in (211, 1000):
        _, sc = scene_of(spec, dur, seed=seed)
        cu = CU.detect_all(sc)
        assert [e.attrs["cut_source"] for e in C.detect_motion(sc)] == ["proxy"]
        res = C.detect_all(sc, cuts=cu)
        assert [e.attrs["cut_source"] for e in res["motion"]] == ["cuts_family"]
        assert any("motion" in e.attrs["name"] for e in res["compositional_name"])
        assert C.detect_motion(sc, cuts=[]) == []


def test_c6_transition_windows_carry_a_fixed_name():
    """C6 (lead decision): name / style events only for half-court set windows; a transition_early window keeps its
    set_window and segment events with the name 'transition_early' and no style."""
    p = {"o1": [(0.0, 0.0, 22.0), (7.0, 0.0, 8.0)], "o2": [(0.0, 4.0, 24.0), (6.6, 5.3, 5.3)],
         "o3": [(0.0, -4.0, 24.0), (6.8, -5.3, 5.3)], "o4": [(0.0, 3.0, 26.0), (7.0, 6.6, 0.6)],
         "o5": [(0.0, -3.0, 26.0), (7.0, -6.6, 0.6), (14.0, -6.6, 0.6), (15.2, -1.5, 1.0), (16.0, -1.5, 1.0)]}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 17.0, "o1")]}}
    for seed in SEEDS3:
        _, sc = scene_of(spec, 17.0, seed=seed)
        wins = C.detect_set_window(sc)
        assert [w.attrs["segment_kind"] for w in wins] == ["transition_early", "halfcourt"]
        assert wins[0].attrs["name"] == "transition_early"
        names, styles = C.detect_compositional_name(sc), C.detect_style_measures(sc)
        assert len(names) == len(styles) == 1 and names[0].start == wins[1].start
        assert not any(n.attrs["name"].startswith("Early") for n in names)
        early = [s for s in C.detect_segments(sc) if s.start <= wins[0].end]
        assert early and all(s.attrs["name"] == "transition_early" for s in early)


def _wide_drag(defense=True):
    """The 'stop' drag of F2 with the trailer setting 1.26 m off the handler's path; the handler's defender x1 meets him."""
    p = {"o1": [(0.0, 0.0, 15.0), (2.3, 0.0, 8.0), (3.2, 0.0, 8.0), (4.2, -3.0, 6.2)],
         "o5": [(0.0, 0.5, 16.5), (2.6, -0.3, 6.35), (3.6, -0.3, 6.35), (5.1, -0.3, 1.5)],
         "o2": [(0.0, 5.0, 14.0), (4.0, 6.8, 0.4)], "o3": [(0.0, -5.0, 14.0), (4.0, -6.8, 0.4)], "o4": [(0.0, 2.0, 16.0), (4.0, 5.3, 5.3)]}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}}
    if defense:
        spec = _with_defense(spec, {"x1": [(0.0, 0.0, 16.0), (2.3, 0.0, 9.0), (3.2, 0.0, 8.9), (3.8, -0.5, 6.9), (4.6, -2.6, 6.8)]})
    return spec, 6.0


def test_c7_drag_uses_the_ball_screen_contact_rule(monkeypatch):
    """C7: drag shares the C2 ball-screen contact rule; a trailer screen 1.26 m off the handler's path (noisy minimum
    above scr_contact_m) is found when the handler's defender meets the trailer, and not without the widening."""
    pair = lambda evs: [e for e in evs if e.actors["handler"] == "o1" and e.actors["screener"] == "o5"]  # noqa: E731
    # loop 6 C7: the widened contact also needs reach evidence (loop 8: wide_reach_test); these seeds keep it (the trailer's noisy
    # minimum stays near scr_contact_m), the loop-5 seeds (0.3, 1004 / 1005), (0.5, 1005) no longer do
    for sig, seed in ((0.3, 1006), (0.3, 1007)):
        _, sc = scene_of(*_wide_drag(True), seed=seed, sigma=sig)
        _, sc0 = scene_of(*_wide_drag(False), seed=seed, sigma=sig)
        assert len(pair(C.detect_drag(sc))) == 1, (sig, seed)
        assert pair(C.detect_drag(sc0)) == []
        with monkeypatch.context() as m:
            # loop 7 C7: the widened band is now scr_contact_m + wide_body_m (physical) plus the noise widening; with
            # both switched off the 1.26 m trailer is outside the contact gate
            m.setitem(C.PRM["event_lattice"], "scr_on_contact_k", 0.0)
            m.setitem(C.PRM["drag"], "wide_body_m", 0.0)
            assert pair(C.detect_drag(sc)) == []


# --------------------------------------------------------------------------------------
# Loop 6 (finishing pass) regressions: each test fails with its fix switched off
# --------------------------------------------------------------------------------------
def _inbound_quick_shot(src, seed, sigma=SIG):
    """Dead-ball inbound: src holds the ball (0-0.8 s), passes in to o1 on the right wing, o1 shoots at 2.3 s."""
    p = {"o5": src, "o1": (5.0, 5.5), "o2": (-5.3, 5.3), "o3": (-6.8, 0.4), "o4": (0.0, 7.8)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 0.8, "o5"), (1.1, 2.3, "o1")], "flights": [(0.8, 1.1, "o5", "o1")]}}
    _, tracks = sim.scenario(spec, 3.2, sigma_p=sigma, seed=seed)
    b = [t for t in tracks if t.oid == "ball"][0]
    a, z = f(2.3), f(2.9)
    b.x[a:] = np.concatenate([np.linspace(5.0, 0.0, z - a + 1), np.zeros(len(b.x) - z - 1)])
    b.y[a:] = np.concatenate([np.linspace(5.5, 0.0, z - a + 1), np.zeros(len(b.y) - z - 1)])
    return mvlib.build_scene(tracks)


def test_c3_loop6_baseline_inbound_is_a_set_not_a_scramble():
    """Loop 6 C3: a baseline out-of-bounds quick hitter (inbounder behind the baseline 2.0 m from the rim, or in the lane
    corner 3.2 m out) opens a set window; the loop-5 putback rule read the out-of-bounds ball as a ball at the rim.
    The putback scramble of loop 5 C3 stays no set."""
    for seed in SEEDS3:
        for src in ((1.2, -1.9), (2.6, -1.8)):
            for sig in (0.3, 0.5):
                sc = _inbound_quick_shot(src, seed, sig)
                assert [w.attrs["segment_kind"] for w in C.detect_set_window(sc)] == ["halfcourt"], (src, sig, seed)
        assert C.detect_set_window(_inbound_quick_shot((1.2, -1.9), seed), scramble_inbound_excl=False) == []  # loop 5
        assert C.detect_set_window(_putback(True, seed)) == []


def _rim_run_drag(seed, sigma):
    """A trailer runs from the backcourt to the rim 1.6-1.8 m off the handler's side and never stops; both
    defenders are near him (the handler's defender passes 1.3 m from the trailer). No drag screen."""
    o1 = [(0.0, 0.0, 15.0), (2.3, 0.0, 8.0), (3.2, 0.0, 8.0), (4.2, -3.0, 6.2)]
    o5 = [(0.0, 2.9, 17.5), (2.6, 1.6, 7.3), (4.2, 1.6, 1.2)]
    p = {"o1": o1, "o5": o5, "o2": [(0.0, 5.0, 14.0), (4.0, 6.8, 0.4)], "o3": [(0.0, -5.0, 14.0), (4.0, -6.8, 0.4)],
         "o4": [(0.0, 2.0, 16.0), (4.0, 5.3, 5.3)]}
    spec = _with_defense({"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}},
                         {"x1": [(0.0, 0.0, 14.0), (2.3, 0.3, 7.0), (3.2, 0.3, 7.0), (4.2, -2.6, 5.4)],
                          "x5": [(0.0, 2.7, 16.5), (2.6, 1.8, 6.5), (4.2, 1.8, 1.6)]})
    return scene_of(spec, 6.0, seed=seed, sigma=sigma)[1]


def test_c7_loop6_widened_drag_contact_needs_the_trailer_to_reach_the_handler():
    """Loop 6 C7: the loop-5 widened drag contact (scr_contact_m + 2 sigma_dist with the defender check) admitted a
    trailer running to the rim 1.7 m off the handler (noisy minimum 1.4-1.5 m, the handler's defender 1.3 m from him).
    A widened contact now also needs the trailer to reach the handler (loop 8: measured minimum <= scr_contact_m +
    wide_body_m, wide_reach_test)."""
    for seed in (1003, 1004, 1007):
        sc = _rim_run_drag(seed, 0.3)
        assert C.detect_drag(sc) == [], seed
        assert C.detect_drag(sc, wide_reach_test=False)  # loop 5: a drag (loop 8: the reach test is wide_reach_test)


def _hedge_scene(seed, sigma):
    """o1 dribbles across the top past o2 (1.45 m above his path: no contact). o1's own defender x1 sags 2.0 m on the
    rim side all along; o2's defender x2 hedges out toward o1 just before the pass-by (1.0-2.4 s)."""
    p = {"o1": [(0.0, -3.0, 8.0), (1.0, -3.0, 8.0), (3.0, 3.5, 8.0), (4.0, 3.5, 8.0)], "o2": (0.0, 9.45),
         "o3": (-6.8, 0.4), "o4": (6.8, 0.4), "o5": (-5.3, 5.3)}
    spec = _with_defense({"actors": actors(p), "ball": {"held": [(0.0, 4.0, "o1")]}},
                         {"x1": [(0.0, -3.0, 6.0), (1.0, -3.0, 6.0), (3.0, 3.5, 6.0), (4.0, 3.5, 6.0)],
                          "x2": [(0.0, 0.0, 8.9), (1.0, 0.0, 8.9), (1.6, -1.0, 8.4), (2.4, 0.0, 8.8), (4.0, 0.0, 8.8)]})
    return scene_of(spec, 4.0, seed=seed, sigma=sigma)[1]


def test_c2_loop6_handler_defender_is_the_sustained_matchup():
    """Loop 6 C2: the handler's defender is the sustained matchup (lowest mean distance over [t - 3 s, t - 0.5 s]), not
    the 1 s nearest, which picks the screener's hedging defender; the defense family's matchup wins when passed in."""
    lp = C.PRM["event_lattice"]
    for seed in SEEDS3:
        for sig in (0.05, 0.2):
            sc = _hedge_scene(seed, sig)
            t = int(np.nanargmin(mvlib.dist(sc.kins["o1"], sc.kins["o2"])))
            assert C._handler_defender(sc, "o1", t, lp) == "x1", (seed, sig)
            assert C._handler_defender(sc, "o1", t, dict(lp, scr_on_def_match_s=1.0, scr_on_def_match_end_s=0.0)) == "x2"
            assert not C._defender_meets(sc, "o2", "o1", t, lp)  # x1 never comes near o2
        sc = _hedge_scene(seed, 0.05)
        C._cache(sc)["matchup_family"] = {"x1": [None] * sc.n, "x2": ["o1"] * sc.n}
        assert C._handler_defender(sc, "o1", sc.n // 2, lp) == "x2"
    # detect_all passes the matchup through (sliced per possession span)
    sc = _hedge_scene(1000, 0.05)
    C.detect_all(sc, matchup={"x1": ["o1"] * sc.n, "x2": ["o2"] * sc.n})
    assert C._cache(sc)["matchup_family"]["x1"][0] == "o1"


def _soft_pass_hold(hold, seed, sigma):
    """o1 catches a slow pass (5.5 m in 1.3 s = 4.3 m/s, under catch_max_ball_mps) at 2.0 s, holds `hold` s on the
    right wing with teammates spaced and his defender on him, and passes back as slowly."""
    t_in, t1, pd = 2.0, 2.0 + hold, 1.3
    p = {"o1": [(0.0, 5.5, 7.0), (t_in, 5.5, 7.0), (t_in + 0.6 * hold, 4.6, 6.4), (t1, 5.0, 6.8), (t1 + 1.5, 5.0, 6.8)],
         "o2": (-5.3, 5.3), "o3": (-6.8, 0.4), "o4": (0.0, 7.8), "o5": (-3.0, 8.0)}
    dur = t1 + pd + 1.0
    spec = {"actors": actors(p), "ball": {"held": [(0.0, t_in - pd, "o4"), (t_in, t1, "o1"), (t1 + pd, dur, "o4")],
                                         "flights": [(t_in - pd, t_in, "o4", "o1"), (t1, t1 + pd, "o1", "o4")]}}
    spec = _with_defense(spec, {"x1": [(0.0, 4.6, 6.2), (t_in, 4.6, 6.2), (t_in + 0.6 * hold, 3.9, 5.7), (t1, 4.2, 6.0), (dur, 4.2, 6.0)]})
    return scene_of(spec, dur, seed=seed, sigma=sigma)[1]


def test_c1_loop6_soft_pass_frames_are_not_hold():
    """Loop 6 C1: a 2.6 s hold between two soft 4.3 m/s passes read as a >= 3 s ISO (the hard holder takes the ball
    inside HOLD_R during the flights, the hold hysteresis extends further); the hold now ends where the ball starts
    leaving at > release_vr_mps and starts where the arriving ball slows under it. A 3.6 s hold is still an ISO."""
    for seed in SEEDS3:
        for sig in (0.05, 0.3):
            sc = _soft_pass_hold(2.6, seed, sig)
            assert C.detect_iso(sc) == [], (seed, sig)
            assert [e.actors["handler"] for e in C.detect_iso(sc, release_vr_mps=0.0)] == ["o1"]  # loop 5: an ISO
            assert [e.actors["handler"] for e in C.detect_iso(_soft_pass_hold(3.6, seed, sig))] == ["o1"]
        assert [e.actors["handler"] for e in C.detect_iso(_iso_dribble(3.3, 0.5, seed + 3))] == ["o1"]  # dribble kept


def _hand_back(hold, seed, sigma):
    """o1 hands off to o2 (1.6 s), o2 hands back to o1 (3.0 s), o1 keeps it `hold` s and passes to o4 on the left."""
    t2 = 3.0 + hold
    p = {"o1": [(0.0, 0.0, 8.0), (1.5, 2.4, 7.6), (2.2, 2.0, 7.0), (2.9, 2.4, 7.3), (t2 + 0.6, 2.0, 7.0)],
         "o2": [(0.0, 3.4, 5.0), (1.2, 3.0, 7.2), (2.0, 3.6, 7.6), (2.9, 3.0, 7.5), (t2 + 0.6, 4.6, 6.0)],
         "o3": (6.8, 0.4), "o4": (-5.3, 5.3), "o5": (-6.8, 0.4)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 1.6, "o1"), (1.6, 3.0, "o2"), (3.0, t2, "o1"), (t2 + 0.6, 6.0, "o4")],
                                         "flights": [(t2, t2 + 0.6, "o1", "o4")]}}
    return scene_of(spec, 6.0, seed=seed, sigma=sigma)[1]


def test_c4_loop6_short_hand_back_is_no_chain_link():
    """Loop 6 C4: a hand-back the receiver keeps for less than chain_min_hold_s (0.2 s here, a 0.30-0.33 s holder run)
    makes no DHO chain; a 1.0 s hand-back still does."""
    chains = lambda sc, **kw: [e for e in C.detect_get_dho_chain(sc, **kw) if e.kind == "dho_chain"]  # noqa: E731
    for sig in (0.2, 0.3):
        for seed in (1000, 1002):
            sc = _hand_back(0.2, seed, sig)
            assert chains(sc) == [], (sig, seed)
            assert chains(sc, chain_min_hold_s=0.0)  # loop 5: a chain
    for seed in SEEDS3:
        assert [e.actors["receiver"] for e in chains(_hand_back(1.0, seed, 0.3))] == ["o1"]



# --------------------------------------------------------------------------------------
# Loop 7 (regression-only finishing pass): each test fails on the loop-6 (0.6.0) code
# --------------------------------------------------------------------------------------
def test_c3_loop7_inbounds_rebounder_near_the_baseline_stays_a_scramble():
    """Loop 7 C3: an offensive rebounder 0.15 m inside the baseline (y -1.45) whose noisy position at the window's
    first frame read out of bounds was taken for an inbounder (the loop-6 rule: holder median, no margin, over the
    lookback frames only), so the putback scramble became a set (sigma_p 0.5 seeds 1000 / 1003 / 1006 / 1009). The
    inbound now needs the ball median out and the holder-and-ball mean beyond the line by inbound_oob_k sigma over the
    whole inbound hold. A BLOB inbounder 0.2 m behind the line still opens a set."""
    for seed in (1000, 1003, 1006, 1009):
        assert C.detect_set_window(_inbound_quick_shot((1.0, -1.45), seed, 0.5)) == [], seed
    for seed in SEEDS3:
        sc = _inbound_quick_shot((0.3, -1.8), seed, 0.3)
        assert [w.attrs["segment_kind"] for w in C.detect_set_window(sc)] == ["halfcourt"], seed


def _post_catch(seed, sigma):
    """o1 waits in the short corner at r 4.0 m, catches a soft 4.3 m/s pass at 2.0 s and steps out to r 5.8 m within
    0.8 s, holds 4 s and passes back; his defender follows him. A catch inside post_max_r_m: a post-up, not an ISO."""
    t_in, t1, pd = 2.0, 6.0, 1.3
    p = {"o1": [(0.0, 3.0, 2.6), (t_in, 3.0, 2.6), (t_in + 0.8, 4.4, 3.8), (t1 + 1.5, 4.4, 3.8)],
         "o2": (-5.3, 5.3), "o3": (-6.8, 0.4), "o4": (0.0, 7.8), "o5": (-3.0, 8.0)}
    dur = t1 + pd + 1.0
    spec = {"actors": actors(p), "ball": {"held": [(0.0, t_in - pd, "o4"), (t_in, t1, "o1"), (t1 + pd, dur, "o4")],
                                         "flights": [(t_in - pd, t_in, "o4", "o1"), (t1, t1 + pd, "o1", "o4")]}}
    spec = _with_defense(spec, {"x1": [(0.0, 2.4, 2.0), (t_in, 2.4, 2.0), (t_in + 0.8, 3.6, 3.2), (dur, 3.6, 3.2)]})
    return scene_of(spec, dur, seed=seed, sigma=sigma)[1]


def test_c1_loop7_post_window_is_anchored_at_the_catch():
    """Loop 7 C1: the post-up test (median r over the first post_window_s) starts at the untrimmed hold start, like the
    attack test. The loop-6 flight trim moved it to the trimmed start, after the catcher had stepped out of the post,
    and a short-corner catch at r 4.0 m became an ISO (on SportVU: a back-down caught at r ~4.6 m)."""
    for seed in SEEDS3:
        for sig in (0.05, 0.2):
            assert C.detect_iso(_post_catch(seed, sig)) == [], (seed, sig)


def _fast_pass_hold(hold, seed, sigma, pd=0.35):
    """The wing ISO of _soft_pass_hold with fast passes in and out (5.5 m in 0.35 s, ~16 m/s)."""
    t_in, t1 = 2.0, 2.0 + hold
    p = {"o1": [(0.0, 5.5, 7.0), (t_in, 5.5, 7.0), (t_in + 0.6 * hold, 4.6, 6.4), (t1, 5.0, 6.8), (t1 + 1.5, 5.0, 6.8)],
         "o2": (-5.3, 5.3), "o3": (-6.8, 0.4), "o4": (0.0, 7.8), "o5": (-3.0, 8.0)}
    dur = t1 + pd + 1.0
    spec = {"actors": actors(p), "ball": {"held": [(0.0, t_in - pd, "o4"), (t_in, t1, "o1"), (t1 + pd, dur, "o4")],
                                         "flights": [(t_in - pd, t_in, "o4", "o1"), (t1, t1 + pd, "o1", "o4")]}}
    spec = _with_defense(spec, {"x1": [(0.0, 4.6, 6.2), (t_in, 4.6, 6.2), (t_in + 0.6 * hold, 3.9, 5.7), (t1, 4.2, 6.0), (dur, 4.2, 6.0)]})
    return scene_of(spec, dur, seed=seed, sigma=sigma)[1]


def test_c1_loop7_fast_pass_trim_cuts_at_the_half_speed_point():
    """Loop 7 C1: the RTS smoother spreads a fast pass's velocity step over the held frames around the catch and the
    release; cutting where v_r first passes release_vr_mps took 3-5 held frames and a true 3.25 s hold read 2.97 s at
    sigma_p 0.5 (seeds 1003, 1006). The cut is now at half the flight's radial speed, the centre of the smoothed step."""
    for seed in (1003, 1006):
        sc = _fast_pass_hold(3.25, seed, 0.5)
        assert [e.actors["handler"] for e in C.detect_iso(sc)] == ["o1"], seed
        assert C.detect_iso(sc, release_half_peak=False) == [], seed  # loop 6 cut


def test_c1_loop7_release_stretch_tolerates_one_noisy_frame():
    """Loop 7 C1: one frame under release_vr_mps inside the release stretch at a run end (noise) no longer stops the
    trim (release_gap_frames 1); two such frames still do."""
    from types import SimpleNamespace as NS
    n, b = 60, 49
    z = np.zeros(n)
    vx = np.zeros(n)
    vx[b - 7:b + 1] = 3.0  # the ball leaves the holder at 3 m/s over the run's last 8 frames ...
    vx[b - 1] = 1.5        # ... with one noisy frame under release_vr_mps
    x = np.cumsum(vx) * DT + 0.3
    ball = NS(x=x, y=z.copy(), vx=vx, vy=z.copy(), var_v=np.full(n, 1e-4))
    holder = NS(x=z.copy(), y=z.copy(), vx=z.copy(), vy=z.copy(), var_v=np.full(n, 1e-4))
    sc = NS(ball=ball, kins={"o1": holder}, n=n)
    assert C._trim_flights(sc, [("o1", 0, b)], 2.0, 3, 0.5, 1) == [("o1", 0, b - 8)]
    assert C._trim_flights(sc, [("o1", 0, b)], 2.0, 3, 0.5, 0) == [("o1", 0, b)]  # loop 6: the dip ends the stretch
    vx[b - 2] = 1.5
    assert C._trim_flights(sc, [("o1", 0, b)], 2.0, 3, 0.5, 1) == [("o1", 0, b)]


def _stop_drag(off, seed, sigma):
    """The 'stop' drag of F2 with the trailer setting `off` m off the handler's drive line; the handler's defender
    x1 runs into the trailer (confirm6 adversarial geometry)."""
    o1 = [(0.0, 0.0, 15.0), (2.3, 0.0, 8.0), (3.2, 0.0, 8.0), (4.2, -3.0, 6.2)]
    sx, sy = -0.947 + 0.514 * off, 7.432 - 0.857 * off
    p = {"o1": o1, "o5": [(0.0, 0.5, 16.5), (2.6, sx, sy), (3.6, sx, sy), (5.1, sx, 1.5)],
         "o2": [(0.0, 5.0, 14.0), (4.0, 6.8, 0.4)], "o3": [(0.0, -5.0, 14.0), (4.0, -6.8, 0.4)], "o4": [(0.0, 2.0, 16.0), (4.0, 5.3, 5.3)]}
    spec = _with_defense({"actors": actors(p), "ball": {"held": [(0.0, 6.0, "o1")]}},
                         {"x1": [(0.0, 0.0, 16.0), (2.3, 0.0, 9.0), (3.2, 0.0, 8.9), (3.8, -0.5, 6.9), (4.6, -2.6, 6.8)]})
    return scene_of(spec, 6.0, seed=seed, sigma=sigma)[1]


def test_c7_loop7_widened_drag_band_is_the_physical_contact_width():
    """Loop 7 C7: the widened drag band runs to scr_contact_m + wide_body_m (the handler's defender's body between the
    two attackers), not to scr_contact_m + 0.67 sigma_dist: a stop-drag 1.35 m off the handler with the defender
    meeting the trailer was lost at low noise (loop 6: 1 of 10 at sigma_p 0.05). The 1.7 m rim run stays no drag."""
    pair = lambda evs: [e for e in evs if e.actors["handler"] == "o1" and e.actors["screener"] == "o5"]  # noqa: E731
    for seed in SEEDS3:
        sc = _stop_drag(1.35, seed, 0.05)
        assert len(pair(C.detect_drag(sc))) == 1, seed
        assert pair(C.detect_drag(sc, wide_body_m=0.0)) == [], seed  # no physical band (loop 6 collapsed it to ~1.2-1.34 m)
    for seed in (1003, 1004, 1007):
        assert C.detect_drag(_rim_run_drag(seed, 0.3)) == [], seed


# --------------------------------------------------------------------------------------
# Loop 8 (final targeted pass): each test fails on the loop-7 (0.7.0) code
# --------------------------------------------------------------------------------------
def _inbound_ball_offset(src, dy, seed, sigma):
    """_inbound_quick_shot with the observed ball shifted dy (m, + toward the court) while src holds it (0-0.8 s)."""
    p = {"o5": src, "o1": (5.0, 5.5), "o2": (-5.3, 5.3), "o3": (-6.8, 0.4), "o4": (0.0, 7.8)}
    spec = {"actors": actors(p), "ball": {"held": [(0.0, 0.8, "o5"), (1.1, 2.3, "o1")], "flights": [(0.8, 1.1, "o5", "o1")]}}
    _, tracks = sim.scenario(spec, 3.2, sigma_p=sigma, seed=seed)
    b = [t for t in tracks if t.oid == "ball"][0]
    b.y[f(0.0):f(0.8) + 1] += dy
    a, z = f(2.3), f(2.9)
    b.x[a:] = np.concatenate([np.linspace(5.0, 0.0, z - a + 1), np.zeros(len(b.x) - z - 1)])
    b.y[a:] = np.concatenate([np.linspace(5.5, 0.0, z - a + 1), np.zeros(len(b.y) - z - 1)])
    return mvlib.build_scene(tracks)


def test_c3_loop8_inbounder_holding_the_ball_over_the_line_opens_a_set():
    """Loop 8 C3: a BLOB inbounder 0.35 m behind the baseline holds the ball out over the line (ball centre 0.10 m in
    bounds). Loop 7 required the ball median out of bounds and lost the set (synthetic TP 10/10/10/10 -> 0/1/2/2); the
    holder route accepts the holder median alone beyond the line by inbound_oob_k x sigma_holder with the ball within
    inbound_reach_m. A rebounder 0.2 m inside the baseline who swings the ball 0.3 m behind it stays a scramble."""
    for seed in SEEDS3:
        for sig in (0.2, 0.3):
            sc = _inbound_ball_offset((0.8, -1.95), 0.45, seed, sig)
            assert [w.attrs["segment_kind"] for w in C.detect_set_window(sc)] == ["halfcourt"], (seed, sig)
        assert C.detect_set_window(_inbound_ball_offset((0.8, -1.95), 0.45, seed, 0.2), inbound_reach_m=0.0) == []
        assert C.detect_set_window(_inbound_ball_offset((0.8, -1.40), -0.30, seed, 0.2)) == [], seed
    unit = C.ITEMS["set_window"]["params"]["inbound_oob_k"]["unit"]
    assert "either route" in unit and "both the holder median and the ball median out" not in unit


def test_c7_loop8_reach_test_is_the_measured_minimum_edge():
    """Loop 8 C7: with wide_reach_p 0.5 the loop-7 probability test p_below(d, 1.4, wide_reach_k x sigma) >= p was the
    edge d <= 1.4 m and wide_reach_k had no effect; the parameterisation is now that edge (wide_reach_test). The
    1.35 m stop-drag stays a drag, switching the test off restores the loop-5 rim-run drag."""
    assert "wide_reach_k" not in C.PRM["drag"] and "wide_reach_p" not in C.PRM["drag"]
    assert C.PRM["drag"]["wide_reach_test"] is True
    pair = lambda evs: [e for e in evs if e.actors["handler"] == "o1" and e.actors["screener"] == "o5"]  # noqa: E731
    for seed in SEEDS3:
        assert len(pair(C.detect_drag(_stop_drag(1.35, seed, 0.05)))) == 1, seed
    assert C.detect_drag(_rim_run_drag(1003, 0.3)) == []
    assert C.detect_drag(_rim_run_drag(1003, 0.3), wide_reach_test=False)
