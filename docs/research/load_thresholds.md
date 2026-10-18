# Load thresholds: speed zones, acceleration bands and what broadcast tracking can measure

Research document for MSU Alpha 3, Job E of `coord/prompts/002-claude-code-taxonomy-and-markets.md`, with belief-register entries for Job C. Written 2026-10-17. Revised after a source-verification pass (fixer, 2026-10-18): corrections are made in place, and the claims re-checked in that pass cite the sources re-opened for it (listed at the end under "Re-opened in the verification pass").

Scope: speed zones, acceleration and deceleration thresholds, jump counts and PlayerLoad-style measures in basketball tracking and wearable research; absolute vs individualised bands; what broadcast-camera tracking can measure and with what error; a recommended band set for MSU Alpha 3 with a calibration plan on our own data.

Our placeholder bands under review (from the Job E prompt): walk < 2.0, jog 2.0–4.0, run 4.0–5.5, sprint > 5.5 m/s; accelerations above 2.5 m/s². `docs/requirements.md` ("Physical load and the physics of the shot") already asks for distance by speed band with "thresholds calibrated on our data", acceleration and deceleration counts per minute, and within-game decline of top speed and acceleration.

Conventions:
- Units are SI: m, s, m/s, m/s². Papers that used km/h are converted (m/s = km/h ÷ 3.6) with the original km/h in brackets; sources in miles, mph or feet are converted (1 mi = 1,609.344 m, 1 mph = 0.44704 m/s, 1 ft = 0.3048 m) and only the SI value is shown; g is converted at g = 9.81 m/s²; milliseconds are written as seconds. The NCAA court is 28.65 m × 15.24 m.
- Court positions and calibration zones use r (m) and θ (degrees from the right baseline at the rim centre), as in `config/vocabulary_map.yaml`; zones are defined in Section 10, step 2.
- **Tracked point.** Every speed and acceleration in our outputs is the magnitude of the 2-D court-plane velocity (m/s) or acceleration (m/s²) of one named body point, after the named filter. Default point: the pelvis keypoint projected vertically onto the floor plane when pose is available; otherwise the ground projection of the midpoint between the two ankle keypoints. Each output row records the point type (`pelvis_floor` or `ankle_mid`), because foot-point speed oscillates with each step and inflates the top bands, and because optical systems (near the pelvis) and wearables (between the scapulae) diverge at high speed [https://pmc.ncbi.nlm.nih.gov/articles/PMC10761404/].
- Every claim carries the URL of a source opened during this research. **unverified** means the claim was seen only in a search snippet or secondary citation, or the page could not be opened. **[derivation]** means a value worked out here from sourced numbers, not taken from a source.
- Europe PMC REST API records (abstract-level) are cited as "Europe PMC, DOI …"; all were retrieved from https://www.ebi.ac.uk/europepmc/webservices/rest/search queried by DOI.
- Per-minute values depend on the denominator (live time, minutes played, or total time on court including stoppages). This one choice moves published m/min by about 30–50% (Section 6).

---

## 1. Summary

1. **There is no consensus threshold set in basketball.** Tuttle et al. 2024 (Sports Med, 86 studies) found 78 studies used fixed thresholds; its Discussion says 22 of 26 studies (85%) used Catapult devices (the Results list 33 microsensor studies; the review does not explain the 26 denominator) with thresholds that align with manufacturer presets, and relative zones appeared in only 8 studies, none of them local-positioning (LPS) speed studies. They call for a Delphi consensus and recommend no single threshold set [https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/]. Russell et al. 2021 (122 papers) found methods and reporting inconsistent (abstract only; their proposed definitions are **unverified**) [Europe PMC, DOI 10.1007/s40279-020-01375-9].
2. **The most common identical multi-zone LPS speed scheme is 1.94 / 3.89 / 5.00 m/s (7 / 14 / 18 km/h), but only 3 of 25 LPS speed studies used it** (Alonso Pérez-Chao ×2, Sosa); 8 studies used five zones with varying edges and 9 used a single high-speed zone (mean > 17.4 ± 1.2 km/h ≈ 4.83 ± 0.33 m/s [derivation], range 14.4–18.0 km/h). Of the 20 studies that referred specifically to "high-speed" or "high-intensity running", 16 (80%) used ~18 km/h (5.0 m/s). For sprinting, 7 of 12 studies used > 24.1 km/h (6.69 m/s) and 3 of 12 used > 21 km/h (5.83 m/s) [https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/]. NBA optical tracking as used in D'Amelio's thesis sets high-speed running (HSR) at > 4.0 m/s (14.4 km/h) [https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf].
3. **Acceleration thresholds split by technology.** LPS studies mostly use ±2.0 m/s² (mean initial threshold 2.0 ± 0.6); microsensor studies mostly use > 3.5, inherited from Catapult inertial movement analysis (IMA), which is not the same quantity as a position-derived acceleration [https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/], [https://www.jssm.org/jssm-19-204.xml-Fulltext]. NBA optical work counts high accelerations at > 3.5 m/s². Kinexon acc/dec events at 1.5 m/s² held ≥ 0.5 s are described by Stone 2022 as "dictated by the proprietary software" (a software setting; whether it is a vendor default is **unverified**) [https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full].
4. **Our placeholders against the literature:** walk < 2.0 and jog 2.0–4.0 m/s are within 0.06–0.11 m/s of the 7 and 14 km/h edges. Our own speed error is unknown until calibration step 5; the literature range runs from 0.20 m/s (best detected frames, wide soccer tactical feed) to ≥ 1.1 m/s (monocular broadcast), with 95% LoA up to about ±2 m/s even for fixed multi-camera NBA tracking (Section 7.1). Either way the 0.06–0.11 m/s difference is smaller than any plausible error. The 4.0 m/s edge equals the NBA HSR threshold. **The 5.5 m/s "sprint" edge is used by no basketball study found**; it matches a soccer high-intensity threshold (Carling, > 5.5 m/s) [https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2017.00432/full]. **The 2.5 m/s² acceleration edge** sits between the LPS (2.0) and IMU/NBA (3.5) conventions.
5. **NCAA D-I men's game peaks are modest:** guards 7.04 ± 0.39, forwards 6.63 ± 0.52, centres 6.23 ± 0.33 m/s (Kinexon, 10 players; 221 observations in the methods, 229 in the abstract, Table 3 sums to 224) [https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full]. Distance above 5.0 m/s is typically only 2–4 m per minute of court time [https://pmc.ncbi.nlm.nih.gov/articles/PMC7196749/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/]. Any top band therefore holds few metres, and those are where camera tracking is worst.
6. **Broadcast tracking error grows with speed and is worst for acceleration.** The best single-feed commercial broadcast tracking reached speed RMSE 0.34 m/s, but overall range was 0.34–2.38 m/s and total-distance bias −21.8% to +24.3%; acceleration was not evaluated [https://arxiv.org/pdf/2508.19477]. Monocular broadcast acceleration RMSE was 4.17 m/s² at a 0.20 s differentiation span and 0.93 m/s² at 1.64 s, but against ground truth derived from annotated trajectories with the same differentiation (not GPS, LPS or radar), with acceleration further smoothed by a 20-sample moving average; the authors flag possible bias [https://arxiv.org/pdf/2604.05636]. Even multi-camera TRACAB had R² 0.338 against an IMU for accelerations > 4 m/s² [Europe PMC, DOI 10.3390/s25061804].
7. **Absolute vs individual:** relative bands change individual high-speed distance substantially (fast players' Z4 161 m absolute vs 47.4 m relative, d = 1.75) [https://pmc.ncbi.nlm.nih.gov/articles/PMC12526517/], but single-anchor individualisation misinterpreted 39–61% of players' high-speed shares [Europe PMC, DOI 10.1055/s-0034-1384547] and game-derived acceleration anchors are unreliable even with GPS [Europe PMC, DOI 10.1371/journal.pone.0353385]. The literature recommends both: absolute for benchmarking, relative for individual monitoring.
8. **Recommendation (Section 9):** store per-player speed histograms at 0.1 m/s resolution so any band scheme is a view; make the primary absolute set 2.0 / 4.0 / 5.0 / 5.83 m/s; keep literature-exact and placeholder views; add a relative overlay anchored on a robust per-player reference speed; report accelerations at ±2.0 and ±3.0 m/s² only after both the stationary noise-floor test and the in-motion acceleration check pass (Section 10, steps 3 and 5b), labelled exploratory; never attempt PlayerLoad from video. By our own noise arithmetic (Section 7.3), if measured position error is above about 0.3 m, acceleration counts are expected to fail that gate.

---

## 2. Reviews that frame the field

| Review | Coverage | Key findings for thresholds | Source |
|---|---|---|---|
| Tuttle, Power, Dalbo, Scanlan 2024, Sports Med 54(10):2571 | 86 basketball studies: video time-motion analysis (TMA) 24, microsensors 33, LPS speed 25, LPS acceleration 22 | LPS speed: 9 single-zone studies had mean initial threshold > 17.4 ± 1.2 km/h (≈ 4.83 ± 0.33 m/s [derivation]), range 14.4–18.0 km/h (4.0–5.0 m/s); 16 of the 20 studies that referred to HSR/HIR (80%) used ~18 km/h (5.0 m/s); only 3 studies shared the identical 7/14/18 km/h four-zone scheme. Microsensors: the Discussion's "22 of 26 (85%) Catapult" uses a denominator of 26, not the 33 in the Results (not explained). Microsensor accel: mostly > 3.5 (mean 3.3 ± 0.3, range 2.5–3.5); three-zone 1.5–2.5 / 2.5–3.5 / > 3.5. LPS accel: mostly ±2.0 (mean 2.0 ± 0.6); no LPS study used 3.5. Jumps: 10 studies used > 40 cm. PlayerLoad zones 0–1 … 4–6 AU and relative 0–10% … 60–100% of peak. Recommends Delphi consensus, outcome validation, more relative-zone work, report decelerations as negatives, merge standing and walking, report direction, consider level-specific (k-means) thresholds, report hardware, sampling and filtering. Optical tracking excluded as "emerging" | https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/ |
| Russell, McLean, Impellizzeri, Strack, Coutts 2021, Sports Med 51(1):81 | 122 papers (76 male, 34 female, 9 both, as recorded from the abstract; these sum to 119 and the remaining 3 are not explained in the abstract) | Inconsistent methods and reporting; small, short studies. Full text not opened; operational definitions **unverified** | Europe PMC, DOI 10.1007/s40279-020-01375-9 |
| Stojanović et al. 2018, Sports Med 48(1):111 | 25 studies | 5–6 km of live play over 40 min, ~85% HRmax; HR and lactate fall in Q4; guards sprint and shuffle more. "70–90 m/min and 40–50 jumps per match" attributed to it in a secondary source: **unverified** | Europe PMC, DOI 10.1007/s40279-017-0794-z |
| Petway et al. 2020, PLoS One 15(3):e0229212 | 35 articles (20 elite, 9 sub-elite, 6 youth) | TMA zones stand/walk 0–1, jog 1.1–3.0, run 3.1–7.0, sprint > 7.0 m/s. High-intensity accel bands are one-sided: Svilar > 3.5 m/s² (decel < −3.5), Vázquez-Guerrero 2018 > 3 m/s² (decel < −3). NBA top speed from Caparrós 2017 (via Petway; n = 87): mean 8.09 ± 0.44, maximum 8.76 m/s. Elite total distance mean 4,369 m (1,991–6,310); elite match ranges 43–145 accelerations (1–15 high-intensity), 24–95 decelerations (4–40 high-intensity) | https://pmc.ncbi.nlm.nih.gov/articles/PMC7058381/ |
| Fox, Scanlan et al. 2022, Sports Med Open (female) | 32 studies on women | Speed schemes: Scanlan 1.1–3.0 / 3.1–7.0 / > 7.0; Reina 1.00–1.81 / 1.81–2.83 / 2.83–4.00 / > 4.0; Portes sprint > 5.8 m/s; shuffling bands ≤ 2 / > 2 m/s. Jumps counted at flight time > 0.40 s (Reina); high IMA ≥ 3.5 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9391561/ |
| Sweeting, Cormack, Morgan, Aughey 2017, Front Physiol 8:432 | Cross-sport | Accel cut-offs in use range 1.11–4.00 m/s²; the common 2.78 appears arbitrary. Soccer high-intensity > 5.5 m/s (Carling). Individualisation anchors: % max speed, VT2/vVT2, maximal aerobic speed (MAS). Data-mining options: k-means, self-organising maps, Gaussian mixtures. Always state minimum effort duration and filtering. "Limited research exists on court-based team-sports" | https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2017.00432/full |
| Clemente et al. 2023, Biol Sport (scoping) | 36 studies, 69.4% soccer, 1 basketball (PlayerLoad) | Anchors: maximal sprint speed (MSS) 41.7%, MAS + MSS + anaerobic speed reserve (ASR) 30.6%, VT2/RCT 5 studies. MSS from 40 m sprint (11) or match/training peak (8). 33.3% high risk of bias on exposure (test > 4 weeks from data) | https://pmc.ncbi.nlm.nih.gov/articles/PMC10286616/ |
| Delves et al. 2021 | 124 elite team-sport acceleration studies | Only 13% reported the filter and 32% the minimum effort duration (MED). MEDs in use: 0.5 s (19 studies), 0.4 s (8), 1 s (6), 0.2 s (3), 0.6 s (3), 2 s (1) | https://pmc.ncbi.nlm.nih.gov/articles/PMC8245618/ |
| Gualtieri et al. 2023 (pro soccer) | Review | No consensus on absolute thresholds; relative thresholds for sessions targeting near-maximal velocity | Europe PMC, DOI 10.3389/fspor.2023.1116293 |
| Power et al. 2022 (female basketball load) | Review | Methods too inconsistent to pool | Europe PMC, DOI 10.1186/s40798-022-00498-9 |

---

## 3. Speed zones and acceleration thresholds by study

Speeds in m/s with original km/h in brackets; accelerations in m/s² unless the source used IMA magnitude (Section 4.2).

| Study | Population (n) | Device, sampling | Speed bands (m/s) | Accel / decel bands (m/s²) | Typical values | Source |
|---|---|---|---|---|---|---|
| Vázquez-Guerrero et al. 2019 | 94 male U18 elite, EuroLeague Next Generation, 13 games, 266 records | WIMU PRO UWB LPS, positions 20 Hz, IMU 100 Hz | < 1.67 (< 6); 1.67–3.33 (6–12); 3.36–5.0 (12.1–18); 5.03–6.67 (18.1–24); > 6.69 (> 24.1) | > 2 / < −2; jumps "> 3 g" (≈ 29.4 m/s², device-axis magnitude, not centre-of-mass acceleration) | Q1 73–80 m/min (playing duration) → Q4 64–70; 18–24 km/h zone 1.8–3.2 m/min; > 24 km/h 0.03–0.22 m/min; acc > 2: 1.3–2.2/min; WIMU PL 1.26–1.50 AU/min (per-minute units inferred from methods and discussion; table unlabelled); peak 5.2–5.5 m/s per quarter [derivation from 18.75–19.64 km/h] | https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/ |
| Vázquez-Guerrero, Ayala, Garcia, Sampaio 2020 | Same 94 U18 | WIMU PRO 20 / 100 Hz | Same five zones | ±2 | Peak 60 s distance 113 (C), 120 (F), 123 (G) m; peak 300 s 395–439 m; peak 60 s acc count 6.2–7.3 | https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.00552/full |
| García, Vázquez-Guerrero, Castellano, Casals, Schelling 2020, JSSM 19:256 | 13 pro men, Spanish LEB Oro, 17 games, 708 records | WIMU PRO UWB 18 Hz, IMU 100 Hz | HSR > 5.0 (> 18) | ≥ 2 / ≤ −2; impacts > 8 g (≈ 78.5 m/s²); jumps > 3 g (≈ 29.4 m/s²); both device-axis magnitudes, not centre-of-mass acceleration | Per min total court time incl. stoppages (per-minute units inferred from the normalisation description "normalized by the total time spent on court"; Table 1 headers say m and counts): 72.4 m/min; > 18 km/h 3.2 m/min; acc 3.5/min; dec 3.1/min; peak 5.75 m/s; Q1 83.1 vs Q4 69.8 m/min | https://pmc.ncbi.nlm.nih.gov/articles/PMC7196749/ |
| Puente et al. 2017, JSCR 31(4):956 | 25 experienced men, one outdoor game | 15 Hz GPS + accelerometer | HSR > 5.0 (> 18) | Not in abstract | 82.6 ± 7.8 m/min; 3 ± 3% of distance > 18 km/h; max G 6.67, C 5.92 m/s | https://lida.sport-iat.de/ta/Record/4042881 ; https://repositorio.ucjc.edu/handle/20.500.12020/415 |
| Alonso Pérez-Chao et al. 2021 | 13 elite U18 men (Madrid), 9 games | Catapult ClearSky/Vector S7, LPS 10 Hz, IMU 100 Hz | ≤ 1.94 (≤ 7); 1.94–3.89 (7–14); 3.89–5.0 (14–18); > 5.0 (> 18) | > 2 / < −2 with **0.3 s dwell** | Peak demands 30 s–5 min; less prior playing time → higher peaks | https://pmc.ncbi.nlm.nih.gov/articles/PMC8558607/ |
| Alonso Pérez-Chao et al. 2023 | 13 U18 men, 270 quarter samples | Same | Same | ±2, 0.3 s | 1 min peak HSR 20.9 ± 10.8 m (quarters won) vs 17.4 ± 8.4 m (lost), p = 0.03, small | https://pmc.ncbi.nlm.nih.gov/articles/PMC10108746/ |
| Irid et al. 2025, Biol Sport 42(4):37 | INSEP elite youth, 20 M + 11 F, 40 games, 683 samples | Kinexon UWB 20 Hz + accelerometer 100 Hz | HSR > 5.0 (> 18) | ±2; jumps > 0.40 m; change of direction > 90° | Peak distance M / F: 10 s 251 / 237; 60 s 142.5 / 139.8 m/min; peak 60 s acc 4.6 / 3.7 per min | https://pmc.ncbi.nlm.nih.gov/articles/PMC12490299/ |
| **Stone et al. 2022** | **NCAA D-I men**, 10 players, 27 games, 221 observations (methods; abstract 229, Table 3 sums to 224) | Kinexon IMU, 20 Hz | No zones | acc/dec events ≥ 1.5 for ≥ 0.5 s ("as dictated by the proprietary software"); jump = minimum airtime 0.3 s; no sprint threshold given | Max speed C 6.23 ± 0.33, F 6.63 ± 0.52, G 7.04 ± 0.39 m/s; total decelerations C 308, F 397, G 362 | https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full |
| Vučković et al. 2026, MJSSM | 8 Hungarian 1st-league pros, 8 games | Kinexon UWB 20 Hz ("sub-10 cm", vendor claim) | Sprint event > 4.2 (> 15.12) for ≥ 0.5 s (threshold used in this study; whether it is a Kinexon default is **unverified**) | acc/dec > 1.5 for ≥ 0.5 s; jumps airtime ≥ 0.3 s (thresholds used in this study) | 66.6–72.1 m/min; max speed 6.6–6.7 m/s; 36–39 sprints/game; 304–455 acc/game; max decel −3.5 to −3.8; jumps 35–39 (backcourt), 67–77 (frontcourt) | https://www.mjssm.me/clanci/MJSSM_March_2026_Vuckovic.pdf |
| Ruiz-Álvarez et al. 2025, Sensors 25:6085 | 12 men, Spanish 4th division, 565 files (126 match) | Catapult Vector S7 LPS 10 Hz, IMU 100 Hz | Absolute < 1.94 / 1.94–3.92 / 3.92–5.0 / > 5.0; **relative < 29 / 29.1–58 / 58.1–75 / > 75% of peak** | – | Season peaks 7.0–8.0 m/s (k-means centroids 7.03 and 8.00); fast players Z4 161 vs 47.4 m (d = 1.75) | https://pmc.ncbi.nlm.nih.gov/articles/PMC12526517/ |
| Ibáñez, López-Sierra, Lorenzo, Feu 2023, Appl Sci 13:11936 | Liga ACB pros, 6 preseason games | Inertial + UWB | k-means: < 0.82; 0.82–2.11; 2.11–3.53; 3.53–4.86; > 4.86 | Not in abstract | – | https://oa.upm.es/82113/ |
| Ibáñez et al. 2024, Sensors | 68 ACB pros, 6 teams | WIMU PRO UWB 33 Hz, IMU 100 Hz | k-means top zone by position: G > 4.23, F > 4.59, C > 5.12 | k-means accel top clusters 5.32–12.25 and decel to −26 (implausible; likely differentiation noise — interpretation in our notes, not the authors') | > 96% of acc/dec in the two lowest zones | https://pmc.ncbi.nlm.nih.gov/articles/PMC10891821/ |
| Ibáñez, Gómez-Carmona, Mancha-Triguero 2022 | 22 Spanish women, 5v5 training | WIMU | k-means combined top zone 3.65–4.74 m/s; edges differ by level | Five k-means zones | Internal inconsistencies noted | https://pmc.ncbi.nlm.nih.gov/articles/PMC8749797/ |
| Reina et al. 2020 (PMC7084748; Tuttle ref [79], speed profile) | 48 U18 women, Final Four, 6 games | WIMU PRO + UWB | < 1.0; 1.0–1.81; 1.81–2.83; 2.83–4.0; sprint > 4.0 (> 14.4) | Not reported in this study (the > 2.5 and 1.0–2.5 / 2.5–4.0 / > 4.0 m/s² values are from two other Reina papers, Tuttle refs [44] and [97]; see below the table) | 112.7–124.0 m/min; sprint distance 196–235 m; 22–28 sprints; max 5.2–5.5 m/s | https://pmc.ncbi.nlm.nih.gov/articles/PMC7084748/ |
| Ben Abdelkrim et al. 2007, BJSM 41:69 | 38 Tunisian U19 elite men (TMA on 18) | Video TMA, 0.04 s | Categories (Abdelkrim scheme per Tuttle: walk ≤ 1.7, jog 1.7–3.3, run 3.4–5.0, stride 5.0–6.7, sprint > 6.7) | – | ~1,050 movements/game; 55 ± 11 sprints; 44 ± 7 jumps; 16.1% of live time high intensity | https://pmc.ncbi.nlm.nih.gov/articles/PMC2658931/ ; https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/ |
| Fox et al. 2020, Biol Sport | 8 semi-pro men | Catapult OptimEye S5 | – | High-intensity > 3.5 (IMA) for acc, dec, change of direction; jumps > 40 cm | PL 529–575 AU/game (5.3–5.7 AU/min); high-intensity acc 8–10, dec 9–11; jumps 56–65 total, 17 high | https://pmc.ncbi.nlm.nih.gov/articles/PMC7075230/ |
| Fox, Stanton, Scanlan 2018, RQES 89:103 | 15 semi-pro men | Catapult | – | – | PL competition 449 AU (4.35/min) vs training 624–632 AU (6.10–6.50/min) | https://lida.sport-iat.de/dbb/Record/4047641?lng=en ; https://researchonline.jcu.edu.au/62135/ |
| **Olthof et al. 2021** | **NCAA D-I men** (Power Five), 2 seasons, 263 + 278 observations (7 regular players per season; one observation is a row with "the game load and corresponding training loads of a player") | Catapult OptimEye S5, 100 Hz | – | IMA default 1.5 | Game PlayerLoad 810 ± 258 and 777 ± 272 AU | https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2021.670018/full |
| Heishman et al. 2020, JSSM 19:204 | 14 NCAA D-I men, 22 preseason practices | Catapult OptimEye T6, 100 Hz | – | IMA low 1.5–2.5, medium 2.5–3.5, high > 3.5 (reported in m/s) | Practice PL/min 5.4 ± 1.3 (W1) and 5.3 ± 1.2 (W2), the highest weeks (no overall average given); high IMA 70.9 (scholarship) vs 41.3 (walk-on) | https://www.jssm.org/jssm-19-204.xml-Fulltext |
| Heishman et al. 2020, Sports | 13 NCAA D-I men, off-season | Catapult T6 + ShotTracker indoor positioning system (IPS) | – | – | Distance vs PL r = 0.86–0.95; practice 1,198–1,940 m, PL 295–473 AU | https://pmc.ncbi.nlm.nih.gov/articles/PMC7183077/ |
| Towner et al. 2023 | 11 NCAA D-I women, 102 practices + 30 games | Catapult ClearSky T6 | – | High IMA ≥ 3.5 | PL 429–532 AU per session; 5.3–5.4 AU/min; jumps 76–113 | https://pmc.ncbi.nlm.nih.gov/articles/PMC10127672/ |
| Ransdell et al. 2020, JSCR 34:632 | 6 NCAA D-I women, 4 seasons | Catapult S5 | – | High IMA | PL 656 ± 173 AU, 7.1 AU/min, high IMA 52 ± 19, jumps 90 ± 33 per game, total-time basis (values via Fox 2022 review: PlayerLoad and IMA from its Table 10; the jump count sits in the "Jump" column of its Table 8, re-read from the Europe PMC full-text XML [https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9391561/fullTextXML]; Ransdell full text not opened) | https://lida.sport-iat.de/ta/Record/4062017?lng=en ; https://pmc.ncbi.nlm.nih.gov/articles/PMC9391561/ |
| **D'Amelio 2020 PhD (UTS), NBA** | 504 NBA players, 39,962 player-games (≥ 17.5 min) | Optical, 6 cameras, 25 Hz (SportVU cameras, Second Spectrum processing) | **HSR > 4.0 (> 14.4)**; k-means edges 2.17 / 4.36 / 5.98 | High accel **> 3.5** | 3,103 ± 1,044 m/game; 106–109 m/min played; HSR 694 m (23–26 m/min); total acc 185–206; high acc C 16, F 20, G 25; HSR/min CV ~15–16% | https://opus.lib.uts.edu.au/handle/10453/147346 ; https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf |
| Markerless 3×3, Paris 2024 | 32 women, Olympic 3×3, 24 games | 3 iPhone 13, 1080p, 25 fps, RTMPose 3D | Low < 2.5; moderate 2.5–3.5; high > 3.5 | ACC by > 3.5 m/s rule | Video "PlayerLoad" 13.6 (not comparable with Catapult) | https://pmc.ncbi.nlm.nih.gov/articles/PMC12568105/ |
| Rojas-Valverde et al. 2022, MHSalud | Basketball (population not visible) | – | Proposed from SDs of max speed: 0–2.78; 2.78–3.83; 3.83–4.89; 4.89–5.97; > 5.97 | – | Derivation formula not visible | https://kimuk.conare.ac.cr/Record/PUNA_968fbf7a8e7409822c0d3acdd0d22d47 |
| Sosa et al. 2021, Appl Sci 11:4390 | Spanish men, age categories, LPS | LPS | Zone edges **unverified** (Tuttle lists the 7 / 14 / 18 km/h scheme) | – | 3,189 ± 808 m; distance shares 43.5 / 36.6 / 14.7 / 5.2%; time shares 75.2 / 18.4 / 4.8 / 1.9% | https://abacus.universidadeuropea.com/entities/publication/c3e98425-cd12-4fb1-b849-02cd7eb0a30c |
| Schelling & Torres 2016, JSSM 15:585 | Basketball drills | 100 Hz accelerometer | – | – | Acceleration load/min 18.7 (3v3 full court), 17.9 (5v5), 14.6 (2v2), 13.8 (4v4) | https://www.jssm.org/jssm-15-585.xml-abst |

Other LPS and TMA schemes listed in Tuttle 2024 [https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/]: Castillo walk < 1.67, jog 1.67–3.33, cruise 3.36–5.0, HSR 5.03–6.67, sprint > 6.69; Portes high intensity 3.89–5.83, sprint > 5.83; Pino-Ortega high-intensity > 4.44; Garcia > 5.0 and > 5.83; Hulka low 0–3.0, medium 3.1–5.0, high > 5.1; Sampaio walk 0.2–2.0, jog 2.1–3.7, run 3.8–6.0, sprint > 6.1. Garcia used ±3.0 m/s²; Reina et al. 2020 (Int J Perform Anal; Tuttle ref [44], LPS) used a single > 2.5 m/s² acc and dec zone, while Reina et al. 2019 (Sports; Tuttle ref [97]) used 2.5 only as a zone edge (1.0–2.5 / 2.5–4.0 / > 4.0); neither is the PMC7084748 Reina 2020 study in the table. Ball et al. 2022 (Tuttle ref [57]; 14 professional women; Catapult OptimEye S5 microsensor) used acceleration ≥ 2.5 m/s², a microsensor (IMA-type) value, not a position-derived one.

Cross-sport speed references [https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2017.00432/full]: Australian football sprint > 4.00 or 4.17; soccer high-intensity > 5.5 (Carling); soccer sprint > 5.31 (Buchheit); rugby league sprint > 6.67 m/s. Vendor defaults: SciSports run > 4.17, high-intensity run > 5.56, sprint > 6.94 m/s each held ≥ 1.0 s (female 3.61 / 5.28 / 6.39, from 13 / 19 / 23 km/h), acceleration ≥ 3.0 m/s² for 0.5 s reaching ≥ 2.78 m/s [https://support.scisports.com/en/articles/4476826-physical-variables-glossary]; SkillCorner HSR 5.56 and sprint 6.94 m/s, high acceleration > 0.7 s at 3 m/s² [https://skillcorner.com/articles/new-feature-explosive-accelerations].

---

## 4. PlayerLoad-style measures and vendor definitions

### 4.1 PlayerLoad (Catapult)
- Definition: square root of the sum of squared instantaneous rates of change of acceleration on the three accelerometer axes, divided by 100, summed over time, in arbitrary units (AU) [https://www.jssm.org/jssm-19-204.xml-Fulltext], [https://pmc.ncbi.nlm.nih.gov/articles/PMC7183077/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC10127672/]. Catapult confirms the scaling factor of 100 and that PlayerLoad 2D drops the vertical axis [https://www.catapult.com/blog/fundamentals-playerload-athlete-work]. Accelerometer 400 Hz smoothed to 100 Hz: **unverified**.
- Typical values: NCAA D-I men 777–810 AU per game [https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2021.670018/full]; semi-pro men 449–575 AU per game, 4.35–5.7 AU/min [https://pmc.ncbi.nlm.nih.gov/articles/PMC7075230/], [https://lida.sport-iat.de/dbb/Record/4047641?lng=en]; NCAA D-I women 5.3–7.1 AU/min [https://pmc.ncbi.nlm.nih.gov/articles/PMC10127672/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC9391561/].
- PlayerLoad zones: instantaneous 0–1, 1–2, 2–3, 3–4, 4–6 AU (Leicht), plus 6–10 AU and relative 0–10% … 60–100% of each player's peak (Scanlan) [https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/].
- WIMU "player load" uses a similar jerk formula but runs ~1.2–1.5 AU/min, not Catapult's ~4–7 AU/min [https://pmc.ncbi.nlm.nih.gov/articles/PMC7196749/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/]. **Never compare PlayerLoad across vendors.**
- **Video cannot measure PlayerLoad**: it needs a body-worn accelerometer, and position-derived jerk is a third derivative, which is noise at our position error (Section 7.3).

### 4.2 Catapult inertial movement analysis (IMA)
- Fuses 100 Hz accelerometer and gyroscope with Kalman filtering; low, medium and high zones [https://www.catapult.com/blog/white-paper-introduction-ima]. Basketball bands low 1.5–2.5, medium 2.5–3.5, high > 3.5, **reported in m/s** (a velocity change), not m/s² [https://www.jssm.org/jssm-19-204.xml-Fulltext]. Catapult support pages stating the unit returned 403 (**unverified** beyond Heishman).
- Implication: the "3.5 m/s² microsensor threshold" in reviews is IMA magnitude and **not the same quantity** as a tracking-derived acceleration of 3.5 m/s².

### 4.3 Kinexon
- UWB LPS at 20 Hz plus IMU. Software setting: acceleration and deceleration events at 1.5 m/s² for ≥ 0.5 s, "as dictated by the proprietary software"; mechanical load from "a proprietary equation" (Stone 2022) [https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full]. Thresholds used in Vučković 2026 (Kinexon): sprint > 4.2 m/s (15.12 km/h) for ≥ 0.5 s, acc/dec > 1.5 m/s² for ≥ 0.5 s, jumps ≥ 0.3 s airtime [https://www.mjssm.me/clanci/MJSSM_March_2026_Vuckovic.pdf]; Stone 2022 also used 0.3 s minimum airtime. That any of these is a Kinexon **default** is **unverified** (no Kinexon document opened; kinexon.com pages returned 404).
- Validity vs Vicon (handball): r > 0.90 for peak speed, acceleration and deceleration, worst for high accelerations and decelerations in linear sprints near the side of the court (zone not defined in r/θ by the source) [https://www.termedia.pl/Validity-of-an-ultra-wideband-local-positioning-system-to-assess-specific-movements-in-handball,78,41138,0,0.html]; vs Qualisys (Blauberger 2021, Table 2): position RMSE 0.09 m (sport-specific course) and 0.08 m (small-sided games); speed RMSE 0.07 and 0.06 m/s; acceleration RMSE 0.20 and 0.18 m/s²; 4th-order Butterworth, 1 Hz cut-off for players [https://pmc.ncbi.nlm.nih.gov/articles/PMC7923412/], Table 2 re-read in the verification pass from the Europe PMC full-text XML [https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7923412/fullTextXML].
- Ten men's and 13 women's 2023 NCAA tournament teams used Kinexon, including Purdue and Iowa, not MSU (vendor news) [https://locationbusinessnews.com/kinexon-tracks-ncaa-basketball-tournament-players]. MSU men's basketball reportedly uses Catapult Vector: **unverified** (search snippet only; source page 404).

### 4.4 NBA tracking
- SportVU league-wide from 2013–14, Second Spectrum from 2017–18, both centre-of-mass point tracking at 25 fps [https://en.wikipedia.org/wiki/Player_tracking_(NBA)]; SportVU used 6 catwalk cameras at 25 images/s [https://www.tvtechnology.com/news/cameras-record-big-data-for-the-nba]. Sony Hawk-Eye pose tracking from 2023–24 [https://www.espn.com/nba/story/_/id/35818363/nba-use-hawk-eye-tracking-system-follow-players-ball], reported as 12 cameras and 29 body points [https://www.sportsvideo.org/?p=236963] or 14 cameras and 29 points [https://ministryofsport.com/exclusive-inside-the-nbas-player-tech-revolution/]. A 60 Hz rate is **unverified**.
- NBA.com publishes distance and "Avg Speed" (mph over all movement while on court) but no band thresholds [https://www.nba.com/stats/help/glossary]. Distance leader 4,667 m per game (source in miles; mid-season 2021–22 leaderboard at the time of writing; the article is internally inconsistent, crediting the same figure to "last season" in its introduction and giving 4,442 m for that player's previous season later); average speeds 1.63–2.10 m/s (source in mph; season not stated) [https://www.washingtoninformer.com/20-percent-of-nba-players-run-equivalent-of-5-marathons-throughout-a-season/].

### 4.5 A tracking-derived load index for MSU (proposal)
Since PlayerLoad is impossible from video, the closest feasible analogue is a Kinexon-style **mechanical load**: a weighted count of validated acceleration and deceleration efforts by intensity bin, plus distance in speed bands. It must be labelled as not comparable with Catapult PlayerLoad or Kinexon mechanical load. It should only be computed once the stationary noise floor and the in-motion acceleration check both pass (Section 10, steps 3 and 5b).

---

## 5. Jumps

| Threshold | Approx. height (h = g·t²/8) | Used by | Source |
|---|---|---|---|
| Airtime ≥ 0.30 s | 0.11 m [derivation] | Thresholds used in Vučković 2026 and Stone 2022 (Kinexon); vendor default **unverified** | https://www.mjssm.me/clanci/MJSSM_March_2026_Vuckovic.pdf ; https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full |
| Flight time > 0.40 s | 0.20 m [derivation] | Reina (women) | https://pmc.ncbi.nlm.nih.gov/articles/PMC9391561/ |
| > 0.40 m (high-intensity) | flight ≈ 0.571 s [derivation] | 10 studies; Irid 2025; Fox 2020 | https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/ ; https://pmc.ncbi.nlm.nih.gov/articles/PMC12490299/ ; https://pmc.ncbi.nlm.nih.gov/articles/PMC7075230/ |
| < 0.20 / 0.20–0.40 / > 0.40 m | – | Fox ×2, Scanlan | https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/ |
| Vertical IMA ≥ 0.254 m | – | Peterson | https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/ |
| "> 3 g" impact (≈ 29.4 m/s², device-axis magnitude) | – | WIMU studies | https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/ ; https://pmc.ncbi.nlm.nih.gov/articles/PMC7196749/ |

Per-game counts: U19 elite men 44 ± 7 (TMA, live time) [https://pmc.ncbi.nlm.nih.gov/articles/PMC2658931/]; LEB Oro men ~0.2 per min of total court time [https://pmc.ncbi.nlm.nih.gov/articles/PMC7196749/]; semi-pro men 56–65 total, 17 above 0.40 m [https://pmc.ncbi.nlm.nih.gov/articles/PMC7075230/]; Hungarian pros 35–39 backcourt vs 67–77 frontcourt [https://www.mjssm.me/clanci/MJSSM_March_2026_Vuckovic.pdf]; NCAA D-I women 90 ± 33 (Ransdell, "Jump" column of Fox 2022 Table 8, total-time basis) and semi-pro women 43 ± 6 [https://pmc.ncbi.nlm.nih.gov/articles/PMC9391561/], [https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9391561/fullTextXML]. Counts depend heavily on the detection threshold: sensor systems count low jumps that TMA misses.

From video, jumps need vertical information from pose (hip or ankle lift relative to the floor plane) or ball-and-rim geometry; `docs/requirements.md` already lists jump height as a pose-derived item. A video jump count should use estimated height ≥ 0.20 m (≈ 0.40 s flight) as the base threshold and > 0.40 m as the high-jump band, both validated against hand-labelled frames.

**Measurable video jump signature (exploratory until validated).**
- **Event:** both ankle keypoints above the per-player floor baseline for ≥ 0.30 s (≥ 9 frames at 30 fps; ≥ 18 at 60 fps). The floor baseline is the player's median ankle image height over the preceding 1.0 s of ground contact, mapped through the court homography; the floor plane is the court plane fixed by the calibrated lines (Section 10, step 2).
- **Height:** h = g·t²/8 from flight time t (s), g = 9.81 m/s², cross-checked against the pelvis keypoint's vertical lift (m), converted from pixels using the homography scale at the player's floor position plus a body-height prior from the roster.
- **Monocular depth ambiguity:** in a single view, vertical lift and movement towards or away from the camera both move keypoints up the image. The event therefore also requires the floor-projected ankle position (from the last contact frame) to stay within 0.5 m [assumption, to be tuned] while airborne is measured, and flight time is preferred over pixel lift as the height estimate.
- **Frame-quantisation error [derivation]:** take-off and landing are each known to ±1 frame, so t is uncertain by up to ±2 frames (±0.067 s at 30 fps, ±0.033 s at 60 fps). Since dh/dt = g·t/4, at t = 0.571 s (h = 0.40 m) one frame (0.033 s) shifts h by about ±0.05 m and two frames by about ±0.09 m at 30 fps; at the 0.20 m base threshold (t = 0.404 s), one frame shifts h by ±0.033 m. Every jump output carries the frame rate and this quantisation error.
- **Validation gap:** no study validating jump height or jump counts from broadcast pose was found in this research (Section 12). Jump outputs stay labelled exploratory until checked against hand-labelled take-off and landing frames.

---

## 6. Typical values and the denominator problem

| Denominator | Typical m/min | Examples | Source |
|---|---|---|---|
| Total court time incl. stoppages | 66–83 | García 72.4; Puente 82.6; Vučković 67–72; U18 quarters 64–80 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7196749/ ; https://lida.sport-iat.de/ta/Record/4042881 ; https://www.mjssm.me/clanci/MJSSM_March_2026_Vuckovic.pdf ; https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/ |
| Minutes played | 105–112 | NBA 106–109; by quarter 112 → 105 | https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf |
| Live or total game time (women) | 94–130 | Japanese collegiate ~100; Reina U18 113–124; Scanlan semi-pro 130 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9391561/ ; https://pmc.ncbi.nlm.nih.gov/articles/PMC7084748/ |
| Peak 60 s window | 113–143 | Vázquez-Guerrero 2020; Irid 2025 | https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.00552/full ; https://pmc.ncbi.nlm.nih.gov/articles/PMC12490299/ |
| Peak 10 s window | ~240–250 | Irid 2025 | https://pmc.ncbi.nlm.nih.gov/articles/PMC12490299/ |

Distance by band, elite U18 guards Q1 per minute of playing duration: < 1.67 m/s 30.3 m/min; 1.67–3.33 30.1; 3.33–5.0 16.7; 5.0–6.67 3.1; > 6.67 0.16. About 79% of distance is below 3.33 m/s and about 4% above 5.0 m/s [https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/]. NBA distance above 4.0 m/s: 694 m per game, ~22% of total [https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf].

Mapping onto our placeholders [derivation from the shares above, not measured on our edges]: walk < 2.0 m/s holds roughly 40–45% of distance and ~75% of time; jog 2.0–4.0 roughly 35–40% of distance; run 4.0–5.5 roughly 10–15%; sprint > 5.5 m/s about 1–3%.

Peak game speeds (m/s):

| Population | Peak | Source |
|---|---|---|
| U18 elite men (per quarter) | 5.2–5.5 [derivation from 18.75–19.64 km/h] | https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/ |
| LEB Oro men | 5.75 ± 0.42 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7196749/ |
| Outdoor guards / centres | 6.67 / 5.92 | https://repositorio.ucjc.edu/handle/20.500.12020/415 |
| Hungarian pros | 6.6–6.7 | https://www.mjssm.me/clanci/MJSSM_March_2026_Vuckovic.pdf |
| **NCAA D-I men** | **G 7.04, F 6.63, C 6.23** | https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full |
| U18 women | 5.2–5.5 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7084748/ |
| Japanese college / pro women | 7.4 / 8.0 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9391561/ |
| NBA single team (Caparrós 2017, via Petway review; n = 87) | mean top 8.09 ± 0.44, max 8.76 (treat with caution: secondary source; a "low total distance" caveat in an earlier draft is **unverified**, as Petway reports no total distance for this study) | https://pmc.ncbi.nlm.nih.gov/articles/PMC7058381/ |
| Liga EBA season peaks incl. training | 7.0–8.0 | https://pmc.ncbi.nlm.nih.gov/articles/PMC12526517/ |

Straight-line capacity: NBA Draft Combine three-quarter-court sprint, drafted players 1999–2018: frontcourt 3.35 ± 0.13 s, backcourt 3.23 ± 0.10 s [https://pmc.ncbi.nlm.nih.gov/articles/PMC7601684/]. The distance (22.86 m, reported in feet) is **unverified** (snippets only; the opened test list gave no distance [https://www.topendsports.com/sport/basketball/testing-nba-draft.htm]). If correct, mean speed is 6.8–7.1 m/s from a standing start [derivation].

---

## 7. What broadcast-camera tracking can measure

### 7.1 Validation benchmarks (error budgets)

| System | Sampling, filter | Position RMSE (m) | Speed RMSE (m/s) | Accel RMSE (m/s²) | Notes | Source |
|---|---|---|---|---|---|---|
| TRACAB Gen5 multi-camera (soccer) vs Vicon | 25 Hz; 4th-order Butterworth 1 Hz on positions (residual optimum 1–1.5 Hz) | 0.08 | 0.08 | 0.21 | Gen4: 0.09 / 0.09 / 0.26; Gen4 15 m sprint accel RMSE 0.68; Gen4 1.08% erroneous frames (> 1 m), mostly ID swaps; Gen4 distance −19% below 1.67 m/s, +9% at 5.6–6.9 m/s; Gen5 within ±5% | https://pmc.ncbi.nlm.nih.gov/articles/PMC7064167/ |
| SportVU 3 cameras (soccer) vs Vicon | 16 fps, raw | 0.56 ± 0.16 | 0.41 ± 0.08; by band 0.33 (0.28–1.67), 0.43 (1.67–4.17), 0.49 (4.17–5.56), 0.50 (5.56–6.94), 0.61 (≥ 6.94 m/s) | 0.91 ± 0.19 | High-speed distance error up to 97.6% (video) in small-sided games; > 40% for every system. Do not compare KPIs across systems | https://pmc.ncbi.nlm.nih.gov/articles/PMC6056042/ |
| NBA optical (6 cameras, Second Spectrum) vs radar, 49 × 20 m sprints | 25 Hz | – | Bias +0.11 (low band), −0.24 (medium), −0.27 (high), **−0.42 (maximal)**; 95% LoA by band (thesis Table 3.1, km/h ÷ 3.6): low −1.67 to +1.89, medium −2.11 to +1.63, high −1.50 to +0.97, maximal −2.01 to +1.19 m/s (half-widths ≈ 1.2–1.9 m/s); within-band r 0.08 (maximal) | – | Caution using it "for assessing instantaneous velocity across narrow activity bands" | https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf |
| Commercial broadcast-feed AI tracking (World Cup 2022, 3 providers) vs TRACAB Gen5 | 50 fps captured, 25 fps stored; 1 Hz Butterworth on speed | 1.68–16.39 overall; detected 0.44–1.14 (Providers 1–2), 0.44–2.23 across providers; 4.62–12.23 undetected | 0.34–2.38 overall (best: bias 0.02, LoA −0.63 to 0.67); 0.20–0.46 detected; 0.78–1.13 undetected | Not evaluated | Total-distance mean bias −21.8% to +24.3% across providers and feeds; Providers 1–2: camera 1 feed −0.74% to −5.73%, tactical feed +1.20% to +3.78%; Provider 3: +14.54% to +24.32%. **Detection 89–96% (tactical feed) vs 36–64% (programme and camera 1 feeds combined; programme feed alone 36–42% in the detection table)**; 720p vs 1080p no meaningful effect. Acceptability ~1 m and ~1 m/s | https://arxiv.org/pdf/2508.19477 ; https://arxiv.org/abs/2508.19477 |
| Monocular broadcast speed/accel (SoccerNet GSR, 25 fps) | Differentiation span 0.20–1.64 s; Kalman vs Savitzky-Golay | – | **1.73 at 0.20 s → 1.10 at 1.64 s**; r 0.62 → 0.88 | **4.17 at 0.20 s → 0.93 at 1.64 s**; r 0.09 → 0.72 | **Not a physical-truth validation:** error is against speed and acceleration derived from annotated trajectories with the same differentiation window, not against GPS, LPS or radar; the authors say this "can introduce a potential bias" and under-represent high-frequency motion, and call for a GPS benchmark. Acceleration is further smoothed by a central 20-sample moving average, so the RMSE does not reflect the differentiation span alone. Top 30% most reliable athletes: speed MAE 0.23, accel MAE 0.26; bottom 30%: speed MAE 1.08, accel RMSE 2.71; these groups are selected post hoc by a reliability score built from the same speed MAE, so the split is circular, and Table 3 lists top-30% speed RMSE 0.132 below MAE 0.234, which is impossible (RMSE ≥ MAE), so it contains a reporting error. Errors are on moving athletes' tracks, not a stationary noise floor. Gaps > 3 frames (0.12 s) not interpolated; speeds > 15 m/s removed | https://arxiv.org/pdf/2604.05636 |
| Broadcast soccer pipeline vs 25 Hz multi-camera | Main camera | mean 1.66–2.52, median 1.13–1.66; 61–79% of frames within 2 m | – | – | ~95% homography IoU still gives ~1 m mean error | https://arxiv.org/pdf/2110.11107 |
| Basketball court registration (KaliCalib, DeepSport) | Single image | Challenge re-projection error metric (called "MSE" by the authors, reported in cm): 126.61 cm test, 140.14 cm challenge set; **76.5% of per-image values on the test set below 1 m**; no homography for 2 test images | – | – | Challenge baseline 592.48 cm; overall error divided by 4.7 vs baseline. Re-checked in the verification pass from the PDF (Section 4.4 and Table 1) | https://arxiv.org/pdf/2209.07795 ; https://arxiv.org/abs/2209.07795 |
| Early 25 Hz optical, basketball (Pers 2002, via D'Amelio) | Unsmoothed | 0.28 (centre court) vs 0.64 (boundary) | 2.00–2.10 | – | Error depends on court location (zones as named by the source, not in r/θ; our zones are defined in Section 10, step 2) | https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf |
| Single-camera basketball (DeepLabCut) vs optoelectronic, 10 youth | – | – | ICC 0.78–0.94; errors rose with task speed; velocity curves differed at 90° cuts | Not reported | | https://sponet.de/sponet/Record/4097236?lng=en |
| Catapult ClearSky T6 indoor (handball) vs Qualisys | Raw | 0.21 optimal / 1.79 sub-optimal | Instantaneous speed error 33–39% raw | – | Walls and corners degrade accuracy | https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2018.00115/full |
| Catapult ClearSky UWB indoor vs Vicon | Filtered | – | Linear drills 0.2–12% | Decel worse | Change-of-direction drills moderate to very large differences near the side of the court | Europe PMC, DOI 10.1080/02640414.2017.1411867 |

Optical vs wearable in matches: Second Spectrum vs GPS (EPL) r² > 0.99 but optical higher for total distance (+4%), HSR (+12%) and sprint distance (+18%) [https://www.termedia.pl/Interchangeability-of-external-player-load-variables-from-different-athlete-tracking-systems-in-English-Premier-League-soccer-players,78,56509,0,0.html]; TRACAB vs Catapult ICC 0.974 (distance), 0.766 (HSR distance), 0.640 (sprint count) [Europe PMC, DOI 10.1177/00368504231187501]; TRACAB + Mediacoach vs IMU R² 0.954 for total accelerations, 0.956 for 2–4 m/s², **0.338 above 4 m/s²**, with optical under-counting decelerations (d = 1.17) [Europe PMC, DOI 10.3390/s25061804]. Optical tracks near the pelvis, wearables sit between the scapulae, and the two diverge more at high speed and acceleration [https://pmc.ncbi.nlm.nih.gov/articles/PMC10761404/].

### 7.2 Sampling rate
- Typical rates: optical 25 Hz, LPS 10–50 Hz, GNSS 10 Hz [https://pmc.ncbi.nlm.nih.gov/articles/PMC10761404/]. US broadcast at 29.97 or 59.94 fps is general knowledge, **unverified** as a sourced figure; our B1G+ recording rate is an open question in `docs/requirements.md`.
- **A higher frame rate does not by itself reduce speed or acceleration error** [derivation, consistent with https://arxiv.org/pdf/2604.05636]: error is governed by position noise and the differentiation span, and one-frame differences amplify noise more at 60 fps than at 30 fps. 60 fps helps detection, motion blur and identity continuity, which do reduce error indirectly.

### 7.3 How position noise propagates [derivation]
*Corrected in the verification pass: the earlier version used one "span S" that meant the full window for speed but the step h for acceleration, so its acceleration rows described windows twice as long as labelled and understated acceleration noise by 4× at a given window.*

Definitions, used everywhere in this document: **W = full window** (s) between the first and last sample used; **h = W/2** is the step on each side of the centre sample. For independent (white) per-frame position noise σ_p:
- Three-point estimates (only the two end samples and the centre are used): speed σ_v = √2·σ_p / W = σ_p / (√2·h); acceleration (second difference with step h) σ_a = √6·σ_p / h² = 4√6·σ_p / W².
- Least-squares estimates (a quadratic fitted to **all** frames in the window, i.e. a Savitzky-Golay-type filter, here at 30 fps): noise falls roughly with the square root of the number of frames, so σ_a is about 0.35–0.6 of the three-point value for W = 0.5–1.6 s.
- The three-point column is a pessimistic bound for a given window and the least-squares column an optimistic one; real errors are not white (see below), so the truth for our pipeline lies between them and must be measured (Section 10, steps 3 and 5b). "Share > 2.5" assumes Gaussian noise: share = 2·(1 − Φ(2.5/σ_a)).

| σ_p (m) | Full window W (s) [step h] | σ_v three-point (m/s) | σ_a three-point (m/s²) | Share \|noise\| > 2.5 m/s², three-point | σ_v LS (m/s) | σ_a LS (m/s²) | Share > 2.5, LS |
|---|---|---|---|---|---|---|---|
| 0.10 (multi-camera grade) | 0.2 [0.1] | 0.71 | 24.5 | 92% | 0.57 | 19.6 | 90% |
| 0.10 | 0.5 [0.25] | 0.28 | 3.92 | 52% | 0.16 | 2.38 | 29% |
| 0.10 | 1.0 [0.5] | 0.14 | 0.98 | 1.1% | 0.06 | 0.45 | ~0% |
| 0.30 (optimistic; below any broadcast value found) | 1/15 [1/30, minimum at 30 fps] | 6.36 | 661 | ~100% | – | – | – |
| 0.30 | 0.2 [0.1] | 2.12 | 73.5 | 97% | 1.70 | 58.9 | 97% |
| 0.30 | 0.5 [0.25] | 0.85 | 11.8 | 83% | 0.49 | 7.14 | 73% |
| 0.30 | 1.0 [0.5] | 0.42 | 2.94 | 40% | 0.18 | 1.36 | 6.6% |
| 0.30 | 1.6 [0.8] | 0.27 | 1.15 | 3.0% | 0.09 | 0.43 | ~0% |
| 0.50 (best detected broadcast frames, Crang) | 0.5 [0.25] | 1.41 | 19.6 | 90% | 0.81 | 11.9 | 83% |
| 0.50 | 1.0 [0.5] | 0.71 | 4.90 | 61% | 0.30 | 2.26 | 27% |
| 0.50 | 1.6 [0.8] | 0.44 | 1.91 | 19% | 0.15 | 0.72 | 0.05% |
| 1.00 (typical broadcast, Theiner mean 1.66–2.52 m; Crang detected up to 2.23 m) | 0.5 [0.25] | 2.83 | 39.2 | 95% | 1.63 | 23.8 | 92% |
| 1.00 | 1.0 [0.5] | 1.41 | 9.80 | 80% | 0.60 | 4.53 | 58% |
| 1.00 | 1.6 [0.8] | 0.88 | 3.83 | 51% | 0.30 | 1.44 | 8.2% |

Sources for the σ_p levels: detected-frame broadcast position RMSE 0.44–1.14 m (Providers 1–2) and up to 2.23 m across providers [https://arxiv.org/pdf/2508.19477]; broadcast soccer mean 1.66–2.52 m [https://arxiv.org/pdf/2110.11107]; court re-projection metric 1.27 m on the test set [https://arxiv.org/pdf/2209.07795]; multi-camera 0.08–0.09 m [https://pmc.ncbi.nlm.nih.gov/articles/PMC7064167/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC7923412/]. No broadcast source found reaches 0.30 m. All table values [derivation].

Full window needed for acceleration noise SD < 0.5 m/s² [derivation]:

| σ_p (m) | Three-point: step h / full window W (s) | Least-squares at 30 fps: full window W (s) |
|---|---|---|
| 0.10 | 0.70 / 1.40 | 0.97 |
| 0.30 | 1.21 / 2.42 | 1.53 |
| 0.50 | 1.57 / 3.13 | 1.87 |
| 1.00 | 2.21 / 4.43 | 2.47 |

Implications: acceleration counts from broadcast tracking are dominated by noise unless positions are smoothed over a full window of at least about 1 s even at multi-camera-grade σ_p, and 1.5–2 s at σ_p 0.3–0.5 m, **and** a minimum dwell is applied. Windows that long blunt real basketball accelerations, many of which last under 1 s, so peak and count values would be biased low. **Honest consequence: if our measured σ_p on detected frames is above about 0.3 m, acceleration counts are expected to fail the go/no-go gate (Section 10, step 3) and will not be reported.** The single minimum effective full window for any acceleration output is **W ≥ 1.0 s** (used in Sections 9.4 and 10, step 4); this is necessary, not sufficient: the gate in Section 10 decides. Real errors are not white: homography drift acts as a slowly varying bias, while identity swaps and re-detections create spikes, which is why raw broadcast accelerations above 50 m/s² appear [https://arxiv.org/pdf/2001.07692] and why unfiltered UWB k-means clusters ran above 12 m/s² [https://pmc.ncbi.nlm.nih.gov/articles/PMC10891821/]. Jerk (third derivative) is not measurable at these noise levels.

### 7.4 Smoothing
- 4th-order zero-lag Butterworth at 1 Hz on positions is the validation standard for TRACAB [https://pmc.ncbi.nlm.nih.gov/articles/PMC7064167/], Kinexon [https://pmc.ncbi.nlm.nih.gov/articles/PMC7923412/] and the broadcast validation (on speed) [https://arxiv.org/pdf/2508.19477]. A common 1 Hz filter cut between-manufacturer acceleration RMSD from 1.77 to 0.27 m/s² [Europe PMC, DOI 10.1080/02640414.2022.2051332]. For 10 Hz GNSS vs Vicon, 2 Hz was best (bias 0.00, LoA ±1.55, RMSE 0.79 m/s²) [https://www.citedrive.com/en/discovery/accuracy-of-gnss-derived-acceleration-data-for-dynamic-team-sport-movements-a-comparative-study-of-smoothing-techniques/]. Applying a 1 Hz filter to a section of data shifted a system's speed RMSD against the criterion from about 0.03 to about 0.08 m/s (their Fig. 6 compares 1 vs 5 Hz filtering); an early 8 Hz cut-off let step oscillations through [https://pmc.ncbi.nlm.nih.gov/articles/PMC10761404/].
- Savitzky-Golay: databallpy default window 7, order 2 [https://databallpy.readthedocs.io/en/latest/getting_started/preprocessing_options.html]; Bou used window 9, order 2; differences between Savitzky-Golay and Kalman shrink as the differentiation span increases, and Kalman had better temporal correlation (r and max-lag r) with the reference [https://arxiv.org/pdf/2604.05636]. SciSports used a Kalman filter with Newtonian mechanics on 10 Hz football trajectories [https://arxiv.org/pdf/1808.04550].
- **Processing can change counts by orders of magnitude**: in AFL GNSS data, average high-zone (≥ 3 m/s²) acceleration efforts per player file (262 player files, no minimum playing time; not stated as per game) were 224 raw, 138 with custom processing (2 Hz Butterworth, central difference, 0.3 s minimum, ±2 and ±3 m/s²) and 3 with manufacturer processing; high-zone acceleration distance averaged 1,380 m raw vs 7.5 m manufacturer-processed (up to 184× lower), and manufacturer efforts were up to 89× lower than raw [https://pmc.ncbi.nlm.nih.gov/articles/PMC11244311/].

### 7.5 Minimum dwell times (minimum effort duration)
- Varley et al. 2017 (10 Hz GPS, MED 0.1–0.9 s): different velocity filters changed HSR and sprint counts by ES 0.28–1.09 when MED < 0.5 s, and acceleration counts (≥ 2.78 m/s²) by ES −5.69 to 0.26 when MED < 0.7 s; counts fell exponentially as MED rose; MEDs below ~0.4 s split one sprint into several accelerations unless an effort ends when acceleration returns to ≤ 0 m/s²; a software filter upgrade caused large drops in counts [Europe PMC, DOI 10.1123/ijspp.2016-0534], [https://hira.hope.ac.uk/1821/1/HIRA%20Submission.pdf].
- In use: 0.3 s (Pérez-Chao, basketball) [https://pmc.ncbi.nlm.nih.gov/articles/PMC8558607/]; 0.5 s (the Kinexon software setting in Stone 2022 and the threshold used in Vučković 2026; the most common MED) [https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full], [https://pmc.ncbi.nlm.nih.gov/articles/PMC8245618/]; 0.7 s (SkillCorner) [https://skillcorner.com/articles/new-feature-explosive-accelerations]; 1.0 s for speed efforts (SciSports) [https://support.scisports.com/en/articles/4476826-physical-variables-glossary]. PlayerData 0.5 s at ±3 m/s²: **unverified**.
- Basketball context [derivation]: a full-court sprint of 28.65 m at 6–7 m/s takes about 4–5 s including build-up, and half-court bursts are shorter, so a 1.0 s speed MED keeps genuine efforts while a 0.5 s acceleration MED is near the duration of a real first step.

### 7.6 Occlusion, pan and zoom, off-screen players
- Detection drives the error: undetected (extrapolated) frames carry 4.6–12 m position error, and the programme and camera 1 feeds together detected only 36–64% of frames (programme feed alone 36–42%) vs 89–96% for the tactical feed [https://arxiv.org/pdf/2508.19477].
- Off-screen time is **not missing at random**: in simulated broadcast soccer, players were off camera 35–52% of the time and moved faster on camera; models predicted off-screen total distance with RMSPE 183 m (CV 0.05) but very-high-speed distance (> 5.7 m/s) with CV 0.31 [https://arxiv.org/pdf/2001.07692]. Graph-network imputation of off-screen players beat baselines (no load-error numbers in the abstract) [Europe PMC, DOI 10.1038/s41598-022-12547-0].
- In basketball [derivation], the broadcast camera follows the ball, so most players are in frame in the half-court, but in transition the players getting back on defence, leak-outs and trailers are most often out of frame. This biases sprint and high-speed counts low for exactly the actions the transition requirements (Job D) care about.
- Identity swaps when players bunch caused TRACAB Gen4's erroneous frames [https://pmc.ncbi.nlm.nih.gov/articles/PMC7064167/]; frequent three-or-more-player occlusion in basketball is **unverified** (snippet only). Frame-to-frame calibration error during pans becomes spurious velocity [derivation, from https://arxiv.org/pdf/2110.11107].
- Dead-ball filtering: one basketball sensor study removed dead-ball time when all five players stayed below about 2.5–2.8 m/s (9–10 km/h) for 2.5 s [https://arxiv.org/pdf/1806.10412].

### 7.7 Verdict table for MSU broadcast tracking

| Metric | Verdict | Basis |
|---|---|---|
| Court position for tactics (spacing, shot location) | OK when detected and calibration verified (~0.5–1.5 m); no sub-metre claims | https://arxiv.org/pdf/2508.19477 ; https://arxiv.org/pdf/2110.11107 ; https://arxiv.org/pdf/2209.07795 |
| Total distance per player-game | Programme feed: −22% to +24% mean bias across providers in the only broadcast validation (soccer); within about ±6% only for Providers 1–2 on camera 1 (−0.74% to −5.73%) and tactical (+1.20% to +3.78%) feeds with high detection; Provider 3 +14.54% to +24.32%. MSU verdict pending coverage (Section 10, step 1) and the step-5 checks; always report coverage | https://arxiv.org/pdf/2508.19477 ; https://arxiv.org/pdf/2001.07692 |
| Mean speed, time and distance in broad bands (< 2, 2–4, 4–5 m/s) | OK only if step 5 gives band-wise 95% LoA narrower than the band width (2.0 m/s for the 2–4 m/s band; 1.0 m/s for 4–5 m/s), on detected frames with W ≥ 1.0 s smoothing. Our speed error is unknown until step 5; literature range 0.20 m/s (best detected frames, wide soccer tactical feed) to ≥ 1.1 m/s (monocular broadcast, 1.64 s span), and 95% LoA up to about ±2 m/s even for fixed multi-camera NBA tracking (D'Amelio) | https://arxiv.org/pdf/2508.19477 ; https://arxiv.org/pdf/2604.05636 ; https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf |
| High-speed and sprint distance (> 5 m/s) | Fragile: > 40% deviation even for professional systems; negative bias at high speed; off-screen bias | https://pmc.ncbi.nlm.nih.gov/articles/PMC6056042/ ; https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf ; https://arxiv.org/pdf/2001.07692 |
| Robust peak speed (1 s rolling mean, top-3 games or P99) | OK as an anchor if artefacts are screened | https://www.skillcorner.com/articles/skillcorner-releases-new-peak-velocity-metric ; https://arxiv.org/pdf/2001.07692 ; https://sponet.de/sponet/Record/4097014?lng=en |
| Single-frame maximum speed | Not reliable | https://arxiv.org/pdf/2604.05636 ; https://sponet.de/sponet/Record/4097014?lng=en |
| Acceleration/deceleration counts at 2–3 m/s² | Exploratory; noise-dominated unless smoothed over W ≥ 1.0 s with an MED; reported only if the stationary and in-motion checks pass (Section 10, steps 3 and 5b); expected to fail if σ_p > ~0.3 m | Section 7.3; https://arxiv.org/pdf/2604.05636 ; https://pmc.ncbi.nlm.nih.gov/articles/PMC11244311/ |
| High-intensity accelerations > 3.5–4 m/s² | Not reliable (R² 0.338 even for multi-camera TRACAB above 4 m/s²) | Europe PMC, DOI 10.3390/s25061804 |
| Individual acceleration-speed profile, %-of-a_max bands | Not reliable from game data even with GPS | Europe PMC, DOI 10.1371/journal.pone.0353385 |
| Jerk; PlayerLoad | Not measurable | Section 7.3; Section 4.1 |
| Jump count and height | Possible only from pose; exploratory; signature and frame-quantisation error in Section 5; no broadcast-pose validation found | Section 5 |
| Change of direction and movement direction | Exploratory; signature in Section 9.5; same validation gates as accelerations | Section 9.5 |

---

## 8. Absolute vs individualised bands

### 8.1 Definitions
Absolute (fixed) bands use the same edges for everyone. Individualised bands anchor on % of maximal sprint speed or match peak speed, % of maximal aerobic speed, anaerobic speed reserve (ASR = MSS − MAS), physiological thresholds (VT2), % of maximal acceleration, or data-driven clusters. Pimenta et al. 2026 argue most "individualised" schemes are normalisation, sensitive to the reference chosen, and propose each athlete's maximum speed registered up to the point of monitoring [Europe PMC, DOI 10.3389/fspor.2026.1873257].

### 8.2 Evidence

| Study | Sport, n | Comparison | Effect | Source |
|---|---|---|---|---|
| Ruiz-Álvarez et al. 2025 | Basketball, 12 men, 565 files | 7 / 14 / 18 km/h vs < 29 / 29–58 / 58–75 / > 75% of peak | Fast players, matches: Z4 161 vs 47.4 m (d = 1.75); Z3 400 vs 259.5 m (d = 0.85); Z1 1,336 vs 1,599 m (d = 0.41). Slow players Z4 86.9 vs 45.1 m (d = 0.93). The percentages match 7 / 14 / 18 ÷ 24.1 km/h (29.0 / 58.1 / 74.7%) [derivation]; the paper mentions "an arbitrary peak speed of 24.1 km/h" for comparability but does not state this formula, so the construction is our inference. Methods and abstract disagree on whether the peak was per quarter or per season stage | https://pmc.ncbi.nlm.nih.gov/articles/PMC12526517/ |
| Scanlan et al. 2021 | Basketball, 13 semi-pro men, PlayerLoad | Individual (% of peak) vs fixed software zones | Fixed: more zone-2 time (11.9 ± 1.2 vs 9.3 ± 2.4 min, large) and zone-3 time (1.7 vs 0.8 min, moderate) | https://lida.sport-iat.de/ta/Record/4071579?lng=en |
| Lovell & Abt 2013 | EPL soccer, 8 | VT-individualised vs arbitrary | 41% between-player difference in high-intensity distance vs 5–7% with fixed bands; use both "in synergy" | Europe PMC, DOI 10.1123/ijspp.8.4.456 |
| Abt & Lovell 2009; Lovell & Abt 2012 (via Sweeting) | Soccer | vVT2 vs fixed 5.5 m/s; fixed 4.0 m/s | +167% distance at vVT2; fixed 4.0 overestimated by 9% on average, −22% to +33% individually | https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2017.00432/full |
| Clarke, Anson, Pyne 2015 | Women's rugby sevens, 12 | 5 m/s vs VT2 speed (mean 3.5 m/s) | 5 m/s underestimated high-intensity running by up to 30%; individuals ±14% from mean VT2 | Europe PMC, DOI 10.1080/02640414.2014.988740 |
| Hunter et al. 2015 | U18 soccer, 12 players, 22 fixtures (50 eligible match observations), 5 Hz GPS | Single vs multi-anchor | MSS alone misinterpreted 61% of players' %HSR and 39% of %VHSR; RCT estimated from MAS misinterpreted %HSR in 50% of cases; **do not individualise on one characteristic** | Europe PMC, DOI 10.1055/s-0034-1384547 |
| Rago et al. 2020 | Pro soccer, 13, 302 files | Arbitrary vs MAS/ASR | r = 0.67–0.78 but ES 0.86–5.47; not interchangeable | Europe PMC, DOI 10.2478/hukin-2019-0113 |
| Abbott et al. 2018 | EPL academy, 31 | Accel 1–2 / 2–3 / > 3 vs 25 / 50 / 75% of max acceleration | High-capacity athletes had more acceleration distance in all zones under global thresholds (p < 0.01); no difference for low-capacity | Europe PMC, DOI 10.1519/jsc.0000000000002875 |
| Silva et al. 2024 | Portuguese 1st division, 20, 34 matches | Sprint > 7.0 m/s vs 70–90% of season peak | Absolute 134.5 ± 103.5 m; relative minus absolute +135.8 m (70%) to −122.9 m (90%); relative reduced positional differences; suggest > 80% | https://pmc.ncbi.nlm.nih.gov/articles/PMC11167479/ |
| Andrey et al. 2026 | 159 youth elite soccer, GPS | Game-derived acceleration-speed profile vs test | Validity TEE ~7%, ~12%, ~17% ("extremely large"); more games did not help; relative acceleration thresholds "still require a test-based approach" | Europe PMC, DOI 10.1371/journal.pone.0353385 |
| Massard et al. 2018 | 23 semi-pro soccer | Match peak vs test | Match peak 8.72 m/s, 0.22–0.32 m/s above tests; derive from "a series of matches" | https://researchers.westernsydney.edu.au/en/publications/peak-speed-determination-in-football-is-sprint-testing-necessary/ |
| Kyprianou et al. 2022 | 12 elite youth soccer | Match peak vs 40 m test | Test 8.76 ± 0.39 vs match 7.94 ± 0.49 m/s (~9% lower); sprint testing needed | https://www.research.ed.ac.uk/en/publications/to-measure-peak-velocity-in-soccer-let-players-sprint-peak-veloci/ |
| Djaoui et al. 2017 | Soccer | Match %MSS by position | Wide players reach higher %MSS; no numbers in abstract | https://lida.sport-iat.de/ta/Record/4043474?lng=en |
| Fischer-Sonderegger et al. 2021 | Laser reference | v_max bias | 15 Hz GPS −3.3 to −1.0%; an LPS −12.4 to +1.5%, worst with repeated changes of direction | https://pmc.ncbi.nlm.nih.gov/articles/PMC8064559/ |

Cautions: Catapult notes that peak-speed-anchored zones assume fast players also have high aerobic speed, and that fixed percentages such as 50% of peak have no physiological basis [https://www.catapult.com/blog/individualisation-gps-speed-thresholds-challenges-complexities]. Clustering only mirrors the tracking and filtering: noisy derivatives produced implausible acceleration clusters [https://pmc.ncbi.nlm.nih.gov/articles/PMC10891821/]. Peak match speed can be distorted by collisions; plot speed-time and acceleration-time together and exclude artefacts [https://sponet.de/sponet/Record/4097014?lng=en]. In basketball [derivation], the 28.65 m court limits straight-line build-up, so match peaks are likely further below test MSS than in soccer, and any %-of-peak band must state which peak.

### 8.3 Recommendation
Store both. Use **absolute bands as the primary, published scheme** (benchmarking against literature, opponents and seasons, and stable under fitness change), and a **relative overlay for individual interpretation** of speed only. This is what Tuttle 2024, Ruiz-Álvarez 2025, Silva 2024 and Lovell & Abt 2013 recommend [https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC12526517/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC11167479/], [Europe PMC, DOI 10.1123/ijspp.8.4.456]. Do not individualise accelerations from game video (Andrey 2026). Because we have no fitness tests, the relative anchor must be a robust match-derived peak, which Kyprianou 2022 shows sits below test MSS; treat it as a "match reference speed", not maximal sprint speed.

---

## 9. Recommended band set for MSU Alpha 3

### 9.1 Storage principle
Store, per player per stint, **time and distance in 0.1 m/s speed bins** (0–10 m/s) and acceleration efforts with their peak, duration and start speed. Every band scheme below is then a view computed afterwards, so changing a threshold never requires reprocessing video. This also lets us report literature-exact edges (1.94, 3.89, 6.69 m/s) alongside rounded ones.

### 9.2 Primary absolute speed bands

Speeds are of the tracked point defined in Conventions (court-plane speed, m/s, after the chosen filter, point type recorded).

| Band | MSU primary (m/s) | Placeholder (m/s) | Literature anchor | Justification | Status |
|---|---|---|---|---|---|
| Stand–walk | < 2.0 | < 2.0 (kept) | < 1.94 (7 km/h), Catapult/ACB scheme | Difference of 0.06 m/s; our speed error is unknown until calibration step 5 (literature range 0.20 m/s best detected wide-feed frames to ≥ 1.1 m/s monocular broadcast; 95% LoA up to about ±2 m/s even for fixed multi-camera NBA tracking), so the difference is immaterial whatever the error turns out to be; Tuttle recommends merging standing and walking | Reported with coverage once step 5 band-wise LoA are known |
| Jog | 2.0–4.0 | 2.0–4.0 (kept) | 1.94–3.89 (7–14 km/h) | Difference ≤ 0.11 m/s; 4.0 m/s equals the NBA HSR edge, giving NBA comparability for free | As above; OK only if step-5 LoA narrower than 2.0 m/s |
| Run | 4.0–5.0 | 4.0–5.5 (changed) | 3.89–5.0 (14–18 km/h) | 5.0 m/s is the threshold used by 16 of the 20 basketball LPS studies that referred to HSR/HIR (Tuttle); the full 7/14/18 km/h scheme was shared by only 3 studies | As above; OK only if step-5 LoA narrower than 1.0 m/s |
| High-speed running (HSR) | 5.0–5.83 | – (new) | > 5.0 (18 km/h) | Lets "distance > 5.0 m/s" match the dominant literature measure | **Fragile (Section 7.7)**: reported as observed with coverage; counts only after step 5 band-wise LoA |
| Sprint | > 5.83 | > 5.5 (replaced) | > 5.83 (21 km/h): Portes, Garcia, 3 of 12 LPS studies | 5.5 m/s is a soccer value with no basketball use. > 6.69 m/s (24 km/h) would be near-empty for NCAA players (centre peak 6.23, forward 6.63) and is where broadcast speed is most negatively biased (−0.42 m/s at maximal speeds) | **Fragile (Section 7.7)**: reported as observed with coverage; counts only after step 5 band-wise LoA |

Sources for the table: https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/ ; https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf ; https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full ; https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2017.00432/full.

Secondary views, all computed from the same histograms:
- **Literature-exact Catapult/ACB:** < 1.94 / 1.94–3.89 / 3.89–5.0 / > 5.0 m/s [https://pmc.ncbi.nlm.nih.gov/articles/PMC8558607/].
- **WIMU/EuroLeague:** < 1.67 / 1.67–3.33 / 3.33–5.0 / 5.0–6.67 / > 6.67 m/s [https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/].
- **NBA:** HSR > 4.0 m/s [https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf].
- **Kinexon sprint event (threshold used in Vučković 2026; vendor default unverified):** > 4.2 m/s held ≥ 0.5 s [https://www.mjssm.me/clanci/MJSSM_March_2026_Vuckovic.pdf].
- **Placeholder (kept, never deleted):** 2.0 / 4.0 / 5.5 m/s, labelled "non-standard in basketball; soccer-derived 5.5 m/s edge".

Speed efforts (HSR and sprint counts): above threshold for **≥ 1.0 s** on detected frames, with a sensitivity view at 0.5 s for Kinexon comparability.

### 9.3 Individualised overlay (speed only)
1. **Reference speed v_ref** per player: compute the 1 s rolling mean of filtered speed on detected frames; take each game's maximum (G1); v_ref = median of the player's top 3 G1 values to date, updated cumulatively. Store P99 of 1 s speeds above 4.17 m/s (the SkillCorner PSV-99 analogue) as a second anchor [https://www.skillcorner.com/articles/skillcorner-releases-new-peak-velocity-metric], [https://arxiv.org/pdf/2001.07692]. Mark v_ref provisional until the player has ≥ 5 games each with detected coverage ≥ 70% of on-court time (provisional numbers, to be revised from the variance on our first games); player-stints with detected coverage < 70% of on-court time are excluded from G1.
2. **Artefact screen** before G1: drop speeds > 10 m/s (team-sport peaks are about 10 m/s per [https://arxiv.org/pdf/2508.19477]; Bou removed > 15 m/s [https://arxiv.org/pdf/2604.05636]), windows that span undetected frames or identity changes, and peaks accompanied by implausible acceleration [https://sponet.de/sponet/Record/4097014?lng=en]. Provisional artefact rule (to be revised): |a| > 6 m/s² sustained ≥ 0.2 s, or a speed jump > 2 m/s between consecutive frames (6 m/s² sits below the peak accelerations of 6–7 m/s² measured in agility drills by Blauberger 2021 Table 3, so it may need raising after step 5b [https://pmc.ncbi.nlm.nih.gov/articles/PMC7923412/]).
3. **Percentages calibrated to our team**: set the relative edges so that the team-median player's relative edges equal the absolute edges. This is analogous to Ruiz-Álvarez, whose percentages match the absolute edges divided by the 24.1 km/h (6.69 m/s) sprint threshold (our inference; the paper does not state the formula [https://pmc.ncbi.nlm.nih.gov/articles/PMC12526517/]); we divide by the team-median v_ref instead. Worked example [derivation]: if the team-median v_ref were 6.63 m/s (the NCAA D-I forward mean in Stone 2022), the edges 2.0 / 4.0 / 5.0 / 5.83 m/s become 30.2 / 60.3 / 75.4 / 87.9% of v_ref, close to Ruiz-Álvarez's 29 / 58 / 75%. Using the unrounded 75.4% (5.0 ÷ 6.63), the relative HSR edge would be 5.31 m/s for a guard at 7.04 m/s and 4.70 m/s for a centre at 6.23 m/s (rounding to 75% would give 5.28 and 4.67 m/s). The stored percentages keep one decimal so that edges are reproducible.
4. Report relative and absolute side by side; never replace one with the other.

### 9.4 Acceleration and deceleration

| Band | Edge (m/s²) | Status | Justification |
|---|---|---|---|
| Moderate acc / dec | ≥ +2.0 / ≤ −2.0 | Primary once validated | Modal LPS threshold [https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/]; comparable with Pérez-Chao, Irid, García, Vázquez-Guerrero |
| High acc / dec | ≥ +3.0 / ≤ −3.0 | Primary once validated | Comparability with Garcia (±3.0), SciSports and SkillCorner (3 m/s²) [https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/], [https://support.scisports.com/en/articles/4476826-physical-variables-glossary], [https://skillcorner.com/articles/new-feature-explosive-accelerations]. The multi-camera agreement with IMUs (R² 0.956 for 2–4 m/s², TRACAB + Mediacoach, soccer) [Europe PMC, DOI 10.3390/s25061804] does **not** transfer to monocular broadcast; by Section 7.3, ±3.0 m/s² is noise-dominated at any σ_p ≥ 0.3 m unless W ≥ ~1.5 s |
| Placeholder | ≥ +2.5 / ≤ −2.5 | Kept as a view | In Tuttle 2024, Reina et al. 2020 (ref [44], LPS) used > 2.5 m/s² as its single acc/dec threshold and Ball et al. 2022 (ref [57]) used ≥ 2.5 m/s², a microsensor (IMA-type) value; Reina 2019 (ref [97]) used 2.5 only as a zone edge [https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/] |
| NBA high acceleration | ≥ +3.5 | Not reported unless the in-motion check (Section 10, step 5b) passes for this band; matches Section 7.7 ("not reliable") | NBA comparability only; do not confuse with Catapult IMA 3.5 |
| > 4 m/s² | – | Not reported | Optical R² 0.338 above 4 m/s² |

Effort rules: positions smoothed (Section 10), acceleration from the smoothed series over a full window W ≥ 1.0 s (Section 7.3 definitions; necessary, not sufficient); effort must stay beyond threshold **≥ 0.5 s** and ends when acceleration crosses 0 m/s² [Europe PMC, DOI 10.1123/ijspp.2016-0534], [https://pmc.ncbi.nlm.nih.gov/articles/PMC11244311/]; never count an effort spanning undetected or interpolated frames, and do not bridge gaps longer than 0.12 s [https://arxiv.org/pdf/2604.05636]. All acceleration outputs carry an "exploratory" label until both the stationary noise-floor test (Section 10, step 3) and the in-motion acceleration check (step 5b) pass. Decelerations are stored as negative values (Tuttle).

### 9.5 Other measures
- **Jumps:** pose-derived, base ≥ 0.20 m, high > 0.40 m, event = both ankles above the floor baseline for ≥ 0.30 s, height from flight time with its frame-quantisation error (Section 5); exploratory.
- **Change of direction and movement direction (exploratory; requested by Tuttle 2024, "report direction", and used by Irid 2025 at > 90°)** [https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC12490299/]: change of direction = heading change of the smoothed court-plane velocity vector ≥ 45° (moderate) or ≥ 90° (sharp) within ≤ 1.0 s while speed ≥ 2.0 m/s throughout; direction class per sample from the angle between the velocity vector and the body-facing direction from the hip or shoulder keypoints (forward ≤ 45°, lateral 45–135°, backward ≥ 135°), with time and distance stored per class. Heading is undefined at low speed, hence the 2.0 m/s floor. Gated by the same validation steps as accelerations (Section 10, steps 3, 5b and 6).
- **Peak demands:** rolling 30, 60, 120 and 300 s peaks of distance, HSR distance and acceleration efforts; more robust than instantaneous values and the current reporting standard [https://pmc.ncbi.nlm.nih.gov/articles/PMC8558607/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC12490299/].
- **Denominators:** store m/min against live time, minutes played and total on-court time separately (Section 6).
- **Mechanical load index:** Section 4.5, after validation, clearly labelled non-comparable.
- **No PlayerLoad from video.**

---

## 10. Calibration plan on our data

No wearables are available, so calibration is self-validation on our own footage, plus a wearable or radar comparison only if MSU or a partner later allows it.

1. **Record conditions first.** Log frame rate, resolution and feed type (wide vs programme) for every game; the B1G+ frame rate is an open question in `docs/requirements.md`. Compute per-player detected-frame coverage; all load outputs carry it. Provisional rule (to be revised): player-stints with detected coverage < 70% of on-court time are excluded from load summaries and shown only as "insufficient coverage".
2. **Position error budget.** Hand-annotate the tracked point (Conventions: pelvis floor projection, or ankle midpoint) on a few hundred frames spread across court zones, zoom levels and pans, and compute position RMSE (m) per zone and separately for each end of the court. Check homography against known court lines (the 28.65 m length, 15.24 m width, key and 3-point arc). Target: ≤ 0.5 m on detected frames; flag frames whose line reprojection exceeds 1 m (KaliCalib's challenge metric was below 1 m on 76.5% of test images [https://arxiv.org/pdf/2209.07795]).
   **Calibration zones** (r in m, θ in degrees from the right baseline at the rim centre, per `config/vocabulary_map.yaml`; r and θ measured from the rim of the half the player is in):
   - Paint / inside: r < 4.57 m (the elbow radius in the vocabulary map).
   - Mid-range: 4.57 ≤ r < 6.75 m.
   - Perimeter corners: r ≥ 6.60 m and θ ≤ 12° or θ ≥ 168° (vocabulary "corner").
   - Perimeter wings: r ≥ 6.75 m, 12° < θ ≤ 60° or 120° ≤ θ < 168° (vocabulary "wing").
   - Perimeter slots and top: r ≥ 6.75 m, 60° < θ < 120° (vocabulary "slot" and "top").
   - Deep frontcourt: r ≥ 9.0 m within the frontcourt [assumption: a band beyond normal shooting range, to be tuned].
   - Backcourt (relative to the attacking direction): distance from the half-court line in 0–5 m, 5–10 m and > 10 m bands, with r and θ measured from the far rim. With the rim centre about 1.6 m from the baseline, the half-court line lies about 12.7 m from the rim centre [derivation from the 28.65 m court length; the rim offset is **unverified** in this document].
   Report RMSE (m) per zone, per court end, and per zoom level.
3. **Noise floor (stationary).** Use players standing still during free throws and timeouts: report residual speed and acceleration distributions after filtering. Go/no-go targets (hypothesis new-62 below): speed noise < 0.3 m/s and acceleration noise < 0.5 m/s² (SD). If acceleration noise exceeds this, acceleration counts are not reported. This test measures only position jitter; it misses motion blur, pose and foot-point changes, identity swaps, pans and zoom, and extrapolation through undetected frames, so passing it is necessary but not sufficient (step 5b).
   **Consistency with the step-2 target (implied windows) [derivation, Section 7.3].** A position target of 0.5 m and an acceleration-noise target of 0.5 m/s² are compatible only with long smoothing windows. Full window W needed for σ_a < 0.5 m/s²: σ_p 0.1 m → 1.4 s (three-point) / 1.0 s (least-squares, 30 fps); σ_p 0.3 m → 2.4 / 1.5 s; σ_p 0.5 m → 3.1 / 1.9 s. Windows that long remove most real basketball accelerations, so **if measured σ_p is above about 0.3 m, acceleration counts are expected to fail this gate**. The single minimum effective full window for acceleration used throughout this document is W ≥ 1.0 s (Sections 7.3 and 9.4); the gate, not the window, decides whether accelerations are reported.
4. **Choose the filter.** Run Winter residual analysis on our positions with 4th-order zero-lag Butterworth candidates at 1, 1.5 and 2 Hz [https://pmc.ncbi.nlm.nih.gov/articles/PMC7064167/], [https://www.citedrive.com/en/discovery/accuracy-of-gnss-derived-acceleration-data-for-dynamic-team-sport-movements-a-comparative-study-of-smoothing-techniques/], and compare with a constant-velocity Kalman/RTS smoother and Savitzky-Golay (order 2) [https://arxiv.org/pdf/2604.05636]. For speed, a Savitzky-Golay full window of 0.3–0.5 s may be tested; for acceleration the full window is ≥ 1.0 s (Section 7.3). Record filter type, cut-off or window, frame rate and tracked-point type in every output.
5. **Speed check on known efforts.** Time players between court lines on clear straight-line runs (hand-timed frame counts over known distances) and compare with tracked mean speed; fit bias and 95% limits of agreement by speed band, as D'Amelio did against radar [https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf]. Gate for a speed band: 95% LoA narrower than the band width (Section 7.7).
5b. **In-motion acceleration check.** Hand-label ≥ 50 start-from-standstill events, ≥ 50 hard stops and ≥ 50 cuts of about 90°, with frame-counted displacement over known line-to-line distances (e.g. baseline to free-throw line, 5.79 m; lane width 3.66 m [standard NCAA markings; **unverified** in this document]). Fit a constant-acceleration model to the labelled positions of each event and compare peak and mean acceleration (m/s²) and effort duration (s) with the pipeline. Gate: bias and 95% LoA reported by band (2–3 m/s², 3–4 m/s², > 4 m/s²); a band is reported only if its LoA half-width is smaller than the distance from the band's lower edge to the next lower edge (1.0 m/s² for the ±2/±3 bands). Hypothesis new-62 has a stationary and an in-motion condition; both must pass.
6. **Sensitivity curves.** For each count (HSR efforts, sprints, acc/dec efforts, changes of direction), plot counts against MED (0.3, 0.5, 0.7, 1.0 s) and threshold (±0.25 m/s for speed edges, ±0.5 m/s² for acceleration edges). Publish the curves. Provisional instability rule (to be revised): a band is flagged unstable if its count changes by > 20% for a 0.1 s MED change or for a 0.25 m/s speed-edge change (0.5 m/s² for acceleration edges).
7. **Distribution check.** Inspect our speed and acceleration histograms after the first games and run k-means as a cross-check against the chosen edges (as D'Amelio and Ibáñez did), not as the definition.
8. **Off-screen handling.** Quantify off-screen share by game phase (transition vs half-court) and report HSR and sprint values as "observed" with coverage; test a Mortensen-style regression or graph imputation for totals only [https://arxiv.org/pdf/2001.07692], [Europe PMC, DOI 10.1038/s41598-022-12547-0].
9. **v_ref stability.** Track v_ref against the number of games; freeze relative percentages only when the team-median v_ref changes by less than the step-5 speed bias (or 0.1 m/s, whichever is larger) between successive games, and every player in it has ≥ 5 games with ≥ 70% coverage.
10. **External anchor (optional).** If any MSU game appears in a public multi-camera tracking set, or if wearable or radar data become available for practice segments, fit band-wise bias and limits of agreement and apply a regression alignment as recommended for optical vs wearable data [https://www.termedia.pl/Interchangeability-of-external-player-load-variables-from-different-athlete-tracking-systems-in-English-Premier-League-soccer-players,78,56509,0,0.html].

---

## 11. Belief register entries (Job C format)

Markets: no source opened in this research links in-game physical load measures to betting prices. `docs/research/odds_markets_research.md` records travel and injury adjustments in some public models (relevant to H10), not in-game load. So for every entry below, whether markets price it is **not known**.

Proposed new hypothesis IDs continue the shared sequence of `docs/research/beliefs_register.md`, which already uses new-1 to new-59 (it renumbered the per-batch IDs of earlier research batches; `neutral_site_proximity.md` separately uses its own new-1 to new-8). This document therefore uses **new-60 to new-65**. An earlier draft numbered them new-1 to new-6 (old new-1 → new-60, new-2 → new-61, new-3 → new-62, new-4 → new-63, new-5 → new-64, new-6 → new-65); these entries are not yet in the register. The requirements session assigns final IDs, and JEV hypotheses keep their numbers.

| ID | Belief | Evidence for | Evidence against | Markets | How to test |
|---|---|---|---|---|---|
| new-60 | Running intensity (m/min, HSR m/min) falls from Q1 to Q4 | NBA 39,962 player-games: distance per minute played 112 → 105, HSR/min 28 → 22, Q1 vs Q4 ES ≈ 1.0–1.28 [https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf]; U18 EuroLeague declines in all positions [https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/]; LEB Oro 83.1 vs 69.8 m/min [https://pmc.ncbi.nlm.nih.gov/articles/PMC7196749/]; ACB UWB declines (ηp² 0.17–0.18; 14 players, 3 games) [Europe PMC, DOI 10.3389/fphys.2026.1713000]; HR and lactate fall in Q4 [Europe PMC, DOI 10.1007/s40279-017-0794-z] | NBA Q4 absolute distance is higher (964 vs 923 m in Q1) but absolute HSR is lower (202 vs 226 m) (D'Amelio thesis Table 4.3); that the higher Q4 distance reflects more minutes is our inference, not stated in the thesis [https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf]; peak speed does not decline (García); Q4 stoppages inflate total-time denominators; rotation, score and pacing confound; prior playing time lowers peaks [https://pmc.ncbi.nlm.nih.gov/articles/PMC8558607/] | Not known | Video/tracking: m/min by quarter on minutes-played denominator, mixed model with player random effect, controlling for score margin and pace. Play-by-play gives only proxies (possessions per minute) |
| new-61 | A player's robust 1 s peak speed per stint falls with continuous minutes on the floor | Within-game decline studies above; requirements line on within-game decline | Pacing, matchups and role changes; no NCAA test found | Not known | Video/tracking: mixed model of stint peak speed on stint minutes and quarter, player random effect |
| new-62 | After filtering, our broadcast tracking meets two conditions (prerequisite for any acceleration count): **(a) stationary:** speed noise SD < 0.3 m/s and acceleration noise SD < 0.5 m/s² for players standing still; **(b) in motion:** on hand-labelled starts, hard stops and ~90° cuts, acceleration bias and 95% LoA by band pass the step-5b gate | Weak, not independent: Bou 2026 top-30% reliable athletes, speed MAE 0.23 m/s, accel MAE 0.26 m/s², but error is against annotation-derived trajectories processed with the same differentiation (not GPS/LPS/radar), the authors flag possible bias, the top/bottom 30% are selected post hoc by a reliability score that uses the same speed error, acceleration is additionally smoothed by a 20-sample moving average, and Table 3 speed RMSE (0.132) < MAE (0.234) indicates a reporting error [https://arxiv.org/pdf/2604.05636]. Multi-camera systems reach 0.20–0.21 m/s² acceleration RMSE [https://pmc.ncbi.nlm.nih.gov/articles/PMC7064167/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC7923412/], but with ~0.1 m position error, not broadcast | Bou overall accel RMSE 0.93–4.17 m/s² even against its own annotation-derived reference; noise derivation (Section 7.3): at σ_p ≥ 0.3 m, σ_a < 0.5 m/s² needs a full window of about 1.5–2.4 s; broadcast detected-frame position RMSE 0.44–2.23 m [https://arxiv.org/pdf/2508.19477] | Not applicable | Tracking only: (a) free-throw and timeout stationary segments; (b) in-motion check, Section 10, step 5b |
| new-63 | Players reach higher running intensity in quarters their team wins | U18: 1 min peak HSR 20.9 vs 17.4 m (p = 0.03, small); 5 min PL 54.1 vs 50.5 AU [https://pmc.ncbi.nlm.nih.gov/articles/PMC10108746/] | No game-level differences (same study; Hungarian pros n = 8 [https://www.mjssm.me/clanci/MJSSM_March_2026_Vuckovic.pdf]); NCAA women's high IMA higher in losses [https://lida.sport-iat.de/ta/Record/4062017?lng=en]; reverse causality; Fox 2021 "Not all about the effort?" findings **unverified** | Not known | Video/tracking plus quarter scores from play-by-play |
| new-64 | Using relative instead of absolute speed bands changes the positional ordering of high-speed distance (guards vs bigs) | Ruiz-Álvarez d up to 1.75 [https://pmc.ncbi.nlm.nih.gov/articles/PMC12526517/]; Silva: relative thresholds reduced positional differences [https://pmc.ncbi.nlm.nih.gov/articles/PMC11167479/]; Lovell & Abt 41% [Europe PMC, DOI 10.1123/ijspp.8.4.456] | Hunter 2015 single-anchor misclassification [Europe PMC, DOI 10.1055/s-0034-1384547]; relative zones hide real speed differences; video peaks biased low | Not applicable | Tracking: both band sets on the same tracks; compare ordering, game-to-game CV (NBA HSR/min CV ~15–16%) and links to outcomes |
| new-65 | Higher-level players cover less distance but have more high-speed capacity | Petway 2020 review (35 studies) [https://pmc.ncbi.nlm.nih.gov/articles/PMC7058381/] | Stojanović 2018: higher-level players have greater intermittent workload [Europe PMC, DOI 10.1007/s40279-017-0794-z]; denominator and method dependence | Not applicable | Tracking: MSU vs opponents from the same pipeline, stratified by opponent rating |
| (method) | Match-derived peak speed is an adequate individual anchor | Massard 2018 (match ≥ test in soccer) | Kyprianou 2022 (match ~9% below test); short basketball court [derivation] | Not applicable | Tracking: v_ref stability vs games; compare with NBA Combine sprint times for MSU alumni where published |
| (method) | Broadcast tracking can count accelerations | Bou top-30% (weak, not independent; see new-62); TRACAB R² 0.956 at 2–4 m/s² (multi-camera soccer; does not transfer to broadcast) | Bou overall RMSE; TRACAB R² 0.338 > 4 m/s²; Andrey 2026 | Not applicable | Noise floor and in-motion check (new-62), MED sensitivity, hand-labelled cuts |

---

## 12. Gaps and open items

- No NCAA men's game study with LPS speed zones was found; NCAA D-I men's game data are Kinexon IMU (Stone 2022) and Catapult PlayerLoad (Olthof 2021). No NCAA women's LPS speed study either.
- Full texts not opened: Stojanović 2018 and Russell 2021 (abstracts only); Svilar 2018 (> 3.5 m/s² via Petway); Scanlan 2011; Puente 2017 full methods; Sampaio 2015 NBA; Caparrós 2017 (secondary only, via Petway); Sosa 2021 zone edges; Rojas-Valverde 2022 derivation; Catapult IMA defaults (support pages 403); a Catapult rolling-average summary behind a login (**unverified**).
- Torres-Ronda 2016 could not be located; the closest match is Schelling & Torres 2016 [https://www.jssm.org/jssm-15-585.xml-abst].
- No published basketball validation of Second Spectrum or Hawk-Eye acceleration; the only NBA optical validation found is D'Amelio's sprint-velocity study.
- No validation of jump height or jump counts from broadcast pose was found; video jump outputs (Section 5) stay exploratory until our own hand-labelled check.
- No validation of acceleration from monocular broadcast against a physical reference (GPS, LPS, radar or motion capture) was found; Bou 2026 compares against annotation-derived trajectories only.
- Kinexon vendor defaults (sprint > 4.2 m/s, jump airtime ≥ 0.3 s, acc/dec 1.5 m/s² for 0.5 s) are **unverified** as defaults; only their use in Stone 2022 and Vučković 2026 is sourced.
- Ransdell 2020 full text not opened; its jump count (90 ± 33) is taken from the Fox 2022 review table.
- Our own speed and position error are unknown until calibration steps 2 and 5; no literature value can stand in for them.
- MSU's own device (Catapult Vector) is **unverified**.
- US broadcast frame rates, Hawk-Eye 60 Hz, basketball multi-player occlusion statistics and PlayerData definitions are **unverified**.
- Pages attempted but not usable (not cited for any claim): pubmed.ncbi.nlm.nih.gov (cookie wall), acuresearchbank.acu.edu.au (403), link.springer.com (login), support.catapultsports.com and onesupport.catapultsports.com (403), kinexon.com basketball pages (404), support.playerdata.com (SSL error), mdpi.com (403 or expired certificate), revistas.una.ac.cr (CAPTCHA), ddd.uab.cat (access denied), unleash.catapult.com (login), healthpartnerships.msu.edu (404), researchonline.ljmu.ac.uk (404), enauka.gov.rs (500), archives.rpd-online.com (connection refused).

---

## Sources

Every URL below was opened during this research (Job E notes, 2026-10-17). Europe PMC records were retrieved from the REST API by DOI.

Reviews and basketball studies
1. https://pmc.ncbi.nlm.nih.gov/articles/PMC11467009/ — Tuttle et al. 2024, intensity zones in basketball (systematic review)
2. https://pmc.ncbi.nlm.nih.gov/articles/PMC7058381/ — Petway et al. 2020, load by competition level (review)
3. https://pmc.ncbi.nlm.nih.gov/articles/PMC9391561/ — Fox et al. 2022, female basketball load (review)
4. https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2017.00432/full — Sweeting et al. 2017, "When is a sprint a sprint?"
5. https://pmc.ncbi.nlm.nih.gov/articles/PMC10286616/ — Clemente et al. 2023, individualised thresholds (scoping review)
6. https://pmc.ncbi.nlm.nih.gov/articles/PMC8245618/ — Delves et al. 2021, acceleration reporting in team sports (review)
7. https://pmc.ncbi.nlm.nih.gov/articles/PMC6720027/ — Vázquez-Guerrero et al. 2019, U18 EuroLeague by quarter
8. https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2020.00552/full — Vázquez-Guerrero et al. 2020, peak windows
9. https://pmc.ncbi.nlm.nih.gov/articles/PMC7196749/ — García et al. 2020, LEB Oro (also https://jssm.org/jssm-19-256.xml)
10. https://lida.sport-iat.de/ta/Record/4042881 — Puente et al. 2017 abstract
11. https://repositorio.ucjc.edu/handle/20.500.12020/415 — Puente et al. 2017 repository record (max speeds)
12. https://pmc.ncbi.nlm.nih.gov/articles/PMC8558607/ — Alonso Pérez-Chao et al. 2021
13. https://pmc.ncbi.nlm.nih.gov/articles/PMC10108746/ — Alonso Pérez-Chao et al. 2023
14. https://pmc.ncbi.nlm.nih.gov/articles/PMC12490299/ — Irid et al. 2025, INSEP Kinexon
15. https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full — Stone et al. 2022, NCAA D-I men Kinexon
16. https://www.mjssm.me/clanci/MJSSM_March_2026_Vuckovic.pdf — Vučković et al. 2026, Hungarian pros Kinexon
17. https://pmc.ncbi.nlm.nih.gov/articles/PMC12526517/ — Ruiz-Álvarez et al. 2025, absolute vs relative zones
18. https://pmc.ncbi.nlm.nih.gov/articles/PMC10891821/ — Ibáñez et al. 2024, ACB k-means
19. https://oa.upm.es/82113/ — Ibáñez et al. 2023, ACB k-means speed ranges
20. https://pmc.ncbi.nlm.nih.gov/articles/PMC8749797/ — Ibáñez et al. 2022, women's basketball k-means
21. https://kimuk.conare.ac.cr/Record/PUNA_968fbf7a8e7409822c0d3acdd0d22d47 — Rojas-Valverde et al. 2022
22. https://abacus.universidadeuropea.com/entities/publication/c3e98425-cd12-4fb1-b849-02cd7eb0a30c — Sosa et al. 2021 abstract
23. https://pmc.ncbi.nlm.nih.gov/articles/PMC7084748/ — Reina et al. 2020, U18 women
24. https://pmc.ncbi.nlm.nih.gov/articles/PMC2658931/ — Ben Abdelkrim et al. 2007
25. https://pmc.ncbi.nlm.nih.gov/articles/PMC7075230/ — Fox et al. 2020, semi-pro men Catapult
26. https://lida.sport-iat.de/dbb/Record/4047641?lng=en — Fox, Stanton, Scanlan 2018 record
27. https://researchonline.jcu.edu.au/62135/ — Fox, Stanton, Scanlan 2018 repository record
28. https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2021.670018/full — Olthof et al. 2021, NCAA D-I men PlayerLoad
29. https://www.jssm.org/jssm-19-204.xml-Fulltext — Heishman et al. 2020 JSSM, PlayerLoad formula and IMA bands
30. https://pmc.ncbi.nlm.nih.gov/articles/PMC7183077/ — Heishman et al. 2020 Sports
31. https://pmc.ncbi.nlm.nih.gov/articles/PMC10127672/ — Towner et al. 2023, NCAA D-I women
32. https://lida.sport-iat.de/ta/Record/4062017?lng=en — Ransdell et al. 2020 abstract
33. https://lida.sport-iat.de/ta/Record/4071579?lng=en — Scanlan et al. 2021, individualised vs fixed PlayerLoad zones
34. https://www.jssm.org/jssm-15-585.xml-abst — Schelling & Torres 2016
35. https://opus.lib.uts.edu.au/handle/10453/147346 — D'Amelio 2020 PhD record
36. https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf — D'Amelio 2020 PhD full text (NBA optical vs radar; NBA load)
37. https://pmc.ncbi.nlm.nih.gov/articles/PMC12568105/ — markerless 3×3 Olympic study
38. https://pmc.ncbi.nlm.nih.gov/articles/PMC7601684/ — García-Rubio 2020, NBA Combine sprint times
39. https://www.topendsports.com/sport/basketball/testing-nba-draft.htm — NBA Combine test list
40. https://termedia.pl/Influence-of-ball-possession-and-playing-position-on-the-physical-demands-encountered-during-professional-basketball-games,78,41028,0,0.html — Ferioli et al. 2020 abstract (opened during research; not cited above)
41. https://arxiv.org/pdf/1806.10412 — Metulini 2017, basketball sensor data and dead-ball rule

Individualisation (non-basketball)
42. https://pmc.ncbi.nlm.nih.gov/articles/PMC11167479/ — Silva et al. 2024
43. https://researchers.westernsydney.edu.au/en/publications/peak-speed-determination-in-football-is-sprint-testing-necessary/ — Massard et al. 2018
44. https://www.research.ed.ac.uk/en/publications/to-measure-peak-velocity-in-soccer-let-players-sprint-peak-veloci/ — Kyprianou et al. 2022
45. https://lida.sport-iat.de/ta/Record/4043474?lng=en — Djaoui et al. 2017
46. https://pmc.ncbi.nlm.nih.gov/articles/PMC8064559/ — Fischer-Sonderegger et al. 2021
47. https://sponet.de/sponet/Record/4097014?lng=en — Marcelino & Silva 2026, peak-speed artefacts
48. https://www.catapult.com/blog/individualisation-gps-speed-thresholds-challenges-complexities — Catapult, individualisation cautions (vendor)

Vendors and leagues
49. https://www.catapult.com/blog/fundamentals-playerload-athlete-work — Catapult PlayerLoad (vendor)
50. https://www.catapult.com/blog/white-paper-introduction-ima — Catapult IMA (vendor)
51. https://locationbusinessnews.com/kinexon-tracks-ncaa-basketball-tournament-players — Kinexon NCAA tournament use (vendor news)
52. https://www.nba.com/stats/help/glossary — NBA tracking definitions
53. https://en.wikipedia.org/wiki/Player_tracking_(NBA) — NBA tracking history
54. https://www.washingtoninformer.com/20-percent-of-nba-players-run-equivalent-of-5-marathons-throughout-a-season/ — 2021–22 NBA distance and speed leaders
55. https://www.espn.com/nba/story/_/id/35818363/nba-use-hawk-eye-tracking-system-follow-players-ball — NBA Hawk-Eye from 2023–24
56. https://www.sportsvideo.org/?p=236963 — Hawk-Eye 12 cameras, 29 points
57. https://ministryofsport.com/exclusive-inside-the-nbas-player-tech-revolution/ — 14 cameras, 29 points
58. https://www.tvtechnology.com/news/cameras-record-big-data-for-the-nba — SportVU 6 cameras, 25 images/s
59. https://support.scisports.com/en/articles/4476826-physical-variables-glossary — SciSports thresholds and minimum durations
60. https://www.skillcorner.com/articles/skillcorner-releases-new-peak-velocity-metric — SkillCorner PSV-99 and Peak Velocity
61. https://skillcorner.com/articles/new-feature-explosive-accelerations — SkillCorner acceleration definition
62. https://skillcorner.com/articles/does-camera-position-and-capture-style-affect-tracking-quality — SkillCorner camera-position test
63. https://inside.fifa.com/technical/football-technology/standards/epts/epts-testing-process — FIFA EPTS testing

Tracking validity, filtering and dwell times
64. https://pmc.ncbi.nlm.nih.gov/articles/PMC6056042/ — Linke et al. 2018, SportVU / LPS / GPS vs Vicon
65. https://pmc.ncbi.nlm.nih.gov/articles/PMC7064167/ — Linke et al. 2020, TRACAB Gen4/Gen5 vs Vicon
66. https://pmc.ncbi.nlm.nih.gov/articles/PMC7923412/ — Blauberger et al. 2021, Kinexon vs Qualisys
67. https://www.termedia.pl/Validity-of-an-ultra-wideband-local-positioning-system-to-assess-specific-movements-in-handball,78,41138,0,0.html — Fleureau et al. 2020, Kinexon validity
68. https://www.frontiersin.org/journals/physiology/articles/10.3389/fphys.2018.00115/full — Luteberget et al. 2018, indoor UWB LPS
69. https://arxiv.org/pdf/2508.19477 — Crang et al. 2025, broadcast tracking validity (PDF)
70. https://arxiv.org/abs/2508.19477 — Crang et al. 2025, abstract page
71. https://arxiv.org/pdf/2001.07692 — Mortensen & Bornn 2020, off-screen load
72. https://arxiv.org/pdf/2110.11107 — Theiner et al. 2021, broadcast soccer positions
73. https://arxiv.org/pdf/2604.05636 — Bou et al. 2026, monocular broadcast speed and acceleration
74. https://arxiv.org/pdf/2209.07795 — KaliCalib, basketball court calibration
75. https://arxiv.org/pdf/1808.04550 — SciSports Kalman filtering of trajectories
76. https://pmc.ncbi.nlm.nih.gov/articles/PMC10761404/ — Robertson et al. 2023, EPTS validity considerations
77. https://pmc.ncbi.nlm.nih.gov/articles/PMC11244311/ — Ellens et al. 2024 Sensors, processing effects on counts
78. https://www.citedrive.com/en/discovery/accuracy-of-gnss-derived-acceleration-data-for-dynamic-team-sport-movements-a-comparative-study-of-smoothing-techniques/ — Ellens et al. 2024 Appl Sci abstract
79. https://hira.hope.ac.uk/1821/1/HIRA%20Submission.pdf — Varley et al. 2017 accepted manuscript
80. https://databallpy.readthedocs.io/en/latest/getting_started/preprocessing_options.html — databallpy Savitzky-Golay defaults
81. https://www.termedia.pl/Interchangeability-of-external-player-load-variables-from-different-athlete-tracking-systems-in-English-Premier-League-soccer-players,78,56509,0,0.html — Kavanagh 2026, Second Spectrum vs GPS
82. https://sponet.de/sponet/Record/4097236?lng=en — Giovanini & Moura 2026, single-camera basketball

Europe PMC REST API records (https://www.ebi.ac.uk/europepmc/webservices/rest/search, by DOI)
83. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1007/s40279-017-0794-z&resultType=core&format=json — Stojanović et al. 2018
84. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1007/s40279-020-01375-9&resultType=core&format=json — Russell et al. 2021
85. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1123/ijspp.2017-0534&resultType=core&format=json — Svilar et al. 2018 (opened; not cited above)
86. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1519/jsc.0000000000003001%20OR%20DOI:10.1519/jsc.0000000000003486&resultType=core&format=json — Scanlan 2021 and Fox 2021 records
87. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=AUTH:%22Fox%20JL%22%20AND%20basketball&resultType=lite&format=json&pageSize=40 — Fox JL basketball listing (Fox 2021 "Not all about the effort?" title)
88. Europe PMC, DOI 10.3390/s25061804 — González-Rodenas et al. 2025, TRACAB + Mediacoach vs IMU
89. Europe PMC, DOI 10.1177/00368504231187501 — Makar et al. 2023, TRACAB vs Catapult
90. Europe PMC, DOI 10.1080/02640414.2017.1411867 — Serpiello et al. 2018, ClearSky indoor validity
91. Europe PMC, DOI 10.5114/biolsport.2020.96850 — Fleureau et al. 2020
92. Europe PMC, DOI 10.3390/s20133693 — Hodder et al. 2020, ClearSky inter-unit reliability (opened; not cited above)
93. Europe PMC, DOI 10.1080/02640414.2022.2051332 — Delves et al. 2022, common 1 Hz filter
94. Europe PMC, DOI 10.1123/ijspp.2016-0534 — Varley et al. 2017
95. Europe PMC, DOI 10.1123/ijspp.2016-0236 — Malone et al. 2017 (opened; not cited above)
96. Europe PMC, DOI 10.1080/02640414.2011.627941 — Varley et al. 2012, 5 vs 10 Hz GPS (opened; not cited above)
97. Europe PMC, DOI 10.1371/journal.pone.0353385 — Andrey et al. 2026, game-derived acceleration-speed profiles
98. Europe PMC, DOI 10.1519/jsc.0000000000002875 — Abbott et al. 2018
99. Europe PMC, DOI 10.2478/hukin-2019-0113 — Rago et al. 2020
100. Europe PMC, DOI 10.1055/s-0034-1384547 — Hunter et al. 2015
101. Europe PMC, DOI 10.1123/ijspp.8.4.456 — Lovell & Abt 2013
102. Europe PMC, DOI 10.1080/02640414.2014.988740 — Clarke, Anson & Pyne 2015
103. Europe PMC, DOI 10.1038/s41598-022-12547-0 — Omidshafiei et al. 2022, Graph Imputer
104. Europe PMC, DOI 10.3389/fspor.2026.1873257 — Pimenta et al. 2026
105. Europe PMC, DOI 10.3389/fspor.2023.1116293 — Gualtieri et al. 2023
106. Europe PMC, DOI 10.3389/fphys.2026.1713000 — Feu et al. 2026, ACB within-game decline
107. Europe PMC, DOI 10.1186/s40798-022-00498-9 — Power et al. 2022, female basketball load review

Re-opened in the verification pass (fixer, 2026-10-18)
108. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7923412/fullTextXML — Blauberger et al. 2021, full text and Table 2 (speed RMSE 0.07 / 0.06 m/s, acceleration RMSE 0.20 / 0.18 m/s²) and Table 3 (peak accelerations)
109. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9391561/fullTextXML — Fox et al. 2022, Tables 8 and 10 (Ransdell jump count and PlayerLoad)
110. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11467009/fullTextXML — Tuttle et al. 2024, full text (zone counts, Ball and Reina thresholds, 22 of 26 Catapult)
111. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1055/s-0034-1384547&resultType=core&format=json — Hunter et al. 2015 abstract (12 players, 22 fixtures, 50 eligible match observations)
112. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11244311/fullTextXML — Ellens et al. 2024 Sensors (262 player files; 224 / 138 / 3 high-zone efforts; 1,380 vs 7.5 m)
113. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6720027/fullTextXML — Vázquez-Guerrero et al. 2019 (peak speed 18.75–19.64 km/h)
114. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7058381/fullTextXML — Petway et al. 2020 (Caparrós 2017 reference; one-sided > 3.5 / > 3 m/s² bands)
115. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC7183077/fullTextXML — Heishman et al. 2020 Sports (ShotTracker described as IPS)
116. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC10761404/fullTextXML — Robertson et al. 2023 (1 Hz filter RMSD 0.03 → 0.08 m/s)
117. Re-opened: https://arxiv.org/pdf/2508.19477 (Crang; detection by feed, distance by provider and feed), https://arxiv.org/pdf/2604.05636 (Bou; 20-value moving average, ground-truth caveat, Table 3), https://arxiv.org/pdf/2209.07795 (KaliCalib Section 4.4 and Table 1), https://opus.lib.uts.edu.au/bitstream/10453/147346/2/02whole.pdf (D'Amelio Tables 3.1 and 4.3), https://pmc.ncbi.nlm.nih.gov/articles/PMC7196749/ (García Table 1 headers), https://pmc.ncbi.nlm.nih.gov/articles/PMC12526517/ (Ruiz-Álvarez 24.1 km/h wording), https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2022.795897/full (Stone observation counts and "proprietary software" wording), https://www.frontiersin.org/journals/sports-and-active-living/articles/10.3389/fspor.2021.670018/full (Olthof observations), https://www.jssm.org/jssm-19-204.xml-Fulltext (Heishman W1/W2), https://www.washingtoninformer.com/20-percent-of-nba-players-run-equivalent-of-5-marathons-throughout-a-season/ (season inconsistency)


---

## Additions 2026-10-18

Gap-filling pass (2026-10-18). Nothing above is changed; this section adds material on seven gaps a review raised. Same conventions as the rest of the document: SI units (cm for jump heights), every claim carries the URL of a page opened in this pass, **unverified** marks claims seen only in snippets or secondary citations, **[derivation]** marks values worked out here. Sources for this section are listed at its end as A1–A40 so they do not collide with the numbered list above.

### A. Deceleration as its own construct

**Why it matters.** Sections 9.4 and 10 treat every acceleration band as a mirror-image deceleration band (±2.0, ±3.0 m/s²) and give no deceleration-specific source. The evidence below says decelerations differ from accelerations in how often they happen, how large they get, how they load the body, and how well tracking systems measure them.

**Frequency: decelerations outnumber accelerations at high intensity in most team sports.**
- Harper, Carling & Kiely 2019 (Sports Med, systematic review and meta-analysis; 19 studies, 469 male players; GPS > 5 Hz; high intensity > 2.5 m/s², very high > 3.5 m/s², the same edge used for both directions): every sport except American football had more high- and very-high-intensity decelerations than accelerations. Soccer showed the largest gap (standardised mean difference, SMD −1.74, 95% CI −1.28 to −2.21, high; SMD −3.19, −2.05 to −4.33, very high); Australian football SMD −1.15. American football was the exception (SMD +1.26 high; +0.19, not significant, very high). In one rugby sevens study, about 1.8 decelerations vs 0.4 accelerations per minute [https://knowledge.lancashire.ac.uk/id/eprint/29984/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC6851047/]. Basketball was not among the sports pooled.
- The authors' recommendations: set **separate, mutually exclusive thresholds for decelerations**, individualise them on each player's maximal deceleration capacity, record starting speed and the actions before and after, and standardise and report the minimum effort duration (MED) and end-of-effort rules. A short MED can split one effort into several, and no included study reported end-of-effort criteria, so published counts may be inflated [https://pmc.ncbi.nlm.nih.gov/articles/PMC6851047/].
- Rationale given for monitoring decelerations separately: they "comprise the highest magnitude of mechanical load per metre"; repeated high-force braking is linked to eccentric muscle damage, lower countermovement-jump output, hamstring strength asymmetry and injury risk, with effects lasting up to 64 h after a match [https://pmc.ncbi.nlm.nih.gov/articles/PMC6851047/]. Harper et al. 2026 (Sports Med review on assessing deceleration) adds that decelerations need large negative work from eccentric contractions and are among the highest mechanical forces in competition. They cite reports that 32–66% of non-contact ACL injuries in soccer happen during defensive pressing, when the player decelerates before changing direction [https://pmc.ncbi.nlm.nih.gov/articles/PMC12913331/].

**Basketball-specific evidence.**
- Vázquez-Guerrero, Suarez-Arrones, Casamichana & Rodas 2018 (Kinesiology 50(2):228; 12 elite men, 2 official matches, accelerometer-based load model): in every position, **peak decelerations were larger than peak accelerations (ES 2.70–6.87)**, but **moderate accelerations outnumbered moderate decelerations (ES 0.54–3.12)**. The acceleration-to-deceleration ratio above 3 m/s² was lower for guards (PG, SG) than for PF and C (ES 1.03–2.21). Abstract only; the full-text PDF returned an error, so zone edges and raw counts are **unverified** [https://hrcak.srce.hr/en/206142]. The ratio's direction (which side outnumbers above 3 m/s²) is not stated in the abstract.
- Petway et al. 2020 review (already cited in Section 2): elite match ranges of 1–15 high-intensity accelerations and 4–40 high-intensity decelerations; the high-intensity bands it reports are one-sided (Svilar > 3.5 / < −3.5 m/s²; Vázquez-Guerrero 2018 > 3 / < −3 m/s²) [https://pmc.ncbi.nlm.nih.gov/articles/PMC7058381/].
- Svilar et al. 2018 (IJSPP; 13 professional players, 300 training-session records): RPE and session RPE correlated highly with total accelerations, decelerations and changes of direction in every position; the high-intensity deceleration count loaded on a principal component for forwards only. Training data, abstract only [https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1123/ijspp.2017-0534&resultType=core&format=json].
- Deceleration capacity is larger in magnitude than the band edges. Harper et al. 2026 tabulate maximal decelerations of −7.58 to −8.40 m/s² over 20 m radar tests in team-sport athletes. NCAA Power 4 men in a 5-0-5 test reached about −7.68 ± 0.75 m/s² (bigs) and −8.13 ± 0.61 m/s² (guards); the review's table alignment for these rows is ambiguous. Professional basketball players averaged −4.45 ± 0.77 m/s² over a 10 m assessment (high-performing group). The review warns that peak deceleration is "highly influenced by sampling frequency and filtering approach" and that sampling below 25 Hz blurs rapid velocity changes and effort start and end [https://pmc.ncbi.nlm.nih.gov/articles/PMC12913331/]. In 124 NCAA Power 4 men, maximal deceleration correlated r = −0.42 with 5-0-5 time, and maximal acceleration in phase 1a r = −0.73 [https://knowledge.lancashire.ac.uk/id/eprint/56328/].
- Correction to the review request: the Lancashire (clok) record 56328 suggested for this gap is a change-of-direction test study (Petway, Harper, Cohen & Eriksrud 2026), not a match study showing that decelerations outnumber accelerations and track perceived exertion. No basketball match study making both claims was found. The RPE link rests on Svilar 2018 (training, totals).

**Measurement: optical systems treat decelerations differently.**
- TRACAB Gen5 + Mediacoach vs GPS-IMU (González-Rodenas et al. 2025; 46 LaLiga players, 662 match datasets, 95,371 accelerations and 100,952 decelerations on the IMU): optical under-counted decelerations (p < 0.001, d = 1.17) and "systematically underestimates both accelerations and decelerations". By band, R² was 0.944 (moderate dec, −2 to −4 m/s²) and **0.838 for high decelerations (< −4 m/s²)**, against **0.338 for high accelerations (> 4 m/s²)**. The abstract gives no percentage deficit, so the expected size of the under-count in counts cannot be stated [https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.3390/s25061804&resultType=core&format=json]. So the "> 4 m/s² not reported" row in Section 9.4 is justified by the acceleration side only. For this multi-camera system, high-deceleration agreement was much better, though counts were still low.
- Single-athlete basketball markerless tracking (8 cameras, 60 fps) reported its largest errors in lateral shuffles and decelerations, which the authors attribute to motion blur and abrupt changes of posture [https://pmc.ncbi.nlm.nih.gov/articles/PMC12252153/].

**Implications for MSU Alpha 3 [inference from the sources above].**
1. **Keep the symmetric ±2.0 / ±3.0 m/s² edges as comparability views.** Almost all published work, including Harper's pooled studies, uses the same edge in both directions, so symmetric edges are needed to compare with the literature. Do not present them as physiologically equivalent.
2. **Gate acceleration and deceleration bands separately.** In Section 10, step 5b, judge the acceleration bands on starts and the deceleration bands on hard stops and on the braking phase of cuts. One direction may pass while the other fails.
3. **Expect our smoothing to blunt decelerations more than accelerations.** Basketball stops are larger in magnitude (peaks of −7 to −8 m/s² vs band edges of −2 to −3) and, from the stop mechanics above, likely shorter. A full window W ≥ 1.0 s (Section 7.3) therefore attenuates deceleration peaks more than acceleration peaks, so broadcast deceleration counts should be biased low by more than acceleration counts [inference; to be measured in step 5b].
4. **Ratio diagnostic.** Compute the per-player-game ratio of high-intensity decelerations to high-intensity accelerations (≤ −3 vs ≥ +3 m/s²). If it falls well below the literature pattern (decelerations ≥ accelerations at high intensity in most sports), suspect filter attenuation before reading it as a real pattern. Basketball direction evidence is thin (Vázquez-Guerrero abstract), so this is a diagnostic, not a gate.
5. **Exploratory individualised deceleration view.** Express deceleration bands as fractions of each player's hand-labelled maximal deceleration from step 5b, as Harper 2019 recommends. Only once enough hard stops per player are labelled; until then, not reported.
6. **Under-count size.** No source gives a percentage under-count for optical decelerations. Multi-camera soccer shows a large effect (d = 1.17), and broadcast is expected to be worse. Our own value comes only from step 5b.

### B. Validation analogues for video and sensor jump measures

Section 5 says that no broadcast-pose jump validation exists. That is still true, but close analogues set realistic error budgets.

| Study | Setup | Reference | Result | Relevance | Source |
|---|---|---|---|---|---|
| Aderinola et al. 2023 (IEEE OJEMB; arXiv 2302.10749) | One smartphone, **720p, 30 fps**, side view, OpenPose 2-D; height from **toe vertical displacement** after pixel-to-mm scaling from a calibrating jump (not flight time); n = 16, 96 countermovement jumps, 77 valid (19 unilateral jumps removed as pose failures) | AMTI force plates 1,000 Hz (height from flight time) and CODA optical capture | All jumps vs force plate: ICC 0.95, bias −1.57 to −1.83 cm, 95% LoA about −6.7 to +3.6 cm; bilateral ICC 0.93–0.95, LoA about −7.4 to +3.8 cm; unilateral ICC 0.84–0.88. Against optical capture, ICC 0.96–0.99 | Closest analogue to our frame rate. **About ±5 cm limits at 30 fps with the camera close, side-on, fixed and unoccluded.** Broadcast will be worse. Authors list video quality, viewpoint, keypoint noise and movement towards or away from the camera (which changes the pixel-to-metric scale) as the main error sources | https://arxiv.org/abs/2302.10749 ; https://arxiv.org/pdf/2302.10749 |
| Aleksic et al. 2024 (Life 14:1641) | One iPhone 13, **240 fps**, 1080p, sagittal, 2 m away; MMPose (RTMDet + RTMPose); n = 12, 5 CMJs each | AMTI force plates 1,000 Hz | **Flight-time height: ICC 0.985, mean difference 0.1 cm**. Centre-of-mass displacement height overestimated by 6.8 cm (ICC 0.787); ankle-corrected displacement 0.5 cm. The **r = 0.992 is for the velocity–time trace** (bias 0.005 m/s, LoA −0.253 to 0.263 m/s), not jump height | Flight time beats pixel displacement when frame rate is high. At 240 fps one frame is 0.0042 s; at 30 fps it is 0.033 s, 8× coarser | https://pmc.ncbi.nlm.nih.gov/articles/PMC11677309/ |
| Pino-Ortega et al. 2018 (PeerJ 6:e4709) | WIMU IMU, accelerometer 1,000 Hz, proprietary flight-time algorithm; 15 adolescent soccer players, CMJ and squat jump | Force platform 1,000 Hz | Flight time: ICC 0.97 (CMJ) / 0.96 (SJ); CV 3.1% / 2.5%; SEM 0.0097 s / 0.0056 s; bias 0.0013 s / 0.0006 s. No numerical LoA; no height statistics | A lab IMU's flight time agrees with a force plate to about 0.01 s. That is the sensor side of any video-vs-sensor comparison | https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5933316/fullTextXML |
| Gageler, Wearing & James 2015 (IJPAS 15(1):284) | Inertial jump detector in volleyball training; 7 men, 5 women | 1,201 jumps hand-identified on video; force plate for flight time | **1,144 / 1,201 detected (95%), 57 false negatives (5%), 54 false positives (4%)**. Flight time −0.015 s mean, SD 0.058 s vs force plate | A field IMU jump count is itself wrong by about ±5% per event class, and its in-game flight time is much noisier than in the lab | https://lida.sport-iat.de/dvv/Record/4034386?lng=en |

**Converting these to height error at our thresholds [derivation; h = g·t²/8, dh/dt = g·t/4, g = 9.81 m/s²].**
- At the 0.40 m high-jump edge (t = 0.571 s), dh/dt = 1.40 m/s. Gageler's in-game flight-time SD of 0.058 s gives a height SD of about 0.08 m. The WIMU lab SEM of 0.0097 s gives about 0.014 m. One video frame at 30 fps (0.033 s) gives about 0.047 m, and at 240 fps (0.0042 s) about 0.006 m.
- So a field IMU's in-game height noise (≈ 0.08 m) is of the same order as our 30 fps frame quantisation with ±2 frames (≈ 0.09 m, Section 5). **Agreement between a video jump height and a wearable jump height should not be expected to be better than about ±0.1 m at 30 fps**, even if both were unbiased.

**What a sensor-reported jump count means, and how to compare it with video [inference].**
- A vendor count is a count of events above the vendor's airtime or impact threshold (Kinexon ≥ 0.30 s airtime as used by Stone 2022; WIMU "> 3 g" impacts; Section 5), with roughly 5% misses and 4% false events even in a validated IMU (Gageler). It is not a count of "real" jumps.
- **Compare event by event, not by totals.** Match each video jump to a sensor event within a ±0.2 s window around take-off [assumption, to be tuned]. Report true positives, misses and false events separately, and report counts at the **sensor's own threshold** (e.g. video airtime ≥ 0.30 s for Kinexon comparisons) as well as at our ≥ 0.20 m / > 0.40 m bands.
- Totals can agree by chance while misses and false events cancel; Gageler's 57 misses and 54 false events nearly cancelled in the total (1,144 + 54 = 1,198 detected vs 1,201 true) [derivation].
- **Validation design for our pipeline:** hand-label take-off and landing frames (the Gageler protocol) on broadcast footage. Report detection rate, false-event rate and flight-time bias and SD against those labels. Use the Aderinola and Aleksic results as the best case (fixed side-on camera) and Gageler as the sensor comparator.

### C. NCAA video time-motion analysis studies

Video time-motion analysis (TMA) is the method closest to ours, and the NCAA rows above contain only wearable data.

| Study | Population | Method | Findings | Source |
|---|---|---|---|---|
| Huynh, Guadagnino, Zendler & Agresta 2024 (Front Sports Act Living 6:1324650) | 11 NCAA D-I players (6 men, 5 women; 4 guards, 4 centres, 3 forwards), 4 practices (2 men's, 2 women's; about 189 min men, 227 min women in total) | Two cameras, 30 Hz; frame-by-frame coding by three raters in a modified McInnes scheme: stand/walk, jog, run, stride/sprint, low-, medium- and high-intensity shuffle, jump, plus "transitions" (pivots, cuts, quick side shuffles of no more than two steps). Proposed a faster **foot-loading** scheme: below bodyweight, bodyweight, above bodyweight (share of practice time) | Definitions are qualitative (trunk lean, knee drive, urgency, target), **with no speed thresholds**. Medium-intensity shuffle: speed "does not exceed jogging speed"; high-intensity shuffle: "rapid foot movement while usually in squat position". **Inter-rater ICC > 0.70 for all categories except run (0.63) and high-intensity shuffle (0.43).** Women had less stand/walk, run, stride/sprint, medium- and high-intensity shuffle and transitions than men, and more jog. Centres jogged less than forwards (p = 0.002). Per-minute counts are only in the supplement (not opened). Practice only, small sample | https://pmc.ncbi.nlm.nih.gov/articles/PMC11472002/ |
| Narazaki, Berg, Stergiou & Chen 2009 (Scand J Med Sci Sports 19(3):425) | 12 players aged 20.4 ± 1.1 y, women and men (split and competitive level not stated in the abstract) | 20-min practice game with referees and coaches; portable VO2; lactate in breaks; video TMA | **34.1% of play time running and jumping, 56.8% walking, 9.0% standing.** VO2 33.4 ± 4.0 (women) and 36.9 ± 2.6 mL·kg⁻¹·min⁻¹ (men); lactate 3.2 ± 0.9 and 4.2 ± 1.3 mmol/L. VO2max correlated with VO2 in play (r = 0.673) and with the share of time running and jumping (r = 0.935 women, 0.962 men) | https://digitalcommons.unomaha.edu/biomechanicsarticles/131 |
| Ben Abdelkrim et al. 2007 (Br J Sports Med; already cited for jumps) | 18 elite U19 Tunisian men (6 per position), 6 play-off games | McInnes-type TMA with nine categories; "specific movement" means "principally" shuffling | See Section D: shuffling ("specific movement") is about 41% of live time | https://pmc.ncbi.nlm.nih.gov/articles/PMC2658931/ |

**Use for MSU Alpha 3 [inference].**
- **Hand-labelled validation set.** Use the Huynh/McInnes category definitions, plus a direction tag, as the label scheme for a hand-coded subset of our footage. Then check that our numeric speed bands and direction classes (Section 9.5) map onto the coded categories, i.e. run a confusion matrix of numeric band vs coded category.
- **Label reliability is part of the error budget.** Run and high-intensity shuffle did not reach ICC 0.70 between trained raters. If our labels use them, report our own inter-rater agreement, or merge run with stride/sprint and medium with high-intensity shuffle for validation.
- **Rough cross-check of time shares [comparison, not a test].** Narazaki's walking + standing share (65.8% of play time) is below the "about 75% of time below 2.0 m/s" mapped in Section 6. The populations, the denominators (play time vs on-court time) and the classification (visual vs speed) all differ, so this only shows the order of magnitude.
- **NCAA rows for Sections 3 and 6 (additions, not edits):** Huynh 2024 (D-I practice, video TMA, qualitative categories, no speed edges); Narazaki 2009 (college-age, practice game, time-motion shares linked to measured VO2).

### D. Lateral shuffling and backward movement: intensity and energy cost

**How common it is in basketball.**
- Ben Abdelkrim et al. 2007 (elite U19 men, TMA): specific movements (mainly shuffling) took about 41% of live time (high 8.8%, medium 17.7%, low 14.2%). Per game: 94 ± 16 high-, 197 ± 33 medium- and 175 ± 10 low-intensity specific movements, against 55 ± 11 sprints. A high-intensity specific movement lasted 2.0 s on average. Guards had more medium-intensity specific movement than forwards and centres (19.8% of live time) [https://pmc.ncbi.nlm.nih.gov/articles/PMC2658931/].
- The coding schemes split shuffling into low, medium and high intensity by visual criteria, not speed [https://pmc.ncbi.nlm.nih.gov/articles/PMC11472002/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC2658931/]. The only numeric shuffle bands found remain Fox 2022's ≤ 2 / > 2 m/s (Section 2).

**Energy cost at matched speed (laboratory).**

| Study | n | Speed (m/s) | Backward vs forward | Lateral vs forward | Source |
|---|---|---|---|---|---|
| Williford et al. 1998 (MSSE 30(9):1419) | 13 athletes | 1.34 (80.45 m/min) | VO2 +28%, HR +17% | VO2 +78%, HR +24% (lateral > backward > forward, all significant) | https://lida.sport-iat.de/twm/Record/4001721 |
| same | same | 2.23 (134.08 m/min) | VO2 +15%, HR +15% | VO2 +20%, HR +16% (lateral ≈ backward, both > forward) | same |
| Gao et al. 2021 (Front Physiol 12:780699), 5 m shuttles, 5 min | 24 male college soccer players | 1.67 (6 km/h) | Forward-backward shuttle: VO2 +12.5%, lactate +54%, RPE +10% | Lateral shuttle: VO2 +25.9%, HR +16.6%, peak lactate +173% (1.73 → 4.73 mmol/L), RPE +28%; ES 0.86–2.83 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8892136/ |
| Rasica, Porcelli, Minetti & Pavei 2020 (Eur J Appl Physiol 120:2507) | 8 male runners | backward 0.97–1.67; forward 1.39–2.78 on 0 to +25% gradients | Energy cost **+35 ± 7%** on average across gradients; "almost inelastic rebound" (little elastic energy return) | – | https://pmc.ncbi.nlm.nih.gov/articles/PMC7557486/ |
| Masumoto & Mercer 2023 (Hum Mov Sci 88:103065), no body-weight support | not in abstract | matched (value not in abstract) | Cost of transport 5.8 ± 1.4 vs 4.4 ± 1.1 J·kg⁻¹·m⁻¹ (**+32%** [derivation]) | – | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=(%22backward%20running%22%20OR%20%22lateral%20shuffle%22%20OR%20%22side%20shuffle%22%20OR%20%22lateral%20movement%22)%20AND%20(%22energy%20cost%22%20OR%20%22oxygen%20uptake%22%20OR%20%22metabolic%20cost%22)&resultType=core&format=json&pageSize=20 |

**What this means [inference].**
- At the same speed, backward movement costs roughly 15–35% more than forward running and lateral shuffling roughly 20–80% more. The extra cost is largest at slow speeds (≤ 1.7 m/s), where most shuffling happens. No study tested shuffling above about 2.2 m/s.
- Speed-only bands therefore **under-state defensive load**. Most shuffling falls in our walk (< 2.0 m/s) or low jog band and is counted as recovery-level distance. This matters for the transition and getting-back requirements (stopping the ball, cross-matches), which are largely backward and lateral movement.
- Video also measures shuffling worst. Distance bias reached 4.61% in lateral shuffles in the multi-camera basketball study [https://pmc.ncbi.nlm.nih.gov/articles/PMC12252153/], and the direction class depends on body orientation from pose (Section 9.5).

**Recommendation.**
- Keep speed bands direction-free (the primary view, for comparability).
- Store time and distance per direction class × speed band, which Section 9.5 already proposes.
- Add an **exploratory cost-weighted distance view** that weights backward distance by 1.15–1.35 and lateral distance by 1.2–1.8 at speeds ≤ 2.2 m/s [derivation: rounded from the table above], published as a range (low and high weights), never as a single number. Do not extrapolate the weights above 2.2 m/s; label the view "lab-derived weights, not validated in basketball".
- Do not fold it into the primary bands or into any load index until the direction classifier passes its own hand-labelled check (Section 10, step 5b; Huynh-style labels, Section C).

### E. Metabolic power and equivalent distance (di Prampero–Osgnach framework)

**What it is.** Osgnach, Poser, Bernardini, Rinaldo & di Prampero 2010 (MSSE 42(1):170) treat accelerated running on flat ground as running uphill at constant speed, with an "equivalent slope" set by the acceleration. Instantaneous energy cost is then estimated from the known cost of uphill running, and metabolic power is cost × speed. In 399 Serie A players: 10,950 ± 1,044 m per match, 61.12 ± 6.57 kJ/kg; "high power" (> 20 W/kg) covered about 26% of distance and about 42% of energy [https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1249/MSS.0b013e3181ae5cfd&resultType=core&format=json]. "Equivalent distance" is the distance at constant speed on flat ground that would cost the same energy.
- **In use:** handball, EURO 2020, 414 players, 65 matches, 1,853 datasets, LPS: centre backs 7.85 W/kg (95% CI 7.67–8.03); intensity fell 2.5% per 10 min played (given in the abstract as 0.2 kJ/kg/s; units as printed); other positions not given numerically in the abstract [https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=AUTH:%22Venzke%20J%22&resultType=core&format=json&pageSize=15]. The repository page suggested for it (rua.ua.es handle 10045/136468) returned no content.
- **Basketball:** a Europe PMC search ("metabolic power" AND basketball) found no basketball study reporting metabolic power in W/kg [https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22metabolic%20power%22%20AND%20basketball&resultType=core&format=json&pageSize=15].

**Validity against measured energy expenditure.**

| Study | n | Activity | Metabolic power vs measured | Source |
|---|---|---|---|---|
| Brown et al. 2016 (IJSPP) | 27 | Walking, jogging, running, field-sport circuits (90 min, GPS) | Circuits **−44%**; whole session −19%; walking +43%; jogging and running not significant | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22metabolic%20power%22%20AND%20(GPS%20OR%20%22global%20positioning%22)%20AND%20(underestimat*%20OR%20%22energy%20expenditure%22)%20AND%20PUB_YEAR:[2014%20TO%202019]&resultType=core&format=json&pageSize=15 |
| Oxendale et al. 2017 (J Sci Med Sport) | 12 | Linear vs multidirectional running | Multidirectional **−52%** (95% LoA 20–93%); linear −34% (12–59%); r > 0.89 | same |
| Brochhagen & Hoppe 2025 (Front Sports Act Living) | 12 | Shuttle runs, repeated accelerations, repeated sprints with 180° turns; 20 Hz GPS | vs 3-component model (measured VO2, lactate, phosphocreatine): shuttles −13.5 ± 11.8%; **repeated accelerations +352 ± 116%**; repeated sprints +75 ± 17%. The equivalent-slope model was developed for accelerations up to about 4.5 m/s² | https://pmc.ncbi.nlm.nih.gov/articles/PMC12043615/ |
| Barba, Padulo & Maffulli 2026 (Br Med Bull, narrative review) | – | – | "systematic underestimations of 29%-85% relative to indirect calorimetry"; a fixed energy cost of 4.6 J·kg⁻¹·m⁻¹ ignores about 20% individual variation | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22metabolic%20power%22%20AND%20(validity%20OR%20calorimetry%20OR%20%22oxygen%20uptake%22)%20AND%20(team%20OR%20soccer%20OR%20shuttle)&resultType=core&format=json&pageSize=15 |
| Venzke, Schäfer & Platen 2025 (PLoS One) | 339 treadmill tests | Constant-speed running, gas exchange | Energy cost of running: soccer 3.79, field hockey 3.95, handball 4.04 J·kg⁻¹·m⁻¹; sport- and VO2max-dependent | same |

**Verdict: do not compute metabolic power or equivalent distance from broadcast tracking.** Reasons:
1. **It depends on acceleration.** The equivalent slope is driven by instantaneous acceleration, so it inherits the acceleration noise in Section 7.3. With the equivalent slope roughly proportional to a/g [simplification; the exact form in Osgnach 2010 is not reproduced here and is **unverified** in this document], an acceleration noise SD of 1 m/s² is a slope noise of about 0.10 (a 10% gradient) on every sample [derivation].
2. **It is invalid where basketball lives.** Even with good GPS, validity is worst in multidirectional, change-of-direction and repeated-acceleration work: −44% to −52%, and +352% for repeated 5 m accelerations with 180° turns. The model assumes forward running, while Section D shows that backward and lateral movement cost 15–80% more at the same speed.
3. **It has never been validated in basketball.**
4. **The output looks precise but isn't.** A W/kg number looks like physiology but would be noise passed through a model with a documented bias of tens of percent.

This matches the "no PlayerLoad from video" verdict in Section 9.5. If a reviewer asks, the cost-weighted direction view (Section D) is the defensible, simpler alternative, and it too stays exploratory.

### F. Between-game reliability, typical error and smallest worthwhile change

**Why it matters.** Calibration steps 2–5b measure *measurement* error. They do not say how much a band metric varies *biologically and tactically* from game to game. Without that, we cannot tell whether a player's or a quarter's change in high-speed running (HSR) or acceleration counts is real.

**Basketball evidence: thin.**
- Reina, García-Rubio, Esteves & Ibáñez 2020 (IJPAS 20(6):917; 48 youth players, short tournament, WIMU PRO LPS; distance, high-speed distance, accelerations, decelerations, jumps, PlayerLoad): forwards were more variable than other positions and guards the most stable; variability rose through the game (Q1 → Q3 and Q3 → Q4); jumps per minute varied most with playing time. Abstract only; no CV values [https://lida.sport-iat.de/ta/Record/4067569].
- Europe PMC searches for basketball between-game, match-to-match or within-player variability, typical error or smallest worthwhile change found no basketball game study reporting between-game CV, typical error or SWC for external load [https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=basketball%20AND%20(%22between-game%22%20OR%20%22game-to-game%22%20OR%20%22match-to-match%22%20OR%20%22between-match%22)%20AND%20(variability%20OR%20%22coefficient%20of%20variation%22)&resultType=core&format=json&pageSize=20], [https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=basketball%20AND%20(%22smallest%20worthwhile%20change%22%20OR%20%22typical%20error%22%20OR%20%22within-player%20variability%22%20OR%20%22intra-individual%20variability%22)%20AND%20(load%20OR%20accelerometer%20OR%20tracking)&resultType=core&format=json&pageSize=20].
- A UWB LPS study in professional basketball cites a device test–retest CV of 0.23–0.78% and %TEM of 2 from earlier work. That is device reliability, not game-to-game variation, and it reports no SWC [https://pmc.ncbi.nlm.nih.gov/articles/PMC8329980/].
- The only basketball figure in this document remains NBA HSR/min CV of about 15–16% (Section 11, new-64).

**Analogues from soccer (mixed models, log scale).**

| Study | Sample | Between-match CV | Other | Source |
|---|---|---|---|---|
| Myhill et al. 2025 (PLoS One), women's WSL academy | 257 players, 171 matches, foot-mounted IMUs | Whole match: total distance 3%, HSR distance 16%, sprint distance 24%, acceleration distance (> 3 m/s²) 16%, deceleration distance (< −3 m/s²) 17%. Peak 1-min: acceleration 10%, deceleration 10%, HSR 17%, sprint 22%; 5-min: acceleration 5%, deceleration 6% | The per-minute whole-match CVs in its Table 2 (e.g. acceleration distance per min 2%) are much smaller than the totals; reported as published | https://pmc.ncbi.nlm.nih.gov/articles/PMC11819598/ |
| Lee et al. 2026 (Sports), youth men | 32 players, 12 matches (97 player-matches) | Peak intensities: total distance 4.7%, high-speed distance (> 4.0 m/s, 14.4 km/h) 10.3%, average acceleration 5.0%, PlayerLoad 4.4% | Within-player CV: high-speed distance 21.8%, total distance 6.7%. SWC set at **0.6 × between-player SD** for this sub-elite cohort (0.2 for elite). "Practical change" thresholds: high-speed distance 38.6%, average acceleration 13.1%, total distance 13.0% | https://pmc.ncbi.nlm.nih.gov/articles/PMC13611161/ |
| Barreira et al. 2026 (Biol Sport), women | 27 players, 344 observations, GPS | – | Minimum detectable change about ±14% for total distance, > 30% for HSR and high-intensity acceleration and deceleration distance | https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=(soccer%20OR%20football)%20AND%20(%22match-to-match%20variability%22%20OR%20%22between-match%20variability%22)%20AND%20(acceleration%20OR%20%22high-speed%22)&resultType=core&format=json&pageSize=15 |

**Framework (Hopkins).** SWC is 0.2 × the between-subject SD for fitness-type measures, or 0.3–0.5 × an athlete's competition-to-competition variation for performance. If the typical error is much smaller than the SWC, trust an observed change; if it is much larger, the measure is too noisy; if they are about equal, use probabilities and repeated measures [https://www.sportsci.org/resource/stats/relyappl.html], [https://www.sportsci.org/resource/stats/precision.html].

**Proposed calibration step 10b (addition to Section 10; provisional).**
1. After the first block of games with adequate coverage (Section 10, step 1), fit a log-scale mixed model per metric (distance per minute in each band, HSR, acceleration and deceleration counts per minute, peak 60 s windows) with random intercepts for player and game. Report between-game CV, within-player CV and between-player SD, by position group.
2. SWC = 0.2 × between-player SD (also report 0.6× for comparison with Lee 2026).
3. **Monitorability rule:** a metric is usable for individual game-to-game monitoring only if our *measurement* typical error (from steps 2–5b, in the same units) is ≤ SWC. Otherwise it is reported only as multi-game or season averages.
4. **Band-edge rule:** an edge is worth keeping as a primary band only if its metric passes the monitorability rule, or is needed for literature comparability (then labelled as a view).
5. **How many games a stable mean needs [derivation]:** the standard error of a player's mean over k games is about CV/√k. With an HSR between-game CV of 16% (Myhill) or about 15–16% (NBA), 10 games give an SE of about 5%. With a within-player CV of 22% (Lee), 10 games give about 7%. Single-game HSR changes below about 30% (Barreira's minimum detectable change) should not be interpreted.

### G. Basketball-specific broadcast and single-camera tracking benchmarks

**Finding: no basketball broadcast paper reporting player localisation error in court metres was found.** Section 7.1's broadcast position, speed and distance budgets come from soccer (Crang, Theiner, Bou). Basketball broadcast has tighter framing, more cuts and replays, and heavier occlusion, so those numbers may not transfer, and we cannot say in which direction. A targeted web search returned only student projects and calibration papers, not metric player-position validations (search results only; not opened, so not cited). Hu et al., "Robust camera calibration and player tracking in broadcast basketball video", reports homography RMSE 1.25 and corner error 14.1 in units the snippet does not state (**unverified**).

**Candidate basketball datasets and what each can and cannot give us.**

| Dataset | Content | Metric ground truth? | Use for us | Source |
|---|---|---|---|---|
| KaliCalib / DeepSport calibration challenge (already in Section 7.1) | Single basketball images with camera calibration | Court-registration reprojection error (126.61 cm test set; 76.5% of images < 1 m) | Court-registration benchmark only, not player position | https://arxiv.org/pdf/2209.07795 |
| DeepSportradar-v1 (Van Zandycke et al. 2022, MMSports) | Basketball images with camera parameters; four tasks: ball 3-D localisation, camera calibration, player instance segmentation, player re-identification. Keemotion images from 15 arenas and 37 LNB Pro A games (from a search snippet; **unverified**) | Camera parameters give court-registration truth. The ball task is scored in pixels (ball-diameter error), not metres. No metric player positions | Calibration and re-ID test images from fixed, broadcast-like arena cameras | https://arxiv.org/abs/2208.08190v1 ; https://github.com/DeepSportradar/ball-3d-localization-challenge/blob/main/README.md |
| SportsMOT (Cui et al. 2023) | 240 sequences (basketball, volleyball, football), 720p, 25 fps, overhead shots of professional games including NCAA (from MultiSports); basketball clips average 845.4 frames; image-space boxes and IDs | **None**: no court coordinates | Detection, identity and re-ID robustness on basketball footage close to broadcast | https://arxiv.org/abs/2304.05170 ; https://arxiv.org/html/2304.05170 |
| TrackID3x3 (Yamada et al. 2025, MMSports '25) | 3x3 basketball: indoor fixed camera, outdoor fixed camera and drone subsets; multi-player tracking, identification and pose | The page states field detection is excluded from the Track-ID task; no metric error reported on the abstract page. Dataset "will be available" (repository not checked) | Pose and ID under occlusion; not a broadcast-geometry test | https://arxiv.org/abs/2503.18282 |

**Basketball-specific multi-camera markerless validations (not broadcast, but the only basketball metric numbers found).**
- Li et al. 2026 (Sensors 26:1689): six consumer cameras at 25 fps against a 10-camera Vicon over about 5.33 × 5.33 m; 3 men, 42 trials, 12 limb joints, 6 Hz Butterworth. Joint displacement RMSE 0.075–0.176 m; **velocity RMSE 0.67–1.29 m/s**; **acceleration RMSE 14.3–31.9 m/s²** (LoA about ±193 m/s²). The three-step layup was worst (velocity RMSE 4.42 m/s). The authors state that "a 25 Hz configuration is insufficient for high-precision impact analysis". These are limb-joint values, not a pelvis or floor point, so they overstate whole-body error, but they confirm that differentiated video kinematics are unusable without heavy smoothing [https://pmc.ncbi.nlm.nih.gov/articles/PMC12986566/].
- Zheng et al. 2025 (Sensors 25:4003): eight cameras at 60 fps, 10 collegiate athletes, single-player drills, tape-measure and TMA criteria (no motion capture). Hip-midpoint mean speed ICC 0.97–1.00 with LoA within ±0.42 m/s; distance bias up to 4.61% (lateral shuffle); larger errors in shuffles and decelerations; no occlusion or game play tested [https://pmc.ncbi.nlm.nih.gov/articles/PMC12252153/].

**Consequence [inference].** Section 7.1's soccer budgets stay as placeholders. No public basketball dataset provides metric player positions from a broadcast view, so our only metric ground truth is our own hand annotation on court-line geometry (Section 10, step 2). DeepSportradar (calibration) and SportsMOT (ID and detection) can serve as external test sets for the components, not for end-to-end metres.

### H. Proposed belief-register entries from this pass

ID numbering follows this document's continuation of the shared sequence (Section 11 used new-60 to new-65); the requirements session assigns final IDs, and JEV hypotheses keep their numbers.

| ID | Belief | Evidence for | Evidence against | Markets | How to test |
|---|---|---|---|---|---|
| new-66 | In MSU games, high-intensity decelerations (≤ −3 m/s²) per player-game outnumber high-intensity accelerations (≥ +3 m/s²) | Harper 2019 meta-analysis: decelerations > accelerations at high intensity in all pooled sports except American football [https://pmc.ncbi.nlm.nih.gov/articles/PMC6851047/]; basketball elite ranges 4–40 vs 1–15 per match [https://pmc.ncbi.nlm.nih.gov/articles/PMC7058381/]; peak decelerations > peak accelerations in all positions (ES 2.70–6.87) [https://hrcak.srce.hr/en/206142] | Moderate accelerations outnumber moderate decelerations in basketball (ES 0.54–3.12) [https://hrcak.srce.hr/en/206142]; optical tracking under-counts decelerations (d = 1.17) [https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.3390/s25061804&resultType=core&format=json]; smoothing likely blunts short stops more (Section A) | Not known | Video/tracking only, and only if the deceleration and acceleration bands each pass Section 10, step 5b. Play-by-play cannot test it |
| new-67 | Speed-only distance under-ranks defensive load: players with more backward and lateral movement have a larger gap between cost-weighted distance and speed-band distance, and the gap is larger in defensive and getting-back phases | Lab cost at matched speed: backward +15–35%, lateral +20–78% [https://lida.sport-iat.de/twm/Record/4001721], [https://pmc.ncbi.nlm.nih.gov/articles/PMC8892136/], [https://pmc.ncbi.nlm.nih.gov/articles/PMC7557486/]; shuffling about 41% of live time in elite U19 [https://pmc.ncbi.nlm.nih.gov/articles/PMC2658931/] | Weights come from steady treadmill or shuttle work at ≤ 2.2 m/s, not game play; the direction classifier is unvalidated; video errors are largest in shuffles [https://pmc.ncbi.nlm.nih.gov/articles/PMC12252153/] | Not known | Video/tracking with pose (direction class) plus possession phase from play-by-play; compare rankings under speed-only and cost-weighted views |

### I. Still missing after this pass

- Basketball between-game CV, typical error and SWC for any external-load metric: none found. Our own estimate (step 10b) is the only route.
- Optical under-count of decelerations as a percentage: not reported (González-Rodenas abstract gives only d = 1.17). Broadcast value unknown until step 5b.
- Full texts not opened: Vázquez-Guerrero 2018 (PDF returned HTTP 418; zone edges and counts **unverified**); Gageler 2015 (abstract record only); Narazaki 2009 (abstract; competitive level and sex split not stated); Huynh 2024 supplement (per-minute counts); Venzke 2023 handball (abstract; only centre-back W/kg); Osgnach 2010 (abstract; equivalent-slope formula not reproduced).
- Claims in the review request not confirmed in the opened sources: smartphone jump-height "MAE 1.47–2.82 cm" and "poor-to-moderate flight-time agreement" (Aderinola reports bias and LoA, not MAE, and estimates height from toe displacement, not flight time; 1.47 cm is a bias against optical capture); "MMPose r = 0.992" refers to the velocity–time trace, not jump height; the "Petway manuscript" showing more high-intensity decelerations that track RPE was not found (the suggested record is a change-of-direction test study).
- No basketball broadcast player-localisation benchmark in metres. Hu et al. calibration units **unverified**.
- No basketball metabolic-power study; no validity data for lateral or backward movement above about 2.2 m/s.
- Pages attempted but not usable in this pass: peerj.com/articles/4709 (403; used the Europe PMC full text instead), research-repository.griffith.edu.au (403), rua.ua.es handle 10045/136468 (empty), hrcak.srce.hr/file/303043 (HTTP 418).

### Sources for Additions 2026-10-18

All opened in this pass (2026-10-18) unless marked.
- A1. https://knowledge.lancashire.ac.uk/id/eprint/29984/ — Harper, Carling & Kiely 2019, repository record
- A2. https://pmc.ncbi.nlm.nih.gov/articles/PMC6851047/ — Harper et al. 2019, full text (first 100,000 characters read; the remainder was references)
- A3. https://knowledge.lancashire.ac.uk/id/eprint/56328/ — Petway, Harper, Cohen & Eriksrud 2026, change-of-direction test (redirected from clok.uclan.ac.uk/id/eprint/56328)
- A4. https://pmc.ncbi.nlm.nih.gov/articles/PMC12913331/ — Harper et al. 2026, assessing deceleration performance (first 100,000 characters read)
- A5. https://hrcak.srce.hr/en/206142 — Vázquez-Guerrero et al. 2018, abstract
- A6. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1123/ijspp.2017-0534&resultType=core&format=json — Svilar et al. 2018, abstract
- A7. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.3390/s25061804&resultType=core&format=json — González-Rodenas et al. 2025, abstract (re-opened)
- A8. https://pmc.ncbi.nlm.nih.gov/articles/PMC7058381/ — Petway et al. 2020 (cited above; not re-opened in this pass)
- A9. https://arxiv.org/abs/2302.10749 and https://arxiv.org/pdf/2302.10749 — Aderinola et al. 2023 (PDF text extracted locally; Table III and methods read)
- A10. https://pmc.ncbi.nlm.nih.gov/articles/PMC11677309/ — Aleksic et al. 2024
- A11. https://www.ebi.ac.uk/europepmc/webservices/rest/PMC5933316/fullTextXML — Pino-Ortega et al. 2018, WIMU full text
- A12. https://lida.sport-iat.de/dvv/Record/4034386?lng=en — Gageler, Wearing & James 2015, record and abstract
- A13. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=WIMU%20AND%20(jump%20OR%20%22flight%20time%22)%20AND%20(validity%20OR%20force%20plate)&resultType=core&format=json&pageSize=10 — WIMU and jump-validity search
- A14. https://pmc.ncbi.nlm.nih.gov/articles/PMC11472002/ — Huynh et al. 2024
- A15. https://digitalcommons.unomaha.edu/biomechanicsarticles/131 — Narazaki et al. 2009, record and abstract
- A16. https://pmc.ncbi.nlm.nih.gov/articles/PMC2658931/ — Ben Abdelkrim et al. 2007 (re-opened)
- A17. https://lida.sport-iat.de/twm/Record/4001721 — Williford et al. 1998
- A18. https://pmc.ncbi.nlm.nih.gov/articles/PMC8892136/ — Gao et al. 2021
- A19. https://pmc.ncbi.nlm.nih.gov/articles/PMC7557486/ — Rasica et al. 2020
- A20. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=(%22backward%20running%22%20OR%20%22lateral%20shuffle%22%20OR%20%22side%20shuffle%22%20OR%20%22lateral%20movement%22)%20AND%20(%22energy%20cost%22%20OR%20%22oxygen%20uptake%22%20OR%20%22metabolic%20cost%22)&resultType=core&format=json&pageSize=20 — Masumoto & Mercer 2023 and related abstracts
- A21. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1249/MSS.0b013e3181ae5cfd&resultType=core&format=json — Osgnach et al. 2010, abstract
- A22. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=AUTH:%22Venzke%20J%22&resultType=core&format=json&pageSize=15 — Venzke 2023 handball and 2025 energy-cost abstracts
- A23. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22metabolic%20power%22%20AND%20(validity%20OR%20calorimetry%20OR%20%22oxygen%20uptake%22)%20AND%20(team%20OR%20soccer%20OR%20shuttle)&resultType=core&format=json&pageSize=15 — Barba 2026, Brochhagen 2025 and Venzke 2025 abstracts
- A24. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22metabolic%20power%22%20AND%20(GPS%20OR%20%22global%20positioning%22)%20AND%20(underestimat*%20OR%20%22energy%20expenditure%22)%20AND%20PUB_YEAR:[2014%20TO%202019]&resultType=core&format=json&pageSize=15 — Brown 2016 and Oxendale 2017 abstracts
- A25. https://pmc.ncbi.nlm.nih.gov/articles/PMC12043615/ — Brochhagen & Hoppe 2025, full text (first 100,000 characters read)
- A26. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22metabolic%20power%22%20AND%20basketball&resultType=core&format=json&pageSize=15 — basketball metabolic-power search
- A27. https://lida.sport-iat.de/ta/Record/4067569 — Reina et al. 2020, youth basketball variability
- A28. https://pmc.ncbi.nlm.nih.gov/articles/PMC8329980/ — Ibáñez et al. 2021, UWB device reliability (cited from earlier work)
- A29. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=basketball%20AND%20(%22between-game%22%20OR%20%22game-to-game%22%20OR%20%22match-to-match%22%20OR%20%22between-match%22)%20AND%20(variability%20OR%20%22coefficient%20of%20variation%22)&resultType=core&format=json&pageSize=20 — basketball variability search
- A30. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=basketball%20AND%20(%22smallest%20worthwhile%20change%22%20OR%20%22typical%20error%22%20OR%20%22within-player%20variability%22%20OR%20%22intra-individual%20variability%22)%20AND%20(load%20OR%20accelerometer%20OR%20tracking)&resultType=core&format=json&pageSize=20 — basketball typical-error and SWC search
- A31. https://pmc.ncbi.nlm.nih.gov/articles/PMC11819598/ — Myhill et al. 2025
- A32. https://pmc.ncbi.nlm.nih.gov/articles/PMC13611161/ — Lee et al. 2026
- A33. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=(soccer%20OR%20football)%20AND%20(%22match-to-match%20variability%22%20OR%20%22between-match%20variability%22)%20AND%20(acceleration%20OR%20%22high-speed%22)&resultType=core&format=json&pageSize=15 — Barreira 2026 and other soccer variability abstracts
- A34. https://www.sportsci.org/resource/stats/relyappl.html and https://www.sportsci.org/resource/stats/precision.html — Hopkins, applications of reliability and precision
- A35. https://arxiv.org/abs/2503.18282 — TrackID3x3
- A36. https://arxiv.org/abs/2304.05170 and https://arxiv.org/html/2304.05170 — SportsMOT
- A37. https://arxiv.org/abs/2208.08190v1 and https://github.com/DeepSportradar/ball-3d-localization-challenge/blob/main/README.md — DeepSportradar-v1 and ball challenge
- A38. https://pmc.ncbi.nlm.nih.gov/articles/PMC12986566/ — Li et al. 2026, 25 Hz multi-camera basketball vs Vicon (first 100,000 characters read)
- A39. https://pmc.ncbi.nlm.nih.gov/articles/PMC12252153/ — Zheng et al. 2025, RTMPose 3x3 basketball
- A40. https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=basketball%20AND%20deceleration%20AND%20(acceleration%20OR%20tracking)&resultType=lite&format=json&pageSize=40 — basketball deceleration listing (used to locate A4, A38, A39)
