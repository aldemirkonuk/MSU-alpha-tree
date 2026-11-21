"""The generated pages of the views catalogue (ACC-VW-4) and the proposed schema changes of the pack."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "views"))

import gen_doc  # noqa: E402
import vwlib  # noqa: E402

DOC = gen_doc.Doc()
PAGE = (gen_doc.OUT_DIR / gen_doc.PAGE).read_text()
REFERENCE = (gen_doc.OUT_DIR / gen_doc.REFERENCE).read_text()
CHANGES = vwlib.load_yaml_strict(vwlib.CHANGES)
STATUS = "not applied: proposal for the requirements session"


def test_gen_doc_check_passes():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "specgen" / "views" / "gen_doc.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_the_pages_carry_everything_and_no_placeholder():
    assert DOC.checks(PAGE, REFERENCE) == []
    for key, e in DOC.index.items():
        assert f"### {e['id']} {e['name']}" in PAGE and f"### {e['id']} {e['name']}" in REFERENCE
        assert DOC.views[key]["question"] in PAGE


def test_the_first_page_stays_under_the_render_limit():
    assert len(PAGE.encode()) <= gen_doc.MAX_PAGE_BYTES < 500 * 1024


def test_the_checks_catch_a_page_that_lost_something():
    broken = PAGE.replace("### VW-CARD-01 Player card", "### Player card")
    assert any("VW-CARD-01 has no entry" in e for e in DOC.checks(broken, REFERENCE))
    assert any("element spot_shooting_map missing" in e for e in DOC.checks(PAGE.replace("| `spot_shooting_map` |", "| `map` |"), REFERENCE))
    assert any("acceptance ACC-VW-H1 missing" in e for e in DOC.checks(PAGE.replace("| ACC-VW-H1 |", "| ACC |"), REFERENCE))
    assert "placeholder left" in DOC.checks(PAGE + "\n{{MISSING}}\n", REFERENCE)
    assert any("more than" in e for e in DOC.checks(PAGE + "x" * gen_doc.MAX_PAGE_BYTES, REFERENCE))
    assert any("has no heading" in e for e in DOC.checks(PAGE + "\n[x](#no-such-heading)\n", REFERENCE))


def test_a_bare_angle_bracket_is_written_as_an_entity():
    assert gen_doc.html_safe('age "<n> s ago"<br>next <details><summary><b>x</b></summary></details> <img src="a">') == \
        'age "&lt;n> s ago"<br>next <details><summary><b>x</b></summary></details> <img src="a">'
    assert "<n>" not in PAGE and "<n>" not in REFERENCE


def test_the_contract_is_on_one_screen_with_its_legend():
    start, end = PAGE.index("## 1. The display contract"), PAGE.index("### Rule 2.")
    one_screen = PAGE[start:end]
    assert "views/grade_legend.svg" in one_screen
    for line in DOC.dc["summary"]:
        assert line in one_screen
    for grade in DOC.dc["grades"]["appearance"]:
        assert f"| {grade} |" in one_screen


def test_coverage_table_has_every_required_and_reported_row():
    inv = DOC.core["inventory"]
    cov = vwlib.requirement_coverage(DOC.views)
    section = PAGE[PAGE.index("## 9. Coverage"):PAGE.index("## 10.")]
    for rid in list(inv["required_rows"]) + list(inv["reported_rows"]):
        row = next(line for line in section.splitlines() if line.startswith(f"| {rid} |"))
        if rid in inv["no_view_rows"]:
            assert "no view:" in row
        else:
            for key in cov[rid]:
                assert DOC.index[key]["id"] in row


def test_open_questions_are_numbered_without_a_gap_and_the_first_ones_lead():
    qs = DOC.core["open_questions"]
    assert [q["id"] for q in qs] == [f"OQ-VW-{i}" for i in range(1, len(qs) + 1)]
    start = PAGE.index("**Answer these first**")
    lead = PAGE[start:PAGE.index("\n**", start + 10)]
    for q in qs:
        assert (f"| {q['id']} |" in lead) == bool(q.get("first"))


def test_phases_list_every_view_once():
    section = PAGE[PAGE.index("## 10. What each project phase"):PAGE.index("## 11.")]
    for key, e in DOC.index.items():
        assert section.count(f"{e['id']}](") == 1


# --------------------------------------------------------------------------------------------------------------------
# schema/views_changes.yaml
def _columns():
    for table, cols in CHANGES["column_additions"].items():
        for c in cols:
            yield table, c


def test_schema_changes_counts_and_status():
    counts = CHANGES["counts"]
    assert counts["column_additions"] == sum(len(v) for v in CHANGES["column_additions"].values())
    assert counts["tables_touched"] == len(CHANGES["column_additions"])
    assert counts["new_tables"] == len(CHANGES["new_tables"])
    assert counts["new_table_columns"] == sum(len(t["columns"]) for t in CHANGES["new_tables"].values())
    assert counts["removals"] == len(CHANGES["removals"])
    assert "not applied" in CHANGES["status"]
    for _, c in _columns():
        assert c["status"] == STATUS and c["why"] and c["definition"] and c["type"]
    for spec in list(CHANGES["new_tables"].values()) + CHANGES["removals"]:
        assert spec["status"] == STATUS and spec["why"]


def test_schema_changes_propose_nothing_that_exists():
    schema = vwlib.Refs().schema()
    for table, c in _columns():
        assert table in schema, f"{table}: a column addition needs an existing table"
        assert c["column"] not in schema[table], f"{table}.{c['column']} already exists"
    for table in CHANGES["new_tables"]:
        assert table not in schema, f"{table} already exists"
    for r in CHANGES["removals"]:
        assert r["column"] in schema[r["table"]], "a removal names an existing column"


def test_schema_changes_cite_requirements_and_real_elements():
    targets = {f"{k}.{e['key']}" for k, rec in DOC.views.items() for e in rec["elements"]}
    entries = [c for _, c in _columns()] + list(CHANGES["new_tables"].values())
    for e in entries:
        assert e["requirement"] and all(vwlib.REQ_RE.match(r) for r in e["requirement"])
        assert e["read_by"] and set(e["read_by"]) <= targets, sorted(set(e["read_by"]) - targets)
    for r in CHANGES["removals"]:
        assert all(vwlib.REQ_RE.match(x) for x in r["requirement"])


def test_every_proposed_table_a_view_depends_on_is_proposed_somewhere():
    refs = vwlib.Refs()
    for key, rec in DOC.views.items():
        for t in rec["depends_on"]["tables"]:
            assert refs.table_known(t), f"{key}: {t}"
    assert "clip_index" in refs.proposed_by_file()["views_changes.yaml"]


# --------------------------------------------------------------------------------------------------------------------
# hygiene of what this baseline added to the public repo
ADDED = [ROOT / "config" / "views", ROOT / "tools" / "specgen" / "views", ROOT / "docs" / "data" / "views", ROOT / "tests" / "views"]
ADDED_FILES = [ROOT / "schema" / "views_changes.yaml", gen_doc.OUT_DIR / gen_doc.PAGE, gen_doc.OUT_DIR / gen_doc.REFERENCE]


def _added():
    for d in ADDED:
        for p in sorted(d.rglob("*")):
            if p.is_file() and p.suffix in (".yaml", ".py", ".md", ".svg"):
                yield p
    yield from ADDED_FILES


@pytest.mark.parametrize("needle", ["/Users/", "-private/", "data:image", "<image", ".png", ".jpg", ".mp4"])
def test_no_private_path_and_no_picture_in_the_baseline(needle):
    for p in _added():
        if p.parent == Path(__file__).parent:      # the tests name these strings in order to refuse them
            continue
        assert needle not in p.read_text(), f"{p.relative_to(ROOT)} holds {needle!r}"


def test_no_feet_in_the_pack_or_on_the_pages():
    banned = DOC.dc["visual_standard"]["banned_units"]
    for name, text in ((gen_doc.PAGE, PAGE), (gen_doc.REFERENCE, REFERENCE)):
        body = text.replace(", ".join(banned), "")          # the page prints the list of banned units once
        assert vwlib.unit_problems(body.splitlines(), banned) == [], name
    assert vwlib.unit_problems(CHANGES, banned) == []
