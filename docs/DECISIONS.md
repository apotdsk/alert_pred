# DECISIONS

Settled choices; they override SPEC defaults. Codex appends new entries with status
Proposed; the owner sets Accepted or Rejected.
Format: `## D-XX Title — Status`, then the decision, the reason, the evidence.

## D-01 Source file and imputed end times — Open (settle after T01)
Default: `datasets/official_data_en.csv` from the Vadimkin
ukrainian-air-raid-sirens-dataset on GitHub (MIT licence). Records with imputed ends are
kept and flagged; metrics are reported with and without flagged unit-days.

## D-02 Units and capital mapping — Accepted
23 units. Each oblast's administrative centre, its raion and its hromada, as listed in
`alerts/config.py`. Donetsk oblast uses Kramatorsk (de facto centre). Kyiv City and Kyiv
oblast share one unit, "Kyiv", built from Kyiv City records. Reason: closest to where
businesses operate; Kyiv oblast businesses get the city forecast as an approximation.

## D-03 Episode merge tolerance — Open (settle after T01)
Default: 60 s, assuming minute timestamp precision (confirm in the audit). Shorter gaps
are not an all-clear a business could act on.

## D-04 Luhansk oblast — Accepted
Excluded from training, evaluation and forecasts. Reason: near-permanent alert makes the
forecast trivial and distorts pooled models and metrics. The audit confirms the status.

## D-05 Reporting reform dates — Open (settle after T01)
Per unit, the first date its capital is covered by raion- or hromada-level records
instead of oblast-level only. The audit's table is copied here. These are changes in
alert reporting, not in attack tactics; tactics are model C2's subject.

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
