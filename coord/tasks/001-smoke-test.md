---
id: 001
status: done
gpu: L4
max_gpu_hours: 0.5
---
# 001 · Run the smoke-test notebook

**Do:** Run `notebooks/00_smoke_test.ipynb` top to bottom on Colab with an L4 GPU.

**Allowed:** run that notebook; create folders under `MyDrive/MSU-Alpha-3`; write `results/00_smoke/`; commit and push those files plus this task file and `coord/log.md`.

**Done when:** `results/00_smoke/metrics.json` is committed. On failure commit `results/00_smoke/error.txt` with the cell number and full error.

**Report in the task file:** GPU name, run time, people-per-frame median, seconds per frame, anything surprising.

## Runner report (2026-10-18)

- **Result:** all 6 cells passed. Metrics in `results/00_smoke/metrics.json` (copy also in Drive `reports/00_smoke_metrics.json`).
- **GPU:** NVIDIA L4, 23 GB.
- **Run time:** about 4 minutes wall clock, including pip installs and the clip download (well under the 0.5 GPU-hour limit).
- **Tests:** 7 passed.
- **Clip:** 1920x1080 at 25 fps, 2999 frames, 80.9 MB, saved to `MyDrive/MSU-Alpha-3/raw_video/test/`.
- **Detector:** RF-DETR Base, 120 frames scored. People per frame: median 17, min 13, max 20. Every frame had 8 or more.
- **Speed:** 0.026 s per frame median, so about 0.43 GPU-hours for a 40-minute game at full 25 fps.
- **Surprising:** a median of 17 people is well above the 10 players on court. The detector also counts referees, benches and fans, so player filtering (court mask or jersey/team step) is needed before tracking.
- **Method note:** the Colab MCP connects, but its notebook tools don't register in this Mac session. The runner opened the notebook from GitHub in Colab and drove it through the Chrome tab. The metrics were read from the cell 6 output and copied here verbatim.
