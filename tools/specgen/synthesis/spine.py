# Game-flow spine: rules-exact transitions (data engineer T01-T24, ESPN analyst S0-S11, scientist table,
# config/vocab restarts/shot_clock_resets/fouls/violations) with the requirements that cover detection, timing and analysis.
# Old proposal IDs are resolved to N-ids by build.py.
SP = []
def t(tid, frm, to, trigger, rule, clocks, det, tim, ana):
    SP.append(dict(id=tid, frm=frm, to=to, trigger=trigger, rule=rule, clocks=clocks, det=det, tim=tim, ana=ana))

t('T01', 'S0 pre-period / S1 jump ball', 'S6 loose ball (no team control)', 'toss leaves the official\'s hand; legal tap', '6-1.2.a, 6-2, 6-3, 5-10.2.b',
  'GC starts on the legal tap; SC off until control', ['R-DT-15', 'R-EV-14', 'new-EV-1'], ['new-SR-2', 'new-MD-E1', 'R-SR-01'], ['R-EV-14', 'new-IV-19', 'R-MD-12'])
t('T02', 'S6 no control', 'S3/S4 team control', 'player gains control after a jump ball or a try', '4-9, 2-11.5.b, 5-10.3.b',
  'SC starts (30, or 20 flat after ring contact)', ['R-BL-02', 'R-MD-02', 'R-SR-06'], ['new-IV-01', 'R-MD-06', 'R-SY-08'], ['R-MD-04', 'R-SY-04', 'R-SR-05'])
t('T03', 'S3/S4 team A control', 'S3 team B control (live)', 'steal, defensive rebound, loose-ball recovery', '2-11.6.b.1, 2-11.6.b.4, 4-9',
  'SC to 30 on control; GC runs', ['R-EV-09', 'R-EV-08', 'R-EV-10', 'R-BL-02'], ['R-SY-08', 'new-SY-E3', 'new-SY-E1'],
  ['R-TR-08', 'R-TR-09', 'R-TR-22', 'new-DF-A8', 'R-TR-26', 'R-VL-01'])
t('T03a', 'S3 backcourt control', 'S4 frontcourt control', 'ball and both feet of the dribbler (or holder) in the frontcourt', '9-10, 9-12.1-3',
  'GC and SC run; 10-s count stops', ['new-MD-6', 'new-SR-4'], ['new-IV-01', 'new-SR-4'], ['R-TR-20', 'new-DF-8', 'R-ST-19'])
t('T03b', 'S4a primary transition', 'S4b early offense -> S4c half-court', '3 defenders back; defense set (all 10 in the half-court, every attacker guarded within 2.0 m goal-side for 1 s)', 'project definition (R-TR-08/09), no rule',
  'GC and SC run', ['R-TR-08', 'R-TR-12', 'R-DF-20'], ['R-TR-01', 'R-TR-20'], ['R-TR-09', 'R-TR-18', 'R-TR-24', 'R-ST-05', 'new-ST-A10'])
t('T04', 'S4 team control', 'S5 try in flight', 'release of a try (the try starts with the shooting motion)', '5-1.10, 6-6.1, 4-9.4',
  'GC and SC keep running; ball stays live through a whistle until the try ends', ['R-BL-04', 'R-EV-07', 'new-EV-20'], ['R-BL-04', 'R-MB-06', 'new-IV-06'],
  ['R-VL-04', 'new-VL-3', 'new-DF-S3', 'new-MD-S1', 'new-VL-S3', 'R-CO-01'])
t('T05', 'S5 try in flight', 'S7 dead (made goal) -> S2 throw-in', 'ball passes through the basket', '6-5.1.a, 5-1, 5-11.9, 2-10.12',
  'GC keeps running except in the last 59.9 s of the 2nd half and OT; SC to 30 on the opponent\'s inbound touch', ['R-MB-01', 'R-MB-02', 'R-MB-03', 'R-BL-05', 'new-MB-1'],
  ['R-MB-04', 'R-SB-03', 'new-SY-E4', 'new-IV-31', 'new-IV-22'], ['R-SR-02', 'R-MD-17', 'new-EV-A14', 'R-TR-23', 'R-DF-18'])
t('T06', 'S5 try in flight (ring contact)', 'S4 offensive control: new chance, same possession', 'offensive rebound after ring or flange contact', '2-11.6.d.1',
  'SC flat 20 s whatever was left', ['R-MB-07', 'R-EV-08', 'new-EV-22'], ['new-IV-02', 'R-SY-08', 'R-SY-09'], ['R-DQ-06', 'R-SY-05', 'new-VL-S2', 'R-VL-01'])
t('T07', 'S5 try in flight (no ring contact)', 'S4 offensive control: same chance', 'airball rebounded by the offense', '2-11 (no reset listed), 9-11',
  'SC continues; violation if it expires', ['R-MB-07', 'R-BL-08'], ['new-IV-04', 'new-IV-06'], ['R-SY-05', 'R-DQ-06'])
t('T08', 'S5 try in flight / S6 loose', 'S3 defensive control', 'defensive rebound (incl. team and dead-ball rebounds as recorded)', '2-11.6.b.4, 4-30.1',
  'SC 30', ['R-EV-08', 'new-EV-22'], ['R-SY-08', 'new-SY-E3'], ['R-TR-08', 'new-VL-S2', 'R-DQ-06', 'new-VL-S3'])
t('T09', 'S3-S6 live', 'S7 dead (foul)', 'whistle for a foul', '5-11.1.a, 6-5.1.d (6-6.1 if a try is in flight), 4-15, 10-1',
  'GC and SC stop; SC per the reset table', ['R-RF-01', 'R-RF-02', 'R-RF-03', 'new-RF-5', 'R-RF-04', 'new-RF-10'],
  ['new-RF-A13', 'R-SR-01', 'new-MD-E1'], ['R-SR-03', 'R-MD-07', 'R-MD-16', 'new-RF-1', 'new-CG-2', 'new-CC-A5', 'new-IV-11', 'new-IV-32'])
t('T10', 'S7 dead (foul)', 'S8 free-throw sequence', 'foul with a free-throw award (shooting, 7th team foul one-and-one, 10th double bonus, technical, flagrant)', '8-2.1, 8-2.2, 10-1 Penalty, 10-3, 10-4',
  'GC stopped through the free throws', ['R-SR-09', 'R-DT-13'], ['new-IV-07', 'new-IV-08', 'new-IV-10', 'new-IV-29'], ['R-SR-09', 'new-CH-2', 'new-IV-25'])
t('T11', 'S7 dead (foul or violation)', 'S2 throw-in pending', 'common foul before the bonus, player-control foul, violation, out of bounds', '10-1 Penalty a, 7-3.2, 7-2, 9-x',
  'SC 30 (backcourt or change of control) or max(20, left) (defensive foul or kicked ball, frontcourt)', ['R-DT-14', 'R-SR-08', 'R-DT-19', 'new-BL-2'],
  ['new-IV-03', 'new-IV-18', 'R-SY-08'], ['R-SY-04', 'new-EV-18', 'R-DQ-06'])
t('T12', 'S8 FT k of n', 'S8 FT k+1 / S6 live rebound / S2 throw-in', 'each attempt result', '8-5, 8-6, 8-7, 5-10.2.c',
  'GC starts only when a missed last FT is legally touched', ['R-SR-09'], ['new-IV-09', 'new-SR-2'], ['R-SY-05', 'R-DQ-06'])
t('T13', 'S3/S4 live', 'S7 dead (violation) -> S2 throw-in', 'travel, illegal dribble, 3 s, 5 s closely guarded, 10 s backcourt, backcourt, kicked ball, out of bounds, elbows', '6-5.1.g, 9-3 to 9-14, 7-1, 7-2',
  'GC and SC stop; SC per the reset table', ['R-EV-10', 'new-EV-2', 'new-MD-6', 'new-SR-4', 'new-SR-5', 'new-ST-1', 'new-BL-2', 'new-DT-4'],
  ['R-SY-08', 'new-IV-15', 'new-IV-17'], ['R-VL-11', 'new-ST-A11', 'R-DQ-06'])
t('T14', 'S3-S6 live', 'S7 dead (held ball) -> S2 arrow throw-in', 'held ball', '6-5.1.c, 6-3, 6-4',
  'SC per arrow: no reset / 30 / 20 (2-11.6.a.4, b.3, d.4); arrow flips when the AP throw-in ends', ['R-DT-15', 'R-EV-14'], ['new-IV-04', 'R-SY-08'], ['R-MD-12', 'new-IV-19'])
t('T15', 'S2 throw-in pending', 'S3/S4 live, clocks running', 'ball at the thrower\'s disposal, then legal touch inbounds', '6-1.2.b, 7-6.6, 5-10.2.a, 5-10.3.a, 5-10.2.d',
  'GC and SC start on the touch; >= 0.3 s off in the last 59.9 s', ['R-DT-14', 'new-EV-18'], ['new-IV-16', 'new-IV-22', 'new-SR-2', 'new-IV-01'],
  ['R-DF-18', 'new-DF-8', 'R-TR-21', 'R-MD-03'])
t('T16', 'S7 any dead ball (or live with control, last 2:00 for the head coach)', 'S9 timeout (team or media)', 'request granted, or first dead ball at or after a media mark', '5-11.3, 5-11.4, 5-14, 5-14.10.c-e',
  'stopped; timeouts left decrease; SC no reset (2-11.6.a.3)', ['R-EV-15', 'R-EV-11'], ['new-IV-13', 'R-IV-10', 'new-IV-28', 'R-SR-04', 'R-MD-13'],
  ['new-CC-A6', 'R-CC-02', 'R-CH-06', 'new-CH-S1', 'new-HY-S1', 'R-SY-04'])
t('T17', 'S3-S9', 'S10 review / coach\'s challenge', 'official review or challenge', '11-2, 11-3, 11-4, 5-15.1.e',
  'frozen; may correct score, clock, possession; failed challenge costs the timeout', ['R-EV-16', 'R-RF-07'], ['new-IV-14', 'new-IV-27'], ['R-EV-16', 'new-SY-E5'])
t('T18', 'any state value', 'corrected value', 'timing or scoring correction', '5-12.1-5, 2-9.13, 11',
  'GC may go up (Louisville 4:06 -> 4:07, measured); never carried across halves', ['new-SY-E5', 'R-SB-01', 'R-SB-02'], ['R-IV-05', 'new-IV-27'], ['new-SY-E2', 'new-DQ-2'])
t('T19', 'SC on / off', 'SC off / on at 20', 'game clock below a shot-clock period; 2-11.6.d situation', '2-11.2, 2-11.8',
  'SC display blank; reactivated at 20 s', ['R-SY-01'], ['new-IV-05'], ['R-SR-11', 'new-ST-A11', 'R-PE-07'])
t('T20', 'S3-S6 live', 'S11 end of period', 'game clock reaches 0.0 (try in flight completes)', '5-7, 5-11.2.a, 5-1.19',
  'GC 0.0; tap-only rule at <= 0.3 s', ['new-AU-3', 'R-SY-01'], ['new-IV-23', 'R-MB-06', 'new-IV-22'], ['R-SR-11', 'R-PE-07', 'new-ST-A11'])
t('T21', 'S11 end of period', 'S0 intermission -> next period', 'half time; 1-minute intermission before each extra period', '5-8, 5-9, 6-3.6',
  'team fouls reset at the 2nd half only; extra periods continue them; baskets change at half only', ['new-SR-1'], ['new-IV-20', 'new-IV-21', 'R-IV-09'], ['R-CH-06', 'new-VZ-A1'])
t('T22', 'S7 dead (clock stopped)', 'S7 dead (new lineup)', 'substitute beckoned', '3-6, new-IV-25, new-IV-26',
  'none', ['R-EV-11', 'new-SY-A4'], ['new-IV-25', 'new-IV-26'], ['R-MD-15', 'new-MD-12', 'new-CH-S1', 'R-CC-03', 'new-CC-A5'])
t('T23', 'S3-S6 live', 'S7 dead (injury, blood, official stoppage)', 'official suspends play', '5-11.2.b, 5-11.6-5-11.8',
  'stopped; SC no reset (2-11.6.a.2)', ['R-EV-11'], ['new-IV-04'], ['new-FD-3'])
t('T24', 'S11 last period', 'final / forfeit', 'last period ends with a winner', '5-6, new-IV-30',
  'none', ['R-FD-01', 'new-FD-2'], ['new-IV-30'], ['new-DQ-2', 'R-DQ-06', 'R-DQ-01'])
t('T00', 'any', 'observed / not observed', 'camera cut, replay, graphics, condensed-replay edit', 'none (broadcast director)',
  'video time stops being linear in game clock', ['R-VI-03', 'R-VI-04', 'R-VI-05', 'new-VI-5'], ['new-VI-E1', 'new-MD-E1', 'new-VI-E2'], ['R-PL-05', 'R-VI-06', 'new-VA-S5'])

# Decision points inside the flow (where a team reacts) -> requirements that capture the decision.
DP = [
 ('Push or pull back after a change of control', 'ball handler, team rule', '0-3 s after the secure', ['R-TR-16', 'R-TR-24', 'R-TR-26', 'new-DF-A8']),
 ('Inbound fast after a make; press or not', 'inbounder, defensive coach', '0-3 s after the net; pre-planned', ['R-TR-21', 'R-TR-23', 'R-DF-18', 'R-DF-12', 'new-DF-8']),
 ('Set call', 'coach or point guard', 'dead ball or half-court crossing', ['R-ST-05', 'R-ST-07', 'new-MD-A6']),
 ('Ball-screen coverage and handler read', 'X-big, X-ball; handler', 't0 - 1.0 s to t0 + 2.0 s', ['R-ST-17', 'R-ST-20', 'R-DF-16', 'R-DF-06', 'new-DF-S1', 'new-ST-A9']),
 ('Catch: shoot, pass, drive, hold', 'receiver', '0.2-3 s per touch', ['R-CO-01', 'new-MD-S1', 'R-VL-05']),
 ('Help or stay on a drive or skip', 'help defender, low man', '0.2-1.5 s after the trigger (calibrate)', ['R-DF-08', 'R-CO-02', 'new-EV-S1']),
 ('Double the post', 'defensive plan', '0-1.5 s after the post catch', ['R-DF-07', 'new-DF-9']),
 ('Crash or get back at the release', 'all 10 players', 'at release to rim contact', ['new-VL-S3', 'new-EV-22', 'R-EV-08']),
 ('Foul or not late (take foul, foul up 3, foul to extend)', 'defender, coach', 'last 60 s', ['R-PE-07', 'R-SR-11', 'R-TR-25']),
 ('Timeout or challenge', 'head coach', 'any dead ball; live in the last 2:00', ['new-CC-A6', 'R-EV-16', 'R-CC-02']),
 ('Substitution, foul-trouble sit', 'head coach', 'next dead ball', ['new-CC-A5', 'R-CC-03', 'new-SY-A4']),
 ('Scheme change (zone, press, switch)', 'defensive coach', 'next dead ball, 1-3 possessions after the trigger', ['R-DF-19', 'new-CH-S1', 'new-ST-A10', 'new-DF-A6', 'new-HY-S1']),
 ('End of clock: hold, two-for-one, last shot', 'coach, handler', '33-45 s window; SC <= 7 s', ['R-SR-11', 'new-ST-A11', 'R-PE-07']),
 ('Whistle or play on', 'calling official', 'contact to whistle < 1 s (unverified)', ['new-RF-A13', 'new-RF-9', 'R-DT-12']),
]
