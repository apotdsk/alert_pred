# PLAN

Statuses: Todo, In progress, Done. Codex sets Done at Close only after the owner writes "Approved".
Gates: Plan = propose a plan and wait. Decision = the owner settles open items in
DECISIONS.md before the next task starts.

| ID  | Task                                    | Gate     | Status |
|-----|-----------------------------------------|----------|--------|
| T00 | Scaffold                                | -        | Done   |
| T01 | Data audit                              | Decision | Done   |
| T02 | Episodes, labels, panel                 | Plan     | Todo   |
| T03 | Exploratory analysis                    | -        | Todo   |
| T04 | Features, models A and B, backtest      | Plan     | Todo   |
| T05 | Forecast, evaluation report, README     | -        | Todo   |
| T06 | Model C                                 | Plan     | Todo   |
| T07 | Reproducibility check                   | -        | Todo   |

## T00 Scaffold
Scope: package `alerts/` with the modules listed in AGENTS.md as stubs; `run.py`
dispatching the five stages, `inspect` and `--raw-path` (stubs print the stage name);
`requirements.txt` with minimum versions; `README.md` skeleton with the advisory
disclaimer; `tests/`, `notebooks/`, `outputs/figures/`, `data/processed/` with `.gitkeep`.
Done when: `python run.py` prints the five stages and exits 0; `python -m pytest -q`
runs without collection errors.

## T01 Data audit
Scope: `data.py` downloads the source to `data/raw/` if missing (or uses `--raw-path`),
parses timestamps, normalizes region names; `python run.py audit` writes
`outputs/data_audit.md` and its figures as SPEC §5, ending with proposed wording for
D-01 to D-05. Apply D-01 cleaning (duplicates, end <= start, possible_imputed_end flag) and compute D-05 reform dates into data/processed/reform_dates.csv.
Out of scope: episodes, labels, models.
Done when: every item of SPEC §5 appears in the audit; `python run.py audit` exits 0.

## T02 Episodes, labels, panel
Scope: `episodes.py` (covering rule SPEC §2, merge tolerance SPEC §4); `labels.py`
(windows SPEC §3, labels SPEC §4, coverage SPEC §6); `data/processed/panel.csv`; the
`inspect` command; the invariant check in `run.py`; `tests/test_labels.py` (SPEC §11).
Done when: zero invariant violations; label tests pass; `inspect` prints records,
episodes and labels for any unit-day.

## T03 Exploratory analysis
Scope: `notebooks/01_eda.ipynb` importing from `alerts/`: all-unit daily duration over
time with reform dates marked; weekday profile; unit x month duration heatmap; count and
duration distributions; rolling 28-day mean per unit. `outputs/eda_notes.md`: 5
findings, each tied to a chart.
Done when: Restart and Run All succeeds; 5 charts saved to `outputs/figures/`.

## T04 Features, models A and B, backtest
Scope: `features.py` (SPEC §7); `models.py` with A1, A2, B (SPEC §8); `backtest.py`
(SPEC §9); `tests/test_leakage.py`.
Done when: `outputs/backtest_predictions.csv` and `outputs/metrics.csv` exist for the
test window; the `train.date.max() < D` assert runs every iteration; the leakage test
passes; test and validation dates are printed.

## T05 Forecast, evaluation report, README
Scope: `report.py`: forecast CSV for the next local date from the latest snapshot
(SPEC §10); `outputs/evaluation.md` with date ranges, snapshot time, metrics table,
per-day spread, bootstrap intervals and 3 charts (predicted vs observed, MAE by unit,
per-day MAE); README with setup, run command, Jupyter usage, data definitions,
limitations and the disclaimer.
Done when: the forecast has 25 rows or documented exclusions; README commands work in
a new terminal.

## T06 Model C
Scope: C1 and C2 as SPEC §8 in `models.py` and `backtest.py`; a model C section in
`evaluation.md` with a verdict that respects the bootstrap interval.
Done when: N and k are chosen on validation only and printed; the past-only cluster fit
is asserted; the reform-versus-regime comparison is reported.

## T07 Reproducibility check
Scope: clone into a temporary folder, create a fresh venv, run the README commands; fix
only reproducibility problems.
Done when: the fresh clone reproduces `outputs/metrics.csv`.

## Retry notes
One line per discarded attempt: task, date, what went wrong, what to do differently.
