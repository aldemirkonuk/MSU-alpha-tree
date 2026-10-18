# Requirements inbox 005 · Load thresholds: speed bands, acceleration gate, calibration plan

From: research session (Job E of `coord/prompts/002-claude-code-taxonomy-and-markets.md`). To: requirements session. Status: proposal from research, not yet agreed with Aldemir.
Source document (full evidence, every URL): `docs/research/load_thresholds.md` (Sections 7, 9, 10, 11), revised after a source-verification pass.
Action: consider adding the section below under "Physical load and the physics of the shot" in the live requirements doc. Add hypotheses new-60 to new-65 to the hypothesis registry; they continue the `docs/research/beliefs_register.md` sequence (which ends at new-59), and the requirements session assigns the final numbers. JEV hypotheses keep their numbers.

---

## Physical load: bands, gates and calibration

**Principle.** Store, per player per stint, time and distance in 0.1 m/s speed bins (0–10 m/s) and every acceleration effort with its peak (m/s²), duration (s) and start speed (m/s). Every band scheme is a view computed afterwards, so changing a threshold never means reprocessing video. Each output records frame rate, feed type, filter, window, detected coverage and tracked-point type.

**Tracked point.** Speed is the magnitude of the 2-D court-plane velocity (m/s) of one named point after the named filter: the pelvis keypoint projected onto the floor when pose is available, otherwise the midpoint between the ankle keypoints projected onto the floor. The point type is stored on every row.

**Primary absolute speed bands (m/s)**

| Band | MSU primary | Placeholder (kept as a view) | Status |
|---|---|---|---|
| Stand–walk | < 2.0 | < 2.0 | Reported with coverage once step 5 gives band-wise limits of agreement |
| Jog | 2.0–4.0 | 2.0–4.0 | OK only if step-5 95% LoA are narrower than 2.0 m/s |
| Run | 4.0–5.0 | 4.0–5.5 | OK only if step-5 95% LoA are narrower than 1.0 m/s |
| High-speed running | 5.0–5.83 | – | Fragile: reported as "observed" with coverage; counts only after step 5 |
| Sprint | > 5.83 | > 5.5 | Fragile: reported as "observed" with coverage; counts only after step 5 |

Secondary views from the same histograms: literature-exact 1.94 / 3.89 / 5.0 m/s (7 / 14 / 18 km/h; only 3 basketball LPS studies used this exact scheme), WIMU 1.67 / 3.33 / 5.0 / 6.67 m/s, NBA HSR > 4.0 m/s, and the 4.2 m/s for ≥ 0.5 s sprint event used in one Kinexon study. Speed efforts (HSR and sprint counts) last ≥ 1.0 s on detected frames, with a 0.5 s sensitivity view. A relative overlay (percent of a robust per-player match reference speed, v_ref) is reported beside the absolute bands and never replaces them; v_ref stays provisional until ≥ 5 games with ≥ 70% detected coverage.

**Speed error is unknown until we measure it.** The literature runs from 0.20 m/s (best detected frames, wide soccer tactical feed) to ≥ 1.1 m/s (monocular broadcast), with 95% limits of agreement up to about ±2 m/s even for fixed multi-camera NBA tracking. On a programme feed, the only broadcast validation found gave total-distance bias of −22% to +24%. No literature figure stands in for our own step-5 result.

**Acceleration and deceleration gate**

| Band | Edge (m/s²) | Status |
|---|---|---|
| Moderate | ≥ +2.0 / ≤ −2.0 | Primary, only after both gates pass |
| High | ≥ +3.0 / ≤ −3.0 | Primary, only after both gates pass (multi-camera soccer agreement does not transfer to broadcast) |
| Placeholder | ≥ ±2.5 | View only |
| NBA high | ≥ +3.5 | Not reported unless the in-motion check passes for this band |
| > 4 | – | Not reported |

Effort rules: acceleration from positions smoothed over a full window of at least 1.0 s (necessary, not sufficient); effort must stay beyond threshold for ≥ 0.5 s and ends when acceleration crosses 0 m/s²; never bridge gaps longer than 0.12 s or count across undetected or interpolated frames; decelerations are stored as negatives. All acceleration outputs are labelled exploratory until both gates pass.

Gates (hypothesis new-62, two conditions):
- (a) Stationary: speed noise SD < 0.3 m/s and acceleration noise SD < 0.5 m/s² for players standing still at free throws and timeouts.
- (b) In motion: on ≥ 50 hand-labelled starts from standstill, ≥ 50 hard stops and ≥ 50 cuts of about 90°, the pipeline's peak and mean acceleration and effort duration agree with a constant-acceleration fit to frame-counted displacement, with bias and 95% LoA reported by band.

Honest consequence: by our noise arithmetic, a 0.5 m/s² noise target needs a full window of about 1.0–1.4 s at 0.1 m position error, 1.5–2.4 s at 0.3 m and 1.9–3.1 s at 0.5 m. **If our measured position error is above about 0.3 m, acceleration counts are expected to fail the gate and will not be reported.** Jerk and PlayerLoad are not measurable from video.

**Calibration plan (10 steps, plus 5b)**
1. Log frame rate, resolution and feed type for every game; compute detected coverage per player; exclude stints with coverage < 70% of on-court time.
2. Position error budget: hand-annotate the tracked point on a few hundred frames; report RMSE (m) per calibration zone (paint r < 4.57 m; mid-range 4.57–6.75 m; corners r ≥ 6.60 m with θ ≤ 12° or ≥ 168°; wings, slots and top at r ≥ 6.75 m; deep frontcourt; backcourt bands by distance from the half-court line), per court end and per zoom level. Target ≤ 0.5 m on detected frames.
3. Stationary noise floor (gate a).
4. Filter choice: Winter residual analysis over 1 / 1.5 / 2 Hz Butterworth, Kalman/RTS and Savitzky-Golay; acceleration window ≥ 1.0 s.
5. Speed check on hand-timed straight runs between court lines; bias and 95% LoA by speed band; a band is reported only if its LoA are narrower than the band width.
5b. In-motion acceleration check (gate b).
6. Sensitivity curves of every count against MED (0.3–1.0 s) and threshold; a band is unstable if its count moves > 20% for a 0.1 s MED change or a 0.25 m/s (0.5 m/s²) edge change.
7. Histogram and k-means cross-check of the chosen edges (a check, not the definition).
8. Off-screen share by phase (transition vs half-court); high-speed values reported as "observed" with coverage.
9. v_ref stability across games before relative percentages are frozen.
10. Optional external anchor (public multi-camera data, wearables or radar) for band-wise bias correction.

**Proposed hypotheses (evidence in `docs/research/load_thresholds.md`, Section 11; whether betting markets price any of them is not known)**
- new-60: Running intensity (m/min on a minutes-played denominator, HSR m/min) falls from Q1 to Q4. Video/tracking.
- new-61: A player's robust 1 s peak speed per stint falls with continuous minutes on the floor. Video/tracking.
- new-62: Our broadcast tracking passes the stationary and in-motion acceleration gates. Tracking only.
- new-63: Players reach higher running intensity in quarters their team wins. Video/tracking plus play-by-play quarter scores.
- new-64: Relative instead of absolute speed bands change the positional ordering of high-speed distance. Tracking.
- new-65: Higher-level players cover less distance but have more high-speed capacity. Tracking, MSU vs opponents.

---

## Update 2026-10-18 · Summary for the requirements session (bands, absolute vs individual, calibration, limits, questions)

From: research session (Job E summary pass). Nothing above is changed; this section condenses `docs/research/load_thresholds.md` (Sections 1–12 and its "Additions 2026-10-18", A–I) into what the requirements session needs to decide. Units: m, s, m/s, m/s²; km/h only in brackets where a paper used it (m/s = km/h ÷ 3.6). Court zones use r (m) and θ (degrees from the right baseline at the rim centre) per `config/vocabulary_map.yaml`.

Citations: the URLs marked † were re-opened in this pass and the quoted numbers checked against them (list at the end). Every other figure comes from `docs/research/load_thresholds.md`, where each one carries the URL opened during that research; they were not re-opened here. **[derivation]** = worked out by us, not taken from a source.

### 1. Recommended speed bands (absolute, primary)

Speed = court-plane speed of the tracked point (pelvis projected to the floor, else ankle midpoint), after the named filter; the point type is stored on every row. Stored as 0.1 m/s histograms (0–10 m/s) per player per stint, so every scheme below is a view and changing an edge never means reprocessing video.

| Band | Primary edge (m/s) | Literature anchor | Placeholder view (m/s) | Reportable when |
|---|---|---|---|---|
| Stand–walk | < 2.0 | < 1.94 (7 km/h); Tuttle recommends merging standing and walking † | < 2.0 | Step-5 band-wise 95% LoA known; always with detected coverage |
| Jog | 2.0–4.0 | 1.94–3.89 (7–14 km/h) †; 4.0 = NBA HSR edge (> 14.4 km/h) † | 2.0–4.0 | Step-5 95% LoA narrower than 2.0 m/s |
| Run | 4.0–5.0 | 3.89–5.0 (14–18 km/h) | 4.0–5.5 | Step-5 95% LoA narrower than 1.0 m/s |
| High-speed running (HSR) | 5.0–5.83 | ~18 km/h (5.0 m/s) used by 16 of 20 basketball studies that named HSR/HIR † | – | Fragile: "observed" with coverage only, until step 5 passes for this band |
| Sprint | > 5.83 | > 21 km/h (5.83 m/s) in 3 of 12 sprint studies; > 24.1 km/h (6.69 m/s) in 7 of 12 † | > 5.5 (soccer-derived; no basketball use found) | Fragile, as HSR |

Why 5.83 m/s and not 6.69 m/s for sprint: NCAA D-I men's game peaks (Kinexon, 10 players) are guards 7.04 ± 0.39, forwards 6.63 ± 0.52, centres 6.23 ± 0.33 m/s †, so > 6.69 m/s would be near-empty for forwards and centres, and it is where optical speed is most negatively biased (largest NBA optical-vs-radar bias in the maximal band, r = 0.08 within that band †).

Speed efforts (HSR and sprint counts): above the edge for ≥ 1.0 s on detected frames; 0.5 s kept as a sensitivity view.

Secondary views from the same histograms: literature-exact 1.94 / 3.89 / 5.0 m/s; WIMU 1.67 / 3.33 / 5.0 / 6.67 m/s; NBA HSR > 4.0 m/s †; Kinexon-style sprint event > 4.2 m/s for ≥ 0.5 s (vendor default unverified); placeholder 2.0 / 4.0 / 5.5 m/s (kept, labelled non-standard).

### 2. Recommended acceleration and deceleration bands

| Band | Edge (m/s²) | Literature anchor | Status |
|---|---|---|---|
| Moderate acc | ≥ +2.0 | LPS mean initial threshold > 2.0 ± 0.6; 14 of 22 LPS acc/dec studies used > 2 † | Exploratory until gates (a) and (b) pass for accelerations |
| Moderate dec | ≤ −2.0 | Same | Gated **separately** on hard stops (see below) |
| High acc | ≥ +3.0 | Garcia ±3.0; SciSports and SkillCorner 3 m/s² | Exploratory until gates pass; noise-dominated at σ_p ≥ 0.3 m unless W ≥ ~1.5 s [derivation] |
| High dec | ≤ −3.0 | Same | Gated separately |
| Placeholder | ±2.5 | Reina 2020 (LPS) single > 2.5 zone | View only |
| NBA high acc | ≥ +3.5 | NBA optical > 3.5 † (not the same quantity as Catapult IMA 3.5, which is a velocity change) | Not reported unless gate (b) passes for this band |
| Very high | > +4 / < −4 | Multi-camera optical vs IMU R² 0.338 (acc > 4) and 0.838 (dec < −4) † | Not reported |

Effort rules (unchanged from above): acceleration from positions smoothed over a full window W ≥ 1.0 s (necessary, not sufficient); effort lasts ≥ 0.5 s beyond the edge and ends when acceleration crosses 0 m/s²; no gap bridging > 0.12 s; no effort counted across undetected or interpolated frames; decelerations stored as negatives.

New since the first draft (Additions A): **decelerations are a separate construct.** They are larger in magnitude (maximal decelerations of about −7.6 to −8.4 m/s² in team-sport tests), carry the most mechanical load per metre, and are measured differently by optical systems (under-counted, d = 1.17 †). Recommendation: keep symmetric ±2.0 / ±3.0 m/s² edges for literature comparability, but **gate acceleration bands on starts and deceleration bands on hard stops separately**; one may pass while the other fails. Expect our smoothing to blunt deceleration peaks more than acceleration peaks [inference], and use the high-dec / high-acc ratio per player-game as a filter-attenuation diagnostic (new-66).

Not measurable from broadcast video: jerk, Catapult PlayerLoad, metabolic power / equivalent distance (acceleration-driven, −44% to +352% validity errors even with GPS in multidirectional work, never validated in basketball).

### 3. Absolute or individual?

**Both, with absolute as the primary published scheme and a relative overlay for speed only.**
- Absolute: comparable with literature, opponents and seasons, stable under fitness change.
- Relative changes individual numbers a lot: fast players' top-zone match distance 161 ± 84 m absolute vs 47.4 ± 36.8 m relative (d = 1.75; 12 men, basketball) †.
- But single-anchor individualisation misinterprets 39–61% of players' high-speed shares (Hunter 2015, 12 U18 soccer players, 50 match observations; anchoring on maximal sprint speed alone misread 61% of %HSR and 39% of %VHSR) †, and we have no fitness tests, so our anchor is a **match reference speed v_ref** (median of each player's top-3 per-game 1 s rolling-mean peaks, artefact-screened), which sits below true maximal sprint speed.
- Relative edges are set so the team-median player's relative edges equal the absolute edges (worked example: at v_ref 6.63 m/s, edges 2.0 / 4.0 / 5.0 / 5.83 m/s become 30.2 / 60.3 / 75.4 / 87.9% [derivation]).
- v_ref is provisional until each player has ≥ 5 games with ≥ 70% detected coverage.
- **Accelerations are never individualised from game video** (game-derived acceleration anchors are unreliable even with GPS). An exploratory deceleration view as a fraction of each player's hand-labelled maximal stop is allowed only after enough labelled stops exist.

### 4. How to calibrate on our data (condensed; full plan in the section above and in the research doc, Section 10 and Additions F)

1. **Conditions:** log frame rate, resolution, feed type per game; compute detected coverage per player; exclude stints < 70% coverage from load summaries.
2. **Position error:** hand-annotate the tracked point on a few hundred frames; RMSE (m) by calibration zone (paint r < 4.57 m; mid-range 4.57–6.75 m; corners r ≥ 6.60 m with θ ≤ 12° or ≥ 168°; wings, slots, top at r ≥ 6.75 m; deep frontcourt; backcourt bands), by court end, by zoom. Target ≤ 0.5 m on detected frames.
3. **Gate (a), stationary:** players still at free throws and timeouts; speed noise SD < 0.3 m/s and acceleration noise SD < 0.5 m/s².
4. **Filter choice:** Winter residual analysis over Butterworth 1 / 1.5 / 2 Hz, Kalman/RTS, Savitzky-Golay; acceleration window W ≥ 1.0 s.
5. **Speed check:** hand-timed straight runs between court lines; bias and 95% LoA per band; a band is reported only if its LoA are narrower than its width.
6. **Gate (b), in motion:** ≥ 50 starts, ≥ 50 hard stops, ≥ 50 ~90° cuts, frame-counted displacement vs pipeline; bias and LoA per band (2–3, 3–4, > 4 m/s²), **acceleration and deceleration judged separately**.
7. **Sensitivity curves:** counts vs MED (0.3–1.0 s) and edge (±0.25 m/s; ±0.5 m/s²); flag a band unstable if its count moves > 20%.
8. **Distribution check:** histograms and k-means as a cross-check of the edges, not their definition.
9. **Off-screen share** by phase (transition vs half-court); HSR and sprint reported as "observed".
10. **v_ref stability** before relative percentages are frozen.
11. **Between-game variability (step 10b, Additions F):** log-scale mixed model per metric (player and game random intercepts); smallest worthwhile change (SWC) = 0.2 × between-player SD; a metric is used for game-to-game monitoring only if our measurement typical error ≤ SWC, otherwise only multi-game averages. No basketball between-game CV exists in the literature except NBA HSR/min CV ~15–16%; soccer HSR between-match CV is ~16% and minimum detectable change > 30%, so single-game HSR changes below ~30% should not be interpreted.
12. **Optional external anchor:** public multi-camera data, wearables or radar for band-wise bias correction.

### 5. Measurement limits of broadcast tracking (what to expect before we measure)

- **No basketball broadcast validation exists** in metres for player position, speed or acceleration; all broadcast budgets are soccer and are placeholders until steps 2, 5 and 6.
- **Position:** commercial AI tracking on World Cup broadcast feeds: position RMSE 1.68–16.39 m overall †; on detected frames 0.44–1.14 m for the better providers; undetected (extrapolated) frames 4.6–12 m. No broadcast source reached 0.3 m.
- **Speed:** RMSE 0.34–2.38 m/s across providers and feeds †; ≥ 1.1 m/s for monocular broadcast even with a 1.64 s span; even fixed 6-camera NBA optical tracking had 95% LoA half-widths of ~1.2–1.9 m/s against radar and the largest negative bias at maximal speeds †.
- **Distance:** total-distance mean bias −21.8% to +24.3% across providers †; within ~±6% only with a high-detection feed.
- **Detection depends on the feed:** tactical (wide) feed 89–96% of frames detected vs 36–42% for a programme feed; resolution 720p vs 1080p made no meaningful difference †. Our B1G+ recordings are programme feeds, so expect low coverage.
- **Off-screen time is not random:** players off camera move differently; in basketball the camera follows the ball, so getting-back defenders, leak-outs and trailers are most often out of frame, biasing sprint and HSR counts low exactly in transition (Job D).
- **Acceleration:** by our noise arithmetic (white-noise assumption), σ_a < 0.5 m/s² needs a full window of about 1.0–1.4 s at σ_p 0.1 m, 1.5–2.4 s at 0.3 m, 1.9–3.1 s at 0.5 m [derivation]. Windows that long blunt real basketball accelerations. **If measured σ_p > ~0.3 m, acceleration counts are expected to fail the gate and will not be reported.** Real broadcast errors are correlated (homography drift, ID-swap spikes), so this is a lower bound on the problem.
- **High accelerations are unreliable even for multi-camera systems** (R² 0.338 above 4 m/s² vs IMU †).
- **Frame rate:** 60 fps helps detection, blur and identity, not differentiation noise directly; jump flight time is quantised to ±1 frame (±0.033 s at 30 fps ≈ ±0.05 m at a 0.40 m jump [derivation]).
- **Lateral and backward movement** cost 15–80% more energy than forward running at the same speed (lab, ≤ 2.2 m/s), so speed-only bands under-state defensive load; an exploratory cost-weighted direction view is proposed (new-67) but needs a validated direction classifier.

### 6. Hypotheses carried to the registry

new-60 to new-65 (above) plus, from Additions H: **new-66** (high-intensity decelerations outnumber high-intensity accelerations in MSU games; video/tracking only, conditional on both directions passing gate b) and **new-67** (speed-only distance under-ranks defensive load relative to a cost-weighted direction view; video/tracking with pose plus play-by-play phases). Whether betting markets price any in-game load or fatigue measure is **not known** (no source found). The requirements session assigns final IDs; JEV hypotheses keep their numbers.

### 7. Open questions for Aldemir (one line each)

1. Do you accept 2.0 / 4.0 / 5.0 / 5.83 m/s as primary edges, with the 2.0 / 4.0 / 5.5 m/s placeholder kept only as a view?
2. Do you accept ±2.0 / ±3.0 m/s² as acceleration and deceleration edges, reported only after both gates pass and gated per direction?
3. Are you willing to see no acceleration counts at all if our measured position error exceeds ~0.3 m?
4. What resolution and frame rate does your first B1G+ recording actually have (30 or 60 fps, 720p or 1080p)?
5. Can you record or obtain any wide (tactical / all-22-style) camera angle, given programme feeds detect only ~36–42% of player-frames in the soccer benchmark?
6. Is 70% detected coverage of on-court time the right exclusion threshold for load summaries, or should it be set after the first games?
7. Who hand-annotates the calibration set (a few hundred position frames plus ≥ 150 labelled starts, stops and cuts), and how many hours can go to it?
8. Is there any route to wearable, radar or LPS data (MSU's reported Catapult use is unverified), even for a few practice segments, as an external anchor?
9. Should per-minute load use live time, minutes played or total on-court time as the headline denominator (all three stored; they differ by ~30–50%)?
10. Is the relative (v_ref) overlay wanted at all in reports, or stored only for research?
11. Should the exploratory cost-weighted direction view (lateral and backward weights) appear in reports, or stay internal until the direction classifier is validated?
12. Is pelvis-floor projection acceptable as the default tracked point, with ankle midpoint as the fallback?
13. Should jump counts and heights (pose-derived, ±~0.1 m agreement at best at 30 fps) be in scope for v1, or deferred?
14. Should load metrics be linked to the betting/market work at all, given no evidence that markets price in-game load?

### 8. Gaps carried forward (from the research passes)

- No NCAA men's game study with LPS speed zones; NCAA data are Kinexon peak speed and events (Stone 2022) and Catapult PlayerLoad/IMA.
- No validation of broadcast or monocular basketball tracking against multi-camera, LPS or motion-capture ground truth for speed or acceleration; no published SportVU, Second Spectrum or Hawk-Eye acceleration validation; Hawk-Eye 60 Hz unverified.
- No head-to-head comparison of 95th vs 99th percentile peak-speed estimators; no study linking relative vs absolute basketball bands to injury or performance.
- Full texts not opened (abstract or secondary only): Stojanović 2018, Russell 2021, Svilar 2018, Scanlan 2011, Puente 2017 methods, Sampaio 2015, Caparrós 2018, Ibáñez 2022 (women), Sosa 2021 zone edges, Rojas-Valverde 2022, Ellens 2024 Appl Sci, Varley 2017, Serpiello 2018, Massard 2018, Djaoui 2017, Vázquez-Guerrero 2018.
- Unverified: Catapult IMA default bands and rolling averages; Kinexon defaults; NBA Combine ¾-court distance (22.86 m); Hawk-Eye camera count; MSU's use of Catapult Vector; FIFA EPTS numeric cut-offs.
- Our noise-propagation numbers assume white position noise; real broadcast errors are correlated.

### Re-opened and checked in this pass (2026-10-18)

- † https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11467009/fullTextXML — Tuttle et al. 2024 (16 of 20 HSR/HIR studies ~18 km/h; sprint 7 of 12 > 24.1 km/h, 3 of 12 > 21 km/h; 14 of 22 LPS acc/dec studies > 2 m/s²; mean > 2.0 ± 0.6 m/s²; microsensor > 3.5; merge standing and walking; Delphi recommendation)
- † https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full — Stone et al. 2022 (Table 3 max speed C 6.23 ± 0.33, F 6.63 ± 0.52, G 7.04 ± 0.39 m/s; acc/dec 1.5 m/s² for 0.5 s "as dictated by the proprietary software")
- † https://arxiv.org/abs/2508.19477 — Crang et al. 2025 abstract (position RMSE 1.68–16.39 m; speed RMSE 0.34–2.38 m/s; distance bias −21.8% to +24.3%; tactical feed maximises detection; 720p and 1080p both suitable). Feed-specific detection percentages are from the PDF as recorded in the research doc, not re-checked here.
- † https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.3390/s25061804&resultType=core&format=json — González-Rodenas et al. 2025 (optical under-counts decelerations d = 1.17; R² 0.956 moderate acc, 0.944 moderate dec, 0.338 acc > 4, 0.838 dec < −4 m/s²)
- † https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1055/s-0034-1384547&resultType=core&format=json — Hunter et al. 2015 (12 U18 players, 22 fixtures, 50 observations; MSS-only anchor misinterpreted 61% %HSR and 39% %VHSR)
- † https://www.ebi.ac.uk/europepmc/webservices/rest/PMC12526517/fullTextXML — Ruiz-Álvarez et al. 2025 (fast players, match Z4 161 ± 84.1 vs 47.4 ± 36.8 m, ES 1.75)
- † https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf — D'Amelio 2020 thesis (HSR > 14.4 km/h; high accelerations > 3.5 m·s⁻²; maximal velocity band r = 0.08 with the largest mean bias vs radar)
