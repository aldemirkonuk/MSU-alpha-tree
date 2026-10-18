# Literature and Methods Review: Layered Win-Probability for MSU Men's Basketball from Broadcast Video

Prepared 2026-10-17. Scope: Michigan State men's basketball (NCAA D-I, Big Ten). Inputs: TV broadcast video plus ESPN/hoopR play-by-play (PBP). Goal: a nested win-probability and expected-points system (game, half, 5-minute segment, positional matchup, player vs player, possession) centered on the ball-handler. Benchmark: betting markets.

**How to read each entry.** Each entry gives:
- **Cite**: the citation
- **Link**: where to find it
- **Finding**: the key finding, paraphrased
- **Method**
- **Data**
- **Reuse**: what this project can take from it
- **Limit**: the main limitation for college broadcast video. "~35 games" means the season-scale data volume for one team.

Constraint used throughout: the project has no optical tracking, about 35 MSU games a season, and a moving broadcast camera with cuts, replays and players off-screen.

Verification note: Citations were checked against arXiv, publisher, conference or repository pages where possible. Where a detail could not be confirmed from a primary page, it is flagged "(unverified)".

---

## 1. Expected Possession Value (EPV) and possession-value analogues

**1.1 Cervone, D'Amour, Bornn & Goldsberry. Multiresolution EPV.**
- **Cite:** Cervone, D., D'Amour, A., Bornn, L., & Goldsberry, K. (2016). A multiresolution stochastic process model for predicting basketball possession outcomes. *JASA*, 111(514), 585–599. doi:10.1080/01621459.2016.1141685. Conference precursor: "POINTWISE: Predicting points and valuing decisions in real time with NBA optical tracking data," SSAC 2014.
- **Link:** https://arxiv.org/abs/1408.0777
- **Finding:** Expected points for a possession can be estimated continuously, in real time, by combining a fine-grained movement model with a coarse model of discrete events. The approach also exposes each player's spatial decision tendencies.
- **Method:** Two-resolution stochastic process. A continuous player-movement model, with hierarchical spatial priors shared across players, is coupled to a semi-Markov model over discrete "macro" states: pass, shot, turnover, and ball-handler identity. EPV is the conditional expectation of points given the current full state.
- **Data:** NBA SportVU optical tracking, 25 Hz, all 10 players plus the ball.
- **Reuse:** The core architecture. A coarse macro-state chain (ball-handler, court zone, action) is feasible from broadcast plus PBP even when micro-movement is noisy. Hierarchical pooling across players is the right answer to small college samples. The "every pass changes the reference frame" design matches EPV's ball-handler-indexed macro states.
- **Limit:** Requires full 10-player positions every frame. Broadcast gives partial and noisy positions. Parameter counts assume hundreds of NBA games, not ~35.

**1.2 Sicilia, Pelechrinis & Goldsberry. DeepHoops.**
- **Cite:** Sicilia, A., Pelechrinis, K., & Goldsberry, K. (2019). DeepHoops: Evaluating micro-actions in basketball using deep feature representations of spatio-temporal data. *KDD 2019*. doi:10.1145/3292500.3330719.
- **Link:** https://arxiv.org/abs/1902.08081
- **Finding:** A sequence model over recent player and ball locations gives calibrated probabilities of each terminal action. The resulting expected-points curve can credit off-ball micro-actions.
- **Method:** End-to-end deep sequence classifier (LSTM-style) predicting the terminal outcome class at every moment, mapped to expected points. Uses a tuned down-sampling scheme for class imbalance.
- **Data:** NBA SportVU tracking.
- **Reuse:** A simpler, "model-free" alternative to 1.1. The terminal-action framing maps directly onto PBP outcome labels (make, miss, turnover, foul), so labels are free from hoopR.
- **Limit:** Data-hungry. It also assumes complete coordinates, and imputed positions would propagate error.

**1.3 Fernández, Bornn & Cervone. Deep EPV for soccer.**
- **Cite:** Fernández, J., Bornn, L., & Cervone, D. (2021). A framework for the fine-grained evaluation of the instantaneous expected value of soccer possessions. *Machine Learning*, 110, 1389–1427. doi:10.1007/s10994-021-05989-6. Conference version: "Decomposing the Immeasurable Sport," SSAC 2019.
- **Link:** https://arxiv.org/abs/2011.09426
- **Finding:** Decomposing EPV into separately learned, calibrated components gives interpretable full-surface value maps:
  - P(pass succeeds to location)
  - P(shot)
  - value of each destination
- **Method:** Several CNN and U-Net-style networks (SoccerMap) produce probability surfaces over the pitch. They are combined with an explicit EPV equation.
- **Data:** Full-pitch professional soccer tracking plus event data.
- **Reuse:** The decomposition pattern is the strongest template for answering questions like "PnR on right wing with shooter in corner." Learn separate surfaces for pass reception, shot make probability and turnover risk, conditioned on configuration, then combine them. Interpretable components can be trained with less data than an end-to-end model.
- **Limit:** Needs full tracking. Basketball has 5-on-5 in a small space, so the surfaces need a different resolution. Training CNN surfaces on ~35 games is thin unless priors or transfer come from other teams' broadcast footage.

**1.4 Decroos, Bransen, Van Haaren & Davis. VAEP.**
- **Cite:** Decroos, T., Bransen, L., Van Haaren, J., & Davis, J. (2019). Actions speak louder than goals: Valuing player actions in soccer. *KDD 2019*. doi:10.1145/3292500.3330758.
- **Link:** https://arxiv.org/abs/1802.07127
- **Finding:** An action's value equals the change in short-horizon scoring and conceding probabilities before and after it. This works from event data alone.
- **Method:** Gradient-boosted classifiers predict P(score in next k actions) and P(concede in next k actions) from features of the last few actions (the SPADL representation). Value is the difference in those probabilities across the action.
- **Data:** Event data from top European leagues, 2016/17 to 2017/18.
- **Reuse:** The most transferable method for this project's PBP-first phase. Every ESPN play becomes an "action" (shot, rebound, turnover, foul, assist), and broadcast-derived context (zone, ball-handler, defender distance) is added where available. Works with sparse spatial data and is explainable.
- **Limit:** Basketball PBP lacks passes and dribbles, so the action stream is much coarser than soccer event data unless video fills it in.

**1.5 Singh. Expected Threat (xT).**
- **Cite:** Singh, K. (c. 2018–2019). Introducing Expected Threat (xT). Blog post.
- **Link:** https://karun.in/blog/expected-threat.html
- **Finding:** A zone-based Markov value function computes the value of moving the ball between zones from simple counts.
  - Each zone's value = P(shoot) × P(goal) + P(move) × Σ P(move to z) × value(z).
  - It is solved by a few value iterations.
- **Method:** Grid discretization (16×12), with empirical shot, move and transition probabilities and value iteration.
- **Data:** One Premier League season of event data.
- **Reuse:** A cheap, robust baseline for a ball-handler-centered court-zone Markov chain. The state can be extended to (zone, ball-handler role, action type). It is ideal for a ~35-game sample with league-wide priors.
- **Limit:** Ignores defender and teammate positions. Transitions need pass endpoints, which basketball PBP lacks and video must supply.

**1.6 Successors in basketball: decision-quality EPV variants.**
- **Cite:**
  - Expected Action Value (EAV): "Leveraging expected action value to measure on-court decision-making skills in basketball," *Journal of Sports Analytics* 11 (2025). doi:10.1177/22150218251325018. An MIT Sports Lab thesis by I. Jutamulia covers related work.
  - GraphEIV: "A framework for estimating the expected immediate value in basketball using graph neural networks," MLSA 2024, *CCIS* 2460, pp. 29–40 (Springer 2025). doi:10.1007/978-3-031-86692-0_3.
- **Link:**
  - https://sportslab.mit.edu/theses/expected-possession-value-an-evaluation-framework-for-decision-making-strategy-and-execution-in-basketball
  - https://doi.org/10.1007/978-3-031-86692-0_3
- **Finding:** Two results.
  - EAV values the ball-handler's immediate pass and shot options and flags "missed opportunities." This splits team performance into strategy (creating options) and execution.
  - GraphEIV splits immediate value into four parts: xFG, xNAT (pass vs shot), xR (which teammate receives) and xTO.
- **Method:** Tracking-based option valuation (EAV). A graph neural network over player nodes (GraphEIV).
- **Data:** NBA tracking.
- **Reuse:** Both are explicitly ball-handler-centered. A GNN over a variable number of visible players handles off-screen players more gracefully than fixed-size inputs, because nodes can be masked.
- **Limit:** Validated only on complete NBA tracking. The papers report no tests with missing nodes.

## 2. Defensive matchups and player-vs-player evaluation

**2.1 Franks, Miller, Bornn & Goldsberry. Spatial structure of defensive skill.**
- **Cite:** Franks, A., Miller, A., Bornn, L., & Goldsberry, K. (2015). Characterizing the spatial structure of defensive skill in professional basketball. *Annals of Applied Statistics*, 9(1), 94–121. doi:10.1214/14-AOAS799. Companion: "Counterpoints: Advanced defensive metrics for NBA basketball," SSAC 2015.
- **Link:** https://arxiv.org/abs/1405.0231
- **Finding:** "Who is guarding whom" can be inferred probabilistically every frame. Defenders' effects on shot frequency and efficiency can then be separated spatially.
- **Method:** A hidden Markov model over matchup assignments. Each defender's expected location is a convex combination of their assignee, the ball and the basket (roughly 0.62 / 0.11 / 0.27, per the paper; unverified here). It is combined with spatial point processes, non-negative matrix factorization of shot surfaces and hierarchical regression.
- **Data:** NBA SportVU tracking.
- **Reuse:** The matchup-HMM is simple, has few parameters and works with only the 10 positions per frame. Even noisy broadcast positions can feed it, with the HMM smoothing over gaps. This is the foundation of the "positional matchup" and "player vs player" layers.
- **Limit:** Needs all 10 players located. When the camera excludes weak-side defenders, the emission model must handle missing observations, which is possible in an HMM but untested in the paper.

**2.2 Keshri, Oh, Zhang & Iyengar. Defensive assignment plus event HMMs.**
- **Cite:** Keshri, S., Oh, M., Zhang, S., & Iyengar, G. (2019). Automatic event detection in basketball using HMM with energy based defensive assignment. *Journal of Quantitative Analysis in Sports*, 15(2), 141–154. doi:10.1515/jqas-2017-0126.
- **Link:** https://www.nessis.org/nessis17/Keshri_adj.pdf
- **Finding:** The pipeline improves on Franks et al. for assignment accuracy and detects ball screens, drives and post-ups without labels.
- **Method:** Location- and player-dependent attraction ("energy") model using HMMs, Gaussian processes and a "bond-breaking" switch model. Learned assignments then feed event-detection HMMs.
- **Data:** NBA optical tracking.
- **Reuse:** Unsupervised, which matters because there are no labeled college matchups. Switches in assignment are themselves the signal for screens.
- **Limit:** Same full-visibility assumption. Unsupervised detectors may drift with college spacing and zone defenses, which are more common in NCAA play than in the NBA.

**2.3 Daly-Grafstein & Bornn. Shot trajectories and defensive impact.**
- **Cite:** Daly-Grafstein, D., & Bornn, L. (2020). Using in-game shot trajectories to better understand defensive impact in the NBA. *Journal of Sports Analytics*. Related: "Rao-Blackwellizing field goal percentage," *JQAS* (2019). doi:10.1515/jqas-2018-0064.
- **Link:** https://arxiv.org/abs/1905.00822 and https://arxiv.org/abs/1808.04871
- **Finding:** Ball-trajectory features (entry angle, depth, left-right) estimate make probability with far less noise than raw makes. This exposes defender effects on shot quality with fewer samples.
- **Method:** Model make probability from 3-D ball arc, then use the expected make probability in place of the 0/1 outcome (Rao-Blackwellization).
- **Data:** NBA ball tracking.
- **Reuse:** Variance reduction is essential at ~35 games. Even coarse ball-arc estimates from broadcast (DeepSportRadar ball-3D work, §6) could shrink the noise in player-vs-player shooting splits.
- **Limit:** Requires accurate 3-D ball position. From broadcast it is approximate at best.

**2.4 Song et al. Factorized-attention transformers for coverage (NFL; transferable).**
- **Cite:** Song, K., Diewald, E., Siddiquee, O., Boomhower, C., Abdoo, K., Band, M., & Lee, A. (2026). Decoding defensive coverage responsibilities in American football using factorized attention based transformer models. arXiv:2603.25901.
- **Link:** https://arxiv.org/abs/2603.25901
- **Finding:** A transformer with separate time-attention and agent-attention predicts frame-by-frame defender-receiver matchups at about 89% or better accuracy.
- **Method:** Factorized spatio-temporal attention, trained on randomly truncated trajectories.
- **Data:** NFL tracking with labeled coverages.
- **Reuse:** A modern supervised alternative to the HMM in 2.1 once a few hundred MSU possessions are hand-labeled. Agent attention naturally supports masking of missing players.
- **Limit:** Supervised and NFL-specific. College basketball has no matchup labels.

## 3. Player chemistry, lineup synergy and plus-minus

**3.1 Sill. Regularized adjusted plus-minus (RAPM).**
- **Cite:** Sill, J. (2010). Improved NBA adjusted +/- using regularization and out-of-sample testing. *SSAC 2010*.
- **Link:** https://sloansportsconference.com/research-papers/improved-nba-adjusted-using-regularization-and-out-of-sample-testing
- **Finding:** Ridge-regularizing adjusted plus-minus nearly doubles its out-of-sample predictive accuracy.
- **Method:** Stint-level regression of point margin on 10 player indicators, with an L2 penalty tuned by cross-validation.
- **Data:** NBA play-by-play stints.
- **Reuse:** The baseline for the "positional matchup" and "lineup" layers. Stints come directly from hoopR substitution data. Fit over all D-I games, not just MSU's, to identify opponents. Bayesian priors from box-score or recruiting ratings help with transfer-portal roster churn.
- **Limit:** Collinearity is severe in college, with short benches and about 1,100–1,300 possessions per player per season. Single-team, single-season RAPM is very noisy without informative priors.

**3.2 Maymin, Maymin & Shen. Skills Plus-Minus and synergy.**
- **Cite:** Maymin, A., Maymin, P., & Shen, E. (2013). NBA chemistry: Positive and negative synergies in basketball. *International Journal of Computer Science in Sport*, 12(2), 4–23.
- **Link:** https://lida.sport-iat.de/dbb/Record/4030460
- **Finding:** Rating players on offense and defense in three separate skills (scoring, rebounding, ball-handling) and simulating lineups reveals synergies worth up to about 6 wins. Teams are about as likely to have negative chemistry as positive.
- **Method:** Skills Plus-Minus: separate RAPM-like ratings per skill event, then Monte-Carlo game simulation for 5-man units vs the sum of parts.
- **Data:** NBA play-by-play.
- **Reuse:** A play-by-play-only way to define "chemistry" as lineup value beyond the sum of individual skills. It can be built on hoopR events today.
- **Limit:** Interaction terms need many shared minutes. In college, most pairings have too few possessions without strong shrinkage.

**3.3 Lineup-level priors and group decompositions.**
- **Cite:**
  - Petridis, C., & Pelechrinis, K. (2026). Lineup Regularized Adjusted Plus-Minus (L-RAPM). arXiv:2601.15000.
  - Josephs, N., & Upton, E. (2024/2025). Hypergraph adjusted plus-minus. arXiv:2403.20214.
  - Devlin, S., & Uminsky, D. (2020). Identifying group contributions in NBA lineups with spectral analysis. arXiv:2006.14188.
- **Link:**
  - https://arxiv.org/abs/2601.15000
  - https://arxiv.org/abs/2403.20214
  - https://arxiv.org/abs/2006.14188
- **Finding:** Three results.
  - L-RAPM: lineup ratings with player-informed priors beat baselines, and the gain is largest for small lineup samples.
  - Hypergraph APM: individuals, pairs, triples and full lineups can be rated jointly.
  - Spectral analysis: a lineup's value can be split orthogonally into contributions of groups of size 1 to 5.
- **Method:** Opponent-adjusted ridge regression with hierarchical priors; a hypergraph design matrix; Fourier analysis on the symmetric group.
- **Data:** NBA play-by-play.
- **Reuse:** L-RAPM is designed for sparse lineups, which suits a college bench. The hypergraph and spectral methods give a principled "pair chemistry" estimate for MSU duos (for example, guard and big in pick-and-roll).
- **Limit:** All are box-score or stint level, with no spatial context. They are NBA-validated only.

**3.4 Fewell, Armbruster, Ingraham, Petersen & Waters. Passing networks.**
- **Cite:** Fewell, J. H., Armbruster, D., Ingraham, J., Petersen, A., & Waters, J. S. (2012). Basketball teams as strategic networks. *PLoS ONE*, 7(11), e47445.
- **Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC3490980
- **Finding:** Team ball movement can be modeled as a network (player nodes plus inbound and outcome nodes). Network entropy and flow centrality differ across teams and relate to style.
- **Method:** Transition networks from hand-coded possession sequences, using flow centrality, clustering and entropy.
- **Data:** Hand-coded passes from 2010 NBA playoff games.
- **Reuse:** A pass-network is exactly the "ball-handler reference-frame" chain. Video-detected passes (§6) give directed edges, and PBP assists are a weak proxy. ncaahoopR already builds assist networks.
- **Limit:** Small samples. Assist-only networks miss most passes. A pass detector on broadcast video is required for a real network.

**3.5 Bransen & Van Haaren. Pairwise chemistry (soccer).**
- **Cite:** Bransen, L., & Van Haaren, J. (2020). Player chemistry: Striving for a perfectly balanced soccer team. *SSAC 2020*. arXiv:2003.01712.
- **Link:** https://arxiv.org/abs/2003.01712
- **Finding:** Pairwise offensive and defensive chemistry can be measured from joint action values (VAEP) and predicted for pairs who have never played together.
- **Method:** Aggregate action values for interactions within pairs, then regress on player attributes to predict chemistry for unseen pairs.
- **Data:** 361 seasons across 106 competitions (event data).
- **Reuse:** A direct blueprint for "player chemistry" as a possession-value quantity rather than plus-minus. Predicting unseen pairs matters because MSU rosters turn over each year through the portal.
- **Limit:** Soccer event data is richer than basketball PBP.

## 4. Pick-and-roll and play-type detection

**4.1 McQueen, Wiens & Guttag. On-ball screen recognition.**
- **Cite:** McQueen, A., Wiens, J., & Guttag, J. (2014). Automatically recognizing on-ball screens. *SSAC 2014*.
- **Link:** https://www.sloansportsconference.com/research-papers/automatically-recognizing-on-ball-screens
- **Finding:** On-ball screens can be detected from tracking with high accuracy using hand-crafted features of handler, screener and defender geometry.
- **Method:** Rule-based candidate generation (screener close to the ball-handler), then supervised classification (SVM) on distance and velocity features.
- **Data:** NBA SportVU plus labeled screens.
- **Reuse:** The feature set is small and geometric, so it is robust to broadcast noise. On-ball screens happen near the ball, which is almost always on-screen, making this the most feasible detector for broadcast video.
- **Limit:** Needs the screener's defender located. Labels must be re-created for college.

**4.2 McIntyre, Brooks, Guttag & Wiens. Ball-screen defense.**
- **Cite:** McIntyre, A., Brooks, J., Guttag, J., & Wiens, J. (2016). Recognizing and analyzing ball screen defense in the NBA. *SSAC 2016*.
- **Link:** https://www.sloansportsconference.com/research-papers/recognizing-and-analyzing-ball-screen-defense-in-the-nba
- **Finding:** A supervised classifier labeled 270,823 screens by defensive coverage (over, under, switch, trap) across four seasons, enabling team and player coverage tendencies.
- **Method:** Supervised machine learning on trajectory features around the screen.
- **Data:** NBA SportVU, four seasons.
- **Reuse:** Coverage type is a key conditioning variable for "PnR on the right wing raises expected points by X." Value depends on how it is defended.
- **Limit:** Same full-tracking dependence. Coverage labels for college must be hand-made.

**4.3 Wang & Zemel. Classifying NBA offensive plays with RNNs.**
- **Cite:** Wang, K.-C., & Zemel, R. (2016). Classifying NBA offensive plays using neural networks. *SSAC 2016*.
- **Link:** https://www.cs.toronto.edu/~zemel/documents/1536-Classifying-NBA-Offensive-Plays-Using-Neural-Networks.pdf
- **Finding:** An LSTM on trajectory "footprint" images reaches 66% top-1 and 81% top-3 accuracy on 11 Raptors play calls. Fine-tuning transfers to a new season with about 100 labels (62% top-1).
- **Method:** Trajectories rendered as images, then an RNN/LSTM with auxiliary prediction and noise regularization.
- **Data:** SportVU 2013–14 with 1,435 labeled plays.
- **Reuse:** Shows that a few hundred labels plus transfer are enough, which suits labeling MSU set plays.
- **Limit:** Set-play labels are team-specific, and accuracy is moderate.

**4.4 Miller & Bornn. Possession sketches.**
- **Cite:** Miller, A. C., & Bornn, L. (2017). Possession sketches: Mapping NBA strategies. *SSAC 2017*.
- **Link:** https://www.sloansportsconference.com/research-papers/possession-sketches-mapping-nba-strategies
- **Finding:** Unsupervised topic models over a dictionary of short movement primitives cluster possessions into recurring offensive structures.
- **Method:** Trajectory segmentation into "actions," then an LDA-style hierarchical model.
- **Data:** NBA tracking.
- **Reuse:** Label-free play-type discovery for MSU. Primitives can be learned from partial trajectories.
- **Limit:** Interpretability depends on clean trajectories.

**4.5 Patton et al. (Stats Perform). College tracking from broadcast video.**
- **Cite:** Patton, A., Scott, M., Walker, N., Ottenwess, A., Power, P., Cherukumudi, A., & Lucey, P. (2021). Predicting NBA talent from enormous amounts of college basketball tracking data. *SSAC 2021*.
- **Link:** https://www.sloansportsconference.com/research-papers/predicting-nba-talent-from-enormous-amounts-of-college-basketball-tracking-data
- **Finding:** Player and ball tracking extracted from historical NCAA D-I broadcast video (about 650k possessions, 300M+ frames) supports event detection at about 0.8 recall and 0.7 precision. That detection covers ball-screens, drives, isolations, post-ups, handoffs, off-ball screens and matchups. Tracking-derived features beat PBP-only features for NBA-success prediction (log-loss 0.30 vs 0.40).
- **Method:** The full pipeline:
  1. Trackable-shot classification
  2. Moving-camera calibration
  3. Pose-based player detection
  4. Tracking and re-ID
  5. Ball tracking
  6. OCR of game and shot clocks
  7. Event detection (actor-action attention network)
  8. Fuzzy merging with PBP
- **Data:** Thousands of NCAA D-I men's broadcast games.
- **Reuse:** The closest published precedent to this entire project. It shows the end-to-end pipeline is feasible for college broadcast, and its stage list is a ready architecture. The OCR-plus-PBP fuzzy merge is the right sync strategy.
- **Limit:** A proprietary system. It reports no tracking accuracy and does not say how off-screen players are handled. The paper focuses on player evaluation, not possession value or betting.

**4.6 Play-type value reference: Synergy-style points per possession (PPP).**
- **Cite:** Practitioner resource. Synergy Sports play-type categories, explained in Nylon Calculus, "How to understand Synergy play type categories" (FanSided, 2017).
- **Link:** https://fansided.com/2017/09/08/nylon-calculus-understanding-synergy-play-type-data/
- **Finding:** The industry standard values play types by PPP: PnR ball-handler, PnR roll-man, spot-up, isolation, post-up, transition, off-screen, handoff, cut and putback.
- **Method:** Manual video logging.
- **Data:** All D-I games (commercial).
- **Reuse:** Defines a sensible play-type taxonomy and PPP benchmarks for validation.
- **Limit:** Paywalled. Play-type value is unconditional and ignores spacing and personnel configuration.

## 5. Spacing and off-ball value

**5.1 NBA Gravity (league stat).**
- **Cite:** NBA.com Staff (2025, updated 2026). Intro to Gravity: NBA's new stat measuring off-ball pressure.
- **Link:** https://www.nba.com/news/intro-to-gravity-stat-nba-2025
- **Finding:** Gravity is the difference between the defensive pressure a player actually draws and the pressure a model expects given ball and player location, computed frame by frame on a −100 to 100 scale.
- **Method:** An ML "expected defensive pressure" model on pose tracking (29 body points at 60 Hz), with actual minus expected pressure as the metric.
- **Data:** NBA optical pose tracking.
- **Reuse:** The expected-vs-actual attention design can be copied with defender distance to each offensive player. For the corner shooter in the example question, measure how far the corner defender is pulled from the help position.
- **Limit:** Proprietary. The off-ball corner shooter is often off-screen on broadcast.

**5.2 Lucey, Bialkowski, Carr, Yue & Matthews. How to get an open shot.**
- **Cite:** Lucey, P., Bialkowski, A., Carr, P., Yue, Y., & Matthews, I. (2014). How to get an open shot: Analyzing team movement in basketball using tracking data. *SSAC 2014*.
- **Link:** https://la.disneyresearch.com/publication/how-to-get-an-open-shot-analyzing-team-movement-in-basketball-using-tracking-data/
- **Finding:** Open threes go in about 40% of the time vs about 32% for contested ones. The number of defensive role-swaps in a possession predicts whether an open shot results.
- **Method:** Role-based (permutation-invariant) team representation, formation change analysis and play retrieval.
- **Data:** SportVU 2012–13, about 20k possessions ending in a three-point attempt.
- **Reuse:** Role-based representation solves the "who is who" problem when identity is uncertain from broadcast. Counting role-swaps is cheap and robust.
- **Limit:** Needs all 10 players.

**5.3 Kono & Fujii. Off-ball scoring opportunity models (BMOS/BIMOS).**
- **Cite:** Kono, R., & Fujii, K. (2025). Mathematical models for off-ball scoring prediction in basketball. MLSA 2024, *CCIS* 2460 (Springer). doi:10.1007/978-3-031-86692-0_4. arXiv:2406.08749.
- **Link:** https://arxiv.org/abs/2406.08749
- **Finding:** Adapting soccer's Off-Ball Scoring Opportunity (OBSO) to basketball works. Adding an interception model (BIMOS) improves prediction of team scoring.
- **Method:** Physics-style motion and control models (pitch-control analogue) times a scoring model, extended with pass-interception likelihood.
- **Data:** 630 NBA games, 2015–16 SportVU.
- **Reuse:** A transparent, low-parameter off-ball value. Few parameters means it can be calibrated on ~35 games. It values the corner shooter's threat even without the ball.
- **Limit:** Requires positions of all off-ball players.

**5.4 Spearman; Fernández & Bornn. Space control (soccer precursors).**
- **Cite:**
  - Spearman, W. (2018). Beyond expected goals. *SSAC 2018*.
  - Fernández, J., & Bornn, L. (2018). Wide open spaces: A statistical technique for measuring space creation in professional soccer. *SSAC 2018*.
- **Link:** https://www.sloansportsconference.com (paper archive)
- **Finding:** Probabilistic "control" of space, based on time-to-intercept, combined with value surfaces measures off-ball scoring opportunity and space creation.
- **Method:** Physics-based reachability (Spearman); Gaussian influence fields (Fernández & Bornn).
- **Data:** Soccer tracking.
- **Reuse:** The conceptual basis of 5.3 and of measuring how much space an MSU action creates.
- **Limit:** Soccer scale. Basketball needs a defender-reach model tuned to a 94×50 ft court.

**5.5 Spacing geometry.**
- **Cite:**
  - Tsiakalos, A., & Tsiakalos, A. (2025). Graph-based quantification of basketball spacing using spatial and network metrics. *STADIUM – Hungarian Journal of Sport Sciences*, 8(2).
  - Metulini, R., Manisera, M., & Zuccolotto, P. (2018). Modelling the dynamic pattern of surface area in basketball and its effects on team performance. *Journal of Quantitative Analysis in Sports*. Related preprint: "Sensor analytics in basketball," arXiv:1707.01430.
- **Link:**
  - https://dea.lib.unideb.hu/items/336f64cc-e81a-4e19-b1cf-2bca04cef27b
  - https://arxiv.org/abs/1707.01430
- **Finding:** Convex-hull area, total pairwise distance and minimum-spanning-tree weight track tactical efficiency. Offensive hull area relates to scoring.
- **Method:** Geometric and graph descriptors per frame.
- **Data:** Tracking (sensor or optical).
- **Reuse:** Cheap spacing features for configuration-conditioned expected-points models.
- **Limit:** Hull area is biased when players are missing. The weak-side corner, which matters most, is the most often off-screen.

## 6. Tracking from broadcast video

**6.1 Lu, Ting, Little & Murphy. Track and identify players in broadcast basketball.**
- **Cite:** Lu, W.-L., Ting, J.-A., Little, J. J., & Murphy, K. P. (2013). Learning to track and identify players from broadcast sports videos. *IEEE TPAMI*, 35(7), 1704–1716.
- **Link:** https://www.cs.ubc.ca/~murphyk/Papers/weilwun-pami12.pdf
- **Finding:** Broadcast NBA players can be detected, tracked and identified with about 85–92% ID accuracy using only about 200 labels. The key trick is play-by-play substitutions, which restrict the candidate set to the 5 players on court.
- **Method:**
  - DPM detection plus color-histogram team classifier
  - Kalman tracking-by-detection
  - Conditional random field (CRF) identification from weak cues, with mutual-exclusion constraints
  - Weakly supervised EM
  - Court homography by ICP edge matching (about 7 px error at 720p)
- **Data:** 2010 NBA Finals broadcast.
- **Reuse:** The single most important idea for this project. Use hoopR substitution data as a hard prior on identity (the 5 on court out of about 13), with mutual exclusion. Modern detectors replace DPM, but the CRF plus PBP prior design still applies.
- **Limit:** Older detectors. Tested on one series with fixed team colors.

**6.2 Sha, Hobbs, Felsen, Wei, Lucey & Ganguly. End-to-end broadcast camera calibration.**
- **Cite:** Sha, L., Hobbs, J., Felsen, P., Wei, X., Lucey, P., & Ganguly, S. (2020). End-to-end camera calibration for broadcast videos. *CVPR 2020*. doi:10.1109/CVPR42600.2020.01364.
- **Link:** https://openaccess.thecvf.com/content_CVPR_2020/papers/Sha_End-to-End_Camera_Calibration_for_Broadcast_Videos_CVPR_2020_paper.pdf
- **Finding:** Court segmentation, template-based pose and a spatial-transformer refinement trained end to end give state-of-the-art homography on a new college basketball dataset, about 100× faster than prior work.
- **Method:** Area-based court segmentation, then camera-pose retrieval from embedded templates, then homography refinement via a spatial transformer network (STN).
- **Data:** College basketball broadcast plus WorldCup 2014 (soccer).
- **Reuse:** Built for college broadcast, which addresses varied court paint, logos and floor designs. It is the calibration stage of 4.5.
- **Limit:** The college dataset is not public (to my knowledge, unverified). Re-implementation is needed.

**6.3 Maglo, Orcesi & Pham. KaliCalib (basketball court registration).**
- **Cite:** Maglo, A., Orcesi, A., & Pham, Q.-C. (2022). KaliCalib: A framework for basketball court registration. *ACM MMSports '22*. doi:10.1145/3552437.3555701.
- **Link:** https://arxiv.org/abs/2209.07795
- **Finding:** Encoder-decoder keypoint prediction with perspective-aware sampling and heavy augmentation cuts calibration error by 4.7× vs the DeepSportRadar baseline.
- **Method:** Dense keypoint heatmaps, then robust homography, plus basket-position regression.
- **Data:** DeepSportRadar calibration challenge (professional basketball, multiple arenas).
- **Reuse:** Open, basketball-specific calibration recipe. Keypoint-based homography handles zoomed broadcast views when enough lines are visible.
- **Limit:** Challenge images come from fixed, wide arena cameras, not zoomed and panning TV cameras. Tight close-ups and replays fail.

**6.4 DeepSportRadar-v1 and MMSports challenges.**
- **Cite:** Van Zandycke, G., Somers, V., Istasse, M., Del Don, C., & Zambrano, D. (2022). DeepSportradar-v1: Computer vision dataset for sports understanding with high quality annotations. *ACM MMSports '22*.
- **Link:** https://arxiv.org/abs/2208.08190 and https://github.com/DeepSportradar
- **Finding:** A basketball-specific benchmark with four tasks: ball 3-D localization, camera calibration, player instance segmentation and player re-identification.
- **Method:** Dataset plus yearly challenges (2022–2023) with baselines.
- **Data:** High-resolution professional basketball arena images with camera parameters.
- **Reuse:** Pretraining data for court keypoints, player segmentation and re-ID on basketball. The ball-3D task is the only public basketball ball-height benchmark.
- **Limit:** Arena camera views, not broadcast. No jersey-number task and no long video sequences.

**6.5 Cui et al. SportsMOT.**
- **Cite:** Cui, Y., Zeng, C., Zhao, X., Yang, Y., Wu, G., & Wang, L. (2023). SportsMOT: A large multi-object tracking dataset in multiple sports scenes. *ICCV 2023*.
- **Link:** https://arxiv.org/abs/2304.05170
- **Finding:** In sports, the hard part of multi-object tracking is association (similar appearance, fast motion), not detection. MixSort adds appearance association to motion-based trackers.
- **Method:** Dataset plus MixSort, a MixFormer-style appearance model added to ByteTrack/OC-SORT.
- **Data:** 240 clips, 150k+ frames, 1.6M boxes across basketball, volleyball and football (largely broadcast-style footage).
- **Reuse:** Directly includes basketball broadcast-like clips. A good benchmark and pretraining set for the MSU tracker.
- **Limit:** No identities (jersey or name) and no court coordinates. Short clips.

**6.6 SoccerNet Tracking and Game State Reconstruction.**
- **Cite:**
  - Cioppa, A., et al. (2022). SoccerNet-Tracking: Multiple object tracking dataset and benchmark in soccer videos. *CVPRW 2022*.
  - Somers, V., Joos, V., Cioppa, A., et al. (2024). SoccerNet Game State Reconstruction: End-to-end athlete tracking and identification on a minimap. *CVPRW 2024*.
  - Annual challenges, including SoccerNet 2025 Challenges Results, arXiv:2508.19182.
- **Link:**
  - https://arxiv.org/abs/2204.06918
  - https://arxiv.org/abs/2404.11335
  - https://github.com/SoccerNet/sn-gamestate
- **Finding:** Game State Reconstruction (GSR) is defined as top-view position plus role, team and jersey for every athlete from a single moving broadcast camera. The GS-HOTA metric scores it. The task remains far from solved.
- **Method:** Modular baseline pipeline: detection, re-ID, tracking, pitch-line calibration, jersey OCR and tracklet-level voting.
- **Data:** SoccerNet-GSR: 200 × 30 s broadcast clips, 2.36M athlete positions labeled with role, team and jersey.
- **Reuse:** The task definition is exactly this project's video stage. The open-source sn-gamestate pipeline (built on TrackLab) can be adapted to basketball by swapping the field model and retraining detectors. GS-HOTA is the right evaluation metric.
- **Limit:** Soccer. Basketball has more occlusion and more close-ups. Players are larger in frame, but the camera cuts more often.

**6.7 Scott et al. TeamTrack.**
- **Cite:** Scott, A., Uchida, I., Ding, N., Umemoto, R., Bunker, R., Kobayashi, R., Koyama, T., Onishi, M., Kameda, Y., & Fujii, K. (2024). TeamTrack: A dataset for multi-sport multi-object tracking in full-pitch videos. *CVPRW 2024*.
- **Link:** https://arxiv.org/abs/2404.13868
- **Finding:** Standard appearance-based trackers often fail in team sports because players look alike but move differently. Motion modeling matters.
- **Method:** Dataset plus tracker benchmark.
- **Data:** Full-pitch video of soccer, basketball and handball.
- **Reuse:** Basketball full-court sequences for tracker evaluation. Supports adding motion priors (Kalman or learned) to association.
- **Limit:** Full-court fixed or drone views, not broadcast.

**6.8 Koshkina & Elder. Jersey number recognition.**
- **Cite:** Koshkina, M., & Elder, J. H. (2024). A general framework for jersey number recognition in sports video. *CVPRW 2024*.
- **Link:** https://arxiv.org/abs/2405.13896
- **Finding:** Scene-text recognition adapted to jerseys, with legibility filtering, pose-guided crops and tracklet-level aggregation, reaches 91.4% image-level accuracy (hockey) and 87.4% tracklet-level accuracy (SoccerNet).
- **Method:** Legibility classifier, then pose-based torso crop, then a fine-tuned STR model (PARSeq), then voting across the tracklet.
- **Data:** Hockey jersey dataset (new) plus SoccerNet jersey challenge.
- **Reuse:** Tracklet-level voting plus the PBP lineup prior (6.1) gives near-certain identity. Combine with ESPN roster jersey numbers (§12).
- **Limit:** Basketball jerseys are front and back. Many frames are illegible, and numbers 0/00 and similar-looking digits cause confusion.

**6.9 Skalski (Roboflow). Basketball AI open pipeline (practitioner).**
- **Cite:** Skalski, P. (2025, Sept 30). How to detect, track, and identify basketball players with computer vision. Roboflow blog.
- **Link:** https://roboflow.com/blog/identify-basketball-players
- **Finding:** A working open notebook for basketball:
  - RF-DETR detection (players, numbers, ball, rim)
  - SAM2 mask tracking
  - SigLIP plus UMAP plus k-means team split
  - Jersey reading with a fine-tuned ResNet (93%) or SmolVLM2 (86%)
- **Method:** Foundation-model composition. Runs at about 1–2 FPS on a T4 GPU.
- **Data:** Custom labeled basketball frames.
- **Reuse:** The fastest way to a prototype on MSU footage. The team-clustering and number-confirmation heuristics (3 consecutive agreeing reads) can be reused directly.
- **Limit:**
  - Not real-time.
  - Assumes all players are visible in the first frame, with no re-prompting after cuts.
  - No court homography in the post.

**6.10 Yamada et al. TrackID3x3.**
- **Cite:** Yamada, K., Yin, L., Hu, Q., Ding, N., Iwashita, S., Ichikawa, J., Kotani, K., Yeung, C., & Fujii, K. (2025). TrackID3x3: A dataset and algorithm for multi-player tracking with identification and pose estimation in 3x3 basketball full-court videos. arXiv:2503.18282.
- **Link:** https://arxiv.org/abs/2503.18282
- **Finding:** Introduces a "Track-ID" task (tracking plus identity, no field registration) with BoT-SORT-ReID and pose baselines for basketball.
- **Method:** Dataset plus baseline.
- **Data:** Fixed indoor, fixed outdoor and drone 3x3 footage.
- **Reuse:** Basketball-specific identity and pose baselines.
- **Limit:** 3x3 with fixed cameras, not 5v5 broadcast.

**6.11 Scorebug OCR and PBP sync.**
- No standalone academic benchmark was found for basketball scorebug OCR. The best published precedent is the OCR-plus-fuzzy-PBP merge stage in Patton et al. 2021 (4.5).
- Several US patents cover scoreboard-region detection for this use (for example, US11568644, US11792441; https://patents.google.com/patent/US11792441). Treat them as engineering references only.
- Practical approach:
  1. Fixed-ROI crop of the broadcast scorebug.
  2. Off-the-shelf OCR (PaddleOCR or a fine-tuned PARSeq) on period, game clock, score and shot clock.
  3. Monotonic alignment (dynamic time warping) to ESPN PBP `clock_display_value` and score.
  4. Replays are detectable as clock freezes or rewinds, or by replay wipes or graphics.

## 7. Off-screen players and missing positions

**7.1 Le, Carr, Yue & Lucey. Data-driven ghosting.**
- **Cite:** Le, H. M., Carr, P., Yue, Y., & Lucey, P. (2017). Data-driven ghosting using deep imitation learning. *SSAC 2017*.
- **Link:** https://www.sloansportsconference.com/research-papers/data-driven-ghosting-using-deep-imitation-learning
- **Finding:** Deep imitation learning produces league-average or team-specific "ghost" defenders, showing where a typical defense would be. The gap between actual and ghost positions gives a counterfactual value of positioning.
- **Method:** Multi-agent RNN policies trained by imitation on tracking (paired with the ICML paper below).
- **Data:** Soccer tracking (STATS/Prozone), per the original (unverified). The method is sport-agnostic.
- **Reuse:** Two uses:
  - A ghost model trained on whatever MSU positions are visible can impute off-screen defenders as "where a typical defender would be."
  - Counterfactual expected points ("how much does the corner shooter raise expected points?") can be computed by replacing the shooter with a ghost non-shooter.
- **Limit:** Needs a large training corpus of complete trajectories, which is unavailable for college.

**7.2 Le, Yue, Carr & Lucey. Coordinated multi-agent imitation learning.**
- **Cite:** Le, H. M., Yue, Y., Carr, P., & Lucey, P. (2017). Coordinated multi-agent imitation learning. *ICML 2017*, PMLR 70.
- **Link:** https://arxiv.org/abs/1703.03121
- **Finding:** Jointly learning a latent role-assignment and per-role policies greatly improves multi-agent imitation over per-player baselines.
- **Method:** Unsupervised role inference (permutation alignment) plus imitation learning.
- **Data:** Team-sport tracking.
- **Reuse:** Role-based latent structure makes models robust to identity uncertainty from broadcast.
- **Limit:** Same data hunger as 7.1.

**7.3 Zhan, Zheng, Yue, Sha & Lucey; Liu, Yu, Zheng, Zhan & Yue. Generative trajectory models and imputation.**
- **Cite:**
  - Zhan, E., Zheng, S., Yue, Y., Sha, L., & Lucey, P. (2019). Generating multi-agent trajectories using programmatic weak supervision. *ICLR 2019*.
  - Liu, Y., Yu, R., Zheng, S., Zhan, E., & Yue, Y. (2019). NAOMI: Non-autoregressive multiresolution sequence imputation. *NeurIPS 2019*.
- **Link:** https://arxiv.org/abs/1803.07612 and https://arxiv.org/abs/1901.10946
- **Finding:** Two results.
  - Hierarchical variational RNNs with weak "macro-intent" labels generate realistic long-horizon basketball trajectories.
  - NAOMI imputes arbitrary missing segments coarse-to-fine, with about 60% lower error than autoregressive imputation.
- **Method:** Hierarchical variational RNN with programmatic macro-goals (Zhan). Non-autoregressive divide-and-conquer decoding plus adversarial training (NAOMI).
- **Data:** NBA tracking (Zhan). Benchmarks reported to include basketball trajectories (NAOMI; basketball use unverified from the abstract).
- **Reuse:** NAOMI-style bidirectional imputation fills off-screen gaps using both the frames before a player leaves the view and after they return. That is exactly the broadcast case.
- **Limit:** Trained on complete NBA data, so they need a pretraining corpus. Domain shift to college remains.

**7.4 Omidshafiei et al. Graph Imputer (off-screen in broadcast).**
- **Cite:** Omidshafiei, S., Hennes, D., Garnelo, M., et al. (2022). Multiagent off-screen behavior prediction in football. *Scientific Reports*, 12, 8638. Preprint: Time-series imputation of temporally-occluded multiagent trajectories, arXiv:2106.04219.
- **Link:** https://arxiv.org/abs/2106.04219
- **Finding:** A bidirectional graph-network variational model imputes trajectories of players outside a simulated broadcast camera view. It beats specialized baselines and gives distributions, not point estimates.
- **Method:** A graph network (players as nodes) plus a variational autoencoder (VAE), conditioned on past and future visible observations. A projective camera module simulates the broadcast field of view during training.
- **Data:** Premier League full tracking with simulated camera occlusion.
- **Reuse:** The best template. The trick of simulating broadcast occlusion on full tracking lets the model be trained on public NBA tracking (2015–16 SportVU) and applied to MSU broadcast. Distributional output lets expected points carry uncertainty.
- **Limit:** Soccer. Basketball cuts and replays create full-frame gaps, not just partial views.

**7.5 Choi et al. MIDAS; Kim et al. ball-trajectory inference.**
- **Cite:**
  - Choi, H.-J., Kim, H., Lee, M., Jeong, M., Kim, C.-J., Yoon, J., & Ko, S.-K. (2025). Trajectory imputation in multi-agent sports with derivative-accumulating self-ensemble. *ECML/PKDD 2025*. arXiv:2408.10878.
  - Kim, H., et al. (2023). Ball trajectory inference from multi-agent sports contexts using Set Transformer and hierarchical Bi-LSTM. arXiv:2306.08206.
- **Link:** https://arxiv.org/abs/2408.10878 and https://arxiv.org/abs/2306.08206
- **Finding:** Two results.
  - Set-Transformer imputers that jointly predict position, velocity and acceleration, then ensemble physically integrated estimates, beat baselines on accuracy and physical plausibility.
  - Ball location can be inferred from player context.
- **Method:** Set Transformer (permutation-invariant) plus derivative accumulation plus learned ensemble.
- **Data:** Three sports datasets (MIDAS); soccer (ball inference).
- **Reuse:** Permutation-invariant set models handle a variable number of visible players naturally. Physics consistency is useful for speed and fatigue features.
- **Limit:** Not validated on basketball broadcast occlusion.

**7.6 Choi. Training-free off-screen imputation for broadcast.**
- **Cite:** Choi, S. (2026). Training-free off-screen player imputation for broadcast-based spatial football analytics. arXiv:2607.11548.
- **Link:** https://arxiv.org/abs/2607.11548
- **Finding:** A training-free "role-anchored centroid voting" method roughly halves pitch-control error in hidden zones. Ignoring off-screen players biases spatial metrics by about 25 points and can flip analytic verdicts.
- **Method:** Each visible player votes for the team centroid using running role offsets. Hidden players are placed at centroid plus role offset.
- **Data:** Metrica open tracking with simulated viewports, plus two real World Cup broadcast windows.
- **Reuse:** Directly answers "how bad is ignoring off-screen players?" for space metrics. A zero-training baseline that fits a ~35-game regime.
- **Limit:** Errors grow quickly for long occlusions. Soccer formations are more stable than basketball rotations.

## 8. Win probability and segment-level prediction in college basketball

**8.1 Pomeroy. KenPom ratings methodology.**
- **Cite:** Pomeroy, K. (2016, Oct 4). Ratings methodology update. kenpom.com. Also "Ratings explanation" (pre-2014).
- **Link:** https://kenpom.com/blog/ratings-methodology/
- **Finding:** Team strength is expressed as adjusted efficiency margin (AdjEM: points per 100 possessions vs an average D-I team).
  - Offense and defense combine additively.
  - Each game is compared to the national efficiency average on its date.
  - Home court is a flat 3.75 points.
  - Win probability comes from predicted margin.
- **Method:** Iterative opponent adjustment of offensive and defensive efficiency, with recency and game-importance weights, plus a tempo model.
- **Data:** All D-I play-by-play and box scores.
- **Reuse:** The game-level prior. Possessions × (AdjO − AdjD) per segment gives segment-level means for halves and 5-minute blocks. Available via hoopR/cbbdata with a subscription.
- **Limit:** No within-game dynamics, no player availability and no style matchup interactions.

**8.2 Torvik. T-Rank.**
- **Cite:** Torvik, B. T-Rank (barttorvik.com). Methodology summarized by Covers, "Torvik ratings: A guide."
- **Link:** https://barttorvik.com and https://www.covers.com/ncaab/what-are-torvik-ratings
- **Finding:** Adjusted efficiencies similar to KenPom, but recency-weighted: games start losing weight after 40 days, falling about 1% per day to a floor of 60% at day 80. Torvik also publishes player-level splits and game predictions free of charge.
- **Method:** Opponent-adjusted efficiency with recency decay. Garbage-time handling and the GameScript metric are documented on barttorvik.com (details unverified here because the FAQ page could not be fetched).
- **Data:** All D-I play-by-play.
- **Reuse:** A free pregame prior with player-level data. cbbdata exposes it via API (§12).
- **Limit:** Same as 8.1.

**8.3 Pomeroy. In-game win probability.**
- **Cite:** Pomeroy, K. (2012, Sept 4). Win probability for grownups. kenpom.com.
- **Link:** https://kenpom.com/blog/win-probability-for-grownups/
- **Finding:** A per-minute regression on pregame win probability, current margin and possession is well calibrated. The value of possession rises in the last about 40 seconds. Home court was not significant in-game until the final 5 minutes.
- **Method:** Separate logistic-type regressions per minute, with extra end-of-game time slices.
- **Data:** All D-I versus D-I possessions from one season.
- **Reuse:** The template for the half and 5-minute segment layers. Replace "pregame WP" with the market spread (8.5) and add possession-value terms from the EPV layer.
- **Limit:** Underconfident above 98%. No lineup or foul-trouble state.

**8.4 Maddox, Sides & Harvill. Bayesian in-game WP for college basketball.**
- **Cite:** Maddox, J. T., Sides, R., & Harvill, J. L. (2022). Bayesian estimation of in-game home team win probability for college basketball. *JQAS*, 18(3), 201–213. doi:10.1515/jqas-2021-0086.
- **Link:** https://arxiv.org/abs/2204.11777
- **Finding:** A prior that varies with lead and time, blended with a time-decaying pregame probability, matches or beats existing college in-game WP models.
- **Method:** Bayesian beta-binomial-style estimation by (lead, time) cell, plus pregame blending.
- **Data:** NCAA D-I men's seasons 2012–13 to 2019–20.
- **Reuse:** The only peer-reviewed college-specific in-game WP. A good baseline and a template for smoothing sparse state cells.
- **Limit:** No possession or team-specific dynamics.

**8.5 Stern; inpredictable. Score as a random walk, with the spread as prior.**
- **Cite:**
  - Stern, H. S. (1994). A Brownian motion model for the progress of sports scores. *JASA*, 89(427), 1128–1134.
  - inpredictable (2013). NBA in-game win probability.
- **Link:**
  - https://www.stat.berkeley.edu/~aldous/157/Papers/stern.pdf
  - https://inpredictable.com/2013/06/nba-in-game-win-probability.html
- **Finding:** Score difference is well approximated by Brownian motion with drift equal to the spread per unit time. Locally weighted logistic regression on spread, margin, time and possession gives practical in-game WP.
- **Method:** Brownian motion with drift (closed-form WP at any time); LOESS logistic regression.
- **Data:** NBA (Stern also used MLB).
- **Reuse:** The analytic backbone for consistent nested segments. Game, half and 5-minute lines can be derived from one drift and variance, matching how books price derivative lines. Deviations from Brownian motion (for example, end-of-half or foul-game variance) are exactly where segment models can add value.
- **Limit:** Constant variance is false at end of game (intentional fouls) and over pace changes.

**8.6 Kubatko, Oliver, Pelton & Rosenbaum. Possession accounting.**
- **Cite:** Kubatko, J., Oliver, D., Pelton, K., & Rosenbaum, D. T. (2007). A starting point for analyzing basketball statistics. *JQAS*, 3(3).
- **Link:** https://lida.sport-iat.de/dbb/Record/4013456
- **Finding:** Standard definitions of possessions, pace and the Four Factors underpin all per-possession models.
- **Method:** Definitions and estimators.
- **Data:** NBA.
- **Reuse:** Defines possession boundaries in PBP, the unit of the possession layer.
- **Limit:** Possession estimates differ slightly in college because of the 30-second shot clock and the one-and-one free throw (pre-2025 rules apply for older seasons).

## 9. Context effects in college basketball

**9.1 van Bommel, Bornn, Chow-White & Gao. Home-court effects on box-score stats.**
- **Cite:** van Bommel, M., Bornn, L., Chow-White, P., & Gao, C. (2021). Home sweet home: Quantifying home court advantages for NCAA basketball statistics. *Journal of Sports Analytics*, 7(1), 25–36.
- **Link:** https://arxiv.org/abs/1909.04817
- **Finding:** Fouls and free-throw attempts (referee-driven stats) show the largest home effects. Referee bias toward the home team grows with attendance but persists after controlling for it.
- **Method:** Attendance-matched t-tests and quasi-Poisson regressions per stat.
- **Data:** About 141k NCAA games, 2011–12 to 2015–16, Divisions I–III, men's and women's.
- **Reuse:** Use attendance (in the ESPN summary, §12) and the foul/FTA channel as explicit covariates in home-court modeling.
- **Limit:** Observational, at box-score level.

**9.2 Marshall, Locke & Wooten. The COVID no-crowd natural experiment.**
- **Cite:** Marshall, E., Locke, S., & Wooten, J. (2025). The impact of fans on home advantage: Evidence from the Covid-19 pandemic college basketball season. *Applied Economics*. doi:10.1080/00036846.2025.2556040.
- **Link:** https://news.vt.edu/articles/2022/10/cm-COVID-homecourt-2022.html (summary) and https://jadrian.owlstown.net/publications/19081
- **Finding:** With restricted crowds in 2020–21:
  - D-I home win rate fell from 63.2% to 58.9%.
  - Home margin fell from about 4.3 to 3.1 points.
  - The drop was largest in Power-conference versus Power-conference games.
- **Method:** Difference in home advantage across seasons, with conference-tier interactions.
- **Data:** About 7,300 D-I games, 2019–20 and 2020–21.
- **Reuse:** Crowd is roughly a third of home-court advantage, and more in big Power-conference arenas. Relevant to Breslin Center (MSU) and Big Ten road games.
- **Limit:** 2020–21 had other confounds (testing, schedule disruption, empty travel).

**9.3 Pomeroy. Market-implied home court by team.**
- **Cite:** Pomeroy, K. (2018, May 21). Mining point spread data: Home court advantage. kenpom.com.
- **Link:** https://kenpom.com/blog/mining-point-spread-data-home-court-advantage/
- **Finding:** Market home-court advantage (half the difference between home-and-home spreads) averaged about 3.2–3.7 points over 2014–2018. Conference averages ranged from 4.0 (Big 12) to 2.9 (Ivy). Team-level spread is narrow (about 2.5 to 4.5). Hawaii is an outlier, consistent with a travel effect.
- **Method:** Paired spreads compared to model estimates (r = 0.72 for teams with 40+ pairs).
- **Data:** Five seasons of closing spreads.
- **Reuse:** The market already prices team-specific home court. A model gains only by beating it on situational factors such as travel, rest and crowd size.
- **Limit:** Spreads, not outcomes. Includes market bias.

**9.4 Anderson & Pierce. Officiating bias in NCAA basketball.**
- **Cite:** Anderson, K. J., & Pierce, D. A. (2009). Officiating bias: The effect of foul differential on foul calls in NCAA basketball. *Journal of Sports Sciences*, 27(7), 687–694. doi:10.1080/02640410902729733.
- **Link:** https://lida.sport-iat.de/dbb/Record/4016050
- **Finding:** Officials tend to call the next foul on the team with fewer fouls, an "evening-out" tendency. They also favor the home team and call more fouls on the leading team. P(next foul on the visitor) can reach 0.70.
- **Method:** Sequential foul-call modeling.
- **Data:** 365 NCAA games, 2004–05.
- **Reuse:** Foul state is a strong in-game covariate for the segment and possession layers (free-throw rate, bonus timing). Officials' names are in the ESPN summary (`gameInfo.officials`), so crew effects on pace, fouls and totals can be estimated.
- **Limit:** Old sample. Crew-level effects in college are mainly in blogs, for example KenPom on individual referees' foul rates (https://kenpom.com/blog/ted-valentine-hates-to-call-fouls/). No recent peer-reviewed NCAA crew–totals study was found.

**9.5 Travel, time zones and rest.**
- **Cite:**
  - Leota, J., et al. (2022). Eastward jet lag is associated with impaired performance and game outcome in the NBA. *Frontiers in Physiology*, 13, 892681.
  - "Impacts of travel distance and travel direction on back-to-back games in the NBA." *Journal of Clinical Sleep Medicine*, 17(11), 2269–2274 (2021).
- **Link:** https://doi.org/10.3389/fphys.2022.892681 and https://lida.sport-iat.de/ta/Record/4070642
- **Finding:** Two results.
  - Leota et al.: home teams returning from eastward travel lost about 1.3 points of margin and about 6 percentage points of win rate (marginal). Westward travel showed no effect.
  - JCSM study: each additional 500 km of return travel cut win odds by about 4% in back-to-backs.
- **Method:** Multilevel mixed models; logistic regression.
- **Data:** About 11.5k NBA games (2011–2021); NBA back-to-backs (2013–2020).
- **Reuse:** Defines features: direction-aware time-zone shift, distance and days of rest. Big Ten expansion to the West Coast (UCLA, USC, Oregon, Washington) makes these newly relevant for MSU.
- **Limit:** NBA evidence. No rigorous college study was found. A small UNC student poster on 2023 NCAA tournament games found no travel or rest effect on 3P%, but the power was low.

**9.6 Lopez, Matthews & Baumer. Altitude and venue effects.**
- **Cite:** Lopez, M. J., Matthews, G. J., & Baumer, B. S. (2018). How often does the best team win? A unified approach to understanding randomness in North American sport. *Annals of Applied Statistics*, 12(4), 2483–2516.
- **Link:** https://arxiv.org/abs/1701.05976
- **Finding:** Using betting-market data in a state-space model:
  - The NBA is the least random of the four major leagues.
  - Home advantage varies by team.
  - Denver and Utah (altitude) have the largest NBA home edges.
- **Method:** Bayesian state-space model on market-implied probabilities.
- **Data:** About 10 seasons of NBA, NFL, MLB and NHL lines.
- **Reuse:** A method for extracting team strength and home advantage from market odds, ideal for the benchmark side. Altitude matters for Big Ten trips only to Colorado-area non-conference sites; it is mostly irrelevant for MSU.
- **Limit:** Professional leagues only.

## 10. Betting-market efficiency in NCAA basketball

**10.1 Wolfers. Point shaving and the strong-favorite anomaly.**
- **Cite:** Wolfers, J. (2006). Point shaving: Corruption in NCAA basketball. *American Economic Review P&P*, 96(2), 279–283.
- **Link:** https://www.stat.berkeley.edu/~aldous/157/Papers/PointShaving.pdf
- **Finding:** Across 44,120 D-I games, favorites covered 50.01% overall. But favorites of 12 or more points covered only 48.4%, with excess "win but fail to cover" outcomes. Wolfers interprets this as point shaving in about 1% of games.
- **Method:** Distribution of margin relative to the spread, compared to a symmetric benchmark.
- **Data:** D-I spreads, 1989–2005.
- **Reuse:** The large-favorite region is the main documented anomaly in college spreads. Any benchmark should test calibration there separately.
- **Limit:** The interpretation is disputed (10.2).

**10.2 Borghesi, Paul & Weinbach. Asymmetric line-setting explains the anomaly.**
- **Cite:** Borghesi, R., Paul, R. J., & Weinbach, A. P. (2010). Totals markets as evidence against widespread point shaving. *Journal of Prediction Markets*, 4(2), 15–22.
- **Link:** https://ideas.repec.org/a/buc/jpredm/v4y2010i2p15-22.html
- **Finding:** NCAA totals also land just under the line more often than just over, because bettors prefer overs and books shade lines up. The same asymmetric shading of favorites can mimic point shaving.
- **Method:** Distribution tests around closing totals.
- **Data:** NCAA basketball totals.
- **Reuse:** Expect systematic shading toward popular sides (favorites, overs). A model's edge should be measured against de-vigged, shading-aware lines, and closing-line value should be tracked.
- **Limit:** Older data, before the rise of mobile betting.

**10.3 Paul & Weinbach. Bettor preferences and sportsbook pricing.**
- **Cite:** Paul, R. J., & Weinbach, A. P. (2008). Price setting in the NBA gambling market: Tests of the Levitt model of sportsbook behavior. *International Journal of Sport Finance*, 3(3), 137–145. Related: Weinbach & Paul (2009), *International Gambling Studies* 9(1), on national-TV over bias (college football).
- **Link:** https://ideas.repec.org/a/taf/intgms/v9y2009i1p55-66.html
- **Finding:** Two results.
  - Bettors over-bet favorites (especially road favorites) and overs. Fading the public was not reliably profitable in the NBA.
  - In college football totals, an over bias is significant only for nationally televised games.
- **Method:** Bet-percentage data vs outcomes.
- **Data:** About 3,600 NBA games, 2004–07 (bet splits); college football totals.
- **Reuse:** MSU is a heavily televised, high-profile program, a candidate for "public-team" and national-TV over shading. Test this specifically on MSU totals.
- **Limit:** Not NCAA basketball specifically. Small edges.

**10.4 Hickman; Douglas. NCAA tournament market efficiency.**
- **Cite:**
  - Hickman, D. C. (2020). Efficiency in the madness? Examining the betting market for the NCAA men's basketball tournament. *Journal of Economics and Finance*, 44(3), 611–626.
  - Douglas, C. C. (2014). Committee bias and market inefficiency, evidence from the NCAA men's basketball tournament. *Journal of Economic Insight*, 40(2), 1–17.
- **Link:**
  - https://doi.org/10.1007/s12197-020-09507-7
  - https://ideas.repec.org/a/mve/journl/v40y2014i2p1-17.html
- **Finding:** Two results.
  - Hickman: the tournament spread market (1996–2019) is efficient overall, with little seed bias. ACC teams under-cover, especially in the first round.
  - Douglas: the market does not fully correct for seeding-committee bias.
- **Method:** Efficiency regressions and simple-strategy tests.
- **Data:** Tournament spreads.
- **Reuse:** Treat closing lines as near-efficient. Edges, if any, are small and conditional (conference, seed).
- **Limit:** Tournament only. Regular-season and derivative markets are understudied.

**10.5 Simon. Intraday line movement inefficiency (MLB; transferable test design).**
- **Cite:** Simon, J. (2024). Inefficient forecasts at the sportsbook: An analysis of real-time betting line movement. *Management Science*, 70(12), 8583–8611.
- **Link:** https://ideas.repec.org/a/inm/ormnsc/v70y2024i12p8583-8611.html
- **Finding:** Lines overreact, with negatively autocorrelated moves. Weak-form efficiency is rejected, and some simple strategies were profitable.
- **Method:** Opening-to-closing line paths across four books.
- **Data:** 3,681 MLB games.
- **Reuse:** Shows that timing matters. Benchmark against both opening and closing lines, and log line paths (for example, from The Odds API), because a pregame edge may exist only early.
- **Limit:** MLB.

**10.6 Clegg & Cartlidge. Replication caution.**
- **Cite:** Clegg, L., & Cartlidge, J. (2024). Not feeling the buzz: Correction study of mispricing and inefficiency in online sportsbooks. *International Journal of Forecasting*. doi:10.1016/j.ijforecast.2024.06.012.
- **Link:** https://arxiv.org/abs/2306.01740
- **Finding:** A published "profitable" betting strategy depended mostly on one data-error bet. After cleaning, most profits vanished, and post-2020 markets looked more efficient.
- **Method:** Exact replication plus data cleaning and an out-of-sample extension.
- **Data:** Tennis odds.
- **Reuse:** A methodological warning. With about 35 MSU games a season, any "edge" over books will have huge variance. Pre-register the evaluation, use closing-line value and log-loss rather than ROI, and pool across all Big Ten games for power.
- **Limit:** Different sport.

**10.7 Gaps in derivative markets: first half, team totals, player props.**
- No peer-reviewed study of NCAA basketball first-half or quarter lines was found.
- Women's college basketball has used quarters since 2015–16. Men's D-I plays two 20-minute halves, so "quarter lines" for MSU men are book-derived splits, not natural game periods.
- For player props, the only academic work found is NBA-specific: Wornow (2026), a Claremont McKenna senior thesis (https://scholarship.claremont.edu/cmc_theses/4171). It found larger absolute deviations from FanDuel prop lines in states with legal betting.
- College player props are restricted or banned in many US states (state-by-state; verify current rules). Historical NCAA prop data will be sparse and biased toward big games.

## 11. Interpersonal coordination in team sports (ecological dynamics)

**11.1 McGarry, Anderson, Wallace, Hughes & Franks. Sport competition as a dynamical self-organizing system.**
- **Cite:** McGarry, T., Anderson, D. I., Wallace, S. A., Hughes, M. D., & Franks, I. M. (2002). Sport competition as a dynamical self-organizing system. *Journal of Sports Sciences*, 20(10), 771–781.
- **Link:** https://lida.sport-iat.de/twm/Record/4007589
- **Finding:** Dyadic and team contests behave like coupled oscillators with stable states and perturbations (critical moments) that cause phase transitions.
- **Method:** Theoretical framework with squash and team-sport examples.
- **Data:** Squash rallies, illustrative.
- **Reuse:** A framework for defining "momentum" or "critical moments" as phase transitions in coupling. These can be tested against win-probability swings.
- **Limit:** Conceptual. Not predictive.

**11.2 Bourbousson, Sève & McGarry. Space-time coordination in basketball, Parts 1 and 2.**
- **Cite:** Bourbousson, J., Sève, C., & McGarry, T. (2010). Space-time coordination dynamics in basketball. Part 1: Intra- and inter-couplings among player dyads; Part 2: The interaction between the two teams. *Journal of Sports Sciences*, 28(3), 339–347 and 349–358.
- **Link:** https://lida.sport-iat.de/twm/Record/4018269 and https://lida.sport-iat.de/ta/Record/4018270
- **Finding:** Two results.
  - Dyads, especially position-matched attacker–defender pairs, show strong in-phase coupling on the basket-to-basket axis. Same-team wings show anti-phase lateral coupling as the team widens and narrows.
  - Team centroids couple in-phase. The stretch-index difference flips between two stable states on change of possession.
- **Method:** Hilbert-transform relative phase, team centroid and stretch index.
- **Data:** Six game sequences (video-digitized).
- **Reuse:** These are the exact measurable "chemistry" signals:
  - Relative phase between MSU teammates (for example, wing–wing anti-phase).
  - Attacker–defender phase locking, where a lead or lag shows who controls the matchup.
  - Centroid and stretch index, which are robust to a missing player.
- **Limit:** Tiny samples. Needs continuous positions, which off-screen gaps break.

**11.3 Esteves, Araújo, Davids et al. 1v1 attacker–defender dyads.**
- **Cite:**
  - Esteves, P. T., Araújo, D., Davids, K., Vilar, L., Travassos, B., & Esteves, C. (2012). Interpersonal dynamics and relative positioning to scoring target of performers in 1 vs. 1 sub-phases of team sports. *Journal of Sports Sciences*, 30(12), 1285–1293.
  - Esteves, P. T., et al. (2015). Angular relationships regulate coordination tendencies of performers in attacker–defender dyads in team sports. *Human Movement Science*, 40, 264–272.
- **Link:** https://shura.shu.ac.uk/7747 and https://shura.shu.ac.uk/9540/
- **Finding:** Two results.
  - Dyad coordination mode depends on court position relative to the basket and on the dribbler's hand dominance.
  - Successful attackers raise angular velocity and reduce angle variability relative to defender and basket.
- **Method:** Relative phase and angle time series in controlled 1v1 trials.
- **Data:** Small-sided experiments, 4 players, 162 trials.
- **Reuse:** Defines player-vs-player features for the matchup layer from broadcast ball-handler and on-ball defender positions, which are almost always on-screen:
  - Attacker–defender–basket angle
  - Its angular velocity
  - Relative phase
- **Limit:** Laboratory 1v1 experiments, not game data.

**11.4 Duarte, Araújo, Correia & Davids; Travassos et al. Teams as superorganisms; ecological dynamics.**
- **Cite:**
  - Duarte, R., Araújo, D., Correia, V., & Davids, K. (2012). Sports teams as superorganisms. *Sports Medicine*, 42(8), 633–642.
  - Travassos, B., Davids, K., Araújo, D., & Esteves, P. (2013). Performance analysis in team sports: Advances from an ecological dynamics approach. *International Journal of Performance Analysis in Sport*, 13, 83–95.
- **Link:** https://shura.shu.ac.uk/7329 and https://shura.shu.ac.uk/7480
- **Finding:** Team-level collective variables (synchrony, division of labor, communication channels) should be measured rather than only individual actions.
- **Method:** Reviews and frameworks.
- **Data:** Review articles.
- **Reuse:** Justifies team-level synchrony metrics (for example, cluster-phase order parameters) as chemistry features.
- **Limit:** Not linked to outcomes or expected points at scale.

**11.5 Ichikawa, Yokoyama, Ishida & Ichinose. Synchronization and anticipation in basketball.**
- **Cite:** Ichikawa, J., Yokoyama, M., Ishida, S., & Ichinose, G. (2026). Movement synchronization in complex and dynamic team coordination: Relationship with mutual anticipation. arXiv:2606.21009.
- **Link:** https://arxiv.org/abs/2606.21009
- **Finding:** After coaching advice, offensive teammates' relative-phase synchronization rose, with posterior probability of 70% or more, consistent with shared anticipation.
- **Method:** Relative phase plus Bayesian estimation of phase distributions.
- **Data:** 3-on-3 basketball field experiment.
- **Reuse:** A recent, directly basketball, Bayesian relative-phase method that suits small samples.
- **Limit:** Experimental 3x3, with no outcome link.

## 12. Data tooling for college basketball

**12.1 hoopR (SportsDataverse).**
- **Cite:** Gilani, S. et al. hoopR: Access men's basketball play-by-play data. CRAN / SportsDataverse.
- **Link:** https://hoopr.sportsdataverse.org/
- **Finding:** `load_mbb_pbp()` gives D-I men's play-by-play for 2006 to the present. `espn_mbb_pbp()` returns these columns:
  - `coordinate_x`/`coordinate_y` (shot locations when ESPN has them)
  - `athlete_id_1`/`athlete_id_2`
  - `clock_display_value`, `period_number`
  - `wallclock`
  - scores
- **Method:** Wraps ESPN, KenPom (subscription), Torvik, NCAA and Basketball-Reference.
- **Data:** ESPN feeds plus stats.ncaa.org.
- **Reuse:** The primary play-by-play source.
  - `wallclock` timestamps help align PBP to broadcast time.
  - Athlete IDs map to ESPN rosters, jersey numbers and headshots.
- **Limit:**
  - Shot coordinates are missing or approximate in some games.
  - No pass events.
  - Substitution logging is occasionally inconsistent, so validate on-court fives.

**12.2 cbbdata.**
- **Cite:** Weatherman, A. cbbdata (R package plus API; successor to toRvik).
- **Link:** https://github.com/andreweatherman/cbbdata
- **Finding:** About 30 endpoints: Torvik ratings, player and game splits, schedules, game box scores, predictions, NET, and KenPom with a subscription. Updated every 15 minutes in season.
- **Method:** Flask API with an R client. A free key is required.
- **Data:** barttorvik.com, KenPom, NCAA NET.
- **Reuse:** Pregame priors, opponent-adjusted player stats and historical day-by-day ratings for leak-free backtests.
- **Limit:** Depends on a third-party service.

**12.3 CBBpy.**
- **Cite:** CBBpy (PyPI), v2.1.2 (Jan 2025).
- **Link:** https://pypi.org/project/CBBpy/
- **Finding:** A Python ESPN scraper for D-I men's and women's basketball:
  - `get_game_info` (includes referees)
  - `get_game_boxscore`
  - `get_game_pbp` (includes `shot_x`/`shot_y`, shooter and assist)
- **Method:** Scrapes ESPN.
- **Data:** ESPN.
- **Reuse:** A Python-native alternative if the video pipeline is in Python.
- **Limit:** Scraper fragility.

**12.4 ncaahoopR.**
- **Cite:** Benz, L. ncaahoopR (R). Original repository: lbenz730/ncaahoopR.
- **Link:** https://github.com/lbenz730/ncaahoopR
- **Finding:** Play-by-play, rosters, schedules, win-probability charts, assist networks and shot charts from ESPN.
- **Method:** ESPN scraping.
- **Data:** ESPN.
- **Reuse:** Assist networks (3.4) and quick win-probability baselines.
- **Limit:** Maintenance is intermittent.

**12.5 ESPN public JSON endpoints (verified 2026-10-17).**
- Roster: `https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/teams/127/roster` (MSU team id = 127). Per-athlete fields:
  - `jersey`
  - `headshot.href` (populated for about 10 of 15 players in the 2026–27 preseason roster)
  - `position`, `height`, `weight`, `experience`
  - `injuries`
- Game summary: `https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary?event={id}`. Keys:
  - `plays`: each with `coordinate.x/y` for shots, `participants`, `clock`, `period` and `wallclock`
  - `boxscore`
  - `gameInfo.officials`: 3 referees by name
  - `gameInfo.venue` and `gameInfo.attendance`
  - `winprobability`: ESPN's own per-play home WP, a useful baseline
  - `pickcenter` / `odds`: empty for the tested 2025 game, so do not rely on ESPN for historical lines
- Scoreboard: `.../scoreboard?groups=7&dates=YYYYMMDD`. Group 7 is the Big Ten.
- Headshot CDN pattern: `https://a.espncdn.com/i/headshots/mens-college-basketball/players/full/{athlete_id}.png`.
- **Reuse:**
  - Jersey numbers feed jersey-OCR verification (6.8).
  - Headshots seed face or appearance re-ID galleries.
  - Officials enable crew effects (9.4).
  - Attendance enables crowd effects (9.1, 9.2).
  - `wallclock` enables coarse video sync.
- **Limit:** Undocumented API, subject to change. Odds history requires a separate vendor (for example, The Odds API, or archived closing lines from Sports-Reference or covers.com).

**12.6 Injury and availability reports.**
- **NCAA:** In October 2025 the NCAA announced a pilot of public player-availability reports for the 2026 Division I men's and women's tournaments. Reports were due the night before and 2 hours before tip, with statuses "questionable" or "out," administered by HD Intelligence. Source: https://www.ncaa.org/?p=3564 and https://www.legalsportsreport.com/245543/ncaa-to-mandate-injury-reports-for-march-madness-amid-betting-integrity-push/
- **Big 12:** Mandated basketball reports for conference games from 2025–26: the night before and 90 minutes before tip, with statuses available, game-time decision or out. The ACC also announced basketball reports for 2025. Source: https://www.cbssports.com/college-football/news/big-12-to-mandate-player-availability-reports-for-football-basketball-starting-in-2025-26
- **Big Ten:**
  - Football availability reports confirmed since 2023, expanded to four per week for 2026 and published on BigTen.org.
  - No evidence was found of a Big Ten men's basketball availability-report mandate as of October 2026. Verify on BigTen.org before the season.
  - Until confirmed, availability must be inferred from ESPN `injuries` fields, box-score DNPs, beat reporting, and the starting-lineup and substitution PBP.

---

## Ranked: 10 works most useful to this project

1. **Patton et al. (2021), college tracking from broadcast (4.5).** The only published end-to-end NCAA broadcast pipeline: calibration, pose-based tracking, OCR, event detection and PBP fusion. Use it as the architecture blueprint.
2. **Lu, Ting, Little & Murphy (2013), track and identify from broadcast (6.1).** Using PBP lineups as an identity prior turns a hard re-ID problem into choosing among 5 candidates. Highest leverage per line of code.
3. **Cervone, D'Amour, Bornn & Goldsberry (2016), EPV (1.1).** The conceptual core: a ball-handler-indexed macro-state chain with hierarchical pooling across players.
4. **Fernández, Bornn & Cervone (2021), decomposed deep EPV (1.3).** A component decomposition (pass, shot, turnover surfaces) that directly answers configuration questions like the PnR/corner-shooter example.
5. **Omidshafiei et al. (2022), Graph Imputer (7.4).** Simulating broadcast occlusion on full tracking lets the model train on public NBA SportVU and transfer to MSU, giving distributions over off-screen players.
6. **Franks, Miller, Bornn & Goldsberry (2015), defensive matchup HMM (2.1).** Low-parameter "who guards whom" inference that tolerates noise. It is the backbone of the matchup and player-vs-player layers.
7. **Somers et al. (2024), SoccerNet Game State Reconstruction (6.6).** Task definition, GS-HOTA metric and open modular code (sn-gamestate) to adapt to basketball.
8. **Decroos et al. (2019), VAEP (1.4).** Works on event data alone, so it is the right possession-value model for the PBP-first phase before video is reliable.
9. **Stern (1994) plus Pomeroy in-game WP (8.5, 8.3).** A Brownian-drift backbone keeps game, half and 5-minute predictions internally consistent and comparable to how books price derivative lines.
10. **Sha et al. (2020), college broadcast camera calibration (6.2).** Court registration built specifically on college broadcast, the hardest dependency for converting pixels to court coordinates.

Honorable mentions: McQueen et al. (2014) on-ball screens; Koshkina & Elder (2024) jersey OCR; Kono & Fujii (2024) BMOS; Maymin et al. (2013) skills plus-minus; van Bommel et al. (2021) home-court effects; Wolfers (2006) and Borghesi et al. (2010) on market structure.

## 5 biggest open gaps (nothing published for college basketball from broadcast video)

1. **Off-screen imputation for basketball broadcast.** Every off-screen imputation paper (Graph Imputer, MIDAS, Choi 2026) is soccer or uses simulated viewports. No one has quantified how basketball broadcast framing (ball-following zoom, cuts, replays) biases spacing, matchup or EPV estimates, or validated imputation against ground truth in college games.
2. **Possession value (EPV/VAEP-style) for college basketball.** All basketball EPV work uses NBA optical tracking. Patton et al. extract college tracking but evaluate players, not possession value. No public model estimates configuration-conditioned expected points (for example, PnR side plus shooter location plus coverage type) for NCAA play, let alone for one team with about 35 games.
3. **Movement-based chemistry linked to outcomes.** Ecological-dynamics coordination measures (relative phase, centroid and stretch coupling) have never been computed at scale from game broadcast video, nor tied to points per possession, lineup RAPM or win probability in college. Lineup synergy work is all box-score or stint-level and NBA-focused.
4. **Segment-level and derivative-market modeling in NCAA basketball.**
   - No peer-reviewed study tests efficiency of NCAA first-half lines, team totals or player props.
   - None builds 5-minute-segment or half models that use lineup or tactical state.
   - None checks whether video-derived features add information beyond closing lines.
   - Player-prop data for college is legally fragmented and has not been studied.
5. **An open, verified college broadcast tracking dataset and benchmark.** There is no public NCAA broadcast dataset with court homography, 10-player identities, ball and scorebug-synced play-by-play (the analogue of SoccerNet-GSR). Existing basketball sets (DeepSportRadar, SportsMOT, TeamTrack, TrackID3x3) cover arena or fixed cameras, short unlabeled-identity clips, or 3x3. Pairing a small hand-verified MSU set with ESPN rosters, jersey numbers and play-by-play would itself be a publishable contribution.
