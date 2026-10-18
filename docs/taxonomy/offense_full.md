# NCAA D-I Men's Basketball: Full Offensive Taxonomy for Tracking-Based Play Recognition
### Michigan State focus. Extends `/home/claude/set_taxonomy.md` §1 and §3; it does not repeat them.

Compiled 2026-10-17. All text is paraphrased. Source keys `[O#]` resolve in the **Sources** list at the end; every O-key is a page opened for this file. Keys `[S#]` point to sources already listed in `set_taxonomy.md` and are used only where this file extends an item that file already covers. Tags carried over from the first pass:

- **[UNVERIFIED]**: plausible, but no opened source confirms it.
- **[CONVENTION]**: common coaching usage stated from general knowledge.
- **[HEURISTIC]**: a proposed detection rule for this project. It is an engineering choice, not a sourced fact. **Every "Detection signature" cell is [HEURISTIC] unless it cites a source.**
- **[MSU]**: Michigan State usage documented in an opened source.

**What this file adds to the first pass.**
- A five-level hierarchy (Family → Sub-family → Named set/action → Variant/counter → Signature) across 17 families.
- Metric court geometry, plus a detection-primitive library that every signature reuses.
- New families: offensive rebounding, spacing geometry, press offense, a full special-situations layer, zone-offense patterns, and handoff offense as its own family.
- Program-system entries for Kansas, Purdue, Houston, Alabama, Auburn, Virginia, Villanova, Gonzaga, Creighton, Davidson, Baylor and others.
- Timing windows for each action.

---

## 0. Geometry, primitives and notation

### 0.1 Court frame (project convention)

The frame is metric, with the origin at the centre of the attacked rim projected to the floor. Polar angle θ is measured in degrees from the **right baseline**: 0° is the right baseline, 90° the top of the key, and 180° the left baseline. In Cartesian terms, x = r·cosθ (positive toward the right sideline) and y = r·sinθ (toward half-court). The baseline sits at y ≈ −1.60 m and half-court at y ≈ +12.73 m (NCAA court 28.65 m × 15.24 m; rim centre 1.575 m from the baseline). The NCAA men's three-point arc has been 6.75 m (22 ft 1.75 in) since 2019-20 `[O26]`. Lane width is 3.66 m (12 ft) [CONVENTION].

| Spot | Metres (x, y) or (r, θ) | Notes |
|---|---|---|
| Rim / restricted area | r < 1.22 | 4 ft RA arc [CONVENTION] |
| Dunker spot R/L | r 2.4–3.6, θ 5–25° / 155–175° | Baseline, just outside the lane |
| Block R/L | x ±1.9–2.3, y −0.6 to 1.2 (r ≈ 2.0–2.5, θ 10–35°) | Low post |
| Mid-post | x ±1.9–2.5, y 1.5–3.0 | — |
| Short corner R/L | r 3.5–5.5, θ 0–15° | Inside the arc, baseline |
| Elbow R/L | (±1.83, 4.19), θ ≈ 66° / 114° | Given project anchor |
| Nail / high post | (0 ± 0.9, 3.8–4.6) | — |
| Slot R/L | r 7.0–8.2, θ 58–78° / 102–122° | Above the elbow, outside the arc |
| Top | r 7.0–8.5, θ 80–100° | — |
| Wing R/L | r 6.9–8.0, θ 30–55° / 125–150°; centre 45° | FT-line extended |
| Corner R/L | r 6.6–7.3, θ ≤ 12° / ≥ 168° | Corner three |
| "Deep" / logo | r > 8.5 | Ball-screen handler start in some systems |
| SLOB 28-ft mark | x ±7.62, y ≈ 6.9 | NCAA frontcourt throw-in spot `[O27]` |
| BLOB spot | y ≈ −1.6 to −2.2 (out of bounds), x ±1.8–3.0 | End line 3 ft outside the lane `[O27]` |

Zones used below: **paint** (|x| ≤ 1.83, y ≤ 4.19); **arc band** (6.6 ≤ r ≤ 8.5); **strong side** (sign(x) = sign(x_ball)); **weak side** (the opposite sign).

### 0.2 Detection primitives (all [HEURISTIC]; metric versions of first-pass §0)

| Primitive | Rule |
|---|---|
| `SCREEN(s→u)` | Screener *s* has speed < 0.6 m/s for ≥ 0.3 s. Cutter *u* passes within 1.2 m of *s*. *u*'s defender's path deflects or is delayed within 1.5 m of *s*. **Ball screen** if *u* holds the ball. |
| `SCREEN_DIR` | Unit vector from *s* toward the defender being screened, at the moment of contact. **Down**: cutter moves toward +y (away from the baseline) and the screener faces −y. **Back/up**: cutter moves toward −y. **Flare**: the cutter's displacement points away from the ball (angle between the cutter-velocity and cutter→ball vectors > 120°). **Cross**: lateral (\|Δx\| > 2\|Δy\|) with y < 3. |
| `DHO(a→b)` | Ball transfers with the a–b distance < 1.0 m, ball flight < 1.0 m, and at least one of them moving > 1 m/s. `[O20]` used a 1.5 m (5 ft) ball-holder radius and ±2 s windows around the closest screener–cutter approach. |
| `PASS(a→b)` | Ball flight > 1.0 m that ends in b's possession. **Skip** = a pass crossing x = 0 with \|Δx\| > 8 m. **Entry** = a pass whose receiver has r < 3.5. |
| `DRIVE(p)` | Dribble that starts at r > 6.1 (20 ft) and reaches r < 3.05 (10 ft); NBA definition, metric `[S53]`. |
| `CUT(p,path)` | Displacement ≥ 3 m in ≤ 1.5 s without the ball, labelled by path class (basket, backdoor, curl, flare, shallow, UCLA, flex, Iverson, zipper, shuffle, flash, banana, dive, lift, drift). |
| `PAINT_TOUCH` | Ball inside the paint polygon for ≥ 0.2 s, by dribble or pass. |
| `ALIGN(t)` | Snapshot of all 5 offensive (r, θ) values. Assign to the nearest alignment template (§3) by Hungarian matching on role-free positions. Cost = Σ squared distance; reject if the mean error > 1.8 m. |
| `PHASE` | **Transition**: possession start until 7 of 10 players are past half-court (`[O20]` used that test) or until 8 s elapse `[O11]`. **Early**: 4–12 s. **Half-court**: the remainder. **Late clock**: shot clock ≤ 7 s. |
| `CLOCK` | The shot clock resets to 20 s after an offensive rebound that hits the rim `[O26]` and on a frontcourt inbound after a defensive foul if fewer than 20 s remain `[O27]`. Use this to segment sub-possessions. |

### 0.3 Template row format

Every named set or action row has six columns:

1. **Definition** (one line).
2. **Start**: alignment and spots.
3. **Sequence**: ordered actions with approximate t (seconds) from the set moment.
4. **Counters/variants**.
5. **Programs**, with sources.
6. **Detection signature**.

---

## OFFENSE HIERARCHY (overview)

```
OFFENSE
├── F1  Primary transition
│   ├── 1.1 Outlet & advance  ├── 1.2 Lane rules  ├── 1.3 Big-man roles (rim run / trailer)
│   ├── 1.4 Numbered / role-based breaks  ├── 1.5 Named program breaks (incl. MSU/Izzo)  └── 1.6 Advantage outcomes (2v1, 3v2, 4v3)
├── F2  Secondary / early offense
│   ├── 2.1 Drag family  ├── 2.2 Pistol/21 family  ├── 2.3 Trailer actions  ├── 2.4 Early post
│   ├── 2.5 Flow/delay entries  └── 2.6 Named secondary breaks (Carolina, 3-up, Argentina, MSU)
├── F3  Half-court alignments / entries (≈30 named starts)
├── F4  Continuity & motion systems (≈30 systems, with D-I programs)
├── F5  Ball-screen offense (location × angle × screener-action × handler-read)
├── F6  Handoff offense
├── F7  Post offense
├── F8  Off-ball screens & cut vocabulary
├── F9  Isolation & clear-outs
├── F10 Spread / drive-and-kick / paint-touch offenses
├── F11 Zone offense
├── F12 Press offense / press break
├── F13 Special situations (ATO, BLOB, SLOB, EOH/EOG, late clock, FT, jump ball, 2-for-1, delay)
├── F14 Offensive rebounding systems
├── F15 Spacing systems & geometry
├── F16 European/NBA vocabulary ↔ college terms
└── F17 Outcome layer: Synergy play types
```

---

## F1. PRIMARY TRANSITION

The first pass (§1.1) defines outlet, lane filling, primary vs secondary break, trailer and rim run, and summarizes the Izzo break `[S8][S10][S11]`. This family adds the rule sets and role-based breaks needed to label *who* is doing *what*.

### 1.1 Outlet and advance

| Action | Definition | Start | Sequence / timing | Variants | Programs | Detection signature |
|---|---|---|---|---|---|---|
| **Ball-side outlet** | First pass after the DREB, made to the side where the rebound was secured, because that is fastest `[O3]` | Rebounder at r < 4 in its own defensive half | Pass ≤ 1.5 s after the DREB to a guard at the free-throw-line extended or sideline | Middle outlet; dribble-out by the rebounder | UNC (Roy Williams) `[O3]` | The outlet receiver's position has the same x-sign as the rebound location. Pass length 6–15 m within 1.5 s of the DREB |
| **Quick inbound (after make)** | Designated big takes the ball out of the net and inbounds instantly, so the break runs after makes too `[O5][O4]` | 5 under its own defensive rim | Inbound ≤ 2 s after the make | Run-the-baseline inbound | Oregon Tech (Danny Miles) `[O5]`; MSU pushes off makes and misses `[S9]` | Time from made basket to inbound ≤ 2.0 s. The inbounder is the tallest offensive player [HEURISTIC] |
| **Headman / pass-ahead** | The guard passes ahead rather than dribbling the length of the floor `[O1][O5]` | 1 with the ball in the backcourt | First forward pass ≥ 8 m, before the 1 crosses half-court | Long pass to the rim-runner `[O6]` | Carolina `[O1]`; MSU must pass before the timeline or flow to the secondary `[O30]` | Forward pass with Δy ≥ 8 m while the passer has y > 10 m (own half or near it) |
| **Diagonal push** | The ball-handler advances on a diagonal rather than a straight line. Izzo blamed straight-line dribbling for turnovers `[O31]` | 1 at the outlet spot | Dribble path angle 20–45° off the sideline-parallel | — | **[MSU]** `[O31]` | Mean heading of the dribble path ≥ 15° off the y-axis over ≥ 10 m of travel |
| **Speed-dribble advance** | The 1 speed-dribbles while others sprint; three-up flash on arrival `[O7]` | — | Ball crosses half-court ≤ 4 s after possession | — | Coach's Clipboard "3-Up" `[O7]` | Ball speed ≥ 5 m/s sustained ≥ 2 s |

### 1.2 Lane rules

| Rule | Definition | Programs | Detection signature |
|---|---|---|---|
| **Run wide** | Wings run their lanes as wide as possible and catch on the run `[O3][O5]` | UNC `[O3]`; Oregon Tech `[O5]` | Wing \|x\| ≥ 6.0 m while y decreases from 12 → 3 m |
| **Lane before half-court** | Get into your lane before half-court, even if it means cutting straight across `[O5]` | `[O5]` | Lateral position stabilizes (\|dx/dt\| < 1 m/s) before y < 12.7 |
| **Wings to the corners** | The 2 and 3 sprint to the corners `[O2][O4]`; "2 right / 3 left" in the numbered break `[O4]` | UNC `[O2]`; MSU 2025-26 had Fort right / Carr left (pre-season) `[S13]` | Two non-ball players reach r 6.6–7.3, θ ≤ 15° or ≥ 165° within 5 s of possession |
| **Four rim-to-rim** | Four players sprint rim to rim; only the ball-handler stays out `[O5]` | `[O5]` | ≥ 4 offensive players reach y < 2 within 6 s |
| **Score fast** | With ≤ 2 defenders back, shoot in ≤ 2 passes. Otherwise go to the secondary break `[O2][O3]` | UNC `[O2][O3]` | Count defenders with y < ball_y at half-court crossing. If ≤ 2, label the possession *primary-break opportunity* |
| **Score in 4 s** | Target a shot within about 4 s after a make `[O5]` | `[O5]` | Shot ≤ 4 s after the inbound |
| **Weak-side rebounder** | Always keep a big at the weak-side rebounding spot for early shots `[O5]` | `[O5]` | On an early shot, a big has opposite sign(x) to the shooter and r < 3 |

### 1.3 Big-man transition roles

| Role | Definition | Programs | Detection signature |
|---|---|---|---|
| **Rim runner** | A big sprints rim to rim and seals or catches early `[O3][O4]`. In the numbered break, the 4 can run parallel to the 1 to the opposite slot, or run to the rim and cut to the ball-side low post `[O4]` | UNC: both bigs run rim to rim `[O3]` | A big's speed is ≥ 5.5 m/s for ≥ 2 s, and the path ends at r < 2.5 before the ball reaches y < 7 |
| **Trailer (high)** | Last big down the floor. Arrives at the top or slot, serving as the reversal outlet or drag screener `[O1][O4][O2]` | Carolina's 4 is the high trailer `[O1]`. MSU wants a shooting 4/5 trailer for a pitch-back three `[O30]` | The last offensive player across half-court is a big. It decelerates at r 6.5–8.5, θ 70–110° |
| **Post trailer / duck-in** | The second big runs to the ball-side block and ducks in `[O1]` | Carolina 5 `[O1]` | A big finishes the break at the ball-side block within 2 s of the wing catch |
| **Rebounder-inbounder (5)** | Rebounds or takes the ball out of the net, outlets, then trails `[O4]` | `[O4]` | Same player records the DREB or inbound, then is the last to cross half-court |
| **Trailer-hits-rim-runner** | The trailing big hits the other big on the run or on an early post-up `[O3]` | UNC `[O3]` | Big-to-big pass within 6 s of possession, where the receiver has r < 3 |

### 1.4 Numbered / role-based primary breaks

| Named break | Definition | Lanes by number | Sequence (t from possession) | Options (in order) | Source | Detection signature |
|---|---|---|---|---|---|---|
| **Numbered break (generic)** | Fixed roles by position number `[O4]` | 1: ball, ball-side beyond the backcourt arc. 2: right sideline to the corner. 3: left sideline to the corner or the block. 4: opposite slot or rim run. 5: rebound/inbound, then trail to the ball-side post `[O4]` | 0–1.5 s outlet. 2–5 s wings arrive in the corners. 4–6 s trailer arrives | (1) 2 jumper/three; (2) 3 corner three; (3) 3 low-post cut; (4) 4 slot three; (5) 4 rim run; (6) 4 to the far low post `[O4]` | `[O4]` | Two players in opposite corners plus one big at r < 3 within 6 s; the ball-handler is at the slot or wing |
| **Oregon Tech / "run every time"** | Push off makes and misses with four rim-to-rim runners; banana cut or wing break-back as the safety valve `[O5]` | 4 sprint; PG advances | Score ≤ 4 s | Set plays off the break flowing into motion `[O5]` | `[O5]` | ≥ 4 players at y < 2 within 6 s on ≥ 50% of DREB possessions |
| **Izzo / MSU break** | "Go hard, go fast, under control"; diagonal dribble; wings as dedicated lane runners `[O31]`; pass before the timeline, or secondary `[O30]` | Wings wide; shooting 4/5 trails for a pitch-back three `[O30]` | Pass before the ball reaches y ≈ 12.7; pitch-back to the trailer at the top | Fallback: MSU secondary (DHO plus weak-side down screen) `[S11]` | **[MSU]** `[O30][O31][S11]` | 1-to-trailer pitch-back at r 6.7–8.5, θ 70–110° within 7 s. Or a forward pass made before the passer crosses half-court |

### 1.5 Advantage-situation outcomes (labels for primary-break possessions)

| Label | Definition | Teaching rule | Detection signature |
|---|---|---|---|
| **2v1** | Two attackers vs one defender | Attack the rim first with an in-and-out dribble, then pass `[O32]` | ≤ 1 defender below the ball, 2 attackers within 6 m of the ball |
| **3v2** | Three vs two | The top handler stays above the FT line and passes to either side `[O32]` | Ball-handler y > 4.2 while two teammates are at \|x\| > 3 |
| **4v3 / 5v4** | Outnumbered break | Run the lanes and sidelines, keep spacing, drive and dish or kick `[O32]` | Defender count below the ball is one less than attackers |
| **Banana cut** | A wing curves out wide then in to the rim to receive a lead pass `[O5]` | `[O5]` | Wing path curvature > 0.15 m⁻¹ with the final heading toward the rim |

---

## F2. SECONDARY / EARLY OFFENSE

The first pass covers drag, double drag, pistol, flow and the MSU secondary (DHO plus down screen) `[S41][S43][S44][S11]`. Below are the full sub-families, with variants and named program breaks.

### 2.1 Drag family

| Action | Definition | Start | Sequence | Counters | Programs | Detection signature |
|---|---|---|---|---|---|---|
| **Drag (single)** | On-ball screen set on the move by the trailer, usually on the empty side `[O11][O25]` | Handler at the slot or wing; trailer approaching from y > 9 | t = 0 handler at the slot. t ≈ 0.5–1 s screen. Roll, pop or short roll | Tag&Go (tap then roll), Pop, Gator (reject the screen and pass to a nearby player) `[O11]` | UNC uses drag screens to start actions early `[O2]` | SCREEN with the ball within 8 s of possession. The screener's prior velocity has −y ≥ 3 m/s |
| **Double drag ("77")** | Two consecutive drag screens at the arc `[O11]` | Both bigs trail | Screen 1, then screen 2 within ≤ 1.5 s | Drag Flare `[S41]`; one rolls, one pops | — | Two ball screens on the same handler ≤ 1.5 s apart, both at r > 6.5 |
| **Drag slip** | Drag screener slips before contact `[S41]` | — | — | — | — | Screener stationary < 0.3 s, then dives at ≥ 4 m/s |
| **Drag veer** | Central PnR in transition followed by an off-ball screen by the same screener `[O11]` | — | — | — | — | Same-screener ball screen, then an off-ball screen ≤ 2 s apart, ≤ 10 s into the possession |
| **Inverted drag** | A wing screens for an inside handler (inverted PnR) in transition `[O11]` | — | — | — | Michigan 2024-25 inverted PnR `[S24]` | The handler is the tallest player and the screener is a guard |
| **Guard-guard drag** | PnR between two perimeter players `[O11]` | — | — | Switch hunting | — | Screener is a guard; both participants are at r > 6.5 |

### 2.2 Pistol / "21" family (extends first-pass §1.2)

| Variant | Definition | Start | Sequence | Counters | Programs | Detection signature |
|---|---|---|---|---|---|---|
| **Pistol (dribble entry)** | The 1 dribbles at the 2, who screens for the 1. The 5 flares the 2 and the 4 screens for the 3 `[O8]` | 1 brings the ball up one sideline; 2 on the wing; 5 at the top; 3 and 4 on the weak side `[O8]` | 1 dribbles at the 2 ≤ 6 s, guard-guard screen, flare for 2 | Skip to the 2 off the flare if X2 jumps out `[O8]` | NBA teams 2010–16 `[O9]`; all levels `[O8]` | Handler, a wing and a big form a triangle on one side (the big at the top, r ~7, \|θ − 90\| < 20) with no one in the paint `[O9]`. Guard-guard SCREEN ≤ 10 s into the possession |
| **Pistol (pass + chase / "Chase")** | 1 passes to the 2 and chases for a DHO. The 5 flares or sets an empty-wing ball screen `[O8][O10]` | The 2 buttonhooks from the corner to the wing `[O10]` | Pass, DHO at the wing, attack downhill. Else the 5 flares the 2, then sets a ball screen for the 1. Else reversal and weak-side pin-down `[O10]` | Back-door if the 2 is denied | `[O10]` | 2's path runs corner → wing (r 7, θ 30–50) as the 1 arrives. DHO 1↔2 at the wing within 2 s |
| **Keep** | The 2 fakes the handoff, keeps the ball and attacks; the 5 comes up for a ball screen `[O10][O9]` | — | — | — | `[O9][O10]` | DHO approach (a–b distance < 1.5 m) with no ball transfer, then a DRIVE by the holder ≤ 1 s later |
| **Dribble (step-up)** | The 2 sets a step-up ball screen for the 1, who attacks baseline `[O10]` | — | — | 5 flares the 2 | `[O10]` | Guard SCREEN with the screener's back to the near baseline; handler's heading toward the baseline |
| **Down (Pistol)** | 1 centers the ball to the 5; the 2 back-screens for the 1's rim cut; then a 5↔2 DHO, and the 1 exits to the corner `[O10]` | — | — | — | `[O10]` | Pass 1 → big at the top, then a guard back-screen with the 1 cutting toward r < 2, then a big DHO |
| **Pistol exits / zipper** | Secondary actions: STS, wide pin, zipper, slip, backdoor, shuffle cut `[O9]` | — | — | — | `[O9]` | — |

### 2.3 Trailer actions

| Action | Definition | Programs | Detection signature |
|---|---|---|---|
| **Trailer three (pitch-back)** | Hit-back pass to the trailing big above the arc for a three | MSU `[O30]` | The trailer catches at r > 6.75, θ 60–120 ≤ 8 s into the possession and shoots ≤ 1.5 s after the catch |
| **Trailer reversal / high-low** | The trailer receives the reversal and feeds the ducking-in post `[O1]` | Carolina `[O1]` | Pass to the trailer at the top, then a pass to the post (r < 2.5) ≤ 2 s later |
| **Trailer drag** | See 2.1 | `[O2]` | — |
| **Trailer delay** | Transition pass to the arriving centre big at the top to play 5-out `[O11]` | `[O11]` | The big receives at the top with all others at r > 6.5 |
| **Rear screen (back screen in secondary)** | On the reversal, the 2 sets a rear (back) screen for the trailer, then pops; else the 4 cross-screens the 5 for high-low `[O2][O1]` | UNC `[O2][O1]` | After the reversal pass, a guard sets a back screen for the top big who cuts toward the rim; lob window ≤ 1.5 s |

### 2.4 Early post

| Action | Definition | Programs | Detection signature |
|---|---|---|---|
| **Early post seal** | The rim-running big seals on the block before the defense sets; the first look in transition is a posting big `[O2][O3]` | UNC (Hansbrough example) `[O3]` | A big at the ball-side block with back-to-basket orientation, its defender behind, ≤ 8 s into the possession |
| **Reverse-to-seal** | Ball reversal to the side where the big has sealed `[O3]` | `[O3]` | Reversal pass, then an entry ≤ 2 s |
| **Fronted counter** | If the post is fronted, the 4 ball-screens the wing while the 2 cross-screens for the 5 `[O3]` | UNC `[O3]` | — |

### 2.5 Flow / delay entries

| Entry | Definition | Programs | Detection signature |
|---|---|---|---|
| **Delay (transition)** | Pass to the big arriving at the centre, then play 5-out off handoffs and backdoors `[O11]` | `[O11]`; NBA (Mavs Delay Chicago) `[S50]` | Big at the top with the ball ≤ 10 s into the possession; others at the arc |
| **Flow into motion** | If nothing is ahead, swing the ball into the half-court motion without pausing `[O5][O1]` | Carolina, Oregon Tech `[O1][O5]` | No stoppage (ball speed > 0.5 m/s continuously) between transition and the first half-court action |
| **Screen away** | Off-ball screen on the weak side during transition `[O11]` | — | Off-ball SCREEN at x_ball·x < 0 within 8 s |
| **Argentina** | Central PnR plus a cross screen in the paint so the big gets the ball quickly on the low post `[O11]` | — | Ball SCREEN at the top and a simultaneous CROSS screen at y < 2 |

### 2.6 Named secondary breaks

| Break | Alignment | Sequence (ordered options) | Programs | Detection signature |
|---|---|---|---|---|
| **Carolina secondary (Dean Smith / Roy Williams)** | 1 ball side and out of the middle; 2 and 3 run the wings; 4 high trailer; 5 duck-in at the ball-side block `[O1]` | (1) headman to the 2; (2) 2→5 post; (3) 2→4, 5 duck-in, high-low; (4) 2 to the corner, then to the 1, then to the 4; (5) 4 reverses to the 3; (6) on the reversal, the 2 back-screens the 4 for a lob; (7) 5 duck-in again; (8) 2→1 looking low; (9) the 4 cross-screens for the 5 and the 2 down-screens for the 4, flowing into motion `[O1]`. Roy Williams rules: ≥ 3 passes unless a layup, side-to-side, shoulder-to-hip off screens, ball into the post `[O3]` | UNC `[O1][O2][O3]` | 4-to-reversal pass at the top, a duck-in by the 5 at the ball-side block, and a back screen on the trailer within 2 s of the reversal |
| **Secondary "80"-style (Coach's Clipboard #3)** | 1 dribbles with the 3 trailing; 2 to the right corner; 5 to the left block; 4 holds the left wing `[O6]` | (1) seam drive; (2) corner pass to the 2; (3) long pass to the 5; (4) 4 cuts through or trails for the OREB; (5) trailer 3 for three `[O6]` | Generic `[O6]` | Trailer is a wing (not a big) arriving at the slot |
| **3-Up secondary** | 1 speed-dribbles; the 2, 4 and 5 sprint to the baseline, then flash high to FT-line-extended spots ("three high") `[O7]` | Wing pass: 1-on-1, PnR with the 5, 5 screens the 4, high-low. Or a UCLA cut by the 1 off the 5 `[O7]` | `[O7]` | Three non-ball players at y ≈ 3.5–5.5 simultaneously as the ball crosses half-court |
| **MSU secondary** | — | DHO plus weak-side down screen `[S11]`; "Rip to Mid Screen Iso" `[S11][S12]` | **[MSU]** | See first-pass §1.2 |

---

## F3. HALF-COURT ALIGNMENTS / ENTRIES

Classify the **alignment snapshot** first (§0.2 `ALIGN`), then the action sequence. Sets are named `<Alignment> <Action>`. The first pass §1.3 gives shapes for Horns, 1-4 high/low, Box, Stack, 2-guard front, 1-3-1, Chin, Floppy, Zipper, UCLA, Elevator, Spain, Chicago, Hammer, Delay, 4-out/5-out/3-out. Here each one gets a **metric template** and its sub-variants. The FIBA terminology lists these entries: UCLA cut, Iverson cut, Zipper cut, Power, Diamond, Wing exchange, Horns `[O24]`.

### 3.1 Alignment templates (metric)

Positions are listed without role labels. Matching tolerance is ±1.5 m unless noted.

| Alignment | 5 template positions (x, y) m | Key discriminator | Sources | Notes |
|---|---|---|---|---|
| **Horns** | Top (0, 7.6); elbows (±1.8, 4.2); corners (±6.7, 0.3) | Two bigs at the elbows with both corners filled | `[O12][S45]` | UConn base `[O14]`; Gonzaga 2016 `[O16]` |
| **Horns stack** | As Horns, but one elbow has two players stacked (≤ 1.2 m) | Elbow pair distance < 1.2 m | `[O16]` | Gonzaga: ball screen + Spain back screen + pin-down option `[O16]` |
| **1-4 High** | Top; elbows; wings (±6.0, 4.5–5.5) | Four players at y 4–6, none below y < 2 | `[S12]` | — |
| **1-4 Low** | Top; blocks (±2.1, 0.3); corners | Four players at y < 1.5 | [CONVENTION] | Clear-out / iso start |
| **Box** | Top or OOB; elbows; blocks | Two at the elbows and two at the blocks | `[O24][S12]` | BLOB base `[O24]` |
| **Stack (double-low)** | Two players at one block (≤ 1.2 m apart) | Block pair | `[O24]` | — |
| **2-3 High (UCLA high-post)** | Slots (±3.5, 7.0); wings (±6.3, 3.5); nail (0, 4.2) | Two guards in the slots, post at the nail/high post | `[O19]` | Wooden's UCLA high-post `[O19]` |
| **1-3-1** | Top; wings; nail; one at the baseline (short corner or block) | Single high post plus a single baseline player | `[S12][O29]` | Standard zone attack vs 2-3 `[O29]` |
| **2-1-2 / 2-guard front** | Slots; nail; blocks or short corners | Even front | `[O33][O24]` | Used vs odd-front zones (1-2-2, 1-3-1) `[O24]` |
| **4-out 1-in** | Slots (±3.8, 6.8); wings (±6.5, 3.5); dunker spot | One player at r < 3.5 | `[O13]` | Villanova 5 starts at the weak-side dunker spot `[O13]` |
| **5-out** | Top; wings; corners | Nobody at r < 6 | `[S31]` | — |
| **3-out 2-in** | Top; wings; blocks | Two at r < 3 | `[S31]` | Kansas high-low uses one high and one low big `[O17][O18]` |
| **Princeton 2-guard front** | Slots; wings at FT-line extended; elbow post | Two guards and no top player | `[S46]` | — |
| **Chin** | Princeton front, post at the elbow | Reversal, then a slot guard back-cuts past the elbow big | `[S46][S47]` | — |
| **Floppy** | Top; two at the rim (r < 1.5); screeners at the blocks/lane lines on both sides | Shooters under the rim at the set moment | `[S48][O24]` | FIBA: one side single, one side stagger `[O24]` |
| **Zipper start** | Top or wing ball; a block player with a stationary teammate above | Block player moves up the lane line ≥ 4 m | `[O24][S21]` | — |
| **Iverson start (4-high)** | 1-4 high | Wing-to-wing cut through y 4–6 | `[O24][S15]` | UConn Horns Iverson `[O14]` |
| **Elevator start** | Two screeners shoulder to shoulder at the elbows or nail (gap 1–1.2 m) | Gate closes to < 0.6 m after the cutter passes | `[O24][S49]` | — |
| **Diamond** | Top; elbow/high post; both wings; one under the basket | A post under the rim cuts off down screens while the high post goes opposite | `[O24]` | FIBA "Diamond offense" `[O24]` |
| **Power** | (FIBA entry name; no definition opened) | — | `[O24]` | [UNVERIFIED] |
| **Wing exchange** | Weak-side wing and corner exchange via a screen | Two weak-side players swap sides of a screen | `[O24]` | — |
| **Chest (MSU)** | Two wings low and two posts | Simultaneous down screens for both wings at entry | `[S26]` | **[MSU]** |
| **Pistol** | Ball in the slot or wing; guard in the strong-side corner; big at the top | One-side triangle, 5-out | `[O24][O8][O9]` | — |
| **Delay** | Big at the top with the ball; four perimeter | Big holds the ball at r 7–8, θ 80–100 | `[O11][S50]` | — |
| **Spread (Underwood)** | Wide slots, wings; 5 at the nail | Single player at the nail | `[S39]` | — |
| **Line (OOB)** | Four players in a vertical line, usually the ball-side lane line | Four players with \|Δx\| < 1 m, spread in y | `[O28]` | BLOB/SLOB |
| **Double stack (OOB)** | Posts on both blocks with guards stacked behind them | Two pairs at the blocks | `[O28]` | — |

**Detection signature (all alignments) [HEURISTIC]:**
- Take the snapshot when ball-handler speed is < 2 m/s and y_ball < 9 m (half-court entry), or at the first pass after crossing half-court.
- Compute the mean error to each template under the best permutation.
- Accept the best match if the error is < 1.8 m and it beats the runner-up by > 0.4 m. Otherwise label "free / motion".

### 3.2 Horns sub-family (named actions)

| Action | Definition | Sequence (t s from the set) | Counters | Programs | Detection signature |
|---|---|---|---|---|---|
| **Horns PnR / PnP** | Handler uses one elbow screen; that screener rolls or pops and the other big does the opposite `[O12]` | t0 Horns. t1 ball screen at the top. t2 roll/pop split | Twist, Flare | Generic `[O12]` | Horns snapshot, then a ball screen by an elbow player ≤ 3 s |
| **Horns Twist** | Handler uses the first screen, then reverses back off the second `[O12]` | t1 screen 1. t2 screen 2 from the opposite side. Screener 1 dives, then fades or pops | — | `[O12]` | Two ball screens from opposite directions on the same handler ≤ 2 s apart |
| **Horns Flare** | The screener flares to the arc while the other big dives `[O12]` | — | Skip | `[O12][S45]` | After the ball screen, one elbow player moves away from the ball to r > 6.75 |
| **Horns Elbow Chase** | Elbow pass, then the passer chases for a handoff; the opposite big pops or cuts `[O12]` | t1 pass to the elbow. t2 DHO back to the passer | — | `[O12]` | Pass top → elbow, then a DHO elbow → original passer ≤ 2 s |
| **Horns Zoom** | After the elbow pass, the handler screens for a wing/corner shooter who curls into a handoff from the big `[O12]` | — | — | `[O12][O15]` | Pass to the elbow, down screen by the passer, DHO from the elbow big ≤ 2.5 s |
| **Horns Split** | After the elbow pass, the passer screens for the other big or the strong-side corner (split) `[O12]` | — | Curl / flare / back-cut reads | `[O12]` | Elbow catch, then a screen between two non-ball players ≤ 1.5 s |
| **Horns High-Low** | Opposite big dives as the elbow pass is caught `[O12]` | — | Seal read | `[O12]` | Elbow catch plus the other elbow big moves to r < 2 |
| **Horns Flex** | After the elbow pass, the handler flex-screens for the weak-side corner, then gets a down screen to the top `[O12]` | — | STS | `[O12]` | Flex cut from the corner to the ball-side block, followed by a down screen on the flex screener |
| **Horns Stagger / Blast** | The handler staggers the weak-side corner off the opposite elbow; the strong-side corner back-doors ("Blast") `[O12]` | — | — | `[O12]` | — |
| **Horns Elbow Get** | After the elbow pass, the opposite elbow screens the passer, who gets the ball back and attacks downhill `[O12]` | — | — | `[O12]` | — |
| **Horns Rip / Rip Away** | Rip (back) screen variations | — | — | **[MSU]** 2024-25 `[S24b]` | — |
| **Horns Down / Quick Screen** | A guard pin-down for an elbow big | — | — | **[MSU]** `[S29g]` | — |
| **Horns Iverson** | Iverson cut out of Horns, then a cross screen and post entry | — | — | UConn `[O14]` | — |
| **Horns Dive Step-Up Cross Punch** | 5 screens and dives; a wing steps up for a ball screen; the 5 cross-screens for the other big | — | — | UConn `[O14]` | — |
| **DHO Horns Chin** | Horns, then a shallow cut, then a chin back screen and ball screen | — | — | **[MSU]** `[S28]` | — |
| **EOQ Horns** | End-of-period Horns set (title only) | — | — | **[MSU]** `[S29f]` [UNVERIFIED content] | — |

### 3.3 Box / Stack / Line sub-family (half-court and OOB)

| Action | Definition | Programs | Detection signature |
|---|---|---|---|
| **Box Cross** | 5 cross-screens for 4 and 3 cross-screens for 1, then the screeners fill spots `[O28b]` | `[O28b]` | Two simultaneous CROSS screens (\|Δx\| > 2\|Δy\|) at y < 1.5 within 1 s of the inbound/whistle |
| **Box Up** | Two up (back) screens for the high players `[O28b]` | `[O28b]` | Two back screens from the blocks toward the elbows simultaneously |
| **Box Diagonal** | 4 screens for 3; then 5 sets a diagonal screen for 1 and dives `[O28b]` | `[O28b]` | Screen with an axis 30–60° off the baseline |
| **Box STS / Up Screener / Diagonal Screener** | Screeners get screened in turn `[O28b]` | `[O28b]`; MSU Box "Screen the Screener" `[S12]` | Screener becomes a cutter ≤ 1.5 s after screening |
| **Box Elevator** | 3 and 4 set an elevator for the 2 at the wing `[O28]` | `[O28]` | — |
| **Box Double Down** | — | **[MSU]** `[S12]` | — |
| **Stack 1 split / Stack Rub / Double stack / Triple screen** | See F13.2 | `[O28c]` | — |

### 3.4 Other named starts (extensions)

| Start | Definition | Programs | Detection signature |
|---|---|---|---|
| **Elbow** | Ball to the elbow, double pin-downs | Gonzaga "Elbow" sets `[O16]` | Pass to the elbow plus two simultaneous down screens |
| **Rip** | Back screen on the wing for a cutter; Rip DHO = handoff to the back-screener `[O24]` | **[MSU]** Rip Away `[S24b]` | Back screen, then the screener receives a DHO ≤ 2 s |
| **Wide** | High cross screen from the top or wing for a weak-side wing or corner player `[O24]` | — | Screen at y 4–7 with a lateral cutter path |
| **Gortat / Hostage** | The roller screens the drop defender after the handler turns the corner `[O24]`; UConn uses it vs post fronts `[O14]` | UConn `[O14]` | After a ball screen, the roller stops at r 1.5–3 and contacts the help big's path |
| **Shake** | The corner player lifts toward the handler during a side PnR `[O24]` | — | During a wing PnR, the strong-side corner player moves to the wing/slot (Δr ≥ 0, Δθ toward 90°) |
| **Slide (Hoiberg roll)** | Weak-side dunker cuts to the strong-side dunker as the screener rolls into the lane `[O24]` | — | Weak-side dunker crosses the lane at y < 1 within 1 s of the roll |
| **Blind pig** | Handler passes to a big, who passes to a backdoor cutter `[O24]` | Princeton family `[S46]` | Pass to the high post, then a backdoor cutter catches at r < 2 ≤ 1.5 s |
| **Twirl** | Cutter curls the first of two stagger screens; the first screener comes off the second `[O24]` | — | Stagger in which the first screener becomes a cutter off the second |
| **Wiper** | Flare then pin-down (or the reverse) for the same cutter `[O24]` | — | Same cutter uses a flare and a down screen ≤ 2.5 s apart |
| **Ricky** | Back screen then down screen for the same player `[O24][S21]` | — | — |

---

## F4. CONTINUITY & MOTION SYSTEMS

These are **possession-level** labels. Recognize them by *repeating rule patterns* across ≥ 2 cycles, not from one action. The first pass covers 5-out, 4-out 1-in, circle, dribble-drive, Read & React, Flex, Shuffle, Swing, Blocker-Mover, Princeton, Triangle, Underwood Spread, and Euro ball-screen. Below are full entries, plus systems that were missing.

### 4.1 Pattern continuities

| System | Alignment | Core cycle (ordered) | Counters | D-I programs (sourced) | Detection signature |
|---|---|---|---|---|---|
| **Flex** | 4 around 1 with a low post `[S33]` | Flex cut (corner → ball-side block off a block screen), then a down screen on the flex screener (STS), then repeat after reversal `[S33]` | 4-/5-man variants | **Auburn (Pearl)**: 2-guard front, flex screen first, screener *pops* by default, then flows into a weak-side two-man step-up game rather than staying in continuity `[O15]`. Gonzaga used flex as its primary motion system in the late 1990s–2000s `[O16]` | Flex cut (path from θ ≤ 15° weak-side corner along y < 1 to the ball-side block) followed ≤ 1.2 s by a down screen on the flex screener. ≥ 2 repetitions = continuity; 1 = flex action |
| **Shuffle** | Five rotating spots `[S34]` | Shuffle cut over the high post, cutter to the high post, point down-screens the post, repeat `[S34]` | — | Historic: Drake, Spear, Dean Smith `[S35]` | Diagonal weak-side wing → ball-side block cut past a high-post screener; role rotation |
| **UCLA high-post** | 2-3 high (two-guard front, post flashes to the high post) `[O19]` | (1) guard-to-guard; (2) pass to the wing or high post; (3) on a high-post entry, the wings back-cut and the guards V-cut out; (4) post feeds a wing; post down-screens. The wing passer relocates to the corner `[O19]` | Criss-cross, scissors, guard curl, wing-denial back-cut, PnR `[O19]` | John Wooden (UCLA) `[O19]` | Two-guard front, then guard → wing pass, then the passer cuts off a high-post screen to the block (UCLA cut) |
| **Kansas high-low (Bill Self)** | Two true bigs (one high, one low); 1 enters to the wing and cuts to the weak-side corner `[O17][O18]` | (1) wing catch; (2) 4 cross-screens 5, who opens to the top; (3) centering pass to the high big; (4) the low big positions between ball and basket: lob if fronted, scoop if 3/4, duck-in if behind; (5) reverse with down screens; (6) stagger away or weak-side PnR `[O17]`. Rules: bigs slip on screens, littles clear to the arc; pass to a side with one player = stagger away, two players = single down; auto backdoor if overplayed on the reversal `[O18]` | Ball-screen-heavy years vs not; shift to four-guard lineups by 2019 `[O34]` | Kansas (Self) `[O17][O18][O34]` | Two bigs whose y differ by > 3 m, one at the elbow/nail and one at r < 2.5. Big-to-big passes ≥ 1 per possession. The low big is on the line between ball and basket when the high big holds the ball |
| **Swing (Bo Ryan)** | — | See first-pass §1.4 `[S30][S36]` | — | Wisconsin (legacy) | — |
| **Blocker-Mover / "Sides" (Bennett)** | Two blockers near the elbows, three movers `[O35]` | Near-simultaneous pin-downs by both blockers; movers cut/fade/drive; a fade to the top gets a flare from the opposite big; the third guard back-doors off a baseline flare; empty-backside wing PnR `[O35]` | Inside Triangle variant `[O36]` [title only] | Virginia (Tony Bennett) `[O35]` | Two players whose x stays on one side and act only as screeners. Simultaneous pin-downs at the set. An empty-side ball screen late in the clock |
| **Princeton (Carril)** | — | See first-pass §1.4 `[S46][S47]` | — | Princeton; Georgetown (JT III) [CONVENTION] | — |
| **Triangle** | — | See first-pass §1.4 `[S38]` | — | — | — |
| **Underwood Spread** | — | See first-pass §1.4 `[S39]` | — | Illinois | — |
| **Continuity ball screen (Witherspoon)** | "Tandem side" | DHOs and ball screens. The top guard on the tandem side back-doors (2011), then a flare (2012), then a UCLA screen after the flare (2013) `[O37]` | Flare, UCLA | Buffalo / Canisius (Witherspoon) `[O37]` | Repeating DHO → ball screen pairs on alternating sides; tandem (two players stacked on one side) |
| **DHO / Chase motion (5-out handoff continuity)** | 5-out, or a big at the top (Delay) | Ball moves via a chain of DHOs. Dribbled at → back-door or take the handoff `[O41]`. Get/chase: pass and follow for the handoff `[O49]`. Re-screen if the defender goes under, back-door if jammed `[O22]`. Hand-backs in 5-out `[O15]` | Back-door, keep (fake DHO) | Alabama, Creighton, Nebraska (hand-backs) `[O15]`; Delay usage growing in college `[O57]` | ≥ 3 DHOs in one possession with no ball screens between them; receivers relocate along the arc |
| **Chattanooga ball-screen continuity** | — | (diagram title) `[O38]` | — | Chattanooga `[O38]` [UNVERIFIED content] | — |
| **Diamond offense** | Diamond | Post under the basket cuts off down screens while the high post goes opposite `[O24]` | — | — | — |

### 4.2 Rule-based motion systems

| System | Alignment | Rules | D-I programs | Detection signature |
|---|---|---|---|---|
| **4-out 1-in motion (Villanova)** | Slots slightly wider than elbow-extended; wings at FT-line extended; 5 at the weak-side dunker `[O13]` | Slot→wing pass triggers a thru-cut to the weak-side wing (give-and-go look); others rotate to fill. Wing→slot→slot reversal and exchange. On the wing catch, the 5 runs to the strong block for an early entry; the post passer splits with the nearest player. Catch low with eyes on the rim, play off two feet. Slot ball screen on reversal: the strong-side wing lifts behind, the weak side exchanges `[O13]` | Villanova (Jay Wright) `[O13]` | One player at r < 3.5 for ≥ 70% of possession time. Slot→wing pass followed ≤ 1 s by the passer cutting through the paint to the opposite wing. The post moves to the strong block on wing catches |
| **5-out motion** | Top, wings, corners | Pass-cut-fill `[S31]`; Davidson's 5-out under McKillop uses screening, cutting and spacing `[O39]` [details paywalled] | Davidson (McKillop) `[O39]` | No player at r < 4 at the set; cuts are followed by arc refills |
| **Dribble-drive motion** | 1-2-2 / 2-2-1 / 5-out; middle open; post opposite the ball, often on the baseline `[O41]` | Layup first. Kick on perimeter help, dump on post help. The penetrator clears out of the middle. Dribbled at → back-door or DHO. High-post catch → open-side back-door. Ball stuck at the top → weak-side forward posts `[O41]` | Calipari (Memphis), Walberg (Pepperdine) `[O41]` | DRIVE rate high, SCREEN rate low. After each drive, perimeter players relocate along the arc on the drive side |
| **Read & React** | Any | See first-pass §1.4 `[S32]` | — | — |
| **Kansas "Wing Entry-Strongside" motion** | Wing entry with bigs playing off each other (one at the "sweet spot", one posting) `[O18]` | Bigs cross; leg-whip into the lane; ducking in whenever the ball is at the sweet spot; the weak-side player must cut on a no-option reversal `[O18]` | Kansas `[O18]` | Big-big cross screen at y < 2 after the wing entry; the receiving big catches at the sweet spot (r 4–5.5, θ 30–60°) |
| **Pace-and-space / analytics shot diet (Oats)** | 4-out or 5-out with a stretch 5 `[O42]` | About 92% of shots at the rim or from three; the threes are mostly a by-product of chasing rim and paint touches ("shrink threes" after rotation). Fast pace for efficiency. Players are subbed for *passing up* open looks `[O42]` | Alabama (Nate Oats) `[O42]`; Alabama also runs hand-backs, pin-downs and staggers in 5-out `[O15]` | Shot-location distribution with ≥ 85% of FGA at r < 1.5 or beyond the arc. Paint touches precede ≥ 50% of threes |
| **Analytics-driven ball screen + 5-out (Wisconsin 2024-25)** | — | Ball-screen-heavy NBA-style reads; early-clock shots | Wisconsin (Gard / Penney) `[S94]` | — |
| **Purdue post-centric 4-around-1** | One dominant post with four shooters `[S75]` | Post entries to the low block draw fouls; post-catch pivot, fake and hook finishes; more PnR for the guard engine `[O43][S93]` | Purdue (Painter) `[S75][O43]` | One player owns ≥ 50% of touches at r < 3. Repeated wing → block entries |
| **Houston (Sampson)** | — | Multiple options aimed at the best matchup ("move our compass around"); guard-on-big hunting; very low turnovers `[O44]`. Offense is built around offensive rebounding with guards as lead rebounders (F14) `[O45]` | Houston (Sampson) `[O44][O45]` | High OREB attempt rate by guards. Switch-hunting screens (screener's defender is a guard) |
| **UConn motion (Hurley)** | Horns base with two elbow bigs `[O14]` | Iverson, Zipper, Gortat screen vs fronts, Zipper Flare Wedge, Horns Dive Step-Up Cross Punch, Ram Veer Reject Exit, "Wheel" `[O14]` | UConn (Hurley) `[O14]` | Horns snapshot → multi-action chains (≥ 3 screens in 8 s) |
| **Gonzaga (Few)** | Mixed | Evolved from flex/motion (scissor and Carolina entries) to ball-screen continuity, Spain, Floppy, Horns (2016) and zipper middle ball screens; heavy transition post-ups for bigs `[O16]` | Gonzaga (Mark Few) `[O16]` | Early-clock post touches at r < 2.5. Zipper → middle ball screen |
| **Creighton (McDermott)** | 5-out | Zoom action, hand-backs, actions for shooters (Ballock) `[O15][O37]` | Creighton `[O15][O37]` | Zoom (down screen → DHO) frequency high |
| **Nebraska (Hoiberg) / Davidson** | 5-out | Hand-backs, pin-downs, staggers, slice staggers `[O15]` | `[O15]` | — |
| **Michigan (Dusty May)** | Two-big or 5-out | "Create space or put two on the ball"; inverted PnR, Iverson Ram, Spain, Elevator `[S24][S96]` | Michigan | — |
| **MSU (Izzo)** | Multiple | Pro-style sets with freelance; Horns and "452" quick hitters; 1-3-1 zone sets; ball-screen and handoff actions; rip screens; offensive rebounding `[S6][S12][S24b]` | **[MSU]** | See first-pass §3 |

---

## F5. BALL-SCREEN OFFENSE

Model a ball screen as a **5-tuple**: **Location × Angle × Screener-pre-action × Screener-post-action × Handler-read**, plus **off-ball spacing tags**. Each axis is detected separately, and the named actions below are combinations of them. The first pass §1.5 already covers high/side/empty/step-up/sprint-up/drag/double/stagger/Spain/ghost/slip/short roll/re-screen/twist/veer/ram/inverted/screen-own-man.

### 5.1 Location (where the handler is when the screen is set)

| Location | Definition | Detection (handler position at screen contact) |
|---|---|---|
| **High / Top** | Handler at the top of the key `[O24]`; Middle ball screen, with two players spaced in the corners and one on the wing `[O46]` | r 6.5–9.5, θ 75–105° |
| **Slot / Angle** | Handler at the slot spot `[O24]`; "Spread" ball screen in the slot, others at the strong-side corner plus weak-side corner and wing `[O46]` | r 6.5–9, θ 50–75° or 105–130° |
| **Side / Wing** | Handler on the wing, with the ball-side corner empty or filled `[O24][O46]` | r 6.5–8.5, θ 25–50° / 130–155° |
| **Logo / Deep** | Handler far beyond the arc ("logo") — note: FIBA's "logo ball screen" text reads "short-corner spot" `[O24]`, which looks like a transcription issue [UNVERIFIED] | r > 9 |
| **Corner ball screen** | Screen for a handler in the corner (e.g., BLOB box variant: ball screen in the corner for a mid-range shot) `[O28]` | θ ≤ 15° or ≥ 165° |
| **Post / mid-post** | Ball screen near the elbow-extended for a post handler (European "post PnR") `[O47]` | r 3–5 |

### 5.2 Angle (screener's body orientation relative to the baseline)

| Angle | Definition | Detection |
|---|---|---|
| **Flat** | Screener's back is parallel to the baseline (perpendicular to the handler's path) `[O24][O48]` | The screener→defender vector is within ±20° of the +y axis |
| **Angled (45°)** | Set about 45°, which creates more reject opportunities `[O48]` | Vector 25–65° off the y-axis |
| **Step-up** | Big screens from below the FT line, pushing the handler toward the baseline `[O24][S56]` | Screener's prior y < handler's y − 1.5; screener→defender vector has a +y component |
| **Butt screen** | Flat screen near the top with the screener's back to the handler `[O24]` | — |
| **Flip (flipping the screen)** | Screener changes angle at the last moment `[O24]` | Screener orientation rotates > 60° in the 0.5 s before contact |
| **Re-screen** | A second screen from a new angle on the same defender `[O11][O46]` | Same pair, second SCREEN ≤ 3 s, opposite side |

### 5.3 Screener pre-action (how the screener arrives)

| Pre-action | Definition | Programs | Detection |
|---|---|---|---|
| **Sprint-up / sprint** | 5 sprints from below the block into a high screen | **[MSU]** `[S17]` | Screener speed > 3.5 m/s from y < 1 |
| **Drag** | Trailer screens on the move in transition `[O24]` | — | F2 |
| **Ram** | Screener first receives an off-ball screen, then sets the ball screen `[O24][O21]` | Michigan "Iverson Ram" `[S24]`; UConn "Ram Veer Reject Exit" `[O14]` | Player *s* uses an off-ball SCREEN, then sets a ball SCREEN ≤ 2 s |
| **Wedge** | A guard decoy-screens the big, then the big screens the handler `[O24]` | — | Same as Ram, but the first screener is a guard and the second is a big |
| **Zipper → middle ball screen** | Zipper cut into a middle ball screen | Gonzaga `[O16]` | Block→slot cut ≤ 1.5 s before a ball screen by the original down-screener or the zipper cutter |
| **Iverson → ball screen** | Iverson cut, then the elbow big steps up | Michigan "Iverson step-up" `[S24]`; MSU "4-High Iverson Curl" `[S15]` | — |
| **Exit → ball screen** | — | — | — |
| **Touch** | Big touches the defender's hip and slips `[O24]` | — | Screener contact time < 0.2 s, then a dive |

### 5.4 Screener post-action

| Post-action | Definition | Detection |
|---|---|---|
| **Roll / deep roll** | Roll to the basket; deep roll goes all the way to the rim `[O24]` | Screener reaches r < 2 within 1.5 s |
| **Short roll** | Stop near the FT line to receive and make plays `[O24]` | Screener stops at r 3–5 and catches |
| **Pop** | Move to the three-point line `[O24]` | Screener ends at r > 6.5 |
| **Slip** | Leave before contact `[O24][O21]` | Stationary < 0.3 s |
| **Ghost** | Fake screen, no contact, cut away `[O24][O21]` | Approach to within 2 m, never stationary |
| **Seal / Gortat (hostage)** | After the turn, the roller screens the drop defender `[O24][O14]` | Roller stationary at r 1.5–3 between the help big and the handler's path |
| **Veer** | Ball screen, then a wide pin-down by the same screener `[O24][O21]` | Same screener: ball SCREEN, then off-ball SCREEN ≤ 2 s |
| **Twist** | Two ball screens from opposite directions `[O24][O12]` | — |
| **Re-screen** | See 5.2 | — |

### 5.5 Handler reads

| Read | Definition | Detection |
|---|---|---|
| **Use / turn the corner** | Attack in the direction the screen is set; first priority is to score, then hit the screener, then punish the help `[O46]` | Handler passes the screener on the screen side |
| **Reject** | Attack opposite the screen side `[O24][O46]` | Handler goes away from the screener before contact |
| **Snake** | Use the screen, then dribble back across in front of the trailing defender (counter to going over) `[O48]` | Handler's path crosses back over the screener's x within 1.5 s |
| **Split** | Dribble between the two defenders vs a hedge or trap `[O48]` | Handler passes between two defenders that are < 2 m apart |
| **Pull-up** | Shoot vs under / drop `[O48]` | FGA ≤ 1 s after the screen, at r > 4 |
| **Pocket / lob to the roller** | Pass to the roller vs a two-on-ball or a drop `[O48][O24]` | PASS to the screener within 2 s |
| **Freeze dribble** | Stop after the screen to keep the dribble and re-attack for a 2-on-1 `[O24]` | Handler speed < 1 m/s for ≥ 0.5 s with the dribble alive |
| **Hostage dribble** | Keep the defender behind on the back `[O24]` | Defender trails the handler within 1 m while the handler slows |
| **Gator** | Reject the screen and pass to a nearby player `[O11]` | — |
| **Refuse / Keep** | Fake the use and drive the other way `[O11]` | — |

### 5.6 Off-ball spacing tags during a PnR

| Tag | Definition | Detection |
|---|---|---|
| **Empty side** | Side PnR with no ball-side teammate `[S55][O11]` | No teammate with the same sign(x) and \|x\| > 3 |
| **Single tag** | One player on the ball side `[O24]` | — |
| **Double tag** | Two players on the roll side of a top screen `[O24]` | — |
| **Shake** | Corner player lifts during a side PnR `[O24]` | — |
| **Slide (Hoiberg)** | Weak dunker to strong dunker as the roller enters the lane `[O24]` | — |
| **Drift / lift** | Off-ball players drift toward the baseline/midcourt or fill the vacated spot during penetration `[O24]` | — |
| **Strong-side wing lift** | Strong-side wing lifts behind the handler to remove the tag defender `[O13]` | Villanova slot ball screen `[O13]` |
| **Weak-side exchange** | Weak-side players exchange to occupy the nail help `[O13]` | — |
| **Spain** | Back screen on the roller's defender, then the back-screener pops `[S19][O24][O21]` | First-pass §1.5 |

### 5.7 Named ball-screen sets / actions (beyond the first pass)

| Set | Definition | Sequence | Programs | Detection signature |
|---|---|---|---|---|
| **Horns Dive Step-Up Cross Punch** | — | 5 screens and dives, a wing steps up for a ball screen, 5 cross-screens for the other big `[O14]` | UConn | Two consecutive ball screens (top, then side step-up) with a paint cross screen by the first screener |
| **Ram Veer Reject Exit** | — | Cross screen into a ram, sell a veer, handler rejects, exit screen for a shooter `[O14]` | UConn | ≥ 4 screen events in ≤ 6 s involving the same 2 bigs |
| **Detroit** | Double ball screen, shooter pops, non-shooter rolls | — | **[MSU]** `[S12][S18]` | — |
| **Sprint-up** | — | — | **[MSU]** `[S17]` | — |
| **Back-Screen PnR (veer-like)** | 5 back-screens 4, then ball-screens 1 | — | **[MSU]** `[S12]` | — |
| **Rip to Mid Screen Iso** | — | — | **[MSU]** `[S11][S12]` | — |
| **Empty-backside wing PnR (Virginia)** | Ball screens on the empty backside within sides motion `[O35]` | — | Virginia | Side PnR with an empty strong side late in the clock after ≥ 2 pin-downs |
| **Step-up two-man (Auburn)** | Flex screener pops, then a step-up screen for the guard into the paint, or a pick-and-pop | — | Auburn `[O15]` | Flex cut, then the screener pops to r > 6.5, then a step-up SCREEN by the popper ≤ 3 s |
| **Kohler pick-and-pop** | Stretch big pops after the screen | — | **[MSU]** 2025-26 `[S89]` | Screener (a big) ends at r > 6.75 and catches ≤ 2 s after the screen |

---

## F6. HANDOFF OFFENSE

`[O20]` gives a tracking-data DHO detector: SportVU, 1,098 positives, ±2 s windows, SVM best, and fakes ≈ 5% of positives. It is the closest prior art for this family.

| Action | Definition | Start | Sequence | Counters / reads | Programs | Detection signature |
|---|---|---|---|---|---|---|
| **DHO (conventional)** | Ball-handler dribbles into the receiver and hands off; both continue as in a PnR `[O20][O22]` | Any | Approach, then handoff, then the receiver attacks; the hander rolls or pops | Backdoor if jammed; re-screen if the defender goes under; keep if the defense jumps it `[O22]` | Universal | DHO primitive. Receiver speed > 2 m/s at transfer |
| **Fake DHO / Keep** | Approach as a DHO, but the hander keeps the ball and drives `[O20][O22][O9]` | — | — | — | Pistol "Keep" `[O10]` | Hander–receiver distance < 1.5 m, no ball transfer, hander DRIVE ≤ 1 s |
| **Get / Chase / Throw-and-go** | Pass to a big, follow the pass, and receive the handoff back `[O49]` | Usually a big at the top or elbow | t0 pass. t0.5–1.5 handoff back to the passer | Over → turn the corner + roll. Under → pull-up or re-screen. Blitz → the big keeps and attacks `[O49]` | Pro and college; early-offense trigger `[O49]`; Horns Elbow Chase `[O12]`; Pistol "Chase" `[O10]` | PASS(a→b), then DHO(b→a) within 2 s, with the same two players |
| **Handback / Flip** | Pass to a player who hands or pitches it back `[O11][O24][O15]` | Slots with a top screener | — | — | Alabama, Creighton, Nebraska `[O15]` | Pass a→b, then b→a by pitch ≤ 1.5 s, both above the arc |
| **Zoom / Chicago** | Pin-down into an immediate DHO `[O50][O21][O24]` | Receiver in the corner or below the arc on the wing; big brings the ball to the top or elbow `[O50]` | Down screen, receiver comes toward the ball, DHO, read | Drive, pull-up, re-screen, short-roll pass; backdoor vs overplay `[O50]` | Creighton, Purdue `[O15]`; UConn `[O50]`; Horns Zoom `[O12]` | SCREEN(down) on *u*, then DHO to *u* ≤ 1.5 s |
| **Zoom variants** | Wing Zoom (wing to wing), SLOB Zoom (from the elbow), Empty Zoom (decoy cut), Corner Zoom disguise, Motion Zoom `[O50]` | — | — | — | NBA examples `[O50]` | — |
| **Twist (DHO)** | Misdirection changes which player receives the DHO `[O15]` | — | — | — | — | Two candidate receivers converge; the DHO goes to the second |
| **Miami** | Consecutive DHO followed by a pick-and-roll `[O11]` | — | DHO, then an immediate ball screen by the hander | — | — | DHO(a→b), then a→b SCREEN ≤ 1.5 s |
| **Rip DHO** | The player who set a back screen receives a DHO `[O24]` | — | — | — | **[MSU]** Rip Away `[S24b]` | Back SCREEN by *s*, then DHO to *s* ≤ 2 s |
| **Delay DHO chains** | Big at the top hands off to perimeter players in turn | 5-out, big at the top | — | Backdoor on denial | `[S50][S52][O11]` | Big at the top makes ≥ 2 DHOs in one possession |
| **Post Grenade DHO** | DHO run from the post area `[O47]` [name only] | — | — | — | European `[O47]` | DHO with the hander at r < 4 |
| **MSU DHO + weak-side down screen** | — | — | — | — | **[MSU]** `[S11]` | — |
| **DHO Clear Lob** | — | — | — | — | **[MSU]** `[S29d]` | — |

---

## F7. POST OFFENSE

| Sub-family | Action | Definition | Programs | Detection signature |
|---|---|---|---|---|
| **Positioning** | **Seal / duck-in** | Reverse pivot to seal the defender on the back `[O24]` | Universal | Post moves into the paint with the defender behind within 1 m |
| | **Early seal (transition)** | See F2.4 `[O3]` | UNC | — |
| | **Leg-whip** | Reverse pivot to whip the defender into the lane and keep him on the high side `[O18]` | Kansas `[O18]` | — |
| | **Re-post** | After a kick-out from the post, the post re-establishes position for a second entry [CONVENTION] | — | A second entry to the same post ≤ 6 s after the first |
| | **Barkley** | Dribble from the perimeter into the low block `[O24]` | — | Dribble backing in from r > 5 to r < 3 with the back to the basket |
| **Entries** | **Wing entry** | Wing feeds the block | — | PASS from (r 6–8, θ 25–55) to r < 3 |
| | **Corner entry** | Pass from the corner to the block/short corner [CONVENTION] | Kansas: throw to the corner of the backboard when the defender is high-side `[O18]` | — |
| | **High-low** | High post (elbow/nail) feeds the low post `[O24][O17]` | Kansas `[O17]`; MSU Chest `[S26]` | Pass from r 3.8–5 to r < 2.5 |
| | **Lob vs front** | Low big walks the fronting defender up the lane and gets a lob `[O17]` | Kansas | Lob pass (ball height > 3.5 m) to r < 2 |
| | **Scoop vs 3/4 / duck-in vs behind** | Entry chosen by the defender's position `[O17]` | Kansas | — |
| | **Top-down entry** | Swing teaching when fronted `[S30]` | Wisconsin | — |
| **Two-post** | **High-low (two bigs)** | Two true bigs; constant reversals and seals `[O34][O17]` | Kansas | F4 |
| | **Cross-screen post (big-for-big)** | 4 cross-screens 5 on the wing catch `[O17][O18]` | Kansas; Carolina secondary `[O1]` | CROSS screen between two bigs at y < 2 |
| | **Double-post / triple post** | Two or three posts around the lane; Brazilian triple post curl/backdoor `[O47]` | European | ≥ 2 players at r < 4 for ≥ 3 s |
| **Post + perimeter** | **Post split** | After the entry, the passer screens away or uses a screen with the nearest perimeter player; slip/reject variants `[O51][O24]` | Villanova `[O13]` | Post catch, then a SCREEN between the passer and the nearest perimeter teammate ≤ 2 s |
| | **Elbow split** | Two players split at the elbow; one slips/dives, one spaces `[O47]` | European | — |
| | **Flare / re-screen / rip the passer** | Actions for the entry passer immediately after the entry `[O47]` | European | Entry passer gets a SCREEN ≤ 1.5 s after the pass |
| | **Bilbao** | Flare for the passer plus a weak-side elbow split `[O47]` | European | — |
| | **Dunker dive and space** | Opposite big dives to the dunker spot; three space `[O47]` | — | — |
| | **Weak-side action** | Cuts or screens on the weak side while the post attacks the ball side `[O24]` | — | — |
| | **Post PnR** | Ball screen for the post handler `[O47]` [name only] | — | — |
| **Isolation** | **Post iso / clear** | Clear the post side | **[MSU]** ISO-5, Rip to Mid Screen Iso `[S12]` | Ball-side perimeter players vacate (\|x\| on the opposite side) ≤ 2 s after the entry |
| | **High-post iso** | Big flashes to the elbow and the others clear | **[MSU]** ISO-4, ISO-3 Chest `[S12]` | — |
| | **Pinch post** | Big at the weak-side elbow as a hub `[O24]` | Illinois `[S39]`; MSU Iverson to Double Screen `[S27]` | Ball at the elbow (r 4–5, θ 55–75°/105–125°) held ≥ 1.5 s |
| | **Short-corner post** | Post catch in the short corner | **[MSU]** `[S27]` | — |
| **Post-entry scoring finishes** | Hook, drop step, up-and-under, jump hook `[O24]` | Purdue: pivot, fake and hook rather than going through contact `[O43]` | (outcome layer) |

---

## F8. OFF-BALL SCREENS AND CUT VOCABULARY

The first pass §1.7 defines down, wide pin-down, flare, back/rip, cross, stagger, double, elevator, hammer, flex, UCLA, Iverson, zipper, shallow, gut/wedge/slice, exit, Ricky, STS and Hawk. Additions and metric signatures follow.

### 8.1 Screens (geometry classes)

| Screen | Definition | Detection (screener → defender vector *v*; cutter displacement *d*) |
|---|---|---|
| **Down / pin-down** | Screen from the wing to the low post; screener faces the baseline `[O24][O21]` | *v* points −y; *d* points +y; screener at y 0–4, \|x\| 3–7 |
| **Corner pin / wide pin-down** | Pin-down on the corner or wing defender `[O21]` | Screener at θ ≤ 25° or ≥ 155° |
| **Back / up / rip** | Screen behind the defender; cutter goes toward the rim `[O24]` | *d* points −y toward r < 2 |
| **UCLA / up** | From the low post to the slot or top `[O24]`; Synergy logs the cut as a Cut `[O53]` | Screener at the elbow or high post; cutter goes slot/top → block |
| **Cross** | Low post to opposite low post `[O24]` | Both at y < 2; \|Δx_cutter\| > 3 |
| **Flare** | For a player moving away from the ball `[O24]` | Angle(*d*, cutter→ball) > 120° |
| **Hammer** | Weak-side flare for a shooter cutting wing → corner while the handler drives baseline `[O24]` | Simultaneous baseline DRIVE and weak-side flare toward θ ≤ 12° |
| **Stagger** | Two non-adjacent screens for one cutter `[O24]` | Two screeners 2–4 m apart along *d* |
| **Double / parallel** | Two side-by-side screeners `[O24]` | Two screeners < 1.2 m apart |
| **Elevator / gate** | Two screeners slide apart and then close `[O24]` | — |
| **Twirl** | Curl the first stagger screen; the first screener comes off the second `[O24]` | — |
| **Wiper** | Flare then pin-down (or the reverse) for the same cutter `[O24]` | — |
| **Ricky** | Back screen then down screen for the same player `[O24]` | — |
| **Wide** | High cross screen from the top or wing for a weak-side wing or corner `[O24]` | Screener at y 4–7, lateral *d* |
| **Exit / baseline exit** | Baseline-parallel screen toward the corner for a shooter `[O24]` | Screener at y < 1, *d* toward θ ≤ 12° |
| **Shot screen** | Weak-side screen for a shooter `[O24]` | — |
| **Brush screen** | Cutter passes near a defender without contact `[O24]` | No stationary screener; the defender's path is blocked by a moving teammate |
| **Blade** | Cutter goes to the basket during the big's roll instead of lifting `[O24]` | — |
| **Hostage / containing (off-ball)** | Weak-side screen that punishes a help defender's positioning `[O24]` | — |
| **Screen your own** | Screen your own defender to stop a switch `[O24]` | **[MSU]** Winston `[S25]` |
| **Screen away** | Pass one way, screen the other way `[O24]` | Passer sets a SCREEN with opposite sign(x) to the ball ≤ 1.5 s after the pass |
| **STS** | Screener immediately receives a screen `[O24]` | — |
| **Gut / wedge / slice** | Middle-floor screen / diagonal screen into the post (screener faces the nearest sideline) / straight wing back screen `[O21]` | — |
| **Flex** | Weak-side low-post screen for the corner cutter `[O24]` | — |
| **Zipper** | Down screen for a block cutter to the slot `[O24][O21]` | — |
| **Diagonal (BLOB)** | Screen set on a ~45° line `[O28b]` | *v* 30–60° off the axes |

### 8.2 Cuts

| Cut | Definition | Detection |
|---|---|---|
| **Backdoor** | Step out, then cut behind the defender to the basket `[O24]` | Cutter reverses heading (> 120°) and reaches r < 2 ≤ 1.5 s |
| **Banana** | Wide curved cut `[O24][O5]` | — |
| **Basket / dive** | Cut toward the basket `[O24]` | — |
| **Curl** | Around a screen toward the basket `[O24]`; hard (paint) or wide (along the arc) `[O21]` | Path curvature around a stationary screener with the end r < screener r |
| **Fade / flare** | Away from the ball `[O24]` | — |
| **Flash** | Low → high post, or through the middle of a zone `[O24]`; Synergy "flash cut" = an unscreened cut toward the ball `[O53]` | Unscreened move toward the ball ≥ 3 m into the high post |
| **Flex cut** | Weak-side corner → ball-side low post `[O24]` | — |
| **I-cut** | Step in, then back out `[O24]` | — |
| **Iverson** | Horizontal wing-to-wing cut off the elbows `[O24]` | — |
| **Pop-out** | Around a screen straight to the ball `[O24]` | — |
| **Shallow** | Top of the key → ball-side corner `[O24]` | Path from θ 70–110 to θ ≤ 15 on the ball side, staying near the arc |
| **Shuffle** | Around a high-post screen to the basket `[O24]` | — |
| **UCLA** | Top → low post over a high-post screen `[O24]` | — |
| **V / L-cut** | Go to a spot, make contact, then cut out (L = 90°) `[O24]` | Reversal of heading of 90–180° at r 4–6 |
| **Thru-cut (motion)** | Slot passer cuts through the paint to the weak-side wing `[O13]` | — |
| **Stampede** | Off-ball cut already moving to the basket, catching on the move `[O21]` | — |
| **45 cut** | Wing cut at about 45° `[O21]` | — |
| **Delayed / secondary cut** | Cut timed after an initial drive `[O21]` | — |
| **Drift / lift** | Spacing adjustments during penetration `[O24]` | — |
| **Give-and-go** | Pass, cut, return pass `[O24]` | PASS a→b, CUT(a), PASS b→a ≤ 2 s |
| **Blind pig** | Handler → big → backdoor cutter `[O24]` | — |
| **Weak-side baseline cut** | Farthest shooter cuts along the baseline `[O47]` | — |

### 8.3 Screen-use reads (labels)

| Read | Definition | Detection |
|---|---|---|
| Curl / straight / fade / reject / back-cut | First pass §1.7 `[S21][S48]` | Angle of exit relative to the screener and the rim |
| **Slip (off-ball)** | Screener cuts before contact `[O24]` | — |
| **Pop vs dive (screener)** | — | — |

---

## F9. ISOLATION AND CLEAR-OUT SETS

| Set | Definition | Start | Sequence | Programs | Detection signature |
|---|---|---|---|---|---|
| **Clear-out (generic)** | Non-ball players clear so one player can go 1-on-1 `[O24][O52]`; used for the best scorer, a mismatch, low clock, or to force a double `[O52]` | Any | Teammates move to spots away from the ball | — | Ball-handler holds ≥ 3 s with no teammate within 6 m and no SCREEN |
| **1-4 Low iso** | Four along the baseline (corners and blocks), the top player isolates [CONVENTION]; FastModel lists "1-4 Low 3 Iso" and "1-4 Low Push Zip Iso" `[O54]` [titles] | 1-4 low | — | — | 1-4 low snapshot then DRIVE from the top |
| **Wing iso / clear side** | Clear the ball side; most common on the wing `[O52]` | Wing | Ball-side corner and slot clear | — | No teammate with the same sign(x) and \|x\| > 3; handler at the wing |
| **Post iso** | See F7 | — | — | **[MSU]** `[S12]` | — |
| **High-post / elbow iso** | Big catches at the elbow and the others clear | — | — | **[MSU]** ISO-4 `[S12]`; Aces "Pinch Post Elbow Iso" `[O55]` [title] | — |
| **Mismatch iso (switch-hunt)** | Screen to force a switch, then clear | — | — | Houston: get a guard on a big or a big on a guard `[O44]` | Ball SCREEN that causes a defender swap, then the ball-handler holds ≥ 2 s with no further screens |
| **X-ISO** | MSU set name (no description) | — | — | **[MSU]** `[S12]` [UNVERIFIED content] | — |

---

## F10. SPREAD / DRIVE-AND-KICK / PAINT-TOUCH OFFENSES

| Sub-family | Item | Definition | Programs | Detection signature |
|---|---|---|---|---|
| **Systems** | **Dribble-drive motion** | See F4.2 `[O41]` | Memphis (Calipari), Pepperdine (Walberg) `[O41]` | — |
| | **Pace-and-space shot diet** | Rim + three ≈ 92% of FGA. Threes come from collapsing the defense ("shrink threes") `[O42]` | Alabama (Oats) `[O42]` | See F4.2 |
| | **Rim-pressure/backdoor (MSU 2025-26)** | Offense built on Fears' penetration, Carr back-door dunks and kick-out threes `[O56]` | **[MSU]** `[O56]` | DRIVE by the PG, followed ≤ 1 s by a weak-side wing cut to r < 2 (backdoor) or a kick to r > 6.75 |
| | **5-out / Delay** | 5-out with the 5 at the top as the hub. Spreading to college as both a secondary break and a half-court set. Trade-off: better shooting but worse OREB and foul drawing `[O57]` | Richmond (Golden at the top), Dayton, BYU examples `[O57]` | — |
| **Concepts** | **Paint touch** | The ball gets into the paint by pass or drive `[O58]` | 12 high-major D-I programs (ShotTracker, 2016-17): no touch/reversal = 0.706 PPP; paint touch only = 1.061; reversals only = 0.937; ≥ 2 reversals + paint touch = 1.189 PPP `[O58]` | PAINT_TOUCH primitive |
| | **Ball reversal** | Ball moves side to side `[O58]` | `[O58]` | Ball x changes sign with \|Δx\| > 6 m in one or more passes |
| | **Drive-and-kick** | Penetrate, draw help, kick to the open shooter `[O41][O86]` | — | DRIVE, then a PASS to r > 6.75 within 1 s of the drive's minimum r |
| | **Drive-and-dish / dump-off** | Pass to a post or dunker when post help comes `[O41]` | — | DRIVE, then a PASS to r < 2.5 |
| | **Lift / drift / fill** | Adjacent perimeter player fills the driver's vacated spot. On a baseline drive the opposite player drops to the weak corner and the post I-cuts to the elbow. On a middle drive the weak side spots up and the low post goes short corner or opposite block `[O86][O24]` | — | Relocation vectors of off-ball players during DRIVE events |
| | **Kick-out three / extra pass** | Pass to a teammate with a better advantage `[O24]` | — | — |
| | **One-more / "make them guard you"** | Attack until the defense commits `[O29b]` | — | — |

---

## F11. ZONE OFFENSE

### 11.1 Principles (all zones)

| Principle | Definition | Sources | Detection signature |
|---|---|---|---|
| **Front matching** | Use an odd front (one guard) vs even-front zones (2-3, 2-1-2) and an even front (two guards) vs odd-front zones (1-2-2, 1-3-1, 3-2) `[O24]` | `[O24][O33][O60]` | Count offensive players at r > 6.5 with θ 60–120°. Compare to the defenders in the same band |
| **Gap attack** | Dribble into the seam between two zone defenders `[O29][O29b][O33]` | — | DRIVE path passes between two defenders > 3 m apart at the start |
| **Ball reversal / skip** | Shift the zone, then skip to the over-shifted side. A fake skip followed by a lob to the weak block counters a zone that jumps the skip `[O29]` | `[O29][O29b][O33][O60]` | Skip-pass rate; lob to the weak-side block after a pass fake |
| **High-post flash** | Get the ball to the middle of the zone. The high post faces, then shoots or passes quickly; the low post ducks under `[O29][O29b]` | — | Catch at r 3.5–5, θ 70–110 by a player who arrived from r < 3 or from the wing ≤ 1.5 s earlier |
| **Short corner** | Post outlet behind the zone at the short corner; short corner to short corner along the baseline `[O29][O60b]` | — | Player at r 3.5–5.5, θ ≤ 15° or ≥ 165°, receiving passes |
| **Baseline runner** | A shooter runs the baseline corner to corner under the zone `[O29][O29b][O33][O60b]` | Izzo Special-2 `[S12]` | Player crosses x = 0 at y < 0.5 and arrives in the opposite corner ≤ 3 s |
| **Overload** | More attackers than defenders on one side `[O29b][O33][O60]` | — | ≥ 4 offensive players with the same sign(x), or 3 on one side vs 2 defenders |
| **Screening the zone** | Screen the middle or low defender so it cannot rotate; screen "areas, not men" vs match-up `[O29][O61]` | Izzo Special: the 5 screens the low outside defender `[S12]` | SCREEN where the screened player is a zone defender who is not the cutter's matched defender (zone label from the defense model) |
| **Ball screen vs zone / slip into the gap** | Ball screens and down screens work like man; the screener slips into the gap `[O33]` | — | — |
| **One post-touch rule** | Get it inside once before a set-offense jumper `[O29]` | Coach's Clipboard `[O29]` | — |
| **Crash the glass vs zone** | Zone defenders have no box-out assignment `[O33][O60][O60b]` | — | OREB crash count higher vs zone (F14) |
| **Beat it before it sets** | Transition vs zone `[O29b][O60]` | — | — |

### 11.2 By zone type

| Zone faced | Recommended offensive alignment | Named patterns / actions | Sources |
|---|---|---|---|
| **2-3** | 1-3-1 with wings wider than usual; the high post sits in the gap between the high and low defenders `[O29]`. One-guard front `[O24]` | Reversal, then a wing-to-post entry. Short-corner pass with a dive by the high post. High-post entry with a duck-under. Baseline runner. Screen X5 `[O29]`. Post X cuts, box inbound `[O29b]`. **Izzo "Special" / "Special-2" / "1-3-1 Double" / "Fist" / "Fist Down"** (used vs Syracuse and Florida zones) `[S12][S16][O62]` | `[O29][O29b][S12][S16][O62]` |
| **3-2 / 1-2-2** | 2-guard front (2-1-2) `[O33][O24]` | Corner pass turns the 3-2 into a 2-3. Short corner, baseline drive with a drift pass to the weak corner. High-post playmaker. Baseline corner-to-corner runner. Skip. Ball screens with a slip `[O33]` | `[O33]` |
| **1-3-1** | Even front (2-1-2 or 2-3) to split the "chaser"; "Corners" 4-out set `[O60][O60b]` | Reverse before the chaser commits. Overload with four. Short-corner players screen the "warrior" (baseline defender). Skip vs the warrior's long recovery. Lob to the weak block. Screen the chaser after reversal `[O60]`. Zone-2 runner, Corners, "4", "45", "22", "Gold" sets `[O60b]` | `[O60][O60b]` |
| **Match-up zone** | Spread; motion rather than patterns `[O61]` | Screen areas so one defender guards two players. Attack the weak side with flares over the top. Seal or slip after screening. Reverse by pass rather than dribble `[O61]`; man-offense cutting, high-post guard flash `[S63]` | `[O61][S63]` |
| **Junk (box-and-1, triangle-and-2)** | Normal offense | See first-pass §1.8 `[S64]` | `[S64]` |

**Zone-offense detection signature [HEURISTIC]:** zone vs man comes from the defense layer (the defenders' spatial stability relative to the ball versus to their matchups). Given a zone, label offensive actions by front matching, the gap-attack rate, short-corner occupancy, a high-post catch, a baseline runner and skips.

---

## F12. PRESS OFFENSE / PRESS BREAK

### 12.1 Principles

| Principle | Definition | Sources | Detection signature |
|---|---|---|---|
| **Attack, don't just advance** | The goal is a 2v1 or 3v2 layup, not merely crossing half-court `[O63]` | `[O63]` | Shot ≤ 4 s after crossing half-court following a beaten press |
| **Quick inbound by a designated big** | The same post inbounds every time, before the press sets `[O64]` | `[O64]` | Same inbounder across possessions after makes; inbound ≤ 2 s |
| **Safety behind the ball** | One player (O3) always behind the ball for the pass back; also a safety outlet for the inbounder `[O63][O65]` | `[O63][O65]` | ≥ 1 offensive player with y > y_ball (closer to the own baseline) whenever the ball is in the backcourt |
| **Middle first, then sideline** | Look middle first; if denied, sideline. Pass-fake the defender straddling both `[O64]` | `[O64]` | First pass after the inbound goes to \|x\| < 3 |
| **Receivers move toward the ball** | Pass only to players coming to the ball. Don't dribble into traps head-down `[O64][O64b]` | `[O64][O64b]` | Receiver velocity has a component toward the passer at the catch |
| **Sideline receiver at mid-court** | Keep a ball-side sideline receiver near half-court (the weak spot of the 1-2-1-1) `[O64]` | `[O64]` | Player at \|x\| > 6, y ≈ 12–14 (own half) |
| **Reverse when trapped** | Reverse to the inbounder or the trailing safety `[O63][O64]` | — | Backward pass (Δy toward the own baseline) during a trap (two defenders within 2 m of the ball) |

### 12.2 Named press breaks

| Break | Vs | Alignment | Sequence | Source | Detection signature |
|---|---|---|---|---|---|
| **"80"** | 1-2-1-1 full court | O3 inbounds; O1 comes to the ball; O2 and O4 just inside half-court on the sidelines; O5 long `[O63]` | Long sideline pass first, then a corner catch by the 1, the 4 to the middle, the 2 up the sideline. If the 1 is denied: sideline sprints and the 1 cuts up the middle. Reversal through the 3 `[O63]` | Coach's Clipboard `[O63]` | Two players at \|x\| ≈ 6.5–7.5 near half-court plus one deep at the far end at the inbound |
| **"60"** | 2-2-1 (no inbound pressure) | Same | The 4 sits in the middle of the defenders' box. Over-the-top and deep options; back-cuts if denied `[O63]` | `[O63]` | Middle flasher at x ≈ 0 between four defenders |
| **"3-Thru"** | Denial press ("61") | — | 2 and 4 run the sidelines; the 1 stays back; the 3 cuts up the middle `[O63]` | `[O63]` | — |
| **"40"** | 1-2-2 half-court trap | O5 deep, O2 up the sideline, O1 with the ball, O3 trailing opposite, O4 in the middle `[O63]` | The 1 draws, back-dribbles, swings to the 3; the 5 cuts to the ball-side arc; the 4 dives `[O63]` | `[O63]` | Back-dribble then a swing pass at half-court, then a middle dive |
| **Diamond attack (1-2-2 set)** | 1-2-1-1 | Two guards stacked or side by side at the FT line, two at half-court on the sidelines, big inbounds `[O64]` | Best ball-handler catches; the middle receiver pivots to the sideline cutters `[O64]` | `[O64]` | — |
| **4-Across** | 2-2-1 | Four across the front; O2 screens for O1; O3 and O4 on the sidelines `[O65]` | Inbound up the side to the 3, who comes back to meet the trap. The 1 flashes middle, then the opposite sideline (4) or the 2 up the left. The 5 is the safety `[O65]` | `[O65]` | Four players in a horizontal line at y ≈ (own-half) FT line at the inbound |
| **Triangle (late game)** | Pressure when you need the FT shooter to catch | The 2 (best FT shooter) catches off a double screen by the 1 and the 4; the screeners seal and roll `[O63]` | — | `[O63]` | Double screen in the backcourt for one receiver ≤ 1 s after the official hands over the ball |
| **Secondary break as press-break** | — | — | Flow into the secondary break `[O64]` | `[O64]` | — |
| **MSU press break** | — | **[UNVERIFIED]**: no opened source | — | — | — |

---

## F13. SPECIAL SITUATIONS

### 13.1 ATO

| Item | Definition | Programs | Detection signature |
|---|---|---|---|
| **ATO** | After-timeout play to score quickly `[O24]` | MSU Zipper ATO, Down Screen DHO Veer ATO, DHO Clear Lob `[S29c][S23][S29d]` | Possession start follows a timeout (play-by-play) |
| **ATO categories** | Shooter ATOs, post-up ATOs, PnR ATOs; late-clock philosophy (course outline) `[O66]` | `[O66]` | — |
| **Live-ball timeout window** | NCAA allows live-ball timeouts in the last 2 minutes of the second half and of each overtime (since 2019-20) `[O26]` | — | Flag possessions after a live-ball timeout |
| **No advance after timeout** | NCAA men's teams cannot advance the ball to the frontcourt after a timeout; it is the top requested rule change among 100+ D-I coaches (28%) `[O67]`. Not in the 2025-26 approved changes `[O68]` | — | Late-game ATOs after a backcourt possession start from a backcourt inbound (affects templates) |

### 13.2 BLOB (baseline out of bounds)

Inbound spot: on the end line 3 ft (0.91 m) outside the lane if the stoppage was between the corner and the lane/FT-line intersection `[O27]`.

| Alignment | Named play | Sequence | Source | Detection signature |
|---|---|---|---|---|
| **Box** | Cross | 5 cross-screens 4 and 3 cross-screens 1; the screeners fill `[O28b]` | `[O28b]` | Box snapshot with the ball OOB at y < −1.6. Two CROSS screens ≤ 1 s after the official's handover |
| | Up | Two simultaneous up (back) screens from the low players `[O28b]` | `[O28b]` | — |
| | Diagonal | 4 screens 3, then 5 diagonal-screens 1 and dives `[O28b]` | `[O28b]` | — |
| | Up Screener / Diagonal Screener | STS variants. Key: 4 screens the defender of the opposite block `[O28b]` | `[O28b]` | — |
| | Fake Diagonal | 4 fakes the screen and rolls; 5 screens 3 for a mid-range shot `[O28b]` | `[O28b]` | — |
| | Lane screen corner cut / Back screen / Elevator / Elevator + stagger / corner ball screen | `[O28]` | `[O28]` | — |
| | Box Double Down / Screen the Screener | — | **[MSU]** `[S12]` | — |
| **Stack (single)** | Stack 1 split, Stack 3 triple screen to the short corner, Stack 6, Stack Rub | Shooters split from the stack; slip into the vacated space; triple screen; rub off a screen on X5 `[O28c]` | `[O28c]` | ≥ 3 players stacked in a vertical line (\|Δx\| < 1 m) at the set |
| **Double stack** | Stack 2 | Posts on both blocks with guards behind them; the 4 cross-screens the 5; guards V-cut to the corners `[O28c]` | `[O28c]`; vertical stack and double stack variants `[O28]` | Two pairs at the blocks |
| **Line** | — | Four in a line on the lane line | **[MSU]** Screen the Inbounder `[S12]` | — |
| **Diamond / 1-3-1** | — | [CONVENTION]; no opened source describes a diamond BLOB in detail | — | — |
| **vs 2-3 zone** | Box inbound | 4 and 5 cross into the low post and the guards cut to the corners to overload the back three `[O28][O29b]` | `[O28][O29b]` | — |
| **Twist BLOB** | — | — | **[MSU]** `[S25]` | — |
| **STS ATO BLOB** | — | — | **[MSU]** `[S29]` [title only] | — |

### 13.3 SLOB (sideline out of bounds)

The NCAA frontcourt throw-in is at the 28-ft mark on the nearer sideline when the stoppage is outside the BLOB zone `[O27]`.

| Pattern | Definition | Source | Detection signature |
|---|---|---|---|
| **Down screen / ram → ball screen / Spain** | SLOB example 1 `[O69]` | `[O69]` | Ball OOB at \|x\| ≈ 7.6+, y ≈ 6.9 |
| **Cross + elevator** | SLOB example 2: corner three or post feed `[O69]` | `[O69]` | — |
| **V-cut + back screen** | SLOB example 3 `[O69]` | `[O69]` | — |
| **SLOB Zoom** | Zoom from the elbow `[O50]` | `[O50]` | — |
| **Line-1 / SLOB "1"** | — | **[MSU]** `[S12][S29e]` | — |

### 13.4 End of half / end of game

| Situation | Offensive strategy (sourced) | Detection / labeling |
|---|---|---|
| **2-for-1 (end of half)** | Shoot early to get the last possession. In college, the best time for the first action is about 40–44 s before the end of the half; the gain is about 0.2 points per opportunity, or about 1% win probability `[O70]`. NBA causal estimate: +0.66 points when possession is gained at 35–43 s and the shot comes with ≥ 28 s left `[O71]`. FIBA: two quick actions with < 1 minute left `[O24]` | Possession gained with game clock 40–60 s and FGA with game clock ≥ 31 s (≥ 30 s shot clock + 1) → `2for1_attempt` |
| **Last shot (hold for one)** | Hold for the final shot when the game clock < shot clock [CONVENTION] | Game clock ≤ shot clock at possession start and FGA with game clock ≤ 5 s |
| **Down 3** | Going for the tying three is generally better than a quick two `[O72]`. Coaches weigh a quick two plus foul based on the clock (8 s and 5 s thresholds discussed) `[O73]` | Trailing by 3 with < 30 s → label `down3` and record the FGA type |
| **Down 2** | Three to win vs two to tie: with NBA averages, the 3 gives ~25% win vs ~21.5% for the 2 (43% × 50% OT) `[O72]` | — |
| **Up 3 (defense fouls)** | College study (2010–22, 58k games): fouling up 3 is usually best in the final ~12 s; avoid fouling when the shot clock is < 3 s; recommended policy gain is about +1.6 percentage points `[O74]` | Offense label: `fouled_while_down3` |
| **Down 1 / tie** | **[UNVERIFIED]** No opened source gives a D-I-specific offensive rule; convention is a high PnR or iso for the best player with time for a putback [CONVENTION] | — |
| **Intentional FT miss** | When ahead by 3 late, miss on purpose to force a rebound with time expiring `[O73]` | FT trajectory hits the rim with the lane occupied (outcome layer) |
| **Keep-away / clock kill** | Practice keep-away avoiding fouls on the handler `[O73]` | — |

### 13.5 Late clock (shot clock ≤ ~7–10 s)

| Item | Definition | Source | Detection signature |
|---|---|---|---|
| **End-of-clock mode switch** | Teams switch to "end" mode at about 12, 10 or fewer seconds. Keep a working action going, or abort to a set piece. Defaults are PnR/pop or a clear-out; use 2–3 ball-handlers to save time `[O75]` | `[O75]` | Action starts at shot clock ≤ 10 s, where the prior action ended without a paint touch |
| **End-of-clock quick hitters** | Izzo teaches dedicated EOC quick hitters | **[MSU]** `[S6]` | — |
| **Shot-clock reset rules** | 20 s after an OREB that hit the rim (2019-20 onward) `[O26]`; frontcourt inbound after a defensive foul resets to 20 if fewer remain `[O27]` | `[O26][O27]` | Re-segment the "late clock" label after a reset |

### 13.6 Free-throw alignments

| Item | Definition | Source | Detection signature |
|---|---|---|---|
| **Lane occupancy** | Marked lane spaces: max 4 defensive and 2 offensive players `[O76]` (ruleset not named in source; **[UNVERIFIED for NCAA]**) | `[O76]` | At the FT event, offensive players at the 2nd lane spaces (y ≈ 0.3–1.2, \|x\| ≈ 2.1) |
| **Free-throw break (push)** | Strongest rebounders on the baseline spaces. The 2 boxes out the shooter. The 1 and 3 on the arc anticipate the push. After a make the 4 inbounds to the 1; after a miss the 5 outlets to the 1 while the 4 runs. The 2 and 3 release to the outside lanes `[O77]` | `[O77]` | — |
| **Missed-FT offensive play** | Late game, intentional miss plus tip-out (see 13.4) | `[O73]` | — |

### 13.7 Jump ball

| Item | Definition | Source | Detection signature |
|---|---|---|---|
| **Tip play** | Best jumper at the centre. Strong post on the offensive side of the circle. Two quick players at half-court on opposite sides release as the ball goes up. One stays back; the 5 trails. Tip forward for a 2v1 `[O78]` | `[O78]` | Jump-ball event, then two players accelerating to y < 5 within 2 s |
| **Possession arrow** | NCAA uses the alternating possession arrow after the opening tip [CONVENTION] | — | — |

### 13.8 Delay / clock-kill

| Item | Definition | Source | Detection signature |
|---|---|---|---|
| **Four corners** | Four players in the corners of the half-court with the 5th dribbling in the middle. Back-cuts or PG drives; only very safe shots. Created by John McLendon (NC Central) by the early 1950s, popularized by Dean Smith (UNC). The 1985 national shot clock made pure stalling obsolete `[O79]` | `[O79]` | Four players at r > 7 near the corners and wings; the handler at the top dribbling ≥ 5 s with no screens |
| **Delay offense (FIBA)** | Takes more time on each possession `[O24]` | `[O24]` | Possession duration > shot clock − 5 s with low action density |
| **Spread to run clock** | 5-out keep-away, late with a lead | [CONVENTION] | — |

---

## F14. OFFENSIVE REBOUNDING SYSTEMS

| Item | Definition | Programs / evidence | Detection signature |
|---|---|---|---|
| **Crash count** | Number of offensive players moving toward the rim when the shot is released | MSU handout: send 4 to the glass; the PG gets back `[O80]`. Pacers (NBA): 3 crash (both bigs + the weak-side baseline wing), the other wing retreats; MIT tracking measured 2/3/4 crashers `[O81]` | Count offensive players whose rim-ward velocity is > 1 m/s within 0.5 s after the release and who reach r < 4 before the ball hits the rim. SkillCorner's crash classifier reached ~97% agreement on one game `[O82]` |
| **Safety / get-back** | Player(s) assigned to retreat | MSU: PG back `[O80]`. Pacers: one wing `[O81]` | Offensive player moving toward its own basket (+y) > 2 m/s within 1 s of the release |
| **Hit, Find, Fetch** | MSU rebounding mantra: make contact, find the ball, rebound it out of the air `[O80][S1]` | **[MSU]** | — |
| **Tip / keep it alive** | If you can't secure it, tip to a teammate or keep it alive `[O80]` | MSU `[O80]`; Houston tracks "tips" with a goal of 25–30 per game `[O45]` | Ball touched above 3 m by an offensive player without possession, followed by a teammate's control ≤ 1.5 s |
| **Opposite-side rule** | About 70% of rebounds go opposite the shot side `[O80]` | MSU handout `[O80]` | Weak-side crash bias: position crashers at sign(x) ≠ sign(x_shot) |
| **Weak-side rebounder on early shots** | Always a big at the weak-side rebound spot `[O5]` | Oregon Tech `[O5]` | — |
| **Guards crash** | Guards are among the leading rebounders by design `[O45]` | Houston (Sampson) `[O45]` | Guard crash rate ≥ 40% of missed FGA |
| **Already inside** | Elite offensive rebounders are usually already inside at the release rather than crashing from the perimeter. Spacing matters: one-game samples had 2.6–3.6 players on the perimeter at the release `[O83]` | `[O83]` | Count players at r > 6.75 at the release |
| **Corner shooter loop** | Corner shooters loop toward the FT line and decide mid-way whether to crash `[O81]` | Pacers `[O81]` | — |
| **Offense controls OR%** | About 73% of OR% variance is controlled by the offense (2006–15); national OR% fell from 34.0% to 31.1% over that span `[O84]` | `[O84]` | — |
| **Crash vs transition D tradeoff** | College: both aggressive crashers and retreaters allow fewer transition chances than moderate crashers (~1 pp) `[O85]` | `[O85]` | — |
| **5-out penalty** | 5-out spacing tends to reduce OREB and foul drawing `[O57]` | `[O57]` | — |
| **MSU OREB profile** | 1st in Big Ten OR% (2024-25 conference play) `[S83]`; Kohler led the Big Ten in OR% (16.6%) in 2024-25 `[O56b]`; 37.1% OR in 2025-26 Big Ten play `[S87]` | **[MSU]** | — |

---

## F15. SPACING SYSTEMS AND COURT-GEOMETRY CONVENTIONS

| Item | Definition | Source | Metric template / detection |
|---|---|---|---|
| **Perimeter spacing distance** | Perimeter players about 12–15 ft (3.7–4.6 m) apart, above the arc unless cutting or screening `[O86]` | `[O86]` | Mean nearest-teammate distance among perimeter players: alert if < 3.5 m |
| **Spots** | Slot, wing, corner, top, dunker, short corner, elbow, nail | First-pass §0; §0.1 here | §0.1 |
| **5-out** | All five outside the arc; guards enter only to cut; bigs roll then return to the slot `[O57]` | `[O57]` | Five players at r > 6.6 |
| **4-out 1-in** | Post low (weak-side short corner or block) or high (FT line) `[O86]`; Villanova 5 at the weak-side dunker `[O13]` | `[O86][O13]` | — |
| **3-out 2-in** | Posts interchange among the blocks, high post and short corners `[O86]` | `[O86]` | — |
| **1-4** | Clears the basket area `[O86]` | `[O86]` | — |
| **Empty side / empty corner** | No player on the ball-side wing/corner during a side action `[S55][O24]` | — | — |
| **Dunker spot occupancy** | — | — | Player at r 2.4–3.6, θ 5–25° |
| **Slide / Shake / Lift / Drift** | Spacing reactions to PnR or drives `[O24]` | `[O24]` | F5.6 |
| **Hi-lo post spacing** | Opposite posts screen for each other and work hi-lo `[O86]` | `[O86]` | — |
| **Spacing index (tracking)** | [HEURISTIC] Convex-hull area of the 5 offensive players; mean pairwise distance; number of players beyond the arc at the release | — | Hull area > 70 m² typical of 5-out [UNVERIFIED threshold] |

---

## F16. EUROPEAN / NBA VOCABULARY ↔ COLLEGE TERMS

| European / NBA term | Meaning | Common college equivalent | Source |
|---|---|---|---|
| **Spain / Stack / Bamberg** | PnR plus a back screen on the roller's defender | "Spain" (same) | `[S19][O24][O21]` |
| **Chicago / Zoom** | Pin-down → DHO | "Zoom", "Chicago" | `[O24][O21][O50]` |
| **Get / Chase / Throw-and-go** | Pass and follow for the handoff | "Get", "Chase" | `[O49]` |
| **Miami** | DHO → PnR | "DHO into ball screen" | `[O11]` |
| **Ram** | Off-ball screen for the screener before the ball screen | "Ram" | `[O24][O21]` |
| **Wedge** | A guard screens the big who then ball-screens (FIBA). CelticsBlog: a diagonal screen into the post | Ambiguous; record both senses | `[O24][O21]` |
| **Veer** | Ball screen → wide pin-down by the same screener | "Veer" | `[O24]` |
| **Twist** | Two ball screens from opposite directions | "Twist" | `[O24][O12]` |
| **Gortat / Hostage** | Roller screens the drop big | "Seal" | `[O24]` |
| **Hoiberg roll / Slide** | Weak dunker → strong dunker on the roll | "Dunker swap" | `[O24]` |
| **Shake** | Corner lifts during a side PnR | "Lift" | `[O24]` |
| **Lithuania** | Reversal where the near wing cuts and the far wing receives | — | `[O11]` |
| **Argentina** | Central PnR plus a paint cross screen | — | `[O11]` |
| **Bilbao** | Flare for the post-entry passer plus a weak-side elbow split | — | `[O47]` |
| **Brazilian triple post** | Curl/backdoor near the nail with three posts | — | `[O47]` |
| **Grenade DHO** | Post DHO (name only) | — | `[O47]` |
| **Twirl** | Curl the first stagger, then the first screener comes off the second | — | `[O24]` |
| **Wiper** | Flare then pin-down for the same cutter | — | `[O24]` |
| **Ricky** | Rip then down screen for the same player | — | `[O24][O21]` |
| **Blade** | Cutter goes to the rim during the roll | — | `[O24]` |
| **Blind pig** | Big-to-backdoor three-person action | Princeton "backdoor" | `[O24]` |
| **Stampede / 45 cut** | NBA cut terms | — | `[O21]` |
| **77** | Stagger / double drag | "Double drag" | `[O21][O11]` |
| **Logo screen** | Ball screen far beyond the arc | "Deep" screen | `[O24]` |
| **Gator / Tag&Go** | Reject-and-pass / tag-then-roll | — | `[O11]` |
| **Pistol / 21** | Early wing action | "Pistol" | `[O24][O8]` |
| **Delay** | Big-at-top 5-out | "Delay" | `[O11][O57]` |
| **Chest** | FIBA: chest pass. MSU: a set name | "Chest" (MSU) | `[O24][S26]` |
| **Horns** | FIBA entry name | "Horns" | `[O24]` |
| **Hammer** | Weak-side flare to the corner on a baseline drive | "Hammer" | `[O24]` |
| **Power** | FIBA entry name (no definition found) | — | `[O24]` [UNVERIFIED] |

---

## F17. OUTCOME LAYER: SYNERGY PLAY TYPES

This layer is **orthogonal** to the set taxonomy. Each possession gets one terminal play type based on how it ended (shot, turnover or shooting foul) `[O53]`. Official API codes: Isolation, Transition, PRBallHandler, PRRollman, Postup, Spotup, Handoff, Cut, OffScreen, OffRebound (putbacks), Misc `[O87]`.

| Play type | Definition (paraphrased) | Edge rules | Mapping from this taxonomy | Detection signature |
|---|---|---|---|---|
| **Transition** | Possession where the defense is not set; no shot-clock cutoff `[O53]` | A transition possession where the defense is set by the time of a turnover → Misc `[O53]` | F1, F2 (pre-set phase) | Terminal event before the "defense set" flag (all 5 defenders behind the ball and at r < 9 for ≥ 1 s) |
| **PnR Ball-Handler** | Handler finishes off a ball screen (pull-up, floater, rim); includes shots before using the screen and rejects `[O53]` | Passes out of the PnR are credited elsewhere `[O53]` | F5 | Terminal FGA by the handler ≤ 3 s after a ball SCREEN |
| **PnR Roll Man** | Screener scores on a slip, roll or pop `[O53]` | — | F5.4 | Terminal FGA by the screener ≤ 3 s after a SCREEN |
| **Off-Screen** | Player comes off an off-ball screen (pin-down, flare, elevator…) and shoots, pulls up or drives; curls included `[O53]` | **UCLA and flex screens → Cut** `[O53]` | F8 | Terminal FGA ≤ 2 s after the shooter used an off-ball SCREEN that is not UCLA/flex |
| **Hand-Off** | DHO or flip/pitch `[O53]` | — | F6 | Terminal FGA by the DHO receiver ≤ 3 s |
| **Cut** | Basket cuts (backdoor, dump-offs), screen cuts (UCLA, flex), flash cuts `[O53]` | — | F8.2 | Terminal FGA after a CUT ending at r < 3 |
| **Spot-Up** | Catch-and-shoot or catch-and-attack with no screen before the catch; relocation allowed; closeout attacks count `[O53]` | A pass that leads to a spot-up is logged as spot-up `[O53]` | F10 | Terminal FGA by a receiver who used no screen in the prior 3 s |
| **Isolation** | 1-on-1; includes broken actions that become iso `[O53]` | — | F9 | Terminal FGA after ≥ 2 s of holding with no screen |
| **Post-Up** | Back-to-basket or face-up from the post `[O53]` | — | F7 | Terminal FGA by a player who caught at r < 4 with back-to-basket orientation |
| **Putback** | Tip-ins and quick shots after offensive rebounds `[O53]` | NBA.com has Misc and Putback data reversed `[O53]` | F14 | FGA ≤ 2 s after an OREB, at r < 3 |
| **Misc** | Everything else: deflection oddities, backcourt and illegal-screen fouls, passer turnovers not in another action, half-court pull-up threes off the dribble, inbounds straight out of bounds `[O53]` | — | — | Residual |

**Possessions logged:** only those ending in a shot, turnover or shooting foul `[O53]`.

---

## F18. MICHIGAN STATE ADDENDUM (new sets found in this pass + family map)

### 18.1 Newly documented MSU sets (not in first-pass §3.2)

| Set | Year / source | Family | Ordered actions | Options | Detection cues [HEURISTIC] |
|---|---|---|---|---|---|
| **DHO PNR Reject Pin** | FastModel, Mar 2024 `[O88]` | F6 → F5 | 1→4. 4 DHOs to 2, then cuts to the rim. 5 ball-screens 2. **2 rejects**. 4 loops weak side and screens for 1 (flare-type) `[O88]` | Main read is the reject; 1's helper leaves → screen for 1 `[O88]` | DHO, then a ball SCREEN on the same receiver ≤ 2 s, handler heading away from the screener (reject), then a weak-side SCREEN by the DHO-giver |
| **EOQ Horns Set** | FastModel, Mar 2024 `[O89]` | F3 Horns / F13.4 | 4 and 5 cross, each setting a ball screen for 1. 1 picks a side. The used screener rolls and the other pops `[O89]` | Choice of screen `[O89]` | Horns, then the elbow bigs swap sides (cross) ≤ 1.5 s, then a ball screen with a roll/pop split. Game clock ≤ shot clock |
| **21 Pin Chin (ATO)** | FastModel, Apr 2019 `[O90]` | F2.2 Pistol / F13.1 | DHO on the wing ("21"), weak-side pin-down, reversal, the PG clears the corner, chin screen for the wing → lob `[O90]` | Taller athlete on the lob end `[O90]` | Wing DHO at r ≈ 7, θ 30–50 within 3 s of the ATO inbound. Reversal. Back screen at the elbow/slot, then a lob to r < 1.5 |
| **Miami Comeback** | FastModel, Mar 2022 (2021-22) `[O91]` | F6 Miami | 1 dribbles to the side as 4 sets a turnout screen for 3 and 5 back-screens 2. 5 pins for 2, who catches. Miami (DHO→PnR) with 5. 5 sets a "comeback" screen for 2 `[O91]` | Two shot options `[O91]` | DHO then ball screen by the same big, then that big re-screens the original handler from the opposite direction |
| **Double Fan** | 2012 (Izzo for Adreian Payne); FastModel 2015 `[O92]` | F5 double ball screen → F8 flare | Double ball screen by 4+5; they continue into a second double screen for 1; 5 flares for 4 for a quick shot `[O92]` | Stretch-4 shot `[O92]` | Two bigs side by side (< 1.2 m) screening twice in sequence, then big-for-big flare (the cutter ends at r > 6.75) |
| **1-4 High Curl Double Flare** | FastModel 2016 (vs Florida) `[O93]` | F3 1-4 high → F8 stagger/flare | 1→4 at the high post, 2 back-cuts, 1 screens for 5 at the left elbow, 5 posts, 1 pops, 3 comes off the 5+4 stagger. Secondary: 1 flares off 5 `[O93]` | — | 1-4 high snapshot, high-post catch, guard down-screens an elbow big, stagger by two bigs for a wing |
| **Spartan Re-Screen** | FastModel 2016 `[O94]` | F8 flare/down "wiper" | 1 DHOs to 2 while 4 down-screens 3. 2→3, then 2 uses 5's flare, curls, and reverses off a down screen from 5 (a re-screen). Alternative: back screen, then a fake screen and re-screen `[O94]` | — | Same cutter uses a flare and a down screen by the same screener ≤ 3 s (wiper/re-screen) |
| **SLOB Corner** | FastModel 2015 (NCAA vs Georgia) `[O95]` | F13.3 SLOB | 1 sets a zipper screen. 4 looks for an elbow catch. 3 down-screens for 1 after the inbound. 4 passes and follows, or DHOs to 1. 2 and 5 flare for 1 off a ball screen `[O95]` | Flare for 2 `[O95]` | SLOB with an elbow catch by the 4, then DHO/flare |
| **Wizard (SLOB)** | FastModel 2015 `[O96]` | F13.3 SLOB | 5 feigns disinterest. On the ball slap, 2 and 4 screen for 1 and 5 flashes. 3→5. 2 cuts to the rim; 3 sprints past his turning defender; 5 hits 2 or 3 `[O96]` | Athletic 5 can rip-and-drive; full- or half-court `[O96]` | Flash to the ball by the biggest player ≤ 1 s after the official's handover, then two basket cuts |

### 18.2 MSU usage across families (where documented)

| Family | Documented MSU usage | Keys |
|---|---|---|
| F1 Transition | Push off makes and misses; diagonal dribble; pass before the timeline; shooting trailer pitch-back | `[O30][O31][S9]` |
| F2 Secondary | DHO + weak-side down screen; Rip to Mid Screen Iso; 21 Pin Chin | `[S11][O90]` |
| F3 Alignments | Horns (Rip, Rip Away, Quick Screen, Chin, EOQ), 1-4 high, Box, Stack, 4-high Iverson, Chest | `[S12][S24b][S28][S29g][O89][O93]` |
| F5 Ball screen | Detroit (double), Double Fan, sprint-up, back-screen PnR, DHO PNR Reject Pin, Kohler pick-and-pop | `[S12][S17][S18][O88][O92][S89]` |
| F6 Handoff | DHO Clear Lob, Miami Comeback, MSU secondary DHO | `[S29d][O91][S11]` |
| F7 Post | ISO-3/4/5, Chest high-low, pinch post / short corner / deep seal | `[S12][S26][S27]` |
| F8 Off-ball | Hawk, STS, Over-Under, Iverson Stagger Hit, Spartan Re-Screen, Veer | `[S29b][S12b][S29h][O94][S23]` |
| F10 Spread/drive | 2025-26 rim pressure, backdoors for Carr, kick-outs | `[O56]` |
| F11 Zone | 1-3-1 Special/Special-2/Double/Fist/Fist Down vs 2-3 | `[S12][S16][O62]` |
| F12 Press break | **[UNVERIFIED]** | — |
| F13 Special | Zipper ATO, Veer ATO, DHO Clear Lob, 21 Pin Chin ATO, EOQ Horns, Screen the Inbounder, Twist BLOB, Line-1, SLOB "1", SLOB Corner, Wizard | `[S29c][S23][S29d][O90][O89][S12][S25][S29e][O95][O96]` |
| F14 OREB | Send 4, PG back; hit-find-fetch; tip it alive; ~70% opposite side | `[O80][S1]` |

---

## Summary counts (this file)

- **Families:** 18 (F1–F17 as requested, plus the F18 MSU addendum).
- **Sub-families:** 55. These are the 41 numbered sub-sections, plus 8 internal groupings in the F7 and F10 tables, plus 6 families that consist of a single table (F6, F9, F14, F15, F16, F17).
- **Named rows:** 419 bold-named table rows covering sets, actions, variants, reads, spacing tags, rules and play types. Alignment geometry is restated in metric form, but first-pass §3.2 MSU sets are not duplicated.

---

## Sources (URLs opened for this file; `[S#]` keys resolve in `/home/claude/set_taxonomy.md`)

- **O1**: Breakthrough Basketball, "Fast Break Basketball Offense – Carolina Secondary Break". https://www.breakthroughbasketball.com/offense/fast-break-offense-carolina.html
- **O2**: Hoopscoop (B. Farquhar), "Roy Williams Transition Offense". https://www.mensbasketballhoopscoop.com/roy-williams-transition-offense/
- **O3**: Coaching Toolbox, "Roy Williams on Transition Offense". https://coachingtoolbox.net/blog/roy-williams-on-transition-offense
- **O4**: HoopStudent, "Numbered fast break". https://hoopstudent.com/numbered-fast-break/
- **O5**: Breakthrough Basketball, "15 Keys To A High-Scoring Fast Break" (Danny Miles). https://www.breakthroughbasketball.com/offense/15-keys-fast-break
- **O6**: Coach's Clipboard, "Secondary Break 3". https://www.coachesclipboard.net/SecondaryBreak3.html
- **O7**: Coach's Clipboard, "Secondary 3-Up Break". https://www.coachesclipboard.net/Secondary3UpBreak.html
- **O8**: Coach's Clipboard, "Pistol Action Basketball Plays". https://www.coachesclipboard.net/pistol-action-basketball-plays.html
- **O9**: Squared Statistics (J. Gallagher), "Pistol: Disrupting the Defense" (2018). https://squared2020.com/2018/10/10/pistol-disrupting-the-defense/
- **O10**: Hooper University, "Understanding the 'Pistols' Offense". https://hooperuniversity.com/breakdowns/the-hurry-up-offense
- **O11**: Pere Purrà, "1) Early Offense" (Substack, Jan 2025). https://pere.substack.com/p/1-early-offense (same as S43)
- **O12**: The Hoops Geek, "The Complete Guide to Horns Offense". https://www.thehoopsgeek.com/basketball-horns-offense/
- **O13**: Hooper University, "Villanova's 4 Out 1 In Motion Offense". https://www.hooperuniversity.com/breakdowns/villanovas-4-out-motion-offense
- **O14**: MGoBlog, "Scouting The Enemy: UConn Offense". https://mgoblog.com/content/scouting-enemy-uconn-offense
- **O15**: Hoop Vision, "5-Out Offensive Concepts (HV Weekly 6/19/2020)"; "The Auburn Flex (HV Weekly 1/14/22)". https://hoopvision.substack.com/p/5-out-offensive-concepts-hv-weekly ; https://hoopvision.substack.com/p/the-auburn-flex-hv-weekly-11422
- **O16**: Skarrgozags (Substack), "The Evolution of Gonzaga's Offense". https://skarrgozags.substack.com/p/the-evolution-of-gonzagas-offense
- **O17**: FastModel, "Kansas Jayhawks High-Low Offense (Weakside Cut)". https://fastmodelsports.com/library/basketball/fastdraw/67183/play-Kansas-Jayhawks-High-Low-Offense-Weakside-Cut-
- **O18**: FastModel, "Kansas 'Wing Entry-Strongside'". https://playbank.fastmodelsports.com/library/basketball/fastdraw/112384/play-Kansas-Wing-Entry-Strongside-
- **O19**: Coach's Clipboard (J. Gels), "UCLA Offense". https://coachesclipboard.net/UCLAOffense.html
- **O20**: "Using Hex Maps to Classify & Cluster Dribble Hand-off Variants in the NBA" (PDF). https://global-uploads.webflow.com/5f1af76ed86d6771ad48324b/622770e864911f5635f56f75_Using%20Hex%20Maps%20to%20Classify%20%20Cluster%20Dribble%20Hand-off%20Variants%20in%20the%20NBA%202.pdf
- **O21**: CelticsBlog, "A glossary of Xs and Os terms" (Dec 2023). https://www.celticsblog.com/2023/12/31/23995553/a-glossary-of-xs-and-os-terms-boston-celtics-joe-mazzulla (same as S21)
- **O22**: HoopStudent, "Basketball dribble handoff". https://hoopstudent.com/basketball-dribble-handoff/
- **O24**: FIBA Europe, *Basketball Terminology* (Di Matteo & Schwarz). https://assets.fiba.basketball/image/upload/documents-corporate-regional-offices-europe-programs-fiba-europe-coaching-certificate-fiba-europe-basketball-terminology.pdf (same as S20)
- **O25**: Basketball for Coaches, "17 Basketball Screens All Players and Coaches Must Know". https://www.basketballforcoaches.com/basketball-screens/
- **O26**: Saturday Down South, "3-point line extended, other changes … 2019-20". https://www.saturdaydownsouth.com/news/college-football/3-point-line-extended-other-changes-coming-to-college-basketball-in-2019-20-season/
- **O27**: Tulane Athletics, "NCAA Men's Basketball Rules Committee approves 2017-18 rule changes". https://tulanegreenwave.com/news/2017/6/15/ncaa-mens-basketball-rules-committee-approves-2017-18-rule-changes
- **O28**: HoopStudent, "Baseline out of bounds plays". https://hoopstudent.com/baseline-out-of-bounds-plays/
- **O28b**: Breakthrough Basketball, "6 Baseline Out Of Bounds Plays From The Box Set". https://www.breakthroughbasketball.com/plays/baseline-box-plays
- **O28c**: Coach's Clipboard, "'Stack' Baseline Out-of-bounds Plays". https://coachesclipboard.net/OBStackPlays.html
- **O29**: Coach's Clipboard, "Zone-23" 2-3 zone offense. https://www.coachesclipboard.net/23ZoneOffense.html
- **O29b**: The Hoops Geek, "How to Beat a 2-3 Zone Defense". https://www.thehoopsgeek.com/how-to-beat-2-3-zone-defense (same as S59)
- **O30**: FastModel, "MSU Transition". https://playbank.fastmodelsports.com/library/basketball/fastdraw/363514/play-MSU-Transition (same as S10)
- **O31**: The State News (Nov 2021), MSU fast break revamped. https://statenews.com/article/2021/11/msu-basketball-2021-fast-break-revamped (same as S8)
- **O32**: Coach's Clipboard, "Michigan State Progressive Transition Drill". https://www.coachesclipboard.net/MSUTransitionDrill.html
- **O33**: Basketball for Coaches, "How to Beat a 3-2 Zone Defense (17 Strategies)". https://www.basketballforcoaches.com/how-to-beat-a-3-2-zone-defense/
- **O34**: HoopDirt, Bill Self high-low offense article. https://hoopdirt.com/?p=442052
- **O35**: Streaking the Lawn (Mar 2023), Virginia "sides" offense. https://www.streakingthelawn.com/2023/3/4/23619926/uva-basketball-virginia-cavaliers-tony-bennett-offense-sides-isaac-mckneely-kihei-clark
- **O36**: B. Geisinger Substack, "Virginia goes to Inside Triangle offense vs. NC State" (title only, via search). https://briangeisinger.substack.com/p/virginia-goes-to-inside-triangle
- **O37**: Hoop Vision, "The Godfather (HV Weekly 10/30/20)" (Witherspoon continuity ball screen; Creighton). https://hoopvision.substack.com/p/the-godfather-hv-weekly-103020
- **O38**: FastModel, "Chattanooga – Ball Screen Continuity" (title only, via search). https://playbank.fastmodelsports.com/library/basketball/fastdraw/123286/play-Chattanooga--Ball-Screen-Continuity
- **O39**: Half Court Hoops, "Davidson 5-Out Motion Offense" (mostly paywalled). https://halfcourthoops.substack.com/p/davidson-5-out-motion-offense
- **O41**: Breakthrough Basketball, "The High Powered Dribble Drive Motion Offense". https://www.breakthroughbasketball.com/offense/dribble-drive-motion-offense.html
- **O42**: Sports Illustrated (Feb 2024), "Can Alabama Men's Basketball's Supercharged Offense Lead to a National Championship?" https://www.si.com/college/2024/02/23/can-alabama-mens-basketballs-supercharged-offense-lead-to-a-national-championship
- **O43**: Hammer & Rails, "Purdue Basketball: It's Time to Work the Jab". https://www.hammerandrails.com/mens-basketball/57882/purdue-basketball-its-time-to-work-the-jab
- **O44**: PaperCity, Kelvin Sampson/Houston offense vs Baylor (2025). https://www.papercitymag.com/culture/kelvin-sampson-houston-baylor-blitz-offense-underrated-milos-uzan/
- **O45**: The Daily Cougar (Jan 2020), Houston rebounding guards. https://thedailycougar.com/2020/01/29/houston-rebounding-guards/
- **O46**: Hooper University, "Ball Screen Offense—The Rules & Basics". https://hooperuniversity.com/breakdowns/ball-screen-offense-the-rules-and-basics
- **O47**: Slappin' Glass, "European Post Actions: A Primer". https://slappinglass.substack.com/p/european-post-actions-a-primer
- **O48**: Sportplan, "Pick and Roll Mastery: Modern Ball Screen Offense" (2025). https://www.sportplan.net/drills/Basketball/trends/pick-and-roll-mastery-2025-01.jsp
- **O49**: Hooper University, "The Popular 'Get' Action Explained". https://hooperuniversity.com/breakdowns/get-action-explained
- **O50**: The Hoops Geek, "Zoom Action". https://www.thehoopsgeek.com/basketball-zoom-action
- **O51**: HoopStudent, "Basketball split cut". https://hoopstudent.com/basketball-split-cut/
- **O52**: Basketball for Coaches, "What is an Iso in Basketball?". https://www.basketballforcoaches.com/iso-basketball/
- **O53**: Nylon Calculus (FanSided, 2017), "How to understand Synergy play type categories". https://fansided.com/2017/09/08/nylon-calculus-understanding-synergy-play-type-data/ (same as S40)
- **O54**: FastModel, "1-4 Low 3 Iso"; "1-4 Low Push Zip Iso" (titles only, via search). https://playbank.fastmodelsports.com/library/basketball/fastdraw/978/play-1-4-Low-3-Iso
- **O55**: FastModel, "Las Vegas Aces – Pinch Post Series | Elbow Iso" (title only, via search). https://playbank.fastmodelsports.com/library/basketball/fastdraw/290792/play-Las-Vegas-Aces--Pinch-Post-Series--Elbow-Iso
- **O56**: SI (C. Landis, Oct 4 2025), "One Thing MSU Must Do to Keep Offense Efficient". https://www.si.com/college/michiganstate/spartans-basketball-carson-cooper-jeremy-fears-coen-carr-tom-izzo-offense (same as S91)
- **O56b**: Inside the Hall, MSU 2025-26 preview. https://www.insidethehall.com/?p=121207
- **O57**: Hoop Vision, "The Space Race (HV Weekly 6/5/2020)". https://hoopvision.substack.com/p/the-space-race-hv-weekly-652020
- **O58**: ShotTracker, "Ball Reversals or Paint Touches? Use Analytics…". https://shottracker.com/ball-reversals-or-paint-touches-use-analytics-to-learn-what-drives-efficiency-for-your-team/
- **O60**: Basketball for Coaches, "How to Beat a 1-3-1 Zone Defense". https://www.basketballforcoaches.com/?p=9394
- **O60b**: Coach's Clipboard, "1-3-1 Zone Offense". https://www.coachesclipboard.net/131zoneoffense.html
- **O61**: Breakthrough Basketball Q&A (Don Kelbick), attacking the match-up zone. https://www.breakthroughbasketball.com/qa/q1505
- **O62**: Active.com, "Tom Izzo's Unorthodox Attack on Zone Defenses" (Fist Down vs Syracuse/Florida). https://www.active.com/basketball/articles/tom-izzo-s-unorthodox-attack-on-zone-defenses (also opened: https://www.active.com/basketball/articles/tom-izzo-s-breakdown-of-the-1-3-1-special-offense-6 ; https://www.active.com/basketball/articles/video-the-1-3-1-double-with-tom-izzo-f)
- **O63**: Coach's Clipboard, "Basketball Press Offense" (80/60/40/3-Thru/Triangle). https://www.coachesclipboard.net/PressBreakers.html
- **O64**: Coach's Clipboard, "Attacking the Diamond 1-2-1-1 Full Court Press". https://www.coachesclipboard.net/1211PressOffense.html
- **O64b**: Coach's Clipboard (youth), 1-2-1-1 press offense. https://www.coachesclipboard.net/youth/1211PressOffense.html
- **O65**: Coach's Clipboard, "2-2-1 Press Breaker". https://www.coachesclipboard.net/221PressBreaker.html
- **O66**: CoachTube, "5-Out ATOs and Late Clock Philosophy for All Levels". https://coachtube.com/course/basketball/5-out-atos-and-late-clock-philosophy-for-all-levels/18783067
- **O67**: CBS Sports, "Candid Coaches: Which on-court rule change should come next…". https://www.cbssports.com/college-basketball/news/candid-coaches-which-on-court-rule-change-should-come-next-to-mens-college-basketball/
- **O68**: NCAA.org (Jun 10, 2025), "Panel approves changes to enhance the flow of the game in men's basketball". https://www.ncaa.org/news/2025/6/10/media-center-panel-approves-changes-to-enhance-the-flow-of-the-game-in-mens-basketball.aspx
- **O69**: HoopStudent, "Sideline out of bounds plays". https://hoopstudent.com/sideline-out-of-bounds-plays/
- **O70**: KenPom blog, two-for-one analysis. https://kenpom.com/blog/?p=272
- **O71**: arXiv 2412.08840, "The Causal Effect of the Two-For-One Strategy in the NBA". https://arxiv.org/pdf/2412.08840
- **O72**: BestBallStats (Oct 2022), "Foul up 3 or Defend?". https://bestballstats.com/2022/10/12/foul-up-3-or-defend-analyzing-late-game-strategy/
- **O73**: Coaching Toolbox, "Preparing for End of Game Situations". https://coachingtoolbox.net/preparing-for-end-of-game-situations.html
- **O74**: Wharton (Zapata-Hall), "College Basketball Foul-Up-3 Dilemma" (PDF, Dec 2024). https://wsb.wharton.upenn.edu/wp-content/uploads/2024/12/CBBFoulUp3Dilemma_rev-uploaded-121624.pdf
- **O75**: Hoop Coach, end-of-shot-clock offense article. https://www.hoopcoach.org/?p=28311
- **O76**: Officiating.com forum post quoting lane-space rule 8-1-4. https://forum.officiating.com/597346-post3.html
- **O77**: HoopTactics, "Free Throw Break / Early Free Throw Push". https://hooptactics.net/premium/offense/earlyoffense/earlyfreethrowpush.php
- **O78**: Coach's Clipboard, "Tip Play" (jump ball). https://www.coachesclipboard.net/TipPlay.html
- **O79**: Wikipedia, "Four corners offense". https://en.wikipedia.org/wiki/Four_corners_offense
- **O80**: Coaching Toolbox, "Michigan State Rebounding Concepts". https://coachingtoolbox.net/blog/michigan-state-rebounding-concepts
- **O81**: Grantland, "Party Crashers: Debunking the Myths of Offensive Rebounding and Transition Defense". https://grantland.com/the-triangle/party-crashers-debunking-the-myths-of-offensive-rebounding-and-transition-defense/
- **O82**: SkillCorner, "Using tracking & event data … to quantify offensive crashing". https://skillcorner.com/articles/using-tracking-event-data-from-skillcorner-to-quantify-offensive-crashing
- **O83**: Hoop Vision, "Bully Ball (HV Weekly 6/28/2020)". https://hoopvision.substack.com/p/bully-ball-hv-weekly-6282020
- **O84**: KenPom blog, "Offense vs. defense: rebounding". https://kenpom.com/blog/offense-vs-defense-rebounding/
- **O85**: Harvard Sports Analysis Collective (Jan 2017), "College Basketball Teams May Want to Aggressively Crash the Offensive Glass". https://harvardsportsanalysis.org/2017/01/college-basketball-teams-may-want-to-aggresively-crash-the-offensive-glass/
- **O86**: Coach's Clipboard, "Basketball Spacing and Movement – Moving Without the Ball". https://www.coachesclipboard.net/OffBall.html
- **O87**: hoopR reference, `nba_synergyplaytypes` (play_type codes). https://search.r-project.org/CRAN/refmans/hoopR/html/nba_synergyplaytypes.html
- **O88**: FastModel, "Michigan State Spartans – DHO PNR Reject Pin" (Mar 2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461637/play-Michigan-State-Spartans--DHO-PNR-Reject-Pin
- **O89**: FastModel, "Michigan State Spartans – EOQ Horns Set" (Mar 2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461638/play-Michigan-State-Spartans--EOQ-Horns-Set
- **O90**: FastModel, "Michigan State Spartans – 21 Pin Chin" (Apr 2019). https://playbank.fastmodelsports.com/library/basketball/fastdraw/289998/play-Michigan-State-Spartans--21-Pin-Chin
- **O91**: FastModel, "Michigan State Spartans – Miami Comeback" (Mar 2022). https://playbank.fastmodelsports.com/library/basketball/fastdraw/409399/play-Michigan-State-Spartans--Miami-Comeback
- **O92**: FastModel, "Michigan State 'Double Fan'". https://playbank.fastmodelsports.com/library/basketball/fastdraw/80957/play-Michigan-State-Double-Fan-
- **O93**: FastModel, "Michigan State – 1-4 High Curl Double Flare" (2016). https://playbank.fastmodelsports.com/library/basketball/fastdraw/134800/play-Michigan-State--1-4-High-Curl-Double-Flare
- **O94**: FastModel, "Michigan State Spartan Re-Screen" (2016). https://playbank.fastmodelsports.com/library/basketball/fastdraw/118863/play-Michigan-State-Spartan-Re-Screen
- **O95**: FastModel, "Michigan State SLOB Corner" (2015). https://playbank.fastmodelsports.com/library/basketball/fastdraw/66975/play-Michigan-State-SLOB-Corner
- **O96**: FastModel, "Tom Izzo: Wizard" (2015). https://fastmodelsports.com/library/basketball/fastdraw/70225/play-Tom-Izzo-Wizard

Other pages opened that informed context but are not cited above: Coach's Clipboard Newsletter #69 (Sep 2015), https://www.coachesclipboard.net/newsletters/CCNewsLetter09012015RED.html; Grantland "War" rebounding (S1); Coaches Insider, Sampson rebounding video summary, https://coachesinsider.com/womens-basketball/rebounding-wins-championship-with-kelvin-sampson-univ-of-houston-2; Hoop Coach, Bill Self Hi-Lo (PDF link page only), https://www.hoopcoach.org/bill-self-hi-lo-offense/; Hoops Companion zone-offense guest post (paywalled), https://hoopscompanion.substack.com/p/guest-post-simplifying-zone-offense; Hoop Vision, "Purdue's ball screen" (paywalled intro = S93); Raptors Republic, play-type article, https://raptorsrepublic.com/2015/12/17/what-types-of-plays-do-the-raptors-run/; Hoopscoop, MSU zone set (PDF only), https://www.mensbasketballhoopscoop.com/basketball-coaching-top-basketball-plays-for-zone-offense-tom-izzo-michigan-state-zone-set-play-brandon-rosenthal/; FastModel "Villanova Four-Out Ball Screen Motion" rules, https://playbank.fastmodelsports.com/library/basketball/fastdraw/123132/play-Villanova-Wildcats-Four-Out-Ball-Screen-Motion-Offense (Villanova 4-out ball-screen rules: slot-slot pass → interchange; slot-wing → shallow cut through the logo; low post sprints into the opposite-slot ball screen on reversal; bigs replace each other after slot/side screens).
