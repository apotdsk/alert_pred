"""Create the live forecast, evaluation charts, and evaluation report."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from alerts.backtest import clip_predictions
from alerts.config import (BACKTEST_PREDICTIONS_PATH, DAILY_METRICS_PATH,
                           EVALUATION_PATH, FIGURES_DIR, METRICS_PATH,
                           SOURCE_URL, UNIT_AREAS)
from alerts.features import TARGETS, build_features
from alerts.labels import source_gaps
from alerts.models import add_unit_codes, baseline_predictions, pooled_predictions


def build_forecast(panel: pd.DataFrame, records: pd.DataFrame,
                   reforms: pd.DataFrame) -> tuple[pd.DataFrame, Path]:
    """Fit A1, A2, and B before D and save the accepted live forecast."""
    last_complete = pd.to_datetime(panel.loc[panel["complete"], "date"]).max().date()
    forecast_date = (pd.Timestamp(last_complete) + pd.DateOffset(days=1)).date()
    forecast_rows = pd.DataFrame({
        "date": [forecast_date] * len(UNIT_AREAS),
        "unit": list(UNIT_AREAS),
        **{target: [np.nan] * len(UNIT_AREAS) for target in TARGETS},
        "complete": [False] * len(UNIT_AREAS),
        "has_imputed_end": [False] * len(UNIT_AREAS),
    })
    extended_panel = pd.concat([panel, forecast_rows], ignore_index=True)
    features = add_unit_codes(build_features(extended_panel, records, reforms))
    train = features[(features["date"] < forecast_date) & features["complete"]].copy()
    test = features[features["date"].eq(forecast_date)].copy()
    if train.empty or train["date"].max() >= forecast_date:
        raise AssertionError("live forecast training data reaches the forecast date")
    if set(test["unit"]) != set(UNIT_AREAS) or len(test) != len(UNIT_AREAS):
        raise AssertionError(f"forecast date {forecast_date} does not cover all units")

    predictions: dict[str, dict[str, np.ndarray]] = {}
    for target in TARGETS:
        a1, a2 = baseline_predictions(train, test, target)
        predictions[target] = {
            "A1": clip_predictions(a1, target, forecast_date),
            "A2": clip_predictions(a2, target, forecast_date),
            "B": clip_predictions(pooled_predictions(train, test, target), target,
                                  forecast_date),
        }
    rows = []
    snapshot = records["start"].max().isoformat()
    for model in ("A1", "A2", "B"):
        for position, unit in enumerate(test["unit"]):
            rows.append({"forecast_date": forecast_date, "region": unit,
                         **{target: predictions[target][model][position]
                            for target in TARGETS},
                         "model_id": model, "data_snapshot": snapshot})
    forecast = pd.DataFrame(rows)
    path = Path("outputs") / f"forecast_{forecast_date}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    forecast.to_csv(path, index=False)
    if len(forecast) != 69:
        raise AssertionError(f"expected 69 forecast rows, got {len(forecast)}")
    return forecast, path


def _save_charts(predictions: pd.DataFrame, daily: pd.DataFrame) -> list[Path]:
    """Save the three required evaluation charts, each faceted by target."""
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    fig, axes = plt.subplots(3, 1, figsize=(11, 12))
    for ax, target in zip(axes, TARGETS):
        part = predictions[predictions["target"].eq(target)]
        actual = part.groupby("date")["actual"].mean().asfreq("D")
        ax.plot(pd.to_datetime(actual.index), actual, label="Observed", color="black")
        for model in ("A1", "B"):
            values = part[part["model"].eq(model)].groupby("date")["prediction"].mean().asfreq("D")
            ax.plot(pd.to_datetime(values.index), values, label=model)
        ax.set(title=target.replace("_", " "), xlabel="Date", ylabel="Daily mean")
        ax.legend()
    fig.tight_layout()
    paths.append(FIGURES_DIR / "evaluation_daily_predictions.png")
    fig.savefig(paths[-1], dpi=150)
    plt.close(fig)

    scored = predictions.assign(error=lambda x: (x["prediction"] - x["actual"]).abs())
    fig, axes = plt.subplots(3, 1, figsize=(12, 13))
    for ax, target in zip(axes, TARGETS):
        part = scored[scored["target"].eq(target)].groupby(
            ["unit", "model"])["error"].mean().unstack()
        part[["A1", "A2", "B"]].plot.bar(ax=ax)
        ax.set(title=target.replace("_", " "), xlabel="Unit", ylabel="MAE")
        ax.tick_params(axis="x", labelrotation=75)
    fig.tight_layout()
    paths.append(FIGURES_DIR / "evaluation_mae_by_unit.png")
    fig.savefig(paths[-1], dpi=150)
    plt.close(fig)

    overall = daily[(daily["group_type"].eq("overall")) & daily["group"].eq("overall")]
    fig, axes = plt.subplots(3, 1, figsize=(11, 12))
    for ax, target in zip(axes, TARGETS):
        part = overall[overall["target"].eq(target)]
        for model, values in part.groupby("model"):
            series = values.set_index("date")["mae"].sort_index().asfreq("D")
            ax.plot(series.index, series, label=model)
        ax.set(title=target.replace("_", " "), xlabel="Date", ylabel="MAE")
        ax.legend()
    fig.tight_layout()
    paths.append(FIGURES_DIR / "evaluation_daily_mae.png")
    fig.savefig(paths[-1], dpi=150)
    plt.close(fig)
    return paths


def _metrics_table(metrics: pd.DataFrame) -> str:
    selected = metrics[metrics["group_type"].isin(["overall", "reporting_group"])]
    columns = ["group", "target", "model", "mae", "share_days_lower_than_a1",
               "mae_difference_vs_a1_ci90_low", "mae_difference_vs_a1_ci90_high"]
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for values in selected[columns].itertuples(index=False, name=None):
        target = values[1]
        decimals = 3 if target == "alert_count" else 1
        shown = []
        for column, value in zip(columns, values):
            if isinstance(value, float):
                precision = 3 if column == "share_days_lower_than_a1" else decimals
                shown.append(f"{value:.{precision}f}")
            else:
                shown.append(str(value))
        rows.append("| " + " | ".join(shown) + " |")
    return "\n".join([header, rule, *rows])


def build_evaluation(records: pd.DataFrame) -> Path:
    """Write the evaluation report from the persisted backtest artifacts."""
    predictions = pd.read_csv(BACKTEST_PREDICTIONS_PATH, parse_dates=["date"])
    metrics = pd.read_csv(METRICS_PATH)
    daily = pd.read_csv(DAILY_METRICS_PATH, parse_dates=["date"])
    chart_paths = _save_charts(predictions, daily)
    test_dates = sorted(predictions["date"].dt.date.unique())
    validation_end = pd.Timestamp(test_dates[0]) - pd.Timedelta(days=1)
    validation_start = validation_end - pd.Timedelta(days=59)
    gaps = source_gaps(records)
    gap_lines = "\n".join(
        f"- Source gap: `{gap.start.isoformat()}` to `{gap.end.isoformat()}` "
        f"({gap.hours:.2f} hours); all overlapping local dates are excluded."
        for gap in gaps.itertuples(index=False))
    verdicts = []
    candidates = metrics[metrics["group_type"].isin(["overall", "reporting_group"])
                         & ~metrics["model"].eq("A1")]
    for row in candidates.itertuples(index=False):
        if row.mae_difference_vs_a1_ci90_high < 0:
            verdicts.append(f"- {row.group}, {row.target}, {row.model}: better than A1.")
        elif row.mae_difference_vs_a1_ci90_low > 0:
            verdicts.append(f"- {row.group}, {row.target}, {row.model}: worse than A1.")
    verdict_text = "\n".join(verdicts) if verdicts else "No comparison interval excludes zero."
    relative = [path.relative_to(EVALUATION_PATH.parent).as_posix() for path in chart_paths]
    report = f"""# Evaluation

## Data and windows

- Source: [{SOURCE_URL}]({SOURCE_URL})
- Data snapshot (last event timestamp): `{records['start'].max().isoformat()}`
{gap_lines}
- Validation: {validation_start.date()} through {validation_end.date()} (60 dates)
- Test: {test_dates[0]} through {test_dates[-1]} (30 complete dates)

## Metrics

MAE, share of test days with lower MAE than A1, and the 90% day-bootstrap interval
for MAE difference versus A1 are shown below. Negative differences favor the model.

{_metrics_table(metrics)}

## Charts

![All-unit daily mean predictions versus observed]({relative[0]})

![MAE by unit]({relative[1]})

![Per-day MAE]({relative[2]})

## Verdicts

Verdicts are stated only when the 90% interval excludes zero.

{verdict_text}

## Limitations

- The official source ends at the snapshot above and has not been updated beyond it.
- The data contain only one reporting-reform period, in autumn 2025, limiting evidence about reform effects.
- The Kyiv unit uses Kyiv City records as an approximation for both Kyiv City and Kyiv oblast.
- Luhansk, Crimea, and Sevastopol are excluded; Luhansk's near-permanent alert would distort pooled metrics.
- Kherson dates before 2022-11-11 are excluded because occupation-era zeros do not represent quiet days.
- Exactly-30-minute records are retained as possible imputed ends and may bias duration labels.
"""
    EVALUATION_PATH.write_text(report, encoding="utf-8")
    return EVALUATION_PATH
