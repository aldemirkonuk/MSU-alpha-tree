---
id: 001
status: queued
gpu: L4
max_gpu_hours: 0.5
---
# 001 · Run the smoke-test notebook

**Do:** Run `notebooks/00_smoke_test.ipynb` top to bottom on Colab with an L4 GPU.

**Allowed:** run that notebook; create folders under `MyDrive/MSU-Alpha-3`; write `results/00_smoke/`; commit and push those files plus this task file and `coord/log.md`.

**Done when:** `results/00_smoke/metrics.json` is committed. On failure commit `results/00_smoke/error.txt` with the cell number and full error.

**Report in the task file:** GPU name, run time, people-per-frame median, seconds per frame, anything surprising.
