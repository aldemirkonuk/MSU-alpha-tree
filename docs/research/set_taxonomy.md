# Basketball Set and Scheme Taxonomy for Tracking-Based Recognition
### Focus: Michigan State men's basketball (Tom Izzo), with Big Ten opponent context

Compiled 2026-10-17. Everything here is paraphrased. Each claim is tagged with a source key such as `[S12]`, and the keys resolve in the **Sources** section at the end. Tags used:

- **[UNVERIFIED]**: plausible, but no opened source confirmed it.
- **[CONVENTION]**: common coaching usage that I'm stating from general knowledge, without a single authoritative source opened.
- **[HEURISTIC]**: a proposed detection rule for this project. It is an engineering choice, not a sourced fact.

---

## 0. Conventions used for templates

**Court frame (half-court).** Use NCAA dimensions with the origin at the center of the rim, x running sideline to sideline and y running toward half-court. The named spots below are [CONVENTION]:

| Spot | Approx. location (ft from rim) |
|---|---|
| Rim / restricted area | r < 4 |
| Dunker spot (L/R) | x ≈ ±8–10, y ≈ 0–3 (baseline, outside lane) |
| Block (L/R) | x ≈ ±6, y ≈ 2–6 |
| Short corner | x ≈ ±12–15, y ≈ 0–4 |
| Elbow (L/R) | x ≈ ±6, y ≈ 15 |
| Nail | x ≈ 0, y ≈ 15 |
| Slot (L/R) | x ≈ ±10–12, y ≈ 20–24 (just outside arc) |
| Top | x ≈ 0, y ≈ 24–27 |
| Wing (L/R) | x ≈ ±18–20, y ≈ 10–15 (free-throw-line extended, outside arc) |
| Corner (L/R) | x ≈ ±21–22, y ≈ 0–5 |

**Detection primitives, all [HEURISTIC].** Each template below is written as an ordered sequence of these events:

- `SCREEN(s → u)`: screener *s* is nearly stationary (speed under about 2 ft/s) for 0.3 s or more. Teammate *u* passes within about 4 ft of *s*, and *u*'s defender's path is deflected or delayed near *s*. A **ball screen** is one where *u* has the ball. Prior art: a rule-based plus ML on-ball-screen detector reached about 82% sensitivity and 80% PPV on SportVU data `[S60]`. Later work classified how screens were defended across 270k screens `[S61]`, and a model of defensive-strategy changes vs. PnR using all 10 players reached about 69% accuracy `[S62]`.
- `DHO(a → b)`: possession changes between two offensive players while they are under 3 ft apart and at least one is moving. No ball flight beyond about 3 ft.
- `CUT(p, path)`: player displacement of 10 ft or more in under about 1.5 s toward the rim or across the lane, labeled by path (basket, backdoor, curl, flare/fade, shallow, UCLA, flex, Iverson, zipper).
- `PASS(a → b)`, `DRIVE(p)`. NBA tracking defines a drive as a touch starting 20 ft or more from the hoop and dribbled to within 10 ft `[S53]`.
- **Screen angle** comes from the screener's body orientation (shoulders) or the cutter's direction relative to the screen. Down = cutter moves away from the baseline. Back/UCLA/rip/flex = cutter moves toward the baseline. Flare = cutter moves away from the ball. Cross = lateral in the paint.
- **Alignment snapshot** is taken at the "set" moment, when the ball crosses half-court plus about 1–2 s or at the first entry pass. Cluster the 5 offensive positions into one of the alignment classes in §1.3.

---

## 1. OFFENSE TAXONOMY

```
OFFENSE
├── 1.1 Transition (primary break)
├── 1.2 Early offense / secondary break (drag, double drag, pistol/21, flow, trailer)
├── 1.3 Half-court alignments (starting formations / "motion starts")
├── 1.4 Continuity & motion systems
├── 1.5 Ball-screen offense
├── 1.6 Post offense
├── 1.7 Off-ball screening actions & cut vocabulary
├── 1.8 Special situations (ATO, BLOB, SLOB, EOC, EOH/EOG, press break, zone offense)
└── 1.9 European/EuroLeague and NBA action vocabulary (secondary labels)
```

Synergy's possession-ending play types make a useful **outcome layer** that sits orthogonal to the set taxonomy. They are Transition, PnR Ball-Handler, PnR Roll Man, Off-Screen, Spot-Up, Isolation, Hand-Off, Cut, Putback, Post-Up, and Misc. Synergy logs UCLA and flex screens as *Cuts*, not *Off-Screen*. It counts *Transition* as any possession before the defense is set, regardless of the shot clock `[S40]`.

### 1.1 Transition (primary break)

| Element | Definition | Detectable signature |
|---|---|---|
| Outlet | First pass after a defensive rebound to start the break `[S20]` | DREB event, then a pass to a guard near the sideline or elbow-extended within about 2 s |
| Lane filling | Players run the right, middle, and left lanes `[S20]` | Three or more offensive players with velocity toward the far basket. Lateral separation: two near the sidelines (\|x\| > 15) and one in the middle |
| Primary break | A break involving only a few players `[S20]` | Shot or rim attack before the 4th/5th offensive player crosses half-court |
| Secondary break | A break involving most players, flowing into early offense `[S20]` | All 5 cross half-court, then an action starts within about 8 s of the change of possession `[S43]` |
| Trailer | A player trailing the first wave `[S20]` | The last offensive player to cross half-court, typically a big who arrives at the slot or top |
| Rim run | A big sprints rim-to-rim [CONVENTION] | Big's path runs from the defensive paint straight to the offensive paint, arriving before the ball is set |
| Two-for-one | Two quick possessions with under 1 minute left `[S20]` | Shot with game clock ≈ 30–40 s plus shot-clock remainder, in late-period context |

**Izzo-style break (documented elements):**
- Izzo's stated principle is "go hard, go fast, but under control". The staff prefers **diagonal** dribbling to straight-line dribbling, and wing lane running is treated as a job in itself `[S8]`.
- MSU pushes the ball off makes *and* misses. Michigan's staff described MSU as running "all five" `[S9]`.
- The FastModel diagram "MSU Transition" is attributed to Izzo, posted by a lower-level coach. In it, the guard must make a pass before reaching the time line or the team flows into the secondary break, and a shooting 4/5 trailer gets a pitch-back three `[S10]`.
- The "MSU Secondary Break" (FastModel, 2015) runs a **DHO with a weak-side down screen** `[S11]`.
- "Rip to Mid Screen Iso" also comes out of secondary. A rip (back) screen for the 4 is followed immediately by a high ball screen ("mid screen") from the 5, then a post isolation for the 4 `[S11][S12]`.
- 2025-26 wing assignment, as players described it in the preseason: Trey Fort runs the right wing and Coen Carr the left `[S13]`. **[UNVERIFIED in games]** Fort later fell out of the rotation `[S14]`.
- Taught through "5-on-0 Break", "Dummy War into Break", and "War Drill into Live Break" `[S6]`.

**Detectable signature for the MSU break [HEURISTIC]:**
1. DREB or opponent make.
2. Outlet or inbound to the PG in under about 2 s.
3. Two wings with \|x\| > 15 and y-velocity above 15 ft/s, ahead of the ball.
4. Big rim-runs or trails.
5. Either a hit-ahead pass before half-court (per `[S10]`) or a DHO/drag in the slot within 8 s.

### 1.2 Early offense / secondary actions

**Drag screen**
- Definition: an on-ball screen set on the move in transition, typically by the trailing big, before the defense is set `[S41][S43]`.
- Alignment: guards and wings fill the lanes into a 4-out 1-in look. The trailer arrives at the slot `[S41]`.
- Actions: (1) the ball-handler pushes to the slot or wing; (2) the trailer screens on the ball, usually angled toward the middle; (3) the screener rolls or pops while the other big holds the dunker spot `[S41]`.
- Counters: **Drag Slip**, where the screener slips to the rim `[S41]`. Reject. "Tag&Go", "Pop", and "Gator" variants `[S43]`.
- Signature: a ball screen 0–8 s after crossing half-court, with the screener's prior velocity pointing up-court. Location is the slot or top. The other three players are already spaced.

**Double drag ("77")**
- Definition: two consecutive ball screens set by two trailers at the three-point line `[S41][S43]`.
- Alignment: both bigs arrive at the top or slots `[S41]`.
- Actions: (1) the first big to arrive screens; (2) the second screens immediately after; (3) typically one rolls and one pops `[S41]`.
- Counters: "Drag Flare", where the 5 flare-screens for the guard who set the drag `[S41]`.
- Signature: two SCREEN events on the same ball-handler within about 1.5 s, both above the arc. Screeners are stacked roughly 4–8 ft apart in depth.

**Pistol / "21"**
- Definition: an early quick-hitter between the PG and a wing on one side. It starts with a pass ahead or a DHO and flows into a ball screen `[S44][S20]`.
- Alignment: the ball-handler is in the slot or wing, a guard in the strong-side corner, and the big at the top (FIBA describes the "Pistol offense" this way) `[S20]`.
- Actions: (1) the 1 pushes to the slot; (2) the 2 lifts from the corner to the wing; (3) a pass/handoff, or a handoff into an immediate ball screen from the big `[S44]`.
- Counters: back-door by the 2 if denied; ghost or slip by the big [CONVENTION].
- Signature: a DHO or pass between 1 and 2 on the same side within 8 s, followed by a ball screen at the wing.

**Flow / secondary continuity**
- Definition: a pre-set sequence that links transition to half-court without a stoppage [CONVENTION]. MSU's version is DHO + weak-side down screen `[S11]`.
- Signature: actions begin before all 5 are in an alignment snapshot. Hand the possession off to the half-court classifier once the shape stabilizes.

### 1.3 Half-court alignments ("motion starts" and entries)

These are **starting shapes**. Most sets are named `<Alignment> <Action>`, e.g. "Horns Flare" or "Box Double Down". The detector should classify alignment first, then the action sequence.

| Alignment | Shape | Typical entries/actions | Signature |
|---|---|---|---|
| **Horns** | 1 at top; two bigs at the elbows; two wings in the corners [CONVENTION]. FIBA lists Horns as an entry without defining it `[S20]` | Horns PnR (single or double), Horns Flare, Horns Rip, Horns Twist, Horns Down (pin-down) `[S45][S7]` | Two offensive players at (±6, 15±3) with the ball at the top and both corners filled |
| **1-4 High** | 1 at top; four across at the elbows and wings [CONVENTION] | MSU 1-4 High PnR / Post Iso; MSU "14-Circle" back-screen layup `[S12]` | Four players with y ≈ 15–22 and spread x, nobody on the blocks |
| **4-High / Iverson start** | Same as 1-4 high; a wing cuts across the elbows | MSU "4-High Iverson Curl" `[S15]` | 1-4 high snapshot, then a wing-to-wing cut through y ≈ 13–18 |
| **1-4 Low** | 1 at top; four along the baseline (corners and blocks) [CONVENTION] | Clear-outs, iso | Four players with y < 6 |
| **Box** | Four players at the corners of a box, usually the blocks and elbows; common for BLOB `[S20]` | MSU Box "Double Down-Screen"; "Screen the Screener" `[S12]` | Two players at the elbows and two at the blocks, ball at the top or out of bounds |
| **Stack / Double-low stack** | Two players at one block `[S20]`, or all four stacked in the paint vs pressure `[S12]` | MSU ISO-4; ISO-3 "Chest" vs pressure `[S12]` | Two or more players within 4 ft of each other on one block |
| **2-guard front ("4-out high post" / Princeton)** | Guards in both slots, wings at FT-line extended, post at the elbow `[S46]` | Chin, Point, backdoor | Two guards at (±10–12, 22–24) with no player at the top |
| **1-3-1** | Point; two wings plus a high post in the middle row; one baseline player | Izzo zone sets "Special", "Special-2", "1-3-1 Double", "Fist" `[S12][S6][S16]` | Players at the top, both wings, the nail/high post, and one on the baseline |
| **Chin** | Princeton 2-guard front with the post at the elbow; the guard cuts off the post's back screen when the ball reverses `[S46][S47]` | Chin back-cut, then drift/flare screen, then 5-out DHO `[S46]` | 2-guard front, a reversal pass, then a guard cuts from the slot to the rim past a stationary big at the elbow |
| **Floppy** | PG at top; shooter(s) under the basket; bigs screen on both sides, one side doubled or staggered `[S20][S48]` | Floppy curl, fade, or reject; pin-down into DHO; hit the screener `[S48]` | One or two players at the rim area at the set moment, with screeners on both blocks/lane lines. The cutter exits to the wing in 1.5 s |
| **Zipper** | A down screen for a low-block player, who cuts straight up to the slot to catch `[S20][S21]` | Zipper into a PnR or DHO | A block player moves at least 12 ft up the lane line to the slot, past a stationary screener |
| **UCLA** | A screen from the high post (or up screen) for a guard who cuts from the top/slot to the low post `[S20]` | UCLA cut, then the screener steps up (UCLA "Step-Up" PnR) | Pass to the wing, then the passer cuts past a big at the elbow toward the block. Synergy logs these as *Cut* `[S40]` |
| **Elevator ("Gate")** | Two screeners side by side open a "door" for a cutter, then close it on the defender `[S20][S49]` | Catch-and-shoot at the top `[S49]` | Two screeners about 3–4 ft apart near the elbows/FT line. The cutter passes between them, and the screeners' gap closes to under 2 ft within 0.5 s |
| **Spain** | PnR plus a back screen on the roller's defender by a third player who then pops `[S19][S20][S21]` | See §1.5 | Ball screen, then within about 1 s a third offensive player crosses behind the screener's defender (stationary near the FT line) and moves to the arc |
| **Chicago / Zoom** | A pin-down that flows straight into a DHO `[S21][S20][S50]` | Zoom into PnR; Zoom "Delay Chicago" `[S50]` | SCREEN(down) for player *u*, then DHO to *u* within 1.5 s, usually at the wing/slot |
| **Hammer** | A weak-side flare/back screen that frees a shooter to the corner while the ball-handler drives baseline; skip to the corner `[S20][S51]` | Spurs Hammer | Baseline DRIVE on one side, a simultaneous SCREEN on the opposite wing with the cutter moving to the corner, then a skip pass across the baseline |
| **Delay** | 5-out with the ball centered to the trailing big at the top as the hub; read and react around handoffs and backdoors `[S50][S52]` | Delay Chicago, Delay Spain, Delay backdoor | Center at the top (x≈0, y≈24) with the ball. The other four are on the perimeter |
| **Swing / 4-out "slots + wings + post"** | Two slots, two wings, one low post `[S30]` | See §1.4 | — |
| **5-out** | Top, two wings, two corners `[S31]` | Delay, DHO chains, 5-out motion | No player inside the arc at the set moment |
| **4-out 1-in** | Two slots, two wings, one block `[S31]` | Motion, dribble-drive | — |
| **3-out 2-in** | Top, two wings, two blocks `[S31]` | High-low | — |

### 1.4 Continuity and motion systems

**5-out motion**
- Rules: positionless; spots are top, wings, and corners. Pass-and-cut / fill `[S31]`.
- Signature: no post occupant. Cut events are followed by perimeter refills along the arc.

**4-out 1-in motion**
- Rules: four perimeter players plus a fixed post `[S31]`.
- Signature: one player stays within 8 ft of the rim for at least 70% of the possession.

**Circle motion**
- Rules: pass, cut, and fill, rotating in one direction `[S31]`.
- Signature: the perimeter rotation direction stays constant.

**Dribble-drive**
- Rules: 4-out 1-in. Gap attacks with little screening `[S31]`.
- Signature: few SCREEN events and many DRIVE events. Weak-side drift to the corners.

**Read & React (Torbett)**
- Rules: a layered rule set rather than a fixed pattern. Layers include dribble penetration with circle movement (rotate the way the ball penetrates), baseline drive spots, pass-and-cut, post reactions, east-west handoff dribbles, back screens, staggers, and a zone layer. It works from any alignment `[S32]`.
- Signature: a penetration event triggers rotation of the other four. The direction of rotation matches the drive side `[S32]`.

**Flex**
- Alignment: 4 around 1 with one low post. The PG starts the offense on the post's side `[S33]`.
- Sequence: (1) a wing cuts baseline off the low post's screen toward the ball (flex cut); (2) the cutter's screener receives a down screen ("screen the screener") and pops to the top; (3) repeat on the other side `[S33][S20]`.
- Counters: 4-man and 5-man variants; built-in reads `[S33]`.
- Signature: a baseline-to-ball-side-block cut past a block screener, followed within about 1 s by a down screen on that screener. Repeats after reversal.

**Shuffle**
- Alignment: five rotating spots (first cutter, point, feeder, second cutter, post) `[S34]`.
- Sequence: (1) entry pass to the feeder; (2) the post screens for the first cutter, who goes over/around or back-door to the rim (the shuffle cut); (3) the post screens for the second cutter to the high post; (4) the point down-screens for the post, who becomes the new point; (5) repeat on the other side `[S34]`. History: Bruce Drake (Oklahoma, 1950s), Bob Spear (Air Force), Dean Smith `[S35]`.
- Signature: a cutter goes diagonally from the weak-side wing over a high-post screener to the ball-side block. Repeats with a role rotation.

**Swing (Bo Ryan / Wisconsin)**
- Alignment: two slots, two wings, one low post `[S30]`.
- Rules:
  - Slot-to-wing pass → the post sets a UCLA screen for the passer, who takes the post.
  - Ball on the wing → the weak side exchanges.
  - Ball in the slot → the weak-side wing gets a flare.
  - Slot-to-slot pass → the post flex-screens for the wing.
  - Denial counters: back screen, or a dribble-at that triggers a shallow cut `[S30]`.
- Under Ryan, it combined 4-out principles, flex screens for deep post touches, backside flares, and exchanges `[S36]`.
- Signature: wing pass → UCLA cut → weak-side exchange, repeating. A flex screen follows reversal.

**Blocker-Mover (Dick Bennett)**
- Alignment: two blockers (bigs) and three movers. Each blocker stays on its own side, between the lane and the arc `[S37]`.
- Rules: blockers screen for movers. Movers read and use screens `[S37]`.
- Signature: two players whose x stays on one side for the whole possession and who participate only as screeners. Three players change sides through screens.

**Princeton (Carril)**
- Alignment: 2-guard front, wings at FT-line extended, post at the elbow `[S46]`.
- Series:
  - **Chin**: back-cut off the post's back screen, then a drift screen for the other guard, flowing to 5-out DHO `[S47]`.
  - **Chin Strong**: UCLA, stagger ball screens, post down screen.
  - **High-Post Chin**: scissor cuts.
  - **Point**: high-post entry plus split action.
  - **Low**: low-post entry in transition `[S46]`.
- Counters: backdoor when denied. Flow to the 1-3-1 zone set `[S46]`.
- Signature: 2-guard front. Frequent back-door cuts (the cutter's path reverses toward the rim when a defender is on the denial side). High-post entries are followed by scissor cuts.

**Triangle (Tex Winter)**
- Alignment: a sideline triangle (post on the block, forward on the wing, guard in the corner), plus a top guard and the weak-side forward at the high post (two-man game) `[S38]`.
- Sequence: (1) the guard passes to the wing and cuts to the corner; (2) post entry; (3) else the weak-side guard or pinch post; (4) the weak-side forward flashes to the elbow for a handoff, backdoor, or PnR `[S38]`.
- Counters vs pressure: guard-to-guard, flash cuts, and center to the high post `[S38]`.
- Signature: three strong-side players at the block, wing, and corner simultaneously after a guard-to-wing pass, with the passer ending in the corner.

**Spread (Underwood, Illinois)**
- Alignment: four interchangeable perimeter players (slots wider than elbow-extended, wings at FT-line extended). The 5 sits at the middle of the FT line `[S39]`.
- Sequence:
  1. Reverse the ball, then enter to the wing.
  2. The 5 back-screens the passer to the rim, who continues to the corner.
  3. The 5 cross-screens for the weak-side wing (who often rejects to the block).
  4. Pinch post to the 5 at the weak-side elbow (handoff + roll).
  5. Elbow PnR.
- Counters: push-flare and dribble entry `[S39]`.
- Signature: the 5 at the nail at the set moment. A back-screen cut off the 5 follows the first wing entry.

**Read-based ball-screen continuities ("Euro" / 5-out ball screen)**
- See §1.5. Example: an empty-side PnR plus a back screen (UNC, 2024) `[S54]`.

### 1.5 Ball-screen offense

| Type | Definition | Ordered actions | Typical counters | Signature |
|---|---|---|---|---|
| **High / middle PnR** | Ball screen at the top of the key [CONVENTION] | Screen → handler attacks → screener rolls/pops/short-rolls | Slip, re-screen, "snake" | SCREEN with the ball at (\|x\|<8, y>20) |
| **Side PnR** | Ball screen at the wing [CONVENTION] | Same as above, on the side | Reject (baseline), "Ice" counters | SCREEN with the ball at \|x\|>12 |
| **Empty-side PnR** | Side PnR with no teammate on the ball-side wing or corner, so no help defender is one pass away [CONVENTION]. Hoop Vision has a dictionary entry on it `[S55]`, and a UNC example appears in `[S54]` | Clear the side → wing ball screen | Back screen on the roller's defender (UNC) | Side PnR plus zero offensive players with same sign(x) and \|x\|>12 other than the handler and screener |
| **Step-up screen** | The screener comes from away from the middle (often from the baseline or below the ball) toward the wing or slot and sets a ball screen with their back to the near baseline, so the handler attacks toward the baseline or middle `[S56]` | — | — | Screener approaches from lower y than the ball-handler |
| **Sprint-up / "sprint" PnR** | The 5 sprints from below the block to set a high screen | Used by MSU vs Duke (2015 Final Four) for Valentine `[S17]` | Weave-into-PnR. Roll-and-seal into the 4's spot (vs a show) `[S17]` | Screener's velocity above 12 ft/s from y<6 to the screen spot |
| **Drag / Double drag** | See §1.2 | | | |
| **Double / "stack" ball screen** | Two screeners side by side. The handler chooses a side | MSU **"Detroit"**: after a DHO and reversal, 4 and 5 set ball screens on both sides of the handler. The non-shooter (5) always rolls and the shooter (4) always pops. Used when the opposing 5 is slow in ball-screen defense `[S12][S18]` | Pop/roll split; kick to the corners | Two SCREEN-ready bigs within 3 ft of the ball-handler on either side simultaneously |
| **Stagger ball screen ("77")** | Two consecutive screens in a line [CONVENTION]. "77" is the CelticsBlog glossary term `[S21]` | — | — | Two screens in sequence along the dribble path |
| **Spain PnR** | PnR plus a back screen on the roller's defender by a third player, who then pops. Older names: "Stack", "Bamberg" `[S19][S22]` | (1) 5 screens for 1; (2) 2/3 back-screens X5; (3) 5 rolls for a lob; (4) the back-screener pops. Reads: lob, kick, pull-up `[S19]` | Variants: Double Spain, Spain Twist, Wide Spain, Delay Spain, Ghost Spain `[S19]` | Ball screen, then a third player moves from the top/slot downward to within 3 ft of the screener's defender within about 1 s, then moves back out to the arc |
| **Ghost screen** | The screener fakes the screen without contact and pops away `[S21]` | — | — | The "screener" approaches within about 5 ft but never becomes stationary, and exits before the handler passes |
| **Slip** | The screener leaves before contact to roll or short-roll `[S21][S41]` | — | — | Screener stationary under 0.3 s, then accelerates to the rim before the handler reaches the screen line |
| **Short roll** | The screener catches in the 4-on-3 window around the FT line. Purdue example: Kaufman-Renn splits the defense, then floats or hits the dunker `[S57]` | — | — | Screener catches at y 10–17 after a ball screen, while the handler is trapped or hedged |
| **Re-screen / "flip"** | The screen is reset in the opposite direction [CONVENTION] | — | — | Two SCREEN events by the same pair, with screener orientation flipped |
| **Twist** | The ball-handler uses two on-ball screens set in opposite directions `[S20]` | — | — | — |
| **Veer** | An on-ball screen followed by an off-ball screen (often a wide pin-down) from the same screener `[S20][S21]` | MSU "Down Screen DHO Veer ATO" (2023): down screen, then DHO 2/4, then 5 fakes a ball screen and pins down for 4 `[S23]` | — | Screener's SCREEN on the ball, then the same screener SCREEN off-ball within 2 s |
| **Ram** | A player sets an off-ball screen for a big, who then sets the ball screen `[S44]`. Michigan used "Iverson Ram" in 2024-25 `[S24]` | — | — | — |
| **Inverted PnR** | A big handles and a guard screens. Michigan's Wolf, 2024-25 `[S24]` | — | — | The ball-handler is the tallest player |
| **Screen own man** | A guard who is top-locked screens for the player guarding him. Winston/Tillman, MSU `[S25]` | — | — | — |

**Roll-man reads:** roll, pop, short roll, slip, seal. Seal example: MSU's Costello rolled into the 4's spot and sealed, opening Dawson's curl `[S17]`.

### 1.6 Post offense

| Action | Definition | Signature |
|---|---|---|
| **Low-post entry** | A wing or slot feeds the block. Swing teaches the "top-down" entry when fronted, and the weak-side slot dives on post feeds `[S30]` | Pass to a player at the block with back to the basket (orientation toward the passer), with the defender behind or fronting |
| **High-low** | The high-post/elbow big feeds the low post. MSU "Chest" and ISO-3/ISO-4 build in high-low looks. The weak-side big flashes to the high post when the wing entry is denied `[S12][S26]` | Pass from (±6, 15) to (±6, 4), with the passer above the receiver |
| **Duck-in** | The weak-side big seals into the lane as the ball reverses [CONVENTION] | Player moves from the weak-side block to the paint middle with the defender on their back |
| **Post split** | Two perimeter players screen/cut off each other after a post entry. FIBA's "Split action" covers ball-side action around a post attack (straight/reverse) `[S20]` | Post catch, then two perimeter players exchange via SCREEN within 2 s |
| **Post iso / clear** | Clear the post side. MSU "Rip to Mid Screen Iso" `[S11][S12]`, ISO-5 `[S12]` | Ball-side perimeter players move to the opposite side after the entry |
| **Pinch post** | A big at the elbow acts as the hub `[S20]`. Used in the Underwood spread `[S39]` and MSU "Iverson to Double Screen" (pinch post, short corner, deep seal isolations) `[S12][S27]` | — |
| **Deep seal** | The post pins the defender with their back for a catch at the rim. MSU "Iverson to Double Screen" `[S27]` | — |

### 1.7 Off-ball screens and cut vocabulary

| Screen/cut | Definition | Reads | Geometric signature |
|---|---|---|---|
| **Down screen / pin-down** | The screener moves toward the baseline and screens for a player coming up. Wing-to-low-post screen `[S20][S21]` | Curl (tight to the paint), straight, fade/flare, back-cut, reject | Screener's velocity is negative y (toward the baseline) before stopping. The cutter's velocity is positive y |
| **Wide pin-down** | A pin-down near the wing or corner `[S21]` | — | — |
| **Flare** | The cutter moves away from the ball to open perimeter space `[S20][S21]` | Skip pass | Cutter's displacement vector points away from the ball |
| **Back / rip / blind** | A screen set on the defender's back `[S20][S21]` | Rip DHO = handoff to the back-screener `[S20]` | Cutter moves toward the baseline, past a screener positioned between them and the rim |
| **Cross** | A horizontal screen in the paint that sends the receiver to the opposite block `[S21]` | — | Both screener and cutter at y<10, with lateral cutter motion |
| **Stagger** | Two screens set one after another for one cutter. FIBA says "non-adjacent, simultaneous" `[S20][S21]` | — | Two stationary screeners 6–12 ft apart along the cutter's path |
| **Double** | Two screens set close together `[S21]` | — | Two screeners within about 3 ft of each other |
| **Elevator / Gate** | See §1.3 `[S20][S49]` | — | — |
| **Hammer** | See §1.3 `[S20][S51]` | — | — |
| **Flex** | Weak-side corner cuts to the ball-side low post using a block screen `[S20][S21]` | — | — |
| **UCLA** | A screen from the high post to the slot/top area, with the cutter going to the low post `[S20]` | — | — |
| **Iverson** | A horizontal cut wing to wing across the top, using two screens at the elbows `[S20][S21]` | Curl ("4-High Iverson Curl") `[S15]` | Cutter moves across x from one side to the other at y≈13–20, passing two stationary players at the elbows |
| **Zipper** | See §1.3 `[S20]` | — | — |
| **Shallow cut** | A cut from the wing or slot to the corner or opposite slot, under the ball-handler [CONVENTION]. Used in the MSU "DHO Horns Chin" `[S28]` | — | — |
| **Gut / wedge / slice** | Middle-floor screen / diagonal screen toward the post / straight back screen on the wing `[S21]` | — | — |
| **Exit** | A screen freeing a player to the perimeter `[S21]` | — | — |
| **Ricky** | Rip-screen cut, stop, then a down screen to the perimeter `[S21]` | — | — |
| **Screen-the-screener (STS)** | The original screener immediately receives a screen. Common in flex and BLOB. MSU "STS ATO BLOB" entries exist on FastModel `[S29]`. Box "Screen the Screener" `[S12]` | — | Screener *s* goes from SCREEN-giver to SCREEN-receiver within 1.5 s |
| **Hawk** | A diagonal screen for a cutter to the basket, from a 1-dribble wing entry. MSU "Hawk Double Cross" (2017): Hawk cut → reversal → double stagger → screen-the-screener `[S29b]` | — | — |

**Cut reads (for labeling).** Curl means a curved path around the screener toward the paint. Fade/flare means a path away. Straight means a lift to the perimeter. Back-cut/reject means the cutter refuses the screen and goes behind the defender `[S21][S48]`.

### 1.8 Special situations

| Situation | Definition / identification | Documented MSU examples | Signature |
|---|---|---|---|
| **ATO** | First possession after a timeout `[S20]`. Hudl/Instat tags ATO shots `[S58]` | "MSU Zipper" ATO quick hitter with 3 options. 4 and 5 cross-screen for 2, then backdoor/lob/curl options `[S29c]`. "Down Screen DHO Veer ATO" (2023) `[S23]`. "DHO Clear Lob", run to open the 2nd half of the 2019 Elite Eight vs Duke: DHO, then the 1 clears to the corner, then 5 back-screens 3 for a lob on the empty side `[S29d]` | Game-state flag: possession start follows a timeout event (from play-by-play) |
| **BLOB** | Baseline out-of-bounds, often from a box or stack `[S20]` | "Screen the Inbounder": the 5 inbounds, then gets a screen for an inside shot. vs 2-3, screen the low zone defenders `[S12]`. "Twist" BLOB to free a top-locked Winston `[S25]` | Ball OOB at y<0, with the inbounder at the baseline |
| **SLOB** | Sideline out-of-bounds | "Line-1": the line set gives the inbounder a give-and-go, a double screen for the 1, and a slip `[S12]`. "Tom Izzo SLOB 1" (2015): double screen for the 1, iso for the 2, DHO, dive, and kick `[S29e]` | Ball OOB at \|x\|≈25 |
| **End of shot clock (EOC)** | Quick hitters run with about 10 s left `[S6]` | Izzo teaches "end of shot clock quick hitters" `[S6]` | Action starts at shot clock ≤10 |
| **End of half / game (EOH/EOG)** | Last possession(s). Two-for-one `[S20]` | FastModel "EOQ Horns" MSU entry exists (title only) `[S29f]` | Game clock ≤ shot clock |
| **Press break** | Offense vs full-court pressure `[S20]` | **[UNVERIFIED]**: no MSU-specific press-break source opened | Defenders pressing in the backcourt (see §2.6) |
| **Zone offense vs 2-3** | Attack gaps, high post, short corner, overload, skips, and transition before the zone sets `[S59]`. FIBA: one-guard front vs 2-3/2-1-2 `[S20]` | Izzo 1-3-1 sets: **"Special"** (the 4 cuts around the 5's screen on the low outside zone defender; reversal to an open shot) and **"Special-2"** (the 1 cuts to the short corner/corner off the 5's screen; skip) `[S12]`. **"1-3-1 Double"** with a double screen `[S6]`. **"Fist"/"Fist Down"**, used vs Syracuse and Florida `[S16][S12]` | Offense in 1-3-1, ball movement, a screen on a zone defender ("screening the zone"), and a baseline runner |
| **vs 3-2 / 1-2-2 / 1-3-1** | FIBA: two-guard front vs 1-2-2 and 1-3-1 zones `[S20]` | Izzo's 1-3-1 sets are described as working against 2-3, 1-2-2, and 1-3-1 `[S6]` | Two offensive players at the slots vs a single top defender |
| **vs match-up zone** | Use man-offense cutting and screening, flash a guard to the high post, baseline runner, force the switch `[S63]` | — | — |
| **vs junk (box-and-1, triangle-and-2)** | Run normal offense, ball movement, inside-out, patience. Ball screens for the chased player (the chaser has no help) `[S64]` | — | — |

### 1.9 European / NBA action vocabulary (secondary labels)

| Term | Meaning | Source |
|---|---|---|
| Spain | PnR plus a back screen on the roller's defender (formerly "Stack"/"Bamberg") | `[S19][S20][S22]` |
| Chest | (a) FIBA: just a chest pass. (b) Coaching set name: MSU "Chest" (the wings get down screens from 4 and 5, then a high-low flash) and "Chest Down" (adds a UCLA cut, then a 5 ball screen, then a double screen) | `[S20][S26][S11]` |
| Delay | 5-out with the ball to the big at the top as a hub. From D'Antoni-era usage. FIBA also uses "delay offense" for clock-killing | `[S50][S52][S20]` |
| Floppy | Shooter starts under the rim; screens on both sides | `[S20][S48]` |
| Hammer | Weak-side flare to the corner with a baseline drive and skip | `[S20][S51]` |
| Iverson | Wing-to-wing cut over elbow screens | `[S20][S21]` |
| Elevator / Gate | Two screeners close the "doors" | `[S20][S49]` |
| Chicago / Zoom | Pin-down into DHO | `[S20][S21][S44]` |
| Veer / Twist / Ram / Pistol / Shake / Slide (Hoiberg roll) / Gortat roll | Listed in the FIBA Europe terminology | `[S20]` |
| 77 | Stagger / double-drag | `[S21][S43]` |
| Get / Away | Get = a DHO toward the ball. Away = a screen away from the ball | **[CONVENTION; not sourced]** |
| Horns Rip / Rip Away | Rip (back) screen variations used by MSU in 2024-25 | `[S24b]` |

---

## 2. DEFENSE TAXONOMY

```
DEFENSE
├── 2.1 Man principles (pack line, gap/help, pressure/deny, no-middle)
├── 2.2 Ball-screen coverages
├── 2.3 Off-ball screen coverages
├── 2.4 Post defense
├── 2.5 Zones (2-3, 3-2/1-2-2, 1-3-1, 2-1-2, 1-1-3, match-up)
├── 2.6 Presses (full / 3/4 / half; 1-2-1-1, 2-2-1, 1-3-1, run-and-jump, match-up press)
├── 2.7 Junk / combination (box-and-1, diamond-and-1, triangle-and-2)
└── 2.8 Mid-possession scheme switches (hybrids)
```

### 2.1 Man-to-man principles

**Pack line**
- Definition: everyone except the on-ball defender stays inside an imaginary line about 16 ft from the rim. The ball is pressured. Help sits in the gaps. Defenders fight through screens and avoid switching (Bennett). Closeouts on the catch force the ball toward the middle `[S65]`.
- Signature: off-ball defenders' distance to the rim is under 16–17 ft, even when their man is beyond the arc. The on-ball defender is within about 3 ft of the ball.

**Gap / help (sagging) man**
- Definition: off-ball defenders sit between their man and the ball (FIBA: "pressure man-to-man" means defenders stay between their man and the ball) `[S20]`. Izzo teaches a "six eye" half-court positioning `[S6]`.
- Signature: off-ball defender positions lie near the segment between their man and the ball, roughly 1/3 of the way from the man.

**Deny / pressure**
- Definition: the off-ball defender is in the passing lane, one pass away. "Top-lock" means guarding the top side so a cutter can't come off a down screen toward the ball `[S25][S19]`.
- Signature: the defender lies on the man-to-ball line within about 3 ft of the man. A top-locked defender is *above* (higher y than) their man.

**No-middle**
- Definition: force the ball to the sideline and baseline [CONVENTION]. Ice (§2.2) is its ball-screen form `[S20]`.
- Signature: on-ball defender offset toward the middle (smaller \|x\|) relative to the ball-handler.

**Izzo stance cues**
- Square stance. One hand up. Step to split the stance to force direction. Contest passes as well as shots `[S66]`.
- Signature: n/a (needs pose).

### 2.2 Ball-screen coverages

The positions below cover the **screener's defender (X-big)** and the **ball defender (X-ball)**. Signatures are measured at the moment the handler reaches the screen line [HEURISTIC]:

| Coverage | Positions | Typical rotation | Signature |
|---|---|---|---|
| **Drop** | X-big sits a few steps below the screen and backpedals `[S20][S67]`. Contains the ball and the roller until X-ball recovers `[S68]` | Low man tags the roller as needed | X-big's y is 6–15 ft below the screen, and X-big is between the handler and the rim. X-ball goes over |
| **At the level / "up to touch"** | X-big starts at the screen's level, touching the screener `[S20]` | — | X-big y ≈ screen y ± 2 ft |
| **Flat hedge** | X-big starts just below the screen level and contains, between drop and level `[S20]` | — | X-big about 2–5 ft below the screen, lateral to the handler's path |
| **Hedge / show (hard)** | X-big steps into the dribbler's path above the screen, then recovers `[S20][S67]` | Weak-side rotation tags the roller until X-big recovers `[S69]` | X-big moves above the screen line (toward half-court) by 2 ft or more and lateral to the handler. Then a recovery sprint back to the screener within about 1.5 s |
| **Blitz / trap** | X-big positions above the screen and traps with X-ball. Two defenders in a V on the handler `[S20][S67]` | Help (the "low man") rotates to the roller, and the weak side zones up `[S67]` | Two defenders within 4 ft of the handler for 1 s or more, beyond the screen line |
| **Switch** | Defenders exchange assignments `[S20][S67]` | Possible tag of the roller before the switch completes `[S67]`. "Black" in one coach's terms `[S68]` | After the screen, X-big's nearest offensive player is the handler, and X-ball's nearest is the screener, persisting 2 s or more |
| **Ice / blue / down / fan / push-down** | X-ball forces the handler away from the screen toward the sideline/baseline. X-big mirrors and covers the penetration line `[S20][S67][S68]` | — | On a side PnR, X-ball positions between the handler and the screen (above or middle side) *before* the screen. X-big below, at the level, toward the baseline |
| **Under** | X-ball goes beneath the screen (between the screener and the rim) `[S67]` | — | X-ball's path passes on the rim side of the screener |
| **Over** | X-ball fights over the top of the screen `[S20][S67]` | — | X-ball's path passes on the ball/handler side of the screener |
| **Through** | X-ball goes between the screener and X-big (named in FIBA, undefined there) `[S20]` [CONVENTION] | — | X-ball passes between the screener and X-big |
| **Weak** | X-ball forces the handler to their weak hand, irrespective of screen direction `[S20]` | — | X-ball offset toward the handler's strong-hand side |
| **Top-lock (vs off-ball/Spain)** | Deny the top side of a back-screener or cutter. Also a Spain counter `[S19][S25]` | — | — |
| **Pre-switch / "next"** | Swap assignments before the screen. Early weak-side rotation vs Spain `[S19]` | — | — |

**Coverage spectrum.** Hoop Vision orders teams from aggressive (attack the handler: hedge or blitz) to sagging (drop). Houston and Virginia sit on the aggressive side, and Creighton and Alabama on the sagging side `[S70]`. A continuous "aggressiveness" feature works well here, defined as X-big's y relative to the screen at the handler's arrival (positive = above).

### 2.3 Off-ball screen coverages

| Coverage | Description | Signature |
|---|---|---|
| Chase / trail | The cutter's defender follows the cutter's path. Down screens are usually not switched, and defenders follow the cutter `[S71]` | Defender path ≈ cutter path, with lag under 1 s |
| Shoot the gap / under | The defender goes between the screener and the rim to beat the cutter to the spot (allowed on weak-side screens in pack line) `[S65]` | Defender's path is on the rim side of the screener |
| Switch | Back screens and flares are usually switched. Inside post screens: step under, then switch on a high cut `[S71]` | Defender exchange persists after the screen |
| Top-lock | Deny the top side of the cutter to force a back-cut or curl `[S25][S19]` | Defender above the cutter before the screen |
| Bump / show | Screener's defender bumps the cutter, then recovers `[S71]` | Brief displacement of the screener's defender toward the cutter, then return |
| Scram switch | When a guard is on a post, the adjacent big takes the post on the entry pass and the guard rotates out `[S71]` | — |

### 2.4 Post defense

| Technique | Description | Signature |
|---|---|---|
| Front | Defender between the ball and the post. Some coaches front when the ball is below the FT line `[S65]` | Defender's position on the post-to-ball line, nearer the ball than the post |
| 3/4 (high side) | Defender on the high side of the post, one arm in front. Bennett's pack line plays 3/4 high side `[S65]`. Stephens (Western Michigan) also teaches 3/4 top side, where the low man attacks the lob, not the post defender `[S72]` | Defender lateral/above the post, at about 45° from the ball line |
| Behind | Defender between the post and the rim [CONVENTION] | Defender's position on the post-to-rim line |
| Double the post | Big-to-big, or "choke" the post `[S65]` | Two defenders within 4 ft of the post with the ball |

### 2.5 Zones

| Zone | Shape | Signature |
|---|---|---|
| **2-3** | Two guards at the top, two forwards near the blocks or corners, center in the middle `[S59][S20]` | At the set moment, two defenders at y≈18–22, three at y<10. Players stay in regions while offensive cutters pass through (low correlation between defender and any single offensive player's path) |
| **3-2 / 1-2-2** | One top defender, two at the elbows or wings, two low [CONVENTION]. FIBA lists 1-2-2 `[S20]` | — |
| **1-3-1** | Point, three across (two wings plus middle), one baseline runner [CONVENTION]. Also used as a trapping defense `[S59]` | A defender stays near the nail. The baseline defender runs corner to corner |
| **2-1-2 / 1-1-3** | Listed in FIBA `[S20]` | — |
| **Match-up zone** | Zone positioning, but each defender matches a man in their area. Players switch assignments as cutters pass through `[S20][S73]` | Man-like tight coverage on the ball and one-pass-away. Assignment hand-offs occur when cutters cross region boundaries |

Izzo's MSU is "90-some percent" man, and the 2-3 zone is practiced as a situational change-up (e.g., for foul trouble) `[S74]`. Purdue occasionally uses a 1-2-2 match-up zone `[S75]`.

### 2.6 Presses

| Press | Description | Signature |
|---|---|---|
| **Full-court man / pressure** | Man-to-man in the frontcourt `[S20]` | Five defenders in the backcourt (from the offense's perspective), with man correlation |
| **1-2-1-1 (diamond)** | Ball/disruptor on the inbounder, two wings, a middle interceptor, and a safety. Traps the inbound corner, then the next trap on the over-pass `[S76][S20]` | One defender at the baseline, two near the FT line extended, one at about half-way to half-court, and one deep |
| **2-2-1** | Zone press listed by FIBA `[S20]`. Two front, two middle, one back [CONVENTION]. Usually a 3/4-court containment-then-trap | Two defenders near the FT line (backcourt), two at half-court, one deep |
| **1-3-1 (full-court)** | Listed by FIBA `[S20]` | — |
| **Run-and-jump** | Man press with no fixed trap spots. The help defender "jumps" a middle-driving dribbler, and the original defender runs to the open man. Sideline traps. Dean Smith origin `[S77]` | Defender exchange initiated by a help defender running at the ball, with a speed-dribbler and the original defender leaving |
| **Match-up press ("80")** | Matches the offense's up-count. Main trap on the sideline near half-court. Middle uses run-and-jump `[S78]` | — |
| **Half-court trap / 3/4-court** | Containment that traps after half-court [CONVENTION] | Trap events with y within about 10 ft of half-court |

### 2.7 Junk / combination defenses

| Defense | Description | Signature |
|---|---|---|
| Box-and-1 | Four in a zone box plus one man-to-man chaser `[S20]` | Four defenders hold box regions (two at y≈15–18, two at y<8). One defender's path correlates highly with one offensive player |
| Diamond-and-1 | Four in a diamond plus one chaser `[S20]` | — |
| Triangle-and-2 | Three in a zone triangle plus two chasers `[S20]` | Two high-correlation chasers plus three region defenders |

### 2.8 Mid-possession scheme changes (hybrids)

| Hybrid | Description | Signature |
|---|---|---|
| Zone → man on a trigger | e.g., a 1-2-2 zone that switches to man once the ball hits the high post (Boston College), or on the 2nd perimeter pass (Reyer Venezia) `[S79]` | Defender–offense assignment correlation jumps from low to high after a trigger event |
| Man → zone on a trigger | e.g., Žalgiris falls into a 2-3 on a post catch, and Real Madrid on the 2nd DHO `[S79]` | Correlation drops after a post catch or a DHO |
| Situational switching | Switch only after timeouts, on wing PnRs, or in the last 5–10 s of the clock. "1-4 switching" keeps the center out of switches `[S71]` | — |
| Coverage change by personnel | Izzo surprised Michigan in 2019 by switching ball screens with his 5. His usual coverage was flat or hard hedge with his bigs `[S69]` | Coverage label changes within a game. Track per screener-defender identity |

**Detector design note [HEURISTIC].** Compute a per-frame assignment matrix between defenders and attackers (Hungarian matching on distance, smoothed). Man coverage gives stable assignments that follow cutters. Zones give region-stable defenders whose assignment changes when cutters cross. A hybrid shows a regime change. Tian et al. used matched one-on-one relationships to detect defensive strategy changes `[S62]`.

---

## 3. MICHIGAN STATE SPECIFICS (Tom Izzo)

### 3.1 Program identity (multi-season)

- **Rebounding as identity.** Izzo's "War" drill is a 5-on-5 scramble for one ball. His defensive-rebounding technique is "hit-find-fetch" rather than a classic box-out. MSU led the nation in total rebounding % in 2008-09 (56.8%) and 2009-10 (56.3%) `[S1]`. An opposing coach (Louisville's Pat Kelsey, 2026) called Izzo "one of the great offensive rebounding gurus" `[S2]`.
- **Transition.** See §1.1. Izzo said that when MSU plays fast, "we're a better team" (2015) `[S3]`. "Go hard, go fast but be under control", with diagonal dribbling (2021) `[S8]`. MSU led the Big Ten in fast-break points per game (Feb 2025) `[S9]`.
- **Man-to-man base.** MSU is "90-some percent" man, with a 2-3 zone as a change-up `[S74]`. Izzo's teaching includes "six eye" positioning, shell variations, Negaunee, Beat and Belt, Three-Man DHO Switching, Pin Down & Flares, and ball-screen drills against side and top PnR `[S6]`.
- **Ball-screen defense (historical).** Bigs "flat or hard hedge". Weak-side rotations tag the roller, then bigs recover. In 2019 vs Michigan, MSU switched ball screens with the 5 on 27 possessions, allowing 0.67 PPP `[S69]`.
- **Ball-screen defense (2024-25).** Aggressive: hedge-and-recover, sometimes blitz. Bigs (Zapala, Cooper, Kohler) hedged hard, which opened slips. Izzo adjusted by putting Richardson and Kohler in the gaps to bump the roller `[S24b]`.
- **Ball-screen defense (2025-26).** **[UNVERIFIED]** No opened source describes the 2025-26 coverage. What is documented: opponents took 47.4% of shots from three (15th-highest rate in D-I), and opponents shot 46.0% on twos, both as of mid-January 2026 `[S80]`. That fits a paint-protecting scheme around Kohler and Cooper, but the specific PnR coverage needs film tagging.
- **Offensive system (sources).**
  - "Pro-style" half-court sets with a freelance element.
  - Horns and **"452"** quick hitters with counters.
  - 1-3-1 zone quick hitters ("Special", "1-3-1 Double", "Fist").
  - End-of-clock quick hitters `[S6][S12][S16]`.
  - 2024-25 vs Michigan: ball-screen and handoff actions, **Horns Rip**, **Rip Away**, down screens for shooters off rip screens, back screens, plus offensive rebounding `[S24b]`.
  - Cassius Winston era: the PG often gives the ball up early and then runs screening actions. Counters to top-locking included screening his own man, a Twist BLOB, and cutting under the screen `[S25]`.

### 3.2 Catalog of documented MSU sets (template candidates)

| Set | Year/source | Alignment | Ordered actions | Counters/options | Detection cues |
|---|---|---|---|---|---|
| **1-4 High PnR / Post Iso** | Coach's Clipboard `[S12]` | 1-4 high | 3 curls around 5, then 1→3, then 1 cuts to the opposite corner, then 5 ball-screens for 3 | Roll to 5. 4 pops to the top, and 5 posts for a 4→5 entry | 1-4 high, then a curl around the high post, then a wing ball screen |
| **14-Circle** | `[S12]` | 1-4 high | 2 cuts under to the wing, 3 cuts high over the posts, 1→5, 3 uses 4's screen to the rim, 5→3 | 4 slips if switched | High-post catch, then a back-cut past the other elbow big |
| **Box Double Down** | `[S12]` | Box | 5 pops for the pass, 1 goes over 4's screen, 5→4→1, 3 back-screens for 5 posting, and 3+4 double down-screen for 2 | 2 for three | Box, then a double down-screen (two screeners stacked) on the opposite side |
| **ISO-4 (high-post iso)** | `[S12]` | Double-low stack | 1 dribbles left, 2 to the corner, 3 to the wing, 4 flashes to the opposite high post for an iso | 5 for high-low | Stack, then the big flashes to the elbow, then a clear |
| **ISO-3 "Chest" (high-post iso)** | `[S12]` | Paint stack vs pressure, or 4/5 on the wings with 3 at the high post | 3 flashes to the high post, 1 and 2 X-cut, down screens from 4 and 5 | High-low to 4, and 5 flashes to the elbow | Wing X-cuts under a high-post catch |
| **Chest / Chest Down** | FastModel 2015 `[S26][S11]` | Two wings, two posts | 4 and 5 down-screen the wings (rejects allowed). Weak-side big flashes high for high-low. *Down*: adds a UCLA for 1, a 5 ball screen, and a double screen | Rejects, high-low | Two simultaneous down screens for the wings at the entry |
| **Back-Screen PnR** | `[S12]` | — | 5 back-screens for 4, then 5 ball-screens for 1 | Roll, corner kick, 4 to the elbow | Veer-like screener sequence |
| **Detroit (double ball screen)** | `[S12][S18]` | 2 at top after DHO and reversal | 4 and 5 set ball screens on both sides of the handler. The non-shooter rolls and the shooter pops | — | Two bigs flank the handler simultaneously |
| **Sprint-up ball screen** | Hoopscoop (2015 FF vs Duke) `[S17]` | 5 below the block | 5 sprints up for a high PnR. Also weave-into-PnR, and sprint-up plus stagger for the shooter | Roll-and-seal into the 4 spot | Screener's velocity from the baseline to the top |
| **Rip to Mid Screen Iso** | FastModel 2015 `[S11][S12]` | Secondary break | 5 rip-screens for 4, then 5 high-screens for 2, 2→1→4 post iso | DHO variation | Back screen then ball screen by the same screener (veer-like) within 2 s |
| **Over-Under** | FastModel 2015 `[S12b]` | Wing entry | 3→1, flare for 3, 2 runs baseline off 4, 1→2, 1 off the flare, 3 off the baseline screen | Post-ups | Simultaneous flare plus baseline-runner screens |
| **Iverson to Double Screen** | FastModel 2015 `[S27]` | 3 pinch post, 4 short corner, 5 deep seal | 3 to the high post, then a handoff to 1. If kept, a 4+5 double screen for 2 | Pinch-post, short-corner, and deep-seal isos | — |
| **Hawk Double Cross** | FastModel 2017 (Bridges, Ward) `[S29b]` | 1 dribbles at top, 3 under the basket | Hawk diagonal screen 4→2, reversal to 4, 3+5 double stagger for 2, 3 screens 5, STS, then a final PnR | Many | Diagonal screen, then a stagger, then STS |
| **Horns Quick Screen (Horns Down)** | FastModel 2018 (for Bridges) `[S29g]` | Horns | 1→5. 4 fakes a dive, then comes off 1's pin-down for three | — | Horns, then a guard down-screens for an elbow big |
| **Iverson Stagger Hit** | FastModel 2018 `[S29h]` | — | 4+5 stagger for 3, 1 cuts to the corner, a second stagger for 2. Screeners dive if help comes | — | Double stagger twice |
| **DHO Horns Chin** | Hoopscoop 2016 `[S28]` | Horns | 1→2, 1 shallow-cuts to the corner, 3 to the top, 4 back-screens 2 (chin), then 4 ball-screens for 3 | Back-cut or post-seal by 2 | Horns, then a shallow cut, then a back screen from an elbow big |
| **4-High Iverson Curl** | FastModel 2023 `[S15]` | 4-high | 2 Iverson cuts across 4 and 5, 1→4, 4 hits 2 on the curl | — | — |
| **Down Screen DHO Veer ATO** | FastModel 2023 `[S23]` | — | 5 down-screens 2, DHO 2–4, 2 to the corner, 4→1, 5 fakes a ball screen (veer) and pins for 4 | — | — |
| **DHO Clear Lob** | FastModel 2019 (Elite Eight vs Duke) `[S29d]` | — | 1 DHOs to 3, 4 down-screens 2, 3→2, 1 clears to the corner, 5 back-screens 3, lob 2→3 on the empty side | — | — |
| **MSU Zipper (ATO, 3 options)** | Coaching Toolbox `[S29c]` | — | 4+5 cross-screen for 2. Options: (1) 4→5 cut; (2) backdoor for 2 off 4's catch; (3) curl | — | — |
| **Special / Special-2 (vs 2-3)** | `[S12]` | 1-3-1 | See §1.8 | Inside to 5 | 1-3-1 vs a 2-3, with a screen on a low outside zone defender |
| **Screen the Inbounder (BLOB)** | `[S12]` | Stack/line, 5 inbounds | 4 seals, 3 takes the inbound in the corner, 3→1, 2 screens for 5, then 3 down-screens 2 for three | vs 2-3: screen both low defenders | — |
| **Line-1 (SLOB)** | `[S12]` | Line | 3 catches, 2 give-and-go, 1 off the 4+5 double screen | 5 slip, 4 three | — |
| **Twist BLOB** | Hoop Vision 2020 `[S25]` | Winston in the weak-side corner for a pin-down | Rejects, goes under the basket, runs Twist with Henry | — | — |

Named but not described in opened sources: Hawk, Triple-Screen, Screen the Screener, ISO-5, ISO-2, Two Ball-Screens, Slip-Reverse, Double Ball-Screen, Fist, Double, 33, Double-Screen the Screener, Two Double-Screens, Line-2, X-ISO, Double-Slip `[S12]`. Also "452" `[S6]`, "Double Fan", "Double Flare Pin", "Pin Down Circle", "Tom Izzo: Wizard", and "STS ATO BLOB" (FastModel titles only) `[S29]`. **[UNVERIFIED contents]**

Practitioner playbooks also exist: "13 Offensive Plays from Michigan State" (9 man, 2 zone, 1 BLOB, 1 SLOB; Wes Kosel, CoachTube) `[S81]`, and "Tom Izzo Michigan State Playbook" (CoachTube; not opened).

### 3.3 2024-25 team (30-7, 17-3 Big Ten champions; lost the Elite Eight to Auburn)

- Record, title, and awards: Izzo was Big Ten Coach of the Year. Akins made the All-Defensive team `[S82]`.
- As of Feb 11, 2025 (conference only): 1st in the Big Ten in PPP allowed. Opponents shot 28.3% on 3P and 46.5% on 2P. 1st in OR%. 3rd in DR%. **Lowest 3PA volume in the Big Ten.** 1st in FT rate. 15th in TO rate. 10 players averaged 5.0–13.4 ppg. Fears' assist rate was 43.5% (2nd nationally) `[S83]`.
- KenPom adjusted defense ranked 6th on Feb 28, 2025. Closing-lineup paint protection came from Kohler and Cooper `[S84]`.
- Coverage details: §3.1 (hedge/blitz, gap bumps) `[S24b]`.
- Data caution: one fetched Wikipedia summary listed Kohler at 20.8 ppg for 2024-25. That conflicts with other context (balanced scoring with no one above 13.4 ppg `[S83]`) and is likely a parsing error. **Treat it as [UNVERIFIED]**.

### 3.4 2025-26 team (27-8, 15-5 Big Ten; lost the Sweet 16 to UConn 67-63)

- Record and results `[S85]`.
- **Jeremy Fears Jr.:** 15.2 ppg and 9.4 apg (led the nation). School single-season assist record (328). 16 assists vs Louisville, an MSU NCAA-tournament record `[S85][S86]`. Assist rate was 49.9% at mid-season (nation-leading, KenPom). 0-for-11 on 3P in early Big Ten play `[S14]`. He shot 32.1% on 3P for the season `[S86]`.
- **Fears' honors conflict:** Spartan Avenue says second-team All-American `[S86]`, ITH says first-team All-Big Ten `[S87]`, and the Wikipedia fetch said honorable mention. **[CONFLICT; verify]**
- **Fears scouting:** strong PnR operator, lob and tight-window passer, good transition tempo. Can get caught on screens. The jumper is a question mark `[S88]`.
- **Jaxon Kohler:** 12.5 ppg and 8.9 rpg on 50% FG, about 39% 3P `[S86]`. Mid-season he was 32-for-60 on 3P, 2nd in Big Ten DR% `[S14]`. Improved 3P shooting enabled pick-and-pop and spacing that pulled his defender out `[S89]`.
- **Carson Cooper:** 11.1 ppg, 7.1 rpg, 1.0 bpg, 58.4% FG `[S85][S86]`. 1st in the Big Ten in FT rate over the first five league games `[S14]`. Described as a rim protector `[S90]`.
- **Coen Carr:** about 12.0 ppg and 5.4–5.8 rpg, about 52% FG, about 28% 3P `[S85][S86]`. A rim-pressure, back-door, and lob threat. Strong offensive rebounder `[S14][S91]`.
- **Team stats:**
  - Mid-January 2026: 3rd in KenPom AdjD (Jan 12) `[S14]`, then 2nd nationally (Jan 15) with Big Ten-best 90.6 pts/100 `[S80]`.
  - Top-ranked nationally in DR% and 10th in OR% `[S14]`. 37.1% OR in Big Ten play by late February `[S87]`.
  - **Last in the Big Ten in TO% (23.9%)** in early league play `[S14]`.
  - Won the fast-break battle 25-12 vs Indiana `[S87]`.
- **Offensive concept:**
  - Rim pressure via Fears' penetration, creating back-door dunks for Carr and kick-out threes `[S91]`.
  - Two bigs (Kohler + Cooper) for paint advantage and the glass `[S14][S90]`.
  - Recurring problems at season's end: turnovers, 3P defense, and slow starts `[S92]`.
- **2026-27 outlook:**
  - Kohler and Cooper depart. Fears, Carr, Teng, Scott, Ward, and Glenn return.
  - Charlotte C Anton Bonke (7-2) transfers in `[S87b]`.
  - Templates should therefore not overfit to the two-big 2025-26 structure.

### 3.5 What is NOT publicly documented (gaps to fill with film)

- The current-season names of MSU's sets. Public diagrams are mostly 2015–2023 and were drawn by outside coaches.
- MSU's 2025-26 PnR coverage by matchup.
- Press-break structure.
- How many players crash the offensive glass versus get back. The Grantland piece does not specify `[S1]`.

**Recommended:** hand-label 30–50 MSU possessions per set family from the available footage to confirm which of the §3.2 templates are still used.

---

## 4. Big Ten opponents' documented systems (brief)

**Purdue (Matt Painter)**
- Post-centric, four-around-one. Bigs finish or kick to shooters `[S75]`.
- Braden Smith is the engine, with a 44.2% assist rate `[S75]`.
- More ball screens for Smith from 2023-24 `[S93]`.
- High PnR with a dunker, short roll by Kaufman-Renn, side-PnR reject-to-lob `[S57]`.
- Defense: man with an occasional 1-2-2 match-up zone `[S75]`.

**Wisconsin (Greg Gard)**
- The legacy Swing offense (§1.4) `[S30][S36]`.
- 2024-25 makeover: a ball-screen-heavy, NBA-style read attack that encourages early-clock shots. School records for 3PM/3PA. Tempo ranked 155th vs about 321st historically. Kirk Penney was the de facto offensive coordinator `[S94]`.
- 2025-26: more pick-and-pop with shooting bigs, fewer paint touches, back-door cuts `[S95]`.
- Defense: rigid man. Bigs step out and recover `[S95]`.

**Michigan (Dusty May)**
- The goal is to "create space or put two on the ball" `[S96]`.
- 2024-25: two 7-footers (Goldin/Wolf).
  - Base: Goldin roll out of Wolf and Donaldson ball screens, inverted PnR, DHO entries.
  - Also Iverson Ram, Iverson step-up, Away Stagger into DHO or flare, Spain, Elevator, and pin-in screens for corner threes `[S24]`.
- 2025-26: lob threats (Mara, etc.) and rim pressure `[S97]`.

**Illinois (Brad Underwood)**
- The "spread" continuity (§1.4) `[S39]`.
- 2024-25: high-volume threes (30.3 3PA/g, 4th nationally) with poor 3P%. Turnovers flagged as a weakness `[S98]`.

---

## 5. Template-source resources (ranked by usefulness for building set templates)

Few genuinely new (2020–2026) print books on half-court set taxonomy turned up. The most useful current material is digital playbooks, diagram libraries, and newsletters. Ranked:

1. **FastModel Sports PlayBank / FastDraw library** (ongoing). It has many diagrammed MSU sets 2015–2023 (Chest, Detroit, Hawk Double Cross, Iverson Curl, DHO Clear Lob, Veer ATO…). Diagrams are frame-by-frame with numbered players, which is close to a template format. https://playbank.fastmodelsports.com `[S11][S15][S23][S26][S27][S29*]`
2. **FIBA Europe Coaching Certificate, *Basketball Terminology*** by G. Di Matteo & M. Schwarz, FIBA Europe Coaching Dept. (©2024). A free, authoritative glossary of entries, actions, PnR coverages, zones, presses, and junk defenses. https://assets.fiba.basketball/image/upload/documents-corporate-regional-offices-europe-programs-fiba-europe-coaching-certificate-fiba-europe-basketball-terminology.pdf `[S20]`
3. **Coach's Clipboard, "Michigan State Sets"** (Izzo play descriptions; partly members-only). https://coachesclipboard.net/MSUSets.html `[S12]`
4. **Tom Izzo Open Practice Series** (Championship Productions; 3 videos covering the offensive playbook, defense/rebounding, and skills). Year **[UNVERIFIED]**. https://www.mensbasketballhoopscoop.com/?p=23659 `[S6]`
5. **Wes Kosel, *Playbook – Actions and Plays Encyclopedia*** (CoachTube PDF, 142 pp; year not stated). A systematic action naming scheme. https://coachtube.com/course/basketball/playbook-actions-and-plays-encyclopedia/18001880 `[S99]`. Also Kosel, *13 Offensive Plays from Michigan State* `[S81]`.
6. **Synergy play-type definitions**, as summarized by Nylon Calculus (2017). This is the outcome-label layer. https://fansided.com/2017/09/08/nylon-calculus-understanding-synergy-play-type-data/ `[S40]`
7. **Pere Purrà, "Early Offense" series (Substack, Jan 2025)** plus *Xs&Os VideoPlaybook Mega Bundle* (transition, PnR, off-ball). https://pere.substack.com/p/1-early-offense `[S43]`
8. **Coach Hoops Substack** (Spain, Floppy, Elevator, ball-screen coverages; partly paywalled). https://coachhoops.substack.com `[S19][S48][S49][S68b]`
9. **Hoop Vision (Jordan Sperber)**: ball-screen coverage spectrum (2024), empty-screen dictionary, Purdue sets. https://hoopvision.substack.com `[S70][S55][S93]`
10. **CelticsBlog, "A glossary of Xs and Os terms" (Dec 2023)**. https://www.celticsblog.com/2023/12/31/23995553/a-glossary-of-xs-and-os-terms-boston-celtics-joe-mazzulla `[S21]`
11. **Giorgio Gandolfi (ed.), *NBA Coaches Playbook: Techniques, Tactics, and Teaching Points*** (Human Kinetics/NBCA, 2009). Older, but a classic set reference. https://lib.ecu.edu/catalog-preview/catalog/1431281 `[S100]`
12. **WBCA, *Offensive Plays & Strategies*** (Human Kinetics, 2011; 119 plays incl. fast break, zone, OOB, press). https://us.humankinetics.com/products/wbca-offensive-plays-strategies `[S101]`
13. **Research precedents for recognition:**
    - McQueen, Wiens & Guttag, "Automatically Recognizing On-Ball Screens" (MIT Sloan, 2014) `[S60]`.
    - McIntyre, Brooks, Guttag & Wiens, "Recognizing and Analyzing Ball Screen Defense in the NBA" (Sloan/KDD, 2016) `[S61]`.
    - Tian, De Silva, Caine & Swanson, "Use of ML to Automate the Identification of Basketball Strategies Using Whole Team Player Tracking Data", *Applied Sciences* 10(1):24 (2019/2020) `[S62]`.

Not recommended as primary sources: the 2024 "new coaching books" lists I found were mostly biographies, blank playbook journals, or AI-generated titles `[S102]`.

---

## 6. Event and stat definitions

| Event | Definition (paraphrased) | Source(s) | Tracking signature [HEURISTIC] |
|---|---|---|---|
| **Assist** | The last pass that leads directly to a score; at most one per score. FIBA also credits it on free throws after a shooting foul, and requires the scorer to act immediately after the catch | `[S103]` | PASS(a→b), then b shoots and makes within about 2 s / ≤2 dribbles |
| **Secondary (hockey) assist** | The pass to the player who records the assist (NBA; tracked from the 2013-14/2014-15 player-tracking era; no timing window stated). BBall Index's version requires the assister to pass within 0.5 s of receiving | `[S104][S105]` | PASS(x→a) followed by a's assist, with a's hold time ≤ about 1 s |
| **Potential assist** | A pass to a teammate who shoots within one dribble of receiving, make or miss | `[S105][S106]` | PASS(a→b), then a FGA by b with ≤1 dribble |
| **Free-throw assist** | A pass to a teammate who is fouled (shooting) within ≤2 dribbles | `[S105]` | — |
| **Screen assist** | A screen that directly leads to a teammate's made FG. Hudl/Instat has excluded FT-only outcomes since July 2024 | `[S106][S58]` | SCREEN(s→u), then u's FGM within about 2 s with no intervening action |
| **Deflection** | A defender gets a hand on the ball, disrupting a pass or dribble, whether or not it becomes a steal | `[S106][S107]` | Ball trajectory discontinuity near a defender's hand, without a change of possession or with one |
| **Charge drawn** | A defender legally establishes position and draws an offensive (player-control) foul. Recorded as an offensive foul plus a turnover, with no steal credited (FIBA) | `[S106][S103]` | Defender stationary with feet set before contact. Requires officiating play-by-play |
| **Loose ball recovered** | Gaining possession of a 50/50 ball neither team controls. NBA splits it into offensive and defensive recoveries | `[S107][S108]` | Ball not in control for ≥0.5 s, then the first player to establish control |
| **Rebound / rebound chance** | Possession after a missed FGA or last FTA. Team rebounds cover OOB before control, etc. NBA tracking counts a "chance" when a player is within 3.5 ft of the rebound | `[S103][S53]` | — |
| **Contested rebound** | A rebound where at least one player from each team is near the ball when it is touched | `[S109]` | Both teams have a player within about 3.5 ft at first touch |
| **Tip-out** | A controlled tip to a teammate or to an easily-retrievable spot counts as an offensive rebound for the tipper (FIBA). A tip out of bounds gives possession to the team that tipped it. No widely published standalone "tip-out" stat was found **[UNVERIFIED as a named official stat]** | `[S103]` | Ball touched above head height by a player without possession, then a teammate secures it within about 1.5 s |
| **Box-out** | The NBA tracks offensive and defensive box-outs as hustle stats. No official text definition was found **[UNVERIFIED wording]**. Working definition: a player establishes body contact or position between an opponent and the basket during a rebound chance [CONVENTION]. Izzo teaches "hit-find-fetch" instead of a classic box-out | `[S108][S110][S1]` | During a shot's flight, a defender is between their matched opponent and the rim within about 3 ft, with the opponent's rim-ward velocity stopped |
| **Personal foul** | Illegal contact caused by an opponent's conduct | `[S111]` | Requires play-by-play |
| **Shooting foul** | A foul on a player in the act of shooting. A foul that produces FTs only because of team-foul bonus is *non-shooting* | `[S103]` | — |
| **Non-shooting (common) foul** | A personal foul not in the act of shooting. NCAA men: one-and-one on the 7th team foul, double bonus on the 10th; team fouls reset at half | `[S103][S112]` | — |
| **Offensive foul** | A personal foul by the team in possession. Recorded as a turnover plus a personal foul (charge, illegal screen, push-off) | `[S111][S103]` | — |
| **Loose-ball foul** | A personal foul when neither team has possession | `[S111]` | — |
| **Technical** | A non-contact or conduct foul on a player, coach, or bench. NCAA men use Class A/B and contact dead-ball technicals | `[S111][S112]` | — |
| **Flagrant (NCAA men)** | F1 = excessive or severe contact during a live ball (absorbs the former "intentional" breakaway foul): 2 FT plus the ball. F2 = extreme or unsportsmanlike contact or fighting: ejection, 2 FT plus the ball. NBA F1 = unnecessary, F2 = unnecessary and excessive. FIBA equivalents: unsportsmanlike and disqualifying | `[S113][S112]` | — |
| **Intentional foul** | NBA: a purposeful foul (e.g., late-game), not necessarily flagrant. NCAA men folded "intentional" into Flagrant 1 when "flagrant" terminology was adopted (2011-12) | `[S113]` | Late-game, trailing team, contact immediately after an inbound or catch |

---

## Sources (URLs opened during this research)

- **S1**: Grantland, "How Tom Izzo Turned Michigan State Into a Rebounding Factory". https://grantland.com/the-triangle/war-tom-izzo-michigan-state-spartans-rebounding/
- **S2**: Fox Sports (M. Cohen, Mar 2026), offensive rebounding series. https://www.foxsports.com/stories/college-basketball/ncaa-offensive-rebounding-michigan-state-duke-purdue
- **S3**: The State News (Feb 17, 2015), transition game. https://statenews.com/article/2015/02/transitiongamestrongformsu
- **S6**: Tom Izzo Open Practice Series (Hoopscoop listing). https://www.mensbasketballhoopscoop.com/?p=23659
- **S7**: FastModel "Horns RIP" / Horns Flare results (search listing). https://playbank.fastmodelsports.com/library/basketball/fastdraw/336626/play-Horns-RIP (title only, via search)
- **S8**: The State News (Nov 2021), MSU fast break revamped. https://statenews.com/article/2021/11/msu-basketball-2021-fast-break-revamped
- **S9**: UM Hoops (Feb 20, 2025), "Familiar formula: Michigan preps for classic Michigan State test". https://umhoops.com/2025/02/20/familiar-formula-michigan-preps-for-classic-michigan-state-test/ (also https://umhoops.com/?p=156325)
- **S10**: FastModel "MSU Transition". https://playbank.fastmodelsports.com/library/basketball/fastdraw/363514/play-MSU-Transition
- **S11**: FastModel browse page listing MSU 2015 sets (Chest, Chest Down, Secondary Break, Rip to Mid Screen Iso, Detroit, Over Under, Iverson to Double Screen). https://playbank.fastmodelsports.com/library/basketball/search/-browse_all-?page=555
- **S12**: Coach's Clipboard, "Michigan State Sets". https://coachesclipboard.net/MSUSets.html. Also "Rip to Mid Screen Iso": https://playbank.fastmodelsports.com/library/basketball/fastdraw/68103/play-Michigan-State-Rip-to-Mid-Screen-Iso
- **S12b**: FastModel "Michigan State Over Under Play". https://playbank.fastmodelsports.com/library/basketball/fastdraw/68106/play-Michigan-State-Over-Under-Play
- **S13**: Spartan Avenue (Jul 29, 2025), fast-break duo. https://spartanavenue.com/michigan-state-basketball-may-have-most-explosive-fast-break-duo-in-tom-izzo-era-01k1bmkp0r53
- **S14**: Inside the Hall (Jan 12, 2026), IU at MSU preview. https://www.insidethehall.com/2026/01/12/what-to-expect-iu-basketball-travels-to-michigan-state/
- **S15**: FastModel "Michigan State Spartans - 4-High Iverson Curl" (2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/451012/play-Michigan-State-Spartans--4-High-Iverson-Curl
- **S16**: Active.com, "How Tom Izzo Beats the Best Zone Defenses" and "Tom Izzo's Unorthodox Attack on Zone Defenses". https://www.active.com/basketball/articles/how-tom-izzo-beats-the-best-zone-defenses ; https://www.active.com/basketball/articles/tom-izzo-s-unorthodox-attack-on-zone-defenses ; https://www.active.com/basketball/articles/beating-defenses-with-the-1-3-1-special
- **S17**: Hoopscoop, "Michigan State Spartans High Ball Screen Set Plays" (Jul 2015). https://www.mensbasketballhoopscoop.com/michigan-state-spartans-high-ball-screen-set-plays/
- **S18**: FastModel "Michigan State Detroit Play". https://fastmodelsports.com/library/basketball/fastdraw/68107/play-Michigan-State-Detroit-Play
- **S19**: Coach Hoops, "Spain Action". https://coachhoops.substack.com/p/spain-action
- **S20**: FIBA Europe, *Basketball Terminology* (Di Matteo & Schwarz, 2024). https://assets.fiba.basketball/image/upload/documents-corporate-regional-offices-europe-programs-fiba-europe-coaching-certificate-fiba-europe-basketball-terminology.pdf
- **S21**: CelticsBlog, "A glossary of Xs and Os terms" (Dec 31, 2023). https://www.celticsblog.com/2023/12/31/23995553/a-glossary-of-xs-and-os-terms-boston-celtics-joe-mazzulla
- **S22**: Backdoor Podcast, English terms explained, part 2. https://www.backdoorpodcast.com/en/basket-i-termini-inglesi-spiegati-bene-in-italiano-parte-2
- **S23**: FastModel "Michigan State Spartans - Down Screen DHO Veer ATO" (2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/437681/play-Michigan-State-Spartans--Down-Screen-DHO-Veer-ATO
- **S24**: MGoBlog, "Eating Up The Space" (Mar 18, 2025). https://www.mgoblog.com/content/eating-space
- **S24b**: MGoBlog, "State Report" (Feb 2025). https://mgoblog.com/content/state-report
- **S25**: Hoop Vision, "Cassius Winston & Top-Lock Defense" (Apr 10, 2020). https://hoopvision.substack.com/p/cassius-winston-and-top-lock-defense
- **S26**: FastModel "Michigan State 'Chest'" and "'Chest Down'". https://weblibrary-prod.fastmodelsports.com/library/basketball/fastdraw/68108/play-Michigan-State-Chest- ; https://playbank.fastmodelsports.com/library/basketball/fastdraw/68152/play-Michigan-State-Chest-Down-
- **S27**: FastModel "Michigan State Iverson to Double Screen". https://playbank.fastmodelsports.com/library/basketball/fastdraw/68104/play-Michigan-State-Iverson-to-Double-Screen
- **S28**: Hoopscoop, "Tom Izzo Michigan State DHO Horns Chin Play" (Dec 2016). https://www.mensbasketballhoopscoop.com/tom-izzo-michigan-state-dho-horns-chin-play/
- **S29**: FastModel search listings showing MSU titles (STS ATO BLOB, Pin Down Circle, etc.). https://playbank.fastmodelsports.com/library/basketball/search/down%20screen?page=60
- **S29b**: FastModel "Hawk Double Cross" (2017). https://playbank.fastmodelsports.com/library/basketball/fastdraw/177053/play-Hawk-Double-Cross
- **S29c**: Coaching Toolbox, Izzo ATO ("MSU Zipper"). https://coachingtoolbox.net/plays/basketball-plays-izzo-ato.html
- **S29d**: FastModel "Michigan State Spartans - DHO Clear Lob" (2019). https://playbank.fastmodelsports.com/library/basketball/fastdraw/289740/play-Michigan-State-Spartans--DHO-Clear-Lob
- **S29e**: FastModel "Tom Izzo SLOB '1'" (2015). https://fastmodelsports.com/library/basketball/fastdraw/72258/play-Tom-Izzo-SLOB-1-
- **S29f**: FastModel search result "Michigan State Spartans - EOQ Horns Set" (title only, via search)
- **S29g**: FastModel "Michigan State Spartans - Horns Quick Screen" (2018). https://playbank.fastmodelsports.com/library/basketball/fastdraw/244279/play-Michigan-State-Spartans--Horns-Quick-Screen
- **S29h**: FastModel "Michigan State Spartans - Iverson Stagger Hit" (2018). https://playbank.fastmodelsports.com/library/basketball/fastdraw/245378/play-Michigan-State-Spartans--Iverson-Stagger-Hit
- **S30**: Basketball for Coaches, "Swing Offense". https://www.basketballforcoaches.com/?p=7746
- **S31**: Basketball for Coaches, "Motion Offense Basketball: The 5 Types". https://www.basketballforcoaches.com/motion-offense-basketball/
- **S32**: Coach's Clipboard, "Notes on the Read and React Offense". https://www.coachesclipboard.net/ReadandReactOffenseNotes.html
- **S33**: Wikipedia, "Flex offense". https://en.wikipedia.org/wiki/Flex_offense
- **S34**: Coach's Clipboard, "Shuffle Offense". https://coachesclipboard.net/ShuffleOffense.html
- **S35**: Wikipedia, "Shuffle offense". https://en.wikipedia.org/wiki/Shuffle_offense
- **S36**: Rivals Wisconsin, "Film Room: What changed offensively from Bo Ryan to Greg Gard?" https://wisconsin.rivals.com/news/film-room-what-exactly-has-changed-from-bo-ryan-to-greg-gard
- **S37**: Wikipedia, "Blocker-Mover offense". https://en.wikipedia.org/wiki/Blocker-Mover_offense
- **S38**: Wikipedia, "Triangle offense". https://en.wikipedia.org/wiki/Triangle_offense
- **S39**: Hooper University, "Brad Underwood's Spread Offense". https://www.hooperuniversity.com/breakdowns/brad-underwoods-spread-offense ; UM Hoops (2019) https://umhoops.com/2019/12/10/film-room-the-basics-of-brad-underwoods-spread-offense/
- **S40**: Nylon Calculus, "How to understand Synergy play type categories" (2017). https://fansided.com/2017/09/08/nylon-calculus-understanding-synergy-play-type-data/
- **S41**: HoopDirt, "Drag Series For Secondary Break". https://hoopdirt.com/drag-series-for-secondary-break/
- **S43**: Pere Purrà, "1) Early Offense" (Jan 15, 2025). https://pere.substack.com/p/1-early-offense
- **S44**: HoopDirt, "Basketball 'Actions' From Around The World: Olympics". https://hoopdirt.com/?p=1058147
- **S45**: FastModel Horns search results (Horns Flare/Double/RIP). https://playbank.fastmodelsports.com/library/basketball/fastdraw/184835/play-Ball-Screen-Sets--Horns-Flare (via search)
- **S46**: Breakthrough Basketball, "The Princeton Offense". https://www.breakthroughbasketball.com/offense/princeton-offense
- **S47**: Hooper University, "Princeton Offense—Chin Series". https://www.hooperuniversity.com/breakdowns/princeton-offense-chin-series
- **S48**: Coach Hoops, "Floppy Action". https://coachhoops.substack.com/p/floppy-action
- **S49**: Coach Hoops, "Elevator Action". https://coachhoops.substack.com/p/elevator-action
- **S50**: Diggin Basketball, "Mavs Playbook: Delay Chicago". https://digginbasketball.substack.com/p/mavs-playbook-delay-chicago
- **S51**: Breakthrough Basketball, Spurs "Hammer" set. https://www.breakthroughbasketball.com/plays/spurshammer (NBC explainer page also opened: https://nbcsports.com/nba/news/hammer-action-basketball-san-antonio-spurs-nba-glossary-carbaugh-video)
- **S52**: Half Court Hoops, "NBA 5-Out Offense: Delay" (Oct 2021). https://halfcourthoops.substack.com/p/nba-5-out-offense-delay
- **S53**: Wikipedia, "Player tracking (NBA)". https://en.wikipedia.org/wiki/Player_tracking_(NBA)
- **S54**: A Quick Timeout (T. Miller, Apr 2024), "Inside Euro Ball Screen Offense". https://aquicktimeout.substack.com/p/inside-euro-ball-screen-offense
- **S55**: Hoop Vision, "Hoops Dictionary: Empty Ball Screens" (2021). https://hoopvision.substack.com/p/hoops-dictionary-empty-ball-screens
- **S56**: HoopStudent, "Basketball step up screen". https://hoopstudent.com/basketball-step-up-screen/
- **S57**: Hammer & Rails, "Purdue Basketball Film Room: The Return of the Dunk". https://www.hammerandrails.com/2025/6/25/24455836/purdue-basketball-film-room-the-return-of-the-dunk
- **S58**: Hudl/Instat glossary, "Screen Assists". https://instatglossary.hudl.com/basketball/parameters/box-score/screen-assists/
- **S59**: The Hoops Geek, "How to Beat a 2-3 Zone Defense". https://www.thehoopsgeek.com/how-to-beat-2-3-zone-defense
- **S60**: MIT Sloan SSAC, "Automatically Recognizing On-Ball Screens" (McQueen, Wiens, Guttag). https://www.sloansportsconference.com/research-papers/automatically-recognizing-on-ball-screens
- **S61**: MIT Sloan SSAC, "Recognizing and Analyzing Ball Screen Defense in the NBA" (McIntyre, Brooks, Guttag, Wiens). https://www.sloansportsconference.com/research-papers/recognizing-and-analyzing-ball-screen-defense-in-the-nba
- **S62**: Loughborough repository, Tian et al., *Applied Sciences* (2019). https://repository.lboro.ac.uk/articles/journal_contribution/Use_of_Machine_Learning_to_Automate_the_Identification_of_Basketball_Strategies_Using_Whole_Team_Player_Tracking_Data/11828286
- **S63**: Slappin' Glass, "Innovative Defenses: Finnish Playbook" (offensive counters vs hybrid/match-up). https://slappinglass.substack.com/p/innovative-defenses-finnish-playbook
- **S64**: Breakthrough Basketball, "Basketball Offense Versus Junk Defenses". https://www.breakthroughbasketball.com/offense/offense-junk-defense
- **S65**: Basketball for Coaches, "Pack Line Defense – The Complete Guide". https://www.basketballforcoaches.com/?p=1621
- **S66**: Coaching Toolbox, Tom Izzo defensive stance. https://coachingtoolbox.net/?p=38218
- **S67**: HoopStudent, "Ball screen defense basketball". https://hoopstudent.com/ball-screen-defense-basketball
- **S68**: Breakthrough Basketball (Logalbo), "Ball Screen Defense - Ice, Drop, and Switch". https://www.breakthroughbasketball.com/defense/3-ball-screen-logalbo
- **S68b**: Coach Hoops, "Ball Screen Coverages" (partially paywalled). https://coachhoops.substack.com/p/ball-screen-coverages
- **S69**: UM Hoops (Mar 5, 2019), video breakdown vs MSU. https://umhoops.com/2019/03/05/video-breakdown-two-areas-michigan-will-need-improve-win-rematch-michigan-state/ (also https://umhoops.com/?p=102796)
- **S70**: Hoop Vision, "The Ball Screen Coverage Spectrum" (Jan 2024). https://hoopvision.substack.com/p/the-ball-screen-coverage-spectrum
- **S71**: Coach's Clipboard, "Basketball Switching Defense". https://www.coachesclipboard.net/basketball-switching-defense.html
- **S72**: Coaches Insider, "Post Defense: Defending the Lob with Dwayne Stephens" (Aug 2025). https://coachesinsider.com/mens-basketball/post-defense-defending-the-lob-with-dwayne-stephens-western-michigan-university
- **S73**: Breakthrough Basketball, "3 Steps To Mastering The Matchup Zone Defense". https://www.breakthroughbasketball.com/coaching/matchup-zone-installation
- **S74**: NBC Sports CBT, "Michigan State playing zone? It's possible". https://collegebasketball.nbcsports.com/2015/10/03/michigan-state-playing-zone-its-possible/
- **S75**: Cracked Sidewalks, "Purdue Preview 2025-26". https://www.crackedsidewalks.com/2025/10/purdue-preview-2025-26.html
- **S76**: Basketball for Coaches, "1-2-1-1 Press (Diamond)". https://www.basketballforcoaches.com/1-2-1-1-diamond-press/
- **S77**: Basketball for Coaches, "Run and Jump Defense". https://www.basketballforcoaches.com/run-and-jump-defense/
- **S78**: Coach's Clipboard, "Match-up Press". https://www.coachesclipboard.net/MatchupPress.html
- **S79**: Slappin' Glass, "Innovative Defenses: Finnish Playbook". https://slappinglass.substack.com/p/innovative-defenses-finnish-playbook
- **S80**: SI (J. Cotsonika, Jan 15, 2026), "3 Stats Identify MSU's Defensive Dominance". https://www.si.com/college/michiganstate/spartans-3-stats-identify-defensive-dominance-big-ten
- **S81**: CoachTube, "13 Offensive Plays from Michigan State" (W. Kosel). https://coachtube.com/course/basketball/13-offensive-plays-from-michigan-state-man-zone-blob-slob/18014595
- **S82**: Wikipedia, 2024–25 Michigan State Spartans men's basketball team. https://en.wikipedia.org/wiki/2024%E2%80%9325_Michigan_State_Spartans_men%27s_basketball_team
- **S83**: Inside the Hall (Feb 11, 2025), IU at MSU preview. https://www.insidethehall.com/2025/02/11/what-to-expect-indiana-at-michigan-state-2/
- **S84**: SI (T. Marshall, Feb 28, 2025), "Spartans' Defense Continues to Thrive". https://www.si.com/college/michiganstate/basketball/spartans-tre-holloman-jaxon-kohler-carson-cooper-maryland-terrapins-01jn47c8fpkz
- **S85**: Wikipedia, 2025–26 Michigan State Spartans men's basketball team. https://en.wikipedia.org/wiki/2025%E2%80%9326_Michigan_State_Spartans_men%27s_basketball_team
- **S86**: Spartan Avenue (C. Muldowney, Mar 31, 2026), final report card 2025-26. https://spartanavenue.com/final-report-card-for-michigan-state-basketball-s-2025-26-season-01kn0m686mvb
- **S87**: Inside the Hall (Feb 27, 2026), IU hosts MSU preview. https://www.insidethehall.com/2026/02/27/what-to-expect-iu-basketball-hosts-michigan-state-on-sunday-afternoon/
- **S87b**: Inside the Hall (Jun 23, 2026), 2026-27 offseason at a glance: MSU. https://www.insidethehall.com/2026/06/23/2026-27-big-ten-offseason-at-a-glance-michigan-state-spartans/
- **S88**: Babcock Hoops, Jeremy Fears Jr. scouting report. https://www.babcockhoops.com/post/2026-nba-draft-jeremy-fears-jr-scouting-report
- **S89**: SI (J. Cotsonika, Dec 18, 2025), Kohler's 3-point shooting. https://www.si.com/college/michiganstate/why-msu-jaxon-kohler-improved-3-point-shooting-important-
- **S90**: SI (C. Landis, Oct 5, 2025), "MSU Will Play to Its Strengths in 2025-26". https://www.si.com/college/michiganstate/spartans-mens-basketball-tom-izzo-jaxon-kohler-trey-fort-coen-carr-2025-26-schedule
- **S91**: SI (C. Landis, Oct 4, 2025), "One Thing MSU Must Do to Keep Offense Efficient". https://www.si.com/college/michiganstate/spartans-basketball-carson-cooper-jeremy-fears-coen-carr-tom-izzo-offense
- **S92**: Spartan Avenue (Mar 28, 2026), Sweet 16 loss to UConn. https://spartanavenue.com/michigan-state-s-season-abruptly-ended-in-sweet-16-by-uconn-thanks-to-usual-mistakes-01kms91qv6d3
- **S93**: Hoop Vision, "The Starting Five: Purdue's ball screen…" (Nov 2023). https://hoopvision.substack.com/p/the-starting-five-purdues-ball-screen
- **S94**: Hoops HQ (S. Davis, Jan 21, 2025), "Wisconsin Badgers Extreme Makeover". https://www.hoopshq.com/big-ten/wisconsin-badgers-extreme-makeover
- **S95**: Cracked Sidewalks, "UW-Madison Preview 2025-26". https://www.crackedsidewalks.com/2025/10/uw-madison-preview-2025-26.html
- **S96**: UM Hoops (Oct 7, 2024), "Dusty 101: Offensive philosophy". https://umhoops.com/2024/10/07/dusty-101-offensive-philosophy/
- **S97**: UM Hoops (Sep 30, 2025), preseason, 2025-26. https://umhoops.com/?p=160861
- **S98**: The Champaign Room (Mar 2025), "Air raid offense". https://www.thechampaignroom.com/2025/3/8/24380584/college-basketball-air-raid-offense-brad-underwood-illinois-fighting-illini-big-ten-ncaa-purdue ; also https://www.thechampaignroom.com/2025/2/14/24365148/analyzing-underwoods-offense-for-illinois-isnt-as-simple-as-youve-been-told-big-ten-ncaa-jakucionis
- **S99**: CoachTube, "Playbook – Actions and Plays Encyclopedia" (W. Kosel). https://coachtube.com/course/basketball/playbook-actions-and-plays-encyclopedia/18001880
- **S100**: ECU Library catalog, *NBA Coaches Playbook* (Gandolfi, 2009). https://lib.ecu.edu/catalog-preview/catalog/1431281
- **S101**: Human Kinetics, *WBCA Offensive Plays & Strategies* (2011). https://us.humankinetics.com/products/wbca-offensive-plays-strategies
- **S102**: BookAuthority, "New Basketball Coaching Books". https://bookauthority.org/books/new-basketball-coaching-ebooks
- **S103**: FIBA Statisticians' Manual 2024. https://assets.fiba.basketball/image/upload/documents-corporate-fiba-statisticians-manual-2024.pdf
- **S104**: NBA.com, "Stephen Curry, Warriors lead the NBA in secondary assists". https://www.nba.com/news/stephen-curry-warriors-lead-the-nba-in-secondary-assists
- **S105**: BBall Index, "A Guide To Passing Stats". https://www.bball-index.com/a-guide-to-passing-stats/
- **S106**: databallr Stats Glossary. https://databallr.com/stats/glossary
- **S107**: NBA.com, "Alex Caruso 2023-24 NBA Hustle Award". https://www.nba.com/news/alex-caruso-2023-24-nba-hustle-award ; ABC7 (2015) hustle pilot: https://abc7news.com/post/nba-to-use-pilot-stat-program-to-track-hustle-at-las-vegas-summer-league/837061/ ; Hoop Coach hustle follow-up: https://www.hoopcoach.org/?p=30252
- **S108**: nba Ruby gem docs, BoxScoreHustleTeamStat field list (off/def box outs, off/def loose balls). https://rubydoc.info/gems/nba/NBA/BoxScoreHustleTeamStat
- **S109**: Cleaning the Glass docs, "Contested Rebounds". https://docs.cleaningtheglass.com/pro/data-sets/contested-rebounds
- **S110**: NBA.com, "2021-22 NBA Hustle Award". https://www.nba.com/news/2021-22-nba-hustle-award
- **S111**: Wikipedia, "Foul (basketball)". https://en.wikipedia.org/wiki/Foul_(basketball)
- **S112**: 2025-26 MBB/WBB/NFHS major rules differences (PDF). https://a-us.storyblok.com/f/1022696/x/aa2311ef81/2025-26-mbb_wbb_nfhs_major_rules_differences-final.pdf
- **S113**: Wikipedia, "Flagrant foul". https://en.wikipedia.org/wiki/Flagrant_foul

Other pages opened that informed context but are not cited above: Coach's Clipboard "MSU Progressive Transition Drill" (https://www.coachesclipboard.net/MSUTransitionDrill.html), Coach's Clipboard Newsletter Jan 2016, Bruin Sports Analytics "NBA Hustle" (https://www.bruinsportsanalytics.com/post/nba-hustle), Glory League stat tags, CBS Sports Izzo season-opener (Oct 30, 2025), Daily Bruin 2026 Big Ten preview: MSU (https://dailybruin.com/2026/07/12/2026-big-ten-preview-michigan-state/), Human Kinetics *Basketball: Steps to Success* 3rd ed. (Wissel, 2012), Gumroad Xs&Os VideoPlaybook and Horns Offense Unlocked, CoachTube "Playbook Vocabulary".
