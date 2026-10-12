# HANDOFF

## Updated
2026-10-12, after approved T02

## Project start
2026-10-12

## Current state
T00 through T02 are approved and complete. The pipeline cleans official records, applies
the accepted capital-covering rule, merges alert episodes, and writes a DST-safe daily
label panel plus sustained-majority reform dates. `inspect` reads the saved panel and
shows only the requested unit-day's source records, episodes and labels. Panel generation
is vectorized; the final full run completed in 24.495 seconds. Eight synthetic tests pass.

## Data snapshot
Official: 299,275 rows, 2022-03-15 16:10:34 UTC through 2026-09-07 05:28:22 UTC.
Volunteer: 116,174 rows, 2022-02-25 16:36:22 UTC through 2026-10-12 04:49:48 UTC.
The files remain separate. Agreement is reported for complete months from 2022-04-01
through 2026-08-31 in `outputs/data_audit.md`.
`data/processed/panel.csv` contains 37,628 unit-days: 99.8% are complete, 0.1% of
complete unit-days have a possible imputed end, and 3 global zero-record dates are
incomplete for every unit. `data/processed/reform_dates.csv` covers all 23 units.

## Next step
Start T03 exploratory analysis. It has no gate; keep its notebook logic in `alerts/`
and produce the five required figures and evidence-linked findings from the saved panel.

## Known issues
Pytest passes but cannot write `.pytest_cache` in the current environment and emits a
non-failing permission warning.
