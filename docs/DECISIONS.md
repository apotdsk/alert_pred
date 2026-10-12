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