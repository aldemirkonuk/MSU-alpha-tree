"""Schema checks for config/identity_pack.yaml (single source of truth for the identity pack)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "identity"))

import idlib  # noqa: E402

SPEC = idlib.SPEC
CODE = "\n".join(p.read_text() for p in (ROOT / "tools" / "specgen" / "identity").glob("*.py"))
TESTS = "\n".join(p.read_text() for p in (ROOT / "tests" / "identity").glob("test_*.py"))
SPEC_TEXT = idlib.SPEC_PATH.read_text()


def test_every_param_has_value_unit_and_why():
    for owner, block in idlib.param_blocks(SPEC):
        for name, p in block.items():
            assert set(p) >= {"value", "unit", "why"}, (owner, name)
            assert str(p["why"]).strip() and str(p["unit"]).strip(), (owner, name)


def test_param_names_unique_and_read_by_code():
    params = idlib.flat_params(SPEC)  # raises on duplicates
    used = set(re.findall(r'(?:prm|P)\["([a-z0-9_]+)"\]', CODE))
    assert used <= set(params), sorted(used - set(params))
    unused = set(params) - used
    assert unused == set(SPEC["production_only_params"]), sorted(unused ^ set(SPEC["production_only_params"]))


def test_no_face_or_ethnicity_cues():
    forbidden = set(SPEC["forbidden_cues"])
    assert {"face", "skin_tone", "hair_colour", "hair_texture", "race", "ethnicity"} <= forbidden
    cue_ids = {c["id"] for c in SPEC["cues"]}
    assert not cue_ids & forbidden
    fields = SPEC["reference_pack"]["per_player_season"]["fields"]
    assert not set(fields) & forbidden
    assert "skin" in fields["reid_template"]["type"]  # the crop is masked
    assert any("face" in s.lower() for s in SPEC["standing_constraints"])
    for name, cfg in SPEC["harness"]["configs"].items():
        assert set(cfg["cues"]) <= {"team", "jersey", "appearance", "height", "gait"}, name


def test_state_machine_is_closed():
    states = set(SPEC["state_machine"]["states"])
    ids = [t["id"] for t in SPEC["state_machine"]["transitions"]]
    assert len(ids) == len(set(ids))
    for t in SPEC["state_machine"]["transitions"]:
        src = t["from"] if isinstance(t["from"], list) else [t["from"]]
        assert set(src) <= states and t["to"] in states, t["id"]


def test_every_hard_case_has_a_test():
    for hc in SPEC["hard_cases"]:
        names = [n.strip() for n in hc["test"].split(",")]
        for n in names:
            assert re.search(rf"def {n}\(", TESTS), (hc["id"], n)


def test_acceptance_refers_to_defined_metrics():
    metric_ids = {m["id"] for m in SPEC["metrics"]} | {"invariants"}
    for a in SPEC["acceptance"]:
        assert a["metric"] in metric_ids, a["id"]
        assert a["threshold"] and a["on_fail"], a["id"]
    assert any(a["id"] == "ACC-1" and "0" in a["threshold"] for a in SPEC["acceptance"])


def test_version_and_journal():
    assert re.fullmatch(r"\d+\.\d+\.\d+", SPEC["version"])
    assert SPEC["journal"][-1]["version"] == SPEC["version"] or SPEC["journal"][0]["version"] == SPEC["version"]


def test_generated_doc_is_current():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "specgen" / "identity" / "gen_doc.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_owner_decisions_25_oct_recorded():
    """OD-8 .. OD-10 (owner decisions 25 Oct 2026): journal entry with what / why / evidence; zero swaps absolute,
    probable tier offline-only and outside every locked metric; recording standard and the ShotTracker action item in
    requirement / acceptance / open items; live panel HOLD with candidates, no provisional labels."""
    j = next(x for x in SPEC["journal"] if x["version"] == "0.1.1")  # the entry of the version that recorded them
    assert tuple(map(int, SPEC["version"].split("."))) >= (0, 1, 1)
    dec = {x["id"]: x for x in j["decisions"]}
    assert set(dec) == {"OD-8", "OD-9", "OD-10"}
    assert all(x[k] and "owner decision 25 Oct 2026" in x["why"] for x in dec.values() for k in ("what", "why", "evidence"))
    assert "absolute" in SPEC["requirement"]["zero_swaps"]
    rs = SPEC["requirement"]["recording_standard"]
    assert rs["min_resolution"] == "1080p" and rs["min_fps"] >= 59.94 and rs["acceptance"] == "ACC-R1"
    acc = {a["id"]: a for a in SPEC["acceptance"]}
    assert "ACC-R1" in acc and "ACC-P1" in acc and "team-level" in acc["ACC-R1"]["on_fail"]
    assert any(x["id"] == "AI-1" and "ShotTracker" in x["action"] for x in SPEC["open_items"])
    assert {"PW-1", "PW-2"} <= {x["id"] for x in SPEC["planned_work"]}
    assert "never shows a provisional" in SPEC["outputs"]["live_panel"]["rule"]
    assert any("tier" in f for f in SPEC["outputs"]["per_frame"]["fields"])
    assert "offline only" in SPEC["assignment"]["rule"] and SPEC["assignment"]["params"]["p_probable"]["value"] < idlib.P["p_lock"]
    assert all(q.get("decision") for q in SPEC["open_questions"] if q["id"] in ("OQ-2", "OQ-4", "OQ-5", "OQ-6"))


def test_review_round_2_recorded():
    """Review round 2 (independent lenses, 11 Nov 2026): rows continue after RV-10 in the shape of round 1, the 0.2.0
    journal entry exists, and the harness-realism batch left its marks in acceptance, metrics, sources and questions."""
    r1, r2 = SPEC["review_round_1"], SPEC["review_round_2"]
    ids = [x["id"] for x in r1 + r2]
    assert ids == [f"RV-{i:02d}" for i in range(1, len(ids) + 1)] and len(r2) >= 9
    assert all(str(x[k]).strip() for x in r2 for k in ("finding", "fix", "evidence"))
    j = next(x for x in SPEC["journal"] if x["version"] == "0.2.0")
    assert j["date"] == SPEC["date"] == "2026-11-11" and len(j["changes"]) >= 3
    acc = {a["id"]: a for a in SPEC["acceptance"]}
    assert {"ACC-H1", "ACC-H3", "ACC-R2"} <= set(acc)
    assert not any("ShotTracker" in str(acc[i]) for i in ("ACC-H1", "ACC-H3", "ACC-R2"))  # nothing new depends on staff data
    assert {"swap_rate_bound", "swap_mechanism", "pairwise_sigma_p"} <= {m["id"] for m in SPEC["metrics"]}
    refs = " ".join(x["ref"] for x in SPEC["research"]["sources"])
    assert all(k in refs for k in ("Koshkina", "Crang", "KaliCalib", "PRTreID", "SoccerNet 2023"))
    assert "Basket-AI" not in SPEC_TEXT  # a source that is not in the pack
    assert any(q["id"] == "OQ-7" for q in SPEC["open_questions"]) and any(x["id"] == "PW-4" for x in SPEC["planned_work"])
    oq3 = next(q for q in SPEC["open_questions"] if q["id"] == "OQ-3")["question"]
    assert all(k in oq3 for k in ("legible-frame share", "truncation", "repeats the same wrong read"))
    assert "sigma_p" in SPEC["conventions"]["terms"]


def test_review_round_2_purity_batch_recorded():
    """Review round 2, batch A1 (tracklet and chain purity): the rules, parameters, state machine, metric, acceptance row
    and journal rows RV-22 to RV-26 are in the pack, and what was not applied is on record."""
    r2 = {x["id"]: x for x in SPEC["review_round_2"]}
    assert {"RV-22", "RV-23", "RV-24", "RV-25", "RV-26"} <= set(r2)
    tr, ch, asg = SPEC["tracklets"]["rule"], SPEC["chains"]["rule"], SPEC["assignment"]["rule"]
    assert all(k in tr for k in ("OPP GUARD", "UNRESOLVED GROUP", "EDGE BAND"))
    assert "CONTINUATION" in ch and "lock inherited)" not in ch.replace("\n", " ").split("CONTINUATION")[0]
    assert all(k in asg for k in ("COLOUR LATCH", "BRACKET"))
    for name, sec in (("unresolved_clear_s", "tracklets"), ("edge_band_m", "tracklets"), ("colour_latch_n", "assignment"),
                      ("bracket_nats", "assignment")):
        assert name in SPEC[sec]["params"], name
    assert idlib.P["unresolved_clear_s"] >= idlib.P["clear_s"] and idlib.P["edge_band_m"] >= idlib.P["fov_edge_m"]
    sm3 = next(t for t in SPEC["state_machine"]["transitions"] if t["id"] == "SM-3")
    assert sm3["from"] == "LOCKED" and sm3["to"] == "RECONFIRM"  # a lock is never inherited on geometry alone
    terms = SPEC["conventions"]["terms"]
    assert "by construction" not in terms["tracklet"] and "chain_purity" in terms["tracklet"]
    assert "by construction" not in next(p["rule"] for p in SPEC["design_principles"] if p["id"] == "DP2")
    assert "chain_purity" in {m["id"] for m in SPEC["metrics"]}
    acc = {a["id"]: a for a in SPEC["acceptance"]}
    assert acc["ACC-H4"]["metric"] == "chain_purity" and "hard" in acc["ACC-H4"]["scope"] and "ShotTracker" not in str(acc["ACC-H4"])
    assert any(q["id"] == "OQ-8" and "R-DT-06" in q["question"] for q in SPEC["open_questions"])  # TR-06: needs the owner
    pw = {x["id"] for x in SPEC["planned_work"]}
    assert {"PW-5", "PW-6", "PW-7"} <= pw
    j = next(x for x in SPEC["journal"] if x["version"] == "0.2.0")
    assert any("purity" in c.lower() for c in j["changes"])
