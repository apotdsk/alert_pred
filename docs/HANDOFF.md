# HANDOFF

## Updated
2026-10-13, after approved T05b

## Project start
2026-10-12

## Current state
T00 through T05b are approved and complete. The pipeline cleans official records,
builds capital-covering episodes and DST-safe labels, applies the Kherson occupation
coverage rule and D-11 source-gap periods, constructs cutoff-safe features, and runs
walk-forward A1, A2 and B backtests. It produces the D-10 live forecast, evaluation
report and three evaluation charts without connecting lines across excluded dates.
The README documents setup, Jupyter use, data definitions and outputs. Fifteen
synthetic tests pass.

## Data snapshot
Official: 299,275 rows, 2022-03-15 16:10:34 UTC through 2026-09-07 05:28:22 UTC.
`data/processed/panel.csv` contains 37,628 unit-days; 97.9% are complete after D-08
and D-11, and 0.1% of complete unit-days have a possible imputed end. Thirteen source
gaps longer than 12 hours are detected; every overlapping local date is incomplete.
The validation window is 2026-06-04 through 2026-08-02; the 30-date test window is
2026-08-03 through 2026-09-06.
Backtest outputs contain 6,210 predictions, 234 metric rows and 7,020 daily metric rows.
The live forecast is for 2026-09-07 and contains 69 bounded rows: 23 units for each
of A1, A2 and B. `outputs/evaluation.md` reports all 27 overall/frontline/other metric
rows from `outputs/metrics.csv`, with counts rounded to 3 decimals and minutes to 1.

## Next step
Start T06 with its Plan gate: propose the implementation plan for models C1 and C2,
validation-only selection, past-only clustering assertions and evaluation section.

## Known issues
Pytest passes but cannot write `.pytest_cache` in the current environment and emits a
non-failing permission warning. In the sandbox, the full backtest raises WinError 5
while creating a scikit-learn worker pipe; the approved outside-sandbox run succeeds.
