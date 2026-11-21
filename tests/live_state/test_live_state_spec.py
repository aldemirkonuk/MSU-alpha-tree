"""Lint of the live-state pack (config/live_state/*.yaml) and tests of the lint itself."""
from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "live_state"))

import lslib  # noqa: E402

CORE = lslib.load_core()
FIELDS = lslib.load_fields()


def test_core_alone_is_valid():
    assert lslib.validate(CORE, {}, require_all=False) == []


@pytest.mark.parametrize("stem", lslib.FIELD_FILES)
def test_each_fields_file_passes_the_lint(stem):
    fields = lslib.load_fields([stem])
    assert fields, f"{stem}.yaml has no records"
    assert lslib.validate(CORE, fields, require_all=False) == []


def test_whole_pack_when_every_index_entry_has_a_record():
    missing = [k for k in CORE["field_index"] if k not in FIELDS]
    if missing:
        pytest.skip(f"{len(missing)} index entries have no record yet")
    assert lslib.validate(CORE, FIELDS, require_all=True) == []


def test_every_state_machine_dimension_is_in_the_index():
    sm = yaml.safe_load((ROOT / "config" / "state_machine.yaml").read_text())
    alias = {"game_clock": "game_clock_s", "shot_clock": "shot_clock_s"}
    missing = [d for d in sm["dimensions"] if alias.get(d, d) not in CORE["field_index"]]
    assert missing == []


def test_every_param_is_complete():
    for name, p in lslib.params(CORE, FIELDS).items():
        for k in lslib.PARAM_KEYS:
            assert p.get(k) not in (None, ""), (name, k)


def test_grade_ladder_and_dq_enum():
    ladder = CORE["grades"]["ladder"]
    ranks = [CORE["grades"]["defs"][g]["rank"] for g in ladder]
    assert ranks == sorted(ranks) and len(set(ranks)) == len(ranks)
    allowed = {"observed", "inferred", "carried", "imputed", "quarantined"}  # the existing dq enum of the schema
    assert {d["dq_enum"] for d in CORE["grades"]["defs"].values()} <= allowed


def test_profile_limits_equal_their_params():
    allp = lslib.params(CORE)
    for pname, prof in CORE["profiles"].items():
        for d in prof.get("dropout", []):
            for lim, val in (d.get("limits") or {}).items():
                assert lim in allp, (pname, lim)
                assert float(val) == float(allp[lim]["value"]), (pname, lim)


# ---------------------------------------------------------------- the lint must catch bad records
def _one(key="game_clock_s"):
    rec = copy.deepcopy(FIELDS[key])
    return key, rec


def _problems(key, rec):
    return lslib.validate(CORE, {key: rec}, require_all=False)


def test_lint_catches_unknown_transition():
    key, rec = _one("possession_team")
    rec["update"]["changed_by"] = ["T99"]
    assert any("T99" in p for p in _problems(key, rec))


def test_lint_catches_grade_path_moving_up():
    key, rec = _one()
    rec["dropout"][0]["grade_path"] = ["carried", "observed"]
    assert any("down the ladder" in p for p in _problems(key, rec))


def test_lint_catches_missing_none_value():
    key, rec = _one()
    rec["none_value"] = None
    assert any("none_value" in p for p in _problems(key, rec))


def test_lint_catches_unknown_sensor_rule_and_profile():
    key, rec = _one()
    rec["sources"][0]["sensor"] = "crystal_ball"
    rec["dropout"][0]["rule"] = "GUESS"
    probs = _problems(key, rec)
    assert any("crystal_ball" in p for p in probs) and any("GUESS" in p for p in probs)
    key, rec = _one()
    rec["profile"] = "magic"
    assert any("profile" in p for p in _problems(key, rec))


def test_lint_catches_provisional_later_than_confirmed():
    key, rec = _one()
    rec["timing"]["provisional"]["p50_s"] = 5.0
    rec["timing"]["provisional"]["p95_s"] = 6.0
    assert any("later than confirmed" in p for p in _problems(key, rec))


def test_lint_catches_limit_that_differs_from_its_param():
    key, rec = _one()
    rec["dropout"][0]["limits"]["clock_inferred_max_s"] = 10
    assert any("differs from the param" in p for p in _problems(key, rec))


def test_lint_catches_cycle_and_unknown_input_in_derived_from():
    key, rec = _one("win_probability")
    rec["derived_from"] = ["win_probability"]
    assert any("cycle" in p for p in _problems(key, rec))
    rec["derived_from"] = ["no_such_field"]
    assert any("no_such_field" in p for p in _problems(key, rec))


def test_lint_catches_column_that_does_not_exist():
    key, rec = _one()
    rec["lands_in"] = ["state_frame.no_such_column"]
    assert any("no_such_column" in p for p in _problems(key, rec))


# ================================================================ added with the core check of 11 Nov 2026
SM = yaml.safe_load((ROOT / "config" / "state_machine.yaml").read_text())
MEASURED = json.loads((ROOT / "results" / "live_state_test" / "measured_sensors.json").read_text())["summary"]
LSLIB = ROOT / "tools" / "specgen" / "live_state" / "lslib.py"
LIVE_DOC = Path(os.environ.get("MSU_LIVE_DOC_SECTIONS",
                               Path.home() / "MSU-Alpha-3-private" / "work" / "live_doc_export_2026-11-11" / "sections"))


def _core_problems(change):
    core = copy.deepcopy(CORE)
    change(core)
    return lslib.validate(core, {}, require_all=False)


# ---------------------------------------------------------------- the four inventories (ACC-LS-2)
def test_index_names_each_state_machine_dimension_exactly_once():
    owners = [ix["dimension"] for ix in CORE["field_index"].values() if ix.get("dimension")]
    assert sorted(owners) == sorted(SM["dimensions"]) and len(SM["dimensions"]) == 32


def test_every_column_of_state_frame_and_state_second_maps_to_a_field_or_is_out_of_scope():
    covered = {c for cols in CORE["inventory"]["columns"].values() for c in cols}
    for table in ("state_frame", "state_second"):
        doc = yaml.safe_load((ROOT / "schema" / "tables" / f"{table}.yaml").read_text())
        names = {f"{table}.{c['name']}" for c in doc["columns"]}
        loose = sorted(n for n in names if n not in covered and n not in CORE["out_of_scope"])
        assert loose == [], loose
    assert all(f in CORE["field_index"] for f in CORE["inventory"]["columns"])


def test_every_r_sr_row_maps_to_fields_and_the_shall_list_is_right():
    reqs = CORE["inventory"]["requirements"]
    assert sorted(reqs) == [f"R-SR-{n:02d}" for n in range(1, 21)]
    assert [r for r, fs in reqs.items() if not fs] == ["R-SR-19"]  # per touch, out of scope with a reason
    assert any("R-SR-19" in str(v) for v in CORE["out_of_scope"].values())
    assert set(lslib.SHALL_SR) == set(reqs) - {"R-SR-12", "R-SR-19"}
    if LIVE_DOC.exists():  # the tier of each row, from the live requirements
        text = (LIVE_DOC / "19_state_record_and_invariants.md").read_text()
        tiers = dict(re.findall(r"^\| (R-SR-\d\d)[a-c]? \| (Shall|Should) ", text, re.M))
        assert {r for r, t in tiers.items() if t == "Should"} == {"R-SR-12", "R-SR-19"}


def test_every_field_is_on_the_19_oct_page_or_explained_as_added():
    rows = CORE["inventory"]["page_rows"]
    assert set(rows) == set(lslib.GROUP_CODE)  # the 10 groups of the page
    on_page = {f for table in rows.values() for fs in table.values() for f in fs}
    added = set(CORE["inventory"]["added_by_this_pack"])
    assert on_page | added == set(CORE["field_index"]) and not on_page & added


def test_health_signals_of_the_sensors_are_fields():
    for name, s in CORE["sensors"].items():
        for f in s["health"]["fields"]:
            assert f in CORE["field_index"], (name, f)
            assert CORE["field_index"][f]["profile"] == "meta", (name, f)


# ---------------------------------------------------------------- numbers against their sources
def test_every_evidence_string_carries_a_tag():
    for name, p in lslib.params(CORE, FIELDS).items():
        assert lslib.evidence_ok(p["evidence"], CORE), name
    for pname, prof in CORE["profiles"].items():
        assert lslib.evidence_ok(prof["latency"]["evidence"], CORE), pname
        for d in prof["dropout"]:
            assert lslib.evidence_ok(d["evidence"], CORE), (pname, d["when"])
    assert not lslib.evidence_ok("the scorer said so", CORE)


def test_an_assumed_value_names_the_measurement_that_replaces_it():
    words = ("Replaced by", "Measured per run", "to be measured", "Re-set from", "OQ-LS-", "ACC-LS-", "raised if", "measured on")
    for name, p in lslib.params(CORE, FIELDS).items():
        if p["evidence"].startswith("assumed:"):
            assert any(w in p["evidence"] for w in words) or p["_where"] == "harness", name


def test_measured_numbers_in_the_text_equal_measured_sensors_json():
    ev = CORE["profiles"]["clock"]["dropout"][0]["evidence"]
    for row in MEASURED["clock_carry_on_withheld_readings"]:
        if row["withheld_s"] in (2, 3, 5, 10, 20):
            assert f"{100 * row['last_status']['within_1s']:.1f} % after {row['withheld_s']} s" in ev, row["withheld_s"]
    by = {r["withheld_s"]: r["last_status"]["within_1s"] for r in MEASURED["clock_carry_on_withheld_readings"]}
    prm = lslib.params(CORE)
    assert by[int(prm["clock_inferred_max_s"]["value"])] >= prm["clock_inferred_promise"]["value"] > by[5]  # met at 3 s, not at 5 s
    assert f"{100 * by[30]:.1f} % after 30 s" in prm["clock_carried_max_s"]["evidence"]
    changed = [r["changed_share"] for r in MEASURED["score"]["changed_during_real_hidden_run"]]
    assert 0.035 <= min(changed[:4]) and max(changed[:4]) < 0.075 and 0.125 <= min(changed[4:]) and max(changed[4:]) < 0.165  # "4-7 %" and "13-16 %"
    c = MEASURED["clock"]
    avail = CORE["sensors"]["scorebug_ocr"]["availability"]
    for share in (c["availability_in_period"]["pooled"], c["availability_in_period"]["median"],
                  c["availability_in_period"]["min"], c["availability_in_period"]["max"],
                  MEASURED["bug_fields"]["team_fouls_read_share"], MEASURED["bug_fields"]["timeouts_read_share"]):
        assert f"{round(100 * share)} %" in avail, share
    linked = [n for n, p in prm.items() if p.get("measured_key")]
    assert len(linked) >= 9


def test_lint_catches_a_param_that_drifts_from_its_measurement_or_its_mirror():
    def drift(core):
        core["sensors"]["scorebug_ocr"]["params"]["foul_to_bug_p95_s"]["value"] = 30.0
    assert any("differs from the measurement" in p for p in _core_problems(drift))

    def mirror(core):
        core["max_dwell"]["throw_in"]["value"] = 6.0
    assert any("throw_in" in p and "differs from config/invariants.yaml" in p for p in _core_problems(mirror))

    def window(core):
        core["profiles"]["counter"]["params"]["make_confirm_window_s"]["value"] = 5.0
    assert any("make_confirm_window_s" in p for p in _core_problems(window))


def test_max_dwell_bounds_carry_a_rule_and_mirror_the_rules_constants():
    inv = yaml.safe_load((ROOT / "config" / "invariants.yaml").read_text())["constants"]
    md = CORE["max_dwell"]
    assert md["throw_in"]["value"] == inv["throw_in_count_s"] and md["free_throw_attempt"]["value"] == inv["free_throw_release_s"]
    assert md["shot_clock_period"]["value"] == inv["shot_clock_full_s"] and md["backcourt_control"]["value"] == inv["backcourt_count_s"]
    for k, e in md.items():
        if k != "note":
            assert e["rule"] and (e["rule"] == "physics" or e["evidence"].startswith("rule:")), k


def test_degradation_levels_say_something_for_every_graded_profile():
    cols = {"clocks", "counters", "status", "roster", "observation", "derived", "panel", "when"}
    for name, lvl in CORE["degradation_levels"].items():
        if name.startswith("D"):
            assert set(lvl) == cols, name


def test_cited_requirement_ids_exist_in_the_live_requirements():
    if not LIVE_DOC.exists():
        pytest.skip("the private export of the live requirements is not on this machine")
    known = set(re.findall(r"\b((?:R|N)-[A-Z]{2}-\d+[a-z]?)\b", "\n".join(p.read_text() for p in LIVE_DOC.glob("*.md"))))
    rows = set(re.findall(r"^\| \**((?:R|N)-[A-Z]{2}-\d+)", "\n".join(p.read_text() for p in LIVE_DOC.glob("*.md")), re.M))
    for f in ["core"] + lslib.FIELD_FILES:
        text = (ROOT / "config" / "live_state" / f"{f}.yaml").read_text()
        cited = set(re.findall(r"\b(R-[A-Z]{2}-\d+[a-z]?)\b", text))
        assert cited <= known, (f, sorted(cited - known))
    for key, rec in FIELDS.items():  # a record cites table rows only (no retired N- names)
        ids = {re.sub(r"[a-c]$", "", r) for r in rec["requirements"]}
        assert ids <= rows, (key, sorted(ids - rows))


# ---------------------------------------------------------------- the lint must catch bad records (continued)
def test_lint_catches_unknown_steps_by_and_a_changed_by_the_state_machine_lists():
    key, rec = _one()
    rec["update"]["steps_by"] = ["T77"]
    assert any("T77" in p for p in _problems(key, rec))
    key, rec = _one("possession_team")
    rec["update"]["changed_by"] = ["T01", "T03"]
    assert any("lacks T05" in p for p in _problems(key, rec))


def test_lint_catches_a_none_value_outside_off_none_unknown():
    key, rec = _one()
    rec["none_value"] = "n/a"
    assert any("none_value" in p for p in _problems(key, rec))


def test_lint_catches_evidence_without_a_tag_and_missing_limits():
    key, rec = _one()
    rec["dropout"][0]["evidence"] = "it felt right"
    del rec["dropout"][1]["limits"]
    probs = _problems(key, rec)
    assert any("evidence must start with a tag" in p for p in probs) and any("limits missing" in p for p in probs)
    key, rec = _one()
    rec["timing"]["evidence"] = "quick"
    assert any("timing.evidence" in p for p in _problems(key, rec))
    key, rec = _one()
    rec["params"]["clock_upward_confirm_reads"]["evidence"] = "two is enough"
    assert any("clock_upward_confirm_reads" in p for p in _problems(key, rec))


def test_lint_catches_a_limit_that_is_not_a_param():
    key, rec = _one()
    rec["dropout"][0]["limits"] = {"made_up_limit_s": 4}
    assert any("made_up_limit_s" in p for p in _problems(key, rec))


def test_lint_catches_a_record_that_drops_an_inventory_column_or_requirement():
    key, rec = _one()
    rec["lands_in"].remove("state_frame.clock_inferred")
    rec["requirements"].remove("R-SR-17")
    probs = _problems(key, rec)
    assert any("lacks state_frame.clock_inferred" in p for p in probs) and any("lacks R-SR-17" in p for p in probs)
    key, rec = _one()
    rec["lands_in"].remove("clock_map:game")
    assert any("lacks clock_map:game" in p for p in _problems(key, rec))


def test_lint_catches_a_dimension_or_storage_that_differs_from_the_state_machine():
    key, rec = _one("possession_team")
    rec["dimension"] = "team_control"
    assert any("differs from the index" in p for p in _problems(key, rec))
    key, rec = _one("possession_team")
    rec["stored"] = "obs"
    assert any("differs from the state machine" in p for p in _problems(key, rec))


def test_lint_catches_unknown_invariant_timing_source_winner_log_and_mode():
    key, rec = _one()
    rec["invariants"].append("R-PR-11")
    rec["timing"]["provisional"]["by"] = "telepathy"
    rec["conflict"][0]["value_winner"] = "the_crowd"
    rec["conflict"][0]["log_to"] = "nowhere"
    rec["sources"][0]["modes"] = ["live", "dreaming"]
    probs = _problems(key, rec)
    for word in ("R-PR-11", "telepathy", "the_crowd", "nowhere", "dreaming"):
        assert any(word in p for p in probs), word


def test_lint_catches_a_proposed_column_that_already_exists_and_a_stray_freshness_key():
    key, rec = _one()
    rec["lands_in_proposed"].append("state_frame.game_clock_s")
    rec["freshness_needed_s"]["nobody"] = 1.0
    probs = _problems(key, rec)
    assert any("already exists" in p for p in probs) and any("nobody" in p for p in probs)


def test_lint_catches_a_derived_value_known_before_its_input():
    clock = copy.deepcopy(FIELDS["game_clock_s"])
    wp = copy.deepcopy(FIELDS["win_probability"])
    wp["timing"]["provisional"]["p50_s"] = 0.05
    probs = lslib.validate(CORE, {"game_clock_s": clock, "win_probability": wp}, require_all=False)
    assert any("earlier than its input game_clock_s" in p for p in probs)
    wp = copy.deepcopy(FIELDS["win_probability"])
    wp["timing"]["driven_by"] = ["lineup_home"]
    assert any("driven_by" in p for p in _problems("win_probability", wp))
    key, rec = _one()
    rec["derived_from"] = ["period"]
    assert any("only derived fields have inputs" in p for p in _problems(key, rec))


def test_lint_catches_core_defects():
    def two_owners(core):
        core["field_index"]["team_control"]["dimension"] = "possession_team"
    probs = _core_problems(two_owners)
    assert any("possession_team is carried by 2" in p for p in probs) and any("team_control is carried by 0" in p for p in probs)

    def lost_column(core):
        del core["inventory"]["columns"]["ball_visible"]
    assert any("state_frame.ball_visible maps to no field" in p for p in _core_problems(lost_column))

    def lost_health(core):
        core["sensors"]["audio"]["health"]["fields"] = ["no_such_field"]
    assert any("no_such_field" in p for p in _core_problems(lost_health))

    def bad_delay(core):
        core["sensors"]["pbp_feed"]["delay"]["p95"] = "feed_delay_p99_s"
    assert any("feed_delay_p99_s" in p for p in _core_problems(bad_delay))

    def profile_up(core):
        core["profiles"]["clock"]["dropout"][0]["grade_path"] = ["carried", "inferred"]
    assert any("profile clock" in p and "down the ladder" in p for p in _core_problems(profile_up))

    def new_field_unexplained(core):
        core["field_index"]["mystery"] = {"id": "LS-OBS-13", "group": "observability", "profile": "meta", "file": "fields_meta"}
    assert any("mystery" in p for p in _core_problems(new_field_unexplained))

    def gap(core):
        core["field_index"]["audio_present"]["id"] = "LS-OBS-14"
    assert any("gap-free" in p for p in _core_problems(gap))


def test_a_param_defined_twice_is_reported():
    key, rec = _one()
    rec["params"]["clock_tolerance_s"] = {"value": 2.0, "unit": "s", "why": "x", "evidence": "assumed: x"}
    assert any("defined twice" in p for p in _problems(key, rec))


def test_unread_params_reads_the_reference_code(tmp_path):
    assert lslib.unread_params(CORE, FIELDS) is None or isinstance(lslib.unread_params(CORE, FIELDS), list)
    code = tmp_path / "fake_fuse.py"
    code.write_text('x = P["clock_inferred_max_s"]\ny = prm["clock_carried_max_s"]\nz = P("max_dwell.throw_in")\n')
    unread = lslib.unread_params(CORE, FIELDS, code_files=[code])
    assert "clock_inferred_max_s" not in unread and "clock_carried_max_s" not in unread and "max_dwell.throw_in" not in unread
    assert "clock_tolerance_s" in unread


def test_command_line_exit_codes():
    def run(*args):
        return subprocess.run([sys.executable, str(LSLIB), *args], capture_output=True, text=True, cwd="/")
    one = run("--check", "config/live_state/fields_scoreboard.yaml")  # a repo-relative path from another directory
    assert one.returncode == 0 and "0 problems" in one.stdout, one.stdout
    assert run("--check", "config/live_state/no_such_file.yaml").returncode == 2
    whole = run("--check")
    missing = [k for k in CORE["field_index"] if k not in FIELDS]
    assert (whole.returncode == 0) == (not missing and "0 problems" in whole.stdout)


def test_a_key_written_twice_is_refused(tmp_path):
    bad = tmp_path / "fields_twice.yaml"
    bad.write_text("fields:\n  a: {id: LS-KEY-01}\n  b: {id: LS-KEY-02}\n  a: {id: LS-KEY-03}\n")
    with pytest.raises(ValueError, match="written twice"):
        lslib.load_fields([str(bad)])
    out = subprocess.run([sys.executable, str(LSLIB), "--check", str(bad)], capture_output=True, text=True)
    assert out.returncode == 2 and "written twice" in out.stdout


def test_lint_catches_a_timing_sensor_that_is_not_a_source():
    key, rec = _one()
    rec["timing"]["confirmed"]["by"] = "registry"
    assert any("not one of the field's sources" in p for p in _problems(key, rec))
