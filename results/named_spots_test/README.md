# Named-spot dictionary tests (2026-10-20)

- `check_summary.json`: `tools/specgen/named_spots/check.py --step 0.05` on `config/named_spots.yaml`: whitelist, anchors, probes, mirrors (0 failures) and partitions on 231,401 grid points (court_region and the six crosswalks: 100% covered, 0 overlaps).
- `cbbd_summary.json`: `tools/specgen/named_spots/cbbd_check.py` on 3,675 located MSU 2025-26 field-goal attempts (CBBD, licensed; aggregates only). Every shot gets exactly one label per scheme; two-vs-three agreement 3,672/3,675.
- Scenario tests for ball-relative entries were run in the session scratchpad (man-to-man 47/47, zones 53/53, presses 38/39, restarts 61/61); see docs/data/named_spots.md section 6.
- CBBD lateral orientation (2026-10-20): checked on UConn video frames ~1.3 s before four made baskets (makes 3, 4, 9, 10 in the private _audit/uconn/made_basket_lag.csv). All four shooters stand on the side opposite to the first transform, so CBBD's y axis points to the attacker's left; cbbd_check.py now negates it. Only left/right labels change.
