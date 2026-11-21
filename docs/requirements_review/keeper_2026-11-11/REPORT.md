# Requirements keeper, first pass (11 Nov 2026)

Source: live doc export rev 563 (main tab) and the repo as of 11 Nov. Outputs: the private working folder. Nothing in the repo or the live doc was changed.

## Counts
- Ids: 831 (816 own rows + 15 "a" parts that exist only inside their parent row). register.jsonl has 831 rows; tools/build_register.py proves the match. The "about 990" in the brief is not what the export holds.
- Taxonomy: 10 top categories, 60 second-level (59 hold ids), 8 third-level under basketball/events.
- Status: 753 current, 41 stale, 29 superseded (12 existing pointers + 17 proposed merges), 5 unclear, 3 excluded-for-now.
- Duplicates: 17 groups to merge (16 safe, 1 owner); 15 split families copy one test into every part; 16 overlap clusters.
- Conflicts: 27 (15 requirement vs requirement, 9 requirement vs pack or measured data, 3 format); 6 safe fixes, 21 owner.
- Stale: 41 ids (31 safe, 10 owner; 15 of them only cite old inbox ids) + 16 prose passages without ids.
- Gaps: 36 baseline gaps, 8 post-freeze gaps; 53 proposed new ids (none collide). Analytics catalogue: 101 analytics in 17 families, 8 without a requirement.
- Changes: 239 in proposed_changes.json (184 safe, 55 owner); every anchor checked against the export.

## Ten most important findings
1. Identity text contradicts owner decisions: R-ID-06 allows "≤ 5 uncorrected ID switches per game" and gate G3 repeats it; OD-8 says zero locked swaps. R-VI-01b calls 29.97 fps "fully supported"; OD-9 needs ≥ 1080p and ≥ 59.94 fps for player-level numbers. OD-8, OD-9, OD-10 have no requirement rows.
2. Three of the four baseline-6 items have older twins: R-MD-22/R-MD-35, R-SY-12/R-SY-20, R-DQ-04 vs R-EN-19 (row lineage clash). Also duplicated: foul trouble (R-MD-16/R-SR-20), team fouls (R-MD-07/R-SR-03), crosswalk (R-FD-19/R-DS-05).
3. Court geometry text keeps old values (rim 1.60, restricted area 1.22 m, arc 6.75/6.60, half-court 12.73, pack line 5.3 m, short corner r 4.0–5.5) against the locked dictionary (1.6002, 1.2700, 6.7501/6.6008, 12.700, 5.1816). Three files hold court constants; config/court_ncaa_men.yaml still says verified: false.
4. Decisions of 19 Oct (D10, D11, D14, D18, D23, D24) were never folded: 8 rows still say the opposite (hoopR ESPN as model input, birth date, NIL as future input, pose fakes and contest form at Shall). Sections 19, 32 and 39 still list answered questions as open.
5. Movement decisions of 23–25 Oct (official-stat turnovers, OD-1..OD-5 attribution, atomic screen tags, abstention, floor-only ball) live only in the packs. R-MM-04 (Shall) needs ball height that production does not have.
6. Trace is weak: 20 references to old inbox ids; packs quote review-era proposals or the 17 Oct export by line; invariants.yaml names its invariants with 35 inbox ids (new-IV-xx); metrics.yaml cites R-MR-01, which does not exist; named_spots.yaml cites no id.
7. Packs cite ids for things the rows do not say: bigs.yaml uses R-ST-20 for screener-user distance (row: screener-defender); transition.yaml cites R-TR-21 for R-TR-22's margin and finds R-TR-08's defense-set rule unreachable; ball_actions.yaml credits tests to R-BL-06, R-EV-06, R-EV-07.
8. Baseline 4: measured team-foul display lag (p95 31 s, p99 41 s) breaks R-SB-03's 15 s cap; a "R-SB-03 tighten" row waits since 19 Oct; no rows for per-field latency, dropout rules or the live delay measurement allowed on 11 Nov.
9. Privacy flags: identity prose lists "hair" as a cue; "ESPN headshot" and a roster "headshot link" remain (D13 dropped them; identity_pack.yaml keeps headshot_ref); R-ID-16 uses protective equipment (health-adjacent) as a tie-breaker.
10. Same quantity, different targets: crossing time (R-TR-02, R-TR-20, R-PS-03), whistles (R-RF-01 vs R-MM-03), reaction timing (R-DF-08 ±80 ms vs K16 ±0.10 s), four labelling-queue rules, two "sprint" speeds, three shot-type lists. R-GU-01 lost its definition in the 18 Oct fold.

## Decisions only the owner can take (question, then my recommendation)
1. Apply the 184 safe changes as one batch? Yes.
2. Identity metric: "0 wrong locked labels plus a coverage target" instead of "≥ 95% correct"; which target? Report coverage now, set the target after gold-v1.
3. OD-9: current 29.97 fps replays feed team-level numbers only? Yes, as OD-9 says.
4. Drop headshots everywhere, including identity_pack.yaml headshot_ref? Yes.
5. Drop protective equipment as an identity cue (R-ID-16)? Yes.
6. One home for court constants: the rules-edition file filled from named_spots.yaml, court_ncaa_men.yaml retired? Yes.
7. Apply D10, D11, D14, D23, D24 to R-DS-02, R-DS-10, R-PC-01, R-EV-19, R-EV-24, R-PC-22? Yes.
8. One crossing-time tolerance (±0.3 s on 90%), R-TR-02 into R-TR-20, R-TR-15 into R-TR-04 at 90%? Yes.
9. Whistles: one row (R-RF-01) with recall 95%, precision 90%, onset 0.1 s? Yes.
10. Reaction timing ±0.10 s (K16) in R-DF-08 and defense.yaml? Yes.
11. R-MM-04 arc fitting to Should until 3-D ball passes R-CG-11? Yes.
12. One labelling queue: failed gold first, then disagreement × impact, 10% random audit? Yes.
13. Labels Claude makes for you count as gold only after you confirm them? Yes.
14. Scorebug: own cap for the team-foul display, and adopt the pending ±1 s tighten row? Yes to both.
15. Dictionary vs requirement: pick-up classes by y, box-out rule, three named side bands, R-DF-16 bands as event classes? Follow the dictionary in all four.
16. R-TR-08: add the pack's help-covered and 12 s ends? Yes.
17. One leverage (R-MD-33), one shot-type list (R-VI-03), PBP order by ORD-03 (R-SY-18)? Yes.
18. Restore R-GU-01's definition from the "Superseded texts (18 Oct)" tab? Yes.
19. Fold new-MR-01..06 from the stat catalogue tab as the R-MR family? Yes.
20. New scope: view access (R-PR-19) and access paths (R-RG-13) now; run book, retraining, retention at freeze exit; goal 9 (R-FP-01..06) as parked text? Yes.
21. Your own paid-site logins (decision 11) override "free first" in R-DS-03 for manual reads only? Yes.
22. Still open since 18–20 Oct: confirm face emotion is not adopted (yes); define "trapezoid of excellence"; H8 jersey colour descriptive only (yes).

## Not finished
- Overlap links are first-pass (28 corrected on review); duplicates, conflicts and stale items are fully quoted.
- Only the main tab was exported. The other tabs (Validation 20 Oct, Hypothesis candidates C1–C82, Stat catalogue, Improvement pass, Superseded texts) were not reviewed.
- identity_pack.yaml and config/live_state/*.yaml were being edited during this pass; the trace reflects them as read on 11 Nov.
- No web search: the analytics catalogue comes from domain knowledge. tools/similar.py finds about two thirds of known duplicate pairs; MAINTAIN.md adds a manual same-category read.
