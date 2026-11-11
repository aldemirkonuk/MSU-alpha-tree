# Player movement fingerprint (goal 9, added 11 Nov 2026)

Status: goal and design note, v0.1. Spec only; the build freeze stays. Owner request (Aldemir, 11 Nov 2026): "Add this as an additional goal, this is how I want to decipher certain movements and acts on players and so on."

## 1. The reference Aldemir pointed to

An "AI tennis coach" example: a player was measured against pros, then filmed themselves. Pose skeletons were extracted from the videos, each stroke was reduced to a set of named features (serve, forehand, backhand), and a heatmap compared the player against each pro, feature by feature (red and blue = above or below the pros). One feature stood out (the backhand take-back sat 0.93 farther out to the side than the pros' average), and the model then explained the real problem from that table. The pattern is: **pose, then named features, then comparison with a reference group, then the one or two features that really differ, then a plain-language explanation.**

## 2. What it means for MSU basketball

A **movement fingerprint** is, per player and per action type, a vector of pose features. Each feature is normalised to the player's body (height, limb lengths) and compared against a reference group and against the player's own history. Outputs:

1. A heatmap matrix: players (rows) by features (columns), grouped by action, coloured by robust z-score against position-matched peers.
2. A short list of outlier features per player, with the repetitions that show them (clips) and a skeleton overlay against the reference average.
3. A written explanation built **only from the numeric table** (feature, value, unit, reference, sample size, reliability), never from raw video, so every claim cites numbers.

The movement grammar already says **when and what** (screen, cut, closeout, shot windows with labels). Pose adds **how**. That split is the main reason this fits our stack.

## 3. Action types and candidate features (first catalogue, to be refined)

| Action | Example features (all pose-based, body-normalised) |
|---|---|
| Catch-and-shoot, pull-up, free throw | Load depth (knee angle), set-point height, elbow flare, hip/shoulder alignment to the rim, load-to-release time, release height, landing drift |
| Defensive stance and closeout | Stance width, hip height, torso lean, hands up (contest), last-step length, torso facing relative to ball and to man |
| Screen setting | Base width, still frames before contact, contact angle, first step after the screen (roll or pop direction) |
| Cuts and footwork | Plant-foot angle, cut angle, deceleration profile, jump-stop width, first-step timing |
| Ball handling | Dribble height, crossover width, torso posture relative to the defender |
| Rebounding and box-out | Box-out base and contact posture, jump timing |

Features that need 3D or very fine joint angles are included only if their test-retest reliability holds on broadcast video (section 6).

## 4. Pipeline

1. **Identity-locked tracks** (baseline 3; zero ID swaps is a hard dependency, because one swap puts another player's mechanics in a fingerprint).
2. **Pose per locked player:** 2D keypoints per frame, optional 3D lift, scale from court homography (named spots). Torso and limbs only; no face data.
3. **Action windows from the movement grammar** (events and labels), so each repetition is cut automatically.
4. **Feature extraction** with units and per-repetition uncertainty.
5. **Reference groups:** the roster plus position-matched peers. The 33 MSU games already show a few hundred opponent players on the same broadcasts, which gives a large peer group without new video. Peers are grouped by position and role only.
6. **Comparison:** robust z-scores (median and MAD) per feature against peers, plus drift of a player against their own earlier games.
7. **Outlier selection and explanation** as in section 2.

## 5. Data requirements

- Recording standard from the identity pack applies: 1080p at 59.94 fps for any game that feeds player-level numbers; below that, no fingerprint.
- Broadcast video has one moving camera, occlusion and 2D only, so only features robust in 2D are kept.
- At least 10 to 15 clean repetitions per player per action are needed for a stable value; fewer repetitions are reported as insufficient, not averaged.

## 6. Evaluation

- **Test-retest reliability:** the same player, same action, different possessions; keep features with intraclass correlation of at least 0.6.
- **Known-difference checks:** the fingerprint must rediscover differences we already know (left-handed vs right-handed shooters, big vs guard stance).
- **Staff agreement:** MSU coaches rate a sample of flagged outliers ("is this closeout too wide?"); report agreement, not accuracy claims.
- **Synthetic checks:** stick-figure motion with known feature values, at several noise levels, to test the extraction code.

## 7. Guardrails (standing project rules)

- No face data and no face-based identification.
- No race or ethnicity proxies: body-build features are used only to normalise, never to infer anything about a person, and peer groups use position and role, not body type.
- No health or injury inference: outputs describe mechanics only, never injury risk or medical claims.
- Individual player outputs are private to MSU staff; video stays private research material.

## 8. Honest limits

The tennis example used controlled clips filmed for the purpose. Game footage is uncontrolled, so expect only large, repeatable differences to be detectable. The first pilot must prove reliability before any more actions are built.

## 9. Phasing

1. Feature catalogue with exact definitions and units (this note, refined).
2. Pilot on **catch-and-shoot** (the most repeatable action with the best camera view) for a small set of players.
3. Reliability and known-difference checks; keep or drop features.
4. Only then add the next action type.

## 10. Decisions needed from Aldemir

1. Pilot action: catch-and-shoot first (recommended), or another action?
2. Which question matters most to MSU staff (shooting form, closeouts, screen setting)? That sets the first heatmap.
3. Can MSU staff (or ShotTracker) provide player heights and wingspans for normalisation?
