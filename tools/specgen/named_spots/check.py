"""Validate config/named_spots.yaml: whitelist, anchors, probes (static and with context), mirrors,
value probes, text lints, ranks, frame counts, on-the-line rules, thin regions and partitions.

Usage: python tools/specgen/named_spots/check.py [--step 0.05] [--write-summary]

--write-summary stores the result in results/named_spots_test/check_summary.json. The page
docs/data/named_spots.md prints its test numbers from that file, and gen_doc.py refuses a summary
made from other rules (spotlib.rules_sha).

Probe fields of an entry:
  anchor, probes_inside, probes_outside   points that must be inside / outside the expr
  probe_ctx                               the context (ball, handler, ...) those points are run with;
                                          required when the expr uses a context name
  probes_ctx                              extra probes, each with its own context and wanted result
  probes_values                           value_exprs probes: point, context, wanted numbers (or null)
Every entry with an expr must have at least one executed probe.
"""
import argparse, ast, collections, json, math, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from spotlib import C, CTX_NAMES, MIRROR_X, Values, frames_for, load, rules_sha  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
SUMMARY = ROOT / "results" / "named_spots_test" / "check_summary.json"
NO_CTX = {"table_side_x_sign"}  # supplied by the venue, not by the play
LOG_FIELDS = ("review_fixes_2026_10_20", "review_fixes_2026_11_11", "supersedes", "sources", "variants_not_adopted")
FAMILY_RANK = dict(canonical=0, painted=0, interior=1, perimeter=2, defensive=3, restart=4, rule=5, review=5,
                   shot_zone=6, empirical=7, repo=8)
BALL_GATED = ("zone_scheme:2-3", "zone_scheme:1-3-1", "zone_scheme:1-1-3", "zone_scheme:1-2-2", "zone_scheme:2-1-2",
              "zone_scheme:3-2", "zone_scheme:box_and_1", "zone_scheme:diamond_and_1", "zone_scheme:triangle_and_2")


def needs_ctx(s):
    return bool(s.ctx - NO_CTX)


# ---------------------------------------------------------------- probes
def _side(s, x):
    return "right" if (s.side != "mirrored" or x >= 0) else "left"


def _mirror_ctx(ctx):
    return {k: (-v if k in MIRROR_X and v is not None else v) for k, v in ctx.items()}


def run_entry(e, s):
    """Run every probe of one entry. Returns (failures, executed count)."""
    fails, n = [], 0
    ctx_need = s.ctx - NO_CTX
    base = dict(e.get("probe_ctx") or {})
    if s.side == "table_side":
        base.setdefault("table_side_x_sign", 1)
    allowed = set(s.ctx) | ({"bx", "by"} if "ball_side" in s.ctx else set())
    stray = sorted(set(e.get("probe_ctx") or {}) - allowed)
    if stray:
        fails.append(("probe_ctx_unused", stray))

    def ev(p, ctx, z_default):
        x, y = p[0], p[1]
        z = p[2] if len(p) > 2 and p[2] is not None else z_default
        return s.inside(x, y, z, side=_side(s, x), **ctx)

    zd = 0.0 if "z" in s.names else None
    a = e.get("anchor") or {}
    has_anchor = a.get("x") is not None and a.get("y") is not None
    listed = bool(e.get("probes_inside") or e.get("probes_outside"))
    if ctx_need and not e.get("probe_ctx"):
        if has_anchor or listed:
            fails.append(("probes_need_ctx", sorted(ctx_need)))
    else:
        if has_anchor:
            p = [a["x"], a["y"], a.get("z")]
            n += 1
            if ev(p, base, zd) is not True:
                fails.append(("anchor", p[:2]))
            if s.side == "mirrored" and a["x"] > 0:
                n += 1
                if ev([-a["x"], a["y"], a.get("z")], _mirror_ctx(base), zd) is not True:
                    fails.append(("mirror", p[:2]))
        for p in e.get("probes_inside") or []:
            n += 1
            if ev(p, base, zd) is not True:
                fails.append(("probe_in", p))
        for p in e.get("probes_outside") or []:
            n += 1
            # a side label is written for the right: its outside probes are statements about the right label
            z = p[2] if len(p) > 2 and p[2] is not None else zd
            if s.inside(p[0], p[1], z, side="right", **base) is not False:
                fails.append(("probe_out", p))
    for pr in e.get("probes_ctx") or []:
        n += 1
        if ev(pr["p"], pr.get("ctx", {}), None) != pr.get("want"):
            fails.append(("probe_ctx", pr))
    return fails, n


def value_probes(e):
    """Run probes_values of an entry with value_exprs. Returns (failures, executed count)."""
    fails, n = [], 0
    if not e.get("value_exprs"):
        return fails, n
    vals = Values(e["value_exprs"])
    tol = float(e.get("probes_values_tolerance", 5e-4))
    for pr in e.get("probes_values") or []:
        p = pr["p"]
        got = vals.at(p[0], p[1], p[2] if len(p) > 2 else None, **(pr.get("ctx") or {}))
        for name, want in pr["want"].items():
            n += 1
            g = got.get(name, "missing")
            ok = (g is None) if want is None else (isinstance(g, float) and abs(g - want) <= tol)
            if not ok:
                fails.append(("value", p, pr.get("ctx"), name, want, g))
    untested = sorted(set(e["value_exprs"]) - {k for pr in e.get("probes_values") or [] for k in pr["want"]})
    if untested:
        fails.append(("value_without_probe", untested))
    return fails, n


def probe_report(doc, spots):
    """Returns (bad, counts): failures by kind, and executed probes per entry id."""
    bad = collections.defaultdict(list)
    counts = {}
    for e in doc["entries"]:
        s = spots[e["id"]]
        if s.code is not None:
            fails, n = run_entry(e, s)
            counts[e["id"]] = n
            for f in fails:
                bad[f[0]].append((e["id"],) + tuple(f[1:]))
            if n == 0:
                bad["no_probe"].append(e["id"])
        vf, vn = value_probes(e)
        if vn:
            counts[e["id"]] = counts.get(e["id"], 0) + vn
        for f in vf:
            bad[f[0]].append((e["id"],) + tuple(f[1:]))
    return bad, counts


# ---------------------------------------------------------------- text lints
def walk(o, path=""):
    if isinstance(o, str):
        yield path, o
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, f"{path}.{k}" if path else str(k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from walk(v, f"{path}[{i}]")


def all_texts(doc, logs=False):
    """Yield (owner, path, text) for every string of the file; the review logs only when logs=True."""
    for k, v in doc.items():
        if k == "entries":
            for e in v:
                for p, s in walk(e):
                    if logs or p.split(".")[0].split("[")[0] not in LOG_FIELDS:
                        yield e["id"], p, s
        elif k != "journal" or logs:
            for p, s in walk(v, k):
                yield "(top)", p, s


EDIT_START = re.compile(r"^\s*(Replace|Append|Add|Insert|Prepend|Delete|Remove|Change|Rewrite|Rename|Move|Update)\b[ :'\"]")
EDIT_INSIDE = re.compile(r"\[also:|\bReplace '|\bReplace the '|\bAppend(?: to [^:]{0,40})?: '")


def lint_edit_instructions(doc):
    """A text field must hold the text itself, never an instruction on how to edit it (NS-01)."""
    out = []
    for owner, p, s in all_texts(doc):
        if p in ("id", "layer", "expr"):
            continue
        if EDIT_START.search(s) or EDIT_INSIDE.search(s):
            out.append((owner, p, s[:80]))
    return out


FRAME_PAT = re.compile(
    r"(?P<pre>.{0,60}?)(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>ms|s)\b(?P<mid>[^().;]{0,45})\((?:about )?(?P<n>\d+) frames?(?: indices)?(?: at 29\.97 fps)?\)")
FRAME_REV = re.compile(r"(?P<n>\d+)(?: consecutive)? frames \((?:elapsed )?(?:>= )?(?P<val>\d+(?:\.\d+)?) (?P<unit>ms|s)\)")


def frame_mode(pre):
    """How the words before a duration read: 'up to' / '<=' -> at_most, '>' / 'longer than' -> more_than, else at_least."""
    if re.search(r"(up to|at most|<=)\s*$", pre):
        return "at_most"
    if re.search(r"(longer than|more than|>)\s*$", pre):
        return "more_than"
    return "at_least"


def frame_counts_in(text):
    """Yield (seconds, mode, frames written, frames by spotlib.frames_for) for each '(N frames)' with a time."""
    for m in FRAME_PAT.finditer(text):
        sec = float(m.group("val")) / (1000.0 if m.group("unit") == "ms" else 1.0)
        mode = frame_mode(m.group("pre"))
        yield sec, mode, int(m.group("n")), frames_for(sec, mode), m.group(0)[-60:]
    for m in FRAME_REV.finditer(text):
        sec = float(m.group("val")) / (1000.0 if m.group("unit") == "ms" else 1.0)
        yield sec, "at_least", int(m.group("n")), frames_for(sec, "at_least"), m.group(0)


def lint_frame_counts(doc, extra_texts=()):
    """Every frame count in brackets must equal frames_for(its time) (rule_frame_timing; NS-10)."""
    out = []
    texts = list(all_texts(doc)) + [("(page)", name, t) for name, t in extra_texts]
    for owner, p, s in texts:
        for sec, mode, n, want, where in frame_counts_in(s):
            if n != want:
                out.append((owner, p, f"{sec} s {mode}: written {n}, frames_for gives {want}", where))
    return out


def lint_ranks(doc):
    """rank = family_rank * 1000 + priority on every entry (rule_label_precedence; NS-09)."""
    out = []
    for e in doc["entries"]:
        missing = [k for k in ("name", "side", "family", "priority", "rank", "source_kind", "confidence") if e.get(k) is None]
        if missing:
            out.append((e["id"], "missing " + ", ".join(missing)))
            continue
        want = FAMILY_RANK[e["family"]] * 1000 + e["priority"]
        if e["rank"] != want:
            out.append((e["id"], f"rank {e['rank']} != {want}"))
    return out


def label_counts(doc, spots):
    """Side-qualified labels (a mirrored entry counts twice), and those whose expr needs no context and no z."""
    total = static = 0
    for e in doc["entries"]:
        s = spots[e["id"]]
        if s.code is None:
            continue
        k = 2 if s.side == "mirrored" else 1
        total += k
        if not s.ctx and "z" not in s.names:
            static += k
    return {"side_qualified": total, "static_no_context_no_z": static}


def lint_blocks(doc, spots):
    """Lists and counts in the YAML header must agree with the entries (NS-05, NS-08, NS-12)."""
    out = []
    ids = {e["id"] for e in doc["entries"]}
    real = collections.Counter(e["layer"] for e in doc["entries"])
    decl = doc.get("layer_counts", {})
    for k in sorted(set(real) | set(decl)):
        if real.get(k) != decl.get(k):
            out.append(("layer_counts", k, decl.get(k), real.get(k)))
    for i in doc["loader"]["temporal"]["probability_only"]:
        if i not in ids:
            out.append(("probability_only", i, "not an entry id"))
    names = doc.get("context_names") or {}
    if set(names) != CTX_NAMES:
        out.append(("context_names", sorted(set(names) ^ CTX_NAMES), "differs from spotlib.CTX_NAMES"))
    for n, d in names.items():
        if not all(d.get(k) for k in ("what", "unit", "none_when")):
            out.append(("context_names", n, "needs what, unit and none_when"))
    got = label_counts(doc, spots)
    if doc.get("label_counts") != got:
        out.append(("label_counts", doc.get("label_counts"), got))
    for owner, p, s in all_texts(doc):
        for m in re.finditer(r"(\d+) of the (\d+) side-qualified labels", s):
            if (int(m.group(1)), int(m.group(2))) != (got["static_no_context_no_z"], got["side_qualified"]):
                out.append(("label_counts_text", owner, m.group(0)))
    ties = doc.get("tie_rules") or {}
    for k in ties.get("provider_bins", []):
        if k not in real:
            out.append(("tie_rules", k, "not a layer"))
    return out


# ---------------------------------------------------------------- thin regions (probability_only)
_DIRS = [(math.cos(2 * math.pi * k / 32), math.sin(2 * math.pi * k / 32)) for k in range(32)]


def _clearance(inside, x, y, cap=0.30, step=0.01):
    """Distance from an inside point to the nearest outside point, along 32 rays, up to cap."""
    best = cap
    for dx, dy in _DIRS:
        d = step
        while d < best:
            if not inside(x + dx * d, y + dy * d):
                best = d
                break
            d += step
    return best


def thin_regions(doc, spots, only=None):
    """{id: (h, widest clearance found)} for entries whose own region is thinner than the buffer h of their class.

    probability_only_rule: an entry is thin when the inscribed radius of its region is below h at sigma 0.30
    (painted or rule-book: max(0.10, 0.5 x 0.30) = 0.15 m; convention: max(0.25, 0.75 x 0.30) = 0.25 m; an
    entry's own temporal block overrides). Measured from the entry's anchor and inside probes, then on a 2 cm
    lattice around them. Entries that need context or height are not measured.
    """
    out = {}
    for e in doc["entries"]:
        s = spots[e["id"]]
        if s.code is None or needs_ctx(s) or "z" in s.names or (only is not None and e["id"] not in only):
            continue
        a = e.get("anchor") or {}
        pts = [tuple(p[:2]) for p in (e.get("probes_inside") or [])]
        if a.get("x") is not None and a.get("y") is not None:
            pts.append((a["x"], a["y"]))
        if not pts:
            continue
        kw = {"table_side_x_sign": 1} if s.side == "table_side" else {}
        inside = lambda x, y: bool(s.inside(x, y, side=_side(s, x), **kw))  # noqa: E731
        painted = "rule_book" in str(e.get("source_kind")) or e.get("family") == "painted"
        h = 0.15 if painted else 0.25
        t = e.get("temporal") or {}
        if t.get("h_min_m") is not None:
            h = max(t["h_min_m"], t.get("h_k_sigma", 0.5 if painted else 0.75) * 0.30)
        best = max((_clearance(inside, *p) for p in pts if inside(*p)), default=0.0)
        if best < h:
            for (px, py) in pts:
                for i in range(-15, 16):
                    for j in range(-15, 16):
                        x, y = px + i * 0.02, py + j * 0.02
                        if inside(x, y):
                            best = max(best, _clearance(inside, x, y))
                        if best >= h:
                            break
                    if best >= h:
                        break
                if best >= h:
                    break
        if best < h:
            out[e["id"]] = (h, round(best, 3))
    return out


def lint_probability_only(doc, spots, only=None):
    """Every thin region must be on loader.temporal.probability_only (NS-08)."""
    listed = set(doc["loader"]["temporal"]["probability_only"])
    thin = thin_regions(doc, spots, only)
    return [(i, f"inscribed radius {r} m < h {h} m, not on the probability_only list") for i, (h, r) in sorted(thin.items()) if i not in listed]


# ---------------------------------------------------------------- text against expr
_VARS = {"x", "ax", "y", "r", "m", "t", "bx", "by", "hx", "hy"}
_FLIP = {"<": ">", "<=": ">=", ">": "<", ">=": "<="}
_NEG = {"<": ">=", "<=": ">", ">": "<=", ">=": "<"}
_OPS = {ast.Lt: "<", ast.LtE: "<=", ast.Gt: ">", ast.GtE: ">="}


def _val(n):
    try:
        return eval(compile(ast.Expression(n), "c", "eval"), {"__builtins__": {}}, dict(C))
    except Exception:
        return None


def _var(n, fold=True):
    if isinstance(n, ast.Name) and n.id in _VARS:
        return {"ax": "x"}.get(n.id, n.id) if fold else n.id
    if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "abs" and isinstance(n.args[0], ast.Name) \
            and n.args[0].id in ("x", "bx", "hx"):
        return n.args[0].id if fold else "a" + n.args[0].id
    if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "hypot" and len(n.args) == 2 \
            and all(isinstance(a, ast.Name) for a in n.args) and {a.id for a in n.args} == {"x", "y"}:
        return "r"
    if isinstance(n, ast.IfExp) and ast.unparse(n) == "ax - CORNER_X if y <= BREAK_Y else r - ARC_R":
        return "d3"
    return None


def expr_comparisons(expr, fold=True, signed=False):
    """(var, constant, op) for every var-against-constant comparison. signed=True applies 'not' to the op."""
    out = set()

    def visit(n, neg):
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            visit(n.operand, not neg)
        elif isinstance(n, ast.BoolOp):
            for v in n.values:
                visit(v, neg)
        elif isinstance(n, ast.Compare):
            terms = [n.left] + n.comparators
            for a, op, b in zip(terms, n.ops, terms[1:]):
                o = _OPS.get(type(op))
                if not o:
                    continue
                va, vb = _var(a, fold), _var(b, fold)
                if va and not vb and _val(b) is not None:
                    v, c = va, _val(b)
                elif vb and not va and _val(a) is not None:
                    v, c, o = vb, _val(a), _FLIP[o]
                else:
                    continue
                out.add((v, round(c, 3 if not signed else 4), _NEG[o] if (signed and neg) else o))
        elif isinstance(n, ast.Expression):
            visit(n.body, neg)

    visit(ast.parse(expr, mode="eval"), False)
    return out


_NUM = r"-?\d+(?:\.\d+)?"
_TOK = rf"(?:{_NUM}|[A-Z][A-Z_0-9]{{2,}}(?:\s*-\s*LINE_W)?)"
_TVAR = r"(?:\|x\||\|bx\||\|hx\||abs\(x\)|x|y|r|m|theta|t|bx|by|hx|hy)"
_OP = r"(?:<=|>=|<|>)"
_CHAIN = re.compile(rf"(?<![\w.])({_TOK})\s*({_OP})\s*({_TVAR})(?![\w(])(?:\s*({_OP})\s*({_TOK}))?")
_PLAIN = re.compile(rf"(?<![\w.|])({_TVAR})\s*({_OP})\s*({_TOK})(?![\w])")


def _cval(s):
    s = s.strip()
    try:
        return round(float(s), 3)
    except ValueError:
        pass
    try:
        return round(eval(s, {"__builtins__": {}}, dict(C)), 3)
    except Exception:
        return None


def _vname(v):
    return {"theta": "t"}.get(v.strip("|").replace("abs(x)", "x"), v.strip("|").replace("abs(x)", "x"))


def text_comparisons(text):
    """(var, constant, op as 'var op constant', span of the operator, flipped) for inequalities written in prose."""
    out = []
    chained = set()  # where a variable already read as part of 'constant op var [op constant]' starts
    for m in _CHAIN.finditer(text):
        lo, op1, v, op2, hi = m.groups()
        chained.add(m.start(3))
        if _cval(lo) is not None:
            out.append((_vname(v), _cval(lo), _FLIP[op1], m.span(2), True))
        if op2 and _cval(hi) is not None:
            out.append((_vname(v), _cval(hi), op2, m.span(4), False))
    for m in _PLAIN.finditer(text):
        if m.start(1) in chained:
            continue
        v, op, c = m.groups()
        if _cval(c) is not None:
            out.append((_vname(v), _cval(c), op, m.span(2), False))
    return out


def text_expr_mismatches(e):
    """Places where the words give a line to the other side than the expr does (same line, other strictness)."""
    if not e.get("expr"):
        return []
    by = collections.defaultdict(set)
    for v, c, o in expr_comparisons(e["expr"]):
        by[(v, c)].add(o)
    out = []
    for fld in ("bounds_text", "plain"):
        tx = e.get(fld)
        if not tx:
            continue
        for v, c, o, span, flipped in text_comparisons(tx):
            same_way = [p for p in by.get((v, c), ()) if p.rstrip("=") == o.rstrip("=")]
            if same_way and o not in same_way:
                out.append((fld, v, c, o, same_way[0], span, flipped))
    return out


def lint_text_vs_expr(doc):
    return [(e["id"], f, f"{v} {o} {c} in words, {v} {want} {c} in the expr")
            for e in doc["entries"] for f, v, c, o, want, _, _ in text_expr_mismatches(e)]


# ---------------------------------------------------------------- on-the-line (tie) rules
def lint_ties(doc, spots):
    """Inside one of our own partition schemes a shared line belongs to the zone nearer the rim (edge rules).

    Checked on every var-against-constant line of a scheme: r, y, |x|, angle m and the three-point offset d3
    must be written (lo, hi], that is 'v <= c' on the near side and 'v > c' on the far side. Lines with
    y < 0 are the other way round (nearer the rim is larger y). Exempt: the court boundary lines (their own
    edge rule), x = 0 (right owns), schemes listed in tie_rules.provider_bins, and the single lines listed in
    tie_rules.exceptions. The division line edge is checked in every scheme.
    """
    rules = doc.get("tie_rules") or {}
    provider = set(rules.get("provider_bins", []))
    exc = {(x["scheme"], x["var"], round(float(x["value"]), 4)) for x in rules.get("exceptions", [])}
    nearer_line = set(rules.get("nearer_three_point_line", []))
    skip = {round(C["SIDE_X"], 4), round(C["END_Y"], 4), round(C["FAR_END_Y"], 4), 0.0}
    schemes = collections.defaultdict(list)
    for e in doc["entries"]:
        if e.get("partition") and e.get("expr") and not needs_ctx(spots[e["id"]]) and "z" not in spots[e["id"]].names:
            schemes[e["layer"]].append(e)
    out, used = [], set()
    for layer, es in schemes.items():
        lines = collections.defaultdict(list)
        for e in es:
            for v, c, o in expr_comparisons(e["expr"], fold=False, signed=True):
                if v == "x" and e.get("side") == "mirrored":
                    v = "ax"
                if v in ("ax", "y", "r", "m", "d3"):
                    lines[(v, c)].append((o, e["id"]))
        for (v, c), lst in sorted(lines.items()):
            ops = {o for o, _ in lst}
            if c in skip or not (ops & {"<", "<="} and ops & {">", ">="}):
                continue
            half = round(C["HALF_Y"], 4)
            if layer in provider and not (v == "y" and c == half):
                continue
            want = {"<=", ">"}
            if (v == "y" and c < 0) or (layer in nearer_line and v == "d3" and c < 0):
                want = {"<", ">="}
            if ops <= want:
                continue
            if (layer, v, c) in exc:
                used.add((layer, v, c))
                continue
            out.append((layer, v, c, sorted(lst)))
    for x in sorted(exc - used):
        out.append(("unused exception",) + x)
    return out


def ball_gate(expr):
    """The part of an expr that tests only the ball (compiled), or None."""
    tree = ast.parse(expr, mode="eval").body
    parts = tree.values if isinstance(tree, ast.BoolOp) and isinstance(tree.op, ast.And) else [tree]
    names = lambda n: {m.id for m in ast.walk(n) if isinstance(m, ast.Name)}  # noqa: E731
    gate = [p for p in parts if names(p) & {"bx", "by", "ball_side"} and not names(p) & (CTX_NAMES | {"x", "y", "z", "ax", "r", "m", "t"}) - {"bx", "by", "ball_side"}]
    if not gate:
        return None
    node = ast.Expression(ast.BoolOp(ast.And(), gate) if len(gate) > 1 else gate[0])
    return compile(ast.fix_missing_locations(node), "gate", "eval")


def lint_ball_gates(doc, spots):
    """A zone-defence slot is switched on by the ball's zone, so its ball test must be a union of whole ball zones."""
    zones = [spots[e["id"]] for e in doc["entries"] if e["layer"] == "zone_scheme:ball_zone"]
    xs = [0.0, 0.5, 0.89, 0.9, 0.91, 2.59, 2.6, 2.61, 4.99, 5.0, 5.01, 6.0, 7.61]
    ys = [-1.59, 0.0, 1.41, C["BREAK_Y"], 1.42, 2.99, 3.0, 3.01, 4.0, 5.19, 5.2, 5.21, 8.0, 12.69, 12.7]
    lab = {}
    for p in [(sx * x, y) for x in xs for y in ys for sx in (1, -1)]:
        z = [l for s in zones for l in s.labels(*p)]
        if len(z) != 1:
            return [("ball_zone", p, z)]
        lab[p] = z[0]
    out = []
    for e in doc["entries"]:
        if e["layer"] not in BALL_GATED or not e.get("expr"):
            continue
        code = ball_gate(e["expr"])
        if code is None:
            continue
        for sign in ((1, -1) if e.get("side") == "mirrored" else (1,)):
            seen = collections.defaultdict(set)
            for (bx, by), z in lab.items():
                b = bx * sign
                env = dict(C, abs=abs, min=min, max=max, bx=b, by=by, ball_side=0 if abs(b) < 0.9 else (1 if b > 0 else -1))
                seen[z].add(bool(eval(code, {"__builtins__": {}}, env)))
            split = sorted(z for z, v in seen.items() if len(v) > 1)
            if split:
                out.append((e["id"], "ball test cuts through", split))
    return out


# ---------------------------------------------------------------- all entry checks
def entry_checks(doc, spots):
    """Every check that needs no grid. An empty result means the file is sound."""
    bad, _ = probe_report(doc, spots)
    for kind, fn in (("edit_instruction", lambda: lint_edit_instructions(doc)),
                     ("frame_count", lambda: lint_frame_counts(doc)),
                     ("rank", lambda: lint_ranks(doc)),
                     ("header_block", lambda: lint_blocks(doc, spots)),
                     ("text_vs_expr", lambda: lint_text_vs_expr(doc)),
                     ("tie_rule", lambda: lint_ties(doc, spots)),
                     ("ball_gate", lambda: lint_ball_gates(doc, spots))):
        got = fn()
        if got:
            bad[kind] = got
    return bad


def partition_checks(doc, spots, step):
    schemes = collections.defaultdict(list)
    for e in doc["entries"]:
        if e.get("partition") and e.get("expr") and not needs_ctx(spots[e["id"]]):
            schemes[e["layer"]].append(spots[e["id"]])
    nx, ny = int(18 / step) + 1, int(32 / step) + 1
    out = {}
    for name, sp in schemes.items():
        cover = over = 0
        for i in range(nx):
            x = round(-9 + i * step, 4)
            for j in range(ny):
                y = round(-3 + j * step, 4)
                n = sum(len(s.labels(x, y)) for s in sp)
                cover += n > 0
                over += n > 1
        out[name] = {"points": nx * ny, "covered": cover, "overlaps": over}
    return out


def in_bounds_points(step):
    """Grid points strictly inside the boundary lines (the floor the crosswalks must cover)."""
    nx, ny = int(18 / step) + 1, int(32 / step) + 1
    n = 0
    for i in range(nx):
        x = round(-9 + i * step, 4)
        if abs(x) >= C["SIDE_X"]:
            continue
        for j in range(ny):
            y = round(-3 + j * step, 4)
            n += C["END_Y"] < y < C["FAR_END_Y"]
    return n


def probe_summary(doc, spots, counts):
    static = [i for i, s in spots.items() if s.code and not needs_ctx(s)]
    ctx = [i for i, s in spots.items() if s.code and needs_ctx(s)]
    return {"entries_with_expr": len(static) + len(ctx),
            "static_entries": len(static), "context_entries": len(ctx),
            "entries_with_zero_probes": sum(1 for i in static + ctx if not counts.get(i)),
            "probes_executed": sum(counts.values()),
            "probes_executed_static": sum(counts.get(i, 0) for i in static),
            "probes_executed_context": sum(counts.get(i, 0) for i in ctx),
            "value_probes_executed": sum(n for i, n in counts.items() if spots[i].code is None)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", type=float, default=0.05)
    ap.add_argument("--write-summary", action="store_true", help=f"store the result in {SUMMARY.relative_to(ROOT)}")
    a = ap.parse_args()
    doc, spots = load()
    bad, counts = probe_report(doc, spots)
    bad = entry_checks(doc, spots)
    thin = thin_regions(doc, spots)
    listed = doc["loader"]["temporal"]["probability_only"]
    not_listed = sorted(set(thin) - set(listed))
    if not_listed:
        bad["probability_only_rule"] = not_listed
    part = partition_checks(doc, spots, a.step)
    out = {"version": str(doc["version"]), "rules_sha256": rules_sha(doc), "step_m": a.step,
           "entries": len(doc["entries"]), "with_expr": sum(1 for s in spots.values() if s.code),
           "probes": probe_summary(doc, spots, counts), "label_counts": label_counts(doc, spots),
           "in_bounds_points": in_bounds_points(a.step),
           "thin_regions": {"thin": len(thin), "thin_not_on_list": len(not_listed), "probability_only_list": len(listed),
                            "listed_for_another_reason": sorted(set(listed) - set(thin))},
           "entry_failures": {k: v for k, v in bad.items()}, "partitions": part}
    text = json.dumps(out, indent=1, default=str)
    print(text)
    full = part.get("zone_scheme:court_region", {})
    ok = not bad and full.get("covered") == full.get("points") and full.get("overlaps") == 0 \
        and all(p["overlaps"] == 0 for p in part.values())
    if a.write_summary:
        if not ok:
            sys.exit("check failed: summary not written")
        SUMMARY.write_text(text + "\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
