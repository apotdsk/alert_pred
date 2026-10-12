"""Exploratory summaries and charts for the saved daily label panel."""

from __future__ import annotations

import calendar
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from alerts.config import EDA_NOTES_PATH, FIGURES_DIR, PANEL_PATH, REFORM_DATES_PATH


CHART_PATHS = {
    "daily": FIGURES_DIR / "eda_all_unit_daily_duration.png",
    "weekday": FIGURES_DIR / "eda_weekday_profile.png",
    "heatmap": FIGURES_DIR / "eda_unit_month_duration_heatmap.png",
    "distributions": FIGURES_DIR / "eda_count_duration_distributions.png",
    "rolling": FIGURES_DIR / "eda_rolling_28_day_mean_by_unit.png",
}


def load_eda_inputs(
    panel_path: Path = PANEL_PATH, reform_path: Path = REFORM_DATES_PATH
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load complete daily labels and the accepted per-unit reform dates."""
    panel = pd.read_csv(panel_path, parse_dates=["date"])
    reforms = pd.read_csv(reform_path, parse_dates=["reform_date"])
    panel = panel.loc[panel["complete"]].copy()
    return panel, reforms


def _save(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def create_eda_outputs(
    panel_path: Path = PANEL_PATH,
    reform_path: Path = REFORM_DATES_PATH,
    notes_path: Path = EDA_NOTES_PATH,
) -> dict[str, object]:
    """Create the five T03 charts and an evidence-linked findings report."""
    panel, reforms = load_eda_inputs(panel_path, reform_path)
    figures_dir = notes_path.parent / "figures"
    paths = {key: figures_dir / path.name for key, path in CHART_PATHS.items()}

    daily = panel.groupby("date")["alert_duration_minutes"].mean()
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(daily.index, daily, linewidth=0.8, color="#235789")
    for date in sorted(reforms["reform_date"].dropna().unique()):
        ax.axvline(date, color="#d95f02", linewidth=0.6, alpha=0.18)
    ax.set(title="Mean daily alert duration across units (reforms marked)",
           xlabel="Date", ylabel="Mean duration (minutes per unit-day)")
    ax.grid(axis="y", alpha=0.2)
    _save(fig, paths["daily"])

    panel["weekday"] = panel["date"].dt.dayofweek
    weekday = panel.groupby("weekday")["alert_duration_minutes"].mean().reindex(range(7))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar([calendar.day_abbr[i] for i in range(7)], weekday, color="#4c956c")
    ax.set(title="Alert duration by weekday", xlabel="Weekday",
           ylabel="Mean duration (minutes per unit-day)")
    _save(fig, paths["weekday"])

    monthly = (panel.assign(month=panel["date"].dt.to_period("M").astype(str))
               .pivot_table(index="unit", columns="month", values="alert_duration_minutes",
                            aggfunc="mean"))
    fig, ax = plt.subplots(figsize=(14, 7))
    image = ax.imshow(monthly, aspect="auto", cmap="YlOrRd")
    step = max(1, len(monthly.columns) // 12)
    ticks = np.arange(0, len(monthly.columns), step)
    ax.set_xticks(ticks, monthly.columns[ticks], rotation=45, ha="right")
    ax.set_yticks(np.arange(len(monthly.index)), monthly.index)
    ax.set(title="Mean alert duration by unit and month", xlabel="Month", ylabel="Unit")
    fig.colorbar(image, ax=ax, label="Mean duration (minutes per unit-day)")
    _save(fig, paths["heatmap"])

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].hist(panel["alert_count"], bins=np.arange(-0.5, panel["alert_count"].max() + 1.5),
                 color="#2a9d8f")
    axes[0].set(xlabel="Alert count (episodes per unit-day)", ylabel="Unit-days",
                title="Daily alert count")
    axes[1].hist(panel["alert_duration_minutes"], bins=40, color="#e76f51")
    axes[1].set(xlabel="Alert duration (minutes per unit-day)", ylabel="Unit-days",
                title="Daily alert duration")
    fig.suptitle("Count and duration distributions")
    fig.tight_layout()
    _save(fig, paths["distributions"])

    rolling_source = panel.pivot(index="date", columns="unit", values="alert_duration_minutes")
    rolling = rolling_source.rolling(28, min_periods=28).mean()
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(rolling.index, rolling, linewidth=0.7, alpha=0.75)
    ax.set(title="Rolling 28-day mean alert duration by unit", xlabel="Date",
           ylabel="28-day mean duration (minutes per unit-day)")
    ax.grid(axis="y", alpha=0.2)
    _save(fig, paths["rolling"])

    yearly = daily.groupby(daily.index.year).mean().reindex(range(2022, 2027))
    zero_share = panel["alert_count"].eq(0).mean()
    weekday_high = calendar.day_name[int(weekday.idxmax())]
    final_rolling = rolling.iloc[-1]
    frontline_units = ["Donetsk", "Zaporizhzhia", "Sumy", "Kharkiv"]
    other_median = final_rolling.drop(frontline_units).median()
    donetsk_day_share = final_rolling["Donetsk"] / 1440
    observed_reforms = reforms["reform_date"].dropna()
    median_reform = observed_reforms.median()
    before_mean = daily.loc[(daily.index >= median_reform - pd.Timedelta(days=60))
                            & (daily.index < median_reform)].mean()
    after_mean = daily.loc[(daily.index >= median_reform)
                           & (daily.index < median_reform + pd.Timedelta(days=60))].mean()
    yearly_text = "; ".join(f"{year}: {value:.1f}" for year, value in yearly.items())
    frontline_text = "; ".join(
        f"{unit}: {final_rolling[unit]:.1f}" for unit in frontline_units
    )
    notes = f"""# Exploratory analysis notes

Only complete unit-days are included. These summaries are descriptive and do not make
model or evaluation choices.

1. **The annual trend changes materially over the sample.** All-unit mean daily alert
   duration in minutes by year was {yearly_text}. See
   [`{paths['daily'].name}`](figures/{paths['daily'].name}).
2. **The weekday profile is fairly shallow.** {weekday_high} had the highest mean
   duration ({weekday.max():.1f} minutes), versus {weekday.min():.1f} minutes on the
   lowest weekday. See [`{paths['weekday'].name}`](figures/{paths['weekday'].name}).
3. **Frontline units diverge from the rest at the end of the sample.** Final 28-day
   means in minutes were {frontline_text}, versus a median of {other_median:.1f} among
   the other units. Donetsk's {final_rolling['Donetsk']:.1f} minutes represent
   {donetsk_day_share:.1%} of a 1,440-minute day. See
   [`{paths['rolling'].name}`](figures/{paths['rolling'].name}).
4. **The outcome distributions contain many quiet days.** {zero_share:.1%} of complete
   unit-days have zero episodes, while the duration median is
   {panel['alert_duration_minutes'].median():.1f} minutes. See
   [`{paths['distributions'].name}`](figures/{paths['distributions'].name}).
5. **Observed reform dates are concentrated in late 2025.** All {len(observed_reforms)}
   non-missing dates fall from {observed_reforms.min():%Y-%m} through
   {observed_reforms.max():%Y-%m}. Around the median reform date
   ({median_reform:%Y-%m-%d}), the comparison does not show a clear level shift:
   {before_mean:.1f} minutes in the 60 days before versus {after_mean:.1f} in the 60
   days after. See [`{paths['daily'].name}`](figures/{paths['daily'].name}).
"""
    notes_path.parent.mkdir(parents=True, exist_ok=True)
    notes_path.write_text(notes, encoding="utf-8")
    return {"charts": len(paths), "complete_unit_days": len(panel),
            "date_min": panel["date"].min(), "date_max": panel["date"].max()}
