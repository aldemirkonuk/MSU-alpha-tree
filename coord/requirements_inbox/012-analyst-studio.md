# Requirements inbox 012 · Analyst Studio, and four inbox-011 items made priority

From: Mac session (msu-colab), 2026-10-19. To: requirements session. Status: proposal (add-only).

## Priority from inbox 011 (Aldemir, 19 Oct)

Aldemir picked these four of the 20 inbox-011 proposals as priorities. They are also what the Studio below stands on.

| Proposal | Why the Studio needs it |
| --- | --- |
| new-MD-21 home/away storage; the state pipeline runs on any D-I game | The Studio opens any game, not only MSU's. |
| new-EN-12 one SQL query layer; every stat served by its catalogue ID | Every number the Studio shows comes from one query by metric ID. |
| new-EN-13 lineage from every output row to its inputs | Clicking any value shows where it came from. |
| new-SY-12 play-by-play corrections pulled again and propagated | Edits and source corrections follow the same re-score path. |

## Analyst Studio

Aldemir's words: "a live dynamic editing scale ... like a studio vibe ... click on everything you can, such as the
computer vision, the models, the players, the score ... an interface for data scientists to work out the most
efficient way." Design reference: a canvas you edit directly, where every object on screen can be selected,
inspected and changed, and every change shows its effect.

| Proposal | Tier | Text | Acceptance |
| --- | --- | --- | --- |
| new-ST-S01 | Shall | One game canvas: video, top-down court, game-state panel (docs/data/live_game_state.md) and timeline, all synchronised through the clock map. Scrubbing any of them moves the others. | At 100 random instants of a pilot game, video frame, court positions and state panel refer to the same game-clock instant (100%). |
| new-ST-S02 | Shall | Everything is selectable: detection box, track, player, ball, score, clock, state segment, transition, event, set, coverage, stat value, model output. Selecting shows its value, source, confidence, model or rule version, and lineage (new-EN-13); a stat also shows its formula and metric ID. | 100% of on-screen objects open an inspector; lineage resolves for every selected value. |
| new-ST-S03 | Shall | Edits are proposals, never overwrites: relabel an identity, set, coverage or event; move a boundary; change a parameter (R-CX-29); swap a model version. Each edit creates a draft state version with a diff against the current one. Only Aldemir promotes a draft (human-in-the-loop). | An edit leaves the current state version byte-identical until promotion; the diff lists exactly the changed rows. |
| new-ST-S04 | Shall | Live recompute: after an edit, only the affected segments, stats and predictions are recomputed (the changed clock range, K09) and the screen updates. | Possession-scope edit visible in ≤ 2 s; whole-game parameter change in ≤ 60 s on the pilot games (proposal). |
| new-ST-S05 | Shall | Model bench: pick the version of each stage (detection, tracking, team, jersey, pose, court, OCR, action, value, sequence model) and compare versions side by side on gold-v1 with their metrics and failure cases. | Two versions of a stage compared on gold-v1 with per-slice metrics in one view; the chosen version is recorded in the run record. |
| new-ST-S06 | Shall | Selections become queries: lasso players or a court zone, brush a time range, or filter by state ("clutch, MSU ball, after timeout") and the Studio writes the SQL over the query layer with metric IDs. Saved selections are named shortcuts. | Every selection exports its SQL; re-running the SQL returns the same rows. |
| new-ST-S07 | Should | Shortcuts and a command palette: keyboard access to every action (next possession, next disputed label, jump to clock, toggle layers, run a saved selection). | Every Studio action has a command; the 20 most used have keys. |
| new-ST-S08 | Should | Parameter sensitivity: for any parameter, show how the dependent stats and win probability move across its range before committing. | A sweep over a parameter's range renders for every metric that declares it. |
| new-ST-S09 | Shall | Audit and safety: every edit records who, when, why and the state versions before and after; edits are reversible. Edits on held-out games are flagged so they cannot leak into training (D19). | 100% of edits logged; undo restores the previous version byte-identically; held-out edits flagged 100%. |
| new-ST-S10 | Shall | Private by design: runs on the private store, video never leaves it, no face crops exported, the JEV lane is read-only and separate (inbox 001). | No export path writes video or face crops; the Studio never writes to the JEV log. |
| new-ST-S11 | Should | Network view: for the selected frame or possession, show each neural network's architecture, its input, its output, and where available attention or saliency, so a scientist sees why a model decided. | For the detector, jersey reader and sequence model, the view shows input, output and one explanation map for a selected instant. |
| new-ST-S12 | Should | Layers: toggle overlays (boxes, tracks, IDs, court lines, passing lanes, spacing hull, defender matchups, transition numbers, value heat map) on video and court. | Each overlay toggles independently and stays aligned within 1 frame. |

Build note: this is a requirement set only; nothing is built during the freeze. A clickable mockup can be made as a
private artifact for review if Aldemir wants one.
