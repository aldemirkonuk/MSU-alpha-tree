# MSU Alpha 3

Computer vision and analytics for Michigan State men's basketball. The goal is to turn broadcast video into a full 10-player + ball state, value every possession, and build win probabilities from the possession up to the game, benchmarked against betting and prediction markets.

Status: requirements and research phase. No video has been processed yet.

## Layout

| Path | What it holds |
| --- | --- |
| `docs/requirements.md` | Master requirements (exported from the live doc; the doc is the source of truth) |
| `docs/research/` | Literature review, open-source audit, odds and prediction-market research, first-pass set taxonomy |
| `docs/taxonomy/` | Full offense and defense taxonomies with detection signatures |
| `config/court_ncaa_men.yaml` | Court constants in metres (verify against the current NCAA rulebook) |
| `config/vocabulary_map.yaml` | Common basketball terms linked to measured definitions |
| `config/hypotheses.yaml` | Hypothesis registry, written before testing |
| `schema/global_metadata.yaml` | Fields stamped on every record, with units |
| `src/msu_alpha/` | Python package; starts with the court geometry module |
| `tests/` | Tests; run with `pytest` |
| `LICENSES.md` | License register for every dataset, model and library used |

## Data

Video and processed data live in Google Drive, never in this repository. See `data/README.md` for the Drive layout.

## Conventions

- Units: metres, centimetres, seconds, milliseconds, degrees. No feet.
- Court frame: origin under the centre of the attacked rim; x along the baseline (positive to the attacker's right), y toward half-court; θ = 0° right baseline, 90° top of the key.
- Every value carries its source and a confidence.
- A possession ends only when the other team gains control; each shot-clock cycle inside it is a chance.

## Run the tests

```bash
uv run --with pytest --with pyyaml pytest
```
