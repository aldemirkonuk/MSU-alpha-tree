# Player identity on broadcast basketball: what is published (survey, 11 Nov 2026)

Scope: single broadcast feed, NCAA men's basketball, zero swaps on locked labels, no face / skin / hair cues.
Every number below carries its source, dataset and conditions. "Soccer" or "fixed camera" is said where it applies;
those numbers show what is possible, not what we will get. Source numbers in square brackets refer to the list at the end.
Items marked (own calculation) are mine, not published.

## 1. Headline findings

1. No published system reaches zero identity swaps. The best trackers on SportsMOT (basketball, volleyball, football;
   720p, 25 fps, clips with no camera cuts) still record 2,400-3,100 ID switches on the 150-clip test set [T1][T2][T3].
   Identity must therefore come from a layer above the tracker that abstains, which is the pack's design.
2. The jersey number is the only cue every strong system uses to name a player, and it is visible rarely: 5.9 % of
   player images are legible in hockey broadcast [J1]; a keyframe filter on SoccerNet keeps 12.35 % of tracklet frames
   [J3]. No basketball broadcast figure is published.
3. Even after voting over a whole tracklet, the number is wrong or missed for 7-21 % of tracklets (soccer) [J1][J2].
   Reads inside one tracklet are therefore strongly correlated; two reads close in time are not two pieces of evidence.
4. The dominant read error is a two-digit number read as one digit [J1]. With NCAA numbers 0-99 [R1], most rosters
   contain collisions of this kind (own calculation, section 3).
5. Appearance re-ID is strong only over seconds and within one camera. It decays with the time gap [T7], and the
   authors of the datasets say plainly that teammates look alike [A1][A3][J2]. Basketball is the hardest SportsMOT sport,
   and appearance-only association there reaches HOTA 26.94 against 66.17 for the best mix [T1].
6. Basketball identity data on broadcast barely exists in public. The one NBA broadcast benchmark with global identities
   (MuPNIT, WACV 2026) reports that low face visibility makes face-based re-ID fail and uses CLIP-family embeddings [B3];
   its numbers could not be read in full (paper page blocked; abstract and slides only).
7. Play-by-play substitutions are not a safe hard constraint: 2.87 % of substitution windows in 50 NCAA games hold a
   detectable error [P1]; in Canadian university data 24 % of hand-checked substitution rows were wrong [P2].

## 2. Jersey number recognition

| Source | Data and conditions | Result |
|---|---|---|
| SoccerNet 2023 challenge [J2] | Soccer broadcast, 2,853 tracklets (challenge set 1,211), classes 1-99 plus "not visible"; accuracy per tracklet | Best of 15 teams 92.85 % (ZZPM: text detection filter, five recognisers, vote). 2nd 90.95 % (CLIP ViT-L/14 pseudo-labels, vote over images with probability > 0.7). 3rd 88.08 %. Random baseline 3.93 % |
| Koshkina and Elder 2024 [J1] | Hockey images (132,983; 7,787 legible = 5.9 %) and SoccerNet tracklets | Legibility classifier (ResNet34) 94.5 % accuracy, F1 71.7 % on hockey. PARSeq fine-tuned: 91.4 % per legible hockey image. Full pipeline on SoccerNet: 87.45 % test, 79.31 % challenge (tracklet). Ablation: no two-digit bias -0.66 points; no bias and no confidence threshold -2.07; no main-subject filter -2.89 |
| Balaji et al. 2023 [J3] | SoccerNet tracklets; crops fed at 150 x 120 | Keyframe module raises accuracy from 30.89 % to 68.53 % (test) and 36.07 % to 73.77 % (challenge) with the same LSTM. 87.65 % of frames are dropped as showing no number |
| SoccerNet GSR baseline 2024 [J4] | Soccer broadcast, 200 clips of 30 s, 1080p, 25 fps | Oracle test: with everything else ground truth, MMOCR jersey reading alone leaves GS-HOTA at 56.75. The paper names jersey recognition the weakest module |
| SoccerNet 2025 challenge [J5] | Same task | Winner GS-HOTA 63.90 (2024 winner 63.81). Jersey methods: vision-language models (LLaMA-3.2-Vision, Qwen2-VL), fine-tuned CLIP, PARSeq on pose torso crops with outlier rejection; always a tracklet vote |
| Constructor Tech 2024 winner [J6] | Same task | Small ResNet on 32 x 32 crops, two heads (first digit or none, second digit), so half-hidden numbers still give one digit. Tracklets are split so each holds one number and one team, then merged by number, then by re-ID |
| Vats et al. 2021 [J7] | NHL broadcast | Team identification 97 %; player identification 83 % using the game roster |
| Practitioner pipeline 2025 [J8] | NBA playoff broadcast clips, 3.6k number crops | ResNet classifier 93 % test accuracy; fine-tuned SmolVLM2 86 % (56 % before). A number is accepted after three identical reads sampled every 5 frames; number box must sit inside the player mask (intersection over smaller area >= 0.9). Errors are most frequent for far-side players. Not peer reviewed |
| PARSeq [J9] | General scene text benchmarks | 91.9 % (synthetic training), 96.0 % (real training). Not sports |

What the methods have in common: (a) decide legibility first, (b) crop the torso with pose, (c) read with a scene-text
model or a two-head digit classifier, (d) reject outlier crops that belong to another person, (e) vote per tracklet
with a bias toward two digits. What none of them reports: the error of two reads taken seconds apart, a basketball
legibility rate, or the size in pixels at which reading fails.

Size check (own calculation). NCAA requires numbers at least 6 inches high on the back and 4 inches on the front [R1].
At 1080p with a 2 m player about 200 px tall (the pack's assumption), that is about 15 px (back) and 10 px (front);
at 720p 10 px and 7 px; on the far side at 1080p about 11 px and 8 px. The pack's `min_readable_px: 18` would
reject almost every wide-shot read. Published systems gate on a legibility classifier, not on a pixel height.

## 3. Roster collisions under truncation (own calculation)

Random rosters of 15 distinct numbers, a hidden digit turning a two-digit number into a full one-digit read:

| Number model | Rosters with at least one collision | Players affected per roster | Five on court with a collision |
|---|---|---|---|
| Legacy digits 0-5 only | 96.7 % | 48 % | 49 % |
| 80 % legacy, 20 % any 0-99 | 94.0 % | 40 % | 42 % |
| Uniform 0-99 | 79.5 % | 22 % | 25 % |

Real rosters are not random, so these are bounds on the order of magnitude, to be replaced by a count on real rosters.
The conclusion holds either way: a one-digit read cannot be trusted as a full number unless the whole number area is
seen to be unobstructed.

## 4. Re-identification in sport

| Source | Data and conditions | Result | Transfer |
|---|---|---|---|
| DeepSportradar re-ID [A1] | French pro basketball, one fixed sideline camera, 99 sequences of 20 frames at 10 fps; query = frame 1, gallery = frames 2-20 | Baseline 65 % mAP, 90 % rank-1 | Re-ID across 2 s only |
| CLIP-ReIdent [A2] | Same challenge (MMSports 2022) | 98.44 % mAP, CLIP ViT-L/14, image-to-image contrastive training | Same 2 s caveat; authors note the model reads shirt numbers |
| SoccerNet re-ID 2023 [J2] | Soccer, same action seen from several cameras, 340,993 thumbnails | Best 93.26 % mAP, 91.26 % rank-1 | Same instant, different camera; not re-ID over time |
| PRTreID [A3] | Crops from SoccerNet-Tracking | Re-ID 72.59 mAP, 89.57 rank-1; team affiliation by two-cluster k-means 95.6 % (91.87 % with identity-only training); role 94.27 % | Authors warn identity-only models may group players by skin colour. Our crops are skin-masked, so expect less |
| SportsSUSHI [T7] | SoccerNet and a fixed-camera hockey set | Adding field position to re-ID: HOTA 85.37 to 89.22; adding jersey numbers: to 89.78. Re-ID accuracy by frame gap falls from 98.0 (1 frame) to 33.0 (300 frames) in one column of table 3 | Appearance decays within 10 s; the column's dataset label could not be confirmed |
| SportsMOT [T1] | Basketball, volleyball, football | Appearance-only association HOTA: basketball 26.94, volleyball 40.94, football 65.65 | Basketball teammates are the least separable by appearance |

No published re-ID result uses skin- and head-masked crops, and none reports rank-1 among the five teammates on court
over minutes. The pack's `masked_app` profile stays an assumption.

## 5. Tracking through occlusion

| Source | Data and conditions | Result |
|---|---|---|
| SportsMOT, MixSort [T1] | 240 clips (150 test), 720p, 25 fps, overhead game shots only, no abrupt viewpoint change | Test: ByteTrack HOTA 64.1, IDs 3,089; OC-SORT 73.7, 2,728; MixSort-OC 74.1, 2,781. Best HOTA per sport: basketball 66.17, football 73.19, volleyball 76.91 |
| Deep-EIoU [T2] | SportsMOT test | HOTA 77.2, IDF1 79.8, AssA 67.7, IDs 2,659. Uses a 60-frame lost-track buffer because of occlusion. On SoccerNet with oracle detections HOTA 85.44 |
| GTA tracklet splitter and connector [T3] | SportsMOT, SoccerNet-Tracking; offline post-process | Deep-EIoU 77.21 to 81.04 HOTA, IDF1 79.81 to 86.51, IDs 2,909 to 2,737 (SportsMOT); SoccerNet 79.41 to 83.11, IDs 2,803 to 2,188. Splitter = DBSCAN on per-box embeddings inside a tracklet; connector = clustering with no temporal overlap and a reach limit |
| SoccerNet 2023 tracking winner [J2] | Soccer broadcast | HOTA 75.61. Splits tracklets that cross, fine-tunes re-ID on the unambiguous tracklets of the same video, then merges with no duplication and no teleporting |
| CAMELTrack [T4] | SportsMOT test | HOTA 80.4, IDF1 84.8, AssA 72.8. Pose keypoints add nothing on SportsMOT (80.3), which the authors put down to the distant camera |
| McByte [T5] | SportsMOT test; SoccerNet-Tracking 2022 | HOTA 76.9, IDF1 77.5; SoccerNet 85.0 / 79.9. Mask from SAM, propagated by Cutie, used only when confident and only for ambiguous matches; unregulated mask use lowered IDF1 from 51.9 to 44.4 on DanceTrack validation |
| SAM2MOT, SAMIDARE [T6] | SportsMOT | Test: SAM2MOT HOTA 76.4, IDF1 76.5; SAMIDARE 77.3, 78.6. Validation: 83.7 / 82.9 and 86.2 / 87.1. Named failure: mask expansion and drift to neighbouring look-alike players, which then contaminates the memory |
| Basketball-SORT [B2] | Basketball, fixed fisheye side camera (TeamTrack), 30 s clips | ID switches per clip 9.3 +/- 5.0 against 20.7 (Deep-EIoU) and 23.2 (BoT-SORT); HOTA 63.35 against 60.74 and 59.70. Tracks in court coordinates, caps the player count at 10, re-acquires long-lost ids by appearance (cosine cost 0.2) and court distance (2.6 m) |
| TrackID3x3 [B1] | 3x3 basketball, fixed cameras and drone, not broadcast; identity = team + jersey number (outdoor set) | TI-HOTA 85.53 indoor (9 s clips), 71.03 outdoor (40 s clips). The authors state an id exchange during occlusion is the main loss and their merger cannot repair exchanges |
| BasketLiDAR [B4] (already in the pack) | Pro basketball with LiDAR | Restores ids by matching the clearest frame before and after an occlusion |

Reading for our design. Mask-memory trackers help in overlap but drift exactly where we need them (same-kit players in
contact). Court-plane association and a hard player-count cap are the two basketball-specific gains with numbers
behind them, both from a fixed camera. Tracklet splitting on appearance change (GTA, the 2023 winner) is the published
way to restore purity after the fact; every strong pipeline then merges by jersey number before appearance [J6].

Rough scale (own derivation, assumes test clips have the dataset's mean length of 25 s): 2,659 switches over about
63 min of SportsMOT test video is about 40 per minute of footage. A tracker alone is two to three orders of magnitude
away from zero swaps.

## 6. Basketball-specific identity work

- Lu et al., CVPR 2011 (in the pack): NBA broadcast, tracklets + appearance + mutual exclusion, up to 85 %.
- MuPNIT and Global ID Fusion, WACV 2026 [B3]: NBA broadcast with camera cuts and zooms, 2.19 M boxes over 283 K
  frames, a global identity bank of player crops, and five identity metrics (frames to first id, frames to first correct
  id, class switches per tracklet, mean correct ratio, mAP). The slides say face-based re-ID fails for lack of visible
  faces and that CLIP-family and AP3D embeddings work best; the abstract reports +25.3 % HOTA and +79.5 % IDF1 over
  OC-SORT. The paper page returned 403, so table values and the exact cues are not confirmed. Their "frames to first
  correct id" is the right metric for our time-to-lock.
- Jump-Aware, CVPR workshops 2025 [B5]: basketball and volleyball with jersey-based identities and jump annotations;
  jump spotting mAP 95.33. Relevant for the height cue: airborne players corrupt both floor position and height.
- Senocak et al., CVPR workshops 2018 [B6]: part-based identification on NBA broadcast clips, "up to 96 %" per a search
  summary; the paper could not be opened (403), so the protocol (same games in train and test or not) is unknown.
- DeepSportradar [A1], TeamTrack / Basketball-SORT [B2], TrackID3x3 [B1]: fixed cameras.
- SportVU-derived tracking (the harness data) has identities but no pixels.

There is no public dataset of broadcast college basketball with identities, and no published jersey legibility rate,
re-ID rank or id-switch rate for it.

## 7. Camera cuts and replays

- SoccerNet-v2 [C1]: 158,493 annotated camera changes; 71.4 % abrupt, 14.2 % fades, 14.2 % logo transitions. Shots are
  86.7 % live, 10.9 % replay of an action, 2.4 % other replay; replays last 6.8 s on average. Boundary detection mAP:
  histogram baseline 78.5 overall (abrupt 83.2, fading 54.1, logo 82.2); the learned baseline 59.6. Soccer.
- TransNetV2 [C2]: F1 77.9 (ClipShots), 96.2 (BBC), 93.9 (RAI). General video; no sports figure.
- SportsMOT and SoccerNet-Tracking avoid the problem by construction (clips without viewpoint switches) [T1].
- MuPNIT is the only benchmark built around cuts and zooms [B3].

No published miss rate exists for cuts on basketball broadcast. A missed cut links unrelated people, so the identity
layer needs its own fallback (many tracks jumping at once, homography jump) and cannot rely on the detector.

## 8. Body geometry as a soft biometric

- Single image, no calibration: mean absolute height error 5.56 cm [G1]; a later paper notes that guessing the
  gender-specific mean gives about 5.6 cm, so this is close to no information [G2, via search summary].
- Calibrated surveillance camera, walking subjects, head and foot points: about 1.39 cm [G3, via search summary].
- Monocular video with gravity as reference: 3.9 cm on jumps, 13.1 cm on low jumps [G4, via search summary].
- Court registration at 960 x 540: 1.27 m RMS position error (KaliCalib, in the pack). A scale error of a few percent
  moves every player's height together, so only height differences inside one frame are usable.
- Own calculation with the harness height model (guards 1.91 +/- 0.06 m, forwards 2.03 +/- 0.05, centres 2.11 +/-
  0.04): with an effective height error of 0.03 m after averaging, 37 % of on-court teammate pairs differ by more than
  3 sigma, and a player is unique by height among his five in 4 % of line-ups (0 % among 15). At 0.02 m: 56 % and 12 %.

Height cannot name a player. It can exclude candidates.

## 9. Gait and skeleton recognition (future hook only)

- Silhouette gait, walking, in the wild: GaitBase rank-1 60.1 % (GREW), 64.6 % (Gait3D), against 97.6 % in the lab
  (CASIA-B normal walking) [F1]. Later models report 77-82 % on GREW and 75-77 % on Gait3D (search summaries of 2025-26
  papers; protocols differ).
- Runners in a race, action-recognition features on 7 s clips: mAP 63.3 %, rank-1 43-53 %, 111-129 identities; the
  features are not appearance-free [F2].
- Sport: pose keypoints give no tracking gain on SportsMOT at broadcast distance [T4]; pose quality on basketball is
  PDJ 74-89 % with elbows and wrists weakest under occlusion and blur [B1].

No published work identifies team-sport players from movement style alone on broadcast video. All gait results use
walking or steady running, hundreds of frames and silhouettes that include clothing shape.

## 10. Rules that bear on identity (2026-27 NCAA men's rules book [R1])

- Rule 1-22.7.b: numbers on front and back; legal numbers 0-99; a roster may hold 0 or 00, not both; duplicates on one
  team are not permitted; at least 6 inches high on the back and 4 on the front; one solid colour in clear contrast.
- Rule 3-6.3.b: a uniform saturated with blood must be changed before the player returns.
- Rule 10-4.1.m: playing after a number change without reporting it to the scorer and an official is a technical
  infraction. So a number can change in mid-game, and the change is known to the scorer, not necessarily to the feed.
- Rule 3-6.1.a: a substitute reports his number to the scorers before entering.
- Numbers containing 6-9 were illegal until 2023-24 [R2], so number classifiers trained on older college footage have
  never seen them.

## 11. Not established by published evidence

1. Jersey legibility rate, read error and error correlation over time for basketball broadcast at any resolution.
2. The pixel height at which jersey reading fails.
3. Re-ID quality with skin and head masked, among five teammates, over minutes.
4. Any identity value of shoes, sleeves, pads or socks (only passing remarks [A2]).
5. Height or limb-ratio precision from a panning broadcast camera.
6. Movement-style identification of players.
7. Cut and replay detection error on basketball broadcast.
8. Substitution timing error of NCAA Division I play-by-play against video (the two studies cover detectable row
   errors and Canadian data).
9. Any system, in any sport, that reports zero identity errors with an abstention rate.

## Sources

Jersey numbers
- [J1] Koshkina, Elder. A General Framework for Jersey Number Recognition in Sports Video. 2024. https://arxiv.org/html/2405.13896v1
- [J2] Cioppa et al. SoccerNet 2023 Challenges Results. https://arxiv.org/pdf/2309.06006 (tables 5, 6, 7; sections 6-8 and appendix read in full)
- [J3] Balaji et al. Jersey Number Recognition using Keyframe Identification from Low-Resolution Broadcast Videos. 2023. https://arxiv.org/html/2309.06285v1
- [J4] Somers et al. SoccerNet Game State Reconstruction. 2024. https://arxiv.org/html/2404.11335v1
- [J5] SoccerNet 2025 Challenges Results. https://arxiv.org/html/2508.19182
- [J6] From Broadcast to Minimap: Achieving State-of-the-Art SoccerNet Game State Reconstruction. 2025. https://arxiv.org/html/2504.06357
- [J7] Vats et al. Player Tracking and Identification in Ice Hockey. 2021. https://arxiv.org/abs/2110.03090
- [J8] How to Detect, Track, and Identify Basketball Players with Computer Vision (blog, 2025). https://roboflow.com/blog/identify-basketball-players
- [J9] Bautista, Atienza. Scene Text Recognition with Permuted Autoregressive Sequence Models (PARSeq). 2022. https://arxiv.org/abs/2207.06966

Re-identification
- [A1] Van Zandycke et al. DeepSportradar-v1. 2022. https://arxiv.org/html/2208.08190v1
- [A2] Habel, Deuser, Oswald. CLIP-ReIdent. 2023. https://arxiv.org/abs/2303.11855
- [A3] Mansourian et al. Multi-task Learning for Joint Re-identification, Team Affiliation and Role Classification. 2024. https://arxiv.org/html/2401.09942v1

Tracking
- [T1] Cui et al. SportsMOT. 2023. https://arxiv.org/html/2304.05170
- [T2] Huang et al. Deep-EIoU. 2023. https://arxiv.org/html/2306.13074
- [T3] Sun et al. GTA: Global Tracklet Association. 2024. https://arxiv.org/html/2411.08216
- [T4] Somers et al. CAMELTrack. 2025. https://arxiv.org/html/2505.01257
- [T5] Stanczyk et al. McByte. 2025. https://arxiv.org/html/2506.01373v1
- [T6] Hirano, Ukita. SAMIDARE. 2026. https://arxiv.org/html/2604.22162 (SAM2MOT: https://arxiv.org/abs/2504.04519)
- [T7] Koshkina, Elder. Towards long-term player tracking with graph hierarchies and domain-specific features. 2025. https://arxiv.org/html/2502.21242v1

Basketball
- [B1] TrackID3x3. 2025. https://arxiv.org/html/2503.18282
- [B2] Basketball-SORT. 2024. https://arxiv.org/html/2406.19655v1
- [B3] Wojtulewicz, Liu, Carlsson. Advancing Player Identification and Tracking with Global ID Fusion. WACV 2026. https://wacv.thecvf.com/virtual/2026/oral/1215 ; slides https://wacv.thecvf.com/media/wacv-2026/Slides/304.pdf
- [B4] BasketLiDAR. 2025. https://arxiv.org/abs/2508.15299 (not re-read today; as cited in the pack)
- [B5] Oo et al. Jump-Aware. CVPR workshops 2025. https://openaccess.thecvf.com/content/CVPR2025W/CVSPORTS/html/Oo_Jump-Aware_Player_Position_Rectification_and_Identification_in_Dynamic_Sports_Using_CVPRW_2025_paper.html (abstract only)
- [B6] Senocak et al. Part-Based Player Identification. CVPR workshops 2018. https://openaccess.thecvf.com/content_cvpr_2018_workshops/w34/html/Senocak_Part-Based_Player_Identification_CVPR_2018_paper.html (not opened; search summary only)

Cuts and replays
- [C1] Deliege et al. SoccerNet-v2. 2021. https://ar5iv.labs.arxiv.org/html/2011.13367
- [C2] Soucek, Lokoc. TransNet V2. 2020. https://arxiv.org/pdf/2008.04838 (numbers via search summary)

Geometry and gait
- [G1] Gunel et al. What Face and Body Shapes Can Tell Us About Height. 2018. https://arxiv.org/abs/1805.10355
- [G2] Height and weight from a single unconstrained image, CVPR 2021. https://farid.berkeley.edu/downloads/publications/cvpr21b.pdf (search summary only)
- [G3] Li et al. Height estimation in calibrated video surveillance. EURASIP 2015. https://link.springer.com/article/10.1186/s13640-015-0086-1 (search summary only)
- [G4] Bieler et al. Gravity as a Reference for Estimating a Person's Height from Video. ICCV 2019. https://arxiv.org/pdf/1909.02211.pdf (search summary only)
- [F1] Fan et al. OpenGait / GaitBase. 2022. https://arxiv.org/html/2211.06597v3
- [F2] Re-identification in ultra-distance running with action-recognition models. 2023. https://arxiv.org/html/2401.00080v1

Play-by-play and rules
- [P1] Supervised Learning Approach for Improving Data Quality in Sports (50 NCAA games, two teams). MWDSI 2019. https://matthewalanham.github.io/Students/2019/2019_MWDSI_Supervised%20Learning%20Approach%20for%20Improving%20Data%20Quality%20in%20Sports.pdf
- [P2] Wu. Using AI to Correct Play-by-play Substitution Errors (U Sports, 6,049 games; 623 hand-checked rows, 76.1 % and 76.8 % correct; 2.72 unequal substitution stoppages of 43.35 per game). Sloan 2016. https://www.sfu.ca/~tswartz/papers/wu.pdf
- [R1] 2026-27 NCAA Men's Basketball Rules Book, Rules 1-22.7.b, 3-6.1.a, 3-6.3.b, 10-4.1.m (local copy docs/rules/PRMBB_RulesBook.pdf in the repo).
- [R2] Numbers 0-99 approved for 2023-24. https://nsga.org/news/uniform-numbers-among-ncaa-mens-basketball-proposed-rule-changes-for-2023-24
