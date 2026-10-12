# DECISIONS

Settled choices; they override SPEC defaults. Codex appends new entries with status
Proposed; the owner sets Accepted or Rejected.
Format: `## D-XX Title — Status`, then the decision, the reason, the evidence.

## D-01 Source and imputed end times — Accepted
Official dataset `official_data_en.csv`, snapshot ending 2026-09-07 05:28 UTC; the
upstream file has not been updated since. The volunteer dataset is oblast-level only,
so it cannot support the capital rule; it is not used in the pipeline. The report
states the snapshot date as the effective cutoff. Before building episodes: drop
exact duplicate rows and rows with end <= start. Official rows lasting exactly
1800 s are flagged `possible_imputed_end` (the repository documents 30-minute
imputation for missing ends); they are kept, and the share of flagged unit-days
is reported.

## D-02 Units and capital mapping — Accepted
23 units. Each oblast's administrative centre, its raion and its hromada, as listed in
`alerts/config.py`. Donetsk oblast uses Kramatorsk (de facto centre). Kyiv City and Kyiv
oblast share one unit, "Kyiv", built from Kyiv City records. Reason: closest to where
businesses operate; Kyiv oblast businesses get the city forecast as an approximation.

## D-03 Episode merge tolerance — Accepted
60 s. Timestamps have second precision.

## D-04 Luhansk oblast — Accepted
Excluded from training, evaluation and forecasts. Reason: near-permanent alert makes the
forecast trivial and distorts pooled models and metrics. The audit confirms the status.

## D-05 Reporting reform dates — Accepted
A unit's reform date is the first month from which raion- or hromada-level records
make up more than half of the records covering its capital, for at least 3
consecutive months. Units that never meet this (e.g. Kyiv) have no reform date.
Computed from the official data and saved to `data/processed/reform_dates.csv`.
The "first detailed date" table in the T01 audit is not used: one early detailed
record does not mean reporting changed.

## D-06 Minimum dependency versions — Accepted
pandas 2.0, NumPy 1.24, matplotlib 3.7, scikit-learn 1.3, pytest 7.4 as minimum
versions; no upper bounds.

## D-07 Exploratory summary population — Accepted
Complete unit-days only. The all-unit daily value is the mean across complete units
on that date; annual values are the mean of those daily means. The frontline
comparison uses each unit's final 28-day rolling mean versus the median of the other
units. The reform comparison uses the all-unit mean in the 60 days before and after
the median D-05 reform date.

## D-08 Kherson occupation period — Accepted
Kherson unit-days before 2022-11-11 (liberation of Kherson city) are incomplete:
zero alerts there reflect occupation, not quiet days. Labels NaN, excluded from
training and evaluation.

## D-09 Reporting groups — Accepted
Metrics are reported overall and separately for the frontline group (Donetsk,
Kharkiv, Sumy, Zaporizhzhia) and the other 19 units. Reason: the frontline units
approach the 1440-minute ceiling and would otherwise dominate pooled MAE.

## D-10 Bootstrap comparison convention — Proposed
Use seed 42 and 1,000 day-level bootstrap resamples. Report the 5th and 95th
percentiles of model MAE minus A1 MAE, so negative values favour the model.
Reason: SPEC §9 fixes neither the resample count nor the difference direction;
this convention is deterministic and gives the requested 90% interval.
