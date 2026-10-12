"""Command-line entry point for the alert forecasting pipeline."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

import pandas as pd

from alerts.backtest import calculate_metrics, select_windows, walk_forward
from alerts.config import (BACKTEST_PREDICTIONS_PATH, DAILY_METRICS_PATH,
                           EPISODE_MERGE_TOLERANCE_SECONDS, METRICS_PATH, PANEL_PATH,
                           RAW_DATA_PATH, REFORM_DATES_PATH, UNIT_AREAS)
from alerts.data import acquire_sources, build_audit, clean_official, load_official
from alerts.episodes import build_all_episodes, build_episodes, select_unit_records
from alerts.features import build_features
from alerts.labels import build_panel, compute_reform_dates, invariant_violations
from alerts.report import build_evaluation, build_forecast


STAGES = ("audit", "panel", "backtest", "forecast", "report")


def _panel_data(raw_path: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    official_path = acquire_sources(raw_path)[0] if raw_path is not None else RAW_DATA_PATH
    source = clean_official(load_official(official_path))
    snapshot = source["start"].max()
    episodes = build_all_episodes(source, snapshot)
    panel, gaps = build_panel(episodes, source, snapshot)
    return source, episodes, panel, gaps


def run_panel(raw_path: str | None = None) -> dict[str, object]:
    """Build and save the label panel and accepted reform dates."""
    source, _, panel, gaps = _panel_data(raw_path)
    reforms = compute_reform_dates(source)
    PANEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(PANEL_PATH, index=False)
    reforms.to_csv(REFORM_DATES_PATH, index=False, date_format="%Y-%m-%d")
    violations = invariant_violations(panel)
    if violations:
        raise AssertionError(f"label invariant violations: {violations}")
    complete = panel["complete"]
    complete_imputed = panel.loc[complete, "has_imputed_end"]
    summary = {"unit_days": len(panel), "source_gaps": len(gaps),
               "invariant_violations": violations, "complete_share": complete.mean(),
               "complete_imputed_share": complete_imputed.mean()}
    print(f"panel: {summary['unit_days']} unit-days; source gaps: {summary['source_gaps']}; "
          f"invariant violations: {violations}; complete: {summary['complete_share']:.1%}; "
          f"imputed among complete: {summary['complete_imputed_share']:.1%}")
    for gap in gaps.itertuples(index=False):
        print(f"source gap: {gap.start.isoformat()} to {gap.end.isoformat()} ({gap.hours:.2f} hours)")
    return summary


def run_backtest(raw_path: str | None = None) -> dict[str, object]:
    """Run the A1, A2, and B walk-forward backtest and save its metrics."""
    source, _, panel, _ = _panel_data(raw_path)
    reforms = compute_reform_dates(source)
    validation_dates, test_dates = select_windows(panel)
    reform_months = pd.to_datetime(reforms["reform_date"], errors="coerce").dropna()
    if not reform_months.empty:
        latest_safe_date = (reform_months + pd.DateOffset(months=3)).max().date()
        if min(test_dates) < latest_safe_date:
            raise AssertionError("test dates are not three months after every reform month")
    features = build_features(panel, source, reforms)
    predictions = walk_forward(features, test_dates)
    metrics, daily_metrics = calculate_metrics(predictions)
    BACKTEST_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(BACKTEST_PREDICTIONS_PATH, index=False)
    metrics.to_csv(METRICS_PATH, index=False)
    daily_metrics.to_csv(DAILY_METRICS_PATH, index=False)
    print(f"validation: {validation_dates[0]} through {validation_dates[-1]} (60 dates)")
    print(f"test: {test_dates[0]} through {test_dates[-1]} (30 dates)")
    print(f"backtest: {len(predictions)} predictions; {len(metrics)} metric rows; "
          f"{len(daily_metrics)} daily metric rows")
    return {"validation_dates": validation_dates, "test_dates": test_dates,
            "predictions": len(predictions), "metrics": len(metrics),
            "daily_metrics": len(daily_metrics)}


def run_forecast(raw_path: str | None = None) -> dict[str, object]:
    """Build and save the D-10 live forecast."""
    source, _, panel, _ = _panel_data(raw_path)
    forecast, path = build_forecast(panel, source, compute_reform_dates(source))
    print(f"forecast: {path}; {len(forecast)} rows; date: {forecast['forecast_date'].iloc[0]}")
    return {"path": path, "rows": len(forecast)}


def run_report(raw_path: str | None = None) -> dict[str, object]:
    """Create the evaluation report and its three charts."""
    source, _, _, _ = _panel_data(raw_path)
    path = build_evaluation(source)
    print(f"report: {path}; 3 evaluation charts")
    return {"path": path, "charts": 3}


def inspect_unit_day(unit: str, day: str, raw_path: str | None = None) -> None:
    """Print source records, merged episodes, and labels for one unit-day."""
    if unit not in UNIT_AREAS:
        raise ValueError(f"unknown unit: {unit}")
    if not PANEL_PATH.is_file():
        raise FileNotFoundError(f"build the panel first: {PANEL_PATH}")
    official_path = Path(raw_path) if raw_path is not None else RAW_DATA_PATH
    source = clean_official(load_official(official_path))
    panel = pd.read_csv(PANEL_PATH, parse_dates=["date"])
    local_start = pd.Timestamp(day, tz="Europe/Kyiv").tz_convert("UTC")
    local_end = (pd.Timestamp(day) + pd.DateOffset(days=1)).tz_localize("Europe/Kyiv").tz_convert("UTC")
    unit_records = select_unit_records(source, unit)
    tolerance = pd.Timedelta(seconds=EPISODE_MERGE_TOLERANCE_SECONDS)
    episode_records = unit_records[
        unit_records["start"].lt(local_end + tolerance)
        & (unit_records["end"].isna() | unit_records["end"].gt(local_start - tolerance))]
    episodes = build_episodes(episode_records, source["start"].max())
    records = episode_records[
        episode_records["start"].lt(local_end)
        & (episode_records["end"].isna() | episode_records["end"].gt(local_start))]
    selected_episodes = episodes[episodes["start"].lt(local_end) & episodes["end"].gt(local_start)]
    selected_label = panel[(panel["unit"].eq(unit)) & panel["date"].eq(pd.Timestamp(day))]
    print("records")
    print(records[["oblast", "raion", "hromada", "level", "start", "end",
                   "possible_imputed_end"]].to_string(index=False))
    print("episodes")
    print(selected_episodes.to_string(index=False))
    print("labels")
    print(selected_label.to_string(index=False))


def build_parser() -> argparse.ArgumentParser:
    """Build the pipeline command-line parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-path", help="Use a local raw data file.")
    parser.add_argument("command", nargs="?", choices=(*STAGES, "inspect"))
    parser.add_argument("unit", nargs="?")
    parser.add_argument("date", nargs="?")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch a pipeline stage or print all stages for a full run."""
    args = build_parser().parse_args(argv)
    if args.command == "inspect":
        if not args.unit or not args.date:
            build_parser().error("inspect requires <unit> <YYYY-MM-DD>")
        inspect_unit_day(args.unit, args.date, args.raw_path)
        return 0

    stages = (args.command,) if args.command else STAGES
    for stage in stages:
        if stage == "audit":
            build_audit(args.raw_path)
            print("audit")
        elif stage == "panel":
            run_panel(args.raw_path)
        elif stage == "backtest":
            if args.raw_path is None or isinstance(args.raw_path, (str, Path)):
                run_backtest(args.raw_path)
            else:
                print(stage)
        elif stage == "forecast":
            if args.raw_path is None or isinstance(args.raw_path, (str, Path)):
                run_forecast(args.raw_path)
            else:
                print(stage)
        elif stage == "report":
            if args.raw_path is None or isinstance(args.raw_path, (str, Path)):
                run_report(args.raw_path)
            else:
                print(stage)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
