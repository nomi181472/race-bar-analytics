# Karachi Weather Comparison & Race Bar Chart

Download historical daily and hourly weather data for Karachi, compare the current
year day-by-day against the previous five years, and generate animated
**race bar chart** videos plus an HTML report.

The current configuration compares **2026** against **2021–2025**, but every
script is parameterized so you can reuse it for any city, year range, or variable
(temperature, rainfall, etc.).

---

## What it produces

| Output | Description |
|--------|-------------|
| `karachi_weather_race_chart.mp4` | Day-by-day race bar chart (one frame per calendar day) |
| `karachi_weather_intraday_race.mp4` | Hour-by-hour intraday race bar chart (24 hours × 12 months) |
| `karachi_weather_comparison_report.html` | Self-contained HTML report (videos embedded, day table, citations) |
| `karachi_weather_comparison.png` | Static monthly-difference bar chart |
| `datasets/*.csv` | Verified CSV datasets from NASA POWER |

---

## Data sources & citations

All data is **real and verified** — no synthetic data is used by the main pipeline.

### Open-Meteo Archive API (ERA5)

- Docs: <https://open-meteo.com/en/docs/historical-weather-api>
- Endpoint: `https://archive-api.open-meteo.com/v1/archive`
- Dataset: ERA5 Reanalysis (Copernicus Climate Change Service / ECMWF)
- Resolution: 0.25° × 0.25°, **hourly** and **daily**

> Hersbach, H., et al. (2020). "The ERA5 global reanalysis."
> *Quarterly Journal of the Royal Meteorological Society*, 146(730), 1999–2049.
> DOI: <https://doi.org/10.1002/qj.3803>
>
> Copernicus Climate Change Service (C3S) (2017). ERA5.
> DOI: <https://doi.org/10.24381/cds.adbb2d47>

### NASA POWER

- Site: <https://power.larc.nasa.gov/>
- Endpoint: `https://power.larc.nasa.gov/api/temporal/daily/point`
- Variables: `T2M_MAX`, `T2M_MIN`, `T2M`

> Sparks, A.H. (2018). "NASA POWER climatology of solar and meteorological
> parameters." *Theoretical and Applied Climatology*, 134(1), 555–562.
> DOI: <https://doi.org/10.1007/s00704-017-2130-4>

---

## Project structure

```
.
├── fetch_data.py                  # Download daily data (Open-Meteo Archive)
├── fetch_hourly.py                # Download hourly data (Open-Meteo Archive)
├── download_verified_dataset.py   # Download verified CSVs (NASA POWER)
├── create_race_video.py           # Day-by-day race bar chart -> MP4
├── create_intraday_video.py       # Hour-by-hour intraday race chart -> MP4
├── generate_final_report.py       # Build the HTML report (embeds videos)
├── weather_analysis.py            # Simple static bar chart (matplotlib)
├── generate_html_report.py        # Early prototype (synthetic data)
├── datasets/                      # Verified CSV exports + data README
├── karachi_weather_data.json      # Daily data cache (2021–2026)
├── karachi_weather_hourly.json    # Hourly data cache (2021–2026)
└── karachi_weather_*              # Generated videos / report / chart
```

> `weather_analysis.py` and `generate_html_report.py` are earlier prototypes that
> use generated sample data. The **main pipeline** is the five scripts listed
> first and described below.

---

## Requirements

- Python 3.9+
- Packages:

```bash
pip install requests numpy matplotlib
```

- **FFmpeg** is required to write MP4 videos (matplotlib's `FFMpegWriter`):

```bash
# Ubuntu / Debian
sudo apt install ffmpeg
# macOS
brew install ffmpeg
```

---

## Quick start — regenerate everything

Run the scripts from the project root, in this order:

```bash
# 1. Download daily data (2021–2026) -> karachi_weather_data.json
python3 fetch_data.py

# 2. Download hourly data (2021–2026) -> karachi_weather_hourly.json
python3 fetch_hourly.py

# 3. (Optional) Download verified CSV datasets from NASA POWER -> datasets/
python3 download_verified_dataset.py

# 4. Build the day-by-day race bar chart video
python3 create_race_video.py

# 5. Build the hour-by-hour intraday race bar chart video
python3 create_intraday_video.py

# 6. Build the final HTML report (embeds both videos + citations)
python3 generate_final_report.py
```

Then open `karachi_weather_comparison_report.html` in any browser.

> Steps 1–2 need internet access. Steps 4–6 work offline from the cached JSON.

---

## How to generate just the race bar chart

The bar-graph (race chart) is fully driven by `create_race_video.py`. Minimum
workflow:

```bash
python3 fetch_data.py          # creates karachi_weather_data.json
python3 create_race_video.py   # creates karachi_weather_race_chart.mp4
```

`create_race_video.py` reads `karachi_weather_data.json`, computes the average
temperature for each calendar day of each year, and animates the bars so they
re-order as the calendar advances.

---

## Customising

### Change the city

Coordinates are defined at the top of each fetch script. For example in
`fetch_data.py`:

```python
KARACHI_LAT = 24.8607
KARACHI_LON = 67.0011
```

Change these to any latitude/longitude, then re-run the fetch + video scripts.

### Change the years

```python
CURRENT_YEAR = 2026
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]
```

Update `CURRENT_YEAR` and `YEARS`, then re-run. The comparison always uses the
current year against all other years in `YEARS`.

### Change the variable

In the fetch scripts, edit the `daily` / `hourly` parameter, e.g.:

```python
'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum'
```

Then update the `build_*` function in the video script to use the new field.

### Adjust animation speed

In `create_race_video.py` / `create_intraday_video.py`:

```python
FPS = 10            # frames per second
HOLD_FRAMES = 2     # frames a day/hour stays still
TRANS_FRAMES = 5    # frames of smooth transition to the next day/hour
```

Increase `HOLD_FRAMES`, `TRANS_FRAMES`, or lower `FPS` to slow the animation down.

### Colours & year labels

`COLORS` maps each year to a fixed colour so a bar keeps its identity as it moves.
Year labels are drawn inside each bar.

### Rank-points score (hourly timestamp race)

`create_hourly_timestamp_race.py` also draws a **cumulative rank-points score**
next to every bar. For each timestamp (hour), every year earns points based on
its temperature rank among all years in `YEARS`:

| Rank | Points | Meaning |
|------|--------|---------|
| 1st (hottest) | 1.00 | Highest temperature at this hour |
| 2nd | 0.83 | Second hottest |
| 3rd | 0.67 | Middle-high |
| 4th | 0.50 | Middle-low |
| 5th | 0.33 | Second coldest |
| 6th (coldest) | 0.17 | Lowest temperature at this hour |

Scores accumulate frame by frame as the video plays. A year's bar shows
`score: X.X` — the running sum of all rank-points earned so far. The higher the
score, the more consistently that year ranked near the top across all hours.

Example: if 2026 is the hottest at 1 AM on Jan 1, its score becomes `1.00`.
If 2022 is second hottest, its score becomes `0.83`, and so on. The score grows
continuously throughout the video.

---

## Methodology

1. For every calendar day `MM-DD` present in the current year, gather that same
   `MM-DD` from the five previous years.
2. Average the five historical temperatures.
3. Difference = `current_year_avg − five_year_avg` for that day.
   - Positive → warmer than history
   - Negative → cooler than history
4. The race chart animates one day (or hour) at a time, sorted by temperature.

---

## License / attribution

Please retain the ERA5/Copernicus and NASA POWER citations when reusing the data
or outputs. See `datasets/README_data_sources.md` for full source details.
