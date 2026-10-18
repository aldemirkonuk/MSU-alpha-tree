# Notebooks

Workflow between the two Claude sessions:

1. The planning session (cloud) writes a notebook here and commits it.
2. The Mac session pulls, opens it in Colab through the Colab MCP, runs it, and commits outputs to `results/<notebook>/` (metrics JSON, small figures, error logs). Large files go to Google Drive only.
3. The planning session reads the results from the repo.

Rules for every notebook:
- Numbered in run order: `00_`, `01_`, ...
- First markdown cell states goal, GPU, expected run time and pass criteria.
- Re-runnable: creates folders with `exist_ok`, never overwrites raw video.
- Drive root: `/content/drive/MyDrive/MSU-Alpha-3`.
- Results always written to both the repo (`results/`) and Drive (`reports/`).

| Notebook | Purpose | GPU | Status |
| --- | --- | --- | --- |
| `00_smoke_test.ipynb` | GPU, Drive, repo tests, test clip, detector speed | L4 | Ready to run |
