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

## D-06 Minimum dependency versions — Proposed
Use pandas 2.0, NumPy 1.24, matplotlib 3.7, scikit-learn 1.3 and pytest 7.4 as the
minimum supported versions. Reason: these versions support Python 3.11 and the APIs
required by the specification while avoiding unnecessary upper bounds.

## D-07 Primary source and imputed ends — Proposed
Use `official_data_en.csv` as the primary source and keep `volunteer_data_en.csv` only
as a separately audited comparison candidate; never merge them. The volunteer source
starts earlier and has an explicit `naive` flag, but it is oblast-only and cannot supply
the capital-level coverage required by SPEC §2. Flag volunteer ends only when
`naive=True`; do not infer official imputation from an exact 30-minute duration because
the official file supplies no imputation flag. Evidence: `outputs/data_audit.md` reports
per-unit daily-minute correlation and mean absolute difference for complete overlapping
months 2022-04 through 2026-08.

## D-08 Episode merge tolerance — Proposed
Use 60 seconds. Both audited candidates have second-level timestamps; a 60-second
tolerance absorbs only a sub-minute reporting gap and retains the operational meaning
of a longer all-clear.

## D-09 Reporting reform dates — Proposed
Use these first observed dates on which the configured capital is covered by a raion-
or hromada-level official record: Cherkasy 2022-03-16; Chernihiv 2022-03-22;
Chernivtsi 2022-06-07; Dnipro 2022-03-16; Donetsk/Kramatorsk 2022-03-15;
Ivano-Frankivsk 2025-11-06; Kharkiv 2022-03-16; Kherson 2022-03-28;
Khmelnytskyi 2022-03-15; Kropyvnytskyi 2022-03-16; Kyiv not observed; Lutsk
2025-11-06; Lviv 2025-09-03; Mykolaiv 2022-03-16; Odesa 2022-03-16; Poltava
2022-03-16; Rivne 2022-03-20; Sumy 2022-03-15; Ternopil 2025-11-06; Uzhhorod
2025-11-06; Vinnytsia 2022-06-09; Zaporizhzhia 2022-03-16; Zhytomyr 2022-03-15.
Reason: these dates use the accepted capital covering rule; the volunteer source is
oblast-only and provides no reform evidence.

## D-10 Exploratory summary population — Proposed
Use complete unit-days only for exploratory summaries. Define the all-unit daily value
as the mean across complete units on that date and annual values as the mean of those
daily means. Define the endpoint comparison from each unit's final 28-day rolling mean;
compare the four named frontline units with the median of all other units. Compare the
all-unit mean for the 60 calendar days before and after the median non-missing D-05
reform date. Reason: these definitions keep missing coverage out of descriptive values,
weight dates equally, and make the reported trend and reform comparison reproducible.
