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
