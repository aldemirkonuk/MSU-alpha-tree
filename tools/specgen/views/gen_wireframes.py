"""Draw the wireframes of the views catalogue (docs/data/views/*.svg) from config/views/*.yaml.

Nothing is drawn by hand. View ids and names, element keys and kinds, the palette tokens, the grade marks, the text
sizes, the degradation levels and the limits of the live panel are read from the pack; the court lines are read from
the constants of config/named_spots.yaml. Every element a wireframe draws carries its element key (class "key"), so
the catalogue page can refer to it. The numbers on the screens are made up (they live in this file) and the teams are
Home and Away. No broadcast frame is shown: a video element is a hatched box.

Before a text is written its width is estimated from its characters and compared with the box it sits in. A text
that does not fit stops the run, so a wireframe with overflowing text cannot be written. The same estimate is checked
again by tests/views/test_views_wireframes.py from the files on disk (ACC-VW-S2).

Usage: python tools/specgen/views/gen_wireframes.py [--out-dir docs/data/views] [--theme dark|light] [--check] [--draft]
--check regenerates in memory and exits non-zero if a file on disk differs (used by the tests).
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import vwlib  # noqa: E402

ROOT = vwlib.REPO
OUT_DIR = ROOT / "docs" / "data" / "views"
SANS = "Helvetica, Arial, sans-serif"
MONO = "Menlo, Consolas, monospace"
CHART_KINDS = ("court", "chart", "video", "timeline", "overlay")
EDGE_DASH = {"solid": None, "dashed": "6 4", "dotted": "2 3", "hatched": "6 4"}
FOOT = "Generated wireframe. Made-up numbers."


class Overflow(Exception):
    """A text is wider than its box, or smaller than the caption size."""


def text_width(s, size, mono=False, bold=False):
    """Estimated width in px of s in Helvetica or Arial (monospace: 0.6 em), with a 5 % margin."""
    if mono:
        return len(s) * size * 0.6
    w = 0.0
    for ch in s:
        if ch in " .,:;'|!iIjl·/":
            w += 0.28
        elif ch in "ftr()[]-\"*":
            w += 0.36
        elif ch in "mwMW%@→—":
            w += 0.90
        elif ch.isupper():
            w += 0.70
        else:
            w += 0.56
    return w * size * (1.07 if bold else 1.0) * 1.05


def wrap(s, size, maxw):
    """Break s into lines no wider than maxw."""
    lines, cur = [], ""
    for word in s.split():
        trial = f"{cur} {word}".strip()
        if cur and text_width(trial, size) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + ([cur] if cur else [])


def n(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


class Pack:
    """What the wireframes read from the pack."""

    def __init__(self, theme="dark"):
        self.core = vwlib.load_core()
        self.views = vwlib.load_views()
        dc = self.core["display_contract"]
        vs = dc["visual_standard"]
        self.theme = theme
        self.tokens = vwlib.tokens(self.core, theme)
        self.app = dc["grades"]["appearance"]
        self.badges = dc["grades"]["badge_texts"]
        self.sizes = {k: v["value"] for k, v in vs["text_sizes"].items()}
        self.cat = {c["name"]: c["hex"] for c in vs["categorical"]["set"]}
        self.seq = list(vs["sequential"]["stops"])
        self.div = list(vs["diverging"]["stops"])
        self.overhead = vs["court_drawing"]["orientation"] == "overhead"
        spots = vwlib._yaml(vwlib.NAMED_SPOTS)
        self.K = {k: v for k, v in spots["constants"].items() if isinstance(v, (int, float))}
        self.anchor = {e["id"]: e["anchor"] for e in spots["entries"] if e.get("anchor") and e["layer"] in ("spot", "landmark")}
        self.spots_version = spots["version"]
        self.ls = vwlib.Refs().ls_index()

    def rec(self, key):
        return self.views[key]

    def el(self, view, key):
        for e in self.views[view]["elements"]:
            if e["key"] == key:
                return e
        raise KeyError(f"view {view} has no element {key!r}")

    def param(self, view, name):
        return self.views[view]["params"][name]["value"]


class Canvas:
    draft = False     # --draft: write anyway and list every text that does not fit
    problems = []

    def _fail(self, msg):
        if not Canvas.draft:
            raise Overflow(msg)
        Canvas.problems.append(msg)

    def __init__(self, pack, view, w, h, state=None, title=None):
        self.p, self.view, self.w, self.h = pack, view, w, h
        self.title = title
        self.rec = pack.rec(view)
        self.state = state
        self.out = []
        self.keys = []
        self.cap = pack.sizes["caption_px"]

    # colours ------------------------------------------------------------------------------------------------
    def col(self, token):
        if token.startswith("cat:"):
            return self.p.cat[token[4:]]
        if token.startswith("seq:"):
            return self.p.seq[int(token[4:])]
        if token.startswith("div:"):
            return self.p.div[int(token[4:])]
        return self.p.tokens[token]

    # primitives ---------------------------------------------------------------------------------------------
    def _style(self, fill=None, stroke=None, sw=1.0, dash=None, opacity=None):
        a = f' fill="{self.col(fill)}"' if fill else ' fill="none"'
        if stroke:
            a += f' stroke="{self.col(stroke)}" stroke-width="{n(sw)}"'
        if dash:
            a += f' stroke-dasharray="{dash}"'
        if opacity is not None:
            a += f' opacity="{opacity}"'
        return a

    def rect(self, x, y, w, h, fill=None, stroke=None, sw=1.0, dash=None, rx=0, opacity=None):
        r = f' rx="{n(rx)}"' if rx else ""
        self.out.append(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}"{r}{self._style(fill, stroke, sw, dash, opacity)}/>')

    def hatch(self, x, y, w, h, rx=0):
        r = f' rx="{n(rx)}"' if rx else ""
        self.out.append(f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}"{r} fill="url(#hatch)"/>')

    def line(self, x1, y1, x2, y2, stroke="mark.region", sw=1.0, dash=None, opacity=None):
        self.out.append(f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}"{self._style(None, stroke, sw, dash, opacity)}/>')

    def circle(self, cx, cy, r, fill=None, stroke=None, sw=1.0, dash=None, opacity=None):
        self.out.append(f'<circle cx="{n(cx)}" cy="{n(cy)}" r="{n(r)}"{self._style(fill, stroke, sw, dash, opacity)}/>')

    def ellipse(self, cx, cy, rx, ry, fill=None, stroke=None, sw=1.0, dash=None, opacity=None):
        self.out.append(f'<ellipse cx="{n(cx)}" cy="{n(cy)}" rx="{n(rx)}" ry="{n(ry)}"{self._style(fill, stroke, sw, dash, opacity)}/>')

    def poly(self, pts, fill=None, stroke=None, sw=1.0, dash=None, opacity=None, close=False):
        d = " ".join(f"{n(x)},{n(y)}" for x, y in pts)
        tag = "polygon" if close else "polyline"
        self.out.append(f'<{tag} points="{d}"{self._style(fill, stroke, sw, dash, opacity)}/>')

    def text(self, x, y, s, maxw, size=None, fill="text.primary", anchor="start", mono=False, bold=False, cls=None):
        size = size or self.cap
        s = str(s)
        if not s:
            return 0.0
        est = text_width(s, size, mono, bold)
        if size < self.cap:
            self._fail(f"{self.view}: text {s!r} is smaller than the caption size")
        if est > maxw + 0.05:
            self._fail(f"{self.view}: text {s!r} needs {est:.0f} px, its box has {maxw:.0f} px")
        x0 = x if anchor == "start" else x - est if anchor == "end" else x - est / 2
        if x0 < -0.05 or x0 + est > self.w + 0.05:
            self._fail(f"{self.view}: text {s!r} leaves the page ({x0:.0f} to {x0 + est:.0f} of {self.w})")
        a = f' font-family="{MONO if mono else SANS}" font-size="{n(size)}"'
        if bold:
            a += ' font-weight="bold"'
        if anchor != "start":
            a += f' text-anchor="{anchor}"'
        if cls:
            a += f' class="{cls}"'
        self.out.append(f'<text x="{n(x)}" y="{n(y)}"{a} fill="{self.col(fill)}" data-maxw="{n(maxw)}">{escape(s)}</text>')
        return est

    # elements -----------------------------------------------------------------------------------------------
    def frame(self, key, x, y, w, h, grade=None, fill=None):
        """The box of one element of the record, with its key. -> (x, y, w, h) of the room inside."""
        el = self.p.el(self.view, key)
        on_chart = el["kind"] in CHART_KINDS if fill is None else fill == "bg.chart"
        edge = self.p.app[grade]["tile_edge"] if grade else "solid"
        self.rect(x, y, w, h, fill=fill or ("bg.chart" if on_chart else "bg.panel"), stroke="mark.region", dash=EDGE_DASH[edge], rx=6)
        if edge == "hatched":
            self.hatch(x, y, w, h, rx=6)
        self.text(x + 8, y + 16, key, w - 16, fill="text.on_chart_secondary" if on_chart else "text.link", mono=True, cls="key")
        self.keys.append(key)
        return x + 8, y + 22, w - 16, h - 28

    def tag(self, key, x, y, maxw, on_chart=True):
        """The key of an element that has no box of its own (an overlay on video or court)."""
        self.p.el(self.view, key)
        self.text(x, y, key, maxw, fill="text.on_chart_secondary" if on_chart else "text.link", mono=True, cls="key")
        self.keys.append(key)

    def badge(self, x, y, label, on_chart=False):
        """A text badge on the baseline y. -> its width."""
        w = text_width(label, self.cap) + 10
        tok = "text.on_chart_secondary" if on_chart else "text.secondary"
        self.rect(x, y - 12, w, 16, stroke=tok, rx=8)
        self.text(x + 5, y, label, w - 8, fill=tok)
        return w

    def value(self, x, y, s, maxw, grade="observed", size=None, on_chart=False, age_s=None, reason=None, bold=True):
        """One value drawn by the grade table of the contract. -> x after the value and its badge."""
        a = self.p.app[grade]
        size = size or self.p.sizes["value_px"]
        tok = a["value_text"]
        if on_chart:
            tok = {"text.primary": "text.on_chart", "text.stale": "text.on_chart_stale"}[tok]
        if a["badge"] in ("reason", "under review"):
            s = "–"
        w = self.text(x, y, s, maxw, size=size, fill=tok, bold=bold)
        x2 = x + w + 6
        room = maxw - w - 6
        if a["badge"] in ("prov", "est"):
            x2 += self.badge(x2, y, self.p.badges[a["badge"]], on_chart) + 6
            room = maxw - (x2 - x)
        if a["shows_age"] and age_s is not None:
            t = self.p.badges["age"].replace("<n>", str(age_s))
            x2 += self.text(x2, y, t, room, fill="text.on_chart_stale" if on_chart else "text.stale") + 6
        if a["badge"] == "reason":
            x2 += self.text(x2, y, reason, room, fill="text.on_chart_stale" if on_chart else "text.stale") + 6
        if a["badge"] == "under review":
            x2 += self.text(x2, y, "under review", room, fill="text.on_chart_stale" if on_chart else "text.stale") + 6
        return x2

    def label(self, x, y, s, maxw, on_chart=False, fill=None):
        return self.text(x, y, s, maxw, fill=fill or ("text.on_chart_secondary" if on_chart else "text.secondary"))

    def rows(self, x, y, w, cols, rows, on_chart=False, step=18, head=True):
        """A small table. cols: [(header, width share, anchor)]."""
        total = sum(c[1] for c in cols)
        xs, cx = [], x
        for _, share, anchor in cols:
            cw = w * share / total
            xs.append((cx, cw, anchor))
            cx += cw
        sec = "text.on_chart_secondary" if on_chart else "text.secondary"
        pri = "text.on_chart" if on_chart else "text.primary"
        if head:
            for (hx, cw, anchor), (name, _, _) in zip(xs, cols):
                self.text(hx + (cw - 6 if anchor == "end" else 0), y, name, cw - 6, fill=sec, anchor=anchor)
            self.line(x, y + 5, x + w, y + 5, opacity=0.5)
            y += step + 2
        for r in rows:
            stale = isinstance(r, dict)
            cells = r["cells"] if stale else r
            for (hx, cw, anchor), cell in zip(xs, cells):
                self.text(hx + (cw - 6 if anchor == "end" else 0), y, cell, cw - 6, fill=(r["fill"] if stale else pri), anchor=anchor)
            y += step
        return y

    def chip(self, x, y, s, on_chart=False, active=False):
        w = text_width(s, self.cap) + 16
        self.rect(x, y - 13, w, 20, stroke="text.link" if active else "mark.region", rx=10, sw=1.5 if active else 1)
        self.text(x + 8, y + 1, s, w - 14, fill="text.on_chart" if on_chart else "text.primary")
        return w + 6

    def header(self, state_words):
        rec = self.rec
        self.text(12, 20, f"{rec['id']}  {rec['name']}", self.w - 24, size=self.p.sizes["body_px"], bold=True)
        self.text(12, 38, state_words, self.w - 24, fill="text.secondary")

    def footer(self, y=None):
        """The last line. With y (the bottom of the content) the page takes its height from the content."""
        if y is not None:
            self.h = int(math.ceil(y)) + 28
        self.text(12, self.h - 10, FOOT, self.w - 24, fill="text.stale")

    def svg(self):
        rec = self.rec
        title = self.title or f"{rec['id']} {rec['name']}" + (f" at {self.state}" if self.state else "")
        desc = (f"{'Drawing' if self.title else 'Wireframe of the view ' + self.view} of config/views ({self.p.core['version']}), drawn at {self.w} px in the {self.p.theme} theme. "
                f"Made-up numbers; teams are Home and Away. Generated by tools/specgen/views/gen_wireframes.py.")
        nd = self.col("mark.no_data")
        head = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" height="{self.h}" role="img" '
                f'aria-labelledby="t d" data-view="{"" if self.title else self.view}" data-width="{self.w}">',
                f'<title id="t">{escape(title)}</title>', f'<desc id="d">{escape(desc)}</desc>',
                f'<defs><pattern id="hatch" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
                f'<line x1="0" y1="0" x2="0" y2="8" stroke="{nd}" stroke-width="2"/></pattern></defs>']
        page = f'<rect x="0" y="0" width="{self.w}" height="{self.h}" fill="{self.col("bg.page")}"/>'
        return "\n".join(head + [page] + self.out + ["</svg>"]) + "\n"


# --------------------------------------------------------------------------------------------------------------------
# the court, from the named-spots constants
class Court:
    PAD_M = 0.4

    def __init__(self, c, x, y, w):
        K = c.p.K
        self.c, self.K = c, K
        self.s = w / (2 * K["SIDE_X"] + 2 * self.PAD_M)
        self.x, self.y, self.w = x, y, w
        self.top, self.bot = K["HALF_Y"] + self.PAD_M, K["END_Y"] - self.PAD_M
        self.h = (self.top - self.bot) * self.s

    def px(self, X, Y):
        K = self.K
        dy = (Y - self.bot) if self.c.p.overhead else (self.top - Y)
        return self.x + (X + K["SIDE_X"] + self.PAD_M) * self.s, self.y + dy * self.s

    def arc(self, r, a0, a1, centre=(0.0, 0.0), step=4.0):
        k = max(2, int(abs(a1 - a0) / step) + 1)
        return [self.px(centre[0] + r * math.cos(math.radians(a0 + (a1 - a0) * i / k)), centre[1] + r * math.sin(math.radians(a0 + (a1 - a0) * i / k)))
                for i in range(k + 1)]

    def draw(self):
        c, K, P = self.c, self.K, self.px
        ln = dict(stroke="mark.court_line", sw=1.2)
        c.poly([P(-K["SIDE_X"], K["HALF_Y"]), P(-K["SIDE_X"], K["END_Y"]), P(K["SIDE_X"], K["END_Y"]), P(K["SIDE_X"], K["HALF_Y"])], close=True, **ln)
        c.poly([P(-K["LANE_X"], K["END_Y"]), P(-K["LANE_X"], K["FT_Y"]), P(K["LANE_X"], K["FT_Y"]), P(K["LANE_X"], K["END_Y"])], **ln)
        c.poly(self.arc(K["LANE_X"], 0, 180, (0.0, K["FT_Y"])), **ln)                      # free-throw circle: radius = half the lane width
        c.poly(self.arc(K["LANE_X"], 180, 360, (0.0, K["FT_Y"])), dash="4 4", **ln)
        c.poly([P(K["CORNER_X"], K["END_Y"]), P(K["CORNER_X"], K["BREAK_Y"])] + self.arc(K["ARC_R"], K["BREAK_T"], 180 - K["BREAK_T"])
               + [P(-K["CORNER_X"], K["BREAK_Y"]), P(-K["CORNER_X"], K["END_Y"])], **ln)
        c.poly([P(K["RA_R"], K["BOARD_Y"])] + self.arc(K["RA_R"], 0, 180) + [P(-K["RA_R"], K["BOARD_Y"])], **ln)
        half = K["LANE_X"] / 2                                                             # backboard: 1.8288 m wide
        c.line(*P(-half, K["BOARD_Y"]), *P(half, K["BOARD_Y"]), stroke="mark.court_line", sw=2.5)
        c.circle(*P(0, 0), K["LANE_X"] / 8 * self.s, stroke="mark.court_line", sw=1.2)     # rim: 0.2286 m radius
        c.poly(self.arc(K["LANE_X"], 180, 360, (0.0, K["HALF_Y"])), **ln)                  # centre circle

    def player(self, team, X, Y, num, grade="observed", age_s=None, hold=False):
        """One player by the grade table: filled, filled with a ring (HOLD), or hollow with its region."""
        c = self.c
        x, y = self.px(X, Y)
        mark = c.p.core["display_contract"]["visual_standard"]["team_marks"][team]
        marker = c.p.app[grade]["court_marker"]
        r = 10
        if marker.startswith("hollow"):
            c.ellipse(x, y, 1.25 * self.s, 1.0 * self.s, stroke="mark.region", dash="3 3")
            self._shape(mark["shape"], x, y, r, None, mark["token"])
            c.text(x, y + 4, num, 2 * r, fill="text.on_chart", anchor="middle", bold=True)
            c.text(x, y + self.s + 14, f"est {age_s} s", 60, fill="text.on_chart_stale", anchor="middle")
        elif hold:
            c.circle(x, y, r + 4, stroke="mark.region", sw=1.5)
            c.circle(x, y, r, fill="mark.region")
            c.text(x, y + 4, "?", 2 * r, fill="text.on_team_away", anchor="middle", bold=True)
        else:
            self._shape(mark["shape"], x, y, r, mark["token"], None)
            c.text(x, y + 4, num, 2 * r, fill=mark["label_text"], anchor="middle", bold=True)

    def _shape(self, shape, x, y, r, fill, stroke):
        if shape == "circle":
            self.c.circle(x, y, r, fill=fill, stroke=stroke, sw=1.5)
        else:
            self.c.rect(x - r, y - r, 2 * r, 2 * r, fill=fill, stroke=stroke, sw=1.5, rx=2)

    def ball(self, X, Y):
        x, y = self.px(X, Y)
        self.c.circle(x, y, 4, fill="text.on_chart")


# made-up positions in metres, attacked-rim frame (x to the attacker's right, y toward half court)
HOME = [("3", 0.5, 7.9), ("1", 4.9, 5.6), ("11", -5.4, 5.6), ("22", -6.9, 0.3), ("44", -1.83, 4.19)]
AWAY = [("0", 0.4, 6.7), ("5", 4.2, 4.6), ("12", -4.5, 4.7), ("?", -0.9, 1.6), ("33", 6.5, 1.3)]
CAMERA = [(-7.62, 12.7), (5.9, 12.7), (5.2, -1.6), (-7.62, -1.6)]


def draw_ten(ct, offscreen=True):
    for num, X, Y in HOME:
        ct.player("home", X, Y, num)
    for num, X, Y in AWAY:
        if num == "?":
            ct.player("away", X, Y, num, grade="inferred", hold=True)
        elif num == "33" and offscreen:
            ct.player("away", X, Y, num, grade="imputed", age_s=3)
        else:
            ct.player("away", X, Y, num)
    ct.ball(HOME[0][1] + 0.5, HOME[0][2] + 0.1)


def camera_area(ct):
    ct.c.poly([ct.px(X, Y) for X, Y in CAMERA], stroke="mark.region", dash="6 4", close=True, opacity=0.8)


def video_box(c, x, y, w, h):
    c.hatch(x, y, w, h)
    c.rect(x + w / 2 - 150, y + h / 2 - 24, 300, 44, fill="bg.chart", rx=6)
    c.text(x + w / 2, y + h / 2 - 6, "broadcast video, private store", 290, fill="text.on_chart", anchor="middle")
    c.text(x + w / 2, y + h / 2 + 12, "no frame is shown in a wireframe", 290, fill="text.on_chart_stale", anchor="middle")


def band_line(c, pts, band, stroke, x, y, w, h, ymin, ymax, xmax, dash=None):
    """A line with a fading band. pts: [(t, v)], band: half width in value units."""
    def P(t, v):
        return x + w * t / xmax, y + h * (1 - (v - ymin) / (ymax - ymin))
    up = [P(t, min(ymax, v + band)) for t, v in pts]
    lo = [P(t, max(ymin, v - band)) for t, v in reversed(pts)]
    c.poly(up + lo, fill=stroke, opacity=0.22, close=True)
    c.poly([P(t, v) for t, v in pts], stroke=stroke, sw=2, dash=dash)
    return P


# --------------------------------------------------------------------------------------------------------------------
# VW-LIVE-01 at D0, D1 and D3
LEVEL_WORDS = {"D0_full": "D0 full", "D1_bug_away": "D1 bug away", "D3_replay": "D3 replay"}


def live_panel(p, level):
    view = "live_game_state_panel"
    rec = p.rec(view)
    assert level in ["D0_full"] + list(rec.get("wireframe_states") or {}), level
    prov_s, grey_s = p.param(view, "clock_prov_max_s"), p.param(view, "clock_greyed_max_s")
    away_s = {"D0_full": 0, "D1_bug_away": 12, "D3_replay": 8}[level]            # seconds since the level began
    assert prov_s < 12 <= grey_s                                                   # at 12 s the clock is carried, not yet a dash
    frozen = level == "D3_replay"
    g = "carried" if frozen else "observed"                                        # D3: every tile frozen, greyed
    W, M = rec["min_width_px"], 12
    IW = W - 2 * M
    c = Canvas(p, view, W, 0, state=LEVEL_WORDS[level])
    c.header(f"level {LEVEL_WORDS[level]}, drawn at {W} px")
    y = 50

    # as_of_banner
    bx, by, bw, bh = c.frame("as_of_banner", M, y, IW, 62)
    known = {"D0_full": "19:42:07", "D1_bug_away": "19:42:19", "D3_replay": "19:42:15"}[level]
    c.text(bx, by + 12, f"LIVE · as known {known} · oldest value {away_s} s", bw, bold=True)
    words = {"D0_full": "level D0 full · feed ok · stream delay 9 s",
             "D1_bug_away": f"level D1 bug away {away_s} s · feed ok · delay 9 s",
             "D3_replay": f"REPLAY · frozen {away_s} s ago · nothing ticks"}[level]
    c.text(bx, by + 30, words, bw, fill="text.attention" if level != "D0_full" else "text.secondary", bold=frozen)
    y += 70

    # clock_period and score
    half = (IW - 8) / 2
    clock_grade = {"D0_full": "observed", "D1_bug_away": "carried", "D3_replay": "carried"}[level]
    bx, by, bw, bh = c.frame("clock_period", M, y, half, 108, grade=clock_grade)
    c.label(bx, by + 10, "2nd half · " + ("running" if level == "D0_full" else "running?" if level == "D1_bug_away" else "stopped"), bw)
    if level == "D1_bug_away":
        c.value(bx, by + 44, "7:30", bw, grade="carried", size=p.sizes["hero_px"], age_s=away_s)
        c.label(bx, by + 62, "between 7:30 and 7:42", bw, fill="text.stale")
        c.label(bx, by + 78, "shot clock 6 · 12 s ago", bw, fill="text.stale")
    else:
        c.value(bx, by + 44, "7:42", bw, grade=clock_grade, size=p.sizes["hero_px"], age_s=away_s)
        c.label(bx, by + 62, "frozen at the last value" if frozen else "tenths under 1:00", bw, fill="text.stale" if frozen else None)
        c.label(bx, by + 78, "shot clock 18", bw, fill="text.stale" if frozen else None)
    bx, by, bw, bh = c.frame("score", M + half + 8, y, half, 108, grade=g)
    c.label(bx, by + 10, "Home", 70)
    c.label(bx + 78, by + 10, "Away", bw - 78)
    c.value(bx, by + 44, "61", 60, grade=g, size=p.sizes["hero_px"])
    c.value(bx + 78, by + 44, "58", bw - 78, grade=g, size=p.sizes["hero_px"])
    c.label(bx, by + 62, f"frozen {away_s} s ago · margin +3" if frozen else "margin +3 · run 6-0 Home", bw, fill="text.stale" if frozen else None)
    c.label(bx, by + 78, "lead changes 7 · ties 4", bw, fill="text.stale" if frozen else None)
    y += 116

    def tile(key, h, lines, grade=g, x=M, w=IW):
        bx, by, bw, bh = c.frame(key, x, y, w, h, grade=grade)
        for i, (s, strong) in enumerate(lines):
            stale = c.p.app[grade]["value_text"] == "text.stale"
            c.text(bx, by + 12 + 18 * i, s, bw, size=p.sizes["body_px"] if strong else c.cap,
                   fill="text.stale" if stale else "text.primary" if strong else "text.secondary")

    age = f" · {away_s} s ago" if frozen else ""
    tile("possession_ball", 66, [("Home ball · live · half court" + age, True), ("handler #3 · 4 s since control · possession 71", False)])
    y += 74
    tile("foul_tracker", 66, [("6  |  8 BONUS", True), ("team fouls · #44 has 3", False)], w=half)
    tile("timeouts_left", 66, [("3  |  2", True), ("challenge yes | used", False)], x=M + half + 8, w=half)
    y += 74
    tile("lineup_identity", 84, [("Home  #1  #3  #11  #22  #44", True), ("Away  #0  #5  #12  ?  #33", True),
                                 ("? is #2 or #15 · HOLD 6 s · stint 3:10", False)])
    y += 92
    tile("flag_feed", 66, [("1 open flag", True), ("identity · Away #2 or #15 · HOLD 6 s · queued", False)])
    y += 74
    # situation and strip: no model before P6 (open question OQ-VW-13)
    bx, by, bw, bh = c.frame("situation", M, y, IW, 66, grade="unknown")
    x2 = c.label(bx, by + 12, "win probability", bw)
    c.value(bx + x2 + 8, by + 13, "", bw - x2 - 8, grade="unknown", size=p.sizes["body_px"], reason=f"no model before {p.el(view, 'situation')['phase']}")
    c.label(bx, by + 30, "clutch: no · garbage time: no, no, no" + (" · held" if frozen else ""), bw)
    y += 74
    bx, by, bw, bh = c.frame("wp_leverage_strip", M, y, IW, 66, fill="bg.chart")
    c.hatch(bx, by + 2, bw, 18)
    c.text(bx, by + 36, f"not drawn before {p.el(view, 'wp_leverage_strip')['phase']}", bw, fill="text.on_chart_stale")
    y += 74
    tile("tactics", 66, [("Horns 0.86 · man 0.93 · drop 0.88" + age, True), ("set · scheme · screen coverage, with confidence", False)])
    y += 74

    # mini_court
    ct = Court(c, M + 8, 0, IW - 16)
    ch = ct.h + 60
    bx, by, bw, bh = c.frame("mini_court", M, y, IW, ch)
    ct.y = by + 4
    if frozen:
        c.hatch(bx, by + 4, bw, ct.h)
        c.rect(bx + bw / 2 - 110, by + ct.h / 2 - 12, 220, 28, fill="bg.chart", rx=6)
        c.text(bx + bw / 2, by + ct.h / 2 + 7, "court hidden – replay", 210, fill="text.on_chart", anchor="middle", size=p.sizes["body_px"])
        c.text(bx, by + ct.h + 22, "0 of 10 drawn", bw, fill="text.on_chart_stale")
    else:
        ct.draw()
        camera_area(ct)
        draw_ten(ct)
        c.text(bx, by + ct.h + 22, "10 of 10 drawn, 1 estimated · 78 % of the court in view", bw, fill="text.on_chart_secondary")
    y += ch + 8

    bx, by, bw, bh = c.frame("bench_board", M, y, IW, 120, grade=g)
    fill = "text.stale" if frozen else "text.primary"
    c.rows(bx, by + 10, bw, [("Home", 3, "start"), ("fouls", 2, "end"), ("stint", 2, "end"), ("Away", 3, "start"), ("fouls", 2, "end"), ("stint", 2, "end")],
           [{"cells": r, "fill": fill} for r in (["#44 floor", "3 !", "3:10", "#33 floor", "2", "3:10"], ["#22 floor", "1", "5:42", "#12 floor", "4 !", "0:48"],
                                                    ["#15 bench", "2", "1:05", "#21 bench", "0", "6:30"], ["#30 bench", "0", "9:12", "#4 bench", "1", "2:17"])])
    y += 128
    tile("observability", 66, [("replay · bug not shown" if frozen else "main camera · bug hidden" if level == "D1_bug_away" else "main camera · bug visible", True),
                               ("tracking and mapping are not read in a replay" if frozen else "tracking 0.94 · court mapping 0.97 · ball seen", False)], grade="observed")
    y += 74
    tile("game_header", 66, [("Home vs Away · regular season", True), ("neutral site · crew of 3 · pre-game card", False)], grade="confirmed")
    y += 74

    if level == "D1_bug_away":   # the clock tile through one bug-away stretch, by the limits of the record
        c.text(M, y + 18, "The clock tile through one hidden stretch", IW, bold=True, size=p.sizes["body_px"])
        c.text(M, y + 36, f"limits of the record: prov {n(prov_s)} s, greyed up to {n(grey_s)} s", IW, fill="text.secondary")
        y += 46
        steps = [("0 s", "observed", "7:42", None, None), (f"+{n(prov_s - 1)} s", "inferred", "7:40", None, None),
                 (f"+{away_s} s", "carried", "7:30", away_s, None), (f"+{n(grey_s + 1)} s", "unknown", "", None, f"bug away {n(grey_s + 1)} s")]
        for i, (when, grade, val, a_s, reason) in enumerate(steps):
            tx, ty = M + (half + 8) * (i % 2), y + 62 * (i // 2)
            c.rect(tx, ty, half, 54, fill="bg.panel", stroke="mark.region", dash=EDGE_DASH[p.app[grade]["tile_edge"]], rx=6)
            c.text(tx + 8, ty + 16, f"{when} · {grade}", half - 16, fill="text.secondary")
            c.value(tx + 8, ty + 42, val, half - 16, grade=grade, age_s=a_s, reason=reason)
        y += 124
    c.footer(y)
    return c


# --------------------------------------------------------------------------------------------------------------------
# VW-REV-01 possession explorer
def possession_explorer(p):
    view = "possession_explorer"
    rec = p.rec(view)
    W, M = rec["min_width_px"], 16
    c = Canvas(p, view, W, 0)
    c.header(f"one possession chosen, drawn at {W} px")
    bx, by, bw, bh = c.frame("as_of_banner", M, 50, W - 2 * M, 30)
    c.text(bx + 110, by - 6, "RECORDED · as of event · pass anchored · state version 3f9a12c0 · play-by-play version 4 · level at the playhead: D0 full", bw - 110)
    bx, by, bw, bh = c.frame("filter_bar", M, 88, W - 2 * M, 30)
    x = bx + 90
    for s in ("game: Home vs Away", "period: 2", "player: any", "lineup: any", "set: any", "coverage: any"):
        x += c.chip(x, by - 6, s)
    x += c.chip(x, by - 6, "state: clutch, flag K06", active=True)
    c.text(bx + bw, by - 5, "9 possessions left · rates show \"too few\" (n below 30)", 380, fill="text.attention", anchor="end")

    top = 126
    # possession_list
    bx, by, bw, bh = c.frame("possession_list", M, top, 250, 640)
    rows = [["7:58", "Home", "1", "2", "1.02"], ["7:42", "Away", "1", "0", "0.97"], ["7:21", "Home", "2", "3", "1.08"], ["6:55", "Away", "1", "2", "0.99"],
            ["6:31", "Home", "1", "0", "1.01"], ["6:12", "Away", "1", "2", "1.12"], ["5:47", "Home", "1", "2", "1.05"], ["5:20", "Away", "2", "0", "0.94"], ["4:58", "Home", "1", "3", "1.03"]]
    c.rect(bx - 4, by + 18, bw + 8, 20, fill="bg.page", stroke="text.link", rx=4)
    c.rows(bx, by + 10, bw, [("clock", 3, "start"), ("team", 3, "start"), ("ch", 2, "end"), ("pts", 2, "end"), ("value", 3, "end")], rows)
    c.label(bx, by + 214, "pts: official, play-by-play v4", bw)
    c.label(bx, by + 232, "value: model pv-0.2, band in row", bw)
    c.label(bx, by + 250, "every row opens its frames", bw)

    # video with overlays
    vx, vw = M + 258, 470
    bx, by, bw, bh = c.frame("video", vx, top, vw, 296)
    video_box(c, bx, by, bw, bh)
    # timeline
    bx, by, bw, bh = c.frame("timeline", vx, top + 304, vw, 132)
    for i, (name, boxes) in enumerate((("chances", [(0, 1.0)]), ("events", [(0.05, 0.02), (0.38, 0.02), (0.61, 0.02), (0.93, 0.03)]),
                                       ("shot clock", [(0, 0.93)]), ("set phases", [(0.08, 0.3), (0.4, 0.5)]), ("replays", []))):
        yy = by + 10 + 19 * i
        c.text(bx, yy + 4, name, 80, fill="text.on_chart_secondary")
        c.line(bx + 86, yy, bx + bw, yy, opacity=0.4)
        for a, b in boxes:
            c.rect(bx + 86 + (bw - 86) * a, yy - 6, (bw - 86) * b, 12, fill="cat:sky blue", opacity=0.8, rx=2)
    c.line(bx + 86 + (bw - 86) * 0.38, by, bx + 86 + (bw - 86) * 0.38, by + 96, stroke="mark.attention", sw=2)
    # value_curve
    bx, by, bw, bh = c.frame("value_curve", vx, top + 444, vw, 196)
    pts = [(0, 1.02), (3, 1.02), (5, 1.10), (8, 1.10), (9, 1.22), (12, 1.22), (13, 1.31), (15, 1.31), (16, 2.0)]
    P = band_line(c, pts[:-1], 0.08, "cat:sky blue", bx + 36, by + 10, bw - 46, bh - 62, 0.8, 1.6, 16)
    for t, v, s in ((5, 1.10, "+0.08 pass"), (9, 1.22, "+0.12 screen"), (13, 1.31, "+0.09 drive")):
        px_, py_ = P(t, v)
        c.circle(px_, py_, 4, fill="text.on_chart")
        c.text(px_ + 6, py_ + 16, s, 90, fill="text.on_chart")
    for v in (0.8, 1.2, 1.6):
        c.text(bx + 30, P(0, v)[1] + 4, f"{v:.1f}", 30, fill="text.on_chart_secondary", anchor="end")
    c.text(bx + 36, by + bh - 22, "expected points across the possession, by second", bw - 40, fill="text.on_chart_secondary")
    c.text(bx + 36, by + bh - 6, "band 95 % · model pv-0.2 · made 2 points at 16 s (official)", bw - 40, fill="text.on_chart_secondary")

    # court with trails and set overlay
    cx, cw = vx + vw + 8, 300
    ct = Court(c, cx + 8, 0, cw - 16)
    bx, by, bw, bh = c.frame("court", cx, top, cw, ct.h + 74)
    ct.y = by + 4
    ct.draw()
    draw_ten(ct, offscreen=False)
    trail = [ct.px(X, Y) for X, Y in ((-3.0, 8.6), (-1.6, 8.4), (-0.4, 8.1), (0.5, 7.9))]
    c.poly(trail, stroke="team.home", sw=2, opacity=0.9)
    c.poly([ct.px(1.0, 7.9), ct.px(4.4, 5.9)], stroke="text.on_chart", sw=1.5, dash="5 3")
    c.poly([ct.px(-1.83, 4.19), ct.px(-0.6, 6.4)], stroke="mark.attention", sw=1.5, dash="2 3")
    c.tag("trails_and_arrows", bx, by + ct.h + 22, bw)
    c.text(bx + 140, by + ct.h + 22, "trail, pass +0.08", bw - 140, fill="text.on_chart")
    c.tag("set_overlay", bx, by + ct.h + 40, bw)
    c.text(bx + 100, by + ct.h + 40, "Horns 0.86, left at step 3", bw - 100, fill="text.on_chart")
    # possession_header
    hy = top + ct.h + 82
    bx, by, bw, bh = c.frame("possession_header", cx, hy, cw, 640 - (ct.h + 82))
    for i, s in enumerate(("Home · dead-ball start · not after a timeout", "16 s · 1 chance · shot clock 30 to 14", "2 points (official, play-by-play v4)",
                           "value at start 1.02, band 0.94 to 1.10", "model pv-0.2 · seen on main camera 96 %")):
        c.text(bx, by + 12 + 18 * i, s, bw, fill="text.primary" if i < 3 else "text.secondary")

    # inspector, matchups, clip export
    ix = cx + cw + 8
    iw = W - M - ix
    bx, by, bw, bh = c.frame("inspector", ix, top, iw, 330)
    for i, (k, v) in enumerate((("what", "pass, #3 to #1"), ("value", "+0.08 points"), ("grade", "observed, 0.91"), ("source", "tracking and pbp"),
                                ("as of", "event, anchored"), ("version", "pv-0.2, rules 0.2"), ("lineage", "run r-0042"), ("history", "same as v3"), ("actions", "show rows, clip"))):
        c.text(bx, by + 12 + 32 * i, k, bw, fill="text.secondary")
        c.text(bx, by + 28 + 32 * i, v, bw)
    bx, by, bw, bh = c.frame("matchups", ix, top + 338, iw, 204)
    c.rows(bx, by + 10, bw, [("pair", 5, "start"), ("share", 3, "end"), ("height", 4, "end")],
           [["#3 by #0", "88 %", "+0.04 m"], ["#1 by #5", "100 %", "-0.02 m"], ["#11 by #12", "100 %", "0.00 m"], ["#22 by #33", "71 %", "+0.09 m"], ["#44 by ?", "HOLD", "–"]])
    c.label(bx, by + 140, "1 switch at 7:49", bw)
    c.label(bx, by + 158, "? is #2 or #15 (HOLD)", bw)
    bx, by, bw, bh = c.frame("clip_export", ix, top + 550, iw, 90)
    c.chip(bx, by + 12, "clip reference", active=True)
    c.chip(bx + 116, by + 12, "top-down")
    c.label(bx, by + 40, "no video leaves the store", bw)

    # action_list
    bx, by, bw, bh = c.frame("action_list", M, top + 648, W - 2 * M, 176)
    c.rows(bx, by + 10, bw, [("clock", 2, "start"), ("shot clock", 2, "start"), ("who", 3, "start"), ("what", 6, "start"), ("value before", 3, "end"), ("after", 3, "end"), ("change", 3, "end"), ("credit", 4, "start")],
           [["7:55", "27", "#3", "brings the ball up", "1.02", "1.02", "0.00", "  none"], ["7:53", "25", "#3 to #1", "pass, right wing", "1.02", "1.10", "+0.08", "  passer #3"],
            ["7:49", "21", "#44 for #1", "ball screen, coverage drop 0.88", "1.10", "1.22", "+0.12", "  screener #44"], ["7:45", "17", "#1", "drive, middle", "1.22", "1.31", "+0.09", "  driver #1"],
            ["7:42", "14", "#1", "made lay-up, 2 points (official)", "1.31", "2.00", "+0.69", "  shooter #1"]])
    c.label(bx, by + 132, "value: class model, band and version in the inspector · change: who is credited comes from the value credits · every row opens its frames", bw)
    c.footer(top + 648 + 176)
    return c


# --------------------------------------------------------------------------------------------------------------------
# VW-STU-01 Studio game canvas with the inspector open
def studio_game_canvas(p):
    view = "studio_game_canvas"
    rec = p.rec(view)
    W, M = rec["min_width_px"], 16
    c = Canvas(p, view, W, 0)
    c.header(f"inspector open on the game clock, drawn at {W} px")
    bx, by, bw, bh = c.frame("as_of_banner", M, 50, 760, 37)
    c.text(bx + 110, by - 6, "RECORDED · pass anchored · version 3f9a12c0 (current) · 7:40 · video 01:12:33 · D1 bug away", bw - 110)
    bx, by, bw, bh = c.frame("command_palette", M + 768, 50, W - 2 * M - 768, 82)
    for i, s in enumerate(("/ jump to clock ...", "] next possession · n next disputed label · l layer list", "t switch what was true / what we knew · z undo")):
        c.text(bx, by + 12 + 18 * i, s, bw, mono=i == 0, fill="text.primary" if i == 0 else "text.secondary")
    bx, by, bw, bh = c.frame("filter_bar", M, 95, 760, 37)
    x = bx + 90
    for s in ("period: 2", "player: any", "lineup: any", "set: any", "coverage: any", "state: any"):
        x += c.chip(x, by - 6, s)

    top = 140
    # left: tree and layer list
    lw = 196
    bx, by, bw, bh = c.frame("tree_navigator", M, top, lw, 250)
    for i, (s, cur) in enumerate((("game · 138 poss.", False), ("half 2 · 70", False), ("10:00 to 5:00 · 18", False), ("possession 71", False),
                                  ("chance 1", False), ("action: screen", True), ("player #44", False))):
        c.text(bx + 10 * min(i, 6), by + 12 + 29 * i, s, bw - 10 * min(i, 6), fill="text.link" if cur else "text.primary", bold=cur)
        if i:
            c.line(bx + 10 * (i - 1) + 3, by - 12 + 29 * i, bx + 10 * (i - 1) + 3, by + 6 + 29 * i, opacity=0.6)
    bx, by, bw, bh = c.frame("layer_list", M, top + 258, lw, 372)
    layers = ["boxes", "tracks", "ids", "court lines", "passing lanes", "spacing hull", "defender matchups", "transition numbers", "value heat map",
              "trails", "pass arrows", "switch marks", "set template path"]
    on = {"tracks", "ids", "defender matchups", "trails", "pass arrows"}
    for i, s in enumerate(layers):
        yy = by + 12 + 25 * i
        grey = s == "value heat map"
        c.rect(bx, yy - 10, 12, 12, stroke="mark.region", fill="text.link" if s in on else None, rx=2)
        c.text(bx + 20, yy, s + (" – no model" if grey else ""), bw - 20, fill="text.stale" if grey else "text.primary")

    # centre: video, court, state panel, timeline
    vx, vw = M + lw + 8, 420
    bx, by, bw, bh = c.frame("video", vx, top, vw, 266)
    video_box(c, bx, by, bw, bh)
    c.tag("layers", bx + 6, by + bh - 8, bw - 12)
    cx, cw = vx + vw + 8, 286
    ct = Court(c, cx + 8, 0, cw - 16)
    bx, by, bw, bh = c.frame("court", cx, top, cw, 266 + 8 + 116)
    ct.y = by + 4
    ct.draw()
    camera_area(ct)
    draw_ten(ct)
    for a, b in ((0, 0), (1, 1), (2, 2)):
        c.poly([ct.px(HOME[a][1], HOME[a][2]), ct.px(AWAY[b][1], AWAY[b][2])], stroke="mark.region", dash="2 3")
    c.text(bx, by + ct.h + 22, "as of event · offline: #2 probable (flagged)", bw, fill="text.on_chart_secondary")
    c.text(bx, by + ct.h + 40, "est = off screen, 95 % region, at most 10 s", bw, fill="text.on_chart_stale")
    c.text(bx, by + ct.h + 58, "dashed outline: what the camera sees", bw, fill="text.on_chart_stale")
    # state panel under the video (the embedded live panel, as known)
    bx, by, bw, bh = c.frame("state_panel", vx, top + 274, vw, 116)
    c.text(bx + 100, by - 6, f"embeds {p.rec('live_game_state_panel')['id']} · as known at the playhead", bw - 100, fill="text.secondary")
    tw = (bw - 16) / 3
    for i, (lab, val, grade) in enumerate((("game clock", "7:40", "inferred"), ("score", "61  58", "observed"), ("possession", "Home", "observed"))):
        tx = bx + (tw + 8) * i
        c.rect(tx, by + 6, tw, 64, fill="bg.page", stroke="text.link" if i == 0 else "mark.region", dash=EDGE_DASH[p.app[grade]["tile_edge"]], rx=4, sw=2 if i == 0 else 1)
        c.label(tx + 6, by + 22, lab, tw - 12)
        c.value(tx + 6, by + 50, val, tw - 12, grade=grade)
    c.label(bx, by + 86, "selected: game clock (opens the inspector)", bw)
    # timeline
    ty = top + 398
    tw_all = vw + 8 + cw
    bx, by, bw, bh = c.frame("timeline", vx, ty, tw_all, 232)
    names = ["flow state", "possession team", "clock grade", "transitions", "events", "possessions", "set phases", "replays, breaks", "corrections", "crowd loudness"]
    for i, name in enumerate(names):
        yy = by + 10 + 19 * i
        c.text(bx, yy + 4, name, 110, fill="text.on_chart_secondary")
        c.line(bx + 116, yy, bx + bw, yy, opacity=0.35)
    tl = bw - 116

    def seg(row, a, b, tok, dash=None, hatch=False, op=0.85):
        yy = by + 10 + 19 * row
        if hatch:
            c.hatch(bx + 116 + tl * a, yy - 6, tl * b, 12)
        else:
            c.rect(bx + 116 + tl * a, yy - 6, tl * b, 12, fill=None if dash else tok, stroke=tok if dash else None, dash=dash, opacity=op, rx=2)
    for a, b in ((0, 0.2), (0.22, 0.2), (0.44, 0.25), (0.71, 0.29)):
        seg(0, a, b, "cat:bluish green")
    for i, (a, b) in enumerate(((0, 0.2), (0.22, 0.2), (0.44, 0.25), (0.71, 0.29))):
        seg(1, a, b, "team.home" if i % 2 == 0 else "team.away")
    seg(2, 0, 0.5, "text.on_chart")
    seg(2, 0.5, 0.04, "text.on_chart")                      # inferred: solid, with a ring
    seg(2, 0.5, 0.04, "text.link", dash="1 0", op=1)
    seg(2, 0.54, 0.1, "text.on_chart_stale", dash="6 4")    # carried: dashed
    seg(2, 0.64, 0.36, "text.on_chart")
    for a in (0.2, 0.22, 0.42, 0.44, 0.69, 0.71):
        seg(3, a, 0.008, "mark.attention")
        seg(4, a + 0.01, 0.006, "text.on_chart")
    for a, b in ((0, 0.2), (0.22, 0.2), (0.44, 0.25), (0.71, 0.29)):
        seg(5, a, b, "cat:sky blue", op=0.7)
    seg(6, 0.46, 0.08, "cat:reddish purple")
    seg(6, 0.56, 0.1, "cat:reddish purple", op=0.6)
    seg(7, 0.845, 0.06, None, hatch=True)
    seg(8, 0.3, 0.008, "cat:yellow")
    c.poly([(bx + 116 + tl * t / 20, by + 10 + 19 * 9 + 5 - 9 * abs(math.sin(t * 0.9)) * (1.6 if 8 < t < 11 else 1)) for t in range(21)], stroke="cat:orange", sw=1.5)
    ph = bx + 116 + tl * 0.52
    c.line(ph, by - 2, ph, by + 10 + 19 * 9 + 8, stroke="mark.attention", sw=2)
    c.text(ph + 6, by + 10 + 19 * 9 + 22, "playhead 7:40 · bug hidden here", 220, fill="text.on_chart")

    # right: inspector open on the game clock
    ix = cx + cw + 8
    iw = W - M - ix
    f = p.ls["game_clock_s"]
    bx, by, bw, bh = c.frame("inspector", ix, top, iw, 560)
    c.rect(ix, top, iw, 560, stroke="text.link", sw=2, rx=6)
    items = [("what it is", ["game clock", f"game_clock_s ({f['id']})"]),
             ("value", ["true at: 7:40 (as of event)", "known at: 7:40 prov (as known)"]),
             ("grade and confidence", ["inferred, 0.93", "dead-reckoned, bug hidden 2 s"]),
             ("source and as-of", ["last bug reading 7:42", "true at 01:12:33 · known at 01:12:33"]),
             ("version", ["state 3f9a12c0 (current)", f"live_state pack {p.ls and vwlib._yaml(vwlib.LIVE_STATE_CORE)['version']}"]),
             ("lineage", ["run r-0042 · config 9c1e", "input: video file, clock map"]),
             ("history", ["same as the previous version"]),
             ("actions", ["open a draft · show rows", "export a clip reference"])]
    yy = by + 12
    for k, vals in items:
        c.text(bx, yy, k, bw, fill="text.secondary")
        for v in vals:
            yy += 18
            c.text(bx, yy, v, bw)
        yy += 28
    bx, by, bw, bh = c.frame("clip_export", ix, top + 568, iw, 62)
    x = bx
    x += c.chip(x, by + 12, "clip reference", active=True)
    c.chip(x, by + 12, "clip in private store")

    # selection_query
    bx, by, bw, bh = c.frame("selection_query", M, top + 638, W - 2 * M, 116)
    m_id = p.core["components"]["value_curve"]["inputs"]["metrics"][0]
    c.text(bx, by + 12, "selection: time range 7:49 to 7:40 on the timeline (1 possession, 3 actions)", bw, fill="text.secondary")
    c.text(bx, by + 34, f"SELECT action_id, value FROM query_layer WHERE metric_id = '{m_id}' AND game_id = :game AND game_clock_s BETWEEN 460 AND 469;", bw, mono=True)
    c.text(bx, by + 56, "shape of the query only (the query layer is R-EN-18) · 3 rows · run again: same rows · saved selections: late-clock screens, HOLD stretches", bw, fill="text.secondary")
    c.text(bx, by + 74, "only aggregates may leave the private store", bw, fill="text.secondary")
    c.footer(top + 638 + 116)
    return c


# --------------------------------------------------------------------------------------------------------------------
# VW-REV-06 the layered tree: game, half, five-minute window, possession, player
def layered_tree(p):
    view = "win_probability_chart"
    rec = p.rec(view)
    W, M = rec["min_width_px"], 16
    c = Canvas(p, view, W, 0)
    c.header(f"the walk down from game to player, drawn at {W} px · a model exists from {rec['phase']}; every probability here is made up")
    bx, by, bw, bh = c.frame("as_of_banner", M, 50, W - 2 * M, 30)
    c.text(bx + 110, by - 6, "RECORDED · pass anchored · play-by-play version 4 · model wp-0.0 (made up) · curve: as of event; forecasts: as known before each span", bw - 110)

    top = 88
    # tree
    tw = 400
    bx, by, bw, bh = c.frame("tree", M, top, tw, 590)
    levels = [("game", "Home 78, Away 71", "138 possessions", ["Home vs Away"], 0),
              ("half", "2nd half, margin +5", "70 possessions", ["1st", "2nd"], 1),
              ("five-minute window", "10:00 to 5:00, margin +6", "18 possessions", ["20-15", "15-10", "10-5", "5-0"], 2),
              ("possession", "no. 71, Home, 16 s, 2 points", "3 actions", ["69", "70", "71", "72", "73"], 2),
              ("player", "#44, ball screen, value +0.12", "1 of 5 on the floor", ["#1", "#3", "#11", "#22", "#44"], 4)]
    for i, (name, head, count, sibs, cur) in enumerate(levels):
        yy = by + 6 + 112 * i
        ind = 14 * i
        c.rect(bx + ind, yy, bw - ind, 100, fill="bg.page", stroke="mark.region", rx=6)
        c.text(bx + ind + 10, yy + 18, name, 180, fill="text.secondary")
        c.text(bx + bw - 10, yy + 18, count, 150, fill="text.secondary", anchor="end")
        c.text(bx + ind + 10, yy + 44, head, bw - ind - 20, size=p.sizes["body_px"], bold=True)
        x = bx + ind + 10
        for j, s in enumerate(sibs):
            x += c.chip(x, yy + 76, s, active=j == cur)
        if i:
            c.line(bx + ind - 7, yy - 12, bx + ind - 7, yy + 50, opacity=0.7)
            c.line(bx + ind - 7, yy + 50, bx + ind, yy + 50, opacity=0.7)

    # wp curve
    gx = M + tw + 8
    gw = W - M - gx - 238
    bx, by, bw, bh = c.frame("wp_curve", gx, top, gw, 300)
    px0, pw, py0, ph = bx + 40, bw - 50, by + 12, bh - 66
    pts = [(0, 0.62), (3, 0.60), (6, 0.52), (9, 0.47), (12, 0.44), (15, 0.50), (18, 0.55), (20, 0.57), (23, 0.54), (26, 0.61), (29, 0.58),
           (32, 0.68), (35, 0.74), (37, 0.81), (39, 0.93), (40, 1.0)]
    for a, b in ((9, 13), (31, 36)):     # runs, rule K05
        c.rect(px0 + pw * a / 40, py0, pw * (b - a) / 40, ph, fill="mark.region", opacity=0.18)
    c.rect(px0 + pw * 30 / 40, py0, pw * 5 / 40, ph, stroke="text.link", sw=1.5, dash="4 3")
    P = band_line(c, pts, 0.07, "team.home", px0, py0, pw, ph, 0, 1, 40)
    c.line(px0, P(0, 0.5)[1], px0 + pw, P(0, 0.5)[1], opacity=0.5, dash="2 4")
    c.line(px0 + pw / 2, py0, px0 + pw / 2, py0 + ph, opacity=0.6)
    for v in (0, 0.5, 1):
        c.text(px0 - 6, P(0, v)[1] + 4, f"{int(v * 100)} %", 40, fill="text.on_chart_secondary", anchor="end")
    for t, s in ((0, "20:00"), (20, "half"), (40, "0:00")):
        c.text(px0 + pw * t / 40, py0 + ph + 16, s, 60, fill="text.on_chart_secondary", anchor="middle" if t == 20 else "start" if t == 0 else "end")
    c.text(px0, py0 + ph + 34, "Home win probability, band 95 %, model wp-0.0 (made up)", pw, fill="text.on_chart_secondary")
    c.text(px0, py0 + ph + 50, "shaded: runs (rule K05) · dashed box: the chosen window · line at half-time", pw, fill="text.on_chart_secondary")
    # half_and_windows
    bx, by, bw, bh = c.frame("half_and_windows", gx, top + 308, gw, 166)
    px0, pw = bx + 40, bw - 50
    vals = [0.55, 0.48, 0.52, 0.56, 0.50, 0.57, 0.66, 0.71]
    marg = ["+2", "-6", "+1", "+3", "-2", "+1", "+6", "+2"]
    for i, (v, mg) in enumerate(zip(vals, marg)):
        x0 = px0 + pw * i / 8 + 4
        bwid = pw / 8 - 8
        hh = 60 * v
        c.rect(x0, by + 78 - hh, bwid, hh, fill="team.home", opacity=0.75 if i != 6 else 1.0, rx=2)
        c.line(x0 + bwid / 2, by + 78 - hh - 7, x0 + bwid / 2, by + 78 - hh + 7, stroke="text.on_chart", sw=6, opacity=0.35)
        c.text(x0 + bwid / 2, by + 96, mg, bwid, fill="text.on_chart", anchor="middle")
    c.text(px0, by + 116, "per window (halves not drawn): chance that Home wins it, as known before it, with band", pw, fill="text.on_chart_secondary")
    c.text(px0, by + 132, "number under a bar: the margin the window had (official)", pw, fill="text.on_chart_secondary")
    # leverage strip
    bx, by, bw, bh = c.frame("leverage_strip", gx, top + 482, gw, 108)
    px0, pw = bx + 40, bw - 50
    for i in range(69):
        lev = 0.15 + 0.5 * abs(math.sin(i * 0.37)) * (0.4 + i / 69)
        c.rect(px0 + pw * i / 69, by + 52 - 46 * lev, pw / 69 - 1.5, 46 * lev, fill="seq:3", opacity=0.9)
    c.text(px0, by + 72, "leverage of each possession: how far apart a score and a stop put the win probability", pw, fill="text.on_chart_secondary")

    # right column: game flow, inspector
    rx_ = W - M - 230
    bx, by, bw, bh = c.frame("game_flow", rx_, top, 230, 196)
    for i, s in enumerate(("lead changes 7 · ties 4", "largest lead: Home 11, Away 6", "Home led 61 % of the game", "mean win probability 58 %", "official, play-by-play v4")):
        c.text(bx, by + 12 + 22 * i, s, bw, fill="text.primary" if i < 4 else "text.secondary")
    bx, by, bw, bh = c.frame("inspector", rx_, top + 204, 230, 386)
    for i, (k, v) in enumerate((("what", "window 10:00 to 5:00"), ("forecast", "66 %, band 55 to 77"), ("model", "wp-0.0 (made up)"), ("inputs", "score, clock, ratings"),
                                ("as of", "known at 10:00 (2nd)"), ("realised", "margin +6 (official)"), ("lineage", "run r-0042"))):
        c.text(bx, by + 12 + 48 * i, k, bw, fill="text.secondary")
        c.text(bx, by + 30 + 48 * i, v, bw)

    # swing plays
    bx, by, bw, bh = c.frame("swing_plays", M, top + 598, W - 2 * M, 156)
    c.rows(bx, by + 10, bw, [("clock", 2, "start"), ("score", 2, "start"), ("who", 3, "start"), ("what", 6, "start"), ("change", 3, "end"), ("band", 4, "end"), ("clip", 4, "start")],
           [["2nd 2:41", "70-68", "#1", "made three, right wing", "+9 %", "+6 to +12", "   clip 71-a"], ["2nd 4:58", "66-63", "#44", "block, then run-out", "+7 %", "+4 to +10", "   clip 66-c"],
            ["1st 8:12", "21-25", "#5 (Away)", "steal and lay-up", "-6 %", "-9 to -3", "   clip 24-b"], ["2nd 1:03", "74-71", "#3", "2 free throws made", "+6 %", "+3 to +9", "   clip 75-a"],
            ["1st 3:30", "30-33", "#12 (Away)", "made three, top", "-5 %", "-8 to -2", "   clip 33-a"]])
    c.footer(top + 598 + 156)
    return c


# --------------------------------------------------------------------------------------------------------------------
# VW-STU-07 review item
def review_item(p):
    view = "review_item"
    rec = p.rec(view)
    W, M = rec["min_width_px"], 16
    c = Canvas(p, view, W, 0)
    coarse = [v for v in vwlib._yaml(vwlib.SCHEMA_DIR / "screens.yaml")["columns"]["coverage_coarse"]["type"][5:-1].split(", ") if v != "unknown"]
    fine = p.core["display_contract"]["numbers"]["params"]["coverage_fine_min_conf"]["value"]
    c.header(f"a screen item with the guess prefilled, drawn at {W} px")
    bx, by, bw, bh = c.frame("as_of_banner", M, 50, W - 2 * M, 30)
    c.text(bx + 110, by - 6, "item 14 of 60 · label type: ball screen · Home vs Away, 2nd 7:49 · labeller: owner · guide version 0.3 · file 29.97 frames per second", bw - 110)
    top = 88
    vw = 520
    bx, by, bw, bh = c.frame("clip", M, top, vw, 330)
    video_box(c, bx, by, bw, bh - 30)
    x = bx
    for s, act in (("window: 4 s before, 3 s after", True), ("replay +11 s, baseline camera", False), ("extend", False)):
        x += c.chip(x, by + bh - 8, s, on_chart=True, active=act)
    cx, cw = M + vw + 8, 300
    ct = Court(c, cx + 8, 0, cw - 16)
    bx, by, bw, bh = c.frame("court", cx, top, cw, 330)
    ct.y = by + 4
    ct.draw()
    draw_ten(ct, offscreen=False)
    sx_, sy_ = ct.px(-1.83, 4.19)
    c.circle(sx_, sy_, 20, stroke="mark.attention", sw=2)
    c.text(bx, by + ct.h + 22, "ringed: the screen of this item", bw, fill="text.on_chart_secondary")
    # right column: guess, answer bar, re-show note
    gx = cx + cw + 8
    gw = W - M - gx
    bx, by, bw, bh = c.frame("guess_panel", gx, top, gw, 116)
    c.text(bx, by + 14, "system guess", bw, fill="text.secondary")
    c.text(bx, by + 40, "ball screen · coverage: containment", bw, size=p.sizes["body_px"], bold=True)
    c.text(bx, by + 60, "confidence 0.62 · model sc-0.2 · rule set 0.2", bw)
    c.text(bx, by + 80, f"raised by: confidence under {fine} (coarse class only) · rules disagree", bw, fill="text.attention")
    bx, by, bw, bh = c.frame("answer_bar", gx, top + 124, gw, 134)
    x = bx
    for s, act in (("enter  confirm", True), ("x  not this", False), ("u  cannot tell", False), ("not visible", False)):
        x += c.chip(x, by + 14, s, active=act)
    x = bx
    for i, name in enumerate(coarse, 1):      # the coarse classes of schema/tables/screens.yaml, three to a row
        if i == 4:
            x = bx
        x += c.chip(x, by + (42 if i < 4 else 68), f"{i} {name.replace('_', ' ')}")
    c.label(bx, by + 94, "reasons: late read · blocked view · two screens · undo: z", bw)
    bx, by, bw, bh = c.frame("blind_reshow", gx, top + 266, gw, 64)
    c.text(bx, by + 12, "a re-show looks like any item: guess and earlier labels hidden", bw, fill="text.secondary")
    c.text(bx, by + 30, "after the answer: the earlier answer and same or different", bw, fill="text.secondary")

    # variants
    vy = top + 338
    names = ["variant_turnover", "variant_screen", "variant_identity", "variant_scoreboard"]
    tabw = (W - 2 * M - 24) / 4
    for i, key in enumerate(names):
        active = key == "variant_screen"
        el = p.el(view, key)
        bx, by, bw, bh = c.frame(key, M + (tabw + 8) * i, vy, tabw, 222 if active else 62)
        if active:
            c.rect(M + (tabw + 8) * i, vy, tabw, 222, stroke="text.link", sw=2, rx=6)
            c.rows(bx, by + 12, bw, [("field", 4, "start"), ("value", 6, "start")],
                   [["moment", "2nd 7:49, frame 131 004"], ["kind", "ball screen"], ["screener, user", "#44 for #1"], ["strict rule", "no"], ["loose rule", "yes"],
                    ["contact distance", "0.6 m"], ["screener speed", "0.4 m/s"], ["duration", "0.9 s"], ["coverage guess", "containment, 0.62"]])
        else:
            words = {"variant_turnover": "official record beside the video", "variant_identity": f"locked or HOLD, candidates · from {el.get('phase')}",
                     "variant_scoreboard": f"bug, play-by-play, camera · from {el.get('phase')}"}[key]
            c.text(bx, by + 12, words, bw, fill="text.secondary")
    # appearance card, label history, inspector (beside the active variant)
    ry = vy + 70
    bx, by, bw, bh = c.frame("appearance_card", M, ry, tabw, 152)
    c.rows(bx, by + 12, bw, [("candidate", 4, "start"), ("kit", 6, "start")], [["#2", "white, low shoes, sleeve"], ["#15", "white, headband, tape"]])
    c.label(bx, by + 86, "no face image, by rule", bw)
    c.label(bx, by + 104, "shown on identity items", bw)
    lx = M + (tabw + 8) * 2
    bx, by, bw, bh = c.frame("label_history", lx, ry, tabw, 152)
    c.rows(bx, by + 12, bw, [("who", 4, "start"), ("label", 4, "start"), ("gold", 2, "end")], [["model sc-0.2", "containment", "no"], ["Claude", "containment", "no"], ["owner", "–", "–"]])
    c.label(bx, by + 104, "gold only after the owner confirms", bw)
    bx, by, bw, bh = c.frame("inspector", lx + tabw + 8, ry, tabw, 152)
    for i, s in enumerate(("selected: track of #44", "identity locked, 0.99", "source: tracking, run r-0042", "tool 0.4 · model sc-0.2", "lineage: 3 inputs")):
        c.text(bx, by + 12 + 20 * i, s, bw, fill="text.primary" if i < 2 else "text.secondary")
    c.footer(ry + 152)
    return c


# --------------------------------------------------------------------------------------------------------------------
# VW-CARD-01 player card
def player_card(p):
    view = "player_card"
    rec = p.rec(view)
    W, M = rec["min_width_px"], 12
    IW = W - 2 * M
    lvl = int(p.core["display_contract"]["numbers"]["params"]["interval_level_shooting"]["value"] * 100)
    min_n = p.core["display_contract"]["numbers"]["params"]["min_n_default"]["value"]
    c = Canvas(p, view, W, 0)
    c.header(f"frozen at a snapshot, drawn at {W} px")
    y = 50
    bx, by, bw, bh = c.frame("as_of_banner", M, y, IW, 62)
    c.text(bx, by + 12, "FROZEN · as known 14 Feb, 18:00", bw, bold=True)
    c.text(bx, by + 30, "last game included: game 24 · box as of 13 Feb", bw, fill="text.secondary")
    y += 70
    bx, by, bw, bh = c.frame("identity_block", M, y, IW, 104, grade="confirmed")
    c.rect(bx, by + 4, 56, 56, fill="team.home", rx=6)
    c.text(bx + 28, by + 42, "3", 50, size=p.sizes["hero_px"], fill="text.on_team_home", anchor="middle", bold=True)
    c.text(bx + 68, by + 16, "Player 1", bw - 68, size=p.sizes["value_px"], bold=True)
    c.text(bx + 68, by + 36, "guard · junior · right hand", bw - 68)
    c.text(bx + 68, by + 54, "1.93 m, 88 kg (listed, roster page)", bw - 68, fill="text.secondary")
    c.text(bx, by + 76, "no photo: a player is shown by name and number", bw, fill="text.stale")
    y += 112

    def table(key, h, cols, rows, notes=(), grade=None):
        bx, by, bw, bh = c.frame(key, M, y, IW, h, grade=grade)
        yy = c.rows(bx, by + 12, bw, cols, rows)
        for i, s in enumerate(notes):
            c.label(bx, yy + 2 + 18 * i, s, bw)

    table("role_and_usage", 130, [("", 5, "start"), ("value", 3, "end"), ("n", 3, "end")],
          [["games, starts", "24, 22", "official"], ["minutes share", "71 %", "24 g"], ["usage", "23 %", "1 310 poss"], ["rank in rotation", "2", "24 g"]])
    y += 138
    table("production", 166, [("per 100 poss.", 5, "start"), ("value", 2, "end"), ("95 %", 4, "end")],
          [["points", "24.1", "21.0 to 27.2"], ["true shooting", "58 %", "54 to 62"], ["assists", "6.3", "4.9 to 7.7"], ["turnovers", "3.1", "2.2 to 4.0"], ["on-off", "+4.2", "-1.1 to +9.5"]],
          notes=["n = 1 310 possessions on the floor"])
    y += 174
    bx, by, bw, bh = c.frame("tendencies", M, y, IW, 148)
    yy = c.rows(bx, by + 12, bw, [("tendency", 5, "start"), ("value", 2, "end"), ("n", 2, "end"), ("95 %", 3, "end")],
                [["drives left", "62 %", "87", "52 to 71"], ["pull-up after pick", "41 %", "64", "30 to 53"],
                 {"cells": ["finishing hand", "too few", "12", "–"], "fill": "text.stale"}, ["first action: shot", "38 %", "210", "32 to 45"]])
    c.label(bx, yy + 2, f"\"too few\": under {min_n} cases (K12), not drawn on a scale", bw)
    y += 156

    # spot_shooting_map
    ct = Court(c, M + 8, 0, IW - 16)
    bx, by, bw, bh = c.frame("spot_shooting_map", M, y, IW, ct.h + 100)
    ct.y = by + 4
    ct.draw()
    spots = [("corner_high", 1, 41, 39), ("corner_high", -1, 33, 31), ("wing_mid", 1, 44, 52), ("wing_mid", -1, 36, 47), ("elbow", 1, 47, 41),
             ("elbow", -1, None, 4), ("mr_top", 1, 52, 33), ("low_post", 1, 61, 58), ("slot_lane_line", -1, 38, 36)]
    for sid, side, rate, cnt in spots:     # (named-spots id, +1 right or -1 left, made-up rate in %, made-up n)
        a = p.anchor[sid]                  # the place comes from config/named_spots.yaml
        sx_, sy_ = ct.px(side * a["x"], a["y"])
        if rate is None:
            c.circle(sx_, sy_, 13, fill="bg.chart", stroke="mark.no_data", sw=1.5)
            c.hatch(sx_ - 9, sy_ - 9, 18, 18)
            c.text(sx_, sy_ + 28, f"n {cnt}", 40, fill="text.on_chart_stale", anchor="middle")
        else:
            stop = min(4, max(0, int((rate - 30) / 7)))
            c.circle(sx_, sy_, 13, fill=f"seq:{stop}", stroke="text.on_chart", sw=1)
            c.rect(sx_ - 13, sy_ + 16, 26, 15, fill="bg.chart", opacity=0.85, rx=3)
            c.text(sx_, sy_ + 28, str(rate), 26, fill="text.on_chart", anchor="middle", bold=True)
    c.text(bx, by + ct.h + 22, f"shrunk make rate in % at the named spots", bw, fill="text.on_chart_secondary")
    c.text(bx, by + ct.h + 40, f"corner, right: 16 of 39 · 41 %, {lvl} % interval 34 to 48", bw, fill="text.on_chart")
    c.text(bx, by + ct.h + 58, f"hatched: too few (n under {min_n}) · dark = low, bright = high", bw, fill="text.on_chart_stale")
    y += ct.h + 108

    el = p.el(view, "defense_block")
    table("defense_block", 112, [("", 5, "start"), ("value", 3, "end"), ("95 %", 3, "end")],
          [["steal rate", "2.4 %", "1.7 to 3.1"], ["block rate", "0.9 %", "0.4 to 1.4"], {"cells": ["rim defence", "–", f"from {el['phase']}"], "fill": "text.stale"}])
    y += 120
    bx, by, bw, bh = c.frame("availability_line", M, y, IW, 66, grade="observed")
    c.text(bx, by + 12, "available", bw, size=p.sizes["body_px"], bold=True)
    c.text(bx, by + 30, "as of 14 Feb, 17:30 · public report · health never inferred", bw, fill="text.secondary")
    y += 74
    bx, by, bw, bh = c.frame("background", M, y, IW, 66, grade="unknown")
    x2 = c.label(bx, by + 12, "recruiting rank", bw)
    c.value(bx + x2 + 8, by + 13, "", bw - x2 - 8, grade="unknown", size=p.sizes["body_px"], reason="not public")
    c.label(bx, by + 30, "never a model input", bw)
    y += 74
    bx, by, bw, bh = c.frame("inspector", M, y, IW, 66)
    c.text(bx, by + 12, "tap a number: metric id, n, prior, shrinkage,", bw, fill="text.secondary")
    c.text(bx, by + 30, "interval and the rows behind it", bw, fill="text.secondary")
    y += 74
    c.footer(y)
    return c


# --------------------------------------------------------------------------------------------------------------------
# the legend of rule 1: grade to appearance
def grade_legend(p):
    view = "live_game_state_panel"   # the legend belongs to the contract; the canvas only needs a view for its title
    W = 760
    rowh = 74
    grades = list(p.app)
    c = Canvas(p, view, W, 44 + rowh * len(grades) + 26, title="Display contract, rule 1: grade to appearance")
    c.text(12, 22, "Display contract, rule 1: grade to appearance (one mapping for all views)", W - 24, size=p.sizes["body_px"], bold=True)
    for i, (g, a) in enumerate(p.app.items()):
        y = 36 + rowh * i
        c.text(12, y + 38, g, 100, size=p.sizes["body_px"], bold=True)
        c.rect(120, y + 6, 190, 58, fill="bg.panel", stroke="mark.region", dash=EDGE_DASH[a["tile_edge"]], rx=6)
        if a["tile_edge"] == "hatched":
            c.hatch(120, y + 6, 190, 58, rx=6)
        c.value(130, y + 44, "7:42", 172, grade=g, age_s=12, reason="bug away 40 s")
        c.rect(322, y + 6, 76, 58, fill="bg.chart", rx=6)
        m = a["court_marker"]
        if m.startswith("hollow"):
            c.ellipse(360, y + 35, 30, 20, stroke="mark.region", dash="3 3")
            c.circle(360, y + 35, 10, stroke="team.home", sw=1.5)
        elif m.startswith("filled with a ring"):
            c.circle(360, y + 35, 14, stroke="mark.region", sw=1.5)
            c.circle(360, y + 35, 10, fill="team.home")
            c.text(360, y + 39, "3", 20, fill="text.on_team_home", anchor="middle", bold=True)
        elif m.startswith("filled"):
            c.circle(360, y + 35, 10, fill="team.home")
            c.text(360, y + 39, "3", 20, fill="text.on_team_home", anchor="middle", bold=True)
        else:
            c.text(360, y + 39, "not drawn", 72, fill="text.on_chart_stale", anchor="middle")
        for j, line in enumerate(wrap(a["in_words"], c.cap, W - 422)[:4]):
            c.text(410, y + 18 + 15 * j, line, W - 420, fill="text.secondary")
    c.text(12, c.h - 10, "Columns: grade, a tile value, a court marker, the rule in words. Generated from config/views/core.yaml.", W - 24, fill="text.stale")
    return c


WIREFRAMES = {
    "live_panel_d0.svg": lambda p: live_panel(p, "D0_full"),
    "live_panel_d1.svg": lambda p: live_panel(p, "D1_bug_away"),
    "live_panel_d3.svg": lambda p: live_panel(p, "D3_replay"),
    "possession_explorer.svg": possession_explorer,
    "studio_game_canvas.svg": studio_game_canvas,
    "layered_tree.svg": layered_tree,
    "review_item.svg": review_item,
    "player_card.svg": player_card,
    "grade_legend.svg": grade_legend,
}
LEGENDS = ("grade_legend.svg",)   # drawings of the contract, not of one view


def named_by_records(views):
    """{file name: (view key, level or None)} for every wireframe a record names."""
    out = {}
    for key, rec in views.items():
        if rec.get("wireframe"):
            out[Path(rec["wireframe"]).name] = (key, None)
        for lv, path in (rec.get("wireframe_states") or {}).items():
            out[Path(path).name] = (key, lv)
    return out


def build(theme="dark"):
    """-> {file name: svg text}. Fails when a record names a wireframe this file does not draw, or the reverse."""
    p = Pack(theme)
    named = named_by_records(p.views)
    drawn = set(WIREFRAMES) - set(LEGENDS)
    if set(named) != drawn:
        raise SystemExit(f"records and generator disagree: only in the records {sorted(set(named) - drawn)}, only drawn {sorted(drawn - set(named))}")
    out = {}
    for name, fn in WIREFRAMES.items():
        c = fn(p)
        if name in named and c.view != named[name][0]:
            raise SystemExit(f"{name}: drawn for {c.view}, named by {named[name][0]}")
        out[name] = c.svg()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default=str(OUT_DIR))
    ap.add_argument("--theme", default="dark", choices=["dark", "light"])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--draft", action="store_true", help="while drawing: write the files anyway and list every text that does not fit")
    a = ap.parse_args()
    Canvas.draft = a.draft and not a.check
    try:
        files = build(a.theme)
    except Overflow as e:
        print("FAIL", e)
        sys.exit(1)
    out = Path(a.out_dir)
    if a.check:
        bad = [name for name, text in files.items() if not (out / name).exists() or (out / name).read_text() != text]
        stray = sorted(f.name for f in out.glob("*.svg") if f.name not in files)
        if bad or stray:
            print(f"{out}: out of date {bad}, not generated {stray}: run python tools/specgen/views/gen_wireframes.py")
            sys.exit(1)
        return
    out.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (out / name).write_text(text)
    for msg in Canvas.problems:
        print("DRAFT", msg)
    print(f"wrote {len(files)} files to {out}" + (f" ({len(Canvas.problems)} texts do not fit: a draft, not a wireframe)" if Canvas.problems else ""))
    sys.exit(1 if Canvas.problems else 0)


if __name__ == "__main__":
    main()
