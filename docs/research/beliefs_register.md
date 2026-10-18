# Beliefs register

Job C of `coord/prompts/002-claude-code-taxonomy-and-markets.md`. Written 2026-10-17 from three research batches (in-game dynamics; venue, officials and schedule; psychology, narrative and market beliefs). Each belief is a candidate hypothesis for the requirements session. Revised 2026-10-18 after a source-verification pass: dead kenpom.com, harvardsportsanalysis.org and fivethirtyeight.com links replaced by the web.archive.org snapshots read, several verdicts downgraded to match the evidence, and shared measurement definitions added ("How to read"). One-line summary for the requirements session: `coord/requirements_inbox/003-beliefs-and-proximity.md`.

## Why beliefs matter even when they are wrong

A belief does not have to be true to change what happens on the floor or in the market. Three examples from the evidence below:

- **Players and coaches act on beliefs.** After a made shot, NBA shooters take the team's next shot more often, shoot from farther out and make it less often; coaches leave them in after makes and pull them after misses ([Attali 2013, APS summary](https://www.psychologicalscience.org/publications/observer/obsonline/the-cold-truth-about-heating-up-on-the-court.html)). After a made field goal, the defense is about 5 pp more likely to call a timeout in the next 2 minutes ([Lantis & Nesson, NBER WP 26510](https://www.nber.org/system/files/working_papers/w26510/w26510.pdf)). Izzo sits starters with two first-half fouls more than almost anyone ([Hoop Vision](https://hoopvision.substack.com/p/foul-trouble-and-the-auto-bench)). These are measurable behaviours whatever the truth of the belief.
- **Officials may act on beliefs.** Calls track the foul count ("evening up"), the score and the crowd ([Anderson & Pierce 2009](https://lida.sport-iat.de/twm/Record/4016050?lng=en); [van Bommel et al.](https://ar5iv.arxiv.org/html/1909.04817)).
- **Bettors act on beliefs, and books respond.** Bettors pile onto streaking, ranked and televised teams ([Paul, Weinbach & Humphreys 2011](https://ideas.repec.org/a/buc/jgbeco/v5y2011i2p42-56.html); [Humphreys, Paul & Weinbach 2013](http://g.espncdn.com/s/betting/HCB2013.pdf?addata=2014%3Dbettingpapers_Humphreys)). Where that flow moves the price but not the outcome, a mispricing can exist; where the closing line stays unbiased, the belief is "priced away".

So for every belief we record: who holds it, what size they claim, evidence for and against (peer-reviewed first), whether the market prices it, and how we would test it with our own data.

## How to read this register

- **Units.** Metres, centimetres, seconds, m/s, m/s². Court positions use r (m) from the rim centre, per `config/vocabulary_map.yaml`, and θ (degrees) measured from the right baseline at the rim centre, per `config/vocabulary_map.yaml` (e.g. right corner θ ≤ 12°, top of key 80°-100°). Distances from feet-based sources were converted (1 ft = 0.3048 m); miles converted at 1 mile = 1.609 km; km/h converted to m/s. "pp" = percentage points; "PPP" = points per possession; "ATS" = against the spread; "HCA" = home-court advantage.
- **Sources.** Every claim links to a page opened during the research for this task. **(unverified)** means the claim was seen only in a search snippet, a secondary write-up, or a page that could not be opened. **(secondary)** means the primary source was not opened and the figure comes from another opened page that reports it.
- **Test data tiers.** "PBP" = play-by-play (with box scores, schedules and closing lines where stated). "Video/tracking" = our broadcast computer-vision pipeline. "Scoreboard OCR" = reading game and shot clocks from video (`docs/requirements.md`, scoreboard reading).
- **Verdicts.** *Supported*, *mixed*, *not supported*, or *untested* (no adequate study found). A verdict is about the belief as people state it, not about whether an effect of some size exists. A verdict that rests only on evidence from another sport is written *untested in basketball*, with the other-sport result in brackets. Evidence quality is named in the verdict when no peer-reviewed study supports it.
- **Hypothesis IDs.** JEV hypotheses H1 to H10 in `docs/requirements.md` keep their numbers. New proposals are numbered new-1 to new-59 across this register, unique within it (the three research batches each started at new-1; they are renumbered here). The requirements session assigns final numbers. Two existing hypotheses get evidence attached: **H8** (jersey colour) and **H10** (travel and time zones).
- **Shared definitions used by the hypotheses** (added 2026-10-18 after review; cited by ID below).
  - **Run** = net points ≥ 8 for one team within a rolling 120 s game-clock window. **Scoring streak** = consecutive points by one team with no opponent points, recorded in points and in seconds of game clock. Used by new-4, new-5, new-6 and new-7.
  - **Closest-defender distance** = Euclidean distance (m) from the shooter to the nearest defender at the release frame. **Closeout speed** = peak defender speed (m/s) toward the catcher during the 1.0 s after the catch, counted only for a defender starting ≥ 3.0 m from the catcher. Used by new-1, new-2, D1, H5 and new-59; "contest distance" means closest-defender distance.
  - **Transition.** The project stores every analyst definition side by side for each possession (`docs/research/transition_full.md` §5): Synergy (defense not set, no time cutoff), Hoop-Math (shot ≤ 10.0 s after a defensive rebound, ball live throughout), FastScout (possession ends in the first 10.0 s of the shot clock), Hudl InStat (shot within 4-8 s, before the defense is in position; we use ≤ 8.0 s) and the coaching phases (outlet, advance, primary break, secondary break, early offense, flow into the half-court). Any hypothesis that uses "transition" reports its outcome under each stored definition, never one merged flag.
  - **First defender back** = time (s) from the defensive rebound or other change of possession until the first player of the team that lost the ball reaches r ≤ 6.75 m of his own rim, or crosses midcourt (14.33 m from his own baseline), whichever comes first; both times are stored.
  - **Speed and acceleration bands** follow `docs/research/load_thresholds.md` Section 9: primary speed bands 2.0 / 4.0 / 5.0 / 5.83 m/s (high-speed running above 5.0 m/s; sprint above 5.83 m/s); accelerations reported at ±2.0 m/s² (and ±3.0 m/s²) only after the noise-floor test passes, labelled exploratory. The 3.5 m/s² Catapult IMA threshold is a different quantity from a position-derived acceleration and is not used.

### Background that limits every market test

- The closing NCAAB spread is an almost unbiased forecast: across 44,120 D-I games (1989-90 to 2004-05) the favourite covered 50.01%, and forecast errors were roughly normal with SD 10.9 points, except strong favourites (> 12 points, n = 9,244), who covered 48.37%, a statistically significant departure from efficiency that Wolfers reads as possible point shaving (see I2) ([Wolfers 2006, AER](https://www.stat.berkeley.edu/~aldous/157/Papers/PointShaving.pdf)).
- Detecting a 3 pp cover edge (53% vs 50%) at 80% power and two-sided alpha 0.05 needs about 2,180 games; a 2 pp edge needs about 4,900 (binomial normal approximation, computed in the research notes). One MSU season (about 35 games) has a cover-rate standard error of about 8.5 pp. **No market belief can be tested on MSU games alone**; MSU questions need pooled D-I data with MSU as a subgroup or prior.
- In-play: Polymarket NBA order books correct single-market anomalies in a median 3.6 s (75 million snapshots, 173 games; [Cheng, Yang & Zou 2026](https://arxiv.org/abs/2605.00864)). **No peer-reviewed study of in-play basketball pricing of any in-game belief was found.** Our 2025-26 Polymarket and Kalshi minute-level price history (`docs/research/odds_markets_research.md`) would be novel here.

---

# Theme A. Shooting and streaks

## A1. The hot hand (individual shooting streaks)

- **Belief.** A player who has made several shots in a row is more likely to make the next one.
- **Who holds it.** Players, coaches, fans and media almost universally ("near-unanimous belief", [Miller & Sanjurjo 2018](https://arxiv.org/pdf/1902.01265)); bettors at team level.
- **Claimed effect and size.** Implied large by announcers ("he's heating up"); the original 1985 study said zero.
- **Evidence for.**
  - Miller & Sanjurjo (2018, *Econometrica* 86(6): 2019-2047) prove a streak-selection bias: in a finite sequence, the expected difference between the hit rate after 3 hits and after 3 misses is about -8 pp under independence (n = 100, p = .5), even for coin flips. Re-analysing the Gilovich-Vallone-Tversky Cornell shooting data (26 players, about 2,600 shots): GVT's +4 pp (49% vs 45%) is +12 pp above that expectation; with per-player bias correction the average difference goes from +3 to **+13 pp** (SE 4.7 pp, p < .01); 19 of 25 players in the hot-hand direction ([arXiv PDF](https://arxiv.org/pdf/1902.01265); [ar5iv](https://ar5iv.labs.arxiv.org/html/1902.01265)).
  - Miller & Sanjurjo (2021, *European Economic Review* 138): 34 years of NBA Three-Point Contest broadcasts (1986-2020) show "considerable evidence" of hot-hand shooting; effect sizes not on the abstract page ([IDEAS](https://ideas.repec.org/a/eee/eecrev/v138y2021ics0014292121001240.html)).
  - Pelechrinis & Winston (2022, *PLOS ONE*), SportVU 2013-14 and 2014-15 (about 200,000 shots per season; 153 players with at least 1,000 shots), neural-net shot-quality model plus permutation test: at least 24 of 153 players (about 16%) show a significant hot hand at every streak length, with weighted effects of about +1.5 pp after one make up to +5.8 pp after four (authors warn long streaks inflate) ([PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0261890)).
  - Mews & Ötting (2023, *AStA Advances in Statistical Analysis* 107: 313-326), 110,513 NBA free throws, state-space model: hot hand exists but "rather small" ([arXiv](https://arxiv.org/abs/2011.04384)).
  - Bocskocsky, Ezekowitz & Stein (2014, MIT Sloan SSAC; conference paper), 83,000+ NBA shots with optical tracking: players who are outperforming take harder shots (farther, tighter defense); conditional on difficulty, the hot hand is **+1.2 to +2.4 pp** ([Sloan page](https://www.sloansportsconference.com/research-papers/the-hot-hand-a-new-approach-to-an-old-fallacy); [PDF](https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc2208061b_2014_SSAC_The-Hot-Hand-A-New-Approach.pdf)).
  - Lantis & Nesson (NBER WP 26510, rev. 2021; working paper), NBA 2004-05 to 2015-16, more than 500,000 free throws: making the previous free throw raises the next by about 2 pp (2.4 pp within a trip); two straight makes about +3.5 pp; four straight makes about +4.5 pp ([NBER PDF](https://www.nber.org/system/files/working_papers/w26510/w26510.pdf)).
  - Yaari & Eisenmann (2011), more than 300,000 NBA free throws 2005-2010, strong individual-level evidence **(secondary: [Wikipedia, Hot hand](https://en.wikipedia.org/wiki/Hot_hand))**.
  - NCAA commentary: Miller & Sanjurjo cite about +6 pp after three makes from their 2016 working paper, no NCAA sample size given ([Inverse](https://www.inverse.com/article/29553-march-madness-ncaa-tyler-dorsey-hot-hand-oregon-ducks-streak); secondary).
- **Evidence against.**
  - Gilovich, Vallone & Tversky (1985, *Cognitive Psychology*): no positive serial correlation in 76ers field goals, Celtics free throws or the Cornell experiment. The journal page returned 403; content confirmed via Miller & Sanjurjo's re-analysis ([arXiv PDF](https://arxiv.org/pdf/1902.01265)).
  - Lantis & Nesson: no field-goal hot hand; three straight made FGs *lower* the next make probability by 0.6 pp (p < .05) with shot controls ([NBER PDF](https://www.nber.org/system/files/working_papers/w26510/w26510.pdf)).
  - Pelechrinis & Winston: the league-average difficulty-adjusted effect is *negative* ("shooting regression") ([PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0261890)).
  - Koehler & Conley (2003), Three-Point Contest 1994-97: no hot hand **(secondary: [Wikipedia](https://en.wikipedia.org/wiki/Hot_hand))**; later overturned by Miller & Sanjurjo 2021.
- **Behaviour driven by the belief.** Attali (2013, *Psychological Science*), more than 170,000 consecutive-shot pairs, 448 NBA players: after a make, shooters take the next team shot more often, shoot from farther and make it less often; coaches sub out after misses ([APS summary](https://www.psychologicalscience.org/publications/observer/obsonline/the-cold-truth-about-heating-up-on-the-court.html); effect sizes not in the summary). Lantis & Nesson: after a made FG the shooter's next attempt is about 0.24 m farther (about 0.46 m in the regression), about 20 s sooner, he is about 5 pp more likely to take the team's next shot, and the defense is about 5 pp more likely to call timeout within 2 minutes (6 pp after three straight makes) ([NBER PDF](https://www.nber.org/system/files/working_papers/w26510/w26510.pdf)).
- **NCAA gap.** No peer-reviewed NCAA in-game field-goal hot-hand study was found.
- **Does the market price it?** Between-game team streaks: bettors over-bet them, but closing prices stay near unbiased ([Paul, Weinbach & Humphreys 2011](https://ideas.repec.org/a/buc/jgbeco/v5y2011i2p42-56.html); [Paul, Weinbach & Humphreys 2014](https://ideas.repec.org/a/sae/jospec/v15y2014i6p636-649.html)); Camerer (1989, *AER*) found spreads reflect streaks while outcomes do not, too small to exploit ([abstract](https://authors.library.caltech.edu/22148); details **secondary** via [Byrnes & Farinella](https://thesportjournal.org/article/the-effect-of-momentum-on-the-nba-point-spread-market/)). Moskowitz (more than 100,000 contracts): momentum moves prices open-to-close and is reversed by outcomes, too small to beat costs ([NYU Stern PDF](https://w4.stern.nyu.edu/finance/docs/pdfs/Seminars/moskowitz_seminar_paper.pdf)). **In-play pricing of a player's in-game streak: no study found.**
- **How we would test it.** Free-throw streaks: **PBP only**; Miller-Sanjurjo permutation test per player on FT sequences, pooled across Big Ten. Field-goal streaks: **video/tracking** to model shot difficulty (release r in m, closest-defender distance in m, shot-clock s, catch-and-shoot vs pull-up). Behaviour test (strongest for us): after a make vs a miss, change in next-attempt r, defender distance, time-to-shot, and opponent timeout probability (tracking + PBP). Market test: Polymarket price move after a player's 3-make streak vs a no-memory win-probability model (2025-26 on).
- **Proposed hypotheses.** **new-1:** Conditional on tracking-based shot difficulty, a Big Ten player's make probability after 2+ makes differs from after 2+ misses (expect at most 2 pp). **new-2:** After a made shot, the same shooter's next attempt has larger r and a smaller closest-defender distance (m, at release; shared definitions) than after a miss. **new-3:** Opponents call a timeout within 120 s more often after 2+ consecutive MSU makes by one player than after other made baskets.
- **Verdict.** **Mixed.** Real but small in controlled settings and at the line (about +2 pp); in-game field-goal effect near zero or negative once shot difficulty is handled; about 16% of NBA players show one.
- **Addition 2026-10-18.** Measurement-error (Stone 2012) and power (Ritzwoller & Romano 2022) critiques, a power table for new-1 and a pooled D-I free-throw test (new-62): see "Additions 2026-10-18", A1 addition.

## A2. "It's a make-or-miss league"

- **Belief.** Games are decided mainly by whether shots go in, not by strategy, effort or rebounding (Pat Riley's line, per [Pelton, ESPN 2016](https://www.espn.com/nba/insider/story/_/id/15456404/explaning-effects-shot-quality-shot-making-winning-games-nba); body paywalled).
- **Who holds it.** Coaches, media, bettors (as a reason to discount single games).
- **Claimed effect and size.** Shooting dominates outcomes.
- **Evidence for.**
  - Cabarkapa et al. (2024, *Frontiers in Sports and Active Living* 6:1387918), NCAA D-I 2018-19, 5,147 games: 3P% winners 37.8% vs losers 30.9% (d = 0.687); FG% has the largest discriminant coefficient (0.513, 16.8% of explained variance); 3PA nearly identical (22.7 vs 22.1, d = 0.10); model classifies 87.8% of games ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11150523/)).
  - Win-probability decomposition, NBA 2011-2014: shooting 71% of four-factor win-probability movement, turnovers 12%, rebounding 9%, free throws 8% ([inpredictable 2015](https://www.inpredictable.com/2015/02/how-nba-games-are-won.html)), against Oliver's heuristic 40/25/20/15 ([Basketball-Reference](https://basketball-reference.com/about/factors.html)).
  - Three-point shooting is noisy: last season's 3P% explains about 14.5% of this season's variance vs about 70% for FT% (NBA; [The Power Rank 2020](https://thepowerrank.com/2020/07/28/predictability-vs-skill-in-sports-analytics-3-point-shooting/)). Pomeroy's estimate that offense controls about 83% of 3P% accuracy (home edge in 3P% +0.7 pp) ([KenPom 2015, "Offense vs. Defense" summary table, archived](https://web.archive.org/web/20190824065637/https://kenpom.com/blog/offense-vs-defense-block-percentage/); also reported by [Gasaway 2018](https://johngasaway.com/2018/02/27/is-uks-perimeter-d-good-or-lucky/)).
- **Evidence against / nuance.** Shot *quality* is partly controllable (selection, defense), so "make or miss" overstates luck; Gasaway cites Pomeroy's "Boeheim exception": elite interior defense can lower opponent 3P% by forcing overmatched offenses into tough threes. He notes it did not appear for MSU in 2018 Big Ten play: 39.9% 2P% allowed, 33.8% 3P% allowed (about average) ([Gasaway](https://johngasaway.com/2018/02/27/is-uks-perimeter-d-good-or-lucky/)). No peer-reviewed study separates shot quality from shot making in NCAA.
- **Evidence quality.** Winner/loser contrasts (Cabarkapa et al.) are post hoc and partly circular: winning teams by definition scored more, so their higher FG% is partly the outcome restated. The 71% shooting share is from an NBA blog (inpredictable). Neither source separates shot-making from shot quality, which is what the belief claims.
- **Does the market price it?** Pre-game markets price team shooting ability; whether they over-weight a team's recent hot or cold 3P% was not found for NCAA.
- **How we would test it.** PBP for make/miss; **video/tracking** for expected make probability per shot (r, θ, defender distance in m, shot type). Decompose each MSU game margin into shot-quality margin (expected points) and shot-making margin (actual minus expected). Market part: **PBP + lines**.
- **Proposed hypotheses.** **new-9:** In MSU games, the shot-making residual (actual minus tracking-expected points) explains more of game margin than the shot-quality margin does. **new-10:** Closing spreads do not over-react to a team's 3P% in its previous 3 games (ATS result on prior 3P% residual).
- **Verdict.** **Supported descriptively** (shooting margin tracks results); the causal "make-or-miss" reading is **untested** in NCAA, and the "luck" reading is overstated because shot quality is partly controlled.
- **Addition 2026-10-18.** NBA precedent for the quality/making split (Chang et al. 2014 ESQ and EFG+; ESPN qSQ and qSI) and the aligned inputs for new-9: see "Additions 2026-10-18", A2 addition.

## A3. "Live by the three, die by the three" (three-point variance)

- **Belief.** Teams that take many threes have more volatile results; underdogs should shoot more threes to raise upset odds.
- **Who holds it.** Coaches, media, bettors (upset picks), bracket analysts.
- **Claimed effect and size.** Large swings in outcome variance.
- **Evidence for.** Skinner & Goldman (2015, handbook chapter, arXiv review): 10 twos at 60% vs 10 threes at 40% have the same mean (12 points) but variance 9.6 vs **21.6 points²**; underdogs should raise variance, favourites lower it ([arXiv abstract](https://arxiv.org/abs/1512.05652); [PDF](https://arxiv.org/pdf/1512.05652)). Endgame model work (Kenter, Rice) implies late-game choices matter more than full-game volume ([PDF](https://supermariogiacomazzo.github.io/STOR538_WEBSITE/Articles/Basketball/Basketball_Kenter.pdf)).
- **Evidence against.** Simulation with equal expected value per shot: raising 3PA share from 20% to 60% lifts a 5-point underdog only from 36.7% to **37.5%** win probability ([Binomial Basketball](https://www.binomialbasketball.com/p/the-nbas-3-point-variance-lie); single non-peer-reviewed blog simulation). (Context, not a variance test: in NCAA D-I 2018-19 mean 3PA did not separate winners from losers, d = 0.10 ([Cabarkapa et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11150523/)); this concerns the mean, not outcome variance, so it neither supports nor refutes the belief.)
- **Does the market price it?** No study found of whether spreads or totals price higher variance for high-3PA teams (would show in ATS-margin dispersion, not the mean).
- **How we would test it.** **PBP + lines.** Per team 3PA rate vs game-to-game SD of (margin minus closing spread); upset rate for high-3PA vs low-3PA underdogs at the same spread.
- **Proposed hypotheses.** **new-14:** The SD of (actual margin minus closing spread) is larger when the underdog's 3PA rate is in the top quartile. **new-15:** Big Ten underdogs with high 3PA rates cover at the same rate as other underdogs.
- **Verdict.** **Mixed:** true in principle (Skinner & Goldman); size at realistic shot mixes estimated only by one blog simulation.

## A4. Free throws under pressure (clutch choking)

- **Belief.** Players miss more free throws in high-pressure moments; some players are "clutch".
- **Who holds it.** Everyone; coaches choose whom to foul and who gets the ball.
- **Claimed effect and size.** Large choking for weak shooters.
- **Evidence for.**
  - Cao, Price & Stone (2011, *J. Sports Economics* 12(3): 231-252), NBA 2002-03 to 2009-10: 5-10 pp worse in the final seconds of close games; last 15 s, **-8.8 pp down 1, -6.3 pp down 2**; about -5 pp on the final shot of a trip when up 1-2; larger for weak shooters (a 60% shooter about -15 pp); no effect when tied ([PDF](http://media.clemson.edu/economics/gated/data/golf/Performance%20Under%20Pressure%20NBA%20Journal%20of%20Sports%20Economics-2011-Zheng%20Cao-231-52.pdf)).
  - Toma (2017, *J. Sports Economics* 18(6): 539-559), more than 2 million free throws (ESPN PBP 2002-2013): final 30 s of tight games, **NCAA men -2.09 pp**, NCAA women -2.25 pp (n.s.), NBA -3.11 pp, WNBA -5.81 pp; college men who later turned pro dropped 6 pp more ([Warwick repository](https://wrap.warwick.ac.uk/168616/)).
  - Böheim, Grübl & Lackner (IZA DP 11761, 2018; working paper), NBA 2007-08 to 2015-16, weather-instrumented attendance: home FT success falls 7.5 pp when attendance rises 10 pp of capacity ([IZA PDF](https://docs.iza.org/dp11761.pdf)).
  - Goldschmied, Raphaeli & Morgulev (2023): NCAA FT% falls significantly in the last minute for attempts with no preceding timeout (chi2(1) = 69.34, p < .001); attempts after a timeout show no such pattern (chi2(4) = 2.28, p = 0.70) ([abstract](https://lida.sport-iat.de/ta/Record/4085006); numbers **secondary** via [The Upside](https://www.theupside.us/p/upside-studies-icing-the-shooter); journal full text 403).
- **Evidence against / caveats.** Late-game selection: leading teams get their best shooters to the line, trailing teams foul the worst ([Sabin Analytics](https://sabinanalytics.com/blog/2024/02:28:do-college-crowds-affect-free-throws/)). Persistence of "clutch skill" lacks support (a Berkeley honours-thesis replication, **unverified**, not opened).
- **Does the market price it?** Not studied directly.
- **How we would test it.** **PBP only.** FT% by time remaining × margin, shooter fixed effects, first vs second attempt, and who was fouled (selection).
- **Proposed hypothesis.** **new-16:** Big Ten FT% in the last 30 s of games within 3 points is 2-5 pp below the shooter's season FT% (shooter-adjusted).
- **Verdict.** **Supported**, small in NCAA men (about 2 pp), larger for weak shooters and in the NBA.

## A5. "Icing" the free-throw shooter with a timeout

- **Belief.** An opposing timeout right before late free throws makes the shooter more likely to miss.
- **Who holds it.** Coaches (common practice), broadcasters, fans.
- **Claimed effect and size.** Unquantified; assumed meaningful.
- **Evidence for.** Goldschmied, Raphaeli & Morgulev (2023, *Psychology of Sport and Exercise* 68: 102440), NCAA, 99,026 free throws, 22,224 games, 2007-08 to 2019-20: in the last 5 minutes (margin at most 5), FT% after any timeout 67.8% vs 69.5% without (significantly lower: "time extension before execution undermined performance") ([abstract](https://lida.sport-iat.de/ta/Record/4085006); numbers via [The Upside](https://www.theupside.us/p/upside-studies-icing-the-shooter)).
- **Evidence against.** Same study, last minute (margin at most 3): opposing-coach timeout (icing) 70.6% (n = 1,428) vs no timeout 70.3% (n = 23,575), p = 0.80; own-coach timeout 67.5% (n = 268) ([The Upside](https://www.theupside.us/p/upside-studies-icing-the-shooter)). Caveat: the sample window for the no-timeout group is not stated in this secondary source and may not be limited to the same last-minute window; the reported chi-square N (33,543) does not equal 1,428 + 23,575 = 25,003, and the summary's own last-minute share (42.30% of attempts) is not reconciled with the group sizes. Treat the icing-vs-no-timeout comparison as secondary and partly unverified until the tables of *PSE* 68: 102440 are read. NBA: *Scorecasting* found no difference, about 76% either way ([Freakonomics summary](https://freakonomics.com/2011/11/football-freakonomics-why-even-ice-a-kicker)).
- **Does the market price it?** Not studied.
- **How we would test it.** **PBP only** (timeout, caller, FT result), pooled Big Ten, shooter-adjusted.
- **Proposed hypothesis.** **new-11:** In the last 60 s of games within 3 points, FT% after an opposing timeout equals FT% with no timeout (shooter-adjusted).
- **Verdict.** **Not supported** (icing specifically); a general late-stoppage dip exists.

---

# Theme B. Momentum, runs and game state

## B1. Momentum and runs ("basketball is a game of runs")

- **Belief.** Scoring runs reflect a real psychological or tactical state; a team on a run is more likely to keep scoring.
- **Who holds it.** Broadcasters, coaches (timeout behaviour), players, fans, live bettors.
- **Claimed effect and size.** Implied large ("weather the run").
- **Evidence for (small).**
  - Weimer, Steinert-Threlkeld & Coltin (2023, *J. Sports Analytics* 9(2): 117-132), NBA, TV timeouts as a natural experiment (timing set by the clock): a TV timeout causes an **11.2% decline** in subsequent points by the team with momentum ([abstract](https://lida.sport-iat.de/dbb/Record/4082590?lng=en)). This implies some persistence that the break interrupts.
  - A 2025 *American Statistician* state-space study (NBA 2015-16 to 2018-19) reportedly finds a weak positive team-level effect **(unverified: publisher page 403; search snippet only)**.
  - Qiu et al. (2024, *Frontiers in Psychology*), CBA 2021-22, 372 games: momentum (net +6 in 96 s) occurred 1,373 times for winners vs 710 for losers ([Frontiers](https://www.frontiersin.org/articles/10.3389/fpsyg.2024.1412840/full)); close to tautological, not evidence of persistence.
- **Evidence against (runs are mostly chance).**
  - Schilling (2019, arXiv), 2016-17 NBA (1,230 games): expected season-average longest field-goal run under no momentum **5.12**, observed **5.17** ([PDF](https://arxiv.org/pdf/1903.08716)).
  - Gabel & Redner (2012, arXiv; journal venue **unverified**), 6,087 NBA games: scoring is an **anti-persistent** random walk (probability the same team scores next q = 0.348), mean 30.39 s between scores, exponentially distributed gaps with "essentially no memory"; a weak restoring force (leader's scoring rate falls 0.0022 per point of lead) ([PDF](https://arxiv.org/pdf/1109.2825)).
  - Clauset, Kogan & Redner (2015, *Phys. Rev. E* 91: 062815), ~40,000 games and 1.25 million scoring events across four professional or semi-professional sports (NBA among them): a random-walk model fits lead changes ([PDF](https://arxiv.org/pdf/1503.03509)).
  - Morgulev, Azar & Bar-Eli (2019, *J. Economic Psychology* 75), about 900 NBA tied games after 4th-quarter comebacks: comeback momentum does not predict overtime wins **(unverified: search abstract only; university page redirected)**.
- **Does the market price it?** Moskowitz: pre-game markets overreact to momentum and the move is reversed by outcomes ([NYU Stern PDF](https://w4.stern.nyu.edu/finance/docs/pdfs/Seminars/moskowitz_seminar_paper.pdf)). In-play: no peer-reviewed basketball study; Choi & Hui (2014) on exchange over/under-reaction is cited elsewhere **(unverified)**.
- **How we would test it.** **PBP only.** (a) Schilling-style longest-run test on Big Ten games against a possession-level null with team strengths and built-in anti-persistence. (b) Weimer-style natural experiment with NCAA media timeouts (first dead ball under 16:00, 12:00, 8:00, 4:00 each half, per the [NCAA timeout paper](https://www.causeweb.org/usproc/sites/default/files/usresp/2019-1/An%20Examination%20of%20Timeout%20Value,%20Strategy,%20and%20Momentum%20in%20NCAA%20Division%201%20Mens%20Basketball.pdf)). (c) In-play: Polymarket price move after a 10-0 run vs a no-memory model (**PBP + prediction-market prices**).
- **Proposed hypotheses.** **new-4:** Longest scoring streaks and runs (shared definitions: streak in points and s; run = net ≥ 8 points within 120 s) in Big Ten games are no longer or more frequent than an anti-persistent random-walk null with team strengths predicts. **new-5:** A media timeout during an opponent run (net ≥ 8 points within a rolling 120 s; shared definition) reduces the running team's scoring over the next 180 s relative to matched uninterrupted runs. **new-6:** In-play prediction-market prices overreact to runs (shared definition; price change exceeds model-implied change and partly reverses within 5 minutes of game time).
- **Verdict.** **Mixed, leaning not supported.** Runs are about what chance produces; one causal NBA study finds a small persistence that a break interrupts.

## B2. Timeouts stop runs

- **Belief.** Calling a timeout during an opponent's run stops it.
- **Who holds it.** Coaches, broadcasters, fans.
- **Claimed effect and size.** "Stop the bleeding"; unquantified.
- **Evidence for.**
  - NCAA D-I (student paper, not peer-reviewed; author attribution to Luke Benz **unverified**), 10,409 games (2016-17, 2017-18) + 3,625 test games (2018-19), ESPN PBP, mixed-effects model: teams score **1.5-2.2 points better in the 5 minutes after a called timeout than in the 5 minutes before** (pre/post comparison; open to regression to the mean, the same design criticised below for the EuroLeague data); media timeouts little effect; pre-halftime "use it or lose it" timeouts worth 33-50% of earlier ones ([PDF](https://www.causeweb.org/usproc/sites/default/files/usresp/2019-1/An%20Examination%20of%20Timeout%20Value,%20Strategy,%20and%20Momentum%20in%20NCAA%20Division%201%20Mens%20Basketball.pdf)).
  - EuroLeague 2021-22 to 2023-24, more than 4,300 timeouts: net deficit -3.74 points in the minute before vs -1.20 in the minute after (narrows, does not reverse) (Carta, Favero & Maver 2026, *J. Sports Analytics* 12; [SDA Bocconi summary](https://www.sdabocconi.it/en/sda-bocconi-insight/knowledge/in-basketball-timeouts-stop-the-game-but-not-momentum/)).
  - CBA (Qiu et al. 2025, *Frontiers in Psychology*), 4,051 timeouts, 1,235 games: momentum rose after timeouts when trailing (n = 3,141); no regression-to-mean control ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12554673/)).
- **Evidence against.**
  - Selection: more than 95% of EuroLeague timeouts were called during a negative run, so regression to the mean alone predicts improvement ([SDA Bocconi](https://www.sdabocconi.it/en/sda-bocconi-insight/knowledge/in-basketball-timeouts-stop-the-game-but-not-momentum/)); "effective timeouts" add nothing to a season win model.
  - Gibbs, Elmore & Fosdick (arXiv 2011.11691), NBA 2017-18 and 2018-19, 4,684 runs (834 with timeout), genetic matching: ATT = **-0.35** (SE 0.07) on integrated score difference over the next minute, i.e. slightly harmful; sensitive to unmeasured confounding at Γ ≈ 1.5 ([ar5iv](https://ar5iv.labs.arxiv.org/html/2011.11691)).
  - Saavedra, Mukherjee & Bagrow (2012, arXiv), more than 3,000 NBA games: timeout effect non-significant in 74-79 of 90 team-seasons; negatively correlated with coach experience (r = -0.24 to -0.29) ([ar5iv](https://ar5iv.arxiv.org/html/1205.1492)).
- **Does the market price it?** Not studied.
- **How we would test it.** **PBP** for timing, type (called vs media), caller, outcomes; matched runs with and without a timeout plus a "no timeouts left" control. **Video** adds what changed after the timeout (lineup, defensive scheme, set called), which links to JEV set recognition.
- **Proposed hypotheses.** **new-7:** Opponent called timeouts during MSU runs (shared definition: net ≥ 8 points within a rolling 120 s) do not reduce MSU's net points over the next 180 s relative to matched runs without a timeout. **new-8:** MSU's after-timeout possessions score more PPP than MSU's average half-court possession (PBP + video set labels). After-timeout possession = the first MSU possession starting at the restart after a called (non-media) timeout, with the inbound or live ball within 5 s of the restart.
- **Verdict.** **Mixed.** Naive before/after gains are inflated by regression to the mean; NBA causal estimate slightly negative; NCAA pre/post estimate positive but not adjusted for regression to the mean (single non-peer-reviewed student paper).
- **Addition 2026-10-18.** Peer-reviewed NCAA evidence (Mace et al. 1992; Roane et al. 2004) and the regression-to-the-mean critique (Permutt 2011; Assis et al. 2020): see "Additions 2026-10-18", B2 addition.

## B3. Being slightly behind at halftime helps

- **Belief.** Trailing by a point at the half motivates a team to win.
- **Who holds it.** Coaches, media; popularised by the Berger & Pope study.
- **Claimed effect and size.** About +5 pp win probability.
- **Evidence for.** Berger & Pope (2011, *Management Science*), NCAA 2005-2008, 6,572 games within 10 at half: teams down 1 expected to win about 46% won **51.3%**, outscoring opponents by 1.2 points in the second half, half of it in the first 4 minutes ([Wharton Knowledge](https://knowledge.wharton.upenn.edu/article/is-this-madness-how-losing-by-just-a-little-can-help-a-team-or-company-win/); [also](https://knowledge.wharton.upenn.edu/?p=8034)). Gelman criticised the model dependence **(unverified, snippet)**.
- **Evidence against.** Klein Teeselink, van den Assem & van Dolder (2023, *Management Science* 69(1): 513-532): the effect appears only in NBA games inside Berger & Pope's sample period; **absent for NCAA**, other NBA periods and WNBA; meta-analysis cannot reject zero ([VU repository](https://research.vu.nl/en/publications/does-losing-lead-to-winning-an-empirical-analysis-for-four-sports-2/)).
- **Does the market price it?** Not studied.
- **How we would test it.** **PBP + second-half lines** (The Odds API since 2023).
- **Proposed hypothesis.** **new-22:** Big Ten teams trailing by 1-2 at half do not beat the second-half line more often than teams leading by 1-2.
- **Verdict.** **Not supported** (failed replication for NCAA).

## B4. "No lead is safe"

- **Belief.** Big comebacks are common; leads are never safe.
- **Who holds it.** Broadcasters, fans; coaches who keep starters in.
- **Claimed effect and size.** Unquantified. Bill James built a "safe lead" rule for college basketball: (lead - 3, ± 0.5 for possession)² = seconds; safe if above seconds remaining ([Slate 2008](https://www.slate.com/articles/sports/sports_nut/2008/03/the_lead_is_safe.html)).
- **Evidence for.** Gabel & Redner: a weak restoring force (the leader coasts), which makes comebacks slightly more likely than a pure random walk ([PDF](https://arxiv.org/pdf/1109.2825)).
- **Evidence against.** Clauset, Kogan & Redner (2015): James' rule is "quite conservative"; across all scaled lead sizes the random-walk model overestimates the observed safe-lead probability by at most 6.2%; as a model example for evenly matched teams (random-walk formula, z ≈ 1.163), a 10-point lead is 90% safe with 7.87 minutes left (not an observed NBA rate) ([PDF](https://arxiv.org/pdf/1503.03509)).
- **Does the market price it?** Implicitly via in-play win probability; no study of mispricing found.
- **How we would test it.** **PBP only.** Win-probability calibration for Big Ten (lead, time, possession) states.
- **Proposed hypothesis.** **new-24:** Big Ten comeback rates from given (lead, time) states match a random-walk model with a restoring force.
- **Verdict.** **Not supported** as stated: leads are about as safe as a random walk predicts, and safer than James' rule implies.

---

# Theme C. Possession, rebounding and late-game tactics

## C1. The opening tip matters

- **Belief.** Winning the opening jump ball gives a real edge.
- **Who holds it.** Coaches and players (jump-ball sets), bettors (first-team-to-score, first-basket props), fans.
- **Claimed effect and size.** "We're up a possession."
- **Mechanics (NCAA).** The possession arrow goes to the team that *loses* the tip, so the winner gains at most a partial possession over the game ([Wikipedia, Jump ball](https://en.wikipedia.org/wiki/Jump_ball)). An NBA possession is worth "around half a point" in one win-probability model ([Maymin et al. 2012 PDF](https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc220807d3_SSAC11%20-%20Maymin%20Maymin%20and%20Shen%20-%20Early%20Foul%20Trouble%20-%20IJSF%202012.pdf)).
- **Evidence for.** NCAA women 2025-26, 4,466 D-I games: tip winners 57.4% vs pregame expectation 56.2%, **+1.2 pp** (95% CI about 0.1 to 2.4); heavy underdogs +3.4 pp (CI 1.4-5.5); correlational ([Her Hoop Stats](https://herhoopstats.substack.com/p/winning-the-tip)). NBA 2000-2021, more than 27,000 tips: tip winners won **52.8%** and scored first 64% (student research; a 5.6 pp regression figure is not reconciled) ([Dickinson College](https://www.dickinson.edu/news/article/6001/dickinson_research_reveals_a_new_take_on_nba_tipoffs)). McCartney's NCAA men's analysis (19,096 games, about +4 pp) **(unverified: 404)**.
- **Evidence against.** NBA, 888 games: tip winners 52.5%, mostly a home effect (home tip winners 62%, away 43%) ([82games](https://www.82games.com/random14.htm)). Tip winners are already favoured (taller teams), so raw rates overstate.
- **Does the market price it?** First-team-to-score props are typically priced near 50-50 plus vig, largely ignoring jump-ball skill ([Action Network](https://www.actionnetwork.com/nba/finding-edge-random-prop-nba-first-team-to-score)); first FG after a tip win "close to 65%" (unsourced, [BestOdds](https://www.bestodds.com/odds/nba/fb)).
- **How we would test it.** **PBP + pregame line**: tip winner's win rate and ATS margin vs closing-line expectation. **Video**: jumper identity, reach, tip direction. Race-to-5/10 markets on Kalshi and Polymarket (noted in `odds_markets_research.md`).
- **Proposed hypotheses.** **new-12:** The tip winner's final margin exceeds the closing spread by less than 1 point on average (Big Ten). **new-13:** First-team-to-score and race-to markets underprice the tip winner when one jumper has a reach advantage, defined as standing reach difference ≥ 8 cm (roster or combine data), or video-measured peak hand height at the tip ≥ 10 cm higher (tracking, cm); tip direction stored as θ (degrees).
- **Verdict.** **Weakly supported, tiny:** at most a partial possession under the NCAA arrow (< 1 possession, < 0.5 point by an NBA model); no peer-reviewed or verified men's NCAA estimate.

## C2. "The team that wins the rebounding battle wins the game"

- **Belief.** Out-rebounding the opponent is a primary driver of winning. Core to MSU's identity: Izzo's "War" drill; MSU led the nation in total rebounding percentage in 2008-09 (56.8%) and 2009-10 (56.3%) ([Grantland, Koremenos 2014](https://grantland.com/the-triangle/war-tom-izzo-michigan-state-spartans-rebounding/)).
- **Who holds it.** Coaches (especially MSU), broadcasters, fans.
- **Claimed effect and size.** Primary.
- **Evidence for.** NCAA D-I 2018-19 (5,147 games): winners **27.1 DRB vs 23.2** (d = 0.83); TRB 37.0 vs 33.2 ([Cabarkapa et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11150523/)). NCAA women (season not stated; article dated 1 Feb 2023): rebound margin explains about 35% of point differential, DRB rate alone about 12% ([Her Hoop Stats](https://herhoopstats.substack.com/p/more-rebounds-more-wins-not-always)). NBA/WNBA 2021-23: DRB difference correlates with win% (WNBA r ≈ 0.69 without an outlier) ([Berkeley student article](https://sportsanalytics.studentorg.berkeley.edu/articles/a-tale-of-two-rebounds.html)).
- **Evidence against.** Same NCAA data: **ORB identical (9.9 vs 9.9, p = 0.86)**; discriminant coefficient for ORB 0.002 (0.6%) vs DRB 0.372 (12.2%) ([Cabarkapa et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11150523/)). Defensive rebounds come from opponent misses, and winners' opponents shoot worse, so raw rebound margin partly re-measures shooting (reasoning from the same table); rates are the right measure ([Basketball-Reference](https://basketball-reference.com/about/factors.html)). Weights: Oliver about 20%; win-probability model 9% ([inpredictable](https://www.inpredictable.com/2015/02/how-nba-games-are-won.html)).
- **Crash vs get back.** Wiens, Balakrishnan, Brooks & Guttag (2013 MIT SSAC), NBA 2011-12 SportVU: crashing more after missed jumpers raises net value from -0.62 to -0.45 PPP (+0.17 PPP); early retreat can more than halve offensive-rebound probability; early threat neutralisation matters more than getting back (moving the mean distance to the nearest early threat from 1.83 m to 3.66 m ≈ +0.06 PPP allowed). Their definitions: "inside" within 2.44 m of the basket, "outside" beyond 10.06 m, "crash" = moving at least 1.52 m toward the basket ([Sloan page](https://www.sloansportsconference.com/research-papers/to-crash-or-not-to-crash); [PDF](https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc220807a3_SSAC13%20-%20To%20Crash%20or%20Not%20To%20Crash.pdf)). Top-5 NBA offensive-rebounding teams 2008-2013 averaged about 13th-17th in transition defense, no clear trade-off ([Lowe, Grantland 2013](https://grantland.com/the-triangle/party-crashers-debunking-the-myths-of-offensive-rebounding-and-transition-defense/)).
- **Does the market price it?** Team ratings embed rebounding rates; no evidence of mispricing.
- **How we would test it.** **PBP** for ORB% and DRB% and a four-factor margin decomposition with rates. **Video/tracking** for crash and retreat counts at release (r from rim in m), first-defender-back time (s; shared definition: reach r ≤ 6.75 m of own rim or cross midcourt, 14.33 m from own baseline), and Wiens metrics; links to Job D (transition) and the getting-back requirements.
- **Proposed hypotheses.** **new-17:** In MSU games, raw rebound count adds no predictive power for the result once eFG% margin and turnover margin are controlled; ORB% margin adds some. **new-18:** Each additional MSU player crashing (moving at least 1.5 m toward the rim within 1.0 s of release) raises MSU ORB% and changes opponent transition PPP, reported under every stored definition: opponent PPP on possessions with a shot ≤ 10.0 s after the defensive rebound (Hoop-Math), possessions ending in the first 10.0 s of the shot clock (FastScout), shots ≤ 8.0 s (Hudl InStat), Synergy-style defense-not-set and the coaching phases (`transition_full.md` §5); also MSU first-defender-back time (s). Net effect per possession.
- **Verdict.** **Mixed.** Defensive-rebound margin tracks winning but largely mechanically; offensive-rebound margin does not separate winners in NCAA.

## C3. Bench a starter in foul trouble

- **Belief.** A starter with two first-half fouls (NBA: "Q+1") must sit to avoid fouling out.
- **Who holds it.** Coaches (near-universal), broadcasters; analysts often argue the opposite.
- **Claimed effect and size.** Avoids losing the player late.
- **Evidence for.** Maymin, Maymin & Shen (2012, *Int. J. Sport Finance* 7: 324-339), NBA 2006-07 to 2009-10 (about 4,700 games): Q+1 benching is generally right **early in games** when option value or bench quality is high; a tied game with no foul-troubled starters gives the home team 62% at tip, **58%** with one foul-troubled starter on court, **53%** with two; the effect fades to zero by the end; coaches pull 72% of starters at Q+1 ([Sloan page](https://sloansportsconference.com/research-papers/how-much-trouble-is-early-foul-trouble); [PDF](https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc220807d3_SSAC11%20-%20Maymin%20Maymin%20and%20Shen%20-%20Early%20Foul%20Trouble%20-%20IJSF%202012.pdf); [NYU summary](https://engineering.nyu.edu/news/rethinking-foul-trouble)).
- **Evidence against.** Same study: foul-troubled stars should stay in during the 4th quarter; with an average bench only players above WP48 0.164 should stay in. NCAA: starters with two first-half fouls play about 23% of available minutes nationally; strict man-to-man coaches including **Tom Izzo** sit them most; zone-heavy teams 51%. Players already adjust: foul rates per 40 min for 2016 starters were 2.66 with 0 fouls, 2.34 with 1, **1.71 with 2** ([Hoop Vision](https://hoopvision.substack.com/p/foul-trouble-and-the-auto-bench), citing KenPom; **secondary**). No study measures whether NCAA two-foul benching improves winning.
- **Does the market price it?** Not studied.
- **How we would test it.** **PBP only** (fouls per player, substitutions, lineups) plus a win-probability model; matched cases where a two-foul starter sits vs stays.
- **Proposed hypotheses.** **new-19:** An MSU starter who stays in with two first-half fouls commits fouls at a lower rate per 40 min than with 0-1 fouls, and fouls out no more often than a benched starter. **new-20:** Benching a two-foul starter for the rest of the first half lowers MSU's first-half net points relative to matched cases where he stays.
- **Verdict.** **Mixed.** NBA evidence supports early benching in some cases and opposes late benching; NCAA outcomes untested.

## C4. Foul when up 3 late

- **Belief.** Split: "foul to prevent a tying three" vs "never foul, it invites a 3-and-1 or an offensive rebound".
- **Who holds it.** Coaches, analysts, broadcasters.
- **Claimed effect and size.** Either side claims a decisive edge.
- **Evidence for fouling.** Zapata-Hall (arXiv 2402.13289), survey sent to more than 3,100 coaches (163 responses) + NCAA D-I PBP 2010-2022, final 21 s split into 34 game-clock × shot-clock cells: overtime-adjusted win% 87-93% when fouling, 76-94% when not (falls as shot clock runs down); following the cell-by-cell policy gains **1.63 overtime-adjusted win pp**; coaches foul in only 0-18% of opportunities ([PDF](https://arxiv.org/pdf/2402.13289)). Kenter's endgame model: about +10% win probability with a 3-point lead (venue **unverified**) ([PDF](https://supermariogiacomazzo.github.io/STOR538_WEBSITE/Articles/Basketball/Basketball_Kenter.pdf)).
- **Evidence against / small.** NBA: 524 games with a 3-point lead in the final 24 s (2021-22 to 2025-26); with 3-17 s left, fouling 92.0% (n = 143) vs defending 91.7% (n = 381), overtime counted as 50/50; offensive-rebound rate on missed FTs when trailing by 2-3 in the final 10 s over the last two seasons 42% (16/38) vs 10.5% overall; foul rate in the final 10 s over the last two seasons 34.2% (11.5% in a 2010 Synergy analysis) ([Kram, ESPN 2026](https://www.espn.com/nba/story/_/id/48582233/nba-playoffs-2026-foul-3-san-antonio-spurs-portland-trail-blazers-impact)). NCAA D-I 2009-10 to early 2012-13 (KenPom, practitioner): trailing team gains possession down 3 with 5-12 s left; foul 92.0% (n = 138) vs defend 93.5% (n = 676), overtime counted as 50/50 ([KenPom 2013, archived](https://web.archive.org/web/20201217072842/https://kenpom.com/blog/yet-another-study-about-fouling-when-up-3/)).
- **Does the market price it?** Would require in-play reaction within seconds; not studied.
- **How we would test it.** PBP for situations; **shot clock is not in most PBP**, so **scoreboard OCR from video** is needed to place cases in game-clock × shot-clock cells.
- **Proposed hypothesis.** **new-21:** In Big Ten games, fouling when up 3 with at most 10 s on the game clock yields a higher overtime-adjusted win rate than defending, with the gap depending on shot clock.
- **Verdict.** **Mixed.** NCAA evidence is split: Zapata-Hall's cell-by-cell policy model gives a small, shot-clock-dependent edge for fouling (+1.63 pp), while KenPom's raw 2009-2013 rates slightly favour defending (neither peer-reviewed); near zero in recent NBA data.

## C5. "Take the two-for-one"

- **Belief.** Near the end of a half, shooting quickly to get two possessions to the opponent's one is worth it.
- **Who holds it.** Coaches, analysts.
- **Claimed effect and size.** About +0.25 possession and about +0.25 point per attempt over waiting (KenPom; see below).
- **Evidence for.** Sasan & Swartzentruber (arXiv 2412.08840, rev. 2026), NBA 2018-19 and 2021-22, causal framework: positive effect on outcomes (size not on the abstract page) ([arXiv](https://arxiv.org/abs/2412.08840)).
- **Evidence for (NCAA, practitioner).** KenPom (2013), NCAA D-I first halves over four seasons (2009-10 to 2012-13, 35 s shot clock), possession gained with 55-65 s left and margin within 9: trying for the two-for-one nets about +0.25 possession over waiting (extra possession about 55% of the time vs about 30% when waiting) and about +0.25 point; early shots partly reflect fast breaks, so the raw efficiency gain is confounded ([KenPom 2013, archived](https://web.archive.org/web/20201217072142/https://kenpom.com/blog/investigating-the-value-of-twoforones/)).
- **Evidence against.** None found.
- **Does the market price it?** Not studied.
- **How we would test it.** **PBP + scoreboard OCR** (shot clock).
- **Proposed hypothesis.** **new-25:** Big Ten teams gaining possession with 35-45 s left in a half and taking the first shot attempt ≤ 10.0 s after gaining possession (shot clock ≥ 20 s on the NCAA 30 s clock, from scoreboard OCR) score more in the remaining time than teams holding for the last shot.
- **Verdict.** **Plausible:** one non-peer-reviewed NBA preprint (size not reported) and one practitioner NCAA analysis under the old 35 s clock (+0.25 possession); no peer-reviewed estimate; untested under the 30 s clock.

## C6. "Hack-a-Shaq" (foul the bad free-throw shooter)

- **Belief.** Intentionally fouling a poor free-throw shooter lowers the opponent's scoring.
- **Who holds it.** Some coaches; mainly an NBA tactic.
- **Evidence.** Skinner & Goldman list intentional fouling as a way to manipulate variance ([arXiv](https://arxiv.org/abs/1512.05652)). FiveThirtyEight and ESPN analyses arguing it often fails once following possessions count were seen in search snippets only **(unverified)**. Less relevant in NCAA because of bonus rules.
- **Does the market price it?** Not studied.
- **How we would test it.** PBP only. Not proposed as a hypothesis.
- **Verdict.** **Untested** (for us; no verified source).

---

# Theme D. Fatigue within a game

## D1. "Players fade late; long stints kill efficiency"

- **Belief.** Accumulated running in a stint lowers shooting and defensive quality.
- **Who holds it.** Coaches (rotation decisions), strength staff, broadcasters.
- **Claimed effect and size.** Unquantified.
- **Evidence for.** Lab study (38 Greek players): a 12-min basketball exercise simulation (mean HR 89.7% HRmax; sprint time 28.4% worse) cut uncontested 3P success: guards 51.8% to 44.1%, forwards 47.7% to 39.5%, centres 42.2% to 33.9% (overall 47.4% to 39.3%, the robust result); release time 0.7 s to 0.8 s (about +0.1 s) and entry angle 43.5° to 42.0° (-1.3° to -1.8° by position), both marked significant in the paper's PRE-POST table (Table 3); a reviewer reading the change-score figure reported confidence intervals including zero for entry angle and for forwards' and centres' release time, which we could not confirm from the text, so treat those two kinematic changes as uncertain ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC10974731/)). 2016-17 Adidas Next Generation (EuroLeague U18) Tournament Finals tracking (94 players, 13 games): relative distance (m/min) -10.2%, %HIR (above 15 km/h = 4.17 m/s) -24.4%, PlayerLoad per minute (a.u./min) -14.3%, Q1 vs Q4 ([Pino-Ortega et al. 2019](https://www.frontiersin.org/articles/10.3389/fpsyg.2019.01100/pdf)).
- **Evidence against.** NBA tracking (Stephen, Yep & Fain, arXiv 2112.14649): in-game distance per minute explains less than 1% of performance variation (largest adjusted R² ≈ 0.0013); associations positive, attributed to usage ([ar5iv](https://ar5iv.labs.arxiv.org/html/2112.14649)).
- **Does the market price it?** Not studied.
- **How we would test it.** **Video/tracking.** Per player, speed (m/s) and high-intensity distance in the preceding 2-5 minutes vs next-shot make probability (difficulty-adjusted) and defensive closeout speed (m/s; shared definition); continuous minutes from PBP substitutions. Speed bands from `load_thresholds.md` Section 9: high-speed running above 5.0 m/s, sprint above 5.83 m/s.
- **Proposed hypothesis.** **new-26:** An MSU player's difficulty-adjusted make probability declines with sprint distance above 5.83 m/s (`load_thresholds.md` primary set, Section 9) accumulated in the current stint.
- **Verdict.** **Mixed.** Clear in the lab; not visible in NBA game data.

---

# Theme E. Venue and crowd

## E1. Home-court advantage in NCAA D-I is worth about 3 to 4 points (and some arenas far more)

- **Belief.** Home court is worth a few points, and famous arenas much more.
- **Who holds it.** Everyone; bookmakers build it into every line.
- **Claimed effect and size.** 3-4 points default; 6-10 for "the toughest places to play".
- **Evidence for (average).**
  - Market-implied HCA (half the difference of reciprocal spreads): 3.68 (2014, 1,626 games) falling to 3.30 (2018, 1,668); largest team-level market HCA Hawaii 4.5 ([KenPom 2018, archived](https://web.archive.org/web/20210109050736/https://kenpom.com/blog/mining-point-spread-data-home-court-advantage/)).
  - Box-score HCA in conference games: 3.75 points (2002-2009), about 0.5 lower in 2010-2017, 2.78 in 2017 with 59% home wins ([KenPom 2017, archived](https://web.archive.org/web/20201217063917/https://kenpom.com/blog/how-to-measure-home-court-advantage/)); 2.78 in 2024 conference games ([KenPom Substack 2024](https://kenpom.substack.com/p/is-home-court-advantage-stronger)).
  - 2019-20 and 2020-21 D-I vs D-I non-neutral games (7,317): home teams won 61.4%, mean margin +3.77 (SD 13.68); home FTA 19.4 vs 17.6 ([Marshall, Locke & Wooten, working paper dated 11 March 2023](https://spaces-cdn.owlstown.com/blobs/c31otj63qa356zwpeclkyawcy1bv); published in *Applied Economics* 2025, DOI 10.1080/00036846.2025.2556040, per the [author's publication page](https://jadrian.owlstown.net/publications/19081-the-impact-of-fans-on-home-advantage-evidence-from-the-covid-19-pandemic-college-basketball-season); journal page not opened).
  - Makinen (VSiN 2025): about 3.3 points overall (2.9 conference) vs power ratings; bookmakers assign "about 3.0"; team range +9.2 (Alabama) to -2.2 ([VSiN](https://vsin.com/college-basketball/determining-college-basketballs-true-home-court-advantage/)).
  - By statistic (KenPom 2015 "Offense vs. Defense" summary table; sample years not restated in the table): free-throw rate +2.8, 2P% +1.4, block% +1.2 (about 12.5% more blocks), 3P% +0.7, FT% +0.5, PPP +3.7 (units not stated, likely per 100 possessions) ([KenPom, archived](https://web.archive.org/web/20190824065637/https://kenpom.com/blog/offense-vs-defense-block-percentage/)).
  - Pollard & Gómez (2015, *Collegium Antropologicum*), 81,063 college and 22,477 pro games: college HCA exceeds pro by 3.73 pp of win rate on average, basketball among the largest gaps ([journal page](https://collantropol.hr/antropo/article/view/298)).
  - Systematic review (39 studies, 2024): NBA home wins 59.6% (2006-2013), Euroleague 66% (2008-09); no NCAA numbers ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11503446/)).
- **Evidence against (fortress claims).** Of the 50 teams with the largest home-minus-road margin in 2002-2009, 48 had smaller ones in 2010-2017 (Texas Tech 7.6 to 4.0); a plausible true range is about 2.2 to 4.6 points ([KenPom, archived](https://web.archive.org/web/20201217063917/https://kenpom.com/blog/how-to-measure-home-court-advantage/)). Market and box-score team HCAs correlate at r ≈ 0.72 only for teams with 40+ pairs ([KenPom 2018, archived](https://web.archive.org/web/20210109050736/https://kenpom.com/blog/mining-point-spread-data-home-court-advantage/)). The best predictor of a team's future HCA is its home-foul advantage, not past scoring HCA ([KenPom part two, archived](https://web.archive.org/web/20201217063910/https://kenpom.com/blog/how-to-measure-site-specific-home-court-advantage-part-two/)). NBA team-HCA reliability 0.284 (Jones 2008, **unverified**). A Substack estimate of 6.4 points is internally inconsistent and flagged as unreliable ([Beyond The Score](https://beyondthescoresports.substack.com/p/breaking-down-home-court-advantage)).
- **Does the market price it?** **Yes.** About 3 points default ([VSiN](https://vsin.com/college-basketball/determining-college-basketballs-true-home-court-advantage/)); oddsmakers quoted at 3-4 ([Harvard Sports Analysis 2011, archived](https://web.archive.org/web/20220517170805/https://harvardsportsanalysis.org/2011/01/back-to-back-blues-the-effect-of-road-trips-in-the-ivy-league/)); market team HCAs track statistical ones.
- **How we would test it.** **PBP only.** Team-strength model on all D-I games with a home indicator; MSU's own HCA shrunk toward the D-I mean. Power: with per-game margin SD about 13.7, 15 home and 15 road games give SE ≈ 5.0 points on the home-minus-road difference, so one MSU season cannot distinguish its HCA from 3 points.
- **Proposed hypothesis.** **new-27:** MSU's HCA in points per 100 possessions is no different from the D-I average once shrunk toward it (2021-22 on).
- **Verdict.** **Supported** for the average (about 3 points); **not supported** for large team-specific "fortress" effects.
- **Addition 2026-10-18.** Peer-reviewed cross-sport baseline (Jamieson 2010 meta-analysis: basketball home win proportion .629; season-length and game-importance moderators) and new-63: see "Additions 2026-10-18", E1, E2 and E4 addition. Neutral-site proximity in the NCAA tournament is the new belief E8 in the same section.

## E2. Home-court advantage has been declining

- **Belief.** Home teams win less than they used to.
- **Who holds it.** Analysts, media, bettors.
- **Claimed effect and size.** NCAA conference home win% down about 2.5 pp from 2000 to 2015; NBA from about 65% to 54-55%.
- **Evidence for.**
  - NCAA conference home win% fell about 2.5 pp from 2000 to 2015; every 5 possessions per game of pace change moves home win% about 1.6 pp, explaining "a little over half" the decline; more charter travel ([KenPom 2015, archived](https://web.archive.org/web/20180719050613/https://kenpom.com/blog/road-teams-are-winning-more-often-in-college-too/)). Market HCA 3.68 to 3.30 (2014-2018) ([KenPom 2018, archived](https://web.archive.org/web/20210109050736/https://kenpom.com/blog/mining-point-spread-data-home-court-advantage/)). Home-foul advantage declined in step ([KenPom part two, archived](https://web.archive.org/web/20201217063910/https://kenpom.com/blog/how-to-measure-site-specific-home-court-advantage-part-two/)).
  - NBA: HCA about 6 to 3 points, 1987-88 to 1994-95 (8,495 games) ([Steenland & Deddens 1997](https://lida.sport-iat.de/dbb/Record/4003477?lng=en)); 2001-02 to 2013-14 (16,133 games) 3.3 points, declining 0.08 per season ([Ribeiro et al. 2016, PLoS ONE](https://pmc.ncbi.nlm.nih.gov/articles/PMC4807825/)); 2014-15 home wins 53.7% ([ESPN 2015](https://africa.espn.com/nba/story/_/id/12241619/home-court-advantage-decline)); expansion-era about 61% regular season ([The Ringer 2021](https://www.theringer.com/2021/06/01/nba/what-happened-to-home-court-advantage)); Sagarin NBA HCA 2.74 (2015-19) to 1.75 (2020-22) ([Pelechrinis, arXiv](https://arxiv.org/abs/2210.13687)).
  - Long run: every major sport had its highest HCA early; basketball HCA declined over the last two decades of 1876-2003 ([Pollard & Pollard 2005](https://lida.sport-iat.de/twm/Record/4009826?lng=en)).
- **Evidence against.** Not monotonic: NCAA rebound to 61.0% in 2018 ([KenPom 2018, archived](https://web.archive.org/web/20210109050736/https://kenpom.com/blog/mining-point-spread-data-home-court-advantage/)); 2024 not "stronger than ever" but not falling either ([KenPom 2024](https://kenpom.substack.com/p/is-home-court-advantage-stronger)); NBA about 58% in 2022-23 **(unverified)**. Part of the "decline" is pace.
- **Does the market price it?** **Yes.** Market HCA fell 3.68 (2014) to 3.23 (2017) and ticked up to 3.30 in 2018, the same season conference home win% rose from 59.0% to 61.0% ([KenPom 2018, archived](https://web.archive.org/web/20210109050736/https://kenpom.com/blog/mining-point-spread-data-home-court-advantage/)). (Corrected 2026-10-18: an earlier version said the market missed the 2018 rebound; the archived table shows it did not.)
- **How we would test it.** **PBP only.** HCA per 100 possessions by season (D-I conference games, 2010-2026), pace-adjusted, with a four-factor split.
- **Proposed hypothesis.** **new-28:** D-I HCA per 100 possessions has declined since 2010 after pace adjustment, mainly through the free-throw-rate component.
- **Verdict.** **Supported** over decades; not monotonic recently.
- **Addition 2026-10-18.** Jamieson (2010) era moderator (flat since 1950 across sports): see "Additions 2026-10-18".

## E3. Home advantage is front-loaded (it shows up early)

- **Belief.** The crowd matters most at the start; road teams must "survive the first 8 minutes".
- **Who holds it.** Coaches, broadcasters.
- **Evidence for.** NBA: the home-away gap in time between scores is largest in Q1 ([Ribeiro et al. 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC4807825/)). About two-thirds of NBA home edge accrues in Q1 (Jones 2007, **unverified**, snippet only).
- **Evidence against.** No college test found. Early-game intensity is general, not home-specific (U18 tournament: relative distance (m/min) -10.2%, %HIR -24.4% from Q1 to Q4) ([Pino-Ortega et al. 2019](https://www.frontiersin.org/articles/10.3389/fpsyg.2019.01100/pdf)).
- **Does the market price it?** First-half lines exist; no study of first-half HCA pricing.
- **How we would test it.** **PBP only.** Cumulative home-minus-road margin per 100 possessions by 4-minute segment, D-I wide; supports H10.
- **Proposed hypothesis.** **new-29:** In D-I games, more than half the full-game HCA per 100 possessions is accumulated in the first 10 minutes.
- **Verdict.** **Untested** in NCAA; NBA evidence supportive.

## E4. Crowds cause home-court advantage (the 2020-21 empty-arena experiment)

- **Belief.** Fans are the home-court advantage; remove them and it disappears.
- **Who holds it.** Fans, players, coaches (Self, Calipari, Drew, Weber quoted in [CBS Sports 2021](https://www.cbssports.com/college-basketball/news/how-the-home-court-advantage-in-college-basketball-is-shrinking-this-season-due-to-fewer-fans-at-games)).
- **Claimed effect and size.** "Most" of HCA.
- **Evidence for (NCAA).**
  - Marshall, Locke & Wooten (working paper dated 11 March 2023; *Applied Economics* 2025 per the author's page, journal version not opened), 7,317 D-I games: raw home margin 4.29 (2019-20, n = 4,241) to 3.05 (2020-21, n = 3,076); home win% 63.2% to 58.9%. The authors' own reading: home advantage "falls by 2.47 points" in the absence of fans (3.40 in Power-6 vs Power-6 games, n = 1,177; 2.24 in non-Power-6, n = 4,551). **Our derivation:** the regression uses two rows per game (14,634 observations for 7,317 games), so the Home coefficient (8.19) is about twice the raw home margin (pre-pandemic 4.29; pooled 3.77), and the printed coefficients (-2.47, -3.40, -2.24) correspond to about -1.2, -1.7 and -1.1 points in conventional single-game HCA units. Attendance fell 9,614 in Power-6 vs 2,197 in other games: a dose-response pattern ([working paper](https://spaces-cdn.owlstown.com/blobs/c31otj63qa356zwpeclkyawcy1bv)).
  - Samford (19,285 games, four seasons): home win% fell almost 5 pp in 2020-21; visitor fouls fell 4.8%, home fouls flat (16.80 vs 16.86); visitor fouls fell in 27 of 31 conferences ([Samford](https://www.samford.edu/sports-analytics/fans/2021/Did-Minimal-Crowds-in-2020-2021-Impact-College-Basketball-Home-Team-Performance)).
  - D-I home win 57.3% (to January 2021), lowest since 1996-97 ([CBS Sports](https://www.cbssports.com/college-basketball/news/how-the-home-court-advantage-in-college-basketball-is-shrinking-this-season-due-to-fewer-fans-at-games)). Women's D-I: home win .577 to .542; net rating +4.2 to +2.4 per 100 ([Her Hoop Stats](https://herhoopstats.substack.com/p/ncaa-basketball-home-court-pandemic-fans)).
- **Evidence for (NBA, Europe).** NBA 2020-21 (n = 1,080): home win 58.65% with crowds vs 50.60% without, mediated by rebounding (effort) ([Leota et al. 2022](https://research.birmingham.ac.uk/en/publications/home-is-where-the-hustle-is-the-influence-of-crowds-on-effort-and/)). Bubble playoffs: home 0.482 vs 0.613 (not significant after Bonferroni); away scoring +5 points (CI 2.1-8.0) ([Price & Yan 2021](https://arxiv.org/pdf/2103.02832)). Bayesian playoff HCA about 5% of points ([Higgs & Stavness 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC8282683/)). Bubble regular season 55.7% vs 44.3% (p = 0.07) ([McHill & Chinoy 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7732833/)). Staples Center (same building): crowd worth 21-22.8 pp of win probability ([Boudreaux et al. 2017](https://ideas.repec.org/a/sae/jospec/v18y2017i7p737-749.html)). Ten European leagues (27,691 games; 1,026 ghost games): home win 61.1% to 56.0% ([De Angelis & Reade 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC9517988/)).
- **Evidence against.** HCA did not vanish: NCAA home margin stayed near 3 points. About 1.2 of 3.8-4.3 points (28-32%; our derivation) is associated with the attendance drop; a lower bound on the full-crowd effect, since 2020-21 crowds were reduced, not zero (working paper; journal version not opened) ([Marshall et al.](https://spaces-cdn.owlstown.com/blobs/c31otj63qa356zwpeclkyawcy1bv)). Euroleague HCA persisted without fans (Bourdas et al. 2022, via [2024 review](https://pmc.ncbi.nlm.nih.gov/articles/PMC11503446/)). 2020-21 had other changes (regional schedules, COVID absences, partial crowds). Long-run trends favour travel and familiarity over crowds ([Pollard & Pollard 2005](https://lida.sport-iat.de/twm/Record/4009826?lng=en)).
- **Does the market price it?** Europe: priced immediately (implied home probability down 3.5-5.2 pp), no profit ([De Angelis & Reade](https://pmc.ncbi.nlm.nih.gov/articles/PMC9517988/)). NCAA 2020-21 market adjustment: no study found; an oddsmaker said he would adjust totals ([Action Network](https://www.actionnetwork.com/news/coronavirus-sports-games-no-crowd-empty-stadium-fans-rovell)).
- **How we would test it.** **PBP + box-score attendance.** Difference-in-differences 2018-19 to 2022-23 with attendance as a continuous dose, one row per game; decompose by foul rate, FTA, turnover type, ORB. **Video** adds box-out and crash counts to test the effort mechanism.
- **Proposed hypothesis.** **new-30:** In D-I games, each additional 1,000 spectators raises home margin per 100 possessions, mainly through the visitor foul rate (2019-20 vs 2020-21).
- **Verdict.** **Supported, partially:** crowds cause a substantial share, not all (NCAA lower bound ≥ ~30%, our derivation from one working paper).
- **Addition 2026-10-18.** Courneya & Carron (1992) crowd/familiarity/travel/rules framework (secondary, via Jamieson 2010): see "Additions 2026-10-18".

## E5. Altitude helps the home team

- **Belief.** Sea-level teams wilt in thin air, especially late in halves.
- **Who holds it.** Coaches, players, media, bettors.
- **Claimed effect and size.** Several points beyond normal HCA.
- **Evidence for.** Wyoming vs San Diego State 2000-2012 (13 games): 10.4-point home/away swing, about 2.4 points beyond a 4-point HCA; Colorado in the Big 12 (75 + 75 games): 14.5-point gap, about 6.5 beyond normal ([KenPom 2012, archived](https://web.archive.org/web/20201217074226/https://kenpom.com/blog/how-much-is-air-worth/)). KenPom's team-HCA model includes elevation and rated Air Force top at 4.5 in 2017 ([KenPom part two, archived](https://web.archive.org/web/20201217063910/https://kenpom.com/blog/how-to-measure-site-specific-home-court-advantage-part-two/)). Elevations: Wyoming's arena 2,201 m, highest in D-I ([Inside the Hall](https://www.insidethehall.com/2022/03/13/2022-ncaa-tournament-first-look-wyoming-cowboys/)); Colorado's arena 1,655 m ([Daily Bruin](https://dailybruin.com/2014/01/16/high-altitudes-to-give-colorado-home-court-edge-over-ucla)); Albuquerque about 1,615 m ([KenPom 2012, archived](https://web.archive.org/web/20201217074226/https://kenpom.com/blog/how-much-is-air-worth/)); Denver 1,608 m ([NBA.com](https://www.nba.com/news/is-impact-of-denvers-altitude-fact-or-fiction)) or 1,609 m and Salt Lake City about 1,311 m ([MSU Denver](https://red.msudenver.edu/2018/advantage-altitude-exploring-the-largest-home-advantage-in-sports/)); Utah State, Air Force and BYU **unverified**. NBA: Denver and Utah have the largest HCAs, Denver about 67% vs an equal team ([MSU Denver summary](https://red.msudenver.edu/2018/advantage-altitude-exploring-the-largest-home-advantage-in-sports/); [Lopez, Matthews & Baumer](https://arxiv.org/abs/1701.05976)); Denver all-time 1,238-641 home vs 662-1,250 away ([NBA.com](https://www.nba.com/news/is-impact-of-denvers-altitude-fact-or-fiction)). Soccer dose-response: about 0.5 goals per 1,000 m altitude difference ([McSharry 2007, via ScienceDaily](https://www.sciencedaily.com/releases/2007/12/071221094837.htm)).
- **Evidence against.** City elevation added nothing to an NBA team-HCA model over 32 seasons ([Harris & Roebber 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6668839/)). KenPom's samples are small and confound altitude with distance and remoteness. NCAA tournament: no clear elevation effect (Winthrop 2014, **unverified**). The NBA's schedule changes for Denver show the league treats it as real but do not size it ([NBC Sports 2015](https://nbcsports.com/nba/news/report-nba-trying-to-diminish-nuggets-home-court-advantage)).
- **Does the market price it?** Partly (remote and high teams get larger market HCA); no test of full pricing.
- **How we would test it.** **PBP + venue elevation (m).** HCA with elevation difference as a continuous dose, controlling distance and time zones, focusing on minutes 10-20 and 30-40. D-I-wide work; MSU has no high-altitude Big Ten road games.
- **Proposed hypothesis.** **new-37:** Each additional 1,000 m of elevation difference adds to the home margin per 100 possessions, concentrated in the last 8 minutes of each half.
- **Verdict.** **Mixed** (large in small college samples and in Denver; null in an NBA model).

## E6. Arena shooting backgrounds (domes, backdrops, distraction sections)

- **Belief.** Shooters need a near background; football domes hurt shooting, especially threes; distracting backdrops lower opponents' FT%.
- **Who holds it.** Players, coaches, media. Pomeroy said shooting at NRG Stadium was about 4 pp lower ([WBUR 2016](https://www.wbur.org/onlyagame/2016/04/02/ncaa-astrodome-final-four)); his blog estimate of 3-4 pp of 3P% **(unverified: 403)**.
- **Evidence for.** Nylon Calculus (2006-2016; 42 midfield-dome vs 75 arena games): domes 2.3 fewer points per team, mostly free throws (70.5% vs 72.9%) and 2P% (46.2 vs 47.5); 3P% was *higher* in domes (34.6 vs 33.8) ([FanSided](https://fansided.com/2017/03/30/ncaa-tournament-domes-shooting-effect/)). NRG Stadium significant on 2P% and TS% (loses significance without Butler's 2011 final) ([Eldorado](https://www.eldo.co/the-dome-effect-how-nrg-stadium-impacts-shooting.html)). End-zone setups 31.9% 3P vs midfield 35.5% ([Bleacher Report](https://bleacherreport.com/articles/2629585-the-dome-dilemma-why-poor-shooting-at-houstons-nrg-stadiums-may-be-a-myth)). Arizona State's Curtain of Distraction: visitor FT about 70% before vs about 61% after ([Slate](https://slate.com/culture/2015/02/asu-curtain-of-distraction-has-arizona-state-university-discovered-the-holy-grail-of-free-throw-distraction.html)).
- **Evidence against.** Eldorado (165 late-round games 2006-2016, each team vs its own season average): venue type not significant once offense and defense are included; midfield-dome scoring gap (-1.2 ppg) matches opponents' defensive quality (-1.1) ([Eldorado 2017](https://www.eldo.co/dome-effect-college-basketball-ncaa-tournament-2017.html); [180-game update](https://www.eldo.co/domed-football-stadiums-effect-on-shooting-final-four-ncaa-tournament-college-basketball.html)); TS% arenas 51.27, corner domes 51.44, midfield domes 51.33 ([Eldorado by venue type](https://www.eldo.co/the-dome-effect-ncaa-tournament-shooting-by-venue-type.html)). The worst setup is a corner or end-zone dome, not midfield. Curtain critique: in the full curtain season visitors shot 58.9% and 60.1% by half, and Big Ten visitors' FT% rises 2.6 pp from first to second half anyway ([Slate](https://slate.com/culture/2015/02/asu-curtain-of-distraction-has-arizona-state-university-discovered-the-holy-grail-of-free-throw-distraction.html)). NBA bubble FT% rose 77.1% to 80.6% without crowds ([Berkeley student org](https://sportsanalytics.studentorg.berkeley.edu/articles/shooting-percentages.html)); JMLD 2023 figures **unverified**.
- **Does the market price it?** Not documented; test would be closing totals at domed Final Fours.
- **How we would test it.** Domes: **PBP + venue metadata** (shooting residual vs season average, opponent-adjusted). Near backgrounds at regular arenas: **video** to classify each basket's backdrop, then FT% by end and half, shooter fixed.
- **Proposed hypotheses.** **new-47:** In NCAA tournament games, the shooting residual (FT%, 2P%, 3P% minus season average, opponent-adjusted) does not differ between midfield-dome and arena venues; corner-dome setups lower 3P%. **new-48:** FT% differs by basket end within the same arena when one end's backdrop is an active student section (PBP if shot end is known; otherwise video). Video rule for "active": a seated or standing crowd occupies ≥ 50% of the backdrop area in the shooter's line of sight (θ_view within ±15° of the line through the backboard, stands within 10 m behind the baseline), with visible motion or signage during the free throw.
- **Verdict.** **Not supported** for modern midfield domes; **mixed** for corner domes and distraction backdrops (practitioner analyses only; no peer-reviewed study; FanSided's FT% and 2P% deficit conflicts with Eldorado).

## E7. Senior night

- **Belief.** Seniors play inspired in the last home game (or the emotion causes a letdown).
- **Who holds it.** Fans, media, bettors.
- **Evidence for.** None rigorous for basketball.
- **Evidence against.** College football, 10 seasons: final-home-game teams covered slightly less, not significant ([Harvard Sports Analysis 2014, archived](https://web.archive.org/web/20210122215223/http://harvardsportsanalysis.org/2014/12/does-senior-day-matter-in-college-football/)). Basketball: a single Penn anecdote ([Daily Pennsylvanian 2012](https://www.thedp.com/blog/buzz/2012/03/senior-night-stats-revisted)). A mechanical effect exists: walk-on seniors sometimes start.
- **Does the market price it?** Football suggests priced or absent; no basketball test.
- **How we would test it.** **PBP + schedule + closing lines**, D-I wide; also first-4-minute lineup and margin.
- **Proposed hypothesis.** **new-38:** D-I home teams in their final regular-season home game do not beat expectation by more than 1 point.
- **Verdict.** **Untested.**

---

# Theme F. Officials

## F1. Referees favour the home team (crowd pressure)

- **Belief.** Officials give the home team close calls because of crowd noise.
- **Who holds it.** Coaches, players, fans, much of the academic literature.
- **Claimed effect and size.** *Scorecasting* calls official bias the largest single contributor to HCA; NBA FT% identical home and away (75.9%) **(secondary: [Goodreads blog summary](https://www.goodreads.com/author_blog_posts/5893028-how-do-you-explain-home-field-advantage))**.
- **Evidence for (NCAA).** Anderson & Pierce (2009, *J. Sports Sciences* 27(7): 687-694), 365 games, first halves: fouls more likely on visitors and on the leading team; next-foul probability against the visitor can reach about 0.70 ([sponet abstract](https://www.sponet.de/sponet/Record/4016050?lng=en)). Van Bommel, Bornn et al. (arXiv 1909.04817), 141,640 NCAA games: PF and FTA are the statistics most sensitive to attendance; top vs bottom attendance quartile, D-I men's home edge grows 0.87 PF and 1.38 FTA per game; FT% unaffected ([ar5iv](https://ar5iv.arxiv.org/html/1909.04817)). Home-foul advantage predicts future HCA ([KenPom part two, archived](https://web.archive.org/web/20201217063910/https://kenpom.com/blog/how-to-measure-site-specific-home-court-advantage-part-two/)). 2020-21: visitor fouls -4.8%, home flat ([Samford](https://www.samford.edu/sports-analytics/fans/2021/Did-Minimal-Crowds-in-2020-2021-Impact-College-Basketball-Home-Team-Performance)).
- **Evidence for (NBA, mechanism).** Price, Remer & Stone (2012, *J. Econ. Manage. Strategy* 21(1): 271-300): using discretionary vs non-discretionary turnovers, referees favour home teams, trailing teams and teams trailing in a series ([IDEAS](https://ideas.repec.org/a/bla/jemstr/v21y2012i1p271-300.html)); press: about 2.2-2.5% win probability, about 5% in playoffs ([New Republic](https://newrepublic.com/article/86559/basketball-referees-biased-nba-playoffs-study-espn-donaghy)); about 1 pp per 1,000 spectators ([APBR repost, secondary](https://apbr.org/forum/viewtopic.php?p=7958)). Pelechrinis (arXiv 2210.13687), NBA L2M 2015-2022: home net whistle gain +145.6 decisions (about 1.6%), playoffs about 7%; vanished in 2020-2022 (+8.9, p = 0.49) ([arXiv](https://arxiv.org/abs/2210.13687); [PDF](https://arxiv.org/pdf/2210.13687)). Lab: live crowd noise shifted Muay Thai judges' scores 0.53 points per bout (17 judges, 30 bouts); soccer referees with crowd noise gave fewer fouls against the home team ([Myers & Balmer 2012](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2012.00346/full); the 15.5% Nevill figure **unverified**).
- **Evidence against.** Morgulev et al. (2018), 250 Israeli offensive-foul incidents: no home favouritism (18.9% vs 19.5%, p = 0.90) ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6306443/)); Deutscher (2015), 1,229 calls in close NBA games, no home bias (cited there). Harris & Roebber (2019): attendance adds nothing to NBA team HCA ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC6668839/)). Box-score foul differences cannot separate referees from player behaviour without a design like Price et al.
- **Does the market price it?** Average HCA is priced. NBA L2M referees made 23% fewer incorrect calls against visiting underdogs and 42% fewer against home underdogs ([Belasen et al. 2025](https://lida.sport-iat.de/dbb/Record/4096166)), a pattern tied to the line, not a profitability test.
- **How we would test it.** **PBP + attendance + referee names** (ESPN game summary): discretionary vs non-discretionary turnovers home vs away by attendance band, crew fixed effects. **Video**: referee position and distance from play, to test whether ambiguous calls drive the bias.
- **Proposed hypothesis.** **new-31:** In D-I games, discretionary turnovers (traveling, offensive fouls, 3-second violations) are called more against visitors than non-discretionary ones, and the gap grows with attendance.
- **Verdict.** **Supported** (moderate; strongest evidence NBA; NCAA via attendance-sensitive fouls).

## F2. Make-up calls: referees even out the foul count

- **Belief.** After a one-sided call, officials "give one back".
- **Who holds it.** Coaches, players, fans; referees deny it.
- **Evidence for.** Anderson & Pierce (2009), NCAA 365 games: the next foul is more likely called on the team with fewer fouls, growing with the gap ([lida abstract](https://lida.sport-iat.de/twm/Record/4016050?lng=en); [sponet](https://www.sponet.de/sponet/Record/4016050?lng=en)). Noecker & Roback (2012, JQAS 8(3)) follow-up: citation only **(unverified)**. NBA: Paul Gift (1+ million possessions, 2006-2011): offensive fouls, traveling and offensive 3-second calls rise on the possession after the same call against the other team ([Yahoo Sports 2022](https://ca.sports.yahoo.com/news/do-makeup-calls-exist-131350055.html)). NHL make-up penalties (**unverified**).
- **Evidence against.** Even counts can be player-driven (cautious play with more fouls; leading teams foul less late). NBA L2M: the chance an error hurts the same team as the previous error is about 50% ([Yahoo Sports](https://ca.sports.yahoo.com/news/do-makeup-calls-exist-131350055.html)).
- **Does the market price it?** No evidence; possibly relevant to live markets.
- **How we would test it.** **PBP only**: next foul's team as a function of foul differential, margin, time, venue, crew, with team foul-tendency controls. **Video** separates obvious calls (intentional, flagrant).
- **Proposed hypotheses.** **new-23:** In MSU games, the probability the next foul is on MSU rises with the opponent-minus-MSU foul gap (first halves). **new-32:** In D-I games, the probability the next non-intentional foul is on team A rises with team B's foul lead, controlling score, time and team foul tendency. (new-23 is the MSU subgroup of new-32.)
- **Verdict.** **Mixed** (NCAA 2004-05 and NBA sequence evidence for; player-behaviour confound and L2M error sequencing against).

## F3. Star treatment

- **Belief.** Stars draw more fouls and are called for fewer.
- **Who holds it.** Fans and media (mostly NBA).
- **Evidence for (NBA).** Pelechrinis (2022): 12 of 106 high-volume players have significantly positive L2M net whistle gain, mostly All-Stars (Chris Paul +3.97%) ([arXiv](https://arxiv.org/abs/2210.13687)). MIT Sloan study reported by NBC (1.5 million plays): 42% of loose-ball fouls called on stars vs 57% on non-stars; 28% in foul trouble ([NBC Sports 2010](https://www.nbcsports.com/nba/news/nba-referees-are-biased)). Caudill et al. 2014 (+0.32 FTA per minute for All-Stars in playoff 4th quarters) and Lehman & Reifman 1987 via review ([Morgulev et al. 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6306443/); primaries not opened). Higher-salaried players draw more fouls per 48 min ([Barrett 2021](https://digitalcommons.bryant.edu/eeb/vol14/iss1/9)).
- **Evidence against.** Israeli league: no player-status effect (p = 0.81) ([Morgulev et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC6306443/)). Stars attack the rim more, so raw rates differ for real reasons; NCAA has no correct-call ground truth.
- **Does the market price it?** Not at game level, as far as found.
- **How we would test it.** **Video/tracking + PBP**: comparable contact situations (drives by r band, post-ups), call rate for top-usage vs other players.
- **Proposed hypothesis.** **new-33:** For drives ending within r ≤ 1.5 m of the rim, the foul-call rate is higher for the team's top-usage player than for teammates, after adjusting for contact type. Drive = ball-handler dribbling, starting at r ≥ 6.0 m, reducing r by ≥ 3.0 m within ≤ 3.0 s, ending at r ≤ 1.5 m. Contact type = video label: shooting arm, body, hand-check, or block/charge (defender's feet set ≥ 0.5 s before contact), each split inside vs outside the restricted-area arc (r = 1.22 m).
- **Verdict.** **Mixed** (NBA supportive; NCAA untested).

## F4. Referees keep games close (favour the trailing team)

- **Belief.** Officials help the team that is behind.
- **Evidence for.** NBA 2002-2008: referees favour teams trailing in the game ([Price, Remer & Stone 2012](https://ideas.repec.org/a/bla/jemstr/v21y2012i1p271-300.html)); the playoff-series part was described as insignificant by one author ([APBR repost](https://apbr.org/forum/viewtopic.php?p=7958)). NCAA 2004-05: fouls biased toward the leading team ([Anderson & Pierce 2009](https://www.sponet.de/sponet/Record/4016050?lng=en)).
- **Evidence against.** Score-dependent fouling is mostly strategic (late intentional fouls); must be excluded.
- **Does the market price it?** Not studied; may matter for live totals.
- **How we would test it.** **PBP only**: foul and discretionary-turnover call rates by margin bucket before the final 2:00.
- **Proposed hypothesis.** **new-34:** Before the final 2:00, D-I officials call discretionary turnovers and non-shooting fouls more often on the leading team, controlling team tendencies.
- **Verdict.** **Mixed.**

---

# Theme G. Schedule, travel and rest

## G1. Travel distance and time zones hurt the road team

- **Belief.** Long trips, especially across time zones, sap legs and shooting.
- **Who holds it.** Coaches, players, analysts, bettors; **H10** is already in the registry.
- **Evidence for.** NBA 2019-20 pre-pause: away teams won significantly less crossing 1 zone (p = 0.007) or 2 zones (p = 0.005); westward only; away eFG% -1.5 points at 2 zones; defensive rating worse by at least 2.8 per 100; home edge vanished in the bubble ([McHill & Chinoy 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7732833/); [BPS summary](https://bps.org.uk/research-digest/why-do-basketball-teams-have-home-court-advantage-natural-experiment-during)). NBA/NHL/NFL (5 seasons): direction matters, westward evening games worst ([AASM release](https://aasm.org/nfl-nba-and-nhl-teams-have-a-disadvantage-when-traveling-west); F-values **unverified**). NBA 1987-1995: west-to-east cross-country visitors +4 points (p = 0.07) ([Steenland & Deddens](https://lida.sport-iat.de/dbb/Record/4003477?lng=en)). NBA betting: home teams on the second night of a back-to-back underperform ATS, more after eastward travel ([Ashman et al. 2010](https://ideas.repec.org/a/sae/jospec/v11y2010i6p602-613.html)). Hawaii's market HCA 4.5 vs box-score 2.8 ([KenPom 2018, archived](https://web.archive.org/web/20210109050736/https://kenpom.com/blog/mining-point-spread-data-home-court-advantage/)). Sun Belt travel partners 2016-17: visitors vs comparable opponents won 57% of game 1s but 17% of game 2s, -3.25 points (descriptive) ([Mitchell et al. 2019](https://thesportjournal.org/article/evaluating-the-two-game-road-trip-in-college-sports-does-a-travel-partner-scheduling-approach-affect-team-competitiveness/)). NCAA tournament: eastbound teams crossing 2+ zones won below 38%, more than 241 km cut win odds to 0.664 (Winthrop 2014, **unverified**).
- **Evidence against.** Big 12: no relation between trip length and HCA (Watkins 2013, cited in [Mitchell et al.](https://thesportjournal.org/article/evaluating-the-two-game-road-trip-in-college-sports-does-a-travel-partner-scheduling-approach-affect-team-competitiveness/)). Ivy road back-to-backs (168, 2004 on): .385 expected vs .391 actual; distance not significant (author's comment); covers 50% ([Harvard Sports Analysis 2011, archived](https://web.archive.org/web/20220517170805/https://harvardsportsanalysis.org/2011/01/back-to-back-blues-the-effect-of-road-trips-in-the-ivy-league/)). Distance not predictive of NCAA tournament results beyond RPI and seed ([ESRI 2006](https://esri.com/news/arcuser/1006/spatial-madness2of2.html)). Direction effects mixed across NBA studies ([2024 review](https://pmc.ncbi.nlm.nih.gov/articles/PMC11503446/)). Charter travel has eased trips ([KenPom 2015, archived](https://web.archive.org/web/20180719050613/https://kenpom.com/blog/road-teams-are-winning-more-often-in-college-too/)).
- **Does the market price it?** Partly; older NBA inefficiency ([Ashman 2010](https://ideas.repec.org/a/sae/jospec/v11y2010i6p602-613.html)); NCAA tournament market efficient 1996-2019, travel not tested ([Hickman 2020](https://verso.uidaho.edu/esploro/outputs/journalArticle/Efficiency-in-the-madness-examining-the/996651783101851)).
- **How we would test it.** **PBP + venue coordinates + tip times**: great-circle km and time-zone shift from previous venue, direction, local tip time vs home body clock; outcome first-half points per 100 possessions, opponent-adjusted.
- **Proposed refinement of H10.** Keep H10's wording; pre-register direction: westward shifts for evening tips and eastward shifts for early tips lower first-half points per 100 possessions; measure per km and per zone.
- **Proposed hypothesis.** **new-35:** Visitors on the second game of a road trip without returning home lose more points per 100 possessions against expectation than on the first game.
- **Verdict.** **Mixed** (NBA supportive, direction-dependent; NCAA evidence weak or null).
- **Addition 2026-10-18.** Large peer-reviewed NBA jet-lag studies (Leota et al. 2022; Özdalyan et al. 2024; Pradhan et al. 2022) conflict on direction; revised pre-registration advice for H10: see "Additions 2026-10-18", G1 / H10 addition. Officiating crews and totals are the new belief F5 in the same section.

## G2. Rest and short turnarounds

- **Belief.** The more-rested team wins; two-day turnarounds and back-to-backs cost points.
- **Who holds it.** Coaches, bettors, analysts.
- **Evidence for.** Entine & Small (2008, JQAS 4(2)), NBA 2,415 games: 0 days' rest costs **1.77 points** of margin vs 3+ days (SE 0.83, p = 0.032); 1 day only 0.13; rest imbalance explains 10.5% of HCA (bootstrap CI 5.2-17.7%) ([PDF](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Nba.pdf)). NBA 1987-1995: more than one day of rest adds 1.1-1.6 points ([Steenland & Deddens](https://lida.sport-iat.de/dbb/Record/4003477?lng=en)). Compressed 2011-12: road second nights about -3 per 100 ([Grantland 2012](https://grantland.com/the-triangle/the-effects-of-the-compressed-schedule-examining-back-to-backs/)). NBA 2016-17 paint points 42.2 (back-to-back) vs 44.6 (2 days), small effect sizes ([Yang et al. 2021](https://pmc.ncbi.nlm.nih.gov/articles/PMC7925613/)). Women's D-I same-venue back-to-backs (406 games): road record 203-201 on day 1 vs 184-220 on day 2 ([Her Hoop Stats](https://herhoopstats.substack.com/p/ncaa-womens-basketball-back-to-backs-pace-fouls)). Day 2 PlayerLoad per minute lower (ES 0.26), fatigue higher (ES 1.31) ([Conte et al. 2021](https://lida.sport-iat.de/ta/Record/4072988?lng=en)). NCAA D-I (7 players): pre-game jump height 22.7 to 19.9 cm in conference play (ES 0.43), but no change in distance or peak speed (4.31 vs 4.25 m/s) ([Petway et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7739638/)). Charest et al. 2021 (about 4% lower odds per extra 500 km) **unverified**.
- **Evidence against.** Ivy road second nights: no underperformance; lines shaded about 0.45 points; covers 50% ([Harvard Sports Analysis 2011, archived](https://web.archive.org/web/20220517170805/https://harvardsportsanalysis.org/2011/01/back-to-back-blues-the-effect-of-road-trips-in-the-ivy-league/)). 2023 NCAA tournament: rest and travel did not drive 3P%; rotation size did ([UNC poster](https://our.unc.edu/abstract/hayes-fighting-fatigue-investigating-factors-that-influence-3-point-percentage-in-ncaa-mens-basketball)). Per-game PlayerLoad flat across games in a congested week ([Fox et al. 2020](https://pmc.ncbi.nlm.nih.gov/articles/PMC7075230)).
- **Does the market price it?** NBA partly inefficient in older data ([Ashman 2010](https://ideas.repec.org/a/sae/jospec/v11y2010i6p602-613.html)); NCAA Ivy evidence suggests about 0.45-point shading and efficiency. NFL method reference: markets price bye-week edges ([Lopez & Bliss 2024](https://www.frontiersin.org/journals/behavioral-economics/articles/10.3389/frbhe.2024.1479832/full)).
- **How we would test it.** **PBP + schedule**: rest days (0, 1, 2, 3+), rest difference, Saturday-Monday turnarounds; outcome points per 100 possessions vs expectation by half. **Video/tracking (Job E)**: MSU distance per minute, distance per minute above 5.0 m/s (and above 5.83 m/s as the sprint view), accelerations at ±2.0 m/s² (exploratory; only after the noise-floor test in `load_thresholds.md` passes), peak speed on short vs normal rest (bands per `load_thresholds.md` Section 9).
- **Proposed hypothesis.** **new-36:** D-I teams on 1 day of rest facing an opponent with 3+ days lose at least 1 point per 100 possessions against expectation, concentrated in the second half (video add-on: MSU second-half distance per minute above 5.0 m/s, and above 5.83 m/s as the sprint view, falls on short rest; `load_thresholds.md` Section 9).
- **Verdict.** **Mixed** (supported in the NBA at 0 days' rest; weak or null in NCAA).

## G3. Conference-tournament fatigue carries into the NCAA tournament

- **Belief.** Teams that play 3-4 games in 3-4 days arrive tired (or, the opposite belief, carry momentum).
- **Who holds it.** Media, coaches, bettors.
- **Evidence for.** Mined betting trends: teams that missed their conference final 44-64-2 ATS (40.7%) vs conference champions in round 1; power-conference final losers 48-35-2 ATS (57.8%) ([VSiN 2026](https://vsin.com/college-basketball/college-basketball-ncaa-tournament-first-round-betting-trends/)); weak evidence. "Tired legs" unders profitable 2009-2015, once since ([Action Network](https://www.actionnetwork.com/ncaab/do-tired-legs-actually-lead-to-conference-tournament-unders)).
- **Evidence against.** FiveThirtyEight (Paine 2015; every conference-tournament and NCAA tournament game since 1985): "practically no relationship" between conference-tournament and NCAA over-performance (tests carry-over, not fatigue) ([FiveThirtyEight, archived](https://web.archive.org/web/20201128170855/https://fivethirtyeight.com/features/do-conference-tournament-surprises-carry-over-into-the-ncaa-bracket/)). Rest days before the first NCAA game (Kaggle data 1985-2016, seed-differential controlled): no linear or quadratic relationship with winning the first game (tests rest days, not games played) ([Harvard Sports Analysis 2018, archived](https://web.archive.org/web/20210128093705/http://harvardsportsanalysis.org/2018/03/march-madness-does-conference-tournament-timing-matter/)). Weak descriptive relation ([R-bloggers](https://www.r-bloggers.com/2020/09/momentum-in-sports-does-conference-tournament-performance-impact-ncaa-tournament-performance/)). U18 4-day tournament: match 3 had *higher* physical demands than matches 1-2 ([Pino-Ortega et al. 2019](https://www.frontiersin.org/articles/10.3389/fpsyg.2019.01100/pdf)).
- **Does the market price it?** **Yes, largely**: tournament market efficient 1996-2019 ([Hickman 2020](https://ideas.repec.org/a/spr/jecfin/v44y2020i3d10.1007_s12197-020-09507-7.html)); Action Network says the market is "largely accounting for" fatigue.
- **How we would test it.** **PBP + schedule + closing lines**: conference-tournament games played and days since last game vs NCAA first-game margin minus spread. **Video/tracking (Job E)** for MSU's high-speed distance after deep vs short runs. Example: in 2026 MSU (No. 3 seed, triple bye) played one Big Ten tournament game, losing 88-84 to UCLA on 13 March ([Wikipedia](https://en.wikipedia.org/wiki/2026_Big_Ten_men%27s_basketball_tournament)).
- **Proposed hypothesis.** **new-39:** The number of conference-tournament games played in the preceding 5 days does not predict NCAA first-game margin vs the closing spread.
- **Verdict.** **Not supported on indirect, non-peer-reviewed evidence** (carry-over and rest-day tests); the fatigue claim itself (games in the last 5 days vs ATS) is **untested**. new-39 is the direct test.

## G4. Byes: rest vs rust

- **Belief.** Two camps: double- and triple-bye teams come out flat ("rust"), or the bye is an edge ("rest").
- **Who holds it.** Coaches (Boeheim, Beilein on rust), media, bettors.
- **Evidence.** Big East 2009-10: 5 of 8 double-bye teams lost their first game ([Pitt News](https://pittnews.com/article/19295/archives/march-madness-double-byes-a-tricky-part-of-big-east-tournament)). Big Ten 2026: of the four triple-bye seeds only No. 1 Michigan won its quarterfinal; No. 7 Purdue won the title after 4 games in 4 days ([Wikipedia](https://en.wikipedia.org/wiki/2026_Big_Ten_men%27s_basketball_tournament)). Both anecdotal. JuiceReel ("last five seasons"): power-conference favourites off a bye facing teams that already played went 312-106 SU, 219-191 ATS (53.4%) ([newsletter](https://juicereel.beehiiv.com/p/betting-conference-tournaments)); methodology unclear. Rest helps physically in general ([Entine & Small](https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Nba.pdf)). No study isolates rust from regression of top seeds.
- **Does the market price it?** Possibly underprices the rest side (unverified methodology).
- **How we would test it.** **PBP + schedule + closing lines**: bye team vs opponent who played the day before; rust shows as a first-half deficit that disappears. **Video** add-on: early turnover rate and transition-defense timings (first-defender-back time in s, shared definition; opponent PPP under each stored transition definition).
- **Proposed hypothesis.** **new-40:** In conference tournaments, bye teams facing opponents who played the day before perform at or above expectation over the game, but below it in the first 10 minutes.
- **Verdict.** **Untested.**

---

# Theme H. Psychology and narrative

## H1. Revenge games

- **Belief.** A team that lost the previous meeting plays harder in the rematch and beats expectations.
- **Who holds it.** Fans, media, handicappers ("revenge spot"); players and coaches in quotes.
- **Claimed effect and size.** Largest after a recent or embarrassing loss; no numbers given (handicapping guide, **unverified**).
- **Evidence for.** Closest peer-reviewed motivation result is within-game (Berger & Pope; see B3), which failed NCAA replication.
- **Evidence against.** NFL divisional rematches (practitioner, Pinnacle closes 2012+): the revenge team did 1.28 points per game *worse* (n.s.); the spread put no weight on revenge; rematches where the home team won the first meeting went 2.8 points under (p ≈ 0.005) ([Quantum Sports Solutions](https://www.quantumsportssolutions.com/blogs/handicappers-library/nfl-betting-angles-fact-or-fiction-10-revenge)). NHL, 285 blowouts: losers won their next game 50.0%, not significant (OR 1.23, CI 0.88-1.71) ([Chachad et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC10800907/)). Men's college basketball repeat meetings: better team won 54.7% of first and 54.1% of repeat meetings (FiveThirtyEight, **unverified**: page redirects). No peer-reviewed basketball revenge study found. Data-mined systems (e.g. double-digit road dog after a 15+ point loss as a favourite, 42-21 ATS, n = 63) are likely overfit ([procomputergambler](https://www.procomputergambler.com/ncaab-public-betting-ranked-team-ats-trends/)).
- **Does the market price it?** NFL: the spread ignores revenge, and the effect is null.
- **How we would test it.** **PBP + closing lines**, pooled D-I: margin minus spread on "lost previous meeting", previous margin, days since, venue swap; secondary outcomes first-half residual and first-4-minute margin. **Video** adds effort proxies (sprint counts, deflections) for MSU's Big Ten rematches.
- **Proposed hypotheses.** **new-41:** In same-season rematches, the team that lost the first meeting has a positive margin-minus-spread residual. **new-42:** Any rematch effect shows up in the first 4 minutes of each half.
- **Verdict.** **Untested in basketball** (null in NFL practitioner data and NHL, n = 285 blowouts).

## H2. Letdown and look-ahead ("trap") games

- **Belief.** After a big or emotional win a team underperforms (letdown); before a marquee game it underperforms against a weaker opponent (look-ahead).
- **Who holds it.** Coaches, media, handicappers.
- **Claimed effect and size.** Unquantified.
- **Evidence for.** Winfree (2020, *J. Sports Economics*, college football): a close previous game hurts next-game performance; previous opponent strength matters ([IDEAS](https://ideas.repec.org/a/sae/jospec/v21y2020i5p477-492.html); abstract only). CFB Elo analysis: teams favoured in consecutive games did worse in the second, within the margin of error ([Staturdays](https://staturdays.com/2020/11/06/cfb-mythbusters-the-big-win-hangover/)).
- **Evidence against.** Same CFB analysis: no hangover after big wins ([Staturdays](https://staturdays.com/2020/11/06/cfb-mythbusters-the-big-win-hangover/)). NHL: no change after blowout wins (53.15%, n.s.) ([Chachad et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC10800907/)). Harvard football letdown post (82.2% of 242 games, n.s.) **unverified** (HTTP 500).
- **Does the market price it?** Unknown for NCAAB.
- **How we would test it.** **PBP + schedule + lines + polls**: flag letdown games (after a top-25 win, a 10+ point cover, or a one-possession/OT game) and look-ahead games (next opponent ranked or rival, current opponent below a rating cut-off); regress ATS residual.
- **Proposed hypotheses.** **new-43:** After a one-possession or overtime game, a team's next-game ATS residual is negative. **new-44:** The ATS residual is negative when the next opponent is ranked and the current one is unranked.
- **Verdict.** **Untested** in basketball (mixed in football).

## H3. Rivalry games: underdogs play above themselves

- **Belief.** "Throw out the records"; rivalry underdogs cover or win more than the spread implies.
- **Who holds it.** Fans, media, bettors.
- **Evidence for.** Winfree (2020, CFB): rivalry games are harder to predict (more variance, not ATS bias) ([IDEAS](https://ideas.repec.org/a/sae/jospec/v21y2020i5p477-492.html)). Shank (2019, NFL 2003-2016): home teams vs division rivals less likely to cover; divisional games less likely to go over; about 57% out-of-sample ([Emerald](http://www.emerald.com/sef/article/36/4/567-580/353529); abstract only).
- **Evidence against.** NCAA men's basketball, 139 games across 17 rivalries: underdogs covered 46.7%, not different from 50% (Harvard Sports Analysis 2014, **unverified**: HTTP 500, snippet). No peer-reviewed NCAAB rivalry-ATS study.
- **Does the market price it?** NCAAB unknown; NFL familiarity partly mispriced.
- **How we would test it.** **PBP + lines + a rivalry list** (curated, e.g. MSU-Michigan; or data-driven): ATS residual, total residual, and absolute residual (variance).
- **Proposed hypothesis.** **new-45:** In NCAAB rivalry games, the variance of margin minus spread is larger than in matched non-rivalry conference games, and the underdog's mean ATS residual is not above zero.
- **Verdict.** **Mixed** (variance claim plausible from football; underdog-cover claim unsupported on weak evidence).

## H4. Jersey colour (red or dark uniforms) — attach to existing H8

- **Belief.** Teams in red or dark uniforms win more or are called for more fouls.
- **Who holds it.** Fans, some coaches, the uniform industry.
- **Evidence for.** Frank & Gilovich (1988, *JPSP*), NFL 1970-1986 and NHL 1970-71 to 1985-86: black-uniformed teams near the top in penalties; when Pittsburgh and Vancouver switched to black, penalties rose at once; lab experiments point to both referee bias and wearer aggression ([PDF](https://people.uncw.edu/tothj/PSY355/Frank-Black%20Uniforms-JPSP-1988.pdf)); Penguins about 8 to 12 penalty minutes per game ([Psychology Today](https://www.psychologytoday.com/us/blog/attitude-check/201610/do-uniform-colors-matter-in-sports)). Hill & Barton (2005, *Nature*), Olympic combat sports: red won 55% of bouts **(unverified)**.
- **Evidence against (basketball, peer-reviewed).** Goldschmied & Spitznagel (2021, *European J. Sport Science* 21(1): 93-99), women's NCAA tournament 2012-2019: no effect of uniform colour on winning, across colours and with ranking controlled ([abstract](https://lida.sport-iat.de/dbb/Record/4058702)). A 2014 AAHPERD abstract (one D-I school) found no colour-foul relationship **(unverified)**. Rugby league red link mixed after team controls (Savage et al., **unverified**; [CREMA page not opened](https://www.crema-research.ch/?p=3581)).
- **Confound.** College home teams usually wear light uniforms, so "dark" tracks playing away; alternates are chosen for big games. H8 already controls home/away.
- **Does the market price it?** No evidence.
- **How we would test it.** **PBP + one video frame per game** (or a uniform-tracker site): margin minus spread and team fouls, venue fixed; within-team comparisons across colourways.
- **Proposed hypothesis.** Attach to **H8**. Optional **new-46:** With venue fixed, team fouls per 100 possessions do not differ by uniform darkness.
- **Verdict.** **Not supported for winning** (one peer-reviewed women's NCAA tournament study); men's and foul effects **untested**.
- **Addition 2026-10-18.** Large-sample NHL evidence (Webster, Urland & Correll 2012), a Chinese basketball league study and soccer nulls; within-team design for new-46: see "Additions 2026-10-18", H4 / H8 addition.

## H5. "Defense wins championships"

- **Belief.** Elite defense matters more than elite offense for titles; defense "travels" in March.
- **Who holds it.** Coaches (an MSU staple), media.
- **Evidence for.** CBS (2013; KenPom 2004-2012; seeds 1-6): above-median defenses beat seed expectation by +0.166 wins per tournament vs +0.072 for above-median offenses; above-median defenses won 7 of 9 titles ([CBS Sports](https://www.cbssports.com/college-basketball/news/offense-may-be-more-important-than-defense-in-ncaa-tournament)). NBA (632 playoff teams since 1971): defense predicts playoff success, at a similar rate to offense ([Otten, The Conversation](https://theconversation.com/does-defense-actually-win-championships-89628)).
- **Evidence against.** AP (KenPom): 17 of the last 20 champions were top-10 in adjusted offense; 10 of 20 were outside the top 10 in defense ([Press Herald 2023](https://www.pressherald.com/2023/03/31/ncaa-mens-basketball-offense-efficiency-not-defense-wins-championships/)). CBS 2013: 8 of 9 champions had above-median offense ([CBS](https://www.cbssports.com/college-basketball/news/offense-may-be-more-important-than-defense-in-ncaa-tournament)). Sutton (2024, NBA): no evidence defense "clearly and unmistakably matters more" ([Wikipedia](https://en.wikipedia.org/wiki/Defense_wins_championships)). No peer-reviewed NCAAB study.
- **Does the market price it?** Unknown; the CBS result is vs seed, not market; tournament market shows little seed bias ([Hickman 2020](https://ideas.repec.org/a/spr/jecfin/v44y2020i3d10.1007_s12197-020-09507-7.html)).
- **How we would test it.** **PBP + ratings + lines**: tournament ATS residual on pre-tournament adjusted offense and defense, total rating fixed; variance of defensive vs offensive efficiency, neutral vs non-neutral. **Video** adds closest-defender distance at release (m; shared definition) to separate defense from opponent shooting luck.
- **Proposed hypotheses.** **new-49:** With total rating fixed, a defense-heavy profile does not predict a positive ATS residual in NCAA tournament games. **new-50:** Game-to-game variance in defensive PPP is lower than in offensive PPP, for D-I teams and for MSU.
- **Verdict.** **Not supported** as stated; balance wins and elite offense looks necessary.

## H6. Experience: seniors and upperclassmen win in March

- **Belief.** Experienced teams handle March pressure better.
- **Who holds it.** Coaches, media, bracket analysts.
- **Evidence for.** Pifer, DeSchriver, Baker & Zhang (2019, *J. Sports Analytics* 5: 137-152), 693 men's tournament games 2007-2017: prior tournament minutes among top players raise margin in later rounds (details via the replication thesis; publisher pages 403). Roberts (UNC MA thesis 2022, women's replication, n = 189): top-5 prior tournament minutes predicted winning (OR 1.009 per minute, p = 0.046) and margin (+0.046 points per minute of difference, p = 0.003) ([thesis PDF](https://cdr.lib.unc.edu/downloads/1g05fn40t)).
- **Evidence against.** Class year shows no effect in either study ([thesis PDF](https://cdr.lib.unc.edu/downloads/1g05fn40t)). ESPN (2006): upper-class-dominant teams now underperform seed ([ESPN](https://www.espn.com/mens-college-basketball/ncaatourney06/insider/news/story?id=2329124)); a conflicting ESPN claim **unverified**. Portal era: 2023 teams averaged 2.29 years experience and 46.3% minutes continuity ([Bless Your Chart](https://blessyourchart.substack.com/p/022-more-experience-but-less-continuity)), so older results may not transfer.
- **Does the market price it?** Not studied.
- **How we would test it.** **Box scores + lines**: cumulative prior-tournament minutes for each team's top 5; margin and ATS residual, ratings controlled, early vs later rounds.
- **Proposed hypothesis.** **new-51:** The top-5 prior-tournament-minutes difference predicts a positive ATS residual in NCAA tournament games, especially from the Sweet 16 on; class year does not.
- **Verdict.** **Mixed** (prior tournament minutes: supported vs win/margin; class year: not supported).

## H7. Veteran tournament coaches beat expectations

- **Belief.** Coaches with many appearances win more than seed or rating predicts.
- **Who holds it.** Media, fans, bettors.
- **Evidence for.** Torvik 2000-2026: Izzo PAKE +13.3, PASE +16.5 (79 games); Roy Williams PAKE +13.1; Boeheim +9.0; Calipari +9.0 ([BartTorvik](https://barttorvik.com/cgi-bin/ncaat.cgi?type=coach)). Paine (2011, seed model fitted on 1,686 games, 1985-2010), tournament-level metric (expected wins including later rounds): Izzo +12.52 (14 tourneys), Krzyzewski +11.91 (25); game-based metric: Izzo +6.14, Krzyzewski +7.91 ([Basketball-Reference blog](https://www.basketball-reference.com/blog/indexb6a4.html?p=9088)).
- **Evidence against.** Large negative tails for long-tenured coaches: tournament-level metric Keady -7.78 (15 tourneys), Barnes -4.66 (19); game-based Keady -3.07, Barnes -4.31 ([Paine](https://www.basketball-reference.com/blog/indexb6a4.html?p=9088)); Bennett -7.7, Dixon -6.1, Painter -4.6 ([Saturday Down South](https://www.saturdaydownsouth.com/news/college-basketball/which-coaches-historically-beat-expectations-during-the-ncaa-tournament/)). Seed-based metrics mix coaching with seeding error ([Spartans Illustrated](https://spartansillustrated.com/articles/tom-izzo-rertospective-part-three-advanced-ncaa-tournament-performance-metrics)). Over-performance is not stable (Krzyzewski 1985-95 vs 1996-2005) ([ESPN 2006](https://www.espn.com/mens-college-basketball/ncaatourney06/insider/news/story?id=2329124)). Peer-reviewed coach work is thin (Fizel & D'Itri 1997, retention, not tournaments; [IDEAS](https://ideas.repec.org/a/wly/mgtdec/v18y1997i4p295-308.html)).
- **Does the market price it?** Not studied.
- **How we would test it.** **Ratings + lines**, pooled tournament games: ATS residual on coach's prior appearances and prior-years PAKE (out-of-sample), hierarchical shrinkage.
- **Proposed hypothesis.** **new-52:** A coach's prior-years PAKE predicts his next tournament's ATS residual after shrinkage (null: market already prices it).
- **Verdict.** **Mixed** (specific coaches, not tenure, drive it).

## H8. "Hot team entering March"

- **Belief.** Teams finishing strong carry momentum into the NCAA tournament.
- **Who holds it.** Media, fans, bettors, the selection committee.
- **Evidence for.** Stone & Arkes (2018, *Economic Inquiry* 56(3): 1724-1747): recent form predicts tournament wins; the committee underreacts; betting markets incorporate it efficiently ([IDEAS](https://ideas.repec.org/a/bla/ecinqu/v56y2018i3p1724-1747.html)). NBA 2007-2009: positive between-game momentum, +2.2 to +2.8 pp (Model A) or +3.3 to +4.0 pp (Model B) win probability per extra win in the previous 5 games (N = 3,452) (numbers from the [Calhoun PDF](https://calhoun.nps.edu/server/api/core/bitstreams/690c7519-7c43-4d43-baa5-e47ee742b53f/content); [IDEAS](https://ideas.repec.org/a/bpj/jqsprt/v7y2011i3n13.html) for the citation only). Of 10 champions only UConn 2011 lost more than half its last 10 (descriptive) ([ESPN 2016](https://www.espn.com/blog/collegebasketballnation/post/_/id/111975/on-the-quad-does-regular-season-momentum-equate-to-postseason-success)).
- **Evidence against.** 18 slumping at-large teams won 20 tournament games vs 4 expected by seed (tiny, seed-based) ([Paint Touches 2022](https://painttouches.com/2022/03/15/is-momentum-a-thing-going-into-the-ncaa-tournament/)). Four 5-5 finishers reached Final Fours 2011-2013 ([ESPN 2016](https://www.espn.com/blog/collegebasketballnation/post/_/id/111975/on-the-quad-does-regular-season-momentum-equate-to-postseason-success)).
- **Does the market price it?** **Yes, for the NCAA tournament** ([Stone & Arkes](https://ideas.repec.org/a/bla/ecinqu/v56y2018i3p1724-1747.html)). NBA regular season: bettors over-bet streaks, closing line near efficient ([Paul, Weinbach & Humphreys 2014](https://ideas.repec.org/a/sae/jospec/v15y2014i6p636-649.html)); betting against streaks profitable in 1995-2002 ([Paul & Weinbach 2005](https://ideas.repec.org/a/sae/jospec/v6y2005i4p390-400.html)); betting with 4+ game streaks 56.5% ATS 2001-2013 (single blog-tier result, [Byrnes & Farinella](https://thesportjournal.org/article/the-effect-of-momentum-on-the-nba-point-spread-market/)).
- **How we would test it.** **PBP + ratings + lines**: last-30-day minus season adjusted efficiency entering the tournament, vs margin residual and ATS residual.
- **Proposed hypothesis.** **new-53:** Late-season form predicts tournament margin beyond season ratings but not ATS.
- **Verdict.** **Supported** (predictive), and **priced** by the market.

## H9. "Never bet against Izzo in March"

- **Belief.** Izzo's MSU teams outperform seed and market in March, so backing them pays.
- **Who holds it.** Fans, media, bettors.
- **Evidence for (vs seed and ratings).** Torvik 2000-2026: Izzo PASE +16.5 (highest of any coach), PAKE +13.3 (rank 1), 55-24 in 79 games ([BartTorvik](https://barttorvik.com/cgi-bin/ncaat.cgi?type=coach)); PASE 15.4 (2000-2023) ([Saturday Down South](https://www.saturdaydownsouth.com/news/college-basketball/which-coaches-historically-beat-expectations-during-the-ncaa-tournament/)); Paine tournament-level metric +12.52 wins (14 tourneys, 1985-2010; game-based metric +6.14) ([Paine](https://www.basketball-reference.com/blog/indexb6a4.html?p=9088)); PASE +17.10, PAD +9.86, KenPom-based PAKE +5.83 ([Spartans Illustrated](https://spartansillustrated.com/articles/tom-izzo-rertospective-part-three-advanced-ncaa-tournament-performance-metrics)); Torvik 2000-2025 PAKE 13.2 ([SI 2025](https://www.si.com/college/michiganstate/basketball/spartans-tom-izzo-ncaa-tournament--mike-krzyzewski-roy-williams)). Record 61-27 (.693; 88 games), 28 straight NCAA appearances, 8 Final Fours ([MSU Athletics bio](https://msuspartans.com/staff.aspx?staff=189); streak also in [MSU Athletics, 15 Mar 2026](https://msuspartans.com/news/2026/3/15/mens-basketball-spartans-earn-no-3-seed-in-east-region-extend-ncaa-tournament-streak-to-28-straight)). The [Wikipedia page](https://en.wikipedia.org/wiki/Tom_Izzo) is internally inconsistent (infobox 61-27, body 54-23; lead 28 straight, a later section 27) and is not used for the count. The two PAKE figures (+13.3 vs +5.83) disagree and need reconciliation.
- **Evidence against (market).** Round of 64: 15-11 ATS (57.7%), one-sided binomial p = 0.28 ([FOX Sports 2026](https://www.foxsports.com/stories/college-basketball/2026-march-madness-first-round-betting-trends)); 11-10 ATS as lower seed since 2007 ([Action Network 2024](https://www.actionnetwork.com/ncaab/mississippi-state-vs-michigan-state-odds-opening-spread-predictions-for-2024-ncaa-tournament)); 14-9 first-round ATS **unverified**. **No full-tournament ATS record was found.** Part of the seed over-performance is committee under-seeding ([Spartans Illustrated](https://spartansillustrated.com/articles/tom-izzo-rertospective-part-three-advanced-ncaa-tournament-performance-metrics)), irrelevant to spreads. Public money follows ranked and TV teams ([Humphreys et al. 2013](http://g.espncdn.com/s/betting/HCB2013.pdf?addata=2014%3Dbettingpapers_Humphreys)), so MSU lines may be shaded against backers. Tournament market efficient; only the ACC anomaly reported ([Hickman 2020](https://verso.uidaho.edu/esploro/outputs/journalArticle/Efficiency-in-the-madness-examining-the/996651783101851)).
- **Does the market price it?** **Unknown** at full-tournament level.
- **How we would test it.** **Lines only** for the cover test: closing spreads for all 88 Izzo tournament games; cover rate and mean ATS residual with bootstrap CI (SE about 5.3 pp, so only an edge above about 10 pp is significant); pair with new-52. **PBP + video** to decompose any edge (defense, rebounding, free-throw rate, late-game execution, preparation-dependent sets).
- **Proposed hypotheses.** **new-58:** MSU under Izzo has a positive mean ATS residual in NCAA tournament games (n = 88; descriptive). **new-59:** MSU's tournament efficiency margin exceeds its season-adjusted margin, concentrated on defense or rebounding (PBP; video for contest distance in m).
- **Verdict.** **Supported** vs seed and ratings; **untested** vs the market.

---

# Theme I. Betting-market beliefs

## I1. Favourite-longshot bias (moneylines)

- **Belief (market).** Longshots are overpriced and heavy favourites underpriced.
- **Who holds it.** Market researchers, sharp bettors.
- **Evidence for.** Berkowitz, Depken & Gandar (2017, *QREF* 63: 233-239): the bias persists in NCAAB and NCAAF moneylines; heavy favourites return about 0 ([IDEAS](https://ideas.repec.org/a/eee/quaeco/v63y2017icp233-239.html)). Robbins (2023, *American J. Management* 23(2)), 62,106 CBB games 2007-08 to 2022-23: CBB shows "the most significant longshot bias" of the sports examined; biggest-longshot bin about -50% return vs -0.2% for the matching favourite bin; average return -7.71% vs average hold -3.56% ([PDF](https://myweb.ecu.edu/robbinst/PDFs/Weak%20Form%20Efficiency%20in%20Sports%20Betting%20Markets.pdf)).
- **Evidence against.** Not exploitable after vig (both studies).
- **Does the market price it?** **Documented mispricing**, not exploitable. Implication: de-vig CBB moneylines with power or Shin methods, not proportional normalisation (`odds_markets_research.md`).
- **How we would test it.** **Moneylines + results** (no video), 2021-2026, Robbins' binning.
- **Proposed hypothesis.** **new-54:** Post-2021 NCAAB moneylines still show a favourite-longshot bias.
- **Verdict.** **Supported.**

## I2. Big favourites fail to cover (and point shaving)

- **Belief.** Big underdogs cover more than half the time; some say because of point shaving.
- **Evidence for.** Wolfers (2006): favourites of more than 12 points (n = 9,244) covered 48.37%; 46.2% won without covering vs 40.7% in a comparison band; read as shaving in about 6% of strong-favourite games ([PDF](https://www.stat.berkeley.edu/~aldous/157/Papers/PointShaving.pdf)). Paul & Weinbach (2005, *J. Econ. & Finance* 29(3)): dogs of 20+ reject a fair bet ([IDEAS](https://ideas.repec.org/a/spr/jecfin/v29y2005i3p403-408.html)). Paul, Weinbach & Paul (2012), 12,644 games 2004-07: dogs of more than 8 covered 51.59% (p < .05), below 52.38% break-even ([PDF](https://buildingthepride.com/jobie/uploads/JOBIEV17J139.pdf)). Boyd's Bets: favourites cover 46.5-47.0% at -12 to -14 since 2006 ([Boyd's Bets](https://www.boydsbets.com/college-basketball-ats-records-point-spread/)). FOX: round-of-64 20+ point dogs 51.9% ATS since 1985 ([FOX Sports](https://www.foxsports.com/stories/college-basketball/2026-march-madness-first-round-betting-trends)). Large dogs profitable over 19 years per BestOdds (no numbers) ([Boardroom](https://boardroom.tv/college-basketball-underdog-cover-odds/)).
- **Evidence against (point-shaving reading).** Gregory (2018, *Quantitative Economics*): optimal in-game strategy reproduces the skew; the skewness test "detects" shaving in about 7% of big-favourite games with none present ([PDF](https://users.ssc.wisc.edu/~jmgregory/Gregory_pointshaving.pdf); [journal page](https://econometricsociety.org/publications/quantitative-economics/2018/07/01/Do-basketball-scoring-patterns-reflect-illegal-point-shaving-or-optimal-ingame-adjustments)). Bernhardt & Heston (2010): the same patterns appear in games without betting ([UMD summary](https://rhsmith.umd.edu/news/past-study-point-shaving-gives-context-fbi-gambling-probe)), which also notes a 2025 FBI probe with 30+ arrests in 11 states. Borghesi, Paul & Weinbach (2010): outcomes are not symmetric around the line ([IDEAS](https://ideas.repec.org/a/buc/jpredm/v4y2010i2p15-22.html)).
- **Does the market price it?** Mild mispricing (dogs cover about 51.6-52.8%), cause disputed, rarely above break-even.
- **How we would test it.** **Lines + scores**: cover rate by spread band, 2021-2026.
- **Proposed hypothesis.** **new-57:** Underdogs of more than 12 points cover more than 50% in 2021-2026 D-I data.
- **Verdict.** **Mixed** (small cover edge for big dogs; point-shaving interpretation not supported).

## I3. Home underdogs are undervalued

- **Belief.** Home underdogs are undervalued (Levitt-type bias).
- **Evidence for.** Paul & Weinbach (2005a): big underdogs, especially home dogs, profitable 1996-2004 (as described in [Paul, Weinbach & Paul 2012](https://buildingthepride.com/jobie/uploads/JOBIEV17J139.pdf)). Levitt 2004 NFL contest data: selected home-dog bets won 57.7% ([loserwins](https://loserwins.com/data-analysis/underdog-win-rates-by-sport/)).
- **Evidence against.** 2004-07: home dogs 1,456-1,487 (49.47%) ([PWP 2012](https://buildingthepride.com/jobie/uploads/JOBIEV17J139.pdf)). November 2012 to January 2018: home dogs 2,821 of 5,713 (49.4%) ([Gamblers Analytics](https://gamblersanalytics.com/category/college-basketball/)). NCAAB home-team bias "runs opposite" to other sports ([Paul & Weinbach 2005](https://ideas.repec.org/a/spr/jecfin/v29y2005i3p403-408.html)).
- **Does the market price it?** **Priced** after 2004.
- **How we would test it.** **Lines + scores**, by home/road and spread band (covered under new-57 and the replication plan in I4).
- **Verdict.** **Not supported** in post-2004 NCAAB.

## I4. Ranked, public and televised teams are overpriced

- **Belief.** Famous teams (Duke, Kentucky, Michigan State) attract public money, inflating their lines, so fading them pays.
- **Evidence for.** Humphreys, Paul & Weinbach (2013, *J. Economic Psychology* 39: 376-386), about 3,000 games in 2008-09: bet volume rises with Top-25 votes (+2.6 bets per vote point) and TV (network +2,566 bets; ESPN family +1,749; Big Ten Network listed); bets on home teams won 48.3%, on favourites 48.6% ([PDF](http://g.espncdn.com/s/betting/HCB2013.pdf?addata=2014%3Dbettingpapers_Humphreys)). Bet share on the favourite = 56.0 + 0.4288 × spread + 10.21 if the favourite is on the road ([PWP 2012](https://buildingthepride.com/jobie/uploads/JOBIEV17J139.pdf)). Data-mined "ranked road fade" 1,381-960 (59.0%) since 2003 ([procomputergambler](https://www.procomputergambler.com/ncaab-public-betting-ranked-team-ats-trends/)); heavy selection risk.
- **Evidence against.** Contrarian (under 25% of bets) regular season 3,075-3,043 (50.3%, ROI -1.8%); profit only in the most heavily bet games (33-21) ([Sports Insights](https://www.sportsinsights.com/blog/betting-against-the-public-in-heavily-bet-ncaab-games/)). Closing line not greatly biased despite lopsided action ([PWP 2012](https://buildingthepride.com/jobie/uploads/JOBIEV17J139.pdf)).
- **Does the market price it?** Volume follows ranked/TV teams; ATS mispricing unproven.
- **How we would test it.** **Lines + polls + TV metadata** (+ public-bet share if licensed).
- **Proposed hypothesis.** **new-55:** Ranked or nationally televised teams have a negative mean ATS residual, spread band controlled.
- **Verdict.** **Mixed** (behaviour supported; price effect not shown).

## I5. The market overreacts to the last result

- **Belief.** Fading recent extremes (blowouts, upsets) pays.
- **Evidence for.** NBA: betting against winning streaks profitable 1995-2002 ([Paul & Weinbach 2005](https://ideas.repec.org/a/sae/jospec/v6y2005i4p390-400.html)). College football: momentum handled inefficiently, especially negative momentum ([Cox et al. 2021](https://ideas.repec.org/a/sae/jospec/v22y2021i3p251-273.html)). Pre-game overreaction to momentum reversed by outcomes ([Moskowitz](https://w4.stern.nyu.edu/finance/docs/pdfs/Seminars/moskowitz_seminar_paper.pdf)). Postseason "off a win but ATS loss" filtered to 122-78-5 (data-mined) ([Action Network](https://www.actionnetwork.com/ncaab/public-betting-recency-bias-college-basketball-postseason)).
- **Evidence against.** Unfiltered version 496-482-25 (50.7%) ([Action Network](https://www.actionnetwork.com/ncaab/public-betting-recency-bias-college-basketball-postseason)). NBA: no profit with or against streaks ([PWH 2014](https://ideas.repec.org/a/sae/jospec/v15y2014i6p636-649.html)). Tournament momentum priced ([Stone & Arkes](https://ideas.repec.org/a/bla/ecinqu/v56y2018i3p1724-1747.html)). Gray & Gray 1997 NFL **unverified**.
- **Does the market price it?** Unresolved for NCAAB regular season; priced in the tournament.
- **How we would test it.** **Lines + scores**: autocorrelation of ATS residuals.
- **Proposed hypothesis.** **new-56:** A team's ATS residual in game t is negatively related to its residual in game t-1.
- **Verdict.** **Untested** for NCAAB (mixed elsewhere).

## I6. Totals are shaded toward the over

- **Belief.** Bettors prefer overs, so totals are set high.
- **Evidence for.** Totals land "just under" more than "just over", consistent with over-shading ([Borghesi, Paul & Weinbach 2010](https://ideas.repec.org/a/buc/jpredm/v4y2010i2p15-22.html)). Unders 50.5% (n = 29,490); totals 150+ unders 52.7% (n = 2,964); non-conference 150+ 55.6% (n = 1,196) ([Sports Insights](https://www.sportsinsights.com/blog/betting-public-high-college-basketball-totals/); practitioner, data-mined).
- **Evidence against.** Overall unders barely above 50%; subgroup results are filtered.
- **Does the market price it?** Mild over-shading plausible; weak evidence.
- **How we would test it.** **Totals + scores**, 2021-2026 (no hypothesis proposed beyond the replication plan).
- **Verdict.** **Mixed.**

---

# Summary table

PBP = play-by-play (with box scores, schedule, lines where needed). Video = broadcast tracking. OCR = scoreboard reading.

| # | Belief | Verdict | Market prices it? | Test data | Proposed IDs |
|---|---|---|---|---|---|
| A1 | Hot hand | Mixed | Team streaks over-bet, close unbiased; in-play untested | FT: PBP; FG: video | new-1, new-2, new-3 |
| A2 | Make-or-miss league | Supported descriptively; causal reading untested | Team shooting priced; recency untested | PBP + video (shot quality); lines | new-9, new-10 |
| A3 | Live by the three | Mixed (size only from one blog simulation) | Variance pricing not studied | PBP + lines | new-14, new-15 |
| A4 | FT choking under pressure | Supported (small) | Not studied | PBP | new-16 |
| A5 | Icing the shooter | Not supported | Not studied | PBP | new-11 |
| B1 | Momentum and runs | Mixed (leans not) | Pre-game overreaction reversed; in-play untested | PBP; prediction-market prices | new-4, new-5, new-6 |
| B2 | Timeouts stop runs | Mixed (NCAA pre/post only) | Not studied | PBP; video for ATO sets | new-7, new-8 |
| B3 | Down one at half helps | Not supported | Not studied | PBP + 2H lines | new-22 |
| B4 | No lead is safe | Not supported | Implicit in-play | PBP | new-24 |
| C1 | Opening tip | Weakly supported, tiny (< 1 possession under the NCAA arrow; no verified men's NCAA estimate) | Props near 50-50 | PBP + lines; video for jumpers | new-12, new-13 |
| C2 | Win the rebounding battle | Mixed | Embedded in ratings | PBP; video for crash/retreat | new-17, new-18 |
| C3 | Bench a two-foul starter | Mixed | Not studied | PBP | new-19, new-20 |
| C4 | Foul up 3 late | Mixed (NCAA split; NBA near zero) | Not studied | PBP + OCR | new-21 |
| C5 | Two-for-one | Plausible (NBA preprint; NCAA practitioner +0.25 possession, 35 s clock) | Not studied | PBP + OCR | new-25 |
| C6 | Hack-a-Shaq | Untested | Not studied | PBP | none |
| D1 | In-game fatigue | Mixed | Not studied | Video/tracking | new-26 |
| E1 | HCA about 3 points; fortress arenas | Supported (avg); not supported (fortress) | Yes | PBP | new-27 |
| E2 | HCA declining | Supported | Yes | PBP | new-28 |
| E3 | HCA front-loaded | Untested (NCAA) | First-half pricing unstudied | PBP | new-29 |
| E4 | Crowds cause HCA | Supported (partial; ≥ ~30% NCAA lower bound) | Europe priced at once; NCAA unstudied | PBP + attendance | new-30 |
| E5 | Altitude | Mixed | Partly | PBP + elevation | new-37 |
| E6 | Shooting backgrounds / domes | Not supported (midfield); mixed (corner, backdrops); practitioner evidence only | Not documented | PBP + venue; video for backdrops | new-47, new-48 |
| E7 | Senior night | Untested | Football: priced/absent | PBP + lines | new-38 |
| E8 | Tournament proximity: pseudo-home crowd near campus (added 2026-10-18) | Mixed | Partly; residual untested | PBP + coordinates + seeds, ratings, lines | new-60 |
| F1 | Referee home bias | Supported | Avg HCA priced | PBP + attendance + crews; video | new-31 |
| F2 | Make-up calls | Mixed | Not studied | PBP | new-23, new-32 |
| F3 | Star treatment | Mixed | Not studied | Video + PBP | new-33 |
| F4 | Refs favour trailing team | Mixed | Not studied | PBP | new-34 |
| F5 | Referee crew moves fouls, FTs and totals (added 2026-10-18) | Supported for fouls; untested for totals | Unknown | PBP + crew names + closing totals | new-61 |
| G1 | Travel and time zones | Mixed | Partly | PBP + coordinates + tip times | H10 (refined), new-35 |
| G2 | Rest and short turnarounds | Mixed | NBA partly; NCAA about 0.45 pt shading | PBP + schedule; video for load | new-36 |
| G3 | Conference-tournament fatigue | Not supported on indirect evidence; fatigue itself untested | Yes, largely | PBP + lines | new-39 |
| G4 | Byes: rest vs rust | Untested | Possibly underprices rest (unverified) | PBP + lines | new-40 |
| H1 | Revenge games | Untested in basketball (NFL, NHL null) | NFL: ignored, null | PBP + lines | new-41, new-42 |
| H2 | Letdown / look-ahead | Untested (basketball) | Unknown | PBP + lines + polls | new-43, new-44 |
| H3 | Rivalry underdogs | Mixed | NCAAB unknown; NFL familiarity mispriced | PBP + lines | new-45 |
| H4 | Jersey colour | Not supported for winning (women's NCAA); men's and fouls untested | No evidence | PBP + one video frame | H8, new-46 |
| H5 | Defense wins championships | Not supported | Unknown | PBP + ratings + lines; video | new-49, new-50 |
| H6 | Experience in March | Mixed | Not studied | Box + lines | new-51 |
| H7 | Veteran coaches | Mixed | Not studied | Ratings + lines | new-52 |
| H8 | Hot team entering March | Supported | Yes (tournament) | PBP + ratings + lines | new-53 |
| H9 | Never bet against Izzo in March | Supported vs seed/ratings; untested vs market | Unknown | Lines; PBP + video to explain | new-58, new-59 |
| I1 | Favourite-longshot bias | Supported | Mispriced, not exploitable | Moneylines | new-54 |
| I2 | Big favourites fail to cover / shaving | Mixed | Mild mispricing | Lines + scores | new-57 |
| I3 | Home underdogs undervalued | Not supported (post-2004) | Priced | Lines + scores | none |
| I4 | Ranked/public/TV teams overpriced | Mixed | Volume yes; price effect unproven | Lines + polls + TV | new-55 |
| I5 | Overreaction to last result | Untested (NCAAB) | Unresolved | Lines + scores | new-56 |
| I6 | Totals shaded to the over | Mixed | Mild, weak evidence | Totals + scores | none |

## Renumbering key (research-batch IDs to register IDs)

The three research batches each numbered from new-1. Register IDs: batch 1 (in-game) new-1 to new-26 unchanged; batch 2 (venue, officials, schedule) new-1 to new-14 became new-27 to new-40; batch 3 (psychology, narrative, markets) new-1 to new-19 became new-41 to new-59.

## Gaps

- No peer-reviewed NCAA study found for: in-game field-goal hot hand; rest, Saturday-Monday turnarounds, travel or time zones in the men's regular season; revenge, letdown/look-ahead, rivalry ATS, men's jersey colour, near-background arena effects, coach-tenure ATS, Izzo ATS; senior night; byes. These are open questions our PBP, video and closing-line data can answer.
- No peer-reviewed study of in-play pricing of any in-game basketball belief.
- (Added 2026-10-18.) Timeouts: peer-reviewed NCAA studies do exist (Mace et al. 1992; Roane et al. 2004) but are small pre/post designs; see "Additions 2026-10-18", which also lists what is still missing after the gap-filling pass.
- Most market papers use 1996-2007 offshore data; every market finding needs replication on 2021-2026 legal-market lines.
- Practitioner betting "systems" are data-mined filters without out-of-sample tests; treat them as hypotheses at best.
- Inaccessible primaries (claims marked unverified): KenPom dome-background post (?p=281; the foul-up-3 and two-for-one posts were read from web.archive.org on 2026-10-18), McCartney tip study (404), SSRN, several ScienceDirect, SAGE, Taylor & Francis, MDPI and Nature pages (403), Harvard Sports Analysis posts returning HTTP 500, Winthrop 2014 PDF, FiveThirtyEight third-meeting piece (redirect), Charest et al. 2021, Jones 2007/2008, Roy & Forest journal version, Noecker & Roback 2012.

---

# Sources

Every URL below was opened during the research for this task, except those explicitly listed under "Not opened". Pages whose live site is dead or blocked (kenpom.com blog: HTTP 403; harvardsportsanalysis.org: HTTP 500; fivethirtyeight.com: redirects) are cited by the exact web.archive.org snapshot that was read; these snapshots were re-opened and checked on 2026-10-18.

## Repository context (read)

- `coord/prompts/002-claude-code-taxonomy-and-markets.md` (Jobs C and E)
- `docs/requirements.md` (hypothesis registry H1-H10)
- `docs/research/odds_markets_research.md`

## Theme A-D sources (in-game)

- https://arxiv.org/pdf/1902.01265
- https://ar5iv.labs.arxiv.org/html/1902.01265
- https://www.sloansportsconference.com/research-papers/the-hot-hand-a-new-approach-to-an-old-fallacy
- https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc2208061b_2014_SSAC_The-Hot-Hand-A-New-Approach.pdf
- https://www.nber.org/system/files/working_papers/w26510/w26510.pdf
- https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0261890
- https://ideas.repec.org/a/eee/eecrev/v138y2021ics0014292121001240.html
- https://arxiv.org/abs/2011.04384
- https://en.wikipedia.org/wiki/Hot_hand
- https://www.inverse.com/article/29553-march-madness-ncaa-tyler-dorsey-hot-hand-oregon-ducks-streak
- https://www.psychologicalscience.org/publications/observer/obsonline/the-cold-truth-about-heating-up-on-the-court.html
- https://authors.library.caltech.edu/22148
- https://thesportjournal.org/article/the-effect-of-momentum-on-the-nba-point-spread-market/
- https://ideas.repec.org/a/buc/jgbeco/v5y2011i2p42-56.html
- https://ideas.repec.org/a/sae/jospec/v15y2014i6p636-649.html
- https://sites.ualberta.ca/~econwps/2011/wp2011-16.pdf
- https://calhoun.nps.edu/server/api/core/bitstreams/690c7519-7c43-4d43-baa5-e47ee742b53f/content
- https://w4.stern.nyu.edu/finance/docs/pdfs/Seminars/moskowitz_seminar_paper.pdf
- https://arxiv.org/abs/2605.00864
- https://arxiv.org/pdf/1903.08716
- https://arxiv.org/pdf/1109.2825
- https://arxiv.org/pdf/1503.03509
- https://www.slate.com/articles/sports/sports_nut/2008/03/the_lead_is_safe.html
- https://lida.sport-iat.de/dbb/Record/4082590?lng=en
- https://ar5iv.labs.arxiv.org/html/2011.11691
- https://ar5iv.arxiv.org/html/1205.1492
- https://www.sdabocconi.it/en/sda-bocconi-insight/knowledge/in-basketball-timeouts-stop-the-game-but-not-momentum/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC12554673/
- https://www.causeweb.org/usproc/sites/default/files/usresp/2019-1/An%20Examination%20of%20Timeout%20Value,%20Strategy,%20and%20Momentum%20in%20NCAA%20Division%201%20Mens%20Basketball.pdf
- https://www.frontiersin.org/articles/10.3389/fpsyg.2024.1412840/full
- https://lida.sport-iat.de/ta/Record/4085006
- https://www.theupside.us/p/upside-studies-icing-the-shooter
- https://freakonomics.com/2011/11/football-freakonomics-why-even-ice-a-kicker
- http://media.clemson.edu/economics/gated/data/golf/Performance%20Under%20Pressure%20NBA%20Journal%20of%20Sports%20Economics-2011-Zheng%20Cao-231-52.pdf
- https://wrap.warwick.ac.uk/168616/
- https://docs.iza.org/dp11761.pdf
- https://sabinanalytics.com/blog/2024/02:28:do-college-crowds-affect-free-throws/
- https://www.dickinson.edu/news/article/6001/dickinson_research_reveals_a_new_take_on_nba_tipoffs
- https://www.82games.com/random14.htm
- https://herhoopstats.substack.com/p/winning-the-tip
- https://en.wikipedia.org/wiki/Jump_ball
- https://www.bestodds.com/odds/nba/fb
- https://www.actionnetwork.com/nba/finding-edge-random-prop-nba-first-team-to-score
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11150523/
- https://www.inpredictable.com/2015/02/how-nba-games-are-won.html
- https://basketball-reference.com/about/factors.html
- https://www.espn.com/nba/insider/story/_/id/15456404/explaning-effects-shot-quality-shot-making-winning-games-nba
- https://thepowerrank.com/2020/07/28/predictability-vs-skill-in-sports-analytics-3-point-shooting/
- https://johngasaway.com/2018/02/27/is-uks-perimeter-d-good-or-lucky/
- https://www.binomialbasketball.com/p/the-nbas-3-point-variance-lie
- https://arxiv.org/abs/1512.05652
- https://arxiv.org/pdf/1512.05652
- https://supermariogiacomazzo.github.io/STOR538_WEBSITE/Articles/Basketball/Basketball_Kenter.pdf
- https://arxiv.org/pdf/2402.13289
- https://www.espn.com/nba/story/_/id/48582233/nba-playoffs-2026-foul-3-san-antonio-spurs-portland-trail-blazers-impact
- https://sloansportsconference.com/research-papers/how-much-trouble-is-early-foul-trouble
- https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc220807d3_SSAC11%20-%20Maymin%20Maymin%20and%20Shen%20-%20Early%20Foul%20Trouble%20-%20IJSF%202012.pdf
- https://engineering.nyu.edu/news/rethinking-foul-trouble
- https://hoopvision.substack.com/p/foul-trouble-and-the-auto-bench
- https://grantland.com/the-triangle/war-tom-izzo-michigan-state-spartans-rebounding/
- https://www.sloansportsconference.com/research-papers/to-crash-or-not-to-crash
- https://cdn.prod.website-files.com/68d6be744d7efccc2207f571/68d6be744d7efccc220807a3_SSAC13%20-%20To%20Crash%20or%20Not%20To%20Crash.pdf
- https://grantland.com/the-triangle/party-crashers-debunking-the-myths-of-offensive-rebounding-and-transition-defense/
- https://herhoopstats.substack.com/p/more-rebounds-more-wins-not-always
- https://sportsanalytics.studentorg.berkeley.edu/articles/a-tale-of-two-rebounds.html
- https://research.vu.nl/en/publications/does-losing-lead-to-winning-an-empirical-analysis-for-four-sports-2/
- https://knowledge.wharton.upenn.edu/article/is-this-madness-how-losing-by-just-a-little-can-help-a-team-or-company-win/
- https://lida.sport-iat.de/twm/Record/4016050?lng=en
- https://arxiv.org/abs/2412.08840
- https://ar5iv.labs.arxiv.org/html/2112.14649
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10974731/

## Theme E-G sources (venue, officials, schedule)

- https://web.archive.org/web/20210109050736/https://kenpom.com/blog/mining-point-spread-data-home-court-advantage/ (KenPom, 21 May 2018)
- https://web.archive.org/web/20201217063917/https://kenpom.com/blog/how-to-measure-home-court-advantage/ (KenPom, 27 Jul 2017; the old link kenpom.com/blog/?p=1774 redirects here)
- https://web.archive.org/web/20201217063910/https://kenpom.com/blog/how-to-measure-site-specific-home-court-advantage-part-two/ (KenPom, 7 Aug 2017)
- https://web.archive.org/web/20180719050613/https://kenpom.com/blog/road-teams-are-winning-more-often-in-college-too/ (KenPom, 8 Feb 2015; the old link kenpom.com/blog/?p=146 redirects here)
- https://web.archive.org/web/20190824065637/https://kenpom.com/blog/offense-vs-defense-block-percentage/ (KenPom, 7 Oct 2015, Offense vs. Defense summary table; the old link kenpom.com/blog/?p=85 redirects here)
- https://web.archive.org/web/20201217074226/https://kenpom.com/blog/how-much-is-air-worth/ (KenPom, 24 Jan 2012)
- https://web.archive.org/web/20201217072842/https://kenpom.com/blog/yet-another-study-about-fouling-when-up-3/ (KenPom, 12 Feb 2013)
- https://web.archive.org/web/20201217072142/https://kenpom.com/blog/investigating-the-value-of-twoforones/ (KenPom, 2 Jul 2013)
- https://kenpom.substack.com/p/is-home-court-advantage-stronger
- https://kenpom.com/trends.php (subscriber-only; snapshot URL not recorded, no figure in this register depends on it)
- https://vsin.com/college-basketball/determining-college-basketballs-true-home-court-advantage/
- https://www.cbssports.com/college-basketball/news/how-the-home-court-advantage-in-college-basketball-is-shrinking-this-season-due-to-fewer-fans-at-games
- https://spaces-cdn.owlstown.com/blobs/c31otj63qa356zwpeclkyawcy1bv
- https://www.samford.edu/sports-analytics/fans/2021/Did-Minimal-Crowds-in-2020-2021-Impact-College-Basketball-Home-Team-Performance
- https://herhoopstats.substack.com/p/ncaa-basketball-home-court-pandemic-fans
- https://pmc.ncbi.nlm.nih.gov/articles/PMC8282683/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC11503446/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC9517988/
- https://arxiv.org/pdf/2103.02832
- https://research.birmingham.ac.uk/en/publications/home-is-where-the-hustle-is-the-influence-of-crowds-on-effort-and/
- https://arxiv.org/abs/2210.13687
- https://arxiv.org/pdf/2210.13687
- https://www.sponet.de/sponet/Record/4016050?lng=en
- https://ar5iv.arxiv.org/html/1909.04817
- https://ideas.repec.org/a/bla/jemstr/v21y2012i1p271-300.html
- https://newrepublic.com/article/86559/basketball-referees-biased-nba-playoffs-study-espn-donaghy
- https://apbr.org/forum/viewtopic.php?p=7958
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6306443/
- https://lida.sport-iat.de/dbb/Record/4096166
- https://www.nbcsports.com/nba/news/nba-referees-are-biased
- https://digitalcommons.bryant.edu/eeb/vol14/iss1/9
- https://www.goodreads.com/author_blog_posts/5893028-how-do-you-explain-home-field-advantage
- https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2012.00346/full
- https://ca.sports.yahoo.com/news/do-makeup-calls-exist-131350055.html
- https://faculty.wharton.upenn.edu/wp-content/uploads/2012/04/Nba.pdf
- https://lida.sport-iat.de/dbb/Record/4003477?lng=en
- https://pmc.ncbi.nlm.nih.gov/articles/PMC7732833/
- https://bps.org.uk/research-digest/why-do-basketball-teams-have-home-court-advantage-natural-experiment-during
- https://aasm.org/nfl-nba-and-nhl-teams-have-a-disadvantage-when-traveling-west
- https://pmc.ncbi.nlm.nih.gov/articles/PMC7925613/
- https://ideas.repec.org/a/sae/jospec/v11y2010i6p602-613.html
- https://web.archive.org/web/20220517170805/https://harvardsportsanalysis.org/2011/01/back-to-back-blues-the-effect-of-road-trips-in-the-ivy-league/
- https://web.archive.org/web/20210128093705/http://harvardsportsanalysis.org/2018/03/march-madness-does-conference-tournament-timing-matter/
- https://web.archive.org/web/20210122215223/http://harvardsportsanalysis.org/2014/12/does-senior-day-matter-in-college-football/
- https://grantland.com/the-triangle/the-effects-of-the-compressed-schedule-examining-back-to-backs/
- https://herhoopstats.substack.com/p/ncaa-womens-basketball-back-to-backs-pace-fouls
- https://our.unc.edu/abstract/hayes-fighting-fatigue-investigating-factors-that-influence-3-point-percentage-in-ncaa-mens-basketball
- https://thesportjournal.org/article/evaluating-the-two-game-road-trip-in-college-sports-does-a-travel-partner-scheduling-approach-affect-team-competitiveness/
- https://esri.com/news/arcuser/1006/spatial-madness2of2.html
- https://pmc.ncbi.nlm.nih.gov/articles/PMC7739638/
- https://pmc.ncbi.nlm.nih.gov/articles/PMC7075230
- https://lida.sport-iat.de/ta/Record/4072988?lng=en
- https://www.frontiersin.org/articles/10.3389/fpsyg.2019.01100/pdf
- https://www.sciencedaily.com/releases/2007/12/071221094837.htm
- https://red.msudenver.edu/2018/advantage-altitude-exploring-the-largest-home-advantage-in-sports/
- https://arxiv.org/abs/1701.05976
- https://pmc.ncbi.nlm.nih.gov/articles/PMC6668839/
- https://www.nba.com/news/is-impact-of-denvers-altitude-fact-or-fiction
- https://nbcsports.com/nba/news/report-nba-trying-to-diminish-nuggets-home-court-advantage
- https://www.insidethehall.com/2022/03/13/2022-ncaa-tournament-first-look-wyoming-cowboys/
- https://dailybruin.com/2014/01/16/high-altitudes-to-give-colorado-home-court-edge-over-ucla
- https://www.thedp.com/blog/buzz/2012/03/senior-night-stats-revisted
- https://pittnews.com/article/19295/archives/march-madness-double-byes-a-tricky-part-of-big-east-tournament
- https://juicereel.beehiiv.com/p/betting-conference-tournaments
- https://en.wikipedia.org/wiki/2026_Big_Ten_men%27s_basketball_tournament
- https://web.archive.org/web/20201128170855/https://fivethirtyeight.com/features/do-conference-tournament-surprises-carry-over-into-the-ncaa-bracket/ (Paine, FiveThirtyEight 2015)
- https://www.r-bloggers.com/2020/09/momentum-in-sports-does-conference-tournament-performance-impact-ncaa-tournament-performance/
- https://vsin.com/college-basketball/college-basketball-ncaa-tournament-first-round-betting-trends/
- https://www.actionnetwork.com/ncaab/do-tired-legs-actually-lead-to-conference-tournament-unders
- https://www.actionnetwork.com/news/coronavirus-sports-games-no-crowd-empty-stadium-fans-rovell
- https://verso.uidaho.edu/esploro/outputs/journalArticle/Efficiency-in-the-madness-examining-the/996651783101851
- https://ideas.repec.org/a/sae/jospec/v18y2017i7p737-749.html
- https://collantropol.hr/antropo/article/view/298
- https://lida.sport-iat.de/twm/Record/4009826?lng=en
- https://pmc.ncbi.nlm.nih.gov/articles/PMC4807825/
- https://www.theringer.com/2021/06/01/nba/what-happened-to-home-court-advantage
- https://africa.espn.com/nba/story/_/id/12241619/home-court-advantage-decline
- https://beyondthescoresports.substack.com/p/breaking-down-home-court-advantage (opened; flagged as unreliable, not used as evidence)

## Theme H-I sources (psychology, narrative, markets)

- https://www.stat.berkeley.edu/~aldous/157/Papers/PointShaving.pdf
- https://knowledge.wharton.upenn.edu/?p=8034
- https://www.quantumsportssolutions.com/blogs/handicappers-library/nfl-betting-angles-fact-or-fiction-10-revenge
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10800907/
- https://www.procomputergambler.com/ncaab-public-betting-ranked-team-ats-trends/
- https://ideas.repec.org/a/sae/jospec/v21y2020i5p477-492.html
- https://staturdays.com/2020/11/06/cfb-mythbusters-the-big-win-hangover/
- http://www.emerald.com/sef/article/36/4/567-580/353529
- https://people.uncw.edu/tothj/PSY355/Frank-Black%20Uniforms-JPSP-1988.pdf
- https://www.psychologytoday.com/us/blog/attitude-check/201610/do-uniform-colors-matter-in-sports
- https://lida.sport-iat.de/dbb/Record/4058702
- https://www.wbur.org/onlyagame/2016/04/02/ncaa-astrodome-final-four
- https://fansided.com/2017/03/30/ncaa-tournament-domes-shooting-effect/
- https://www.eldo.co/the-dome-effect-how-nrg-stadium-impacts-shooting.html
- https://bleacherreport.com/articles/2629585-the-dome-dilemma-why-poor-shooting-at-houstons-nrg-stadiums-may-be-a-myth
- https://slate.com/culture/2015/02/asu-curtain-of-distraction-has-arizona-state-university-discovered-the-holy-grail-of-free-throw-distraction.html
- https://www.eldo.co/dome-effect-college-basketball-ncaa-tournament-2017.html
- https://www.eldo.co/domed-football-stadiums-effect-on-shooting-final-four-ncaa-tournament-college-basketball.html
- https://www.eldo.co/the-dome-effect-ncaa-tournament-shooting-by-venue-type.html
- https://sportsanalytics.studentorg.berkeley.edu/articles/shooting-percentages.html
- https://www.cbssports.com/college-basketball/news/offense-may-be-more-important-than-defense-in-ncaa-tournament
- https://theconversation.com/does-defense-actually-win-championships-89628
- https://www.pressherald.com/2023/03/31/ncaa-mens-basketball-offense-efficiency-not-defense-wins-championships/
- https://en.wikipedia.org/wiki/Defense_wins_championships
- https://ideas.repec.org/a/spr/jecfin/v44y2020i3d10.1007_s12197-020-09507-7.html
- https://cdr.lib.unc.edu/downloads/1g05fn40t
- https://www.espn.com/mens-college-basketball/ncaatourney06/insider/news/story?id=2329124
- https://blessyourchart.substack.com/p/022-more-experience-but-less-continuity
- https://barttorvik.com/cgi-bin/ncaat.cgi?type=coach
- https://www.basketball-reference.com/blog/indexb6a4.html?p=9088
- https://www.saturdaydownsouth.com/news/college-basketball/which-coaches-historically-beat-expectations-during-the-ncaa-tournament/
- https://spartansillustrated.com/articles/tom-izzo-rertospective-part-three-advanced-ncaa-tournament-performance-metrics
- https://ideas.repec.org/a/wly/mgtdec/v18y1997i4p295-308.html
- https://ideas.repec.org/a/bla/ecinqu/v56y2018i3p1724-1747.html
- https://ideas.repec.org/a/bpj/jqsprt/v7y2011i3n13.html
- https://www.espn.com/blog/collegebasketballnation/post/_/id/111975/on-the-quad-does-regular-season-momentum-equate-to-postseason-success
- https://painttouches.com/2022/03/15/is-momentum-a-thing-going-into-the-ncaa-tournament/
- https://ideas.repec.org/a/sae/jospec/v6y2005i4p390-400.html
- https://ideas.repec.org/a/eee/quaeco/v63y2017icp233-239.html
- https://myweb.ecu.edu/robbinst/PDFs/Weak%20Form%20Efficiency%20in%20Sports%20Betting%20Markets.pdf
- https://ideas.repec.org/a/spr/jecfin/v29y2005i3p403-408.html
- https://users.ssc.wisc.edu/~jmgregory/Gregory_pointshaving.pdf
- https://econometricsociety.org/publications/quantitative-economics/2018/07/01/Do-basketball-scoring-patterns-reflect-illegal-point-shaving-or-optimal-ingame-adjustments
- https://rhsmith.umd.edu/news/past-study-point-shaving-gives-context-fbi-gambling-probe
- https://ideas.repec.org/a/buc/jpredm/v4y2010i2p15-22.html
- https://buildingthepride.com/jobie/uploads/JOBIEV17J139.pdf
- https://www.foxsports.com/stories/college-basketball/2026-march-madness-first-round-betting-trends
- https://www.boydsbets.com/college-basketball-ats-records-point-spread/
- https://loserwins.com/data-analysis/underdog-win-rates-by-sport/
- https://gamblersanalytics.com/category/college-basketball/
- http://g.espncdn.com/s/betting/HCB2013.pdf?addata=2014%3Dbettingpapers_Humphreys
- https://www.sportsinsights.com/blog/betting-against-the-public-in-heavily-bet-ncaab-games/
- https://www.actionnetwork.com/ncaab/public-betting-recency-bias-college-basketball-postseason
- https://ideas.repec.org/a/sae/jospec/v22y2021i3p251-273.html
- https://www.sportsinsights.com/blog/betting-public-high-college-basketball-totals/
- https://en.wikipedia.org/wiki/Tom_Izzo (internally inconsistent; not used for counts)
- https://msuspartans.com/staff.aspx?staff=189 (MSU Athletics Izzo bio, read 2026-10-18)
- https://msuspartans.com/news/2026/3/15/mens-basketball-spartans-earn-no-3-seed-in-east-region-extend-ncaa-tournament-streak-to-28-straight
- https://jadrian.owlstown.net/publications/19081-the-impact-of-fans-on-home-advantage-evidence-from-the-covid-19-pandemic-college-basketball-season (journal venue of Marshall, Locke & Wooten)
- https://www.si.com/college/michiganstate/basketball/spartans-tom-izzo-ncaa-tournament--mike-krzyzewski-roy-williams
- https://www.actionnetwork.com/ncaab/mississippi-state-vs-michigan-state-odds-opening-spread-predictions-for-2024-ncaa-tournament
- https://journalofeconomicinsight.com/index.php/joei/article/view/53 (Douglas 2014: committee seeding bias not fully removed by the market)
- https://ideas.repec.org/a/mve/journl/v40y2014i2p1-17.html
- https://www.frontiersin.org/journals/behavioral-economics/articles/10.3389/frbhe.2024.1479832/full
- https://boardroom.tv/college-basketball-underdog-cover-odds/
- https://people.wku.edu/brian.goff/bbchapter8.pdf (context only; not used as evidence)

## Not opened (claims that depend on these are marked unverified)

- https://www.madduxsports.com/library/cbb-handicapping/betting-tips-for-ncaa-basketball-revenge-games.html (search snippet only)
- https://fivethirtyeight.com/features/it-really-is-harder-to-beat-a-team-the-third-time-in-mens-college-basketball (redirected)
- https://harvardsportsanalysis.org/2014/03/ncaa-basketball-do-underdogs-play-better-in-rivalry-games/ (HTTP 500)
- https://harvardsportsanalysis.org/2015/02/how-distracting-is-asus-curtain-of-distraction (HTTP 500)
- https://harvardsportsanalysis.org/2012/11/debunking-the-trap-game-and-letdown-game-myths/ (HTTP 500)
- https://kenpom.com/blog/?p=281 (403)
- https://www.crema-research.ch/?p=3581 (search snippet only)
- https://pubmed.ncbi.nlm.nih.gov/32028868/ and https://www.tandfonline.com/doi/abs/10.1080/17461391.2020.1727571 (cookie wall / 403)
- https://journals.humankinetics.com/view/journals/jmld/12/1/article-p90.xml (403)
- https://content.iospress.com/articles/journal-of-sports-analytics/jsa180331 and https://journals.sagepub.com/doi/10.3233/JSA-180331 (403; Pifer et al. details taken from the UNC thesis)
- papers.ssrn.com abstract 2481494 (403); kenpom.com live blog (403; the foul-up-3 and two-for-one posts were later read via web.archive.org, listed above); *Applied Economics* journal page for Marshall et al. (not opened); ScienceDirect GVT 1985 and PSE 2023 full texts (403); SAGE JSA-220592 (403); Taylor & Francis American Statistician 2025 (403); MDPI IJFS 2(4):359 and Games 16(6):64 (403); lukemccartney.substack.com tip study (404); teamrankings.com (403); escholarship Weimer PDF (403); ResearchGate (403); ncaa.com possession-arrow explainer (empty); Winthrop Intelligence 2014 PDF (returned HTML).

---

## Additions 2026-10-18

Gap-filling pass on eight topics found missing or thin after the review. Nothing above has been reworded. Each item below is either a **new belief** (E8, F5) or **added evidence** for an existing entry (A1, A2, B2, E1/E2/E4, G1/H10, H4/H8), with the change it makes to that entry's verdict or design. Sources opened in this pass are listed at the end of this section. Distances from mile-based sources are converted at 1 mile = 1.609 km; heights at 1 ft = 0.3048 m. New hypothesis IDs continue the register numbering (new-60 to new-63); the requirements session assigns final numbers.

### E8. "Road home games" in March: tournament teams near campus get a pseudo-home crowd (new belief)

- **Belief.** An NCAA tournament team playing near its campus (a "pod" site or regional close to home) gets a crowd and comfort edge that works like home court, even at a nominally neutral site.
- **Who holds it.** Fans, broadcasters, bracket pickers, coaches; the NCAA's own bracketing principle places teams "as close to home as possible" (NCAA.org, cited in `docs/research/neutral_site_proximity.md` §7.1).
- **Claimed effect and size.** "Like a home game": up to the 3-4 point regular-season HCA.
- **Why it matters for MSU.** MSU is usually sent to East or Midwest sites. The repo already lists distances from the Breslin Center: for example Detroit (Little Caesars Arena, 2028 regional) 126 km, the 2027 Final Four at Ford Field 126 km, Columbus 331 km, Dayton 333 km, but also later-round sites such as Atlanta and Washington where the edge has flipped against MSU (`docs/research/neutral_site_proximity.md` §9.1-9.2). The full evidence review, the distance method (WGS84 geodesic, km) and eight proposed hypotheses live in that document; this entry summarises the belief-level verdict and does not repeat the table there.
- **Evidence for.**
  - Silver (FiveThirtyEight, 11 March 2011; tournaments 2003-2010): teams playing within 50 miles (80 km) of campus were **24-2** (92%); teams travelling at least 1,000 miles (1,609 km) were **121-174** (41.0%). The closer team won 59% of games; with a travel gap of at least 500 miles (805 km) it won 67%; with a gap of at least 1,000 miles (1,609 km) it went **73-25** (74.5%, n = 98, SE about 4.4 pp). With a seed-only logistic model as the benchmark, teams at least 1,500 miles (2,414 km) closer were expected to win about 65% and won 79%; teams 1,000-1,500 miles (1,609-2,414 km) closer were expected to win 61% and won 71%. In points against a seed-based margin, the closer team beat expectation by **about 5 points** (gap ≥ 2,414 km) and **2-3 points** (gap 1,609-2,414 km). FiveThirtyEight's model then gave a concave bonus: about +2 points at 100 miles (161 km), about −1 point at 1,500 miles (2,414 km), rarely more than 3-4 points net, at most about 6 ([FiveThirtyEight via web.archive.org snapshot of 16 Jul 2019](http://web.archive.org/web/20190716031845/https://fivethirtyeight.com/features/in-tournament-theres-no-place-like-close-to-home/)). Bin sizes for the seed-adjusted comparisons are not given; the comparison controls seed only, not ratings. (These figures are marked unverified in `neutral_site_proximity.md` §2.1 and §3 because the live page redirects to ABC News; the archived snapshot read here confirms them.)
  - Carter (2017, *Managerial and Decision Economics* 38(1): 76-91), NCAA men's tournament: when the "relative home team" travels much less than its opponent, logit and OLS models show a positive relation with winning and with margin; sample, controls and coefficients not on the abstract page ([IDEAS](https://ideas.repec.org/a/wly/mgtdec/v38y2017i1p76-91.html); Wiley page returned 403).
- **Evidence against.**
  - **Seeding confounds every raw split.** Silver's own numbers show the mechanism: since 2003, No. 1 seeds travelled on average 254 miles (409 km) to their first-round site and No. 2 seeds 285 miles (459 km), while No. 4 seeds travelled 868 miles (1,397 km) and their No. 13 opponents 855 miles (1,376 km) ([FiveThirtyEight, archived](http://web.archive.org/web/20190716031845/https://fivethirtyeight.com/features/in-tournament-theres-no-place-like-close-to-home/)). The 24-2 record therefore mostly measures that strong teams are placed near home.
  - Horlick, Miller, Webb & Bruss (2023, UNC undergraduate poster; not peer-reviewed), 2019 and 2022 tournaments, games with a seed gap ≤ 7, binary logistic regression with Power-6 membership, automatic bid and a pre/post-COVID indicator: every distance variable had an odds ratio of **1.000** ("no effect"); Power-6 odds ratio 2.254, automatic bid 1.370; 59.1% of games classified correctly ([poster PDF](https://our.unc.edu/wp-content/uploads/sites/1148/2023/04/TeamLukeMaye.pdf); [abstract](https://our.unc.edu/abstract/horlick-does-how-far-youve-come/)). **Our reading:** this null is weak. The sample is two tournaments (the number of games is not printed), team quality is proxied only by conference and bid type (no seed, rating or spread), and an odds ratio reported to three decimals per mile cannot exclude a real effect: an odds ratio of 0.9997 per mile would print as 1.000 yet compound to about 0.74 over 1,000 miles (1,609 km).
  - Ward & Davenhall (2006): distance adds little beyond seed and RPI (AIC gain about 2.5); Williams (2025, undergraduate): no relation between miles travelled and tournament lines (both summarised in `neutral_site_proximity.md` §1 and §2.1).
- **Does the market price it?** **Partly, residual untested.** No study tests proximity against closing-spread residuals in the tournament while controlling for team quality (`neutral_site_proximity.md` §6). Rating systems differ: COOPER and ESPN BPI include a travel term, Torvik does not, and FiveThirtyEight's 2011 model added one (above). The tournament market as a whole looks efficient 1996-2019 with travel not tested ([Hickman 2020](https://verso.uidaho.edu/esploro/outputs/journalArticle/Efficiency-in-the-madness-examining-the/996651783101851), already cited in G1).
- **How we would test it.** **PBP + venue and campus coordinates + seeds, ratings and closing lines; no video needed.** Unit = tournament game (First Four to Final Four, 2002 onward, the pod era). Dose = each team's geodesic km from campus to the arena, entered as the gap f(d_opp) − f(d_team) with f = d^(1/3) (the COOPER form) and, as a check, log(1 + d/100 km). Controls: seed difference, pre-tournament rating difference (KenPom or Torvik adjusted efficiency margin) and, for the market test, the closing spread. Outcomes: (a) margin minus rating-implied neutral margin; (b) margin minus closing spread (ATS residual). Secondary: free-throw-attempt and foul differential (the referee channel, proximity-doc new-3) and attendance where reported. MSU is reported as a descriptive subgroup only (about 2-4 tournament games per season).
- **Power note.** Silver's ≥ 1,609 km-gap bin has n = 98 over eight tournaments. Detecting a 2-point margin effect with margin SD about 11 points (Wolfers' NCAAB forecast-error SD of 10.9, register "Background") at 80% power, two-sided alpha 0.05, needs about (2.80 × 11 / 2)² ≈ 240 games in the exposed group. That is reachable with pod-era tournaments 2002-2026 (about 1,500 games) but not with one or two tournaments, which is one reason the Horlick et al. null is uninformative.
- **Proposed hypothesis.** **new-60:** In NCAA tournament games 2002-2026, the team closer to the venue beats both the rating-implied neutral margin and the closing spread by an amount increasing in f(d_opp) − f(d_team) (f = d^(1/3), d in km), with seed and pre-tournament rating difference controlled. This is the tournament stratum of `neutral_site_proximity.md` new-1 (spread) and new-2 (ratings); if the requirements session merges them, keep the proximity document's IDs and drop new-60.
- **Verdict.** **Mixed.** Raw records strongly favour the near team (24-2 within 80 km), and a seed-adjusted 2003-2010 analysis still finds 2-5 points for large travel gaps (practitioner, not peer-reviewed); a peer-reviewed tournament study finds a positive relation with unknown controls; the only study with a "no effect" verdict is too small and weakly controlled to settle it. Whether the closing line already prices it is **untested**.

### F5. The referee crew moves fouls, free throws and the total (new betting belief)

- **Belief.** The assigned officiating crew changes how many fouls and free throws a game has, so a "tight" crew means more points and the over, and a "loose" crew the under.
- **Who holds it.** Bettors and handicapping services (NBA mostly), fans and coaches ("this crew lets them play").
- **Claimed effect and size.** Betting sites claim 3-5 points on the total for a crew 2-3 fouls above average, presented as illustrations without data or method ([Donaghy Effect explainer](https://www.donaghyeffect.com/nba/referees/explained); practitioner). The same site says NBA crews are "typically announced 1-2 days before games" (its own claim, not checked).
- **Evidence for (fouls).**
  - NCAA D-I, Pomeroy (KenPom blog, 30 Dec 2014; practitioner): regression of fouls per 40 minutes on officials over three seasons and **more than 12,000 games**, controlling for crew partners, day of season, final margin, overtimes and both teams' season foul rates; 350 officials with ≥ 30 games. The most extreme officials differ by about **3.6 fouls per 40 minutes** from average in each direction (e.g. Roger Ayers −3.61, SE 0.40, 231 games; Ted Valentine −3.44, SE 0.43, 197 games; Paul Janssen +2.62, 102 games). In six games worked by Valentine and Ayers together, 50 fewer fouls were called than a three-average-official model expected. Pomeroy's summary: most crews differ from average by no more than "a couple of fouls", but an aggregate deviation of 5-6 fouls "could be something worth knowing" ([KenPom, archived 2 Jul 2016](http://web.archive.org/web/20160702052352/http://kenpom.com:80/blog/ted-valentine-hates-to-call-fouls/)).
  - NBA, Gift & Rodenberg ("Napoleon Complex: Height Bias Among NBA Referees", *Journal of Sports Economics*; journal page not opened), **4,463 regular-season games, 2008-2012**: personal fouls per 48 minutes 4.13 for crews averaging ≤ 1.83 m, 4.09 for 1.83-1.91 m and 4.03 for ≥ 1.91 m (converted from the source's height bands), p = 0.03; FTA and FTM also fall as crew height rises ([Deadspin summary](https://deadspin.com/study-napolean-complex-is-real-shorter-nba-refs-call-1588127960/); secondary). Gift: the shortest crews called 0.147 more personal fouls per game; the effect "didn't seem to impact total points scored", though it did affect free-throw attempts and makes ([WBUR interview, 8 Nov 2014](https://www.wbur.org/onlyagame/2014/11/08/paul-gift-nba-referees-foul); lead author's account). Basketball Bundesliga 2020-21 (219 games, 8,641 foul calls): referee-player height differences have a small effect on foul calls ([Koop et al. 2026, *Int. J. Sports Science & Coaching* 21(1): 341-349](https://ueaeprints.uea.ac.uk/id/eprint/101649)).
  - NBA practitioner database: The F5's "Fouls Above Average" per 100 possessions, regression-adjusted for margin, possessions, team foul tendencies, crew-chief role and the rest of the crew, ≥ 50 games per referee ([Phillips, The F5, 13 Mar 2025](https://thef5.substack.com/p/nba-referee-database)). It makes no claim about totals.
- **Evidence against (totals and market).**
  - The only study that looked at points found **no clear effect on total points** of a crew trait that moved fouls and FTAs (Gift, above). Fouls also stop the clock and change possession counts, so the sign on points is not obvious (our reasoning): free throws add points but also dead-ball time, and frequent whistles can slow pace.
  - Totals markets look broadly efficient where studied (NBA overs a fair bet over more than 10,000 games, Compton & Sigler, per search snippet only, **unverified**; NCAAB totals evidence in I6 is weak and data-mined). No peer-reviewed study tests crew assignment against closing totals in either the NBA or NCAA (extended search, this pass).
  - Crew assignment is not random in college basketball: conference supervisors assign crews, and big games may get senior officials. The NBA describes its regular-season assignments as "completely arbitrary" (quoted in [Price, Remer & Stone](https://ideas.repec.org/a/bla/jemstr/v21y2012i1p271-300.html) per a search snippet; the abstract page opened in this pass does not contain the quote, **unverified**). Any NCAA crew effect therefore needs game-level controls (teams' foul rates, conference, game importance), which is what Pomeroy's model does.
- **Does the market price it?** **Unknown.** Two pre-conditions to check before any test: (1) whether NCAA crew names are public before the closing line (if not, the pre-game market cannot price them, and only in-play prices could); (2) whether crew foul tendencies are stable year to year (Pomeroy warns that 30-game estimates are noisy; 100 games is much better).
- **How we would test it.** **PBP + crew names (ESPN game summaries list officials) + closing totals; no video needed.** Step 1: estimate each official's fouls-above-average per 40 minutes on prior seasons only (Pomeroy's controls: partners, date, margin, overtimes, both teams' foul rates; shrink toward 0). Step 2: crew FAA = sum of the three officials' estimates. Step 3: regress game FTA, fouls and total points minus the closing total on crew FAA, out of sample (2021-22 on). Power: with total-minus-line SD about 16-17 points (assumed; to be measured), detecting a 1-point shift per crew-FAA SD needs a few thousand games, which D-I supplies in one season (about 5,500 games); MSU games alone cannot.
- **Proposed hypothesis.** **new-61:** In D-I games, a crew's prior-season fouls above average predicts the game's free-throw attempts (strongly) and its total points minus the closing total (weakly, null expected if the market prices crews or if fouls do not raise scoring). Links to F1 and F2 (crew fixed effects).
- **Verdict.** **Supported for fouls** (crews differ by up to about 3.6 fouls per 40 minutes in NCAA data; practitioner evidence, consistent with a peer-reviewed NBA crew-height effect on fouls and FTAs); **not supported or untested for totals** (the one NBA check found no effect on points; no market test exists).

### A1 addition. Hot hand: measurement error, statistical power, and a power calculation for new-1

- **Stone (2012, *The American Statistician* 66(1): 61-66, DOI 10.1080/00031305.2012.676467).** The first-order autocorrelation of shot *outcomes* is a "highly biased and inconsistent" estimator of the autocorrelation of the shooter's *make probabilities*: outcome autocorrelation can sit near zero while probability autocorrelation is near one. Makes and misses act as a very noisy measure of the hot state, so streak statistics from outcomes **understate** any true hot hand; the fallacy verdict may partly reflect measurement error ([IDEAS abstract](https://ideas.repec.org/a/taf/amstat/v66y2012i1p61-66.html); full text not opened).
- **Ritzwoller & Romano (2022, *Review of Economic Studies* 89(2): 976-1007; arXiv 1908.01406 v6).** Permutation tests of i.i.d. shooting, with analytic local power. In the GVT Cornell experiment (26 shooters, 100 shots each for 23 of them), i.i.d. shooting is rejected after multiplicity correction for **only one shooter** ("Shooter 109", who made 16 in a row right after missing 15 of 18). Under their streaky-alternative benchmarks derived from the spread of NBA field-goal percentages (ε = 0.024, i.e. a 2.4 pp rise after a streak and 4.8 pp make-minus-miss gap, held by a share ζ of shooters), **none of the four controlled experiments (GVT, Miller-Sanjurjo 2018, Jagacinski et al. 1979, the NBA Three-Point Contest) has adequate power for ζ = 0.25 or ε = 0.024 at any streak length**; "substantially larger data sets are required" ([IDEAS](https://ideas.repec.org/a/oup/restud/v89y2022i2p976-1007..html); [arXiv abstract](https://arxiv.org/abs/1908.01406); [arXiv PDF](https://arxiv.org/pdf/1908.01406v6), Sections 4-5). Their sample-size rule for the pooled make-after-make minus make-after-miss statistic (streak length 1, one-sided α) is n × s ≈ ((z₁₋α − z₁₋β) / (2ζε))², with n shots per shooter and s shooters.
- **What this changes in A1.** (1) Gilovich-style nulls are low-power, not evidence of absence; a null from new-1 would be read the same way. (2) Outcome-based streak tests (FT and FG) measure an attenuated version of the hot state; a tracking model of shot difficulty (new-1) reduces but does not remove this, because the latent "hotness" is still inferred from outcomes. (3) The verdict in A1 stays **Mixed**, with a stronger caveat: small per-player effects of 1-3 pp are plausible and mostly unmeasurable at the player level.
- **Power calculation for new-1 (computed for this register; binomial normal approximation, two-sided α = 0.05, power 0.80, so the minimum detectable effect is 2.80 standard errors).** For the difference D = P(make | previous make) − P(make | previous miss), the standard error is about 1/√n for n qualifying attempts whatever the make rate p (because the after-make share equals p, the terms pq(1/(np) + 1/(nq)) simplify to 1/n). Required n: D = 1 pp: 78,500; 2 pp: 19,600; 3 pp: 8,700; 5 pp: 3,100. Conditioning on 2+ makes vs 2+ misses (new-1's wording) roughly doubles the variance, so multiply n by about 2 (minimum detectable effect × about 1.4).

  | Test | Qualifying attempts (assumption) | SE of D | Minimum detectable D (80% power) |
  |---|---|---|---|
  | One high-volume Big Ten player, FT within a trip, one season | about 90 (about 200 FTA, of which about 45% follow an FT by the same player in the same trip) | 10.5 pp | 29.5 pp |
  | Same player, four seasons | about 360 | 5.3 pp | 14.8 pp |
  | All Big Ten FTs, one season | about 5,000 (18 teams × about 33 games × about 18.5 FTA per team-game; FTA/game from [Marshall et al.](https://spaces-cdn.owlstown.com/blobs/c31otj63qa356zwpeclkyawcy1bv), 19.4 home and 17.6 away) | 1.4 pp | 4.0 pp |
  | All Big Ten FTs, four seasons | about 20,000 | 0.71 pp | 2.0 pp |
  | All D-I FTs, one season | about 94,000 (about 362 teams × about 31 games × 18.5 FTA × 0.45) | 0.33 pp | 0.9 pp |
  | MSU field goals from our video, one season (same-player consecutive FGA within a game) | about 1,700 (about 2,100 MSU FGA) | 2.4 pp | 6.8 pp |
  | MSU and opponents from our video, four seasons | about 13,000-14,000 | 0.88 pp | 2.5 pp |

  **Consequences.** (a) **Per-player hot-hand tests are not informative** at any realistic sample (minimum detectable effect 15-30 pp against expected effects of 1-5 pp); report per-player estimates only inside a hierarchical (partial-pooling) model, never as individual significance tests. (b) The FT test should be pooled across all D-I (one season detects about 0.9 pp; Lantis & Nesson's NBA within-trip effect is 2.4 pp). (c) new-1's video FG test, as worded ("expect at most 2 pp", after 2+ makes vs 2+ misses), cannot separate 2 pp from zero even with four seasons of both teams (minimum detectable about 3.4 pp at streak length 2); it should be stated as an **estimate with a confidence interval** and a pre-declared equivalence bound (e.g. "the 90% CI excludes +5 pp"), not as a significance test. (d) If only a minority of shooters are streaky (Pelechrinis & Winston's 16%, each with a 2.5 pp rise after a make, i.e. a 5 pp make-minus-miss gap), the pooled make-minus-miss gap falls to about 0.8 pp, needing roughly 97,000 shots under the Ritzwoller-Romano rule (one-sided) — about one D-I season of FTs, and far beyond our video.
- **Proposed hypothesis.** **new-62:** Across all D-I free throws (one season or more), the within-trip difference P(make | previous FT made) − P(make | previous FT missed) is positive, with shooter random effects and the Miller-Sanjurjo correction (permutation within shooter-game). PBP only. new-1 is retained for the tracking-based FG question, reframed as estimation (above).

### A2 addition. A tracking-based precedent for separating shot quality from shot making

- **The decomposition exists in the NBA.** Chang, Maheswaran, Su, Kwok, Levy, Wexler & Squire, "Quantifying Shot Quality in the NBA" (MIT Sloan SSAC 2014, Best Paper; conference paper, not peer-reviewed; PDF not opened): **ESQ** (effective shot quality) is the value of a shot if taken by a league-average player, fitted by least squares on spatial inputs including **shot location and the proximity of defenders to the shooter**; **EFG+ = eFG − ESQ** measures shot making relative to that expectation (definitions as described in the peer-reviewed survey by [Gudmundsson & Horton, arXiv 1602.06994](https://arxiv.org/pdf/1602.06994), published in *ACM Computing Surveys*; award confirmed by [USC Viterbi Magazine](https://magazine.viterbi.usc.edu/spring-2015-2/articles/whos-the-best-shooter-in-the-nba/)). The later Second Spectrum/ESPN version, **qSQ** (quantified shot quality, the eFG an average player would get on that shot) and **qSI** (shooter's eFG minus qSQ), uses the positions, movement, distances and velocities of the shooter, the closest and next-closest defenders and the ball ([Maheswaran, ESPN, 13 May 2016](https://africa.espn.com/nba/playoffs/2016/story/_/id/15530589/what-advanced-tracking-data-reveals-nba-shooters)). Example: in 2015-16 Chris Paul ranked 23rd in eFG but 153rd in qSQ (hard shots) and 6th in qSI. Neither source reports a variance split between quality and making.
- **College evidence.** A collegiate shot-difficulty model exists outside the US: Yaita, Aoyagi, Kuraishi & Nodera (2019, *Study Journal of Kyushu Kyoritsu University* 10(1): 19-32), 1,456 shots from 10 games of the All-Japan Collegiate Championship, logistic regression; distance to defender is one of five significant predictors (with shooting area, screen play and the defender's ball handling); coefficients not on the record page ([repository record](https://kyukyo.repo.nii.ac.jp/records/376)). Synergy's D-I "shot quality" model (league-average make probability by context, with shot distance, defensive pressure, play type, shot clock and possession start as the strongest factors) is described only in a search snippet (**unverified**; the page failed a certificate check).
- **Correction to A2.** The sentence "No peer-reviewed study separates shot quality from shot making in NCAA" stays true as written; it should be read as **NCAA-specific**. In the NBA the decomposition is standard practice (ESQ/EFG+, qSQ/qSI), though published as conference papers and media pieces rather than peer-reviewed articles.
- **Alignment of our expected-points model (new-9).** Use the same split: expected value per shot = f(r in m, θ in degrees, closest-defender distance in m at release (shared definition), second-closest defender distance in m, shooter speed in m/s at release, catch-and-shoot vs pull-up, shot-clock s), fitted on all shots in our video, league-average shooter; shot making = actual points − expected points. Report the analogue of EFG+ per player and per game, and state that it is NBA-precedented (ESQ/qSQ) but new for NCAA.

### B2 addition. Peer-reviewed NCAA timeout evidence (behavioural momentum) and the regression-to-the-mean critique

- **Mace, Lalli, Shea & Nevin (1992, *Journal of Applied Behavior Analysis* 25(3): 657-663, DOI 10.1901/jaba.1992.25-657).** Videotapes of **14 games of the 1989 NCAA men's tournament** (Assis et al., below, describe the sample as seven televised games; the abstract says 14). Coded "reinforcers" (points, favourable turnovers), "adversities" (missed shots, unfavourable turnovers, fouls) and responses to adversity. Coaches called timeouts when their opponents' reinforcement rate exceeded theirs by **about 2.63 to 1.0**; in the **3 min after a timeout the two teams' reinforcement rates were nearly equal** ([PMC abstract](https://pmc.ncbi.nlm.nih.gov/articles/PMC1279747/)). Note the unit is the coded reinforcement rate, not points; no inferential test or counterfactual is reported in the abstract.
- **Roane, Kelley, Trosclair & Hauer (2004, *JABA* 37(3): 385-390, DOI 10.1901/jaba.2004.37-385).** Partial replication in "a subset of women's college basketball games" ([PMC abstract](https://pmc.ncbi.nlm.nih.gov/articles/PMC1284512/)); the number of games (4 or 6 in secondary summaries) and the results are **unverified** (PMC PDF not retrievable). A 2025 review describes Mace and Roane together as "small-sample studies" indicating that timeouts reduce the opponent's momentum ([Qiu et al. 2025, Frontiers in Psychology](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1673186/full)).
- **Regression to the mean.** Both JABA studies compare the 3 min before with the 3 min after, the design criticised in B2: timeouts are called at the low point of a run, so the rate ratio would move toward 1.0 without any timeout effect.
  - Permutt (2011, Haverford/Bryn Mawr thesis, "The efficacy of momentum-stopping timeouts on short-term performance in the NBA"; repository page blocked by a bot check, not opened) is described as the first to compare timeouts after a 6-0 run with similar moments without a timeout: home team (first-half restriction) scored 5.47 of the next 10 points after a timeout vs 5.26 without, a 0.21 difference; conclusion: no meaningful momentum effect (as summarised in [Assis et al.](https://arxiv.org/pdf/2009.06750), Section 2; **secondary**).
  - **Correction to the gap list:** arXiv 2009.06750 ("Stop the Clock: Are Timeout Effects Real?") is by **Assis, Assunção & Vaz-de-Melo** (ECML PKDD 2020, Springer 2021, pp. 507-523), not Permutt. NBA play-by-play, four regular seasons (2015-2018), propensity and other matching, 3,766 to 7,082 treated-control pairs per test: the largest estimated timeout effect was **−0.059 points per possession over the next 4 possessions**; all effects "practically irrelevant"; the apparent post-timeout gain is regression to the mean ([arXiv abstract](https://arxiv.org/abs/2009.06750); [PDF](https://arxiv.org/pdf/2009.06750)).
- **What this changes in B2.** B2's statement that the only NCAA timeout evidence is a non-peer-reviewed student paper is now out of date: there is peer-reviewed NCAA evidence (Mace 1992, men's tournament; Roane 2004, women's), but it is small-sample, pre/post and not adjusted for regression to the mean. Three matched or counterfactual NBA designs (Permutt 2011; Assis et al. 2020; Gibbs et al., already in B2) find effects near zero or slightly negative. B2's verdict stays **Mixed**, and the matched-run design of **new-7** (runs with vs without a timeout, plus a "no timeouts left" control) is the right one; Mace's 3-min window and reinforcement coding can be reproduced from PBP as a replication arm.

### E1, E2 and E4 addition. Peer-reviewed cross-sport baseline for home advantage

- **Jamieson (2010, *Journal of Applied Social Psychology* 40(7): 1819-1848, DOI 10.1111/j.1559-1816.2010.00641.x).** Meta-analysis of win-loss data only; **87 independent effect sizes** (56 from 32 published articles, 31 computed from archival records), random-effects framing, unweighted mean of the home win proportion p ([course-hosted PDF](https://classdat.appstate.edu/COB/MGT/VillanPD/OB%20Fall%202021/Unit%203%20-%20Cohesion/Group%20Articles/Jamieson%20-%20Home%20field%20advantage%20MA%202010.pdf)).
  - Overall home win proportion **Mp = .604** (SD .065; 95% CI .590-.618; t(86) = 14.98, d = 3.23).
  - By sport: **basketball .629** (12 effect sizes), soccer .674 (highest), baseball .556 (lowest); F(9, 77) = 5.21. Collegiate vs professional: .608 vs .604 (no difference, p = .88), replicating Courneya & Carron.
  - **Season length:** < 50 games .620 (k = 42), 50-100 games .601 (k = 28), > 100 games .559 (k = 13); F(2, 80) = 4.78. Season length **mediated** the sport differences (Sobel Z = 2.57, p = .01). College basketball (about 30-35 games) sits in the short-season group.
  - **Game type:** championship/playoff .630 vs regular season .590 (t(85) = 2.82); the author's explanation is game importance (larger, denser, louder crowds).
  - **Era:** pre-1950 .650, 1951-1970 .603, 1971-1990 .581, 1991-2007 .592 (F(3, 66) = 2.80, p = .046; only pre-1950 differs).
  - Collegiate basketball effect sizes in the appendix: Snyder 1985 .66 (90 games), Moore 1995 .64 (90 games), Jamieson's archival sample .63 (280 games).
- **Classic frameworks (secondary; primaries not opened).** As described in Jamieson (2010, pp. 1820-1822): Courneya & Carron (1992, *J. Sport & Exercise Psychology* 14: 13-27) define home advantage as home teams winning over 50% of games under a balanced schedule and propose a feed-forward model: game location → **four game-location factors (crowd, familiarity, travel, rules)** → critical psychological states → critical behavioural states (players and officials) → outcomes; Carron, Loughhead & Bray (2005, *J. Sports Sciences* 23(4): 395-407) reviewed it a decade later ([sponet record](https://www.sponet.de/sponet/Record/4009845); [McMaster record](https://experts.mcmaster.ca/scholarly-works/1313526)). Pollard (1986, *J. Sports Sciences* 4: 237-248), English soccer from 1888: home advantage stable to 1984; secondary accounts disagree on whether he found familiarity more important than crowd and travel (search snippets, **unverified**); Jamieson cites him for larger home advantage on unusually sized pitches and for travel distance increasing it.
- **What this changes.**
  - **E1** can open with a peer-reviewed baseline: basketball home win proportion about .63 across 12 samples (NBA-dominated), against the D-I values of 59-63% already in E1. The four framework factors map onto the register: crowd (E4, F1), familiarity (E5 altitude, E6 backgrounds), travel (G1, E8), rules (no register entry).
  - **E2:** Jamieson's era effect is driven by pre-1950 samples; since 1950 the pooled home win proportion is flat (.603 → .581 → .592), so a long-run "decline" in all sports is not supported after 1950; the basketball-specific decline evidence in E2 (pace-linked, NBA and NCAA) stands on its own.
  - **College basketball's large HCA and season length.** Jamieson's mediation suggests short seasons (more important games) carry larger home advantage. Within D-I this predicts a larger HCA in more important games (conference play late in the season) than in November non-conference games, after controlling for opponent strength. This is testable.
- **Proposed hypothesis.** **new-63:** In D-I games 2010-2026, HCA in points per 100 possessions is larger in late-season conference games (February-March) than in early-season games (November-December), opponent strength and pace controlled. PBP only. Caveat: early-season home games are disproportionately against weak "buy-game" opponents, so the comparison must use rating-adjusted margins.

### G1 / H10 addition. Large peer-reviewed NBA jet-lag studies disagree on direction

- **Leota, Hoffman, Czeisler, Mascaro, Drummond, Anderson, Rajaratnam & Facer-Childs (2022, *Frontiers in Physiology* 13), 11,481 NBA regular-season games, 2011-12 to 2020-21** (bubble excluded). Jet lag = time zones crossed minus 1 h of resynchronisation per day. **Home teams** with eastward jet lag (n = 451) vs no jet lag (n = 10,411): win 54.55% vs 58.05% (p = 0.051), points differential +1.24 vs +2.53 (−1.29 points, p = 0.015), worse rebound and eFG differentials (both mediating); 2 h eastward jet lag −2.81 points vs +1.72 for 1 h (p = 0.014); with adequate rest after eastward travel the deficit disappeared (p = 0.984). **Westward** jet lag for home teams: no effect (p = 0.665 wins, 0.477 points). **Away teams:** no significant jet-lag effect in either direction (wins p > 0.136; points p > 0.294). Travel timing was assumed (teams leave right after the previous game) ([Frontiers](https://www.frontiersin.org/articles/10.3389/fphys.2022.892681/full)).
- **Özdalyan, Çene, Gümüş & Açıkgöz (2024, *Chronobiology International*, DOI 10.1080/07420528.2024.2325641), 25,016 NBA regular-season games, 2000-2021:** Pacific home teams beat Eastern visitors 63.5% of the time; Eastern home teams beat Pacific visitors 55.0%. Home teams whose body clocks were ahead of local time after an eastern trip won more often. Travel schedules were modelled, and team strength was **not** controlled ([ScienceDaily release, 1 May 2024](https://www.sciencedaily.com/releases/2024/05/240501091642.htm); journal page not opened; figures **secondary**).
- **Pradhan, Ravi & Devin (2022, *Journal of Sports Analytics* 8(1): 69-76), 499 NBA playoff games, 2013-14 to 2018-19:** teams travelling **east** scored more points than teams staying in the same time zone; evening games had higher 3P% than afternoon games; effect sizes not in the record ([LIDA record](https://lida.sport-iat.de/dbb/Record/4074621)).
- **How they conflict with what G1 already has.** McHill & Chinoy (2019-20, pre-pause): **away** teams hurt by **westward** travel. Leota: **home** teams hurt after **eastward** jet lag, away teams unaffected. Özdalyan: visitors who travelled **west** (Eastern teams at Pacific sites) lose more, consistent with McHill but confounded by team strength. Pradhan: **eastward** travellers do better in the playoffs. Steenland & Deddens (1987-95): west-to-east cross-country visitors +4 points (p = 0.07). The direction depends on whether the team is home or away, on rest days, on tip time relative to body clock, and on uncontrolled team strength.
- **What this changes in the H10 refinement.** Pre-registering one direction now (G1: "westward shifts for evening tips and eastward shifts for early tips lower first-half points") is premature. Recommended pre-registration: (1) estimate **home-team and away-team effects separately**; (2) code direction and days since the shift (Leota's 1 h per day recovery rule), and test eastward and westward with **two-sided** tests; (3) include tip time on the body clock of each team (local tip time minus zone shift) as a separate term; (4) control team strength (ratings) and rest days, which Özdalyan did not. NCAA relevance: since the Big Ten added Pacific-time members, MSU makes two- and three-zone trips in conference play, so H10 can now be tested on Big Ten games as well as D-I-wide.
- **Verdict for G1 unchanged:** **Mixed**; the large-sample NBA literature supports a time-zone effect but not a consistent direction.

### H4 / H8 addition. Large-sample dark-uniform evidence and recent nulls

- **Webster, Urland & Correll (2012, *Social Psychological and Personality Science* 3(3): 274-281, DOI 10.1177/1948550611418535),** NHL **52,098 games, 1984-2010** (969,690 penalty minutes): teams wearing darker jerseys were penalised **about 2 more minutes per game**; teams in black were penalised most (1,528 vs 1,386 penalty minutes per team-season, +10.2%). The NHL's 2003 switch from white-at-home to coloured-at-home acted as a quasi-experiment separating jersey colour from venue; within-team comparisons across a team's uniform history. The design cannot separate player aggression from referee perception ([NPR, 26 Apr 2012](https://www.npr.org/2012/04/26/151383136); [CU Boulder record](https://experts.colorado.edu/display/pubid_81618)).
- **Basketball.** Zhu, Chen, Zhou, Wang & Li (2016, *Journal of Physical Education* (China), issue 3, pp. 42-45, ISSN 1006-7116), **9,668 Chinese football and basketball league games, 2005-2015:** in basketball, teams in warm-colour-series uniforms drew significantly more fouls than teams in cool colours; in men's football no difference; the colour effect was not changed by home vs away. Effect sizes could not be extracted from the PDF (Chinese text); peer-review status of the journal not checked ([PDF](https://tyxk.scnu.edu.cn/editer/doc/20165279493251253.pdf)). A 2014 AAHPERD conference abstract (one D-I school, 16 men's and 13 women's games) found no significant relation (men r = .20, p = .27; dark-uniformed men's teams 1.44 more fouls per game) (search snippet; page returned 404; **unverified**).
- **Recent nulls (soccer).** Cheng, Akman & Duku (2025, *Mathematics and Sports* 7(1), DOI 10.5149/ms.1652), English Premier League about 2009/10-2020: home teams draw fewer fouls and usually wear light kits; **conditioned on home/away, light vs dark jerseys show no foul difference**, including at referee level (search snippets only; the journal site blocks automated access with a bot check, so **unverified**). Patterson (2021, Clemson MS thesis), FIFA men's and women's World Cups of the 2010s: no significant difference in fouls per match for red vs other colours ([Clemson record](https://open.clemson.edu/all_theses/3532); thesis).
- **What this changes.** H4's foul evidence is no longer only Frank & Gilovich (1988): the largest within-team, venue-separated study (NHL, about 52,000 games) supports a dark-uniform penalty effect of about 2 minutes per game, one large basketball league study supports a warm-colour foul effect, and soccer studies that condition on home/away find nothing. Verdict for H4: **not supported for winning**; **mixed for fouls** (supportive in hockey and one Chinese basketball study; null in soccer; untested in NCAA men's basketball).
- **Design for new-46 (no new ID).** Copy Webster's identification: within-team comparisons of the **same team at the same venue in different colourways** (home whites vs home alternates, which college teams wear for "blackout" or rivalry games), with game importance controlled (alternates are chosen for big games). Outcome = team fouls per 100 possessions and opponent FTA; data = PBP + one video frame per game for jersey colour (or a uniform-tracking database).

### Summary rows for the additions

| # | Belief or addition | Verdict | Market prices it? | Test data | Proposed IDs |
|---|---|---|---|---|---|
| E8 | Tournament teams near campus get a pseudo-home crowd | Mixed (raw and seed-adjusted support; weak null) | Partly; residual untested | PBP + coordinates + seeds, ratings, lines | new-60 (or proximity-doc new-1/new-2) |
| F5 | Referee crew moves fouls, FTs and totals | Supported for fouls; untested/not supported for totals | Unknown (check crew publication timing) | PBP + crew names + closing totals | new-61 |
| A1+ | Hot hand: measurement error and power | Mixed (unchanged); per-player tests uninformative | — | PBP (D-I FTs); video FG as estimation | new-62; new-1 reframed |
| A2+ | Shot quality vs shot making | NBA precedent (ESQ, qSQ); NCAA untested | — | Video/tracking | new-9 aligned |
| B2+ | Timeouts stop runs (NCAA peer-reviewed) | Mixed (unchanged) | Not studied | PBP; video | new-7 design supported |
| E1/E2+ | Cross-sport home-advantage baseline | Basketball .629 home win (meta-analysis) | Yes (E1) | PBP | new-63 |
| G1+ | Jet lag direction | Mixed (direction conflicts) | Partly | PBP + coordinates + tip times | H10 refinement revised |
| H4+ | Dark uniforms and fouls | Mixed for fouls; not supported for winning | No evidence | PBP + one video frame | new-46 design |

### Still missing after this pass

- Full texts not opened: Chang et al. 2014 Sloan PDF (definitions via the survey and ESPN only); Carter 2017 (abstract only); Stone 2012 full text; Courneya & Carron 1992 and Pollard 1986 (content via Jamieson 2010); Roane et al. 2004 results; Permutt 2011 thesis; Özdalyan et al. 2024 journal page; Gift & Rodenberg journal page; Cheng, Akman & Duku 2025 (bot check); Synergy D-I shot-quality explainer (certificate error).
- No study tests NCAA tournament proximity against closing spreads with rating controls; no study tests crew assignment against closing totals in any league; no NCAA men's study of uniform colour and fouls.
- Not checked: whether NCAA officiating crews are published before tip (decides whether F5 can be a pre-game market test at all).

### Sources opened in this pass (2026-10-18)

- http://web.archive.org/web/20190716031845/https://fivethirtyeight.com/features/in-tournament-theres-no-place-like-close-to-home/ (Silver 2011; read with curl; the live URL redirects to abcnews.com; a 2025 snapshot is also a redirect)
- https://our.unc.edu/abstract/horlick-does-how-far-youve-come/ and https://our.unc.edu/wp-content/uploads/sites/1148/2023/04/TeamLukeMaye.pdf (poster text extracted)
- https://ideas.repec.org/a/wly/mgtdec/v38y2017i1p76-91.html (Carter 2017 abstract)
- https://ideas.repec.org/a/taf/amstat/v66y2012i1p61-66.html (Stone 2012)
- https://ideas.repec.org/a/oup/restud/v89y2022i2p976-1007..html, https://arxiv.org/abs/1908.01406, https://arxiv.org/pdf/1908.01406v6 (Ritzwoller & Romano)
- https://pmc.ncbi.nlm.nih.gov/articles/PMC1279747/ (Mace et al. 1992); https://pmc.ncbi.nlm.nih.gov/articles/PMC1284512/ (Roane et al. 2004)
- https://arxiv.org/abs/2009.06750 and https://arxiv.org/pdf/2009.06750 (Assis, Assunção & Vaz-de-Melo; Permutt 2011 as summarised there)
- https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1673186/full (Qiu et al. 2025 review statements on Mace, Roane, Permutt)
- https://classdat.appstate.edu/COB/MGT/VillanPD/OB%20Fall%202021/Unit%203%20-%20Cohesion/Group%20Articles/Jamieson%20-%20Home%20field%20advantage%20MA%202010.pdf (Jamieson 2010, full text)
- https://www.sponet.de/sponet/Record/4009845 and https://experts.mcmaster.ca/scholarly-works/1313526 (Carron, Loughhead & Bray 2005 records)
- https://arxiv.org/pdf/1602.06994 (Gudmundsson & Horton survey: ESQ/EFG+ definitions and the Chang et al. reference)
- https://magazine.viterbi.usc.edu/spring-2015-2/articles/whos-the-best-shooter-in-the-nba/ (award, authors)
- https://africa.espn.com/nba/playoffs/2016/story/_/id/15530589/what-advanced-tracking-data-reveals-nba-shooters (qSQ/qSI)
- https://kyukyo.repo.nii.ac.jp/records/376 (Yaita et al. 2019)
- https://www.frontiersin.org/articles/10.3389/fphys.2022.892681/full (Leota et al. 2022)
- https://www.sciencedaily.com/releases/2024/05/240501091642.htm (Özdalyan et al. 2024, press release)
- https://lida.sport-iat.de/dbb/Record/4074621 (Pradhan, Ravi & Devin 2022)
- http://web.archive.org/web/20160702052352/http://kenpom.com:80/blog/ted-valentine-hates-to-call-fouls/ (Pomeroy 2014; read with curl)
- https://www.wbur.org/onlyagame/2014/11/08/paul-gift-nba-referees-foul and https://deadspin.com/study-napolean-complex-is-real-shorter-nba-refs-call-1588127960/ (Gift & Rodenberg, secondary)
- https://ueaeprints.uea.ac.uk/id/eprint/101649 (Koop et al. 2026)
- https://thef5.substack.com/p/nba-referee-database (The F5)
- https://www.donaghyeffect.com/nba/referees/explained (practitioner claims)
- https://ideas.repec.org/a/bla/jemstr/v21y2012i1p271-300.html (Price, Remer & Stone abstract; re-read to check the "arbitrary assignment" quote, which is not on the page)
- https://www.npr.org/2012/04/26/151383136 (Webster et al.; read with curl after WebFetch timed out)
- https://experts.colorado.edu/display/pubid_81618 (Webster, Urland & Correll citation)
- https://tyxk.scnu.edu.cn/editer/doc/20165279493251253.pdf (Zhu et al. 2016; English abstract extracted)
- https://open.clemson.edu/all_theses/3532 (Patterson 2021)

**Not opened in this pass (claims marked unverified or secondary):** Wiley MDE page for Carter 2017 (403); Sloan conference page for Chang et al. (404); synergysports.com (certificate error); scholarship.tricolib.brynmawr.edu Permutt thesis (bot check); PMC and Europe PMC PDFs for Mace 1992 and Roane 2004 (download pages only); janeway.uncpress.org Cheng et al. (Anubis bot check, not bypassed); shapeamerica.confex.com AAHPERD 2014 abstract (404); Springer pages for Nevill & Holder 1999 and Paul & Weinbach 1995 (login redirect); metatoc.com (timeout).
