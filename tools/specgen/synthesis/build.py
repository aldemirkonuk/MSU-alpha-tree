import json, re, yaml, collections, sys, glob
sys.path.insert(0, '.')
from overrides import O
from clusters import C, DICT
from conflicts import K
from decisions import D
from spine import SP, DP

R = '/Users/aldemirkonuk/Projects/MSU-Alpha-3/'
d = json.load(open('parsed.json'))
live, order = d['live'], d['order']
AT = {t['id']: t for t in yaml.safe_load(open(R + 'docs/requirements_review/acceptance_tests.yaml'))['tests']}
leafname = d['leafname']
leaves_by_req = d['leaves_by_req']
cols_by_req = d['cols_by_req']
IDRX = r'new-[A-Z]{2}-[A-Z]?\d+'
FAM_NAME = {}
for l in open('/private/tmp/claude-501/-Users-aldemirkonuk-Projects-MSU-Alpha-3/db1dcec6-4be3-4cc7-9218-9378ebfe1b46/scratchpad/syn/../live_doc2/requirement_ids.md'):
    pass
QRT = open(R + 'docs/requirements_review/quality_review.md').read()
for m in re.finditer(r'^### (R-[A-Z]{2}): (.*?) \(\d+ IDs', QRT, re.M):
    FAM_NAME[m[1]] = m[2]
SRCNAME = {'Q': 'quality_review', 'A': 'espn_analyst', 'E': 'data_engineer', 'S': 'team_data_scientist',
           'R': 'rules_layer', 'G': 'gap_closures_round2', 'I': 'inbox007_or_invariants'}

def clean(s):
    s = re.sub(r'\*\*(.+?)\*\*\s*', lambda m: m[1].rstrip('.') + ': ', s)
    s = s.replace('`', '')
    return s.strip()

# ------------------------------------------------------------------ raw proposals
RAW = collections.OrderedDict()
def add(i, src, tier, text, acc, lands, leaves, **kw):
    assert i not in RAW, ('dup raw', i)
    RAW[i] = dict(id=i, src=src, tier=tier, text=clean(text), acc=clean(acc or ''), lands=clean(lands or ''), leaves=list(leaves or []), **kw)
for x in d['inbox007']:
    add(x['id'], 'inbox007 (game_ontology.yaml)', x['tier'], x['text'], x['acc'], x['lands'], [x['leaf']], prio007=x['prio'])
for x in d['r2']:
    lands = '; '.join(cols_by_req.get(x['id'], [])) or 'see docs/data/gap_closures_round2.md'
    add(x['id'], 'gap_closures_round2', x['tier'], x['text'], x['acc'], lands, x['leaf'], refines=x['refines'])
for x in d['ivnew']:
    add(x['id'], 'config/invariants.yaml', x['tier'], x['text'],
        '0 unreviewed breaks per game on both pilot games; scope ' + str(x['scope']) + '; on break: ' + str((x.get('on_break') or {}).get('action', 'review')),
        'config/invariants.yaml; tables: ' + ', '.join(x['tables'] or []), [])
for src, key in (('espn_analyst', 'ananew'), ('data_engineer', 'engnew'), ('team_data_scientist', 'scinew')):
    for x in d[key]:
        add(x['id'], src, x['tier'], x['text'], x['acc'], x['lands'], [])
DSRC = {'new-CG-2': 'docs/data/court_constants_check.md', 'new-RL-2': 'config/vocab/rules_edition.yaml'}
for k_, v in DICT.items():
    src = DSRC.get(k_, 'docs/data/dictionary_players.md (inbox 006)' if k_.startswith('new-PC') else 'docs/data/dictionary_games.md (inbox 006)')
    add(k_, src, v['tier'], v['text'], v['acc'], v['lands'], v['leaf'])
print('raw proposals', len(RAW))

# ------------------------------------------------------------------ clusters
assigned = {}
ABS = {}  # old id -> existing id
clusters = []
for cl in C:
    if cl['into']:
        assert cl['p'] in RAW, cl['p']
        assert cl['p'] not in assigned, cl['p']
        assert cl['into'] in live
        ABS[cl['p']] = (cl['into'], cl['note'])
        assigned[cl['p']] = 'ABS'
        continue
    mem = [cl['p']] + cl['m']
    for x in mem:
        assert x in RAW, ('unknown', x)
        assert x not in assigned, ('twice', x)
        assigned[x] = len(clusters)
    cl = dict(cl); cl['members'] = mem
    clusters.append(cl)
# auto-add refined inbox-007 ids to the cluster of the refining round-2 id
for x in d['r2']:
    for ref in x['refines']:
        if ref.startswith('new-IV'):
            continue
        if ref in assigned:
            continue
        ci = assigned[x['id']]
        assert ci != 'ABS'
        clusters[ci]['members'].append(ref)
        assigned[ref] = ci
missing = [i for i in RAW if i not in assigned]
assert not missing, missing

# family, numbering
PRI = {'P0': 0, 'P1': 1, 'P2': 2}
for n, cl in enumerate(clusters):
    cl['fam'] = cl['fam'] or re.match(r'new-([A-Z]{2})-', cl['p'])[1]
    cl['ord'] = n
byfam = collections.defaultdict(list)
for cl in clusters:
    byfam[cl['fam']].append(cl)
NMAP = {}
for fam in byfam:
    for j, cl in enumerate(sorted(byfam[fam], key=lambda c: (PRI[c['pr']], c['ord'])), 1):
        cl['nid'] = 'N-%s-%02d' % (fam, j)
        for x in cl['members']:
            NMAP[x] = cl['nid']

def res(tok):
    if tok in live:
        return tok
    if tok in NMAP:
        return NMAP[tok]
    if tok in ABS:
        return ABS[tok][0]
    raise KeyError(tok)
def subst(s):
    def f(m):
        try:
            return res(m[0])
        except KeyError:
            return m[0] + ' (unmapped)'
    return re.sub(IDRX + r'(?![0-9])', f, s)

# wanted-by: originating sources + mentions in other inputs
docs = {'espn_analyst': R + 'docs/requirements_review/perspective_espn_analyst.md',
        'data_engineer': R + 'docs/requirements_review/perspective_data_engineer.md',
        'team_data_scientist': R + 'docs/requirements_review/perspective_team_data_scientist.md',
        'quality_review': R + 'docs/requirements_review/quality_review.md'}
mentions = collections.defaultdict(set)
for who, p in docs.items():
    for i in set(re.findall(IDRX, open(p).read())):
        mentions[i].add(who)
for p in glob.glob(R + 'config/vocab/*.yaml') + [R + 'docs/data/court_constants_check.md']:
    for i in set(re.findall(IDRX, open(p).read())):
        mentions[i].add('rules_layer')
SRCW = {'inbox007 (game_ontology.yaml)': 'ontology_audit_inbox007', 'gap_closures_round2': 'gap_closures_round2',
        'config/invariants.yaml': 'invariants_rules', 'espn_analyst': 'espn_analyst', 'data_engineer': 'data_engineer',
        'team_data_scientist': 'team_data_scientist', 'docs/data/court_constants_check.md': 'rules_layer',
        'config/vocab/rules_edition.yaml': 'rules_layer'}
def srcw(s):
    return SRCW.get(s, 'data_dictionaries_inbox006')

NEW = []
for cl in clusters:
    p = RAW[cl['p']]
    mem = cl['members']
    wanted = []
    for x in mem:
        w = srcw(RAW[x]['src'])
        if w not in wanted:
            wanted.append(w)
        for w2 in sorted(mentions.get(x, ())):
            if w2 not in wanted:
                wanted.append(w2)
    leaves = cl['lv'] or []
    if not leaves:
        for x in mem:
            for l in RAW[x]['leaves']:
                if l not in leaves:
                    leaves.append(l)
    text = subst(clean(cl['t'] or p['text']))
    acc = subst(clean(cl['a'] or p['acc']))
    if not leaves:
        for rid in re.findall(r'R-[A-Z]{2}-\d+', p['text'] + ' ' + p['acc']):
            for l in leaves_by_req.get(rid, [])[:2]:
                if l not in leaves:
                    leaves.append(l)
    assert leaves, cl['p']
    for l in leaves:
        assert l in leafname, (cl['p'], l)
    related = sorted(set(re.findall(r'R-[A-Z]{2}-\d+', text + ' ' + acc + ' ' + p['lands'])) & set(live))
    NEW.append(dict(id=cl['nid'], family='N-' + cl['fam'], priority=cl['pr'], tier=cl['tier'] or p['tier'],
                    text=text, acceptance=acc, lands_in=subst(clean(cl['lands'] or p['lands'])),
                    domain_leaves=leaves, domain_leaf_names=[leafname[l] for l in leaves],
                    wanted_by=wanted, merged_from=mem, sources=sorted(set(RAW[x]['src'] for x in mem)),
                    related_existing=related, note=cl['note'] or ''))
NEW.sort(key=lambda r: (r['family'], r['id']))

# ------------------------------------------------------------------ existing verdicts
P0FAM = {'RR', 'DQ', 'RG', 'GT', 'IV', 'SB', 'MB', 'EN', 'CD'}
P0IDS = set()
for fam, nums in {'RR': range(1, 9), 'DS': [1, 2, 4, 5, 6, 10, 11, 13, 14, 15], 'FD': [1, 2, 3, 5, 8, 9, 10],
                  'MD': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 15, 16, 17, 18, 19], 'ID': range(1, 12),
                  'VI': [1, 2, 3, 4, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16], 'CG': range(1, 9),
                  'DT': [1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 14, 15, 17, 19], 'BL': range(1, 8), 'SY': [1, 2, 3, 4, 5, 6, 8, 9, 10],
                  'EV': [1, 3, 7, 8, 9, 10, 11, 12, 14, 15, 16], 'RF': [1, 2, 3, 7], 'SR': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15],
                  'HR': [1, 2, 3, 4, 5, 6, 7, 8, 12], 'CS': [1, 2, 4, 5, 6, 9, 10], 'VA': [1, 2, 3, 4, 5, 6, 9], 'PL': [13]}.items():
    for n in nums:
        P0IDS.add('R-%s-%02d' % (fam, n))
def prio(i):
    f = i[2:4]
    if f in P0FAM and i != 'R-RR-09' and i != 'R-DQ-08':
        return 'P0'
    if i in P0IDS:
        return 'P0'
    if f in {'CX', 'HY', 'PT', 'VZ', 'CC', 'CH', 'GU', 'CO', 'OS'} and i not in ('R-CC-02',):
        return 'P1' if f not in ('GU',) else 'P1'
    return 'P1'

def qr_class(i, q):
    t, iss = q['text'], q['issues']
    into = split = None
    if i == 'R-CO-08':
        return 'rewrite', 'Should' if live[i]['tier'] == 'Should' else live[i]['tier'], live[i]['text'] + ' (clean vs late switches move to R-CH-05; "two defenders on one attacker" stays here)', None, None
    if t.startswith(('Superseded by', 'Merge into', 'Merge with', 'Mark as a pointer')):
        ids = re.findall(r'R-[A-Z]{2}-\d+', t)
        into = 'R-DF-20' if i == 'R-DF-10' else ids[0]
        return 'merge-into', live[i]['tier'], t, into, None
    if re.search(re.escape(i) + r'a\b', t):
        split = sorted(set(re.findall(re.escape(i) + r'[a-z]\b', t)))
        return 'split', 'mixed', t, None, split
    if t.startswith('Split'):
        return 'split', live[i]['tier'], t, None, ['per view']
    if t.startswith('Keep as the single'):
        return 'keep', live[i]['tier'], live[i]['text'] + ' (' + t + ')', None, None
    if t.startswith('No text change'):
        rest = t[len('No text change'):].lstrip('.;: ')
        v = 'tighten' if ('NS' in iss or 'NV' in iss) else 'keep'
        return v, live[i]['tier'], live[i]['text'] + ((' (' + rest + ')') if rest else ''), None, None
    if t.startswith('Same') or t.startswith('Shall: same text'):
        rest = re.sub(r'^(Same (text|invariant)|Shall: same text)[.;,]?\s*', '', t)
        v = 'rewrite' if any(x in iss for x in ('CORR', 'UNIT', 'STALE')) else 'tighten'
        tier = 'Shall' if t.startswith('Shall: same') else live[i]['tier']
        return v, tier, live[i]['text'] + ((' (' + rest + ')') if rest else ''), None, None
    tier = 'Should' if t.startswith('Should') else ('Shall' if t.startswith('Shall') else live[i]['tier'])
    body = re.sub(r'^(Shall|Should):\s*', '', t)
    v = 'rewrite' if any(x in iss for x in ('CONF', 'CORR', 'STALE', 'UNIT', 'FEAS')) else 'tighten'
    return v, tier, body, None, None

absorbed_into = collections.defaultdict(list)
for k_, (e, note) in ABS.items():
    absorbed_into[e].append(k_)
KBYID = collections.defaultdict(list)
for kk in K:
    for x in kk['ids']:
        if x.startswith('R-'):
            KBYID[x].append(kk['id'])
EX = []
for i in order:
    L, T = live[i], AT[i]
    deflt_acc = '%s: %s' % (T['measure'], T['threshold'])
    rec = dict(id=i, family=i[:4], family_name=FAM_NAME.get(i[:4], ''), live_tier=L['tier'], live_text=L['text'])
    q = d['qr'].get(i)
    pv = [(s, d[key][i]) for s, key in (('E', 'eng'), ('A', 'ana'), ('S', 'sci')) if i in d[key] and d[key][i]['verdict'] != 'keep']
    into = split = None
    if i in O:
        ov = O[i]
        v, text, acc, by = ov['v'], ov['text'], ov['acc'], ov['by']
        tier = ov['tier'] or ('mixed' if v == 'split' else ('Should' if text.startswith('Should') else ('Shall' if text.startswith('Shall') else L['tier'])))
        text = re.sub(r'^(Shall|Should)( \(from [^)]*\)| \(promoted from Should\))?:\s*', '', text) if v != 'split' else text
        into, kk_, note = ov['into'], ov['k'], ov['note']
        if v == 'split':
            split = sorted(set(re.findall(re.escape(i) + r'[a-z]\b', text))) or ['per view']
    else:
        assert not (q and pv), i
        note = None; kk_ = []
        if q:
            v, tier, text, into, split = qr_class(i, q)
            acc = q['acc'] or deflt_acc
            by = ['Q']
        elif pv:
            s, pvv = pv[0]
            assert len(pv) == 1, i
            v = pvv['verdict']; text = pvv['text']; acc = pvv['acc'] or deflt_acc; by = [s]
            tier = L['tier']
        else:
            v, text, acc, by, tier = 'keep', L['text'], deflt_acc, [], L['tier']
    kk_ = sorted(set(list(kk_) + KBYID.get(i, [])))
    explicit_keep = [SRCNAME[s] for s, key in (('E', 'eng'), ('S', 'sci')) if i in d[key] and d[key][i]['verdict'] == 'keep']
    if absorbed_into.get(i) and not all(x in (note or '') for x in absorbed_into[i]):
        note = ((note + '; ') if note else '') + 'absorbs proposals: ' + ', '.join(x for x in absorbed_into[i] if x not in (note or ''))
    text = text[:1].upper() + text[1:] if text else text
    rec.update(verdict=v, proposed_tier=tier, proposed_text=subst(clean(text)), acceptance=subst(clean(acc)), units=T['unit'],
               merge_into=into, split_into=split, drivers=[SRCNAME[b] for b in by], explicit_keep_by=explicit_keep,
               conflicts=kk_, issues=T['issues'], acceptance_status=T['status'], priority=prio(i), note=note or '')
    EX.append(rec)
assert len(EX) == 518
vc = collections.Counter(r['verdict'] for r in EX)
print('verdicts', vc)

# ------------------------------------------------------------------ id map
IDMAP = []
for x, r in RAW.items():
    if x in ABS:
        IDMAP.append(dict(old_id=x, source=r['src'], maps_to=ABS[x][0], relation='absorbed_into_existing', note=ABS[x][1] or ''))
    else:
        ci = clusters[assigned[x]]
        IDMAP.append(dict(old_id=x, source=r['src'], maps_to=ci['nid'], relation='primary' if x == ci['p'] else 'merged', note=''))
MK006 = {'new-MK-10': 'R-MK-25', 'new-MK-11': 'R-MK-26', 'new-MK-12': 'R-MK-27', 'new-MK-13': 'R-MK-28', 'new-MK-14': 'R-MK-29',
         'new-MK-15': 'R-MK-30', 'new-MK-16': 'R-MK-31', 'new-MK-17': 'R-MK-32', 'new-MK-18': 'R-MK-33'}
for a, b in MK006.items():
    IDMAP.append(dict(old_id=a, source='coord/requirements_inbox/006-markets-requirements.md', maps_to=b, relation='already_in_live_doc', note=''))
for n, b in enumerate(['R-MK-12', 'R-MK-13', 'R-MK-14', 'R-MK-15', 'R-MK-16', 'R-MK-17', 'R-MK-18', 'R-MK-19', 'R-MK-20'], 1):
    IDMAP.append(dict(old_id='006-markets R-MK-%02d (prompt-002 name)' % n, source='coord/requirements_inbox/006-markets-requirements.md', maps_to=b, relation='already_in_live_doc', note='name collision with live R-MK-%02d; live runner IDs to be prefixed (quality review C20)' % n))
for a, b in [('R-DQ-01', 'R-MK-21'), ('R-DQ-05', 'R-MK-22'), ('R-RG-07', 'R-MK-23'), ('R-RG-08', 'R-MK-24')]:
    IDMAP.append(dict(old_id='006-markets %s (prompt-002 name)' % a, source='coord/requirements_inbox/006-markets-requirements.md', maps_to=b, relation='already_in_live_doc', note='not the live ' + a))
IDMAP.sort(key=lambda r: r['old_id'])

# ------------------------------------------------------------------ conflicts, decisions, spine
for kk in K:
    kk['ids_resolved'] = sorted(set(res(x) if (x.startswith('new-') or x in live) else x for x in kk['ids']))
DEC = [dict(id=kk['id'], decision=kk['dec'], recommendation=kk['res'], source='conflict ' + kk['id']) for kk in K]
DEC += [dict(id=a, decision=subst(b), recommendation=dd, source=c_) for a, b, c_, dd in D]
SPR = []
for s in SP:
    SPR.append(dict(id=s['id'], from_state=s['frm'], to_state=s['to'], trigger=s['trigger'], rule=subst(s['rule']), clocks=s['clocks'],
                    detection=sorted(set(res(x) for x in s['det']), key=lambda z: (z[:1], z)),
                    timing=sorted(set(res(x) for x in s['tim'])), analysis=sorted(set(res(x) for x in s['ana']))))
SPR.sort(key=lambda s: s['id'])
DPR = [dict(decision_point=a, decider=b, window=c_, requirements=sorted(set(res(x) for x in r))) for a, b, c_, r in DP]

# ------------------------------------------------------------------ minimum build
TABLES = [
 ('games', 'registry', 'existing'), ('teams', 'registry', 'existing'), ('players', 'registry', 'existing'), ('rosters', 'registry', 'existing'),
 ('jersey_history', 'registry', 'existing'), ('id_crosswalk', 'registry', 'existing'), ('venues', 'registry', 'existing'),
 ('game_officials', 'registry', 'existing'), ('video_files', 'video', 'existing'), ('frames', 'video', 'existing (+stage_mask)'),
 ('video_segments', 'video', 'new (cut map)'), ('scoreboard_ocr', 'sync', 'existing'), ('clock_map', 'sync', 'new'),
 ('state_transitions', 'state', 'new'), ('state_segments', 'state', 'new (state_frame becomes a view)'), ('state_second', 'state', 'existing (view-able)'),
 ('state_corrections', 'state', 'existing proposal'), ('pbp_versions', 'sync', 'new'), ('stat_corrections', 'sync', 'new'), ('events', 'events', 'existing (+order_index)'),
 ('substitutions', 'events', 'existing'), ('lineup_stints', 'events', 'existing'), ('possessions', 'events', 'existing'), ('chances', 'events', 'existing'),
 ('score_events', 'events', 'existing'), ('shot_clock_resets', 'events', 'existing'), ('timeouts', 'events', 'existing'), ('restarts', 'events', 'existing'),
 ('free_throws', 'events', 'existing'), ('fouls', 'events', 'existing'), ('shots', 'events', 'existing'), ('rebounds', 'events', 'existing'),
 ('turnovers', 'events', 'existing'), ('made_basket_events', 'events', 'existing'), ('scoreboard_flags', 'quality', 'existing'),
 ('detections', 'vision', 'existing'), ('tracks', 'vision', 'existing'), ('player_positions', 'vision', 'existing (+sigma columns)'),
 ('ball_states', 'vision', 'existing'), ('raw_pulls', 'quality', 'existing'), ('quarantine_rows', 'quality', 'existing'),
 ('run_records', 'quality', 'existing'), ('run_requirement_results', 'quality', 'existing'), ('review_queue', 'review', 'existing'),
 ('review_labels', 'review', 'existing (+timing gold)'), ('stage_outputs', 'engineering', 'new (content-address registry)'),
 ('market tables (already coded)', 'markets', 'existing code'),
]
p0_new = [r['id'] for r in NEW if r['priority'] == 'P0']
p0_ex = [r['id'] for r in EX if r['priority'] == 'P0' and r['verdict'] not in ('merge-into', 'drop')]
DEFER = ['belief_states', 'coach_quiz', 'position_forecasts', 'possession_value (layer 3)', 'value_credits', 'predictions', 'simulation_runs',
         'profile_snapshots', 'player_shooting_sector_ring', 'commentary_segments', 'appearance_cards', 'bench_events', 'scheme_states', 'scheme_changes',
         'set_instances', 'set_instance_phases', 'play_calls', 'configuration_snapshots', 'movement_primitives', 'actions', 'screens', 'drives', 'dribbles',
         'reaction_events', 'defensive_matchups', 'defensive_events', 'frame_geometry', 'post_touches', 'box_outs', 'accel_efforts', 'load_stint_bins',
         'transition_numbers', 'transition_roles', 'official_positions', 'whistles', 'audio_seconds', 'identity_confusions', 'hypothesis_results', 'pregame_cards',
         'runs', 'fakes', 'source_definitions']

json.dump(dict(EX=EX, NEW=NEW, IDMAP=IDMAP, K=K, DEC=DEC, SPR=SPR, DPR=DPR, TABLES=TABLES, p0_new=p0_new, p0_ex=p0_ex, DEFER=DEFER, NMAP=NMAP, ABS={k_: v[0] for k_, v in ABS.items()}),
          open('built.json', 'w'), indent=1)
print('new', len(NEW), collections.Counter(r['family'] for r in NEW))
print('prio', collections.Counter(r['priority'] for r in NEW))
print('p0 ex', len(p0_ex), 'p0 new', len(p0_new))
unm = [r['id'] for r in EX if '(unmapped)' in r['proposed_text'] + r['acceptance']] + [r['id'] for r in NEW if '(unmapped)' in r['text'] + r['acceptance'] + r['lands_in']]
print('unmapped tokens in', unm)
