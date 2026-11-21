# Views catalogue: reference

Date: 2026-11-20. Version 0.1.0. Status: proposal under the build freeze (baseline 5 of 8). No product screen is built. Every limit is an engineering proposal; each one says whether it is measured, published, decided or assumed.

This page is generated from `config/views/*.yaml` by `tools/specgen/views/gen_doc.py`. Do not edit it by hand. It is the second page of the [views catalogue](views_catalogue.md): for every view the number rule and the grade rule of each element in full, what each element shows at every grade and level, the interactions and the definitions; then the inventory of every named output and the metrics the views read. Start with the catalogue page; come here to check one element.

## 1. Live panel

### VW-LIVE-01 Live game-state panel

Entry on the catalogue page: [VW-LIVE-01](views_catalogue.md#vw-live-01-live-game-state-panel). What is the state of this game right now, and how sure are we of each part of it?

**Definitions**

- known-at: the panel at instant t shows the values whose known_at_utc is at most t, at the state version that was current at t. Nothing learned after t is shown for t.
- no back-dating: a late feed row, a correction (T18), a replay found afterwards, an identity lock gained later or a stat correction changes the panel only from its own known-at time on (live-state rule LATE_CORRECTION).
- age: stamp_age_s of the value, the seconds since its last observation. It is printed as "&lt;n> s ago" whenever the grade is carried or imputed; a solid value prints no age. The banner prints the oldest age on screen.
- viewer time: known_at_utc is the event time plus the stream delay plus processing. The banner prints the stream delay, so a reader in the arena knows how far behind the panel runs.
- recorded game: the panel reads the as_of_known view of the stored state, also for the anchored pass. It never reads as_of_event.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | **live_state**: grade = the worst grade of the tiles below; age = the oldest age of the tiles below, in whole seconds; "all fresh" when no value is carried or imputed; link = state | contract | Note: As known: the known-at time is that of the newest value on screen. When the stream delay is not measured the banner says "stream delay not measured" and prints video time only; it never prints a wall-clock time it cannot stand behind. On a recorded game the banner prints the instant chosen and the state version current at it. |
| `game_header` | **official**: source = the registry row of the game; as_of = the pre-game snapshot time; link = none_fixed | contract | Note: As known: the header is the frozen pre-game snapshot. A crew change or a roster fix entered after tip shows only from its own known-at time. No age is printed; the snapshot time is. |
| `clock_period` | **live_state**: grade = by rule 1; age = printed when the clock is carried; the guaranteed interval is printed with it; link = state | contract | Note: As known: in a hidden stretch the panel shows the dead-reckoned value that was on screen then. When the bug returns and the estimate was off, the past instants keep the estimate; the miss is logged and only the as_of_event view is re-graded (live-state rule SNAP_AND_LOG). A stop or start cue re-anchors the estimate from the frame the cue was heard, not before. |
| `score` | **live_state**: grade = by rule 1; age = printed when carried; "stale" is added after counter_stale_mark_s; link = state | contract | *run: the primary rule (net at least 8 points in 120 s) and the broadcast "a-b" form are both printed with their names (K05)*<br>Note: As known: a make seen by CV shows as "prov" from the frame the rule fired and turns solid at the frame the bug or the feed agreed. If neither agrees inside make_confirm_window_s the score stays "prov" and a row appears in the flag feed. A make withdrawn later (T18) stays on screen for every instant before the withdrawal was known. A stat correction after the game never appears on the panel. |
| `foul_tracker` | **live_state**: grade = by rule 1; age = printed when carried; a whistle with no feed row yet prints "foul pending &lt;n> s"; link = state | contract | *foul trouble: the cut-off table of the live-state field foul_trouble (K10 as changed, R-SR-20). The rule that fired is printed beside the flag.*<br>Note: As known: a player foul changes at the instant its feed row was known, not at the whistle. Between whistle and row the tile shows "foul pending" and no player count moves. A foul re-assigned to another player later changes the tile only from the known-at time of the correction. |
| `bench_board` | **live_state**: grade = by rule 1; age = printed on every greyed row; stint seconds are game-clock seconds and stop with the clock; link = state | contract | *foul trouble: the same config table as the foul tracker; the 2 / 4 rule is a named second view (R-SR-20). No cut-off is written in this record.*<br>*bench order: players in foul trouble first, then by seconds on the bench. The order is a display choice and changes no value.*<br>Note: As known: a substitution moves a player between blocks at the instant its row or an identity lock was known. A substitution the feed reports late does not move him earlier on a recorded game. The board is built from the feed by name and number (the roster number, not the number CV read); it needs no face image and shows none. It is the long form of the foul tracker and is rendered and tested with it (the foul tracker carries the requirement row of the foul view). |
| `timeouts_left` | **live_state**: grade = by rule 1; age = printed when carried; a break with no owner yet prints "timeout - team pending &lt;n> s"; link = state | contract | Note: As known: a timeout is charged on screen when its feed row or the bug count was known. A called timeout that turned into a media timeout is shown as charged until the row that says otherwise was known. A challenge is shown as used from the review start; whether it is kept shows only when the outcome row was known. |
| `possession_ball` | **live_state**: grade = by rule 1; age = printed when carried; "seconds since control changed" is itself an age and is a dash when control is not known; link = state | contract | Note: As known: a change of control shows at the frame CV saw it. If the scorebook later credits another team, or the anchored pass moves the instant, the panel of that instant is unchanged. The possession number shown is the count as known then; a possession split found later renumbers nothing on a past instant. |
| `lineup_identity` | **live_state**: grade = by rule 1; age = printed when carried; a HOLD prints how long it has lasted; link = state | contract, except<br>**inferred**: Not used for identity. A player is locked or HOLD; there is no provisional label (OD-10).<br>**carried**: The lineup is greyed with the word "unverified" after a dead ball out of view. | Note: As known: a lock gained later is never back-dated; for the earlier instants the player stays on HOLD. An identity split found offline, or a probable label, never appears here (OD-8, OD-10). |
| `mini_court` | **live_state**: grade = by rule 1; age = an off-screen marker prints the seconds since the player was last seen; the ball line prints "ball not seen &lt;n> s"; link = state | contract | Note: As known: positions are those of the causal tracker at that frame. Nothing is smoothed with later frames and no track is filled in backward. An off-screen marker is the forward estimate made then. The court is drawn toward the attacked rim; the half-court side flips only when basket_attacked_home changes. The live court draws no trails, no pass arrows and no acceleration (K03); those belong to the possession explorer. Stricter than the review court on purpose: at D2 and worse the live court is hidden, not estimated. |
| `situation` | **model**: band = a static band around the value; no needle and no animation; model_version = printed under the value; link = state<br>**live_state**: grade = the worst grade and the oldest age of the driving inputs; age = printed when the band is widened; link = state | contract, except<br>**carried**: The value is held and marked "held" with the stoppage kind. It does not tick.<br>**unknown**: No number. The reason is named: clock unknown, score stale, or "no model before P6". | *clutch: at most 300 s left and margin at most 5, with the last-240 s flag beside it (K06)*<br>*garbage time: the win-probability rule first, the CTG-adapted and source flags beside it (K28)*<br>Note: As known: the value at t is the engine started from the as_of_known state at t; it uses no input that became known later. Replaying a recorded game with another model version is a new run and the tile prints that version; the inputs stay as known. When wp_rule of garbage time is unknown the CTG-adapted flag is shown, labelled as the fallback rule. |
| `wp_leverage_strip` | **model**: band = a static band around the line; no needle, no animation, no smoothing; model_version = printed in the legend; link = state<br>**live_state**: grade = the grade of each stretch of the line; age = a held stretch prints how long it has been held; link = state | contract, except<br>**carried**: The line is flat and dashed for the held stretch, marked "held" with the reason.<br>**unknown**: A gap in the line with the reason printed over it. Nothing is interpolated across a gap. | *run shading: the register rule (M-SIT-025, K05), named in the legend*<br>*swing: the change between two consecutive published values (M-SIT-058). The strip marks the swing_marks_max largest so far (R-PR-12).*<br>*clutch and garbage-time stretches are bands on the axis; each names its rule (K06, K28)*<br>*high leverage: the mark of the live-state field leverage, relative to the game so far*<br>Note: As known: every point sits at the game clock of its state and keeps the value that was published then. Nothing is redrawn. A corrected score moves the line only from the known-at time of the correction; the earlier stretch stays as it was shown. The what-was-true series (as_of_event) is a different series and belongs to the review chart (win_probability_chart). The strip never caps or smooths a swing: a change the state held back is a gap and a row in the flag feed (R-PR-11). Refresh target: within live_model_refresh_s of a scoreboard change, measured and reported, not a gate (K23). |
| `tactics` | **live_state**: grade = by rule 1; age = printed when carried; link = state<br>**label**: confidence = printed beside every label; version = in the inspector; link = state | contract | *coverage: the 4 coarse classes always; a fine coverage only at confidence 0.8 or more (K04)*<br>Note: As known: the label shown is the live belief at that second, the best candidate so far. The final label of the possession, known only at its end, is not shown early and does not replace what was shown. Up to three set candidates are in the inspector. |
| `flag_feed` | **live_state**: grade = the grade of the flagged value; age = every row prints how long its flag has been open; a cleared row prints when it closed; link = state<br>**label**: confidence = the confidence that fell under its threshold, printed with the threshold; version = the flag config version, in the inspector; link = state | contract | *triggers: the six of R-HR-01 - identity or jersey number unsure, ball lost or a scramble, player count not 10, scoreboard against play-by-play, set match unsure or no template, coverage or matchup unclear after a switch. Their thresholds live in the flag config of R-HR-01; none is written in this record.*<br>*state flags: a value in quarantine, and a confirm window that closed without its second sensor (live-state rules QUARANTINE and CONFIRM_WINDOW). They are listed with the six.*<br>*one row per cause: ten frames of the same crossing are one row with its age.*<br>Note: As known: a row appears at the frame its flag entered the state and leaves flag_cleared_linger_s after its cause cleared, as known then. A flag found only later - by the anchored pass, by an offline identity split, by a gold check - never appears in the feed of a past instant; it exists in the review queue only. The feed asks nothing of the reader during a game: labelling happens afterward in the review queue. At 375 px it shows flag_feed_rows_max rows. An identity row shows "?" and the candidates, never a face crop. |
| `observability` | **live_state**: grade = by rule 1; age = not printed: these values are re-read every frame; the banner carries the age of the level; link = state | contract | Note: As known: the marks are what the detectors said at that frame. A replay found only after its transitions were written shows as live play for the instants before it was found. |

**Every element at every grade and level (15)**

`as_of_banner`

| At | Shows |
|---|---|
| grade confirmed | The line reads "all solid". |
| grade observed | The line reads "all solid". |
| grade inferred | The line names the tiles that hold a "prov" value. |
| grade carried | The line names the oldest carried value and its age ("clock 12 s ago"). |
| grade imputed | The line counts the off-screen players drawn as estimates. |
| grade unknown | The line counts the tiles that show a dash and gives the commonest reason. |
| grade quarantined | Counted with unknown, as "under review". The value is in the review queue only. |
| D0 full | One quiet line: LIVE, as known &lt;time>, all solid. |
| D1 bug away | Adds "bug away &lt;n> s". No colour change, no layout change: this happens in about a fifth of all seconds. |
| D2 off the main camera | Adds "off main camera &lt;n> s". |
| D3 replay | The word REPLAY, large. The known-at time stops. |
| D4 break | The word BREAK and its age. |
| D5 no video | The words NO VIDEO - feed only. |
| feed stale | Adds "feed quiet &lt;n> s". |

`game_header`

| At | Shows |
|---|---|
| grade confirmed | Solid. |
| grade observed | Solid. |
| grade inferred | Not used for a fixed value. |
| grade carried | Not used for a fixed value. |
| grade imputed | Not used. |
| grade unknown | A dash and the reason ("crew not published", "no previous game for rest"). |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | Shown in full. |
| D1 bug away | No change. Fixed fields are not degraded at any level. |
| D2 off the main camera | No change. |
| D3 replay | No change. |
| D4 break | No change. |
| D5 no video | No change. |
| feed stale | No change. |

`clock_period`

| At | Shows |
|---|---|
| grade confirmed | Solid digits. Tenths under 1:00. |
| grade observed | Solid digits. |
| grade inferred | Solid digits with "prov". The clock is dead-reckoned from the last reading. |
| grade carried | Greyed digits, "&lt;n> s ago" and the interval "between 7:31 and 7:42". |
| grade imputed | Not used for a clock. |
| grade unknown | A dash and "bug away &lt;n> s". The interval stays printed. |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | Solid. |
| D1 bug away | "prov" for clock_prov_max_s, then greyed with age and interval up to clock_greyed_max_s, then a dash. A median stretch (6 s) ends greyed; nine in ten end before the dash. The shot clock follows the game clock. |
| D2 off the main camera | As read while the bug is on screen; else as D1. |
| D3 replay | Frozen at the last live value, greyed. A clock seen inside the replay is never shown. |
| D4 break | Frozen, greyed, with the age of the freeze. |
| D5 no video | A dash and "no video". Period from the feed. |
| feed stale | No change. The clocks do not need the feed. |

`score`

| At | Shows |
|---|---|
| grade confirmed | Solid. Bug and scorebook, or bug and CV, agree. |
| grade observed | Solid. |
| grade inferred | Solid with "prov": CV saw the make; the bug has not shown it yet (about 2 s). |
| grade carried | Greyed with age. "stale" is added after counter_stale_mark_s with nothing watching. |
| grade imputed | Not used for a score. |
| grade unknown | A dash and the reason. |
| grade quarantined | Shown as unknown: a dash and "under review". The contradicted reading is in the review queue. |
| D0 full | Solid. |
| D1 bug away | Solid while CV watches ball and rim; a make seen by CV is added as "prov". Greyed with age when nothing watches. |
| D2 off the main camera | As read while the bug is on screen; else greyed with age. |
| D3 replay | Frozen, greyed. |
| D4 break | Frozen, greyed. Re-read on return before it is solid. |
| D5 no video | From the feed while it is healthy, solid; else greyed with age. |
| feed stale | Bug and CV keep the score solid. The scorer of the last basket is greyed. |

`foul_tracker`

| At | Shows |
|---|---|
| grade confirmed | Solid. Feed row and bug count agree (the bug shows team fouls up to its cap). |
| grade observed | Solid. One source: the feed, or the bug. |
| grade inferred | Team fouls solid with "prov": the feed is quiet and no whistle was heard, so the count is held by rule. Bonus and fouls to give take "prov" with it. |
| grade carried | Greyed with age: a whistle of unknown cause was heard and no feed row says what it was. Bonus is a dash when the carried count is one below a threshold. |
| grade imputed | Not used for a count. |
| grade unknown | A dash and the reason. A foul-trouble flag is a dash while the clock interval lies across a cut-off instant. |
| grade quarantined | Shown as unknown: a dash and "under review" (the bug label and the count disagree). |
| D0 full | Solid. The bug count is checked against the fold up to its cap of 10. |
| D1 bug away | Team fouls from the feed, solid. Without bug and feed, greyed with age. |
| D2 off the main camera | As read; a whistle heard off camera marks team fouls "prov" until the feed row arrives. |
| D3 replay | Frozen, greyed. |
| D4 break | Frozen, greyed. |
| D5 no video | From the feed while it is healthy. |
| feed stale | Player fouls and foul trouble greyed with age (the bug shows no player fouls). Team fouls as read from the bug. |

`bench_board`

| At | Shows |
|---|---|
| grade confirmed | Solid row. The feed lineup and an identity lock agree on who is on the floor. |
| grade observed | Solid row. One source. |
| grade inferred | Only without a feed (blind pass): a count the state inferred, with "prov". With a feed a player count is never inferred. |
| grade carried | Greyed row with age. The block title says "unverified" after a dead ball that was not seen. |
| grade imputed | Not used. |
| grade unknown | A dash in the cell and the reason ("no feed", "slot not known"). A player whose slot is not known sits in a third block, "floor or bench not known". |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | Solid. |
| D1 bug away | No change. Player fouls and substitutions come from the feed, not from the bug. |
| D2 off the main camera | Counts as read. The floor blocks say "unverified" after a dead ball that was not seen. |
| D3 replay | Frozen, greyed. |
| D4 break | Frozen, greyed. On return the floor blocks say "unverified" until substitution rows or identity locks confirm. |
| D5 no video | From the feed while it is healthy. Stint seconds from the feed clock. |
| feed stale | Every foul count greyed with age. A floor row stays solid only where an identity lock confirms the player. |

`timeouts_left`

| At | Shows |
|---|---|
| grade confirmed | Solid. Feed row and bug agree. |
| grade observed | Solid. One source. |
| grade inferred | Solid with "prov": a break has started and the charge is set by rule before the feed row; or a review is in progress and the charge waits for its outcome. |
| grade carried | Greyed with age: a break whose owner is not known while the feed is quiet. |
| grade imputed | Not used for a count. |
| grade unknown | A dash and the reason ("no feed and the bug shows no timeouts"). |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | Solid. |
| D1 bug away | From the feed, solid; else greyed with age. |
| D2 off the main camera | As read. |
| D3 replay | Frozen, greyed. |
| D4 break | Frozen, greyed. A timeout taken into the break is "prov" until the feed row. |
| D5 no video | From the feed while it is healthy. |
| feed stale | Greyed with age where the bug does not show timeouts. |

`possession_ball`

| At | Shows |
|---|---|
| grade confirmed | Solid. CV and a second sensor (a shot-clock reset, a feed row) agree. |
| grade observed | Solid. |
| grade inferred | Solid with "prov": set by a rule before it is seen - possession from a shot-clock reset while off camera, a dead ball from a stopped clock, a stoppage kind before the whistle cause is known. |
| grade carried | Greyed with age for at most status_greyed_max_s, or the longest time the rules allow for the status; then a dash. |
| grade imputed | Not used in this tile. |
| grade unknown | A dash and the reason ("off main camera", "ball not seen 3 s"). The ball handler is a dash when his identity is on HOLD; the candidates are in the inspector. |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | Solid. |
| D1 bug away | No change. These values come from CV, not from the bug. |
| D2 off the main camera | Greyed with age up to the longest time the rules allow for the status, then a dash. The ball handler is a dash at once. |
| D3 replay | Frozen, greyed. |
| D4 break | Greyed, then a dash on return until the first control is seen. Nothing is assumed after a break. |
| D5 no video | Team in possession from the feed, coarse. Everything else a dash and "no video". |
| feed stale | No change. |

`lineup_identity`

| At | Shows |
|---|---|
| grade confirmed | Name and number solid: the feed lineup and five identity locks agree. |
| grade observed | Solid: the feed lineup, or the identity locks, alone. |
| grade inferred | Not used. No provisional label (OD-10). |
| grade carried | Greyed with "unverified" after a dead ball out of view for lineup_unverified_after_s. |
| grade imputed | Not used in this tile. An off-screen player keeps his locked name; only his court marker is hollow. |
| grade unknown | HOLD: "?" with the candidates in order of posterior and the seconds on HOLD. A slot that is not known is a dash. |
| grade quarantined | Shown as unknown: a dash and "under review" (a lineup conflict between the feed and the cues). |
| D0 full | Ten names solid; a player on HOLD shows "?" and his candidates. |
| D1 bug away | No change. |
| D2 off the main camera | Solid in live play. "unverified" after a dead ball that was not seen. |
| D3 replay | Frozen, greyed. |
| D4 break | Greyed and "unverified" on return, until substitution rows or identity locks confirm. |
| D5 no video | Lineups from the feed while it is healthy. Identity is a dash. |
| feed stale | Lineups stay solid where identity locks confirm five players; else greyed with age. |

`mini_court`

| At | Shows |
|---|---|
| grade confirmed | Filled marker with the jersey number. |
| grade observed | Filled marker with the jersey number. A filled ball. |
| grade inferred | Filled marker with a ring and "?": the position is seen, the identity is on HOLD. Ball: a ring on the holder while the ball is hidden in his hands. |
| grade carried | Players and ball are not drawn at this grade (a position is never carried). An official is drawn greyed at the place last seen. |
| grade imputed | Hollow outline with its 95 % region and the seconds since last seen, for at most offscreen_marker_max_s; then removed. No slow fade. |
| grade unknown | No marker. The line "&lt;n> of 10 drawn" says how many are missing. |
| grade quarantined | Shown as unknown: no marker. |
| D0 full | Filled markers. Off-screen players hollow with their region. |
| D1 bug away | No change. |
| D2 off the main camera | Hidden. In its place: "court hidden - off main camera". |
| D3 replay | Hidden. In its place: "court hidden - replay". |
| D4 break | Hidden. In its place: "court hidden - break". |
| D5 no video | Hidden. In its place: "court hidden - no video". |
| feed stale | No change. |

`situation`

| At | Shows |
|---|---|
| grade confirmed | Not used: a derived value is at best observed. |
| grade observed | Value and band, solid. A flag that is yes is named. |
| grade inferred | Value with "prov" and the wider band: a score is provisional or the clock is dead-reckoned. Leverage is the band over both possession cases while the team in possession is not known. |
| grade carried | The last value greyed and marked "held" with the stoppage kind, or "held - replay". It does not tick. |
| grade imputed | Not used. |
| grade unknown | No number, and the reason. A clutch or end-of-period flag that cannot be decided shows "open", never "no". |
| grade quarantined | Shown as unknown: a dash and "held - input flagged" (a change above wp_max_swing_no_event with no score, turnover or foul event). |
| D0 full | Value and band. Before phase P6 every model value is a dash with "no model before P6". |
| D1 bug away | Value with a wider band and the age of the oldest driving input; "prov" while a score is provisional. |
| D2 off the main camera | As D1. Expected points is a dash without positions. |
| D3 replay | The last value, marked "held - replay". |
| D4 break | The last value, marked "held - break". |
| D5 no video | Win probability from the feed state with the wider band; expected points a dash. |
| feed stale | No change while bug and CV keep score and clock. |

`wp_leverage_strip`

| At | Shows |
|---|---|
| grade confirmed | Not used: a derived value is at best observed. |
| grade observed | Solid line with its band. |
| grade inferred | Solid line with the wider band; the stretch is marked "prov". |
| grade carried | Flat dashed line, marked "held" with the stoppage kind, "replay" or "break". |
| grade imputed | Not used. |
| grade unknown | A gap with the reason ("clock unknown", "score stale"). Leverage bars are missing over the gap. |
| grade quarantined | Shown as unknown: a gap marked "held - input flagged". The held-back value is in the review queue only. |
| D0 full | Line, band, leverage bars, run shading, swing marks. Before phase P6 the strip is a card "no live model before P6" and draws no line. |
| D1 bug away | The band widens over the stretch; a gap once the clock interval is wider than wp_clock_interval_max_s. |
| D2 off the main camera | As D1. Leverage is drawn as the band over both possession cases while possession is not known. |
| D3 replay | Flat dashed line marked "held - replay". The strip does not advance. |
| D4 break | Flat dashed line marked "held - break". |
| D5 no video | Line from the feed state with the wider band; a gap when the feed is quiet too. |
| feed stale | No change while bug and CV keep score and clock. The band widens as fouls and timeouts age. |

`tactics`

| At | Shows |
|---|---|
| grade confirmed | Not used: a label is a model output. |
| grade observed | The label with its confidence. A fine coverage only at confidence coverage_fine_min_conf or more. |
| grade inferred | The label with "prov": a matchup pair with a player on HOLD (paired by track, "?" in place of the name), or a set named from its first actions only. |
| grade carried | The last labels greyed, through a replay only. |
| grade imputed | A matchup pair with an off-screen member is outlined with "est"; its probability is taken over the region. |
| grade unknown | A dash and the reason: "unsure" (below the confidence gate), "no set running", "off main camera". |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | Labels with confidence. Below its confidence gate a label is a dash with "unsure". |
| D1 bug away | No change. |
| D2 off the main camera | A dash. Tactics need the main camera. |
| D3 replay | The last labels, greyed. |
| D4 break | A dash. |
| D5 no video | A dash and "no video". |
| feed stale | No change. |

`flag_feed`

| At | Shows |
|---|---|
| grade confirmed | No row for the value. A model label under its threshold may still have one. |
| grade observed | No row for the value. A model label under its threshold may still have one. |
| grade inferred | A row only when a confirm window closed without the second sensor ("score prov - not confirmed"). |
| grade carried | No row inside the carry limit. A row "stale" after counter_stale_mark_s. |
| grade imputed | No row. An off-screen estimate is normal operation. |
| grade unknown | A row when the cause is one of the six triggers; an identity on HOLD gets its row after hold_flag_after_s. A value that is unknown only because of a replay or a break has no row. |
| grade quarantined | A row that names the field and says "under review". The contradicted reading is hidden here and the tile shows a dash (unknown). Only the review queue shows the reading. |
| D0 full | Rows of open flags; "nothing open" when there is none. |
| D1 bug away | No row for the missing bug: it is normal. Scoreboard flags wait until the bug is back. |
| D2 off the main camera | No new identity, ball, count, set or coverage rows: those triggers need the main camera. Open rows stay with their age. |
| D3 replay | Frozen. No flag is raised from replay pictures. |
| D4 break | Frozen. On return a row "re-reading" stays until score, clock and lineups are solid again. |
| D5 no video | Only scoreboard and feed rows. One row "no video" heads the list. |
| feed stale | One row "feed quiet &lt;n> s". Scoreboard-against-play-by-play rows cannot be raised and the list says so. |

`observability`

| At | Shows |
|---|---|
| grade confirmed | Not used. |
| grade observed | A quiet mark per value. |
| grade inferred | The mark with "prov": the shot-type or replay detector is unsure, and the stricter level applies. |
| grade carried | The audio mark greyed through a replay or a break. |
| grade imputed | Tracking quality counts the off-screen players under "est". |
| grade unknown | A dash on the mark: stream lost, or court mapping below its gate. |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | A row of small marks, all quiet. |
| D1 bug away | The bug mark is hollow. |
| D2 off the main camera | The camera mark names the shot type. Coverage and mapping show their low values. |
| D3 replay | The replay mark is on. |
| D4 break | The camera mark says break. |
| D5 no video | Every mark is a dash except the feed. |
| feed stale | No change here; the banner carries the feed line. |

**Interactions (10)**

| Action | At | Target |
|---|---|---|
| `select` | the view | any tile or value opens the inspector: value, grade, source, confidence, age, known-at time |
| `drill_down` | `score` | the last score change at its frame, in the possession explorer → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `drill_down` | `foul_tracker` | the list of fouls of the game; each row links to its frames |
| `drill_down` | `bench_board` | the fouls and stints of one player as known; each row links to its frames |
| `drill_down` | `wp_leverage_strip` | a swing mark or a leverage bar opens its possession; after the game the same click opens the layered chart → [VW-REV-06](#vw-rev-06-layered-win-probability-chart) |
| `drill_down` | `flag_feed` | a row opens its state transition at the effective frame; after the game it opens the item in the review queue → [VW-STU-06](#vw-stu-06-review-queue) |
| `drill_down` | `game_header` | the frozen pre-game card → [VW-CARD-03](#vw-card-03-pre-game-card) |
| `toggle_layer` | `mini_court` | the camera area, the court regions and the officials, each on or off |
| `scrub` | `as_of_banner` | recorded game only: move to any instant; the panel shows what was known then |
| `export` | the view | the panel at one instant as a page with no video (produces `page`) |


## 2. Review and film room

### VW-REV-01 Possession explorer

Entry on the catalogue page: [VW-REV-01](views_catalogue.md#vw-rev-01-possession-explorer). What happened in this possession, and how much did each action change its value?

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `possession_list` | **official**: source = points from the final play-by-play, with its version; as_of = the anchored pass; link = frames<br>**model**: band = printed beside the value at the start; model_version = in the column head; link = frames | contract | Note: A possession that is not usable (too little seen) stays in the list, greyed, with the reason. |
| `possession_header` | **official**: source = the final play-by-play; as_of = the anchored pass; link = frames<br>**model**: band = printed beside each value; model_version = under the tile; link = frames<br>**measurement**: unit = seconds; error = the clock tolerance of the stretch (1 s above 1:00); link = frames | contract |  |
| `video` | no number | contract |  |
| `court` | no number | contract |  |
| `trails_and_arrows` | **model**: band = printed in the inspector; the arrow carries only the sign and size of the change; model_version = in the inspector; link = frames | contract, except<br>**imputed**: A trail through an off-screen stretch is dotted and hollow. No arrow starts or ends at an imputed point.<br>**unknown**: The trail stops. It is not joined across the gap. | *screen: the mark says whether the strict or the loose rule fired* |
| `value_curve` | **model**: band = a fading band round the line; never bare bar ends; model_version = printed in the chart corner; link = frames | contract, except<br>**carried**: Through a replay or a break the line holds its last value and is marked "held".<br>**unknown**: A gap in the line with the reason. The line is not joined across it. | Note: The credits of one action sum to its value change (R-VL-02). A credit reads locked identities only; a probable label never enters it. |
| `action_list` | **model**: band = printed beside each change; model_version = in the table foot; link = frames | contract |  |
| `set_overlay` | **label**: confidence = printed beside the set name; version = the template version beside it; link = frames | contract |  |
| `matchups` | **label**: confidence = the matchup probability of each pair; version = in the inspector; link = frames<br>**measurement**: unit = centimetres for height, metres per second for speed; error = printed beside each gap; link = frames | contract |  |
| `timeline` | no number | contract |  |
| `filter_bar` | no number | n/a (control) | *clutch (K06)*<br>*garbage time (K28)*<br>*run (K05)*<br>*transition class (the repo rule; other definitions are named when chosen)* |
| `clip_export` | no number | n/a (control) |  |
| `inspector` | no number | n/a (control) |  |

**Every element at every grade and level (1)**

`court`

| At | Shows |
|---|---|
| grade observed | Filled marker with the jersey number. |
| grade imputed | Hollow marker with its 95 % region, for at most offscreen_marker_max_s; then the marker is removed. |
| grade unknown | No marker. The count "8 of 10 shown" is printed in the corner. |

**Interactions (11)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | narrows the possession list |
| `select` | `possession_list` | opens the possession in the header, the video, the court and the curve |
| `scrub` | `timeline` | video, court, overlays and the playhead of the value curve move together |
| `select` | the view | any marker, arrow, mark, point of the curve or table cell opens the inspector |
| `brush` | `value_curve` | a time range of the possession; the selection is a query |
| `toggle_layer` | `trails_and_arrows` | each overlay on or off |
| `toggle_layer` | `set_overlay` | the template path on or off |
| `inspect_query` | `value_curve` | the rows and the query behind the curve |
| `drill_down` | `action_list` | the action in the Studio at its frame → [VW-STU-01](#vw-stu-01-studio-game-canvas) |
| `export` | `clip_export` | a clip reference of the possession or the action (produces `clip_reference`) |
| `export` | `court` | a top-down drawing of one moment (produces `top_down_render`) |


### VW-REV-02 Matchup board

Entry on the catalogue page: [VW-REV-02](views_catalogue.md#vw-rev-02-matchup-board). Who guarded whom in this game, for how long, and what did each pairing give up?

**Definitions**

- matchup: the assignment of defense:matchup, one defender per attacker per second, with its probability. A second below the gate of that rule is counted as "unassigned". It is never given to the likeliest defender.
- switch: the rule defense:switch. An exchange of three or more defenders is one defense:multi_switch.
- observed, not predicted: this board shows who did guard whom. The forecast made before the game is the mismatch map of the pre-game card.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `filter_bar` | no number | n/a (control) | *clutch (K06)*<br>*garbage time (K28)* |
| `pair_grid` | **measurement**: unit = seconds; error = the seconds below the assignment gate, printed as "unassigned" beside every row total; link = frames<br>**label**: confidence = the mean assignment probability of the cell; version = the grammar version of defense:matchup, in the grid foot; link = frames | contract, except<br>**imputed**: A second in which the defender or the attacker is off the main camera is not matched. It is counted in the row "not seen".<br>**unknown**: A pair that shared no observed floor time shows a dash. It never shows 0 s. |  |
| `pair_outcomes` | **estimate**: n = matched possessions, and the effective sample size after shrinkage; interval = the posterior interval printed after the value; level = 0.95; link = rows; min_n = registry<br>**official**: source = made shots, fouls and turnovers of the final play-by-play; as_of = the anchored pass; link = frames<br>**model**: band = printed beside each credited value; model_version = in the table foot; link = frames | contract | Note: R-VL-07: shown only above the minimum count of R-VA-05. One game rarely reaches it; the season scope does. The prior and the shrinkage factor of every estimate are in the inspector (R-VL-12). |
| `assignment_timeline` | no number | contract, except<br>**imputed**: A stretch with either player off the main camera is drawn as a hatched gap in the row. |  |
| `switch_log` | **label**: confidence = the probability of the switch and of the coverage class, beside each; version = the grammar version in the table foot; link = frames<br>**measurement**: unit = centimetres for height, metres per second for speed, seconds for duration; error = a listed height carries none and says "listed"; a speed prints its error; link = frames<br>**official**: source = points of the final play-by-play; as_of = the anchored pass; link = frames | contract | *coverage: the 4 coarse classes always; the fine class only at confidence 0.8 or more, else the coarse class is shown (K04)* |
| `video` | no number | contract |  |
| `court` | no number | contract |  |
| `clip_export` | no number | n/a (control) |  |
| `inspector` | no number | n/a (control) |  |

**Every element at every grade and level (1)**

`court`

| At | Shows |
|---|---|
| grade imputed | Hollow marker with its 95 % region. No assignment line starts or ends at it. |
| grade unknown | No marker. The count "8 of 10 shown" is printed in the corner. |

**Interactions (9)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | narrows the seconds counted, by team, period, lineup and state |
| `select` | `pair_grid` | a pair; the timeline, the outcome row and the switch log narrow to it |
| `drill_down` | `pair_grid` | the matched possessions of the pair as a list → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `select` | `switch_log` | the video and the court jump to the switch |
| `scrub` | `assignment_timeline` | video and court move together |
| `drill_down` | `pair_outcomes` | the rows behind an estimate; each row links to its frames |
| `inspect_query` | `pair_outcomes` | the rows and the query with metric ids |
| `export` | `clip_export` | a clip reference of the selected stretch (produces `clip_reference`) |
| `export` | `court` | a top-down drawing of one moment (produces `top_down_render`) |


### VW-REV-03 Lineup board

Entry on the catalogue page: [VW-REV-03](views_catalogue.md#vw-rev-03-lineup-board). Which five-player units played, for how long, and how did each do, given how few possessions each had?

**Definitions**

- lineup board (decided here, open question OQ-VW-1): lineup plus-minus with n, the stints and the composition of each unit. Who guarded whom is the matchup board.
- scope: one game or the season to date. In the game scope almost no unit reaches the minimum n, so the rating cell reads "too few" and the counts are shown; the season scope shows the rating.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `filter_bar` | no number | n/a (control) | *garbage time (K28): off by default; when a flag is on, its name is printed in the table head*<br>*clutch (K06)* |
| `lineup_plus_minus` | **official**: source = points and substitutions of the final play-by-play, with its version; as_of = the anchored pass, or pbp_only where the game has no video; link = rows<br>**estimate**: n = offensive and defensive possessions, each in its own column; interval = printed after the net rating, and drawn as a fading band in the bar; level = 0.95; link = rows; min_n = default | contract, except<br>**unknown**: A stint whose five players do not add up (lineup_stints.player_count_error) is listed as "lineup unsure". Its seconds are counted. It enters no rating. |  |
| `stint_timeline` | no number | contract |  |
| `composition` | **official**: source = listed heights, positions and class years of the roster snapshot; as_of = the date of the roster snapshot; link = none_fixed<br>**descriptive**: n = the five players of the unit; descriptive_mark = the word "descriptive" in the column head of every as-of count; link = rows | contract |  |
| `combinations` | **estimate**: n = possessions with the group on the floor; interval = printed after each rating; level = 0.95; link = rows; min_n = default<br>**model**: band = printed beside each adjusted rating; model_version = in the column head; link = rows | contract |  |
| `starters_bench` | **official**: source = the official box of the game; as_of = the pull time of the box; link = rows<br>**descriptive**: n = the games of the scope; descriptive_mark = the word "descriptive" under the tile; link = rows | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (7)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | narrows the stints counted; the count of possessions left is printed |
| `select` | `lineup_plus_minus` | a unit; the timeline marks its stints and the composition table opens |
| `drill_down` | `lineup_plus_minus` | the possessions of the unit as a list → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `brush` | `stint_timeline` | a stretch of the game; the tables count only that stretch |
| `drill_down` | `combinations` | the stints behind a group; each stint links to its possessions |
| `inspect_query` | `lineup_plus_minus` | the rows and the query with metric ids |
| `export` | `lineup_plus_minus` | the table of units, aggregates only (produces `aggregate_table`) |


### VW-REV-04 Heat maps

Entry on the catalogue page: [VW-REV-04](views_catalogue.md#vw-rev-04-heat-maps). Where on the court does this player, lineup or set spend its time, touch the ball, shoot and gain value?

**Definitions**

- subject and scope: one player, one lineup, one set or one team; one game or the season to date. Both are printed in the title of every map.
- cell: one cell of the fine grid, in the named-spots frame, both ends of the floor folded onto the attacked rim.
- scales: the sequential scale for seconds and counts; the diverging scale for value, with zero at the mid stop. A cell that was never observed takes the no-data style. No data is not zero.
- what is binned: only positions whose error is at most position_sigma_max_m of the display contract (R-CG-08). The legend prints the share of floor seconds binned.
- court partition: the legend names it (fine grid, court region or named spot).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `filter_bar` | no number | n/a (control) | *garbage time (K28)*<br>*transition class (the repo rule; other definitions are named when chosen)* |
| `layer_picker` | no number | n/a (control) |  |
| `shot_density` | **official**: source = shot rows of the final play-by-play; the location source of the shots is named in the legend; as_of = the anchored pass or pbp_only; link = frames<br>**measurement**: unit = metres; error = the location error of the source, printed in the legend (play-by-play coordinates against video where both exist); link = frames | contract, except<br>**unknown**: A shot with no location is in no cell. The legend counts such shots. |  |
| `occupancy` | **measurement**: unit = seconds per cell; error = only positions within the error limit are binned; the share of floor seconds binned is printed in the legend; link = frames | contract, except<br>**inferred**: Not binned.<br>**carried**: Not binned.<br>**imputed**: Never binned. Imputed seconds are counted in the legend as "not seen".<br>**unknown**: Not binned. A cell with no observed second takes the no-data style. |  |
| `touch_map` | **label**: confidence = the confidence of the touch and drive rows, as a range in the legend; version = the grammar version in the legend; link = frames<br>**descriptive**: n = the touches and drives of the subject in the scope; descriptive_mark = the word "descriptive" in the legend; link = rows | contract, except<br>**imputed**: A touch whose catch point is imputed is not drawn. It is counted in the legend. |  |
| `value_map` | **model**: band = a cell whose band crosses zero is drawn in the mid stop; model_version = in the legend; link = rows<br>**estimate**: n = touches in the cell; interval = printed in the cell read-out; level = 0.95; link = rows; min_n = default | contract |  |
| `zone_table` | **official**: source = made and attempted shots of the final play-by-play; as_of = the anchored pass or pbp_only; link = frames<br>**estimate**: n = attempts or touches in the zone; interval = printed after each rate; level = 0.8; link = rows; min_n = registry<br>**measurement**: unit = seconds; error = the share of floor seconds binned; link = frames | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (7)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | chooses the subject and the scope; the count of seconds, touches and shots left is printed |
| `toggle_layer` | `layer_picker` | each map on or off |
| `lasso` | `shot_density` | a court area; the selection is a query and the zone table counts only it |
| `select` | the view | a cell or a zone opens the inspector with its rows |
| `drill_down` | `zone_table` | the shots, touches or seconds of the zone as a list with clip links → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `inspect_query` | `zone_table` | the rows and the query with metric ids |
| `export` | `shot_density` | the drawn map of the subject, with its legend (produces `top_down_render`) |


### VW-REV-05 Passing network

Entry on the catalogue page: [VW-REV-05](views_catalogue.md#vw-rev-05-passing-network). Who passes to whom on this team, how often, and how much value do those passes carry?

**Definitions**

- edge: an official assist (play-by-play layer) or a completed pass (tracking layer). The legend says which layer is drawn. The two are never added.
- drawing: a player is a node with his number as a direct label; edge width is the count; edge colour is value on the diverging scale. Team colour is not used inside one team.
- centrality numbers describe the graph of this scope. They carry the word "descriptive".

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `filter_bar` | no number | n/a (control) | *garbage time (K28)*<br>*transition class (the repo rule)* |
| `network` | **official**: source = official assists of the final play-by-play; as_of = the anchored pass or pbp_only; link = frames<br>**label**: confidence = the confidence of the pass rows, as a range in the legend; version = the grammar version in the legend; link = frames<br>**model**: band = in the pair table; an edge carries only the sign and size of the value; model_version = in the legend; link = rows<br>**descriptive**: n = the edges and passes of the scope; descriptive_mark = the word "descriptive" beside every centrality number; link = rows | contract, except<br>**imputed**: A pass with either end off the main camera is not an edge of the tracking layer. | Note: The official-assist layer is drawn from P0p. The tracked-pass layer needs P3 and the value layer P5. |
| `pair_table` | **official**: source = official assists of the final play-by-play; as_of = the anchored pass or pbp_only; link = frames<br>**estimate**: n = passes of the pair; interval = printed after each rate; level = 0.95; link = rows; min_n = default<br>**model**: band = printed beside the value per pass; model_version = in the table foot; link = frames | contract |  |
| `player_table` | **official**: source = the official box of the game; as_of = the pull time of the box; link = rows<br>**estimate**: n = possessions on the floor, or passes; interval = printed after each rate; level = 0.95; link = rows; min_n = default<br>**descriptive**: n = the passes of the scope; descriptive_mark = the word "descriptive" in the head of the centrality columns; link = rows | contract |  |
| `court_arrows` | no number | contract, except<br>**imputed**: No arrow starts or ends at an imputed point. |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (6)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | narrows the passes counted; the count left is printed |
| `toggle_layer` | `network` | official assists, tracked passes or pass value |
| `select` | `network` | a player or an edge; both tables and the court arrows narrow to it |
| `drill_down` | `pair_table` | the passes of the pair as a list with clip links → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `inspect_query` | `pair_table` | the rows and the query with metric ids |
| `export` | `network` | the page of the network with its tables (produces `page`) |


### VW-REV-06 Layered win-probability chart

Entry on the catalogue page: [VW-REV-06](views_catalogue.md#vw-rev-06-layered-win-probability-chart). How did the chance to win move through this game, at the level of the game, the half and the five-minute window, and which plays moved it most?

**Definitions**

- layers: game, half and five-minute window, all from one simulation, so the windows add up to the halves and the halves to the game (R-PR-01).
- two as-of rules on one view: the curve is the offline model on the recorded game (as of event). The forecast of a half or a window is the one frozen before that span began (as known). Each element says which.
- run shading: the register rule M-SIT-025 is the shade; the broadcast a-b form M-SIT-024 is the label on it; the legend names both (K05).
- garbage time: the three flags of K28 can each be drawn as a shade, each named. None is on by default.
- no market price is on this view. Market comparisons are on the edge report, which only the owner sees (R-MK-24).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `tree` | no number | n/a (control) |  |
| `wp_curve` | **model**: band = a fading band round the line; never bare bar ends; model_version = printed in the chart corner; link = frames<br>**official**: source = score events of the final play-by-play; as_of = the anchored pass or pbp_only; link = frames | contract, except<br>**carried**: Through a replay, a review or a break the line holds its value and is marked "held".<br>**unknown**: A gap with the reason where the model had no input. The line is not joined across it. |  |
| `half_and_windows` | **model**: band = the interval of the forecast drawn as a fading band on the bar; model_version = model family, level and simulation id under the bars; link = rows<br>**official**: source = the realised margin from the final play-by-play; as_of = the anchored pass or pbp_only; link = rows | contract, except<br>**unknown**: A span with no forecast frozen before it began shows a dash and "no forecast before this span". A forecast made later is never drawn in its place. |  |
| `leverage_strip` | **model**: band = printed in the inspector for the selected possession; model_version = in the chart corner; link = frames | contract |  |
| `swing_plays` | **model**: band = printed beside each change; model_version = in the table foot; link = frames<br>**official**: source = clock and score of the final play-by-play; as_of = the anchored pass or pbp_only; link = frames | contract |  |
| `game_flow` | **official**: source = the score sequence of the final play-by-play; as_of = the anchored pass or pbp_only; link = rows<br>**model**: band = printed beside the mean win probability; model_version = under the tile; link = rows | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (8)**

| Action | At | Target |
|---|---|---|
| `filter` | `tree` | a half, a window or a possession; the curve zooms to it and the swing plays and tiles count only it |
| `select` | `wp_curve` | a point; the inspector shows value, band, model version and the play under it |
| `brush` | `wp_curve` | a stretch of the game; the selection is a query |
| `toggle_layer` | `wp_curve` | band, run shading, timeouts and each garbage-time flag |
| `drill_down` | `half_and_windows` | the possessions of the half or window → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `drill_down` | `swing_plays` | the play in its possession with video → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `inspect_query` | `wp_curve` | the rows and the query with metric ids |
| `export` | `wp_curve` | the page of the chart with its swing plays (produces `page`) |


### VW-REV-07 Shot chart by sector and ring

Entry on the catalogue page: [VW-REV-07](views_catalogue.md#vw-rev-07-shot-chart-by-sector-and-ring). From which sectors and rings does this player or team shoot, how well, and what were those shots worth?

**Definitions**

- partition: 15-degree sectors by 0.5 m rings from the attacked rim (R-CG-05). It is named in the legend. The court-region partition and the provider crosswalk labels can be chosen instead and are then named (R-CG-17).
- a cell: attempts as the size of the mark; shrunk make rate as colour on the diverging scale round the D-I rate of that cell; makes and attempts as text.
- interval: 80 % on a shrunk make rate (R-PC-23). The level is printed.
- heaves are left out by default (M-SQ-007) and counted in a line under the chart.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `filter_bar` | no number | n/a (control) | *transition class (the repo rule; other definitions are named when chosen)*<br>*clutch (K06)*<br>*garbage time (K28)* |
| `chart` | **official**: source = made and attempted shots of the final play-by-play, with the location source; as_of = the anchored pass or pbp_only; link = frames<br>**estimate**: n = attempts in the cell; interval = printed in the cell read-out with its level; level = 0.8; link = rows; min_n = registry | contract, except<br>**unknown**: A shot with no location is in no cell. It is counted in the line "location unknown" under the chart. |  |
| `quality_layer` | **model**: band = printed in the cell read-out; model_version = in the legend, with the layer it used (location only, or contest-aware); link = rows<br>**estimate**: n = attempts in the cell; interval = printed in the cell read-out; level = 0.95; link = rows; min_n = default | contract | Note: The location-only layer is drawn from P0p. The contest-aware layer needs P5 and is greyed until then. |
| `zone_table` | **official**: source = made and attempted shots of the final play-by-play; as_of = the anchored pass or pbp_only; link = frames<br>**estimate**: n = attempts in the region; interval = printed after each rate with its level; level = 0.8; link = rows; min_n = registry | contract |  |
| `shot_list` | **official**: source = the shot rows of the final play-by-play; as_of = the anchored pass or pbp_only; link = frames<br>**measurement**: unit = metres; error = the location error of the source of the shot; link = frames<br>**model**: band = printed beside the expected points; model_version = in the table foot; link = frames | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (7)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | chooses the subject and narrows the shots; the count left is printed |
| `select` | `chart` | a cell; the shot list narrows to it and the inspector opens |
| `lasso` | `chart` | a court area; the selection is a query |
| `toggle_layer` | `quality_layer` | make rate, expected points or shot-making residual as the colour |
| `drill_down` | `shot_list` | the shot in its possession with video → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `inspect_query` | `zone_table` | the rows and the query with metric ids |
| `export` | `chart` | the drawn chart with its legend (produces `top_down_render`) |


### VW-REV-08 Physical load

Entry on the catalogue page: [VW-REV-08](views_catalogue.md#vw-rev-08-physical-load). How far and how fast did each player move in this game, and how much of his floor time did we actually see?

**Definitions**

- movement only: the footer of the view says "movement only: no health or injury inference". No number here is a statement about fitness, fatigue as a medical state, or injury (R-PC-15, display contract rule 7).
- bands: the primary speed bands of R-PL-11 are a view on the stored 0.1 m/s bins of R-PL-09. Another band scheme can be chosen and is then named.
- coverage first: every number prints the share of the floor time of the player that was observed. A stint under the coverage key of R-PL-05 is left out of every sum and listed (R-PL-14).
- acceleration: counts by band are shown only where the K03 gate passes. Elsewhere the cell says "unresolved" and counts the efforts left out (R-PL-18).
- one game: a change of high-speed running below the limit of R-PL-17 between two games is not coloured and not called a change.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `filter_bar` | no number | n/a (control) | *denominator: minutes played is the headline; the other two are named when chosen (R-PL-15)* |
| `coverage_table` | **official**: source = minutes of the official box; as_of = the pull time of the box; link = rows<br>**measurement**: unit = seconds and percent of floor time; error = one second per stint edge; the stints left out are listed with their observed share; link = frames | contract |  |
| `distance_bands` | **measurement**: unit = metres, seconds, and metres per minute played; error = the propagated error of each band; a band whose error is more than half its width shows "unresolved"; link = frames | contract, except<br>**inferred**: Not summed.<br>**carried**: Not summed.<br>**imputed**: Never summed. Imputed seconds are the hatched segment "not seen".<br>**unknown**: Not summed. A player with no observed second shows a dash and "not seen", never 0 m. |  |
| `efforts` | **measurement**: unit = metres per second, metres per second squared, seconds, counts per minute played; error = printed beside each speed; a count prints how many efforts were left out as unresolved; link = frames | contract | Note: The relative-speed column is provisional until the player has the games R-PL-16 asks for; until then it carries "prov" and the count of games used. |
| `decline` | **descriptive**: n = the stints and minutes of this game; descriptive_mark = the word "descriptive" in the chart title in the game scope; link = rows<br>**estimate**: n = games and stints in the season scope; interval = a fading band round the line; level = 0.95; link = rows; min_n = default | contract |  |
| `footer` | no number | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (5)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | team, player, period, band scheme and denominator; the observed share of the selection is printed |
| `select` | `distance_bands` | a player; the effort table and the decline chart narrow to him |
| `drill_down` | `efforts` | the effort at its start frame, with video and court → [VW-STU-01](#vw-stu-01-studio-game-canvas) |
| `select` | the view | any number opens the inspector |
| `inspect_query` | `distance_bands` | the bins and the query with metric ids |


### VW-REV-09 Telestrator freeze-frame

Entry on the catalogue page: [VW-REV-09](views_catalogue.md#vw-rev-09-telestrator-freeze-frame). What did the floor look like at this one moment, and where was everyone about to go?

**Definitions**

- a drawing, never a frame: the output is a top-down diagram on our own court. It holds no broadcast pixel, so it may pass the rights gate (R-RG-02).
- arrows show what happened next, not a forecast: the movement of each player and of the ball over the next arrow_horizon_s, read from the stored tracks.
- labels come from the broadcast vocabulary layer only (R-MD-31). A label below its confidence gate is not drawn.
- export: locked identities only. A player on HOLD, or with only a probable label, is drawn as "?" with his team mark.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `moment_picker` | no number | n/a (control) |  |
| `diagram` | no number | contract, except<br>**imputed**: Hollow marker with its 95 % region. No arrow starts or ends at an imputed point.<br>**unknown**: No marker. The drawing prints "9 of 10 shown", and keeps that line when exported. |  |
| `labels` | no number | contract, except<br>**inferred**: Drawn with "prov".<br>**unknown**: Not drawn. No label is guessed. | *coverage: the coarse class always; the fine class only at confidence 0.8 or more (K04)* |
| `export_drawing` | no number | n/a (control) |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (7)**

| Action | At | Target |
|---|---|---|
| `select` | `moment_picker` | a possession and a frame |
| `step` | the view | one frame or one second forward or back; the drawing is redrawn |
| `select` | `diagram` | a player, an arrow or the ball opens the inspector |
| `toggle_layer` | `labels` | set name, coverage and spot names, each on or off |
| `drill_down` | `diagram` | the same frame with video beside it → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `export` | `export_drawing` | the drawing of the moment (produces `top_down_render`) |
| `export` | `export_drawing` | the moment as a clip reference (produces `clip_reference`) |


## 3. Analyst Studio and review screens

### VW-STU-01 Studio game canvas

Entry on the catalogue page: [VW-STU-01](views_catalogue.md#vw-stu-01-studio-game-canvas). What does the system hold about this moment of the game, where did each value come from, and can I trust it?

**Definitions**

- editable: nothing on the canvas itself. Four kinds of edit start here and open the draft view: a label (identity, set, coverage, event), a boundary of a segment, a registered parameter, the model version of a stage (R-AS-03).
- an edit creates: a draft state version with a diff, shown in draft_diff_promote. The canvas keeps showing the current version until the owner promotes; a switch shows the draft beside it, marked DRAFT.
- never editable: video, detections and tracks as stored, the official play-by-play and box score, a stored model output, a run record, a locked identity in place, any hash. A layer toggle, a filter and a saved selection change the screen, not the data.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `video` | no number | contract |  |
| `court` | no number | contract |  |
| `state_panel` | **live_state**: grade = by rule 1; age = as on the live panel; link = state | contract | Note: The embedded panel keeps the live identity rule: locked or HOLD. What was true at the instant, and how late it became known, is shown in the inspector beside each value. |
| `timeline` | **descriptive**: n = the seconds of the game with audio; descriptive_mark = the loudness curve is marked descriptive - for hypothesis use only; link = frames | contract |  |
| `layers` | **measurement**: unit = metres, square metres; error = from the position error of the players involved, printed in the inspector; link = frames<br>**model**: band = in the inspector; model_version = in the inspector; link = frames | contract, except<br>**imputed**: A box or id of an off-screen player is not drawn on video. On the court it is the hollow marker with its region.<br>**unknown**: Nothing is drawn. The layer list says how many objects the layer could not draw. | Note: A probable identity label may appear on the ids layer, with the word "probable" on the mark (OD-8). The value heat map uses the sequential scale; a cell with too few cases takes the no-data style. |
| `layer_list` | no number | n/a (control) |  |
| `inspector` | no number | n/a (control) | Note: Selectable objects (R-AS-02): detection box, track, player, ball, score, clock, state segment, transition, event, set, coverage, stat value, model output. |
| `selection_query` | no number | n/a (control) |  |
| `filter_bar` | no number | n/a (control) |  |
| `tree_navigator` | no number | n/a (control) |  |
| `command_palette` | no number | n/a (control) |  |
| `clip_export` | no number | n/a (control) |  |

**Interactions (18)**

| Action | At | Target |
|---|---|---|
| `scrub` | `timeline` | video, court, state panel and overlays move to the same game-clock instant through the clock map |
| `step` | `video` | one frame, one second or one possession |
| `select` | the view | any on-screen object opens the inspector with value, source, confidence, version and lineage |
| `add_select` | the view | adds an object to the selection |
| `clear` | the view | clears the selection |
| `brush` | `timeline` | a time range; the Studio writes its SQL with metric ids |
| `lasso` | `court` | players or a court zone; the Studio writes its SQL with metric ids |
| `filter` | `filter_bar` | filters by state, such as clutch, home ball, after timeout |
| `toggle_layer` | `layer_list` | one overlay on or off |
| `inspect_query` | `selection_query` | the rows the selection returns |
| `drill_down` | `timeline` | the possession under the playhead → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `drill_down` | `tree_navigator` | the branch chosen; the playhead moves to its start |
| `edit` | the view | a label, a boundary, a parameter or a model version; the edit opens a draft → [VW-STU-02](#vw-stu-02-draft-diff-and-promote) |
| `command` | `command_palette` | any action by name |
| `export` | `clip_export` | a clip reference of the moment (produces `clip_reference`) |
| `export` | `clip_export` | a clip file written inside the private store (produces `video_clip_private`) |
| `export` | `selection_query` | the query text of the selection (produces `sql`) |
| `export` | `selection_query` | an aggregate of the selection through the published-number gate (produces `aggregate_table`) |


### VW-STU-02 Draft, diff and promote

Entry on the catalogue page: [VW-STU-02](views_catalogue.md#vw-stu-02-draft-diff-and-promote). What exactly would this edit change, which stats and predictions move with it, and should it become the current version?

**Definitions**

- item: one draft. A draft is one proposed edit, or a batch of edits made in one session, on one game.
- editable: the proposed value and the reason of an open draft; the choice to promote, discard or undo. The four kinds of edit of R-AS-03: relabel an identity, set, coverage or event; move a boundary; change a registered parameter (R-CX-29); swap a model version.
- an edit creates: a draft state version. It is a row of state_corrections plus a change set that lists every row it touches. Amending a draft writes a new correction that supersedes the old one; the old one stays readable.
- promote: the owner only. It moves the current pointer to the draft version and logs who, when and why. The analyst seat and a Claude session can open and amend drafts; they cannot promote.
- undo: moves the current pointer back to the version before. Byte for byte the same rows are current again (R-AS-09). Undo is itself a logged row.
- never editable: the current version in place, a promoted version, the audit log, the raw readings behind a corrected value, the official record, and any row of a held-out game without the held-out flag on the draft.
- recompute scope: only segments, stats and predictions whose clock range overlaps the change are recomputed (decision K09). Everything else is shown as unchanged, with its count.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `draft_list` | **descriptive**: n = rows the draft changes; descriptive_mark = a count of rows, not an estimate; link = rows | contract |  |
| `diff` | **descriptive**: n = changed rows per table; descriptive_mark = a count of rows, not an estimate; link = state | contract | Note: Old and new value each keep the appearance of their own grade. The new value carries the word DRAFT and is never drawn as current. |
| `downstream_impact` | **estimate**: n = cases behind the old and the new value; interval = printed after each value; level = 0.95; link = rows; min_n = registry<br>**model**: band = printed after each prediction; model_version = printed in the row; link = rows | contract | Note: The three metric ids are examples of the three kinds that move (a count, a win probability, a possession value). The table lists whatever the change set reaches, by id. |
| `recompute_status` | **measurement**: unit = seconds; error = wall-clock time of the stage run as logged, to 0.1 s; link = rows | contract, except<br>**carried**: A value that waits for its recompute is greyed and carries the word "stale" until the new value arrives. It is never shown solid. |  |
| `video` | no number | contract |  |
| `court` | no number | contract |  |
| `audit_log` | no number | contract |  |
| `held_out_flag` | no number | contract |  |
| `promote_bar` | no number | n/a (control) |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (11)**

| Action | At | Target |
|---|---|---|
| `select` | `diff` | a changed row; the inspector shows both versions and video and court jump to its moment |
| `select` | `downstream_impact` | a stat or prediction; the inspector lists the changed rows that move it |
| `scrub` | `video` | video and court move together inside the changed clock range |
| `filter` | `draft_list` | drafts by state, kind of edit and author |
| `edit` | `draft_list` | amend an open draft: a new correction that supersedes it; the old one stays |
| `promote` | `promote_bar` | the draft becomes the current version; owner only; logged |
| `undo` | `promote_bar` | the version before the last promotion is current again, byte for byte |
| `inspect_query` | `downstream_impact` | the rows and the query with metric ids for both versions |
| `drill_down` | `diff` | the changed moment on the game canvas → [VW-STU-01](#vw-stu-01-studio-game-canvas) |
| `drill_down` | `downstream_impact` | the lineage of a moved value → [VW-STU-10](#vw-stu-10-lineage-explorer) |
| `export` | `audit_log` | the audit log of the game as a page (produces `page`) |


### VW-STU-03 Model bench

Entry on the catalogue page: [VW-STU-03](views_catalogue.md#vw-stu-03-model-bench). Which version of this stage is better on the gold set, on which slices, and what does each one get wrong?

**Definitions**

- stages: detection, tracking, team, jersey, pose, court, OCR, action, value, sequence model (R-AS-05).
- gold: versions are compared on the frozen gold set named in the banner. Gold items are never trained on (R-HR-07) and count as gold only after the owner confirmed them (R-HR-12, R-HR-16).
- editable: the chosen version of a stage.
- an edit creates: a draft of kind "swap a model version" (R-AS-03). On promotion the chosen version is written to the run record of the next run (R-AS-05).
- never editable: a gold label, a target (only the planner changes one, with a log, R-RR-07), a score, a row of the error catalogue (append-only, R-RR-05).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `stage_picker` | no number | n/a (control) |  |
| `score_table` | **estimate**: n = gold cases of the row; interval = bootstrap resampled by game, printed after each value; level = 0.95; link = rows; min_n = default | contract | Note: A requirement with no gold sample reads "not testable", never "pass" (R-RR-02). |
| `slice_table` | **estimate**: n = gold cases in the slice; interval = printed after each value; level = 0.95; link = rows; min_n = 50 | contract |  |
| `failure_cases` | **label**: confidence = the confidence the version gave its wrong answer, where stored; version = the model version of the row; link = frames | contract |  |
| `case_video` | no number | contract |  |
| `case_overlay` | **label**: confidence = printed beside each box or label; version = the model version of the layer; link = frames | contract |  |
| `release_check` | **estimate**: n = gold cases of the test with the largest drop; interval = printed after the drop; level = 0.95; link = rows; min_n = default | contract |  |
| `learning_curve` | **estimate**: n = gold cases scored after each batch; interval = a fading band round the line; level = 0.95; link = rows; min_n = default | contract |  |
| `choose_version` | no number | n/a (control) |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (11)**

| Action | At | Target |
|---|---|---|
| `filter` | `stage_picker` | stage, version A, version B and the gold set |
| `select` | `score_table` | a score; the inspector shows both runs and the gold cases behind the value |
| `select` | `failure_cases` | a case; the clip and the overlays move to it |
| `scrub` | `case_video` | the clip of the case and its overlays |
| `toggle_layer` | `case_overlay` | version A output, version B output or the gold label |
| `drill_down` | `slice_table` | the failure cases of the slice |
| `drill_down` | `failure_cases` | the case as a review item → [VW-STU-07](#vw-stu-07-review-item-screen) |
| `drill_down` | `score_table` | the model card of a version → [VW-CARD-04](#vw-card-04-model-card) |
| `inspect_query` | `score_table` | the rows and the query behind the scores |
| `edit` | `choose_version` | the version of the stage; opens a draft → [VW-STU-02](#vw-stu-02-draft-diff-and-promote) |
| `export` | `score_table` | the comparison as a page (produces `page`) |


### VW-STU-04 Parameter sensitivity sweep

Entry on the catalogue page: [VW-STU-04](views_catalogue.md#vw-stu-04-parameter-sensitivity-sweep). If I move this parameter across its range, which stats and which win probabilities move, and by how much?

**Definitions**

- item: one registered parameter (R-CX-29): its name, definition, unit, default, valid range and who may change it.
- sweep: the dependent metrics are recomputed at steps across the valid range, on the games chosen in the scope bar. The sweep is scratch work. It writes no state version and serves no number to any other view.
- editable: the value to try, the range and step of the sweep (inside the valid range), the games in scope.
- an edit creates: nothing, until "Open as draft". That opens a draft of kind "change a parameter" with the chosen value (R-AS-03).
- never editable: the valid range and the owner of a parameter (registry facts), the formula of a metric, a target of a requirement.
- named variants: where the registry holds side-by-side definitions, the sweep shows them as named columns instead of a range: screen rule strict and loose (R-ST-17), the run rules (K05), the three garbage-time flags (K28), the possession count per source definition (R-SY-17).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `parameter_picker` | no number | n/a (control) |  |
| `scope_bar` | no number | n/a (control) |  |
| `sweep_chart` | **estimate**: n = cases at each step; interval = a fading band round the line; level = 0.95; link = rows; min_n = registry | contract | Note: The four metric ids are examples of metrics that declare a parameter. The chart draws every metric that declares the chosen one (the test of R-AS-08). |
| `win_probability_shift` | **model**: band = a fading band round the line; model_version = printed in the legend; link = rows | contract, except<br>**unknown**: Before a win-probability model exists the chart shows a dash and "no model before P6". The pre-game ratings probability is drawn alone where it depends on the parameter. |  |
| `flipped_rows` | **descriptive**: n = rows that flip; descriptive_mark = a count of rows, not an estimate; link = rows | contract |  |
| `rule_variants` | **official**: source = the source named in each column; as_of = the pull time of the source; link = rows<br>**estimate**: n = cases under each definition; interval = printed after each value; level = 0.95; link = rows; min_n = default | contract |  |
| `open_as_draft` | no number | n/a (control) |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (9)**

| Action | At | Target |
|---|---|---|
| `filter` | `scope_bar` | games, team and period of the sweep |
| `brush` | `sweep_chart` | a part of the range; every chart zooms to it |
| `select` | `sweep_chart` | one step of one metric; the inspector shows value, n and rows |
| `select` | `rule_variants` | one definition; the inspector shows its text and its source |
| `drill_down` | `flipped_rows` | the rows that flip as a list; each row links to its frames |
| `drill_down` | `sweep_chart` | the registry entry of the metric → [VW-STU-09](#vw-stu-09-metric-browser) |
| `inspect_query` | `sweep_chart` | the query with the metric id and the parameter binding of each step |
| `edit` | `open_as_draft` | the tried value becomes a draft parameter change → [VW-STU-02](#vw-stu-02-draft-diff-and-promote) |
| `export` | `sweep_chart` | the sweep as a page (produces `page`) |


### VW-STU-05 Network (explain) view

Entry on the catalogue page: [VW-STU-05](views_catalogue.md#vw-stu-05-network-explain-view). For this frame or possession, what went into each network, what came out, and what did the network look at?

**Definitions**

- trigger: the view refreshes when the selected frame, possession or model changes (refresh class on_select), with its own budget because a forward pass and an explanation map take longer than a plain selection.
- networks: every neural network of the pipeline. The test of R-AS-11 names three: the detector, the jersey reader and the sequence model.
- no explanation method: a model without one shows input and output only, and the map says "no explanation method for this model" (R-AS-11).
- no face: the jersey reader is shown the number region of the torso. A person crop is drawn with the head region masked. Nothing of this view can be exported as pixels.
- editable: nothing. The view is read-only.
- an edit creates: nothing. "Send to review" adds one row to the review queue with the trigger "manual"; it changes no label.
- never editable: the input, the output, the map, the model version.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `model_picker` | no number | n/a (control) |  |
| `architecture` | no number | contract |  |
| `input_view` | no number | contract |  |
| `output_view` | **label**: confidence = the score printed beside each output; version = the model version of the banner; link = frames | contract |  |
| `explanation_map` | **descriptive**: n = one instant and one model; descriptive_mark = the map is descriptive: it shows where the output is sensitive, not why the model is right; link = frames | contract, except<br>**unknown**: No method for this model: no map is drawn and the element says "no explanation method for this model". |  |
| `raw_output_table` | **label**: confidence = the raw score of each row; version = the model version of the banner; link = frames | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (8)**

| Action | At | Target |
|---|---|---|
| `filter` | `model_picker` | the stage and the model version |
| `select` | `output_view` | one output; the inspector shows score, version and lineage, and the map is drawn for it |
| `select` | `raw_output_table` | one row; the same output is marked on the input |
| `toggle_layer` | `explanation_map` | the map on or off |
| `step` | `input_view` | one frame forward or back |
| `drill_down` | `architecture` | the model card of the version → [VW-CARD-04](#vw-card-04-model-card) |
| `drill_down` | `output_view` | the same instant on the game canvas → [VW-STU-01](#vw-stu-01-studio-game-canvas) |
| `command` | the view | send the instant to the review queue as a manual item → [VW-STU-06](#vw-stu-06-review-queue) |


### VW-STU-06 Review queue

Entry on the catalogue page: [VW-STU-06](views_catalogue.md#vw-stu-06-review-queue). Which moments should I label next, why these, and how much of my weekly budget do they take?

**Definitions**

- one queue (R-HR-03): every kind of item waits in the same list. Order: failed gold cases first; then disagreement (between models, between sources, invariant breaks) times downstream impact; a random audit share; identity weakness per player as an input to the score.
- triggers (R-HR-01): low confidence on an identity or a jersey number; ball lost or a scramble; player count not 10 for longer than the set time; scoreboard against play-by-play; set match below threshold or no template; coverage or matchup unclear after a switch. Further sources: unmatched CV events, crossings with a swap risk (R-DT-24), track gaps over 1 s (R-DT-11), probable identity runs, quarantined values, market-mapping doubts (R-MK-17), unwhistled-contact candidates (R-RF-21), disputes of the outside approver (R-HR-19), manual items.
- one moment, one item: flags on the same target within the same clip window are folded into one item that lists all its triggers.
- reproducible order (R-HR-03): the score of an item and its parts are stored. The list can be rebuilt from them.
- editable: the status of an item (defer, skip with a reason, reopen); a manual item added by hand; the weekly budget.
- an edit creates: a new status row for the item, logged with who and when; a new queue row for a manual item; a draft parameter change for the budget (the owner can raise it at any time, R-HR-04).
- never editable: the priority score and its parts, the trigger, the model guess, the audit draw, the gold membership of an item. Labels are made on the review item screen, not here.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `budget_bar` | **measurement**: unit = hours and seconds; error = the median and the 90th percentile of the time per item are both printed, with the count of items they come from; link = rows | contract |  |
| `queue_list` | **label**: confidence = the confidence of the model guess; version = the model version of the guess; link = frames<br>**descriptive**: n = flags folded into the item; descriptive_mark = the priority score is a ranking score, not a probability; link = frames | contract, except<br>**quarantined**: Shown hatched, with the two values that contradict each other and the source of each. The queue and the item screen are the only places that show it. |  |
| `trigger_summary` | **descriptive**: n = open items in the cell; descriptive_mark = a count of items, not an estimate; link = rows | contract |  |
| `label_counts` | **descriptive**: n = labels in the cell; descriptive_mark = a count of labels, not an estimate; link = rows | contract |  |
| `gold_set_status` | **descriptive**: n = items of the set; descriptive_mark = counts of items; an item is gold only with the confirmation of the owner; link = rows | contract |  |
| `filter_bar` | no number | n/a (control) |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (10)**

| Action | At | Target |
|---|---|---|
| `drill_down` | `queue_list` | the item on the review item screen → [VW-STU-07](#vw-stu-07-review-item-screen) |
| `command` | the view | next disputed label: opens the first open item → [VW-STU-07](#vw-stu-07-review-item-screen) |
| `select` | `queue_list` | an item; the inspector shows its flags and score parts |
| `filter` | `filter_bar` | label type, trigger, game, player, status, labeller |
| `edit` | `queue_list` | defer, skip with a reason or reopen an item: a new status row; or add a manual item |
| `edit` | `budget_bar` | the weekly budget: a draft parameter change → [VW-STU-02](#vw-stu-02-draft-diff-and-promote) |
| `drill_down` | `label_counts` | the labels of a cell as rows; each row opens its item → [VW-STU-07](#vw-stu-07-review-item-screen) |
| `drill_down` | `gold_set_status` | the agreement report of the label type → [VW-RPT-12](#vw-rpt-12-labeller-agreement-report) |
| `inspect_query` | `queue_list` | the rows and the stored scores that give the order |
| `export` | `label_counts` | label counts per type and class, aggregates only (produces `aggregate_table`) |


### VW-STU-07 Review item screen

Entry on the catalogue page: [VW-STU-07](views_catalogue.md#vw-stu-07-review-item-screen). What happened in this clip, is the guess of the system right, and if not, what is the right label?

**Definitions**

- one screen, four variants. Clip, court, guess, answer keys and label history are the same for every label type. One variant panel is shown, chosen by the label type of the item: turnover, screen, identity, scoreboard. The turnover and the screen variant catalogue the two private tools in use (R-PR-18); their code and data stay private.
- two stored objects: the model guess and the label of a person are separate rows. Confirm copies the guess into a label with who, when, model version and tool version (R-HR-05). Correct writes the label of the reviewer beside the guess. Abstain stores "not visible" or "cannot tell" as an answer.
- who labels (R-HR-16): the banner names the labeller. A label made by a Claude session is stored apart, is shown with the name Claude wherever it appears, and counts as gold only after the owner confirms it.
- guess shown or hidden: prefilled on a normal item (R-HR-02). Hidden on an audit item and on a blind re-show, together with every earlier label, until the answer is stored.
- editable: the answer of the reviewer; the clip window of this item (the reviewer can extend it, R-HR-02); a quick reason.
- an edit creates: a new row of review_labels. A changed mind is another row; the earlier one stays. A label that contradicts a stored state value also writes a correction and opens a draft state version; it never overwrites the value (R-AS-03).
- never editable: the model guess, an earlier label, the official play-by-play, the scorebug reading as read, the clip window in config, gold membership (only the confirmation of the owner makes an item gold), the labelling guide.
- no face: an identity item shows jersey, kit and appearance card. No face crop is cut, shown or stored (R-PR-19).
- coverage (K04): a fine ball-screen coverage is offered as the guess only at confidence 0.8 or more; below that the guess is the coarse class.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `clip` | no number | contract |  |
| `court` | no number | contract |  |
| `guess_panel` | **label**: confidence = printed beside the guess; version = the model version of the guess; link = frames | contract, except<br>**quarantined**: The contradicted value is shown hatched beside the value that contradicts it, each with its source and time. The reviewer decides which stands. |  |
| `answer_bar` | no number | n/a (control) |  |
| `variant_turnover` | **official**: source = the official play-by-play, by version; as_of = the play-by-play version of the banner; link = frames | contract |  |
| `variant_screen` | **label**: confidence = printed beside kind and coverage; version = the rule set and model version of the row; link = frames<br>**measurement**: unit = metres, metres per second, seconds; error = from the position error of screener and user, printed beside each value; link = frames | contract |  |
| `variant_identity` | **label**: confidence = the posterior of each candidate; version = the identity pack and model version of the run; link = frames | contract | Note: Answers: one of the candidates, "none of these" (the candidate list is open), cannot tell. A locked label is never changed in place: the answer adds a row to the switch log and opens a draft. |
| `appearance_card` | no number | contract |  |
| `variant_scoreboard` | **official**: source = each of the three sources, named in its column; as_of = the play-by-play version and the frame of each reading; link = frames<br>**live_state**: grade = by rule 1; age = the lag of each reading in seconds; link = state | contract, except<br>**quarantined**: Both contradicting values are shown hatched with their sources. This is the item that resolves the quarantine. |  |
| `blind_reshow` | no number | n/a (control) |  |
| `label_history` | no number | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (14)**

| Action | At | Target |
|---|---|---|
| `scrub` | `clip` | clip and court move together inside the window |
| `step` | `clip` | one frame back or forward, to set a moment |
| `confirm` | `answer_bar` | the guess is copied into a label of the reviewer |
| `correct` | `answer_bar` | another answer is stored beside the guess |
| `abstain` | `answer_bar` | "not visible" or "cannot tell" is stored as the answer |
| `undo` | `answer_bar` | the last answer of this session is withdrawn by a new row; the earlier row stays readable |
| `edit` | `clip` | extend the clip window for this item; the config window is unchanged |
| `select` | `court` | a player or the ball; the inspector shows identity state and evidence |
| `select` | `variant_identity` | a candidate; clip and court mark the chain and the appearance card moves to him |
| `drill_down` | `label_history` | the moment on the game canvas → [VW-STU-01](#vw-stu-01-studio-game-canvas) |
| `drill_down` | `variant_identity` | the confusion list of the pair → [VW-RPT-13](#vw-rpt-13-identity-quality-report) |
| `drill_down` | `guess_panel` | what the network saw at this instant → [VW-STU-05](#vw-stu-05-network-explain-view) |
| `command` | the view | next disputed label |
| `export` | `clip` | a clip reference of the item (produces `clip_reference`) |


### VW-STU-08 Coach quiz

Entry on the catalogue page: [VW-STU-08](views_catalogue.md#vw-stu-08-coach-quiz). At this paused moment, does the system read the game the way I do?

**Definitions**

- four question types (R-GU-03): who guards a named player, which set, which defence, what happens next.
- as known: the system answers from its belief state at the paused second (R-GU-01), with nothing dated after it. The video cannot be moved past the pause until the answer of the owner is stored.
- order: the owner answers first. The answer of the system stays hidden until then, so that it cannot lead him.
- random draw: the paused moments are drawn at random from live play, with a logged seed. Replays, breaks and stretches off the main camera are not drawn.
- editable: the answer of the owner, once per question.
- an edit creates: one quiz row with the question, both answers and the result. A later change of mind is a new row; the first answer is the one that is scored.
- never editable: the moment, the question, the answer of the system, the score, the pass mark (set per type after game 3 from the measured distribution, D18).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `paused_frame` | no number | contract |  |
| `court` | no number | contract |  |
| `question_card` | no number | n/a (control) |  |
| `system_answer` | **label**: confidence = printed beside each answer of the system; version = the model version of the belief state; link = frames | contract, except<br>**unknown**: Where the system holds no belief (HOLD on the player asked about, no set matched) its answer reads "no answer" with the reason, and the question is scored as not answered, not as wrong. |  |
| `score_table` | **estimate**: n = questions of the type; interval = printed after each share; level = 0.95; link = rows; min_n = default | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (7)**

| Action | At | Target |
|---|---|---|
| `correct` | `question_card` | the owner picks his answer; it is stored before the answer of the system is shown |
| `abstain` | `question_card` | "cannot tell" is stored; the question is not scored |
| `select` | `system_answer` | an answer of the system; the inspector shows the belief state behind it |
| `scrub` | `paused_frame` | back from the pause only; forward is locked until the answer is stored |
| `drill_down` | `score_table` | the questions of a cell as rows; each row reopens its moment |
| `drill_down` | `system_answer` | the moment on the game canvas after the answer → [VW-STU-01](#vw-stu-01-studio-game-canvas) |
| `command` | the view | next question |


### VW-STU-09 Metric browser

Entry on the catalogue page: [VW-STU-09](views_catalogue.md#vw-stu-09-metric-browser). What is this stat, how is it computed, can it be computed today, and which views show it?

**Definitions**

- item: one metric of config/metrics.yaml, by its id. The browser is the view over the registry; the generated catalogue pages are documents and are linked, not copied (R-MR-01).
- categories: the category list is read from the registry at render time. The nineteen ids listed in the registry table are one per category, so that every category is reachable from a view.
- no formula here: definition, formula, unit and parameters are read from the registry row and shown as text. The browser holds no second definition (rule 8).
- editable: nothing. Filters and the sample scope change the screen only.
- an edit creates: nothing. A definition changes in the registry file under version control; the change appears in the change history. A parameter default is tried in the parameter sweep and changed through a draft.
- never editable: an id, a definition, a formula, a value range, a served value.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `filter_bar` | no number | n/a (control) |  |
| `registry_table` | **descriptive**: n = metrics in the registry as counted at render time; descriptive_mark = registry facts, not game numbers; link = none_fixed | contract |  |
| `metric_page` | no number | n/a (no data) |  |
| `sample_value` | **estimate**: n = cases behind the value; interval = printed after the value; level = 0.95; link = rows; min_n = registry<br>**official**: source = the official box score or play-by-play where the metric is a count of it; as_of = the version of the source; link = rows | contract | Note: The two ids are examples (a counted and a box-score possession figure). The tile serves whichever id is selected. |
| `used_by` | no number | n/a (no data) |  |
| `change_history` | no number | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (8)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | category, data tier, computable now, level, depth, text search |
| `select` | `registry_table` | a metric; the page, the sample value, the views that use it and its history are shown |
| `drill_down` | `sample_value` | the rows behind the value; each row links to its frames |
| `drill_down` | `metric_page` | a parameter of the metric, in the sweep → [VW-STU-04](#vw-stu-04-parameter-sensitivity-sweep) |
| `drill_down` | `used_by` | a view that shows the metric; it opens with the same scope → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `inspect_query` | `sample_value` | the query with the metric id and the rows it returns |
| `export` | `sample_value` | the query text of the sample value (produces `sql`) |
| `export` | `registry_table` | the filtered list of metrics as a page (registry facts only) (produces `page`) |


### VW-STU-10 Lineage explorer

Entry on the catalogue page: [VW-STU-10](views_catalogue.md#vw-stu-10-lineage-explorer). Which input files, stage runs, code and config versions produced this row, and what depends on it?

**Definitions**

- item: one stored row, or one stage output (a partition of a table). Lineage is resolved through the partition manifests; a per-frame row carries no lineage string of its own (R-EN-19).
- upstream: the stage runs and stage outputs that fed the row, back to raw pulls, video files and play-by-play versions, with the code version and config hash of every step.
- downstream: the outputs, served metric values, predictions and published numbers that read the row.
- editable: nothing. The view is read-only.
- an edit creates: nothing. Which version is current changes only by a promotion in the draft view; a re-run is started from the pipeline, not from here.
- never editable: a hash, an output key, a run record, a pointer, a manifest.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `row_header` | **measurement**: unit = rows and bytes; error = exact, counted when the output was written; link = rows | contract |  |
| `upstream_graph` | **measurement**: unit = seconds, rows, US dollars; error = as logged by each stage run; link = rows | contract |  |
| `downstream_list` | **descriptive**: n = dependents of the row; descriptive_mark = a count of dependents, not an estimate; link = rows | contract |  |
| `version_history` | no number | contract |  |
| `lineage_audit` | **estimate**: n = rows sampled; interval = printed after the share; level = 0.95; link = rows; min_n = default | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (7)**

| Action | At | Target |
|---|---|---|
| `select` | `upstream_graph` | a stage run or an output; the inspector shows its record and hashes |
| `drill_down` | `upstream_graph` | the run record of a stage run → [VW-RPT-10](#vw-rpt-10-run-record-and-failure-analysis) |
| `drill_down` | `downstream_list` | a dependent row; the explorer re-centres on it |
| `drill_down` | `version_history` | the draft or promotion that made a version → [VW-STU-02](#vw-stu-02-draft-diff-and-promote) |
| `drill_down` | `row_header` | the moment of the row on the game canvas, where the row has one → [VW-STU-01](#vw-stu-01-studio-game-canvas) |
| `inspect_query` | `downstream_list` | the query that lists the dependents |
| `export` | `upstream_graph` | the lineage of the row as a page (keys and hashes, no data rows) (produces `page`) |


## 4. Reports and packets

### VW-RPT-01 Half-time packet

Entry on the catalogue page: [VW-RPT-01](views_catalogue.md#vw-rpt-01-half-time-packet). What happened in the first half that this team should know before the second half starts?

**Definitions**

- snapshot: the packet is frozen at one instant inside the intermission. It reads only values whose known_at_utc is at most the snapshot. It prints the snapshot time and the play-by-play pull time.
- no second look: a stat correction, a late feed row or a replay found after the snapshot never changes a packet. A rebuild is a new packet with a new snapshot time; both are kept.
- one page per team: the same nine elements, written for the team of the page. The score block and the data basis are the same on both pages.
- recorded game: the packet is built by replaying the first half in live mode. Second-half rows and the anchored pass are never read. That is what makes the latency number of R-VZ-08 honest.
- half numbers are descriptions: a rate of one half is printed with its counts and the word "descriptive". It is not drawn against a scale and carries no interval (see notes).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | **live_state**: grade = the worst grade among the values of the page; age = the seconds from the first-half horn to the snapshot, and from the snapshot to now; link = state | n/a (control) | Note: As known: the snapshot time is the newest known-at time the page may read. The seconds from horn to page are the latency number R-VZ-08 asks to be measured and reported. A page opened after the game still says FROZEN and still shows the half as it was known at the snapshot. |
| `data_basis` | **descriptive**: n = the game seconds and the possessions of the half; descriptive_mark = the word "descriptive" under the tile; link = rows | contract | Note: As known: the shares are those of the levels as detected during the half. A replay found only after the snapshot stays counted as live play on this page. A reader must see first how much of the half the system saw. An open flag is counted here; its contradicted value enters no number of the page. |
| `score_block` | **official**: source = the official half-time box when the feed has it at the snapshot; else the scorebug at the horn, and the tile says so; as_of = the snapshot time; link = rows | contract | Note: As known: if the box and the bug disagree at the snapshot, the bug value is shown, the block is marked and the disagreement is counted in the data basis. The packet does not wait for the answer. |
| `four_factors` | **official**: source = the half-time box pulled at the snapshot; the counts are printed as made-attempted; as_of = the pull time of the box; link = rows<br>**descriptive**: n = the count under each rate (attempts, possessions, rebound chances); descriptive_mark = the word "descriptive" in the column head of the half; link = rows<br>**estimate**: n = games played before this game; interval = printed beside the season value; level = 0.95; link = rows; min_n = default | contract | Note: The half column is a description of what happened: counts are class official, the rates made from them are class descriptive and carry no interval (one half rarely reaches estimate_min_n cases). The season column is the only estimate; it is frozen at the pre-game snapshot, so it holds nothing from this game. The half is never coloured against the season value. As known: the box is the one pulled at the snapshot (team_box.pulled_at_utc); a later pull is never read. The schema has no half scope on team_box; schema/views_changes.yaml proposes the column period_scope. |
| `runs` | **official**: source = the score events known at the snapshot; as_of = the snapshot time; link = rows<br>**descriptive**: n = the count of timeouts and of runs in the half; descriptive_mark = the word "descriptive" on the timeout line; no effect of a timeout is claimed; link = rows | contract | *run: the register rule (M-SIT-025) is the shading; the broadcast "a-b" form (M-SIT-024) is the label; both are named in the legend (K05)*<br>Note: As known: the line is drawn from the score events known at the snapshot, at the game clock each was given then. |
| `foul_trouble_bonus` | **official**: source = the play-by-play rows known at the snapshot, checked against the half-time box; as_of = the snapshot time; link = rows | contract | *flag for the second half: the packet applies the cut-off of the first second of the second half from the config table of the live-state field foul_trouble (K10 as changed, R-SR-20), and says so in the column head. The 2 / 4 rule is printed beside it as the named second view.*<br>*team fouls: the count of the first half. The page says that the team count starts again in the second half and that personal fouls carry over.*<br>Note: As known: a foul re-assigned after the snapshot is not on the page. Names come from the feed; no face image is used or shown. |
| `timeouts_challenges` | **official**: source = the play-by-play rows known at the snapshot and the timeout format of the game; as_of = the snapshot time; link = rows | contract | Note: As known: the carry-over is applied by the timeout format of the game, read from the live state. No allotment is written in this record. |
| `set_coverage_mix` | **descriptive**: n = the count behind every share and the count of possessions seen in full; descriptive_mark = the word "descriptive" in the table head; points per set are printed as points and count, not as a rate; link = rows<br>**label**: confidence = the mean match confidence of each row; the count under the gate is printed as "unsure"; version = the template and rule-set versions, in the footer; link = frames | contract | *coverage: the 4 coarse classes always; a fine coverage is counted only at confidence coverage_fine_min_conf or more, else it is counted under its coarse class (K04)*<br>Note: Before phase P4 the element is a card "set and coverage mix arrive with phase P3 (sets) and P4 (coverage)" and holds no number. As known: the labels are those the live matcher gave by the snapshot; a later re-match changes the post-game report, not this page. |
| `top_possessions` | **model**: band = printed beside the value change; model_version = printed in the table footer; link = frames | contract | *value change of a possession: the total of its value credits (M-IMP-065), ranked by size whatever the sign; the sign is printed. Decided here because R-VZ-08 does not say which change is meant (see notes).*<br>Note: Before phase P5 the element is a card "possession value arrives with phase P5" and ranks nothing; it does not fall back to points scored. As known: the ranking uses the value series of the live run up to the snapshot, with its model version; a later model version re-ranks the post-game report, not this page. A player credited while on HOLD is printed as "?" with his candidates. The clip reference holds times and ids only; the video stays in the private store. |

**Every element at every grade and level (9)**

`as_of_banner`

| At | Shows |
|---|---|
| D0 full | One line: FROZEN, snapshot &lt;time>, first half only, pass, version. |
| D1 bug away | No change. |
| D2 off the main camera | No change. |
| D3 replay | No change. |
| D4 break | Normal: the snapshot is taken inside the intermission, which the broadcast shows as a break. |
| D5 no video | Adds "feed-only page". |
| feed stale | Adds "feed quiet since &lt;game clock>" and the pull time of the last row. |

`data_basis`

| At | Shows |
|---|---|
| grade confirmed | Not used. |
| grade observed | Solid shares. The level of each second is what the detectors said then. |
| grade inferred | Seconds whose level was unsure are counted under the stricter level, in a line of their own. |
| grade carried | Not used. |
| grade imputed | Not used. |
| grade unknown | A dash and "no video for the half" when no level was ever set. |
| grade quarantined | Shown as unknown in every tile it touches. Here it is counted as one open flag; its reading is not printed. |
| D0 full | Counted as seen in full. |
| D1 bug away | Counted apart, as "clock estimated". Normal. |
| D2 off the main camera | Counted as "not on the main camera". Possessions with such a stretch are listed as not seen in full. |
| D3 replay | Counted apart. Replays enter no number. |
| D4 break | Counted apart. If the broadcast came back late from a break, the live play it missed is counted as not seen. |
| D5 no video | Counted as "no video". The page says which sections are feed-only. |
| feed stale | The stretch is named by game clock ("feed quiet from 7:42 to 6:10"). |

`score_block`

| At | Shows |
|---|---|
| grade confirmed | Solid. Bug at the horn and the half-time box agree. |
| grade observed | Solid, with the one source named. |
| grade inferred | Solid with "prov": the last basket was seen by CV and not yet confirmed at the snapshot. |
| grade carried | Greyed with the game clock of the last reading. |
| grade imputed | Not used. |
| grade unknown | A dash and the reason. |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | Shown in full. |
| D1 bug away | No change while CV or the feed saw every basket. A window whose edge rests on an estimated clock prints the clock interval. |
| D2 off the main camera | No change while the bug or the feed gives the score. |
| D3 replay | No change. A score seen inside a replay is never read. |
| D4 break | No change. |
| D5 no video | From the feed. |
| feed stale | From the bug and CV. The line "who scored" is not on this block, so nothing is greyed. |

`four_factors`

| At | Shows |
|---|---|
| grade confirmed | Solid. The box counts equal the counts folded from the play-by-play rows known at the snapshot. |
| grade observed | Solid, with the one source named. |
| grade inferred | Not used. |
| grade carried | Greyed, with the game clock up to which the counts run ("through 3:12"). |
| grade imputed | Not used. |
| grade unknown | A dash and "no box at the snapshot". |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | Shown in full. |
| D1 bug away | No change. The factors come from the feed. |
| D2 off the main camera | No change. |
| D3 replay | No change. |
| D4 break | No change. |
| D5 no video | No change. This table needs no video. |
| feed stale | Counts run only to the last feed row. The table is greyed and says through which game clock. No rate is filled in from video. |

`runs`

| At | Shows |
|---|---|
| grade confirmed | Solid line. |
| grade observed | Solid line. |
| grade inferred | Solid line; a basket still provisional at the snapshot is a ringed point with "prov". |
| grade carried | Dashed line over a stretch in which nothing watched the score, with its clock interval. |
| grade imputed | Not used. |
| grade unknown | A gap in the line with the reason. A run is never shaded across a gap. |
| grade quarantined | Shown as unknown: a gap marked "under review". |
| D0 full | Line, shading, labels, timeout marks. |
| D1 bug away | A run edge that rests on an estimated clock prints its clock interval. |
| D2 off the main camera | No change while the bug or the feed gives the score. |
| D3 replay | No change. Replays enter no number. |
| D4 break | No change. |
| D5 no video | From the feed. |
| feed stale | From bug and CV. Timeout marks without a feed row say "team not known". |

`foul_trouble_bonus`

| At | Shows |
|---|---|
| grade confirmed | Solid. Feed rows and the half-time box agree for the player. |
| grade observed | Solid, with the one source named. |
| grade inferred | Only without a feed (blind pass): a count the state inferred, with "prov". |
| grade carried | Greyed, with the game clock up to which the feed ran. |
| grade imputed | Not used. |
| grade unknown | A dash and "no feed". |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | Shown in full. |
| D1 bug away | No change. A bonus clock that rests on an estimated clock prints its interval. |
| D2 off the main camera | No change. |
| D3 replay | No change. |
| D4 break | No change. |
| D5 no video | From the feed. |
| feed stale | Player fouls greyed, with the game clock up to which they are known. Team fouls from the bug. |

`timeouts_challenges`

| At | Shows |
|---|---|
| grade confirmed | Solid. Feed rows and the bug agree. |
| grade observed | Solid, with the one source named. |
| grade inferred | Solid with "prov": a charge that still waited for its feed row at the snapshot. |
| grade carried | Greyed, with the game clock of the last known charge. |
| grade imputed | Not used. |
| grade unknown | A dash and the reason. |
| grade quarantined | Shown as unknown: a dash and "under review". |
| D0 full | Shown in full. |
| D1 bug away | No change. Timeouts come from the feed. |
| D2 off the main camera | No change. |
| D3 replay | No change. |
| D4 break | No change. A break of the first half whose owner was never named is listed as "team not known". |
| D5 no video | From the feed. |
| feed stale | Greyed, with the game clock of the last known charge, where the bug does not show timeouts. |

`set_coverage_mix`

| At | Shows |
|---|---|
| grade confirmed | Not used: a label is a model output. |
| grade observed | Counted under its label. |
| grade inferred | Counted under its label in a column of its own, "prov" (a set named from its first actions only, a pair with a player on HOLD). |
| grade carried | Not counted. A label held through a replay is one label, counted once. |
| grade imputed | Not counted in the mix: a coverage needs its four players seen. |
| grade unknown | Counted in the row "unsure or no template". The row is always printed, also when it is the largest. |
| grade quarantined | Shown as unknown: counted in the row "unsure or no template". |
| D0 full | Shown in full. |
| D1 bug away | No change. |
| D2 off the main camera | Possessions with a stretch off the main camera are left out and counted in the line "not seen in full". |
| D3 replay | No change. A replay is never matched as a set. |
| D4 break | No change. |
| D5 no video | A card "no video - no set or coverage mix". |
| feed stale | No change. |

`top_possessions`

| At | Shows |
|---|---|
| grade confirmed | Not used: a model value is at best observed. |
| grade observed | A row with value change, band and model version. |
| grade inferred | A row marked "prov": a credited player was on HOLD, or the possession rests on a provisional score. |
| grade carried | Not ranked. |
| grade imputed | Not ranked: a possession with an off-screen estimate inside its key action is left out and counted in the footer. |
| grade unknown | Fewer than top_possessions_n rows, and the footer says why. |
| grade quarantined | Shown as unknown: the possession is left out and counted in the footer as "under review". |
| D0 full | Three rows. |
| D1 bug away | No change. A game clock that was estimated prints its interval. |
| D2 off the main camera | A possession with a stretch off the main camera cannot be ranked and is left out; the footer counts them. |
| D3 replay | No change. A replay of the possession is offered as linked evidence in the clip reference. |
| D4 break | No change. |
| D5 no video | A card "no video - no possession value". |
| feed stale | No change. |

**Interactions (9)**

| Action | At | Target |
|---|---|---|
| `select` | the view | any number opens the inspector: value, class, source, as-of, metric id |
| `drill_down` | `four_factors` | the rows behind a count; each row links to its frames |
| `drill_down` | `runs` | a run opens its first possession in the possession explorer → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `drill_down` | `foul_trouble_bonus` | the fouls of one player; each row links to its frames |
| `drill_down` | `set_coverage_mix` | the possessions of one set or one coverage, as a list → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `drill_down` | `top_possessions` | the possession at its key frame → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `inspect_query` | `four_factors` | the rows and the query with the metric ids |
| `export` | `top_possessions` | the clip references of the three possessions (produces `clip_reference`) |
| `export` | the view | the page of one team, without video frames (produces `page`) |


### VW-RPT-02 Post-game notes sheet

Entry on the catalogue page: [VW-RPT-02](views_catalogue.md#vw-rpt-02-post-game-notes-sheet). What are the ten things about this game most worth telling a coach, each with its proof?

**Definitions**

- a note: one sentence, one number with the parts its class asks for, the definition of the number by metric id, and one clip reference.
- ranking: by value change and by novelty. Novelty is the distance of the number from the same team over the season to date. Both scores are printed beside the note.
- words: terms of the vocabulary map and broadcast phrases only. Words that are not measured ("momentum", "wanted it more") are not used (R-GU-04).
- gate: a note leaves the private store only after the published-number gate (R-DQ-15). The sheet says for each note whether it passed.
- time to notes: the seconds from the full video being in the private store to the sheet. Measured and printed; not a gate (K23).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `data_basis` | **descriptive**: n = the possessions and game seconds of the game; descriptive_mark = the word "descriptive" under the tile; link = rows | contract |  |
| `notes_list` | **estimate**: n = printed in the note; interval = printed in the note with its level; level = 0.95; link = frames; min_n = registry<br>**official**: source = the official box or the final play-by-play; as_of = the pull time printed in the banner; link = frames<br>**model**: band = printed in the note; model_version = under the note; link = frames<br>**descriptive**: n = printed in the note; descriptive_mark = the word "descriptive" at the end of the sentence; link = frames | contract, except<br>**inferred**: No note is written on a value that is still provisional after the anchored pass.<br>**carried**: No note is written on a carried value.<br>**imputed**: No note is written on imputed positions.<br>**unknown**: Fewer than ten rows, and the line "n of 10" (see the empty state). | *a note may cite any metric of the registry; the ids listed here are the pool the first version draws from* |
| `left_out` | **estimate**: n = printed in the row; interval = printed in the row; level = 0.95; link = rows; min_n = registry<br>**descriptive**: n = printed in the row; descriptive_mark = the word "descriptive" in the row; link = rows | contract | Note: For the owner and the analyst: it lets the ranking be checked. It is not part of the sheet a coach reads. |
| `build_line` | **measurement**: unit = seconds; error = none: the difference of two logged times; link = rows | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (5)**

| Action | At | Target |
|---|---|---|
| `select` | `notes_list` | the number of a note opens the inspector |
| `drill_down` | `notes_list` | the clip of the note in its possession → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `inspect_query` | `notes_list` | the rows and the query with the metric id |
| `export` | `notes_list` | the sheet as a page, notes that passed the gate only (produces `page`) |
| `export` | `notes_list` | the clip references of the ten notes (produces `clip_reference`) |


### VW-RPT-03 Post-game report

Entry on the catalogue page: [VW-RPT-03](views_catalogue.md#vw-rpt-03-post-game-report). What happened in this game, from the final score down to the possessions and players that decided it?

**Definitions**

- post-game report (decided here, open question OQ-VW-2): one page that holds the box and four factors, the walk down the game, and at reading width the win-probability chart, shot charts, lineups, matchups, the offense, transition and defense tables, the ten notes, the clip list and a line on stat corrections.
- a held view keeps its own record: an element that embeds another view shows a cut of it and links to it. Its numbers obey the record of that view.
- one-game rates are descriptions: a rate of one game is printed with its counts and the word "descriptive". The season value beside it is the estimate.
- transition class: our state rule is the headline. The play-by-play clock definitions are columns beside it and are never merged (R-TR-18).
- coverage: the 4 coarse ball-screen classes always; the fine class only at confidence 0.8 or more (K04).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `data_basis` | **descriptive**: n = the possessions and game seconds of the game; descriptive_mark = the word "descriptive" under the tile; link = rows | contract |  |
| `box_and_factors` | **official**: source = the official box, with the play-by-play version it was checked against; as_of = the pull time of the box; link = rows<br>**descriptive**: n = the count under each rate (attempts, possessions, rebound chances); descriptive_mark = the word "descriptive" in the head of the game column; link = rows<br>**estimate**: n = games played before this game; interval = printed beside the season value; level = 0.95; link = rows; min_n = default | contract, except<br>**unknown**: A count on which the box and the folded play-by-play disagree is shown from the box, marked, and listed in the data basis. |  |
| `player_lines` | **official**: source = the official box; as_of = the pull time of the box; link = rows<br>**descriptive**: n = the count under each rate (attempts, possessions on the floor); descriptive_mark = the word "descriptive" in the head of the rate columns; link = rows | contract |  |
| `tree` | **official**: source = points of the final play-by-play; as_of = the anchored pass or pbp_only; link = rows<br>**descriptive**: n = the possessions of the span; descriptive_mark = the word "descriptive" beside a rate of one span; link = rows<br>**model**: band = printed beside each value; model_version = under the tree; link = frames | n/a (control) | Note: The owner asked for layers from the game down to the player and a tree to walk down (docs/user_inputs.md). The branch chosen here filters every section of the report. |
| `win_probability` | **model**: band = a fading band round the line; model_version = in the chart corner; link = frames | contract |  |
| `shot_charts` | no number | contract |  |
| `lineups` | **official**: source = points and substitutions of the final play-by-play; as_of = the anchored pass or pbp_only; link = rows<br>**estimate**: n = possessions of the unit in the season to date; interval = printed after the rating; level = 0.95; link = rows; min_n = default | contract |  |
| `matchups` | **measurement**: unit = seconds; error = the seconds unassigned and not seen; link = frames<br>**label**: confidence = the mean assignment probability of the cell; version = in the table foot; link = frames | contract |  |
| `offense_breakdown` | **label**: confidence = the share of chances whose set or play type is above its gate, in the table head; version = the grammar and template versions in the table foot; link = frames<br>**descriptive**: n = the chances of each row; descriptive_mark = the word "descriptive" in the head of the game columns; link = rows | contract, except<br>**unknown**: A chance with no matched set is counted in the row "no set matched". It is not forced into a set. |  |
| `transition_breakdown` | **official**: source = the play-by-play clock definitions, each named in its column head; as_of = the anchored pass or pbp_only; link = rows<br>**label**: confidence = the share of possessions whose transition class is above its gate, in the table head; version = the grammar version in the table foot; link = frames<br>**descriptive**: n = the possessions of each row; descriptive_mark = the word "descriptive" in the head of the game columns; link = rows<br>**model**: band = printed beside the value at stake; model_version = in the table foot; link = frames | contract | Note: The play-by-play columns are drawn from P0p. The state-rule columns, numbers advantages and passed-up breaks need P3 and are marked "no tracking yet" before it. |
| `defense_breakdown` | **label**: confidence = the confidence of each scheme and coverage class, beside its share; version = the grammar version in the table foot; link = frames<br>**descriptive**: n = the possessions or screens of each row; descriptive_mark = the word "descriptive" in the head of the game columns; link = rows<br>**measurement**: unit = metres, metres per second and seconds; error = printed beside each mean; link = frames | contract |  |
| `notes` | **estimate**: n = printed in the note; interval = printed in the note with its level; level = 0.95; link = frames; min_n = registry<br>**descriptive**: n = printed in the note; descriptive_mark = the word "descriptive" at the end of the sentence; link = frames | contract |  |
| `clip_browser` | **measurement**: unit = video seconds and a frame number; error = the window round the key frame comes from config per event type; the key frame is exact to one frame; link = frames | contract, except<br>**unknown**: A row with no clip times shows a dash and "no clip". The count of such rows is printed above the list. | Note: The clip index is a data product with no screen of its own (core.yaml out_of_scope). This element is the place where a person browses it. |
| `stat_corrections` | **official**: source = the two play-by-play versions named in the row; as_of = the pull time of each version; link = rows | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (11)**

| Action | At | Target |
|---|---|---|
| `filter` | `tree` | a branch of the walk down; every section narrows to it and the count of possessions left is printed |
| `drill_down` | `tree` | one possession with video → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `drill_down` | `win_probability` | the full chart → [VW-REV-06](#vw-rev-06-layered-win-probability-chart) |
| `drill_down` | `shot_charts` | the full shot chart → [VW-REV-07](#vw-rev-07-shot-chart-by-sector-and-ring) |
| `drill_down` | `lineups` | the full board → [VW-REV-03](#vw-rev-03-lineup-board) |
| `drill_down` | `matchups` | the full board → [VW-REV-02](#vw-rev-02-matchup-board) |
| `drill_down` | `notes` | the full sheet → [VW-RPT-02](#vw-rpt-02-post-game-notes-sheet) |
| `drill_down` | `clip_browser` | the clip in its possession → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `select` | the view | any number opens the inspector |
| `inspect_query` | `box_and_factors` | the rows and the query with metric ids |
| `export` | the view | the report as a page without video frames (produces `page`) |


### VW-RPT-04 Opponent scouting packet

Entry on the catalogue page: [VW-RPT-04](views_catalogue.md#vw-rpt-04-opponent-scouting-packet). What does this opponent normally do, who does it, and where can it be hurt, as known before tip?

**Definitions**

- frozen: the packet reads only games played before the target game, and ratings dated on or before the day before tip. It prints its snapshot time and shows nothing dated after it (R-FD-07, R-CX-09).
- no footage: our video covers an opponent only in its games against Michigan State. A section that needs video is built from those games alone and says how many; with none, it carries "no footage: play-by-play and public data only" (R-OS-05).
- population: a number shows its D-I rank or percentile where a population source exists; else "this team only".
- pre-game report: the name R-OS-03 uses. It is this packet plus the pre-game card. There is no third view.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `data_basis` | **descriptive**: n = the games of the opponent before the snapshot; descriptive_mark = the word "descriptive" under the tile; link = rows | contract |  |
| `opponent_normal` | **estimate**: n = games and possessions before the snapshot; interval = printed after each value; level = 0.95; link = rows; min_n = default<br>**official**: source = the rating system named in the row, from its snapshot dated on or before the day before tip; as_of = the date of the rating snapshot; link = none_fixed | contract, except<br>**carried**: A value that falls back on last season is greyed and says "prior season". |  |
| `style` | **estimate**: n = possessions before the snapshot; interval = printed after each value; level = 0.95; link = rows; min_n = default<br>**label**: confidence = the share of chances with a matched set, in the section head; version = the template version in the section foot; link = frames | contract, except<br>**unknown**: A row that needs video and has none shows a dash and "no footage". |  |
| `defense_profile` | **estimate**: n = games and possessions before the snapshot; interval = printed after each value; level = 0.95; link = rows; min_n = default<br>**label**: confidence = the confidence of each scheme and coverage class; version = the grammar version in the section foot; link = frames | contract, except<br>**unknown**: A row that needs video and has none shows a dash and "no footage". | *coverage: the 4 coarse classes always; the fine class only at confidence 0.8 or more (K04)*<br>Note: The play-by-play rows (shooting allowed by zone, forced turnovers) are drawn from P0p. See the notes of the record on R-OS-03. |
| `players` | **estimate**: n = games and attempts on the card; interval = printed after each value; level = 0.95; link = rows; min_n = registry | contract |  |
| `spot_game_plan` | **estimate**: n = attempts at the spot; interval = printed under each rate with its level; level = 0.8; link = rows; min_n = registry | contract | Note: The part per opponent player needs only play-by-play coordinates (P0p). The part per defender needs the closest defender of each shot (P5). |
| `coach` | **descriptive**: n = the games on the card; descriptive_mark = the word "descriptive" beside every reaction number; link = rows | contract |  |
| `head_to_head` | **official**: source = the official box of each earlier game; as_of = the pull time of each box; link = rows<br>**descriptive**: n = the earlier meetings; descriptive_mark = the word "descriptive" in the section head; link = rows | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (8)**

| Action | At | Target |
|---|---|---|
| `select` | the view | any number opens the inspector |
| `drill_down` | `opponent_normal` | the games behind a number as a list |
| `drill_down` | `players` | the frozen card of the player → [VW-CARD-01](#vw-card-01-player-card) |
| `drill_down` | `coach` | the frozen card of the coach → [VW-CARD-02](#vw-card-02-coach-card) |
| `drill_down` | `head_to_head` | the report of an earlier meeting → [VW-RPT-03](#vw-rpt-03-post-game-report) |
| `drill_down` | `spot_game_plan` | the shots at a spot → [VW-REV-07](#vw-rev-07-shot-chart-by-sector-and-ring) |
| `inspect_query` | `opponent_normal` | the rows and the query with metric ids |
| `export` | the view | the packet as a page without video frames (produces `page`) |


### VW-RPT-05 Edge report per market

Entry on the catalogue page: [VW-RPT-05](views_catalogue.md#vw-rpt-05-edge-report-per-market). Where did our frozen probability differ from the fair market probability, and did the closing line then move our way?

**Definitions**

- frozen first: a prediction enters only if it was made and hashed before the market snapshot it is compared with (R-MK-07). A prediction with no hash, or with a later time, is listed as "not frozen" and enters no number.
- fair probability: the bookmaker margin is removed by the default method chosen under R-MK-32. The method is named in every column head; the power and Shin values are both stored and can both be shown (R-MK-04).
- two variants, never pooled: the model without any market input, and the model with line movement as a feature (R-MK-08).
- no edge claim: a market with fewer priced events than min_priced_events shows its numbers with the line "no edge claim" and never a verdict (R-PR-08).
- paper only: staking is a simulation on stored prices. Nothing on this view is an order, an account action or advice.
- as-of: predictions and prices are read as known at the snapshot. The two elements that need the result of the game read it as of event and say so.
- private: raw prices never leave the private store. Only derived statistics (closing-line value, calibration, skill scores) may be published, through the calibration report or the pitch package (R-MK-24).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `filter_bar` | no number | n/a (control) | *held-out season: 2025-26 is scored once per model family; the banner prints the date it was scored (R-PR-04)* |
| `market_table` | **estimate**: n = priced events of the market; interval = printed after the mean edge and the mean closing-line value; level = 0.95; link = rows; min_n = 200<br>**model**: band = printed in the game rows for each probability; model_version = model family, level and variant in the row; link = rows | contract, except<br>**unknown**: A market with no closing snapshot shows a dash for closing-line value and "no close". |  |
| `game_rows` | **model**: band = the interval printed beside our probability; model_version = in the row; link = rows<br>**official**: source = the book or consensus named in the row, with the snapshot label; as_of = the snapshot time; link = rows | contract, except<br>**unknown**: A price row that failed a contract or carries a data-quality flag is not compared. The row shows a dash and the flag. |  |
| `clv_chart` | **estimate**: n = priced events to date; interval = a fading band round the running mean; level = 0.95; link = rows; min_n = 200 | contract |  |
| `graded_results` | **official**: source = the final score of the official record and the closing line of the named source; as_of = the pull time of the record; link = rows | contract |  |
| `paper_staking` | **descriptive**: n = the graded paper stakes; descriptive_mark = the words "paper simulation, descriptive" in the chart title; link = rows<br>**estimate**: n = the graded paper stakes; interval = printed after the return; level = 0.95; link = rows; min_n = 200 | contract |  |
| `in_game_divergence` | **model**: band = a fading band round our line; model_version = in the chart corner; link = frames<br>**official**: source = the exchange named, mid price with its bid-ask spread; as_of = the source time of each price; a price is joined only inside the UTC error limit of R-MK-03; link = rows | contract, except<br>**unknown**: A stretch where the UTC error of the clock map is over the limit has no joined price. The exchange line has a gap there, with the reason. |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (6)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | market type, variant, level, season and snapshot; the count of priced events left is printed |
| `select` | `market_table` | a market and variant; the game rows and the charts narrow to it |
| `drill_down` | `market_table` | the priced events behind a mean, shown as the game rows |
| `drill_down` | `game_rows` | the pre-game card of the game → [VW-CARD-03](#vw-card-03-pre-game-card) |
| `inspect_query` | `market_table` | the rows and the query with metric ids |
| `export` | `market_table` | derived statistics only: closing-line value and scores per market, no price (produces `aggregate_table`) |


### VW-RPT-06 Calibration and scoring report

Entry on the catalogue page: [VW-RPT-06](views_catalogue.md#vw-rpt-06-calibration-and-scoring-report). When this model said 70 percent, did it happen 70 percent of the time, and does it beat the ratings baseline and the closing line?

**Definitions**

- what is scored: predictions frozen before the event, against results from the official record. A prediction that was not frozen in time is not scored and is counted in the banner.
- baselines: a ratings model as of the day before, and the closing line itself (R-PR-03). Both are in every score table.
- walk-forward: every score is out of sample. The held-out season 2025-26 is scored once per model family and the date is printed (R-PR-04).
- aggregates only: the view holds no player row, no video and no raw price. Its page may be published through the published-number gate (R-DQ-15, R-MK-24).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `scope_bar` | no number | n/a (control) |  |
| `reliability_curve` | **estimate**: n = predictions in each bin; interval = a fading band per bin; level = 0.95; link = rows; min_n = default | contract |  |
| `score_table` | **estimate**: n = predictions scored; interval = printed after each difference to a baseline; level = 0.95; link = rows; min_n = default | contract |  |
| `pit_histogram` | **estimate**: n = predictions per bar; interval = the band a flat histogram would give at this n; level = 0.95; link = rows; min_n = default | contract |  |
| `window_scores` | **estimate**: n = windows scored; interval = printed after each difference; level = 0.95; link = rows; min_n = default | contract |  |
| `rolling_monitor` | **estimate**: n = predictions in the ten games; interval = a fading band round the line; level = 0.95; link = rows; min_n = default | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (7)**

| Action | At | Target |
|---|---|---|
| `filter` | `scope_bar` | model, level, layer, target and period; the count of predictions scored is printed |
| `select` | `reliability_curve` | a bin; the inspector lists its predictions and results |
| `drill_down` | `score_table` | the predictions behind a score as rows |
| `drill_down` | `rolling_monitor` | the win-probability chart of one game → [VW-REV-06](#vw-rev-06-layered-win-probability-chart) |
| `inspect_query` | `score_table` | the rows and the query with metric ids |
| `export` | `score_table` | the scores per layer, aggregates only (produces `aggregate_table`) |
| `export` | the view | the report as a page (produces `page`) |


### VW-RPT-07 Pitch package

Entry on the catalogue page: [VW-RPT-07](views_catalogue.md#vw-rpt-07-pitch-package). What can this system show Michigan State that it does not have today, and how well has it predicted so far?

**Definitions**

- rights gate: the package is built only after the owner signs the gate. It holds numbers, drawings on our own top-down court and clip references. It never holds a broadcast frame, audio, a face image or a raw market price (R-RG-02, R-MK-24).
- every number passes the published-number gate (R-DQ-15) before it is on a page.
- a held view keeps its own record: each section embeds a view of this catalogue and obeys its rules.
- no edge claim below the count of R-PR-08: the results table prints n beside every number and the line "no edge claim" where it applies.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `gate_line` | no number | contract, except<br>**unknown**: Gate not signed: the package shows only this line and "not released" (see the empty state). |  |
| `walk_forward_results` | **estimate**: n = priced events per level and market; interval = printed after each value; level = 0.95; link = rows; min_n = 200 | contract |  |
| `calibration` | **estimate**: n = predictions in each bin; interval = a fading band per bin; level = 0.95; link = rows; min_n = default | contract |  |
| `processed_game` | **official**: source = the official box of the game; as_of = the pull time of the box; link = rows<br>**descriptive**: n = the count under each rate; descriptive_mark = the word "descriptive" in the head of the game columns; link = rows | contract |  |
| `halftime` | **official**: source = the half-time box known at the snapshot of the packet; as_of = the snapshot time of the packet; link = rows | contract |  |
| `notes` | **estimate**: n = printed in the note; interval = printed in the note with its level; level = 0.95; link = frames; min_n = registry<br>**descriptive**: n = printed in the note; descriptive_mark = the word "descriptive" at the end of the sentence; link = frames | contract |  |
| `what_video_adds` | **descriptive**: n = the possessions of the game and the share seen in full; descriptive_mark = the word "descriptive" in the table head; link = rows<br>**label**: confidence = the confidence of each class shown; version = the grammar version in the table foot; link = frames | contract |  |
| `drawings` | no number | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (6)**

| Action | At | Target |
|---|---|---|
| `select` | the view | any number opens the inspector |
| `drill_down` | `processed_game` | the full report of the game → [VW-RPT-03](#vw-rpt-03-post-game-report) |
| `drill_down` | `calibration` | the full calibration report → [VW-RPT-06](#vw-rpt-06-calibration-and-scoring-report) |
| `drill_down` | `notes` | the full notes sheet → [VW-RPT-02](#vw-rpt-02-post-game-notes-sheet) |
| `export` | the view | the package as a page: numbers, drawings and clip references (produces `page`) |
| `export` | `drawings` | one drawing (produces `top_down_render`) |


### VW-RPT-08 Hypothesis result table

Entry on the catalogue page: [VW-RPT-08](views_catalogue.md#vw-rpt-08-hypothesis-result-table). Which registered hypotheses were tested, what was found, and which findings are only exploratory?

**Definitions**

- item: one test of one registered hypothesis (config/hypotheses.yaml). A hypothesis is registered before its data is looked at (R-HY-01).
- one format: a null result has the same row as a positive one - estimate, interval, adjusted p, n, data version, decision (R-HY-05).
- exploratory: a finding that was not registered first carries the word "exploratory" in its row and is promoted only after confirmation on held-out games (R-HY-04).
- intervals: bootstrap over whole games, not possessions (R-VA-06). Multiple testing: Holm inside a registered family; Benjamini-Hochberg across exploratory features (R-VA-07).
- editable: nothing.
- an edit creates: nothing. A new test writes a new row. A changed statement is a new version of the hypothesis with a new registration date.
- never editable: a registration date, a statement after registration, an estimate, a decision. The decision is written by the test under the decision rule that was registered.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `filter_bar` | no number | n/a (control) |  |
| `result_table` | **estimate**: n = printed in the row; interval = printed after the estimate; level = 0.95; link = rows; min_n = default | contract |  |
| `family_view` | **estimate**: n = tests in the family and cases per test; interval = the interval of each estimate is in the result table; level = 0.95; link = rows; min_n = default | contract |  |
| `registration_check` | no number | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (6)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | family, decision, registered or exploratory, data version |
| `select` | `result_table` | a test; the inspector shows the registered text and the query |
| `drill_down` | `result_table` | the games and rows behind the estimate; each row links on to its frames |
| `drill_down` | `result_table` | the registry entry of the primary metric → [VW-STU-09](#vw-stu-09-metric-browser) |
| `inspect_query` | `result_table` | the rows and the query with metric ids |
| `export` | `result_table` | the result table as a page (produces `page`) |


### VW-RPT-09 Game processing and data-quality report

Entry on the catalogue page: [VW-RPT-09](views_catalogue.md#vw-rpt-09-game-processing-and-data-quality-report). Is the data of this game complete and sound enough to use, and where is it weak?

**Definitions**

- one page per game and run, read top to bottom: verdict, intake, usable share, completeness, distributions, possession counts, official-record checks, invariant breaks, time at each level, latency, cost, revisions.
- latency (decision K23): measured and reported beside its budget, per field and per view. It is never a pass or fail line on this page.
- invariant breaks: each break is named by its invariant id, with the row and the frame. A value held in quarantine is named here by rule and row; the contradicted value itself is shown only on the review screens.
- drift (K17): games 1 to 10 of a source tier show quantiles only. A drift verdict appears from game 11.
- editable: nothing.
- an edit creates: nothing. A wrong value is corrected by answering its review item, or by a new run; both leave this page as it was and produce a new page.
- never editable: any number, flag or verdict of the page. A page of a failed run is kept until the fix is verified (R-RR-08).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `verdict` | **official**: source = the official box score and play-by-play; as_of = the play-by-play version of the banner; link = rows<br>**descriptive**: n = breaks and differences counted over the whole game; descriptive_mark = counts of this game, not estimates; link = rows | contract |  |
| `intake` | **measurement**: unit = seconds, frames, pixels, frames per second; error = as measured at intake; the spread of the frame interval is printed beside the frame rate; link = frames | contract |  |
| `usable_share` | **estimate**: n = possessions of the game; interval = printed after the share; level = 0.95; link = rows; min_n = default | contract |  |
| `completeness` | **descriptive**: n = rows of the table in this game; descriptive_mark = an exact share for this game, not an estimate; link = rows | contract |  |
| `distributions` | **descriptive**: n = rows of the field in this game and games in the baseline; descriptive_mark = quantiles only until 10 games of the same source tier exist; a verdict from game 11; link = rows | contract |  |
| `possession_counts` | **official**: source = the source named in each column; as_of = the pull time of each source; link = rows | contract |  |
| `official_record_checks` | **official**: source = the official record named in each row; as_of = the play-by-play and box version of the banner; link = rows<br>**measurement**: unit = metres; error = the position error of the release point, printed beside the difference; link = frames | contract |  |
| `invariant_breaks` | **descriptive**: n = breaks per invariant in this game; descriptive_mark = counts of this game, not estimates; link = frames | contract |  |
| `level_time` | **measurement**: unit = seconds and share of game time; error = whole seconds; a boundary is known to one second; link = frames | contract |  |
| `latency` | **measurement**: unit = seconds; error = median and 95th percentile are both printed; the error of the wall-clock estimate is printed beside each delay; link = state | contract |  |
| `cost` | **measurement**: unit = seconds, calls, gigabytes, US dollars; error = as logged by each stage run; link = rows | contract |  |
| `revisions` | **official**: source = the official play-by-play and box score; as_of = the time each version became known; link = rows | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (8)**

| Action | At | Target |
|---|---|---|
| `select` | `completeness` | a field; the inspector shows the check and the rows that are empty |
| `drill_down` | `invariant_breaks` | a break as a review item, where one exists → [VW-STU-07](#vw-stu-07-review-item-screen) |
| `drill_down` | `level_time` | a stretch on the game canvas → [VW-STU-01](#vw-stu-01-studio-game-canvas) |
| `drill_down` | `revisions` | the version diff of the game → [VW-RPT-15](#vw-rpt-15-play-by-play-version-diff) |
| `drill_down` | `cost` | the run record of the run → [VW-RPT-10](#vw-rpt-10-run-record-and-failure-analysis) |
| `drill_down` | `official_record_checks` | the rows that differ; each row links to its frames |
| `inspect_query` | `possession_counts` | the query with the metric ids of each definition |
| `export` | the view | the report as a page (produces `page`) |


### VW-RPT-10 Run record and failure analysis

Entry on the catalogue page: [VW-RPT-10](views_catalogue.md#vw-rpt-10-run-record-and-failure-analysis). What did this run test, what passed or failed and on what evidence, and what changed since the run before?

**Definitions**

- result (R-RR-02): pass, fail or not testable. A requirement with no gold sample is "not testable", never "pass". Each result has n and a 95 % interval from a bootstrap resampled by game.
- slices (R-RR-03a): nine technical slices and six game-situation slices. Every slice shows its n. A slice with n below 50 is listed, not flagged.
- cause (R-RR-03b): one of data, label, model, threshold, upstream gate, compute.
- source tier (R-GT-03): one result row per tier of video source.
- editable: nothing.
- an edit creates: nothing. A target changes only through the planner, with date, old value, new value and reason (R-RR-07); the change is shown in the header of the next run.
- never editable: a result, a target from this page, a row of the error catalogue (append-only, R-RR-05), the outputs of a failed run (kept until the fix is verified, R-RR-08).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `run_header` | **measurement**: unit = hours, compute units, gigabytes; error = as logged by the runner; link = rows | contract |  |
| `stage_table` | **measurement**: unit = rows, seconds, US dollars; error = as logged by each stage run; link = rows | contract |  |
| `requirement_results` | **estimate**: n = gold cases of the row; interval = bootstrap resampled by game, printed after the value; level = 0.95; link = rows; min_n = default | contract |  |
| `slice_report` | **estimate**: n = gold cases in the slice; interval = printed after each rate; level = 0.95; link = rows; min_n = 50 | contract |  |
| `worst_cases` | **label**: confidence = the confidence of the wrong prediction, where stored; version = the model version of the row; link = frames | contract |  |
| `reproducibility` | **descriptive**: n = stages re-run; descriptive_mark = a count of stages that matched, not an estimate; link = rows | contract |  |
| `filter_bar` | no number | n/a (control) |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (8)**

| Action | At | Target |
|---|---|---|
| `filter` | `filter_bar` | result, phase, requirement family, source tier, cause |
| `select` | `requirement_results` | a result; the inspector shows its gold cases and the interval |
| `drill_down` | `requirement_results` | the slices and worst cases of the requirement |
| `drill_down` | `worst_cases` | the case as a review item with its clip → [VW-STU-07](#vw-stu-07-review-item-screen) |
| `drill_down` | `stage_table` | the lineage of a stage output → [VW-STU-10](#vw-stu-10-lineage-explorer) |
| `drill_down` | `slice_report` | the two versions side by side on the bench → [VW-STU-03](#vw-stu-03-model-bench) |
| `inspect_query` | `requirement_results` | the rows and the query behind a result |
| `export` | the view | the run record as a page (produces `page`) |


### VW-RPT-11 Monitoring and alerts board

Entry on the catalogue page: [VW-RPT-11](views_catalogue.md#vw-rpt-11-monitoring-and-alerts-board). Since the last game, is anything drifting, missing, late or over budget, and what needs my attention first?

**Definitions**

- as known: the board shows the state of the platform as known now and prints the time of its newest and its oldest input.
- alert: a rule that is true now. An alert closes when its rule is no longer true. It cannot be closed by hand.
- privacy lane (R-AS-10, R-PR-19): the board is where the standing privacy checks are read - no video frame and no face crop outside the private store, exports by kind, the outside-approver lane read-only and separate.
- latency (K23): the trend is reported beside the budgets. It raises no alert.
- editable: nothing.
- an edit creates: nothing. An alert threshold is a registered parameter: it is tried in the parameter sweep and changed through a draft.
- never editable: an alert, a verdict, a count.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `alerts` | **descriptive**: n = games or weeks the rule looked at; descriptive_mark = the value that tripped the rule, shown with its threshold; link = rows | contract |  |
| `table_health` | **descriptive**: n = rows of the table in the game; descriptive_mark = exact counts and shares per game; a drift verdict only from game 11 (K17); link = rows | contract |  |
| `model_health` | **estimate**: n = predictions in the ten games; interval = a fading band round the line; level = 0.95; link = rows; min_n = default | contract, except<br>**unknown**: Before a model is deployed the chart shows a dash and "no deployed model before P6". |  |
| `market_health` | **estimate**: n = games of the week per source; interval = printed after each share; level = 0.95; link = rows; min_n = default | contract |  |
| `latency_trend` | **measurement**: unit = seconds; error = median and 95th percentile per game are both drawn; link = rows | contract |  |
| `budget_use` | **measurement**: unit = compute units, hours, gigabytes, calls, US dollars; error = as logged by the runner and the collectors; link = rows | contract |  |
| `privacy_lane` | **descriptive**: n = exports and served numbers checked; descriptive_mark = counts from the audit; any count above zero in the first line is an alert; link = rows | contract |  |
| `review_load` | **descriptive**: n = open items; descriptive_mark = a count of items, not an estimate; link = rows | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (8)**

| Action | At | Target |
|---|---|---|
| `select` | `alerts` | an alert; the inspector shows the rule and the values that tripped it |
| `drill_down` | `alerts` | the processing report of the game the alert names → [VW-RPT-09](#vw-rpt-09-game-processing-and-data-quality-report) |
| `drill_down` | `model_health` | the calibration report of the model → [VW-RPT-06](#vw-rpt-06-calibration-and-scoring-report) |
| `drill_down` | `budget_use` | the run record behind a cost → [VW-RPT-10](#vw-rpt-10-run-record-and-failure-analysis) |
| `drill_down` | `review_load` | the review queue → [VW-STU-06](#vw-stu-06-review-queue) |
| `drill_down` | `privacy_lane` | the calibration report of the outside approver → [VW-RPT-14](#vw-rpt-14-jev-calibration-report) |
| `inspect_query` | `table_health` | the rows and the query behind a health number |
| `export` | the view | the board as a page (produces `page`) |


### VW-RPT-12 Labeller agreement report

Entry on the catalogue page: [VW-RPT-12](views_catalogue.md#vw-rpt-12-labeller-agreement-report). Do my labels agree with my own earlier labels, with a second labeller and with the labels Claude made, for each label type?

**Definitions**

- item: one label type (turnover, screen, identity, set, coverage, event).
- self-agreement (R-HR-06): the share of blind re-shows on which the owner gave the same answer again. Below the line the label type is paused.
- second labeller (R-HR-10, R-HR-14): agreement beyond chance on a shared sample. Claude is a named labeller; its labels are stored apart (R-HR-16).
- gate for AI labels (R-HR-16): labels made by Claude are scored against the labels of the owner per type before any of them is used, and one counts as gold only after the owner confirmed it.
- editable: nothing.
- an edit creates: nothing. A disagreement is resolved by the owner on the review item screen, as a new label.
- never editable: a label, an agreement number, the paused state of a label type (it lifts when agreement is back above the line).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `self_agreement` | **estimate**: n = items shown again; interval = printed after the share; level = 0.95; link = rows; min_n = default | contract |  |
| `agreement_matrix` | **estimate**: n = shared possessions in the cell; interval = printed in the cell; level = 0.95; link = rows; min_n = 50 | contract |  |
| `ai_label_gate` | **estimate**: n = items labelled by both; interval = printed after the share; level = 0.95; link = rows; min_n = default | contract |  |
| `disagreement_list` | no number | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (5)**

| Action | At | Target |
|---|---|---|
| `select` | `agreement_matrix` | a cell; the inspector lists the shared items and both labels |
| `drill_down` | `disagreement_list` | the item on the review item screen → [VW-STU-07](#vw-stu-07-review-item-screen) |
| `drill_down` | `self_agreement` | the re-shown items of a label type as rows |
| `inspect_query` | `ai_label_gate` | the rows and the query behind the agreement |
| `export` | the view | the agreement numbers per label type as a page (produces `page`) |


### VW-RPT-13 Identity quality report

Entry on the catalogue page: [VW-RPT-13](views_catalogue.md#vw-rpt-13-identity-quality-report). Which players does the system identify reliably, which pairs does it mix up, and may this game feed player-level numbers?

**Definitions**

- label: every number here reads locked labels only. HOLD is a state, counted as HOLD. The probable tier is counted in its own column as a share of frames; a probable name is never printed in a row and never feeds a number (OD-8).
- recording standard (R-ID-18, OD-9): a game feeds player-level numbers only if recorded at 1080 lines or more and 59.94 frames per second or more. Below that the page says "team-level only".
- locked labels never swap (R-ID-17): the switch log lists every label change, alarm and offline correction as a row. Nothing in it is overwritten.
- no face: identity rests on jersey, kit, build and movement cues. The page shows no face image and uses none.
- editable: nothing.
- an edit creates: nothing. A wrong identity is corrected on the review item screen; that adds a row to the switch log and opens a draft.
- never editable: a locked label in place, the switch log, an accuracy number.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `recording_standard` | **measurement**: unit = pixels and frames per second; error = as read from the file at intake; link = rows | contract |  |
| `per_player` | **estimate**: n = on-court frames of the player and gold frames where accuracy is given; interval = printed after each share; level = 0.95; link = frames; min_n = default | contract |  |
| `confusion_list` | **descriptive**: n = frames with both players on the floor; descriptive_mark = counts of this game, not estimates; link = frames<br>**measurement**: unit = nats per second; error = from the spread over the frames of the pair, printed beside the rate; link = frames | contract |  |
| `switch_log` | **estimate**: n = exposure in frames and crossings; interval = the upper bound of the swap rate, printed; level = 0.95; link = frames; min_n = default | contract |  |
| `lock_timeline` | no number | contract |  |
| `probable_runs` | **label**: confidence = the mean posterior of the run; version = the identity pack and model version of the run; link = frames | contract |  |
| `lineup_check` | **descriptive**: n = possessions of the game; descriptive_mark = counts and shares of this game, not estimates; link = frames | contract |  |
| `season_roll_up` | **estimate**: n = games and gold frames of the player; interval = printed after each share; level = 0.95; link = rows; min_n = default | contract |  |
| `jersey_read_curve` | **estimate**: n = person boxes per height bin; interval = a fading band round the line; level = 0.95; link = frames; min_n = default | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (8)**

| Action | At | Target |
|---|---|---|
| `select` | `per_player` | a player; the timeline, the confusion list and the switch log narrow to him |
| `select` | `lock_timeline` | a stretch; the inspector shows the lock state and the hold reason |
| `drill_down` | `switch_log` | the row as an identity review item → [VW-STU-07](#vw-stu-07-review-item-screen) |
| `drill_down` | `probable_runs` | the run as an identity review item, where the name is read on clip and court → [VW-STU-07](#vw-stu-07-review-item-screen) |
| `drill_down` | `lock_timeline` | the stretch on the game canvas → [VW-STU-01](#vw-stu-01-studio-game-canvas) |
| `drill_down` | `confusion_list` | the crossings of the pair as rows; each links to its frames |
| `inspect_query` | `per_player` | the rows and the query behind a share |
| `export` | the view | the report as a page inside the private store (produces `page`) |


### VW-RPT-14 JEV calibration report

Entry on the catalogue page: [VW-RPT-14](views_catalogue.md#vw-rpt-14-jev-calibration-report). For each kind of question, how often is the outside approver right against my answer key, and may its verdicts count?

**Definitions**

- JEV: the outside approver. It never creates, changes or deletes a label, track, feature or prediction (R-HR-17). Its verdicts only confirm an item or send it to the review queue as a dispute.
- read-only lane (R-AS-10): this report is the only screen of the lane. The Studio never writes to the consultation log, and no pipeline module reads it (R-HR-13).
- calibration (R-HR-19): each consultation type is scored on the locked answer key of the owner before its verdicts count, and again on every change of the pinned model version.
- not shown: the questions as sent (blind multiple choice with raw frames, R-HR-18) are shown to a model, not to a person; they are no view.
- editable: nothing.
- an edit creates: nothing. A new answer key is a new key version made by the owner; it starts a new calibration.
- never editable: the consultation log, a verdict, the answer key from this page, the pinned model version.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `type_table` | **estimate**: n = items of the answer key for the type; interval = printed after each value; level = 0.95; link = rows; min_n = default | contract |  |
| `reliability_curve` | **estimate**: n = items in each bin; interval = a fading band per bin; level = 0.95; link = rows; min_n = default | contract |  |
| `verdict_use` | **descriptive**: n = consultations of the game and type; descriptive_mark = counts of verdicts; a verdict is never a label; link = rows | contract |  |
| `cost` | **measurement**: unit = calls and US dollars; error = as logged by the lane; link = rows | contract |  |
| `isolation_checks` | no number | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (5)**

| Action | At | Target |
|---|---|---|
| `select` | `type_table` | a consultation type; the curve and the verdict table narrow to it |
| `drill_down` | `verdict_use` | a dispute as a review item → [VW-STU-07](#vw-stu-07-review-item-screen) |
| `drill_down` | `type_table` | the items of the answer key for the type as rows |
| `inspect_query` | `type_table` | the rows and the query behind the accuracy |
| `export` | the view | the calibration report as a page (produces `page`) |


### VW-RPT-15 Play-by-play version diff

Entry on the catalogue page: [VW-RPT-15](views_catalogue.md#vw-rpt-15-play-by-play-version-diff). What did the official play-by-play or box score change after the game, and which of our numbers moved because of it?

**Definitions**

- version (R-SY-20): every pull that differs from the one before is stored as a version with a content hash. A pull with no change is counted and makes no version.
- as known: the report compares what was known at two times. Each version prints the time it became known.
- scope of re-scoring: only tables and published outputs whose clock range overlaps a change are re-scored, and they are marked. Everything else is listed as untouched, with its count.
- editable: nothing. Choosing the two versions to compare changes the screen only.
- an edit creates: nothing. The official record is never corrected by us; a disagreement with it is a review item.
- never editable: a version (old versions stay readable), which version is canonical (the stored rule decides), a diff row.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `version_list` | **official**: source = the official play-by-play feed named in the row; as_of = the time the version became known; link = rows | contract |  |
| `play_diff` | **official**: source = the two versions named in the banner; as_of = the time each version became known; link = frames | contract |  |
| `box_diff` | **official**: source = the official box score; as_of = the two snapshots named in the row; link = rows | contract | Note: The four metric ids are examples of counts a revision re-credits (assists, turnovers, rebounds, fouls). The table lists whichever ids the corrections name. |
| `affected_outputs` | **descriptive**: n = tables and served numbers that overlap a change; descriptive_mark = counts of rows and outputs, not estimates; link = rows | contract |  |
| `change_strip` | no number | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (8)**

| Action | At | Target |
|---|---|---|
| `filter` | `version_list` | the two versions to compare |
| `select` | `play_diff` | a changed play; the inspector shows both raw rows |
| `brush` | `change_strip` | a clock range; the diff tables narrow to it |
| `drill_down` | `play_diff` | the possession of the play with its video → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `drill_down` | `affected_outputs` | the lineage of an affected output → [VW-STU-10](#vw-stu-10-lineage-explorer) |
| `drill_down` | `box_diff` | the plays that caused the re-credit |
| `inspect_query` | `affected_outputs` | the query that finds the overlapping outputs |
| `export` | the view | the diff as a page (produces `page`) |


### VW-RPT-16 Rest-of-season simulation

Entry on the catalogue page: [VW-RPT-16](views_catalogue.md#vw-rpt-16-rest-of-season-simulation). Against which of the remaining opponents is Michigan State favoured, and how sure is that?

**Definitions**

- two as-of rules: a remaining game shows a forecast (as known at the time of the simulation). A played game shows its result (as of event) beside the forecast that was frozen before tip.
- one simulation at a time: the view names the simulation, its time, its model versions and its count of simulated seasons. Two simulations are compared in their own table, never mixed in one column.
- two model variants are kept apart: without any market input, and with line movement as a feature (R-MK-08). The variant is named in the title.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `remaining_games` | **model**: band = printed beside each probability and margin; parameter and simulation uncertainty are named apart; model_version = the simulation id and model versions in the table head; link = rows | contract, except<br>**unknown**: A game the simulation could not price (opponent with no rating yet) shows a dash and the reason. |  |
| `played_games` | **official**: source = final scores of the official record; as_of = the pull time of the record; link = rows<br>**model**: band = the frozen interval beside each forecast; model_version = in the table head; link = rows | contract |  |
| `season_outlook` | **model**: band = the full distribution is drawn; the interval is printed under it; model_version = in the chart corner; link = rows | contract |  |
| `change_since_last` | **model**: band = both bands are printed; a difference inside both bands is marked "inside the band"; model_version = both simulation ids in the table head; link = rows | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (5)**

| Action | At | Target |
|---|---|---|
| `select` | `remaining_games` | a game; the inspector shows the simulation and its inputs |
| `drill_down` | `remaining_games` | the pre-game card of the game → [VW-CARD-03](#vw-card-03-pre-game-card) |
| `drill_down` | `played_games` | the win-probability chart of the game → [VW-REV-06](#vw-rev-06-layered-win-probability-chart) |
| `inspect_query` | `remaining_games` | the rows and the query with metric ids |
| `export` | `remaining_games` | the table of remaining games, aggregates only (produces `aggregate_table`) |


## 5. Cards

### VW-CARD-01 Player card

Entry on the catalogue page: [VW-CARD-01](views_catalogue.md#vw-card-01-player-card). Who is this player, what does he tend to do, and how sure are we of each tendency, as of this date?

**Definitions**

- frozen: one card per player per game date. Every field carries its source and date. Nothing dated after the snapshot is on it (R-PC-14).
- not public: a field that is not published says "not public". It is never estimated.
- no face image: the identity block is name, number, team mark and listed measures. No headshot is shown or needed (decision of 11 Nov 2026).
- excluded by design: race, ethnicity or proxies for them, face data, private health, private social media (R-PC-15).
- population: a metric shows its D-I percentile where a population source exists; else the label "MSU games only" (R-PC-18).
- every estimate states its prior, its effective sample size and its shrinkage factor in the inspector (R-VL-12).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `identity_block` | **official**: source = the roster listing or the public source named on each field; as_of = the date on each field; link = none_fixed | contract, except<br>**unknown**: A field that is not public shows "not public". It is never estimated. | Note: The birth date is not shown; only the age at tip. The roster table has a headshot link column; no view reads it. |
| `role_and_usage` | **estimate**: n = games and possessions used; interval = the posterior interval after each value; level = 0.95; link = rows; min_n = registry | contract, except<br>**unknown**: A role cluster that is not stable is not shown. The row says "role not stable yet" and n. |  |
| `production` | **estimate**: n = games and possessions used; interval = the posterior interval after each value; level = 0.95; link = rows; min_n = registry | contract, except<br>**carried**: A value that falls back on last season is greyed and says "prior season". |  |
| `tendencies` | **estimate**: n = the actions behind the tendency; interval = the posterior interval after each value; level = 0.95; link = rows; min_n = registry | contract, except<br>**unknown**: A tendency below its reliability n shows "too few" and n, never a value (R-PC-11). | Note: Shot-clock use and finishing from play-by-play at P0p. The tendencies that need tracking arrive at P3 to P5 and are hidden until they reach their n. |
| `spot_shooting_map` | **estimate**: n = attempts at the spot; interval = printed under the rate with its level; level = 0.8; link = rows; min_n = registry | contract, except<br>**unknown**: A shot with no location is at no spot. The count of such shots is printed under the map. | *partition: the named spots of config/named_spots.yaml. The sector and ring chart is the shot chart view.* |
| `defense_block` | **estimate**: n = possessions or shots defended; interval = the posterior interval after each value; level = 0.95; link = rows; min_n = registry | contract, except<br>**unknown**: Before tracking the rim rows show a dash and "needs tracking". Block and steal rates are shown from the box. |  |
| `availability_line` | **official**: source = the public report named on the line; as_of = the as-of time of the status; link = none_fixed | contract, except<br>**unknown**: No public report: the line says "no public report". Health is never inferred. | Note: A private note of the owner (availability.is_private_note) is shown to the owner alone and is marked private. |
| `background` | **official**: source = the publication named, with its kind; as_of = the publication date; link = none_fixed | contract, except<br>**unknown**: Nothing published: "not public". | Note: Never a model input (decision D24). |
| `inspector` | no number | n/a (control) |  |

**Interactions (5)**

| Action | At | Target |
|---|---|---|
| `select` | the view | any number opens the inspector |
| `drill_down` | `tendencies` | the plays behind a tendency as a list with clip links → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `drill_down` | `spot_shooting_map` | the shots at a spot → [VW-REV-07](#vw-rev-07-shot-chart-by-sector-and-ring) |
| `inspect_query` | `production` | the rows and the query with metric ids |
| `export` | the view | the card as a page (produces `page`) |


### VW-CARD-02 Coach card

Entry on the catalogue page: [VW-CARD-02](views_catalogue.md#vw-card-02-coach-card). How does this coach run a game, and which of those habits are measured, as of this date?

**Definitions**

- frozen: computed only from games played before the target game; the card prints its snapshot date (R-FD-07).
- descriptive unless designed: a number about a reaction (a timeout during a run, a substitution after a mistake, a scheme change) carries the word "descriptive". An effect is shown only when a registered identification design stands behind it, and the design is named (R-HY-08).
- run: the register rule M-SIT-025 unless another definition is chosen and named (K05).
- not on the card: timeout purpose (R-CC-07 is excluded for now) and sideline reactions seen on video (R-CC-04), until staff respond and the labels exist.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `profile` | **official**: source = the public record named on the tile; as_of = the snapshot date; link = none_fixed | contract |  |
| `timeouts_and_runs` | **descriptive**: n = the timeouts and runs counted; descriptive_mark = the word "descriptive" beside every count, share and lag; link = rows<br>**estimate**: n = the matched timeouts of the registered design; interval = printed after the effect; level = 0.95; link = rows; min_n = default | contract | Note: The effect column is empty, with "no registered design yet", until the design of R-HY-08 exists. |
| `after_timeout_sets` | **label**: confidence = the match confidence of each set; version = the template version in the table foot; link = frames<br>**descriptive**: n = the timeouts with a matched set; descriptive_mark = the word "descriptive" in the table head; link = rows | contract, except<br>**unknown**: A timeout with no matched set is counted in the row "no set matched". |  |
| `substitutions_and_fouls` | **descriptive**: n = the substitutions and foul-trouble cases counted; descriptive_mark = the word "descriptive" in the table head; link = rows | contract |  |
| `adjustments` | **descriptive**: n = the games and changes counted; descriptive_mark = the word "descriptive" in the table head; link = rows<br>**measurement**: unit = seconds; error = printed beside each lag; link = frames | contract | Note: The half-time row is drawn from play-by-play at P0p; the scheme rows need P4. |
| `end_game` | **descriptive**: n = the cases of each choice; descriptive_mark = the word "descriptive" in the table head; link = rows | contract |  |
| `head_to_head` | **official**: source = the official record of each meeting; as_of = the snapshot date; link = rows | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (6)**

| Action | At | Target |
|---|---|---|
| `select` | the view | any number opens the inspector |
| `drill_down` | `timeouts_and_runs` | the timeouts as a list; each opens in the chart of its game → [VW-REV-06](#vw-rev-06-layered-win-probability-chart) |
| `drill_down` | `after_timeout_sets` | the possessions after a timeout → [VW-REV-01](#vw-rev-01-possession-explorer) |
| `drill_down` | `head_to_head` | the report of an earlier meeting → [VW-RPT-03](#vw-rpt-03-post-game-report) |
| `inspect_query` | `timeouts_and_runs` | the rows and the query with metric ids |
| `export` | the view | the card as a page (produces `page`) |


### VW-CARD-03 Pre-game card

Entry on the catalogue page: [VW-CARD-03](views_catalogue.md#vw-card-03-pre-game-card). What is known about this game before tip, and what does each prediction layer say, with which drivers?

**Definitions**

- one record, one view: the card renders the frozen record pregame_cards. The "pre-game report" of R-OS-03 is this card plus the opponent packet.
- two snapshots: the frozen card of the day before, and the snapshot at 900 s before tip with announced starters and availability updates when public. Both are kept; the banner says which one is shown (R-CX-18).
- nothing after the snapshot: every block prints its as-of time. A value dated after the snapshot is never on the card (R-CX-09, R-MR-03).
- mismatch map: predicted before the game. Who did guard whom is the matchup board.
- officials: tendencies only. The card holds no judgement of calls and no "missed call" number.
- no market price is on the card. The market comparison is on the edge report, which only the owner sees (R-MK-24).

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `context` | **official**: source = the schedule and venue registry; as_of = the snapshot time; link = none_fixed<br>**measurement**: unit = kilometres, metres and days; error = none stated: computed from registry coordinates and the schedule; link = none_fixed | contract |  |
| `ratings` | **official**: source = the rating system named in the row; a snapshot that is not point-in-time is marked; as_of = the date of the rating snapshot; link = none_fixed | contract, except<br>**carried**: When the snapshot of the day before is missing, the nearest earlier one is shown, greyed, with its date. |  |
| `availability` | **official**: source = the public report named in the row; as_of = the as-of time of the status; link = none_fixed | contract, except<br>**unknown**: No public report: "no public report". A status is never inferred. | Note: A private note of the owner is shown to the owner alone and is marked private. |
| `officials_crew_sheet` | **estimate**: n = games worked before the snapshot; interval = printed after each tendency; level = 0.95; link = rows; min_n = default<br>**official**: source = the public listing of the crew; as_of = the as-of time of the listing; link = none_fixed | contract, except<br>**unknown**: Crew not announced at the snapshot: "crew not announced" and no tendency. |  |
| `predictions` | **model**: band = the interval beside each value; parameter and simulation uncertainty are named apart; model_version = model family, level and simulation id in the row; link = rows | contract, except<br>**unknown**: Before P6, or when no prediction was frozen for this card: a dash and "no model before P6". |  |
| `prediction_drivers` | **model**: band = printed beside each driver; model_version = in the table foot; link = rows | contract |  |
| `mismatch_map` | **model**: band = the probability of each predicted pairing; model_version = in the table foot; link = rows<br>**measurement**: unit = centimetres, kilograms, metres per second; error = a listed value carries none and says "listed"; a measured speed prints its error and n; link = rows | contract, except<br>**unknown**: A pair with no history and no rule to place it shows a dash and "no basis". |  |
| `mismatch_check` | **measurement**: unit = seconds and percent of matched seconds; error = the seconds unassigned and not seen; link = frames<br>**descriptive**: n = the predicted pairings of the game; descriptive_mark = the word "descriptive" beside the share that came true; link = rows | contract | Note: This block is added after the game and reads what happened. It is not part of the frozen card and never changes it. |
| `snapshot_changes` | **official**: source = the public reports named in each row; as_of = the time of each snapshot; link = none_fixed | contract |  |
| `inspector` | no number | n/a (control) |  |

**Interactions (7)**

| Action | At | Target |
|---|---|---|
| `select` | the view | any value opens the inspector |
| `drill_down` | `availability` | the frozen card of the player → [VW-CARD-01](#vw-card-01-player-card) |
| `drill_down` | `predictions` | the simulation rows behind a prediction |
| `drill_down` | `mismatch_map` | the matchup board of earlier games of the pair → [VW-REV-02](#vw-rev-02-matchup-board) |
| `drill_down` | `ratings` | the opponent packet → [VW-RPT-04](#vw-rpt-04-opponent-scouting-packet) |
| `inspect_query` | `predictions` | the rows and the query with metric ids |
| `export` | the view | the card as a page (produces `page`) |


### VW-CARD-04 Model card

Entry on the catalogue page: [VW-CARD-04](views_catalogue.md#vw-card-04-model-card). What is this model, what was it trained and tested on, how well does it score out of sample, and where does it fail?

**Definitions**

- one card per model version (R-PR-16). Every stored prediction names its model version, and every version resolves to a card.
- frozen: the card is written when the version is registered and prints that date. A correction is a new revision of the card with its own date; the old one stays readable.
- five blocks, always in this order: what it is; data and period; features by metric id; held-out and walk-forward scores; known failures.
- source tags (R-RG-04): a model trained on a research-only or non-commercial source carries that tag on its card and on every output.
- held out: gold sets and the held-out season are named, with the check that no item of them was trained on (R-HR-07).
- editable: nothing.
- an edit creates: nothing. A new model version makes a new card.
- never editable: a score, the data block, the version, the source tags.

**Elements: the rules in full**

| Element | Number rule | Grade rule | Definitions and notes |
|---|---|---|---|
| `as_of_banner` | no number | n/a (control) |  |
| `identity_block` | no number | contract |  |
| `data_block` | **descriptive**: n = games and rows used for training; descriptive_mark = counts of the training data, not estimates; link = rows | contract |  |
| `features_block` | **descriptive**: n = features of the model; descriptive_mark = a list of inputs by id; no value is shown; link = none_fixed | contract | Note: The four ids are examples of features of a play-by-play win-probability model. A card lists the ids of its own model; a vision model lists its input tables instead. |
| `scores_block` | **estimate**: n = held-out cases of the row; interval = printed after each score; level = 0.95; link = rows; min_n = default | contract |  |
| `failures_block` | **descriptive**: n = failed cases per cause; descriptive_mark = counts from the error catalogue, not estimates; link = rows | contract |  |
| `release_block` | no number | contract |  |
| `prediction_count` | **descriptive**: n = stored predictions of this version; descriptive_mark = a count, not an estimate; link = rows | contract |  |

**Interactions (6)**

| Action | At | Target |
|---|---|---|
| `select` | `scores_block` | a score; the rows behind it are listed with the runs that produced them |
| `drill_down` | `scores_block` | this version against another on the bench → [VW-STU-03](#vw-stu-03-model-bench) |
| `drill_down` | `failures_block` | the failed cases of a cause in the run record → [VW-RPT-10](#vw-rpt-10-run-record-and-failure-analysis) |
| `drill_down` | `features_block` | the registry entry of a feature → [VW-STU-09](#vw-stu-09-metric-browser) |
| `inspect_query` | `scores_block` | the rows and the query behind a score |
| `export` | the view | the card as a page; inside the private store until the rights gate clears a public edition (produces `page`) |


## 6. Where every named output lives

Every output named by a requirement or by an owner input, and the view, element, component or contract rule that holds it.

| Output | Requirement | Where it lives |
|---|---|---|
| Video and top-down replay side by side | R-VZ-01 | [VW-REV-01](#vw-rev-01-possession-explorer) element `video` |
| Video and top-down replay in the Studio | R-VZ-01 | [VW-STU-01](#vw-stu-01-studio-game-canvas) element `court` |
| Every number links to its frames | R-VZ-02 | [VW-REV-01](#vw-rev-01-possession-explorer); contract rule `numbers` |
| Every number with n and interval | R-VZ-03 | [VW-REV-01](#vw-rev-01-possession-explorer); contract rule `numbers` |
| Trails, pass arrows, switch marks, value curve | R-VZ-04 | [VW-REV-01](#vw-rev-01-possession-explorer) element `value_curve` |
| Set overlay | R-VZ-05 | [VW-REV-01](#vw-rev-01-possession-explorer) element `set_overlay` |
| Matchup board | R-VZ-06a | [VW-REV-02](#vw-rev-02-matchup-board) |
| Heat maps | R-VZ-06b | [VW-REV-04](#vw-rev-04-heat-maps) |
| Passing network | R-VZ-06c | [VW-REV-05](#vw-rev-05-passing-network) |
| Layered win probability with run shading | R-VZ-06d | [VW-REV-06](#vw-rev-06-layered-win-probability-chart) |
| Filters | R-VZ-06e | [VW-REV-01](#vw-rev-01-possession-explorer) element `filter_bar`; component `filter_bar` |
| Clip export | R-VZ-06f | [VW-REV-01](#vw-rev-01-possession-explorer) element `clip_export`; component `clip_export` |
| Foul tracker | R-VZ-06g | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `foul_tracker` |
| Timeouts left | R-VZ-06h | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `timeouts_left` |
| Shot chart by sector and ring | R-VZ-06i | [VW-REV-07](#vw-rev-07-shot-chart-by-sector-and-ring) |
| Lineup plus-minus with n | R-VZ-06j | [VW-REV-03](#vw-rev-03-lineup-board) element `lineup_plus_minus` |
| One visual standard | R-VZ-07 | [VW-LIVE-01](#vw-live-01-live-game-state-panel); contract rule `visual_standard` |
| Half-time packet | R-VZ-08 | [VW-RPT-01](#vw-rpt-01-half-time-packet) |
| Post-game notes sheet | R-VZ-09 | [VW-RPT-02](#vw-rpt-02-post-game-notes-sheet) |
| Clip index | R-VZ-10 | [VW-REV-01](#vw-rev-01-possession-explorer) element `clip_export`; not a view (`clip_index`) |
| Telestrator freeze-frame | R-VZ-11 | [VW-REV-09](#vw-rev-09-telestrator-freeze-frame) |
| Clip index browser of a game | R-VZ-10 | [VW-RPT-03](#vw-rpt-03-post-game-report) element `clip_browser` |
| One game canvas | R-AS-01 | [VW-STU-01](#vw-stu-01-studio-game-canvas) |
| Inspector | R-AS-02 | [VW-STU-01](#vw-stu-01-studio-game-canvas) element `inspector`; component `inspector` |
| Edits as draft versions | R-AS-03 | [VW-STU-02](#vw-stu-02-draft-diff-and-promote) |
| Live recompute | R-AS-04 | [VW-STU-02](#vw-stu-02-draft-diff-and-promote) |
| Model bench | R-AS-05 | [VW-STU-03](#vw-stu-03-model-bench) |
| Selections become queries | R-AS-06 | [VW-STU-01](#vw-stu-01-studio-game-canvas) element `selection_query`; component `selection_query` |
| Shortcuts and command palette | R-AS-07 | [VW-STU-01](#vw-stu-01-studio-game-canvas) element `command_palette`; component `command_palette` |
| Parameter sensitivity | R-AS-08 | [VW-STU-04](#vw-stu-04-parameter-sensitivity-sweep) |
| Audit and undo | R-AS-09 | [VW-STU-02](#vw-stu-02-draft-diff-and-promote) |
| Private by design | R-AS-10 | [VW-STU-01](#vw-stu-01-studio-game-canvas); contract rule `privacy` |
| Network view | R-AS-11 | [VW-STU-05](#vw-stu-05-network-explain-view) |
| Layers | R-AS-12 | [VW-STU-01](#vw-stu-01-studio-game-canvas) element `layers`; component `layer_toggle` |
| Audit log of edits | R-AS-09 | [VW-STU-02](#vw-stu-02-draft-diff-and-promote) element `audit_log` |
| Recompute status after an edit | R-AS-04 | [VW-STU-02](#vw-stu-02-draft-diff-and-promote) element `recompute_status` |
| Privacy lane (what left the private store) | R-AS-10 | [VW-RPT-11](#vw-rpt-11-monitoring-and-alerts-board) element `privacy_lane` |
| R-PR-14 output: post-game report | R-PR-14 | [VW-RPT-03](#vw-rpt-03-post-game-report) |
| R-PR-14 output: opponent scouting packet | R-PR-14 | [VW-RPT-04](#vw-rpt-04-opponent-scouting-packet) |
| R-PR-14 output: player card | R-PR-14 | [VW-CARD-01](#vw-card-01-player-card) |
| R-PR-14 output: lineup board | R-PR-14 | [VW-REV-03](#vw-rev-03-lineup-board) |
| R-PR-14 output: in-game state panel | R-PR-14 | [VW-LIVE-01](#vw-live-01-live-game-state-panel) |
| R-PR-14 output: pre-game card | R-PR-14 | [VW-CARD-03](#vw-card-03-pre-game-card) |
| Live game state as one panel | R-PR-15 | [VW-LIVE-01](#vw-live-01-live-game-state-panel) |
| Game-state panel at the playhead of a recorded game | R-PR-15 | [VW-STU-01](#vw-stu-01-studio-game-canvas) element `state_panel` |
| Model card | R-PR-16 | [VW-CARD-04](#vw-card-04-model-card) |
| Private review tools as catalogued views | R-PR-18 | [VW-STU-07](#vw-stu-07-review-item-screen) |
| Review queue | R-HR-03, R-HR-04 | [VW-STU-06](#vw-stu-06-review-queue) |
| Review item screen | R-HR-02 | [VW-STU-07](#vw-stu-07-review-item-screen) |
| Turnover review (private tool in use) | R-PR-18 | [VW-STU-07](#vw-stu-07-review-item-screen) element `variant_turnover` |
| Screens tagging (private tool in use) | R-PR-18 | [VW-STU-07](#vw-stu-07-review-item-screen) element `variant_screen` |
| Identity confirm | R-ID-19 | [VW-STU-07](#vw-stu-07-review-item-screen) element `variant_identity` |
| Scoreboard discrepancy | R-SB-01 | [VW-STU-07](#vw-stu-07-review-item-screen) element `variant_scoreboard` |
| Appearance card | R-ID-12 | [VW-STU-07](#vw-stu-07-review-item-screen) element `appearance_card` |
| Consistency re-show (blind) | R-HR-06 | [VW-STU-07](#vw-stu-07-review-item-screen) element `blind_reshow` |
| Label counts per class | R-HR-08 | [VW-STU-06](#vw-stu-06-review-queue) element `label_counts` |
| Learning curve | R-HR-09 | [VW-STU-03](#vw-stu-03-model-bench) element `learning_curve` |
| Labeller agreement | R-HR-06, R-HR-10, R-HR-16 | [VW-RPT-12](#vw-rpt-12-labeller-agreement-report) |
| Gold-set status | R-HR-07, R-HR-12 | [VW-STU-06](#vw-stu-06-review-queue) element `gold_set_status` |
| Live flag feed (what the system is unsure about right now) | R-HR-01 | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `flag_feed` |
| JEV calibration | R-HR-19 | [VW-RPT-14](#vw-rpt-14-jev-calibration-report) |
| Coach quiz | R-GU-03 | [VW-STU-08](#vw-stu-08-coach-quiz) |
| Coach card | R-CC-01 | [VW-CARD-02](#vw-card-02-coach-card) |
| Baseline spot shooting map | R-PC-23 | [VW-CARD-01](#vw-card-01-player-card) element `spot_shooting_map` |
| Officials crew sheet | R-RF-06 | [VW-CARD-03](#vw-card-03-pre-game-card) element `officials_crew_sheet` |
| Pre-game mismatch map | R-MX-06 | [VW-CARD-03](#vw-card-03-pre-game-card) element `mismatch_map` |
| Prediction drivers | R-PR-13 | [VW-CARD-03](#vw-card-03-pre-game-card) element `prediction_drivers` |
| Swing plays list | R-PR-12 | [VW-REV-06](#vw-rev-06-layered-win-probability-chart) element `swing_plays` |
| Live win-probability and leverage strip | R-PR-11, R-PR-12 | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `wp_leverage_strip` |
| Bench board (fouls and stint time of every player) | R-SR-20 | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `bench_board` |
| Live top-down court | R-PR-15 | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `mini_court`; component `top_down_court` |
| Offense breakdown of a game | R-ST-25 | [VW-RPT-03](#vw-rpt-03-post-game-report) element `offense_breakdown` |
| Transition breakdown of a game | R-TR-09 | [VW-RPT-03](#vw-rpt-03-post-game-report) element `transition_breakdown` |
| Defense breakdown of a game | R-DF-14 | [VW-RPT-03](#vw-rpt-03-post-game-report) element `defense_breakdown` |
| Spot game plan against one opponent | R-PC-24 | [VW-RPT-04](#vw-rpt-04-opponent-scouting-packet) element `spot_game_plan` |
| Mismatch check after the game | R-MX-06 | [VW-CARD-03](#vw-card-03-pre-game-card) element `mismatch_check` |
| Physical load views | R-PL-01 | [VW-REV-08](#vw-rev-08-physical-load) |
| Rest-of-season simulation | R-PR-10 | [VW-RPT-16](#vw-rpt-16-rest-of-season-simulation) |
| Crowd loudness curve | R-AU-03 | [VW-STU-01](#vw-stu-01-studio-game-canvas) element `timeline` |
| Edge report and closing-line value | R-MK-05 | [VW-RPT-05](#vw-rpt-05-edge-report-per-market) |
| Calibration and scoring | R-PR-03 | [VW-RPT-06](#vw-rpt-06-calibration-and-scoring-report) |
| Pitch package | R-PT-01 | [VW-RPT-07](#vw-rpt-07-pitch-package) |
| Hypothesis results | R-HY-01 | [VW-RPT-08](#vw-rpt-08-hypothesis-result-table) |
| Run record | R-RR-01 | [VW-RPT-10](#vw-rpt-10-run-record-and-failure-analysis) |
| Lineage | R-EN-19 | [VW-STU-10](#vw-stu-10-lineage-explorer) |
| Data quality per game | R-DQ-07 | [VW-RPT-09](#vw-rpt-09-game-processing-and-data-quality-report) |
| Monitoring and alerts | R-DQ-08 | [VW-RPT-11](#vw-rpt-11-monitoring-and-alerts-board) |
| Play-by-play version diff | R-SY-20 | [VW-RPT-15](#vw-rpt-15-play-by-play-version-diff) |
| Identity quality | R-ID-14 | [VW-RPT-13](#vw-rpt-13-identity-quality-report) |
| Identity confusion list | R-ID-14 | [VW-RPT-13](#vw-rpt-13-identity-quality-report) element `confusion_list` |
| Identity switch log | R-ID-17 | [VW-RPT-13](#vw-rpt-13-identity-quality-report) element `switch_log` |
| Latency per game (reported | R-SY-21 | [VW-RPT-09](#vw-rpt-09-game-processing-and-data-quality-report) element `latency` |
| Invariant-break list | R-IV-40 | [VW-RPT-09](#vw-rpt-09-game-processing-and-data-quality-report) element `invariant_breaks` |
| Live state group: keys and stamps |  | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `as_of_banner` |
| Live state group: time |  | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `clock_period` |
| Live state group: score |  | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `score` |
| Live state group: counts |  | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `foul_tracker` |
| Live state group: possession and ball |  | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `possession_ball` |
| Live state group: personnel |  | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `lineup_identity` |
| Live state group: tactics |  | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `tactics` |
| Live state group: situation |  | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `situation` |
| Live state group: observability |  | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `observability` |
| Live state group: fixed |  | [VW-LIVE-01](#vw-live-01-live-game-state-panel) element `game_header` |
| Stat category TEFF, team efficiency |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category TRAT, team ratings |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category SHOOT, shooting |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category SQ, shot quality |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category PASS, playmaking |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category TOV, turnovers and steals |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category REB, rebounding |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category FOUL, fouls and free throws |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category DEF, defense |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category TRN, transition |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category PLAY, play types |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category SPACE, spacing and off-ball |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category PHYS, physical |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category IMP, impact |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category PROF, player profile |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category SIT, situational |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category COACH, coaching |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category MKT, market |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Stat category TREE, decision trees |  | [VW-STU-09](#vw-stu-09-metric-browser) |
| Owner input: layers from game to player, a tree to walk down |  | [VW-STU-01](#vw-stu-01-studio-game-canvas) element `tree_navigator`; component `tree_navigator` |
| Owner input: the layered tree on the win-probability chart | R-AS-07 | [VW-REV-06](#vw-rev-06-layered-win-probability-chart) element `tree`; component `tree_navigator` |
| Owner input: the layered tree on the post-game report | R-AS-07 | [VW-RPT-03](#vw-rpt-03-post-game-report) element `tree`; component `tree_navigator` |
| Owner input: flag uncertain moments for him to label |  | [VW-STU-06](#vw-stu-06-review-queue) |
| Owner input: court geometry in metres and degrees |  | [VW-REV-01](#vw-rev-01-possession-explorer) element `court`; component `top_down_court` |
| Game-day run book | R-EN-26 | not a view (`game_day_run_book`) |
| Weekly digest | R-RR-09 | not a view (`weekly_digest`) |
| Generated spec pages and stat catalogue pages |  | not a view (`spec_pages`) |
| Views catalogue page | R-PR-17 | not a view (`views_catalogue_page`) |
| Requirements tree |  | not a view (`requirements_tree`) |
| JEV verification packet | R-HR-18 | not a view (`jev_verification_packet`) |
| Labelling guides | R-HR-15 | not a view (`labelling_guides`) |
| Code and data of the private review tools |  | not a view (`private_review_tools_code`) |
| Movement fingerprint profile (goal 9) | R-FP-01 | future view (`movement_fingerprint_profile`) |

## 7. Metrics the views read

By registry id (`config/metrics.yaml`). A view lists ids and never a formula.

| Metric | Name in the registry | Views |
|---|---|---|
| `M-COACH-001` | Timeouts used (by type, length and caller) | VW-CARD-02, VW-RPT-01, VW-STU-09 |
| `M-COACH-002` | Timeouts remaining (state) and at key checkpoints | VW-LIVE-01, VW-RPT-01 |
| `M-COACH-003` | Unused timeouts at game end and timeouts lost at halftime carry-over | VW-RPT-01 |
| `M-COACH-010` | Opponent run size at timeout and coach response threshold | VW-CARD-02 |
| `M-COACH-011` | Timeout lag after an opponent run reaches its threshold | VW-CARD-02 |
| `M-COACH-012` | Share of timeouts called during an opponent run | VW-CARD-02, VW-RPT-01 |
| `M-COACH-015` | After-timeout (ATO) offensive efficiency | VW-CARD-02, VW-RPT-03 |
| `M-COACH-016` | After-timeout defensive efficiency and ATO net | VW-CARD-02 |
| `M-COACH-024` | Timeout-during-run causal effect (matched ATT on integrated score difference) | VW-CARD-02 |
| `M-COACH-030` | Timeout-followed-by-scheme-change rate | VW-CARD-02 |
| `M-COACH-032` | Challenge success rate (overall and by call type) | VW-CARD-02 |
| `M-COACH-037` | Substitutions per game and substitution timing | VW-CARD-02 |
| `M-COACH-040` | Distinct lineups used and starting-five minutes | VW-REV-03 |
| `M-COACH-041` | Bench minutes share | VW-RPT-04 |
| `M-COACH-042` | Bench points and bench points share | VW-RPT-04 |
| `M-COACH-043` | Rotation size: players used, core rotation and bench utilisation | VW-CARD-02, VW-REV-03 |
| `M-COACH-044` | Playing-time concentration (HHI, effective rotation size, minutes entropy) | VW-CARD-02 |
| `M-COACH-046` | Player pull rate after a mistake (vs substitution hazard baseline) | VW-CARD-02 |
| `M-COACH-050` | Foul-trouble benching rate and two-foul first-half participation | VW-CARD-02 |
| `M-COACH-052` | Starters on the floor not in foul trouble | VW-LIVE-01 |
| `M-COACH-053` | Foul-trouble decision log outcomes | VW-CARD-02 |
| `M-COACH-054` | Two-for-one opportunity and window flag | VW-LIVE-01 |
| `M-COACH-055` | Two-for-one attempt rate and execution | VW-CARD-02 |
| `M-COACH-059` | Fouls to give and their use at end of half | VW-CARD-02 |
| `M-COACH-060` | Foul-up-3 decision, rate and outcome | VW-CARD-02 |
| `M-COACH-066` | End-game decision regret (win probability lost vs model-best action) | VW-CARD-02 |
| `M-COACH-069` | Play-call mix and diversity (set-family shares and entropy) | VW-CARD-02 |
| `M-COACH-070` | Counter usage rate | VW-CARD-02 |
| `M-COACH-075` | Scheme-change lag, adjustment latency and 'not working' PPP | VW-CARD-02 |
| `M-COACH-077` | Half-time adjustment | VW-CARD-02 |
| `M-COACH-078` | Reaction catalogue latency and rate | VW-CARD-02 |
| `M-COACH-081` | Coach experience (head-coach and any-role seasons) | VW-CARD-02 |
| `M-COACH-091` | Head-coach overall win-loss record (career, current school, current season) | VW-CARD-02 |
| `M-COACH-092` | Head-coach conference win-loss record (regular-season conference games; conference tournament separate) | VW-CARD-02 |
| `M-COACH-094` | Head-to-head record vs a specific opposing head coach | VW-CARD-02, VW-RPT-04 |
| `M-COACH-095` | Seasons at current school (tenure length and season number) | VW-CARD-02 |
| `M-DEF-001` | Opponent points per game (scoring defense) | VW-STU-09 |
| `M-DEF-002` | Defensive points per possession (raw, un-adjusted) | VW-RPT-03 |
| `M-DEF-006` | Opponent effective field-goal percentage (eFG% defense) | VW-RPT-03, VW-RPT-04 |
| `M-DEF-008` | Opponent three-point attempt rate allowed | VW-RPT-04 |
| `M-DEF-009` | Opponent rim attempt rate allowed | VW-RPT-04 |
| `M-DEF-010` | Opponent rim field-goal percentage allowed (team) | VW-RPT-04 |
| `M-DEF-020` | Block percentage | VW-CARD-01 |
| `M-DEF-034` | Contest rate | VW-RPT-03 |
| `M-DEF-038` | Closeout distance and speed | VW-RPT-03 |
| `M-DEF-044` | Defended field-goal percentage (DFG%) | VW-REV-02, VW-RPT-04 |
| `M-DEF-046` | DFG% difference vs shooter normal (DIFF%) | VW-REV-02 |
| `M-DEF-047` | Rim defended field-goal percentage | VW-CARD-01 |
| `M-DEF-048` | Rim deterrence (rim attempts deterred) | VW-CARD-01 |
| `M-DEF-052` | Matchup assignment probability | VW-REV-02 |
| `M-DEF-056` | Defensive matchup entropy (player) | VW-REV-02 |
| `M-DEF-058` | Matchup persistence (rho) | VW-REV-02 |
| `M-DEF-059` | Assignment confusion seconds | VW-REV-02 |
| `M-DEF-060` | Matchup time and share | VW-CARD-03, VW-REV-02, VW-RPT-07 |
| `M-DEF-061` | Matchup box outcomes | VW-REV-02 |
| `M-DEF-062` | Counterpoints (points allowed per 100 matched possessions) | VW-REV-02 |
| `M-DEF-063` | Matchup points allowed (shrunk) and expected matchup PPP | VW-CARD-03, VW-REV-02 |
| `M-DEF-065` | Player and team points difference in matchup | VW-REV-02 |
| `M-DEF-068` | Matchup difficulty | VW-CARD-03 |
| `M-DEF-069` | Defensive versatility index | VW-CARD-01 |
| `M-DEF-070` | Mismatch hunting share (targeted defender) | VW-REV-02 |
| `M-DEF-071` | Defensive switches | VW-REV-01, VW-REV-02 |
| `M-DEF-072` | Switch mismatch size and exposure | VW-CARD-03, VW-REV-01, VW-REV-02 |
| `M-DEF-091` | Help arrival time on drives | VW-RPT-03 |
| `M-DEF-097` | Rotation failure (open shot after rotation) rate | VW-RPT-03 |
| `M-DEF-102` | Ball-screen coverage mix | VW-RPT-01, VW-RPT-02, VW-RPT-03, VW-RPT-04, VW-RPT-07 |
| `M-DEF-103` | Ball-screen coverage outcome (points per chance and points per screen) | VW-RPT-02, VW-RPT-03 |
| `M-DEF-104` | Drop depth | VW-RPT-03 |
| `M-DEF-110` | Defensive scheme mix | VW-RPT-01, VW-RPT-03, VW-RPT-04 |
| `M-DEF-111` | PPP allowed by defensive scheme | VW-RPT-03, VW-RPT-04 |
| `M-DEF-112` | Press usage and outcome | VW-RPT-03, VW-RPT-04 |
| `M-DEF-113` | Scheme-change lag and effect | VW-CARD-02, VW-RPT-03 |
| `M-DEF-128` | Defensive value credits | VW-REV-02 |
| `M-DEF-132` | Zone-family split: frequency and PPP allowed by named zone | VW-RPT-04 |
| `M-FOUL-001` | Personal fouls committed | VW-LIVE-01, VW-RPT-01, VW-RPT-15, VW-STU-09 |
| `M-FOUL-003` | Fouls per 100 defensive possessions (Foul%) | VW-CARD-01, VW-RPT-02, VW-RPT-03, VW-RPT-04 |
| `M-FOUL-010` | Team fouls in the half | VW-LIVE-01, VW-RPT-01 |
| `M-FOUL-011` | Bonus state | VW-LIVE-01, VW-RPT-01 |
| `M-FOUL-012` | Fouls to give | VW-LIVE-01 |
| `M-FOUL-013` | Clock at bonus entry (one-and-one) | VW-RPT-01 |
| `M-FOUL-014` | Clock at double-bonus entry | VW-RPT-01 |
| `M-FOUL-047` | Disqualifications (foul-outs) | VW-LIVE-01 |
| `M-FOUL-065` | Free-throw percentage | VW-RPT-03, VW-RPT-04 |
| `M-FOUL-066` | Projected (shrunk) free-throw percentage | VW-CARD-01 |
| `M-FOUL-067` | Lineup projected free-throw percentage | VW-REV-03 |
| `M-FOUL-114` | Foul-trouble flag | VW-LIVE-01, VW-RPT-01 |
| `M-FOUL-115` | Minutes lost to foul trouble | VW-CARD-02, VW-RPT-01 |
| `M-FOUL-121` | Game officials and crew chief | VW-CARD-03 |
| `M-FOUL-122` | Official games worked | VW-CARD-03 |
| `M-FOUL-123` | Crew fouls per 40 minutes / per 100 possessions | VW-CARD-03 |
| `M-FOUL-124` | Crew free-throw rate (FTA per 40, FTA/FGA) | VW-CARD-03 |
| `M-FOUL-125` | Crew away-minus-home foul split | VW-CARD-03 |
| `M-FOUL-126` | Official fouls above average (FAA) | VW-CARD-03 |
| `M-FOUL-128` | Crew effect on totals | VW-CARD-03 |
| `M-FOUL-130` | Official metric percentile | VW-CARD-03 |
| `M-IMP-001` | Raw plus-minus (on-court point differential) | VW-REV-03, VW-RPT-03, VW-STU-09 |
| `M-IMP-002` | On-court team ratings (offensive, defensive, net rating with player on floor) | VW-CARD-01, VW-REV-03 |
| `M-IMP-003` | On/off differential (net, offense, defense) | VW-CARD-01, VW-REV-03 |
| `M-IMP-006` | Garbage-time filter for impact stats | VW-REV-03, VW-STU-04 |
| `M-IMP-007` | With-or-without-you (WOWY) splits | VW-REV-03 |
| `M-IMP-008` | Lineup stint (base unit) and 10-player matchup stint | VW-REV-03 |
| `M-IMP-009` | Lineup plus-minus | VW-REV-03 |
| `M-IMP-010` | Lineup raw efficiency (offensive, defensive, net) for k-man groups | VW-REV-03 |
| `M-IMP-014` | Lineup composition profile | VW-REV-03 |
| `M-IMP-015` | Starters vs bench unit split | VW-REV-03 |
| `M-IMP-016` | Lineup and pair RAPM with informed priors | VW-REV-03 |
| `M-IMP-017` | Teammate chemistry and weighted chemistry | VW-REV-03 |
| `M-IMP-019` | Regularized adjusted plus-minus (RAPM) | VW-REV-03 |
| `M-IMP-044` | Game Score (Hollinger) | VW-RPT-03 |
| `M-IMP-062` | Player win probability added (WPA) and leverage-neutral wins | VW-REV-06 |
| `M-IMP-063` | Expected possession value (EPV) per instant | VW-REV-01, VW-REV-04, VW-RPT-01, VW-STU-01, VW-STU-02 |
| `M-IMP-065` | Per-frame and per-action value credit (total value added) | VW-REV-01, VW-REV-04, VW-RPT-01, VW-RPT-02, VW-RPT-03, VW-RPT-07 |
| `M-IMP-066` | Off-ball value added | VW-REV-01 |
| `M-IMP-067` | Screen value added | VW-REV-01 |
| `M-MKT-001` | Implied probability (raw, with margin) | VW-RPT-05, VW-STU-09 |
| `M-MKT-015` | Fair probability, power method (with exponent k) | VW-RPT-05 |
| `M-MKT-016` | Fair probability, Shin method (with insider share z) | VW-RPT-05 |
| `M-MKT-021` | Fair probability conditional on no push (integer lines) | VW-RPT-05 |
| `M-MKT-022` | Consensus fair probability (cross-book median) | VW-RPT-05 |
| `M-MKT-023` | Point spread (line) | VW-RPT-05 |
| `M-MKT-024` | Moneyline price | VW-RPT-05 |
| `M-MKT-025` | Game total (over/under line) | VW-RPT-05 |
| `M-MKT-026` | Opening line | VW-RPT-05 |
| `M-MKT-027` | Closing line | VW-RPT-05 |
| `M-MKT-033` | Line movement (open to close, per step) | VW-RPT-05 |
| `M-MKT-043` | Exchange midpoint | VW-RPT-05 |
| `M-MKT-044` | Exchange bid-ask spread (and bid-ask overround) | VW-RPT-05 |
| `M-MKT-049` | Exchange-implied live win probability | VW-RPT-05 |
| `M-MKT-055` | Market completeness rate | VW-RPT-05, VW-RPT-11 |
| `M-MKT-060` | Cover indicator (ATS result) and push | VW-RPT-05 |
| `M-MKT-061` | Against-the-spread (ATS) margin | VW-RPT-05 |
| `M-MKT-063` | Over/under result and total margin | VW-RPT-05 |
| `M-MKT-067` | Edge (model minus market fair probability) | VW-RPT-05 |
| `M-MKT-069` | Expected value per unit stake | VW-RPT-05 |
| `M-MKT-070` | Closing-line value (probability points) | VW-RPT-05, VW-RPT-07 |
| `M-MKT-071` | CLV percent (EV at closing fair probability) | VW-RPT-05 |
| `M-MKT-072` | CLV relative percent | VW-RPT-05 |
| `M-MKT-073` | CLV in line points | VW-RPT-05 |
| `M-MKT-074` | CLV in cents | VW-RPT-05 |
| `M-MKT-076` | Kelly fraction (and edge condition) | VW-RPT-05 |
| `M-MKT-078` | Betting units gained, return on investment (yield) | VW-RPT-05 |
| `M-MKT-079` | Graded win rate (bets) | VW-RPT-05 |
| `M-MKT-080` | Maximum drawdown (paper bankroll) | VW-RPT-05 |
| `M-MKT-081` | Sharpe ratio of paper betting returns | VW-RPT-05 |
| `M-MKT-085` | Market vs model in-game win-probability divergence | VW-RPT-05 |
| `M-MKT-087` | Log loss | VW-CARD-04, VW-RPT-05, VW-RPT-06, VW-RPT-07 |
| `M-MKT-088` | Brier score | VW-CARD-04, VW-RPT-06, VW-RPT-07 |
| `M-MKT-089` | Brier decomposition (reliability, resolution, uncertainty) | VW-RPT-06 |
| `M-MKT-090` | Brier skill score | VW-RPT-06, VW-RPT-07 |
| `M-MKT-091` | Expected calibration error (ECE) | VW-CARD-04, VW-RPT-06, VW-RPT-07, VW-RPT-11 |
| `M-MKT-092` | Maximum calibration error (MCE) | VW-RPT-06 |
| `M-MKT-093` | Platt scaling / calibration slope and intercept | VW-RPT-06 |
| `M-MKT-094` | Ranked probability score (RPS) | VW-RPT-06 |
| `M-MKT-095` | Continuous ranked probability score (CRPS) | VW-RPT-06 |
| `M-MKT-096` | Probability integral transform (PIT) uniformity | VW-RPT-06 |
| `M-MKT-097` | Real-time Brier curve (loss over game time) | VW-RPT-06 |
| `M-MKT-098` | Real-time skill difference (functional test) | VW-RPT-06 |
| `M-MKT-099` | Spread prediction MAE | VW-RPT-06 |
| `M-MKT-100` | Spread prediction RMSE | VW-RPT-06 |
| `M-MKT-102` | Home bias of predictions | VW-RPT-06 |
| `M-MKT-112` | NIL value estimate (player labour market) | VW-CARD-01 |
| `M-PASS-001` | Assists | VW-REV-05, VW-RPT-15, VW-STU-09 |
| `M-PASS-002` | Assist percentage (player AST%) | VW-CARD-01, VW-REV-05 |
| `M-PASS-021` | Passes made | VW-REV-05 |
| `M-PASS-022` | Passes received | VW-REV-05 |
| `M-PASS-023` | Pass matrix (passes from player a to player b) | VW-REV-05 |
| `M-PASS-024` | Pass completion rate | VW-REV-05 |
| `M-PASS-025` | Potential assists | VW-REV-05 |
| `M-PASS-026` | Assist-to-pass percentage | VW-REV-05 |
| `M-PASS-027` | Secondary assists (hockey assists) | VW-REV-05 |
| `M-PASS-030` | Screen assists | VW-STU-04 |
| `M-PASS-039` | Pass value added | VW-REV-01, VW-REV-05 |
| `M-PASS-040` | Expected assists (expected points after a pass) | VW-REV-05 |
| `M-PASS-041` | EPV-Added (ball-handler value added) | VW-REV-01 |
| `M-PASS-045` | Decision latency (catch to first action) | VW-CARD-01 |
| `M-PASS-050` | Pass-or-shoot tendency by zone | VW-CARD-01, VW-REV-04 |
| `M-PASS-052` | Video vs official assist gap | VW-REV-05 |
| `M-PASS-053` | Touches | VW-REV-04, VW-REV-05 |
| `M-PASS-058` | Elbow touches | VW-REV-04 |
| `M-PASS-059` | Post touches | VW-REV-04 |
| `M-PASS-060` | Paint touches | VW-REV-04 |
| `M-PASS-068` | Drives | VW-REV-04 |
| `M-PASS-073` | Assist network edge weight | VW-REV-05 |
| `M-PASS-074` | Assist and shot frequency, involvement (ncaahoopR) | VW-REV-05 |
| `M-PASS-075` | Passing network degree centrality | VW-REV-05 |
| `M-PASS-076` | Passing network betweenness and closeness centrality | VW-REV-05 |
| `M-PASS-077` | Passing network PageRank, eigenvector, hub and authority scores | VW-REV-05 |
| `M-PASS-078` | Passing network clustering coefficient | VW-REV-05 |
| `M-PASS-080` | Ball-movement entropy (player and team) | VW-REV-05 |
| `M-PASS-083` | Assist balance and point balance | VW-REV-05 |
| `M-PASS-085` | Matchup assists and potential assists allowed | VW-REV-02 |
| `M-PASS-086` | Lineup assist capacity (sum of member shrunk AST% priors, ours) | VW-REV-03 |
| `M-PHYS-001` | Court-plane kinematics per frame (speed, velocity, heading, acceleration) with propagated sigma | VW-STU-09 |
| `M-PHYS-003` | Tracking coverage share for load (observed on-court time) | VW-REV-04, VW-REV-08 |
| `M-PHYS-006` | Minutes played and games (official) | VW-REV-08 |
| `M-PHYS-009` | Continuous minutes on court at an instant (fatigue clock) | VW-LIVE-01, VW-REV-08 |
| `M-PHYS-018` | Total distance | VW-REV-08 |
| `M-PHYS-020` | Relative distance (distance per minute) with three denominators | VW-REV-08 |
| `M-PHYS-021` | Distance per possession | VW-REV-08 |
| `M-PHYS-022` | Speed-bin histogram (time and distance per 0.1 m/s bin) | VW-REV-08 |
| `M-PHYS-023` | Distance and time in MSU primary speed bands | VW-REV-08 |
| `M-PHYS-025` | High-speed running distance and time | VW-REV-08 |
| `M-PHYS-026` | Sprint distance | VW-REV-08 |
| `M-PHYS-027` | Relative (individualised) speed bands | VW-REV-08 |
| `M-PHYS-028` | Average speed (overall, offense, defense) | VW-REV-08 |
| `M-PHYS-029` | Top speed, robust (95th percentile of 1-s smoothed speed) | VW-CARD-03, VW-REV-08 |
| `M-PHYS-031` | Match reference speed (v_ref) | VW-REV-08 |
| `M-PHYS-033` | High-speed efforts (runs, HI runs, HSR efforts) | VW-REV-08 |
| `M-PHYS-034` | Sprint count (efforts) | VW-REV-08 |
| `M-PHYS-037` | Rolling 5-second distance | VW-REV-08 |
| `M-PHYS-042` | Acceleration and deceleration efforts (position-derived, banded) | VW-REV-08 |
| `M-PHYS-043` | Acceleration effort attributes (peak, duration, start speed) | VW-REV-08 |
| `M-PHYS-084` | Within-game decline of top speed and acceleration | VW-REV-08 |
| `M-PHYS-091` | Team average height (minutes-weighted) | VW-REV-03 |
| `M-PLAY-001` | Play-type possession (Synergy-style scoring chance) | VW-STU-09 |
| `M-PLAY-003` | Transition possessions, frequency and PPP | VW-RPT-03 |
| `M-PLAY-004` | Pick-and-roll ball handler possessions, frequency and PPP | VW-RPT-03 |
| `M-PLAY-014` | Play-type frequency (%Time) | VW-RPT-03, VW-RPT-04 |
| `M-PLAY-015` | Play-type points per possession (PPP) | VW-RPT-03, VW-RPT-04 |
| `M-PLAY-029` | Play-type mix diversity | VW-RPT-04 |
| `M-PLAY-049` | Ball-screen outcome PPP by coverage faced | VW-RPT-03 |
| `M-PLAY-060` | Set frequency and points per chance (PPC_set) | VW-RPT-01, VW-RPT-02, VW-RPT-03, VW-RPT-04 |
| `M-PLAY-063` | Set completion and counter rate | VW-RPT-03 |
| `M-PLAY-065` | Mismatch hunting rate and PPP | VW-REV-02 |
| `M-PLAY-066` | After-timeout (ATO) possession PPP and frequency | VW-CARD-02, VW-RPT-03 |
| `M-PROF-001` | Games played (GP) | VW-CARD-01, VW-STU-09 |
| `M-PROF-002` | Games started and start rate | VW-CARD-01 |
| `M-PROF-003` | Did-not-play flag, games missed and availability rate | VW-CARD-01, VW-CARD-03 |
| `M-PROF-004` | Minutes played (MP) and minutes per game | VW-RPT-03 |
| `M-PROF-005` | Minutes share (Min%, percentage of possible minutes) | VW-CARD-01 |
| `M-PROF-009` | Per-100 possessions rate | VW-CARD-01 |
| `M-PROF-013` | Usage rate (USG%, possessions used while on court) | VW-CARD-01, VW-RPT-03 |
| `M-PROF-020` | D-I population percentile | VW-CARD-01 |
| `M-PROF-021` | Listed position | VW-CARD-01 |
| `M-PROF-024` | Position minutes distribution (share of minutes at PG/SG/SF/PF/C) | VW-CARD-01 |
| `M-PROF-027` | Tracked floor-position profile (listed vs played position) | VW-REV-04 |
| `M-PROF-037` | Role cluster soft membership (ours) | VW-CARD-01 |
| `M-PROF-040` | Decision-style vector (first action after the catch) | VW-CARD-01 |
| `M-PROF-042` | Shooting hand | VW-CARD-01 |
| `M-PROF-043` | Drive hand / direction bias | VW-CARD-01 |
| `M-PROF-045` | Lineup composition descriptors | VW-REV-03 |
| `M-PROF-047` | Bench minutes share and bench production (team) | VW-REV-03 |
| `M-PROF-048` | Rotation depth and minutes concentration (team) | VW-REV-03 |
| `M-PROF-049` | Rotation tier and minutes rank | VW-CARD-01 |
| `M-PROF-058` | Defensive assignment versatility | VW-CARD-01 |
| `M-PROF-059` | Age | VW-CARD-01 |
| `M-PROF-061` | Class year and eligibility | VW-CARD-01 |
| `M-PROF-063` | Career D-I exposure and seasons in program | VW-CARD-01 |
| `M-PROF-070` | Split-half reliability and n70 | VW-CARD-01 |
| `M-PROF-074` | Recruit rating and rank (player) | VW-CARD-01 |
| `M-PROF-076` | Transfer history | VW-CARD-01 |
| `M-REB-001` | Offensive rebounds (ORB) | VW-RPT-15, VW-STU-09 |
| `M-REB-007` | Offensive rebound percentage (team) | VW-RPT-03, VW-RPT-04 |
| `M-REB-008` | Defensive rebound percentage (team) | VW-RPT-03 |
| `M-REB-010` | Player offensive rebound percentage | VW-CARD-01 |
| `M-REB-011` | Player defensive rebound percentage | VW-CARD-01 |
| `M-REB-024` | Second-chance points | VW-RPT-02, VW-RPT-03 |
| `M-SHOOT-001` | Shot attempt outcome (event atom) | VW-STU-09 |
| `M-SHOOT-011` | Effective field goal percentage (eFG%) | VW-CARD-01, VW-REV-07, VW-RPT-03 |
| `M-SHOOT-012` | True shooting percentage (TS%) | VW-CARD-01, VW-RPT-03 |
| `M-SHOOT-017` | Scoring rate per 100 possessions | VW-CARD-01 |
| `M-SHOOT-021` | Shooting skill posterior by zone and context (beta-binomial) | VW-CARD-01, VW-REV-07, VW-RPT-04 |
| `M-SHOOT-022` | Make rate by 15-degree sector and 0.5 m ring (shrunk) | VW-CARD-01, VW-REV-07, VW-RPT-04 |
| `M-SHOOT-023` | Spatial shooting surface (LGCP intensity, propensity and skill) | VW-REV-04 |
| `M-SHOOT-024` | Rim field-goal percentage | VW-REV-07 |
| `M-SHOOT-025` | Mid-range field-goal percentage | VW-REV-07 |
| `M-SHOOT-026` | Corner and above-the-break three-point percentage | VW-REV-07 |
| `M-SHOOT-027` | Shooting accuracy and frequency by zone (zone splits) | VW-REV-04, VW-REV-07 |
| `M-SHOOT-040` | Shot-making over expected (points and FG% above shot-quality expectation) | VW-REV-07 |
| `M-SHOOT-069` | Rim finishing by hand (left / right / two-hand) | VW-CARD-01 |
| `M-SIT-001` | Game clock state and time remaining | VW-CARD-04, VW-STU-09 |
| `M-SIT-002` | Score margin (score state) | VW-CARD-04 |
| `M-SIT-004` | Game-segment splits (half, extra period, media segment, 5-min window, last 240 s) | VW-REV-06, VW-RPT-03 |
| `M-SIT-005` | Segment margin vs random-walk baseline | VW-REV-06, VW-RPT-06 |
| `M-SIT-006` | Clutch flag (single config definition plus filter family) | VW-LIVE-01, VW-STU-04 |
| `M-SIT-015` | Largest lead | VW-LIVE-01, VW-REV-06, VW-RPT-01 |
| `M-SIT-017` | Lead changes and times tied | VW-LIVE-01, VW-REV-06, VW-RPT-01 |
| `M-SIT-018` | Percent of game led, tied and trailed | VW-REV-06 |
| `M-SIT-019` | Time-weighted average margin (GameScript) | VW-REV-06 |
| `M-SIT-023` | Run: unanswered points | VW-LIVE-01, VW-REV-06, VW-RPT-01 |
| `M-SIT-024` | Run: broadcast a-b | VW-LIVE-01, VW-REV-06, VW-RPT-01 |
| `M-SIT-025` | Run: register (net >= 8 in 120 s) | VW-LIVE-01, VW-REV-06, VW-RPT-01, VW-RPT-02 |
| `M-SIT-039` | After-timeout (ATO) efficiency | VW-RPT-02, VW-RPT-03 |
| `M-SIT-040` | Timeout effect on an opponent run (matched causal estimate) | VW-CARD-02 |
| `M-SIT-043` | Efficiency by shot-clock band | VW-RPT-04 |
| `M-SIT-052` | Garbage-time flag (three side-by-side definitions) and share | VW-LIVE-01, VW-REV-06, VW-STU-04 |
| `M-SIT-055` | In-game win probability | VW-LIVE-01, VW-REV-06, VW-STU-02, VW-STU-04 |
| `M-SIT-058` | Win probability added (WPA) per event, player and team | VW-LIVE-01, VW-REV-06 |
| `M-SIT-059` | Swing-play count | VW-LIVE-01, VW-REV-06 |
| `M-SIT-060` | Leverage index (possession and frame) | VW-LIVE-01, VW-REV-06 |
| `M-SIT-063` | Leverage-weighted PPP | VW-REV-06 |
| `M-SIT-072` | Time-weighted average win probability | VW-REV-06 |
| `M-SIT-073` | Minimum win probability of the winner and comeback factor | VW-REV-06 |
| `M-SIT-076` | Surprise per event | VW-REV-06 |
| `M-SIT-082` | Rest, travel and schedule position | VW-CARD-03 |
| `M-SIT-083` | Venue geography: altitude difference and neutral-site proximity | VW-CARD-03 |
| `M-SIT-086` | Mismatch possessions | VW-REV-02 |
| `M-SIT-092` | Rest and schedule-load differential (rest advantage) | VW-CARD-03 |
| `M-SIT-094` | Rivalry game flag | VW-CARD-03 |
| `M-SIT-099` | Schedule-spot profile and splits | VW-CARD-03 |
| `M-SPACE-001` | Offensive spacing (mean pairwise distance) | VW-STU-01, VW-STU-09 |
| `M-SPACE-002` | Offensive convex hull area | VW-STU-01 |
| `M-SPACE-014` | Corner occupancy rate | VW-REV-04 |
| `M-SPACE-016` | Same-spot occupancy seconds | VW-REV-04 |
| `M-SPACE-038` | Shooting gravity surface | VW-REV-04 |
| `M-SPACE-045` | Cut value added | VW-REV-01 |
| `M-SQ-001` | Shot release location (x, y, r, theta) | VW-REV-04, VW-REV-07, VW-STU-09 |
| `M-SQ-002` | Shot distance | VW-REV-07 |
| `M-SQ-004` | Shot zone (canonical scheme with source schemes as variants) | VW-REV-04, VW-REV-07 |
| `M-SQ-005` | Sector x ring cell (15 degree x 0.5 m) | VW-REV-04, VW-REV-07 |
| `M-SQ-006` | Distance-band shot distribution and accuracy | VW-REV-07 |
| `M-SQ-007` | Heave flag and heave counts | VW-REV-07 |
| `M-SQ-008` | Shot-location source disagreement | VW-REV-04, VW-RPT-09 |
| `M-SQ-010` | Three-point attempt rate | VW-REV-07, VW-RPT-04 |
| `M-SQ-011` | Rim attempt rate | VW-REV-07, VW-RPT-04 |
| `M-SQ-012` | Mid-range attempt rate | VW-REV-07, VW-RPT-04 |
| `M-SQ-014` | Corner three rate | VW-REV-07 |
| `M-SQ-022` | Shot-clock-at-release distribution and efficiency | VW-CARD-01 |
| `M-SQ-023` | Shot creation: assisted and unassisted share by zone | VW-REV-07 |
| `M-SQ-024` | Points in the paint | VW-RPT-03 |
| `M-SQ-046` | Shrunk make rate by sector, ring and shot context | VW-CARD-01, VW-REV-07, VW-RPT-04 |
| `M-SQ-047` | Spatial shooting effectiveness and Range% | VW-RPT-04 |
| `M-SQ-052` | Contested / open shot rate and split efficiency | VW-REV-07 |
| `M-SQ-060` | Shooter-agnostic expected FG% (xFG) | VW-REV-07 |
| `M-SQ-061` | Shooter-agnostic expected points per shot (xPts) | VW-REV-07 |
| `M-SQ-063` | Average shot quality (mean xPts or xeFG per FGA) | VW-REV-07, VW-RPT-02 |
| `M-SQ-066` | Shot-making residual (points above expected) | VW-REV-07, VW-RPT-02 |
| `M-TEFF-001` | Possessions (counted, our definition) | VW-CARD-04, VW-RPT-03, VW-RPT-09, VW-STU-02, VW-STU-04, VW-STU-09 |
| `M-TEFF-002` | Box-score possession estimate (single team) | VW-RPT-09, VW-STU-04, VW-STU-09 |
| `M-TEFF-003` | Two-team averaged possession estimate (game possessions) | VW-RPT-01 |
| `M-TEFF-004` | Possession-count discrepancy by source definition | VW-RPT-03 |
| `M-TEFF-010` | Tempo / pace (raw possessions per 40 minutes) | VW-RPT-04 |
| `M-TEFF-011` | Adjusted tempo | VW-CARD-03 |
| `M-TEFF-013` | Average possession length | VW-REV-01 |
| `M-TEFF-015` | Expected game possessions (pre-game tempo projection) | VW-CARD-03 |
| `M-TEFF-018` | Offensive efficiency (points per possession / offensive rating) | VW-RPT-01, VW-RPT-02, VW-RPT-03, VW-RPT-04, VW-RPT-07 |
| `M-TEFF-019` | Defensive efficiency (points allowed per possession / defensive rating) | VW-RPT-03, VW-RPT-04 |
| `M-TEFF-020` | Net rating (raw efficiency margin) | VW-RPT-03 |
| `M-TEFF-024` | Expected points per possession (model value) | VW-LIVE-01, VW-REV-01, VW-RPT-03 |
| `M-TEFF-028` | Four factors: effective field-goal percentage (team, offense and defense) | VW-RPT-01, VW-RPT-02, VW-RPT-03, VW-RPT-04 |
| `M-TEFF-029` | Four factors: turnover rate (team, offense and defense) | VW-RPT-01, VW-RPT-02, VW-RPT-03, VW-RPT-04 |
| `M-TEFF-030` | Four factors: offensive and defensive rebound rate (team) | VW-RPT-01, VW-RPT-02, VW-RPT-03, VW-RPT-04 |
| `M-TEFF-031` | Four factors: free-throw rate (team, offense and defense) | VW-RPT-01, VW-RPT-02, VW-RPT-03, VW-RPT-04 |
| `M-TEFF-035` | Adjusted offensive efficiency | VW-CARD-03, VW-RPT-04 |
| `M-TEFF-036` | Adjusted defensive efficiency | VW-CARD-03, VW-RPT-04 |
| `M-TEFF-038` | Expected game efficiency and score (pre-game projection) | VW-CARD-03 |
| `M-TEFF-039` | On-court team efficiency (player and lineup) | VW-REV-03 |
| `M-TEFF-040` | Individual offensive rating (Oliver points produced) | VW-CARD-01 |
| `M-TEFF-045` | Usable-possession share | VW-RPT-02, VW-RPT-03, VW-RPT-07, VW-RPT-09, VW-STU-04 |
| `M-TEFF-048` | Per-100-possession rate conversion | VW-REV-03 |
| `M-TEFF-052` | Four-factor differentials (team minus opponent, per game and per season) | VW-RPT-03, VW-RPT-04 |
| `M-TEFF-053` | Four factors won (count per game) and factors-won versus win rate | VW-RPT-03 |
| `M-TOV-001` | Turnovers | VW-RPT-15, VW-STU-07, VW-STU-09 |
| `M-TOV-002` | Team turnovers (not charged to a player) | VW-STU-07 |
| `M-TOV-006` | Turnover percentage (team, per possession) | VW-RPT-03, VW-RPT-04 |
| `M-TOV-009` | Player turnover rate (per used possession) | VW-CARD-01, VW-REV-05 |
| `M-TOV-010` | Opponent turnover percentage (forced turnover rate) | VW-RPT-04 |
| `M-TOV-012` | Steal percentage (per opponent possession) | VW-CARD-01 |
| `M-TOV-016` | Live-ball and dead-ball turnovers (counts, rates, share) | VW-RPT-02 |
| `M-TOV-021` | Opponent points off turnovers | VW-RPT-02, VW-RPT-03 |
| `M-TOV-023` | Turnover cost (expected points) | VW-REV-01 |
| `M-TRAT-001` | Adjusted efficiency margin (AdjEM) | VW-CARD-03, VW-CARD-04, VW-RPT-04, VW-STU-09 |
| `M-TRAT-002` | Rating rank, percentile and z-score (any system, any component) | VW-CARD-03, VW-RPT-04 |
| `M-TRAT-004` | MSU Alpha opponent-adjusted team rating (our replica, dissectable) | VW-CARD-03 |
| `M-TRAT-013` | Availability-adjusted team rating (injury / ineligibility adjustment) | VW-CARD-03, VW-RPT-16 |
| `M-TRAT-015` | Rating and rank change over time (trend) | VW-RPT-16 |
| `M-TRAT-031` | Remaining and projected strength of schedule | VW-RPT-16 |
| `M-TRAT-043` | Won-lost record and winning percentage | VW-RPT-16 |
| `M-TRAT-052` | Game prediction residual (bust) and performance against expectation | VW-RPT-16 |
| `M-TRAT-054` | Projected tournament seed and seed-relative rating gap | VW-RPT-16 |
| `M-TRAT-056` | Point-in-time rating gap between the two teams | VW-CARD-03, VW-RPT-16 |
| `M-TRAT-057` | Predicted possessions and predicted score | VW-CARD-03 |
| `M-TRAT-058` | Predicted margin (point spread from ratings) | VW-CARD-03, VW-RPT-16 |
| `M-TRAT-059` | Pre-game win probability from ratings | VW-CARD-03, VW-REV-06, VW-RPT-16, VW-STU-04 |
| `M-TRAT-060` | Prediction drivers (margin decomposition) | VW-CARD-03, VW-RPT-16 |
| `M-TRAT-061` | Rating-model context adjustments (site, travel, rest, altitude) | VW-CARD-03 |
| `M-TRAT-062` | Projected season record (overall and conference) | VW-RPT-16 |
| `M-TRAT-063` | Chance to win the conference | VW-RPT-16 |
| `M-TRAT-064` | Tournament advancement probabilities | VW-RPT-16 |
| `M-TRAT-065` | Rating-system predictive accuracy | VW-RPT-06 |
| `M-TRAT-074` | Opponent style profile vector (as-of team style features) | VW-RPT-04 |
| `M-TRAT-075` | Opponent style class (named binary splits and data-driven clusters) | VW-RPT-04 |
| `M-TRAT-078` | Performance against similar opponents (k-nearest-neighbour record and matchup effect) | VW-RPT-04 |
| `M-TRAT-079` | Style clash and pace mismatch (who dictates tempo, style distance) | VW-RPT-04 |
| `M-TREE-001` | Catch side → first action → outcome (court split by width) | VW-CARD-01, VW-STU-09 |
| `M-TREE-002` | Hand tree: catch hand → dribble hand → drive direction → finish hand | VW-CARD-01 |
| `M-TREE-004` | Opponent height variance → mismatch → big-man advantage | VW-CARD-03 |
| `M-TREE-009` | After-timeout tree | VW-CARD-02, VW-RPT-02 |
| `M-TREE-013` | Run response tree | VW-RPT-02 |
| `M-TREE-016` | Score-state behaviour tree | VW-RPT-04 |
| `M-TRN-001` | Transition possession flags (one per definition) | VW-RPT-03, VW-STU-09 |
| `M-TRN-002` | Transition frequency (offense) | VW-RPT-02, VW-RPT-03, VW-RPT-04 |
| `M-TRN-003` | Opponent transition frequency (defense) | VW-RPT-03 |
| `M-TRN-004` | Transition points per possession (offense) | VW-RPT-02, VW-RPT-03, VW-RPT-04 |
| `M-TRN-005` | Transition points per possession allowed (defense) | VW-RPT-03 |
| `M-TRN-013` | Fast-break points (official box) | VW-RPT-03 |
| `M-TRN-015` | Fast-break definition agreement (official vs ours) | VW-RPT-03 |
| `M-TRN-016` | Points off turnovers | VW-RPT-03 |
| `M-TRN-018` | Points per possession by start type | VW-RPT-03 |
| `M-TRN-019` | Possession start-type mix | VW-RPT-03, VW-RPT-04 |
| `M-TRN-021` | Seconds to first shot | VW-RPT-04 |
| `M-TRN-034` | Numbers-advantage opportunities by configuration | VW-RPT-03 |
| `M-TRN-036` | Points per possession by numbers label | VW-RPT-03, VW-RPT-07 |
| `M-TRN-037` | Push vs pull-back with an advantage (opportunity conversion) | VW-RPT-03 |
| `M-TRN-038` | Passed-up break rate (declined / denied / failed) | VW-RPT-03 |
| `M-TRN-044` | Seconds to defense set and last man back | VW-RPT-03 |
| `M-TRN-066` | Game possessions and predicted possessions (tempo context) | VW-RPT-09 |
