"""Spec checks for config/named_spots.yaml (fast grid; the full 0.05 m check is tools/specgen/named_spots/check.py)."""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "named_spots"))
import check  # noqa: E402
import proptest  # noqa: E402
from check import entry_checks, partition_checks, probe_report  # noqa: E402
from spotlib import Spot, Values, court_region, frames_for, load, rules_sha  # noqa: E402

DOC, SPOTS = load()
E = {e["id"]: e for e in DOC["entries"]}
RESULTS = ROOT / "results" / "named_spots_test"


def variant(change):
    """A copy of the dictionary with one change applied (to show that a check can fail)."""
    doc = copy.deepcopy(DOC)
    change({e["id"]: e for e in doc["entries"]}, doc)
    return doc, {e["id"]: Spot(e) for e in doc["entries"]}


def labels(layer, x, y, **ctx):
    return [l for s in SPOTS.values() if s.d["layer"] == layer for l in s.labels(x, y, **ctx)]


def test_every_expr_passes_whitelist_and_ids_unique():
    ids = [e["id"] for e in DOC["entries"]]
    assert len(ids) == len(set(ids))
    assert sum(1 for s in SPOTS.values() if s.code) > 400


def test_anchors_probes_and_mirrors():
    """Every probe (static and with context), every value probe and every lint of check.py."""
    assert dict(entry_checks(DOC, SPOTS)) == {}


def test_every_exact_rule_has_an_executed_probe():
    bad, counts = probe_report(DOC, SPOTS)
    assert dict(bad) == {}
    assert [i for i, s in SPOTS.items() if s.code and not counts.get(i)] == []
    # context and relative entries are run, not skipped
    assert counts["box_high"] >= 5 and counts["help_side_two_away"] >= 6 and counts["short_roll_pocket"] >= 6


def test_an_entry_without_probes_fails():
    def strip(ents, doc):
        for k in ("anchor", "probes_inside", "probes_outside", "probes_ctx"):
            ents["nail_defender"].pop(k, None)

    bad, _ = probe_report(*variant(strip))
    assert bad["no_probe"] == ["nail_defender"]

    def no_ctx(ents, doc):
        del ents["nail_defender"]["probe_ctx"]

    bad, _ = probe_report(*variant(no_ctx))
    assert [b[0] for b in bad["probes_need_ctx"]] == ["nail_defender"] and bad["no_probe"] == ["nail_defender"]


def test_a_wrong_context_probe_fails():
    """The four mismatches of the 2026-11-11 audit would be caught now."""
    def old_box_high(ents, doc):
        ents["box_high"]["probes_outside"] = [[4.25, 4.6], [3, 3.35]]  # the 0.3.3 probes of a 1.2 m radius

    bad, _ = probe_report(*variant(old_box_high))
    assert [b[0] for b in bad["probe_out"]] == ["box_high", "box_high"]

    def old_anchor(ents, doc):
        ents["p1211_disruptor"]["anchor"].update(x=0, y=26)

    bad, _ = probe_report(*variant(old_anchor))
    assert [b[0] for b in bad["anchor"]] == ["p1211_disruptor"]


def test_edit_instruction_lint():
    assert check.lint_edit_instructions(DOC) == []

    def damage(ents, doc):
        ents["rule_learned_soft_zones"]["bounds_text"] = "Replace '-1.6002 <= y < 9.0' with '-1.6002 <= y < 9.0678'"
        ents["ball_backboard_contact"]["bounds_text"] = "Append: 'The z band assumes the recommended board.'"
        ents["rule_spot_occupancy_dwell"]["bounds_text"] += " [also: rule_occlusion_handling '0.5 s (16 frames)']"
        ents["nail"]["notes"] = "Add a sentence about the nail."

    found = {f[0] for f in check.lint_edit_instructions(variant(damage)[0])}
    assert found == {"rule_learned_soft_zones", "ball_backboard_contact", "rule_spot_occupancy_dwell", "nail"}
    # the restored texts are the definitions again
    assert E["rule_learned_soft_zones"]["bounds_text"].startswith("Build offline, version-pin")
    assert "NMF with K = 10" in E["rule_learned_soft_zones"]["bounds_text"]
    assert E["rule_continuous_coordinates"]["bounds_text"].startswith("Every object, every frame")
    assert E["ball_backboard_contact"]["bounds_text"].startswith("Ball centre within one ball radius")


def test_frame_counts_follow_frame_timing():
    assert (frames_for(0.5), frames_for(0.6), frames_for(1.0), frames_for(0.133), frames_for(0.233)) == (16, 19, 31, 5, 8)
    assert (frames_for(3.0, "more_than"), frames_for(10.0), frames_for(0.5, "at_most"), frames_for(1.0, "more_than")) == (91, 301, 15, 31)
    assert check.lint_frame_counts(DOC) == []

    def wrong(ents, doc):
        ents["trap_roles"]["bounds_text"] = ents["trap_roles"]["bounds_text"].replace("(19 frames)", "(18 frames)")

    assert [f[0] for f in check.lint_frame_counts(variant(wrong)[0])] == ["trap_roles"]


def test_rank_is_materialised_on_every_entry():
    assert check.lint_ranks(DOC) == []
    for e in DOC["entries"]:
        assert e["rank"] == check.FAMILY_RANK[e["family"]] * 1000 + e["priority"], e["id"]


def test_header_lists_and_context_names():
    assert check.lint_blocks(DOC, SPOTS) == []
    ids = set(E)
    assert all(i in ids for i in DOC["loader"]["temporal"]["probability_only"])
    for band in ("free_throw_line_extended", "lane_line_extended", "line_28ft_extended", "on_the_line"):
        assert band in DOC["loader"]["temporal"]["probability_only"]

    def undefined(ents, doc):
        del doc["context_names"]["sx"]

    assert any(b[0] == "context_names" for b in check.lint_blocks(*variant(undefined)))


def test_thin_regions_are_on_the_probability_only_list():
    """probability_only_rule: a region thinner than its buffer h is stored as a probability, never a yes/no."""
    assert check.lint_probability_only(DOC, SPOTS) == []
    bands = {"free_throw_line_extended", "lane_line_extended", "line_28ft_extended", "on_the_line"}
    assert set(check.thin_regions(DOC, SPOTS, only=bands | {"paint"})) == bands

    def unlisted(ents, doc):
        doc["loader"]["temporal"]["probability_only"].remove("on_the_line")

    assert [f[0] for f in check.lint_probability_only(*variant(unlisted), only=bands)] == ["on_the_line"]


def test_court_region_is_an_exact_partition():
    part = partition_checks(DOC, SPOTS, 0.25)
    full = part["zone_scheme:court_region"]
    assert full["covered"] == full["points"] and full["overlaps"] == 0
    inb = check.in_bounds_points(0.25)  # crosswalks cover exactly the in-bounds floor
    assert 0 < inb < full["points"]
    for name in ("zone_scheme:nba_basic", "zone_scheme:ctg", "zone_scheme:pbpstats", "zone_scheme:nba_range", "zone_scheme:br_distance",
                 "zone_scheme:nba_area", "zone_scheme:court_thirds"):
        assert part[name]["covered"] == inb, name
    for name, v in part.items():
        assert v["overlaps"] == 0, name


def test_edge_rules():
    def lab(x, y):
        out = labels("zone_scheme:court_region", x, y)
        assert len(out) == 1, (x, y, out)
        return out[0]

    assert lab(6.6008, 0.0) == "long_mid_baseline_right"  # on the corner line is a two
    assert lab(6.61, 0.0) == "corner_three_right"
    assert lab(0.0, 1.27) == "restricted_area"  # arc line is inside the RA
    assert lab(0.0, 12.700) != "backcourt"  # division line's near edge is frontcourt
    assert lab(0.0, 12.71) == "backcourt"
    assert lab(7.62, 5.0) == "out_of_bounds"  # boundary lines are out
    assert lab(-5.3, 5.3) == "wing_three_left"
    assert court_region(SPOTS, float("nan"), 1.0) == ["unknown"]
    assert sum(len(s.labels(float("nan"), 1.0)) for s in SPOTS.values()) == 0


def test_points_exactly_on_a_line_have_one_owner():
    """Edge rule 6 (ties go to the zone nearer the rim) and rule 7 (lines that are in on purpose)."""
    assert check.lint_ties(DOC, SPOTS) == []
    assert check.lint_text_vs_expr(DOC) == []
    assert check.lint_ball_gates(DOC, SPOTS) == []
    # |x| = 2.54: both thirds schemes give the middle
    assert labels("zone_scheme:court_thirds", 2.54, 10) == ["middle_third"]
    assert labels("zone_scheme:court_thirds", -2.54, 10) == ["middle_third"]
    assert labels("zone_scheme:transition_lanes_3", 2.54, 10) == ["lane3_middle"]
    assert labels("zone_scheme:court_thirds", 2.55, 10) == ["outer_third_right"]
    # y = 3.0: the low post is nearer the rim; the zone slot switched on by a high-post ball agrees
    assert labels("zone_scheme:ball_zone", 0.0, 3.0) == ["ball_zone_low_post"]
    assert labels("zone_scheme:ball_zone", 0.0, 3.01) == ["ball_zone_high_post"]
    assert SPOTS["z23_hp_low_middle"].inside(0.0, 0.9, bx=0.0, by=3.0) is False
    assert SPOTS["z23_hp_low_middle"].inside(0.0, 0.9, bx=0.0, by=3.01) is True
    # five lanes
    assert labels("zone_scheme:transition_lanes_5", 1.8288, 14) == ["lane5_middle"]
    assert labels("zone_scheme:transition_lanes_5", 5.3, 14) == ["lane5_laneline_right"]
    # the stated exception: |x| = 0.9 is already a side
    assert labels("zone_scheme:ball_zone", 0.9, 7.6) == ["ball_zone_wing_right"]
    # trap zones and the post area include their lines on purpose (oob_ok); other in-court zones do not
    assert SPOTS["baseline_corner_trap"].labels(7.62, 0.5) == ["baseline_corner_trap_right"]
    assert SPOTS["baseline_corner_trap"].labels(7.63, 0.5) == []
    assert SPOTS["backcourt_corner_trap"].labels(-6.2, 27.051) == ["backcourt_corner_trap_left"]
    assert SPOTS["post_area"].inside(0.0, -1.62) is True and SPOTS["three_second_lane"].inside(0.0, -1.62) is True
    assert SPOTS["post_area"].inside(0.0, -1.66) is False
    assert labels("zone_scheme:court_thirds", 7.62, 5.0) == []

    def tie_away(ents, doc):
        ents["middle_third"]["expr"] = "ax < 2.54 and END_Y < y < FAR_END_Y"
        ents["outer_third"]["expr"] = "2.54 <= x < SIDE_X and END_Y < y < FAR_END_Y"

    doc, spots = variant(tie_away)
    assert [t[:3] for t in check.lint_ties(doc, spots)] == [("zone_scheme:court_thirds", "ax", 2.54)]
    assert {t[0] for t in check.lint_text_vs_expr(doc)} == {"middle_third", "outer_third"}

    # the words lint reads every inequality of a sentence, also the second one after a word ('... and |x| <= SIDE_X')
    def words(expr, text):
        return [(v, c, o, want) for _, v, c, o, want, _, _ in check.text_expr_mismatches({"expr": expr, "bounds_text": text})]

    assert words("ax < SIDE_X and y <= END_Y", "y <= END_Y and |x| <= SIDE_X") == [("x", 7.62, "<=", "<")]
    assert words("ax < SIDE_X and y <= END_Y", "y <= END_Y and |x| < SIDE_X") == []
    assert words("x >= SIDE_X and y <= END_Y", "x >= SIDE_X and y < END_Y") == [("y", -1.6, "<", "<=")]
    assert words("x >= SIDE_X and 3.7338 <= y <= 4.6482", "go to the 28-ft mark. x > SIDE_X and 3.7338 <= y <= 4.6482") == [("x", 7.62, ">", ">=")]
    assert words("r >= 7.3152 and y <= HALF_Y", "r >= 7.3152 and y < 12.700. Not all threes.") == [("y", 12.7, "<", "<=")]
    # a chained inequality is read once, not a second time from its middle
    assert sorted(t[:3] for t in check.text_comparisons("5.0 < |x| <= SIDE_X and END_Y <= y <= BREAK_Y")) == sorted(
        [("x", 5.0, ">"), ("x", 7.62, "<="), ("y", -1.6, ">="), ("y", 1.412, "<=")])

    def second_inequality_wrong(ents, doc):  # the 0.3.4 repair: the first inequality agrees, the second does not
        ents["oob_behind_attacked_endline"]["bounds_text"] = "y <= END_Y and |x| <= SIDE_X"
        ents["oob_far_corner"]["bounds_text"] = "x >= SIDE_X and y > FAR_END_Y"

    assert {t[0] for t in check.lint_text_vs_expr(variant(second_inequality_wrong)[0])} == {"oob_behind_attacked_endline", "oob_far_corner"}

    def gate_left_behind(ents, doc):  # the ball zone moved its line but a zone slot's ball test did not
        ents["z23_hp_low_middle"]["expr"] = ents["z23_hp_low_middle"]["expr"].replace("3.0 < by", "3.0 <= by")

    assert [g[0] for g in check.lint_ball_gates(*variant(gate_left_behind))] == ["z23_hp_low_middle"]


def test_missing_context_is_none_not_false():
    rel = next(s for s in SPOTS.values() if s.ctx and s.code)
    assert rel.inside(1.0, 5.0) is None


def test_per_player_relative_layer():
    """Decision 12: distance and bearing to the rim, the ball and the matchup; null without the context."""
    e = E["rule_continuous_coordinates"]
    assert check.value_probes(e)[0] == [] and check.value_probes(e)[1] >= 40
    v = Values(e["value_exprs"])
    for name in ("rim_dist", "rim_bearing", "ball_dist", "ball_bearing", "matchup_dist", "matchup_bearing"):
        assert name in v.items
    got = v.at(3.0, 4.0, bx=3.0, by=8.0, mx=0.0, my=4.0)
    assert got["rim_dist"] == pytest.approx(5.0) and got["ball_dist"] == pytest.approx(4.0) and got["matchup_dist"] == pytest.approx(3.0)
    assert got["ball_bearing"] == pytest.approx(90.0) and got["matchup_bearing"] == pytest.approx(180.0)
    assert got["rim_bearing"] == pytest.approx(-126.8699, abs=1e-3)
    none = v.at(3.0, 4.0)
    assert none["rim_dist"] == pytest.approx(5.0)
    assert all(none[k] is None for k in ("ball_dist", "ball_bearing", "matchup_dist", "matchup_bearing", "ball_angle_delta"))
    assert v.at(3.0, 4.0, bx=float("nan"), by=8.0)["ball_dist"] is None
    assert all(x is None for x in v.at(float("nan"), 4.0, bx=1.0, by=1.0).values())
    # the base frame is unchanged: the older values are still there
    assert v.at(0.0, 7.6)["d3"] == pytest.approx(0.8499, abs=5e-4)

    def drop_probe(ents, doc):
        ents["rule_continuous_coordinates"]["probes_values"] = ents["rule_continuous_coordinates"]["probes_values"][:1]

    bad, _ = probe_report(*variant(drop_probe))
    assert "value_without_probe" in bad


def test_player_backcourt_status_is_defined():
    t = E["rule_frontcourt_backcourt_player"]["bounds_text"]
    assert "in the backcourt if any grounded foot point is in the backcourt" in t
    assert "rule_frontcourt_backcourt_player" in E["rule_transition_window"]["bounds_text"]
    s = SPOTS["rule_frontcourt_backcourt_player"]
    assert s.inside(0.0, 12.60) is True and s.inside(0.0, 12.80) is False  # the two feet of the straddling player


def test_property_tests_pass_and_can_fail():
    bad, counts, _ = proptest.run(scale=0.02, log=lambda *a: None)
    assert dict(bad) == {}
    assert counts["gating"]["cases"] > 400 and counts["rays"]["points"] > 1000

    def overlap(ents, doc):
        ents["middle_third"]["expr"] = "ax <= 2.6 and END_Y < y < FAR_END_Y"

    bad, _, _ = proptest.run(scale=0.005, log=lambda *a: None, loaded=variant(overlap))
    assert "overlap:zone_scheme:court_thirds" in bad

    def wrong_break(ents, doc):
        ents["nba_corner_3"]["expr"] = "is_three(x, y) and x > 0 and y <= 2.0"

    bad, _, _ = proptest.run(scale=0.02, log=lambda *a: None, loaded=variant(wrong_break))
    assert "corner:nba_corner_3" in bad

    def lopsided(ents, doc):
        ents["middle_third"]["expr"] = "-2.0 < x <= 2.54 and END_Y < y < FAR_END_Y"

    bad, _, _ = proptest.run(scale=0.005, log=lambda *a: None, loaded=variant(lopsided))
    assert "centre_sym:middle_third" in bad


def test_stored_results_were_made_from_these_rules():
    """results/named_spots_test: the summaries the page prints come from the rules now in the YAML."""
    sha = rules_sha(DOC)
    c = json.loads((RESULTS / "check_summary.json").read_text())
    assert c["rules_sha256"] == sha and c["entry_failures"] == {} and c["step_m"] == 0.05
    full = c["partitions"]["zone_scheme:court_region"]
    assert full["points"] == 231401 and full["covered"] == 231401
    assert all(v["overlaps"] == 0 for v in c["partitions"].values())
    assert c["probes"]["entries_with_zero_probes"] == 0
    p = json.loads((RESULTS / "proptest_summary.json").read_text())
    assert p["rules_sha256"] == sha and p["failed_properties"] == {} and p["scale"] == 1.0
    # real data: the page's sentence on the two-vs-three disagreements is built from the stored aggregate
    b = json.loads((RESULTS / "cbbd_summary.json").read_text())
    agree, total = (int(v) for v in b["two_vs_three_agreement"].split("/"))
    d = b["two_vs_three_disagreements"]
    assert d["n"] == total - agree and 0 <= d["within_0p05_m"] <= d["n"]
    assert (d["max_from_line_m"] is None) == (d["n"] == 0)
    page = (ROOT / "docs" / "data" / "named_spots.md").read_text()
    if d["n"]:
        assert d["max_from_line_m"] > 0.05 or d["within_0p05_m"] == d["n"]
        assert f"{b['two_vs_three_agreement']} ({d['n']} disagreement" in page
        assert f"{d['within_0p05_m']} within 0.05 m of the three-point line, the farthest {d['max_from_line_m']:.2f} m from it" in page
    assert "disagreements are within" not in page


def test_doc_shows_every_entry_in_full():
    """docs/data/named_spots.md: no entry missing, no text shortened, tables well formed (doc_no_truncation)."""
    from gen_doc import build, check as page_check  # noqa: E402

    md, entries = build()
    assert page_check(md, entries, entries) == []


def test_page_on_disk_is_the_generated_page():
    """gen_doc.py --check: the committed page equals a fresh one (a YAML or template edit needs a regenerate)."""
    from gen_doc import OUT, build  # noqa: E402

    md, _ = build()
    assert OUT.read_text() == md, "run python tools/specgen/named_spots/gen_doc.py"
    assert f"Version {DOC['version']}." in md


def test_court_picture_matches_court_region():
    """docs/data/named_spots_court.svg: random points in every shaded cell get that cell's label."""
    from gen_svg import region_polygons, verify  # noqa: E402

    consts = {k: v for k, v in DOC["constants"].items() if isinstance(v, (int, float))}
    assert verify(region_polygons(consts), SPOTS, n=60) == []


def test_picture_on_disk_is_the_generated_picture():
    """gen_svg.py --check: the committed picture equals a fresh one."""
    import gen_svg  # noqa: E402

    assert gen_svg.OUT.read_text() == gen_svg.build(DOC, SPOTS), "run python tools/specgen/named_spots/gen_svg.py"


def test_check_modes_of_the_generators_fail_on_a_stale_file(tmp_path):
    import subprocess

    for tool in ("gen_doc.py", "gen_svg.py"):
        stale = tmp_path / tool
        stale.write_text("stale\n")
        r = subprocess.run([sys.executable, str(ROOT / "tools" / "specgen" / "named_spots" / tool), "--check", "--out", str(stale)],
                           capture_output=True, text=True)
        assert r.returncode != 0 and "out of date" in (r.stdout + r.stderr), tool
