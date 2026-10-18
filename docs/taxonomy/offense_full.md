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


---

## Additions 2026-10-18 (Job A deep research)

Appended 2026-10-18 by the single writer for this file. Nothing above this line was edited or reworded. This section merges six Job A research notes compiled 2026-10-17/18: MSU sets (2024-25 and 2025-26), other Big Ten teams' sets, ball-screen offense, off-ball screens and cuts, special situations, and zone offense / press offense. Generic motion starts and half-court entries found in those notes are **not** repeated here; they belong in `docs/taxonomy/motion_starts.md`. MSU- and Big Ten-specific sets that begin from a motion start are kept.

**Rules for this section.**
- Only items that are **NEW** to this file, or **RICHER** versions of an existing row (new evidence, college or MSU attribution, roles, timings, metric signatures), are listed. Each block says which existing row it extends. Existing rows that the research merely re-confirmed without new content are listed in one line in the "Confirmations" sub-blocks, not repeated.
- **Units:** metres, seconds, degrees. Court spots are **(r m, θ°)**: r from the centre of the attacked rim, θ measured at the rim centre from the **right** baseline (0° = right baseline, 90° = straight up the lane, 180° = left baseline), as in `config/vocabulary_map.yaml` and §0.1. x = r·cos θ, y = r·sin θ. Left-side spots mirror right-side spots: θ_L = 180° − θ_R. Negative θ = out of bounds under the basket. Every foot value found in a source was converted at 1 ft = 0.3048 m.
- **Tags:** **unverified** = no source opened in the research confirmed it, or the opened page did not contain it. **[HEURISTIC]** = a detection threshold, timing window or template coordinate proposed for this project; it is an engineering choice, not a sourced fact. **Every numeric threshold, timing window and template coordinate below is [HEURISTIC] unless a source key is attached to that number.** **[CONVENTION]** = common coaching usage without a single opened source. **[pre-window]** = documented only before the season window the note was searching (2024-26 for MSU, 2023-26 for other Big Ten teams); kept because it defines a template.
- **Source keys** in this section resolve in **Additional sources (2026-10-18)** at the end of the section: `[M#]` MSU note, `[B#]` Big Ten note, `[P#]` ball-screen note, `[X#]` off-ball note, `[Q#]` special-situations note, `[Z:TAG]` zone/press note (the note's own alphabetic tags). `[O#]` and `[S#]` keys resolve in the Sources list above, as before. Every key was a page opened during the 2026-10-17/18 research with WebFetch or an equivalent HTTP fetch, as recorded in the research notes. This writer did not re-open them.
- **College (NCAA D-I) terms first.** NBA and European names are secondary aliases.

### A0. Spot landmarks and detection primitives used in this section

**Landmarks (r m, θ°)** (computed from `vocabulary_map.yaml` and §0.1; right side first, left side in brackets):

| Spot | (r, θ) | Basis |
|---|---|---|
| Top | (7.6, 90) | vocab "top": r ≥ 6.75, 80° < θ < 100° |
| Deep top / logo | (9.5, 90) | §0.1: r > 8.5 |
| Slot | (7.3–7.4, 70) [(7.3–7.4, 110)] | vocab: 60° < θ ≤ 80° |
| Wing (coaches' "45") | (7.2, 40) [(7.2, 140)]; wing centre (7.07, 45) | vocab: 12° < θ ≤ 60° |
| Corner | (6.8, 4–5) [(6.8, 175–176)] | vocab: r ≥ 6.60, θ ≤ 12° |
| Elbow | (4.57, 66.4) [(4.57, 113.6)] | vocab (exact) |
| Nail (point anchor); high post = band r 3.8–5.2, θ 70–110° (A9) | (4.19, 90) | vocab (exact) |
| Block | (2.0–2.04, 24–26) [(2.0–2.04, 154–156)] | vocab: x = ±1.83, y 0.3–1.5 |
| Dunker spot | (2.7, 6) [(2.7, 174)] | vocab: 2.0 ≤ \|x\| ≤ 3.5, y ≤ 0.6 |
| Mid-post | (3.1, 45) [(3.1, 135)] | §0.1 [HEURISTIC] |
| Short corner | (4.5, 8) [(4.5, 172)] | vocab "to be defined from film"; §0.1 r 3.5–5.5, θ 0–15 [HEURISTIC] |
| Lane line, high (just below the elbow) | (3.95, 62) [(3.95, 118)] | x ±1.83, y 3.5 |
| Lane line, low | (2.4, 39) [(2.4, 141)] | x ±1.83, y 1.5 |
| Wide-pin screen spot | (5.8, 18) [(5.8, 162)] | §8.1: screener at θ ≤ 25° [HEURISTIC] |
| BLOB inbound spot (0.91 m outside the lane, 0.3 m out of bounds) | (3.33, −34.7) [(3.33, 214.7); 214.7° ≡ −145.3° mod 360, convention in A11.20] | §0.1, `[O27]` |
| SLOB 8.53 m mark (8.53 m from the baseline), 0.3 m out of bounds | (10.5, 41) [(10.5, 139)] | §0.1, `[O27]` |
| Half-court centre | (12.73, 90) | §0.1 |

**Primitives (all [HEURISTIC]; they tighten §0.2 to the values used by the Job A notes):**
- `SCREEN(s→u)`: screener *s* speed ≤ 0.3 m/s for ≥ 0.5 s; the path of teammate *u* passes within ≤ 1.2 m of *s* while *s* is stationary; *u* speed ≥ 2.0 m/s at closest approach. Ball screen if *u* holds the ball.
- `ROLL`: after a ball screen the screener's radial velocity is ≤ −1.5 m/s within 1.0 s of the handler passing and he reaches r < 2.5 within 2.0 s. `POP`: the screener reaches r ≥ 6.6 within 2.0 s (`POP_ARC`; see `POP_MID` in A11.18). `SHORT_ROLL`: the screener catches a pass at r 3.0–6.0, \|θ − 90°\| ≤ 35°, within 2.0 s (A3's deceleration version is a strict confidence flag). `SLIP`: the screener is stationary < 0.5 s (fails the SCREEN dwell) and then accelerates toward the rim (radial velocity ≤ −2.0 m/s) before the handler reaches the screen line. `GHOST`: approach to ≤ 1.5 m without ever becoming stationary, then exit to r ≥ 6.6.
- `DHO(a→b)`: ball transfer with an a–b distance ≤ 1.0 m, ball air time ≤ 0.3 s; at least one of the two moving > 1.0 m/s.
- `CUT`: displacement ≥ 3 m in ≤ 1.5 s without the ball. `BACKDOOR`: a cut toward the rim from r ≥ 6 that starts within 0.5 s of the cutter's defender being between cutter and ball.
- `LOB`: a pass whose apex is above both players' heads (ball apex ≥ 3.5 m when ball height is tracked); otherwise a pass caught at r < 1.5 by a receiver moving toward the rim at ≥ 3 m/s.
- `t0`: the first frame of the first identifiable action of the set (half-court), the official's handover (out of bounds) or the rebound/outlet frame (live ball). Timing windows are seconds relative to the reference event declared for each subsection in A11.19 (negative values are allowed where stated, e.g. A3/A4 screen contact t₀); every timing cell should name its reference.
- `ALIGN`: Hungarian match of the 5 offensive (r, θ) points to a template; accept if the mean error is ≤ 1.8 m (§0.2).
- **Canonical values (fixer 2026-10-18):** where a block below states its own value for ROLL, POP, SHORT_ROLL, DHO, LOB, ELEVATOR or a named spot, the A11.18 primitive table and the A11.20 landmark list govern. Rim centre = 1.60 m from the baseline (`docs/requirements.md`); §0.1's 1.575 m is superseded here pending reconciliation by the requirements owner (A11.20).

### A1. F18 MSU: sets and actions documented for 2024-25 and 2025-26 (extends F18.1 and F18.2)

**Scope note.** MSU 2024-25: 30-7, Big Ten champions, Elite Eight. MSU 2025-26: 27-8, Sweet 16 (lost 67-63 to UConn) `[V4][V3]`; Sweet 16 also `[M14]`. **Key gap:** no opened source gives a 2025-26 MSU set by its in-house name. FastModel PlayBank had no MSU entry newer than 13 Mar 2025 (the MSU researcher scanned the ~1,200 most recent uploads and searched "michigan state", "michigan st", "spartans", "izzo", "msu" and player names) `[M50]`. *Fixer note 2026-10-18:* the cited `[M50]` page 1 shows only 15 of 120 results and is not sorted by date, so it cannot show this absence on its own; the claim rests on the researcher's scan of all 8 result pages and other searches that are not individually cited — treat it as an **unverified absence**. The 2025-26 items below (A1.6–A1.9, A1.12) therefore come from film-room prose by analysts and fan writers, not from diagrams. MSU-specific spots use the A0 landmarks.

#### A1.1 "77 Wide Pindown" — NEW (MSU, 2024-25)
- **Name and aliases:** "77 Wide Pindown" (analyst's name). "77" = a double screen at the top of the key; related rows: F2.1 "Double drag ('77')" and F16 "77".
- **Family / sub-family:** F5 (77 double ball screen at the top) → F8.1 corner pin / wide pin-down. Sub-family: "77 → wide pin" quick hitter for a lead guard.
- **Start alignment [HEURISTIC; the clip was not transcribed]:** 1 handler top (7.6, 90); 4 and 5 side by side just below the top (6.9, 84) and (6.9, 96); 2 (shooter) in a corner (6.8, 4) or (6.8, 176); 3 on the opposite wing (7.2, 140) or (7.2, 40).
- **Roles:** 1 = PG (Fears in the source); 2 = shooter receiving the wide pin (Akins; "Fidler some too"); 4/5 = double screeners. **Wide-pin screener: unverified** (the source says the play "immediately flows into a wide pindown in the corner" but does not name who sets it; one of the 77 screeners, a veer-type continuation, is the likely candidate).
- **Ordered actions (t0 = 1's first dribble toward the double screen) [HEURISTIC timings]:** (1) 0.0–2.0 s: 1 uses the 77 double screen. (2) 1.5–3.5 s: wide pin-down for 2 in the corner (side unverified). (3) 2.5–4.5 s: 2 curls or lifts off the pin; per the source the curl "will always be going to the dominant hand of the ball handler". (4) 3.0–5.0 s: catch-and-shoot or curl drive.
- **Usual counters:** curl toward the dominant hand (sourced). Fade/flare or a screener slip are generic F8.3 reads, **unverified** for MSU.
- **Detection signature [HEURISTIC]:** (a) two teammates stationary (≤ 0.3 m/s for ≥ 0.5 s) within 1.2 m of each other at r 6.5–7.5, θ 75–105°, while the handler's path passes within 1.2 m of both, entering from r > 7.6; (b) within 2.0 s of the handler clearing the second screener, a third player is stationary at the wide-pin spot (r 5–6.5, θ ≤ 25° or ≥ 155°) for ≥ 0.5 s and the corner player's path (start r ≥ 6.6, θ ≤ 12° or ≥ 168°) passes within 1.2 m of him moving +y (SCREEN_DIR = down/pin); (c) catch at r 5.5–7.5 within 1.5 s of the pin; (d) curl direction (sign of angular velocity around the screener) matches the shooter's dominant hand (needs a handedness label).
- **Teams documented (MSU first):** MSU 2024-25: first play of the exhibition vs Northern Michigan, 13 Oct 2024, Superior Dome `[M4][M9]`. The source says Izzo ran it for Tyson Walker "all the time" (2022-24) — **unverified** beyond that statement.
- **Sources:** `[M4]` https://feedthepost.substack.com/p/5-takeaways-michigan-state-vs-northern ; `[M9]` https://en.wikipedia.org/w/index.php?title=2024%E2%80%9325_Michigan_State_Spartans_men%27s_basketball_team&action=raw
- **Confidence:** medium (analyst, exhibition). Spots and the pin screener's identity **unverified**.

#### A1.2 "Shuffle Pick-and-Roll" — NEW (MSU, 2024-25)
- **Name and aliases:** "Shuffle Pick and Roll" (analyst's name); the source notes a "UCLA cut could also refer to this". Related rows: F8.2 UCLA cut, Shuffle cut.
- **Family / sub-family:** F8.2 UCLA/shuffle cut off a back screen → F5 wing ball screen for a wing scorer.
- **Start alignment [HEURISTIC]:** 1 top (7.6, 90); wings (7.2, 40) and (7.2, 140); back-screener at the elbow away from the first pass, (4.57, 113.6) if the pass goes right; 5th player at the opposite block (2.04, 26.2) or dunker spot (2.7, 6).
- **Roles:** 1 = PG (Fears), passer and back-screen cutter; ball-side wing = receiver; elbow/high post = back-screener; Akins (left-handed) = PnR handler; big = ball screener.
- **Ordered actions [HEURISTIC timings]:** (1) 0.0–1.0 s: 1 passes to one wing. (2) 0.5–2.5 s: 1 cuts off a back screen "on the other side" (source wording). (3) 2.0–5.0 s: the screener sets the ball screen so that the wing handler (Akins) drives to his left hand.
- **Usual counters:** lob or layup on the shuffle/UCLA cut if the defender trails high — generic, **unverified** for MSU.
- **Detection signature [HEURISTIC]:** (a) pass top (r ≥ 6.75, θ 80–100°) → wing (θ 12–60° or 120–168°); (b) within 1.5 s the passer's path passes within 1.2 m of a stationary teammate at an elbow/high post (r 3.8–5.0, θ 60–120°) moving −y (back screen) and reaches r < 3.0 within 1.5 s; (c) within 3 s, a ball SCREEN for a wing handler whose drive vector points to his dominant hand.
- **Teams documented:** MSU 2024-25 (exhibition vs Northern Michigan, 13 Oct 2024) `[M4]`.
- **Sources:** `[M4]` (URL in A1.1).
- **Confidence:** medium. Ambiguity: the source does not say whether the back screen is on the pass side or the opposite side.

#### A1.3 "Chicago" into an empty-corner side PnR with a big as handler — NEW MSU attribution (extends F6 "Zoom / Chicago" and F5 "Inverted PnR")
- **Name and aliases:** "Chicago action (pindown into a handoff)", then "empty corner pick and roll" (source). Related rows: F6 Zoom/Chicago; F15 empty side/corner.
- **Family / sub-family:** F6 Chicago/Zoom (pin-down → DHO) → F5 side PnR, empty-corner tag; the handler is a 2.11 m big.
- **Start alignment [HEURISTIC]:** Chicago receiver in the corner/low wing (6.8, 4); pin screener at the wide-pin spot (5.8, 18); DHO big with the ball at the slot (7.4, 70); weak side corner (6.8, 176) and wing (7.2, 140).
- **Roles:** Chicago receiver (guard); pin screener; DHO giver (big); then the PnR handler (Xavier Booker, a big) with a ball screener; strong-side corner emptied.
- **Ordered actions [HEURISTIC timings]:** (1) 0–1.5 s: pin-down for the corner/wing player. (2) 1.0–2.5 s: DHO from the big to the cutter at the slot/wing. (3) 2.5–6 s: when the defence takes it away, side PnR with the strong-side corner empty, big as handler. Source: "Northern Michigan defends it well, and MSU goes into an empty corner pick and roll with … Xavier Booker as the ball handler".
- **Usual counters:** inverted PnR (F2.1/F5 "Inverted"); whether a guard set the screen for Booker is **unverified**.
- **Detection signature [HEURISTIC]:** (a) SCREEN(down) for *u* with the screener stationary ≥ 0.5 s at r 5–6.5, θ ≤ 25° or ≥ 155°, *u* moving +y past him within 1.2 m; (b) DHO to *u* within 1.5 s at r 6.5–8.0, θ 30–80° or 100–150°; (c) within 4 s, a ball SCREEN where the handler is the tallest player on the floor (roster height) and no offensive player has θ ≤ 12° on the handler's side for the 2 s around the screen.
- **Teams documented:** MSU 2024-25 (exhibition, 13 Oct 2024) `[M4]`. Booker left after 2024-25 ("shooting 50% from deep at UCLA now") `[M16]`, so this does not carry to 2025-26. **False-match warning:** FastModel 487398 "MICHIGAN CHICAGO SPLIT" (2025-26) is **Michigan (Dusty May), not MSU** `[M49]`.
- **Sources:** `[M4]`; `[M16]` https://www.si.com/college/michiganstate/why-msu-jaxon-kohler-improved-3-point-shooting-important- ; `[M49]` https://playbank.fastmodelsports.com/library/basketball/fastdraw/487398/play-MICHIGAN-CHICAGO-SPLIT
- **Confidence:** medium (exhibition only; player-specific).

#### A1.4 "Double High Trade" ("2le High Trade") — NEW (MSU, 2024-25)
- **Name and aliases:** "Michigan St. 2le High Trade" (FastModel title; "2le" = double); "double high PnR with a trade action". Related rows: Detroit (set_taxonomy §3.2) and Double Fan (F18.1) are also double ball screens, but in Detroit both bigs flank the handler at once; here the two screens come in sequence ("trade"). Purdue's "Double High PnR" is the same family (see A2.1).
- **Family / sub-family:** F5.7, new sub-family **double/sequential high ball screen ("trade": the first screener lifts and the second screener re-screens)**. Start = new F3 alignment "Double High" (two bigs above the elbows).
- **Start alignment [HEURISTIC; frames give no spots]:** 1 top or deep (7.6–9.5, 90); 4 at (6.9, 80); 5 at (6.9, 100); 2 and 3 in the corners (6.8, 4) and (6.8, 176), or on the wings.
- **Roles:** 1 = PG ("PG exploits options"); 4 = first ball screener, then "lift up"; 5 = second ball screener (roll man).
- **Ordered actions (frame text `[M5]`):** (1) "2le high PnR, 1 PnR with 4"; (2) "1 PnR with 5, 4 Lift up, 1 exploits options". Timing [HEURISTIC]: screen 1 at 0–1.0 s; screen 2 at 1.0–3.0 s; 4 lifts to r ≥ 6.75 at 1.5–3.5 s; read at 2.5–5.0 s.
- **Usual counters:** roll by 5, lift/pop by 4, kick-out to the corners; specific reads **unverified**.
- **Detection signature [HEURISTIC]:** (a)+(b) canonical `double_high` (A11.17): pre-screen bigs at r 4.5–8.0, θ 60–120°, ≤ 3.5 m apart; ball SCREEN #1 by big A, then ball SCREEN #2 by big B on the same handler within 3.0 s and ≥ 0.8 s apart (sub-label `trade`), from the opposite side or re-screening in the same direction; (c) big A moves to r ≥ 6.75 (Δr ≥ +1.0 m) within 2.0 s of his screen and big B ROLLS (r < 3.0 within 2.0 s); (d) vs Detroit: in Detroit both screeners are stationary at the same moment ≤ 1.5 m from the handler on either side; in the trade the screens are separated by ≥ 0.8 s.
- **Teams documented:** MSU 2024-25. FastModel 2024-25 tag, published 4 Mar 2025 `[M5]`; the YouTube clip titled "NCAA 2024 25 Michigan 2le High trade 01" shows MSU in white at the Breslin Center, scorebug "WISCONSIN 21 – MICHIGAN ST 19, 1st, 9:56", MSU 23-5 — i.e. MSU vs Wisconsin, **2 Mar 2025** (MSU won 71-62) `[M6][M9]`. The game identification is the researcher's inference from the thumbnail. Purdue 2023-24 runs the same family (A2.1).
- **Sources:** `[M5]` https://playbank.fastmodelsports.com/library/basketball/fastdraw/478091/play-Michigan-St-2le-High-Trade ; `[M6]` https://www.youtube.com/watch?v=Jv0AvUTP-M4 ; `[M9]`.
- **Confidence:** medium-high.

#### A1.5 "MSU vs Zone" swallow-cut set — NEW (MSU, 2024-25; F11)
- **Name and aliases:** "Michigan State Vs Zone" (FastModel tag "ZONE OFFENSE"). Opponent zone type **unverified** (17 s clip; only the thumbnail was inspected).
- **Family / sub-family:** F11 zone offense: swallow/cut-through rotation (11.1), post-up of the 5 against the zone, corner cut and reversal.
- **Start alignment [HEURISTIC]:** likely one-guard front: 1 top (7.6, 90); 3 wing (7.2, 40); 2 opposite wing (7.2, 140); 4 high post/elbow (4.57, 66.4) or (4.19, 90); 5 low (2.04, 26.2) or the opposite block.
- **Roles:** 1 = PG (passer, cutter); 3 = wing, reverser, then corner cutter; 2 = fills 1's spot; 4 = high post/reverser; 5 = post-up.
- **Ordered actions (frame text `[M7]`):** (1) "1 swallow cut with 3, 1 pass to 3, 4 replace with 2"; (2) "3 pass to 2, 5 post up"; (3) "3 cut to corner, 2 pass to 4, 4 pass to 3". Timing [HEURISTIC]: frame 1 at 0–2 s, frame 2 at 2–4 s, frame 3 at 4–7 s.
- **Usual counters:** post entry to 5 on the reversal; corner shot for 3 (**unverified** beyond the frames).
- **Detection signature [HEURISTIC]:** (a) defence classified as zone (defense_full F8.0); (b) PG passes top → wing, then CUTs through the zone (path crossing r < 4.5) to the weak side while another player fills the top within 1.5 s; (c) reversal top → opposite side with 5 stationary at r 1.8–3.5 facing the ball for ≥ 0.5 s (post seal); (d) the original wing cuts baseline to the corner (θ ≤ 12° or ≥ 168°, r ≥ 6.6) and receives a pass via 4 within 3 s.
- **Teams documented:** MSU 2024-25. Clip thumbnail: MSU in white at the Breslin Center, "MICHIGAN 15 – MICHIGAN ST 30, 1st, 6:43" → **9 Mar 2025 vs Michigan** (researcher's inference) `[M7][M8]`. Context: Indiana beat MSU 71-67 on 11 Feb 2025 after switching to a 2-3 zone ("the zone threw them for a loop") `[M21]`; a YouTube description says MSU adjusted with "better spacing to quicker ball movement" (sets **unverified**) `[M33]`. **Not MSU-confirmed:** FastModel 473108 "Zone Offense – Izzo 2" is another coach's practice wrinkle named after Izzo `[M48]`.
- **Sources:** `[M7]` https://playbank.fastmodelsports.com/library/basketball/fastdraw/478264/play-Michigan-State-Vs-Zone ; `[M8]` https://www.youtube.com/watch?v=LhTyXYidfT8 ; `[M21]` https://feedthepost.substack.com/p/big-ten-basketball-weekly-newsletter-bb0 ; `[M33]` https://www.youtube.com/watch?v=TdhAecbJKJQ ; `[M48]` https://playbank.fastmodelsports.com/library/basketball/fastdraw/473108/play-Zone-Offense--Izzo-2
- **Confidence:** medium (frames verbatim; zone type, spots and timings **unverified**).

#### A1.6 Weave → high PnR ("Weave Zoom" family) with Kohler pick-and-pop — NEW to this file (MSU, 2025-26; diagram 2022-23)
- **Name and aliases:** "a weave up top followed by a high pick-and-roll" (TOC film room, 2025-26: "one of its go-to sets"); template diagram FastModel "Michigan State Spartans – Weave Zoom" (17 Mar 2023, tagged AFTER TIMEOUT). set_taxonomy §3.2 mentions "weave-into-PnR" (2015) as a Sprint-up option; "Weave Zoom" was not in the repo.
- **Family / sub-family:** F6 weave (chained DHOs) → F5 high PnR, screener post-action pop by a shooting big.
- **Start alignment [HEURISTIC]:** 1 top (7.6, 90); 2 slot/wing (7.3, 60); 4 opposite slot (7.3, 120) (in the 2023 diagram the 4 is a weave participant, i.e. a perimeter-capable big); 5 low or at an elbow (2.04, 26.2) or (4.57, 66.4); 3 in a corner (6.8, 176). 2025-26 mapping: Fears = handler; Kohler = screener who pops; Fort/Teng = corner shooter.
- **Roles:** handler (1); weave partners (2, 4); ball screener (5 in 2023; Kohler in 2025-26); corner shooter.
- **Ordered actions:** 2023 diagram `[M36]`: "1 DHO to 2"; "2 DHO to 4"; "4 DHO to 1"; "5 ball screens for 1". 2025-26 vs Arkansas (8 Nov 2025) `[M1]`: weave up top, high PnR Kohler–Fears, quick pass to the corner, Trey Fort finds Kohler for an open three. Timing [HEURISTIC]: DHO 1→2 at 0–1.2 s; DHO 2→next at 1.0–2.5 s; DHO back to 1 at 2.0–3.8 s; high ball screen at 3.0–5.0 s; pop or corner → popper at 4.0–6.5 s.
- **Usual counters:** corner pass then pass to the popping big (2025-26, sourced); roll. Generic weave counters (reject, backdoor off the weave) **unverified** for MSU.
- **Detection signature [HEURISTIC]:** (a) canonical `weave` (A4.6; flag `weave_3dho_return` for the 2023 diagram); (b) within 2.0 s of the last DHO, a ball SCREEN on the receiver at r 6.5–8.5, θ 65–115°; (c) the screener POPs (r ≥ 6.75 within 2.0 s, Δr ≥ +1.0 m) and receives a pass within 3.0 s, possibly via a corner touch (θ ≤ 12° or ≥ 168°); (d) 2025-26 screener identity Kohler (#0) or Cooper (#15); Cooper more often rolls (A1.12).
- **Teams documented:** MSU 2025-26 (TOC, vs Arkansas, 8 Nov 2025) `[M1]`; MSU 2022-23 (FastModel ATO) `[M36]` [pre-window]. Xavier 2022-23 "Weave PnR" (title only, not opened) — **unverified**.
- **Sources:** `[M1]` https://www.theonlycolors.com/basketball/43621/msu-basketball-film-room-plays-of-the-month ; `[M36]` https://playbank.fastmodelsports.com/library/basketball/fastdraw/437671/play-Michigan-State-Spartans--Weave-Zoom
- **Confidence:** medium for 2025-26 (named a go-to set but no frame order); high for the 2023 diagram text.

#### A1.7 DHO used as a ball screen, big rolls + baseline cutter → two lob options — NEW (MSU, 2025-26)
- **Name and aliases:** no in-house name published. TOC: "Coop and Fears will run a dribble hand-off, which serves as a ballscreen … Coen Carr cuts hard along the baseline. Jeremy gets to choose, he can throw a lob to either Carr or Coop." Generic: handoff-and-roll with a baseline "dunker" cut.
- **Family / sub-family:** F6 DHO → roll (DHO as ball screen) + F8.2 baseline cut → lob finish.
- **Start alignment [HEURISTIC]:** Fears receiving at the slot/wing (7.4, 70); Cooper bringing the ball from the top (7.6, 90); Carr in the weak-side corner (6.8, 176) or dunker spot (2.7, 174); Kohler at the weak wing/top (7.2, 140); Fort in the strong-side corner (6.8, 4).
- **Roles:** handler Fears; DHO giver/roller Cooper; baseline cutter Carr; spacers Fort and Kohler.
- **Ordered actions [HEURISTIC timings]:** (1) 0–1.0 s: DHO Cooper → Fears. (2) 0.8–2.5 s: Fears comes downhill (r from ~7 to ~4.5) while Cooper rolls down the lane. (3) 1.0–2.5 s: Carr cuts along the baseline toward the rim. (4) 2.0–3.5 s: lob to Cooper (chosen in the clip; and-one) or to Carr.
- **Usual counters:** kick-out to the shooters if help comes from them (the same article describes that read in the Kentucky clip, A1.12).
- **Detection signature [HEURISTIC]:** (a) DHO at r 6.5–8.0 whose giver is a 5; (b) the giver reaches r < 2.5 within 2.0 s after the DHO (roll from a DHO); (c) at the same time a weak-side player starting at θ ≥ 160° or ≤ 20° with r ≤ 7.0 moves along y < 1.0 toward the rim (\|x\| decreases ≥ 2 m in ≤ 1.5 s); (d) LOB to one of the two, caught at r < 1.5; (e) two perimeter players stay at r ≥ 6.6 with their defenders ≤ 1.5 m away during the action.
- **Teams documented:** MSU 2025-26, vs North Carolina, 27 Nov 2025 (Fort Myers Tip-Off), late first half; tied the game at 22 `[M1]`.
- **Sources:** `[M1]`.
- **Confidence:** medium (one clip in prose).

#### A1.8 Fake DHO → backdoor (Carr) — RICHER (extends F6 "Fake DHO / Keep" and F8.2 "Backdoor"; adds MSU 2025-26)
- **Name and aliases:** TOC: Cooper and Carr "close the gap … appearing to set up a dribble hand-off … he feels #11 for Iowa overplaying the exchange … and makes a great back door cut". Generic: "DHO away", fake handoff backdoor.
- **Family / sub-family:** F6 counter (fake DHO) → F8.2 backdoor cut.
- **Start alignment [HEURISTIC]:** Cooper (5) with the ball at the slot/top (7.4, 70); Carr (3) on the wing moving toward him (7.2, 40).
- **Roles:** ball-holder = 5; cutter = 3.
- **Ordered actions [HEURISTIC timings]:** (1) 0–1.0 s: the cutter moves toward the 5 (gap closes to ≤ 2 m). (2) 0.8–1.5 s: his defender jumps the exchange. (3) 1.0–2.5 s: plant, backdoor cut, bounce or lob pass, dunk.
- **Usual counters:** if not overplayed, the DHO happens and flows into the handler's action (generic).
- **Detection signature [HEURISTIC]:** (a) off-ball *u* approaches the ball-holding 5 to ≤ 2.0 m at r 6.5–8.0; (b) no DHO occurs; (c) within 0.8 s of the closest approach *u* reverses direction (> 120°) and reaches r < 2.0 within 1.5 s, with *u*'s defender between *u* and the ball at the reversal; (d) pass 5 → *u* at r < 2.0.
- **Teams documented:** MSU 2025-26, vs Iowa, 2 Dec 2025 (Big Ten opener, second half) `[M1]`. Fits SI (4 Oct 2025): "If [Fears] is getting to the rim, there is a good chance Carr will be there for a backdoor dunk" `[M17]`.
- **Sources:** `[M1]`; `[M17]` https://www.si.com/college/michiganstate/spartans-basketball-carson-cooper-jeremy-fears-coen-carr-tom-izzo-offense
- **Confidence:** medium.

#### A1.9 Post hub: low-post big feeds basket cutters; high-post big feeds; post double → kick-out — RICHER (extends F7 entries/splits; MSU 2025-26)
- **Name and aliases:** no set name. Labels: post hub with cutters; high-post passing; post double → kick-out.
- **Family / sub-family:** F7 post offense (hub passing, double-team reads) with F8.2 basket/middle cuts.
- **Start alignment [HEURISTIC]:** low-post big at the block (2.04, 26.2); high-post big at the nail (4.19, 90) or elbow (4.57, 113.6); cutters on the wings (7.2, 40) and (7.2, 140); PG top (7.6, 90).
- **Roles:** post hub Kohler (low) or Cooper (high); cutters Carr, Ward; kick-out shooter Fears (UNC example).
- **Ordered actions [HEURISTIC timings]:** entry pass to the post (receiver r < 3.5) → a cutter moves through the middle or baseline to r < 2.0 within 2.0 s of the entry → pass to the cutter. Alternative: the double arrives (two defenders ≤ 1.5 m from the post) → pass out to r ≥ 6.75 within 1.5 s.
- **Usual counters:** kick-out vs a double; cutter vs a ball-watching defender.
- **Detection signature [HEURISTIC]:** entry (receiver r < 3.5), then ≥ 1 CUT starting at r > 5 and ending at r < 2.0 within 2.5 s while the post holds the ball (≤ 2 dribbles). High-post variant: receiver at r 3.8–5.0, θ 60–120°. Post-double tag: ≥ 2 defenders within 1.5 m of the ball-holder at r < 3.5 for ≥ 0.4 s, then a pass to r ≥ 6.75.
- **Teams documented:** MSU 2025-26: vs Arkansas, 8 Nov 2025 (Kohler "finding both Carr and Ward on basket cuts"; Cooper "passing out of the high post"; Ward scored off middle cuts and off BLOBs) `[M12]`; vs UNC, 27 Nov 2025 (a Fears three "came off of a post double of Jaxon Kohler") `[M1]`; vs UConn, 27 Mar 2026 ("running post-up possessions for Cooper"; complaint about "two big men posted up on the blocks") `[M2]`.
- **Sources:** `[M12]` https://netscoutsbasketball.com/?p=937 ; `[M1]`; `[M2]` https://www.theonlycolors.com/basketball/45979/tom-izzo-must-adapt-if-he-wants-another-national-title
- **Confidence:** medium-low (actions and reads, not a named set).

#### A1.10 Dunker-spot big opposite the PnR (Kohler) — RICHER (extends F5.6 spacing tags and F15 "Dunker spot occupancy")
- **Name and aliases:** "dunker" spot (vocab `dunker_spot`). Source: most of Kohler's 2PA came "from the 'dunker' spot in Michigan State's offense (the spot on the opposite side of the lane to the pick and roll)".
- **Family / sub-family:** F5.6 off-ball spacing tag during a PnR / F15; linked to F14 (the dunker big is the offensive rebounder).
- **Start alignment:** during a PnR on one side, the big sits at the opposite dunker spot: (2.7, 174) if the PnR is on the right, (2.7, 6) if on the left.
- **Roles:** dunker big (Kohler, 2nd on the team in 2PA, 118, in 2024-25); PnR handler; screener.
- **Ordered actions:** big holds the weak-side dunker spot during the screen; if the low man over-rotates to the roll → dump-off or lob to the dunker; then crash.
- **Usual counters:** low man stays home → roller open (generic, **unverified** for MSU).
- **Detection signature [HEURISTIC]:** during any ball SCREEN, an offensive player with 2.0 ≤ \|x\| ≤ 3.5 m, y ≤ 0.6 m and sign(x) opposite to the ball for ≥ 60% of the 3 s window around the screen.
- **Teams documented:** MSU 2024-25 (Hammer & Rails preview of Purdue at MSU, 17 Feb 2025) `[M10]`.
- **Sources:** `[M10]` https://www.hammerandrails.com/2025/2/17/24367290/purdue-basketball-michigan-state-preview
- **Confidence:** medium (opponent-blog description).

#### A1.11 Split-court "mirrored" dual-PG offense — NEW (MSU, 2024-25; F15/F4)
- **Name and aliases:** "they can split the court and run a mirrored offense with Fears on one half and Holloman on the other. If the defense stuffs a Fears drive, Holloman can immediately reset the offense and attack" (Hammer & Rails).
- **Family / sub-family:** F15 spacing system; proposed new tag **"two-handler split court"**; possibly F4 two-side continuity.
- **Start alignment [HEURISTIC]:** Fears at the slot (7.4, 70); Holloman at the opposite slot (7.4, 110); the other three one per side plus a big.
- **Roles:** two lead handlers, one per half-court side.
- **Ordered actions:** handler A attacks on his half; if the drive is stopped, reversal to handler B who attacks immediately.
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** two designated handlers each spend ≥ 70% of a half-court possession on opposite sides (sign(x) differs); a handler-to-handler reversal within 2 s of a stopped drive (drive ends at r 2–5 with a pass out).
- **Teams documented:** MSU 2024-25 `[M10]`. Holloman transferred to NC State after the season, so it does not carry to 2025-26.
- **Sources:** `[M10]`.
- **Confidence:** low (characterisation, no clip).

#### A1.12 Fears high/side PnR as the 2025-26 base action — RICHER (extends F5 location/post-action/reads with MSU 2025-26 evidence)
- **Name and aliases:** high/side PnR, "Fears/Cooper or Kohler pick and roll" (TOC).
- **Family / sub-family:** F5: location high/side; post-action roll (Cooper) or pop/roll (Kohler); handler reads lob, kick-out, cutter.
- **Start alignment [HEURISTIC]:** Fears top (7.6, 90) or slot (7.4, 70); screener arriving from the elbow/high post (4.57, 66.4); second big at the weak-side dunker spot (2.7, 174) or block (2.04, 153.8); Carr in the weak-side corner (6.8, 176) or dunker/baseline; shooter (Teng/Fort) on the strong-side wing (7.2, 40) or corner (6.8, 4).
- **Roles:** handler Fears; screeners Cooper (rolls) and Kohler (pops or rolls); cutter Carr; shooters Teng, Fort.
- **Ordered actions [HEURISTIC timings]:** (1) 0–1.0 s: ball screen. (2) 0.5–2.0 s: Fears turns the corner; Cooper rolls, Kohler pops or rolls. (3) 1.0–3.0 s: lob to the roller, kick to the tagged-off shooter, or pass to a cutter.
- **Usual counters:** vs hedge/double: early pass to the roller or cutter (Louisville "hedged and even doubled … that allowed Fears to dice them"); vs drop/under: pull-up, which was low-efficiency ("when they went under screens or played drop coverage … he didn't do much damage") `[M14]`.
- **Detection signature [HEURISTIC]:** ball SCREEN at r 6.5–8.5, θ 60–120° (high) or 30–60°/120–150° (side); post-action ROLL (r < 3.0 within 2 s) vs POP (r ≥ 6.75); coverage label from defense_full F3 (hedge/double = ≥ 2 defenders within 2.0 m of the handler within 1.0 s of the screen); spacing tag = count of offensive players at r < 6.6 at the screen moment — the documented 2025-26 problem case is 4 of 5 inside the arc.
- **Teams documented:** MSU 2025-26: Izzo (Fox Sports, updated 22 Nov 2025; a 21 Nov date is **unverified**): Fears "he's got to come off those ball screens, which can wear you down a little bit" `[M13]` (re-opened 2026-10-18); vs Kentucky, 18 Nov 2025 (Cooper screens up top; the tag helper sinks; kick to Kur Teng for three; general read "if they step up and help … an easy kick out … If they cling to their men … a Fears lob to his bigs") `[M1]`; vs North Dakota State, 19 Mar 2026 (Fears–Cooper PnR with "four of the five Spartans inside the three-point line") `[M2]`; vs Louisville, 21 Mar 2026 (Fears–Kohler PnR; Fears 16 assists, an MSU NCAA-tournament record) `[M2][M14]`. Kohler's improved three "allowed Kohler to help run the pick-and-roll or pick-and-pop more effectively" `[M16]`. Transition FG 68.5% (99th percentile) vs half-court 41.9% (59th), citing CBBAnalytics `[M14]`.
- **Sources:** `[M13]` https://amp.foxsports.com/stories/college-basketball/michigan-state-hc-tom-izzo-jeremy-fears-jr-stats-as-good-any-guard-ive-had ; `[M1]`; `[M2]`; `[M14]` https://spartanavenue.com/jeremy-fears-shooting-struggles-are-letting-the-worst-michigan-state-fears-linger-to-the-sweet-16 ; `[M16]`.
- **Confidence:** medium.

#### A1.13 MSU primary break with roles (2024-25 and 2025-26) — RICHER (extends F1.4 "Izzo / MSU break" and F18.2 F1 row)
- **Name and aliases:** MSU primary break; "run all five". Job D (transition) owns the multi-definition transition model; this block only records the MSU role evidence.
- **Family / sub-family:** F1.1 outlet/advance, F1.2 lane rules, F1.3 big-man roles.
- **Start alignment:** at the DREB or inbound spot in MSU's backcourt; in the attacked-rim frame the players start at y ≈ 12.7–27.4 m (backcourt, including an inbounder behind the far end line; r > 12.7, θ ≈ 59–121°).
- **Roles (mapped to ball-handler, rim runner, wings, leak-out, trailer):** **ball-handler** = PG (Fears; Holloman in 2024-25), "out on the run"; **wings** "sprinting down the wings" (wide lanes); **rim runner** = "the first big down puts pressure on the rim"; in 2025-26 a "seal" big (Kohler) pins defenders in the paint; **leak-out: unverified** (the Arkansas clip shows the rebounding wing, Carr, running the lane himself after a pitch-ahead); **trailer: unverified for 2024-26** (the repo's shooting-trailer pitch-back `[O30]` is undated for these seasons).
- **Ordered actions [HEURISTIC; reconcile with Job D's Synergy / Hoop-Math 10 s / FastScout first-10 s / Hudl 4–8 s definitions]:** (1) 0–1.5 s after the possession change: outlet or pitch-ahead by the PG. (2) 1.0–4.0 s: wings fill lanes at \|x\| ≥ 5.5 m and cross half-court (y = 12.73 m). (3) 2.5–5.5 s: first big down reaches r < 2.0 or seals in the paint (\|x\| ≤ 1.83, y ≤ 4.19) with a defender on his back. (4) 3.0–7.0 s: shot at the rim or kick to a wing.
- **Usual counters (defence):** full-court pressure (Arkansas, 8 Nov 2025; Fears "controlled the ball against the Razorbacks' full-court pressure") `[M12]`.
- **Detection signature [HEURISTIC]:** possession change (DREB, steal or opponent make); ≥ 3 MSU players with forward speed ≥ 5 m/s within 2 s; ball crosses y = 12.73 m by ≤ 4 s; ≥ 2 MSU players at \|x\| ≥ 5.5 m during the advance; the first MSU big (roster position) reaches r < 2.0 or the paint before the second big within 6 s; shot by ≤ 7 s (primary) or ≤ 12 s (secondary). Store each external transition definition as a separate flag (Job D).
- **Teams documented:** MSU 2024-25: Michigan assistant Kyle Church, "They just run so fast, all five of them … the wings are sprinting down the wings, the first big down puts pressure on the rim" `[M11]`; Feed The Post: Fears "pushing the ball and getting MSU out and running" `[M22]`; `[M23]` (re-opened 2026-10-18) does not mention Fears and supports only the general tempo point ("The tempo that MSU plays at can just wear teams out"). MSU 2025-26: first possession vs Arkansas, 8 Nov 2025 (Carr DREB and dunk; Fears slows the chaser after passing ahead; Fort "aggressively popping out" on the right wing; Kohler seals "not one, but two Arkansas bigs") `[M1]`; transition FG 68.5% `[M14]`; fast-break points 25-12 vs Indiana `[M18]`.
- **Sources:** `[M11]` https://umhoops.com/2025/02/20/familiar-formula-michigan-preps-for-classic-michigan-state-test/ ; `[M22]` https://feedthepost.substack.com/p/big-ten-basketball-weekly-newsletter-26a ; `[M23]` https://feedthepost.substack.com/p/big-ten-basketball-weekly-newsletter-1c4 ; `[M1]`; `[M14]`; `[M18]` https://www.insidethehall.com/2026/02/27/what-to-expect-iu-basketball-hosts-michigan-state-on-sunday-afternoon/ ; `[M12]`.
- **Confidence:** high that MSU runs it in both seasons; medium for the role mapping; leak-out and trailer **unverified**.

#### A1.14 Confirmations of existing MSU rows (2024-25 / 2025-26), no new block needed
| Existing row | New confirmation | Season / game | Keys | Confidence |
|---|---|---|---|---|
| set_taxonomy §3.2 Sprint-up, option "weave-into-PnR" | Weave → high PnR is "one of its go-to sets" (A1.6) | 2025-26, vs Arkansas, 8 Nov 2025 | `[M1]` | medium |
| set_taxonomy §3.4 / F5.7 Kohler pick-and-pop `[S89]` | Kohler three off weave → PnR → corner pass; SI repeats the pick-and-pop point | 2025-26 | `[M1][M16]` | medium-high |
| F10 rim pressure / Carr backdoors `[O56]` | Carr backdoor off a fake DHO (A1.8); baseline cut as a lob option (A1.7) | 2025-26, vs Iowa (2 Dec), UNC (27 Nov) | `[M1][M17]` | medium |
| F1.4 / F18.2 F1 transition `[O30][O31][S9]` | Role-level quotes and clip (A1.13) | 2024-25, 2025-26 | `[M11][M1][M14][M18]` | high |
| F5.7 Detroit, F18.1 Double Fan | Sequential double high screen in a 2024-25 game (A1.4) — same family, not the same set | 2024-25, vs Wisconsin, 2 Mar 2025 | `[M5][M6]` | medium (family level) |
| F6 Zoom/Chicago (no MSU program listed) | MSU runs Chicago (A1.3) | 2024-25 exhibition | `[M4]` | medium |
| F2.1 / F16 "77" (generic) | MSU "77 Wide Pindown" (A1.1) | 2024-25 | `[M4]` | medium |
| F11 MSU 1-3-1 Special etc. | Zone trouble vs Indiana's 2-3 (11 Feb 2025) and a swallow-cut zone set by 9 Mar 2025 (A1.5). **Special / Fist / 1-3-1 Double were not re-confirmed for 2024-26** | 2024-25 | `[M21][M7]` | low-medium |

**Could not re-confirm for 2024-26 (left as cited above):** Horns Rip / Rip Away `[S24b]` (MGoBlog returned a Cloudflare challenge, HTTP 403; not bypassed) — **unverified in this research**. Every F18.1 set (DHO PNR Reject Pin, EOQ Horns, 21 Pin Chin, Miami Comeback, Double Fan, 1-4 High Curl Double Flare, Spartan Re-Screen, SLOB Corner, Wizard): no 2024-26 source mentions them — **unverified for 2024-26**. MSU press break: still **unverified**; the only mention is ball-handling against Arkansas's full-court pressure `[M12]`. MSU ATOs 2024-26: none diagrammed; the final ATO at UCLA (5 Feb 2025, down 63-61, < 10 s) ended in an Akins three, set not described `[M34]`. **Correction (2026-10-18, fixer):** the UCLA game was 4 Feb 2025 (local date; photo caption) `[M34][M9]`; the ATO ended in a **missed** Akins three-point attempt as the clock expired (UCLA won 63-61) `[M9]`; set not described. Both pages re-opened 2026-10-18.

#### A1.15 MSU FastModel sets 2020-21 to 2023-24 not described in this file [pre-window] — NEW to this file
These are outside the 2024-26 window but several 2024-26 players (Fears, Akins, Holloman, Kohler, Cooper, Carr) were on the 2023-24 roster, so they are plausible templates. **None is confirmed for 2024-26.** Captions are paraphrased from the FastModel frames `[M36]–[M46]`. Each row uses the full item format in compact form; start spots not given by the frames are [HEURISTIC] (A0 landmarks); timings are [HEURISTIC]. Confidence for every row: **high for the caption text, low for 2024-26 use**; for MSU usage, **medium-low** where the FastModel contributor is a third party (e.g. 1-4 STS, A3.1).

| Set (FastModel title, date) | Family / sub-family | Start alignment (r, θ) | Roles | Ordered actions with timing | Counters | Detection signature [HEURISTIC] | Source |
|---|---|---|---|---|---|---|---|
| **Weave Zoom** (17 Mar 2023, ATO) | F6 weave → F5 high PnR | See A1.6 | See A1.6 | See A1.6 | Pop, corner | Evidence row only: canonical `weave` (A4.6) with flag `weave_3dho_return`, then a high ball screen within 2.0 s (`weave_then_high_screen`) | `[M36]` |
| **Zipper Spain PNR SLOB** (17 Mar 2023) | F13.3 SLOB → F8 zipper → F6 → F5 Spain | Inbounder at the SLOB mark (10.5, 41); 1 at the block (2.04, 26.2) under a zipper screener at the lane line (3.95, 62); bigs at the elbows | 1 zipper cutter; 2 DHO giver; 3 weak-side DHO receiver; 4 corner cutter; Spain screener | 0–1.5 s zipper; 1.5–2.5 s 1→2; 2.5–4 s 2 DHO with 3 on the weak side; 1 flashes to the other post while 4 cuts to the opposite corner; 2 opens to the corner; 4–7 s side Spain PnR | Spain back-screen pop | Evidence row only — see **A3.21** (canonical: SLOB start with the inbounder out of bounds at \|x\| > 7.62, ≈ (10.55, 41.1)); zipper cut up the lane (+y ≥ 3 m); DHO; then a back screen on the roller's defender ≤ 1 s after a ball screen | `[M37]` |
| **Pin Down Circle** (23 Mar 2023, ATO / need a 3) — RICHER: set_taxonomy §3.2 had the title only | F6 → F8 stagger | 1 top (7.6, 90); 3 wing (7.2, 40); 2 weak-side block (2.04, 153.8); 4 and 5 stagger spots on the lane line | 1 DHO giver then stagger user; 4 pin screener; 5+4 stagger | 0–1.5 s 1 DHO to 3 while 4 down-screens 2; 1.5–3 s 3→2 while 1 runs off a 5+4 stagger; 3–4.5 s 2→1 | Shooter choice | DHO plus a simultaneous weak-side pin; the original passer then uses a stagger (two screeners ≤ 2.5 m apart along his path) | `[M38]` |
| **Iverson Ram Reject Away** (25 Sep 2023, for Joey Hauser; "46% 3P per Synergy") — NEW for MSU (F5 Ram had Michigan/UConn only) | F8 Iverson → F5 Ram → reject → F8 screen away | 1-4 high: 1 top; 4, 5 elbows (4.57, 66.4/113.6); 2, 3 wings | 3 Iverson cutter then handler; 4 screener then Ram screener then screen-away target; 5 ball screener (fake) then screen-away screener | 0–1.5 s 3 Iverson cut; 2 cuts under; 4 screens for 3; 1.5–2.5 s 1→3; 1 clears weak side and exchanges with 2; 2.5–4 s 4 sets a Ram for 5; 5 fakes the ball screen; 3 rejects and drives baseline; 4–6 s 5 screens away for 4 behind 3; 3 hits 4 | Reject drive; screen-away shot | Iverson cut across y 3–5 m; Ram (screener himself screened ≤ 1.5 s before the ball screen); handler drives away from the screener; screener then screens away | `[M39]` |
| **1-4 STS** (21 Mar 2024; "a Tom Izzo staple over the last 15 years") — NEW sequence (STS and Box STS existed) | F3 1-4 high → F8 STS → F5 | 1 top (7.6, 90); 4, 5 elbows; 2, 3 wings (7.2, 40/140) | posts = screeners/poppers; guards = curl and STS users | 0–1.5 s post screens the wing defender, guard curls to the corner; post pops for the entry; 1.5–3.5 s opposite guard cuts high or low off 5's elbow screen; 5 pops to the top and reverses; 3.5–5.5 s STS for a layup or top three; post re-screens into roll/replace; else reversal and a guard+post stagger away | Layup / top three; stagger away | 1-4 high snapshot (4 players at r 4.5–7.5, θ 40–140°, nobody at r < 3); curl; elbow screen; STS (screener becomes screenee ≤ 1.5 s) | `[M40]` |
| **BLOB** (24 Mar 2024; "a good BLOB to run down the stretch") | F13.2 BLOB | Inbounder (3.3, −35); box/stack spots in the lane | 2, 4 loop runners; 5 screener; 1 inbounder | 0–1 s 2 and 4 loop around each other (brush); 1–2 s 5 screens for 4; 1→2 | — | Two paths cross ≤ 1.0 m apart inside the lane within 1 s of the inbounder receiving the ball, then a SCREEN for one of them | `[M41]` |
| **Horns Twist Veer** (28 Mar 2024) — RICHER (F3.2 Horns Twist had no MSU veer ending) | F3.2 Horns → F5 twist → F5.4 veer | Horns (§3.1) | handler; two elbow screeners | "Stacking multiple ball screen actions ending with a veer screen for the open shot" (no frames); timing [HEURISTIC] screen 1 at 0–1.5 s, screen 2 at 1.5–3 s, veer pin at 3–5 s | Open shot off the veer | Horns; ball screen 1, then screen 2 from the opposite side (twist); screener 2 sets an off-ball pin ≤ 2 s later (veer) | `[M42]` |
| **Stagger Slip Curl & Pop** (20 Mar 2022) | F8 stagger → slip; down screen → pop | Stagger screeners on the lane line (2.4, 39) and (3.95, 62); user at the block | 4 first stagger screener who slips; 5 down-screener; 4 popper | "stagger screen into a slip by the 4 and down screen by the 5 for a pop out for 4"; timing [HEURISTIC] 0–2 s stagger, 1–2.5 s slip, 2.5–4.5 s down screen and pop | Slip; pop | Stagger where the first screener leaves before contact (speed > 0.6 m/s within 0.3 s of the cutter passing); 5 then down-screens 4, who reaches r ≥ 6.75 | `[M43]` |
| **Quick Duck-In BLOB** (19 Mar 2022) | F13.2 BLOB, 4-low | 4-Low per A6.7: all four in-bounds attackers at y ≤ 1.5 m with x spread ≥ 9 m at t_dispose | 5 duck-in post | "A classic BLOB out of the 4 Low. Quick duck in for your 5 gets you a deep post touch"; 0–1 s duck-in | — | 4-low snapshot; 5 reaches r < 1.5 within 1 s of the handover | `[M44]` |
| **Clear BLOB** (19 Mar 2022, ATO) | F13.2 BLOB late clock → F9 clear | Inbounder (3.3, −35) | playmaker receiver; three clearing teammates | "Late in the shot clock … get the ball into your playmaker and give them space to make a play"; 0–1.5 s inbound to the handler; 1.5–3 s clear | Iso | Inbound to the primary handler, then ≥ 3 teammates move to r ≥ 6.6 | `[M45]` |
| **STS ATO BLOB** (8 Dec 2020; run at Duke, 1 Dec 2020) — RICHER: title only in §13.2 / set_taxonomy | F13.2 BLOB / F8 STS | Inbounder (3.3, −35); box | 3 elbow-extended receiver; 2 screener then turnout user; 4 turnout screener; 5 screened big | 0–1 s entry to the corner; 1–2 s 3 gets open at the elbow extended; 2–3.5 s 2 screens for 5 and 4 sets a turnout screen for 2 | — | Corner entry; a guard screens a big, then a big screens that guard (STS) ≤ 1.5 s | `[M46]` |

Also opened: FastModel "Zone Lob (Michigan State)" (22 Dec 2021, M. Hackenberg), an outside coach's zone lob vs 2-3 or 3-2 (wing entry; 2 drives baseline; 3 flattens to the weak corner; 2 returns the ball to 1 while 5 screens the low weak-side forward; 4 flashes in front of X5). Not tied to an MSU game; recorded only as a lead `[M47]`.

**False-match warnings (for clip labelling).** (1) The YouTube channel "Antonios kourmoulis" abbreviates both Michigan and Michigan State as "Michigan": its "NCAA 2025 26 Michigan 2le High PnR Chicago split", "… Michigan BLOB" and "… Michigan Rip Screen" thumbnails show **Michigan Wolverines** (vs Purdue, Big Ten Championship; vs Indiana at Crisler) and are excluded; its "NCAA 2024 25 Michigan 2le High trade" **is MSU** `[M52][M6]`. (2) FastModel 487398 "MICHIGAN CHICAGO SPLIT" is Michigan `[M49]`. (3) "Zone Offense – Izzo 2" is not an MSU game set `[M48]`. (4) The "Tom Izzo Open Practice Series" description (posted 7 Nov 2015) predates 2024-26 `[M69]`.

### A2. Big Ten other teams (2023-24 to 2025-26): new sets and new team confirmations

**Scope note.** Purdue, Michigan, Illinois, Wisconsin, Maryland, Indiana, Iowa, Ohio State, Nebraska, Northwestern, Rutgers, Penn State, Minnesota, UCLA, USC, Oregon, Washington. Many FastModel PlayBank pages are short user-contributed summaries; entries that were explicitly women's were excluded, and entries whose gender is not stated are used only when the opened page made the men's team clear (exclusion list at the end of A2). *Fixer note 2026-10-18:* four items break this rule — A2.2 `[B7]`, A2.17 `[B2]`, A2.35 `[B16]` and A2.41 `[B13]` come from pages that do not say men's/MBB and name no men's player or game; their men's attribution is **unverified** until a men's source is opened (each item carries a note). Families follow this file. MSU items found in this pass (2le High Trade, 1-4 STS, Vs Zone) are in A1.

#### A2.1 Double High PnR (Purdue) — NEW (same family as MSU "2le High Trade", A1.4)
- **Name and aliases:** Double High PnR (FastModel/Purdue title); Purdue 2022-23 "Double High Pin" start. Not the NBA "77" (in this file "77" is a stagger/double drag).
- **Family / sub-family:** F5.7 double/sequential high ball screen; start = new F3 alignment "Double High" (two bigs above the elbows).
- **Start alignment [HEURISTIC; the page gives none]:** 1 top (7.6, 90) or deep (9.5, 90); 4 high left (6.0, 105); 5 high right (6.0, 75); 2 corner (6.8, 5); 3 opposite corner (6.8, 175). The 2022-23 "Double High Pin" page says "4 & 5 lift up to elbows" `[B42]`, so the elbows (4.57, 66.4)/(4.57, 113.6) are an equally valid start.
- **Roles:** 1 handler; 4 first screener, then "moves to the low post" (Purdue) — contrast MSU, where 4 "lifts up"; 5 second screener; 2 lifts, 3 spaces.
- **Ordered actions `[B10]`:** (1) 1–4 PnR, t ≈ 0–2 s; (2) 4 to the low post, 1.5–3 s; (3) 1–5 second PnR, 2.5–4.5 s; (4) 2 lifts; (5) 1 reads. Timings [HEURISTIC].
- **Usual counters:** not stated; [CONVENTION, unverified] reject the second screen; 4 ducks in vs a switch; skip to the lifted corner.
- **Detection signature [HEURISTIC]:** two ball SCREENs on the same handler by two different screeners within 3.0 s, both at r 6.5–9.0, θ 60–120°; first screener's post-action ROLL to r < 2.5 (Purdue) or POP/lift to r ≥ 6.6 (MSU trade); the handler's lateral direction may reverse or continue between screens (Twist requires opposite direction); snapshot before screen 1: canonical `double_high` (A11.17) — two non-handlers at r 4.5–8.0, θ 60–120°; the two screens ≥ 0.8 s apart; sub-labels `sink` (first screener to r < 2.5, Purdue) and `trade` (first screener to r ≥ 6.75, MSU).
- **Teams documented (MSU first):** MSU 2024-25 (A1.4) `[B35]`; Purdue 2023-24 (NCAA tournament set, FastModel 1 Apr 2024) `[B10]`; Purdue 2022-23 "Double High Pin" (4 & 5 lift to the elbows, 4 back-screens 1, 5 pins for 1) [pre-window] `[B42]`.
- **Sources:** `[B10][B35][B42]`.
- **Confidence:** medium.

#### A2.2 Ram Double Ball Screen (Purdue) — NEW combination (extends F5.3 "Ram" and F5.7 "Detroit")
- **Name and aliases:** Ram Double Ball Screen (FastModel/Purdue): a ram screen that creates a double (stacked) ball screen.
- **Family / sub-family:** F5.3 screener pre-action (Ram) + F5.7 double ball screen.
- **Start alignment [HEURISTIC]:** 1 top (7.6, 90); 4 elbow (4.57, 66.4); 5 opposite elbow or block; 2 and 3 in the corners (6.8, 5)/(6.8, 175).
- **Roles:** 5 ram screener; 4 first ball screener; 1 handler; 2 strong-side corner (pitch target).
- **Ordered actions `[B7]`:** (1) 5 screens for 4 (ram), t ≈ 0–1.5 s; (2) 4 and 5 set a double ball screen for 1, 1.5–3 s; (3) when X2 helps on the drive, 1 pitches to the corner, 3–5 s.
- **Usual counters:** corner pitch when the corner defender helps `[B7]`; others **unverified**.
- **Detection signature [HEURISTIC]:** off-ball SCREEN(5→4) with 4 moving ≥ 2 m toward the handler; within 1.5 s both 4 and 5 stationary (≤ 0.3 m/s, ≥ 0.5 s) within 1.5 m of each other and within 2.0 m of the handler at r 6.5–8.5; handler drive (Δr ≤ −3 m) then a pass to r ≥ 6.6, θ ≤ 12° (or ≥ 168°) on the drive side.
- **Teams documented:** MSU related only ("EOQ Horns Set", 4 and 5 cross into ball screens; already F18.1 `[O89]`, re-opened `[B36]`); Purdue 2023-24 (FastModel 14 Nov 2023, Tony Miller) `[B7]`. Gender not stated on the source page; men's attribution **unverified** (A2 scope rule).
- **Sources:** `[B7][B36]`.
- **Confidence:** medium.

#### A2.3 Ram PnR — RICHER (extends F5.3 "Ram": Illinois 2024-25; Purdue "Ram Fake Lob")
- **Name and aliases:** Ram, Ram to PnR; Purdue "Ram Fake Lob".
- **Family / sub-family:** F5.3 screener pre-action.
- **Start alignment [HEURISTIC]:** 1 top (7.6, 90); 4 at the low lane line (2.4, 39); 5 at the same-side elbow (4.57, 66.4); 2, 3 wings/corners.
- **Roles:** 4 ram screener, then exits to the top; 5 ball screener; 1 handler.
- **Ordered actions:** Illinois `[B3]`: (1) 4 down-screens 5, t ≈ 0–1.5 s; (2) 1–5 PnR, 1.5–3.5 s; (3) 4 exits to the top, 2–4 s; (4) 1 reads. Purdue "Ram Fake Lob" `[B41]`: 1 sets a ram for 5; 5 cuts hard toward 1, then **slips** for a lob.
- **Usual counters:** "PG exploits options" only (**unverified** detail); slip lob (Purdue).
- **Detection signature [HEURISTIC]:** off-ball SCREEN(4→5) whose user moves ≥ 2 m toward the handler, followed within 1.5 s by SCREEN(5→1 with ball); screener 4 then reaches r ≥ 6.6, θ 70–110° within 2.0 s (exit). Fake-lob variant: 5 fails the SCREEN dwell and reaches r < 1.5 with a LOB within 1.5 s.
- **Teams documented:** Illinois 2024-25 (FastModel 27 Jan 2025) `[B3]`; Purdue 2022-23 [pre-window] `[B41]`. Existing: Michigan "Iverson Ram" `[S24]`, UConn `[O14]`, MSU "Iverson Ram Reject Away" (A1.15).
- **Sources:** `[B3][B41]`.
- **Confidence:** medium (Illinois); high for the 2022-23 Purdue text.

#### A2.4 "Spread" PnR family (Purdue): Horns Spread PnR, Iverson Spread Ball Screen, Spread Lift Slip — NEW
- **Name and aliases:** "Spread" in Purdue titles = a top/slot ball screen with both corners filled and the paint emptied. **Not** the Underwood/Altman "Spread" continuity (F3.1 "Spread (Underwood)"). See Vocabulary proposals.
- **Family / sub-family:** F5.1 location top/slot + F5.6 spacing tag "spread / both corners"; Horns start = F3.2.
- **Start alignment:** Horns Spread PnR `[B4]`: "A-set" — evens on the right, odds on the left; either side. Interpreted [HEURISTIC]: 1 top (7.6, 90); 4 right elbow (4.57, 66.4); 5 left elbow (4.57, 113.6); 2 right corner (6.8, 5); 3 left corner (6.8, 175). Iverson Spread `[B39]`: 2 low on one side, 3 and 4 on the opposite side.
- **Roles:** 1 handler; one elbow big sprints to the post (4); the other (5) is the pick-and-pop screener; corners hold.
- **Ordered actions:** Horns Spread PnR `[B4]`: (1) 4 sprints to the post (r < 2.5), t ≈ 0–1.5 s; (2) 5 ball-screens and pops for reversal or an iso, 1–3 s; (3) on the catch 5 may rip-and-drive, 3–5 s. Iverson Spread Ball Screen `[B39]`: 2 Iverson-cuts to the wing; 4 and 3 cut to the opposite corner; 1 comes off 5's ball screen; 5 rolls; 3 "show corner discipline and remain shot ready". Spread Lift Slip `[B40]`: 1→2 and 1 inside-cuts to the corner; 4 lifts to the slot (occupies the help); 5 sprints to the ball screen and slips.
- **Usual counters:** pick-and-pop reversal or iso for the popper `[B4]`; slip vs hedge/blitz `[B40]`.
- **Detection signature [HEURISTIC]:** ball SCREEN at r 6.5–8.5, θ 60–120° with both corners occupied (one player at r ≥ 6.6, θ ≤ 12° and one at θ ≥ 168°) and the lane empty (no offensive player at r < 3.0 other than the roller) at screen time ± 0.5 s. Horns version: Horns snapshot and, within 1.5 s, one elbow player reaching r < 2.5 before the other elbow player's SCREEN. Slip version: screener approach speed ≥ 3 m/s and dwell < 0.5 s, plus a corner/wing player moving to a slot (Δθ toward 90° ≥ 20°) within ± 1 s.
- **Teams documented:** Purdue 2023-24 (FastModel 31 Mar 2024) `[B4]`; Purdue 2022-23 [pre-window] `[B39][B40]`.
- **Sources:** `[B4][B39][B40]`.
- **Confidence:** medium (Horns Spread); high for the 2022-23 step lists.

#### A2.5 Iverson PnR "Under" (Rutgers) — NEW
- **Name and aliases:** Iverson PnR Under (FastModel).
- **Family / sub-family:** F5 wing/slot PnR with an F8.2 Iverson entry and a new F5.6 spacing tag **"under / slide-under"** (a big slides underneath the ball screen toward the short-corner side as a shooter).
- **Start alignment [HEURISTIC]:** 1 top (7.6, 90); 2 wing (7.2, 140); 3 opposite wing (7.2, 40); 4 and 5 at the elbows (4.57, 66.4)/(4.57, 113.6) as Iverson screeners.
- **Roles:** 2 scorer/handler; 3 clears; 4 "sneaks under" shooter; 5 ball screener/roller; 1 entry passer.
- **Ordered actions `[B24]`:** (1) 3 clears, t ≈ 0–1 s; (2) 2 uses the Iverson screens across the elbows for a wing entry, 0.5–2.5 s; (3) 5 ball-screens for 2 while 4 slides underneath, 2.5–4.5 s; (4) 2 drives, hits the rolling 5 or passes back to 4, 4–6 s.
- **Usual counters:** drive / roll / pass to the under-sliding shooter `[B24]`.
- **Detection signature [HEURISTIC]:** lateral CUT by 2 through y 4–6 (θ 60–120°) past two stationary elbow players → catch at a wing (r 6.6–8, θ 25–55° or 125–155°) → ball SCREEN by 5 within 2.0 s; during the screen a fourth player moves from the high side to below the screen (passes y < screen-y − 1.5 m) and stops at r 5.5–7.5 on the same side within 1.5 s.
- **Teams documented:** Rutgers 2024-25 ("basic action they ran during the 2024-25 season", FastModel 1 Mar 2025) `[B24]`.
- **Sources:** `[B24]`.
- **Confidence:** medium.

#### A2.6 Swing Iso PnP (pop, reversal, second pop) (Illinois) — NEW sequence
- **Name and aliases:** Swing Iso PNP (FastModel; "Euroball action with a main PnPop").
- **Family / sub-family:** F5.4 screener post-action pop → reversal → second pick-and-pop.
- **Start alignment [HEURISTIC]:** 1 top (7.6, 90); 5 high (6.0, 90); 2 wing (7.2, 40); 3 opposite wing (7.2, 140); 4 corner or short corner.
- **Roles:** 5 popping big (two pops); 1, then 2 handlers; 3 backdoor cutter; 4 fills the "45" (wing); 1 finishes in the low post.
- **Ordered actions `[B14]`:** (1) 1–5 pick-and-pop, 1→5, t ≈ 0–3 s; (2) 3 back-cuts, 2 lifts, 5→2, 3–5 s; (3) 3 to the corner, 4 to the 45, 1 to the low post; 2–5 pick-and-pop; 5 reads, 5–9 s.
- **Usual counters:** backdoor by 3 on the reversal `[B14]`; post seal by 1 after the second pop — **unverified** as a designed option.
- **Detection signature [HEURISTIC]:** two POP events by the same screener within 8 s with two different handlers; between them a pass to the popper at r ≥ 6.6, a BACKDOOR by a wing and a lift by the other guard to a slot; the original handler reaches r < 2.5 before the second screen.
- **Teams documented:** Illinois 2023-24 (FastModel 25 Mar 2024) `[B14]`.
- **Sources:** `[B14]`.
- **Confidence:** medium.

#### A2.7 Pick-and-pop and short roll with 2.13–2.18 m bigs in five-out — RICHER (extends F5.4 "Short roll"/"Pop"; 2025-26 team confirmations)
- **Name and aliases:** pick-and-pop (PnP); short roll; new counter label **"short roll vs the sideline trap of a wing ball screen"**.
- **Family / sub-family:** F5.4 screener post-action; F10 spacing.
- **Start alignment [HEURISTIC]:** 5-out: handler at a wing (7.2, 40) (Illinois: "Wagler starts a lot of his actions from this spot") `[B53]`; screener arrives from the slot/top; others at the top (7.6, 90), opposite wing (7.2, 140), corners (6.8, 5)/(6.8, 175).
- **Roles:** Illinois 2025-26 handlers Wagler (wing), Boswell, Stojakovic; pop/short-roll bigs Mirkovic, Tomislav Ivisic, Zvonimir Ivisic (2.18 m) `[B57][B53][B54]`. Purdue 2025-26: Smith handler, Kaufman-Renn short roll `[B53]`. Iowa 2025-26: Stirtz handler, short roll "with a cutting option" `[B60]`.
- **Ordered actions `[B53]`:** wing ball screen (t 0–1.5 s) → hedge/trap on the sideline → screener catches in the "pocket of space" between the trappers (short roll, 1.5–3 s) → 4-on-3: kick to a relocating shooter or dump-off to the dunker side when the low man helps (3–4.5 s). PnP: screener pops to the arc. Underwood quote "It distorts the defense when you've got a 5-man that can shoot" — **unverified** (seen only in a search summary; the opened SI piece `[B57]` paraphrases the idea).
- **Usual counters (defence):** drop (Illinois expected drop vs Alabama-style actions) `[B53]`; blitz (Alabama blitzed Smith ball screens) `[B53]`.
- **Detection signature [HEURISTIC]:** handler at r 6.6–8.0, θ 25–55° (or 125–155°) receives a ball SCREEN; two defenders within 2.0 m of the handler for ≥ 0.5 s (trap) and a pass to the screener at r 3.5–6.0 within 2.0 s (SHORT_ROLL); next pass within 1.5 s to r ≥ 6.6 (kick) or r < 2.0 (dump-off). PnP: screener reaches r ≥ 6.6 within 1.5 s and receives (catch-and-shoot ≤ 1.0 s or rip-and-drive).
- **Teams documented:** MSU (Kohler pick-and-pop 2025-26, A1.12 / `[S89]`); Illinois 2025-26 `[B53][B54][B57]`; Purdue 2025-26 (Kaufman-Renn short roll vs Alabama's blitz, Nov 2025) `[B53]`; Iowa 2025-26 `[B60]`; Wisconsin 2025-26 ("a ton of pick-and-roll and pick-and-pop actions") `[B59]`.
- **Sources:** `[B53][B54][B57][B59][B60]`.
- **Confidence:** medium.

#### A2.8 Switch-hunt ball screen into a post-up ("mismatch hunt") — NEW action entry (extends F9 "Mismatch iso" and F4 Houston signature)
- **Name and aliases:** switch hunting; "get the switch and post the smaller defender".
- **Family / sub-family:** F5.7 (ball screen chosen by the screener's defender) → F7 post-up on the mismatch; F17 outcome Post-Up.
- **Start alignment [HEURISTIC]:** handler at the top/slot (7.3, 70); screener arriving from the high post (4.19, 90).
- **Roles:** screener = mismatch target (Northwestern: Martinelli); handler = decoy/creator (Jalen Leach).
- **Ordered actions `[B43]`:** (1) a first ball screen by a big (Mullins) "that doesn't do much", t 0–2 s; (2) a second ball screen by the target forward, chosen to involve the two freshmen defenders, 2–4 s; (3) if switched, the forward seals and backs the smaller defender down to a left-hand flip, 4–9 s; (4) if not switched, the handler attacks downhill (Leach and-one). Northwestern ran it on all 6 OT possessions (5 scores) `[B43]`. Iowa 2025-26: "If the Hawkeyes see a mismatch, they will hunt it or force a ball screen switch" `[B60]`.
- **Usual counters:** refuse to switch (Illinois did once; the handler then attacked) `[B43]`.
- **Detection signature [HEURISTIC]:** ball SCREEN after which the two defenders swap assignments (nearest-neighbour defender labels exchange within 1.0 s) and the screener's new defender is ≥ 8 cm shorter or is a guard (roster height); within 2.5 s the screener sets up at r 1.5–4.0 with his back to the rim (speed toward the rim < 0.5 m/s, facing the ball) and receives an entry; or the same pair repeats the screen on ≥ 3 consecutive possessions.
- **Teams documented:** Northwestern 2024-25 (Collins; OT vs Illinois, Dec 2024) `[B43]`; Iowa 2025-26 (McCollum) `[B60]`.
- **Sources:** `[B43][B60]`.
- **Confidence:** medium-high (Northwestern); medium (Iowa).

#### A2.9 Fake pin-down into a slipped tandem ball screen (Iowa 2024-25) — NEW combination
- **Name and aliases:** described, not named: "a fake pindown by Freeman and then a Sandfort slipped ball screen at the top of the key in tandem with Dix" `[B43]`.
- **Family / sub-family:** F5.3 pre-action (fake pin-down) + F5.4 slip; F8.1 decoy.
- **Start alignment [HEURISTIC]:** handler top (7.6, 90); big (Freeman) at the high lane line (3.95, 62); shooter (Sandfort) below him at the block; second guard (Dix) at the opposite slot.
- **Roles:** Freeman fake pin-down screener; Sandfort slipping screener (shooter); Dix second top player (tandem).
- **Ordered actions `[B43]`:** (1) earlier in the possession, a Freeman ball screen for Thelwell; (2) Freeman fakes a pin-down; (3) Sandfort slips a ball screen at the top in tandem with Dix; (4) Northwestern switched; Dix drove. Times **unverified** (prose only).
- **Usual counters:** switching neutralised it in the clip `[B43]`.
- **Detection signature [HEURISTIC]:** a non-ball player approaches a teammate below the elbow (≤ 1.5 m) moving upward but never dwells ≥ 0.5 s (fake pin-down) → within 1.5 s two players arrive at r 6.5–8.5, θ 70–110° within 3 m of each other near the handler; one fails the SCREEN dwell (SLIP) toward the rim or the arc.
- **Teams documented:** Iowa 2024-25 (McCaffery; vs Northwestern, Dec 2024) `[B43]`.
- **Sources:** `[B43]`.
- **Confidence:** low-medium.

#### A2.10 Purdue base high PnR with the screener parked at the nail — RICHER (team-specific tendency for F5.1 "High / Top")
- **Name and aliases:** high pick-and-roll Smith–Kaufman-Renn; the screener "loitered in his normal location at the free throw line" before screening; Smith initiates "the vast majority" of the offense from the top `[B48]`.
- **Family / sub-family:** F5.1 location top / F5.3 pre-action (screener starts at the nail).
- **Start alignment `[B48]`:** 1 (Smith) top (7.6, 90); 4/5 (Kaufman-Renn) nail (4.19, 90); 2 (Loyer) wing (7.2, 40); 3 (Cox) baseline/corner; other big low.
- **Roles:** Smith handler; Kaufman-Renn screener/short-roller; shooters spaced.
- **Ordered actions:** screener steps up from the nail to the ball (≈ 3.4 m in ≈ 1 s) [HEURISTIC] → high PnR → roll/short roll (A2.7).
- **Usual counters:** Painter breaks the tendency with a wing entry + fake pin-down post-up (A2.15) `[B48]`.
- **Detection signature [HEURISTIC]:** in ≥ 50% of half-court possessions the first ball SCREEN is set by a player who, 2 s before the screen, was within 1.2 m of the nail (r 3.5–5.0, θ 75–105°), for a handler at r 6.8–9.0, θ 75–105°.
- **Teams documented:** Purdue 2024-25 (KenPom adj. offence 10th, tempo 307th at 2 Jan 2025) `[B48][B49]`; 2025-26 ("played through their point guard on nearly every possession" `[B68]`; "nation's best offense" `[B52]`; `[B53]`).
- **Sources:** `[B48][B49][B52][B53][B68]`.
- **Confidence:** high (2024-25); medium (2025-26).

#### A2.11 "Jet" (Michigan early offense) — NEW (F2.6)
- **Name and aliases:** "Michigan Jet" / "motion jet action" (FastModel). No college alias found; NBA "Jet" usage varies.
- **Family / sub-family:** F2.6 named secondary break; contains a stack-sprint (elevator-like) action and an F5.5 reject.
- **Start alignment `[B19]`:** 1 with the ball on the right side above the elbow, read as the right slot (7.3, 70) (interpretation **unverified**); 2 behind the arc on the left (7.2, 140); 3 and 4 stacked on the strong-side block (2.0, 24) and (2.4, 39); 5 trailing toward the ball (screen spot ≈ (7.3, 80)).
- **Roles:** 1 handler (rejects); 3 shooter; 4 stack partner/screener; 2 baseline runner to the strong-side short corner; 5 ball screener (decoy).
- **Ordered actions `[B19]`:** (1) 3 and 4 sprint together from the block to the high post, t ≈ 0–1.5 s; (2) 2 sprints along the baseline to the strong-side short corner (4.5, 8), 0.5–2.5 s; (3) 5 ball-screens for 1, 1.5–3 s; (4) 1 **rejects** and passes to 3, "ready to catch and shoot", 3–4.5 s; (5) 4 and 5 crash. Step (4) wording on the page is garbled; tags EARLY OFFENSE, ELEVATOR SCREEN, BALL SCREEN, NEED A 3.
- **Usual counters:** the reject is the scoring read `[B19]`; others **unverified**.
- **Detection signature [HEURISTIC]:** early window (t 4–10 s after possession start); two players within 1.2 m of each other at r < 2.5 accelerate together (both ≥ 3 m/s, headings within 30°) to r 4–5.5, θ 60–120° within 1.5 s; a weak-side perimeter player runs the baseline (y < 1.0) to r 4–5, θ ≤ 15° on the strong side; a ball SCREEN is approached but the handler moves away from the screener (reject) and the next pass goes to one of the sprinters, either after he relocates to r ≥ 6.6 within 1.5 s of reaching the high post (tag 3PA) or at r ≥ 4.0 (tag 2PA), for an FGA ≤ 1.0 s after the catch.
- **Teams documented:** Michigan 2024-25 (vs UC San Diego, 2025 NCAA R64; FastModel 22 Mar 2025) `[B19]`.
- **Sources:** `[B19]`.
- **Confidence:** medium.

#### A2.12 Double drag entered by a screen-the-screener stagger (Purdue) — RICHER (extends F2.1 "Double drag")
- **Name and aliases:** Double Drag PnR (FastModel/Purdue).
- **Family / sub-family:** F2.1 drag family; new entry (5 screens 3, then 3 and 5 stagger for 4).
- **Start alignment [HEURISTIC]:** 1 advancing at the deep slot (9.0, 80); 3 and 5 trailing at the lane line; 4 low; 2 opposite wing.
- **Roles:** 5 first screener and second drag screener; 3 screener for 4; 4 first drag screener; 1 handler.
- **Ordered actions `[B8]`:** (1) 5 screens for 3, t ≈ 0–1 s; (2) 3 and 5 stagger for 4, 1–2.5 s; (3) 4 and 5 double-drag for 1, 2.5–4.5 s; (4) 1 reads.
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** early window; off-ball SCREEN(5→3), then within 1.0 s two stationary screeners (3, 5) aligned along 4's path (second screen ≤ 3 m beyond the first), then two ball SCREENs on 1 by 4 then 5 within 1.5 s of each other at r 7–9.5.
- **Teams documented:** Purdue 2023-24 (FastModel 11 Dec 2023) `[B8]`.
- **Sources:** `[B8]`.
- **Confidence:** medium.

#### A2.13 Pistol Flare Curl (Illinois) — NEW variant (extends F2.2 Pistol)
- **Name and aliases:** Pistol Flare Curl (FastModel; Basic Basketball tweet).
- **Family / sub-family:** F2.2 Pistol/"21".
- **Start alignment [HEURISTIC; source says only "out of pistol"]:** handler at the slot/wing (7.2, 40); guard in the strong-side corner (6.8, 5); big at the top (7.6, 90); weak side emptied.
- **Roles:** flare-screen user curls instead of flaring (lob target); weak side empty.
- **Ordered actions `[B15]`:** "curl the flare" and "empty the weak side" to clear help for the lob. Step order and timing **unverified**.
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** Pistol snapshot (§3.1) with no offensive player at \|x\| > 2 on the weak side; a flare SCREEN whose user turns toward the rim (path curvature toward the rim, ending r < 2) and receives a LOB (apex > 3.5 m) within 1.5 s of the screen.
- **Teams documented:** Illinois 2023-24 (FastModel 24 Mar 2024) `[B15]`.
- **Sources:** `[B15]`.
- **Confidence:** low (concept only).

#### A2.14 Michigan 2025-26 transition: rim-runner/corner lanes and the centre's long outlet — RICHER (extends F1.1 "Headman / pass-ahead" and F1.2)
- **Name and aliases:** primary break lane rules; long outlet by the centre.
- **Family / sub-family:** F1.1 / F1.2.
- **Start alignment:** DREB by the centre (Aday Mara, 2.21 m) `[B67][B69]`.
- **Roles:** centre = rebounder-outlet passer; lane runners "either sprinting to the rim to get an easy two or to the corner for a three" `[B68]`.
- **Ordered actions:** Mara "immediately spun and fired a two-hand pass down to … Lendeborg at the opposite 3-point line" (dunk) `[B69]`; full-court pass to McKenney vs Howard `[B67]`; 27 fast-break points vs Wake Forest `[B69]`. Timing [HEURISTIC]: rebound-to-pass ≤ 1.0 s; pass length ≥ 15 m.
- **Usual counters (defence):** Wake Forest doubled the bigs in the half court and pressured the ball `[B69]`.
- **Detection signature [HEURISTIC]:** after a DREB by a centre, first pass ≤ 1.0 s travelling ≥ 15 m to a teammate at r ≤ 7 of the attacked rim (y < 6); two lane runners reach r < 2 and r ≥ 6.6, θ ≤ 12°/≥ 168° within 4 s of the rebound.
- **Teams documented:** Michigan 2025-26 `[B67][B68][B69]`.
- **Sources:** `[B67][B68][B69]`.
- **Confidence:** medium.

#### A2.15 Fake pin-down → mid-post seal ("show the pin-down, give the post-up") (Purdue) — NEW (F7 + F8.1 decoy)
- **Name and aliases:** described, not named (Hammer & Rails, Purdue vs McNeese; the game was the 2025 NCAA second round (round of 32) `[V1]` — `[B48]` itself states no round). Designed against switch-everything defences.
- **Family / sub-family:** F7 mid-post seal with an F8.1 decoy screen.
- **Start alignment `[B48]`:** 1 (Smith) top (7.6, 90) → passes to 2 (Loyer) on the right wing (7.2, 40) and cuts to the right corner (6.8, 5); 3 (Cox) starts at the right block/dunker (2.7, 6); 4/5 (Kaufman-Renn) at the nail (4.19, 90), then at the right lane line (3.95, 62) as the "screener".
- **Roles:** Loyer entry passer; Cox decoy cutter up the lane; Kaufman-Renn fake screener then post; Smith corner spacer holding the help.
- **Ordered actions `[B48]`:** (1) 1→2 wing entry, 1 to the corner, t ≈ 0–2 s; (2) 3 cuts straight up the lane toward the top as if using a pin-down, 2–3.5 s; (3) the "screener" does not screen: he pivots and shows his numbers to the wing for a mid-post seal while his defender stays high to switch the non-existent screen, 3–4 s; (4) entry pass leading him to the rim, dunk (help from the corner held by Smith), 4–5 s; (5) if not open, 3 pops to the top to reset.
- **Usual counters:** the real pin-down to Cox at the top if the defender does not cheat `[B48]`.
- **Detection signature [HEURISTIC]:** a player cuts from r < 3 up the lane (Δy ≥ 4 m in ≤ 1.5 s) passing within 1.5 m of a teammate who never becomes stationary toward him (no SCREEN) and instead turns to face the ball wing (orientation change ≥ 90°) at r 2.5–4.0, θ 30–70°; entry pass from the wing to him within 1.5 s; ball-side corner occupied.
- **Teams documented:** Purdue 2024-25 (vs McNeese, opening possession `[B48]`; 2025 NCAA second round at Providence, Purdue won 76-62 `[V1]`; the date 22 Mar 2025 is inferred from `[V1]`'s "Thu/Sat" slot in the 22–23 Mar round — Saturday = 22 Mar — and is not stated in `[B48]`, which is dated 25 Mar 2025).
- **Sources:** `[B48]`.
- **Confidence:** high.

#### A2.16 Stagger Curl Through (Purdue) — NEW
- **Name and aliases:** Stagger Curl Through (FastModel): stagger curl → pin-down → curl into a DHO, dive and replace.
- **Family / sub-family:** F8.1 stagger + F6 DHO (Zoom-like, via a stagger first).
- **Start alignment [HEURISTIC]:** 1 top (7.6, 90); 2 at the block (2.0, 24); 4 and 5 as a stagger on the lane line (3.95, 62)/(2.4, 39); 3 opposite wing.
- **Roles:** 2 scorer; 4, 5 stagger screeners; 5 wing-flash handoff big; 1 pin-down screener then replace.
- **Ordered actions `[B9]`:** (1) 4 and 5 stagger for 2, who curls to the (opposite) elbow, t ≈ 0–2 s; (2) 5 flashes to the wing, 1→5, 2–3 s; (3) 4 opens to the corner; 1 down-screens for 2, who curls into a DHO from 5, 3–5 s; (4) 5 dives, 1 replaces 2 at the arc; 2 attacks and picks the pass, 5–7 s. The page says both "elbow" and "opposite elbow".
- **Usual counters:** dive/replace reads `[B9]`.
- **Detection signature [HEURISTIC]:** two consecutive off-ball SCREENs on one user (second screener 2–4 m beyond the first along the path), user ends at r 4–5, θ 55–125° (curl); a big catches at the wing (r 6.6–8, θ 25–55°); SCREEN(down) for the same user, then DHO(big→user) within 1.5 s at r 5.5–7.5; the big's radial velocity ≤ −1.5 m/s within 1.0 s after the DHO.
- **Teams documented:** Purdue 2023-24 (vs Gonzaga `[B9]`; FastModel 31 Mar 2024). `[B9]` gives no round or date. Purdue beat Gonzaga 80-68 in the 2024 NCAA Sweet 16 on 29 Mar 2024 `[V2]`, which fits the FastModel date, but that the play comes from that game is **unverified**.
- **Sources:** `[B9]`.
- **Confidence:** medium-high.

#### A2.17 Stack Under "3" (Purdue box) — NEW (extends F3.3 Box sub-family)
- **Name and aliases:** Stack Under "3" (FastModel).
- **Family / sub-family:** F3.3 Box/Stack → F7 post entry → F8.1 back/"under" screen for a shooter.
- **Start alignment `[B2]`:** 2 right elbow (4.57, 66.4); 4 right block (2.0, 24); 5 left block (2.0, 156); 3 left elbow (4.57, 113.6) (inferred, **unverified**); 1 top (7.6, 90).
- **Roles:** 2 shooter; 3 entry wing; 5 post; 4 curl screener then under/back screener; 1 spacer.
- **Ordered actions `[B2]`:** (1) 2 curls off 4 to the weak-side block, t ≈ 0–1.5 s; (2) 3 comes off 5's screen and catches on the wing, 1–2.5 s; (3) 3 enters to 5; 1 spaces away, 2.5–3.5 s; (4) on the post catch 4 dives to the weak-side block and screens for 2, 3.5–4.5 s; (5) 2 catches at the top for three, 4.5–6 s.
- **Usual counters:** post score if no help; three for 2 when his defender helps `[B2]`.
- **Detection signature [HEURISTIC]:** Box snapshot; within 1.5 s an elbow player curls to the weak block (Δθ ≥ 80°, ending r < 2.5); wing catch then entry to r < 3.0 within 1.0 s; then a SCREEN at r < 3.0 on the weak side whose user moves from the block to r 7–8, θ 75–105° and receives within 1.5 s (FGA from r ≥ 6.75).
- **Teams documented:** Purdue 2023-24 (FastModel 16 Mar 2024) `[B2]`. Gender not stated on the source page; men's attribution **unverified** (A2 scope rule).
- **Sources:** `[B2]`.
- **Confidence:** medium-high.

#### A2.18 Iverson curl → flare for the handler → elevator (Northwestern) — NEW chain
- **Name and aliases:** Iverson Elevator (FastModel; Basic Basketball "Iverson curl into flare and an elevator").
- **Family / sub-family:** F8 off-ball chain (Iverson → F8.1 flare → elevator).
- **Start alignment [HEURISTIC]:** 1-4 high: 1 top (7.6, 90); 4, 5 elbows (4.57, 66.4)/(4.57, 113.6); 2, 3 wings (7.2, 40)/(7.2, 140).
- **Roles:** Iverson cutter; handler (flare user); two elevator screeners and the elevator user.
- **Ordered actions `[B31]`:** (1) Iverson curl; (2) flare for the handler; (3) elevator. Timing and personnel **unverified** (video).
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** within 8 s: lateral CUT across y 4–6 past two stationary elbow players → SCREEN whose user is the original handler moving away from the ball (angle > 120°) → two stationary screeners shoulder to shoulder (gap 1.0–1.2 m) that close to < 0.6 m after a cutter passes between them.
- **Teams documented:** Northwestern 2023-24 (FastModel 21 Mar 2024; tweet 9 Mar 2024) `[B31]`.
- **Sources:** `[B31]`.
- **Confidence:** low-medium.

#### A2.19 Stagger (misdirection) into a Horns back screen (Nebraska) — NEW
- **Name and aliases:** Stagger to Horns Back Screen (FastModel; Basic Basketball).
- **Family / sub-family:** F3.2 Horns + F8.1 back screen.
- **Start alignment [HEURISTIC]:** starts as a stagger for a wing and ends in Horns: 1 top (7.6, 90); bigs at the elbows at the back-screen moment; shooters in the corners.
- **Roles:** stagger user = decoy; back-screen user = rim cutter.
- **Ordered actions `[B28]`:** "Nebraska using a stagger for a misdirection to set up a horns back screen"; steps beyond that **unverified**.
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** stagger whose user does not receive the ball, followed within 3 s by a Horns snapshot and a back SCREEN (user moving −y toward the rim from r ≥ 6) by an elbow player.
- **Teams documented:** Nebraska 2023-24 (tweet 12 Feb 2024; FastModel 21 Mar 2024) `[B28]`.
- **Sources:** `[B28]`.
- **Confidence:** low.

#### A2.20 "Inverted stagger" — NEW term (definition unverified)
- **Name and aliases:** inverted stagger (FastModel; A Quick Timeout). **Neither opened source defines it**; in both, two players screen in sequence and the action produces a lob or shot for someone other than the obvious user.
- **Family / sub-family:** F8.1 screen geometry class (proposed).
- **Start alignment / ordered actions:** Illinois "Winner SLOB" (A2.35): 5 and 3 set an inverted stagger for 4, and 1 lobs to 5 (the first screener is the lob target) `[B16]`. Nebraska 5-out ATO: if the 5 does not score off a DHO + weak-corner back screen, "the 3 and 4 set an inverted stagger screen to free the 2" `[B44]`.
- **Roles / counters:** **unverified**.
- **Detection signature [HEURISTIC; operational meaning proposed, unverified]:** two screeners set screens in sequence for one user **with the user moving toward the baseline (−y) rather than toward the ball/arc**, or the first screener immediately cutting to the rim for a LOB.
- **Teams documented:** Illinois 2023-24 `[B16]`; Nebraska 2025-26 (the article also mentions "Hoosiers", so team identity is partly unclear) `[B44]`.
- **Sources:** `[B16][B44]`.
- **Confidence:** low.

#### A2.21 Big-handled side DHO / side PnR to the free-throw line (Indiana, Woodson) — NEW action entry
- **Name and aliases:** "side pick and roll / dribble hand-off" game; "run the offense from the free-throw line" (Hammer & Rails).
- **Family / sub-family:** F6 side DHO → F5 side PnR; target zone the nail for a facilitator.
- **Start alignment `[B50]`:** big (Trayce Jackson-Davis) handling at the top (7.6, 90); facilitator wing (Galloway) on a wing (7.2, 40); scorer (Hood-Schifino) at the weak-side slot/top ≈ (7.6, 110); others pinning defenders low.
- **Roles:** big = handler, DHO giver and roller; wing = facilitator; weak-side guard = shooter who steps into the open pocket.
- **Ordered actions `[B50]`:** (1) the big dribbles at the rim protector to push him under the rim, t 0–2 s; (2) pass to the wing, then a DHO with the wing, 2–4 s; (3) the wing turns the corner and stops at the nail, 4–5.5 s; (4) reads: top-side help commits → weak-side guard steps into the open three; drop big stays back → nail pull-up; big steps up late → lob to the rolling big, 5–7 s.
- **Usual counters:** the defending big must step up early; switching was apparently planned by Purdue `[B50]`.
- **Detection signature [HEURISTIC]:** the handler is the tallest offensive player at r 6.6–8.5 for ≥ 2 s; DHO(big→wing) at r 6.0–7.5, θ 25–60°; the receiver's path ends at r 3.8–4.8, θ 75–105° with speed < 1.0 m/s for ≥ 0.4 s; next pass within 1.5 s to a weak-side player at r ≥ 6.75 or the big at r < 2.0.
- **Teams documented:** Indiana 2022-23 film, previewed as the plan vs Purdue (Jan 2024) `[B50]`; 2023-24 use **unverified**.
- **Sources:** `[B50]`.
- **Confidence:** medium.

#### A2.22 Michigan high-post hub centre with basket cutters (2025-26) — RICHER (extends F7 "Pinch post")
- **Name and aliases:** high-post offence through the centre; pinch post.
- **Family / sub-family:** F7 high-post hub / F8.2 basket cuts.
- **Start alignment `[B67]`:** centre (Mara, 2.21 m) at the nail (4.19, 90) or an elbow (4.57, 66.4); wings and guards above the arc; cutters from the wings/corners.
- **Roles:** hub centre; cutters (Gayle, Johnson); lob passer Cadeau.
- **Ordered actions `[B67]`:** high-post catch; "he easily found cutters to the basket"; Gayle: "if I just cut hard he'll be able to find me"; backdoor pass to Johnson for a dunk; lobs. Mara: "We don't play with sets or plays" `[B68]`. Further Cadeau-to-Mara lobs vs Ohio State appear only in a search summary — **unverified**.
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** the tallest player catches at r 3.8–5.0, θ 60–120° and holds ≥ 1.0 s; within 2.0 s a perimeter teammate CUTs toward r < 2 and receives (bounce or lob).
- **Teams documented:** MSU (pinch post `[S12][S27]`; Cooper high-post passing 2025-26, A1.9); Michigan 2025-26 `[B67][B68]`.
- **Sources:** `[B67][B68]`.
- **Confidence:** medium.

#### A2.23 Wisconsin cross-screen post-up and Chicago action (2023-24) — RICHER (team confirmations for F7 "Cross-screen post" and F6 "Zoom / Chicago")
- **Name and aliases:** "Post Up" (cross-screen post-up); "Chicago Action".
- **Family / sub-family:** F7 cross-screen post; F6 Chicago.
- **Start alignment [HEURISTIC]:** Post Up: 2 switches sides; 3 and 5 cut low to the blocks (2.0, 24)/(2.0, 156); 1 top; 4 slot. Chicago: 1 and 2 on top; 5 elbow (4.57, 66.4); 4 low.
- **Roles:** Post Up: 3 cross-screener, 5 post, 2 entry passer. Chicago: 1 DHO giver, 5 pop then back-screener then DHO giver and diver, 4 screener.
- **Ordered actions:** Post Up `[B33]`: 2 switches side, 3 cuts low, 1→4, 5 cuts low; 3 cross-screens for 5; 2→5; 5 reads. Chicago Action `[B34]`: 1 DHOs with 2; 5 pops to the elbow; 4 screens for 3; 2→3; 5 back-screens 2; 3→5; then 1 DHO with 5, 5 dives, 4 screens 2, 1 reads. Timings [HEURISTIC] ≈ 1–1.5 s per step.
- **Usual counters:** 5 reads (post); **unverified** beyond that.
- **Detection signature [HEURISTIC]:** Post Up: CROSS screen (\|Δx\| > 2\|Δy\|, y < 1.5) whose user catches at r < 2.5 within 1.5 s. Chicago: SCREEN(down) → DHO within 1.5 s (§F6 Zoom signature).
- **Teams documented:** Wisconsin 2023-24 (FastModel 22 Jan 2024) `[B33][B34]`.
- **Sources:** `[B33][B34]`.
- **Confidence:** medium.

#### A2.24 Patternless ball-screen offence (McCollum, Iowa 2025-26) — NEW system (F4.2)
- **Name and aliases:** "ball screens with no pattern": McCollum believes "in the ball screen, but does not believe in a set pattern for offense or set patterns for screens" (paraphrase in Staking the Plains) `[B62]`.
- **Family / sub-family:** F4.2 rule-based motion (read-based ball-screen continuity) / F5.
- **Start alignment [HEURISTIC]:** 4-out/5-out around one primary handler (Stirtz) at the top (7.6, 90) or slot (7.3, 70).
- **Roles:** Stirtz handler (93.7% of minutes; "constant ball-screen actions") `[B60]`; screeners "set them so many different ways" (switch, post up, pick-and-pop) `[B62]`; Folgueiras pick-and-pop big; Banks/Manyawu offensive rebounders and physical screeners `[B60]`.
- **Ordered actions / rules `[B60]`:** ball screen from varied angles → handler "great at hitting the pocket or the elbow" → short roll with a cutting option → mismatch hunting via switches. Pace: average possession length **19.9 s (363rd of 365)**, adj. tempo 62.7 (361st), eFG 56.3% (18th).
- **Usual counters:** defend the ball screen, stay down on fakes `[B60]`.
- **Detection signature [HEURISTIC]:** ≥ 60% of half-court possessions contain ≥ 1 ball SCREEN for the same handler; Shannon entropy of screener orientation (8 bins of 45°) ≥ 2.5 bits over ≥ 20 ball screens; median time from possession start to FGA ≥ 18 s; team average possession length ≈ 19–20 s.
- **Teams documented:** Iowa 2025-26 `[B60][B61]`; McCollum at Northwest Missouri State (context) `[B62]`.
- **Sources:** `[B60][B61][B62]`.
- **Confidence:** medium.

#### A2.25 Free-flow "no sets", transition-first offence (Michigan, May) — RICHER (extends F4.2 "Michigan (Dusty May)")
- **Name and aliases:** free-flowing offence.
- **Family / sub-family:** F4.2 / F1.
- **Start alignment:** varies (transition lanes; see A2.14).
- **Roles:** see A2.14 and A2.22.
- **Ordered actions / evidence:** "We don't play with sets or plays, so it's easier like that to create" (Mara); "don't walk the ball up"; lanes to the rim or corner `[B68]`; Michigan "branched out from its typical sets" vs Howard `[B67]` — the two statements conflict; treat "no sets" as player hyperbole. 2024-25: "relatively few downhill attacks from their guards and wings"; threes mostly from post kick-outs and off-ball screens; spot-up usage 13th percentile `[B70]`.
- **Usual counters:** double the bigs, pressure the ball (Wake Forest) `[B69]`.
- **Detection signature [HEURISTIC]:** ≥ 30% of possessions with the first FGA ≤ 10 s after possession start, and a template-match rate < 20% (share of possessions whose ALIGN start plus action order matches any stored set).
- **Teams documented:** Michigan 2024-25 `[B70]`; 2025-26 `[B67][B68][B69]`.
- **Sources:** `[B67][B68][B69][B70]`.
- **Confidence:** medium.

#### A2.26 Medved Chin variation: passer clears to the weak corner; corner big flares then slips (Minnesota) — NEW variant (extends F3.1 "Chin" / Princeton)
- **Name and aliases:** "Chin quick hitters" (A Quick Timeout).
- **Family / sub-family:** F4.1/F4.2 Princeton family → Chin.
- **Start alignment `[B46]` [HEURISTIC coordinates]:** Princeton 2-guard front: 1 and 2 at the slots (7.3, 70)/(7.3, 110); 5 at the high post/elbow (4.57, 113.6) receives the entry; 4 in a corner (6.8, 175); 3 opposite wing.
- **Roles:** 1 passer who clears to the **weak-side** corner (instead of the usual strong-side corner); 5 entry receiver; 4 corner man who flares for 2 then slips; 2 shooter.
- **Ordered actions `[B46]`:** (1) 1 clears to the weak-side corner, t 0–1.5 s; (2) entry to 5, 1–2.5 s; (3) 4 flares for 2, then slips to the rim, 2.5–4 s; (4) defenders drop to the cutter → 2 open on the wing; defenders stay high → 4 open on the slip, 4–5 s. Related Medved (Colorado State, 2023-24) action `[B47]`: early handoff → guard exchange → loose Chin → "Point Over" (the big fakes a DHO; on the overplay the wing back-cuts for a layup). "Burn-cut" and "naked layup" language for Minnesota appears only in a search summary — **unverified**.
- **Usual counters:** flare/slip read `[B46]`; backdoor on DHO overplay `[B47]`.
- **Detection signature [HEURISTIC]:** 2-guard-front snapshot; pass to r 3.8–5.0 while the passer runs to the opposite-side corner (θ crosses 90°, ends θ ≥ 168° or ≤ 12° away from the receiver); within 1.5 s a corner player moves up to screen a wing (flare: user moves away from the ball) and then accelerates to r < 2.0 (slip).
- **Teams documented:** Minnesota 2025-26 (Medved; practice observation, Jan 2026) `[B46]`; Colorado State 2023-24 (pre-Big Ten) `[B47]`.
- **Sources:** `[B46][B47]`.
- **Confidence:** medium.

#### A2.27 Nebraska five-out: "Dribble at Burn" and the 5-out ATO (Hoiberg) — NEW named actions (extends F4.2 "Nebraska (Hoiberg) / Davidson")
- **Name and aliases:** Dribble at Burn; 5-Out ATO.
- **Family / sub-family:** F10 5-out / F6 DHO / F8.2 backdoor ("burn"); ATO = F13.1.
- **Start alignment:** 5-out: top (7.6, 90), wings (7.2, 40)/(7.2, 140), corners (6.8, 5)/(6.8, 175); the 5 holds one perimeter spot.
- **Roles:** 1 PG and backdoor cutter; 4 and 5 DHO/flare pair; 5 dribble-at big; ATO: weak-side corner back-screener, 2 stagger user.
- **Ordered actions:** Dribble at Burn `[B45]`: (1) swing and hand back to the PG, t 0–3 s; (2) DHO with a flare between the 4 and 5, 3–5 s; (3) ball back to the 5, who dribbles at the corner; when X1 moves to guard the DHO, 1 back-cuts for an uncontested finish, 5–7 s. 5-Out ATO `[B44]`: (1) DHO involving the 5, 0–2 s; (2) the weak-side corner back-screens for the 5, 2–3.5 s; (3) if the 5 is not open, 3 and 4 set an inverted stagger to free the 2, 3.5–6 s.
- **Usual counters:** backdoor when the defender jumps the DHO `[B45]`.
- **Detection signature [HEURISTIC]:** 5-out snapshot (nobody at r < 6) → hand-back/DHO chain (≥ 2 DHOs in ≤ 6 s) → a big dribbling toward a corner occupant (velocity toward him ≥ 2 m/s, distance closing to < 2 m) → the receiver's BACKDOOR to r < 2.0 with the catch within 1.0 s.
- **Teams documented:** Nebraska 2023-24 `[B45]`; Nebraska 2025-26 ATO (article Jan 2026; text also says "Hoosiers" → team attribution partly **unverified**) `[B44]`.
- **Sources:** `[B44][B45]`.
- **Confidence:** medium (Burn); low-medium (ATO).

#### A2.28 Team system profiles (2024-26) — RICHER (team confirmations for F4.2 / F10 / F14 / F17 rows)
| Team, season | Profile | Family | Detection signature [HEURISTIC] | Keys | Confidence |
|---|---|---|---|---|---|
| Nebraska 2025-26 | 5-out with stretch 5 ("John Beilein's offense" shorthand); 51% of shots are threes (11th); assists 10th; "abandons the offensive boards to prevent transition"; stretch-5 Rienk Mast highest usage, posts smaller defenders; Pryce Sandfort movement shooter; slow | F10 5-out / F14 retreat | 3PA/FGA ≥ 0.48; crash count ≤ 1 (≤ 1 attacker at r < 3 when the shot hits the rim) on ≥ 70% of misses; the 5 at r ≥ 6 for ≥ 50% of half-court time | `[B66]` | medium |
| Penn State 2024-25 | "essentially play 5-out with the post open"; Baldwin high PnR with 2.13 m rim-runner Konan Niederhauser and lobs; Zach Hicks parked in the corner during the PnR; basket cuts; push after makes and misses; full-court diamond press at the end of halves (defence) | F10 / F5 | no attacker at r < 4 for ≥ 70% of half-court time before the first action; top ball SCREEN then LOB to the roller at r < 1.5 within 2.0 s; screen-side corner occupied | `[B51]` | medium |
| Wisconsin 2025-26 | four-guard small-ball five-out (scored on 7 of 8 possessions in a 3:39 stretch vs Michigan, +9); shooting forced Michigan "to hug the three-point line"; corner-turning ball screens with kick/drive/dump reads; switch 1-5 on defence; "a ton of pick-and-roll and pick-and-pop"; top-15 3PA rate | F10 / F5 | lineup with ≤ 1 player ≥ 2.03 m; 5-out snapshot; ball SCREEN by a guard or wing | `[B58][B59]` | medium |
| Indiana 2025-26 (DeVries) | read-based three-point offence: slip and ghost screens, off-ball screens and cutting, skip passes, occasional post-ups and backdoors `[B65]`; drive-and-kick, inside-out, pick-and-pop; took the three whenever the defence went under a screen; twos at the rim in transition, off backdoors and PnR `[B64]`. "50.5% of FGA from three (14th)" — **unverified** (search summary only) | F10 / F5.4 | SLIP + GHOST ≥ 20% of ball screens; FGA from r ≥ 6.75 within 1.0 s after an under-screen coverage | `[B64][B65]` | low-medium |
| Maryland 2025-26 (Buzz Williams) | Rice and Adams initiate via ball screens; Payne and Washington "devastating screen setters"; three bigs crash the offensive glass as the main efficiency source (Texas A&M mould: sub-240 team 3P% all six years, top-5 OR% the last three; early 2025-26 Maryland OR% 35.2%) | F5 / F14 | crash count ≥ 3 on ≥ 50% of misses; ball SCREEN as the first action | `[B63]` | medium |
| Illinois 2025-26 | Tyler Underwood's "Gold, Silver and Bronze" shot-choice medals; "never about the action that you run"; KenPom adj. offence 130.5 (No. 1 in KenPom history at 29 Jan 2026); corner players crash the offensive glass | F17 outcome / F14 | shot-quality tiers from location × defender distance; corner-crash rate | `[B53][B55]` | medium |
| UCLA 2025-26 (Cronin) | transition led by Donovan Dent; Dent top PnR to a rolling big or shooter; shooting centre Xavier Booker `[B71]`; "doesn't get a lot of three pointers up" `[B52]` | F1 / F5 | Dent as handler in ≥ 50% of ball screens; transition share from the Job D flags | `[B71][B52]` | low |
| Washington 2025-26 (Sprinkle) | "play fast … get our guards downhill. Bigs in front of the rim … a lot more threes" (stated intent) | F1 / F10 | ≥ 25% of FGA within 10 s of possession start; 3PA/FGA tracked against stated intent | `[B72]` | low |
| Oregon (Altman) | spread roots (Johnny Orr / Iowa State), position-less, FT-line screening, back cuts — 2017 description [pre-window]; 2024-25 detail not found | F4.2 | not implementable until a 2024-26 description is opened | `[B74]` | low |

USC, Ohio State, Rutgers (beyond A2.5) and Minnesota (beyond A2.26): no opened source with set-level detail for 2023-26.

#### A2.29 Double Elevator BLOB (Michigan) — NEW (content unverified)
- **Name and aliases:** "Michigan: Double Elevator" (PGC Basketball post quoted by A Quick Timeout).
- **Family / sub-family:** F13.2 BLOB → elevator (existing generic row: Box "Elevator / Elevator + stagger").
- **Start alignment:** **unverified** (embedded video not described). Template [HEURISTIC]: inbounder (3.3, −35); two elevator pairs at both lane lines (3.95, 62)/(3.95, 118), or the ball-side lane line and the top.
- **Roles / ordered actions:** **unverified**; the name implies two elevator ("closing doors") screens in sequence or at once.
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** ball out of bounds at y < −1.6; two pairs of stationary screeners each with a 1.0–1.2 m gap; within 2.5 s of the handover at least one cutter passes through a gap and both screeners close to < 0.6 m within 0.3 s; a second gap event within 1.5 s.
- **Teams documented:** Michigan 2025-26 (post dated 14 Jan 2026; 423K views) `[B1]`.
- **Sources:** `[B1]`.
- **Confidence:** low (existence high; content **unverified**).

#### A2.30 3 Low Flare BLOB (Michigan) — NEW
- **Name and aliases:** 3 Low Flare (A Quick Timeout).
- **Family / sub-family:** F13.2 BLOB → cross screen + flare.
- **Start alignment [HEURISTIC]:** inbounder (3.3, −35); 3 low at the block (2.0, 24); 5 on the opposite block (2.0, 156); 2 on the far side/wing; 4 high.
- **Roles:** 5 first target (freed by a cross screen); 3 cross-screener then flare-screener; 2 shooter fading away from the ball.
- **Ordered actions `[B1]`:** (1) cross screen frees the 5, t 0–1.5 s; (2) 3 screens for 2, who fades (flare), 1.5–3 s; (3) catch-and-shoot three, 3–4 s.
- **Usual counters:** inbound to the 5 on the cross screen (first option) `[B1]`.
- **Detection signature [HEURISTIC]:** CROSS screen at y < 1.5 within 1.0 s of the handover; the inbound goes to the cross-screen user (r < 3) or is withheld; then a SCREEN by the same cross-screener whose user moves away from the ball (angle > 120°) ending at r ≥ 6.75; pass and FGA ≤ 1.0 s after the catch.
- **Teams documented:** Michigan 2025-26 `[B1]`.
- **Sources:** `[B1]`.
- **Confidence:** medium.

#### A2.31 Pin Down BLOB (Michigan, 2025 NCAA) — NEW
- **Name and aliases:** Michigan Pin Down BLOB (FastModel).
- **Family / sub-family:** F13.2 BLOB → down screen.
- **Start alignment `[B20]`:** 1 inbounds (3.3, −35); 4 ball-side block (2.0, 24); 3 ball-side elbow (4.57, 66.4); 2 weak-side elbow (4.57, 113.6) (number inferred, **unverified**); 5 top (7.6, 90).
- **Roles:** 3 pin-down screener ("holds tight"); 4 user who sprints above the ball-side elbow; 2 and 5 crashers / return-pass options.
- **Ordered actions `[B20]`:** (1) 3 pins down for 4; 4 sprints above the ball-side elbow; 3 holds, t 0–1.5 s; (2) 1→4, 1–2.5 s; (3) 2 and 5 crash on the pass and sprint to the ball-side lane for a return pass from 4; open three per the description, 2.5–4 s.
- **Usual counters:** return pass to a crasher `[B20]`.
- **Detection signature [HEURISTIC]:** ball out of bounds; SCREEN(down) at r 2.5–4.5 on the ball side within 1.0 s; the user's path runs from the block to r 5–7, θ 55–80°; inbound to that user ≤ 1.0 s after the screen.
- **Teams documented:** Michigan 2024-25 (vs Texas A&M `[B20]`; FastModel 24 Mar 2025). `[B20]` gives no round. Michigan beat Texas A&M 91-79 in the 2025 NCAA second round (R32) `[V1]`, consistent with the FastModel date; the link of the play to that game is inferred.
- **Sources:** `[B20]`.
- **Confidence:** medium.

#### A2.32 Stack Curl BLOB (Purdue and Illinois, 2024 NCAA) — NEW (extends F13.2 "Stack")
- **Name and aliases:** Stack Curl BLOB (both FastModel titles).
- **Family / sub-family:** F13.2 BLOB → stack.
- **Start alignment:** Purdue `[B12]`: all four inbound options stacked on a diagonal just inside the arc [HEURISTIC: from (2.4, 39) to (5.8, 60) on the ball side]; 5 in the lane. Illinois `[B18]`: 1 and 2 stacked; 5 a screener near the ball-side block.
- **Roles:** Purdue: 1 corner cutter off a double stagger; top of the stack curls and screens; first stagger screener pops; 5 posts. Illinois: 1 and 2 read pair; 5 screener then safety inbound.
- **Ordered actions:** Purdue `[B12]`: (1) 1 uses a double stagger to the corner, t 0–1.5 s; (2) the top of the stack curls and screens the first stagger screener, who pops outside the arc, 1–2.5 s; (3) 5 posts in the lane at once; (4) others spread 4-out 1-in. Illinois `[B18]`: (1) if 1 stays put, 2 curls around 1 to seal his defender and score; (2) otherwise 1 uses 5's screen to catch in the corner, or cuts to the corner first; (3) if 1 is not open, 2 curls off 5 for a rub score; 5 backpedals as the safety.
- **Usual counters:** curl vs corner-cheating defender `[B18]`.
- **Detection signature [HEURISTIC]:** ball out of bounds; ≥ 3 attackers with consecutive-neighbour distance ≤ 1.5 m along a fitted line (stack; diagonal if the line is 25–65° to the baseline; canonical rule A11.21); within 1.0 s one stack member curls around another toward the rim (ending r < 2.0) and another exits to the corner (r ≥ 6.6, θ ≤ 12° or ≥ 168°).
- **Teams documented:** Purdue 2023-24 (FastModel 28 Mar 2024) `[B12]`; Illinois 2023-24 (FastModel 28 Mar 2024) `[B18]`.
- **Sources:** `[B12][B18]`.
- **Confidence:** medium.

#### A2.33 Duck-In BLOB (Purdue, decoy star post) — NEW
- **Name and aliases:** Duck In BLOB (FastModel).
- **Family / sub-family:** F13.2 BLOB → decoy + duck-in.
- **Start alignment:** "unconventional formation" (no coordinates) `[B11]`; **unverified**.
- **Roles:** 5 (Zach Edey) decoy; 4 screener/slipper into the vacated space; 1 safety inbound; 5 last-resort high-post target.
- **Ordered actions `[B11]`:** (1) 5 draws attention and cuts away, t 0–1 s; (2) 4 screens or slips into the vacated space, 0.5–2 s; (3) 1 flashes to the wing as the safe inbound, 1–2.5 s; (4) 5 to the high post; iso or a handoff from there.
- **Usual counters:** high-post iso/handoff `[B11]`.
- **Detection signature [HEURISTIC]:** ball out of bounds; the tallest player moves ≥ 2 m away from the inbounder within 1.0 s, and a second big reaches r < 2.0 on the ball side within 1.5 s and receives the inbound.
- **Teams documented:** Purdue 2023-24 (FastModel 28 Mar 2024) `[B11]`.
- **Sources:** `[B11]`.
- **Confidence:** low-medium.

#### A2.34 Stagger Twist BLOB (Illinois) — RICHER (content for the F13.2 "Twist BLOB" row, which had a title only)
- **Name and aliases:** Stagger Twist BLOB.
- **Family / sub-family:** F13.2 BLOB.
- **Start alignment [HEURISTIC]:** inbounder (3.3, −35); 4 and 5 stagger on the lane line (2.4, 39)/(3.95, 62); 2 at the block.
- **Roles:** 2 curl user; 4, 5 stagger screeners; 5 STS screener then slipper.
- **Ordered actions `[B17]`:** (1) 4 and 5 stagger for 2; 2 curls off the first screen, t 0–1.5 s; (2) 5 screens for 4, then slips to the rim, 1.5–3 s.
- **Usual counters:** slip to the rim `[B17]`.
- **Detection signature [HEURISTIC]:** ball out of bounds; stagger with the user curling at the first screen (ends r < 3); then the second screener sets an off-ball SCREEN for the first screener (STS) and reaches r < 1.5 within 0.8 s (slip).
- **Teams documented:** Illinois 2023-24 (FastModel 24 Mar 2024) `[B17]`. MSU "Twist BLOB" `[S25]` is a different (Winston) action.
- **Sources:** `[B17]`.
- **Confidence:** medium.

#### A2.35 Winner SLOB (Illinois; inverted-stagger lob) — NEW
- **Name and aliases:** Winner SLOB (FastModel). "Winner" also titles a UCLA 2023 "Box Winner BLOB" (a version of Brad Stevens' "Winner") seen in a listing [pre-window, gender not stated] `[B78]`.
- **Family / sub-family:** F13.3 SLOB.
- **Start alignment [HEURISTIC]:** inbounder at the SLOB mark (10.5, 41); 5 and 3 in a stagger above the ball-side elbow; 4 below them.
- **Roles:** 5 first screener and lob target; 3 second screener; 4 decoy user; 1 inbounder.
- **Ordered actions `[B16]`:** (1) 5 and 3 set an inverted stagger for 4, t 0–1.5 s; (2) 1 lobs over the top to 5, 1–2.5 s. Tags NEED A 2, AFTER TIMEOUT.
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** ball out of bounds at \|x\| ≥ 7.62, y ≈ 6.9; two screeners in a stagger for a third player; the first screener cuts to r < 1.5 and receives a LOB within 1.5 s of the handover.
- **Teams documented:** Illinois 2023-24 (FastModel 30 Mar 2024) `[B16]`. Gender not stated on the source page (the page has no description); men's attribution **unverified** (A2 scope rule).
- **Sources:** `[B16]`.
- **Confidence:** medium.

#### A2.36 SLOB Top Iso (Maryland game-winner) — NEW
- **Name and aliases:** SLOB Top Iso (FastModel).
- **Family / sub-family:** F13.3 SLOB → F9 isolation; F13.4 end of game.
- **Start alignment [HEURISTIC]:** inbounder 1 at the SLOB mark (10.5, 41); 4 (Derik Queen) and 5 near the ball-side elbow/lane line (4.57, 66.4)/(3.95, 62); 2 at the top/slot; 3 weak side.
- **Roles:** 2 corner cutter (decoy); 5 screener; 4 receiver and isolation scorer; 1 inbounder.
- **Ordered actions `[B21]`:** (1) 2 cuts to the ball-side corner between 4 and 5, t_dispose + 0–1 s; (2) 4 cuts to the top off 5's screen, t_dispose + 0.5–1.8 s; (3) 1→4 = t_touch (game clock starts); (4) 4 attacks left into the open area for the winning shot, t_touch + 0–3.7 s (3.7 s on the clock, down 1).
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** game clock ≤ 5 s; SLOB; one cutter splits two teammates to the corner, then a big uses a down SCREEN to reach r 7–8, θ 75–105° and receives the inbound; his next action is a drive with all teammates at r ≥ 6.
- **Teams documented:** Maryland 2024-25 (FastModel 24 Mar 2025: down 1, 3.7 s, isolation for Derik Queen, game-winner with "a Sweet Sixteen trip on the line" `[B21]`; `[B21]` names no opponent, coach or round). Opened 2026-10-18: coach Kevin Willard `[V5]`; the game is the 2025 NCAA second round vs Colorado State, 23 Mar 2025, Seattle — Maryland trailed 71-70 with 3.6 s left after a timeout and Queen hit a buzzer-beating fadeaway for 72-71 `[V6][V5]`. The 3.7 s vs 3.6 s difference is between sources.
- **Sources:** `[B21]`.
- **Confidence:** high.

#### A2.37 Triple Curl BLOB (Northwestern, 0.7 s, designed for a game-winning shot) — NEW
- **Name and aliases:** Triple Curl BLOB (FastModel; "Northwestern Wildcats MBB").
- **Family / sub-family:** F13.2 BLOB / F13.4 end of game.
- **Start alignment [HEURISTIC]:** inbounder (3.3, −35); 2, 3 and 4 low/in the lane; 5 low, lifting to the elbow.
- **Roles:** 2 first curler (to the opposite block, then corner); 4 screener for 3, then STS shooter; 3 second curler; 5 lifting screener.
- **Ordered actions `[B29]`:** (1) 2 curls to the opposite block and on to the corner; 4 screens for 3; (2) 3 curls under 5, who lifts to the elbow; (3) 4 uses 5's screen and curls for the shot (STS). 0.7 s on the clock (catch-and-shoot).
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** game clock ≤ 1.0 s at the handover; three curl paths within 1.2 s; the screener of the second curl becomes the shooter; FGA ≤ 0.7 s after the catch.
- **Teams documented:** Northwestern 2024-25 (FastModel 17 Jan 2025) `[B29]`. `[B29]` gives the design intent (a game-winning shot with 0.7 s on the clock) but no outcome, opponent or game date, so no made game-winner is claimed.
- **Sources:** `[B29]`.
- **Confidence:** medium-high.

#### A2.38 Floppy UCLA BLOB (Northwestern) — NEW chain
- **Name and aliases:** Floppy UCLA (FastModel).
- **Family / sub-family:** F13.2 BLOB → Floppy → UCLA cut → high-low → DHO → PnR.
- **Start alignment [HEURISTIC]:** Floppy template (§3.1): two shooters under the rim (r < 1.5); screeners at the blocks/lane lines; PG at the top.
- **Roles:** Floppy shooters; top screener; PG UCLA cutter; 5 step-out big; weak-side big slicing into the post.
- **Ordered actions `[B30]`:** (1) Floppy, priority to the double-screen side, t 0–1.5 s; (2) the top screener sets a flat screen for the PG's UCLA cut to the rim, 1.5–3 s; (3) if not open, 5 steps out to catch while the PG screens for the weak-side big to slice into the post (high-low), 3–4.5 s; (4) if no high-low, 1 continues into a handoff; if 1 cannot get downhill, 1 and 5 go into PnR, 4.5–7 s.
- **Usual counters:** high-low; DHO; PnR `[B30]`.
- **Detection signature [HEURISTIC]:** out-of-bounds snapshot with two players under the rim; within 3 s a UCLA cut (top → block over a high screen); then a pass to a big at r 4–6 and a CUT by the other big into r < 2.5; then DHO and SCREEN by the same pair ≤ 2 s apart.
- **Teams documented:** Northwestern 2023-24 (FastModel 26 Mar 2024) `[B30]`.
- **Sources:** `[B30]`.
- **Confidence:** medium.

#### A2.39 Back Screen Lob clear-out (Oregon) — NEW
- **Name and aliases:** Back Screen Lob (FastModel; Basic Basketball).
- **Family / sub-family:** F13.1 ATO → F8.1 back screen → lob.
- **Start alignment:** right side cleared (others on the left) [HEURISTIC]; detail **unverified**.
- **Roles:** back-screener; lob user; passer.
- **Ordered actions `[B32]`:** clear out the right side, then a back screen for a lob. Detail **unverified** (video).
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** no attacker beyond \|x\| > 2 on one side for ≥ 1 s (clear-out), then a back SCREEN on that side and a LOB to the user at r < 1.5.
- **Teams documented:** Oregon 2023-24 (tweet 21 Mar 2024; FastModel 19 Apr 2024) `[B32]`.
- **Sources:** `[B32]`.
- **Confidence:** low.

#### A2.40 Other Big Ten BLOB / ATO entries (compact full format)
| Set | Family | Start alignment (r, θ) [HEURISTIC] | Roles | Ordered actions with timing [HEURISTIC timings] | Counters | Detection signature [HEURISTIC] | Team, season, key | Confidence |
|---|---|---|---|---|---|---|---|---|
| **Back Screen Stagger BLOB** (Michigan) | F13.2 BLOB → back screen → stagger | Inbounder (3.3, −35); box | 2 back-screener then stagger screener; 5 back-screen user; 4 stagger user | 0–1.5 s 2 back-screens 5; 1.5–3 s 2 sets a stagger for 4; 4 uses it; 1→4 | — | Back SCREEN within 1 s of the handover, then the same screener in a stagger ≤ 2 s later | Michigan 2023-24 (Howard) `[B25]` | medium |
| **Horns Quick Hitter (EOQ)** (Michigan) | F3.2 Horns / F13.4 | Horns (§3.1) | 1, 4 passers; 1+5 stagger; 3 back-cutter; 5 down-screener | 0–1 s 1→4; 1–2.5 s 1 and 5 stagger for 3, who back-cuts; 2.5–4 s 5 down-screens 1; 4→1 for three | Back-cut | Horns; elbow catch; stagger whose user back-cuts (heading reverses > 120°); down screen for the original passer and a pass to him at r ≥ 6.75 | Michigan 2023-24 (Howard) `[B26]` | medium |
| **BLOB** (Nebraska) | F13.2 BLOB / STS | Inbounder (3.3, −35); box | 2 wing cutter; 4, 3, 5 screen-and-dive chain | 0–1 s 2 cuts to the wing; 0.5–1.5 s 4 screens 5; 1–2 s 3 screens 4 and dives; 1.5–2.5 s 5 screens 2 and dives | Dives | Three sequential screen-then-dive events within 2.5 s of the handover | Nebraska 2023-24 `[B27]` | medium |
| **STS** (Iowa; "NCAA 2025-26 IOWA set") | F8.1 STS | 1 top; 2, 3 wings; 4 low; 5 high | 2 corner; 3 back-screener then shooter; 5 down-screener | 0–1 s 2 crosses to the corner, 3 cuts low; 1–2 s 3 back-screens 4, 4 low; 2–3 s 5 down-screens 3; 1→3 for the shot | — | Back SCREEN by *s*, then a down SCREEN for *s* ≤ 1.5 s later (STS), catch at r ≥ 6.75 | Iowa 2025-26 `[B22]` — men's vs women's **not stated (unverified)** | low |
| **Horns Spain for Edey** (Purdue) | F3.2 Horns → F5.6 Spain | Horns (§3.1) | 5 ball screener/roller; 4 Spain screener | 0–1.5 s 5 ball-screens 1; 1–2.5 s 4 Spain-screens 5's defender; rim look (foul drawn) | Spain pop | Horns; ball screen; back screen on the roller's defender ≤ 1 s later | Purdue 2023-24 (2024 Elite Eight vs Tennessee) `[B5]` — new Purdue confirmation of Spain | medium |

#### A2.41 3-Out Football press break (Purdue, end of game with a lead) — NEW (F12.2)
- **Name and aliases:** "3 Out Football Press Break" (FastModel).
- **Family / sub-family:** F12.2 named press breaks / F13.4.
- **Start alignment [HEURISTIC]:** backcourt end line: inbounder 3 out of bounds at (27.4, 90) in attacked-rim coordinates (far baseline); 2 also out of bounds (running the baseline after a make); 4 at the opposite end of the baseline, out of bounds; 1 and 5 in the backcourt near the far FT line (r ≈ 21.3–21.5, θ 80–100°; backcourt elbows (21.36, 85.1)/(21.36, 94.9)).
- **Roles:** 3 inbounder then sideline runner; 2 baseline receiver then come-back cutter; 4 second baseline receiver; 1 corner cutter off 5; 5 come-back receiver.
- **Ordered actions `[B13]`:** (1) 3→2 (2 out of bounds); (2) 2→4, who cuts out of bounds to receive; (3) 3 cuts down the sideline; (4) 2 cuts to the second lane marker and comes back to the ball; (5) 1 cuts off 5 toward the ball-side corner; (6) 5 comes straight back to receive from 4. No screens listed. Timing [HEURISTIC]: baseline passes within 4 s.
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** after an opponent make, two baseline passes with both passers beyond the far end line (y > 27.1 m) within 4 s; then one player sprinting along a sideline (\|x\| > 6.5) toward the frontcourt while two others come back toward the ball (radial speed toward the inbounder ≥ 2 m/s).
- **Teams documented:** Purdue 2023-24 (FastModel 6 Apr 2024) `[B13]`. Gender not stated on the source page; men's attribution **unverified** (A2 scope rule).
- **Sources:** `[B13]`.
- **Confidence:** medium.

#### A2.42 EOG Press Break 3 (Iowa, down 2 with 8.9 s) — NEW (F12.2 / F13.4)
- **Name and aliases:** "Iowa – EOG Press Break 3" (FastModel).
- **Family / sub-family:** F12.2 / F13.4.
- **Start alignment [HEURISTIC]:** inbounder 2 on the far end line (r ≈ 27, θ ≈ 90); 1 and 4 in the backcourt (4 as screener); 3 and 5 ahead.
- **Roles:** 2 inbounder (runs the baseline); 1 receiver off 4's screen, then ball-handler; 3 corner spacer/shooter.
- **Ordered actions `[B23]`:** (1) 2 fakes the pass, then runs the baseline as 1 cuts off 4; (2) 2 leads 1 with the pass; (3) 1 dribbles up the floor; (4) 3 cuts to the corner; (5) once 3's defender commits to the ball, 1→3 for an open look at a game-winning three `[B23]` (design intent; `[B23]` names Florida, 8.9 s, down 2, and gives no result or round). The made game-winning three is from `[B60]` (Folgueiras, "upset win"); the game was the 2026 NCAA second round (R32), Iowa 73-72 over No. 1 Florida `[V3]`. `[B60]` names Folgueiras as the game-winner shooter, so the number-to-player mapping is **unverified**.
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** game clock ≤ 10 s, trailing ≤ 3; the inbounder moves along the end line before passing; the receiver catches in stride (≥ 4 m/s) after cutting off a backcourt screen; ball crosses half-court ≤ 4 s after the catch; a teammate reaches a frontcourt corner (r ≥ 6.6, θ ≤ 12°/≥ 168°) and receives a kick for the FGA.
- **Teams documented:** Iowa 2025-26 (FastModel 24 Mar 2026) `[B23]`.
- **Sources:** `[B23][B60]`.
- **Confidence:** medium-high.

#### A2.43 Pace and possession-length figures (for Job D)
| Team | Season | Figure | Key |
|---|---|---|---|
| Iowa | 2025-26 | Average possession length 19.9 s (363rd of 365); adj. tempo 62.7 (361st) | `[B60]` |
| Purdue | 2024-25 (at 2 Jan 2025) | KenPom adj. offence 10th; tempo 307th | `[B49]` |
| Nebraska | 2025-26 | 51% 3PA rate (11th); "abandons the offensive boards to prevent transition" | `[B66]` |
| Michigan | 2025-26 | 27 fast-break points vs Wake Forest; 10 vs Oakland | `[B69]` |
| Illinois | 2025-26 | KenPom adj. offence 130.5 (No. 1 in KenPom history at 29 Jan 2026) | `[B55]` |
| Minnesota | 2025-26 | 362nd of 365 in adj. tempo — **unverified** (search summary; page not opened) | — |

**Excluded or ambiguous (opened, not used as men's evidence)** `[B88]`. Explicitly women's: Iowa WBB Box STS BLOB (458503); USC WBB Push Punch Double Stagger and Horns Exit (471774, 471773); UCLA Box Twirl (457360); Indiana PNP Stagger Flare and Shuffle Triple Curl (462263, 462264); Indiana Swing Single Double (461741; treated as WBB, **unverified**). Gender not stated: Iowa Stack Elevator BLOB (462603), Staggers Box BLOB (461924), Ram Exit Back Screen (461923), Point Split Action (460485); Ohio State Line SLOB (461960), Cross Screen BLOB (458453), 4 Flat Chicago Action BLOB (454962), Through Action Backdoor (454955); UCLA 4-High Back Screen (458506); Oregon Curl into Stagger (455590), Chicago Action BLOB (455589); USC Double Drag Stagger (454468), Through Post Up (452299); Washington Four High PNR (460169); Indiana Triangle BLOB (455762), 5 Out Collision Cross Screen (455761). Several would be new items if a men's attribution is confirmed. Out of window: Purdue Rip DHO Triple (2019) `[B77]`.

### A3. F5 Ball-screen offense: new and richer variants (extends 5.1–5.7)

Source keys `[P#]` in A3 and A4 are the ball-screen/handoff research note's keys (renamed from that note's local `[B#]` to avoid a clash with the Big Ten keys). Screen contact time **t₀** = the moment of minimum handler–screener distance; **P_s** = the screener's position at t₀. Extra primitives used only here [HEURISTIC]: **REPLACE** = a third attacker *p* moves from r < 4.5 to r ≥ 6.6, starting −0.5 to +1.0 s from the ROLL start, ending within 2.5 m of P_s or on the arc opposite the roller's lane. **SHORT_ROLL (strict)** = the screener decelerates to < 1.5 m/s at r 3.0–5.5, \|θ − 90°\| ≤ 35°, within 1.2 s of t₀. These strict primitives (≤ 0.3 m/s for ≥ 0.5 s) are tighter than §0.2 (< 0.6 m/s for ≥ 0.3 s); compute both and keep the stricter one as a confidence flag.

#### A3.1 Roll-and-replace ("roll/replace", "leak", "Replace") — NEW sub-family F5.4/F5.6 "Roll-and-replace" (no existing row contains "replace" or "leak")
- **Name and aliases:** roll-and-replace; roll/replace; roll-replace; leak; "Replace".
- **Family / sub-family:** F5, screener post-action (5.4) plus a spacing action by a third player (5.6). New sub-family **5.8 Roll-and-replace**.
- **Start alignment (middle screen; 4-out 1-in or Horns):** 1 handler top (7.6–8.5, 90); 5 screener arrives at (6.5–7.0, 75–105); 4 replacer low or under — block (2.0, 26/154), dunker, or elbow (4.57, 113.6); 2 corner (6.8, 5); 3 corner (6.8, 175). Teaching version: 1 top, 2 and 3 on the low posts; 2 cuts up to screen and rolls, 3 "replaces to the top" `[P26]`.
- **Roles:** handler; screener-roller; replacer; two corner spacers.
- **Ordered actions [HEURISTIC timings]:** −1.5 to 0 s screener arrives; 0 screen; 0.2–1.0 s roll starts; −0.5 to +1.0 s from the roll start the replacer moves out of the paint/block to the screen spot or top, "on the opposite side of the roller's path" `[P26]`; 1.0–2.5 s handler reads: lob/pocket to the roller, kick to the replacer, attack. Timing rule: too early → the defence rotates or switches; too late → his defender tags the roller and recovers `[P26]`.
- **Usual counters (defence, defense_full):** soft hedge + low-man tag (F3.2 + F7.2); X-replacer stays home so X-big must recover; no tag late in games; switch (F3.4) `[P26]`. Structural point: the replacer's defender is the tag defender and must choose between roller and replacer `[P26][P27]`.
- **Detection signature [HEURISTIC]:** BALL_SCREEN at \|θ_s − 90°\| ≤ 30°, r_s 6.0–8.5, then ROLL; REPLACE by a player whose pre-t₀ position is r < 4.5, his outward path crossing the roller's inward path within 2.0 s with closest approach ≥ 1.5 m (they pass on opposite sides); at t₀ + 2.0 s exactly 1 attacker at r < 3 and ≥ 3 at r ≥ 6.6 (the "4 around 1" shape described in `[P42]`).
- **Teams documented (MSU first):** **MSU** — "1-4 STS" (Izzo staple "over the last 15 years", page 21 Mar 2024): "the post re-screens and goes into roll/replace action" `[P51]` (see A1.15). Ole Miss 2014-15 (vs BYU, NCAA R1) `[P27]`; Notre Dame ~2015-16 "High Roll Replace" (4 screens and rolls, 5 replaces) `[P30]`; Texas A&M ~2015-16 `[P28]`; Duke 2000-01 (Battier spacing) and Maryland 2001-02 ("flex roll replace") `[P23]`; Wisconsin ~2014-15 `[P29]`. Seasons marked "~" are inferred from publication dates.
- **Sources:** `[P26][P27][P28][P30][P23][P29][P51][P42]`.
- **Confidence:** high for the definition and timing logic; high for the caption text; medium-low for MSU usage (third-party high-school contributor's FastModel page); low for 2024-26 (same wording as A1.15).

#### A3.2 Curl Roll-Replace (Ole Miss) — NEW (roll-and-replace with a same-screener pre-action chain)
- **Name and aliases:** Curl Roll-Replace.
- **Family / sub-family:** F5.8 roll-and-replace; pre-action F8 (pin-down curl decoy plus baseline screen).
- **Start alignment (spots unverified; diagrams were images):** 1 top (7.6, 90); 3 low on one side, curling from the block/dunker (2.0–2.7, 6–26); 2 opposite low, heading to a corner; 5 pin-down screener near (3.5, 30); 4 in the paint/short area.
- **Roles:** 3 decoy curler; 2 baseline runner; 5 two off-ball screens then ball screener and roller; 4 under-slider and replacer.
- **Ordered actions `[P27]`:** (1) 3 curls off 5's pin-down (catch-and-shoot decoy); (2) 2 runs off 5's baseline screen to the corner; (3) 5 "circles up" into a middle PnR with 1; (4) 4 "slides underneath, then replaces high as the 5 rolls". Timing [HEURISTIC]: pin-down t ≈ −3 to −2 s, baseline screen −2 to −1 s, ball screen 0, replace 0.3–1.2 s.
- **Usual counters:** 5's defender arrives late and can only "zone" the ball screen; 4's defender becomes the only bumper `[P27]`.
- **Detection signature [HEURISTIC]:** screener *s* sets two off-ball SCREENs (pin-down, then baseline) within 3.5 s before a BALL_SCREEN by the same *s*; then ROLL + REPLACE by the player who was at r < 3 under the action.
- **Teams documented:** Ole Miss 2014-15 vs BYU `[P27]`.
- **Sources:** `[P27]`.
- **Confidence:** medium.

#### A3.3 Rub Roll/Replace (Texas A&M) — NEW
- **Name and aliases:** Rub Roll/Replace.
- **Family / sub-family:** F5.8 roll-and-replace with a rub/front-cut pre-action (a 2 "runs in front of the ball-screen action").
- **Start alignment [HEURISTIC]:** 1 top or slot (7.6, 90)/(7.4, 70); 5 high; 4 at a block (2.0, 26/154); 2 on the arc near the screen side.
- **Roles:** 2 rub cutter; 5 screener-roller; 4 replacer; 1 handler.
- **Ordered actions `[P28]`:** (1) 2 runs across the screen line just before contact; (2) 5 screens for 1; (3) 5 rolls; (4) 4 "starts at the block and fills up". Timing [HEURISTIC]: rub −1.0 to 0 s, screen 0, replace 0.3–1.2 s.
- **Usual counters:** not stated; the rub occupies X-ball and X2 at the screen line.
- **Detection signature [HEURISTIC]:** a non-ball attacker crosses the segment (handler → P_s) within 1.0 s before t₀, passing within 1.5 m of P_s; then ROLL + REPLACE from the block.
- **Teams documented:** Texas A&M ~2015-16 vs Green Bay `[P28]`.
- **Sources:** `[P28]`.
- **Confidence:** medium.

#### A3.4 Horns Twist Leak (Horns Twist + roll-and-replace) — NEW combination (extends F3.2 "Horns Twist")
- **Name and aliases:** Horns Twist Leak.
- **Family / sub-family:** F3.2 Horns × F5 Twist × F5.8 roll-and-replace.
- **Start alignment `[P20]`:** "two shooters in the corners and two bigs at the elbows": 1 top (7.6–8.5, 90); 4 (stretch) right elbow (4.57, 66.4); 5 left elbow (4.57, 113.6); 2 corner (6.8, 5); 3 corner (6.8, 175).
- **Roles:** PG initiator; stretch 4 first screener then replacer; 5 second screener and roller.
- **Ordered actions `[P20]` [HEURISTIC timings]:** t 0: 1 uses 4's screen toward one side; 0.8–2.0 s: 1 reverses; 5 lifts for a second screen (Twist); 2.0–3.0 s: 5 rolls while 4 "pops from the paint to the perimeter" (the leak).
- **Usual counters:** the tag defender must choose between replacer and roller; also opens "a double gap" for the PG `[P20]`.
- **Detection signature [HEURISTIC]:** Horns snapshot; BALL_SCREEN #1 by the right-elbow player; handler heading reverses (> 120°) within 2.0 s; BALL_SCREEN #2 by the left-elbow player within 2.5 s of #1; ROLL by screener #2 and REPLACE by screener #1, who first drifted to r < 4.5 before popping to r ≥ 6.6.
- **Teams documented:** LSU (Will Wade) 2021-22 vs Ohio; McNeese (Wade) 2024-25; NC State (Wade) 2025-26 projected only `[P20]`.
- **Sources:** `[P20]`.
- **Confidence:** high for the action; medium for timings.

#### A3.5 On-Ball Flare (roll-and-replace counter; Wisconsin) — NEW post-action ("screener receives a flare after the ball screen")
- **Name and aliases:** On-Ball Flare ("Wisco On-Ball Flare").
- **Family / sub-family:** F5.8 roll-and-replace variant: the replacer becomes a flare screener for the original roller.
- **Start alignment (spots unverified):** 1 top (7.6, 90); 5 (Kaminsky) screening high (6.5–7.5, 75–105); 4 (Hayes) low in the paint/block; others on the arc.
- **Roles:** 5 screener → aborted roller → flare user and shooter; 4 flare screener → roller.
- **Ordered actions `[P29]`:** (1) 5 screens for 1; (2) 5 "begins to roll toward the rim, then runs off a flare screen set by the 4"; (3) 4 holds the flare, then rolls; (4) 5 gets a "wide open jump shot" on the wing. Timing [HEURISTIC]: screen 0, roll start 0.3–0.8 s, flare contact 1.0–2.0 s, 4's roll 1.5–2.5 s.
- **Usual counters:** exploits defenders "used to the traditional roll-and-replace"; the help defender (X4) is pinned by the deep angle `[P29]`.
- **Detection signature [HEURISTIC]:** BALL_SCREEN; the screener moves inward ≥ 1.0 m (aborted roll); SCREEN by the low big on the screener's defender, with the screener's path pointing away from the ball (angle > 120°) and ending at r ≥ 6.6, θ 25–55° or 125–155°; then ROLL by the flare screener.
- **Teams documented:** Wisconsin vs Kentucky; season not on the page, Kaminsky/Hayes context suggests 2014-15 (**unverified**) `[P29]`.
- **Sources:** `[P29]`.
- **Confidence:** medium.

#### A3.6 Corner Step-Up ("Continuity Step-Up"; guard step-up from the corner) — RICHER (extends F5.2 "Step-up", which is big-from-below-the-FT-line only)
- **Name and aliases:** corner step-up; Hoop Vision "Continuity Step-Up" (patterned version).
- **Family / sub-family:** F5.2 angle (step-up) × F5.3 pre-action (from the corner); usually a **guard** screener.
- **Start alignment `[P9]`:** handler at a wing (7.2, 40) or slot (7.4, 70); guard screener in the same-side corner (6.8, 5) ("starts in the corner. He runs up to set a screen on the ball near the wing or slot"); big(s) weak side or dunker.
- **Roles:** handler; guard step-up screener who screens hard or ghosts; weak-side big, often the next empty-side screener.
- **Ordered actions:** (1) corner guard sprints up the sideline/arc; (2) hard step-up screen (handler drives baseline or middle) or ghost; (3) optional flow into an "empty ball screen" with a big (Texas A&M example) `[P9]`. Timing [HEURISTIC]: corner exit −1.2 to −0.4 s; screen/ghost 0; next ball screen 2–5 s.
- **Usual counters:** switch miscommunication was exploited (Houston vs TCU) → defence F3.4 switch/pre-switch; the ghost punishes X-ball's helper over-helping `[P9]`.
- **Detection signature [HEURISTIC]:** screener path starts at θ ≤ 12° (or ≥ 168°), r ≥ 6.6, moves with dθ toward 90° and \|Δr\| ≤ 1.0 m (along the arc) at ≥ 3 m/s, ends within 1.2 m of the handler's defender on the baseline side (screener y < handler y); then SCREEN or GHOST; screener roster height ≤ 1.96 m; continuity flag = ≥ 2 such step-ups in one possession.
- **Teams documented:** Marquette 2023-24 (Kolek ghosted the step-up for Kam Jones vs Butler); Texas A&M 2023-24 (Hefner step-up ghost for Wade Taylor vs Kentucky, then an empty ball screen with Leveque); Houston 2023-24 (Shead step-up, Cryer open three vs TCU) `[P9]`.
- **Sources:** `[P9]` (Jordan Sperber, 15 Jan 2024).
- **Confidence:** high for existence and examples; continuity reads **unverified** (paywall).

#### A3.7 Angle Pop (flat slot screen, pop to the middle, weak-side action on the swing) — NEW
- **Name and aliases:** Angle Pop.
- **Family / sub-family:** F5.1 slot × F5.2 flat × F5.4 pop; second phase F8 (down screen or 45 cut).
- **Start alignment `[P20]`:** handler right slot (7.4, 70); 5 flat screen "on the edge of the middle third, closer to the slot than the top": P_s ≈ (6.8–7.3, 70–80); opposite slot (7.4, 110); corners (6.8, 5)/(6.8, 175).
- **Roles:** handler; popping 5; weak-side 4 (down-screener or 45 cutter); corner shooters/back-cutters.
- **Ordered actions `[P20]` [HEURISTIC timings]:** 0 flat screen; 0.2–1.5 s handler dribbles toward the sideline while 5 pops toward the middle (θ → 85–100°, r 6.6–7.5); 1.5–3.0 s swing to the popped 5; 2.0–4.0 s weak side: 4 lifts and down-screens for the weak-corner guard, or cuts at 45° to the rim; corners shoot or back-cut. Counter-read: "If the first screen doesn't work, the big can re-screen and dive".
- **Usual counters:** the pop forces rotations, then the attack shifts weak side for backdoors; targets drop coverage (F3.1) `[P20]`.
- **Detection signature [HEURISTIC]:** BALL_SCREEN with the handler at θ 55–80° (or 100–125°) and the screener on the sideline side of X-ball (screener→X-ball vector within ±30° of −sign(x_handler)·x̂; verify on film — if unreliable, drop the orientation test and keep the \|x\|-increasing drive plus the screen location); the handler's post-screen velocity has \|x\| increasing; POP with end θ within 15° of 90°; pass to the popper within 3.0 s; then SCREEN(down) on the weak side within 2.0 s of the catch, or a CUT at heading 30–60° toward the rim from the weak wing.
- **Teams documented:** NC State 2024-25 (vs Purdue, Texas A&M-CC, Clemson); Texas Tech 2024-25 (Darrion Williams screens and pops himself, plus a two-man DHO off it); NC State (Wade) 2025-26 projected only `[P20]`.
- **Sources:** `[P20]`.
- **Confidence:** high.

#### A3.8 Pick-and-pop destination classes — RICHER (sub-classes F5.4 "Pop" by destination)
- **Name and aliases:** high / flat / side / step-up / corner / pass-and-follow / ram / double-drag / drag pick-and-pop.
- **Family / sub-family:** F5.4 pop, sub-classed by where the screener ends.
- **Start alignment and destinations (from `[P59]`; converted to this frame [HEURISTIC]):**

  | Class | Screen location | Pop destination (r, θ) |
  |---|---|---|
  | High PnP | top | middle behind the arc (6.8–7.6, 80–100) |
  | Flat PnP | slot | slot behind the arc (7.0–7.5, 60–80) |
  | Side PnP 1 | wing | back to the same wing (6.8–7.4, 30–55) |
  | Side PnP 2 | wing | corner (6.6–7.0, ≤ 12) |
  | Step-up PnP 1 | step-up | elbow (4.3–4.9, 60–72) — mid-range pop |
  | Step-up PnP 2 | step-up | top (7.0–8.0, 80–100) |
  | Corner PnP 1 / 2 / 3 | corner | vacant corner / short corner (4.0–5.5, ≤ 15) / wing |
  | Pass-and-follow PnP | passer screens after handing off | extended slot; ball then skipped to the popper |
  | Ram PnP | down screen, then ram | wing |
  | Double-drag PnP / Drag PnP | transition | top, behind the arc |
- **Roles:** screener-popper; handler; spacers.
- **Ordered actions [HEURISTIC]:** pop complete within 2.0 s of t₀; catch within 3.0 s.
- **Usual counters:** drop (F3.1) is beaten by the pop; hedge (F3.2) by short roll/pop; full rotation onto the popper concedes the roll.
- **Detection signature [HEURISTIC]:** POP; classify by the screener's end (r, θ) relative to P_s using the table; tag "mid-range pop" if end r < 6.6 and the catch-and-shoot is at r 4–6. POP here is the union of `POP_ARC` (r ≥ 6.6) and `POP_MID` (outward ≥ 1.5 m, stops at r 4.0–6.6 without rolling, within 2.0 s), A11.18.
- **Teams documented (MSU first):** MSU 2025-26 — Kohler MSU's most efficient catch-and-shoot player (40.8% 3P), threes nearly half his shots `[P38]`; detailed PnP set usage **unverified** for 2025-26. MSU "Detroit" (2014-15 era): the shooter (4) always pops `[P7]`. MSU 1-4 High: "O4 pops out on top to the arc" after the 5's wing screen `[P7]`. Florida 2005-06: pick-and-pop beat hedging UCLA bigs in the title game `[P23]`.
- **Sources:** `[P59][P7][P38][P23]`.
- **Confidence:** medium (one teaching site; converted coordinates heuristic).

#### A3.9 Pop throwback vs two-on-ball ("Four Low" high screen) — NEW (F5.4 pop × F5.5 read)
- **Name and aliases:** Four Low pop throwback; 2-v-1 on the catch. Distinct from the short roll: the screener pops and catches above the arc.
- **Family / sub-family:** F5.4 pop × F5.5 handler read (throwback vs blitz/hedge).
- **Start alignment `[P3]`:** 1 top (7.6–8.5, 90); 4 starts low and sprints up to screen; 5 low, relocating to the dunker ("porch") opposite the pop (2.7, 6/174); 2 and 3 in the corners (6.8, 5/175). Alternate entry: a stack.
- **Roles:** handler; 4 sprint screener and popper; 5 dunker; corners.
- **Ordered actions `[P3]` [HEURISTIC timings]:** (1) 4 sprints out to screen, trying to arrive without a defender attached (−1.5 to 0 s); (2) 4 pops to the opposite side (0.3–1.5 s); (3) on two-on-ball, 1 throws back to 4 (1.0–2.0 s); (4) reads 2.0–4.0 s: X3 runs at the ball or freezes → extra pass to the corner; X3 stunts → backdoor by 3; X3 stays attached → shoot or drive the gap; X5 helps → drop to 5 at the dunker; X2 helps the helper → 2 lifts, skip. Also a blast cut from the corner on 4's look, or 4 follows into a wing ball screen.
- **Usual counters:** built to beat F3.3 blitz / F3.2 hard hedge; defence answers with X3 rotation and corner tags (F7.2).
- **Detection signature [HEURISTIC]:** two defenders within 2.0 m of the handler at t₀ + 0.5 s; POP to r ≥ 6.6 on the side opposite the handler's drift; pass handler → screener within 2.0 s of t₀; the non-screening big at the dunker spot opposite the pop (2.0 ≤ \|x\| ≤ 3.5, y ≤ 0.6) within 1.5 s of t₀.
- **Teams documented:** Iowa State (page published 2 Oct 2017; coach and season **unverified**) `[P3]`.
- **Sources:** `[P3]`.
- **Confidence:** medium.

#### A3.10 Short-roll 4-on-3 decision tree vs blitz / hard hedge — RICHER (extends F5.4 "Short roll")
- **Name and aliases:** short roll 4-on-3; "near the Nail" short roll.
- **Family / sub-family:** F5.4 short roll × F5.5 reads.
- **Start alignment [HEURISTIC]:** any high or slot PnR; weak side one big or wing at the dunker spot; shooters in the corners.
- **Roles:** handler (gets off the ball early); short roller; backside cutters/shooters; dunker.
- **Ordered actions [HEURISTIC timings]:** 0 screen; 0.3–0.8 s blitz/hedge recognised and the handler passes immediately rather than dribbling through the trap (Kansas vs Houston) `[P35]`; 0.6–1.5 s short roller catches "near the Nail" (suits a big who can finish and pass) `[P5]`; 1.5–3.0 s decision: (1) finish if the rim is open; (2) "get off the ball" to backside cutters/shooters `[P5]`; supplementary: drop to the dunker, skip to the weak corner, ghost cut by a corner player as the help tags `[P3][P36]`.
- **Usual counters:** blitz with fast low-man rotation (F7.2 tag); defence may live with a non-shooting short roller catching (NBA example, secondary) `[P16]`.
- **Detection signature [HEURISTIC]:** at t₀ + 0.3–1.0 s two defenders within 2.0 m of the handler; SHORT_ROLL; pass handler → screener caught at r 3.0–5.5, \|θ − 90°\| ≤ 35°, within 1.5 s of the trap onset; next event within 1.5 s: FGA at r < 2 by the roller, pass to r < 3 (dunker) or pass to r ≥ 6.6. Label 4-on-3 if, at the catch, attackers excluding the handler = 4 and non-trapping defenders = 3.
- **Teams documented (MSU first):** MSU zone-offense version (FastModel 29 Mar 2015): 4 sprints into a high ball screen and short-rolls to the high post; if 1 can't hit 4, 1 hands off to 3 lifting from the corner and 3 hits 4; the roller reads a stepping-up defender; if not fed early he seals in the high post `[P6]` [pre-window]. Kansas 2023-24 vs Houston's blitz (KJ Adams; 1.22 PPP, 75.6% eFG that game) `[P35]`. Purdue 2024-25 Kaufman-Renn short roll (`[S57]`; and A2.7).
- **Sources:** `[P5][P6][P35][P3][P36][P16]`.
- **Confidence:** high for the concept and the Kansas/MSU examples; Hoop Vision reads paywalled.

#### A3.11 "Shorting" the second big to the dunker spot before the screen ("Angle Short") — NEW spacing tag (F5.6; NBA-only documentation)
- **Name and aliases:** shorting to the dunker / "Ghost" spot; Angle Short. Related to F5.6 "Slide", but done **before** the screen.
- **Family / sub-family:** F5.6 off-ball spacing tag.
- **Start alignment `[P36]`:** 4 near the dunker spot (2.7, 6); 5 sets an elbow-angle ball screen for 1 around (4.6–6.0, 60–75); 2 rubs off 5 and clears to the right corner (6.8, 5).
- **Roles:** 4 dunker; 5 screener-roller; 2 rub cutter; 1 handler.
- **Ordered actions `[P36]` [HEURISTIC timings]:** (1) 2 rubs off 5 and clears to the corner (−1.5 to −0.5 s); (2) 4 shorts to the dunker spot (−1.0 to 0); (3) 5 sprints into the elbow-angle screen (0); (4) 5 rolls (0.3–1.2 s); (5) lob vs a hedge (1.0–1.8 s).
- **Usual counters:** a hedge invites the lob; a drop (F3.1) takes it away.
- **Detection signature [HEURISTIC]:** before t₀ the non-screening big has been at 2.0 ≤ \|x\| ≤ 3.5, y ≤ 0.6 for ≥ 0.5 s; ROLL; pass to the roller at r < 1.5 with ball apex > 3.0 m when ball height is tracked.
- **Teams documented:** Washington Wizards (NBA), FastModel 16 Apr 2017 `[P36]` — secondary alias only; no college team found. Related college evidence: MSU's dunker big opposite the PnR (A1.10).
- **Sources:** `[P36]`.
- **Confidence:** medium.

#### A3.12 Horns Slip / MSU "Horns Out Slip" — NEW (F3.2 Horns × F5.4 slip)
- **Name and aliases:** Horns Slip (fake one elbow screen, slip to the opposite block, use the other); MSU **"Horns Out Slip"** (screen-the-screener, then slip).
- **Family / sub-family:** F3.2 Horns × F5.4 slip.
- **Start alignment:** Horns: 1 top (7.6, 90); 4 at an elbow (4.57, 66.4); 5 at the other elbow (4.57, 113.6); 2 and 3 in the corners (6.8, 5)/(6.8, 175). Exact sides **unverified** `[P53]`; MSU alignment **unverified** (image-only diagram) `[P46]`.
- **Roles:** generic: 4 slipper/post target, 5 ball screener then down-screener, 2 down-screen user. MSU: 5 screens for 4, 4 "out cuts", 5 slips the ball screen and receives.
- **Ordered actions:** generic `[P53]` [HEURISTIC timings]: (1) 1 dribbles toward 4 (−0.8 to 0 s); (2) 4 slips to the opposite block, ending near (2.0, 154) (0–0.8 s); (3) 1 uses 5's screen instead (0.5–1.5 s); (4) after 1 clears, 5 down-screens for 2 in the corner (1.5–3.0 s); (5) reads: post to 4, else 2 off the down screen. MSU `[P46]`: 5 screens for 4; 4 out-cuts; 5 sprints off the ball screen and slips it; 1 passes to 5 for the dunk.
- **Usual counters:** switch / pre-switch on Horns (F3.4); weak-side low man fronts the slipper.
- **Detection signature [HEURISTIC]:** Horns snapshot; the handler's first dribble heads toward elbow player A; A shows GHOST/SLIP (dr/dt < 0, ends r < 2.5 with sign(x) flipped); BALL_SCREEN by elbow player B within 2.0 s; B then SCREEN(down) for a corner player within 2.0 s. MSU version: elbow-to-elbow SCREEN (B→A), A exits outward (r increasing), then B approaches the handler and SLIPs to r < 1.5 with a pass within 1.5 s.
- **Teams documented (MSU first):** **MSU 2018-19** (FastModel 4 Apr 2019): run as an ATO in the one-point Elite Eight win over Duke `[P46]` [pre-window]. New Mexico State 2014-15 vs Kansas `[P53]`.
- **Sources:** `[P53][P46]`.
- **Confidence:** high for the MSU text sequence; MSU alignment **unverified**.

#### A3.13 Stagger / 77 slip (first screener slips vs ice) — NEW
- **Name and aliases:** stagger slip; 77 slip.
- **Family / sub-family:** F5 stagger ball screen ("77") × F5.4 slip.
- **Start alignment [HEURISTIC]:** handler at a wing (7.2, 40) or slot (7.4, 70); two screeners in line along the dribble path, 1.5–2.5 m apart.
- **Roles:** 4 first screener and slipper; 5 second screener; handler.
- **Ordered actions `[P54]`:** (1) 4 and 5 set a stagger ball screen (t 0); (2) the defence "ices" the first screen, X4 in front of it (0–0.5 s); (3) 4 slips into the gap to the rim (0.3–1.2 s).
- **Usual counters:** exploits ice (F3.5); defence answer = low-man tag on the slipper (F7.2).
- **Detection signature [HEURISTIC]:** two screeners within 3.0 m of each other along the handler's path; the first never satisfies SCREEN and dives (SLIP) while X-ball sits on the screen side (ice signature per defense_full F3.5).
- **Teams documented:** Miami (FL) vs Villanova, FastModel 24 Mar 2016 (~2015-16 NCAA) `[P54]`. MSU related: "Stagger Slip Curl & Pop" (A1.15; on/off-ball status of the stagger **unverified**) `[P49]`.
- **Sources:** `[P54][P49]`.
- **Confidence:** medium.

#### A3.14 Slip-to-arc ("slip-pop") — NEW screener post-action label (F5.4)
- **Name and aliases:** slip-pop; slip to the arc.
- **Family / sub-family:** F5.4 slip whose destination is the arc rather than the rim.
- **Start alignment:** any ball screen with a stretch-big screener; e.g. handler top (7.6, 90), screener arriving at (6.8, 80–100) [HEURISTIC].
- **Roles:** stretch screener; handler.
- **Ordered actions [HEURISTIC]:** approach (−0.8 to 0 s); early release before contact (≤ 0); arrival at r ≥ 6.6 within 1.5 s; catch within 2.5 s.
- **Usual counters:** the big defender must "track him to the three-point line" `[P38]`; switching (F3.4) neutralises it.
- **Detection signature [HEURISTIC]:** SLIP with dr/dt > 0 and end r ≥ 6.6 within 1.5 s of the approach peak. Distinct from POP because the SCREEN dwell is never satisfied.
- **Teams documented:** **MSU 2025-26**, Jaxon Kohler — a UCLA scouting report says Bilodeau "must track him to the three-point line when he slips a screen" (17 Feb 2026) `[P38]`.
- **Sources:** `[P38]`.
- **Confidence:** medium (one sentence; frequency unknown).

#### A3.15 Ghost → back screen → middle ball screen (switch-bait sequence) — NEW
- **Name and aliases:** ghost-Spain-PnR switch bait.
- **Family / sub-family:** F5 pre-action chain: ghost (5.4) → Spain-like back screen → middle ball screen.
- **Start alignment [HEURISTIC]:** 1 top (7.6, 90); wing shooter (Grady Dick) near a slot (7.4, 70/110); 5 low or at an elbow; two others in the corners.
- **Roles:** ghost-screener (shooter); handler; 5 ball screener and diver.
- **Ordered actions `[P14]` [HEURISTIC timings]:** (1) wing ghost-screens for 1 and draws a switch (−3 to −2 s); (2) a back screen "similar to Spain action" (−2 to −1 s); (3) 5 ball-screens for 1 to drive the paint (0); (4) 5 dives hard; the ghost-screener loops back to the top (0.3–1.5 s); (5) the ghoster's defender tags the roll, leaving the throwback three.
- **Usual counters:** switching is the bait; the tag on the roll (F7.2) leaves the throwback open.
- **Detection signature [HEURISTIC]:** GHOST by *g* on the handler's defender; defender swap within 1.0 s; *g* then SCREEN(back) on another defender within 2.5 s; BALL_SCREEN at \|θ − 90°\| ≤ 20° within 2.5 s of that; *g* ends at the top (r ≥ 6.6, \|θ − 90°\| ≤ 15°) and receives within 3.0 s.
- **Teams documented:** Kansas vs Howard, 2023 NCAA R1 (2022-23), end of clock `[P14]`.
- **Sources:** `[P14]`.
- **Confidence:** medium-high.

#### A3.16 Double ghost — NEW
- **Name and aliases:** double ghost.
- **Family / sub-family:** F5.4 ghost × 2.
- **Start alignment [HEURISTIC]:** handler top (7.6, 90); two would-be screeners approaching from the elbows (4.57, 66.4/113.6) or slots.
- **Roles:** handler attacks the gap; two ghosting screeners (follow-ups: flare to the arc or back-cut slip to the rim); corner player = kick-out if help comes inside `[P34]`.
- **Ordered actions [HEURISTIC]:** jog approach ~1 s, sprint away at contact (−0.3 to 0 s); handler drives the gap.
- **Usual counters:** best against switching teams `[P34]`; defence: stay home / no switch.
- **Detection signature [HEURISTIC]:** two GHOST events on the same handler within 1.0 s of each other; both screeners exit outward (or one dives); handler DRIVE within 1.5 s.
- **Teams documented:** none named `[P34]`.
- **Sources:** `[P34]`.
- **Confidence:** medium (generic coaching source).

#### A3.17 "Blue" (fake) drag → flare for the handler; "Red" (real) re-entry — NEW (F2.1 × F5 × F8)
- **Name and aliases:** "Blue" = fake ball screen, "Red" = real ball screen (in this terminology) `[P31]`.
- **Family / sub-family:** F2.1 drag × F5 fake ball screen × F8.1 flare.
- **Start alignment [HEURISTIC]:** transition: 1 dribbling at the slot or top (7.4, 70)/(7.6, 90); 5 trailing behind 1; 4 on the wing (7.2, 40).
- **Roles:** 5 fake drag screener then flare screener; 1 passer then flare user; 4 receiver and return passer.
- **Ordered actions `[P31]` [HEURISTIC timings]:** (1) 5 "follows behind" 1 as if to drag, no roll or pop (−1 to 0 s); (2) 1→4 (0–0.5 s); (3) 5 immediately flares 1, back to the top of the key (0.5–1.5 s); (4) 4 passes back to 1 for a shot or drive (1.5–2.5 s); (5) variation: if 1 cannot pass, he spins back into a real ("Red") ball screen.
- **Usual counters:** X-ball sags to cover the flare; switch.
- **Detection signature [HEURISTIC]:** within 10 s of the possession start a trailer within 2.0 m of the handler with no SCREEN; PASS handler → wing; SCREEN by the trailer on the passer's defender within 1.0 s with the passer moving away from the ball; return PASS within 2.5 s.
- **Teams documented:** none named (contributor Radius Athletics, 29 Oct 2020) `[P31]`.
- **Sources:** `[P31]`.
- **Confidence:** medium-low. Also named but undefined: "Dummy ball screen" (a video section title in a Hoop Vision piece; probably = ghost/"blue"; definition **unverified**) `[P10]`.

#### A3.18 Spain "release" read (skip the back screen vs hard hedge) — RICHER (extends F5.6 "Spain")
- **Name and aliases:** Spain release; "Stack/Spain screen and release" (Slappin' Glass) `[P40]`.
- **Family / sub-family:** F5.6 Spain × read.
- **Start alignment `[P57]`:** 1 top (7.6–8.5, 90); 5 screens at (6.5–7.2, 80–100); back-screener (2) starts in the paint/under the rim (1.0–2.5, 60–120); corners (6.8, 5)/(6.8, 175). Base Spain per `[P57]`: the ball screen and back screen "happen at the same time"; the shooter "head hunts" X-screener; the other two sit in the corners.
- **Roles:** handler; ball screener/roller; back-screener who releases; corner spacers.
- **Ordered actions [HEURISTIC timings]:** ball screen at t₀; the back-screener reaches X5 at t₀ + 0.0–0.8 s. Rule: if X-screener hard-hedges and is detached from the screener, the back-screener skips the back screen and sprints to space at the top `[P57][P58]`; expect the release if X5 is ≥ 0.8 m above the screen line (defense_full F3.0 λ ≤ −0.8 m) at t₀ + 0.3 s — the back-screener's r reaches ≥ 6.6 by t₀ + 1.5 s with no SCREEN.
- **Usual counters:** top-lock or pre-switch (F3.6); "Next" early weak-side rotation `[P2]`; Spain itself targets drop (F3.1) `[P2]`.
- **Detection signature [HEURISTIC]:** Spain approach (third player moving from r < 3 toward X-screener); no SCREEN formed; third player reaches the arc above the screen within 1.5 s → label Spain-release.
- **Teams documented:** Purdue 2023-24 — Gillis (48% 3P) set the back screen on every Spain in the Elite Eight vs Tennessee `[P41]`; Purdue 2022-23 (Edey): the roll/replace becomes Spain "when the back screen is added" `[P24]`. Purdue "Horns Spain" (A2.40) `[B5]`.
- **Sources:** `[P57][P58][P40][P2][P41][P24]`.
- **Confidence:** high for the definition; medium for timing thresholds.

#### A3.19 Ram-into-Spain ("Stack Spain") — NEW combination (F5.3 × F5.6)
- **Name and aliases:** Ram-into-Spain; Stack Spain.
- **Family / sub-family:** F5.3 ram (or sprint-into) × F5.6 Spain.
- **Start alignment [HEURISTIC]:** 1 top (7.6, 90); 5 at the block (2.0, 26); 3 near the lane to screen 5; 4 on the wing (7.2, 40); 2 low/under.
- **Roles:** 3 ram screener; 5 ball screener/roller; 2 Spain back-screener then pop; 4 corner clearer.
- **Ordered actions `[P25]` [HEURISTIC timings]:** (1) 3 screens for 5, who sprints up into the ball screen; 4 clears to a corner (−2 to 0 s); (2) 1 uses 5's screen; 3 clears to the other corner; 2 sprints up (0–0.6 s); (3) 2 back-screens X5; 5 rolls; 2 steps out (0.4–1.5 s).
- **Usual counters:** as A3.18.
- **Detection signature [HEURISTIC]:** off-ball SCREEN on behalf of the eventual ball screener within 2.0 s before t₀ (ram); BALL_SCREEN; a third player SCREENs X-screener within 0.8 s of t₀; POP by the back-screener.
- **Teams documented:** Spain national team, EuroBasket 2015 final vs Lithuania `[P25]` (European, secondary). College analogue: Purdue 2022-23 pin-down ram for Edey with lift or Spain (A3.25) `[P24]`.
- **Sources:** `[P25][P24]`.
- **Confidence:** high (text sequence).

#### A3.20 Big-on-big Spain ("Wolverine", Michigan) — NEW variant (F5.6)
- **Name and aliases:** "Wolverine"; big-on-big Spain (the second big sets the back screen).
- **Family / sub-family:** F5.6 Spain variant.
- **Start alignment `[P58]`:** four-out: O2 corner → opposite corner; O3 lifts to the wing (7.2, 40); O1 dribbles left to set the angle; O5 sprints up; O4 starts inside (r < 3).
- **Roles:** 5 ball screener and rim cutter; 4 back-screener then top shooter; 1 handler; 2, 3 spacers.
- **Ordered actions `[P58]` [HEURISTIC timings]:** (1) 5 sprints up and screens for 1 (0); (2) 4 slides slightly inside and back-screens 5 (0.3–1.0 s); (3) 5 cuts around to the rim (0.6–1.5 s); (4) reads: lob if X5 helps; layup if not; jump-stop kick to 2 or to 4 "now on top" for three.
- **Usual counters:** switch the back screen (creates mismatches) `[P58]`.
- **Detection signature [HEURISTIC]:** Spain signature where the back-screener is a big (roster height ≥ 2.03 m, or the player with pre-action r < 3 for ≥ 2 s); after the screen the back-screener ends at the top (r ≥ 6.6, \|θ − 90°\| ≤ 20°).
- **Teams documented:** Michigan ("Wolverine"); era not stated (**unverified**) `[P58]`.
- **Sources:** `[P58]`.
- **Confidence:** medium.

#### A3.21 Side Spain out of zipper + DHO (MSU SLOB) — NEW (F5.1 side × F5.6 Spain; F13.3)
- **Name and aliases:** MSU "Zipper Spain PNR SLOB" (also in A1.15).
- **Family / sub-family:** F5.1 side × F5.6 Spain; entry via F6 DHO; F13.3 SLOB.
- **Start alignment:** SLOB (inbounder out of bounds at \|x\| > 7.62 m, y ≈ 6.9 m → ≈ (10.55, 41.1), A6 landmarks); **canonical entry** for this MSU set (A1.15 row points here); zipper cutter at the block (2.0, 26); others [HEURISTIC] as in A1.15.
- **Roles:** 1 zipper cutter then post flasher; 2 DHO giver then corner; 3 weak-side DHO receiver (PnR handler); 4 opposite-corner cutter; Spain screener **unverified** (the page does not say who screens).
- **Ordered actions `[P47]`:** (1) zipper; 1→2; (2) 2 DHOs to 3 on the weak side; (3) 4 cuts to the opposite corner, 1 flashes to the opposite post; (4) 2 opens to the corner; (5) side Spain PnR. Timing [HEURISTIC] as in A1.15.
- **Usual counters:** top-lock / pre-switch (F3.6).
- **Detection signature [HEURISTIC]:** SLOB start; zipper cut (block → slot within 2.0 s, A5.24 as amended); DHO at the wing/slot; BALL_SCREEN with the handler at θ 25–55°/125–155° and a third player (the post flasher) approaching X-screener within 0.8 s of t₀.
- **Teams documented:** **MSU**, FastModel 17 Mar 2023 (~2022-23) `[P47]` [pre-window].
- **Sources:** `[P47]`.
- **Confidence:** medium (screen assignments **unverified**, image-only).

#### A3.22 Spain in the secondary break ("early Spain") and named Spain sub-variants — RICHER (extends F5.6 "Spain" and F2)
- **Name and aliases:** early Spain; Double Spain; Spain Twist; Wide Spain; Delay Spain; Ghost Spain.
- **Family / sub-family:** F2 secondary × F5.6 Spain; F5.6 sub-variants.
- **Start alignment:** early Spain: any secondary-break alignment, Spain within 10 s of the possession start. Sub-variants: as in the table.
- **Roles:** as Spain (handler, roller, back-screener, corners).
- **Ordered actions / definitions:** early Spain — North Carolina 2004-05 produced a McCants three at the start of the title game; SI's Grant Wahl wrote that Larry Brown showed Dean Smith the wrinkle `[P23]`. This conflicts with sources crediting the 2009 EuroLeague or Spain at the 2016 Olympics `[P2][P57]`; the origin is **unverified**. Sub-variants, single source `[P2]` (teams: none named; EuroLeague cited for Double Spain):

  | Variant | Definition | Detection [HEURISTIC] |
  |---|---|---|
  | Double Spain | two back screens stacked on the roller's defender | two third players SCREEN X-screener within 1.0 s of t₀ |
  | Spain Twist | the roller twists back into a re-screen before the back screen arrives | same pair re-screens from the opposite side within 1.5 s, then the back screen |
  | Wide Spain | started from a wing ball screen | Spain with the handler at θ 25–55°/125–155° |
  | Delay Spain | from a 5-out Delay set; the big has the ball and initiates late | big at the top with the ball, then a DHO/ball screen, then a back screen |
  | Ghost Spain | the back-screener fakes and pops without contact | third player approaches X-screener within 1.5 m, never SCREENs, then POP |
- **Usual counters:** as A3.18.
- **Detection signature [HEURISTIC]:** early Spain = Spain signature with PHASE = early (≤ 10 s); sub-variants per table.
- **Teams documented:** North Carolina 2004-05 `[P23]`.
- **Sources:** `[P23][P2][P57]`.
- **Confidence:** medium (single sources; origin disputed). **Naming conflict "Stack PnR":** in NBA writing "Stack Pick and Roll" = Spain (the screener's defender "is screened off by a tertiary offensive player"; follow-up reads: dive vs extra attention, corner open vs a tag, above-break three for the second screener vs a double, then a DHO) `[P1]`; in college diagram libraries "Stack" also means a guard stacked under the screener (A3.23) or a stacked formation. See Vocabulary proposals.

#### A3.23 Stack Roll (guard stacked under the screener) — NEW (distinct from Spain)
- **Name and aliases:** Stack Roll.
- **Family / sub-family:** F5: a guard is pre-positioned under/behind the ball screener so the roll goes around his body; the guard then pops. Not Spain: the guard does not back-screen after the ball screen; he is pre-stacked.
- **Start alignment `[P19]`:** 1 top (7.6, 90); 2 wing (7.2, 40); 5 high; after passing, 1 "moves underneath" 5, ending ≈ 1.0–2.0 m below 5 toward the rim.
- **Roles:** 2 handler; 5 screener-roller; 1 stacked guard → popper → post passer.
- **Ordered actions `[P19]` [HEURISTIC timings]:** (1) 1→2 and 1 moves underneath 5 (−2 to −0.5 s); (2) 2 dribbles off 5's screen (0); (3) 5 rolls "around 1" to the block (0.3–1.5 s); (4) 1 pops out and can make the post pass (0.5–2.0 s).
- **Usual counters:** switch, or X1 top-locks the popping guard.
- **Detection signature [HEURISTIC]:** ≥ 0.5 s before t₀ a teammate stands 0.8–2.0 m from the screener on the rim side (r_teammate < r_screener) within ±25° of the screener's θ; BALL_SCREEN; ROLL whose path passes within 1.2 m of that teammate; the teammate POPs to r ≥ 6.6; post entry (pass to r < 2.5) within 3 s.
- **Teams documented:** Texas A&M (Billy Kennedy era), FastModel 19 Mar 2016 (~2015-16) `[P19]`.
- **Sources:** `[P19]`.
- **Confidence:** medium.

#### A3.24 77 Wall, 77 Pop-and-Flare, and Horns double ball screen ("Horns 77") — NEW (extends F2.1 "Double drag" and F5.7 "Detroit")
- **Name and aliases:** 77 Wall; 77 Pop-and-Flare; Horns 77 (sequential same-direction Horns double).
- **Family / sub-family:** F5 stacked/double ball screens; F2.1 double drag; F3.2 Horns.
- **Start alignment:** 77 Wall `[P16]`: handler at the slot/top; two screeners shoulder to shoulder (≤ 1.2 m apart) perpendicular to the handler's path, on **one** side (Detroit has them on both sides); corner filled. 77 Pop-and-Flare `[P16]`: double drag, corner empty; base geometry puts the first screener a body length higher than the second. Horns 77 `[P18][P17]`: Horns — 1 top, 5 and 4 at the elbows (4.57, 66.4/113.6), 2 and 3 in the corners.
- **Roles:** Wall: bottom screener pops, top screener rolls. Pop-and-Flare: screener 2 pops; screener 1 flares for the popper or a backside shooter. Horns 77: 5 first screener rolls; 4 second screener pops.
- **Ordered actions [HEURISTIC timings]:** Wall: set at t 0; handler comes off 0–0.8 s; bottom screener pops 0.3–1.5 s; top screener rolls. Pop-and-Flare: screen 1 at t₀; screen 2 at t₀ + 0.5–1.5 s (the second screen is "often set a step late" `[P16]`); flare t₀ + 1.5–3.0 s. Horns 77: Ohio `[P18]` — 5 sets screen 1 (0), 4 sets screen 2 (0.5–1.5 s), 1 uses both, 5 rolls, 4 pops, 2 drifts to the corner on the drive; UNC `[P17]` — 1 and 3 DHO first (−2 to 0 s), then the 5+4 double for 3; 5 rolls, 4 pops.
- **Usual counters:** Wall exploits X-shooter's hesitation to help `[P16]`; Horns 77: switch the second screen, X4 stays home on the popper.
- **Detection signature [HEURISTIC]:** Wall: two SCREENs with inter-screener distance ≤ 1.2 m, joining line within ±25° of perpendicular to the handler's velocity, both on the same side of his path; one POPs. Pop-and-Flare: double-drag signature (two ball screens within 1.5 s, both at r > 6.5), POP by screener 2, then a SCREEN by screener 1 with flare geometry within 2.0 s. Horns 77: Horns snapshot; two BALL_SCREENs in the **same** direction within 1.5 s (handler heading change < 45°); screener 1 ROLLs, screener 2 POPs; optional preceding DHO.
- **Teams documented:** Wall — Swarthmore (D-III) `[P16]`, no D-I team. Pop-and-Flare — Johns Hopkins (D-III, Josh Loeffler); NBA Warriors 77 with Curry (secondary); EuroLeague ASVEL 77 flows (throwback, zoom DHO, guard-guard DHO, reverse ball screen, triple weave into step-up) `[P16]`. Horns 77 — Ohio ~2020-21 (FastModel 22 Mar 2021) `[P18]`; North Carolina ~2021-22 (FastModel 26 Mar 2022) `[P17]`. MSU's EOQ Horns Set `[O89]` is a cross into a ball screen, not sequential, so it does not count.
- **Sources:** `[P16][P17][P18]`.
- **Confidence:** medium (Wall, Pop-and-Flare); medium-high (Horns 77).

#### A3.25 Pin-down Ram (wing pins down for the centre; lift or Spain) — RICHER (extends F5.3 "Ram" with the down-screen version)
- **Name and aliases:** pin-down ram; "head start" ram.
- **Family / sub-family:** F5.3 ram, down-screen version (the repo's ram examples are cross/back rams).
- **Start alignment `[P24]` [HEURISTIC spots]:** 1 top or slot (7.6, 90)/(7.4, 70); wing W (7.2, 40); centre C at the block (2.0, 26); others on the arc.
- **Roles:** W pin-down screener then lifter or Spain back-screener; C ball screener and roller; 1 handler.
- **Ordered actions `[P24]` [HEURISTIC timings]:** (1) W comes down and pins for C (−2 to −1 s); (2) C, with "a head start on his defender", ball-screens for 1 (0); (3) C rolls; W lifts to the top for a shot (0.3–1.5 s); (4) alternative: W back-screens for C = Spain.
- **Usual counters:** drop (F3.1) with X-wing staying home; pre-switch.
- **Detection signature [HEURISTIC]:** SCREEN(down) by a guard/wing on the centre's defender; the centre moves +y ≥ 3 m within 1.5 s and sets a BALL_SCREEN within 2.0 s of the down screen; the down-screener then reaches the top (r ≥ 6.6, \|θ − 90°\| ≤ 20°) within 2.0 s of t₀ (lift) or SCREENs X-centre (Spain).
- **Teams documented:** Purdue 2022-23 (Edey, Smith, Loyer; IU film preview, Feb 2023) `[P24]`.
- **Sources:** `[P24]`.
- **Confidence:** high.

#### A3.26 Shake ball screen (fake wide pin-down, then sprint into a spread ball screen; Michigan/Beilein) — NEW pre-action (name collision with F5.6 "Shake")
- **Name and aliases:** Michigan "shake" ball screen (hand-shake signal). Store as `shake_ballscreen`, separate from the F5.6 spacing tag `shake` (corner lift during a side PnR). See Vocabulary proposals.
- **Family / sub-family:** F5.3 sprint-in after a fake off-ball screen.
- **Start alignment `[P21]` [HEURISTIC spots]:** main guard on the wing/below the arc (7.2, 40) or top; big as if to set a wide pin-down near (3.5–4.5, 30–50); spread spacing.
- **Roles:** big fake pin-down then sprint ball screener; main guard handler; optional re-screener (big or wing guard).
- **Ordered actions `[P21]` [HEURISTIC timings]:** (1) big fakes the wide pin-down (−1.5 to −0.8 s); (2) big sprints up into a "spread ballscreen for the main guard" (0); (3) reads: turn the corner vs a soft hedge or drop for a jumper; re-screen by the big or a wing guard (0.8–2.0 s).
- **Usual counters:** soft hedge or drop, "forcing the guard to take a jumper or floater"; hard to hedge or ice because the screen arrives at sprint speed `[P21]`.
- **Detection signature [HEURISTIC]:** the big decelerates toward a wing defender (within 2.0 m, speed < 1.5 m/s for < 0.5 s; never a SCREEN); then accelerates ≥ 3.5 m/s toward the handler and sets a BALL_SCREEN within 1.5 s; optional re-screen (same pair, second SCREEN within 3 s).
- **Teams documented:** Michigan (John Beilein) 2015-16 (Walton, LeVert, Albrecht; Trey Burke referenced as an earlier user) `[P21]` [pre-window].
- **Sources:** `[P21]`.
- **Confidence:** medium-high.

#### A3.27 MSU "Motion Go Duck-In": sprint-into middle PnR + weak-side pin-down throwback + duck-in — NEW (MSU, 2012-13) [pre-window]
- **Name and aliases:** "Motion Go Duck-In" (FastModel title).
- **Family / sub-family:** F5.3 sprint-up × F5.6 weak-side action × F7 duck-in.
- **Start alignment [HEURISTIC]:** 1 dribbling at 2 on the wing (7.2, 40); 5 below the block (1.85, 3) (x ≈ 1.85, y ≈ 0.1); 4 low on the weak side (2.0, 154); 3 in the weak corner (6.8, 175).
- **Roles:** 1 dribble-at; 2 new handler at the top; 5 sprint screener → roller → duck-in post; 4 pin-down screener and feeder; 3 throwback receiver.
- **Ordered actions `[P52]` [HEURISTIC timings]:** (1) 1 dribbles at 2; 2 cuts to the top (−2 to −1 s); (2) 5 sprints into a middle PnR while 4 pins down for 3, who comes up as the "throwback" if 2 can't reach the rim (0–1.0 s); (3) on the throwback, 2 and 4 look to feed 5, who "ducks in hard" (1.5–3.5 s).
- **Usual counters:** low man tags 5; X3 trails the pin.
- **Detection signature [HEURISTIC]:** DHO or dribble-at exchange at the wing putting a new handler at the top; BALL_SCREEN by a big whose pre-t₀ speed is ≥ 3.5 m/s from r < 2.5; SCREEN(down) at sign(x) opposite the ball within ±0.5 s of t₀; pass to the pin-down user within 3 s; then the screener at r < 2.0 back to the basket receives a post pass within 2 s.
- **Teams documented:** **MSU**, FastModel 8 Mar 2013 (~2012-13): "ran this set on a Thursday night after a dead ball" `[P52]`.
- **Sources:** `[P52]`.
- **Confidence:** medium.

#### A3.28 Weave into high ball screen with roll-and-seal (MSU 2015 Final Four) — RICHER (extends A1.6 with the 2014-15 seal variant and the 5-on-the-block start)
- **Name and aliases:** weave → high ball screen → roll-and-seal; related MSU sets from the same game: sprint-up ball screen; sprint-up + 4/5 stagger for the shooter.
- **Family / sub-family:** F6 weave (DHO chain) → F5 high ball screen → F5.4 seal.
- **Start alignment `[P8]` [HEURISTIC spots]:** perimeter weave above the arc (r 6.8–8.5, θ 45–135°); 5 low at the block (2.0, 26) — Izzo had the 5 start on the block "in near all" high ball-screen sets.
- **Roles:** weave players; target wing handler (Valentine); 5 screener-roller-sealer (Costello); curler (Dawson).
- **Ordered actions `[P8]` [HEURISTIC timings]:** (1) weave handoffs until the ball reaches the target wing (−4 to 0 s); (2) 5 ball-screens (0); (3) on X5's show, 5 rolls and seals Duke's Winslow, rolling "into the 4's area" instead of roll-and-replace (0.3–1.5 s); (4) Dawson curls off that seal into the paint (1.0–2.5 s). Same game: sprint-up ball screen from below the block; sprint-up + a 4/5 stagger for Valentine (the PG can attack with the backside cleared, DHO with the strong-side wing, or wait for the stagger).
- **Usual counters:** the roll-seal punishes X5's show/hedge (F3.2).
- **Detection signature [HEURISTIC]:** canonical `weave` (A4.6); BALL_SCREEN by a player whose pre-t₀ r < 2.5; ROLL to r 1.5–3.0 with the roller stationary (SCREEN) on a help defender within 1.5 s (seal); a cutter passes within 1.2 m of the sealing roller toward r < 3.
- **Teams documented:** **MSU** vs Duke, 2015 Final Four (2014-15) `[P8]` [pre-window]; MSU 2025-26 weave → PnR (A1.6).
- **Sources:** `[P8]`.
- **Confidence:** high (MSU text sequence).

#### A3.29 Ball screen + simultaneous weak-side occupier action — NEW grouping under F5.6 (empty-side + weak-side stagger; ball screen + paint cross screen)
- **Name and aliases:** empty-side ball screen with a weak-side stagger; ball screen + paint cross screen (college examples for F2.5/F16 "Argentina").
- **Family / sub-family:** F5.6 empty side × F8.1 stagger (occupier); F5.6 × F8.1 cross.
- **Start alignment [HEURISTIC]:** empty-side: handler at a wing (7.2, 40) with only the screener on that side; two weak-side screeners and a cutter at (2.4, 141)–(3.95, 118). Cross version: top ball screen (7.6, 90) with two bigs low (2.0, 26)/(2.0, 154).
- **Roles:** guard handler; ball screener; weak-side stagger screeners and cutter (occupiers); cross-screener and post.
- **Ordered actions:** Georgia Tech 2003-04 (Jack, Bynum): empty ball screens for the guard while a weak-side stagger occupies help defenders, run about 10 times vs UConn in the title game `[P23]`. Charleston 2022-23: side cleared for a downhill PG with a triple stagger on the other side `[P14]`. Syracuse 2002-03: a cross screen in the paint alongside the ball screen; Duany found Warrick on the pop when the post feed was cut off `[P23]`. Timing [HEURISTIC]: occupier action within ± 1.5 s of t₀.
- **Usual counters:** help defenders stay attached to the occupiers; switch.
- **Detection signature [HEURISTIC]:** BALL_SCREEN with the empty-side tag (no teammate with the same sign(x) and \|x\| > 3 except the screener) and a SCREEN sequence (≥ 2 screeners for one cutter) at the opposite sign(x) within ± 1.5 s of t₀; cross version = Argentina signature (top ball screen + simultaneous CROSS at y < 2).
- **Teams documented:** Georgia Tech 2003-04, Syracuse 2002-03 `[P23]`; Charleston 2022-23 `[P14]`. MSU playbook title "Ball-screen with Down-Screen for O2" (members-only; content **unverified**) `[P7]`.
- **Sources:** `[P23][P14][P7]`.
- **Confidence:** medium.

#### A3.30 Back-screen series into a re-screen PnR ("Slice Twist", Oregon) — NEW
- **Name and aliases:** Slice Twist (FastModel).
- **Family / sub-family:** F8.1 back screens → F5 ball screen → F5.2 re-screen.
- **Start alignment [HEURISTIC]:** 1 top (7.6, 90); 3 wing (7.2, 40); 4 and 2 low/opposite; 5 high post (4.19, 90).
- **Roles:** 5 serial back-screener, then ball screener and re-screener; 3 handler; 1 hander then top; 2 popper.
- **Ordered actions `[P56]` [HEURISTIC timings]:** (1) 1 hands off to 3; (2) 3 passes back to 1 as 5 back-screens 4; (3) 1 passes to 3 as 5 back-screens 2 (≈ 2 s after the first); (4) 2 pops, 1 shifts to the top, 3 uses 5's ball screen (within 2 s); (5) 5 re-screens for 3 (within 1.5 s), who attacks or hits 5 rolling.
- **Usual counters:** switch the re-screen (**unverified**).
- **Detection signature [HEURISTIC]:** same screener: SCREEN(back) × 2, then a BALL_SCREEN, then a second BALL_SCREEN by the same pair from the opposite side within 2.0 s, all within 8 s.
- **Teams documented:** Oregon (Dwayne Benjamin era), FastModel 15 Mar 2016 (~2015-16) `[P56]` [pre-window].
- **Sources:** `[P56]`.
- **Confidence:** medium.

#### A3.31 Tag-attacking spacing options during a PnR — RICHER (extends F5.6 spacing tags; European/pro examples, secondary aliases)
Source for all rows: Slappin' Glass "Attacking the Tag" primer `[P40]`. **No college team is documented in that source.** Name/aliases = the option name; family F5.6; roles = the named off-ball player(s) plus handler and screener; timing windows are measured from t₀. Confidence: medium for definitions, low for college prevalence. Items already in this file (lift/shake, 45 cut, ghost, shallow cut) appear only where the source adds a PnR-specific role.

| Option | Definition `[P40]` | Start / positions (r, θ) [HEURISTIC] | Ordered actions / timing [HEURISTIC] | Usual counter | Detection signature [HEURISTIC] |
|---|---|---|---|---|---|
| **Dunker shadow** (NEW) | The second big shadows the handler's drive along the baseline, opening a lane and a 2-v-1 | second big in the dunker band (2.0 ≤ \|x\| ≤ 3.5, y ≤ 0.6) | tracks the drive from t₀ to t₀ + 2 s | low man commits to the big | second big's Δx tracks the handler's Δx (correlation > 0.7 over t₀…t₀ + 2 s) while staying in the dunker band |
| **Elbow release** (NEW) | The non-PnR big releases to the elbow and becomes the tag defender's problem; follow-ups: post, cut-and-skip, top-guard step-up, DHO with the elbow big | non-screener big ends at the weak elbow (4.57, 66.4/113.6) | release within 1.5 s of t₀ | tag stays on the roller | non-screening big moves from r < 3 to r 4–5, \|θ − 90°\| 20–30° within 1.5 s of t₀ |
| **Obradović spacing / "wheel"** (NEW) | Two players behind the PnR combine a lift and a baseline cut so the correct tag is unclear | backside wing lifts toward the slot; backside corner cuts the baseline | simultaneous (± 0.7 s) | — | simultaneous LIFT (Δθ toward 90°, Δr ≥ 0) and baseline CUT (y < 1.0, toward r < 2) by two weak-side players |
| **Baseline cut (during the PnR or the short roll)** | Corner player cuts the baseline, including as a short-roller catches at the nail | corner (6.8, 5) → dunker/rim | within 1.5 s of t₀ or of a short-roll catch | low man stays home | CUT from θ ≤ 12° with y < 1.0 within 1.5 s of t₀ or of a short-roll catch |
| **Burn cut ("cut the stunt")** (NEW in the PnR sense) | A pop-capable big cuts when the nail defender stunts, opening space for the popper; used when the PnR goes away from the two-man side | weak big from the arc to the rim | within 0.5 s of the stunt | — | weak-side big CUT toward r < 2 within 0.5 s of a defender's stunt at the nail |
| **Shallow under the PnR** | A baseline or wing player loops underneath the PnR and back out, confusing whether his defender should tag | wing → under P_s → arc | 0–2.5 s | — | path passes rim-side of P_s within 2.5 m, then returns to r ≥ 6.6 |
| **Flare-and-drift** (NEW combination) | Backside corner flares his own man while the 45 player drifts into the space (reverse-angle PnR) | corner flare screen; wing drifts toward the corner | within 1 s | — | SCREEN by the corner player on a weak-side defender plus a teammate moving θ toward 0°/180° behind it within 1 s |
| **Veer (slip/ghost into pin-down)** | The on-ball big slips or ghosts the PnR and flows into a pin-down for a shooter (adds slip/ghost to F5.4 "Veer") | — | within 1.5 s | — | SLIP/GHOST, then SCREEN(down) by the same player within 1.5 s |

**Context for priors (not taxonomy items).** D-I teams averaged just under 9 ball-screen plays per game in 2010, more than doubling over the decade toward 20+ `[P10]`; NCAA average "right around 20 ball screens directly used per game" (Mar 2020) `[P12]`. D-I 2018-19 outcomes: handler keeps 0.91 PPP, pass to screener 1.00, pass to other 0.95 `[P11]`. Across 75 teams, 25 had one player responsible for ≥ 50% of team ball screens; the average top-player share was 46% `[P10]`. MSU 2025-26: when Fears shot poorly, opponents went **under** Kohler/Cooper screens, which "cuts off passes to the roller"; Fears' assists fell from 9.9 (first 7 games) to 8.2 `[P39]`; Fears led the nation at 9.2 assists per game as of 17 Feb 2026, finding bigs for lobs `[P38]`.

**Ball-screen gaps (searched, not found).** No NCAA definition separating "empty corner" (wing occupied) from "empty side" — **unverified**; the "DHO Wheel" page does not define "wheel" `[P32]`; no college Ram film breakdown; no 2024-26 MSU film-level source on Spain/ram/zoom usage; MSU playbook titles "Two Ball-Screens", "Slip-Reverse", "Double Ball-Screen", "Ball-screen with Down-Screen for O2", "DHO/Double-Screens" are members-only `[P7]`; "Inverted Spain" / guard-roller Spain not found.

### A4. F6 Handoff offense: new and richer variants

#### A4.1 Handoff into a trailing third-player ball screen (MSU "Horns Pistol") — NEW (distinct from F6 "Miami", where the hander ball-screens)
- **Name and aliases:** handoff with a trailing ball screen; MSU "Horns Pistol" (FastModel); Duke "Hand Off with Ball Screen" ("basically a double ball screen").
- **Family / sub-family:** F6 DHO → F5 ball screen by a **third** player who trails the handoff.
- **Start alignment (MSU) [HEURISTIC spots]:** Horns: 1 top (7.6, 90); 4 and 5 at the elbows (4.57, 66.4)/(4.57, 113.6); 2 on a wing (7.2, 40); 3 on the weak side (7.2, 140).
- **Roles:** 4 hander who then "rises behind the roll"; 5 flare screener (misdirection) then trailing ball screener and roller; 2 receiver/handler; 1 and 3 weak-side exchange.
- **Ordered actions `[P45]` [HEURISTIC timings]:** (1) 1→4; 5 sets a flare for 1 (misdirection) (−3 to −1.5 s); (2) 4 dribbles toward 2 and hands off, 5 trailing 4 (−1.5 to 0 s); (3) 3 and 1 exchange on the weak side; (4) 5 ball-screens for 2 and rolls; 4 rises behind the roll (0–1.5 s). Duke variant `[P37]`: 1 dribbles over and hands off to 2 (screening the wing defender), 2 dribbles toward the top, 5 ball-screens, 4 pops to the corner. A re-screen version ("let the shooter decide whether to attack off the hand off or the re-screen") appears only in a search snippet for FastModel 1178 — **unverified**.
- **Usual counters:** DHO switch (defense_full F4), then a ball-screen coverage on the trailing screen; the trailing screener's defender is late after guarding the flare.
- **Detection signature [HEURISTIC]:** DHO(a→b) at r ≥ 6.5; a third player *c* within 3.0 m behind *a* during the approach; BALL_SCREEN by *c* on *b*'s defender within 1.5 s of the DHO; ROLL by *c*; *a* moves outward to r ≥ 6.0 within 2 s.
- **Teams documented (MSU first):** **MSU** vs Kansas, 2017 NCAA Tournament (2016-17): early layup for the rolling post `[P45]` [pre-window]; Duke 2005-06 `[P37]`.
- **Sources:** `[P45][P37]`.
- **Confidence:** high (MSU text sequence).

#### A4.2 Horns Swing Pistol (MSU zoom from Horns) — NEW MSU-ordered variant (extends F3.2 "Horns Zoom")
- **Name and aliases:** Horns Swing Pistol (FastModel).
- **Family / sub-family:** F3.2 Horns Zoom × F6 Zoom.
- **Start alignment [HEURISTIC spots]:** Horns: 1 top (7.6, 90); 3 on a wing (7.2, 40); 4 and 5 at the elbows; 2 in a corner (6.8, 175).
- **Roles:** 1 hander then zoom receiver (Cassius Winston); 3 DHO receiver and passer; 5 receiver at the top then zoom hander and roller; 4 down-screener and popper.
- **Ordered actions `[P48]` [HEURISTIC timings]:** (1) 1 dribbles and hands off to 3 (−4 to −3 s); (2) 3 dribbles toward the top and passes to 5 (−3 to −2 s); (3) 3 cuts to the ball-side wing; (4) 4 down-screens for 1 (−1.5 to −0.5 s); (5) 5 dribbles and hands off to 1 (0); (6) 4 pops, 5 rolls (0.3–1.5 s). Purpose: get Winston attacking the basket.
- **Usual counters:** DHO coverages (under/switch, F4); backdoor if 1 is denied.
- **Detection signature [HEURISTIC]:** Horns snapshot; DHO 1→3; pass to an elbow big at the top; SCREEN(down) by the other elbow big on 1's defender; DHO big → 1 within 1.5 s of the down screen; the down-screener POPs and the hander ROLLs within 2.0 s.
- **Teams documented:** **MSU** 2018-19 (FastModel 25 Feb 2019) `[P48]` [pre-window].
- **Sources:** `[P48]`.
- **Confidence:** high.

#### A4.3 DHO → ball screen → veer down screen ("Chicago Pin" / Miami-veer) — NEW combination (F6 "Miami" × F5.4 "Veer")
- **Name and aliases:** Chicago Pin (FastModel title); Miami-veer. Note: "Chicago" here is not the F6 pin-down → DHO "Chicago"; see Vocabulary proposals.
- **Family / sub-family:** F6 Miami × F5.4 veer.
- **Start alignment [HEURISTIC]:** 1 at the slot/top (7.4, 110); 2 on the left wing (7.2, 140); 4 high; 5 low (2.0, 154).
- **Roles:** 1 hander; 4 follow-up ball screener then down-screener; 2 handler; 5 down-screen cutter.
- **Ordered actions `[P55]` [HEURISTIC timings]:** (1) 1 dribbles left to hand off (DHO at t −1.5 s); (2) 4 follows the handoff and ball-screens for 2 (0); (3) 4 then down-screens for 5 (0.8–2.0 s); (4) 2 turns the corner or passes to 5 cutting off the down screen.
- **Usual counters:** switch; X4 sags into the down-screen lane.
- **Detection signature [HEURISTIC]:** DHO(1→2); BALL_SCREEN by a third player *c* on 2's defender within 1.5 s; SCREEN(down) by *c* off the ball within 2.0 s of t₀.
- **Teams documented:** Cal State Bakersfield vs Oklahoma (FastModel 18 Mar 2016; ~2015-16 NCAA) `[P55]`.
- **Sources:** `[P55]`.
- **Confidence:** medium.

#### A4.4 Zoom Reject (reject the DHO → backdoor → empty ball screen → DHO → baseline-angled ball screen) — NEW (extends F6 "Zoom variants")
- **Name and aliases:** Zoom Reject.
- **Family / sub-family:** F6 Zoom × F5.5 reject × F5.6 empty side.
- **Start alignment [HEURISTIC]:** 1 (or the 5) with the ball at the top (7.6, 90); 2 at the block (2.0, 26) or corner (6.8, 5); 3 pins down for 2 from (5.8, 18).
- **Roles:** 2 zoom receiver who rejects and back-cuts; 3 pin-down screener then receiver and empty-side ball screener's partner; 1 hander then passer.
- **Ordered actions `[P13]` [HEURISTIC timings]:** (1) zoom approach: 2 comes off 3's pin-down toward the wing/slot as 1 dribbles to hand off (−1.5 to 0 s); (2) 2 rejects the DHO and back-cuts (0–0.8 s); (3) if not open, the pin-down man turns back, receives, and runs an empty ball screen with the passer (1.0–3.0 s); (4) that can flip into a DHO, then a ball screen angled toward a baseline attack (3.0–6.0 s). Base zoom reads: shoot off the handoff, attack, backdoor, swing, lob to the roller, hit the lifting pin-screener if his defender tags.
- **Usual counters:** jamming/denying the receiver (defense_full F4 "Jam") triggers the reject; switch.
- **Detection signature [HEURISTIC]:** zoom approach (SCREEN(down), then the receiver moves to within 1.5 m of the hander) with no ball transfer; the receiver's velocity reverses toward r < 2 within 0.8 s (backdoor); then a pass to the pin-screener and a BALL_SCREEN with no teammate on that side (empty-side tag) within 4 s.
- **Teams documented:** zoom in general attributed to Alabama (Oats, for Mark Sears), Baylor, Kentucky (Mark Pope: motion built around zoom), Florida and Gonzaga (zoom into continuity ball screen) `[P13]`. Zoom Reject itself: team usage **unverified**.
- **Sources:** `[P13]`.
- **Confidence:** medium (single source, partly paywalled).

#### A4.5 Fake DHO on the wing → baseline drive (clear-out keep) — RICHER (direction subclass of F6 "Fake DHO / Keep")
- **Name and aliases:** "Fake the hand off, drive the baseline"; keeper (NBA).
- **Family / sub-family:** F6 keep, wing/baseline-direction subclass.
- **Start alignment [HEURISTIC]:** hander at the wing (7.2, 40); receiver approaching from the corner (6.8, 5) or top; ball side cleared.
- **Roles:** hander/driver; decoy receiver.
- **Ordered actions [HEURISTIC timings]:** approach slows for 0.3–0.6 s at a hander–receiver distance < 1.5 m; then the hander accelerates ≥ 3 m/s toward the baseline (y decreasing) within 0.8 s. Wing fake handoffs are misdirection for a baseline drive, especially paired with an action where the handoff is used `[P33]`; keeper mechanics: keep when the receiver's defender jumps the handoff; rhythm effect after repeated DHOs `[P15]` (NBA, secondary).
- **Usual counters:** X-hander stays home; X-receiver does not over-commit; jam risk.
- **Detection signature [HEURISTIC]:** the F6 keep signature plus direction: after the fake, the hander's path enters y < 2.0 within 1.0 s, then reaches r < 3.05 with θ ≤ 30° (or ≥ 150°).
- **Teams documented:** none named (TeamFastModel contributor, 2022) `[P33]`. College related: MSU fake DHO → backdoor by the receiver (A1.8) is the receiver-side counterpart.
- **Sources:** `[P33][P15]`.
- **Confidence:** medium-low.

#### A4.6 Weave (chained perimeter DHOs) as a named F6 entry — NEW row; **canonical** F6 `weave` primitive (the weave also appears in A1.6, A1.15 and A3.28 and in motion_starts U05; those point here, A11.16)
- **Name and aliases:** weave; "Weave Zoom" (MSU); weave into high ball screen.
- **Family / sub-family:** F6 DHO chains (perimeter, no big at the top), feeding F5.
- **Start alignment [HEURISTIC]:** three perimeter players above the arc (r 6.8–8.5, θ 45–135°); bigs low or at an elbow.
- **Roles:** weave handlers (each hander follows and replaces); eventual handler; ball screener.
- **Ordered actions [HEURISTIC]:** ≥ 2 DHOs in 4–5 s, alternating players and directions; then a high ball screen within 2 s (A1.6, A3.28).
- **Usual counters:** reject/backdoor off a weave handoff (generic, **unverified** for MSU).
- **Detection signature [HEURISTIC]:** **canonical `weave`:** ≥ 2 consecutive DHOs within 5.0 s (first to last), all at r 6.5–9.0, θ 45–135°, with alternating participants and the hander continuing past the receiver. Variant flags: `weave_3dho_return` (3 DHOs, the last returning the ball to the first handler: MSU Weave Zoom), `weave_then_high_screen` (a ball screen within 2.0 s of the last DHO).
- **Teams documented:** MSU 2025-26 (go-to set) `[M1]`; MSU 2022-23 `[M36]`; MSU 2014-15 `[P8]`.
- **Sources:** `[M1][M36][P8]`.
- **Confidence:** medium-high.

### A5. F8 Off-ball screens and cuts: new classes, new actions and richer rows (extends 8.1–8.3)

Source keys `[X#]` follow the off-ball research note's numbered source list. Defensive counters cite defense_full F5 (off-ball coverages: F5.1 down/pin-down, F5.2 back/UCLA, F5.3 flare, F5.4 cross/post, F5.5 stagger/floppy/Iverson/elevator, F5.6 screener's-defender techniques), F6 (post) and F7 (help).

**Extra primitives for F8 [HEURISTIC unless keyed]:**
- `SCREEN_strict` (≤ 0.3 m/s for ≥ 0.5 s; user within 1.2 m; user's defender within 1.0 m of the screener or slowed ≥ 30% within 1.5 m) and `SCREEN_loose` (= §0.2: < 0.6 m/s for ≥ 0.3 s) are both computed so precision and recall can be tuned.
- **Search window** (Cleaning the Glass, tracking-based off-ball screen data set): only frontcourt screens with the screener ≤ 12.19 m up-court from the ball, screen window ≤ 3 s; CTG favours precision over recall; its main error sources are clustered players, dunker-spot activity, unused screens and out-of-bounds actions `[X3]`. CTG uses 13 off-ball screen types; three are missing from F8 (pin-in, out, middle; A5.1–A5.3) `[X3]`.
- **Speed bands** (converted from km/h) `[X5]`: standing/walking < 1.94 m/s; jogging 1.94–3.89 m/s; running 3.92–5.0 m/s; high speed > 5.0 m/s; sprint usually > 6.69 m/s; elite peak 5.6–6.8 m/s. Used below: **hard cut** = cutter speed ≥ 3.9 m/s for ≥ 0.4 s; jog/set-up = 1.9–3.9 m/s. **Project bands (fixer 2026-10-18, [HEURISTIC], contiguous; these are the thresholds to use):** walk < 1.94; jog 1.94–3.9; run 3.9–5.0; high speed 5.0–6.0; sprint ≥ 6.0 m/s; elite peak 5.6–6.8 m/s is informational only. The `[X5]` values above (gap 3.89–3.92, sprint > 6.69) are kept as the source's conversion and are not used as thresholds.
- **Heading reversal** = change of velocity direction ≥ 120° within ≤ 0.4 s (backdoor, reject, I-cut).
- **Blind-screen spacing:** a screen outside the defender's field of vision must allow "one normal step" before contact `[X7]`; expect back/flare screeners to stop ≥ 0.7–1.0 m behind the defender vs ≤ 0.6 m for down screens (the 0.7–1.0 m value for "one normal step" is **unverified**).
- No opened source gives seconds for off-ball actions; **every timing window in A5 is [HEURISTIC]** and should be fitted on MSU film. The only numeric timing source found is the squared2020 hammer analysis (A5.21) `[X75]`.

#### A5.1 Pin-in screen — NEW screen class (CTG `pin_in`)
- **Name and aliases:** pin-in; pin-in screen; CTG `pin_in`. Related: Exit (§8.1) when the cutter instead moves to the corner. A high-school FastModel play titled "Need a 3: Pin-in" uses the term without defining it `[X12]`.
- **Family / sub-family:** F8.1 screens, new sub-family **interior pin** (screen on a help defender inside the arc to keep a stationary perimeter player open).
- **Start alignment [HEURISTIC, from the CTG definition]:** shooter in the corner (6.67, 3.9) or wing (7.20, 45); screener in the paint/dunker area (2.82, 6.1) or block (2.04, 26.2); handler driving or holding on the opposite side or top (7.60, 90).
- **Roles:** shooter (2/3); screener (4/5, or a guard pinning the low man); handler/driver.
- **Ordered actions [HEURISTIC timings]:** (1) t0: a drive or reversal draws the shooter's defender toward the paint (defender at r ≤ 5.0); (2) t0 to t0 + 1.0 s: the screener moves from inside out to the defender's top/inside shoulder and stops (screener between defender and shooter); (3) t0 + 0.5 to t0 + 2.0 s: pass, catch-and-shoot or attack the delayed closeout. Definition (CTG, paraphrased): a screen for a perimeter player who stays mostly in place while the screener pins that player's defender (or the interior help) inside `[X3]`.
- **Usual counters:** the pinned defender fights over (top-sides) the screener (D-F5.6), or the defence rotates the next defender ("next", D-F5.1).
- **Detection signature [HEURISTIC]:** screener moves outward (Δr > +1.5 m) from r < 4.5 and stops (strict) at r 4.0–6.5 on the line between the target defender and the shooter; shooter displacement during the window ≤ 1.5 m at r ≥ 6.6; target defender inside the shooter (r_def < r_shooter − 1.0 m) and his speed toward the shooter drops ≥ 30% within 1.0 m of the screener. Not a flare (shooter displacement ≥ 3 m away from the ball) and not an exit (shooter moves to θ ≤ 12° along y < 1).
- **Teams documented:** none confirmed at college level. NBA tracking label (CTG) `[X3]`. Michigan 2024-25 pin-ins for corner threes (set_taxonomy §1.9, `[S24]`) — **unverified** in this research (MGoBlog HTTP 403).
- **Sources:** `[X3][X12]`.
- **Confidence:** medium (definition, single tracking source); low (college usage).

#### A5.2 Out screen — NEW screen class (CTG `out`)
- **Name and aliases:** out screen; CTG `out`; close to the FIBA "pop-out cut" (§8.2 has the cut but no screen class).
- **Family / sub-family:** F8.1 screens → "elbow/FT-line out".
- **Start alignment [HEURISTIC]:** screener at the elbow (4.57, 66.4) or nail (4.19, 90); cutter in the lane/mid-post (3.02, 52.7) or block (2.04, 26.2); ball at the top or slot.
- **Roles:** cutter (wing); screener (big at the elbow); passer (1).
- **Ordered actions [HEURISTIC timings]:** t0 cutter starts below the screener; t0 + 0.3–1.2 s cutter passes the elbow screener and arcs outward; t0 + 1.0–2.0 s catch at the wing (7.2–7.7, 30–55). Definition (CTG): a screen near the free-throw line that lets the cutter pop out to a wing `[X3]`.
- **Usual counters:** trail/top-lock (D-F5.1; offense answers with curl or back-cut); switch.
- **Detection signature [HEURISTIC]:** stationary screener at r 3.8–5.2, θ 55–125°; the cutter's path crosses within 1.2 m of him with r increasing ≥ 2.5 m and ending at r ≥ 6.6; the cutter's θ changes ≤ 35° (exits to the same side, unlike Iverson, which crosses x = 0).
- **Teams documented:** no college team confirmed.
- **Sources:** `[X3][X1]`.
- **Confidence:** medium.

#### A5.3 Middle screen — NEW residual screen class (CTG `middle`)
- **Name and aliases:** CTG `middle`.
- **Family / sub-family:** F8.1 screens → residual "toward ball/middle" (CTG includes split, quick actions and BLOB actions here) `[X3]`.
- **Start alignment:** any; most often a post split (F7) or a BLOB box/stack.
- **Roles:** cutter; screener.
- **Ordered actions:** a screen moving the cutter toward the ball or the middle of the court `[X3]`; timing [HEURISTIC] within the 3 s CTG window.
- **Usual counters:** switch (generic).
- **Detection signature [HEURISTIC]:** SCREEN where the cutter's displacement has a positive dot product with the cutter→ball vector (angle < 60°) and the cutter ends with \|x\| reduced by ≥ 1.5 m; exclude if it matches out, Iverson, zipper or flash. Use as a catch-all so the classifier does not force a wrong class.
- **Teams documented:** none specific.
- **Sources:** `[X3]`.
- **Confidence:** medium.

#### A5.4 Turnout (turnout screen) — NEW
- **Name and aliases:** turnout; turn-out screen. Not in the FIBA terminology `[X1]`.
- **Family / sub-family:** F8.1 down-screen sub-family "baseline-to-wing exit". Differs from a pin-down by the cutter's start: the cutter starts in the paint/under the rim and turns out to the wing or top off a screener near the block or lane line.
- **Start alignment [HEURISTIC]:** cutter at the rim front (0.60, 90) or opposite block (2.04, 153.8) after a prior cut; screener at the block/mid lane line (2.04–3.02, 26–53); ball at the wing or top.
- **Roles:** shooter (2); screener (4/5); passer.
- **Ordered actions:** MSU "STS ATO BLOB" (at Duke, 1 Dec 2020): entry to the corner; 3 gets open at the extended elbow; 2 screens for 5 (STS style); 4 sets a turnout for 2 `[X51]`. UConn 2022-23: back screen for 2 to the rim, then 5 sets a turnout for 2, then 2 exits off the opposite big for three `[X27]`. Duke vs MSU (1 Dec 2020) "Wheel Action" options "flare screen/turnout" and "back screen/turnout" `[X71]`. Timing [HEURISTIC]: the turnout begins 0.5–1.5 s after the cutter reaches r < 2.0; catch 1.0–2.0 s later at r ≥ 6.75.
- **Usual counters:** trail (D-F5.1; offense curls back into the lane), under (offense pops/fades), switch; bump (D-F5.6).
- **Detection signature [HEURISTIC]:** cutter at r < 2.5 (often just after a back-cut or STS) with speed < 2 m/s, then accelerates to ≥ 3.9 m/s with Δr ≥ +4.0 m in ≤ 1.5 s, passing within 1.2 m of a strictly stationary screener at r 1.8–3.5; cutter ends at r ≥ 6.75. Pin-down cutters start at r ≥ 4.5 on the wing/corner with the screener arriving from above; turnout cutters start in the restricted area/paint.
- **Teams documented (MSU first):** **MSU** 2020-21 (STS ATO BLOB, at Duke) `[X51]`; Connecticut 2022-23 `[X27]`; Duke 2020-21 vs MSU `[X71]`.
- **Sources:** `[X51][X27][X71][X1]`.
- **Confidence:** medium (term used in three college diagrams; no glossary definition; spots inferred).

#### A5.5 Loop cut / loop action — NEW
- **Name and aliases:** loop; loop cut; "loop under"; loop-around. Close to the FIBA banana cut `[X1]`, but defined by circling a screener or group and coming back out.
- **Family / sub-family:** F8.2 curved cuts; often paired with a down screen or Floppy.
- **Start alignment [HEURISTIC]:** cutter on the wing/slot or at the block; one or two screeners at the blocks/elbows.
- **Roles:** looping cutter; screener(s); passer; post.
- **Ordered actions:** **MSU "Floppy Loop Under"** (2012 NCAA Tournament): 5 pin-downs for 2, who goes to the wing; 3 loops around 4; 4 steps out and receives from 1; 3 screens for 5, who loops under the basket; 5 receives a post feed from 4; if 5 is doubled, 3 is open for a dump-off `[X69]`. Houston "Loop Double" (Nov 2020): 1 dribbles at the 2 side, sending 2 through; 2 tight-curls around 5 and clears back out; 5 "smashes down" on X4 for a paint catch at the FT line; 4 shoots, lobs to 5 (high-low) or isolates `[X74]`. "Michigan Wolverines Loop Down Flare BLOB" (2019; the Michigan label is the contributor's, a Lamar CC assistant): 2 walks his man in and cuts around 4 and 5 to the middle of the lane, 5 pops for the entry, 1 takes a handoff from 5, 3 flares for 4, 5 down-screens 2 to the corner `[X32]`. Timing [HEURISTIC]: loop path 4–7 m, completed in 1.2–2.5 s.
- **Usual counters:** switch the loop (D-F5.5) or trail-and-tag; zone looks.
- **Detection signature [HEURISTIC]:** the cutter's heading rotates ≥ 180° (cumulative signed curvature) within 2.5 s while staying 1.0–2.5 m from a stationary teammate or pair; loop centre within 1.5 m of a stationary player; exit point within 2.5 m of the entry point, or continuing to the perimeter (loop-out) or under the rim (loop-under, ending at r < 1.5).
- **Teams documented (MSU first):** **MSU** 2011-12 `[X69]` [pre-window]; Houston 2020-21 `[X74]`; "Michigan" BLOB 2019 (contributor's attribution; season not stated) `[X32]`.
- **Sources:** `[X69][X74][X32][X1]`.
- **Confidence:** medium ("loop" is not defined on any opened page; meaning inferred from the steps).

#### A5.6 X-cut / cross pin-downs (guards cross off a post, then pin-downs) — NEW
- **Name and aliases:** X; X-cut; "X / Floppy option"; cross pin-downs; "scissors" (FIBA uses scissors for a post split; see A5.25).
- **Family / sub-family:** F8.2 cross-cut pair → F8.1 pin-down pair.
- **Start alignment (WVU "X") `[X73]`:** two-guard front at the slots (7.30, 70)/(7.30, 110); 3 and 4 at the blocks, then popping to the wings (7.20, 45)/(7.20, 135); 5 at the nail/high post (4.19–5.20, 90).
- **Roles:** two guards (1, 2) as cutters; 5 as the cross point, then passer at the top; 3 and 4 pin-down screeners.
- **Ordered actions:** WVU `[X73]`: 3 and 4 pop to the wings; 1→3; 2 cuts over 5 to the block; 1 follows over 5 on the same path (the routes cross at 5); 5 pops to the top and receives from 3; 3 screens for 2 and 4 screens for 1; 5 reads both pin-downs. **MSU "Blast"** (Mar 2015; Izzo set "run for years", used vs Georgia in the 2015 NCAA Tournament): base — guard-to-guard pass, 4 pops out, both guards dive to the rim; "X/Floppy option" — the guards cross and come off opposite-side pin-downs `[X18]`. **MSU "ISO-3 / Chest"**: O1 and O2 X-cut around O3 (high-post catch) in the paint, then use down screens from O4 and O5 back out to the wings `[X70]`. Timing [HEURISTIC]: second cutter starts 0.4–1.0 s after the first; both guards reach r < 2.5 within 2.0 s; pin-downs 0.5–1.5 s after the guards reach the blocks.
- **Usual counters:** top-lock both pin-downs (D-F5.1; offense back-cuts/rejects or the screener slips); switch the two guard defenders at the crossing.
- **Detection signature [HEURISTIC]:** two guards, both starting at r ≥ 6.5, cut toward the rim within 1.0 s of each other; their paths intersect inside r < 4.5 with the crossing point within 1.5 m of a stationary teammate (high post/nail) or within 1.5 m of each other in the paint; within 2.5 s each guard uses a separate pin-down and exits to the side opposite his start (sign(x) flips for both).
- **Teams documented (MSU first):** **MSU** (Blast, 2014-15 NCAA vs Georgia `[X18]`; ISO-3 "Chest", season not stated `[X70]`); West Virginia 2020-21 `[X73]`.
- **Sources:** `[X18][X70][X73]`.
- **Confidence:** medium-high (MSU "Chest" season **unverified**).

#### A5.7 Circle cut (MSU "14-Circle") — NEW cut label
- **Name and aliases:** circle; circle cut; "14-Circle" (MSU; set_taxonomy §3.2 lists the set, not the cut class).
- **Family / sub-family:** F8.2 cut over the high post, then a back screen to the rim (relative of UCLA/Hawk).
- **Start alignment (MSU 14-Circle):** 1-4 high — 1 top (7.60, 90); 4 and 5 at the elbows (4.57, 66.4/113.6); 2 and 3 at the wings/corners.
- **Roles:** 3 circle cutter; 4 back-screener; 5 high-post passer; 2 underneath cutter.
- **Ordered actions `[X70]`:** O2 cuts underneath to the left wing; O3 cuts high over the high-post players; O1→O5; O3 uses O4's screen and cuts to the hoop for a pass from O5; if switched, O4 slips. Stanford 2022-23 also showed a "fake zoom" into a circle cut through the paint (Brandon Angel) `[X29]`. Timing [HEURISTIC]: high cut 0.8–1.5 s; back-screen use and rim catch within 1.5 s of the high-post catch.
- **Usual counters:** switch (D-F5.2; offense answers with the screener's slip); step in front.
- **Detection signature [HEURISTIC]:** cutter moves from the wing (r ≥ 6.5) above both elbow players (min y along the path ≥ 4.6 m) toward the opposite elbow, then turns down (heading change 90–150°) around a stationary elbow screener and reaches r < 2.0 within 2.0 s; ball at the high post (r 4.0–5.5) at the moment of the downward cut.
- **Teams documented (MSU first):** **MSU** (season not stated) `[X70]`; Stanford 2022-23 `[X29]`.
- **Sources:** `[X70][X29]`.
- **Confidence:** medium ("circle" not defined in either source; action step by step).

#### A5.8 Laker cut — NEW
- **Name and aliases:** Laker cut; "Pass into the Post – Laker Cut". Named after the Showtime Lakers per HoopStudent (attribution otherwise unverified).
- **Family / sub-family:** F8.2 post-entry give-and-go (relative of the F7 post split, but no screen).
- **Start alignment `[X8]`:** passer on the wing (7.20, 45); post at the ball-side block (1.90–2.04, 15–26); 1 at the slot (7.30, 70).
- **Roles:** wing passer/cutter (3); post (5); slot (1).
- **Ordered actions `[X8][X9]`:** 1→3 on the wing; 3→5 in the low post; 3 cuts to the rim; 5 hands or passes back. **High-side** version: the cutter goes over the top (between post and elbow), preferred for spacing. **Low-side** version: baseline side with a handoff, useful against "no-middle" defences playing the high side. FastModel (2018): after the post entry, 1 cuts off the post `[X9]`. Timing [HEURISTIC]: cut starts ≤ 0.8 s after the entry is caught; return pass/handoff ≤ 1.5 s after the catch.
- **Usual counters:** the perimeter defender digs/doubles as the cutter passes (HoopStudent warns of steals); post doubles (D-F6); switch.
- **Detection signature [HEURISTIC]:** entry PASS from r ≥ 6 to a receiver at r < 3.5 with his back to the basket; the passer then CUTs with closest approach ≤ 1.2 m to the post, ending at r < 2.0; **high side** if he passes on the larger-y side of the post, **low side** if on the baseline side; return PASS or DHO (< 1.0 m) within 1.5 s. Separate from the post split (F7): in a split the passer screens or is screened by a third player.
- **Teams documented:** no college team confirmed.
- **Sources:** `[X8][X9]`.
- **Confidence:** medium (definition); low (team usage).

#### A5.9 Rub cut and rub screen (two meanings) — NEW
- **Name and aliases:** (a) rub cut — perimeter cut off a stationary post to the rim (Hawk and shuffle cuts are rub cuts off a high post `[X35][X44]`); (b) rub screen — a moving brush on the ball-handler's defender (§8.1 "Brush screen" has no ball-handler version).
- **Family / sub-family:** (a) F8.2 cut; (b) F8.1 brush/rub screen.
- **Start alignment:** (a) Coaching Toolbox "Rub Cut" `[X30]`: 1 dribbles to the FT line; 4 L-cuts to the top; 2 breaks to the FT-line extended; 5 shapes up in the post; 3 is the rub cutter from the wing. (b) any: ball-handler at the top/slot with a teammate running past his defender.
- **Roles:** (a) rub cutter; post; high-low passer. (b) rubbing teammate; handler.
- **Ordered actions:** (a) `[X30]`: 3 cuts off 5 to the rim; 5 steps in; 4 looks high-low; reverse to 2; 3 cross-screens for 5; 4 pin-downs for 3; 4 ball-screens for 3 and rolls; 5 replaces; flows into a side PnR. (b) Hoopscoop (28 Jun 2016) `[X31]`: a rub frees the handler without a set screen; the screener runs past the handler's defender, clipping him, so the handler drives at full speed; timing is critical; the screener's defender is usually not ready to help; officials may call it illegal. Programs in the same article: Colorado School of Mines "1-4 High Rub Side Ball-Screen" (4 runs past 5 and clips 5's defender, then 5 sprints into a ball screen — rub-into-ram); Indiana "X Rub" (two rubs behind the PG); Middle Tennessee "Trail Rub" (1 passes to 4 and cuts in front of him as a rub; 4 drives); Texas A&M "Rub Roll/Replace" (A3.3); South Dakota State "Rub Handoff Ball Screen"; Wisconsin-Platteville "Rub Flash". Timing [HEURISTIC]: (b) handler acceleration within 0.6 s of the brush.
- **Usual counters:** switch on contact (D-F5.5); officials' moving-screen calls.
- **Detection signature [HEURISTIC]:** (a) the cutter's path passes within ≤ 0.8 m of a stationary post (r < 3.5) on the way to r < 2.0 at ≥ 3.9 m/s, with the cutter's defender deflected or delayed within 1.0 m of the post. (b) a teammate moving ≥ 2.5 m/s passes within ≤ 0.8 m of the handler's defender without ever meeting the SCREEN stationarity rule; within 0.6 s the handler's speed rises ≥ 1.5 m/s and his separation from his defender grows ≥ 1.0 m.
- **Teams documented:** (b) Indiana, Middle Tennessee, Texas A&M, South Dakota State (2016 article) `[X31]`. Breakthrough Basketball's "over the top and through the screener's defender" description and Florida "RUB CUT Pistol" — **unverified** (403 / title only). Golden State's "rub" for a BLOB screen on the inbounder — **unverified** (snippet only).
- **Sources:** `[X30][X31][X35][X44]`.
- **Confidence:** medium.

#### A5.10 Pinch fade (fade screen from a pinched big for a nail guard) — NEW
- **Name and aliases:** pinch fade; pinch flare.
- **Family / sub-family:** F8.1 flare sub-family (screen set by a big who first pinches toward the lane).
- **Start alignment (Floppy Diamond) `[X65]`:** 2 under the basket (0.60, 90); 3 at the nail (4.19, 90); 4 and 5 wide on opposite sides (blocks/lane lines).
- **Roles:** 2 floppy shooter; 3 nail guard (fade user); 4, 5 pin-down screeners, one becoming the fade screener.
- **Ordered actions `[X65]`:** 4 and 5 set single pin-downs for 2 on both sides; 2 chooses a side; the opposite big readjusts to set a fade (flare) screen for 3, who exits the opposite way (e.g. 2 uses the left pin-down → 3 uses the pinch fade on the right). Flows into GET or GO handoff actions (F6). Timing [HEURISTIC]: the pinch fade is set 0.3–1.0 s after 2 commits.
- **Usual counters:** switch or chase over (D-F5.3; offense curls to the lane or slips).
- **Detection signature [HEURISTIC]:** a big moves toward x = 0 by ≥ 1.0 m and stops at r 3.5–5.5; a player starting at the nail (r 3.8–4.6, θ 80–100°) moves away from the ball with Δr ≥ +2.5 m passing within 1.2 m of that big (flare rule: angle > 120°); simultaneously another player uses a pin-down on the opposite side.
- **Teams documented:** none named (contributor ELEV|8 Sports) `[X65]`.
- **Sources:** `[X65]`.
- **Confidence:** medium.

#### A5.11 "Elbow Away" (screen away after an elbow entry, then a return pin-down or STS) — NEW (MSU set family, 2020-21)
- **Name and aliases:** Elbow Away Pindown; Elbow Away STS (MSU set names). "Michigan State runs many elbow actions" (FastModel text).
- **Family / sub-family:** F8.1 screen away (generic row exists) + pin-down/STS; F3.4 "Elbow" start.
- **Start alignment [HEURISTIC spots]:** 1 top (7.60, 90); 5 popping to the elbow (4.57, 66.4 or 113.6); 4 on the opposite side (block or wing); 2 and 3 in the corners/wings.
- **Roles:** 1 passer → away screener → shooter; 5 elbow receiver → pin-down screener; 4 rim cutter → passer; 3 cutter to the opposite block.
- **Ordered actions:** **Elbow Away Pindown** `[X52]`: 5 pops to the elbow and receives from 1; 1 screens away for 4, who cuts to the rim; 3 cuts to the opposite block; 5→4; after a brief pause 1 comes back to the top off 5's pin-down; 4→1 for three. **Elbow Away STS** `[X53]`: 5 steps out to the elbow and receives from 1; 1 screens away for 4; 5→4 at the top; 4 reverses to 2 cutting out of the corner; 1 comes back to screen for 5, who cuts to the basket (STS); primary 2→5 in the post; secondary 1 to the top off 4's screen. Timing [HEURISTIC]: away screen ≤ 1.5 s after the elbow catch; return pin-down 1.0–2.5 s after the away screen.
- **Usual counters:** switch the away screen (D-F5.2); top-lock the return pin-down (D-F5.1) → 1 back-cuts.
- **Detection signature [HEURISTIC]:** PASS from the top to r 4.0–5.2, θ 55–125° (elbow); the passer then SCREENs at sign(x) opposite the elbow receiver within 1.5 s; within 3.5 s of that screen the away screener becomes a screen **user** (pin-down by the elbow big: screener stationary at r 3.5–5.5, user +Δr ≥ 2.5 m to r ≥ 6.75 near θ 70–110°). STS variant: the away screener sets a second screen for the elbow big (big −Δr ≥ 3 m toward r < 2).
- **Teams documented:** **MSU** 2020-21 (FastModel 18 Nov 2020, contributor Matt Wheeler) `[X52][X53]` [pre-window].
- **Sources:** `[X52][X53][X50]`.
- **Confidence:** high (two MSU diagrams with step text).

#### A5.12 Chin screen / back-screen lob from the elbow-slot (incl. MSU "clear lob") — NEW off-ball geometry (Chin existed only as an alignment/set name in F3)
- **Name and aliases:** chin; chin screen; chin series (Princeton); "clear lob"; back-screen lob.
- **Family / sub-family:** F8.1 back-screen sub-family "elbow/slot back screen for a wing or guard, usually for a lob or rim cut".
- **Start alignment:** back-screener (usually a big) at the elbow/high post (4.57–5.20, 66–114); cutter at the slot or wing (7.2–7.3, 45–70); ball reversed to the opposite slot/wing; ball-side corner emptied by a clear (MSU).
- **Roles:** back-screener (4/5); cutter/lob target (2/3, or a taller athlete for MSU); passer; clearing PG.
- **Ordered actions:** **MSU 21 Pin Chin** (ATO, 7 Apr 2019): wing DHO ("21"); weak-side pin-down; reversal; the PG clears to the corner; the wing gets a chin screen and the lob; MSU used a taller athlete as the lob target `[X79]` (= F18.1 `[O90]`). **MSU DHO Clear Lob** (opened the second half of the 2019 Elite Eight win over Duke): 1 DHOs to 3; 4 down-screens 2; 3→2; 1 cuts through to the opposite corner; 5 back-screens 3; 2 lobs to 3 — Duke's pressure was used to open the empty side `[X80]` (title in §6 `[S29d]`; sequence now known). **MSU DHO Horns Chin** (Hoopscoop, 17 Dec 2016) `[X33]` (= set_taxonomy §3.2 `[S28]`). Princeton chin series: after slot-to-slot and slot-to-wing passes, 5 at the high post back-screens 3, who cuts to the basket; then 5 flares for 4 to the high-post elbow; continuity repeats `[X34]`. Xavier "Chin Hammer" (2017 NCAA vs Maryland): down screen and zipper for 2, flare for 1, angle ball screen, DHO, 2 to the corner, then 2 attacks baseline and 4 drifts to the corner `[X76]`. Timing [HEURISTIC]: chin screen 0.3–1.0 s after the reversal is caught; lob 0.6–1.5 s after the cutter passes the screener.
- **Usual counters:** switch, step in front (D-F5.2); weak-side low man rotating to the rim (D-F7) — MSU's clear removes that help.
- **Detection signature [HEURISTIC]:** (1) a reversal PASS crosses x = 0 or moves the ball ≥ 4 m laterally; (2) within 1.0 s a screener stationary at r 4.0–5.5, θ 55–125° is between the cutter's defender and the rim (≥ 0.7 m behind the defender); (3) the cutter at r 6.5–7.6 moves −Δr ≥ 4.5 m to r < 1.5 within 1.5 s at ≥ 3.9 m/s; (4) **clear-lob** flag if the ball-side corner/wing area (\|x\| > 3 m, the cutter's finishing side) has no attacker in the 1.0 s before the catch; (5) lob = catch above 3.05 m when ball height is tracked.
- **Teams documented (MSU first):** **MSU** 2015-16 (DHO Horns Chin), 2018-19 (21 Pin Chin; DHO Clear Lob vs Duke, 2019 Elite Eight — the page gives no game date; a related FastModel tweet is dated 5 Apr 2019) `[X79][X80][X33]`; Xavier 2016-17 `[X76]`; Princeton offence (generic) `[X34]`.
- **Sources:** `[X79][X80][X33][X34][X76]`.
- **Confidence:** high for MSU usage; medium for the generic chin geometry.

#### A5.13 Ghost flare (off-ball) — NEW (brief)
- **Name and aliases:** ghost flare; ghost into flare.
- **Family / sub-family:** F8.1 flare; ghost = fake screen with no contact (F5.4 covers ghost ball screens).
- **Start alignment [HEURISTIC]:** player A near a teammate's defender at the slot/wing; flare screener on the weak side.
- **Roles:** ghosting player A (then flare user); flare screener.
- **Ordered actions:** a ghost screen (fake, no contact, pop into space) into a flare screen `[X2]`; ghost screens = faked ball screens followed by a pop (flare option) or slip (Coach's Clipboard, via the ball-screen note `[P34]`). Timing [HEURISTIC]: flare within 1.5 s of the ghost.
- **Usual counters:** switch (D-F5.3).
- **Detection signature [HEURISTIC]:** player A approaches a teammate's defender to ≤ 1.5 m but never meets the SCREEN stationarity rule, then moves away (Δr ≥ +2.0 m toward r ≥ 6.75) and within 1.5 s receives a flare SCREEN from a third player (angle > 120°).
- **Teams documented:** NBA Celtics (glossary) `[X2]`; Saint Mary's "Horns Flare Ghost" (title only) — **unverified**.
- **Sources:** `[X2][P34]`.
- **Confidence:** low-medium.

#### A5.14 "Wheel" action — NEW name only (definition unverified)
- **Name and aliases:** Wheel (UConn motion lists "Wheel", F4 `[O14]`); Duke "Wheel Action".
- **Family / sub-family:** provisional F8 chain.
- **Start alignment:** DHO entry (Duke).
- **Roles / ordered actions:** Duke vs MSU, 1 Dec 2020: DHO entry; 3 sets up his defender; 5 screens for 3 while 1 cuts to the basket and 4 sets up on the perimeter; option 1 flare screen/turnout; high-low; option 2 back screen/turnout; pick-and-pop `[X71]`. The Louisville "DHO Wheel" page also does not define "wheel" `[P32]`.
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC, provisional]:** DHO → off-ball screen on the DHO receiver's side → choice of flare or back screen into a turnout — **not implementable until defined** (no thresholds or windows yet; see A9 "Wheel").
- **Teams documented:** Duke 2020-21 `[X71]`; UConn `[O14]`.
- **Sources:** `[X71][P32]`.
- **Confidence:** low (term **unverified**).

#### A5.15 Floppy — RICHER (F8 had no Floppy row; §3.1 has only the alignment)
- **Name and aliases:** Floppy; Single-Double; Double floppy (two cutters); Floppy X (cutters cross); Floppy Loop Under (MSU); Floppy Punch (post-entry finish); Floppy Diamond (with pinch fade); Reject floppy.
- **Family / sub-family:** F8.1 baseline pin-down family; F3.1 alignment "Floppy".
- **Start alignment `[X1][X16][X67][X68]`:** 1 top (7.60, 90); shooter 2 (and 3 in double floppy) under the basket (0.6, 90) or rim-side of the blocks; 4 and 5 on the blocks/lane lines (2.04, 26.2/153.8); FIBA version: the 3 sets a staggered screen behind one big (stagger at ≈ 2.0 m and 3.0 m from the rim).
- **Roles:** shooter(s); 1–2 screeners per side; passer.
- **Ordered actions:** the shooter reads and chooses a side; catch at the wing (7.2–7.7, 30–50) or slot. Options `[X16]`: catch-and-shoot; curl to mid-range if trailed; flare to the corner if the defender goes over, with the big changing angle to re-screen; pin-down into DHO; screener post seal; hit the screener if two defenders go to the shooter. Offence counters: reject floppy (fake one way, go the other), reject both (backdoor or curl). "Floppy-Elbow": after the floppy, O5 outside the elbow, O2 back-cut or opposite corner, O1 pinch-post handoff, down screen, handoff, back-screen lob; Floppy pick-and-roll: the shooter catches and gets an immediate ball screen from the screener he used `[X68]`. Timing [HEURISTIC]: commit 0.5–1.5 s after the PG reaches the top; wing catch point 1.0–2.0 s after leaving the rim area; pass ≤ 0.5 s after clearing the screen.
- **Usual counters:** top-lock (D-F5.5; offense rejects/back-doors), switch-everything (screener slip/seal, mismatch post), trail-and-tag; bump (D-F5.6).
- **Detection signature [HEURISTIC]:** at the set moment (all 10 in the frontcourt) one or two attackers at r < 1.5 with \|x\| < 1.5 and slow (< 1.0 m/s) teammates at both blocks/lane lines (one each sign of x, r 1.8–3.5); within 2.0 s one inside player accelerates (≥ 3.9 m/s) past a screener (≤ 1.2 m) and ends at r ≥ 6.6, θ 20–70° (or mirror). Single-double: one side has two screeners 1.0–3.0 m apart along the path (stagger) or < 1.2 m apart (double). Double floppy: two inside players exit to opposite sides within 1.0 s. Reject: first 1.0 m of motion to one side, then a heading reversal ≥ 120° and an exit on the other side.
- **Teams documented (MSU first):** **MSU** 2011-12 "Floppy Loop Under" (2012 NCAA) `[X69]`; 2014-15 "Blast" X/Floppy option (vs Georgia) `[X18]`; "Floppy Stagger Punch" vs Ohio State (5 Mar 2012) — **unverified** (page 404). Troy 2016-17 "Floppy Punch" (2017 NCAA R1) `[X66]`.
- **Sources:** `[X1][X16][X67][X68][X69][X18][X66][X65]`.
- **Confidence:** high.

#### A5.16 Iverson — RICHER (adds a metric detection signature and MSU usage to the §8.2 row)
- **Name and aliases:** Iverson cut; Iverson curl; Iverson curl lob; Iverson rip; Iverson ram; Iverson decoy DHO; Iverson stagger; "4-High Iverson". CTG type `iverson` `[X3]`.
- **Family / sub-family:** F8.2 horizontal cut over elbow screens.
- **Start alignment:** 1-4 high — 1 top (7.60, 90); bigs at both elbows (4.57, 66.4/113.6); cutter on one wing (7.2, 45); opposite wing cleared to the corner (6.67, 176.1).
- **Roles:** cutter (2/3); two elbow screeners (4, 5) — sometimes only one `[X2]`; passer (1); weak-side corner spacer.
- **Ordered actions:** the cutter crosses the top over the elbow screens to the opposite wing `[X1][X2]`. Variants `[X42]`: Iverson Curl Lob (ball to the opposite post; cutter curls the second screen for a lob); Iverson Rip (after the wing entry a teammate sets a diagonal screen for a post dive, then staggers); Iverson Decoy DHO. **MSU 4-High Iverson Curl** (3 Nov 2023): 2 Iverson-cuts over 4 and 5; 1→4; 4 hits 2 on the curl `[X63]`. **MSU Iverson Stagger Hit** (7 Jul 2018): 4 and 5 stagger for 3; 1→3, 1 loops to the strong-side corner; second 4/5 stagger for 2; 3→2; a screener dives if his defender helps `[X22]`. Washington Mystics "1-4 Iverson Ram BS" (WNBA, 2021): two Iverson cuts; 4 cross-screens 5; 5 ball-screens 2 (ram); 5 rolls, 4 slips `[X41]`. Timing [HEURISTIC]: wing-to-wing 1.5–2.3 s (≈ 9–10 m at 4.5–6.0 m/s); pass ≤ 0.5 s after clearing the second screener.
- **Usual counters:** top-lock (D-F5.5; offense backdoors via an elbow entry `[X42]`), switch-everything, chase/trail (curl).
- **Detection signature [HEURISTIC]:** cutter starts at r ≥ 6.5 with \|x\| ≥ 3.5; path crosses x = 0 with y 4.6–7.0 m (above the FT line, below the arc band); passes within 1.2 m of one or two stationary players at r 4.0–5.5, θ 55–125°; \|Δx\| ≥ 6.0 m in ≤ 2.5 s; ends at r ≥ 6.6 on the opposite side. **Curl** read: r < 4.0 after the second screener. **Iverson-ram** flag: an elbow screener sets a ball SCREEN ≤ 2.0 s later after himself receiving a cross screen (A5.30).
- **Teams documented (MSU first):** **MSU** 2017-18 (Iverson Stagger Hit) `[X22]`, 2023-24 (4-High Iverson Curl) `[X63]`; MSU "Iverson to Double Screen" 2015 (`[S27]`); Michigan 2024-25 "Iverson Ram" (`[S24]`; **unverified** in this research, 403); UConn `[O14]`.
- **Sources:** `[X1][X2][X3][X42][X63][X22][X41]`.
- **Confidence:** high.

#### A5.17 Elevator / gate — RICHER (adds a detection signature and college examples to the §8.1 row)
- **Name and aliases:** elevator; gate; gator; funnel `[X13]`.
- **Family / sub-family:** F8.1 double screen that closes.
- **Start alignment `[X13]`:** screeners 4 and 5 shoulder to shoulder just above the FT line or near the elbows (≈ 4.3–5.0, θ 75–105°, 1.5–2.5 m apart before closing); shooter on the baseline/corner (6.67, 3.9) or wing; handler at the wing or top.
- **Roles:** shooter (usually the best shooter); two screeners; passer.
- **Ordered actions:** the shooter runs up the lane between the screeners; once he reaches the gap they step together, trapping the defender behind; catch just beyond the arc at the top `[X13]`. Mississippi State 2008-09 (Stansbury): 1→4 and cuts away; 2 to the top, 4→2; 2→1 and staggers with 4 for 3; 1→3; as the ball swings, 1 sprints through an elevator set by 4 and 5 — a timing play where the 3→2 pass must match the elevator `[X60]`. Sacramento Kings "5 Out Elevator" (listing): DHO to 2, elevator by 3 and 4 for 1 `[X17]`. Timing [HEURISTIC]: screeners close 0.3–0.6 s after the shooter passes; catch ≤ 0.8 s later at r 6.75–7.8, θ 70–110°.
- **Usual counters:** switch before the doors close (D-F5.5); defender goes under/around; the screener's defender jumps out (D-F5.6).
- **Detection signature [HEURISTIC]:** two attackers stationary (loose SCREEN) at r 4.0–5.5, 1.2–3.0 m apart laterally; the cutter crosses the segment joining them heading +y at ≥ 3.9 m/s; within 0.6 s their separation drops below 1.0 m (each moves ≥ 0.4 m toward the other); the cutter's defender detours > 1.5 m or slows ≥ 40%; catch at r ≥ 6.75.
- **Teams documented:** MSU "Elevator Drive Option" ATO — **unverified** (page 404); Mississippi State 2008-09 `[X60]`; Virginia Tech "Elevator Decoy" (video title) and Golden State (Mark Jackson era) credited by `[X13]`; Michigan 2024-25 (`[S24]`, **unverified**); Michigan 2025-26 Double Elevator BLOB (A2.29).
- **Sources:** `[X1][X13][X60][X17]`.
- **Confidence:** high (definition); medium (college teams).

#### A5.18 Hammer — RICHER (adds college programs, a tracking metric and timing to the §8.1 row)
- **Name and aliases:** hammer; hammer screen; flip hammer; chin hammer; stagger hammer.
- **Family / sub-family:** F8.1 weak-side flare/back screen timed to a baseline drive.
- **Start alignment [HEURISTIC]:** handler on one wing/slot attacking baseline (ends at r < 3.0, θ ≤ 25°); shooter on the weak-side wing (7.2, 135) moving to the weak corner (6.67, 176.1); screener at the weak-side block/mid lane or high post.
- **Roles:** baseline driver; weak-side shooter; hammer screener (often the centre).
- **Ordered actions:** FIBA: weak-side flare for a shooter cutting wing → corner while the handler drives baseline `[X1]`. NBC (Spurs glossary): often a back screen by the centre on the weak side; strong-side action is the decoy; baseline pass out for the corner three `[X39]`. **Northwestern "Flip Hammer"** (early offense, 19 Mar 2017): 1 hits ahead to 3 and follows for a handoff; 4 loops to the opposite wing and back-screens 2; 2 flares to the corner; 1 drives and passes to 2 `[X77]`. Xavier "Chin Hammer" (A5.12) `[X76]`. squared2020 (SportVU, NBA): Clippers 2012 playoffs — Rudy Gay 1.75 m from the passing lane; his distance to the shooter fell from 3.95 m to 2.86 m during a 0.66 s pass flight (closeout 1.66 m/s); fast closeouts exceed 2.13 m/s `[X75]`. Timing [HEURISTIC]: hammer screen 0.3–1.0 s before the driver reaches r < 3.0; shooter in the corner 0.2–0.8 s before the kick-out; pass flight ≈ 0.5–0.8 s (consistent with 0.66 s `[X75]`).
- **Usual counters:** low man stays home ("next"/stunt, D-F7); switch the flare (D-F5.3); top-side the screener.
- **Detection signature [HEURISTIC, extends §8.1]:** DRIVE (start r > 6.1, reach r < 3.05) with final θ ≤ 30° (or ≥ 150°); concurrently on the opposite sign of x, a SCREEN whose user moves from r ≥ 6.6, θ 120–160° (or 20–60°) to θ ≥ 168° (or ≤ 12°) with the screen ≥ 0.7 m behind the user's defender; the user reaches the corner ≤ 0.8 s before a PASS from the driver at r < 3.5 to the corner (\|Δx\| > 8 m). Secondary metric: closeout speed of the screened defender over the pass flight (m/s) `[X75]`.
- **Teams documented:** Northwestern 2016-17 `[X77]`; Xavier 2016-17 `[X76]`; NBA Spurs, Clippers, Pacers, Timberwolves `[X39][X75]`. A "Virginia late-game hammer against Michigan State" — **unverified** (search summary only).
- **Sources:** `[X1][X39][X77][X76][X75]`.
- **Confidence:** high.

#### A5.19 Shake / lift and blade (corner relocation during a side PnR) — RICHER (adds a detection signature to the F5.6 "Shake" tag)
- **Name and aliases:** shake; lift; lift-up (HoopStudent uses shake and lift for the same move); alternative = FIBA "blade" (cut to the basket instead of lifting). Distinct from "drift" (toward the baseline). Distinct from the Michigan "shake" ball screen (A3.26).
- **Family / sub-family:** F5.6 off-ball spacing tag (an off-ball relocation cut).
- **Start alignment:** shake player in the strong-side corner (6.67, 3.9); side PnR at the wing (7.2, 45); handler driving middle.
- **Roles:** corner player; handler; roller; tagging low man (defence).
- **Ordered actions [HEURISTIC timings]:** t0 ball screen used; t0 + 0.3–1.0 s handler turns the corner toward the middle and the roller dives; t0 + 0.5–1.5 s the corner player lifts to the wing; kick-out ≤ 1.0 s after the lift ends. Definition: the corner player lifts along the perimeter toward the handler during a side ball screen `[X1]`; the dribble goes away from him; he lifts into the vacated wing space; effective vs hedge because the low defender who tagged the roller must leave the corner `[X28]`.
- **Usual counters:** the tagger recovers to the lifted shooter (D-F7); X-out rotations.
- **Detection signature [HEURISTIC]:** during a ball SCREEN on the same sign of x, an off-ball player starting at θ ≤ 15° (or ≥ 165°), r ≥ 6.6 moves along the arc band (r 6.6–8.0) with Δθ ≥ +20° toward the slot within 1.5 s while the handler moves inward (Δx ≥ 1.5 m toward 0). **Blade:** the same corner player instead reaches r < 2.0 during the roll.
- **Teams documented:** none specific.
- **Sources:** `[X1][X28]`.
- **Confidence:** high (definition).

#### A5.20 UCLA — RICHER (adds MSU usage, Wooden high-post detail and timing to §8.1/§8.2)
- **Name and aliases:** UCLA cut; UCLA screen; up screen. FIBA: UCLA **screen** = low post → slot/top; UCLA **cut** = top → low post over a high-post screen `[X1]`.
- **Family / sub-family:** F8.1 back-screen family.
- **Start alignment `[X38]`:** two-guard front: guards at the slots (7.3, 70/110); centre moving to the ball-side elbow (4.57, 66.4); small forward L-cuts to the wing.
- **Roles:** passing guard → UCLA cutter → post-up; elbow screener; wing receiver.
- **Ordered actions:** Fraschilla (ESPN, 2003, "Wooden's West Coast Offense"): guard-to-guard entry; 3 L-cuts to the wing; 5 to the ball-side elbow; the off-guard UCLA-cuts off 5 and posts up; 3 to the opposite block; 1 to the FT-line extended; high-post pass to 5; 4 down-screens the off-guard; double-down screen; options include STS, a blind-pig counter when the guard-to-guard pass is denied, an X cut off the high post with a handoff, and "guard around" `[X38]`. NBC: pass above the arc to the wing, elbow screen, cutter to the rim toward the baseline `[X37]`. **MSU "Chest Down"** (3 Apr 2015): Chest (wings get down screens from 4 and 5), 2 catches on the wing, 1 UCLA-cuts, 5 continues to a wing ball screen, 1 continues off a double screen `[X78]`. Timing [HEURISTIC]: cut starts ≤ 0.8 s after the wing catch; cutter at r < 2.0 within 1.5 s.
- **Usual counters:** switch, step in front, show-and-recover (D-F5.2). Synergy logs the cutter's shot as Cut `[O53]`.
- **Detection signature [HEURISTIC]:** PASS from the slot/top (r ≥ 6.75, θ 60–120°) to the wing; the passer moves −Δr ≥ 4.5 m to r < 2.0 within 1.8 s, passing within 1.2 m of a stationary teammate at the ball-side elbow (r 4.0–5.2, θ 55–80° or 100–125°) who is ≥ 0.7 m behind the passer's defender.
- **Teams documented (MSU first):** **MSU** 2014-15 (Chest Down) `[X78]`; UCLA (Wooden, historic) `[X37][X38]`. MSU 2024-25 "Shuffle Pick-and-Roll" (A1.2) may use a UCLA cut.
- **Sources:** `[X1][X37][X38][X78]`.
- **Confidence:** high.

#### A5.21 Hawk cut — RICHER (adds origin, reads and detection to the first-pass MSU "Hawk" rows)
- **Name and aliases:** Hawk; Hawk cut (rub cut off a high-post back screen after a dribble entry).
- **Family / sub-family:** F8.2 rub cut off a high-post back screen; relative of the UCLA high post and a shuffle derivative `[X35]`.
- **Origin:** Hubie Brown, Atlanta Hawks; also Chuck Daly, Rudy Tomjanovich, Flip Saunders `[X35][X36]`.
- **Start alignment `[X36]`:** two guards at the slots (7.3, 70/110); O4 at the high post/top of the key (≈ 5.2–6.0, 90); O3 and O5 stacked low on the weak side; corner-3 variation: O3 in the weak corner, O5 halfway up the lane line.
- **Roles:** dribbling PG; O4 back-screener; O2 Hawk cutter; O3/O5 weak-side screen pair.
- **Ordered actions:** O1 dribbles to the wing; O4 back-screens O2; O2 cuts over or behind O4 to the ball-side block; pass on the cut or post-up; else O1→O4 stepping out to the top; O3 comes off O5's screen (corner-3 version: O5 down-screens O3, then pops) `[X36]`. Reads `[X35]`: over the top if the defender chases; under/behind if he goes over; pop back for a jumper if he goes under; switch → screener rolls or cutter clears to the corner; anticipation → screener slips. **MSU "Hawk Double Cross"** (17 Feb 2017; Nairn, Harris, Bridges, Langford, Ward): 1 dribbles to the wing, pushing 3 under the basket; 4 sets a diagonal screen for 2, who cuts to the basket; reversal to 4 popping behind the top of the key; 3 and 5 double-stagger for 2; 3 turns and screens 5 (STS); 4 screens the screener, then slips; 5 screens for 3, who attacks; 2 drifts to the corner `[X21]` (= set_taxonomy `[S29b]`). Timing [HEURISTIC]: back screen ≤ 0.6 s after the dribble entry reaches the wing; cutter at the block within 1.5 s.
- **Usual counters:** switch / show-and-recover (D-F5.2); early post doubles.
- **Detection signature [HEURISTIC]:** PG dribble from the slot to the wing (Δθ ≥ 15°, ends r 6.8–8.0, θ 25–55°); within 0.8 s the opposite slot guard cuts diagonally (Δx toward the ball ≥ 2.5 m and −Δr ≥ 4.5 m) past a stationary high-post player (r 4.5–6.5, θ 70–110°) to the ball-side block (r < 2.5, same sign of x as the ball). §8.1 "Diagonal (BLOB)" covers only the BLOB variant.
- **Teams documented (MSU first):** **MSU** 2016-17 `[X21]`; NBA Hawks (historic) `[X35]`.
- **Sources:** `[X35][X36][X21]`.
- **Confidence:** high.

#### A5.22 Blind pig — RICHER (adds a detection signature to the §8.2 / §3.4 rows)
- **Name and aliases:** blind pig; blind pig action (FIBA also lists a "blind pig pass": a two-handed pass behind the legs or back by the big) `[X1]`.
- **Family / sub-family:** F8.2 backdoor via a flash to the high post (pressure release).
- **Start alignment `[X10]`:** 1 at the slot/top; 3 on the wing (denied); 2 on the weak-side slot/wing (denied); 4 weak-side forward flashing to the high post (5.2, 90) or elbow.
- **Roles:** handler; flashing big; backdoor cutter.
- **Ordered actions:** 1 cannot pass to 3; the lag pass to 2 is also denied; 4 flashes to the high post and catches; 2 back-cuts; 4 hits 2 at the rim `[X10]`. UCLA high post: if the guard-to-guard pass is overplayed, the power forward flashes and the off-guard cuts backdoor `[X38]`. Memphis Grizzlies ATO (2015 playoffs vs Golden State): Gasol flashes to the high post after Conley comes off a screen; Conley back-cuts high side; backdoor pass for a floater (frames: 5 and 4 set a double low screen; 1's defender overplays; 5 flashes to the elbow and hits 1 backdoor) `[X11]` (NBA, secondary). Timing [HEURISTIC]: back-cut 0.0–0.5 s after the flash catch; pass ≤ 1.0 s after the catch.
- **Usual counters:** weak-side low-man help on the backdoor (D-F7); deny the flash.
- **Detection signature [HEURISTIC]:** (1) a big moves +Δy ≥ 2.5 m from r < 3.0 (or the weak side) to r 4.0–5.5, θ 60–120° and catches; (2) within ± 0.5 s of the catch a perimeter player at r ≥ 6.0 reverses heading (≥ 120°) and moves −Δr ≥ 4.0 m; (3) pass from the high post to that cutter at r < 2.5 ≤ 1.2 s after the catch. Precondition flag: the cutter's defender was within 1.0 m of the passing lane in the 1.0 s before the flash.
- **Teams documented:** no current college program confirmed; UCLA high post (Wooden era) `[X38]`; Memphis Grizzlies 2015 `[X11]`.
- **Sources:** `[X1][X10][X11][X38]`.
- **Confidence:** high (definition); low (current college usage).

#### A5.23 Shuffle cut — RICHER (adds origin and a detection signature to the §8.2 row)
- **Name and aliases:** shuffle cut (rub cut off a high-post screen to the basket).
- **Family / sub-family:** F8.2; F4.1 "Shuffle" continuity.
- **Origin:** Bruce Drake, Oklahoma, early 1950s; predecessor of the Princeton, Flex, Hawk and Reverse Action offences `[X44]`.
- **Start alignment `[X44]`:** O1 point; O2 feeder on the wing; O3 wing/side cutter; O4 corner; O5 high-post screener (the only main screener).
- **Roles:** O3 shuffle cutter; O5 high-post screener; O2 feeder.
- **Ordered actions `[X44]`:** O3 passes to O1 and walks X3 into O5's screen; O1 relays to O2; O2 feeds O3 on the rub cut for a layup; O4 to the weak-side rebound spot; if covered, O2→O5 popping off O1's down screen; O4 flashes to the middle as O3 clears to the corner; overload-opposite repeats. Against a switch, O5 sets a post screen facing the basket and O3 goes over it. Timing [HEURISTIC]: cut starts ≤ 0.6 s after the cutter's pass; layup pass ≤ 1.8 s later.
- **Usual counters:** switch (offence answers with the facing post screen) `[X44]`.
- **Detection signature [HEURISTIC]:** PASS by A from the weak-side wing/slot toward the top; A then cuts diagonally past a stationary high-post screener (r 4.0–5.5, θ 60–120°) to the ball-side block (r < 2.5, ball-side sign of x) with −Δr ≥ 4.0 m in ≤ 1.8 s. UCLA vs shuffle: the UCLA cutter passes **to** the ball-side wing and cuts on the ball side; the shuffle cutter passes **away** from the side he finishes on, starting weak side.
- **Teams documented:** Oklahoma (Drake) `[X44]`; Air Force (Spear) and North Carolina (Dean Smith) per search summaries — **unverified** beyond `[S35]`.
- **Sources:** `[X44]`.
- **Confidence:** medium-high.

#### A5.24 Zipper — RICHER (adds MSU sets, a metric signature and the CTG inbound caveat)
- **Name and aliases:** zipper; zipper screen; zipper cut; "two zipper cuts".
- **Family / sub-family:** F8.1 down screen at the block for a vertical cut to the slot `[X1][X2]`.
- **CTG caveat:** CTG's `zipper` is a down screen **before a sideline inbound pass**, for the cutter to come up the court — narrower than the coaching meaning `[X3]`. Keep the coaching meaning and flag the inbound context separately.
- **Start alignment:** cutter at the low block (1.90–2.04, 15–26) strong or weak side; screener coming down from the slot/elbow; ball at the top or out of bounds.
- **Roles:** zipper cutter; down-screener; passer.
- **Ordered actions:** **MSU Zipper ATO** (Coaching Toolbox): 4 and 5 cross-screen for 2; option 1: 2 over the top to the left wing, 3 back-cuts, 1 dribbles to the left wing and passes to 4, 5 cuts to the basket; option 2: 2 back-cuts after passing to 4; option 3: 2 curls 4's cross screen to the basket `[X58]` (= set_taxonomy `[S29c]`). **MSU Zipper Spain PNR SLOB** (17 Mar 2023) (A3.21) `[X57]`. Xavier Chin Hammer: 3 down-screens 2, "two zipper cuts" to the wing `[X76]`. CelticsBlog: zipper cut, then a weak-side pin-down curled into a stampede cut `[X2]`. Timing [HEURISTIC]: block to slot in 1.3–2.0 s (≈ 5–6 m at 3–4.5 m/s); catch at r 6.75–7.6, θ 60–80°.
- **Usual counters:** top-lock (D-F5.1; cutter back-cuts or goes under the screen); switch.
- **Detection signature [HEURISTIC]:** user starts at r < 2.6, θ 10–40° (or mirror); screener arrives from above (Δy ≤ −1.5 m) and stops within 1.2 m of the user's path at r 2.5–4.5; user moves +Δy ≥ 4.0 m to r ≥ 6.75, θ 55–85° in ≤ 1.6 s on a near-vertical path (\|Δx\| < 0.6·\|Δy\|). Inbound flag if the ball is out of bounds.
- **Teams documented (MSU first):** **MSU** (Zipper ATO, season not stated `[X58]`; Zipper Spain PNR SLOB 2022-23 `[X57]`); Xavier 2016-17 `[X76]`; UConn `[O14]`.
- **Sources:** `[X1][X2][X3][X58][X57][X76]`.
- **Confidence:** high.

#### A5.25 Cross screen, post split (straight / reverse), STS, Ricky, Twirl, off-ball Ram, wide pin-down reads, stagger, fake-DHO backdoor, baseline runner, stack-flash — RICHER rows (compact full format)

| Item (extends) | Name and aliases | Family | Start alignment (r, θ) [HEURISTIC] | Roles | Ordered actions with timing [HEURISTIC timings] | Usual counters | Detection signature [HEURISTIC] | Teams (MSU first), season, keys | Confidence |
|---|---|---|---|---|---|---|---|---|---|
| **Cross screen** (§8.1) | cross screen; double cross; cross → curl; cross into ram; "Floppy cross" | F8.1 | screener and user at y < 2.0, blocks (2.04, 26.2/153.8) | screener; post user | Definition: low post to opposite low post `[X1]`; horizontal screen in the paint for post play or to flow into another screen `[X2]`; CTG `cross` near the block `[X3]`. **Timing rule** `[X7]`: the big should not start early — wait, move away from resistance, then accelerate. Variants: double cross (MSU Zipper ATO, 4 and 5 for 2 `[X58]`); cross → curl (option 3); cross into ram (A5.30); Floppy cross (2 and 4 double cross for 5 after a floppy `[X67]`) | step under and switch (high cut) / stay (low cut), front (D-F5.4) | both at y < 2.0; screener strictly stationary with \|x\| ≤ 2.0; user crosses x = 0 with \|Δx\| ≥ 3.0 m ending at r < 2.5; **high cut** if the user passes above the screener, **low cut** if below; **wait flag** if the user's speed stays < 1.5 m/s until ≥ 0.3 s after screener stationarity, then ≥ 3.0 m/s within 0.5 s; double cross = two stationary screeners < 1.2 m apart in the paint | **MSU** Zipper ATO `[X58]`; Hawk Double Cross 2016-17 `[X21]` | high |
| **Post split: straight vs reverse** (F7 "Post split") | split action; straight split; reverse split | F7 / F8.1 | post at the block (2.04, 26.2); passer on the wing (7.2, 45); top player (7.6, 90) | wing passer A; top player B; post | FIBA `[X1]`: **straight** = the wing passer, after the entry, screens for the top player; **reverse** = the wing passer receives a screen from the top player. Warriors: the entry passer immediately screens away for the nearest player; shooter reject/back-cut or screener slip `[X26]`. Timing: screen within 1.0 s of the entry | switch; slip vs switch | entry PASS (receiver r < 3.5); within 1.0 s a SCREEN between A and B; **straight** if A is stationary, **reverse** if B is; slip flag = screener stationary < 0.3 s then −Δr ≥ 3 m | Villanova ("loves to go into split and slip the screener", undated) `[X26]` | high (definition); medium (Villanova) |
| **Screen-the-screener (STS)** (§8.1 "STS") | STS | F8.1 | varies | first screener → screenee; second screener | FIBA definition `[X1]`. MSU sets: STS ATO BLOB (A1.15, A5.4) `[X51]`; Elbow Away STS (A5.11) `[X53]`; 1-4 STS (A1.15) `[X54]`; Hawk Double Cross (3 screens 5, then 4 screens 3) `[X21]`. Timing: the STS screen arrives 0.3–1.5 s after the first screener's stationary window ends | switch both screens and "reconnect", top-side the second screener (D-F5.5) | screener *s* goes from SCREEN-giver to SCREEN-receiver within 1.5 s; the STS user usually moves −Δr ≥ 3.5 m (to the rim) after a back/cross first screen, or +Δr ≥ 3.0 m (to the top) after a down first screen | **MSU** 2016-17, 2020-21, 2023-24 `[X21][X51][X53][X54]` | high |
| **Ricky** (§8.1 / §3.4) | Ricky; rip then down | F8.1 | user at the slot/wing; screener at the elbow/block | single screener; user | Back screen then down screen for the same player `[X1]`; cutter cuts off the rip, stops, turns, comes off the down screen `[X2]`; the re-screen must be immediate `[X14]`. **Texas Tech "Stack Rip Pindown"** (base offense, 18 Nov 2020): 2 pops for the pass; 1 cuts to the basket off 5's screen; if not open, 5 sets a second screen for 1, who catches for the shot `[X72]`. Timing: second screen stationary ≤ 1.2 s after the cutter passes the first | — | same *s*, same *u*; SCREEN #1 with *u* −Δr ≥ 3 m (back geometry, *s* ≥ 0.7 m behind *u*'s defender); *u* reaches r < 3.0 and reverses heading; SCREEN #2 by *s* (*s* moved ≤ 3.0 m) with *u* +Δr ≥ 3.5 m to r ≥ 6.6; total ≤ 3.0 s. Compare Wiper and MSU Spartan Re-Screen (F18.1) | Creighton, UConn, Alabama, Virginia, VCU, Penn State (no seasons) `[X14]`; Texas Tech 2020-21 `[X72]` | high (definition); medium (teams) |
| **Twirl** (§8.1) | twirl; twirl-screen variant | F8.1 | stagger along the lane line | user; first screener (twirler); second screener | Curl the first of two staggered screens; the first screener then comes off the second `[X1][X15]`. **Dayton 2023-24:** slice screen into a stagger on the right, then a stagger on the left where Enoch Cheeks twirls the stagger and **screens for Koby Brea** instead of using the screen `[X15]`. Timing: the first screener uses the second screen ≤ 1.0 s after the curl | switch | stagger (screeners 1.5–4.0 m apart along the path); the user curls inside the first screener; the first screener then moves ≥ 2.5 m within 1.2 m of the second screener; **twirl-screen** variant: the twirler becomes a SCREEN-giver for a third player within 1.0 s | Dayton 2023-24 `[X15]` | medium |
| **Ram, off-ball part** (F5.3 "Ram") | ram screen; big-big ram; rub-ram | F8.1 → F5.3 | big at r < 4.5; guard/wing screener at r 2.0–5.0 | ram screener; big | On-ball screen in which the screener first receives an off-ball screen `[X1]`. Mystics "1-4 Iverson Ram BS" (A5.16) `[X41]`; Colorado School of Mines rub-into-ram (A5.9) `[X31]`; UConn "Ram Veer Reject Exit" (F5.7). The "guard/wing screening down or across on a big in the middle of the lane" description is **unverified** (snippet; page 404). Timing: the big becomes a ball screener 0.8–2.0 s after the off-ball screen | pre-switch; drop with X-ram-screener home | off-ball SCREEN whose user is a big at r < 4.5 and whose screener is a guard/wing (or a big) stationary at r 2.0–5.0; the big moves ≥ 3 m toward the handler and becomes a ball screener within 0.8–2.0 s; **rub-ram** if the first screen fails stationarity | — (see A2.2, A2.3, A3.19, A3.25) | medium |
| **Wide pin-down / corner pin reads** (§8.1) | wide pin-down; corner pin; reads: reject, curl, **flash** (NEW read), pop; **under-the-screen** (NEW read); screener slip | F8.1 / F8.3 | receiver low in the corner, wider than the screener; screener starts high at the slot `[X64]` | receiver; screener | Geometry: screen angled toward or in line with the passer; catch even with the wing/FT line `[X64]`; screener faces the baseline `[X2]`; CTG `wide_pin_down` `[X3]`. Reads `[X64]`: **reject** (overplay → plant and cut to the rim; screener pops back); **curl** (trail + attached screener's defender → curl to the elbow); **flash** (trail + screener's defender drops on the curl → space is toward the passer); **pop** (under → stop behind the screen). **Under** (Hoop Vision, Winston vs Ohio State, 2019-20): vs extreme corner-pin denial, cut **under** the screener, between screener and baseline, "similar to zipper action" `[X81]` | top-lock, switch, hard hedge (screener slip) | user starts at θ ≤ 25° or ≥ 155°, r ≥ 6.0; screener arrives from above (Δy ≤ −2.0 m) and stops at r 4.5–6.5, θ 15–40°; **curl** = end r < screener r − 1.0 m with θ toward 90°; **flash** = exit heading within 30° of user→ball, end r 5.0–6.5; **pop/straight** = end r ≥ 6.75, θ 30–55°; **reject** = heading reversal ≥ 120° before reaching 1.2 m of the screener, then −Δr ≥ 3 m; **under** = user passes on the baseline side of the screener (user y < screener y − 0.5 m) and ends at r ≥ 6.6 | **MSU** 2019-20 (Winston) `[X81]`; MSU 2024-25 "77 Wide Pindown" (A1.1); Arkansas 2025-26 opening set vs MSU (pin-downs for both corner wings) `[X47]` | high |
| **Stagger / double stagger** (§8.1) | stagger; double stagger (note: CelticsBlog uses "stagger" also for ball-handlers, "77") | F8.1 | two screeners on the lane line/elbow | user; two screeners | Two screens not next to each other, set at once for one cutter `[X1][X2]`. MSU: Iverson Stagger Hit `[X22]`; Hawk Double Cross `[X21]`; 1-4 High Curl Double Flare (2015-16 vs Florida) `[X20]`; Stagger Slip Curl & Pop `[X19]`; 1-4 STS stagger away `[X54]`. Timing: user passes screener 1 then 2 within 1.2 s | top-lock, switch-everything (D-F5.5) | two stationary screeners 1.5–4.0 m apart along the path (double if < 1.2 m), both within 1.2 m of it; **slip** flag if one leaves before the user arrives (stationary < 0.3 s, then −Δr ≥ 3 m) | **MSU** 2015-16 to 2023-24 `[X19][X20][X21][X22][X54]` | high |
| **Backdoor off a fake DHO** (§8.2 "Backdoor") | `backdoor_fake_dho` | F8.2 / F6 | see A1.8 | receiver; hander | MSU 2025-26 vs Iowa: Cooper and Carr close the gap as if for a DHO; Carr feels the overplay and back-cuts for a dunk `[X47]` (A1.8). MSU Zipper ATO backdoors by 3 and by 2 `[X58]`. Timing: reversal ≤ 0.5 s after the approach | see A1.8 | DHO approach (hander–receiver < 2.0 m, hander holding) with no transfer; within 0.5 s the receiver reverses heading (≥ 120°) and moves −Δr ≥ 4.0 m to r < 2.0; precondition: the receiver's defender is between receiver and hander | **MSU** 2025-26 `[X47]` | high |
| **Baseline cut / baseline runner** (§8.2 / F11.1) | baseline runner; baseline cut to the rim | F8.2 | runner in a corner or at the block | runner; screener at the block | **MSU "Over-Under"** (3 Apr 2015): 3→1 wing entry; 3 gets a back or flare screen while 2 runs the baseline off 4's screen; as 1→2, 1 comes off a flare; 2 dribbles out of the corner and 3 runs off the baseline screen `[X61]` (= `[S12b]`). MSU 2025-26: Carr "cuts hard along the baseline" during the Cooper DHO (A1.7) `[X47]`. Timing: runner covers \|Δx\| ≥ 4 m in ≤ 1.8 s | — | off-ball player moves along y < 1.0 with \|Δx\| ≥ 4.0 m in ≤ 1.8 s, optionally past a stationary screener at the block; **baseline cut to the rim** if it ends at r < 1.5 during a ball screen or DHO | **MSU** 2014-15 `[X61]`, 2025-26 `[X47]` | high |
| **Flash — stack-flash flag** (§8.2 "Flash") | stack flash | F8.2 | flasher in a vertical paint stack | flasher | MSU ISO-3 "Chest": vs heavy pressure, O3 (lowest in a paint stack) flashes to the high post; after a wing pass, O5 flashes to the ball-side elbow `[X70]`; MSU Wizard (F18.1). Timing: flash ≤ 1.5 s | deny the flash | existing §8.2 flash rule plus **stack-flash** flag: the flasher starts in a vertical stack (≥ 3 players within 1.5 m in x along the lane) at r < 2.5 | **MSU** (season not stated) `[X70]` | medium |

**Re-confirmed with no new content** (FIBA PDF and CelticsBlog re-opened `[X1][X2]`): down/pin-down, flare, back, cross (generic), staggered, hammer (base rule), flex, slice, gut, wedge, exit/baseline exit, screen your own, off-ball slip, brush, blade, shot screen, hostage, wiper, curl/fade/straight reads, give-and-go, I-cut, V/L-cut, stampede, 45 cut, delayed cut, thru-cut. **Off-ball gaps:** pin-in in college (only CTG defines it); MSU "Elevator Drive Option" and "Floppy Stagger Punch" pages returned 404; "wheel" undefined; "turnout" has no glossary definition; Laker cut has no college program; Hoop Vision off-ball rankings, Iverson dictionary and twirl articles are paywalled beyond the intro; Breakthrough Basketball rub cut and the Medium "Basketball Action Dictionary" returned 403.

### A6. F13 Special situations: rules layer, BLOB, SLOB, ATO, end of clock / half / game (extends 13.1–13.8)

Source keys `[Q#]` resolve in the special-situations block of the Additional sources list. Rule numbers are from the **2024-25 NCAA Men's Basketball Rules** (NCAA-published, August 2024) `[Q1]`; the 2025-26 book exists but was too large to fetch, so **2025-26 rule wording is unverified**; 2026-27 adjustments are from NCAA.org (8 May 2026) `[Q2]`. Rule items already in F13 (OREB → 20 reset `[O26]`, frontcourt defensive-foul → 20 `[O27]`, BLOB/SLOB spots `[O27]`, live-ball timeouts `[O26]`, no advance after a timeout `[O67][O68]`) are not repeated.

**Restart landmarks and primitives [HEURISTIC unless keyed]:** BLOB designated spot = end line 0.91 m outside the lane line `[Q1]` → (±2.74, −1.60) = (3.17, −30.3°) [left (3.17, 210.3°)]; BLOB inbounder ≈ 0.30 m behind the line (3.33, −34.7°) (same offset as A0). SLOB designated spot = sideline at the 8.53 m mark (8.53 m from the end line) `[Q1]` → (±7.62, 6.93) = (10.30, 42.3°); SLOB inbounder (10.55, 41.1°). Lane-line stack spots 0.9 m apart above the block: (2.58, 35.5°), (3.19, 48.8°), (3.91, 57.5°). Backcourt 8.53 m mark (20.03, 67.6°). Far end line centre (27.05, 90°). Left-side angles: 180° − θ in court; 180° + \|θ\| behind the end line.
- `INBOUND_EVENT`: ball held by an attacker whose feet are out of bounds (\|x\| > 7.62, y < −1.60 or y > 27.05) with the game clock stopped. Sub-types: BLOB (y < −1.60, \|x\| ≤ 7.62); SLOB (\|x\| > 7.62, y < 12.73); BACKCOURT_SLOB (\|x\| > 7.62, y > 12.73); FULLCOURT (y > 27.05).
- `t_dispose` = official hands/bounces the ball to the thrower (5-s count starts) `[Q1]`; `t_release` = ball leaves the thrower; `t_touch` = first legal in-bounds touch — game and shot clocks start here `[Q1]`. **All A6 timing windows are measured from t_touch unless stated.**
- `LOB_CATCH`: ball apex ≥ 3.6 m and catch at r ≤ 1.5 by a player whose hands are ≥ 3.0 m. `DHO` (restart version): hand-to-hand within 0.6 m, no air time > 0.2 s.
- Alignment snapshot = the four in-bounds attackers at t_dispose (or the last frame before any reaches 2.5 m/s).

#### A6.1 NCAA rules that control special-situation timing — NEW rule-layer items (F13 rule layer)
Each row is a rule-derived label: name, the rule `[Q1]`, the timing window it implies, and the detection signature [HEURISTIC]. Confidence high for every rule row (rule text read); MSU cases as stated.

| Item | Rule (paraphrased) | Why it matters | Detection signature [HEURISTIC] |
|---|---|---|---|
| **R1 Five-second throw-in count** ("five on the inbound") | The count begins when the ball is at the thrower's disposal and ends at release; > 5 s is a violation `[Q1]` (7-6.4, 7-6.6, 7-6.7; 9-2) | caps every inbound set | t_release − t_dispose ≤ 5.0 s; a set with no receiver separation ≥ 1.5 m by t_dispose + 4.0 s = "burned inbound" (expect a timeout or a safety pass) |
| **R2 Designated-spot geometry** | Spot 0.91 m wide, no depth limit; thrower keeps one foot on or over it until release; may not leave before the ball crosses the plane `[Q1]` (7-6.8.b–d) | spot templates | thrower's feet within ± 0.46 m of the spot centre (x for BLOB, y for SLOB) from t_dispose to t_release; lateral displacement > 0.9 m ⇒ made-basket inbound (R3) or tracking error |
| **R3 Running the end line** | After a made basket the thrower may move along the end line and pass to a teammate also out of bounds; also if a timeout or certain defensive fouls happen before the throw-in ends `[Q1]` (7-4.6.a–b) | full-court end-of-game ATOs after an opponent make (A6.23, A6.25) | FULLCOURT inbound where the thrower's x changes > 1.0 m before release, or two attackers out of bounds behind the far end line (y > 27.05) with a ball transfer before the first in-bounds touch |
| **R4 Clocks start on the first legal touch; ≥ 0.3 s run-off in the last 59.9 s** | Game and shot clocks start at the in-bounds touch; in the last 59.9 s (and shot clock < 5 s with tenths), a touch followed by an immediate stop must run ≥ 0.3 s `[Q1]` (5-10.2.a/d, 5-10.3.a/d) | clock audits | flag any in-bounds touch + whistle in the last 60 s where clock_before − clock_after < 0.3 s. **MSU case:** MSU 78–77 FGCU, 20 Nov 2016 — the Big Ten said an official "improperly set the clock in motion" on FGCU's final 1.6-s possession; earlier ≈ 0.8 s was wrongly docked after a Miles Bridges deflection `[Q3]` |
| **R5 0.3-second rule (tap only)** | With ≤ 0.3 s on a tenths display at a throw-in or FT restart, a player may not gain control and shoot; only a tap scores `[Q1]` (5-1.19). Coaching card: under 0.4 s the receiver taps (lob to the box); above that "catch-and-shoot in the air" `[Q4]` | last-second templates (A6.27) | INBOUND_EVENT with game clock ≤ 0.3 s ⇒ expected LOB_CATCH redirect with ball contact ≤ 0.1 s; a held catch then a made basket in this window = rules error |
| **R6 Shot clock off when the game clock is shorter** | Shot clock off on a reset when less than a full shot-clock period remains; reactivated (to 20) on an OREB-type situation `[Q1]` (2-11.8) | last-shot segmentation | possession start with game clock < 30 s after a change of possession ⇒ `shot_clock_off`; segment last-shot possessions by game clock; re-activate `late_clock` after an OREB-to-20 reset if game clock > 20 |
| **R7 10-second backcourt count; 2026-27 "19"** | Count starts on a legal backcourt touch; resets on all stoppages except defence-caused out of bounds, offence-retained held ball or an offensive technical; **always resets if the offence is charged a timeout** `[Q1]` (9-10; 2-7.9). 2026-27: violation called when the shot clock shows 19 instead of 20 `[Q2]` | because NCAA men cannot advance after a timeout, a late backcourt timeout gives a fresh 10 s to cross | t_cross (ball and both dribbler's feet at y < 12.73) − t_touch ≤ 10 s; `10s_violation` if the shot clock reaches 20.0 (≤ 2025-26) / 19.0 (2026-27) with the ball in the backcourt |
| **R8 Timeout allotment and media timeouts** | Media format: three 30-s and one 60-s timeout per team per game; up to two 30-s carry over; media timeouts at the first dead ball at/after 16/12/8/4-minute marks (or 15/10/5 by agreement); the first team timeout of the second half becomes a media timeout; a team timeout within 30 s before a media mark becomes it; +1 30-s timeout per OT `[Q1]` (5-14.10.a–g); timeouts during throw-ins and with the clock running only in the last two minutes of the second half/OT `[Q1]` (5-14.1.a). 2026-27: back-to-back media timeouts need the clock to run between them `[Q2]` | separate team ATOs from media restarts (Creighton's ATO list includes post-media plays; see the notes after A6.28) | stoppage ≥ 30 s starting within 30 s after a 16:00/12:00/8:00/4:00 mark ⇒ `ATO_media`; otherwise a 30–75 s stoppage with a team timeout in play-by-play ⇒ `ATO_team` |
| **R9 Shot-clock reset catalogue (beyond F13)** | Reset to 30: change of team control, opponent score, re-established backcourt control after a loss of control, single defensive foul with the offence in its backcourt (2-11.6.b). Reset to **20 or the time remaining, whichever is greater**: defensive personal/technical foul or kick/fist with a frontcourt inbound before a try hits the ring (2-11.6.c). Reset to 20 on a violation/offensive foul giving the **defence** a frontcourt throw-in (2-11.6.d.6). No reset when the defence knocks the ball out of bounds `[Q1]` | keeps `late_clock` labels correct | after each whistle set shot_clock_expected per the table and compare with the broadcast clock (OCR) |
| **R10 Throw-in spot after a defensive knock-out** | Frontcourt throw-ins go to the nearest 8.53 m mark or end-line spot **except** when the defence caused the ball out of bounds — then from where it went out `[Q1]` (7-3.2.a) | SLOBs are not always at the 8.53 m mark; sets needing the mark (e.g. MSU Misdirection SLOB, A6.16) need an offence-side stoppage | SLOB with \|y − 6.93\| > 1.5 m ⇒ `spot_point_of_out`, else `spot_8p53m` |
| **R11 2026-27: halves kept** | Four quarters discussed, not approved; men's games stay two halves in 2026-27 `[Q2]` | F13.4 end-of-half and 2-for-1 templates stay valid; there is no end-of-quarter in NCAA men's play | — ("EOQ" in the MSU "EOQ Horns Set" title, F18.1, is a FastModel label; its NCAA-men meaning is **unverified**) |

#### A6.2 "Sparty" BLOB (MSU) — NEW
- **Name and aliases:** Sparty; Box Sparty.
- **Family / sub-family:** F13.2 BLOB, Box → corner pop + cross screen + stagger + ball screen.
- **Start alignment (box; ball on the right end line; spots [HEURISTIC]):** inbounder 1 (3.33, −34.7); 3 ball-side low block (2.18, 15.9); 4 weak-side low block (2.18, 164.1); 5 ball-side elbow (4.57, 66.4); 2 weak-side elbow (4.57, 113.6).
- **Roles:** 1 inbounder then stagger screener; 3 corner receiver then stagger user; 5 cross-screener → ball screener → down-screener; 2 primary handler; 4 stagger screener.
- **Ordered actions (FastModel text) [windows HEURISTIC]:** (1) 3 pops to the ball-side corner and receives (t_touch = 0); (2) 5 cross-screens for 2, who comes to the ball-side wing and catches from 3 (0.5–2.5 s); (3) 3 runs off a baseline stagger by 1 and 4 (2.0–4.0 s); (4) 2 uses a ball screen from 5 at the top (3.0–5.5 s); (5) 5 down-screens for 1 (4.5–6.5 s); (6) 2 drives or hits 3 or 1.
- **Usual counters:** switch the cross screen (defense_full F14: "switch screens coming from the baseline up"); top-lock the stagger user; ice/drop the side ball screen (derived, not play-specific).
- **Detection signature [HEURISTIC]:** box snapshot at t_dispose (one attacker within 0.8 m of each block and one within 1.0 m of each elbow); first catch in the ball-side corner (r ≥ 6.0, θ ≤ 12°) ≤ 1.5 s after t_release; cross SCREEN by the ball-side elbow player on the weak-side elbow player moving toward the ball (Δx ≥ 3 m) within 2.5 s; baseline stagger (two stationary screeners at y ≤ 0.5, \|x\| 1.5–4.5, 1.5–3.0 m apart) used by the corner player moving to the weak side within 4 s; ball screen at r 7–8.5, θ 70–110° by the original ball-side elbow player within 5.5 s, then his down screen.
- **Teams documented:** MSU; season not stated (FastModel post 6 Mar 2018 ⇒ likely 2017-18, **unverified**) `[Q5]`. Tags: BLOB, AFTER TIMEOUT, LATE GAME SITUATIONS, CROSS SCREEN, DOWN SCREEN, NEED A 2, NEED A 3.
- **Sources:** `[Q5]`.
- **Confidence:** medium.

#### A6.3 "MSU BLOB" — elbow scorer, inbounder step-in screen, DHO, stagger (vs Maryland) — NEW
- **Name and aliases:** MSU BLOB (FastDraw 60206); "elbow scorer stagger".
- **Family / sub-family:** F13.2 BLOB, corners-and-elbow → DHO → stagger.
- **Start alignment (spots [HEURISTIC]):** 4 inbounder (3.33, −34.7); 1 ball-side corner (6.60, 0); 2 weak-side corner (6.60, 180); 3 (scorer) ball-side elbow (4.57, 66.4); 5 not stated (weak-side elbow or middle of the lane, **unverified**).
- **Roles:** 3 scorer; 5 screener and DHO big; 4 inbounder who steps in to screen; 1 DHO receiver and passer.
- **Ordered actions `[Q6]` [windows HEURISTIC]:** (1) 5 screens for 3, who cuts to the weak-side block (−1.0 to 0 s before t_release); (2) 5 separates for the entry from 4 (t_touch = 0); (3) 4 steps in and screens for 3 (0.5–2.0 s); (4) 5 DHOs to 1 (1.5–3.5 s); (5) 5 sets the second screen of a stagger for 3 (3.0–5.0 s); (6) 1 passes to 3 for the shot.
- **Usual counters:** switch the 4/5 screens; lock-and-trail 3 through both screens; jam the DHO.
- **Detection signature [HEURISTIC]:** attackers in both corners (θ ≤ 12° and ≥ 168°, r ≥ 6.0) and one at the ball-side elbow at t_dispose; first touch by the big at r 3–6 on the ball side ≤ 1.5 s after release; the inbounder enters and becomes a stationary screener within 2.5 s; DHO by the big to a corner player within 4 s; the same big becomes the second screener of a stagger used by the original elbow player, who ends at r 5–7.5.
- **Teams documented:** MSU, "inbounds vs. Maryland" (FastModel post 22 Jan 2015; 2014-15; game date **unverified**) `[Q6]`.
- **Sources:** `[Q6]`.
- **Confidence:** medium.

#### A6.4 BLOB Passer Pin (MSU) — NEW (distinct from "Screen the Inbounder" `[S12]`)
- **Name and aliases:** Passer Pin; "screen the passer" BLOB.
- **Family / sub-family:** F13.2 BLOB, "inbounder becomes shooter" (reversal + pin for the inbounder).
- **Start alignment [HEURISTIC]:** 1 inbounder (3.33, −34.7); 3 ball-side block (2.18, 15.9); 4 weak-side block (2.18, 164.1); 5 top/slot (7.34, 70.1); 2 weak-side wing (7.00, 135.6).
- **Roles:** 1 inbounder/shooter; 3 cross-screener; 4 receiver then pin screener for 1; 5 reversal receiver/passer.
- **Ordered actions `[Q7]` [windows HEURISTIC]:** (1) 3 screens across for 4, who cuts to the corner (−1.0 to 0 s); (2) 1→4 (t_touch = 0); (3) 4→5 (0.8–2.0 s); (4) 4 pins for 1 (1.5–3.0 s); (5) 5→1 for a shot or drive (2.5–4.0 s).
- **Usual counters:** the inbounder's defender switches the pin or jumps to the ball; stay home on the inbounder.
- **Detection signature [HEURISTIC]:** low cross SCREEN (both y < 1.5) before t_touch; corner catch; reversal pass to r ≥ 6.75, θ 60–120°; a stationary screener at y 0–2 near the lane line used by the **former inbounder** (identity = the player out of bounds at t_dispose) within 3 s; catch by him at r ≥ 6.0.
- **Teams documented:** MSU (FastModel post 10 Feb 2016, author Wes Kosel; likely 2015-16, **unverified**) `[Q7]`.
- **Sources:** `[Q7]`.
- **Confidence:** medium.

#### A6.5 Fake Pin Step-Out (MSU) — NEW
- **Name and aliases:** Fake Pin Step Out; corner loop DHO BLOB.
- **Family / sub-family:** F13.2 BLOB, corner DHO.
- **Start alignment [HEURISTIC; diagram not readable]:** 3 near the ball-side block (2.18, 15.9); 1 above 3 on the lane line (3.19, 48.8); 5 weak-side low (2.18, 164.1).
- **Roles:** 3 step-out receiver, DHO giver and fake pin screener for 5; 1 looping guard; 5 decoy.
- **Ordered actions `[Q8]` [windows HEURISTIC]:** (1) 3 steps out to the ball-side corner and catches (t_touch = 0); (2) 1 loops around 3 for a quick DHO in the corner (0.8–2.0 s); (3) 1 drives middle or shoots (2.0–3.5 s); (4) 3 acts as if screening for 5 (fake pin).
- **Usual counters:** switch the corner DHO; ice/force baseline on the DHO receiver.
- **Detection signature [HEURISTIC]:** catch at r ≥ 6.0, θ ≤ 15° within 1.2 s of release; DHO in the corner (both at θ ≤ 20°, r ≥ 5.5) within 2.0 s; the receiver's first move toward θ 30–90° at ≥ 3 m/s; the corner player approaches a teammate to < 1.5 m without stopping (fake screen).
- **Teams documented:** MSU (article 16 Dec 2016, Wes Kosel; season not stated) `[Q8]`.
- **Sources:** `[Q8]`.
- **Confidence:** low-medium.

#### A6.6 MSU BLOB vs Valparaiso (box combination: corner screen, seal, curl, STS, slip) — NEW
- **Name and aliases:** "BLOB – Mich ST vs Valpo".
- **Family / sub-family:** F13.2 BLOB, box combination.
- **Start alignment [HEURISTIC; tags say BOX ACTIONS]:** inbounder (3.33, −34.7); 4 and 5 low/high on the ball side; 1 and 2 on the weak side; 3 weak-side low.
- **Roles:** 4 corner cutter → screener → slipper; 5 seal man (vs switch) and clearing screener; 2 down-screener; 3 curler; 1 wing.
- **Ordered actions `[Q9]` [windows HEURISTIC]:** (1) 4 cuts off a screen to the ball-side corner; if switched, 5 seals (−1.0 to 0.5 s); (2) 5 screens for 1 mainly to clear the block; 1 cuts to the wing while 2 moves to down-screen for 3 (0–2.0 s); (3) 2 screens for 3, who curls; then 4 screens for 2 (STS) (1.5–4.0 s); (4) 4 is also open on the slip (3.0–4.5 s).
- **Usual counters:** switch everything with a big on the ball (A6.33); keep the post defender behind 5 to beat the seal.
- **Detection signature [HEURISTIC]:** box snapshot; first corner cut off a low screen; if the two defenders swap assignments, the screener holds at r ≤ 1.5 with a defender on his high side within 0.8 m for ≥ 0.6 s (seal); then down screen → curl (path curvature ≥ 90° within 2 m of the screener) → STS within 1.5 s; then the last screener leaves before contact toward r < 2 at ≥ 2.5 m/s (slip).
- **Teams documented:** MSU vs Valparaiso, NCAA second round, 21 Mar 2013 (2012-13), early first half `[Q9]`; result 65–54 (headline and URL date only) `[Q10]`.
- **Sources:** `[Q9][Q10]`.
- **Confidence:** medium.

#### A6.7 4-Low / 1-4 Low BLOB alignment — RICHER (BLOB use of the existing §3.1 "1-4 Low" alignment; listed next to Box / Stack / Line / Diamond in F13.2)
- **Name and aliases:** 4-Low BLOB; 1-4 Low BLOB; four-flat BLOB ("baseline line" European alias **unverified**).
- **Family / sub-family:** F13.2 BLOB alignment level.
- **Start alignment [HEURISTIC]:** (2.18, 15.9), (2.18, 164.1), (6.60, 0) or (4.31, 4.0), (6.60, 180); inbounder (3.33, −34.7). Hoop Vision describes "4-Low" as starting with a pass to the elbow that leads to many options (12 actions cited) `[Q16]`.
- **Roles:** post diver; corner shooter; screener/slipper; safety (lifter to the top).
- **Ordered actions (Illinois 1-4 Low BLOB text) `[Q14]` [windows HEURISTIC]:** 4 fakes the lift to the elbow; 2 cuts to the corner off 5's screen (0–1.5 s); options: post dive, corner three, slip, safety lift to r ≥ 7.5, θ 80–100°.
- **Usual counters:** 2-3 zone with a forward on the corner (F14 BLOB); switch the corner screen.
- **Detection signature [HEURISTIC]:** ALIGN = 4-Low if all four in-bounds attackers have y ≤ 1.5 m at t_dispose and their x spread is ≥ 9 m; first pass to the elbow area (r 4–5.5, θ 55–125°) within 1.5 s, or to a corner after a baseline screen.
- **Teams documented (MSU first):** MSU "Quick Duck-In BLOB" (A1.15) `[Q13]`; Illinois (FastModel post 19 Mar 2022; likely 2021-22) `[Q14]`; Creighton 2023-24 under-8 ATO inbound "with four players low" `[Q15]`; Hoop Vision (generic) `[Q16]`.
- **Sources:** `[Q13][Q14][Q15][Q16]`.
- **Confidence:** medium.

**Richer detail for MSU BLOBs already in A1.15 (no new block):** MSU "BLOB" (24 Mar 2024) = "brush loop" BLOB — detection adds: two attackers starting within 1.5 m of each other cross paths within 1.0 s of each other with no stationary phase (brush, §8.1) before t_release; a third player's SCREEN on one of them within 1.5 s; first catch by the other looper `[Q11]`. "Clear BLOB" (19 Mar 2022): BLOB with shot clock ≤ 10 s at t_dispose; after the catch the three non-ball in-bounds teammates all at r ≥ 6.5 and ≥ 4 m from the ball within 2.5 s; isolation (no screen within 2 m for ≥ 2 s) then DRIVE `[Q12]`. "Quick Duck-In BLOB": 4-Low snapshot (A6.7 rule: all four in-bounds attackers at y ≤ 1.5 m with x spread ≥ 9 m at t_dispose); 5 steps into the lane (\|x\| < 1.83, y < 1.5) and seals (stationary ≥ 0.4 s with a defender behind) before t_release; post catch at r ≤ 2.0 `[Q13]`. Purdue "Stack Curl BLOB" and "Duck-In BLOB" are in A2.32/A2.33; the special-situations note adds: diagonal stack = four players with consecutive-neighbour distances ≤ 1.5 m on a fitted line 25–65° to the baseline, deepest at r ≤ 3 (canonical rule A11.21; heuristic example spots on a 45° line with ≈ 1.06 m spacing: (2.42, 38.3), (3.48, 40.3), (4.53, 41.4), (5.59, 42.1) ball side right, mirrored (2.42, 141.7), (3.48, 139.7), (4.53, 138.6), (5.59, 137.9) on the left; angle **unverified**) `[Q17]`; Duck-In decoy: the tallest attacker moves away from the ball (Δr ≥ +2 m or crosses to the weak side) in the 1.0 s before t_release while two defenders are within 1.5 m of him; second big catches at r ≤ 2 in the vacated area; else wing safety; else high-post catch (r 4–5, θ 60–120°) by the decoy `[Q19]`. Illinois "Stack Curl BLOB" is title-only in the listing seen by that note `[Q18]` (the Big Ten note opened its detail page, A2.32).

#### A6.8 Corner Lob BLOB / "Circle Lob" vs lock-and-trail — NEW (STS-lob sub-family)
- **Name and aliases:** Corner Lob BLOB (Purdue); Circle Lob (Hoop Vision); "STS lob" family.
- **Family / sub-family:** F13.2 BLOB, lob off a screen-the-screener; the inbound itself is the lob.
- **Start alignment [HEURISTIC]:** 3 low ball side (2.18, 15.9); 2 high ball side (4.57, 66.4); 5 low weak side (2.18, 164.1); 4 high weak side (4.57, 113.6); 1 inbounder (3.33, −34.7).
- **Roles:** 3 decoy sprinter; 2 fake screener then back-screener; 5 short-corner clear; 4 lob finisher; 1 lob passer.
- **Ordered actions (Purdue) `[Q20]` [windows HEURISTIC; t_touch = lob catch]:** (1) 3 sprints under the basket, then cuts toward the top (−0.5 to 1.0 s); (2) 2 fakes a screen for 5; 5 cuts to the weak-side short corner (0–1.5 s); (3) 2, without breaking stride, back-screens for 4 (1.0–2.0 s); (4) 1 lobs to 4 at the rim (1.5–2.5 s). Hoop Vision: lob plays are often combined with screen-the-screener action; the circle lob counters lock-and-trail coverage `[Q16]`.
- **Usual counters:** switch the back screen; keep a low man at the rim (lob protection, defense_full F6.5 / F14).
- **Detection signature [HEURISTIC]:** no in-bounds catch before LOB_CATCH; ball from the inbounder to r ≤ 1.5 with apex ≥ 3.6 m, released at t_dispose + 1.5–4.0 s; the receiver ran ≥ 4 m toward the rim in the 1.5 s before the catch after passing within 1.2 m of a teammate who had just faked a screen (approach to < 1.5 m without stopping) on someone else.
- **Teams documented:** Purdue (FastModel post 12 Jan 2023; likely 2022-23; tags BLOB, LOB, NEED A 2, LATE GAME, ATO) `[Q20]`; Hoop Vision decade review `[Q16]`.
- **Sources:** `[Q20][Q16]`.
- **Confidence:** medium.

#### A6.9 4 High BLOB (Michigan) — NEW alignment row "4 High" (four in-bounds players at or above the FT-line extended)
- **Name and aliases:** 4 High BLOB; horns BLOB.
- **Family / sub-family:** F13.2 BLOB, alignment "4 High".
- **Start alignment (text partly garbled) [HEURISTIC]:** 1 inbounder; 4 weak-side elbow (4.57, 113.6); 5 ball-side elbow (4.57, 66.4); 2 between the elbows (4.19, 90); 3 ball-side wing (7.00, 44.4).
- **Roles:** 2 middle splitter (basket cut); 3 curl shooter; 5 side screener; 1 inbounder → weak-side corner.
- **Ordered actions `[Q21]` [windows HEURISTIC]:** (1) 1 throws in; a player sprints to the top (who is **unverified**); (2) 2 splits the middle straight to the rim for a direct pass (0–1.5 s from t_dispose); (3) 3 curls off 5's side screen for three (1.0–3.0 s); (4) 1 sprints to the weak-side corner as an option for 3 (2.0–4.0 s).
- **Usual counters:** **unverified**.
- **Detection signature [HEURISTIC]:** ALIGN = 4 High if all four in-bounds attackers have y ≥ 3.5 m at t_dispose; a basket cut from (≈ 4.2, 80–100°) to r ≤ 1.5 within 1.5 s; a curl by the wing around a stationary elbow big; the inbounder enters and reaches the weak-side corner (θ ≥ 168°) within 4 s.
- **Teams documented:** Michigan (FastModel post 12 Mar 2023; likely 2022-23, **unverified**) `[Q21]`.
- **Sources:** `[Q21]`.
- **Confidence:** medium-low.

#### A6.10 High-Low BLOB (Michigan) — NEW
- **Name and aliases:** High Low BLOB.
- **Family / sub-family:** F13.2 BLOB, post entry (high-low).
- **Start alignment:** not stated; [HEURISTIC] 3 low ball side (2.18, 15.9); 4 and 5 low/in the lane; 1 inbounder (3.33, −34.7).
- **Roles:** 3 pop-out receiver; 5 down-screener then sealing post; 4 high-post receiver and feeder.
- **Ordered actions `[Q22]` [windows HEURISTIC]:** 3 pops out (−0.5 to 0.5 s); 5 down-screens for 4; 1→3 (t_touch); 3→4 high (0.8–2.0 s); 4 feeds 5, who seals (1.5–3.0 s).
- **Usual counters:** front the sealing post; switch the down screen.
- **Detection signature [HEURISTIC]:** first catch at r ≥ 5.5; down SCREEN by a big with the screened big ending at r 4–5.5 and catching within 2 s; the screener seals at r ≤ 2 (stationary, defender on the high side) and catches from the high post (pass 2.5–4.5 m, descending).
- **Teams documented:** Michigan (FastModel post 25 Mar 2022; likely 2021-22) `[Q22]`.
- **Sources:** `[Q22]`.
- **Confidence:** medium.

#### A6.11 Wisconsin STS BLOB — NEW (with Illinois Stagger Twist, A2.34)
- **Name and aliases:** STS BLOB (Wisconsin).
- **Family / sub-family:** F13.2 BLOB, screen-the-screener for the inbounder.
- **Start alignment [HEURISTIC]:** inbounder 1 (3.33, −34.7); 3 ball-side corner/short corner; 2 weak-side wing; 5 low in the lane.
- **Roles:** 1 inbounder → back-screener → STS user; 3 receiver → down-screener; 5 back-screen user.
- **Ordered actions `[Q24]` [windows HEURISTIC]:** 1→3 (t_touch); 3→2 while 1 back-screens for 5; 3 down-screens for 1 (STS) (0–3 s).
- **Usual counters:** switch both screens.
- **Detection signature [HEURISTIC]:** the inbounder enters and back-screens a big (screen at y 1–4 m), then the first receiver down-screens for the former inbounder within 2 s.
- **Teams documented:** Wisconsin (FastModel post 15 Nov 2020; likely 2020-21) `[Q24]`. Wisconsin was #7 in Hoop Vision's decade BLOB-efficiency list (2010s) `[Q16]`. Illinois Stagger Twist: A2.34 `[Q23]`.
- **Sources:** `[Q24][Q16][Q23]`.
- **Confidence:** medium.

#### A6.12 Triangle alignment (BLOB and SLOB) — NEW alignment row (geometry unverified)
- **Name and aliases:** Triangle BLOB / Triangle SLOB.
- **Family / sub-family:** F13.2/F13.3 alignment level.
- **Start alignment:** HoopTactics organises BLOB plays into Box, Stack, Line and **Triangle** (Triangle BLOB plays: Pick the Picker, Base Pinch, Back Screen, Base Cross Screen) and SLOB plays into Box, Stack, Line and Triangle (Misdirection Double, Single Double, Triangle Flex) `[Q25]`; names only (premium content), so the spot geometry is **unverified**.
- **Roles / ordered actions / counters:** **unverified**.
- **Detection signature [HEURISTIC, pending film]:** three in-bounds attackers forming a triangle with sides 2.5–5 m inside r ≤ 6, plus one safety at r ≥ 7; vs Box: 3 players in the cluster instead of 4.
- **Teams documented:** none at D-I.
- **Sources:** `[Q25]`.
- **Confidence:** low.

#### A6.13 Hawk BLOB (box; inbounder becomes shooter) — NEW (youth/HS text)
- **Name and aliases:** Hawk (BLOB; unrelated to the half-court Hawk cut, A5.21 — see Vocabulary proposals).
- **Family / sub-family:** F13.2 BLOB box, inbounder becomes shooter off a screen.
- **Start alignment `[Q26]`:** 5 strong-side block (2.18, 15.9); 1 strong-side elbow (4.57, 66.4); 3 weak-side elbow (4.57, 113.6); 4 weak-side block (2.18, 164.1); 2 inbounder, the best shooter (3.33, −34.7).
- **Roles:** 2 inbounder/shooter; 5 corner receiver then screener; 1 wing; 3 safety; 4 rebounder.
- **Ordered actions `[Q26]`:** 5 fakes to the basket, then out to the corner and catches (t_touch); 1 fakes in, then out to the wing; 5→1; 2 cuts to the basket, then to the same-side corner 3.7–4.6 m from the basket; 5 turns and screens for 2; 1→2 shot; 3 floats to the key; 4 rebounds. Timing [HEURISTIC]: shot within 4 s of t_touch.
- **Usual counters:** stay with the inbounder.
- **Detection signature [HEURISTIC]:** box snapshot; corner catch by the low ball-side player; wing catch; the former inbounder ends at r 3.7–4.6, θ ≤ 25° off a stationary screen by the corner player; shot within 4 s of t_touch.
- **Teams documented:** youth/HS text (Miniscalco & Kot); no D-I team `[Q26]`.
- **Sources:** `[Q26]`.
- **Confidence:** medium (description); low (D-I relevance).

#### A6.14 Tom Izzo SLOB "2" (elevator) — NEW (MSU)
- **Name and aliases:** SLOB "2"; Izzo elevator SLOB.
- **Family / sub-family:** F13.3 SLOB, elevator / double-down.
- **Start alignment [HEURISTIC]:** 2 inbounder at the 8.53 m spot (10.55, 41.1); 1 receiver near the ball-side slot/top (7.34, 70.1); 3 near the ball-side block (2.18, 15.9); 4 and 5 side by side at the FT line (4.19–4.83, 70–110).
- **Roles:** 2 inbounder → lay-up cutter; 1 handler; 3 screener → elevator user; 4 and 5 elevator doors.
- **Ordered actions `[Q27]` [windows HEURISTIC]:** (1) 2→1 (t_touch); (2) 1 dribbles to the opposite wing (0.5–2.5 s); (3) 2 comes off 3's screen near the block — option 1, lay-up (1.5–3.0 s); (4) 3 comes through an elevator (or double-down) by 4 and 5 for a shot near the top — option 2 (2.5–4.5 s).
- **Usual counters:** switch the block screen; top-lock and trail through the elevator (defense_full F5.5).
- **Detection signature [HEURISTIC]:** SLOB at the 8.53 m spot; the handler dribbles ≥ 6 m across (sign(x) changes); the former inbounder cuts to r ≤ 1.5 off a stationary screener at the block; then an elevator: two stationary teammates 0.9–1.6 m apart that close to < 0.6 m within 0.4 s after the cutter passes between them; catch at r 6.5–8, θ 70–110°.
- **Teams documented:** MSU (FastModel post 16 May 2015, Brandon Mullis; tags SLOB, ATO, LATE GAME, NEED A 2/3, ELEVATOR) `[Q27]` [pre-window].
- **Sources:** `[Q27]`.
- **Confidence:** medium.

#### A6.15 Line Post Stagger SLOB (MSU, 2021) — NEW
- **Name and aliases:** Line Post Stagger SLOB.
- **Family / sub-family:** F13.3 SLOB, Line alignment → triple screen → back screen → stagger.
- **Start alignment [HEURISTIC]:** 2, 4, 5 and the PG in a line on the ball side; 3 inbounder (10.55, 41.1).
- **Roles:** PG cutter → back-screener → stagger user (shooter); 2 stagger user → handler at the top; 3 inbounder → back-screen user → post; 4/5 stagger screeners.
- **Ordered actions `[Q28]` [windows HEURISTIC]:** (1) PG cuts off screens by 5, 4 and 2 to the strong-side short corner (0–2.0 s around release); (2) 2 comes off 4 and 5 to the top; 3 enters to 2's spot (t_touch by 2 at the top, 1.5–3.0 s); (3) 3 steps in and comes off a back screen by the PG to the opposite block; 2 dribbles in and looks to the post (3.0–5.0 s); (4) after the back screen, the PG comes off 4 and 5 to the top; 2 hits the PG for the shot (4.5–7.0 s).
- **Usual counters:** switch the stagger; front the post.
- **Detection signature [HEURISTIC]:** line snapshot (≥ 3 attackers within 1.2 m of a common straight line, spacing ≤ 1.5 m) at t_dispose; a cutter through three consecutive screeners; the same two-man stagger used by two different players within 7 s; a guard back-screens the former inbounder.
- **Teams documented:** MSU (FastModel post 19 Mar 2021; likely 2020-21) `[Q28]` [pre-window].
- **Sources:** `[Q28]`.
- **Confidence:** medium.

#### A6.16 Misdirection SLOB (MSU, end of clock) — NEW
- **Name and aliases:** Misdirection SLOB.
- **Family / sub-family:** F13.3 SLOB × F13.5 late clock; seal after a stack/stagger misdirection.
- **Start alignment [HEURISTIC]:** 4 inbounder at the 8.53 m spot (10.55, 41.1); 1 near the ball-side wing; 5 and 2 in a stack near the lane line; 3 weak side.
- **Roles:** 4 inbounder → back-screen user; 1 handler; 5 back-screener → stack screener → slipper/sealer; 2 stack screener; 3 stack user.
- **Ordered actions `[Q29]` [windows HEURISTIC]:** "End of clock SLOB that MSU ran to get a seal after the misdirection of the stack or stagger screen": 1 pops out; 4→1 (t_touch); 5 back-screens; 4 cuts off it; 1 dribbles over (0–3 s); 1→4; 5 and 2 set a stack screen for 3; 5 slips (3–6 s).
- **Usual counters:** switch the stack; front the slipper.
- **Detection signature [HEURISTIC]:** SLOB with shot clock ≤ 10 s or game clock ≤ shot clock; the former inbounder cuts off a back screen into the paint; later a stacked double screen (two stationary screeners ≤ 1.0 m apart along the cutter's path) where the lower screener leaves early toward r ≤ 1.5 (slip) and seals. Needs the 8.53 m spot (R10).
- **Teams documented:** MSU (FastModel post 19 Mar 2021; tags LATE GAME, NEED A 2/3, ATO) `[Q29]` [pre-window].
- **Sources:** `[Q29]`.
- **Confidence:** medium.

#### A6.17 Sideline Elevator (MSU) — NEW
- **Name and aliases:** Sideline Elevator.
- **Family / sub-family:** F13.3 SLOB, elevator for a game-winning three.
- **Start alignment [HEURISTIC]:** 3 inbounder (10.55, 41.1); 1 receiver at the slot; 4 and 5 shoulder to shoulder near the FT line; 2 shooter below them.
- **Roles:** 1 handler; 3 inbounder → return receiver → weak-side clear; 4, 5 elevator; 2 shooter.
- **Ordered actions `[Q30]` [windows HEURISTIC]:** 1→3 (t_touch); 3→1 and 3 clears weak side (0.5–2.0 s); 1 dribbles away from the elevator by 4 and 5, looking for 2 (2.0–4.0 s); 1→2. "A little misdirection and an elevator screen can get you an open look from deep for a game winner."
- **Usual counters:** switch before the doors close.
- **Detection signature [HEURISTIC]:** return pass to the inbounder within 2 s; handler dribbles away from the elevator; elevator (A6.14 signature) used by 2, catch at r ≥ 6.75.
- **Teams documented:** MSU (FastModel post 6 Jul 2018; tags ELEVATOR, ATO, LATE GAME, NEED A 3) `[Q30]` [pre-window].
- **Sources:** `[Q30]`.
- **Confidence:** medium.

#### A6.18 Back Screen Post-Up / Stagger Option SLOB (MSU, Bridges) — NEW
- **Name and aliases:** Back Screen Post Up / Stagger Option SLOB.
- **Family / sub-family:** F13.3 SLOB, guard-to-big back-screen post-up + STS stagger.
- **Start alignment [HEURISTIC]:** 4 inbounder (Bridges) at (10.55, 41.1); 1 receiver at the slot; 2 guard near the elbow; 5 and 3 stagger spots on the weak-side lane line.
- **Roles:** 4 inbounder → post receiver (Bridges); 2 back-screener → stagger user; 5, 3 stagger screeners; 1 handler.
- **Ordered actions `[Q31]` [windows HEURISTIC]:** 4→1 (t_touch); 1 dribbles to the opposite side (0.5–2.5 s); 2 back-screens for 4 (1.5–3.0 s); 5 and 3 stagger for 2 (2.5–4.5 s); 1 hits 2 or 4.
- **Usual counters:** switch the guard-to-big back screen (creates a post mismatch the set wants); top-lock the stagger.
- **Detection signature [HEURISTIC]:** the former inbounder becomes a post receiver at r ≤ 2.5 after a back screen by a guard (shorter screener than screened player; position-based if heights unknown); the guard screener immediately uses a two-man stagger (STS) to r ≥ 6.75.
- **Teams documented:** MSU (FastModel post 19 Jun 2018; 2017-18) `[Q31]` [pre-window].
- **Sources:** `[Q31]`.
- **Confidence:** medium.

#### A6.19 Izzo inside-out SLOB (Coaching Toolbox version) — NEW
- **Name and aliases:** Sideline Inbounds Play (Izzo). Izzo SLOBs "usually aim to score inside-out" `[Q33]`.
- **Family / sub-family:** F13.3 SLOB, back screen on the inbounder → double screen → four-option read. May be the same family as Line-1 / SLOB "1" (F13.3 `[S12][S29e]`), kept separate because it starts with a back screen on the inbounder.
- **Start alignment [HEURISTIC]:** 3 inbounder (10.55, 41.1); 2 popping to the middle; 1 near the ball-side lane; 4 and 5 side by side near the FT line.
- **Roles:** 3 inbounder → post-up; 1 back-screener → double-screen user (three); 5 slipper; 4 popper; 2 handler.
- **Ordered actions `[Q33]` [windows HEURISTIC]:** 2 pops to the middle; 3→2 (t_touch); 1 back-screens for 3 (0.5–2.0 s); 4 and 5 double-screen for 1; 2 dribbles to the wing; 1 uses the double to the top; 3 continues to the block; 5 slips; 4 pops (2–5 s). Options: 3 post-up, 1 three, 5 slip, 4 pop.
- **Usual counters:** switch the back screen on the inbounder; top-lock the double-screen user.
- **Detection signature [HEURISTIC]:** the inbounder is back-screened and ends on the block (r ≤ 2.2) ≤ 3 s after release; a side-by-side double screen (two stationary screeners ≤ 1.2 m apart) used by the back-screener to r ≥ 6.75, θ 70–110°; then one double screener moves rim-ward (slip) and the other outward (pop) within 1.0 s.
- **Teams documented:** MSU (Coaching Toolbox diagram; no season) `[Q33]`.
- **Sources:** `[Q33]`.
- **Confidence:** medium-low.

#### A6.20 Wisconsin Diamond / Ghost / Box Pop SLOB family — NEW (down screen + flare + back screen on the inbounder + ghost/pop)
- **Name and aliases:** Diamond SLOB; Ghost SLOB; Box Pop SLOB.
- **Family / sub-family:** F13.3 SLOB. Alignment: Diamond = diamond (title); Box Pop = box (title); Ghost not stated.
- **Start alignment [HEURISTIC]:** inbounder at (10.55, 41.1); down-screener 5 and receiver near the ball-side lane line/slot; weak-side flare pair 4 and 2 at the weak slot/wing.
- **Roles:** 5 down-screener → back-screener on the inbounder; receiver (3 or 1); 4 flare screener → ghost/pop (or step-up) screener; 2 flare user; inbounder → back-screen user.
- **Ordered actions:** Diamond `[Q36]`: 5 down-screens for 3; 1 (inbounder)→3 (t_touch); 4 flares for 2 (0.5–2.0 s); 4 ghost-screens for 3 while 5 back-screens for 1 (2.0–4.0 s); 3 hits 2, 4 or 1. Ghost `[Q37]`: 5 down-screens for 1; 3 (inbounder)→1; on the catch 4 flares for 2; after the throw-in 5 back-screens for 3; 4 fakes a ball screen and pops; 1 attacks or hits 4 — run several times vs Baylor, NCAA Round of 32 (March 2021). Box Pop `[Q38]`: 5 down-screens for 1; 2 (inbounder)→1; 4 flares for 3 while 5 back-screens for 2; 5 down-screens for 2; 4 step-up screens for 1 and pops; 1→4 — end-of-game set vs Maryland for a three (Jan 2019). Timing [HEURISTIC] as given.
- **Usual counters:** switch the down screen; "next" on the flare; top-lock the inbounder after the back screen.
- **Detection signature [HEURISTIC]:** down-SCREEN catch at r 6.5–8 on the ball side within 1.5 s of release; within 1.0 s of that catch a weak-side flare ending at r ≥ 6.75; the former inbounder is back-screened (screen at y 4–8 m) and cuts toward the rim; ghost/pop = a big approaches the handler to < 1.5 m without becoming stationary, then reaches r ≥ 6.75 and catches.
- **Teams documented:** Wisconsin 2018-19 (Box Pop) and 2020-21 (Diamond, Ghost) `[Q36][Q37][Q38]`.
- **Sources:** `[Q36][Q37][Q38]`.
- **Confidence:** medium.

#### A6.21 Sideline Stack (staggered screens toward the inbounder) — NEW alignment row (youth/HS text)
- **Name and aliases:** Sideline Stack.
- **Family / sub-family:** F13.3 SLOB, Stack (sideline version).
- **Start alignment `[Q26]` (converted):** three players 2.4–3.0 m off the sideline directly across from the inbounder, 1.2–1.5 m apart; 4 across near the opposite sideline; 5 inbounds. For a right-side SLOB at the 8.53 m mark: (x ≈ 4.8, y ≈ 6.9 ± 1.4) → r ≈ 7.3–9.6 m, θ ≈ 49–60° (centre (8.41, 55.2°)); 4 at (x ≈ −6.6, y ≈ 6.9) → (9.6, 133.7).
- **Roles:** 1, 2, 3 stack; 4 weak-side basket cutter; 5 inbounder.
- **Ordered actions `[Q26]`:** 2 screens for 1, then cuts to the basket; then 3 screens for 2; 1 comes off for the pass; 4 runs to the basket for a pass from 2; 5→2 quick basket. 2 must screen for 1 before 3 screens for 2; five-second limit (R1).
- **Usual counters:** switch within the stack.
- **Detection signature [HEURISTIC]:** three attackers within 1.6 m of each other on a line parallel to the sideline at \|x\| 4.5–5.5 m opposite the inbounder at t_dispose; sequential screens (second starts ≥ 0.5 s after the first ends).
- **Teams documented:** youth/HS text; no D-I team `[Q26]`.
- **Sources:** `[Q26]`.
- **Confidence:** medium (description); low (D-I relevance).

#### A6.22 Late-game protect-the-lead SLOB "split" read (MSU vs Duke, 2019) — NEW situational label
- **Name and aliases:** proposed label `SLOB_protect_split`.
- **Family / sub-family:** F13.3 SLOB × F13.4 end of game (ahead).
- **Start alignment:** two receivers close together in the backcourt/midcourt; inbounder on the sideline in front of the opponent's bench.
- **Roles:** inbounder (Xavier Tillman); two splitting receivers (Kenny Goins, Cassius Winston).
- **Ordered actions `[Q39]`:** MSU up 1 with 4.7 s left, Elite Eight vs Duke (31 Mar 2019); Duke still needed fouls to reach the bonus; Tillman nodded to Goins and Winston to split apart and threw to Winston running down-court, having read Tre Jones overplaying Winston. Timing [HEURISTIC]: split at t_dispose + ≤ 1 s.
- **Usual counters:** deny both receivers; foul on the catch.
- **Detection signature [HEURISTIC]:** game clock ≤ 10 s, offence leading by 1–3; two receivers within 2 m at t_dispose diverge (relative velocity ≥ 5 m/s) within 1.0 s; pass ≥ 10 m to the receiver whose defender is on his ball side (overplay).
- **Teams documented:** MSU 2018-19 `[Q39]` [pre-window].
- **Sources:** `[Q39]`.
- **Confidence:** medium (alignment and outcome not described in detail).

**MSU SLOB names without descriptions** (Coach's Clipboard "Michigan State Sets"; members-only) `[Q34]`: sideline Line-2, X-ISO, Double-Slip; BLOB "Double-Screen the Screener" and "Two Double-Screens". Label placeholders only; content **unverified**. Already-listed SLOBs re-confirmed: "Zipper Spain PNR SLOB" (A3.21) `[Q32]`; Illinois "Winner SLOB" (A2.35) `[Q35]`.

#### A6.23 "Nova" — full-court ATO with a pitch-back to the trailing inbounder (Villanova reference template) — NEW
- **Name and aliases:** Nova; part of Villanova's "Wildcat Minute" late-game drill.
- **Family / sub-family:** F13.4 end of game / F13.1 ATO, full court with a backcourt inbound (NCAA no-advance rule).
- **Start alignment [HEURISTIC]:** inbounder behind the far end line (27.2, 84–96); handler at the backcourt FT-line area (r ≈ 21–23, θ 80–100); screener near half-court (r ≈ 13–15, θ 60–120); two others deep in the frontcourt.
- **Roles:** inbounder → trailer/shooter (Kris Jenkins); handler (Arcidiacono); midcourt screener (Ochefu); two deep spacers.
- **Ordered actions `[Q40]` (t_touch = 0, 4.7 s on the clock):** (1) inbound to the handler in the backcourt; (2) speed dribble, midcourt ball screen (≈ 1.5–2.5 s); (3) handler attacks to the top of the key, drawing two defenders (≈ 3.0–3.8 s); (4) pitch back to the trailing inbounder for a catch-and-shoot three, 7.3 m, at the horn (≈ 3.8–4.4 s). Tied 74–74, 2016 national final vs North Carolina (4 Apr 2016); a variation was run by the 2009 team. Windows [HEURISTIC].
- **Usual counters:** switch the midcourt screen and keep a defender on the trailer.
- **Detection signature [HEURISTIC]:** FULLCOURT inbound with game clock ≤ 6 s; the thrower crosses half-court behind the ball (y_thrower > y_ball for ≥ 2 s); a ball screen at y 10–15 m; the handler dribbles ≥ 13 m in ≤ 3.5 s (mean ≥ 3.7 m/s); a backward pass (ball Δy ≥ +1 m) to the trailer at r 6.75–8.0 with ≤ 1.0 s catch-to-release.
- **Teams documented:** Villanova 2015-16 (non-Big Ten reference template) `[Q40]`.
- **Sources:** `[Q40]`.
- **Confidence:** high (event facts); medium (positions).

#### A6.24 "Indiana" — full-court option route to a half-court catch (Michigan, Beilein) — NEW
- **Name and aliases:** Indiana.
- **Family / sub-family:** F13.4 end of game / F13.1 ATO, full court with a backcourt end-line inbound.
- **Start alignment [HEURISTIC]:** inbounder behind the far end line (27.1, 84–96); option-route receiver near half-court (r 12–15, θ 70–110); shooter on the right at r 9–11; two others deep.
- **Roles:** inbounder (strong arm; Isaiah Livers, unguarded); option-route receiver and decision-maker (Abdur-Rahkman); shooter (Jordan Poole); two deep decoys.
- **Ordered actions `[Q41][Q42]`:** Michigan 64–63 Houston, NCAA second round, 17 Mar 2018: after Houston missed two FTs, Wagner rebounded and Michigan called timeout with 3.6 s (ESPN); SI says Michigan had no timeouts left earlier in the possession — **timeout status conflicts between sources**. (1) The receiver comes back toward the ball from midcourt as the pass is thrown (release ≈ t_dispose + 1–2 s; flight ≈ 0.8–1.2 s) [HEURISTIC]; (2) catch near half-court (t_touch = 0, 3.6 s); (3) two dribbles toward the middle/right (0–1.5 s); (4) pass to the shooter a step behind the arc, caught with 1.6 s left, three made. Run "hundreds of times this year in practice" (Simpson); the same play beat Maryland in January 2018 (catch, drive, foul, two FTs, 68–67).
- **Usual counters:** guard the inbounder (Houston did not); double the option receiver only if the shooter is covered.
- **Detection signature [HEURISTIC]:** FULLCOURT inbound, game clock ≤ 5 s; inbound pass ≥ 12 m caught at y 11–16 m by a player moving toward the inbounder (≥ 2 m/s at the catch); ≤ 3 dribbles; lateral pass to a teammate at r 6.75–8.5; release with ≤ 1.0 s left.
- **Teams documented:** Michigan 2017-18 (Big Ten) `[Q41][Q42]`.
- **Sources:** `[Q41][Q42]`.
- **Confidence:** high (event); medium (positions; timeout status conflicting).

#### A6.25 Full-court home-run pass: Northwestern vs Michigan 2017 (unverified) and Duke 1992 catch-turn-shoot — NEW
- **Name and aliases:** home-run pass; full-court lob/catch; "The Shot" set (Duke). The Hoopscoop definition of "home run" (basketball's "Hail Mary" for down 1–3 with ≤ 3 s) is from a search snippet — **unverified**.
- **Family / sub-family:** F13.4 end of game, length-of-floor pass.
- **Start alignment:** inbounder behind the far end line (r ≈ 27.1, θ ≈ 90); receiver near the backcourt side of the frontcourt FT line (Duke) or near the rim (Northwestern).
- **Roles:** inbounder (Grant Hill; Nathan Taphorn); receiver (Christian Laettner; Dererk Pardon).
- **Ordered actions:** Duke 1992 East Regional final vs Kentucky (down 103–102, 2.1 s, OT): after a timeout, a 24.1 m pass (the source gives the pass as 79 ft = 24.08 m, `[Q43]` re-opened 2026-10-18; from an inbounder at x ≈ 0 behind the far end line, y ≈ 27.05–27.4, to (0, 4.19) the distance is only ≈ 22.9–23.2 m, so 24.1 m implies a lateral offset of ≈ 7.6 m or an approximate source figure — inbounder and catch x-offsets **unverified**); Laettner caught at the opposite foul line (0, 4.19) → (4.19, 90), one dribble right, turnaround jumper at the horn; Kentucky did not guard Hill and put an extra defender on Laettner; Duke had run it once before that season vs Wake Forest, when Hill was guarded and the pass went astray `[Q43]`. Timing: the clock starts at the touch, so all 2.1 s remain at the catch; flight ≈ 1.0–1.4 s [HEURISTIC]. Northwestern 67–65 Michigan (1 Mar 2017, tied, 1.7 s): full-court pass from Taphorn to Pardon, who scored at the buzzer — details from search snippets only (InsideNU and SI returned 403) — **unverified**.
- **Usual counters:** guard the inbounder with a long player (defense_full F14) vs not guarding and doubling the target (A6.35).
- **Detection signature [HEURISTIC]:** FULLCOURT inbound, game clock ≤ 3 s; pass ≥ 22 m caught at r 3.5–6.5, θ 60–120° (Duke type; ≤ 1 dribble; FGA ≤ 2.0 s after the catch) or ≥ 24 m with flight 1.2–1.8 s caught at r ≤ 2.0 and shot within 0.5 s (lob type).
- **Teams documented:** Duke 1991-92 (reference template, not Big Ten) `[Q43]`; Northwestern 2016-17 — **unverified**.
- **Sources:** `[Q43]`.
- **Confidence:** high (Duke event per Wikipedia), medium (timing); low (Northwestern).

#### A6.26 "Maryland" (full-court three, decoy press-break look) and "Split" (return pass + speed dribble) — NEW full-court templates
- **Name and aliases:** "Maryland"; "Split" (Coach's Clipboard full-court buzzer-beaters) `[Q44]`.
- **Family / sub-family:** F13.4 end of game, full court (Maryland = need a 3; Split = need a 2 or a foul).
- **Start alignment:** Maryland: the team's usual "80" press-break alignment (F12.2) so the defence expects the pass to 1. Split: 1 (best handler) inbounds; 2 and 3 break opposite; 4 runs wide up a sideline; 5 goes deep.
- **Roles:** Maryland: 5 half-court catcher and passer; 2 and 4 back-cutters to the arc. Split: 1 inbounder → return receiver → speed dribbler and shooter; 2/3 first receivers; 5 deep option.
- **Ordered actions `[Q44]`:** Maryland: on "go", 5 cuts hard to the half-court line and catches the long pass; 2 and 4 step toward the ball then back-cut to the arc on opposite sides; 5 pivots and passes to the open one for three ("only a few seconds"). Split: 1→2 or 3; 1 sprints in for the return pass and speed-dribbles, usually taking the last shot; 5 deep if time; needs more than 5–6 s.
- **Usual counters:** deny the return pass (Split); stay deep on the back-cutters (Maryland).
- **Detection signature [HEURISTIC]:** Maryland: FULLCOURT inbound, game clock ≤ 5 s; catch by a big at y 11–14 m; two teammates reverse their y-velocity and finish at r 6.75–8.0 on opposite sides; pass from the half-court big within 1.0 s. Split: the thrower receives the ball back within 1.5 s of t_touch; dribble ≥ 18 m with mean speed ≥ 4.5 m/s (peak ≥ 5.5 m/s); FGA or drawn foul at r ≤ 3 with ≤ 1 s left.
- **Teams documented:** coaching text, no D-I team `[Q44]`. MSU example of the Split family: vs Kentucky (15 Nov 2022), end of the first OT, AJ Hoggard threw ahead "like a quarterback" to a streaking Tyson Walker, who passed to Malik Hall for a tying dunk (inbound location/time not stated) `[Q45]`. Brad Stevens full-court play — **unverified** (snippet).
- **Sources:** `[Q44][Q45]`.
- **Confidence:** medium (description); low (D-I usage).

#### A6.27 Time-remaining menu for last-second inbounds — NEW template layer (F13.4)
- **Name and aliases:** last-second play card.
- **Family / sub-family:** F13.4 template layer.
- **Start alignment / roles / ordered actions `[Q4]`:** 5 s baseline — best passer inbounds, no slap to start, 2 corner jumper or step-in reverse; 4 s full court — 1 breaks to the ball off 2+3 screens, 2 sprints for a jumper; 3 s sideline — 4 screens for 3, 5 down-screens for 2; 3 s full court — 1 and 2 break opposite, 5 screens for 4, who throws to 5 cutting for a lay-up; few seconds need-3 full court — 5 breaks ball side, 3 and 1 screen for 2; 1 s sideline — 3 screens for 2, 1 back-screens for 5, lob from 4 to 5; 1 s full court — catch-and-shoot for 4 or 5; 1 s baseline vs man — lob 1→4 in the box, catch-and-shoot in the air; **under 0.4 s tap**.
- **Usual counters:** see A6.32–A6.36.
- **Detection signature [HEURISTIC]:** bucket end-of-game inbounds by game clock — ≤ 0.3 s (tap only, R5); 0.4–1.0 s (catch-and-shoot in the air / lob); 1–3 s (one action); 3–5 s (one pass + dribble); > 5–6 s (Split-type return + dribble) — and compare the observed action with the bucket.
- **Teams documented:** coaching text, not D-I-specific `[Q4]`.
- **Sources:** `[Q4]`.
- **Confidence:** medium.

#### A6.28 MSU hold for the last shot after a 60-s timeout at a tie (Purdue, 2022) — RICHER (documented MSU instance for F13.4 "Last shot", which was [CONVENTION])
- **Name and aliases:** last-shot ATO (tie game); label `last_shot_tie_ATO`.
- **Family / sub-family:** F13.4 last shot / F13.1 ATO.
- **Start alignment:** half-court after a 60-s timeout (spots not described).
- **Roles:** shooter Tyson Walker (pull-up three).
- **Ordered actions `[Q48]`:** MSU vs No. 4 Purdue, 26 Feb 2022: tied 65–65 after a Purdue putback at 0:30; MSU 60-s timeout at 0:16; Walker pull-up three at 0:01 (68–65); MSU 30-s timeout at 0:01; Purdue turned it over at 0:00. Shot clock off (game clock < 30 s, R6). ATO possession ≈ 15 s, released with ≈ 1 s left.
- **Usual counters:** switch everything late; foul when up 3 (not applicable at a tie).
- **Detection signature [HEURISTIC]:** possession starts with game clock ≤ 30 s and the score tied; ATO; FGA at game clock ≤ 3 s.
- **Teams documented:** MSU 2021-22 `[Q48]` [pre-window].
- **Sources:** `[Q48]`.
- **Confidence:** high (play-by-play).

**End-of-game data and rules of thumb (no new block; feed priors).** ATO efficiency: Creighton 2023-24 0.985 PPP on ATOs, 91st percentile (Synergy via Hurrdat), 1.364 PPP (15 points on 11 ATOs) vs Oregon, media-timeout ATOs included `[Q15]`. Special Teams Playbook (Chris Filios) top sets: ATO vs man UCLA 2017 1.124 PPP; ATO vs zone UNC Wilmington 2017 1.448; BLOB vs man Virginia 2017 1.198; BLOB vs zone IPFW 2016 1.929; SLOB La Salle 2017 1.280; Izzo stresses five special-teams areas (jump balls, BLOB, SLOB, free throws, ATO) `[Q46]`. Izzo's goal: 4–5 points per game from dead-ball play; his 2010 DVD covers 3 jump-ball plays, 5 BLOBs, 4 SLOBs, 5 ATOs vs pressure `[Q47]`. ATO prior ≈ 0.85–1.0 PPP (Creighton 0.985 = 91st pct, so the D-I median is below 0.985; exact median **unverified**). NCAA.com ATO article (Baylor 1.55, Villanova 1.50) — **unverified** (empty page). Last-shot timing: HoopTactics "in position at 10 s, start at ~8 s, shoot at 3–5 s" — **unverified** (snippet); Better Basketball (HS, 2016): change mode at 1:00 and shoot at about 3 s so there is time for a tip-in `[Q49]`. Timeout vs no-timeout late (Harvard Sports Analysis, 2009-10 close games: tied 35.7% vs 53.0% scoring; down 2 1.05 vs 1.18 PPP) — **unverified** (pages returned HTTP 500). Use: flag `ATO` vs `no_timeout_play_on` for possessions starting with game clock ≤ 35 s and margin within 3; compute `last_shot_start` (game clock at the first screen or drive of the final action) and `last_shot_release` (game clock at the FGA).

#### A6.29 Late-clock shot profile (D-I 2025-26) — NEW data layer for F13.5
- **Name and aliases:** late-clock shot mix.
- **Family / sub-family:** F13.5 late clock (data/prior layer).
- **Start alignment / roles / ordered actions:** not applicable (prior).
- **Data `[Q50]`:** ShotTracker (31 Aug 2026; 2025-26 season): with ≤ 5 s on the shot clock, men's 3PA rate rises to 43.5% from 39.6% overall; bigs' FG% falls to 38.5% from 49.9%; guards' 3P% falls to 28.5% from 34.4%; sample size not given.
- **Usual counters:** —
- **Detection signature / use [HEURISTIC]:** priors for the `late_clock` (shot clock ≤ 5 s) shot-type classifier and expected points.
- **Teams documented:** D-I men 2025-26 (aggregate) `[Q50]`.
- **Sources:** `[Q50]`.
- **Confidence:** medium-high.

#### A6.30 End-of-clock SLOB/BLOB as a late-clock tool (MSU) — NEW label
- **Name and aliases:** `late_clock_inbound`.
- **Family / sub-family:** F13.5 × F13.2/F13.3.
- **Start alignment / roles / ordered actions:** MSU Misdirection SLOB is described as an "end of clock SLOB" (A6.16) `[Q29]`; MSU Clear BLOB is for "late in the shot clock" (A1.15) `[Q12]`. Expected: one action, then a shot within the remaining shot clock.
- **Usual counters:** switch everything; deny the primary target.
- **Detection signature [HEURISTIC]:** INBOUND_EVENT with shot clock ≤ 10 s at t_dispose ⇒ `late_clock_inbound`; compare shot quality with live late-clock possessions.
- **Teams documented:** MSU (2020-21, 2021-22 diagrams) `[Q29][Q12]`.
- **Sources:** `[Q29][Q12]`.
- **Confidence:** medium.

#### A6.31 BLOB efficiency ≈ half-court efficiency (decade study) — NEW prior
- **Name and aliases:** BLOB PPP prior.
- **Family / sub-family:** F13.2 data layer.
- **Data:** Hoop Vision (15 Sep 2019): over the 2010s, excluding second chances, D-I BLOB plays averaged 0.84 points per play vs 0.85 on other half-court plays; r = 0.50 between a team's BLOB and half-court efficiency; samples are small (2018 Wake Forest ran only 138 BLOB plays). Top-10 BLOB teams of the decade: Gonzaga, Belmont, William & Mary, Denver, South Dakota State, Duke, Wisconsin, Davidson, San Francisco, Wichita State `[Q16]`. Hudl: a top college team posts about 1.2 points per BLOB/SLOB (sample undefined) `[Q51]`.
- **Detection signature / use [HEURISTIC]:** prior PPP for BLOB ≈ 0.84; flag team BLOB PPP with n < 150 as low-confidence.
- **Teams documented:** D-I aggregate; Wisconsin #7 (Big Ten) `[Q16]`.
- **Sources:** `[Q16][Q51]`.
- **Confidence:** high (Hoop Vision); low (Hudl figure, undefined).

**Defensive special-situation items found by the same research** (defence family numbering from `defense_full.md` F14 Special-situation defence; recorded here because they are the counters the A6 offensive templates are built against; the defence file has its own single writer):

| Item | Defence family | Definition / evidence | Detection signature [HEURISTIC] | Teams, keys | Confidence |
|---|---|---|---|---|---|
| **A6.32 Lock-and-trail BLOB coverage** | defense_full F14 (BLOB) using F5.1 lock-and-trail | defenders trail cutters tightly through BLOB screens; effective BLOB designs account for it; the **circle lob** (A6.8) counters it `[Q16]` | on BLOB screens the cutter's defender stays within 1.0 m behind the cutter on the same side of the screen (chase) rather than switching; count per BLOB | D-I generic `[Q16]` | medium |
| **A6.33 "Big on the inbounder, switch everything"** | defense_full F14 BLOB (adds the big-on-ball assignment and turnover rates to the existing "switch all screens from the baseline up" `[D79]`) | Stephen F. Austin (2015, 2016) put the centre on the inbounder and switched everything; **Ohio State 2010-11** put Jared Sullinger or Dallas Lauderdale on the ball and switched everything else; five teams forced turnovers on 30% of BLOB plays in a season: SFA 2015 and 2016, Denver 2012, East Tennessee State 2017, Ohio State 2011 `[Q16]` | at t_dispose the inbounder's defender is the tallest defender within 1.5 m of the inbounder; switch rate on BLOB screens ≥ 0.9; outcome flag BLOB turnover | Ohio State 2010-11 (Big Ten), SFA, Denver, ETSU `[Q16]` | high |
| **A6.34 BLOB zone with a strong-side corner trap (Florida State)** | defense_full F14 BLOB zone variant (F14 has the 2-3 with a forward on the corner; new = trapping the corner) | length on the ball, anticipate the safety pass, trap the strong-side corner `[Q16]` | zone classification (F8.0) during the BLOB window; on a corner catch (θ ≤ 12°) two defenders within 1.5 m of the receiver within 1.0 s | Florida State `[Q16]` | medium |
| **A6.35 No man on the inbounder, double the primary target** | defense_full F14 end of game (F9.1 "41 Deny" is the press version) | Kentucky 1992 did not guard Grant Hill and doubled Laettner (Duke scored, A6.25) `[Q43]`; Houston 2018 did not guard Isaiah Livers and initially doubled Abdur-Rahkman (Michigan scored, A6.24) `[Q42]` | FULLCOURT or SLOB inbound with game clock ≤ 5 s: no defender within 3 m of the inbounder at t_release; one receiver with two defenders within 2 m | Kentucky 1991-92, Houston 2017-18 `[Q43][Q42]` | high |
| **A6.36 Disguise and switch on late inbounds; double to disrupt set plays** | defense_full F14 last shot ("disguise" is new) | switch all screens, attack passing lanes, disguise coverage on inbounds plays, double to disrupt set plays, consider a combination defence vs a star, avoid fouling, box out every shot `[Q52]` | coverage label at t_dispose (man/zone, F8.0) differs from the label 2 s after t_touch | generic coaching source `[Q52]` | medium |

#### A6.37 Enrichments to existing F13 rows (content now known; rows above keep their wording)
| Existing row | New sourced content | Keys | Confidence |
|---|---|---|---|
| F13.2 "STS ATO BLOB" ([title only]) | Run at Duke, 1 Dec 2020 (2020-21): entry pass to the corner; 3 comes off a screen to the elbow extension; 2 screens for 5; 4 sets a turnout screen for 2; 2- or 3-point options. Contributor Kostas Kalogeropoulos (Olympiacos), posted 8 Dec 2020 (also A1.15, A5.4) | `[Q55]` | high (caption) |
| F13.2 "Line — Screen the Inbounder" (MSU) | Coach's Clipboard newsletter (16 Feb 2022) gives the stack version and a vs-2-3 variant: 2 screens the middle low zone defender; 3's down screen on the outside low defender frees 2 in the corner | `[Q53][Q34]` | medium |
| F13.3 "Line-1 / SLOB '1'" (MSU) | FastModel "One SLOB" (6 Aug 2019): "a Tom Izzo classic SLOB out of a timeout": feed the post (3 seals); 1 sprints to the wing on the catch; 2 follows the pass; 1 pivots back off a 4–5 stagger; 3 shoots or kicks to 1 | `[Q54]` | medium |
| F13.2 "Box Double Down" (MSU) | Full text: 5 pops to the arc; 1 cuts over 4's top screen; 5→4→1; 3 back-screens for 5 (post); 3 and 4 double-down for 2 (three) | `[Q34]` | medium |

**Special-situation gaps.** No opened source gives MSU BLOB/SLOB/ATO PPP or frequency (Synergy/Hoop Vision ATO data paywalled). No 2024-25 or 2025-26 MSU end-of-game inbound breakdown found. Exact game dates for several MSU FastModel entries (Maryland 2014-15, Sparty, Clear BLOB, Quick Duck-In) not confirmed. No D-I source describes a "diamond/1-3-1" BLOB in detail (the F13.2 gap persists; Wisconsin "Diamond" is a SLOB). No dedicated "end-of-half" set distinct from the F13.4 2-for-1 logic was found. Starting alignments for most FastModel plays are image-only, so every coordinate in A6 is [HEURISTIC] until checked on film.

### A7. F11 Zone offense: MSU zone sets, named college zone hitters, systems and rule sets (extends 11.1–11.2)

Source keys `[Z:TAG]` are the zone/press research note's tags (resolved in the zone/press block of the Additional sources list). Proposed sub-family codes (extending F11.1/F11.2): **F11.3 MSU zone sets**, **F11.4 named college zone quick-hitters (vs 2-3)**, **F11.5 continuity/system zone offences**, **F11.6 zone principles (new rule sets)**, **F11.7 vs match-up zone**, **F11.8 vs 1-3-1**, **F11.9 vs 1-2-2/3-2**, **F11.10 overload sets by programme**. Defensive counterparts: defense_full F8.1 (2-3), F8.2 (odd fronts), F8.3 (match-up), F8.4 (zone tactics).

**Zone primitives [HEURISTIC]:**
- `ZONE_SCREEN` ("screen the zone", pin, pin-in, back-screen the zone): a SCREEN whose target is a zone defender (defence layer, F8); valid if (a) the screener is within 1.0 m of the defender, (b) the defender's displacement toward the area the cutter/shooter enters is < 0.6 m over the next 1.0 s, and (c) a teammate catches or shoots within 2.5 s in the region that defender would have covered. Sub-types by target slot: top (X1/X2), wing/forward "low outside" (X3/X4), middle (X5).
- `SEAL / DUCK-IN`: attacker within 1.0 m of a defender on the rim or ball side, ≤ 0.3 m/s for ≥ 0.8 s; a duck-in is a 1–3 m move toward the lane from the block/short corner ending in a seal.
- `FLASH` (zone): ≥ 2.5 m in ≤ 1.5 s, peak ≥ 3.0 m/s, ending in the high post (r 3.5–5.0, θ 65–115°), at an elbow or in the gap between two adjacent zone defenders.
- `SKIP`: sign(x_start) ≠ sign(x_end), \|Δx\| ≥ 9 m, bypassing at least one perimeter teammate.
- `GAP_DRIVE`: a dribble from r ≥ 6.5 heading within ± 20° of the bisector between two adjacent zone defenders ≥ 3.0 m apart; ends at r ≤ 5.0 or with a pass.
- `DRIBBLE_AT` ("dribble at, run away"): handler dribbles ≥ 2 m within 30° of a perimeter teammate, who moves ≥ 2 m away or cuts within 1.5 s; `THROW_BACK`: a pass within 2.0 s whose direction is > 120° from the dribble vector.
- `BASELINE_RUN`: a player at y < 0.8 m crosses x = 0 with \|Δx\| ≥ 9 m in ≤ 3.5 s. `OVERLOAD_STATE`: ≥ 4 attackers with the same sign(x), or 3 attackers in a 7 m-wide ball-side window guarded by 2 defenders, held ≥ 1.0 s.
- Extra zone spots: "high" short corner (4.27, 20.6) [(4.27, 159.4)].

#### A7.1 MSU "33" (box set vs 2-3) — NEW (F11.3)
- **Name and aliases:** "33" (also in the MSU zone list `[Z:MSUSETS]`).
- **Family / sub-family:** F11.3 MSU zone sets (vs defense_full F8.1 2-3).
- **Start alignment (box; spots [HEURISTIC]):** O1 top (7.5, 90); O3 right wing (7.2, 45); O2 left wing/high side of the box (7.2, 135); O4 left elbow/high box (4.57, 113.6); O5 left block/low box (2.04, 153.8).
- **Roles:** O1 passer, cutter to the corner; O3 hub/passer; O4 screener on the top-left zone defender; O5 back-side screener on the low-left outside defender, then lob target; O2 shooter off O5.
- **Ordered actions `[Z:CCNL14]` [timing HEURISTIC; t0 = first pass O1→O3]:** (1) O1→O3 and O1 cuts around O3, shifting the zone right; (2) O3 fakes a handoff, O1 continues to the right corner (0.8–1.8 s); (3) O4 screens the top-left defender while O5 screens the low-left outside defender on the back side (1.5–3.0 s); (4) O2 cuts around O5's screen for a pass from O3 and an open shot (2.5–4.5 s); (5) options: O3 lobs to O5, bounces to O4 cutting through, or returns to O1 in the corner for three.
- **Usual counters:** the zone does not shift on the O1 cut, or X5 sits in the lane to take the lob; high-post swarm or a 2-3 that bumps the forward (defense_full F8.4).
- **Detection signature [HEURISTIC]:** pass and follow-cut (O1 within 1.5 m of O3 within 1.5 s of the pass); fake DHO (two players within 1.0 m without a ball transfer for ≥ 0.4 s); two simultaneous ZONE_SCREENs (onsets within 0.7 s) opposite the ball — one on a top defender at r 5.5–7.5, one on a low outside defender at r 3–5, θ 120–170°; a cutter passes within 1.5 m of the low screener and catches at r 4.5–6.5 on the weak side within 2.5 s.
- **Teams documented:** MSU (Izzo); season not stated (newsletter 1 Dec 2014) `[Z:CCNL14]`.
- **Sources:** `[Z:CCNL14][Z:MSUSETS]`.
- **Confidence:** medium.

#### A7.2 MSU "Spartan Zone Options" (dribble entry, curl off a middle screen, weak-side down screen) — NEW (F11.3)
- **Name and aliases:** Spartan Zone Options.
- **Family / sub-family:** F11.3 (vs 2-3).
- **Start alignment [HEURISTIC]:** O1 top (7.5, 90); O2 right wing (7.2, 45); O3 left short corner/low wing (4.27, 159.4); O4 left block (2.04, 153.8); O5 right elbow/high post (4.57, 66.4).
- **Roles:** O1 dribble-entry passer; O2 curler; O5 screener on the middle defender; O4 down-screener on the low-left defender, then layup target; O3 shooter lifting to the wing.
- **Ordered actions `[Z:FMSZO1][Z:FMSZO2]` [timing HEURISTIC]:** (1) O1 dribbles to the right wing, pushing O2 into the lane (0–1.5 s); (2) O2 stops at the rim while O5 screens the middle defender (1.0–2.5 s); (3) O2 curls into the middle (catch 2.0–3.5 s); (4) weak side: O4 screens the low-left defender and O3 cuts up to the wing; (5) read on O2's catch: low-left defender follows O3 → O4 layup; stays with O4 → O3 shot; middle defender steps up to O2 → O4 at the rim. Kick or dump ≤ 1.0 s after the catch.
- **Usual counters:** X5 jams the curl; the weak-side low defender splits O3 and O4.
- **Detection signature [HEURISTIC]:** DRIBBLE_AT from the top to the wing (≥ 3 m, θ 90 → 45°) with the wing cutting to r < 2 within 1.5 s (push cut); ZONE_SCREEN on the middle defender at r 2–4; a curl from r < 1.5 to r 3–4.5 at θ 70–110°; simultaneous weak-side SCREEN by a big on the low weak defender (θ 140–170°, r 2–4) with a teammate moving from r < 4.5 to r ≥ 6.5 on the weak wing; the curler's pass ends at r < 2 (dump) or r ≥ 6.5 weak side (kick).
- **Teams documented:** MSU (Izzo), FastModel (published 2 Apr 2015 and 18 Jul 2015); season not stated `[Z:FMSZO1][Z:FMSZO2]`.
- **Sources:** `[Z:FMSZO1][Z:FMSZO2]`.
- **Confidence:** medium.

#### A7.3 MSU "Arm Chop" (vs 2-3) — NEW (F11.3)
- **Name and aliases:** Tom Izzo: Arm Chop.
- **Family / sub-family:** F11.3 (vs 2-3).
- **Start alignment [HEURISTIC]:** O1 top (7.5, 90); O3 right wing (7.2, 45); O2 left wing (7.2, 135); O5 right block/post (2.04, 26.2); O4 below the zone, left (2.04, 153.8).
- **Roles:** O1 driver; O3 entry passer, then top shooter; O5 post, then baseline cutter; O4 high-side screener on the top defender; O2 spot-up target.
- **Ordered actions `[Z:FMARM]` [timing HEURISTIC]:** (1) O1→O3; O3 takes 1–2 dribbles toward the wing looking to feed O5; O4 rises to the weak-side elbow (0.5–2.0 s); (2) O3→O1; O5 cuts below the zone toward the basket; O4 screens the top defender; O1 attacks (drive, or draw and kick to O2) (2.0–4.0 s); (3) if nothing: O4 down-screens the top defender, O3 cuts to the top and O1 hits O3 for three (4.0–6.5 s).
- **Usual counters:** the top defender goes under O4; X5 stays home on the baseline cutter.
- **Detection signature [HEURISTIC]:** wing catch, 1–2 dribbles (≤ 2 m), pass back to the top; a big moves from r < 3 to the weak elbow (r 4.2–5.0, θ 105–120°) within 2 s; ZONE_SCREEN on a top defender (r 5.5–7.5) by that big, then a dribble ≥ 2 m by O1 toward the screened side; a post crossing under the zone (y < 1.0, \|Δx\| ≥ 3 m); a second ZONE_SCREEN by the same big (down screen) and a catch at the top (r 7–8.5, θ 80–100°) by the original wing.
- **Teams documented:** MSU (Izzo), FastModel (published 26 Apr 2015; season not stated) `[Z:FMARM]`.
- **Sources:** `[Z:FMARM]`.
- **Confidence:** medium.

#### A7.4 MSU "Push Pipe Pin" vs 2-3 — NEW (F11.3)
- **Name and aliases:** Push Pipe Pin.
- **Family / sub-family:** F11.3 (vs 2-3).
- **Start alignment [HEURISTIC]:** O1 top (7.5, 90); O3 right wing (7.2, 45); O2 left low (4.27, 159.4), popping to the wing; O4 left mid-post (3.11, 135); O5 right block/high post.
- **Roles:** O1 passer then driver at X1; O3 "pushed" into a pipe cut; O5 occupies X5 and seals X4; O4 pin-down screener on X3; O2 shooter.
- **Ordered actions `[Z:FMPPP]` [timing HEURISTIC]:** (1) O1→O3 and O1 follows to get it back, shifting X2 toward the wing and X1 toward the high post (0–1.5 s); (2) O1 pushes O3 into a pipe cut — down the baseline, then up the middle of the lane to the high post — occupying X5 while O5 seals X4 (1.5–4.0 s; ≈ 8–10 m at 3–4 m/s); (3) O4 pins down on X3 and O2 pops to the wing (3.0–4.5 s); (4) O1 drives at X1; if X1 helps, O2 is open (4.0–6.0 s).
- **Usual counters:** X1 stays home and X5 steps up to the drive → dump to O5.
- **Detection signature [HEURISTIC]:** pass-and-follow with a hand-back (two passes between the same pair within 2.5 s); a wing cutter's U-shaped "pipe" path from (7, 45) down to y < 1.0, along the baseline toward x = 0 and up to r 3.5–5, θ 80–100°, lasting 2–3.5 s; a big SEALs the ball-side forward slot defender; a ZONE_SCREEN pin-down on the weak-side forward with a teammate rising from r < 5 to r ≥ 6.75 at θ 120–150°; a DRIBBLE_AT the top defender ending in a pass to the weak wing.
- **Teams documented:** MSU vs Iowa, Big Ten Tournament — produced MSU's first lead (page 16 Mar 2013; season most likely 2012-13, **unverified**) `[Z:FMPPP]`.
- **Sources:** `[Z:FMPPP]`.
- **Confidence:** medium.

#### A7.5 MSU "Zone Lob Set" (double zone screen at the top, drive, lob vs a 2-3 match-up) — NEW (F11.3 / F11.7)
- **Name and aliases:** Zone Lob Set.
- **Family / sub-family:** F11.3 / F11.7 (vs F8.3 match-up 2-3).
- **Start alignment [HEURISTIC]:** O1 top (7.5, 90); O2 and O5 near the top defenders (slot/elbow); O4 weak-side block (2.04, 153.8); O3 ball-side wing (7.2, 45).
- **Roles:** O1 driver; O5 first screener on X1; O2 second screener on X2; O4 lob receiver.
- **Ordered actions `[Z:FMZLS]` [timing HEURISTIC]:** (1) wing pass shifts the zone; (2) O5 screens X1 and O2 screens X2 (1.5–3.0 s after the return pass); (3) O1 drives the gap (2.5–4.0 s); (4) when X5 steps up, O1 lobs to O4 (≤ 0.8 s after X5's first forward step).
- **Usual counters:** X5 stays down and the weak forward fronts O4.
- **Detection signature [HEURISTIC]:** two ZONE_SCREENs on both top defenders within 0.8 s (screeners at r 5.5–7.5, θ 60–120°); a GAP_DRIVE between them ending at r 3.5–5; X5's y increases ≥ 1.0 m within 0.8 s; then a lob proxy (pass from r ≈ 4–5 to r < 1.5 on the weak side, flight ≥ 0.7 s).
- **Teams documented:** listed as MSU, modelled on the 2-3 match-up Louisville played against MSU in the East Regional final (page 29 Mar 2015 → 2014-15, inferred, **unverified**); the contributor is a Canadian university coach, not MSU `[Z:FMZLS]`.
- **Sources:** `[Z:FMZLS]`.
- **Confidence:** low-medium.

#### A7.6 "Zone Cross Lob" (NCAA set; MSU among the users) — NEW (F11.4)
- **Name and aliases:** NCAA Set: Zone Cross Lob.
- **Family / sub-family:** F11.4 (vs 2-3).
- **Start alignment [HEURISTIC]:** O1 top (7.5, 90); O2 and O3 on the wings; O5 high or mid-post; O4 low.
- **Roles:** O2, O3 crossing zone screeners; O5 big-to-big screener; O4 lob diver; O1 passer.
- **Ordered actions `[Z:FMXL]` [timing HEURISTIC]:** (1) O1→O3→O1 (shift and return, 0–2 s); (2) O2 and O3 cross under the top two zone defenders and screen the **opposite** guard on the inside (2–3.5 s); (3) O5 screens for O4, who dives for a lob; (4) O1→O4 (3–4.5 s). Key: isolate X5 and draw him toward the ball so the baseline opens.
- **Usual counters:** X5 refuses to step up; the weak forward rotates under.
- **Detection signature [HEURISTIC]:** two wings cross paths (intersection within r 4–7, θ 60–120°) and each stops within 1.0 m of the far-side top defender (crossed ZONE_SCREENs); a big-to-big SCREEN at r 2–4.5, then the screened big dives to r < 1.5; a pass from the top to the rim with flight ≥ 0.7 s.
- **Teams documented:** the page lists MSU, Arizona, Kansas, Iowa State, Louisville and NC State; no seasons `[Z:FMXL]`.
- **Sources:** `[Z:FMXL]`.
- **Confidence:** low-medium (multi-team attribution without seasons).

#### A7.7 MSU "Fist-Down" full sequence — RICHER (extends F11.2 "Izzo … Fist Down", which had the name only)
- **Name and aliases:** Fist-Down.
- **Family / sub-family:** F11.3 (vs 2-3 and 3-2).
- **Start alignment `[Z:CCFD]` (spots [HEURISTIC]):** O2 right wing, best shooter (7.2, 45); O3 left short corner (4.51, 176.2); O4 left wing (7.2, 135); O5 high post, least skilled scorer (4.19, 90); O1 top with the ball (7.5, 90).
- **Roles:** O1 passer then wing replacer and feeder; O2 dribbler then paint cutter; O5 middle screener; O4 weak-side down-screener then basket cutter; O3 weak-wing lift.
- **Ordered actions `[Z:CCFD]`:** (1) O1→O2; O2 dribbles toward the corner, then passes back to O1, who has replaced O2 on the wing; (2) during O2's dribble, O5 screens X5, O4 down-screens the weak low defender (X3) and O3 cuts out to the left wing; (3) O2 passes to O1 and cuts hard around O5's screen into the paint; (4) O1 "waits a second", dribbles up for an angle and feeds O2. Options: O4 cuts to the basket after screening (bounce pass); O3 open on the wing if X3 stays with O4; skip O1→O3 if the paint is clogged; O5 post-up if X5 steps to O2. Timing: feed ≈ 1 s after O2's cut begins (source); rest [HEURISTIC]: dribble 0.5–2 s, screens 1.0–2.5 s, paint catch 2.5–4.5 s. Izzo calls it strange; it works against 2-3 and 3-2 zones, not well against a 1-3-1.
- **Usual counters:** a 1-3-1 (stated); X5 stays home.
- **Detection signature [HEURISTIC]:** a wing dribble toward the corner (θ 45 → < 20°, ≥ 2 m) with the top player replacing on the wing (≥ 3 m) within 1.5 s; simultaneous screens — high post on X5, weak-wing big on the weak low defender; pass back to the replacing wing, then the passer cuts into the paint (r < 3) within 1.5 m of the high-post screener; a ≈ 1 s hold, a short upward dribble (≤ 2 m) and a pass to r < 3.
- **Teams documented:** MSU vs Syracuse and Florida 2-3 zones (seasons not stated) `[Z:CCFD]` (cf. `[O62]`).
- **Sources:** `[Z:CCFD]`.
- **Confidence:** medium-high for the sequence.

**MSU zone context (not plays).** In the 71–67 loss at Indiana (11 Feb 2025, inferred from a 12 Feb article), SI's MSU site said the offence looked poor against a simple 2-3: no rim attacks, no big moving into the middle, early-clock low-quality shots `[Z:SIIND25]`. **Requirement implication:** log "no high-post touch" and "early-clock jumper vs zone" as negative markers. MSU "Vs Zone" (2024-25) is A1.5; MSU "Zone O – Short Roll" (2015) is in A3.10 `[Z:FMSR]`. A Hoopscoop post (6 Feb 2012) lists a "Tom Izzo Michigan State Zone Set Play" in a PDF that was not read — **unverified** `[Z:HSIZ12]`. FastModel "Zone Offense – Izzo 2" (2024) and "Zone Lob – 'Michigan State'" (2021) do not attribute the play to MSU in their text — do not tag [MSU] `[Z:FMIZ2][Z:FMZLMSU]`.

#### A7.8 Kansas (Bill Self) stationary "hot potato" 2-3 zone offence — NEW system (F11.5)
- **Name and aliases:** Self "stationary" zone offence; "hot potato" (Self's phrase).
- **Family / sub-family:** F11.5 system zone offence (vs 2-3).
- **Start alignment [HEURISTIC spots]:** 3-out 2-in with both posts low: O1 top (7.5, 90); O2/O3 wings (7.2, 45)/(7.2, 135); O4/O5 blocks (2.04, 26.2)/(2.04, 153.8).
- **Roles:** stationary perimeter passers; two posts reacting to the ball.
- **Ordered actions / rules `[Z:CCKZO]`:** perimeter stays relatively stationary and moves the zone by quick passing; minimal dribbling except a gap dribble; best shots come after several reversals. Wing pass → the opposite low post cuts to the ball-side elbow (if denied, seals for a lob). Wing → low post → the elbow player dives, then relocates to the opposite block or short corner. Wing-to-wing skip → both posts cross the lane to the ball side. Low post → opposite wing → the FT-line post crack-back screens the defender of the opposite wing's man, who cuts into the lane; the screener seals ball side. One dribble by the wing toward the top → the ball-side post goes to the short corner and the opposite post to the ball-side elbow. Flash denied → the post back-screens the low outside defender, the opposite wing slides to the corner, skip to the corner for three. Self (Dec 2013): keep the ball moving ("hot potato"); get into the gaps because the zone "distorts"; make two defenders guard three perimeter players honestly; shooting is the best zone offence; KU had prepared mostly against the 1-3-1 before the Florida loss on 10 Dec 2013 `[Z:KUS13]`. Timing [HEURISTIC]: perimeter pass rate ≥ 1 per 1.5 s; shot after ≥ 2 reversals, typically 8–20 s into the half-court possession.
- **Usual counters:** trap the wing; deny the elbow flash.
- **Detection signature [HEURISTIC]:** 3-2 shape (3 at r ≥ 6.75, 2 at r < 3) at the half-court set; mean perimeter holding time ≤ 1.2 s; ≤ 1 dribble per perimeter touch; on each wing catch the weak block player reaches the ball-side elbow (r 4.2–5.0, θ 60–75° or 105–120°) within 1.2 s (score the compliance rate); on each skip both posts cross x = 0 toward the ball within 1.5 s; crack-back = the FT-line post moves away from the ball and screens a perimeter-slot zone defender.
- **Teams documented:** Kansas (Self) `[Z:CCKZO]`; 2013-14 quotes `[Z:KUS13]`.
- **Sources:** `[Z:CCKZO][Z:KUS13]`.
- **Confidence:** medium-high (rules); high (quotes).

#### A7.9 Kansas (Self) zone quick-hitters #1, #2, #3, #4, #8 and "Ball Screen to Pin In" — NEW (F11.4)
- **Name and aliases:** KU Zone Play 1/2/3/4/8; "Ball Screen to Pin In".
- **Family / sub-family:** F11.4 (vs 2-3).
- **Start alignment:** base 3-out 2-in, both posts low (A7.8); #1 has O5 at the high post (4.19, 90); #3 has O1 on the left lane line extended (≈ 7.7, 104) [HEURISTIC].
- **Roles:** as per play (posts screen zone defenders; perimeter passers and cutters).
- **Ordered actions `[Z:CCKZP][Z:FMKBSP]`:** **#1:** O1→O3 and cut through to the opposite corner; O5 steps out for a pass from O3 and swings to O2, who hits O1 in the corner; O5 cuts to the ball-side elbow, gets it from O1 and looks to O4 sealing the low defender; option O1→O4 and O5 dives to the weak block (high-low). **#2:** O1 dribbles right; O2 slides to the corner and catches; O2 skips to O3, drawing the outside low defender; O4 cuts to the ball-side elbow to hold the middle; O5 screens the low defender who was on O2, and O2 cuts around for a pass from O3 (weak-side lob for big teams). **#3:** O1→O2; O5 flashes to the ball-side elbow; O3 drops inside, then screens the low defender for O4; O2→O1 and O4 cuts left for a quick pass. **#4:** O1→O3 and cut to the ball-side corner; O3→O1, pulling the outside low defender; O5 screens the middle low defender and O4 cuts ball side for a layup; option skip to O2 for three. **#8:** O1→O3; O4 screens X2 and O5 screens the inside low X5; O3 dribbles right and passes back to O1; O4 slips down the right lane for a layup, or kicks to O2 if X4 helps. **Ball Screen to Pin In** (FastModel 2023): O1→O2 and O4 sets a ball screen; O2 comes off it and passes back to O1 while O4 dives into the middle of the zone; O5 screens the middle of the zone (pin-in) and O1 hits O4 for a layup. Timing [HEURISTIC]: one-reversal hitters; scoring pass 3–6 s after the first pass.
- **Usual counters:** the middle defender steps through the pin early; the weak forward fronts.
- **Detection signature [HEURISTIC]:** **#2** = corner catch → SKIP to the far wing → ZONE_SCREEN on the low defender of the original corner side, the corner man cutting off it within 2.0 s of the skip. **#4** = corner cut by the first passer (θ < 12° or > 168°) → pass back to the corner → ZONE_SCREEN on the middle low defender → ball-side cut to r < 2. **#8** = two ZONE_SCREENs (a top defender and X5) followed by a slip (screener leaves within 0.6 s toward r < 2). **Ball Screen to Pin In** = a wing ball screen (r 6.5–8, θ 25–65°), the screener dives into the zone middle (r 2–4, θ 60–120°) and a second big holds a ZONE_SCREEN on the middle defender within 1.0 m of the diver's endpoint.
- **Teams documented:** Kansas (Self); seasons not given; plays #5–#7 premium (not seen); the "best zone play ever" quote — **unverified** `[Z:CCKZP][Z:FMKBSP]`.
- **Sources:** `[Z:CCKZP][Z:FMKBSP]`.
- **Confidence:** medium.

#### A7.10 "Carolina" and "Zone-1 X" (skip, then screen the middle; vs 2-3) — NEW (F11.4; generic)
- **Name and aliases:** Carolina; Zone-1 X.
- **Family / sub-family:** F11.4 (vs 2-3).
- **Start alignment [HEURISTIC]:** 1-2-2 or 1-3-1 base; O4 at the ball-side elbow area; O5 low weak side.
- **Roles:** O3 re-screener (outside low, then middle); O4 cutter; O5 weak-corner skip target (Carolina).
- **Ordered actions `[Z:CC23P]`:** Carolina: O1→O2 shifts the zone; O5 slides to the weak corner; O3 back-screens the outside low defender; O2 skips to O5; O4 cuts to the ball-side elbow, then to the block off O3's screen on the middle defender for a layup. Zone-1 X (no skip): O1 dribbles right to draw the top defender; O3 screens the outside low defender while O2 slides to the corner; O1→O2; O3 lets the defender out, then screens the middle defender, and O4 cuts around for a layup — best when the middle defender cheats up to the high post. Timing [HEURISTIC]: re-screen 1.5–3.5 s; layup ≤ 1.5 s after the second screen.
- **Usual counters:** the middle defender stays low.
- **Detection signature [HEURISTIC]:** "re-screen" = the same screener sets two ZONE_SCREENs on different defenders within 2.5 s — first the outside low (r 3–5, θ < 30° or > 150°), then the middle (r 1.5–3.5); a cutter goes elbow → block passing within 1.5 m of the second screen.
- **Teams documented:** none named (generic) `[Z:CC23P]`.
- **Sources:** `[Z:CC23P]`.
- **Confidence:** medium (pattern); no team attribution.

#### A7.11 Named zone quick-hitters from coaching sources (compact full format) — NEW (F11.4 unless stated)
Timing windows are [HEURISTIC]; start spots are [HEURISTIC] unless keyed. All rows: confidence **medium for the pattern**, low or none for team usage unless stated.

| Set | Family | Start alignment (r, θ) | Roles | Ordered actions with timing | Usual counters | Detection signature [HEURISTIC] | Teams, keys |
|---|---|---|---|---|---|---|---|
| **"91"** (two-high posts, back-screen flare over the top; simplified man "90 series") | F11.4 vs 2-3 | O4 and O5 at the slots ≈ (7.5, 70)/(7.5, 110); O1 with the ball at the top | O4/O5 receiver and back-screener; O1 flare user; O2 wing clearer; O3 rotates to the point | O1→O4 or O5 (0–1 s); the opposite post back-screens O1's zone defender and O1 flares to the wing (1–2.5 s); O2 moves inside to clear the wing and keep X4 low; over-the-top pass to O1 for a jumper (2–3.5 s); O4, O5 crash; O3 to the point | top defender goes under | two bigs at r ≥ 6.75 at the start; a pass to one big, then the other big SCREENs O1's top/slot zone defender while O1 moves outward ≥ 2 m within 1.5 s (flare vs zone); lob/over-the-top pass from the slot to the wing | none (Coach's Clipboard original) `[Z:CC23P]` |
| **"Chicago" (zone)** (double back-screen lob) — name collision with the F6 pin-down → DHO "Chicago" | F11.4 | O2 left wing (7.2, 135); O4, O5 below the zone at the blocks/dunker spots; O3 weak low; O1 top | O4, O5 crossing back-screeners; O3 baseline lob receiver; O2 lob passer | O2 V-cuts and catches from O1 (0–1.5 s); O5 back-screens X5 and O4 back-screens the weak low X4, crossing for better angles (1.5–3 s); O3 slides below the screens for a lob from O2 (2.5–4 s) | X5 stays home | two bigs at y < 1.5 cross paths (X) and each holds a ZONE_SCREEN on a back-line defender, onsets within 0.7 s; a third player moves along y < 1 beneath them and catches at r < 1.5 off a pass with flight ≥ 0.7 s | Ken Sartini (Arlington Heights, IL; high school); no college team `[Z:CC23P]` |
| **"Miami" (zone)** (pin, skip, re-screen the middle) — name collision with the F6 "Miami" DHO → PnR | F11.4 | O1 top; O3 wing; O4 curling to the left short corner (4.5, 172); O5 low; O2 wing | O4 pin then re-screen; O5 baseline cutter; O2 skip passer; O1 corner receiver | O1→O3 and they exchange spots (0–2.5 s); O4 curls toward the ball, then to the left short corner as a screener; O3→O2; O4 pin-screens the weak low X3; O2 skips to O1, who has dropped to the left corner; O4 delays X3, then screens the middle low defender; O5 cuts under for a power layup | middle defender stays low | guard-to-wing exchange (two players swap spots within 2.5 s); short-corner player (r 3.5–5.5, θ > 160°) pins, then re-screens the middle (A7.10 "re-screen"); SKIP to the far corner (θ > 168°); baseline cut by O5 to r < 1.5 | none named `[Z:CC23P]` |
| **"Vermont"** (double-low-stack entry vs 2-3) | F11.4 | double low stack: O2 over O3 on the left lane line, O4 over O5 on the right, O5 low ≈ (2.2, 30)/(3.0, 50) and mirrored | O5 intended shooter; O4 entry wing then down-screener; O2 corner then wing; O3 wing | O2 cuts to the right corner, O3 to the left wing, O4 pops to the right wing for the entry from O1 (0–1.5 s); O4 looks at O2 and reverses to O1; O1 dribbles left; O2 cuts up to the wing and O4 down-screens X5; O5 curls for an inside jumper (3–5 s) | X5 avoids the down screen | four players within 1.2 m of the lane lines in two vertical pairs (≤ 1.5 m apart) at the start; simultaneous release to corner, wing and wing within 1.5 s; later a big DOWN-screen on the middle zone defender and a curl by the low stacker to r 2.5–4 | from a Jeff Walz DVD (women's coach — affiliation **unverified**); no men's D-I team `[Z:CC23P]` |
| **Flannery "Special" / "Special-Down"** — **name collision with MSU "Special"** (1-3-1; 5 screens the low outside defender `[Z:MSUSETS]`); namespace e.g. `MSU.Special` vs `Flannery.Special` | F11.4 | right-side version: O1 dribbles to the right wing; O3/O5 double screen low; O4 weak side | O3, O5 double screeners; O2 corner shooter; O4 inside cutter; O5 high-low flasher | Special: O1 dribbles to the right wing; O2 cuts under the O3/O5 double screen on X3 for a corner shot (0–2 s); O5 and O3 then screen the middle defender X5 and O4 cuts around for an inside pass (2–4 s); if covered, O5 flashes to the ball-side elbow (high-low) and O3 goes to the opposite wing. Special-Down: O2 and O3 criss-cross to opposite corners below the FT-line extended; O1 passes to the corner; O5 seals X5 for a quick post feed | — | double screen (two screeners within 1.0 m, both stationary ≥ 0.5 s) on a forward zone defender, re-set on the middle defender within 2 s; Special-Down: two guards cross under the basket (paths cross at y < 1.5) and finish in opposite corners within 2.5 s, plus an immediate SEAL on X5 | Eric Flannery (team not given) `[Z:CC23P]` |
| **"West"** (double screen under for a ball-side block cut) | F11.4 | 1-2-2 base; O3 dropping to the baseline; O4 weak side | O5, O3 screeners on X5 and X4; O4 under-cutter; O2 corner fill | optional shift O1→O2→O1; O3 drops toward the baseline; O1 dribbles left; O2 cuts under to the left corner/wing; O5 screens X5 and O3 screens X4; O4 cuts under both screens to the ball-side block (within 2 s); if X3 steps to O2, O1→O4 layup; else O2 three or inside | X3 stays home | two adjacent ZONE_SCREENs on the middle and a forward (screeners ≤ 2.5 m apart along the baseline); a cutter passes under both (y < 1.0) to the ball-side block within 2 s; corner fill by a guard (θ > 160°) | Lindsay Gottlieb (California women's coach at the time); not a men's D-I team `[Z:CC23P]` |
| **"X-Screen Lob"** (Mike White) | F11.4 | O1 top; O2 wing holding; O3, O4 near the top defenders; O5 weak block | O3, O4 crossing screeners on X2/X1; O2 under-cutter and back-screener on X4; O5 lob receiver; O1 driver/lobber | O1→O2, who holds to shift the zone (≥ 1.5 s); O3 sprints out to X-screen X2 and O4 screens X1; O2 passes back to O1, cuts under and back-screens X4; O5 cuts under that screen to the rim; O1 dribbles middle, draws X5 up and lobs to O5 | X5 stays down | wing hold ≥ 1.5 s; two screens on the top defenders by players arriving from opposite sides (crossing paths); the wing cuts under and screens the weak forward; a big cuts from the weak block to r < 1.5; GAP_DRIVE middle with X5's y rising ≥ 1 m, then a lob | Florida (Mike White), DVD "Zone Offense Philosophy, Tactics & Sets"; seasons not given (White at Florida 2015-22 is general knowledge — **unverified**) `[Z:CC23P]` |
| **"Stack-1 / Stack-2 / Stack-3"** (Bryce Drew) | F11.4 | O4 and O5 stacked on the left low lane line; O3 right short corner (4.5, 8); O1 top; O2 wing | stack bigs (screeners/cutters); O3 baseline crosser; O2 lob cutter (Stack-3) | O1→O2 and back; O3 cuts under to the left wing/corner (0–2 s). Stack-1: O1 dribbles left; O5 screens X5 and O4 cuts into the gap for a 3.05 m turnaround. Stack-2: no dribble; O4 back-screens X5 and O5 cuts around for a two-hand overhead lob. Stack-3: after the return pass O2 slides to the corner, O1 dribbles left, O4 and O5 back-screen the two inside defenders, O2 cuts from the corner for a lob (2–5 s) | — | two bigs within 1.2 m on one lane line at the start; a short-corner player crosses the baseline to the far side (≥ 7 m); big-on-X5 screen + gap cut (Stack-1); back screen + lob (Stack-2); double back screen on both back-line defenders + corner-to-rim cut (Stack-3) | Vanderbilt (Bryce Drew), DVD "Multiple Strategies for Attacking Zone Defenses"; season not given `[Z:CC23P]` |
| **Loop action / "Dribble up, throw back" (Loop MIX)** | F11.6 | wing with the ball; point player above | wing dribbler; point loop cutter; throw-back receiver | the wing dribbles at the point player and the zone shifts with the dribble; the dribble-at sends the point on a loop cut; O2 throws back against the grain of the dribble (within 2 s) | zone does not shift | DRIBBLE_AT from the wing toward the top (θ moves toward 90° by ≥ 15°); the dribbled-at player makes a looping cut (curved, ≥ 3 m, returning to r ≥ 6.75 on the side the dribble came from); THROW_BACK to him within 2.0 s; zone-shift measure: mean x of the zone defenders moves ≥ 0.8 m with the dribble before the pass | none (Randy Sherman, Radius Athletics, 2022) `[Z:FMLOOP]` |
| **1-3-1 attacks "Elbow" and "X"** (Creighton Burns) | F11.8 vs 1-3-1 | even front: O1 (7.5, 110), O2 (7.5, 70); wings O3/O4; O5 high or low | Elbow: O2 screener of the bottom defender then of the weak wing; O3 corner/short-corner skip target; O5 decoy diver; O4 flare screener. X: O4 false diver then duck-in; O5 bottom screener; O2 corner sprinter | Elbow: O1 dribbles toward the 2 spot; O2 screens the bottom defender; O3 sprints to the short corner or corner; O2 then screens the weak wing; O5 dives to the block to pull the middle; O4 flares his own defender; O1 cuts diagonally away; O3 is the skip target (taller 3 recommended). X: O1→O2; O4 dives as false action; O2→O1→O3 and O2 cuts to the ball-side block; O3 dribbles to draw the top defender and kicks to O1 sliding away; O5 screens the bottom defender; O4 ducks in; O2 sprints to the corner; O1→O4 or O2 | baseline "warrior" recovers on the skip | vs a 1-3-1 label (one defender at y < 1, three across y 3–6, one at the top): ZONE_SCREEN on the bottom defender paired with a corner/short-corner occupation on that side within 1.5 s; a second screen on the weak wing defender; SKIP to the corner over the baseline defender; a false dive (big to the block, leaves within 2 s with no touch) | Creighton Burns (HS and college coach; teams not named) `[Z:CT131]` |
| **Read & React "Pin & Skip"; 5-out vs 1-3-1** | F11.8 / F11.6 | 5-out (all five at r ≥ 6.0), or 4-out | pinner; skip passer; dribble-at wing | Uie Garcia attacks the 1-3-1 from 5-out, then 4-out; Rick Torbett's Pin & Skip: pin a deep help defender and skip over his head, repeating within the possession; shortcut: a dribble-at makes the dribbled-at wing cut and receive the skip on the opposite side | — | 5-out shape vs a 1-3-1; a PIN (SEAL of a deep defender, y < 2) at the moment of a SKIP whose flight passes within 2 m above that defender; repeat count ≥ 2 per possession | none (Better Basketball; women's example implied) `[Z:BBRR]` |
| **"Triangle" overload continuity and "Toledo" system** (vs 2-3) | F11.5 | Triangle: overload side with the ball. Toledo: posts at the short corner and high post; guards top and wings | posts X-cutting; shooting guard baseline runner; seal post | Triangle: the guard passes weak side; the posts X-cut to opposite spots; the 2 runs the baseline; a post screens and seals the bottom defender; ball to the corner shooter, 5 shot-ready, 4 posting the bottom defender. Toledo: wing pass, then PG attack; the opposite post flashes to the high post/elbow; the 5 in the short corner posts or pops to the corner; a high-post catch triggers shoot/drive/post-to-post/kick; a pass back to the PG triggers a quick reversal | — | Triangle: posts' paths cross inside the lane within 1.5 s of a guard-to-guard pass, plus a BASELINE_RUN by the 2 into the corner, plus a SEAL on the bottom defender on the corner side. Toledo: occupation of the short corner (one post at r 3.5–5.5, θ ≤ 15° or ≥ 165°) and the high post (other post at r 3.8–5.2, θ 70–110°) for ≥ 60% of set time, vacated and re-filled by the opposite post on each side change | none (The Hoops Geek); "Toledo" = University of Toledo is **unverified** `[Z:THG23]` |
| **Fraschilla "play opposite the ball" 2-on-1 vs the 2-3 bump-out** | F11.6 | — | short-corner arriver; flasher | when the back-side forward bumps out to help the guard on his side, a teammate runs to the short corner for a 2-on-1 against that forward; also flash middle behind the zone and screen the back of the zone. Claim: 70% of shots from one side rebound to the opposite side → position weak-side rebounders (original evidence not given) | — | weak-side forward defender's y rises ≥ 2 m (bump-out, cf. defense_full F8.1 on-and-off) and within 1.0 s an attacker arrives at the same-side short corner (r 3.5–5.5, θ ≤ 15° or ≥ 165°) behind him; the 70% claim is testable from project data | none (ESPN "Hoops 101", Fran Fraschilla, Jan 2003) `[Z:ESPNFR]` |
| **"Baseline Overload – 'Kentucky'"** (vs 2-3 / 3-2) | F11.10 | O1 top; O3 wing; O2 slot between guard and wing defenders; O4 low; O5 low | O4 baseline sprinter; O3 curler/mid-post flasher; O5 sealer; O1 gap dribbler | O1→O3→O1; O1 gap-dribbles and reverses to O2; O4 sprints to the opposite corner; O3 curls off O5 and flashes to the mid-post (≤ 1.5 s after the reversal); O5 seals the middle defender; primary O3's curl; corner three if the zone does not shift; O1 floats to the back side | zone shifts in time | a big's BASELINE_RUN to the opposite corner during a reversal; a wing curling off a sealing big into the mid-post (r 2.5–4, θ 30–60° or 120–150°) ≤ 1.5 s after the reversal pass | "Kentucky" in the title only — UK attribution **unverified** (contributor Matt Hackenberg, 14 Dec 2021) `[Z:FMKY]`; confidence low |
| **Loyola Chicago "Zone Offense Double Cut"** | F11.4 | O1 top; O2 wing; O3 opposite wing; O4 following O1; O5 low | O1 and O4 consecutive cutters (O4 stops in the short corner); O5 middle flasher | O1→O2 and O1 cuts through to the weak wing; O4 follows O1 but stops in the short corner (≤ 1.5 s behind); O2→O3; O5 flashes into the middle and passes to O4 or kicks to O1 depending on X3 | X3 reads correctly | two consecutive cutters through the lane (second ≤ 1.5 s after the first, similar path), the second stopping at the weak short corner; a middle FLASH by the 5 on the next pass; then 5→short corner or 5→wing | Loyola Chicago (page 27 Mar 2021; 2020-21 likely, **unverified**) `[Z:FMLUC]`; confidence low-medium |

#### A7.12 4-Out "Corners" patterned version and named hitters (Larry, Curly, Mo, Stack, Star, Weak, Wing Flash) — RICHER (extends F11.2 "Corners")
- **Name and aliases:** Corners; Corners 52; hitters Larry, Curly, Mo, Stack, Star (Mark Lane), Weak, Wing Flash.
- **Family / sub-family:** F11.5 system / F11.4 hitters.
- **Start alignment `[Z:CC41]`:** 4-out: O1 and O2 at the slots ≈ (7.5, 70)/(7.5, 110); O3 and O4 in the wing-corner areas; O5 post.
- **Roles:** four perimeter passers/cutters; O5 post who moves with the ball.
- **Ordered actions / rules `[Z:CC41]`:** quick reversal and skip passing; **the post moves with the ball** (ball at the top → O5 at the ball-side elbow; ball on a low wing or in a corner → O5 at the ball-side low post); if the high-post pass is denied, O3 and O4 back-cut; vs 1-2-2, O5 seeks the high post or middle of the paint; vs 1-3-1 the low post is easier; vs 2-3, O5 seeks the FT line or the gap below the elbows and dives when the low outside defender comes out. Hitters: **Larry** — pass to the corner pulls the low outside defender; the corner dribbles up to the FT-line extended; the passer cuts to the ball-side corner for a return three. **Curly** — O3 pin-screens X1 (denying the high post) and O1 dribbles around for a pull-up or a kick to the corner. **Mo** — O1 dribbles right to engage X1; O5 to the left wing; O3 steps to the top, catches, swings to O5; if X3 closes, O5 finds O4 in the corner and O3 dives. **Star** — O4 pin-screens X2 at the top left and O1 dribbles around into the gap. **Weak** — Star with the screen from the weak block. **Stack** — O3 and O5 double-screen X4 while O2 cuts to the corner, then O5 screens X5 and O3 cuts to the slot. **Wing Flash** — O3 flashes to the ball-side elbow, O5 cuts under to the short corner and catches from the corner, and O3 dives for a dump. Timing [HEURISTIC]: hitters within 2–5 s of the first pass.
- **Usual counters:** deny the high post; switch to a match-up.
- **Detection signature [HEURISTIC]:** 4-out shape (4 at r ≥ 6.5) with one interior player tracking the ball: corr(sign x_O5, sign x_ball) ≥ 0.8 and O5 at r 3.8–5.2 when the ball is at θ 70–110° and at r < 2.5 when the ball is at θ < 30° or > 150°. **Star/Weak** = a big's ZONE_SCREEN on a top defender with the handler dribbling around it into the gap (GAP_DRIVE starting within 1.5 m of the screener). **Larry** = corner catch → dribble up (corner → wing ≥ 2 m) → the original passer cuts to the same corner → return pass ("corner exchange").
- **Teams documented:** none (Coach's Clipboard; Mark Lane) `[Z:CC41]`; "Corners 52" also `[Z:CC23P]`.
- **Sources:** `[Z:CC41][Z:CC23P]`.
- **Confidence:** medium (pattern).

#### A7.13 Zone-2 "Runner" offence: rule set and plays "Back", "Middle cut", "Back – Skip", "Flex" — RICHER (extends F11.2 "Zone-2 runner", "45")
- **Name and aliases:** Zone-2; runner offence; "45"/"54"; Back; Middle cut; Back – Skip; Flex.
- **Family / sub-family:** F11.9 (vs 1-2-2/1-3-1; also packed 2-3 and box-and-1).
- **Start alignment `[Z:CC122]` [spots HEURISTIC]:** 2-out 2-in: O1 (7.5, 110) and O3 (7.5, 70) flank X1; O4 (2.5, 135) and O5 (2.5, 45) just above the blocks; O2 (best shooter) is the runner, in a corner (6.76, 2.5).
- **Roles:** runner (O2); two guards; two posts (flash/screen).
- **Ordered actions / rules `[Z:CC122]`:** O2 always runs ball-side corner to corner; with the ball on top the opposite post flashes middle; on a pass to the corner he returns to the opposite block to rebound; after O2 has hit a couple of corner shots the low outside defender runs out early, so the guard fakes the corner pass and feeds the post. "45"/"54": pass to the corner; O4 screens X5 (vs 2-3, the middle low defender) and O5 cuts ball side. Back: O2 starts the run, then returns. Middle cut: O2 cuts into the open paint for a turnaround. Back – Skip: pass to the opposite wing, O2 fakes the run and returns, O5 back-screens the outside low defender, and the wing skips to O2. Flex: reversal, then O5 screens for O2, who flex-cuts into the paint. Timing [HEURISTIC]: a corner-to-corner run (≈ 13.5 m) takes 2.5–3.5 s at 4–5 m/s; the fake-then-feed window opens after ≥ 2 corner catches in the game (game-state trigger).
- **Usual counters:** the low outside defender runs out early (answered by the post feed).
- **Detection signature [HEURISTIC]:** repeated BASELINE_RUNs by the same player (≥ 2 per possession) whose side matches sign(x_ball) within 1.0 s; **Back** = a run aborted after ≤ 3 m with a return to the origin corner; **Middle cut** = the runner turns up into r < 3, θ 60–120°; a post flash to the high post whenever the ball is at θ 80–100°.
- **Teams documented:** none (Coach's Clipboard) `[Z:CC122]`; MSU "Special-2" baseline runner (`[S12]`, F11.1) is the MSU analogue.
- **Sources:** `[Z:CC122]`.
- **Confidence:** medium.

#### A7.14 "Gap Attack" zone offence (Brad Brownell, Clemson) — NEW (F11.5 / F11.4)
- **Name and aliases:** Gap Attack Zone Offense.
- **Family / sub-family:** F11.5 / F11.4 (vs 2-3).
- **Start alignment [HEURISTIC]:** 1-2-2 / 3-out 2-in: O1 top (7.5, 90); O2, O3 wings; O4, O5 low.
- **Roles:** O1 distort dribbler then reset; O2 shallow cutter then flare/skip target; O1 and O4 back-side pinners; O3 skip passer; O5 elbow flasher.
- **Ordered actions `[Z:CCGAP]` [timing HEURISTIC]:** (1) distort: O1 dribbles to the right wing while O2 shallow-cuts to the top (0–1.5 s); (2) reverse O1→O2→O3 (1.5–3.5 s); (3) O1 and O4 back-screen the zone (back-side double pin) while O2 flare-cuts to the right wing (3–4.5 s); (4) O3 skips to O2 (4–5.5 s); (5) O1 resets to the top. Options: O4 seals X5 and posts if a back-to-basket big; otherwise O4 to the short corner and O5 flashes to the ball-side elbow, then short corner → elbow → weak corner (O3 slides there).
- **Usual counters:** the zone does not over-shift on the reversal; the weak forward splits the flare and the pins.
- **Detection signature [HEURISTIC]:** dribble entry to the wing with a shallow cut (the wing moves toward the top ≥ 3 m as the dribbler arrives); two back-side ZONE_SCREENs (pins) on the weak-side defenders within 0.8 s; a flare (the receiver moves outward ≥ 2 m away from the screens); then a SKIP to the flaring player.
- **Teams documented:** Clemson (Brownell), DVD "Gap Attack Zone Offense"; season not given `[Z:CCGAP]`.
- **Sources:** `[Z:CCGAP]`.
- **Confidence:** medium.

#### A7.15 Dribble-drive zone attack (Walberg/Calipari DDM, zone version) — NEW (F11.5; links F10)
- **Name and aliases:** DDM vs zone; "4-out zone dribble-drive".
- **Family / sub-family:** F11.5 (links F10 spread/drive-and-kick; F4.2 "Dribble-drive motion").
- **Start alignment `[Z:CCDDZ]`:** 4-out, no high post: O1 and O4 at the top; O2 and O3 on the wings (higher vs a 2-3) or in the corners (vs 1-2-2/3-2); O5 inside or away from the ball; six perimeter spots (four wing/top, two corners).
- **Roles:** gap driver; safety pitch-back filler; kick targets; O5 sealer/pinner.
- **Ordered actions / rules `[Z:CCDDZ]`:** O1 attacks the gap between the two top defenders; from the wing the dribbler attacks the elbow; a dribble into the elbow or lane counts as a "post touch"; vs a 2-3 the driver usually cannot reach the rim, so he pulls up, kicks or dumps; avoid the baseline drive vs a 2-3 except after a wing-to-wing skip (usable vs 1-2-2/3-2); the safety pitch-back player fills behind the dribbler; kick options: open shooter, opposite wing, post seal, pitch-back; O5 seals low defenders or pins the outside low defender for a skip to the corner; on a top-to-wing pass the passer cuts through and the others rotate; on a wing/corner shot the opposite wing crashes; not recommended vs a 1-3-1 (use Zone-2). Timing [HEURISTIC]: kick ≤ 1.0 s after the deepest point of the drive.
- **Usual counters:** pack the gaps; 1-3-1 (stated).
- **Detection signature [HEURISTIC]:** 4-out shape with nobody at the high post (r 3.5–5, θ 70–110°) for ≥ 70% of set time; GAP_DRIVEs ending at r 3–5 at the elbow or lane with a kick ≤ 1.0 s later; a teammate 3–5 m behind the driver (pitch-back position) at the drive's deepest point; cut-through-and-fill after top → wing passes.
- **Teams documented:** concept credited to Walberg (Pepperdine; **unverified**) and Calipari; zone version from Jerry Petitgoue (Cuba City HS, Wisconsin); no specific college zone usage on the page `[Z:CCDDZ]`.
- **Sources:** `[Z:CCDDZ]`.
- **Confidence:** medium (rules); low (college usage).

#### A7.16 Sonny Smith's zone-attack rules (saddle dribble, "dribble at, run away", post cross, diagonal) — NEW (F11.6 principles beyond F11.1)
- **Name and aliases:** Sonny Smith's ten zone-attack rules.
- **Family / sub-family:** F11.6 principles.
- **Start alignment:** any.
- **Roles:** gap dribbler; posts; cutters; man behind the zone.
- **Ordered actions / rules `[Z:CTSS]`:** **gap rule** — get between a baseline and a wing defender, dribbling at one defender's shoulder (the "saddle dribble") so you face only one; **screening rule** — choose interior vs perimeter screening (Smith screens the interior more); **dribble rule** — "if I dribble toward you, you run away from me", while the player behind follows for a throw-back; **flash/duck-in rule** — from the front, interior or back of the zone; **cutter rule** — cut strong to weak, not weak to strong; **step-out rule** — step posts to the high post to help reversal; **post-cross rule** — with the ball on the wing, posts cross, the second off the first's hip; **man-behind-the-zone rule** — stand one (Smith prefers the short corner) or cut one; **fake a pass to make a pass**; **diagonal rule** — diagonal cuts and passes.
- **Usual counters:** —
- **Detection signature [HEURISTIC]:** **saddle dribble** = a GAP_DRIVE whose heading points within 0.5 m of one defender's shoulder (nearer defender's position offset ± 0.4 m laterally) rather than the gap midpoint, ending < 1.2 m laterally from that defender; **dribble-at/run-away** = DRIBBLE_AT; **post cross** = with the ball at θ < 60° or > 120°, two bigs' paths intersect inside the lane within 2 s, the second passing within 1.0 m of the first; **strong-to-weak cut** = cutter starts with sign(x) of the ball and ends opposite (track the strong→weak vs weak→strong ratio).
- **Teams documented:** Sonny Smith (former Auburn head coach) via Coaching Toolbox, 2010; no season-specific usage `[Z:CTSS]`.
- **Sources:** `[Z:CTSS]`.
- **Confidence:** medium (principles).

#### A7.17 Baylor "Inside Ball Screen" vs 2-3 (with weak-side triangulation) — NEW (F11.4; F5 interplay)
- **Name and aliases:** Inside Ball Screen (Baylor).
- **Family / sub-family:** F11.4 / ball screen vs zone.
- **Start alignment [HEURISTIC]:** O1 at the top or slot; O4 screener; O3 high wing ≈ (7.2, 55); O2 weak corner; O5 weak-side post (triangulated with O2 and O3 against X3).
- **Roles:** O1 handler (split or kick); O4 inside screener (pop/short roll); O3 high-wing kick target; O2 corner "one more"; O5 duck-in.
- **Ordered actions `[Z:FMBIBS]` [timing HEURISTIC]:** (1) O4 sets an **inside** ball screen for O1, spacing lets O1 split the guards (0–1 s); (2) X2 seals the gap and X3 stays flat, so O1 kicks to O3 at the high wing (≤ 1.5 s after the screen). Reads: O5 ducks hard on X5 (if fronted, triangulation is lost); X3 flies out to O3 → "one more" to O2 in the corner (shoot, drive or enter to O5); X3 takes the high wing → O1 corner-skips to O2 and O5 ducks in; O4 pops or short-rolls into the zone's soft spot. Duck-in onset within 0.5 s of the kick.
- **Usual counters:** X2 seals the gap and X3 stays home; the zone switches the screen.
- **Detection signature [HEURISTIC]:** a slot/top ball screen with the screener on the inside (screener's x closer to 0 than the handler's) and the handler splitting the two top defenders (both within 2.5 m) or turning away; weak-side triangle occupied at the screen moment — wing (r 6.8–7.5, θ 120–150°), corner (θ > 168°) and post (r 2–3.5, θ 120–160°); a post duck-in within 0.5 s of a kick to the wing.
- **Teams documented:** Baylor 2018-19 zone offence (Radius Athletics breakdown, 20 Mar 2019) `[Z:FMBIBS]`.
- **Sources:** `[Z:FMBIBS]`.
- **Confidence:** medium.

#### A7.18 Baylor "Pull" and "Rub" vs a match-up 2-3 — NEW (F11.7)
- **Name and aliases:** Pull; Rub (vs match-up zone).
- **Family / sub-family:** F11.7 (vs defense_full F8.3 match-up).
- **Start alignment `[Z:FMBRUB][Z:FMBPULL]`:** 3-out 2-in with both bigs behind the back line of the zone (y < 0.5).
- **Roles:** Pull: opposite guard middle flasher; handler dribbling to the top; wing shooter. Rub: ball-side low post flasher near the elbow; opposite wing to the weak corner; low big screens for the high big, who slices.
- **Ordered actions:** Pull: swing to one side; the opposite guard flashes to an open middle spot and catches; the handler dribbles to the top of the key, pulling the paint defender and confusing the top two; pass to the open wing shooter. Rub: swing; the ball-side low post flashes near the elbow and the opposite wing slides to the weak corner; a dribble to the top pulls a defender up and the ball rotates across the top; the high post draws the middle defender; as the ball swings to the opposite slot, the low big screens for the high big, who slices through the lane to catch. Timing [HEURISTIC]: slice within 1.5 s of the swing.
- **Usual counters:** match-up defenders hand off cleanly.
- **Detection signature [HEURISTIC]:** two bigs at y < 0.5 behind the back-line defenders (offensive y < defender y) at the set; **Pull** = guard FLASH into the middle (r 4–6, θ 70–110°), then the handler's dribble to the top, with the nearest zone defender's y rising ≥ 1.0 m; **Rub** = a big-to-big SCREEN (low screens for high) during a slot-to-slot swing, with the high big cutting from r 4–5 through the lane to r < 2.5 within 1.5 s.
- **Teams documented:** Baylor, 2019 NCAA Tournament vs Syracuse ("get a 2"; pages 10 Apr 2019) `[Z:FMBRUB][Z:FMBPULL]`.
- **Sources:** `[Z:FMBRUB][Z:FMBPULL]`.
- **Confidence:** medium.

#### A7.19 Oregon "Zone 32" (Altman: posts in the short corners, three guards free) — NEW (F11.5)
- **Name and aliases:** Zone 32.
- **Family / sub-family:** F11.5.
- **Start alignment `[Z:FMORE32]` [spots HEURISTIC]:** both posts low in the short corners (4.51, 3.8)/(4.51, 176.2); three guards across the top (7.5, 90) and wings (7.2, 45)/(7.2, 135), one rotating into the high post (4.19, 90).
- **Roles:** two short-corner posts; three interchanging guards.
- **Ordered actions `[Z:FMORE32]`:** the three guards exchange positions by cuts or dribbles; a guard rotates into the high post. Timing [HEURISTIC]: ≥ 2 exchanges per possession.
- **Usual counters:** —
- **Detection signature [HEURISTIC]:** both bigs in the short-corner region (r 3.5–5.5, θ ≤ 15° or ≥ 165°) for ≥ 60% of the possession; a guard at the high post ≥ 1 time per possession; guard-guard exchanges (paths crossing above r 4) ≥ 2 per possession.
- **Teams documented:** Oregon (Altman), FastModel 23 Mar 2016 (season not given) `[Z:FMORE32]` — Oregon is a Big Ten member since 2024-25; this is [pre-window].
- **Sources:** `[Z:FMORE32]`.
- **Confidence:** medium.

#### A7.20 Michigan (Beilein) "Michigan X" and "Michigan Hand"; 2013 Final Four high-post approach vs Syracuse — NEW (F11.4 / F11.6; Big Ten)
- **Name and aliases:** Michigan X; Michigan Hand; high-post playmaker vs 2-3.
- **Family / sub-family:** F11.4 (zone type not stated for X/Hand); F11.6 high-post playmaker.
- **Start alignment [HEURISTIC]:** O1 top (7.5, 90); O2, O3 wings; O4, O5 low (rising up the lane for X).
- **Roles:** X: O4/O5 rising zone screeners on the ball-side top and bottom outside defenders; O3 shooter/driver. Hand: O2 short-corner cutter; O4 ball screener who pops; O5 posting the middle defender.
- **Ordered actions `[Z:CTBEIL][Z:UMH13]`:** Michigan X: O1→O2; O4 and O5 move up the lane; O2→O1; as O1 swings to O3, O5 screens the bottom outside defender and O4 screens the top outside defender; O3 shoots a pull-up three or drives. Michigan Hand: O1→O2; O2 passes back and cuts to the short corner; O4 comes up to ball-screen for O1 and pops; O1→O4; reads — bottom outside steps out to O4 → O2 shoots; top outside takes O4 and bottom covers O2 → O4 to O5 posting the middle defender; or skip to O3. 2013 Final Four vs Syracuse's 2-3 (6 Apr 2013): Michigan got the ball to the middle; McGary caught at the FT line and found Albrecht on the baseline after Triche committed; McGary's FT-line jumper forced the zone to respect him and opened baseline cuts; Burke ran a pick-and-pop at the top on Carter-Williams; Syracuse answered with traps at the arc late. Timing [HEURISTIC]: shot/drive ≤ 1.5 s after the catch.
- **Usual counters:** traps at the arc (Syracuse, late).
- **Detection signature [HEURISTIC]:** **Michigan X** = two bigs rise from r < 2 to r 4–6 together, then set simultaneous ZONE_SCREENs on the top and bottom outside defenders of the ball side during a swing pass, and the receiver shoots or drives ≤ 1.5 s after the catch; **Hand** = a passer cuts to the short corner (r 3.5–5.5, θ < 15° or > 165°) after a return pass, then a big ball-screens and pops (ends r ≥ 6.5); **high-post playmaker** = a big catches at r 3.5–5, θ 70–110° and makes the next pass to the baseline (y < 1) or a corner within 1.5 s (count high-post-originated assists).
- **Teams documented:** Michigan (Beilein), playbook sets (season not given) `[Z:CTBEIL]`; Michigan vs Syracuse, 2012-13 Final Four `[Z:UMH13]` [pre-window].
- **Sources:** `[Z:CTBEIL][Z:UMH13]`.
- **Confidence:** medium.

#### A7.21 Pete Gillen's match-up-zone attack ("screen the wings", "screen the point", block screen → box overload, duck-in seal-back) — NEW (F11.7)
- **Name and aliases:** Gillen match-up attack.
- **Family / sub-family:** F11.7 (vs F8.3).
- **Start alignment [HEURISTIC]:** 1-2-2 or 2-1-2 spread with cutters.
- **Roles:** point dribbler; wings who fade; 4 and 5 screeners/rollers/duck-in posts.
- **Ordered actions / rules `[Z:CTGIL]`:** attacking the match-up is "80% mental"; act, don't react. (1) Fast break. (2) Send cutters through — standing still helps the match-up. (3) Attack the baseline and reverse to the other baseline; with the ball on the baseline all zones become 2-3s. (4) Dribble penetration after stretching with passes (citing Don Casey). (5) **Screen the wings:** the point dribbles at a wing, who fades to the corner; on a corner pass the 5 rolls and the 4 fills the high post for a 2v1; on a pass back, reverse to the 3. (6) **Screen the point:** 1→2 and the 4 screens for the point; 4–1 screen-and-roll while the 3 fades to the baseline, giving 3/5 high-low. (7) **Screen in the block area:** on reversal the 4 screens the back of the zone and ducks in; the wing dribbles to the corner and the 5 back-picks to create a box overload (ball path 2-1-3-2-5). (8) Skip only after a ball fake. (9) Four on the offensive glass. (10) **Duck-in / seal-back:** after 1→2→1 the 5 moves along the baseline then ducks in; if not open, the 3 dribbles hard to the baseline and bounce-passes to the 5 (ball path 1-2-1-3-5).
- **Usual counters:** match-up defenders hand off cutters at region boundaries.
- **Detection signature [HEURISTIC]:** vs a defence labelled match-up (F8.3): through-cuts (a cutter crossing x = 0 at r < 4) ≥ 1 per possession; "baseline attack then reverse" = the ball at y < 1.5 on one side, then within 4 s at y < 1.5 on the opposite side; offensive rebounders in the paint at the release ≥ 4 (F14); the pass fake needs pose (not measurable from XY).
- **Teams documented:** Pete Gillen clinic notes (Gillen coached Xavier, Providence and Virginia — general knowledge, **unverified**); no team/season usage given `[Z:CTGIL]`.
- **Sources:** `[Z:CTGIL]`.
- **Confidence:** medium.

#### A7.22 Overload sets by programme (Wes Kosel compilation) — NEW (F11.10; titles + one-line descriptions)
- **Name and aliases:** Green Bay "Zone Shallow Overload"; Gonzaga "Zone Overload Slot Screen"; Oklahoma "Zone Overload Pick & Pop"; Fairleigh Dickinson "Zone Overload Ball Screen"; Texas "Zone Overload".
- **Family / sub-family:** F11.10 overload sets (vs 2-3).
- **Start alignment `[Z:HSOVL]`:** players in the corner, on the block, in the slot and on the wing on one side, so the bottom defender must pick between wing and corner.
- **Roles / ordered actions `[Z:HSOVL]`:** Green Bay — overloads the left side and forces X4 to pick wing or corner. Gonzaga — after a right-side overload, the 5 screens the top zone defender so X2 must stop the ball or guard the wing. Oklahoma — weak-side ball screen and pop as the zone shifts. Fairleigh Dickinson — slot ball screen for a left-corner shot. Texas — the 5 posts the middle defender so X4 guards two. (Diagrams not read.)
- **Usual counters:** zone rotates the weak-side guard down.
- **Detection signature [HEURISTIC]:** OVERLOAD_STATE ≥ 1.0 s with corner (θ < 12°), block (r < 2.5), wing (θ 25–60°) and slot (θ 60–80°) occupied on one side; sub-labels: + ZONE_SCREEN on a top defender (slot screen); + weak-side ball screen with the screener popping (pick-and-pop); + slot ball screen; + SEAL on X5 (post the middle).
- **Teams documented:** Green Bay, Gonzaga, Oklahoma, Fairleigh Dickinson, Texas (seasons not given; article 31 Aug 2016) `[Z:HSOVL]`.
- **Sources:** `[Z:HSOVL]`.
- **Confidence:** low-medium (titles only).

**Zone items left out as unverified:** Duke vs Syracuse 2019 high-post plan (Duke Basketball Report and Duke Chronicle returned 403) and Pitt (Jamie Dixon) vs the Syracuse 2-3 (pages not opened; Breakthrough "Pitt" play 403) — not catalogued until a page opens.

### A8. F12 Press offense / press break: new breaks, half-court trap breakers, principles (extends 12.1–12.2)

Proposed sub-families: **F12.3 vs full-court man (inbound-denial breaks)**, **F12.4 vs zone presses (1-2-1-1, 2-2-1, 1-2-2, 1-3-1)**, **F12.5 vs half-court traps (3-1-1, 2-2-1, 3-2, 2-1-2, 1-3-1, 1-1-2-1, 1-2-1-1)**, **F12.6 end-of-game get-it-in sets**, **F12.7 press-break principles**, **F12.8 MSU press-break evidence**. Defensive counterparts: defense_full F9.1 (full-court man), F9.2 (zone presses), F9.3 (match-up / run-and-jump), F9.4 (half-court traps), F9.5 (programme systems).

**Full-court frame (attacked rim at the origin):** half-court y = 12.73 m; own (defended) rim y ≈ 25.47 m; far baseline y ≈ 27.05 m. Spots: inbounder out of bounds right/left of the lane (x ±2.5, y 27.6) = (27.71, 84.8)/(27.71, 95.2); backcourt block (24.67, 85.7)/(24.67, 94.3); backcourt "volleyball" corner (x ±6.7, y 26.5) = (27.33, 75.8)/(27.33, 104.2); backcourt elbow (21.36, 85.1)/(21.36, 94.9); backcourt FT-line extended at the sideline (22.25, 73.0)/(22.25, 107.0); backcourt top of the key (18.60, 90); backcourt sideline mid (18.31, 68.2)/(18.31, 111.8); half-court sideline, backcourt side (15.12, 63.3)/(15.12, 116.7); half-court middle, backcourt side (13.50, 90); half-court sideline, frontcourt side (13.62, 60.0)/(13.62, 120.0); frontcourt FT-line extended at the sideline (7.73, 32.8)/(7.73, 147.2); deep in front of the rim (1.00, 90).

**Press primitives [HEURISTIC]:** `INBOUND` t0 = ball through the net (made FG/FT) or the official's handover; Δt_in = release − t0. The 5-s throw-in, 10-s backcourt and run-the-end-line rules are confirmed from the NCAA rules text in A6.1 (R1, R3, R7) `[Q1]` (the zone/press note itself had marked them unverified). `TRAP` = two defenders within 2.0 m of the handler for ≥ 0.5 s. `GO_ROUTE` = sprint ≥ 5 m/s for ≥ 1.5 s toward the attacked rim; `LONG_PASS` ≥ 15 m in the air. `BACKCOURT_REVERSAL` = a pass with Δy > +1 m or a sign change in x while the ball is at y > 12.73. **Timing frame [HEURISTIC]:** inbound release ≤ 2.0 s after a make (existing F12.1 principle); first backcourt pass ≤ 2.5 s after the catch; cross half-court within 4–8 s of t0; "attack" = shot within 4 s of crossing (F12.1).

#### A8.1 MSU press-break evidence ("special teams") — RICHER (replaces nothing; adds the only documented evidence to F12.2 "MSU press break [UNVERIFIED]")
- **Name and aliases:** MSU press breakers; "special teams" (MSU term).
- **Family / sub-family:** F12.8.
- **Start alignment / roles / ordered actions:** not documented. In the 2024 NCAA first-round win over Mississippi State (21 Mar 2024), Mississippi State went to a half-court trap in the second half that forced two early MSU turnovers; Tyson Walker: "We always go over our press breakers" and "We call it special teams", describing preparation and "knowing where you're supposed to be" `[Z:CBS24]`. 2025-26: Fears "controlled the ball against the Razorbacks' full-court pressure" (8 Nov 2025) — ball-handling, not a structure `[M12]`. Spartan Avenue (2022) snippets about late-game inbound struggles vs Portland and Maryland — **unverified** (not opened).
- **Usual counters:** half-court trap (defense_full F9.4).
- **Detection signature [HEURISTIC]:** tag MSU possessions after opponent half-court traps (F9.4) and log turnovers ≤ 4 s after trap onset.
- **Teams documented:** MSU 2023-24 `[Z:CBS24]`; MSU 2025-26 `[M12]`.
- **Sources:** `[Z:CBS24][M12]`.
- **Confidence:** high for the quote; MSU press-break structure still **unverified**.

#### A8.2 Man-press sets "Side", "Line 321", "Shuffle", "Big 5" (Joao Costa) — NEW (F12.3)
- **Name and aliases:** Side; Line 321; Shuffle; Big 5.
- **Family / sub-family:** F12.3 (vs F9.1 full-court man; also match-up presses, which become man after the first pass or dribble).
- **Start alignment [HEURISTIC]:** inbounder (27.71, 84.8); receivers between the backcourt FT line and the block — elbows (21.36, 85.1)/(21.36, 94.9), block (24.67, 85.7); big at the backcourt elbow.
- **Roles:** 1, 2 and 3 are interchangeable handlers `[Z:CCM2M]`.
- **Ordered actions `[Z:CCM2M]`:** **Side:** 4 inbounds; 5 near the elbow; 3 breaks to the ball-side wing; 2 screens 1's defender, then comes to the ball; 1 cuts to the baseline; inbound to 3, 2 or 1; 3 dribbles up with 2 and 1 in the lanes, 4 trails, 5 goes elbow → opposite low post; 3 and 5 screen for 2, 4 cuts to the basket. **Line 321:** 5 inbounds; 3 breaks to the ball-side wing; 1 cuts to the opposite short corner off 2's screen; 2 seals 1's defender at the baseline and shows to 5; 1 brings it up, 2 and 3 fill the lanes, 4 to the left block, 5 trails; then 5 screens for 2 and rolls. **Shuffle:** 4 inbounds; 3 screens for 1; 2 screens for 3, then rolls toward 4; 2 dribbles up, 1 and 3 fill, 5 to the top of the key, 4 trails; 5 down-screens for 4, and 4 at the elbow looks high-low to 5. **Big 5:** 1 inbounds from the sideline; 3 screens for 2 and goes to the weak corner; 2 to the ball-side corner; 5 cuts to 1, catches and hands back to 1 (inbounder return); 4 at the elbow; 1→2, 2 hands back to 1, 4 screens for 3, and 1 drives. Timing [HEURISTIC]: first screen within 1.5 s of t0.
- **Usual counters:** switch every screen (then the screener seals and shows); face-guard with a centrefielder (F9.1 "41 Deny").
- **Detection signature [HEURISTIC]:** INBOUND with ≥ 1 backcourt SCREEN within 1.5 s of t0 (screener ≤ 0.3 m/s ≥ 0.5 s within 1.2 m of a receiver's path at y 20–26.5). **Line 321** = a receiver cuts to the backcourt short corner (\|x\| 3.5–5.5, y 25–26.5) with a teammate's screen and seal. **Big 5 / Shuffle** = the inbounder receives a return pass in bounds ≤ 3 s after t0 via a hand-off; then two players sprint the sidelines (\|x\| ≥ 5.5, Δy ≤ −8 m in ≤ 3 s) and the inbounder trails (y_inbounder − y_ball = 2–6 m).
- **Teams documented:** none (Costa, ex-European pro, US and international coach) `[Z:CCM2M]`.
- **Sources:** `[Z:CCM2M]`.
- **Confidence:** medium.

#### A8.3 "3-Up" press break (triangle) — NEW (F12.3 / F12.4)
- **Name and aliases:** 3-Up press break.
- **Family / sub-family:** F12.3 / F12.4 (vs PG denial, and vs presses that let the PG catch and then trap).
- **Start alignment `[Z:CC3UP]` [spots HEURISTIC]:** O1 and O2 start at the elbows and split wide to (22.25, 73.0)/(22.25, 107.0); O3 sprints up the middle as the triangle point (18.6, 90); O4 inbounds (27.71, 84.8) and stays behind the ball; O5 deep (1.0, 90).
- **Roles:** O3 triangle point / middle receiver; O1, O2 sideline runners; O4 inbounder-safety; O5 deep.
- **Ordered actions `[Z:CC3UP]`:** **Denial:** O4 looks to O3 in the middle; if O3 catches, O1 and O2 run the sidelines; if O3 is denied, O1, O2 and O3 take their men to the end line (y ≈ 26) and back-cut for a long (not short) lob. **PG trap:** O1 catches; O3 cuts diagonally for a pass, then speed-dribbles to attack with O5; if O3 is not open, O3 runs the right sideline and O2 cuts diagonally, then locates in the middle; O4 stays behind the ball for the pass back; if the trap is loose, O1 splits it or speed-dribbles the sideline, watching for a second trap near half-court. Timing [HEURISTIC]: walk-down and back-cut 1.5–3 s, inside the 5-s limit (R1).
- **Usual counters:** deny the middle and stay deep.
- **Detection signature [HEURISTIC]:** at t0 two players at \|x\| 4–6.5, y 20–22 and one at x ≈ 0, y 17–20 (triangle); a middle catch at \|x\| < 3 → two sideline sprints; or the denial pattern — all three front receivers move toward the inbounder's baseline (Δy ≥ +3 m), then reverse sharply (> 150° within 0.5 s) → LONG_PASS ≥ 15 m; trailing safety = the inbounder at y > y_ball for ≥ 80% of backcourt time.
- **Teams documented:** none (Coach's Clipboard) `[Z:CC3UP]`.
- **Sources:** `[Z:CC3UP]`.
- **Confidence:** medium.

#### A8.4 "Flood" press break (Bob Hurley Sr.) — NEW (F12.4)
- **Name and aliases:** Flood.
- **Family / sub-family:** F12.4 (vs 1-2-1-1 or 1-2-2 full court, especially denial or first-pass traps).
- **Start alignment `[Z:CCFLOOD]` [spots HEURISTIC]:** guards O1/O2 at the backcourt elbows (21.36, 85.1)/(21.36, 94.9); posts O4/O5 wide at half-court (15.12, 63.3)/(15.12, 116.7); O3 inbounds.
- **Roles:** O2 go-route decoy; O1 sideline-and-hook middle receiver; O4/O5 come-back receivers; O3 inbounder-safety.
- **Ordered actions `[Z:CCFLOOD]`:** O2 sprints all the way to the basket (pulls X2 deep); O1 sprints up the right sideline, turns at half-court and cuts back hard to the middle near the arc; O4 and O5 sprint from half-court back to the backcourt three-point-arc areas (not the elbows or paint); O3 inbounds, avoiding a short pass vs the 1-2-1-1 (the long pass to O2 is mainly a decoy). Primary: O4 or O5 catches and hits O1 in the middle, who speed-dribbles; alternate O3→O1 directly; O3 stays below the ball. Timing [HEURISTIC]: O2's go route ≈ 20 m in 3–4 s; O4/O5 come back ≈ 7–9 m in ≤ 2 s; middle catch 2–4 s after t0.
- **Usual counters:** front the come-back receivers.
- **Detection signature [HEURISTIC]:** at t0 the two guards at the backcourt elbows and the two bigs at the half-court sidelines; within 2 s the bigs move toward the inbounder (Δy ≥ +6 m) to the backcourt arc (6.5–7.5 m from the own rim), one guard runs a GO_ROUTE (to y < 5) and the other's path goes up the sideline and hooks back to \|x\| < 3 at y 13–16; the first or second pass ends in the middle (\|x\| < 3).
- **Teams documented:** Bob Hurley Sr. (St. Anthony HS, NJ — affiliation not stated on the page, **unverified**); no college team `[Z:CCFLOOD]`.
- **Sources:** `[Z:CCFLOOD]`.
- **Confidence:** medium.

#### A8.5 Half-court press breakers by trap type — NEW (F12.5)
- **Name and aliases:** half-court trap breakers vs 3-1-1, 2-2-1 ("tight end"), 3-2, 2-1-2, 1-3-1, 1-1-2-1, 1-2-1-1; "tall-passer" tip.
- **Family / sub-family:** F12.5 (vs F9.4 half-court traps and F9.2 relatives).
- **Start alignment [HEURISTIC]:** tight end at x 0, y 14–16 (backcourt-side middle); frontcourt corners (6.71, 2.6)/(6.71, 177.4); deep receiver (1.0, 90).
- **Roles:** ball-handler who draws two; tight end (middle receiver); sideline receivers; deep holder.
- **Ordered actions `[Z:CCHCPB]`:** **vs 3-1-1:** O3 and O4 on the sidelines near the top of the key extended; one receiver deep to hold X5; O2 slides to the sideline beyond X2; O1 dribbles to draw two and passes just before the trap; if X3 shifts, O4 cuts into the middle for a 2v1 with O5. **vs 2-2-1:** a tall "tight end" in the middle between the second-tier defenders, O3 and O5 in the corners; O1 attacks the middle, then passes middle or to a corner; variation: O2 sets an outside screen on X2 and O1 dribbles up the right sideline, hitting O5 in the corner for a 2v1 with O3 vs X5. **vs 3-2:** tight end (O4) in the middle, ball-side wing on the sideline, a tall receiver deep (turns the 3-2 into a 3-1-1). **vs 2-1-2:** "put players where they ain't"; O1 does not dribble into the trap but draws two and passes to the side; if X4 covers O2, O4 is open in the corner and O5 cuts to the paint; if X3 cheats, O3 goes to the middle; the tight end can pivot and find the deep man. **vs 1-3-1:** use a 2-1-2 set — two guards flank the point defender and two players are deep on the sidelines beyond the three across; O1 dribbles one way, then passes over the top up the sideline or reverses to O2; if X5 slides to the sideline, O5 drops to the middle for an over-the-top pass; if X3 and X4 trap O2, O5 slides to that sideline. **vs 1-1-2-1:** two deep in the corners beyond the deep defender; O2 and O3 level with O1 as he crosses; long over-the-top passes to a corner, a quick pass up the sideline, wings cut through for a layup, skip to the opposite corner; pin the deep defender and cut the opposite corner player ball side. **vs 1-2-1-1:** three into the frontcourt; O3 and O4 deep on the sidelines; O5 to the middle of the zone on the non-ball guard's side, screening and sealing the middle defender; pin the deep defender and cut the opposite deep player ball side. **Tall-passer tip:** a taller passer stays back with a small PG; the PG passes sideways just before half-court and the tall player passes up the floor. Full-court 1-3-1 counter: the power forward or centre flashes to midcourt and a quick pass goes to the weak-side guard running the sideline `[Z:WIKI131]`.
- **Usual counters:** traps sprung later; middle defender denies the tight end.
- **Detection signature [HEURISTIC]:** **tight end** = an attacker at \|x\| < 2, y 11–16 between two second-tier defenders (each within 4 m) when the handler crosses y = 16; **draw two, then pass** = TRAP onset with the pass released ≤ 0.6 s after the second defender comes within 2.5 m (score early / on time / late); **deep holder** = an attacker at r < 3 from the moment the ball crosses y = 16; **over the top** = a pass ≥ 10 m whose midpoint passes over the second-tier defenders.
- **Teams documented:** none (Coach's Clipboard) `[Z:CCHCPB]`.
- **Sources:** `[Z:CCHCPB][Z:WIKI131]`.
- **Confidence:** medium.

#### A8.6 Other named press breaks (compact full format) — NEW
Timings [HEURISTIC]; spots [HEURISTIC] unless keyed.

| Break | Family | Start alignment | Roles | Ordered actions with timing | Usual counters | Detection signature [HEURISTIC] | Teams, keys | Confidence |
|---|---|---|---|---|---|---|---|---|
| **"Dos"** (2-1-2 half-court press offence vs odd trapping zones) | F12.5 | 2-1-2: 1 and 2 stationary at the slots; 3, 4, 5 rotate | guards (stationary); rotating block/wing/corner players; 4 high post | on the guard-to-guard pass the strong-side block flashes to the wing and the weak-side corner flashes to the block (within 1.5 s); 4 posts hard near the FT line; short-corner or block pass → the high post dives; high-post catch → shot → high-low → skip opposite for three; on a skip, 3 flashes to the corner area and 5 attacks the weak block; on a corner pass, 5 sneaks across the zone `[Z:FMDOS]` | — | two guards fixed at the slots (each moves ≤ 2 m over the possession) vs a one-top defence; three interior/wing players rotate (block → wing, corner → block) on each guard-to-guard pass within 1.5 s | none (Norman North HS contributor) `[Z:FMDOS]` | medium |
| **1-1-2-1 press break ("count to two")** | F12.4 | O3 inbounds, not right under the basket; O1 receiver; O2 and O4 near half-court on opposite sides; O5 long to the right block | O1 handler; O2/O4 sideline-middle receivers; O3 trailer up the middle | O1 dribbles, passes up the sideline to O2, middle to O4, or back to O3; if O1 catches opposite O4, O4 stays up the sideline and O2 flashes middle; **count to two:** if the inbound is not getting to O1, O2 and O4 cut hard back, even to the baseline; no press → O2 and O4 release long into the secondary break `[Z:CC1121]`. Timing: 2-s trigger after the inbounder has the ball (sourced; exact start event not stated) | — | inbound not released by t0 + 2.0 s → the half-court receivers (y 12–15) cut back toward the inbounder (Δy ≥ +5 m within 2 s); the inbounder trails up the middle (\|x\| < 3, y_inbounder − y_ball 2–6 m) | none `[Z:CC1121]` | medium |
| **"4-Across" options 1–3 and "4-Fly"** — RICHER (extends F12.2 "4-Across") | F12.3 / F12.6 | four receivers in a horizontal line at y 20–23 (backcourt FT line); O5 inbounder outside the backboard span (\|x\| > 0.9) | O2/O4 double screeners; O1 cutter; O3 long decoy; O5 inbounder | Option 1: O3 fakes toward the ball and cuts long; O2 and O4 double-screen for O1, who cuts through the lane to the opposite elbow for the inbound (≤ 1.5 s); O2 slides to the weak-side short corner; O4 releases to the weak half-court. Option 2: O5 runs the baseline and inbounds to O2. Option 3: O4 comes back to the top of the key. **4-Fly (EOG):** O1 cuts over the double screen; when O1 meets O4, O2 runs a fly route for a long pass from O5 `[Z:CC4X]`. Texas Tech up two late vs Gonzaga's heavy denial: O2 cuts tight in front of the 4–5 screens, O5 curls to the rim behind 2, O3 runs the baseline; the cross-screen decoy opens the backside for O4 sprinting to the corner `[Z:FMTTU]` | heavy denial | four receivers with \|Δy\| ≤ 1.5 m at y 20–23 at t0; a double screen (screeners within 1.0 m) at y 20–23 with a cutter passing to the opposite backcourt elbow ≤ 1.5 s after t0; 4-Fly adds a GO_ROUTE by a front-line player and a LONG_PASS ≥ 15 m; thrower \|x\| > 0.9 | Texas Tech (page 31 Mar 2019 → 2018-19, exact game **unverified**) `[Z:FMTTU]`; generic `[Z:CC4X]` | medium |
| **"1-4" press break** (four across at the FT-line extended + deep diagonal) | F12.3 / F12.4 | four across at the backcourt FT-line extended (y ≈ 21.3); inbounder behind the baseline; fifth player at a "deep diagonal" spot | four receivers; deep diagonal; 5 second screener for 1 | spacing rule: sideline, middle and reverse options at all times; after a make the inbounder may run the baseline and switch sides if the strong side is covered (rule confirmed in A6.1 R3 `[Q1]`); grab and inbound immediately; vs a centrefielder face-guarding the inbounder: all four walk their men toward the baseline, then the handler reads the centrefielder and passes ahead; vs zone: flash to the middle, then reverse, look for the deep diagonal; vs man: screen-and-seal; vs switching, screen your own defender; 5 sets a second screen for 1; no trap → clear out 1-on-1; trap after the dribble → pull-back dribble and teammates come back `[Z:BFC14]` | centrefielder | four receivers with \|Δy\| ≤ 1.5 m at y ≈ 21.3 at t0; **inbounder baseline run** = thrower's x changes ≥ 3 m before release while y > 27.05; **walk-down** = all four increase y ≥ 2 m together in ≤ 2 s; **pull-back dribble** = handler's velocity reverses (Δy > +1.5 m) within 1 s of TRAP onset | none (Basketball for Coaches) `[Z:BFC14]` | medium |
| **Hooper University set list:** 1-4 Loops; Circle; 1-4 Break; Loyola Slips; Middle Go; Diamond X-Go; Go Stick; Diamond Scissors; Baseline Boomerang; Box STS | F12.3 / F12.6 | mostly not given; Go Stick = all five lined up just inside the baseline; Baseline Boomerang = 1 and 2 stacked above the FT line; Box STS = guards in opposite corners, bigs in opposite corners | see actions | **1-4 Loops:** 4 and 5 stagger-double-screen; 1 loops over the top to the strong side; 2 loops under to the weak side; 4 and 5 come to the ball. **Circle:** three breakers run a circle before the handover; when 1 breaks, 2 and 3 break away. **1-4 Break (vs man):** 1 and 2 at the elbows, 4 and 5 at half-court; on the handover 1, 4 and 5 break toward the baseline, 3 hits 4, 2 down-screens for 1 to streak and 4 hits 1 long. **Loyola Slips:** 1 and 2 turn to up-screen for 4; 4 rejects to the weak side; 5 sprints to the centre; 1 and 2 slip to the ball. **Middle Go:** 4 and 5 sprint from half-court toward the baseline; 2 screens for 1, who flashes to the baseline; 2 runs a go for a long pass. **Diamond X-Go:** 1 sprints at 4 and cuts over to the strong corner; 2 to the weak corner; 5 sprints at 4 to pull his man; 4 goes long. **Go Stick (vs a late-game man press):** everyone runs a go route except the PG or FT shooter, who runs a comeback. **Diamond Scissors:** 4 screens for 1 over the top to the strong wing, then screens for 2 to the opposite wing and dives to the FT line. **Baseline Boomerang:** 1 steps fully out of bounds to receive from 3 (legal end-line exchange after a make, R3), 3 steps in for the return, dribbles middle while 1 fills the sideline. **Box STS:** 1 diagonal-screens for 2; 4 screens for 1 (STS) and dives as the safety `[Z:HOOPU]` | — | **Go Stick** = all five within 1.5 m of the baseline (y 26–27.05) at t0, then 3–4 GO_ROUTEs and one comeback; **Baseline Boomerang** = two attackers out of bounds (y > 27.05) at once before the inbound, a pass between them along the end line, then a return pass in bounds; **Middle Go / X-Go / 1-4 Break** = a backcourt SCREEN, then one player's GO_ROUTE and a pass ≥ 15 m within 2.5 s of t0; **Circle** = three receivers' paths form a closed loop (cumulative heading change ≥ 300°) in the backcourt before the handover | none named ("Loyola" link to Loyola Chicago **unverified**) `[Z:HOOPU]` | low-medium |
| **UCLA "Wooden press break" (stack) and "Cuba"** | F12.3 / F12.6 | Wooden: 1, 2 and 5 in a vertical stack on the ball side (\|x\| 1.5–3, y 22–25); 4 throws in (27.71, 84.8); 3 at centre court (13.5, 90). Cuba: from a stack | Wooden: 1 strong-corner receiver; 2 opposite cutter; 5 back-screener then trailer; 3 come-back; 1 and 4 sideline sprinters. Cuba: last stacker (3) breaks to the basket; 2 to the weak-side baseline; 1 short ball-side baseline | Wooden `[Z:FMUCLA]`: 3 fakes downcourt and 4 fakes a pass; 1 reads (fakes inside, cuts to the strong corner); 2 cuts opposite, timed for 4's look; 5 steps toward the basket after 4 looks at 2; 3 can come back; 1 catches, fakes to 3, hits 2; 5 goes weak side to back-screen for 4 coming in bounds; 5 stays as trailer and emergency outlet (two-guard front); 2 hits 3 and stays with 5; 1 and 4 sprint the sidelines. Cuba `[Z:FMCUBA]`: the last player in the stack (3) breaks to the basket; 2 sprints to the weak-side baseline (option 2); 1 goes short down the ball-side baseline (option 3); a baseball pass is best | — | 3 players within 1.2 m laterally and ≤ 1.5 m apart in y on the inbounder's side at t0, then a split (one to the strong corner \|x\| > 5.5, y > 25; one opposite; one toward the inbounder or deep); Cuba: the last stacker's GO_ROUTE plus a pass ≥ 15 m within 1.5 s of the release | UCLA (Wooden era; page 2018) `[Z:FMUCLA]`; **Michigan** used Cuba as one of its four press breakers (season not given) `[Z:FMCUBA]`; Wooden-stack derivation from the listing `[Z:FMPB2]` | medium |
| **Michigan 2019 NCAA (vs Florida): "1-3-1 Press Break" and "Press Break Backdoor"** (Big Ten) | F12.4 / F12.6 | 1-3-1 PB: 1 inbounds; 2 at the backcourt top of the key; 3 and 4 from midcourt; 5 in the frontcourt low post opposite the ball | 2 handler; 1 inbounder → runner; 3 dunker; 5 deep. Backdoor: 2, 1 reversers; 3 arc catcher → passer; 5 backdoor cutter | 1-3-1 PB `[Z:FMUM131]`: 2 gets open and dribbles hard looking for a free runner (1); 1 dribbles down the middle and finds 3 for a dunk (the name describes the offensive set; the press faced is not named). Press Break Backdoor `[Z:FMUMBD]`: 2 and 1 reverse the ball to make the defence slide; 1 passes to an open shooter above the arc (3); 3 catches, turns and bounce-passes to 5 cutting backdoor | — | **1-3-1 PB** = 1-3-1 offensive shape at t0 (one at the inbound, three across y 15–20, one deep at y < 3); the inbounder catches back in bounds within 2 s, then dribbles the middle (\|x\| < 3) ≥ 8 m; **Backdoor** = BACKCOURT_REVERSAL → frontcourt catch above the arc (r ≥ 6.75) → within 1.0 s a bounce pass to a big moving from r > 4 to r < 1.5 | Michigan vs Florida, 2019 NCAA first round (2018-19) `[Z:FMUM131][Z:FMUMBD]` [pre-window] | medium |
| **Villanova "M-M press break"** (clear the frontcourt, back screen) | F12.3 | frontcourt cleared; ball entered to the 2 guard | 2 receiver; back-screener (1); 5 come-back | the frontcourt is cleared, the ball enters to the 2 guard, and a back screen is set; the 2 was open, the 5 open coming back, and the 1 would have been open had he kept running after screening; Villanova "hits the home run" for an and-one; a switched back screen would have stopped it `[Z:FMVU]` | switch the back screen | at t0, 0–1 attackers at y < 12.73 other than a deep runner; a backcourt back screen (screener moves toward the own baseline and screens from behind) and a LONG_PASS to the screener's partner or a runner | Villanova (page 2 May 2016; 2015-16 likely, **unverified**) `[Z:FMVU]` | low-medium |
| **Stephen F. Austin "stack" press break** (footrace) | F12.3 | 2-player guard stack (≤ 1.0 m apart) at the backcourt FT line | one to the ball, one deep; inbounder | from a guard stack one goes to the ball and one goes deep, and the inbounder throws long enough to reach the deep player; exploits defenders playing one in front of and one behind the stack — if that defender is slow, two flash to the ball and one runs; three passes to get the ball to the target player `[Z:FMSFA]` | — | 2-player stack at the backcourt FT line at t0 with simultaneous divergent cuts (one Δy ≥ +3 m toward the ball, one GO_ROUTE); then a pass ≥ 15 m, or ≤ 3 passes to reach the frontcourt | Stephen F. Austin (page 22 Mar 2016) `[Z:FMSFA]` | low-medium |
| **Colorado State "Stack Press Break (EOG)"** | F12.6 | a unique stack formation (alignment only in the diagram) | best FT shooters/handlers as targets | counters switching to get the best FT shooters or handlers the ball at the end of a game `[Z:FMCSU]` | switching (the target) | game clock ≤ 30 s in the half, margin ≤ 3, backcourt end-line inbound; a stack (≥ 3 players within 1.2 m laterally); catcher identity = the team's best FT% player (roster join) | Colorado State (page 13 Jan 2022; 2021-22 inferred, **unverified**) `[Z:FMCSU]` | low-medium |
| **"Run & Jump / Scramble Break", "Buddy" and "Buddy Go"** (diagonal screens; PG inbounds and gets a return pass) | F12.3 / F12.4 (vs F9.3 run-and-jump; vs "trap the first pass") | backcourt; R&J: 1 and 2 receivers; Buddy: PG inbounds | R&J: 2 diagonal screener; 1 user; 3 circle-back release. Buddy: 3 diagonal screener; 2 user; PG return receiver; 5 sideline flash; 4 middle flash | R&J/Scramble `[Z:FMRJ]`: the 2 diagonal-screens for the 1, who goes high or low; the 2 breaks opposite; on a catch look middle for a 3v2; the 3 diagonals out and circles back as a pressure release if his defender leaves to trap; if the defence takes the release, the weak-side guard flashes middle; attack any middle catch. Buddy `[Z:FMBUDDY]`: the PG inbounds; 3 diagonal-screens for 2 (high or low), 3 breaks opposite; inbound to 2 or 3, then the PG cuts hard down the middle for a quick return (good vs "trap the first pass"); if not open, reverse through 3 to 5 flashing to the sideline; 4 flashes middle, the PG flashes sideline, and 2 sprints wide as a throw-over option. Timing: diagonal screen within 1.0 s of t0 | trap the release | backcourt DIAGONAL SCREEN (screener path 30–60° to the baseline) within 1.0 s of t0; **circle back** = a receiver who released away turns back (> 120°) within 0.8 s of a TRAP onset on the handler; **Buddy** = the thrower is the PG (roster join) and receives a pass ≤ 2.5 s after the inbound while moving down the middle (\|x\| < 3, Δy ≤ −4 m) | none (Norman North HS contributor) `[Z:FMRJ][Z:FMBUDDY]` | medium |
| **"2-Up" press breaker** (2-1-2 shape, entry-dependent reversal cuts, windshield wiper) | F12.3 / F12.4 | two players help the inbound; any entry ends in a 2-1-2 | entries "1", "2", "3" (vs Diamond press: 3 cuts hard above the FT line), "5" (emergency; 4 runs the baseline) | the receiver pivots up-court immediately; reversal cuts on the pass back to 4: 1-Entry → 3 middle, 2 strong sideline, 5 basket; 2-Entry → 5 middle, 1 sideline, 3 basket; 3-Entry → 1 sideline, 2 middle, 5 basket; 5-Entry → 2 sideline, 1 middle, 3 basket; ball back to the inbounder after a reversal → "windshield wiper" cuts; cuts to soft spots vs zones; specials "Go" (3 and 5 flash to the sideline, 2 fakes a screen and goes deep) and "Streak" (hit the inbounder streaking up-court); avoid catching deep in the corner `[Z:FM2UP]` | — | after the first backcourt catch a 2-1-2 forms within 2.0 s (two within 3 m of the ball in y; one middle at \|x\| < 3, 4–8 m up-court; two deep 8–14 m up-court); on each BACKCOURT_REVERSAL check the role swap among middle, strong-sideline and basket cutters (label = entry type); **windshield wiper** = after the ball returns to the thrower, two cutters cross x = 0 in opposite directions within 1.5 s | none (Matt Hackenberg) `[Z:FM2UP]` | medium |
| **Wootten (DeMatha) "second handler sprints back"** | F12.3 | PG doubled at t0 by his defender and the inbounder's defender | second ball-handler starting at half-court | after a make the defence doubles the PG with the inbounder's defender; a second handler sprints back from half-court to get the ball; then the 3 brings it up, or the 4 screens so the 1 can cut to the ball `[Z:HSPB]` | — | at t0 TRAP or double denial on the PG (two defenders within 2.5 m before the inbound); a teammate starting at y 12–15 moves toward the inbounder (Δy ≥ +6 m in ≤ 2.5 s) and catches the inbound | DeMatha HS (Wootten) — high school only `[Z:HSPB]` | medium |

Purdue "3 Out Football" and Iowa "EOG Press Break 3" are A2.41/A2.42 `[Z:FMPUR][Z:FMIOWA]`.

#### A8.7 Press-break principles new to F12 (Coaching Toolbox; VCU "Havoc" lessons) — NEW (F12.7)
- **Name and aliases:** press-offence principles (Brian Williams, 2012); "Havoc" counters.
- **Family / sub-family:** F12.7 principles.
- **Start alignment:** inbound receivers no deeper than the backcourt "volleyball" corner (27.33, 75.8/104.2); three receivers about 4.57 m apart from each other and from the ball `[Z:CTPO]`.
- **Roles:** designated inbounder (with a backup on a depth chart); four players bring it up; one stays at the basket as the finisher; best perimeter player in the middle.
- **Ordered actions / rules `[Z:CTPO]`:** if inbounds are denied, two go long and one stays short; pass fakes; never pass across the basket in the backcourt; the reversal player stays ball side; **at most two reversals before the ten-second line**; pass across the ten-second line rather than dribble, so the handler keeps a live dribble. **Vs VCU "Havoc"** (SI 2013): VCU's man press is called "fist" and its double-team "double fist" (**name collision** with Izzo's zone set "Fist"; namespace `def.VCU.Fist` vs `off.MSU.Fist`); traps are sprung near the sideline just past half-court; the diamond press (a "madman" on the inbounder) funnels the inbound to a corner; Rhode Island beat the diamond by passing back to the inbounder and advancing without much dribbling `[Z:SIVCU]`.
- **Usual counters:** sideline traps just past half-court (Havoc).
- **Detection signature [HEURISTIC]:** receiver spacing = mean pairwise distance among the three nearest receivers and the ball, flagged if < 3.5 m (crowded) or within 4.57 ± 1.5 m (on spec); cross-basket pass = a backcourt pass whose line passes within 2 m of the own rim (x ≈ 0, y ≈ 25.47) → risk flag; reversal count before y = 12.73 (flag > 2); crossing mode = pass vs dribble across y = 12.73; corner-catch risk = a catch at \|x\| > 5.5 with y > 24 or 11 < y < 15.
- **Teams documented:** VCU defence (Shaka Smart era, 2012-13) and its opponent Rhode Island (2012-13) `[Z:SIVCU]`.
- **Sources:** `[Z:CTPO][Z:SIVCU]`.
- **Confidence:** medium-high (stated rules); usage frequency unknown.

**Press-break gaps.** No opened source names an MSU press-break alignment (A8.1); film tagging is the only route. Breakthrough Basketball (Line press breaker, others) and MGoBlog "Un-wreaking Havoc" returned 403.

### A9. Vocabulary proposals (coaches' words vs measured geometry; `config/vocabulary_map.yaml` was NOT edited)

Each row records both the word as coaches use it and what the geometry measures, so the vocabulary owner can decide. Proposals only.

| Term | Coaching usage found | Measured geometry / conflict | Proposal |
|---|---|---|---|
| **"45"** | (a) the wing spot ("4 to the 45", Illinois Swing Iso PnP, A2.6 `[B14]`; "45 player drifts", A3.31 `[P40]`); (b) a set name (Zone-2 "45"/"54", F11.2 `[O60b]`, A7.13 `[Z:CC122]`); (c) a cut heading ("45 cut", F8.2 `[O21]`); (d) loosely the elbow area (vocab note) | the elbow is at (4.57, 66.4°); the wing centre is (7.07, 45°); the FT-line-extended wing used in several notes is (7.73, 32.8°) | keep `45_spot` → wing (r ≥ 6.75, 12° < θ ≤ 60°, centroid (7.07, 45°)); namespace `45` the set (`zone.Zone2.45`) and `45_cut` (heading 30–60° toward the rim) separately; never map "45" to the elbow without context |
| **"Elbow-extended" / "FT-line extended"** | screen spots "near the elbow extended" (A1.15 STS ATO BLOB); wings "at FT-line extended" (§0.1, A6/A8 notes) | inside the arc just outside the lane: (4.83, 60.2°); FT-line extended near the sideline: (7.73, 32.8°) (0.98 m beyond the arc, ≈ 1.1 m from the sideline); on the arc: (6.75, 38.4°) | add three measured terms: `ft_line_ext_inside` = (4.83, 60.2°)/(4.83, 119.8°); `ft_line_ext_wing` = (7.73, 32.8°)/(7.73, 147.2°) (near the sideline); `ft_line_ext_arc` = (6.75, 38.4°)/(6.75, 141.6°) |
| **Short corner** | used for screens, cutters and zone posts in every note | values used: (4.5, 8°), (4.31, 4.0°), (4.51, 3.8°), (4.53, 6.3°); §0.1 r 3.5–5.5, θ 0–15°; defense additions (4.02, 5.7°); vocab "to be defined from film" | provisional `short_corner` = r 4.0–5.5 m, θ ≤ 15° (≥ 165°), centroid (4.5, 6°) until film calibration; add `high_short_corner` (4.27, 20.6°) (zone note) |
| **Block** | low post, "block" | vocab: x = ±1.83, y 0.3–1.5 (θ ≈ 9°–39°); §0.1: x ±1.9–2.3, y −0.6 to 1.2 (r 2.0–2.5, θ 10–35°); notes used (2.0, 24°), (2.04, 26.2°), (2.18, 15.9°) "just outside the lane" | vocab is authoritative; record the §0.1 band as `block_outside_lane` (x ±2.1, y 0.6 → (2.18, 15.9°)) used by the special-situations note for box/stack spots |
| **Dunker spot / "porch" / "Ghost spot"** | "porch" (Iowa State, A3.9 `[P3]`); "Ghost spot" (Wizards Angle Short, A3.11 `[P36]`); MSU "dunker" opposite the PnR (A1.10 `[M10]`) | all inside vocab `dunker_spot` (2.0 ≤ \|x\| ≤ 3.5, y ≤ 0.6) | add aliases `porch`, `ghost_spot` → `dunker_spot`; keep "ghost" the screen action separate |
| **"77"** | double drag (F2.1 `[O11]`); stagger ball screen (set_taxonomy §1.5); CelticsBlog "stagger" for handlers `[X2]`; MSU "77 Wide Pindown" = double screen side by side at the top (A1.1); "77 Wall" side by side on one side (A3.24) | three geometries: sequential on-the-move screens (≥ 0.5 s apart, first a body length higher, `[P16]`), staggered (1.5–4 m apart along the path), side-by-side wall (≤ 1.2 m apart, same level) | store `77` with a geometry sub-label {`77_drag`, `77_stagger`, `77_wall`} measured from screener separation and timing |
| **"Trade" / "2le"** | MSU "2le High Trade" (A1.4); Purdue "Double High PnR" (A2.1) | sequential high ball screens by two bigs ≥ 0.8 s apart; first screener lifts (MSU) or sinks to the post (Purdue) | add `double_high` alignment and `trade` = first screener lifts to r ≥ 6.75 after screen 1 |
| **"Spread"** | Purdue "Spread" PnR = top/slot ball screen with both corners filled and the paint empty (A2.4); Michigan "spread ballscreen" (A3.26); Underwood/Altman "Spread" continuity (F3.1, F4.2) | first two are spacing tags at the screen moment; the third is a system | `spread_pnr` (spacing tag) vs `system.Spread` (Underwood) |
| **"Shake"** | F5.6 spacing tag = corner lift during a side PnR `[O24]` (A5.19); Michigan/Beilein "shake" ball screen = fake wide pin-down, then sprint into a spread ball screen (A3.26) | spacing relocation vs screener pre-action | `shake` (spacing) vs `shake_ballscreen` (pre-action) |
| **"Chicago"** | F6 pin-down → DHO `[O50]`; Cal State Bakersfield "Chicago Pin" = DHO → follow ball screen → veer (A4.3); zone "Chicago" = double back-screen lob (A7.11); Michigan "Chicago Split" (`[M49]`) | different actions | `chicago` = pin-down → DHO only; others namespaced (`zone.Chicago`, `CSUB.ChicagoPin`, `UM.ChicagoSplit`) |
| **"Miami"** | DHO → PnR (F6 `[O11]`); zone "Miami" = pin, skip, re-screen the middle (A7.11) | different actions | `miami` (F6) vs `zone.Miami` |
| **"Special"** | MSU "Special" (1-3-1 vs 2-3; the 5 screens the low outside defender, `[S12]`); Flannery "Special"/"Special-Down" (double-low stack, A7.11) | different sets | `MSU.Special` vs `Flannery.Special` |
| **"Fist"** | MSU zone set "Fist"/"Fist Down" (A7.7); VCU man press "fist"/"double fist" (A8.7) | offence vs defence | `off.MSU.Fist` vs `def.VCU.Fist` |
| **"80" / "Corners"** | "80" press break (F12.2) vs a defensive match-up press name (zone/press note); "Corners" 4-out zone offence (A7.12) vs 2-1-2 "Corners" vs odd fronts (F11.2 `[O60b]`) | name collisions | namespace by side of the ball and by zone faced |
| **"Stack"** | NBA "Stack PnR" = Spain (A3.22 `[P1]`); "Stack Roll" = guard pre-stacked under the screener (A3.23); stack formations (BLOB stack, diagonal stack, sideline stack, press-break stacks) | three meanings | Spain aliases {Spain, Stack, Bamberg}; separate `stack_roll`; formations as `align.stack_{vertical,diagonal,sideline}` |
| **"Hawk"** | Hawk cut (rub cut off a high-post back screen after a dribble entry, A5.21); Hawk BLOB (box, inbounder becomes shooter, A6.13) | different actions | `hawk_cut` vs `blob.Hawk` |
| **"Wheel"** | UConn motion "Wheel" (F4.2 `[O14]`); Duke "Wheel Action" (A5.14); Louisville "DHO Wheel" `[P32]`; Obradović spacing "wheel" (A3.31) | undefined in every opened source | keep `wheel` as an unresolved label; do not map until defined |
| **"Zipper"** | coaching: down screen at the block for a vertical cut to the slot; CTG: a down screen **before a sideline inbound** (A5.24) | context differs | `zipper` (coaching) + flag `inbound_context` |
| **"Pin-in"** | CTG `pin_in` = screen on the defender of a stationary perimeter player (A5.1); Kansas "Ball Screen to Pin In" = screening the middle zone defender (A7.9) | man vs zone target | `pin_in` with target class {man defender, zone slot} from the defence layer |
| **"Inverted stagger"** | Illinois Winner SLOB, Nebraska 5-out ATO (A2.20) | undefined | provisional: stagger whose user moves −y, or whose first screener cuts for a lob; **unverified** |
| **"Circle"** | circle cut (MSU 14-Circle, A5.7); "Circle" press break (A8.6); "Circle Lob" BLOB (A6.8) | three actions | `circle_cut`, `press.Circle`, `blob.CircleLob` |
| **"EOQ"** | MSU "EOQ Horns Set" (F18.1 `[O89]`) | NCAA men play halves; 2026-27 keeps halves `[Q2]` | treat "EOQ" as a FastModel label = end of half/period; meaning **unverified** |
| **"High post" vs "nail"** | high post used for (4.19–5.2, 90°) in several notes | vocab nail = (4.19, 90°) exactly | `high_post` = r 3.8–5.2 m, θ 70–110°; `nail` stays the point anchor |
| **"Top"** | notes use (7.5, 90°) and (7.6, 90°) | both inside vocab "top" (r ≥ 6.75, 80° < θ < 100°) | no change; use (7.6, 90°) as the template centroid |
| **"Blast"** | MSU "Blast" (A5.6: two-guard front, guard-to-guard pass, 4 pops, both guards dive; "X/Floppy option") `[X18]`; existing "Horns Stagger / Blast" (§3.2: strong-side corner backdoor) `[O12]` | two different actions share the name (added by the fixer, 2026-10-18) | `MSU_Blast` vs `blast_backdoor`, matching motion_starts G06 |

### A10. Counts (this section)

| Sub-section | Family | Blocks | Table-row items | Total items | Notes |
|---|---|---|---|---|---|
| A1 | F18 MSU (2024-26 sets + pre-window FastModel sets) | 13 | 11 | **24** | + 8 confirmation rows (A1.14) not counted |
| A2 | Big Ten other teams (F1, F2, F4, F5, F6, F7, F8, F10, F12, F13, F14, F17) | 40 | 14 (9 team profiles + 5 BLOB/ATO rows) | **54** | + 6 pace/possession data rows not counted |
| A3 | F5 Ball-screen offense | 30 | 13 (8 tag-attack options + 5 Spain sub-variants) | **43** | |
| A4 | F6 Handoff offense | 6 | 0 | **6** | |
| A5 | F8 Off-ball screens and cuts | 24 | 11 | **35** | |
| A6 | F13 Special situations | 30 | 11 rule rows | **41** | + 5 defence cross-reference rows (defense_full F14) and 4 enrichment rows not counted |
| A7 | F11 Zone offense | 21 | 15 | **36** | |
| A8 | F12 Press offense | 6 | 13 | **19** | |
| **Total** | | **170** | **88** | **258** | MSU-attributed items appear in A1 and also inside A3–A8 (e.g. A3.12, A3.21, A3.27, A3.28, A4.1, A4.2, A5.11, A5.12, A6.2–A6.6, A6.14–A6.19, A6.22, A6.28, A7.1–A7.7, A8.1) |

**Distinct items after de-duplication (fixer, 2026-10-18):** **255**. Three counted items are not distinct: the A1.15 "Weave Zoom" row (same set as A1.6; the canonical weave primitive is A4.6), the A1.15 "Zipper Spain PNR SLOB" row (same set as A3.21) and A6.7 (a BLOB use of the existing §3.1 "1-4 Low" alignment, now marked RICHER). Distinct per sub-section: A1 **22**, A6 **40**, others unchanged. The 13 MSU sets that also have entries in `motion_starts.md` (A11.15) are counted once in this file; across both files they are one set each.

### A11. Corrections 2026-10-18 (older text above is unchanged; these notes apply to it)

1. **§0.1 "Block" row** (x ±1.9–2.3, y −0.6 to 1.2; r ≈ 2.0–2.5, θ 10–35°) disagrees with `vocabulary_map.yaml` block (x = ±1.83, y 0.3–1.5; θ ≈ 9°–39°). Correction 2026-10-18: the vocabulary map is the project anchor; this section uses it. See A9 "Block".
2. **§0.2 `SCREEN`** (< 0.6 m/s for ≥ 0.3 s) is looser than the Job A rule (≤ 0.3 m/s for ≥ 0.5 s within ~1.2 m). Correction 2026-10-18: keep both as `SCREEN_loose` and `SCREEN_strict` and store which one fired (A0, A5).
3. **F12.2 "MSU press break — [UNVERIFIED]: no opened source"**. Correction 2026-10-18: one opened source documents MSU press-break preparation ("We always go over our press breakers… We call it special teams", Tyson Walker, 21 Mar 2024) `[Z:CBS24]`; the alignment is still unverified (A8.1).
4. **F13.4 "Last shot (hold for one) [CONVENTION]"**. Correction 2026-10-18: a documented MSU instance now exists (vs Purdue, 26 Feb 2022: 60-s timeout at 0:16, Walker three at 0:01) `[Q48]` (A6.28).
5. **F13.2 "STS ATO BLOB — [title only]"**, set_taxonomy §3.2 "Pin Down Circle [UNVERIFIED contents]", §6 "Twist BLOB" (title only). Correction 2026-10-18: STS ATO BLOB and Pin Down Circle contents are now known `[M46][M38]` (A1.15, A6.37); "Twist BLOB" (MSU, Winston) is still title-level — Illinois "Stagger Twist BLOB" (A2.34) is a different play.
6. **F18.1 / F3.2 "EOQ Horns Set"**. Correction 2026-10-18: NCAA men play two halves (kept for 2026-27) `[Q2]`, so "EOQ" is a FastModel label whose NCAA-men meaning is unverified (A6.1 R11).
7. **F16 "77 = Stagger / double drag"**. Correction 2026-10-18: three distinct geometries share the name; see A9 "77".
8. **F16 "Chest — FIBA: chest pass. MSU: a set name"** and **F11.2 "Fist"** — no change in meaning, but note the new collisions recorded in A9 ("Fist" with VCU's press; "Special" with Flannery).
9. **F1.4 "Izzo / MSU break" — shooting-trailer pitch-back `[O30]`**. Correction 2026-10-18: no 2024-25 or 2025-26 source confirms the trailer role or leak-outs; the 2024-26 role evidence is in A1.13 (unverified for trailer/leak-out).
10. **F11.2 MSU zone row "Izzo Special / Special-2 / 1-3-1 Double / Fist / Fist Down"**. Correction 2026-10-18: none of these was re-confirmed for 2024-26; the only 2024-25 MSU zone set found is the swallow-cut "Vs Zone" (A1.5); Fist-Down's full sequence is in A7.7.
11. **Rules wording in F12/F13 that was "unverified" in the zone/press research** (5-s throw-in, 10-s backcourt, running the end line after a make) is confirmed from the 2024-25 NCAA rules text in A6.1 (R1, R3, R7) `[Q1]`; 2025-26 rule wording remains unverified (book not fetched).
12. **Outside this file (for the owner of `docs/research/set_taxonomy.md`, not edited here):** the off-ball research notes that set_taxonomy's first-pass Iverson signature used "y ≈ 13–20", which is in feet; the metric equivalent used here is y 4.6–7.0 m (A5.16).

13. **Fixer pass 2026-10-18 — source attribution (applied in place to today's text).** Pages re-opened or newly opened in this pass are keyed `[V#]` (A12, last block) or re-cite the original key. Changes: A1 scope — MSU 2025-26 record 27-8 and Sweet 16 exit to UConn now cited `[V4][V3]`; the `[M50]` "no MSU entry after 13 Mar 2025" claim is an **unverified absence** (page 1 alone cannot show it). A1.12 — exact Izzo quote ("he's got to come off those ball screens …"), Fox Sports updated 22 Nov 2025 `[M13]`; 21 Nov **unverified**. A1.13 — the Fears quote is `[M22]` only; `[M23]` supports only the general tempo statement. A1.14 — UCLA game was 4 Feb 2025 and ended in a missed Akins three `[M34][M9]`. A2.15 — Purdue vs McNeese was the 2025 second round (R32), not R64 `[V1]`; 22 Mar 2025 is inferred from the bracket slot. A2.16 — "Sweet 16" is not in `[B9]`; the 2024 Sweet 16 meeting exists `[V2]` but the link of the play to it is **unverified**. A2.31 — round not in `[B20]`; the 2025 R32 meeting is `[V1]`. A2.36 — "Willard" and "vs Colorado State" are now sourced `[V5][V6]` (not from `[B21]`). A2.37 — "game-winner" is design intent only `[B29]`. A2.42 — the made game-winner is attributed to `[B60]`; the R32 round is `[V3]`.
14. **A2 scope rule exceptions.** A2.2 `[B7]`, A2.17 `[B2]`, A2.35 `[B16]` and A2.41 `[B13]` do not state men's/MBB on the source page; each now carries "men's attribution **unverified**". Treat them as provisional (equivalent to the "Excluded or ambiguous" list) until a men's source is opened; Northwestern `[B29]` ("MBB") and Purdue `[B9]` (vs Gonzaga) are unaffected.
15. **Cross-reference with `docs/taxonomy/motion_starts.md` (one canonical entry per set).** Rule: the **template and detection signature** live in `motion_starts.md`; this file keeps the **MSU evidence** (games, quotes, frames). Exceptions: Weave Zoom and 2le High Trade use the canonical primitives in A11.16 and A11.17, which both files should reference. Where the two files' thresholds still differ for the other sets, the motion_starts signature governs until the owners harmonise them (motion_starts is not edited by this pass).

| Set | This file | motion_starts | Canonical signature |
|---|---|---|---|
| Horns Pistol | A4.1 | H02 | motion_starts H02 |
| Horns Swing Pistol | A4.2 | H03 | motion_starts H03 |
| Horns Out Slip | A3.12 | H06 | motion_starts H06 |
| 1-4 STS | A1.15 row, A3.1 | O04 | motion_starts O04 |
| Iverson Ram Reject Away | A1.15 row | O05 | motion_starts O05 |
| Floppy Loop Under | A5.5, A5.15 | K03 | motion_starts K03 |
| MSU Blast | A5.6 | G06 (`MSU_Blast`) | motion_starts G06 |
| Elbow Away STS / Pindown | A5.11 | E01, E02 | motion_starts E01, E02 |
| Stagger Slip Curl & Pop | A1.15 row | S04 | motion_starts S04 |
| Pin Down Circle | A1.15 row | U06 | motion_starts U06 |
| Motion Go Duck-In | A3.27 | U07 | motion_starts U07 (start spot for 5 = (1.85, 3), A3.27 as amended) |
| 2le High Trade | A1.4 (A2.1 Purdue = same family) | U12 | `double_high` + `trade` (A11.17) |
| Weave Zoom | A1.6, A1.15 row, A3.28, A4.6 | U05 | `weave` + `weave_3dho_return` (A4.6, A11.16) |

16. **Weave — one canonical primitive.** A4.6 is the single F6 `weave` primitive: ≥ 2 consecutive DHOs within 5.0 s (first to last), all at r 6.5–9.0, θ 45–135°, alternating participants, hander continuing past the receiver. Flags: `weave_3dho_return` (motion_starts U05's 3-DHO-and-return version), `weave_then_high_screen` (ball screen ≤ 2.0 s after the last DHO). A1.6 and A3.28 now reference it; the A1.15 "Weave Zoom" row is evidence only. The earlier variants (≥ 2 in 4.0 s at θ 50–130; ≥ 3 in 5 s; ≥ 2 in 5 s at r ≥ 6.5; 3 in ≤ 5 s at r 6–8.5) are superseded. A4.6's former claim that the weave "appears nowhere above" was false and has been replaced.
17. **Double high — one canonical primitive `double_high`.** Pre-screen: two bigs at r 4.5–8.0, θ 60–120°, ≤ 3.5 m apart; two ball SCREENs on the same handler by different bigs within 3.0 s and ≥ 0.8 s apart (Detroit, where both are stationary together, is excluded by the 0.8 s gap). Sub-labels: `trade` (first screener reaches r ≥ 6.75 within 2.0 s of his screen; MSU A1.4, motion_starts U12) and `sink` (first screener reaches r < 2.5; Purdue A2.1). A1.4 and A2.1 now reference it; the 2.5 s window (A1.4) and the r 4.5–6.5 snapshot (A2.1) are superseded.
18. **Canonical primitive table (one value per primitive; strict/loose pairs only where kept on purpose).** Blocks that state their own value now read as references to these names.

| Primitive | Canonical value [HEURISTIC] | Kept variant (flag) | Superseded block-local values |
|---|---|---|---|
| `SCREEN` | strict ≤ 0.3 m/s for ≥ 0.5 s within 1.2 m | `SCREEN_loose` < 0.6 m/s for ≥ 0.3 s (A11.2) | — |
| `ROLL` | radial velocity ≤ −1.5 m/s within 1.0 s of the handler passing; r < 2.5 within 2.0 s | — | A0 "r < 2.0–3.0" |
| `POP_ARC` (= `POP`) | screener reaches r ≥ 6.6 within 2.0 s | — | A0 "1.5–2.0 s" |
| `POP_MID` | screener moves outward ≥ 1.5 m and stops at r 4.0–6.6 without rolling, within 2.0 s | — | needed by A3.8 step-up and short-corner pops |
| `SHORT_ROLL` | catch at r 3.0–6.0, \|θ − 90°\| ≤ 35°, within 2.0 s | `SHORT_ROLL_strict`: decelerates to < 1.5 m/s in that zone within 1.2 s of t₀ (A3) | A0 "r 3.5–6.0" |
| `DHO` | hand-to-hand ≤ 1.0 m, air time ≤ 0.3 s | `DHO_strict`: ≤ 0.6 m, ≤ 0.2 s (A6 restarts) | A0 "ball flight ≤ 1.0 m" |
| `LOB` | apex ≥ 3.5 m; proxy when height is not tracked: catch at r < 1.5 by a receiver moving rimward ≥ 3 m/s | `LOB_high_catch`: hands ≥ 3.0 m at the catch (A6) | A3.11 apex > 3.0; A5.12 catch > 3.05; A6 apex ≥ 3.6 |
| `ELEVATOR` | two stationary screeners with a pre-gap 0.9–1.6 m that closes to < 0.6 m within 0.5 s of the cutter passing between them | `elevator_wide`: pre-gap 1.6–3.0 m closing to < 1.0 m within 0.6 s (A5.17 gate variant) | A2.18 / A2.29 "1.0–1.2 → < 0.6 within 0.3 s"; A6.14 "within 0.4 s" |

19. **Timing reference event per subsection (supersedes A0's "all windows are after t0").** A1/A2 half-court sets, A5, A7: t0 = first identifiable action. A1.13 and other live-ball transition items: t0 = possession-change frame (DREB, steal, or ball through the net). A3/A4: t₀ = screen contact (minimum handler–screener distance); negative windows are allowed. A6 and every BLOB/SLOB/full-court restart in A1/A2 (A1.15 BLOB rows, A2.29–A2.42): windows from **t_touch** (game and shot clocks start); movement before the touch is written t_dispose + Δ. A8: ball through the net (after a make) or the official's handover. Game-clock values ("3.7 s on the clock") are context conditions, not windows; A2.36 has been re-expressed this way. Every timing cell should name its reference.
20. **Court conventions and landmarks.** (a) This section uses the rim centre **1.60 m** from the baseline (`docs/requirements.md`): baseline y = −1.60, half-court 12.73, far end line 27.05. The older §0.1 sentence ("1.575 m") is superseded here pending reconciliation by the requirements owner; the differences are ≤ 0.025 m (baseline −1.575, half-court 12.75, end line 27.075). (b) Out-of-bounds inbounder offset: **0.30 m** behind the line everywhere → BLOB inbounder (3.33, −34.7°); A6's 0.35 m / (3.36, −35.4°) has been replaced in today's text. (c) Left side: θ_L = 180° − θ_R everywhere, including behind the end line (BLOB left inbounder 214.7°; A6's "180° + \|θ\|" is the same rule); −145.3° is the same direction mod 360 and parsers should normalise. (d) A0 is canonical for named spots; other values in the blocks are named variants: `block_outside_lane` (2.18, 15.9) (x = 2.10, outside vocab x = ±1.83; A6 BLOB templates); `corner_deep` (6.8, 4.5) as the corner centroid, with (6.67, 3.9), (6.60, 0), (6.76, 2.5), (6.71, 2.6) all inside the vocab corner region (r ≥ 6.60, θ ≤ 12°); `mid_post_lane_line` (3.02, 52.7) (A5.2); `high_post` = band r 3.8–5.2, θ 70–110° (A9), so A5.21/A5.22's (5.2, 90) is the top of that band and the nail (4.19, 90) stays the point anchor.
21. **Stack and 4-Low alignment rules.** Stack (A2.32, A6.7 note): consecutive-neighbour distance ≤ 1.5 m along a fitted line (not "pairwise", which is impossible for 3–4 players on a line); diagonal if the fitted line is 25–65° to the baseline; A2.32's corner exit includes θ ≥ 168°. The old example spots (6.4, 135), (5.0, 125), (3.8, 110), (2.6, 80) broke the rule (neighbour gaps 1.71, 1.66, 2.02 m; line ≈ 22°) and were replaced by compliant spots on a 45° line. 4-Low: one ALIGN rule — all four in-bounds attackers at y ≤ 1.5 m with x spread ≥ 9 m at t_dispose; A1.15's "r < 3.5" (which excluded the corners) and the A6.7 note's "y ≤ 1.2" are replaced. A6.7 is RICHER (BLOB use of §3.1 "1-4 Low"), not NEW.
22. **Zipper Spain PNR SLOB.** A3.21 is canonical (SLOB start with the inbounder out of bounds at \|x\| > 7.62, ≈ (10.55, 41.1)); the A1.15 row points to it. A1.15's "ball out of bounds at \|x\| ≈ 7.6 m" put the ball on the sideline and is superseded.
23. **"Blast" name collision.** `MSU_Blast` (A5.6) vs `blast_backdoor` (§3.2 "Horns Stagger / Blast"), as in motion_starts G06; row added to A9.
24. **Feet labels.** The A6.1 R10 label `spot_28ft` is renamed `spot_8p53m` in today's text; use the metric name in every downstream schema. Older text: §0.1's "SLOB 28-ft mark" and the F13 sentence "at the 28-ft mark" should be read as **the 8.53 m mark** (not reworded here).
25. **Geometry and timing corrections applied in place (fixer pass).** A1.13 backcourt start y 12.7–27.4 m, θ 59–121°. A2.41 far FT line r ≈ 21.3–21.5 (y = 27.05 − 1.60 − 4.19 = 21.26), not r ≈ 23. A3.27 "below the block" = (1.85, 3), not (1.5, 20) (which is inside the lane at block height). A4.5 fake-DHO baseline drive: the path enters y < 2.0 within 1.0 s of the fake and reaches r < 3.05 with θ ≤ 30° (or ≥ 150°) — the old "stays at y < 2.0" could not match a wing start (y = 4.63). A5 speed bands made contiguous (sprint ≥ 6.0 m/s). A5.16 Iverson 1.5–2.3 s at 4.5–6.0 m/s. A5.24 zipper block → slot 1.3–2.0 s (≈ 6.1 m at 3–4.5 m/s); A3.21's zipper window widened to 2.0 s to match. A6.21 SLOB stack (x ≈ 4.8, y ≈ 6.9 ± 1.4) → r 7.3–9.6 m, θ 49–60° (centre (8.41, 55.2°)). A6.23 Nova ≥ 13 m in ≤ 3.5 s (mean ≥ 3.7 m/s). A6.25 Duke 1992: the source's 79 ft (24.1 m) is kept and the ≈ 23 m coordinate distance is noted; offsets **unverified**. A6.26 Split mean ≥ 4.5 m/s (peak ≥ 5.5). A3.7 Angle Pop orientation test restated (screener on the sideline side of X-ball). A3.8 uses `POP_ARC ∪ POP_MID`. A2.11 Jet adds the relocation step (or catch at r ≥ 4.0 with 2PA/3PA tags). A6.2 Sparty box = one attacker per block and per elbow. A9 "Elbow-extended": (7.73, 32.8°) is FT-line extended near the sideline (0.98 m beyond the arc); the on-arc spot is `ft_line_ext_arc` (6.75, 38.4°)/(6.75, 141.6°).
26. **Vague signatures given numbers.** A2.24 screener-orientation entropy ≥ 2.5 bits (8 bins) over ≥ 20 screens. A2.25 ≥ 30% of possessions with first FGA ≤ 10 s and template-match rate < 20%. A2.28: UCLA Dent handler in ≥ 50% of ball screens; Washington ≥ 25% of FGA within 10 s; Indiana SLIP + GHOST ≥ 20% of ball screens; Oregon not implementable until a 2024-26 description is opened. A7.11 Toledo: short-corner post and high-post post for ≥ 60% of set time. A7.12 Corners: O5 at r 3.8–5.2 (ball θ 70–110°), r < 2.5 (ball θ < 30° or > 150°). A5.14 Wheel: **not implementable until defined**.
27. **Confidence harmonised.** MSU 1-4 STS: "high for the caption text; medium-low for MSU usage (third-party contributor); low for 2024-26" in both A1.15 and A3.1.

### A12. Additional sources (2026-10-18)

Every URL below was opened (WebFetch, or curl / in-app browser where WebFetch was blocked, as each research note records) during the 2026-10-17/18 Job A research. Pages that could not be opened are not listed as sources; claims that depended on them are marked **unverified** above. This writer did not re-open the pages.
**MSU note (`[M#]`; numbering follows the MSU research note's source list)**
- **M1**: The Only Colors (SB Nation), "MSU Basketball Film Room: Plays of the Month" (3 Dec 2025). https://www.theonlycolors.com/basketball/43621/msu-basketball-film-room-plays-of-the-month
- **M2**: The Only Colors, "Tom Izzo must adapt if he wants another national title" (7 Apr 2026). https://www.theonlycolors.com/basketball/45979/tom-izzo-must-adapt-if-he-wants-another-national-title
- **M4**: Feed The Post (J. Jackson), "5 Takeaways – Michigan State vs Northern Michigan" (14 Oct 2024). https://feedthepost.substack.com/p/5-takeaways-michigan-state-vs-northern
- **M5**: FastModel PlayBank 478091, "Michigan St 2le High Trade" (4 Mar 2025). https://playbank.fastmodelsports.com/library/basketball/fastdraw/478091/play-Michigan-St-2le-High-Trade
- **M6**: YouTube Jv0AvUTP-M4, "NCAA 2024 25 Michigan 2le High trade 01" (thumbnail inspected). https://www.youtube.com/watch?v=Jv0AvUTP-M4
- **M7**: FastModel PlayBank 478264, "Michigan State Vs Zone" (13 Mar 2025). https://playbank.fastmodelsports.com/library/basketball/fastdraw/478264/play-Michigan-State-Vs-Zone
- **M8**: YouTube LhTyXYidfT8 (thumbnail inspected). https://www.youtube.com/watch?v=LhTyXYidfT8
- **M9**: Wikipedia, 2024-25 Michigan State Spartans men's basketball team (raw). https://en.wikipedia.org/w/index.php?title=2024%E2%80%9325_Michigan_State_Spartans_men%27s_basketball_team&action=raw
- **M10**: Hammer & Rails, "Purdue Basketball: Michigan State Preview" (17 Feb 2025). https://www.hammerandrails.com/2025/2/17/24367290/purdue-basketball-michigan-state-preview
- **M11**: UM Hoops, "Familiar formula: Michigan preps for classic Michigan State test" (20 Feb 2025). https://umhoops.com/2025/02/20/familiar-formula-michigan-preps-for-classic-michigan-state-test/
- **M12**: NetScouts Basketball (N. Koesel), "Michigan State Tops Arkansas in Instant Classic" (Nov 2025). https://netscoutsbasketball.com/?p=937
- **M13**: Fox Sports (22 Nov 2025), Izzo on Jeremy Fears Jr. https://amp.foxsports.com/stories/college-basketball/michigan-state-hc-tom-izzo-jeremy-fears-jr-stats-as-good-any-guard-ive-had
- **M14**: Spartan Avenue (21 Mar 2026), Fears shooting struggles. https://spartanavenue.com/jeremy-fears-shooting-struggles-are-letting-the-worst-michigan-state-fears-linger-to-the-sweet-16
- **M16**: SI (Dec 2025), "Why MSU Jaxon Kohler's improved 3-point shooting is important". https://www.si.com/college/michiganstate/why-msu-jaxon-kohler-improved-3-point-shooting-important-
- **M17**: SI (4 Oct 2025), "One Thing MSU Must Do to Keep Offense Efficient" (same page as `[O56]`, re-opened). https://www.si.com/college/michiganstate/spartans-basketball-carson-cooper-jeremy-fears-coen-carr-tom-izzo-offense
- **M18**: Inside the Hall (27 Feb 2026), IU hosts MSU preview (same as `[S87]`, re-opened). https://www.insidethehall.com/2026/02/27/what-to-expect-iu-basketball-hosts-michigan-state-on-sunday-afternoon/
- **M21**: Feed The Post newsletter (17 Feb 2025). https://feedthepost.substack.com/p/big-ten-basketball-weekly-newsletter-bb0
- **M22**: Feed The Post newsletter (13 Jan 2025). https://feedthepost.substack.com/p/big-ten-basketball-weekly-newsletter-26a
- **M23**: Feed The Post newsletter (27 Jan 2025). https://feedthepost.substack.com/p/big-ten-basketball-weekly-newsletter-1c4
- **M33**: YouTube TdhAecbJKJQ (AndrewTalksHoops, 11 Mar 2025; description only). https://www.youtube.com/watch?v=TdhAecbJKJQ
- **M34**: Spartan Avenue (5 Feb 2025), loss at UCLA. https://spartanavenue.com/what-went-wrong-in-michigan-state-basketball-s-loss-to-ucla-01jkbvdfry35
- **M36**: FastModel 437671, "Michigan State Spartans – Weave Zoom" (17 Mar 2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/437671/play-Michigan-State-Spartans--Weave-Zoom
- **M37**: FastModel 437680, "Zipper Spain PNR SLOB" (17 Mar 2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/437680/play-Michigan-State-Spartans--Zipper-Spain-PNR-SLOB
- **M38**: FastModel 438159, "Pin Down Circle" (23 Mar 2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/438159/play-Michigan-State-Spartans--Pin-Down-Circle
- **M39**: FastModel 447226, "Iverson Ram Reject Away" (25 Sep 2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/447226/play-Michigan-State-Spartans--Iverson-Ram-Reject-Away
- **M40**: FastModel 461577, "1-4 STS" (21 Mar 2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461577/play-Michigan-State-Spartans--1-4-STS
- **M41**: FastModel 461774, "BLOB" (24 Mar 2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461774/play-Michigan-State-Spartans--BLOB
- **M42**: FastModel 462143, "Horns Twist Veer" (28 Mar 2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462143/play-Michigan-State-Spartans--Horns-Twist-Veer
- **M43**: FastModel 409321, "Stagger Slip Curl & Pop" (20 Mar 2022). https://playbank.fastmodelsports.com/library/basketball/fastdraw/409321/play-Michigan-State-Spartans--Stagger-Slip-Curl--Pop
- **M44**: FastModel 409173, "Quick Duck-In BLOB" (19 Mar 2022). https://playbank.fastmodelsports.com/library/basketball/fastdraw/409173/play-Michigan-State-Spartans--Quick-Duck-In-BLOB
- **M45**: FastModel 409177, "Clear BLOB" (19 Mar 2022). https://playbank.fastmodelsports.com/library/basketball/fastdraw/409177/play-Michigan-State-Spartans--Clear-BLOB
- **M46**: FastModel 361191, "STS ATO BLOB" (8 Dec 2020). https://playbank.fastmodelsports.com/library/basketball/fastdraw/361191/play-Michigan-State-Spartans--STS-ATO-BLOB
- **M47**: FastModel 400662, "Zone Lob (Michigan State)" (22 Dec 2021; outside coach). https://playbank.fastmodelsports.com/library/basketball/fastdraw/400662/play-Zone-Lob--Michigan-State-
- **M48**: FastModel 473108, "Zone Offense – Izzo 2" (not an MSU game set). https://playbank.fastmodelsports.com/library/basketball/fastdraw/473108/play-Zone-Offense--Izzo-2
- **M49**: FastModel 487398, "MICHIGAN CHICAGO SPLIT" (Michigan; excluded). https://playbank.fastmodelsports.com/library/basketball/fastdraw/487398/play-MICHIGAN-CHICAGO-SPLIT
- **M50**: FastModel PlayBank search listings used to enumerate MSU entries (no MSU entry after 13 Mar 2025). https://playbank.fastmodelsports.com/library/basketball/search/michigan%20state?page=1
- **M52**: YouTube Michigan (not MSU) clips, thumbnails inspected: https://www.youtube.com/watch?v=h6m2GwdTYak ; https://www.youtube.com/watch?v=cKyBtUPV4s8 ; https://www.youtube.com/watch?v=EyLXp9Kw0eU
- **M69**: Hoopscoop, Tom Izzo Open Practice description (posted 2015; pre-window). https://www.mensbasketballhoopscoop.com/?p=23659

**Big Ten note (`[B#]`; numbering follows the Big Ten research note; "FM" = FastModel PlayBank)**
- **B1**: A Quick Timeout, "Inside Dusty May's OOB Playbook" (Tony Miller, 12 Feb 2026). https://aquicktimeout.substack.com/p/inside-dusty-mays-oob-playbook — Michigan 2025-26 Double Elevator BLOB (PGC post 14 Jan 2026, 423K views); 3 Low Flare BLOB steps; rest paywalled.
- **B2**: FM "Purdue Boilermakers - Stack Under '3'" (03/16/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461389/play-Purdue-Boilermakers--Stack-Under-3- — box with 2 at the elbow; full step list (3.3).
- **B3**: FM "NCAA Illinois Ram PnR" (01/27/2025). https://playbank.fastmodelsports.com/library/basketball/fastdraw/476681/play-NCAA-Illinois-Ram-PnR — Illinois 2024-25 ram → PnR, 4 exits top.
- **B4**: FM "Purdue Boilermakers - Horns Spread PNR" (03/31/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462363/play-Purdue-Boilermakers--Horns-Spread-PNR — A-set evens right/odds left; 4 sprints to post; 5 pick-and-pop reversal/iso; rip and drive.
- **B5**: FM "Purdue Boilermakers - Horns Spain" (04/01/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462377/play-Purdue-Boilermakers--Horns-Spain — Edey set, 2024 Elite Eight vs Tennessee; 5 ball screens 1, 4 Spain-screens 5.
- **B6**: FM search "purdue", pages 1–6. https://playbank.fastmodelsports.com/library/basketball/search/purdue?page=1 (…page=6) — inventory of Purdue sets and dates (83 plays).
- **B7**: FM "Purdue Boilermakers - Ram Double Ball Screen" (11/14/2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/452585/play-Purdue-Boilermakers--Ram-Double-Ball-Screen — 5 screens 4; 4 & 5 double ball screen; corner pitch.
- **B8**: FM "Purdue Boilermakers - Double Drag PNR" (12/11/2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/455733/play-Purdue-Boilermakers--Double-Drag-PNR — NCAA 2023-24; 5 screens 3; 3 & 5 stagger for 4; double drag.
- **B9**: FM "Purdue Boilermakers - Stagger Curl Through" (03/31/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462338/play-Purdue-Boilermakers--Stagger-Curl-Through — vs Gonzaga; full step list.
- **B10**: FM "Purdue Boilermakers - Double High PNR" (04/01/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462387/play-Purdue-Boilermakers--Double-High-PNR — 1–4 PnR, 4 low post, 1–5 PnR, 2 lifts.
- **B11**: FM "Purdue Boilermakers - Duck In BLOB" (03/28/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462147/play-Purdue-Boilermakers--Duck-In-BLOB — Edey decoy; 4 into space; 1 safety; 5 high post.
- **B12**: FM "Purdue Boilermakers - Stack Curl BLOB" (03/28/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462148/play-Purdue-Boilermakers--Stack-Curl-BLOB — diagonal stack inside the arc; double stagger to corner; STS pop; 4-out 1-in.
- **B13**: FM "Purdue Boilermakers - 3 Out Football Press Break" (04/06/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462617/play-Purdue-Boilermakers--3-Out-Football-Press-Break — EOG press break steps.
- **B14**: FM "Illinois Fighting Illini - Swing Iso PNP" (03/25/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461842/play-Illinois-Fighting-Illini--Swing-Iso-PNP — PnP, backdoor, reversal, second PnP.
- **B15**: FM "Illinois Fighting Illini - Pistol Flare Curl" (03/24/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461792/play-Illinois-Fighting-Illini--Pistol-Flare-Curl — pistol special; curl the flare; empty weak side; lob.
- **B16**: FM "Illinois Fighting Illini - Winner SLOB" (03/30/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462287/play-Illinois-Fighting-Illini--Winner-SLOB — inverted stagger; lob to 5.
- **B17**: FM "Illinois Fighting Illini - Stagger Twist BLOB" (03/24/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461752/play-Illinois-Fighting-Illini--Stagger-Twist-BLOB — stagger curl; 5 screens 4 then slips.
- **B18**: FM "Illinois Fighting Illini - Stack Curl BLOB" (03/28/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462142/play-Illinois-Fighting-Illini--Stack-Curl-BLOB — Illinois men, 2024 NCAA; 1/2 read, curl/seal, corner.
- **B19**: FM "Michigan Jet" (03/22/2025). https://playbank.fastmodelsports.com/library/basketball/fastdraw/478445/play-Michigan-Jet — Michigan vs UC San Diego 2025 NCAA; stack sprint, baseline run, reject, catch-and-shoot.
- **B20**: FM "Michigan Pin Down BLOB" (03/24/2025). https://playbank.fastmodelsports.com/library/basketball/fastdraw/478546/play-Michigan-Pin-Down-BLOB — vs Texas A&M; alignment and steps.
- **B21**: FM "Maryland - SLOB Top Iso" (03/24/2025). https://playbank.fastmodelsports.com/library/basketball/fastdraw/478543/play-Maryland--SLOB-Top-Iso — Queen game-winner, down 1, 3.7 s.
- **B22**: FM "IOWA STS" (02/17/2026). https://playbank.fastmodelsports.com/library/basketball/fastdraw/486730/play-IOWA-STS — "NCAA 2025-26 IOWA set" (gender not stated); steps.
- **B23**: FM "Iowa - EOG Press Break 3" (03/24/2026). https://playbank.fastmodelsports.com/library/basketball/fastdraw/487411/play-Iowa--EOG-Press-Break-3 — vs Florida, down 2, 8.9 s; steps.
- **B24**: FM "Rutgers - Iverson PnR Under" (03/01/2025). https://playbank.fastmodelsports.com/library/basketball/fastdraw/477909/play-Rutgers--Iverson-PnR-Under — 2024-25 base action; steps.
- **B25**: FM "Michigan Wolverines - Back Screen Stagger BLOB" (02/07/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/459348/play-Michigan-Wolverines--Back-Screen-Stagger-BLOB — steps.
- **B26**: FM "Michigan Wolverines - Horns Quick Hitter" (01/18/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/458612/play-Michigan-Wolverines--Horns-Quick-Hitter — EOQ steps.
- **B27**: FM "Nebraska Cornhuskers - BLOB" (03/22/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461703/play-Nebraska-Cornhuskers--BLOB — steps.
- **B28**: FM "Nebraska Cornhuskers - Stagger to Horns Back Screen" (03/21/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461608/play-Nebraska-Cornhuskers--Stagger-to-Horns-Back-Screen — concept (tweet 12 Feb 2024).
- **B29**: FM "Northwestern Wildcats - Triple Curl BLOB" (01/17/2025). https://playbank.fastmodelsports.com/library/basketball/fastdraw/476282/play-Northwestern-Wildcats--Triple-Curl-BLOB — MBB; 0.7 s; steps.
- **B30**: FM "Northwestern Wildcats - Floppy UCLA" (03/26/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461956/play-Northwestern-Wildcats--Floppy-UCLA — BLOB chain steps.
- **B31**: FM "Northwestern Wildcats - Iverson Elevator" (03/21/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461605/play-Northwestern-Wildcats--Iverson-Elevator — Iverson curl → flare → elevator (tweet 9 Mar 2024).
- **B32**: FM "Oregon Ducks - Back Screen Lob" (04/19/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/463199/play-Oregon-Ducks--Back-Screen-Lob — clear the right side, back-screen lob (tweet 21 Mar 2024).
- **B33**: FM "Wisconsin Badgers - Post Up" (01/22/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/458848/play-Wisconsin-Badgers--Post-Up — NCAA 2023-24; cross-screen post steps.
- **B34**: FM "Wisconsin Badgers - Chicago Action" (01/22/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/458847/play-Wisconsin-Badgers--Chicago-Action — NCAA 2023-24; Chicago steps.
- **B35**: FM "Michigan St. 2le High Trade" (03/04/2025). https://playbank.fastmodelsports.com/library/basketball/fastdraw/478091/play-Michigan-St-2le-High-Trade — MSU 2024-25 double-high PnR with trade.
- **B36**: FM "Michigan State Spartans - EOQ Horns Set" (03/21/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461638/play-Michigan-State-Spartans--EOQ-Horns-Set — 4 & 5 cross into ball screens (already repo O89).
- **B37**: FM "Michigan State Spartans - 1-4 STS" (03/21/2024). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461577/play-Michigan-State-Spartans--1-4-STS — full description; "Izzo staple".
- **B38**: FM "Michigan State Vs Zone" (03/13/2025). https://playbank.fastmodelsports.com/library/basketball/fastdraw/478264/play-Michigan-State-Vs-Zone — 2024-25 swallow-cut zone set.
- **B39**: FM "Purdue Boilermakers - Iverson Spread Ball Screen" (01/12/2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/433667/play-Purdue-Boilermakers--Iverson-Spread-Ball-Screen — steps [pre-window].
- **B40**: FM "Purdue Boilermakers - Spread Lift Slip" (01/12/2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/433669/play-Purdue-Boilermakers--Spread-Lift-Slip — steps [pre-window].
- **B41**: FM "Purdue Boilermakers - Ram Fake Lob" (01/12/2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/433668/play-Purdue-Boilermakers--Ram-Fake-Lob — steps [pre-window].
- **B42**: FM "Purdue Boilermakers - Double High Pin" (01/30/2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/435106/play-Purdue-Boilermakers--Double-High-Pin — 4 & 5 lift to elbows; steps [pre-window].
- **B43**: Inside NU, "Collins' Classroom: Martinelli's mismatches" (13 Dec 2024). https://insidenu.com/2024/12/13/24319739/collins-classroom-martinellis-mismatches — Northwestern OT switch-hunt (6 possessions); Iowa fake pin-down + slipped tandem top screen.
- **B44**: A Quick Timeout, "Fred Hoiberg's 5-Out Offense" (13 Jan 2026). https://aquicktimeout.substack.com/p/fred-hoibergs-5-out-offense — 5-out ATO steps (DHO with 5, weak-corner back screen, inverted stagger); paywalled rest.
- **B45**: A Quick Timeout, "Friday's 4 Xs & Os: Fred Hoiberg's 5-Out Offense" (15 Mar 2024). https://aquicktimeout.substack.com/p/fridays-4-xs-and-os-fred-hoibergs — "Dribble at Burn" steps.
- **B46**: A Quick Timeout, "Niko Medved's Chin Quick Hitters" (3 Jan 2026). https://aquicktimeout.substack.com/p/niko-medveds-chin-quick-hitters — Minnesota Chin variant (1 to weak corner; 4 flare then slip).
- **B47**: A Quick Timeout, "Friday's 4 Xs & Os: Niko Medved's …" (17 Nov 2023). https://aquicktimeout.substack.com/p/fridays-4-xs-and-os-niko-medveds — CSU Chin → Point Over fake DHO backdoor.
- **B48**: Hammer & Rails, "Matt Painter Starts with Something Different Against McNeese" (25 Mar 2025). https://www.hammerandrails.com/2025/3/25/24394085/purdue-basketball-matt-painter-starts-with-something-different-against-mcneese — Purdue base high PnR tendency; fake pin-down post-up steps.
- **B49**: Hammer & Rails, "Are the Boilers more Methodical or Just Slower on Offense this Season?" (2 Jan 2025). https://www.hammerandrails.com/2025/1/2/24333269/are-the-boilers-more-methodical-or-just-slower-on-offense-this-season — AdjO 10th, tempo 307th.
- **B50**: Hammer & Rails, "Purdue vs Indiana: Film Room - Indiana Side Pick and Roll / Dribble Hand-Off" (15 Jan 2024). https://www.hammerandrails.com/2024/1/15/24039367/purdue-vs-indiana-film-room-indiana-side-pick-and-roll-dribble-hand-off — Indiana big-handled side DHO to FT line.
- **B51**: Hammer & Rails, "Purdue Basketball: Penn State Preview" (5 Dec 2024). https://www.hammerandrails.com/2024/12/5/24314173/purdue-basketball-penn-state-preview — Penn State 5-out open post, Baldwin–YKN PnR lobs, corner Hicks, cuts, diamond press.
- **B52**: Hammer & Rails, "Game Preview - #4 Purdue at UCLA" (20 Jan 2026). https://www.hammerandrails.com/mens-basketball/57746/game-preview-4-purdue-at-ucla — UCLA low 3PA, weak DReb; Purdue "nation's best offense".
- **B53**: The Champaign Room, "Scouting Alabama as Illinois looks for another top-15 win" (18 Nov 2025). https://www.thechampaignroom.com/illinois-fighting-illini-basketball-news/48791/scouting-alabama-as-illinois-looks-for-another-top-15-win-fighting-illini-ncaa-big-ten-crimson-tide — Wagler wing ball screens; Mirkovic short roll vs trap; Kaufman-Renn short roll vs Alabama blitz; Illinois corner OREB crash.
- **B54**: The Champaign Room, "David Mirkovic: Illinois' freshman who can do it all" (20 Feb 2026). https://www.thechampaignroom.com/illinois-fighting-illini-basketball-news/51842/david-mirkovic-illinois-freshman-who-can-do-it-all — Mirkovic 39% 3P on 4 att/g, secondary handler, passer.
- **B55**: The Champaign Room, "How Tyler Underwood helped build Illinois' historically efficient offense" (29 Jan 2026). https://www.thechampaignroom.com/illinois-fighting-illini-basketball-news/51129/how-tyler-underwood-helped-build-illinois-historically-efficient-offense-fighting-illini-ncaa-big-ten — Gold/Silver/Bronze shot framework; AdjO 130.5.
- **B56**: The Champaign Room, "Analyzing Underwood's Illinois offense isn't as simple as you think" (14 Feb 2025). https://www.thechampaignroom.com/2025/2/14/24365148/analyzing-underwoods-offense-for-illinois-isnt-as-simple-as-youve-been-told-big-ten-ncaa-jakucionis — 2024-25 conference 3P% 29.4%; no set detail.
- **B57**: SI (J. Langendorf), "Iowa Coach Ben McCollum Reveals What Sets Illinois' Offense Apart" (12 Jan 2026). https://www.si.com/college/illinois/basketball/iowa-coach-ben-mccollum-reveals-what-sets-illinois-offense-apart — Mirkovic post + pick-and-pop; second 2.18 m pick-and-pop big; downhill Stojakovic/Boswell; KenPom O No. 3.
- **B58**: SI, "Wisconsin Badgers plan to stick with small-ball lineup that gave Michigan fits" (12 Jan 2026). https://www.si.com/college/wisconsin/basketball/badgers-stick-with-small-ball-lineup-that-gave-michigan-fits — four-guard lineup stats and reads.
- **B59**: Action Network (K. McKeon), "Marquette vs Wisconsin Predictions…" (6 Dec 2025). https://www.actionnetwork.com/ncaab/marquette-golden-eagles-vs-wisconsin-badgers-predictions-picks-odds-college-basketball-saturday-december-6 — Wisconsin "a ton of pick-and-roll and pick-and-pop"; top-15 3PA rate.
- **B60**: Hail Varsity / Hurrdat, "Nebraska Men's Basketball Opponent Breakdown: Iowa" (25 Mar 2026). https://hurrdatsports.com/hailvarsity/mens-basketball/nebraska-mens-basketball-opponent-breakdown-iowa/ — Iowa possession length 19.9 s, tempo 62.7, eFG 56.3%; Stirtz ball screens, pocket/elbow passes, short roll + cutter, switch hunting; Folgueiras pick-and-pop; OREB.
- **B61**: SI, "Early Trends in Iowa's Ben McCollum Era" (9 Nov 2025). https://www.si.com/college/iowa/basketball/early-trends-iowa-hawkeyes-ben-mccollum-era — Stirtz ball-dominant role.
- **B62**: Staking the Plains, "A Preview of the Texas Tech Offense, Inspired by NW Missouri St?" (18 Aug 2021). https://stakingtheplains.com/2021/08/18/texas-tech-basketball-a-preview-of-the-texas-tech-offense-inspired-by-nw-missouri-st/ — McCollum: ball screens without set pattern; versatile screeners.
- **B63**: Cracked Sidewalks, "Maryland Preview 2025-26" (Sep 2025, updated early season). https://www.crackedsidewalks.com/2025/09/maryland-preview-2025-26.html — Maryland ball-screen initiation, OREB identity, A&M stats.
- **B64**: Cracked Sidewalks, "Indiana Preview 2025-26". https://www.crackedsidewalks.com/2025/09/indiana-preview-2025-26.html — drive-and-kick, cuts, pick-and-pop; threes vs under; backdoor twos.
- **B65**: W. McDermott (Substack), "Darian DeVries: The offense" (25 Mar 2025). https://williammcdermottiubb.substack.com/p/darian-devries-the-offense — slip and ghost screens, off-ball screens, skips, backdoor.
- **B66**: MGoBlog (Brian), "Hoops Preview: Nebrasketball, 2025-26" (27 Jan 2026; opened in browser). https://mgoblog.com/content/hoops-preview-nebrasketball-2025-26 — Nebraska 51% 3PA, no OREB, stretch-5 Mast, Sandfort.
- **B67**: Michigan Daily, "Stellar playmaking powers Michigan to victory over Howard" (20 Mar 2026). https://www.michigandaily.com/sports/mens-basketball/stellar-playmaking-powers-michigan-to-victory-over-howard/ — Mara high-post hub, cutters, lobs, backdoor.
- **B68**: Michigan Daily, "Michigan and Connecticut's competing philosophies vying for national championship" (5 Apr 2026). https://www.michigandaily.com/sports/mens-basketball/michigan-and-connecticuts-competing-philosophies-vying-for-national-championship/ — transition lanes; "We don't play with sets or plays"; Purdue plays through PG; Iowa slow.
- **B69**: Michigan Daily, "Michigan transition offense takes leap in second game" (13 Nov 2025). https://www.michigandaily.com/sports/mens-basketball/michigan-transition-takes-leap-in-second-game/ — Mara outlet to Lendeborg; 27 fast-break points.
- **B70**: Stats By Will, "How a Dusty May masterclass sent Michigan to the Sweet Sixteen" (25 Mar 2025). https://statsbywill.substack.com/p/how-a-dusty-may-masterclass-sent — Michigan 2024-25 shot sources (post kickouts, off-ball screens; spot-up 13th pct).
- **B71**: Daily Bruin, "UCLA men's basketball 2025-26 roster breakdown" (30 Oct 2025). https://dailybruin.com/2025/10/30/ucla-mens-basketball-2025-26-roster-breakdown — Dent transition and top PnR; Booker shooting centre.
- **B72**: SI, "Sprinkle Promises Next Huskies Will Play at Much Faster Pace" (2 Jul 2025). https://www.si.com/college/washington/basketball/sprinkle-promises-next-huskies-will-play-at-much-faster-pace-01jz35s8ymsp — Washington 2025-26 intent.
- **B73**: Slappin' Glass, "The Ghost Flare: A Primer" (28 Mar 2021). https://slappinglass.substack.com/p/the-ghost-flare-a-primer?r=8c8kg — ghost flare definition; no Big Ten team (context only; not used as team evidence).
- **B74**: Men's Basketball Hoop Scoop, "Dana Altman Oregon Ducks Spread Offense" (21 Feb 2017). https://www.mensbasketballhoopscoop.com/dana-altman-oregon-ducks-spread-offense/ — Altman spread roots [pre-window].
- **B75**: Hammer & Rails, "Matt Painter's masterpiece and master class against the NCAA" (30 Dec 2025). https://www.hammerandrails.com/mens-basketball/57409/matt-painters-masterpiece-and-master-class-against-the-ncaa — no set detail (checked).
- **B76**: CBS Sports, "The unique tweak that could send Purdue on a deep NCAA Tournament run" (9 Mar 2017). https://www.cbssports.com/college-basketball/news/the-unique-tweak-that-could-send-purdue-on-a-deep-ncaa-tournament-run — out of window; no set detail.
- **B77**: FM "Purdue Boilermakers - Rip DHO Triple" (03/29/2019). https://playbank.fastmodelsports.com/library/basketball/fastdraw/288918/play-Purdue-Boilermakers--Rip-DHO-Triple — out of window.
- **B78**: FM search listings opened (inventory/dates): https://playbank.fastmodelsports.com/library/basketball/search/michigan%20wolverines?page=1 (and page 2); …/search/illinois?page=1; …/search/wisconsin?page=1; …/search/illinois%20fighting%20illini?page=1; …/search/wisconsin%20badgers?page=1; …/search/maryland%20terrapins; …/search/indiana%20hoosiers; …/search/iowa%20hawkeyes; …/search/ohio%20state%20buckeyes; …/search/nebraska%20cornhuskers; …/search/northwestern%20wildcats; …/search/rutgers; …/search/penn%20state; …/search/minnesota%20gophers; …/search/ucla%20bruins; …/search/usc%20trojans; …/search/oregon%20ducks; …/search/washington%20huskies; …/search/NCAA%202024-25; …/search/NCAA%202025-26; plus single-word and coach-name queries (cronin, altman, hoiberg, pikiell, rhoades, sprinkle, musselman, diebler, gard, willard, woodson, mccaffery, underwood, painter, buckeyes, terrapins, trojans, bruins, ducks, hawkeyes, nittany) — confirmed which in-window entries exist and their dates; Justin Lewis contributor page https://playbank.fastmodelsports.com/library/contributors/651a59abe17cad27945f7fa4651b2440/Justin-Lewis-TeamFastModel.
- **B79**: Feed The Post, "Ben McCollum Breakdown" (30 Apr 2025). https://feedthepost.substack.com/p/ben-mccollum-breakdown-iowas-new — paywalled; no set detail.
- **B80**: A Quick Timeout, "4 Basketball Plays: Alabama vs. Purdue" (14 Nov 2025). https://aquicktimeout.substack.com/p/4-basketball-plays-alabama-vs-purdue — Alabama plays only before paywall.
- **B81**: A Quick Timeout, "Coach Basketball Like Dusty May" (10 Apr 2026). https://aquicktimeout.substack.com/p/coach-basketball-like-dusty-may — Michigan early-offense quick hitter exists; paywalled.
- **B82**: A Quick Timeout, "2024 NCAA Tournament Playbook" (10 Apr 2024). https://aquicktimeout.substack.com/p/2024-ncaa-tournament-playbook — paywalled.
- **B83**: UM Hoops, "Film Room: How Michigan has optimized Yaxel Lendeborg" (4 Dec 2025). https://umhoops.com/2025/12/04/film-room-how-michigan-has-optimized-yaxel-lendeborg/ — paywalled after intro.
- **B84**: CoachTube, "Matt Painter Purdue Playbook & FREE Video Playbook" (T. Bergstraser). https://coachtube.com/course/basketball/matt-painter-purdue-playbook-free-video-playbook/14996383 — no set names visible.
- **B85**: A Quick Timeout sitemaps 2023–2026. https://aquicktimeout.substack.com/sitemap/2024 (and /2023, /2025, /2026) — located Big Ten-related posts.
- **B86**: Badger Extra, "Inside assistant's worldwide journey to lead Wisconsin men's basketball's offensive evolution". https://badgerextra.com/sports/basketball/men/wisconsin-mens-basketball-offense-kirk-penney-greg-gard-elite-shooting/article_1bab0a68-dc35-11ef-a112-032b050215ce.html — body paywalled.
- **B87**: Inside the Hall film sessions: https://www.insidethehall.com/2026/02/16/film-session-how-keaton-wagler-got-to-the-rim-against-indiana/ (Wagler 15 of 18 points on drives) and https://www.insidethehall.com/2026/01/12/film-session-nebraskas-paint-touches-in-the-second-half-against-indiana/ (Nebraska paint touches off high ball screens; 53 second-half points) — video-only detail.
- **B88**: Opened FM detail pages used only for the A2 exclusion list: 458503, 462603, 461924, 461923, 460485, 461960, 458453, 454962, 454955, 457360, 458506, 471774, 471773, 454468, 452299, 455590, 455589, 460169, 455762, 455761, 461741 (all under https://playbank.fastmodelsports.com/library/basketball/fastdraw/<id>/…), plus 487399 (Iowa State, not Big Ten).
- **B89**: YouTube pages (title only visible): https://www.youtube.com/watch?v=vAQ66mdwtMc (Braden Smith breaks down game-winning play vs Texas), https://www.youtube.com/watch?v=LvEFbv88PbI (Illini Inquirer film room, big lineup at Minnesota) — no usable text.

**Ball-screen / handoff note (`[P#]`; renamed from that note's local `[B#]` keys, same numbers)**
- **P1**: Raptors Republic, "Raptors Playbook: Stack Pick and Roll" (2017). https://raptorsrepublic.com/2017/11/08/raptors-playbook-stack-pick-roll/ Confirmed:
  - "Stack PnR" = a third player screens the screener's defender.
  - Reads: dive, corner, above-break three.
  - Flow into a DHO.
- **P2**: Coach Hoops, "Spain Action". https://coachhoops.substack.com/p/spain-action Confirmed:
  - Spain roles and sequence.
  - Double/Twist/Wide/Delay/Ghost Spain definitions.
  - Counters: pre-switch, top-lock, "next".
  - Example titles: Zipper, Gut, Motion Strong-Touch, DHO-Empty.
- **P3**: FastModel, "Iowa State High Ball Screen Concepts" (2017-10-02). https://playbank.fastmodelsports.com/library/basketball/fastdraw/199779/play-High-Ball-Screen-Concepts Confirmed: Four Low; 4 sprint-screen and pop; throwback vs two-on-ball; the 5 at the dunker/"porch"; the full read tree; stack entry.
- **P4**: The Hoops Geek, "Pick & Roll in Basketball – The Ultimate Guide". https://thehoopsgeek.com/basketball-pick-and-roll Confirmed:
  - Screen angles 90/0/45°.
  - STS/"Ram" naming.
  - Short-roll and pocket pass drills.
  - Spread PnR example. (Context; not cited above.)
- **P5**: Slappin' Glass, "The Art of the Roll". https://slappinglass.substack.com/p/the-art-of-the-roll Confirmed:
  - Sprint roll, roll-and-seal, short roll near the nail.
  - Short-roller reads: finish, then "get off the ball".
  - Gortat; "get out" options (ghost, touch-and-go).
- **P6**: FastModel, "Michigan State Zone O – Short Roll" (2015-03-29). https://playbank.fastmodelsports.com/library/basketball/fastdraw/67791/play-Michigan-State-Zone-O--Short-Roll Confirmed: MSU attacks zones with high ball screens; 4 sprint-screen, short roll to the high post; DHO to the lifting 3; seal read.
- **P7**: Coach's Clipboard, "Michigan State Sets". https://coachesclipboard.net/MSUSets.html Confirmed:
  - Back-screen PnR, Detroit and 1-4 High PnR sequences.
  - Title-only MSU ball-screen plays (members).
- **P8**: Hoopscoop, "Michigan State Spartans High Ball Screen Set Plays". https://www.mensbasketballhoopscoop.com/michigan-state-spartans-high-ball-screen-set-plays/ Confirmed (2015 FF vs Duke):
  - Sprint-up screen.
  - Weave into high ball screen with roll-and-seal into the 4's area.
  - Sprint-up plus stagger.
  - The 5 starts on the block.
- **P9**: Hoop Vision, "The Corner Step-Up" (J. Sperber, 2024-01-15). https://hoopvision.substack.com/p/the-corner-step-up Confirmed: guard corner step-up, hard or ghost; Marquette, Texas A&M and Houston examples; "Continuity Step-Up" name (rest paywalled).
- **P10**: Hoop Vision, "The Ball Screen Revolution (HV Weekly 8/9/2020)". https://hoopvision.substack.com/p/the-ball-screen-revolution-hv-weekly Confirmed:
  - ~9 ball screens per game in 2010, doubling.
  - Probe actions; pace-based ball-screen offense.
  - Spread ball screen; "dummy ball screen" (section name).
  - Usage-share data.
- **P11**: Hoop Vision, "Ball Screen Essentials (7/7/19)". https://hoopvision.substack.com/p/hoop-vision-weekly-ball-screen-essentials Confirmed: 2018-19 PPP by ball-screen outcome; team examples.
- **P12**: Hoop Vision, "The Starting Five: Ball Screen Outliers" (2020-03-02, preview). https://hoopvision.substack.com/p/the-starting-five-ball-screen-outliers Confirmed: NCAA average ≈ 20 ball screens used per game.
- **P13**: Coach Hoops, "Zoom Action". https://coachhoops.substack.com/p/zoom-action Confirmed: zoom definition and reads; Zoom Reject sequence; teams (Alabama, Baylor, Kentucky/Pope, Florida, Gonzaga).
- **P14**: A Quick Timeout, "Inside March Madness: First Round Xs & Os" (2023-03-17). https://aquicktimeout.substack.com/p/inside-march-madness-first-round Confirmed:
  - Kansas ghost → back screen → middle ball screen.
  - Charleston cleared side plus triple stagger.
  - Duke stack back-screen lob.
- **P15**: theScore, "How the keeper play became a weapon for modern big men". https://www.thescore.com/nba/news/2872869/how-the-keeper-play-became-a-weapon-for-modern-big-men Confirmed: keeper mechanics; DHO rate data (NBA).
- **P16**: Slappin' Glass, "Double Drag Screens: A Primer". https://slappinglass.substack.com/p/double-drag-screens-a-primer Confirmed:
  - 77 geometry (first screener a body length higher).
  - Counters.
  - Johns Hopkins pop-and-flare (empty corner); Swarthmore 77 Wall (filled corner).
  - ASVEL flows; Looney short-roll choice.
- **P17**: FastModel, "North Carolina Tar Heels – Horns Double Ball Screen" (2022-03-26). https://playbank.fastmodelsports.com/library/basketball/fastdraw/409840/play-North-Carolina-Tar-Heels--Horns-Double-Ball-Screen Confirmed: DHO then 5+4 double ball screen; 5 rolls, 4 pops.
- **P18**: FastModel, "Ohio Bobcats – Horns Double Ball Screen" (2021-03-22). https://playbank.fastmodelsports.com/library/basketball/fastdraw/373648/play-Ohio-Bobcats--Horns-Double-Ball-Screen Confirmed: 5 then 4 sequential screens; roll/pop; drift on the drive.
- **P19**: FastModel, "Texas A&M – Stack Roll Duck" (2016-03-19). https://playbank.fastmodelsports.com/library/basketball/fastdraw/123720/play-Texas-A-M--Stack-Roll-Duck Confirmed: 1 moves under 5; 5 rolls around 1 to the block; 1 pops for the post pass.
- **P20**: Brian Geisinger, "Breaking down 2 of Will Wade's go-to ball screen sets". https://briangeisinger.substack.com/p/breaking-down-2-of-will-wades-go Confirmed: Horns Twist Leak (LSU 2021-22, McNeese 2024-25); Angle Pop (NC State 2024-25, Texas Tech 2024-25).
- **P21**: UM Hoops (p=72524), Michigan shake ball screen (2015-16). https://umhoops.com/?p=72524 Confirmed: fake wide pin-down, then sprint into a spread ball screen; hand-shake signal; soft-hedge/drop counter; re-screen counter.
- **P22**: Hoop Vision, "Countering Switches" (2024-02-27, preview). https://hoopvision.substack.com/p/countering-switches Confirmed only: screen-your-own-man, boomerang and hi-lo listed vs switches; BYU/Duke concept paywalled.
- **P23**: Hoop Vision, "Ball Screen Revolution: Part 2". https://hoopvision.substack.com/p/ball-screen-revolution-part-2 Confirmed:
  - Duke 2001 roll-replace; Maryland 2002 flex roll-replace.
  - Syracuse 2003 PnR plus cross screen.
  - Georgia Tech 2004 empty ball screens with weak-side stagger.
  - UNC 2005 Spain in secondary; Florida 2006 pick-and-pop; Ohio State 2007 spread.
- **P24**: The Hoosier Network, "IUBB Purdue film preview" (Feb 2023). https://thehoosiernetwork.com/article/2023/02/iubb-purdue-film-preview Confirmed: wing pin-down for Edey into the ball screen (head start); roll plus lift; Spain when the back screen is added.
- **P25**: FastModel, "Stack Spain" (2016-02-27). https://playbank.fastmodelsports.com/library/basketball/fastdraw/121289/play-Stack-Spain Confirmed: 3 screens 5 into the ball screen; 2 back-screens X5; Spain NT, EuroBasket 2015 final.
- **P26**: HoopStudent, "Basketball roll and replace". https://hoopstudent.com/basketball-roll-and-replace Confirmed: definition, alignment, timing too early/late, opposite-side replace, counters.
- **P27**: FastModel, "Ole Miss Curl Roll-Replace" (2015-03-18). https://playbank.fastmodelsports.com/library/basketball/fastdraw/66574/play-Ole-Miss-Curl-Roll-Replace Confirmed: curl/baseline-screen decoy; 5 circles into a middle PnR; 4 slides under and replaces high.
- **P28**: FastModel, "Texas A&M – Rub Roll/Replace" (2016-03-19). https://playbank.fastmodelsports.com/library/basketball/fastdraw/123718/play-Texas-A-M--Rub-Roll-Replace Confirmed: 2 runs in front of the ball screen; 5 rolls; 4 fills up from the block.
- **P29**: FastModel, "Wisco On-Ball Flare" (2015-05-11). https://playbank.fastmodelsports.com/library/basketball/fastdraw/71425/play-Wisco-On-Ball-Flare Confirmed: roll-replace variant; 4 flares the rolling 5 (Kaminsky) to the wing, then rolls; vs Kentucky.
- **P30**: FastModel, "Notre Dame – High Roll Replace" (2016-03-23). https://playbank.fastmodelsports.com/library/basketball/fastdraw/124494/play-Notre-Dame--High-Roll-Replace Confirmed: 4 screens and rolls; 5 replaces.
- **P31**: FastModel, "Drag 'BLUE'" (2020-10-29). https://playbank.fastmodelsports.com/library/basketball/fastdraw/354342/play-Drag-BLUE- Confirmed: blue = fake ball screen, red = real; fake drag, pass, flare for the passer.
- **P32**: FastModel, "Louisville DHO Wheel" (2016-02-09). https://playbank.fastmodelsports.com/library/basketball/fastdraw/118718/play-Louisville-DHO-Wheel Confirmed: DHO, then wing cuts; "wheel" undefined.
- **P33**: FastModel, "Fake DHO Clear Out" (2022). https://playbank.fastmodelsports.com/library/basketball/fastdraw/410865/play-Fake-DHO-Clear-Out Confirmed: wing fake hand-off, then baseline drive as misdirection.
- **P34**: Coach's Clipboard, "Basketball ghost screens". https://www.coachesclipboard.net/basketball-ghost-screens.html Confirmed: ghost definition; flare/slip follow-ups; double ghost; works vs switching.
- **P35**: Hoop Vision, "The Short Roll" (2024-02-05, preview). https://hoopvision.substack.com/p/the-short-roll Confirmed: Kansas short roll vs Houston blitz (2023-24); KJ Adams; 1.22 PPP / 75.6% eFG.
- **P36**: FastModel, "Washington Wizards – Angle Short" (2017-04-16). https://playbank.fastmodelsports.com/library/basketball/fastdraw/183825/play-Washington-Wizards--Angle-Short Confirmed: 4 "shorts" to the dunker/"Ghost" spot; elbow-angle screen; lob vs hedge.
- **P37**: FastModel, "Hand Off with Ball Screen" (Duke 2005-06). https://playbank.fastmodelsports.com/library/basketball/fastdraw/1175/play-Hand-Off-with-Ball-Screen Confirmed: hand-off, then a third-player ball screen; "basically a double ball screen" vs denial.
- **P38**: Daily Bruin, "Scouting report: UCLA vs Michigan State" (2026-02-17). https://dailybruin.com/2026/02/17/scouting-report-ucla-mens-basketball-vs-michigan-state Confirmed: Fears 9.2 APG, lobs to bigs; Kohler 40.8% 3P, slips screens to the 3-point line; MSU adjusted offense/tempo.
- **P39**: SI (J. Cotsonika, 2025-12-26), "MSU Needs Jeremy Fears Jr. to Break Out of Shooting Slump". https://www.si.com/college/michiganstate/msu-needs-jeremy-fears-jr-break-out-shooting-slump- Confirmed: defenders going under Kohler/Cooper screens cuts off roller passes; assist decline.
- **P40**: Slappin' Glass, "'Attacking the Tag' Primer". https://slappinglass.substack.com/p/attacking-the-tag-concepts-and-actions Confirmed: the 12 tag-attack concepts (high lift, dunker shadow, elbow release, Obradović spacing, baseline cut, 45 cut, burn cut, shallow cut, Spain release, veer, ghost, flare-and-drift).
- **P41**: Hoop Vision, "Breaking Down the Elite Eight" (2024-04-02). https://hoopvision.substack.com/p/breaking-down-the-elite-eight Confirmed: Purdue "spammed" Spain in the 2nd half vs Tennessee; Gillis back-screener (48% 3P); Smith "Angle" pivot to Edey.
- **P42**: FastModel, "Horns Ball Screen – Roll/Pop Into Duck & Pins" (2022-01-06). https://playbank.fastmodelsports.com/library/basketball/fastdraw/402273/play-Horns-Ball-Screen--Roll-Pop-Into-Duck--Pins Confirmed: roll/pop creates "4 around 1"; high-low; DHO; pins.
- **P43**: FastModel, "Horns Staggered Pick and Roll" (Virginia Union WBB, 2016). https://playbank.fastmodelsports.com/library/basketball/fastdraw/123621/play-Horns-Staggered-Pick-and-Roll Confirmed: big-big stagger ball screen to avoid switches. Not D-I men; context only.
- **P44**: A Quick Timeout, "Inside Euro Ball Screen Offense". https://aquicktimeout.substack.com/p/inside-euro-ball-screen-offense Confirmed: empty-side PnR popular in the 2024 NCAAT; UNC Ryan back-screens Bacot, who chooses block or empty-side PnR with Davis (already in the repo as S54).
- **P45**: FastModel, "Michigan State – Horns Pistol" (2017-03-19). https://playbank.fastmodelsports.com/library/basketball/fastdraw/180888/play-Michigan-State--Horns-Pistol Confirmed: MSU vs Kansas 2017; flare misdirection; DHO 4 → 2 with 5 trailing into a ball screen and roll.
- **P46**: FastModel, "Michigan State Spartans – Horns Out Slip" (2019-04-04). https://playbank.fastmodelsports.com/library/basketball/fastdraw/289792/play-Michigan-State-Spartans--Horns-Out-Slip Confirmed: 5 screens 4; 4 out-cuts; 5 slips the ball screen for the dunk; 2019 Elite Eight vs Duke.
- **P47**: FastModel, "Michigan State Spartans – Zipper Spain PNR SLOB" (2023-03-17). https://playbank.fastmodelsports.com/library/basketball/fastdraw/437680/play-Michigan-State-Spartans--Zipper-Spain-PNR-SLOB Confirmed: zipper, DHO, post flash, side Spain PnR.
- **P48**: FastModel, "Michigan State Spartans – Horns Swing Pistol" (2019-02-25). https://playbank.fastmodelsports.com/library/basketball/fastdraw/285961/play-Michigan-State-Spartans--Horns-Swing-Pistol Confirmed: the full 6-step sequence; for Cassius Winston.
- **P49**: FastModel, "Michigan State Spartans – Stagger Slip Curl & Pop" (2022-03-20). https://playbank.fastmodelsports.com/library/basketball/fastdraw/409321/play-Michigan-State-Spartans--Stagger-Slip-Curl--Pop Confirmed: stagger, slip by 4, down screen by 5, pop for 4.
- **P50**: FastModel, "Michigan State Spartans – Miles Bridges Set" (2018). https://playbank.fastmodelsports.com/library/basketball/fastdraw/261948/play-Michigan-State-Spartans--Miles-Bridges-Set Confirmed: back-screen/cross/down-screen ATO (no ball screen). Context only.
- **P51**: FastModel, "Michigan State Spartans – 1-4 STS" (2024-03-21). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461577/play-Michigan-State-Spartans--1-4-STS Confirmed: STS, then "post re-screens and goes into roll/replace"; "Izzo staple over the last 15 years".
- **P52**: FastModel, "Motion Go Duck-In" (MSU, 2013-03-08). https://playbank.fastmodelsports.com/library/basketball/fastdraw/1716/play-Motion-Go-Duck-In Confirmed: dribble-at; 5 sprints into a middle PnR; weak-side pin-down throwback; duck-in.
- **P53**: FastModel, "New Mexico State Horns Slip" (2015-03-20). https://playbank.fastmodelsports.com/library/basketball/fastdraw/66939/play-New-Mexico-State-Horns-Slip Confirmed: fake 4's screen, 4 slips to the opposite block, use 5, 5 down-screens the corner.
- **P54**: FastModel, "Miami – Stagger Slip" (2016-03-24). https://playbank.fastmodelsports.com/library/basketball/fastdraw/124662/play-Miami--Stagger-Slip Confirmed: Villanova iced the first screen; 4 slipped to the rim.
- **P55**: FastModel, "Cal State Bakersfield – Chicago Pin" (2016-03-18). https://playbank.fastmodelsports.com/library/basketball/fastdraw/123702/play-Cal-State-Bakersfield--Chicago-Pin Confirmed: DHO, then a follow ball screen by 4, then 4 down-screens 5.
- **P56**: FastModel, "Oregon – Slice Twist" (2016-03-15). https://playbank.fastmodelsports.com/library/basketball/fastdraw/123146/play-Oregon--Slice-Twist Confirmed: two back screens by 5, ball screen, re-screen, roll.
- **P57**: Hooper University, "Ball Screen Offense—Spain Pick and Roll Explained". https://www.hooperuniversity.com/breakdowns/ball-screen-offense-spain-pnr-explained Confirmed:
  - Simultaneous screens.
  - Corner spacing.
  - Hard-hedge release read.
  - Scariolo/2016 attribution.
- **P58**: Coach's Clipboard, "Spain pick and roll". https://www.coachesclipboard.net/spain-pick-and-roll.html Confirmed: base Spain reads; Michigan "Wolverine" big-on-big Spain variation.
- **P59**: HoopStudent, "Basketball pick and pop". https://hoopstudent.com/basketball-pick-and-pop/ Confirmed: pop destinations by screen type (high, flat, side ×2, step-up ×2, corner ×3, pass-and-follow, ram, double drag, drag).

**Off-ball note (`[X#]`; numbering follows the off-ball research note; pages that returned 403/404/DNS errors there — its items 6, 23, 40, 55, 59, 82, 83, 84, 85 — are omitted and every claim that depended on them is marked unverified above)**
- **X1**: https://assets.fiba.basketball/image/upload/documents-corporate-regional-offices-europe-programs-fiba-europe-coaching-certificate-fiba-europe-basketball-terminology.pdf — WebFetch saved the PDF; text extracted locally with pdftotext. Confirmed definitions: off-ball screens (back, blade, brush, containing/hostage, cross, double/parallel, down/pin down, elevator, flare, hammer, RAM, Ricky, rip, shot, staggered, screen away, screen your own, STS, twirl, UCLA/up, veer, wide, wiper), cuts (banana, backdoor, basket, curl, fade/flare, flash, flex, I-cut, Iverson, pop-out, shuffle, shallow, UCLA, V/L), blind pig action and pass, floppy action, shake action, split action (straight/reverse), zipper, zoom, pinch post, baseline exit, slip. "Turnout", "loop", "pin-in", "Laker" and "rub" do not appear.
- **X2**: https://www.celticsblog.com/2023/12/31/23995553/a-glossary-of-xs-and-os-terms-boston-celtics-joe-mazzulla — WebFetch 403; opened with curl. Confirmed: stagger ("77"), double, pin-down/corner pin, wedge, slice, gut, zipper, flex, cross, rip, Spain, flare, ghost, slip, exit, veer, stampede, 45, delayed, V/L, Ricky, Iverson (sometimes one screener), curl (hard/wide), zoom/Chicago, ghost flare.
- **X3**: https://docs.cleaningtheglass.com/pro/data-sets/off-ball-screens — CTG off-ball screen definition, 12.19 m frontcourt limit, ≤ 3 s window, precision-over-recall, error sources, 13 screen types incl. pin_in, out, middle, zipper (inbound), flags.
- **X4**: https://docs.cleaningtheglass.com/pro/data-sets/cuts — CTG basket-cut definition (excludes rolls and cuts off off-ball screens), flags (cross-court, direct, roundness); no numeric thresholds.
- **X5**: https://pmc.ncbi.nlm.nih.gov/articles/PMC12526517/ — speed-zone thresholds (< 7, 7–14, 14.1–18, > 18 km/h; sprint > 24.1 km/h) and elite peak 20–24.5 km/h.
- **X7**: https://coachesinsider.com/mens-basketball/screening-article/ — screen timing is shared; moving early = offensive foul; blind screen allows "one normal step"; cross-screen user waits then accelerates; jab-step set-up on down screens.
- **X8**: https://hoopstudent.com/basketball-laker-cut/ — Laker cut sequence, high-side vs low-side versions, Showtime attribution.
- **X9**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/251724/play-Pass-into-the-Post--Laker-Cut — Laker cut after a post entry (2018), 1 cuts off the post.
- **X10**: https://hoopstudent.com/basketball-blind-pig/ — blind pig triangle sequence and roles.
- **X11**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/71991/play-Memphis-Grizzlies-Blind-Pig- — Memphis 2015 ATO blind pig vs Golden State (Gasol flash, Conley backdoor).
- **X12**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/292657/play-Rockwall-Heath-HS--Need-a-3-Pin-in — title uses "Pin-in"; term not defined.
- **X13**: https://coachhoops.substack.com/p/elevator-action — elevator alignment, gap-closing mechanics, aliases (gator, funnel, gate), Golden State credit, Virginia Tech video title.
- **X14**: https://coachhoops.substack.com/p/ricky-action — Ricky definition, immediate re-screen, teams named (Creighton, UConn, Alabama, Virginia, VCU, Penn State; NBA teams).
- **X15**: https://hoopvision.substack.com/p/twirl-action — twirl definition; Dayton 2023-24 example (Cheeks twirls and screens for Brea).
- **X16**: https://coachhoops.substack.com/p/floppy-action — floppy alignment, single-double, reads (curl/fade/DHO/seal/hit the screener), reject floppy.
- **X17**: https://playbank.fastmodelsports.com/library/basketball/search/need%20a%203?page=17 — listing incl. Sacramento Kings 5 Out Elevator, Sparks Ricky Overload, Chicago Sky Decoy Stagger Backdoor, Lynx Loop Flare SLOB.
- **X18**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/66973/play-Michigan-State-Blast — MSU Blast (Mar 2015; vs Georgia NCAA): single option and X/Floppy option.
- **X19**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/409321/play-Michigan-State-Spartans--Stagger-Slip-Curl--Pop — MSU stagger into slip by 4 and down screen by 5 (Mar 20 2022).
- **X20**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/134800/play-Michigan-State--1-4-High-Curl-Double-Flare — MSU vs Florida (2016 post), stagger then flare.
- **X21**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/177053/play-Hawk-Double-Cross — MSU Hawk Double Cross (Feb 17 2017), full five-frame sequence with player names.
- **X22**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/245378/play-Michigan-State-Spartans--Iverson-Stagger-Hit — MSU double stagger twice (Jul 7 2018).
- **X24**: https://hoopvision.substack.com/p/hoops-dictionary-iverson-cut-hv — intro only (paywalled); no details used.
- **X25**: https://hoopvision.substack.com/p/the-starting-five-off-ball-screens — intro only (paywalled); no details used.
- **X26**: https://www.hooperuniversity.com/breakdowns/golden-state-warriors-split-action — split action trigger, options, counters; Villanova uses split and slips the screener.
- **X27**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/438291/play-Connecticut-Huskies--Back-Screen-Turnout-Choice — UConn (Mar 26 2023) back screen, turnout by 5, choice exit.
- **X28**: https://hoopstudent.com/basketball-shake-action/ — shake/lift definition, timing relative to the PnR, purpose vs hedge.
- **X29**: https://stanforddaily.com/2022/12/08/stanford-basketball-film-study-zoom-action/ — Stanford 2022-23 zoom, fake zoom into a circle cut.
- **X30**: https://coachingtoolbox.net/plays/diagrams/basketball-plays-rub-cut.html — rub cut play steps (3 cuts off 5 to the rim, etc.).
- **X31**: https://www.mensbasketballhoopscoop.com/college-basketball-rub-action-plays/ — rub screen definition and six college examples (Jun 28 2016).
- **X32**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/288317/play-Michigan-Wolverines--Loop-Down-Flare-BLOB — loop around 4 and 5, flare, down screen (Mar 23 2019; contributor Lamar CC assistant).
- **X33**: https://www.mensbasketballhoopscoop.com/tom-izzo-michigan-state-dho-horns-chin-play/ — MSU DHO Horns Chin steps (Dec 17 2016); chin screen not defined.
- **X34**: https://hoopstudent.com/basketball-princeton-chin-series/ — chin series: high-post back screen, flare, continuity.
- **X35**: https://hooptactics.net/premium/offense/setoffense/hawk.php — Hawk origin (Hubie Brown; UCLA high post relative; shuffle derivative), reads by defense.
- **X36**: https://www.coachesclipboard.net/HawkOffense.html — Hawk alignment, sequence, corner-3 variation, coaches who used it.
- **X37**: https://nbcsports.com/nba/news/video-breakdown-what-is-the-ucla-cut — UCLA cut three steps, Wooden attribution.
- **X38**: https://www.espn.com/ncb/2003/0212/1507738.html — Fraschilla, UCLA high post offense incl. UCLA cut, double-down, STS, blind pig counter, X cut.
- **X39**: https://nbcsports.com/nba/news/hammer-action-basketball-san-antonio-spurs-nba-glossary-carbaugh-video — hammer: weak-side back/flare screen, shooter to the corner, strong-side decoy.
- **X41**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/377877/play-Washington-Mystic--1-4-Iverson-Ram-BS — Iverson cuts, 4 cross-screens 5, 5 ball-screens 2 (May 18 2021).
- **X42**: https://www.basketballforcoaches.com/iverson-cut-basketball/ — Iverson cut alignment, reads, variants (curl lob, rip, decoy DHO).
- **X43**: https://www.cbssports.com/college-basketball/news/court-report-how-michigan-cracked-code-to-play-two-bigs-cooper-flaggs-season-resembles-ben-simmons-at-lsu/ — Michigan 2024-25 two-big PnR/switching; no off-ball actions mentioned (did not confirm pin-in/elevator).
- **X44**: https://hooptactics.net/premium/offense/motionoffense/shuffle.php — shuffle origin (Drake), roles, rub cut off the high post, sequence.
- **X45**: https://github.com/akashsebastian/Automatically-Detect-On-Ball-Screens — on-ball screen SVM pipeline; no numeric thresholds.
- **X46**: https://www.nessis.org/nessis17/Keshri_adj.pdf — WebFetch saved the PDF; text extracted locally. Columbia event-detection slides (25 Hz SportVU, HMM defensive assignment); no off-ball screen thresholds.
- **X47**: https://www.theonlycolors.com/basketball/43621/msu-basketball-film-room-plays-of-the-month — WebFetch 403; opened with curl. MSU 2025-26 (Dec 3 2025): Arkansas opening pin-downs vs MSU; weave + Fears/Kohler PnR as a go-to set; Carr baseline cut + Cooper DHO lob choice vs UNC; Carr fake-DHO backdoor vs Iowa.
- **X48**: https://spartanavenue.com/the-2025-26-spartans-are-a-vintage-tom-izzo-team-and-that-s-music-to-fans-ears-01kb4a3929sk — no off-ball tactical content (confirmed absence).
- **X49**: https://www.theonlycolors.com/basketball/45979/tom-izzo-must-adapt-if-he-wants-another-national-title — WebFetch 403; opened with curl. MSU 2025-26 half-court spacing critique (two bigs inside, Carr forced outside); no named off-ball actions.
- **X50**: https://playbank.fastmodelsports.com/library/basketball/search/down%20screen?page=60 — listing with MSU STS ATO BLOB, Elbow Away Pindown, Elbow Away STS, Duke Wheel Action, Texas Tech Stack Rip Pindown, WVU X, Houston Loop Double.
- **X51**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/361191/play-Michigan-State-Spartans--STS-ATO-BLOB — MSU at Duke Dec 1 2020: corner entry, 2 screens 5, 4 turnout for 2.
- **X52**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/357611/play-Michigan-State-Spartans--Elbow-Away-Pindown — MSU elbow away pin-down (Nov 18 2020).
- **X53**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/357610/play-Michigan-State-Spartans--Elbow-Away-STS — MSU elbow away STS (Nov 18 2020).
- **X54**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/461577/play-Michigan-State-Spartans--1-4-STS — MSU 1-4 STS, "Izzo staple for about 15 years" (Mar 21 2024).
- **X56**: https://playbank.fastmodelsports.com/library/basketball/search/SLOb?page=7 — listing with MSU Zipper Spain PNR SLOB URL.
- **X57**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/437680/play-Michigan-State-Spartans--Zipper-Spain-PNR-SLOB — MSU zipper into weak-side DHO and side Spain (Mar 17 2023).
- **X58**: https://coachingtoolbox.net/plays/basketball-plays-izzo-ato.html — MSU Zipper ATO three options (4 and 5 cross screen for 2; backdoor; curl).
- **X60**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/2631/play-Elevator — Mississippi State 2008-09 (Stansbury) elevator timing play.
- **X61**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/68106/play-Michigan-State-Over-Under-Play — MSU Over-Under (Apr 3 2015): flare + baseline runner.
- **X62**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/437681/play-Michigan-State-Spartans--Down-Screen-DHO-Veer-ATO — MSU down screen → DHO → veer pin-down (Mar 17 2023).
- **X63**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/451012/play-Michigan-State-Spartans--4-High-Iverson-Curl — MSU 4-High Iverson Curl (Nov 3 2023).
- **X64**: https://www.hooperuniversity.com/breakdowns/wide-pin-down-reads — wide pin-down geometry; reject/curl/flash/pop reads; screener slip; coverage links.
- **X65**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/82024/play-Floppy-Diamond — Floppy Diamond with single pin-downs both sides and a pinch fade for the nail guard (Sep 4 2015).
- **X66**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/182747/play-Troy--Floppy-Punch — Troy floppy punch, 2017 NCAA first round.
- **X67**: https://hoopstudent.com/basketball-floppy — floppy alignment, single vs stagger side, cross-screen and high-low variants.
- **X68**: https://www.coachesclipboard.net/floppy-basketball-plays.html — floppy basics, Floppy-Elbow, Floppy pick-and-roll.
- **X69**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/580/play-Play-of-the-Day-05-19-12-Floppy-Loop-Under — MSU 2012 NCAA Tournament double floppy, 3 loops 4, 5 loops under for a post feed.
- **X70**: https://www.coachesclipboard.net/MSUSets.html — MSU sets incl. 14-Circle, Double Down-Screen, ISO-3 Chest (X-cut and flashes), Back-Screen PnR, Line-1, Screen the Inbounder.
- **X71**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/361135/play-Duke-Blue-Devils--Wheel-Action — Duke vs MSU Dec 1 2020 "Wheel Action" with flare/turnout and back screen/turnout options; wheel undefined.
- **X72**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/357605/play-Texas-Tech-Red-Raiders--Stack-Rip-Pindown — Texas Tech base back-screen then down-screen (Ricky-type) for 1 (Nov 18 2020).
- **X73**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/357599/play-West-Virginia-Mountaineers--X — WVU X cut off 5 then pin-downs for both guards (Nov 17 2020).
- **X74**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/357657/play-Houston-Cougars--Loop-Double — Houston tight-curl loop then big smashes down (Nov 18 2020).
- **X75**: https://squared2020.com/2017/09/14/hammer-offense-mechanics-and-quantification/ — hammer mechanics; SportVU passing-lane distance 1.75 m, closeout 3.95→2.86 m over 0.66 s (1.66 m/s); fast closeouts > 2.13 m/s.
- **X76**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/180528/play-Xavier--Chin-Hammer — Xavier vs Maryland 2017 NCAA: zipper, flare, angle ball screen, DHO, baseline drive, drift to the corner.
- **X77**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/180776/play-Northwestern--Flip-Hammer — Northwestern early-offense flip hammer (Mar 19 2017).
- **X78**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/68152/play-Michigan-State-Chest-Down- — MSU Chest Down with UCLA cut, wing ball screen, double screen (Apr 3 2015).
- **X79**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/289998/play-Michigan-State-Spartans--21-Pin-Chin — MSU 21 Pin Chin ATO (Apr 7 2019): DHO, pin-down, reversal, clear, chin screen, lob; taller athlete as lob target.
- **X80**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/289740/play-Michigan-State-Spartans--DHO-Clear-Lob — MSU 2019 Elite Eight vs Duke second-half opener: DHO, down screen, clear, back-screen lob.
- **X81**: https://hoopvision.substack.com/p/cassius-winston-and-top-lock-defense — top-lock vs Winston; MSU counters: screen his own man, Twist BLOB, cutting under the corner pin-down (vs Ohio State).

**Special-situations note (`[Q#]`; keys assigned by this writer, in order of first use; every URL was opened in the special-situations research)**
- **Q1**: NCAA, 2024-25 Men's Basketball Rules (PDF, NCAA-published, Aug 2024). https://nbcsports.brightspotcdn.com/15/c2/e15320424538aa0c375182350c65/ncaa-2024-25-mens-rules.pdf
- **Q2**: NCAA.org, "Men's basketball rules committees discuss state of the game" (8 May 2026). https://www.ncaa.org/?p=11092
- **Q3**: CBS Sports, "Big Ten says refs made mistake in Michigan State-FGCU final shot debacle" (Nov 2016). https://www.cbssports.com/college-basketball/news/big-ten-says-refs-made-mistake-in-michigan-state-fgcu-final-shot-debacle
- **Q4**: Coach's Clipboard, "Last Second Situations". https://www.coachesclipboard.net/LastSecondSituations.html
- **Q5**: FastModel 227818, "Michigan State Spartans – Sparty BLOB" (6 Mar 2018). https://playbank.fastmodelsports.com/library/basketball/fastdraw/227818/play-Michigan-State-Spartans--Sparty--BLOB
- **Q6**: FastModel 60206, "MSU BLOB" (22 Jan 2015). https://playbank.fastmodelsports.com/library/basketball/fastdraw/60206/play-MSU-BLOB
- **Q7**: FastModel 118858, "Michigan State BLOB Passer Pin" (10 Feb 2016). https://playbank.fastmodelsports.com/library/basketball/fastdraw/118858/play-Michigan-State-BLOB-Passer-Pin
- **Q8**: Hoopscoop (W. Kosel), "Tom Izzo Michigan State BLOB" (16 Dec 2016). https://www.mensbasketballhoopscoop.com/tom-izzo-michigan-state-blob/
- **Q9**: FastModel 1785, "BLOB – Mich ST vs Valpo" (22 Mar 2013). https://playbank.fastmodelsports.com/library/basketball/fastdraw/1785/play-BLOB-Mich-ST-vs-Valpo
- **Q10**: MSU Athletics, "MSU powers past Valparaiso in NCAA opener 65-54" (21 Mar 2013; headline and URL date only). https://msuspartans.com/news/2013/3/21/msu_powers_past_valparaiso_in_ncaa_opener_65_54
- **Q11**: FastModel 461774, "Michigan State Spartans – BLOB" (24 Mar 2024) (= `[M41]`). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461774/play-Michigan-State-Spartans--BLOB
- **Q12**: FastModel 409177, "Clear BLOB" (19 Mar 2022) (= `[M45]`). https://playbank.fastmodelsports.com/library/basketball/fastdraw/409177/play-Michigan-State-Spartans--Clear-BLOB
- **Q13**: FastModel 409173, "Quick Duck-In BLOB" (19 Mar 2022) (= `[M44]`). https://playbank.fastmodelsports.com/library/basketball/fastdraw/409173/play-Michigan-State-Spartans--Quick-Duck-In-BLOB
- **Q14**: FastModel 409226, "Illinois Fighting Illini – 1-4 Low BLOB" (19 Mar 2022). https://playbank.fastmodelsports.com/library/basketball/fastdraw/409226/play-Illinois-Fighting-Illini--1-4-Low-BLOB
- **Q15**: Hurrdat Sports, "ATO execution keys Creighton's return to Sweet 16" (2024). https://hurrdatsports.com/creighton/mens-basketball/ato-execution-keys-creightons-return-to-sweet-16
- **Q16**: Hoop Vision, "The One About BLOBs (HV Weekly 9/15/19)". https://hoopvision.substack.com/p/the-one-about-blobs-hv-weekly-91519
- **Q17**: FastModel 462148, "Purdue Boilermakers – Stack Curl BLOB" (28 Mar 2024) (= `[B12]`). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462148/play-Purdue-Boilermakers--Stack-Curl-BLOB
- **Q18**: FastModel search listing "Illinois Fighting Illini". https://playbank.fastmodelsports.com/library/basketball/search/Illinois%20Fighting%20Illini
- **Q19**: FastModel 462147, "Purdue Boilermakers – Duck In BLOB" (28 Mar 2024) (= `[B11]`). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462147/play-Purdue-Boilermakers--Duck-In-BLOB
- **Q20**: FastModel 433672, "Purdue Boilermakers – Corner Lob BLOB" (12 Jan 2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/433672/play-Purdue-Boilermakers--Corner-Lob-BLOB
- **Q21**: FastModel 437378, "Michigan Wolverines – 4 High BLOB" (12 Mar 2023). https://playbank.fastmodelsports.com/library/basketball/fastdraw/437378/play-Michigan-Wolverines--4-High-BLOB
- **Q22**: FastModel 409756, "Michigan Wolverines – High Low BLOB" (25 Mar 2022). https://playbank.fastmodelsports.com/library/basketball/fastdraw/409756/play-Michigan-Wolverines--High-Low-BLOB
- **Q23**: FastModel 461752, "Illinois Fighting Illini – Stagger Twist BLOB" (24 Mar 2024) (= `[B17]`). https://playbank.fastmodelsports.com/library/basketball/fastdraw/461752/play-Illinois-Fighting-Illini--Stagger-Twist-BLOB
- **Q24**: FastModel 357106, "Wisconsin Badgers – STS BLOB" (15 Nov 2020). https://playbank.fastmodelsports.com/library/basketball/fastdraw/357106/play-Wisconsin-Badgers--STS-BLOB
- **Q25**: HoopTactics, out-of-bounds plays index (names only; premium). https://hooptactics.net/premium/offense/situations/outofboundsplays.php
- **Q26**: Human Kinetics, "Out-of-bounds plays" (excerpt, Miniscalco & Kot, *Survival Guide for Coaching Youth Basketball*). https://us.humankinetics.com/blogs/excerpt/out-of-bounds-plays
- **Q27**: FastModel 72259, "Tom Izzo SLOB '2'" (16 May 2015). https://playbank.fastmodelsports.com/library/basketball/fastdraw/72259/play-Tom-Izzo-SLOB-2-
- **Q28**: FastModel 373222, "Michigan State Spartans – Line Post Stagger SLOB" (19 Mar 2021). https://playbank.fastmodelsports.com/library/basketball/fastdraw/373222/play-Michigan-State-Spartans--Line-Post-Stagger-SLOB
- **Q29**: FastModel 373221, "Michigan State Spartans – Misdirection SLOB" (19 Mar 2021). https://playbank.fastmodelsports.com/library/basketball/fastdraw/373221/play-Michigan-State-Spartans--Misdirection-SLOB
- **Q30**: FastModel 245299, "Michigan State Spartans – Sideline Elevator" (6 Jul 2018). https://playbank.fastmodelsports.com/library/basketball/fastdraw/245299/play-Michigan-State-Spartans--Sideline-Elevator
- **Q31**: FastModel 244280, "Michigan State Spartans – Back Screen Post Up / Stagger Option SLOB" (19 Jun 2018). https://playbank.fastmodelsports.com/library/basketball/fastdraw/244280/play-Michigan-State-Spartans--Back-Screen-Post-Up-Stagger-Option-SLOB
- **Q32**: FastModel 437680, "Zipper Spain PNR SLOB" (17 Mar 2023) (= `[M37]`, `[P47]`). https://playbank.fastmodelsports.com/library/basketball/fastdraw/437680/play-Michigan-State-Spartans--Zipper-Spain-PNR-SLOB
- **Q33**: Coaching Toolbox, Tom Izzo sideline inbounds play diagram. https://coachingtoolbox.net/plays/diagrams/basketball-plays-tom-izzo.html
- **Q34**: Coach's Clipboard, "Michigan State Sets" (= `[P7]`, `[X70]`). https://coachesclipboard.net/MSUSets.html
- **Q35**: FastModel 462287, "Illinois Fighting Illini – Winner SLOB" (30 Mar 2024) (= `[B16]`). https://playbank.fastmodelsports.com/library/basketball/fastdraw/462287/play-Illinois-Fighting-Illini--Winner-SLOB
- **Q36**: FastModel 377884, "Wisconsin Badgers – Diamond SLOB" (18 May 2021). https://playbank.fastmodelsports.com/library/basketball/fastdraw/377884/play-Wisconsin-Badgers--Diamond-SLOB-
- **Q37**: FastModel 373464, "Wisconsin Badgers – Ghost SLOB" (Mar 2021). https://playbank.fastmodelsports.com/library/basketball/fastdraw/373464/play-Wisconsin-Badgers--Ghost-SLOB
- **Q38**: FastModel 280738, "Wisconsin Badgers – Box Pop SLOB" (15 Jan 2019). https://playbank.fastmodelsports.com/library/basketball/fastdraw/280738/play-Wisconsin-Badgers--Box-Pop-SLOB
- **Q39**: Spartan Avenue, MSU top plays in the win over Duke (1 Apr 2019). https://spartanavenue.com/2019/04/01/michigan-state-basketball-top-plays-win-duke-2019/2
- **Q40**: The Ringer, Villanova 2016 title shot (14 Mar 2017). https://www.theringer.com/2017/03/14/uncategorized/villanova-2016-ncaa-title-shot-kris-jenkins-jay-wright-49f028eb011f
- **Q41**: ESPN, Jordan Poole buzzer-beater vs Houston (Mar 2018). https://www.espn.com/mens-college-basketball/story/_/id/22815610/jordan-poole-michigan-basks-buzzer-beating-3-pointer-houston
- **Q42**: SI, "Michigan Jordan Poole buzzer beater" (22 Mar 2018). https://www.si.com/college/2018/03/22/michigan-jordan-poole-buzzer-beater-ncaa-tournament
- **Q43**: Wikipedia, "The Shot (Duke–Kentucky)". https://en.wikipedia.org/wiki/The_Shot_(Duke%E2%80%93Kentucky)
- **Q44**: Coach's Clipboard, "Buzzer Beaters – Full Court". https://www.coachesclipboard.net/BuzzerBeatersFullCourt.html
- **Q45**: Spartan Avenue, MSU takeaways vs Kentucky (15 Nov 2022). https://spartanavenue.com/2022/11/15/michigan-state-basketball-takeaways-kentucky-2022/
- **Q46**: Coaching Toolbox Building Blocks, special teams / Special Teams Playbook (Filios). https://buildingblocks.coachingtoolbox.net/?p=2070
- **Q47**: Coaching Toolbox store, "Tom Izzo: Winning Dead Ball Situations" DVD. https://onlinestore.coachingtoolbox.net/product/tom-izzo-winning-dead-ball-situations-dvd/
- **Q48**: CBS Sports play-by-play, Purdue at Michigan State, 26 Feb 2022. https://www.cbssports.com/college-basketball/gametracker/playbyplay/NCAAB_20220226_PURDUE@MICHST
- **Q49**: Better Basketball, last-shot timing (2016). https://betterbasketball.com/?p=5402
- **Q50**: ShotTracker, "What our Data Says About Clutch Shooting in Division I Basketball: Part 2" (31 Aug 2026). https://shottracker.com/?p=2562
- **Q51**: Hudl blog, "Sideline to baseline: how efficiency numbers make all the difference when inbounding". https://www.hudl.com/blog/sideline-to-baseline-how-efficiency-numbers-make-all-the-difference-when-inbounding
- **Q52**: HoopTactics newsletter, last-shot offence and defence. https://hooptactics.net/news/?p=202
- **Q53**: Coach's Clipboard newsletter (16 Feb 2022), "Izzo" Screen-the-Inbounder. https://www.coachesclipboard.net/newsletters/CCNewsLetter03022022.html
- **Q54**: FastModel 297784, "Michigan State Spartans – One SLOB" (6 Aug 2019). https://playbank.fastmodelsports.com/library/basketball/fastdraw/297784/play-Michigan-State-Spartans--One-SLOB
- **Q55**: FastModel 361191, "STS ATO BLOB" (8 Dec 2020) (= `[M46]`, `[X51]`). https://playbank.fastmodelsports.com/library/basketball/fastdraw/361191/play-Michigan-State-Spartans--STS-ATO-BLOB

**Zone / press note (`[Z:TAG]`; tags follow the zone/press research note)**
- **Z:CCNL14**: https://coachesclipboard.net/newsletters/CCNewsLetter12012014RWD.html — MSU "33" box set vs 2-3: full sequence
- **Z:MSUSETS**: https://coachesclipboard.net/MSUSets.html — MSU zone list (Special, Special-2, Fist, Double, 33); MSU Special and Special-2 sequences; no press breaks on the page
- **Z:CCFD**: https://coachesclipboard.net/MSUFistDownZonePlay.html — Fist-Down alignment, sequence, options; works vs 2-3/3-2, not 1-3-1; used vs Syracuse and Florida
- **Z:FMSZO1**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/68088/play-Spartan-Zone-Options — Spartan Zone Options steps and reads
- **Z:FMSZO2**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/77124/play-Spartan-Zone-Options — Second version; MSU attribution; reads
- **Z:FMARM**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/70227/play-Tom-Izzo-Arm-Chop — Arm Chop steps; Izzo/MSU vs 2-3
- **Z:FMPPP**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/1758/play-Michigan-State-Push-Pipe-Pin-vs-2-3 — Push Pipe Pin steps; vs Iowa, B1G Tournament
- **Z:FMZLS**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/67789/play-Michigan-State-Zone-Lob-Set — Zone Lob Set; Louisville match-up 2-3, East Regional Final
- **Z:FMSR**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/67791/play-Michigan-State-Zone-O--Short-Roll — Short-roll ball screen vs zone
- **Z:FMXL**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/67790/play-NCAA-Set-Zone-Cross-Lob — Zone Cross Lob; MSU, Arizona, Kansas, Iowa State, Louisville, NC State listed
- **Z:FMVZ25**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/478264/play-Michigan-State-Vs-Zone — MSU 2024-25 zone set, partial steps
- **Z:FMIZ2**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/473108/play-Zone-Offense--Izzo-2 — Title only; no MSU attribution in text
- **Z:FMZLMSU**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/400662/play-Zone-Lob--Michigan-State- — Backside lob vs 2-3; MSU only in title
- **Z:FMMSU1**: https://playbank.fastmodelsports.com/library/basketball/search/Michigan%20State?page=1 — Index that surfaced Push Pipe Pin
- **Z:FMMSU2**: https://playbank.fastmodelsports.com/library/basketball/search/Michigan%20State?page=2 — Index that surfaced Zone Lob Set and Short Roll
- **Z:FMMSU3**: https://playbank.fastmodelsports.com/library/basketball/search/Michigan%20State?page=3 — Index; no zone or press items beyond the 1-3-1 Double (existing)
- **Z:FMMSU4**: https://playbank.fastmodelsports.com/library/basketball/search/Michigan%20State?page=4 — Index; none
- **Z:FMMSU5**: https://playbank.fastmodelsports.com/library/basketball/search/Michigan%20State?page=5 — Index; MSU Vs Zone (2024-25), Zone Lob "MSU"
- **Z:FMMSU6**: https://playbank.fastmodelsports.com/library/basketball/search/Michigan%20State?page=6 — Index; Arm Chop
- **Z:FMMSU7**: https://playbank.fastmodelsports.com/library/basketball/search/Michigan%20State?page=7 — Index; Zone Cross Lob, Spartan Zone Options ×2
- **Z:FMMSU8**: https://playbank.fastmodelsports.com/library/basketball/search/Michigan%20State?page=8 — Index; none
- **Z:SIIND25**: https://www.si.com/college/michiganstate/basketball/spartans-indiana-hoosiers-jeremy-fears-jr-jaxon-kohler-szymon-zapala-01jkw4014t2n — MSU poor vs Indiana 2-3, Feb 2025
- **Z:HSIZ12**: https://www.mensbasketballhoopscoop.com/basketball-coaching-top-basketball-plays-for-zone-offense-tom-izzo-michigan-state-zone-set-play-brandon-rosenthal/ — Exists; content in a PDF not read (unverified)
- **Z:ACT1**: https://www.active.com/basketball/articles/how-tom-izzo-beats-the-best-zone-defenses — Only titles of Izzo 1-3-1 videos (already in F11)
- **Z:CBS24**: https://www.cbssports.com/college-basketball/gametracker/recap/NCAAB_20240321_MICHST@MISSST — Walker "press breakers... special teams"; MSST half-court trap
- **Z:CCBP**: https://www.coachesclipboard.net/BasketballPlays.html — Index of zone and press pages
- **Z:CCKZP**: https://www.coachesclipboard.net/KansasZonePlays.html — Self plays #1, #2, #3, #4, #8
- **Z:CCKZO**: https://www.coachesclipboard.net/KansasZoneOffense.html — Self stationary zone rules
- **Z:KUS13**: https://www2.kusports.com/news/2013/dec/12/self-ku-reacting-too-slow-vs-zone/ — Self "hot potato" quotes, Dec 2013
- **Z:FMKBSP**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/436843/play-Kansas-Jayhawks--Ball-Screen-to-Pin-In-Zone-Offense — KU Ball Screen to Pin In
- **Z:CC23P**: https://www.coachesclipboard.net/23ZoneOffensePlays.html — Carolina, Zone-1 X, 91, Corners 52, 45/54, Chicago, Miami, Vermont, Special/Special-Down (Flannery), West (Gottlieb), X-Screen Lob (Mike White), Stack-1/2/3 (Bryce Drew)
- **Z:CC41**: https://www.coachesclipboard.net/41ZoneOffense.html — 4-out Corners rules; Larry, Curly, Mo, Stack, Star, Weak, Wing Flash
- **Z:CC122**: https://www.coachesclipboard.net/122zoneoffense.html — Zone-2 runner rules; 45/54, Back, Middle cut, Back-Skip, Flex
- **Z:CCGAP**: https://www.coachesclipboard.net/GapAttackZonePlay.html — Brownell Gap Attack
- **Z:CCDDZ**: https://www.coachesclipboard.net/DribbleDriveZoneOffense.html — DDM zone adaptation rules
- **Z:CTSS**: https://coachingtoolbox.net/blog/zone-attack-principles — Sonny Smith ten zone rules
- **Z:FMLOOP**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/406149/play-Zone-Offense-Concepts--Loop-MIX — Loop / dribble up, throw back
- **Z:FMZO1**: https://playbank.fastmodelsports.com/library/basketball/search/ZONE%20OFFENSE?page=1 — Index (Izzo 2, KU pin-in, Loop MIX, Kentucky overload, Loyola)
- **Z:FMBIBS**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/287903/play-Baylor-Bears--Inside-Ball-Screen — Baylor inside ball screen vs 2-3, reads
- **Z:FMBRUB**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/290216/play-Baylor-Bears--Rub-vs-Match-Up-Zone — Baylor Rub vs match-up; 2019 NCAA vs Syracuse
- **Z:FMBPULL**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/290217/play-Baylor-Bears--Pull-vs-Match-Up-Zone — Baylor Pull vs match-up
- **Z:FMORE32**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/124255/play-Oregon--Zone-32 — Altman Zone 32
- **Z:CTBEIL**: https://coachingtoolbox.net/?p=11033 — Michigan X and Michigan Hand
- **Z:UMH13**: https://umhoops.com/2013/04/07/five-key-plays-michigan-vs-syracuse/ — Michigan vs Syracuse 2-3, 2013 Final Four actions
- **Z:CTGIL**: https://coachingtoolbox.net/?p=1639 — Gillen match-up attack principles
- **Z:CT131**: https://coachingtoolbox.net/1-3-1-zone-attack-ideas — Elbow and X 1-3-1 attacks
- **Z:BBRR**: https://betterbasketball.com/attacking-1-3-1-zones-with-read-react/ — Pin & Skip; 5-out vs 1-3-1
- **Z:HSOVL**: https://www.mensbasketballhoopscoop.com/overloading-offense-zone-defense/ — Overload base; Green Bay, Gonzaga, Oklahoma, FDU, Texas overload sets
- **Z:THG23**: https://www.thehoopsgeek.com/how-to-beat-2-3-zone-defense — Toledo continuity; Triangle overload
- **Z:ESPNFR**: https://www.espn.com/ncb/2003/0113/1491739.html — Fraschilla tips; 70% claim
- **Z:FMKY**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/399810/play-Zone-Offense-Baseline-Overload--Kentucky- — Baseline overload steps; Kentucky only in title
- **Z:FMLUC**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/374114/play-Loyola-Chicago-Ramblers--Zone-Offense-Double-Cut — Loyola Chicago double cut
- **Z:CWT**: https://coachingtoolbox.net/cutters-zone-actions-ryan-odom-umbc — Only that Odom (UMBC) has a "cutters" zone offense video; no details (not catalogued)
- **Z:CCPO**: https://www.coachesclipboard.net/BasketballPressOffenses.html — Index of press-break pages
- **Z:CCM2M**: https://www.coachesclipboard.net/M2MPressBreak.html — Side, Line 321, Shuffle, Big 5
- **Z:CC3UP**: https://www.coachesclipboard.net/3UpPressBreak.html — 3-Up press break
- **Z:CCFLOOD**: https://coachesclipboard.net/FloodPressBreak.html — Hurley Flood
- **Z:CCHCPB**: https://www.coachesclipboard.net/HalfCourtPressBreakers.html — Half-court breakers by trap type
- **Z:WIKI131**: https://en.wikipedia.org/wiki/1%E2%80%933%E2%80%931_defense_and_offense — 1-3-1 full-court trap break: big flashes midcourt, pass to the weak guard on the sideline
- **Z:FMDOS**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/191510/play-Dos — Dos 2-1-2 vs odd traps
- **Z:CC1121**: https://coachesclipboard.net/PressBreaker.html — 1-1-2-1 press break; count to two
- **Z:CC4X**: https://www.coachesclipboard.net/4AcrossPressBreak.html — 4-Across options 1–3, 4-Fly
- **Z:FMTTU**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/289140/play-Texas-Tech-Red-Raiders--4-Across-Press-Break — Texas Tech 4-Across vs Gonzaga denial
- **Z:BFC14**: https://www.basketballforcoaches.com/1-4-press-break/ — 1-4 press break; inbounder runs baseline; centerfielder walk-down
- **Z:HOOPU**: https://hooperuniversity.com/playbooks/press-breakers — Ten named press-break sets
- **Z:FMUCLA**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/231864/play-UCLA--Wooden-Press-Break — Wooden stack press break
- **Z:FMCUBA**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/455056/play-Cuba-Press-Break — Cuba; Michigan's four press breakers
- **Z:FMPB1**: https://playbank.fastmodelsports.com/library/basketball/search/press%20break?page=1 — Index of college press breaks
- **Z:FMPB2**: https://playbank.fastmodelsports.com/library/basketball/search/press%20break?page=2 — Index; Cuba from Wooden stack; UCLA, Villanova, SFA
- **Z:FMPB3**: https://playbank.fastmodelsports.com/library/basketball/search/press%20break?page=3 — Index; Dos, R&J, Buddy, 4-up, EOG sets
- **Z:FMUM131**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/288333/play-Michigan-Wolverines--1-3-1-Press-Break — Michigan 1-3-1 press break vs Florida, 2019
- **Z:FMUMBD**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/288334/play-Michigan-Wolverines--Press-Break-Backdoor — Michigan backdoor press break vs Florida, 2019
- **Z:FMVU**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/128507/play-Villanova-M-M-Press-Break — Villanova man press break
- **Z:FMSFA**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/124060/play-Stephen-F-Austin--Press-Break — SFA stack footrace
- **Z:FMIOWA**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/487411/play-Iowa--EOG-Press-Break-3 — Iowa EOG press break, down 2, 8.9 s
- **Z:FMPUR**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/462617/play-Purdue-Boilermakers--3-Out-Football-Press-Break — Purdue EOG football press break
- **Z:FMCSU**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/402998/play-Colorado-State-Rams--Stack-Press-Break-EOG- — Colorado State EOG stack; anti-switch
- **Z:FMRJ**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/191507/play-Run--Jump-Scramble-Break — R&J/scramble break
- **Z:FMBUDDY**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/191506/play-Buddy — Buddy
- **Z:FM2UP**: https://playbank.fastmodelsports.com/library/basketball/fastdraw/397437/play-2-Up-Press-Breaker — 2-Up rules
- **Z:CTPO**: https://coachingtoolbox.net/offense/press-offense.html — Press offense principles; 4.57 m spacing; two reversals
- **Z:SIVCU**: https://www.si.com/college/2013/02/11/vcu-press — VCU fist/double fist, diamond, trap spot; Rhode Island counter
- **Z:HSPB**: https://www.mensbasketballhoopscoop.com/basketball-plays-press-breakers/ — Wootten DeMatha press break
- **Z:OFF920**: https://forum.officiating.com/920285-post1.html — Opened; did **not** contain NCAA 10 s text (rule left unverified)

**Sources opened by the fixer pass (2026-10-18), keyed `[V#]`** (each opened with WebFetch on 2026-10-18; `[M9]`, `[M13]`, `[M23]`, `[M34]` and `[Q43]` were also re-opened):
- **V1**: Wikipedia, 2025 NCAA Division I men's basketball tournament. https://en.wikipedia.org/wiki/2025_NCAA_Division_I_men%27s_basketball_tournament — Purdue 76-62 McNeese (second round, Providence, Thu/Sat, round dated 22–23 Mar); Michigan 91-79 Texas A&M (second round, Denver); Maryland 72-71 Colorado State (second round, Seattle).
- **V2**: Wikipedia, 2024 NCAA Division I men's basketball tournament. https://en.wikipedia.org/wiki/2024_NCAA_Division_I_men%27s_basketball_tournament — Purdue 80-68 Gonzaga, Midwest regional semifinal (Sweet 16), Detroit, 29 Mar 2024.
- **V3**: Wikipedia, 2026 NCAA Division I men's basketball tournament. https://en.wikipedia.org/wiki/2026_NCAA_Division_I_men%27s_basketball_tournament — Iowa 73-72 Florida (second round, Tampa); MSU beat North Dakota State 92-67 and Louisville 77-69, lost 67-63 to UConn in the Sweet 16.
- **V4**: Wikipedia, 2025-26 Michigan State Spartans men's basketball team. https://en.wikipedia.org/wiki/2025%E2%80%9326_Michigan_State_Spartans_men%27s_basketball_team — "The loss ended the season with MSU 27–8 overall" (Sweet 16 loss to UConn).
- **V5**: Wikipedia, 2024-25 Maryland Terrapins men's basketball team. https://en.wikipedia.org/wiki/2024%E2%80%9325_Maryland_Terrapins_men%27s_basketball_team — head coach Kevin Willard; 72-71 win over Colorado State, 23 Mar 2025, Seattle; Queen 17 points.
- **V6**: NBC Washington (AP), "Derik Queen's buzzer-beating fadeaway gives Maryland a 72-71 March Madness win over Colorado State" (24 Mar 2025). https://www.nbcwashington.com/news/sports/capital-games/derik-queens-buzzer-beating-fadeaway-gives-maryland-a-72-71-march-madness-win-over-colorado-state/3874530/ — trailing 71-70, 3.6 s left, second round, coach Willard.
