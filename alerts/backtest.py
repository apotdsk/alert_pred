"""Walk-forward backtesting and metric calculation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from alerts.config import (BOOTSTRAP_RESAMPLES, FRONTLINE_UNITS, RANDOM_SEED,
                           UNIT_AREAS)
from alerts.features import TARGETS
from alerts.labels import day_windows
from alerts.models import add_unit_codes, baseline_predictions, pooled_predictions


def select_windows(panel: pd.DataFrame) -> tuple[list[object], list[object]]:
    """Select the accepted 60-date validation and final 30-date test windows."""
    complete_counts = panel[panel["complete"]].groupby("date")["unit"].nunique()
    eligible = sorted(complete_counts[complete_counts.eq(len(UNIT_AREAS))].index)
    if len(eligible) < 90:
        raise ValueError("fewer than 90 dates are complete for every unit")
    test = eligible[-30:]
    return eligible[-90:-30], test


def clip_predictions(values: np.ndarray, target: str, day: object) -> np.ndarray:
    """Clip predictions to the target's valid bounds for the local date."""
    upper = np.inf
    if target == "alert_duration_minutes":
        start, end, _, _ = day_windows(day)
        upper = (end - start).total_seconds() / 60
    elif target == "business_hours_duration_minutes":
        upper = 960
    return np.clip(values, 0, upper)


def walk_forward(features: pd.DataFrame, test_dates: list[object]) -> pd.DataFrame:
    """Refit A1, A2, and B for every test date and target."""
    frame = add_unit_codes(features)
    rows: list[pd.DataFrame] = []
    for day in test_dates:
        train = frame[(frame["date"] < day) & frame["complete"]].copy()
        test = frame[(frame["date"] == day) & frame["complete"]].copy()
        if train.empty or train["date"].max() >= day:
            raise AssertionError(f"training data reaches prediction date {day}")
        for target in TARGETS:
            a1, a2 = baseline_predictions(train, test, target)
            predictions = {"A1": a1, "A2": a2,
                           "B": pooled_predictions(train, test, target)}
            for model, values in predictions.items():
                part = test[["date", "unit", target]].rename(columns={target: "actual"})
                part = part.assign(target=target, model=model,
                                   prediction=clip_predictions(values, target, day))
                rows.append(part[["date", "unit", "target", "model", "actual", "prediction"]])
    return pd.concat(rows, ignore_index=True)


def calculate_metrics(predictions: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Calculate daily, reporting-group, and unit MAE with bootstrap comparisons."""
    scored = predictions.assign(
        absolute_error=lambda x: (x["prediction"] - x["actual"]).abs())
    daily_parts = []
    memberships = [("overall", "overall", scored),
                   ("reporting_group", "frontline",
                    scored[scored["unit"].isin(FRONTLINE_UNITS)]),
                   ("reporting_group", "other",
                    scored[~scored["unit"].isin(FRONTLINE_UNITS)])]
    memberships += [("unit", unit, scored[scored["unit"].eq(unit)])
                    for unit in UNIT_AREAS]
    for group_type, group, subset in memberships:
        daily = subset.groupby(["date", "target", "model"], as_index=False)[
            "absolute_error"].mean()
        daily_parts.append(daily.assign(group_type=group_type, group=group))
    daily_metrics = pd.concat(daily_parts, ignore_index=True).rename(
        columns={"absolute_error": "mae"})
    rng = np.random.default_rng(RANDOM_SEED)
    output = []
    for (group_type, group, target, model), values in daily_metrics.groupby(
            ["group_type", "group", "target", "model"], sort=False):
        current = values.set_index("date")["mae"].sort_index()
        baseline = daily_metrics[(daily_metrics["group_type"] == group_type)
                                 & (daily_metrics["group"] == group)
                                 & (daily_metrics["target"] == target)
                                 & (daily_metrics["model"] == "A1")].set_index(
                                     "date")["mae"].sort_index()
        difference = current - baseline
        samples = rng.choice(difference.to_numpy(),
                             (BOOTSTRAP_RESAMPLES, len(difference)),
                             replace=True).mean(axis=1)
        output.append({"group_type": group_type, "group": group, "target": target,
                       "model": model, "mae": current.mean(),
                       "share_days_lower_than_a1": (current < baseline).mean(),
                       "mae_difference_vs_a1_ci90_low": np.quantile(samples, .05),
                       "mae_difference_vs_a1_ci90_high": np.quantile(samples, .95)})
    return pd.DataFrame(output), daily_metrics
