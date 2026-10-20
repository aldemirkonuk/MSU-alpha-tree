"""Reference evaluator for config/named_spots.yaml (spec tooling, not the production labeller).

Frame: attacked-rim frame, metres; theta from atan2(y, x) in degrees. Expressions are checked
against an AST whitelist before they are compiled. Missing positions give "unknown"; missing
context (ball, handler, assigned attacker) gives None, never False or out of bounds.
"""
import ast
import math
from pathlib import Path

import yaml

CONFIG = Path(__file__).resolve().parents[3] / "config" / "named_spots.yaml"

C = dict(RIM_Y_FROM_END=1.6002, END_Y=-1.6002, BOARD_Y=-0.381, LANE_X=1.8288, FT_Y=4.191,
         ARC_R=6.7501, CORNER_X=6.6008, BREAK_Y=1.4118, BREAK_T=12.073, RA_R=1.2700,
         HALF_Y=12.700, SIDE_X=7.62, FAR_END_Y=27.051, LINE_W=0.0508)


MAX_ABS_M = 100.0


def _fin(v):
    return v is not None and isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _ok(v):
    return _fin(v) and abs(v) <= MAX_ABS_M


def is_three(x, y):
    if y <= C["BREAK_Y"]:
        return abs(x) > C["CORNER_X"]
    return math.hypot(x, y) > C["ARC_R"]


def fold(t):
    if -90 <= t <= 90:
        return t
    return 180 - t if t > 90 else -180 - t


def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def seg_dist(p, a, b):
    ax_, ay_ = b[0] - a[0], b[1] - a[1]
    L = ax_ * ax_ + ay_ * ay_
    if L == 0:
        return dist(p, a)
    u = max(0.0, min(1.0, ((p[0] - a[0]) * ax_ + (p[1] - a[1]) * ay_) / L))
    return dist(p, (a[0] + u * ax_, a[1] + u * ay_))


BASE = dict(abs=abs, min=min, max=max, hypot=math.hypot, atan2=math.atan2, degrees=math.degrees,
            sqrt=math.sqrt, floor=math.floor, is_three=is_three, dist=dist, seg_dist=seg_dist, **C)


def env(x, y, z=None, **ctx):
    z = 0.0 if z is None else z
    t = math.degrees(math.atan2(y, x)) if (x or y) else 90.0
    e = dict(BASE, x=x, y=y, z=z, ax=abs(x), r=math.hypot(x, y), t=t, m=(math.degrees(math.atan2(y, abs(x))) if (x or y) else 90.0))
    bx = ctx.get("bx")
    if bx is not None:
        e["ball_side"] = 0 if abs(bx) < 0.9 else (1 if bx > 0 else -1)
    e.update(ctx)
    return e


CTX_NAMES = {"bx", "by", "hx", "hy", "ax_", "ay_", "ball_side", "dribbling", "lowest_defender_y", "px", "py",
             "sx", "sy", "n_off_in_paint", "team_centroid_x", "team_centroid_y", "t_since_catch_s", "table_side_x_sign",
             "lowest_attacker_y", "game_clock_s", "shot_clock_s"}
MIRROR_X = ("bx", "hx", "ax_", "px", "sx", "team_centroid_x")
POINT_NAMES = {"x", "y", "z", "ax", "r", "t", "m"}
OK_NODES = (ast.Expression, ast.BoolOp, ast.BinOp, ast.UnaryOp, ast.Compare, ast.IfExp, ast.Call, ast.Name,
            ast.Constant, ast.Load, ast.Tuple, ast.And, ast.Or, ast.Not, ast.USub, ast.UAdd, ast.Add, ast.Sub,
            ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv, ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Eq, ast.NotEq)


def check_expr(src):
    """Whitelist check: only arithmetic, comparisons, boolean logic and BASE functions."""
    tree = ast.parse(src, mode="eval")
    names = set()
    for n in ast.walk(tree):
        if not isinstance(n, OK_NODES):
            raise ValueError(f"disallowed syntax {type(n).__name__}")
        if isinstance(n, ast.Call) and not (isinstance(n.func, ast.Name) and n.func.id in BASE):
            raise ValueError("call to a non-whitelisted function")
        if isinstance(n, ast.Constant) and not isinstance(n.value, (int, float)):
            raise ValueError("non-numeric constant")
        if isinstance(n, ast.Name):
            names.add(n.id)
    unknown = names - set(BASE) - POINT_NAMES - CTX_NAMES
    if unknown:
        raise ValueError(f"unknown names {sorted(unknown)}")
    return names


class Spot:
    def __init__(self, d):
        self.d = d
        self.id = d["id"]
        self.side = d.get("side", "n/a")
        self.names = check_expr(d["expr"]) if d.get("expr") else set()
        self.ctx = self.names & CTX_NAMES
        self.code = compile(d["expr"], self.id, "eval") if d.get("expr") else None

    def inside(self, x, y, z=None, side="right", **ctx):
        if self.code is None:
            return None
        if not _ok(x) or not _ok(y):
            return None  # missing or non-finite position: label unknown, never out of bounds
        if "z" in self.names and not _ok(z):
            return None  # height needed but not measured: label absent (reason no_height)
        need = {"bx", "by"} if "ball_side" in self.ctx else set()
        if any(not _fin(ctx.get(k)) for k in (self.ctx - {"ball_side", "table_side_x_sign"}) | need):
            return None  # missing context: label absent (reason no_context)
        if self.side == "table_side":
            s_ = ctx.get("table_side_x_sign")
            if s_ not in (1, -1):
                return None
            x = x * s_
        if self.side == "mirrored" and (x < 0 if side == "right" else x >= 0):
            return False
        if self.side == "mirrored" and side == "left":
            x = -x
            ctx = {k: (-v if k in MIRROR_X and v is not None else v) for k, v in ctx.items()}
        return bool(eval(self.code, {"__builtins__": {}}, env(x, y, z, **ctx)))

    def labels(self, x, y, z=None, **ctx):
        """Return the side-qualified ids this point falls in."""
        out = []
        if not _ok(x) or not _ok(y):
            return []
        if self.side == "mirrored":
            for s in ("right", "left"):
                if self.inside(x, y, z, side=s, **ctx):
                    out.append(f"{self.id}_{s}")
        elif self.inside(x, y, z, **ctx):
            out.append(self.id)
        return out


def court_region(spots, x, y):
    """The canonical region label(s) of a point, or ["unknown"] when the position is missing."""
    if not _ok(x) or not _ok(y):
        return ["unknown"]
    return [l for s in spots.values() if s.d["layer"] == "zone_scheme:court_region" for l in s.labels(x, y)]


def load(path=CONFIG):
    """Return (document, {id: Spot}) for every entry with an expr."""
    doc = yaml.safe_load(Path(path).read_text())
    return doc, {e["id"]: Spot(e) for e in doc["entries"]}
