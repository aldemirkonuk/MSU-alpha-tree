# Open-Source Reusability Audit: MSU Basketball Broadcast CV and Possession Value

Prepared 2026-10-17. Companion to `research_review.md`.

**Scope.** This audit covers every entry in the literature review (73 numbered entries, about 84 individual works), plus the additional items requested: DeepHoops, Piotr Skalski / Roboflow basketball work, other open basketball CV pipelines and datasets, and labeling tools.

**How it was verified.**
- Repositories were confirmed to exist with `git ls-remote` and shallow clones.
- License files were read directly from each repo.
- Star counts and last-push dates come from the ecosyste.ms GitHub mirror, retrieved 2026-10-17. Star counts are approximate.
- Paper code links were found by scanning each arXiv HTML page for GitHub, Zenodo, Hugging Face (HF) and Google Drive links.
- Dataset licenses come from HF dataset cards, Roboflow Universe pages, Kaggle and DatasetNinja pages, and repo READMEs.
- "(unverified)" means a primary page could not confirm the detail.
- "No license file" means the repo has no LICENSE. Legally that defaults to all rights reserved: you may read it and learn from it, but you should not copy it into your own code without permission.

**Reusability scale.**
- **High:** usable now, with a compatible license, for this project's pipeline.
- **Medium:** usable with significant adaptation, or under license or data restrictions.
- **Low:** only the idea is reusable; there is no code or data, or it is proprietary.

**License flags used below.**
- **NC** = non-commercial only (CC BY-NC, CC BY-NC-SA, CC BY-NC-ND).
- **Copyleft** = GPL, AGPL or CeCILL. Linking or distributing triggers source-sharing obligations, and AGPL also covers network use.
- **Pat.** = the method is patented.
- **None** = no license file.

---

## 1. Summary table

Stage abbreviations:

| Abbreviation | Stage |
|---|---|
| ING | ingest |
| CAL | court calibration |
| DET | detection |
| TRK | tracking |
| TEAM | team assignment |
| JID | jersey ID |
| BALL | ball |
| OCR | scorebug OCR |
| SYNC | PBP sync |
| ACT | action recognition |
| MATCH | matchup inference |
| EPV | possession value |
| IMP | off-screen imputation |
| LINE | lineup/RAPM |
| WP | win probability |
| CTX | context |
| MKT | betting market |
| COORD | coordination |
| LAB | labeling |
| DATA | data access |

### 1a. Works from the literature review

| # | Work | Stage | Code (link) | Data (link) | License | Reuse |
|---|---|---|---|---|---|---|
| 1.1 | Cervone et al. 2016, Multiresolution EPV | EPV | Y: github.com/dcervone/EPVDemo (R, about 77★, last push 2015) | Y (sample): one full NBA game in the repo, shared with STATS consent | None (code); sample data under STATS consent | Medium |
| 1.2 | Sicilia et al. 2019, DeepHoops | EPV | N. The only repo, github.com/anthonysicilia/DeepHoopsRealtimeApplication, holds 2 demo videos | N: about 750 NBA games of 2016-17 SportVU, proprietary | n/a | Medium (method only) |
| 1.3 | Fernández, Bornn & Cervone 2021, deep EPV | EPV | N official. Community SoccerMap: github.com/ML-KULeuven/un-xPass (`unxpass/components/soccermap.py`, about 63★) | N (proprietary tracking) | un-xPass: Apache-2.0 (LICENSE.rst) | Medium |
| 1.4 | Decroos et al. 2019, VAEP | EPV | Y: github.com/ML-KULeuven/socceraction (Python, about 818★, Jan 2026) | Y: StatsBomb open-data (soccer events) | MIT (code); StatsBomb has its own terms (LICENSE.pdf) | High |
| 1.5 | Singh, Expected Threat (xT) | EPV | Community: `socceraction.xthreat` module | Public soccer event data | MIT | High |
| 1.6 | EAV (JSA 2025 / MIT thesis); GraphEIV (MLSA 2024) | EPV | N (unverified; none found) | N (NBA tracking) | n/a | Low |
| 2.1 | Franks et al. 2015, matchup HMM | MATCH | N official. Community: github.com/imadmali/bball-hmm (R/Stan, about 18★, 2019), also a Stan case study | Sample: one 2015-16 SportVU game (Dec 21, 2015, Timberwolves vs Celtics) in RDS | BSD-3 (code); case-study text CC BY-NC | High |
| 2.2 | Keshri et al. 2019, energy assignment + event HMM | MATCH/ACT | N (none found) | N | n/a | Low |
| 2.3 | Daly-Grafstein & Bornn 2019/2020, shot trajectories | EPV/MATCH | N (no links on arXiv pages) | N | n/a | Low |
| 2.4 | Song et al. 2026, factorized-attention coverage (NFL) | MATCH | N | N (NFL tracking; source unverified) | arXiv paper CC BY-NC-SA | Low |
| 3.1 | Sill 2010, RAPM | LINE | N official. Trivial with sklearn or glmnet ridge | Stints from hoopR PBP | n/a | High (method) |
| 3.2 | Maymin et al. 2013, Skills Plus-Minus | LINE | N | N | n/a | Medium (PBP-only method) |
| 3.3 | L-RAPM 2026; Hypergraph APM 2024; Devlin & Uminsky 2020 | LINE | N (no repo links on any arXiv page; unverified) | NBA PBP (public sources) | n/a | Medium |
| 3.4 | Fewell et al. 2012, passing networks | LINE | N | Partial: only supplementary figures and tables (lineups, flow centrality), no raw pass data | Article CC BY | Low |
| 3.5 | Bransen & Van Haaren 2020, pair chemistry | LINE | N (Papers with Code lists one implementation; unverified) | N | n/a | Low |
| 4.1 | McQueen et al. 2014, on-ball screens | ACT | N official. Community: github.com/akashsebastian/Automatically-Detect-On-Ball-Screens (about 1★, 2019) | N (labels private) | None | Medium (simple geometry; rewrite) |
| 4.2 | McIntyre et al. 2016, ball-screen defense | ACT | N | N | n/a | Low |
| 4.3 | Wang & Zemel 2016, play classification RNN | ACT | N | N | n/a | Low |
| 4.4 | Miller & Bornn 2017, possession sketches | ACT | N (none found) | N | n/a | Low |
| 4.5 | Patton et al. 2021, college broadcast tracking (Stats Perform) | all | N (proprietary AutoSTATS) | N | Proprietary | Low (architecture blueprint only) |
| 4.6 | Synergy play types (Nylon Calculus) | ACT | N | Commercial | Paid | Low |
| 5.1 | NBA Gravity | EPV | N | N | Proprietary | Low |
| 5.2 | Lucey et al. 2014, open shot | ACT/EPV | N | N | n/a | Low |
| 5.3 | Kono & Fujii 2024, BMOS/BIMOS | EPV | Y: github.com/Run-summer/bimos_bmos_basketball (Python, about 6★, Nov 2025, marked work in progress) | Y: Google Drive `.mat` files derived from SportVU (links in the README) | None | Medium |
| 5.4 | Spearman 2018; Fernández & Bornn 2018, space control | EPV | N official. Community pitch control: github.com/Friends-of-Tracking-Data-FoTD/LaurieOnTracking (about 255★) | Metrica sample data (3 games, "acknowledge source" terms) | MIT (code) | Medium |
| 5.5 | Tsiakalos 2025; Metulini et al. 2018, spacing geometry | EPV | N (geometry is trivial with scipy). Same group's BasketballAnalyzeR on CRAN (GPL-2/3); hull functions unverified | Book sample data (unverified) | GPL | Medium |
| 6.1 | Lu et al. 2013, track and identify from broadcast with a PBP prior | TRK/JID | N | N (2010 NBA Finals footage) | n/a | Medium (idea is key; reimplement) |
| 6.2 | Sha et al. 2020, end-to-end broadcast calibration | CAL | N | N (college set not public) | Pat. (US11861806) | Low |
| 6.3 | Maglo et al. 2022, KaliCalib | CAL | Y: github.com/CEA-LIST/KaliCalib (Python, about 15★, 2022/23, ships trained `.pth` models) | Uses DeepSportRadar calibration set (728 images) | **CeCILL-2.1 (Copyleft)** | Medium |
| 6.4 | DeepSportRadar-v1 2022 | CAL/DET/BALL/re-ID | Y: github.com/DeepSportradar (instance-seg and re-ID: Apache-2.0; calibration and ball-3D challenge repos: none). Baseline lib github.com/gabriel-vanzandycke/deepsport | Y: kaggle.com/datasets/deepsportradar/basketball-instants-dataset (about 700+ to 1,456 images, LNB Pro A arenas) | Code mixed (deepsport is **CC BY-NC-ND**); data **CC BY-NC-SA 4.0** per DatasetNinja (unverified on Kaggle) | Medium |
| 6.5 | Cui et al. 2023, SportsMOT / MixSort | TRK | Y: github.com/MCG-NJU/SportsMOT (about 232★, 2023) | Y: HF `MCG-NJU/SportsMOT`, gated (240 clips including NCAA/NBA basketball) | Repo: none; data **CC BY-NC 4.0** | Medium (eval/pretrain, NC) |
| 6.6 | SoccerNet-Tracking 2022; SoccerNet GSR 2024; Challenges 2025 | TRK/CAL/JID | Y: github.com/SoccerNet/sn-gamestate (about 465★, May 2026), built on github.com/TrackingLaboratory/tracklab (MIT, about 251★); sn-tracking / sn-calibration (no license file) | Y: HF `SoccerNet/SN-GSR-2025` (ungated); tracking via the `SoccerNet` pip package | sn-gamestate **GPL-3.0**; SN-GSR HF tag GPL-3.0; TrackLab MIT; components PRTReid/BPBreID **Hippocratic 3.0**, PnLCalib **GPL-2.0** | High (architecture), Medium (license) |
| 6.7 | Scott et al. 2024, TeamTrack | TRK | Y: github.com/AtomScott/TeamTrack (MIT, about 15★, 2024); SportsLabKit (**GPL-3.0**, about 324★) | Y: Google Drive and kaggle.com/datasets/atomscott/teamtrack (basketball full-court, 4K to 8K) | Data license not stated (unverified) | Medium |
| 6.8 | Koshkina & Elder 2024, jersey number recognition | JID | Y: github.com/mkoshkina/jersey-number-pipeline (about 74★, Oct 2024; weights on Drive) | Y: weakly labeled crops on Drive; hockey set github.com/grant81/hockeyTrackingDataset (GPL-3.0) | **Creative Commons NC + share-alike style license (NC)** | High for research; NC blocks commercial use |
| 6.9 | Skalski 2025, Roboflow basketball AI | DET/TRK/TEAM/JID/CAL | Y: github.com/roboflow/notebooks (3 basketball notebooks) + github.com/roboflow/sports (branch `feat/basketball`) | Y: 3 Roboflow Universe datasets (details in §2) | sports: MIT; notebooks: none; datasets CC BY 4.0 | High |
| 6.10 | Yamada et al. 2025, TrackID3x3 | TRK/JID | Y: github.com/open-starlab/TrackID3x3 (about 30★, Dec 2025) | Y: Google Drive (60 videos, about 278k frames, 3x3) | Code Apache-2.0; data license not stated | Medium |
| 6.11 | Scorebug OCR (patents US11568644, US11792441) | OCR | N (patents only) | N | Pat. | Low (avoid copying claims) |
| 7.1 | Le et al. 2017, data-driven ghosting | IMP | N | N | **Pat. US12165395** | Low |
| 7.2 | Le et al. ICML 2017, coordinated imitation | IMP | Y (minimal): github.com/hoangminhle/MultiAgent-ImitationLearning (one script, about 23★, 2017) | N | None | Low |
| 7.3 | Zhan et al. 2019; NAOMI (Liu et al. 2019) | IMP | Y: github.com/ezhan94/multiagent-programmatic-supervision (MIT, about 60★); github.com/felixykliu/NAOMI (about 53★, 2019) | Basketball data via AWS Data Exchange (Stats Perform) | Zhan MIT; NAOMI none; data has vendor terms | Medium |
| 7.4 | Omidshafiei et al. 2022, Graph Imputer | IMP | N | N (authors say they cannot release the data; they point to Metrica and Last-Row) | n/a | Medium (method; reimplement) |
| 7.5 | Choi et al. 2025, MIDAS; Kim et al. 2023, ball inference | IMP/BALL | Y: github.com/gkswns95/midas (2025, data not uploaded); github.com/pientist/ballradar (2023) | Metrica sample data | Both none; papers CC BY-NC-ND | Medium |
| 7.6 | Choi 2026, training-free off-screen imputation | IMP | Y: github.com/nowayfootball/offscreen-impute (Python, Jul 2026, CPU-only) | Metrica, via download script | MIT | High (port to basketball) |
| 8.1 | KenPom ratings | WP | N | Subscription (via hoopR/cbbdata with login) | Paid | Medium |
| 8.2 | Torvik T-Rank | WP | N (site) | Y: free at barttorvik.com and through cbbdata | Site terms | High |
| 8.3 | Pomeroy in-game WP | WP | N | N | n/a | Medium (simple to rebuild) |
| 8.4 | Maddox et al. 2022, Bayesian college WP | WP | N (none found) | N (D-I seasons; rebuild from PBP) | n/a | Medium |
| 8.5 | Stern 1994; inpredictable | WP | N (closed form) | n/a | n/a | High (method) |
| 8.6 | Kubatko et al. 2007, possession accounting | SYNC/EPV | N (definitions) | n/a | n/a | High (method) |
| 9.1 | van Bommel et al. 2021, home court | CTX | N (none found) | N | n/a | Medium |
| 9.2 | Marshall et al. 2025, COVID crowd | CTX | N | N | n/a | Low |
| 9.3 | Pomeroy, market home court | CTX | N | N | n/a | Low |
| 9.4 | Anderson & Pierce 2009, officiating | CTX | N | N | n/a | Low |
| 9.5 | Leota et al. 2022; JCSM 2021, travel | CTX | N (unverified) | N | n/a | Low |
| 9.6 | Lopez et al. 2018, randomness | MKT | Y: github.com/bigfour/competitiveness (R/JAGS, about 16★, 2018) | Line data in repo (unverified) | CC0 | Medium |
| 10.1 | Wolfers 2006 | MKT | N | N | n/a | Low |
| 10.2 | Borghesi et al. 2010 | MKT | N | N | n/a | Low |
| 10.3 | Paul & Weinbach 2008/2009 | MKT | N | N | n/a | Low |
| 10.4 | Hickman 2020; Douglas 2014 | MKT | N | N | n/a | Low |
| 10.5 | Simon 2024 | MKT | N (unverified) | N | n/a | Low |
| 10.6 | Clegg & Cartlidge 2024 | MKT | Y: github.com/Faxulous/notFeelingTheBuzz (about 2★); original github.com/philiprami/betting_on_a_buzz (Stata) | Tennis odds in repo (unverified) | None | Low (method warning only) |
| 10.7 | Derivative-market gap; Wornow 2026 thesis | MKT | N | N | n/a | Low |
| 11.1 | McGarry et al. 2002 | COORD | N | N | n/a | Low |
| 11.2 | Bourbousson et al. 2010 | COORD | N (Hilbert relative phase is a few lines of scipy) | N | n/a | Medium (method) |
| 11.3 | Esteves et al. 2012/2015 | COORD | N | N | n/a | Low |
| 11.4 | Duarte et al.; Travassos et al. | COORD | N (reviews) | N | n/a | Low |
| 11.5 | Ichikawa et al. 2026 | COORD | N (none on arXiv page) | N | n/a | Low |
| 12.1 | hoopR | SYNC/DATA | Y: github.com/sportsdataverse/hoopR (R, about 150★, Oct 2026) | Y: github.com/sportsdataverse/hoopR-mbb-data | MIT (code); data repo CC BY 4.0 (ESPN-sourced) | High |
| 12.2 | cbbdata | DATA | Y: github.com/andreweatherman/cbbdata (R, about 17★, Oct 2024) | Y: API (free key) | MIT | High |
| 12.3 | CBBpy | SYNC/DATA | Y: github.com/dcstats/CBBpy (Python, about 29★, v2.1.2) | ESPN (scraped) | Apache-2.0 | High |
| 12.4 | ncaahoopR | DATA | Y: github.com/lbenz730/ncaahoopR (R, about 230★, Feb 2026) | ESPN (scraped) | MIT | Medium-High |
| 12.5 | ESPN public JSON endpoints | SYNC/JID | n/a | Y: undocumented API | ESPN terms of use | Medium |
| 12.6 | Injury / availability reports | CTX | n/a | Public reports (NCAA pilot, Big 12, ACC) | n/a | Medium |

**Counts (literature review, 73 entries).**
- **Author-released code:** 21 entries (about 24 individual works). These are 1.1, 1.4, 5.3, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 7.2, 7.3 (2 works), 7.5 (2 works), 7.6, 9.6, 10.6 and 12.1–12.4.
- **Community reimplementation only:** 6 more entries (1.3, 1.5, 2.1, 3.1, 4.1, 5.4).
- **Downloadable data, including samples:** 16 entries. These are 1.1, 1.4, 2.1 (community sample), 5.3, 6.4, 6.5, 6.6, 6.7, 6.8, 6.9, 6.10, 7.5, 7.6, 8.2, 12.1 and 12.2. ESPN feeds (12.3–12.5) are reachable but not a licensed dataset.
- **Code with a permissive OSI license (MIT/Apache/BSD/CC0):** 13 entries. The rest are unlicensed, NC or copyleft.
- None of the NBA EPV, matchup or play-type papers (Sections 1, 2 and 4) released their tracking data. All rely on proprietary SportVU or Second Spectrum.

### 1b. Additional items (Task B)

| Item | Stage | Code (link) | Data (link) | License | Reuse |
|---|---|---|---|---|---|
| DeepHoops (detail in §2) | EPV | N | N | n/a | Medium (reimplement) |
| roboflow/sports, branch `feat/basketball` (+ `feat/basketball_radar`) | CAL/TEAM/EPV | Y: github.com/roboflow/sports (Python, about 5.4k★; main last commit May 2025, basketball branch Nov 2025) | Universe datasets | MIT | High |
| Roboflow notebook: detect, track and identify basketball players | DET/TRK/TEAM/JID/CAL | Y: github.com/roboflow/notebooks/blob/main/notebooks/basketball-ai-how-to-detect-track-and-identify-basketball-players.ipynb | Sample videos: 2025 NBA Playoffs Celtics vs Knicks (Drive) | No license in notebooks repo | High |
| Roboflow notebook: 3-second violations | CAL/TRK/ACT | Y: `.../basketball-ai-automatic-detection-of-3-second-violations.ipynb` | Same | Same | Medium |
| Roboflow notebook: make or miss jump shots | ACT | Y: `.../basketball-ai-make-or-miss-jumpshot-detection.ipynb` | Same | Same | Medium |
| Roboflow Football AI notebook + `examples/soccer` | DET/TRK/TEAM/CAL | Y: `notebooks/football-ai.ipynb`; github.com/roboflow/sports/tree/main/examples/soccer | Universe soccer datasets (CC BY 4.0) | MIT (sports); YOLOv8 is **AGPL-3.0** | High (components transfer) |
| Universe: basketball-player-detection-3-ycjdo | DET/BALL/ACT | n/a | universe.roboflow.com/roboflow-jvuqo/basketball-player-detection-3-ycjdo (654 images, 10 classes) | CC BY 4.0 | High |
| Universe: basketball-court-detection-2 | CAL | n/a | universe.roboflow.com/roboflow-jvuqo/basketball-court-detection-2 (850 images, keypoints) | CC BY 4.0 | High |
| Universe: basketball-jersey-numbers-ocr | JID | n/a | universe.roboflow.com/roboflow-jvuqo/basketball-jersey-numbers-ocr (3,615 crops, NBA) | CC BY 4.0 | High |
| RF-DETR | DET/CAL | Y: github.com/roboflow/rf-detr (about 9.8k★, Oct 2026) | COCO / RF100-VL | Apache-2.0 for N/S/M/L; **PML 1.0 for A/F/P sizes** | High |
| roboflow/trackers | TRK | Y: github.com/roboflow/trackers (about 3.9k★, Oct 2026) | Benchmarked on SportsMOT | Apache-2.0 | High |
| supervision | all | Y: github.com/roboflow/supervision (about 51k★) | n/a | MIT | High |
| SAM2 / SAM2.1; real-time fork | TRK | Y: github.com/facebookresearch/sam2 (about 20k★); github.com/Gy920/segment-anything-2-real-time (about 267★) | n/a | Apache-2.0 (both; HF weights Apache-2.0) | High |
| SigLIP, SmolVLM2, ViTPose+ (HF weights) | TEAM/JID/pose | HF `google/siglip-base-patch16-224`, `HuggingFaceTB/SmolVLM2-*`, `usyd-community/vitpose-plus-large` | n/a | Apache-2.0 (all three, per HF tags) | High |
| abdullahtarek/basketball_analysis | DET/TRK/TEAM/CAL/ACT | Y: github.com/abdullahtarek/basketball_analysis (about 32★, May 2025; YOLO + FashionCLIP + homography + pass/interception) | Weights on Drive | **No license file** (README says "see LICENSE", but none exists); depends on ultralytics **AGPL-3.0** | Medium (read only; do not copy) |
| NBA SportVU 2015-16 mirrors | IMP/EPV/MATCH pretraining | github.com/linouk23/NBA-Player-Movements (about 726★; about 630 game `.7z` files); github.com/neilmj/BasketballData (about 201★, original); github.com/sealneaward/nba-movement-data (MIT code); HF loader `dcayton/nba_tracking_data_15_16` | Raw SportVU logs, Oct 2015 to Jan 2016 | Repos: none (data is NBA/STATS-originated, unclear rights); loader script Apache-2.0 | High for research, uncertain for commercial |
| neilmj NCAA SportVU 2014-15 CSV | CTX | Same repo | `NCAAM.Player.Tracking/NCAA_SportVU_2014-2015.csv` (about 1,660 player-game rows, 19 MSU rows; box-score-level tracking stats, not coordinates) | None | Low |
| DeepSportRadar repos + deepsport | CAL/BALL/re-ID | See 6.4 | See 6.4 | Mixed, **NC** | Medium |
| SportsMOT | TRK | See 6.5 | See 6.5 | **NC** | Medium |
| TeamTrack | TRK | See 6.7 | See 6.7 | MIT / unstated | Medium |
| BasketLiDAR (Hayashi et al. 2025, arXiv 2508.15299) | TRK | N | On request only: sites.google.com/keio.jp/keio-csg/projects/basket-lidar (4,445 frames, 3 LiDAR + 3 cameras) | Not stated | Low |
| SoccerNet sn-gamestate / TrackLab / CAMELTrack | TRK/JID/CAL | github.com/SoccerNet/sn-gamestate (GPL-3.0); TrackLab (MIT); github.com/TrackingLaboratory/CAMELTrack (Apache-2.0, about 136★) | SN-GSR | Mixed | High (TrackLab/CAMELTrack), Medium (sn-gamestate) |
| E-BARD (Giudici et al. 2026) | DET/TEAM/JID/ACT | Y: github.com/GabrieleGiudic/E-BARD (Mar 2026; Qwen2.5-VL pipeline) | Y: HF `GabrieleGiudici/E-BARD-detection` (1,800 frames, 22k boxes), `-JerseyNumberRecognition`, `-TeamAttribution`, `-ObjectClassification`; models YOLOv8n and RF-DETR-N | CC BY 4.0 (repo and HF datasets) | High |
| NSVA (Wu et al. ECCV 2022) | ACT | Y: github.com/jackwu502/NSVA (about 34★, 2023) | NBA.com clips (download scripts), captions, coarse/fine/event action labels, player ID | **CC BY-NC** (README) | Medium |
| MultiSports (ICCV 2021) | ACT | Y: github.com/MCG-NJU/MultiSports (MIT code) | HF `MCG-NJU/MultiSports`; basketball classes include pass, drive, dribble, screen, pick-and-roll defense, sag, rebounds and steals | Data **CC BY-NC 4.0** | Medium |
| FineSports (CVPR 2024) | ACT | Y: github.com/PKU-ICST-MIPL/FineSports_CVPR2024 (about 31★) | Signed release agreement by email (NBA, 52 fine-grained types, 123k boxes) | No license file; agreement-gated | Low-Medium |
| PL-NBA (arXiv 2608.19646) | ACT/SYNC | N | Not released (11k NBA possessions with event captions) | n/a | Low (watch) |
| Stan bball-hmm | MATCH | See 2.1 | See 2.1 | BSD-3 | High |
| PaddleOCR / PARSeq / EasyOCR / MMOCR | OCR/JID | github.com/PaddlePaddle/PaddleOCR (about 91k★); github.com/baudm/parseq; github.com/JaidedAI/EasyOCR; github.com/open-mmlab/mmocr | n/a | All Apache-2.0 | High |
| mmaction2 | ACT | github.com/open-mmlab/mmaction2 (about 5.2k★) | n/a | Apache-2.0 (VideoMAE and CoTracker weights are **CC BY-NC**) | High |
| BoxMOT; Ultralytics YOLO | TRK/DET | github.com/mikel-brostrom/boxmot; github.com/ultralytics/ultralytics | n/a | **AGPL-3.0** (both) | Medium (license) |
| PySceneDetect; TrackEval; UMAP; scikit-learn | ING/TRK/TEAM | Breakthrough/PySceneDetect; JonathonLuiten/TrackEval; lmcinnes/umap; scikit-learn | n/a | BSD-3 / MIT / BSD-3 / BSD-3 | High |
| CVAT | LAB | github.com/cvat-ai/cvat (about 16.9k★, Oct 2026) | n/a | MIT (self-hosted Community) | High |
| Label Studio + ML backend | LAB | github.com/HumanSignal/label-studio (about 28k★); github.com/HumanSignal/label-studio-ml-backend (about 1.1k★) | n/a | Apache-2.0 (Community) | High |
| FiftyOne + Brain + plugins | LAB/QA | github.com/voxel51/fiftyone (about 11k★); voxel51/fiftyone-brain; voxel51/fiftyone-plugins | n/a | Apache-2.0 (all three repos) | High |
| Roboflow Annotate | LAB | SaaS (not open source) | Projects are private by default on Core/free; Universe publishing optional | Proprietary; free tier gives 10 credits/month | Medium |

---

## 2. Per-item notes

### 2.1 Expected possession value

**Cervone EPV (1.1).**
- `EPVDemo` is the only official basketball EPV code anywhere.
- It contains R code (needs INLA) and a one-game STATS sample. The full model needs hundreds of games.
- Use it as a reference implementation of the macro-state, semi-Markov idea, not as a library.
- It has no license, so read it and rewrite rather than vendoring it.

**DeepHoops (1.2; Task B item 1).**
- *Method.*
  - A stacked LSTM over a sliding window of all 10 players' and the ball's court coordinates, plus a learned player embedding for the 10 players on court.
  - At every moment it outputs a probability for each terminal-action class: field goal attempt, shooting foul, non-shooting foul, turnover, or "null" (possession continues).
  - The window is T=128 moments (about 5.1 s at 25 Hz), ending with a "blind spot" of r=16 moments (about 0.64 s). The blind spot hides late frames that trivially reveal the outcome, such as ball height during a shot.
  - Each class carries a value relative to the league baseline (about 1.02 points per possession). Expected points are the probability-weighted sum. For example, a field goal attempt is worth about +0.23 and a turnover about −1.02.
  - "Null" windows outnumber terminal windows about 600:1. The authors downsample null windows with a tunable rate and show the resulting probabilities are still calibrated.
  - Micro-action value is the change in expected points across an action. Their example: a screen plus a pass to an open corner three raises expected points from 1.08 to 1.27.
- *Data.* About 750 NBA games of 2016-17 optical tracking, which is proprietary.
- *Code.* None. The authors' repo `anthonysicilia/DeepHoopsRealtimeApplication` holds two demo `.mov` files and a README.
- *What it teaches this project:*
  1. Terminal-action labels come free from hoopR PBP (shot, foul type, turnover). Only the input windows need video.
  2. The sliding window with a blind spot is the right way to avoid label leakage when windows are built around PBP timestamps.
  3. Explicit class rebalancing and calibration checks are mandatory.
  4. The player-embedding trick handles personnel but needs many games per player. With about 35 MSU games, replace the embedding with role or position features, or pretrain on public 2015-16 SportVU (about 630 games).
  5. Inputs must be masked when players are off-screen. Train with simulated broadcast occlusion, borrowing the Graph Imputer idea.
- *Reusability.* Medium. It is reimplementable in about 300 lines of PyTorch, and the public 2015-16 SportVU season (one season earlier than the paper's) is a usable pretraining stand-in.

**Deep EPV / SoccerMap (1.3).**
- The paper has no code.
- KU Leuven's `un-xPass` contains a clean PyTorch SoccerMap component (pass selection, success and value surfaces) under Apache-2.0.
- Change the pitch grid to a 94×50 ft court, or a half court.

**VAEP and xT (1.4, 1.5).**
- `socceraction` (MIT) implements SPADL, VAEP, Atomic-VAEP and xT.
- The value-iteration and gradient-boosting code is sport-agnostic once basketball PBP is mapped to a SPADL-like action table.
- This is the highest-leverage reusable possession-value code for a PBP-first phase.

**Decision-quality EPV (1.6).** No code or data found for EAV or GraphEIV (unverified).

### 2.2 Matchups

**Franks et al. (2.1).**
- No author code.
- `imadmali/bball-hmm` (BSD-3) is a Stan reimplementation of the defensive-assignment HMM. It uses the convex-combination mean (assignee, ball, hoop) and a drive-detection HMM.
- It includes processed 2015-16 SportVU possessions.
- This is the best starting point for MATCH. It ports easily to PyMC or NumPyro, or use cmdstanpy directly.

**Keshri (2.2), Song (2.4).** Nothing released.
- Song's arXiv paper is CC BY-NC-SA. That covers the text only, so reimplementing the method is fine.

**Daly-Grafstein & Bornn (2.3).** Nothing released.

### 2.3 Lineups and chemistry

- **RAPM family (3.1–3.3).** No released code was found for L-RAPM, hypergraph APM or the spectral method, though all are short to implement. Ridge or Bayesian RAPM from hoopR stints is standard.
- **Fewell (3.4).** The article is CC BY, but only aggregate figures and tables were released.
- **Bransen (3.5).** No code found (unverified).

### 2.4 Play types

- **No public code** from McQueen, McIntyre, Wang & Zemel or Miller & Bornn.
- **McQueen's screen detector.** A tiny community reimplementation exists with no license. The method is a short list of geometric rules plus an SVM, so write it fresh.
- **Patton et al. (4.5) and Stats Perform.** Proprietary. Sha et al. (6.2) and the ghosting work (7.1) are patented by Stats Perform, so copy only general ideas and avoid their specific claimed pipelines.
- **No open dataset labels named sets** such as Horns, Iverson cut or Floppy. The closest open labels are listed below.

| Dataset | Labels that help | License |
|---|---|---|
| MultiSports | Basketball "screen" and "pick-and-roll defense" atomic actions | NC |
| NSVA | Fine-grained NBA events | NC |
| FineSports | 52 fine-grained types | Agreement-gated |
| Roboflow detector | Per-frame jump-shot, layup/dunk, block and possession classes | CC BY 4.0 |

### 2.5 Spacing and off-ball value

- **BMOS/BIMOS (5.3)** is the only basketball off-ball model with code. It is a work in progress with known bugs and no license, so treat it as a reference.
- **LaurieOnTracking (MIT)** gives a pitch-control implementation that can be re-parameterized for a basketball court.

### 2.6 Broadcast tracking

**KaliCalib (6.3).**
- The trained model is included.
- CeCILL-2.1 is GPL-compatible copyleft. Distributing a derivative requires releasing source.
- It is trained on fixed arena cameras, so expect to fine-tune on broadcast frames.

**DeepSportRadar (6.4).**
- The images come from Keemotion fixed cameras in LNB Pro A, not broadcast TV.
- The dataset license is NC-SA (per DatasetNinja), and the `deepsport` baseline library is NC-ND.
- Useful for research pretraining of keypoints and ball size only.

**SportsMOT (6.5).** NC data; the HF dataset is gated. Basketball clips include NCAA and NBA broadcasts, which makes it the best open tracking benchmark that resembles MSU footage.

**SoccerNet GSR (6.6).**
- sn-gamestate is GPL-3.0 and uses components under restrictive licenses:
  - PRTReid and BPBreID: Hippocratic License 3.0, which is not OSI-approved and adds use restrictions.
  - PnLCalib: GPL-2.0.
  - YOLOv8: AGPL-3.0.
- TrackLab (MIT) and CAMELTrack (Apache-2.0) are the cleanly licensed parts.
- The task definition and GS-HOTA metric are the most reusable pieces.

**TeamTrack (6.7).** Code is MIT, and the data includes basketball full-court footage. The data license is not stated anywhere checked, so ask the authors before redistributing.

**Koshkina & Elder (6.8).**
- A full pipeline: legibility classifier, ViTPose torso crop, fine-tuned PARSeq, tracklet voting. Weights are on Drive.
- The license is a Creative Commons public license with non-commercial and share-alike terms. Research use is fine; commercial use is blocked.
- Its sub-components (ViTPose, PARSeq, centroids-reid) are separately Apache-2.0 or MIT, so the same architecture can be rebuilt cleanly.

**Skalski / Roboflow (6.9; Task B item 2).** Exact assets:

*Blog and video.*
- Blog: "How to Detect, Track, and Identify Basketball Players with Computer Vision" (Sep 30, 2025), roboflow.com/blog/identify-basketball-players.
- YouTube: "Basketball AI: Player Tracking, Team Detection, and Number Recognition with Python" (Roboflow channel, Dec 4, 2025), youtube.com/watch?v=yGQb9KkvQ1Q.

*Main notebook:* github.com/roboflow/notebooks/blob/main/notebooks/basketball-ai-how-to-detect-track-and-identify-basketball-players.ipynb (last updated Aug 2026). Its stages:

| Stage | What the notebook uses |
|---|---|
| Detection | RF-DETR fine-tuned on `basketball-player-detection-3-ycjdo` (hosted model v4; the blog says RF-DETR-S; 10 classes: ball, ball-in-basket, number, player, player-in-possession, player-jump-shot, player-layup-dunk, player-shot-block, referee, rim) |
| Tracking | SAM2.1 Hiera-Large via `Gy920/segment-anything-2-real-time`, prompted once with RF-DETR boxes |
| Team assignment | SigLIP-base-patch16-224 embeddings of the central crop, then UMAP to 3-D, then k-means with k=2 (`sports.common.team.TeamClassifier`) |
| Jersey ID | Number boxes matched to players by IoS ≥ 0.9. Read with a fine-tuned SmolVLM2 (hosted `basketball-jersey-numbers-ocr/3`; 86% test accuracy, vs 56% zero-shot) or a fine-tuned ResNet-32 classifier (93%). A number is accepted after 3 agreeing consecutive reads, then mapped to names with a roster |
| Court keypoints and homography | Hosted keypoint model `basketball-court-detection-2/14`, keeping points with confidence ≥ 0.5 (at least 4 needed). Then OpenCV `findHomography` via `sports.common.view.ViewTransformer` onto an NBA/FIBA court template from `sports.basketball.config`, path smoothing, and a "radar" minimap |
| Shot events | Made/missed shot tracking from jump-shot and ball-in-basket classes (`ShotEventTracker`) |

*Other notebooks:*
- `basketball-ai-automatic-detection-of-3-second-violations.ipynb` adds paint-region projection, ViTPose+ Large ankle keypoints, and time-in-zone.
- `basketball-ai-make-or-miss-jumpshot-detection.ipynb` covers shot outcomes.

*Licenses.*
- The `sports` library code is MIT. Note that the basketball modules live on the `feat/basketball` and `feat/basketball_radar` branches, not `main`.
- The notebooks repo has no LICENSE file (flag). Treat its notebooks as examples, and rewrite rather than copy large blocks.
- Datasets are CC BY 4.0 (attribution required).
- Hosted Roboflow models need a `ROBOFLOW_API_KEY` and are covered by Roboflow's platform terms. Retrain your own RF-DETR on the CC BY data to avoid that dependency.
- RF-DETR N/S/M/L are Apache-2.0. The new Atto/Femto/Pico sizes are under Roboflow's PML 1.0, not Apache.

*Limitations stated by the author:*
- About 1–2 FPS on a T4.
- SAM2 assumes every player is visible in the first frame and is never re-prompted. This breaks on broadcast cuts.
- Masks leak onto the ball or background.
- Distant shooters are hard to read.
- The jersey data covers 00–99 unevenly (for example, "6" appears only 8 times).

*Soccer transfer.*
- `examples/soccer` and `football-ai.ipynb` (video "Football AI Tutorial", Aug 22, 2024, youtube.com/watch?v=aBVGKoNZQUw) use the same SigLIP+UMAP+KMeans team classifier, ByteTrack, a pitch-keypoint homography and a radar view.
- Ball and player detectors there are YOLOv8 (AGPL).
- The team classifier, ViewTransformer and radar code transfer directly.
- The ByteTrack-based tracking is a better template for long broadcast clips than one-shot SAM2 prompting.

**TrackID3x3 (6.10).** Apache-2.0 code bundles CAMELTrack, BoT-SORT and the Koshkina jersey pipeline. Because it includes the Koshkina code, the NC term applies to that sub-folder. The 3x3 fixed-camera videos are on Drive.

**Scorebug OCR (6.11).** No open dataset or code exists for college scorebugs. Use Apache-licensed OCR libraries (PaddleOCR, PARSeq).

### 2.7 Off-screen imputation

- **Choi 2026 (`offscreen-impute`, MIT).**
  - The only fully open, reproducible broadcast-occlusion imputer.
  - It is training-free and CPU-only.
  - Porting it means swapping the pitch for a court and soccer roles for basketball roles.
- **NAOMI and MIDAS.** Both have code but no license, and MIDAS has not released its data.
- **Zhan.**
  - Code is MIT.
  - Its basketball data is now sold through AWS Data Exchange (Stats Perform). Use the public 2015-16 SportVU mirror instead.
- **Graph Imputer.** No code. The authors could not release their data.

### 2.8 Win probability, context and markets

- Little is released as code except `bigfour/competitiveness` (CC0; R/JAGS state-space model on market lines) and the Clegg replication (no license).
- All methods here are short statistical models that can be rebuilt on hoopR plus cbbdata.

### 2.9 Data tooling

- **hoopR.**
  - Code is MIT, and the data release repo `hoopR-mbb-data` is CC BY 4.0.
  - The underlying facts come from ESPN, so check ESPN's terms before redistributing raw feeds commercially.
- **CBBpy:** Apache-2.0, v2.1.2.
- **cbbdata:** MIT. Its code was last pushed Oct 2024, but the API is live.
- **ncaahoopR:** MIT.

### 2.10 Other open pipelines and datasets (Task B item 3)

**abdullahtarek/basketball_analysis.**
- An end-to-end demo: YOLO detection for player, ball and court keypoints, ByteTrack-style tracking, FashionCLIP zero-shot team colors, homography "tactical view", ball possession, passes, interceptions, and speed and distance.
- It has no LICENSE file even though its README refers to one, and it depends on Ultralytics (AGPL-3.0). Use it for ideas only.

**NBA SportVU 2015-16.**
- `linouk23/NBA-Player-Movements` mirrors about 630 per-game `.7z` logs from the first half of the season. `neilmj/BasketballData` is the original source.
- An HF loader (`dcayton/nba_tracking_data_15_16`, Apache-2.0 script) pairs the logs with PBP from `sumitrodatta/nba-alt-awards`.
- There is no license on the data itself. It was released publicly by the NBA and STATS in 2016 and later withdrawn. Fine for research and pretraining, but do not redistribute or build a product on it.

**Court keypoint datasets.**

| Dataset | Size | License | Notes |
|---|---|---|---|
| Roboflow `basketball-court-detection-2` | 850 images | CC BY 4.0 | NBA broadcast |
| DeepSportRadar calibration | 728 images | NC | Arena cameras |
| Community Universe sets (`vayvay/basketball_keypoint_detection`, `priver-one/basketball_courts`) | n/a | Unverified | n/a |

None of these covers NCAA court markings or college floor designs.

**Jersey datasets.**

| Dataset | Size | License | Notes |
|---|---|---|---|
| Roboflow `basketball-jersey-numbers-ocr` | 3,615 | CC BY 4.0 | NBA |
| E-BARD JNR | n/a | CC BY 4.0 | NBA |
| Koshkina hockey and SoccerNet-derived crops | n/a | NC | n/a |
| SoccerNet jersey (sn-jersey) | n/a | No license file | Soccer |

**Ball detection.**
- Roboflow player-detection set (ball and rim classes; CC BY 4.0).
- E-BARD detection (CC BY 4.0).
- DeepSportRadar ball-3D, for ball size and height (NC).

**Action and play datasets.**
- NSVA (NC), MultiSports (NC), FineSports (by agreement) and E-BARD/BARD.
- PL-NBA (possession-level, 11k possessions) is not released.
- None labels college sets.

**BasketLiDAR.** Available on request only; no license stated.

### 2.11 Labeling and human-in-the-loop (Task B item 4)

**CVAT (MIT, self-hosted Community edition).**
- *Video support:* track annotation with linear interpolation between keyframes, and polygon or mask tracks.
- *Serverless auto-annotation functions:* SAM (image), TransT tracker, YOLOv7, Detectron2 and others. A CLI/SDK "agent" interface also exists for custom detector and tracker functions.
- *Limits:* the SAM2 video tracker is documented for CVAT Online and Enterprise only (Nuclio version: Enterprise; agent version: Online and Enterprise).
- *Best for:* multi-object player tracks with IDs on broadcast clips. It exports MOT, COCO and Datumaro formats.

**Label Studio (Apache-2.0, Community).**
- `VideoRectangle` with keyframe interpolation. Exports contain keyframes only unless `interpolate_key_frames` is set.
- The open ML backend repo includes `segment_anything_2_video`, `yolo`, `easyocr` and `tesseract` examples, which allow pre-labeling and interactive SAM2 video propagation.
- Some features are Enterprise-only (unverified by edition).
- *Best for:* mixed tasks (event or timestamp labels plus boxes) and custom UIs for play labels.

**Roboflow Annotate (proprietary SaaS).**
- Label Assist, Smart Polygon, box prompting and Auto Label, all paid with credits. The free tier gives 10 credits a month.
- Video is uploaded as sampled frames, so there is no true track-ID annotation.
- Projects can stay private. Universe publishing is optional and should not be used for copyrighted broadcast frames.
- *Best for:* quick detector datasets and direct RF-DETR training.

**FiftyOne (Apache-2.0, including fiftyone-brain and plugins).**
- A video dataset viewer with frame-level labels.
- Two-way integrations with CVAT and Label Studio for send-to-annotate and load-back loops.
- Brain methods (uniqueness, mistakenness, hardness, embeddings visualization) plus an Active Learning plugin; the plugin's edition and license were not confirmed.
- *Best for:* choosing which MSU frames or tracklets to label next, and auditing model errors.

**Recommended loop:**
1. Model predictions go into FiftyOne.
2. Pick uncertain or unique frames.
3. Correct them in CVAT, with interpolated tracks.
4. Load the corrections back and retrain RF-DETR.
5. Repeat.

---

## 3. Recommended starter stack

| Stage | Best open component(s) | License notes |
|---|---|---|
| **Ingest** | FFmpeg (decode), PySceneDetect (shot cuts), a custom "trackable shot" classifier on RF-DETR features. yt-dlp only for footage you have rights to | PySceneDetect BSD-3; FFmpeg LGPL/GPL depending on build. **Broadcast video is copyrighted (ESPN/BTN/FOX/CBS): analysis is a fair-use question, redistribution is not.** No open replay detector exists |
| **Court calibration** | RF-DETR keypoint (or YOLO-pose) trained on Roboflow `basketball-court-detection-2` plus your own NCAA frames, then `sports` ViewTransformer homography with temporal smoothing. KaliCalib as a reference or fallback | RF-DETR Apache-2.0 (N/S/M/L); dataset CC BY 4.0; `sports` MIT. **Add an NCAA court preset** (only NBA/FIBA exist). KaliCalib is **CeCILL copyleft**. YOLO-pose is **AGPL** |
| **Detection** | RF-DETR-S/M fine-tuned on `basketball-player-detection-3-ycjdo` + E-BARD detection + labeled MSU frames | Apache-2.0 + CC BY 4.0 (attribution). Avoid RF-DETR A/F/P (PML 1.0) and Ultralytics (**AGPL**) if the project may go commercial |
| **Tracking** | `roboflow/trackers` BoT-SORT or McByte (camera-motion compensation), optionally SAM2.1 mask refinement re-prompted per shot. TrackLab/CAMELTrack as a framework. TrackEval for HOTA | trackers and CAMELTrack Apache-2.0; TrackLab, TrackEval MIT; SAM2 Apache-2.0. Use SportsMOT/TeamTrack only for evaluation (**NC** / unstated). BoxMOT is **AGPL** |
| **Team assignment** | `sports` TeamClassifier: SigLIP + UMAP + k-means, refit per game; add a referee class | All permissive (MIT / Apache / BSD) |
| **Jersey ID** | Koshkina-style pipeline rebuilt from permissive parts: legibility filter, then ViTPose torso crop, then PARSeq or SmolVLM2 fine-tuned on Roboflow jersey OCR + E-BARD JNR, then tracklet voting. Constrain with the ESPN roster (jersey→athlete) and the hoopR on-court five (Lu et al. mutual exclusion) | PARSeq, ViTPose, SmolVLM2 Apache-2.0; datasets CC BY 4.0. Original Koshkina repo is **NC** (research only) |
| **Ball** | RF-DETR ball and rim classes + Kalman/interpolation; possession from the `player-in-possession` class; ball-height ideas from DeepSportRadar | DSR data and `deepsport` are **NC**; ballradar has no license (reimplement) |
| **Scorebug OCR** | Fixed ROI per broadcaster template, then PaddleOCR or PARSeq, then rule checks (monotonic clock, score deltas) | Apache-2.0. Avoid copying the patented scoreboard-detection claims |
| **PBP sync** | hoopR (R) or CBBpy / sportsdataverse-py, then DTW alignment of OCR clock and score to PBP `clock_display_value`, with `wallclock` for coarse alignment | hoopR MIT (data CC BY 4.0); CBBpy Apache-2.0; ESPN endpoints fall under ESPN terms |
| **Action recognition** | Stage 1: geometric rules on court coordinates (McQueen-style screens, handoffs, cuts) + Roboflow shot classes. Stage 2: mmaction2 (SlowFast/VideoMAE-style) fine-tuned on hand-labeled MSU clips; pretrain on MultiSports or NSVA for research | mmaction2 Apache-2.0; **MultiSports, NSVA, VideoMAE weights are NC**. Named sets need your own labels |
| **Matchup inference** | Franks HMM via `imadmali/bball-hmm` (Stan), extended with missing-observation emissions; validate on public SportVU 2015-16 | BSD-3; SportVU mirror has no license (research only) |
| **EPV** | Phase 1: `socceraction` VAEP/xT adapted to basketball PBP + video context. Phase 2: DeepHoops-style LSTM (own code) or SoccerMap surfaces (`un-xPass`) pretrained on SportVU 2015-16, then MSU fine-tune | socceraction MIT; un-xPass Apache-2.0; EPVDemo no license (reference only) |
| **Imputation** | `offscreen-impute` (role-anchored centroid voting) as baseline; NAOMI or Graph-Imputer-style model trained on SportVU with simulated broadcast masks | offscreen-impute MIT; NAOMI no license (reimplement) |
| **Labeling** | CVAT (tracks) + FiftyOne (curation, active learning); Label Studio for event/play labels | MIT / Apache-2.0. CVAT's SAM2 tracker is not in the self-hosted Community edition |

**License summary for the stack.** Everything recommended above as the default is MIT, Apache-2.0, BSD or CC BY 4.0. The non-commercial or copyleft items are optional:
- **NC (research only):** Koshkina jersey pipeline, SportsMOT, MultiSports, NSVA, DeepSportRadar data and `deepsport`, VideoMAE and CoTracker weights.
- **Copyleft:** sn-gamestate (GPL-3.0), KaliCalib (CeCILL), Ultralytics and BoxMOT (AGPL-3.0), PnLCalib (GPL-2.0).
- **Other restrictive:** PRTReid/BPBreID (Hippocratic 3.0), RF-DETR A/F/P (PML 1.0).
- **Unclear rights:** SportVU 2015-16 data, TeamTrack data, TrackID3x3 videos.
- **Unlicensed code (read, don't copy):** Roboflow notebooks, abdullahtarek, NAOMI, MIDAS, ballradar, EPVDemo, BMOS.

Keep NC and unlicensed assets in a separate "research" environment, so the core pipeline stays permissively licensed.

---

## 4. Gaps: nothing open exists

1. **An NCAA broadcast tracking dataset.** No open set provides college broadcast frames with court homography, 10-player IDs, ball position and PBP sync. SportsMOT has some NCAA clips but no IDs or court coordinates, and its license is NC.
2. **NCAA court template and keypoints.** Open keypoint sets are NBA-only or come from arena cameras. No college court preset or labels exist that cover the varied floor paint and logos.
3. **Replay, cut and trackable-shot detection for basketball broadcast.** There is no open model or dataset. Patton et al. solved it privately.
4. **College scorebug OCR.** There is no dataset or code, and the only references are patents.
5. **Named set plays and coverages.** There are no open labels for Horns, Floppy, Iverson cut, Spain PnR, or ICE/drop/switch coverage. MultiSports "screen" is the closest atomic label, and it is NC.
6. **Matchup ground truth.** No labeled "who guards whom" data exists for any league, college or pro.
7. **Basketball EPV code.** No maintained, licensed basketball EPV implementation exists. EPVDemo is a 2015 R demo with no license, and DeepHoops, EAV and GraphEIV are unreleased.
8. **Off-screen imputation for basketball broadcast.** Every open imputer is soccer or Metrica-based, and none handles full-frame cuts or replays.
9. **College jersey data.** All open jersey sets are NBA, soccer or hockey. College uniforms differ in fonts, sizes and colors.
10. **Licensed public NBA tracking.** The 2015-16 SportVU mirror is the only full-tracking corpus, and its license is undefined. Zhan's basketball data is now behind AWS Data Exchange.
