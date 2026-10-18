# Spec generators (prompt 003, 2026-10-18)

Python scripts that generated the proposed data dictionaries and schema files. Kept so the specs can be
rebuilt after the requirements session decides. They contain specifications only, no data.

- `core_tables/`: docs/data/dictionary_games.md and schema/tables/*.yaml for the 91 core tables (`gen.py`).
- `state_tables/gen_state.py`: docs/data/dictionary_state.md, the 13 state-table schemas and config/invariants.yaml.
- `ontology/`: docs/data/game_ontology_coverage.md, config/game_ontology.yaml and
  coord/requirements_inbox/007-game-ontology-gaps.md (`gen.py`, checked by `validate.py`).

Paths inside the scripts may point at the original scratch folder (the live-doc export and a text copy of the
rules book); adjust before re-running. The rules-book text is not copied here (derive it with
`pdftotext -layout docs/rules/PRMBB_RulesBook.pdf`).
