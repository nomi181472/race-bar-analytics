import requests
import json
import os

KARACHI_LAT = 24.8607
KARACHI_LON = 67.0011
CURRENT_YEAR = 2026
YEARS = [2020, 2021, 2022, 2023, 2024, 2025, 2026]
DATA_FILE = 'karachi_weather_data.json'
API_SOURCE = 'https://archive-api.open-meteo.com/v1/archive'

def fetch_year(year):
    """Fetch real daily weather data for Karachi from Open-Meteo Archive API."""
    url = API_SOURCE
    params = {
        'latitude': KARACHI_LAT,
        'longitude': KARACHI_LON,
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
        'timezone': 'Asia/Karachi',
        'start_date': f'{year}-01-01',
        'end_date': f'{year}-12-31' if year < CURRENT_YEAR else f'{year}-10-19'
    }
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    data = r.json()
    
    daily = data['daily']
    records = []
    for i, date in enumerate(daily['time']):
        records.append({
            'date': date,
            'max': daily['temperature_2m_max'][i],
            'min': daily['temperature_2m_min'][i],
            'precip': daily['precipitation_sum'][i]
        })
    return records

def fetch_all_years():
    """Fetch data for all years and save to JSON."""
    all_data = {}
    for year in YEARS:
        print(f"Fetching {year}...")
        records = fetch_year(year)
        all_data[year] = records
        print(f"  Got {len(records)} days")
    
    with open(DATA_FILE, 'w') as f:
        json.dump(all_data, f)
    print(f"\nData saved to {DATA_FILE}")
    return all_data

def load_data():
    """Load previously fetched data or fetch if not available."""
    if os.path.exists(DATA_FILE):
        print("Loading cached data...")
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return fetch_all_years()

if __name__ == '__main__':
    data = fetch_all_years()
    for year in YEARS:
        print(f"{year}: {len(data[str(year)])} days")
