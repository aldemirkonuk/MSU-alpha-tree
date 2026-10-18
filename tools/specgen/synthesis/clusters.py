# Cluster definitions for NEW requirement proposals.
# Every raw proposal id lands in exactly one cluster (-> one N-id) or is absorbed into an existing live ID.
# Fields: p = primary old id; m = other members merged in; fam = N family (default: primary's family);
# pr = priority P0/P1/P2; lv = ontology leaves (default: from source); t/a/tier/lands override text, acceptance, tier, table.

# Dictionary-level proposals (inbox 006 / docs/data/dictionary_*.md), not in any table format elsewhere.
DICT = {
 'new-PC-1': dict(tier='Should', text='Store the team-captain flag per player-season with its source (school site or announcement).',
                  acc='Filled (true/false) or "not public" for 100% of MSU players; every true value has a source URL and date.',
                  lands='players.captain_flag (dictionary_players.md)', leaf=['C.01.17']),
 'new-PC-2': dict(tier='Should', text='Store roster status per player-season (scholarship, walk-on, preferred walk-on, manager-turned-player, unknown) with source.',
                  acc='Filled or "unknown" for 100% of MSU players; every non-unknown value has a source and date.',
                  lands='players.roster_status (dictionary_players.md)', leaf=['C.01.02']),
 'new-PC-3': dict(tier='Should', text='Store shoe size (US men\'s) where published, for a CV foot-size scale check.',
                  acc='Field present; filled or "not public" (expected ~0% public).',
                  lands='players.shoe_size_us (dictionary_players.md)', leaf=['C.01.05']),
 'new-PC-4': dict(tier='Should', text='Store shooting hand (L/R) per player from release pose with the number of clear releases seen, and use it as an identity tie-breaker (R-ID-13).',
                  acc='Value only with n >= 10 clear releases; agrees with film labels for 100% of MSU players with n >= 10.',
                  lands='players.shooting_hand, shooting_hand_n', leaf=['C.01.08', 'L.06.06']),
 'new-PC-5': dict(tier='Should', text='NIL valuation fields (published value, kind: model estimate, reported deal, public record; public deals) kept as exploratory context only.',
                  acc='Every value has source, date and kind.', lands='players.nil_valuation_usd, nil_valuation_kind, nil_deals_public', leaf=['C.01.14']),
 'new-DS-1': dict(tier='Shall', text='Player-level crosswalk ESPN athlete ID <-> CBBD athlete ID <-> NCAA engine player ID <-> Torvik/KenPom/EvanMiya name strings, versioned, in id_crosswalk.',
                  acc='100% of PBP athlete IDs of in-scope games resolve.', lands='id_crosswalk', leaf=['M.02.04', 'C.01.01']),
 'new-SY-1': dict(tier='Should', text='Source garbage-time flags stored per possession (possessions.is_garbage_time_source), never used to drop rows.',
                  acc='Flag stored for 100% of possessions where the source has one; 0 rows dropped by it.', lands='possessions.is_garbage_time_source', leaf=['D.02.04']),
 'new-FD-1': dict(tier='Should', text='Source game-flow descriptors kept on the registry row (CBBD excitement; KenPom excitement/tension/dominance if the API is bought), post-game only.',
                  acc='Stored with source and as-of = post-game; 0 pre-game features read them (leakage lint).', lands='games.excitement_cbbd', leaf=['A.01.06']),
 'new-CG-2': dict(tier='Shall', text='The restricted-area membership test uses the outer edge of the arc, r <= 1.270 m (1.2192 m inner radius + 0.0508 m line), with straight segments to the backboard face at y = -0.381 m; the frontcourt test uses the near edge of the division line (y < 12.700 m in the attacked-rim frame).',
                  acc='Unit tests: feet at r = 1.25 m return inside the restricted area; a foot at y = 12.71 m returns backcourt.',
                  lands='config/vocab/court_constants_proposed.yaml; src/msu_alpha/geometry.py', leaf=['B.01.07', 'B.01.04', 'A.06.06']),
 'new-RL-2': dict(tier='Shall', text='The rules edition of a game is the record of config/vocab/rules_edition.yaml whose season window (1 July - 30 June, our convention) contains the local tip date; a game outside every window gets rules_edition_id = unknown and every rule-derived check is skipped and flagged.',
                  acc='100% of registered games carry an edition or "unknown"; a 2014-15 game resolves to the 35-s-shot-clock edition or "unknown", never to 2026-27; unit test on boundary dates.',
                  lands='games.rules_edition_id; config/vocab/rules_edition.yaml', leaf=['A.01.10']),
}

C = []
def c(p, m=(), fam=None, pr='P1', lv=None, t=None, a=None, tier=None, lands=None, into=None, note=None):
    C.append(dict(p=p, m=list(m), fam=fam, pr=pr, lv=lv, t=t, a=a, tier=tier, lands=lands, into=into, note=note))

# ---------------- absorbed into existing live IDs (no N-id) ----------------
c('new-RF-3', into='R-RF-03', note='R-RF-03 rewrite carries the 2026-27 foul classes and the legacy "intentional" mapping')
c('new-EV-3', into='R-EV-10', note='backcourt over-and-back added to the turnover list')
c('new-EV-4', into='R-EV-10', note='elbows added to the turnover list')
c('new-SY-2', into='R-SY-08', note='full shot-clock cause list (41 causes, config/vocab/shot_clock_resets.yaml)')
c('new-EN-E4', into='R-EN-07', note='partition layout with manifests and current pointer')
c('new-VL-S4', into='R-VL-01', note='value layers stored side by side')
c('new-RG-E1', into='R-RG-11', note='shared private-root guard and pre-commit hook; markets RawStore part fixed 2026-10-18')
c('new-MK-E1', into='R-MK-27', note='RESOLVED in code 2026-10-18 (dedup_key includes source_event_id; CBBD reported rows keyed on scheduled tip); regression tests in tests/markets/test_engineer_review_fixes.py')
c('new-MK-E2', into='R-MK-27', note='RESOLVED in code 2026-10-18 (store skips keys already present: idempotent across runs)')
c('new-IV-12', into='R-IV-10', note='timeout allotment per media format')
c('new-IV-34', into='R-IV-13', note='court and ball-height bounds join the shared physics key')
c('new-DS-1', into='R-DS-05', note='player-level, bitemporal crosswalk')

# ---------------- clock, state and sync backbone (engineer-led) ----------------
c('new-MD-E1', into='R-MD-08', note='clock_map becomes the R-MD-08 rewrite')
c('new-SY-E6', into='R-MD-08', note='UTC from monotone wall clock only')
c('new-MD-E2', pr='P0', lv=['D.02.01', 'D.04.01', 'D.10.03', 'M.06.01'])
c('new-MD-E3', pr='P0', lv=['D.01.01', 'D.03.01', 'M.06.01'])
c('new-MD-E4', pr='P0', lv=['A.02.06', 'M.02.06', 'J.05.03'])
c('new-MD-E5', pr='P0', lv=['M.02.05', 'M.02.02'])
c('new-SY-E1', m=['new-SR-A6'], pr='P0', lv=['A.04.09', 'D.03.02', 'D.08.01', 'M.03.02'],
  t='Log every game-state change as one typed transition of the rules state machine (config/state_machine.yaml: T01-T24 and subtypes, each with its rule reference and the allowed from -> to pairs), with all four clocks, trigger event and the sources that observed it; the analyst flow state (S0-S11, S4 split into primary transition, early offense, half-court) is a dimension of state_segments, so per-frame flow_state is a view; a disallowed transition is an invariant break.',
  a='0 untyped transitions; every state_segments boundary references one transition; disallowed transitions = 0 on gold-v1 or each explained in review; transition count per type reported per game.',
  lands='new table state_transitions; new config/state_machine.yaml; state_segments.dimension = flow_state (view state_frame.flow_state)')
c('new-SY-E2', m=['new-DQ-A3'], pr='P0', lv=['M.02.01', 'A.05.06', 'M.03.04'],
  t='Every pull of PBP and of the official box score is stored as a version with a content hash; a diff (plays added, removed, changed; box stats re-credited with old and new value) is computed; downstream tables and published outputs that used a changed value are rebuilt and marked; the official box is re-pulled weekly for processed games.',
  a='Re-pull with no change -> 0 rebuilt tables; an injected change -> only dependent tables rebuilt (test); 100% of box diffs logged; dependent outputs re-run within 7 days.',
  lands='new tables pbp_versions (game_id, source, pull_id, sha256, n_plays, n_added, n_removed, n_changed, known_at_utc) and stat_corrections (game_id, player_id, stat, old, new, seen_utc, source)')
c('new-SY-E3', pr='P0', lv=['M.02.06', 'D.01.02'])
c('new-SY-E4', m=['new-SY-A5'], pr='P0', lv=['L.03.03', 'L.03.02'],
  t='Estimate scorebug lag per game and per field (score, game clock start/stop, shot clock reset, fouls, timeouts) from events whose true time is seen on video, and use lag-corrected times for state while keeping raw read times.',
  a='>= 10 events per field per game; lag median and IQR in the run record; after correction the score-change time is within +/- 0.5 s of the ball-through-net frame on >= 95% of makes (raw lag 1.50-2.60 s measured); state uses corrected times on 100% of OCR-sourced changes.',
  lands='scoreboard_ocr.read_ts_ms (raw); new view scorebug_lag (game_id, field, n, p50_s, p90_s, p95_s); corrected *_time_s columns')
c('new-SY-E5', pr='P0', lv=['A.02.05', 'A.05.06'])
c('new-SY-A4', pr='P1', lv=['A.11.02', 'A.11.06', 'D.07.01'])
c('new-VI-E1', pr='P0', lv=['L.01.02', 'L.02.06', 'A.02.06'])
c('new-VI-E2', pr='P0', lv=['L.02.04', 'M.05.03'])
c('new-FD-E1', pr='P0', lv=['A.01.09', 'L.03.01', 'A.10.02'])
c('new-IV-E1', pr='P0', lv=['M.03.02'])

# ---------------- engineering, compute, run records ----------------
c('new-EN-E1', pr='P0', lv=['M.05.04'])
c('new-EN-E2', pr='P0', lv=['M.05.04'])
c('new-EN-E3', pr='P0', lv=['M.02.06', 'M.05.04'])
c('new-EN-E5', into='R-EN-01', note='one dialect and validator')
c('new-EN-E6', pr='P1', lv=['M.06.01'])
c('new-EN-E7', pr='P1', lv=['M.06.01', 'M.06.02'])
c('new-EN-E8', pr='P0', lv=['M.05.04'])
c('new-EN-A1', pr='P1', lv=['M.05.03', 'L.05.04'])
c('new-CS-E1', pr='P0', lv=['M.05.03'])
c('new-CS-E2', pr='P1', lv=['M.05.03'])
c('new-RR-E1', pr='P0', lv=['M.05.01'])

# ---------------- data quality and validation ----------------
c('new-DQ-E1', pr='P0', lv=['M.03.02', 'M.05.01'])
c('new-DQ-E2', pr='P0', lv=['M.03.07', 'M.04.03'])
c('new-DQ-E3', pr='P0', lv=['M.03.03'])
c('new-DQ-A2', pr='P1', lv=['L.05.02', 'H.02.01', 'M.03.04'])
c('new-DQ-2', pr='P0')
c('new-DQ-3', pr='P1')
c('new-DQ-4', pr='P2')
c('new-VA-E1', pr='P0', lv=['M.04.03', 'A.02.06', 'L.06.11'])
c('new-VA-S1', pr='P0', lv=['H.05.08', 'M.04.04'])
c('new-VA-S2', pr='P1', lv=['M.02.05'])
c('new-VA-S3', pr='P1', lv=['H.04.03', 'M.04.05'])
c('new-VA-S4', pr='P1', lv=['M.03.05', 'H.05.05'])
c('new-VA-S5', pr='P1', lv=['I.03.06', 'L.02.04', 'M.04.04'])
c('new-HY-S1', pr='P1', lv=['M.06.07', 'J.06.01', 'G.06.01'])

# ---------------- kinematics uncertainty ----------------
c('new-DT-E1', m=['new-PL-S1'], pr='P0', lv=['I.01.01', 'I.03.06', 'L.06.05'],
  t='Every position, speed, acceleration and heading value carries a propagated 1-sigma (position_sigma_m, speed_sigma_mps, accel_sigma_mps2, heading_sigma_deg) from mapping confidence, detection and the named filter; bias and SD measured on hand-timed runs and gold positions (R-PL-13) are propagated by simulation into every reported load and athletic interval.',
  a='Sigma present on 100% of rows; 68% intervals cover 60-76% of hand-measured values per court zone; every load and athletic metric shows an interval that includes measurement error.',
  lands='player_positions.position_sigma_m, speed_sigma_mps, accel_sigma_mps2, heading_sigma_deg; load_stint_bins, accel_efforts, profile_snapshots intervals')
c('new-PL-E1', pr='P1', lv=['I.02.01', 'I.02.02', 'I.03.06'])
c('new-DF-S3', into='R-EV-07', note='contest unknown, never imputed')

# ---------------- rules layer, court, rules-domain inbox 007 ----------------
c('new-RL-1', pr='P0')
c('new-RL-2', fam='RL', pr='P0')
c('new-CG-1', pr='P0')
c('new-CG-2', fam='CG', pr='P1')
c('new-SR-1', pr='P1')
c('new-SR-2', pr='P1')
c('new-SR-4', pr='P1')
c('new-SR-5', pr='P1')
c('new-SY-3', pr='P1')
c('new-EV-1', pr='P2')
c('new-EV-2', pr='P1')
c('new-MB-1', pr='P1')
c('new-ST-1', pr='P1')
c('new-RF-1', pr='P1')
c('new-RF-2', pr='P1')
c('new-RF-4', pr='P1')
c('new-RF-5', pr='P1')
c('new-RF-6', pr='P2')
c('new-RF-7', pr='P2')
c('new-RF-8', pr='P2')
c('new-RF-9', pr='P2')
c('new-RF-10', pr='P1')
c('new-RF-11', pr='P2')
c('new-CC-1', pr='P2')
c('new-FD-2', pr='P2')
c('new-FD-3', pr='P2')
# invariants (config/invariants.yaml new-IV-xx), one N-IV each
for i, lv, pr in [
    ('01', ['A.03.02', 'M.03.02'], 'P0'), ('02', ['A.03.04'], 'P0'), ('03', ['A.03.05'], 'P0'), ('04', ['A.03.06'], 'P0'),
    ('05', ['A.03.07'], 'P0'), ('06', ['A.03.08'], 'P0'), ('07', ['A.07.01', 'A.06.18'], 'P0'), ('08', ['A.07.01', 'A.06.02'], 'P0'),
    ('09', ['A.07.06'], 'P0'), ('10', ['A.07.04'], 'P1'), ('11', ['A.06.19', 'A.06.20', 'A.11.04'], 'P0'),
    ('13', ['A.10.02'], 'P0'), ('14', ['A.13.02'], 'P0'), ('15', ['A.04.14'], 'P1'), ('16', ['A.09.04'], 'P0'),
    ('17', ['A.04.15'], 'P1'), ('18', ['A.09.03'], 'P0'), ('19', ['A.04.07'], 'P0'), ('20', ['A.01.05'], 'P0'),
    ('21', ['A.01.01'], 'P0'), ('22', ['A.02.04'], 'P0'), ('23', ['A.01.03'], 'P0'), ('24', ['A.05.03', 'A.05.04'], 'P0'),
    ('25', ['A.07.08'], 'P1'), ('26', ['A.11.03'], 'P1'), ('27', ['A.02.05'], 'P0'), ('28', ['A.10.04'], 'P0'),
    ('29', ['A.07.03'], 'P1'), ('30', ['A.01.07'], 'P1'), ('31', ['A.05.06', 'D.01.02'], 'P0'), ('32', ['A.06.07'], 'P0'),
    ('33', ['C.04.01'], 'P0')]:
    c('new-IV-' + i, pr=pr, lv=lv)

# ---------------- dictionary-level proposals ----------------
c('new-PC-2', pr='P2')
c('new-PC-3', pr='P2', note='low value (about 0% public); candidate to drop')
c('new-PC-4', pr='P1')
c('new-FD-1', pr='P2')

# ---------------- round-2 gap closures (each refines an inbox-007 proposal unless stated) ----------------
for p, pr in [('new-MD-6', 'P1'), ('new-BL-2', 'P1'), ('new-CC-5', 'P2'), ('new-MD-7', 'P1'), ('new-FD-6', 'P2'),
              ('new-FD-7', 'P0'), ('new-ID-2', 'P2'), ('new-CX-9', 'P2'), ('new-VI-4', 'P2'), ('new-CX-10', 'P2'),
              ('new-CX-11', 'P2'), ('new-CC-6', 'P2'), ('new-RF-13', 'P2'), ('new-CX-12', 'P2'),
              ('new-MD-8', 'P0'), ('new-MD-10', 'P1'), ('new-MD-12', 'P1'), ('new-ST-9', 'P2'), ('new-PL-5', 'P2'),
              ('new-DT-3', 'P2'), ('new-DT-4', 'P2'), ('new-PL-6', 'P2'), ('new-DF-6', 'P2'), ('new-EV-14', 'P2'),
              ('new-EV-15', 'P2'), ('new-EV-16', 'P2'), ('new-EV-17', 'P2'), ('new-EV-18', 'P1'), ('new-EV-19', 'P2'),
              ('new-EV-20', 'P1'), ('new-EV-21', 'P2'), ('new-EV-22', 'P1'), ('new-ST-10', 'P1'), ('new-DF-7', 'P1'),
              ('new-CC-7', 'P2'), ('new-CO-1', 'P2'), ('new-ST-11', 'P2'), ('new-ST-12', 'P1'), ('new-ST-13', 'P1'),
              ('new-ST-14', 'P1'), ('new-ST-15', 'P1'), ('new-DF-8', 'P1'), ('new-DF-9', 'P2'), ('new-DF-10', 'P1'),
              ('new-OS-2', 'P1'), ('new-VL-4', 'P2'), ('new-VL-5', 'P2'), ('new-PL-7', 'P2'), ('new-PL-8', 'P2'),
              ('new-CX-13', 'P2'), ('new-CX-14', 'P2'), ('new-CX-15', 'P1'), ('new-CX-16', 'P1'), ('new-MK-20', 'P2'),
              ('new-CH-2', 'P1'), ('new-VI-5', 'P1'), ('new-VI-6', 'P1'), ('new-VI-7', 'P1'), ('new-AU-3', 'P1'),
              ('new-AU-4', 'P2'), ('new-DS-3', 'P1'), ('new-CD-2', 'P1'), ('new-HR-2', 'P1')]:
    c(p, pr=pr)

# merged round-2 + 007 + dictionary + perspective clusters with hand-written text
c('new-PC-9', m=['new-PC-1'], pr='P2')
c('new-PC-8', m=['new-PC-5'], pr='P2', note='keep only if Aldemir keeps NIL at all (decision)')
c('new-MD-11', m=['new-SY-1'], pr='P1',
  t='Each possession stores garbage-time flags side by side under three named definitions: the source flag (hoopR NCAA is_garbage_time and others), the CTG-adapted margin/time/starters rule (last 12:00 of the second half), and the win-probability rule (pre-possession WP > 0.98 or < 0.02 with <= 300 s left); no row is ever dropped by any of them.',
  a='All three flags present (or null with reason) on 100% of possessions; 0 rows dropped; share of possessions flagged per definition per game reported (%).',
  lands='possessions.is_garbage_time_source, garbage_time_ctg_adapted, garbage_time_wp')
c('new-VL-3', m=['new-VL-S1'], pr='P1',
  t='Each shot stores its shot-making residual (points minus shooter-agnostic expected points of R-VL-04) and, when the ball trajectory is available, a trajectory-based make probability (entry angle, depth, left-right) to reduce variance; shooter profiles report the shrunk residual per attempt with n and a 95% interval as of each date.',
  a='Residual stored for 100% of shots with xPts; per-shooter estimate shrunk toward the position-group prior with n and interval; trajectory make probability calibrated (10-bin ECE <= 0.05) on held-out games before use.',
  lands='shots.shot_making_residual, shots.p_make_traj; profile_snapshots')
c('new-EV-A14', m=['new-MD-9'], pr='P1', lv=['D.01.05', 'K.01.03', 'G.06.01'],
  t='Runs are stored as rows under each R-MD-17 definition (unanswered, broadcast a-b, register net >= 8 in 120 s of game clock), with start and end score events, points for and against, timeouts during, the event that ended the run (called timeout and which team, media timeout, opponent score, foul, period end), possessions and game-clock seconds from start to stop, and what changed at the stop (lineup, scheme, set) linked to substitutions and scheme_changes.',
  a='Every run has exactly one end row; recomputes from score_events and events (0 differences); changes link to scheme_changes and substitutions where present.',
  lands='new table runs (run_id, definition, start_s, end_s, for_pts, against_pts, ended_by, changes)')

# ---------------- ESPN analyst ----------------
for p, pr, lv in [
    ('new-MD-A6', 'P1', ['M.06.03', 'L.05.04', 'F.13.05']),
    ('new-CC-A5', 'P1', ['K.01.09', 'D.05.04']),
    ('new-CC-A6', 'P1', ['A.10.03', 'K.01.03']),
    ('new-ST-A9', 'P1', ['D.07.05', 'G.10.02']),
    ('new-ST-A10', 'P1', ['G.05.01', 'F.10.01', 'G.06.01']),
    ('new-ST-A11', 'P1', ['F.11.04', 'F.11.03', 'D.02.03']),
    ('new-DF-A6', 'P1', ['G.06.01', 'G.10.01']),
    ('new-DF-A7', 'P2', ['G.09.03', 'D.05.01']),
    ('new-DF-A8', 'P1', ['G.07.01', 'F.01.05']),
    ('new-EV-A15', 'P2', ['E.09.05', 'E.05.03', 'I.02.08']),
    ('new-RF-A13', 'P2', ['A.12.06', 'L.04.01']),
    ('new-RF-A14', 'P2', ['A.12.04', 'C.03.02']),
    ('new-RF-A15', 'P2', ['A.12.04', 'M.04.01']),
    ('new-VZ-A1', 'P1', ['L.05.02', 'M.06.09']),
    ('new-VZ-A2', 'P1', ['L.05.02', 'L.05.04']),
    ('new-VZ-A3', 'P1', ['L.05.01', 'L.02.07']),
    ('new-VZ-A4', 'P1', ['L.05.01', 'L.05.03']),
    ('new-PR-A1', 'P1', ['H.05.02', 'D.09.01']),
    ('new-PR-A2', 'P1', ['H.05.01']),
    ('new-CX-A9', 'P2', ['J.03.04', 'J.06.02'])]:
    c(p, pr=pr, lv=lv)

# ---------------- team data scientist ----------------
c('new-CH-S1', m=['new-CH-A2'], pr='P1', lv=['G.06.01', 'K.01.07', 'K.01.02', 'D.07.04'],
  t='Reaction catalogue: one row per detected reaction (trigger from the panel list: made basket, long rebound, live-ball turnover, bonus reached, timeout, ball screen, post entry, drive, skip pass, zone look, press, foul trouble, end of clock, scoring run, lineup composition change, hot shooter), response type (counter-substitution, scheme change, set family, tempo change, none), team, latency in s and possessions, plus for each trigger type the baseline rate of the same response in matched moments without the trigger.',
  a='Every scheme change, timeout and substitution linked to the nearest preceding trigger or "none"; every lineup composition change (R-MD-12 classes) has a response row; baseline rates per team-season with 95% intervals.',
  lands='reaction_events (trigger, response, lag_s, lag_poss, baseline_rate); lineup_responses view')
for p, pr, lv in [
    ('new-VL-S2', 'P2', ['E.05.05', 'H.03.07', 'E.05.03']),
    ('new-VL-S3', 'P1', ['F.12.01', 'E.05.04']),
    ('new-DF-S1', 'P1', ['G.02.01', 'F.05.03']),
    ('new-DF-S2', 'P2', ['G.04.01', 'E.07.04']),
    ('new-MD-S1', 'P1', ['F.03.01', 'D.10.01']),
    ('new-ST-S1', 'P2', ['F.13.03']),
    ('new-PC-S1', 'P1', ['H.04.03', 'C.01.21'])]:
    c(p, pr=pr, lv=lv)
c('new-EV-S1', into='R-EV-06', note='help timing on drives')
