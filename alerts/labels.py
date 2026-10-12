"""Construct DST-safe daily alert labels and reporting-reform dates."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from alerts.config import (BUSINESS_END_HOUR, BUSINESS_START_HOUR,
                           KHERSON_LIBERATION_DATE, LOCAL_TIMEZONE, UNIT_AREAS)
from alerts.episodes import unit_record_mask


def day_windows(day: date | str) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    """Return UTC day and business-window bounds for one Kyiv local date."""
    naive_day = pd.Timestamp(day)
    local_start = naive_day.tz_localize(LOCAL_TIMEZONE)
    local_end = (naive_day + pd.DateOffset(days=1)).tz_localize(LOCAL_TIMEZONE)
    business_start = (naive_day + pd.Timedelta(hours=BUSINESS_START_HOUR)).tz_localize(LOCAL_TIMEZONE)
    business_end = (naive_day + pd.Timedelta(hours=BUSINESS_END_HOUR)).tz_localize(LOCAL_TIMEZONE)
    return tuple(value.tz_convert("UTC") for value in
                 (local_start, local_end, business_start, business_end))


def _overlap_minutes(start: pd.Series, end: pd.Series,
                     window_start: pd.Timestamp, window_end: pd.Timestamp) -> pd.Series:
    clipped_start = start.where(start.gt(window_start), window_start)
    clipped_end = end.where(end.lt(window_end), window_end)
    return (clipped_end - clipped_start).dt.total_seconds().clip(lower=0) / 60


def label_unit_day(episodes: pd.DataFrame, day: date | str, *, complete: bool = True) -> dict[str, object]:
    """Calculate the three labels and coverage flags for one unit-day."""
    start, end, business_start, business_end = day_windows(day)
    overlapping = episodes[episodes["start"].lt(end) & episodes["end"].gt(start)]
    has_imputed = bool(overlapping.get("has_imputed_end", pd.Series(False, index=overlapping.index)).any())
    has_open = bool(overlapping.get("has_open_end", pd.Series(False, index=overlapping.index)).any())
    is_complete = bool(complete and not has_open)
    if is_complete:
        duration = float(_overlap_minutes(overlapping["start"], overlapping["end"], start, end).sum())
        business = float(_overlap_minutes(overlapping["start"], overlapping["end"],
                                          business_start, business_end).sum())
        count: float = float(len(overlapping))
    else:
        count = duration = business = np.nan
    return {"alert_count": count, "alert_duration_minutes": duration,
            "business_hours_duration_minutes": business, "complete": is_complete,
            "has_imputed_end": has_imputed}


def source_gaps(frame: pd.DataFrame) -> pd.DataFrame:
    """Return periods longer than 12 hours between consecutive source starts."""
    starts = frame["start"].dropna().drop_duplicates().sort_values().reset_index(drop=True)
    gaps = pd.DataFrame({"start": starts.shift(), "end": starts}).dropna()
    gaps["hours"] = (gaps["end"] - gaps["start"]).dt.total_seconds() / 3600
    return gaps.loc[gaps["hours"].gt(12)].reset_index(drop=True)


def gap_dates(gaps: pd.DataFrame, first_day: date, last_day: date) -> set[date]:
    """Return local dates whose day windows overlap a detected source gap."""
    affected: set[date] = set()
    for day in pd.date_range(first_day, last_day, freq="D").date:
        day_start, day_end, _, _ = day_windows(day)
        if ((gaps["start"] < day_end) & (gaps["end"] > day_start)).any():
            affected.add(day)
    return affected


def _split_episodes_by_day(episodes: pd.DataFrame) -> pd.DataFrame:
    """Split episodes at local day and business-window boundaries in bulk."""
    columns = ["unit", "date", "duration", "business_duration", "episode_count",
               "has_imputed_end", "has_open_end"]
    if episodes.empty:
        return pd.DataFrame(columns=columns)
    work = episodes.reset_index(drop=True).copy()
    work["episode_id"] = work.index
    local_start = work["start"].dt.tz_convert(LOCAL_TIMEZONE)
    local_end = work["end"].dt.tz_convert(LOCAL_TIMEZONE)
    work["first_date"] = local_start.dt.tz_localize(None).dt.normalize()
    work["last_date"] = (local_end - pd.Timedelta(1, unit="ns")).dt.tz_localize(None).dt.normalize()
    spans = (work["last_date"] - work["first_date"]).dt.days.add(1).clip(lower=0)
    pieces = work.loc[work.index.repeat(spans)].copy()
    if pieces.empty:
        return pd.DataFrame(columns=columns)
    offsets = pieces.groupby("episode_id", sort=False).cumcount()
    pieces["date_naive"] = pieces["first_date"] + pd.to_timedelta(offsets, unit="D")
    day_start = pieces["date_naive"].dt.tz_localize(LOCAL_TIMEZONE).dt.tz_convert("UTC")
    day_end = (pieces["date_naive"] + pd.DateOffset(days=1)).dt.tz_localize(
        LOCAL_TIMEZONE).dt.tz_convert("UTC")
    business_start = (pieces["date_naive"] + pd.Timedelta(hours=BUSINESS_START_HOUR)).dt.tz_localize(
        LOCAL_TIMEZONE).dt.tz_convert("UTC")
    business_end = (pieces["date_naive"] + pd.Timedelta(hours=BUSINESS_END_HOUR)).dt.tz_localize(
        LOCAL_TIMEZONE).dt.tz_convert("UTC")
    clipped_start = pieces["start"].where(pieces["start"].gt(day_start), day_start)
    clipped_end = pieces["end"].where(pieces["end"].lt(day_end), day_end)
    pieces["duration"] = (clipped_end - clipped_start).dt.total_seconds() / 60
    business_clipped_start = pieces["start"].where(
        pieces["start"].gt(business_start), business_start)
    business_clipped_end = pieces["end"].where(pieces["end"].lt(business_end), business_end)
    pieces["business_duration"] = (
        (business_clipped_end - business_clipped_start).dt.total_seconds() / 60).clip(lower=0)
    pieces["date"] = pieces["date_naive"].dt.date
    pieces["episode_count"] = 1
    return pieces[columns]


def build_panel(episodes: pd.DataFrame, source: pd.DataFrame,
                snapshot: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the complete unit-date panel through the last covered local day."""
    first_local = source["start"].min().tz_convert(LOCAL_TIMEZONE)
    first_day = (first_local.normalize() + pd.DateOffset(days=1)).date()
    snapshot_local = snapshot.tz_convert(LOCAL_TIMEZONE)
    last_day = (snapshot_local.normalize() - pd.DateOffset(days=1)).date()
    gaps = source_gaps(source) if source["oblast"].nunique() > 1 else source_gaps(source).iloc[0:0]
    incomplete_gap_dates = gap_dates(gaps, first_day, last_day)
    pieces = _split_episodes_by_day(episodes)
    grouped = pieces.groupby(["unit", "date"], sort=False).agg(
        alert_count=("episode_count", "sum"),
        alert_duration_minutes=("duration", "sum"),
        business_hours_duration_minutes=("business_duration", "sum"),
        has_imputed_end=("has_imputed_end", "any"),
        has_open_end=("has_open_end", "any"),
    )
    index = pd.MultiIndex.from_product(
        [UNIT_AREAS, pd.date_range(first_day, last_day, freq="D").date], names=["unit", "date"])
    panel = grouped.reindex(index).reset_index()
    numeric = ["alert_count", "alert_duration_minutes", "business_hours_duration_minutes"]
    panel[numeric] = panel[numeric].fillna(0.0)
    panel[["has_imputed_end", "has_open_end"]] = panel[
        ["has_imputed_end", "has_open_end"]].fillna(False).astype(bool)
    panel["complete"] = ~panel["date"].isin(incomplete_gap_dates) & ~panel["has_open_end"]
    occupied_kherson = panel["unit"].eq("Kherson") & (
        pd.to_datetime(panel["date"]) < pd.Timestamp(KHERSON_LIBERATION_DATE))
    panel.loc[occupied_kherson, "complete"] = False
    panel.loc[~panel["complete"], numeric] = np.nan
    panel = panel.drop(columns="has_open_end")
    return panel[["date", "unit", *numeric, "complete", "has_imputed_end"]], gaps


def compute_reform_dates(frame: pd.DataFrame) -> pd.DataFrame:
    """Compute accepted sustained-majority reporting-reform months for every unit."""
    results = []
    for unit in UNIT_AREAS:
        rows = frame.loc[unit_record_mask(frame, unit)].dropna(subset=["start"]).copy()
        rows["month"] = rows["start"].dt.tz_convert(LOCAL_TIMEZONE).dt.tz_localize(None).dt.to_period("M")
        rows["detailed"] = rows["level"].isin(["raion", "hromada"])
        monthly = rows.groupby("month")["detailed"].mean()
        reform = pd.NaT
        for month in monthly.index:
            run = pd.period_range(month, periods=3, freq="M")
            if all(candidate in monthly.index and monthly.loc[candidate] > .5 for candidate in run):
                reform = month.to_timestamp()
                break
        results.append({"unit": unit, "reform_date": reform})
    return pd.DataFrame(results)


def invariant_violations(panel: pd.DataFrame) -> int:
    """Count violations of the daily-label invariants."""
    complete = panel[panel["complete"]].copy()
    if complete.empty:
        return 0
    day_lengths = complete["date"].map(
        lambda day: (day_windows(day)[1] - day_windows(day)[0]).total_seconds() / 60)
    invalid = ((complete["alert_duration_minutes"] < 0)
               | (complete["alert_duration_minutes"] > day_lengths)
               | (complete["business_hours_duration_minutes"] < 0)
               | (complete["business_hours_duration_minutes"] > 960)
               | (complete["alert_count"].eq(0) != complete["alert_duration_minutes"].eq(0)))
    return int(invalid.sum())
