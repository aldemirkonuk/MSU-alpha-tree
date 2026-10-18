import json, yaml, collections, re
R = '/Users/aldemirkonuk/Projects/MSU-Alpha-3/'
b = json.load(open('built.json'))
EX, NEW, IDMAP, K, DEC, SPR, DPR = b['EX'], b['NEW'], b['IDMAP'], b['K'], b['DEC'], b['SPR'], b['DPR']
NMAP, ABS = b['NMAP'], b['ABS']
def N(x):
    return NMAP.get(x) or ABS.get(x) or x
def esc(s):
    return str(s).replace('|', '\\|').replace('\n', ' ')

vc = collections.Counter(r['verdict'] for r in EX)
fam_vc = collections.defaultdict(collections.Counter)
for r in EX:
    fam_vc[r['family']][r['verdict']] += 1
nfam = collections.defaultdict(collections.Counter)
for r in NEW:
    nfam[r['family']][r['priority']] += 1
npr = collections.Counter(r['priority'] for r in NEW)
ntier = collections.Counter(r['tier'] for r in NEW)
rel = collections.Counter(r['relation'] for r in IDMAP)
n_raw = sum(1 for r in IDMAP if r['relation'] in ('primary', 'merged', 'absorbed_into_existing'))
n_abs = rel['absorbed_into_existing']
VORD = ['keep', 'tighten', 'loosen', 'rewrite', 'split', 'merge-into', 'drop']
p0_new = b['p0_new']; p0_ex = b['p0_ex']

TOP15 = [
 ('Clock map as a table', ['R-MD-08', 'new-MD-E1', 'new-SY-E6'], 'Video, game clock, shot clock and UTC aligned in piecewise segments with stated residuals; every timing metric and every market join runs through it.', 'data engineer (+ analyst, scientist on timing)'),
 ('Typed rules state machine with a flow state', ['new-SY-E1', 'new-SR-A6', 'new-IV-E1'], 'Every state change is one typed transition (T01-T24) with its rule reference and allowed from/to pairs; invariants run on transitions, not on 155,000 frames.', 'data engineer, ESPN analyst'),
 ('State stored once', ['new-MD-E2', 'R-MD-01', 'R-SR-06', 'new-MD-E3'], 'state_segments per dimension, team-neutral; per-frame state and the global stamp become views, so a correction is made in one place.', 'data engineer'),
 ('Rules layer and rule corrections', ['new-RL-1', 'new-RL-2', 'R-IV-02', 'R-IV-10', 'R-RF-03', 'R-SY-08', 'new-CG-1'], 'Rules edition per game; two or three officials; media-format timeouts; 2026-27 foul classes without "intentional"; 41 shot-clock causes; edge-correct court constants.', 'rules layer, quality review, ESPN analyst'),
 ('One chance definition', ['R-DQ-06', 'R-SY-05', 'R-MD-06'], 'Fixed terminal-event list; a shot-clock reset inside a possession opens a new chance; team and dead-ball rebounds counted as the scorer records them.', 'quality review, data engineer, ESPN analyst'),
 ('Scorebug timing', ['R-SB-03', 'new-SY-E4', 'R-SY-01'], 'Window 4.0 s (not 15 s), per-field lag model, lag-corrected state times; POSS is the arrow, never possession.', 'all three'),
 ('Timing in frames at 29.97 fps', ['R-VI-01', 'R-MB-04', 'R-BL-04'], 'The footage that exists is 29.97 fps; every tolerance restated in frames; make frame +/- 2 frames on 95%.', 'all three, quality review'),
 ('One physics key', ['R-IV-13', 'R-DQ-02', 'R-EN-03', 'R-DT-08'], 'Speed 10.0 m/s hard and 9.0 m/s soft over >= 0.3 s; acceleration 12 m/s² over >= 0.5 s, to 8.0 after calibration; checks on filtered tracks.', 'data engineer, team data scientist'),
 ('Uncertainty travels with every kinematic value', ['new-DT-E1', 'R-CG-08', 'R-PL-12', 'new-PL-E1', 'R-CO-02'], 'Sigma columns; bands and onsets reported only where resolvable; change-point onsets; no jerk.', 'data engineer, team data scientist'),
 ('Ball-screen coverage gates', ['R-DF-06', 'R-DF-16', 'new-DF-S1'], 'Coarse always; fine only after its validation gate and at confidence >= 0.8; coverage-by-outcome table.', 'ESPN analyst, team data scientist'),
 ('One vocabulary per word', ['R-MD-17', 'new-EV-A14', 'R-MD-13', 'R-CO-04', 'R-MD-16', 'new-MD-A6'], 'Runs (three named definitions), clutch (one key), foul trouble (config table), broadcast phrases for every label.', 'ESPN analyst (+ all)'),
 ('Layered value and shot quality', ['R-VL-01', 'R-VL-04', 'new-VL-3', 'R-EV-07'], 'PBP, location and tracking layers side by side; shooter-agnostic and shooter-adjusted shot quality; contest unknown rather than imputed.', 'team data scientist, ESPN analyst'),
 ('Reactions with baselines and designs', ['new-CH-S1', 'new-HY-S1', 'R-DF-19', 'R-CC-03'], 'Every reaction linked to its trigger with latency in s and possessions and a matched baseline; no causal claim without a registered design.', 'team data scientist, ESPN analyst'),
 ('Idempotent, replayable lake', ['new-EN-E1', 'new-EN-E3', 'R-EN-07', 'new-SY-E2', 'new-VI-E1', 'new-VI-E2'], 'Content-addressed stage outputs, deterministic IDs, PBP and box versions with diffs, cut map of condensed replays, per-frame stage mask.', 'data engineer'),
 ('Numbers that reconcile', ['new-DQ-A2', 'R-DQ-01', 'new-DQ-2', 'new-VA-E1', 'new-VA-S1'], 'Published-number gate against the official box; end-of-game reconciliation; timing gold set; held-out games registered before any fit.', 'ESPN analyst, data engineer, team data scientist'),
]

def ids(lst):
    out = []
    for x in lst:
        y = N(x)
        if y not in out:
            out.append(y)
    return ', '.join(out)

# ======================================================================= YAML
ydoc = dict(
    version='0.1.0', date='2026-10-18', status='proposed',
    description='Consolidated, de-duplicated requirement proposals from the requirements improvement pass and the three-perspective panel. Proposal only: the live requirements doc is owned by the requirements session. Human-readable companion: docs/requirements_review/synthesis.md.',
    inputs=['docs/requirements_review/quality_review.md', 'docs/requirements_review/acceptance_tests.yaml',
            'docs/requirements_review/perspective_espn_analyst.md', 'docs/requirements_review/perspective_data_engineer.md',
            'docs/requirements_review/perspective_team_data_scientist.md', 'docs/data/gap_closures_round2.md',
            'schema/tables_proposed_changes.yaml', 'config/vocab/*.yaml', 'docs/data/court_constants_check.md',
            'coord/requirements_inbox/007-game-ontology-gaps.md (via config/game_ontology.yaml gaps)', 'config/invariants.yaml',
            'coord/requirements_inbox/006-data-dictionary-and-first-games.md', 'coord/requirements_inbox/006-markets-requirements.md',
            'docs/data/dictionary_players.md', 'docs/data/dictionary_games.md',
            'scratchpad live_doc2/requirement_ids.md (518 IDs)'],
    conventions=dict(
        verdicts={'keep': 'as written in the live doc (acceptance from acceptance_tests.yaml)', 'tighten': 'same intent, sharper text or acceptance',
                  'loosen': 'scope, tier or threshold relaxed', 'rewrite': 'text was wrong, conflicting or untestable', 'split': 'several requirements in one row; children ID-a, ID-b',
                  'merge-into': 'superseded by merge_into (row kept, marked superseded, add-only)', 'drop': 'remove (none proposed; drops became merge-into)'},
        drivers={'quality_review': 'docs/requirements_review/quality_review.md', 'espn_analyst': 'perspective_espn_analyst.md',
                 'data_engineer': 'perspective_data_engineer.md', 'team_data_scientist': 'perspective_team_data_scientist.md',
                 'rules_layer': 'config/vocab/*.yaml, court_constants_check.md', 'gap_closures_round2': 'docs/data/gap_closures_round2.md',
                 'inbox007_or_invariants': 'inbox 007 / config/invariants.yaml'},
        priority={'P0': 'needed for the first two games (UConn 401856571, Louisville 401856531)', 'P1': 'this season', 'P2': 'later'},
        new_ids='N-<FAMILY>-nn; one series per family; old proposal IDs in id_map; N-RL is the proposed rules-layer family',
        units='m, cm, s, ms, degrees, m/s, m/s², %, counts; "(proposal)" and "(initial value, to calibrate)" mark numbers that are not decisions'),
    counts=dict(existing_ids=len(EX), existing_verdicts={v: vc.get(v, 0) for v in VORD},
                new_requirements=len(NEW), new_by_priority=dict(sorted(npr.items())), new_by_tier=dict(ntier),
                new_by_family={f: dict(sorted(c.items())) for f, c in sorted(nfam.items())},
                raw_proposals_merged=n_raw, absorbed_into_existing_ids=n_abs,
                conflicts_resolved=len(K), decisions_for_aldemir=len(DEC)),
    conflicts=[dict(id=k['id'], title=k['title'], affected_ids=k['ids_resolved'],
                    views=[dict(who=w, view=v) for w, v in k['views']], recommended_resolution=k['res'], reason=k['why'], decision=k['dec']) for k in K],
    decisions=DEC,
    existing_verdicts=[dict(id=r['id'], family=r['family'], live_tier=r['live_tier'], verdict=r['verdict'], merge_into=r['merge_into'],
                            split_into=r['split_into'], proposed_tier=r['proposed_tier'], proposed_text=r['proposed_text'],
                            acceptance=r['acceptance'], units=r['units'], drivers=r['drivers'], explicit_keep_by=r['explicit_keep_by'],
                            conflicts=r['conflicts'], issues=r['issues'], acceptance_status=r['acceptance_status'], priority=r['priority'],
                            note=r['note'], live_text=r['live_text']) for r in EX],
    new_requirements=NEW,
    id_map=IDMAP,
    game_flow_spine=dict(transitions=SPR, decision_points=DPR),
    minimum_build_first_two_games=dict(
        tables=[dict(table=t, area=a, status=s) for t, a, s in b['TABLES']],
        deferred_tables=b['DEFER'],
        requirements_existing_p0=p0_ex, requirements_new_p0=p0_new),
    resolved_code_findings=[
        dict(id='M1', file='src/msu_alpha/markets/models.py', finding='dedup_key without source_event_id', status='resolved 2026-10-18', test='tests/markets/test_engineer_review_fixes.py::test_unmatched_events_with_same_line_do_not_collide', requirement='R-MK-27'),
        dict(id='M2', file='src/msu_alpha/markets/sources/cbbd.py', finding='CBBD reported open/close stamped with fetch time', status='resolved 2026-10-18 (finished games keyed on scheduled tip)', test='test_cbbd_reported_rows_are_idempotent_across_pulls', requirement='R-MK-27'),
        dict(id='M3', file='src/msu_alpha/markets/store.py', finding='de-duplication per batch only', status='resolved 2026-10-18 (existing keys skipped across runs)', test='test_store_dedup_holds_across_runs', requirement='R-MK-27'),
        dict(id='M4', file='src/msu_alpha/markets/raw_store.py', finding='RawStore did not call ensure_private', status='resolved 2026-10-18', test='test_raw_store_refuses_repo_and_keeps_received_hash', requirement='R-RG-11'),
        dict(id='M5', file='src/msu_alpha/markets/raw_store.py, models.py', finding='sha256 computed after redaction', status='resolved 2026-10-18 (sha256_received added)', test='test_raw_store_refuses_repo_and_keeps_received_hash', requirement='R-MK-13'),
        dict(id='M6', file='src/msu_alpha/markets/store.py, raw_store.py', finding='JSONL appends without atomic rename', status='open', requirement=N('new-EN-E2')),
        dict(id='M7', file='src/msu_alpha/markets/store.py', finding='read() without partition pruning', status='open (performance only)', requirement='none'),
        dict(id='M8', file='src/msu_alpha/markets/models.py', finding='schema_version not in Parquet metadata', status='open', requirement='R-MK-31'),
    ],
    top_15_changes=[dict(rank=i + 1, change=t, ids=ids(l).split(', '), what=w, driven_by=by) for i, (t, l, w, by) in enumerate(TOP15)],
)
class D(yaml.SafeDumper):
    pass
def str_rep(dumper, data):
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
D.add_representer(str, str_rep)
ytxt = yaml.dump(ydoc, Dumper=D, sort_keys=False, allow_unicode=True, width=200)
hdr = '# Consolidated requirement proposals (2026-10-18). PROPOSAL ONLY; the requirements session owns the live doc.\n# Generated from the six panel/improvement inputs; companion: docs/requirements_review/synthesis.md; inbox: coord/requirements_inbox/008-requirements-improvement.md.\n'
open(R + 'docs/requirements_review/proposals_consolidated.yaml', 'w').write(hdr + ytxt)
chk = yaml.safe_load(open(R + 'docs/requirements_review/proposals_consolidated.yaml'))
assert len(chk['existing_verdicts']) == 518 and len(chk['new_requirements']) == len(NEW)
print('yaml ok', len(ytxt))

# ======================================================================= synthesis.md
L = []
w = L.append
w('# Requirements synthesis: three perspectives, one proposal set')
w('')
w('Date: 2026-10-18. Status: PROPOSAL ONLY. Add-only file. Nothing in the live requirements doc, `config/`, `schema/` or `src/` was edited; the requirements session decides. Machine-readable twin: `docs/requirements_review/proposals_consolidated.yaml` (validated with `yaml.safe_load`). Inbox note: `coord/requirements_inbox/008-requirements-improvement.md`.')
w('')
w('Aldemir asked to think from an ESPN analyst\'s, a data engineer\'s and an NBA team data scientist\'s point of view (Think: game flow under the rules; Understand: how teams react; Analyze: how each role moves) and to synthesize how each perspective adjusts the requirements. This file merges those three panel reviews with the quality review of all 518 IDs, the round-2 ontology gap closures, the rules vocabularies and every earlier repo proposal into one verdict per existing ID, one de-duplicated `N-<FAMILY>-nn` series of new requirements, a rules-exact game-flow spine and a minimum build for the first two games.')
w('')
w('## 0. Counts')
w('')
w('| Item | Count |')
w('| --- | ---: |')
w('| Existing IDs given one merged verdict | %d |' % len(EX))
for v in VORD:
    w('| verdict: %s | %d |' % (v, vc.get(v, 0)))
w('| Raw new-requirement proposals read (inbox 007: 93, round 2: 71, invariants: 34, analyst: 28, engineer: 35, scientist: 19, dictionaries and rules files: 10) | %d |' % n_raw)
w('| absorbed into an existing ID (no new ID needed) | %d |' % n_abs)
w('| merged into the N-series | %d |' % (n_raw - n_abs))
w('| New requirements after de-duplication (N-series) | %d (P0 %d, P1 %d, P2 %d) |' % (len(NEW), npr['P0'], npr['P1'], npr['P2']))
w('| Markets proposals already in the live doc (inbox 006 markets, mapped) | %d |' % rel['already_in_live_doc'])
w('| Cross-input conflicts resolved (each a decision for Aldemir) | %d |' % len(K))
w('| Further open decisions, de-duplicated across the six inputs | %d |' % (len(DEC) - len(K)))
w('')
w('Verdicts per existing family (keep / tighten / loosen / rewrite / split / merge-into):')
w('')
w('| Family | Area | IDs | keep | tighten | loosen | rewrite | split | merge-into |')
w('| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |')
fams = []
for r in EX:
    if r['family'] not in fams:
        fams.append(r['family'])
famname = {r['family']: r['family_name'] for r in EX}
for f in fams:
    c = fam_vc[f]
    w('| %s | %s | %d | %d | %d | %d | %d | %d | %d |' % (f, famname[f], sum(c.values()), c['keep'], c['tighten'], c['loosen'], c['rewrite'], c['split'], c['merge-into']))
w('| **All** | | **%d** | **%d** | **%d** | **%d** | **%d** | **%d** | **%d** |' % (len(EX), vc['keep'], vc['tighten'], vc['loosen'], vc['rewrite'], vc['split'], vc['merge-into']))
w('')
w('New requirements per family and priority:')
w('')
w('| Family | P0 | P1 | P2 | Total |')
w('| --- | ---: | ---: | ---: | ---: |')
for f, c in sorted(nfam.items()):
    w('| %s | %d | %d | %d | %d |' % (f, c['P0'], c['P1'], c['P2'], sum(c.values())))
w('| **All** | **%d** | **%d** | **%d** | **%d** |' % (npr['P0'], npr['P1'], npr['P2'], len(NEW)))
w('')
w('Method. A script parsed every input table (quality review section 4: 181 rows; engineer verdicts: 92; analyst: 48 changed IDs; scientist: 43; new-requirement tables of the three panels; inbox 007 from `config/game_ontology.yaml` gaps; round-2 requirements; `config/invariants.yaml`), then: (1) one verdict per ID: the single changing input\'s verdict where only one input touched it, a hand-merged verdict for the 61 IDs touched by two or more inputs and for every ID in a conflict; quality-review rows without a verdict word were classed by their rewrite (pointer -> merge-into, a/b/c -> split, new text with CONF/CORR/STALE/UNIT/FEAS -> rewrite, acceptance only -> tighten, trace-only -> keep). (2) Round-2 requirements that "refine" an inbox-007 ID were merged with it; perspective proposals were merged where they ask for the same product; proposals that restate an existing ID were absorbed into that ID\'s merged verdict. (3) N-IDs were assigned per family in priority order. Every old proposal ID is in the id_map.')
w('')

w('## 1. How each perspective adjusts the requirements')
w('')
w('### 1.1 Think: game flow under the 2026-27 rules')
w('')
w('All three panels drew the same state machine from the rules book (Rules 2-11, 4-9, 5-7 to 5-14, 6-1 to 6-6, 7, 8, 9, 11). They differ in what they need from it:')
w('')
w('- **Data engineer**: state is a product of independent dimensions (ball live/dead, game clock, shot clock, team control, try in flight, restart pending, stoppage, period phase, counts). A throw-in is live with both clocks stopped for up to 5 s (6-1.2.b vs 5-10.2.a), so one "ball state" column is wrong. Each dimension changes a few hundred times a game while there are 155,000-162,000 frames, so state should be stored once per transition (%s, %s) and stamped with four clocks (%s). Condensed replays make video time discontinuous (UConn: 86.5 min of video for 134.4 min tip-to-final), so the clock map is a table (%s) and the cut map another (%s).' % (N('new-MD-E2'), N('new-SY-E1'), N('new-MD-E4'), N('new-MD-E1'), N('new-VI-E1')))
w('- **ESPN analyst**: the run of show (tip, media timeouts at 16/12/8/4 or 15/10/5, bonus at the 7th and 10th team foul, last 2:00 challenge rules, last 59.9 s clock stop, shot clock off, extra periods) decides what the stats desk must have ready; the flow state S0-S11 becomes a dimension of the same transition log (%s), and late-game situation flags become Shall (R-SR-11).' % N('new-SR-A6'))
w('- **Team data scientist**: a possession or chance boundary in the wrong place moves points between start types and corrupts every model label; the chance terminal list (R-DQ-06c, K08) and the full 41-cause shot-clock vocabulary (R-SY-08, K18) are model inputs, not bookkeeping.')
w('')
w('Requirements that follow: the rules layer (%s, %s), the invariants (%s to %s), the typed transitions (%s), the clock map (R-MD-08), the chance definition (R-DQ-06, R-SY-05) and the spine in section 6, which traces every transition to detection, timing and analysis requirements.' % (N('new-RL-1'), N('new-RL-2'), 'N-IV-01', 'N-IV-33', N('new-SY-E1')))
w('')
w('### 1.2 Understand: how teams react')
w('')
w('- **Data engineer**: almost every reaction is a pair of rows in different tables linked by time (timeout -> first set; screen -> coverage within t0 + 2.0 s). Joins need one time base, a declared window per pair and explicit "not observed" rows, so a reaction cut out of a condensed replay is not counted as "no reaction" (R-VI-02, %s).' % N('new-VI-E2'))
w('- **ESPN analyst**: adjustments land at dead balls, often two or three possessions after the trigger; lags must be stored in possessions (R-DF-19). New products: run stoppers (%s), timeout purpose (%s), foul-trouble decisions (%s), hot-shooter response (%s), zone recognition lag (%s), mismatch hunting (%s), end-of-clock possessions (%s), get-back onset (%s).' % tuple(N(x) for x in ['new-EV-A14', 'new-CC-A6', 'new-CC-A5', 'new-DF-A6', 'new-ST-A10', 'new-ST-A9', 'new-ST-A11', 'new-DF-A8']))
w('- **Team data scientist**: teams react when things go badly, so naive before/after comparisons measure regression to the mean (beliefs register B2). Every reaction needs a matched baseline (%s) and every causal claim a registered design (%s).' % (N('new-CH-S1'), N('new-HY-S1')))
w('')
w('### 1.3 Analyze: how each role moves, and what broadcast video can measure')
w('')
w('- Reference speeds: NCAA D-I peaks 7.04 +/- 0.39 m/s (guards), 6.63 +/- 0.52 (forwards), 6.23 +/- 0.33 (centres) (Stone et al. 2022, via `docs/research/load_thresholds.md`).')
w('- The engineer\'s noise-floor table is the decisive input: at position error 0.3 m a 0.5 s window gives speed noise 0.54 m/s and acceleration noise 8.39 m/s²; at the R-PL-13 target of 0.5 m, 0.90 m/s and 13.98 m/s². Speed bands are resolvable with 1 s windows; acceleration bands (+/- 2.0 / 3.0 m/s²), a 1 m/s² onset and jerk are not. This drives K01 and K03 and the uncertainty columns (%s), the resolvability gate (%s) and the change-point onset (R-CO-02).' % (N('new-DT-E1'), N('new-PL-E1')))
w('- The analyst and scientist add what the camera hides: weak-side help, tag defenders and far corners are off-frame exactly when they matter (missing not at random), so contest fields are "unknown" rather than imputed (R-EV-07), off-screen estimates are flagged (R-DT-07) and the broadcast error budget decides what is estimable (%s).' % N('new-VA-S5'))
w('- Timing: one frame is 33.4 ms at 29.97 fps; the made-basket frame can be fixed to about +/- 1 frame by hand; the scorebug lags the net by 1.50-2.60 s (median 1.933 s, n = 10). Hence R-MB-04, R-BL-04, R-SB-03 and %s.' % N('new-SY-E4'))
w('')
w('### 1.4 Synthesize: six adjustments the three perspectives share')
w('')
w('1. **Measure in the footage we have**: tolerances in frames at 29.97 fps (R-VI-01, R-MB-04, R-BL-04); scorebug window from measured lag (R-SB-03).')
w('2. **Store state once, typed by the rules**: transitions and segments, team-neutral, with views for per-frame and MSU-relative use (K09).')
w('3. **Uncertainty travels with every number**: position and kinematic sigma, resolvability gates, n and interval, reliability before display (K03, K12).')
w('4. **One definition per word**: runs, clutch, transition class, coverage levels, foul trouble, chance, garbage time, all in config (K05, K06, K04, K10, K08, K28).')
w('5. **Reconcile with the official record**: cross-source rows, end-of-game reconciliation, published-number gate, stat corrections propagated (%s, %s, %s).' % (N('new-DQ-2'), N('new-DQ-A2'), N('new-SY-E2')))
w('6. **Reactions need baselines; pipelines need idempotency**: reaction catalogue with matched baselines and designs; content-addressed outputs, deterministic IDs and versioned sources.')
w('')

w('## 2. Conflicts between inputs and recommended resolutions')
w('')
w('Each conflict is also a one-line decision for Aldemir (section 9 and inbox 008).')
w('')
for k in K:
    w('### %s %s' % (k['id'], k['title']))
    w('')
    w('Affected: %s.' % ', '.join(k['ids_resolved']))
    w('')
    for who, view in k['views']:
        w('- %s: %s' % (who, view))
    w('- **Recommended**: %s' % k['res'])
    w('- **Why**: %s' % k['why'])
    w('- **Decision**: %s' % k['dec'])
    w('')

w('## 3. The 15 most important changes')
w('')
w('| # | Change | IDs | What | Driven by |')
w('| ---: | --- | --- | --- | --- |')
for i, (t, l, wh, by) in enumerate(TOP15, 1):
    w('| %d | %s | %s | %s | %s |' % (i, t, ids(l), esc(wh), by))
w('')

w('## 4. Existing IDs: merged verdicts')
w('')
w('Every one of the 518 IDs has a full record (verdict, proposed tier and text, acceptance, units, drivers, conflicts, priority) in `proposals_consolidated.yaml` under `existing_verdicts`. Below: every ID whose verdict is not keep, then the kept IDs per family.')
w('')
for f in fams:
    rows = [r for r in EX if r['family'] == f and r['verdict'] != 'keep']
    if not rows:
        continue
    w('### %s %s' % (f, famname[f]))
    w('')
    w('| ID | Verdict | Proposed text (tier) | Acceptance (unit) | Drivers | Conflict |')
    w('| --- | --- | --- | --- | --- | --- |')
    for r in rows:
        v = r['verdict'] + ((' ' + r['merge_into']) if r['merge_into'] else '')
        tier = r['proposed_tier']
        w('| %s | %s | %s (%s)%s | %s (%s) | %s | %s |' % (r['id'], v, esc(r['proposed_text']), tier, (' ' + esc(r['note'])) if r['note'] else '', esc(r['acceptance']), esc(r['units']), ', '.join(r['drivers']), ', '.join(r['conflicts'])))
    w('')
w('### Kept as written')
w('')
w('| Family | Kept IDs |')
w('| --- | --- |')
for f in fams:
    k_ = [r['id'][5:] for r in EX if r['family'] == f and r['verdict'] == 'keep']
    w('| %s | %s |' % (f, ', '.join(k_) if k_ else 'none'))
w('')
w('Explicit keeps by the data engineer (reviewed and judged right): %s.' % ', '.join(r['id'] for r in EX if 'data_engineer' in r['explicit_keep_by']))
w('')

w('## 5. New requirements: one N-series')
w('')
w('Columns: tier, priority (P0 first two games, P1 this season, P2 later), text, acceptance with units, where it lands, ontology leaves (`config/game_ontology.yaml`), who wants it, and the old proposal IDs merged into it. Full records with leaf names, sources and related existing IDs are in the YAML.')
w('')
cur = None
for r in NEW:
    if r['family'] != cur:
        cur = r['family']
        w('### %s' % cur)
        w('')
        w('| N-ID | Tier | P | Requirement | Acceptance | Lands in | Leaves | Wanted by | From |')
        w('| --- | --- | --- | --- | --- | --- | --- | --- | --- |')
    w('| %s | %s | %s | %s | %s | %s | %s | %s | %s |' % (r['id'], r['tier'], r['priority'], esc(r['text']) + ((' (' + esc(r['note']) + ')') if r['note'] else ''), esc(r['acceptance']), esc(r['lands_in']),
                                                       ', '.join(r['domain_leaves']), ', '.join(r['wanted_by']), ', '.join(r['merged_from'])))
    nxt = None
w('')
w('### 5.x Proposals absorbed into existing IDs')
w('')
w('| Old proposal | Absorbed into | Note |')
w('| --- | --- | --- |')
for r in IDMAP:
    if r['relation'] == 'absorbed_into_existing':
        w('| %s | %s | %s |' % (r['old_id'], r['maps_to'], esc(r['note'])))
w('')

w('## 6. Game-flow spine')
w('')
w('The rules-exact state machine of a game and a possession (data engineer T01-T24 and the analyst\'s S0-S11, rule numbers from the 2026-27 book as verified in `config/invariants.yaml` and `config/vocab/*.yaml`). For each transition, the requirements that detect it, time it and analyse it. T00 is the observability dimension (the broadcast director decides whether we see anything at all).')
w('')
w('| T | From -> to | Trigger | Rule | Clocks | Detection | Timing | Analysis |')
w('| --- | --- | --- | --- | --- | --- | --- | --- |')
for s in SPR:
    w('| %s | %s -> %s | %s | %s | %s | %s | %s | %s |' % (s['id'], esc(s['from_state']), esc(s['to_state']), esc(s['trigger']), esc(s['rule']), esc(s['clocks']), ', '.join(s['detection']), ', '.join(s['timing']), ', '.join(s['analysis'])))
w('')
w('Decision points inside the flow (where a team reacts), and the requirements that capture each decision:')
w('')
w('| Decision point | Decider | Window | Requirements |')
w('| --- | --- | --- | --- |')
for p in DPR:
    w('| %s | %s | %s | %s |' % (p['decision_point'], p['decider'], p['window'], ', '.join(p['requirements'])))
w('')
allsp = set()
for s in SPR:
    allsp |= set(s['detection'] + s['timing'] + s['analysis'])
w('Coverage check: every transition has at least one detection, one timing and one analysis requirement; the spine cites %d distinct IDs (%d existing, %d N-IDs).' % (len(allsp), sum(1 for x in allsp if x.startswith('R-')), sum(1 for x in allsp if x.startswith('N-'))))
w('')

w('## 7. Minimum build for the first two games (P0 only)')
w('')
w('Games: UConn 401856571 (5,188 s, 155,492 frames) and Louisville 401856531 (5,394 s, 161,653 frames), both VP9 1920x1080 at 29.97 fps constant, condensed replays (`results/w3_intake/`).')
w('')
w('**Reconciliation with the engineer\'s 43-table recommendation.** The engineer\'s 43 (40 existing specs + `clock_map`, `state_transitions`, `state_segments`; markets counted once) is kept. Four small tables from his own "what is missing" list are added because P0 requirements write to them: `video_segments` (%s), `pbp_versions` and `stat_corrections` (%s, which also carries the analyst\'s stat corrections), `stage_outputs` (%s). `frames.stage_mask` (%s) is a column. The analyst and scientist P0 additions change columns, not tables (possession situation flags, contest unknown, sigma columns). Everything else stays a proposal until the gates it depends on pass.' % (N('new-VI-E1'), N('new-SY-E2'), N('new-EN-E1'), N('new-VI-E2')))
w('')
w('| Area | Tables |')
w('| --- | --- |')
area = collections.OrderedDict()
for t, a, s_ in b['TABLES']:
    lab = s_.replace('existing ', '').replace('existing', '').strip()
    lab = lab.replace('new (', 'new: ').rstrip(')') if lab.startswith('new (') else lab
    lab = lab.strip('()')
    area.setdefault(a, []).append(t + ((' (' + lab + ')') if lab else ''))
for a, ts in area.items():
    w('| %s | %s |' % (a, ', '.join(ts)))
w('')
w('Deferred (specs stay, no build): %s.' % ', '.join(b['DEFER']))
w('')
w('P0 requirements, new (%d): %s.' % (len(p0_new), ', '.join(p0_new)))
w('')
byf = collections.OrderedDict()
for i in p0_ex:
    byf.setdefault(i[:4], []).append(i[5:])
w('P0 requirements, existing (%d, merged verdict applies): %s.' % (len(p0_ex), '; '.join('%s %s' % (f, ', '.join(v)) for f, v in byf.items())))
w('')
w('Build order (each step testable on game 1 before game 2):')
w('')
w('1. Registry and rules: games registry fields (%s, %s), rules edition (%s, %s), court constants (%s), crosswalk (R-DS-05).' % (N('new-FD-E1'), N('new-FD-7'), N('new-RL-1'), N('new-RL-2'), N('new-CG-1')))
w('2. Lake mechanics: content addressing, atomic writes, deterministic IDs, DAG runner, run logs (%s).' % ', '.join(N(x) for x in ['new-EN-E1', 'new-EN-E2', 'new-EN-E3', 'new-EN-E8', 'new-RR-E1']))
w('3. Video intake and cut map (R-VI-01, R-VI-02, %s, %s); scorebug OCR (R-SY-01) with lag model (%s, R-SB-03).' % (N('new-VI-E1'), N('new-VI-E2'), N('new-SY-E4')))
w('4. PBP versions and ordering (%s, %s); clock map (R-MD-08); timing gold set of 100 instants (%s).' % (N('new-SY-E2'), N('new-SY-E3'), N('new-VA-E1')))
w('5. State: transitions and segments (%s, %s), team-neutral stamps (%s), four clocks and known_at (%s, %s), invariants on transitions (%s and the rules invariants).' % tuple(N(x) for x in ['new-SY-E1', 'new-MD-E2', 'new-MD-E3', 'new-MD-E4', 'new-MD-E5', 'new-IV-E1']))
w('6. Events from PBP plus scoreboard: possessions, chances (R-DQ-06, R-SY-05), shot-clock resets (R-SY-08), fouls, free throws, timeouts, restarts, made baskets (R-MB-*), discrepancy flags (R-SB-*), end-of-game reconciliation (%s).' % N('new-DQ-2'))
w('7. Vision: detections, tracks, identity within the PBP lineup (R-ID-03), positions with sigma (R-CG-08, %s), ball states; physics key (R-IV-13).' % N('new-DT-E1'))
w('8. Quality: invariant break rates (%s), event-volume sanity (%s), game-1 regression fixture (%s), throughput and size per stage (%s), held-out register (%s).' % tuple(N(x) for x in ['new-DQ-E1', 'new-DQ-E3', 'new-DQ-E2', 'new-CS-E1', 'new-VA-S1']))
w('')

w('## 8. Code findings already resolved')
w('')
w('The engineer\'s markets findings M1-M5 are fixed in `src/msu_alpha/markets/` with regression tests in `tests/markets/test_engineer_review_fixes.py` (uncommitted working-tree changes on 2026-10-18). They are recorded as resolved in R-MK-27, R-MK-13 and R-RG-11; the matching proposals (new-MK-E1, new-MK-E2, new-RG-E1) are absorbed, not renumbered.')
w('')
w('| # | File | Finding | Status | Requirement |')
w('| --- | --- | --- | --- | --- |')
for f in ydoc['resolved_code_findings']:
    w('| %s | %s | %s | %s | %s |' % (f['id'], f['file'], f['finding'], f['status'], f['requirement']))
w('')

w('## 9. Decisions for Aldemir')
w('')
w('Conflict decisions first (K01-K29), then the open questions of the six inputs, de-duplicated (D01-D45). Recommendation in brackets.')
w('')
for dd in DEC:
    w('- **%s** %s [%s] (%s)' % (dd['id'], dd['decision'], dd['recommendation'] if dd['id'].startswith('D') else 'see section 2', dd['source']))
w('')

w('## 10. Sources opened for this synthesis (2026-10-18)')
w('')
w('Repo: `docs/requirements_review/quality_review.md`, `acceptance_tests.yaml`, `perspective_espn_analyst.md`, `perspective_data_engineer.md`, `perspective_team_data_scientist.md`; `docs/data/gap_closures_round2.md`, `docs/data/court_constants_check.md`, `docs/data/dictionary_games.md` and `dictionary_players.md` (proposal lines only); `schema/tables_proposed_changes.yaml`; `config/vocab/*.yaml` (headers, requirements lists, open questions); `config/game_ontology.yaml` (leaves and gaps = inbox 007 proposals); `config/invariants.yaml` (new-IV statements, corrections); `coord/requirements_inbox/006-data-dictionary-and-first-games.md`, `006-markets-requirements.md`, `007-game-ontology-gaps.md`; `src/msu_alpha/markets/` working-tree diff and `tests/markets/test_engineer_review_fixes.py`. Scratchpad: `brief_panel.md`, `brief_improve.md`, `brief_003.md`, `live_doc2/requirement_ids.md` (518 IDs). No web pages, APIs or data providers were called for this synthesis; rule numbers are cited as verified in the inputs.')
w('')
open(R + 'docs/requirements_review/synthesis.md', 'w').write('\n'.join(L))
print('md ok', sum(len(x) for x in L))

# ======================================================================= inbox 008
I = []
w = I.append
w('# Requirements inbox 008 · Requirements improvement: consolidated proposal set')
w('')
w('From: requirements improvement synthesis (2026-10-18). To: requirements session. Status: proposal, not yet agreed with Aldemir. Nothing in the live doc, `config/`, `schema/` or `src/` was edited by this pass; the markets fixes in `src/msu_alpha/markets/` were made earlier today by the main session and are only recorded here.')
w('')
w('## What was produced (add-only)')
w('')
w('| File | Content |')
w('| --- | --- |')
w('| `docs/requirements_review/synthesis.md` | Perspective synthesis (Think, Understand, Analyze), %d conflicts with resolutions, top 15 changes, merged verdicts, the N-series, the game-flow spine, the minimum build, resolved code findings, decisions |' % len(K))
w('| `docs/requirements_review/proposals_consolidated.yaml` | Machine-readable: `existing_verdicts` (518), `new_requirements` (%d), `id_map` (%d rows), `conflicts`, `decisions`, `game_flow_spine`, `minimum_build_first_two_games`, `resolved_code_findings`; validated with yaml.safe_load |' % (len(NEW), len(IDMAP)))
w('| this file | how to apply, counts, decisions |')
w('')
w('Inputs consolidated: quality review + acceptance tests (518 IDs, 181 with issues), the three panel reviews (ESPN analyst, data engineer, NBA team data scientist), round-2 gap closures (71 requirements, 185 columns), the rules vocabularies and court-constants check, inbox 007 (93), `config/invariants.yaml` (new-IV-01..34), inbox 006 (dictionaries, markets).')
w('')
w('## Counts')
w('')
w('- Existing IDs: 518 merged verdicts: ' + ', '.join('%s %d' % (v, vc.get(v, 0)) for v in VORD) + '.')
w('- New proposals read: %d; absorbed into existing IDs: %d; merged into %d N-requirements (P0 %d, P1 %d, P2 %d; Shall %d, Should %d).' % (n_raw, n_abs, len(NEW), npr['P0'], npr['P1'], npr['P2'], ntier.get('Shall', 0), ntier.get('Should', 0)))
w('- N-requirements per family: ' + ', '.join('%s %d' % (f, sum(c.values())) for f, c in sorted(nfam.items())) + '.')
w('- Inbox 006 markets proposals: all %d already in the live doc as R-MK-12..33 (mapped in id_map).' % rel['already_in_live_doc'])
w('- Conflicts resolved: %d (K01-K29); open decisions after de-duplication: %d (D01-D45).' % (len(K), len(DEC) - len(K)))
w('- Game-flow spine: %d transitions (T00-T24 with T03a/T03b) and %d decision points, every transition with detection, timing and analysis requirements.' % (len(SPR), len(DPR)))
w('- Minimum build for the first two games: %d table entries (the engineer\'s 43 plus video_segments, pbp_versions, stat_corrections, stage_outputs); %d existing and %d new P0 requirements.' % (len(b['TABLES']), len(p0_ex), len(p0_new)))
w('- Code: markets findings M1-M5 resolved in code with regression tests (recorded in R-MK-27, R-MK-13, R-RG-11); M6 (atomic writes) and M8 (schema_version in Parquet metadata) remain open as %s and R-MK-31.' % N('new-EN-E2'))
w('')
w('## How to apply (order)')
w('')
w('1. **Decisions first.** Get Aldemir\'s answers to K01-K29 (they set config values that several rewrites cite) and to D01-D06 (rules corrections, R-RL, officials, 43-table build, pass enum, global metadata).')
w('2. **Rules layer.** Adopt the rules edition (%s, %s), the 13 rule-number corrections and the N-IV invariants (was new-IV-01..34; new-IV-12 folds into R-IV-10, new-IV-34 into R-IV-13), the 41-cause shot-clock list (K18), the foul classes (R-RF-03) and the edge-correct court constants (%s, %s). Many rewrites cite these.' % (N('new-RL-1'), N('new-RL-2'), N('new-CG-1'), N('new-CG-2')))
w('3. **Merge-into rows** (%d): mark each superseded row "superseded by <ID>" (add-only, row kept) before editing the keepers, so no edit lands on a superseded row.' % vc['merge-into'])
w('4. **Splits** (%d): add the child rows ID-a, ID-b (ID-c) with their own tier and test; keep the parent as a pointer.' % vc['split'])
w('5. **Rewrites, then tighten and loosen** (%d, %d, %d): replace text and Test cells from `existing_verdicts`; numbers marked "(proposal)" or "(initial value, to calibrate)" stay marked; tier changes (R-SB-04, R-SR-11 to Shall; R-PL-01 to Should) per D17.' % (vc['rewrite'], vc['tighten'], vc['loosen']))
w('6. **New requirements**: add the N-series by priority (P0, then P1, then P2), renumbering into R-<FAMILY>-nn freely; keep the N-ID and the old IDs in a "was" column so the id_map survives. New family R-RL if D02 is yes.')
w('7. **Schema**: for P0 only, add `clock_map`, `state_transitions`, `state_segments`, `video_segments`, `pbp_versions`, `stat_corrections`, `stage_outputs`, `frames.stage_mask` and the key fixes (pass in frame PKs, time_base keys, game_id in state-table PKs); apply `schema/tables_proposed_changes.yaml` columns for the adopted N-requirements; regenerate specs in one dialect (R-EN-01).')
w('8. **Tests and ontology**: copy the acceptance criteria into `acceptance_tests.yaml`, then run the ontology check (%s) so every leaf, ID and column stays traced.' % N('new-CD-2'))
w('')
w('## Decisions for Aldemir (one line each)')
w('')
for dd in DEC:
    rec = ('[recommended: %s]' % dd['recommendation']) if dd['id'].startswith('D') else '[see synthesis section 2]'
    w('- %s: %s %s' % (dd['id'], dd['decision'], rec))
w('')
open(R + 'coord/requirements_inbox/008-requirements-improvement.md', 'w').write('\n'.join(I))
print('inbox ok')
