# License register

Policy (decided 17 Oct 2026): any dataset or open-source component we can lawfully access may be used for this research. Every component is logged here with its terms, so non-commercial or copyleft terms are visible if the project ever becomes commercial. Licenses are re-checked when a component is actually adopted.

| Component | Use | License | Commercial use | Status |
| --- | --- | --- | --- | --- |
| hoopR | Play-by-play, rosters, shot locations | MIT | Yes | Planned |
| RF-DETR (N/S/M/L) | Detection, court keypoints | Apache-2.0 | Yes | Planned |
| RF-DETR (A/F/P sizes) | Detection | Roboflow PML 1.0 | Check terms | Avoid unless needed |
| roboflow/sports (feat/basketball) | Court mapping, team clustering | Check repo | Check | To verify |
| TeamTrack | Tracker development | CC BY-SA 4.0 | Share-alike | Planned |
| DeepSportRadar data | Calibration, ball, re-ID | Research only | No | Research setup |
| SportsMOT | Tracking pre-training | CC BY-NC 4.0 | No | Research setup |
| NBA SportVU 2015-16 mirrors | Imputation and EPV pre-training | Unclear | Unclear | Research setup |
| Ultralytics YOLO | Detection (alternative) | AGPL-3.0 | Copyleft | Not planned |
| sn-gamestate | Game-state reference | GPL-3.0 | Copyleft | Reference only |
| pyarrow | Parquet snapshot tables for the market collector (optional extra `markets`) | Apache-2.0 (PyPI, checked 18 Oct 2026) | Yes | Adopted (B2 foundation) |
| Broadcast footage (YouTube, B1G+ recordings) | Model input | Copyrighted | No | Private research use only, never redistributed |

Full audit: `docs/research/open_source_audit.md`.
