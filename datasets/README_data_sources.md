# Karachi Weather Dataset — Data Sources & Citations

## Primary Source: NASA POWER (Prediction of Worldwide Energy Resources)

- **Agency:** NASA Goddard Space Flight Center (GSFC)
- **Program:** NASA POWER (Prediction of Worldwide Energy Resources)
- **Website:** https://power.larc.nasa.gov/
- **API Endpoint:** https://power.larc.nasa.gov/api/temporal/daily/point
- **Parameters:** T2M_MAX (max temp), T2M_MIN (min temp), T2M (avg temp at 2m)
- **Spatial Resolution:** ~0.5° x 0.625° (MERRA-2 reanalysis)
- **Temporal Resolution:** Daily
- **Location:** Karachi, Pakistan (24.8607°N, 67.0011°E)
- **Period:** 2021-01-01 to 2026-10-19
- **Retrieved:** Mon Oct 19 06:07:16 PM PKT 2026

### Citation for NASA POWER:

> NASA POWER (2024). Prediction of Worldwide Energy Resources (POWER).
> NASA Goddard Space Flight Center. https://power.larc.nasa.gov/
>
> Reference: Sparks, A.H. (2018). "NASA POWER climatology of solar and meteorological
> parameters." Theoretical and Applied Climatology, 134(1), 555-562.
> DOI: https://doi.org/10.1007/s00704-017-2130-4

## Secondary Source: Open-Meteo Archive API (ERA5 Reanalysis)

- **Provider:** Copernicus Climate Change Service (C3S) / ECMWF
- **API Endpoint:** https://archive-api.open-meteo.com/v1/archive
- **Dataset:** ERA5 Reanalysis
- **Website:** https://open-meteo.com/en/docs/historical-weather-api

### Citation for ERA5:

> Hersbach, H., et al. (2020). "The ERA5 global reanalysis."
> Quarterly Journal of the Royal Meteorological Society, 146(730), 1999-2049.
> DOI: https://doi.org/10.1002/qj.3803
>
> Copernicus Climate Change Service (C3S) (2017). ERA5 data available at the
> Copernicus Climate Change Service Climate Data Store (CDS).
> DOI: https://doi.org/10.24381/cds.adbb2d47

## Dataset Files

| File | Description |
|------|-------------|
| karachi_weather_2021.csv | Daily temps for 2021 |
| karachi_weather_2022.csv | Daily temps for 2022 |
| karachi_weather_2023.csv | Daily temps for 2023 |
| karachi_weather_2024.csv | Daily temps for 2024 |
| karachi_weather_2025.csv | Daily temps for 2025 |
| karachi_weather_2026.csv | Daily temps for 2026 (partial) |
| karachi_weather_2021_2026_all.csv | All years combined |
| karachi_weather_comparison_2026_vs_2021_2025.csv | Day-by-day comparison |

## Methodology

- Each day of 2026 (e.g., 2026-01-15) is compared with the same calendar day
  in 2021, 2022, 2023, 2024, and 2025
- The `diff_c` column = 2026 average temperature - average of 2021-2025 for that day
- Positive diff = warmer than historical average
- Negative diff = cooler than historical average
