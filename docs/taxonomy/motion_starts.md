# Motion Starts and Half-Court Entries: Taxonomy for Tracking-Based Recognition
### Michigan State (Tom Izzo) focus. Extends `docs/taxonomy/offense_full.md` (F3 half-court alignments / entries) and `docs/research/set_taxonomy.md` (§1.3, §3.2); it does not repeat what they already hold.

Date: 2026-10-18. Status: research draft (job A of `coord/prompts/002-claude-code-taxonomy-and-markets.md`). Not reviewed on film.

**Scope.** A "motion start" or "half-court entry" is the first 2–4 actions that start a half-court possession (the alignment plus the opening passes, cuts and screens). This file lists named starts that are **not** in `offense_full.md` or `set_taxonomy.md`, plus entries flagged **[RICHER VARIANT]** where the repo has only a name or a one-liner. Entries are grouped by the **alignment family** at the set moment, then numbered inside each family.

**How this file was built.** It merges two research notes compiled on 2026-10-17 by the job-A researchers in this run (`motion-a`, which used FastModel PlayBank, Coach's Clipboard, Breakthrough Basketball, Better Basketball and HoopStudent; and `motion-b`, which used Hooper University, The Hoops Geek, HoopStudent, the FIBA Europe terminology PDF, Basketball For Coaches, Coaching Toolbox, UM Hoops, Hoop Scoop and Wikipedia). Every URL in the Sources section was opened in this run by a researcher (WebFetch, or the built-in browser for Breakthrough Basketball, which returns HTTP 403 to automated fetches). Three pages were re-opened by the writer on 2026-10-18 as spot checks and matched the notes: [MA34], [MB2], [MA9]. No source was added from memory.

---

## 0. Notation

### 0.1 Coordinates and units

- **Frame and spot names:** see `config/vocabulary_map.yaml`. Origin at the rim centre; θ in degrees measured from the **right baseline** at the rim centre (0° = right baseline, 90° = top of the key, 180° = left baseline); x = r·cosθ (positive toward the right sideline), y = r·sinθ (toward half-court). Units: metres, seconds, degrees. Any feet in a source were converted at 1 ft = 0.3048 m.
- **Mirroring:** every play can be run to either side. Mirror by θ → 180° − θ (x → −x).
- **Player numbers** (1–5) are the role labels each source uses (1 = point guard, 2 = shooting guard, 3 = wing, 4 = power forward / big, 5 = centre), not jersey numbers.

### 0.2 Canonical spots used in "Start alignment"

The sources give spots in words or as diagram images that the fetch tools could not read. The (r, θ) values below are this file's canonical coordinates for each named spot, chosen to sit inside the `vocabulary_map.yaml` class. When a source does not say where a player starts, the item says **inferred** or **unverified**.

`ALIGN` matches against the `offense_full.md` §3.1 template coordinates; the canonical spots below and the per-section "Template start" lines are descriptive only (for reading the items), and the two tables should be harmonised before coding. Slot tests in signatures use the vocabulary slot class: θ 60–80° / 100–120°, r ≥ 6.75 m (upper bound 8.2 m allowed).

| Code | x, y (m) | r (m), θ (°) right / left | `vocabulary_map.yaml` class |
|---|---|---|---|
| TOP | 0.00, 7.60 | 7.60, 90.0 | top (r ≥ 6.75, 80° < θ < 100°) |
| DEEP | 0.00, 9.80 | 9.80, 90.0 | top, about 3 m beyond the arc |
| SLOT | ±3.00, 7.00 | 7.62, 66.8 / 113.2 | slot (r ≥ 6.75, 60° < θ ≤ 80°) |
| SLOT-LL (slot on the lane line extended; Hooper Princeton spots [MB2]) | ±1.83, 7.40 | 7.62, 76.1 / 103.9 (computed) | slot |
| ARC-HIGH (Horns bigs just outside the arc) | ±1.80, 6.90 | 7.13, 75.4 / 104.6 | slot |
| WING (centre, "45") | ±5.30, 5.30 | 7.50, 45.0 / 135.0 | wing (r ≥ 6.75, 12° < θ ≤ 60°) |
| FTX (free-throw line extended, about 0.6 m outside the arc; the arc is at \|x\| = 5.29 m at y = 4.19 m) | ±6.00, 4.19 | 7.32, 34.9 / 145.1 | wing |
| CORNER | ±6.80, 0.40 | 6.81, 3.4 / 176.6 | corner (r ≥ 6.60, θ ≤ 12° or ≥ 168°) |
| ELBOW | ±1.83, 4.19 | 4.57, 66.4 / 113.6 | elbow (given anchor) |
| HIGH POST | ±0.90, 4.30 | 4.39, 78.2 / 101.8 | — |
| NAIL | 0.00, 4.19 | 4.19, 90.0 | nail |
| MID-POST | ±2.20, 2.20 | 3.11, 45.0 / 135.0 | — |
| BLOCK | ±1.83, 0.90 | 2.04, 26.2 / 153.8 | block (x = ±1.83, y 0.3–1.5) |
| DUNKER | ±2.70, 0.30 | 2.72, 6.3 / 173.7 | dunker_spot (2.0 ≤ \|x\| ≤ 3.5, y ≤ 0.6) |
| SHORT CORNER | ±4.50, 0.60 | 4.54, 7.6 / 172.4 | short_corner ("to be defined from film" in the map; provisional) |
| UNDER | ±0.90, 0.30 | 0.95, 18.4 / 161.6 | under the basket |
| RIM | — | r < 1.22 | restricted area (`offense_full.md` §0.1) |

### 0.3 Detection primitives used in signatures [HEURISTIC]

Every "Detection signature" and every timing window in seconds in this file is **[HEURISTIC]**: an engineering proposal to be fitted on film, not a sourced fact. **No opened source gives timings in seconds.** The only sourced timing cues are spatial (Corey cut, slot cut). The screen rule follows this task's brief; `offense_full.md` §0.2 uses a looser screen rule (screener speed < 0.6 m/s for ≥ 0.3 s), and the two should be harmonised before coding.

| Primitive | Rule |
|---|---|
| `SCR(s→u)` | Screener *s* has speed ≤ 0.3 m/s for ≥ 0.5 s, and teammate *u*'s path passes within 1.2 m of *s* during that window; *u*'s defender is deflected (heading change > 30°) or slowed (speed drop > 40%) within 1.5 m of *s*. **Ball screen** if *u* holds the ball. Direction classes (down / back / flare / cross / UCLA / flex) as `SCREEN_DIR` in `offense_full.md` §0.2. |
| `STAGGER(s1,s2→u)` | Two `SCR` events on the same *u*, screeners 2–5 m apart along *u*'s path, second contact ≤ 1.5 s after the first. Triple stagger = three such contacts. |
| `DOUBLE(s1,s2→u)` | Two screeners ≤ 1.2 m apart, both stationary, *u* passes both within 1.2 m. **Elevator** = a `DOUBLE` whose gap closes to < 0.6 m within 0.5 s after *u* passes. |
| `DHO(a→b)` | Ball changes hands with a–b distance ≤ 1.0 m, ball flight ≤ 1.0 m, and at least one of the two moving > 1 m/s. |
| `FAKE_DHO(a,b)` | a–b distance ≤ 1.5 m with the ball holder dribbling toward b, no transfer, and b moves away ≥ 3 m within 1.5 s. |
| `DRIBBLE_AT(a→b)` | Ball handler dribbles ≥ 2.5 m on a heading within 25° of teammate b, ending ≤ 3.5 m from b. |
| `PASS(a→b)` | Ball flight > 1.0 m ending in b's control. `ENTRY` = receiver at r < 3.5 m (`POST_ENTRY` if back to the basket). `SKIP` = crosses x = 0 with \|Δx\| > 8 m. `REVERSAL` = sign(x_ball) changes over ≤ 2 passes. |
| `CUT(p)` | Off-ball displacement ≥ 3 m in ≤ 1.5 s. Path classes: basket (ends r < 2 m), backdoor (heading reverses > 120° within 0.6 s of a step toward the ball, ends r < 2 m), shallow (top/slot → ball-side corner along r 6–8 m), Iverson (wing → opposite wing at y 4–7 m), UCLA (top/slot → block past an elbow screener), flex (weak corner → ball-side block along y < 1.5 m), zipper (block → slot/top up the lane line), chin (slot/wing → rim past an elbow back-screener after a reversal), loop (corner → wing/top behind the ball handler), shuffle (diagonal weak wing → ball-side block past a high screener). |
| `ROLL / POP / SLIP` | After a screen: **roll** = screener reaches r ≤ 2.5 m within 2.0 s with Δr ≤ −2 m from the screen spot (a short roll that stops at r 3–5 m, as in H30, is not a roll); **pop** = after the screen the screener moves ≥ 1.5 m away from the handler with Δr ≥ 0 (not toward the rim), ends at r ≥ 6.75 m within 1.5 s, and never comes within r 5.5 m in that window (a screener who only holds or drifts < 1.5 m is neither; redefined by the fixer, 2026-10-18 (UTC) so that screens set at or above the arc do not count as pops by default); **slip** = screener stationary < 0.5 s, then moves toward the rim at ≥ 3 m/s. |
| `DRIVE(p)` | Dribble that starts at r > 6.1 m and reaches r < 3.05 m (`offense_full.md` §0.2). |
| `SEAL` | Post player at r < 2.5 m with speed < 0.5 m/s for ≥ 0.8 s, body between his defender and the ball line. |
| `LOB` | Pass with ball apex > 3.5 m that ends at r < 1.5 m. |
| `ALIGN(t)` | Five-player snapshot when the ball handler first slows below 2 m/s with y_ball < 9 m (or the first pass after crossing half-court), matched to a template by Hungarian assignment; accept if mean error < 1.8 m and it beats the runner-up by > 0.4 m (`offense_full.md` §0.2, §3.1). |
| `t0` | The first action named in the sequence (usually the first pass, or the first dribble toward a screen). All timing windows are seconds after t0. |

### 0.4 Item format and tags

Each item has: **Name and aliases; Family** (offense family numbers F1–F18 from `offense_full.md`; no defensive items were found for this file, so the `defense_full.md` numbering is not used); **Start alignment** (each spot as (r m, θ°)); **Roles; Ordered actions** (timing windows [HEURISTIC]); **Usual counters; Detection signature** [HEURISTIC]; **Teams documented** (MSU first, then other NCAA D-I, then other levels; NBA, WNBA and European names are secondary aliases); **Sources; Confidence**.

Tags: **[MSU]** = Michigan State usage documented in an opened source. **[RICHER VARIANT]** = overlaps a name already in the repo but adds the sequence. **[NAME COLLISION]** = reuses a repo label for a different action. **unverified** = not confirmed from a page opened in this run. **inferred** = spot or season assigned by the researcher from the step text or a publish date.

Source keys: `[MA#]` = URLs opened for note `motion-a` (A-numbers kept from the note); `[MB#]` = URLs opened for note `motion-b` (numbered 1–43 as in that note). Full URLs are in the Sources section.

Season convention: "2018-19" etc. Where a page gives only a publish date and no game, the season is marked inferred.

---
## 1. Horns family (F3.2)

**Template start** (used where an item says "Horns template"): 1 at TOP (7.60, 90.0) with the ball; 4 and 5 at the ELBOWS (4.57, 66.4 / 113.6), or just outside the arc at ARC-HIGH (7.13, 75.4 / 104.6) when stated; 2 and 3 in the CORNERS (6.81, 3.4 / 176.6). FastModel diagrams were not readable, so Horns spots are template assignments unless the item says otherwise. Detection base for every item: `ALIGN` matches Horns (`offense_full.md` §3.1), then the item's discriminator.

Alias only (not a new entry): **Horns Re-Screen** (Coach's Clipboard: 1 off 5, 5 clears to the opposite block, 1 turns back off 4) = `offense_full.md` **Horns Twist** with the first screener clearing to the block [MA1].

### H01. Elbow Punch Stagger / "Spartan" [MSU]

- **Name and aliases:** "Elbow Punch Stagger" (FastModel, 2019) [MA30]; "Spartan" (Coach's Clipboard, Lason Perkins Horns offense DVD) [MA2]. Correction (fixer, 2026-10-18 (UTC)): [MA2] does not credit Spartan to Izzo; it credits the plays to Perkins's DVD and says only that Izzo "uses the Horns set at times and might run this play". MSU usage of this exact play via [MA2] = unverified; the MSU tag for H01 rests on [MA30] only. One family; the step order differs slightly between the two sources. Not the same as repo "Spartan Re-Screen" (F18).
- **Family:** F3.2 Horns → F7 post feed ("punch") → F8 triple stagger.
- **Start alignment:** Horns template: 1 TOP (7.60, 90.0); 4 and 5 ELBOWS (4.57, 66.4 / 113.6); 2 and 3 CORNERS (6.81, 3.4 / 176.6) [MA2]. FastModel: 4 at an elbow, 2 in a corner; other spots unverified [MA30].
- **Roles:** elbow catcher (4 in FastModel, 5 in Coach's Clipboard); 1 cutter, then screener for the other big (post target); 2 shooter off the triple stagger; 3, 4, 5 stagger screeners.
- **Ordered actions (FastModel):**
  1. t0: 1 passes to 4 at the elbow; 2 lifts out of the corner; 3 cuts to the weak side (0–2.0 s).
  2. 1 cuts, turns and screens for 5; 5 cuts over the screen; 4 feeds 5 (2.0–4.0 s).
  3. If no post feed, 1 pops to catch from 4 (4.0–5.5 s).
  4. 3, 5 and 4 set a triple stagger for 2; 1 passes to 2 (5.5–8.0 s) [MA30].
  - Coach's Clipboard version: 1 passes to 5, screens for 4 who goes to the low block, then 3/4/5 triple-stagger for 2 [MA2].
- **Usual counters:** post feed first, shooter second [MA30]; if X4 helps on 2, 4 slips into the middle [MA2].
- **Detection signature [HEURISTIC]:** Horns `ALIGN`; `PASS(TOP→ELBOW)`; the passer runs down the lane and becomes a stationary screener for the other big, who reaches r < 2.5 m within 1.5 s; optional `ENTRY`; then three `SCR` contacts on one cutter (triple `STAGGER`, spacing per §0.3) along a baseline-to-wing path, last contact ≤ 2.5 s after the first; cutter catches at r ≥ 6.75 m.
- **Teams documented:** **Michigan State 2018-19** (revived for the NCAA Tournament; long-running set) [MA30]. [MA2] = unverified for MSU (Izzo "might run this play" only).
- **Sources:** [MA30], [MA2].
- **Confidence:** high.

### H02. Horns Pistol [MSU]

- **Name and aliases:** "Michigan State – Horns Pistol". Not the same as `offense_full.md` 2.2 Pistol ("21") dribble entry: here the DHO comes from a big at the top ("misdirection DHO").
- **Family:** F3.2 Horns → F6 DHO → F5 trailing ball screen.
- **Start alignment:** Horns template (page diagram unreadable).
- **Roles:** 1 passer, flare receiver, weak-side exchanger; 4 catcher up top, DHO giver, then lifts; 5 flare screener, then trailing ball screener and roller; 2 DHO receiver and handler; 3 weak-side exchanger.
- **Ordered actions:**
  1. t0: 1 passes to 4; 5 flare-screens for 1 (0–1.5 s).
  2. 4 DHOs to 2; 5 trails behind 4 (1.5–3.0 s).
  3. 3 and 1 exchange on the weak side; 5 ball-screens for 2 and rolls; 4 rises behind the roll (3.0–5.5 s) [MA29].
- **Usual counters:** none listed.
- **Detection signature [HEURISTIC]:** `PASS(TOP→elbow big)` caught at r 6.5–7.5 m; flare `SCR` by the other big on the passer; `DHO(big→corner player)` with the receiver having come up from θ ≤ 12° to θ 25–50°; within 2.0 s a ball `SCR` on the DHO receiver by the flare screener with `ROLL`, while the DHO giver moves to r ≥ 6.75 m behind the ball.
- **Teams documented:** **Michigan State 2016-17** (early in the NCAA game vs Kansas; layup) [MA29].
- **Sources:** [MA29].
- **Confidence:** high.

### H03. Horns Swing Pistol [MSU]

- **Name and aliases:** "Horns Swing Pistol". The page links it to a "Horns Elbow Series" post [MA32].
- **Family:** F3.2 Horns → F6 DHO chain → F5 roll/pop split.
- **Start alignment:** Horns template.
- **Roles:** 1 (Cassius Winston) DHO giver, then down-screen user and DHO receiver; 3 DHO receiver and swing passer; 5 hub, second DHO giver, roller; 4 down screener, popper.
- **Ordered actions:**
  1. t0: 1 DHOs with 3 (0–1.5 s).
  2. 3 dribbles toward the top and passes to 5; 3 cuts to the ball-side wing (1.5–3.0 s).
  3. 4 down-screens for 1; 5 DHOs with 1 (3.0–5.0 s).
  4. 4 pops and 5 rolls (5.0–6.5 s) [MA32].
- **Usual counters:** none listed.
- **Detection signature [HEURISTIC]:** `DHO(1→3)` at r 6.5–8 m; `PASS(3→5)` with 5 at r 6.5–7.5 m, θ 75–105°; down `SCR(4→1)`; `DHO(5→1)` within 2.5 s of the pass; then the two bigs split (one `ROLL`, one `POP`) within 2.0 s.
- **Teams documented:** **Michigan State 2018-19** (to get Winston attacking toward the basket; published 2019-02-25; season inferred from publish date) [MA32].
- **Sources:** [MA32].
- **Confidence:** high.

### H04. Horns Loop STS [MSU]

- **Name and aliases:** "Horns Loop STS". Uses the word "loop" but the page text has no corner loop (see H12 and L06).
- **Family:** F3.2 Horns → F8 down screen, back screen, screen-the-screener → F5.
- **Start alignment:** Horns template.
- **Roles:** 4 down screener for 2, then STS receiver; 2 wing receiver and PnR handler; 5 back screener for 1, ball screener, down screener for 1; 1 entry passer, back-screen cutter, back screener for 4, shooter.
- **Ordered actions:**
  1. t0: 4 down-screens for 2; 1 passes to 2 (0–2.0 s).
  2. 5 back-screens for 1 (2.0–3.5 s).
  3. 5 ball-screens for 2; 1 back-screens for 4 (3.5–5.5 s).
  4. 5 down-screens for 1 (5.5–7.0 s) [MA33].
- **Usual counters:** two scoring outcomes, layup off the back screen and three off the down screen; screening before receiving a screen occupies the defender [MA33].
- **Detection signature [HEURISTIC]:** down `SCR` by an elbow big for a corner player (cutter +y from θ ≤ 12° to the wing); `PASS(TOP→wing)`; back `SCR(5→1)` with 1 reaching r < 2 m; within 2.0 s a ball `SCR` by 5 on the wing **and** a concurrent back `SCR` by 1 on 4; then a down `SCR(5→1)` with 1 ending at r ≥ 6.75 m. Key cue: 5 is the screener in three screen events within about 5 s.
- **Teams documented:** **Michigan State 2018-19** (published 2019-03-30; season inferred from publish date) [MA33].
- **Sources:** [MA33].
- **Confidence:** high.

### H05. Horns, Winston read set (roll and seal) [MSU] [RICHER VARIANT of Horns PnR / Horns Twist]

- **Name and aliases:** "Michigan State Spartans – Horns" (2019). Adds MSU's roll-and-seal with the opposite big filling behind; the pass to the filling big is read here as a high-low (inferred; [MA38] shows "5 rolls and seals" and a pass from 1 to 4 but does not name a high-low).
- **Family:** F3.2 Horns → F5 Horns PnR / Twist → F7 seal, high-low (inferred).
- **Start alignment:** 1 TOP (7.60, 90.0); 4 and 5 lift to ARC-HIGH (7.13, 75.4 / 104.6) "for horns screens"; 2 in a CORNER (6.81, 3.4) [MA38]; 3 not described.
- **Roles:** 1 reader and handler; 5 and 4 screeners (one rolls and seals, the other fills behind); 2 corner lift.
- **Ordered actions:**
  - Option 1: t0 4 and 5 lift; 1 comes off 5 (0–1.5 s); 5 rolls and seals, 4 fills behind (1.5–3.0 s); 1 passes to 4; 2 lifts out of the corner (3.0–4.5 s).
  - Option 2: 1 comes off 4; 4 rolls; 1 goes off 5 (twist); 5 rolls and seals; 1 passes to 4; 2 lifts (0–6.0 s) [MA38].
- **Usual counters:** Option 1 vs Option 2 is the handler's read [MA38].
- **Detection signature [HEURISTIC]:** Horns `ALIGN` with both bigs at r 6.5–7.5 m; ball `SCR`; screener `ROLL`s to r < 2.5 m and `SEAL`s; the other big moves to r ≥ 6.75 m, θ 70–110° and catches from 1 within 3.0 s; corner player moves from θ ≤ 12° to θ 20–45°.
- **Teams documented:** **Michigan State 2018-19** (vs LSU, NCAA Tournament) [MA38].
- **Sources:** [MA38].
- **Confidence:** high.

### H06. Horns Out Slip [MSU]

- **Name and aliases:** "Horns Out Slip".
- **Family:** F3.2 Horns → F8 screens for out-cuts → F5 slipped ball screen.
- **Start alignment:** Horns-type; spots unverified (the page text was garbled in the fetch) [MA31].
- **Roles:** perimeter cutters coming "out" to the arc; 5 ball screener who slips; 1 passer.
- **Ordered actions (as rendered):** screens are set for out-cuts; 5 sprints to slip the ball screen; 1 passes to 5 for a dunk [MA31]. Exact order unverified.
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** one or two off-ball `SCR` events sending perimeter players outward (Δr > +2 m, ending r ≥ 6.75 m); 5 approaches the handler at ≥ 3 m/s and `SLIP`s (stationary < 0.5 s within 1.5 m of the handler) to r < 1.5 m, catching within 1.0 s.
- **Teams documented:** **Michigan State 2018-19** (ATO; key basket in the one-point Elite Eight win over Duke) [MA31].
- **Sources:** [MA31].
- **Confidence:** low-medium (steps garbled; alignment unverified).

### H07. Horns 23 Back [MSU]

- **Name and aliases:** "Horns 23 Back".
- **Family:** F3.2 Horns → F8 back screen, dribble-at backdoor.
- **Start alignment:** Horns template.
- **Roles:** 1 entry passer, back-screen cutter, shooter; 4 receiver and dribbler at 2; 2 backdoor cutter; 5 back screener.
- **Ordered actions:**
  1. t0: 1 enters to 4 (0–1.0 s).
  2. 5 back-screens 1, who clears (1.0–2.5 s).
  3. 4 dribbles toward 2, who cuts backdoor (2.5–4.0 s).
  4. 4 turns back and passes to 1 coming off 5's back screen (4.0–5.5 s) [MA44].
- **Usual counters:** backdoor for 2 on the dribble-at [MA44].
- **Detection signature [HEURISTIC]:** `PASS(TOP→elbow big)`; back `SCR(5→1)`; `DRIBBLE_AT(4→2)` and 2 `CUT(backdoor)` to r < 2 m; then `PASS(4→1)` with 1 at r ≥ 6.75 m (page tags say "need a 3").
- **Teams documented:** **Michigan State 2018-19** (late vs Texas Tech, Final Four) [MA44].
- **Sources:** [MA44].
- **Confidence:** medium-high.

### H08. Horns Cutter 15 PNR [MSU]

- **Name and aliases:** "Horns Cutter 15 PNR" ("15" = 1–5 pick-and-roll).
- **Family:** F3.2 Horns → F8 cutter off 5's screen → F5 slipped 1–5 PnR.
- **Start alignment:** Horns template.
- **Roles:** 1 handler; 3 cutter to the wing off 5's screen; 5 off-ball screener, ball screener, slipper; 4 corner lift.
- **Ordered actions:**
  1. t0: 1 dribbles over; 3 cuts to the wing off 5's screen (0–1.5 s).
  2. 5 runs PnR with 1 and slips hard to the rim (1.5–3.0 s).
  3. 1 passes to 3 on the wing; 4 rises from the corner (3.0–4.0 s).
  4. 3 throws into 5 on the block or creates (4.0–5.5 s) [MA45].
- **Usual counters:** post feed vs drive by 3 [MA45].
- **Detection signature [HEURISTIC]:** off-ball `SCR(5→3)` (page tag: cross screen); 5 then approaches 1 and `SLIP`s to r < 2.5 m; `PASS(1→3)` at the wing; `ENTRY(3→5)` within 2.0 s; corner player lifts (θ ≤ 12° → 15–40°).
- **Teams documented:** **Michigan State 2018-19** (late second half vs Texas Tech, Final Four) [MA45].
- **Sources:** [MA45].
- **Confidence:** medium-high.

### H09. Horns Weak Pin [MSU]

- **Name and aliases:** "Horns Weak Pin".
- **Family:** F3.2 Horns → F5 re-screen → F8 weak-side pin-down → slip.
- **Start alignment:** Horns template.
- **Roles:** 4 ball screener and re-screener; 1 handler; 5 weak-side pin screener and slipper; 3 pin receiver.
- **Ordered actions:**
  1. t0: 4 screens for 1, then re-screens (0–2.5 s).
  2. 5 pins for 3; 1 passes to 3 (2.5–4.0 s).
  3. 5 slips; 3 passes to 5 (4.0–5.0 s) [MA47].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** two ball `SCR` events by the same big on 1 within 2.5 s with opposite screener orientation (re-screen); a concurrent weak-side down `SCR(5→3)`; `PASS(1→3)` at r ≥ 6.75 m; 5 `SLIP`s to r < 2 m and catches within 1.5 s.
- **Teams documented:** **Michigan State 2013-14** (vs Ohio State; season inferred from the 2014-01-20 publish date) [MA47].
- **Sources:** [MA47].
- **Confidence:** medium-high.

### H10. Horns Rub Triple Stagger [MSU]

- **Name and aliases:** "Horns Rub Triple Stagger".
- **Family:** F3.2 Horns → F8 shuffle/rub cut by a big, triple stagger.
- **Start alignment:** Horns template.
- **Roles:** 5 shuffle cutter, then screener; 4 passer, then the last screener; 2 cutter around three screens; 1 receiver.
- **Ordered actions:**
  1. t0: 5 looks for the ball on a shuffle cut ("timing is crucial") (0–1.5 s).
  2. If not open, 5 continues and screens for 2 (1.5–3.0 s).
  3. After passing to 1, 4 screens for 2 (third and final screen) (3.0–4.5 s).
  4. 2 penetrates; others space (4.5–6.0 s) [MA37].
- **Usual counters:** 2 changes pace around the screens [MA37].
- **Detection signature [HEURISTIC]:** an elbow big cuts diagonally toward the rim past the other elbow (shuffle) and continues to screen; three `SCR` contacts on cutter 2 within ≤ 3.0 s total, the last by the player who just passed to 1; 2 catches and `DRIVE`s.
- **Teams documented:** **Michigan State 2014-15** (run throughout the tournament; published 2015-03-28) [MA37].
- **Sources:** [MA37].
- **Confidence:** medium.

### H11. Horns Twist Veer [MSU]

- **Name and aliases:** "Horns Twist Veer".
- **Family:** F3.2 Horns → F5 twist, veer.
- **Start alignment:** Horns template.
- **Roles:** handler; two Horns screeners; perimeter shooter (summary only).
- **Ordered actions:** the page gives only a summary: stacked ball-screen actions ending in a veer screen for an open shot [MA42]. Sequence unverified.
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** two ball `SCR` events from opposite directions on the same handler within 2.0 s (twist, `offense_full.md` 3.2); then the second screener sets an off-ball `SCR` (veer) for a perimeter shooter within 2.0 s of his ball screen.
- **Teams documented:** **Michigan State 2023-24** (published 2024-03-28; season inferred) [MA42].
- **Sources:** [MA42].
- **Confidence:** low (summary only).

### H12. Horns Loop (corner loop off a down screen)

- **Name and aliases:** "Loop" (Coach's Clipboard Horns plays, Cheryl Reeve, Minnesota Lynx) [MA1]; "Loop" (Lason Perkins Horns offense DVD, three variations; Breakthrough, Joe Haefner) [MA67] (re-opened by the fixer, 2026-10-18 (UTC) in the built-in browser; the Perkins steps and the three variations below match the page). Related: L06 Loop behind (1-4 low), S03 Transition loop. Not the same as H04 Horns Loop STS.
- **Family:** F3.2 Horns → F8 down screen, loop cut → F7 high-low.
- **Start alignment:** 1 TOP (7.60, 90.0); 4 and 5 at the ELBOWS / ARC-HIGH (7.13, 75.4 / 104.6); 2 and 3 in the CORNERS (6.81, 3.4 / 176.6) [MA1].
- **Roles:** 1 dribbler high and wide; ball-side corner 3 looper to the top; 5 down screener, then high-post receiver; 2 inside cutter for the high-low; 4 spacer.
- **Ordered actions (Reeve, Coach's Clipboard):**
  1. t0: 1 dribbles left, high and wide (0–1.5 s).
  2. Ball-side corner 3 gets a down screen from 5 and cuts to the top to fill 1's spot; 1 passes to 3 (1.0–3.0 s).
  3. 5 steps out to the ball; 4 slides out; 3 hits the ball-side high post 5; 2 cuts hard inside for the high-low (3.0–5.0 s) [MA1].
  - Perkins version: 1 dribbles down the side; 4 steps out and catches; 2 clears to the opposite block; 5 screens for 3 to the ball-side block, then for 2; 4 passes to 2 on the wing; 3 clears to the corner; 5 ball-screens 2 (roll → 4 fills behind; pop → 4 dives). Variation 2: 3 and 5 stagger back-screen for 1, 4 screens for 3. Variation 3: 5 and 4 set an L-screen for 2 [MA67].
- **Usual counters:** if X3 jumps the screen, 3 pops back to 1 for a shot [MA1].
- **Detection signature [HEURISTIC]:** handler dribbles toward FTX (r 6–7.5 m, θ 25–45°) while the same-side corner player gets a down `SCR` from the elbow big and moves from θ ≤ 12° up and **behind** the handler (y > y_handler + 1 m) to the slot/top, catching within 1.0 s of arrival; then `PASS` to a big at the high post (r 4–5 m) and a cutter reaching r < 2 m.
- **Teams documented:** No NCAA D-I program confirmed. Minnesota Lynx (WNBA, Reeve) [MA1]; Perkins's DVD version [MA67], Perkins coaching at Cary Academy HS [MA2]. Note: [MA2] supports only Perkins = Cary Academy; it has no play called "Loop".
- **Sources:** [MA1], [MA67], [MA2] (Perkins = Cary Academy only).
- **Confidence:** medium-high.

### H13. Bucks

- **Name and aliases:** "Bucks" (Coach's Clipboard Horns plays; credited to Del Harris, Milwaukee Bucks; starts from a box and the bigs step up to Horns) [MA1].
- **Family:** F3.3 Box → F3.2 Horns → F5 → F8 stagger for a big.
- **Start alignment:** Box, then Horns: bigs rise from the BLOCKS (2.04, 26.2 / 153.8) to the ELBOWS (4.57, 66.4 / 113.6); 1 TOP; 2 and 3 to the CORNERS (spots per template) [MA1].
- **Roles:** 1 handler; 4 ball screener, then down screener for 2; 2 and 3 stagger screeners for 5; 5 cutter.
- **Ordered actions:** 1 dribbles off 4's screen (0–1.5 s); 3 and 2 set a staggered double screen for 5, who cuts for 1's pass (1.5–3.5 s); else 4 down-screens 2 to the top for a three (3.5–5.0 s) [MA1].
- **Usual counters:** down screen for 2 as the second option [MA1].
- **Detection signature [HEURISTIC]:** box → Horns transition (two block players rise to the elbows ≤ 2 s); ball `SCR`; then, ≤ 2.0 s after the ball `SCR`, **guards** `STAGGER` for the **big**, who reaches r < 2.5 m. Roles come from the roster position/height table; fallback without it: the screeners are the two players who started in the corners and the cutter is the block player who did not set the ball screen.
- **Teams documented:** none at college level. NBA alias: Milwaukee Bucks (Del Harris) [MA1].
- **Sources:** [MA1].
- **Confidence:** medium.

### H14. Lynx

- **Name and aliases:** "Lynx" (Cheryl Reeve, Minnesota Lynx; Coach's Clipboard) [MA1].
- **Family:** F3.2 Horns → F5 → F6 → F5 → F8 weak-side pin.
- **Start alignment:** Horns template.
- **Roles:** 1 handler, then U-turn receiver; 5 ball screener twice; 3 DHO receiver and PnR handler; 4 weak-side pin screener and slipper; 2 pin receiver.
- **Ordered actions:** 1 dribbles left off 5 and hands off to 3 (0–2 s); 3 uses 5's ball screen (2–4 s); weak side 4 pins for 2 to the weak elbow; U-turn pass to 1, or pocket/lob to 4 slipping (4–6 s) [MA1].
- **Usual counters:** U-turn pass; 4 slip [MA1].
- **Detection signature [HEURISTIC]:** ball `SCR` by 5, then `DHO(1→3)`, then a second ball `SCR` by the same big on the DHO receiver ≤ 2 s; concurrent weak-side down `SCR`.
- **Teams documented:** none at college level; Minnesota Lynx (WNBA) [MA1].
- **Sources:** [MA1].
- **Confidence:** medium.

### H15. Michigan (Horns) [NAME COLLISION with X03 "Michigan" youth continuity]

- **Name and aliases:** "Michigan" (Coach's Clipboard Horns play; also a 3-out 2-in "Michigan" page) [MA1][MA13]. No coach credited.
- **Family:** F3.2 Horns → F8 big-for-big screen, cut-through.
- **Start alignment:** Horns template; 2 starts in a corner [MA1].
- **Roles:** 2 corner-to-wing receiver; 1 passer and cutter to the opposite corner; 4 screener for 5; 5 cutter to the ball-side block; 3 rotates to the point.
- **Ordered actions:** 2 cuts from the corner to the wing for 1's pass; 4 screens 5 on the ball side; 1 basket-cuts and exits to the opposite corner; 3 rotates to the point; 5 cuts off 4 to the ball-side block after 1 clears (0–4 s) [MA1][MA13].
- **Usual counters:** 5 back-screens 2 [MA1][MA13].
- **Detection signature [HEURISTIC]:** corner-to-wing catch; the passer cuts through to the far corner while a big-for-big `SCR` sends one big to the ball-side block ≥ 0.5 s after the cutter passes.
- **Teams documented:** none named (the name does not establish University of Michigan usage; unverified).
- **Sources:** [MA1], [MA13].
- **Confidence:** medium-high (sequence); team usage unverified.

### H16. Horns-3

- **Name and aliases:** "Horns-3" (Roy Rana, Ryerson; Coach's Clipboard) [MA1].
- **Family:** F3.2 Horns → F8 sequential staggers.
- **Start alignment:** bigs start **outside** the arc at ARC-HIGH (7.13, 75.4 / 104.6); 1 TOP; 2 and 3 CORNERS [MA1].
- **Roles:** 1 dribbler to the wing; 4 and 5 stagger screeners; 2 first stagger cutter; 3 second stagger cutter, then baseline-screen user.
- **Ordered actions:** 1 dribbles over 4 to the wing; 4 and 5 stagger for 2 to the top (0–3 s); else reset stagger for 3 (3–5 s); else 3 to the top, baseline screens for 1 to the far corner (5–8 s) [MA1].
- **Usual counters:** sequential staggers [MA1].
- **Detection signature [HEURISTIC]:** bigs at r ≥ 6.75 m, θ 70–110° at the snapshot; two `STAGGER` events by the same pair for two different cutters within 5 s.
- **Teams documented:** Ryerson (Canadian U Sports; not NCAA) [MA1].
- **Sources:** [MA1].
- **Confidence:** medium.

### H17. Horns-5

- **Name and aliases:** "Horns-5" (Coach's Clipboard; no coach credited) [MA1].
- **Family:** F3.2 Horns → F5 → F8 big-for-big back screen (Spain-like with a big).
- **Start alignment:** Horns template.
- **Roles:** 1 handler; 5 ball screener and lob cutter; 4 back screener; 3 kick-out receiver.
- **Ordered actions:** 1 dribbles left off 5; 4 screens 5 to the hoop (0–2.5 s); 1 drives and kicks to 3 [MA1].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** ball `SCR` by 5, then the **other** big sets a back `SCR` on 5 ≤ 1.5 s later; 5 reaches r < 1.5 m.
- **Teams documented:** none named.
- **Sources:** [MA1].
- **Confidence:** medium.

### H18. Horns Cross-Screen Hi-Lo

- **Name and aliases:** "Horns Cross-Screen Hi-Lo" (Coach's Clipboard) [MA1].
- **Family:** F3.2 Horns → F5 → F8 down and cross screens → F7 high-low.
- **Start alignment:** Horns template.
- **Roles:** 1 handler; 5 ball screener, down screener, cross screener, post target; 4 diver; 2 baseline runner; 3 top receiver and high-low passer.
- **Ordered actions:** 1 off 5's screen; 4 dives to the ball-side block; 2 runs the baseline to the far corner (0–2 s); 5 sprints to screen for 3 to the top; 1→3; 5 cross-screens 4; high-low 3→5 (2–6 s) [MA1].
- **Usual counters:** seal for the high-low [MA1].
- **Detection signature [HEURISTIC]:** the ball screener then sets two more screens (down for 3, cross for 4) within 4 s; `ENTRY` from r ≥ 6.75 m to the screener at r < 2.5 m.
- **Teams documented:** none named.
- **Sources:** [MA1].
- **Confidence:** medium.

### H19. Suns

- **Name and aliases:** "Suns" (Coach's Clipboard; credited to the Phoenix Suns) [MA1].
- **Family:** F3.2 Horns → F5 twist variant.
- **Start alignment:** Horns template.
- **Roles:** 1 handler; 4 first screener who goes to the wing; 5 second screener and diver; 2 lift shooter.
- **Ordered actions:** 1 off 4's screen; 4 to the left wing; 1 reverses over 5; 5 cuts to the hoop; 2 lifts to the wing; 1→2 for a three (0–5 s) [MA1].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** two ball `SCR` events on the same handler from opposite directions within 2.0 s (twist); the first screener reaches r ≥ 6.75 m, θ 12–60° or 120–168° (wing) ≤ 2.0 s after his screen instead of rolling; the second screener reaches r < 2 m ≤ 2.0 s after his screen; a corner player lifts to the wing and catches at r ≥ 6.75 m ≤ 2.0 s later.
- **Teams documented:** none at college level; NBA alias Phoenix Suns [MA1].
- **Sources:** [MA1].
- **Confidence:** medium.

### H20. Kansas Horns Flare (lob) [RICHER VARIANT of Horns Flare]

- **Name and aliases:** "Kansas Horns Flare" (Bill Self, Kansas; Coach's Clipboard) [MA1].
- **Family:** F3.2 Horns → F5 → F8 flare screen on the ball screener (STS lob).
- **Start alignment:** overloaded Horns: both wings on the right (CORNER 6.81, 3.4 and WING 7.50, 45.0, inferred), left side empty; 1 TOP; 4 and 5 ELBOWS [MA1].
- **Roles:** 1 handler and lob passer; 4 ball screener and lob cutter; 5 flare screener.
- **Ordered actions:** 4 ball-screens 1; 5 flare-screens 4, who cuts to the rim for a lob from 1 (0–3 s) [MA1].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** overloaded `ALIGN` (both non-big perimeter players with the same sign of x); the ball screener is screened by the other big and reaches r < 1.5 m (not out to the arc as in Horns Flare); `LOB`.
- **Teams documented:** Kansas (Self), season unverified [MA1].
- **Sources:** [MA1].
- **Confidence:** medium-high.

### H21. Carolina Horns Double Ball-Screen

- **Name and aliases:** "Carolina Horns Double Ball-Screen" (Hubert Davis, North Carolina; Coach's Clipboard) [MA1].
- **Family:** F3.2 Horns → F6 pistol DHO → F5 double ball screen.
- **Start alignment:** Horns template.
- **Roles:** 1 dribbler at 2, DHO giver, then corner; 2 DHO receiver and handler; 4 popper; 5 diver; 3 corner spacer.
- **Ordered actions:** 1 dribbles at 2 for a pistol DHO and slides to the corner (0–2 s); 4 and 5 double ball-screen 2; 5 dives, 4 pops (2–4.5 s) [MA1].
- **Usual counters:** kick to 3 in the corner [MA1].
- **Detection signature [HEURISTIC]:** `DHO` slot → wing; the DHO giver reaches θ ≤ 12° or ≥ 168° ≤ 2.0 s after the transfer; ≤ 2.0 s after the DHO a `DOUBLE` ball screen by both bigs on the receiver; ≤ 2.0 s after the handler passes the screen, one screener `ROLL`s and the other `POP`s.
- **Teams documented:** North Carolina (Hubert Davis), season unverified [MA1].
- **Sources:** [MA1].
- **Confidence:** high.

### H22. Illinois Horns Post-Up

- **Name and aliases:** "Illinois Horns Post-Up" (credited to Matt Bollant, Eastern Illinois women; Coach's Clipboard) [MA1]. The name does not establish Illinois men's usage.
- **Family:** F3.2 Horns → F7 wing post-up.
- **Start alignment:** Horns template; 4 catches at the arc [MA1].
- **Roles:** 1 passer, screen user to the left wing; 4 catcher at the arc and post feeder; 5 screener for 1; 3 wing who posts.
- **Ordered actions:** 1→4 at the arc; 5 screens 1 to the left wing; 3 cuts early to post and catches from 4; vs a front, seal and lob (0–4 s) [MA1].
- **Usual counters:** bounce pass vs a defender behind; lob vs a front [MA1].
- **Detection signature [HEURISTIC]:** a **wing** (not a big) reaches the block (r < 2.5 m) ≤ 2.5 s after `PASS(TOP→big)` and catches `ENTRY` from that big at r ≥ 6.75 m ≤ 2.0 s after arriving. Roles come from the roster position/height table; fallback: the wing is a player who was at FTX/WING at the `ALIGN` snapshot.
- **Teams documented:** Eastern Illinois women (Bollant), season unverified [MA1].
- **Sources:** [MA1].
- **Confidence:** medium.

### H23. Screen-Flare (Perkins)

- **Name and aliases:** "Screen-Flare" (Lason Perkins Horns offense; Coach's Clipboard) [MA2].
- **Family:** F3.2 Horns → F8 down screen, double screen, flare.
- **Start alignment:** Horns template.
- **Roles:** 1 handler using a double screen; 4 down screener for 2, then screener for 3; 5 double screener and flare screener; 2 shooter.
- **Ordered actions:** 1 dribbles right; 4 down-screens 2 to the top; 5 and 2 double-screen 1; 4 screens 3 to the left wing; 5 flare-screens 2 to the right wing for a skip (0–6 s) [MA2].
- **Usual counters:** 5 slips vs a switch [MA2].
- **Detection signature [HEURISTIC]:** the handler uses a `DOUBLE` of a big and a guard; ≤ 3.0 s later the big sets a flare `SCR` for that guard; ≤ 1.5 s after the flare contact a `PASS` that crosses x = 0 with |Δx| ≥ 6 m reaches him at r ≥ 6.75 m. Roles come from the roster table; fallback: the guard is the player who came off the preceding down `SCR` to the top.
- **Teams documented:** Cary Academy HS (Perkins); no college team [MA2].
- **Sources:** [MA2].
- **Confidence:** medium.

### H24. Flare PnR (Perkins)

- **Name and aliases:** "Flare" (Perkins Horns offense) [MA2]. Distinct from repo Horns Flare.
- **Family:** F3.2 Horns → F5 → F8 flare → F5 second ball screen.
- **Start alignment:** Horns template.
- **Roles:** 1 handler; 4 first ball screener who flares; 5 flare screener, then ball screener and roller; 2 rotates.
- **Ordered actions:** 4 screens 1 to the left wing; 5 screens 4, who flares right; 5 ball-screens 1 and rolls; 2 rotates to the left wing (0–5 s) [MA2].
- **Usual counters:** kick to 4 or 3 [MA2].
- **Detection signature [HEURISTIC]:** flare `SCR` on the first screener, then a second ball `SCR` by the flare screener on the same handler ≤ 2 s.
- **Teams documented:** Cary Academy HS (Perkins) [MA2].
- **Sources:** [MA2].
- **Confidence:** medium.

### H25. Barcelona

- **Name and aliases:** "Barcelona" (Perkins Horns offense) [MA2].
- **Family:** F3.2 Horns → F8 double stagger, skip → F5.
- **Start alignment:** Horns template.
- **Roles:** 1 handler and skip passer; 4 and 5 stagger screeners; 3 weak-corner receiver and PnR handler; 2 corner clear.
- **Ordered actions:** 1 dribbles right; 5 and 4 stagger down-screen for 3 to the left wing; skip; 2 clears to the right corner (0–3 s); 4 ball-screens 3, roll or pop (3–6 s) [MA2].
- **Usual counters:** the ball-screen counter [MA2].
- **Detection signature [HEURISTIC]:** both bigs leave the elbows to `STAGGER` down for the weak-corner player, who catches a `SKIP`; ball `SCR` on him ≤ 3 s.
- **Teams documented:** Cary Academy HS (Perkins) [MA2].
- **Sources:** [MA2].
- **Confidence:** medium.

### H26. Sonic

- **Name and aliases:** "Sonic" (Perkins Horns offense) [MA2].
- **Family:** F3.2 Horns → F6 → F8 two double screens.
- **Start alignment:** Horns template.
- **Roles:** 1 entry passer, cutter, DHO receiver; 4 catcher, DHO giver, final cutter; 5 and 3 double screeners twice; 2 wing receiver.
- **Ordered actions:** 1→4, 1 cuts to the left wing; 5 and 3 double-screen 2 to the right wing; 4 DHOs to 1; 1→2; 5 and 3 double-screen 4 to the rim for a layup (0–7 s) [MA2].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** two `DOUBLE` screens by the same pair (a big and a wing) within 5 s, the second for the big who started at the elbow.
- **Teams documented:** Cary Academy HS (Perkins) [MA2].
- **Sources:** [MA2].
- **Confidence:** medium.

### H27. Post-Switch / Post-Cross [Post-Switch = alias of repo MSU "EOQ Horns Set"; Post-Cross = RICHER VARIANT]

- **Name and aliases:** "Post-Switch", "Post-Cross" (Perkins Horns offense) [MA2]. **Post-Switch** is an alias of the repo MSU version, `offense_full.md` "EOQ Horns Set" [O89] (4 and 5 cross, each setting a ball screen for 1; the used screener rolls and the other pops; same detection: elbow bigs swap sides ≤ 1.5 s, then a ball screen). It is not a new action. **Post-Cross** (4 cross-screens 5, who loops into the ball screen) is the distinct variant kept here.
- **Family:** F3.2 Horns → F8 big-for-big cross → F5.
- **Start alignment:** Horns template.
- **Roles:** 4 and 5 exchange elbows; 1 handler.
- **Ordered actions:** 4 and 5 cross and swap elbows (Post-Switch); or 4 cross-screens 5, who loops into the ball screen (Post-Cross) (0–2.5 s) [MA2].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** Post-Switch (= repo EOQ Horns Set): bigs exchange elbows (sign of x swaps) ≤ 1.5 s before the first ball `SCR`. Post-Cross (distinct): one big sets a cross `SCR` on the other at r 3.5–6 m; the screened big's path turns > 90° (loop) and he sets the first ball `SCR` ≤ 2.0 s after the cross-screen contact.
- **Teams documented:** Cary Academy HS (Perkins) [MA2].
- **Sources:** [MA2].
- **Confidence:** medium.

### H28. Toledo Horns Zoom (fake DHO + screen-the-screener) [RICHER VARIANT of Horns Zoom]

- **Name and aliases:** Toledo Horns Zoom (Breakthrough) [MA69].
- **Family:** F3.2 Horns → F6 fake DHO, zoom DHO → F8 STS.
- **Start alignment:** Horns template.
- **Roles:** 1 entry passer, fake-DHO cutter; 4 catcher and dribbler, popper; 5 down screener; 3 zoom DHO receiver; 2 baseline cross screener.
- **Ordered actions:** 1 enters to 4 and cuts for a fake DHO; 5 down-screens 3 in the corner; 4 dribbles at 5 as 3 comes up for the zoom DHO; 2 cross-screens 5 from the far corner (STS); 1 slides to the ball-side corner; 4 pops [MA69].
- **Usual counters:** not given beyond the STS.
- **Detection signature [HEURISTIC]:** `FAKE_DHO`; then zoom (down `SCR` then `DHO` ≤ 1.5 s); then a baseline cross `SCR` (y < 1.5 m) on the original down screener.
- **Teams documented:** Toledo (clip dated 2023-04-24; season 2022-23 inferred) [MA69].
- **Sources:** [MA69].
- **Confidence:** medium-high.

### H29. Pitt Horns DHO with clear-out

- **Name and aliases:** Pitt Horns DHO clear-out (Breakthrough) [MA69].
- **Family:** F3.2 Horns → F5 → F6 zoom.
- **Start alignment:** Horns template.
- **Roles:** 1 handler; 5 ball screener who pops, catches and dribbles at the zoom; 4 down screener and popper; 3 zoom receiver; 2 corner clear.
- **Ordered actions:** 1 comes off a ball screen; screener 5 pops to the top and catches; 4 down-screens 3 in the corner while 5 dribbles at the screen (zoom); 2 clears the corner; 5 rim-runs, 4 pops, 1 slides to the corner [MA69].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** ball `SCR` → screener `POP` and catch ≤ 2.0 s after the screen → zoom (down `SCR` + `DHO` ≤ 1.5 s) ≤ 2.0 s after the catch; during the zoom the weak-corner player moves to the far side (sign of x flips) so only the zoom pair is on the ball side.
- **Teams documented:** Pitt (clip dated 2023-04-19; season 2022-23 inferred) [MA69].
- **Sources:** [MA69].
- **Confidence:** medium-high.

### H30. Georgia Tech Horns back cut (roll and replace)

- **Name and aliases:** Georgia Tech Horns back cut (Breakthrough) [MA78].
- **Family:** F3.2 Horns → F5 twist, short roll, replace → F8 backdoor.
- **Start alignment:** Horns template.
- **Roles:** 1 handler; two Horns screeners (one short-rolls, one replaces); corner back-door cutter.
- **Ordered actions:** 1 uses one Horns screen, screener rolls; second ball screen, 1 to the middle; short roll and the other big replaces; the corner player back-doors as the dribble nears the wing [MA78].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** Horns twist; short roll (roller stops at r 3–5 m); the corner player cuts from θ ≤ 12° to r < 1.5 m as the ball reaches the wing.
- **Teams documented:** Georgia Tech, season unverified [MA78].
- **Sources:** [MA78].
- **Confidence:** medium.

### H31. High-post exchange with PnR (Brazil)

- **Name and aliases:** high-post exchange with pick-and-roll (Breakthrough) [MA75]. International (FIBA) secondary alias.
- **Family:** F3.2 Horns-like → F8 big-to-big cross exchanges → F6 → F5.
- **Start alignment:** Horns-like: bigs high; wings drop to the baseline (spots inferred) [MA75].
- **Roles:** 4 and 5 exchange cross screeners; 1 handler and DHO receiver.
- **Ordered actions:** 4 cross-screens 5 to the arc; wings go to the baseline; 1→5; 1 takes a handoff from 5; 5 cross-screens 4, who ball-screens 1; roll [MA75].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** two big-to-big cross `SCR` events at y 4–7 m within 4 s around a `DHO`; then a ball `SCR` with `ROLL`.
- **Teams documented:** Brazil men's national team (August 2014, vs USA) [MA75]. No college team.
- **Sources:** [MA75].
- **Confidence:** medium.

---
## 2. 1-4 High family (F3.1), including 4-High / Iverson starts

**Template start** ("1-4 High template"): 1 at TOP (7.60, 90.0); 4 and 5 at the ELBOWS (4.57, 66.4 / 113.6); 2 and 3 on the wings at FTX (7.32, 34.9 / 145.1). Discriminator (`offense_full.md` §3.1): four players at y 4–6 m, none at y < 2 m.

### O01. 1-4 High Rub [MSU]

- **Name and aliases:** "Michigan State 1-4 High Rub".
- **Family:** F3.1 1-4 High → F8 curl, flare.
- **Start alignment:** 1-4 High template (page gives no spots).
- **Roles:** 4 screener, then wing receiver; 2 curler; 5 screener for 3, then flare screener for 1; 3 post-up player; 1 entry passer, flare shooter.
- **Ordered actions:**
  1. t0: 4 screens for 2 on the wing; 2 curls and, if not open, goes to the corner (0–3.5 s).
  2. 1 passes to 4 stepping out to the wing (1.5–3.0 s).
  3. 5 screens for 3 on the opposite wing; 3 posts up off 5's screen (rim cut unverified); 4 looks for 3 (3.0–5.0 s).
  4. If 3 is not open, 1 flares off 5's screen and 4 passes to 1 for a shot (5.0–7.0 s) [MA24].
- **Usual counters:** flare for 1 as the second option [MA24].
- **Detection signature [HEURISTIC]:** an elbow player sets `SCR` for the same-side wing, who curls (reaches r < 3.5 m within 2.0 s of the screen contact) and then reaches θ ≤ 12°, r ≥ 6.6 m within 4.0 s of the contact; the screener moves to r ≥ 6.75 m on the wing and catches from TOP; the opposite elbow sets `SCR` for the opposite wing, who moves to a post spot (r 1.5–3.5 m, ball side of the lane) and holds with speed < 0.5 m/s for ≥ 0.8 s (post-up; a rim cut is not sourced); within 3.0 s a flare `SCR` by that same player on 1, then `PASS(wing→1)` at r ≥ 6.75 m.
- **Teams documented:** **Michigan State**, published 2015-12-02 (season 2015-16 inferred) [MA24].
- **Related (repo):** `offense_full.md` "1-4 High Curl Double Flare" [O93] (MSU, 2016). Not a duplicate: O93 enters to 4 at the high post, 2 back-cuts, 1 screens for 5, then 3 comes off a 5+4 stagger; O01 starts with a curl into the corner, a wing entry to 4, a post-up for 3 and a flare for 1.
- **Sources:** [MA24].
- **Confidence:** high (steps); spots per template.

### O02. MSU 1-4 High Lob [MSU]

- **Name and aliases:** "MSU 1-4 High Lob".
- **Family:** F3.1 1-4 High → F8 back screen on the point guard's defender, lob.
- **Start alignment:** 1 Appling at TOP (7.60, 90.0); 4 Dawson at an ELBOW (4.57, 66.4); 5 Gauna at the other ELBOW (4.57, 113.6); 3 Valentine and 2 Harris on the wings at FTX (7.32, 34.9 / 145.1) [MA51]; wing sides unverified.
- **Roles:** 3 rub cutter; 1 passer, then lob cutter; 4 wing receiver and lob passer; 2 weak-side clear-out; 5 back screener on X1.
- **Ordered actions:**
  1. t0: 3 makes a rub cut to the corner (0–3.0 s).
  2. 1 passes to 4, who steps off the elbow to the wing; 2 cuts baseline to clear the weak-side help (2.0–3.5 s).
  3. 5 steps up and screens X1; 1 cuts to the rim and 4 throws the lob (3.5–5.0 s) [MA51].
- **Usual counters:** none listed.
- **Detection signature [HEURISTIC]:** a wing moves to the corner on a path passing within 1.2 m of an elbow player (rub) within 3.0 s; `PASS(TOP→elbow player)` received at r 6–7.5 m, θ 25–50°; weak-side wing moves along y < 1.5 m to the far corner; back `SCR` on 1 at r 4–6 m; 1 reaches r < 1.5 m within 1.2 s; `LOB`.
- **Teams documented:** **Michigan State 2013-14** (vs Kentucky, Champions Classic, Chicago) [MA51].
- **Sources:** [MA51].
- **Confidence:** high.

### O03. 1-4 Twist Lob [MSU]

- **Name and aliases:** "1-4 Twist Lob" (FastModel Play of the Day, 2012-02-17).
- **Family:** F3.1 1-4 High → F6 DHO → F8 pin-down for a big → big-to-big lob.
- **Start alignment:** 1 TOP (7.60, 90.0); 4 at the ELBOW (4.57, 66.4) (the page says "high post"); 5 at the other ELBOW (4.57, 113.6); 3 on the wing (7.32, 34.9), clears to the opposite CORNER (6.81, 176.6); 2 opposite wing (not mentioned on the page).
- **Roles:** 1 entry passer, DHO receiver; 4 hub, DHO giver, pin-down screener, lob finisher; 5 pin-down receiver at the top, driver, lob passer; 3 clear-out.
- **Ordered actions:**
  1. t0: 1 enters to 4 at the high post; 3 clears to the opposite corner (0–1.5 s).
  2. 1 follows the pass for a handoff from 4 toward the wing (1.0–2.5 s).
  3. 4 pins down for 5 to the top of the key; 1 passes to 5 (2.5–4.5 s).
  4. 5 drives hard and lobs to 4 rolling to the rim (4.5–6.5 s) [MA48].
- **Usual counters:** none listed.
- **Detection signature [HEURISTIC]:** `PASS(TOP→ELBOW)`; `DHO(elbow big→1)` within 2.0 s; the same big sets a down `SCR` for the other big, who ends at r 6.75–8 m, θ 80–100° and catches; that big `DRIVE`s and passes to the first big at r < 1.5 m within 2.5 s. Cue: a big is both screener and lob finisher, and the passer is the other big.
- **Teams documented:** **Michigan State 2011-12** (win over Wisconsin) [MA48].
- **Sources:** [MA48].
- **Confidence:** high.

### O04. 1-4 STS [MSU]

- **Name and aliases:** "Michigan State Spartans – 1-4 STS". The page calls it "a Tom Izzo staple over the last 15 years" [MA34].
- **Family:** F3.1 1-4 High → F8 screen-the-screener → F5 roll/replace.
- **Start alignment:** 1-4 High template [MA34].
- **Roles:** post A screens the wing defender, then pops back for the entry; wing guard curls to the corner; opposite guard cuts off 5's elbow screen; 5 moves to the top and reverses; point guard spaces.
- **Ordered actions:**
  1. t0: a post screens the wing defender; the guard comes off to the corner (0–2.0 s).
  2. The post steps back out for the entry pass (1.5–3.0 s).
  3. After the catch, the opposite guard cuts high or low off 5's elbow screen; the point guard spaces away (3.0–4.5 s).
  4. 5 moves to the top and quickly reverses to the wing (4.0–5.5 s).
  5. Screen-the-screener for a layup or a top-of-key shot (5.5–7.5 s) [MA34].
- **Usual counters:** if the guard does not shoot, the post re-screens into roll/replace; if no high-low, reverse and stagger away for a shooter [MA34].
- **Detection signature [HEURISTIC]:** `SCR(elbow big→wing)` with the wing ending at θ ≤ 12°; the screener moves back toward the ball to r 5–7 m and catches; the opposite wing cuts within 1.2 m of the other elbow big; 5 moves to r ≥ 6.75 m, θ 80–100° and makes a `REVERSAL` within 1.5 s of catching; then two `SCR` events where the first screener is screened ≤ 1.5 s after screening.
- **Teams documented:** **Michigan State**, published 2024-03-21; "staple over the last 15 years" (exact seasons unverified) [MA34].
- **Sources:** [MA34] (re-opened 2026-10-18; matches).
- **Confidence:** high.

### O05. Iverson Ram Reject Away [MSU]

- **Name and aliases:** "Iverson Ram Reject Away". Iverson cut and Ram are in the repo; this four-step chain is new.
- **Family:** F3.1 4-High / Iverson start → F5 ram, fake ball screen, reject → F8 screen away.
- **Start alignment (inferred):** 4-High: 1 TOP (7.60, 90.0); 4 and 5 at the ELBOWS (4.57, 66.4 / 113.6); 3 on a wing (7.32, 34.9); 2 opposite wing or low.
- **Roles:** 1 entry passer, weak-side exchanger; 3 Iverson cutter, handler, baseline driver; 2 cuts under; 4 screener for 3, ram screener, shooter (Joey Hauser); 5 fake ball screener, then away screener.
- **Ordered actions:**
  1. t0: 1 passes to 3; Iverson cut; 2 cuts under; 4 screens for 3 (0–2.5 s).
  2. 1 clears weak side and exchanges with 2 (2.0–3.5 s).
  3. 4 sets a ram screen for 5, who comes to ball-screen; 5 fakes the ball screen; 3 rejects and drives baseline (3.5–5.5 s).
  4. 5 screens away for 4, who comes behind 3; 3 hits 4 for the three (5.5–7.5 s) [MA40].
- **Usual counters:** none listed (the deception is built in) [MA40].
- **Detection signature [HEURISTIC]:** 4-High `ALIGN`; `CUT(Iverson)` at y 4–7 m past the elbow bigs; ram = off-ball `SCR(4→5)` followed ≤ 1.0 s by 5 moving to the handler; 5 within 1.5 m of the handler but the handler goes the other way (heading to the screener > 90°) toward θ ≤ 25° or ≥ 155°; then `SCR(5→4)` away from the ball and `PASS(3→4)` at r ≥ 6.75 m behind the drive.
- **Teams documented:** **Michigan State 2022-23** (Hauser; published 2023-09-25; season inferred) [MA40].
- **Sources:** [MA40].
- **Confidence:** high.

### O06. Forwards Out (Regular) [MSU]

- **Name and aliases:** "Forwards Out Regular" (MSU). The FastModel author compares the "Forwards Out" look to NBA Chin action with guards and forwards swapped [MA22]. Related: G05 Forwards Out (Princeton) and F08 UConn Forwards Out Zoom; whether MSU's set descends from the Princeton concept is unverified.
- **Family:** F3.1 1-4 High-like (forwards above the elbows) → F8 shallow cut, pin-down, chin back cut.
- **Start alignment (inferred from the step text; diagram unreadable):** 1 at TOP (7.60, 90.0) with the ball; 2 on the right WING (7.50, 45.0); 3 on the left WING (7.50, 135.0); 5 at the right ELBOW (4.57, 66.4); 4 at the left ELBOW (4.57, 113.6). Exact spots unverified.
- **Roles:** 1 entry passer, then shallow cutter; 2 receiver, then chin cutter; 3 reversal receiver; 4 pin-down screener; 5 chin (back) screener at the elbow.
- **Ordered actions:**
  1. t0: 1 passes to 2, then shallow-cuts to the corner (0–1.5 s).
  2. 4 pin-down screens for 3 for the reversal (1.0–3.0 s).
  3. 2 makes a chin cut off 5, with a "bump back" option for a three (3.0–5.0 s) [MA21].
- **Usual counters:** 2 bumps back off the chin screen for a three [MA21]; the Wide option (O07).
- **Detection signature [HEURISTIC]:** `ALIGN` with no player at r < 3.5 m and two bigs at r 4.3–5.5 m above the elbows; `PASS(TOP→wing)` then the passer moves from θ ≈ 90° to the ball-side corner at r 6.5–8 m within 2.0 s; a weak-side down `SCR` and a `REVERSAL` within 3.0 s; then a back `SCR` by the elbow big on the original wing receiver, who reaches r < 2.5 m within 1.5 s or steps back to r ≥ 6.75 m ("bump").
- **Teams documented:** **Michigan State 2014-15** (twice in the first half vs Georgia; Travis Trice open three) [MA21]. [MA21] gives no round; the MSU–Georgia game was the 2015 NCAA Tournament first round (round of 64), MSU won 70–63 [MC2].
- **Sources:** [MA21], [MA20].
- **Confidence:** medium (steps sourced; spots inferred).

### O07. Forwards Out (Wide) [MSU]

- **Name and aliases:** "Forwards Out Wide" (MSU).
- **Family:** F3.1 1-4 High-like → F8 wide pin-down → slip.
- **Start alignment:** as O06 (inferred; the page gives no spots).
- **Roles:** as O06; a forward sets the wide pin-down and is the slip man.
- **Ordered actions (page summary only):** a wide pin-down meant to put X5 in several help situations; in the clip X5 over-helped and the screener slipped to the rim for a dunk [MA22]. Exact order unverified.
- **Usual counters:** screener slip when the big defender helps [MA22].
- **Detection signature [HEURISTIC]:** O06 alignment; a down `SCR` at θ ≤ 25° or ≥ 155°, r 5.5–7.5 m (wide pin-down); if the screener's defender moves > 2 m toward the cutter, a `SLIP` by the screener to r < 2 m within 1.5 s.
- **Teams documented:** **Michigan State 2014-15** (early vs Virginia, NCAA round of 32) [MA22].
- **Sources:** [MA22].
- **Confidence:** low-medium (summary only; order unverified).

### O08. Bulldog (Gonzaga)

- **Name and aliases:** "Bulldog" (Mark Few, Gonzaga; Coach's Clipboard) [MA4].
- **Family:** F3.1 1-4 High → F8 UCLA cut → F5 side PnR continuity with high-low (F4.1).
- **Start alignment:** 1-4 High template.
- **Roles:** 1 passer, UCLA cutter; 5 UCLA screener, then ball screener and roller; 2 PnR handler; 4 top receiver, high-low passer, next ball screener; 3 cutter to the opposite corner.
- **Ordered actions:**
  1. t0: 1 passes to 2; 5 sets a UCLA screen and 1 cuts to the rim or the opposite corner (0–2.0 s).
  2. 5 sprints to ball-screen for 2 and rolls; 2 passes to 4 at the top; 3 cuts to the opposite corner; 4 looks high-low to 5 (2.0–5.0 s).
  3. Next pass to 1 on the left wing; 5 sprints to the top; 4 follows and ball-screens for 1, then dives; 1 passes to 5, who looks for 4 inside (5.0–9.0 s).
  4. Repeat side to side [MA4].
- **Usual counters:** high-low after every roll [MA4].
- **Detection signature [HEURISTIC]:** `PASS(TOP→wing)`; `CUT(UCLA)` by 1 past the ball-side elbow big (1 to r < 2 m within 1.5 s); the same big sets a ball `SCR` on the wing ≤ 2.0 s later with `ROLL`; `PASS(wing→top big)`; pass from the top big to the roller at r < 2.5 m. Continuity: the screener/roller role alternates between the bigs on successive sides (≥ 2 cycles).
- **Teams documented:** Gonzaga (Few), season unverified [MA4].
- **Sources:** [MA4].
- **Confidence:** medium-high.

### O09. Georgetown / Hoyas / Hoyas-21

- **Name and aliases:** "Georgetown", "Hoyas", "Hoyas-21" (Coach's Clipboard 1-4 plays) [MA4]. No coach credited; three related plays in one block.
- **Family:** F3.1 1-4 High → F8 wing low-cross, back screen, flex → F7.
- **Start alignment:** 1-4 High template.
- **Roles (Georgetown):** 2 and 3 cross low; ball-side high post drops to the block; 4 flashes high; 3 back-screens 1; 1 skip-pass shooter; 5 short corner.
- **Ordered actions:**
  - Georgetown: t0 2 and 3 cut low and cross; 1 passes to either side (0–2.0 s); ball-side high post drops to the block for an inside pass, or 2 shoots (2.0–3.5 s); 4 flashes to the ball-side high post while 3 back-screens 1; 5 slides to the short corner (3.5–5.0 s); 1 comes off the back screen for a skip pass from 4, or 3 slips up the lane (5.0–6.5 s). Back option: wings fake the low cut and return [MA4].
  - Hoyas: 4 drops and back-screens 2, then 3 (both cut low; 3 crosses to the far wing); 4 cuts to the elbow and catches from 3; 5 drops and flex-screens 2; 1 back-screens 3 [MA4].
  - Hoyas-21: as Hoyas, but instead of the flex cut 2 back-screens 1 for a three; 5 cuts through the paint [MA4].
- **Usual counters:** slip by the back screener; fake low cut [MA4].
- **Detection signature [HEURISTIC]:** both wings move from FTX to y < 1.5 m and their paths cross x = 0 within 2.0 s; an elbow big drops to r < 2.5 m; then a back `SCR` on 1 at r 5–7 m with 1 exiting to the weak wing for a `PASS` that crosses x = 0 with |Δx| ≥ 6 m.
- **Teams documented:** none confirmed ("Georgetown" is a name only; unverified as Georgetown usage).
- **Sources:** [MA4].
- **Confidence:** medium.

### O10. Auriemma Elbow Series (Elbow Strong / Middle / Weak)

- **Name and aliases:** "Elbow Strong", "Elbow Middle", "Elbow Weak" (Geno Auriemma, UConn women; Coach's Clipboard) [MA4]. Distinct from Gonzaga "Elbow" (double pin-downs, repo), MSU "Elbow Away" (E01/E02), and the Spurs "Elbow Series" that Motion Strong flows into [MA15] (whether these match is unverified).
- **Family:** F3.1 1-4 High → F3.4 elbow entries → F8 / F6.
- **Start alignment:** 1-4 High template; 4 receives at the ELBOW (4.57, 66.4); 5 at the opposite elbow or block.
- **Roles:** 1 passer and cutter; 4 elbow hub; 2 and 3 wings; 5 screener / post.
- **Ordered actions:**
  - Strong: t0 1→4 at the elbow; 1 screens for 2, who cuts to the rim; else 4 and 1 DHO, three-man game with 2; 5 and 3 spot up (0–5 s).
  - Middle: 1→4; 1 cuts through the middle and flex-screens 3; 5 down-screens 1 to the arc; or 1 feeds 5 posting (0–6 s).
  - Weak: 1→4; 3 drops; 5 sets two screens for 1; 1 uses the first and screens for 3 (inside cut); 1 comes off 5's second screen for a shot or 5 posts; if switched, 5 slips (0–6 s) [MA4].
- **Usual counters:** slip on a switched second screen (Weak) [MA4].
- **Detection signature [HEURISTIC]:** `PASS(TOP→ELBOW)` (receiver at r 4–5 m, θ 60–75° or 105–120°) within 3 s of the snapshot. Strong = the passer screens the **same-side** wing, who reaches r < 2 m, or `DHO(4→1)` within 2 s. Middle = the passer cuts through the nail area to the weak block and sets a flex `SCR`. Weak = the passer goes weak side, uses a screen, screens, then uses a second screen from the same big.
- **Teams documented:** UConn women (Auriemma), seasons unverified [MA4].
- **Sources:** [MA4], [MA15].
- **Confidence:** medium-high.

### O11. Lobo (1-4 back-screen continuity)

- **Name and aliases:** "Lobo" (Coach's Clipboard; no coach credited) [MA4].
- **Family:** F3.1 1-4 High → F4.1 continuity (back screen on each wing pass).
- **Start alignment:** 1-4 High template.
- **Roles:** 1 passer and lob cutter; 2 wing receiver and lob passer; 4 back screener, step-out receiver; 5 ball-side post; 3 down and cross screener.
- **Ordered actions:** t0 1→2; 5 slides to the ball-side post; 4 back-screens 1 for a lob from 2 (0–2.5 s); else 2→4 stepping out; 3 down-screens 1; 4→1 as 3 cross-screens 5; 4 down-screens 3 or screens away for 2; on the next pass 5 back-screens 1 for a basket cut; the pattern repeats [MA4].
- **Usual counters:** back cut on every wing catch [MA4].
- **Detection signature [HEURISTIC]:** ≥ 2 back `SCR` events on the player who just passed to the wing, each followed by a cut to r < 1.5 m; interleaved down and cross screens; no ball screens.
- **Teams documented:** none named.
- **Sources:** [MA4].
- **Confidence:** medium.

### O12. Illini (Lou Henson 1-4 shuffle continuity)

- **Name and aliases:** "Illini" (Lou Henson, Illinois; Coach's Clipboard) [MA4].
- **Family:** F3.1 1-4 High → F4.1 back screen, shuffle cut, screen-the-screener.
- **Start alignment:** 1-4 High template.
- **Roles:** 1 dribbler, back-screen cutter, back screener for 4; 4 step-out receiver, shuffle cutter; 5 back screener, step-out receiver, STS screener; 2 wing receiver.
- **Ordered actions:** t0 1 dribbles right and passes to 4 stepping beyond the arc; 5 back-screens 1 to the rim; 5 steps out and catches from 4; 5→2 as 1 back-screens 4; 4 shuffle-cuts for a layup; 5 screens the screener (1) to the top; if not open, 2→1 and 4 returns to the elbow (back to 1-4); repeat to the left [MA4].
- **Usual counters:** run to the other side on the second cycle [MA4].
- **Detection signature [HEURISTIC]:** elbow big steps out to r ≥ 6.75 m and catches; back `SCR` by the other elbow big on the passer (to r < 2 m); that screener steps out and catches; a second back `SCR` on the first elbow big by the original point guard; STS ≤ 1.5 s later; re-`ALIGN` to 1-4 High after about 8–10 s.
- **Teams documented:** Illinois (Lou Henson era), seasons unverified [MA4].
- **Sources:** [MA4].
- **Confidence:** medium.

### O13. Aggie (Steve Forbes)

- **Name and aliases:** "Aggie" (Steve Forbes; Coach's Clipboard) [MA4]. School and seasons not given on the page (unverified).
- **Family:** F3.1 1-4 High → F8 cross and down screens → F6 elbow DHO → F7 high-low.
- **Start alignment:** 1-4 High template.
- **Roles:** 1 passer, corner cutter, elbow DHO receiver; 2 wing receiver, down screener; 4 cross screener, top catcher, dribbler and DHO giver; 5 cross-screen user, high-low target; 3 decoy.
- **Ordered actions:** t0 1→2 and 1 cuts to the ball-side corner; 4 cross-screens 5 to the right block; 4 pops to the top and catches from 2; 4 fakes to 3; 5 ducks under for the high-low; else 4 dribbles to the right elbow while 2 down-screens 1; 1 comes to the elbow for a DHO from 4; 4 cuts to the block; 1 shoots or hits 5 high-low; else 1→2, 1 to the left corner, 5 to the top, high-low for 4 [MA4].
- **Usual counters:** repeated high-low [MA4].
- **Detection signature [HEURISTIC]:** passer to the ball-side corner; cross `SCR` between the two bigs at y < 2 m; a big pops to r ≥ 6.75 m, θ 80–100° and catches; a `DHO` at the elbow (r 4–5 m) within 4 s; ≥ 2 big-to-big passes from r > 4 m to r < 2.5 m.
- **Teams documented:** none named beyond the coach.
- **Sources:** [MA4].
- **Confidence:** medium.

### O14. Zip-Loop-Hammer

- **Name and aliases:** "Zip-Loop-Hammer" (Josh Gamblin, per the source video; Coach's Clipboard) [MA4].
- **Family:** F3.1 1-4 High → F8 shallow/zip, Iverson → F5 cross-screen ram into reject → F8 hammer/flare.
- **Start alignment:** 1-4 High template.
- **Roles:** 1 handler, Iverson cutter, rejecting driver; 2 shallow cutter, return passer, flare user; 4 and 5 screeners (4 cross-screens 5 into a ram); 3 cut-under, short corner, hammer screener.
- **Ordered actions:** 1 dribbles left as 2 shallow-cuts around 5 to the top and gets the return pass; 5 and 4 screen for 1, who Iverson-cuts to the right wing; 3 cuts under to the left wing; 2→1; 4 cross-screens 5, who ball-screens 1; 3 to the short corner; 1 rejects and drives; 3 flare-screens 4 to the weak corner (hammer); 1 finishes or kicks to 4; 5 flare-screens 2 for a pass back [MA4].
- **Usual counters:** short-corner slip by 3 [MA4].
- **Detection signature [HEURISTIC]:** `CUT(shallow)` and `CUT(Iverson)` within 3 s; big-to-big cross `SCR` followed ≤ 1.0 s by a ball `SCR` (ram); handler rejects toward θ ≤ 25° or ≥ 155°; simultaneous weak-side flare `SCR` toward θ ≤ 12° (hammer, `offense_full.md` 8.1).
- **Teams documented:** none named.
- **Sources:** [MA4].
- **Confidence:** medium.

### O15. 4-Up (1-4 elbow get-and-roll)

- **Name and aliases:** "4-Up" (Coach's Clipboard) [MA4]. Close to repo "Horns Elbow Get" but from 1-4, with the big rolling.
- **Family:** F3.1 1-4 High → F6 elbow DHO → roll.
- **Start alignment:** 1-4 High template.
- **Roles:** 1 passer and DHO receiver; 4 elbow hub, DHO giver, roller; 5 pops to the weak wing; 2 slides to the corner; 3 safety.
- **Ordered actions:** 1→4 at the left elbow; 2 slides to the corner; 5 pops to the weak wing; 1 cuts around 4 for a DHO and drives; 4 rolls; 3 stays as the safety. If switched, 4 keeps and drives [MA4].
- **Usual counters:** 4 keeps vs a switch [MA4].
- **Detection signature [HEURISTIC]:** `PASS(TOP→ELBOW)`; the other elbow big `POP`s; the passer runs around the receiver within 1.0 m and gets `DHO` within 2.0 s; the giver `ROLL`s.
- **Teams documented:** none named.
- **Sources:** [MA4].
- **Confidence:** medium.

### O16. Alabama (1-4 shallow-clear PnR)

- **Name and aliases:** "Alabama" (Coach's Clipboard; no coach credited; not linked to Nate Oats on the page) [MA4].
- **Family:** F3.1 1-4 High → F8 shallow → F5 empty-side PnR.
- **Start alignment:** 1-4 High template.
- **Roles:** 3 shallow cutter, then safety at the top; 2 corner clear; 5 ball screener; 1 handler.
- **Ordered actions:** 3 shallow-cuts to the right wing; 2 slides to the corner, clearing the left side; 5 and 1 run PnR; 3 to the top as the safety [MA4].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** `CUT(shallow)` plus a same-side clear so that one side has no offensive player at r > 5 m; ball `SCR` on the empty side within 2 s.
- **Teams documented:** none confirmed (the name does not establish Alabama usage).
- **Sources:** [MA4].
- **Confidence:** medium-low.

### O17. 1-4 Up / 1-4 Down (Steege zoom)

- **Name and aliases:** "1-4 Up", "1-4 Down" (Nate Steege's Zoom offense; Breakthrough) [MA68].
- **Family:** F3.1 1-4 High → F8 back screen for a big → F6 zoom (down screen into DHO).
- **Start alignment:** 1-4 High template; 5 catches at an ELBOW inside the arc; for Down, the wings drop lower (spots unverified) [MA68].
- **Roles:** 1 entry passer, flare to the wing; 5 elbow hub and DHO giver, roll or pop; 2 back screener for 4, then DHO receiver; 4 back-screen cutter, then pop to the far wing; 3 to the corner.
- **Ordered actions:** Up: 1 enters to 5 at the elbow and flares to the right wing; 2 cuts behind 4 to back-screen; 4 cuts to the rim (first look); else 2 sprints into a DHO with 5; 5 rolls or pops; 4 pops to the far wing; 3 to the corner; 1 fills behind. Down: same entry; 4 down-screens 2 into the zoom DHO with 5; 2 attacks, 5 rolls [MA68].
- **Usual counters:** 5 keeps and attacks if the DHO is anticipated [MA68].
- **Detection signature [HEURISTIC]:** elbow pass (receiver r 4–5 m); passer flares; Up = a guard back-screens a big (cutter to r < 1.5 m), then sprints into `DHO` with the elbow big ≤ 2.0 s; Down = down `SCR` then `DHO` ≤ 1.5 s.
- **Teams documented:** high school (Steege) [MA68]; no college team.
- **Sources:** [MA68].
- **Confidence:** medium-high.

### O18. X (Schuring) — high-post scissors into flex, STS and double

- **Name and aliases:** "X" play (Tim Schuring; Breakthrough) [MA73]; "41 X" on the Breakthrough index [MA66].
- **Family:** F3.1 1-4 High / high-post entry → F8 scissors cut, flex, STS, double screen → flows to 5-out or 4-out 1-in.
- **Start alignment (inferred):** 1 TOP (7.60, 90.0); 4 at the right ELBOW (4.57, 66.4) receiving (inferred); 5 at the HIGH POST (4.39, 78.2); 3 on a wing (7.32, 34.9); 2 opposite wing (7.32, 145.1).
- **Roles:** 1 passer and scissors cutter, then flex screener and STS user; 4 receiver and scissors cutter; 5 high-post screener, clear-out, reverser, down screener; 3 V/L cutter, then flex cutter; 2 double-screen user.
- **Ordered actions:** 1→4; 3 V/L-cuts and catches; 4 and 1 both cut off 5 at the high post making an X; 1 stops at the block; 5 clears to the far corner, then steps out and catches; 5 reverses to 2; 3 flex-cuts off 1; 5 down-screens 1 (STS) for a top three; else 1→5 and 2 comes off a double screen by 3 and 4. Flow into 5-out or 4-out 1-in ball screens [MA73].
- **Usual counters:** the flow options [MA73].
- **Detection signature [HEURISTIC]:** two passers/cutters run paths that cross within 1.5 m of a stationary high post within 1.0 s of each other (scissors); then a flex `CUT` and an STS within 3 s; then a `DOUBLE`.
- **Teams documented:** none at college level named.
- **Sources:** [MA73], [MA66].
- **Confidence:** medium.

---
## 3. 1-4 Low family (F3.1) [RICHER VARIANTS of repo "1-4 Low" (iso start only)]

**Template start** ("1-4 Low template"): 1 at TOP (7.60, 90.0) or DEEP (9.80, 90.0); 2 and 3 in the CORNERS (6.81, 3.4 / 176.6); 4 and 5 on the BLOCKS (2.04, 26.2 / 153.8) [MA76]. Alias "1-4 flat" (HoopStudent) [MB15]. Discriminator: four players at y < 1.5 m. No MSU usage found for any item in this section.

### L01. 1-4 Double-Cross / Cross (1-4 Low)

- **Name and aliases:** "1-4 Double-Cross" (Coach's Clipboard) [MA5]; "Cross" (Breakthrough 1-4 Low) [MA76]. Merged: both describe the corner players crossing along the baseline past the posts. Different from Box Cross (repo) and R03 Cross (3-out 2-in).
- **Family:** F3.1 1-4 Low → F8 baseline cross screens → F7 high-low.
- **Start alignment:** 1-4 Low template.
- **Roles:** 2 and 3 baseline cross cutters; 4 and 5 baseline screeners, then flash / post; 1 handler.
- **Ordered actions:**
  - Coach's Clipboard: t0 2 and 3 run the baseline and cross to the opposite corner/wing (0–2.0 s); 1 looks for a corner three; else 1 dribbles right, 5 flashes to the FT line and catches, 4 posts for the high-low (2.0–5.0 s) [MA5].
  - Breakthrough: perimeter players cross through baseline screens by the posts (each post screens for the wings); posts open to the ball [MA76].
- **Usual counters:** short-corner slide by the post on penetration [MA76]; high-low [MA5].
- **Detection signature [HEURISTIC]:** 1-4 Low `ALIGN`; both corner players' paths cross x = 0 at y < 1.5 m within 2.0 s, each passing within 1.2 m of a block player; optional flash by a block player to the NAIL (4.19, 90.0) with a catch.
- **Teams documented:** none named.
- **Sources:** [MA5], [MA76].
- **Confidence:** medium-high.

### L02. 1-4 Scissors (1-4 Low)

- **Name and aliases:** "1-4 Scissors" (Coach's Clipboard) [MA5].
- **Family:** F3.1 1-4 Low → F6 scissors handoffs → F7 high-low.
- **Start alignment:** 1-4 Low template.
- **Roles:** 4 flash catcher and handoff hub; 2 and 1 scissors cutters; 5 high-low target; corners.
- **Ordered actions:** t0 4 flashes high and catches (0–1.5 s); 2, then 1, cut off 4 (scissors) for handoffs (1.5–4.0 s); high-low to 5 or kick to the corners (4.0–6.0 s) [MA5].
- **Usual counters:** high-low or corner kick [MA5].
- **Detection signature [HEURISTIC]:** a block player flashes to the NAIL / HIGH POST (r 4.2–4.6 m, θ 78–102°) and catches; two cutters pass within 1.0 m of him within 2.5 s (with or without `DHO`).
- **Teams documented:** none named.
- **Sources:** [MA5].
- **Confidence:** medium-high.

### L03. Pinball / 1-4 Low Base (drive and kick)

- **Name and aliases:** "Pinball" (Coach's Clipboard) [MA5]; "1-4 Low Base" (Breakthrough) [MA76]. Merged.
- **Family:** F3.1 1-4 Low → F10 drive-and-kick / F9 isolation.
- **Start alignment:** 1-4 Low template.
- **Roles:** 1 driver; corners as kick-out targets; posts as dump-off targets.
- **Ordered actions:** t0 1 drives (0–2.0 s); kicks to a corner or dumps to a post depending on which low defender helps (1.5–3.5 s) [MA5][MA76].
- **Usual counters:** the post slides to the short corner on penetration [MA76].
- **Detection signature [HEURISTIC]:** 1-4 Low `ALIGN`; `DRIVE` by 1 with no `SCR` within 3 s of the snapshot; first pass after the drive goes to r ≥ 6.6 m at θ ≤ 12° / ≥ 168° (kick) or to r < 3 m (dump).
- **Teams documented:** none named.
- **Sources:** [MA5], [MA76].
- **Confidence:** medium-high.

### L04. Spurs (1-4 Low)

- **Name and aliases:** "Spurs" (Coach's Clipboard 1-4 low) [MA5]. NBA secondary alias; not the same as Spurs Motion Strong/Weak (S01/S02).
- **Family:** F3.1 1-4 Low → F8 big-for-big screen → F7 post feed.
- **Start alignment:** 1-4 Low template.
- **Roles:** 2 splits to the arc and catches; 4 screener for 5; 5 post target ("Duncan feed").
- **Ordered actions:** t0 2 splits to the arc and catches (0–1.5 s); 4 screens for 5 to the ball-side post (1.5–3.0 s); 2 feeds 5 (3.0–4.0 s) [MA5].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** a corner player moves up to the wing (θ ≤ 12° → 25–50°) and catches; a big-for-big `SCR` at y < 2 m sends one big to the ball-side block; `POST_ENTRY` within 2.0 s.
- **Teams documented:** none at college level; San Antonio Spurs (NBA) per the page name [MA5].
- **Sources:** [MA5].
- **Confidence:** medium.

### L05. 1-4 Low High (high ball screen at varied angles)

- **Name and aliases:** "1-4 Low High" (Breakthrough) [MA76].
- **Family:** F3.1 1-4 Low → F5 high ball screen.
- **Start alignment:** 1-4 Low template.
- **Roles:** a post rises to set a high ball screen for 1; corners and the other post space.
- **Ordered actions:** a post sets a high ball screen for 1 at varied angles (0–3 s) [MA76]. Further order not given.
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** 1-4 Low `ALIGN`; a block player moves from r < 2.5 m to r 6.5–8.5 m and sets a ball `SCR` within 3 s of the snapshot (sprint-up shape, `set_taxonomy.md` §1.5).
- **Teams documented:** none named.
- **Sources:** [MA76].
- **Confidence:** low-medium (thin description).

### L06. Loop behind (1-4 Low re-screen into loop)

- **Name and aliases:** "loop action", "loop behind", "loop series" (HoopStudent) [MA18][MB12]. Merged from both notes (the same HoopStudent page). Related: H12 Horns Loop, S03 Transition loop.
- **Family:** F3.1 1-4 Low → F5 re-screen → F8 loop cut.
- **Start alignment:** HoopStudent 1-4 low: 1 at TOP (7.60, 90.0); 2 and 4 in the CORNERS (6.81, 3.4 / 176.6); 3 and 5 on the BLOCKS (2.04, 26.2 / 153.8) [MB12][MB15].
- **Roles:** 1 handler; 5 ball screener and re-screener; 2 loop cutter; 3 fills the top; 4 fills the corner.
- **Ordered actions:**
  1. t0: 5 sets a ball screen at the top; 1 uses it toward one side (0–2 s).
  2. 5 turns and re-screens; 1 dribbles toward FTX, inside the arc, on the opposite side (2–4 s).
  3. 3 fills the top, 4 the strong-side corner, 5 the weak-side low post.
  4. As 1 dribbles, 2 cuts up from the corner to the strong-side wing and loops behind 1, for a three or to keep the ball while 1 fills the corner (3–5 s).
  5. Part 2: post look to 5; else a pass to 3 at the top, who dribbles to the wing and triggers a corner-to-top loop on the other side, with 5 cross-screening for 4 (5–9 s) [MB12][MA18].
- **Usual counters:** a second loop on the opposite side [MB12][MA18].
- **Detection signature [HEURISTIC]:** two ball `SCR` events by the same screener for the same handler from opposite directions within 2.5 s; then the handler dribbles toward FTX (ending r 5.5–7 m, θ 25–45°) while a teammate starting in the same-side corner rises (θ up by 25–45°, r 6.5–8 m) and passes **behind** the dribbler (larger r at the crossing) within 1.5 s of the dribbler reaching the wing.
- **Teams documented:** none named (HoopStudent refers to a Cheryl Reeve resource that was not opened).
- **Sources:** [MB12], [MA18], [MB15].
- **Confidence:** medium.

---

## 4. 4-out 1-in family (F3.1 / F4.2)

**Template start** ("4-out 1-in template"): two players in the SLOTS (7.62, 66.8 / 113.2); two on the wings at FTX (7.32, 34.9 / 145.1) or WING (7.50, 45.0 / 135.0); one inside at a BLOCK (2.04, 26.2 / 153.8) or DUNKER (2.72, 6.3 / 173.7). Discriminator: exactly one player at r < 3.5 m (`offense_full.md` §3.1). No MSU usage found for any item in this section.

### F01. Heat (Steve Fisher, San Diego State)

- **Name and aliases:** "Heat" (Coach's Clipboard 4-out quick hitters; credited to Steve Fisher, San Diego State) [MA8].
- **Family:** F3 4-out 1-in → F8 UCLA cut → F5 wing ball screen → F8 back screen under, stagger for the post → F7 high-low.
- **Start alignment:** "4-out with O5 low" [MA8]. Sides unverified: the [MA8] text gives no left/right or slot/wing spots (re-opened by the fixer, 2026-10-18 (UTC); diagrams unreadable). Working assignment (inferred): 1 in the right SLOT (7.62, 66.8); 2 on the right WING (7.50, 45.0); 3 and 4 on the left side (WING 7.50, 135.0 / CORNER 6.81, 176.6); 5 low on the right BLOCK (2.04, 26.2), so the first pass is a same-side slot → wing pass.
- **Roles:** 1 passer, UCLA cutter, back screener, shooter; 2 wing receiver and PnR handler; 5 UCLA screener, ball screener, post target; 3 back-screen cutter, stagger screener; 4 stagger screener, elbow flash.
- **Ordered actions:** 1→2; 5 comes to the ball-side elbow for a UCLA screen; 1 cuts (0–2 s); 5 ball-screens 2; 2 to the top; 1 back-screens 3 under; 1 to the arc for a three (2–6 s); 3 and 4 stagger for 5 to the block; 4 flashes to the elbow for the high-low (6–10 s) [MA8].
- **Usual counters:** multiple built-in options; high-low [MA8].
- **Detection signature [HEURISTIC]:** `PASS(slot→wing)` + `CUT(UCLA)` by the passer past a post who **came up** from the block; that post's next action is a ball `SCR` on the wing ≤ 2 s; later a `STAGGER` for the post to the block.
- **Teams documented:** San Diego State (Steve Fisher), season unverified [MA8].
- **Sources:** [MA8].
- **Confidence:** medium-high.

### F02. "45" Hi-Lo / ball-screen option

- **Name and aliases:** "45" Hi-Lo (Coach's Clipboard 4-out quick hitters) [MA8]. "45" here is a play name, not the 45° wing.
- **Family:** F2 secondary → F3 4-out 1-in → F7 high-low → F5 pass-and-follow ball screen.
- **Start alignment:** out of transition: 1 on the right side; 4 fills the middle at TOP (7.60, 90.0); 5 posts (BLOCK); others on the wings (spots inferred) [MA8].
- **Roles:** 4 top catcher, high-low passer, ball screener and popper; 5 post; 1 and 2 exchange via a down screen; 3 receiver.
- **Ordered actions:** 4 catches at the top and looks high-low; 1 down-screens 2 (exchange); else 4→3, follows, ball-screens and pops; repeat to 2 [MA8].
- **Usual counters:** 4 dribble attack vs pressure [MA8].
- **Detection signature [HEURISTIC]:** a big catches at TOP ≤ 8 s into the possession; then a pass-and-follow ball `SCR` by that big with `POP`.
- **Teams documented:** none named.
- **Sources:** [MA8].
- **Confidence:** medium.

### F03. Gator (Michael Peck) [NAME COLLISION: repo "Gator" = drag reject-and-pass read]

- **Name and aliases:** "Gator" (Coach's Clipboard 4-out quick hitters; credited to Michael Peck, Findlay Prep HS) [MA8]. Store as `Gator_4out` to avoid the collision.
- **Family:** F3 4-out 1-in → F8 shuffle, stagger, double.
- **Start alignment:** 4-out 1-in template [MA8].
- **Roles:** 1 passer, corner cutter, stagger user; 2 wing receiver, shuffle cutter, double-screen user; 4 reversal passer and screener; 5 post, shuffle screener, stagger and double screener; 3 reversal receiver.
- **Ordered actions:** 1→2 and cuts to the right corner; 2 looks to 5 or drives; reversal via 4 to 3; 5 shuffle-screens 2; 5 and 4 stagger down for 1 (curl or pop); 5 and 4 double for 2 (0–9 s) [MA8].
- **Usual counters:** curl vs a trailing defender, pop vs a defender going under [MA8].
- **Detection signature [HEURISTIC]:** passer to the ball-side corner; `REVERSAL`; shuffle `CUT` (≤ 2.0 s after the `REVERSAL`) past a post standing at |x| 2.0–2.8 m; then `STAGGER` and then `DOUBLE` by the same two bigs.
- **Teams documented:** Findlay Prep (HS); no college team [MA8].
- **Sources:** [MA8].
- **Confidence:** medium.

### F04. High (4-out high-post option)

- **Name and aliases:** "High" (Coach's Clipboard 4-out quick hitters) [MA8].
- **Family:** F3 4-out 1-in → F8 flash, backdoor → F6 weave DHO → F5.
- **Start alignment:** 4-out 1-in; 5 flashes from low to the HIGH POST (4.39, 78.2) [MA8].
- **Roles:** 5 high-post catcher, DHO giver, dribbler into the weave; 2 backdoor cutter; 4 down screener; 3 exchange; 1 handoff cutter.
- **Ordered actions:** 5 catches at the high post; 2 backdoors; 4 down-screens 3 (exchange); 1 cuts around 5 for a handoff; 5 dribbles at 3 for a weave DHO into PnR; 4 down-screens 2 (0–8 s) [MA8].
- **Usual counters:** backdoor first [MA8].
- **Detection signature [HEURISTIC]:** flash `CUT` low → NAIL area with a catch; a wing `CUT(backdoor)` to r < 2 m within 1.5 s of that catch; later a `DHO` from the post.
- **Teams documented:** none named.
- **Sources:** [MA8].
- **Confidence:** medium.

### F05. "2" Baseline Runner

- **Name and aliases:** "2" Baseline Runner (Coach's Clipboard 4-out quick hitters) [MA8]. The play abandons 4-out for a two-guard front with two blocks.
- **Family:** F3 4-out → two-guard front with two blocks → F8 baseline runner.
- **Start alignment:** two guards in the SLOTS (7.62, 66.8 / 113.2); 4 and 5 on the BLOCKS (2.04, 26.2 / 153.8); 2 UNDER the basket (0.95, 18.4) (spots inferred from the description) [MA8].
- **Roles:** 2 baseline runner; 4 and 5 baseline screeners who shape up for the high-low; guards pass.
- **Ordered actions:** 2 runs the baseline off 5 and 4 and comes out either side; the screener shapes up for the high-low; shallow cut if denied (0–6 s) [MA8].
- **Usual counters:** high-low to the screener [MA8].
- **Detection signature [HEURISTIC]:** a shooter starts at r < 1.2 m and exits along y < 1.5 m to a corner or wing past a block screener (`SCR`); catch at r ≥ 6.6 m.
- **Teams documented:** none named.
- **Sources:** [MA8].
- **Confidence:** medium.

### F06. Topside / Counter / Flash / Jet-Back (4-out high-post motion)

- **Name and aliases:** "Topside", "Counter", "Flash", "Jet-Back" (Coach's Clipboard 4-out high motion plays; Jet-Back credited to Jesse Shaw, *The Jet 4-Out High Post Offense*) [MA12]. Four named plays in one block; the page did not give separate text for "Counter" beyond the list (unverified content).
- **Family:** F3 4-out 1-in (high post) → F7 seal / lob → F8 back screens → F5 slip.
- **Start alignment:** 4-out with 5 at the HIGH POST (4.39, 78.2) or low [MA12].
- **Roles:** 5 high post (seal, flash, back screener, ball screener, slipper); 4 back screener / back cutter; 1, 2, 3 perimeter.
- **Ordered actions:**
  - Topside: 5 seals the fronting defender for a lob; 4 back-screens 2 [MA12].
  - Flash: 5 flashes to the FT line; 4 back-cuts; else 4 back-screens 3 [MA12].
  - Jet-Back: 1→3; 5 back-screens 1 (to the weak block, then corner); 2 to FTX; 5 ball-screens 3; if X5 jumps out, 5 slips for a lob from 2 [MA12].
- **Usual counters:** seal; slip [MA12].
- **Detection signature [HEURISTIC]:** Topside = the high post has his defender between him and the ball, then moves to r < 1.5 m on a `LOB`. Flash = post moves to the NAIL and catches; a wing `CUT(backdoor)` ≤ 1.5 s. Jet-Back = back `SCR` by the post on the passer, then a ball `SCR` by the same post ≤ 2 s, then `SLIP`.
- **Teams documented:** none at college level named [MA12].
- **Sources:** [MA12].
- **Confidence:** medium.

### F07. W2 / W3 (weave screen)

- **Name and aliases:** "W2", "W3" (Coach's Clipboard 4-out high motion plays) [MA12].
- **Family:** F3 4-out 1-in or 3-out 2-in → F6 DHO → F8 screen on the receiver's defender.
- **Start alignment:** 3-out 2-in or 4-out [MA12].
- **Roles:** 1 dribbler, DHO giver, then screener on X2; 2 (or 3) DHO receiver.
- **Ordered actions:** 1 dribbles at 2 (or 3), hands off and screens X2; "Back" counter if X2 jams the handoff [MA12].
- **Usual counters:** backdoor ("Back") [MA12].
- **Detection signature [HEURISTIC]:** `DHO` at the arc where the giver then stays stationary ≥ 0.5 s within 1.2 m of the receiver's defender.
- **Teams documented:** none named.
- **Sources:** [MA12].
- **Confidence:** medium.

### F08. UConn Forwards Out Zoom [RICHER VARIANT of Zoom]

- **Name and aliases:** UConn "Forwards Out Zoom" (Breakthrough) [MA70]. Related: O06/O07 MSU Forwards Out, G05 Princeton Forwards Out.
- **Family:** F3 4-out → F6 DHO → F8 back screen, loop under the rim → F6 zoom DHO → F8 flare (hammer-like).
- **Start alignment:** 4-out; 5 lifts to the ELBOW during the action (spots otherwise unverified) [MA70].
- **Roles:** 1 DHO giver, flare screener; 2 DHO receiver, back-screen cutter, looper, zoom receiver; 3 weak-side down screener; 4 top filler, runs off 1's flare; 5 elbow back screener and zoom DHO giver.
- **Ordered actions:** 1 DHOs with 2 while 3 down-screens 4 on the weak side; 2 dribbles to the slot and passes to 4 filling the top; 5 lifts to the elbow; 2 sprints off 5's back screen (scoring look); 2 loops under the rim and gets a down screen from 3; 4 runs over 5; 5 dribbles at 2 for the zoom DHO; 4 runs off 1's flare to the corner [MA70].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** `DHO` → back `SCR` (UCLA-like) → loop under the rim (cutter x changes sign at y < 1.5 m) → zoom (down `SCR` + `DHO` ≤ 1.5 s) + weak-side flare toward θ ≤ 12° within about 10 s.
- **Teams documented:** UConn (Hurley); clip used in a 2024 article; season 2022-23 or 2023-24 (unverified) [MA70].
- **Sources:** [MA70].
- **Confidence:** medium-high.

### F09. Gate (Spurs)

- **Name and aliases:** "Gate" (Breakthrough, Spurs set) [MA80]. NBA secondary alias.
- **Family:** F3 4-out 1-in → F8 decoy cut, elevator.
- **Start alignment:** 4-out 1-in; shooter 2 on the left [MA80].
- **Roles:** 1 handler; 3 decoy cutter through two screens; 2 screener at the left elbow, then elevator user; 4 and 5 elevator screeners.
- **Ordered actions:** 1 dribbles right; 3 runs through two screens to the left wing (decoy); 2 sets a screen at the left elbow, then goes through the 4+5 double, which closes the gate; 1→2 for a three; else 1→3 with the left side cleared [MA80].
- **Usual counters:** pass to 3 on the cleared side [MA80].
- **Detection signature [HEURISTIC]:** a decoy cutter first (a cutter who passes two `SCR` contacts and receives no pass within 2.0 s of the second); ≤ 2.0 s later a player who **just screened** goes through an elevator (`DOUBLE` closing to < 0.6 m) and catches at r ≥ 6.75 m ≤ 1.5 s after passing it.
- **Teams documented:** none at college level; San Antonio Spurs (NBA) [MA80].
- **Sources:** [MA80].
- **Confidence:** medium-high.

### F10. Spurs two-man game

- **Name and aliases:** "How the Spurs run their two-man game" (Breakthrough) [MA84]. NBA secondary alias.
- **Family:** F2 secondary → F3 4-out 1-in → F8 big-for-big down screen → F6 / F5 side two-man game.
- **Start alignment:** 4-out 1-in from secondary [MA84].
- **Roles:** 1 dribbler, then two-man partner; 3 to the far corner; 2 to 5's spot; 5 to 1's spot, reverser and down screener; 4 down-screen receiver at FTX.
- **Ordered actions:** 1 dribbles to the wing; 3 to the far corner; 2 to 5's spot; 5 to 1's spot; 1→5→2; 5 down-screens 4; 2→4; 4 shoots, drives, or plays DHO / side PnR with 1 (wrinkle: 4 back-screens 5) [MA84].
- **Usual counters:** 4 back-screens 5 [MA84].
- **Detection signature [HEURISTIC]:** ≥ 4 players each move ≥ 3 m to a different canonical spot within 3 s (the dribbler to the wing, a wing to the far corner, two others into the vacated spots); ≤ 3.0 s later a big down-screens a big, who catches at FTX; then `DHO` or ball `SCR` on that side ≤ 3.0 s after the catch.
- **Teams documented:** none at college level; San Antonio Spurs (NBA) [MA84].
- **Sources:** [MA84].
- **Confidence:** medium.

### F11. Slot cut

- **Name and aliases:** "slot cut" (HoopStudent) [MB39].
- **Family:** F8.2 cut used as an entry trigger in 4-out 1-in (F3 / F4.2).
- **Start alignment:** Example 1 (4-out 1-in): 1 and 4 in the SLOTS (7.62, 66.8 / 113.2); 2 and 3 on the wings (7.32, 34.9 / 145.1); 5 on the low post (BLOCK 2.04, 26.2). Example 2: 2 with the ball on the left wing; 4 on the left BLOCK (2.04, 153.8); 3 in the weak-side extended slot; 5 at the weak-side DUNKER (2.72, 6.3) [MB39].
- **Roles:** slot player = cutter; feeder = post or driver.
- **Ordered actions:**
  - (a) Post-entry trigger: 1→3, then 3 enters to 5; the opposite slot (4) cuts to the rim through the slot and 5→4 for the layup (0–3 s).
  - (b) Drive trigger: 2 drives baseline off a step-up screen by 4; when 2 reaches the lane line, 3 starts the slot cut and 2→3 at the rim [MB39].
  - Sourced spatial cue: the cutter starts as the dribbler reaches the lane line and brushes the elbow so the nail help cannot see the cut [MB39].
- **Usual counters:** not given beyond timing.
- **Detection signature [HEURISTIC]:** a `CUT` starting at a slot (r 6.75–8.2 m, θ 60–80° / 100–120°, vocabulary slot class) that passes within 1.5 m of an ELBOW anchor and ends at r < 2 m, started within 0.5 s of either a `POST_ENTRY` catch or a driver crossing |x| < 1.83 m; the path must not cross within 0.9 m of the NAIL (4.19, 90.0) before reaching the elbow.
- **Teams documented:** none named [MB39].
- **Sources:** [MB39].
- **Confidence:** medium.

### F12. Phoenix Reverse Xavier Shuffle ("Pick the Picker")

- **Name and aliases:** "Phoenix Reverse Xavier Shuffle"; "Pick the Picker" (Coaching Toolbox, from Vonn Read's *The Basketball Encyclopedia of Plays*) [MB16]. The name suggests Xavier; that attribution is unverified.
- **Family:** F2 secondary → F3 4-out 1-in → F8 flex, pin-down, screen-the-screener.
- **Start alignment:** 4-out 1-in out of transition: 1, 2 and 4 on the perimeter (slots and wings); 5 inside; the text does not reference 3 [MB16].
- **Roles:** 1 reverser, then pin-down screener; 4 reversal receiver and cutter; 2 flex cutter who stops in the lane, then screener; 5 flex screener, then popper.
- **Ordered actions:**
  1. 1→4 (reversal, 0–1.5 s).
  2. 5 flex-screens for 2, who stops in the middle of the lane (1–3 s).
  3. 1 pin-down screens for 5, who pops high; 1 spaces to the mid-wing (2.5–4.5 s).
  4. 4→5→1 (4–6 s).
  5. 4 cuts hard to the basket off 2's screen, either side; 2 pops to the top for a shot ("Pick the Picker") (5.5–7.5 s) [MB16].
- **Usual counters:** 4 can cut either side of 2's screen [MB16].
- **Detection signature [HEURISTIC]:** within 10 s of possession start: a flex `SCR`, after which the flex cutter stops at r < 3 m, θ 70–110° for ≥ 0.5 s and becomes a screener; a down `SCR` on the original flex screener, who exits to r 5–7 m; the final `SCR` is by the original flex cutter for the reversal receiver going to r < 2 m, after which the screener pops to TOP within 1.5 s.
- **Teams documented:** none named [MB16].
- **Sources:** [MB16].
- **Confidence:** medium (sequence); low (team).

---
## 5. 5-out family (F3.1 / F4.2), including 5-out early-offense entries

**Template start** ("5-out template"): TOP (7.60, 90.0); WINGS (7.50, 45.0 / 135.0); CORNERS (6.81, 3.4 / 176.6). Discriminator: nobody at r < 6 m at the snapshot (`offense_full.md` §3.1). Spacing is NCAA (r ≥ 6.75 m); sources that use NBA-line spots are mapped to these spots. No MSU usage found for any item in this section (MSU's Weave Zoom, which may start 5-out, is U05).

### V01. Stagger Away (5-out) [RICHER VARIANT of the "stagger away" mention under Kansas high-low, `offense_full.md` 4.1]

- **Name and aliases:** "Stagger Away" (Hooper University 5-out early offense) [MB28]; "Stagger" (Travis Steele, Xavier; Coach's Clipboard 5-out quick hitters) [MA9]. Merged: both are a reversal followed by a two-man stagger away from the ball for the far shooter.
- **Family:** F2 / F3 5-out → F8 stagger away.
- **Start alignment:** Hooper: 1 centres the ball to 5 at TOP (7.60, 90.0); 5 reverses to 4 on the opposite WING (7.50, 45.0); shooter 2 in the weak-side CORNER (6.81, 176.6) (mirror: 135.0 / 3.4) [MB28]. Xavier: the ball reverses to 2 on the left wing; 1 and 5 stagger away for 3 [MA9].
- **Roles:** 1 and 5 stagger screeners; far shooter (2 in Hooper, 3 in Xavier); reversal receiver passes.
- **Ordered actions:**
  1. t0: 1→5→4 (or the reversal to 2) (0–3 s).
  2. 1 and 5 set staggered away screens; the shooter sprints to the top for a shot (2.5–6.0 s) [MB28][MA9].
- **Usual counters:** trail → shooter curls to the rim; overplay → shooter rejects and back-cuts, and 1 pops off 5's single down screen; no advantage → 5 sets a middle ball screen for the top player, or flow into the Point series or Zoom [MB28]. Xavier follow-ups: V03 Lob, V04 Boston, V05 Boomerang [MA9].
- **Detection signature [HEURISTIC]:** a big catches at TOP and reverses to a wing (`REVERSAL`); within 1.5 s two weak-side screeners set a `STAGGER` (spacing per §0.3) along a path from the corner (θ ≥ 168° or ≤ 12°) to TOP; the corner player traverses that path to r 7–8.5 m, θ 80–100° within 3.5 s and catches.
- **Teams documented:** Xavier (Travis Steele), season unverified [MA9]. Hooper names no team for this action [MB28].
- **Sources:** [MB28], [MA9] (re-opened 2026-10-18; matches).
- **Confidence:** medium-high.

### V02. Single Away (5-out)

- **Name and aliases:** "Single Away" (Hooper University) [MB28].
- **Family:** F2 secondary → F3 5-out → F8 screen away.
- **Start alignment:** 5-out after transition: 1 centres the ball to 5 at TOP (7.60, 90.0); 5 swings to 4 on the opposite wing (7.50, 45.0 / 135.0); 1 on the weak-side wing [MB28].
- **Roles:** 5 centre hub, then away screener; 1 cutter; 4 wing receiver.
- **Ordered actions:**
  1. t0: 1→5 at the top; 5→4 on the wing (0–3 s).
  2. 5 screens away for 1, who sets up and pops to the top (2.5–4.5 s) [MB28].
- **Usual counters:** trail → 1 curls to the rim; overplay → 1 rejects and back-cuts for 4's pass, and if not open 5 pops to the top for a "Get" (V09); switch → 5 ducks in and posts X1; no advantage → middle ball screen from 5, or flow into the Point series or Zoom [MB28].
- **Detection signature [HEURISTIC]:** a big at TOP (r 7–8.5 m, θ 80–100°) catches, then swings to a wing; within 1.5 s the big becomes a stationary `SCR` at r 6–7.5 m on the weak side for the guard who passed to him; that guard exits to TOP (pop), to r < 2 m (curl or reject), or the big `SEAL`s at r < 2.5 m (switch).
- **Teams documented:** none named for this action; the page names Villanova as using 5-out actions in transition [MB28].
- **Sources:** [MB28].
- **Confidence:** medium-high.

### V03. Lob (Xavier 5-out)

- **Name and aliases:** "Lob" (Travis Steele, Xavier; Coach's Clipboard) [MA9].
- **Family:** F3 5-out → F8 stagger → back screen for the big (lob).
- **Start alignment:** 5-out template; starts like V01 [MA9].
- **Roles:** 1 and 5 stagger screeners; 3 stagger cutter to the top; 1 then back-screens 5; 5 lob cutter; wing passer throws the lob.
- **Ordered actions:** 1 and 5 set the staggered down screen for 3, who cuts to the top (0–3 s); 1 back-screens for 5, who cuts for a lob from the wing (3–5 s) [MA9].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** V01 front end; stagger screener #1 (a guard) immediately back-screens screener #2 (the big), who reaches r < 1.5 m on a `LOB`.
- **Teams documented:** Xavier (Steele), season unverified [MA9].
- **Sources:** [MA9].
- **Confidence:** medium-high.

### V04. Boston (Xavier 5-out)

- **Name and aliases:** "Boston" (Travis Steele, Xavier; Coach's Clipboard) [MA9].
- **Family:** F3 5-out → F8 fake stagger, curl, down screen.
- **Start alignment:** 5-out template.
- **Roles:** 1 passer, then first stagger screener and down-screen user; 5 hub, second screener, down screener; 4 receiver; 3 curler.
- **Ordered actions:** 1→5→4; 1 and 5 appear to stagger for 3, but 3 curls around 1 for an inside shot; 5 down-screens 1, who cuts to the top for a pass and a three (0–5 s) [MA9].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** ≤ 2.0 s after the pass to the wing the cutter curls within 1.2 m of the **first** stagger screener and reaches r < 3 m (does not use the second); ≤ 2.0 s later the second screener down-screens the first, who catches at TOP ≤ 1.5 s after the contact.
- **Teams documented:** Xavier (Steele), season unverified [MA9].
- **Sources:** [MA9].
- **Confidence:** medium.

### V05. Boomerang (pass and immediate return to attack the closeout)

- **Name and aliases:** "Boomerang" (Travis Steele, Xavier 5-out quick hitter; Coach's Clipboard) [MA9]; "boomerang action / boomerang pass" (HoopStudent) [MB38]. Merged: the Xavier play is a named team version of the general action.
- **Family:** F3 entry vs pressure → F10 drive-and-kick.
- **Start alignment:** Xavier: 5-out template, starting like V01 [MA9]. HoopStudent: any; pressure example with 1 at TOP and 2 on the adjacent wing [MB38].
- **Roles:** passer (who gets it back and attacks); adjacent receiver.
- **Ordered actions:**
  - Xavier: 1 reverses the ball; 1 and 5 stagger away for 3, who cuts to the top for a pass from 2; 3 immediately passes back to 2, who attacks off the dribble (0–4 s) [MA9].
  - HoopStudent: 1 passes to the adjacent teammate; 1's defender sags into help around the high post; 1 mini-V-cuts and gets the ball straight back; 1 attacks the closeout. Switch example: after a switched PnR, the handler passes out and gets it back to attack the slower big [MB38].
- **Usual counters:** after the first pass the passer can instead screen the corner, screen away or cut; an escape dribble is the weaker alternative [MB38].
- **Detection signature [HEURISTIC]:** `PASS(a→b)` then `PASS(b→a)` within 2.0 s, players ≤ 7.5 m apart (Xavier version: the first catch comes off a stagger); between the passes, a's defender moves ≥ 1.5 m toward the paint and then closes out at ≥ 3 m/s; `DRIVE` by a, or first-step speed > 4 m/s, within 1.0 s of the return.
- **Teams documented:** Xavier (Steele), season unverified [MA9].
- **Sources:** [MA9], [MB38].
- **Confidence:** medium.

### V06. Flare (Xavier 5-out)

- **Name and aliases:** "Flare" (Travis Steele, Xavier; Coach's Clipboard) [MA9]. Distinct from repo Horns Flare and H24.
- **Family:** F3 5-out → F8 flare → skip.
- **Start alignment:** 5-out template; 5 at TOP.
- **Roles:** 1 passer; 5 top receiver and skip passer; 3 flare screener; 2 shooter.
- **Ordered actions:** 1→5 while 3 sets a flare screen for 2; 5 passes over the top to 2 for a three (0–3 s) [MA9].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** pass to a big at TOP; weak-side flare `SCR`; `PASS` from the TOP big (|x_ball| < 1.5 m) of length ≥ 6 m to the flare user at r ≥ 6.75 m within 1.5 s of the flare contact.
- **Teams documented:** Xavier (Steele), season unverified [MA9].
- **Sources:** [MA9].
- **Confidence:** medium.

### V07. Georgia (Lennie Acuff, Lipscomb)

- **Name and aliases:** "Georgia" (Lennie Acuff, Lipscomb; Coach's Clipboard 5-out quick hitters) [MA9].
- **Family:** F3 5-out → F8 curl → F6 pop and DHO → F5 roll.
- **Start alignment:** 5-out template; 5 at TOP.
- **Roles:** 1 passer and curler, then left corner; 5 hub, screener for 1, popper, DHO giver, roller; 3 receiver and DHO receiver; 4 moves up, cuts if 5 pops; 2 kick-out target.
- **Ordered actions:** 1→5→3; 5 screens for 1, who curls for 3's pass; 1 to the left corner, 4 up; 5 pops, catches and DHOs to 3; roll; 4 cuts if 5 pops (0–8 s) [MA9].
- **Usual counters:** 3 attacks, shoots, hits 5 rolling, or kicks to 2 [MA9].
- **Detection signature [HEURISTIC]:** a big screens for the point guard to curl after a pass-pass chain; then `POP` and `DHO` by the same big ≤ 3 s.
- **Teams documented:** Lipscomb (Acuff), season unverified [MA9].
- **Sources:** [MA9].
- **Confidence:** medium.

### V08. Pitt 5-out fake DHO into double zoom

- **Name and aliases:** Pitt 5-out fake DHO into double zoom (Breakthrough) [MA69].
- **Family:** F3 5-out → F6 fake DHO → F8 stagger → F6 zoom DHO.
- **Start alignment:** 5-out; 5 pops to the top [MA69].
- **Roles:** 5 top catcher and dribbler into the zoom; 1 fake-DHO cutter, stagger screener; 4 stagger screener; 3 corner player and zoom receiver.
- **Ordered actions:** 5 pops to the top and catches; 1 fakes a DHO and follows 4 into a stagger for 3 in the corner; 5 dribbles at the staggered screeners; 3 comes up for the DHO; 4 and 1 pop [MA69].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** `FAKE_DHO`; ≤ 1.5 s later a down `STAGGER` whose user takes a `DHO` ≤ 2.0 s after the second contact (double zoom); both screeners `POP` ≤ 1.5 s after the DHO.
- **Teams documented:** Pitt (season 2022-23 inferred) [MA69].
- **Sources:** [MA69].
- **Confidence:** medium-high.

### V09. Get (pass to the big, sprint for a handoff) [RICHER VARIANT; `set_taxonomy.md` §1.9 lists "Get" as convention only]

- **Name and aliases:** "Get" action (Hooper University, two pages) [MB27][MB28]. Pass-less version: V11 dribble-at handoff. Related: repo Horns Elbow Get; V10 Spanoulis DHO.
- **Family:** F6 handoff → F2 early offense.
- **Start alignment:** the handler passes to the trailing big, who catches above the FT line (y > 4.19 m), typically at TOP (7.60, 90.0) [MB28].
- **Roles:** 1 passer, then handoff receiver; 5 handoff big.
- **Ordered actions:**
  1. t0: 1→5 (0 s).
  2. 1 sprints to 5 for the handoff (0.3–1.8 s).
  3. Reads: defender over → turn the corner, 5 rolls; defender under → shoot if a shooter, else 5 twists or re-screens to force over (1.5–4 s) [MB28].
- **Usual counters:** twist / re-screen [MB28].
- **Detection signature [HEURISTIC]:** `PASS(a→big)` with the big at y > 4.19 m; a moves toward the big at > 3 m/s; `DHO(big→a)` within 2.0 s of the pass with the big at r 6–8.5 m; the big's next move is a `ROLL` or a second contact from the opposite side (twist / re-screen).
- **Teams documented:** Northern Iowa uses "Get" in early offense (AJ Green named as the primary handler; no coach or season named) [MB27].
- **Sources:** [MB27], [MB28].
- **Confidence:** high (definition); medium (team usage).

### V10. Spanoulis DHO action

- **Name and aliases:** "Spanoulis Action", "Spanoulis DHO" (Breakthrough; Mark Brase; Frank Bennett, USA Basketball / Chaminade HS) [MA65]. European secondary alias. A low player sprints up into a DHO.
- **Family:** F6 handoff (5-out) → F5.
- **Start alignment:** 5-out-like with the ball near TOP (7.60, 90.0); one player low (CORNER 6.81, 3.4 or UNDER 0.95, 18.4) who sprints up; Bennett starts it with a flare screen on both sides [MA65].
- **Roles:** ball holder at the top (DHO giver, then roller); low sprinter (DHO receiver and attacker).
- **Ordered actions:** t0 the low player sprints toward the ball (0–1.5 s); DHO at the slot/top (1.0–2.0 s); the attacker turns the corner, shoots or passes (2.0–4.0 s) [MA65].
- **Usual counters:** lob or pass to the rolling post if switched or denied; pass to the wing for a post entry; second DHO by dribbling back toward the wing; back cut if the handoff is denied [MA65].
- **Detection signature [HEURISTIC]:** a player starting at r < 2 m or θ ≤ 12° accelerates to ≥ 4 m/s toward the ball and receives `DHO` at r 6.5–8.5 m within 2.0 s; the giver stays stationary ≥ 0.5 s after the transfer, then `ROLL`s.
- **Teams documented:** no college team named (HS / USA Basketball coach) [MA65].
- **Sources:** [MA65].
- **Confidence:** medium.

### V11. Dribble-at entry (backcut, handoff or shallow read)

- **Name and aliases:** "Dribble At" (Basketball For Coaches) [MB19]; "dribble entry" counter (HoopStudent 3-out 2-in) [MB25]. The repo mentions dribble-at only as a denial counter (`set_taxonomy.md` §1.4).
- **Family:** F4.2 rule-based motion (5-out / 4-out / 3-out 2-in) → F3 entry vs denial.
- **Start alignment:** 5-out template [MB19].
- **Roles:** dribbler; the player being dribbled at; three fillers.
- **Ordered actions:**
  1. Trigger: the handler is pressured and passes are denied.
  2. `DRIBBLE_AT` toward the teammate at the next spot (0–2 s).
  3. The receiver reads (1–3 s): (a) backcut to the rim, and if not passed to, fill the weak-side corner while the others rotate toward the ball; or (b) take the handoff, attack the rim and kick to shooters if help comes [MB19].
  - HoopStudent 3-out 2-in variant: if the wing pass is denied, 1 dribbles at the wing and 3 shallow-cuts under 1 to the top; or 5 cuts to the top while 3 replaces in the low post [MB25].
- **Usual counters:** shallow / replace instead of a backcut; attack closeouts after the DHO [MB19][MB25].
- **Detection signature [HEURISTIC]:** `DRIBBLE_AT(a→b)` with b at r ≥ 6.5 m; within 1.0 s of the dribbler closing to ≤ 3.5 m, b either `CUT(backdoor)`s to r < 2 m ("dribble-at backcut"), meets the dribbler for a `DHO` ("dribble-at handoff"), or moves along the arc behind the dribbler toward the vacated spot ("dribble-at shallow / replace"); in the preceding 2 s b's defender was within 1.2 m on the ball-side line (denial).
- **Teams documented:** none named [MB19][MB25].
- **Sources:** [MB19], [MB25].
- **Confidence:** high (concept); low (team usage).

### V12. Pass-and-cut entry with fill rules (5-out) [RICHER VARIANT of "Give-and-go" (F8.2)]

- **Name and aliases:** "pass and cut", "basic cutting", give-and-go (HoopStudent; Basketball For Coaches) [MB19][MB30].
- **Related (repo):** `offense_full.md` 4.2 "5-out motion: Pass-cut-fill" [S31]. Not a duplicate: the repo row names the continuity rule only; V12 adds the entry sequence and the fill rules as a half-court start.
- **Family:** F4.2 5-out motion → F3 entry.
- **Start alignment:** 5-out template.
- **Roles:** passer-cutter; receiver; fillers.
- **Ordered actions (the cutter reaches r < 2 m within about 1.5 s of the pass; [HEURISTIC]):**
  - Top → wing: the passer basket-cuts through the key to the **opposite corner**; the others slide one spot toward the ball.
  - Wing → corner: the passer basket-cuts to the opposite corner; the others fill toward the ball.
  - Corner → wing: the passer basket-cuts and **replaces himself** in the same corner; the others hold.
  - Wing → top: the passer basket-cuts and fills the corner on his own side; the weak-side wing moves up and the corner replaces it [MB19].
  - Reads: overplayed → back-cut; defender jumps to the ball → back-cut and step in front [MB19].
- **Usual counters:** a mismatched cutter posts up for 1–2 s [MB19]; cut through to a corner when covered [MB30].
- **Detection signature [HEURISTIC]:** `PASS` from r ≥ 6.5 m; the passer starts a `CUT` within 0.8 s, reaches r < 2.5 m, then exits to a corner (opposite corner for top → wing and wing → corner, same corner for corner → wing); ≥ 2 teammates shift one spot along the arc (|Δθ| 25–50°) within 2.5 s. ≥ 2 consecutive passes with this pattern → "5-out pass-cut-fill motion".
- **Teams documented:** none named.
- **Sources:** [MB19], [MB30].
- **Confidence:** high.

### V13. Screen-away entry, "always curl" vs "curl or pop" [RICHER VARIANT of "Screen away" (F8.1)]

- **Name and aliases:** "screen away", "pass and screen away" (HoopStudent) [MB42]; Option 1 / Option 2 (Basketball For Coaches) [MB19].
- **Family:** F4.2 motion → F8.1 screen away.
- **Start alignment:** 5-out template; also used in 3-out 2-in and 4-out 1-in [MB42].
- **Roles:** passer-screener; screened cutter; receiver.
- **Ordered actions:**
  1. Pass; the passer moves to the next teammate **away** from the ball and screens at an angle so the cutter can reach the rim; the screener calls the cutter's name and raises a fist (0.5–2 s) [MB19].
  2. Option 1 (always curl): the cutter curls to the rim, then fills the weak-side corner; the screener pops back to the spot he screened from (1.5–3.5 s). Option 2 (curl or pop): the screener goes opposite to the cutter: cutter pops → screener cuts to the rim and fills the corner; cutter curls → screener pops [MB19].
  - Allowed on top → wing, wing → corner and wing → top passes, not corner → wing [MB19]. HoopStudent adds cutter reads (reject and back-cut, speed cut, split) and screener reads (pop, self-replace, slip, back screen, STS) [MB42].
- **Usual counters:** cutter pops if his defender goes under [MB19]; screener slips if switched [MB42].
- **Detection signature [HEURISTIC]:** `PASS(a→b)`; within 1.5 s a becomes a `SCR` at sign(x) ≠ sign(x_b), or ≥ 3 m along the arc away from b, for teammate u; label u's exit: curl (r < 3 m within 1.5 s), pop (toward the ball along the arc), reject (path never within 1.2 m of a); the screener's next move is the opposite of u's (Option 2). "Always curl" tag requires ≥ 3 occurrences with u curling and a popping.
- **Teams documented:** none named.
- **Sources:** [MB19], [MB42].
- **Confidence:** high.

### V14. Cut through the nail (Open Post L-cut rule)

- **Name and aliases:** "Cut Through the Nail (L-Cut variation)"; attributed by Basketball For Coaches to Bob Huggins' Open Post Motion [MB19]. Which program and season: unverified.
- **Family:** F4.2 motion → F8.2 V/L cut.
- **Start alignment:** 5-out template.
- **Roles:** any player refilling the top.
- **Ordered actions:** every cut **to the top** passes through the nail; if denied at the top, the player back-cuts and fills the weak-side corner; if played off, he pops out to the top (each decision 0.5–1.5 s) [MB19].
- **Usual counters:** built in (deny → back-cut) [MB19].
- **Detection signature [HEURISTIC]:** a player's path to TOP (r 7–8.5 m, θ 80–100°) passes within 1.0 m of the NAIL (4.19, 90.0) just before arriving, with a heading change of 70–110° at the nail ("L") or a reversal > 120° back toward the rim (back-cut). Possession tag "open-post / nail-route motion" if ≥ 70% of top refills go through the nail.
- **Teams documented:** Bob Huggins' Open Post Motion; school and season not given (unverified) [MB19].
- **Sources:** [MB19].
- **Confidence:** medium.

---
## 6. Box family (F3.3)

**Template start** ("Box template"): 1 at TOP (7.60, 90.0) or out of bounds; two players at the ELBOWS (4.57, 66.4 / 113.6); two on the BLOCKS (2.04, 26.2 / 153.8). H13 Bucks also starts from a box but is filed under Horns (where the source puts it).

### X01. Wheel (Spurs) [repo mentions UConn "Wheel" without detail]

- **Name and aliases:** "Spurs Wheel" (Breakthrough; 2014 Finals) [MA72]. NBA secondary alias. Not the same as W01 Wheel offense (Pinholster) or U20 Duke Wheel Action.
- **Family:** F3.3 Box → F8 down screen, run across three screens → F5 option.
- **Start alignment:** guards on the BLOCKS (2.04, 26.2 / 153.8); posts at the ELBOWS (4.57, 66.4 / 113.6); 1 at TOP (7.60, 90.0) [MA72].
- **Roles:** 1 handler, passer, then the runner through three screens; 4 down screener for 2, then optional ball screener; 2 wing receiver and return passer; 3, 4 and 5 screeners for 1.
- **Ordered actions:** 1 dribbles to a side; 4 down-screens 2 on the block; 1→2 and runs to the other side through screens by 3, 4 and 5; 1 catches from 2 and attacks; option: 4 ball-screens 1 [MA72].
- **Usual counters:** 4 ball screen for 1 [MA72].
- **Detection signature [HEURISTIC]:** Box `ALIGN`; a down `SCR` from an elbow for a block guard who catches at the wing; the passer then runs across the lane past **three** stationary teammates (three `SCR` contacts) within 3 s and receives the return pass at r ≥ 6.75 m.
- **Teams documented:** none at college level; San Antonio Spurs (NBA) [MA72].
- **Sources:** [MA72].
- **Confidence:** medium-high.

### X02. Box Rip Lob (Texas Tech)

- **Name and aliases:** "Box Rip Lob" (FastModel) [MA63].
- **Family:** F3.3 Box → F8 fake cross, rip (back) screen → lob.
- **Start alignment:** Box template (spots per template; page diagram unreadable) [MA63].
- **Roles:** 2 fake cross screener, then cutter off 4 to the wing; 3 back screener for 4; 4 lob cutter; 1 lob passer.
- **Ordered actions:** 2 fakes a cross screen for 3 and cuts off 4 to the wing; 3 back-screens 4; 1 lobs to 4 (0–3 s) [MA63].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** Box `ALIGN`; a fake cross (the guard moves ≥ 1.5 m in |Δx| toward the other block player, then reverses heading > 120° within 0.8 s); ≤ 2.0 s later a guard sets a back `SCR` on a big from the block area; `LOB` to r < 1.5 m ≤ 1.5 s after the back-screen contact.
- **Teams documented:** Texas Tech 2018-19 (opening play vs Michigan State, Final Four) [MA63]. MSU was the defending team.
- **Sources:** [MA63].
- **Confidence:** medium-high.

### X03. Michigan (youth continuity: double down, then cross and away) [NAME COLLISION with H15 "Michigan" (Horns)]

- **Name and aliases:** "Michigan" (Breakthrough "Youth Offense – Michigan") [MA85].
- **Family:** F3.3 Box → F4.1 continuity (two down screens, then cross + away screens).
- **Start alignment (inferred from the step text):** 1 at TOP (7.60, 90.0); 2 and 3 low (BLOCK 2.04, 26.2 / 153.8); 4 and 5 above them near the ELBOWS (4.57, 66.4 / 113.6).
- **Roles:** 4 and 5 down screeners, then 4 cross-screens 5; 2 and 3 down-screen users; 1 passer, then away screener.
- **Ordered actions:** 4 down-screens 2 and 5 down-screens 3 as 1 arrives (0–2 s); 1→2; 4 cross-screens 5 and 1 screens away for 3 (2–4 s); 5 to the ball side, 3 to the top (4–5 s); repeat from the mirror [MA85].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** two simultaneous down `SCR` events (|Δt| ≤ 0.5 s) send both wings from y < 2 m to FTX; then a low cross `SCR` and a high away `SCR` concurrently; mirror repeat = continuity.
- **Teams documented:** none (youth / HS) [MA85].
- **Sources:** [MA85].
- **Confidence:** medium.

---

## 7. Stack, Floppy and Zipper (low) starts (F3.3 / F3.1)

**Template start:** ≥ 3 players at r < 2.5 m at the snapshot, or pairs stacked at the blocks (≤ 1.2 m apart). Floppy = shooters at r < 1.5 m with screeners on the lane lines; Zipper = a block player moves up the lane line ≥ 4 m past a stationary teammate (`offense_full.md` §3.1).

### K01. Stack dribble entry into double pin-down and reversal

- **Name and aliases:** Stack offense, Example 1 (HoopStudent) [MB43]. The repo has the Stack alignment only.
- **Family:** F3.3 Stack → F8 pin-downs → cross screen + flare.
- **Start alignment:** 1 at TOP (7.60, 90.0); pairs stacked near both low posts: 3 above 2 at the left BLOCK (2.04, 153.8), 4 above 5 at the right BLOCK (2.04, 26.2). HoopStudent puts the pairs "near the low post"; the stacking order is inferred from the actions (unverified) [MB43].
- **Roles:** 2 and 5 pin-down screeners; 3 top receiver; 4 right-wing receiver; 1 dribbler, then flare screener; 5 later cutter to the right low post.
- **Ordered actions:**
  1. 1 dribbles toward the left wing; 2 and 5 set pin-downs; 3 cuts to the top and 4 to the right wing (0–2.5 s).
  2. 1→3→4 reversal (2.5–5 s).
  3. 2 cross-screens; 5 cuts through the lane to the right low post; 1 moves to the top to set a flare for 3, who goes to the left wing (5–8 s).
  4. 4 feeds 5, or skips to 3 [MB43].
  - Example 2: 5 steps up for a ball screen with Spain (2 back-screens 5's defender), then reversal and a flex for 3 [MB43].
- **Usual counters:** Example 2 [MB43].
- **Detection signature [HEURISTIC]:** Stack snapshot (two pairs at r < 2.5 m on both sides, each pair < 1.2 m apart); within 2.5 s of the first dribble, both upper (or both lower) stack members exit to TOP and the far wing off simultaneous stationary screens (≤ 0.5 s apart); `REVERSAL` by two passes within 3 s; then a cross `SCR` at y < 2 m plus a flare `SCR` at TOP within 3 s.
- **Teams documented:** none named for this sequence [MB43]. The repo lists MSU stack-based ISO-4 and Chest (`set_taxonomy.md` §3.2).
- **Sources:** [MB43].
- **Confidence:** medium-low (alignment detail).

### K02. Floppy Stagger Punch [MSU]

- **Name and aliases:** "Floppy Stagger Punch" (FastModel Play of the Day, 2012-03-05). "Punch" = post feed.
- **Family:** F3.1 Floppy → F8 loop, floppy, stagger → F7 post seal.
- **Start alignment (inferred):** 1 TOP (7.60, 90.0); 2 on a wing (7.50, 45.0); 3 and 5 low near the lane (BLOCK / UNDER); 4 on the backside (BLOCK 2.04, 153.8 or MID-POST 3.11, 135.0). Exact spots unverified.
- **Roles:** 1 passer; 2 looper around 3 and 5, screened by 4; 3 follower who stops under the basket and uses 5's floppy screen, then post feeder; 5 floppy screener, then sealing post.
- **Ordered actions:**
  1. t0: 1 passes to 2; 2 passes back to 1 and loops around 3 and 5, getting a backside screen from 4 (0–3.0 s).
  2. 3 follows 2, stops under the basket and gets a screen from 5 (floppy); 1 passes to 3; 3 feeds 5 sealing in the paint (3.0–5.5 s) [MA49].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** `PASS(1→2)`, `PASS(2→1)` within 1.5 s; 2 then runs a loop through the lane within 1.2 m of two low teammates and off a backside stationary teammate; a second cutter reaches r < 1.2 m and exits off a `SCR` by 5; `PASS(1→3)` at r 5–7 m; `ENTRY(3→5)` with 5 having `SEAL`ed.
- **Teams documented:** **Michigan State 2011-12** (vs Ohio State; season inferred from the 2012-03-05 publish date) [MA49].
- **Sources:** [MA49].
- **Confidence:** medium-high.

### K03. Floppy Loop Under [MSU]

- **Name and aliases:** "Floppy Loop Under" (FastModel Play of the Day, 2012-05-19; page tag "Stack Actions") [MA50].
- **Family:** F3.1 Floppy / F3.3 Stack → F8 pin-in, loop → F7 post feed, high-low dump.
- **Start alignment (inferred):** 1 TOP (7.60, 90.0); 2 low / UNDER (0.95, 18.4), exits to the wing; 5 low (pin screener) on the same side; 3 and 4 stacked low on the other side (BLOCK 2.04, 153.8) [MA50].
- **Roles:** 5 pin-in screener, then loop-under post target; 2 wing receiver; 3 looper, then screener for 5 and dump-down target; 4 step-out receiver and post feeder.
- **Ordered actions:**
  1. t0: 5 pins in for 2 to the wing; 3 loops around 4 (0–2.0 s).
  2. 4 steps out to receive from 1; 3 screens for 5, who loops under the basket (2.0–4.0 s).
  3. 5 receives a post feed from 4 (4.0–5.0 s).
  4. If 5 is doubled, 3 is open for a dump-down (5.0–6.0 s) [MA50].
- **Usual counters:** dump-down to 3 vs a double on 5 [MA50].
- **Detection signature [HEURISTIC]:** low `ALIGN` (≥ 3 players at r < 2.5 m); two floppy `SCR` events (one per side) within 1.5 s; a big steps out to r 5–7 m and catches from TOP; a cross/back `SCR` under the rim (y < 1.5 m) for 5, who passes under the basket (x changes sign at y < 1 m) and receives `ENTRY` within 2.0 s.
- **Teams documented:** **Michigan State 2011-12** (2012 NCAA Tournament) [MA50].
- **Sources:** [MA50].
- **Confidence:** medium-high.

### K04. Zipper Again [MSU] [RICHER VARIANT of Zipper start]

- **Name and aliases:** "Zipper Again". Here a **big** zippers off a guard, which is unusual. The page says "4 zippers 2"; read here as 4 cutting up off 2 (interpretation unverified).
- **Family:** F3.1 Zipper start → F8 pin-down → drive and dump.
- **Start alignment (inferred):** 1 TOP (7.60, 90.0); 2 low on a BLOCK (2.04, 26.2) as the screener; 4 low (zipper cutter); 3 weak side low; 5 weak side.
- **Roles:** 4 zipper cutter; 2 receiver; 5 pin screener, then dump target; 3 pin receiver and driver.
- **Ordered actions:**
  1. t0: 4 zippers off 2; 1 passes to 2 (0–2.0 s).
  2. 5 pins for 3; 2 passes to 3 (2.0–4.0 s).
  3. 3 drives and passes to 5 (4.0–5.5 s) [MA52].
- **Usual counters:** can be run as a SLOB [MA52].
- **Related (repo):** `set_taxonomy.md` "MSU Zipper (ATO, 3 options)" [S29c]. Not a duplicate: that set is a 4+5 cross-screen for 2 with three options; K04 is a big zippering off a guard into a weak-side pin and a drive-and-dump.
- **Detection signature [HEURISTIC]:** `CUT(zipper)` (block → slot up the lane line, Δy ≥ 4 m) by a big past a stationary guard; `PASS(1→2)`; weak-side down `SCR(5→3)`; `PASS(2→3)`; `DRIVE` by 3 and a pass to 5 at r < 2 m within 1.5 s of the drive start.
- **Teams documented:** **Michigan State 2013-14** (overtime game vs Ohio State per [MA52], which does not state the result; season inferred from the 2014-01-17 publish date). The only 2013-14 MSU–Ohio State overtime game, 2014-01-07, was an MSU win per the Wikipedia season schedule [MC3]; that this is the clipped game is inferred from the dates.
- **Sources:** [MA52].
- **Confidence:** medium (who zippers whom is ambiguous).

---

## 8. Diamond family (F3 / F4.1)

No new named Diamond entry was found in the opened sources. The repo already holds the FIBA Diamond definition (`offense_full.md` §3.1 and 4.1). Count: 0.

---

## 9. Two-guard front family (F3.1 Princeton 2-guard front; F4.1 Princeton)

**Template start** ("2-guard-front template"): guards 1 and 2 in the slots: SLOT-LL (7.62, 76.1 / 103.9) for Hooper's lane-line-extended slots [MB2], or SLOT (7.62, 66.8 / 113.2) for wider fronts; forwards 3 and 4 on the wings at FTX (7.32, 34.9 / 145.1); 5 at the strong-side BLOCK (2.04, 26.2) or at an ELBOW / HIGH POST (4.57, 66.4 / 4.39, 78.2). Discriminator: two players at the slots, nobody at θ 80–100° beyond the arc. Hooper University's Princeton spots: 1 and 2 in the slots on the lane line extended, 3 and 4 on the wings at FT-line extended, 5 at the strong-side low post [MB2] (re-opened 2026-10-18; matches). The Hoops Geek alternative: 1 and 4 at the top two spots, 2 and 3 on the wings, 5 at the ball-side low post [MB3].

### G01. Point Over (Princeton Point series) [RICHER VARIANT of "Point" in `set_taxonomy.md` §1.4]

- **Name and aliases:** "Point Over"; part of the "Point series", most often triggered from the elbow (Hooper University) [MB2][MB3].
- **Family:** F4.1 Princeton (Carril) → F3 two-guard front; high-post (elbow) entry into a corner pin-down plus DHO.
- **Start alignment:** 2-guard-front template with 5 at the strong-side BLOCK (2.04, 26.2) [MB2].
- **Roles:** 1 entry passer, then shallow cutter to the corner; 2 reversal receiver and Point passer, then pin-down screener; 3 corner player who comes off the pin-down; 5 elbow hub and DHO big; 4 weak-side spacer.
- **Ordered actions:**
  1. t0: 1 reverses to 2 in the weak-side slot; 1 shallow-cuts to the strong-side corner (0–2 s).
  2. 5 lifts from the block to the high elbow, about 3.3 m of travel (BLOCK → ELBOW in this file's frame, computed; Hooper gives no distance and places the catch "1 step outside and higher than the elbow" [MB2]) (0.5–2.5 s).
  3. 2 passes to 5 at the elbow (2–4 s).
  4. 2 cuts over the top of 5 and sets a pin-down for 3 in the strong-side corner (3.5–5.5 s).
  5. 3 comes off the pin-down into a DHO from 5 and turns the corner; 5 rolls to the rim and 2 lifts to the wing (5–7.5 s) [MB2].
- **Usual counters:** if 3's defender overplays, 3 backdoors for a pass from 5; otherwise 3 empties to the weak side and 2 pops back to the wing for a pass and a ball screen from 5 [MB2]. Hoops Geek: the pin-down receiver may reject, tight-curl or post; after 5→1, 1 and 5 run an empty-side ball screen with the screener popping if he shoots [MB3].
- **Detection signature [HEURISTIC]:** 2-guard-front snapshot (two players at r 6.75–8.2 m with θ 60–80° and 100–120° (vocabulary slot class), nobody at θ 80–100° outside the arc, one player at r < 3 m); guard-to-guard `PASS` with |Δx| > 3.0 m, both players at r 7.0–8.2 m, then the passer runs from the slot to the strong-side corner (θ ≤ 12°) within 2.5 s; the low player rises to r 4.2–5.0 m within 2.5 s and catches; the passer moves within 1.5 m of the elbow player on the side away from the ball and becomes a `SCR` at r 3–5 m, θ ≤ 25° on the corner defender ≤ 2 s after the elbow catch; `DHO` at r 4–6 m between the elbow big and the corner cutter ≤ 2 s after the pin-down. Label "Over" when the screener's path crosses to the strong-side corner.
- **Teams documented:** Princeton under Pete Carril (head coach 1967–1996), the originator; Hooper notes Princeton's 1996 NCAA upset of UCLA [MB2][MB3]. MSU: none found.
- **Sources:** [MB2], [MB3].
- **Confidence:** high (sequence, two sources agree); low (timings).

### G02. Point Away (Princeton Point series) [RICHER VARIANT of "Point"]

- **Name and aliases:** "Point Away"; the Point passer screens away from the ball (split-like action) [MB2][MB3].
- **Family:** F4.1 Princeton → F7 post + perimeter (split after a high-post entry).
- **Start alignment:** as G01; the ball goes to 5 at the ELBOW (4.57, 66.4 / 113.6).
- **Roles:** 2 (Hooper; 1 in Hoops Geek) Point passer and away screener; 4 (Hooper; 3 in Hoops Geek) cutter; 5 elbow hub and follow ball screener; strong-side corner player lifts.
- **Ordered actions:**
  1. t0–4 s: reversal and lift to the elbow, as in G01.
  2. The Point passer cuts away from 5 and sets an away screen for 4 (split action) (4–6 s).
  3. 4 usually rejects and back-cuts for a pass from 5 (5–7 s); if no backdoor pass, 4 continues to the opposite corner.
  4. The passer pops back out; 5 follows with a ball screen and rolls hard; the strong-side corner player lifts to the wing (6.5–9 s) [MB2].
- **Usual counters:** no backdoor → 4 empties to the opposite corner [MB2]; cutter tight-curls or curl-pops; screener slips if his defender cheats; the cutter posts, seals and ducks in; 5 can DHO instead of setting a ball screen [MB3].
- **Detection signature [HEURISTIC]:** G01 front end up to the elbow catch; the passer then moves away from the strong-side corner and becomes a stationary `SCR` near r 5.5–7.5 m, θ 25–50° or 130–155° within 2 s of the elbow catch; the screened player `CUT(backdoor)`s to r < 2 m within 1.5 s or exits to the opposite corner; then a ball `SCR` by the elbow big for the original passer above the arc ≤ 3 s after the back-cut.
- **Teams documented:** Princeton (Carril) [MB2][MB3]. MSU: none found.
- **Sources:** [MB2], [MB3].
- **Confidence:** high (sequence); low (timings).

### G03. Wave-through entry into Point (Princeton)

- **Name and aliases:** wave-through entry; "1 waves through to 2" (Hooper University) [MB2].
- **Family:** F3 two-guard front → F4.1 Princeton; entry without a guard-to-guard pass.
- **Start alignment:** 2-guard-front template; 1 holds the ball in the right SLOT (7.62, 66.8).
- **Roles:** 1 handler and Point passer; 2 shallow cutter; 5 elbow lift.
- **Ordered actions:**
  1. t0: 1 waves 2 through; 2 shallow-cuts to the corner opposite his own (weak-side) slot, i.e. the ball-side corner below 1 (Hooper: 1 "can wave through the weak side slot (2)", which "triggers the shallow cut from 2 to the opposite corner"; the ball-side reading is the fixer's inference from 2 starting weak side, re-opened 2026-10-18 (UTC)) (0–4.0 s).
  2. 5 lifts to the **opposite** high elbow (0.5–2.5 s).
  3. 1 passes to 5 at the elbow (2–3.5 s), starting Point Over or Point Away (G01/G02) [MB2].
- **Usual counters:** as G01/G02; if the elbow pass is denied, go backdoor (Hoops Geek, on Point entries in general) [MB3].
- **Detection signature [HEURISTIC]:** 2-guard front at t0 with no guard-to-guard pass; the non-ball slot guard shallow-cuts (r 6–8 m) to the ball-side corner (θ ≤ 12° with sign(x) = sign(x_ball); mirror θ ≥ 168°) in ≤ 4.0 s; the low big moves to the elbow on the side opposite its start (sign of x flips), r 4.2–5.0 m, and catches from the original handler within 3.5 s of t0.
- **Teams documented:** Princeton (Carril) [MB2]. MSU: none found.
- **Sources:** [MB2], [MB3].
- **Confidence:** medium (single source for the entry).

### G04. Low-post series entry (Princeton "Low") [RICHER VARIANT of "Low" in `set_taxonomy.md` §1.4]

- **Name and aliases:** "Low Post Series", "Low"; lets teams go from transition into the Princeton offense with low-post play (The Hoops Geek) [MB3].
- **Family:** F4.1 Princeton → F7 post entry.
- **Start alignment:** 1 and 4 at the top two spots (SLOT 7.62, 66.8 / 113.2); 2 and 3 on the wings (FTX 7.32, 34.9 / 145.1); 5 at the ball-side low post (BLOCK 2.04, 26.2) [MB3].
- **Roles:** 1 guard-to-wing passer; 3 wing post feeder; 5 post.
- **Ordered actions:**
  1. t0: 1 passes to 3 on the wing and cuts hard to the opposite corner (0–3.5 s).
  2. 5 cuts to the block (0.5–2 s); 3 feeds 5 (1.5–3.5 s) [MB3].
- **Usual counters:** 5 beats the denial with swim and spin moves, or catches in the short corner or mid-post [MB3]. Later options: the page cut off (unverified beyond the entry).
- **Detection signature [HEURISTIC]:** slot → wing `PASS`; the passer's path crosses the lane (sign of x flips) and ends in the far corner within 3.5 s; `POST_ENTRY` from the wing to r 2–4.5 m within 2 s of the wing catch. Distinguish from T01 (Triangle speed cut): here the passer goes to the **opposite** corner.
- **Teams documented:** Princeton family [MB3]. MSU: none found.
- **Sources:** [MB3].
- **Confidence:** medium (entry); low (later options).

### G05. Forwards Out (Princeton)

- **Name and aliases:** "Forwards Out"; usable from any series (Hooper University) [MB2]. Related: O06/O07 MSU Forwards Out and F08 UConn Forwards Out Zoom (link unverified).
- **Family:** F3 two-guard front; personnel-inverting entry (forwards to the slots).
- **Start alignment:** 2-guard-front template [MB2].
- **Roles:** 1 handler; strong-side forward receives the DHO or pass; guards and forwards exchange.
- **Ordered actions:**
  1. t0: 1 runs a slot-to-wing DHO with the strong-side forward, or passes to that forward at the wing and cuts through to the strong-side corner (0–2.5 s).
  2. The weak-side forward and guard also exchange, so both forwards end up in the slots (2–5 s); any series (Chin, Point) then starts from the inverted alignment [MB2].
- **Usual counters:** not stated.
- **Detection signature [HEURISTIC]:** 2-guard front at t0; within 5 s the two players who were on the wings (θ 25–45° and 135–155°) occupy the slots (θ 60–80° and 100–120°, r 6.75–8.2 m) and the two slot guards occupy wing or corner spots. Needs player identity: the role swap is the label (with heights known, the two tallest perimeter players end in the slots).
- **Teams documented:** Princeton family [MB2]. MSU: none found for this generic version.
- **Sources:** [MB2].
- **Confidence:** medium.

### G06. Blast (MSU) [MSU] [NAME COLLISION: repo "Blast" = strong-side corner backdoor inside Horns Stagger]

- **Name and aliases:** "Michigan State Blast". Store as `MSU_Blast`.
- **Family:** F3 two-guard front → F8 pin-downs / floppy.
- **Start alignment (inferred):** guards 1 and 2 in the SLOTS (7.62, 66.8 / 113.2); 4 and 5 inside on the BLOCKS (2.04, 26.2 / 153.8); 3 spot-up; exact spots unverified.
- **Roles:** guards cutters and shooters; 4 pop-out receiver, then pin-down screener; 5 pin-down screener and slip man.
- **Ordered actions:**
  1. t0: guard-to-guard pass (0–1.0 s).
  2. 4 pops out to receive (1.0–2.5 s).
  3. Both guards dive to the rim (2.0–3.5 s).
  4. Single option: guards come off same-side pin-downs, bigs look to slip. "X" / Floppy option: guards cross and come off the opposite pin-downs (3.5–6.0 s) [MA23].
- **Usual counters:** big slips when the guard defenders cheat the pin-down [MA23].
- **Detection signature [HEURISTIC]:** `PASS(slot→slot)` (|Δx| 3.5–6.5 m, both at r 7–8.2 m); a big moves from r < 3 m to r ≥ 6.75 m and catches within 2.5 s; both guards reach r < 2 m within 1.5 s of that catch; each guard exits off a down `SCR`; "X" variant = the two guard paths cross x = 0 at y < 1.5 m before the screens.
- **Teams documented:** **Michigan State 2014-15** (several times vs Georgia, NCAA; the page calls it a set Izzo has run for years) [MA23].
- **Sources:** [MA23].
- **Confidence:** medium.

### G07. Ear / Hip / Nose / Weakside Flash (Princeton entries) [RICHER VARIANT of the repo's Princeton entries]

- **Name and aliases:** "Ear", "Hip", "Nose" (Ear-Nose-Hip series, Mark Lane, Ohio Express); "Weakside Flash" (Lee DeForest) (Coach's Clipboard) [MA10]. Four named entries in one block.
- **Family:** F4.1 Princeton → F3 two-guard front entries.
- **Start alignment:** 1 and 4 in the SLOTS (7.62, 66.8 / 113.2) (in Ear, 1 passes to 4 at a guard spot); 2 and 3 on the wings at FTX (7.32, 34.9 / 145.1); 5 at the HIGH POST (4.39, 78.2). Inferred from Princeton conventions on the page; diagrams unreadable [MA10].
- **Roles:** slot guards (passers, cutters, dribble-at); wings (back cutters); 5 high-post screener, pop-out hub, ball screener.
- **Ordered actions:**
  - Ear: t0 1→4; 1 cuts off 5's screen to the ball-side block looking for a pass from 2, then out to the left corner; 4 quickly→2; 2→1 inside first; else 4 cuts through or pops when 5 screens; dribble-at on 3 for a back cut (0–6 s).
  - Hip: 1 dribbles at 4, who cuts through; 5 pops out and catches; 1 screens for 3, who back-cuts (5→3); spacing refill; 5 passes to 1, follows and ball-screens; else 1 sets up a back cut for 2 (0–7 s).
  - Nose: 1 "waves" 4 through off a double screen by 2 and 5 at the backside elbow; dribble-at back cut for 3; 5 slips if X5 cheats; 5 runs off 2 (cut or pop) (0–7 s).
  - Weakside Flash (when 4 is denied): 2 flashes to the left elbow and catches; 4 cuts around 2 for a handoff; 5 flex-screens 3; 5 ducks in or pops; reset into Chin (0–7 s) [MA10].
- **Usual counters:** dribble-at backdoors; slips; Chin reset [MA10].
- **Detection signature [HEURISTIC]:** 2-guard-front `ALIGN`. Ear = the slot passer cuts **through the post screen** to the ball-side block within 1.5 s of passing. Hip = `DRIBBLE_AT` a teammate who cuts through, while the high post moves out to r ≥ 6.75 m. Nose = a slot player runs off a `DOUBLE` at the far elbow while the handler dribbles at the opposite wing, who back-cuts. Weakside Flash = the weak-side wing flashes to the elbow and catches, then a handoff cut around him.
- **Teams documented:** none at college level named (Ohio Express is AAU) [MA10].
- **Sources:** [MA10].
- **Confidence:** medium.

### G08. Michigan "Point Backdoor Triple Hand Off"

- **Name and aliases:** "Michigan Point Backdoor Triple Hand Off" (Coaching Toolbox, from Chris Filios's Hoop Scoop *Michigan Two Guard Front Offense Playbook*) [MB7].
- **Family:** F3 two-guard front → F6 handoff → F8 stagger.
- **Start alignment:** text gives no positions and the diagrams were unreadable; inferred 2-guard front (unverified): 1 right SLOT (7.62, 66.8), 2 left SLOT (7.62, 113.2), 3 and 4 on the wings (7.32, 34.9 / 145.1), 5 low post or elbow.
- **Roles:** 5 pop-out hub and DHO giver; 1 cutter off 5, then stagger screener; 2 cuts away, then stagger screener; 4 fills up, then back-cuts; 3 shooter / DHO receiver.
- **Ordered actions:**
  1. 5 pops out; 1→5 (0–2 s).
  2. 2 cuts away; 1 cuts off 5's screen (1.5–3.5 s).
  3. 4 fills up the floor, then back-cuts (2.5–4.5 s).
  4. 2 and 1 set a stagger for 3 (4–6 s).
  5. 5 runs a DHO with 3 (5.5–7.5 s) [MB7].
- **Usual counters:** not listed.
- **Detection signature [HEURISTIC]:** 2-guard front; a big moves out to r 5–7.5 m and catches from a slot guard; the passer cuts within 1.2 m of the big; a wing `CUT(backdoor)`s to r < 2 m within 3 s; two guards `STAGGER` for a wing, who takes a `DHO` from the big at r 5–7.5 m within 2 s.
- **Teams documented:** Michigan, John Beilein era; no season given [MB7]. Hoop Scoop associates the two-guard system with Richmond, West Virginia and Michigan [MB10]. MSU: none found.
- **Sources:** [MB7], [MB10].
- **Confidence:** medium (sequence); low (alignment).

### G09. Michigan "Pin Bump Single-Double"

- **Name and aliases:** "Pin Bump Single-Double" (same post and source as G08) [MB7].
- **Family:** F3 two-guard front → F8 pin-down / single-double.
- **Start alignment:** inferred 2-guard front (unverified): 1 and 2 in the SLOTS, 3 and 4 on the wings, 5 low.
- **Roles:** 1 reverser, then bump cutter; 2 corner cutter, then double-screen user; 5 spin-out pin screener; 3 back-cutter, then single-screen user; 4 wing receiver and single screener.
- **Ordered actions:**
  1. 1 reverses to 2; 2→4; 2 cuts to the ball-side corner (0–3 s).
  2. 1 bumps off 5; 4→1 (2.5–4.5 s).
  3. 5 spins out and pins down for 3, who back-cuts (4–6 s).
  4. Staggered double for 2; 3 comes off a single screen from 4 (5.5–8 s) [MB7].
- **Usual counters:** single vs double choice for the shooters [MB7].
- **Detection signature [HEURISTIC]:** guard-to-guard reversal, guard → wing pass, passer to the ball-side corner (θ ≤ 12°); the weak-side guard's path passes within 1.2 m of the post (bump); the post rotates ≥ 120° in place, then sets a down `SCR`; the pin-down target `CUT(backdoor)`s; two shooters come off one-screen and two-screen actions on opposite sides within 3 s.
- **Teams documented:** Michigan (Beilein); no season [MB7]. MSU: none found.
- **Sources:** [MB7].
- **Confidence:** medium-low.

### G10. Michigan "Reverse" (shuffle, then back screen)

- **Name and aliases:** "Michigan Wolverines Reverse" (Coaching Toolbox, from the *NCAA Top Offensive Minds Playbook* and the *2 Guard Front Playbook*) [MB8].
- **Family:** F3 two-guard front → F8 shuffle cut + back screen.
- **Start alignment:** 2 Guard Front: 1 and 2 in the SLOTS; 3 and 4 on the wings or blocks (inferred); 5 high (inferred, unverified).
- **Roles:** 1 passer, corner cutter; 4 to the block, then shuffle and back screener; 5 step-out hub, reverser, back-screen cutter; 2 shuffle cutter.
- **Ordered actions:**
  1. 1→2; 1 cuts to the corner (0–2 s).
  2. 4 cuts to the block; 5 steps out and receives (1–3 s).
  3. 2 cuts off a shuffle screen from 4 (2.5–4.5 s).
  4. 5 reverses to 1; 5 cuts off a back screen from 4 (4–6.5 s) [MB8].
- **Usual counters:** not listed.
- **Detection signature [HEURISTIC]:** guard-to-guard pass with the passer to the corner; a big steps out to r 5–7.5 m and catches; a guard cuts diagonally from the slot toward the opposite block past a stationary screener at r 2–4 m (shuffle); the same screener then back-screens the stepped-out big, who reaches r < 2 m within 2 s of his reversal pass.
- **Teams documented:** Michigan; no season given [MB8]. MSU: none found.
- **Sources:** [MB8].
- **Confidence:** medium-low.

### G11. Michigan backdoor-screen spread (vs Indiana, 2012)

- **Name and aliases:** no set name; UM Hoops calls them backdoor-screen actions within Michigan's base offense [MB9].
- **Family:** F4.2 motion (Beilein two-guard / spread) → F8 back screen ("backdoor screen").
- **Start alignment:** spread with both CORNERS filled (6.81, 3.4 / 176.6); other spots not given [MB9].
- **Roles:** Burke passer and thru-cutter; Douglass second passer, then cutter off a back screen; Morgan screener for both; Hardaway wing passer.
- **Ordered actions:**
  1. Burke→Douglass; Burke cuts through the paint using Morgan's first screen (0–2 s).
  2. Douglass→Hardaway on the wing; Douglass comes off Morgan's second screen shoulder to shoulder (2–4 s).
  3. Hardaway→Douglass for the backdoor alley-oop at the elbow area [MB9].
  - Play 2: Hardaway passes to the wing, Smotrycz screens for him, and Hardaway runs through without a V-cut for a lob [MB9].
- **Usual counters:** not stated.
- **Detection signature [HEURISTIC]:** two consecutive passer-cutters use the **same** stationary screener within 4 s; the second cutter reaches r < 2 m off a back `SCR` and catches a `LOB` from the wing.
- **Teams documented:** Michigan 2011-12 (vs Indiana; posted 2012-02-03). UM Hoops says Michigan ran nearly the same play at home against **Michigan State** in 2010-11 with Darius Morris passing: MSU was the defending team, not the runner [MB9].
- **Sources:** [MB9].
- **Confidence:** medium.

### G12. Stephen F. Austin two-guard "push and stagger"

- **Name and aliases:** "Stephen F. Austin (SFA) Play" (Coaching Toolbox, same playbooks as G10) [MB8].
- **Family:** F3 two-guard front → F8 baseline stagger to the corner + down screen.
- **Start alignment:** 2 Guard Front: 1 and 2 in the SLOTS; 3 on the right wing (7.32, 34.9); 4 on the left wing (7.32, 145.1); 5 high (inferred, unverified).
- **Roles:** 1 dribbler who pushes 3; 3 stagger user to the corner; 2 and 4 stagger screeners; 5 down screener for 2.
- **Ordered actions:**
  1. 1 dribbles right, pushing 3 into the lane (0–2 s).
  2. 4 cuts to the corner; 2 cuts to the block (1–3 s).
  3. 3 runs off a stagger from 2 and 4 to the corner (2.5–4.5 s).
  4. 5 down-screens for 2 (4–6 s) [MB8].
- **Usual counters:** not listed.
- **Detection signature [HEURISTIC]:** `DRIBBLE_AT` the wing that makes the wing move to r < 4 m (push) instead of a backdoor; the pushed player runs along y < 1.5 m to the far corner past a `STAGGER`; a down `SCR` for one of the stagger screeners within 2 s.
- **Teams documented:** Stephen F. Austin; no season [MB8]. MSU: none found.
- **Sources:** [MB8].
- **Confidence:** medium-low.

---

## 10. Triangle family (F4.1 Triangle)

The repo has one Triangle paragraph (sideline triangle and pinch post). The named entries below are absent. General source: HoopStudent Triangle offense [MB14], which names USC (Sam Barry originated the system; Tex Winter played there), Kansas State (where Winter developed it), the Chicago Bulls (titles 1991–93, 1996–98) and the Los Angeles Lakers (titles 2000–02, 2009–10). No D-I program in the current era and no MSU usage is documented for these entries. Spacing in the source is **4.6–6.1 m** (3.7–4.6 m for youth and high school; the source gives imperial values, converted to metres) [MB14]. The "line of deployment" puts 5 between the basket and the wing (3) [MB14].

**Template start** ("Triangle template", before the first pass): 1 at the right SLOT (7.62, 66.8) with the ball; 3 on the right wing at FTX (7.32, 34.9) (the trigger); 5 at the right BLOCK (2.04, 26.2); 2 at TOP or the weak-side SLOT (7.62, 113.2); 4 at the weak-side wing or HIGH POST / left ELBOW (4.57, 113.6). Sideline triangle after the first pass: 3 at the wing, 1 in the strong-side CORNER (6.81, 3.4), 5 at the block.

### T01. Speed-cut entry (forms the sideline triangle)

- **Name and aliases:** first pass plus speed cut; "guard outside cut" (search-snippet wording, unverified) [MB14].
- **Family:** F4.1 Triangle; formation entry.
- **Start alignment:** Triangle template.
- **Roles:** 1 first passer and speed cutter; 3 trigger (key passer); 5 post; 2 weak-side guard; 4 weak-side forward.
- **Ordered actions:**
  1. t0: 1→3, the first pass.
  2. 1 cuts straight to the basket (speed cut, 0–1.5 s); if not open, he continues to the strong-side corner, forming the sideline triangle 3–1–5 (1.5–3 s).
  3. 3 reads in order: 5 (post), 2, 4 (cutting to the strong-side high post), 1 [MB14].
- **Usual counters:** low-post options (split by 2 and 3, screen-the-screener by 4), pinch post (T06), solo cut (T02) [MB14].
- **Detection signature [HEURISTIC]:** slot → wing `PASS`; the passer `CUT`s to r < 2 m within 1.5 s, then exits to the **same-side** corner (θ ≤ 12° on the ball side); at t0 + 3 s three players form a strong-side triangle: one at r 6.5–8 m, θ 25–55°; one at θ ≤ 12°; one at r 2–3.5 m, θ 15–50°; the post lies within 1.0 m of the rim → wing line. Distinguish from G04 (Princeton Low) by the corner side.
- **Teams documented:** see the section header [MB14].
- **Sources:** [MB14].
- **Confidence:** high.

### T02. Solo cut

- **Name and aliases:** "solo cut"; related terms in the source: "freeze spot", "garden spot", "fan cut", "action-zone speed cut" [MB14].
- **Family:** F4.1 Triangle → F8.2 cut; wing back-cut off a post handoff.
- **Start alignment:** as T01 after the first pass; 4 near the weak-side low post (BLOCK 2.04, 153.8) [MB14].
- **Roles:** 1 speed cutter to the weak-side corner; 4 rub screener at the freeze spot; 3 solo cutter; 5 post handoff; 2 fan cut to the garden spot (weak-side wing).
- **Ordered actions:**
  1. t0: 1→3.
  2. 1 speed-cuts to the **weak-side** corner off a rub screen from 4 near the weak-side post (0–2 s).
  3. 3 solo-cuts to the basket and takes a handoff from 5 for the layup (1.5–3.5 s).
  4. 2 fan-cuts to the weak-side wing for a three [MB14].
- **Usual counters:** Example 2: 1 solo-cuts to the corner, and 4 cuts into the lane from the freeze spot off 3's screen for a pass from 5 [MB14].
- **Detection signature [HEURISTIC]:** slot → wing `PASS`; the passer crosses the lane to the opposite corner past a `SCR` by a player at r 2–3 m, θ 150–175°; within 2 s the wing receiver passes to the post (r < 3.5 m) and cuts past him to r < 1.5 m for a `DHO`; the weak-side guard moves out to the weak-side wing.
- **Teams documented:** see the section header [MB14].
- **Sources:** [MB14].
- **Confidence:** medium-high.

### T03. Corner series (banana cut plus corner ball screen)

- **Name and aliases:** corner options; "banana cut"; "corner ball screen" [MB14].
- **Family:** F4.1 Triangle → F5 ball screen at the corner.
- **Start alignment:** sideline triangle formed: 1 in the right CORNER (6.81, 3.4); 3 on the right wing (7.32, 34.9); 5 at the right BLOCK (2.04, 26.2) [MB14].
- **Roles:** 1 corner handler; 3 banana cutter; 5 back screener, then corner ball screener; 4 pops to the left corner.
- **Ordered actions:**
  1. The ball goes to 1 in the corner.
  2. 3 banana-cuts off a back screen from 5, with a pass from 1 if open (0–2 s); otherwise 3 continues to the left wing and 4 pops to the left corner.
  3. 5 sets a corner ball screen; 1 dribbles toward the lane and 5 rolls (2–5 s).
  4. For continuity, 5 goes to the left block to re-form the triangle [MB14].
- **Usual counters:** kick-out to 3 or 4 [MB14].
- **Detection signature [HEURISTIC]:** ball at θ ≤ 12°, r 6.5–7.2 m; a wing teammate `CUT`s on a curved path (radius 2–4 m) to r < 2 m past a stationary `SCR` from the block player; then a ball `SCR` for the corner handler at r 5.5–7 m, θ 3–15° ≤ 4 s later. Discriminator: ball screens at θ ≤ 15° are rare elsewhere.
- **Teams documented:** see the section header [MB14].
- **Sources:** [MB14].
- **Confidence:** medium.

### T04. Wing reverse and guard squeeze (pressure release)

- **Name and aliases:** "wing reverse"; part 2 "guard squeeze action" [MB14].
- **Family:** F4.1 Triangle → F3 entry vs denial.
- **Start alignment:** 1 at TOP (7.60, 90.0) under pressure; 3 on the wing (7.32, 34.9) denied; 5 at the strong-side BLOCK (2.04, 26.2); 2 and 4 weak side [MB14].
- **Roles:** 5 high-post receiver, then safety at the top; 3 backdoor stepper; 2 squeeze cutter; 1 top screener, then fan cut; 4 brush screener.
- **Ordered actions:**
  1. t0: 5 lifts to the strong-side high post (0–1.5 s) and receives from 1.
  2. 3 backdoor-steps to the basket for a pass from 5 (1–2.5 s); if not open, 3 cuts to the left corner off 4's brush screen.
  3. Squeeze: 2 cuts to 5 off 1's top screen and takes a handoff for the layup (2.5–4.5 s); if not, 2 goes to the right short corner and 1 fans to the garden spot for a skip three; 5 pops to the top as a safety [MB14].
- **Usual counters:** built in, as above [MB14].
- **Detection signature [HEURISTIC]:** the block player moves to the elbow (r 2.0 → 4.3–5.0 m, same sign of x) and catches from the top; within 1.5 s the strong-side wing `CUT(backdoor)`s to r < 2 m; then a `SCR` by the original passer at r 6–8 m near the top, used by the weak-side guard, who takes a `DHO` from the elbow big (r 3.5–5.0 m) within 2 s.
- **Teams documented:** see the section header [MB14].
- **Sources:** [MB14].
- **Confidence:** medium.

### T05. Lag-pass entry and center opposite

- **Name and aliases:** "lag principle", "lag pass"; related terms "line of truth", "moment of truth", "center opposite" [MB14].
- **Family:** F4.1 Triangle; guard-to-guard pressure-release entry.
- **Start alignment:** 1 with the ball at TOP or a SLOT, unable to make the first pass; 2 in the other SLOT (7.62, 113.2) [MB14].
- **Roles:** 2 lag receiver; 1 corner cutter; 4 wing fill; 3 back cutter; 5 cross-screen user.
- **Ordered actions:**
  1. If the wing is not open when the defender reaches the "line of truth" (about 0.9 m in front of the handler's defender; source value converted from imperial) [MB14], 1 makes the lag pass to 2, who stays behind the line of truth.
  2. 1 cuts to the left corner, which triggers 4 to the left wing (0–2 s).
  3. 2 dribbles and passes to 4; 3 cuts to the basket off 2's screen (2–4 s).
  4. If 3 is not open, 5 cuts to the left block off 3's cross screen, re-forming the triangle (4–6 s).
  - Center opposite: the weak-side centre stays opposite while the weak-side wing cuts to the strong-side low post [MB14].
- **Usual counters:** Example 2: 4 receives, 5 goes to the block off 2's cross screen, 4→5, and 4 cuts baseline for a handoff [MB14].
- **Detection signature [HEURISTIC]:** guard-to-guard `PASS` (both at r 7–8.5 m, θ 55–125°) **before** any wing entry; the passer cuts to the corner on the receiver's side within 2 s; a weak-side forward moves to the wing on that side; a cross `SCR` at y < 2 m brings a big to the new strong-side block within 6 s of t0. Center opposite: the post stays at the opposite sign of x to the ball while a wing becomes the strong-side post.
- **Teams documented:** see the section header [MB14].
- **Sources:** [MB14].
- **Confidence:** medium.

### T06. Pinch-post two-man game with rebound screen cut [RICHER VARIANT of "Pinch post" (F7)]

- **Name and aliases:** pinch post (Triangle); "rebound screen cut" [MB14].
- **Family:** F4.1 Triangle → F7 pinch post.
- **Start alignment:** sideline triangle formed: 3 on the right wing (7.32, 34.9), 1 in the right CORNER (6.81, 3.4), 5 at the right BLOCK (2.04, 26.2); 2 at TOP (7.60, 90.0); 4 at the weak-side high post / left ELBOW (4.57, 113.6) [MB14].
- **Roles:** 2 top guard and handoff receiver; 4 pinch-post hub; 3 rebound-screen cutter who sets a wide pin-down for 1; 1 shooter off the pin-down.
- **Ordered actions:**
  1. 3→2 at the top.
  2. 4 opens at the left high post and receives from 2 (0–1.5 s).
  3. 2 cuts to the basket and takes a handoff from 4 (1–3 s).
  4. 3 feints toward the rebound, then sets a wide pin-down for 1, who cuts to the top; 3 then fills the empty right corner (2–4.5 s) [MB14].
- **Usual counters:** if 4 is denied, 2 dribbles to the right wing and 1 comes off 3's rebound screen cut into a DHO from 2 [MB14].
- **Detection signature [HEURISTIC]:** the weak-side elbow player (θ 105–125° with the ball on the right) catches from the top; the passer cuts past him within 1 s and takes a `DHO` at r 2.5–4.5 m; concurrently the strong-side wing moves toward the rim (r falls ≥ 2 m), then sets a `SCR` for the corner player, who exits to the top (θ from ≤ 12° to 60–90°).
- **Teams documented:** see the section header [MB14].
- **Sources:** [MB14].
- **Confidence:** medium.

### T07. Guard quickie

- **Name and aliases:** "guard quickie" (HoopStudent; a Triangle PnR option) [MB14].
- **Family:** F4.1 Triangle → F5 ball screen.
- **Start alignment:** Triangle template.
- **Roles:** 1 speed cutter off a back screen; 5 back screener, then ball screener; 3 wing handler; 2 fan cut; 4 to the corner.
- **Ordered actions:**
  1. t0: 1→3.
  2. 1 speed-cuts to the basket off 5's back screen; 4 cuts to the right corner (0–2 s); if not open, 1 exits to the left corner.
  3. 3 dribbles to the middle off 5's ball screen, and 5 rolls (2–4.5 s).
  4. 2 fans to the garden spot for a three [MB14].
- **Usual counters:** as above [MB14].
- **Detection signature [HEURISTIC]:** slot → wing `PASS`; the passer `CUT`s to r < 2 m past a stationary `SCR` by the block player, who has moved up to r 3–5 m within 1.5 s; the **same** screener then sets a ball `SCR` for the wing at r 6–7.5 m within 2.5 s (veer-like: same screener, off-ball then on-ball, ≤ 3 s apart).
- **Teams documented:** see the section header [MB14].
- **Sources:** [MB14].
- **Confidence:** medium.

---
## 11. 3-out 2-in family (F3.1 / F4.2)

**Template start** ("3-out 2-in template"): handler at TOP (7.60, 90.0) or a SLOT; wings at FTX (7.32, 34.9 / 145.1); two bigs on the BLOCKS (2.04, 26.2 / 153.8). Discriminator: two players at r < 3 m (`offense_full.md` §3.1). No MSU usage found for any item in this section.

### R01. Corey (Maggette) cut quick hitter

- **Name and aliases:** "Corey cut", "Maggette cut" (HoopStudent; named after the NBA player Corey Maggette) [MB25].
- **Family:** F3 3-out 2-in → F5 middle ball screen → F8 cut to the lane line.
- **Start alignment:** 3-out 2-in template [MB25].
- **Roles:** 1 handler; 5 ball screener; 2 right-wing receiver and passer; 3 Corey cutter; 4 right-corner kick-out target.
- **Ordered actions:**
  1. 1 dribble-enters to the left wing; 3 drops to the left corner and 4 cuts to the right corner (0–2 s).
  2. 5 lifts to set a ball screen; 1 uses it to the middle, then passes to 2 on the right wing (2–4.5 s).
  3. 3 moves up from the corner, then cuts toward the left lane line (the Corey cut).
  4. 2 passes when 3's feet touch the lane line below the FT line (the source's own spatial cue: |x| = 1.83 m, y < 4.19 m).
  5. 3 shoots a mid-range shot or floater, attacks, or kicks out to 4 [MB25].
- **Usual counters:** kick-out to 4 in the corner [MB25].
- **Detection signature [HEURISTIC]:** a middle ball `SCR`, then a `PASS` to the opposite wing; within 1.5 s a player who was in the far corner lifts ≥ 1.5 m (θ toward 90°), then cuts toward the lane line and catches with |x| ≤ 2.0 m and y < 4.19 m, ≥ 2.5 m from the rim (not a rim cut).
- **Teams documented:** none named [MB25].
- **Sources:** [MB25].
- **Confidence:** medium.

### R02. 3-out 2-in "Wing series" (shuffle, then stagger, then elevator)

- **Name and aliases:** "Wing series" (HoopStudent) [MB25].
- **Family:** F3 3-out 2-in → F8 shuffle, stagger and elevator chain.
- **Start alignment:** 3-out 2-in template [MB25].
- **Roles:** 1 dribble entry; 2 thru-cutter to the right corner, then stagger user; 4 lifts to the top, then stagger and elevator screener; 3 shuffle cutter, then elevator user; 5 shuffle screener, then stagger and elevator screener.
- **Ordered actions:**
  1. 1 dribble-enters to the left wing; 2 cuts through to the right corner; 4 lifts from the left post to the top (0–2.5 s).
  2. 3 shuffle-cuts off 5's screen just outside the right elbow, with a pass from 1 at the rim (2–4 s).
  3. 4 and 5 stagger toward the right corner; 2 comes to the top for three (4–6.5 s).
  4. If no shot, 4 and 5 set an elevator in the lane for 3 back to the right wing, then crash the glass (6–9 s) [MB25].
- **Usual counters:** built-in chain [MB25].
- **Detection signature [HEURISTIC]:** ordered chain within 9 s of t0: dribble entry to a wing; opposite wing → corner; a low post lifts to TOP; a diagonal `CUT` past a `SCR` at r 4–5.5 m, θ 55–75° to r < 2 m; a `STAGGER` for the corner player to TOP; an elevator (`DOUBLE` closing to < 0.6 m) near the lane.
- **Teams documented:** none named [MB25].
- **Sources:** [MB25].
- **Confidence:** medium.

### R03. Cross (Breakthrough): wing cross, posts flash high

- **Name and aliases:** "Cross" (Breakthrough) [MA83]. Different from repo Box Cross and from L01.
- **Family:** F3 3-out 2-in → F8 cross cuts, flash → F6 → F5 big-big PnR.
- **Start alignment:** 1 TOP (7.60, 90.0); 2 right WING (7.50, 45.0); 3 left WING (7.50, 135.0); 4 left BLOCK (2.04, 153.8); 5 right BLOCK (2.04, 26.2) [MA83].
- **Roles:** 2 and 3 crossing wings (3 then backdoors); 4 and 5 high-post flashers; 1 passer, then FT-line cutter and DHO receiver.
- **Ordered actions:** t0 2 and 3 cross; 4 and 5 cut to the high post; 1 passes to 4 or 5 (0–2 s); 3 backdoors (2–3.5 s); else 3 to the far corner, 1 cuts to the FT line, then off 5 for a DHO (5 may fake and attack) (3.5–6 s); else 4 ball-screens 5 (big-big PnR); if no high-post entry: 1 enters to the wing, 5 screens 4, 4 ball-screens 3 [MA83].
- **Usual counters:** fake DHO; big-big PnR [MA83].
- **Detection signature [HEURISTIC]:** both wings' paths cross x = 0 while both blocks rise to y 3.5–5 m within 1.5 s; `PASS(TOP→high post)`; a wing `CUT(backdoor)` within 1.5 s.
- **Teams documented:** none named [MA83].
- **Sources:** [MA83].
- **Confidence:** medium.

### R04. "Kentucky" (Wildcat) lob

- **Name and aliases:** "Kentucky" / Wildcat lob (Breakthrough; man and zone versions) [MA79]. Team usage by Kentucky unverified (name only).
- **Family:** F3 3-out 2-in → F8 high-post back screen → lob.
- **Start alignment:** 3-out 2-in template [MA79].
- **Roles:** 1 passer and lob cutter; 3 wing receiver and lob passer; 2 deep cutter to the strong corner; 5 flash to the high post, back screener; 4 low post, later back screener for 2.
- **Ordered actions:** 1→3; 2 deep-cuts to the strong corner; 5 flashes high and screens 1 for a lob from 3; 1 clears; 3→2 (shoot, drive or post 4); swing; 5 drives or ducks in for 4; 4 back-screens 2 [MA79].
- **Usual counters:** swing options [MA79].
- **Detection signature [HEURISTIC]:** a post flashes to the high post and **back-screens the passer** within 1.0 s; `LOB` to r < 1.5 m.
- **Teams documented:** none confirmed [MA79].
- **Sources:** [MA79].
- **Confidence:** medium.

---

## 12. Post-entry starts: wing, low post and top (F7 post + perimeter)

**Template start** ("post-entry template"): ball on the wing at FTX (7.32, 34.9); a teammate at the same-side BLOCK (2.04, 26.2); a player at TOP (7.60, 90.0) or the SLOT (7.62, 66.8); the other two spaced on the weak side. The repo has "Post split" as a one-liner (F7, Villanova). No MSU usage found for any item in this section.

### P01. Straight Split [RICHER VARIANT of "Post split" (F7)]

- **Name and aliases:** "Straight Split" (FIBA Europe terminology) [MB1]; "split action", "post split" (HoopStudent) [MB41]; NBA alias Golden State "Split" [MB29].
- **Family:** F7 post + perimeter.
- **Start alignment:** post-entry template ("the player on the wing spot… the player on the top of the key", FIBA) [MB1].
- **Roles:** wing = entry passer, then screener; top player = cutter; post = hub.
- **Ordered actions:**
  1. t0: the wing feeds the low post (`POST_ENTRY`).
  2. The wing passer sets a screen for the player at the top (0.3–1.8 s after the entry).
  3. The top player uses it toward the vacated wing for a shot, or rejects and back-cuts for a pass from the post (1–3 s) [MB1][MB41][MB29].
- **Usual counters:** screener slips to the rim if both defenders take the shooter or switch [MB29][MB41]; screener pops if his defender helps on the ball [MB41]; the post goes 1-on-1 into the space the split opens [MB41].
- **Detection signature [HEURISTIC]:** `POST_ENTRY` from a wing (r 6.5–8 m, θ 25–55° / 125–155°) to r < 3.5 m; within 1.8 s the **passer** becomes a stationary `SCR` at r 6–8 m between the wing and the top (θ 45–80° / 100–135°); the top player's path passes within 1.2 m of that screen toward the wing, or `CUT(backdoor)` to r < 2 m. Straight vs Reverse rule: screener = entry passer.
- **Teams documented:** Villanova favours splitting and slipping the screener (Hooper GSW page) [MB29]; HoopStudent credits a two-guard high-post version to Dana Altman's book *The Complete Guide to the High Post Offense vs. Any Defense* [MB41]; NBA: Golden State Warriors "Split", including "double drag + split" [MB29]. MSU: none found.
- **Sources:** [MB1], [MB41], [MB29].
- **Confidence:** high (definition); medium (team usage).

### P02. Reverse Split [RICHER VARIANT of "Post split"]

- **Name and aliases:** "Reverse Split" (FIBA Europe) [MB1]; the "screen from the top" option (HoopStudent) [MB41].
- **Family:** F7 post + perimeter.
- **Start alignment:** post-entry template.
- **Roles:** wing = entry passer, then cutter; top player = screener; post = hub.
- **Ordered actions:**
  1. t0: the wing feeds the post.
  2. The **top player** comes down and screens for the entry passer (0.3–1.8 s).
  3. The entry passer uses the screen to the top for a shot ("2 move to the top to receive from 3 and shoot"), or curls or back-cuts [MB1][MB41].
- **Usual counters:** screener slip or pop, as in P01 [MB41].
- **Detection signature [HEURISTIC]:** as P01, but the `SCR` is set by the player who was at the top (r 7–8.5 m, θ 70–110° at t0), and the entry passer is the cutter, moving from the wing toward TOP (θ toward 90°) or to r < 2 m.
- **Teams documented:** generic (FIBA) [MB1]. MSU: none found.
- **Sources:** [MB1], [MB41].
- **Confidence:** high (definition).

### P03. Laker cut (high side and low side)

- **Name and aliases:** "Laker cut" (HoopStudent; attributed to the Showtime-era Lakers) [MB35]. FIBA and the repo have no entry.
- **Family:** F7 post + perimeter; also F8.2 cut after a post entry.
- **Start alignment:** 1 at the right SLOT (7.62, 66.8); 3 on the right wing (7.32, 34.9); 5 at the right BLOCK (2.04, 26.2); others spaced on the weak side [MB35].
- **Roles:** 3 entry passer, then cutter; 5 post (return pass or handoff).
- **Ordered actions:**
  1. t0: 1→3.
  2. 3 enters to 5 (0.5–2 s).
  3. 3 cuts past the post 0–1.0 s after his entry pass: **high side** (through the lane near the elbow; generally preferred) or **low side** (along the baseline; more practical against no-middle defence).
  4. 5 returns the ball (high side) or hands off / short-passes (low side) for a layup (1–2.5 s) [MB35].
- **Usual counters:** if the cutter comes too close on the high side, the wing defender can dig or double; the low-side cut beats no-middle [MB35]. "A player can Laker-cut herself" when the cut is blocked: Better Basketball search snippet only (unverified; page not opened).
- **Detection signature [HEURISTIC]:** `POST_ENTRY` wing → block; the entry passer starts a `CUT` ≤ 1.0 s after release toward r < 2 m: **high side** if the path's minimum distance to the ELBOW is < 1.5 m or it passes above the post (y_path > y_post + 1.0 m); **low side** if the path stays at y < y_post and |x| decreases along the baseline (θ ≤ 15°); a return `PASS` or `DHO` post → cutter within 1.5 s ends the action (without a return, label "Laker cut (decoy)"). Distinguish from P01/P02: no stationary screen by the passer.
- **Teams documented:** Los Angeles Lakers, Showtime era (NBA, secondary alias) [MB35]. MSU: none found.
- **Sources:** [MB35], [MB30].
- **Confidence:** high (definition); low (college usage).

---

## 13. 2-1-2 / 1-3-1 family (F3.1 / F4.1)

### W01. Wheel offense (Pinholster) [NAME COLLISION with X01 Spurs Wheel and U20 Duke Wheel Action]

- **Name and aliases:** "Wheel offense" (Garland Pinholster, Oglethorpe, late 1950s) [MB17][MB18]. Not the same as Blocker-Mover or Witherspoon's continuity ball screen (repo F4.1).
- **Family:** F4.1 pattern continuity.
- **Start alignment:** Wikipedia: a 2-1-2 with two players "edge to edge at the free throw lane", becoming a 1-3-1 with the ball on the wing [MB18]; HoopStudent: "generally starts with a slot to wing pass" [MB17]. Template (2-1-2 phase): SLOTS (7.62, 66.8 / 113.2), NAIL (4.19, 90.0), BLOCKS (2.04, 26.2 / 153.8).
- **Roles (HoopStudent numbering):** 1 and 2 guards; 5 back screener; 3 back-screen cutter; 1 and 4 stagger screeners.
- **Ordered actions:**
  1. t0: 1→2 at the wing (2 V-cuts to get open).
  2. 5 sets an angled back screen for 3, who cuts to the basket; 2→3 for the layup (0.5–2.5 s); otherwise 3 fill-cuts to the low post.
  3. 1 and 4 set a stagger for 5, who cuts toward the ball for a jumper; or 2→3 posting (2.5–5 s).
  4. If 2 holds, reverse 2→4→1; 3 back-screens for 2, then a stagger for 3 on the other side (5–10 s); repeat [MB17].
  - Wikipedia's wording of the cycle: the first cutter gets a screen from the low post, passes to the top, and cuts baseline or over the top; the fourth cutter swings, then screens for the second cutter across the FT line; the third cutter (double-screening in the lane) breaks to the top; the formation returns to 1-3-1 on the other side [MB18].
- **Usual counters:** fill cuts [MB17]; reset to 1-3-1 [MB18].
- **Detection signature [HEURISTIC]:** slot → wing `PASS`; within 1.5 s a back `SCR` whose axis is 30–60° off the baseline, cutter to r < 2 m; then a `STAGGER` for the back screener, who moves toward the ball to r 4.5–6.5 m within 2.5 s; after a `REVERSAL`, the mirror of the same pattern within 10 s → "Wheel continuity" (≥ 2 cycles). Distinguish from Flex: the first screen is an angled back screen from the post, not a baseline flex screen.
- **Teams documented:** Oglethorpe (Pinholster), late 1950s (not D-I) [MB17][MB18]. MSU: none found.
- **Sources:** [MB17], [MB18].
- **Confidence:** medium (the two sources differ in detail).

---

## 14. Elbow / high-post entries (F3.4; start alignment varies)

A big pops to an elbow and catches from the top, then the passer acts away. The sources do not show a full five-player start, so spots are inferred.

### E01. Elbow Away STS [MSU]

- **Name and aliases:** "Elbow Away STS". The page says MSU runs many "Elbow" actions [MA27]. Distinct from Gonzaga "Elbow" (double pin-downs, repo) and O10.
- **Family:** F3.4 elbow entries → F8 screen away, screen for the post, screen-the-screener.
- **Start alignment (inferred):** 1 TOP (7.60, 90.0); 5 starts low and pops to an ELBOW (4.57, 66.4); 4 low on the weak side (BLOCK 2.04, 153.8), lifts to the top; 2 in the CORNER (6.81, 3.4); 3 not mentioned.
- **Roles:** 5 elbow catcher, then post target; 1 away screener, then screener for 5, then cutter to the top; 4 screened player and reverser, then STS screener; 2 corner-to-wing receiver and post feeder.
- **Ordered actions:**
  1. t0: 5 pops out to receive from 1 (0–1.5 s).
  2. 1 screens away for 4; 5 passes to 4 up top (1.5–3.0 s).
  3. 4 reverses to 2 cutting out of the corner (3.0–4.0 s).
  4. 1 cuts back to screen for 5, who cuts to the basket; 2 looks for 5 in the post (4.0–5.5 s).
  5. 1 comes to the top off 4's screen as the secondary option (5.5–7.0 s) [MA27].
- **Usual counters:** secondary option for 1 off 4's screen (STS) [MA27].
- **Detection signature [HEURISTIC]:** `PASS(TOP→elbow big)` with the big having moved ≥ 2 m up from r < 3 m; the passer sets an away `SCR` (opposite sign of x to the ball) within 1.5 s; `PASS(elbow→top)`; `PASS(top→wing)` to a player who left the corner (θ < 12° → 25–45°); the original passer screens the elbow big, who reaches r < 2 m; the screener is then screened and exits to r ≥ 6.75 m, θ 80–100°.
- **Teams documented:** **Michigan State**, published 2020-11-18 (season unverified) [MA27].
- **Sources:** [MA27].
- **Confidence:** medium.

### E02. Elbow Away Pindown [MSU]

- **Name and aliases:** "Elbow Away Pindown".
- **Family:** F3.4 elbow entries → F8 screen away, pin-down return for the point guard's three.
- **Start alignment (inferred):** 1 TOP (7.60, 90.0); 5 steps out to an ELBOW (4.57, 66.4); 4 weak side; 3 cuts to the opposite BLOCK (2.04, 153.8).
- **Roles:** 1 passer, away screener, shooter; 5 elbow hub and pin-down screener; 4 top receiver and passer; 3 clearing cutter.
- **Ordered actions:**
  1. t0: 5 steps out to the elbow and receives from 1 (0–1.5 s).
  2. 1 screens for 4; 3 cuts to the opposite block; 5 passes to 4 (1.5–3.0 s).
  3. After a brief pause, 1 cuts back to the top off 5's pin-down; 4 passes to 1 for the shot (3.5–5.5 s) [MA28].
- **Usual counters:** none listed.
- **Detection signature [HEURISTIC]:** as E01 for steps 1–2; then the elbow big sets a down `SCR` for 1 (1 moves +y from r 4–6 m to r ≥ 6.75 m, θ 70–110°), and 1 catches and shoots within 1.0 s. Distinguish from E01: no reversal to a corner player and no screen for the big.
- **Teams documented:** **Michigan State**, published 2020-11-18 (season unverified) [MA28].
- **Sources:** [MA28].
- **Confidence:** medium-high.

### E03. Elbow Special (decoy dive into wing backdoor)

- **Name and aliases:** "Elbow Special" (Vonn Read, via Coaching Toolbox) [MB5][MB6].
- **Family:** F3.4 elbow entry → F8 backdoor; used as an entry, a set ending or an end-of-game play.
- **Start alignment:** not given in the text (unverified). From the actions: 1 at TOP or a SLOT; 4 at an ELBOW (4.57, 66.4); 5 low or high on the strong side; 3 on the wing (7.32, 34.9).
- **Roles:** 1 elbow-entry passer, then corner cutter; 5 decoy diver; 4 elbow hub (decoy face-up); 3 backdoor cutter.
- **Ordered actions:**
  1. 1→4 at the elbow; 1 cuts hard to the corner (0–2 s).
  2. 5 dives hard to the strong-side block as a decoy, forcing X5 to play high side (1–2.5 s).
  3. 4 faces up and looks at 3 (decoy); 3 calls for the ball and steps toward it (2–3 s).
  4. If X3 bites, 3 back-cuts for the layup (2.5–4 s) [MB5].
- **Usual counters:** not listed beyond the X3 overplay read [MB5].
- **Detection signature [HEURISTIC]:** elbow catch (r 4.2–5.0 m); the passer goes to the corner; a big moves to the strong-side block (r < 2.5 m) within 1.5 s with its defender on the high side (defender y > big y + 0.5 m); the strong-side wing steps ≥ 1 m toward the elbow, then `CUT(backdoor)`s to r < 2 m within 1.5 s and catches from the elbow.
- **Teams documented:** none (Read is the author credited) [MB5]. MSU: none found.
- **Sources:** [MB5], [MB6].
- **Confidence:** medium.

---

## 15. Secondary / early-offense entries into the half court (F2 → F3)

These start from a transition shape (trailer, rim runner, wings running lanes) and flow straight into a half-court action. Use `PHASE` = early (about 4–12 s of possession, `offense_full.md` §0.2).

### S01. Motion Strong

- **Name and aliases:** "Motion Strong" (Spurs origin; the point guard flexes his bicep on the way up, hence "Strong") [MA15]. Paired with S02: the pass to the trailing big triggers Strong, the pass to the wing triggers Weak [MA14].
- **Family:** F2 secondary → F3 entry → F8 double stagger → flows into F3.2 Horns or an "Elbow Series" [MA15].
- **Start alignment (from the step text; spots inferred):** 1 at the SLOT (7.62, 66.8) with the ball; trailing big 4 at TOP / DEEP (7.60–9.80, 90.0); first big 5 at the ball-side BLOCK (2.04, 26.2); 2 on the ball-side wing (7.50, 45.0) or corner; 3 on the opposite wing (7.50, 135.0) [MA15].
- **Roles:** 1 passer, stagger screener; 4 trailer, reverser, stagger screener; 5 rim-run big who follows the ball across; 3 reversal receiver; 2 shooter off the double stagger.
- **Ordered actions:**
  1. t0: 1 passes to the trailing 4, not the wing (0–1.0 s).
  2. 4 reverses to the opposite wing 3; 5 follows the ball across (1.0–2.5 s).
  3. 1 and 4 set a double stagger for 2 on the opposite wing (2's original ball side, now the weak side after the reversal); 3 passes to 2 for a shot (2.5–5.0 s).
  4. If nothing: flow into Horns (double screen, pin-down into DHO, flex options off the handoff) or the Elbow Series [MA15].
- **Usual counters:** Horns flow; Motion Weak if the trailer pass is denied [MA14][MA15].
- **Detection signature [HEURISTIC]:** within 10 s of possession start: `PASS(1→trailer)` where the trailer is a big at r 7–9.8 m, θ 75–105°; `REVERSAL` within 1.5 s; the rim-run big crosses x = 0 at y < 2 m; then `STAGGER(1,4→2)` with 1 and 4 being the two previous passers, 2 catching at r ≥ 6.75 m.
- **Teams documented:** no NCAA D-I program confirmed in an opened source (college usage unverified). NBA: San Antonio Spurs [MA15]. A Golden State adaptation appeared in search results only (not opened; unverified).
- **Sources:** [MA15], [MA14].
- **Confidence:** medium.

### S02. Motion Weak

- **Name and aliases:** "Motion Weak", "Spurs Motion Weak" [MA14]; "Motion Weak Cross" (Johns Hopkins variant) [MA17]; Michigan Wolverines "Motion Weak" [MA16].
- **Family:** F2 / F3 entry → F8 cut-through, cross screen, STS down screen → F7 post.
- **Start alignment (spots inferred):** 1 at the SLOT (7.62, 66.8); 2 on the ball-side wing (7.50, 45.0); 5 at the ball-side BLOCK (2.04, 26.2); 4 trailer opposite (SLOT / TOP 7.62, 113.2); 3 on the weak wing or corner (7.50, 135.0). Trigger: 1's pass to the strong-side wing [MA14].
- **Roles:** 1 passer and basket cutter to the weak side, then cross screener; 2 wing receiver and post feeder; 5 post; 4 down screener and reverser; 3 down-screen user, then cross screener for 5 (Better Basketball) or reversal receiver (Johns Hopkins).
- **Ordered actions (Better Basketball):**
  1. t0: 1 passes to 2 and cuts to the basket, continuing to the weak-side wing (0–2.0 s).
  2. 2 looks to feed 1 or 5 posting (1.0–2.5 s).
  3. 4 down-screens for 3 (2.0–3.5 s).
  4. 2 passes to 4; 3 cuts to screen for 5 (cross) (3.5–5.0 s).
  5. 4 swings to 1 (5.0–6.0 s); else flow into Horns (4 and 5 to the elbows, 1 and 2 to the corners) [MA14].
  - Johns Hopkins "Motion Weak Cross": 1 enters to 2 and cuts through to the weak-side block; 2 reverses to 4, who reverses to 3; 1 cross-screens for 5; 3 feeds 5; 4 down-screens for 1 (STS) to the top [MA17].
  - Michigan listing: wing entry and cut-through; swing and cross screen; STS action [MA16].
- **Usual counters:** sideline PnR variation (the big who would post ball-screens after the reversal); Horns flow [MA14].
- **Detection signature [HEURISTIC]:** `PASS(slot→ball-side wing)`; the passer `CUT`s through the paint to the weak side (crosses x = 0 at y < 3 m) within 1.5 s; `REVERSAL` via a high player within 3 s; a cross `SCR` (|Δx| > 2|Δy|, y < 2 m) by the cutter-through for the post big, who catches at r < 2.5 m on the new ball side; then a down `SCR` on the cross screener (STS) sending him to r ≥ 6.75 m, θ 70–110°.
- **Teams documented:** Michigan (FastModel, published 2021-03-21; season 2020-21 inferred, unverified) [MA16]; Johns Hopkins women (NCAA D-III, 2022-23) [MA17]; NBA origin San Antonio Spurs [MA14]. MSU: none found.
- **Sources:** [MA14], [MA16], [MA17].
- **Confidence:** medium-high.

### S03. Transition loop (corner loop off a down screen)

- **Name and aliases:** "transition loop offense" (HoopStudent) [MB12]. Related: H12, L06.
- **Family:** F2 secondary → F3 entry; loop via a down screen.
- **Start alignment:** after a defensive rebound: 1 dribbles down one sideline to the wing (7.32, 34.9); 2 and 4 run to the weak-side wing (7.32, 145.1) and low post (BLOCK 2.04, 153.8); 3 sprints to the strong-side CORNER (6.81, 3.4); 5 sprints to the strong-side "extended low post", about (3.1, 30) (inferred; the source gives no coordinates) [MB12].
- **Roles:** 1 handler; 5 down screener; 3 loop cutter to the top.
- **Ordered actions:**
  1. 1 dribbles to the wing.
  2. 5 sets a down screen at the strong-side extended low post (within about 8 s of possession).
  3. 3 sprints to the corner, then loops to the top off 5's screen (cut starts ≤ 2.0 s after 3 reaches the corner; arrival at the top ≤ 3.5 s after the cut starts).
  4. 1→3 for a shot or a secondary action [MB12].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** within 10 s of a defensive rebound: a wing player reaches θ ≤ 12°; the cut starts ≤ 2.0 s after the player first reaches θ ≤ 12°; the player passes within 1.2 m of a stationary `SCR` at r 2.5–4 m, θ 15–40° and reaches θ 60–100°, r 7–8.5 m ≤ 3.5 s after the cut starts; the ball handler is on the same-side wing; catch at the top within 1 s of arrival.
- **Teams documented:** none named [MB12].
- **Sources:** [MB12].
- **Confidence:** medium.

### S04. Stagger Slip Curl & Pop [MSU]

- **Name and aliases:** "Stagger Slip Curl & Pop" (FastModel).
- **Family:** F2 early offense → F8 stagger, slip, down screen, pop.
- **Start alignment:** unverified.
- **Roles:** 4 first stagger screener who slips, later pop receiver; 5 down screener for 4; others unverified.
- **Ordered actions (summary only):** a stagger screen into a slip by 4 and a down screen by 5, ending in a pop-out for 4 [MA57]. Order otherwise unverified.
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** `STAGGER` where the first screener (4) `SLIP`s; 5 then down-screens for 4, who ends at r ≥ 6.75 m and catches, within 8 s of possession start.
- **Teams documented:** **Michigan State 2021-22** (published 2022-03-20; season inferred from publish date) [MA57].
- **Sources:** [MA57].
- **Confidence:** low (summary only).

### S05. Early Offense Loop DHO (Bradley)

- **Name and aliases:** "Early Offense Loop DHO" (FastModel) [MA60].
- **Family:** F2 → F6 high-post DHO → F5 slip.
- **Start alignment:** 5 at the HIGH POST (4.39, 78.2); 3 clears to the weak CORNER; 4 on the opposite arc; 1 and 2 guards (spots otherwise unverified) [MA60].
- **Roles:** 1 passer and DHO receiver; 5 high-post catcher, DHO giver, slipper; 2 screener for 1, then slips behind the arc; 3 clear; 4 spacer.
- **Ordered actions:** 1→5 at the high post; 3 clears to the weak corner; 4 on the opposite arc; 2 screens for 1; 5 steps to 1 for a DHO; 2 slips behind the arc; 5 slips to the low post after the DHO; 1 hits 5 or 2 [MA60].
- **Usual counters:** 5 low-post slip vs 2 behind the arc [MA60].
- **Detection signature [HEURISTIC]:** high-post catch ≤ 8 s into the possession; a guard-for-guard `SCR` into a `DHO` from the high post; the DHO giver `SLIP`s to r < 2.5 m ≤ 1.0 s after the transfer.
- **Teams documented:** Bradley 2018-19 (vs Michigan State, NCAA first round; MSU was the defending team) [MA60].
- **Sources:** [MA60].
- **Confidence:** medium-high.

### S06. Double Drag Double Zoom (Purdue) [RICHER VARIANT of Zoom / double drag]

- **Name and aliases:** Purdue "Double Drag Double Zoom" (Breakthrough) [MA70].
- **Family:** F2 double drag → F6 two consecutive zoom DHOs.
- **Start alignment:** transition double drag (two bigs high); 5 ends at TOP (spots otherwise unverified) [MA70].
- **Roles:** 1 (Braden Smith era guard) double-drag handler, then cutter and second zoom user; 5 (Zach Edey) top hub and zoom DHO giver twice, re-screener, roller; 4 down screener for 2; 2 first zoom user.
- **Ordered actions:** 1 comes off a double drag; pass back to 5 at the top; 1 cuts through; 2 comes off a down screen from 4 into a DHO / keep by 5; 1 trails 2 for the second zoom; 5 re-screens if the defender goes under; roll [MA70].
- **Usual counters:** keep; re-screen [MA70].
- **Detection signature [HEURISTIC]:** `DOUBLE` drag ball screen; then two zoom `DHO`s by the same big for two different guards within 4 s.
- **Teams documented:** Purdue (Painter; Edey, Braden Smith, Lance Jones; season 2023-24) [MA70].
- **Sources:** [MA70].
- **Confidence:** medium-high.

### S07. Slice Quick 3 Out Rub (Memphis Grizzlies)

- **Name and aliases:** "Slice Quick 3 Out Rub" (Breakthrough) [MA77]. NBA secondary alias.
- **Family:** F2 trailer → F3 → F8 circle off a back screen, down screen, slice cross → F5.
- **Start alignment:** 1 brings the ball up the right side; 5 trails about 3 m above the arc at DEEP (9.80, 90.0); 3 at the left ELBOW (4.57, 113.6); 2 and 4 on the right BLOCK (2.04, 26.2) [MA77].
- **Roles:** 5 trailer, reverser, down screener, cross screener, ball screener; 1 passer, down-screen user, PnR handler; 3 wing receiver, slice cutter; 2 circle cutter off 4's back screen; 4 back screener.
- **Ordered actions:** 1→5; 3 up to the left wing; 5→3; 2 circles off 4's back screen to the left corner; 1 cuts off 5's down screen to the top; 5 cross-screens 3 (slice cut to the right wing); 5 ball-screens 1 and rolls [MA77].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** trailer catch at r ≈ 9–10 m; ≥ 4 `SCR` events by that trailer within ≤ 8.0 s of his catch.
- **Teams documented:** none at college level; Memphis Grizzlies (NBA) [MA77].
- **Sources:** [MA77].
- **Confidence:** medium.

---

## 16. Wing dribble-entry starts (F3 entry → F8 / F5)

The handler dribbles to the wing to start the set; the remaining alignment forms around the dribble.

### D01. Hawk set (dribble entry plus high-post back-screen chain) [RICHER VARIANT of the "Hawk" cut (F8) and MSU "Hawk Double Cross" (`set_taxonomy.md` §3.2)]

- **Name and aliases:** "Hawk offense", "Hawk set" (HoopStudent; credited to Hubie Brown, Atlanta Hawks, mid-1970s; NBA origin) [MB37]. In college vocabulary the repo's "Hawk" is a diagonal screen from a one-dribble wing entry.
- **Family:** F3 entry → F8 back screen → STS.
- **Start alignment:** 1 dribble-enters to the right wing (7.32, 34.9); 4 at the high post near the right ELBOW (4.57, 66.4); 2 on the right side (wing or corner); 3 on the left wing (7.32, 145.1); 5 near the left BLOCK (2.04, 153.8) [MB37].
- **Roles:** 4 back screener, then popper to the top and new hub; 2 back-screen cutter to the right low post; 5 down screener; 3 shooter; 1 handler.
- **Ordered actions:**
  1. t0: 1 dribble-enters right.
  2. 4 back-screens for 2, who cuts to the right low post (0–1.5 s); 1→2 for a post move.
  3. If covered, 4 pops to the top and catches from 1 (1.5–3 s).
  4. 5 down-screens for 3, who goes to the left wing (2.5–4.5 s); 4→3 for three.
  5. Part 2: 3→5 post, or 4 down-screens for 2 to the top (4.5–7 s) [MB37].
  - Example 2 adds a cross screen by 2 for 5 plus STS (4 down-screens 2); Example 3 adds a 4 ball screen for 1 plus an elevator by 3 and 5 for 2 [MB37].
- **Usual counters:** Examples 2 and 3 [MB37].
- **Detection signature [HEURISTIC]:** dribble entry to a wing; within 1.2 s of the dribble start the elbow player sets a `SCR` whose cutter moves −y to r < 2.5 m (back screen); the screener moves to TOP (θ 80–100°, r 7–8.5 m) within 2 s and catches; a weak-side down `SCR` follows within 2.5 s.
- **Teams documented:** **Michigan State** "Hawk Double Cross" (2017) is already in the repo (`set_taxonomy.md` §3.2 `[S29b]`; not re-opened for this file). Atlanta Hawks (Hubie Brown) [MB37].
- **Sources:** [MB37].
- **Confidence:** medium.

### D02. Euro set (Blatt) options

- **Name and aliases:** "Euro set", Options 1–3 (Coach's Clipboard; David Blatt used these overseas) [MA11]. European secondary alias family.
- **Family:** F3 entry (dribble to the wing + stagger to the top) → F5 / F8.
- **Start alignment:** 1 dribbles to the left wing (7.50, 135.0); 3 starts at TOP (7.60, 90.0); 4 and 5 set a double stagger for 3 to the top [MA11]; 2 on the right side (unverified spot).
- **Roles:** 1 dribbler and passer; 3 stagger user and top receiver; 4 and 5 stagger screeners; 2 elevator / stagger user.
- **Ordered actions (base):** 1 dribbles to the left wing; 4 and 5 stagger for 3 to the top; 1→3 (0–3 s). Then:
  - Option 1: 4 down-screens 5 (4 to the left short corner); 5 ball-screens 3 (PnR); 1 down-screens 2; 4 to the high post.
  - Option 2: elevator (or stagger) for 2 to the top; 1 to the corner.
  - Option 3: 2 cuts to the right corner, clearing the left; 1 back-cuts if overplayed; else 3→1 and ball-screens; 5 and 4 stagger for 2 to the top [MA11].
- **Usual counters:** backdoor vs an overplay (Option 3) [MA11].
- **Detection signature [HEURISTIC]:** dribble entry to the wing; `STAGGER` by both bigs for a player who ends at TOP and catches the pass back from the wing within 3 s; then one of: big-for-big down screen into a ball screen (Option 1), an elevator closing to < 0.6 m (Option 2), or a pass-and-follow ball screen at the wing (Option 3).
- **Teams documented:** David Blatt (European clubs) per the page; no college team [MA11].
- **Sources:** [MA11].
- **Confidence:** medium.

---
## 17. 1-2-2 and Line families

No named half-court entry from a 1-2-2 or a Line start was found in the opened sources (Line remains an out-of-bounds alignment in the repo, `offense_full.md` §3.1). Count: 0 each. Gap: dribble-drive "1-2-2" entries (DDM "415", "153", "253", "150", "Wave", "Rocket") were found by name only (§20).

---

## 18. Alignment not documented by the source

The pages below give the ordered actions but not the five-player start (FastModel diagrams were not readable, and some pages give a summary only). Each item records the researcher's inference where one exists; all such spots are unverified. MSU items first.

### U01. Elbow Ball Screen [MSU]

- **Name and aliases:** "Michigan State Elbow Ball Screen".
- **Family:** F6 DHO entry → F8 down and back screens → F5 high ball screen, drag to the roll.
- **Start alignment (inferred):** 1 at TOP / SLOT with the ball; 3 (Valentine) on a wing (7.50, 45.0); 5 near an ELBOW, pops to the perimeter; 2 (Harris) low at a BLOCK (2.04, 153.8) for the down screen; 4 (Dawson) at the opposite ELBOW (4.57, 113.6).
- **Roles:** 1 DHO giver; 3 DHO receiver, then back-screen cutter and corner filler; 5 popper and down screener; 2 shooter off the down screen and PnR handler; 4 back screener, then ball screener and roller.
- **Ordered actions:**
  1. t0: 1 dribbles into a DHO with 3; 5 pops to the perimeter (0–2.0 s).
  2. 5 down-screens for 2, who comes to the perimeter; 3 dribbles and passes to 2 (2.0–4.0 s).
  3. 4 back-screens for 3, who looks at the rim, then clears to the corner (4.0–5.5 s).
  4. 4 ball-screens for 2 and rolls hard; 2 "drags" the screen until 4 is open (5.5–8.0 s) [MA25].
- **Usual counters:** none named; the read is the drag timing [MA25].
- **Detection signature [HEURISTIC]:** `DHO` at r 6.5–8 m within 3 s of the snapshot; a big moves to r ≥ 6.75 m; a down `SCR` by that big for a low player who ends at r ≥ 6.75 m and catches; a back `SCR` by the other big on the DHO receiver (to r < 2 m, then θ ≤ 12°); a ball `SCR` by the back screener with `ROLL` ≤ 2.0 s.
- **Teams documented:** **Michigan State 2013-14** (NCAA win over Harvard) [MA25].
- **Sources:** [MA25].
- **Confidence:** high (steps); alignment inferred.

### U02. Curl (MSU 2014) [MSU]

- **Name and aliases:** "Michigan State – Curl".
- **Family:** F8 down screen, back-screen lob, cross screen → curl; F7 post entry.
- **Start alignment (inferred):** 1 at TOP (the page labels 2 = Trice, 3 = Harris, 5 = Payne); 5 low or high post; 2 low for the down screen; 4 near an ELBOW; 3 low on the weak side.
- **Roles:** 2 first option off 5's down screen; 4 back screener for 1, then cross screener for 3; 1 lob cutter, then corner; 3 curl cutter; 5 post.
- **Ordered actions:**
  1. t0: 2 comes off a down screen by 5 (0–1.5 s).
  2. 4 back-screens 1, who looks for a lob, then clears to the corner (1.5–3.0 s).
  3. 3 rotates up to FT-line extended (2.5–3.5 s).
  4. 2 passes to 5 in the post (3.5–4.5 s).
  5. 4 cross-screens for 3, who curls to the rim (4.5–6.0 s) [MA26].
- **Usual counters:** none listed.
- **Detection signature [HEURISTIC]:** down `SCR(5→2)` with 2 ending at r ≥ 6.75 m; back `SCR(4→1)`, 1 reaches r < 1.5 m, then θ ≤ 12°; `ENTRY` to 5 at r < 2.5 m; then a cross `SCR` (|Δx| > 2|Δy|, y < 2 m) by 4 with 3 curling to r < 1.5 m within 1.2 s.
- **Teams documented:** **Michigan State 2013-14** (Big Ten Tournament championship game) [MA26].
- **Sources:** [MA26].
- **Confidence:** high (steps).

### U03. Pin Naked Curl [MSU]

- **Name and aliases:** "Pin Naked Curl". "Naked curl" = a curl with no screener set for it (definition unverified; the page uses the term without defining it).
- **Family:** F8 down-screen wing entry, pin screen, curl.
- **Start alignment (inferred):** 1 TOP; 4 near the block / wing; 2 low (BLOCK) → wing; 5 low on the other side; 3 in the weak CORNER (6.81, 176.6).
- **Roles:** 4 down screener, then post-up; 2 wing receiver and swing passer; 1 cutter to the FT line, then pin-screen user; 5 pin screener, then clears; 3 naked-curl cutter from the corner.
- **Ordered actions:**
  1. t0: 4 down-screens 2 for the wing entry; 4 holds the block post-up; 1 cuts to the FT line, then uses 5's pin screen (0–3.0 s).
  2. 2 swings to 1; 5 clears to the backside; 3 runs a naked curl from the corner (3.0–5.5 s) [MA43].
- **Usual counters:** post-up by 4 after the down screen [MA43].
- **Detection signature [HEURISTIC]:** down `SCR(4→2)` then `PASS(1→2)` at the wing; 4 stays at r < 2.5 m; 1 cuts to the NAIL (4.19, 90.0), then out off a down `SCR(5→1)`; `PASS(2→1)`; then the weak-corner player moves from θ ≥ 168° on a curved path to r < 3 m with **no** stationary teammate within 1.2 m of the path.
- **Teams documented:** **Michigan State 2018-19** (second half vs Bradley, NCAA first round) [MA43].
- **Sources:** [MA43].
- **Confidence:** medium.

### U04. L Option Post Up [MSU]

- **Name and aliases:** "L Option Post Up". "L" appears to refer to the point guard's choice of a pin-down from 4 or a baseline screen from 5 (meaning unverified).
- **Family:** F8 pin-down wing entry, back screen on X1, pin-down / baseline-screen choice → F7 post entry.
- **Start alignment (inferred):** 1 TOP; 2 low → wing off 5's pin-down; 4 at an ELBOW; 5 on a BLOCK (Nick Ward, post target) [MA46].
- **Roles:** 2 wing receiver, post feeder; 4 back screener on X1, then weak-side diver; 1 cutter to the block, then pin-down or baseline-screen user, post feeder; 5 pin screener, baseline screener, post target.
- **Ordered actions:**
  1. t0: 2 comes off a pin-down from 5; 1 passes to 2 (0–2.0 s).
  2. 4 back-screens X1 (2.0–3.0 s).
  3. 1 cuts to the block, then comes off either a pin-down from 4 or a baseline screen from 5 (primary: off 5) (3.0–5.0 s).
  4. 4 dives to the weak-side block (4.0–5.0 s).
  5. 2 makes a direct post entry or an extra pass to 1, who enters (5.0–6.5 s) [MA46].
- **Usual counters:** pin-down vs baseline screen keeps the defense honest [MA46].
- **Detection signature [HEURISTIC]:** down `SCR(5→2)`; `PASS(1→2)`; back `SCR(4→1)` with 1 reaching r < 2.5 m; 1 exits either +y (pin-down) or along y < 1.5 m (baseline) off a stationary teammate; `ENTRY` to 5 at r < 2.5 m within 2.5 s.
- **Teams documented:** **Michigan State 2018-19** (first play vs Purdue; Winston, Ward; season inferred from "this past season" in a 2019-05-22 post) [MA46].
- **Sources:** [MA46].
- **Confidence:** high (steps).

### U05. Weave Zoom [MSU]

- **Name and aliases:** "Weave Zoom".
- **Family:** F6 DHO chain (weave) → F5 ball screen.
- **Start alignment:** unverified (diagram unreadable); likely 5-out or 4-out with 4 on the perimeter (inference).
- **Roles:** DHO chain 1 → 2 → 4 → 1, then 5 ball-screens 1.
- **Ordered actions:**
  1. t0: DHO to 2 (0–1.5 s).
  2. DHO to 4 (1.5–3.0 s).
  3. 4 DHOs to 1 (3.0–4.5 s).
  4. 5 ball-screens for 1 (4.5–6.0 s) [MA39].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** three `DHO` events within ≤ 5 s along the arc (r 6–8.5 m), the third given by a big (4) to the original handler, then a ball `SCR` by the other big on that handler within 1.5 s. Distinguish from DHO / Chase motion (`offense_full.md` 4.1) by the terminal ball screen and the return to 1.
- **Teams documented:** **Michigan State 2022-23** (ATO tag; published 2023-03-17; season inferred from publish date) [MA39].
- **Sources:** [MA39].
- **Confidence:** medium.

### U06. Pin Down Circle [MSU] [RICHER VARIANT; `set_taxonomy.md` §3.2 lists the title only]

- **Name and aliases:** "Pin Down Circle".
- **Family:** F6 DHO → F8 down screen, stagger.
- **Start alignment:** unverified.
- **Roles:** DHO receiver 3; 4 down screener for 2, then stagger screener; 2 down-screen user and passer; 1 stagger user; 5 stagger screener.
- **Ordered actions:**
  1. t0: DHO to 3; 4 down-screens for 2 (0–2.0 s).
  2. 3 passes to 2 while 1 runs off a stagger from 5 and 4 (2.0–4.0 s).
  3. 2 passes to 1 (4.0–5.0 s) [MA41].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** `DHO` at the arc; concurrent down `SCR(4→2)`; `PASS(3→2)`; `STAGGER(5,4→1)` (4 being the player who just down-screened) with 1 catching at r ≥ 6.75 m within 1.5 s of the second contact.
- **Teams documented:** **Michigan State 2022-23** (ATO; published 2023-03-23; season inferred from publish date) [MA41].
- **Sources:** [MA41].
- **Confidence:** medium.

### U07. Motion Go Duck-In [MSU]

- **Name and aliases:** "Motion Go Duck-In".
- **Family:** F4 motion entry → F5 sprint-up middle PnR → F7 duck-in.
- **Start alignment (inferred):** 1 at TOP / wing with the ball; 2 on a wing (cuts to the top); 5 low; 4 weak-side low; 3 weak-side low → wing.
- **Roles:** 1 dribbler at 2; 2 cutter to the top, then PnR handler; 5 sprint ball screener, then duck-in post; 4 pin-down screener, post feeder; 3 throwback option.
- **Ordered actions:**
  1. t0: 1 dribbles toward 2, who cuts to the top of the key (0–1.5 s).
  2. 5 sprints into a middle PnR with 2; 4 pins down for 3 (throwback option) (1.5–3.5 s).
  3. On the throwback, 2 and 4 look to feed 5 ducking in hard (3.5–5.5 s) [MA53].
- **Usual counters:** throwback to 3 if 2 cannot reach the rim [MA53].
- **Detection signature [HEURISTIC]:** `DRIBBLE_AT` a wing while that wing cuts to TOP (θ 80–100°) and catches; a big reaches the top at ≥ 3 m/s and sets a ball `SCR` (sprint-up, `set_taxonomy.md` §1.5); simultaneous weak-side down `SCR`; then a big moves from the weak block into the middle of the lane (|x| decreasing ≥ 1.5 m at y < 2.5 m, duck-in) and receives `ENTRY`.
- **Teams documented:** **Michigan State 2012-13** (after a dead ball; published 2013-03-08; season inferred from publish date) [MA53].
- **Sources:** [MA53].
- **Confidence:** medium-high.

### U08. Quick Double [MSU]

- **Name and aliases:** "Quick Double". (The page spells the coach "Tim Izzo"; treated as a typo.)
- **Family:** F8 back screen, then stagger away.
- **Start alignment (inferred):** two-guard / 1-4-like: 1 TOP; 2 on a wing; 4 high (reversal hub); 3 opposite wing; 5 low.
- **Roles:** 1 passer, corner cutter, stagger user; 2 receiver, reverser, back-screen cutter; 4 reversal passer, stagger screener; 5 back screener, stagger screener; 3 reversal receiver.
- **Ordered actions:**
  1. t0: 1 passes to 2 and cuts to the strong-side corner (0–1.5 s).
  2. 2 reverses to 4, who swings to 3 (1.5–3.5 s).
  3. 5 back-screens for 2 at the block (3.5–4.5 s).
  4. 5 and 4 turn and stagger away for 1 (4.5–6.5 s) [MA54].
- **Usual counters:** the back screen draws the defense in, so the stagger is hard to guard [MA54].
- **Detection signature [HEURISTIC]:** `PASS(TOP→wing)`, then the passer to θ ≤ 12° on the same side; `REVERSAL` in two passes within 2.0 s; back `SCR(5→2)` near the block; within 1.5 s `STAGGER(5,4→1)` with 1 moving from the corner toward the weak-side wing / top and catching at r ≥ 6.75 m.
- **Teams documented:** **Michigan State 2012-13** (vs Wisconsin; published 2013-03-09; season inferred from publish date) [MA54].
- **Sources:** [MA54].
- **Confidence:** high (steps).

### U09. Piston Stagger [MSU]

- **Name and aliases:** "Piston Stagger".
- **Family:** F8 double stagger: wing, then corner.
- **Start alignment:** unverified.
- **Roles:** 2 first stagger cutter; 1 passer, then cuts around 2 to the corner; 4 and 5 stagger screeners twice; 3 corner stagger user.
- **Ordered actions:**
  1. t0: 2 cuts off a stagger by 5 and 4 (0–2.0 s).
  2. 1 passes to 2 and cuts around 2 to the corner (2.0–3.5 s).
  3. 4 and 5 set a second stagger for 3 in the corner (3.5–5.5 s) [MA35].
- **Usual counters:** screener slip (4 slipped the second screen for a layup) [MA35].
- **Detection signature [HEURISTIC]:** two `STAGGER` events by the same screener pair within 4.0 s for two different cutters; between them `PASS(1→2)` and 1 passing within 1.5 m of 2 on the way to θ ≤ 12°.
- **Teams documented:** **Michigan State 2015-16** (published 2016-02-10; season inferred from publish date) [MA35].
- **Sources:** [MA35].
- **Confidence:** medium-high.

### U10. Rub Down Screen [MSU]

- **Name and aliases:** "Rub Down Screen".
- **Family:** F5 rub screen for the big → ball screen; F8 down screen.
- **Start alignment:** unverified.
- **Roles:** 1 handler; 2 rub screener for 5, then down-screen user; 5 ball screener; 4 down screener.
- **Ordered actions:**
  1. t0: 1 dribbles right while 2 rub-screens for 5 (0–1.5 s).
  2. 5 ball-screens for 1 (1.5–3.0 s).
  3. 4 down-screens for 2 (2.5–4.0 s) [MA36].
- **Usual counters:** not given; produced an open corner three [MA36].
- **Detection signature [HEURISTIC]:** a guard sets an off-ball `SCR` for a big, who sets a ball `SCR` ≤ 1.0 s later (a guard-set ram); concurrent down `SCR(4→2)` for the rub screener; `PASS` to a corner / wing at r ≥ 6.75 m.
- **Teams documented:** **Michigan State 2015-16** (overtime; published 2016-02-10; season inferred from publish date) [MA36].
- **Sources:** [MA36].
- **Confidence:** medium.

### U11. STS Spain Action [MSU] [RICHER VARIANT of Spain]

- **Name and aliases:** "STS Spain Action". Here the back screen is set **for the ball screener (5) by 4** (screen-the-screener), not the classic back screen on the roller's defender by a guard.
- **Family:** F5 Spain → F8 STS.
- **Start alignment:** unverified.
- **Roles:** 5 flat ball screener and back-screen cutter; 1 handler; 4 back screener, pop option.
- **Ordered actions:**
  1. t0: 5 sets a flat ball screen (0–1.0 s).
  2. 1 dribbles off (1.0–2.0 s).
  3. 4 back-screens for 5; 4 is open on the pop if the defense takes the back screen away (2.0–3.5 s) [MA56].
- **Usual counters:** 4 pop [MA56].
- **Detection signature [HEURISTIC]:** ball `SCR` with the screener's body parallel to the baseline (flat, `offense_full.md` 5.2); within 1.5 s a back `SCR` on the ball screener by a **big**, with 5 reaching r < 1.5 m, or 4 `POP`s to r ≥ 6.75 m.
- **Teams documented:** **Michigan State 2020-21** (published 2021-03-19; season inferred) [MA56].
- **Sources:** [MA56].
- **Confidence:** medium.

### U12. 2le High Trade [MSU]

- **Name and aliases:** "Michigan St. 2le High Trade". "2le" is undefined on the page (reads as "double", two high screeners); "Trade" is not defined (unverified).
- **Family:** F5 double high PnR.
- **Start alignment:** unverified; two bigs (4, 5) high.
- **Roles:** 1 handler; 4 first ball screener who lifts; 5 second ball screener.
- **Ordered actions (summary only):** 1 runs PnR with 4, then PnR with 5 while 4 lifts up; the point guard exploits the options [MA58].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** two ball `SCR` events on 1 by different bigs within 3.0 s, both at r 6.5–9 m; after the second, the first screener moves to r ≥ 6.75 m behind the ball (lift).
- **Teams documented:** **Michigan State 2024-25** (the page calls it an "NCAA 2024-25 Michigan State set"; published 2025-03-04) [MA58]. As of the fixer, 2026-10-18 (UTC) re-scan of all 8 result pages of [MA20] (120 results, not sorted by date), this is the most recent MSU man-to-man half-court set in the search. One later MSU title exists, "Michigan State Vs Zone" (2025-03-13; a zone set; page not opened), and no result is dated in the 2025-26 season or in 2026. The list grows over time; re-scan before relying on this.
- **Sources:** [MA58].
- **Confidence:** low (summary only).

### U13. 5-up Muscle (Kansas)

- **Name and aliases:** "5-up Muscle" (FastModel) [MA61].
- **Family:** F5 → STS lob (Spain with a big) → F7 high-low post isolation.
- **Start alignment:** unverified.
- **Roles:** 5 ball screener, lob cutter, post isolation; 4 back screener, popper, post feeder; 1 handler; 2 and 3 exchange.
- **Ordered actions:** 5 ball-screens 1; 4 back-screens 5 for a lob; else 4 pops and catches; 3 and 2 exchange; 4 feeds 5 for a post isolation [MA61].
- **Usual counters:** pop and high-low [MA61].
- **Detection signature [HEURISTIC]:** the ball screener is back-screened by the other big; then a high-low `ENTRY` from the popper (r ≥ 6.75 m) to r < 2.5 m.
- **Teams documented:** Kansas 2016-17 (vs Michigan State, NCAA Tournament; MSU defending) [MA61].
- **Sources:** [MA61].
- **Confidence:** medium-high.

### U14. Elbow Slip (Purdue)

- **Name and aliases:** "Elbow Slip" (FastModel) [MA62].
- **Family:** F6 DHO → F5 stagger ball screen with a slip.
- **Start alignment:** unverified.
- **Roles:** 1 DHO giver; 3 DHO receiver and handler; 5 first stagger screener who slips; 4 second screener.
- **Ordered actions:** 1 dribbles left and DHOs to 3; 3 dribbles toward 5 and 4 (stagger ball-screen look); 5 slips when X5 jumps up [MA62].
- **Usual counters:** slip vs a jump-out [MA62].
- **Detection signature [HEURISTIC]:** `DHO`, then ≤ 2.0 s later the receiver dribbles toward two bigs set 2–5 m apart (stagger ball screen); the first screener `SLIP`s ≤ 1.0 s after the handler comes within 3 m.
- **Teams documented:** Purdue 2015-16 (vs Michigan State, Big Ten Tournament; MSU defending) [MA62].
- **Sources:** [MA62].
- **Confidence:** medium.

### U15. Handoff Slip (Purdue)

- **Name and aliases:** "Handoff Slip" (FastModel; ATO) [MA64].
- **Family:** F6 DHO → slip.
- **Start alignment:** unverified.
- **Roles:** 1 DHO giver; 3 DHO receiver; 5 fake screener who slips.
- **Ordered actions:** 1 DHOs to 3; 5 fakes a screen for 3 and slips [MA64].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** `DHO`, then ≤ 2.0 s later a big approaches within 2 m of the receiver and `SLIP`s (no stationary phase ≥ 0.5 s).
- **Teams documented:** Purdue 2015-16 (ATO vs Michigan State; MSU defending) [MA64].
- **Sources:** [MA64].
- **Confidence:** medium.

### U16. Ball Screen to Stagger (UConn)

- **Name and aliases:** UConn "Ball Screen to Stagger" (Breakthrough) [MA81].
- **Family:** F5 false action → F8 baseline stagger.
- **Start alignment:** unverified; 1 enters from the perimeter to 2 coming off a down screen.
- **Roles:** 1 (Cam Spencer) passer, corner runner, baseline stagger user; 2 (Diarra) down-screen user and handler; 4 (Karaban) ball screener, roller, stagger screener; 5 stagger screener.
- **Ordered actions:** 1 enters to 2 coming off a down screen and runs to the ball-side corner; 4 ball-screens 2 and rolls while 1 lifts; 2 to the top; 1 sprints the baseline off 4 and 5 (stagger) for a three [MA81].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** ball `SCR` + `ROLL` while the corner player lifts, then reverses to run along y < 1.5 m off two big screeners (baseline `STAGGER`), catching at r ≥ 6.75 m.
- **Teams documented:** UConn (Hurley; Spencer era, 2023-24), end of half vs San Diego State [MA81].
- **Sources:** [MA81].
- **Confidence:** high.

### U17. Double Ball Screen (Kansas 2011-12)

- **Name and aliases:** Kansas double / stagger ball screen (Breakthrough; Don Kelbick) [MA82].
- **Family:** F5 → F6 → F5 stagger ball screen.
- **Start alignment:** unverified.
- **Roles:** 1 handler, DHO giver, then low post; 4 first ball screener, then stagger screener; 2 backdoor option, DHO receiver, stagger ball-screen user; 5 to the high post, stagger screener.
- **Ordered actions:** 1 dribbles left off 4's ball screen; 2 sets up a backdoor; else 1 DHOs to 2; 5 to the high post; 1 to the low post; 4 and 5 stagger ball-screen for 2; counter: 4 and 5 stagger for 1 [MA82].
- **Usual counters:** off-ball stagger for 1 [MA82].
- **Detection signature [HEURISTIC]:** ball `SCR` → `DHO` ≤ 3.0 s later → stagger ball screen (two bigs, 2–5 m apart) on the DHO receiver ≤ 3.0 s after the DHO; counter = the same pair sets an off-ball `STAGGER` for the original handler.
- **Teams documented:** Kansas (Self) 2011-12 [MA82].
- **Sources:** [MA82].
- **Confidence:** medium-high.

### U18. Opening set: empty-side PnR into exit screen seal (Loyola Chicago)

- **Name and aliases:** Loyola Chicago opening set (Breakthrough) [MA71].
- **Family:** F5 empty-side wing PnR → F8 exit screen → F7 seal.
- **Start alignment:** unverified; ball side cleared for a wing ball screen; a big in the lane; a player on the opposite block.
- **Roles:** wing handler; ball screener; lane big (fluff back screener, exit screener, then sealing post); opposite-block player (exit-screen user); elbow receiver.
- **Ordered actions:** cleared wing ball screen; the lane big back-screens the ball screener (fluff); then sets an exit screen for the opposite-block player to the ball-side corner while the ball goes to the big at the elbow; the post seals in front of the rim [MA71].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** wing ball `SCR` with the ball side empty; then a baseline-parallel `SCR` at y < 1 m (exit) toward the ball-side corner; then `ENTRY` at r < 1.5 m to a `SEAL`ed post.
- **Teams documented:** Loyola Chicago, season unverified [MA71].
- **Sources:** [MA71].
- **Confidence:** medium.

### U19. Ghost Hi-Lo (Indiana women)

- **Name and aliases:** Indiana "Ghost Hi-Lo" (Breakthrough) [MA74].
- **Family:** F5 ghost screen → F7 high-low.
- **Start alignment:** others deep in the corners (CORNERS 6.81, 3.4 / 176.6); 4 high; 5 low (spots otherwise unverified) [MA74].
- **Roles:** 4 ghost screener, then top receiver and high-low passer; 1 handler (first option: attack); 5 sealing post.
- **Ordered actions:** 4 ghost-screens for 1 (first option: attack); the ball is thrown back to 4 at the top; 5 seals for the high-low; others deep in the corners [MA74].
- **Usual counters:** not given.
- **Detection signature [HEURISTIC]:** a screener approaches the handler (< 1.5 m) with no stationary phase and leaves to the top, catches, then `ENTRY` to a `SEAL`ed post.
- **Teams documented:** Indiana women (NCAA second round; season unverified) [MA74].
- **Sources:** [MA74].
- **Confidence:** medium.

### U20. Wheel Action (Duke) [NAME COLLISION with X01 and W01]

- **Name and aliases:** "Duke Blue Devils – Wheel Action" (FastModel) [MA59].
- **Family:** F6 DHO entry → F8 basket cut, turnout → F5 pick-and-pop / F7 high-low.
- **Start alignment:** unverified; 4 at the perimeter.
- **Roles:** DHO giver (1), then basket cutter; 3 sets up his defender and uses 5's screen (turnout); 5 screener; 4 perimeter.
- **Ordered actions:** DHO entry; 3 sets up his defender; 5 screens 3 while 1 cuts to the basket; 4 at the perimeter; Option 1: flare / turnout, then high-low; Option 2: back screen / turnout, then pick-and-pop [MA59].
- **Usual counters:** Options 1 and 2 [MA59].
- **Detection signature [HEURISTIC]:** `DHO`, then ≤ 2.0 s later a basket cut by the DHO giver (to r < 2 m) and, within ±1.0 s of it, a turnout `SCR` for a wing.
- **Teams documented:** Duke 2020-21 (vs Michigan State, 1 Dec 2020; MSU defending) [MA59].
- **Sources:** [MA59].
- **Confidence:** medium.

### U21. Doornekamp action

- **Name and aliases:** "Doornekamp Action": a fake lift toward the safety pass, then a basket cut; FastModel credits the term to Basketball Immersion [MA87]. Origin of the name not given on the page.
- **Family:** F8 back screen + fake lift → STS.
- **Start alignment (from the step text):** 4 low, lifts as if for a safety pass; 2 shooter as back screener; 5 in the ball-side CORNER (6.81, 3.4); 3 lifts from the weak CORNER (6.81, 176.6) [MA87].
- **Roles:** 4 fake lifter and rim cutter; 2 back screener, then STS user; 5 screener of the screener; 3 lane-clearing lift.
- **Ordered actions:** 4 lifts (fake safety) (0–1.0 s); 2 back-screens 4; 3 lifts to clear the lane; 4 cuts to the rim (1.0–2.5 s); 5 screens the screener (2) (2.5–4.0 s) [MA87].
- **Usual counters:** open shot for 2 off the STS, or attack a switch [MA87].
- **Detection signature [HEURISTIC]:** a player moves +y ≥ 1.5 m (lift), then reverses (> 150°) to r < 1.5 m within 1.5 s off a back `SCR`; the back screener is screened ≤ 1.5 s later.
- **Teams documented:** none (the example is a BLOB) [MA87].
- **Sources:** [MA87].
- **Confidence:** medium (as a term).

### U22. Triple Wing Screen (Beilein)

- **Name and aliases:** "John Beilein Triple Wing Screen" (Coaching Toolbox; the URL slug says "double-wing-screen", the title says "Triple Wing Screen") [MB32].
- **Family:** F3 entry → F5 sequential wing ball screens.
- **Start alignment:** not described in the text; numbers are role labels (1, 3, 4, 10, 11) [MB32].
- **Roles:** 3 initial passer, then primary handler; 4 step-out passer, then second ball screener and roller; 11 wing passer, then first ball screener who pops to the corner; 1 third screener; 10 weak-side corner.
- **Ordered actions:**
  1. 3→4; 3 cuts to the opposite corner, and 10 cuts behind 3 to the opposite corner (0–2.5 s).
  2. 1 and 11 move up to the wing; 4 steps out and passes to 11 (2–4 s).
  3. 11→3; 3 receives ball screens from 11 (pops to the corner), then 4 (rolls), then 1 (4–8 s) [MB32].
- **Usual counters:** throwback to 11 in the corner, post entry to 4, or 3 attacks the lane; Michigan's finish: 4 sets a face screen for 3 [MB32].
- **Detection signature [HEURISTIC]:** three ball `SCR` events on the same handler from three different screeners within ≤ 4.5 s, all at r 6–8 m on one side; the first screener ends in the corner (`POP`), the second at r < 2 m (`ROLL`).
- **Teams documented:** Michigan (Beilein); no season [MB32]. MSU: none found.
- **Sources:** [MB32].
- **Confidence:** medium.

---
## 19. Name collisions and alias map

| Label | Meanings found | Resolution in this file |
|---|---|---|
| **Blast** | Repo: strong-side corner backdoor inside Horns Stagger (`offense_full.md` 3.2). MSU: two-guard front, 4 pops, guards dive, pin-downs or "X" floppy [MA23] | G06 stored as `MSU_Blast` |
| **Gator** | Repo: drag reject-and-pass read. Coach's Clipboard: 4-out shuffle-then-stagger quick hitter [MA8] | F03 stored as `Gator_4out` |
| **Michigan** | Coach's Clipboard Horns / 3-out play [MA1][MA13] vs Breakthrough youth continuity [MA85]; neither establishes University of Michigan usage | H15 and X03 |
| **Elbow** | Gonzaga double pin-downs (repo) vs Auriemma Elbow Series (O10) vs MSU Elbow Away (E01, E02) vs Spurs "Elbow Series" (S01; contents unverified) vs Elbow Special (E03) | Separate entries |
| **Loop** | Corner-to-top loop off a down screen (H12, S03); loop behind a dribbler after a re-screen (L06); title word only in MSU Horns Loop STS (H04); cutter looping around screeners in MSU Floppy Loop Under (K03); repo `offense_full.md` "Corner shooter loop" (Pacers, corner shooters loop toward the FT line) [O81] | Separate entries |
| **Flare** | H24 Perkins "Flare" (flare then second ball screen) [MA2]; V06 Xavier 5-out "Flare" [MA9]; repo Horns Flare (`offense_full.md`); H20 Kansas Horns Flare (lob variant) [MA1] | Separate entries; H20 is a richer variant of repo Horns Flare |
| **Split** | P01 Straight Split (post split) [MB1][MB41]; repo `offense_full.md` "Horns Split" (elbow pass, passer screens for the other big or the corner) [O12]; repo ball-screen counter "Split" (dribble between two defenders) [O48]; repo European "Elbow split" [O47] | Separate entries |
| **Spartan** | Coach's Clipboard (Perkins DVD) Horns "Spartan", same family as MSU Elbow Punch Stagger (H01) [MA30]; [MA2] does not establish MSU usage of "Spartan" | vs repo "Spartan Re-Screen" (F18): different plays |
| **Wheel** | Spurs Wheel (box start, X01); Pinholster Wheel offense (W01); Duke Wheel Action (U20); UConn "Wheel" (repo, no detail); Witherspoon "wheel action" continuity (repo) | Separate entries |
| **Forwards Out** | Princeton personnel inversion (G05); MSU Regular / Wide (O06, O07); UConn Forwards Out Zoom (F08) | Separate entries; common origin unverified |
| **Boomerang** | Xavier 5-out play [MA9] = HoopStudent boomerang action [MB38] | Merged (V05) |
| **Stagger / Stagger Away** | Xavier "Stagger" [MA9] = Hooper "Stagger Away" [MB28] | Merged (V01) |
| **Double-Cross / Cross (1-4 Low)** | Coach's Clipboard [MA5] = Breakthrough 1-4 Low Cross [MA76] | Merged (L01); Breakthrough "Cross" from 3-out 2-in is separate (R03) |
| **Pinball / Base** | Coach's Clipboard [MA5] = Breakthrough 1-4 Low Base [MA76] | Merged (L03) |
| **Horns Re-Screen** | Coach's Clipboard [MA1] = repo Horns Twist | Alias only, not counted |
| **Pistol** | Repo 2.2 Pistol ("21") dribble entry vs MSU Horns Pistol (big DHO from the top) | H02, H03 kept separate |
| **Get** | Hooper "Get" (V09) vs Spanoulis DHO (V10, low player sprints up) vs repo Horns Elbow Get | Separate entries |

---

## 20. Found but not templated (names only; not counted)

| Item | What the opened source says | Source | Status |
|---|---|---|---|
| MSU "Early Offense Post Entry" (vs UCLA, published 2021-03-19) | Title and summary only | [MA55] | Not counted |
| MSU titles: "Miles Bridges Set" (2018), "Michigan State: 1-4" (2019 teaser), "Line Post Stagger SLOB", "Elevator Drive Option", "3 Point Special", "Baseline Cross" | Titles in the FastModel MSU search listing; pages not opened or no steps | [MA20] | Not counted |
| DDM entries "415", "153", "253", "150" | Triple-gap entries for Dribble Drive Motion; 415 gets the 5 a triple gap; 153 and 253 use false motion to move the 3 to the slot; 150 attacks after a back cut; no step text | [MB4] | Names only |
| DDM "Wave", "Rocket" | Kevin Gaudet entries: "Wave" opens a "super gap" for the 3 (or 2); "Rocket" uses false motion to invert the start | [MB4] | Names only |
| Fake Double Staggers (FGCU, Karl Smesko) | Double staggers that occupy help so a gap can be driven; 4-out version uses a single pin-down | [MB34] | Women's program; no steps |
| Ghost Veer / Double Elevator / Horns Over Clear (Arkansas women, Mike Neighbors) | Gap-creating decoy actions | [MB34] | Women's program; no steps |
| Pinch-post catch series (Jordan Delp, Pure Sweat) | Four elbow-catch reads (rip-through; fake handoff and jab; fake back-cut, jab and shot fake then attack middle; double fake then attack baseline) | [MB33] | Player-level reads, not a team entry |
| "Power" (FIBA entry list) | Listed with "Diamond" under the most popular entries, with no definition | [MB1] | Still unverified (repo agrees) |
| Bill Self "Six Effective Entries into the High/Low Motion Offense"; James Jones (Yale) "eleven motion starters" | Product pages | [MB22], [MB23] (HTTP 403) | Could not open; unverified |
| Beilein "Chin", "Shuffle", "Basic Motion" series | Chin is the first series, then Shuffle, then Basic Motion; 4-out 1-in start; no ordered actions | [MB10] | Chin and Shuffle already in the repo |
| Charlotte DHO counter | Video only; no written steps | [MA86] | Not cited for content |

---

## 21. Counts

"Blocks" = numbered items in this file. "Named entries" counts each separately named play inside a block (O09 = 3, O10 = 3, F06 = 4, G07 = 4). "MSU" = blocks with Michigan State running the action in an opened source.

| # | Alignment family | Blocks | Named entries | MSU blocks | IDs |
|---|---|---|---|---|---|
| 1 | Horns | 31 | 31 | 11 | H01–H31 |
| 2 | 1-4 High (incl. 4-High / Iverson) | 18 | 22 | 7 | O01–O18 |
| 3 | 1-4 Low | 6 | 6 | 0 | L01–L06 |
| 4 | 4-out 1-in | 12 | 15 | 0 | F01–F12 |
| 5 | 5-out | 14 | 14 | 0 | V01–V14 |
| 6 | Box | 3 | 3 | 0 | X01–X03 |
| 7 | Stack / Floppy / Zipper | 4 | 4 | 3 | K01–K04 |
| 8 | Diamond | 0 | 0 | 0 | — |
| 9 | Two-guard front (Princeton and others) | 12 | 15 | 1 | G01–G12 |
| 10 | Triangle | 7 | 7 | 0 | T01–T07 |
| 11 | 3-out 2-in | 4 | 4 | 0 | R01–R04 |
| 12 | Post-entry starts (wing–post–top) | 3 | 3 | 0 | P01–P03 |
| 13 | 2-1-2 / 1-3-1 | 1 | 1 | 0 | W01 |
| 14 | Elbow / high-post entries (alignment varies) | 3 | 3 | 2 | E01–E03 |
| 15 | Secondary / early-offense entries | 7 | 7 | 1 | S01–S07 |
| 16 | Wing dribble-entry starts | 2 | 2 | 0 | D01–D02 |
| 17 | 1-2-2 / Line | 0 | 0 | 0 | — |
| 18 | Alignment not documented | 22 | 22 | 12 | U01–U22 |
| | **Total** | **149** | **159** | **37** | |

- **Beyond the repo:** all 149 blocks are new to `offense_full.md` / `set_taxonomy.md` or are flagged [RICHER VARIANT] of a repo name that had no sequence. Flagged richer variants: H05, H20, H28, the 1-4 Low section (L01–L06), F08, V01, V09, V12, V13, K04, G01, G02, G04, G07, T06, P01, P02, S06, D01, U06, U11. Name collisions: G06, F03, H15/X03, W01/X01/U20. H27 Post-Switch is an alias of the repo MSU "EOQ Horns Set" (`offense_full.md`, [O89]); only H27 Post-Cross is new, so H27 stays one block.
- **MSU seasons covered:** 2011-12, 2012-13, 2013-14, 2014-15, 2015-16, 2016-17, 2018-19, 2020-21 (inferred), 2021-22, 2022-23, 2023-24 (inferred), 2024-25. No 2025-26 MSU half-court set was found (FastModel search [MA20], all 8 pages re-scanned by the fixer, 2026-10-18 (UTC)).
- **Confidence:** every timing window and detection signature is [HEURISTIC]; start spots are template assignments unless the item cites a source for them.

---

## 22. Gaps

- **No timing in seconds** appears in any opened source; all windows were estimated from typical cut speeds (3–6 m/s) and spot distances and must be fitted on film. The only sourced timing cues are spatial (R01 Corey cut, F11 slot cut).
- **Starting spots:** almost every FastModel page shows positions only as diagram images that the fetch tools could not read. Spots are template assignments; confirm on film.
- **MSU usage** was not documented for any Princeton, Triangle, post-split, 5-out early-offense, 4-out quick-hitter or Beilein/Michigan entry. Seven opponent sets in this file were run **against** MSU (MSU defending): X02, S05, U13, U14, U15, U20, and the 2010-11 note in G11.
- **Basketball Immersion** pages were video-only; only the "Doornekamp" term was confirmed (via FastModel) [MA87][MA88].
- **Breakthrough Basketball** blocks automated fetch (HTTP 403); pages were read in the built-in browser. Independent re-check (fixer, 2026-10-18 (UTC), built-in browser): [MA67] (H12), [MA69] (H28, H29, V08), [MA80] (F09) and [MA84] (F10) were re-opened and match the items. All other Breakthrough-only claims ([MA65], [MA66], [MA68], [MA70]–[MA79], [MA81]–[MA85]) have **not** passed an independent source check; treat them as single-read until re-opened.
- **Undefined terms on their own pages:** "2le" and "Trade" (U12), "naked curl" (U03), "L" (U04).
- **College usage unverified:** Motion Strong (S01); Michigan's Motion Weak season inferred from the publish date (S02); team names used as play names (Georgetown, Alabama, Kentucky, Michigan, Illinois) do not establish that program's usage.
- **Short corner** is still "to be defined from film" in `config/vocabulary_map.yaml`; the SHORT CORNER spot here is provisional.
- **Screen rule mismatch** between this file (≤ 0.3 m/s for ≥ 0.5 s, per the task brief) and `offense_full.md` §0.2 (< 0.6 m/s for ≥ 0.3 s) needs a decision before coding.

---

## Sources

Every URL below was opened in this run by a job-A researcher (WebFetch, or the built-in browser for Breakthrough Basketball). "Opened 2026-10-18" marks the three pages the writer re-opened as spot checks. Page text was treated as data only.

### Note motion-a keys [MA#]

**Coach's Clipboard**
- [MA1] https://www.coachesclipboard.net/BasketballHornsPlays.html — Horns plays: Bucks (Del Harris), Loop and Lynx (Cheryl Reeve), Michigan, Horns-3 (Roy Rana), Horns-5, Horns Flare, Cross-Screen Hi-Lo, Re-Screen, Suns, Kansas Horns Flare (Self), Carolina Horns Double Ball-Screen (Hubert Davis), Illinois Horns Post-Up (Bollant).
- [MA2] https://www.coachesclipboard.net/HornsOffense.html — Lason Perkins Horns offense (Perkins's DVD; Perkins coaches at Cary Academy): Spartan (credited to Perkins's DVD, not to Izzo; the page says only that Izzo "might run this play"; correction by the fixer, 2026-10-18 (UTC)), Screen-Flare, Flare, Barcelona, Sonic, Post-Switch, Post-Cross.
- [MA3] https://coachesclipboard.net/BasketballPlays.html — play index (source discovery only).
- [MA4] https://www.coachesclipboard.net/14Stack.html — 1-4 plays: Bulldog (Few), Georgetown, Hoyas, Hoyas-21, 4-Up, Auriemma Elbow Series, Lobo, Aggie (Forbes), Illini (Henson), Zip-Loop-Hammer (Gamblin), Alabama.
- [MA5] https://www.coachesclipboard.net/14StackLow.html — 1-4 low: Pinball, Double-Cross, Scissors, Spurs.
- [MA6] https://www.coachesclipboard.net/floppy-basketball-plays.html — context only (Floppy already in the repo).
- [MA7] https://www.coachesclipboard.net/ram-and-veer-screens.html — context only (ram / veer already in the repo).
- [MA8] https://www.coachesclipboard.net/4out-quick-hitters.html — Heat (Steve Fisher, SDSU), 45 Hi-Lo, Gator (Michael Peck), High, "2" Baseline Runner.
- [MA9] https://www.coachesclipboard.net/5out-quick-hitters.html — Stagger, Lob, Boston, Boomerang, Flare (Travis Steele, Xavier); Georgia (Lennie Acuff, Lipscomb). Opened 2026-10-18.
- [MA10] https://www.coachesclipboard.net/PrincetonOffensePlays.html — Weakside Flash (Lee DeForest); Ear, Hip, Nose (Mark Lane).
- [MA11] https://www.coachesclipboard.net/basketball-Euro-set.html — Euro set Options 1–3; David Blatt.
- [MA12] https://www.coachesclipboard.net/4OutHighMotionOffensePlays.html — Topside, Counter, Flash, W2/W3, Jet-Back (Jesse Shaw).
- [MA13] https://www.coachesclipboard.net/Michigan.html — "Michigan" play steps.

**Better Basketball, HoopStudent**
- [MA14] https://betterbasketball.com.au/motion-weak/ — Motion Weak steps, Horns flow, sideline PnR variation.
- [MA18] https://hoopstudent.com/loop-offense/ — loop action / loop behind; 1-4 low and transition loop examples.

**FastModel PlayBank (generic, NBA, other programs)**
- [MA15] https://playbank.fastmodelsports.com/library/basketball/fastdraw/76630/play-San-Antonio-Spurs-Motion-Strong- — Motion Strong (2015-07-10).
- [MA16] https://playbank.fastmodelsports.com/library/basketball/fastdraw/373481/play-Michigan-Wolverines--Motion-Weak — Michigan Motion Weak (2021-03-21).
- [MA17] https://playbank.fastmodelsports.com/library/basketball/fastdraw/437138/play-Johns-Hopkins-Blue-Jays--Motion-Weak-Cross — Johns Hopkins women (2023-03-07).
- [MA19] https://playbank.fastmodelsports.com/library/basketball/fastdraw/180605/play-Iona--Chin-High — context only (Chin flows).
- [MA59] https://playbank.fastmodelsports.com/library/basketball/fastdraw/361135/play-Duke-Blue-Devils--Wheel-Action — Duke vs MSU (1 Dec 2020).
- [MA60] https://playbank.fastmodelsports.com/library/basketball/fastdraw/288148/play-Bradley-Braves--Early-Offense-Loop-DHO — Bradley vs MSU (2019).
- [MA61] https://playbank.fastmodelsports.com/library/basketball/fastdraw/180893/play-Kansas--5-up-Muscle — Kansas vs MSU (2017).
- [MA62] https://playbank.fastmodelsports.com/library/basketball/fastdraw/123063/play-Purdue--Elbow-Slip — Purdue vs MSU (2016).
- [MA63] https://playbank.fastmodelsports.com/library/basketball/fastdraw/290081/play-Texas-Tech-Red-Raiders--Box-Rip-Lob — Texas Tech vs MSU (2019 Final Four).
- [MA64] https://playbank.fastmodelsports.com/library/basketball/fastdraw/123151/play-Purdue--Handoff-Slip — Purdue ATO vs MSU (2016).
- [MA87] https://playbank.fastmodelsports.com/library/basketball/fastdraw/247181/play-Doornekamp-Action-STS-BLOB — Doornekamp definition (2018-08-04).

**FastModel PlayBank (Michigan State)**
- [MA20] https://playbank.fastmodelsports.com/library/basketball/search/Michigan%20State and https://playbank.fastmodelsports.com/library/basketball/search/Michigan%20State?page=2 , ?page=3 , ?page=4 , ?page=5 , ?page=6 , ?page=7 , ?page=8 — MSU play titles, dates and one-line summaries.
- [MA21] https://playbank.fastmodelsports.com/library/basketball/fastdraw/66974/play-Michigan-State-Forwards-Out-Regular
- [MA22] https://playbank.fastmodelsports.com/library/basketball/fastdraw/67148/play-Michigan-State-Forwards-Out-Wide
- [MA23] https://playbank.fastmodelsports.com/library/basketball/fastdraw/66973/play-Michigan-State-Blast
- [MA24] https://playbank.fastmodelsports.com/library/basketball/fastdraw/105590/play-Michigan-State-1-4-High-Rub
- [MA25] https://playbank.fastmodelsports.com/library/basketball/fastdraw/22122/play-Michigan-State-Elbow-Ball-Screen
- [MA26] https://playbank.fastmodelsports.com/library/basketball/fastdraw/21572/play-Michigan-State-Curl
- [MA27] https://playbank.fastmodelsports.com/library/basketball/fastdraw/357610/play-Michigan-State-Spartans--Elbow-Away-STS
- [MA28] https://playbank.fastmodelsports.com/library/basketball/fastdraw/357611/play-Michigan-State-Spartans--Elbow-Away-Pindown
- [MA29] https://playbank.fastmodelsports.com/library/basketball/fastdraw/180888/play-Michigan-State--Horns-Pistol
- [MA30] https://playbank.fastmodelsports.com/library/basketball/fastdraw/288937/play-Michigan-State-Spartans--Elbow-Punch-Stagger
- [MA31] https://playbank.fastmodelsports.com/library/basketball/fastdraw/289792/play-Michigan-State-Spartans--Horns-Out-Slip
- [MA32] https://playbank.fastmodelsports.com/library/basketball/fastdraw/285961/play-Michigan-State-Spartans--Horns-Swing-Pistol
- [MA33] https://playbank.fastmodelsports.com/library/basketball/fastdraw/288961/play-Michigan-State-Spartans--Horns-Loop-STS
- [MA34] https://playbank.fastmodelsports.com/library/basketball/fastdraw/461577/play-Michigan-State-Spartans--1-4-STS — opened 2026-10-18.
- [MA35] https://playbank.fastmodelsports.com/library/basketball/fastdraw/118860/play-Michigan-State-Piston-Stagger
- [MA36] https://playbank.fastmodelsports.com/library/basketball/fastdraw/118861/play-Michigan-State-Rub-Down-Screen
- [MA37] https://playbank.fastmodelsports.com/library/basketball/fastdraw/67727/play-Michigan-State-Horns-Rub-Triple-Stagger
- [MA38] https://playbank.fastmodelsports.com/library/basketball/fastdraw/289743/play-Michigan-State-Spartans--Horns
- [MA39] https://playbank.fastmodelsports.com/library/basketball/fastdraw/437671/play-Michigan-State-Spartans--Weave-Zoom
- [MA40] https://playbank.fastmodelsports.com/library/basketball/fastdraw/447226/play-Michigan-State-Spartans--Iverson-Ram-Reject-Away
- [MA41] https://playbank.fastmodelsports.com/library/basketball/fastdraw/438159/play-Michigan-State-Spartans--Pin-Down-Circle
- [MA42] https://playbank.fastmodelsports.com/library/basketball/fastdraw/462143/play-Michigan-State-Spartans--Horns-Twist-Veer
- [MA43] https://playbank.fastmodelsports.com/library/basketball/fastdraw/288182/play-Michigan-State-Spartans--Pin-Naked-Curl
- [MA44] https://playbank.fastmodelsports.com/library/basketball/fastdraw/290275/play-Michigan-State-Spartans--Horns-23-Back
- [MA45] https://playbank.fastmodelsports.com/library/basketball/fastdraw/290279/play-Michigan-State-Spartans--Horns-Cutter-15-PNR
- [MA46] https://playbank.fastmodelsports.com/library/basketball/fastdraw/293107/play-Michigan-State-Spartans--L-Option-Post-Up
- [MA47] https://playbank.fastmodelsports.com/library/basketball/fastdraw/16118/play-Horns-Weak-Pin
- [MA48] https://playbank.fastmodelsports.com/library/basketball/fastdraw/335/play-Play-of-the-Day-02-17-2012-1-4-Twist-Lob
- [MA49] https://playbank.fastmodelsports.com/library/basketball/fastdraw/387/play-Play-of-the-Day-03-05-2012-Floppy-Stagger-Punch
- [MA50] https://playbank.fastmodelsports.com/library/basketball/fastdraw/580/play-Play-of-the-Day-05-19-12-Floppy-Loop-Under
- [MA51] https://playbank.fastmodelsports.com/library/basketball/fastdraw/6475/play-MSU-1-4-High-Lob
- [MA52] https://playbank.fastmodelsports.com/library/basketball/fastdraw/16116/play-Zipper-Again
- [MA53] https://playbank.fastmodelsports.com/library/basketball/fastdraw/1716/play-Motion-Go-Duck-In
- [MA54] https://playbank.fastmodelsports.com/library/basketball/fastdraw/1718/play-Quick-Double
- [MA55] https://playbank.fastmodelsports.com/library/basketball/fastdraw/373220/play-Michigan-State-Spartans--Early-Offense-Post-Entry — title / summary only (not counted).
- [MA56] https://playbank.fastmodelsports.com/library/basketball/fastdraw/373223/play-Michigan-State-Spartans--STS-Spain-Action
- [MA57] https://playbank.fastmodelsports.com/library/basketball/fastdraw/409321/play-Michigan-State-Spartans--Stagger-Slip-Curl--Pop
- [MA58] https://playbank.fastmodelsports.com/library/basketball/fastdraw/478091/play-Michigan-St-2le-High-Trade

**Breakthrough Basketball** (read in the built-in browser; WebFetch and curl returned HTTP 403. Re-opened by the fixer, 2026-10-18 (UTC) in the built-in browser: [MA67], [MA69], [MA80], [MA84]; the rest not independently re-checked)
- [MA65] https://www.breakthroughbasketball.com/offense/spanoulis-dho-action
- [MA66] https://www.breakthroughbasketball.com/plays/ — play index (lists "41 X").
- [MA67] https://www.breakthroughbasketball.com/plays/loop
- [MA68] https://www.breakthroughbasketball.com/plays/two-zoom-sets
- [MA69] https://www.breakthroughbasketball.com/plays/zoom-toledo-pitt
- [MA70] https://www.breakthroughbasketball.com/plays/Uconn-Purdue-zoom
- [MA71] https://www.breakthroughbasketball.com/plays/loyola-chicago-opening-set
- [MA72] https://www.breakthroughbasketball.com/plays/spurswheelplay
- [MA73] https://www.breakthroughbasketball.com/plays/x-not-play-tips
- [MA74] https://www.breakthroughbasketball.com/plays/indiana-ghost-hilo
- [MA75] https://www.breakthroughbasketball.com/plays/high-post-exchange-with-pick-n-roll
- [MA76] https://www.breakthroughbasketball.com/plays/14low
- [MA77] https://www.breakthroughbasketball.com/plays/slice-quick-3-out-rub
- [MA78] https://www.breakthroughbasketball.com/plays/g-tech-back-cut
- [MA79] https://www.breakthroughbasketball.com/plays/kentucky-wildcat-lob
- [MA80] https://www.breakthroughbasketball.com/plays/spursgate
- [MA81] https://www.breakthroughbasketball.com/plays/uconn-stagger
- [MA82] https://www.breakthroughbasketball.com/plays/kansas-ball-screen
- [MA83] https://www.breakthroughbasketball.com/plays/play-cross
- [MA84] https://www.breakthroughbasketball.com/plays/how-spurs-run-their-two-man-game
- [MA85] https://www.breakthroughbasketball.com/plays/Youth-Offense-2
- [MA86] https://www.breakthroughbasketball.com/plays/dho-charlotte — video only; not cited for content.

**Basketball Immersion**
- [MA88] https://basketballimmersion.com/ , https://basketballimmersion.com/blog/ , https://basketballimmersion.com/?s=action , https://basketballimmersion.com/teach-zoom-actions/ , https://basketballimmersion.com/3-on-3-wide/ , https://basketballimmersion.com/teaching-stampede-action-with-3-on-3/ — pages exist and are video-only; no content cited.

### Note motion-b keys [MB#]

- [MB1] https://assets.fiba.basketball/image/upload/documents-corporate-regional-offices-europe-programs-fiba-europe-coaching-certificate-fiba-europe-basketball-terminology.pdf — entry list (UCLA, Iverson, Zipper, Power, Diamond, Wing Exchange, Horns; no definition for Power); Straight Split and Reverse Split definitions.
- [MB2] https://hooperuniversity.com/breakdowns/princeton-offense-point-series — Point series alignment, reversal and wave-through entries, Point Over, Point Away, Forwards Out, Carril 1967–1996. Opened 2026-10-18.
- [MB3] https://www.thehoopsgeek.com/princeton-basketball-offense — Princeton alignment; Point, Point Away, Point Over; Low Post Series entry.
- [MB4] https://coachmarchart.substack.com/p/entries-for-your-dribble-drive-motion — DDM entry names (§20).
- [MB5] https://coachingtoolbox.net/plays/diagrams/basketball-plays-elbow-special.html — Elbow Special; Vonn Read.
- [MB6] https://coachingtoolbox.net/?p=3077 — same Elbow Special post.
- [MB7] https://coachingtoolbox.net/michigan-point-backdoor-triple-hand-off — Michigan Point Backdoor Triple Hand Off; Pin Bump Single-Double.
- [MB8] https://coachingtoolbox.net/plays/basketball-plays-2-guard-front.html — Michigan Wolverines Reverse; SFA play.
- [MB9] https://umhoops.com/2012/02/03/inside-the-play-backdoor-screens-shred-indiana-defense/ — Michigan 2011-12 backdoor screens vs Indiana; same play vs MSU in 2010-11.
- [MB10] https://www.mensbasketballhoopscoop.com/michigan-two-guard-offense-learn-from-john-beilein-and-the-university-of-michigan-matt-duble/ — Beilein series; Richmond, WVU, Michigan association.
- [MB12] https://hoopstudent.com/loop-offense/ — loop behind; 1-4 low re-screen loop; transition loop (same page as [MA18]).
- [MB14] https://hoopstudent.com/triangle-offense/ — Triangle entries and options; USC, K-State, Bulls, Lakers.
- [MB15] https://hoopstudent.com/1-4-low-offense/ — 1-4 low alignment; "1-4 flat" alias.
- [MB16] https://coachingtoolbox.net/plays/diagrams/basketball-plays-phoenix-reverse-xavier-shuffle.html — Phoenix Reverse Xavier Shuffle; Vonn Read.
- [MB17] https://hoopstudent.com/basketball-wheel-offense/ — Wheel Parts 1–4; Pinholster, Oglethorpe.
- [MB18] https://en.wikipedia.org/wiki/Wheel_offense — Wheel origin; 2-1-2 to 1-3-1 cycle.
- [MB19] https://www.basketballforcoaches.com/5-out-motion-offense/ — pass-and-cut fill rules; screen-away Options 1 and 2; dribble-at; cut through the nail (Huggins Open Post); post-up.
- [MB20] https://www.hoopcoach.org/initiating-your-offense-an-overlooked-and-under-appreciated-tactic/ — general article on entries; names none (context only).
- [MB21] https://www.hoopsking.com/?s=entry — search page; nothing usable.
- [MB24] https://umhoops.com/2019/02/22/film-room-breaking-michigan-states-transition-offense/ — confirmed only the 2018-19 date and topic (MSU primary and secondary break); nothing used.
- [MB25] https://hoopstudent.com/3-out-2-in-motion-offense/ — wing entry, dribble entry and counter, Corey/Maggette cut and timing cue, Wing series.
- [MB26] https://www.hooperuniversity.com/breakdowns — index (source discovery).
- [MB27] https://www.hooperuniversity.com/breakdowns/northern-iowa-5-out-offense — Northern Iowa "Get"; AJ Green.
- [MB28] https://www.hooperuniversity.com/breakdowns/5-out-actions-to-create-early-offense — Stagger Away, Single Away, Get; Villanova uses 5-out actions in transition.
- [MB29] https://www.hooperuniversity.com/breakdowns/golden-state-warriors-split-action — split steps and reads; Villanova split and slip; GSW double drag + split.
- [MB30] https://hoopstudent.com/basketball-pass-and-cut/ — pass-and-cut steps; mentions of the Laker cut.
- [MB31] https://hoopstudent.com/4-out-1-in-motion-offense/ — 4-out entries; context only (mostly already in the repo).
- [MB32] https://coachingtoolbox.net/plays/diagrams/basketball-plays-john-beilein-double-wing-screen.html — Beilein Triple Wing Screen.
- [MB33] https://blog.drdishbasketball.com/basketball-drills-pinch-post-series-with-jordan-delp — Delp pinch-post reads (§20).
- [MB34] https://coachmarchart.substack.com/p/screening-actions-to-create-triple — FGCU Fake Double Staggers; Arkansas women's decoy actions (§20).
- [MB35] https://hoopstudent.com/basketball-laker-cut/ — Laker cut definition, high and low side, Showtime origin.
- [MB36] https://hoopstudent.com/basketball-glossary — index (source discovery).
- [MB37] https://hoopstudent.com/hawk-offense/ — Hawk set examples; Hubie Brown / Atlanta Hawks.
- [MB38] https://hoopstudent.com/basketball-boomerang-action/ — boomerang definition and examples.
- [MB39] https://hoopstudent.com/basketball-slot-cut/ — slot cut definition, triggers and spatial cue.
- [MB40] https://hoopvision.substack.com/p/cassius-winston-and-top-lock-defense — MSU 2019-20 cross-check only (actions already in the repo).
- [MB41] https://hoopstudent.com/basketball-split-cut/ — split cut steps, options, counters; Dana Altman book credit.
- [MB42] https://hoopstudent.com/basketball-pass-and-screen-away/ — screen-away cutter and screener reads.
- [MB43] https://hoopstudent.com/basketball-stack-offense/ — Stack Examples 1 and 2.

### Fixer re-check keys [MC#] (opened by the fixer, 2026-10-18 UTC)

- [MC2] https://en.wikipedia.org/wiki/2015_NCAA_Division_I_men%27s_basketball_tournament — Michigan State 70, Georgia 63, first round (round of 64), East Region; MSU beat Virginia 60–54 in the round of 32 (used for O06; consistent with O07).
- [MC3] https://en.wikipedia.org/wiki/2013%E2%80%9314_Michigan_State_Spartans_men%27s_basketball_team — schedule: MSU beat Ohio State in overtime on 2014-01-07 (the page gives 73–68 in the table and 72–68 in a note; score not used); lost 67–69 on 2014-03-09 (used for K04).
- Re-opened for checks (keys unchanged): [MA2], [MA8], [MB2], [MA20] all 8 pages; built-in browser: [MA67], [MA69], [MA80], [MA84].

### Opened but failed or blocked (not cited for content)

- [MB11] https://halfcourthoops.substack.com/p/furman-5-out-offense-chin-series (HTTP 404)
- [MB13] https://hoopstudent.com/dribble-entry (HTTP 404)
- [MB22] https://www.championshipproductions.com/cgi-bin/champ/p/Basketball/Six-Effective-Entries-into-the-HighLow-Motion-Offense_BD-01814.html (HTTP 403; Cloudflare block)
- [MB23] https://www.championshipproductions.com/cgi-bin/champ/p/Basketball/Mastering-the-Motion-Offense-Critical-Actions-Breakdown-Drills-High-Scoring-Entries_BD-06089.html (HTTP 403)
- videos.championshipproductions.com (DNS failure)
- https://fastmodelsports.com/library/basketball/fastdraw/123143/play-Xavier--Rip-Motion-Weak-Entry- (404)
- https://www.fastmodelsports.com/library/basketball/fastdraw/116032/play-Warriors-Motion-Weak (404)
- https://fastmodelsports.com/library/basketball/fastdraw/76625/play-San-Antonio-Spurs-Motion-Weak- (404)
- www.fastmodelsports.com copies of pages 357610, 357611, 180888, 288937 (404 on the www host; the same pages opened on the playbank host above)
- Search-snippet-only items (Wikipedia Triangle, MasterClass, Better Basketball "Laker cut herself", FastModel titles, Golden State Motion Strong) were not used as citations and are marked unverified where mentioned.
