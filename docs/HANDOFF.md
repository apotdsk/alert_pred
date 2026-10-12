# HANDOFF

## Updated
2026-10-12, after approved T01

## Project start
2026-10-12

## Current state
T00 and T01 are approved and complete. The audit pipeline downloads and independently
audits the official and volunteer candidate datasets, uses the accepted 23-unit mapping,
generates source-specific figures, and compares per-unit daily alert minutes over their
complete overlapping months. `python run.py` executes the implemented audit stage and
prints stubs for the remaining stages. The required pytest and full-run checks pass.

## Data snapshot
Official: 299,275 rows, 2022-03-15 16:10:34 UTC through 2026-09-07 05:28:22 UTC.
Volunteer: 116,174 rows, 2022-02-25 16:36:22 UTC through 2026-10-12 04:49:48 UTC.
The files remain separate. Agreement is reported for complete months from 2022-04-01
through 2026-08-31 in `outputs/data_audit.md`.

## Next step
Decision gate: the owner settles the open T01-derived choices in `docs/DECISIONS.md`
before starting T02. T02 itself has a Plan gate.

## Known issues
Pytest passes but cannot write `.pytest_cache` in the current environment and emits a
non-failing permission warning.
