"""Lint of the data-platform pack (config/data_platform.yaml, schema/platform_changes.yaml), tests of the lint itself
and of the shared helpers of tools/specgen/platform/dplib.py. Everything here runs without private data, except the
last two smoke tests, which are skipped when the private play-by-play is absent."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "platform"))

import dplib  # noqa: E402

PACK = dplib.load_pack()
CHANGES = dplib.load_changes()


def problems_of(pack=None, changes=None, **kw):
    return dplib.validate(pack if pack is not None else PACK, changes if changes is not None else CHANGES, **kw)


def mutated(fn, what="pack"):
    doc = copy.deepcopy(PACK if what == "pack" else CHANGES)
    fn(doc)
    return problems_of(pack=doc) if what == "pack" else problems_of(changes=doc)


# ------------------------------------------------------------------------------------------------------- the pack
def test_pack_passes_the_lint():
    assert problems_of() == []


def test_cli_check_exits_zero():
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    r = subprocess.run([sys.executable, str(ROOT / "tools/specgen/platform/dplib.py"), "--check"], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "0 problems" in r.stdout


def test_final_mode_reports_rows_that_wait_for_a_prototype():
    pending = [a for i in dplib.ITEMS for a, row in PACK[i]["acceptance"].items() if row["status"] == "pending_prototype"]
    final = problems_of(final=True)
    if pending:
        assert any("still pending its prototype" in p for p in final)
    else:
        assert not any("pending" in p for p in final)


def test_the_four_items_and_their_parts_are_there():
    assert PACK["pack"] == "data_platform" and PACK["version"] == "0.1.0"
    for item in dplib.ITEMS:
        for part in dplib.ITEM_PARTS:
            assert part in PACK[item], f"{item}.{part}"
        assert PACK[item]["prototype"]["results_file"].startswith("results/platform_test/")


def test_the_four_priority_rows_are_sharpened_not_replaced():
    sharpened = {r["id"] for i in dplib.ITEMS for r in PACK[i]["requirements"] if r["kind"] == "sharpens"}
    assert {"R-MD-35", "R-EN-18", "R-EN-19", "R-SY-20"} <= sharpened


def test_every_requirement_row_has_the_fields_of_the_live_format():
    n = 0
    for item in dplib.ITEMS:
        for r in PACK[item]["requirements"]:
            n += 1
            for k in dplib.REQ_KEYS + ("kind", "test_data", "acceptance"):
                assert r.get(k), f"{r.get('id')}: {k}"
    assert n >= 24


def test_first_bindings_name_at_least_forty_registry_metrics():
    fb = PACK["query_layer"]["schemas"]["first_bindings"]
    ids = [m for grain in ("team_game", "player_game", "team_season") for m in fb[grain]]
    assert len(ids) == len(set(ids)) >= PACK["query_layer"]["params"]["first_bindings_min"]["value"]
    assert set(ids) <= dplib.metric_ids()


def test_grain_list_is_the_fixed_eleven_and_every_view_has_one():
    grains = PACK["conventions"]["grains"]
    assert len(grains) == 11 and len(set(grains)) == 11
    view_grains = {v["grain"] for v in CHANGES["views"].values() if v["layer"] in ("grain", "team_keyed")}
    assert set(grains) <= view_grains


def test_id_table_equals_the_constants_of_dplib():
    ids = PACK["cross_item"]["ids"]
    for prefix, name in dplib.ID_PREFIXES.items():
        assert ids[name]["prefix"] == prefix
    assert PACK["cross_item"]["params"]["id_hex_len"]["value"] == dplib.ID_HEX_LEN
    for name, rule in ids.items():   # rule X-4: no id is made from an ordinal, a clock or a time
        if name in ("pull_id", "run_id"):
            continue                 # the two event ids
        text = " ".join(map(str, rule["made_from"])).lower()
        for word in ("order_index", "possession number", "wall", "fetched_at", "clock"):
            assert word not in text, f"{name} is made from {word}"


# ---------------------------------------------------------------------------------- the lint catches what it should
def test_lint_catches_a_requirement_row_without_a_test():
    def f(d):
        del d["team_neutral"]["requirements"][0]["test"]
    assert any("test is missing" in p for p in mutated(f))


def test_lint_catches_an_exception_field_left_out():
    def f(d):
        d["lineage"]["requirements"][0]["exceptions"] = ""
    assert any("exceptions is missing" in p for p in mutated(f))


def test_lint_catches_a_met_row_without_results_and_a_missing_reason():
    def f(d):
        d["team_neutral"]["acceptance"]["ACC-DP-TN-2"].update(status="met", results="results/platform_test/nope.json#x")
    assert any("does not exist" in p for p in mutated(f))

    def g(d):
        del d["team_neutral"]["acceptance"]["ACC-DP-TN-9"]["reason"]
    assert any("not_yet_testable needs the reason" in p for p in mutated(g))

    def h(d):
        d["pbp_versions"]["acceptance"]["ACC-DP-PV-3"]["status"] = "pass"
    assert any("status is not one of" in p for p in mutated(h))


def test_lint_catches_an_acceptance_row_nobody_cites_and_a_citation_of_nothing():
    def f(d):
        d["lineage"]["acceptance"]["ACC-DP-LN-99"] = dict(d["lineage"]["acceptance"]["ACC-DP-LN-1"])
    assert any("ACC-DP-LN-99 is cited by no requirement row" in p for p in mutated(f))

    def g(d):
        d["lineage"]["requirements"][0]["acceptance"].append("ACC-DP-LN-98")
    assert any("ACC-DP-LN-98 is cited by a requirement row but not defined" in p for p in mutated(g))


def test_lint_catches_a_param_without_why_or_with_an_untagged_evidence():
    def f(d):
        del d["query_layer"]["params"]["interval_level"]["why"]
    assert any("param interval_level: why is missing" in p for p in mutated(f))

    def g(d):
        d["query_layer"]["params"]["interval_level"]["evidence"] = "everyone uses 95 %"
    assert any("evidence does not start with a tag" in p for p in mutated(g))

    def h(d):
        d["lineage"]["params"]["lineage_max_hops"]["evidence"] = "measured: results/platform_test/never_written.json"
    assert any("never_written.json, which does not exist" in p for p in mutated(h))


def test_lint_catches_unknown_columns_metrics_transitions_and_dimensions():
    def col(d):
        d["team_neutral"]["ask"] += " See games.home_side_colour."
    assert any("games.home_side_colour" in p for p in mutated(col))

    def structured(d):
        d["pbp_versions"]["schemas"]["tables"]["pbp_versions"]["columns"].append("n_typos")
    assert any("column n_typos" in p for p in mutated(structured))

    def metric(d):
        d["query_layer"]["schemas"]["first_bindings"]["team_game"].append("M-SHOOT-999")
    assert any("M-SHOOT-999 is not in config/metrics.yaml" in p for p in mutated(metric))

    def transition(d):
        d["pbp_versions"]["ask"] += " As T77."
    assert any("transition T77" in p for p in mutated(transition))

    def integrity(d):
        d["team_neutral"]["ask"] += " SEG-09."
    assert any("integrity rule SEG-09" in p for p in mutated(integrity))

    def dim(d):
        d["pbp_versions"]["schemas"]["dimensions_read"].append("score_msu")
    assert any("score_msu is not a dimension" in p for p in mutated(dim))

    def alg(d):
        d["lineage"]["ask"] += " ALG-LN-77."
    assert any("algorithm ALG-LN-77 is cited but not defined" in p for p in mutated(alg))


def test_lint_catches_a_bad_decision():
    def two_chosen(d):
        d["query_layer"]["decisions"][0]["options"][1]["verdict"] = "chosen"
    assert any("exactly one option is chosen" in p for p in mutated(two_chosen))

    def no_why(d):
        del d["pbp_versions"]["decisions"][0]["options"][1]["why"]
    assert any("has no why" in p for p in mutated(no_why))


def test_lint_catches_misnumbered_steps_and_a_stage_graph_fault():
    def steps(d):
        d["lineage"]["algorithms"]["ALG-LN-1"]["steps"][2] = "4. out of order"
    assert any("step 3 does not start with" in p for p in mutated(steps))

    def cycle(d):
        d["lineage"]["stage_graph"]["stages"][1]["reads"].append("pbp_diffs")
        d["lineage"]["stage_graph"]["stages"][2]["reads"].append("pbp_plays")
    assert any("cycle" in p for p in mutated(cycle))

    def two_writers(d):
        d["lineage"]["stage_graph"]["stages"][0]["writes"].append("events")
    assert any("events is written by" in p for p in mutated(two_writers))

    def no_source(d):
        d["lineage"]["stage_graph"]["stages"][3]["reads"].append("id_crosswalk")
    assert any("reads id_crosswalk, which no stage writes" in p for p in mutated(no_source))


def test_lint_catches_a_long_digit_string_in_the_public_pack():
    def f(d):
        d["team_neutral"]["ask"] += " game 123456789"
    assert any("digit string of 9 or more" in p for p in mutated(f))


def test_lint_catches_an_id_prefix_that_differs_from_dplib():
    def f(d):
        d["cross_item"]["ids"]["segment_id"]["prefix"] = "seg"
    assert any("segment_id" in p for p in mutated(f))


# ----------------------------------------------------------------------------- the team-neutral audit (ACC-DP-TN-1)
def test_audit_finds_the_74_flagged_columns_and_every_one_has_a_disposition():
    flagged = dplib.audit_msu_relative()
    assert len(flagged) == CHANGES["team_neutral"]["counts"]["flagged"] == 74
    assert len({t for t, *_ in flagged}) == CHANGES["team_neutral"]["counts"]["tables_touched"]
    audit = CHANGES["team_neutral"]["audit"]
    actions = [audit[t][c]["action"] for t, c, *_ in flagged]
    counts = CHANGES["team_neutral"]["counts"]
    assert actions.count("false_hit") == counts["false_hits"]
    assert actions.count("keep") == counts["kept_row_relative"]
    assert len(actions) - actions.count("false_hit") - actions.count("keep") == counts["changed"]
    assert len(dplib.schema_tables()) == counts["tables_scanned"]
    assert sum(len(c) for c in dplib.schema_tables().values()) == counts["columns_scanned"]


def test_lint_catches_a_missing_and_a_stale_disposition():
    def missing(d):
        del d["team_neutral"]["audit"]["timeouts"]["left_after_msu"]
    assert any("timeouts.left_after_msu is flagged" in p for p in mutated(missing, "changes"))

    def stale(d):
        d["team_neutral"]["audit"]["timeouts"]["called_by"] = {"action": "rename", "to": "called_by_side", "why": "x"}
    assert any("timeouts.called_by has a disposition but the audit no longer flags it" in p for p in mutated(stale, "changes"))


def test_lint_refuses_msu_relative_names_the_change_set_would_add():
    def rename(d):
        d["team_neutral"]["audit"]["state_frame"]["score_msu"]["to"] = "score_our"
    assert any("new name score_our" in p for p in mutated(rename, "changes"))

    def enum(d):
        d["team_neutral"]["audit"]["timeouts"]["team"] = {"action": "enum", "values_map": {"msu": "us", "opponent": "them"}, "why": "x"}
    assert any("still team-relative" in p for p in mutated(enum, "changes"))

    def new_col(d):
        d["new_tables"]["team_game_pbp"]["columns"].append({"column": "points_msu", "type": "int16", "definition": "x"})
    assert any("team_game_pbp.points_msu" in p for p in mutated(new_col, "changes"))

    def opp_in_stored(d):
        d["new_tables"]["team_game_pbp"]["columns"].append({"column": "opp_points", "type": "int16", "definition": "x"})
    assert any("team_game_pbp.opp_points" in p for p in mutated(opp_in_stored, "changes"))

    def focus_in_grain_view(d):
        d["views"]["v_game"]["columns"].append("score_focus")
    assert any("v_game.score_focus" in p for p in mutated(focus_in_grain_view, "changes"))

    def default_focus(d):
        d["views"]["focus_game"]["default_focus"] = "127"
    assert any("no default focus team" in p for p in mutated(default_focus, "changes"))

    def no_param(d):
        d["views"]["focus_game"]["parameters"] = []
    assert any("takes focus_team_id as a parameter" in p for p in mutated(no_param, "changes"))


def test_every_block_of_the_change_set_says_not_applied():
    for section in ("new_tables", "views"):
        for name, spec in CHANGES[section].items():
            assert spec["status"].startswith("not applied"), name
    for name in CHANGES["column_additions"]:
        assert CHANGES["column_additions_status"][name].startswith("not applied"), name
    for block in ("harness_proposals", "state_machine_proposals", "requirement_text_fixes"):
        for entry in CHANGES[block]:
            assert entry["status"].startswith("not applied"), entry

    def applied(d):
        d["new_tables"]["pbp_versions"]["status"] = "applied"
    assert any("pbp_versions: status does not start with" in p for p in mutated(applied, "changes"))


def test_relative_problem_rules():
    assert dplib.relative_problem("score_home") is None
    assert dplib.relative_problem("score_msu")
    assert dplib.relative_problem("opp_points")
    assert dplib.relative_problem("opp_points", layer="team_keyed") is None
    assert dplib.relative_problem("opponent_lineup_key", row_relative=True) is None
    assert dplib.relative_problem("score_focus")
    assert dplib.relative_problem("score_focus", layer="focus") is None
    assert dplib.relative_problem("bonus_status") is None        # "us" only counts as a whole token
    assert dplib.relative_problem("status") is None


# ---------------------------------------------------------------------------------------- canonical form and hashes
def test_canonical_json_test_vectors():
    # A port of dplib.canonical_json must reproduce these bytes and digests.
    assert dplib.canonical_json({"b": 1, "a": [1, 2.5, None, True, "x"]}) == b'{"a":[1,2.5,null,true,"x"],"b":1}'
    assert dplib.canonical_json({"k": "é ü", "z": -0.0, "t": (1, 2)}) == '{"k":"é ü","t":[1,2],"z":0.0}'.encode("utf-8")
    assert dplib.canonical_json(1.0) == b"1.0" and dplib.canonical_json(1) == b"1"
    assert dplib.canonical_json(0.1 + 0.2) == b"0.30000000000000004"
    assert dplib.content_hash({"b": 1, "a": [1, 2.5, None, True, "x"]}) == "6e71f2554609a67eb2c788231116a3f84477fee89d4f2e87660d343e3ed31782"
    assert dplib.sha256_hex(b"") == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert dplib.content_hash([]) == "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"


def test_hash_is_stable_under_key_order_and_differs_on_content():
    a = {"period": 1, "secondsRemaining": 600, "nested": {"x": 1.5, "y": [3, 2, 1]}}
    b = {"nested": {"y": [3, 2, 1], "x": 1.5}, "secondsRemaining": 600, "period": 1}
    assert dplib.content_hash(a) == dplib.content_hash(b)
    assert dplib.content_hash(a) != dplib.content_hash({**a, "period": 2})
    assert dplib.content_hash({"y": [3, 2, 1]}) != dplib.content_hash({"y": [1, 2, 3]})     # list order is content
    assert dplib.content_hash({"a": None}) != dplib.content_hash({})                          # null is not absent
    assert dplib.content_hash({"a": 1}) != dplib.content_hash({"a": 1.0})                     # int is not float
    assert dplib.content_hash({"a": "1"}) != dplib.content_hash({"a": 1})


def test_canonical_json_refuses_what_has_no_canonical_form():
    for bad in (float("nan"), float("inf"), {1: "int key"}, {"a": {2, 3}}, {"a": b"bytes"}):
        with pytest.raises((ValueError, TypeError)):
            dplib.canonical_json(bad)


def test_hash_is_the_same_in_a_fresh_process():
    code = ("import sys; sys.path.insert(0, %r); import dplib; "
            "print(dplib.det_id('tr', 'G1', 'pbp_only', 'G1:cbbd:77', 'T05', 0), dplib.content_hash({'b': [1, 2], 'a': 'x'}))"
            % str(ROOT / "tools" / "specgen" / "platform"))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="12345")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env).stdout.split()
    assert out == [dplib.det_id("tr", "G1", "pbp_only", "G1:cbbd:77", "T05", 0), dplib.content_hash({"b": [1, 2], "a": "x"})]


# ---------------------------------------------------------------------------------------------------- deterministic ids
def test_det_id_shape_and_determinism():
    a = dplib.det_id("tr", "G1", "pbp_only", "G1:cbbd:77", "T05", 0)
    assert a == dplib.det_id("tr", "G1", "pbp_only", "G1:cbbd:77", "T05", 0)
    assert a.startswith("tr-") and len(a) == 3 + dplib.ID_HEX_LEN
    assert a != dplib.det_id("tr", "G1", "pbp_only", "G1:cbbd:77", "T05", 1)       # k
    assert a != dplib.det_id("tr", "G1", "pbp_only", "G1:cbbd:78", "T05", 0)       # trigger
    assert a != dplib.det_id("sg", "G1", "pbp_only", "G1:cbbd:77", "T05", 0)       # prefix is part of the id's meaning
    assert dplib.det_id("tr", "ab", "c") != dplib.det_id("tr", "a", "bc")          # parts do not run together
    assert dplib.det_id("tr", 1) != dplib.det_id("tr", "1")


def test_det_id_refuses_unknown_prefixes_and_the_run_prefix():
    for prefix in ("xx", "run", ""):
        with pytest.raises(ValueError):
            dplib.det_id(prefix, "a")
    with pytest.raises(ValueError):
        dplib.det_id("tr")


def test_transition_id_does_not_move_with_clock_or_order():
    # The id rule of the pack: (game, pass, trigger event, ttype, k). A clock fix or an inserted neighbour keeps it.
    made_from = PACK["cross_item"]["ids"]["transition_id"]["made_from"]
    assert len(made_from) == 5
    before = dplib.det_id("tr", "G1", "pbp_only", dplib.event_id("G1", "cbbd", "0077"), "T08", 0)
    assert before == "tr-2d692e9ed3681eb1"                                  # test vector for a port
    after_clock_fix = dplib.det_id("tr", "G1", "pbp_only", dplib.event_id("G1", "cbbd", "0077"), "T08", 0)
    assert before == after_clock_fix
    seg = dplib.det_id("sg", "G1", "pbp_only", "possession_team", "", before)
    assert seg == dplib.det_id("sg", "G1", "pbp_only", "possession_team", "", after_clock_fix)


def test_event_id_is_readable_and_strict():
    assert dplib.event_id("G1", "cbbd", "0077") == "G1:cbbd:0077"
    for bad in (("G1", "cbbd", None), ("G1", "", "7"), ("G:1", "cbbd", "7")):
        with pytest.raises(ValueError):
            dplib.event_id(*bad)


def test_run_id_is_an_event_not_content():
    a, b = dplib.new_run_id("2026-11-11T10:00:00.000000Z"), dplib.new_run_id("2026-11-11T10:00:00.000000Z")
    assert a != b and a.startswith("run-20261111T100000Z-")


def test_row_hash_and_slice_hash():
    rows = [{"id": "b", "side": "home", "points": 2, "possession_id": 7}, {"id": "a", "side": "away", "points": 0, "possession_id": 8}]
    assert dplib.row_hash(rows[0]) != dplib.row_hash(rows[1])
    assert dplib.row_hash(rows[0], exclude=("possession_id",)) == dplib.row_hash({**rows[0], "possession_id": 99}, exclude=("possession_id",))
    full = dplib.slice_hash(rows, ["id", "side", "points", "possession_id"], ["id"])
    assert full == dplib.slice_hash(list(reversed(rows)), ["id", "side", "points", "possession_id"], ["id"])     # row order is not content
    # A stage that does not read the ordinal column is not re-run by a renumbering (rule X-4, DD-LN-3).
    renumbered = [dict(r, possession_id=r["possession_id"] + 1) for r in rows]
    assert dplib.slice_hash(rows, ["id", "side", "points"], ["id"]) == dplib.slice_hash(renumbered, ["id", "side", "points"], ["id"])
    assert full != dplib.slice_hash(renumbered, ["id", "side", "points", "possession_id"], ["id"])
    with pytest.raises(ValueError):
        dplib.slice_hash(rows, ["side"], ["id"])


def test_config_hash_reads_parsed_keys_not_bytes(tmp_path):
    (tmp_path / "c.yaml").write_text("a: {x: 1, y: 2}\nb: 3\n")
    h = dplib.config_hash([("c.yaml", ["a.x"])], repo=tmp_path)
    (tmp_path / "c.yaml").write_text("# a comment\nb: 4\na:\n  y: 9\n  x: 1\n")      # comment, order, undeclared keys
    assert dplib.config_hash([("c.yaml", ["a.x"])], repo=tmp_path) == h
    (tmp_path / "c.yaml").write_text("a: {x: 2, y: 2}\nb: 3\n")
    assert dplib.config_hash([("c.yaml", ["a.x"])], repo=tmp_path) != h
    assert h.startswith("cf-")


def test_code_version_follows_the_declared_files(tmp_path):
    (tmp_path / "s.py").write_text("x = 1\n")
    (tmp_path / "other.py").write_text("y = 1\n")
    v = dplib.code_version(["s.py"], repo=tmp_path)
    (tmp_path / "other.py").write_text("y = 2\n")
    assert dplib.code_version(["s.py"], repo=tmp_path) == v
    (tmp_path / "s.py").write_text("x = 2\n")
    assert dplib.code_version(["s.py"], repo=tmp_path) != v
    (tmp_path / "s.py").write_text("x = 1\n")
    (tmp_path / "uv.lock").write_text("lock 1\n")
    assert dplib.code_version(["s.py"], repo=tmp_path) != v                        # the environment is part of the code


def test_output_key_and_state_version():
    k = dplib.output_key("state_fold", "cv-1", "cf-1", [("events", "h1"), ("games", "h2")])
    assert k == dplib.output_key("state_fold", "cv-1", "cf-1", [("games", "h2"), ("events", "h1")])   # inputs are sorted
    assert k != dplib.output_key("state_fold", "cv-2", "cf-1", [("events", "h1"), ("games", "h2")])
    assert k != dplib.output_key("state_fold", "cv-1", "cf-2", [("events", "h1"), ("games", "h2")])
    assert k != dplib.output_key("state_fold", "cv-1", "cf-1", [("events", "h9"), ("games", "h2")])
    assert k != dplib.output_key("game_gate", "cv-1", "cf-1", [("events", "h1"), ("games", "h2")])
    assert dplib.state_version(k) == "sv-" + k[3:]
    with pytest.raises(ValueError):
        dplib.state_version("pv-123")


# ---------------------------------------------------------------------------------------------- the two write guards
def test_guard_refuses_to_write_inside_the_repo(tmp_path, monkeypatch):
    for inside in (ROOT / "results" / "platform_test" / "rows.parquet", ROOT / "x.json", ROOT):
        with pytest.raises(dplib.PrivatePathError):
            dplib.ensure_private(inside)
    with pytest.raises(dplib.PrivatePathError):
        dplib.atomic_write(ROOT / "results" / "platform_test" / "licensed_rows.json", b"[]")
    assert not (ROOT / "results" / "platform_test" / "licensed_rows.json").exists()
    monkeypatch.setenv(dplib.PRIVATE_ENV, str(tmp_path))
    p = dplib.atomic_write(tmp_path / "lake" / "a.bin", b"abc")
    assert p.read_bytes() == b"abc" and not list(p.parent.glob(".*tmp"))


def test_guard_refuses_tmp_unless_a_private_root_is_set(monkeypatch):
    monkeypatch.delenv(dplib.PRIVATE_ENV, raising=False)
    with pytest.raises(dplib.PrivatePathError):
        dplib.ensure_private("/tmp/platform_rows.parquet")


def test_scratch_dir_is_under_the_private_root(tmp_path, monkeypatch):
    monkeypatch.setenv(dplib.PRIVATE_ENV, str(tmp_path))
    d = dplib.scratch_dir("core")
    assert d == (tmp_path / "work" / dplib.SCRATCH_DATE / "core").resolve() and d.is_dir()
    with pytest.raises(ValueError):
        dplib.scratch_dir("../escape")


def test_public_result_guard_refuses_licensed_fields_ids_and_names(tmp_path):
    ok = {"totals": {"games": 37, "untyped_transitions": 0}, "per_game": {"P01": {"breaks": 2}}}
    dplib.assert_public_safe(ok, forbidden={"Some College", "990000001"})
    for bad in ({"per_game": {"P01": {"playText": "made up"}}}, {"sample": [{"participants": []}]},
                {"note": "game 990000001 failed"}, {"note": "Some College at home"}, {"id": 990000001},
                {"x": {"onFloor": []}}):
        with pytest.raises(dplib.PublicResultError):
            dplib.assert_public_safe(bad, forbidden={"Some College", "990000001"})
    path = dplib.write_public_result("guard_test", ok, results_dir=tmp_path)
    assert json.loads(path.read_text()) == ok
    with pytest.raises(dplib.PublicResultError):
        dplib.write_public_result("guard_test", {"rows": [1]}, results_dir=tmp_path)
    with pytest.raises(ValueError):
        dplib.write_public_result("../x", ok, results_dir=tmp_path)


# -------------------------------------------------------------------------------------------------------- run records
def test_stage_run_writes_one_record_with_duration_cost_and_keys(tmp_path, monkeypatch):
    monkeypatch.setenv(dplib.PRIVATE_ENV, str(tmp_path))
    with dplib.stage_run("state_fold", "core", config_refs=[("config/state_machine.yaml", ["constants"])],
                         code_files=["tools/specgen/platform/dplib.py"], seed=7) as run:
        run.add_input("events", "h1", rows=470)
        run.add_input("games", "h2", rows=1)
        key = run.output_key()
        run.add_output("state_transitions", key, rows=507, content="c1", bytes_=1234, file_sha="f1")
        run.count("TRN-03", 2)
        run.note("synthetic")
    files = list((tmp_path / "work" / dplib.SCRATCH_DATE / "core" / "runs").glob("run-*.json"))
    assert len(files) == 1
    doc = json.loads(files[0].read_text())
    assert doc["status"] == "ok" and doc["stage"] == "state_fold" and doc["run_id"] == files[0].stem
    assert doc["duration_s"] >= 0 and doc["cost"]["cpu_s"] >= 0 and doc["cost"]["api_calls"] == 0
    assert doc["config_hash"].startswith("cf-") and doc["code_version"].startswith("cv-")
    assert doc["inputs"][0] == {"name": "events", "key": "h1", "rows": 470, "kind": "slice"}
    assert doc["outputs"][0]["output_key"] == key and key.startswith("ok-")
    assert doc["counts"] == {"TRN-03": 2} and doc["started_utc"] <= doc["finished_utc"]
    # the key does not depend on the run: a second run with the same inputs gives the same key and a new record
    with dplib.stage_run("state_fold", "core", config_refs=[("config/state_machine.yaml", ["constants"])],
                         code_files=["tools/specgen/platform/dplib.py"]) as run2:
        run2.add_input("games", "h2", rows=1)
        run2.add_input("events", "h1", rows=470)
        assert run2.output_key() == key
        run2.skipped()
    docs = [json.loads(f.read_text()) for f in (tmp_path / "work" / dplib.SCRATCH_DATE / "core" / "runs").glob("run-*.json")]
    assert sorted(d["status"] for d in docs) == ["ok", "skipped_cached"] and len({d["run_id"] for d in docs}) == 2


def test_a_failed_stage_still_leaves_its_record(tmp_path, monkeypatch):
    monkeypatch.setenv(dplib.PRIVATE_ENV, str(tmp_path))
    with pytest.raises(RuntimeError):
        with dplib.stage_run("game_gate", "core") as run:
            run.add_input("state_segments", "h3")
            raise RuntimeError("boom")
    doc = json.loads(next((tmp_path / "work" / dplib.SCRATCH_DATE / "core" / "runs").glob("run-*.json")).read_text())
    assert doc["status"] == "failed" and "boom" in doc["error"] and doc["finished_utc"]


def test_stage_run_refuses_a_scratch_inside_the_repo():
    with pytest.raises(dplib.PrivatePathError):
        with dplib.stage_run("state_fold", "core", scratch=ROOT / "results" / "platform_test"):
            pass


# ----------------------------------------------------------------------------------------------- private data discovery
def _fake_private(tmp_path):
    cbbd = tmp_path / "data" / "licensed" / "cbbd"
    (cbbd / "2026-01-01" / "plays").mkdir(parents=True)
    (cbbd / "2026-02-01" / "plays").mkdir(parents=True)
    games = [{"id": 900 + i, "sourceId": f"SRC{i}", "homeTeam": f"Home College {i}", "awayTeam": f"Away Tech {i}",
              "homePoints": 70, "awayPoints": 60, "season": 2026 if i < 3 else 2027} for i in range(4)]
    (cbbd / "2026-01-01" / "02_games_msu.json").write_text(json.dumps(games[:3]))
    (cbbd / "2026-02-01" / "01_games_msu_2027.json").write_text(json.dumps(games[3:]))
    row = lambda gid: [{"gameId": gid, "period": 1, "secondsRemaining": 1200, "playText": "made up"}]  # noqa: E731
    (cbbd / "2026-01-01" / "03_plays_game.json").write_text(json.dumps(row(902)))
    (cbbd / "2026-01-01" / "plays" / "900.json").write_text(json.dumps(row(900)))
    (cbbd / "2026-01-01" / "plays" / "901.json").write_text(json.dumps(row(901)))
    (cbbd / "2026-02-01" / "plays" / "903.json").write_text(json.dumps(row(903)))
    (cbbd / "2026-02-01" / "plays" / "900.json").write_text(json.dumps(row(900) * 2))     # a second pull of game 900
    (cbbd / "2026-02-01" / "plays" / "broken.json").write_text("not json")
    return games


def test_discover_games_gives_stable_codes_and_never_names(tmp_path):
    _fake_private(tmp_path)
    games = dplib.discover_games(tmp_path)
    assert [g.code for g in games] == ["P01", "P02", "P03", "P04"]
    assert [g.cbbd_game_id for g in games] == [902, 900, 901, 903]         # single-game file first, then plays/ by name
    assert [g.season_label for g in games] == ["S1", "S1", "S1", "S2"]
    assert [len(g.pulls) for g in games] == [1, 2, 1, 1]                   # the later file is a second pull, not a new code
    assert len(games.by_code("P02").load_plays()) == 2 and len(games.by_code("P02").load_plays(0)) == 1
    text = repr(list(games)) + str(games[0]) + f"{games[1]}"
    assert "College" not in text and "900" not in text and "SRC" not in text and "/" not in text
    forbidden = games.forbidden_strings()
    assert {"Home College 0", "Away Tech 3", "SRC1"} <= forbidden
    with pytest.raises(dplib.PublicResultError):
        dplib.assert_public_safe({"note": "home college 2 won"}, forbidden)
    assert dplib.discover_games(tmp_path / "nothing_here") == []


# ----------------------------------------------------------------------------- real data (skipped when it is absent)
REAL = dplib.discover_games()
needs_private = pytest.mark.skipif(not REAL, reason="private play-by-play not present")


@needs_private
def test_real_data_is_discovered_as_codes_only():
    assert len(REAL) >= 37 and [g.code for g in REAL[:3]] == ["P01", "P02", "P03"]
    assert len({g.cbbd_game_id for g in REAL}) == len(REAL)
    assert all(g.record_file for g in REAL), "a held game has no game record"
    dplib.assert_public_safe({"codes": [g.code for g in REAL], "seasons": sorted({g.season_label for g in REAL})}, REAL.forbidden_strings())


@needs_private
def test_real_play_rows_hash_the_same_twice_and_the_guard_knows_their_ids():
    g = REAL[0]
    plays = g.load_plays()
    assert dplib.content_hash(plays) == dplib.content_hash(json.loads(json.dumps(plays)))
    assert dplib.content_hash(plays) != dplib.content_hash(plays[:-1])
    with pytest.raises(dplib.PublicResultError):
        dplib.assert_public_safe({"per_game": {g.code: {"first_row": plays[0]}}}, REAL.forbidden_strings())
    with pytest.raises(dplib.PublicResultError):
        dplib.assert_public_safe({"note": f"game {g.cbbd_game_id}"}, REAL.forbidden_strings())
