import requests
import json
import os

KARACHI_LAT = 24.8607
KARACHI_LON = 67.0011
CURRENT_YEAR = 2026
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]
HOURLY_FILE = 'karachi_weather_hourly.json'
API = 'https://archive-api.open-meteo.com/v1/archive'

def fetch_hourly(year):
    end = f'{year}-12-31' if year < CURRENT_YEAR else f'{year}-10-19'
    params = {
        'latitude': KARACHI_LAT,
        'longitude': KARACHI_LON,
        'hourly': 'temperature_2m',
        'timezone': 'Asia/Karachi',
        'start_date': f'{year}-01-01',
        'end_date': end
    }
    print(f"Fetching hourly {year}...")
    r = requests.get(API, params=params, timeout=180)
    r.raise_for_status()
    data = r.json()
    times = data['hourly']['time']
    temps = data['hourly']['temperature_2m']
    records = [{'time': t, 'temp': v} for t, v in zip(times, temps) if v is not None]
    print(f"  {len(records)} hourly records")
    return records

def main():
    if os.path.exists(HOURLY_FILE):
        print(f"{HOURLY_FILE} already exists. Re-fetching to refresh...")

    all_data = {}
    for year in YEARS:
        all_data[str(year)] = fetch_hourly(year)

    with open(HOURLY_FILE, 'w') as f:
        json.dump(all_data, f)
    print(f"\nSaved {HOURLY_FILE}")

if __name__ == '__main__':
    main()
