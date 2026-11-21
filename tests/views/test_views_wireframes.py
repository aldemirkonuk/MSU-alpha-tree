"""The wireframes of docs/data/views: each one a record names exists, parses, is current, labels only element keys of its
view, uses only colour tokens of the contract, and holds no text wider than its box (ACC-VW-S2)."""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "views"))

import gen_wireframes as gw  # noqa: E402
import vwlib  # noqa: E402

SVG = "{http://www.w3.org/2000/svg}"
CORE = vwlib.load_core()
VIEWS = vwlib.load_views()
NAMED = gw.named_by_records(VIEWS)                       # {file name: (view key, level or None)}
ALL = sorted(set(NAMED) | set(gw.LEGENDS))
VS = CORE["display_contract"]["visual_standard"]


def _root(name):
    return ET.parse(gw.OUT_DIR / name).getroot()


def _texts(name):
    return [t for t in _root(name).iter(f"{SVG}text")]


def _allowed_colours():
    out = set(vwlib.tokens(CORE, "dark").values())
    out |= {c["hex"] for c in VS["categorical"]["set"]} | set(VS["sequential"]["stops"]) | set(VS["diverging"]["stops"])
    return {c.upper() for c in out}


def test_the_required_wireframes_are_named_by_records():
    # the live panel at D0, D1 and D3, the possession explorer, the Studio canvas, the layered tree, the review item, the player card
    want = {"live_game_state_panel": {None, "D1_bug_away", "D3_replay"}, "possession_explorer": {None}, "studio_game_canvas": {None},
            "win_probability_chart": {None}, "review_item": {None}, "player_card": {None}}
    got = {}
    for view, level in NAMED.values():
        got.setdefault(view, set()).add(level)
    for view, levels in want.items():
        assert levels <= got.get(view, set()), view


@pytest.mark.parametrize("name", ALL)
def test_every_named_wireframe_exists_and_parses(name):
    root = _root(name)
    assert root.tag == f"{SVG}svg"
    assert root.find(f"{SVG}title").text and root.find(f"{SVG}desc").text
    assert int(root.get("width")) == int(root.get("data-width"))


def test_the_files_on_disk_are_what_the_generator_draws():
    files = gw.build()
    assert sorted(files) == ALL
    for name, text in files.items():
        assert (gw.OUT_DIR / name).read_text() == text, f"{name} is out of date: run python tools/specgen/views/gen_wireframes.py"
    assert sorted(p.name for p in gw.OUT_DIR.glob("*.svg")) == ALL, "a drawing in docs/data/views is not generated"


@pytest.mark.parametrize("name", sorted(NAMED))
def test_a_wireframe_labels_only_element_keys_of_its_view(name):
    view, _ = NAMED[name]
    root = _root(name)
    assert root.get("data-view") == view
    keys = [t.text for t in root.iter(f"{SVG}text") if t.get("class") == "key"]
    element_keys = [e["key"] for e in VIEWS[view]["elements"]]
    assert keys and set(keys) <= set(element_keys)
    assert len(keys) == len(set(keys)), "an element is labelled twice"
    assert len(keys) >= 0.75 * len(element_keys), "a wireframe draws at least three quarters of the elements of its view"
    assert int(root.get("width")) == VIEWS[view]["min_width_px"], "a wireframe is drawn at the stated width of its view"


@pytest.mark.parametrize("name", ALL)
def test_only_colour_tokens_of_the_contract(name):
    text = (gw.OUT_DIR / name).read_text()
    used = {c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}\b", text)}
    assert used and used <= _allowed_colours(), sorted(used - _allowed_colours())
    assert not re.search(r'(?:fill|stroke)="(?!none|url\(#hatch\)|#)[^"]+"', text), "a colour that is not a hex token"


@pytest.mark.parametrize("name", ALL)
def test_no_text_is_wider_than_its_box_or_smaller_than_the_caption(name):
    root = _root(name)
    width = int(root.get("width"))
    caption = VS["text_sizes"]["caption_px"]["value"]
    texts = _texts(name)
    assert texts
    for t in texts:
        size = float(t.get("font-size"))
        mono, bold = "Menlo" in t.get("font-family"), t.get("font-weight") == "bold"
        est = gw.text_width(t.text, size, mono, bold)
        assert size >= caption, t.text
        assert est <= float(t.get("data-maxw")) + 0.05, f"{t.text!r} needs {est:.0f} px, its box has {t.get('data-maxw')}"
        x = float(t.get("x"))
        x0 = x if t.get("text-anchor") is None else x - est if t.get("text-anchor") == "end" else x - est / 2
        assert x0 >= -0.05 and x0 + est <= width + 0.05, f"{t.text!r} leaves the page"
        assert 0 < float(t.get("y")) <= int(root.get("height"))


@pytest.mark.parametrize("name", ALL)
def test_no_banned_unit_and_no_real_name(name):
    strings = [t.text for t in _texts(name)]
    assert vwlib.unit_problems(strings, VS["banned_units"]) == []
    joined = " ".join(strings)
    for word in ("Michigan", "MSU", "Spartan", "Big Ten", "ESPN"):
        assert word not in joined
    assert "<image" not in (gw.OUT_DIR / name).read_text(), "no picture is embedded in a wireframe (no broadcast frame)"


def test_the_text_fit_check_stops_a_wide_text():
    p = gw.Pack()
    c = gw.Canvas(p, "player_card", 375, 100)
    c.text(10, 20, "fits", 100)
    with pytest.raises(gw.Overflow):
        c.text(10, 20, "this sentence is far too long for a box of sixty pixels", 60)
    with pytest.raises(gw.Overflow):
        c.text(360, 20, "leaves the page", 200)
    with pytest.raises(gw.Overflow):
        c.text(10, 20, "tiny", 100, size=9)
    with pytest.raises(KeyError):
        c.frame("no_such_element", 0, 0, 100, 40)


def test_the_live_panel_shows_each_level_as_its_record_says():
    def strings(name):
        return [t.text for t in _texts(name)]
    d0, d1, d3 = strings("live_panel_d0.svg"), strings("live_panel_d1.svg"), strings("live_panel_d3.svg")
    assert not any(s.endswith("s ago") for s in d0) and "prov" not in d0
    assert "12 s ago" in d1 and "between 7:30 and 7:42" in d1 and "prov" in d1        # carried with its age and interval; the strip shows prov
    assert any("bug away" in s for s in d1) and any(s.startswith("REPLAY") for s in d3)
    assert any("court hidden" in s for s in d3) and not any("court hidden" in s for s in d1)
    for s in (d0, d1, d3):                                                              # no made-up live win probability (OQ-VW-13)
        assert "no model before P6" in s and not any(re.fullmatch(r"\d+ %", x) for x in s)


def test_no_tile_moves_or_resizes_between_levels():
    def boxes(name):
        return {t.text: (t.get("x"), t.get("y")) for t in _texts(name) if t.get("class") == "key"}
    d0, d1, d3 = boxes("live_panel_d0.svg"), boxes("live_panel_d1.svg"), boxes("live_panel_d3.svg")
    assert d0 == d1 == d3


def test_grade_marks_follow_the_contract():
    app = CORE["display_contract"]["grades"]["appearance"]
    text = (gw.OUT_DIR / "grade_legend.svg").read_text()
    strings = [t.text for t in _texts("grade_legend.svg")]
    for grade, a in app.items():
        assert grade in strings
    assert text.count('stroke-dasharray="6 4"') >= 2 and 'stroke-dasharray="2 3"' in text and "url(#hatch)" in text   # dashed, dotted, hatched edges
    assert "prov" in strings and "est" in strings and "under review" in strings


def test_the_court_follows_the_orientation_of_the_contract():
    p = gw.Pack()
    c = gw.Canvas(p, "player_card", 375, 100)
    ct = gw.Court(c, 0, 0, 300)
    assert VS["court_drawing"]["orientation"] == "overhead" and p.overhead
    assert ct.px(0, 0)[1] < ct.px(0, 5)[1] and ct.px(1, 0)[0] > ct.px(0, 0)[0]      # rim at the top, +x to the right
    p.overhead = False
    assert ct.px(0, 0)[1] > ct.px(0, 5)[1]
    k = p.K
    assert abs((ct.px(k["SIDE_X"], 0)[0] - ct.px(-k["SIDE_X"], 0)[0]) / ct.s - 2 * k["SIDE_X"]) < 1e-9      # drawn from the named-spots constants
