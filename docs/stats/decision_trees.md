# decision_trees (TREE)

Status: proposed, 2026-10-19 (Aldemir: "20 deep tree analysis stats ... think in tree branches and states ... from a quant engineer perspective"). Registry: `config/metrics.yaml` category `decision_trees`. Generated from `M-TREE-*` entries.

## What a tree stat is

A tree stat follows one situation down a fixed set of branches (root condition → level 1 → level 2 … → leaf) and measures an outcome at every leaf: points per chance, make %, who scores, win probability. Example (M-TREE-001): catch on the left half of the court → first action is a drive → the drive ends back in the middle → points per chance.

## Rules every tree follows (the quant part)

- **Registered before looking.** The branches are fixed in the registry before any game is analysed (R-HY-01). Re-cutting branches after seeing results is how false patterns are made.
- **Shrinkage.** Every leaf is pulled toward its parent branch, the parent toward the team, the team toward the league: leaf = (successes + k × parent rate) / (n + k), k = 20 possessions by default (`tree_prior_strength_poss`). A leaf with 6 possessions cannot look like a 2.0 points-per-possession miracle.
- **Small leaves merge.** Fewer than 15 observations (`tree_min_leaf_n`) and the leaf joins its parent. Trees stop at depth 4 (`tree_max_depth`).
- **False-discovery control.** A tree with 40 leaves will show a few big differences by chance. A difference is called a finding only if Benjamini-Hochberg q ≤ 0.10 across all of that tree's leaves.
- **Out of sample.** A finding must keep its sign walk-forward on later games and on the held-out games (D19). Everything else is reported as description, not as a pattern.
- **Intervals, always.** Each leaf is shown with a 90% interval. Effect sizes come with their uncertainty.
- **As-of.** Pre-game uses only games before tip; in-game uses only branches already completed at that instant.

## The 20 trees

| ID | Tree | Branches | Leaf | Data | Now? |
| --- | --- | --- | --- | --- | --- |
| M-TREE-001 | Catch side → first action → outcome (court split by width) | catch in the frontcourt (touches) → catch half: left | right (y relative to the attacked basket, facing it) → first action: drive left | drive right | drive middle | pass | shot | hold → drive end half: same side | crossed to other half | chance points, make %, turnover % | tracking_broadcast | after_tracking |
| M-TREE-002 | Hand tree: catch hand → dribble hand → drive direction → finish hand | touch with at least one dribble → first dribble hand: left | right → drive direction: left | right | none → finish hand: left | right (layup_hand) or pull-up | make %, PPP, turnover % | tracking_broadcast | after_tracking |
| M-TREE-003 | Entry side × set family → who scores (scorer distribution per branch) | half-court possession → entry side: left | right | middle (first pass or dribble entry) → set family (top 5 MSU families, else other) → lineup (5-man key) when n allows, else none | share of points by player; usage share; PPP | tracking_broadcast | after_tracking |
| M-TREE-004 | Opponent height variance → mismatch → big-man advantage | possession against an opponent lineup → opponent height spread: SD of the 5 heights from profile_snapshots (metric_code height_cm; low | mid | high terciles) → switch on a ball or off-ball screen: yes | no → mismatch: height gap >= mismatch_height_gap_cm between attacker and his defender → who attacks: our big posts or rolls | guard isolates | not attacked | PPP, rim attempt rate, foul drawn rate | tracking_broadcast | after_tracking |
| M-TREE-005 | Leading-scorer cascade (home/away) | MSU game → site: home | away | neutral → leading scorer points vs his rolling median: below by >= cascade_drop_pts | normal | above → rest of team points vs expectation (pace and opponent adjusted) | others' points residual; team ORtg; win % | box | yes |
| M-TREE-006 | National television tree | game → broadcast: national (CBS, ESPN, ESPN2, FOX, FS1, TBS, TNT, truTV) | regional or streaming (BTN, Peacock, B1G+) → site: home | away | neutral → opponent tier (KenPom/Torvik quartile at tip) | margin minus expected margin; win % minus expected | box | yes |
| M-TREE-007 | Pattern adherence premium ('do what you always do') | player touch ending in a shot, drive or pass → sequence is in the player's top-3 by frequency: yes | no → defender pressure at catch: tight | loose | PPP, make %, turnover % | tracking_broadcast | after_tracking |
| M-TREE-008 | Transition × opponent size back | transition chance (K14 tempo label) → start: steal | defensive rebound | made basket | dead ball → numbers: advantage | even | disadvantage → opponent's tallest on-court player back in the paint by the first shot: yes | no | rim attempt rate, PPP, seconds to first shot | tracking_broadcast | after_tracking |
| M-TREE-009 | After-timeout tree | first possession after a timeout → caller: MSU | opponent | media → set family → first action: ball screen | off-ball screen | post entry | isolation | PPP minus matched dead-ball PPP | pbp | after_pbp |
| M-TREE-010 | Foul-trouble ripple | key player enters foul trouble (2 in the first 900 s, 3 with > 600 s left in half 2, 4 late) → action: sits within 60 s | stays → replacement type: same position | small-ball | big | net points per 100 over the next 300 s vs expectation; fouls drawn against | pbp | after_pbp |
| M-TREE-011 | Shot-clock decision map | catch in the frontcourt → shot clock: 21-30 | 14-21 | 7-14 | 0-7 s → catch half: left | right → closest defender: < 1.2 m | 1.2-1.83 m | > 1.83 m (K22 bins) → decision: shoot | drive | pass | hold | chance value after the decision | tracking_broadcast | after_tracking |
| M-TREE-012 | Ball-screen side × coverage → read → outcome | ball screen → location: left wing | right wing | middle | side → coverage (4 coarse classes, K04) → handler read: use | reject | split | snake → finisher: handler | roller | popper | kick-out shooter | PPP | tracking_broadcast | after_tracking |
| M-TREE-013 | Run response tree | opponent run detected → response: MSU timeout | substitution | none → next 3 possessions: run continues | stops | net points over the next 3 possessions each way | pbp | after_pbp |
| M-TREE-014 | Scheme switch response | opponent scheme change (scheme_changes) → change: man→zone | zone→man | to press → MSU first 5 possessions: set family used | PPP vs the same possessions' expectation | tracking_broadcast | after_tracking |
| M-TREE-015 | Offensive rebound: putback vs kick-out | offensive rebound → location: rim area | short | long (r rings) → action: putback | kick-out | reset | second-chance PPP | tracking_broadcast | after_tracking |
| M-TREE-016 | Score-state behaviour tree | possession → margin (MSU view): <= -10 | -9..-4 | -3..3 | 4..9 | >= 10 → time: > 10 min | 4-10 | < 4 min left in the half | seconds to first shot, 3PA rate, PPP | pbp | after_pbp |
| M-TREE-017 | Fatigue tree | player stint → continuous minutes: < 4 | 4-8 | > 8 (H13) → top speed vs his game baseline: normal | down >= 5% | make %, defensive reaction delay, PPP on his touches | tracking_broadcast | after_tracking |
| M-TREE-018 | Free-throw trip aftermath | MSU free-throw trip ends → result: all made | some missed | all missed → next opponent possession start: after make | live rebound | opponent PPP next possession | pbp | after_pbp |
| M-TREE-019 | Monte Carlo lineup duel (best five vs each opponent five) | MSU lineup L vs opponent lineup O → possession start type (from the opponent's tendencies) → who uses the possession (usage tree) → action and shot (player tendency trees) → make, foul, turnover, rebound (player rates, shrunk) | simulated net points per 100 | pbp | conditional |
| M-TREE-020 | Game-script simulator and what-if tree | pre-game or current state → condition (what-if): scorer held under X | big fouls out | pace +5 | 3P% at 25th percentile → simulated game paths | P(win), margin distribution, player point distributions | pbp | conditional |

## Simulators (M-TREE-019, M-TREE-020)

- **Lineup duel (M-TREE-019).** For every MSU five and each likely opponent five, simulate 20,000 possessions each way. Each simulated possession walks the player trees: who uses it, which action and shot, then make, foul, turnover or rebound from shrunk player rates. Output: net points per 100 with an interval; best five against each opponent five = the highest lower bound. Lineups that never played together are simulated from player rates and flagged.
- **Game-script what-ifs (M-TREE-020).** Run the game forward 10,000 times from the possession engine with the player trees. Then ask conditional questions by keeping only the paths where the condition holds (importance resampling): leading scorer held under X, their big fouls out early, a slower pace, a cold 3-point night. Output: change in win probability and each player's point distribution. Reported only once the simulator is calibrated (R-PR).

## Data each tree needs

- Box score now: M-TREE-005 (leading-scorer cascade), M-TREE-006 (national TV).
- Play-by-play (state fold built and tested): M-TREE-009, 010, 013, 016, 018.
- Broadcast tracking: M-TREE-001 to 004, 007, 008, 011, 012, 014, 015, 017. Hand-level branches (M-TREE-002) need pose and stay Should until pose error is measured (D23).
- Simulators: M-TREE-019, 020 need the player trees and a calibrated possession engine.
