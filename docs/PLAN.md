# PLAN

Statuses: Todo, In progress, Done. Codex sets Done at Close only after the owner writes "Approved".
Gates: Plan = propose a plan and wait. Decision = the owner settles open items in
DECISIONS.md before the next task starts.

| ID  | Task                                    | Gate     | Status |
|-----|-----------------------------------------|----------|--------|
| T00 | Scaffold                                | -        | Done   |
| T01 | Data audit                              | Decision | Done   |
| T02 | Episodes, labels, panel                 | Plan     | Done   |
| T03 | Exploratory analysis                    | -        | Done   |
| T04 | Features, models A and B, backtest      | Plan     | Done   |
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
D-01 to D-05. 
Out of scope: episodes, labels, models.
Done when: every item of SPEC §5 appears in the audit; `python run.py audit` exits 0. 

## T02 Episodes, labels, panel
Scope: `episodes.py` (covering rule SPEC §2, merge tolerance SPEC §4); `labels.py`
(windows SPEC §3, labels SPEC §4, coverage SPEC §6); `data/processed/panel.csv`; the
`inspect` command; the invariant check in `run.py`; `tests/test_labels.py` (SPEC §11).
Apply D-01 cleaning (duplicates, end <= start, possible_imputed_end flag) and compute D-05 reform dates into data/processed/reform_dates.csv.
Done when: zero invariant violations; label tests pass; `inspect` prints records,
episodes and labels for any unit-day. reform_dates.csv covers all 23 units.

## T03 Exploratory analysis
Scope: `notebooks/01_eda.ipynb` importing from `alerts/`: all-unit daily duration over
time with reform dates marked; weekday profile; unit x month duration heatmap; count and
duration distributions; rolling 28-day mean per unit. `outputs/eda_notes.md`: 5
findings, each tied to a chart.
Done when: Restart and Run All succeeds; 5 charts saved to `outputs/figures/`.

## T04 Features, models A and B, backtest
Scope: apply D-08 in `labels.py` (Kherson incomplete before 2022-11-11) and regenerate
the panel; `features.py` with cutoff-safe features (SPEC §7–8, `post_reform` from D-05,
0 for units without a reform date); `models.py` with A1, A2 and B (SPEC §8, library
defaults plus `loss="absolute_error"`, no hyperparameter search); `backtest.py` with
the walk-forward loop and metrics (SPEC §9), grouped per D-09; `tests/test_leakage.py`
(SPEC §11).
Out of scope: model C (T06); forecast CSV, evaluation report and charts (T05).
Done when:
- test window (30 dates) and validation window (60 dates before it) are printed; the
  test window ends at the last complete date;
- the `train.date.max() < D` assert runs every iteration; the leakage test passes;
  all earlier tests pass unchanged;
- `outputs/backtest_predictions.csv`: one row per unit, test date, target and model;
- `outputs/metrics.csv`: MAE per target and model for overall, frontline, other
  (D-09) and each unit; versus A1, the share of test days with lower MAE and a 90%
  day-level bootstrap interval of the MAE difference;
- `outputs/daily_metrics.csv`: MAE per test date, target and model;
- Kherson has no complete unit-day before 2022-11-11; invariant violations stay 0;
- `python run.py` finishes in under 5 minutes.

## T05 Forecast, evaluation report, README
Scope: `report.py`:
- forecast per D-10 to `outputs/forecast_<date>.csv` (SPEC §10 columns; data_snapshot
  = last event timestamp);
- `outputs/evaluation.md`: source and snapshot; the 2026-08-30..09-01 source gap and
  its exclusion; validation and test ranges; per target and model for overall,
  frontline and other (D-09): MAE, share of days better than A1, 90% bootstrap
  interval; 3 charts: all-unit daily mean predicted (A1, B) vs observed per target,
  MAE by unit, per-day MAE; verdicts only where the interval excludes 0;
  limitations: data end, single autumn-2025 reform period, Kyiv approximation,
  Luhansk/Crimea excluded, Kherson occupation, imputed ends;
- `README.md`: purpose and advisory disclaimer; setup on Python 3.12 venv; install;
  `python run.py`; Jupyter (kernel registration, notebook path); data definitions
  (units, covering rule, three labels, windows); outputs; link to evaluation.md;
- `requirements.txt`: add `ipykernel` and `notebook`.
Out of scope: model C (T06).
Done when: forecast has 69 rows (23 units x 3 models) within bounds; every number
in evaluation.md matches metrics.csv; README commands work in a new terminal;
`python run.py` finishes in under 5 minutes.

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
