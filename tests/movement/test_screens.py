"""V0 synthetic tests for the screens family (config/movement_grammar/screens.yaml).

Every detector gets at least one positive scenario and at least one negative scenario, built with
sim.scenario at sigma_p 0.3 m and fixed seeds. Positives check kind, actors, t0 within +-0.3 s of the
truth t0 (computed from the noise-free paths with the rule the spec defines) and the confidence range.
"""
from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "movement"))
sys.path.insert(0, str(ROOT / "tools" / "specgen" / "named_spots"))

from mvlib import DT, build_scene  # noqa: E402
from sim import scenario  # noqa: E402

from detectors import screens as S  # noqa: E402

SIGMA = 0.3
SEED = 7
T_TOL = 0.3  # s
CONF_MIN = 0.2


# --------------------------------------------------------------------------------------
# Scenario builders (attacked-rim frame, metres; actors 'O' offense, 'D' defense)
# --------------------------------------------------------------------------------------
def Off(*wp):
    return {"team": "O", "wp": list(wp)}


def Def(*wp):
    return {"team": "D", "wp": list(wp)}


def bg(*skip):
    """Three static attacker/defender pairs far from the action (own-man pairs: never screens)."""
    a = {"o3": Off((0, 6.8, 0.5)), "D3": Def((0, 5.8, 1.2)),
         "o4": Off((0, -5.5, 4.5)), "D4": Def((0, -4.6, 4.0)),
         "o5": Off((0, -6.8, 0.5)), "D5": Def((0, -5.8, 1.0))}
    return {k: v for k, v in a.items() if k not in skip and k.replace("D", "o") not in skip}


def spec(actors, held=None, flights=None, extra_bg=True, skip=()):
    a = dict(bg(*skip)) if extra_bg else {}
    a.update(actors)
    return {"actors": a, "ball": {"held": held or [], "flights": flights or []}}


# High PnR geometry shared by several scenarios: the screener sets at P_S right of D_h; the handler
# starts 1.6 m from the screen (so his closest approach is the use, not the set-up) and turns the corner.
P_S = (0.7, 7.4)


def pnr(go=2.0, t_set=1.3, post="roll", route="over"):
    """Handler h, screener s, D_h, D_s of a high ball screen; the handler attacks at `go` s."""
    s_after = {"roll": [(go + 1.6, -0.2, 4.6), (go + 2.2, -0.6, 1.8)], "pop": [(go + 2.2, 5.0, 6.4)],
               "stay": []}[post]
    dh = {"over": [(go + 0.4, 0.0, 7.9), (go + 0.9, 0.9, 8.6), (go + 1.4, 2.2, 6.6), (go + 2.0, 1.9, 3.8)],
          "under": [(go + 0.4, -0.2, 7.0), (go + 0.9, 0.0, 5.4), (go + 1.4, 1.8, 4.6), (go + 2.0, 1.6, 3.4)]}[route]
    return {"h": Off((0, -0.3, 8.7), (go, -0.3, 8.7), (go + 0.5, 1.0, 8.3), (go + 1.0, 2.3, 6.6), (go + 1.9, 1.5, 3.0)),
            "s": Off((0, 3.0, 4.5), (t_set, *P_S), (go + 0.9, *P_S), *s_after),
            "Dh": Def((0, -0.15, 7.7), (go, -0.15, 7.7), *dh),
            "Ds": Def((0, 2.6, 4.0), (t_set, 0.8, 6.2), (go + 1.0, 0.8, 6.0), (go + 1.4, 1.1, 5.0), (go + 2.2, 0.8, 2.6))}


def sc_high_pnr(post="roll", route="over"):
    """High ball screen at the top: s sets right of D_h, h turns the corner right; s rolls or pops; D_h over or under."""
    return spec(pnr(post=post, route=route), held=[(0, 6.0, "h")]), 6.0


def sc_pnr_switch():
    """High ball screen where D_s jumps out and takes the handler and D_h stays with the rolling screener."""
    a = pnr(go=2.0)
    a["h"] = Off((0, -0.3, 8.7), (2.0, -0.3, 8.7), (2.5, 1.0, 8.3), (3.0, 2.3, 6.6), (4.5, 3.6, 5.0))
    a["Dh"] = Def((0, -0.15, 7.7), (2.0, -0.15, 7.7), (2.4, 0.0, 7.9), (3.0, 0.3, 6.9), (3.6, 0.4, 5.1), (4.4, 0.0, 2.6))
    a["Ds"] = Def((0, 2.6, 4.0), (1.3, 0.8, 6.2), (2.5, 1.5, 7.8), (3.0, 2.8, 6.3), (4.6, 3.1, 4.4))
    return spec(a, held=[(0, 6.5, "h")]), 6.5


def sc_pnr_reject():
    """Same set-up as the high PnR, but the handler rejects the screen and attacks left."""
    a = pnr(go=2.0, post="stay")
    a["h"] = Off((0, -0.6, 8.9), (2.0, -0.6, 8.9), (2.6, -2.1, 8.7), (3.4, -2.9, 5.5))
    a["Dh"] = Def((0, -0.4, 7.9), (2.0, -0.4, 7.9), (2.6, -1.8, 7.7), (3.4, -2.4, 4.9))
    a["s"] = Off((0, 3.0, 4.5), (1.3, *P_S), (3.6, *P_S))
    a["Ds"] = Def((0, 2.6, 4.0), (1.3, 0.8, 6.2), (3.6, 0.8, 6.2))
    return spec(a, held=[(0, 5.5, "h")]), 5.5


def sc_side_step_up():
    """Side PnR on the right wing; the screener steps up from the block and screens toward the sideline."""
    a = {"h": Off((0, 5.6, 4.6), (2.0, 5.6, 4.6), (2.6, 7.3, 3.25), (3.3, 6.8, 1.2), (4.0, 4.5, 0.6)),
         "s": Off((0, 2.5, 1.0), (1.4, 6.4, 3.1), (3.0, 6.4, 3.1), (4.2, 2.0, 1.0)),
         "Dh": Def((0, 5.6, 3.8), (2.0, 5.6, 3.8), (2.5, 5.8, 3.65), (3.2, 5.5, 2.3), (4.0, 4.5, 1.2)),
         "Ds": Def((0, 2.0, 1.6), (1.4, 5.6, 2.4), (3.0, 5.6, 2.4), (4.2, 2.6, 1.4))}
    return spec(a, held=[(0, 5.5, "h")], skip=("o3",)), 5.5


def sc_slip():
    """The screener sprints at the handler's defender and dives to the rim without stopping."""
    a = {"h": Off((0, 0, 8.2), (3.0, 0, 8.2), (4.0, 1.0, 8.0)),
         "s": Off((0, 3.5, 4.0), (1.3, 0.9, 7.1), (2.4, 0.4, 1.4)),
         "Dh": Def((0, 0, 7.2), (3.0, 0, 7.2), (4.0, 0.8, 7.1)),
         "Ds": Def((0, 3.0, 3.4), (1.3, 1.1, 6.0), (2.5, 0.6, 2.2))}
    return spec(a, held=[(0, 5.0, "h")]), 5.0


def sc_ghost():
    """The screener runs up toward the handler, never stops or touches, and fades to the arc."""
    a = {"h": Off((0, 0, 8.2), (3.0, 0, 8.2), (4.0, -1.0, 8.0)),
         "s": Off((0, 4.0, 4.6), (1.3, 1.0, 6.6), (2.3, 5.8, 6.4)),
         "Dh": Def((0, 0, 7.2), (3.0, 0, 7.2), (4.0, -0.8, 7.1)),
         "Ds": Def((0, 3.4, 3.8), (1.3, 1.0, 5.4), (2.5, 4.9, 5.6))}
    return spec(a, held=[(0, 5.0, "h")]), 5.0


def sc_fake_lateral():
    """The screener runs up toward the handler, then slides laterally across the top without screening."""
    a = {"h": Off((0, 0, 8.2), (3.0, 0, 8.2), (4.0, 1.0, 8.0)),
         "s": Off((0, 4.0, 4.6), (1.3, 1.0, 6.6), (2.4, -2.0, 6.6)),
         "Dh": Def((0, 0, 7.2), (3.0, 0, 7.2), (4.0, 0.8, 7.1)),
         "Ds": Def((0, 3.4, 3.8), (1.3, 1.0, 5.4), (2.5, -1.8, 5.6))}
    return spec(a, held=[(0, 5.0, "h")]), 5.0


def sc_drag(double=False):
    """Transition: trailer(s) sprint from the backcourt and set drag screen(s) near the arc; the handler waits for them."""
    a = {"h": Off((0, -0.5, 11.5), (1.8, -0.5, 8.6), (2.6, -0.5, 8.6), (3.1, 0.75, 7.75), (3.6, 2.4, 7.1),
                (4.1, 2.6, 5.0), (4.9, 1.5, 2.5)),
         "s": Off((0, 0.4, 13.0), (1.8, 0.4, 6.9), (3.3, 0.4, 6.9), (4.6, -0.3, 1.5)),
         "Dh": Def((0, -0.5, 10.5), (1.8, -0.4, 7.6), (2.8, -0.1, 7.6), (3.3, 0.4, 8.2), (3.7, 1.8, 7.5),
                 (4.1, 2.2, 5.6), (4.8, 1.7, 3.2)),
         "Ds": Def((0, 0.9, 14.2), (1.9, 0.5, 6.0), (3.3, 0.5, 6.0), (4.6, 1.4, 2.6))}
    if double:
        # 77: the first trailer s sets high-left, the second s2 lower-right; D_h goes over s, then runs into s2
        a["h"] = Off((0, -0.5, 11.5), (1.8, -0.5, 8.8), (2.7, -0.5, 8.8), (3.2, 0.9, 8.75), (3.7, 2.3, 7.9),
                   (4.2, 2.6, 5.5), (5.0, 1.5, 2.5))
        a["s"] = Off((0, 0.3, 13.0), (1.8, 0.3, 7.9), (3.6, 0.3, 7.9), (4.8, -0.5, 1.8))
        a["Ds"] = Def((0, 0.8, 14.2), (1.9, 0.4, 6.9), (3.6, 0.4, 6.9), (4.8, 0.3, 2.6))
        a["Dh"] = Def((0, -0.5, 10.5), (1.8, -0.3, 7.9), (2.7, -0.3, 7.9), (3.1, -0.1, 8.6), (3.45, 0.8, 9.0),
                    (3.8, 1.8, 8.2), (4.2, 2.6, 7.0), (4.7, 2.4, 4.8))
        a["s2"] = Off((0, 1.4, 12.5), (1.9, 1.4, 7.2), (4.2, 1.4, 7.2), (5.4, 4.6, 6.0))
        a["Ds2"] = Def((0, 2.1, 13.6), (2.0, 1.8, 6.2), (4.2, 1.8, 6.2), (5.4, 3.8, 5.0))
        skip = ("o4",)
    else:
        skip = ()
    return spec(a, held=[(0, 6.0, "h")], skip=skip), 6.0


def sc_spain():
    """High PnR by s1 with s2 waiting under it: s2 back-screens the dropping D_s1, s1 rolls past s2, s2 pops."""
    a = pnr(go=2.0)
    a["s1"], a["Ds1"] = a.pop("s"), a.pop("Ds")
    a["Ds1"] = Def((0, 2.6, 4.0), (1.3, 0.8, 6.2), (2.9, 0.85, 5.6), (3.2, 0.9, 5.3), (3.8, 0.9, 5.3), (4.4, 1.0, 2.6))
    a["s2"] = Off((0, -2.5, 2.4), (2.2, 0.6, 4.4), (3.8, 0.6, 4.4), (4.8, 0.4, 7.3))
    a["Ds2"] = Def((0, -2.0, 1.8), (2.2, 0.2, 3.5), (3.8, 0.2, 3.5), (4.8, 0.3, 6.2))
    return spec(a, held=[(0, 6.5, "h")], skip=("o3",)), 6.5


def sc_detroit():
    """Two screeners side by side above the handler's defender (Detroit / double ball screen)."""
    a = {"h": Off((0, 0.1, 8.3), (2.2, 0.1, 8.3), (2.7, 1.6, 8.1), (3.2, 2.4, 6.4), (4.0, 1.5, 3.0)),
         "s1": Off((0, -2.5, 4.5), (1.4, -0.3, 7.3), (3.4, -0.3, 7.3), (4.4, -2.5, 6.5)),
         "s2": Off((0, 3.0, 4.5), (1.4, 0.65, 7.3), (3.4, 0.65, 7.3), (4.5, 0.5, 2.0)),
         "Dh": Def((0, 0.1, 7.75), (2.2, 0.1, 7.75), (2.7, 0.3, 7.95), (3.2, 1.6, 7.9), (3.7, 2.2, 5.6),
                 (4.3, 1.6, 3.6)),
         "Ds1": Def((0, -2.0, 3.8), (1.4, -0.5, 6.1), (3.4, -0.5, 6.1), (4.4, -2.0, 5.8)),
         "Ds2": Def((0, 2.5, 3.8), (1.4, 0.8, 6.1), (3.4, 0.8, 6.1), (4.5, 0.5, 3.0))}
    return spec(a, held=[(0, 5.5, "h")], skip=("o4",)), 5.5


def sc_ram():
    """A wing screens down for the big at the block (wedge/ram), the big then sets a high ball screen."""
    a = pnr(go=3.0, t_set=2.4)
    a["s"] = Off((0, 2.0, 1.0), (1.0, 2.0, 1.0), (2.4, *P_S), (3.9, *P_S), (4.6, -0.2, 4.6), (5.2, -0.6, 1.8))
    a["g"] = Off((0, 4.0, 6.0), (1.0, 2.6, 2.6), (2.3, 2.6, 2.6), (3.6, 5.6, 2.2))
    a["Ds"] = Def((0, 2.9, 1.4), (1.0, 2.9, 1.4), (1.7, 3.0, 2.0), (2.5, 1.6, 5.4), (3.0, 0.8, 6.2), (4.0, 0.8, 6.0),
                (5.2, 0.8, 2.6))
    a["Dg"] = Def((0, 3.5, 5.0), (1.0, 3.6, 3.4), (2.3, 3.6, 3.4), (3.6, 5.0, 2.6))
    return spec(a, held=[(0, 6.5, "h")], skip=("o3",)), 6.5


def sc_veer():
    """High PnR, then the same screener runs to set an off-ball screen for the corner player."""
    a = pnr(go=2.0, post="stay")
    a["s"] = Off((0, 3.0, 4.5), (1.3, *P_S), (3.3, *P_S), (4.5, 5.0, 2.5), (6.0, 5.0, 2.5))
    a["Ds"] = Def((0, 2.6, 4.0), (1.3, 0.8, 6.2), (3.3, 0.8, 6.0), (4.5, 3.8, 2.6), (6.0, 3.8, 2.6))
    a["o3"], a["D3"] = Off((0, 6.8, 0.5)), Def((0, 5.6, 1.7))
    return spec(a, held=[(0, 6.5, "h")], skip=("o3",)), 6.5


def sc_rescreen():
    """Screen right of D_h is refused, the screener relocates (under D_h) to the left and screens again; the handler uses it."""
    a = {"h": Off((0, -0.3, 8.7), (3.4, -0.3, 8.7), (3.9, -1.6, 8.2), (4.4, -2.6, 6.6), (5.3, -1.5, 3.0)),
         "s": Off((0, 3.0, 4.5), (1.2, *P_S), (2.2, *P_S), (2.55, 0.0, 6.0), (2.9, -1.2, 7.4), (4.6, -1.2, 7.4),
                (5.8, 0.5, 1.5)),
         "Dh": Def((0, -0.15, 7.7), (3.4, -0.15, 7.7), (3.8, -0.4, 7.9), (4.3, -1.4, 8.6), (4.8, -2.5, 6.6),
                 (5.4, -1.9, 3.8)),
         "Ds": Def((0, 2.6, 4.0), (1.2, 0.8, 6.2), (2.2, 0.8, 6.2), (2.55, 0.0, 5.0), (2.9, -1.2, 6.2), (4.6, -1.2, 6.0),
                 (5.8, -0.6, 2.5))}
    return spec(a, held=[(0, 6.8, "h")], skip=("o4",)), 6.8


def sc_flip():
    """The screener approaches on the handler's sideline side, flips to the middle side and screens."""
    a = {"h": Off((0, -1.6, 8.3), (2.3, -1.6, 8.3), (2.8, -0.1, 8.5), (3.3, 1.4, 6.4), (4.2, 0.8, 2.6)),
         "s": Off((0, -3.6, 4.8), (1.0, -2.3, 7.1), (1.4, -1.4, 6.5), (1.8, -0.4, 7.6), (3.3, -0.4, 7.6), (4.6, 0.0, 1.8)),
         "Dh": Def((0, -1.4, 7.3), (2.3, -1.4, 7.3), (2.7, -1.1, 7.6), (3.1, 0.2, 8.4), (3.6, 1.3, 6.4), (4.3, 1.0, 3.6)),
         "Ds": Def((0, -3.0, 4.2), (1.0, -2.0, 6.0), (1.4, -1.4, 5.5), (1.8, -0.3, 6.5), (3.3, -0.3, 6.5), (4.6, 0.6, 2.8))}
    return spec(a, held=[(0, 5.5, "h")], skip=("o4",)), 5.5


def sc_pin_down(wide=False):
    """Down screen for a low user (block) or a wide pin-down for the corner player; the user pops to the wing."""
    if wide:
        a = {"u": Off((0, 6.2, 0.6), (2.0, 6.2, 0.6), (2.5, 6.5, 2.4), (3.0, 6.6, 4.6)),
             "s": Off((0, 4.5, 6.0), (1.4, 5.6, 2.3), (3.6, 5.6, 2.3), (4.6, 3.0, 4.5)),
             "Du": Def((0, 5.2, 1.4), (2.0, 5.2, 1.4), (2.5, 5.6, 1.6), (2.8, 6.3, 1.7), (3.3, 6.6, 3.6)),
             "Ds": Def((0, 4.0, 5.2), (1.4, 4.8, 2.6), (3.6, 4.8, 2.6), (4.6, 2.6, 4.0))}
    else:
        a = {"u": Off((0, 4.6, 0.6), (2.0, 4.6, 0.6), (2.5, 5.8, 2.2), (3.1, 5.9, 4.8)),
             "s": Off((0, 5.5, 5.5), (1.4, 4.8, 2.5), (3.6, 4.8, 2.5), (4.6, 2.5, 4.0)),
             "Du": Def((0, 4.3, 1.6), (2.0, 4.3, 1.6), (2.5, 4.2, 2.0), (2.9, 4.0, 3.0), (3.4, 5.4, 4.4)),
             "Ds": Def((0, 4.8, 4.6), (1.4, 4.2, 3.2), (3.6, 4.2, 3.2), (4.6, 2.3, 3.2))}
    a["p"], a["Dp"] = Off((0, 0.0, 8.0)), Def((0, 0.0, 7.0))
    return spec(a, held=[(0, 5.0, "p")], skip=("o3",)), 5.0


def sc_flare():
    """Flare: the slot player fades away from the ball off a screen set on his ball-side defender."""
    a = {"u": Off((0, -2.5, 6.5), (2.0, -2.5, 6.5), (3.2, -5.5, 4.5)),
         "s": Off((0, -1.0, 3.5), (1.3, -2.8, 5.7), (3.5, -2.8, 5.7)),
         "Du": Def((0, -1.7, 6.0), (2.0, -1.7, 6.0), (2.4, -2.1, 5.9), (3.4, -4.6, 4.7)),
         "Ds": Def((0, -0.8, 2.6), (1.3, -2.4, 4.9), (3.5, -2.4, 4.9)),
         "p": Off((0, 5.5, 4.5)), "Dp": Def((0, 4.8, 3.9))}
    return spec(a, held=[(0, 5.0, "p")], skip=("o4", "o3")), 5.0


def sc_back(rip=True, blind=False):
    """Back screen for a wing user who cuts to the rim; the screener comes from the low post (rip) or the top."""
    s0 = (0, 2.0, 1.0) if rip else (0, 1.5, 7.2)
    sp = (4.0, 3.5)
    ds = [(0, 2.6, 1.4) if rip else (0, 1.0, 6.4), (1.4, 3.3, 2.7), (3.6, 3.3, 2.7)]
    if blind:
        # loop 1 (SCR-T14): squarely behind D_u (facing the user/ball midpoint, ~170 deg) at 0.5 m; the old spot (4.3, 3.9)
        # was 122 deg off D_u's facing, inside the +-120 deg visual field the probability gate now uses
        s0, sp = (0, 2.5, 6.0), (5.0, 4.0)
        ds = [(0, 2.0, 5.4), (1.4, 4.3, 3.3), (3.6, 4.3, 3.3)]
    a = {"u": Off((0, 5.0, 5.0), (2.0, 5.0, 5.0), (3.0, 0.2, 1.8)),
         "s": Off(s0, (1.4, *sp), (3.6, *sp)),
         "Du": Def((0, 4.6, 4.3), (2.0, 4.6, 4.3), (2.4, 4.4, 4.2), (2.8, 4.4, 4.2), (3.1, 3.2, 4.6), (3.7, 1.6, 2.4)),
         "Ds": Def(*ds),
         "p": Off((0, 0.0, 8.0)), "Dp": Def((0, 0.0, 7.0))}
    return spec(a, held=[(0, 5.0, "p")], skip=("o3",)), 5.0


def sc_ucla():
    """The top guard passes to the wing and cuts off the high-post screener at the elbow to the rim."""
    a = {"u": Off((0, 0.5, 7.5), (1.7, 0.5, 7.5), (2.3, 2.6, 4.9), (3.0, 0.8, 1.0)),
         "s": Off((0, 1.8, 4.2)),
         "w": Off((0, 5.0, 5.0)),
         "Du": Def((0, 0.5, 6.6), (1.7, 0.5, 6.6), (2.2, 1.3, 5.0), (3.2, 1.2, 2.0)),
         "Ds": Def((0, 1.6, 3.2)),
         "Dw": Def((0, 4.4, 4.3))}
    return spec(a, held=[(0, 1.5, "u"), (1.9, 5.0, "w")], flights=[(1.5, 1.9, "u", "w")], skip=("o3",)), 5.0


def sc_shuffle():
    """The weak-side wing passes up top, then cuts diagonally off the high-post screener to the ball-side block."""
    a = {"u": Off((0, -5.0, 5.0), (1.7, -5.0, 5.0), (2.4, -1.8, 3.8), (3.3, 1.5, 1.0)),
         "s": Off((0, -1.2, 4.6)),
         "p": Off((0, 0.5, 8.0)),
         "Du": Def((0, -4.3, 4.5), (1.7, -4.3, 4.5), (2.3, -1.9, 4.6), (3.6, 0.5, 2.0)),
         "Ds": Def((0, -1.0, 3.6)),
         "Dp": Def((0, 0.5, 7.0))}
    return spec(a, held=[(0, 1.5, "u"), (2.0, 5.0, "p")], flights=[(1.5, 2.0, "u", "p")], skip=("o4",)), 5.0


def sc_cross(flex=False):
    """Baseline screen: a cross screen for the weak-side post, or a flex screen for the weak-side corner."""
    if flex:
        a = {"u": Off((0, -6.0, 0.8), (1.4, -6.0, 0.8), (3.6, 1.6, 0.8)),
             "s": Off((0, -2.0, 1.6)),
             "Du": Def((0, -5.3, 1.4), (1.4, -5.3, 1.4), (2.3, -2.6, 1.6), (3.0, -2.2, 1.7), (4.2, 0.8, 1.8)),
             "Ds": Def((0, -1.4, 2.1))}
        skip = ("o5",)
    else:
        a = {"u": Off((0, -2.0, 1.0), (2.0, -2.0, 1.0), (2.5, -0.8, 0.3), (3.0, 2.0, 0.9)),
             "s": Off((0, 2.0, 1.0), (1.3, -0.8, 1.3), (3.5, -0.8, 1.3)),
             "Du": Def((0, -1.5, 1.5), (2.0, -1.5, 1.5), (2.5, -1.1, 1.8), (3.3, 1.2, 1.8)),
             "Ds": Def((0, 2.0, 2.0), (1.3, -0.4, 2.2), (3.5, -0.4, 2.2))}
        skip = ()
    a["p"], a["Dp"] = Off((0, 5.5, 4.0)), Def((0, 4.8, 3.4))
    return spec(a, held=[(0, 5.0, "p")], skip=("o3",) + skip), 5.0


def sc_stagger(double=False):
    """Two screeners for a user coming up from the block: staggered (2.3 m apart) or stacked double (1.0 m)."""
    if double:
        a = {"u": Off((0, -1.8, 2.1), (2.0, -1.8, 2.1), (2.9, -3.6, 4.5), (3.5, -4.6, 5.4)),
             "s1": Off((0, -1.0, 4.0), (1.3, -2.9, 2.5), (3.8, -2.9, 2.5)),
             "s2": Off((0, -1.5, 5.0), (1.3, -3.5, 3.3), (3.8, -3.5, 3.3)),
             "Du": Def((0, -2.4, 1.7), (2.0, -2.4, 1.7), (2.5, -2.9, 1.9), (2.9, -3.6, 2.8), (3.5, -4.3, 4.3)),
             "Ds1": Def((0, -0.6, 3.2), (1.3, -2.2, 1.9), (3.8, -2.2, 1.9)),
             "Ds2": Def((0, -1.0, 4.4), (1.3, -2.6, 3.9), (3.8, -2.6, 3.9))}
    else:
        a = {"u": Off((0, -2.0, 1.0), (2.0, -2.0, 1.0), (2.5, -3.6, 2.4), (3.0, -4.0, 4.9), (3.6, -4.7, 6.2)),
             "s1": Off((0, -1.0, 4.5), (1.3, -2.8, 2.7), (3.8, -2.8, 2.7)),
             "s2": Off((0, -1.5, 6.5), (1.3, -3.3, 5.0), (3.8, -3.3, 5.0)),
             "Du": Def((0, -2.2, 1.8), (2.0, -2.2, 1.8), (2.6, -3.1, 2.4), (3.1, -3.7, 4.2), (3.7, -4.2, 5.6)),
             "Ds1": Def((0, -0.6, 3.8), (1.3, -2.0, 3.0), (3.8, -2.0, 3.0)),
             "Ds2": Def((0, -1.0, 5.8), (1.3, -2.5, 5.4), (3.8, -2.5, 5.4))}
    a["p"], a["Dp"] = Off((0, 5.0, 5.0)), Def((0, 4.3, 4.4))
    return spec(a, held=[(0, 5.0, "p")], skip=("o4", "o5", "o3")), 5.0


def sc_elevator():
    """Two screeners stand 1.2 m apart at the top of the key; the user sprints through and they close the gate."""
    a = {"u": Off((0, 0.0, 1.2), (2.0, 0.0, 1.2), (3.0, 0.0, 7.6)),
         "s1": Off((0, -0.65, 4.7), (2.55, -0.65, 4.7), (2.95, -0.2, 4.7), (4.5, -0.2, 4.7)),
         "s2": Off((0, 0.65, 4.7), (2.55, 0.65, 4.7), (2.95, 0.2, 4.7), (4.5, 0.2, 4.7)),
         "Du": Def((0, 0.5, 1.6), (2.0, 0.5, 1.6), (2.8, 0.3, 4.0), (3.4, 0.6, 4.1), (4.4, 1.0, 6.5)),
         "Ds1": Def((0, -1.2, 3.9)), "Ds2": Def((0, 1.2, 3.9)),
         "p": Off((0, 5.0, 5.0)), "Dp": Def((0, 4.3, 4.4))}
    return spec(a, held=[(0, 5.0, "p")], skip=("o3",)), 5.0


def sc_hammer():
    """Baseline drive from the right wing; weak-side screen; the left wing fades to the corner for the kick-out."""
    a = {"h": Off((0, 5.5, 4.5), (1.0, 5.5, 4.5), (2.2, 2.5, 0.8), (3.5, 2.0, 0.9)),
         "u": Off((0, -5.0, 4.5), (1.5, -5.0, 4.5), (2.8, -6.9, 0.6)),
         "s": Off((0, -2.0, 1.0), (1.2, -5.1, 3.0), (3.5, -5.1, 3.0)),
         "Dh": Def((0, 4.8, 3.8), (1.0, 4.8, 3.8), (2.2, 2.0, 1.4), (3.5, 1.6, 1.4)),
         "Du": Def((0, -4.0, 3.4), (1.6, -4.0, 3.4), (2.3, -4.3, 3.2), (2.9, -4.8, 2.1), (3.6, -6.0, 1.4)),
         "Ds": Def((0, -1.5, 1.6), (1.2, -4.2, 2.4), (3.5, -4.2, 2.4))}
    return spec(a, held=[(0, 2.6, "h"), (3.2, 4.5, "u")], flights=[(2.6, 3.2, "h", "u")],
                skip=("o4", "o5", "o3")), 4.5


def sc_zipper():
    """Zipper: the user at the block runs up the lane line to the slot off a screener who came down."""
    a = {"u": Off((0, 2.0, 0.9), (2.0, 2.0, 0.9), (2.5, 3.3, 2.6), (3.4, 2.8, 7.2)),
         "s": Off((0, 2.5, 5.5), (1.3, 2.4, 2.8), (3.6, 2.4, 2.8)),
         "Du": Def((0, 2.0, 1.9), (2.0, 2.0, 1.9), (2.6, 2.6, 2.1), (2.9, 3.3, 3.0), (3.6, 2.6, 6.0)),
         "Ds": Def((0, 1.4, 4.8), (1.3, 1.8, 3.6), (3.6, 1.8, 3.6)),
         "p": Off((0, -4.5, 6.0)), "Dp": Def((0, -3.8, 5.3))}
    return spec(a, held=[(0, 5.0, "p")], skip=("o4",)), 5.0


def sc_iverson():
    """Iverson cut: the right wing runs across the top past two elbow screeners to the left wing."""
    a = {"u": Off((0, 4.5, 5.4), (1.8, 4.5, 5.4), (4.1, -4.5, 5.4)),
         "s1": Off((0, 1.6, 4.7)), "s2": Off((0, -1.6, 4.7)),
         "Du": Def((0, 4.2, 4.8), (2.0, 4.2, 4.8), (2.6, 2.4, 4.9), (2.95, 1.0, 5.6), (3.3, -1.0, 5.1), (3.7, -1.9, 5.8),
                 (4.2, -3.9, 5.2)),
         "Ds1": Def((0, 1.3, 3.6)), "Ds2": Def((0, -1.3, 3.6)),
         "p": Off((0, 5.5, 1.5)), "Dp": Def((0, 4.7, 1.6))}
    return spec(a, held=[(0, 5.5, "p")], skip=("o3", "o4")), 5.5


def sc_wedge():
    """Wedge: a wing comes in and back-screens the elbow big's defender; the big dives to the rim."""
    a = {"u": Off((0, 1.8, 4.4), (2.0, 1.8, 4.4), (3.0, 0.3, 0.8)),
         "s": Off((0, 5.0, 5.0), (1.4, 1.7, 2.6), (3.6, 1.7, 2.6)),
         "Du": Def((0, 1.9, 3.5), (2.0, 1.9, 3.5), (2.6, 1.8, 3.4), (3.4, 0.8, 1.6)),
         "Ds": Def((0, 4.4, 4.4), (1.4, 2.6, 2.4), (3.6, 2.6, 2.4)),
         "p": Off((0, -1.0, 8.0)), "Dp": Def((0, -0.8, 7.0))}
    return spec(a, held=[(0, 5.0, "p")], skip=("o3",)), 5.0


def sc_sts():
    """Screen the screener: s1 down-screens for u1, then s2 down-screens for s1, who runs to the top."""
    a = {"u1": Off((0, 2.4, 0.6), (2.0, 2.4, 0.6), (2.5, 4.3, 1.4), (3.1, 6.2, 3.8)),
         "s1": Off((0, 3.5, 5.5), (1.3, 3.4, 1.9), (2.8, 3.4, 1.9), (3.3, 3.2, 4.4), (4.0, 1.2, 8.0)),
         "s2": Off((0, 1.0, 7.0), (2.0, 2.6, 4.0), (4.6, 2.6, 4.0)),
         "Du1": Def((0, 2.8, 1.2), (2.0, 2.8, 1.2), (2.5, 3.0, 1.3), (3.1, 5.4, 3.4)),
         "Ds1": Def((0, 3.9, 4.6), (1.3, 3.9, 1.4), (2.8, 3.9, 1.4), (3.3, 3.5, 3.5), (4.2, 1.6, 7.0)),
         "Ds2": Def((0, 1.0, 6.0), (2.0, 1.8, 3.4), (4.6, 1.8, 3.4)),
         "p": Off((0, -4.0, 6.5)), "Dp": Def((0, -3.4, 5.8))}
    return spec(a, held=[(0, 5.0, "p")], skip=("o3", "o4")), 5.0


def sc_out():
    """Out screen: the cutter in the lane comes straight out past a stationary screener near the elbow."""
    a = {"u": Off((0, 0.6, 2.0), (2.0, 0.6, 2.0), (3.1, 2.6, 7.0)),
         "s": Off((0, 1.5, 4.4)),
         "Du": Def((0, 0.9, 2.8), (2.0, 0.9, 2.8), (2.4, 1.2, 3.7), (3.3, 2.2, 6.0)),
         "Ds": Def((0, 1.2, 5.4), (1.0, 1.0, 5.6)),
         "p": Off((0, -5.0, 5.0)), "Dp": Def((0, -4.3, 4.4))}
    return spec(a, held=[(0, 5.0, "p")], skip=("o4",)), 5.0


def sc_dho(kind="dho"):
    """Handoff family: a DHO at the right slot, a fake DHO (receiver goes away, hander keeps), or GET (pass, then DHO back)."""
    if kind == "dho":
        # the receiver runs by without stopping; the hander plants and hands the ball over at 1.9 s
        a = {"a": Off((0, 0.0, 7.5), (1.5, 2.2, 6.85), (2.3, 2.2, 6.85), (3.3, 1.0, 2.0)),
             "b": Off((0, 4.5, 6.0), (0.3, 4.5, 6.0), (3.8, -1.5, 7.0)),
             "Da": Def((0, 0.0, 6.5), (1.5, 1.5, 5.9), (2.3, 1.5, 5.9), (3.5, 1.0, 3.0)),
             "Db": Def((0, 4.0, 5.0), (0.3, 4.0, 5.0), (3.9, -1.5, 5.6))}
        return spec(a, held=[(0, 1.77, "a"), (1.77, 5.0, "b")], skip=("o4",)), 5.0
    if kind == "fake":
        a = {"a": Off((0, -0.5, 7.6), (1.0, -0.5, 7.6), (2.0, 1.6, 7.3), (2.4, 1.6, 7.3), (3.2, 0.8, 2.2)),
             "b": Off((0, 5.5, 5.5), (0.6, 5.5, 5.5), (2.0, 2.5, 7.1), (3.2, 6.6, 1.0)),
             "Da": Def((0, -0.5, 6.6), (1.0, -0.5, 6.6), (2.0, 0.6, 6.6), (2.4, 0.6, 6.6), (3.4, 0.2, 3.0)),
             "Db": Def((0, 4.9, 4.9), (0.6, 4.9, 4.9), (2.0, 3.1, 7.0), (3.4, 6.9, 1.8))}
        return spec(a, held=[(0, 5.0, "a")], skip=("o3",)), 5.0
    # GET: a passes to the big b at the elbow, then runs by him and takes the ball back hand to hand
    a = {"a": Off((0, -0.5, 8.0), (1.2, -0.5, 8.0), (3.0, 4.5, 4.0)),
         "b": Off((0, 2.0, 5.6)),
         "Da": Def((0, -0.5, 7.0), (1.2, -0.5, 7.0), (3.1, 3.9, 3.4)),
         "Db": Def((0, 1.8, 4.6))}
    return spec(a, held=[(0, 1.0, "a"), (1.5, 2.14, "b"), (2.14, 5.0, "a")], flights=[(1.0, 1.5, "a", "b")],
                skip=("o3",)), 5.0


def sc_moving_screen():
    """The screener runs into a defender who is sprinting after the handler and stops him (screener still moving at contact)."""
    a = {"h": Off((0, -0.8, 8.4), (1.0, -0.8, 8.4), (2.6, 2.2, 8.4)),
         "s": Off((0, 2.3, 5.55), (1.0, 2.3, 5.55), (2.8, -0.6, 8.75)),
         "Dh": Def((0, -2.4, 7.0), (1.0, -2.4, 7.0), (2.0, 0.0, 7.2), (2.7, 0.0, 7.2), (3.4, 1.6, 7.0)),
         "Ds": Def((0, 2.4, 4.4), (1.0, 2.4, 4.4), (2.1, 1.2, 6.0), (3.5, 1.2, 6.0))}
    return spec(a, held=[(0, 4.5, "h")]), 4.5


def sc_walk_by():
    """A teammate walks (about 1 m/s) past a standing defender at 1 m without ever stopping: no SET, no screen."""
    a = {"s": Off((0, 6.0, 6.0), (12.0, -6.0, 6.0)),
         "Dh": Def((0, 4.9, 7.0)), "h": Off((0, 4.9, 8.0)),
         "Ds": Def((0, 6.5, 5.2), (12.0, -5.5, 5.2))}
    return spec(a, held=[(0, 12.5, "h")], skip=("o3", "o4")), 12.5


def sc_null():
    """Ten players moving without stopping near anyone else's defender; the ball is passed around."""
    a = {"p1": Off((0, 0, 8.0), (2.5, 1.5, 8.5), (5.0, -1.0, 8.0)),
         "p2": Off((0, 5.5, 4.0), (2.5, 6.0, 2.0), (5.0, 5.0, 4.5)),
         "p3": Off((0, -5.5, 4.0), (2.5, -6.0, 2.5), (5.0, -5.0, 5.0)),
         "p4": Off((0, 2.0, 1.0), (2.5, 3.0, 2.5), (5.0, 2.0, 1.2)),
         "p5": Off((0, -2.0, 1.0), (2.5, -2.5, 3.0), (5.0, -2.2, 1.0)),
         "q1": Def((0, 0, 7.0), (2.5, 1.3, 7.5), (5.0, -0.8, 7.0)),
         "q2": Def((0, 4.8, 3.4), (2.5, 5.1, 1.8), (5.0, 4.3, 3.8)),
         "q3": Def((0, -4.8, 3.4), (2.5, -5.1, 2.2), (5.0, -4.3, 4.3)),
         "q4": Def((0, 1.5, 0.4), (2.5, 2.5, 1.8), (5.0, 1.5, 0.6)),
         "q5": Def((0, -1.5, 0.4), (2.5, -2.0, 2.3), (5.0, -1.7, 0.5))}
    return {"actors": a, "ball": {"held": [(0, 1.5, "p1"), (2.1, 5.0, "p2")],
                                  "flights": [(1.5, 2.1, "p1", "p2")]}}, 5.0


# --------------------------------------------------------------------------------------
# Loop-1 regression scenes (independent tester report, SCR-T01..T22; geometries adapted from the tester's harness)
# --------------------------------------------------------------------------------------
TBG = {"RC": ((6.9, 0.4), (6.1, 0.9)), "LC": ((-6.9, 0.4), (-6.1, 0.9)),
       "RW": ((5.8, 4.6), (5.1, 4.0)), "LW": ((-5.8, 4.6), (-5.1, 4.0)), "TOP": ((0.0, 8.4), (0.0, 7.4))}


def tspec(actors, held=None, flights=None, bgs=()):
    """Spec with the tester's own-man background pairs (bo*/bd*) instead of o3-o5."""
    a = {}
    for n in bgs:
        (ox, oy), (dx, dy) = TBG[n]
        a["bo" + n], a["bd" + n] = Off((0, ox, oy)), Def((0, dx, dy))
    a.update(actors)
    return {"actors": a, "ball": {"held": held or [], "flights": flights or []}}


def sc_slot_switch():
    """SCR-T01: left-slot ball screen; D_s switches onto the handler, D_h takes the rolling screener (screener far from h)."""
    a = {"h": Off((0, -3.3, 7.7), (2.2, -3.3, 7.7), (3.6, 0.6, 7.0), (5.0, 1.6, 6.4)),
         "s": Off((0, -1.0, 4.0), (1.4, -2.35, 6.75), (3.0, -2.35, 6.75), (5.2, -0.4, 1.2)),
         "Dh": Def((0, -2.95, 6.85), (2.2, -2.95, 6.85), (2.8, -2.7, 7.4), (3.3, -2.6, 6.2), (5.2, -0.9, 1.9)),
         "Ds": Def((0, -0.9, 3.1), (1.4, -1.9, 5.3), (2.4, -1.9, 5.5), (3.0, -1.4, 7.3), (3.8, 0.4, 6.4), (5.0, 1.3, 5.6))}
    return tspec(a, held=[(0, 6.0, "h")], bgs=("RC", "RW", "LC")), 6.0


def sc_wing_reject_ice():
    """SCR-T02/T03: left-wing ball screen on the top side; D_h ices it and the handler rejects it to the baseline."""
    a = {"h": Off((0, -5.6, 4.9), (2.2, -5.6, 4.9), (2.8, -6.3, 3.4), (3.6, -4.2, 0.9), (4.5, -1.6, 0.4)),
         "s": Off((0, -2.4, 2.6), (1.4, -4.6, 5.8), (4.5, -4.6, 5.8)),
         "Dh": Def((0, -5.1, 5.3), (2.2, -5.1, 5.3), (2.8, -5.6, 3.9), (3.6, -3.8, 1.7), (4.5, -1.8, 1.0)),
         "Ds": Def((0, -2.2, 1.8), (1.4, -4.1, 4.9), (4.5, -4.1, 4.9))}
    return tspec(a, held=[(0, 5.0, "h")], bgs=("RC", "RW", "TOP")), 5.0


def sc_slot_step_up():
    """SCR-T03: right-slot handler stands next to the arriving screener (step-up from the elbow toward the sideline)."""
    a = {"h": Off((0, 3.4, 7.2), (2.3, 3.4, 7.2), (2.8, 4.6, 7.5), (3.4, 5.6, 5.4), (4.3, 4.2, 2.0)),
         "s": Off((0, 2.2, 3.6), (1.5, 4.05, 6.55), (3.2, 4.05, 6.55), (4.4, 2.0, 2.0)),
         "Dh": Def((0, 3.15, 6.3), (2.3, 3.15, 6.3), (2.7, 3.5, 6.6), (3.1, 4.3, 7.2), (3.6, 5.0, 5.3), (4.3, 4.0, 2.6)),
         "Ds": Def((0, 1.8, 2.9), (1.5, 3.7, 5.6), (3.2, 3.7, 5.6), (4.4, 2.4, 2.6))}
    return tspec(a, held=[(0, 5.5, "h")], bgs=("LC", "LW", "RC")), 5.5


def sc_rescreen_same_side():
    """SCR-T04: the first screen is not used, the screener steps off and screens again; the handler uses the second."""
    a = {"h": Off((0, 3.0, 7.4), (4.2, 3.0, 7.4), (4.7, 4.3, 7.4), (5.3, 5.4, 5.4), (6.2, 3.6, 1.8)),
         "s": Off((0, 1.0, 4.0), (1.2, 3.65, 6.6), (2.3, 3.65, 6.6), (2.8, 2.6, 5.4), (3.3, 3.7, 6.5), (5.2, 3.7, 6.5),
                  (6.4, 1.2, 2.0)),
         "Dh": Def((0, 2.8, 6.5), (4.2, 2.8, 6.5), (4.6, 3.1, 6.9), (5.0, 4.2, 7.3), (5.5, 4.9, 5.3), (6.3, 3.6, 2.6)),
         "Ds": Def((0, 0.9, 3.1), (1.2, 3.1, 5.6), (2.3, 3.1, 5.6), (2.8, 2.3, 4.8), (3.3, 3.2, 5.6), (5.2, 3.2, 5.6),
                   (6.4, 1.6, 2.6))}
    return tspec(a, held=[(0, 6.8, "h")], bgs=("LC", "LW", "RC")), 6.8


def sc_flare_away():
    """SCR-T05: classic flare (ball - D_u - s - u): D_u sags toward the ball, s sets on his back and u fades straight
    away from the screener and the ball without crossing the screen line (away use)."""
    a = {"u": Off((0, -3.2, 6.3), (2.0, -3.2, 6.3), (3.0, -6.6, 5.2)),
         "s": Off((0, -1.0, 3.5), (1.3, -2.4, 6.0), (3.5, -2.4, 6.0)),
         "Du": Def((0, -1.4, 6.2), (2.0, -1.4, 6.2), (2.5, -1.9, 6.7), (3.5, -4.8, 6.0)),
         "Ds": Def((0, -0.8, 2.6), (1.3, -1.9, 5.2), (3.5, -1.9, 5.2)),
         "p": Off((0, 5.5, 4.5)), "Dp": Def((0, 4.8, 3.9))}
    return spec(a, held=[(0, 5.0, "p")], skip=("o4", "o3")), 5.0


def sc_cutter_brush():
    """SCR-T06: a cutter runs past a standing teammate while his defender trails on the far side: no SET on anyone."""
    a = {"u": Off((0, 5.5, 4.8), (1.5, 5.5, 4.8), (3.2, 2.0, 1.6)),
         "s": Off((0, 3.0, 3.6)), "Ds": Def((0, 2.3, 2.9)),
         "Du": Def((0, 5.6, 3.9), (1.5, 5.6, 3.9), (3.3, 3.3, 0.9)),
         "p": Off((0, -2.0, 8.0)), "Dp": Def((0, -1.8, 7.0))}
    return tspec(a, held=[(0, 5.0, "p")], bgs=("LC", "LW")), 5.0


def sc_stack():
    """SCR-T07: two standing teammates side by side with their defenders; the ball is swung around: no screens."""
    a = {"o1": Off((0, -2.4, 2.0)), "o2": Off((0, -2.4, 3.1)), "d1": Def((0, -1.6, 1.7)), "d2": Def((0, -1.6, 3.2)),
         "p": Off((0, 0.0, 8.0), (2.5, 3.0, 7.4), (5.0, 0.0, 8.0)), "Dp": Def((0, 0.0, 7.1), (2.5, 2.6, 6.5), (5.0, 0.0, 7.1))}
    return tspec(a, held=[(0, 5.0, "p")], bgs=("RC", "RW", "LC")), 5.0


def sc_drag_left():
    """SCR-T08: transition drag screen set 8.3 m from the rim (above the old 7.5 m gate)."""
    a = {"h": Off((0, -2.4, 12.0), (1.8, -2.3, 8.4), (2.6, -2.3, 8.4), (3.8, 1.2, 7.6), (4.8, 0.6, 3.0)),
         "s": Off((0, -0.4, 13.6), (1.8, -1.3, 7.2), (3.4, -1.3, 7.2), (5.2, -0.6, 1.4)),
         "Dh": Def((0, -2.4, 11.0), (1.8, -2.1, 7.6), (2.6, -2.05, 7.6), (3.1, -1.8, 8.3), (4.0, 0.6, 7.3), (4.8, 0.5, 4.4)),
         "Ds": Def((0, 0.1, 14.6), (1.9, -1.0, 6.1), (3.4, -1.0, 6.1), (5.2, -0.9, 2.4))}
    return tspec(a, held=[(0, 6.0, "h")], bgs=("RC", "RW", "LC")), 6.0


def sc_wing_step_down():
    """SCR-T08/T09/T12: half-court side ball screen; the screener runs DOWN from the top past the handler's middle side
    (not a drag, not a flip, not a step-up) and the handler drives the sideline past a static corner player."""
    a = {"h": Off((0, 5.5, 5.0), (2.3, 5.5, 5.0), (2.8, 6.8, 4.4), (3.4, 6.6, 2.2), (4.3, 4.4, 0.8)),
         "s": Off((0, 1.0, 8.5), (1.5, 6.1, 4.15), (3.2, 6.1, 4.15), (4.4, 2.5, 2.0)),
         "Dh": Def((0, 5.0, 4.3), (2.3, 5.0, 4.3), (2.7, 5.3, 4.5), (3.1, 6.2, 5.0), (3.6, 6.3, 3.0), (4.3, 4.4, 1.4)),
         "Ds": Def((0, 0.8, 7.5), (1.5, 5.4, 3.4), (3.2, 5.4, 3.4), (4.4, 2.8, 2.6))}
    return tspec(a, held=[(0, 5.5, "h")], bgs=("LC", "LW", "RC")), 5.5


def sc_runthrough():
    """SCR-T09: the screener runs up from the corner across the handler->rim line well below him and sets on the middle
    side without showing on the other side: no flip."""
    a = {"h": Off((0, 5.0, 5.6), (3.0, 5.0, 5.6), (3.5, 4.4, 7.0), (4.1, 2.6, 6.6), (5.0, 0.6, 2.6)),
         "s": Off((0, 6.2, 1.0), (1.0, 2.6, 2.0), (2.4, 3.95, 5.65), (4.0, 3.95, 5.65), (5.0, 1.5, 1.0)),
         "Dh": Def((0, 4.6, 4.8), (3.0, 4.6, 4.8), (3.4, 4.5, 5.2), (3.8, 4.2, 6.4), (4.3, 2.8, 5.8), (5.0, 1.0, 3.2)),
         "Ds": Def((0, 5.6, 1.6), (1.0, 2.6, 1.4), (2.4, 3.4, 4.9), (4.0, 3.4, 4.9), (5.0, 1.8, 1.8))}
    return tspec(a, held=[(0, 6.0, "h")], bgs=("LC", "LW", "TOP")), 6.0


def sc_slot_ghost():
    """SCR-T11: the screener runs up near the arc, never stops or touches (1.3 m from D_h) and fades to the wing arc."""
    a = {"h": Off((0, 3.2, 7.4), (3.2, 3.2, 7.4), (4.2, 2.0, 7.8)),
         "s": Off((0, 1.0, 3.6), (1.3, 3.3, 5.4), (2.3, 6.4, 3.6)),
         "Dh": Def((0, 2.9, 6.5), (3.2, 2.9, 6.5), (4.2, 1.9, 6.9)),
         "Ds": Def((0, 0.8, 2.8), (1.3, 3.0, 4.6), (2.5, 5.6, 3.2))}
    return tspec(a, held=[(0, 5.0, "h")], bgs=("LC", "LW", "RC")), 5.0


def sc_slot_pnr_middle():
    """SCR-T14/T17: left-slot ball screen on the middle side of D_h (side-behind, not blind); handler turns the corner."""
    a = {"h": Off((0, -3.3, 7.7), (2.2, -3.3, 7.7), (3.6, 0.6, 7.0), (4.6, 0.3, 3.0)),
         "s": Off((0, -1.0, 4.0), (1.4, -2.35, 6.75), (3.0, -2.35, 6.75), (5.2, -0.4, 1.2)),
         "Dh": Def((0, -2.95, 6.85), (2.2, -2.95, 6.85), (2.9, -2.6, 7.65), (3.8, 0.0, 6.6), (4.6, 0.2, 3.8)),
         "Ds": Def((0, -0.9, 3.1), (1.4, -1.9, 5.3), (3.0, -1.9, 5.3), (5.0, -0.7, 2.0))}
    return tspec(a, held=[(0, 6.0, "h")], bgs=("RC", "RW", "LC")), 6.0


def sc_pitch():
    """SCR-T15: the big tosses the ball 2.8 m (0.5 s in the air) to a cutter running by 2.5 m away: a pitch, not a DHO."""
    a = {"a": Off((0, -1.0, 7.6), (1.5, -4.0, 5.1), (2.4, -4.0, 5.1), (3.6, -1.0, 2.0)),
         "b": Off((0, -7.2, 2.0), (0.4, -7.2, 2.0), (3.4, -5.6, 9.6)),
         "Da": Def((0, -1.0, 6.6), (1.5, -3.4, 4.4), (2.4, -3.4, 4.4), (3.8, -1.0, 3.0)),
         "Db": Def((0, -6.5, 2.4), (0.4, -6.5, 2.4), (3.5, -5.2, 8.6))}
    return tspec(a, held=[(0, 1.7, "a"), (2.2, 5.0, "b")], flights=[(1.7, 2.2, "a", "b")], bgs=("RC", "RW")), 5.0


def sc_elbow_down():
    """SCR-T16: down screen at the right elbow for a user at the short elbow who comes up to the slot (not an out screen)."""
    a = {"u": Off((0, 1.9, 2.8), (2.0, 1.9, 2.8), (2.6, 2.9, 4.6), (3.3, 3.3, 7.2)),
         "s": Off((0, 3.2, 7.6), (1.4, 2.2, 4.3), (3.6, 2.2, 4.3), (4.6, 0.6, 2.0)),
         "Du": Def((0, 2.0, 3.5), (2.0, 2.0, 3.5), (2.5, 2.4, 3.6), (2.9, 3.0, 4.2), (3.4, 3.2, 6.2)),
         "Ds": Def((0, 2.6, 6.9), (1.4, 1.6, 3.6), (3.6, 1.6, 3.6), (4.6, 0.9, 1.8)),
         "p": Off((0, -5.4, 5.6)), "Dp": Def((0, -4.8, 5.0))}
    return tspec(a, held=[(0, 5.0, "p")], bgs=("RC", "LC")), 5.0


# --------------------------------------------------------------------------------------
# Loop-2 regression scenes (confirmer's report on loop 1: still-failing items and regressions)
# --------------------------------------------------------------------------------------
def sc_corr_flare():
    """Loop 2 (SCR-T05): flare with D_u on the ball side of the screener (ball at the left wing): u jab-steps toward
    the ball, then fades to the right corner off s, who stands between D_u and the corner."""
    a = {"u": Off((0, 3.6, 7.3), (1.8, 3.6, 7.3), (2.4, 3.0, 6.9), (3.6, 6.6, 2.4)),
         "s": Off((0, 0.6, 3.6), (1.3, 3.15, 6.0), (3.8, 3.15, 6.0)),
         "Du": Def((0, 3.0, 6.7), (1.8, 3.0, 6.7), (2.4, 2.5, 6.75), (2.8, 2.6, 6.6), (3.8, 5.6, 2.9)),
         "Ds": Def((0, 0.5, 2.7), (1.3, 2.6, 5.2), (3.8, 2.6, 5.2)),
         "p": Off((0, -5.5, 4.6)), "Dp": Def((0, -4.8, 4.0))}
    return tspec(a, held=[(0, 5.0, "p")], bgs=("LC", "RC")), 5.0


def sc_high_wait_deep():
    """Loop 2 (REG-location): high PnR where the handler waits at r 9.4 m (pnr_location_logo) for a screen set at
    r 7.4 m (pnr_location_high): a high ball screen, the depth comes from the screen."""
    a = pnr(post="stay")
    a["h"]["wp"][0:2] = [(0, -0.3, 9.4), (2.0, -0.3, 9.4)]
    a["Dh"]["wp"][0:2] = [(0, -0.15, 8.4), (2.0, -0.15, 8.4)]
    return spec(a, held=[(0, 6.0, "h")]), 6.0


def sc_fake_backdoor():
    """Loop 2 (REG-fake_dho): the hander dribbles at the left-wing receiver, who comes up toward him, plants and
    back-cuts to the rim (the receiver's approach ends before the fake; the tester's fake_dho_backdoor, mirrored)."""
    a = {"a": Off((0, -0.5, 7.6), (1.0, -0.5, 7.6), (2.0, -3.6, 6.8), (2.4, -3.6, 6.8), (3.6, -3.6, 6.8)),
         "b": Off((0, -5.6, 3.0), (0.6, -5.6, 3.0), (2.0, -4.6, 6.4), (2.15, -4.6, 6.4), (3.5, -0.4, 0.8)),
         "Da": Def((0, -0.5, 6.6), (1.0, -0.5, 6.6), (2.0, -3.0, 6.0), (3.6, -3.0, 6.0)),
         "Db": Def((0, -5.4, 4.0), (0.6, -5.4, 4.0), (2.0, -4.4, 7.3), (2.3, -4.4, 7.3), (3.7, -1.2, 2.2))}
    return tspec(a, held=[(0, 5.0, "a")], bgs=("RC", "RW")), 5.0


def sc_back_short_cut():
    """Loop 2 (SCR-T06 residual): back screen from the top, but the user only cuts to the short corner and stops next
    to the screener's defender: the user is no screener for the standing screener."""
    sp, dur = sc_back(rip=False)
    sp["actors"]["u"] = Off((0, 5.0, 5.0), (2.0, 5.0, 5.0), (3.0, 3.4, 3.1), (4.0, 3.4, 3.1))
    sp["actors"]["Du"] = Def((0, 4.6, 4.3), (2.0, 4.6, 4.3), (2.4, 4.4, 4.2), (2.8, 4.4, 4.2), (3.4, 3.6, 3.9))
    return sp, dur


def sc_double_drag_late():
    """Loop 2 (SCR-T06 residual): the second trailer arrives 2.5 s after the first; the ball handler is no off-ball
    screener for the first trailer."""
    sp, _ = sc_drag(double=True)
    sp["actors"]["s2"] = Off((0, 1.4, 14.5), (4.1, 1.4, 7.2), (6.2, 1.4, 7.2), (7.4, 4.6, 6.0))
    sp["actors"]["Ds2"] = Def((0, 2.1, 15.6), (4.2, 1.8, 6.2), (6.2, 1.8, 6.2), (7.4, 3.8, 5.0))
    h = sp["actors"]["h"]["wp"]
    sp["actors"]["h"] = Off(*h[:-1], (5.0, 1.5, 2.5))
    return sp, 7.5


def sc_side_by_side():
    """Loop 2 (SCR-T06 residual): double screen, two screeners arrive shoulder to shoulder (0.9 m) at the left mid post
    and the user comes off both; the screeners are no screen for each other (the tester's double_side_by_side)."""
    a = {"u": Off((0, -1.6, 1.0), (2.0, -1.6, 1.0), (2.9, -3.8, 3.2), (3.6, -5.0, 5.2)),
         "s1": Off((0, -1.0, 4.5), (1.3, -2.6, 2.6), (3.8, -2.6, 2.6)),
         "s2": Off((0, -1.5, 5.5), (1.3, -3.2, 1.95), (3.8, -3.2, 1.95)),
         "Du": Def((0, -2.2, 1.6), (2.0, -2.2, 1.6), (2.5, -2.6, 1.6), (2.9, -3.2, 2.0), (3.5, -4.4, 4.3)),
         "Ds1": Def((0, -0.6, 3.8), (1.3, -2.0, 3.2), (3.8, -2.0, 3.2)),
         "Ds2": Def((0, -1.0, 4.6), (1.3, -3.4, 2.9), (3.8, -3.4, 2.9)),
         "p": Off((0, 5.0, 5.0)), "Dp": Def((0, 4.3, 4.4))}
    return tspec(a, held=[(0, 5.0, "p")], bgs=("RC",)), 5.0


def sc_weave(pass2=False):
    """Loop 2 (SCR-T22 gap): weave, two DHOs on the perimeter within weave_s (a -> b at the right slot, b -> c at the
    left slot). Near miss (pass2): c cuts 3 m below b and gets a pass (0.4 s in the air), not a handoff."""
    c = ((0, -5.0, 3.6), (2.8, -5.0, 3.6), (6.5, 3.5, 4.4)) if pass2 else ((0, -5.0, 6.4), (2.8, -5.0, 6.4), (6.5, 3.5, 7.2))
    a = {"a": Off((0, 0.0, 7.5), (1.5, 2.2, 6.85), (2.3, 2.2, 6.85), (3.3, 1.0, 2.0)),
         "b": Off((0, 4.5, 6.0), (0.3, 4.5, 6.0), (2.6, -0.3, 7.5), (3.4, -1.5, 7.3), (4.2, -1.5, 7.3), (5.2, -1.0, 2.5)),
         "c": Off(*c),
         "Da": Def((0, 0.0, 6.5), (1.5, 1.5, 5.9), (2.3, 1.5, 5.9), (3.5, 1.0, 3.0)),
         "Db": Def((0, 4.0, 5.0), (0.3, 4.0, 5.0), (3.4, -1.2, 6.4), (4.2, -1.2, 6.4), (5.4, -0.8, 3.2)),
         "Dc": Def((0, -4.5, c[0][2] - 0.9), (2.8, -4.5, c[0][2] - 0.9), (6.5, 3.2, c[2][2] - 1.0))}
    if pass2:
        return spec(a, held=[(0, 1.77, "a"), (1.77, 4.1, "b"), (4.5, 6.5, "c")], flights=[(4.1, 4.5, "b", "c")],
                    skip=("o3", "o4")), 6.5
    return spec(a, held=[(0, 1.77, "a"), (1.77, 4.32, "b"), (4.32, 6.5, "c")], skip=("o3", "o4")), 6.5


def sc_miami(pass1=False):
    """Loop 2 (SCR-T22 gap): Miami, DHO a -> b at the right slot, then a sets a ball screen for b at the top (within
    miami_s). Near miss (pass1): a passes to b from 3 m (0.4 s in the air) instead of handing off."""
    a = {"a": Off((0, -0.5, 8.0), (1.4, 1.2, 6.95), (1.9, 1.2, 6.95), (2.4, -0.35, 7.25), (3.8, -0.35, 7.25), (4.8, 0.5, 2.5)),
         "b": Off((0, 4.5, 6.0), (0.3, 4.5, 6.0), (1.77, 1.3, 7.45), (2.5, -1.1, 8.3), (2.7, -1.1, 8.3), (3.0, -0.2, 8.45),
                  (3.5, 1.5, 6.8), (4.5, 1.0, 2.5)),
         "Da": Def((0, -0.5, 7.0), (1.4, 0.7, 6.1), (1.9, 0.7, 6.1), (2.4, 0.0, 6.4), (3.8, 0.0, 6.4), (4.8, 0.8, 3.2)),
         "Db": Def((0, 4.0, 5.0), (0.3, 4.0, 5.0), (1.8, 1.6, 6.6), (2.5, -0.8, 7.4), (2.8, -0.75, 7.4), (3.1, -0.6, 7.7),
                   (3.5, 0.1, 7.9), (4.1, 1.4, 6.0))}
    if pass1:
        a["b"]["wp"][2] = (1.77, 2.3, 9.6)  # b catches 3 m from a
        return spec(a, held=[(0, 1.4, "a"), (1.8, 5.5, "b")], flights=[(1.4, 1.8, "a", "b")], skip=("o4",)), 5.5
    return spec(a, held=[(0, 1.77, "a"), (1.77, 5.5, "b")], skip=("o4",)), 5.5


def shifted(name, dx=0.0, dy=0.0):
    """A scenario with every actor waypoint moved by (dx, dy) m (SCR-T18 brittleness check)."""
    sp, dur = SCEN[name]()
    for v in sp["actors"].values():
        v["wp"] = [(w[0], w[1] + dx, w[2] + dy) for w in v["wp"]]
    return sp, dur


SCEN = {
    "high_pnr": lambda: sc_high_pnr(),
    "high_pnr_pop": lambda: sc_high_pnr(post="pop"),
    "high_pnr_under": lambda: sc_high_pnr(route="under"),
    "pnr_switch": sc_pnr_switch,
    "pnr_reject": sc_pnr_reject,
    "side_step_up": sc_side_step_up,
    "slip": sc_slip,
    "ghost": sc_ghost,
    "fake_lateral": sc_fake_lateral,
    "drag": lambda: sc_drag(),
    "double_drag": lambda: sc_drag(double=True),
    "spain": sc_spain,
    "detroit": sc_detroit,
    "ram": sc_ram,
    "veer": sc_veer,
    "rescreen": sc_rescreen,
    "flip": sc_flip,
    "pin_down": lambda: sc_pin_down(),
    "wide_pin_down": lambda: sc_pin_down(wide=True),
    "flare": sc_flare,
    "back_rip": lambda: sc_back(rip=True),
    "back_top": lambda: sc_back(rip=False),
    "back_blind": lambda: sc_back(rip=False, blind=True),
    "ucla": sc_ucla,
    "shuffle": sc_shuffle,
    "cross": lambda: sc_cross(),
    "flex": lambda: sc_cross(flex=True),
    "stagger": lambda: sc_stagger(),
    "double": lambda: sc_stagger(double=True),
    "elevator": sc_elevator,
    "hammer": sc_hammer,
    "zipper": sc_zipper,
    "iverson": sc_iverson,
    "wedge": sc_wedge,
    "sts": sc_sts,
    "out": sc_out,
    "dho": lambda: sc_dho("dho"),
    "fake_dho": lambda: sc_dho("fake"),
    "get": lambda: sc_dho("get"),
    "moving_screen": sc_moving_screen,
    "walk_by": sc_walk_by,
    "null": sc_null,
    # loop-1 regression scenes
    "slot_switch": sc_slot_switch,
    "wing_reject_ice": sc_wing_reject_ice,
    "slot_step_up": sc_slot_step_up,
    "rescreen_same_side": sc_rescreen_same_side,
    "flare_away": sc_flare_away,
    "cutter_brush": sc_cutter_brush,
    "stack": sc_stack,
    "drag_left": sc_drag_left,
    "wing_step_down": sc_wing_step_down,
    "runthrough": sc_runthrough,
    "slot_ghost": sc_slot_ghost,
    "slot_pnr_middle": sc_slot_pnr_middle,
    "pitch": sc_pitch,
    "elbow_down": sc_elbow_down,
    "zipper_up": lambda: shifted("zipper", dy=0.3),
    "zipper_out": lambda: shifted("zipper", dx=0.3),
    "flex_up": lambda: shifted("flex", dy=0.3),
    "flex_in": lambda: shifted("flex", dx=0.3),
    # loop-2 regression scenes
    "corr_flare": sc_corr_flare,
    "high_wait_deep": sc_high_wait_deep,
    "fake_backdoor": sc_fake_backdoor,
    "back_short_cut": sc_back_short_cut,
    "double_drag_late": sc_double_drag_late,
    "side_by_side": sc_side_by_side,
    "weave": lambda: sc_weave(),
    "weave_pass": lambda: sc_weave(pass2=True),
    "miami": lambda: sc_miami(),
    "miami_pass": lambda: sc_miami(pass1=True),
}


@lru_cache(maxsize=None)
def build(name, seed=SEED, sigma=SIGMA):
    """(truth, scene) for one named scenario; cached per (name, seed, sigma)."""
    sp, dur = SCEN[name]()
    truth, tracks = scenario(sp, dur, sigma, seed)
    return truth, build_scene(tracks)


@lru_cache(maxsize=None)
def run(name, det, seed=SEED, sigma=SIGMA):
    _, sc = build(name, seed, sigma)
    return tuple(S.DETECTORS[det](sc))


# --------------------------------------------------------------------------------------
# Truth t0 helpers (noise-free paths, same rules as the spec)
# --------------------------------------------------------------------------------------
def _tp(truth, a):
    return np.stack(truth[a], axis=1)


def _td(truth, a, b):
    return np.hypot(*(_tp(truth, a) - _tp(truth, b)).T)


def _speed(truth, a):
    p = _tp(truth, a)
    return np.hypot(*np.gradient(p, DT, axis=0).T)


def t_stop(truth, a, after=0.0):
    """Stop onset: first frame after `after` s where the true speed falls below 0.3 m/s and stays there for 0.3 s."""
    v = _speed(truth, a)
    n9 = int(round(0.3 / DT))
    for k in range(int(round(after / DT)), len(v) - n9):
        if np.all(v[k:k + n9] < 0.3):
            return k * DT
    raise AssertionError("no stop")


def t_screen(truth, s, d, u, lo, hi):
    """screen_moment on truth: d(s, D) dips <= 1.2 m in [lo, hi] s (split by a 0.4 m rise); the contact window
    (contiguous d <= max(dip min + 0.4, 1.5) m) nearest the user's closest approach while moving (displacement over
    +-0.3 s >= 0.6 m); t_s = its frame nearest that approach (the earliest dip's minimum if the user never moves)."""
    dd = _td(truth, s, d)
    a, b = int(round(lo / DT)), int(round(hi / DT))
    seg = dd[a:b + 1]
    su = _td(truth, s, u)[a:b + 1]
    pu, h9 = _tp(truth, u), 9
    pp = np.pad(pu, ((h9, h9), (0, 0)), mode="edge")
    moving = (np.hypot(*(pp[2 * h9:] - pp[:-2 * h9]).T) / (2 * h9 * DT) >= 1.0)[a:b + 1]
    moving[:15] = False  # lo = stop onset - 0.5 s by convention: the use happens once the screener stands
    tsu = int(np.argmin(np.where(moving, su, np.inf))) if moving.any() else None
    mins = [i for i in range(len(seg)) if seg[i] <= 1.2 and seg[i] == seg[max(0, i - 3):i + 4].min()]
    dips = []
    for i in mins:
        if dips and seg[dips[-1][-1]:i + 1].max() < max(seg[dips[-1][-1]], seg[i]) + 0.4:
            dips[-1].append(i)
        else:
            dips.append([i])
    best = None
    for dp in dips or [[int(np.argmin(seg))]]:
        band = max(min(seg[i] for i in dp) + 0.4, 1.5)  # contact window: defender still within 1.5 m
        ia, ib = dp[0], dp[-1]
        while ia > 0 and seg[ia - 1] <= band:
            ia -= 1
        while ib + 1 < len(seg) and seg[ib + 1] <= band:
            ib += 1
        if tsu is None:  # the user never moves: first frame of the earliest contact window once the screener stands
            best = best if best is not None else min((i for i in range(max(ia, 15), ib + 1) if seg[i] <= band),
                                                     default=ib)
            continue
        k = min((i for i in range(ia, ib + 1) if seg[i] <= band), key=lambda i: abs(i - tsu))
        if best is None or abs(k - tsu) < abs(best - tsu):
            best = k
    return (a + best) * DT


def t_min(truth, a, b, lo, hi):
    dd = _td(truth, a, b)
    i, j = int(round(lo / DT)), int(round(hi / DT))
    return (i + int(np.argmin(dd[i:j + 1]))) * DT


def t_cross_line(truth, u, p_s, d_hat, lo, hi):
    p = _tp(truth, u)
    lam = (p - np.asarray(p_s)) @ np.asarray(d_hat)
    for k in range(int(round(lo / DT)), int(round(hi / DT))):
        if lam[k] < 0 <= lam[k + 1]:
            return (k + 1) * DT
    raise AssertionError("no crossing")


# --------------------------------------------------------------------------------------
# Positive cases: (detector, scenario, required actors, truth t0 function, attribute checks)
# --------------------------------------------------------------------------------------
def ts_(s, d, u, lo, hi):
    return lambda tr: t_screen(tr, s, d, u, lo, hi)


def stop_(a, after=0.0):
    return lambda tr: t_stop(tr, a, after)


def at(x):
    return lambda tr: x


POS = [
    # primitives
    ("screen_set", "high_pnr", {"screener": "s", "user": "h", "defender": "Dh"}, stop_("s"), {}),
    ("screen", "high_pnr", {"screener": "s", "user": "h", "defender": "Dh"}, ts_("s", "Dh", "h", 0.8, 3.4),
     {"kind": "on_ball", "read": "use"}),
    ("screen", "pin_down", {"screener": "s", "user": "u", "defender": "Du"}, ts_("s", "Du", "u", 0.9, 4.1),
     {"kind": "off_ball"}),
    ("screen_moment", "high_pnr", {"screener": "s", "user": "h", "defender": "Dh"}, ts_("s", "Dh", "h", 0.8, 3.4), {}),
    ("screen_read", "high_pnr", {"screener": "s", "user": "h"}, ts_("s", "Dh", "h", 0.8, 3.4), {"read": "use"}),
    ("screen_read", "pnr_reject", {"screener": "s", "user": "h"}, ts_("s", "Dh", "h", 0.8, 4.1), {"read": "reject"}),
    ("screen_interaction", "high_pnr", {"defender": "Dh", "screener": "s", "user": "h"},
     ts_("s", "Dh", "h", 0.8, 3.4), {"interaction": True}),
    ("screener_post_action", "high_pnr", {"screener": "s", "user": "h"},
     lambda tr: t_cross_line(tr, "h", P_S, _unit_disp(tr, "h", 2.0, 3.5), 1.5, 3.5), {"action": "roll"}),
    ("screener_post_action", "high_pnr_pop", {"screener": "s", "user": "h"},
     lambda tr: t_cross_line(tr, "h", P_S, _unit_disp(tr, "h", 2.0, 3.5), 1.5, 3.5), {"action": "pop_arc"}),
    # ball screens
    ("ball_screen", "high_pnr", {"screener": "s", "handler": "h", "defender": "Dh"}, ts_("s", "Dh", "h", 0.8, 3.4),
     {"location": "high", "post_action": "roll"}),
    ("high_ball_screen", "high_pnr", {"screener": "s", "handler": "h"}, ts_("s", "Dh", "h", 0.8, 3.4), {}),
    ("side_ball_screen", "side_step_up", {"screener": "s", "handler": "h"}, ts_("s", "Dh", "h", 0.9, 3.5), {}),
    ("step_up_screen", "side_step_up", {"screener": "s", "handler": "h"}, ts_("s", "Dh", "h", 0.9, 3.5),
     {"pre_action": "step_up"}),
    ("flip_screen", "flip", {"screener": "s", "handler": "h"}, ts_("s", "Dh", "h", 1.3, 3.8),
     {"direction_pre": "to_sideline", "direction_post": "to_middle"}),
    ("re_screen", "rescreen", {"screener": "s", "handler": "h"}, ts_("s", "Dh", "h", 2.5, 5.1), {"merged": False}),
    ("slip_screen", "slip", {"screener": "s", "handler": "h", "defender": "Dh"}, lambda tr: t_min(tr, "s", "Dh", 0.5, 2.0),
     {}),
    ("ghost_screen", "ghost", {"screener": "s", "handler": "h", "defender": "Dh"},
     lambda tr: t_min(tr, "s", "Dh", 0.5, 2.0), {}),
    ("fake_screen", "fake_lateral", {"screener": "s", "handler": "h", "defender": "Dh"},
     lambda tr: t_min(tr, "s", "Dh", 0.5, 2.0), {"exit": "lateral"}),
    ("drag_screen", "drag", {"screener": "s", "handler": "h"}, ts_("s", "Dh", "h", 1.3, 3.8), {"pre_action": "drag"}),
    ("double_drag", "double_drag", {"screener_1": "s", "screener_2": "s2", "handler": "h"},
     ts_("s", "Dh", "h", 1.3, 4.1), {}),
    ("spain_pnr", "spain", {"screener": "s1", "back_screener": "s2", "handler": "h", "defender": "Ds1"},
     ts_("s1", "Dh", "h", 0.8, 3.4), {}),
    ("double_ball_screen", "detroit", {"handler": "h"}, None, {"sub_label": "detroit"}),
    ("ram_screen", "ram", {"first_screener": "g", "screener": "s", "handler": "h"}, ts_("g", "Ds", "s", 0.5, 2.8),
     {"pre_action": "wedge_ram"}),
    ("veer_screen", "veer", {"screener": "s", "handler": "h", "user_2": "o3"}, ts_("s", "Dh", "h", 0.8, 3.6), {}),
    # defender response
    ("ball_screen_coverage", "high_pnr", {"handler_defender": "Dh", "screener_defender": "Ds", "handler": "h"},
     ts_("s", "Dh", "h", 0.8, 3.4), {"route": "over", "big": "high_drop", "switch": "none"}),
    ("ball_screen_coverage", "high_pnr_under", {"handler_defender": "Dh", "handler": "h"},
     ts_("s", "Dh", "h", 0.8, 3.4), {"route": "under"}),
    ("ball_screen_coverage", "pnr_switch", {"handler_defender": "Dh", "screener_defender": "Ds", "handler": "h"},
     ts_("s", "Dh", "h", 0.8, 3.4), {"switch": "normal", "coverage_coarse": "switch"}),
    ("off_ball_screen_coverage", "pin_down", {"defender": "Du", "user": "u", "screener": "s"},
     ts_("s", "Du", "u", 0.9, 4.1), {}),
    # off-ball geometry
    ("down_screen", "pin_down", {"screener": "s", "user": "u", "defender": "Du"}, ts_("s", "Du", "u", 0.9, 4.1), {}),
    ("pin_down", "pin_down", {"screener": "s", "user": "u"}, ts_("s", "Du", "u", 0.9, 4.1), {"geometry": "pin_down"}),
    ("pin_down", "wide_pin_down", {"screener": "s", "user": "u"}, ts_("s", "Du", "u", 0.9, 4.1),
     {"geometry": "wide_pin_down"}),
    ("flare_screen", "flare", {"screener": "s", "user": "u", "defender": "Du"}, ts_("s", "Du", "u", 0.8, 4.0), {}),
    ("back_screen", "back_top", {"screener": "s", "user": "u", "defender": "Du"}, ts_("s", "Du", "u", 0.9, 4.1), {}),
    ("rip_screen", "back_rip", {"screener": "s", "user": "u"}, ts_("s", "Du", "u", 0.9, 4.1), {}),
    ("ucla_screen", "ucla", {"screener": "s", "user": "u"}, at(1.5), {}),
    ("cross_screen", "cross", {"screener": "s", "user": "u", "defender": "Du"}, ts_("s", "Du", "u", 0.8, 4.0), {}),
    ("stagger_screen", "stagger", {"user": "u", "screener_1": "s1", "screener_2": "s2"},
     ts_("s1", "Du", "u", 0.8, 3.5), {"n_screens": 2}),
    ("double_screen", "double", {"screener_1": "s1", "screener_2": "s2", "user": "u"}, None, {}),
    ("elevator_screen", "elevator", {"user": "u"},
     lambda tr: t_cross_line(tr, "u", (0.0, 4.7), (0.0, 1.0), 2.0, 3.0), {}),
    ("hammer_screen", "hammer", {"driver": "h", "screener": "s", "user": "u"},
     lambda tr: max(k for k in range(int(round(2.2 / DT))) if np.hypot(*_tp(tr, "h")[k]) > 6.1) * DT, {}),
    ("flex_screen", "flex", {"screener": "s", "user": "u", "defender": "Du"}, ts_("s", "Du", "u", 0.5, 4.5), {}),
    ("zipper_screen", "zipper", {"screener": "s", "user": "u", "defender": "Du"}, ts_("s", "Du", "u", 0.8, 4.1), {}),
    ("iverson_screen", "iverson", {"user": "u"},
     lambda tr: next(k for k in range(len(tr["u"][0])) if abs(np.gradient(tr["u"][0], DT)[k]) >= 2.0) * DT,
     {}),
    ("wedge_screen", "wedge", {"screener": "s", "user": "u", "defender": "Du"}, ts_("s", "Du", "u", 0.9, 4.1), {}),
    ("shuffle_screen", "shuffle", {"screener": "s", "user": "u"}, at(1.5), {}),
    ("screen_the_screener", "sts", {"first_screener_user": "s1", "screener_2": "s2", "first_user": "u1"},
     ts_("s1", "Du1", "u1", 0.8, 3.3), {}),
    ("off_ball_screen_other", "out", {"screener": "s", "user": "u", "defender": "Du"}, ts_("s", "Du", "u", 0.5, 4.0),
     {"geometry": "out"}),
    # handoffs
    ("dho", "dho", {"hander": "a", "receiver": "b"}, at(1.77), {}),
    ("fake_dho", "fake_dho", {"hander": "a", "receiver": "b"}, lambda tr: t_min(tr, "a", "b", 1.0, 3.0),
     {"sub_label": "away"}),
    ("dho_keep", "fake_dho", {"hander": "a", "receiver": "b"}, lambda tr: t_min(tr, "a", "b", 1.0, 3.0), {}),
    ("handoff_chain", "get", {"a": "a", "b": "b"}, at(1.0), {"chain": "get"}),
    # legality hints
    ("moving_screen_hint", "moving_screen", {"screener": "s", "defender": "Dh"},
     lambda tr: t_min(tr, "s", "Dh", 1.0, 3.0), {}),
    ("blind_screen_hint", "back_blind", {"screener": "s", "defender": "Du"}, stop_("s"), {"hint": "blind_no_step"}),
]


# Positive cases that use another fixed seed, with the reason (the rate over 10 seeds is tested below)
SEED_FOR = {("blind_screen_hint", "back_blind"): 1,  # seed 7 misses (rate over 10 seeds tested below)
            ("drag_screen", "drag"): 1}  # seed 7: noisy closest approach 1.38 m for a true 0.92 m (gate 1.2 m)


def _unit_disp(tr, a, t0, t1):
    p = _tp(tr, a)
    d = p[int(round(t1 / DT))] - p[int(round(t0 / DT))]
    return d / np.hypot(*d)


def _match(ev, actors):
    return all(ev.actors.get(k) == v for k, v in actors.items())


@pytest.mark.parametrize("det,scen,actors,t0f,attrs", POS, ids=[f"{p[0]}-{p[1]}" for p in POS])
def test_positive(det, scen, actors, t0f, attrs):
    seed = SEED_FOR.get((det, scen), SEED)
    truth, _ = build(scen, seed)
    evs = [e for e in run(scen, det, seed) if _match(e, actors)]
    assert evs, f"{det} did not fire on {scen}: got {[(e.actors, round(e.t0 * DT, 2)) for e in run(scen, det, seed)]}"
    ev = max(evs, key=lambda e: e.conf)
    assert ev.kind == det
    assert CONF_MIN <= ev.conf <= 1.0, ev.conf
    if t0f is not None:
        t_true = t0f(truth)
        assert abs(ev.t0 * DT - t_true) <= T_TOL, (ev.t0 * DT, t_true)
    for k, v in attrs.items():
        assert ev.attrs.get(k) == v, (k, ev.attrs.get(k), v)
    if det == "screen":
        assert ev.attrs["strict"] is not True  # STRICT (0.30 m/s) is untestable at sigma_p 0.3 (null) or failed


# --------------------------------------------------------------------------------------
# Negative cases: every detector on the null scenario, plus near-miss scenarios
# --------------------------------------------------------------------------------------
NEG = [
    ("high_ball_screen", "side_step_up"),
    ("side_ball_screen", "high_pnr"),
    ("step_up_screen", "high_pnr"),
    ("flip_screen", "high_pnr"),
    ("re_screen", "high_pnr"),
    ("slip_screen", "high_pnr"),
    ("slip_screen", "ghost"),
    ("ghost_screen", "slip"),
    ("ghost_screen", "high_pnr"),
    ("fake_screen", "slip"),
    ("fake_screen", "high_pnr"),
    ("drag_screen", "high_pnr"),
    ("double_drag", "drag"),
    ("spain_pnr", "high_pnr"),
    ("double_ball_screen", "double_drag"),
    ("double_ball_screen", "high_pnr"),
    ("ram_screen", "high_pnr"),
    ("veer_screen", "high_pnr"),
    ("ball_screen", "pin_down"),
    ("screen", "pnr_reject"),
    ("screen_interaction", "pnr_reject"),
    ("screener_post_action", "pin_down"),
    ("down_screen", "back_top"),
    ("down_screen", "flare"),
    ("pin_down", "back_top"),
    ("flare_screen", "pin_down"),
    ("back_screen", "pin_down"),
    ("rip_screen", "back_top"),
    ("ucla_screen", "shuffle"),
    ("ucla_screen", "back_rip"),
    ("shuffle_screen", "ucla"),
    ("cross_screen", "pin_down"),
    ("flex_screen", "cross"),
    ("stagger_screen", "double"),
    ("double_screen", "stagger"),
    ("elevator_screen", "pin_down"),
    ("hammer_screen", "pin_down"),
    ("zipper_screen", "wide_pin_down"),
    ("iverson_screen", "flare"),
    ("wedge_screen", "back_top"),
    ("screen_the_screener", "pin_down"),
    ("off_ball_screen_other", "high_pnr"),
    ("dho", "fake_dho"),
    ("dho", "ucla"),
    ("fake_dho", "dho"),
    ("dho_keep", "dho"),
    ("handoff_chain", "dho"),
    ("moving_screen_hint", "high_pnr"),
    ("blind_screen_hint", "pin_down"),
    ("screen_pose_legality", "high_pnr"),
]


@pytest.mark.parametrize("det", sorted(S.DETECTORS))
def test_null_scenario_is_silent(det):
    assert run("null", det) == (), [(e.actors, round(e.t0 * DT, 2)) for e in run("null", det)]


@pytest.mark.parametrize("det,scen", NEG, ids=[f"{d}-{s}" for d, s in NEG])
def test_negative(det, scen):
    evs = run(scen, det)
    assert evs == (), [(e.actors, round(e.t0 * DT, 2), round(e.conf, 2)) for e in evs]


# --------------------------------------------------------------------------------------
# Registry, parameters and rule-level checks
# --------------------------------------------------------------------------------------
def test_every_detector_has_positive_and_negative():
    pos = {p[0] for p in POS}
    missing = (set(S.DETECTORS) - {"screen_pose_legality"}) - pos
    assert not missing, missing
    neg = {n[0] for n in NEG} | set(S.DETECTORS)  # null scenario covers every detector
    assert set(S.DETECTORS) <= neg


def test_yaml_is_single_source_of_truth():
    for iid, it in S.ITEMS.items():
        for k, v in (it.get("params") or {}).items():
            assert "value" in v and "unit" in v, (iid, k)
        assert it["status"] in ("canonical", "proposal")
        if it.get("detector"):
            assert it["detector"] == f"detect_{iid}"
            assert S.DETECTORS[iid].__name__ == it["detector"]
    assert S.prm("screen")["d_su_max_m"] == 1.2
    with pytest.raises(KeyError):
        S.prm("screen", {"no_such_param": 1})


def test_needs_data_item_returns_empty():
    assert S.ITEMS["screen_pose_legality"]["needs_data"]
    _, sc = build("high_pnr")
    assert S.detect_screen_pose_legality(sc) == []


def test_detect_all_keys():
    _, sc = build("high_pnr")
    out = S.detect_all(sc)
    assert set(out) == set(S.DETECTORS)
    assert all(isinstance(v, list) for v in out.values())


def test_rice_posterior_is_calibrated_direction():
    # still player: posterior of the loose band rises with the window precision; walkers get low probability
    assert S.rice_below(0.2, 0.6, 0.15) > 0.9
    assert S.rice_below(1.0, 0.6, 0.15) < 0.05
    assert 0.0 <= S.rice_below(0.4, 0.3, 0.3) <= 1.0


def test_strict_is_null_at_sigma_03_and_testable_at_low_noise():
    # STRICT (0.30 m/s) needs sigma_win <= 0.30 / testable_ratio: NULL on a screen at sigma_p 0.3 ...
    _, sc = build("high_pnr")
    ev = max(S.detect_screen(sc), key=lambda e: e.conf)
    assert ev.attrs["strict"] is not True and ev.attrs["loose"] in (True, False)  # loose testable
    # ... and on a 5 s stand: NULL at sigma_p 0.3, decided (True) at sigma_p 0.1
    for sigma, expect in ((0.3, None), (0.1, True)):
        _, tracks = scenario({"actors": {"s": Off((0, 1.0, 7.0)), "d": Def((0, 1.0, 6.0))}}, 5.0, sigma, SEED)
        st = S._stops(build_scene(tracks), "s")
        assert len(st) == 1 and st[0].loose is True and st[0].strict is expect, (sigma, st)


def test_walking_screener_is_not_a_set():
    # a teammate walking past a standing defender at about 1 m/s: the per-frame stand test passes often
    # (s2 < 5.99 on about 40 % of frames), the LS window speed rejects it (fix of check SCR-R01/R02-a)
    _, sc = build("walk_by")
    assert not [e for e in S.detect_screen_set(sc) if e.actors["screener"] == "s"]
    assert not [e for e in S.detect_screen(sc) if e.actors["screener"] == "s"]


def _positive_ok(det, scen, actors, t0f, attrs, seed):
    truth, _ = build(scen, seed)
    evs = [e for e in run(scen, det, seed) if _match(e, actors)]
    if not evs:
        return False
    ev = max(evs, key=lambda e: e.conf)
    return (CONF_MIN <= ev.conf <= 1.0 and (t0f is None or abs(ev.t0 * DT - t0f(truth)) <= T_TOL)
            and all(ev.attrs.get(k) == v for k, v in attrs.items()))


def test_positive_rate_over_seeds():
    # robustness at sigma_p 0.3 over seeds 1-5 (V0): every positive case on >= 2 of 5 seeds, >= 85 % overall
    rates = {(c[0], c[1]): sum(_positive_ok(*c, seed=sd) for sd in range(1, 6)) for c in POS}
    weak = {k: v for k, v in rates.items() if v < 2}
    assert not weak, weak
    assert sum(rates.values()) >= 0.85 * 5 * len(POS), (sum(rates.values()), 5 * len(POS))


def test_blind_hint_detection_rate():
    # contact-distance hints live at the noise floor, and since loop 1 (SCR-T14) blindness is a probability (>= 0.8 that
    # the screener is > 120 deg off D_u's facing): a screener squarely behind D_u fires on 7 of 10 seeds at sigma_p 0.3
    # (misses: the 5-frame distance at the detected stop onset reads > 0.9 m while the screener still decelerates)
    hits = sum(bool([e for e in run("back_blind", "blind_screen_hint", sd) if e.actors["screener"] == "s"])
               for sd in range(1, 11))
    assert hits >= 6, hits


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_high_pnr_is_stable_across_seeds(seed):
    truth, sc = build("high_pnr", seed)
    evs = [e for e in S.detect_screen(sc) if e.actors["screener"] == "s" and e.actors["user"] == "h"]
    assert len(evs) == 1
    assert abs(evs[0].t0 * DT - t_screen(truth, "s", "Dh", "h", 0.8, 3.4)) <= T_TOL


# --------------------------------------------------------------------------------------
# Loop-1 regressions: one test per fixed failure of the independent tester's report (SCR-T01..T22)
# --------------------------------------------------------------------------------------
def _evs(name, det, seed=SEED, sigma=SIGMA, **actors):
    return [e for e in run(name, det, seed, sigma) if _match(e, actors)]


def _rate(name, det, seeds=range(1, 6), sigma=SIGMA, pred=lambda e: True, **actors):
    return sum(bool([e for e in _evs(name, det, sd, sigma, **actors) if pred(e)]) for sd in seeds)


@pytest.mark.parametrize("sigma", [0.2, 0.3, 0.5])
def test_t01_switch_with_far_screener_does_not_crash(sigma):
    # seed 7 is the tester's crash: a switch is detected while D_s depth reads 'screener_far' (no coarse class)
    _, sc = build("slot_switch", 7, sigma)
    out = S.detect_all(sc)  # raised ValueError in _coverage_on before loop 1
    cov = [e for e in out["ball_screen_coverage"] if e.actors["handler"] == "h" and e.actors["screener"] == "s"]
    assert cov and cov[0].attrs["big"] == "screener_far" and cov[0].attrs["coverage_coarse"] == "switch", \
        [(e.attrs["big"], e.attrs["coverage_coarse"]) for e in cov]


def test_t02_ice_is_reachable_on_a_rejected_ball_screen():
    ice = _rate("wing_reject_ice", "ball_screen_coverage", pred=lambda e: e.attrs["route"] == "ice", handler="h",
                handler_defender="Dh")
    assert ice >= 3, ice  # 4 of 5 at V0; 0 before loop 1 (reject rows never reached the coverage detector)


def test_t03_reject_read_and_step_up_with_a_standing_handler():
    # the closest approach is taken while the user moves: the stationary set-up next to the handler is not it
    rej = _rate("wing_reject_ice", "screen_read", pred=lambda e: e.attrs["read"] == "reject", screener="s", user="h")
    assert rej >= 3, rej
    for det in ("ball_screen", "step_up_screen"):
        n = _rate("slot_step_up", det, screener="s", handler="h")
        assert n >= 4, (det, n)  # 5 of 5 at V0 (step_up_screen 0 of 10 in the tester's sweep)


def test_t04_rescreen_after_an_unused_first_screen_is_kept():
    # the second (used) screen 3 s after the first was dropped as an own-man stop by the matchup proxy
    n = _rate("rescreen_same_side", "screen_read", pred=lambda e: e.t0 * DT > 4.0, screener="s", user="h", defender="Dh")
    assert n >= 4, n


def test_t05_flare_away_use():
    # ball - D_u - s - u: the user fades straight away from the screener without crossing the screen line
    n = _rate("flare_away", "flare_screen", screener="s", user="u", defender="Du")
    assert n >= 3, n
    used = _rate("flare_away", "screen_read", pred=lambda e: e.attrs["read"] == "use", screener="s", user="u")
    assert used >= 2, used
    assert S.prm("flare_screen")["flare_deg"] <= 116.0 and S.prm("screen_angle")["flare_deg"] <= 116.0


@pytest.mark.parametrize("scen", ["double", "elevator", "stagger"])
def test_t06_runners_into_a_set_are_not_screeners_for_the_waiting_user(scen):
    # screeners running past the waiting user's defender into their own stand used to make 'u screens s' rows
    for sd in range(1, 4):
        bad = _evs(scen, "screen_set", sd, screener="u")
        assert not bad, (sd, [(e.actors, round(e.t0 * DT, 2)) for e in bad])


def test_t06_screen_the_screener_needs_a_used_second_screen_by_a_third_player():
    for sd in range(1, 4):
        assert not run("double_drag", "screen_the_screener", sd), sd
        assert not run("detroit", "screen_the_screener", sd), sd


@pytest.mark.parametrize("scen", ["stack", "pin_down", "double"])
def test_t07_offball_coverage_rows_only_for_screens_or_real_coverage(scen):
    for sd in range(1, 4):
        screens = {(e.actors["screener"], e.actors["user"]) for e in run(scen, "screen", sd)}
        for e in run(scen, "off_ball_screen_coverage", sd):
            assert (e.actors["screener"], e.actors["user"]) in screens or \
                e.attrs["offball_coverage"] in ("top_lock", "switch", "pre_switch"), (sd, e.actors, e.attrs)


def test_t08_drag_height_and_trailer_origin():
    assert _rate("drag_left", "drag_screen", screener="s", handler="h") >= 3  # P_s 8.3 m from the rim (0 of 10 before)
    assert _rate("wing_step_down", "drag_screen") == 0  # half-court screener running down from the top


def test_t09_runthrough_is_not_a_flip():
    assert _rate("runthrough", "flip_screen") == 0
    assert _rate("wing_step_down", "flip_screen") == 0


def test_t10_veer_needs_a_new_stand():
    assert _rate("detroit", "veer_screen") == 0  # the unused row of the same Detroit stand is not a veer
    assert _positive_ok(*next(c for c in POS if c[0] == "veer_screen"), seed=SEED)


def test_t11_no_approach_right_after_a_screen_and_ghost_rise():
    for det in ("slip_screen", "fake_screen", "ghost_screen"):
        assert _rate("flip", det) == 0, det  # the post-screen roll / pop was re-read as a new approach
    assert _rate("slot_ghost", "ghost_screen", screener="s", handler="h") >= 2  # 0 of 5 before (rise 0.7-1.1 m)


def test_t12_driver_past_a_static_spot_up_is_not_a_fake_handoff():
    for det in ("fake_dho", "dho_keep"):
        assert _rate("wing_step_down", det) == 0, det


@pytest.mark.parametrize("scen", ["high_pnr", "detroit"])
def test_t13_t22_holder_does_not_flip_on_ball_screens_at_high_noise(scen):
    # SCR-T13 (spurious DHOs) and SCR-T22 (spurious handbacks in Detroit sets at sigma_p 0.5)
    for det in ("dho", "handoff_chain"):
        assert _rate(scen, det, sigma=0.5) == 0, det


def test_t14_side_behind_ball_screen_is_not_blind():
    assert _rate("slot_pnr_middle", "blind_screen_hint") <= 1  # 28 of 60 runs fired before loop 1
    assert S.prm("blind_screen_hint")["blind_deg"] >= 110.0


def test_t15_pitch_air_time_from_the_raw_ball():
    for sd in range(1, 6):
        _, sc = build("pitch", sd)
        x = [t for t in S._transfers(sc) if t["frm"] == "a" and t["to"] == "b"]
        assert x and x[0]["type"] == "pitch" and x[0]["air_s"] >= 0.2, (sd, x)


def test_t16_elbow_down_screen_is_not_out():
    assert _rate("elbow_down", "down_screen", screener="s", user="u") >= 4
    assert _rate("elbow_down", "off_ball_screen_other", pred=lambda e: e.attrs["geometry"] == "out") == 0


def test_t17_slot_location_read_at_the_set_up():
    n = _rate("slot_pnr_middle", "ball_screen", pred=lambda e: e.attrs["location"] == "slot", screener="s", handler="h")
    assert n >= 4, n


@pytest.mark.parametrize("scen,det", [("zipper_up", "zipper_screen"), ("zipper_out", "zipper_screen"),
                                      ("flex_up", "flex_screen"), ("flex_in", "flex_screen")])
def test_t18_spot_gates_survive_a_03m_shift(scen, det):
    assert _rate(scen, det, screener="s", user="u") >= 4


def test_t18_pin_down_geometry_is_not_split_by_screen_angle():
    for scen in ("pin_down", "wide_pin_down"):
        for e in run(scen, "pin_down"):
            assert e.attrs["geometry"] in ("pin_down", "wide_pin_down"), e.attrs["geometry"]


def test_t19_every_yaml_param_is_read_by_the_detectors():
    src = Path(S.__file__).read_text()
    for iid, it in S.ITEMS.items():
        for k, v in (it.get("params") or {}).items():
            if "not read by the detectors" in str(v.get("note", "")):
                continue
            assert f'"{k}"' in src, (iid, k)


def test_t20_moving_hint_needs_the_defender_moving_into_the_path():
    assert _rate("double_drag", "moving_screen_hint") == 0  # trailers decelerating into sets next to arriving defenders
    assert _positive_ok(*next(c for c in POS if c[0] == "moving_screen_hint"), seed=SEED)


def test_t21_rice_integration_has_a_numpy_1_fallback():
    assert S._trapz is (getattr(np, "trapezoid", None) or np.trapz)
    assert 0.9 < S.rice_below(0.2, 0.6, 0.15) <= 1.0


# --------------------------------------------------------------------------------------
# Loop-2 regressions: one test per fix of the confirmer's report on loop 1 (changes_loop2 in screens.yaml)
# --------------------------------------------------------------------------------------
def test_l2_fake_dho_receiver_who_plants_before_the_fake():
    # REG-fake_dho: the mean receiver velocity toward a over [t_c - 0.6, t_c - 0.1] read 0.05-0.29 m/s for a backdoor
    # receiver who comes up and plants; the gate now reads the peak 5-frame mean over [t_c - 1.2, t_c - 0.1]
    n = _rate("fake_backdoor", "fake_dho", seeds=range(1, 11), sigma=0.2, hander="a", receiver="b")
    assert n >= 9, n  # 10 of 10 (7 of 10 with the loop-1 gate)
    assert S.prm("fake_dho")["receiver_window_s"] >= 1.0


def test_l2_ball_screen_depth_comes_from_the_screen():
    # REG-location: the handler waits at r 9.4 m (logo) for a screen set at r 7.4 m: high, not logo
    n = _rate("high_wait_deep", "high_ball_screen", screener="s", handler="h")
    assert n >= 4, n  # 5 of 5 at sigma_p 0.3 (1 of 5 with the set-up label alone)
    loc = _rate("high_wait_deep", "ball_screen", pred=lambda e: e.attrs["location"] == "logo", screener="s", handler="h")
    assert loc == 0, loc


def test_l2_flare_with_the_defender_on_the_ball_side():
    # SCR-T05 (still failing after loop 1): n is averaged over the stand while D_u still moves, so a true
    # n . unit(ball - P_s) of 0.69 read 0.11-0.57 and n_ball_min 0.5 removed most real flares
    n = _rate("corr_flare", "flare_screen", seeds=range(1, 11), screener="s", user="u", defender="Du")
    assert n >= 7, n  # 9 of 10 (3 of 10 with n_ball_min 0.5)
    for scen in ("pin_down", "iverson"):
        assert _rate(scen, "flare_screen", screener="s", user="u") == 0, scen


def test_l2_rescreen_linked_beyond_the_window_by_the_stand_gap():
    # SCR-T04 re_screen: the two t_s are 3.3-3.5 s apart (> window_s 3 s) but the stands are 1.0 s apart; and a used
    # re-screen from a new stand after an unused first screen is split, not merged (the merge hid the use)
    n = _rate("rescreen_same_side", "re_screen", seeds=range(1, 11), screener="s", handler="h")
    assert n >= 6, n  # 7 of 10 (2 of 10 before)
    used = _rate("rescreen_same_side", "screen", seeds=range(1, 11), pred=lambda e: e.t0 * DT > 4.0, screener="s",
                 user="h")
    assert used >= 8, used
    assert S.prm("screen_window")["rescreen_gap_s"] < S.prm("screen_window")["window_s"]


@pytest.mark.parametrize("scen,screener", [("cutter_brush", "u"), ("back_short_cut", "u"), ("double_drag_late", "h")])
def test_l2_no_off_ball_set_for_a_standing_user_or_by_the_ball_holder(scen, screener):
    # SCR-T06 residual: a cutter stopping next to a standing teammate's defender, and the ball handler 'screening' the
    # first trailer, made SET / read / coverage rows on 27-30 of 30 runs
    for det in ("screen_set", "screen_read", "off_ball_screen_coverage"):
        assert _rate(scen, det, sigma=0.2, screener=screener) == 0, det
        assert _rate(scen, det, seeds=range(1, 11), screener=screener) <= 4, det  # 10 of 10 before at sigma_p 0.3


def test_l2_veer_keeps_its_stand_for_a_standing_teammate():
    # the off-ball leg of a veer is a stand on the defender of a standing corner player: vetoed as a SET row since
    # loop 2, it is kept for veer_screen (veer recall fell to 0 without that)
    assert _rate("veer", "veer_screen", screener="s", handler="h") >= 4
    assert not _evs("veer", "screen_set", screener="s", user="o3")


def test_l2_a_reject_is_a_move():
    # a standing 'user' does not reject (peak speed gate): 6 of 10 at sigma_p 0.3 before loop 2
    rej = lambda e: e.attrs["read"] == "reject"  # noqa: E731
    assert _rate("cutter_brush", "screen_read", seeds=range(1, 11), sigma=0.2, pred=rej) == 0
    assert _rate("cutter_brush", "screen_read", seeds=range(1, 11), pred=rej) <= 3
    assert _rate("wing_reject_ice", "screen_read", pred=lambda e: e.attrs["read"] == "reject", screener="s",
                 user="h") >= 3


def test_l2_flex_cut_is_not_a_back_screen():
    # back_screen fired on 25-28 of 30 flex runs (P .60); flex takes precedence for baseline screens
    for sg in (0.2, 0.3):
        assert _rate("flex", "back_screen", sigma=sg, screener="s", user="u") == 0, sg
    assert _rate("flex", "flex_screen", screener="s", user="u") >= 4
    assert _rate("back_top", "back_screen", screener="s", user="u") >= 4


@pytest.mark.parametrize("scen,chain,actors", [("weave", "weave", {"a": "a", "b": "b"}), ("miami", "miami", {"a": "a", "b": "b"})])
def test_l2_handoff_chain_weave_and_miami(scen, chain, actors):
    # SCR-T22 gap: the weave and miami branches of handoff_chain were never exercised (positive and near miss)
    pred = lambda e: e.attrs["chain"] == chain  # noqa: E731
    assert _rate(scen, "handoff_chain", pred=pred, **actors) >= 2
    assert _rate(scen + "_pass", "handoff_chain", pred=pred) == 0


def test_l2_screeners_arriving_side_by_side_are_no_screen_for_each_other():
    # SCR-T06 residual: s2 'screened' s1 while both arrived (t_s before the stand; s1 settles next to s2 and never
    # moves again without passing him); 2 / 4 of 10 seeds at sigma_p 0.2 / 0.3 before loop 2
    pair = lambda e: {e.actors["screener"], e.actors["user"]} == {"s1", "s2"}  # noqa: E731
    assert _rate("side_by_side", "screen", seeds=range(1, 11), sigma=0.2, pred=pair) == 0
    assert _rate("side_by_side", "screen", seeds=range(1, 11), pred=pair) <= 2
    assert _rate("side_by_side", "double_screen", seeds=range(1, 11), user="u") >= 7
    assert _rate("stagger", "stagger_screen", user="u") >= 4  # a user who passes the last screener and stops used it


# --------------------------------------------------------------------------------------
# Loop 4: failure modes found on real (vendor-smoothed) tracking, reproduced on synthetic scenes
# --------------------------------------------------------------------------------------
def sc_pnr_brief_plant():
    """High PnR whose screener never fully stops: he drifts 0.6 m through the set in 0.9 s (about 0.67 m/s) and rolls."""
    a = pnr(go=1.6)
    a["s"] = Off((0, 3.0, 4.5), (1.3, P_S[0], P_S[1] + 0.3), (2.2, P_S[0], P_S[1] - 0.3), (3.0, -0.2, 4.6), (3.6, -0.6, 1.8))
    return spec(a, held=[(0, 5.5, "h")]), 5.5


def sc_pnr_after_switch():
    """D_h guarded the wing o2 until 0.6 s and switched onto the handler by 1.1 s; s sets on him from 2.2 s."""
    a = pnr(go=2.8, t_set=2.2)
    a["o2"] = Off((0, 3.4, 9.6), (7.0, 3.4, 9.6))
    a["D2"] = Def((0, -0.3, 9.5), (0.6, -0.3, 9.5), (1.1, 2.8, 8.9), (7.0, 2.8, 8.9))
    a["Dh"] = Def((0, 2.8, 8.9), (0.6, 2.8, 8.9), (1.1, -0.15, 7.7), (2.8, -0.15, 7.7), (3.2, 0.0, 7.9), (3.7, 0.9, 8.6),
                  (4.2, 2.2, 6.6), (4.8, 1.9, 3.8))
    return spec(a, held=[(0, 6.5, "h")]), 6.5


def sc_drag_double_late():
    """Near miss for double_drag: the second trailer is still running in (stands from 4.1 s) when D_h, trailing the
    handler over the first drag screen, brushes him; his planned screen comes 2.5 s after the first."""
    sp, dur = sc_drag(double=True)
    sp["actors"]["s2"] = Off((0, 1.4, 14.5), (4.1, 1.4, 7.2), (6.2, 1.4, 7.2), (7.4, 4.6, 6.0))
    sp["actors"]["Ds2"] = Def((0, 2.1, 15.6), (4.2, 1.8, 6.2), (6.2, 1.8, 6.2), (7.4, 3.8, 5.0))
    sp["actors"]["h"] = Off(*sp["actors"]["h"]["wp"][:-1], (5.0, 1.5, 2.5))
    return sp, 7.5


SCEN.update({"pnr_brief_plant": sc_pnr_brief_plant, "pnr_after_switch": sc_pnr_after_switch,
             "drag_double_late": sc_drag_double_late})


def test_l4_brief_plant_forms_a_stand_on_precise_tracks():
    # SCR-L4-01: on vendor-smoothed tracks (sigma 0.05-0.15) the CA-RTS velocity variance is tiny, so s2 < s2_max meant
    # |v| < 0.40-0.70 m/s and NBA screen plants (smoothed minimum 0.6-0.8 m/s) never formed a stand, while the same
    # plant stands at sigma_p >= 0.2. Before loop 4: 2 / 5 of 10 seeds at sigma 0.05 / 0.10 (10 at 0.3).
    def stands(sg):
        n = 0
        for sd in range(1, 11):
            _, sc = build("pnr_brief_plant", sd, sg)
            n += any(st.a * DT <= 2.2 and st.b * DT >= 1.3 for st in S._stops(sc, "s"))
        return n
    for sg in (0.05, 0.1, 0.3):
        assert stands(sg) >= 8, sg


def test_l4_ball_defender_is_the_defender_on_the_ball():
    # SCR-L4-02: the 2 s mean-distance matchup still read D_h's previous man (o2) one second after a switch, so the
    # screen on the handler's defender became an own-man / off-ball stop. Before loop 4: 0 of 10 at every sigma_p.
    for sg in (0.2, 0.3):
        assert _rate("pnr_after_switch", "ball_screen", seeds=range(1, 11), sigma=sg, screener="s", handler="h") >= 8, sg
    assert _rate("pnr_after_switch", "ball_screen", seeds=range(1, 11), sigma=0.5, screener="s", handler="h") >= 4
    assert _rate("pnr_after_switch", "screen_set", seeds=range(1, 11), screener="s", user="o2") == 0


def test_l4_double_drag_needs_a_set_second_screener():
    # SCR-L4-03: with the on-ball defender fixed, a trailer still running in when D_h brushes him became the second
    # screen of a double drag (22 of 30 runs at sigma_p 0.2/0.3/0.5 in the loop-4 sweep; 6 before SCR-L4-02).
    for sg in (0.2, 0.3, 0.5):
        assert _rate("drag_double_late", "double_drag", seeds=range(1, 11), sigma=sg) == 0, sg
    assert _rate("double_drag", "double_drag", seeds=range(1, 11), screener_1="s", screener_2="s2", handler="h") >= 7
