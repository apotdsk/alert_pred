# Evaluation

## Data and windows

- Source: [https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/master/datasets/official_data_en.csv](https://raw.githubusercontent.com/Vadimkin/ukrainian-air-raid-sirens-dataset/master/datasets/official_data_en.csv)
- Data snapshot (last event timestamp): `2026-09-07T05:28:22+00:00`
- The source gap 2026-08-30 through 2026-09-01 is excluded because those dates are not complete for every unit.
- Validation: 2026-06-06 through 2026-08-04 (60 dates)
- Test: 2026-08-05 through 2026-09-06 (30 complete dates)

## Metrics

MAE, share of test days with lower MAE than A1, and the 90% day-bootstrap interval
for MAE difference versus A1 are shown below. Negative differences favor the model.

| group | target | model | mae | share_days_lower_than_a1 | mae_difference_vs_a1_ci90_low | mae_difference_vs_a1_ci90_high |
| --- | --- | --- | --- | --- | --- | --- |
| overall | alert_count | A1 | 1.5320910973084885 | 0 | 0 | 0 |
| overall | alert_count | A2 | 1.5391304347826087 | 0.56666666666666665 | -0.045962732919254602 | 0.0567287784679089 |
| overall | alert_count | B | 1.4169008942154635 | 0.6333333333333333 | -0.18131703965841131 | -0.038439892034030698 |
| overall | alert_duration_minutes | A1 | 94.945531400966203 | 0 | 0 | 0 |
| overall | alert_duration_minutes | A2 | 96.981207729468593 | 0.40000000000000002 | -2.3652946859903401 | 5.9678136645962727 |
| overall | alert_duration_minutes | B | 92.6827007727113 | 0.56666666666666665 | -9.6044782881913395 | 4.1320563860743125 |
| overall | business_hours_duration_minutes | A1 | 70.783316080055201 | 0 | 0 | 0 |
| overall | business_hours_duration_minutes | A2 | 71.389396135265699 | 0.46666666666666667 | -2.5283540372670772 | 3.4919777432712218 |
| overall | business_hours_duration_minutes | B | 67.728671656183664 | 0.53333333333333333 | -6.4162681910289612 | 0.52815614243150999 |
| frontline | alert_count | A1 | 1.926190476190476 | 0 | 0 | 0 |
| frontline | alert_count | A2 | 2.0333333333333332 | 0.40000000000000002 | -0.0035714285714285002 | 0.22380952380952371 |
| frontline | alert_count | B | 1.8935930817839248 | 0.53333333333333333 | -0.1374017499072889 | 0.0723313289279746 |
| frontline | alert_duration_minutes | A1 | 95.214047619047605 | 0 | 0 | 0 |
| frontline | alert_duration_minutes | A2 | 98.925416666666678 | 0.36666666666666659 | -0.52263194444442029 | 7.4667777777778008 |
| frontline | alert_duration_minutes | B | 105.06997942688513 | 0.36666666666666659 | 3.6734124503204 | 16.420952293679296 |
| frontline | business_hours_duration_minutes | A1 | 81.464365079365081 | 0 | 0 | 0 |
| frontline | business_hours_duration_minutes | A2 | 84.431944444444468 | 0.36666666666666659 | -1.7285535714285798 | 7.6190019841269923 |
| frontline | business_hours_duration_minutes | B | 86.696079498753534 | 0.33333333333333331 | -0.039273324606863003 | 10.060269284090571 |
| other | alert_count | A1 | 1.4491228070175437 | 0 | 0 | 0 |
| other | alert_count | A2 | 1.4350877192982461 | 0.53333333333333333 | -0.072932330827067696 | 0.039373433583959797 |
| other | alert_count | B | 1.3165446442010498 | 0.66666666666666663 | -0.21578071313605771 | -0.057660639816433698 |
| other | alert_duration_minutes | A1 | 94.889001670843783 | 0 | 0 | 0 |
| other | alert_duration_minutes | A2 | 96.571900584795316 | 0.43333333333333329 | -3.3410833333333367 | 7.169064745196323 |
| other | alert_duration_minutes | B | 90.074852634990506 | 0.56666666666666665 | -12.801464016990156 | 2.9511803013599569 |
| other | business_hours_duration_minutes | A1 | 68.534674185463658 | 0 | 0 | 0 |
| other | business_hours_duration_minutes | A2 | 68.643596491228067 | 0.53333333333333333 | -3.5182299498746845 | 3.749223475355056 |
| other | business_hours_duration_minutes | B | 63.735533163011041 | 0.56666666666666665 | -9.1509666055992405 | -0.3552162055995508 |

## Charts

![All-unit daily mean predictions versus observed](figures/evaluation_daily_predictions.png)

![MAE by unit](figures/evaluation_mae_by_unit.png)

![Per-day MAE](figures/evaluation_daily_mae.png)

## Verdicts

Verdicts are stated only when the 90% interval excludes zero.

- overall, alert_count, B: better than A1.
- frontline, alert_duration_minutes, B: worse than A1.
- other, alert_count, B: better than A1.
- other, business_hours_duration_minutes, B: better than A1.

## Limitations

- The official source ends at the snapshot above and has not been updated beyond it.
- The data contain only one reporting-reform period, in autumn 2025, limiting evidence about reform effects.
- The Kyiv unit uses Kyiv City records as an approximation for both Kyiv City and Kyiv oblast.
- Luhansk, Crimea, and Sevastopol are excluded; Luhansk's near-permanent alert would distort pooled metrics.
- Kherson dates before 2022-11-11 are excluded because occupation-era zeros do not represent quiet days.
- Exactly-30-minute records are retained as possible imputed ends and may bias duration labels.
