# HANDOFF

## Updated
2026-10-12, after approved T05

## Project start
2026-10-12

## Current state
T00 through T05 are approved and complete. The pipeline cleans official records,
builds capital-covering episodes and DST-safe labels, applies the Kherson occupation
coverage rule, constructs cutoff-safe features, and runs walk-forward A1, A2 and B
backtests. It also produces the D-10 live forecast, evaluation report and three
evaluation charts. The README documents setup, Jupyter use, data definitions and
outputs. Fourteen synthetic tests pass.

## Data snapshot
Official: 299,275 rows, 2022-03-15 16:10:34 UTC through 2026-09-07 05:28:22 UTC.
`data/processed/panel.csv` contains 37,628 unit-days; 99.2% are complete after D-08,
0.1% of complete unit-days have a possible imputed end, and 3 global zero-record
dates are incomplete for every unit. The validation window is 2026-06-06 through
2026-08-04; the 30-date test window is 2026-08-05 through 2026-09-06.
Backtest outputs contain 6,210 predictions, 234 metric rows and 7,020 daily metric rows.
The live forecast is for 2026-09-07 and contains 69 bounded rows: 23 units for each
of A1, A2 and B. `outputs/evaluation.md` reports all 27 overall/frontline/other metric
rows directly from `outputs/metrics.csv`.

## Next step
Start T06 with its Plan gate: propose the implementation plan for models C1 and C2,
validation-only selection, past-only clustering assertions and evaluation section.

## Known issues
Pytest passes but cannot write `.pytest_cache` in the current environment and emits a
non-failing permission warning. In the sandbox, the full backtest raises WinError 5
while creating a scikit-learn worker pipe; the approved outside-sandbox run succeeds.
