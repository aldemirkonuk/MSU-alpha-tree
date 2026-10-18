# Requirements inbox 001 · JEV as external consultant

From: planner session. To: requirements session. Status: agreed with Aldemir on 17 Oct 2026, ready to paste.
Action: add the section below to the live requirements doc as a new section titled **External consultant: JEV**, placed after "Human-in-the-loop flagging and labeling". Add the two hypotheses to the hypothesis registry and the one line to the license register. Update the requirements tree with a branch "External consultant (JEV)" outside the main pipeline. Do not change the wording of the decisions.

---

## External consultant: JEV

JEV is an outside second opinion, not part of the pipeline: it reads our outputs and the raw frames, writes its verdict to its own log, and nothing in the pipeline ever reads that log.

**Decisions (Aldemir, 17 Oct)**
- Role: third-party approver, authenticator and double verifier only. Never a pipeline module.
- JEV never creates, changes, overwrites or deletes a label, a track, a feature or a prediction.
- Its outputs are never used as model features, training labels or inputs to win probabilities.
- Questions are always asked blind: multiple choice that includes our answer, close alternatives and "none of these". Never "is this X? yes or no".
- Model: the most advanced JEV we can access. Default: TypeSafe API `jev` version that supports images (Jev 1.13 or 1.14 at time of writing), pinned to an exact version, never `jev-latest`. Alternative: open-weights JEV-27B-VL (AutoTrust AI, Apache-2.0) self-hosted on the Colab G4 if API access or rights are a problem. JEV Omni (claims video) only if access is confirmed.

**What JEV is asked (consultation types)**

| ID | Question | Input sent | Answer type |
| --- | --- | --- | --- |
| J1 | Which set is this possession? | ~10 broadcast frames in time order + top-down path drawing + text facts | Choice: our label, 2–4 closest alternatives from the taxonomy, "none of these" |
| J2 | What defense is this, man or which zone? | 3–6 frames across 2–3 s + defender positions as text | Choice: man, 2-3, 3-2, 1-3-1, match-up, press, junk, unclear |
| J3 | Did the defense change scheme in this window? | Frames before and after the detected switch time | Noul (yes probability) + Choice of the new scheme |
| J4 | Which camera shot is this frame? | 1 frame | Choice: main wide, close-up, replay, slow motion, crowd, bench, graphic |
| J5 | Which team or role is this person? | Player crop + reference crops of both kits and a referee | Choice: team A, team B, referee, other |
| J6 | Which referee signal is this? | Referee crop sequence (2–4 frames) | Choice: foul, travel, 3-point attempt, timeout, jump ball, none |
| J7 | Which ball-control state is this moment? | 3 frames around the moment | Choice: MSU ball, Team X ball, contested, in flight, inbound pending, dead |
| J8 | Text classification of availability reports | News/injury text for a player and game date | Choice: available, questionable, out, returned |
| J9 | Text classification of commentary | Transcript lines around a possession | Choice over set and scheme labels, or "not mentioned" |

**Verification packet (what one consultation contains)**
- Frames: up to 10 broadcast frames, oldest first, each with its game-clock time; still JPEG or PNG; each side between 280 and 1568 pixels (resize full frames down, pad or upscale small crops up); rotated upright.
- Optional: the top-down court drawing of tracked paths in the metre grid, clearly labelled "from our tracking".
- Text facts: the measured values (positions in metres, angles in degrees, timings in seconds) and the candidate definitions copied from the taxonomy.
- Example images in the answer options: each Choice option defined by a written definition plus 2–3 example frames from hand-labelled possessions.
- Size: within the API limits (32 MiB per request including all images; each image counted again every time it is referenced). Frames used by several questions go in the state once.
- Every packet stored with an ID, so any verdict can be traced to exactly what JEV saw.

**Independence rules**
- The raw broadcast frames are always included; the tracking drawing alone is never enough, because it comes from our own pipeline and would make JEV agree with our mistakes.
- Our label is never marked as the expected answer; option order is shuffled.
- Example images for the options come from the locked answer key's training split, never from the possession being judged.

**Calibration (before any verdict counts)**
1. Answer key: about 200 possessions hand-labelled by Aldemir, spread across set families, defensive schemes, camera shots and ball states. Locked: never used to train our own models. Split into a part for option examples and a part for calibration.
2. Ask JEV blind on the calibration part; record answer and probability.
3. Group answers by stated probability (for example 0.5–0.6, …, 0.9–1.0) and measure the real accuracy in each group against the key.
4. Fit a correction from stated probability to real accuracy (isotonic regression; Platt scaling if data is thin), separately for each consultation type J1–J9.
5. Report per type: accuracy, calibration error (ECE), reliability curve, and accuracy by our own confidence level.
6. Set verdict thresholds per type from the corrected probability (proposals to tune): **confirms** our label at ≥ 0.85; **disputes** when it picks a different option at ≥ 0.70; anything else is **no opinion**.
7. A consultation type is switched on only if JEV beats a minimum accuracy on the key (proposal: ≥ 80% top-1 on that type). Types below it stay off.
8. Recalibrate whenever the JEV version changes (TypeSafe states accuracy can change between releases).

**What happens with a verdict**
- Confirms: logged; no other effect.
- Disputes: logged and the possession is added to Aldemir's review queue, ranked with the pipeline's own low-confidence flags. Aldemir's decision is the only thing that can change data.
- No opinion: logged only.

**The JEV log (separate store)**
- One row per consultation: packet ID, game ID, possession or frame IDs, consultation type, JEV model and exact version, question text, option list in shown order, JEV raw probabilities, corrected probabilities, verdict, our label and our confidence, latency, cost, timestamp.
- Stored apart from pipeline data, in `MyDrive/MSU-Alpha-3/consultant/jev/` and summarized in reports.

**Audit metrics (reported per game and per season)**
- Agreement rate between JEV and our pipeline, per consultation type and per set family or scheme.
- Dispute rate, and of disputes reviewed by Aldemir, how often JEV was right vs our pipeline.
- Trend over time: agreement should rise as our pipeline improves; a drop flags a regression.

**Budget and scope**
- Consultations at possession level, not per frame: about 70 possessions per game for J1, plus sampled checks for J2–J7 (proposal: 20 per type per game).
- A per-game cost and token log; a monthly spending cap set by Aldemir.
- Every 10th consultation re-run to measure consistency (JEV answers are not fully deterministic).

**Limits to respect**
- Images are still frames only: motion is inferred from frame order, so timing-based actions (slip vs screen, screen angle) carry lower weight; prefer J2, J4, J5, J7 for trust.
- Image support is labelled "dreamer-ready" by TypeSafe: not production grade.
- Broadcast frames sent to a third party: private research use only, logged, nothing sensitive sent.

**Acceptance tests**
- A pipeline run with JEV switched off produces byte-identical pipeline outputs to a run with JEV on.
- No pipeline module imports or reads the JEV log.
- Calibration report exists for each enabled type, with the version it applies to.

**New hypotheses for the registry**
- H11: JEV agreement with our pipeline rises as our pipeline's validation accuracy rises (agreement works as a label-free quality signal). Measure: correlation across model versions.
- H12: Possessions JEV disputes contain a higher share of our pipeline's real errors than random possessions. Measure: error rate in disputed vs random reviewed possessions.

**License register line**
- JEV (TypeSafe API, pinned version) or JEV-27B-VL (AutoTrust AI, Apache-2.0): external consultant only; broadcast frames sent to a third party for private research; not used for training or features.

**Sources**
- TypeSafe images documentation (attached by Aldemir, 17 Oct): images in state, instructions and criteria; frame-history pattern; limits 280–1568 px, 32 MiB; "dreamer-ready" status; Jev 1.13 and 1.14 accept images.
- JEV-27B-VL model page: https://www.gradually.ai/en/ai-models/autotrustjev-27b-vl/
- JEV Omni summary: https://hermes-ai.net/news/jev-omni-scores-decisions-across-text-images-audio-and-video-in-milliseconds/
- Raschka on JEV's Choice, Noul and Score APIs and calibration: https://magazine.sebastianraschka.com/p/classifier-history-and-jev
