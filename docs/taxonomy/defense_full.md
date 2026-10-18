# NCAA D-I Men's Basketball: Defensive Taxonomy for Per-Second Scheme Labeling
### Extends `/home/claude/set_taxonomy.md` §2 (defense) and §3 (MSU). Michigan State (Tom Izzo) focus.

Compiled 2026-10-17. Everything is paraphrased. Source keys look like `[D12]`. They resolve in the **Sources** list at the end. Keys like `[S69]` point to sources from the first-pass file (`set_taxonomy.md`). Those are re-listed at the end, and any I re-opened in this pass are marked.

Tags carried over from the first pass:
- **[UNVERIFIED]**: plausible, but no opened source confirmed it.
- **[CONVENTION]**: common coaching usage, stated from general knowledge with no single authoritative source opened.
- **[HEURISTIC]**: a detection rule proposed for this project. It is an engineering choice, not a sourced fact. All numeric thresholds in "Detection signature" columns are [HEURISTIC] unless a source key is attached.

**How this file relates to the first pass.** `set_taxonomy.md` §2.1–2.8 already gives short definitions for pack line, gap, deny, no-middle, the core ball-screen coverages, off-ball coverages, post techniques, the basic zone, press and junk shapes, and a few hybrids. This file does not repeat those one-liners. It:
1. adds a deeper hierarchy (Family → Sub-family → Named scheme → Variants);
2. adds roles, triggers, programs, counters, and **metric-unit detection signatures**;
3. adds the families the first pass did not have: on-ball rules, DHO coverage, help/rotation systems, transition, rebounding, special situations, fouling, a communication vocabulary, and outcome labels.

---

## 0. Coordinate frame, derived features, and detection primitives

### 0.1 Frame (project standard)
- Units are metres. The origin is the centre of the **attacked rim**, projected to the floor.
- Polar coordinates: **r** is the distance from the rim. **θ** is in degrees, measured from the **right baseline** (as seen by the defense facing the offense... see the note below). θ = 0° runs along the baseline toward the right sideline, θ = 90° runs straight up the lane toward half-court, and θ = 180° runs along the baseline toward the left sideline.
- Cartesian helpers: x = r·cos θ (positive toward the right sideline) and y = r·sin θ (positive toward half-court).
- "Right" follows the project's own convention: the right baseline as seen from the camera or attacking-team view in the existing pipeline. Nothing below depends on the handedness, because every signature uses |x| or a side-of-ball sign.

### 0.2 NCAA landmarks in this frame [CONVENTION; NCAA court geometry]

| Landmark | Metres from rim centre | Notes |
|---|---|---|
| Baseline | y ≈ −1.60 | The rim centre is 5.25 ft from the baseline |
| Restricted-area arc | r = 1.22 | 4 ft |
| Lane edges | x = ±1.83 | The lane is 12 ft wide |
| Free-throw line | y ≈ 4.19 | 15 ft from the backboard face. The rim centre is 1.25 ft in front of the backboard |
| "Nail" | (0, 4.2) | Middle of the FT line |
| Elbows | (±1.83, 4.2) | |
| Pack line | r ≈ 4.9–5.2 | 16–17 ft `[D2][D3]` |
| 3-pt arc (men, since 2019-20) | r = 6.75 (corners 6.60) | Same as the FIBA distance |
| Sidelines | x = ±7.62 | 50 ft wide |
| Half-court line | y ≈ 12.73 | 47 ft from the baseline, minus 1.6 m |
| Opposite FT line (full-court frame) | y ≈ 21.3 | For presses. Use the *defended* rim as the origin, so the backcourt has y > 12.73 |

### 0.3 Per-frame features used throughout [HEURISTIC]
For defender *d*, attacker *a*, ball *b*, and rim *R* = (0,0):

- **dist(d,a)**, **dist(d,b)**, **r_d** (the defender's distance to the rim).
- **Canonical guarding point** `g(a) = 0.62·a + 0.11·b + 0.27·R`. Franks et al. estimated these weights from NBA SportVU data. They were stable across games, and defenders stood roughly 70% of the way from the hoop to their man `[D35]`. Define the **guarding residual** `e(d,a) = |d − g(a)|`.
- **Matchup posterior** P(d guards a): an HMM with per-frame stay probability ρ ≈ 0.96–0.99 `[D35]`. This is the backbone for man/zone/switch detection. A football analogue showed that HMM-derived features (switch count, assignment entropy) improve man-vs-zone classification `[D36]`.
- **Assignment entropy** H_d: the entropy of the matchup posterior for defender *d*. **Team entropy** H = Σ H_d.
- **Follow correlation** ρ_follow(d,a): the correlation of the defender's velocity with attacker *a*'s velocity over a sliding 2 s window. Compare it with **ball correlation** ρ_ball(d): the correlation of the defender's velocity with the ball's velocity, or with the ball-to-region shift.
- **Region stability** σ_reg(d): the std-dev of the defender's position, relative to a ball-conditioned zone template slot, over the possession.
- **Side-of-ball sign** s(d): the sign of x_d·x_b. A positive sign means the defender is on the ball side.
- **Line metrics.** On-line distance is the perpendicular distance from d to segment(a,b). **Pass-lane fraction** t ∈ [0,1] is the projection parameter along a→b: 0 = at the man, 1 = at the ball.
- **Gap occupancy**: whether d lies inside the triangle (ball, rim, adjacent attacker).
- **Help depth** = r_d − r_a: how far the defender sits inside his man toward the rim.

### 0.4 Event primitives (inherited and extended)
`SCREEN`, `DHO`, `CUT`, `PASS`, and `DRIVE` are as in set_taxonomy §0. New:
- `TRAP(d1,d2,a)`: two defenders within 1.5 m of the ball-handler, and within 2.5 m of each other, for at least 0.6 s.
- `CLOSEOUT(d,a)`: after a catch by *a*, defender *d* travels at least 2.5 m toward *a* with a peak speed of at least 4 m/s and ends within 1.5 m of *a*.
- `ROTATE(d, a_old→a_new)`: the HMM matchup changes and persists for at least 1.0 s.
- `STUNT(d)`: *d* moves 1.0 m or more toward the ball-handler, then reverses back toward his own man within 1.0 s, without a matchup change.
- `SWITCH(d1,d2)`: a reciprocal matchup exchange within 1.0 s, persisting at least 1.5 s.
- `SET_DEF`: the defensive "set" moment. All five defenders are past half-court (y < 12.7) and the mean defender speed has dropped below 2.5 m/s for 0.5 s.

---

## Top-level hierarchy (this file)

```
DEFENSE
├── F1  Man-to-man philosophies (system level)
├── F2  On-ball defense rules
├── F3  Ball-screen (PnR) coverages
├── F4  Dribble-handoff (DHO) coverages
├── F5  Off-ball screen coverages
├── F6  Post defense
├── F7  Help & rotation systems
├── F8  Zones
├── F9  Presses & full-court pressure
├── F10 Junk / combination defenses
├── F11 Hybrid & changing defenses (mid-possession and between-possession)
├── F12 Transition defense
├── F13 Defensive rebounding
├── F14 Special-situation defense
├── F15 Fouling strategy & foul-trouble adjustments
├── F16 Communication vocabulary → measurable behaviors
├── F17 Defensive play-type outcome labels (Synergy-style)
└── F18 Detection architecture & label hierarchy for per-second output
```

---

## F1. MAN-TO-MAN PHILOSOPHIES (system level)

A *philosophy* is the possession-long default that governs every off-ball defender's spacing. It is labelled per possession, or per 5 s window. Ball-screen, DHO and off-ball coverages (F3–F5) are *event-level* labels that sit underneath it.

```
F1 Man-to-man
├── F1.1 Help-first (gap) family
│   ├── F1.1.1 Pack line ─ variants: Bennett/Virginia, Soderberg, "Boone" post-front variant
│   ├── F1.1.2 Gap / ball-you-man help man (Bo Ryan-style)
│   ├── F1.1.3 Sagging man (FIBA)
│   └── F1.1.4 Shrink-the-floor / shift-to-ball posture
├── F1.2 Pressure family
│   ├── F1.2.1 Pressure/deny man (one-pass-away on the line)
│   ├── F1.2.2 Houston "aggressive everything" (Sampson): blitz PnR, lane denial, post trap, fly-by
│   ├── F1.2.3 Iowa State "mini-Houston" (Otzelberger)
│   └── F1.2.4 Half-court run-and-jump man
├── F1.3 Directional family
│   ├── F1.3.1 No-middle / Outer-third (LoGalbo; Beard)
│   ├── F1.3.2 Force-to-help-middle / "no baseline" (pack line)
│   └── F1.3.3 Force-sideline (Beard toes-to-sideline)
├── F1.4 Switching family
│   ├── F1.4.1 Switch-everything (positionless)
│   ├── F1.4.2 1-4 switching (center exempt)
│   └── F1.4.3 Situational switching (ATO / wing PnR / late clock / personnel)
└── F1.5 Program profiles (D-I) incl. Michigan State (F1.6)
```

### F1.1 Help-first (gap) family

| Scheme | Definition & roles | Trigger / when | D-I programs (sourced) | Offensive counters | Detection signature [HEURISTIC unless keyed] |
|---|---|---|---|---|---|
| **Pack line (base)** | One defender pressures the ball. The other four stay inside an imaginary arc about 16–17 ft (4.9–5.2 m) from the rim and sit in gaps rather than denying `[D2][D3]`. If fewer than four defenders are inside the line, something is wrong `[D2]`. On a dead ball (dribble used), all may deny for a steal, then return to the gaps `[D3]`. It is a "gap" system, the opposite of a deny system. A line taped on the practice floor teaches the depth `[D1]` | Possession-long default | Dick Bennett (origin), Tony Bennett at Virginia: top-6 KenPom AdjD in 3 of 4 seasons as of 2015 `[D1]`. Brad Soderberg version `[D2]` | Pre-help is set, so offenses use catch-and-shoot threes over the pack, ball reversal and skip-to-attack-closeout, and post-ups against the 3/4 front. Spacing alone does not pull the pack out [CONVENTION] | (1) While the ball is outside the arc (r_b > 6.75 m), **at least 3 of 4** off-ball defenders have r_d ≤ 5.3 m in at least 70% of frames. (2) Off-ball defenders whose man is beyond the arc have help depth r_a − r_d ≥ 1.5 m. (3) One-pass-away defenders are **not** on the passing lane: perpendicular distance to segment(a,b) > 0.8 m, and they sit inside triangle(ball, rim, man). (4) On-ball defender within 1.2 m of the ball (pressure). (5) After a pass, the new on-ball defender closes out and the previous one falls back inside 5.3 m within 1.0 s `[D3]` |
| ↳ *Variant: Bennett/Virginia* | Never give up the baseline: force toward the middle, where help is pre-positioned `[D3][D43]`. Post fronted 3/4 from the high side. Posts trapped from the middle `[D43]`. Off-ball screens are fought through with no switching, and a defender may cheat over or under a weak-side screen `[D3]`. Grantland notes Virginia does not "down" (ice) ball screens and lets handlers go middle `[D1]`. Hoop Vision places Virginia on the **aggressive** side of the ball-screen spectrum (attack the handler) `[D9]` | — | Virginia (Bennett) | Same as base | Side PnR: X-ball does **not** pre-position on the screen side (no ice). Baseline drive rate allowed is low. The off-ball switch rate on off-ball screens is ≈ 0 |
| ↳ *Variant: Soderberg (Dick Bennett lineage)* | The 1 and 2 "back every time" (get back in transition). The other three keep the opponent off the offensive glass. Heavy 4-on-4 practice `[D2]` | — | Soderberg / Bennett notes `[D2]` | — | Transition: two guards are first back. See F12 |
| ↳ *Variant: "Boone" post front* | Front the post when the ball is **below the FT line**, instead of 3/4 high side `[D3]` | Ball at y < 4.2 m on the wing | Named in `[D3]` | Lob over the front | Post defender is on the ball side of the post (F6) when y_b < 4.2 |
| **Gap / ball-you-man help (traditional)** | One pass away: deny or sit in the gap with a hand in the lane. Two passes away: weak-side foot in the paint, or drop to the middle of the lane. Close out with a high hand and short, quick steps. Keep the ball out of the middle and the post, and force catches beyond the arc (Bo Ryan) `[D4]`. Help-side players use the "pistols" position, with the help-side line up the middle of the floor `[D41]` | Possession default | Bo Ryan (Wisconsin) `[D4]` | Skip passes, penetrate-and-kick | Two-away defenders: \|x_d\| ≤ 1.8 m (lane) or x_d on the help-side line (\|x_d\| < 1 m) while the ball is on the wing. One-away defenders sit at t ≈ 0.2–0.4 of the man→ball segment, 0.3–1.0 m off it |
| **Sagging man** | Defenders stay between their man and the basket rather than between man and ball (FIBA) `[D10]` | Against poor shooters | — | Open catch-and-shoot | Defender lies near segment(man, rim). Angle ∠(a→d, a→R) < 20°. Help depth ≥ 1.5 m for most off-ball defenders, regardless of the side of the ball |
| **Shrink the floor / shift to ball** | Off-ball defenders move toward the ball-handler to close driving lanes, keeping their distance from their own man (FIBA) `[D10]` | On the dribble | — | Kick-out on the drive | Mean off-ball defender distance to the ball decreases ≥ 1.0 m within 0.5 s of a dribble start. Convex-hull area of the 5 defenders shrinks ≥ 15% |

### F1.2 Pressure family

| Scheme | Definition & roles | Trigger | Programs | Counters | Detection signature |
|---|---|---|---|---|---|
| **Pressure / deny man** | Every defender stays between his man and the ball (FIBA "pressure man-to-man") `[D10]`. One pass away: "on the line" (in the passing lane). Two passes away: "up the line" into the paint `[D41]`. Deny the reversal pass and the post entry `[D41]` | Default for pressure teams | Classical Knight / Indiana lineage [CONVENTION]. FIBA definition `[D10]` | Back-cuts and backdoor lobs. Dribble entry instead of a pass. Wide pin-downs | **Deny index** = fraction of one-pass-away defender-frames with perpendicular distance to segment(a,b) ≤ 0.6 m and lane fraction t ∈ [0.05, 0.35]. Pressure man if deny index ≥ 0.5. Pack line ≈ 0 except on dead balls |
| **Houston (Kelvin Sampson): aggressive everything** | Blitz/trap nearly every ball screen. Houston forced the ball out of the handler's hands on 71% of ball screens, vs a 54% D-I average `[D7]`. Defenders jump passing lanes for deflections, and Houston forced turnovers on 31% of ball screens `[D7]`. Bigs rotate fast to the roller `[D7]`. Rim denial and attacking post touches. Houston was #1 in block rate (19%) `[D7]`. **Fly-by closeouts** (sprint and leap past the shooter): they allow a high 3PA rate but close out on > 60% of threes, and held opponents < 30% 3P for six straight seasons `[D7]`. Post: **"Monster" post trap**, an immediate, designated-helper double on a back-to-basket catch, with the weak side rotating early `[D8]`. Sampson dislikes the word "trap" for the PnR blitz `[D7]` | Every PnR. Every post catch | Houston (Sampson) `[D7][D8]` | Short roll and 4-on-3 behind the blitz. Slip screens. Skip to the weak side. Spread pick-and-pop | (1) PnR: `TRAP` at or above the screen line in ≥ 60% of ball screens. (2) Post: a second defender arrives within 1.5 m of the post-catcher within 0.8 s of the catch. The arriving defender came from the baseline or the top guard spot `[D8]`. (3) Closeouts: closeout end speed ≥ 3 m/s and the defender's path passes within 1 m of the shooter, then continues past (fly-by). (4) Deny index high (≥ 0.5) |
| **Iowa State (T.J. Otzelberger): "mini-Houston"** | Blitzes and hedges more than most high-major teams, but more measured than Houston. Lipsey anchors point-of-attack pressure. Four players can converge at the rim. Weak-side closeouts are a known weakness: 254th in open-3 rate allowed `[D7]` | PnR | Iowa State `[D7]` | Weak-side catch-and-shoot | Mixture: blitz/hedge share ≈ 0.4–0.6. High help-convergence count (≥ 3 defenders within 3 m of the rim on drives) |
| **Half-court run-and-jump** | A help defender "jumps" a dribbler heading toward him (a jump switch). The original defender "runs" to the open man. Middle dribble → run-and-jump. Sideline dribble → trap. Dean Smith (UNC, 1970s) origin `[D50]`. "Next" (FIBA) is the run-and-jump after a screen or penetration `[D10]` | Dribbler with head down toward a helper. Sideline dribble | UNC (Dean Smith) `[D50]` | Pass ahead before the jump. Lob over the jumper | Event: helper d2 moves ≥ 3 m toward the handler at ≥ 4 m/s while d1 (the original) leaves the handler, and HMM matchups swap d1↔d2 **without a screen**. Distinguishes from a switch, which needs `SCREEN` |

### F1.3 Directional family (force rules)

| Scheme | Definition & roles | Programs | Counters | Detection signature |
|---|---|---|---|---|
| **No-middle / Outer-third** | Keep the ball in the outer thirds of the court. Use the sideline and baseline as an extra defender. Allow baseline drives, and expect the low (weak-side bottom) defender to rotate. The defense is meant to cut passing options in half, and it forces more skip passes `[D39][D42]`. LoGalbo's coverages: "Black" (switch), Ice for side PnR, Drop only for middle PnR `[D26]`. Beard: stance parallel to the sideline with a high foot, ice ball screens, post defender comes up on the far side, baseline help traps the driver `[D38]` | Chris Beard (Texas Tech, Texas) `[D38][D43]`. **Baylor (Scott Drew)**: square up to the outside, early baseline help (often outside the paint), weak side zones up. Ices sideline ball screens and otherwise switches everything aggressively. 3rd nationally in TO% (2021) `[D77]`. Baylor and Texas Tech named by `[D39]`. Nebraska 2025-26 `[D42]` | Middle ball screens. Skip-then-attack. Short corner and dunker spot vs baseline help. Pick-and-pop vs ice | (1) **Middle-shade offset**: on-ball defender sits 0.3–0.8 m closer to the middle (smaller \|x\|) than the handler when the ball is on the wing or corner (θ<50° or >130°). (2) Drive-direction ratio: baseline drives / all drives ≥ 0.6 on side possessions. (3) Weak-side low defender within 2 m of the ball-side block or dunker spot when the ball is in the corner. (4) Side PnR → ice signature (F3) |
| **Force to help-middle / "no baseline"** | Eliminate baseline drives, because help sits in the middle `[D43][D3]` | Virginia (Bennett) `[D43]` | Middle pull-ups. Kick-out from the middle | On-ball defender offset to the **baseline** side by 0.3–0.8 m. Baseline drive rate ≤ 0.3 |
| **Force-sideline (toes-to-sideline)** | Don't force baseline or the corner. Force to the sideline with toes pointed at it. Help attacks penetration early `[D43]` | Beard `[D43]` | — | Defender's offset vector points toward the near sideline (Δx toward x=0 plus Δy toward half-court), not toward the baseline |
| **Classic "sideline then baseline"** | Force the ball to the sideline, then to the baseline. Close out with the sideline foot back. Ball in the corner → load all five to that side `[D41]` | Generic `[D41]` | Skip | All 5 defenders with s(d) > 0 (ball side) when the ball is in the corner |

### F1.4 Switching family

| Scheme | Definition | Programs | Counters | Detection signature |
|---|---|---|---|---|
| **Switch-everything** | Elite rosters with five comparable athletes switch all screens. Switch tight with contact. Each switch is a new matchup `[D19]` | Generic `[D19]` | Mismatch hunting (re-screen to get the big on the guard). Slips. Post-seal on the small | ≥ 80% of `SCREEN` events (on- and off-ball) produce `SWITCH` within 1.0 s. Low ice/drop/hedge counts |
| **1-4 switching** | X5 stays inside and never switches. The other four switch everything `[D19]` | Generic `[D19]` | Use 5 as the screener (forces a non-switch coverage) | Switch rate ≥ 0.8 for screens not involving the C's man. ≈ 0 for screens where the C's man screens |
| **Situational switching** | Switch only after timeouts, only on wing ball screens, or only in the last 5–10 s of the shot clock `[D19]` | MSU switched ball screens with its 5 vs Michigan in 2018-19 (27 possessions, 0.67 PPP `[S69]`). Michigan's guards and wings were held to 0.58 PPP over three games `[D25]` | — | Switch rate conditioned on context: shot clock ≤ 10 s, possession after timeout, PnR θ (wing vs top). A rate jump ≥ 0.5 between contexts = situational |
| **Switch-back rules** | After a big-small switch: help side active, deny the post, switch back ASAP, often on the next perimeter (especially weak-side) pass `[D19]` | — | Quick post entry | A `SWITCH` followed within 3 s by a reverse `SWITCH` of the same pair, without a screen, on a pass event |

### F1.5 D-I program defensive profiles (for priors)

| Program / coach | Base | Ball-screen default | Post | Notable | Source |
|---|---|---|---|---|---|
| Virginia (Tony Bennett; retired 2024 [UNVERIFIED for current staff]) | Pack line | Aggressive on the spectrum `[D9]`. No ice `[D1]` | 3/4 high side. Trap from the middle `[D43]` | No baseline. Fight through screens `[D3]` | `[D1][D3][D9][D43]` |
| Houston (Kelvin Sampson) | Pressure/deny man | Blitz (71% ball out of hands) | Monster post trap | Fly-by closeouts. Block rate 19% | `[D7][D8]` |
| Iowa State (Otzelberger) | Pressure man | Blitz/hedge (measured) | — | Top in Big 12 TO rate | `[D7]` |
| Tennessee (Rick Barnes) | Gap/shell man; "get into their shell and their gaps" (Underwood) `[D6]` | [UNVERIFIED]. One game study shows PnR threes pushed to 25+ ft and many pull-ups forced `[D22]` | [UNVERIFIED] | Length and physicality `[D6]` | `[D6][D22]` |
| Texas Tech / Texas (Chris Beard) | No-middle | Ice | Far-side post comes up | Baseline trap help | `[D38][D43]` |
| Creighton, Alabama | — | Sagging/drop end of the spectrum | — | — | `[D9]` |
| Syracuse (Jim Boeheim, through 2023) | 2-3 zone as primary | — | — | See F8 | `[D31][D20]` |
| Purdue (Painter) | Man | — | — | Occasional 1-2-2 match-up | `[S75]` |
| Michigan State (Izzo) | See F1.6 | | | | |

### F1.6 Michigan State (Tom Izzo) man principles: documented elements

| Element | What is documented | Source | Detection signature / label |
|---|---|---|---|
| Base mix | "90-some percent" man-to-man. A 2-3 zone is practised as a change-up, e.g. for foul trouble | `[S74]` | Prior: P(man) ≈ 0.9+ per possession |
| Positioning | "Six eye" half-court positioning. Shell variations. Named drills: Negaunee, Beat and Belt, Three-Man DHO Switching, Pin Down & Flares, side and top PnR drills | `[S6]` | Three-Man DHO Switching suggests **DHOs are switched** [UNVERIFIED in games] → test the DHO switch rate (F4) |
| Stance | Square stance, one hand up, step to split the stance to force direction. Contest passes as well as shots | `[S66]` | Needs pose |
| Ball pressure & containment | Ball pressure forces more TOs than the other four defenders. Contain the ball, because multiple help rotations leave players out of rebounding position. Requires **elbow help and block help** | `[D4]` | Help positions: when the ball is on the wing, one help defender within 1.5 m of the ball-side elbow (±1.83, 4.2) and one within 1.5 m of the block/dunker area. Rotation count per drive should be low (≤ 1 `ROTATE`) |
| Ball screens, 2017-20 | Base was a **soft hedge** (2019-20). Rarely switched 1-5 (never vs Wagner in 2017-18), but switched vs Michigan in 2018-19 | `[D25]` | Soft hedge = X-big 0–1.5 m above the screen line, short duration (< 1.0 s). See F3 |
| Ball screens, historical | Bigs flat- or hard-hedge. Weak-side rotations tag the roller, then the bigs recover | `[S69]` | Hedge + `TAG` from the weak-side low man |
| Ball screens, 2024-25 | "Aggressive" coverage: hedge + recover and/or blitz. Zapala, Kohler and Cooper hard-hedged (slips exploited). Gap defenders (Richardson, Kohler) **bump the roller** | `[D24]` | Hedge share high. Gap bumper = an off-ball defender contacts (≤ 0.8 m) the roller within 1 s of the roll start |
| Paint protection, 2024-25 | Closing lineup with Kohler + Cooper "clogging the paint". Opponents shot 28% 3P and 40% FG (as of Feb 28, 2025). KenPom AdjD #6 | `[D58]` | Two bigs both at r < 3 m during drives |
| 2025-26 | KenPom AdjD #2 (Jan 15, 2026). 90.6 pts/100 in Big Ten play. Opponent 3PA rate 47.4% (15th-highest in D-I; D-I average 39.8%). Opponent 2P 46.0%, 3P 30.4%. Fears is a disruptive POA defender | `[D57]` | Prior for a paint-first scheme. Coverage still [UNVERIFIED] |
| Full-court pressure, 2023-24 | Pressed baseline-to-baseline more than in prior years in exhibitions. 20 forced TOs vs Tennessee. Izzo: half-court D "weren't very good" | `[D5]` | Press detection F9. Expect a man press (full-court man) [UNVERIFIED structure] |
| Rebounding & transition link | "Hit, Find and Fetch". Low man wins the initial contact. **Send 4 to the offensive glass with the PG back** | `[D4]` | F12: MSU's get-back count after its own missed shots is typically 1 (the PG) |

---

## F2. ON-BALL DEFENSE RULES

On-ball rules are labeled on the **primary on-ball defender** (the HMM matchup of the ball-handler) every frame. Labels are not exclusive: a possession can have `pressure=high` and `force=sideline` at the same time.

```
F2 On-ball
├── F2.1 Pressure level: pick-up point (full / 3/4 / half / arc), cushion
├── F2.2 Force direction: no-middle, no-baseline, sideline, weak hand, "quickest path"
├── F2.3 Containment: stay-in-front, retreat step, swing step, beaten → help trigger
├── F2.4 Dead-ball / picked-up dribble: "inch up", swarm, deny-all
└── F2.5 Closeout-to-on-ball transitions (see F7.6)
```

| Rule | Definition | Source | Detection signature [HEURISTIC] |
|---|---|---|---|
| **Pick-up point** | Where the on-ball defender first engages the handler: full-court, 3/4, half-court, or at the arc [CONVENTION] | — | Record y_b at the first frame where dist(d_ball, b) ≤ 1.5 m and d_ball faces the handler. Classes: full (y_b > 21 m), 3/4 (16–21), half (12–16), arc (< 9.5) |
| **Ball pressure (tight)** | Pressure the handler without fouling. Pack line wants the on-ball defender "right up on" the ball `[D3]`. Izzo: ball pressure forces more turnovers than the other four defenders `[D4]` | `[D3][D4]` | Mean dist(d_ball, b) ≤ 1.2 m while dribbling. "Loose cushion" ≥ 2.0 m |
| **Cushion vs threat (scout-driven)** | Tighten or give cushion to keep the ball in front, one of five checkpoints in a Houston-clip clinic `[D11]` | `[D11]` | Per-handler mean cushion. Compare it with the handler's 3P% to infer scouting |
| **Force middle-away (no-middle)** | See F1.3. The stance is parallel to the sideline with a high foot `[D38]` | `[D38]` | Middle-shade offset 0.3–0.8 m |
| **Force away from the baseline** | Bennett: no baseline drives `[D43]` | `[D43]` | Baseline-shade offset |
| **Weak (force to the weak hand)** | Force the handler to his weak hand, regardless of screen direction `[D10][D72]` | `[D10][D72]` | Offset on the handler's strong-hand side (needs handedness metadata). The weak-hand dribble share rises |
| **Inch up on a picked-up dribble** | When the dribble is picked up, step closer to take away vision (Cronin) `[D4]`. Pack line: all four may deny on a dead ball `[D3]` | `[D3][D4]` | On a `DRIBBLE_END` event: dist(d_ball, b) drops by ≥ 0.4 m within 0.5 s. All one-pass-away defenders move onto passing lanes (deny index → 1) |
| **Containment failure ("beaten")** | The handler gets level with or past the on-ball defender. This triggers help (F7) | [CONVENTION] | The handler's projection onto the rim line is closer to the rim than d_ball's: r_b < r_d_ball − 0.3 m. Duration ≥ 0.3 s = **blow-by** |
| **Retreat step / swing step / mirror the ball** | FIBA footwork terms `[D10]` | `[D10]` | Pose. Out of scope for position-only tracking |

---

## F3. BALL-SCREEN (PnR) COVERAGES

The first pass (§2.2) gave one-line definitions and a coarse signature table. This section adds a hierarchy, roles, help assignments (F7 links), programs, counters, and **numeric signatures in metres**.

### F3.0 Measurement frame for every ball screen [HEURISTIC]
At `SCREEN(s→u)` with u holding the ball, define:
- **Screen point** P_s: the screener's position at contact time t₀.
- **Screen line**: the line through P_s perpendicular to the handler's pre-screen velocity. **Level offset** λ(d) = signed distance of a defender from the screen line along the handler's direction of travel. Positive = beyond the screen, in the handler's path toward the rim. Negative = on the handler's starting side (above).
  Then:
  - **X-big depth** = −λ(X-big) at t₀ + 0.3 s. Positive = dropped below the screen toward the rim.
  - **X-ball path class**: over (X-ball passes on the handler side of P_s), under (rim side of P_s *and* the screener's defender, i.e. X-big), through (between the screener and X-big), or ice (X-ball sits between the handler and the screen *before* t₀).
- **Screen location class**: middle (|x_s| < 2.5 m and y_s > 6 m), wing/side (|x_s| ≥ 2.5 m), step-up/sideline, empty-side (no offensive player in the corner and wing on the screen side), or drag (in transition, < 4 s after crossing half).
- **Coverage resolution window**: t₀ − 1.0 s to t₀ + 2.0 s. Pre-screen positioning (ice, pre-switch) is decided before t₀.

```
F3 Ball-screen coverages
├── F3.1 Containment ("two-man contain") family
│   ├── Drop ─ variants: deep/low drop, high drop (mid), "catch" drop
│   ├── Flat / at-the-level contain ─ "up to touch", flat hedge
│   └── Under (X-ball under; X-big stays home)
├── F3.2 Show family
│   ├── Soft hedge / show
│   ├── Hard hedge (hedge-and-recover)
│   └── Hedge-to-switch ("show and stay") [CONVENTION]
├── F3.3 Two-on-ball family
│   ├── Blitz / trap (above the screen)
│   ├── Blitz-to-switch (FIBA: double after a switch)
│   └── "Next" / run-and-jump off the screen
├── F3.4 Exchange family
│   ├── Switch ─ variants: straight switch, jump switch, "Black"/active switch (LoGalbo)
│   ├── Pre-switch
│   ├── Peel switch
│   ├── Triple switch / scram (mismatch repair)
│   └── Steer switching (FIBA)
├── F3.5 Directional family
│   ├── Ice / Blue / Down / Push / Fan (side PnR)
│   ├── Weak (force the weak hand)
│   └── Strong [CONVENTION]
└── F3.6 Spain/stack-PnR coverages (top-lock the back-screener, pre-switch, "next")
```

### F3.1 Containment family

| Coverage | Roles | Help assignment | Programs (sourced) | Counters | Detection signature |
|---|---|---|---|---|---|
| **Deep / low drop** | X-big sits near the nail or between the roller and the rim, backpedalling with "no man behind". X-ball usually goes over, or under against an efficient mid-range scorer `[D72]`. FIBA: X-big a few steps below the screen `[D10]`. Drop became the most popular coverage over the last 10–20 years, replacing hedging. It concedes pull-up twos `[D40]` | No tag needed; two defenders contain `[D72]` | Creighton and Alabama sit at the sagging end of the spectrum `[D9]`. LoGalbo uses drop only for **middle** PnR `[D26]` | Pick-and-pop, snake dribble, pull-up shooter, Spain PnR (back-screen on X-big) `[D27][D72]` | X-big depth ≥ 3.5 m at t₀+0.3 s, *and* r_Xbig ≤ 5.5 m (near the nail or FT line). X-ball path = over, or under. **No** second defender within 1.5 m of the handler. Roller-to-X-big distance ≤ 2.0 m during the roll |
| **High drop (mid/level-ish)** | X-big about two steps behind the screen, prioritising containment of the ball. X-ball stops the reject and must use the screen, then recovers `[D72]` | A tag man must pick up the roller `[D72]` | — | Quick pop, fast ball movement to the popper `[D72]` | X-big depth 1.0–3.5 m. Tag defender (F7.2) within 1.5 m of the roller by t₀+1.2 s |
| **Flat hedge** | X-big just below the screen level to slow penetration (FIBA) `[D10]` | — | MSU bigs historically "flat or hard hedge" `[S69]` | Slip, roll behind | X-big depth 0–1.0 m, lateral (x) offset into the handler's path ≥ 0.5 m |
| **At the level / "up to touch"** | X-big starts at the screen's height, touching the screener `[D10]` | Tag roller | — | Slip, early roll | \|λ(X-big)\| ≤ 0.6 m and dist(X-big, screener) ≤ 1.0 m at t₀ |
| **Under (X-ball under)** | X-ball goes under the screen. X-big need not act `[D27]` | — | Against non-shooters [CONVENTION] | Pull-up three over the screen `[D27]` | X-ball path: rim side of both the screener and X-big. Handler's distance to the nearest defender at t₀+0.5 s ≥ 2.0 m |

### F3.2 Show family

| Coverage | Roles | Help assignment | Programs | Counters | Detection signature |
|---|---|---|---|---|---|
| **Soft hedge / show** | X-big shows briefly in the handler's path, then gets back to the screener [CONVENTION]. MSU's 2019-20 base was a soft hedge `[D25]` | Low-man tag if the X-big recovery is late | **MSU 2019-20** `[D25]` | Slip. Short roll | λ(X-big) between −1.0 and +0.5 m (at or just above the level), with show duration (time with \|λ\| < 1 m and lateral to the handler) ≤ 0.8 s, then X-big moves toward the screener at ≥ 3 m/s |
| **Hard hedge (hedge-and-recover)** | X-big steps 1–2 steps above the screen and lateral to the handler. X-ball fights over, close to the screener's hip, then recovers. X-big recovers to the screener `[D72][D27]` | Tag man, usually from the corner, tags the roller, creating 4-on-3 on the backline `[D72]` | MSU 2024-25: hedge + recover with Zapala, Kohler and Cooper. Gap defenders bump the roller `[D24]`. MSU historical `[S69]` | Slip. Short roll 4-on-3. Empty-side PnR (no tag man). Late tags → open threes `[D72]`. Michigan exploited Kohler's hard hedge with slips `[D24]` | λ(X-big) ≤ −0.6 m (above the screen), lateral offset ≥ 0.8 m into the handler's path. Hold duration 0.5–1.5 s. Then a **recovery sprint**: X-big speed ≥ 4 m/s toward the screener within 1.5 s. The handler's dribble is pushed laterally or backward (handler v_y ≥ 0 for ≥ 0.3 s) |
| **Hedge-to-switch ("show and stay")** | X-big shows and stays on the ball. X-ball takes the screener [CONVENTION] | — | — | Mismatch | Hard-hedge geometry followed by persistent `SWITCH` |

### F3.3 Two-on-ball family

| Coverage | Roles | Help assignment | Programs | Counters | Detection signature |
|---|---|---|---|---|---|
| **Blitz / trap** | X-big at screen level or above, traps with high hands until the dribble stops. X-ball forces the handler diagonally toward half-court `[D72]`. FIBA: X-big above the screen and traps `[D10]` | Backline plays 4-on-3. A corner defender may be sacrificed to pressure the nearest outlet `[D72]`. Weak side tags the roller `[D27]` | **Houston**: ball out of hands on 71% of screens `[D7]`. Iowa State `[D7]`. MSU 2024-25 "and/or blitz" `[D24]` | Short roll to 4-on-3. Skip. Slip before the trap. Pass early `[D72]` | `TRAP(X-ball, X-big, handler)` with λ(X-big) ≤ +0.5 m. Both within 1.5 m of the handler for ≥ 0.6 s. Handler's distance from the rim increases (pushed back) ≥ 1.0 m. Ball-out-of-hands within 2.0 s is a strong confirmatory feature |
| **Blitz-to-switch** | Double-team after a switch, to stop a mismatch or a late shot (FIBA) `[D10]` | — | — | Quick pass | `SWITCH` then `TRAP` within 2 s, on the same handler |
| **"Next" (run-and-jump off a screen or penetration)** | After the screen, a third defender "jumps" the ball and the others rotate to force a pass (FIBA) `[D10]` | Rotation | — | Pass to the vacated man | Defender d3 (neither X-ball nor X-big) becomes the ball matchup within 1 s of t₀. X-ball and X-big rotate out |

### F3.4 Exchange family

| Coverage | Roles | Help assignment | Programs | Counters | Detection signature |
|---|---|---|---|---|---|
| **Switch (straight)** | Defenders exchange assignments `[D10]`. The new X-ball (former X-big) stays high enough to stop the shot. The new X-screener (former X-ball) fronts or denies the roller `[D72]` | Tag the roller until the switch completes `[S67]` | MSU vs Michigan 2018-19 with the 5 `[D25][S69]`. LoGalbo "Black" `[D26]` | Slip, slip-and-seal, post the mismatch `[D72]`. Isolation hunting | `SWITCH(X-ball, X-big)` with reciprocal matchup probability > 0.8 by t₀+1.0 s, persisting ≥ 2 s. No trap |
| **"Black" (LoGalbo active switch)** | X-ball goes **under** to stop the roll. X-big touches hands so the offense can't split, then actively switches as the handler extends `[D26]` | — | LoGalbo/outer-third `[D26]` | Split | Under-path for X-ball, plus X-big and X-ball within 1.2 m of each other at t₀ (no split gap), then swap |
| **Jump switch** | On under ball screens or handoffs: X1 goes under the screener, X5 sprints above to pressure the ball, and they swap `[D19]` | — | — | Re-screen | X-big moves above the screen (λ ≤ −0.5 m) at speed ≥ 4 m/s *before* the handler reaches the screen line. X-ball goes under. Swap |
| **Pre-switch** | A quicker defender guards the screen action before it happens. The original screener's defender stays near the rim `[D72]`. FIBA: off-ball switch before a ball screen `[D10]` | — | — | Recognise and re-screen | `SWITCH` between X-ball's teammates **before** t₀ (−3 s to −0.3 s), with no screen at that moment. Typically the C's matchup leaves the incoming screener |
| **Peel switch** | A help defender switches onto the beaten handler. The original defender peels to the vacated man. The rim protector may switch onto the roller `[D10][D72]` | — | — | — | After a blow-by (F2), a helper takes the handler and the original defender takes the helper's man within 1.5 s (a 3-way matchup permutation) |
| **Triple switch / scram** | Two switches in sequence with a third defender, to avoid a mismatch `[D10]`. LoGalbo suggests a triple or scram switch when a guard is on a big `[D26]` | — | — | Quick post entry | 3-cycle matchup permutation within 3 s |
| **Steer switching** | X-big pushes the screener toward the ball defenders to force a switch `[D10]` | — | — | — | Pre-t₀ contact between X-big and the screener, with screener displacement ≥ 0.5 m toward the ball |

### F3.5 Directional family

| Coverage | Roles | Help assignment | Programs | Counters | Detection signature |
|---|---|---|---|---|---|
| **Ice / Blue / Down / Push / Fan** | X-ball jumps the screen side and forces a reject toward the sideline or baseline. X-big sits on the side the handler is forced toward, keeping "no man behind" `[D72][D10]`. X-ball turns parallel to the sideline `[D27]`. Defender calls "Ice!" early and X-big holds the handler until X-ball recovers `[D19][D26]` | Low man tags the roller `[D27]`. The sideline acts as a 6th defender, and traps are possible `[D72]` | Beard (no-middle) `[D38]`. LoGalbo for side PnR `[D26]`. **Virginia does not ice** `[D1]` | Pick-and-pop vs X-big (late closeout) `[D27]`. Communication breakdown → middle drive `[D72]`. Re-screen ("flip") [CONVENTION] | Screen location = side. **Pre-t₀**: X-ball between the handler and the screener (perpendicular distance ≤ 0.8 m to segment(handler, P_s)), on the screen side for ≥ 0.5 s before t₀. X-big below the screen (depth 1–3 m) and offset toward the baseline/sideline. Handler's post-screen velocity has \|x\| increasing (away from the middle) or v_y < 0 (toward the baseline) |
| **Weak** | Force the weak hand regardless of screen direction `[D10][D72]` | — | — | Dominant-hand hesitation `[D72]` | Requires handedness. X-ball offset to the strong-hand side for ≥ 0.5 s pre-t₀, whichever side the screen is on |
| **Strong** | The opposite of weak (a team may "give up" the left side) `[D72]` | — | — | — | — |

### F3.6 Spain / stack PnR coverages

| Coverage | Description | Source | Detection signature |
|---|---|---|---|
| **Top-lock the back-screener** | X-back-screener sits on the top side to deny his man's pop after the back screen | `[S19][S25]` | Defender of the back-screener above (larger λ) the screener at screen time |
| **Pre-switch / "next" vs Spain** | Swap assignments before the Spain back screen hits X-big | `[S19][D10]` | Swap before the back-screen contact |
| **Drop vulnerability** | Spain is a named counter to drop (it forces X-big to avoid a back screen) | `[D27]` | Context flag: Spain + drop → expect a rim attempt or a late tag |

### F3.7 Coverage-spectrum feature (continuous)
The Hoop Vision spectrum runs from aggressive (attack the handler) to sagging (concede space to the handler) `[D9]`. **Aggression index A** = −depth(X-big) + 1.5·[TRAP] + 0.5·[hedge lateral offset > 0.8 m]. A team-level mean of A by game gives a scouting fingerprint: Houston high, Creighton and Alabama low `[D9]`. Prior work on SportVU: a rule-based plus ML screen detector reached ~82% sensitivity and ~80% PPV `[S60]`. Coverage classification across 270k screens `[S61]`. A model of defensive-strategy deviations vs PnR using all 10 players reached up to 69% accuracy `[D37]`.

---

## F4. DRIBBLE-HANDOFF (DHO) COVERAGES

```
F4 DHO
├── Switch (Loyola/Valentine; Izzo "Three-Man DHO Switching" drill)
├── Under (giver's defender opens, receiver's defender goes under)
├── Over / chase [CONVENTION]
├── Hedge / show at the handoff
├── Jam / deny the receiver (prevent the handoff)
├── Jump switch on the handoff
├── Ice the handoff (force the receiver away from the giver) [CONVENTION]
└── Trap the receiver [CONVENTION]
```

| Coverage | Roles | Programs | Counters | Detection signature [HEURISTIC] |
|---|---|---|---|---|
| **Switch** | The on-ball (giver's) defender doesn't press the ball and keeps a hand up. He steers the dribbler sideways to stop a wheel (keep) and steps up as the switch happens, calling it. The receiver's defender plays high in his gap with his head on a swivel for the back-cut `[D28]` | Loyola Chicago (Drew Valentine) `[D28]`. Izzo's practice drill "Three-Man DHO Switching" `[S6]` | Keep and turn the corner. Back-cut by the receiver before the exchange. Screener (giver) slips to the rim | At `DHO(a→b)` time t_h: d_a takes b and d_b takes a within 0.8 s (reciprocal matchup). No trap |
| **Go under** | The receiver's defender goes under the giver at the handoff to stop penetration `[D30]` | — | Catch-and-shoot three off the handoff | d_b's path passes on the rim side of the giver *a* at t_h ± 0.3 s. Receiver's open distance at catch ≥ 2.0 m |
| **Over / chase** | The receiver's defender trails over the top of the giver, staying attached [CONVENTION] | — | Giver re-screens. Downhill turn | d_b's path is on the receiver side of the giver, within 1.0 m of b throughout |
| **Hedge** | The giver's defender steps up above the giver at the handoff to stop penetration, then both recover `[D30]` | — | Giver's dive/slip | d_a moves ≥ 0.8 m into the receiver's path (λ ≤ −0.5 m) at t_h, then recovers to *a* within 1.5 s |
| **Jam / deny** | An off-ball defender uses his body to block the receiver's path so the handoff can't happen `[D30]`. FIBA "jam the cutter" `[D10]` | — | Back-cut ("ghost handoff") | Before t_h: d_b sits between b and the giver, on b's approach path, for ≥ 0.5 s. The handoff aborts (no DHO), or b back-cuts |
| **Jump switch** | Used on handoff (weave) screens: one defender goes under, the other sprints above to pressure `[D19]` | — | Re-handoff | As F3.4, with a DHO trigger |
| **Ice the handoff** | d_b forces the receiver away from the giver (toward the sideline) and d_a drops [CONVENTION] | — | Reject back-cut | d_b on the giver side of b before t_h |
| **Trap the receiver** | Both defenders trap the receiver after the exchange [CONVENTION] | — | Short-roll pass to the giver | `TRAP(d_a, d_b, b)` within 1 s after t_h |

---

## F5. OFF-BALL SCREEN COVERAGES

```
F5 Off-ball screens
├── F5.1 Down screens / pin-downs: trail (lock-and-trail), top-lock, under / shoot-the-gap, switch (equal matchups), bump/show, "next" (stunt or rotate)
├── F5.2 Back screens / UCLA: switch, step-in-front, show-and-recover, "jam"
├── F5.3 Flares: switch, chase over, under
├── F5.4 Cross / post screens: step under & switch (high cut), step under & stay (low cut), front-the-cutter
├── F5.5 Staggers / floppy / Iverson / elevator: top-lock, switch-everything, "trail-and-tag"
└── F5.6 Screener's-defender techniques: bump the cutter, open up/"let him through", top-side the screener (vs slip/pop), jam the cutter
```

| Coverage | Definition / roles | Source | Counters | Detection signature [HEURISTIC] |
|---|---|---|---|---|
| **Chase / trail (lock-and-trail)** | The cutter's defender locks onto the cutter's hip and trails over the screen. Down screens default to chasing with no switch `[D19]`. Pack line chases through every screen and stays within touching distance `[D3]` | `[D3][D19][D69]` | Curl (tight cut to the rim). Defender caught on the screen → screener slips | d_cut's path is within 1.0 m of the cutter's path with a lag of ≤ 0.6 s. The path crosses the screen on the **ball side** of the screener. The screener's defender stays home |
| **Top-lock** | The defender takes the top side of the cutter (between cutter and screen), chest-to-shoulder, forcing the cutter backdoor or away. The backline must tag the backdoor. Used vs pin-downs, staggers, floppies and Iverson cuts `[D73]` | `[D73][S25][S19]` | Back-cut, screener slips into space, re-screen ("rescreen", "screen the screener") `[D69]` | **Before the cutter reaches the screen**: d_cut's y (along the cutter's intended path) is beyond the cutter's position, i.e. λ(d_cut) < 0 relative to a screen line oriented with the cutter's planned direction, *and* d_cut is on the screen side, within 1.0 m. Back-cut rate of the cutter ↑ |
| **Under / shoot the gap** | The defender goes under the screen (between screener and rim) and beats the cutter to his destination. Used against average or below-average shooters. Vulnerable to the fade `[D74]`. Pack line allows it on weak-side screens `[D3]` | `[D3][D74][D69]` | Fade, curl-to-pop, re-screen `[D69][D74]` | d_cut's path passes on the rim side of the screener (r_d < r_screener at the crossing) and reaches the cutter's catch spot within 0.4 s of the cutter |
| **Switch (off-ball)** | Back screens and flares are usually switched. Down screens only switch on equal matchups. Inside post screens: step under, then stay on a low cut and switch on a high cut `[D19]` | `[D19]` | Slip of the screener, mismatch post-up | `SWITCH(d_cut, d_scr)` within 0.8 s of the screen contact |
| **Bump / show** | The screener's defender bumps the cutter, then recovers to the screener `[D19]` | `[D19]` | Screener slips during the bump | d_scr moves ≥ 0.8 m toward the cutter's path at contact, then returns to the screener within 1.2 s |
| **Off-ball "Next" (stunt or rotate)** | Against a wide pin-down, the "next" defender trails to funnel the shooter, then stunts into the gap or fully rotates onto the ball. The shooter's original defender sprints underneath to close out on the shooter, now the ball. The far-side defender "stunts and funnels" if the pass goes back to the top. It depends on the scouting report (stay home vs a 31% shooter) `[D29]` | European (Slappin' Glass) `[D29]` | Flare for the passer. "Boomerang" pass back `[D29]` | A third defender (not d_cut or d_scr) makes a `STUNT` or `ROTATE` toward the curling cutter within 0.8 s of the cutter's catch. d_cut then takes an under-path |
| **Jam the cutter** | Step into the cutter's path (FIBA) `[D10]` | `[D10]` | Back-cut | d_cut's body is on the cutter's path, cutter's velocity drops ≥ 30% |
| **Defending staggers / double screens** | Switch every screen quickly and reconnect to new assignments `[D19]` | `[D19]` | Screen-the-screener | Multiple sequential `SWITCH` events in ≤ 2 s |
| **Box-and-1 chaser screen choice** | The chaser picks "lock and trail" or "shoot the gap" by screen angle. Box defenders call screens and bump the star `[D68]` | `[D68]` | — | See F10 |

**Read map (what the offense sees):** gap/under → shot or re-screen. Lock-and-trail and top-lock → read open space (curl or back-cut) `[D69]`. This is useful as a *consistency check*: a label of "top-lock" should co-occur with back-cuts or rejects more than with curls.

---

## F6. POST DEFENSE

```
F6 Post defense
├── F6.1 Pre-catch positioning: full front, 3/4 high side, 3/4 low side, behind, "push out" (deny + displace)
├── F6.2 Post-catch: play behind straight-up, "one-step cushion", yo-yo / dig
├── F6.3 Double-team schemes: from top, from passer, from lowest/baseline, from weakest player, big-to-big, Monster/designated, choke
├── F6.4 Post rotations after a double: split-line, "help the helper", nail/basket "my ball"
└── F6.5 Lob protection: low-man lob responsibility, face-guard + safety (inbound)
```

### F6.1–F6.2 Positioning techniques

| Technique | Definition / roles | Programs / source | Counters | Detection signature [HEURISTIC] |
|---|---|---|---|---|
| **Full front** | The defender is between the post and the ball `[D10]`. Classic man: front the low post as the ball moves to the wing and corner `[D41]`. Bo Ryan: front on a dead-front position `[D4]` | `[D4][D10][D41]` | Lob over the top. The help-side post must double, and the opposite wing drops to the block `[D41]` | Post defender p_d with t ∈ [0.0, 0.4] on segment(post→ball) and perpendicular distance ≤ 0.5 m. Distance to the ball < distance of the post to the ball |
| **3/4 high side** | The defender sits on the high side with an arm across the front. Bennett's pack line `[D3][D43]`. Painter: when the ball is above the FT line, 3/4 and never two feet in front `[D47]` | Virginia `[D43]`. Purdue `[D47]`. Western Michigan (Stephens) `[S72]` | Low-side seal and baseline entry | Angle ∠(rim→post, post→d) ≈ 45–90° on the half-court side. dist ≤ 0.9 m |
| **3/4 low side / push out** | Ball below the lane: deny 3/4 and push the post out as far as possible `[D47]` | Purdue `[D47]` | High-side flash | Defender on the baseline side. Post's r increases ≥ 0.5 m during the denial |
| **Behind** | The defender is between the post and the rim [CONVENTION]. Pack line: once the ball enters, slip behind `[D3]` | `[D3]` | Turnaround over a smaller defender | Defender on segment(post, rim), 0.3–1.0 m from the post |
| **One-step cushion** | Don't lean or hug. Keep one step of space (Bo Ryan) `[D4]` | `[D4]` | Face-up | dist(p_d, post) ≈ 0.6–1.0 m on the catch |
| **Yo-yo / dig** | An off-ball defender bothers the post dribble by hitting at the ball and recovering. "Dig hard" is an aggressive yo-yo `[D10]` | `[D10]` | Kick-out to the digger's man | A perimeter defender moves ≥ 1.5 m toward the post-catcher, comes within 1.2 m, then returns ≥ 1.0 m toward his own man within 1.5 s, with no matchup change |
| **Spy** | The defender of the pivot (center) stays in the paint to help on cuts and rim shots `[D10]` | `[D10]` | Pop or face-up by that big | Defender of a non-post big has r_d < 3 m while his man is at r > 5 m |

### F6.3 Double-team schemes

| Scheme | Who comes / when | Rotations of the other three | Programs / source | Counters | Detection signature |
|---|---|---|---|---|---|
| **Top double** | The highest defender turns and sprints from the top on the flight of the entry pass `[D45]` | The lowest stays on the split line under the rim. The second-lowest slides to the high split line `[D45]` | `[D45]` | Pass to the vacated top man. Ball reversal | The arriving defender's starting position has y > 5.5 m and is not the post defender. Arrival within 0.8 s of the catch |
| **Double from the passer** | The strong-side guard who passed the entry doubles `[D45]` | No practical rotation. The guard returns on the kick-out `[D45]` | `[D45]` | Return pass for a three | The doubler is the same player as the passer's defender |
| **Baseline / lowest-defender double** | The lowest weak-side defender, usually the other big, doubles from the baseline `[D45]` | The second-lowest drops to the low split line. The top defender drops to the high split line `[D45]` | `[D45]`. FIBA level-3 variants `[D46]` | Big-to-big dump pass. Flash cut | The doubler's start position is at y < 2 m on the weak side (s(d) < 0). Path along the baseline |
| **Double from the weakest player** | The designated defender leaves the weakest offensive player `[D45]` | Split-line help `[D45]` | `[D45]` | Weakest player cuts | The doubler's original man has the lowest 3P% (metadata) |
| **Big-to-big (Painter)** | The weak-side big cheats on the wing ball and arrives as the post catches. No double if the post is off the block. If the double is late, scrape ball-side. Stay if the post dribbles baseline, return if he dribbles to the middle `[D47]` | The nail and basket defenders race to the first pass. "My ball" and bump `[D47]` | **Purdue (Matt Painter)** `[D47]` | Wing big-to-big entries. Overloads `[D47]` | The doubler is the other big. Pre-catch drift of the doubler toward the ball-side block ≥ 1 m while the ball is on the wing. Arrival ≤ 0.5 s after the catch. Two weak-side defenders at roughly the nail (0, 4.2) and the rim (r < 2) |
| **Monster post trap (Houston)** | An immediate, hard double from a designated helper, usually the nearest baseline guard or the top guard, on a back-to-basket catch `[D8]` | The weak side rotates early to skip and corner `[D8]` | Houston `[D8]` | Quick skip | As the top double, but the arrival is ≤ 0.5 s and happens on ≥ 70% of post catches |
| **Choke / dig the post** | The closest perimeter player drops to deflect `[D3]`. Traditional pack line doubles any post `[D3]` | — | Pack line `[D3]` | Kick to the digger's man | The digger leaves a one-pass-away man |
| **Double down** | Drop from the perimeter to double a low post `[D10]` | — | `[D10]` | — | Generic: second defender within 1.5 m of the post-catcher for ≥ 0.6 s |
| **Trap from the middle** | Bennett traps posts from the middle of the floor `[D43]` | — | Virginia `[D43]` | Baseline kick | The doubler comes from \|x\| < 1.5 m (the nail or lane) |

### F6.4 Post-double rotation logic (for labeling)
"Help the helper": X1 rotates to low help and X2 to high help. Alternatively, X1 takes the second (nearest perimeter) pass `[D46]`. A two-man **split-line tandem** (high and low split-line defenders guarding three weak-side players) is the common structure `[D45][D47]`. The tracking signature is two weak-side defenders whose x lies within ±1.5 m of the lane centre, at y ≈ 0–2 m (low) and y ≈ 4–6 m (high), while three offensive players sit on the weak side.

### F6.5 Lob protection
The low (weak-side) man is responsible for the lob, not the post defender, when the post defender plays 3/4 top side (Stephens, Western Michigan) `[S72]`. Signature: when the post is fronted or 3/4-fronted, the weak-side low defender stays at r ≤ 2.5 m and |x| ≤ 2 m.

---

## F7. HELP & ROTATION SYSTEMS

```
F7 Help & rotation
├── F7.1 Help positions: on-the-line (1 pass), up-the-line / split line (2 passes), help-side line, nail, low man (LMH), "I" alignments (1i/2i/3i), open-corner
├── F7.2 Roller coverage: tag (bump), low-man meet-the-roller, gap bump
├── F7.3 Help actions: sink/sag, stunt, dig, show/hedge-help on a drive, help-and-recover
├── F7.4 Rotations: X-out, sink-and-fill, rotate-up (help the helper), scram switch, peel switch, "my ball/bump"
├── F7.5 Shrink / shift-to-ball; load to the ball (all 5 ball-side)
└── F7.6 Closeouts: sprint-stop, choppy, short, fly-by; angle by force rule
```

### F7.1 Help positions

| Position | Definition | Source | Detection signature [HEURISTIC] |
|---|---|---|---|
| **One pass away (deny)** | "On the line" (passing lane), hand and foot in the lane `[D41][D10]`. Pack line instead plays a gap position off the lane `[D3]` | `[D3][D10][D41]` | Deny: perpendicular distance to segment(a,b) ≤ 0.6 m, t ∈ [0.05, 0.35]. Gap: perpendicular distance 0.8–2.5 m toward the rim side |
| **Two passes away (help side)** | "Up the line" into the paint. Foot on the help-side line when the ball is in the corner or below the FT line `[D41]`. Bo Ryan: weak-side foot in the paint `[D4]` | `[D4][D41]` | \|x_d\| ≤ 1.8 m (in the lane) or within 1.0 m of the x = 0 help-side line, with s(d) < 0 |
| **Nail** | The help defender stationed at the nail (FT-line middle) to discourage middle drives. Painter uses nail + basket defenders to take the first pass out of a double `[D47]` | `[D47]` | A defender within 1.2 m of (0, 4.2) while the ball is on the wing and that defender's man is one pass away on the ball side |
| **Low man (LMH)** | The weak-side lowest defender. "LMH's first responsibility is meeting the roller." When the ball goes away, LMH comes from the away side. Hard show/blitz brings LMH up the lane early. Passive coverage keeps LMH near the restricted area `[D49]` | `[D49]` | The defender with the min y among weak-side defenders. During a PnR, it is the one with the min r. Flag "LMH up" when y ≥ 2 m during a hedge or blitz |
| **"I" alignments (1i, 2i, 3i) & open corner** | The backside defenders' stack relative to the ball. 2i is the most common X-out setup vs a corner skip. In open-corner (OC) spacing, LMH comes from 3i `[D49]` | `[D49]` | Count of weak-side defenders stacked within 2 m in x (vertical "I"). Open corner = no offensive player within 2 m of the ball-side corner (±7, ≤ 1) |
| **Elbow help & block help (Izzo)** | MSU requires both `[D4]` | `[D4]` | See F1.6 |

### F7.2 Roller coverage

| Action | Definition | Source | Detection signature |
|---|---|---|---|
| **Tag (the roller)** | An off-ball defender bumps the roller so he can't roll deep (FIBA) `[D10]`. In a hedge, the tag usually comes from the corner `[D72]` | `[D10][D72][D27]` | A non-X-big defender reaches ≤ 1.0 m of the roller between t₀+0.5 and t₀+1.8 s, at r_roller ≤ 4.5 m, then leaves within 1.5 s (no persistent switch) |
| **Gap bump (MSU 2024-25)** | Gap defenders positioned to bump the roller vs a hedge `[D24]` | `[D24]` | Same as tag, but the tagger came from a gap position (inside triangle(ball, rim, man)), not from the corner |
| **Meet the roller (LMH)** | `[D49]` | `[D49]` | The LMH's path intercepts the roller's path at r ≤ 3 m |

### F7.3 Help actions

| Action | Definition | Source | Detection signature |
|---|---|---|---|
| **Sag / sink** | Leave your man to drop into the lane and protect the basket `[D10]` | `[D10]` | Help depth ↑ ≥ 1.5 m within 0.7 s of a drive start |
| **Stunt** | A fake help that slows the dribbler, then recovers `[D10]`. VCU Havoc: "stunt at the ball" `[D55]` | `[D10][D55]` | `STUNT` (F0.4) |
| **Dig** | Aggressive yo-yo on a post or driver `[D10]` | `[D10]` | As yo-yo, with a closer approach (≤ 0.8 m) |
| **Help and recover** | Leave your man to help, then return `[D10]`. The beaten defender recovers and the helper returns `[D41]` | `[D10][D41]` | A helper moves ≥ 2 m off his man, then the original matchup is restored within 2 s |
| **Drive help ("show")** | The adjacent defender hedges to stop the dribble `[D41]` | `[D41]` | The adjacent defender's position enters the handler's projected drive path (a 1.5 m-wide corridor to the rim) |

### F7.4 Rotations

| Rotation | Definition | Source | Detection signature |
|---|---|---|---|
| **X-out (2i)** | (1) LMH meets the roller. (2) The top of the "I" sinks to guard both and takes the first pass. (3) The top of the "I" closes out to the corner. (4) LMH closes out to the top-of-"I" man. If the ball goes to the wing, both return `[D49]` | `[D49]` | Two weak-side defenders swap assignments **crossing paths** (their trajectories intersect) within 2.5 s after a skip pass. A matchup swap with crossing = X-out. Without crossing = sink-and-fill |
| **Rotate-up / help the helper** | X1 to low help, X2 to high help, after a baseline double `[D46]`. Baseline penetration: the low post defender traps, the wing doubles, the opposite post covers, and the weak wing drops `[D41]` | `[D41][D46]` | A chain of ≥ 3 `ROTATE` events within 2 s, each defender moving toward the rim-side vacancy |
| **Scram switch** | When a guard is on a post, the adjacent big takes the post as the entry is in the air, and the guard rotates out `[D19]` | `[D19]` | `SWITCH` triggered by a `PASS` to the post (ball in flight), not by a screen |
| **Peel switch** | See F3.4 `[D10]` | `[D10]` | — |
| **"My ball" / bump** | After a kick-out from a double, the nail and basket defenders race to the pass. One calls "my ball" and bumps the other to the nearest man `[D47]` | `[D47]` | Two defenders converge on the receiver, one peels within 0.8 s |
| **Load to ball** | Ball in the corner → load all five to that side `[D41]` | `[D41]` | All 5 defenders with s(d) > 0, or within 1 m of x = 0 |
| **Back pressure** | When the ball gets past, sprint to recover and get a back tip (Havoc) `[D55]` | `[D55]` | A defender who is trailing the handler (farther from the defended rim than the handler) and closing on him from behind at ≥ 5 m/s |

### F7.5 Closeouts

| Closeout type | Definition | Programs / source | Detection signature |
|---|---|---|---|
| **Sprint-stop** | Sprint to arm's length, a sudden one-two stop, a high hand within reach of the ball, inside hand to the face. Take away 2 of 3 options (shot first). Angle the feet per scheme: pack line takes away shot + baseline, no-middle takes away shot + middle `[D53]` | `[D53]` | Speed ≥ 4 m/s for ≥ 60% of the path, then deceleration to < 1 m/s within 0.4 s. End distance 0.6–1.0 m. End-position offset to the forced side |
| **Choppy / short-step** | High hands, short choppy final steps with the weight back. Never give up the baseline (pack line) `[D3]`. Bo Ryan: high hand, short quick steps `[D4]` | `[D3][D4]` | A gradual deceleration profile over the last 1.5 m |
| **Fly-by** | Sprint and leap past the shooter with hands up, beside him. Houston contests > 60% of threes this way `[D7]` | Houston `[D7]` | End speed ≥ 3 m/s, path passes within 1 m of the shooter and continues ≥ 1 m beyond. A vertical-jump flag if pose is available |
| **Smart closeout (fake)** | Fake to force a shot (FIBA "smart closeouts") `[D10]` | `[D10]` | Stop at 1.5–2.5 m, then lunge |
| **Zone "on and off"** | The zone forward closes out high then retreats once the guard arrives ("bump" back) `[D63][D64]` | 2-3 zone `[D63]` | See F8 |

---

## F8. ZONES

### F8.0 Universal man-vs-zone discriminator [HEURISTIC]
This is the most important single detector in the file. Compute it over a sliding **3.0 s window**, from `SET_DEF` until the shot, turnover or foul.

| Feature | Man | Zone | Matchup zone | Note |
|---|---|---|---|---|
| **Follow score** F_d = max_a corr(v_d, v_a) over the window, using the HMM-matched attacker | ≥ 0.6 for ≥ 4 defenders | ≤ 0.35 for ≥ 3 defenders | 0.35–0.6, with handoffs | Use velocity correlation of *off-ball* movement only (exclude frames when the defender is within 1.5 m of the ball) |
| **Ball-shift score** B_d = corr(v_d, ball-driven zone-slot displacement) | low | ≥ 0.6 | ≥ 0.5 | The zone-slot target comes from a ball-location-conditioned template (§F8 tables) |
| **Assignment entropy** H (HMM) | low, with switch events only at screens | high: assignments re-map whenever cutters cross region boundaries | moderate: re-maps happen at boundary crossings and are *followed by tight guarding* | `[D35][D36]` |
| **Region stability** σ_reg(d) | > 2.5 m | < 1.5 m | < 2.0 m | Measured relative to the template slot for the current ball zone (top / wing / corner / high post / short corner / low post) |
| **Cutter test** | The cutter's defender travels with him across the lane (≥ 70% of the cutter's path length) | The defender passes the cutter off. The defender's displacement is ≤ 40% of the cutter's | A pass-off happens, then the receiving defender guards tightly (≤ 1.2 m) | The strongest single test: any `CUT` of ≥ 6 m through the lane |
| **Offense-empty test** | A defender follows his man to the corner or the opposite side, even if that leaves no one in a zone area | Zone areas stay occupied even when empty of attackers (e.g. the weak-side low defender stays at the block with no attacker within 3 m) | — | — |

Decision rule: P(zone) = σ(w·[mean B − mean F, mean σ_reg, H, cutter-test]). A zone→man change is detected by a change-point (CUSUM or HMM regime) on this score (see F11).

```
F8 Zones
├── F8.1 Even-front zones: 2-3 (Syracuse/Boeheim; aggressive/trapping 2-3), 2-1-2 (FIBA)
├── F8.2 Odd-front zones: 1-2-2 / 3-2, 1-3-1 (base, trapping, Beilein/WVU-Michigan), 1-1-3 (Baylor), 3-2
├── F8.3 Match-up zones: Temple (Chaney), generic match-up (Kelbick), 1-2-2 match-up (Purdue), amoeba (Tarkanian), "Mayhem" (McCarthy)
├── F8.4 Zone tactics: on-and-off (bump), corner trap, short-corner trap, high-post swarm, PG "jump"
└── F8.5 Zone switches (into man): see F11
```

### F8.1 2-3 zone (and variants)

| Item | Content | Source |
|---|---|---|
| **Definition / roles** | Two guards at the top (around the elbows), two forwards low (wing to just below the basket), and a center who owns the paint and watches middle cutters and posts `[D33]`. Guards pinch to stop dribble penetration `[D64]` | `[D33][D64]` |
| **Base slides (ball at wing)** | The forward (X4) comes up to stop the shot. The top guard (X1) hustles to the wing and "pushes" X4 back down. X2 fronts or sinks on the high post. X5 slides to the low block. X4 then slides to the short corner `[D64]`. Aggressive version: X4 closes out high-handed and retreats when X1 arrives ("on and off"). X2 gaps between the high post and the point. X3 drops into the weak-side paint `[D63]` | `[D63][D64]` |
| **Ball in corner** | X4 guards the corner. X1 sinks 2 steps inside the arc within reach of the wing `[D64]`. The corner defender bumps up to the wing, then retreats to the corner `[D31]` | `[D31][D64]` |
| **High post** | Ball to the high post from the top: X5 steps up to guard it, X4 takes the block, the guards deny the pass back out `[D64]`. Aggressive: both guards drop and "swarm" the high post `[D63]` | `[D63][D64]` |
| **Short corner** | X4 and X5 trap immediately. X1 denies the wing. X3 denies the high post. X2 plays centre field `[D64]`. Syracuse version: X5 steps out with X3 doubling, X4 comes across to the block, X2 drops `[D20]` | `[D20][D64]` |
| **Skip wing→wing** | X3 takes the shot away until X2 arrives, then is nudged back down. X1 rotates across `[D64]` | `[D64]` |
| **Syracuse (Boeheim)** | Primary defense, not a change-up, built on length (the 2010-11 starters were 6-2 to 7-0) `[D31]`. Corner trap (X1 + X4, others deny). Short-corner trap after reversal. A "jump" trap on the PG as he crosses `[D31]`. Corner trap with X4 + X5, X1 takes away the wing, X3 the mid-post `[D20]`. The whole zone moves as one, with high hands. It "never shows the same look twice" `[D23]`. Game-state rules: stay in zone when down 8–10 and add press/traps. Go **man when down 15+**. Stay in zone even if a team hits early threes `[D20]`. Guards keep drivers out of the paint and *find shooters*. Common failures are late rotations on kick-outs and guards sinking too low `[D21]` | `[D20][D21][D23][D31]` |
| **Counters** | Gaps (top-wing seam), high post, short corner, skip passes, overloads, ball fakes (which force early slides) `[D31]` [CONVENTION] | `[D31]` |
| **MSU usage** | A situational 2-3 change-up (e.g. foul trouble) `[S74]`. Hoop Vision: Izzo is among the strict man coaches with low two-foul participation, unlike zone coaches `[D84]` | `[S74][D84]` |
| **Detection signature** | At `SET_DEF` with the ball at the top: 2 defenders at y ≈ 4.5–7.0 m, \|x\| ≈ 1.5–3.5 m. 2 at y ≈ 0–2.5 m, \|x\| ≈ 2.5–4.5 m. 1 at \|x\| < 1.2 m, y ≈ 0.5–3 m. Ball to the wing → the ball-side forward's y rises ≥ 2 m within 1 s, then falls back when the guard arrives ("on-and-off" signature: forward y rise-and-return within 2.5 s). Corner-trap signature: `TRAP` at (\|x\| > 6, y < 2) between a guard-slot and a forward-slot defender. Man/zone features from F8.0 |

### F8.2 Odd-front zones

| Zone | Definition / slides | Programs (sourced) | Counters | Detection signature |
|---|---|---|---|---|
| **1-3-1 (base)** | Point X1 moves laterally. Wings X2/X3 move up and down. Middle X5 denies, usually fronting. Baseline X4 stays at or below the block and moves laterally. Ball to the corner: X4 closes out, X2 drops or traps, X1 drops to the ball-side elbow. Reversal: X4 sprints across `[D61]` | Beilein's West Virginia teams used it consistently after made FGs. Used sparingly at Michigan `[D32]`. Baylor 2025: a 1-3-1 with Edgecombe roaming the middle, used with Omier on the floor `[D78]`. Auburn: occasional 1-3-1 `[D79b]` | Short corners, diagonal and skip passes, shooters in the corners, rebounding gaps `[D62]` | 1 defender at y ≈ 6–8 m (point). 3 across at y ≈ 3.5–5 m (two wings at \|x\| ≈ 4–6, middle at \|x\| < 1.2). 1 baseline defender at y < 1.5 m whose x tracks the ball's x sign (corner-to-corner runs ≥ 8 m) |
| **1-3-1 trapping** | Roles: **Chaser** (top), **Center**, **Warrior** (baseline, corner to corner), and two wings "connected by a string". Traps in the half-court corners (wing + chaser), baseline corners (warrior + wing), and high post (chaser + center double). Also runs full-court from the opponent's FT line with a trap after the timeline `[D62]`. "Tight 1-3-1" = no traps and tighter spacing `[D62]` | `[D62]` | Diagonal passes out of a trap `[D62]` | `TRAP` frequency ≥ 1 per possession, located at the (\|x\| > 5, 8 < y < 12.7) half-court corners or the (\|x\| > 6, y < 2) baseline corners |
| **1-1-3 (Baylor)** | Guard 1 picks up the ball as far out as needed. Guard 2 plays the high post and anticipates the first pass. Forwards on the wings deny direct corner passes. Center 5 takes the blocks. The guards trade ball and high-post duty (after the first pass, G2 goes to the ball and G1 to the high post). The weak-side forward sits deeper than the lowest offensive player. A short-corner catch draws a strong-side forward + C double. Uses man principles and can trap anywhere within ~30 ft. Baylor can switch to true man `[D75]` | Baylor (Scott Drew) `[D75]` | Drive-and-kick rather than skips. Two-guard front. Handling bigs in the short corner. Overloads `[D75]` | 2 defenders stacked near x≈0 (one at y ≈ 7–9 m on the ball, one at y ≈ 4–5 m at the high post). 3 low at y < 3 m spanning the lane. Ball-to-wing → the high-post guard becomes the ball defender (role swap between X1/X2 within 1 s of the first pass) |
| **1-2-2 / 3-2** | One top, two at the elbows/wings, two low [CONVENTION]. FIBA lists 1-2-2 (as a press) and 3-2 `[D10]` | Purdue: occasional 1-2-2 match-up `[S75]`. Boston College 1-2-2 → man on a high-post catch `[D80]` | Short corner, high post | 1 at y ≈ 7–8, 2 at y ≈ 4.5–6 (\|x\| 3–5), 2 at y < 2.5 (\|x\| 2–4). The top defender pressures the ball, and the high pair takes the wings |
| **2-1-2** | Listed by FIBA `[D10]`. The middle defender owns the high post [CONVENTION] | — | Wings and corners | The 2-3 shape with the middle defender at y ≈ 3.5–4.5 instead of < 3 |

### F8.3 Match-up zones

| Zone | Definition | Programs | Counters | Detection signature |
|---|---|---|---|---|
| **Match-up zone (generic)** | Zone defenders match up with the attackers in their area (FIBA) `[D10]`. Blends man ("the ball is always accounted for") and zone (positional control). It is hard to scout because the offense can't tell which offense to run. Teaching starts from man principles: shell, 4v3, 5v4 `[D71]` | Kelbick system `[D71]` | Screening the zone. A point guard in the middle ("once a PG gets into the middle of the zone, it's over") `[D76]` | Man-like pressure on the ball and one-pass-away men (dist ≤ 1.2 m). Assignment re-maps when cutters cross region boundaries (H moderate). F in the 0.35–0.6 band. Defenders don't follow cutters across the lane (cutter test = pass-off) yet guard tightly in their area |
| **Temple match-up (John Chaney)** | Defenders play tight man on the players in their area. The goal is to limit transition, control tempo, pressure the ball, deny the interior and dare threes. Often paired with a slow-paced offense `[D76]` | Temple (Chaney) `[D76]` | Spread the floor, hit open shots. PG penetration into the middle `[D76]` | As generic. Plus opponent possession length ↑ |
| **Amoeba (Tarkanian)** | Vs a one-guard front, a "diamond-and-1" look: X1 pressures from half-court, X2 denies the high post, X3/X4 on the lane lines below the elbows, X5 is the hoop defender. Wing pass: X2 closes out, X5 fronts the ball-side post, X4 drops to the hoop. Corner pass: X5 closes out, X3 fronts the post. Skip: X4 closes out, X3 slides across, X5 drops. Vs a two-guard front it looks like a 2-3. Wing dribble → X3 sprints out to trap with X2 `[D60]` | UNLV (Jerry Tarkanian, creator). Tarkanian saw it as a change-up. McCarthy's "Mayhem" extension `[D60]` | Shape-shifting by the offense's front | Alignment depends on the offense's front (1-guard → 1-3-1/diamond, 2-guard → 2-3). Role permutation per ball zone. X5 alternates between "hoop" and "corner closeout" (unusual for a C, since in a 2-3 the forward takes the corner) |
| **1-2-2 match-up** | See F8.2 | Purdue `[S75]` | — | — |

---

## F9. PRESSES & FULL-COURT PRESSURE

### F9.0 Press detection primitives [HEURISTIC]
- **Press active**: ≥ 3 defenders with y > 12.7 m (in the offense's backcourt) while the ball is in the backcourt, *and* the ball-handler's nearest defender is ≤ 2.0 m.
- **Depth class** (by where the first defender engages, or the trap location): full (y ≥ 21 m, i.e. at or beyond the opponent's FT line), 3/4 (16–21 m), half-court (trap within ±3 m of the half line, 9.7–15.7 m), half-court trap zone (8 < y < 12.7).
- **Zone press vs man press**: compute F (follow score) and B (ball-shift score) in the backcourt. Zone presses show "landmark" positions (e.g. the 2-2-1 guards at the FT-line ends) *before* the inbound, and slots that move with the ball after it.
- **Inbound pressure**: a defender within 1.5 m of the inbounder (`Disruptor`/"Jammer") vs. none (the inbound is free, as in a 2-2-1 or 41 Deny safety).
- **Trap count & location**: `TRAP` events clustered by court zone: corner (x > 5.5, y > 24), sideline-pre-half (\|x\| > 5, 12.7 < y < 16), sideline-post-half, middle.
- **Fall-back event**: the frame where ≥ 4 defenders have y < 9 m. This marks the transition to the half-court scheme. **Record what scheme follows** (e.g. press → 2-3 zone, as Syracuse's zone-press combos).

```
F9 Presses
├── F9.1 Full-court man: 41 Deny (inbound safety), deny-all, face-guard, double-fist (VCU man trap)
├── F9.2 Zone presses: 1-2-1-1 diamond (fist / flat), 2-2-1 (full / 3/4), 1-2-2 ("80", "70", "76", "Red 76"), 2-1-2, 1-3-1 full/3/4
├── F9.3 Match-up press ("80" Coach's Clipboard), run-and-jump press
├── F9.4 Half-court traps: 2-2-1 half-court trap, 1-3-1 half-court trap, 1-2-2 "76" corner trap
└── F9.5 Program systems: Havoc (VCU/Smart), 40 Minutes of Hell (Arkansas/Richardson), Pearl press (Tennessee/Auburn), MSU 2023-24 full-court pressure
```

### F9.1–F9.4 Named presses

| Press | Alignment & roles | Traps & rotations | Fall-back | Programs | Counters | Detection signature |
|---|---|---|---|---|---|---|
| **Full-court man / "41 Deny"** | The inbounder's defender drops to at least half-court as the safety. The other four deny the passing lanes. The inbounder's defender shades to force the pass to the corner `[D93]` | Traps are opportunistic: sideline, corner (yellow), and the "red" area near the 10-second line `[D93]` | Everyone but the ball defender sprints to the paint when the ball gets past `[D93]` | Generic. MSU 2023-24 pressed baseline to baseline more than in recent years [structure UNVERIFIED] `[D5]` | Long pass over the safety. Screens for the receiver | No defender within 3 m of the inbounder. One defender at y ≈ 12–14 m in the middle. Four defenders within 1.5 m of their men and on the lanes (deny index ≥ 0.7) |
| **Double-fist (VCU man trap)** | Man-to-man full-court trap. VCU's most used press (~2/3 of the time) `[D94]` | Trap near the sideline, past half-court, with the ball "heated up" and from a surprise angle `[D94]` | — | VCU (Shaka Smart) `[D94]` | — | Man press (high F) plus `TRAP` events concentrated at sideline zones near the half line |
| **1-2-1-1 diamond** | Disruptor (a tall player) on the inbounder. Two wings behind the nearest attackers. Interceptor halfway between the arc and half-court. Safety even with the deepest attacker `[D3b]`. Pearl version: the inbound defender stays on his feet, doesn't jump, and counts aloud. P1 is the sideline-to-sideline interceptor. P5 is man-to-man deep `[D44]` | Fist = trap the first receiver immediately. Flat = deny the return, trap on the dribble. Pass over the top → interceptor + nearest wing trap `[D3b]`. VCU's "diamond" is a 1-2-1-1 `[D94]` | Until the ball enters the middle or crosses half-court `[D3b]` | Pearl (Tennessee 2010) `[D44]`. VCU Havoc `[D94]`. Generic `[S76]` | Pass to the middle. Inbounder steps in. Long pass vs a cheating safety | Pre-inbound: 1 defender ≤ 1.5 m from the inbounder, 2 at y ≈ 21–25 m with \|x\| ≈ 3–6, 1 at y ≈ 15–18 near the middle, 1 at y ≤ 12 (deep). First `TRAP` within 2 s of the inbound, at the corner/sideline beyond the opponent's FT line |
| **2-2-1 (full / 3/4)** | Guards at the FT-line ends, mid-court defenders just inside half-court, X5 deep "prevent". The inbound is uncontested and the middle denied `[D65]` | Guards trap near the sideline after the first dribble. Up the sideline: the mid-court defender stops it and traps with the guard. Kampe variant: X1+X2 trap on a sideline dribble, X3 cuts off the sideline pass `[D65]` | Off-ball defenders sprint back once it's broken. The ball defender stays on the ball `[D65]` | Kampe (Oakland) named `[D65]` | Middle flash, skip to the weak side | Pre-inbound: no defender on the inbounder. 2 at y ≈ 20–22 m (\|x\| ≈ 2), 2 at y ≈ 13–15 m, 1 at y ≈ 6–10 m. Then trap events at \|x\| > 5, 14 < y < 20 |
| **1-2-2 "80" (3/4 aggressive)** | X1 pressures and stops middle penetration. X2/X3 sideline + middle. X4 slides up to the ball-side half line. X5 is the deep middle safety. Usually one deep trap, sometimes a second near half `[D67]` | Reversal rotations: X1 slides, X3 waits for X2, then X1 sprints to trap on the second reversal while X5 rotates up `[D67]` | — | Generic `[D67]` | Long diagonal | Defender slot pattern 1-2-2 starting ≈ the top of the arc / FT line extended in the backcourt |
| **1-2-2 "70" (containment)** | X1 just inside the top of the key, no trapping, float and keep the ball in front, avoid long passes `[D67]` | None | — | `[D67]` | — | 1-2-2 slots, F low, **no** `TRAP` events. Ball-handler cushion ≥ 2 m |
| **1-2-2 "76" / "Red 76"** | Starts as 70, steers to a sideline, and traps the corner once the ball crosses half. In Red 76, X5 leaves the safety spot to deny the middle `[D67]` | Trap at the frontcourt corner. The opposite wing denies the middle `[D67]` | — | `[D67]` | Diagonal pass (Red 76 has no safety) | Contain phase → `TRAP` at the frontcourt corner (y ≈ 7–12, \|x\| > 5) right after the ball crosses half |
| **2-2-1 half-court trap** | X1/X2 at the half line, X3/X4 near the arc, X5 near the FT line to cut off the centre `[D66]` | Sideline: X4 steps up and traps with X1. Cross-court: X2 + X3 trap. Corner: X5 covers, X4 to the ball-side block `[D66]` | Corner → switch to man or zone `[D66]` | Generic `[D66]` | Middle pass | 2 defenders at y ≈ 11–13 m. Traps at 7 < y < 12, \|x\| > 4 |
| **1-3-1 full/3/4** | Starts at the opponent's FT line shaded to a sideline. Trap right after the timeline. Wing stops the dribble, chaser doubles, warrior takes the corner pass, center denies the high post `[D62]` | `[D62]` | Becomes the half-court 1-3-1 | Generic `[D62]` | — | 1-3-1 slot pattern centred at y ≈ 16–22 m |
| **Match-up press ("80")** | Everyone matches man once the ball is inbounded. "Play someone" sets the 1-Up/2-Up/3-Up/4-Up alignment by the offense. X4 on the inbounder (tip the pass) and X3 the quick back defender `[D92b]` | Main trap on the sideline near half-court (cut-and-double / run-and-jump). Corner trap below the block. Middle: only run-and-jump, where the momentum defender "jumps" `[D92b]` | Sprint to the paint when beaten. Back-tip `[D92b]` | Generic `[D92b]` | Middle pass after the jump | Man-like F in the backcourt, with alignment matching the offense count. `TRAP` at the sideline near half-court. `run-and-jump` events in the middle |
| **Run-and-jump press** | Middle dribble → jump switch. Sideline → trap. Often a one-and-done trap, then sprint back to protect the paint `[D50]` | `[D50]` | `[D50]` | Dean Smith/UNC origin `[D50]` | Pass ahead | See F1.2 run-and-jump event, located in the backcourt |

### F9.5 Program pressure systems

| System | What is documented | Source | Detection notes |
|---|---|---|---|
| **Havoc (VCU, Shaka Smart)** | Two base presses: double-fist (man trap, ~2/3 of the time) and the diamond 1-2-1-1, plus 11 variations and hybrids. Occasional "Jammer" on the inbound to the PG. Steals on 17.7% of possessions and TOs on 29.3% (both #1). Origin: a Pitino 1989 tape via his HS coach, Clemson under Purnell (diamond + double-fist), named in May 2009 `[D94]`. Every trap has 2 trappers, 2 interceptors and 1 goaltender (the defender farthest from the ball). Side diamond on sideline inbounds. No traps in the middle. "Madman" = the on-ball defender. "Fixing it" = re-matching after the press is broken `[D54]`. Never trap in the middle. Use the sideline and half line as extra defenders. Off-ball players "think like a trapper". Stunt at the ball. Back pressure `[D55]` | `[D54][D55][D94]` | Each `TRAP` should co-occur with exactly 2 defenders on the nearest passing lanes (interceptors: perpendicular distance ≤ 1 m to segment(ball, a) for the 2 nearest attackers) and 1 defender at max distance from the ball near the rim (goaltender). "Fixing it" = the HMM re-matches after a press break: a burst of `ROTATE` events in the 2 s after the ball crosses half |
| **"40 Minutes of Hell" (Arkansas, Nolan Richardson)** | The name came from practice conditioning and became the style `[D52]`. A two-platoon, perpetual-pressure system at both ends (1990) `[D95]`. Full-court trapping pressure kept on even when trailing (1994 vs Kentucky). Richardson: keep the pressure on and "something's gonna break" `[D51]`. **Specific press alignments were not found in opened sources [UNVERIFIED]** | `[D51][D52][D95]` | Detection is the *volume* of pressure: press active on ≥ 70% of opponent possessions incl. after misses, plus heavy substitution (needs lineup data) |
| **Pearl press (Tennessee 2010; Auburn)** | Tennessee 2010: a 1-2-1-1 the length of the court, pressuring the inbound and the 10-second count `[D44]`. Auburn 2022-23: presses after made baskets. Half-court is mostly drop coverage with 1-4 switching and occasional junk zone. Top-5 block rate (Broome, Cardwell) `[D79a]`. Auburn 2023-24 scouting: presses after made FTs and FGs, more aggressive after made FTs, backs off after a couple of passes following a made FG. Mostly man with an occasional 1-3-1. Tends to over-help (lobs and kick-outs available) `[D79b]` | `[D44][D79a][D79b]` | Press trigger is conditioned on the *previous event* (made FT > made FG > miss). See F11.3 |
| **MSU 2023-24** | Baseline-to-baseline ball pressure in exhibitions. 20 forced TOs vs Tennessee. The prior season ranked 332nd in steals and 341st in forced TOs `[D5]` | `[D5]` | Track press rate by MSU season. Prior: low |

---

## F10. JUNK / COMBINATION DEFENSES

| Defense | Structure & rules | Trigger / when | Programs | Counters | Detection signature [HEURISTIC] |
|---|---|---|---|---|---|
| **Box-and-1** | Box: two high at the FT line extended, two low with a foot in the lane, fronting strong-side posts. The weak-side high defender always denies the high post. Wing: the strong high closes out, the weak high slides to the middle, the strong low fronts, the weak low goes to the split line. Corner: the strong low closes out (no baseline). High-post catch → both high defenders trap. The box doesn't switch screens and never extends past the arc. **Chaser** denies the star from between him and the ball, choosing lock-and-trail or shoot-the-gap by screen angle. Box defenders call and bump the star `[D68]` | The star got hot. After a timeout. End of a quarter `[D68]` | 2019 Raptors vs Curry (pro) `[D68]` | Screens on the chaser, the star as a screener, several shooters, high-post scoring `[D68]` | One defender with F ≥ 0.8 against one attacker (the chaser), on the star's ball side (deny index ≥ 0.6), regardless of court region. Four defenders with σ_reg < 1.5 m in box slots: (±2.5–3.5, 4–5.5) and (±1.5–2.5, 0–1.5) |
| **Diamond-and-1** | Four in a diamond (top, two wings, one low) plus a chaser `[D10]` | — | Amoeba resembles it vs a one-guard front `[D60]` | Corners | As box-and-1 with slots (0, 6–7), (±3.5, 3–4), (0, 0.5–1.5) |
| **Triangle-and-2** | Two chasers in full denial with no help duties. The top triangle defender (quick) owns the high post and the ball above the FT line. Two bottom defenders (big) front posts and guard the ball below the FT line. When a star catches, the triangle collapses to its spots. Closeout angles push the drive to the middle `[D70]` | The offense depends on two players. A backup when the main D fails `[D70]` | Coach K's Duke vs UNC in the late '90s (cited) `[D68]` | Several shooters, post scorers `[D70]` | Two defenders with F ≥ 0.8 against two different attackers. Three defenders in a triangle: (0, 4–5.5) and (±2, 0–1.5) |
| **Chaser rules (generic)** | Deny, face-guard, top-lock or trail by screen angle `[D68][D73]` | — | — | — | The chaser's deny index ≥ 0.6 even two passes away (unlike man, where two-away defenders sag) |
| **Zone + face-guard ("junk 2-3")** | Auburn "occasional junk zone" `[D79a]` | — | — | — | Mixed: a zone with one high-F defender |

---

## F11. HYBRID & CHANGING DEFENSES

Two time scales need labels:
- **Intra-possession switch** (scheme A → scheme B within one possession). Label it with `scheme_before`, `scheme_after`, `trigger_event`, `t_trigger`, and `t_switch_complete`.
- **Inter-possession change** (the defense differs by possession context). Label it as a context-conditioned policy.

```
F11 Hybrid & changing
├── F11.1 Zone→man on trigger: high-post catch, Nth pass, ball screen, shot clock, "Match" call
├── F11.2 Man→zone on trigger: post catch, Nth DHO, press break ("fixing it" → zone), mismatch after full-court switches
├── F11.3 Press→half-court mapping: zone press → zone / man; man press → man; "fall back" timing
├── F11.4 Between-possession policies: after made FG vs miss vs made FT; after timeout; by score margin; by foul trouble; by lineup (big on floor)
├── F11.5 Coverage switching within man: switch late clock, switch on wing PnR only, hedge→switch by personnel
└── F11.6 Disguise families: zone "showing man" pre-set, man "showing zone" (sink-all), 1-1-3 role-swaps
```

### F11.1–F11.2 Intra-possession switches

| Hybrid | Trigger | Programs (sourced) | Offensive counters | Detection signature [HEURISTIC] |
|---|---|---|---|---|
| **1-2-2 zone → man on a high-post catch** | Ball caught at the high post. Defenders match the nearest man and stay man for the rest of the possession `[D80][D98]` | Boston College (Jim Christian) vs Rhode Island. Brisbane `[D80][D98]` | Recognize and attack the mismatch. Run man sets after the switch | Zone score high before; a `PASS` to an attacker in the high-post region (\|x\| < 2.5, 3.5 < y < 6.5); within ≤ 1.5 s, F rises above 0.6 for ≥ 4 defenders and σ_reg grows. Mark t_trigger = catch time |
| **Zone → man on the 2nd perimeter pass** | Zone keeps the ball out of the high post, then goes man on the second perimeter pass `[D80][D98]` | Reyer Venezia (De Raffaele) `[D80]` | Burn-clock awareness. Early high-post flash | Pass counter since `SET_DEF`. Change-point aligned within ±1 s of the 2nd perimeter pass (both passer and receiver at r > 6 m) |
| **Match-up "Match" call on a high-post entry** | On the ball to the high post, the call is "Match" and every defender touches his matchup `[D99]` | College of Idaho (Colby Blaine) `[D99]` | — | As above, but the scheme stays labeled "match-up zone". The assignment entropy H drops sharply at the high-post catch |
| **Man → 2-3 on a post catch** | Defense drops into a 2-3 when the post catches `[D80]` | Žalgiris (Jasikevičius) `[D80]` | Kick-out three vs the shifting zone | F falls below 0.35 within 1.5 s after the post catch. The 2-3 template residual falls below 1.5 m |
| **Man → 2-3 on the 2nd DHO** | Specific to an opponent set `[D80]` | Real Madrid (Laso) `[D80]` | — | DHO counter. Change-point after the 2nd `DHO` |
| **Zone with ball-screen rules ("Sprint Under", "Switch and Drop")** | 1-1-3: a middle-going screen → the defender sprints under and a top guard drops to the high post. A reverse-angle screen toward the short side → the guards swap ball defenders and the other drops to the FT line. 2-3: the big helps only on reverse-angle top screens `[D98]` | Georgia Tech, Anwil (1-1-3). Oregon State, Utah Jazz (2-3) `[D98]` | Screen the zone. Overloads | Within the zone label, attach a sub-label to `SCREEN` events: guard-swap (two guard-slot defenders exchange ball duty within 0.8 s) vs under. Stays zone (F stays low) |
| **Zone → man after a ball screen [CONVENTION; the project's prompt example]** | The first ball screen (zone defenders can't "under" it) prompts a matchup | No opened D-I source names a program **[UNVERIFIED]** | — | Change-point within 2 s after `SCREEN` with the ball. Post-screen ball-screen coverage labels (F3) become meaningful only after the switch |
| **Shot-clock trigger** | Zone early, man late (or vice versa). Switch everything in the last 5–10 s `[D19]` | Situational switching `[D19]` | Late-clock iso | Change-point aligned with the shot clock crossing 10 s ± 2 s, consistent across possessions |
| **Full-court switches → half-court zone** | After full-court man switches create mismatches, switch back in the half-court, *or* drop into a half-court zone `[D93]` | Generic `[D93]` | Early offense before the zone sets | Press (man) then, at fall-back, the zone score rises |
| **Zone press → man** | Zone press falls back into man `[D99]`. 2-2-1 half-court trap → man or zone after the corner `[D66]` | College of Idaho `[D99]` | — | Fall-back event, then the half-court classifier |
| **Syracuse score-state rule** | Stay in zone down 8–10 (add press/traps). Go man down 15+ `[D20]` | Syracuse (Boeheim) `[D20]` | — | Possession-level P(man) conditioned on the margin |

### F11.4 Between-possession policies (context-conditioned)

| Policy | Example (sourced) | How to detect |
|---|---|---|
| **After made FG** | Beilein's WVU teams used the 1-3-1 consistently after made FGs `[D32]`. Auburn presses after makes `[D79a]` | P(scheme \| previous possession outcome) with a χ² test vs the base rate. Previous outcome comes from PBP |
| **After made FT** | Auburn: more aggressive press after a made FT. Backs off after a couple of passes following a made FG `[D79b]` | As above. The press "back-off" time = time from the inbound to the fall-back event |
| **After timeout (ATO)** | Situational switching after timeouts `[D19]`. Box-and-1 after timeouts `[D68]`. Off-ball "Next" used once to disrupt an ATO `[D29]` | Flag possessions starting within 30 s of game time after a timeout. Compare the switch rate and junk rate |
| **Foul-trouble policies** | Zone-heavy teams (>80% zone) play 2-foul starters 51% of the remaining first-half minutes vs the NCAA average of 23%. Strict man coaches (Bennett, Moser, **Izzo**) near the bottom. Passive coverage instead of hard hedges protects a foul-troubled big `[D84]`. MSU: 2-3 as a foul-trouble change-up `[S74]` | Join to foul counts. Coverage aggression index A drops for the screener-defender with ≥ 2 fouls |
| **Lineup-driven** | Baylor 2025: 1-3-1 zone with Omier on the floor, man when he sits `[D78]` | P(scheme \| on-court 5) |
| **Score/time** | Syracuse margin rule `[D20]`. End of game "ring the arc" (F14) | — |

### F11.6 Detecting a scheme change: the generic algorithm [HEURISTIC]
1. Per frame, compute the zone-vs-man score Z_t (F8.0) and the template residuals for each zone family (2-3, 1-3-1, 1-1-3, 1-2-2, box-and-1, triangle-and-2) under the current ball-location bin.
2. Run a **4-state HMM** (man, zone-family-k, match-up, transition/unsettled) with sticky transitions (stay ≈ 0.995 per 10 Hz frame, i.e. a mean dwell ≈ 20 s). Emissions: Z_t, H_t, the residuals, and the cutter-test indicator.
3. Allow transitions only at **candidate triggers** (high-post catch, post catch, Nth pass, `SCREEN`, `DHO`, shot clock ≤ 10 s, ball crossing half) by boosting the transition prob ×20 within ±1.0 s of the trigger. This adds the coaching prior that switches are trigger-driven `[D80][D98]`.
4. Report `t_switch_complete` = the first frame after which the new state's posterior > 0.8 for ≥ 1.5 s, and `lag` = t_switch_complete − t_trigger. Expected lags are 0.5–1.5 s for the "match the nearest man" triggers [HEURISTIC].
5. **Disguise guard:** require that the new state persist ≥ 2.0 s *and* survive one cutter test (if any cut occurs), to avoid labeling a late zone slide as man.

---

## F12. TRANSITION DEFENSE

```
F12 Transition
├── F12.1 Get-back rules: 1 back (PG/safety), 2 back (full back + half back), shooter-back (Underwood), guards-back (pack line)
├── F12.2 Stop the ball: second man back picks up the ball (even past half)
├── F12.3 Protect the basket: first back to the rim, "as low as the lowest attacker"
├── F12.4 Matchup on the fly / cross-match: pick up the closest man, switch back when the ball is stopped
├── F12.5 Jam the rebounder / tag after an offensive rebound attempt
└── F12.6 Outnumbered: 2-on-1, 3-on-2 (top "ball, ball, ball"), "cover two"
```

| Rule | Definition | Programs / source | Detection signature [HEURISTIC] |
|---|---|---|---|
| **One back (safety)** | One designated guard stays back beyond the arc as the safety. If he attacks the rim, a second guard takes over `[D85]`. Izzo: send 4 to the offensive glass, the PG gets back `[D4]` | **MSU** `[D4]` | At shot release + 1.0 s, count the shooting team's players moving away from the attacked rim at ≥ 2 m/s with r > 7 m (retreaters). MSU's expected count on its own shots is 1 (the PG) |
| **Two back (Full Back / Half Back)** | Full Back protects the paint, Half Back pressures the ball and keeps it on one side. The trail big fills the gap. No assignments until the ball is stopped `[D86]`. Pack line: 2 guards back on each shot, 3 crash `[D3]`. Dick Bennett lineage: the 1 and 2 "back every time" `[D2]` | Chris Holtmann `[D86]`. Pack line `[D2][D3]` | Two players retreating at shot + 1 s. The deeper one reaches r < 3 m of his own rim before the outlet crosses half |
| **Shooter back first** | On a three-point attempt, the shooter gets back first and the other four pursue the rebound (Underwood) `[D85]` | Brad Underwood (Illinois) `[D85]` | The first retreating player = the shooter on 3PA |
| **Stop the ball** | The second player back picks up the ball wherever it is, even past half `[D85]`. Half Back pressures and keeps it on one side `[D86]` | `[D85][D86]` | Time from the defensive rebound/outlet to the first defender within 2 m of the ball-handler. Location of the pickup (y). Stop = handler speed drops below 3 m/s |
| **Protect the basket** | The first back sprints to the rim and takes one step out. Force at least one pass. In 2-on-1 / 3-on-2, "get as low as the lowest offensive player" `[D85]` | `[D85]` | The deepest defender's r ≤ 2.5 m when the ball crosses half |
| **Matchup on the fly** | Sprint back "with vision", find shooters. Youth teams sprint to the paint then match `[D85]`. Transition pick-up: closest man, accept mismatches, switch back in the half-court `[D93]` | `[D85][D93]` | **Cross-match**: HMM matchups in transition differ from the half-court "home" assignment (the modal assignment of the previous settled possessions). Count the cross-matches at `SET_DEF`. **Scramble switch** back = a `SWITCH` without a screen within 6 s after `SET_DEF` |
| **Jam / tag the rebounder** | The nearest rebounder jams the defensive rebounder to slow the outlet, while the others sprint back `[D85]`. Each offensive player tags his matchup with a bump from behind, then releases `[D88b]`. Transition roles after a rebound: ball stopper, middle stopper, sideline denier, weak-side denier, safety `[D88b]` | `[D85][D88b]` | A defender within 1.5 m of the rebounder for ≥ 0.5 s after the rebound. Outlet delay ↑ |
| **Get-back vs crash trade-off** | NBA tracking study: after a missed shot, players crash, get back, or hold. Teams that tend to get back early cut their own offensive-rebound probability by more than half, and getting back early helps defensive success `[D100]` | MIT SSAC (Wiens et al.) `[D100]` | Crash = within 5 ft (1.5 m) of the basket at the rebound, or moved ≥ 5 ft toward it and ended 5–20 ft away (AutoStats definition) `[D101]` |
| **Cover two** | In transition, cover the ball and the man sprinting to the rim, with an agreed split `[D102]` | `[D102]` | One defender's position between two attackers (ball + rim runner), equidistant within ±1 m |

> **Note on [D100]:** only the abstract was opened. Its distance and timing definitions are not known here, so the crash definition above comes from the AutoStats college definitions `[D101]`.

---

## F13. DEFENSIVE REBOUNDING

```
F13 Defensive rebounding
├── F13.1 Box-out (block-out): contact first, then pursue
├── F13.2 Hit-Find-Fetch (Izzo/MSU): hit → find ball → fetch with two hands, above the head
├── F13.3 Gang / team rebounding: 5 to the glass vs leak-outs; "run opposite"
├── F13.4 Role-specific: low man wins the initial contact (Izzo); get behind the post on a shot (Izzo); guards take long rebounds (wing-elbow)
└── F13.5 Anti-crash: tag/jam (offense) → defense "tag up" (Breakthrough glossary)
```

| Technique | Definition | Programs / source | Detection signature [HEURISTIC] |
|---|---|---|---|
| **Box-out** | Make contact to establish position between the opponent and the ball (FIBA) `[D10]`. Box out on every shot (pack line) `[D3]`. "Hit first" to unbalance, then go get it `[D102]` | `[D3][D10][D102]` | Between shot release and the rim hit: the defender is within 1.0 m of his matchup, positioned on segment(attacker, rim) (perpendicular distance ≤ 0.5 m), for ≥ 0.4 s. The attacker's speed toward the rim drops ≥ 40% during the contact |
| **Hit-Find-Fetch (MSU)** | Step into the man you're boxing out and make contact to push him off the rim. Find the ball. Rebound it in the air with two hands, above the head is a good one. The low man wins the initial contact. On a shot, get behind the post player `[D4]`. Hit = contact to disrupt, find = locate the ball in the air, fetch = go get it `[D103]`. A Grantland piece says Izzo prefers it to the classic box-out `[S1]`. Practised in the "War" drill (5v5, +2 for an offensive rebound, all loose balls live) `[D91]` and a 5-under-the-rim block-out drill (first to 10) `[D90]` | **MSU (Izzo)** `[D4][D90][D91][D103][S1]` | Box-out contact phase short (0.3–0.8 s), followed by the defender **leaving the contact and moving toward the predicted rebound location** (velocity toward the ball's predicted landing point ≥ 2 m/s before the ball falls below rim height). Classic box-out: contact maintained until the ball is close to the floor |
| **Gang rebounding** | All five pursue the ball. No leak-outs [CONVENTION] | — | 5 defenders inside r < 5 m within 1.0 s after the rim hit |
| **Run opposite** | About 70% of rebounds land on the opposite side of the rim, so after the box-out move there `[D102]` | `[D102]` | The weak-side defender's position at the rim hit is on the opposite side to the shot's x sign |
| **Long-rebound coverage** | Wings and guards take the wing-elbow areas for long rebounds `[D88b]` | `[D88b]` | Guard defenders at r ≈ 4–6 m at the rim hit |
| **Rebound-chance accounting** | A chance = a player within 3.5 ft (1.07 m) of the rebound. Contested = an opponent also within 3.5 ft. Deferrals adjusted `[D101]` | AutoStats (Genius) `[D101]` | Use these definitions directly for DREB-chance metrics |

---

## F14. SPECIAL-SITUATION DEFENSE

| Situation | Defensive options / rules | Source | Detection signature [HEURISTIC] |
|---|---|---|---|
| **BLOB (baseline out of bounds)** | The ball defender denies the direct pass to the rim, stepping back at an angle. He protects the basket first, then switches out. Switch all screens that come from the baseline up and on screen-the-screener. Keep posts in the post. Corner pin: the off-ball defender takes the corner and the ball defender switches out. Middle protected by both bigs. Zone options: 2-3 with a forward covering the corner. Lob protection: face-guard the big with a defender behind, or "sandwich" the block `[D79]`. Syracuse: forwards can't let the ball go to the corner `[D20]`. Inside post screens on BLOBs: step under and switch `[D19]` | `[D19][D20][D79]` | Inbound from the baseline (y_ball ≈ −1.6 m, out of bounds). The inbounder's defender is at r ≤ 2 m, between the inbounder and the rim. Classify the scheme (man/switch/zone) with F8.0 over the 5 s inbound window. Switch rate per screen ≈ 1 in switch-all BLOB D |
| **SLOB (sideline out of bounds)** | Match-up defense vs sideline plays to avoid back-door lobs. 1-3-1 match-up vs SLOB `[D79]`. Late game: the tallest player guards the long pass and the inbounder. Quickest on the sidelines and wings. Keep the ball in play, and bat it into the backcourt `[D104]` | `[D79][D104]` | Inbound at \|x\| ≈ 7.6+. The inbounder's defender within 1.5 m or dropped as a safety. Deny index of all four others |
| **ATO (after timeout)** | Situational switch-everything after timeouts `[D19]`. Junk (box-and-1) after timeouts `[D68]`. Off-ball "Next" to disrupt one ATO `[D29]` | `[D19][D29][D68]` | Possession context flag. Compare the scheme vs the team's baseline |
| **End of game, up 3** | Option A (defend): ring the arc, switch every screen, concede twos, never foul a shooter `[D104][D105]`. Option B (foul): foul with 1–2 s left once the ball is in the half-court. Risky with > 3 s because of the miss-rebound-three sequence `[D104]`. KenPom (since 2009-10, trailing team with 5–12 s left): defend ≈ 93.5% wins vs foul ≈ 92.0%. Differences within noise. Default "don't foul". Fouling may be better vs several strong shooters if you rebound FTs well. Offensive rebounds on missed FTs ran 40.6% in these spots `[D81]` | `[D81][D104][D105]` | Context: margin = +3, clock ≤ 12 s. **Ring-the-arc signature**: ≥ 4 defenders at r ≥ 6.2 m, each within 1.5 m of a perimeter attacker. A `SWITCH` on every screen. Foul-up-3 = a defensive foul on the ball-handler before a shot (PBP) at clock ≤ 6 s with the handler at r > 6.75 m |
| **End of game, up 1–2** | Man or zone. X4/X5 guard against the long pass to the paint, X2 the sideline pass and corner three, X1 the arc and skips. Watch the inbounder step-in `[D104]` | `[D104]` | — |
| **Last-shot / late-clock** | Switch all perimeter screens to keep ball pressure `[D104]`. Situational switch in the last 5–10 s `[D19]`. A star driving with < 6 team fouls can be fouled before the shot to force a reset `[D104]` | `[D19][D104]` | Shot clock ≤ 10 s: switch-rate jump. The deny index on the opponent's star ↑ |
| **Free-throw alignment** | NFHS: up to 4 defenders and 2 offensive players in the marked spaces. Defense occupies the first spaces (nearest the neutral zone) and may take the spaces nearest the shooter `[D106]`. **NCAA men's specifics [UNVERIFIED]** — follow the current NCAA rulebook | `[D106]` | Defensive-rebound position on FTs: compare which team holds the inside lane spaces. The DREB% on missed FTs is a known swing factor (≈ 40.6% OREB in up-3 spots) `[D81]` |
| **Press after made FT** | Auburn presses harder after a made FT `[D79b]`. Havoc side diamond on inbound/halftime `[D54]` | `[D54][D79b]` | Previous event = made FT, then press active |

---

## F15. FOULING STRATEGY & FOUL-TROUBLE ADJUSTMENTS

| Item | Content | Source | Detection / labeling |
|---|---|---|---|
| **Foul up 3** | See F14. Default is to defend (within noise) `[D81]`. A 2024 paper argues for a time-varying, coachable foul decision instead of treating time as a blocking factor `[D82]` | `[D81][D82]` | Label `foul_strategy = foul_up_3` when the defense commits a non-shooting foul in a +3 / ≤ 12 s context |
| **Intentional foul when trailing** | Late-game fouling to stop the clock [CONVENTION] | — | Defensive foul with margin < 0 and clock < 60–120 s. A time-to-foul after the inbound ≤ 3 s |
| **Foul to give** | With fewer than six team fouls, foul a driving star before the shot to force a reset `[D104]` | `[D104]` | Non-shooting foul in late clock, team fouls below the bonus |
| **Two-foul auto-bench** | Starters with 2 first-half fouls play ~23% of the remaining first-half minutes. Coaches treat halftime as a hard line `[D84]`. KenPom: a 1-foul penalty fades by ~11:00 of the first half. Two-foul players see little time until the last 4–6 min. 3-foul players often sit to start the second half until ~9:00. 4-foul starters don't reach 50% playing time until ~5:00 `[D83]` | `[D83][D84]` | Lineup context → expect scheme shifts (zone, passive coverage) |
| **Defending with a foul-troubled player** | Players foul less as fouls mount: 2.66 / 2.34 / 1.71 fouls per 40 with 0 / 1 / 2 fouls. Hide him on the weakest scorer. Switch hard hedges to passive coverage. Zone teams keep 2-foul players in far more (51% vs 23%) `[D84]` | `[D84]` | For a foul-troubled screener-defender, the aggression index A should drop. The matchup is reassigned to a lower-usage attacker |
| **MSU** | Izzo is near the bottom in 2-foul first-half participation (strict man) `[D84]`. MSU practises the 2-3 for foul-trouble situations `[S74]` | `[D84][S74]` | Expect MSU's 2-3 usage to correlate with big-man fouls |

> **Note:** the NCAA men's team-foul bonus thresholds (1-and-1 at 7, double bonus at 10 per half) are [CONVENTION] here. No rulebook was opened.

---

## F16. COMMUNICATION VOCABULARY → MEASURABLE BEHAVIOURS

Audio is unavailable from broadcast tracking. Each call is mapped to the **behaviour it should produce**, which the label generator can emit as a "virtual call".

| Call | Meaning | Source | Behaviour to detect [HEURISTIC] |
|---|---|---|---|
| "Ball!" | I have the ball-handler | `[D19]` | A defender becomes the ball matchup (≤ 1.5 m) |
| "Help (left/right)!" | Help is here, and from which side | `[D19][D102]` | A help defender within 3 m of the drive lane |
| "Switch!" / "Switch left/right" | Exchange assignments | `[D19]` | `SWITCH` event |
| "Stay!" | No switch | `[D19]` | `SCREEN` with no matchup change |
| "Ice!" | Side-PnR force away from the screen | `[D19][D26]` | Ice pre-positioning (F3.5) |
| "Black" | Switch (LoGalbo outer-third terminology) | `[D26]` | Switch coverage with an X-ball under-path |
| "Jump!" / a teammate's name | Run-and-jump: the jumper commits | `[D50]` | Run-and-jump event |
| "Match!" | Zone → matchup on a high-post entry. Touch the matchup | `[D99]` | Entropy drop at a high-post catch |
| "My ball" (+ bump) | After a post double, one rotator takes the pass and bumps the other | `[D47]` | Two defenders converge, one peels |
| "Ball, ball, ball!" | The top defender in a 3-on-2 | `[D85]` | The top transition defender engages the handler |
| "Shooter right corner!" | Name the threat and its location | `[D102]` | Closeout bias toward the named shooter's area |
| "Dead!" | The dribble is picked up. Everyone denies (pack line dead-ball rule) | `[D3][D102]` | Deny index → 1 within 0.5 s of the dribble end |
| "Screen left/right!" | Early screen call | `[D19]` | Defender pre-adjustment (e.g. top-lock, jump) ≥ 0.5 s before the screen contact |
| "Fixing it" | Re-matching after the press is broken (Havoc) | `[D54]` | A burst of `ROTATE`s after the ball crosses half |
| "Out" / "Home" | 1-1-3 top guards: pressure the ball (out) vs drop to the high post (home) | `[D98]` | Role swap between the top two defenders |
| "Next" | Run-and-jump after a screen or penetration | `[D10][D29]` | A third defender takes the ball |
| "Peel" | Peel switch | `[D10]` | 3-way swap after a blow-by |
| "Scram" | A big takes a guard's post matchup on the entry | `[D19]` | Pass-triggered switch |
| "Tag" | Bump the roller | `[D10]` | `TAG` event |
| "Fist" / "Flat" | 1-2-1-1: trap immediately vs deny then trap on the dribble | `[D3b]` | Trap latency after the inbound: < 1 s = fist, after the first dribble = flat |
| "Madman" | Havoc on-ball defender | `[D54]` | On-ball cushion ≤ 1 m in the backcourt |

---

## F17. DEFENSIVE PLAY-TYPE OUTCOME LABELS (Synergy-style)

Synergy logs a possession when it ends in a FGA, a turnover, or free throws (technical fouls excluded). The **final action** decides the category `[D87][D88]`. Defensive reports present the same play types from the defense's perspective [CONVENTION; the defensive view is not defined in the opened pages].

| Label (defensive view) | Synergy offensive definition | Source | Tracking-derived trigger [HEURISTIC] |
|---|---|---|---|
| **Def. P&R Ball Handler** | The handler uses, splits, or goes away from a screen and ends the possession | `[D87]` | The last `SCREEN` with the ball ≤ 4 s before the end, and the handler is the finisher |
| **Def. P&R Roll Man** | The screener catches and ends it (roll, pop, slip) | `[D87]` | The finisher = the screener of the last ball screen. Sub-label roll/pop/slip from the screener's path |
| **Def. Spot Up** | Catch-and-shoot or catch-and-drive, with a defender open or closing out | `[D87]` | The finisher caught without using a screen. Closeout features attached (F7.5) |
| **Def. Isolation** | One-on-one | `[D87]` | ≥ 3 s of the handler being 1v1 with no screen, other attackers spaced at r > 6 m |
| **Def. Post-Up** | Single defender in the post | `[D87]` | Back-to-basket catch at r < 4.5 m, then the finish |
| **Def. Hand Off** | The screener hands to a cutter | `[D87]` | The last action is a `DHO` |
| **Def. Off Screen** | Coming off an (usually down) screen away from the basket. Curls, fades, flares | `[D87]` | The last off-ball `SCREEN` within 2 s before the catch |
| **Def. Cut** | Catch while moving toward, parallel to, or away from the basket (incl. back screens and flashes). UCLA/flex logged as cuts | `[D87][D88]` | `CUT` then the catch at r < 4 m |
| **Def. Offensive Rebound (Putback)** | The rebounder scores before passing | `[D87][D88]` | An OREB then a FGA within 2 s |
| **Def. Transition** | Ends before the defense is set. Includes press breaks | `[D87]` | The end occurs before `SET_DEF` |
| **Def. Miscellaneous** | Anything else | `[D87]` | — |

**Shot-defense sub-labels**
- **Guarded / unguarded**: ShotTracker reports D-I men's guards shooting 39.3% guarded vs 55.0% unguarded, and bigs 45.2% vs 67.0%. About 79–81% of FGAs are guarded `[D89]`. The threshold is not published there. Use **closest-defender distance at release ≥ 1.8 m (≈ 6 ft) → open** as a [HEURISTIC] (NBA-style convention).
- **SSQ inputs**: Synergy's shot-quality model uses shot type, distance, defender distance (open/guarded), and play type `[D87]`.
- **Turnover type**: live-ball (steal) vs dead-ball. Havoc's goal is live-ball TOs `[D55]`.
- **Contest type**: sprint-stop, fly-by, none (F7.5). **Block**, **charge drawn**, **shooting foul**.

---

## F18. DETECTION ARCHITECTURE & PER-SECOND LABEL SCHEMA

### F18.1 Label hierarchy emitted every second (1 Hz, computed at 10–25 Hz)
```
L0 phase        : {dead_ball, inbound_BLOB, inbound_SLOB, inbound_backcourt, press, transition, half_court_set, FT}
L1 base_scheme  : {man:<philosophy F1>, zone:<family F8>, matchup_zone, junk:<F10>, press:<F9>, unsettled}
L1b scheme_conf : posterior of the L1 label
L2 events       : list of active coverages
                   ball_screen:{coverage F3, X_ball_path, X_big_depth_m, aggression_A}
                   dho:{coverage F4}
                   off_ball_screen:{coverage F5}
                   post:{position F6.1, double F6.3}
L3 help         : {tag, stunt, dig, sink, rotate, x_out, scram, peel, closeout:<type>}
L4 on_ball      : {pressure_m, force_dir, contained:boolean}
L5 context      : {shot_clock, game_clock, margin, prev_outcome, ATO, foul_trouble_ids, lineup}
L6 outcome      : (at possession end) Synergy-style label F17 + guarded/unguarded + TO type
Change log      : {t_trigger, trigger_type, scheme_before, scheme_after, lag_s}
```

### F18.2 The five highest-value detection rules (summary)
1. **Man vs zone via the cutter test plus the follow/ball-shift ratio (F8.0).** When an attacker cuts ≥ 6 m through the lane, does his defender travel ≥ 70% of the cutter's path (man), or hand him off and stay within 1.5 m of the zone slot (zone)? Combine this with F (velocity correlation with the matched attacker) against B (correlation with the ball-conditioned slot shift) over 3 s windows.
2. **Trigger-gated scheme change-point (F11.6).** A sticky HMM over {man, zone-k, match-up} whose transitions are allowed only within ±1 s of coaching triggers: high-post catch, post catch, Nth perimeter pass, ball screen, DHO, shot clock ≤ 10 s, ball crossing half. Report the trigger, t_switch_complete and the lag.
3. **Ball-screen coverage from screen-frame geometry (F3.0).** Measure X-big depth relative to the screen line at t₀+0.3 s (drop ≥ 3.5 m, high drop 1–3.5 m, flat 0–1, level ±0.6, hedge ≤ −0.6 with a lateral offset, blitz = `TRAP` above the line). Add X-ball's pre-t₀ side (ice) and path (over/under/through), plus a reciprocal-matchup test (switch).
4. **Pack-line vs pressure-man via help depth and the deny index (F1.1–F1.2).** Pack line: ≥ 3 off-ball defenders at r ≤ 5.3 m and off the passing lanes. Pressure: one-pass-away defenders on the lane (≤ 0.6 m off segment(a,b), t ≤ 0.35).
5. **Help-action events relative to the roller and the drive (F7).** Tag = a non-X-big defender within 1 m of the roller between t₀+0.5 and t₀+1.8 s, then release. X-out = two weak-side defenders swapping with crossing paths after a skip. Post double = a second defender within 1.5 m of the post-catcher within 0.8 s, labelled by origin (top / baseline / passer / big-to-big).

### F18.3 Matchup backbone
Use the Franks et al. canonical guarding point (0.62 man / 0.11 ball / 0.27 hoop) and an HMM with ρ ≈ 0.96–0.99 as the matchup prior `[D35]`. Re-fit the weights for college (expect more hoop weight for pack-line teams) [HEURISTIC]. HMM-derived features (switch counts, assignment entropy) are known to improve man/zone classification in football tracking `[D36]`. A team-level ball-screen-defense classification across all 10 players reached ≈ 69% accuracy in NBA data `[D37]`, which is a realistic ceiling for an untuned first model.

### F18.4 Michigan State consolidated usage index (what is documented)

| Family | MSU documented usage | Years | Source |
|---|---|---|---|
| Base | Man "90-some %". 2-3 change-up | 2015 | `[S74]` |
| Ball screens | Flat/hard hedge + weak-side tag | ~2019 | `[S69]` |
| Ball screens | Soft hedge base. Rarely switch 1-5 | 2019-20 | `[D25]` |
| Ball screens | Switch with the 5 vs Michigan (0.58–0.67 PPP allowed) | 2018-19 | `[D25][S69]` |
| Ball screens | Hedge-and-recover and/or blitz. Gap bumpers on the roller | 2024-25 | `[D24]` |
| DHO | "Three-Man DHO Switching" practice drill (game usage UNVERIFIED) | — | `[S6]` |
| Help | Elbow help + block help. Contain to avoid multiple rotations | — | `[D4]` |
| Paint | Two-big paint clog (Kohler + Cooper). Opponents 28% 3P (Feb 2025). Opponent 3PA rate 47.4% (Jan 2026) | 2024-26 | `[D57][D58]` |
| Press | Increased full-court pressure in exhibitions | 2023-24 | `[D5]` |
| Rebounding | Hit-Find-Fetch. Low man wins contact. War drill | multi-year | `[D4][D91][D103][S1]` |
| Transition | 4 crash, PG back (offensive glass → 1 back) | — | `[D4]` |
| Foul trouble | Strict-man coach. Low 2-foul participation | — | `[D84]` |
| 2025-26 PnR coverage | **[UNVERIFIED]**. Hand-label from film | 2025-26 | — |

---

## Counts (this file)

- **Families:** 18 (F1–F18). F18 is the architecture and MSU index.
- **Sub-families:** 63, counted from the hierarchy blocks: F1 5 (+MSU), F2 5, F3 6, F4 1 (8 coverages), F5 6, F6 5, F7 6, F8 5, F9 5, F10 1, F11 6, F12 6, F13 5, F14 1, F15 1, F16 1, F17 1, F18 4.
- **Table rows:** 278 data rows in 39 tables. About 210 of them are named schemes, coverages, variants or rules, each with a detection signature. The rest are landmarks, program profiles, the MSU index, and feature definitions.

## Open gaps / to verify with film
- MSU's 2025-26 PnR coverage by personnel **[UNVERIFIED]**.
- MSU press structure (2023-24 onward) **[UNVERIFIED]**.
- Tennessee (Barnes) PnR coverage **[UNVERIFIED]**. Only "shell/gaps" `[D6]` and pull-up-forcing evidence `[D22]` were found.
- "40 Minutes of Hell" press alignments **[UNVERIFIED]**.
- A named D-I program using zone → man on the *first ball screen* **[UNVERIFIED]**. The documented triggers are a high-post catch, the 2nd pass, a post catch, and the 2nd DHO `[D80][D98]`.
- NCAA (not NFHS) free-throw lane-space rule **[UNVERIFIED]**.
- All numeric thresholds are [HEURISTIC]. Calibrate them on 30–50 hand-labelled MSU possessions per family (per set_taxonomy §3.5).

---

## Sources (URLs opened during this pass)

- **D1**: Grantland, "Pack-Line Progeny" (Virginia, Bennett). https://grantland.com/the-triangle/virginia-defense-pack-line-dick-tony-bennett
- **D2**: Hoopscoop, "Brad Soderberg and Dick Bennett Packline Defense Notes". https://www.mensbasketballhoopscoop.com/dick-bennett-and-brad-soderbergs-version-of-the-pack-line-defense/
- **D3**: Basketball for Coaches, "Pack Line Defense – The Complete Guide" (= S65, re-opened). https://www.basketballforcoaches.com/?p=1621
- **D3b**: Basketball for Coaches, "1-2-1-1 Press (Diamond)" (= S76, re-opened). https://www.basketballforcoaches.com/1-2-1-1-diamond-press/
- **D4**: Coaching Toolbox, "D1 Defensive Notes" (Izzo, Cronin, Bo Ryan). https://coachingtoolbox.net/defense/d1-defensive-notes.html
- **D5**: Detroit Free Press via PressReader (Nov 2, 2023), MSU full-court press. https://www.pressreader.com/usa/detroit-free-press/20231102/281925957714961
- **D6**: SI (Illinois), Underwood on Tennessee's defense. https://www.si.com/college/illinois/basketball/illinois-brad-underwood-game-plan-vs-tennessee-defense
- **D7**: Action Network, film breakdown of Houston and Iowa State. https://www.actionnetwork.com/ncaab/college-basketball-film-breakdown-deep-dive-into-houston-iowa-state
- **D8**: Coach Hoops, "Monster Post Trapping". https://coachhoops.substack.com/p/monster-post-trapping
- **D9**: Hoop Vision, "The Ball Screen Coverage Spectrum" (= S70, re-opened, preview only). https://hoopvision.substack.com/p/the-ball-screen-coverage-spectrum
- **D10**: FIBA Europe, *Basketball Terminology* (= S20, re-opened). https://assets.fiba.basketball/image/upload/documents-corporate-regional-offices-europe-programs-fiba-europe-coaching-certificate-fiba-europe-basketball-terminology.pdf
- **D11**: PGC, "Defensive Habits of Houston and Saint Louis". https://coach.pgcbasketball.com/resource/defensive-habits-of-houston-and-saint-louis/
- **D19**: Coach's Clipboard, "Basketball Switching Defense" (= S71, re-opened). https://www.coachesclipboard.net/basketball-switching-defense.html
- **D20**: Coaching Toolbox, "2-3 Zone Part 2" (Boeheim via Neighbors). https://coachingtoolbox.net/defense/basketball-defense-2-3-zone-part-2.html
- **D21**: Daily Orange, film review: guards' miscues in the 2-3 zone. https://dailyorange.com/?p=177693
- **D22**: Stats by Will, "Five plays: Arizona 75, Tennessee 70". https://statsbywill.substack.com/p/five-plays-arizona-75-tennessee-70
- **D23**: Grantland, Syracuse 2-3 zone (Final Four). https://grantland.com/features/syracuse-2-3-zone-final-four/?print=1
- **D24**: MGoBlog, "State Report" (Feb 2025). https://mgoblog.com/content/state-report
- **D25**: Dylan Burkhardt, "Making sense of Michigan at Michigan State" (Jan 2020). https://dylanburkhardt.substack.com/p/making-sense-of-michigan-at-michigan
- **D26**: Breakthrough Basketball (LoGalbo), "Ball Screen Defense - Ice, Drop, and Switch" (= S68, re-opened). https://www.breakthroughbasketball.com/defense/3-ball-screen-logalbo
- **D27**: HoopStudent, "Ball screen defense" (= S67, re-opened). https://hoopstudent.com/ball-screen-defense-basketball
- **D28**: Coaches Insider, "Switching on a Dribble Handoff with Drew Valentine". https://coachesinsider.com/mens-basketball/switching-on-a-dribble-handoff-with-drew-valentine-loyola-univ
- **D29**: Slappin' Glass, "Off-Ball 'Next' Defense". https://slappinglass.substack.com/p/off-ball-next-defense-steve-donahue
- **D30**: HoopStudent, "Basketball dribble handoff". https://hoopstudent.com/basketball-dribble-handoff/
- **D31**: UM Hoops, "Breaking down the Syracuse 2-3 zone" (Nov 2010). https://umhoops.com/2010/11/24/breaking-down-the-syracuse-2-3-zone/
- **D32**: UM Hoops, "Season preview 2010-11: five thoughts on the defense" (Beilein 1-3-1). https://umhoops.com/2010/11/17/season-preview-2010-11-five-thoughts-on-the-defense/
- **D33**: Inspirational Basketball, "Playing Syracuse's 2-3 Zone". https://inspirationalbasketball.com/how-to-play-syracuses-2-3-zone-defense/
- **D35**: Franks, Miller, Bornn, Goldsberry, "Characterizing the spatial structure of defensive skill" (arXiv 1405.0231). https://arxiv.org/pdf/1405.0231
- **D36**: arXiv 2602.10784 (NFL man/zone coverage with HMM features; football analogue). https://www.arxiv.org/pdf/2602.10784
- **D37**: Deakin repository, ML identification of PnR defensive strategies from NBA tracking (up to 69% accuracy). https://dro.deakin.edu.au/articles/journal_contribution/Use_of_machine_learning_to_automate_the_identification_of_basketball_strategies_using_whole_team_player_tracking_data/20690734
- **D38**: Rivals (Texas), "GIF Breakdown: Chris Beard's No-Middle Defense". https://texas.rivals.com/news/gif-breakdown-chris-beard-s-no-middle-defense
- **D39**: Hoopsalytics, "The Analytics of No-Middle Defense". https://blog.hoopsalytics.com/basketball-no-middle-defense-analytics/
- **D40**: Hoop Vision, "The Starting Five: Drop Coverage" (preview only). https://hoopvision.substack.com/p/the-starting-five-drop-coverage-hv
- **D41**: Coach's Clipboard, "Man-to-Man Defense". https://www.coachesclipboard.net/M2MDefense.html
- **D42**: Breakthrough Basketball, "Why No Middle Defense Works". https://www.breakthroughbasketball.com/defense/no-middle-defense-works
- **D43**: Breakthrough Basketball, "Beard vs. Bennett" on-ball positioning. https://www.breakthroughbasketball.com/defense/beardbennettposition
- **D44**: Eleven Warriors, "Breaking the Pearl Press" (2010). https://www.elevenwarriors.com/2010/03/breaking-the-pearl-press.html
- **D45**: Basketball for Coaches, "How to Double the Post – The 4 Best Tactics". https://www.basketballforcoaches.com/how-to-double-the-post/
- **D46**: FIBA WABC Level 3 manual, "Double-team post players". https://wabc-chn.fiba.com/manual/level-3/l3-team/1-defensive-tactics-and-strategies/1-4-advanced-defensive-techniques/1-4-2-double-team-post-players
- **D47**: NABC, "Matt Painter: Big-to-Big Post Double". https://nabc.com/?p=1445
- **D49**: Low Man Help, "The Blueprint: Pick and Roll 101". https://lowmanhelp.substack.com/p/the-blueprint-pick-and-roll-101?open=false
- **D50**: Basketball for Coaches, "Run and Jump Defense" (= S77, re-opened). https://www.basketballforcoaches.com/run-and-jump-defense/
- **D51**: SLAM, "A Beautiful System of Anger" (Richardson). https://slamonline.com/?p=187211
- **D52**: Swish Appeal, "Nolan Richardson, 40 Minutes of Hell". https://www.swishappeal.com/2011/3/11/2044606/nolan-richardson-40-minutes-of-hell-arkansas-razorbacks
- **D53**: Hooper University, "The Right Way to Closeout & Contest". https://www.hooperuniversity.com/breakdowns/the-right-way-to-closeout-and-contest
- **D54**: Hoopscoop, "Shaka Smart VCU Havoc Press Notes". https://www.mensbasketballhoopscoop.com/?p=18679
- **D55**: Better Basketball, "Keys to VCU's HAVOC Defense". https://betterbasketball.com/keys-to-vcus-havoc-defense/
- **D57**: SI (MSU), "3 Stats Identify MSU's Defensive Dominance over Big Ten" (Jan 2026). https://www.si.com/college/michiganstate/spartans-3-stats-identify-defensive-dominance-big-ten
- **D58**: SI (MSU), "Spartans' Defense Continues to Thrive When it Matters Most" (Feb 2025). https://www.si.com/college/michiganstate/basketball/spartans-tre-holloman-jaxon-kohler-carson-cooper-maryland-terrapins-01jn47c8fpkz
- **D60**: Coach's Clipboard, "Amoeba Defense". https://coachesclipboard.net/AmoebaDefense.html
- **D61**: Coach's Clipboard, "1-3-1 Zone Defense". https://www.coachesclipboard.net/131zonedefense.html
- **D62**: The Hoops Geek, "1-3-1 Zone Defense – Complete Guide". https://www.thehoopsgeek.com/1-3-1-zone-defense
- **D63**: Coach's Clipboard, "Aggressive 2-3 Zone Defense". https://www.coachesclipboard.net/Aggressive23zonedefense.html
- **D64**: Breakthrough Basketball, "2-3 Zone Defense, Tips, and Drills". https://www.breakthroughbasketball.com/defense/23-zone
- **D65**: Coach's Clipboard, "2-2-1 Zone Press". https://www.coachesclipboard.net/221ZonePress.html
- **D66**: Coach's Clipboard, "2-2-1 Half-Court Press". https://www.coachesclipboard.net/221HalfCourtPress.html
- **D67**: Coach's Clipboard, "1-2-2 Press". https://www.coachesclipboard.net/122Press.html
- **D68**: The Hoops Geek, "The Box and 1 Defense". https://www.thehoopsgeek.com/box-and-1-defense/
- **D69**: Low Man Help, "How to read off-ball screens". https://lowmanhelp.substack.com/p/how-to-read-off-ball-screens-feat
- **D70**: Basketball for Coaches, "Triangle and 2 Defense". https://www.basketballforcoaches.com/triangle-and-2-defense/
- **D71**: Breakthrough Basketball, "3 Steps To Mastering The Matchup Zone" (= S73, re-opened). https://www.breakthroughbasketball.com/coaching/matchup-zone-installation
- **D72**: The Hoops Geek, "How to Defend the Pick & Roll – 7 Strategies". https://www.thehoopsgeek.com/pick-and-roll-defense
- **D73**: Coach Hoops, "Top Lock". https://coachhoops.substack.com/p/top-lock
- **D74**: HoopStudent, "Shoot the gap". https://hoopstudent.com/basketball-shoot-the-gap
- **D75**: SI (Arizona), "Navigating Baylor's 1-1-3 Zone Defense". https://www.si.com/college/arizona/basketball/arizona-basketball-navigating-baylor-bears-1-1-3-zone-defense
- **D76**: Temple News, "Matchup zone defense has mixed results" (2002). https://temple-news.com/matchup-zone-defense-has-mixed-results/
- **D77**: Action Network, "How to upset Baylor's no-middle defense". https://www.actionnetwork.com/ncaab/ncaa-tournament-betting-film-room-how-to-upset-baylor-bears-no-middle-defense
- **D78**: Baylor Lariat, "Baylor's new small-ball zone defense" (Feb 2025). https://baylorlariat.com/2025/02/12/film-breakdown-baylors-new-small-ball-zone-defense-shows-promise/?amp=1
- **D79**: Breakthrough Basketball, "How To Defend Out Of Bounds". https://www.breakthroughbasketball.com/defense/defending-out-of-bounds-plays
- **D79a**: Stats by Will, "Show Me My Opponent 2022-23: Auburn". https://statsbywill.substack.com/p/show-me-my-opponent-2022-23-auburn
- **D79b**: GoCoogs, "Film study: scouting Auburn". https://gocoogs.com/?p=41665
- **D80**: Slappin' Glass, "Innovative Defenses: Finnish Playbook" (= S79, re-opened). https://slappinglass.substack.com/p/innovative-defenses-finnish-playbook
- **D81**: KenPom, "Yet another study about fouling when up 3". https://kenpom.com/blog/yet-another-study-about-fouling-when-up-3/
- **D82**: arXiv 2402.13289, "College Basketball: An In-depth Study of the Foul Up 3 Dilemma" (abstract). https://arxiv.org/abs/2402.13289v1
- **D83**: KenPom, "Foul trouble as defined by coaches". https://kenpom.com/blog/foul-trouble-as-defined-by-coaches/
- **D84**: Hoop Vision, "Foul Trouble and the Auto-Bench". https://hoopvision.substack.com/p/foul-trouble-and-the-auto-bench
- **D85**: Coach's Clipboard, "Transition Defense". https://www.coachesclipboard.net/TransitionDefense.html
- **D86**: FastModel, "BCAM – Chris Holtmann – Transition Defense". https://playbank.fastmodelsports.com/library/basketball/fastdraw/92338/play-BCAM--Chris-Holtmann--Transition-Defense
- **D87**: Synergy Sports support, "Common Terms & Definitions". https://support.synergysports.com/support/solutions/articles/77000565960--common-terms-definitions
- **D88**: Nylon Calculus (FanSided), "How to understand Synergy play type categories". https://fansided.com/2017/09/08/nylon-calculus-understanding-synergy-play-type-data/
- **D88b**: Coach's Clipboard, "Offensive Rebounding and Transition Defense". https://www.coachesclipboard.net/offensive-rebounding-and-transtion-defense.html
- **D89**: ShotTracker, "Guarded vs. Unguarded: D-I Shot Data Heading Into 2026-27". https://shottracker.com/blog-division-i-basketball-guarded-unguarded-shot-data-2026-27/
- **D90**: Coaching Toolbox, "Tom Izzo rebounding drill". https://coachingtoolbox.net/blog/tom-izzo-rebounding-drill
- **D91**: Coach's Clipboard, "War Drill". https://www.coachesclipboard.net/WarDrill.html
- **D92b**: Coach's Clipboard, "Match-up Press" (= S78, re-opened). https://www.coachesclipboard.net/MatchupPress.html
- **D93**: Coach's Clipboard, "Pressure Defense" (full-court man / 41 Deny). https://www.coachesclipboard.net/PressureDefense.html
- **D94**: Sports Illustrated Vault, "Cry Havoc..." (Feb 4, 2013). https://vault.si.com/vault/2013/02/04/cry-havoc-and-let-slip-the-dogs-of-hoops
- **D95**: Sports Illustrated Vault, "Scouting Reports: May Day, May Day" (Nov 1990). https://vault.si.com/vault/1990/11/19/scouting-reports-may-day-may-day
- **D98**: Slappin' Glass, "Rise of the Zones". https://slappinglass.substack.com/p/rise-of-the-zones
- **D99**: Coaching Idaho, "Let's talk some zone". https://coachingidaho.substack.com/p/lets-talk-some-zone
- **D100**: MIT Sloan SSAC, "To Crash or Not to Crash" (abstract). https://www.sloansportsconference.com/research-papers/to-crash-or-not-to-crash
- **D101**: The Analyst (Opta), "Tracking data reveals which college players are the nation's top rebounders". https://theanalyst.com/articles/tracking-data-reveals-which-college-players-are-the-nations-top-rebounders
- **D102**: PGC Basketball, "10 Commandments of Defense". https://pgcbasketball.com/?p=23732
- **D103**: FastModel, "Drill of the Day: Hit, Find and Fetch". https://fastmodelsports.com/library/basketball/fastdraw/299/play-Drill-of-the-Day-07-20-2011-Hit-Find-and-Fetch-Drill
- **D104**: Coach's Clipboard, "End of Game Defense". https://coachesclipboard.net/EndOfGameDefense.html
- **D105**: Breakthrough Basketball, "Do You Have a Three Point Defense?". https://www.breakthroughbasketball.com/coaching/game-strategy-3-point-defense
- **D106**: Officiating.com forum (NFHS 8-1-4 lane spaces). https://forum.officiating.com/archive/index.php/t-60765.html

**Opened in this pass but not cited above:** Breakthrough Basketball glossary (https://www.breakthroughbasketball.com/basketball-glossary). Hoop Vision "Countering Switches" (preview; https://hoopvision.substack.com/p/countering-switches). Both confirm vocabulary only.

**First-pass sources cited here (from `set_taxonomy.md`, not re-opened in this pass unless listed above):**
- S1 Grantland, Izzo rebounding: https://grantland.com/the-triangle/war-tom-izzo-michigan-state-spartans-rebounding/
- S6 Hoopscoop, Izzo Open Practice Series: https://www.mensbasketballhoopscoop.com/?p=23659
- S19 Coach Hoops, Spain Action: https://coachhoops.substack.com/p/spain-action
- S25 Hoop Vision, Winston & top-lock: https://hoopvision.substack.com/p/cassius-winston-and-top-lock-defense
- S60 SSAC, on-ball screen recognition: https://www.sloansportsconference.com/research-papers/automatically-recognizing-on-ball-screens
- S61 SSAC, ball-screen defense recognition: https://www.sloansportsconference.com/research-papers/recognizing-and-analyzing-ball-screen-defense-in-the-nba
- S66 Coaching Toolbox, Izzo stance: https://coachingtoolbox.net/?p=38218
- S67 = D27. S76 = D3b.
- S69 UM Hoops 2019 MSU breakdown: https://umhoops.com/2019/03/05/video-breakdown-two-areas-michigan-will-need-improve-win-rematch-michigan-state/
- S72 Coaches Insider, Stephens lob defense: https://coachesinsider.com/mens-basketball/post-defense-defending-the-lob-with-dwayne-stephens-western-michigan-university
- S74 NBC CBT, MSU zone: https://collegebasketball.nbcsports.com/2015/10/03/michigan-state-playing-zone-its-possible/
- S75 Cracked Sidewalks, Purdue preview 2025-26: https://www.crackedsidewalks.com/2025/10/purdue-preview-2025-26.html

---

## Additions 2026-10-18 (Job A deep research)

Appended 2026-10-17 by the single writer for this file (date stamp corrected on 2026-10-17; the "2026-10-18" in this section's headings is kept only as the section label so that existing references still resolve). Nothing above this line was edited. This section merges two Job A research notes (man/ball-screen/handoff/off-ball, and zones/presses/junk/scheme changes/transition), both compiled 2026-10-17.

**Rules for this section.**
- Only items that are **new** to this file, or **richer** versions of an existing row (new evidence, numbers, roles, timings, college or MSU attribution), are listed. Each block names the existing row it extends. Rows already complete above are not repeated.
- Units: metres, seconds, degrees. Court spots are **(r m, θ°)**: r from the rim centre, θ from the right baseline measured at the rim centre (θ = 0° along the baseline toward the right sideline, 90° straight up the lane, 180° toward the left sideline), as in `config/vocabulary_map.yaml` and §0.1. x = r·cos θ, y = r·sin θ. Every foot value found in a source was converted at 0.3048 m per foot. For presses the origin stays at the **defended** rim, so the offence's backcourt is y > 12.73 m (opponent FT line y ≈ 21.26 m, opponent top of the arc y ≈ 18.70 m, opponent baseline y ≈ 27.05 m). All y values assume the rim centre 1.60 m from the baseline (old §0.2). **Rim being shot at** = the far rim at (0, 25.45 m) in this defended-rim frame; "attacked rim" keeps its §0.1 meaning (the rim this defence protects).
- Landmarks used below: top (7.6, 90°); right wing (7.3, 35°); left wing (7.3, 145°); wing centre (7.07, 45° / 135°); right corner (6.86, 3°); left corner (6.86, 177°); right block (2.0, 24°); left block (2.0, 156°); right elbow (4.57, 66.4°); left elbow (4.57, 113.6°); nail (4.19, 90°); right slot (7.47, 70°); left slot (7.47, 110°); short corner (4.02, 5.7° / 174.3°) [HEURISTIC; vocabulary_map: to be defined from film]; high screen point (7.34, 84°); right-wing screen point (7.56, 52.5°).
- Detection primitives are those of §0.3–0.4, §F3.0 and §F8.0. **Screen:** this section uses the inherited `SCREEN` primitive of §0.4 / set_taxonomy §0 unchanged. A stricter rule (screener speed ≤ 0.3 m/s for ≥ 0.5 s within ≤ 1.2 m of a teammate's path) is listed only as a proposed alternative `SCREEN_v2`, pending the cross-file screen-rule decision flagged in `docs/taxonomy/motion_starts.md`. **Screen moment t₀** = the frame with the smallest screener-to-on-ball-defender distance, as used by McIntyre et al. `[N32]`; this is the operational definition of the F3.0 contact time t₀, not a second anchor. New primitives `SHAPE_MATCH`, `ONE_ON_BALL`, `CHASER`, `SLOT_RESIDUAL_k`, `PRESS_SETUP`, `INBOUND_LAG`, `GET_BACK` clocks, `OUTNUMBER`, `JAILBREAK`, `SPLIT`, `FAKE_TRAP`, `RECOVER` and `STEP_RELEASE` are defined in A0 below.
- Tags: **unverified** = no source opened in the research confirmed it (or the opened page did not contain it). **[HEURISTIC]** = a detection threshold or template position proposed for this project. **Every numeric threshold, timing window and template coordinate below is [HEURISTIC] unless a source key is attached to that number.** **[CONVENTION]** = common coaching usage without a single opened source.
- Source keys `[Nxx]` and `[DZxx]` resolve in **Additional sources (2026-10-18)** at the end of this section. `[Dxx]` and `[Sxx]` keys resolve in the existing Sources list above; where a D/S source was re-opened in this research it is also listed under its new key.
- College (NCAA D-I) terms first. NBA and European terms are secondary aliases or secondary priors and are labelled that way.

### A0. New detection primitives (extend §0.3–0.4) [HEURISTIC]

| Primitive | Definition |
|---|---|
| `SHAPE_MATCH` (d̄_m) | Hungarian assignment of the 5 defenders to the 5 attackers minimising total distance; d̄_m = mean matched distance. Man and match-up zones give d̄_m ≤ 2.0 m in the half-court; pure zones give d̄_m ≥ 2.5 m when the offence overloads one side |
| `ONE_ON_BALL` | Exactly one defender within 1.5 m of the ball-handler on ≥ 80% of frames outside `TRAP` windows. Encodes the match-up-zone rule "never two defenders on one player" `[DZ01][DZ59]` |
| `CHASER(d,a)` | Defender d has follow score F ≥ 0.8 against attacker a and stays within 2.0 m of a on ≥ 85% of frames, even when a is two or more passes away (ordinary two-away man defenders sag to r_d − r_a ≤ −2 m) |
| `SLOT_RESIDUAL_k` | Mean distance of the 5 defenders (optimally permuted) to the ball-location-conditioned template of zone family k (templates in the zone blocks below) |
| `PRESS_SETUP` | t_setup = time from the opponent's made FG/FT (PBP timestamp) until ≥ 3 defenders sit within 2.0 m of backcourt template slots (y > 12.73 m) |
| `INBOUND_LAG` | t_ib = time from the made basket to the inbound pass leaving the inbounder's hands (ball crosses the baseline plane, y ≈ 27.05 m) |
| `GET_BACK` clocks | After a change of possession at t0 (defensive-rebound frame, steal frame or made-basket frame): **t_rim** = first time a defender of the team that lost the ball is at r ≤ 1.5 m from his own rim; **t_stop** = first time a defender is ≤ 2.0 m from the ball-handler *and* the handler's speed falls below 3.0 m/s; **n_back(t0+Δ)** = number of that team's players with y below the ball at Δ = 2, 3, 4 s |
| `OUTNUMBER(k_o, k_d)` | At t0 + 2 s, count attackers and defenders with y < y_ball + 1.0 m in the attacking half (2v1, 3v2, 4v3, 5v4) |
| `JAILBREAK` | The ball-handler reaches r ≤ 3.0 m with no defender within 1.5 m, ≤ 1.5 s after t₀ of a ball screen (see BS2) |
| `SPLIT` | The ball-handler passes between X-ball and X-big while their separation is ≥ 1.2 m (see BS4) |
| `FAKE_TRAP` | A second defender comes within 2.0 m of the handler and the approach does **not** meet `TRAP` (either the distance stays > 1.5 m or the 1.5 m contact lasts < 0.6 s), followed by a retreat ≥ 1.0 m within 1.0 s (see P-2). Every approach within 2.0 m is therefore either `TRAP` or `FAKE_TRAP`, with no gap between them |
| `RECOVER(d,a)` | Defender d travels ≥ 1.5 m toward attacker a and ends within 2.0 m of a. `CLOSEOUT` (§0.4: ≥ 2.5 m travel, peak ≥ 4 m/s, end ≤ 1.5 m) is the strict subset. Closeout length classes use the end distance as the class variable: **hard** = `CLOSEOUT` ending ≤ 0.8 m; **short** = `RECOVER` ending 1.2–2.0 m (see M-4, BS-8) |
| `STEP_RELEASE(d)` | Displacement ≥ 0.5 m toward the ball-handler starting within 0.4 s of a middle-dribble start (\|x_b\| decreasing ≥ 0.8 m), then a reversal ≥ 0.4 m toward d's own man within 0.5 s of the dribble pickup, with no matchup change. Replaces the 1.0 m `STUNT` threshold for the Izzo one-step help (M-1, M-5) |

---

### A1. Man principles (extends F1, F7)

#### M-1. Izzo "head-up, help-not-deny" man (MSU "Defensive Anticipation") — RICHER (extends F1.6 and F1.1)
- **Name and aliases:** Izzo man philosophy; "Defensive Anticipation"; "Pass Defense / Man Philosophy" (Izzo clinic notes).
- **Family / sub-family:** F1.1 Help-first family (it is **not** pack line), program profile F1.6. New sub-family **F1.1.5 Help-position man (one big step off the line)**.
- **Start alignment** (ball at the right wing, 5-out offence; X3 on the ball):

  | Defender | Man at | Defender spot (r, θ) | Note |
  |---|---|---|---|
  | X3 on ball | right wing (7.3, 35°) | (6.4, 34°) | ≈ 0.9–1.0 m in front, square |
  | X1 one pass away | top (7.6, 90°) | (6.0, 75°) | ≈ 1/3 of the way from man to ball, ≈ 0.8 m off the line toward the rim |
  | X2 one pass away | right corner (6.86, 3°) | (6.0, 14°) | same rule |
  | X4 two passes away | left wing (7.3, 145°) | (2.8, 116°) | both feet in the lane, \|x\| ≤ 1.83 m |
  | X5 post | right block (2.0, 24°) | (2.4, 38°) | 3/4 high side, ball side |

  Spots are [HEURISTIC]; one "big step" is taken as ≈ 0.8 m.
- **Roles / rules** `[N10]`: guard the man head-up, body always between man and basket. On the ball: shoulder to shoulder, feet to feet, do not drop a foot to open up; stay square and split the man with one foot to force him (right foot forces left, left foot forces right); one hand pressures the ball, the other is down; mirror the ball. Off the ball: help position, not denial, one big step off the passer–receiver line; step at the dribbler to stop penetration, release back as he picks up the dribble. Move on the pass, not on the catch (all five). Closeouts with choppy steps, not a jump stop. Help ↔ ball in two steps each way. Post usually **not** fronted: 3/4 high side, ball side, elbow in the post's back ("chicken wing"); fronting is avoided because it hurts rebounding. Weak side "two feet in the paint". Rationale: taking away penetration lets the bigs help less, which helps rebounding `[N10]`. Also: ball pressure forces more turnovers than help; elbow help and block help; on a shot the post defender gets behind the post `[N12]` (= D4 re-opened).
- **Ordered actions with timing:**
  1. Pass released (t = 0). All five start moving during the flight (≈ 0.3–0.8 s on perimeter passes).
  2. The new on-ball defender closes out with choppy steps and is set by the catch, or ≤ 0.4 s after it.
  3. New one-pass-away defenders reach the help spot (≈ 0.8 m off the line) in two steps (≈ 0.6–0.9 s).
  4. On a dribble toward the middle, the nearest helper steps at the ball (≈ 0.6–1.0 m) and releases back when the dribble is picked up `[N10][N38]`. Detected with `STEP_RELEASE` (A0), not `STUNT`.
- **Usual counters:** skip passes over a help side that sits two steps from the ball rather than packed; quick reversal before helpers recover; low-side post seals against 3/4 high side. Backdoor is less effective than against denial. [CONVENTION; no opened source lists counters.]
- **Detection signature [HEURISTIC]:**
  - (a) **Help-line offset:** one-pass-away defenders sit 0.5–1.2 m off segment(man, ball) on the rim side, lane fraction t ∈ [0.2, 0.45]. Deny is ≤ 0.6 m on the line (F1.2); expected r_d for helpers whose man is at the arc is **5.5–6.3 m**, i.e. outside the pack line (r ≤ 5.3 m). This is the main Izzo-man vs pack-line separator.
  - (b) **Move-on-pass latency:** median time from pass release to each off-ball defender's acceleration (≥ 1.5 m/s²) toward his new spot ≤ 0.25 s, and before the catch on ≥ 70% of passes.
  - (c) **Choppy closeout:** deceleration spread over the last 1.0–1.5 m, no single-frame stop; end distance 0.8–1.2 m.
  - (d) **Two-step help-to-ball:** a helper converted to on-ball defender travels ≤ 2.0 m in ≤ 0.9 s.
  - (e) **Weak side in the paint:** two-pass-away defenders have \|x\| ≤ 1.83 m while the ball is on a wing or in a corner.
  - (f) **Post:** with y_b > 4.19 m, the post defender is on the ball side and half-court side of the post within ≤ 0.9 m; full front on < 15% of post-entry-threat frames.
  - (g) Square stance / stance split needs pose; not readable from positions.
- **Teams documented (MSU first):** Michigan State (Izzo), clinic notes in a 2017 playbook compilation, clinic season **unverified** — https://thebasketballplaybook.com/wp-content/uploads/2017/08/Tom-Izzo-Michigan-State-Playbook.pdf `[N10]`. MSU practice video 2015 lists "six-eye" positioning, shell, Jump to the Ball, Negaunee — https://www.mensbasketballhoopscoop.com/?p=23659 `[N40]`. MSU 2010-11 practice video: 4-on-3 / 4-on-4 shell for ball pressure, communication and help-side recovery — https://onlinestore.coachingtoolbox.net/product/all-access-michigan-state-basketball-practice-with-tom-izzo/ `[N11]`.
- **Sources:** `[N10][N12][N38][N40][N11]`.
- **Confidence:** high for the principles (direct clinic text); thresholds and the 0.8 m step are heuristic; season of the notes **unverified**.

#### M-2. Ball-line man (Tubby Smith) — NEW (F1.1 variant)
- **Name and aliases:** ball-line defense; ball-line man; "ball line" help.
- **Family / sub-family:** F1.1 Help-first family, new sub-family **F1.1.6 Ball-line man**.
- **Definition** `[N1]`: man-to-man with on-ball pressure and off-ball help. The ball line is a horizontal line through the ball to each sideline (y = y_b). Defenders near the ball line stay close to their men; weak-side defenders farther away sink to the lane and basket. Discourages penetrating passes (toward the basket) and allows non-penetrating ones.
- **Start alignments** (roles from `[N1]`; coordinates [HEURISTIC]):
  - Ball at the top: X2 and X3 deny the wings at about (6.5, 45°) and (6.5, 135°); X4 steps off toward the left-corner help spot; X5 guards 5 and protects the basket.
  - Ball at the right wing: X1 slides to the nail (4.19, 90°); X3 to the left elbow (4.57, 113.6°); X4 into the lane at about (2.0, 120°); X5 may front the post on the high side.
  - Ball in the right corner: X5 fronts on the baseline side; X2 drops to the right mid-post; X1 below the FT line at about (3.5, 80°); X3 above the left block near the ball line.
- **Roles / rules** `[N1]`: post entry → X2 and X5 double, X4 digs, X1 and X3 stay in the lane near the ball line. Post-front rule: ball above the FT-line extension → front high side; below it → front baseline side. Baseline/corner trap: the nearest off-ball defender traps with the on-ball defender; the open outlet is the non-penetrating pass.
- **Ordered actions with timing [HEURISTIC]:** (1) pass to the wing/corner (t = 0); (2) all off-ball defenders reach y ≤ max(y_b + 0.5, 3.5) m within 1.0 s; (3) post-front side flips within 0.5 s of the ball crossing y = 4.19 m; (4) corner trap formed within 1.0 s of a corner catch.
- **Usual counters:** skip over the sunken weak side; lob over the front; the open man opposite a corner trap [CONVENTION].
- **Detection signature [HEURISTIC]:**
  - (a) **Ball-line depth rule (wing ball, y_b ≥ 2.5 m):** Δy_d = y_d − y_b ≤ +0.5 m for **all** off-ball defenders. Pack line sets depth by radius (r_d ≤ 5.3 m), not by y relative to the ball. Single-rule form covering wing and corner: y_d ≤ max(y_b + 0.5, 3.5) m for all off-ball defenders.
  - (b) **Corner ball (y_b < 2.5 m, e.g. y_b ≈ 0.4 m):** rule (a) is not used; test instead that all four off-ball defenders are at y_d ≤ 3.5 m and at least 3 at y_d ≤ 2.0 m (consistent with the start alignment, where X1 sits at y ≈ 3.45 m). Ball at the wing (y_b ≈ 4.2 m): helpers at the nail and elbow (y ≈ 4.2 m), not deeper.
  - (c) Post-front side flips with y_b: high-side front when y_b > 4.19 m, baseline-side front when y_b < 4.19 m.
  - (d) Corner trap: `TRAP` with the ball at θ ≤ 12° or ≥ 168°, second trapper = nearest off-ball defender.
- **Teams documented:** Tubby Smith's programs, credited without a season — https://hoopstudent.com/ball-line-defense `[N1]`. No D-I team-season confirmed: **unverified**. MSU: none.
- **Sources:** `[N1]`.
- **Confidence:** medium for the principles (one coaching site); low for program attribution.

#### M-3. Help-side "I" with "bottom out, top down" and the 1/3–2/3 deny rule — RICHER (extends F7.1 "I" alignments and F7.4)
- **Name and aliases:** Helpside I; Low I / Top I; cover down; 1/3–2/3 deny rule.
- **Family / sub-family:** F7.1 Help positions + F7.4 Rotations.
- **Start alignment** (ball in the right corner (6.86, 3°)): Low I at about (1.2, 121°), on the midline near the rim; Top I at about (3.5, 98°), near the nail; strong-side helpers as F7.1.
- **Roles / rules** `[N24]`: one pass away, deny stance about 1/3 of the way toward the man and 2/3 away from the ball. Two passes away with the ball above the FT-line extension: straddle the lane line just below the ball line. Ball below the FT-line extension: the two help-side defenders form the "I" on the midline. On paint penetration the Low I meets the drive (outside the lane if it threatens the rim), the Top I covers down to replace him ("bottom out, top down"), the last help-side defender X-outs to the open shooter. Shared calls make the rotation about **0.5 s** faster `[N24]`.
- **Ordered actions with timing:** (1) drive enters the paint, t = 0; (2) Low I meets the driver by t + 0.5 s; (3) Top I drops ≥ 1.5 m toward the rim by t + 0.8 s; (4) last helper starts the X-out on the kick-out pass. Windows [HEURISTIC] except the 0.5 s gain `[N24]`.
- **Usual counters:** lob to the Low I's man; kick to the Top I's man [CONVENTION].
- **Detection signature [HEURISTIC]:**
  - (a) "I" stack: two weak-side defenders with \|x\| ≤ 1.0 m and Δy ≥ 1.5 m between them while y_b < 4.19 m.
  - (b) "Bottom out, top down": within 1.0 s of paint entry (ball \|x\| ≤ 1.83 m, y ≤ 4.19 m), the lower I moves toward the ball and the upper I's r falls ≥ 1.5 m; their HMM matchups change in sequence (a two-step `ROTATE` chain).
  - (c) 1/3 rule: lane fraction t ≈ 0.33 from the man; with perpendicular offset ≤ 0.6 m → deny; 0.8–1.2 m → Izzo help (M-1).
- **Teams documented:** generic coaching source, no team named — https://fastbreak.playbooktech.com/coaches-community/?p=2195 `[N24]`. X-out mechanics match LMH 2i — https://lowmanhelp.substack.com/p/the-blueprint-pick-and-roll-101?open=false `[N36]` (= D49 re-opened). MSU: **unverified**.
- **Sources:** `[N24][N36]`.
- **Confidence:** medium.

#### M-4. Rotation policies: help the helper / rotate-and-recover / no rotation (KYP); strong-side corner rule; sink-and-fill; hard vs short closeout — RICHER (extends F7.4 and F7.5)
- **Name and aliases:** help the helper; full rotation; rotate-and-recover; "KYP" (know your personnel) no-rotate; "don't help off the strong-side corner"; sink and fill; hard (long) closeout; short closeout.
- **Family / sub-family:** F7.4 Rotations, new **rotation-policy** label set; F7.5 Closeouts (length class).
- **Start alignment** (drive from the right wing; [HEURISTIC]): ball-side corner defender at (6.0, 10°) on a man at (6.86, 3°); weak-side low man at (1.2, 121°); weak-side top helper at (5.6, 117°); post defender at (2.4, 38°).
- **Roles / rules** `[N22]` (NBA source; principles apply to D-I, secondary): help comes from the weak side, the low man is the first line at the rim; do not help out of the strong-side corner (some teams allow a jab step only); help the helper = after the first help another defender takes the newly open man; full rotation = a chain where the original helper recovers to the end and matchups change permanently; rotate-and-recover = the helper returns to his own man while a nearby defender stunts to buy time; no rotation = leave a non-shooter (KYP); sink and fill = a perimeter defender sinks to take away the interior pass and the nearest helper fills for him, then recovery to original men or an X-out; hard (long) closeout against shooters (fly-by is the extreme), short closeout against non-shooters.
- **Ordered actions with timing [HEURISTIC]:** (1) help commits at t_help; (2) second line moves within 0.8 s; (3) policy resolves within t_help + 3 s.
- **Usual counters:** kick to the man left by KYP when he can shoot; second-side drive against a short closeout [CONVENTION].
- **Detection signature [HEURISTIC]:**
  - **Strong-side corner rule:** the ball-side corner defender (man at θ ≤ 12°, same sign of x as the ball) moves ≤ 1.0 m toward the driver; a ≤ 0.5 m excursion that returns within 0.6 s = jab. Report the rate per drive.
  - **Policy per drive:** count `ROTATE` events in [t_help, t_help + 3 s]. 0 rotations with the helper back on his man ≤ 2.0 s → rotate-and-recover. ≥ 2 sequential rotations with new matchups persisting ≥ 2 s → full rotation / help the helper. An open kick-out receiver whose nearest defender stays ≥ 3.5 m away for the window while that defender stays in the paint → no-rotation (KYP); validate against the receiver's 3P% metadata.
  - **Sink-and-fill:** defender A moves ≥ 1.5 m toward the rim and defender B shifts ≥ 1.0 m toward A's vacated man within 0.8 s, without crossing paths (crossing = X-out, existing F7.4).
  - **Closeout length:** hard = `CLOSEOUT` with end distance ≤ 0.8 m and speed ≥ 3 m/s at 1.5 m from the shooter; short = `RECOVER` (A0) that stops at 1.2–2.0 m. A short closeout never satisfies `CLOSEOUT` (end ≤ 1.5 m is required there), so it is built on `RECOVER`.
- **Teams documented:** NBA league-wide principles (secondary) — https://cleaningtheglass.com/how-do-nba-defensive-rotations-work/ `[N22]`. D-I team attribution **unverified**; MSU **unverified**.
- **Sources:** `[N22]`.
- **Confidence:** high for the definitions; thresholds heuristic.

#### M-5. Izzo "Jump to the Ball" / step-and-release — NEW (F7.3 help action, MSU)
- **Name and aliases:** jump to the ball; step-and-release; "see both".
- **Family / sub-family:** F7.3 Help actions, new sub-family **on-pass jump + dribble step**.
- **Start alignment:** attackers 0.30 m (converted from the source's foot) off the extended lane line (side not specified) `[N38]`; taking the outside side, \|x\| = 1.83 + 0.30 = 2.13 m just beyond the arc: (7.32, 73.1°) and (7.32, 106.9°) [HEURISTIC]; ball defender at about (6.6, 73°); helper at about (5.6, 100°), in the gap between the ball and the left elbow.
- **Roles / rules:** FastModel's Izzo drill: two attackers pass back and forth; x2 starts on the ball and x1 in help; they swap help↔ball on every pass; the coach stands with the help defender and asks whether he can see both. Frame 2 adds a dribble toward the middle: the helper stays low, takes **one step** at the dribbler and releases back as the dribbler starts to pick up the ball `[N38]`. Generic definition: on a pass between adjacent perimeter spots the passer's defender side-jumps into the gap during the flight, taking away the face cut and middle penetration `[N23]`.
- **Ordered actions with timing [HEURISTIC]:** (1) pass in flight (0.3–0.6 s): the passer's defender starts the jump during the flight and reaches 1.0–2.0 m toward the ball side and the rim by catch + 0.5 s; (2) catch: the new on-ball defender closes out; (3) middle dribble: the helper steps ≈ 0.6–1.0 m toward the ball within 0.4 s of the dribble start; (4) pickup: the helper recovers ≥ 0.5 m toward his man within 0.5 s.
- **Usual counters:** face cut when the jump is late; kick to the helper's man during the step [CONVENTION].
- **Detection signature [HEURISTIC]:** **Jump** — the passer's defender moves ≥ 0.5 m inside [t_release, t_catch] (optionally ≥ 1.5 m/s × flight time) and ≥ 1.0 m by t_catch + 0.4 s, with Δx of the receiver's x sign, ending with r_d ≥ 0.8 m smaller than the passer's r. (From a stance start at about 4–5 m/s² a defender covers only ≈ 0.2–0.25 m in 0.3 s and ≈ 0.8–0.9 m in 0.6 s, so ≥ 1.0 m inside the flight would miss most real jumps; arithmetic only.) **Step-and-release** — `STEP_RELEASE` (A0), triggered by a middle dribble and released at the dribble-pickup event, not on the fixed 1.0 s `STUNT` timer. The trigger and the 0.5 m threshold separate it from F7.3 Stunt.
- **Teams documented (MSU first):** Michigan State (Izzo drill; FastModel entry undated) — https://playbank.fastmodelsports.com/library/basketball/fastdraw/68911/play-Tom-Izzo-Jump-to-the-Ball `[N38]`; the Izzo course lists "Jump to the Ball" as a lesson — https://coachtube.com/course/basketball/defensive-skills-and-drills/118044 `[N37]`; MSU 2015 practice video lists the drill `[N40]`.
- **Sources:** `[N38][N23][N37][N40]`.
- **Confidence:** high for the definition; thresholds heuristic.

---

### A2. Ball-screen coverages (extends F3)

#### BS-1. Ball-screen labelling backbone: screen moment, four coarse classes, priors — RICHER (extends F3.0 and F3.7)
- **Name and aliases:** over / under / switch / trap (level-1 classes); hedge and show as named sub-types.
- **Family / sub-family:** F3.0 measurement frame; F3.7 spectrum; F18 architecture.
- **Start alignment:** any ball screen; reference high PnR = screener at (7.34, 84°), handler at (7.6, 90°), X-big within 1.5 m of the screener on the rim side.
- **Roles / definitions (NBA SportVU)** `[N32]`: **Over** = the on-ball defender stays between handler and screener. **Under** = he does not. **Switch** = on-ball and screener defenders exchange matchups. **Trap** = both double the handler. Sub-types named but not modelled: **hedge** (the screener's defender jumps out on the handler) and **show** (slides out just far enough to present an obstacle). Each instance is labelled by its most defining characteristic (over then trap = trap).
- **Ordered actions with timing:** t₀ = minimum screener-to-on-ball-defender distance; features from 10 frames before t₀ until the shot, pass, turnover or stoppage, from summary statistics of all pairwise distances among handler, on-ball defender, screener and screener defender (25 Hz) `[N32]`.
- **Results (for priors):** multinomial logistic regression on 340 hand labels (199 over, 56 under, 57 switch, 28 trap): **69% (±3%) accuracy**; trap was the hardest class; 2013-14 Heat trapped 13.2% vs a 7.5% league average `[N32]`; applied to 270,823 screens over 4 seasons `[N31][N32]`. International prior (2019 FIBA World Cup, n = 515): switch 46.0%, over 24.5%, under 17.5%, trap 8.7%, ice 3.3%; effectiveness differed by type (χ² = 14.4, p = 0.006) `[N33]` — non-NCAA prior only.
- **Usual counters:** n/a (labelling method).
- **Detection signature [HEURISTIC]:** keep the four coarse classes as level-1 labels with the finer F3 coverages (drop depth, hedge type, ice, …) as level-2. Over/under test at t₀ ± 0.2 s: the on-ball defender's projection onto segment(handler, screener) has parameter 0 < t < 1 with perpendicular distance ≤ 0.8 m → over; otherwise rim side of the screener → under. Expect level-1 accuracy above 69% with 25 Hz college tracking plus pose; calibrate on MSU film.
- **Teams documented:** NBA 2013-14 to 2016-17 (secondary) — https://www.sloansportsconference.com/research-papers/recognizing-and-analyzing-ball-screen-defense-in-the-nba `[N31]`; 2019 FIBA World Cup — https://pmc.ncbi.nlm.nih.gov/articles/PMC9820029/ `[N33]`.
- **Sources:** `[N31][N32][N33]`.
- **Confidence:** high for the cited methodology and numbers.

#### BS-2. Point-of-attack options "Quickest path" and "Down"; jailbreak — NEW (Down, jailbreak) / RICHER for the name "quickest path" (F2 / F3.5)
- **Name and aliases:** quickest path (label `poa_quickest_path`: over/under chosen by position; distinct from the F2.2 force-direction label "quickest path", which keeps its older meaning); down (= ice family); "jailbreak" (failure state).
- **Family / sub-family:** F2 On-ball rules + F3.5 Directional.
- **Start alignment:** high PnR reference (BS-1); X-ball at about (6.8, 95°) on the handler at (7.6, 90°).
- **Roles / rules** `[N36]` (= D49 re-opened): the four standard POA options are Over, Under, Quickest Path (pick over or under from where you are in the action) and Down. With Down the POA defender and the big must agree; miscommunication causes "jailbreaks", which almost always end in baskets.
- **Ordered actions with timing [HEURISTIC]:** POA choice is fixed by t₀ − 0.3 s; jailbreak resolves within t₀ + 1.5 s.
- **Usual counters:** re-screen to flip the angle against Down; attack the miscommunication [CONVENTION].
- **Detection signature [HEURISTIC]:** **`poa_quickest_path`** (team-level label): within a game, over/under per screen is predicted by the on-ball defender's pre-t₀ position (rim side of the handler–screener segment at t₀ − 0.3 s → under; handler side → over) with accuracy ≥ 0.8, and the team's over share is between 0.3 and 0.7 (no fixed preference), over ≥ 20 ball screens. **Jailbreak:** `JAILBREAK` primitive (A0).
- **Teams documented:** generic — https://lowmanhelp.substack.com/p/the-blueprint-pick-and-roll-101?open=false `[N36]`. MSU **unverified**.
- **Sources:** `[N36]`.
- **Confidence:** medium.

#### BS-3. "Through" (slide through, "open up") — RICHER (F3.1; path class existed in F3.0, coverage row was missing)
- **Name and aliases:** slide through; through; open up and let him through.
- **Family / sub-family:** F3.1 Containment, X-ball path.
- **Start alignment:** screener at (7.34, 84°); X-big ≈ 1.0–1.5 m below him at about (6.0, 84°); X-ball on the handler at about (6.8, 92°).
- **Roles / rules:** used when the handler is not a shooting threat. The screener's defender calls "Screen right/left … Through!" and steps back to open a lane; the screened defender drops below the screener and slides between screener and screener's defender `[N20]`. The same "open up" concept is used on down screens with a post–guard mismatch `[N35]`.
- **Ordered actions with timing [HEURISTIC]:** (1) t₀ − 0.5 s: X-big steps back ≈ 0.5–1.0 m; (2) t₀: X-ball passes between screener and X-big; (3) t₀ + 0.5 s: X-ball re-attached at 1.0–2.0 m.
- **Usual counters:** pull-up three over the screen; re-screen [CONVENTION].
- **Detection signature [HEURISTIC]:** X-ball's path at t₀ crosses the segment between screener and X-big (path class "through"), X-big depth 0.8–2.0 m at t₀, and X-big moves ≥ 0.5 m away from the screener in [t₀ − 0.6, t₀]. Under differs: X-ball also passes on the rim side of X-big.
- **Teams documented:** generic (ASEP coaching text) — https://coachesinsider.com/mens-basketball/defending-screens-article/ `[N20]`. D-I attribution **unverified**.
- **Sources:** `[N20][N35]`.
- **Confidence:** medium.

#### BS-4. "Up to touch" with arrival timing; split event — RICHER (extends F3.1 "At the level")
- **Name and aliases:** up to touch; at the level; level; "aggressive drop" / "level drop" (Eurohoops alias).
- **Family / sub-family:** F3.1, boundary row between containment and show.
- **Start alignment:** screener at (7.34, 84°); X-big ≤ 0.6 m from him on the rim side at about (6.9, 84°) at t₀.
- **Roles / rules:** FIBA: the screener's defender starts at the level of the screen; flat hedge is just below the level `[N34]` (= D10 re-opened). New timing: the big must get up to touch, arriving at the screen **at the same time as the offensive big**, stand the handler up so the guard can recover, keep contact with the rolling screener so no backside switch is needed, and turn his head to the ball for a possible late switch `[N9]`. A level or aggressive drop sits much higher than drop and relies on the low man to tag the roll `[N2]`.
- **Ordered actions with timing [HEURISTIC]:** (1) t₀ − 1.5 s to t₀: X-big moves with the screener, ≤ 1.0 m apart; (2) t₀: \|λ\| ≤ 0.6 m; (3) t₀ to t₀ + 0.8 s: X-big holds the handler; (4) recovery to the roller.
- **Usual counters:** split the screen when the big is late; slip; early roll `[N9]`.
- **Detection signature [HEURISTIC]:** arrival lag Δt_arr = (first time X-big is within 1.0 m of the screen point) − (time the screener becomes stationary). Up to touch: Δt_arr ≤ +0.2 s; late (split risk): Δt_arr > 0.5 s. Keep the existing \|λ\| ≤ 0.6 m geometry. `SPLIT` primitive (A0).
- **Teams documented:** NBA examples (secondary) — https://slappinglass.substack.com/p/pnr-defense-canceling-screens `[N9]`. D-I **unverified**.
- **Sources:** `[N34][N9][N2]`.
- **Confidence:** high for the definition; thresholds heuristic.

#### BS-5. Quick show-and-recover (soft show) with MSU attribution and the no-rotation check — RICHER (extends F3.2 "Soft hedge / show")
- **Name and aliases:** quick show; show-and-recover; soft show; soft hedge.
- **Family / sub-family:** F3.2 Show family.
- **Start alignment (MSU high PnR):** screener (5) at (7.34, 84°); X5 up to touch at about (6.8, 86°); X-ball on the handler at (6.8, 95°); weak-side low man at about (1.5, 120°).
- **Roles / rules:** the big briefly shows, then recovers to the roller, keeping the PnR a 2-on-2 and the defence out of rotation; the guard fights over, keeps contact, must not "die on the screen" `[N9]`. Show = the screener's defender slides out just far enough to present an obstacle `[N32]`. NBA example (secondary): in "last year's NBA Finals" (2020, inferred from the Feb 2021 article date) the Heat used a quick show-and-recover so that Butler or Crowder could stay on LeBron James instead of switching the screener's defender onto him `[N9]`. **MSU 2019-20:** base defence is generally to soft hedge ball screens; MSU rarely switches 1-5, and never switched 1-5 against Moritz Wagner in 2017-18 `[N43]` (= D25 re-opened). *Re-confirmation of F1.6 (line "Ball screens, 2017-20") and the F18.4 rows; not new evidence.*
- **Ordered actions with timing [HEURISTIC]:** (1) t₀: X-big shows 0.5–1.0 m into the handler's path; (2) t₀ + 0.4–0.8 s: X-ball re-attaches ("back, back"); (3) X-big back on the roller by t₀ + 1.2–1.6 s, no tag needed when on time.
- **Usual counters:** split; slip; middle penetration on a late show `[N9]`.
- **Detection signature [HEURISTIC]:** existing soft-hedge geometry (λ between −1.0 and +0.5 m, show ≤ 0.8 s) plus (a) **no-rotation check**: no off-ball `ROTATE` in [t₀, t₀ + 2 s] and no tag (no off-ball defender within 1.0 m of the roller) — the 2-on-2 property, the main split from hard hedge; (b) X-ball within 1.5 m of the handler by t₀ + 0.8 s.
- **Teams documented (MSU first):** Michigan State 2019-20 (base) and 2017-18 (no 1-5 switch vs Michigan) — https://dylanburkhardt.substack.com/p/making-sense-of-michigan-at-michigan `[N43]` (re-confirmation of F1.6). Miami Heat, 2020 NBA Finals vs the Lakers (secondary; season inferred) — https://slappinglass.substack.com/p/pnr-defense-canceling-screens `[N9]`.
- **Sources:** `[N9][N32][N43]`.
- **Confidence:** high for the MSU 2019-20 attribution; mechanics from an NBA/European coaching source.

#### BS-6. Late switch (after show-and-recover) — NEW (F3.4)
- **Name and aliases:** late switch.
- **Family / sub-family:** F3.4 Exchange family, new sub-family **conditional switch**.
- **Start alignment:** as BS-4/BS-5 (up-to-touch or soft-show geometry at t₀).
- **Roles / rules** `[N9]`: after recovering, the big switches onto the handler if the handler gets to the rim, and the guard takes the rolling big; the guard can use the roller's momentum to push or pin him under the rim (re-checked on the opened page in the 2026-10-17 fix pass: the late-switch section states this; the "limits offensive rebounds" rationale is not on the page — **unverified**).
- **Ordered actions with timing [HEURISTIC]:** (1) show-and-recover, t₀ to t₀ + 1.2 s; (2) handler drives to r ≤ 3 m; (3) X-big leaves the roller and becomes the ball matchup at t₀ + 1.0 to 2.5 s; (4) X-ball takes the roller near the rim.
- **Usual counters:** lob or dump to the roller over the smaller defender; offensive rebound [CONVENTION].
- **Detection signature [HEURISTIC]:** soft-show or up-to-touch geometry at t₀, then `SWITCH(X-ball, X-big)` that **starts after t₀ + 1.0 s** with the handler at r ≤ 3.5 m at the switch moment (an ordinary switch completes by t₀ + 1.0 s).
- **Teams documented:** none named in `[N9]` (https://slappinglass.substack.com/p/pnr-defense-canceling-screens). The Heat 2020 Finals example on that page illustrates the quick show-and-recover and is filed under BS-5. D-I **unverified**.
- **Sources:** `[N9]`.
- **Confidence:** medium.

#### BS-7. Hard hedge: footwork, "scream and scare", MSU and college attribution — RICHER (extends F3.2 "Hard hedge")
- **Name and aliases:** hard hedge; hard show; hedge-and-recover; "scream and scare" (Travis Ford).
- **Family / sub-family:** F3.2 Show family.
- **Start alignment:** screener at (7.34, 84°); X-big **≤ 0.5 m** behind the screener on the rim side at t₀ (bottom foot between the screener's feet); handler at (7.6, 92°); tagger (opposite post) at about (1.5, 150°).
- **Roles / rules** `[N4]`: the screener's defender gets parallel to the sideline behind the screener, keeps contact, puts his bottom (baseline-side) foot between the screener's feet so there is no gap to split, then slides aggressively high as the handler comes off to force a retreat toward half-court. Calls: "Screen left/right!" then "Ball, ball, ball!". X-ball fights over low near the screener's hips, goes under the hedger and calls "Back, back, back!". The hedger sprints back with high hands; the lowest off-ball defender (often the opposite post) tags the roller. Generic: X-big takes 1–2 slides with the handler, then sprints back; the weak-side tag covers the screener temporarily `[N9]`.
- **Ordered actions with timing [HEURISTIC]:** (1) t₀ − 0.5 s: call, X-big makes contact; (2) t₀: X-big slides high 1–2 steps (λ ≤ −0.6 m); (3) t₀ + 0.5 to 1.5 s: handler retreats, X-ball goes under the hedger and re-attaches; (4) "Back" call, X-big sprints ≥ 4 m/s to the roller; (5) low-man tag between t₀ + 0.5 and 1.8 s.
- **Usual counters:** split if there is a gap; short-roll pocket pass; punishing the help; pick-and-pop (longer recovery) `[N4]`.
- **Detection signature [HEURISTIC]:** add to the existing hard-hedge row: (a) **pre-contact gap** X-big–screener ≤ 0.5 m at t₀ − 0.2 s; > 1.0 m → split-risk flag; (b) **X-ball under the hedger**: at t₀ + 0.3–1.0 s X-ball passes on the rim side of X-big while staying on the handler side of the screener; (c) **retreat**: handler r increases ≥ 1.0 m, or velocity points away from the rim, for ≥ 0.4 s; (d) `TAG` by the weak-side defender with minimum y.
- **Teams documented (MSU first):**
  - Michigan State 2014-15 (vs Indiana, published 7 Jan 2015): main coverage was hedging perimeter ball screens and recovering to keep Indiana out of the paint; Schilling hedged, Nairn recovered; weak-side help came across the lane to strip a short-corner catch — https://www.insidethehall.com/2015/01/07/film-session-michigan-state/ `[N14]`.
  - Michigan State through 2018-19: bigs usually flat or hard hedge; weak-side rotations cover the roller, then the bigs retreat — https://umhoops.com/?p=102796 `[N13]` (= S69 re-opened; re-confirmation of the older S69 flat/hard-hedge rows, not new evidence).
  - Virginia (Tony Bennett) said to hard hedge every ball screen and led the ACC in steals per game (season not given); Saint Louis (Travis Ford coined "scream and scare") — https://www.hooperuniversity.com/breakdowns/ball-screen-defense-hard-hedging-ball-screens `[N4]`.
- **Sources:** `[N4][N9][N13][N14]`.
- **Confidence:** high for MSU 2014-15, MSU through 2018-19 and the footwork; medium for Virginia "every ball screen" (one secondary source; see Corrections C-7).

#### BS-8. Hedge-and-plug — NEW (F3.2)
- **Name and aliases:** hedge and plug; hedge-plug.
- **Family / sub-family:** F3.2 Show family, new sub-family **hedge with POA roll-plug**.
- **Start alignment:** as BS-7.
- **Roles / rules** `[N18]` (podcast show notes; European/ACB context, secondary): pressure the ball without fully committing two defenders, protect the short roll and stay compact behind the play. The **on-ball defender disengages from the handler to plug the roll** while the big hedges. Key vulnerability: the on-ball defender's micro closeout after plugging.
- **Ordered actions with timing [HEURISTIC]:** (1) t₀: X-big hedges high; (2) t₀ + 0.2–0.8 s: X-ball releases the handler into the roll lane (between roller and rim, or the short-roll spot at r ≈ 4.0–5.5 m); (3) t₀ + 0.8–1.8 s: X-big recovers toward the roller/screener while X-ball micro-closes back to the handler or the nearest perimeter man.
- **Usual counters:** reject the hedge; Gortat screen on the recovering big; flip/hook the screen angle; "stick" the plug defender; boomerang re-screens that turn the hedge into a drop or switch `[N18]`.
- **Detection signature [HEURISTIC]:** hard-hedge geometry (λ_Xbig ≤ −0.6 m) **plus** X-ball's distance to the handler rising to ≥ 2.0 m by t₀ + 0.8 s while X-ball comes within ≤ 1.5 m of the roller's path; no off-ball tag (X-ball took the tag role); then an X-ball `RECOVER` (A0) of ≥ 2.0 m back to the handler or a perimeter man within 2.0 s (`CLOSEOUT` would need ≥ 2.5 m and would miss short recoveries). Matchups return (not a switch).
- **Teams documented:** none named (European, secondary) — https://www.buzzsprout.com/1288787/episodes/19494515-hedge-plug-solutions-learning-frameworks-and-european-film-sg-deep-dive `[N18]`. D-I **unverified**.
- **Sources:** `[N18]`.
- **Confidence:** medium for the definition (show notes only); low for prevalence.

#### BS-9. Drop depth bands; high drop as "level/aggressive drop"; D-I attribution — RICHER (extends F3.1 Deep / High drop)
- **Name and aliases:** drop; deep/low drop; high drop; level drop; aggressive drop; "KalkDrop" (Creighton).
- **Family / sub-family:** F3.1 Containment.
- **Start alignment:** screener at (7.34, 84°); standard-drop X-big 1.8–3.0 m below the screen at about (5.0, 85°); X-ball over the top on the handler at (7.0, 92°).
- **Roles / rules:** FIBA: the screener's defender is a few steps below the screen and backpedals `[N34]`. HooperU: the drop defender sits **1.83–3.05 m** below the level of the screen (converted from the source's feet); X-ball chases over the top and funnels the handler to the drop; off-ball help is minimal against shooters `[N3]`. Eurohoops: drop keeps the rim at the big's back and never lets the roller get behind `[N2]`; level/aggressive drop sits much higher with the low man tagging `[N2]`. Creighton's "predetermined drop level" is left vague `[N25]`.
- **Ordered actions with timing [HEURISTIC]:** (1) t₀: X-big at band depth; (2) t₀ to t₀ + 2 s: X-big backpedals with the roller behind him; (3) X-ball re-attaches from behind by t₀ + 1.0–1.5 s.
- **Usual counters:** reject the screen; mid-range handler; pick-and-pop; offensive rebounds `[N3]`.
- **Detection signature [HEURISTIC]:** depth bands at t₀ + 0.3 s (replacing the earlier "deep drop ≥ 3.5 m" as the only drop threshold; see Corrections C-3): **high/level drop 0.6–1.83 m; standard drop 1.83–3.05 m (sourced band `[N3]`, exact conversion of the source's feet); deep drop > 3.05 m or X-big at r ≤ 4.5 m**. Flat hedge = depth 0–0.6 m **and** lateral offset into the handler's path ≥ 0.5 m `[N34]` (old F3.1); up to touch = \|λ\| ≤ 0.6 m **and** dist(X-big, screener) ≤ 1.0 m (BS-4). The lateral-offset and screener-distance tests separate the two, whose depth bands overlap. "No man behind": roller-to-rim distance > X-big-to-rim distance on ≥ 90% of frames in [t₀, t₀ + 2 s]. X-ball path = over in ≥ 80% of the team's drop screens (guards fight over `[N3][N44]`). Team-level confirmatory outcome: high mid-range share allowed.
- **Teams documented (MSU first):**
  - Michigan State: no opened source shows drop as an MSU base — **unverified**.
  - Purdue 2022-23: main coverage put Edey and Trey Kaufman-Renn in a deep drop, guards over; opponents' far-2 share 38.1% (2nd highest) and close-2 rate 25.4% (2nd lowest), per Torvik, via https://thehoosiernetwork.com/article/2023/02/iubb-purdue-film-preview `[N44]` (3 Feb 2023).
  - Creighton 2023-24 (Kalkbrenner): drop; 3PA rate allowed 26% (2nd), rim-and-3 rate allowed 67% (1st), FT rate 13.1% (1st), opponent mid-range 41% FG and 0.83 PPP — https://www.actionnetwork.com/ncaab/college-basketball-film-breakdown-deep-dive-into-creighton-ryan-kalkbrenner `[N25]` (30 Dec 2023).
  - USC: drop (photo caption, season not given) — https://www.hooperuniversity.com/breakdowns/ball-screen-defense-playing-drop-coverage `[N3]`.
- **Sources:** `[N2][N3][N25][N34][N44]`.
- **Confidence:** high for Purdue 2022-23 and Creighton 2023-24; depth bands partly sourced (1.83–3.05 m), otherwise heuristic.

#### BS-10. Drop "load" (gap load) — NEW (help structure attached to F3.1 drop; F7.3)
- **Name and aliases:** drop load; gap load; gap-defender slide. Label `drop_gap_load`, distinct from F7.5 `load_to_ball` (all five to the ball side with the ball in the corner) and from T-4 `transition_wall_load`.
- **Family / sub-family:** F3.1 Containment + F7.3 Help actions.
- **Start alignment:** handler at the top (7.6, 90°), screen point (7.34, 84°); X-big at 1.8–3.0 m depth, about (5.0, 85°); gap defender of the right-wing man (7.3, 35°) at about (5.8, 50°).
- **Roles / rules** `[N2]`: in drop, a wing defender sits in the gap between his man and the handler; when the handler comes around the screen, he slides into the driving lane, then recovers. Risk: the wing shooter is open on a slow recovery.
- **Ordered actions with timing [HEURISTIC]:** (1) t₀; (2) t₀ + 0.3–0.8 s: handler turns the corner, gap defender slides 1.0–2.0 m toward the drive line; (3) t₀ + 1.0–2.0 s: gap defender closes out to his man on a kick-out or retreat.
- **Usual counters:** drive and kick to the loaded defender's man; pick-and-pop [CONVENTION].
- **Detection signature [HEURISTIC]:** drop signature (X-big depth ≥ 1.8 m, no trap) plus one strong-side off-ball defender entering the handler's drive corridor (1.5 m wide, handler to rim) between t₀ and t₀ + 1.2 s and coming within ≤ 2.0 m of the handler, then returning ≥ 1.0 m toward his own man within 1.5 s; no matchup change (unlike Next or peel).
- **Teams documented:** generic (European/NBA article, secondary) — https://www.eurohoops.net/en/trademarks/1409927/basketball-101-pick-and-roll-defense/3 `[N2]`. D-I **unverified**.
- **Sources:** `[N2]`.
- **Confidence:** medium.

#### BS-11. Ice-and-switch — NEW (F3.5)
- **Name and aliases:** ice and switch; ice-switch.
- **Family / sub-family:** F3.5 Directional, new sub-family **ice → exchange**.
- **Start alignment** (side PnR): handler at the right wing (7.3, 35°), screener at (7.56, 52.5°); X-ball on the handler's top/screen side at about (6.9, 42°); X-big below the screen toward the baseline at about (5.2, 30°).
- **Roles / rules:** the handler is iced, then the two defenders switch as the handler dribbles down toward the sideline/baseline, preventing the pass back to the screener; Texas Tech credited with popularising it in college `[N28]` (Tony Miller, 30 May 2021). Base ice footwork: X-ball on the high side forces baseline; the screener's defender stays between ball and basket and never lets the screener behind him; the screener's defender calls "Ice, ice, ice!" and X-ball points the direction; off-ball defenders shrink; weakness = middle penetration `[N27]`. FIBA aliases "Fan", "Push down"; on side PnR the handler is pushed baseline `[N34]`.
- **Ordered actions with timing [HEURISTIC]:** (1) t₀ − 1.0 to t₀: ice positioning; (2) t₀ to t₀ + 1.0 s: reject/dribble toward the baseline, X-big meets the handler; (3) t₀ + 0.6–1.5 s: X-big **stays** on the handler and X-ball takes the screener (persistent swap).
- **Usual counters:** pick-and-pop before the switch; screener posts the small defender; middle drive when the ice fails `[N27][N28]`.
- **Detection signature [HEURISTIC]:** existing ice pre-t₀ signature (X-ball between handler and P_s on the screen side ≥ 0.5 s; handler \|x\| increasing or v_y < 0) **followed by** `SWITCH(X-ball, X-big)` starting in [t₀ + 0.4, t₀ + 1.8 s] and persisting ≥ 2 s; the roller/popper's nearest defender is the former X-ball within 2.0 m by t₀ + 1.5 s (no open pass back).
- **Teams documented:** Texas Tech (era not specified; credited with popularising) — https://aquicktimeout.substack.com/p/2-ball-screen-coverage-adjustments `[N28]`. MSU **unverified**.
- **Sources:** `[N27][N28][N34]`.
- **Confidence:** medium.

#### BS-12. Switch-and-attack — NEW (F3.4 variant)
- **Name and aliases:** switch and attack; aggressive switch.
- **Family / sub-family:** F3.4 Exchange, sub-family switch (aggressive).
- **Start alignment:** high PnR reference; X-big up to touch at (6.9, 84°).
- **Roles / rules** `[N28]`: a straight switch in which the defender switching onto the handler attacks the handler's outside hand instead of waiting, for a poke-away chance and to stop a quick attempt. Zion Williamson at Duke (2018-19) cited as a strong practitioner.
- **Ordered actions with timing [HEURISTIC]:** (1) swap at t₀ to t₀ + 0.5 s; (2) new ball defender closes ≥ 0.7 m within 0.5 s of the swap.
- **Usual counters:** quick reject or split before the new defender arrives; roller seals the switched guard [CONVENTION].
- **Detection signature [HEURISTIC]:** `SWITCH`, then the new ball defender closes from ≥ 1.5 m to ≤ 0.8 m within 0.5 s of the swap at ≥ 3 m/s. Passive switch: new defender distance ≥ 1.2 m held ≥ 1 s.
- **Teams documented:** Duke 2018-19 (Williamson cited) — https://aquicktimeout.substack.com/p/2-ball-screen-coverage-adjustments `[N28]`.
- **Sources:** `[N28]`.
- **Confidence:** medium (preview text only).

#### BS-13. Switch & Shrink (late-clock switch + packed shell) — NEW (F3.4 / F1.1 hybrid; European secondary)
- **Name and aliases:** Switch & Shrink; switch-and-shrink.
- **Family / sub-family:** F3.4 Exchange with an F1.1 pack-line shell; F11.5 coverage switching by shot clock.
- **Start alignment** (after a switch on a right-slot PnR): guard fronting the roller at about (2.5, 60°); shrink defenders at about (2.0, 24°) and (2.0, 156°); elbow-gap defender at the left elbow (4.57, 113.6°).
- **Roles / rules** `[N17]` (FC Barcelona, Jasikevičius, 2020-21 (season inferred from "first season at the helm", article 30 May 2021); late-possession PnR defence): switch, with the guard who switched onto the roller fronting with active hands; two defenders shrink toward the blocks; the opposite perimeter defender sits in the elbow gap; the bottom-block defender keeps a tight backline; the elbow helper stunts and may double late in the clock (**shot clock < 5 s**); the post double comes on the flight of the ball; on a skip everyone moves "on a string" to the next gap; in the outer third keep the ball on that side and load the backside.
- **Ordered actions with timing:** (1) switch at t₀ to t₀ + 1.0 s; (2) shrink formed by t₀ + 2.0 s [HEURISTIC]; (3) late double only with shot clock < 5 s `[N17]`.
- **Usual counters:** flare and flare-slip; hi-lo with a flare; bigs at the dunker spots with guards on the wings and corners (Zenit); shooting over the top `[N17]`.
- **Detection signature [HEURISTIC]:** a ball-screen `SWITCH` with shot clock ≤ 10 s plus, within 1 s: (a) the switched guard on the ball side of the roller within 0.6 m (front); (b) ≥ 2 off-ball defenders within 1.5 m of the blocks (2.0, 24°)/(2.0, 156°); (c) one defender within 1.2 m of the weak-side elbow; (d) `TRAP` only when the shot clock is < 5 s.
- **Teams documented:** FC Barcelona 2020-21 (season inferred from "first season at the helm"; EuroLeague; secondary, not NCAA) — https://slappinglass.substack.com/p/switch-and-shrink-barcelonas-unique `[N17]`. NCAA usage **unverified**.
- **Sources:** `[N17]`.
- **Confidence:** high for the description; NCAA usage **unverified**.

#### BS-14. Scram (kick-out) switch: perimeter and swing-pass timing — RICHER (extends F7.4 "Scram switch" and F3.4 "Triple switch / scram")
- **Name and aliases:** scram switch; kickout switch; scramming. Labels: the pass-triggered two-way swap (old F7.4 and this item) = `scram_2way`; the F3.4 "triple switch / scram" 3-cycle permutation within 3 s = `scram_3cycle`. The only new content here is the perimeter / swing-pass trigger window; the post-entry detection repeats F7.4.
- **Family / sub-family:** F3.4 Exchange / F7.4 Rotations, sub-family **mismatch repair**.
- **Start alignment:** after a switched PnR: guard X1 on big 5 at the left block (2.0, 156°); X5 on guard 1 at the left wing (7.3, 145°) or near the nail (4.19, 90°).
- **Roles / rules:** existing file has the post-entry version (re-confirmed `[N6]` = D19 re-opened). New: the best time to scram is **on a pass while the ball is in the air**, including a **swing pass that sets up a post entry**. Example: Boston, Game 1 of the 2020 first round vs Philadelphia — after a swing to the corner, Theis switched with Tatum so the best post defender ended on Embiid. Needs constant communication. 2016-17 Warriors (Draymond Green) and the 2020 Rockets' small-ball defence named as heavy users `[N5]` (NBA only, secondary).
- **Ordered actions with timing [HEURISTIC]:** (1) mismatch exists at t_m (guard on big within 1.5 m of the block); (2) during the swing or entry flight (0.3–0.8 s) the nearest big-sized defender sprints to the post and the guard leaves for the perimeter; (3) new matchups persist by catch + 0.3 s.
- **Usual counters:** throw the entry early, before the scram; pass to the scrammer's vacated man [CONVENTION].
- **Detection signature [HEURISTIC]:** `SWITCH` triggered by a `PASS` in flight (not a `SCREEN`) when the pre-switch matchup was a size mismatch (roster height/position), and the new matchup reduces it; starts after release and completes ≤ 0.5 s after the catch. Perimeter variant: receiver at r > 5 m, but the pass sets up a post entry within 3 s.
- **Teams documented:** NBA (secondary): Celtics 2020, Warriors 2016-17, Rockets 2020 — https://mediumlights.substack.com/p/scram-switching `[N5]`. D-I **unverified**; MSU **unverified**.
- **Sources:** `[N5][N6]`.
- **Confidence:** high for definition and timing; low for college usage.

#### BS-15. Peel switch: named variants and D-I attribution — RICHER (extends F3.4 / F7.4 "Peel switch")
- **Name and aliases:** peel switch; peel; corner peel; post peel; nail peel; PnR peel.
- **Family / sub-family:** F3.4 Exchange / F7.4 Rotations.
- **Start alignment** (corner peel, drive from the right wing (7.3, 35°)): corner defender at about (6.0, 10°); beaten on-ball defender trailing at (6.5, 40°); post defender at about (2.4, 38°).
- **Roles / rules:** FIBA: a help defender switches onto the handler and the original defender peels off to the man left open `[N34]`. Variants (Slappin' Glass, 24 Jan 2021; Will Voigt) `[N7]`: **corner peel** (45° drive: same-side corner defender takes the ball, beaten defender peels to the corner); **post peel** (45° or middle drive: post defender steps up, beaten guard peels inside the big); **top-drive corner peel** and a two-peel rotation from the nearest guard; **PnR peel (top)** (on-ball defender peels behind to the shake/lift man, low help/tag takes the handler, screener's big chokes or jams the roller); **PnR peel (empty corner)** (nail defender takes the handler). An early corner peel gives up the corner three `[N7]`. NCAA: Florida Atlantic (Dusty May, 2022-23 (inferred from "this past season", article 13 Sep 2023)) used the peel as a protection plan when a defender gambled or was beaten in the backcourt; the nearest logical defender rotates chest-first to the handler and the beaten defender peels behind the ball (e.g. the centre picks up a baseline driver and the beaten guard peels to the big) `[N45]`.
- **Ordered actions with timing [HEURISTIC]:** (1) blow-by at t_b (F2 "beaten"); (2) t_b + 0.2–0.6 s: peeler steps into the drive line chest-first; (3) t_b + 0.3–1.0 s: beaten defender re-routes behind the ball to the peeler's man; (4) matchups persist ≥ 1.5 s.
- **Usual counters:** kick to the corner before the peel completes; re-screen on the new matchup `[N7]`.
- **Detection signature [HEURISTIC]:** after a blow-by the helper becomes the HMM ball matchup within 0.8 s, and the beaten defender's next matchup is the helper's former man within 1.5 s (reciprocal swap); the beaten defender's path passes **behind** the ball (larger r than the handler) and stays ≥ 1.5 m from the handler. Sub-labels by the peeler's pre-drive role: corner peel (peeler's man at θ ≤ 12° or ≥ 168°), post peel (peeler's man at r ≤ 3 m), nail peel (peeler within 1.2 m of (4.19, 90°)).
- **Teams documented (MSU first):** MSU — no evidence (**unverified**). Florida Atlantic 2022-23 (inferred from "this past season", article 13 Sep 2023) — https://backyardbuckets.substack.com/p/florida-atlantics-switching-defensive `[N45]`. Will Voigt (Angola national team; Telekom Bonn; secondary) — https://slappinglass.substack.com/p/the-peel-switch-a-primer `[N7]`.
- **Sources:** `[N7][N34][N45]`.
- **Confidence:** high for definition and variants; medium for the FAU attribution (single analyst blog).

#### BS-16. "Catch" drop and "No screen" — status notes (no new item)
- **"Catch" drop** (listed in the F3 hierarchy above): searched three ways; no opened source defines "catch" as a ball-screen coverage — not FIBA `[N34]`, not Eurohoops `[N2]`, not LMH `[N36]`. **Unverified**; no detection rule until a source or film definition exists (Corrections C-5).
- **"No screen"**: no opened source defines it as a coverage. The sourced equivalents are ice/fan/push down (force a reject) `[N34][N27]` and top-lock for off-ball screens (F5). Treat as an alias of ice on side screens and of top denial before a screen is set. **Unverified**.
- **Hedge-to-switch / blitz-to-switch / Next:** FIBA definitions re-verified `[N34]`; the Filios article only says Next is a jump-switch type coverage combining hedge, switch and drop, used in Europe, with no roles `[N8]`. Nothing to add beyond F3.2–F3.3.

---

### A3. Handoff (DHO) coverages (extends F4)

#### H-1. MSU DHO switching "two ways by position" — RICHER (extends F4 "Switch" and F1.6 "Positioning")
- **Name and aliases:** Three-Man DHO Switching (MSU drill).
- **Family / sub-family:** F4 DHO, sub-family Switch (position-conditional).
- **Start alignment** [HEURISTIC]: giver (big or guard) at the right slot (7.47, 70°) with the ball; receiver at the right wing (7.3, 35°) running toward the giver; d_giver at (6.6, 72°); d_receiver at (6.4, 38°); third defender (help) at the nail (4.19, 90°).
- **Roles / rules:** MSU's 2015 open-practice video lists a Three Man DHO Switching drill that teaches **two ways to defend handoffs depending on which positions are involved** `[N40]` (= S6 re-opened). The two coverages are not described in the listing: content **unverified**. Most likely pairing is switch vs a non-switch coverage when a big is the giver, but that is unconfirmed.
- **Ordered actions with timing [HEURISTIC]:** handoff at t_h; switch (if used) completes within 0.8 s (existing F4 Switch signature).
- **Usual counters:** keep and turn the corner; receiver back-cut; giver slip (existing F4 `[D28]`).
- **Detection signature [HEURISTIC]:** for MSU DHOs, switch rate conditional on giver role (guard vs big, roster position). Expect a bimodal policy — switch rate ≥ 0.7 for guard–guard/wing exchanges and lower for big-giver exchanges — *if* the two ways are switch vs non-switch.
- **Teams documented:** Michigan State, 2015 practice video — https://www.mensbasketballhoopscoop.com/?p=23659 `[N40]`.
- **Sources:** `[N40]`.
- **Confidence:** high that position-dependent DHO rules exist; the rules' content **unverified**.

*(Checked, nothing new: DHO "hedge and bounce" — the Grantz DHO page had no coverage content `[N21]`; the hedge-and-bounce drill page was not opened.)*

---

### A4. Off-ball screen coverages (extends F5)

#### OB-1. Point switching (off-ball pre-screen release) — NEW (F5 switch variant)
- **Name and aliases:** point switch; point-and-release.
- **Family / sub-family:** F5 Off-ball screen coverages, sub-family switch (pre-screen release).
- **Start alignment** (baseline exchange): cutter starts at the left corner (6.86, 177°) and runs the baseline to the right corner; cutter's defender at about (5.8, 170°); low/receiving defender at about (2.0, 41°) on the right side.
- **Roles / rules** `[N45]`: the low defender points and takes the cutter through the lane; the original cutter's defender takes **two steps** with the cutter, hands him off, and fans back to the arc with a hand in the passing lane. Each defender releases **before the screen's point**, so both are square on the catch; removes curl, pop and fade reads and lets defenders be more aggressive with their hands; needs elite communication. Shown on back-cuts, baseline exchanges and staggers.
- **Ordered actions with timing [HEURISTIC]:** (1) cut starts, t = 0; original defender trails two steps (≈ 1.2–1.6 m, ≈ 0.5–0.8 s); (2) receiving defender picks up the cutter ≥ 0.3 s before the cutter's closest approach to the screener; (3) original defender fans out to the open man or the arc.
- **Usual counters:** screener slip (defenders already exchanged); screening the switcher; mismatch post-ups `[N45]`.
- **Detection signature [HEURISTIC]:** `SWITCH` between d_cut and d_scr (or the low man) that **completes before** the cutter's closest approach to the screener (matchup flip at t ≤ t_closest − 0.3 s vs ≥ t_closest for an ordinary switch); the original defender's path with the cutter ≤ 2.0 m before he turns away; no defender–screener contact (distance ≥ 0.7 m).
- **Teams documented (MSU first):** MSU **unverified**. Florida Atlantic 2022-23 (Dusty May; inferred from "this past season", article 13 Sep 2023) — https://backyardbuckets.substack.com/p/florida-atlantics-switching-defensive `[N45]`.
- **Sources:** `[N45]`.
- **Confidence:** medium.

#### OB-2. Back screen: automatic contact switch with "jump out", invert, error flags — RICHER (extends F5.2)
- **Name and aliases:** contact switch; jump out; step-in-front; invert (anticipate).
- **Family / sub-family:** F5.2 Back screens / UCLA.
- **Start alignment** (UCLA screen: 5 at the right elbow (4.57, 66.4°) screens for 1 at the right slot (7.47, 70°) after the pass to the wing): X5 at about (4.0, 70°), rim side of 5; X1 at about (6.6, 72°).
- **Roles / rules** `[N19][N35]`: the screener's defender warns the cutter's defender (back to the screen) and **jumps out into the cutter's path** to the basket; the cutter's defender steps around the screener into strong denial so the screener cannot roll; the ball defender pressures the passer into dribbling; the switch is automatic on contact. Invert before the screen when possible to keep bigs inside `[N19]`. Errors: chasing under (lob or layup); show-and-recover on back screens (screener fakes or slips); cheating over early (pop); recovering after cheating (back-cut) `[N19]`. Coach's Clipboard: back screens are switched; the screened defender steps in front and around for inside position on the screener and switches back at the first chance, often the next perimeter pass `[N35]`.
- **Ordered actions with timing [HEURISTIC]:** (1) t₀ − 0.8 s: "Back screen!"; (2) t₀ − 0.3 to t₀: X5 steps into the cutter's lane; (3) t₀ to t₀ + 0.5 s: swap, X1 steps around to the ball side; (4) switch-back on the next perimeter pass.
- **Usual counters:** screener slip; screener pop against a defender who cheats over; mismatch post-up `[N19]`.
- **Detection signature [HEURISTIC]:** (a) in [t₀ − 0.5, t₀], d_scr moves ≥ 0.6 m laterally into the cutter's predicted path (cutter heading to the rim) and ends between cutter and rim; (b) `SWITCH` by t₀ + 0.5 s; (c) the new screener defender ends on the **ball side** of the screener within 1.0 m; (d) error flags: d_cut passes on the rim side of the screener with no switch (chase-under → lob risk); d_scr leaves the screener ≥ 1.0 m and returns without a swap (show-and-recover on a back screen); (e) **invert**: `SWITCH` before t₀ − 0.5 s when the cutter is a big.
- **Teams documented:** generic coaching — https://hooptactics.net/premium/defense/disruptivepressure/defscreensoff4back.php `[N19]`; https://coachesclipboard.net/basketball-defending-screens.html `[N35]`. MSU **unverified**.
- **Sources:** `[N19][N35]`.
- **Confidence:** high for the technique.

#### OB-3. Down screens "switch equals, open up on mismatches" (Fraschilla) and step-under timing — RICHER (extends F5.1 and F5.4)
- **Name and aliases:** switch equals; open up / let him through; step under (inside screens).
- **Family / sub-family:** F5.1 Down screens / F5.4 Cross and post screens.
- **Start alignment** [HEURISTIC]: down screen — screener from the right elbow (4.57, 66.4°) down to the right block (2.0, 24°); cutter's defender at about (2.3, 30°); screener's defender at about (3.2, 55°).
- **Roles / rules** `[N35][N6]`: default on down screens is chase, no switch. Fraschilla: switch **equals** (guard–guard, post–post); do not switch post-on-guard mismatches — the screener's defender opens up so the screened defender slides through. Inside post screens: the screened defender always steps under (toward the baseline) before the screen arrives; low cut = step under and stay (arm bar), high cut = step under and switch. Weak-side wing lateral screens: step under a step or two before the screen, then switch. Step under before contact, not after `[N35]`.
- **Ordered actions with timing [HEURISTIC]:** (1) step under in [t₀ − 0.8, t₀ − 0.1]; (2) low/high-cut branch at t₀ + 0.5 s.
- **Usual counters:** curl against a late step-under; mismatch seal after an equal switch [CONVENTION].
- **Detection signature [HEURISTIC]:** **switch-equals policy**: off-ball `SWITCH` probability conditioned on position difference cutter vs screener ≥ 0.6 for equals, ≤ 0.1 for mismatches. **Open-up**: on non-switched mismatch screens d_scr moves ≥ 0.5 m away from the screener in [t₀ − 0.5, t₀] and d_cut passes between them. **Step under**: d_cut's y decreases ≥ 0.4 m in [t₀ − 0.8, t₀ − 0.1] on inside screens; branch decided by the cutter's y at t₀ + 0.5 s (below or above the screener).
- **Teams documented:** Fran Fraschilla's approach as named by Coach's Clipboard (program and season not given → **unverified**) — https://coachesclipboard.net/basketball-defending-screens.html `[N35]`; switching rules re-confirmed — https://www.coachesclipboard.net/basketball-switching-defense.html `[N6]`.
- **Sources:** `[N35][N6]`.
- **Confidence:** medium.

*(Not added, unverified: hip-pocket trail with the screener's defender bumping the shooter out of the curl — Breakthrough page returned 403, overlaps F5 Chase + Bump. FIBA three-defender stagger rule — WABC page did not resolve. Existing F5 rows stand.)*

---

### A5. Zones and match-up rules (extends F8)

#### Z-1. 3-2 zone (flat three-man top line) — NEW (split from the F8.2 "1-2-2 / 3-2" row)
- **Name and aliases:** 3-2 zone. FIBA lists 3-2 separately from 1-2-2 `[D10]`.
- **Family / sub-family:** F8.2 Odd-front zones, new sub-family **F8.2.a 3-2 (flat top line)**.
- **Start alignment (ball at the top)** [HEURISTIC template from `[DZ16][DZ17]`]: X3 top (4.60, 90°) at moderate pressure `[DZ16]`; X1/X2 wings near the FT line extended (6.30, 46.9°) / (6.30, 133.1°). `[DZ16]` also gives a high-pressure top at (7.30, 90°): with the wings left at the FT line extended that shape is a **1-2-2 (Z-2)** by the C-4 rule; it stays a 3-2 only if the wings move up with the top to within 1.0 m of its y (e.g. wings at about (8.0, 65.9°) / (8.0, 114.1°), y ≈ 7.3 m, \|x\| ≈ 3.27 m [HEURISTIC]); X4/X5 low posts (2.15, 27.8°) / (2.15, 152.2°).
- **Roles / rules:** the top defender (a long, mobile player, often the 3; Sharman White, Pace Academy HS, GA; secondary, non-college; article by Brian Williams) stays between ball and basket at all times; wings play the ball man-to-man when it is in 3-point range on their side; block defenders guard the low post and close out to the corner when the scouting report says shooter `[DZ17]`. Ball screens: generally switch `[DZ17]`.
- **Ordered actions with timing [HEURISTIC windows]:**
  1. Ball to the right wing: X1 closes out (arrive ≤ 1.0 s after the catch); X3 drops to the ball-side elbow (4.6, 66°); X5 fronts the ball-side post; X4 slides into the lane; X2 may sink against a basket cut `[DZ16]`.
  2. Ball to the corner: X5 closes out, no baseline; X1 drops into the wing–post gap (4.48, 38.7°); X4 slides to the ball-side post; X3 owns the high post; X2 watches the weak side `[DZ16]`. White's version: top drops to ball level to protect the baseline, weak-side block tucks under the rim, opposite wing at the nail `[DZ17]`.
  3. Reversal to the top: the nail defender guards the top until the original top recovers and bumps him back (temporary hand-off, typically < 2 s) `[DZ17]`.
  4. Low-post catch: X4 + X5 double with high hands, X1 digs `[DZ16]`.
  5. Optional corner trap: X1 + X5; X3 holds the high post, then jumps the wing pass (skip to the top is the danger if X3 commits early) `[DZ16]`.
  6. Sliding variation: on a corner pass X3 slides all the way to the ball-side low post (front high side), X4 plays the low side → automatic X3/X4 double on a post entry `[DZ16]`.
- **Usual counters:** dribble-drive teams; quick wing → corner → wing ball movement that tests every closeout `[DZ16]`; high post [CONVENTION].
- **Detection signature [HEURISTIC]:** at `SET_DEF` with the ball at r > 6.75 m, θ 80–100°: a flat line of three defenders within 1.0 m of the same y, at any height with 4.0 ≤ y ≤ 7.5 m, outer two ≥ 7 m apart in x, plus two at r < 2.8 m with θ < 45° and θ > 135°. Versus 1-2-2: there the top defender is ≥ 1.5 m higher (y) than the two wings; a top 1.0–1.5 m above the wings is ambiguous (report both posteriors). Corner pass: the low ball-side defender (r < 2.8 m) travels ≥ 3.5 m to the corner within 1.2 s while the ball-side top-line defender drops ≥ 1.5 m. Top-recovery: after a reversal to the top, the nail defender (r 3.8–4.6 m, θ 80–100°) moves up ≥ 1.5 m and returns within 2.5 s as the original top arrives (screenless exchange). F8.0 zone features apply.
- **Teams documented:** no D-I program with a primary 3-2 found. Iowa (McCaffery) reportedly showed 2-3 and 3-2 looks at Wisconsin — **unverified** (page returned 429; snippet only). MSU: none.
- **Sources:** `[DZ16][DZ17][D10]` — https://hoopstudent.com/3-2-zone-defense/ ; https://coachingtoolbox.net/teaching-the-3-2-zone-positioning-communication-rotations
- **Confidence:** medium for structure (two coaching sources agree); low for D-I usage.

#### Z-2. 1-2-2 half-court zone; Purdue "1-2-2 man-zone hybrid" — RICHER (extends F8.2 "1-2-2 / 3-2" and F8.3 "1-2-2 match-up")
- **Name and aliases:** 1-2-2 zone; Purdue: Painter avoids calling it a zone, reporters call it a man-zone hybrid most like a 1-2-2 `[DZ36]` or a 1-2-2 match-up zone `[DZ37]`. "Jug" alias **unverified**.
- **Family / sub-family:** F8.2 (base 1-2-2) and F8.3 (Purdue hybrid / match-up).
- **Start alignment** [HEURISTIC]: top X1 (7.30, 90°); second line (6.17, 63.0°) / (6.17, 117.0°); back line (2.50, 36.9°) / (2.50, 143.1°).
- **Roles / rules** `[DZ19]`: stronger low-post and corner coverage than a 1-3-1, more conservative, concedes more perimeter shots; the top defender may drop deep into the lane to deny; back-line players must guard the corners; the high post/elbow needs an explicit rule. Purdue 2023-24 vs Northwestern's Boo Buie: for parts of possessions two layers of two defenders with arms spread forced the ball out of Buie's hands and limited inside entries, Zach Edey protecting the rim `[DZ36]`. Purdue (2025-26 preview, 8 Oct 2025): primarily man, flexing into a 1-2-2 match-up zone to limit dynamic guards; opponents took 31.3% of shots at the rim (season not stated; most likely 2024-25, from the Oct 2025 preview) `[DZ37]`.
- **Ordered actions with timing [HEURISTIC, from `[DZ19][DZ36]`]:** (1) top meets the ball at r ≥ 7 m; (2) second-line pair shades the driving lanes, forcing a pass within ~2 s; (3) on the pass the nearest second-line defender closes out and the top drops toward the nail; (4) corner pass → back-line defender closes out; (5) corner trap available (top/wing + back line) `[DZ19]`.
- **Usual counters:** a dominant post working FT line → low post; high-post catches; slow back-line closeouts to the corner `[DZ19]`; reversal before the trap [CONVENTION].
- **Detection signature [HEURISTIC]:** 1-2-2 `SLOT_RESIDUAL` < 1.5 m with the ball at the top. **Purdue hybrid** (`hybrid_122_vs_star`): inside a possession otherwise labelled man (F ≥ 0.6), a window ≥ 3 s in which the star handler has **two** defenders within 3.5 m in front of him (both with y_d > y_ball − 1.0 m and \|x_d − x_ball\| ≤ 3.0 m) but neither within 1.0 m (no trap), while the two lowest defenders have r < 3.0 m. Expected trigger: the star brings the ball over half-court.
- **Teams documented:** Purdue (Painter) 2023-24 hybrid vs Northwestern — https://www.crackedsidewalks.com/2024/09/purdue-preview-2024-25.html `[DZ36]`; Purdue 2025-26 occasional 1-2-2 match-up — https://www.crackedsidewalks.com/2025/10/purdue-preview-2025-26.html `[DZ37]` (= S75 re-opened); Boston College 1-2-2 → man (existing `[D80]`).
- **Sources:** `[DZ19][DZ36][DZ37]`.
- **Confidence:** medium.

#### Z-3. 2-1-2 zone with slides and the "Buzz" extension — RICHER (extends F8.2 "2-1-2", which had no slides)
- **Name and aliases:** 2-1-2 zone (FIBA lists it `[D10]`); a 2-3 variant with the centre starting at the high post `[DZ18]`.
- **Family / sub-family:** **F8.1 Even-front zones** (two-guard front; see Corrections C-2 for the placement above).
- **Start alignment** [HEURISTIC from `[DZ18]`]: tops (6.39, 69.9°) / (6.39, 110.1°); middle (4.00, 90°); wings/low (3.10, 14.9°) / (3.10, 165.1°).
- **Roles / rules** `[DZ18]`: tops own the ball at or above the FT line extended and keep the high post hard to reach; wings own the ball below the FT line extended plus the weak-side post (lob protection); the middle owns the high post and paint and is a long, athletic shot-blocker who makes or breaks the defence.
- **Ordered actions with timing [`[DZ18]`; windows HEURISTIC]:**
  1. Ball at the top: tops pressure without fully committing; wings slide out and up to take a wing pass briefly; middle behind a high post.
  2. Ball to the wing: ball-side wing takes the ball until a top bumps him (bump within ~1.5 s), then slides toward the baseline; weak-side top drops to the FT line to deny the high post; middle fronts the block; weak-side wing at the rim.
  3. Ball to the corner: wing closes out (deny baseline); ball-side top drops to the elbow; middle fronts the block; weak-side top mid-paint watching skips; weak-side wing in the lane.
  4. High-post catch: middle plays 1-on-1; tops do **not** converge; wings first deny the blocks, then widen to shooters.
  5. Short corner: middle starts a trap that keeps the ball off the baseline, ball-side wing completes it; weak-side wing mid-paint; ball-side top cheats to the wing; weak-side top centre field.
  6. Skip from the wing: weak-side wing takes it until bumped; skip from the corner: opposite top takes it.
  7. Drives: middle stops the ball before the paint; wings force middle, never baseline.
- **"Buzz" pressure variation** `[DZ18]`: tops pick up near the volleyball line (≈ 3 m beyond the arc — conversion of "volleyball line" is [HEURISTIC], exact distance **unverified**) and sit in passing lanes; middle stays about 4.57 m from the rim (converted from the source's feet), in line with ball and basket.
- **Usual counters:** multiple perimeter shooters; overloads; lobs over smaller back players `[DZ18]`.
- **Detection signature [HEURISTIC]:** ball at the top: one defender at r 3.5–4.6 m with \|x\| < 1.0 m and two at r < 3.5 m with θ < 25° or > 155° (in a 2-3 the centre sits at r < 2.5 m). High-post catch: the two tops' distances to the catcher **do not** fall by more than 1.0 m in the next 1.0 s (no swarm; contrast the aggressive 2-3 swarm `[D63]`). Buzz: tops' first contact with the ball at r ≥ 9.0 m; middle at r ≈ 4.0–5.0 m within 0.8 m of the ball–rim line.
- **Teams documented:** none named. A 2-1-2 match-up variant (Hoop Student) seen in search results only — **unverified**. MSU: none.
- **Sources:** `[DZ18][D10]` — https://www.basketballforcoaches.com/2-1-2-zone-defense/
- **Confidence:** medium (one detailed coaching source).

#### Z-4. Point zone (Dean Smith, North Carolina) — NEW (F8.3)
- **Name and aliases:** point zone.
- **Family / sub-family:** F8.3 Match-up zones (one on-ball "point" defender plus paired zone coverage), new sub-family **F8.3.a point zone**.
- **Start alignment** [HEURISTIC from `[DZ57]`]: 2-3-like — tops (6.32, 66.7°) / (6.32, 113.3°); lows (3.42, 20.6°) / (3.42, 159.4°); X5 in the lane (1.50, 90°).
- **Roles / rules** `[DZ57]`: whoever takes the ball calls "point" and plays it man-to-man; perimeter defenders work in complementary pairs (if X1 has point, X4 covers the baseline); X5 protects the basket from the lane.
- **Ordered actions** `[DZ57]` (timing [HEURISTIC]): (1) ball at the top: X1 pressures, X3 lifts to the high post, X5 steps toward the FT line, X4 into the lane; (2) wing pass: X2 takes point (≤ 1.0 s after the catch), X1 drops to the ball-side elbow, X5 to the post, X4 short corner, X3 sinks weak side; (3) corner: X4 takes point, X2 drops between wing and low post; (4) every pass reassigns the point; others fill gaps; (5) stunts on middle penetration and baseline drives.
- **Usual counters:** **unverified** (not in the source); expected: skips that force a long point change [CONVENTION].
- **Detection signature [HEURISTIC]:** zone-like F (≤ 0.35) for 4 defenders but **one** defender within 1.2 m of the ball on every catch, with that identity changing on ≥ 70% of passes; the new point defender is the one whose template slot is nearest the receiver on ≥ 85% of passes. Pair check: when a perimeter defender takes point on a wing/corner catch, the paired defender's distance to the baseline band (y < 1.0 m) falls ≥ 1.0 m within 1.0 s.
- **Teams documented:** North Carolina under Dean Smith (season not given) — https://hoopstudent.com/point-zone-defense/ `[DZ57]`.
- **Sources:** `[DZ57]`.
- **Confidence:** low–medium (one source; UNC usage not dated).

#### Z-5. 2-3 match-up zone (rule set; Louisville, Oregon) — NEW (F8.3)
- **Name and aliases:** 2-3 match-up zone; "matchup 2-3" (Oregon base-defence label `[DZ05]`); Louisville "matchup zone" (Pitino) `[DZ60]`.
- **Family / sub-family:** F8.3, new sub-family **F8.3.b 2-3 match-up**.
- **Start alignment** [HEURISTIC]: standard 2-3 slots (tops (6.32, 66.7°)/(6.32, 113.3°); forwards (3.42, 20.6°)/(3.42, 159.4°); centre (1.50, 90°)), then the defence takes the shape of the offence `[DZ01]`.
- **Roles / rules** (TeamArete; a blend of Fred Litzenberger's Oregon 2-3 and Don Meyer's point-and-talk) `[DZ01]`: (1) point to your man and talk; (2) never two defenders on one attacker; (3) the defence takes the shape of the offence; (4) bigs in, smalls out; (5) the post defender leaves the paint only in emergencies (five out, or an elite shooter); (6) weak-side helpers straddle the weak-side lane line; (7) guards dig at the post; (8) switch to keep bigs in / smalls out, but **not** on the dribble; (9) pressure every shot; (10) guard only to the arc, protect paint and high post; (11) don't deny perimeter passes, pressure the ball; (12) box out, pursue, chin, outlet. Structural principle: two defenders guard three attackers, scaling to one-on-two, three-on-four, four-on-five `[DZ01]`. Oregon (Altman): on-ball man characteristics, off-ball help like a 2-3, frequent switches regardless of position `[DZ05]`; possessions often start with a press (usually 1-2-2) flowing into man or the match-up zone `[DZ03]` (see P-4).
- **Ordered actions with timing [HEURISTIC]:** (1) as the ball crosses half, each defender points to the attacker in or nearest his area (≤ 1.5 s); (2) on-ball defender closes to ≤ 1.2 m; (3) cutters crossing a boundary are passed off unless cutting toward the ball (Z-7 Huber rule); (4) on a post catch guards dig, then recover on the kick-out.
- **Usual counters:** driving into the lane (Boeheim on Louisville; snippet only — **unverified**); screening the zone; PG penetration into the middle (existing `[D76]`).
- **Detection signature [HEURISTIC]:** `SHAPE_MATCH` d̄_m ≤ 2.0 m (man-like) **and** cutter test = pass-off on ≥ 60% of lane cuts ≥ 6 m (zone-like); `ONE_ON_BALL` holds; ≤ 0.1 half-court `TRAP` per possession; "bigs in": the tallest defender at r < 3.0 m on ≥ 80% of frames even when his nearest attacker is at r > 6.75 m (rule 5); `SWITCH` at screens and boundary crossings but not within 1.0 s of a screenless dribble move (rule 8); weak-side helpers' \|x\| within 0.5 m of the lane line (\|x\| ≈ 1.83 m) when two passes away (rule 6; separates it from the Temple match-up).
- **Teams documented (MSU first):**
  - Used **against** MSU: Louisville 2011-12, NCAA Sweet 16 (22 Mar 2012) — the match-up zone held MSU (the tournament's best-shooting team) to 28% FG in a 57-44 win; guards pressured from the top and Gorgui Dieng blocked seven shots — https://www.bangordailynews.com/2012/03/22/sports/louisville-knocks-off-top-seeded-michigan-state/ `[DZ60]`. The description of it as a man defence that switches everything (NBC 2012) could not be opened — **unverified**.
  - Oregon (Altman): base listed as match-up 2-3 in 2021-22 — https://dailybruin.com/2022/01/13/scouting-report-ucla-mens-basketball-vs-oregon-oregon-state/ `[DZ05]`; press → match-up in 2019-20 — https://umhoops.com/2019/12/13/film-room-breaking-down-oregons-matchup-zone-defense/ `[DZ03]`; Oregon (Big Ten since 2024-25 `[DZ74]`) zone vs MSU on (inferred) 20 Jan 2026 worked for about 32 minutes before MSU pulled away, alignment not stated — https://spartanavenue.com/tom-izzo-kur-teng-can-t-guard-my-99-year-old-mother-01kfgk0xf6np `[DZ35]`. An Oregon assistant quote (MGoBlog 403) — **unverified**.
- **Sources:** `[DZ01][DZ03][DZ05][DZ35][DZ60][DZ74]` — rule set: https://id3430.securedata.net/teamarete/23matchupzone.html
- **Confidence:** medium (rules from a coaching site; usage from journalism).

#### Z-6. 1-3-1 match-up zone (10-rule version) — NEW (F8.3)
- **Name and aliases:** 1-3-1 match-up zone.
- **Family / sub-family:** F8.3, new sub-family **F8.3.c 1-3-1 match-up**.
- **Start alignment** [HEURISTIC]: top (7.00, 90°); wings (6.53, 40.0°) / (6.53, 140.0°); middle X5 (4.20, 90°); baseline (0.80, 90°).
- **Roles / rules** (Coach's Clipboard 10 rules) `[DZ42]`: (1) 1-3-1 set with X5 in the middle; (2) **X5 plays O5 man-to-man at all times**, the other four rotate around him; (3) if O5 steps out, X5 goes with him (sag if O5 can't shoot); (4) flash cuts to the high post/elbow are played man-to-man (X4 follows O4; X1 drops to face the wing, foot beside O4's to avoid being hooked); (5) against the dribble: stay with your man and switch zones, not men; (6) switch on screens (perimeter ball screen: X2 takes the ball, X1 steps under to the screener — zones kept, men change); (7–9) shallow ball-side, deep ball-side and weak-side cut rules: the three perimeter defenders rotate clockwise around X5 toward the ball, option to stay man with the cutter; (10) baseline cut on reversal: X4 stays with O4 to the corner. Versus a 2-1-2 set: X1 takes the guard to his right, X2 the other guard, X3 and X4 drop to the corners, X5 the middle — aim to force a two-guard look. Against heavy hi-low teams X4 and X5 may play man on O4 and O5 throughout `[DZ42]`.
- **Ordered actions with timing [HEURISTIC]:** (1) set by `SET_DEF` + 1.5 s; (2) perimeter rotation completes within 1.5 s of a ball-side cut; (3) screen switch within 0.8 s of t₀.
- **Usual counters:** high-to-low cuts and overloads that confuse the hand-offs `[DZ42][DZ43]`.
- **Detection signature [HEURISTIC]:** one defender (X5) with F ≥ 0.8 against the opponent's centre for the whole possession regardless of region (even at r > 6.75 m), while the other four show F ≤ 0.45 and σ_reg < 2.0 m relative to 1-3-1 slots; on a ball-side cut the three non-X5 perimeter defenders' angular positions about X5 all change with the same rotational sign within 1.5 s; `SWITCH` on ≥ 80% of perimeter ball screens. Versus box/diamond-and-1 chasers: the man-marked attacker is a post (r < 4 m on ≥ 60% of frames) and the marker is the centre.
- **Teams documented:** no D-I program named. Northwestern (Carmody) paired a match-up zone with its 1-3-1 (Z-8) but the opened articles do not say it followed these rules.
- **Sources:** `[DZ42][DZ43]` — https://coachesclipboard.net/MatchupZone131.html
- **Confidence:** medium.

#### Z-7. Match-up pick-up rules by offensive set; cutter hand-offs (Huber rule) — RICHER (extends F8.3 "Match-up zone (generic)")
- **Name and aliases:** match-up pick-up tables; Jim Huber cutter rule; "Match" call.
- **Family / sub-family:** F8.3.
- **Start alignment:** depends on the offence's front (tables below); default 2-1-2 match-up slots as Z-3.
- **Roles / rules** `[DZ43]`: ball defender closes out tight as in man; off-ball defenders play zone that resembles help-side man; pressure the ball, front the low post, deny lanes, help on penetration; switch freely so bigs stay low and guards stay out. Pick-up tables: 2-1-2 match-up vs a 1-3-1 offence (X1 point, X2 right wing, X3 out to the left wing; vs 3-out-2-in X5 drops to the block); one-guard-front match-ups vs 2-1-2 (1-3-1 version: X1 guard to his right, X2 other guard, X3/X4 corners, X5 middle; 1-2-2 version: X1/X2 guards, X3 own-side wing/corner, X4 opposite corner, X5 high post); vs 1-4 high (X2/X3 gap between wing and elbow post and deny the wing; back-cut → X4/X5 pick up, gap defender slides to the vacated post); vs 1-4 low (X2/X3 gap and deny; X4/X5 three-quarter front the low posts; X1 tight on the point). Cutters: away from the ball → X2 bumps, denies, then switches with X4 at the corner; toward the ball → stay man to the corner; alternate: X4 drops in and takes the cutter to the opposite corner. **Huber rule:** let cutters moving away from the ball go; play cutters moving toward the ball man-to-man until a hand-off. Simplified option: after the initial match-ups disrupt the set, everyone goes man `[DZ43]`. College of Idaho: never two on the ball; always bump the wings; "Match" call on a high-post catch `[DZ59]` (= D99 re-opened).
- **Ordered actions with timing [HEURISTIC]:** (1) pick-up complete by `SET_DEF` + 1.5 s; (2) cutter hand-off at the zone boundary within 1.0 s of the crossing.
- **Usual counters:** screening the zone; PG into the middle (existing `[D76]`).
- **Detection signature [HEURISTIC]:** **pick-up mirror test** at `SET_DEF` + 1.5 s: offensive front = number of attackers at r > 6.75 m with θ 60–120°; defensive front = defenders with y ≥ 5.0 m and 45° ≤ θ ≤ 135°, counted at the same moment; in a match-up zone the defensive front count equals the offensive front count at `SET_DEF` + 1.5 s on ≥ 85% of possessions (man pairs follow their men; fixed zones keep their own front). **Huber cutter asymmetry:** for cuts with velocity component toward the ball > 2.0 m/s the nearest defender follows ≥ 70% of the path; for cuts away ≤ 40%; asymmetry index = follow(toward) − follow(away) ≥ 0.3 → match-up zone; ≈ 0 for man (both high) or pure zone (both low).
- **Teams documented:** College of Idaho (NAIA; rules) — https://coachingidaho.substack.com/p/lets-talk-some-zone `[DZ59]`; tables generic — https://www.coachesclipboard.net/MatchUpZone.html `[DZ43]`. MSU: none.
- **Sources:** `[DZ43][DZ59]`.
- **Confidence:** medium.

#### Z-8. 1-3-1 Big Ten lineage (Northwestern/Carmody) and Oakland vs MSU — RICHER (extends F8.2 "1-3-1 (base)" and "1-3-1 trapping")
- **Name and aliases:** 1-3-1 zone (Carmody's "signature defense" at Northwestern) `[DZ07]`.
- **Family / sub-family:** F8.2 Odd-front, lineage label `odd_front_trap_131`.
- **Start alignment:** one top, three just outside the FT line, one baseline defender guarding the corner threes side to side `[DZ06]`. Template [HEURISTIC]: top (7.00, 90°); line of three (6.53, 40°) / (4.20, 90°) / (6.53, 140°); baseline (0.80, 90°), sliding to the corners at about (6.3, 4.5°) / (6.3, 175.5°).
- **Roles / rules:** the top (Jeremy Nash) pressured and trapped on the perimeter almost immediately after the ball crossed centre court, forcing skip passes that are easier to intercept; the baseline player (Craig Moore or Michael Thompson) ran side to side for the corners `[DZ06][DZ67]`. Unveiled vs Purdue (2008-09); NU used it extensively on the way to wins in five of its next six games; Purdue committed 22 turnovers; after Iowa found open corner threes (Iowa won 56-51) it became the backup to the match-up zone `[DZ06]`. Carmody calling it tiring and best used sparingly (NIT 2011) — snippet only, **unverified**.
- **Ordered actions with timing [HEURISTIC]:** (1) top meets the ball within ~2 s of it crossing half-court (y 11–13 m); (2) trap with a wing on the perimeter; (3) baseline defender sprints to the ball-side corner on a wing-to-corner pass (≥ 4.5 m in 1.5 s, or arrival within 1.5 m of the corner receiver by catch + 1.0 s).
- **Usual counters:** corner threes (Iowa 2009) `[DZ06]`; gap drives + kick to corners `[DZ56]`; gap and rim attacks for free throws (MSU 2025) `[DZ11]`.
- **Detection signature [HEURISTIC]:** existing 1-3-1 signature plus (a) **pick-up depth**: top's first contact (≤ 1.5 m) at y ≥ 11.0 m within 2.0 s of the ball crossing y = 12.73 m; (b) perimeter `TRAP` at r > 7.5 m, 35° < θ < 145°; (c) baseline lateral run \|Δx\| ≥ 8 m within 2.0 s after corner-to-corner ball movement.
- **Teams documented (MSU first):**
  - Oakland (Greg Kampe) vs MSU, 20 Dec 2025 (2025-26): 1-3-1; MSU won 79-70, 15-of-35 FG in the first half, better gap attacks and rim pressure after halftime (12-of-17 FT in the second half) — https://www.si.com/college/michiganstate/tom-izzo-drops-blunt-review-following-oakland-golden-grizzlie-game- `[DZ11]`. Oakland plays zone every possession except BLOBs, prefers 1-3-1 and 1-1-3, occasional 2-3/3-2 (2025-26, preview dated 12 Nov 2025) — https://gocoogs.com/?p=46293 `[DZ56]`.
  - Northwestern (Carmody) 2008-09 — https://dailynorthwestern.com/2009/03/03/archive-manual/mens-basketball-cats-season-lives-dies-by-the-zone/ `[DZ06]`; https://dailynorthwestern.com/2009/01/19/archive-manual/mens-basketball-wildcats-1-3-1-zone-tops-tubby `[DZ67]`; 2010-11 — https://dailynorthwestern.com/2010/11/18/sports/mens-basketball-zone-boosts-cats-defense/ `[DZ07]`.
  - Michigan (Beilein) and West Virginia (existing `[D32]`). West Virginia (Huggins) 1-3-1 from Beilein, 2009 and 2012 — **unverified** (WVU pages opened with empty bodies `[DZ72][DZ73]`).
- **Sources:** `[DZ06][DZ07][DZ11][DZ56][DZ67]`.
- **Confidence:** medium.

#### Z-9. Amoeba: origin and two-guard-front form — RICHER (extends F8.3 "Amoeba")
- **Name and aliases:** amoeba defense.
- **Family / sub-family:** F8.3.
- **Start alignment** [HEURISTIC]: diamond form — top (7.0, 90°); second (4.6, 90°); lane-line pair (3.81, 60.1°) / (3.81, 119.9°); rim (0.8, 90°). Two-guard-front form (a 2-1-2 with the rim defender moving up behind the high post) — tops (6.39, 69.9°) / (6.39, 110.1°); middle (3.0, 90°); lows (3.10, 14.9°) / (3.10, 165.1°).
- **Roles / rules** `[DZ61]`: two quickest at the top of the key and just above the FT line, biggest under the basket, two on opposite lane sides just below the elbows; versus a two-guard front it becomes a 2-1-2; a high-post catch draws a triple team. Origin: Fran Webster developed it as a Pittsburgh assistant and refined it in the 1970s with Charles Ridl and Tim Grgurich; Grgurich later joined Tarkanian at UNLV; Pitt used it in its 1973-74 run (22 straight wins, Elite Eight); Webster's 1984 book is cited `[DZ61]`. (Origin note → Corrections C-1.)
- **Ordered actions with timing [HEURISTIC]:** high-post catch → triple within 1.0 s; other slides as the existing amoeba row `[D60]`.
- **Usual counters:** shape-shifting by the offence's front (existing); quick kick-out from the high-post triple [CONVENTION].
- **Detection signature [HEURISTIC]:** add a **high-post triple** event: three defenders within 2.0 m of a high-post catcher (r 3.5–6.0 m, θ 60–120°) within 1.0 s of the catch. Gambling indicator: steals per 100 opponent possessions ≥ the 80th percentile of D-I, together with open layups when beaten (the source notes the gamble). Deflections are added only once a deflection event is defined (not a tracking primitive yet).
- **Teams documented:** Pittsburgh 1973-74; UNLV (Tarkanian); Ole Miss in combination with other defences (no season) — https://en.wikipedia.org/wiki/Amoeba_defense `[DZ61]`; existing `[D60]`.
- **Sources:** `[DZ61][D60]`.
- **Confidence:** medium.

#### Z-10. 2-3 zone used against MSU (2012–2026 log) and Ohio State's own 2-3 (2014-15) — RICHER (extends F8.1 teams, "MSU usage" row, F18.4)
- **Name and aliases:** 2-3 zone.
- **Family / sub-family:** F8.1.
- **Start alignment** [HEURISTIC]: standard 2-3 slots (tops (6.32, 66.7°)/(6.32, 113.3°); forwards just outside the blocks (3.42, 20.6°)/(3.42, 159.4°); centre (1.50, 90°)).
- **Roles / rules (re-confirmed):** two guards up, two forwards just outside the blocks, centre roaming the middle; one player on the ball, sprint on the pass, everyone rebounds his area; ball on the wing → deny the high post; high post "avoid at all costs" → centre on the ball, guards crowd, X3 denies the low post; corner-trap options `[DZ02]`. Matta (Ohio State): when the ball moves, all five shift together, connected like his man `[DZ34]`.
- **Ordered actions with timing:** as existing F8.1 rows.
- **Usual counters:** as existing F8.1; MSU's documented answers: gap attacks, rim pressure for free throws `[DZ11]`, second-half rim attacks (Iowa 2025 `[DZ12]`).
- **Teams documented (MSU first; opponents zoning MSU unless stated):**

  | Season | Opponent / event | What is documented | Source |
  |---|---|---|---|
  | 2025-26 | Oregon (Altman), 20 Jan 2026 (date inferred) | Zone-heavy plan worked ~32 minutes; MSU won by 16; Oregon scored 52 | https://spartanavenue.com/tom-izzo-kur-teng-can-t-guard-my-99-year-old-mother-01kfgk0xf6np `[DZ35]` |
  | 2025-26 | Oakland, 20 Dec 2025 | 1-3-1 (Z-8) | `[DZ11]` |
  | 2025-26 | Duke, 6 Dec 2025 | Zone in the final minutes; Izzo blamed his own zone offence | https://spartanavenue.com/tom-izzo-says-his-coaching-is-the-reason-michigan-state-isn-t-11-0-01kcs43bkpkj `[DZ10]` |
  | 2024-25 | Iowa, Mar 2025 | Zone effective in the first half (MSU 4-of-16 3P, 16 paint points, 2 FT trips); MSU won 91-84 after 61.3% second-half FG | https://www.si.com/college/michiganstate/basketball/spartans-iowa-hawkeyes-big-ten-jase-richardson-jaden-akins-jaxon-kohler `[DZ12]` |
  | 2024-25 | Indiana, 11 Feb 2025 | 2-3 after falling behind 20-8 in ~9 min; closed the half 12-2; MSU 38.2% FG, 4-of-23 3P; Ballo anchored, zone weaker when he sat with fouls | https://www.si.com/college/indiana/basketball/mike-woodson-s-inspired-switch-to-zone-defense-against-michigan-state-pays-off-for-indiana-01jkxd7dckhz `[DZ04]`; https://www.insidethehall.com/2025/02/12/iu-basketball-relies-on-zone-defense-total-team-effort-to-beat-no-11-michigan-state/ `[DZ08]` |
  | 2024-25 | Penn State, Jan 2025 | Season-high 28 zone possessions vs MSU; MSU 10-of-24 with 3 TOs vs the zone | https://nittanysportsnow.com/2025/01/penn-state-basketball-has-a-new-look-on-defense/ `[DZ40]` |
  | 2024-25 | Izzo response | Dared teams to zone MSU after the Indiana loss | https://spartanavenue.com/tom-izzo-dares-teams-to-play-zone-against-michigan-state-basketball-moving-forward-01jm2ywh2zcb `[DZ09]` |
  | 2017-18 | Syracuse (Boeheim), NCAA 2nd round | MSU 26% FG, school-record 37 3PA with 8 makes; scoreless final 5:41 | https://www.espn.com.au/mens-college-basketball/recap/_/gameId/401025873 `[DZ38]` |
  | 2011-12 | Louisville match-up zone | MSU 28% FG (Z-5) | `[DZ60]` |
  | 2014-15 | Ohio State's own 2-3 | Primary defence for most of the season (until 3 Jan 2015); full-time man vs Illinois from 3 Jan 2015 after a timeout when down 8 (~4 min left in the 1st half); 6-2 after; opponents 42% FG / 34% 3P over 8 games | https://www.elevenwarriors.com/ohio-state-basketball/2015/02/49530/ohio-state-looks-like-a-different-team-largely-due-to-its-defensive-switch `[DZ34]` |
  | 2011-12 | Syracuse's own 2-3 | All-zone on every possession after some early-season man `[DZ46]`; opponents' eFG 44.2 vs 52.7 the prior year; Fab Melo ~1 block per 8 min; asked whether he would leave the zone if an opponent got hot, Boeheim said no (hypothetical) `[DZ46]` | https://www.si.com/more-sports/2012/02/20/syracuse `[DZ46]` |

- **MSU own usage:** still the existing "90-some % man, 2-3 change-up" (2015) `[S74]`; no MSU 2-3 usage found in 2024-26 coverage — gap.
- **Detection signature additions [HEURISTIC]:** (a) **anchor dependency**: tag the 2-3 centre-slot occupant; when he is off the floor (lineup data) expect a rise in opponent rim attempts (Indiana/Ballo `[DZ08]`); (b) **zone onset after a deficit** — see SC-1.
- **Sources:** `[DZ02][DZ04][DZ08][DZ09][DZ10][DZ11][DZ12][DZ34][DZ35][DZ38][DZ40][DZ46][DZ60]`; structure https://www.thehoopsgeek.com/2-3-zone-defense-basketball `[DZ02]`.
- **Confidence:** high for events (game reports); medium for structure.

---

### A6. Presses (extends F9)

#### P-1. 2-1-2 full-court press — NEW (F9.2 listed the name only)
- **Name and aliases:** 2-1-2 press. Three-quarter-court variant (not full court): Cincinnati (Huggins) 1990s, "a lot of 2-1-2 pressure", usually three-quarter court, per Larry Harrison `[DZ25]`.
- **Family / sub-family:** F9.2 Zone presses.
- **Start alignment** [HEURISTIC from `[DZ24]`]: X1/X2 front line around the opponent's elbows (21.34, 85.1°) / (21.34, 94.9°); X3 middle, in front of the half-court circle on the backcourt side (14.56, 90°); X4/X5 back line in the defended half around the arc (6.88, 54.5°) / (6.88, 125.5°).
- **Roles / rules** `[DZ24]`: X1 (ball-side guard) pressures the inbounded ball, steers it up the sideline toward X3 and rides the hip; X2 (weak-side guard) drops toward the middle, takes reversals, replaces X3 when X3 traps; X3 (middle) keeps the middle covered and is the **first trapper** once the dribble goes up the sideline; X4 (ball-side deep) moves toward the sideline and up for sideline passes; X5 (weak-side deep) protects the rim and reads deep passes.
- **Ordered actions with timing [windows HEURISTIC]:**
  1. Inbound (t = 0): no defender on the inbounder; X1/X2 play behind-inside the receivers to push the catch to the sideline.
  2. 0–2 s: X1 pushes the dribble up the sideline; X2 drops to the middle; X3 inches ball-side; X4 out toward the sideline; X5 to the lane.
  3. First trap, as close to half-court as possible: X3 sprints perpendicular to the sideline (outside foot on or out of bounds), X1 on the hip, X2 middle, X4 up on the nearest sideline receiver, X5 at the rim. Expected ≈ 2–5 s after the inbound at \|x\| > 5.5 m, 11.5 < y < 16 m.
  4. Sideline pass out of the trap → second trap: X4 cuts off the sideline, X3 chases to complete; X1/X2 sprint back looking middle first, then basket; X5 stays in the lane.
  5. Fall-back: not fully specified; weak-side deep keeps dropping, X5 protects the rim `[DZ24]`.
- **Usual counters:** quick pass over X3 up the sideline (triggers trap 2); repeated reversals; deep passes behind the back line `[DZ24]` (the source author's inferences).
- **Detection signature [HEURISTIC]:** pre-inbound after a made basket: 2 defenders at y 19.5–23 m with \|x\| ≤ 3.0 m, 1 at y 13.5–16.5 m with \|x\| ≤ 2.0 m, 2 at y < 9 m, none within 2.5 m of the inbounder. First `TRAP` at \|x\| > 5.5 m, 11.5 < y < 16 m with one trapper from the middle slot (pre-trap \|x\| < 2.0 m within 1.5 s before). Middle denial: no completed pass to an attacker at \|x\| < 3.0 m, 13 < y < 20 m before the first trap on ≥ 80% of press possessions. Versus 2-2-1 `[D65]`: two mid defenders at y 13–15 m with \|x\| ≈ 3–5 m; the 2-1-2 has one middle defender and two **deep** defenders.
- **Teams documented:** generic — https://www.basketballforcoaches.com/2-1-2-press/ `[DZ24]`; Cincinnati (Huggins) 1990s, 2-1-2 pressure usually three-quarter court (a three-quarter-court variant, not this full-court template), per Larry Harrison — https://www.nbcsports.com/college-basketball/news/a-shift-in-philosophy-led-bob-huggins-to-build-press-virginia `[DZ25]`.
- **Sources:** `[DZ24][DZ25]`.
- **Confidence:** medium.

#### P-2. 1-2-2 three-quarter press converting to 1-3-1 / 2-3; the 1-1-2-1 — NEW variant (F9.2 + F11.3)
- **Name and aliases:** 1-2-2 three-quarter-court press; 1-1-2-1 (looks the same at first, more conservative) — Jay Wright (Villanova) clinic `[DZ44]`.
- **Family / sub-family:** F9.2 Zone presses; F11.3 press → half-court mapping.
- **Start alignment** [HEURISTIC]: X1 at the opponent's top of the arc (18.70, 90°); X2/X3 (16.14, 73.8°) / (16.14, 106.2°); X4 ball-side half line (12.18, 70.8°); X5 deep middle safety (5.50, 90°). 1-1-2-1: X2 behind X1 in the middle at (15.5, 90°).
- **Roles / rules** `[DZ44]`: "attack small, retreat big"; fake and real traps; keep the ball out of the middle; get players to the ball side; handle reversal, skip and back-row containment; do not give up an open three while converting; after conversion stay aggressive and tag assignments with man principles. The 1-1-2-1 pairs with a half-court 2-3; the 1-2-2 converts to either 1-3-1 or 2-3. The exact five rules are behind a paywall — **unverified**.
- **Ordered actions with timing [HEURISTIC]:** (1) X1 influences the dribble to a sideline by y ≈ 17–19 m; (2) wing + X1 trap or fake-trap near y 13–16 m; (3) on the ball crossing half-court or a middle pass: retreat — X1 becomes the 1-3-1 point (or a 2-3 top), X4 the baseline/back line, X5 the middle (1-3-1) or rim (2-3); conversion complete ≤ 3 s after the ball crosses y = 12.73 m.
- **Usual counters:** middle flash; skips; long diagonal over the back row [CONVENTION; partly `[D67]`].
- **Detection signature [HEURISTIC]:** press slots held ≥ 1 s before the inbound; `FAKE_TRAP` events (A0); conversion = the half-court classifier's best template (1-3-1 vs 2-3) reaches posterior > 0.8 within 3 s after the ball crosses half-court, and the X1 track maps to the 1-3-1 point slot or a 2-3 top slot.
- **Teams documented:** Villanova (Jay Wright) clinic content, recorded at the Spring 2015 Pittsburgh clinic, released 2016 `[DZ44]` — https://onlinestore.coachingtoolbox.net/product/jay-wright-1-2-2-and-1-1-2-1-three-quarter-court-pressure-defense/ `[DZ44]`. Iowa (McCaffery) 1-2-2 three-quarter press — page 404, **unverified**. See P-3 (Ohio State), P-4 (Oregon).
- **Sources:** `[DZ44]`.
- **Confidence:** low–medium.

#### P-3. Ohio State 1-2-2 zone press (2015-16): timeout and dead-ball usage — RICHER (Big Ten program row for F9.5)
- **Name and aliases:** Ohio State 1-2-2 press.
- **Family / sub-family:** F9.5 Program systems; usage policy SC-3.
- **Start alignment:** P-2 1-2-2 slots [HEURISTIC]; front line Keita Bates-Diop, JaQuan Lyle, and Marc Loving or Kam Williams `[DZ33]`.
- **Roles / rules** `[DZ33]`: keep the ball out of the middle; Bates-Diop's length at the top tipped passes; sideline traps past half-court at Purdue (21 Jan 2016) forced throws over the top; used sparingly **out of timeouts and drawn-out dead balls**, then half-court man; against Northwestern it was extended full court and the ball did not cross half-court until 21 s remained on the shot clock (≈ 9 s burned of 30); practised after every made basket; Matta noted often only three and a half or four players engaged.
- **Ordered actions with timing [HEURISTIC]:** (1) timeout/dead ball; (2) press set ≤ 3 s; (3) sideline trap just past half-court; (4) half-court man after the fall-back.
- **Usual counters:** throws over the top out of the trap (the source shows them forced, not completed); tempo inbound [CONVENTION].
- **Detection signature [HEURISTIC]:** press-active begins ≤ 3 s after a **dead ball following a timeout** (PBP) and is absent after live-ball changes of possession; backcourt time (inbound → ball crosses y = 12.73 m) ≥ 7 s on press possessions vs the team baseline; sideline `TRAP` at \|x\| > 5.0 m, 9 < y < 13 m; **engagement count** = defenders with y > y_ball − 2 m during the press (Matta's complaint ≈ ≤ 4).
- **Teams documented:** Ohio State (Matta) 2015-16 — https://www.elevenwarriors.com/ohio-state-basketball/2016/02/67852/hoops-film-study-the-evolving-effective-ohio-state-zone-press `[DZ33]`.
- **Sources:** `[DZ33]`.
- **Confidence:** medium.

#### P-4. Oregon (Altman) 1-2-2 press / trap after makes → man or match-up — RICHER (F9.5 + F11.3)
- **Name and aliases:** Oregon 1-2-2 press/trap.
- **Family / sub-family:** F9.5; F11.3 press → half-court mapping.
- **Start alignment:** P-2 1-2-2 slots [HEURISTIC].
- **Roles / rules:** Oregon typically starts defensive possessions with a press, usually a 1-2-2, flowing into man or the match-up zone (2019-20) `[DZ03]`; full-court pressure including a 1-2-2 trap after made baskets (2021-22) `[DZ05]`. Big Ten from 2024-25 `[DZ74]`.
- **Ordered actions with timing [HEURISTIC]:** made FG → 1-2-2 set before the inbound (`PRESS_SETUP` ≤ 4 s) → trap or contain to half-court → fall-back → man (F ≥ 0.6) or match-up 2-3 (Z-5) within 3 s.
- **Usual counters:** quick inbound before the set (see P-5); middle flash [CONVENTION].
- **Detection signature [HEURISTIC]:** P(press \| previous possession = opponent made FG) − P(press \| defensive rebound) ≥ 0.4; record the **post-press scheme** and its per-game share (man vs match-up).
- **Teams documented:** Oregon 2019-20 `[DZ03]`, 2021-22 `[DZ05]`; vs MSU 2025-26 zone (alignment not stated) `[DZ35]` (URLs in Z-5).
- **Sources:** `[DZ03][DZ05][DZ35][DZ74]`.
- **Confidence:** medium (older seasons; 2024-26 Big Ten press use not confirmed).

#### P-5. Penn State (Rhoades) full-court pressure; MSU's quick-inbound counter — RICHER (F9.1, F9.5)
- **Name and aliases:** Penn State press ("press matchups").
- **Family / sub-family:** F9.1 Full-court man (matchup-assigned press) + F9.5 program row.
- **Start alignment** [HEURISTIC]: man press — each defender within 1.5 m of his assigned attacker in the backcourt; ball defender on the inbounder or receiver at y ≥ 21 m (≈ (21.3, 90°)).
- **Roles / rules:** full- and half-court pressure with opportunistic traps; 20 forced TOs vs St. Francis (Nov 2023) `[DZ68]` and 29 vs Morehead State (Nov 2023, including two 10-second violations) `[DZ69]`; man on 93.9% of 2024-25 possessions through 23 Jan 2025 `[DZ40]`. The press being **man-to-man**, and a diamond press at the end of halves, appear only in snippets — **unverified**. A Penn State player referred to "press matchups" assigned by the coach `[DZ13]`.
- **Ordered actions with timing [HEURISTIC]:** (1) made basket; (2) defenders locate assigned men (~2–4 s); (3) deny/pressure the inbound; (4) opportunistic sideline trap near half; (5) half-court man.
- **Usual counters (MSU, 14 Feb 2024, MSU 80-72 at Penn State):** inbound quickly with the player nearest the boundary and throw early outlets to get up the floor before the press is set; Penn State forced only 11 MSU turnovers vs an average above 15 `[DZ13]`.
- **Detection signature [HEURISTIC]:** backcourt F ≥ 0.6 for ≥ 4 defenders with HMM matchups equal to the half-court matchups (`[D35]` HMM) → "assigned man press". **Press beaten by tempo:** `INBOUND_LAG` < `PRESS_SETUP` → label `press_beaten_early`; compare TO rate vs set-press possessions (for MSU offence analysis, how often MSU beats presses with tempo).
- **Teams documented (MSU first):** MSU counter 2023-24 — https://www.si.com/college/pennstate/basketball/penn-state-mens-basketball-michigan-state-spartans-defeat-nittany-lions-tom-izzo-mike-rhoades `[DZ13]`. Penn State 2023-24 — https://gopsusports.com/news/2023/11/15/defensive-dominance-drives-penn-state-to-win `[DZ68]`; https://bellisariostudentmedia.psu.edu/story/turnovers-free-throws-only-needed-for-penn-states-win-against-morehead-state `[DZ69]`; 2024-25 `[DZ40]`.
- **Sources:** `[DZ13][DZ40][DZ68][DZ69]`.
- **Confidence:** medium.

#### P-6. Iowa (McCaffery) contained vs trapping press — RICHER (F9.5)
- **Name and aliases:** Iowa 1-2-2 press (contain / trap).
- **Family / sub-family:** F9.5; F9.2 1-2-2 "70" (contain) vs trapping variants.
- **Start alignment:** 1-2-2 press slots as P-2 [HEURISTIC]; the structure of Iowa's 1-2-2 itself is **unverified**.
- **Roles / rules (14 Feb 2023 press conference)** `[DZ14]`: Iowa plays both contained and trapping press and varies aggression game to game; the press disrupts rhythm; risk vs four-guard lineups; McCaffery said he learned the 1-2-2 press from Rollie Massimino `[DZ14]`. Iowa 2017-18 (article 1 Mar 2018): man on about 62% of possessions per Synergy (9th percentile man, 47th percentile zone); opened the 2017-18 game at Michigan in zone (first time in McCaffery's 17-year career, per announcers); split ~50-50 vs Illinois `[DZ15]`.
- **Ordered actions with timing [HEURISTIC]:** contain — keep the ball in front with cushion ≥ 2.0 m to half-court; trap — first backcourt `TRAP` within 2–5 s of the inbound.
- **Usual counters:** four-guard lineups `[DZ14]`.
- **Detection signature [HEURISTIC]:** classify each press possession as **contain** (no `TRAP`, handler cushion ≥ 2.0 m; existing "70" signature `[D67]`) or **trap** (≥ 1 backcourt `TRAP`); report the per-game contain/trap ratio as the aggression dial.
- **Teams documented:** Iowa (McCaffery) 2022-23 — https://hawkfanatic.com/?p=64664 `[DZ14]`; man/zone split 2017-18 (article 1 Mar 2018) — https://umhoops.com/?p=93283 `[DZ15]`.
- **Sources:** `[DZ14][DZ15]`.
- **Confidence:** low (press structure unverified).

#### P-7. "Press Virginia" (Huggins / Kevin Mackey lineage) — RICHER (F9.5)
- **Name and aliases:** Press Virginia.
- **Family / sub-family:** F9.5 program systems (volume pressure).
- **Start alignment:** man vs zone structure **not stated** in the source — **unverified**; use F9.0 press-active slots.
- **Roles / rules** `[DZ25]`: Huggins studied Kevin Mackey (Cleveland State, 1986 Sweet 16 as a 14 seed) and moved to full-court pressure all the time; trapping and picking up full court; accepts the risk of transition points; 2014-15: turnovers forced on about 28% of opponent possessions, opponents' eFG 52.7%, the nation's most fouls (821, 23.5 per game), 25 wins and a Sweet 16.
- **Ordered actions with timing [HEURISTIC]:** press on every possession including after misses; trap in the backcourt within 2–5 s.
- **Usual counters:** beat the trap for transition points (the accepted risk) `[DZ25]`.
- **Detection signature [HEURISTIC]:** volume rule as for "40 Minutes of Hell" (F9.5): press active on ≥ 70% of opponent possessions; plus a **foul-cost** feature (team fouls per 100 opponent possessions while pressing).
- **Teams documented:** West Virginia 2014-15 (Big 12) — https://www.nbcsports.com/college-basketball/news/a-shift-in-philosophy-led-bob-huggins-to-build-press-virginia `[DZ25]`.
- **Sources:** `[DZ25]`.
- **Confidence:** medium.

#### P-8. Zone-press fall-back rules — RICHER (extends F9.0 "Fall-back event")
- **Name and aliases:** fall-back; sprint to the paint.
- **Family / sub-family:** F9.0 primitives / F11.3.
- **Start alignment:** at the break moment, 2-2-1 slots per existing F9 row `[D65]`.
- **Roles / rules (2-2-1, re-opened `[D65]` = `[DZ45]`):** once the press is broken or the ball passes midcourt, every defender not on the ball sprints to the paint, unless an easy sideline or midcourt-corner trap is available; the on-ball defender stays on the ball and stops penetration; never let the ball get ahead of you; the weak-side deep defender comes up only for a clear interception. The 2-2-1 as a natural complement to a 2-3 (same shape stretched full court) — snippet only, **unverified**.
- **Ordered actions with timing [HEURISTIC]:** (1) ball crosses y = 12.73 m at t_x; (2) non-ball defenders sprint toward the rim during t_x … t_x + 1.5 s; (3) ≥ 3 of them at r < 5.5 m by t_x + 3.0 s.
- **Usual counters:** advance pass ahead of the retreating defenders [CONVENTION].
- **Detection signature [HEURISTIC]:** ≥ 3 of the 4 non-ball defenders that are at r > 8 m at t_x have mean radial speed toward the rim ≥ 2.5 m/s in [t_x, t_x + 1.5 s] (a team mean of 4 m/s is not reachable from a stance start, and the deep defender is already near the rim), and, as the outcome test, ≥ 3 of them at r < 5.5 m by t_x + 3.0 s; exception flag when a `TRAP` starts within 1.0 s of t_x at \|x\| > 5 m near half-court. "Ball ahead" violation = any non-ball defender with y > y_ball + 1.0 m after t_x for > 1.0 s.
- **Teams documented:** generic — https://www.coachesclipboard.net/221ZonePress.html `[DZ45]`.
- **Sources:** `[DZ45]`.
- **Confidence:** medium.

*(MSU 2026-27 exhibition press: see MSU-4.)*

---

### A7. Junk / combination defences (extends F10)

#### J-1. Diamond-and-one: alignment by offensive front, rotations, chaser rules — RICHER (extends F10 "Diamond-and-1")
- **Name and aliases:** diamond-and-1; amoeba resembles it vs a one-guard front (existing `[D60]`).
- **Family / sub-family:** F10.
- **Start alignment** [HEURISTIC from `[DZ22][DZ21]`]: top X1 covering elbow to elbow (5.50, 90°); wings X3/X4 covering elbow to block, on the lane line at mid-height (3.17, 54.8°) / (3.17, 125.2°) → x = ±1.83 m, y = 2.59 m; X5 on the ball–basket line near the rim (1.20, 90°), shifting along that line; chaser on the star anywhere. Vs a one-guard front align 1-3; vs a two-guard front the wing on that side steps up `[DZ22]`. Starting in a 1-2-2 or 2-3 and shifting after half-court — snippet only, **unverified**.
- **Roles / rules** `[DZ22][DZ21]`: the denier plays total denial on the star's hip (not on top) and sends him to the side where a wing can extend; bump cutters; extend on every screen; force outside shots; know the shooters. The chaser should be mobile (PG/SG, sometimes SF/PF), ideally not the team's top scorer; multiple or rotating chasers are possible `[DZ21]`.
- **Ordered actions with timing [HEURISTIC windows]:**
  1. Wing-to-basket cut by the passer: X1 takes the cutter to the lane line, X4 absorbs him (hand-off within ~1 s) `[DZ22]`.
  2. Wing-to-corner pass: X5 shows, X4 slides down and bumps X5 back to the rim (within ~1.5 s) `[DZ22]`.
  3. Ball to the wing: X1 drops to deny the high post; no pass behind X1 into the heart of the zone `[DZ22]`. Hoop Student version: wing defender on the ball, X1 to the weak elbow, opposite wing to mid-post, X5 behind or in front of the low post `[DZ21]`.
  4. Low-post catch: weak-side wing sprints across to double with X5; X1 drops into the lane and can close out on a skip `[DZ21]`.
- **When used:** whole game, after timeouts, to stop a run, or for a set period such as until the opponent scores twice `[DZ22]`.
- **Usual counters:** heavy screening to free the star `[DZ22]`; middle gap (high post / lane); two or more good low-post players `[DZ21]`.
- **Detection signature [HEURISTIC]:** `CHASER(d, star)` true; the other four fit diamond slots (`SLOT_RESIDUAL` < 1.5 m) with the top at r 4.6–6.5 m and **no** defender between the top and the arc at the top of the key; X5 within 0.8 m of the ball–rim segment on ≥ 70% of frames. Onset/offset: change-point in the chaser feature within ±10 s of a timeout or a made basket (PBP); "until they score twice" → offset within one possession after the opponent's second made FG since onset (test on data).
- **Teams documented:** no D-I program named — gap. MSU: none.
- **Sources:** `[DZ21][DZ22]` — https://hoopstudent.com/diamond-and-1-defense/ ; https://coachingtoolbox.net/?p=414
- **Confidence:** medium (structure), low (D-I usage).

#### J-2. Triangle-and-two: screen rules, post traps, D-I examples — RICHER (extends F10 "Triangle-and-2")
- **Name and aliases:** triangle-and-2.
- **Family / sub-family:** F10.
- **Start alignment** [HEURISTIC]: top (5.00, 90°); bottoms (2.19, 24.2°) / (2.19, 155.8°); two chasers on the targets.
- **Roles / rules** `[DZ22][DZ23]`: the top of the triangle is the most athletic/crafty defender, never with both feet outside the arc, elbow to elbow; if the offence brings a third player high, a defender comes up to match `[DZ22]`. **Screen rules:** denied player screens denied player (cross-screen) → switch; an unguarded player screens a guarded player → trap it, or string it out and let the chaser fight over `[DZ22]`; if a chaser is screened, the nearest zone defender pressures temporarily, then the chaser recovers and sends him back `[DZ23]`. **Post rule:** on a post pass X1 traps down with a wing, only if the catch is in scoring position; the basket is never left empty `[DZ22]`. **Chaser rules:** one pass away → hard deny, forcing backdoor cuts into the zone; more than one pass away → keep denying or sink toward the mid-post at the lane line; on baseline runs stay on the high side, never trail beneath `[DZ23]`. Treat the opponent's third scorer as the only "shooter" among the other three `[DZ23]`.
- **Ordered actions with timing [HEURISTIC]:** cross-screen switch within 1.0 s; post trap within 0.8 s of a scoring-position catch; temporary zone pressure on a screened chaser ≤ 2 s.
- **Usual counters:** several shooters, post scorers (existing `[D70]`); screening the chasers [CONVENTION].
- **Detection signature [HEURISTIC]:** two `CHASER` pairs on two different attackers; on a cross-screen between the two targets a `SWITCH` between the two chasers within 1.0 s; on a screen by an unguarded attacker for a target, either a `TRAP` on the target or the chaser stays (no switch) — never a zone defender holding the target > 2 s; post `TRAP` only when the catch is at r < 3.0 m.
- **Teams documented (D-I):** Utah (Majerus) 1997-98 vs Arizona (Simon, Bibby), 76-51 Elite Eight; Sam Houston State vs Baylor, 2010 NCAA; Kansas (Self) vs North Carolina (Barnes, Bullock), 2012 Midwest Regional final, UNC scoreless over the final 3:58 — https://en.wikipedia.org/wiki/Triangle-and-two_defense `[DZ20]`. (The page also mentions use against Saint Joseph's in 2004 with ambiguous wording.) Bill Self's career-long use — snippet only, **unverified**. No Big Ten use found for 2023-26.
- **Sources:** `[DZ20][DZ22][DZ23]` — https://hoopstudent.com/triangle-and-2-defense
- **Confidence:** medium.

#### J-3. Box-and-one: D-I usage notes — RICHER (teams only; structure already complete in F10 `[D68]`)
- **Name and aliases:** box-and-1.
- **Family / sub-family:** F10.
- **Start alignment:** as F10 (re-confirmed: high pair at the FT line extended, low pair one foot in the lane on the blocks; weak-side high always denies the high post) `[DZ48]`.
- **Roles / rules / actions / counters / detection:** as F10; nothing new `[DZ48]`.
- **Teams documented:** Wikipedia names Allen Iverson (Georgetown) and Ray Allen (UConn) as college players who faced it, without opponents or seasons — https://en.wikipedia.org/wiki/Box-and-one_defense `[DZ47]`. Izzo joking in Feb 2015 about a box-and-one on D'Angelo Russell — snippet only, **unverified** and facetious. No Big Ten box-and-one found for 2023-26 — gap.
- **Sources:** `[DZ47][DZ48]` — https://thehoopsgeek.com/basketball-plays/box-and-1-defense-roles-responsibilities/
- **Confidence:** low.

---

### A8. Mid-possession and between-possession scheme changes (extends F11)

#### SC-1. Score-run + timeout trigger — NEW policy (F11.4)
- **Name and aliases:** timeout-after-run scheme change.
- **Family / sub-family:** F11.4 Between-possession policies (trigger `timeout_after_run`).
- **Start alignment:** n/a (policy); scheme before and after per F8/F1 templates.
- **Roles / rules:** a defence changes scheme (man → zone or zone → man) at a timeout, often a media timeout, after the opponent opens a lead or a run, and holds the change for long stretches. Cases:
  - Indiana vs MSU, 11 Feb 2025: down 20-8 in about the first nine minutes, Indiana went 2-3 and closed the half on a 12-2 run; won 71-67 `[DZ08][DZ04]`. The switch coming out of the under-12 media timeout — snippet only, **unverified**.
  - Ohio State vs Illinois, 3 Jan 2015: down 8 with just over 4 minutes left in the first half, Matta called a timeout and went from 2-3 to man for good `[DZ34]`.
  - Northwestern vs Northern Illinois, Nov 2010: opened man, fell behind 13-5, switched to the 1-3-1; a 19-3 run followed and NU never trailed again. Vs Texas-Pan American: stayed man until late in the second half, then switched to the zone, which helped build an 11-point lead after UTPA had come close to an upset `[DZ07]`.
  - Northwestern vs Minnesota, Jan 2009: opened in a 2-3 match-up; Minnesota shot 14-of-18 in the first 15 minutes; trailing by nine late in the half, Carmody switched to the 1-3-1; Minnesota missed 5 of its last 6 first-half shots and had 15 of its 19 turnovers in the final 25 minutes `[DZ67]`.
- **Ordered actions with timing [HEURISTIC]:** run → timeout → new scheme from the first live possession → dwell ≥ 10 possessions.
- **Usual counters:** have the zone offence ready after timeouts (Izzo's own diagnosis in `[DZ10]`) [CONVENTION].
- **Detection signature [HEURISTIC]:** scheme change-point (F11.6 HMM) at the first live possession after a timeout (PBP), preceded by an opponent run: margin change ≥ +8 for the opponent over the previous 6 game-minutes, or opponent FG% ≥ 65% over the previous 10 possessions. Label `trigger = timeout_after_run`. Expected dwell ≥ 10 possessions.
- **Teams documented (MSU first):** Indiana vs MSU 2024-25 — URLs in Z-10 `[DZ04][DZ08]`; Ohio State 2014-15 `[DZ34]`; Northwestern 2008-09 `[DZ67]`, 2010-11 `[DZ07]`.
- **Sources:** `[DZ04][DZ07][DZ08][DZ34][DZ67]`.
- **Confidence:** high for the events; medium for the generalisation.

#### SC-2. "Start in match-up, go 1-3-1 if not working" — NEW policy (F11.4)
- **Name and aliases:** match-up base with 1-3-1 change-up.
- **Family / sub-family:** F11.4.
- **Start alignment:** match-up (Z-5/Z-7) then 1-3-1 (Z-8) templates.
- **Roles / rules:** Northwestern 2009, after the Iowa loss: start in the match-up zone and switch to the 1-3-1 if needed; Carmody changed between the two by opponent, game flow and how comfortable the opponent looked `[DZ06]`.
- **Ordered actions with timing [HEURISTIC]:** first scheme of the game = match-up; switch after ~10 half-court possessions if the opponent scores efficiently.
- **Usual counters:** corner threes vs the 1-3-1 (Z-8).
- **Detection signature [HEURISTIC]:** per-game sequence model: first scheme = match-up (Z-5/Z-7 signature); P(switch to 1-3-1 \| opponent PPP ≥ 1.15 over the first 10 half-court possessions) above the base rate.
- **Teams documented:** Northwestern (Carmody) 2008-09 — https://dailynorthwestern.com/2009/03/03/archive-manual/mens-basketball-cats-season-lives-dies-by-the-zone/ `[DZ06]`.
- **Sources:** `[DZ06]`.
- **Confidence:** medium.

#### SC-3. Dead-ball / timeout-only press — NEW policy (F11.4)
- **Name and aliases:** situational press; timeout press.
- **Family / sub-family:** F11.4.
- **Start alignment:** P-3 slots.
- **Roles / rules:** Ohio State 2015-16 used its 1-2-2 press mainly out of timeouts and long dead balls `[DZ33]`. Penn State's diamond press at the end of halves — snippet only, **unverified**.
- **Ordered actions with timing [HEURISTIC]:** press set ≤ 3 s after the dead ball; fall-back after half-court.
- **Usual counters:** quick inbound is unavailable after a dead ball, so: middle flash, over-the-top pass [CONVENTION].
- **Detection signature [HEURISTIC]:** P(press \| possession starts after a timeout or a dead ball ≥ 45 s) / P(press \| other) ≥ 3, with ≥ 10 timeout/dead-ball possessions in the sample; end-of-half variant: P(press \| game clock ≤ 60 s in the half).
- **Teams documented:** Ohio State 2015-16 — https://www.elevenwarriors.com/ohio-state-basketball/2016/02/67852/hoops-film-study-the-evolving-effective-ohio-state-zone-press `[DZ33]`.
- **Sources:** `[DZ33]`.
- **Confidence:** medium.

#### SC-4. Press after made shots, falling back into man or match-up — RICHER (extends F11.3 / F11.4 "After made FG")
- **Name and aliases:** make-press.
- **Family / sub-family:** F11.3 / F11.4.
- **Start alignment:** P-4 slots.
- **Roles / rules:** Oregon — press to start possessions (2019-20) and a 1-2-2 trap after made baskets (2021-22), flowing into man or match-up `[DZ03][DZ05]`. Auburn presses after made FGs and FTs (existing `[D79a][D79b]`). Syracuse pressing only after made baskets as a change-up from the 2-3 — snippets only, **unverified**.
- **Ordered actions with timing [HEURISTIC]:** as P-4.
- **Usual counters:** quick inbound (P-5).
- **Detection signature [HEURISTIC]:** see P-4; add the **back-off time** (existing F11.4) and the **post-press scheme** label.
- **Teams documented:** Oregon 2019-20, 2021-22 `[DZ03][DZ05]` (URLs in Z-5).
- **Sources:** `[DZ03][DZ05]`.
- **Confidence:** medium.

#### SC-5. All-zone team that plays man only on baseline out-of-bounds — NEW policy (F11.4 / F14 BLOB)
- **Name and aliases:** BLOB-man exception.
- **Family / sub-family:** F11.4; F14 BLOB.
- **Start alignment:** zone templates (1-3-1, 1-1-3) in the half-court; man on BLOB inbounds.
- **Roles / rules:** Oakland (Kampe) plays zone every possession except baseline out-of-bounds plays, where it goes man `[DZ56]`.
- **Ordered actions with timing [HEURISTIC]:** BLOB inbound → man for the inbound window (5 s) and the possession; next non-BLOB possession → zone.
- **Usual counters:** BLOB sets against man (offence_full F13.2) [CONVENTION].
- **Detection signature [HEURISTIC]:** P(man \| possession starts with a frontcourt BLOB inbound, inbound spot y < 0) ≥ 0.8 while P(man \| other) ≤ 0.1.
- **Teams documented (MSU first):** Oakland vs MSU 20 Dec 2025 confirms only the 1-3-1 `[DZ11]`; the BLOB rule is from a 2025-26 preview dated 12 Nov 2025 — https://gocoogs.com/?p=46293 `[DZ56]`.
- **Sources:** `[DZ56][DZ11]`.
- **Confidence:** medium-high (single dated 2025-26 preview with a direct observation; partly corroborated by the 20 Dec 2025 game `[DZ11]`).

#### SC-6. Change-up zone dosing — NEW policy (F11.4)
- **Name and aliases:** change-up zone; back-pocket zone.
- **Family / sub-family:** F11.4.
- **Start alignment:** 2-3 slots (Z-10).
- **Roles / rules:** Penn State 2024-25: man on 93.9% of possessions; Rhoades calls the 2-3 a change-up kept in his back pocket; 75 zone possessions through 19 games (89 the whole previous season), 50 of them in three games (Oregon, MSU, Rutgers); MSU saw a season-high 28 zone possessions and went 10-of-24 with 3 turnovers; across the three games opponents scored 42 points on 50 zone possessions (0.84 PPP); used to disrupt rhythm and stop downhill attacks `[DZ40]`.
- **Ordered actions with timing:** n/a (dosing policy).
- **Usual counters:** zone offence readiness [CONVENTION].
- **Detection signature [HEURISTIC]:** per-game zone share; flag "change-up" when the season zone share ≤ 10% but a single game ≥ 25%; store PPP by scheme per game for comparison with Synergy-style splits.
- **Teams documented (MSU first):** Penn State vs MSU, Jan 2025 (2024-25) — https://nittanysportsnow.com/2025/01/penn-state-basketball-has-a-new-look-on-defense/ `[DZ40]`.
- **Sources:** `[DZ40]`.
- **Confidence:** high.

#### SC-7. Late-game zone switch vs MSU (Duke, 6 Dec 2025) — NEW event (F11.4)
- **Name and aliases:** late-game zone.
- **Family / sub-family:** F11.4 (trigger `late_game`).
- **Start alignment:** zone alignment not stated — **unverified**.
- **Roles / rules:** Duke switched to a zone in the final minutes; Izzo said on his radio show that MSU would be 11-0 if his coaching against zones were better `[DZ10]`. Duration and alignment not stated; game outcome inferred — **unverified details**.
- **Ordered actions with timing [HEURISTIC]:** change to zone with game clock ≤ 5:00 in the 2nd half.
- **Usual counters:** n/a (not stated).
- **Detection signature [HEURISTIC]:** change-point to zone with game clock ≤ 5:00 in the 2nd half; label `trigger = late_game`.
- **Teams documented (MSU first):** Duke vs MSU 2025-26 — https://spartanavenue.com/tom-izzo-says-his-coaching-is-the-reason-michigan-state-isn-t-11-0-01kcs43bkpkj `[DZ10]`.
- **Sources:** `[DZ10]`.
- **Confidence:** low.

---

### A9. Transition defence (extends F12)

**Definitions note.** The transition-offence windows in the project brief (Synergy "defence not set"; Hoop-Math shot ≤ 10 s after a defensive rebound with the ball live; FastScout possession ending in the first 10 s of the shot clock; Hudl InStat 4–8 s; coaching phases) belong to Job D. The Hoop-Math and FastScout pages could not be opened in this research (MGoBlog 403; Hudl support 404), so those definitions are **unverified** here. The `GET_BACK` clocks (A0) are built to be computed on any of those windows. NCAA clock facts used: 30 s shot clock and a 10 s backcourt count that does not reset after a stoppage in play (with few exceptions), and the 1.22 m restricted arc, all since 2015-16 `[DZ64]`.

#### T-1. Two-guards-back geometry — RICHER (extends F12.1 "Two back")
- **Name and aliases:** two back; guards back. Label `two_back_halfcourt` (vs break-every-time teams, `[DZ53]`); the old F12.1 Full Back / Half Back row becomes `two_back_full_half`. Both map to the parent `two_back`.
- **Family / sub-family:** F12.1 Get-back rules.
- **Start alignment:** two-back spots at the half-court line, one each side of the centre circle: (12.86, 81.8°) / (12.86, 98.2°), measured from the team's **own** defended rim.
- **Roles / rules (re-opened `[D85]` = `[DZ53]`):** against teams that break every time, three bigs crash and two guards retreat to the half-court line, one on each side of the centre circle; the normal rule is one guard back as the safety beyond the arc; Underwood's shooter-back rule on 3PA.
- **Ordered actions with timing [HEURISTIC]:** at own shot release + 1.0 s the two guards are moving toward their own rim; they are at their spots by release + 3.0 s, or by the opponent's defensive-rebound frame + 1.0 s. (At release the guards are near the arc of the rim being shot at, y ≈ 18.7 m; reaching y ≤ 14.0 m in 1.0 s would need ≈ 5–6 m/s average from near standstill.)
- **Usual counters:** offensive-rebound loss (fewer crashers) — the trade-off in F12 `[D100]`.
- **Detection signature [HEURISTIC]:** (a) kinematic test at own shot release + 1.0 s (as old F12.1): two players moving toward their own rim at ≥ 2 m/s; (b) position test by release + 3.0 s, or by the opponent's defensive-rebound frame + 1.0 s: the same two with 11.5 ≤ y ≤ 14.0 m and \|x\| ≤ 3.0 m on opposite sides (sign of x differs), moving toward their own rim or stationary (speed < 1.5 m/s), while 3 teammates are within 4 m of the rim being shot at (distance to (0, 25.45 m) < 4 m) at release + 1.0 s. Label `get_back_policy = two_back_halfcourt` (parent `two_back`). All timings [HEURISTIC].
- **Teams documented:** generic — https://www.coachesclipboard.net/TransitionDefense.html `[DZ53]`.
- **Sources:** `[DZ53]`.
- **Confidence:** medium.

#### T-2. 4-on-3 rules — NEW (F12.6 Outnumbered)
- **Name and aliases:** 4-on-3 transition defence; stacked two back.
- **Family / sub-family:** F12.6.
- **Start alignment** [HEURISTIC]: stacked two back — top at (5.5, 90°), bottom at (1.5, 90°); third defender arriving at the nail (4.19, 90°).
- **Roles / rules:** in a 4v4 drill the defender matched with the passer must touch the baseline first; the other three get back, stop the ball and match up in help positions until the fourth returns `[DZ54]`. In 4-on-4-on-4, the two back defenders are stacked: top stops the ball in the backcourt, bottom protects the paint; bottom closes out to the first receiver, top drops as low as the lowest attacker `[DZ55]`. The rule that the remaining two split the three off-ball attackers and the trailer takes the farthest from the ball — snippet only, **unverified**.
- **Ordered actions with timing [HEURISTIC]:** (1) ball stopped before r = 8 m; (2) three defenders in help spots; (3) matchups resolve within 2 s of the fourth crossing half-court.
- **Usual counters:** quick ball movement before the fourth arrives [CONVENTION].
- **Detection signature [HEURISTIC]:** `OUTNUMBER(4,3)`; `t_stop` before the ball reaches r = 8 m; the three defenders each inside triangle(ball, rim, nearest attacker) (existing gap occupancy); when the fourth crosses half-court the HMM matchup entropy drops ≥ 50% within 2 s.
- **Teams documented:** generic drills — https://thehoopsgeek.com/basketball-drills/4-v-4-transition-drill/ `[DZ54]`; https://coachesclipboard.net/4on4on4Drill.html `[DZ55]`.
- **Sources:** `[DZ54][DZ55]`.
- **Confidence:** low–medium.

#### T-3. Role-based get-back: Stopper / Protector / Sprinters (Travis Ford) — NEW (F12.1)
- **Name and aliases:** Stopper, Protector, Sprinters.
- **Family / sub-family:** F12.1 Get-back rules (role-based, not position-based).
- **Start alignment** [HEURISTIC]: Protector at (1.4, 90°), outside the 1.22 m restricted arc, by t_rim; Stopper on the primary handler in the backcourt (y ≥ 12.73 m); Sprinters crash then retreat.
- **Roles / rules** `[DZ26]`: **Stopper** = best full-court on-ball defender, keeps the primary handler from getting into rhythm; **Protector** = a slower player least likely to get an offensive rebound, protects the basket; **Sprinters** = three players who always crash the glass, then hustle back to stop specific shots. Cross-matchups can create an advantage when the ball is pushed up the wing.
- **Ordered actions with timing [HEURISTIC]:** shot → Protector retreats immediately → Stopper picks up the handler → Sprinters retreat after the rebound is lost.
- **Usual counters:** push past the Stopper up the wing (cross-matchup advantage noted) `[DZ26]`.
- **Detection signature [HEURISTIC]:** from own-shot possessions across a game: Protector = largest share of first-to-own-rim events (t_rim) and lowest offensive-rebound share; Stopper = most often first within 2 m of the opposing primary handler after a change of possession, pickup at y ≥ 12.73 m; Sprinters = the three within 3 m of the rim being shot at (distance to (0, 25.45 m) < 3 m) at release + 1 s. Role stability (same player on ≥ 70% of possessions) separates a role system from a position system (PG back).
- **Teams documented:** Travis Ford clinic, no team/season given — https://www.mensbasketballhoopscoop.com/?p=20023 `[DZ26]`.
- **Sources:** `[DZ26]`.
- **Confidence:** medium.

#### T-4. Wall / loading to the ball / strong-side-first fill — NEW (F12.2 / F12.4)
- **Name and aliases:** build a wall; post shadow; load to the ball; strong side first. Label `transition_wall_load`, distinct from F7.5 `load_to_ball` (half-court, ball in the corner) and from BS-10 `drop_gap_load`.
- **Family / sub-family:** F12.2 Stop the ball / F12.4 Matchup on the fly.
- **Start alignment** [HEURISTIC]: wall line at y 6.5–8.5 m (just above the arc) across the ball's lane, \|x − x_ball\| ≤ 2.5 m, e.g. (7.65, 78.7°) for a ball pushed up the right-centre lane.
- **Roles / rules:** the defensive big sprints ahead of the ball and turns his body to stop middle penetration ("building a wall", "post shadow"), already positioned so his closeout goes one way; risk: a trailing big who can shoot (Zak Boisvert breakdown) `[DZ28]`. OKC vs Indiana (2025 NBA Finals; secondary): sprint back on the shot with no ball-watching, contest outlets, fill the strong side first with trailers rotating weak side, build a wall before the paint when a defender is already beaten, send extra help at the ball when back in numbers; Indiana's transition points fell to 14 and 13 in Games 1–2 `[DZ27]`.
- **Ordered actions with timing [HEURISTIC]:** wall formed before the ball reaches r = 8 m; strong side filled first by the first two defenders back.
- **Usual counters:** trailing big who can shoot `[DZ28]`.
- **Detection signature [HEURISTIC]:** during transition (ball moving toward the defended rim at ≥ 3 m/s), ≥ 2 defenders with y between y_ball − 4 m and y_ball − 1 m within 3 m laterally of the ball's projected path, facing up court, approximated from positions as velocity toward own rim between 0 and 1.5 m/s while the ball is above the defender (y_ball > y_d); true backpedalling needs pose and is flagged as pose-dependent; all before the ball reaches r = 8 m. "Load" by the big: the tallest defender is one of them. Strong-side-first: the first two defenders below the ball have sign(x) = sign(x_ball) on ≥ 70% of transition possessions.
- **Teams documented:** coaching/NBA (secondary), no D-I team named — https://coachingtoolbox.net/loading-to-the-basketball `[DZ28]`; https://lockdowndefense.substack.com/p/how-okc-shut-down-indianas-fast-break `[DZ27]`.
- **Sources:** `[DZ27][DZ28]`.
- **Confidence:** medium.

#### T-5. Cross-match swap rule; size-matched ball stopper; rim protector = tallest — RICHER (extends F12.4)
- **Name and aliases:** transition cross-match; swap; half-court cross-matching (NBA alias).
- **Family / sub-family:** F12.4 Matchup on the fly.
- **Start alignment** [HEURISTIC]: rim protector (tallest) at (1.4, 90°), outside the 1.22 m restricted arc; ball stopper of similar size on the handler at y ≈ 11–13 m.
- **Roles / rules** `[DZ30]`: protect the basket first (rim protector should be the taller/longer defender, not necessarily the closest), stop or slow the ball (ideally a similar-size defender), then match three-point shooters and similar-size players. A mismatch is acceptable if the mismatched attacker does not have the ball; if it becomes a problem, the small defender cuts into the lane to protect the rim and the rim protector slides out to the attacker. Turn and backpedal to see ball and man. Half-court cross-matching (NBA; secondary): a centre guards a non-shooter while a wing takes the opposing big, keeping the rim protector out of ball screens; Boston, Charlotte and Houston named as base users `[DZ49]`.
- **Ordered actions with timing [HEURISTIC]:** (1) rim protected by t_rim; (2) ball stopped; (3) matchups; (4) swap within 6 s after `SET_DEF` if needed.
- **Usual counters:** post the mismatch before the swap [CONVENTION].
- **Detection signature [HEURISTIC]:** at t0 + 3 s compute each HMM pair's height difference; cross-match = \|height_d − height_a\| ≥ 10 cm and the pair differs from the half-court home assignment (existing F12.4). **Swap event**: within 6 s after `SET_DEF`, a screenless reciprocal exchange between the mismatched small defender (moving to r < 2.5 m) and the rim protector (moving out to r > 5 m) → `transition_swap`. Rim-protector test: the first defender to r ≤ 1.5 m is the tallest of the five on ≥ 60% of possessions.
- **Teams documented:** generic — https://hoopstudent.com/transition-defense/ `[DZ30]`; NBA (secondary) — https://www.thescore.com/nba/news/3195631 `[DZ49]`.
- **Sources:** `[DZ30][DZ49]`.
- **Confidence:** medium.

#### T-6. Reaction rule (two quick first steps); one-guard vs two-guard back — RICHER (extends F12.1)
- **Name and aliases:** first two steps; react, don't look.
- **Family / sub-family:** F12.1.
- **Start alignment:** first back at (1.4, 90°), one step out from the rim, outside the 1.22 m restricted arc (r 1.25–1.8 m band); t_rim's r ≤ 1.5 m stays the arrival test.
- **Roles / rules** `[DZ29]`: all sprint back; the first back runs to the rim and takes one step out, forcing at least one pass; the second back stops the ball wherever it is, even just over half-court, buying a second or two; the other three sprint back with vision and match the shooters; usually one guard protects the basket after a score, rebound or steal; against a fast-breaking team use two guards back (or a press); the first two steps decide it — react with two quick steps rather than look then go.
- **Ordered actions with timing [HEURISTIC; calibrate on MSU film]:** reaction ≤ 0.6 s; starting targets t_rim ≤ 3.5 s after a defensive rebound at the far end and ≤ 4.0 s after a made-basket inbound; report t_rim percentiles rather than a hard pass/fail. (A first back starting at y ≈ 15–18.7 m needs 13–17 m to reach r ≤ 1.5 m; 2.5 s would need 5.4–6.9 m/s average. Arithmetic only; no speed source opened — **unverified**.)
- **Usual counters:** advance pass over the second back [CONVENTION].
- **Detection signature [HEURISTIC]:** reaction latency = t0 to the first frame where a retreating player's speed toward his own rim exceeds 2.5 m/s; target ≤ 0.6 s for the two players nearest half-court. Second defender's pickup y at t_stop ≥ 11 m = "stop the ball past half" (existing F12.2).
- **Teams documented:** generic newsletter (18 Jun 2025) — https://www.coachesclipboard.net/newsletters/CCNewsLetter06182025.html `[DZ29]`.
- **Sources:** `[DZ29]`.
- **Confidence:** medium.

#### T-7. Contest the outlet receivers — RICHER (extends F12.5 "Jam / tag the rebounder")
- **Name and aliases:** outlet contest; deny the outlet.
- **Family / sub-family:** F12.5.
- **Start alignment** [HEURISTIC]: outlet receiver at the near wing, about (7.3, 35°) at the opponent's end in full-court terms; contesting defender within 1.5 m of him.
- **Roles / rules:** OKC contested outlet passes to Indiana's guards, forcing them back toward the ball and slowing the start of the break `[DZ27]` (NBA, secondary). Only one player should jam the rebounder; the others sprint back (existing `[D85]`, re-opened `[DZ53]`).
- **Ordered actions with timing [HEURISTIC]:** contest inside t0 … t0 + 1.5 s after the defensive rebound.
- **Usual counters:** rebounder dribbles out himself; long outlet over the top [CONVENTION].
- **Detection signature [HEURISTIC]:** after a defensive rebound at t0, the primary outlet receiver (first pass target) has a defender within 1.5 m during t0 … t0 + 1.5 s; outlet delay = rebound → outlet pass, compared with and without the contest; rule check: ≤ 1 player within 2 m of the rebounder.
- **Teams documented:** NBA (secondary) — https://lockdowndefense.substack.com/p/how-okc-shut-down-indianas-fast-break `[DZ27]`; generic — https://www.coachesclipboard.net/TransitionDefense.html `[DZ53]`.
- **Sources:** `[DZ27][DZ53]`.
- **Confidence:** medium.

*(MSU progressive transition rules: see MSU-5.)*

---

### A10. MSU / Izzo defence (extends F1.6, F18.4)

Items M-1 (Izzo man), M-5 (Jump to the Ball), BS-5 (MSU 2019-20 soft show), BS-7 (MSU 2014-15 and through 2018-19 hard hedge), H-1 (MSU DHO switching by position), Z-10 (zones faced by MSU) and P-5 (MSU's quick-inbound counter) are MSU-attributed and sit in their families above. This subsection adds the remaining MSU evidence.

#### MSU-1. MSU off-ball coverage evidence: "Beat and Belt" flash denial, Pin Down & Flares, man/zone vs double screens — RICHER (extends F1.6 and F5)
- **Name and aliases:** Beat and Belt (MSU 2015 video listing; the Izzo course lists "Beat the Belt" — see Corrections C-6); Pin Down & Flares; Defending Screen and Screen Players (screen-the-screener); Elbow and Block Coverage.
- **Family / sub-family:** F5 Off-ball screen coverages; F1.6 MSU profile.
- **Start alignment** [HEURISTIC]: weak-side attacker at the left wing (7.3, 145°) flashing to the high post (≈ (4.6, 100°)); his defender in help at (2.8, 116°) (M-1 spot), stepping ball-side of the flash path.
- **Roles / rules:** MSU 2015 practice video: Pin Down & Flares drill teaches how to defend two common off-ball screens; Beat and Belt: players deny flash cuts into the high post and adjust quickly to stop the back cut `[N40]`. MSU 2010-11 video covers pin-down defence and how Izzo uses man and zone against double screens `[N11]`. Izzo course lessons include "Defending Screen and Screen Players" and "Elbow and Block Coverage" (titles only) `[N37]`. Coverage specifics **unverified**.
- **Ordered actions with timing [HEURISTIC]:** flash cut starts (t = 0) → defender ball-side within 0.5 s → back-cut stopped within 1.0 s of the cutter's reversal.
- **Usual counters:** back-cut behind the flash denial (the drill's second phase) `[N40]`.
- **Detection signature [HEURISTIC]:** (a) **High-post flash denial:** when a weak-side attacker cuts toward the high-post region (\|x\| < 2.5 m, 3.5 < y < 6.5 m), his defender is ball-side of him (≤ 0.6 m from segment(ball, cutter)) within 0.5 s of the cut start. (b) **Zone-vs-double-screen flag:** on double/stagger screens the F8.0 man-vs-zone score may briefly flip toward zone for MSU (2010-11 claim); test the zone score in [t₀, t₀ + 3 s] around double screens.
- **Teams documented:** Michigan State 2015 video — https://www.mensbasketballhoopscoop.com/?p=23659 `[N40]`; 2010-11 video — https://onlinestore.coachingtoolbox.net/product/all-access-michigan-state-basketball-practice-with-tom-izzo/ `[N11]`; Izzo course (undated) — https://coachtube.com/course/basketball/defensive-skills-and-drills/118044 `[N37]`.
- **Sources:** `[N40][N11][N37]`.
- **Confidence:** high that these drills/topics exist; coverage specifics **unverified**.

#### MSU-2. MSU ball-screen coverage timeline 2010–2020 — RICHER (extends F1.6 rows and F18.4)
- **Name and aliases:** MSU PnR coverage by season.
- **Family / sub-family:** F3 (by season) / F18.4 MSU usage index.
- **Start alignment:** see BS-5 (soft show) and BS-7 (hard hedge) MSU templates.
- **Roles / rules (new evidence only):**

  | Season | Base PnR coverage | Other | Source | Confidence |
  |---|---|---|---|---|
  | 2010-11 (practice video) | "Handles ball screens" (unspecified) | Man and zone vs double screens; 4v3/4v4 shell | `[N11]` | high (topic exists); coverage **unverified** |
  | 2014-15 | **Hedge and recover** (Schilling, Nairn), keep out of the paint | Weak-side help across the lane strips short-corner catches | `[N14]` | high |
  | 2015 (practice video) | Multiple ball-screen coverages (Continuous Ball Screens drill), options vs pull-up shooters, drivers and stretch bigs; side and top PnR coverages | DHO switching by position; Pin Down & Flares; Beat and Belt | `[N40]` | high (topics); specifics **unverified** |
  | through 2018-19 | **Flat or hard hedge** by bigs; weak-side rotations cover the roller | vs Michigan 2018-19: **switched with the 5** on 27 possessions, 18 pts = 0.67 PPP (author's own count; **new**) | `[N13]` | high; base coverage is a re-confirmation (= F1.6 / old lines for S69) |
  | 2018-19 (3 games vs Michigan) | Switching ball screens (re-confirmation of F1.6) | Michigan guards/wings: 64 ball-screen/iso plays, 37 pts, 0.58 points per play (**new**) | `[N43]` | high |
  | 2017-18 | Did **not** switch 1-5 vs Wagner (re-confirmation of F1.6; not new) | — | `[N43]` | high |
  | 2019-20 | **Soft hedge** base; rarely switch 1-5 (re-confirmation of F1.6 / F18.4) ; Tillman able to switch | MSU allowed 0.9 PPP in Big Ten play (as of 3 Jan 2020; **new**) | `[N43]` | high |
  | 2024-25 | Hedge + recover and/or blitz; gap bump on the roller | existing `[D24]` (MGoBlog returned 403 in this research; not re-opened) | `[D24]` | as above |
  | 2025-26 / 2026-27 | **Unverified** — no opened film source | — | — | — |

- **Ordered actions with timing:** per BS-5 / BS-7.
- **Usual counters (documented vs MSU):** slips against Kohler's hard hedge (existing `[D24]`).
- **Detection signature / prior [HEURISTIC]:** P(show family: soft or hard hedge \| MSU ball screen) high across 2014-2020; switching is opponent-specific (Michigan 2018-19); expect a weak-side low-man tag after hedges (2014-15 and 2018-19 sources); expect few 1-5 switches except in game plans built around a switchable 5 (Tillman, 2019-20).
- **Teams documented:** Michigan State — URLs: `[N14]` https://www.insidethehall.com/2015/01/07/film-session-michigan-state/ ; `[N13]` https://umhoops.com/?p=102796 ; `[N43]` https://dylanburkhardt.substack.com/p/making-sense-of-michigan-at-michigan ; `[N40]` https://www.mensbasketballhoopscoop.com/?p=23659 ; `[N11]` (URL in MSU-1).
- **Sources:** `[N11][N13][N14][N40][N43]`.
- **Confidence:** high for 2014-15 to 2019-20; 2025-27 **unverified**.

#### MSU-3. MSU transition defence: "4 crash, PG back" re-confirmed; transition D as a first-half problem (2020) — RICHER (extends F12.1 "One back" MSU row)
- **Name and aliases:** MSU one back.
- **Family / sub-family:** F12.1.
- **Start alignment** [HEURISTIC]: at release + 1.0 s, PG at or beyond the arc of the rim being shot at, about (17.85, 90°) in the defended-rim frame (7.6 m from the rim being shot at), moving toward his own rim at ≥ 2 m/s (as the old one-back signature); four within 4 m of the rim being shot at (distance to (0, 25.45 m) < 4 m). No own-end position is tested at 1.0 s.
- **Roles / rules:** send 4 to the offensive glass, the PG gets back (= D4 re-opened) `[DZ52][N12]`; Izzo named transition defence as MSU's biggest first-half problem in one game (Feb 2020) `[DZ51]`.
- **Ordered actions with timing [HEURISTIC]:** as existing F12 one-back row.
- **Usual counters:** leak-outs against four crashers [CONVENTION].
- **Detection signature [HEURISTIC]:** existing one-back count (expected 1 for MSU) plus the `GET_BACK` clocks (A0) per MSU possession, to track the 2020-type failure (report t_rim percentiles; provisional flag t_rim > 3.5 s after a defensive rebound or > 4.0 s after a made-basket inbound [HEURISTIC; calibrate on MSU film], or n_back(t0+2 s) ≤ 1 when outnumbered).
- **Teams documented:** Michigan State (undated clinic notes) — https://coachingtoolbox.net/defense/d1-defensive-notes.html `[DZ52]`; Feb 2020 — https://www.si.com/college/michiganstate/basketball/tom-izzo-talks-michigan-state-basketball-ahead-of-the-iowa-hawkeyes `[DZ51]`.
- **Sources:** `[DZ51][DZ52][N12]`.
- **Confidence:** medium.

#### MSU-4. MSU 2026-27 full-court press (exhibition) — RICHER (extends F9.5 "MSU 2023-24")
- **Name and aliases:** MSU full-court pressure.
- **Family / sub-family:** F9.5 program row; structure (F9.1 man vs F9.2 zone) **unverified**.
- **Start alignment:** not described — **unverified**; use F9.0 press-active.
- **Roles / rules:** in an exhibition vs UIW (89-59; game most likely 2 Oct 2026, article dated 3 Oct 2026) MSU used a full-court press from the start; UIW had several scoreless first-half stretches; MSU committed 18 turnovers; the writer read it as Izzo testing how much pressure the team can sustain `[DZ63]`.
- **Ordered actions with timing:** **unverified**.
- **Usual counters:** n/a.
- **Detection signature [HEURISTIC]:** existing F9.0 press-active primitive; track MSU press rate by season (2023-24 exhibitions `[D5]`, 2026-27 exhibition `[DZ63]`); add `PRESS_SETUP` and the post-press scheme label.
- **Teams documented:** Michigan State 2026-27 — https://roundtable.io/sports/ncaa/michigan-state/game-day/michigan-state-shows-off-in-89-59-exhibition-win-over-uiw `[DZ63]`.
- **Sources:** `[DZ63]`.
- **Confidence:** low–medium.

#### MSU-5. MSU progressive transition drill rules (2v1, 3v2 stack, 4v3, 5v4) — RICHER (extends F12.6 Outnumbered; MSU-specific)
- **Name and aliases:** Tom Izzo's Michigan State progressive transition drill.
- **Family / sub-family:** F12.6 Outnumbered.
- **Start alignment:** 3v2 stack — top (5.50, 90°), bottom (1.50, 90°) (outside the 1.22 m restricted arc, consistent with the tandem rule in `[DZ53]`); 2v1 — lone defender at r ≤ 2.0 m.
- **Roles / rules** `[DZ50]`: sequence 2v1 → 3v2 → 4v3 → 5v4 → 5v5 full court, rebounders outletting to sideline wings and attackers sprinting back to become defenders; run 15–20 minutes. **1v2:** get as low as the lowest attacker, stay below the ball, concede the jumper, do not come up to challenge. **3v2:** stack one top, one low; the low defender takes the first pass and closes out, the top defender drops to the basket. **4v3 / 5v4:** stop the layup, talk, box out.
- **Ordered actions with timing [HEURISTIC]:** 3v2 — (1) top meets the ball at r 6–8 m; (2) first pass to a wing → bottom closes out (arrive ≤ 1.0 s after the catch); (3) top's r drops ≥ 2.5 m within 1.5 s of the pass and reaches r ≤ 2.5 m within 2.5 s; (4) third defender arrives → match up.
- **Usual counters:** quick second pass to the opposite wing after the bottom closes out [CONVENTION].
- **Detection signature [HEURISTIC]:** `OUTNUMBER(3,2)` true at t0 + 2 s; two defenders within 1.0 m of the ball–rim line, separated radially by 3–5 m; on the first pass to a wing (θ < 60° or > 120°), the deeper defender's distance to the receiver drops ≥ 2.5 m within 1.0 s **and** the higher defender's r drops ≥ 2.5 m within 1.5 s. 2v1: lone defender at r ≤ 2.0 m while the ball is outside r = 5 m; a step > 2 m toward the handler counts as a rule violation.
- **Teams documented:** Michigan State (Izzo) practice drill, season not stated — https://www.coachesclipboard.net/MSUTransitionDrill.html `[DZ50]`.
- **Sources:** `[DZ50][DZ53]`.
- **Confidence:** medium.

---

### A11. Detection literature (extends F18)

#### X-1. Energy-based matchup HMM; unsupervised man/zone clustering — RICHER (extends F18.3)
- **Energy-based matchup HMM** (Keshri, Oh, Zhang, Iyengar; NESSIS 2017) `[DZ65]`: defender location given assignment follows Franks et al.; transitions among the 5⁵ = 3125 matchings are made tractable with **bond energies** — 1-on-1 on-ball and off-ball bonds and "extra" on-ball/off-ball bonds. A double team (extra on-ball bond) has higher energy and is unstable, so the model expects reversion to 1-on-1 → usable as a **trap-detector prior** (`TRAP` = extra on-ball bond persisting ≥ 0.6 s [HEURISTIC]). Events are detected with binary HMMs on simple emissions: screens (on-ball defender to potential screener distance, hoop–handler distance, screener speed), drives (handler velocity toward the hoop), post-ups (on-ball defender–handler distance and handler speed). 25 Hz SportVU — https://www.nessis.org/nessis17/Keshri_adj.pdf
- **Man vs zone clustering in football** (Dutta et al., arXiv 1906.11373) `[DZ66]`: unsupervised Gaussian mixtures and hierarchical clustering on tracking features separate man from zone coverage, labels assigned after viewing clusters; soft assignments allow mixed coverages. An analogue for labelling MSU possessions without hand labels, alongside the existing HMM analogue `[D36]` — https://arxiv.org/abs/1906.11373v3
- **Screen-detection literature checked:** McQueen 2014 (21 quarters, 14 games, 2012-13) and McIntyre 2016 (2011-12 to 2014-15) are summarised in `[N30]` https://arxiv.org/pdf/2311.16564 ; a pipeline outline links the McQueen PDF but gives no thresholds `[N29]` https://github.com/akashsebastian/Automatically-Detect-On-Ball-Screens. The McQueen thresholds themselves were not opened (404) — **unverified**.
- **Gap:** no basketball paper on automatic zone or press detection was found.
- **Confidence:** medium.

---

### A12. Counts (this section)

| Subsection | Items | New | Richer | Status-only notes (no item) |
|---|---|---|---|---|
| A1 Man principles (F1, F7) | 5 | 2 (M-2, M-5) | 3 (M-1, M-3, M-4) | — |
| A2 Ball-screen coverages (F3) | 15 | 7 (BS-2, BS-6, BS-8, BS-10, BS-11, BS-12, BS-13) | 8 (BS-1, BS-3, BS-4, BS-5, BS-7, BS-9, BS-14, BS-15) | BS-16 (catch, no screen, hedge-to-switch) |
| A3 Handoff coverages (F4) | 1 | 0 | 1 (H-1) | hedge-and-bounce (nothing new) |
| A4 Off-ball coverages (F5) | 3 | 1 (OB-1) | 2 (OB-2, OB-3) | hip-pocket trail, FIBA stagger rule (unverified) |
| A5 Zones and match-up rules (F8) | 10 | 4 (Z-1, Z-4, Z-5, Z-6) | 6 (Z-2, Z-3, Z-7, Z-8, Z-9, Z-10) | — |
| A6 Presses (F9) | 8 | 2 (P-1, P-2) | 6 (P-3 to P-8) | — |
| A7 Junk (F10) | 3 | 0 | 3 (J-1, J-2, J-3) | — |
| A8 Scheme changes (F11) | 7 | 6 (SC-1, SC-2, SC-3, SC-5, SC-6, SC-7) | 1 (SC-4) | — |
| A9 Transition defence (F12) | 7 | 3 (T-2, T-3, T-4) | 4 (T-1, T-5, T-6, T-7) | — |
| A10 MSU / Izzo (F1.6, F18.4) | 5 | 0 | 5 (MSU-1 to MSU-5) | — |
| A11 Detection literature (F18) | 1 | 0 | 1 (X-1) | — |
| **Total** | **65** | **25** | **40** | 4 notes |

Items with an MSU attribution: M-1, M-5, BS-5, BS-7, H-1, Z-5 (opponent vs MSU), Z-8 (opponent vs MSU), Z-10, P-5, SC-1, SC-5, SC-6, SC-7, MSU-1 to MSU-5 = 18. A new primitive table (A0) adds 13 primitives (11 original plus `RECOVER` and `STEP_RELEASE`, added in the 2026-10-17 fix pass). BS-2 counts as NEW for Down and jailbreak; its "quickest path" name is RICHER (`poa_quickest_path`, cf. F2.2).

---

### Additional sources (2026-10-18)

All URLs below were opened in the Job A research (2026-10-17) with WebFetch, or downloaded and text-extracted locally where noted. "= Dxx / Sxx re-opened" marks a source already in this file's lists.

**Man, ball-screen, handoff, off-ball (N keys)**
- **N1**: Hoop Student, "Ball line defense". https://hoopstudent.com/ball-line-defense
- **N2**: Eurohoops, "Basketball 101: pick-and-roll defense" (p. 3). https://www.eurohoops.net/en/trademarks/1409927/basketball-101-pick-and-roll-defense/3
- **N3**: Hooper University, "Ball screen defense: playing drop coverage". https://www.hooperuniversity.com/breakdowns/ball-screen-defense-playing-drop-coverage
- **N4**: Hooper University, "Ball screen defense: hard hedging ball screens". https://www.hooperuniversity.com/breakdowns/ball-screen-defense-hard-hedging-ball-screens
- **N5**: Medium Lights, "Scram switching". https://mediumlights.substack.com/p/scram-switching
- **N6**: Coach's Clipboard, "Basketball Switching Defense" (= D19 re-opened). https://www.coachesclipboard.net/basketball-switching-defense.html
- **N7**: Slappin' Glass, "The peel switch: a primer". https://slappinglass.substack.com/p/the-peel-switch-a-primer
- **N8**: Hoopscoop, Chris Filios, "The next defensive trend in basketball". https://www.mensbasketballhoopscoop.com/the-next-defensive-trend-in-basketball-by-chris-filios/
- **N9**: Slappin' Glass, "PnR defense: canceling screens". https://slappinglass.substack.com/p/pnr-defense-canceling-screens
- **N10**: The Basketball Playbook, Tom Izzo Michigan State playbook (PDF, text extracted locally). https://thebasketballplaybook.com/wp-content/uploads/2017/08/Tom-Izzo-Michigan-State-Playbook.pdf
- **N11**: Coaching Toolbox store, "All Access Michigan State basketball practice with Tom Izzo". https://onlinestore.coachingtoolbox.net/product/all-access-michigan-state-basketball-practice-with-tom-izzo/
- **N12**: Coaching Toolbox, "D1 Defensive Notes" (= D4 re-opened). https://coachingtoolbox.net/defense/d1-defensive-notes.html
- **N13**: UM Hoops, 2019 MSU breakdown (= S69 re-opened). https://umhoops.com/?p=102796
- **N14**: Inside the Hall, "Film session: Michigan State" (7 Jan 2015). https://www.insidethehall.com/2015/01/07/film-session-michigan-state/
- **N17**: Slappin' Glass, "Switch and Shrink: Barcelona's unique …". https://slappinglass.substack.com/p/switch-and-shrink-barcelonas-unique
- **N18**: Slappin' Glass podcast (Buzzsprout), "Hedge plug solutions …". https://www.buzzsprout.com/1288787/episodes/19494515-hedge-plug-solutions-learning-frameworks-and-european-film-sg-deep-dive
- **N19**: HoopTactics, back-screen defence (disruptive pressure). https://hooptactics.net/premium/defense/disruptivepressure/defscreensoff4back.php
- **N20**: Coaches Insider, "Defending screens". https://coachesinsider.com/mens-basketball/defending-screens-article/
- **N21**: Hoopscoop, DHO article (opened; no coverage content). https://www.mensbasketballhoopscoop.com/?p=11247
- **N22**: Cleaning the Glass, "How do NBA defensive rotations work?". https://cleaningtheglass.com/how-do-nba-defensive-rotations-work/
- **N23**: Hoop Student, "Basketball jump to the ball". https://hoopstudent.com/basketball-jump-to-the-ball/
- **N24**: Playbook Tech coaches community, Helpside I / 1/3–2/3 deny. https://fastbreak.playbooktech.com/coaches-community/?p=2195
- **N25**: Action Network, Creighton / Kalkbrenner film breakdown. https://www.actionnetwork.com/ncaab/college-basketball-film-breakdown-deep-dive-into-creighton-ryan-kalkbrenner
- **N27**: Hooper University, "How to ice ball screens". https://hooperuniversity.com/breakdowns/ball-screen-defense-how-to-ice-ball-screens
- **N28**: A Quick Timeout, "2 ball screen coverage adjustments". https://aquicktimeout.substack.com/p/2-ball-screen-coverage-adjustments
- **N29**: GitHub, "Automatically-Detect-On-Ball-Screens". https://github.com/akashsebastian/Automatically-Detect-On-Ball-Screens
- **N30**: arXiv 2311.16564 (PDF, text extracted locally; related work on screen detection). https://arxiv.org/pdf/2311.16564
- **N31**: MIT Sloan SSAC, "Recognizing and analyzing ball screen defense in the NBA" (abstract page). https://www.sloansportsconference.com/research-papers/recognizing-and-analyzing-ball-screen-defense-in-the-nba
- **N32**: Same paper, PDF (text extracted locally). https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc2208063d_Recognizing%20and%20Analyzing%20Ball%20Screen%20Defense%20in%20the%20NBA.pdf
- **N33**: PMC, 2019 FIBA World Cup ball-screen defence study. https://pmc.ncbi.nlm.nih.gov/articles/PMC9820029/
- **N34**: FIBA Europe, *Basketball Terminology* (= D10 re-opened; text extracted locally). https://assets.fiba.basketball/image/upload/documents-corporate-regional-offices-europe-programs-fiba-europe-coaching-certificate-fiba-europe-basketball-terminology.pdf
- **N35**: Coach's Clipboard, "Defending screens". https://coachesclipboard.net/basketball-defending-screens.html
- **N36**: Low Man Help, "The Blueprint: Pick and Roll 101" (= D49 re-opened). https://lowmanhelp.substack.com/p/the-blueprint-pick-and-roll-101?open=false
- **N37**: CoachTube, Izzo "Defensive skills and drills" course page. https://coachtube.com/course/basketball/defensive-skills-and-drills/118044
- **N38**: FastModel, "Tom Izzo — Jump to the Ball". https://playbank.fastmodelsports.com/library/basketball/fastdraw/68911/play-Tom-Izzo-Jump-to-the-Ball
- **N40**: Hoopscoop, Izzo Open Practice Series (= S6 re-opened). https://www.mensbasketballhoopscoop.com/?p=23659
- **N43**: Dylan Burkhardt, "Making sense of Michigan at Michigan State" (= D25 re-opened). https://dylanburkhardt.substack.com/p/making-sense-of-michigan-at-michigan
- **N44**: The Hoosier Network, IU–Purdue film preview (Feb 2023). https://thehoosiernetwork.com/article/2023/02/iubb-purdue-film-preview
- **N45**: Backyard Buckets, "Florida Atlantic's switching defensive …". https://backyardbuckets.substack.com/p/florida-atlantics-switching-defensive

**Zones, presses, junk, scheme changes, transition (DZ keys)**
- **DZ01**: TeamArete, 2-3 match-up zone. https://id3430.securedata.net/teamarete/23matchupzone.html
- **DZ02**: The Hoops Geek, "2-3 zone defense". https://www.thehoopsgeek.com/2-3-zone-defense-basketball
- **DZ03**: UM Hoops, "Film room: Oregon's matchup zone" (Dec 2019). https://umhoops.com/2019/12/13/film-room-breaking-down-oregons-matchup-zone-defense/
- **DZ04**: SI (Indiana), Woodson's switch to zone vs MSU (Feb 2025). https://www.si.com/college/indiana/basketball/mike-woodson-s-inspired-switch-to-zone-defense-against-michigan-state-pays-off-for-indiana-01jkxd7dckhz
- **DZ05**: Daily Bruin, scouting report vs Oregon (Jan 2022). https://dailybruin.com/2022/01/13/scouting-report-ucla-mens-basketball-vs-oregon-oregon-state/
- **DZ06**: Daily Northwestern, "Cats' season lives, dies by the zone" (Mar 2009). https://dailynorthwestern.com/2009/03/03/archive-manual/mens-basketball-cats-season-lives-dies-by-the-zone/
- **DZ07**: Daily Northwestern, "Zone boosts Cats' defense" (Nov 2010). https://dailynorthwestern.com/2010/11/18/sports/mens-basketball-zone-boosts-cats-defense/
- **DZ08**: Inside the Hall, IU zone beats MSU (Feb 2025). https://www.insidethehall.com/2025/02/12/iu-basketball-relies-on-zone-defense-total-team-effort-to-beat-no-11-michigan-state/
- **DZ09**: Spartan Avenue, Izzo dares teams to zone MSU. https://spartanavenue.com/tom-izzo-dares-teams-to-play-zone-against-michigan-state-basketball-moving-forward-01jm2ywh2zcb
- **DZ10**: Spartan Avenue, Izzo on not being 11-0 (Dec 2025). https://spartanavenue.com/tom-izzo-says-his-coaching-is-the-reason-michigan-state-isn-t-11-0-01kcs43bkpkj
- **DZ11**: SI (MSU), Izzo review after Oakland (Dec 2025). https://www.si.com/college/michiganstate/tom-izzo-drops-blunt-review-following-oakland-golden-grizzlie-game-
- **DZ12**: SI (MSU), MSU vs Iowa (Mar 2025). https://www.si.com/college/michiganstate/basketball/spartans-iowa-hawkeyes-big-ten-jase-richardson-jaden-akins-jaxon-kohler
- **DZ13**: SI (Penn State), MSU beats Penn State (Feb 2024). https://www.si.com/college/pennstate/basketball/penn-state-mens-basketball-michigan-state-spartans-defeat-nittany-lions-tom-izzo-mike-rhoades
- **DZ14**: Hawk Fanatic, McCaffery on the press (Feb 2023). https://hawkfanatic.com/?p=64664
- **DZ15**: UM Hoops, Ethan Sears, "Breaking down Iowa's defensive options against Michigan" (1 Mar 2018; 2017-18). https://umhoops.com/?p=93283
- **DZ16**: Hoop Student, "3-2 zone defense". https://hoopstudent.com/3-2-zone-defense/
- **DZ17**: Coaching Toolbox, Sharman White 3-2 zone. https://coachingtoolbox.net/teaching-the-3-2-zone-positioning-communication-rotations
- **DZ18**: Basketball for Coaches, "2-1-2 zone defense". https://www.basketballforcoaches.com/2-1-2-zone-defense/
- **DZ19**: Better Basketball (AU), "1-2-2 or 3-2 zone defence". https://betterbasketball.com.au/1-2-2-or-3-2-zone-defence/
- **DZ20**: Wikipedia, "Triangle-and-two defense". https://en.wikipedia.org/wiki/Triangle-and-two_defense
- **DZ21**: Hoop Student, "Diamond-and-1 defense". https://hoopstudent.com/diamond-and-1-defense/
- **DZ22**: Coaching Toolbox, Will Rey diamond-and-one / triangle-and-two. https://coachingtoolbox.net/?p=414
- **DZ23**: Hoop Student, "Triangle-and-2 defense". https://hoopstudent.com/triangle-and-2-defense
- **DZ24**: Basketball for Coaches, "2-1-2 press". https://www.basketballforcoaches.com/2-1-2-press/
- **DZ25**: NBC Sports, Huggins and "Press Virginia". https://www.nbcsports.com/college-basketball/news/a-shift-in-philosophy-led-bob-huggins-to-build-press-virginia
- **DZ26**: Hoopscoop, Travis Ford transition roles. https://www.mensbasketballhoopscoop.com/?p=20023
- **DZ27**: Lockdown Defense, "How OKC shut down Indiana's fast break". https://lockdowndefense.substack.com/p/how-okc-shut-down-indianas-fast-break
- **DZ28**: Coaching Toolbox, "Loading to the basketball" (Boisvert). https://coachingtoolbox.net/loading-to-the-basketball
- **DZ29**: Coach's Clipboard newsletter (18 Jun 2025), transition defence. https://www.coachesclipboard.net/newsletters/CCNewsLetter06182025.html
- **DZ30**: Hoop Student, "Transition defense". https://hoopstudent.com/transition-defense/
- **DZ33**: Eleven Warriors, Ohio State zone press film study (Feb 2016). https://www.elevenwarriors.com/ohio-state-basketball/2016/02/67852/hoops-film-study-the-evolving-effective-ohio-state-zone-press
- **DZ34**: Eleven Warriors, Ohio State's defensive switch (Feb 2015). https://www.elevenwarriors.com/ohio-state-basketball/2015/02/49530/ohio-state-looks-like-a-different-team-largely-due-to-its-defensive-switch
- **DZ35**: Spartan Avenue, MSU vs Oregon (Jan 2026). https://spartanavenue.com/tom-izzo-kur-teng-can-t-guard-my-99-year-old-mother-01kfgk0xf6np
- **DZ36**: Cracked Sidewalks, Purdue preview 2024-25. https://www.crackedsidewalks.com/2024/09/purdue-preview-2024-25.html
- **DZ37**: Cracked Sidewalks, Purdue preview 2025-26 (= S75 re-opened). https://www.crackedsidewalks.com/2025/10/purdue-preview-2025-26.html
- **DZ38**: ESPN recap, Syracuse vs MSU (Mar 2018). https://www.espn.com.au/mens-college-basketball/recap/_/gameId/401025873
- **DZ40**: Nittany Sports Now, Penn State's new look on defense (Jan 2025). https://nittanysportsnow.com/2025/01/penn-state-basketball-has-a-new-look-on-defense/
- **DZ42**: Coach's Clipboard, "1-3-1 match-up zone". https://coachesclipboard.net/MatchupZone131.html
- **DZ43**: Coach's Clipboard, "Match-up zone". https://www.coachesclipboard.net/MatchUpZone.html
- **DZ44**: Coaching Toolbox store, Jay Wright 1-2-2 and 1-1-2-1 pressure (recorded Spring 2015 Pittsburgh clinic, released 2016). https://onlinestore.coachingtoolbox.net/product/jay-wright-1-2-2-and-1-1-2-1-three-quarter-court-pressure-defense/
- **DZ45**: Coach's Clipboard, "2-2-1 zone press" (= D65 re-opened). https://www.coachesclipboard.net/221ZonePress.html
- **DZ46**: SI, Syracuse 2011-12 zone (Feb 2012). https://www.si.com/more-sports/2012/02/20/syracuse
- **DZ47**: Wikipedia, "Box-and-one defense". https://en.wikipedia.org/wiki/Box-and-one_defense
- **DZ48**: The Hoops Geek, box-and-1 roles. https://thehoopsgeek.com/basketball-plays/box-and-1-defense-roles-responsibilities/
- **DZ49**: theScore, NBA cross-matching. https://www.thescore.com/nba/news/3195631
- **DZ50**: Coach's Clipboard, MSU transition drill. https://www.coachesclipboard.net/MSUTransitionDrill.html
- **DZ51**: SI (MSU), Izzo ahead of Iowa (Feb 2020). https://www.si.com/college/michiganstate/basketball/tom-izzo-talks-michigan-state-basketball-ahead-of-the-iowa-hawkeyes
- **DZ52**: Coaching Toolbox, "D1 Defensive Notes" (= D4 re-opened). https://coachingtoolbox.net/defense/d1-defensive-notes.html
- **DZ53**: Coach's Clipboard, "Transition Defense" (= D85 re-opened). https://www.coachesclipboard.net/TransitionDefense.html
- **DZ54**: The Hoops Geek, 4-v-4 transition drill. https://thehoopsgeek.com/basketball-drills/4-v-4-transition-drill/
- **DZ55**: Coach's Clipboard, 4-on-4-on-4 drill. https://coachesclipboard.net/4on4on4Drill.html
- **DZ56**: GoCoogs, Oakland scouting (12 Nov 2025; 2025-26). https://gocoogs.com/?p=46293
- **DZ57**: Hoop Student, "Point zone defense". https://hoopstudent.com/point-zone-defense/
- **DZ59**: Coaching Idaho, "Let's talk some zone" (= D99 re-opened). https://coachingidaho.substack.com/p/lets-talk-some-zone
- **DZ60**: Bangor Daily News, Louisville beats MSU (Mar 2012). https://www.bangordailynews.com/2012/03/22/sports/louisville-knocks-off-top-seeded-michigan-state/
- **DZ61**: Wikipedia, "Amoeba defense". https://en.wikipedia.org/wiki/Amoeba_defense
- **DZ62**: SI (Arizona), Baylor 1-1-3 (= D75 re-opened; confirms the existing row). https://www.si.com/college/arizona/basketball/arizona-basketball-navigating-baylor-bears-1-1-3-zone-defense
- **DZ63**: Roundtable, MSU 89-59 exhibition vs UIW (Oct 2026). https://roundtable.io/sports/ncaa/michigan-state/game-day/michigan-state-shows-off-in-89-59-exhibition-win-over-uiw
- **DZ64**: ESPN, NCAA rule changes for 2015-16. https://www.espn.com/mens-college-basketball/story/_/id/13037928/ncaa-announces-rule-changes-2015-16-including-30-second-shot-clock-fewer-outs
- **DZ65**: NESSIS 2017, Keshri et al. (PDF, text extracted locally). https://www.nessis.org/nessis17/Keshri_adj.pdf
- **DZ66**: arXiv 1906.11373, unsupervised man/zone coverage clustering (NFL). https://arxiv.org/abs/1906.11373v3
- **DZ67**: Daily Northwestern, 1-3-1 tops Tubby's Minnesota (Jan 2009). https://dailynorthwestern.com/2009/01/19/archive-manual/mens-basketball-wildcats-1-3-1-zone-tops-tubby
- **DZ68**: GoPSUsports, Penn State defensive dominance (Nov 2023). https://gopsusports.com/news/2023/11/15/defensive-dominance-drives-penn-state-to-win
- **DZ69**: Bellisario Student Media, Penn State vs Morehead State (Nov 2023). https://bellisariostudentmedia.psu.edu/story/turnovers-free-throws-only-needed-for-penn-states-win-against-morehead-state
- **DZ74**: Wikipedia, "2024–25 Big Ten Conference men's basketball season" (opened in the 2026-10-17 fix pass; four schools including Oregon joined in 2024). https://en.wikipedia.org/wiki/2024%E2%80%9325_Big_Ten_Conference_men%27s_basketball_season
- **DZ72 / DZ73**: WVU Sports pages (2012, 2009) — opened, headline only, cited only to mark the WVU 1-3-1 claim **unverified**. https://wvusports.com/news/2012/12/22/22681_131465957237595816 ; https://wvusports.com/news/2009/3/2/14280_131441773651516892

**Opened but not cited for any claim:** N15 https://www.insidethehall.com/2016/02/16/film-session-michigan-state-3/5/ ; N16 https://umhoops.com/2019/03/07/michigan-can-improve-ball-screen-defense-vs-michigan-state/ ; N26 https://umhoops.com/2021/02/12/film-room-how-michigan-built-the-best-defense-in-the-big-ten-part-2/ ; N39 https://playbank.fastmodelsports.com/library/basketball/fastdraw/70227/play-Tom-Izzo-Arm-Chop ; N41 https://www.active.com/basketball/articles/2-defensive-drills-by-tom-izzo ; N42 https://www.wxyz.com/sports/michigan-state-defense-stifles-michigan-77-70 ; DZ31 https://coachesinsider.com/mens-basketball/defensive-transition-drill-with-brad-underwood-univ-of-illinois ; DZ32 https://spartanavenue.com/michigan-state-s-defense-in-the-first-half-of-big-ten-play-has-been-historic-01kfy2sjbxah (MSU No. 1 KenPom defence 2025-26, no scheme detail) ; DZ39 https://statsbywill.substack.com/p/the-slow-death-of-zone-defenses ; DZ41 https://hawkeyesports.com/news/2010/11/3/a-first-look-at-the-new-look-hawkeyes ; DZ58 https://coachmarchart.substack.com/p/match-up-zone-defense ; DZ70 https://www.psucollegian.com/sports/men_basketball/very-physical-and-very-aggressive-northwestern-defeats-penn-state-men-s-basketball-behind-turnovers/article_946a282e-0c0b-4458-94aa-155f26e3c512.html ; DZ71 https://mgoblue.com/news/2015/2/5/postgame_quotes_iowa_72_michigan_54

**Attempted, not opened (no claim rests on them):** theonlycolors.com (403), eu.detroitnews.com (402), msuspartans.com clips PDF (404), mgoblog.com State Report / Picture Pages / Oregon preview / hoop-math post (403), michigandaily.com switching article (429), wabc.fiba.com (DNS), breakthroughbasketball.com coverage, hip-pocket, down-screen, box/triangle/diamond and 2-3 pages (403), medium.com screen write-up (403), ece.engin.umich.edu (403), Sloan 2014 McQueen PDF (404), FastModel DHO progression (404), ncaa.com 2018 switching (empty), InsideNU 1-3-1 (403), NBC Sports Louisville 2012 (redirect), The Gazette Iowa pages (429), Cyclone Fanatic (403), Washington Times WVU (403), Daily Orange Syracuse press pages (403), hoopcoach.org McCaffery press (404), Hammer and Rails (403), PSU Collegian Nebraska/Rutgers (429), Hudl/FastScout support (404), 360Player drill (DNS), Rivals/On3 Indiana story (redirect).

---

### Corrections 2026-10-18

These notes correct or qualify text above this section. The original text is left unchanged; the merge reader should apply these notes when using it.

- **C-1 (F8.3 Amoeba row, "UNLV (Jerry Tarkanian, creator)"):** Wikipedia credits **Fran Webster** (Pittsburgh assistant) with developing the amoeba, refined in the 1970s with Charles Ridl and Tim Grgurich; Grgurich later joined Tarkanian at UNLV; Pitt used it in 1973-74 `[DZ61]`. Keep both attributions side by side: Webster/Pitt as origin per `[DZ61]`, Tarkanian as the coach most associated with it per `[D60]`.
- **C-2 (F8 hierarchy and F8.2 table, 2-1-2 listed under odd-front zones):** the 2-1-2 is a two-guard (even) front `[DZ18]`; it belongs under **F8.1 Even-front zones**. Z-3 uses F8.1.
- **C-3 (F3.1 drop thresholds and F18.2 rule 3, "drop ≥ 3.5 m, high drop 1–3.5 m"):** the sourced coaching depth for an ordinary drop is **1.83–3.05 m below the screen** `[N3]`. Use the bands in BS-9: high/level drop 0.6–1.83 m, standard drop 1.83–3.05 m, deep drop > 3.05 m or X-big at r ≤ 4.5 m. Flat hedge = depth 0–0.6 m **and** lateral offset into the handler's path ≥ 0.5 m (old F3.1); up to touch = \|λ\| ≤ 0.6 m **and** dist(X-big, screener) ≤ 1.0 m. All bands remain [HEURISTIC] except the 1.83–3.05 m range.
- **C-4 (F8.2 row "1-2-2 / 3-2" treated as one zone):** the 3-2 with a flat three-man top line is distinct from the 1-2-2 `[DZ16][DZ17]` and FIBA lists them separately `[D10]`. Use Z-1 (3-2) and Z-2 (1-2-2) as separate labels; the distinguishing feature is the top defender's height relative to the wings (≥ 1.5 m higher in a 1-2-2, within 1.0 m in a 3-2), at any line height 4.0 ≤ y ≤ 7.5 m; a high top (7.30, 90°) with wings left at the FT line extended is a 1-2-2 [HEURISTIC].
- **C-5 (F3 hierarchy, "Drop ─ variants: … 'catch' drop"):** no opened source defines a "catch" coverage (`[N34][N2][N36]` checked). Treat "catch" as **unverified**; do not train a label for it until a source or film definition exists.
- **C-6 (F1.6 "Positioning" row, drill name "Beat and Belt"):** the 2015 video listing says "Beat and Belt" `[N40]`; the Izzo course lists "Beat the Belt" `[N37]`. Both spellings are in use; treat them as one drill.
- **C-7 (F1.5 Virginia row, ball-screen default "Aggressive on the spectrum; no ice"):** one secondary source says Virginia **hard hedges every ball screen** (season not given) `[N4]`. This is consistent with "aggressive" `[D9]` and "no ice" `[D1]`, but it rules out a drop prior for Virginia. Confidence medium (single source).
- **C-8 (F1.6 "Positioning" row, "Three-Man DHO Switching suggests DHOs are switched"):** the drill teaches **two ways** to defend handoffs depending on the positions involved `[N40]`. The prior should be position-conditional (H-1), not "DHOs are switched". The two ways themselves remain **unverified**.
- **C-9 (F18.4 MSU usage index):** add MSU **2014-15 hedge-and-recover** (Schilling, Nairn) `[N14]`, the 2015 "multiple ball-screen coverages" listing `[N40]`, and the 2026-27 exhibition full-court press `[DZ63]`. (The 2017-18 no-1-5-switch vs Wagner `[N43]` is already in F1.6 and applies only to the F18.4 table, if that table lacks it.) See MSU-2 and MSU-4.
- **C-10 (F1.6 "Ball screens, 2024-25" row, source `[D24]`):** MGoBlog returned HTTP 403 during this research, so `[D24]` was **not re-confirmed**. The claim stands on the earlier pass only.
- **C-11 (§0.2 restricted-arc row "r = 1.22"):** confirmed for NCAA men since 2015-16, together with the 30 s shot clock and the 10 s backcourt count that does not reset after a stoppage in play (with few exceptions) `[DZ64]`.
- **C-12 (F12 transition, definition windows):** the Hoop-Math and FastScout transition definitions cited in the project brief were **not** opened in Job A (pages 403/404). They stay **unverified** in this file until Job D confirms them.
- **C-13 (F11.1 "Zone → man after a ball screen [UNVERIFIED]"):** still unverified after this research. The newly documented change triggers are a timeout after an opponent run (SC-1), a game-flow change-up (SC-2), the BLOB inbound (SC-5) and the late game (SC-7).
