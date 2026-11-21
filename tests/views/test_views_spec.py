"""Lint of the views catalogue (config/views/*.yaml), the palette contrast check, and tests of the lint itself."""
from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "views"))

import vwlib  # noqa: E402

VWLIB = ROOT / "tools" / "specgen" / "views" / "vwlib.py"
CORE = vwlib.load_core()
VIEWS = vwlib.load_views()
REFS = vwlib.Refs()
WRITTEN = [stem for stem in vwlib.VIEW_FILES if (vwlib.PACK_DIR / f"{stem}.yaml").exists()]
LIVE, REVIEW, STUDIO = "live_game_state_panel", "possession_explorer", "studio_game_canvas"


# --------------------------------------------------------------------------------------------------------------------
# the pack as written
def test_core_alone_is_valid():
    assert vwlib.validate(CORE, {}, require_all=False) == []


def test_the_three_views_files_exist():
    assert WRITTEN == vwlib.VIEW_FILES


@pytest.mark.parametrize("stem", vwlib.VIEW_FILES)
def test_each_views_file_passes_the_lint(stem):
    views = vwlib.load_views([stem])
    assert views, f"{stem}.yaml has no records"
    assert vwlib.validate(CORE, views, require_all=False) == []


def test_the_three_worked_examples_are_present():
    for key, stem in ((LIVE, "views_live"), (REVIEW, "views_review"), (STUDIO, "views_studio")):
        assert VIEWS[key]["_file"] == stem


def test_whole_pack_reports_only_index_entries_without_a_record():
    problems = vwlib.validate(CORE, VIEWS, require_all=True)
    other = [p for p in problems if not p.startswith(vwlib.MISSING)]
    assert other == []
    missing = {k for k in CORE["view_index"] if k not in VIEWS}
    assert len(problems) == len(missing)
    for k in missing:
        assert any(p.startswith(f"{vwlib.MISSING} {k} ") for p in problems)


def test_whole_pack_when_every_index_entry_has_a_record():
    missing = [k for k in CORE["view_index"] if k not in VIEWS]
    if missing:
        pytest.skip(f"{len(missing)} index entries have no record yet")
    assert vwlib.validate(CORE, VIEWS, require_all=True) == []


def test_index_is_complete_and_gap_free():
    index = CORE["view_index"]
    by_code = {}
    for e in index.values():
        code, num = vwlib.VIEW_ID_RE.match(e["id"]).groups()
        by_code.setdefault(code, []).append(int(num))
    assert set(by_code) == {s["code"] for s in CORE["surfaces"].values()}
    for nums in by_code.values():
        assert sorted(nums) == list(range(1, len(nums) + 1))
    assert len({e["id"] for e in index.values()}) == len(index)


def test_every_required_requirement_row_has_a_view():
    rows = CORE["inventory"]["rows"]
    for rid in CORE["inventory"]["required_rows"]:
        assert any(rid in (r.get("req") or []) and r.get("view") in CORE["view_index"] for r in rows), rid
    want = {f"R-VZ-{n:02d}" for n in (1, 2, 3, 4, 5, 7, 8, 9, 10, 11)} | {f"R-VZ-06{c}" for c in "abcdefghij"}
    want |= {f"R-AS-{n:02d}" for n in range(1, 13)} | {"R-PR-14", "R-PR-15", "R-PR-16"}
    assert set(CORE["inventory"]["required_rows"]) == want


def test_inventory_covers_every_live_state_group_and_registry_category():
    rows = CORE["inventory"]["rows"]
    assert {r["live_state_group"] for r in rows if "live_state_group" in r} == REFS.ls_groups()
    assert {r["metric_category"] for r in rows if "metric_category" in r} == REFS.metric_categories()


def test_the_live_panel_maps_every_live_state_field():
    rec = VIEWS[LIVE]
    shown = {REFS.ls_key(f) for el in rec["elements"] for f in (el.get("inputs") or {}).get("live_state") or []}
    assert shown | set(rec.get("not_shown") or {}) == set(REFS.ls_index())
    levels = REFS.levels()
    for el in rec["elements"]:
        if (el.get("inputs") or {}).get("live_state"):
            assert list(el["by_level"]) == levels, el["key"]


def test_the_grade_table_is_the_live_state_grade_ladder():
    assert list(CORE["display_contract"]["grades"]["appearance"]) == REFS.grades()
    assert CORE["display_contract"]["degraded"]["levels"] == [x for x in REFS.levels() if x != "D0_full"]


def test_cli_checks_one_file_and_the_whole_pack():
    def run(*args):
        return subprocess.run([sys.executable, str(VWLIB), *args], capture_output=True, text=True, cwd="/")
    one = run("--check", "config/views/views_live.yaml")
    assert one.returncode == 0 and "0 problems" in one.stdout
    missing = [k for k in CORE["view_index"] if k not in VIEWS]
    everything = run("--check")
    assert everything.returncode == (1 if missing else 0)
    assert f"{len(missing)} problems" in everything.stdout
    assert run("--check", "config/views/does_not_exist.yaml").returncode == 2
    assert "text.primary" in run("--palette").stdout


def test_a_key_written_twice_is_refused(tmp_path):
    bad = tmp_path / "views_twice.yaml"
    bad.write_text("views:\n  a_view: {id: VW-REV-01}\n  a_view: {id: VW-REV-02}\n")
    out = subprocess.run([sys.executable, str(VWLIB), "--check", str(bad)], capture_output=True, text=True)
    assert out.returncode == 2 and "written twice" in out.stdout


# --------------------------------------------------------------------------------------------------------------------
# palette
def test_contrast_formula_on_known_values():
    assert vwlib.contrast("#000000", "#FFFFFF") == pytest.approx(21.0)
    assert vwlib.contrast("#777777", "#777777") == pytest.approx(1.0)
    assert vwlib.luminance("#FFFFFF") == pytest.approx(1.0)
    assert vwlib.contrast("#767676", "#FFFFFF") == pytest.approx(4.54, abs=0.01)   # the well-known AA grey on white
    assert vwlib.contrast("#0072B2", "#FFFFFF") == vwlib.contrast("#FFFFFF", "#0072B2")


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_every_text_pair_reaches_4_5(theme):
    vs = CORE["display_contract"]["visual_standard"]
    tk = vwlib.tokens(CORE, theme)
    assert vs["params"]["text_contrast_min"]["value"] >= 4.5
    for p in vs["text_pairs"]:
        got = vwlib.contrast(tk[p["text"]], tk[p["bg"]])
        assert got >= 4.5, (theme, p["text"], p["bg"], got)
        assert p["ratio"][theme] == pytest.approx(got, abs=0.006)
    assert {n for n in tk if n.startswith("text.")} == {p["text"] for p in vs["text_pairs"]}


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_every_mark_and_categorical_colour_reaches_3(theme):
    vs = CORE["display_contract"]["visual_standard"]
    tk = vwlib.tokens(CORE, theme)
    for p in vs["graphic_pairs"]:
        assert vwlib.contrast(tk[p["mark"]], tk[p["bg"]]) >= 3.0, p
    cat = vs["categorical"]
    assert len(cat["set"]) >= 8
    for c in cat["set"]:
        assert vwlib.contrast(c["hex"], tk[cat["use_on"]]) >= 3.0, c


def test_the_note_on_light_surfaces_is_true():
    # the contract keeps charts on the dark surface because half of the categorical set fails on a white page
    cat = {c["name"]: c["hex"] for c in CORE["display_contract"]["visual_standard"]["categorical"]["set"]}
    white = CORE["display_contract"]["visual_standard"]["themes"]["light"]["bg.page"]
    failing = sorted(n for n, hx in cat.items() if vwlib.contrast(hx, white) < 3.0)
    assert failing == ["neutral", "orange", "sky blue", "yellow"]
    assert [round(vwlib.contrast(cat[n], white), 2) for n in ("orange", "sky blue", "yellow", "neutral")] == [2.25, 2.31, 1.32, 1.23]


def test_scales_rise_and_diverge():
    vs = CORE["display_contract"]["visual_standard"]
    seq = [vwlib.luminance(s) for s in vs["sequential"]["stops"]]
    assert seq == sorted(seq) and len(set(seq)) == len(seq)
    div = [vwlib.luminance(s) for s in vs["diverging"]["stops"]]
    assert div.index(max(div)) == len(div) // 2


def _core_with(mutate):
    core = copy.deepcopy(CORE)
    mutate(core)
    return vwlib.validate(core, {}, require_all=False)


def test_palette_lint_catches_a_weak_text_colour():
    def weak(core):
        core["display_contract"]["visual_standard"]["themes"]["light"]["text.stale"] = "#9AA3AF"
    problems = _core_with(weak)
    assert any("text.stale" in p and "below 4.5" in p for p in problems)
    assert any("text.stale" in p and "differs from the computed" in p for p in problems)


def test_palette_lint_catches_a_wrong_stored_ratio_a_short_set_and_a_bad_scale():
    def wrong(core):
        vs = core["display_contract"]["visual_standard"]
        vs["text_pairs"][0]["ratio"]["dark"] = 9.99
        vs["categorical"]["set"] = vs["categorical"]["set"][:7]
        vs["sequential"]["stops"] = list(reversed(vs["sequential"]["stops"]))
        vs["diverging"]["stops"][3] = "#000000"
        vs["themes"]["dark"].pop("text.link")
    problems = _core_with(wrong)
    for needle in ("stored ratio 9.99", "at least 8 are required", "luminance must rise", "middle stop must be the lightest", "light and dark differ"):
        assert any(needle in p for p in problems), needle


def test_palette_lint_refuses_a_text_minimum_below_4_5():
    def low(core):
        core["display_contract"]["visual_standard"]["params"]["text_contrast_min"]["value"] = 3.0
    assert any("must be at least 4.5" in p for p in _core_with(low))


# --------------------------------------------------------------------------------------------------------------------
# references into the other baselines
def test_references_resolve_against_the_other_packs():
    assert REFS.ls_key("game_clock_s") == "game_clock_s"
    assert REFS.ls_key("LS-TIME-03") == "game_clock_s"
    assert REFS.ls_key("game_clock") is None
    assert REFS.column_state("state_transitions.known_at_utc") == "schema"
    assert REFS.column_state("clip_index.in_s") == "proposed"
    assert REFS.column_state("state_transitions.nope") is None and REFS.column_state("no_table.x") is None
    assert "M-SIT-055" in REFS.metric_ids() and "M-SIT-999" not in REFS.metric_ids()
    assert REFS.spot_ok("elbow") and REFS.spot_ok("layer:spot") and REFS.spot_ok("layer:zone_scheme:court_region")
    assert not REFS.spot_ok("layer:nope") and not REFS.spot_ok("free_throw_line_extended_typo")
    assert REFS.event_kind("T05") == "transition" and REFS.event_kind("T27") is None
    assert REFS.event_kind("dim:flow_state") == "dimension" and REFS.event_kind("dim:nope") is None
    assert REFS.event_kind("screens:ball_screen") == "grammar" and REFS.event_kind("screens:nope") is None
    assert REFS.event_kind("ball_screen") is None   # a grammar item needs its family


def test_unit_scan():
    banned = CORE["display_contract"]["visual_standard"]["banned_units"]
    ok = {"a": "4.2 m from the rim, 2 free throws (FT), ft_state, footwork, 3 in a row", "unit": "m"}
    assert vwlib.unit_problems(ok, banned) == []
    for bad in ({"a": "a 20 ft jumper"}, {"a": "distance in feet"}, {"x": {"unit": "ft"}}, {"a": ["speed 12 mph"]}, {"a": "6 inches off"}):
        assert vwlib.unit_problems(bad, banned), bad


# --------------------------------------------------------------------------------------------------------------------
# tests of the lint itself: a bad record must be caught
def _el(rec, key):
    return next(e for e in rec["elements"] if e["key"] == key)


def _problems(view_key, mutate):
    views = vwlib.good_copy(VIEWS, view_key)
    mutate(views[view_key])
    return vwlib.validate(CORE, views, require_all=False)


def _append(path_fn, value):
    return lambda rec: path_fn(rec).append(value)


BAD = [
    # (name, view, mutation, text the lint must print)
    ("unknown live-state key", LIVE, _append(lambda r: _el(r, "score")["inputs"]["live_state"], "score_total"), "unknown live-state key 'score_total'"),
    ("unknown live-state id", LIVE, _append(lambda r: _el(r, "score")["inputs"]["live_state"], "LS-SCORE-99"), "unknown live-state key 'LS-SCORE-99'"),
    ("unknown metric id", LIVE, _append(lambda r: _el(r, "score")["inputs"]["metrics"], "M-SIT-999"), "unknown metric id 'M-SIT-999'"),
    ("metric written as a formula", LIVE, _append(lambda r: _el(r, "score")["inputs"]["metrics"], "points / possessions"), "unknown metric id"),
    ("unknown table column", LIVE, _append(lambda r: _el(r, "score")["inputs"]["tables"], "score_events.nope"), "unknown table.column 'score_events.nope'"),
    ("unknown spot", REVIEW, _append(lambda r: _el(r, "court")["inputs"]["spots"], "elbwo"), "unknown named-spots id or layer 'elbwo'"),
    ("unknown event", REVIEW, _append(lambda r: _el(r, "set_overlay")["inputs"]["events"], "T99"), "unknown event id 'T99'"),
    ("grammar id without its family", REVIEW, _append(lambda r: _el(r, "set_overlay")["inputs"]["events"], "set_match"), "unknown event id 'set_match'"),
    ("missing degraded state", LIVE, lambda r: r["degraded"].pop("D3_replay"), "degraded state D3_replay is missing"),
    ("empty degraded state", REVIEW, lambda r: r["degraded"].update(D5_no_video=""), "degraded state D5_no_video is missing"),
    ("degraded state that is no level", LIVE, lambda r: r["degraded"].update(D9_fog="x"), "degraded state 'D9_fog' is not a level"),
    ("live view reading as_of_event", LIVE, lambda r: r["as_of"].update(view="as_of_event"), "a live_panel view reads as_of_known only"),
    ("live view reading mixed", LIVE, lambda r: r["as_of"].update(view="mixed"), "a live_panel view reads as_of_known only"),
    ("live element reading as_of_event", LIVE, lambda r: _el(r, "score").update(as_of="as_of_event"), "cannot read as_of_event"),
    ("review view without a pass", REVIEW, lambda r: r["as_of"].update({"pass": []}), "names its pass"),
    ("mixed view with an unmarked element", STUDIO, lambda r: _el(r, "court").pop("as_of"), "the view is mixed, so the element states its as_of"),
    ("embedded live panel as of event", STUDIO, lambda r: _el(r, "state_panel").update(as_of="as_of_event"), "an embedded live panel reads as_of_known"),
    ("number without a number_rule", LIVE, lambda r: _el(r, "score").pop("number_rule"), "element score: shows a number but has no number_rule"),
    ("metric on an overlay without a number_rule", REVIEW, lambda r: _el(r, "trails_and_arrows").pop("number_rule"), "shows a number but has no number_rule"),
    ("estimate without n", REVIEW, lambda r: _el(r, "action_list").update(number_rule={"class": "estimate", "interval": "shown", "level": 0.95, "link": "frames", "min_n": "default"}), "number_rule of class estimate lacks n"),
    ("number without a link", LIVE, lambda r: _el(r, "score")["number_rule"].pop("link"), "lacks link"),
    ("unknown number class", LIVE, lambda r: _el(r, "score")["number_rule"].update({"class": "vibes"}), "number_rule class"),
    ("a feet unit in the text", LIVE, lambda r: _el(r, "mini_court").update(shows="Players from above, distance to the rim in feet."), "names a non-metric unit"),
    ("a feet unit after a number", REVIEW, lambda r: _el(r, "court").update(shows="A marker within 3 ft of the rim."), "names a non-metric unit"),
    ("a feet unit key", REVIEW, lambda r: _el(r, "matchups")["number_rule"][1].update(unit="inches"), "unit 'inches' is not metric"),
    ("unknown audience", LIVE, lambda r: r.update(audience=["owner", "fans"]), "audience"),
    ("audience the privacy class forbids", LIVE, lambda r: r.update(audience=["owner", "public_demo"]), "audience public_demo may not see a view of privacy class msu_staff"),
    ("unknown privacy class", LIVE, lambda r: r.update(privacy="everyone"), "privacy 'everyone' is not one of"),
    ("player grain in a public view", REVIEW, lambda r: r.update(grain="player-game", privacy="public_demo", audience=["public_demo"]), "an individual player output cannot have privacy class public_demo"),
    ("video in a shareable view", REVIEW, lambda r: r.update(privacy="shareable_aggregate", audience=["owner"]), "cannot show video"),
    ("export the class forbids", LIVE, lambda r: r["interactions"].append({"action": "export", "at": "view", "target": "rows", "produces": "sql"}), "does not allow the export sql"),
    ("export of an unknown kind", STUDIO, lambda r: r["interactions"].append({"action": "export", "at": "view", "target": "a clip", "produces": "video_upload"}), "export produces 'video_upload'"),
    ("no acceptance test", LIVE, lambda r: r.update(acceptance=[]), "names no acceptance test"),
    ("unknown acceptance id", LIVE, lambda r: r["acceptance"].append("ACC-VW-99"), "acceptance 'ACC-VW-99' is not defined"),
    ("no requirement", STUDIO, lambda r: r.update(requirements=[]), "cites no requirement"),
    ("requirement of the inventory not cited", LIVE, lambda r: (r["requirements"].remove("R-VZ-06g"), _el(r, "foul_tracker")["requirements"].remove("R-VZ-06g")), "the inventory assigns R-VZ-06g"),
    ("element of the inventory missing", LIVE, lambda r: r["elements"].remove(_el(r, "timeouts_left")), "the inventory expects an element 'timeouts_left'"),
    ("unknown refresh class", LIVE, lambda r: r.update(refresh={"class": "whenever"}), "is not a refresh class"),
    ("budget without evidence", LIVE, lambda r: r.update(refresh={"class": "on_event", "budget_s": 2}), "refresh.budget_s needs an evidence string"),
    ("identity without a rule", LIVE, lambda r: _el(r, "lineup_identity").pop("identity_rule"), "reads player identity, so identity_rule must be one of"),
    ("probable label on the live panel", LIVE, lambda r: _el(r, "mini_court").update(identity_rule="probable_flagged_offline"), "the probable tier is offline only"),
    ("probable label in a table", REVIEW, lambda r: _el(r, "action_list").update(identity_rule="probable_flagged_offline"), "never in a table"),
    ("a face image as input", REVIEW, _append(lambda r: _el(r, "possession_header")["inputs"]["tables"], "rosters.headshot_url"), "is banned (no face image in any view)"),
    ("quarantined value outside the review screens", LIVE, lambda r: _el(r, "lineup_identity")["grade_rule"].update(quarantined="shown in red"), "only the review screens may show a quarantined value"),
    ("grade that does not exist", LIVE, lambda r: _el(r, "lineup_identity")["grade_rule"].update(guessed="x"), "is not a grade"),
    ("data element without a grade rule", REVIEW, lambda r: _el(r, "value_curve").pop("grade_rule"), "lacks grade_rule"),
    ("tile without all levels", LIVE, lambda r: _el(r, "score")["by_level"].pop("D4_break"), "by_level must say what the tile shows at each of"),
    ("live-state field shown nowhere", LIVE, lambda r: _el(r, "score")["inputs"]["live_state"].remove("ties"), "live-state field ties is in no element and not in not_shown"),
    ("id that differs from the index", REVIEW, lambda r: r.update(id="VW-REV-02"), "differs from the index"),
    ("surface that differs from the index", REVIEW, lambda r: r.update(surface="studio"), "differs from the index"),
    ("element key written twice", REVIEW, lambda r: r["elements"].append(copy.deepcopy(_el(r, "matchups"))), "an element key is written twice"),
    ("unknown element kind", REVIEW, lambda r: _el(r, "matchups").update(kind="widget"), "kind 'widget' is not one of"),
    ("unknown key in a record", LIVE, lambda r: r.update(colour="blue"), "unknown key 'colour'"),
    ("unknown key in an element", LIVE, lambda r: _el(r, "score").update(grade_rules="contract"), "unknown key 'grade_rules'"),
    ("a bare on read as a boolean", LIVE, lambda r: r["interactions"][0].update({True: "view"}), "YAML reads a bare on"),
    ("component that does not exist", LIVE, lambda r: _el(r, "score").update(component="score_bug"), "component 'score_bug' does not exist"),
    ("component of another kind", LIVE, lambda r: _el(r, "score").update(component="video_player"), "component video_player is a video"),
    ("interaction on a missing element", LIVE, lambda r: r["interactions"][1].update(at="scoreboard"), "is neither the word view nor an element key"),
    ("interaction to a missing view", LIVE, lambda r: r["interactions"][1].update(to="shot_explorer"), "to 'shot_explorer' is not a view of the index"),
    ("unknown action", LIVE, lambda r: r["interactions"][0].update(action="pinch"), "is not in the interaction grammar"),
    ("no way to follow a number", LIVE, lambda r: r.update(interactions=[r["interactions"][-1]]), "no select or drill_down interaction"),
    ("baseline read but not declared", LIVE, lambda r: r["depends_on"]["baselines"].remove("live_state"), "reads the baseline live_state but depends_on does not name it"),
    ("table read but not declared", LIVE, lambda r: r["depends_on"]["tables"].remove("foul_state"), "reads the table foul_state but depends_on does not name it"),
    ("unknown table declared", LIVE, lambda r: r["depends_on"]["tables"].append("scoreboard_dreams"), "depends_on names the table 'scoreboard_dreams'"),
    ("no empty state", STUDIO, lambda r: r.update(empty_state=""), "empty_state is missing"),
    ("no question mark", STUDIO, lambda r: r.update(question="The state of the game"), "question must be one plain question"),
    ("unknown grain", STUDIO, lambda r: r.update(grain="moment"), "grain 'moment' is not one of"),
    ("wireframe outside the views folder", STUDIO, lambda r: r.update(wireframe="docs/wire.png"), "wireframe must be docs/data/views/<file>.svg or null"),
    ("param without evidence tag", LIVE, lambda r: r["params"]["clock_prov_max_s"].update(evidence="we think so"), "evidence must start with a tag"),
    ("param that left its mirror", LIVE, lambda r: r["params"]["clock_prov_max_s"].update(value=5.0), "differs from config/live_state/core.yaml"),
    ("param that left its measurement", LIVE, lambda r: r["params"]["hidden_stretch_median_s"].update(value=4), "differs from the measured 6"),
    ("element phase that is no phase", LIVE, lambda r: _el(r, "tactics").update(phase="P9"), "phase 'P9' is not a phase"),
    ("missing required key", STUDIO, lambda r: r.pop("privacy"), "lacks privacy"),
    ("number rule with a stray key", LIVE, lambda r: _el(r, "score")["number_rule"].update(stale="is added after a while"), "has the unknown key 'stale'"),
    ("live tile that skips a grade", LIVE, lambda r: _el(r, "score")["by_grade"].pop("carried"), "by_grade must say what the tile shows at each of"),
    ("wireframe state of an unknown level", LIVE, lambda r: r["wireframe_states"].update(D9_fog="docs/data/views/x.svg"), "which is not a degradation level"),
    ("wireframe state without a wireframe", LIVE, lambda r: r.update(wireframe=None), "beside a wireframe of the view at D0"),
    ("court that names no spot layer", "player_card", lambda r: _el(r, "spot_shooting_map")["inputs"].pop("spots"), "a court names the named-spots layers or ids it draws"),
    ("refresh class that does not exist", LIVE, lambda r: r.update(refresh={"class": "hourly"}), "is not a refresh class"),
]


@pytest.mark.parametrize("name,view,mutate,needle", BAD, ids=[b[0] for b in BAD])
def test_a_bad_record_is_caught(name, view, mutate, needle):
    problems = _problems(view, mutate)
    assert any(needle in p for p in problems), f"{name}: expected {needle!r} in {problems}"


def test_a_good_copy_stays_clean():
    for key in (LIVE, REVIEW, STUDIO):
        assert vwlib.validate(CORE, vwlib.good_copy(VIEWS, key), require_all=False) == []


def test_a_view_that_is_not_in_the_index_is_caught():
    views = {"shot_explorer": copy.deepcopy(VIEWS[REVIEW])}
    assert any("view shot_explorer: not in view_index" in p for p in vwlib.validate(CORE, views, require_all=False))


def test_two_records_with_one_id_are_caught():
    views = {REVIEW: copy.deepcopy(VIEWS[REVIEW]), "matchup_board": copy.deepcopy(VIEWS[REVIEW])}
    assert any("is also the id of" in p for p in vwlib.validate(CORE, views, require_all=False))


# --------------------------------------------------------------------------------------------------------------------
# tests of the lint itself: a bad core must be caught
BAD_CORE = [
    ("gap in the ids", lambda c: c["view_index"]["matchup_board"].update(id="VW-REV-12"), "are not 01.."),
    ("id used twice", lambda c: c["view_index"]["matchup_board"].update(id="VW-REV-01"), "is also"),
    ("id with the wrong surface code", lambda c: c["view_index"]["matchup_board"].update(id="VW-STU-11"), "does not carry the code of surface"),
    ("required row without a view", lambda c: c["inventory"]["rows"].__setitem__(slice(None), [r for r in c["inventory"]["rows"] if "R-VZ-06b" not in (r.get("req") or [])]), "required row R-VZ-06b is covered by no view"),
    ("inventory row to a missing view", lambda c: c["inventory"]["rows"].append({"item": "x", "view": "shot_explorer"}), "view 'shot_explorer' is not in the index"),
    ("live-state group without a row", lambda c: c["inventory"]["rows"].__setitem__(slice(None), [r for r in c["inventory"]["rows"] if r.get("live_state_group") != "tactics"]), "live-state groups differ"),
    ("registry category without a row", lambda c: c["inventory"]["rows"].__setitem__(slice(None), [r for r in c["inventory"]["rows"] if r.get("metric_category") != "TREE"]), "stat categories differ"),
    ("grade missing from the table", lambda c: c["display_contract"]["grades"]["appearance"].pop("imputed"), "differ from the live-state pack"),
    ("carried value without its age", lambda c: c["display_contract"]["grades"]["appearance"]["carried"].update(shows_age=False), "must show its age"),
    ("quarantined value visible everywhere", lambda c: c["display_contract"]["grades"]["appearance"]["quarantined"].update(visible_in="all"), "must be visible in the review queue only"),
    ("grade carried by colour alone", lambda c: c["display_contract"]["grades"]["appearance"]["inferred"].update(badge="none"), "needs a text badge"),
    ("surface without degraded defaults", lambda c: c["display_contract"]["degraded"]["defaults"]["card"].pop("D4_break"), "display_contract.degraded.defaults.card"),
    ("live surface allowing as_of_event", lambda c: c["surfaces"]["live_panel"]["as_of_allowed"].append("as_of_event"), "must allow as_of_known only"),
    ("component with an unknown column", lambda c: c["components"]["timeline"]["inputs"]["tables"].append("events.nope"), "component timeline: unknown table.column"),
    ("public class with video", lambda c: c["display_contract"]["privacy"]["classes"]["public_demo"].update(video=True), "may hold no video"),
    ("param without evidence", lambda c: c["refresh_classes"]["on_event"]["budget_s"].pop("evidence"), "param lacks evidence"),
    ("mirror that moved", lambda c: c["display_contract"]["grades"]["params"]["offscreen_marker_max_s"].update(value=8.0), "differs from config/live_state/core.yaml"),
    ("refresh policy without K23", lambda c: c["refresh_classes"].update(policy="latency is a gate"), "must state decision K23"),
    ("acceptance id written twice", lambda c: c["acceptance"].append(copy.deepcopy(c["acceptance"][0])), "an id is written twice"),
    ("open question without an answer", lambda c: c["open_questions"][0].update(recommended=""), "needs question, recommended answer and status"),
    ("fewer than 20 shortcut keys", lambda c: c["interaction_grammar"]["shortcuts"]["keys"].pop("z"), "fewer than 20 keys"),
    ("a feet unit in the contract", lambda c: c["components"]["top_down_court"]["behaviour"].append("The rim is 10 ft high."), "names a non-metric unit"),
    ("view from no inventory row", lambda c: c["view_index"].update(shot_explorer={"id": "VW-REV-11", "surface": "review", "file": "views_review", "name": "x", "phase": "P1"}), "view shot_explorer comes from no inventory row"),
    ("missing section", lambda c: c.pop("refresh_classes"), "section refresh_classes is missing"),
    ("reason for a row that is not reported", lambda c: c["inventory"]["no_view_rows"].update({"R-ZZ-01": "x"}), "must be a reported row"),
    ("follow-up without an owner", lambda c: c["follow_ups"][0].pop("owner"), "needs id, owner, where, what and why"),
]


def test_a_reported_row_needs_a_view_or_a_reason():
    core = copy.deepcopy(CORE)
    core["inventory"]["reported_rows"].append("R-HR-99")
    assert any("reported row R-HR-99 is cited by no record" in p for p in vwlib.validate(core, VIEWS, require_all=True))
    core = copy.deepcopy(CORE)
    core["inventory"]["no_view_rows"]["R-HR-02"] = "no reason"
    assert any("no_view_rows.R-HR-02: the row is cited by" in p for p in vwlib.validate(core, VIEWS, require_all=True))


@pytest.mark.parametrize("name,mutate,needle", BAD_CORE, ids=[b[0] for b in BAD_CORE])
def test_a_bad_core_is_caught(name, mutate, needle):
    problems = _core_with(mutate)
    assert any(needle in p for p in problems), f"{name}: expected {needle!r} in {problems[:5]}"
