# tools/state: pre-production test harness

`k09_fold.py` and `tests/state/` were written during the build freeze (19 Oct 2026) only to test the K09 specs
(`config/state_machine.yaml`, `schema/tables/clock_map.yaml`, `state_transitions.yaml`, `state_segments.yaml`) on the
UConn and Louisville games. Results: `results/state_machine_test/README.md`.

Aldemir, 19 Oct: keep it as evidence for the requirements; **remove it before production** (when the freeze lifts and
the production build of these tables starts, delete `tools/state/` and `tests/state/` and rebuild under the approved
requirements).
