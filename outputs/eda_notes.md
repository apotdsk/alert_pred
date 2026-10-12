# Exploratory analysis notes

Only complete unit-days are included. These summaries are descriptive and do not make
model or evaluation choices.

1. **The annual trend changes materially over the sample.** All-unit mean daily alert
   duration in minutes by year was 2022: 114.3; 2023: 116.9; 2024: 207.1; 2025: 256.0; 2026: 315.8. See
   [`eda_all_unit_daily_duration.png`](figures/eda_all_unit_daily_duration.png).
2. **The weekday profile is fairly shallow.** Thursday had the highest mean
   duration (206.4 minutes), versus 186.9 minutes on the
   lowest weekday. See [`eda_weekday_profile.png`](figures/eda_weekday_profile.png).
3. **Frontline units diverge from the rest at the end of the sample.** Final 28-day
   means in minutes were Donetsk: 1391.7; Zaporizhzhia: 1314.6; Sumy: 1180.1; Kharkiv: 1117.7, versus a median of 76.5 among
   the other units. Donetsk's 1391.7 minutes represent
   96.6% of a 1,440-minute day. See
   [`eda_rolling_28_day_mean_by_unit.png`](figures/eda_rolling_28_day_mean_by_unit.png).
4. **The outcome distributions contain many quiet days.** 28.8% of complete
   unit-days have zero episodes, while the duration median is
   89.3 minutes. See
   [`eda_count_duration_distributions.png`](figures/eda_count_duration_distributions.png).
5. **Observed reform dates are concentrated in late 2025.** All 22
   non-missing dates fall from 2025-08 through
   2025-11. Around the median reform date
   (2025-11-01), the comparison does not show a clear level shift:
   259.2 minutes in the 60 days before versus 257.7 in the 60
   days after. See [`eda_all_unit_daily_duration.png`](figures/eda_all_unit_daily_duration.png).
