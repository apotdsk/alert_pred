"""Baseline and pooled forecasting models."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from alerts.config import RANDOM_SEED, UNIT_AREAS
from alerts.features import feature_columns


def baseline_predictions(train: pd.DataFrame, test: pd.DataFrame,
                         target: str) -> tuple[np.ndarray, np.ndarray]:
    """Predict with per-unit means and medians of the last seven complete days."""
    recent = train[train["complete"] & train[target].notna()].groupby(
        "unit", sort=False).tail(7)
    means = recent.groupby("unit")[target].mean()
    medians = recent.groupby("unit")[target].median()
    return (test["unit"].map(means).to_numpy(float),
            test["unit"].map(medians).to_numpy(float))


def pooled_predictions(train: pd.DataFrame, test: pd.DataFrame, target: str) -> np.ndarray:
    """Fit and predict the pooled absolute-error gradient-boosting model."""
    columns = feature_columns(target)
    estimator = HistGradientBoostingRegressor(
        loss="absolute_error", categorical_features=[0], random_state=RANDOM_SEED)
    estimator.fit(train[columns], train[target])
    return estimator.predict(test[columns])


def add_unit_codes(frame: pd.DataFrame) -> pd.DataFrame:
    """Add stable integer codes for the configured categorical unit feature."""
    result = frame.copy()
    result["unit_code"] = result["unit"].map(
        {unit: index for index, unit in enumerate(UNIT_AREAS)})
    return result
