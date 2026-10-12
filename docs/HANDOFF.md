# HANDOFF

## Updated
2026-10-12, after approved T03

## Project start
2026-10-12

## Current state
T00 through T03 are approved and complete. The pipeline cleans official records, applies
the accepted capital-covering rule, merges alert episodes, and writes a DST-safe daily
label panel plus sustained-majority reform dates. Exploratory analysis is implemented in
`alerts/eda.py` and orchestrated by `notebooks/01_eda.ipynb`. The notebook contains five
captioned inline charts, and `outputs/eda_notes.md` contains five chart-linked findings.
Eight synthetic tests pass.

## Data snapshot
Official: 299,275 rows, 2022-03-15 16:10:34 UTC through 2026-09-07 05:28:22 UTC.
Volunteer: 116,174 rows, 2022-02-25 16:36:22 UTC through 2026-10-12 04:49:48 UTC.
The files remain separate. Agreement is reported for complete months from 2022-04-01
through 2026-08-31 in `outputs/data_audit.md`.
`data/processed/panel.csv` contains 37,628 unit-days: 99.8% are complete, 0.1% of
complete unit-days have a possible imputed end, and 3 global zero-record dates are
incomplete for every unit. The EDA uses 37,559 complete unit-days from 2022-03-16
through 2026-09-06. `data/processed/reform_dates.csv` covers all 23 units.

## Next step
Start T04 with its Plan gate: propose the features, models A and B, backtest, leakage
test, and verification approach, then wait for owner approval before implementation.

## Known issues
Pytest passes but cannot write `.pytest_cache` in the current environment and emits a
non-failing permission warning.
