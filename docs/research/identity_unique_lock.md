# The unique parameter: what may lock a player's identity (11 Nov 2026)

Owner request: "find a parameter to detect that it's unique to the player and lock it in."
Sources in square brackets are listed in research.md. (own calculation) marks my arithmetic, not a published number.

## Answer

The lock is **team + jersey number, read twice independently on a pure tracklet**. Nothing else may create a lock.

- It is the only cue that is unique by rule: duplicate numbers on one team are not permitted, and the number is on the
  front and the back (Rule 1-22.7.b [R1]).
- It is printed on the player, public, and not a biometric, so it is clean under the privacy rules.
- Every published system that names players relies on it [J1][J2][J5][J6][J7][B1]; no published system names players
  from appearance, body shape or movement alone at broadcast distance.
- Its weakness is visibility (5.9 % of frames legible in hockey [J1], 12 % kept as keyframes in soccer [J3]), not
  uniqueness. Visibility costs coverage, which is the variable allowed to pay. Every other candidate fails on
  uniqueness or stability, which costs swaps, and those are not allowed.

Three roles, strictly separated:

| Role | Allowed cues | What it may do |
|---|---|---|
| CREATE a lock | Team + jersey number only | Bind a roster name to a tracklet: 2 independent legible full reads, or 1 read that agrees with an identity already held on that chain |
| MAINTAIN a lock | Position and motion continuity on a pure tracklet; the per-game appearance card and kit signature learned at verified reads; later the movement fingerprint | Carry an existing lock forward or back along a chain, and across a gap inside a closed candidate set. Never name a player who has no number anchor in the current stretch |
| VETO a lock | Team colour, body geometry, the on-court set with one label per player, kinematic reach, contact or overlap state, a contradicting number read | Demote to "unknown", block a create or a maintain. Never add support |

The asymmetry is deliberate: two reads to create, one contradicting read to demote. A wrong demotion costs seconds of
coverage; a wrong creation is a swap.

## What gets locked in: the per-game identity card

One card per player per game, opened by the first number anchor and filled only from frames within a short window of
verified reads on a pure, non-contact tracklet:

1. Anchor: team, number, the log of verified reads (time, front or back, crop size, score).
2. Appearance card: torso-and-legs embedding with skin and head masked, one prototype per view (front, back, side).
3. Kit signature: shoe colours, sleeves, tights, pads, socks as discrete fields.
4. Body geometry: shoulder-line height in court metres, shoulder width to height, leg to torso ratio. Head top is
   avoided so hair never enters the measurement.
5. Slot reserved for the movement fingerprint (empty, weight zero).

The card is scoped to one half. The season pack keeps only the number, body geometry and (later) the fingerprint,
because those are the fields that survive from game to game.

## Candidates

### 1. Team + jersey number

| Aspect | Assessment |
|---|---|
| Unique among five / fifteen | Yes / yes, by rule. With team, unique among all ten. One exception: 0 and 00 never share a roster [R1] |
| Stable in game / across games | Yes, except a blood-rule jersey change (Rules 3-6.3.b, 10-4.1.m [R1]): rare, reported to the scorer / yes within a season |
| Far side | Weak: about 11 px (back) and 8 px (front) at 1080p (own calculation). Practitioner report: most errors on far-side players [J8] |
| Motion blur | Weak. No published rate; 60 fps helps by halving exposure and doubling chances |
| Low bitrate | Weak; digits smear first. 720p gives about 10 px and 7 px (own calculation) |
| Back or side to camera | Back: good (6 inch number). Front: usable (4 inch). Side: none |
| Contact | Read may belong to the other player; must be attributed through the torso mask or discarded [J1][J8] |
| Cost | Pose torso crop, legibility classifier, digit reader on at most ten crops per frame; small models suffice (two-head ResNet on 32 x 32 [J6]) |
| Failure modes | Two-digit number read as one digit (dominant error [J1]; most rosters contain a collision, own calculation); the same misread repeating for seconds (tracklet votes still 7-21 % wrong [J1][J2]); shape confusions (1/7, 3/8, 6/8); read attributed to a neighbour; number changed by a jersey swap; classifier never trained on digits 6-9 in college kits [R2] |
| Published evidence | 92.85 % tracklet accuracy, soccer [J2]; 91.4 % per legible image, hockey [J1]; 93 % per crop, NBA clips, not reviewed [J8]. Nothing for college broadcast |

### 2. Per-game appearance card, learned only at verified number reads

| Aspect | Assessment |
|---|---|
| Unique among five / fifteen | No. Teammates share the kit; what differs is shoes, accessories, build and the number itself. Published rank-1 about 90 % uses unmasked crops and short gaps [A1][A3]; masked value unknown |
| Stable in game / across games | Minutes, then drifts with pose, light and sweat; one source shows re-ID falling from 98.0 to 33.0 over 300 frames [T7]. Not stable across games (shoes, kit variant), hence per game |
| Far side | Usable for coarse colour, weak for texture |
| Motion blur | Moderate; colour survives, texture does not |
| Low bitrate | Degrades; chroma is subsampled first |
| Back or side to camera | Works if the card holds a prototype per view |
| Contact | Contaminated by the neighbour; mask trackers drift to look-alikes in exactly this case [T6]. Excluded |
| Cost | One embedding per crop at 5 Hz; cheap |
| Failure modes | Two teammates with the same shoes and build; a card learned from the wrong person (prevented by learning only at verified reads on pure tracklets); a new substitute who resembles the player he replaced |
| Published evidence | The 2023 SoccerNet tracking winner fine-tunes re-ID on the unambiguous tracklets of the same video [J2]; the 2024 GSR winner merges by number first, appearance second [J6]. Both soccer |

### 3. Kit and equipment signature (shoes, sleeves, pads, socks)

| Aspect | Assessment |
|---|---|
| Unique among five / fifteen | Sometimes. It splits the five into groups; it rarely isolates one player. Team-issued shoes remove the strongest field |
| Stable in game / across games | Mostly stable within a half (a sleeve can come off, shoes can change at half-time) / no |
| Far side | Shoes about 20-30 px long at 1080p: colour only |
| Motion blur | Worst at the feet, which move fastest |
| Low bitrate | Saturated colours survive |
| Back or side to camera | Independent of orientation, which is its main value |
| Contact | Feet and arms are the first parts hidden |
| Cost | Colour statistics on pose-located regions; cheap |
| Failure modes | Same shoes on two teammates; accessory removed; sock and shoe colours merging with the floor |
| Published evidence | None quantitative. One paper remarks that shoes matter when kits are identical [A2] |

### 4. Body geometry in court metres

| Aspect | Assessment |
|---|---|
| Unique among five / fifteen | No. With 0.03 m effective error a player is unique by height among his five in 4 % of line-ups and 37 % of teammate pairs are separable at 3 sigma; at 0.02 m, 12 % and 56 % (own calculation) |
| Stable in game / across games | Yes / yes. The only cue that never changes |
| Far side | Coarser: one pixel is about 1.3 cm |
| Motion blur | Mild effect |
| Low bitrate | Mild effect |
| Back or side to camera | Independent of orientation |
| Contact | Invalid: feet or shoulders hidden, posture bent |
| Cost | Pose and homography, both needed anyway |
| Failure modes | Crouch, jump and landing (airborne players corrupt position and height [B5]); homography scale error shared by the whole frame; listed heights biased |
| Published evidence | 5.56 cm single-image error, close to guessing the mean [G1][G2]; 1.39 cm with a calibrated fixed camera and walking subjects [G3]. Nothing for a panning broadcast camera |

### 5. On-court set from substitutions, one-to-one among the five

| Aspect | Assessment |
|---|---|
| Unique among five / fifteen | It is a constraint, not an observation. It cuts fifteen to five and forbids one name on two bodies |
| Stable in game / across games | Changes at every substitution; rows are late, missing or wrong: 2.87 % of substitution windows with a detectable error in 50 NCAA games [P1]; 24 % of hand-checked rows wrong in Canadian university data [P2] |
| Hard cases | Unaffected by video quality. That is the danger: it answers when the video shows nothing |
| Cost | None |
| Failure modes | A late or missing row puts the departed player's name on his replacement; a bench player or a substitute at the table inside the frame; elimination naming "the fifth" when the fifth is not who the feed says |
| Published evidence | Roster constraint lifts hockey identification to 83 % [J7]; a hard cap of ten players halves id switches on a fixed camera [B2] |

### 6. Position and motion continuity

| Aspect | Assessment |
|---|---|
| Unique among five / fifteen | Perfect while the tracklet is pure, zero after any ambiguity |
| Hard cases | Fails at contact, merge, pan out of frame and cut, which are the cases at issue |
| Cost | None beyond the tracker |
| Failure modes | Swap at a crossing; a track resuming on whoever is nearby; hidden-person swaps |
| Published evidence | Best trackers still make thousands of id switches on SportsMOT [T1][T2][T3], about 40 per minute of footage (own derivation); court-plane association and splitting crossed tracklets are the measured remedies [B2][J2][T3] |

### 7. Movement fingerprint (parked goal)

| Aspect | Assessment |
|---|---|
| Unique among five / fifteen | Unknown. Walking gait in the wild reaches 60-82 % rank-1 among thousands [F1]; runners 43-53 % rank-1 [F2]. No team-sport evidence |
| Stable in game / across games | Plausibly stable across games; changes with fatigue and injury, which must never be read as a health signal |
| Hard cases | Independent of orientation and of the number; needs 1-2 s of clean pose; fails in contact; pose is weaker on the far side [B1][T4] |
| Cost | High: pose for every player at full frame rate plus a temporal model |
| How it plugs in | Fills slot 5 of the card. First as a MAINTAIN cue next to the appearance card (same closed-set and margin rules), then as a VETO. It may be promoted to CREATE only after a gold-sample test shows a calibrated error below the lock target. The design does not wait for it |

## Lock rules

CREATE (number anchor)
1. Two legible full reads of the same roster number on one pure chain, independent of each other: separated in time
   and taken from a different view (front and back, or a clear change of body orientation).
2. One read is enough when it agrees with an identity the chain already holds as a prior (a lock demoted at a
   substitution opportunity, or a closed-set candidate).
3. A one-digit read counts as a full number only when no teammate on the roster carries a two-digit number containing
   that digit, or the whole number area is seen clear of arms, folds and other players.
4. The read belongs to the chain only when the number box lies inside the chain's own torso region and inside no
   other person's box. No create while boxes overlap.
5. The number must be on that team's game roster. The play-by-play on-court set is a prior, not a filter.

MAINTAIN
1. Continuity along a pure tracklet and unique continuations, forward live and both ways offline.
2. Across a gap with no substitution opportunity (pan out of frame, short live cut, occlusion): the card may re-attach
   a lock when the candidates are a closed set of at most three unseen teammates, the margin to the runner-up is
   large, the pair is not on the confusable list, and no veto fires.
3. Through opponent-only contact: team colour on the mask keeps the two apart while the pair stays closed.
4. Across a substitution opportunity nothing is maintained except on a chain tracked without a break through the dead
   ball. Every other chain keeps its old identity as a prior and needs one agreeing read.

VETO
1. A legible full read of a different roster number: immediate demotion; a second independent read re-anchors.
2. Team colour of the other class on the mask, outside overlap.
3. Shoulder-line height off by more than the veto margin over enough upright frames.
4. The same name on two bodies: both demoted unless one holds a fresh anchor.
5. A name outside the on-court set: held back until two reads confirm it, then the line-up feed is corrected and logged.
6. Unreachable position for the claimed player given where he was last anchored.
7. A read of a number that is on nobody's roster entry (jersey change): the chain becomes "unknown number NN" and
   goes to review; it is never mapped automatically.

## How this answers the review findings

| Finding | Rule that closes it |
|---|---|
| Late or missing substitution row names the new player as the departed one | CREATE 5, MAINTAIN 4, VETO 1 and 5: a new chain after a dead ball needs a number read, and the replacement's number is not the departed player's |
| Tracklets not pure across crossings | Trajectory-level swap test and tracklet splitting on appearance change (proposals P15, P16); card learned only on pure stretches |
| The same misread accepted twice | CREATE 1: independence in time and view |
| 1 against 11 against 17 | CREATE 3 |
| Team-colour errors in runs | Colour from the mask, ignored in overlap, modelled as runs (P12) |
| A resumed track jumps to whoever is near | MAINTAIN 2 with every unseen teammate counted as a candidate (P11) |
| About 2 % locked labels in post and screen zones | MAINTAIN 3, set-valued labels for same-team contact, offline fill between anchors (P13, P14) |

## What this design gives up

- Live coverage after every dead ball until the first read: seconds near side, tens of seconds far side (model
  estimate, to be measured).
- Players whose number is hidden for a whole stretch between two dead balls stay "unknown" live and are filled
  offline only if an anchor exists on the same pure chain.
- Same-team contact yields a set of names, not one name per body.
