# Air Raid Alert Forecasting

This Python pipeline forecasts next-day alert count, total alert duration, and
business-hours alert duration for 23 Ukrainian oblast-capital units. It produces
advisory planning information only: it is not an alert or warning system and must
not replace official civil-defence alerts or instructions.

## Setup

Python 3.12 is recommended. In PowerShell, create and activate a virtual environment,
install the dependencies, and run the complete pipeline:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run.py
```

The first run downloads the public source data into `data/raw/`. A local official
CSV can instead be supplied with `python run.py --raw-path <file>`.

To use the exploratory notebook, register the environment and launch Jupyter:

```powershell
python -m ipykernel install --user --name alert-analysis --display-name "Python (alert-analysis)"
python -m notebook notebooks/01_eda.ipynb
```

Select the `Python (alert-analysis)` kernel if Jupyter does not select it automatically.

## Data definitions

The 23 units are the capitals of 22 included oblasts, with Kramatorsk representing
Donetsk, plus a single Kyiv unit. A unit is active when an oblast record, its capital
raion record, or the capital's own hromada record is active. Kyiv uses Kyiv City
records only and approximates Kyiv oblast. Luhansk, Crimea, and Sevastopol are excluded.

For each local Europe/Kyiv date, the pipeline labels:

- `alert_count`: merged alert episodes overlapping the local-day window;
- `alert_duration_minutes`: active minutes in the full local day (23, 24, or 25 hours);
- `business_hours_duration_minutes`: active minutes in `[06:00, 22:00)` local time.

Incomplete unit-days have missing labels and are excluded from training and evaluation.

## Outputs

- `outputs/data_audit.md` and audit figures: source quality and coverage;
- `data/processed/panel.csv`: unit-day labels and coverage flags;
- `outputs/backtest_predictions.csv`, `metrics.csv`, and `daily_metrics.csv`: walk-forward results;
- `outputs/forecast_<YYYY-MM-DD>.csv`: A1, A2, and B forecasts for every unit;
- [`outputs/evaluation.md`](outputs/evaluation.md): evaluation tables, charts, verdicts, and limitations;
- `outputs/eda_notes.md` and `outputs/figures/`: exploratory findings and charts.

Individual stages are available as `python run.py audit`, `panel`, `backtest`,
`forecast`, or `report`. Inspect one unit-day with
`python run.py inspect <unit> <YYYY-MM-DD>`.
