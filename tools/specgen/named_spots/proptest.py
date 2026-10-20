"""Bounded property tests for named_spots (fixed seeds)."""
import sys, math, random, collections, re, time
from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parent))
from spotlib import load, C, is_three, court_region
doc, SP = load()
R = random.Random(20261020)
bad = collections.defaultdict(list)
CTXN = re.compile(r'\b(bx|by|hx|hy|ax_|ay_|ball_side|dribbling|lowest_defender_y|lowest_attacker_y|px|py|sx|sy|n_off_in_paint|team_centroid_x|team_centroid_y|t_since_catch_s|game_clock_s|shot_clock_s)\b')
static = [s for s in SP.values() if s.code and not CTXN.search(s.d['expr']) and 'z' not in s.names and s.side != 'table_side']
def pt():
    return R.uniform(-8.5, 8.5), R.uniform(-2.5, 28.0)
t0 = time.time()
# 1 mirror symmetry (static entries), 30k points
for _ in range(30000):
    x, y = pt()
    for s in static:
        if s.side == 'mirrored':
            a = s.inside(x, y, side='right' if x >= 0 else 'left'); b = s.inside(-x, y, side='right' if -x >= 0 else 'left')
            if x != 0 and a != b: bad['mirror:' + s.id].append((x, y))
        elif s.side == 'centre':
            if s.inside(x, y) != s.inside(-x, y) and x != 0: bad['centre_sym:' + s.id].append((x, y))
print('mirror done', time.time() - t0)
# 2 partitions on random points (no overlaps; court_region full)
parts = collections.defaultdict(list)
for e in doc['entries']:
    if e.get('partition') and e.get('expr') and not CTXN.search(e['expr']) and 'z' not in SP[e['id']].names: parts[e['layer']].append(SP[e['id']])
for _ in range(40000):
    x, y = pt()
    for k, sp in parts.items():
        n = sum(len(s.labels(x, y)) for s in sp)
        if n > 1: bad['overlap:' + k].append((x, y))
        if k == 'zone_scheme:court_region' and n != 1: bad['cr_cover'].append((x, y))
print('partitions done', time.time() - t0)
# 3 monotonicity along rays: three never turns back to two moving away from rim (in bounds)
for _ in range(4000):
    a = math.radians(R.uniform(-15, 195)); prev = None
    for k in range(0, 1300):
        r = 5.5 + k * 0.002; x, y = r * math.cos(a), r * math.sin(a)
        if abs(x) >= C['SIDE_X'] or y <= C['END_Y']: break
        th = is_three(x, y); cr = court_region(SP, x, y)[0]
        if th != cr.replace('_right', '').replace('_left', '').endswith('_three'): bad['cr_vs_is_three'].append((x, y, cr))
        if prev and not th: bad['ray_back_to_two'].append((math.degrees(a), r))
        prev = th
print('rays done', time.time() - t0)
# 4 boundary ownership: points exactly on lines must be false for non-oob_ok entries
for _ in range(3000):
    for (x, y) in ((C['SIDE_X'] * R.choice([1, -1]), R.uniform(-1.6, 27.0)), (R.uniform(-7.6, 7.6), C['END_Y']), (R.uniform(-7.6, 7.6), C['FAR_END_Y'])):
        for s in static:
            if not s.d.get('oob_ok') and s.labels(x, y): bad['owns_line:' + s.id].append((x, y))
print('lines done', time.time() - t0)
# 5 context gating and z gating
ctxents = [s for s in SP.values() if s.code and s.ctx]
for s in ctxents:
    if s.inside(1.0, 5.0) is not None: bad['ctx_not_gated:' + s.id].append(1)
    if s.inside(1.0, 5.0, bx=float('nan'), by=5, hx=1, hy=5, ax_=1, ay_=4) is not None and {'bx', 'by'} & s.ctx: bad['nan_ctx:' + s.id].append(1)
for s in SP.values():
    if s.code and 'z' in s.names and s.inside(0.1, 0.1) is not None: bad['z_not_gated:' + s.id].append(1)
print('gating done', time.time() - t0)
# 6 corner vs above-break consistency for threes in the frontcourt
CORNER = ['corner_three', 'nba_corner_3', 'ctg_corner_3', 'three_depth_corner', 'pbpstats_corner3']
ABOVE = ['above_the_break', 'above_the_break_three', 'nba_above_the_break_3', 'ctg_non_corner_3', 'pbpstats_arc3']
for _ in range(60000):
    x, y = R.uniform(-7.61, 7.61), R.uniform(-1.6, 3.5)
    if not is_three(x, y): continue
    corner = y <= C['BREAK_Y']
    for e in CORNER:
        if e in SP and bool(SP[e].labels(x, y)) != corner: bad['corner:' + e].append((x, y))
    for e in ABOVE:
        if e in SP and bool(SP[e].labels(x, y)) != (not corner): bad['above:' + e].append((x, y))
print('corner done', time.time() - t0)
for k, v in sorted(bad.items()): print(k, len(v), v[:2])
print('TOTAL issue kinds', len(bad))
