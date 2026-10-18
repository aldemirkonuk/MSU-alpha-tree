import re, glob, os, sys, yaml
sys.path.insert(0, os.path.dirname(__file__))
from core import NODES
import dom_a, dom_bc, dom_de, dom_fg, dom_hk, dom_lm, dom_extra  # noqa

REPO = "/Users/aldemirkonuk/Projects/MSU-Alpha-3"
SCR = "/private/tmp/claude-501/-Users-aldemirkonuk-Projects-MSU-Alpha-3/db1dcec6-4be3-4cc7-9218-9378ebfe1b46/scratchpad"

REQS = {}
for line in open(f"{SCR}/live_doc/requirement_ids.md"):
    m = re.match(r"- (R-[A-Z]+-\d+) \[([^\]]+)\]: (.*)", line)
    if m:
        REQS[m.group(1)] = (m.group(2), m.group(3))

COMMON = ['source', 'source_ref', 'pulled_at_utc', 'transform_version', 'model_version', 'confidence', 'dq_flag', 'pass', 'licence_class', 'schema_version']
TABLES = {}
for f in glob.glob(f"{REPO}/schema/tables/*.yaml"):
    d = yaml.safe_load(open(f))
    cols = d.get('columns') or {}
    names = [c.get('name') for c in cols] if isinstance(cols, list) else list(cols)
    TABLES[os.path.basename(f)[:-5]] = set(map(str, names)) | set(COMMON)
CARD = set(open(f"{REPO}/docs/data/templates/player_card_template.csv").readline().strip().split(","))


def check():
    errs = []
    ids = set()
    for n in NODES:
        if n['id'] in ids:
            errs.append(f"dup id {n['id']}")
        ids.add(n['id'])
    for n in NODES:
        if n['parent'] != 'ROOT' and n['parent'] not in ids:
            errs.append(f"{n['id']}: parent {n['parent']} missing")
        if not n['leaf']:
            continue
        for r in n['requirement_ids']:
            if r not in REQS:
                errs.append(f"{n['id']}: unknown req {r}")
        for t in n['tables']:
            if t.startswith('config/') or t.startswith('schema/'):
                if not os.path.exists(f"{REPO}/{t}"):
                    errs.append(f"{n['id']}: missing file {t}")
                continue
            if '.' in t:
                tb, col = t.split('.', 1)
                if tb == 'player_card':
                    if col not in CARD:
                        errs.append(f"{n['id']}: card field {col}")
                elif tb not in TABLES:
                    errs.append(f"{n['id']}: unknown table {tb}")
                elif col not in TABLES[tb]:
                    errs.append(f"{n['id']}: unknown column {t}")
            elif t not in TABLES:
                errs.append(f"{n['id']}: unknown table {t}")
        if n['status'] != 'covered' and not n['gaps']:
            errs.append(f"{n['id']}: {n['status']} without gap")
        if n['status'] == 'covered' and n['gaps']:
            errs.append(f"{n['id']}: covered with gap")
        if n['status'] == 'covered' and not n['requirement_ids']:
            errs.append(f"{n['id']}: covered without requirement")
    return errs


if __name__ == "__main__":
    e = check()
    print("\n".join(e) or "OK")
    leaves = [n for n in NODES if n['leaf']]
    print(len(leaves), "leaves")
    used = set(r for n in leaves for r in n['requirement_ids'])
    print("requirements referenced:", len(used), "of", len(REQS))
    unref = sorted(set(REQS) - used)
    print("unreferenced:", " ".join(unref))
    usedt = set(t.split('.')[0] for n in leaves for t in n['tables'])
    print("tables unreferenced:", sorted(set(TABLES) - usedt))
