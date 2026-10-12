"""Synthetic tests for cutoff safety and T04 coverage rules."""

import numpy as np
import pandas as pd

import alerts.backtest as backtest
from alerts.episodes import build_episodes
from alerts.features import TARGETS, build_features, cutoff_state, feature_columns
from alerts.labels import build_panel


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


def test_active_at_cutoff_ignores_future_end():
    early = _records([{"start": "2024-01-01 21:00Z", "end": "2024-01-01 22:30Z"}])
    late = _records([{"start": "2024-01-01 21:00Z", "end": "2024-01-02 03:00Z"}])
    assert cutoff_state(early, "Cherkasy", "2024-01-02") == cutoff_state(
        late, "Cherkasy", "2024-01-02")


def test_record_after_cutoff_cannot_bridge_to_active():
    rows = _records([
        {"start": "2024-01-01 21:00:00Z", "end": "2024-01-01 21:59:30Z"},
        {"start": "2024-01-01 22:00:10Z", "end": "2024-01-01 23:00:00Z"},
    ])
    assert cutoff_state(rows, "Cherkasy", "2024-01-02")["active_at_cutoff"] == 0


def test_label_features_use_prior_dates_only():
    dates = pd.date_range("2024-01-01", periods=35, freq="D").date
    panel = pd.DataFrame({"date": dates, "unit": "Cherkasy", "complete": True,
                          "has_imputed_end": False})
    for target in TARGETS:
        panel[target] = np.arange(len(panel), dtype=float)
    records = _records([{"start": "2023-12-01 00:00Z", "end": "2023-12-01 01:00Z"}])
    reforms = pd.DataFrame({"unit": ["Cherkasy"], "reform_date": [pd.NaT]})
    original = build_features(panel, records, reforms)
    changed_panel = panel.copy()
    changed_panel.loc[changed_panel["date"] >= dates[-1], list(TARGETS)] = 9999
    changed = build_features(changed_panel, records, reforms)
    columns = [column for column in original if "lag_" in column or "rolling_" in column
               or "all_unit" in column or "days_since" in column]
    pd.testing.assert_series_equal(original.iloc[-1][columns], changed.iloc[-1][columns])


def test_incomplete_gap_does_not_advance_label_features():
    dates = pd.date_range("2024-01-01", periods=40, freq="D").date
    panel = pd.DataFrame({"date": dates, "unit": "Cherkasy", "complete": True,
                          "has_imputed_end": False})
    for target in TARGETS:
        panel[target] = np.arange(len(panel), dtype=float)
    gap_dates = dates[32:35]
    panel.loc[panel["date"].isin(gap_dates), "complete"] = False
    panel.loc[panel["date"].isin(gap_dates), list(TARGETS)] = np.nan
    without_gap = panel[~panel["date"].isin(gap_dates)].copy()
    records = _records([{"start": "2023-12-01 00:00Z", "end": "2023-12-01 01:00Z"}])
    reforms = pd.DataFrame({"unit": ["Cherkasy"], "reform_date": [pd.NaT]})
    with_features = build_features(panel, records, reforms).set_index(["unit", "date"])
    without_features = build_features(without_gap, records, reforms).set_index(["unit", "date"])
    label_columns = [column for column in with_features if "lag_" in column
                     or "rolling_" in column or "all_unit" in column
                     or "days_since" in column]
    key = ("Cherkasy", dates[35])
    pd.testing.assert_series_equal(with_features.loc[key, label_columns],
                                   without_features.loc[key, label_columns])


def test_walk_forward_training_precedes_prediction_date(monkeypatch):
    dates = pd.date_range("2024-01-01", periods=3, freq="D").date
    rows = []
    for day in dates:
        row = {"date": day, "unit": "Cherkasy", "complete": True}
        for target in TARGETS:
            row[target] = 1.0
            for column in feature_columns(target):
                row[column] = 0.0
        rows.append(row)
    seen = []
    monkeypatch.setattr(backtest, "baseline_predictions",
                        lambda train, test, target: (np.zeros(len(test)), np.zeros(len(test))))

    def pooled(train, test, target):
        seen.append(train["date"].max())
        return np.zeros(len(test))

    monkeypatch.setattr(backtest, "pooled_predictions", pooled)
    backtest.walk_forward(pd.DataFrame(rows), [dates[-1]])
    assert seen and all(day < dates[-1] for day in seen)


def test_kherson_pre_liberation_is_incomplete():
    source = _records([{"start": f"2022-11-{day:02d} 12:00Z",
                        "end": f"2022-11-{day:02d} 13:00Z"}
                       for day in range(8, 13)])
    snapshot = pd.Timestamp("2022-11-13 12:00Z")
    episodes = build_episodes(source, snapshot)
    episodes.insert(0, "unit", "Cherkasy")
    panel, _ = build_panel(episodes, source, snapshot)
    kherson = panel[panel["unit"].eq("Kherson")].set_index("date")
    assert not bool(kherson.loc[pd.Timestamp("2022-11-10").date(), "complete"])
    assert bool(kherson.loc[pd.Timestamp("2022-11-11").date(), "complete"])
