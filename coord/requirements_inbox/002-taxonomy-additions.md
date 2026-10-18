# Requirements inbox 002 · Taxonomy additions (offense, defense, motion starts) of 2026-10-18

From: Job A of `coord/prompts/002-claude-code-taxonomy-and-markets.md` (deep research, ten research notes). To: requirements session. Status: research output, not yet agreed with Aldemir. Written 2026-10-18.
Source documents (full evidence, every URL, every [HEURISTIC] tag):
- `docs/taxonomy/offense_full.md`, section **"Additions 2026-10-18 (Job A deep research)"** (A0–A12, from line 1016).
- `docs/taxonomy/defense_full.md`, section **"Additions 2026-10-18 (Job A deep research)"** (A0–A12, "Additional sources", "Corrections 2026-10-18", from line 974).
- `docs/taxonomy/motion_starts.md` (new file, 149 blocks, §0–§22 and Sources).

Action: decide which detection requirements below enter `docs/requirements.md` ("Actions and playbook recognition" and "Defensive structure"), which vocabulary proposals go to `config/vocabulary_map.yaml`, and answer the open questions. Nothing here edits those files. Transition items are in inbox 004 (`coord/requirements_inbox/004-transition.md`) and are cross-referenced, not repeated.

Units: m, s, °, m/s, cm (heights). Court positions are (r m, θ°): r from the rim centre, θ from the right baseline at the rim centre, per `config/vocabulary_map.yaml`; left side θ_L = 180° − θ_R. Every threshold and timing window below is **[HEURISTIC]** (a proposal to fit on film) unless a source key is named in the taxonomy file; **no opened source gave any set timing in seconds**.

Sourcing note for this file: it summarises the three repo files above. No web page was opened while writing it, so it adds no new external claims. Every source key quoted (`[M#]`, `[N#]`, `[DZ#]`, `[MA#]`, …) resolves in the Sources section of the file named next to it.

---

## 1. Counts of new items per family

### 1a. By file and family (counts as stated in each file's own count section)

"Items" counts blocks plus separately named table rows, as each file defines them. "NEW / RICHER" for offense is my tally of the block headings (the file's A10 table gives totals only). Tallies of headings and the file's "Blocks" column differ by 1–3 in A1, A2 and A6 because A1.14, A2.40, A2.43 and A6.37 are confirmation, compact-table or data blocks.

| File | Section | Family | Blocks | Items | NEW / RICHER (blocks) | MSU-attributed |
|---|---|---|---|---|---|---|
| offense_full | A1 | F18 MSU sets 2024-26 + 11 pre-window FastModel sets (P1–P11) | 13 | 24 (22 distinct) | 9 / 5 | all |
| offense_full | A2 | Big Ten other teams (F1, F2, F4–F8, F10, F12–F14, F17) | 40 | 54 | 31 / 10 | 0 (one cross-ref) |
| offense_full | A3 | F5 Ball-screen offense | 30 | 43 | 23 / 8 | A3.12, A3.21, A3.27, A3.28 |
| offense_full | A4 | F6 Handoff offense | 6 | 6 | 5 / 1 | A4.1, A4.2 |
| offense_full | A5 | F8 Off-ball screens and cuts | 24 | 35 | 14 / 11 | A5.7, A5.11, A5.12 and MSU usage rows in A5.15–A5.24 |
| offense_full | A6 | F13 Special situations (rules layer, BLOB, SLOB, ATO, end of clock) | 30 | 41 (40 distinct) | 29 / 2 | A6.2–A6.6, A6.14–A6.19, A6.22, A6.28, A6.30 |
| offense_full | A7 | F11 Zone offense | 21 | 36 | 19 / 3 | A7.1–A7.7 |
| offense_full | A8 | F12 Press offense / press break | 6 | 19 | 6 / 1 | A8.1 |
| **offense_full** | | **Total** | **170** | **258 (255 distinct)** | | |
| defense_full | A1 | Man principles (F1, F7) | 5 | 5 | 2 / 3 | M-1, M-5 |
| defense_full | A2 | Ball-screen coverages (F3) | 15 | 15 | 7 / 8 | BS-5, BS-7 |
| defense_full | A3 | Handoff coverages (F4) | 1 | 1 | 0 / 1 | H-1 |
| defense_full | A4 | Off-ball screen coverages (F5) | 3 | 3 | 1 / 2 | — |
| defense_full | A5 | Zones and match-up rules (F8) | 10 | 10 | 4 / 6 | Z-5, Z-8 (opponents vs MSU), Z-10 |
| defense_full | A6 | Presses (F9) | 8 | 8 | 2 / 6 | P-5 |
| defense_full | A7 | Junk / combination (F10) | 3 | 3 | 0 / 3 | — |
| defense_full | A8 | Scheme changes (F11) | 7 | 7 | 6 / 1 | SC-1, SC-5, SC-6, SC-7 |
| defense_full | A9 | Transition defence (F12) | 7 | 7 | 3 / 4 | — |
| defense_full | A10 | MSU / Izzo defence (F1.6, F18.4) | 5 | 5 | 0 / 5 | MSU-1 to MSU-5 |
| defense_full | A11 | Detection literature (F18) | 1 | 1 | 0 / 1 | — |
| **defense_full** | | **Total** | **65** | **65** (+ 13 new primitives in A0, + 4 status notes) | **25 / 40** | **18** |
| motion_starts | §1 | Horns (F3.2) | 31 | 31 | 28 / 3 | 11 |
| motion_starts | §2 | 1-4 High incl. 4-High / Iverson (F3.1) | 18 | 22 | 18 / 0 | 7 |
| motion_starts | §3 | 1-4 Low (F3.1) | 6 | 6 | 0 / 6 | 0 |
| motion_starts | §4 | 4-out 1-in (F3.1 / F4.2) | 12 | 15 | 11 / 1 | 0 |
| motion_starts | §5 | 5-out (F3.1 / F4.2) | 14 | 14 | 10 / 4 | 0 |
| motion_starts | §6 | Box (F3.3) | 3 | 3 | 3 / 0 | 0 |
| motion_starts | §7 | Stack / Floppy / Zipper (F3.3 / F3.1) | 4 | 4 | 3 / 1 | 3 |
| motion_starts | §8 | Diamond | 0 | 0 | — | 0 |
| motion_starts | §9 | Two-guard front (Princeton and others) | 12 | 15 | 8 / 4 | 1 |
| motion_starts | §10 | Triangle (F4.1) | 7 | 7 | 6 / 1 | 0 |
| motion_starts | §11 | 3-out 2-in | 4 | 4 | 4 / 0 | 0 |
| motion_starts | §12 | Post-entry starts | 3 | 3 | 1 / 2 | 0 |
| motion_starts | §13 | 2-1-2 / 1-3-1 | 1 | 1 | 1 / 0 | 0 |
| motion_starts | §14 | Elbow / high-post entries | 3 | 3 | 3 / 0 | 2 |
| motion_starts | §15 | Secondary / early-offense entries | 7 | 7 | 6 / 1 | 1 |
| motion_starts | §16 | Wing dribble-entry starts | 2 | 2 | 1 / 1 | 0 |
| motion_starts | §17 | 1-2-2 / Line | 0 | 0 | — | 0 |
| motion_starts | §18 | Alignment not documented | 22 | 22 | 20 / 2 | 12 |
| **motion_starts** | | **Total** | **149** | **159** | **123 / 26** | **37** |
| **All three files** | | | **384 blocks** | **482 items** (13 MSU sets are in both offense_full and motion_starts; one canonical entry each, offense A11.15) | | |

### 1b. Raw item counts as reported by the ten research notes (before merging and de-duplication)

| Research note | Items reported | Landed in |
|---|---|---|
| Motion starts A (FastModel, Coach's Clipboard, Breakthrough, …) | 64 blocks (37 MSU A1–A37, 27 other B1–B27; > 100 named entries counting table rows) | motion_starts (`[MA#]`) |
| Motion starts B (Hooper, Hoops Geek, FIBA, Coaching Toolbox, …) | 39 | motion_starts (`[MB#]`) |
| MSU sets 2024-26 | 13 (+ 11 pre-window sets P1–P11) | offense A1 |
| Big Ten other teams | 44 | offense A2 |
| Ball-screen offense | 40 | offense A3, A4 |
| Off-ball screens and cuts | 35 | offense A5 |
| Special situations | 59 | offense A6 |
| Zone offense / press offense | 59 | offense A7, A8 |
| Man / ball-screen / handoff / off-ball defence | 26 | defense A1–A4, A10 |
| Zones / presses / junk / scheme changes / transition defence | 38 | defense A5–A9 |
| **Total** | **417** | |

---

## 2. Items that need new detection requirements (one line each, with the measurable signal)

`docs/requirements.md` already asks for: pick-and-roll, pick-and-pop, slip, re-screen, ghost screen, DHO, keep fake; down, flare, back, cross, stagger, pin-down, elevator and hammer screens; backdoor, basket, Iverson, curl, flare, shallow, UCLA and zipper cuts; post-up, seal, short roll, dive, lift, drift, dunker spot; a coverage label per action; a man/zone/press scheme label every second. The lines below are **not** covered by that list, or they need a measurement the list does not name. Section 2k lists existing requirements that now have sharper signals.

### 2a. Data prerequisites that several items depend on

- **Ball height (z):** the canonical `LOB` needs ball apex ≥ 3.5 m (offense A11.18); `LOB_high_catch` needs hands ≥ 3.0 m at the catch. Without z, use the proxy: catch at r < 1.5 by a receiver moving rimward at ≥ 3 m/s.
- **Roster heights (cm) and positions:** switch-hunt (A2.8: new defender ≥ 8 cm shorter), cross-match (T-5: |Δheight| ≥ 10 cm), scram switch (BS-14), rim protector = tallest (T-5), Corner Step-Up screener ≤ 1.96 m (A3.6).
- **Inbounder tracking out of bounds:** BLOB inbounder at (3.33, −34.7°), SLOB at the 8.53 m mark (10.5, 41°), and the thrower's feet within ±0.46 m of the spot centre from t_dispose to t_release (A6.1 R2).
- **t_dispose and t_touch events:** t_dispose = ball at the thrower's disposal; t_touch = first legal in-bounds touch, when both clocks start (A6.1 R1, R4; A11.19).
- **Game and shot clock (OCR) to 0.1 s:** `late_clock` (shot clock ≤ 5 s), `late_clock_inbound` (≤ 10 s at t_dispose, A6.30), shot-clock-off (A6.1 R6), the 10 s backcourt count (R7), the ≥ 0.3 s run-off audit in the last 59.9 s (R4).
- **PBP join:** timeouts, runs and made baskets drive SC-1, SC-3, P-3, P-4, J-1 and `PRESS_SETUP` / `INBOUND_LAG`.
- **Pose (optional):** true backpedalling in the transition "wall" (T-4) and the defender's facing in the post seal; flagged pose-dependent.
- **Lineup data:** 2-3 anchor dependency (Z-10: rim attempts when the centre-slot defender is off the floor).

### 2b. Offense primitives (offense A0 and A11.18, motion_starts §0.3)

- `SCREEN_strict` vs `SCREEN_loose`: strict = screener ≤ 0.3 m/s for ≥ 0.5 s within 1.2 m of the user's path; loose = < 0.6 m/s for ≥ 0.3 s. Store which one fired (A11.2).
- `SCR` deflection test (motion_starts): the user's defender changes heading by > 30° or slows by > 40% within 1.5 m of the screener.
- `POP_MID`: screener moves outward ≥ 1.5 m and stops at r 4.0–6.6 m without rolling, within 2.0 s (A11.18). `POP_ARC` = reaches r ≥ 6.6 m within 2.0 s.
- `SHORT_ROLL_strict`: screener decelerates to < 1.5 m/s at r 3.0–6.0 m, |θ − 90°| ≤ 35°, within 1.2 s of t₀.
- `GHOST`: screener approaches to ≤ 1.5 m, is never stationary, then exits to r ≥ 6.6 m.
- `DHO_strict`: hand-to-hand distance ≤ 0.6 m and air time ≤ 0.2 s (restarts), next to the canonical ≤ 1.0 m / ≤ 0.3 s.
- `FAKE_DHO`: a–b distance ≤ 1.5 m with the holder dribbling toward b, no transfer, and b moves away ≥ 3 m within 1.5 s (motion_starts).
- `DRIBBLE_AT`: handler dribbles ≥ 2.5 m on a heading within 25° of a teammate and ends ≤ 3.5 m from him.
- `ELEVATOR` (canonical): pre-gap 0.9–1.6 m closes to < 0.6 m within 0.5 s of the cutter passing; `elevator_wide`: 1.6–3.0 m closing to < 1.0 m within 0.6 s.
- `STAGGER` timing: screeners 2–5 m apart along the path, second contact ≤ 1.5 s after the first.
- `DOUBLE`: two stationary screeners ≤ 1.2 m apart, user passes both within 1.2 m.
- `weave` (canonical, A4.6): ≥ 2 consecutive DHOs within 5.0 s, all at r 6.5–9.0 m, θ 45–135°, alternating participants; flags `weave_3dho_return` and `weave_then_high_screen` (ball screen ≤ 2.0 s after the last DHO).
- `double_high` (A11.17): two bigs at r 4.5–8.0 m, θ 60–120°, ≤ 3.5 m apart; two ball screens on one handler 0.8–3.0 s apart; sub-labels `trade` (first screener reaches r ≥ 6.75 m within 2.0 s) and `sink` (first screener reaches r < 2.5 m).
- `77` geometry sub-labels: `77_drag` (sequential, ≥ 0.5 s apart), `77_stagger` (1.5–4 m apart along the path), `77_wall` (≤ 1.2 m apart at the same level).
- `ALIGN` snapshot rule: five-player snapshot when the handler first slows below 2 m/s with y_ball < 9 m (or at the first pass after crossing half-court); accept if mean error < 1.8 m **and** the best template beats the runner-up by > 0.4 m.
- Speed bands for cuts: walk < 1.94, jog 1.94–3.9, run 3.9–5.0, high speed 5.0–6.0, sprint ≥ 6.0 m/s; "hard cut" = ≥ 3.9 m/s for ≥ 0.4 s (A5; conflicts with load_thresholds, see §4).
- Timing reference per set family: t0 = first action (half-court), t₀ = screen contact (minimum handler–screener distance; negative windows allowed), t_touch (restarts), possession-change frame (live-ball transition) (A11.19).

### 2c. Alignments and motion starts (motion_starts)

- Alignment templates for `ALIGN` beyond the examples already in requirements (Horns, 1-4 high, Box, Stack, 4-high, Chest, 5-out): 3-out 2-in, two-guard front (Princeton), Triangle (sideline triangle), 2-1-2 / 1-3-1, post-entry start, wing dribble-entry, elbow entry, 4-out 1-in, 1-4 Low; plus per-family template starts for 5-out early entries and Stack/Floppy. Discriminator example: two-guard front = two players at the slots and nobody at θ 80–100° beyond the arc.
- New cut path classes: flex (weak corner → ball-side block along y < 1.5 m), chin (slot/wing → rim past an elbow back-screener after a reversal), loop (corner → wing/top behind the handler), shuffle (diagonal weak wing → ball-side block past a high screener).
- Alignment-family label per possession, so a set can be "Horns + unknown continuation" when the start matches but the sequence does not.
- Horns-family discriminators: 4 and 5 at the elbows (4.57, 66.4° / 113.6°) or at ARC-HIGH (7.13, 75.4° / 104.6°); store which (affects pop vs roll reading).
- Mirror normalisation: θ → 180° − θ before sequence matching (already in requirements; motion_starts adds the per-section template starts).

### 2d. Ball-screen and handoff actions (offense A3, A4)

- Roll-and-replace (A3.1): ball screen at |θ − 90°| ≤ 30°, ROLL, a player from r < 4.5 m moves out, crossing the roller's path within 2.0 s with closest approach ≥ 1.5 m; at t₀ + 2.0 s exactly 1 attacker at r < 3 m and ≥ 3 at r ≥ 6.6 m.
- On-ball flare (A3.5): aborted roll (inward ≥ 1.0 m), low big screens the screener's defender, screener exits at > 120° from the ball to r ≥ 6.6 m, θ 25–55°.
- Corner step-up (A3.6): screener starts at θ ≤ 12°, r ≥ 6.6 m, travels along the arc (|Δr| ≤ 1.0 m) at ≥ 3 m/s and screens from the baseline side.
- Pop destination classes (A3.8): end (r, θ) of `POP_ARC ∪ POP_MID` relative to the screen spot; "mid-range pop" if end r < 6.6 m and the catch-and-shoot is at r 4–6 m.
- Short-roll 4-on-3 (A3.10): two defenders within 2.0 m of the handler at t₀ + 0.3–1.0 s; screener catches at r 3.0–5.5 m within 1.5 s of trap onset; label 4-on-3 by count at the catch.
- "Shorting" the second big (A3.11): non-screening big at the dunker spot (2.0 ≤ |x| ≤ 3.5, y ≤ 0.6) for ≥ 0.5 s before t₀.
- Slip-to-arc (A3.14): SLIP with dr/dt > 0, end r ≥ 6.6 m within 1.5 s; SCREEN dwell never met.
- Ghost → back screen → middle ball screen (A3.15): GHOST, defender swap ≤ 1.0 s, back screen ≤ 2.5 s, ball screen at |θ − 90°| ≤ 20° ≤ 2.5 s later.
- Double ghost (A3.16): two GHOSTs on one handler within 1.0 s, then a drive within 1.5 s.
- Blue/Red drag (A3.17): trailer within 2.0 m of the handler with no SCREEN in the first 10 s, pass to the wing, trailer screens the passer's defender within 1.0 s, return pass within 2.5 s.
- Stack roll (A3.23): teammate 0.8–2.0 m rim-side of the screener for ≥ 0.5 s before t₀; roll passes within 1.2 m of him; he pops to r ≥ 6.6 m.
- 77 Wall / Pop-and-Flare / Horns 77 (A3.24): wall = screeners ≤ 1.2 m apart, joining line within ±25° of perpendicular to the handler's velocity.
- Ball screen + weak-side occupier action (A3.29): empty-side tag plus a ≥ 2-screener sequence on the opposite sign(x) within ±1.5 s of t₀.
- Empty-side tag: no teammate with the same sign(x) and |x| > 3 m other than the screener (A3.29, A4.4).
- Switch-hunt ball screen into a post-up (A2.8): defender labels swap within 1.0 s, screener's new defender ≥ 8 cm shorter, screener sets up at r 1.5–4.0 m with speed toward the rim < 0.5 m/s and gets an entry within 2.5 s.
- DHO → ball screen → veer (A4.3): DHO, ball screen by a third player within 1.5 s, his down screen within 2.0 s.
- Zoom reject (A4.4): zoom approach without transfer, receiver reverses toward r < 2 m within 0.8 s, then an empty-side ball screen within 4 s.
- DHO used as a ball screen with roll + baseline cutter (A1.7): giver (a 5) reaches r < 2.5 m within 2.0 s; weak-side corner player moves along y < 1.0 m toward the rim; lob caught at r < 1.5 m.
- Dunker-spot big opposite the PnR (A1.10): during any ball screen, a player at 2.0 ≤ |x| ≤ 3.5, y ≤ 0.6 m, opposite sign(x) to the ball for ≥ 60% of the 3 s window.
- Split-court dual-PG offence (A1.11): two handlers each on opposite sides for ≥ 70% of the possession; handler-to-handler reversal within 2 s of a stopped drive.

### 2e. Off-ball screens and cuts (offense A5)

- Pin-in screen (A5.1): screener moves out (Δr > +1.5 m) from r < 4.5 m and stops at r 4.0–6.5 m between the target defender and a shooter who moves ≤ 1.5 m at r ≥ 6.6 m.
- Out screen (A5.2): stationary screener at r 3.8–5.2 m, θ 55–125°; cutter's r increases ≥ 2.5 m to r ≥ 6.6 m with θ change ≤ 35° (same-side exit).
- Middle screen (A5.3): residual class; cutter moves toward the ball (angle < 60°) and ends with |x| reduced ≥ 1.5 m; used so the classifier does not force a wrong class.
- Turnout (A5.4): cutter at r < 2.5 m with speed < 2 m/s accelerates to ≥ 3.9 m/s with Δr ≥ +4.0 m in ≤ 1.5 s past a stationary screener at r 1.8–3.5 m.
- Loop cut (A5.5): heading rotates ≥ 180° within 2.5 s while staying 1.0–2.5 m from a stationary teammate; exits loop-out or loop-under (r < 1.5 m).
- X-cut / cross pin-downs (A5.6): two guards from r ≥ 6.5 m cut within 1.0 s of each other, paths cross inside r < 4.5 m, both exit to the opposite side (sign(x) flips).
- Circle cut (A5.7, MSU 14-Circle): wing cutter passes above both elbows (min y ≥ 4.6 m), turns down 90–150° around an elbow screener, reaches r < 2.0 m within 2.0 s.
- Laker cut (A5.8): post entry, passer cuts within 1.2 m of the post to r < 2.0 m; high side vs low side by which side of the post he passes.
- Rub cut / rub screen (A5.9): cutter passes within 0.8 m of a stationary post at ≥ 3.9 m/s; or a moving teammate (≥ 2.5 m/s) brushes the handler's defender without ever meeting the screen dwell.
- Pinch fade (A5.10): a big pinches ≥ 1.0 m toward x = 0 and stops at r 3.5–5.5 m; the nail player fades (Δr ≥ +2.5 m) past him.
- Ghost flare (A5.13): approach to ≤ 1.5 m without dwell, exit to r ≥ 6.75 m, flare screen from a third player within 1.5 s.
- Shake / lift and blade (A5.19): corner player moves along r 6.6–8.0 m by Δθ ≥ +20° toward the slot within 1.5 s of a same-side ball screen; blade = he reaches r < 2.0 m during the roll.
- "Inverted stagger" (A2.20; meaning unverified): stagger whose user moves −y, or whose first screener cuts for a lob. Keep as a provisional label only.
- "Wheel" (A5.14): **not implementable until defined** (no opened source defines it).

### 2f. Team- and system-level offense measures (offense A2)

- Patternless ball-screen offence (A2.24): ≥ 60% of half-court possessions with a ball screen for the same handler; screener-orientation entropy ≥ 2.5 bits (8 bins of 45°) over ≥ 20 screens; median time to FGA ≥ 18 s.
- Free-flow "no sets" offence (A2.25): ≥ 30% of possessions with first FGA ≤ 10 s, and template-match rate < 20%. The template-match rate is a new per-team metric.
- Jet early offense (A2.11): in the 4–10 s window, two players within 1.2 m at r < 2.5 m accelerate together (≥ 3 m/s, headings within 30°) to r 4–5.5 m, θ 60–120°, within 1.5 s.
- MSU primary break roles (A1.13): ≥ 3 MSU players at ≥ 5 m/s within 2 s of the change of possession; ball over y = 12.73 m by ≤ 4 s; first big to r < 2.0 m within 6 s. Every external transition definition is stored as its own field (inbox 004).

### 2g. Special situations (offense A6)

- Rules layer (A6.1 R1–R11) as derived labels: `burned_inbound` (no receiver separation ≥ 1.5 m by t_dispose + 4.0 s); `made_basket_inbound` via the thrower's x moving > 1.0 m (R3); `clock_audit` (touch + whistle in the last 60 s with < 0.3 s run-off, R4); `tap_only` window (game clock ≤ 0.3 s, R5); `shot_clock_off` (R6); `10s_violation` (R7; 2026-27 call at the shot-clock reading of 19, `[Q2]`); `spot_point_of_out` vs `spot_8p53m` (SLOB with |y − 6.93| > 1.5 m, R10).
- Time-remaining menu (A6.27): bucket end-of-game inbounds by game clock (≤ 0.3, 0.4–1.0, 1–3, 3–5, > 5–6 s) and compare the observed action with the bucket.
- Corner lob BLOB / Circle Lob (A6.8): no in-bounds catch before the lob; ball to r ≤ 1.5 m with apex ≥ 3.6 m at t_dispose + 1.5–4.0 s, receiver ran ≥ 4 m rimward after passing a fake screener.
- New inbound alignments: 4 High (four in-bounds players at or above the FT line extended, A6.9), 4-Low (all four at y ≤ 1.5 m with x spread ≥ 9 m, A11.21), Triangle (three attackers with sides 2.5–5 m inside r ≤ 6 m plus a safety at r ≥ 7 m, A6.12, geometry unverified), Sideline Stack (A6.21), stack rule (consecutive-neighbour gap ≤ 1.5 m along a fitted line; diagonal if 25–65° to the baseline).
- Protect-the-lead SLOB split (A6.22): game clock ≤ 10 s, lead 1–3; two receivers within 2 m diverge at ≥ 5 m/s relative velocity within 1.0 s; pass ≥ 10 m to the overplayed receiver.
- Full-court ATO templates: Nova (A6.23: thrower trails the ball for ≥ 2 s, ≥ 13 m dribble in ≤ 3.5 s, backward pitch to r 6.75–8.0 m), Indiana (A6.24), home-run pass (A6.25), Maryland and Split (A6.26: mean ≥ 4.5 m/s).
- `late_clock_inbound` (A6.30) and late-clock shot-type priors (A6.29).

### 2h. Zone offense and press offense (offense A7, A8)

- Zone-screen and gap events: `ZONE_SCREEN` (pin on a zone defender), `GAP_DRIVE` ending at r 3–5 m with a kick ≤ 1.0 s later, saddle dribble (heading within 0.5 m of one defender's shoulder, A7.16), post cross inside the lane within 2 s.
- Hot-potato zone offence (A7.8): mean perimeter holding time ≤ 1.2 s, ≤ 1 dribble per touch, weak-block player reaches the ball-side elbow within 1.2 s of each wing catch (compliance rate).
- Gap Attack (A7.14): dribble entry with a shallow cut ≥ 3 m, two back-side zone pins within 0.8 s, flare ≥ 2 m, skip.
- Zone DDM (A7.15): high post (r 3.5–5 m, θ 70–110°) empty for ≥ 70% of set time; pitch-back player 3–5 m behind the driver.
- Half-court trap breakers (A8.5): tight end at |x| < 2 m, y 11–16 m; "draw two, then pass" timing (release ≤ 0.6 s after the second defender comes within 2.5 m: early / on time / late); deep holder at r < 3 m.
- Press-break spacing (A8.7): receiver spacing flag < 3.5 m (crowded) or 4.57 ± 1.5 m (on spec); cross-basket pass within 2 m of the own rim; reversal count before half-court (> 2 flagged); crossing mode (pass vs dribble).

### 2i. Defense primitives and coverages (defense A0–A4)

- `SHAPE_MATCH` d̄_m: Hungarian defender-to-attacker mean distance; ≤ 2.0 m man/match-up, ≥ 2.5 m pure zone on overloads.
- `ONE_ON_BALL`: exactly one defender within 1.5 m of the handler on ≥ 80% of non-trap frames.
- `CHASER(d,a)`: follow score F ≥ 0.8 and within 2.0 m of the attacker on ≥ 85% of frames even two passes away.
- `SLOT_RESIDUAL_k`: mean distance of the 5 defenders to the ball-conditioned template of zone family k.
- `FAKE_TRAP`: second defender within 2.0 m without meeting `TRAP`, then a retreat ≥ 1.0 m within 1.0 s.
- `RECOVER`: travel ≥ 1.5 m toward the attacker, ending within 2.0 m; hard closeout ends ≤ 0.8 m, short ends 1.2–2.0 m.
- `STEP_RELEASE` (Izzo one-step help, M-1/M-5): ≥ 0.5 m toward the handler within 0.4 s of a middle dribble, reversal ≥ 0.4 m within 0.5 s of the pickup, no matchup change.
- `JAILBREAK`: handler reaches r ≤ 3.0 m with no defender within 1.5 m ≤ 1.5 s after t₀ of a ball screen.
- `SPLIT`: handler passes between X-ball and X-big while they are ≥ 1.2 m apart.
- Screen moment t₀ = minimum screener-to-on-ball-defender distance (`[N32]`), shared by all coverage labels.
- Jump to the ball (M-5): passer's defender moves ≥ 0.5 m during the pass flight and ≥ 1.0 m by t_catch + 0.4 s toward the receiver's side.
- Two-level coverage labels (BS-1): four coarse classes at level 1, fine F3 coverages at level 2; over/under test at t₀ ± 0.2 s (projection parameter 0 < t < 1, perpendicular distance ≤ 0.8 m → over).
- Point-of-attack "quickest path" (BS-2, team label): over/under predicted from the defender's position at t₀ − 0.3 s with accuracy ≥ 0.8, over share 0.3–0.7, over ≥ 20 screens.
- Up to touch arrival lag (BS-4): Δt_arr ≤ +0.2 s; late (split risk) > 0.5 s.
- Soft show no-rotation check (BS-5): no off-ball rotate and no tag in [t₀, t₀ + 2 s].
- Late switch (BS-6): switch that starts after t₀ + 1.0 s, handler at r ≤ 3.5 m.
- Hard hedge additions (BS-7): pre-contact gap ≤ 0.5 m at t₀ − 0.2 s (> 1.0 m = split risk); handler retreat ≥ 1.0 m for ≥ 0.4 s.
- Hedge-and-plug (BS-8): X-ball ≥ 2.0 m off the handler by t₀ + 0.8 s while within 1.5 m of the roller's path, then a `RECOVER` ≥ 2.0 m within 2.0 s; no switch.
- Drop depth bands (BS-9, C-3): high/level 0.6–1.83 m, standard 1.83–3.05 m (sourced `[N3]`), deep > 3.05 m or X-big at r ≤ 4.5 m, measured at t₀ + 0.3 s.
- Drop "load" (BS-10): a strong-side defender enters a 1.5 m wide handler-to-rim corridor between t₀ and t₀ + 1.2 s, comes within 2.0 m, returns ≥ 1.0 m within 1.5 s.
- Ice-and-switch (BS-11): ice before t₀, then a switch starting in [t₀ + 0.4, t₀ + 1.8 s] lasting ≥ 2 s.
- Switch-and-attack (BS-12): new ball defender closes from ≥ 1.5 m to ≤ 0.8 m within 0.5 s at ≥ 3 m/s; passive = ≥ 1.2 m held ≥ 1 s.
- Switch & Shrink (BS-13): switch with shot clock ≤ 10 s plus a front on the roller (≤ 0.6 m), ≥ 2 defenders within 1.5 m of the blocks, trap only below 5 s.
- Scram switch (BS-14): switch triggered by a pass in flight on a size mismatch, completes ≤ 0.5 s after the catch.
- Peel switch sub-labels (BS-15): reciprocal swap within 0.8 s / 1.5 s; corner, post and nail peel by the peeler's pre-drive spot.
- Position-conditional DHO switching (H-1): switch rate by giver role (guard vs big).
- Point switching (OB-1): off-ball switch completes ≥ 0.3 s before the cutter's closest approach to the screener.
- Back-screen jump-out (OB-2): screener's defender moves ≥ 0.6 m into the cutter's path in [t₀ − 0.5, t₀], switch by t₀ + 0.5 s; error flags (chase-under, show-and-recover without swap).
- Switch-equals policy (OB-3): off-ball switch probability ≥ 0.6 for equal positions, ≤ 0.1 for mismatches; step-under = cutter's defender y drops ≥ 0.4 m in [t₀ − 0.8, t₀ − 0.1].
- Izzo high-post flash denial (MSU-1): defender ball-side (≤ 0.6 m from the ball–cutter segment) within 0.5 s of a flash toward |x| < 2.5 m, 3.5 < y < 6.5 m.

### 2j. Zones, presses, junk, scheme changes, transition defence (defense A5–A10)

- 3-2 vs 1-2-2 split (Z-1, C-4): top defender ≥ 1.5 m higher than the wings = 1-2-2; within 1.0 m = 3-2; 1.0–1.5 m = report both posteriors.
- 2-1-2 (Z-3): one defender at r 3.5–4.6 m, |x| < 1.0 m; no swarm on high-post catches (tops close < 1.0 m in 1.0 s); Buzz = first contact at r ≥ 9.0 m.
- Point zone (Z-4): zone-like F ≤ 0.35 for 4 defenders, one defender within 1.2 m of the ball on every catch, identity changing on ≥ 70% of passes.
- 2-3 match-up (Z-5): d̄_m ≤ 2.0 m and pass-off on ≥ 60% of lane cuts ≥ 6 m; tallest defender at r < 3.0 m on ≥ 80% of frames.
- 1-3-1 match-up (Z-6): one defender F ≥ 0.8 on the opponent centre everywhere, the other four F ≤ 0.45; switch on ≥ 80% of perimeter ball screens.
- Match-up pick-up mirror test (Z-7): defensive front count equals offensive front count at `SET_DEF` + 1.5 s on ≥ 85% of possessions.
- 1-3-1 pick-up depth (Z-8): top's first contact at y ≥ 11.0 m within 2.0 s of the ball crossing half-court.
- Amoeba high-post triple (Z-9): three defenders within 2.0 m of a high-post catcher within 1.0 s.
- Purdue 1-2-2 man-zone hybrid (Z-2): ≥ 3 s window with two defenders within 3.5 m in front of the star, neither within 1.0 m, inside a man possession.
- Press templates: 2-1-2 full-court (P-1: two at y 19.5–23 m, one at 13.5–16.5 m, two at y < 9 m), 1-2-2 converting to 1-3-1 / 2-3 (P-2: half-court posterior > 0.8 within 3 s).
- `PRESS_SETUP` and `INBOUND_LAG` (A0): `press_beaten_early` when `INBOUND_LAG` < `PRESS_SETUP` (P-5).
- Press usage policies: after makes vs after DREB (P-4: difference ≥ 0.4), dead-ball/timeout-only press (SC-3: ratio ≥ 3), contain vs trap ratio (P-6), press on ≥ 70% of possessions (P-7), engagement count = defenders with y > y_ball − 2 m (P-3).
- Zone-press fall-back (P-8): ≥ 3 of 4 non-ball defenders at r > 8 m retreat at mean ≥ 2.5 m/s in 1.5 s and reach r < 5.5 m by 3.0 s; "ball ahead" violation flag.
- Diamond-and-one / triangle-and-two (J-1, J-2): `CHASER` on one or two attackers; diamond top at r 4.6–6.5 m; onset/offset change-points within ±10 s of a timeout or make.
- Scheme-change triggers stored with each change-point: `timeout_after_run` (SC-1: opponent +8 in 6 game-minutes or FG% ≥ 65% over 10 possessions), `not_working` (SC-2: opponent PPP ≥ 1.15 over the first 10 half-court possessions), `blob_man` (SC-5: P(man | BLOB) ≥ 0.8 with P(man | other) ≤ 0.1), `late_game` (SC-7: game clock ≤ 5:00 in the 2nd half), change-up dosing (SC-6: season zone share ≤ 10% but one game ≥ 25%).
- `GET_BACK` clocks (A0): t_rim (first defender at r ≤ 1.5 m of his rim), t_stop (defender ≤ 2.0 m from the handler and handler speed < 3.0 m/s), n_back at 2, 3, 4 s. Overlaps inbox 004 `t_protect` (r ≤ 2.5 m) and `t_stop`; see §4.
- `OUTNUMBER(k_o, k_d)` at t0 + 2 s; 4-on-3 rules (T-2): matchup entropy drops ≥ 50% within 2 s of the fourth defender crossing half-court.
- Role-based get-back (T-3): Protector / Stopper / Sprinters assigned per game; role system if the same player holds a role on ≥ 70% of possessions.
- Transition wall (T-4): ≥ 2 defenders 1–4 m below the ball within 3 m of its path before the ball reaches r = 8 m.
- Transition swap (T-5): screenless reciprocal exchange within 6 s of `SET_DEF` between a mismatched small and the rim protector.
- Reaction latency (T-6): t0 to retreat speed > 2.5 m/s; target ≤ 0.6 s for the two players nearest half-court.
- Outlet contest (T-7): outlet receiver has a defender within 1.5 m during t0 … t0 + 1.5 s; ≤ 1 player within 2 m of the rebounder.
- MSU transition-defence flag (MSU-3): t_rim > 3.5 s after a DREB or > 4.0 s after a made-basket inbound, or n_back(t0 + 2 s) ≤ 1 when outnumbered.
- MSU 3v2 stack rule (MSU-5): two defenders within 1.0 m of the ball–rim line, 3–5 m apart radially; on the first wing pass the deep defender closes ≥ 2.5 m within 1.0 s.

### 2k. Existing requirements with sharper signals now available (no new label, new measurement)

- Iverson (A5.16): wing → opposite wing at y 4.6–7.0 m in 1.5–2.3 s at 4.5–6.0 m/s (set_taxonomy's first-pass y band was in imperial units; this is the metric equivalent).
- Elevator / gate (A5.17), hammer (A5.18), UCLA (A5.20), Hawk cut (A5.21), blind pig (A5.22), shuffle (A5.23), zipper (A5.24: block → slot in 1.3–2.0 s; flag `inbound_context` for the CTG pre-inbound meaning), floppy (A5.15).
- Short roll (A11.18: catch at r 3.0–6.0 m, |θ − 90°| ≤ 35°, within 2.0 s) and roll (radial velocity ≤ −1.5 m/s within 1.0 s; r < 2.5 m within 2.0 s).
- Spain (A3.18–A3.22: release read, Ram-into-Spain, big-on-big, side Spain from zipper + DHO, early Spain).
- Drop coverage depth now has a sourced band (1.83–3.05 m, `[N3]`).

---

## 3. Vocabulary proposals (for the owner of `config/vocabulary_map.yaml`; not edited here)

Sources: offense A9 and A11.20, defense "Rules for this section" landmarks and C-1 to C-13, motion_starts §0.2 and §19.

**Spots and regions**

- `short_corner`: provisional r 4.0–5.5 m, θ ≤ 15° (≥ 165°), centroid (4.5, 6°) until film calibration. Values in use differ: offense (4.5, 8°), motion_starts (4.54, 7.6°), defense (4.02, 5.7°).
- `high_short_corner`: (4.27, 20.6°) (zone note).
- `high_post`: band r 3.8–5.2 m, θ 70–110°; `nail` stays the point anchor (4.19, 90°).
- `ft_line_ext_inside` (4.83, 60.2°), `ft_line_ext_arc` (6.75, 38.4°), `ft_line_ext_wing` (7.73, 32.8°), mirrored on the left.
- `block_outside_lane` (2.18, 15.9°): used by BLOB templates; outside the vocab block (x = ±1.83 m).
- `mid_post` (3.1, 45°) and `mid_post_lane_line` (3.02, 52.7°).
- `corner_deep` centroid (6.8, 4.5°); all corner variants in use are inside the vocab corner class.
- Aliases `porch` and `ghost_spot` → `dunker_spot` (the "ghost" screen action stays separate).
- `45_spot` → wing (centroid (7.07, 45°)); never map "45" to the elbow without context; namespace the zone set `zone.Zone2.45` and `45_cut`.
- `top` template centroid (7.6, 90°).
- Canonical spot table: three files use different centroids (slot (7.3–7.4, 70°) vs (7.47, 70°) vs (7.62, 66.8°); wing (7.2, 40°) vs (7.3, 35°) vs (7.50, 45°); corner (6.8, 4–5°) vs (6.86, 3°) vs (6.81, 3.4°)). Proposal: one canonical table in the vocabulary map, with the others as named variants.
- Fill `one_pass_away` from passing-lane geometry; the defense file's 1/3–2/3 deny rule (M-3) is a candidate input.

**Action and set names (namespace where meanings collide)**

- `77` with sub-labels {`77_drag`, `77_stagger`, `77_wall`}.
- `double_high` with `trade` and `sink`; "2le" = MSU's spelling of "double" (inferred; undefined on its page).
- `spread_pnr` (spacing tag) vs `system.Spread` (Underwood).
- `shake` (corner lift during a side PnR) vs `shake_ballscreen` (Beilein fake wide pin-down into a spread ball screen).
- `chicago` = pin-down → DHO only; `zone.Chicago`, `CSUB.ChicagoPin`, `UM.ChicagoSplit` separate.
- `miami` (DHO → PnR) vs `zone.Miami`.
- `MSU.Special` vs `Flannery.Special`; `off.MSU.Fist` vs `def.VCU.Fist`; "80" and "Corners" namespaced by side of the ball and zone faced.
- Spain aliases {Spain, Stack PnR, Bamberg}; `stack_roll` separate; `align.stack_{vertical,diagonal,sideline}`.
- `hawk_cut` vs `blob.Hawk`; `circle_cut`, `press.Circle`, `blob.CircleLob`.
- `MSU_Blast` vs `blast_backdoor`; `Gator_4out` vs the drag "Gator" read; H15 vs X03 "Michigan"; separate entries for each "Elbow", "Loop", "Flare", "Split", "Forwards Out", "Get" and "Pistol" meaning (motion_starts §19).
- "Spartan" (Perkins Horns, H01 family) vs repo "Spartan Re-Screen": different plays.
- Horns Re-Screen = alias of Horns Twist (not a new item).
- `pin_in` with target class {man defender, zone slot}.
- `zipper` plus flag `inbound_context`.
- `wheel`: keep as an unresolved label; do not map until defined.
- `inverted_stagger`: provisional, unverified.
- "EOQ": FastModel label meaning end of half/period; NCAA men play halves (2026-27 keeps halves, `[Q2]`); meaning unverified.
- `spot_8p53m` replaces the legacy imperial-unit label for the 8.53 m mark.

**Defense names**

- "Beat and Belt" = "Beat the Belt" (one drill, two spellings, C-6).
- "catch" drop: unverified; no label until defined (C-5). "no screen": treat as an alias of ice / top-lock until film says otherwise (defense BS-16).
- 2-1-2 belongs under even-front zones (C-2); 3-2 and 1-2-2 are separate labels (C-4).
- `poa_quickest_path` (team-level over/under policy, BS-2).
- Amoeba origin: keep Webster/Pitt and Tarkanian side by side (C-1).

---

## 4. Open questions for Aldemir (one line each)

1. Which screen rule governs coding: strict (≤ 0.3 m/s for ≥ 0.5 s) or loose (< 0.6 m/s for ≥ 0.3 s), or store both as the offense file now does?
2. Rim centre from the baseline: 1.60 m (`docs/requirements.md`) or 1.575 m (offense §0.1)?
3. Approve one canonical spot table (slot, wing, corner, short corner centroids) in the vocabulary map, replacing the three slightly different tables?
4. Accept the provisional short corner (r 4.0–5.5 m, θ ≤ 15°) until film calibration?
5. Speed bands: the offense file uses sprint ≥ 6.0 m/s, inbox 003 uses sprint > 5.83 m/s, load_thresholds has a 5.5 m/s placeholder. Which one is the project band?
6. Transition-defence clocks conflict: `t_rim` r ≤ 1.5 m (defense A0) vs `t_protect` r ≤ 2.5 m (inbox 004) vs "first defender back" r ≤ 6.75 m or midcourt (inbox 003). Keep all three as separate fields?
7. Do you know MSU's in-house names for its 2025-26 sets? No public source names any.
8. What do "2le", "Trade", "naked curl", "L option" and "EOQ" mean in MSU's book?
9. Which F18.1 sets (DHO PNR Reject Pin, EOQ Horns, 21 Pin Chin, Miami Comeback, Double Fan, Spartan Re-Screen, SLOB Corner, Wizard) are still run in 2025-26 or 2026-27?
10. Is the 1-3-1 "Special" / "Fist" zone package still used, or is the 2024-25 swallow-cut "Vs Zone" the current zone offence?
11. What is MSU's press-break alignment? Only the "special teams" quote exists.
12. Does MSU's break use a designated trailer and leak-out, as in the older shooting-trailer pitch-back?
13. What is MSU's 2025-26 and 2026-27 ball-screen coverage? Nothing opened describes it.
14. Does MSU defend handoffs "two ways by position" as switch vs non-switch, or something else?
15. Ball height: is a lob-apex measurement (z ≥ 3.5 m) in scope for broadcast tracking, or do we use the catch-location proxy only?
16. Is pose estimation in scope for the transition "wall" backpedal and post-defender facing?
17. Which source of roster heights (cm) should we use for mismatch, cross-match and scram labels?
18. Should women's, high-school, NBA and European items stay as templates or only as low-weight priors?
19. Keep or drop the four Big Ten items whose men's attribution is unverified (A2.2, A2.17, A2.35, A2.41)?
20. Approve the namespacing scheme for name collisions (`MSU.`, `zone.`, `blob.`, `press.`, `def.`)?
21. Confirm the rule that motion_starts holds the canonical template and signature while offense_full keeps the MSU evidence for the 13 shared sets?
22. Is a paid source worth it for the key gaps (Synergy, Hoop Vision, UM Hoops+, Feed The Post, A Quick Timeout, Championship Productions videos)? Budget decision.
23. May researchers read Cloudflare- or 403-blocked sites (MGoBlog, Breakthrough, The Only Colors) in the built-in browser, as was done for Breakthrough?
24. Which Big Ten opponents get templates first, given that USC, Ohio State, Washington, UCLA, Oregon, Penn State and Rutgers 2025-26 have no step-by-step sets?
25. Are the Diamond and 1-2-2 / Line alignment families needed? No source filled them.
26. Should "Wheel" be defined from film, or dropped as a label?
27. Is the 2026-27 "19 on the shot clock" backcourt rule confirmed for our games (`[Q2]`)?

---

## 5. Research gaps (consolidated from the ten notes and the three files)

**Timing and geometry**
- No opened source gives any set, cut, slide or trap timing in seconds. Every timing window and detection signature is [HEURISTIC] and must be fitted on film. The only sourced timing items: squared2020's 0.66 s pass flight with closeout speeds; speed bands from PMC12526517; drop depth 1.83–3.05 m `[N3]`. Sourced cues for motion starts are spatial only (Corey cut, slot cut).
- FastModel shows positions only as diagram images the fetch tools could not read. Most start spots are template assignments marked inferred or unverified, including Coaching Toolbox alignments.
- `short_corner` and `one_pass_away` are still undefined in the vocabulary map.
- No basketball paper on automatic zone or press detection was found. The McQueen 2014 screen-detection thresholds were unavailable (Sloan PDF 404, Medium 403).

**MSU coverage**
- No 2025-26 MSU set by in-house name. FastModel has no MSU entry after 13 Mar 2025, but this rests on a scan whose pages are not individually cited, so it is an **unverified absence**. 2025-26 items come from film-room prose only.
- Paywalled MSU breakdowns read as previews only: UM Hoops+ film rooms (28 Jan, 1 Feb, 10 Mar 2026), Feed The Post paid posts. Also MGoBlog (403/Cloudflare): Horns Rip / Rip Away `[S24b]` and the 2024-25 hedge/blitz claim `[D24]` are unverified in this research.
- No YouTube transcripts (timedtext empty; yt-dlp failed). N4/N5 game identifications are inferred from scorebugs.
- Unconfirmed for 2024-26: every F18.1 set, the 1-3-1 Special/Fist zone sets, press-break structure, trailer and leak-out roles, any diagrammed ATO, MSU end-of-game inbounds.
- MSU's own zone use in 2024-26: none found (only opponents zoning MSU). MSU press structure (2023-24, Oct 2026 exhibition) unverified.
- MSU ball-screen coverage for 2025-26 and 2026-27: no source opened (The Only Colors 403, Detroit News 402, MSU clips PDF 404, Michigan Daily 429).
- Izzo's two DHO coverages, pin-down/flare coverages and elbow-and-block technique: video titles only (paywalled).
- Title-only MSU entries: Two Ball-Screens, Slip-Reverse, Double Ball-Screen, Ball-screen with Down-Screen for O2, DHO/Double-Screens (Coach's Clipboard members area); summary-only: Horns Twist Veer, 2le High Trade, Stagger Slip Curl & Pop, Forwards Out Wide, Horns Out Slip; "Twist BLOB" still title-level.
- No MSU BLOB/SLOB/ATO PPP or frequency data (Synergy and Hoop Vision paywalled).
- Seasons unverified: Elbow Away STS / Pindown (published Nov 2020), MSU 14-Circle, ISO-3 Chest, Zipper ATO; several FastModel game dates (vs Maryland 2014-15, Sparty, Clear BLOB, Quick Duck-In, Brush BLOB); several zone-set seasons inferred from publish dates.
- Failed MSU pages: Elevator Drive Option, Floppy Stagger Punch (vs Ohio State 2012) and "Sparty" BLOB (FastModel 404).

**Big Ten and other programs**
- No step-by-step 2023-26 men's sets for USC (Musselman), Ohio State (Diebler), Penn State 2025-26, Rutgers 2025-26, Washington, UCLA, Oregon. Purdue, Michigan, Iowa and Illinois 2025-26 named sets are paywalled or video-only (A Quick Timeout, Hoop Vision, Feed the Post, Inside the Hall).
- Michigan Double Elevator BLOB: exists (14 Jan 2026), geometry unverified (video only).
- Many FastModel entries do not state men's vs women's; women's entries were excluded.
- Claims from search summaries only (unverified): Ohio State short-roll reads, Indiana 50.5% 3PA rate, Minnesota tempo 362nd, Underwood pick-and-pop quote, Oregon post traps on Bittle, Iowa 1-2-2 press and Wisconsin 2-3/3-2, Penn State man press and end-of-half diamond, Syracuse press after makes, Louisville "switch-everything" zone, Oregon assistant quote, WVU 1-3-1 lineage, "Virginia hammer vs MSU", shuffle at Air Force and North Carolina, Northwestern 2017 home-run pass.
- No Big Ten box-and-one, diamond-and-one or triangle-and-two found for 2023-26. No D-I team found for scram switch, late switch, hedge-and-plug or drop load (NBA/European evidence only). Tennessee coverage unverified. No D-I team confirmed for Motion Strong; Michigan Motion Weak season inferred; no college "Laker cut" or "pin-in" user confirmed.
- No NCAA source separates empty-corner from empty-side ball screens (FiveThirtyEight piece redirected; archive blocked). No source for an inverted Spain; no college "Ram" breakdown; Spain origin disputed (UNC 2005 via Larry Brown, 2009 EuroLeague, Scariolo 2016).

**Terms without definitions on any opened page**
- "Wheel", "Turnout", "loop" and "circle" (meanings inferred from diagrams), "inverted stagger", "2le", "Trade", "naked curl", "L option", "catch" coverage, "no screen" coverage, FIBA "Power" entry, DHO "wheel".

**Rules**
- The 2025-26 NCAA men's rulebook was over the 10 MB fetch limit; rule numbers come from the 2024-25 book. 2025-26 wording unverified.
- Sources conflict on whether Michigan had a timeout left in 2018. The HoopTactics last-shot second counts and Harvard Sports Analysis timeout studies did not open (premium / HTTP 500); the NCAA.com 2021 ATO PPP article was empty.

**Blocked or failed sources (not cited for content)**
- HTTP 403: Breakthrough Basketball (read in the built-in browser instead; only [MA67], [MA69], [MA80], [MA84] independently re-checked), CelticsBlog Elbow Zoom, Championship Productions (Bill Self entries, James Jones motion starters), Duke Basketball Report, Duke Chronicle, InsideNU, SI, Daily Orange, Medium.
- HTTP 404: every www.fastmodelsports.com URL (the playbank host worked), FastModel Xavier Rip, Spurs Motion Weak, Warriors Motion Weak, Texas Flat Weave, VCU Quick Slip, UCLA Early Pindown PNR Slip, Oklahoma Ram Motion, Celtics Ram newsletter, halfcourthoops Furman Chin and NCAA openers, hoopstudent dribble-entry, Kansas Zone Post Hook.
- DNS failure: FIBA WABC coaching pages, 360Player. Video-only: Basketball Immersion (only "Doornekamp" confirmed, via FastModel).
- Not located: "Coach Daniel" / "TheCoachingTools" (coachingtoolbox.net used instead), "The Basketball Dictionary" (HoopStudent glossary used).

**Cross-file consistency still to settle (see §4)**
- Screen rule, rim offset, spot centroids, speed bands and transition-defence clocks differ between files and inboxes.
- Hoop-Math and FastScout transition definitions were not opened in Job A (C-12). Job D covers them in `docs/research/transition_full.md` and inbox 004.
