"""Construct cutoff-safe model features."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from alerts.config import EPISODE_MERGE_TOLERANCE_SECONDS, LOCAL_TIMEZONE, UNIT_AREAS
from alerts.episodes import build_episodes, select_unit_records

TARGETS = ("alert_count", "alert_duration_minutes", "business_hours_duration_minutes")


def _unit_history_features(base: pd.DataFrame, target: str) -> dict[str, pd.Series]:
    """Build target history using only prior complete observations per unit."""
    names = {f"{target}_lag_{lag}": pd.Series(np.nan, index=base.index) for lag in (1, 2, 7)}
    names.update({f"{target}_rolling_{window}": pd.Series(np.nan, index=base.index)
                  for window in (7, 28)})
    days_name = f"{target}_days_since_last_alert"
    names[days_name] = pd.Series(np.nan, index=base.index)
    for _, group in base.groupby("unit", sort=False):
        history: list[float] = []
        last_alert_position: int | None = None
        for row in group.itertuples():
            for lag in (1, 2, 7):
                if len(history) >= lag:
                    names[f"{target}_lag_{lag}"].at[row.Index] = history[-lag]
            for window in (7, 28):
                if len(history) >= window:
                    names[f"{target}_rolling_{window}"].at[row.Index] = float(
                        np.mean(history[-window:]))
            if last_alert_position is not None:
                names[days_name].at[row.Index] = len(history) - last_alert_position
            if bool(row.complete) and pd.notna(getattr(row, target)):
                history.append(float(getattr(row, target)))
                if row.alert_count > 0:
                    last_alert_position = len(history) - 1
    return names


def _all_unit_history_features(base: pd.DataFrame, target: str,
                               dates: list[date]) -> tuple[pd.Series, pd.Series]:
    """Build all-unit history using only prior dates complete for every unit."""
    unit_count = base["unit"].nunique()
    by_date = base.groupby("date")
    eligible = by_date["complete"].agg(["sum", "count"])
    eligible_dates = set(eligible.index[(eligible["sum"] == unit_count)
                                        & (eligible["count"] == unit_count)])
    daily = base[base["date"].isin(eligible_dates)].groupby("date")[target].mean()
    lag_values: dict[date, float] = {}
    mean_values: dict[date, float] = {}
    history: list[float] = []
    for day in dates:
        lag_values[day] = history[-1] if history else np.nan
        mean_values[day] = float(np.mean(history[-7:])) if len(history) >= 7 else np.nan
        if day in eligible_dates:
            history.append(float(daily.loc[day]))
    return base["date"].map(lag_values), base["date"].map(mean_values)


def cutoff_state(records: pd.DataFrame, unit: str, day: date | str) -> dict[str, float]:
    """Return state at C(D) after clipping capital records before the cutoff."""
    cutoff = pd.Timestamp(day).tz_localize(LOCAL_TIMEZONE).tz_convert("UTC")
    rows = select_unit_records(records, unit)
    rows = rows[rows["start"].lt(cutoff)].copy()
    crosses = rows["end"].isna() | rows["end"].gt(cutoff)
    rows["end"] = rows["end"].where(~crosses, cutoff)
    episodes = build_episodes(rows, cutoff)
    if episodes.empty or episodes.iloc[-1]["end"] != cutoff or not crosses.any():
        return {"active_at_cutoff": 0.0, "elapsed_minutes": 0.0}
    elapsed = (cutoff - episodes.iloc[-1]["start"]).total_seconds() / 60
    return {"active_at_cutoff": 1.0, "elapsed_minutes": float(elapsed)}


def _all_cutoff_states(records: pd.DataFrame, dates: list[date]) -> pd.DataFrame:
    """Compute cutoff states for all units and dates with a past-only sweep."""
    tolerance = pd.Timedelta(seconds=EPISODE_MERGE_TOLERANCE_SECONDS)
    snapshot = records["start"].max()
    output: list[dict[str, object]] = []
    cutoffs = [(day, pd.Timestamp(day).tz_localize(LOCAL_TIMEZONE).tz_convert("UTC"))
               for day in dates]
    for unit in UNIT_AREAS:
        rows = select_unit_records(records, unit).dropna(subset=["start"]).copy()
        rows["effective_end"] = rows["end"].fillna(snapshot)
        rows = rows[rows["effective_end"].gt(rows["start"])].sort_values(
            ["start", "effective_end"])
        values = list(rows[["start", "effective_end"]].itertuples(index=False, name=None))
        episodes: list[list[pd.Timestamp]] = []
        cursor = 0
        for day, cutoff in cutoffs:
            while cursor < len(values) and values[cursor][0] < cutoff:
                start, end = values[cursor]
                if not episodes or start - episodes[-1][1] >= tolerance:
                    episodes.append([start, end])
                else:
                    episodes[-1][1] = max(episodes[-1][1], end)
                cursor += 1
            active = bool(episodes and episodes[-1][1] > cutoff)
            output.append({"unit": unit, "date": day,
                           "active_at_cutoff": float(active),
                           "elapsed_minutes": float(
                               (cutoff - episodes[-1][0]).total_seconds() / 60) if active else 0.0})
    return pd.DataFrame(output)


def build_features(panel: pd.DataFrame, records: pd.DataFrame,
                   reforms: pd.DataFrame) -> pd.DataFrame:
    """Build past-only features for every unit-date-target row."""
    base = panel.copy()
    base["date"] = pd.to_datetime(base["date"]).dt.date
    base = base.sort_values(["unit", "date"]).reset_index(drop=True)
    dates = sorted(base["date"].unique())
    base = base.merge(_all_cutoff_states(records, dates), on=["unit", "date"],
                      how="left", validate="one_to_one")
    reform_map = reforms.assign(
        reform_date=pd.to_datetime(reforms["reform_date"], errors="coerce")).set_index("unit")["reform_date"]
    base["post_reform"] = [float(pd.notna(reform_map.get(unit)) and
                                 pd.Timestamp(day) >= reform_map.get(unit))
                           for unit, day in base[["unit", "date"]].itertuples(index=False, name=None)]
    base["weekday"] = pd.to_datetime(base["date"]).dt.weekday
    for target in TARGETS:
        for name, values in _unit_history_features(base, target).items():
            base[name] = values
        all_unit_lag, all_unit_mean = _all_unit_history_features(base, target, dates)
        base[f"{target}_all_unit_lag_1"] = all_unit_lag
        base[f"{target}_all_unit_mean_7"] = all_unit_mean
    return base


def feature_columns(target: str) -> list[str]:
    """Return the model-B columns for one target."""
    return ["unit_code", "weekday", "active_at_cutoff", "elapsed_minutes", "post_reform",
            f"{target}_lag_1", f"{target}_lag_2", f"{target}_lag_7",
            f"{target}_rolling_7", f"{target}_rolling_28",
            f"{target}_all_unit_lag_1", f"{target}_all_unit_mean_7",
            f"{target}_days_since_last_alert"]
