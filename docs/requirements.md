# MSU Basketball CV — Master Requirements Brainstorm (v1)

Oct 17, 2026 · @Aldemir

## How to read this

This lists every requirement we can think of, from the first data row to the final win probability. It is grouped by pipeline stage only; nothing is ranked, weighted or cut yet. Ranking is the next step.

| Term | Definition in this project |
| --- | --- |
| Possession | Starts when a team gains control of the ball and ends only when the other team gains control (or the period ends). Offensive rebounds and shot-clock resets do not end it. |
| Chance | One shot-clock cycle inside a possession. A possession with two offensive rebounds has three chances. Each chance records its start shot clock (30 s, or 20 s after an offensive rebound in men's college). |
| Action | One building block: a screen, handoff, cut, drive, post entry, pass or dribble move. |
| Set | A named, designed sequence of actions with a start alignment, ordered phases and counters (taxonomy section). |
| Set instance | One set as run in a game: start time, phase times, end time, outcome. |
| Motion | How a set unfolds live, including counters when the defense takes the first option away. |
| Scheme state | The defense's structure at one second: man, a named zone, press, switching, junk. It can change inside a chance. |
| Coverage | How the defense answers one action: switch, drop, hedge, ice, trap, under, over. |
| Configuration | The positions of all 10 players at one instant, in the coordinate frames of the geometry section. |
| Possession value (EPV) | Expected points of the possession at that instant. |
| Ball-handler frame | Coordinates measured from the player holding the ball; reset on every pass. |
| Units | Metres, centimetres, seconds, milliseconds, degrees; no feet anywhere in the system. |

## The causal stack

Your chain, as the system will compute it: each layer is built only from the layers above it, and possession value is where they meet.

&#91;embedded content: causal stack · 7 layers, 2 side inputs\]

Defense is read from the same movements as offense; context enters when possessions are simulated into segments and games.

## Foundation data and metadata layer

Every game gets one row in a game registry before any video is touched, and every later file links back to that row. Nothing enters training without its registry row.

**Game registry: one row per game**

- ESPN game ID, date, local tip time, season, game type (exhibition, non-conference, Big Ten, Big Ten tournament, NCAA tournament) and round
- Home, away or neutral; venue, city, capacity, attendance
- Opponent, opponent conference, both head coaches
- TV network and broadcast crew
- The three referees (ESPN's game summary lists them)
- Final score, score by half, overtime
- MSU jersey color and opponent jersey color
- Footage source (YouTube, your B1G+ recording, other), file path, resolution, frame rate, length, footage quality score
- Play-by-play available, shot coordinates available
- Market data at close: spread, total, moneyline, first-half lines (source still to be found; ESPN's odds fields were empty for past games)
- Days of rest, travel distance and time zones crossed, for both teams
- Both teams' adjusted ratings (KenPom or Torvik) as of the day before the game
- Availability notes (your input)

**Roster registry: one row per player per season**

- ESPN player ID, name, jersey number (numbers can change between seasons), listed position, height, weight, class year, shooting hand, transfer origin, headshot link
- Same registry for every opponent's roster

**Player attribute profile: one card per player, built before any game is extracted**

- Body: height (cm), weight (kg), wingspan (cm), standing reach (cm), hand length and width (cm), shoe size where published; flagged "not public" when missing, never guessed
- Laterality: shooting hand, dominant dribble hand, preferred finishing hand, preferred drive direction (measured from video)
- Athletic: sprint speed, acceleration, vertical estimate, measured from tracking; combine numbers where they exist (NBA Draft Combine publishes them for invitees)
- History: age, class, years in Izzo's system, previous school, recruiting ranking, position history, change in weight and height season to season
- Load and health: minutes per game, continuous-minutes pattern, games missed, public injury history (your availability log)
- Skill splits: free-throw rate and accuracy, shooting by distance and angle bin, usage, turnover rate, foul rate, offensive and defensive rebound rates
- Behaviour: shot-clock usage when he has the ball, pass-or-shoot tendency per zone, help frequency on defense
- Sources: ESPN roster, MSU roster page, Sports-Reference, recruiting sites, combine data, our own tracking; every field carries its source and date

**Team and coach profiles**

- Team: pace, four factors, shot profile by angle and distance, set frequency, scheme frequency on defense, rotation depth, continuity (returning minutes)
- Coach: years at the school, set library observed, timeout usage, substitution patterns, late-game choices, record by situation

**Availability log: one row per player per game**

- Status (played, out, limited, returned), minutes, source link, note
- I build the date list from the schedule; you fill or confirm the status

**Opponent baselines**

- Adjusted offensive and defensive efficiency, tempo, the four factors (shooting, turnovers, rebounding, free throws), 3-point attempt rate, all as of the game date, never end-of-season
- Play-type tendencies where we can derive them

**Rules for the whole layer**

- No leakage: a feature for a game uses only what was known before tip
- Every file is stamped with its source, pull date and code version
- One shared player and game ID system across video, play-by-play, market and context data

## Global metadata on every record

Every frame, event, set instance and prediction is stamped with the same global fields, so any number can be filtered or joined by game state.

| Field | Unit or format |
| --- | --- |
| Game ID, season, game type | ESPN ID; text |
| Video frame index and timestamp | integer; ms from video start |
| Period and game clock | integer; s remaining, 0.1 s resolution |
| Shot clock | s remaining, 0.1 s resolution |
| Score MSU, score opponent, margin | points |
| Possession ID, chance ID, chance number | integers |
| Team in possession, basket attacked | MSU or opponent; north or south end of the court model |
| 10 player IDs on the floor | roster IDs |
| Team fouls, bonus status, personal fouls per player | counts |
| Timeouts left per team | counts |
| Scheme state of the defense | label + confidence |
| Camera shot type, coverage score | label; 0 to 1 |
| Court constants | court 28.65 m × 15.24 m; all positions in m |
| Model and code version | version string |
| Source and confidence for every value | source tag; 0 to 1 |

**Ball-control state (every frame)**

| State | Meaning |
| --- | --- |
| MSU ball | An MSU player holds or dribbles the ball in live play |
| Team X ball | An opponent player holds or dribbles the ball in live play |
| Contested | Live ball nobody controls: scramble, loose ball, tip, deflection, held-ball tie-up |
| In flight | Live ball in the air after a shot or pass, before anyone controls it |
| Inbound pending | Dead ball awaiting a throw-in; carries side (sideline or baseline), court half and the inbounding team |
| Dead | Whistle, free throws, timeout, end of period, review |

- Every state change is timestamped; possession and chance IDs follow from these changes
- Contested and in-flight time is counted separately, never credited to either team

**Vocabulary map: common terms ↔ our measured definitions**

- When a common term and the math disagree, both are kept and linked, so we can read coaches, commentators and articles correctly
- Example: coaches and broadcasts may call a spot "45"; our measurement puts the elbow at about 66° and the wing centre at 45°. The map records which spot a source means in that context; it does not rewrite every "45" we read
- Each entry: common term, measured definition (distance, angle, time), where the term is used, examples, and notes on ambiguity
- First entries: elbow, wing, slot, corner, short corner, dunker spot, block, top, nail, strong side, weak side, "two-side", "one-pass away", "help side", "tag", "low man"

## Player identity and appearance layer

A player is identified by a stack of cues voted over many frames; no single cue carries it. At broadcast distance a face is a few pixels, so identity comes from the jersey, the lineup and the body, not from face recognition.

**Cues, in the order the system checks them**

1. Team, from jersey color clustered per game (no labels needed).
2. The five players on the floor, from play-by-play substitutions: the tracker only has to choose among those five, not the whole roster.
3. Jersey number, front and back, read whenever visible and voted across frames.
4. Height and build relative to others, once court calibration gives a scale.
5. Per-game appearance: shoes, sleeves, headbands, tape, tights, hair.
6. Movement signature: speed, gait, shooting hand, favorite spots.
7. Role context: who brings the ball up, who sets the screens.

**Reference pack per player**

- ESPN headshot and roster data, for human checking of the model's labels
- 50 to 200 confirmed broadcast crops per player per season, collected by the labeling loop (section on human-in-the-loop)
- A per-game appearance card filled at tip-off: shoe color, sleeve, headband

**Your idea: studio-style images generated with Nano Banana**

- Listed, not cut. My view: generated images can invent details that are not on the real player, and the model must learn from what broadcast frames actually show. Where it could help: synthetic kit and lighting variants to make team-color classification robust across arenas.

**Checks**

- Identity accuracy per player per game against a hand-labeled sample
- Every identity switch logged and reviewed

**Hard cases identity must survive**

- Every body orientation: facing the camera, back turned, side-on left and right, bent over, mid-jump, on the floor
- Number partly hidden: one digit visible, number folded by the jersey, arm across the chest; partial reads are kept as evidence, not discarded
- Small players in frame: a player standing 28 m from the camera may be only tens of pixels tall; the minimum readable size is measured, not assumed
- Motion blur at 30 fps on fast cuts; prefer 60 fps recordings
- Two players stacked or crossing during a screen; identity is re-confirmed after every crossing
- Same number on both teams; team color decides first
- Uniform variants: home light, road dark, alternates, throwbacks, warm-up shirts, shooting shirts at the bench
- Arena lighting and floor glare that shift jersey color; color is normalized per arena
- Players re-entering after a substitution, a timeout or a camera cut
- Referees in striped shirts, coaches, mascots and band members on the floor during stoppages; excluded by class, not by luck

**Identity outputs**

- Per frame: player ID + confidence; per possession: identity agreement with the play-by-play lineup
- Per game: a confusion list (which pairs of players the model mixes up), sent to the review queue
- Per season: accuracy per player, so weak identities get more labels

## Video ingest and quality

Only frames from the main wide game camera go to tracking; everything else is detected and set aside first.

**Capture standard**

- Sources: March Madness YouTube replays, your B1G+ screen recordings, later MSU film
- Record at native resolution (1080p minimum), constant frame rate (30 or 60 fps), no rescaling, high bitrate
- Keep the audio: whistles, buzzers and crowd noise are event cues
- File name: date, opponent, source; linked to the game registry ID

**Per-game intake checks**

- Length matches a full game, no dropped or frozen frames, no letterboxing, overlays noted

**Shot classification (every frame)**

- Main wide camera, tight close-up, replay, slow motion, crowd, bench, studio, commercial, graphic
- Replay detection from the network's replay wipe and slow-motion cues

**Coverage score**

- Per frame: players visible out of 10, share of the half-court in view, camera zoom level, ball visible or not
- Per possession: average of the above, number of camera cuts, occlusion level
- High-coverage possessions are used first; low-coverage ones are imputed and flagged

**Audio features**

- Whistle and buzzer detection to cross-check events
- Crowd loudness as a possible home-crowd measure

## Court geometry, defined as math (metric)

Every position is in metres from the centre of the basket being attacked, and every named spot is a range of distance and angle, not a word. Names are labels on the math, kept only for reading.

**Coordinate system**

- Origin: the point on the floor directly under the centre of the attacked rim
- x axis: along the baseline, positive to the attacker's right when facing the basket
- y axis: from the baseline toward half-court
- Polar form: r = √(x² + y²) in metres; θ = atan2(y, x) in degrees, so 0° is the right baseline, 90° is straight out to the top of the key, 180° is the left baseline
- The other half is mirrored into the same frame, so every possession of both teams is compared in one system
- Stored to 1 cm, reported to 0.1 m

**Court constants (NCAA men's; verify each against the current rulebook before building)**

| Element | Value |
| --- | --- |
| Court | 28.65 m × 15.24 m |
| Rim centre from baseline | 1.60 m |
| Rim height | 3.05 m |
| Lane width | 3.66 m (x = ±1.83 m) |
| Free-throw line from rim centre | 4.19 m |
| 3-point arc radius | 6.75 m |
| Corner 3 (straight section) | 6.60 m from rim centre, meets the arc at θ ≈ 12° |
| Restricted-area arc | 1.22 m radius |
| Half-court line from rim centre | 12.73 m |

**Named spots, derived from the constants**

| Label | Definition | Check |
| --- | --- | --- |
| Restricted area | r ≤ 1.22 m |  |
| Block (low post) | x = ±1.83 m, y 0.3–1.5 m | θ ≈ 9°–39°, r ≈ 1.9–2.4 m |
| Dunker spot | 2.0 ≤ \|x\| ≤ 3.5 m, y ≤ 0.6 m | θ ≤ 17° |
| Elbow | x = ±1.83 m, y = 4.19 m | r = 4.57 m, θ = 66.4° right, 113.6° left |
| Corner 3 | r ≥ 6.60 m, θ ≤ 12° (or ≥ 168°) |  |
| Wing 3 | r ≥ 6.75 m, 12° < θ ≤ 60° (mirrored) | 45° is the centre of the wing |
| Slot 3 | r ≥ 6.75 m, 60° < θ ≤ 80° (mirrored) |  |
| Top 3 | r ≥ 6.75 m, 80° < θ < 100° |  |
| Paint | \|x\| ≤ 1.83 m, y ≤ 4.19 m |  |

- Correction to the earlier "elbow is 45°": by the math the elbow sits at about 66° from the baseline; 45° is the wing.
- The wing, slot and top cut-offs are proposals; they will be checked against where players actually stand.

**Bins and grid (your angle idea, made exact)**

- Angle sectors every 15° (12 sectors across 0°–180°); 5° sectors for shot analysis
- Distance rings every 0.5 m from the rim to half-court; full-court rings for transition
- Rays at 0°, 30°, 45°, 60°, 90°, 120°, 135°, 150°, 180°: the diagonals and named angles
- Parallels: lines of constant x (parallel to the sideline) and constant y (parallel to the baseline) every 0.5 m
- Fine grid: 0.25 m × 0.25 m cells over the full court (115 × 61 cells) for heat maps and storage

**Relative geometry, computed every frame**

- Ball-handler frame: each player's distance (m) and bearing (degrees) from the ball-handler, with 0° pointing at the basket
- Defender to attacker: distance, goal-side or not, angular offset from the attacker–basket line
- Passing lane: the nearest defender's perpendicular distance (m) from the passer–receiver line and the angle at the passer
- Driving lane: angular width (degrees) of the open cone from the ball-handler to the rim
- Screen: screen angle relative to the handler's path, contact distance (m), screen duration (s)
- Spacing: mean pairwise distance of the four off-ball attackers (m), area of their convex hull (m²), each attacker's distance to the nearest defender
- Shot: release r and θ, contest distance (m), defender closing speed (m/s), shooter's facing angle to the rim
- Body facing: torso direction (degrees) relative to the basket and to the ball, from pose
- Strong side and weak side: sign of the ball's x

**Calibration**

- Court keypoints every frame (lane corners, free-throw line ends, arc ends, half-court line, centre circle, rim)
- Camera-to-court mapping per frame with lens distortion, smoothed over time; camera pan, tilt and zoom estimated
- Per-arena template for floor graphics, paint and glare
- Direction of play per half from the mapping plus the halftime switch
- Target accuracy to validate: median position error ≤ 0.30 m in the half-court

**Later, needs 3D**

- Ball height from its arc against the 3.05 m rim, release height, jump height

## Detection and tracking

The tracker always knows 10 players are on the floor; when it sees fewer, it records which ones are missing, which edge they left by, and where they probably are.

**Detect every frame**

- Players, referees, ball, rim and backboard, scoreboard; bench players and coaches detected and excluded
- Team label per detection: team A, team B, referee, other

**Track**

- Persistent ID per player across frames, through screens, crossings and occlusion
- Re-identification after camera cuts and replays
- Speed, acceleration, distance covered, direction changes, stops and starts
- Pose: body facing, stance, hands up (contest), jump, hips square or turned

**Player count check (your idea)**

- Every frame: count each team's players in view; expected 5 and 5
- Fewer than 10 → list exactly who is missing, using the on-court lineup from play-by-play

**Frame-exit memory (your idea)**

- When a track leaves the left or right edge, store exit side, court position, speed and heading
- While off-screen, predict where that player is from the exit state, the camera's movement and teammates' positions
- When someone re-enters on that side, match them to the stored track first
- Your fast-break example: if the last defender left the frame running toward the far rim, the system knows a defender is already waiting there, so a "3 on 2" is really a "3 on 3"

**Off-screen imputation**

- Estimate missing players from last-seen state plus the team's typical shape (Graph Imputer approach, trained on full-court tracking where every player is known)
- Carry uncertainty: a likely area, not a single point

**Ball**

- Position, who holds it, dribble vs held vs in flight, pass start and end, shot release

**Confidence**

- Every output carries a confidence score; low confidence feeds the flag queue

**Validation gates, bottom up (each must pass before the next is built)**

1. Player detection: every player found in every orientation (front, back, both sides, airborne, on the floor)
2. Team assignment: MSU vs opponent vs referee, per frame
3. Jersey number reading: from front and back, including partial reads
4. Ball detection: in hand, dribbled, passed, shot, loose, out of bounds
5. Scoreboard reading: clock, shot clock, score
6. Offense and defense side: which team attacks which basket, every second
7. Referee calls: whistle, signal, and the call type matched to play-by-play
8. Only then: actions, sets, schemes, value

**Detection, deeper**

- Players in every pose: crouched defensive stance, post seal, boxing out, diving on the floor, airborne for a block
- Referees separated from players by class and stripe pattern; their positions tracked too (lead, trail, centre)
- Ball: tracked through hands, dribbles, passes and shots; size check (a basketball is about 0.24 m across) to reject heads and shoes
- Rim and net: net movement confirms a make; rim contact flagged for rebounds
- Broadcast graphics that hide players (score bug, lower thirds, replay wipes) masked out per frame

**Tracking, deeper**

- Positions per frame in metres, plus velocity (m/s), acceleration (m/s²), heading (degrees), jerk for sudden cuts
- Footwork events: plant foot, jump stop, pivot, first step direction
- Contact events: screen contact, box-out contact, collisions before a foul
- Camera motion estimated every frame so player motion is separated from camera motion
- Track quality score per player per second; gaps longer than a set time sent to imputation and the review queue
- Pile-ups and scrambles: identities resolved once players separate
- Jump balls, held balls, out-of-bounds plays and free throws handled as fixed formations with known positions

**Out-of-bounds plays (ball off the court)**

- Detect a throw-in while the ball is still outside the court: inbounder's position beyond the line, the referee handing over the ball, players setting a formation
- Classify: sideline or baseline; front court or back court; which team; after-timeout or not
- Record the 5-second count, the formation (stack, box, line, diamond), the set run, and the first-pass target
- Same for free-throw formations: who is on each lane spot and who leaks out after the shot

## Sync and events

The on-screen scoreboard is the bridge: reading its game clock ties every video frame to the official play-by-play.

**Scoreboard reading (every second of live play)**

- Game clock, shot clock, score, period, team fouls, timeouts left, possession arrow
- Cross-check against play-by-play; a mismatch is flagged

**Alignment**

- Video time ↔ game clock ↔ play-by-play events (shots, makes, misses, rebounds, turnovers, fouls, substitutions, timeouts)
- Lineups on the floor for both teams at every moment, from substitutions

**Possession segmentation**

- Start, end, outcome, points, length, shot clock at the end
- Type: half-court, transition, early offense, after timeout, sideline out of bounds, baseline out of bounds, after a make, after a defensive rebound, after a turnover, after free throws

**Chances inside a possession (your definition)**

- A possession ends only when the other team gains control; every offensive rebound or shot-clock reset starts a new chance inside it
- Per chance: chance number, shot-clock start (30 s or the reset value), time used, how it ended (shot, foul drawn, reset, turnover)
- Counted features: offensive rebounds so far in the possession, kick-outs after an offensive rebound, put-backs, second-chance points
- Testable questions: after the 2nd offensive rebound, is MSU's scoring chance higher or lower than on the first chance? Does a reset with under 10 s used change shot selection?

**Transition clock (your idea)**

- Seconds since the change of possession (rebound, steal, turnover), counted from the catch
- Time to cross half-court, time to first shot
- Numbers advantage each second: attackers ahead of the ball vs defenders back (2 on 1, 3 on 2, 4 on 3), using tracked plus frame-exit players
- Who started the break (for example Jeremy Fears Jr. securing the rebound) and who filled each lane
- Value of the break at each second: how the scoring chance changes as defenders get back

**Shot events from video**

- Shooter, location, shot type (catch-and-shoot, pull-up, layup, dunk, floater, post move), nearest defender distance, contest, assisted or not and by whom
- Check: video shot locations against ESPN shot coordinates

## Event taxonomy: everything we count

Every event is stored separately, with its time, the players involved, their positions in metres, and the value before and after it, so no event hides inside another.

**Passing**

- Pass type: chest, bounce, overhead, lob, skip, kick-out, outlet, entry, post entry, handoff, tap pass
- Pass chain position: assist, the pass before the assist (hockey assist, e.g. Jeremy Fears Jr.'s pass two passes before a score), third pass back, screen assist
- Potential assist: a pass that led to a missed shot
- Pass speed (m/s), distance (m), angle change (degrees), lane openness, receiver's first action (shoot, drive, pass, hold)
- Deflected, intercepted, thrown away

**Ball-handling**

- Dribble count per touch, hand used, dribble type (crossover, between the legs, behind the back, hesitation, spin, retreat)
- Touch time (s) from catch to release, touches per possession
- Drives: start point, direction (baseline or middle, left or right), depth reached (r at the end), result

**Shooting**

- Shot type: catch-and-shoot, pull-up, step-back, floater, layup (hand used), dunk, hook, tip-in, put-back, free throw
- Bank shot vs direct (your question): tracked as its own attribute and tested; kept or dropped by the data
- Release point (r, θ), contest distance, shot clock left, dribbles before, touch time before
- Result: make, miss (front rim, back rim, air ball), blocked, fouled, and-one

**Rebounding**

- Offensive or defensive, contested or not, tip-out, tip-in, team rebound, long vs short (distance from rim)
- Box-outs made and lost, crashers per team, who leaked out

**Defensive events**

- Steals, deflections, blocks (kept in play or out), charges drawn, loose balls recovered, forced turnovers, contests

**Turnovers**

- Bad pass, lost ball, travel, double dribble, offensive foul, shot-clock violation, 5-second closely guarded, 10-second backcourt, 3-second lane, out of bounds, carry

**Fouls and referee calls**

- Foul type: shooting, non-shooting, offensive, loose-ball, technical, flagrant 1, flagrant 2, intentional, bench
- Who fouled whom, where (r, θ), shot clock, team-foul count, bonus or double bonus, free throws awarded
- Fouls drawn per player, and what follows: does MSU score more on the possession after drawing a foul?
- Referee detection: whistle from audio, referee signal from pose (foul, travel, 3-point attempt, timeout, jump ball), referee positions (lead, trail, centre)
- Calls matched to the play-by-play; disagreements flagged
- Crew tendencies: foul rate, home-away split, call types per referee
- Video reviews, held balls and possession-arrow use

**Stoppages**

- Timeouts (who called, when, score run before), media timeouts, substitutions (who for whom), injuries, end of period

**Sequence features built from events**

- What happened on the previous possession (score, foul drawn, turnover, offensive rebound) and its effect on the next one
- Runs: points in the last 2, 4 and 6 minutes for each team
- After a timeout: first set called, its outcome

## Actions and playbook recognition

College teams run a limited book of sets, so the system recognizes a play by matching tracked movement against written templates, then learns each team's own versions from your corrections.

**Actions (the building blocks)**

- On-ball: pick-and-roll, pick-and-pop, slip, re-screen, ghost screen, dribble handoff, keep fake
- Off-ball screens: down, flare, back, cross, stagger, pin-down, elevator, hammer
- Cuts: backdoor, basket, Iverson, curl, flare, shallow, UCLA, zipper
- Ball movement: entry pass, post entry, skip pass, kick-out, swing, extra pass
- Drives: left or right, baseline or middle, and the defender's reaction
- Big-man actions: post-up, seal, short roll, dive, lift, drift, dunker spot

**Sets (written as templates)**

- Examples to start with: Horns, Horns Iverson, 1-4 high, Floppy, Elevator, Spain pick-and-roll, Chicago action, Zipper, UCLA, Stack, Box, Hammer, 5-out motion, Flex
- Each template records: starting spots, roles (ball-handler, screener, cutter, shooter, big), the ordered actions, timing windows, and the usual counters
- Templates are mirror-aware: the same set run to the right or left side is one set

**How a possession is matched**

1. Convert tracked movement into role trajectories on the court model, mirrored to one side.
2. Score how closely the trajectories follow each template's steps in order (sequence alignment that tolerates speed differences).
3. Output: set name, confidence, and where the live play broke from the template (counter, switch, broken play).
4. Possessions that match nothing are clustered as possible new sets for you to name.
5. Once enough sets are labeled, a learned classifier (an end-to-end deep sequence model, DeepHoops-style) works alongside the templates.
6. Each team builds a playbook library over time: MSU's sets and every opponent's.

**Your configuration hypotheses become countable**

- "Handoff goes right, with Carson Cooper on the left block and Jaxon Kohler on the right block" is a configuration the system can count, then value against the same handoff with a different alignment
- Same for "right-wing pick-and-roll with a shooter in the corner"

**Template sources**

- Your own coaching knowledge, published coaching clinics and playbooks, MSU film once available, opponent scouting

**Worked example**

&#91;embedded content: set recognition · Horns Iverson worked example\]

The first three steps follow the template; at step 4 the screener slips to the rim instead of setting the screen, so the possession is labeled Horns Iverson with a slip counter, and the counter itself becomes data.

**Set instances on a timeline (your 0–2 s, 2–7 s idea)**

- Every set instance records: start time t0, the time each phase begins, end time, all to 0.1 s on the game clock and the shot clock
- Example record: Horns Iverson from 0.2 s to 7.0 s of the chance; alignment 0.2–2.0 s, Iverson cut 2.0–4.1 s, wing entry 4.1–4.8 s, ball screen 4.8–7.0 s
- Execution speed per phase: cutter speed (m/s), time from screen arrival to cut (s), time from catch to next action (s)
- Defensive response per phase: reaction delay after each pass (ms), defender displacement (m), coverage chosen
- Spacing per phase: mean attacker spacing (m) and hull area (m²)
- Value per phase: possession value at each phase boundary, so a phase that adds or loses value is visible
- Tempo questions the data answers: did this set score more when run faster or slower than its own average? Where does the defense break?
- Counters and broken plays recorded as their own phases, never forced into the template

**Set taxonomy by playbook style**

Offense is organized in eight families; each named set carries its start alignment, ordered actions, counters and the geometric signature to look for in tracking.

| Family | What it covers | Examples |
| --- | --- | --- |
| Transition | Primary break, lanes, rim runs | Izzo's push off makes and misses |
| Early offense | Secondary actions before the half-court set | Drag, double drag, pistol |
| Half-court alignments (motion starts) | How a set begins, about 25 alignments | Horns, 1-4 high, Box, Stack, 4-high, Chest |
| Continuity systems | Repeating patterns | 5-out, 4-out 1-in, read and react, flex, shuffle, swing, blocker-mover, Princeton, triangle, spread |
| Ball-screen offense | Every ball-screen type and its reads | High, side, empty-side, step-up, Spain, double (Detroit) |
| Post offense | Entries and post actions | High-low, duck-in, post split, post iso |
| Off-ball screens and cuts | Screen and cut vocabulary | Down, flare, back, stagger, hammer, Iverson, UCLA, zipper, chin, rip |
| Special situations | Non-standard possessions | After timeout, BLOB, SLOB, end of clock or game, zone offense, press break |

- European terms are kept as secondary labels in the vocabulary map; Synergy play types are a separate outcome label
- Defense taxonomy: man principles (pack line, gap, deny/top-lock, no-middle), 13 ball-screen coverages, off-ball screen coverages, post defense, zones including match-up, presses, junk defenses, and mid-possession scheme changes

**MSU's documented system**

- Identity: rebounding (the "War" drill, "hit-find-fetch"), pushing the ball after makes and misses, man-to-man about 90% of the time with a 2-3 zone as a change-up
- Ball-screen defense: historically flat or hard hedge; 2024-25 aggressive hedge-and-recover with some blitzing; 2025-26 coverage not publicly described, so film will decide
- About 20 MSU sets found with full sequences, including Chest, Chest Down, 14-Circle, Detroit (double ball screen), Hawk Double Cross, Rip to Mid Screen Iso, Over-Under, DHO Horns Chin, 4-High Iverson Curl, Down Screen DHO Veer ATO, DHO Clear Lob, MSU Zipper ATO, Special (vs 2-3), Screen the Inbounder (BLOB) and Line-1 (SLOB)
- Most public diagrams date from 2015 to 2023, so each template is confirmed against current film before it is trusted
- 2026-27: Kohler and Cooper leave, so templates must not overfit two-big lineups

**Template sources, ranked**

1. [FastModel PlayBank](https://playbank.fastmodelsports.com): frame-by-frame diagrams of many MSU sets, the closest thing to a template format
2. [FIBA Europe, Basketball Terminology (2024)](https://assets.fiba.basketball/image/upload/documents-corporate-regional-offices-europe-programs-fiba-europe-coaching-certificate-fiba-europe-basketball-terminology.pdf): a free, authoritative glossary for actions, coverages, zones and presses
3. Coach's Clipboard "Michigan State Sets" and the Tom Izzo Open Practice Series

Plan: hand-label 30–50 MSU possessions per set family from the free games to confirm which templates are still in use. Full taxonomy with about 115 sources: `research/set_taxonomy.md` in the project.

## Defensive structure

Every second, the system knows who is guarding whom, who is helping, and how the defense answered the last action.

- Matchup inference: each defender's assignment, every second (hidden-Markov approach from the review)
- Help position: distance from the ball, from his own man, in the gap or not
- Rim protector: who is under the rim (your "player C") and how far he is from the play
- Coverage per action: switch, drop, hedge or show, blitz or trap, ice, go under, go over, top-lock, deny
- Zone or man, and which zone (2-3, 3-2, 1-3-1, match-up); full-court or half-court press
- Rotations: help-and-recover timing, reaction delay after each pass, closeout distance and speed
- Shell shape: spacing between defenders, team centroid, area covered
- Switch outcomes: mismatches created (size, speed) and how long they last
- Rebounding: box-outs, how many crash the glass, who leaks out
- Transition defense: how many get back, cross-matches, who stops the ball
- Fouls: who fouls whom, where, foul trouble and its effect on aggressiveness

**Live scheme state, every second**

- A scheme label every second on both ends: man (pack line, pressure, deny), switch-everything, 2-3, 3-2, 1-3-1, match-up zone, box-and-1, triangle-and-2, full-court press (1-2-1-1, 2-2-1), half-court trap, junk
- Changes are detected as they happen: a 2-3 that turns to man after a ball screen is two states with a timestamp between them, not one label
- Signals used: whether defenders follow a man or guard an area (correlation of each defender's movement with an attacker vs with the ball), how defenders exchange attackers when they cross zones, starting shape after a made basket
- Smoothing so one odd second does not flip the label, plus a confidence score; low confidence goes to review
- Per chance: the sequence of scheme states, the attack that triggered each change, points scored in each state
- Ball-screen coverage per screen, off-ball screen coverage per screen, post defense (front, three-quarter, behind) per post touch
- MSU's own defense gets the same treatment

## Value and scoring

The scoring engine is possession value centered on the ball-handler: it is recalculated on every pass, and every action is credited with the change it caused.

**Possession value**

- Expected points at every moment, from the full 10-player state, the shot clock and the ball-handler frame
- Change in value per action (screen, pass, cut, drive), credited to the players involved
- Separate pieces for pass, shot and turnover chances, so a wrong decision shows separately from a bad shot

**Configuration value**

- Value of a set or alignment against the same action with a different alignment (your corner-shooter and two-bigs examples)
- Every configuration stat reported with its count and an uncertainty range

**Players**

- Shot quality: expected points per shot from location, contest, type and shooter
- Decision quality: value of the option taken against the best option open at that moment
- Off-ball value: how many defenders a player pulls (gravity), spacing he creates, screens that free a teammate
- Player vs player: points created and allowed in direct matchups, with the help defender's effect counted
- Within-game fatigue: continuous minutes, speed decline, effect on value

**Chemistry**

- Pair and lineup interaction terms: does A plus B beat what A and B do separately
- Passing networks: who passes to whom, more or less than expected
- Movement coordination: how in sync two players move (relative phase, timing of cut after screen)
- Screener and ball-handler timing on pick-and-rolls and handoffs
- Defensive cohesion: clean switches, rotation timing as a unit

**Coaches**

- Sets called after timeouts and their value
- Substitution patterns and rotation minutes
- Halftime adjustments: what changes in the second half
- Timeout timing against opponent runs
- Same for the opposing coach, and head-to-head history

**Game flow**

- Runs and momentum: whether value really changes after a run, or only feels like it

**Event-chain value**

- Value credited along the whole pass chain: scorer, assister, the pass before the assist, the screener, the player whose gravity opened the lane
- Value of a drawn foul: points from free throws plus the change in the next possessions (bonus, foul trouble on a key defender)
- Value of an offensive rebound by chance number
- Value lost per turnover type and per location

**Neural sequence model (the end-to-end layer)**

- Input: every frame's 10-player + ball state in metres, the global metadata, the event stream
- Output: probability of each possession outcome (score 2, score 3, foul drawn, turnover, miss) updated every 0.1 s
- Trained first on public full-court tracking, then fine-tuned on our MSU games
- Its predictions are checked against the simpler counted models; a gain must survive the held-out season

## Context features

Everything outside the play itself, listed without weights; each one will be tested, not assumed.

**Venue and crowd**

- Home, away or neutral; the specific arena; attendance and share of capacity; student section size; altitude
- Home-court history per team: how much each opponent gains at home
- Arena details: floor color, lighting, the backdrop behind each basket (shooting background), rim type

**Travel and schedule**

- Flight time and distance, time zones crossed, bus vs flight (your one-to-five-hour flight point)
- Days of rest for both teams, games in the last 7 and 14 days, back-to-back road games, first game home after a road trip
- Exam weeks, holidays, game time (noon vs night), day of week

**Officials**

- Referee crew identity, each referee's foul-rate tendency, home-foul tendency

**Jerseys (your idea)**

- MSU green vs opponent white, MSU green vs opponent colored, MSU white vs opponent colored, every combination
- Watch for confounding: in college the home team usually wears the light jersey, so jersey color mostly tracks home or away. The test has to separate the two, or it will rediscover home-court advantage and call it jersey color.

**Weather**

- Game-day and travel-day weather at both cities, mainly as a travel-disruption signal

**Stakes and storylines**

- Conference standing, seeding at stake, ranked opponent, rivalry, revenge game, senior night, nationally televised

**People**

- Injuries and availability, return from injury, minutes limits (your availability log)
- Roster continuity: transfers, freshmen's games played
- Coaches: Izzo against this coach historically, coaching experience

**Market**

- Opening and closing lines, line movement, public betting share where available

**Opponent's recent form**

- Last game result, overtime last game, days since, their travel

## Physical load and the physics of the shot

Tracking gives each player's workload and each shot's mechanics without wearables.

- Distance covered per minute and per possession (m), split by speed band (walk, jog, run, sprint; thresholds calibrated on our data)
- Accelerations and decelerations above a threshold (count per minute)
- Within-game decline: top speed and acceleration by period and by continuous minutes on the floor
- Recovery: change after timeouts, media timeouts and halftime
- Shot physics: release height and time (catch to release, s), arc and entry angle once the ball is tracked in 3D, release point relative to the defender's hand
- Free throws: routine time (s), arc consistency, effect of crowd and game state

## Behavioural and cognitive measures

Your psychology background makes this a distinct layer: decisions and reactions measured in time and space.

- Decision latency: time from catch to first action (pass, shot, drive), by player and pressure
- Reaction time on defense: delay from a pass or cut to the defender's first move (ms)
- Anticipation: defenders moving before the pass is thrown (interceptions, early rotations)
- Pressure: decisions and shooting under close contest, late shot clock, close score in the last 4 minutes
- After errors: shot choice and decision speed on the next possession after a turnover or miss
- Fatigue and decisions together: does decision quality drop with continuous minutes?
- Communication proxies on defense: switches executed cleanly vs late, two defenders on one attacker

## Broadcast audio and commentary as extra signals

- Speech-to-text of the commentary, time-aligned: announcers often name sets ("horns"), defenses ("they've gone to a zone") and calls; used as weak labels to check our detections, never as truth
- Crowd loudness curve: test whether it moves with runs and with opponent free-throw accuracy
- Whistle and buzzer timing to cross-check events

## Opponent scouting layer

- Each opponent gets the same profiles as MSU: set library, scheme frequency, player cards, coach tendencies
- Before each MSU game: how this opponent's defense has handled MSU's most-used sets in other teams' games
- Matchup forecasts: likely defensive assignments for each MSU player and their history

## Engineering and data standards

- One schema for every table, with units in column names (`x_m`, `speed_mps`, `clock_s`)
- Every run is reproducible: fixed random seeds, recorded code version, input file versions
- Automatic tests on every stage: counts of possessions vs box score, scores vs official, no player in two places
- Logs of every model decision with confidence, so any result can be audited back to the frame
- Pipelines that resume after a Colab disconnect without redoing finished games

## Rights, licenses and ethics

- Broadcast footage is copyrighted: used for private research only, never redistributed; published outputs are numbers, drawings and short excerpts within fair-use limits, to be checked
- No face recognition: identity comes from jersey, lineup, build and appearance
- Player data limited to public information and what the video shows; health details only from public reports
- Any dataset or open-source part we can lawfully access is usable for this research; a license register lists each component's terms

## Layered prediction and market benchmarks

One possession engine is simulated forward to produce every layer, so the game, half, segment and matchup numbers always agree with each other.

| Layer | Question | Market to compare against |
| --- | --- | --- |
| Game | Does MSU win; by how much; total points | Moneyline, spread, total |
| Half | Who wins each half | First-half spread and total |
| 5-minute window | Who wins minutes 0–5, 5–10, and so on | Live lines only; internal measure |
| Matchup | Does player A beat player B, with help defenders counted | Player props (points, rebounds, assists) |
| Possession | Expected points from this configuration | None; internal |

- Pre-game probabilities first; live, second-by-second probabilities only after the offline system is proven
- Every output is a probability with an uncertainty range
- Edge = our probability minus the market's implied probability after removing the bookmaker's margin
- Rest of the season simulated forward: which upcoming opponents MSU is favored against

## Odds and prediction-market data

Closing game lines for every MSU game since 2021-22 are free; first-half lines, player props and live lines have little or no archive, so we start collecting them ourselves now.

| Need | Source | Coverage | Cost |
| --- | --- | --- | --- |
| Closing spread, total, moneyline | [CollegeBasketballData.com](https://collegebasketballdata.com/api-tiers) `/lines` endpoint | Open and close per book, filterable to the Big Ten | Free key |
| Cross-check of the above | ESPN odds API via [hoopR](https://search.r-project.org/CRAN/refmans/hoopR/html/espn_mbb_betting.html) | Spread for all 163 MSU games over five seasons; open and close from 2022-23 | Free |
| Third check | [Sportsbook Reviews Online archives](https://www.sportsbookreviewsonline.com/scoresoddsarchives/ncaabasketball/ncaabasketballoddsarchives.htm), [Prediction Tracker](https://www.thepredictiontracker.com/basketball.php) | Spreadsheets for older seasons | Free |
| Timestamped multi-book lines, first-half lines, player props | [The Odds API historical data](https://the-odds-api.com/historical-odds-data/) | From May 2023 | About $59–$119 for one month |
| Prediction-market prices | [Kalshi API](https://docs.kalshi.com/getting_started/historical_data), [Polymarket price history](https://docs.polymarket.com/developers/CLOB/timeseries) | College basketball games from the 2025-26 season only | Free, no account needed to read |

**Start collecting now (no archive exists)**

- Player props each game day
- Live lines during MSU games (ESPN live odds, Kalshi 1-minute prices, Polymarket prices)
- First-half lines for every Big Ten game

**What the evidence says about these markets**

- College spreads are close to efficient: unbiased, with a typical miss of about 11 points (Wolfers, 2006)
- Moneylines lean toward favorites, so the bookmaker's margin is removed with the power or Shin method, not a simple proportional split
- No published study covers college first-half or player-prop markets: an open area for us
- None of KenPom, Torvik, Haslametrics, EvanMiya or ESPN BPI publishes accuracy against closing lines; we run that benchmark ourselves
- Closing-line value (our probability vs the closing line) is the evaluation standard; any staking uses a fraction of Kelly at most

**Access note**

- Michigan users currently cannot trade sports contracts on Kalshi, Robinhood, Polymarket US or Novig after court and state action in 2026 ([Spectrum News](https://spectrumlocalnews.com/mi/michigan/news/2026/09/02/michigan-judge-blocks-kalshi)). Reading public price data for research is a separate activity; not legal advice.

Full research, with every source: `research/odds_markets_research.md` in the project.

## Human-in-the-loop flagging and labeling

The system asks you about the moments it is least sure of, and every answer becomes training data; this is how it improves game by game.

**When it flags**

- Low confidence on a player's identity or a jersey number
- Ball lost, or a scramble (four or more players around a loose ball)
- Player count not 10 for longer than a set time
- Scoreboard reading disagrees with play-by-play
- Set match below a confidence threshold, or a possession that matches no template
- Coverage or matchup unclear after a switch

**What you see for each flag**

- A short clip from a few seconds before to after the moment, with the top-down view beside it
- The model's current guess, prefilled
- One-click confirm, or correct the label

**What happens next**

- Corrections are saved as labels with who, when and which model version
- The model retrains on a schedule, asking first about the cases it is least sure of (active learning)
- A running count of labels per class shows where data is thin

**Label types**

- Boxes, track IDs, jersey numbers, court keypoints, ball position, actions, sets, coverages, possession type

**My part**

- Cut the clips, prefill the guesses, log your corrections, keep the label counts, retrain

**Tools**

- Candidates: CVAT, Label Studio, FiftyOne, Roboflow (license and fit checked in the open-source audit)

## Visualization layer

Every number the system produces can be traced back to the moment of video that produced it.

- Broadcast video and a top-down court replay side by side, in sync
- Movement trails for every player, every pass drawn as an arrow, every switch marked
- Possession value curve across the possession, each action's change marked on it
- Set recognition overlay: the template's path shown faintly beside the players' real paths
- Matchup board: who guarded whom, for how long, with what result
- Heat maps per player, per lineup, per set
- Passing network per game and per season
- Layered win-probability view: game, half, 5-minute windows
- Filters by player, lineup, set, coverage, opponent, game, period
- Export any moment as a clip with its overlays

## Compute and storage

Colab works for this if video is processed once into small files and only those are reused; the budget is GPU hours, not raw power.

**Decisions (17 Oct)**

- Quality first: G4 (RTX PRO 6000, 96 GB) is approved when quality needs it
- Budget: 300 compute units now (about 34 G4 hours), plus 100 a month; units expire after 90 days, so they are spent, not saved
- Everything lives in Google Drive: raw video, processed data, labels, models
- Colab is driven from Claude through the Colab MCP server once it is installed

**Colab GPUs and cost per hour** ([McCormick, checked March 2026](https://mccormickml.com/2024/04/23/colab-gpus-features-and-pricing/))

| GPU | Memory | Compute units per hour |
| --- | --- | --- |
| T4 | 15 GB usable | 1.19 |
| L4 | 22.5 GB | 1.71 |
| A100 40GB | 40 GB | 5.40 |
| A100 80GB | 80 GB | 7.52 |
| G4 (RTX PRO 6000) | 96 GB | 8.71 |
| H100 | 80 GB | not yet published |

- No H200 appears on Colab's list.
- Colab Pro has included 100 compute units a month (approximate; confirm in your Colab resources panel). That is about 18 A100-40GB hours, 58 L4 hours or 84 T4 hours a month.
- Idle runtimes still spend units, and the runtime disk is wiped when a session ends ([explainx summary of Colab FAQ](https://explainx.ai/blog/google-ai-pro-colab-a100-h100-200-compute-units-claimed-vs-verified-2026)).

**How to fit the budget**

- Run detection and tracking once per game; save tracks, events and features as small files (tens of MB per game, to be measured on the first game)
- Use L4 or T4 for processing video, A100 only for training
- Process in chunks that can resume after a timeout; save model checkpoints often
- Measure real GPU hours on the first game before planning the season

**Storage**

- One Drive folder for the project:
  - `raw_video/<season>/<date>_<opponent>_<source>.mp4`, never edited or overwritten
  - `registry/` games, rosters, player cards, availability log
  - `processed/<game_id>/<version>/` tracks, events, features as Parquet files
  - `labels/` your review corrections, with who, when and model version
  - `models/<name>/<version>/` checkpoints and their evaluation reports
  - `reports/` per-game and per-season outputs
- Size estimate: about 5.4 GB per 2-hour game at 1080p; 13 games about 70 GB, a recorded season about 190 GB more
- Processed versions are kept side by side, so any result can be rebuilt from the exact inputs

**Other options if Colab is not enough**

- Hourly GPU rental (Lambda, RunPod, vast.ai)
- MSU's high-performance computing center (ICER); access usually needs a faculty sponsor, to be confirmed

## Validation and evaluation

Every stage is checked against something independent before the next stage is allowed to use its output.

**Against official records**

- Score and clock from the scoreboard reading vs the official play-by-play
- Shot locations from video vs ESPN shot coordinates
- Possession counts vs the box score
- On-court lineups vs play-by-play substitutions

**Vision quality**

- Tracking accuracy (HOTA and ID switches, the standard tracking scores)
- Identity accuracy per player per game on a hand-labeled sample
- Court mapping error in feet
- Set recognition precision and recall against your labels

**Prediction quality**

- Walk-forward testing: train only on games before, predict the next game
- 2025-26 held out until the end
- Calibration: events we call 60% happen about 60% of the time
- Scored with log loss and Brier score, and against the closing line

**Research discipline**

- Hypotheses written down before testing (registry kept in this project)
- Correction for testing many features at once
- Every configuration result reported with its count and uncertainty range
- A small-sample rule: below a minimum count, a result is shown as descriptive only

## Hypothesis registry (first entries)

Each hypothesis is written before it is tested, with its measure and the minimum count needed; results are reported as found, including nulls.

| ID | Hypothesis | Measure |
| --- | --- | --- |
| H1 | Right-wing ball screen with an above-average shooter in the corner raises MSU points per chance | Points per chance vs same screen without that shooter |
| H2 | A handoff to the right with bigs on both blocks scores differently from other handoff alignments | Points per chance by alignment |
| H3 | After the 2nd offensive rebound in a possession, MSU's scoring chance changes | Points per chance by chance number |
| H4 | The possession after MSU draws a foul scores more than average | Points on the next possession |
| H5 | Fears Jr.'s pass before the assist adds value beyond his assists | Value credited to the hockey-assist pass |
| H6 | Running a set faster than its own average changes its outcome | Points per instance by execution-speed bin |
| H7 | A defense switching from zone to man mid-chance concedes more | Points per chance with vs without a switch |
| H8 | Jersey color matters after controlling for home and away | Margin, with home/away held fixed |
| H9 | Bank shots from specific angle sectors are more accurate than direct shots | Make rate by sector and shot type |
| H10 | Travel distance and time zones crossed lower first-half efficiency | Points per possession, first half |

## Open questions and decisions

These need your answer before the requirements are ranked.

- [x] Sample size: start with the free games; you record every 2026-27 game on B1G+, and add older games back to 2024 when the core roster was together
- [x] "Low ball" is low post
- [x] Availability log: you fill or confirm statuses; I search news for each game date
- [x] Nano Banana images: tested later, not now
- [x] MSU pitch: after the first 13 games are processed
- [x] Storage: everything in Google Drive; compute: G4 approved when quality needs it
- [ ] Confirm the first 13 games: 2026 tournament (North Dakota State, Louisville, UConn), 2025 tournament (Bryant, New Mexico, Ole Miss, Auburn), 2025-26 regular season (Illinois, Duke, Kentucky), then 2024 games to fill the rest
- [ ] B1G+ recording quality: resolution and frame rate on your first recording
- [ ] Historical betting lines: plan set (see the odds section); first job is pulling closing lines for every MSU game since 2021-22
- [ ] Set-template sources: FastModel PlayBank first; about 20 MSU sets documented, to be confirmed against film
- [ ] First templates: generic sets or MSU's own plays you know (comment thread on the set list). Licenses decided: any dataset or open-source part we can lawfully access may be used for this research; every component's license is logged so non-commercial terms are known if the project ever goes commercial.
