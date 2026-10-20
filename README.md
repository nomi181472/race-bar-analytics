# race-bar-analytics

Animated **race bar charts** for weather analytics — download real historical
weather data, compare the current year day-by-day and hour-by-hour against the
previous five years, and generate videos + an HTML report.

## Contents

- [`weather analytics/`](weather%20analytics/) — the full project
  (scripts, datasets, generated videos, HTML report, and detailed README).

## Quick start

```bash
cd "weather analytics"
python3 fetch_data.py          # daily data  -> karachi_weather_data.json
python3 create_race_video.py   # race bar chart video -> karachi_weather_race_chart.mp4
```

See [`weather analytics/README.md`](weather%20analytics/README.md) for the full
pipeline, data sources, citations, and customisation options.

## Data sources

- Open-Meteo Archive API — ERA5 Reanalysis (Copernicus / ECMWF)
- NASA POWER (NASA Goddard Space Flight Center)
