# Player identity reference pack

Date: 2026-10-25. Version 0.1.1. Status: proposal under the build freeze (baseline 3 of 8). Every numeric value is an engineering proposal until measured on MSU film; the harness numbers below come from simulated cues on real NBA SportVU motion.

This page is generated from `config/identity_pack.yaml` and `results/identity_test/sportvu_harness.json` by `tools/specgen/identity/gen_doc.py` (prose from `tools/specgen/identity/doc_template.md`). Do not edit it by hand.

## 0. The rule and how to read this page

Aldemir's rule: **we cannot allow an ID swap**. A player's identity is locked when he enters the frame, kept through occlusions, re-checked after every crossing and released when he leaves the frame. When re-acquisition could fail, measurements (jersey number, team colour, build and height, gait) make the re-labelling exact.

How the spec reads that rule: a detection carries a player id only when the evidence makes that id near certain. Otherwise it carries **HOLD**, a short list of who it could be. A HOLD is lost coverage, never a swap. Coverage is pushed up as far as the evidence allows, but never by guessing.

- **Detection**: one person box in one frame, no id.
- **Tracklet**: boxes joined by motion only. It is cut at every doubt, so it never contains two people.
- **Chain**: tracklets joined where nobody else could have taken over. One chain carries one identity.
- **Encounter group**: the people who were too close to tell apart for a moment (a crossing, a screen, a pile-up). Who comes out is matched to who went in by cues, not by motion.
- **Lock**: the label of a chain once its probability reaches 0.995. It stays until the player leaves, the camera cuts, he is substituted, or the cues contradict it (an alarm).
- **Live** labels use only what has been seen so far. **Offline** (post-game) labels use the whole chain, before and after each frame. Reports use offline labels.

## 1. Results in one table

Three NBA SportVU 2015-16 games (G1, G2, G3; 157 minutes of tracked play) with true ids; ids stripped, noise, broadcast view, occlusions, cuts and simulated cues added (section 14). The spec (`full`, cue profile good) makes **0 swap events offline at sigma_p 0.15 m and 0 at 0.30 m** (acceptance ACC-H1: met). A standard tracker on the same detections makes 5072 (sigma_p 0.30 m).

**Cue profile `good`** (1080p main wide camera, normal arena light). Swaps are summed over the games; the scores are weighted by player boxes.

| Config | What it is | sigma_p (m) | Swaps offline | Swaps live | IDF1 offline | HOTA offline | Coverage offline | Coverage live | Re-confirm median (s) | Games |
|---|---|---|---|---|---|---|---|---|---|---|
| `naive_tracker` | standard tracker, labels kept once given | 0.15 | 3238 | 5248 | 0.689 | 0.543 | 0.717 | 0.692 | 0.16 | 3 |
| `naive_tracker` | standard tracker, labels kept once given | 0.30 | 5072 | 7143 | 0.616 | 0.468 | 0.664 | 0.631 | 0.36 | 3 |
| `naive_tracker` | standard tracker, labels kept once given | 0.50 | 8190 | 10554 | 0.512 | 0.371 | 0.584 | 0.560 | 0.72 | 3 |
| `motion_team` | pure tracklets + team colour | 0.30 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | - | 3 |
| `motion_team_lineup` | + PBP lineup | 0.30 | 0 | 0 | 0.000 | 0.000 | 0.000 | 0.000 | - | 3 |
| `plus_jersey` | + jersey numbers | 0.30 | 0 | 0 | 0.229 | 0.137 | 0.152 | 0.059 | 4.08 | 3 |
| `plus_appearance` | + torso/legs appearance | 0.15 | 0 | 0 | 0.612 | 0.451 | 0.521 | 0.283 | 1.76 | 3 |
| `plus_appearance` | + torso/legs appearance | 0.30 | 0 | 1 | 0.485 | 0.336 | 0.380 | 0.195 | 2.60 | 3 |
| `plus_appearance` | + torso/legs appearance | 0.50 | 1 | 0 | 0.297 | 0.186 | 0.206 | 0.097 | 4.08 | 3 |
| `full` | + height and gait (the spec) | 0.15 | 0 | 0 | 0.668 | 0.513 | 0.593 | 0.373 | 1.20 | 3 |
| `full` | + height and gait (the spec) | 0.30 | 0 | 1 | 0.563 | 0.404 | 0.463 | 0.276 | 2.24 | 3 |
| `full` | + height and gait (the spec) | 0.50 | 1 | 1 | 0.355 | 0.226 | 0.255 | 0.137 | 3.76 | 3 |
| `full_no_jersey` | spec without jersey numbers | 0.15 | 0 | 0 | 0.606 | 0.458 | 0.515 | 0.295 | 1.48 | 3 |
| `full_no_jersey` | spec without jersey numbers | 0.30 | 0 | 1 | 0.502 | 0.353 | 0.397 | 0.211 | 2.64 | 3 |
| `full_no_jersey` | spec without jersey numbers | 0.50 | 1 | 0 | 0.291 | 0.180 | 0.201 | 0.092 | 4.12 | 3 |
| `full_no_lineup` | spec without the lineup | 0.30 | 0 | 1 | 0.518 | 0.368 | 0.413 | 0.210 | 2.38 | 3 |
| `full_forced` | spec, but always emits its best guess | 0.15 | 1157 | 6762 | 0.778 | 0.641 | 0.762 | 0.701 | 0.36 | 3 |
| `full_forced` | spec, but always emits its best guess | 0.30 | 1590 | 6945 | 0.674 | 0.516 | 0.613 | 0.556 | 1.00 | 3 |
| `full_forced` | spec, but always emits its best guess | 0.50 | 2148 | 6076 | 0.477 | 0.324 | 0.383 | 0.339 | 2.48 | 3 |
| `naive_tracklets_full_catch` | standard tracker upstream + all cues, alarms, splits | 0.30 | 2518 | 2719 | 0.784 | 0.653 | 0.794 | 0.666 | 0.12 | 3 |

**Cue profile `poor`** (720p or low bitrate, dim arena, heavy motion blur). Swaps are summed over the games; the scores are weighted by player boxes.

| Config | What it is | sigma_p (m) | Swaps offline | Swaps live | IDF1 offline | HOTA offline | Coverage offline | Coverage live | Re-confirm median (s) | Games |
|---|---|---|---|---|---|---|---|---|---|---|
| `plus_appearance` | + torso/legs appearance | 0.15 | 0 | 1 | 0.077 | 0.045 | 0.047 | 0.016 | 3.92 | 3 |
| `plus_appearance` | + torso/legs appearance | 0.30 | 0 | 0 | 0.047 | 0.028 | 0.029 | 0.010 | 4.68 | 3 |
| `plus_appearance` | + torso/legs appearance | 0.50 | 0 | 0 | 0.020 | 0.013 | 0.012 | 0.004 | 5.92 | 3 |
| `full` | + height and gait (the spec) | 0.15 | 0 | 1 | 0.183 | 0.133 | 0.119 | 0.048 | 3.28 | 3 |
| `full` | + height and gait (the spec) | 0.30 | 0 | 0 | 0.142 | 0.103 | 0.091 | 0.036 | 4.08 | 3 |
| `full` | + height and gait (the spec) | 0.50 | 0 | 0 | 0.041 | 0.031 | 0.024 | 0.008 | 5.56 | 3 |
| `full_no_jersey` | spec without jersey numbers | 0.15 | 0 | 0 | 0.089 | 0.087 | 0.056 | 0.021 | 3.48 | 3 |
| `full_no_jersey` | spec without jersey numbers | 0.30 | 0 | 0 | 0.077 | 0.069 | 0.048 | 0.017 | 4.16 | 3 |
| `full_no_jersey` | spec without jersey numbers | 0.50 | 0 | 0 | 0.013 | 0.017 | 0.008 | 0.002 | 4.80 | 3 |
| `full_forced` | spec, but always emits its best guess | 0.15 | 3851 | 13676 | 0.706 | 0.559 | 0.712 | 0.650 | 0.64 | 3 |
| `full_forced` | spec, but always emits its best guess | 0.30 | 4632 | 12638 | 0.581 | 0.426 | 0.552 | 0.496 | 1.60 | 3 |
| `full_forced` | spec, but always emits its best guess | 0.50 | 4808 | 9797 | 0.371 | 0.243 | 0.327 | 0.282 | 3.04 | 3 |

**Cue profile `poor_uncalibrated`** (the poor recording read with the assigner still calibrated for good video (kappa_app, sigma_h, e_ocr not refitted)). Swaps are summed over the games; the scores are weighted by player boxes.

| Config | What it is | sigma_p (m) | Swaps offline | Swaps live | IDF1 offline | HOTA offline | Coverage offline | Coverage live | Re-confirm median (s) | Games |
|---|---|---|---|---|---|---|---|---|---|---|
| `plus_appearance` | + torso/legs appearance | 0.15 | 5 | 2 | 0.246 | 0.157 | 0.166 | 0.066 | 3.40 | 3 |
| `plus_appearance` | + torso/legs appearance | 0.30 | 2 | 1 | 0.154 | 0.095 | 0.099 | 0.036 | 4.40 | 3 |
| `plus_appearance` | + torso/legs appearance | 0.50 | 1 | 0 | 0.057 | 0.036 | 0.034 | 0.011 | 5.04 | 3 |
| `full` | + height and gait (the spec) | 0.15 | 4 | 2 | 0.440 | 0.299 | 0.333 | 0.155 | 2.64 | 3 |
| `full` | + height and gait (the spec) | 0.30 | 1 | 1 | 0.340 | 0.220 | 0.242 | 0.107 | 3.68 | 3 |
| `full` | + height and gait (the spec) | 0.50 | 1 | 0 | 0.144 | 0.091 | 0.092 | 0.036 | 4.76 | 3 |

**Probable tier** (owner decision OD-8: offline only, flagged, shown to viewers, never feeds stats; config `full`). Locked swaps and coverage are the locked tier's own numbers and do not change; probable errors are logged here and are not locked swaps.

| Cue profile | sigma_p (m) | Locked swaps | Locked coverage | Probable gain | Coverage with probable | Probable labels | Probable wrong | Probable error rate | Probable wrong runs |
|---|---|---|---|---|---|---|---|---|---|
| `good` | 0.15 | 0 | 0.593 | 0.102 | 0.694 | 176224 | 161 | 0.0009 | 13 |
| `good` | 0.30 | 0 | 0.463 | 0.084 | 0.547 | 145295 | 182 | 0.0013 | 14 |
| `good` | 0.50 | 1 | 0.255 | 0.064 | 0.319 | 111230 | 82 | 0.0007 | 10 |
| `poor` | 0.15 | 0 | 0.119 | 0.299 | 0.419 | 520839 | 957 | 0.0018 | 42 |
| `poor` | 0.30 | 0 | 0.091 | 0.202 | 0.293 | 349343 | 205 | 0.0006 | 18 |
| `poor` | 0.50 | 0 | 0.024 | 0.117 | 0.141 | 202977 | 118 | 0.0006 | 15 |
| `poor_uncalibrated` | 0.15 | 4 | 0.333 | 0.163 | 0.497 | 284367 | 3949 | 0.0139 | 148 |
| `poor_uncalibrated` | 0.30 | 1 | 0.242 | 0.131 | 0.373 | 227684 | 2272 | 0.0100 | 87 |
| `poor_uncalibrated` | 0.50 | 1 | 0.092 | 0.089 | 0.181 | 154937 | 1990 | 0.0128 | 86 |

What the columns mean: **swaps** = swap events, runs of frames where a player carries another player's id (or an official carries any id); the target is 0. **IDF1** and **HOTA** are the standard tracking scores (1 = perfect; they fall when boxes are left on HOLD). **coverage** = share of player boxes that carry an id. **re-confirm** = median seconds from the end of a true crossing until the player carries his correct id again.

- **Prevention, not repair.** The standard tracker extends tracks through crossings and keeps the first label: 5072 swap events at sigma_p 0.30 m. With the same detections and cues, pure tracklets, encounter groups and abstention give 0.
- **Catching after the fact is not enough.** Giving the standard tracker every cue, live alarms and offline change-point splits still leaves 2518 swap events (4654 splits applied): swaps must be prevented at the tracklet layer, and alarms and splits are the safety net.
- **Abstention is necessary.** The same spec forced to always emit its best guess makes 1590 swap events, with coverage 0.613 instead of 0.463.
- **Team colour and the lineup alone label nobody** (coverage 0.000 and 0.000): they only decide which five candidates a box can be.
- **Each identity cue adds coverage without adding swaps:** `plus_jersey` 0.152 (swaps 0); `plus_appearance` 0.380 (swaps 0); `full` 0.463 (swaps 0).
- **Dropping a cue costs coverage:** without jersey numbers 0.397 (swaps 0); without the lineup 0.413 (swaps 0).
- **Position precision sets the coverage.** At sigma_p 0.15 / 0.30 / 0.50 m the spec labels 0.593 / 0.463 / 0.255 of player boxes offline (swaps 0 / 0 / 1). Two players closer than about 4 sigma cannot be kept apart by motion, so their boxes wait on HOLD until a cue says who is who.
- **Poor video** (720p, dim, blur), assigner calibrated for it: swaps 0 / 0 / 0, coverage 0.119 / 0.091 / 0.024 at sigma_p 0.15 / 0.30 / 0.50 m: appearance no longer separates teammates, so almost every label waits for two jersey sightings.
- **Calibration is a safety rule, not a tuning detail.** The same poor video read with the good-video cue parameters makes 4 / 1 / 1 swap events (coverage 0.333 / 0.242 / 0.092): overconfident appearance evidence locks wrong labels. Cue parameters must be refitted per recording quality on labelled crops before any label is trusted.
- **Probable tier** (OD-8, offline, flagged, never in stats): at sigma_p 0.30 m on good video it adds 0.084 of player boxes (0.463 -> 0.547) with 182 wrong of 145295 probable labels (error rate 0.0013, 14 wrong runs); locked swaps unchanged.
- **Posterior calibration** (`full`, good, sigma_p 0.30 m, offline): posterior 0.995-0.999: 67747 labels, 0 wrong; posterior 0.999-0.9999: 97363 labels, 0 wrong; posterior 0.9999-1.0: 639310 labels, 0 wrong.
- Invariants ID-INV-1 to ID-INV-3 broken 0 times over every config and noise level.
- The cue error rates are assumptions (section 14); the real jersey read rate and OCR error on our recordings are the largest unknowns (open question OQ-3).

## 2. Standing constraints

- No face data of any kind (no face crops, face embeddings or face recognition), requirements line 742.
- No race or ethnicity proxies: skin tone, hair colour and hair texture are not cues and are masked out of appearance crops (torso and legs only, skin pixels removed).
- No private health data; injury or bandage status only from public reports, and tape/sleeves are appearance cues, not health labels.
- Player data limited to public information (roster, listed height, number) and what the broadcast shows.
- Generated or synthetic studio images (Nano Banana idea) are not identity references; they may only augment the team-colour classifier.

Forbidden as cues: `face`, `face_embedding`, `skin_tone`, `hair_colour`, `hair_texture`, `ethnicity`, `race`, `health_status`, `tattoos`.

**Zero swaps.** Owner decision 25 Oct 2026 (OD-8): zero swaps stays absolute for locked labels. Coverage is raised by planned work (planned_work), never by lowering p_lock; a separately flagged probable tier (assignment rule, offline only) may show more boxes to viewers but never feeds stats.

**Recording standard (ACC-R1).** Owner decision 25 Oct 2026 (OD-9): any game that feeds player-level numbers must be recorded at >= 1080p and >= 60 fps (59.94). Below that standard the game feeds team-level numbers only, or its player labels are shown probable-only (no locked labels, no player-level stats). Why: harness: on poor video (720p, dim, blur) locked coverage falls to 2-12 % of player boxes and an assigner not refitted for it swaps (profile poor_uncalibrated); 60 fps doubles jersey-read chances and halves motion blur (cues.jersey validity).

## 3. How others do it

Commercial in-arena systems (SportVU, Second Spectrum, Hawk-Eye) do not publish their identity methods; what is public is that optical tracking still relies on human operators to correct identities after close encounters, and that the academic broadcast pipelines combine tracklets that are pure by construction, team colour, rarely visible jersey numbers voted over tracklets, and a mutual-exclusion constraint (one player at most once per frame). We adopt all four, add the play-by-play lineup as a hard candidate constraint, make the re-confirmation after occlusions explicit (frame matching before and after), and add abstention so that no label is committed without evidence.

| Source | What it supports |
|---|---|
| [Lu, Ting, Murphy, Little. Identifying Players in Broadcast Sports Videos using Conditional Random Fields. CVPR 2011.](https://www.cs.ubc.ca/~murphyk/Papers/cvpr2011-camera.pdf) | broadcast NBA, faces about 15x15 px and numbers rarely visible; tracklets + appearance (colour, SIFT, MSER) + CRF with mutual-exclusion edges (a player appears once per frame); up to 85 % identification accuracy. Our joint per-frame posterior is the same exclusion idea solved exactly. |
| [Muller, Manger, Metzler. Recognition of Soccer Players after Occlusions using Temporal Color Signatures. IPCV 2011 (Fraunhofer IOSB).](https://publica-rest.fraunhofer.de/server/api/core/bitstreams/bf9096de-423b-4131-a081-7372ab0c5daa/content) | human operators correct tracker output after close encounters; merge-and-split handling re-assigns identities with appearance signatures gathered over many frames. Their cues include skin and hair colour, which we exclude (standing constraint). |
| [Hayashi et al. BasketLiDAR: LiDAR-camera multimodal dataset for professional basketball MOT. arXiv 2508.15299, 2025.](https://arxiv.org/abs/2508.15299) | occlusion sessions detected from the drop and return of the active-ID count; for each, the clearest frame before and after is searched and pre/post appearance features are matched (cosine) to restore IDs; this is our frame matching across occlusions (group -> children). |
| [Somers et al. SoccerNet Game State Reconstruction. CVPRW 2024, arXiv 2404.11335.](https://arxiv.org/html/2404.11335v1) | jersey number read per detection and majority-voted within each tracklet; GS-HOTA requires role, team and jersey to match. We vote per sighting, not per frame, because consecutive reads are correlated. |
| [Vats, Walters, Fani, Clausi, Zelek. Player Tracking and Identification in Ice Hockey. arXiv 2110.03090, 2021.](https://arxiv.org/abs/2110.03090) | team identification network about 97 %, player identification from box sequences 83 % with the game roster as a constraint; identity from roster + temporal evidence, not faces. |
| [Luiten et al. HOTA: A Higher Order Metric for Evaluating Multi-Object Tracking. IJCV 2021, arXiv 2009.07736.](https://arxiv.org/abs/2009.07736) | HOTA = sqrt(DetA x AssA); AssA isolates association (identity) quality; IDF1 over-weights association, MOTA over-weights detection. |
| [Ristani et al. Performance Measures and a Data Set for Multi-Target, Multi-Camera Tracking. ECCVW 2016, arXiv 1609.01775.](https://arxiv.org/abs/1609.01775) | IDF1, IDP, IDR from the optimal one-to-one matching of true and predicted identities. |
| [TrackID3x3 (3x3 basketball tracking with identification), 2025.](https://www.themoonlight.io/en/review/trackid3x3-a-dataset-and-algorithm-for-multi-player-tracking-with-identification-and-pose-estimation-in-3x3-basketball-full-court-videos) | identity annotated mainly by jersey number; ID switches under occlusion reported as the open problem (secondary review page, not the paper). |

Aldemir asked how broadcast providers (he named Peacock) do it. Streaming providers show tracking graphics bought from the league's in-arena vendor; no public document describes their identity logic. ShotTracker (MSU's in-arena system) uses wearable sensors, so identity there is hardware-assigned; if MSU staff share it, it is the best identity truth for NCAA film and the gold sample below should use it.

## 4. Design principles

| Id | Rule | Why |
|---|---|---|
| DP1 | Abstain rather than guess. A label is emitted only when its joint posterior is >= p_lock; otherwise the detection carries HOLD with its candidate set. | zero swaps is a hard requirement; coverage is the variable that pays for it. |
| DP2 | Tracklets are pure by construction. The motion tracker cuts every tracklet involved in an ambiguity (pair-swap test, merge, nearby miss, camera cut) instead of guessing through it. | a standard tracker that extends tracks through crossings is where swaps are born (harness config naive_tracker shows it). |
| DP3 | Identity is a constrained labelling of chains, not a property of the tracker. Constraints are hard - team, on-court lineup, one label per person per frame, at most five labels per team per frame. | the lineup turns a 13-way choice into a 5-way choice and makes elimination possible (four locked teammates leave one label). |
| DP4 | Re-confirm after every crossing. Teammate crossings - children of a group inherit only the mixture of the group's identities and must be confirmed by their own cues before a label is emitted again. Opponent crossings - re-confirmed on every frame by team colour (colour veto, per-box colour HOLD, class alarm) and still recorded as split points. | Aldemir's lock-and-keep rule needs a re-check at exactly the moments where a keep would be a guess. |
| DP5 | Lock from entry to exit. A locked chain keeps its label through unambiguous gaps; the identity is released on frame exit, camera cut, substitution or long loss. | the owner rule (lock on entry, release on exit). |
| DP6 | Every label change is logged with its evidence; a swap alarm (locked label contradicted by cues) demotes the chain, splits it at the last close encounter and sends it to review. | requirements - every identity switch logged and reviewed. |
| DP7 | Offline (post-game) labels use the whole chain's evidence, both before and after each frame; live labels use evidence so far. Both are scored; reports use offline labels. | frame matching after the occlusion corrects provisional live labels retroactively. |

## 5. The reference pack

One pack per player per season, plus one appearance card per player per game and one kit card per team per game. The pack holds measurements and broadcast crops (torso and legs, skin masked); never faces.

**Per player, per season.**

| Field | Type | Source | Why |
|---|---|---|---|
| `player_id` | string | roster registry (ESPN/CBBD id crosswalk) | join key |
| `team_id` | string | roster | team constraint |
| `jersey_number` | string | official roster; checked against the box score each game | strongest single cue; '00' and '0' are different numbers |
| `jersey_history` | list of (number, from_date, to_date) | roster changes | numbers can change mid-season |
| `listed_height_m` | float | public roster | build prior; listed heights are biased up by about 0.02-0.05 m, so only relative height within the floor is trusted |
| `measured_height_m` | float | median over confirmed broadcast frames with court calibration (standing, upright pose only) | replaces the listed height after >= height_min_frames confirmed frames |
| `build_index` | float | shoulder width / height from pose on confirmed frames | separates same-height teammates; no body-composition or health inference |
| `gait_signature` | vector | pose keypoints on confirmed running frames (stride frequency, stride length / height, arm swing amplitude) | weak cue that works with the back turned and the number hidden |
| `shooting_hand` | enum [left, right, unknown] | confirmed shots | role-context cue; tie-breaker only |
| `reid_template` | vector (embedding of torso and legs, skin masked) | mean of 50-200 confirmed broadcast crops per season (labelling loop) | appearance cue for same-kit teammates |
| `crop_bank` | list of crop ids with game, frame, pose, view (front/back/side) | labelling loop | re-training and audits; private, never committed |
| `headshot_ref` | url | ESPN | human checking of labels only; never a model input (no face data) |

**Per player, per game (appearance card). Filled at tip-off, at every substitution entry and after every camera cut, from the first confirmed frames of each player (warm-up shirts excluded) - the per-game lock of appearance Aldemir asked for.**

| Field | Type | Source | Why |
|---|---|---|---|
| `shoe_colour` | Lab colour (2 dominant) |  | changes game to game; strong within-game cue |
| `sleeve` | enum [none, left, right, both] + colour |  | within-game appearance cue |
| `headband` | enum [none, headband, bandana] + colour |  | within-game accessory cue |
| `tights_or_knee_sleeve` | enum [none, left, right, both] + colour |  | within-game cue |
| `tape_or_wrist` | enum [none, left, right, both] |  | within-game cue; never interpreted as an injury |
| `game_template` | vector |  | reid_template updated with the first confirmed crops of this game (season template + game delta) |
| `confusable_pairs` | list of (player_id, player_id) |  | teammates the soft cues cannot separate (assignment.confusable_rate); a lock between them needs jersey evidence (twin_jersey_nats); refreshed with the game templates |

**Per team, per game (kit card).**

| Field | Type | Source | Why |
|---|---|---|---|
| `kit_colour_primary` | Lab colour |  | team classifier centre, normalised per arena |
| `kit_colour_secondary` | Lab colour |  | trim and numbers |
| `number_colour` | Lab colour |  | number detector contrast |
| `uniform_variant` | enum [home_light, road_dark, alternate, throwback] |  | hard case uniform variants |
| `arena_colour_norm` | 3x3 matrix + offset |  | lighting and floor glare normalisation per arena |

Privacy: the pack lives in the private store; the repo holds only this schema. Crops are broadcast-derived and copyrighted (research use only).

## 6. Cues

The system checks the cues in this order. No single cue carries an identity; each adds evidence (in nats, natural-log units: +2.3 nats = ten times more likely).

### 6.1 `team_colour`

- **Observation:** per detection, a class in {team_A, team_B, official_or_other} from kit colours clustered per game after arena normalisation; no labels needed.
- **Model:** P(obs = true class) = 1 - e_team; errors spread evenly over the other classes.
- **Valid when:** skipped on frames flagged merged (two people in one box).
- **Hard cases:** same number on both teams (team decides first); referees and staff (class official_or_other); uniform variants; arena lighting

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `e_team` | 0.03 | probability | assumed classifier error at broadcast distance after arena normalisation (hockey team-ID reports about 3 %; Vats et al. 2021) |
| `tau_team` | 0.5 | 1 | consecutive frames of one person share lighting and pose |
| `p_team` | 0.999 | probability | a chain joins a team's assignment only above this class posterior; below it the chain stays HOLD (referee, coach, mascot, mixed box) |

### 6.2 `lineup`

- **Observation:** the five players of each team on the floor from play-by-play substitutions (CBBD / ESPN PBP), plus the starting five.
- **Model:** hard candidate constraint; inside a substitution window the candidates are the union of outgoing and incoming players and the five-count is relaxed.
- **Valid when:** live play only; during dead balls the bench, warm-up shirts and shooting shirts may be in frame (class official_or_other or bench zone).
- **Hard cases:** substitutions during dead balls; injury or blood exits pending replacement; PBP substitution missing or late

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `sub_window_s` | 8.0 | s | PBP substitution times can lag or lead the real change by a few seconds (R-DQ-09 says 1 s for timing, but subs are logged at the dead ball, not when the player steps on); the window must cover the worst lag |
| `lineup_check_interval_s` | 2.0 | s | how often the emitted labels are compared with the PBP lineup (per-possession agreement output) |

### 6.3 `jersey_number`

- **Observation:** a read (full number or partial single digit with its position) from the front or back of the jersey, with the OCR score; a sighting is a run of consecutive reads of the same detection chain without a gap > sighting_gap_s.
- **Model:** Each sighting contributes once (its reads are correlated): full read r -> P(r | n) = 1 - e_ocr if r == n, else e_ocr x conf_share(r, n), where confusable digit pairs (1/7, 3/8, 6/8, 5/6, 0/8, 1/4) get confusable_share of the error mass and every other number shares the rest; partial read d -> P(d | n) = (1 - e_ocr) / len(digits(n)) when d is a digit of n, else e_partial. Reads below ocr_min_score are discarded (counted for the read-rate metric).
- **Valid when:** no reads while the detection is merged; both front and back count (NCAA rule 1-22 requires numbers front and back); sighting rates fall with distance from the camera, back-or-side orientation and motion blur (prefer 60 fps recordings).
- **Hard cases:** number partly hidden (partial reads kept); folded jersey; back turned; small players far from camera; motion blur at 30 fps; same number on both teams

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `e_ocr` | 0.1 | probability | assumed full-read error after the score gate at 1080p; SoccerNet and Basket-AI report about 79-90 % read accuracy, so 10 % is the planning value until measured on MSU film |
| `confusable_share` | 0.5 | probability | half of OCR errors go to a visually confusable number (digit shape pairs); the rest spread uniformly |
| `e_partial` | 0.05 | probability | probability of a partial digit that is not in the true number (fold |
| `sighting_gap_s` | 0.2 | s | reads closer than this are the same view of the jersey and are counted once |
| `tau_jersey` | 1.0 | 1 | sightings are already de-correlated |
| `sighting_cap_nats` | 4.0 | nats | one sighting may favour a number by at most this (about 55:1); a single confusable misread (8 read as 3) must not lock an identity on its own - two agreeing sightings, or one sighting plus appearance or a group prior, are needed (SportVU harness, review round 1) |
| `ocr_min_score` | 0.5 | score | reject gate for the OCR head; measured read rate and error are reported above this gate |
| `min_readable_px` | 18 | px number height | proposal; requirements line 157 says the minimum readable size is measured, not assumed - the measurement replaces this value |

### 6.4 `height_build`

- **Observation:** standing height from the calibrated image scale (head top to floor contact) on upright frames, every cue_stride_s; build index from pose.
- **Model:** robust likelihood (1 - o) N(h_obs; h_ref, sigma_h) + o U(h_lo, h_hi); posture outliers (bent, jumping, landing) fall in the outlier term.
- **Valid when:** only frames with court calibration confidence >= 0.8 and an upright pose; not on merged frames.
- **Hard cases:** same-team same-build pairs (height alone never decides); mid-jump; on the floor

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `sigma_h` | 0.06 | m | height from a calibrated broadcast frame at 1080p: about 3-4 px of 200 px for a 2 m player, plus foot-contact error |
| `outlier_h` | 0.2 | probability | share of frames whose height is posture-corrupted (crouch |
| `h_lo` | 1.5 | m | outlier support lower bound |
| `h_hi` | 2.4 | m | outlier support upper bound |
| `tau_height` | 0.3 | 1 | consecutive height estimates share calibration and pose error |
| `height_min_frames` | 30 | frames | confirmed upright frames before measured_height_m replaces the listed height |

### 6.5 `appearance_reid`

- **Observation:** a re-ID embedding of the torso and legs crop (skin pixels masked, head excluded), every cue_stride_s; compared with the player's game template (season template + game card).
- **Model:** von Mises-Fisher-like LL = tau_app x kappa_app x cos(e_obs, template); constants cancel across labels.
- **Valid when:** not on merged frames; crops below min_crop_px tall are skipped.
- **Hard cases:** same-team same-build pairs; warm-up and shooting shirts; uniform variants; arena lighting

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `kappa_app` | 20.0 | 1/cos | concentration of the per-sample embedding around its template; refit on MSU crops (the harness uses the simulator's own value) |
| `tau_app` | 0.25 | 1 | consecutive crops of one player are strongly correlated (same pose |
| `template_min_crops` | 20 | crops | a game template needs this many confirmed crops before it replaces the season template |

### 6.6 `gait_posture`

- **Observation:** a short gait descriptor (stride frequency, stride length / height, arm swing) from pose over the last 1 s while the player runs; posture class (upright, crouched) for the height gate.
- **Model:** weak vMF-like LL = tau_gait x kappa_gait x cos(g_obs, g_ref); only when speed >= gait_min_speed_mps.
- **Valid when:** running frames only; not on merged frames.
- **Hard cases:** jersey hidden; back turned

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `kappa_gait` | 2.0 | 1/cos | gait is weak at broadcast resolution; it may only tip a decision when other cues agree |
| `tau_gait` | 0.3 | 1 | overlapping 1 s windows |
| `gait_min_speed_mps` | 2.0 | m/s | below a jog |

### 6.7 `role_context`

- **Observation:** who brings the ball up, who sets screens, shooting hand.
- **Model:** not used for assignment in 0.1.0 (it would make identity depend on the labels it feeds); kept as a review-queue hint only.
- **Valid when:** review hints only.

_No parameters._

### Common to all cues

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `cue_stride_s` | 0.2 | s | appearance |
| `merged_box_iou` | 0.5 | IoU | a box overlapping another person's box above this is flagged merged and gives no cues |

## 7. Tracklets, chains and assignment

### 7.1 Tracklets

Motion-only linking of detections frame to frame with a pair-swap likelihood test; any track involved in an ambiguity is cut, so tracklets are pure.

```text
Per frame: predict each active track with an alpha-beta (constant-velocity) filter; cost = squared distance to each
detection; gate = gate_base_m x gap + gate_k x sigma_pair (sigma_pair = max(sqrt(2) x sigma_p, sigma_floor_m), grown
with the gap); Hungarian assignment.
PAIR-SWAP TEST: for every two assigned pairs (track i -> det j, track k -> det l), the log-likelihood ratio of the
swapped assignment is LLR = [c(i,l) + c(k,j) - c(i,j) - c(k,l)] / (2 sigma_pair^2); LLR < swap_llr_min fails.
MERGE TEST: a track without a detection, or matched to a merged / no-cue box, fails together with every track within
merge_base_m + merge_k x sigma_pair (two people in one box, or a person hidden behind another).
ENCOUNTER GROUP: a track that fails a test ends its clean tracklet (reason ambiguous) and continues as an amb segment
(motion kept, identity unknown, never labelled); failing pairs join one encounter group (union of the identities that
entered it, including tracks that vanished inside it). A track that passes every test for clear_s leaves the group
as a new clean tracklet whose explicit parents are all identities that entered the group (it must be re-confirmed).
This replaces cutting at every frame of a long close encounter (a defender 1 m from his man would otherwise create
a new tracklet every frame).
JUMP TEST: a one-frame innovation above jump_k x sigma_pair moves the track into an encounter group (with every
person that vanished within reach). CONTESTED DETECTION: a matched detection near the predicted position of a
same-class person that vanished less than contest_s ago does the same. NEWCOMER: a detection that starts a new
track within the merge radius of a tracked person makes both ambiguous.
COLOUR: an opponent pair (both tracks confidently of different classes) is not cut by the pair-swap or merge
test; team colour separates them, and a detection whose observed class contradicts its track's class during such an
encounter (colour veto) makes the pair ambiguous. Every encounter is still recorded as a candidate split point.
LEADING GUARD: a new track that starts from a detection with another detection within isolation_m starts as an amb
segment (group = identities that vanished within reach) and becomes clean after clear_s; TRAILING GUARD: a track
that is lost next to another detection gives its last clear_s detections to an amb segment.
DECISION DELAY: entering a group moves the last clear_s detections of the clean tracklet into the amb segment, so a
swap made up to clear_s before a test fires never reaches a labelled tracklet (labels are emitted clear_s late).
NO COASTING (pure): an unmatched track ends (lost, or fov_exit within fov_edge_m of the frame edge); the chain linker
decides any continuation.
CAMERA CUT: every track ends (reason cut); no link crosses a cut.
```

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `gate_base_m` | 0.6 | m | at 10 m/s a player moves 0.33 m per frame at 29.97 fps (0.4 m at 25 Hz); the base covers it |
| `gate_k` | 4.0 | sigma | 4 sigma of pair noise keeps the miss probability below 1e-3 |
| `swap_llr_min` | 9.2 | nats | ln(1e4): a pair is kept only when the swapped assignment is 10,000 times less likely; a cut costs coverage, a swap is forbidden |
| `jump_k` | 3.0 | sigma | JUMP TEST: a matched detection more than jump_k x sigma_pair from the one-frame prediction is a jump (the box moved to another person whose own box was hidden); the track enters an encounter group with every person that vanished within reach |
| `merge_base_m` | 1.0 | m | two box centres closer than about 1 m merge in the broadcast view |
| `merge_k` | 3.0 | sigma | noise margin on the merge distance |
| `contest_s` | 0.5 | s | a matched detection near the predicted position of a same-class person who vanished less than this ago is contested (the hidden person re-appears in this track's box while its own person is hidden); longer losses are handled by the chain linker |
| `v_err_mps` | 1.5 | m/s | velocity error of the alpha-beta filter at the moment a track is lost; the vanished person's position sigma grows as sigma_pair + (v_err t + a_max t^2 / 2) / 3 |
| `contest_prior_nats` | 5.3 | nats | prior log-odds against the hidden-person swap at a given frame: P(own box missing) about 0.05 x P(the hidden person re-appears in this frame) about 0.1; the detection is contested when log N(own track) - log N(vanished person) + this < swap_llr_min |
| `a_max_mps2` | 6.0 | m/s^2 | a player cannot deviate from his predicted path by more than about a_max t^2 / 2 (sprint starts and cuts reach 5-7 m/s^2) |
| `isolation_m` | 2.5 | m | nobody else this close means a gap cannot hide a swap |
| `coast_max_s` | 0.0 | s | pure tracklets never coast (a gap ends the tracklet; the chain linker decides the continuation with the isolation tests); the naive tracker coasts link_window_s |
| `clear_s` | 0.12 | s | a track leaves its encounter group after passing every test for this long (3 frames at 25-30 fps); shorter re-enters on noise |
| `pos_alpha` | 0.6 | 1 | alpha-beta filter position gain: smooths position noise for prediction while following sharp cuts within a frame or two |
| `vel_beta` | 0.05 | 1 | alpha-beta velocity gain; per-frame differences of a 0.3 m noisy position are about 10 m/s, so velocity must be heavily smoothed |
| `sigma_floor_m` | 0.1 | m | minimum pair sigma in the swap test (filter lag on sharp cuts is about 0.1 m even with exact positions) |
| `fov_edge_m` | 1.5 | m | tracks ending this close to the frame edge are treated as leaving the frame |

Outputs: tracklet_id, start_frame, end_frame, end_reason (cut | ambiguous | lost | fov_exit | end), amb (encounter segment), encounter_group, explicit_parents, encounter_frames.

### 7.2 Chains

Tracklets are joined into chains only by unambiguous continuations; all other starts receive a mixture prior from the group that may contain them.

```text
A clean tracklet that leaves an encounter group has explicit parents (the group's identities). Any other new
tracklet starting at frame s at position p takes as parent candidates the tracklets that ended within link_window_s
before s (no camera cut in between, not ended by fov_exit) whose last position is within reach = reach_base_m +
v_max_mps x gap + 3 sigma_pair of p; an amb segment in reach contributes all identities of its group.
UNIQUE CONTINUATION: no explicit parents, exactly one parent candidate, that parent has exactly one child candidate,
the parent ended with reason lost, and both the parent's last detection and the new first detection are isolated
(no other detection within isolation_m in that frame) -> the tracklet joins the parent's chain (lock inherited).
GROUP CHILD: otherwise a new chain with prior = (1 - leak) x mean over parent chains of their posterior at their
end + leak x uniform over the on-court candidates of the class (adaptive leak, see leak_eps). No parents (start, after a cut, frame entry):
uniform prior.
AMB SEGMENTS are chains of their own, never labelled (HOLD with the group as candidate set).
FOV ENTRY: a chain that starts within fov_edge_m of the frame edge has no parents (released identities are not
inherited across an exit; entering players are re-acquired by cues).
```

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `link_window_s` | 1.5 | s | longest occlusion that is still bridged by a group prior; longer losses re-acquire from scratch |
| `reach_base_m` | 1.0 | m | body width |
| `v_max_mps` | 9.0 | m/s | top sprint speed of D-I players is about 9-10 m/s |
| `leak_eps` | 0.1 | probability | ADAPTIVE LEAK: prior mass left for an identity that was not in the group = leak_min + leak_eps x (team candidates not visible anywhere in the frame) / (team candidates). A teammate who is not on screen may be hiding behind someone; 0.02 everywhere let a group child lock on the group prior plus noise when a hidden teammate stepped out (SportVU harness) |
| `leak_min` | 0.002 | probability | leak when every candidate of the team is visible (nobody can be hiding); at 0.002 a one-identity group child (opponent crossing, solo merge) keeps a prior of 0.998 and stays above p_lock under the joint constraint on team colour alone |

### 7.3 Joint assignment

Per frame and per team, the joint label posterior of all visible chains of that team over the on-court candidates under one-person-one-label; labels are emitted only above p_lock.

```text
Chain score S[c, L] = log prior(c, L) + sum over the chain's cue samples so far (live) or over the whole chain
(offline) of the tempered cue log-likelihoods. Live prior = the group mixture of the parents' joint marginals at
their end; offline prior = forward mixture (parents) x backward mixture (children), each direction computed from
its own side only so no cue is counted twice. Jersey sightings are capped at sighting_cap_nats each. Class: a chain enters team T's problem when its class posterior for T
>= team_colour.p_team; otherwise it is HOLD.
Candidates: the on-court players of T from the PBP lineup; inside a substitution window, the union of outgoing and
incoming players. When the chains outnumber the candidates, dummy labels with score log(dummy_eps) absorb the extras.
Joint posterior: P(c -> L) = sum over injective maps of chains to labels containing (c -> L) of exp(sum S) / Z,
enumerated exactly (<= 2,520 maps for 5 chains and 7 candidates). When the map count exceeds max_enum (pile-ups with
many fragments), each chain's posterior is its own softmax and the Hungarian MAP enforces exclusivity (logged).
Because the joint marginals of one label sum to <= 1 over chains, at most one chain can hold a label above 0.5: two
chains can never emit the same label in a frame (checked by invariant ID-INV-1).
LOCK (live) / EMIT (offline) needs all of: joint posterior >= p_lock; chain margin (S without the one-label
constraint) >= min_evidence_nats; own-cue support (at least one cue sample of the chain's own and its own cues favour
the label by >= own_margin_nats); for a label with a confusable teammate among the candidates, own jersey evidence
>= twin_jersey_nats against that teammate; the box itself is not merged and does not show another team's colour.
Offline label of a chain: the label with the highest mean marginal over its frames, emitted on the frames where all
the conditions hold (one label per chain, so no within-chain flicker).
PROBABLE TIER (owner decision 25 Oct 2026, OD-8; offline only, never live): on a frame of that chain where the lock
conditions fail, the same label is emitted as a separate, flagged probable label when joint posterior >= p_probable,
chain margin >= probable_min_evidence_nats, own cues (>= one sample) favour it by >= probable_own_margin_nats and the
jersey evidence against a confusable teammate is >= probable_twin_jersey_nats. A probable label never repeats a locked
or another probable label in the frame (dropped to HOLD). It lives in its own output field: the locked label field,
swap_events, idsw, IDF1, HOTA, coverage and every stat read locked labels only; probable labels are shown to viewers
flagged as probable, and a wrong probable label is logged (harness: probable_wrong_frames / probable_wrong_events)
but is not a locked swap.
```

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `p_lock` | 0.995 | probability | emission and lock threshold; at the harness' 1e5 chain decisions per game a 0.5 % residual error would still be too many, so the posterior must also be calibrated (calibration metric) - the threshold is the knob, not the guarantee |
| `p_unlock` | 0.5 | probability | a locked chain is demoted (swap alarm) when its locked label falls below this; at 0.5 no other chain can hold the same label, so exclusivity is never broken by stickiness |
| `dummy_eps` | 0.0001 | probability | cost of explaining a chain as nobody on the lineup (fragment |
| `max_enum` | 20000 | maps | exact enumeration limit per team per frame |
| `min_evidence_nats` | 2.0 | nats | a chain locks only if its chain score without the one-label-per-person constraint (own cues + the directional priors from its parents and, offline, its children) favours the label over the runner-up by this margin; elimination alone (four teammates locked, so the fifth must be the fifth) never locks a chain |
| `confusable_rate` | 1.0 | nats/s | CONFUSABLE PAIRS (per-game confusion list of the reference pack): teammates whose expected appearance + height log-likelihood ratio grows slower than this (tau_app kappa_app (1 - cos of templates) + tau_height (dh/sigma_h)^2/2, per cue sample) cannot be told apart by soft cues within a possession |
| `twin_jersey_nats` | 5.0 | nats | a label with a confusable teammate among the candidates locks only when the chain's own jersey evidence favours it over that teammate by this much (more than one capped sighting: one misread confusable with the twin's number, 7 read as 80 for 30, locked a twin in the harness); template bias made the SportVU twins swap on appearance alone (review round 1) |
| `own_margin_nats` | 0.5 | nats | OWN-CUE SUPPORT: a chain locks a label only if it has at least one cue sample of its own and its own cues favour that label over every other candidate by at least this; priors (group mixture, children, elimination) can speed a lock up, never decide it (a group child inherited a teammate's label when a hidden teammate stepped out; tolerance 1.0 against still let it through) |
| `class_window_s` | 1.0 | s | live swap catch for opponents: a locked chain whose last 1 s of team-colour evidence is confidently the other class raises a class alarm (opponent pairs are not cut by the tracklet layer, see tracklets.rule) |
| `p_probable` | 0.9 | probability | PROBABLE TIER (owner decision 25 Oct 2026, OD-8; offline only): a detection the locked tier leaves on HOLD gets a flagged probable label when the chain's joint posterior for its offline label is >= this and the lower bars below hold. Probable labels are shown to viewers flagged as probable and never feed stats or any metric that counts locked identity |
| `probable_min_evidence_nats` | 1.0 | nats | probable tier: chain margin without the one-label constraint (min_evidence_nats is 2.0 for a lock); elimination alone still never gives a probable label |
| `probable_own_margin_nats` | 0.0 | nats | probable tier: at least one own cue sample and the chain's own cues may not favour another candidate (own_margin_nats is 0.5 for a lock) |
| `probable_twin_jersey_nats` | 0.0 | nats | probable tier: against a confusable teammate the own jersey evidence may not point to the twin (twin_jersey_nats is 5.0 for a lock) |

Outputs: label or HOLD, posterior, candidate set (labels with posterior >= 0.05), lock state, evidence breakdown per cue, probable label (offline only, flagged; OD-8).

## 8. Identity state machine

Per chain; identities are locked on entry (after confirmation), held through occlusions, re-confirmed after every crossing and released on exit.

| State | Meaning |
|---|---|
| `ENTER` | chain started with no parent (frame entry, start of play, after a camera cut); candidates = free on-court labels of its class |
| `CONFIRMING` | posterior of the best label < p_lock; output HOLD with candidates |
| `LOCKED` | label emitted every frame while the chain is visible |
| `HELD` | the chain ended inside a group (crossing, merge, pile-up); the identity is reserved for the group's children for link_window_s |
| `RECONFIRM` | a group child; prior = mixture of the group's identities; output HOLD until p_lock (cues confirm which member it is) |
| `ALARM` | a LOCKED chain's label fell below p_unlock (contradicting cues); output HOLD, chain split at its last encounter, review record written |
| `RELEASED` | frame exit, camera cut, substitution, or loss longer than link_window_s; the identity is free |

| Id | From | To | When |
|---|---|---|---|
| SM-1 | ENTER | CONFIRMING | first frame of a chain without parents |
| SM-2 | CONFIRMING | LOCKED | joint posterior >= p_lock, chain margin >= min_evidence_nats and own-cue support (own_margin_nats, at least one cue sample) |
| SM-3 | LOCKED | LOCKED | unique continuation after a short gap (single parent |
| SM-4 | LOCKED | HELD | the chain ends with reason ambiguous (pair-swap test failed |
| SM-5 | HELD | RECONFIRM | a child tracklet starts within reach and link_window_s |
| SM-6 | RECONFIRM | LOCKED | joint posterior >= p_lock with own evidence margin; time from the group end to this frame is the time-to-reconfirm metric |
| SM-7 | LOCKED | ALARM | posterior of the locked label < p_unlock |
| SM-8 | ALARM | CONFIRMING | next frame (the chain is split; the split part starts as a group child of the encounter) |
| SM-9 | LOCKED, CONFIRMING, HELD, RECONFIRM | RELEASED | camera cut, FOV exit, PBP substitution of the label, or HELD longer than link_window_s |
| SM-10 | RELEASED | ENTER | the player is seen again (new chain |

Invariants checked on every frame:

- **ID-INV-1**: no label is emitted twice in one frame
- **ID-INV-2**: at most five labels per team per frame outside substitution windows (R-IV-01)
- **ID-INV-3**: every emitted label is in the PBP lineup or the substitution window union
- **ID-INV-4**: a chain emits at most one label over its life offline; live label changes only through ALARM, and every change is logged
- **ID-INV-5**: no label on a chain whose class posterior is below p_team (officials, coaches, mascots, band, bench)

## 9. How swaps are caught and corrected

How swaps are caught and corrected - frame matching across occlusions.

```text
1. Prevention: pair-swap and merge tests cut tracklets, so a group child is matched to the group's members by cues
   (frame matching: the members' evidence before the group vs the child's evidence after it), never by motion alone.
2. Live catch: a LOCKED chain whose posterior for its label drops below p_unlock raises ALARM; the chain is split at
   its last close encounter (encounter_frames from the tracklet layer) and the part after it is re-confirmed.
3. Offline catch (change-point): for every chain and every close encounter in it, the split log-likelihood gain
   G = max_L1 S_before[L1] + max_L2 S_after[L2] - max_L S_all[L] is computed; the best split with G >= split_llr_min is
   applied, and the search repeats on each part (at most max_splits). When several split points are equally good
   (within split_tie_nats: no evidence between them), the stretch between the first and the last of them stays
   unlabelled - the swap happened there but the evidence cannot say where. This catches swaps made by an upstream
   tracker that did not cut.
4. Review: every ALARM, every offline split, every chain whose offline label differs from its live label, every
   on-court player left on HOLD for longer than review_hold_s while in view (requirements line 801: low identity
   confidence is flagged) and every ID-INV break goes to the identity review queue with the frames before and after, the cue evidence per side and the
   group membership.
```

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `split_llr_min` | 6.9 | nats | ln(1000): a split is applied only when two identities explain the chain 1,000 times better than one |
| `max_splits` | 3 | splits | per chain per pass |
| `review_hold_s` | 10.0 | s | a player in view who carries no label for this long is flagged to the human-in-the-loop queue (one possession of HOLD is worth a human look) |
| `split_tie_nats` | 1.0 | nats | every candidate split point whose gain is within this of the best is equally plausible (no evidence between them); the detections between the first and the last such point stay unlabelled |
| `encounter_m` | 1.5 | m | tracks closer than this record an encounter (candidate split point) |

## 10. Confidence and abstention

```text
Per-frame confidence = the joint posterior of the emitted label. HOLD is emitted when (a) the class is unsure, (b) no
label reaches p_lock, (c) the chain margin is below min_evidence_nats or the chain's own cues do not favour the label (own_margin_nats),
(d) the box is merged or occluded (no cues), (e) the chain is in ALARM or inside an encounter group, or (f) the box's
own team-colour observation contradicts its chain's team (a one-frame swap with an opponent or an official at a
chain edge, or a colour misread; costs about e_team of the boxes). HOLD carries the candidate set (labels with posterior >= 0.05). Downstream consumers use
candidate sets for counting (a HOLD in a two-player group still counts both players on the floor) and never guess.
Live panel (owner decision 25 Oct 2026, OD-10): when unsure the live panel shows HOLD with the candidate list; no
provisional or probable label is ever shown live. The probable tier (assignment rule, OD-8) exists offline only and is
flagged as probable wherever it is shown; it never feeds stats.
Calibration: on the gold sample the emitted posteriors are binned and the observed error rate per bin must stay below
the bin's mean (1 - posterior) x calibration_slack.
```

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `calibration_slack` | 2.0 | 1 | tolerated over-confidence before p_lock is raised |
| `candidate_min_p` | 0.05 | probability | smallest posterior listed in a HOLD candidate set |

## 11. Hard cases

| Id | Case | Handling | Test |
|---|---|---|---|
| HC-crossing | Two players cross or screen (one passes behind the other) | pair-swap test cuts both tracklets; the children inherit the 2-member mixture; jersey sightings, appearance and height re-confirm (SM-5, SM-6); live labels HOLD until then. | `test_crossing_reconfirmed_by_jersey, test_crossing_without_evidence_holds` |
| HC-pileup | Pile-up (scramble, rebound scrum, jump ball) - three or more players within merge distance | one group with all members; children re-confirm against the whole group; when detections merge, HOLD until the group dissolves. | `test_pileup_group_of_four` |
| HC-twins | Same-team, same-build pair with similar appearance (twins problem) | height and appearance cannot separate them; only jersey sightings (or elimination with own-evidence margin) lock them; otherwise HOLD. | `test_same_build_pair_needs_jersey` |
| HC-jersey-hidden | Jersey hidden (arm across chest, back to the wall, folded number) | partial digits kept as evidence; appearance, height and gait accumulate; lock only above p_lock with own evidence. | `test_partial_digit_reads_count` |
| HC-same-number | Same number on both teams | team class decides first (chains enter one team's problem only above p_team); the number then disambiguates within that team. | `test_same_number_both_teams` |
| HC-camera-cut | Camera cuts, replays, close-ups and the dead-ball gap | every track ends and every identity is RELEASED (no link across a cut); re-acquisition from cues with the lineup constraint; replays are not main-wide frames and give no detections. | `test_camera_cut_releases_and_reacquires` |
| HC-fov | Player leaves and re-enters the broadcast field of view | exit releases (owner rule); entry starts a new chain with no parents; re-acquired by cues. | `test_fov_exit_releases` |
| HC-substitution | Substitutions during dead balls (and late PBP entries) | lineup candidates widen to outgoing + incoming inside sub_window_s; a released player's label is not available after his substitution leaves the window. | `test_substitution_window` |
| HC-timeout | Timeouts and huddles | dead ball - camera leaves the main wide view; RELEASE on return; bench zone detections are class official_or_other or excluded by court zone. | `test_camera_cut_releases_and_reacquires` |
| HC-free-throw | Free-throw line-ups (players stand still in lane spaces, close together, often after a cut) | lane-space positions are fixed and well separated (about 0.9 m spaces), so pair tests pass; re-acquisition after the cut uses jersey sightings, which are frequent because players stand still facing the camera or the basket. | `test_free_throw_lineup_reacquired` |
| HC-officials | Referees, coaches, mascots, band members on the floor | class official_or_other; never enter a team problem (ID-INV-5). | `test_referee_never_labelled` |
| HC-tracker-swap | The upstream tracker swaps two tracks without cutting | live ALARM when cues contradict the lock; offline change-point split at the encounter (swap_catch 2-3). | `test_injected_tracker_swap_is_split_offline` |

## 12. Outputs

- **per frame**: `game_id`, `frame`, `pts`, `detection_id`, `chain_id`, `label (player_id or HOLD)`, `posterior`, `candidates`, `lock_state`, `class`, `class_posterior`, `evidence_by_cue`, `merged_flag`, `tier (locked | probable | hold)`, `probable_label (player_id or null; offline only)`, `probable_posterior`. label holds locked identities only; every stat, every count of locked identity and every metric of the metrics section reads label. probable_label is filled offline only (OD-8), flagged probable wherever it is shown, and never feeds stats.
- **live panel**: `frame`, `detection_id`, `label (player_id or HOLD)`, `candidates (when HOLD`, `posterior >= candidate_min_p)`, `lock_state`. Owner decision 25 Oct 2026 (OD-10): the live panel shows a locked label or HOLD with the candidate list; it never shows a provisional, unconfirmed or probable label.
- **probable log**: `game_id`, `frame_start`, `frame_end`, `chain_id`, `probable_label`, `mean_posterior`, `review_status`. OD-8: every probable run is logged; when truth exists (gold sample, harness) a wrong probable run is counted as probable_wrong_events, never as a locked swap.
- **per possession**: `possession_id`, `lineup_pbp (10 ids)`, `lineup_seen (labels emitted at least once)`, `agreement (labels seen subset of lineup)`, `unexplained_holds_s`, `abstention_share`. agreement must be 1.0 (ID-INV-3); a disagreement goes to review with the PBP row.
- **switch log**: `game_id`, `frame`, `chain_id`, `from_label`, `to_label`, `kind (alarm | offline_split | live_vs_offline | invariant_break)`, `evidence_before`, `evidence_after`, `group_members`, `review_status`. every label change, every alarm and every offline correction is a row; nothing is overwritten silently.
- **per game**: `confusion_list (pairs of players with any alarm or split between them)`, `identity accuracy per player`, `coverage per player`, `read rate of jersey numbers`
- **per season**: `accuracy per player`, `weak identities (lowest coverage) -> more labelled crops`

## 13. Metrics and acceptance

| Id | Metric | Definition |
|---|---|---|
| `idsw` | ID switches (CLEAR-MOT definition on labels) | for each true player, the sequence of emitted labels on his detections (HOLD skipped); every change between two consecutive emitted labels counts one switch. |
| `swap_events` | Swap events (the zero-swap quantity) | maximal runs of frames in which a true player's detection carries a wrong label (or an official's detection carries any label), runs closer than 1 s merged. Target 0. |
| `wrong_label_frames` | Wrong-label frames | detections with an emitted label different from the true player. |
| `idf1` | IDF1, IDP, IDR | optimal one-to-one matching between true players and emitted labels over the game (Ristani 2016); IDTP = matched co-occurrences; ground truth = every frame the player is on court inside the field of view (occluded frames count as misses). |
| `hota` | HOTA, DetA, AssA (source-matched) | Luiten 2021 at a single localisation threshold with each detection matched to the person it was made from (the harness knows it); TP = emitted labels on a true player's detection, FN = in-view true-player frames without a TP, FP = labels on officials or fragments; AssA = mean over TPs of TPA / (TPA + FNA + FPA). |
| `id_accuracy_player_game` | Identity accuracy per player per game | correct labelled frames / in-view frames of that player (coverage-weighted accuracy), plus precision = correct / emitted for that player. |
| `coverage` | Coverage | share of player detections that carry a label (1 - abstention share); offline and live separately. |
| `time_to_reconfirm` | Time to re-confirm after a crossing | for every true crossing (pair centre distance < 1.0 m with bearing flip >= 90 deg, the id_swap_risk crossed attribute of config/movement_grammar/bigs.yaml), the time from the end of the encounter to the first correctly labelled frame of each player; median, p90 and share within 2 s. |
| `calibration` | Posterior calibration | error rate per posterior bin of emitted labels vs 1 - mean posterior. |
| `probable_coverage_gain` | Probable-tier coverage gain (OD-8) | share of player detections that carry a probable label where the locked tier abstains (offline); coverage_with_probable = coverage + this gain. Reported apart from coverage. |
| `probable_error_rate` | Probable-tier error rate (OD-8) | wrong probable labels / probable labels (offline); wrong runs (merged within 1 s) are probable_wrong_events. Logged, never added to swap_events. |
| `recording_standard` | Recording standard (OD-9) | per game, the source resolution and frame rate of the main wide recording. |

| Id | Metric | Scope | Threshold | If it fails |
|---|---|---|---|---|
| ACC-1 | `swap_events` | gold sample (>= 5 MSU games, >= 20 min of labelled live play each, all 10 players labelled per frame) | == 0 (offline labels) | every swap gets a review record; the root cause (cue, rule, threshold) is fixed and the gold sample re-run; a swap is never waived |
| ACC-2 | `swap_events` | gold sample | <= 1 per game (live labels) | the live/offline difference must be caught by an ALARM or an offline split |
| ACC-3 | `idf1` | gold sample | >= 0.80 (offline) | coverage work (more cues |
| ACC-4 | `coverage` | gold sample | >= 0.85 of in-view player frames (offline) | as ACC-3 |
| ACC-5 | `id_accuracy_player_game` | gold sample | precision 1.0 for every player; coverage >= 0.70 for every player with >= 5 min on court | weak identities get more labelled crops (per-season output) |
| ACC-6 | `time_to_reconfirm` | gold sample | median <= 1.0 s, p90 <= 3.0 s, share within 2 s >= 0.80 (offline) | cue rates or pair-test thresholds revisited |
| ACC-7 | `invariants` | every game | ID-INV-1..5 zero breaks | quarantine affected frames (identity_review queue |
| ACC-8 | `calibration` | gold sample | observed error <= calibration_slack x (1 - mean posterior) in every bin with >= 1,000 labels | raise p_lock and re-tune taus |
| ACC-H1 | `swap_events` | SportVU harness, cue profile good, sigma_p 0.15 and 0.30 m, all three games, config full (offline) | == 0 | spec defect - fix before 0.1.x is accepted |
| ACC-P1 | `probable_error_rate` | SportVU harness (every cue profile and sigma_p, config full) and the gold sample, offline | reported with probable_coverage_gain on every run; probable labels never enter swap_events, idsw, IDF1, HOTA, coverage or any stat | a probable label found in a stat input is a defect; a probable error rate above 1 % on the gold sample raises p_probable |
| ACC-R1 | `recording_standard` | every game that feeds player-level numbers | >= 1080p and >= 59.94 fps (OD-9) | team-level numbers only, or probable-only player labels for that game |
| ACC-H2 | `idsw` | SportVU harness, config naive_tracker, cue profile good, sigma_p 0.30 m | > 0 (the harness must be able to produce swaps; otherwise it cannot test the rules) | harness defect |

**Gold sample.** Hand-label all ten players every 0.5 s on >= 5 MSU games (>= 20 min live play each, including at least 20 crossings and 5 substitution windows per game) in the local review tool; ShotTracker player ids, if MSU staff share them, replace hand labels as truth. Frames between labels are interpolated only inside one labelled chain.

## 14. The SportVU harness

tools/specgen/identity/harness.py simulates the identity problem on NBA SportVU 2015-16 tracking (true ids known): ids stripped, position noise added, broadcast camera field of view, camera-model occlusions and merged boxes, dead-ball gaps as camera cuts, PBP lineup with lag, referees as distractors, and cue observations drawn from configurable error models. The reference assigner (tools/specgen/identity/idlib.py) implements this spec. Aggregates only are written to results/identity_test/; per-player outputs stay in the private folder.

Data: ~/MSU-Alpha-3-private/data/research/sportvu_2015_16/json (3 games, private, never copied); 25 Hz; dead-ball moments are collapsed by the loader, so every wall-clock gap > dead_gap_s is a camera cut

| Parameter | Value | Unit | Why |
|---|---|---|---|
| `dead_gap_s` | 0.2 | s | wall-clock jump between consecutive kept moments that marks a dead ball (always treated as a camera cut) |
| `live_cut_rate_per_min` | 0.1 | 1/min | rare live-play cuts (alternate angle |
| `live_cut_s` | 1.0, 3.0 | s | duration range of a live-play cut |
| `fov_width_m` | 18.0 | m | main wide broadcast shot shows about 55-60 ft of the 94 ft court |
| `fov_tau_s` | 1.0 | s | camera pan smoothing (exponential) following the ball |
| `camera_xy_m` | 14.33, -8.0 | m | main camera at mid-court, 8 m behind the near sideline (SportVU y = 0 side) |
| `occl_lateral_m` | 0.45 | m | two players whose lines of sight from the camera are closer than this laterally overlap |
| `occl_depth_m` | 3.0 | m | overlap only matters within this depth difference (elevated camera) |
| `p_occl_drop` | 0.7 | probability | share of overlapped far players whose box is lost (else detected with no cues) |
| `merge_m` | 0.6 | m | centres closer than this give one box at the midpoint with the near player's cues |
| `p_miss` | 0.01 | probability per frame | detector drop-out start probability |
| `miss_len_s` | 0.04, 0.3 | s | drop-out duration range |
| `pbp_lag_s` | -1.0, 4.0 | s | PBP substitution time minus true change (the lineup feed the assigner sees) |
| `n_referees` | 3 | persons | officials on the floor as distractors (D-I three-person crews) |
| `e_ref_class` | 0.02 | probability | officials misclassified as a team |
| `reach_dist_ref_m` | 14.0 | m | camera distance at which jersey sighting rates are quoted; rates fall linearly to 30 % at 28 m |

assigner_overrides are the cue parameters the production system would fit on labelled crops of that recording quality (kappa_app about 1 / app_noise^2 scaled to the good profile, sigma_h, e_team, e_ocr). The assigner must be calibrated per recording quality: poor video read with good-video parameters is overconfident (profile poor_uncalibrated).

Noise grid sigma_p: 0.15, 0.3, 0.5 m (white + AR(1) mix of tools/specgen/movement/sim.py).

Heights are not in SportVU; they are drawn per roster position (G / F / C mean and sd: G 1.91 / 0.06 m; F 2.03 / 0.05 m; C 2.11 / 0.04 m).

**Cue profiles** (simulator truth; the assigner keeps the YAML cue parameters):

| Field | good | poor | poor_uncalibrated |
|---|---|---|---|
| note | 1080p main wide camera, normal arena light | 720p or low bitrate, dim arena, heavy motion blur | the poor recording read with the assigner still calibrated for good video (kappa_app, sigma_h, e_ocr not refitted) |
| e_team | 0.01 | 0.04 | 0.04 |
| jersey_sightings_per_s | 0.6 | 0.2 | 0.2 |
| jersey_sighting_len_s | 0.12, 0.4 | 0.08, 0.25 | 0.08, 0.25 |
| e_ocr | 0.05 | 0.15 | 0.15 |
| p_partial | 0.2 | 0.35 | 0.35 |
| app_dims | 16 | 16 | 16 |
| app_w_ind | 0.35 | 0.25 | 0.25 |
| app_w_game | 0.15 | 0.15 | 0.15 |
| app_noise | 0.12 | 0.2 | 0.2 |
| app_rho | 0.9 | 0.9 | 0.9 |
| game_card | True | False | False |
| template_crops | 50 | 30 | 30 |
| sigma_h | 0.05 | 0.08 | 0.08 |
| outlier_h | 0.15 | 0.25 | 0.25 |
| gait_noise | 0.6 | 0.9 | 0.9 |
| twin_pairs_per_team | 1 | 1 | 1 |
| assigner_overrides | none (YAML values) | kappa_app 7.2; sigma_h 0.08; outlier_h 0.25; e_team 0.06; e_ocr 0.15 |  |

**Configs** (ablations of the spec):

| Config | Tracklets | Cues | Lineup | Abstain | Alarms | Splits | Note |
|---|---|---|---|---|---|---|---|
| `naive_tracker` | naive | team, jersey, appearance, height, gait | True | False | False | False | standard tracker: links through crossings, labels once at first confirmation and keeps them |
| `motion_team` | pure | team | False | True | True | True |  |
| `motion_team_lineup` | pure | team | True | True | True | True |  |
| `plus_jersey` | pure | team, jersey | True | True | True | True |  |
| `plus_appearance` | pure | team, jersey, appearance | True | True | True | True |  |
| `full` | pure | team, jersey, appearance, height, gait | True | True | True | True |  |
| `full_no_jersey` | pure | team, appearance, height, gait | True | True | True | True |  |
| `full_no_lineup` | pure | team, jersey, appearance, height, gait | False | True | True | True |  |
| `full_forced` | pure | team, jersey, appearance, height, gait | True | False | True | True | emit the argmax always (no abstention) |
| `naive_tracklets_full_catch` | naive | team, jersey, appearance, height, gait | True | True | True | True | a standard tracker upstream; tests whether alarms and offline splits catch its swaps |

Production-only parameters (act on pixels, OCR scores, crop banks or the gold sample; the harness has none): `review_hold_s`, `calibration_slack`, `candidate_min_p`, `height_min_frames`, `lineup_check_interval_s`, `merged_box_iou`, `min_readable_px`, `ocr_min_score`, `template_min_crops`.

## 15. Open questions for Aldemir

- **OQ-1**: Hair (style, colour) is listed as an appearance cue in requirements line 151 but can act as an ethnicity proxy; 0.1.0 excludes hair and skin entirely (head and skin masked). Keep the exclusion?
- **OQ-2**: Live labels: is HOLD acceptable on the live panel (with the candidate set), or do you want a provisional label marked "unconfirmed"? The zero-swap rule is met only if provisional labels never feed stats. **Decided 25 Oct 2026 (OD-10): the live panel shows HOLD with the candidate list when unsure; no provisional labels (outputs.live_panel).**
- **OQ-3**: Jersey read rate and OCR error at our recording quality are the largest unknowns (the harness assumes 0.6 sightings per second and 5 % error for good video). Measure them on the first labelled MSU game before tuning anything else?
- **OQ-4**: ShotTracker ids from MSU staff would give exact identity truth for MSU home games; ask staff? **Decided 25 Oct 2026 (OD-9): yes - action item AI-1 (open_items).**
- **OQ-5**: Zero swaps costs coverage. On the harness the spec labels about 59 % / 46 % / 26 % of player boxes offline at sigma_p 0.15 / 0.30 / 0.50 m (good video) and only 2-12 % on poor video, against ACC-3/ACC-4 targets of IDF1 >= 0.80 and coverage >= 0.85. Keep the zero-swap rule absolute and treat coverage as the thing to improve (better position precision during encounters, 60 fps, more jersey reads), or allow a separately flagged "probable" label tier for analysis that never feeds stats? **Decided 25 Oct 2026 (OD-8): zero swaps stays absolute; a flagged probable tier is added (offline, viewer-only, never feeds stats; coverage gain and error rate measured on the harness); coverage levers (60 fps, more jersey reads) are planned work PW-1 / PW-2.**
- **OQ-6**: Poor recordings (720p, low bitrate, dim): appearance stops separating teammates, so labels wait for two jersey sightings. Should we set a minimum recording standard (1080p, 60 fps) for any game that feeds player-level numbers? **Decided 25 Oct 2026 (OD-9): yes - requirement.recording_standard and acceptance ACC-R1 (below it: team-level only or probable-only).**

**Action items**

| Id | Action | Owner | Status |
|---|---|---|---|
| AI-1 | Ask MSU staff for ShotTracker player ids (per-player tracking ids of MSU home games) as identity truth for the gold sample and for re-measuring coverage and probable-tier errors on MSU video. | Aldemir (owner decision 25 Oct 2026, OD-9) | open |
| AI-2 | Agree the recording standard (1080p, 59.94 fps main wide camera) with whoever records MSU games; until a game meets it, it feeds team-level numbers only or probable-only labels (ACC-R1). | Aldemir (owner decision 25 Oct 2026, OD-9) | open |

**Planned work (coverage levers)**

| Id | Lever | Why | How it is measured |
|---|---|---|---|
| PW-1 | 60 fps recordings | Coverage lever (OD-8): twice the frames per jersey sighting window and less motion blur raise jersey_sightings_per_s; the zero-swap bar stays. | re-run the harness with a 60 fps cue profile once MSU 60 fps footage gives a measured read rate (OQ-3) |
| PW-2 | more jersey reads (OCR on front and back, partial digits, more crops per sighting) | Coverage lever (OD-8): jersey sightings are the only cue that separates same-build teammates (twin rule) and the main driver of re-confirmation after crossings. | jersey read rate and OCR error on the first labelled MSU game (OQ-3), then the harness coverage at the measured rate |
| PW-3 | better position precision during encounters | Coverage falls with sigma_p (section 1); two players closer than about 4 sigma cannot be kept apart by motion. | tracker sigma_p on MSU film (movement noise model) |

## 16. Journal

**0.1.0 (2026-10-25)**

- First version of the identity pack (baseline 3), from the requirements identity section, Aldemir's zero-swap rule (23 Oct) and a short survey of broadcast identification work.
- Reference assigner, cue simulator, SportVU harness and synthetic rule tests written against this file; the design was iterated on the harness (RV-01 to RV-10 below).
- Independent review pass (requirements and hard cases): standing-constraint YAML item fixed (it parsed as a mapping), assignment rule text completed (directional priors, lock conditions), DP4 split into teammate and opponent crossings, game card refreshed at substitution entries, low-confidence review trigger (review_hold_s), orientation and blur noted for jersey sightings, ID-INV-2 and posterior calibration added to the harness metrics.

**0.1.1 (2026-10-25)**

- Owner decisions of 25 Oct 2026 (OD-8 .. OD-10; answers to OQ-2, OQ-4, OQ-5, OQ-6): zero swaps absolute with a flagged offline probable tier; minimum recording standard and the ShotTracker action item; live panel HOLD with candidates.
- harness.py writes G1 / G2 / G3 codes (game_code) in the repo results and keeps real ids in the private output only; the repo results record game counts per run.

| Id | What | Why | Evidence |
|---|---|---|---|
| OD-8 | Zero swaps stays absolute (requirement.zero_swaps). New probable tier (assignment rule and params p_probable 0.9, probable_min_evidence_nats 1.0, probable_own_margin_nats 0.0, probable_twin_jersey_nats 0.0): offline only, emitted on frames where the locked tier abstains but the chain's offline label passes the lower bar; its own output field (Result.probable; outputs per_frame tier / probable_label, probable_log), never repeated in a frame, never written to the locked label, so swap_events, idsw, IDF1, HOTA, coverage and stats are unchanged. New metrics probable_coverage_gain and probable_error_rate (metrics.probable_metrics, harness rows and summary), acceptance ACC-P1. Coverage levers recorded as planned work PW-1 (60 fps), PW-2 (more jersey reads), PW-3 (position precision). | owner decision 25 Oct 2026 (OQ-5): keep the zero-swap rule absolute and treat coverage as the thing to improve; a separately flagged probable tier may be shown to viewers but never feeds stats or any metric that counts locked identity; its coverage gain and its error rate are both reported, and wrong probable labels are logged, not counted as locked swaps. | SportVU harness (3 games G1-G3, config full, offline, 251 s wall, 4 workers): every locked metric of all 228 result rows identical before / after (swap_events, idsw, wrong-label frames, IDF1, HOTA, coverage, re-confirm, alarms, splits). Probable tier, good video, sigma_p 0.15 / 0.30 / 0.50 m: coverage 0.593 / 0.463 / 0.255 -> with probable 0.694 / 0.547 / 0.319 (gain +0.102 / +0.084 / +0.064); probable labels wrong 161 of 176,224 / 182 of 145,295 / 82 of 111,230 (error rate 0.09 / 0.13 / 0.07 %; 13 / 14 / 10 wrong runs; 2 probable frames on officials at 0.50). Poor video (calibrated): gain +0.299 / +0.202 / +0.117 (coverage 0.120 / 0.091 / 0.024 -> 0.419 / 0.293 / 0.141), error rate 0.18 / 0.06 / 0.06 % (42 / 18 / 15 wrong runs). Poor video read with good-video parameters (poor_uncalibrated): error rate 1.39 / 1.00 / 1.28 % (148 / 87 / 86 wrong runs), so calibration per recording quality applies to the probable tier too. Threshold check on 12 min of G1 (good 0.15 / 0.30 / 0.50, poor 0.30): (p 0.8, margin 0.5) raised the gain by 0.01-0.04 but wrong labels rose 32 -> 54 at good 0.30 and 11 -> 129 on poor; (0.95, 1.5, own 0.25) cut the gain by about a fifth with the same 32 wrong at good 0.30. Tests test_od8_single_sighting_gives_a_probable_label_not_a_lock, test_od8_elimination_never_gives_a_probable_label, test_od8_probable_tier_never_changes_locked_labels, test_owner_decisions_25_oct_recorded. |
| OD-9 | requirement.recording_standard: any game that feeds player-level numbers needs >= 1080p and >= 59.94 fps; below it the game feeds team-level numbers only or probable-only player labels (acceptance ACC-R1, metric recording_standard). Action items AI-1 (ask MSU staff for ShotTracker player ids as identity truth) and AI-2 (agree the recording standard with whoever records MSU games), both owned by Aldemir. | owner decision 25 Oct 2026 (OQ-6, OQ-4): poor recordings stop appearance from separating teammates, and exact identity truth for MSU games would replace hand labels in the gold sample. | Harness, full offline, poor vs good video at sigma_p 0.30 m: locked coverage 0.091 vs 0.463; read with good-video parameters (poor_uncalibrated) 1 / 1 / 4 swap events at 0.50 / 0.30 / 0.15 m (section 1). Test test_owner_decisions_25_oct_recorded. |
| OD-10 | outputs.live_panel: the live panel shows a locked label or HOLD with the candidate list (candidate_min_p); never a provisional, unconfirmed or probable label. confidence_and_abstention rule and outputs per_frame say so; the solver's live result carries no probable label (Result.probable is None live). | owner decision 25 Oct 2026 (OQ-2): HOLD with candidates is acceptable live; provisional labels would invite stats from guesses. | Live labels and live metrics unchanged (harness rows identical). Tests test_od8_single_sighting_gives_a_probable_label_not_a_lock (live carries no probable label), test_owner_decisions_25_oct_recorded. |

**Review round 1 (self-review against the requirements and hard cases)**

| Id | Finding | Fix | Evidence |
|---|---|---|---|
| RV-01 | Cutting both tracklets at every frame of a close encounter (pair-swap test) made 1.6 tracklets per frame: a defender 1 m from his man restarted his identity every frame, and every child had dozens of parents. | Encounter groups - a failing track continues as an unlabelled amb segment and leaves the group as one clean tracklet with explicit parents after clear_s. | SportVU game G1, first 5 min, sigma_p 0.3: 12,054 tracklets -> 3,117; offline coverage 0.00 -> 0.48. |
| RV-02 | Hidden-person swaps: a track whose own box is missing takes the box of a teammate who was hidden behind someone (no active track, so no pair test); clean tracklets were impure at their edges. | Jump test, contested-detection likelihood test (contest_s, v_err_mps, a_max_mps2, contest_prior_nats), newcomer test, leading and trailing guards, decision delay of clear_s. A first, radius-based contest test was rejected (it left 50-60 % of boxes in amb segments). | Impure clean tracklets (5 min, sigma_p 0.15 / 0.3): 144 -> 2 / 1; full-game offline swap events fell from 6-10 per game to 1-8 before RV-05. |
| RV-03 | Opponent pairs (most close encounters - a defender on his man) were cut like teammates, leaving about 40 % of boxes on HOLD at sigma_p 0.3. | Opponent pairs with confident, different classes are not cut; team colour separates them, with a colour veto in the pair test, a per-box colour HOLD (confidence rule f) and a live class alarm (class_window_s); every encounter stays a split point. | 5 min, sigma_p 0.3, offline coverage 0.48 -> 0.56; the colour HOLD removed the 1-2 frame opponent tails that were the last full-game swaps. |
| RV-04 | SportVU itself re-assigns player ids at some substitutions without a wall-clock gap (players teleport 6 m in 0.04 s); the harness scored the source's own swap. | sportvu_truth marks a gap (camera cut) where the on-court set changes or any player moves more than 1 m in one frame. | Game G1 one substitution: players 0, 5, 8 exchange positions; gaps 105 -> 123. |
| RV-05 | A group child inherited a parent's label when a teammate hidden for longer than link_window_s stepped out of the encounter (the true identity was not in the group); with leak 0.02 the prior alone almost locked. | Adaptive leak (leak_min + leak_eps x unseen candidates / candidates) and the own-cue support rule (own_margin_nats - priors can speed a lock, never decide it). | Full games, sigma_p 0.15-0.5: pure-chain mislabels of 4-46 frames disappeared; a tolerance version (own cues may disagree by 1 nat) still let one through. |
| RV-06 | One confusable misread (8 read as 3, 7 read as 80) locked a label: a single sighting carried about 4-7 nats. | sighting_cap_nats 4 for locking (two agreeing sightings needed); uncapped sightings for the offline change-point test, where more evidence only adds splits. | Full game G1, sigma_p 0.15 - chain labelled 16 for player 20 from one confusable read. |
| RV-07 | Same-team same-build pairs (the twins hard case) swapped on appearance alone, because template noise biases the appearance evidence the same way every frame. | Per-game confusable pairs from the reference pack (confusable_rate) - a lock against a confusable teammate needs twin_jersey_nats (5) of own jersey evidence. | Game G3, sigma_p 0.3: twin 0 labelled 3 for 46 frames offline -> 0. |
| RV-08 | When an offline split had equally good candidate points (no evidence between them), the first was taken and the frames up to the true swap were mislabelled. | Every point within split_tie_nats of the best is equally plausible; the stretch between them stays unlabelled. | test_injected_tracker_swap_is_split_offline. |
| RV-09 | Offline labels used only forward information (parents to children); a chain confirmed late could not help its parents. | Offline forward and backward identity messages through the chain graph (directional_mixtures), each using only its own direction so no cue is counted twice. | 5 min, sigma_p 0.15: offline coverage 0.48 -> 0.71 before the safety rules of RV-05 to RV-07 (which brought it back to about 0.6). |
| RV-10 | Catching swaps after the fact does not replace prevention. | Kept as a harness config (naive_tracklets_full_catch) and stated in the doc; alarms and splits are the safety net, not the mechanism. | See section 1 results. |
