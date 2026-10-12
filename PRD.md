# PRD — Ukraine Air Raid Alert Forecasting

**Version:** 1.0  
**Status:** MVP specification  
**Project type:** Python time-series forecasting / business-continuity analytics  
**Primary forecast issue time:** 00:00 Europe/Kyiv  

## 1. Objective

Build a reproducible Python tool that forecasts air raid alert activity for the next local calendar day across Ukraine's 24 oblasts and Kyiv City (25 geographic units). The intended use is experimental business-continuity planning: estimating potential disruption, **not** replacing official air raid warnings or supporting real-time safety decisions.

**Research hypothesis:** Alert behavior changes over time. Selecting or weighting historical observations from the currently relevant behavior regime might produce better forecasts than using all history. This must be tested against simpler approaches; clustering is not assumed to improve accuracy.

## 2. MVP Outputs

At 00:00 Kyiv local time on date D, produce **one forecast per supported region for the local calendar day D**:

1. `alert_count`: number of distinct continuous alert episodes that overlap any part of day D, **including alerts that began on D−1 and continue after midnight**. Count a single episode at most once per region per day.
2. `alert_duration_minutes`: total time under alert within day D, measured as the **union of alert-active intervals** (overlapping alerts are not double counted).
3. `business_hours_duration_minutes`: total time under alert within the intersection of day D and **06:00–22:00 Europe/Kyiv**, also measured using interval union.

Count and duration targets are different: one continuous alert crossing midnight is counted on both calendar days, while its minutes are apportioned to each day. Overlapping district records must not inflate oblast totals.

**Presentation:** A CSV or DataFrame with `forecast_date`, `region`, the three predicted values, and model identifier. Include a compact model evaluation report and charts. Counts should be presented as nonnegative forecasts; if rounded for display, compute accuracy from unrounded predictions and document the decision. Durations must be constrained to the length of the applicable local-day/business-hours window, including DST transitions.

**Boundary condition:** At forecast issuance, an already-active alert's status and elapsed duration are known, but the time at which it will end is unknown. Only facts available by the issuance cutoff may be used as inputs.

## 3. Geographic Unit and Raw Records

**MVP:** Oblast-level predictions for the 24 oblasts plus Kyiv City. **Future:** district/raion-level predictions for fixed business locations.

Preserve original district identifiers where provided, but do not naively sum district alert counts. Construct region-level active intervals using a documented rule (e.g. oblast considered under alert when at least one covered district/oblast alert is active). Explicitly distinguish what the chosen rule means, and verify that it can be applied consistently across source versions.

An alternative oblast-level source may be used if it is more consistent. Before choosing, inspect latest available coverage, reporting changes, time precision, duplicates, completeness, and whether end times are actual or estimated. Do not silently merge sources with incompatible alert definitions.

## 4. Data Pipeline

1. Download or load the latest available historical alert data; record source, retrieval time, last event timestamp, and limitations.
2. Parse start/end timestamps and convert to `Europe/Kyiv`, retaining timezone-aware datetimes.
3. Normalize geographic identifiers; detect duplicates, missing ends, impossible intervals, and known source-format changes.
4. Reconstruct continuous regional alert episodes according to the documented geographic aggregation rule. Merge overlapping/adjacent source intervals only when justified; preserve episode boundaries for counting.
5. Build a complete `region × local_date` panel. Split intervals at local midnight and at 06:00/22:00 for duration attribution. Derive all three labels.
6. Mark data-coverage gaps as missing/unknown rather than assuming zero alerts. Exclude or handle incomplete observations explicitly.
7. Export the processed panel and a data-quality summary.

**Critical check:** Changes in district-vs-oblast reporting may create false apparent 'regimes'. Inspect this before conducting regime analysis.

## 5. Analysis and Models

Explore trends, weekly patterns, regional variation, counts, duration distributions, and rolling changes. Use only confirmed complete observations for analysis and model training.

Compare the following approaches on identical test dates and targets:

- **A — Simple baseline (P0):** trailing 7-day average (or a documented comparable naive forecast).
- **B — Full-history model (P0):** a straightforward regression model (e.g. scikit-learn Random Forest / HistGradientBoosting) using past alert counts, durations, rolling statistics, weekday/calendar features, and optionally the active-alert state at the issue time.
- **C — Regime-aware comparison (P1):** test recent rolling-window training against regime identification via clustering. Compare shared nationwide versus region-specific regime signals only if time/data are sufficient. Any regime labels, scalers or clusters used for historical forecasts must be learned exclusively from data available at each forecast cutoff.

Use one clear feature/target pipeline for all three outputs; separate models per target are acceptable. Do not build a complex multi-model infrastructure unless it is demonstrably necessary.

## 6. Evaluation and Leakage Controls

- **Test period:** latest 30 **complete, sufficiently covered** local calendar days available at development time; report actual dates. If the most recent data has reporting lag or incomplete coverage, end testing at the latest fully reliable day.
- **Validation:** earlier chronological period for feature/hyperparameter/regime decisions. Do not use test results to choose a model and then present them as unbiased final performance.
- **Backtesting:** walk forward through the test period. For each date D, create predictions at simulated `D 00:00 Europe/Kyiv`. Inputs must have been available then. Previous-day labels may be used only if their full observation was actually available at that cutoff.
- **Feature safety:** lag/rolling features must be shifted appropriately. Fit preprocessing and clustering only on available training history. External published data is excluded from MVP.
- **Metrics:** report MAE separately for count, 24-hour duration, and 06:00–22:00 duration, overall and by region. Compare against baseline A and show charts of predicted versus observed values. Note that MAEs of different targets have different units and are not directly comparable.
- **Integrity tests:** crossing-midnight counts, interval union, local-time / DST boundaries, missing-data treatment, and at least one synthetic no-leakage case.

**Success criterion:** Code runs reproducibly, emits forecasts and valid recent-period evaluation for all supported/covered regions, and transparently compares baseline and model performance. Regime modeling is a research extension, not a prerequisite for a valid MVP, and superiority must never be assumed.

## 7. Technical Stack and Repository

- Python 3.11+, pandas, NumPy, matplotlib, scikit-learn.
- Notebook/Google Colab permitted for exploration; reusable `.py` files preferred for data pipeline, modeling, evaluation and testable logic.
- GitHub repository contains code, `requirements.txt`, `README.md`, small safe sample/processed outputs where license permits, evaluation report, and a documented end-to-end run command.
- Do not depend on an undocumented local file path or secret API key to reproduce the core run. If download requires credentials, document an alternative data-loading path.

## 8. Implementation Priorities

**P0 — Mandatory MVP:** data audit and region semantics; clean and construct daily targets; exploratory analysis; baseline and standard forecasting model; leak-free chronological backtest; three output metrics; reproducible repository and README.

**P1 — Research differentiation:** compare recent-window training against clustering-based regime selection/weighting; investigate nationwide vs region-specific regime definitions; assess whether any gain holds on held-out dates.

**P2 — Product extensions:** custom hours, district-level locations, uncertainty intervals and interactive dashboard.

If time is limited, finish P0 before P1. A robust baseline comparison is preferable to an unverified clustering claim.

## 9. Future Extensions

1. **District/raion forecasting:** Provide more localized estimates for individual business locations. Validate coverage and resolve district administrative boundary/reporting changes first.
2. **Custom business hours:** Allow users to specify opening/closing times and forecast disruption minutes for that window. The MVP uses 06:00–22:00 only.
3. **Seven-day vector forecast:** At a single issuance, generate seven separate forecasts (D through D+6), retaining weekday patterns. Evaluate each horizon independently; do **not** use actual intermediate-day outcomes when forecasting all seven days at once.
4. **Automated updates and retraining:** Ingest new data regularly, audit freshness and quality, and provisionally retrain every 14 days. Re-detect regimes using past-only inputs. Validate updated models against the currently deployed model before replacing it; adjust cadence if performance suggests drift.
5. **Longer horizons:** Weekly/monthly aggregated forecasts, with horizon-specific validation and suitable uncertainty communication.
6. **Business-facing reporting:** Region comparisons, likely disruption during configured hours, dashboard and uncertainty intervals. Predictions remain advisory rather than authoritative warning signals.

## 10. Submission and Definition of Done

Provide three separate application artifacts:

1. GitHub link to a working Python repository.
2. Full plain-text export of the AI-assisted development conversation(s), without reconstructing or selectively editing the history.
3. Approximately 100-word plain-text reflection: what went wrong, what changed and why the final approach is better.

**Done when:** A reviewer can follow the README to run the pipeline, reproduce the dated recent-period evaluation, and inspect three next-day forecasts for each supported region, with transparent data definitions and no future-data leakage.
