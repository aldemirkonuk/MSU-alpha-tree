"""The generated page (docs/data/live_game_state.md), the proposed schema changes (schema/live_state_changes.yaml)
and the loose ends of the pack: open questions, follow-ups, journal counts, hygiene of everything the baseline added."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "live_state"))

import gen_doc  # noqa: E402
import lslib  # noqa: E402
import measure_real as mr  # noqa: E402

CORE = lslib.load_core()
FIELDS = lslib.load_fields()
PAGE = ROOT / "docs" / "data" / "live_game_state.md"
NOT_APPLIED = "not applied: proposal for the requirements session"
BASELINE_FILES = [p for pat in ("config/live_state/*.yaml", "tools/specgen/live_state/*.py", "tools/specgen/live_state/*.md", "tests/live_state/*.py",
                                "results/live_state_test/*", "docs/data/live_game_state.md", "schema/live_state_changes.yaml") for p in sorted(ROOT.glob(pat))]


# ------------------------------------------------------------------------------------------------------------ the page
def test_generated_doc_is_current():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "specgen" / "live_state" / "gen_doc.py"), "--check"], capture_output=True, text=True, cwd="/")
    assert r.returncode == 0, r.stdout + r.stderr


def test_page_keeps_the_ten_groups_of_19_oct_and_holds_every_field_once():
    text = PAGE.read_text()
    heads = re.findall(r"^### (\d+)\. (.+)$", text, re.M)
    assert [int(n) for n, _ in heads] == list(range(1, 11))
    assert [h.split(" (")[0] for _, h in heads] == ["Keys and provenance", "Time", "Score", "Possession and the ball", "Counts the rules run on", "Personnel",
                                                   "Situation", "Tactics", "Observability", "Fixed for the game"]
    rows = re.findall(r"^\| \*\*(LS-[A-Z]+-\d\d)\*\* `([a-z0-9_]+)`", text, re.M)
    assert sorted(rows) == sorted((r["id"], k) for k, r in FIELDS.items())
    for line in text.splitlines():                                   # every field row has the eight columns
        if line.startswith("| **LS-"):
            assert len(re.findall(r"(?<!\\)\|", line)) == 9, line[:80]
    order = [text.index(f"\n## {h}") for h in ("What this page is", "One-screen summary", "How to read this page", "Sensors", "Grades", "Rules and profiles",
                                                "Degradation levels", "The fields", "Reconciliation windows", "Real-data replay", "Acceptance",
                                                "What is measured and what is assumed", "Open questions for Aldemir", "Follow-up edits outside this page", "Journal")]
    assert order == sorted(order)
    assert text.index("## One-screen summary") < 3000                 # the summary is the first screen


def test_doc_checks_catch_a_missing_id_a_placeholder_and_a_cut_row():
    text = PAGE.read_text()
    assert gen_doc.checks(text) == []
    assert any("LS-TIME-03" in e for e in gen_doc.checks(text.replace("LS-TIME-03", "LS-TIME-XX")))
    assert any("placeholder" in e for e in gen_doc.checks(text + "\n{{LEFT_OVER}}\n"))
    assert any("DEAD_RECKON" in e for e in gen_doc.checks(text.replace("`DEAD_RECKON`", "`DEAD-RECKON`")))
    assert any("OQ-LS-4 " in e + " " for e in gen_doc.checks(text.replace("| OQ-LS-4 |", "| OQ-LS-x |")))
    assert any("FU-LS-02" in e for e in gen_doc.checks(text.replace("| FU-LS-02 |", "| FU-LS-xx |")))
    assert any("clock_inferred_max_s" in e for e in gen_doc.checks(text.replace("`clock_inferred_max_s`", "`clock_max`")))
    row = next(line for line in text.splitlines() if line.startswith("| **LS-SCORE-01**"))
    assert any("table row" in e for e in gen_doc.checks(text.replace(row, row + " extra |")))
    assert any("feet" in e for e in gen_doc.checks(text + "\nThe line is 22 " + "fe" + "et from the basket.\n"))


def test_text_from_the_yaml_cannot_break_a_table():
    assert gen_doc.x("a | b") == "a \\| b" and gen_doc.x("state_frame.*_dq") == "state_frame.\\*\\_dq"
    assert gen_doc.x("open-<run_id>-<n>") == "open-&lt;run\\_id>-&lt;n>".replace("\\_", "_")   # only a leading underscore is escaped
    assert gen_doc.x("line one\n  line two") == "line one line two"
    assert "clock_inferred_max_s (3 s)" in gen_doc.xv("inferred up to clock_inferred_max_s, then carried")
    assert gen_doc.num(1200.0) == "1,200" and gen_doc.num(1.93) == "1.93" and gen_doc.num(0.017) == "0.017" and gen_doc.num(3.0) == "3"


def test_summary_numbers_are_the_measured_ones():
    m = gen_doc.measured()
    text = PAGE.read_text()
    lag = m["score"]["made_fg_lag_vs_pbp_clock_s"]
    assert f"**{100 * m['clock']['availability_in_period']['pooled']:.0f} %** | of in-period seconds show a readable game clock" in text
    assert f"median {lag['p50']} s, p95 {lag['p95']} s, p99 {lag['p99']} s (n = {lag['n']:,})" in text
    h = gen_doc.harness()
    assert f"**{100 * h['summary'][gen_doc.NO_CUE]['clock_by_grade']['inferred']['within_tolerance']:.1f} %**" in text
    assert "The replay used the limits on this page." in text and "stale" not in text.split("## Real-data replay")[1].split("## Acceptance")[0]


# ---------------------------------------------------------------------------------------------- the schema change set
def _pack_ids():
    """Every requirement id the pack cites: the lists of the records and the list of core.yaml (ranges written out)."""
    ids = {r for rec in FIELDS.values() for r in rec["requirements"]}
    for item in CORE["requirement"]["requirements"]:
        m = re.fullmatch(r"(R-[A-Z]{2}-)(\d{2})\.\.(\d{2})", item)
        ids |= {f"{m.group(1)}{n:02d}" for n in range(int(m.group(2)), int(m.group(3)) + 1)} if m else {item}
    return ids


PACK_IDS = _pack_ids()


def test_change_set_holds_every_proposed_column_with_type_unit_why_and_requirement():
    doc = lslib.load_yaml_strict(lslib.CHANGES)
    assert doc["status"].startswith("proposed") and "not applied" in doc["status"]
    listed = {f"{t}.{c['column']}" for t, cols in doc["column_additions"].items() for c in cols}
    listed |= {f"{t}.{c['column']}" for t, d in doc["new_tables"].items() for c in d["columns"]}
    named = {t for r in FIELDS.values() for t in (r.get("lands_in_proposed") or [])}
    assert named <= listed, sorted(named - listed)
    extra = {f"{t}.{c['column']}": c for t, cols in doc["column_additions"].items() for c in cols if f"{t}.{c['column']}" not in named}
    assert all(c.get("note") for c in extra.values()), sorted(extra)   # a column no record names says where it comes from
    exists = lslib._schema_columns()
    for t, cols in doc["column_additions"].items():
        assert t in exists, f"{t} is not a table of schema/tables (a new table goes under new_tables)"
        for c in cols:
            assert c["column"] not in exists[t], f"{t}.{c['column']} already exists"
            assert all(c.get(k) for k in ("type", "unit", "field", "requirement", "definition", "why")), c
            assert c["status"] == NOT_APPLIED and c["field"] in FIELDS
            assert all(re.fullmatch(r"R-[A-Z]{2}-\d{2}[a-z]?", r) for r in c["requirement"]), c["requirement"]
            assert set(c["requirement"]) <= PACK_IDS, f"{t}.{c['column']}: {sorted(set(c['requirement']) - PACK_IDS)} is cited nowhere in the pack"
            assert not re.search(r"(^|_)(msu|opp|opponent)(_|$)", c["column"]), f"{t}.{c['column']} is relative to one programme (R-MD-22)"
    for t, d in doc["new_tables"].items():
        assert t not in exists and d["status"] == NOT_APPLIED and d["field"] in FIELDS and set(d["primary_key"]) <= {c["column"] for c in d["columns"]}
    for e in doc["enum_changes"] + doc["definition_changes"]:
        assert e["status"] == NOT_APPLIED and e["field"] in FIELDS and e["why"] and e["requirement"] and set(e["requirement"]) <= PACK_IDS
    ids = [e["id"] for e in doc["enum_changes"]] + [e["id"] for e in doc["definition_changes"]]
    assert ids == [f"EC-{i}" for i in range(1, len(doc["enum_changes"]) + 1)] + [f"DC-{i}" for i in range(1, len(doc["definition_changes"]) + 1)]
    counts = doc["counts"]
    assert counts["column_additions"] == sum(len(c) for c in doc["column_additions"].values()) and counts["tables_touched"] == len(doc["column_additions"])
    assert counts["of_which_named_by_field_records"] + counts["of_which_named_by_field_records_in_new_tables"] == len(named)


def test_change_set_points_at_the_team_neutral_renames_it_does_not_repeat():
    doc = lslib.load_yaml_strict(lslib.CHANGES)
    tn = doc["team_neutral"]
    reads = tn["renames_this_pack_reads"]
    assert tn["fields_that_read_renamed_columns"] == len(reads) > 0 and (ROOT / "schema" / "platform_changes.yaml").exists()
    for field, cols in reads.items():
        assert field in FIELDS and set(cols) <= set(FIELDS[field]["lands_in"]), field
    listed = {f"{t}.{c['column']}" for t, cols in doc["column_additions"].items() for c in cols}
    assert not listed & {c for cols in reads.values() for c in cols}       # a rename is never also an addition


# ---------------------------------------------------------------------------- questions, follow-ups, journal, status
def test_open_questions_and_follow_ups_are_complete_and_every_reference_exists():
    qs, fus = CORE["open_questions"], CORE["follow_ups"]
    assert [q["id"] for q in qs] == [f"OQ-LS-{i}" for i in range(1, len(qs) + 1)]
    assert [f["id"] for f in fus] == [f"FU-LS-{i:02d}" for i in range(1, len(fus) + 1)]
    assert all(q["question"] and q["recommended"] and q["status"] for q in qs)
    assert all(f["where"] and f["what"] and f["why"] and f["status"] for f in fus)
    text = "".join(p.read_text() for p in sorted(lslib.PACK_DIR.glob("*.yaml"))) + lslib.CHANGES.read_text()
    assert set(re.findall(r"OQ-LS-\d+", text)) <= {q["id"] for q in qs}
    assert set(re.findall(r"FU-LS-\d+", text)) <= {f["id"] for f in fus}
    assert set(re.findall(r"\b[ED]C-\d+\b", lslib.CHANGES.read_text().split("team_neutral:")[1])) <= {"EC-8", "DC-1"}
    # the two owner answers of 11 Nov 2026 are recorded: the live measurements are allowed, nothing depends on staff data
    by = {q["id"]: q for q in qs}
    assert "Allowed by Aldemir on 11 Nov 2026" in by["OQ-LS-1"]["status"] and "Allowed by Aldemir on 11 Nov 2026" in by["OQ-LS-2"]["status"]
    assert "Nothing here depends on MSU staff data" in by["OQ-LS-3"]["status"]


def test_status_line_and_journal_counts():
    assert CORE["pack"] == "live_state" and CORE["version"] == "0.1.0"
    assert CORE["status"].startswith("proposal under the build freeze (baseline 4 of 8)")
    assert all(j["entries"] for j in CORE["journal"]) and [j["date"] for j in CORE["journal"]] == sorted(j["date"] for j in CORE["journal"])
    journal = " ".join(e for j in CORE["journal"] for e in j["entries"])
    for name, sentence in gen_doc.journal_quotes().items():
        assert sentence in journal, f"{name}: the journal no longer says what the pack counts ({sentence})"
    assert f"{len(FIELDS)} fields" in journal and f"{len(CORE['follow_ups'])}" in journal


# ------------------------------------------------------------------------------------------------------------ hygiene
def test_baseline_files_hold_no_user_path_no_recording_name_and_no_feet():
    assert len(BASELINE_FILES) >= 18
    for p in BASELINE_FILES:
        text = p.read_text()
        if p.parent.name != "live_state" or p.suffix != ".py" or "tests" not in p.parts:   # the tests name the strings they forbid
            assert "/Users/" not in text and "MichiganState" not in text, p
        assert not re.search(r"\d\s*(feet|foot|ft)\b(?!_)", text), p
    for p in (PAGE, lslib.CHANGES):
        assert "MSU-Alpha-3-private" not in p.read_text(), p


HOME_SPACED = " ".join(["Michi" + "gan", "State"])
HOME = HOME_SPACED.replace(" ", "")


@pytest.mark.skipif(not mr.STATE.exists(), reason="private recordings not on this machine")
def test_no_team_name_or_game_id_of_the_private_recordings_is_in_the_baseline():
    tokens = set()
    for d in mr.STATE.iterdir():
        m = re.fullmatch(r"\d{4}-\d{2}-\d{2}_(.+)_(?:at|vs)_(.+?)_(\d{6,})", d.name)
        if m:
            tokens |= {t for t in m.groups() if t != HOME and len(t) >= 4}
    assert len(tokens) >= 30
    for p in BASELINE_FILES:
        text = p.read_text().replace(HOME_SPACED, "MSU")               # the project's own name is not a recording name
        hits = [1 for t in tokens if re.search(rf"(?<![A-Za-z0-9]){re.escape(t)}(?![A-Za-z0-9])", text)]
        assert not hits, f"{p.name}: {len(hits)} name(s) or id(s) of the private recordings"
