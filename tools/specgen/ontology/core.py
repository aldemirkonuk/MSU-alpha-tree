# Core helpers for the game ontology generator (scratchpad only).
NODES = []   # list of dicts, in order


def D(code, name, definition):
    """Domain or group node (non-leaf)."""
    parent = code.rsplit(".", 1)[0] if "." in code else "ROOT"
    NODES.append(dict(id=code, name=name, parent=parent, definition=definition, leaf=False))


def G(fam, tier, text, acc, change, prio=3, domain=None):
    """A proposed new requirement for a partial or missing leaf."""
    return dict(kind="new", fam=fam, tier=tier, text=text, acc=acc, change=change, prio=prio)


def X(*ids, note=""):
    """Gap already covered by a proposal that exists in the repo (not yet in the live doc)."""
    return dict(kind="existing", ids=list(ids), note=note)


def L(code, name, definition, r="", req="", t="", v="", s="C", note="", gap=None, gap2=None):
    parent = code.rsplit(".", 1)[0]
    gaps = [g for g in (gap, gap2) if g]
    NODES.append(dict(
        id=code, name=name, parent=parent, definition=definition, leaf=True,
        rule_ref=r, requirement_ids=req.split(), tables=t.split(), vocab=v.split() if v else [],
        status={"C": "covered", "P": "partial", "M": "missing"}[s], note=note, gaps=gaps))


def EXT(code, req="", t="", v=""):
    """Add requirement IDs, tables or vocab to an existing leaf."""
    for n in NODES:
        if n['id'] == code:
            n['requirement_ids'] += [r for r in req.split() if r not in n['requirement_ids']]
            n['tables'] += [x for x in t.split() if x not in n['tables']]
            n['vocab'] += [x for x in v.split() if x not in n['vocab']]
            return
    raise KeyError(code)
