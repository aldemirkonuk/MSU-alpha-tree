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
