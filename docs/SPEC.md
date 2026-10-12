# SPEC — Air Raid Alert Forecasting

Technical contract for the code. Choices in DECISIONS.md override the defaults here.

## 1. Purpose
At 00:00 Europe/Kyiv on date D, forecast three values for local date D for each unit,
using only data available at that moment. The output is advisory planning information,
not a warning system.

## 2. Units
- 23 units: the capitals of 22 oblasts (Kramatorsk for Donetsk oblast) and one Kyiv
  unit that serves both Kyiv City and Kyiv oblast. Luhansk oblast, Crimea and
  Sevastopol are excluded.
- A unit is under alert while any record whose area contains its capital is active:
  - an oblast-level record of that oblast;
  - a raion-level record of the raion containing the capital;
  - a hromada-level record of the capital's own hromada.
- Records for other raions or hromadas of the oblast are ignored.
- The Kyiv unit uses Kyiv City records only; Kyiv oblast records are ignored.
- The mapping (unit -> oblast, capital raion, capital hromada, source names) lives in
  `alerts/config.py` and follows D-02. Unmapped source names are reported, never dropped.
  
## 3. Time
- All timestamps are tz-aware. Store UTC; attribute days in `Europe/Kyiv` via `zoneinfo`.
- Day window W(D) = [local midnight D, local midnight D+1): 1380, 1440 or 1500 minutes.
  Build it from tz-aware local midnights, never as midnight + 24 h.
- Business window B(D) = [06:00, 22:00) local on D: 960 minutes.

## 4. Episodes and labels
- An episode is a maximal interval of the unit's active union. A gap shorter than the
  merge tolerance (D-03) does not end an episode.
- `alert_count`: episodes with positive overlap with W(D), including episodes that
  started before D; each counted once per unit-day.
- `alert_duration_minutes`: length of (union ∩ W(D)) in minutes.
- `business_hours_duration_minutes`: length of (union ∩ B(D)) in minutes.
- Invariants, asserted by `run.py`: 0 <= duration <= length of W(D);
  0 <= business duration <= 960; count = 0 exactly when duration = 0.

## 5. Data audit (`outputs/data_audit.md`)
- Source, retrieval time, last event timestamp, source time zone, timestamp precision.
- Records by level (oblast, raion, hromada) per oblast and month, as a chart.
- Reform date per unit: first date its capital is covered by raion- or hromada-level
  records rather than oblast-level only (D-05).
- Imputed end times: the source flag if present, else exactly-30-minute durations;
  share per unit and year (D-01).
- Duplicates, missing ends, end <= start, overlapping records for the same area.
- Mapping coverage for all 25 units; units under alert most of the last 180 days (D-04).
- Proposed wording for D-01 to D-05, each with its evidence.

## 6. Coverage
- A unit-day is `complete` only if the snapshot covers all of W(D) and no known source
  gap overlaps it. Incomplete unit-days get NaN labels, never 0, and are excluded from
  training and evaluation.
- An alert without an end at snapshot time makes its unit-days incomplete.
- Unit-days containing an imputed end are flagged `has_imputed_end`; handling per D-01.
- Near-permanent-alert units (D-04) are excluded from headline metrics and reported
  separately.

## 7. Leakage rules
- Cutoff C(D) = 00:00 Europe/Kyiv on D.
- Features for D come from raw intervals clipped at C(D). An episode active at C(D)
  contributes `active_at_cutoff = 1` and `elapsed_minutes`; its end is never used.
- Label-based features use dates <= D-1 only, via `shift(1)` on each unit's
  date-sorted series. No centred windows.
- Every fit (model, scaler, clusterer) and every choice (hyperparameters, window, k)
  for D uses dates < D only. `backtest.py` asserts `train.date.max() < D` each iteration.
- The validation window precedes the test window. Test results never feed a choice.
- The live forecast's cutoff is the data snapshot time, written into the output.

## 8. Models
Compared on identical dates and targets. Predictions clipped to [0, window length];
never rounded before metrics.
- A1: mean of the last 7 complete days per unit and target. A2: median of the same.
- B: one pooled `HistGradientBoostingRegressor` per target, `loss="absolute_error"`,
  unit as a categorical feature, full history. Features: lags 1, 2, 7; rolling means
  over 7 and 28 days; all-unit lag-1 and 7-day means; weekday; `active_at_cutoff`;
  `elapsed_minutes`; days since the last alert; `post_reform` (D-05).
- C1: B's features and estimator trained on the last N days only;
  N in {30, 60, 120, 240}, chosen on validation.
- C2: each date described by trailing 14-day behaviour features (mean duration, mean
  count, night-time share, share of units under alert simultaneously). KMeans refit on
  dates < D at every refit; train only on dates in the cluster nearest to the state at
  C(D), minimum 60 dates, else fall back to C1. k in {2, 3, 4}, chosen on validation.
  Report whether cluster boundaries coincide with the D-05 reform dates.
- Refit for every test date. If the backtest exceeds 5 minutes, refit every 7 days and
  record it as a proposed decision.

## 9. Evaluation
- Test window: the last 30 consecutive dates on which every evaluated unit is complete.
  Validation: the 60 complete dates before it. Print both ranges on every run.
- Walk forward: for each test date D, fit on dates < D and predict D.
- Per target and model: MAE overall and per unit; the per-day MAE series; versus A1,
  the share of test days with lower MAE and a 90% bootstrap interval of the MAE
  difference, resampling days.

## 10. Outputs
- `outputs/data_audit.md`, `outputs/eda_notes.md`, `data/processed/panel.csv`
- `outputs/backtest_predictions.csv`, `outputs/metrics.csv`, `outputs/evaluation.md`
- `outputs/forecast_<YYYY-MM-DD>.csv`: forecast_date, region, alert_count,
  alert_duration_minutes, business_hours_duration_minutes, model_id, data_snapshot
- `outputs/figures/*.png`

## 11. Integrity tests
Synthetic intervals only, no network. Only these unless a task asks for more:
- `tests/test_labels.py`: an episode crossing midnight counts on both days with minutes
  split; overlapping records do not double count; a record for another raion of the
  same oblast is ignored; gaps below and above the merge tolerance; DST spring day =
  1380 min and autumn day = 1500 min; business-window clipping; a coverage gap yields
  NaN, not 0.
- `tests/test_leakage.py`: an episode active at C(D) yields identical features for D
  whether it ends at 00:30 or at 05:00.