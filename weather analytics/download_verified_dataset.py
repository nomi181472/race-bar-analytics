import requests
import csv
import os
import json

NASA_URL = 'https://power.larc.nasa.gov/api/temporal/daily/point'
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]
CURRENT_YEAR = 2026
HIST_YEARS = [2021, 2022, 2023, 2024, 2025]
LAT = 24.8607
LON = 67.0011

DATASET_DIR = 'datasets'
os.makedirs(DATASET_DIR, exist_ok=True)

def fetch_nasa_power(start_year, end_year):
    """Fetch daily temperature data from NASA POWER API."""
    start = f'{start_year}0101'
    end = f'{end_year}1231' if end_year < CURRENT_YEAR else f'{end_year}1019'

    params = {
        'parameters': 'T2M_MAX,T2M_MIN,T2M',
        'community': 'AG',
        'longitude': LON,
        'latitude': LAT,
        'start': start,
        'end': end,
        'format': 'JSON'
    }
    print(f"Fetching NASA POWER: {start} to {end}...")
    r = requests.get(NASA_URL, params=params, timeout=120)
    r.raise_for_status()
    data = r.json()
    return data['properties']['parameter']

def save_year_csv(param_data, year):
    """Save one year of data to CSV."""
    path = os.path.join(DATASET_DIR, f'karachi_weather_{year}.csv')
    dates = sorted(param_data['T2M_MAX'].keys())

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'temp_max_c', 'temp_min_c', 'temp_avg_c', 'year', 'month', 'day'])
        for d in dates:
            max_t = param_data['T2M_MAX'][d]
            min_t = param_data['T2M_MIN'][d]
            avg_t = param_data['T2M'][d]
            # NASA uses -999 for missing values
            if max_t == -999 or min_t == -999:
                continue
            y = int(d[:4])
            m = int(d[4:6])
            day = int(d[6:8])
            writer.writerow([f'{y}-{m:02d}-{day:02d}', max_t, min_t, avg_t, y, m, day])

    count = len(dates)
    print(f"  Saved {path} ({count} days)")
    return path

def save_combined_csv(all_params):
    """Save all years into one combined CSV."""
    path = os.path.join(DATASET_DIR, 'karachi_weather_2021_2026_all.csv')
    rows = []
    for year in YEARS:
        if year not in all_params:
            continue
        pd = all_params[year]
        for d in sorted(pd['T2M_MAX'].keys()):
            max_t = pd['T2M_MAX'][d]
            min_t = pd['T2M_MIN'][d]
            avg_t = pd['T2M'][d]
            if max_t == -999 or min_t == -999:
                continue
            y = int(d[:4])
            m = int(d[4:6])
            day = int(d[6:8])
            rows.append([f'{y}-{m:02d}-{day:02d}', max_t, min_t, avg_t, y, m, day])

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'temp_max_c', 'temp_min_c', 'temp_avg_c', 'year', 'month', 'day'])
        writer.writerows(rows)

    print(f"  Saved {path} ({len(rows)} total days)")
    return path

def save_comparison_csv(all_params):
    """Save day-by-day comparison: each 2026 day vs same day in 2021-2025."""
    path = os.path.join(DATASET_DIR, 'karachi_weather_comparison_2026_vs_2021_2025.csv')

    # Build day maps
    day_maps = {}
    for year in YEARS:
        day_maps[year] = {}
        if year not in all_params:
            continue
        pd = all_params[year]
        for d in sorted(pd['T2M_MAX'].keys()):
            max_t = pd['T2M_MAX'][d]
            min_t = pd['T2M_MIN'][d]
            avg_t = pd['T2M'][d]
            if max_t == -999 or min_t == -999:
                continue
            md = f"{int(d[4:6]):02d}-{int(d[6:8]):02d}"
            day_maps[year][md] = {'max': max_t, 'min': min_t, 'avg': avg_t}

    rows = []
    for md in sorted(day_maps[CURRENT_YEAR].keys(), key=lambda x: (int(x[:2]), int(x[3:]))):
        curr = day_maps[CURRENT_YEAR][md]

        hist_avgs = []
        hist_maxes = []
        hist_mins = []
        for hy in HIST_YEARS:
            if md in day_maps[hy]:
                hist_avgs.append(day_maps[hy][md]['avg'])
                hist_maxes.append(day_maps[hy][md]['max'])
                hist_mins.append(day_maps[hy][md]['min'])

        if not hist_avgs:
            continue

        hist_avg = sum(hist_avgs) / len(hist_avgs)
        hist_max_avg = sum(hist_maxes) / len(hist_maxes)
        hist_min_avg = sum(hist_mins) / len(hist_mins)
        diff = curr['avg'] - hist_avg

        m = int(md[:2])
        d = int(md[3:])
        rows.append([
            f'2026-{m:02d}-{d:02d}',
            round(curr['max'], 2),
            round(curr['min'], 2),
            round(curr['avg'], 2),
            round(hist_avg, 2),
            round(hist_max_avg, 2),
            round(hist_min_avg, 2),
            round(diff, 2),
            'Warmer' if diff > 0 else 'Cooler' if diff < 0 else 'Same'
        ])

    with open(path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'date',
            '2026_max_c', '2026_min_c', '2026_avg_c',
            'hist_avg_c_2021_2025', 'hist_max_avg_c', 'hist_min_avg_c',
            'diff_c', 'direction'
        ])
        writer.writerows(rows)

    print(f"  Saved {path} ({len(rows)} comparison rows)")
    return path

def save_metadata():
    """Save source metadata."""
    path = os.path.join(DATASET_DIR, 'README_data_sources.md')
    with open(path, 'w') as f:
        f.write(f"""# Karachi Weather Dataset — Data Sources & Citations

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
- **Retrieved:** {os.popen('date').read().strip()}

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
""")
    print(f"  Saved {path}")

if __name__ == '__main__':
    print("=" * 60)
    print("Downloading Karachi Weather Dataset from NASA POWER")
    print("=" * 60)

    all_params = {}
    for year in YEARS:
        params = fetch_nasa_power(year, year)
        all_params[year] = params
        save_year_csv(params, year)

    print("\nSaving combined dataset...")
    save_combined_csv(all_params)

    print("\nSaving day-by-day comparison...")
    save_comparison_csv(all_params)

    print("\nSaving metadata & citations...")
    save_metadata()

    print("\n" + "=" * 60)
    print("DONE — All files in 'datasets/' directory")
    print("=" * 60)
    for f in sorted(os.listdir(DATASET_DIR)):
        size = os.path.getsize(os.path.join(DATASET_DIR, f))
        print(f"  {f:60s} {size:>10,} bytes")
