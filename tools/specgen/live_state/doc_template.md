# Live game state: what we know at every instant, how late, and what it becomes when a sensor drops

Date: {{DATE}} (last journal entry {{LAST_ENTRY}}). Version {{VERSION}}. Status: {{STATUS}}

This page is generated from `config/live_state/*.yaml`, `schema/live_state_changes.yaml` and `results/live_state_test/*.json` by `tools/specgen/live_state/gen_doc.py` (prose from `tools/specgen/live_state/doc_template.md`). Do not edit it by hand.

## What this page is

{{SCOPE}}

The ask: {{ASK}}

The page of 19 Oct listed the fields in 10 groups. This page keeps those 10 groups and adds, for every field: where the value comes from, when it changes, how late we know it, and what it becomes when the sensor that gives it goes away. The first screen is the summary. Everything after it is reference.

## One-screen summary

**The rule.** {{THE_RULE}}

**The grade ladder.** Every value carries one grade at every instant. Best first: {{LADDER}}. A value only moves down the ladder with time; it moves up only when a sensor sees it again.

**The five numbers that matter most** (all measured on our own recordings):

{{FIVE_NUMBERS}}

**Not measured yet** (every value that rests on one of these is tagged assumed):

{{NOT_MEASURED}}

**Size of the pack.** {{COUNTS}}

## How to read this page

- **Field tables** (the 10 groups) have eight columns.
  - *Field*: the id, the key used in the YAML, and the plain name.
  - *Values / unit*: what the field can hold, its type and unit, and the word stored when it is not known. No field is ever empty.
  - *Stored*: `key` = part of the row key; `segment` = a dimension of `state_segments` (changed only by typed transitions); `clock_map` = the clock map; `obs` = a per-frame observation table; `derived` = computed, not stored as truth; `fixed` = set before tip.
  - *Sources by authority*: the sensors, by role. `value` gives the value (the scorebook first), `confirm` agrees or disagrees with it, `timing` gives the instant, `fallback` is used when the others are away. A derived field lists its inputs.
  - *Changes on*: the transition types of `config/state_machine.yaml` (T00 to T26) that can change it, or `continuous`, `per_frame`, `on_input_change`. "Instant" is the exact definition of the moment the fact becomes true in the game.
  - *Live latency budget*: median / p95 of known time minus event time, in seconds of video time. Provisional = first held at any grade; confirmed = agreed by a second sensor. The tag in brackets says whether the budget is measured or assumed. Latency is reported, not a gate (K23).
  - *When a sensor drops*: one line per condition: the grades the value passes (with the limit of each step), the rule applied, the rule applied when the sensor is back, and the evidence tag. "Rules of profile" means the field uses the rules of its profile unchanged (section Rules and profiles).
  - *Conflict rule*: when two sources disagree, who wins the value, who wins the instant, and where the disagreement is logged.
- **A grade path** such as `observed > inferred > carried > unknown` with limits 3 s and 30 s reads: observed until the sensor goes; inferred for up to 3 s; carried up to 30 s; unknown after that.
- **Parameters** are written as `name` with their value. Every one is listed once in the table of section "What is measured and what is assumed", with its evidence.
- **Requirement ids** (R-SR, R-IV, R-SB, R-MB, R-SY, R-MD ...) are those of the live requirements. This pack answers: {{REQUIREMENTS}}. {{IDS_NOTE}}
- Each record in the YAML also lists the table columns the field lands in (`lands_in`; a column that does not exist yet is in `schema/live_state_changes.yaml`), its invariants and its consumers, and has notes that say what happens on a tight shot, in a replay, in a break and with play-by-play only. Those are not repeated here.

{{CONVENTIONS}}

## Sensors

A sensor is anything that can show a value. Each has a health signal: a field of this pack that says the sensor has dropped. The dropout rules read those fields.

{{SENSORS}}

### What the sensors measured

{{SENSOR_NUMBERS}}

## Grades

{{GRADES}}

## Rules and profiles

A field names one profile and overrides only what differs. A profile fixes the sources, the latency budget, the conflict rule and the dropout rules.

### Rule library

{{RULES}}

{{PROFILES}}

### Longest time a state can last (max dwell)

A carried status may not outlive what the rules or physics allow. Past its bound the old value becomes unknown, or the value the rules imply starts at grade inferred.

{{MAX_DWELL}}

## Degradation levels

What the broadcast shows decides what can be known. The level is itself a field (`degradation_level`). The columns are the profiles.

{{LEVELS}}

## The fields, in the 10 groups of the 19 Oct page

### 1. Keys and provenance (on every row)

{{GROUP_KEYS}}

### 2. Time (four clocks, kept apart)

{{GROUP_TIME}}

### 3. Score

{{GROUP_SCORE}}

### 4. Possession and the ball

{{GROUP_POSSESSION_BALL}}

### 5. Counts the rules run on

{{GROUP_COUNTS}}

### 6. Personnel

{{GROUP_PERSONNEL}}

### 7. Situation (derived, recomputed at every change)

{{GROUP_SITUATION}}

### 8. Tactics (from tracking; each label with a confidence)

{{GROUP_TACTICS}}

### 9. Observability (what we can actually see)

{{GROUP_OBSERVABILITY}}

### 10. Fixed for the game (known before tip)

{{GROUP_FIXED}}

### What is not a field, and what was added

{{OUT_OF_SCOPE}}

## Reconciliation windows

The scorebook wins values. CV and audio win instants. A raw reading is never overwritten.

{{RECONCILIATION}}

**How a latency budget is put together.** {{LATENCY_COMPOSITION}}

## Real-data replay

The reference fuser was run on the real scorebug readings with extra stretches hidden on purpose, and scored against the readings it was not shown.

{{REPLAY}}

What the replay proves: on real readings the rules never claim more than they hold, nothing is empty, and every miss and correction leaves a log row. What it cannot prove: anything finer than 1 s; a late or wrong bug (the bug is the truth here); real whistle or CV cues (stand-ins were used); the real feed delay (swept); made-basket detection, lineups, possession or any field that needs pixels.

## Acceptance

{{ACCEPTANCE}}

## What is measured and what is assumed

Every number in the pack carries an evidence tag. Counts by tag:

{{EVIDENCE_SUMMARY}}

All parameters, measured first and assumed last. "Read by" says whether the reference code (replay and rule tests) reads the parameter, or why it cannot.

{{PARAMS}}

## Open questions for Aldemir

Each question has a recommended answer. Where the pack had to pick one to be complete, it follows the recommendation.

{{QUESTIONS}}

## Follow-up edits outside this page

Nothing below is applied. Each is an edit to a file this pack does not own, or work for a later version.

{{FOLLOW_UPS}}

### Proposed schema changes

{{SCHEMA_CHANGES}}

## Journal

{{JOURNAL}}
