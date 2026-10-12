"""Select capital-covering alerts and merge them into unit episodes."""

from __future__ import annotations

import pandas as pd

from alerts.config import EPISODE_MERGE_TOLERANCE_SECONDS, UNIT_AREAS


def unit_record_mask(frame: pd.DataFrame, unit: str) -> pd.Series:
    """Return records covering a unit under the accepted capital mapping."""
    oblast, capital = UNIT_AREAS[unit]
    if unit == "Kyiv":
        return frame["oblast"].eq("Kyiv City") & frame["level"].eq("oblast")
    same_oblast = frame["oblast"].eq(oblast)
    oblast_rows = same_oblast & frame["level"].eq("oblast")
    raion_rows = (same_oblast & frame["level"].eq("raion")
                   & frame["raion"].fillna("").str.contains(capital, case=False, regex=False))
    hromada_rows = (same_oblast & frame["level"].eq("hromada")
                     & frame["hromada"].fillna("").str.contains(capital, case=False, regex=False))
    return oblast_rows | raion_rows | hromada_rows


def select_unit_records(frame: pd.DataFrame, unit: str) -> pd.DataFrame:
    """Return source records that cover one configured forecast unit."""
    if unit not in UNIT_AREAS:
        raise ValueError(f"unknown unit: {unit}")
    return frame.loc[unit_record_mask(frame, unit)].copy()


def build_episodes(records: pd.DataFrame, snapshot: pd.Timestamp | None = None) -> pd.DataFrame:
    """Build maximal active-union intervals, merging gaps below the tolerance."""
    columns = ["start", "end", "has_imputed_end", "has_open_end"]
    if records.empty:
        return pd.DataFrame(columns=columns)
    snapshot = pd.Timestamp(snapshot) if snapshot is not None else records["start"].max()
    if snapshot.tzinfo is None:
        snapshot = snapshot.tz_localize("UTC")
    else:
        snapshot = snapshot.tz_convert("UTC")
    rows = records.dropna(subset=["start"]).copy()
    rows["has_open_end"] = rows["end"].isna()
    rows["effective_end"] = rows["end"].fillna(snapshot)
    rows = rows[rows["effective_end"].gt(rows["start"])].sort_values(["start", "effective_end"])
    tolerance = pd.Timedelta(seconds=EPISODE_MERGE_TOLERANCE_SECONDS)
    merged: list[dict[str, object]] = []
    for row in rows.itertuples(index=False):
        start, end = row.start, row.effective_end
        imputed = bool(getattr(row, "possible_imputed_end", getattr(row, "imputed_end", False)))
        is_open = bool(row.has_open_end)
        if not merged or start - merged[-1]["end"] >= tolerance:
            merged.append({"start": start, "end": end, "has_imputed_end": imputed,
                           "has_open_end": is_open})
        else:
            merged[-1]["end"] = max(merged[-1]["end"], end)
            merged[-1]["has_imputed_end"] = merged[-1]["has_imputed_end"] or imputed
            merged[-1]["has_open_end"] = merged[-1]["has_open_end"] or is_open
    return pd.DataFrame(merged, columns=columns)


def build_all_episodes(frame: pd.DataFrame, snapshot: pd.Timestamp) -> pd.DataFrame:
    """Build episodes for all configured units."""
    parts = []
    for unit in UNIT_AREAS:
        episodes = build_episodes(select_unit_records(frame, unit), snapshot)
        episodes.insert(0, "unit", unit)
        parts.append(episodes)
    return pd.concat(parts, ignore_index=True)
