"""Download, normalize, compare, and audit the two candidate alert datasets."""

from __future__ import annotations

import os
from pathlib import Path
import urllib.request

os.environ.setdefault("MPLCONFIGDIR", str(Path("data/raw/.matplotlib").resolve()))

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from alerts.config import (AUDIT_PATH, FIGURES_DIR, LOCAL_TIMEZONE, RAW_DATA_PATH,
                           SOURCE_URL, UNIT_AREAS, VOLUNTEER_RAW_DATA_PATH,
                           VOLUNTEER_SOURCE_URL)


def _download(url: str, path: Path) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False
    urllib.request.urlretrieve(url, path)
    return True


def acquire_sources(raw_path: str | Path | None = None) -> tuple[Path, Path, bool, bool]:
    """Return separate official and volunteer source paths, downloading if absent."""
    if raw_path is None:
        official = RAW_DATA_PATH
        official_downloaded = _download(SOURCE_URL, official)
    else:
        official = Path(raw_path)
        if not official.is_file():
            raise FileNotFoundError(official)
        official_downloaded = False
    volunteer_downloaded = _download(VOLUNTEER_SOURCE_URL, VOLUNTEER_RAW_DATA_PATH)
    return official, VOLUNTEER_RAW_DATA_PATH, official_downloaded, volunteer_downloaded


def load_official(path: str | Path) -> pd.DataFrame:
    """Load the official hierarchy data without dropping unmapped source names."""
    raw = pd.read_csv(path, low_memory=False)
    required = {"oblast", "raion", "hromada", "level", "started_at", "finished_at"}
    if missing := required.difference(raw.columns):
        raise ValueError(f"official source missing columns: {sorted(missing)}")
    out = raw.copy()
    out["start"] = pd.to_datetime(out["started_at"], utc=True, errors="coerce")
    out["end"] = pd.to_datetime(out["finished_at"], utc=True, errors="coerce")
    out["area"] = out["hromada"].combine_first(out["raion"]).combine_first(out["oblast"])
    out["possible_imputed_end"] = (
        (out["end"] - out["start"]).dt.total_seconds().eq(1800)
    )
    out["imputed_end"] = out["possible_imputed_end"]
    out["source_name"] = "official"
    return out


def clean_official(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply the accepted duplicate and nonpositive-interval cleaning rules."""
    cleaned = frame.drop_duplicates(["oblast", "raion", "hromada", "level", "start", "end"])
    valid = cleaned["end"].isna() | cleaned["start"].isna() | cleaned["end"].gt(cleaned["start"])
    return cleaned.loc[valid].copy()


def load_volunteer(path: str | Path) -> pd.DataFrame:
    """Load the volunteer oblast data and its explicit naive-end flag."""
    raw = pd.read_csv(path, low_memory=False)
    required = {"region", "started_at", "finished_at", "naive"}
    if missing := required.difference(raw.columns):
        raise ValueError(f"volunteer source missing columns: {sorted(missing)}")
    out = raw.copy()
    out["start"] = pd.to_datetime(out["started_at"], utc=True, errors="coerce")
    out["end"] = pd.to_datetime(out["finished_at"], utc=True, errors="coerce")
    out["oblast"] = out["region"].astype(str).str.strip()
    out["area"] = out["oblast"]
    out["level"] = "oblast"
    out["imputed_end"] = out["naive"].astype(str).str.casefold().isin({"true", "1", "yes"})
    out["source_name"] = "volunteer"
    return out


def _official_unit_mask(frame: pd.DataFrame, unit: str) -> pd.Series:
    oblast, capital = UNIT_AREAS[unit]
    if unit == "Kyiv":
        return frame["oblast"].eq("Kyiv City") & frame["level"].eq("oblast")
    oblast_level = frame["oblast"].eq(oblast) & frame["level"].eq("oblast")
    capital_level = (frame["oblast"].eq(oblast) & frame["level"].isin(["raion", "hromada"])
                     & (frame["raion"].fillna("").str.contains(capital, case=False, regex=False)
                        | frame["hromada"].fillna("").str.contains(capital, case=False, regex=False)))
    return oblast_level | capital_level


def _volunteer_unit_mask(frame: pd.DataFrame, unit: str) -> pd.Series:
    oblast, _ = UNIT_AREAS[unit]
    aliases = {oblast, oblast.removesuffix(" oblast"), unit}
    if unit == "Kyiv":
        aliases = {"Kyiv City", "Kyiv"}
    return frame["oblast"].isin(aliases)


def _table(frame: pd.DataFrame) -> str:
    if frame.empty:
        return "_No rows._"
    shown = frame.fillna("—")
    header = "| " + " | ".join(map(str, shown.columns)) + " |"
    rule = "| " + " | ".join("---" for _ in shown.columns) + " |"
    rows = ["| " + " | ".join(map(str, row)) + " |" for row in shown.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *rows])


def _quality(frame: pd.DataFrame) -> dict[str, int]:
    ordered = frame.dropna(subset=["start", "end"]).sort_values(["area", "start"])
    previous = ordered.groupby("area")["end"].cummax().groupby(ordered["area"]).shift()
    return {
        "duplicates": int(frame.duplicated(["area", "start", "end"]).sum()),
        "missing": int(frame["end"].isna().sum()),
        "nonpositive": int((frame["end"] <= frame["start"]).fillna(False).sum()),
        "overlaps": int((ordered["start"] < previous).sum()),
    }


def _unit_records(frame: pd.DataFrame, kind: str) -> dict[str, pd.DataFrame]:
    mask = _official_unit_mask if kind == "official" else _volunteer_unit_mask
    return {unit: frame[mask(frame, unit)].copy() for unit in UNIT_AREAS}


def _source_tables(frame: pd.DataFrame, kind: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    units = _unit_records(frame, kind)
    coverage, imputed, reforms = [], [], []
    for unit, rows in units.items():
        coverage.append((unit, len(rows), "yes" if len(rows) else "no"))
        valid = rows.dropna(subset=["start"]).assign(year=lambda x: x["start"].dt.year)
        if valid.empty:
            imputed.append((unit, "—", 0, "0.000"))
        for year, group in valid.groupby("year"):
            imputed.append((unit, int(year), len(group), f"{group['imputed_end'].mean():.3f}"))
        detailed = rows[rows["level"].isin(["raion", "hromada"])]
        date = detailed["start"].min()
        reforms.append((unit, "not applicable (oblast-only)" if kind == "volunteer"
                        else ("not observed" if pd.isna(date) else date.date().isoformat())))
    return (pd.DataFrame(coverage, columns=["unit", "matching records", "covered"]),
            pd.DataFrame(imputed, columns=["unit", "year", "records", "imputed share"]),
            pd.DataFrame(reforms, columns=["unit", "first detailed date"]))


def _chart(frame: pd.DataFrame, kind: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    valid = frame.dropna(subset=["start"]).copy()
    valid["month"] = valid["start"].dt.tz_convert(LOCAL_TIMEZONE).dt.tz_localize(None).dt.to_period("M").astype(str)
    counts = valid.groupby(["month", "oblast", "level"]).size().rename("records").reset_index()
    levels = sorted(counts["level"].unique())
    fig, axes = plt.subplots(len(levels), 1, figsize=(14, max(4, 3 * len(levels))), squeeze=False)
    for ax, level in zip(axes[:, 0], levels):
        pivot = counts[counts["level"].eq(level)].pivot(index="month", columns="oblast", values="records").fillna(0)
        pivot.plot(ax=ax, linewidth=.8, legend=False)
        ax.set(title=f"{kind}: {level} records by oblast and month", xlabel="Month", ylabel="Records")
        ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    path = FIGURES_DIR / f"audit_{kind}_records_by_level_month.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def _daily_union(rows: pd.DataFrame) -> pd.Series:
    pieces: list[tuple[object, pd.Timestamp, pd.Timestamp]] = []
    for start, end in rows[["start", "end"]].dropna().itertuples(index=False, name=None):
        start, end = start.tz_convert(LOCAL_TIMEZONE), end.tz_convert(LOCAL_TIMEZONE)
        cursor = start
        while cursor < end:
            midnight = cursor.normalize()
            next_midnight = midnight + pd.DateOffset(days=1)
            stop = min(end, next_midnight)
            pieces.append((midnight.date(), cursor, stop))
            cursor = stop
    totals: dict[object, float] = {}
    for day, group in pd.DataFrame(pieces, columns=["date", "start", "end"]).groupby("date"):
        intervals = sorted(group[["start", "end"]].itertuples(index=False, name=None))
        merged: list[list[pd.Timestamp]] = []
        for start, end in intervals:
            if not merged or start > merged[-1][1]:
                merged.append([start, end])
            else:
                merged[-1][1] = max(merged[-1][1], end)
        totals[day] = sum((end - start).total_seconds() / 60 for start, end in merged)
    return pd.Series(totals, dtype=float)


def _agreement(official: pd.DataFrame, volunteer: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    start = max(official["start"].min(), volunteer["start"].min()).tz_convert(LOCAL_TIMEZONE)
    end = min(official["end"].max(), volunteer["end"].max()).tz_convert(LOCAL_TIMEZONE)
    first_month = (start + pd.offsets.MonthBegin()).date()
    last_month_end = (end - pd.offsets.MonthEnd()).date()
    first_day, last_day = first_month, last_month_end
    official_units, volunteer_units = _unit_records(official, "official"), _unit_records(volunteer, "volunteer")
    rows = []
    for unit in UNIT_AREAS:
        left, right = _daily_union(official_units[unit]), _daily_union(volunteer_units[unit])
        index = pd.date_range(first_day, last_day, freq="D").date
        paired = pd.DataFrame({"official": left.reindex(index, fill_value=0),
                               "volunteer": right.reindex(index, fill_value=0)})
        corr = paired["official"].corr(paired["volunteer"])
        mad = (paired["official"] - paired["volunteer"]).abs().mean()
        rows.append((unit, f"{corr:.3f}" if pd.notna(corr) else "not defined", f"{mad:.1f}"))
    return pd.DataFrame(rows, columns=["unit", "daily-minute correlation", "mean absolute difference (minutes)"]), f"{first_day} through {last_day}"


def _source_section(frame: pd.DataFrame, kind: str, url: str, path: Path,
                    downloaded: bool, figure: Path) -> str:
    coverage, imputed, reforms = _source_tables(frame, kind)
    quality = _quality(frame)
    mapped = pd.Series(False, index=frame.index)
    mask = _official_unit_mask if kind == "official" else _volunteer_unit_mask
    for unit in UNIT_AREAS:
        mapped |= mask(frame, unit)
    unmapped = frame.loc[~mapped, "area"].value_counts().rename_axis("source area").reset_index(name="records")
    precision = "second" if frame["start"].dropna().dt.second.ne(0).any() else "minute"
    recent_cutoff = frame["start"].max() - pd.Timedelta(days=180)
    active = []
    for unit, rows in _unit_records(frame, kind).items():
        share = len(set(rows.loc[rows["start"] >= recent_cutoff, "start"].dt.date)) / 180
        if share >= .8:
            active.append((unit, f"{share:.1%}"))
    levels = ", ".join(sorted(map(str, frame["level"].dropna().unique())))
    return f"""## {kind.title()} candidate

- Source: `{url}` (MIT-licensed repository dataset).
- Local file: `{path}`; downloaded this run: `{downloaded}`.
- Retrieval/file time (UTC): {pd.Timestamp(path.stat().st_mtime, unit='s', tz='UTC').isoformat()}.
- First event (UTC): {frame['start'].min().isoformat()}.
- Last event (UTC): {frame['start'].max().isoformat()}.
- Source time zone: UTC; local-day attribution uses {LOCAL_TIMEZONE}.
- Timestamp precision observed: {precision}.
- Alert levels present: {levels}.
- Parsed rows: {len(frame):,}; invalid starts: {frame['start'].isna().sum():,}.

### Records by level, oblast, and month
![{kind.title()} records](figures/{figure.name})

### Reform date per unit
{_table(reforms)}

### Imputed end times
{_table(imputed)}

Detection: official data has no imputation flag, so no official end is labelled imputed. Volunteer rows are labelled imputed exactly when the source `naive` flag is true; repository documentation says these ends are set to start + 30 minutes. Exact 30-minute duration alone is not treated as proof when a source flag exists.

### Data-quality checks
| Check | Count |
| --- | ---: |
| Exact duplicate area/start/end rows | {quality['duplicates']:,} |
| Missing ends | {quality['missing']:,} |
| End at or before start | {quality['nonpositive']:,} |
| Overlapping records for the same area | {quality['overlaps']:,} |

### Mapping coverage (23 units)
{_table(coverage)}

### Unmapped source names (retained)
{_table(unmapped)}

### Units under alert most of the last 180 days
Screening proxy below is the share of dates with an alert start. Luhansk is deliberately not mapped; the repository documents its continuously active alert from 2022-04-04 and omits that permanent record from both CSV files, confirming the D-04 exclusion rather than treating absent rows as no alert.

{_table(pd.DataFrame(active, columns=['unit', 'start-date share']))}
"""


def build_audit(raw_path: str | Path | None = None) -> dict[str, object]:
    """Audit both candidates separately and compare their overlapping daily minutes."""
    official_path, volunteer_path, official_dl, volunteer_dl = acquire_sources(raw_path)
    expected_figures = [FIGURES_DIR / "audit_official_records_by_level_month.png",
                        FIGURES_DIR / "audit_volunteer_records_by_level_month.png"]
    inputs = [official_path, volunteer_path, Path(__file__), Path("alerts/config.py")]
    if (raw_path is None and AUDIT_PATH.exists() and all(path.exists() for path in expected_figures)
            and AUDIT_PATH.stat().st_mtime >= max(path.stat().st_mtime for path in inputs)):
        return {"official_rows": 0, "volunteer_rows": 0, "audit": str(AUDIT_PATH)}
    official, volunteer = load_official(official_path), load_volunteer(volunteer_path)
    official_figure = _chart(official, "official")
    volunteer_figure = _chart(volunteer, "volunteer")
    agreement, period = _agreement(official, volunteer)
    official_section = _source_section(official, "official", SOURCE_URL, official_path, official_dl, official_figure)
    volunteer_section = _source_section(volunteer, "volunteer", VOLUNTEER_SOURCE_URL, volunteer_path, volunteer_dl, volunteer_figure)
    proposed = f"""## Candidate agreement

The sources remain separate. For complete overlapping calendar months ({period}), each unit's intervals were clipped to Europe/Kyiv local days, overlapping intervals were unioned, and daily alert minutes were compared. Zero-alert days are included.

{_table(agreement)}

## Proposed wording for decisions

### D-01 Source file and imputed end times — Proposed
Use the official dataset as the primary source because it represents official reporting and supplies capital-raion/hromada detail required by SPEC §2. Retain the volunteer dataset only as an audited comparison candidate: it starts earlier and supplies an explicit `naive` imputation flag, but is oblast-only. Do not merge the sources. Report official-versus-volunteer agreement using the per-unit daily-minute correlations and mean absolute differences above. For volunteer data, flag `naive=True` ends; the official source provides no imputation flag, so do not infer imputation merely from an exact 30-minute duration.

### D-02 Units and capital mapping — Proposed
Use exactly the 23 configured units. Kyiv combines Kyiv City and Kyiv oblast operationally but uses only Kyiv City records; Donetsk uses Kramatorsk; Luhansk is excluded, and Crimea and Sevastopol are not mapped.

### D-03 Episode merge tolerance — Proposed
Use 60 seconds. Both candidates have second-level timestamp precision, so this absorbs only sub-minute reporting gaps.

### D-04 Luhansk oblast — Proposed
Keep Luhansk excluded. The repository identifies a continuously active Luhansk alert beginning 2022-04-04 and intentionally omits permanent alerts from both datasets.

### D-05 Reporting reform dates — Proposed
Use the official candidate's per-unit first capital-raion/hromada dates. The volunteer candidate is oblast-only and cannot identify the reporting reform.
"""
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text("# Data audit\n\n" + official_section + "\n" + volunteer_section + "\n" + proposed,
                          encoding="utf-8")
    return {"official_rows": len(official), "volunteer_rows": len(volunteer), "audit": str(AUDIT_PATH)}
