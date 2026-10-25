# Player identity reference pack

Date: {{DATE}}. Version {{VERSION}}. Status: {{STATUS}}

This page is generated from `config/identity_pack.yaml` and `{{RESULTS_FILE}}` by `tools/specgen/identity/gen_doc.py` (prose from `tools/specgen/identity/doc_template.md`). Do not edit it by hand.

## 0. The rule and how to read this page

Aldemir's rule: **we cannot allow an ID swap**. A player's identity is locked when he enters the frame, kept through occlusions, re-checked after every crossing and released when he leaves the frame. When re-acquisition could fail, measurements (jersey number, team colour, build and height, gait) make the re-labelling exact.

How the spec reads that rule: a detection carries a player id only when the evidence makes that id near certain. Otherwise it carries **HOLD**, a short list of who it could be. A HOLD is lost coverage, never a swap. Coverage is pushed up as far as the evidence allows, but never by guessing.

- **Detection**: one person box in one frame, no id.
- **Tracklet**: boxes joined by motion only. It is cut at every doubt, so it never contains two people.
- **Chain**: tracklets joined where nobody else could have taken over. One chain carries one identity.
- **Encounter group**: the people who were too close to tell apart for a moment (a crossing, a screen, a pile-up). Who comes out is matched to who went in by cues, not by motion.
- **Lock**: the label of a chain once its probability reaches {{P_LOCK}}. It stays until the player leaves, the camera cuts, he is substituted, or the cues contradict it (an alarm).
- **Live** labels use only what has been seen so far. **Offline** (post-game) labels use the whole chain, before and after each frame. Reports use offline labels.

## 1. Results in one table

{{HEADLINE}}

{{RESULTS_TABLE}}

What the columns mean: **swaps** = swap events, runs of frames where a player carries another player's id (or an official carries any id); the target is 0. **IDF1** and **HOTA** are the standard tracking scores (1 = perfect; they fall when boxes are left on HOLD). **coverage** = share of player boxes that carry an id. **re-confirm** = median seconds from the end of a true crossing until the player carries his correct id again.

{{FINDINGS}}

## 2. Standing constraints

{{CONSTRAINTS}}

## 3. How others do it

{{RESEARCH}}

## 4. Design principles

{{PRINCIPLES}}

## 5. The reference pack

{{PACK}}

## 6. Cues

The system checks the cues in this order. No single cue carries an identity; each adds evidence (in nats, natural-log units: +2.3 nats = ten times more likely).

{{CUES}}

## 7. Tracklets, chains and assignment

{{RULES}}

## 8. Identity state machine

{{STATE_MACHINE}}

## 9. How swaps are caught and corrected

{{SWAP_CATCH}}

## 10. Confidence and abstention

{{ABSTAIN}}

## 11. Hard cases

{{HARD_CASES}}

## 12. Outputs

{{OUTPUTS}}

## 13. Metrics and acceptance

{{METRICS}}

## 14. The SportVU harness

{{HARNESS}}

## 15. Open questions for Aldemir

{{QUESTIONS}}

## 16. Journal

{{JOURNAL}}
