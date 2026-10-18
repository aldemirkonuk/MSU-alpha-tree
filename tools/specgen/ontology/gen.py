import os, sys, re, yaml
from collections import Counter, OrderedDict, defaultdict
sys.path.insert(0, os.path.dirname(__file__))
from validate import NODES, REQS, TABLES, check, REPO

errs = [e for e in check() if 'config/game_ontology.yaml' not in e]
assert not errs, errs

NODES.sort(key=lambda n: [int(p) if p.isdigit() else p for p in n['id'].split('.')])
byid = {n['id']: n for n in NODES}
leaves = [n for n in NODES if n['leaf']]
domains = [n for n in NODES if n['parent'] == 'ROOT']

# ---------------------------------------------------------------- proposed IDs
START = {'IV': 35, 'PC': 6, 'FD': 2, 'DS': 2, 'SY': 2, 'MK': 19}
counter = defaultdict(int)
proposals = []
for n in leaves:
    for g in n['gaps']:
        if g['kind'] == 'new':
            fam = g['fam']
            num = START.get(fam, 1) + counter[fam]
            counter[fam] += 1
            g['pid'] = f"new-{fam}-{num}"
            g['leaf'] = n['id']
            g['domain'] = n['id'][0]
            proposals.append(g)

existing = [(n, g) for n in leaves for g in n['gaps'] if g['kind'] == 'existing']

TOP15 = ["A.06.17", "A.01.10", "A.06.11", "A.03.06", "B.01.02", "A.06.06", "E.04.05", "E.02.06",
         "A.04.12", "A.08.07", "A.09.02", "H.04.06", "D.07.04", "G.01.04", "M.01.06"]
WHY = {
    "A.06.17": "Every foul is stored by class only; the contact mechanism (hand-check, hold, push, block, illegal screen, landing space ...) that physicality questions and the 2026-27 points of emphasis need is not captured anywhere.",
    "A.01.10": "Rule constants live in three files (court config, invariants config, requirement text) with no edition key; 35 s-era games, the 2025-26 challenge and 2026-27 appeals need per-season rules or checks will misfire on older games.",
    "A.06.11": "The live doc's 9 foul types include `intentional`, a class the 2026-27 rules book does not have; foul counts by type will not reconcile with the rules or the box score.",
    "A.03.06": "Shot-clock reset causes are 6 coarse values while the rules (and config/invariants.yaml) list 33; no-reset stoppages are not recorded, so R-SY-09 cannot check most stoppages.",
    "B.01.02": "Court config lacks line widths, centre circle, lane spaces, backboard, ring diameter, 28-ft marks; out-of-bounds, lane occupancy, jump-ball formation and bank shots depend on them, and R-CG-01 still fails (verified: false).",
    "A.06.06": "Block/charge calls do not store restricted-area status or whether the defender was a secondary defender; a central officiating and defensive-value question.",
    "E.04.05": "Shot contest is only a distance; hand up vs not and hand-to-ball distance drive shot quality more than distance alone.",
    "E.02.06": "Shot fakes, pass fakes and jab steps are absent from the event model; they are among the most common creation actions and defender-discipline measures.",
    "A.04.12": "Frontcourt status is not stored; backcourt violations, the 10-second count and the shot-clock 30 s backcourt rules cannot be checked.",
    "A.08.07": "Over-and-back backcourt violations have no turnover code (only 10-second), so turnover types will not reconcile with PBP.",
    "A.09.02": "Out-of-bounds plays do not store who touched the ball last; needed for coach's-challenge modelling, turnover credit and R-SY-10 matching.",
    "H.04.06": "Defensive value is credited mostly through steals, blocks and matchups; contests, rotations and rim deterrence have no credit rule.",
    "D.07.04": "Lineup composition (size, shooters, handlers) is not a feature anywhere, yet every lineup, matchup and engine level needs it.",
    "G.01.04": "Where the defence picks up the ball (full, three-quarter, half court) is not measured; it defines pressure and press usage.",
    "M.01.06": "Each source's own definitions (possession, assist, fast break, shot zone) are not stored as data, so cross-source checks cannot explain disagreements.",
}


def esc(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


# ---------------------------------------------------------------- YAML
def ynode(n):
    d = dict(id=n['id'], name=n['name'], parent=n['parent'])
    if n['definition']:
        d['definition'] = n['definition']
    if not n['leaf']:
        d['leaf'] = False
        return dict(d)
    d['leaf'] = True
    d['rule_ref'] = n['rule_ref'] or None
    d['vocab'] = n['vocab']
    d['tables'] = n['tables']
    d['requirement_ids'] = n['requirement_ids']
    d['status'] = n['status']
    if n['note']:
        d['note'] = n['note']
    gl = []
    for g in n['gaps']:
        if g['kind'] == 'new':
            gl.append(dict(proposed_id=g['pid'], tier=g['tier'], text=g['text'], acceptance=g['acc'], implies=g['change'], priority=g['prio']))
        else:
            key = 'see' if g['ids'][0].startswith('(') else 'existing_proposal'
            gl.append({key: " ".join(g['ids']).strip('()'), 'note': g['note'] or None})
    if gl:
        d['gaps'] = gl
    return dict(d)


stats = {}
for dnode in domains:
    c = Counter(n['status'] for n in leaves if n['id'][0] == dnode['id'])
    stats[dnode['id']] = dict(name=dnode['name'], leaves=sum(c.values()), covered=c['covered'], partial=c['partial'], missing=c['missing'])
tot = Counter(n['status'] for n in leaves)
famc = Counter(p['fam'] for p in proposals)

header = f"""# Game ontology of a college basketball game: every aspect, categorised, with its coverage.
# Status: PROPOSAL (2026-10-18, prompt 003 coverage audit). The requirements session approves; nothing here is final.
# Human-readable view and gap list: docs/data/game_ontology_coverage.md. Inbox for the requirements session:
# coord/requirements_inbox/007-game-ontology-gaps.md.
#
# Node fields: id, name, parent, definition, leaf; leaves also carry
#   rule_ref         2026-27 NCAA Men's Rules Book reference (Rule-Section.Article; App. = appendix), docs/rules/PRMBB_RulesBook.pdf
#   vocab            controlled vocabulary: OFF.F<n> (docs/taxonomy/offense_full.md), DEF.F<n> (defense_full.md),
#                    MS (motion_starts.md), TR.ST/TR.PH/TR.RO (docs/research/transition_full.md), global_metadata enums,
#                    config/vocabulary_map.yaml
#   tables           schema/tables/<table>.yaml columns as <table>.<column>; player_card.<field> = docs/data/templates/player_card_template.csv;
#                    config/... and schema/... = files
#   requirement_ids  exact IDs of the live requirements export of 2026-10-18 (518 IDs, 43 families)
#   status           covered = a requirement names it AND a table/column stores it (and its vocabulary exists);
#                    partial = one of these is missing or incomplete, or only a repo proposal (new-IV-xx) covers it;
#                    missing = neither a requirement nor a store exists
#   gaps             proposed_id new-<FAMILY>-n (numbering continues after IDs already proposed in the repo) or existing_proposal
# Validated: every requirement ID exists in the export; every <table>.<column> exists in schema/tables; all 518 IDs and
# all {len(TABLES)} schema tables map to at least one leaf.
"""
doc = dict(
    version="0.1.0", status="proposed", date="2026-10-18",
    sources=["live requirements export 2026-10-18 (requirements_main.md, requirement_ids.md, hypothesis_candidates.md)",
             "docs/rules/PRMBB_RulesBook.pdf (2026-27), PRMBB_CaseBook.pdf, 2025-26PRMBB_RulesChanges.pdf, 2026-27PRMBB_PostClinicInterpretations.pdf",
             "docs/taxonomy/*.md", "docs/research/*.md", "docs/data/*.md", "schema/tables/*.yaml", "schema/global_metadata.yaml", "config/*.yaml"],
    summary=dict(leaves=len(leaves), covered=tot['covered'], partial=tot['partial'], missing=tot['missing'],
                        proposed_new_requirements=len(proposals), gaps_closed_by_existing_repo_proposals=len(existing),
                        per_domain={k: v for k, v in stats.items()}, proposals_per_family=dict(sorted(famc.items()))),
    nodes=[ynode(n) for n in NODES])
yml = header + yaml.safe_dump(dict(doc), sort_keys=False, allow_unicode=True, width=10000)
open(f"{REPO}/config/game_ontology.yaml", "w").write(yml)
yaml.safe_load(open(f"{REPO}/config/game_ontology.yaml"))

# ---------------------------------------------------------------- Markdown
md = []
A = md.append
A("# Game ontology and requirements coverage audit")
A("")
A("Written 2026-10-18 for prompt 003 (coverage audit). Status: **proposal** for the requirements session; nothing here changes the live doc. Machine-readable twin: `config/game_ontology.yaml` (same IDs, generated from one source). Inbox: `coord/requirements_inbox/007-game-ontology-gaps.md`.")
A("")
A("**Goal (Aldemir):** requirements so complete that every part of a basketball game is configured, with each aspect categorised. This file lists every aspect of a college basketball game as a tree of leaf concepts, maps each leaf to the requirement IDs, tables, columns, vocabularies and rule-book articles that cover it today, and proposes a requirement for every leaf that is only partly covered or not covered.")
A("")
A("## How to read this")
A("")
A(f"- **Inputs read:** the live requirements export of 18 Oct (518 IDs in 43 families, `requirements_main.md`, `requirement_ids.md`, `hypothesis_candidates.md`); the 2026-27 NCAA Men's Rules Book, Case Book, 2025-26 rules changes and 2026-27 post-clinic interpretations (`docs/rules/`, text from `pdftotext -layout`); `docs/taxonomy/*.md`; `docs/research/*.md`; `docs/data/*.md`; `schema/tables/*.yaml` ({len(TABLES)} tables); `schema/global_metadata.yaml`; `config/*.yaml`.")
A("- **Rule references** use Rule-Section.Article of the 2026-27 book (e.g. 2-11.6.d.1); `App.` is an appendix (App. III officiating guidelines, App. VIII signals).")
A("- **Vocabulary codes:** `OFF.F<n>` offense taxonomy, `DEF.F<n>` defense taxonomy, `MS` motion starts, `TR.ST`/`TR.PH`/`TR.RO` transition start types, phases and roles, enum names from `schema/global_metadata.yaml`, and `config/vocabulary_map.yaml`.")
A("- **Tables** are `<table>.<column>` from `schema/tables/*.yaml`; `player_card.<field>` is the W1 card template.")
A("- **Status:** **covered** = a requirement names the concept and a table/column stores it (with its vocabulary); **partial** = one of the two is missing or incomplete (e.g. enum lacks values the rules book defines), or only a repo proposal not yet in the live doc covers it (e.g. `new-IV-22` in `config/invariants.yaml`); **missing** = no requirement and no store.")
A("- **Proposed IDs** `new-<FAMILY>-n` continue after the IDs already proposed in the repo (new-IV-01..34, new-PC-1..5, new-FD-1, new-DS-1, new-SY-1, new-MK-10..18). The requirements session renumbers. One new family is proposed: **R-RL (rules layer)**, because no existing family owns the versioned rules edition that court constants (R-CG), invariants (R-IV), shot-clock rules (R-MD-06, R-SY-09) and timeout allotments all read from.")
A(f"- **Validation:** every requirement ID cited exists in the export; every `<table>.<column>` exists in the schema; all 518 requirement IDs and all {len(TABLES)} tables map to at least one leaf (reverse index at the end).")
A("")
A("## 1. Coverage statistics")
A("")
A("| Domain | Leaves | Covered | Partial | Missing | Covered % |")
A("| --- | ---: | ---: | ---: | ---: | ---: |")
for k, v in stats.items():
    A(f"| {k}. {v['name']} | {v['leaves']} | {v['covered']} | {v['partial']} | {v['missing']} | {100*v['covered']/v['leaves']:.0f}% |")
A(f"| **All** | **{len(leaves)}** | **{tot['covered']}** | **{tot['partial']}** | **{tot['missing']}** | **{100*tot['covered']/len(leaves):.0f}%** |")
A("")
A(f"Gaps: {tot['partial'] + tot['missing']} leaves are partial or missing. They get **{len(proposals)} proposed new requirements**; {len(existing)} gaps are closed (fully or in part) by proposals already in the repo, mainly the 34 `new-IV` invariants in `config/invariants.yaml` that the live doc has not adopted yet.")
A("")
A("Proposed new requirements per family:")
A("")
A("| Family | Proposed | Family | Proposed |")
A("| --- | ---: | --- | ---: |")
items = sorted(famc.items())
half = (len(items) + 1) // 2
for i in range(half):
    a = items[i]
    b = items[i + half] if i + half < len(items) else ("", "")
    A(f"| R-{a[0]} | {a[1]} | {('R-' + b[0]) if b[0] else ''} | {b[1]} |")
A("")
tier = Counter(p['tier'] for p in proposals)
A(f"Tier split: {tier['Shall']} Shall, {tier['Should']} Should.")
A("")
A("## 2. Key findings")
A("")
A(f"1. **Every one of the 518 requirement IDs and all {len(TABLES)} tables map to at least one leaf**, so nothing in the live doc is orphaned; the gaps are aspects of the game that no requirement names yet.")
A("2. **Rule-book mismatches.** The 9 foul types include `intentional`, which the 2026-27 book does not have (deliberate fouls are common fouls or Flagrant 1, Rule 4-15.2.c.1.d); the turnover list lacks the over-and-back backcourt violation (9-12) and the elbows violation (9-13); `shot_clock_resets.cause` has 6 values against 33 rule causes; the official-signal enum has 10 of about 50 Appendix VIII signals.")
A("3. **Rules are not versioned.** Constants are spread across `config/court_ncaa_men.yaml` (still `verified: false`), `config/invariants.yaml` and requirement text, with no rules edition per game; older 35 s-era games and the 2025-26 and 2026-27 changes need one (proposed R-RL family).")
A("4. **Court config is incomplete:** no line width, centre circle, lane-space marks, backboard, ring diameter, coaching box or 28-ft marks, though out-of-bounds, lane occupancy, jump-ball formations and bank shots depend on them.")
nIV = len([1 for n, g in existing if any(i.startswith("new-IV") for i in g["ids"])])
A(f"5. **34 invariants already proposed** (`new-IV-01..34`) would close {nIV} partial leaves here once the live doc adopts them (more are cited in leaf notes as support for covered leaves).")
pct = {k: round(100*v["covered"]/v["leaves"]) for k, v in stats.items()}
A(f"6. **Lowest coverage: court/equipment/venue (B, {pct['B']}%), rules (A, {pct['A']}%) and individual actions (E, {pct['E']}%).** In E: fakes, contest form, landing space, jumps, slides and backpedals, named cuts, finish subtypes, footwork and gather are not stored.")
A("7. **Officials' mechanics** (rotations, primary coverage areas, calling distance, full signal list, visible counts) are almost absent, although the 2026-27 points of emphasis are about them.")
A(f"8. **Tactics are well covered** (offence {pct['F']}%, defence {pct['G']}% covered) because the taxonomy files are wired into `set_instances`, `screens`, `scheme_states`; the remaining gaps are screener arrival, PnR spacing tags, paint touches, ball movement, pick-up point and lob protection.")
A("")
A("## 3. Top 15 gaps")
A("")
A("| Rank | Leaf | Proposed | Why it matters |")
A("| ---: | --- | --- | --- |")
for i, lid in enumerate(TOP15, 1):
    n = byid[lid]
    pids = ", ".join(g.get('pid', " ".join(g.get('ids', []))) for g in n['gaps'])
    A(f"| {i} | {lid} {esc(n['name'])} | {pids} | {esc(WHY[lid])} |")
A("")
A("## 4. Ontology tree")
A("")
A("Domains and groups with their leaves (status in brackets: C covered, P partial, M missing).")
A("")
A("```")
for n in NODES:
    depth = n['id'].count('.')
    if n['leaf']:
        A("    " * depth + f"{n['id']} {n['name']} [{n['status'][0].upper()}]")
    else:
        A("    " * depth + f"{n['id']} {n['name'].upper() if depth == 0 else n['name']}")
A("```")
A("")
A("## 5. Coverage matrix (per leaf)")
A("")
A("Gap column: proposed ID(s) for partial and missing leaves (details in section 6), or an existing repo proposal.")
for dnode in domains:
    A("")
    A(f"### {dnode['id']}. {dnode['name']}")
    A("")
    A(esc(dnode['definition']))
    A("")
    A("| ID | Leaf | Rule ref | Requirement IDs | Tables / columns | Vocab | Status | Gap |")
    A("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for n in leaves:
        if n['id'][0] != dnode['id']:
            continue
        gp = []
        for g in n['gaps']:
            gp.append(g['pid'] if g['kind'] == 'new' else (" ".join(g['ids']) if g['ids'][0].startswith('(') else "existing: " + " ".join(g['ids'])))
        name = esc(n['name']) + (f" — {esc(n['definition'])}" if n['definition'] and n['status'] != 'covered' else "")
        if n['note']:
            name += f" *(note: {esc(n['note'])})*"
        A(f"| {n['id']} | {name} | {esc(n['rule_ref'])} | {' '.join(n['requirement_ids'])} | {esc(', '.join(n['tables']))} | {esc(' '.join(n['vocab']))} | {n['status']} | {'; '.join(gp)} |")
A("")
A("## 6. Gap list: proposed new requirements")
A("")
A("One row per proposal. Units: m, s, degrees, m/s. Priority 1 = needed before the first processed games are trusted; 2 = needed for the value and tactics layers; 3 = completeness.")
A("")
A("| Proposed ID | Tier | Leaf | Requirement | Acceptance criterion | Table / vocabulary change | Priority |")
A("| --- | --- | --- | --- | --- | --- | ---: |")
for p in proposals:
    A(f"| {p['pid']} | {p['tier']} | {p['leaf']} {esc(byid[p['leaf']]['name'])} | {esc(p['text'])} | {esc(p['acc'])} | {esc(p['change'])} | {p['prio']} |")
A("")
A("### Gaps closed by proposals already in the repo")
A("")
A("| Leaf | Existing proposal or cross-reference | Note |")
A("| --- | --- | --- |")
for n, g in existing:
    A(f"| {n['id']} {esc(n['name'])} | {esc(' '.join(g['ids']))} | {esc(g['note'])} |")
A("")
A("## 7. Reverse index: requirement ID → leaves")
A("")
rev = defaultdict(list)
for n in leaves:
    for r in n['requirement_ids']:
        rev[r].append(n['id'])
fams = {}
for r in REQS:
    fams.setdefault(r.rsplit('-', 1)[0], []).append(r)
A("| Family | ID → leaves |")
A("| --- | --- |")
for f, ids in fams.items():
    A(f"| {f} | " + "; ".join(f"{r[len(f)+1:]}: {', '.join(rev[r])}" for r in ids) + " |")
A("")
A("## 8. Open questions for Aldemir")
A("")
OPEN = [
    "New family R-RL (rules layer) for a versioned rules edition per game: accept, or fold it into R-IV / R-CG?",
    "Drop `intentional` from the foul types and map it to rulebook classes (common foul + end-game flag, or Flagrant 1)?",
    "Rule 7-3.2.b boundary for throw-in spots: the 2025-26 change text (FT line extended) or the 2026-27 book text (imaginary line to the end-line corner)? (also open in docs/data/dictionary_state.md item 7)",
    "Adopt the 34 proposed invariants new-IV-01..34 into the live doc (they close 14 leaves here)?",
    "Add the missing Rule 1 marks to config/court_ncaa_men.yaml and then mark it `verified: true`?",
    "Officials' mechanics (rotations, primary coverage areas, calling distance, full signal list): label now or after gate G7?",
    "Fakes (shot fake, pass fake, jab step) and contest form (hand up, hand-to-ball distance) as Shall, given pose quality at broadcast distance is not yet measured?",
    "Bench side and scorers'-table side per game: you fill them from the broadcast at intake, or detected automatically?",
    "Conduct events (flopping, taunting, player gestures) and fighting/suspensions: in scope?",
    "NIL valuations on the player card: keep as public estimates (exploratory only) or drop?",
    "Public betting share for the market-input model variant: look for a free source, or out of scope?",
    "Context extras (ball model, rim type, court placement in domes, student-section end, crowd allegiance share): collect, or leave as Should with 'unknown'?",
]
for q in OPEN:
    A(f"- {q}")
A("")
open(f"{REPO}/docs/data/game_ontology_coverage.md", "w").write("\n".join(md))

# ---------------------------------------------------------------- Inbox 007
ib = []
B = ib.append
B("# Requirements inbox 007 · Game ontology coverage audit: gaps and proposed requirements")
B("")
B("From: prompt 003 coverage-audit agent (2026-10-18). To: requirements session. Status: proposal, not yet agreed with Aldemir.")
B("Source documents: `docs/data/game_ontology_coverage.md` (tree, per-leaf matrix, statistics, gap list, reverse index) and `config/game_ontology.yaml` (same content, machine-readable, validated with yaml.safe_load).")
B("Action: decide which proposals enter the live doc (renumber freely; each keeps its leaf ID so the mapping survives), adopt the existing repo proposals listed below, and answer the open questions. Nothing here edits the live doc, the schema or any config other than the new ontology file.")
B("")
B("Units: m, s, degrees, m/s, cm. Court positions r (m) and theta (degrees from the right baseline at the rim centre).")
B("")
B("## Counts")
B("")
B(f"- Leaves: {len(leaves)} in 13 domains. Covered {tot['covered']}, partial {tot['partial']}, missing {tot['missing']} ({100*tot['covered']/len(leaves):.0f}% covered).")
B("- Per domain (leaves / covered / partial / missing): " + "; ".join(f"{k} {v['leaves']}/{v['covered']}/{v['partial']}/{v['missing']}" for k, v in stats.items()) + ".")
B(f"- Proposed new requirements: {len(proposals)} ({tier['Shall']} Shall, {tier['Should']} Should). Per family: " + ", ".join(f"R-{k} {v}" for k, v in sorted(famc.items())) + ".")
B(f"- Gaps closed by proposals already in the repo: {len(existing)} (mostly new-IV-xx in config/invariants.yaml).")
B(f"- All 518 live requirement IDs and all {len(TABLES)} schema tables map to at least one leaf.")
B("- New family proposed: R-RL (rules layer): no existing family owns a versioned rules edition per game; R-CG holds court constants, R-IV invariants, R-MD-06/R-SY-09 shot-clock rules, but none versions them by season or competition.")
B("")
B("## Proposed requirements (one per line: ID · tier · text · acceptance · domain/leaf · implied change)")
B("")
for p in proposals:
    B(f"- {p['pid']} · {p['tier']} · {p['text']} · Acceptance: {p['acc']} · Domain {p['domain']}, leaf {p['leaf']} ({byid[p['leaf']]['name']}) · Implies: {p['change']}")
B("")
B("## Existing repo proposals that close gaps (adopt into the live doc)")
B("")
for n, g in existing:
    if g['ids'][0].startswith('new-'):
        B(f"- {' '.join(g['ids'])} → leaf {n['id']} ({n['name']}){': ' + g['note'] if g['note'] else ''}")
B("")
B("## Top 15 gaps")
B("")
for i, lid in enumerate(TOP15, 1):
    n = byid[lid]
    pids = ", ".join(g.get('pid', " ".join(g.get('ids', []))) for g in n['gaps'])
    B(f"{i}. {lid} {n['name']} ({pids}): {WHY[lid]}")
B("")
B("## Open questions for Aldemir (one line each)")
B("")
for q in OPEN:
    B(f"- {q}")
B("")
open(f"{REPO}/coord/requirements_inbox/007-game-ontology-gaps.md", "w").write("\n".join(ib))

print("leaves", len(leaves), dict(tot))
for k, v in stats.items():
    print(k, v)
print("proposals", len(proposals), dict(sorted(famc.items())), dict(tier))
print("existing", len(existing))
