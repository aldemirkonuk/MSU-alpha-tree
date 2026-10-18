# Perspective review: senior sports data engineer

Date: 2026-10-18. Status: PROPOSAL ONLY. Nothing in the live requirements doc, the schemas or the code was edited; this file is add-only. The requirements session decides.

Persona: a senior sports data engineer who has built tracking and play-by-play pipelines (event streams, video ingestion, Parquet lakes, orchestration, data contracts, lineage). What I care about, in order: (1) one clean event/state model that follows the rules' state machine exactly, with every transition typed and stamped on all four clocks (`video_ts_ms`, game clock, shot clock, UTC); (2) idempotent, replayable pipelines; (3) keys and joins across sources; (4) late, out-of-order and corrected data; (5) contracts and invariants; (6) throughput, storage and reprocessing cost; (7) the public-repo versus private-Drive line.

Persona letter for new IDs: **E** (`new-<FAMILY>-E<n>`). Highest existing proposal numbers checked in `coord/requirements_inbox/002..007`, `config/invariants.yaml` (new-IV-34) and the docs (new-EV-13, new-RF-12, new-MK-19, new-CX-8, new-PC-7, new-ST-8 ...); the E prefix avoids every clash.

Units: m, cm, s, ms, degrees, m/s, m/s², counts, bytes. Estimates are marked "(estimate)"; anything not checked is "(unverified)". No web pages were opened for this review; every source is a repo or scratchpad file listed at the end.

---

## 0. The short version

The 104 proposed tables are careful about meaning (rule citations, units, licence class, as-of rules) and weak on mechanics: keys that collide across passes and video files, no content-addressed versioning, no clock-alignment table, an MSU-centric global stamp, per-frame denormalisation of a state that changes a few hundred times a game, and two YAML dialects. The markets package is the most mature code in the repo and already shows the failure mode the rest will hit: a de-duplication key that is not stable under re-runs.

For the first two games (UConn 401856571, Louisville 401856531: VP9 1920×1080, 29.97 fps constant, 155,492 and 161,653 frames, condensed replays, `results/w3_intake/README.md`), I would build 43 tables (3 of them new), not 104, around two new backbone tables: `clock_map` (video ↔ game clock ↔ shot clock ↔ UTC) and `state_transitions` (one typed row per rule-defined state change). Everything else either hangs off those two or waits.

---

## 1. THINK: game flow as a state machine (2026-27 NCAA men's rules)

### 1.1 The state is a product of independent dimensions, not one enum

The rules separate things a single "ball state" column conflates. The clearest case: on a throw-in the ball becomes **live** when it is at the thrower's disposal (Rule 6-1.2.b), but the **game clock starts** only when an inbounds player legally touches it (Rule 5-10.2.a), and the **shot clock** starts on the same touch (5-10.3.a). For up to 5 s (7-6.6) the ball is live and both clocks are stopped. A free throw is the same: live at the free-thrower's disposal (6-1.2.c), clock stopped until a missed last attempt is touched (5-10.2.c). So the data model needs these as separate typed columns, each with its own transition rules:

| Dimension | Values | Governing rules | Stored today in |
|---|---|---|---|
| Ball status | live, dead | 6-1 (live), 6-5 (dead), 6-6 (not dead while a try is in flight) | `state_frame.ball_live` |
| Game clock | running, stopped; value 0-1200 s (0-300 s OT), tenths under 60 s | 5-10 (start), 5-11 (stop), 5-12 (corrections), 1-18.2 (tenths) | `state_frame.game_clock_s`, `game_clock_running` |
| Shot clock | running, stopped, off; value 0-30 s | 2-11.1 (30 s), 2-11.6 (resets), 2-11.2/2-11.8 (off, reactivated at 20 s), 5-10.3 (start) | `state_frame.shot_clock_s`, `shot_clock_status` |
| Team control | team A, team B, none | 4-9.1/4-9.2 (player and team control), 4-9.4 (no team control during a try, jump ball, rebound tap) | `team_in_possession` |
| Try in flight | none, in flight (and whether it touched ring/flange) | 6-6.1; 2-11.6.d.1 needs ring contact | `try_in_flight`, `ring_contact` |
| Restart pending | none, jump ball, throw-in (side, half, team, cause), free throw (k of n, award type) | 6-5.2 (three ways to resume), 6-2, 7 (all), 8 (all) | `restarts`, `free_throws` (rows, not a state column) |
| Stoppage | none, foul, violation, held ball, timeout (30/60/75, media), review, challenge, injury/blood, period end, intermission | 5-11.1 to 5-11.9, 5-13 to 5-17, 11, 11-4 | `stoppage_type` |
| Period phase | pregame, period k, intermission, final | 5-6 to 5-9 | `period` |
| Counts | team fouls per half, bonus, timeouts left by length, challenge available, arrow | 8-2, 5-14.8 to 5-14.10, 11-4.1.d, 6-3 | `foul_state`, timeout columns, `possession_arrow` |

Data-engineering consequence: a frame's state is the as-of value of each dimension. Each dimension changes rarely (an estimated 600-1,200 transitions per game across all dimensions), while there are 155,000-162,000 frames. Storing the state once per transition and deriving per-frame values is both cheaper and safer than stamping 102 columns on every frame (section 4.1, finding K6).

### 1.2 Transition table (the state machine I would encode as `config/state_machine.yaml`)

Each row is one typed transition. "Clocks" lists what happens to game clock (GC) and shot clock (SC). "Seen by" lists which sensor can observe the trigger first; the latency column is what a pipeline must tolerate.

| # | Transition (from → to) | Trigger | Rule | Clocks | Seen by (latency) |
|---|---|---|---|---|---|
| T01 | pregame/intermission(OT) → live, no control | jump-ball toss leaves the official's hand | 6-1.2.a, 6-2 | GC starts when the toss is legally touched (5-10.2.b) | CV (frame); PBP "jump ball" (1 s) |
| T02 | no control → team control | player gains control after a jump ball or a try | 4-9, 5-10.3.b | SC starts | CV only |
| T03 | team A control → team B control (live) | steal, defensive rebound, loose ball recovered | 2-11.6.b.1, 2-11.6.b.4 | SC reset to 30 | CV; PBP rebound/turnover (1 s) |
| T04 | control → try in flight | release of a try | 6-6.1, 4-9.4 | both keep running; ball stays live until the try ends even if a whistle blows | CV (release frame ±1 frame = ±0.033 s) |
| T05 | try in flight → dead (made goal) | ball passes through the basket | 6-5.1.a, 5-1 | GC keeps running, except it stops in the last 59.9 s of the 2nd half and OT (5-11.9, 2-10.12); SC to 30 for the opponent on its touch | CV (net frame); scorebug +1.50 to +2.60 s, median 1.933 s (measured, `results/w3_intake/made_basket_lag.md`); PBP 1 s |
| T06 | try in flight → offensive control after ring contact | offensive rebound | 2-11.6.d.1 | SC flat 20 s whatever was left; new chance, same possession | CV; arena shot clock resets at ring contact, 0.97 s before to 0.47 s after the make frame (measured) |
| T07 | try in flight (no ring contact) → offensive control | airball rebounded by the offense | 2-11 (no reset listed) | SC continues; a violation if it expires (new-IV-06) | CV only; the 20 s/no-reset split is invisible in PBP |
| T08 | try in flight → defensive control | defensive rebound | 2-11.6.b.4 | SC 30 | CV; PBP |
| T09 | live → dead (foul) | whistle for a foul | 5-11.1.a, 6-5.1.d (but 6-6.1 if a try is in flight) | both stop | audio whistle (frame); PBP 1 s; officials' signal |
| T10 | dead (foul) → free-throw pending | foul with FT award (shooting, bonus 7th, double bonus 10th, technical, flagrant) | 8-2.1, 8-2.2, 10-1 Penalty, 10-3, 10-4 | GC stopped through the FTs | PBP; lane formation in CV |
| T11 | dead (foul) → throw-in pending | common foul before the bonus, player-control foul | 10-1 Penalty a, 7-3.2.b | SC 30 (backcourt, 2-11.6.b.5) or max(20, left) (frontcourt, 2-11.6.c.1) | PBP; CV throw-in spot |
| T12 | FT k of n → FT k+1, or → live, or → throw-in | each attempt result | 8-5, 8-6, 8-7 | GC starts only when a missed last FT is touched (5-10.2.c) | CV, PBP, scorebug "1 SHOT"/"2 SHOTS" label |
| T13 | live → dead (violation) | travel, 3 s, 5 s closely guarded, 10 s backcourt, backcourt, kicked ball, OOB | 6-5.1.g, 9-3 to 9-14, 9-9.2, 9-10, 9-14.2 | both stop; SC per the reset table | PBP (turnover type); CV for counts |
| T14 | live → dead (held ball) → AP throw-in | held ball | 6-5.1.c, 6-3, 6-4 | SC per arrow: no reset / 30 / 20 (2-11.6.a.4, b.3, d.4); arrow flips when the AP throw-in ends | PBP; scorebug arrow ("POSS" is the arrow, measured) |
| T15 | dead → throw-in → live, clocks running | ball at thrower's disposal, then legal touch inbounds | 6-1.2.b, 7-6.6, 5-10.2.a, 5-10.3.a | GC and SC start on the touch; at least 0.3 s off in the last 59.9 s (5-10.2.d) | CV; OCR clock start (scorebug lag to measure per field) |
| T16 | any dead → timeout | team request granted, or media slot | 5-11.3, 5-11.4, 5-14, 5-14.10.c (first dead ball at or after 16:00, 12:00, 8:00, 4:00) | stopped; timeouts left decrease; SC no reset (2-11.6.a.3) | PBP; scorebug timeout bars (matched every UConn timeout, measured) |
| T17 | live/dead → review / coach's challenge | official review or challenge | 11, 11-4.1 | frozen; may correct score, clock, possession; failed challenge costs the timeout | PBP text; video replay segments; scorebug bar drop and restore (measured at 2nd half 11:11 UConn) |
| T18 | state value → corrected value | timing or scoring correction | 5-12.1 to 5-12.5, 2-9.13 | GC may go UP (Louisville 4:06 → 4:07, measured); never carried across halves | OCR (non-monotone clock); PBP revision |
| T19 | SC on → off / off → on at 20 | game clock below a shot-clock period; 2-11.6.d situation | 2-11.2, 2-11.8 | SC display blank (10 of 177 samples had the slot blank, measured) | OCR |
| T20 | live → dead (period end) | game clock reaches 0.0 | 5-11.2.a, 5-7, new-IV-23 (try released before zeros counts) | GC 0.0 | OCR, audio horn |
| T21 | period end → intermission → next period | half time; OT intermission | 5-8, 5-9 | team fouls reset at period 2; extend into OT (5-9.4); baskets change at half only | PBP; video (half time cut to about 3 min in condensed replays, measured) |
| T22 | dead → dead (substitution) | sub beckoned during a dead ball with clock stopped | 3-x substitution articles (via R-IV-03), new-IV-25, new-IV-26 | none | PBP (1 s, timing errors known, R-DQ-09); CV identity |
| T23 | live → dead (injury/blood) | official suspends play | 5-11.2.b, 5-11.6 to 5-11.8 | stopped; SC no reset (2-11.6.a.2) | PBP sometimes; video |
| T24 | period k → final / forfeit | last period ends with a winner | 5-6, new-IV-30 | none | PBP; registry |

### 1.3 Which clocks run in which state

| State | Game clock | Shot clock | Video time | UTC |
|---|---|---|---|---|
| Live, team control | running | running (or off, 2-11.2) | running | running |
| Live, throw-in or FT at disposal, not yet touched | stopped | stopped | running | running |
| Try in flight | running | running (horn does not kill the try, 6-6) | running | running |
| Dead after a made goal, not last 59.9 s of 2nd half/OT | **running** | stopped (resets on the inbound touch) | running | running |
| Dead (whistle), timeout, review, injury | stopped | stopped | running, or **cut** in a condensed replay | running |
| Intermission | stopped | off | mostly cut (3.2 of 21.4 min of UConn's half time kept, measured) | running |

The last two columns are the data-engineering problem: in the two files we have, video time is not a linear function of UTC. UConn has 86.5 min of video for 134.4 min tip-to-final in the PBP wall clock (`results/w3_intake/intake_check.csv`). Video time maps linearly to game clock only inside running-clock stretches (R-MD-08), and to UTC only through PBP `wallclock`, which CBBD documents as nullable and which the source map found **not monotonic** (`docs/data/source_field_map.md`, line 739). Every in-game join with 1-minute prediction-market prices (R-MK-03, R-MK-16) therefore goes through game clock → PBP wall clock → UTC, never through video time.

### 1.4 Where the flow is decided (decision points) and who decides

| Decision point | Decider | Window | What it changes in the data |
|---|---|---|---|
| Shoot, pass, drive, hold | ball handler | 0.2-3 s per touch | ends a touch; may end a chance |
| Push or pull back after a change of control | handler, coach's rule | first 2-6 s (R-TR-08 to R-TR-16) | transition class |
| Coverage on a ball screen | X-big, X-ball | t0 − 1.0 s to t0 + 2.0 s (`docs/taxonomy/defense_full.md` F3.0) | `screens.coverage_code` |
| Foul or not (take foul, foul to extend, foul when up 3) | defender, coach | last 60 s (`config/invariants.yaml` foul_to_extend_clock_s: 60) | foul type, FT award, possession count |
| Whistle | official | immediate; review later | stoppage; the largest single source of state changes |
| Timeout / challenge | head coach (player in live play) | any dead ball; live ball with control (5-11.3) | timeouts left; ATO set; scheme change |
| Substitution | coach | dead ball, clock stopped | lineup stint; identity candidates (R-ID-03) |
| Clock start/stop | timer, shot-clock operator | 0.1-0.5 s after the trigger (estimate) | the clock values everyone else uses |
| **Camera cut, replay, graphics** | **broadcast director** | continuous | **whether we observe anything at all** (scorebug absent in 16.9% of samples; replays 0 of 17 with a bug; main wide 95 of 177 samples, measured) |

The last row is the one analysts forget. It belongs in the state machine as an observability dimension (`camera_shot_type`, `scorebug_visible`, `coverage_score`), and every derived metric needs the share of its time base actually observed (R-PL-05 does this for load only).

---

## 2. UNDERSTAND: how teams react, seen as data

Each trigger produces a burst of state changes and events. The engineering questions are: which table catches the response, how fast it happens (so we know the join window), and which source can see it.

| Trigger | Typical offensive response | Typical defensive response | Speed | Signature in data | Lands in | Gap |
|---|---|---|---|---|---|---|
| Made basket | inbound fast (push off makes, R-TR-14) or walk it up; run the end line (new-IV-16) | press or get back; matchups in transition | inbound 1-5 s after the net; crossing half-court 4-8 s (estimate) | net frame → inbound release → inbound catch (R-TR-21 anchors); scorebug +1.9 s | `made_basket_events`, `restarts`, `transition_phases` | inbound release often off camera after a cut to the scorer |
| Miss, long rebound | outlet, numbers break; crash or leak-out | 1-2 back, ball stopped, crash vs get back | secure to outlet 0.5-1.5 s; defense set 4-8 s (R-TR-08 rule) | rebound distance, numbers state at 10 Hz (R-TR-22) | `rebounds`, `transition_numbers` | rebound distance needs the ball, 3D height absent |
| Live-ball turnover | immediate break; highest transition PPP | sprint back, take foul (R-TR-25) | 0-3 s | steal frame; numbers advantage at the secure moment | `turnovers`, `transition_phases` | steal attribution at 1 s PBP resolution |
| Foul to the bonus (7th, 10th) | attack the rim, draw fouls | less hand-checking; foul-trouble subs | possessions, not seconds | team fouls state; FT award type | `foul_state`, `free_throws` | scorebug shows "BONUS" at the opponent's 6th foul and "BONUS+" at 9 (measured): the label leads the state by one foul; do not read it as the state |
| Timeout (called) | ATO set; lineup change | scheme change, matchup swap | effect on the first possession after the restart (beliefs B2 hypothesis new-8: restart within 5 s) | `timeouts` → next `set_instances`, `scheme_changes`, `substitutions` | `timeouts`, `scheme_changes` | condensed replays cut most of the timeout, so timeout duration is not measurable from video (W3 point 4) |
| Media timeout | same as above, weaker | same | every ~4 min of game clock (16/12/8/4, 5-14.10.c) | slot id, first dead ball at or after the mark | `timeouts` (type media) | slot inference needs the 30 s pre-mark rule (5-14.10.e) |
| Ball screen | reject, use, split, snake; roll, pop, slip, short roll | 13 coverages (R-DF-06), tag by low man | coverage resolves in t0 − 1.0 to t0 + 2.0 s; tag 0.5-1.5 s after the roll starts (estimate) | screener speed ≤ 0.3 m/s for ≥ 0.5 s within 1.2 m (R-ST-17 strict) | `screens`, `actions` | needs 10 players in view; main wide only |
| Post entry | seal, dump, re-post, kick-out | front, 3/4, behind (R-DF-07); double from a fixed spot | entry pass to double 0.5-2.0 s (estimate) | `post_touches`; defender side relative to the post player | `post_touches` | post seal angle needs pose |
| Drive | finish, kick, dump-off | help from the gap, rotate, X-out | help onset 0.2-0.6 s after the drive starts (estimate; R-CO-02 measures it) | drive ≥ 3 m toward the rim (R-EV-06) | `drives`, `reaction_events` | reaction onset below the derivative noise floor (section 3.3) |
| Skip pass | swing, attack the closeout | closeout distance and speed, rotate | ball flight 0.6-1.0 s across ~12-14 m (estimate) | `passes.distance_m`, closeout in `defensive_events` | `passes` | ball often lost against the crowd at the far sideline |
| Zone look | overload, gap drives, short corner, high post | match-up zone rules | recognised in the first 3-6 s of the half-court set | `scheme_states` per second (R-DF-04) | `scheme_states` | label confidence is the product; store it |
| Press | press-break alignment, middle flash | trap, rotate, fall back | inbound to trap 1-3 s; beaten press shows as transition | full-court shape after a make (R-DF-12, R-DF-18) | `scheme_states`, `restarts` | backcourt often out of frame on the main camera |
| Foul trouble | hide the player, sub | sit the starter (Izzo sits two-foul starters most; starters with two first-half fouls foul at 1.71 per 40 min vs 2.66 with none, `docs/research/beliefs_register.md` C3) | immediately at the next dead ball | personal fouls by period (R-MD-16) | `foul_state`, `substitutions` | PBP substitution timing errors (R-DQ-09) |
| End of clock (shot or game) | hold, two-for-one (33-45 s window), last shot | foul up 3, switch everything | last 60 s of a period, last 5 s of the shot clock | SC off/on, tenths, 0.3 s rule (5-10.2.d) | `state_transitions`, `shots` | clock tenths below 1:00 only; condensed replay keeps all live play (no cut detected, W3) |
| Scoring run | timeout, scheme change, sub | same | run = net ≥ 8 in a rolling 120 s (beliefs B2 shared definition) | `score_events` rolling window | derived view | regression to the mean in any before/after test (B2) |
| Lineup change | new set family, new tempo | matchup re-assignment | first possession after the change | new `lineup_stints` row | `lineup_stints` | ID resolution from CBBD athlete IDs to ESPN IDs (source map: play athlete IDs are CBBD IDs) |
| Opponent hot shooter | more touches for the shooter | top-lock, switch the matchup, deny | within 1-3 possessions | matchup change per second (R-DF-01) | `defensive_matchups`, `scheme_changes` | "hot" needs a fixed rolling definition (A1) |

What this means for the pipeline: almost every reaction is a **pair of rows in different tables linked by time**. The joins need (a) one common time base per pass (`clock_map`), (b) a declared join window per pair (e.g. timeout → first set within the next possession; screen → coverage within t0 + 2.0 s), and (c) explicit "not observed" rows rather than missing rows, so a reaction that happened off camera is not counted as "no reaction".

---

## 3. ANALYZE: how each role moves, as data volume and event types

### 3.1 Per-role movement signatures and what they cost

Speeds are court-plane magnitudes of the named tracked point (R-PL-10). Peak reference: NCAA D-I men's game peaks about 7.04 ± 0.39 m/s (guards), 6.63 ± 0.52 (forwards), 6.23 ± 0.33 (centres) (Stone et al. 2022, Kinexon 20 Hz, as summarised in `docs/research/load_thresholds.md`). Volumes are per game, both teams, from typical D-I counts (estimate; measure on game 1).

| Role | Movement signature (metric) | Event types it emits | Volume per game (estimate) | Needed sample rate and accuracy | Broadcast 1080p 29.97 fps can / cannot |
|---|---|---|---|---|---|
| Ball handler | 0-7 m/s; first step 2-4 m/s² (estimate); hesitation = speed drop ≥ 1.5 m/s within 0.3 s then re-acceleration; drive gains ≥ 3 m toward the rim (R-EV-06) | touch, dribble, drive, pass, shot, turnover, foul drawn | touches 700-1,000; dribbles 2,500-4,000; drives 60-100 | position 10 Hz at ≤ 0.3 m; event timing ±1 frame (0.033 s) | can: path, dribble count (ball visible), release frame. cannot: dribble moves when the ball is occluded by the body; hand used, reliably |
| Screener | approach 1-4 m/s, set ≤ 0.3 m/s for ≥ 0.5 s within 1.2 m of the user's path (R-ST-17 strict) | screen (on-ball, off-ball, handoff), roll, pop, slip, short roll | ball screens 60-110; off-ball 80-150 | 10 Hz; position ≤ 0.3 m; screen moment from minimum screener–defender distance (R-ST-20) | can: set and roll from the main camera. cannot: contact (legal vs moving screen) |
| Roller / popper | roll 3-6 m/s toward the rim within 0.5-1.0 s of the screen moment; pop to the arc at 6.75 m | roll, pop, catch, finish | 60-110 follow-ups | 10 Hz | can; lob apex needs 3D ball height (R-ST-26) |
| Spacer / shooter | relocate, lift, drift 1-3 m at 1-4 m/s; catch-and-shoot release 0.5-0.9 s after the catch (estimate) | relocation primitive, catch, shot | 200-300 relocations | 10 Hz; shot release ±1 frame | can, except far-corner spacers partly out of frame on tight zoom |
| Cutter | V/L-cut direction change ≥ 45° within 0.5 s at ≥ 3 m/s entry (new-PL-2 rule); back cut sprint 5-7 m/s | cut primitive by type (new-ST-3 list) | 150-250 | 15-30 Hz around cuts for the angle; heading needs ≤ 0.1 m position noise | heading change is the noisiest signal we have; classify cuts on path shape over ≥ 1 s |
| Post | seal (low speed, contact, torso facing), 0-2 m/s; duck-in | post touch, seal, re-post | 30-70 post touches | 10 Hz + pose | can: location. cannot: seal force, arm bar |
| Rim protector | vertical: jump; horizontal 0-4 m/s; stays at r ≤ 2.5 m | contest, block, verticality | 100-150 contests at the rim | jump height needs 3D (R-CG-11) | can: r, contest presence. cannot: jump height without 3D |
| On-ball defender | lateral slide 2-4 m/s; backpedal; closeout 3-6 m/s decelerating ≥ 3 m/s² in the last 1.5 m (estimate) | contest, deflection, steal, foul, closeout | closeouts 150-250 | 10-30 Hz around closeouts; deceleration is beyond the broadcast noise floor (3.3) | can: distance at release (new-EV-11). cannot: reliable deceleration bands |
| Help defender | gap position, step-and-release (Izzo one-step help, R-DF-15), stunt ≥ 1.0 m and back within 1.0 s (`defense_full.md` 0.4) | help, stunt, rotation, tag | per second for all 5: 2 × 2,400 s × 5 = 24,000 defender-seconds of live play (estimate, upper bound) | 1 Hz state, 10 Hz around events | can on the main camera; weak-side help often off frame |
| Tag / low man | 1-3 m move toward the roller within 0.5-1.5 s of the roll | tag event | 50-100 | 10 Hz | can when the roller and the low man are both in frame |
| Rebounder | box-out contact, pursuit 2-5 m/s, jump | box-out, rebound, tip | 65-80 rebounds, 150-250 box-outs | 10 Hz + ball flight | can: who is inside. cannot: contact force; rebound landing point needs the ball |
| Officials (lead, trail, centre) | trail and lead positions; rotation after fouls (new-RF-8) | whistle, signal, rotation | 60-90 whistles; ~30 rotations | 1-5 Hz is enough | partly: officials often at the frame edge; R-IV-02 needs 2 or 3 |
| Coaches / bench | stand, gesture, box position (new-CC-2) | timeout call, challenge, sub, technical | 8-12 timeouts, 30-60 subs, 0-2 challenges | 1 Hz | only when the director cuts to the bench (21 of 177 samples crowd or bench, measured) |
| Ball | pass speed 6-15 m/s (estimate), dribble 3-4 bounces/s, shot arc apex 4-5 m (estimate) | held, dribbled, passed, shot, loose, out | ball state every frame | full frame rate; ±1 frame for release and net | can in 2D; motion blur 1-2 frames at the ring (measured); height needs 3D |

### 3.2 Volume per game for the first two games

Frames are measured; the rest are estimates for planning (R-CS-02, R-CS-05) and must be replaced by measured values after game 1.

| Table | Grain | Rows per game per pass (estimate) | Notes |
|---|---|---|---|
| `frames` | frame | 155,492 (UConn), 161,653 (Louisville) | measured |
| `detections` | box per frame | 1.0-1.6 million | main wide about 54% of frames (95 of 177 samples) × 10-16 boxes |
| `player_positions` | player per frame | 0.85-1.6 million | observed main-wide rows ≈ 0.85 million; 1.6 million if off-screen imputation is per frame (R-DT-07) |
| `ball_states` | frame | 155,000-162,000 | |
| `state_frame` | frame | 155,000-162,000 × 102 columns | denormalised; see K6 |
| `state_second` | second | 5,200-5,400 (video seconds) | |
| `possession_value`, `transition_numbers` | 0.1 s | 24,000 live-play rows; × 3 margins for numbers | |
| events of all kinds | event | 8,000-15,000 (dribbles dominate) | |
| `scoreboard_ocr` | reading | up to 4 fields × frames read | read at 29.97 fps only around changes; 2-5 fps otherwise |

Storage (estimate, zstd Parquet): 0.3-0.8 GB processed per game per version against 1.82-1.97 GB of raw video (measured). Raw dominates; processed versions accumulate, so version retention matters more than row width.

### 3.3 The noise floor: what broadcast tracking can and cannot measure

Speeds and accelerations are derivatives of position. With independent position errors σ, a local polynomial fit over a window of N frames at 29.97 fps gives the following 1-σ noise per axis (computed for this review; correlated homography errors lower the velocity noise but add bias):

| Position error σ | Window 0.5 s (15 frames): speed σ | accel σ | Window 1.0 s (31 frames): speed σ | accel σ |
|---|---|---|---|---|
| 0.10 m | 0.18 m/s | 2.80 m/s² | 0.06 m/s | 0.45 m/s² |
| 0.15 m | 0.27 m/s | 4.20 m/s² | 0.09 m/s | 0.68 m/s² |
| 0.30 m | 0.54 m/s | 8.39 m/s² | 0.18 m/s | 1.35 m/s² |
| 0.50 m (R-PL-13 target) | 0.90 m/s | 13.98 m/s² | 0.30 m/s | 2.26 m/s² |

Consequences:
- At the R-PL-13 target of ≤ 0.5 m, acceleration bands of ±2.0 and ±3.0 m/s² (R-PL-12) are not resolvable at any window short enough to time a first step; the 1 m/s² onset rule of R-CO-02 is below the noise floor even at σ = 0.1 m with a 0.5 s window.
- Speed bands with edges 0.83 m/s apart (5.0 vs 5.83 m/s, R-PL-11) need speed σ ≤ 0.2 m/s, i.e. σ ≤ 0.3 m with 1.0 s windows, which smear sprints shorter than 1 s (R-PL-11 requires ≥ 1.0 s efforts, so it is consistent).
- R-IV-13's frame-to-frame 12 m/s² check would fire on most frames of a raw track; it must run on filtered tracks.
- Literature for broadcast tracking: speed RMSE 0.34-2.38 m/s, distance bias −21.8% to +24.3% (`docs/research/load_thresholds.md`, finding 6).

So every derived kinematic column needs an uncertainty column, and every band or onset report needs a "resolvable" test (new-DT-E1, new-PL-E1).

### 3.4 Timing resolution at 29.97 fps

One frame is 33.37 ms. The measured make frame is fixable to about ±1 frame (the ball crosses the ring plane within 1-2 frames, `made_basket_lag.md`). R-MB-04's ±0.05 s was written for 60 fps (±3 frames); at 29.97 fps it is ±1.5 frames, which forbids even a 2-frame disagreement. Restate in frames (section 4.3).

---

## 4. SYNTHESIZE: how the data-engineering view adjusts the requirements

### 4.1 Schema review: findings on `schema/tables/*.yaml`, `docs/data/*.md`

Counted with a parser over all 104 files (13 use `table:` as the name key, 91 use `name:`). ~3,000 columns. Storage line: 83 tables share `processed/<game_id>/<version>/<table>.parquet`.

**Keys and grain**

| # | Finding | Tables affected | Change |
|---|---|---|---|
| K1 | `pass` is a column but not in the primary key of frame-level CV tables, though blind and anchored rows of the same frame will both exist in one `<version>` folder | `player_positions` (PK video_id, frame_index, player_id), `detections` (video_id, frame_index, det_id), `ball_states` (video_id, frame_index), `official_positions`, `frame_geometry`, `frames` | add `pass` to the PK, or partition by pass and declare it; same for every table whose provenance block has `pass` |
| K2 | 10 Hz and 1 Hz tables keyed on video time without `video_id`: a game with two files (R-FD-09 says one game can have several) collides; video time also includes dead balls and replays | `possession_value` (game_id, ts_ds), `transition_numbers`, `defensive_matchups` (game_id, second_index, defender_id), `scheme_states`, `belief_states`, `position_forecasts`, `audio_seconds` (video_id but no game) | adopt the `state_second` convention: (game_id, pass, time_base, t_index) with `time_base ∈ {video_s, game_clock_s}`; add `video_id` when time_base is video |
| K3 | `run_id` / model version not in PKs of CV outputs; two runs in one version folder overwrite or duplicate | `detections` has `run_id` as a column only; `tracks` has it in the PK | content-addressed partitions (new-EN-E1) make run identity physical; then PKs need not carry it |
| K4 | Event IDs `<game_id>:<kind>:<n>` with n assigned at run time are not stable under re-runs | `events`, `shots`, `fouls`, `passes` ... | PBP rows: `<game_id>:<source>:<source_play_id>` (CBBD `id` is contiguous and chronological, source map line 629); CV rows: hash of (stage output key, kind, video_id, start frame, primary track) (new-EN-E3) |
| K5 | 7 state tables use a global surrogate PK without `game_id` (`free_throw_id`, `restart_id`, `score_event_id`, `timeout_id`, `review_id`, `make_id`, `reading_id`), unlike the other 91 | the 13 `table:`-dialect files | (game_id, pass, id) like the rest |
| K6 | `state_frame` stamps 102 columns on every frame per pass, while each state dimension changes 10-300 times a game | `state_frame`, and R-MD-01 asks every row of every table to carry all global fields | store `state_segments` (valid_from/valid_to) once; `state_frame` and the per-row stamps become views (as-of join). One place to correct, no drift between copies (new-MD-E2) |
| K7 | `video_id` = SHA-256 hex (64 characters) on every frame row; fine with Parquet dictionary encoding, but it is also the key users type | frame tables | keep the hash as identity; add a short `video_key` (int16 per game) for humans and joins |
| K8 | Views with 0 columns (`lines_odds_snapshots`, `prediction_market_prices`) count as tables | 2 | list them as views; the count is 102 tables + 2 views |

**Time**

| # | Finding | Change |
|---|---|---|
| T1 | No table holds the video ↔ game-clock map that R-MD-08 requires; columns cite "R-MD-08 map" 11 times but it lives implicitly in `state_frame` | new `clock_map` table (new-MD-E1) |
| T2 | UTC is missing on in-game rows: `wallclock_utc` exists only in `events`; `video_ts_ms` appears in 21 tables | every event row gets `est_utc` and `est_utc_err_s` from `clock_map` (new-MD-E4); needed for in-game market joins |
| T3 | Scorebug lag (median 1.933 s, range 1.498-2.604 s, measured) is a per-field latency, not a flag window | `scoreboard_ocr` keeps raw frame time; state uses lag-corrected time; per-field lag model (new-SY-E4) |
| T4 | No bitemporal stamp: rows say when the instant happened, not when the system could have known it; leakage rules (`as_of`) are per column, not per row | `known_at_utc` on every row that can be revised (PBP, OCR, reviews) (new-MD-E5) |
| T5 | PBP order within a second is unreliable (ESPN `sourceId` not chronological inside a second; source map line 739) | explicit `order_index` and `order_source` (new-SY-E3) |

**Versioning, idempotency, evolution**

| # | Finding | Change |
|---|---|---|
| V1 | `processed/<game_id>/<version>/`: "version" is undefined (pipeline? stage? schema?). One upstream fix forces a whole-game copy, and nothing says which upstream version a table was built from | per-table, per-stage content-addressed layout with a manifest and a `current.json` pointer (new-EN-E1, new-EN-E4) |
| V2 | Two YAML dialects (13 `table:` + `owner:`; 91 `name:` + `group:`), different PK conventions and provenance placement | one generator, one dialect, CI validation (new-EN-E5) |
| V3 | `schema_version` is an int16 per row, with no rule for what bumps it | semver per table; additive = minor; breaking = major + migration; readers refuse unknown majors (new-EN-E7) |
| V4 | `pass` vocabularies differ: provenance block {blind, anchored, none}; state tables propose `pbp_only` | one enum {blind, anchored, pbp_only, none} |

**Normalisation versus denormalisation**

- Good: events are long (one row per event, linked by IDs, R-EV-12); sources are separate rows (`source` column), never merged; ratings and profiles are long format (`ratings_snapshots`, `profile_snapshots`); markets are one row per outcome (R-MK-14).
- Over-denormalised: `state_frame` (K6); the 10-column provenance block on every per-frame row (`source_ref` as a per-row string is the expensive one: lineage belongs at partition level for frame tables, row level for events, R-DQ-04 tighten).
- Under-normalised: `players_on_floor` as `list[string]` of 10 sorted IDs in a fixed MSU-first order on every frame; store `lineup_stint_id` per team and join.
- MSU-centric global stamp (`score_msu`, `team_fouls_msu`, `team_in_possession ∈ {msu, opponent}`) cannot represent the all-D-I PBP-only pass (R-SY-06, R-PE-08). Store by `team_id` (or home/away) and make MSU-relative columns a view (new-MD-E3).

**Partitioning (proposal)**

```
processed/
  <table>/
    stage=<stage_name>/key=<output_key_12hex>/          # content address (code + config + inputs)
      game_id=<espn_id>/pass=<blind|anchored|pbp_only>/
        part-0000.parquet                               # sorted by (video_id, frame_index) or (period, -game_clock_s, order_index)
        _manifest.json                                  # rows, sha256, schema_version, input keys, run_id
  _current/<table>/game_id=<espn_id>.json               # which key is "current" for each game
```

Row groups of 64-128 MB for frame tables (about one period each); one file per game for event tables. DuckDB over hive partitions is enough for two games and for a season (new-EN-E6). No orchestration server: a DAG file and a runner that skips existing output keys (new-EN-E8).

**What is over-engineered for the first two games**

Build first (43 tables, 3 of them new): `games`, `teams`, `players`, `rosters`, `jersey_history`, `id_crosswalk`, `venues`, `game_officials`, `video_files`, `frames`, `scoreboard_ocr`, `clock_map` (new), `state_transitions` (new), `state_segments` (new; replaces stored `state_frame`), `state_second`, `events`, `substitutions`, `lineup_stints`, `possessions`, `chances`, `score_events`, `shot_clock_resets`, `timeouts`, `restarts`, `free_throws`, `fouls`, `shots`, `rebounds`, `turnovers`, `made_basket_events`, `scoreboard_flags`, `state_corrections`, `detections`, `tracks`, `player_positions`, `ball_states`, `raw_pulls`, `quarantine_rows`, `run_records`, `run_requirement_results`, `review_queue`, `review_labels`, plus the market tables already coded.

Defer until the gates they depend on pass (schemas stay as proposals): `belief_states`, `coach_quiz`, `position_forecasts`, `possession_value`, `value_credits`, `predictions`, `simulation_runs`, `profile_snapshots`, `player_shooting_sector_ring`, `commentary_segments`, `appearance_cards`, `bench_events`, `scheme_states`, `scheme_changes`, `set_instances`, `set_instance_phases`, `play_calls`, `configuration_snapshots`, `movement_primitives`, `actions`, `screens`, `drives`, `dribbles`, `reaction_events`, `defensive_matchups`, `defensive_events`, `frame_geometry`, `post_touches`, `box_outs`, `accel_efforts`, `load_stint_bins`, `transition_numbers`, `transition_roles`, `official_positions`, `whistles`, `audio_seconds`, `identity_confusions`, `hypothesis_results`, `pregame_cards`.

**What is missing**

`clock_map`, `state_transitions`, `state_segments`, `pbp_versions` (one row per PBP pull per game with a content hash and diff counts), `stage_outputs` (the content-address registry), `video_segments` (cut map of a condensed replay: which game-clock ranges each video stretch covers), `frame_stage_mask` (which stages ran on which frame, so "not processed" differs from "nothing found").

### 4.2 Code review: `src/msu_alpha/markets/`

The package is well structured (raw-before-parse, manifest, UTC µs everywhere, naive datetimes refused, counts-only run records, private-root guard on the snapshot store, contracts with quarantine). Findings, most important first:

| # | File:line | Finding | Effect | Fix |
|---|---|---|---|---|
| M1 | `models.py:140-146` | `dedup_key()` uses `game_id`, which is null until matched, and not `source_event_id` | two different unmatched games in one fetch with the same book, market, side and line (e.g. totals, which carry no team_id) get the same key; `parse.py:76-90` then quarantines the second as a C-14 duplicate, and it is never re-matched | add `source_event_id` (and `source`) to the dedup key; R-MK-27 rewrite |
| M2 | `sources/cbbd.py:61-66` | CBBD rows labelled `close_reported` / `open_reported` take `snapshot_time_utc = fetched_at` | every re-pull of a finished season writes another "close" with a new snapshot time; C-14 cannot see the duplicate; a "closing line" query returns one row per pull | for `*_reported` labels, dedup on content (game, source, book, market, label, side, team, line, price) and keep `first_seen_utc`/`last_seen_utc` |
| M3 | `store.py:69-86` | de-duplication is per batch only; files are never overwritten (good) but re-ingesting the same raw creates a second part file with the same rows | not idempotent: reprocessing doubles rows | read through a "latest per key" view, or make the part file name a hash of (raw sha256, parser version) and skip if present (new-MK-E2) |
| M4 | `raw_store.py:67-69` | `RawStore` does not call `ensure_private()` (the snapshot and quarantine stores do) | raw responses can be written under the public repo by mistake | call `ensure_private` in `RawStore.__init__` (new-RG-E1) |
| M5 | `raw_store.py:87-88` | `sha256` is computed after identity redaction, while R-MK-13 says raw is stored as received | the hash cannot prove what the server sent | store `sha256_received` and `sha256_stored`; manifest already lists redacted fields |
| M6 | `store.py:96-104`, `raw_store.py:115` | JSONL appends without fsync/atomic rename; quarantine file named per run_id is appended to | crash leaves a partial line; a re-run appends duplicates | write temp + rename, one file per run (new-EN-E2) |
| M7 | `store.py:88-89` | `read()` reads all partitions with `partitioning=None` | fine now; slow when the store grows (no pruning by source/season) | read with hive partitioning; filter pushdown |
| M8 | `models.py:111`, store schema | `schema_version` is per row (good) but not in Parquet key-value metadata | readers cannot refuse an unknown version before reading rows | write it to file metadata too (R-MK-31 tighten) |

No secret, account, order or trading code was found; the allowlisted HTTP client design (R-MK-12) is not re-reviewed here.

### 4.3 Verdicts on existing requirements

Verdicts: keep = fine as written; tighten = same intent, sharper acceptance; loosen = scope or threshold relaxed (often "after the first games"); rewrite = the text is wrong or untestable for an engineer; drop = remove or merge. IDs not listed are outside this persona's competence and get no verdict.

| ID | Verdict | New text (proposal) | Acceptance criterion | Why (engineer) |
|---|---|---|---|---|
| R-RR-01 | tighten | Run record adds config hash, stage output keys of every input and output, and the DAG node per stage. | Re-running a run record's inputs reproduces the output keys of all deterministic stages (100%); GPU stages within the R-EN-02 tolerance. | Without input keys, "same inputs" cannot be checked. |
| R-RR-02 | keep | | | |
| R-RR-03 | keep | | | |
| R-RR-05 | keep | | | Append-only error catalogue is correct. |
| R-RR-06 | keep | | | |
| R-RR-08 | keep | | | |
| R-RR-09 | keep | | | |
| R-DQ-01 | tighten | Cross-source checks write one row per (game, field, source pair) to a `dq_cross_source` view with tolerance and result: scores and final box exact; jersey numbers exact; lines ≤ 0.5 points (R-MK-22); officials exact name match after crosswalk. | 100% of fields with a second source checked per game; tolerances in config. | Today it is a list; it needs a table and tolerances. |
| R-DQ-02 | tighten | Contracts are generated from `schema/tables/*.yaml` (type, unit, range, nullable, enum, PK uniqueness, FK existence) and run on every write. | 104 of 104 specs produce a contract; CI fails on a spec without type, unit (or "none") and range; 0 writes bypass the checker. | Hand-written contracts drift from specs. |
| R-DQ-03 | keep | | | |
| R-DQ-04 | tighten | Lineage at two levels: partition-level manifest (input output-keys, code and config hashes) for every table; row-level `source_ref` only for event and registry rows, not per-frame rows. | For any row, the manifest chain resolves to raw pulls or the video hash in ≤ 5 hops; per-frame tables carry no per-row lineage string. | Per-row lineage strings on 1.6 million rows per game add cost and no information. |
| R-DQ-05 | keep | | | |
| R-DQ-06 | rewrite | Accounting identities per game: possession points = final score; team minutes = 200 (+25 per OT); FGA = makes + misses; **every chance ends in exactly one terminal event from a fixed list** (made FG, missed FG with defensive rebound, turnover, foul with FTs or throw-in, offensive rebound starting the next chance, held ball, period end). | 0 chances with zero or two terminal events per game; identities hold for 100% of games. | "Rebounds + turnovers close every chance" is false (makes, fouls and period ends close chances). |
| R-DQ-07 | keep | | | |
| R-DQ-08 | loosen | Drift check runs once ≥ 10 games of the same source tier exist; before that, distributions are reported without a PSI verdict. | PSI computed from game 11 on; earlier games report quantiles only. | PSI on a baseline of one or two games is noise. |
| R-DQ-09 | keep | | | |
| R-DQ-10 | keep | | | |
| R-DS-05 | tighten | Crosswalk is bitemporal (valid_from, valid_to, recorded_at) and covers CBBD athlete IDs, which differ from ESPN IDs on plays, subs and lineups. | 100% of PBP athlete IDs of in-scope games resolve to an ESPN athlete ID or a local `x-` ID; 0 many-to-one mappings within a validity period. | Verified: CBBD play athlete IDs are CBBD IDs (source map). |
| R-DS-13 | keep | | | |
| R-FD-02 | tighten | ESPN game ID is the game-level join key; within a game, rows join on (game_id, source, source key) or on (video_id, frame_index); no join on names or times without the crosswalk or `clock_map`. | Lint over transforms: 0 joins on team or player names; every game row has its CBBD game ID or a recorded "none". | Louisville (401856531) has no CBBD game ID in the manifest yet. |
| R-FD-09 | tighten | Video specs live in `video_files` (one game, several files); the registry row lists `video_ids`. | Both first games: hash, fps (30000/1001), resolution, codec, duration, edit type present. | The registry has no hash or fps columns (W3 point 3). |
| R-FD-10 | keep | | | |
| R-MD-01 | rewrite | Every row carries the key stamp (game_id, pass, stage output key, and either (video_id, frame_index) or (period, game_clock_s, order_index)); the state stamp (clocks, score, fouls, control, lineup) is obtained by an as-of join to `state_segments` and is materialised only in views and exports. | For a random 1% sample of rows, joined state equals the materialised view (100%); no stored table except `state_segments` holds a copy of global state fields. | Copies of state in 100 tables drift after every correction. |
| R-MD-02 | keep | | | |
| R-MD-04 | keep | | | |
| R-MD-06 | keep | | | Correct after the 18 Oct correction; the reset table in `invariants.yaml` encodes it. |
| R-MD-08 | rewrite | A `clock_map` table holds piecewise segments per running-clock stretch: video_id, start and end frame, period, game clock at both ends, rate, shot clock at start, UTC estimate with source and error. | Over live main-camera frames with a legible clock: median abs(OCR − map) ≤ 0.1 s, 99th percentile ≤ 0.5 s; game clock non-increasing within a segment (100%); every live frame in exactly one segment. | The map is the backbone of every timing metric and every in-game join; today it has no table. |
| R-MD-09 | keep | | | |
| R-MD-12 | keep | | | |
| R-MD-13 | keep | | | |
| R-MD-17 | keep | | | |
| R-MD-18 | tighten | Event rows carry `est_utc` and `est_utc_err_s` (from `clock_map`), not only game-level UTC. | ≥ 95% of PBP events of games with PBP wall clock carry est_utc with err ≤ 30 s. | Needed for 1-minute market joins (R-MK-16). |
| R-MD-19 | keep | | | |
| R-VI-01 | loosen | 1080p constant frame rate is the floor; 29.97 fps is the expected rate for condensed official replays (60 fps not offered); requirements written in frames state the rate. | Both first games pass at 29.97 fps; every timing tolerance is restated per frame rate. | Measured: no 1080p60 exists for these uploads. |
| R-VI-02 | tighten | Intake report adds edit type (full broadcast, condensed replay, highlights), a cut map of video stretches versus game-clock ranges, and the live-play share in main wide. | Both games: cut map covers 100% of the 2,400 s of game clock; frozen segments in live play listed (Louisville 2.3 s at 2,302.6 s). | Condensed replays change what video time means. |
| R-VI-09 | keep | | | |
| R-VI-12 | keep | | | |
| R-VI-14 | keep | | | |
| R-VI-15 | keep | | | |
| R-VI-16 | keep | | | VP9 decode on NVDEC is supported on L4 (unverified for this Colab image). |
| R-CG-08 | tighten | Positions stored to 1 cm and every position row carries `position_sigma_m` (1-σ). | Calibration points: the stated 68% interval covers 60-76% of hand-measured positions per court zone. | 1 cm storage with 0.3-0.5 m error is false precision unless the error travels with it. |
| R-DT-07 | loosen | Off-screen estimates are stored at 10 Hz (not per frame), with a 95% region. | 10 Hz rows for every missing player during live play. | Per-frame imputation triples the largest table for no extra information. |
| R-DT-08 | rewrite | Velocity, acceleration and heading from smoothed positions with the filter and window named, each with a propagated 1-σ; jerk is not computed. | Filter named on 100% of rows; sigma present; no jerk column. | Conflicts with R-PL-12 (jerk not measurable from video); see 3.3. |
| R-DT-11 | keep | | | |
| R-BL-04 | tighten | Pass start/end, release and catch stored as frame index plus `video_ts_ms`, with ±1 frame (±0.033 s at 29.97 fps) as the stated resolution. | 100% of rows carry frame index; resolution in run record. | |
| R-SY-01 | tighten | Scoreboard read on every frame around value changes and at ≥ 2 fps otherwise; gaps filled from `clock_map` with status (observed, interpolated, unknown). | Game clock known (observed or interpolated) on 100% of live main-camera frames; observed share reported (expected about 80%, measured 79.7% of samples). | "Every second" is the wrong grain; changes need frame timing. |
| R-SY-02 | tighten | Every PBP event mapped to a video time with an interval (start, end) and method; order within a second from CBBD `id`. | Median abs error ≤ 1.0 s and 95th percentile ≤ 3.0 s against 100 hand-labelled events on game 1. | PBP is 1 s resolution; the error must be stated. |
| R-SY-06 | keep | | | |
| R-SY-08 | keep | | | |
| R-SY-10 | keep | | | |
| R-SR-01 | keep | | | |
| R-SR-13 | keep | | | Blind versus anchored is the best CV error estimate available. |
| R-SR-15 | keep | | | |
| R-IV-05 | tighten | Game clock never goes up within a period except as a logged correction event (5-12) with old and new values. | Every upward step has a `state_corrections` row; Louisville 4:06 → 4:07 is one. | Measured in game 2. |
| R-IV-13 | rewrite | Physics checks run on filtered tracks: speed ≤ 10 m/s over ≥ 0.3 s windows; acceleration ≤ 12 m/s² over ≥ 0.5 s windows; breaks are flags, not quarantines, until calibrated. | False-break rate ≤ 1 per 1,000 player-seconds on hand-checked clips. | Frame-to-frame limits fire on noise (3.3). |
| R-SB-03 | tighten | The lag window starts at 4 s (measured 1.50-2.60 s, n = 10) and is re-estimated per game and per field. | ≥ 99% of matched makes fall inside the window; window and lag quantiles in the run record. | 15 s is six times the measured maximum. |
| R-MB-04 | rewrite | Make frame within ±2 frames of the hand label at 29.97 fps (±0.067 s) and ±3 frames at 60 fps; 2 vs 3 agreement with PBP ≥ 99%. | Measured on all makes of game 1. | ±0.05 s at 30 fps is ±1.5 frames; the hand label itself is ±1 frame. |
| R-EN-01 | tighten | One schema dialect generated from one spec; semver per table. | 104 of 104 specs validate in CI. | Two dialects today. |
| R-EN-02 | tighten | Determinism stated per stage: bitwise for CPU transforms; for GPU inference, outputs within a declared tolerance (positions ±0.01 m, scores ±1e-4). | Re-run of game 1: 0 differences in CPU stages; GPU stages within tolerance. | GPU kernels are not bitwise deterministic. |
| R-EN-03 | keep | | | |
| R-EN-04 | keep | | | |
| R-EN-05 | tighten | Chunks are (video_id, keyframe-aligned frame range of about 60 s); outputs written atomically (temp + rename) with a completion marker; a chunk with a marker is never recomputed. | Kill test: 20 random interruptions on game 1 give byte-identical outputs to an uninterrupted run. | Colab disconnects are the norm. |
| R-EN-06 | keep | | | |
| R-EN-07 | rewrite | Processed outputs are Parquet under `processed/<table>/stage=<s>/key=<output_key>/game_id=<id>/pass=<p>/` with a manifest and a per-game `current` pointer; versions side by side. | A change to one stage writes new keys only for that stage and its descendants (checked on a test change). | "version" is undefined today and forces whole-game copies. |
| R-EN-08 | keep | | | |
| R-CS-02 | keep | | | |
| R-CS-04 | tighten | Full frame rate on main-wide live play; other shot types get only shot-type classification and OCR at ≤ 5 fps; replay frames get shot-type only. | Frame-stage mask present for 100% of frames; accuracy loss of any sampling measured before adoption. | About 46% of frames are not main wide (measured sample). |
| R-CS-05 | keep | | | |
| R-CS-09 | tighten | Storage plan uses measured sizes: 1.82-1.97 GB per 1080p 29.97 fps condensed replay (2.81-2.92 Mb/s); processed per version measured on game 1. | Plan updated after game 1 with measured processed GB per game. | Estimates are replaced by measurements. |
| R-MK-03 | tighten | In-game prediction-market prices are joined to game state through `clock_map.est_utc`; a join is made only when the UTC error is ≤ 30 s. | ≥ 90% of in-game 1-minute prices of an MSU game with PBP wall clock joined. | Video time is not UTC in condensed replays. |
| R-MK-13 | tighten | Raw store records `sha256_received` (before any redaction) and `sha256_stored`; the raw root is guarded as private. | Unit test: redacted body → two different hashes, both in the manifest; writing raw under the repo raises. | M4, M5. |
| R-MK-14 | keep | | | |
| R-MK-17 | keep | | | |
| R-MK-21 | keep | | | |
| R-MK-25 | keep | | | |
| R-MK-27 | rewrite | De-duplication key = (source, source_event_id, book, market, phase, snapshot label, side, team/player, line, snapshot time); for `*_reported` labels the snapshot time is replaced by the content (price, line) and first/last seen times are kept. | Two unmatched games with equal totals in one fetch both survive; re-pulling a finished season adds 0 close rows. | M1, M2. |
| R-MK-31 | tighten | `schema_version` also written to Parquet key-value metadata; readers refuse unknown major versions. | Reader test with a future version fails loudly. | M8. |
| R-RG-11 | tighten | Enforced in code: every writer of rows (video, processed, markets raw and parsed) checks a shared private-root guard; a pre-commit hook blocks Parquet, video and row-level CSV under the repo except whitelisted registry files. | Hook test: committing a `.parquet` or a 1 MB CSV under `results/` fails. | Policy without enforcement leaks eventually. |
| R-VA-03 | keep | | | |
| R-VA-06 | keep | | | |
| R-HR-05 | keep | | | |
| R-HR-07 | keep | | | |
| R-PL-05 | keep | | | Coverage correction is exactly right. |
| R-PL-09 | keep | | | Bins as the stored form, bands as views: the right design. |
| R-PL-12 | tighten | Acceleration bands are reported only where the propagated acceleration σ is ≤ 0.5 m/s² (section 3.3); elsewhere the value is "unresolved". | Share of player-time resolvable reported per game. | At σ = 0.3 m and 0.5 s windows, accel σ is 8.4 m/s². |
| R-PL-13 | keep | | | |
| R-CO-02 | rewrite | Defensive reaction onset is detected by change-point on velocity direction and magnitude, with a stated uncertainty (≥ ±1 frame plus filter delay); no acceleration-threshold onset. | Onset within ±0.1 s of hand labels on ≥ 80% of 100 labelled reactions on game 1; uncertainty column on 100% of rows. | 1 m/s² onset is below the noise floor (3.3). |
| R-CO-06 | keep | | | |
| R-TR-22 | keep | | | 10 Hz with 3 margins is cheap; the 0.5 m margin is inside the position error and will flip; the requirement already defers to 1.0 m. |
| R-VL-01 | loosen | Possession value at 10 Hz starts after gates G1-G4 pass on two games; until then PBP-level value per possession only. | Gate record shows G1-G4 pass before the first 10 Hz value row. | No value model can outrun its tracking. |
| R-GU-01 | loosen | Belief state starts after R-VL-01. | Same gating. | |
| R-GU-03 | loosen | Coach quiz deferred to the third processed game. | | Not a data dependency for games 1-2. |

### 4.4 New requirements (persona E)

| ID | Tier | Text | Acceptance criterion (units) | Table / column / vocabulary | Why the engineer needs it |
|---|---|---|---|---|---|
| new-MD-E1 | Shall | Store the video ↔ game clock ↔ shot clock ↔ UTC map as piecewise segments, one per running-clock stretch per video file and pass. | Median abs(OCR − map) ≤ 0.1 s, p99 ≤ 0.5 s on live main frames with a legible clock; 100% of live frames in exactly one segment; game clock non-increasing within a segment. | new table `clock_map` (game_id, pass, video_id, segment_id, start/end frame, start/end video_ts_ms, period, gc_start_s, gc_end_s, rate, sc_start_s, sc_status, est_utc_start, utc_source, utc_err_s, residual_med_s, residual_p99_s) | Every timing metric and every cross-source join runs through it. |
| new-MD-E2 | Shall | Store game state as validity intervals per dimension and pass; per-frame and per-second state are views. | View regenerated from segments equals the stored per-frame values of the current `state_frame` spec on 100% of frames of game 1. | new table `state_segments` (game_id, pass, dimension, value, valid_from_ts_ms, valid_to_ts_ms, valid_from_gc, valid_to_gc, period, source, conf, dq, opened_by_transition_id) | One copy of state; corrections in one place; about 1,000 rows instead of 155,000 × 102 cells. |
| new-MD-E3 | Shall | Store team-relative state by `team_id` (or home/away); MSU-relative columns exist only in views. | A PBP-only non-MSU D-I game runs end to end with 0 nulls in team-relative state. | `global_metadata.yaml` (score_team_a/b by team_id), views `*_msu` | R-SY-06 and R-PE-08 need all D-I games in one vocabulary. |
| new-MD-E4 | Shall | Every event row carries four time stamps: `video_ts_ms` (null for pbp_only), period + `game_clock_s`, `shot_clock_s` with status, `est_utc` with `est_utc_err_s`. | ≥ 99% of video-pass events have all four (UTC may carry a large error); 100% have period and game clock. | all event tables | The four clocks are the join surface between video, PBP and markets. |
| new-MD-E5 | Shall | Rows that can be revised (PBP, OCR, reviews, crosswalk) carry `known_at_utc` (when the value was first available) in addition to the instant they describe. | Leakage test: a feature at in-game instant t or pre-game cutoff C uses only rows with known_at_utc ≤ the matching UTC; 0 violations on games 1-2. | provenance block | Bitemporality is the only general defence against leakage from corrections. |
| new-SY-E1 | Shall | Log every game-state change as one typed row of the state machine in section 1.2 (transition type from `config/state_machine.yaml`), with all four clocks, rule reference, trigger event, and which sources observed it. | 0 untyped transitions; every `state_segments` boundary references one transition; per game the transition count per type is reported. | new table `state_transitions`; new vocabulary `config/state_machine.yaml` (T01-T24 + subtypes) | Typed transitions are what invariants should check and what analysts query ("all T06 resets"). |
| new-SY-E2 | Shall | Every PBP pull of a game is stored as a version with a content hash; a diff (plays added, removed, changed) is computed; downstream tables are rebuilt only when the diff is non-empty. | Re-pull with no change → 0 rebuilt tables; an injected change → only dependent tables rebuilt (test). | new table `pbp_versions` (game_id, source, pull_id, sha256, n_plays, n_added, n_removed, n_changed, known_at_utc) | Sources change past data (R-DQ-05); corrections must propagate without full reprocessing. |
| new-SY-E3 | Shall | Events in the same game-clock second carry an explicit `order_index` and `order_source` (cbbd_id, video, inferred). | No two events share (game_id, pass, period, game_clock_s, order_index). | `events.order_index`, `events.order_source` | ESPN order within a second is unreliable (source map). |
| new-SY-E4 | Shall | Estimate scorebug lag per game and per field (score, game clock start/stop, shot clock reset, fouls, timeouts) and use lag-corrected times for state while keeping raw read times. | ≥ 10 events per field per game; lag median and IQR in the run record; state uses corrected times on 100% of OCR-sourced changes. | `scoreboard_ocr.read_ts_ms` (raw), new `scorebug_lag` view (game_id, field, n, p50_s, p90_s) | The 1.9 s score lag would otherwise shift every score-based window. |
| new-SY-E5 | Shall | A clock or score correction (5-12, 2-9.13, review) produces a correction event with old value, new value and the affected window; only state segments inside the window are rebuilt. | Louisville 4:06 → 4:07 produces exactly one correction and rebuilds only segments after it. | `state_corrections` + `state_transitions` (T18) | Late data must not trigger whole-game reprocessing. |
| new-SY-E6 | Should | Video-to-UTC for condensed replays uses PBP wall clock only where it is monotone over ≥ 3 consecutive plays; elsewhere UTC is interpolated with a stated error. | Non-monotone stretches flagged; error bound reported per segment. | `clock_map.utc_source`, `utc_err_s` | CBBD wall clock is nullable and not monotonic. |
| new-VI-E1 | Shall | Each video file has a cut map: video stretches with the game-clock range they cover and the cut type (commercial, timeout trim, half time trim, replay insert). | Covers 100% of game clock for both first games; stretches of live play never overlap in game clock. | new table `video_segments` | Condensed replays make video time discontinuous. |
| new-VI-E2 | Shall | Store per frame which pipeline stages ran (bitmask), so "not processed" differs from "nothing found". | 100% of frames carry the mask; a detection count of 0 with the detector bit unset is never read as "no players". | `frames.stage_mask` | Frame policy (R-CS-04) creates holes that must be explicit. |
| new-EN-E1 | Shall | Stage outputs are content-addressed: output_key = sha256(stage name, code version, config hash, sorted input keys); a stage whose key exists is skipped. | Second run of the full pipeline on game 1 with unchanged inputs writes 0 new files and takes < 5% of the first run's wall time. | new table `stage_outputs` (output_key, stage, inputs, code_version, config_hash, created_utc, rows, bytes) | Idempotency and cheap reprocessing. |
| new-EN-E2 | Shall | All writers write to a temp path and rename atomically; JSONL and manifest appends are one file per run, never appended across runs. | Kill test (R-EN-05) passes; no partial lines in any JSONL after 20 interruptions. | all writers incl. `markets/store.py`, `markets/raw_store.py` | Crash safety. |
| new-EN-E3 | Shall | IDs are deterministic: PBP events `<game_id>:<source>:<source_play_id>`; CV events hash(stage output key, kind, video_id, start frame, primary track). | Two runs with identical inputs give identical IDs (100%); changing a non-upstream stage leaves IDs unchanged. | all `*_id` columns of event tables | Joins, reviews and labels must survive re-runs. |
| new-EN-E4 | Shall | Physical layout `processed/<table>/stage=<s>/key=<k>/game_id=<id>/pass=<p>/` with `_manifest.json` (rows, sha256, schema_version, input keys) and `_current/<table>/game_id=<id>.json`. | Manifest present for 100% of partitions; `current` pointer resolves for every processed table and game. | storage convention (replaces the `<version>` path of R-EN-07) | Versions side by side without whole-game copies. |
| new-EN-E5 | Shall | All table specs share one dialect generated from one source; a validator checks names, PK, FK targets, units, ranges, licence, as-of and requirement IDs. | 104 of 104 specs pass in CI; a spec citing an unknown requirement ID fails. | `schema/tables/*.yaml`, `tools/specgen/` | Two dialects today. |
| new-EN-E6 | Should | Provide DuckDB views over the lake for the 10 most common queries (possessions per game, chances by start type, player speed bins, shot chart, lineup stints, foul state, transitions by type). | Each query runs in < 5 s over two games on a laptop. | `sql/views/*.sql` | Analysts need access without Spark or a server. |
| new-EN-E7 | Shall | Schema evolution: adding a nullable column is minor; renaming, retyping or changing grain is major and needs a migration script and note; readers refuse unknown majors. | A test reader rejects a major bump; every major bump has a migration file. | `schema_version` as semver; `schema/migrations/` | Safe evolution across 100 tables. |
| new-EN-E8 | Should | The pipeline DAG (stages, inputs, outputs, versions) is declared in one config file and run by a small runner on Colab or the Mac; no orchestration server. | DAG passes a cycle check; the runner executes game 1 end to end from the file. | `config/pipeline.yaml` | Orchestration sized to two games, not to a league. |
| new-DQ-E1 | Shall | Invariant breaks are counted per invariant per 1,000 live-play frames (and per 100 transitions) per game and pass, with alarm thresholds in config. | Rates in every run record; a rate above its threshold blocks the game from training (R-SB-04 style). | `run_requirement_results` (metric = break_rate) | Turns invariants into an observability signal. |
| new-DQ-E2 | Shall | Game 1 (UConn) outputs are frozen as a regression fixture; any later run whose row counts change by > 1% or whose key metrics change beyond tolerance raises a review item. | Fixture exists after the first full run; regression check runs on every stage change. | `results/fixtures/401856571/` (counts and metrics only; rows stay private) | Catches silent regressions in a 30-stage pipeline. |
| new-DQ-E3 | Shall | Event-volume sanity: per game, CV event counts are compared with PBP-implied ranges (e.g. passes per half-court chance 1.5-6.0, dribbles per touch 0-15, screens per chance 0-4; proposals) and out-of-range games are flagged. | Ranges in config; flags in the run record for 100% of processed games. | `dq_reports` | Cheap first check that detectors are not silently dead or exploding. |
| new-DT-E1 | Shall | Every position, speed, acceleration and heading value carries a propagated 1-σ (`*_sigma`), from mapping confidence, detection and the named filter. | Calibrated: 68% intervals cover 60-76% of hand-measured values per court zone; sigma present on 100% of rows. | `player_positions.position_sigma_m`, `speed_sigma_mps`, `accel_sigma_mps2`, `heading_sigma_deg` | Without uncertainty every band and onset looks real. |
| new-PL-E1 | Shall | Kinematic bands, efforts and onsets are reported only where the propagated sigma is ≤ half the band width (speed) or ≤ 0.5 m/s² (acceleration); elsewhere they are "unresolved" and counted. | Resolvable share per player-game in every load report. | `load_stint_bins`, `accel_efforts` (`resolvable` flag) | Section 3.3. |
| new-IV-E1 | Shall | Invariants run on `state_transitions` and `state_segments` (event level); frame-level checks are limited to physics and court bounds. | Full invariant check < 60 s per game per pass on a laptop. | `config/invariants.yaml` (`evaluated_on` field) | Checking 34+16 invariants on 155,000 frames per pass is wasteful; transitions are where rules live. |
| new-FD-E1 | Shall | The games registry gains `cbbd_game_id`, `video_ids`, `scorebug_left_team_id` (team order on the bug), `media_format` (16/12/8/4 or 15/10/5) and `pbp_status`. | Filled for both first games (Louisville CBBD ID resolved or "none"); scorebug order matches W3 (UConn file: MSU left; Louisville file: Louisville left). | `games` / `registry/games.csv` | The team order on the bug flips between files (measured). |
| new-CS-E1 | Shall | Each stage logs throughput (frames/s, GPU-s per 1,000 frames, rows/s) and output size (MB per table per game) into the run record. | Present for every stage of games 1-2; per-game cost model updated from them. | `run_records.stage_metrics` | Reprocessing cost cannot be planned without it. |
| new-CS-E2 | Shall | Before any reprocessing, compute its cost from the DAG (affected stages × games × measured cost) and require sign-off above 2 compute units. | Cost estimate logged for 100% of re-runs; estimate within ±30% of actual. | `run_records.estimated_units`, `actual_units` | Content addressing makes this exact. |
| new-RG-E1 | Shall | One shared private-root guard used by every row writer (video, processed, markets raw and parsed, review clips); a pre-commit hook blocks `.parquet`, video and row-level CSV files in the repo. | Writing under the repo raises in a unit test for every writer; committing a `.parquet` fails the hook. | `src/msu_alpha/privacy.py` (new), `.pre-commit-config.yaml` | M4 shows the guard is missing in one writer already. |
| new-MK-E1 | Shall | Market de-duplication includes `source_event_id`; reported closes/opens are de-duplicated on content with first/last seen times. | The two cases in R-MK-27 rewrite pass as unit tests. | `markets/models.py` dedup_key; `market_snapshots.first_seen_utc`, `last_seen_utc` | M1, M2. |
| new-MK-E2 | Shall | Market snapshots are read through a "latest per key" view, so re-ingesting the same raw files is idempotent. | Ingesting the same raw twice gives identical view row counts. | view `market_snapshots_current` | M3. |
| new-RR-E1 | Should | Every stage writes structured JSON-lines logs (stage, game, chunk, counters, warnings); the run record aggregates them. | Logs present for 100% of stages; a failed chunk is findable from the run record in one lookup. | private `logs/<run_id>/` | Observability on Colab, where consoles vanish. |
| new-VA-E1 | Shall | A timing gold set on game 1: 100 hand-labelled instants (net frames, whistles, throw-in touches, clock starts, releases) used to measure every latency and alignment error in this review. | 100 labels, each with frame index and labeller; all latency metrics in the run record cite it. | `review_labels` (label_kind = timing) | Every time tolerance above needs ground truth. |

Count: 35 new requirements across 14 families.

### 4.5 Verdict counts per family (existing IDs reviewed: 92)

| Family | keep | tighten | loosen | rewrite | drop |
|---|---|---|---|---|---|
| R-RR | 6 | 1 | 0 | 0 | 0 |
| R-DQ | 5 | 3 | 1 | 1 | 0 |
| R-DS | 1 | 1 | 0 | 0 | 0 |
| R-FD | 1 | 2 | 0 | 0 | 0 |
| R-MD | 8 | 1 | 0 | 2 | 0 |
| R-VI | 5 | 1 | 1 | 0 | 0 |
| R-CG | 0 | 1 | 0 | 0 | 0 |
| R-DT | 1 | 0 | 1 | 1 | 0 |
| R-BL | 0 | 1 | 0 | 0 | 0 |
| R-SY | 3 | 2 | 0 | 0 | 0 |
| R-SR | 3 | 0 | 0 | 0 | 0 |
| R-IV | 0 | 1 | 0 | 1 | 0 |
| R-SB | 0 | 1 | 0 | 0 | 0 |
| R-MB | 0 | 0 | 0 | 1 | 0 |
| R-EN | 4 | 3 | 0 | 1 | 0 |
| R-CS | 2 | 2 | 0 | 0 | 0 |
| R-MK | 4 | 3 | 0 | 1 | 0 |
| R-RG | 0 | 1 | 0 | 0 | 0 |
| R-VA | 2 | 0 | 0 | 0 | 0 |
| R-HR | 2 | 0 | 0 | 0 | 0 |
| R-PL | 3 | 1 | 0 | 0 | 0 |
| R-CO | 1 | 0 | 0 | 1 | 0 |
| R-TR | 1 | 0 | 0 | 0 | 0 |
| R-VL | 0 | 0 | 1 | 0 | 0 |
| R-GU | 0 | 0 | 2 | 0 | 0 |
| **Total** | **52** | **25** | **6** | **9** | **0** |

No drops: nothing in the reviewed set is wrong enough to remove; the conflicts (R-DT-08 jerk vs R-PL-12; R-MB-04 at 30 fps) are fixed by rewriting.

### 4.6 The 10 most valuable outputs of the whole project (engineer's view)

1. A replayable, versioned game lake: every processed game rebuilt from raw video, raw pulls and config by one command, with content-addressed outputs.
2. `clock_map`: video, game clock, shot clock and UTC aligned per game, with stated error. It unlocks every timing metric and every cross-source join.
3. `state_transitions` + `state_segments`: the rules' state machine as typed, timestamped data, checked by `config/invariants.yaml`.
4. Possession and chance tables in one vocabulary for every D-I game (PBP-only) and for every video game (blind and anchored), so the engine and the video layer share keys.
5. Player and ball tracks with uncertainty, on a court frame that follows the rulebook geometry.
6. Event tables (shots, fouls, turnovers, rebounds, passes, screens) matched to PBP, with unmatched CV events kept as their own stream.
7. A data-quality layer that runs on every write: contracts from specs, invariants, cross-source and blind-versus-anchored diffs, quarantine.
8. A bitemporal crosswalk and registry (ESPN, CBBD, Torvik, KenPom names, players, officials) that resolves every external ID.
9. A market snapshot store joined to games, and in-game prices joined to game state through UTC.
10. A measured cost and throughput model per game (GPU-s, GB, units), so the season plan is arithmetic, not hope.

### 4.7 The 10 biggest risks

1. **Clock alignment on condensed replays.** Video time is discontinuous; scorebug absent in 16.9% of samples and shot clock legible in 71.8%; PBP is 1 s with an unreliable in-second order and a non-monotone wall clock. If `clock_map` is weak, every timing number is wrong. Mitigation: new-MD-E1, new-VI-E1, new-VA-E1.
2. **Non-idempotent runs.** Run-time ordinal IDs and per-batch de-duplication (already visible in markets M1-M3) produce duplicates and break labels and reviews after re-runs. Mitigation: new-EN-E1, new-EN-E3, new-MK-E1/E2.
3. **Schema sprawl ahead of evidence.** 104 specs, about 3,000 columns and two dialects for two games; maintenance cost grows faster than value and specs drift from code. Mitigation: build 43 tables, defer the rest, one generator (new-EN-E5).
4. **Derivative noise read as signal.** Accelerations, reaction onsets and cut angles from broadcast tracking are below the noise floor at realistic position errors (3.3). Mitigation: new-DT-E1, new-PL-E1, R-CO-02 rewrite.
5. **Key collisions.** `pass` missing from frame PKs; video-time keys without `video_id`. Mitigation: K1, K2.
6. **Licence and privacy leak to the public repo.** One writer lacks the private guard; registry CSVs from ESPN are in the repo (inbox 006 question 5). Mitigation: new-RG-E1, hook.
7. **Late corrections not propagated.** PBP revisions, timing corrections and reviews change the past; without versions and diffs the lake silently goes stale. Mitigation: new-SY-E2, new-SY-E5, new-MD-E5.
8. **MSU-centric stamp breaks the all-D-I engine.** Mitigation: new-MD-E3.
9. **Identity errors propagate everywhere.** Every player-level table inherits identity mistakes; without confidence propagation and the PBP-lineup constraint they cannot be bounded. Mitigation: R-ID-03, R-ID-11, sigma columns.
10. **Reprocessing cost overrun.** Without content addressing, a fix in an early stage re-runs every game end to end. Mitigation: new-EN-E1, new-CS-E1/E2.

### 4.8 The 10 most important requirement and schema changes

1. Add `clock_map` (new-MD-E1; R-MD-08 rewrite).
2. Add `state_transitions` with the typed state machine in `config/state_machine.yaml` (new-SY-E1), and run invariants on it (new-IV-E1).
3. Store state as `state_segments`; make `state_frame` and the global stamp views (new-MD-E2; R-MD-01 rewrite).
4. Content-addressed stage outputs and the partition layout with manifests and `current` pointers (new-EN-E1, new-EN-E4; R-EN-07 rewrite).
5. Deterministic IDs for PBP and CV events (new-EN-E3).
6. Fix keys: `pass` in every frame-level PK; `video_id` or game-clock time base in every 1 Hz and 10 Hz PK; `game_id` in the 7 state-table PKs (K1, K2, K5).
7. Four time stamps plus `known_at_utc` on every event row (new-MD-E4, new-MD-E5).
8. Uncertainty columns on all kinematics and a resolvability gate on bands and onsets (new-DT-E1, new-PL-E1; R-DT-08, R-CO-02, R-IV-13 rewrites).
9. Team-neutral storage with MSU views (new-MD-E3).
10. Markets: de-duplication on `source_event_id` and content for reported lines, idempotent reads, private guard on the raw store (new-MK-E1, new-MK-E2, new-RG-E1; R-MK-27 rewrite, R-MK-13 tighten).

---

## Sources opened (2026-10-18)

Repo: `schema/tables/*.yaml` (all 104, parsed for name, grain, PK, column count, storage; read in full: `state_frame.yaml` header, `events.yaml` header, column lists of `frames`, `player_positions`, `state_frame`; PKs of `possession_value`, `transition_numbers`, `defensive_matchups`), `schema/global_metadata.yaml`, `config/invariants.yaml` (header, constants, shot-clock reset table, free-throw award table, invariant statements and rule refs), `docs/data/dictionary_state.md` (sections 1, 7, 8), `docs/data/dictionary_games.md` (sections 2.1-2.9), `docs/data/source_field_map.md` (wall clock, clock resolution and ordering lines), `results/w3_intake/README.md`, `video_manifest.csv`, `intake_check.csv`, `made_basket_lag.md`, `scorebug_summary.md`, `registry/games.csv` (first rows), `coord/requirements_inbox/006-data-dictionary-and-first-games.md`, `coord/requirements_inbox/007-game-ontology-gaps.md` (proposal list), `docs/research/beliefs_register.md` (B2, C3), `docs/research/load_thresholds.md` (summary findings), `docs/taxonomy/defense_full.md` (sections 0.4, F3), `docs/research/transition_full.md` (headings), `src/msu_alpha/markets/models.py`, `store.py`, `raw_store.py`, `parse.py`, `contracts.py` and `checks.py` (definitions), `timeutil.py`, `run_record.py`, `sources/cbbd.py`, `__init__.py`.

Scratchpad: `brief_panel.md`, `brief_improve.md`, `brief_003.md`, `live_doc2/requirement_ids.md` (all 518 IDs), `rules.txt` (pdftotext of `docs/rules/PRMBB_RulesBook.pdf`, 2026-27: Rules 5-10, 5-11, 5-12, 6-1, 6-2, 6-5, 6-6; table of contents for Rules 5-8, 6-3, 6-4, 7, 8, 9, 11). Other rule numbers are cited as verified in `config/invariants.yaml` (rule_refs with pdf and printed pages).

Computed for this review: derivative-noise table in 3.3 (least-squares polynomial fits, independent errors, 29.97 fps). No web pages, APIs or data providers were called.
