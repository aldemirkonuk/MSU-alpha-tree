---
id: 002
status: queued
gpu: L4
max_gpu_hours: 0.75
---
# 002 · Separate players from everyone else (team clustering)

**Why:** task 001 found a median of 17 people per frame. Tracking must follow only the 10 players.

**Do:** run `notebooks/01_team_clustering.ipynb` top to bottom on Colab with an L4 GPU.

**Allowed:** run that notebook; read `MyDrive/MSU-Alpha-3/raw_video/test/`; write `MyDrive/MSU-Alpha-3/reports/01_team_clustering/`; commit and push `results/01_team_clustering/`, this task file and `coord/log.md`.

**Done when:** `results/01_team_clustering/metrics.json` and the four `cluster_*.png` contact sheets are committed.

**Report in the task file:** run time; what each contact sheet shows in a few words; the players-per-frame median from the two team clusters.
