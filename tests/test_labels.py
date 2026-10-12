"""Synthetic integrity tests for episodes and daily labels."""

import pandas as pd

from alerts.episodes import build_episodes, select_unit_records
from alerts.labels import build_panel, day_windows, label_unit_day, source_gaps


def _records(rows):
    frame = pd.DataFrame(rows)
    defaults = {"oblast": "Cherkaska oblast", "raion": None, "hromada": None,
                "level": "oblast", "possible_imputed_end": False}
    for column, value in defaults.items():
        if column not in frame:
            frame[column] = value
    frame["start"] = pd.to_datetime(frame["start"], utc=True)
    frame["end"] = pd.to_datetime(frame["end"], utc=True)
    return frame


def test_cross_midnight():
    episodes = build_episodes(_records([{"start": "2024-01-01 21:30Z", "end": "2024-01-01 22:30Z"}]))
    first = label_unit_day(episodes, "2024-01-01")
    second = label_unit_day(episodes, "2024-01-02")
    assert (first["alert_count"], first["alert_duration_minutes"]) == (1, 30)
    assert (second["alert_count"], second["alert_duration_minutes"]) == (1, 30)


def test_overlaps_union():
    episodes = build_episodes(_records([
        {"start": "2024-01-01 10:00Z", "end": "2024-01-01 11:00Z"},
        {"start": "2024-01-01 10:30Z", "end": "2024-01-01 11:30Z"}]))
    label = label_unit_day(episodes, "2024-01-01")
    assert (label["alert_count"], label["alert_duration_minutes"]) == (1, 90)


def test_other_raion_ignored():
    rows = _records([{"level": "raion", "raion": "Umanskyi raion",
                      "start": "2024-01-01 10:00Z", "end": "2024-01-01 11:00Z"}])
    assert select_unit_records(rows, "Cherkasy").empty


def test_merge_tolerance():
    episodes = build_episodes(_records([
        {"start": "2024-01-01 10:00:00Z", "end": "2024-01-01 10:30:00Z"},
        {"start": "2024-01-01 10:30:59Z", "end": "2024-01-01 11:00:00Z"},
        {"start": "2024-01-01 11:01:00Z", "end": "2024-01-01 11:30:00Z"}]))
    assert len(episodes) == 2


def test_dst_day_lengths():
    spring = day_windows("2024-03-31")
    autumn = day_windows("2024-10-27")
    assert (spring[1] - spring[0]).total_seconds() / 60 == 1380
    assert (autumn[1] - autumn[0]).total_seconds() / 60 == 1500


def test_business_window_clipping():
    episodes = build_episodes(_records([{"start": "2024-01-01 03:00Z", "end": "2024-01-01 21:00Z"}]))
    label = label_unit_day(episodes, "2024-01-01")
    assert label["business_hours_duration_minutes"] == 960


def test_coverage_gap_is_nan():
    episodes = build_episodes(_records([{"start": "2024-01-01 10:00Z", "end": "2024-01-01 11:00Z"}]))
    label = label_unit_day(episodes, "2024-01-01", complete=False)
    assert not label["complete"]
    assert pd.isna(label["alert_count"])
    assert pd.isna(label["alert_duration_minutes"])


def test_source_gap_period_makes_every_overlapping_day_incomplete():
    source = _records([
        {"oblast": "Cherkaska oblast", "start": "2024-01-01 04:00Z",
         "end": "2024-01-01 04:30Z"},
        {"oblast": "Vinnytska oblast", "start": "2024-01-03 13:00Z",
         "end": "2024-01-03 13:30Z"},
        {"oblast": "Cherkaska oblast", "start": "2024-01-03 23:00Z",
         "end": "2024-01-03 23:30Z"},
    ])
    episodes = build_episodes(source)
    gaps = source_gaps(source)
    panel, _ = build_panel(episodes.assign(unit="Cherkasy"), source,
                           pd.Timestamp("2024-01-05 00:00Z"))
    cher = panel[panel["unit"].eq("Cherkasy")].set_index("date")
    assert len(gaps) == 1
    assert not cher.loc[pd.Timestamp("2024-01-01").date():
                        pd.Timestamp("2024-01-03").date(), "complete"].any()
