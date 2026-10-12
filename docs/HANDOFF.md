# HANDOFF

## Updated
2026-10-12, after approved T04

## Project start
2026-10-12

## Current state
T00 through T04 are approved and complete. The pipeline cleans official records,
builds capital-covering episodes and DST-safe labels, applies the Kherson occupation
coverage rule, constructs cutoff-safe features, and runs walk-forward A1, A2 and B
backtests. Label history advances only across complete observations; all-unit history
uses eligible dates. Fourteen synthetic tests pass.

## Data snapshot
Official: 299,275 rows, 2022-03-15 16:10:34 UTC through 2026-09-07 05:28:22 UTC.
`data/processed/panel.csv` contains 37,628 unit-days; 99.2% are complete after D-08,
0.1% of complete unit-days have a possible imputed end, and 3 global zero-record
dates are incomplete for every unit. The validation window is 2026-06-06 through
2026-08-04; the 30-date test window is 2026-08-05 through 2026-09-06.
Backtest outputs contain 6,210 predictions, 234 metric rows and 7,020 daily metric rows.

## Next step
Start T05: implement the forecast CSV, evaluation report and charts, and complete the
README as scoped in `docs/PLAN.md`.

## Known issues
Pytest passes but cannot write `.pytest_cache` in the current environment and emits a
non-failing permission warning. In this environment, the full backtest needs single-
thread OpenMP/BLAS settings to avoid a Windows worker-pipe permission error.
