import json
import os
import base64
import numpy as np
from datetime import datetime

DATA_FILE = 'karachi_weather_data.json'
VIDEO_FILE = 'karachi_weather_race_chart.mp4'
INTRADAY_VIDEO_FILE = 'karachi_weather_intraday_race.mp4'
HTML_OUTPUT = 'karachi_weather_comparison_report.html'

CURRENT_YEAR = 2026
HIST_YEARS = [2021, 2022, 2023, 2024, 2025]
ALL_YEARS = HIST_YEARS + [CURRENT_YEAR]

MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

CITATION_INFO = {
    'source_name': 'Open-Meteo Archive API',
    'url': 'https://open-meteo.com/en/docs/historical-weather-api',
    'api_url': 'https://archive-api.open-meteo.com/v1/archive',
    'dataset': 'ERA5 Reanalysis',
    'provider': 'Copernicus Climate Change Service (C3S) / ECMWF',
    'provider_url': 'https://cds.climate.copernicus.eu/',
    'license': 'CC BY 4.0 (Open-Meteo) — ERA5 data: Copernicus C3S Terms of Use',
    'resolution': '0.25° x 0.25° spatial, hourly & daily temporal',
    'coords': '24.8607° N, 67.0011° E (Karachi, Pakistan)',
    'retrieved': datetime.now().strftime('%Y-%m-%d %H:%M UTC+5')
}

def load_data():
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def get_day_map(data, year):
    """Return dict mapping MM-DD -> record for a given year."""
    day_map = {}
    for rec in data[year]:
        parts = rec['date'].split('-')
        month, day = int(parts[1]), int(parts[2])
        key = f"{month:02d}-{day:02d}"
        day_map[key] = rec
    return day_map

def calculate_daily_comparison(data):
    """For each day of 2026, compare with same day in 2021-2025."""
    curr_map = get_day_map(data, CURRENT_YEAR)
    hist_maps = {y: get_day_map(data, y) for y in HIST_YEARS}

    results = []
    for md_key in sorted(curr_map.keys(), key=lambda x: (int(x[:2]), int(x[3:]))):
        curr = curr_map[md_key]
        if curr['max'] is None or curr['min'] is None:
            continue

        curr_avg = (curr['max'] + curr['min']) / 2

        hist_avgs = []
        for y in HIST_YEARS:
            if md_key in hist_maps[y]:
                h = hist_maps[y][md_key]
                if h['max'] is not None and h['min'] is not None:
                    hist_avgs.append((h['max'] + h['min']) / 2)

        if hist_avgs:
            hist_avg = np.mean(hist_avgs)
            diff = curr_avg - hist_avg
            month = int(md_key[:2])
            results.append({
                'month': month,
                'day': int(md_key[3:]),
                'date': f"{CURRENT_YEAR}-{md_key}",
                'curr_max': round(curr['max'], 1),
                'curr_min': round(curr['min'], 1),
                'curr_avg': round(curr_avg, 1),
                'hist_avg': round(hist_avg, 1),
                'diff': round(diff, 2),
                'hist_temps': [round(t, 1) for t in hist_avgs],
                'historical_daily': {
                    y: (hist_maps[y][md_key]['max'], hist_maps[y][md_key]['min'])
                    for y in HIST_YEARS if md_key in hist_maps[y]
                }
            })
    return results

def get_monthly_summary(results):
    """Compute monthly average differences."""
    monthly = {}
    for r in results:
        m = r['month']
        monthly.setdefault(m, []).append(r['diff'])
    return {m: round(np.mean(v), 2) for m, v in sorted(monthly.items())}

def get_monthly_temps(data):
    """Get monthly average temps for each year."""
    result = {}
    for year in ALL_YEARS:
        result[year] = {}
        month_data = {}
        for rec in data[year]:
            if rec['max'] is not None and rec['min'] is not None:
                m = int(rec['date'].split('-')[1])
                avg = (rec['max'] + rec['min']) / 2
                month_data.setdefault(m, []).append(avg)
        for m, temps in month_data.items():
            result[year][m] = round(np.mean(temps), 1)
    return result

def video_to_base64(path):
    """Read video file and convert to base64 for embedding."""
    if os.path.exists(path):
        with open(path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    return None

def generate_html(results, monthly_diff, monthly_temps, data):
    """Generate complete HTML report."""
    video_b64 = video_to_base64(VIDEO_FILE)
    intraday_b64 = video_to_base64(INTRADAY_VIDEO_FILE)

    warmer_days = sum(1 for r in results if r['diff'] > 0)
    cooler_days = sum(1 for r in results if r['diff'] < 0)
    same_days = sum(1 for r in results if r['diff'] == 0)
    avg_all = round(np.mean([r['diff'] for r in results]), 2)

    # Find extremes
    max_diff = max(results, key=lambda r: r['diff'])
    min_diff = min(results, key=lambda r: r['diff'])

    # Build day-by-day table rows
    table_rows = ""
    for r in results:
        diff_class = "positive" if r['diff'] > 0 else ("negative" if r['diff'] < 0 else "neutral")
        direction = "Warmer" if r['diff'] > 0 else ("Cooler" if r['diff'] < 0 else "Same")

        hist_details = " | ".join([
            f"{y}: {r['historical_daily'][y][0]}°C/{r['historical_daily'][y][1]}°C"
            for y in HIST_YEARS if y in r['historical_daily']
        ])

        table_rows += f"""        <tr>
            <td>{r['date']}</td>
            <td>{r['curr_max']}°C</td>
            <td>{r['curr_min']}°C</td>
            <td>{r['curr_avg']}°C</td>
            <td>{r['hist_avg']}°C</td>
            <td class="{diff_class}">{r['diff']:+.2f}°C</td>
            <td class="{diff_class}">{direction}</td>
            <td class="hist-detail">{hist_details}</td>
        </tr>
"""

    # Monthly summary table
    monthly_rows = ""
    for m in range(1, 13):
        if m in monthly_diff:
            d = monthly_diff[m]
            trend_class = "positive" if d > 0 else "negative"
            trend = "Warmer" if d > 0 else "Cooler"
            yearly_str = " | ".join([f"{monthly_temps[y].get(m, 'N/A')}°C" for y in ALL_YEARS])
            monthly_rows += f"""        <tr>
            <td>{MONTH_NAMES[m-1]}</td>
            {"".join(f"<td>{monthly_temps[y].get(m, 'N/A')}°C</td>" for y in ALL_YEARS)}
            <td class="{trend_class}">{d:+.2f}°C</td>
            <td class="{trend_class}">{trend}</td>
        </tr>
"""

    ci = CITATION_INFO

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Karachi Weather Comparison Report 2026 vs 2021-2025</title>
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, sans-serif; background: #f0f2f5; color: #333; }}
    .container {{ max-width: 1300px; margin: 0 auto; padding: 20px; }}

    .hero {{ background: linear-gradient(135deg, #0f0f23, #1a1a4e, #16213e); color: white;
             padding: 50px 30px; border-radius: 12px; margin-bottom: 25px; text-align: center; }}
    .hero h1 {{ font-size: 32px; margin-bottom: 10px; }}
    .hero p {{ font-size: 16px; color: #bbb; }}

    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 25px; }}
    .card {{ background: white; border-radius: 10px; padding: 20px; text-align: center;
             box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .card .number {{ font-size: 30px; font-weight: bold; color: #1a1a4e; }}
    .card .label {{ font-size: 13px; color: #888; margin-top: 5px; }}

    .section {{ background: white; border-radius: 12px; padding: 30px; margin-bottom: 25px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
    .section h2 {{ font-size: 22px; color: #1a1a4e; margin-bottom: 15px; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
    .section h3 {{ font-size: 17px; color: #333; margin: 15px 0 10px; }}

    video {{ width: 100%; border-radius: 10px; margin: 10px 0; background: #000; }}

    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th {{ background: #1a1a4e; color: white; padding: 10px 8px; text-align: left;
          position: sticky; top: 0; }}
    td {{ padding: 8px; border-bottom: 1px solid #eee; }}
    tr:nth-child(even) {{ background: #f9f9fb; }}
    tr:hover {{ background: #e8ecf5; }}

    .positive {{ color: #e74c3c; font-weight: 600; }}
    .negative {{ color: #27ae60; font-weight: 600; }}
    .neutral {{ color: #888; }}

    .hist-detail {{ font-size: 11px; color: #777; }}
    .table-scroll {{ max-height: 600px; overflow-y: auto; border: 1px solid #ddd; border-radius: 8px; }}

    .highlight {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0;
                  border-left: 4px solid #f0ad4e; }}

    .citation {{ background: #f8f9fa; border-radius: 8px; padding: 20px; font-size: 14px; line-height: 1.7; }}
    .citation a {{ color: #1a1a4e; }}
    .citation ul {{ margin-left: 20px; }}

    .bar {{ display: inline-block; height: 14px; border-radius: 3px; vertical-align: middle; }}

    .note {{ background: #e8f4f8; padding: 15px; border-radius: 8px; border-left: 4px solid #3498db;
             margin: 15px 0; font-size: 14px; }}
</style>
</head>
<body>
<div class="container">

<div class="hero">
    <h1>Karachi Weather Comparison Report</h1>
    <p>Current Year {CURRENT_YEAR} vs Historical Average (2021-2025)</p>
    <p style="margin-top:8px; color:#888;">Every day of {CURRENT_YEAR} compared with the same calendar day across 5 previous years</p>
</div>

<div class="cards">
    <div class="card"><div class="number">{len(results)}</div><div class="label">Days Compared</div></div>
    <div class="card"><div class="number">{warmer_days}</div><div class="label">Days Warmer</div></div>
    <div class="card"><div class="number">{cooler_days}</div><div class="label">Days Cooler</div></div>
    <div class="card"><div class="number">{avg_all:+.2f}°C</div><div class="label">Overall Avg Diff</div></div>
    <div class="card"><div class="number">{max_diff['diff']:+.1f}°C</div><div class="label">Max Warming ({max_diff['date']})</div></div>
    <div class="card"><div class="number">{min_diff['diff']:+.1f}°C</div><div class="label">Max Cooling ({min_diff['date']})</div></div>
</div>

<div class="section">
    <h2>Animated Race Bar Chart — Day by Day</h2>
    <p style="margin-bottom:15px; color:#666;">Each frame shows one calendar day. Bars are the average temperature of that specific day in each year ({', '.join(str(y) for y in ALL_YEARS)}). Watch how {CURRENT_YEAR} ranks against the 5 previous years as the calendar advances.</p>
"""

    if video_b64:
        html += f'    <video controls autoplay muted loop>\n        <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">\n        Your browser does not support the video tag.\n    </video>\n'
    else:
        html += f'    <p style="color:red;">Video file not found: {VIDEO_FILE}</p>\n'

    html += f"""    <div class="note">
        <strong>How to read:</strong> Each colored bar represents one year. Bars are sorted by temperature
        (highest at top). Each frame = one calendar day (e.g., Jan 15), comparing that same day across
        2021-2026. When the {CURRENT_YEAR} bar rises to the top, that day was warmer than history.
    </div>
</div>

<div class="section">
    <h2>Animated Race Bar Chart — Intraday (Hour by Hour)</h2>
    <p style="margin-bottom:15px; color:#666;">Temperature is not constant through a day — it changes every hour. This video animates through all 24 hours (00:00 → 23:00) for each month, showing the average temperature at that hour for each year. This reveals Karachi's daily temperature cycle and where {CURRENT_YEAR} diverges.</p>
"""

    if intraday_b64:
        html += f'    <video controls muted loop>\n        <source src="data:video/mp4;base64,{intraday_b64}" type="video/mp4">\n        Your browser does not support the video tag.\n    </video>\n'
    else:
        html += f'    <p style="color:red;">Video file not found: {INTRADAY_VIDEO_FILE}</p>\n'

    html += f"""    <div class="note">
        <strong>How to read:</strong> Each frame is one hour of the day for a given month, averaged across
        all days in that month from Open-Meteo hourly data. You can see the temperature climb from early
        morning to afternoon and fall again at night — and how {CURRENT_YEAR}'s hourly temperatures compare
        with the 2021-2025 average at each hour.
    </div>
</div>

<div class="section">
    <h2>Monthly Temperature Summary ({CURRENT_YEAR} vs 2021-2025)</h2>
    <p style="margin-bottom:10px; color:#666;">Average monthly temperatures for each year, and the difference between {CURRENT_YEAR} and the 5-year historical average.</p>
    <table>
        <thead>
            <tr>
                <th>Month</th>
                {"".join(f"<th>{y}</th>" for y in ALL_YEARS)}
                <th>{CURRENT_YEAR} Diff</th>
                <th>Trend</th>
            </tr>
        </thead>
        <tbody>
{monthly_rows}        </tbody>
    </table>
</div>

<div class="section">
    <h2>Day-by-Day Comparison</h2>
    <div class="highlight">
        <strong>Methodology:</strong> Each day of {CURRENT_YEAR} (e.g., 2026-01-14) is compared with
        the same calendar day in 2021, 2022, 2023, 2024, and 2025. The <em>Difference</em> column shows:
        <br><code>({CURRENT_YEAR} avg temperature) − (average of 2021-2025 for that same day)</code>
        <br>Positive = warmer than history. Negative = cooler than history.
    </div>

    <div class="note">
        <strong>Most Warmer Day:</strong> {max_diff['date']} ({max_diff['diff']:+.2f}°C — Current: {max_diff['curr_avg']}°C vs Hist: {max_diff['hist_avg']}°C)
        &nbsp;|&nbsp;
        <strong>Most Cooler Day:</strong> {min_diff['date']} ({min_diff['diff']:+.2f}°C — Current: {min_diff['curr_avg']}°C vs Hist: {min_diff['hist_avg']}°C)
    </div>

    <div class="table-scroll">
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>{CURRENT_YEAR} Max</th>
                    <th>{CURRENT_YEAR} Min</th>
                    <th>{CURRENT_YEAR} Avg</th>
                    <th>Hist Avg (5yr)</th>
                    <th>Difference</th>
                    <th>Direction</th>
                    <th>Individual Year Details (Max/Min)</th>
                </tr>
            </thead>
            <tbody>
{table_rows}            </tbody>
        </table>
    </div>
</div>

<div class="section">
    <h2>Data Source &amp; Citations</h2>
    <div class="citation">
        <h3>Primary Data Source</h3>
        <ul>
            <li><strong>API:</strong> <a href="{ci['url']}" target="_blank">{ci['source_name']}</a></li>
            <li><strong>API Endpoint:</strong> <code>{ci['api_url']}</code></li>
            <li><strong>Dataset:</strong> {ci['dataset']}</li>
            <li><strong>Provider:</strong> <a href="{ci['provider_url']}" target="_blank">{ci['provider']}</a></li>
            <li><strong>Resolution:</strong> {ci['resolution']}</li>
            <li><strong>Location:</strong> {ci['coords']}</li>
            <li><strong>License:</strong> {ci['license']}</li>
            <li><strong>Data Retrieved:</strong> {ci['retrieved']}</li>
        </ul>

        <h3 style="margin-top: 15px;">Full Citations</h3>
        <ul>
            <li>Hersbach, H., et al. (2020). "The ERA5 global reanalysis." <em>Quarterly Journal of the Royal
                Meteorological Society</em>, 146(730), 1999–2049.
                <a href="https://doi.org/10.1002/qj.3803" target="_blank">https://doi.org/10.1002/qj.3803</a></li>
            <li>Copernicus Climate Change Service (C3S) (2017): ERA5: Fifth generation of ECMWF atmospheric
                reanalyses of the global climate. Copernicus Climate Change Service Climate Data Store (CDS).
                <a href="https://doi.org/10.24381/cds.adbb2d47" target="_blank">https://doi.org/10.24381/cds.adbb2d47</a></li>
            <li>Open-Meteo (2024). Historical Weather API Documentation.
                <a href="https://open-meteo.com/en/docs/historical-weather-api" target="_blank">https://open-meteo.com/en/docs/historical-weather-api</a></li>
        </ul>

        <h3 style="margin-top: 15px;">Data Description</h3>
        <p>All temperature data used in this report was downloaded from the Open-Meteo Archive API,
        which serves ERA5 reanalysis data produced by the European Centre for Medium-Range Weather
        Forecasts (ECMWF) under the Copernicus Climate Change Service. The data provides daily
        maximum (<code>temperature_2m_max</code>) and minimum (<code>temperature_2m_min</code>)
        air temperatures at 2 metres above ground level, spatially interpolated to the Karachi
        location (24.8607°N, 67.0011°E).</p>

        <p style="margin-top:10px;"><strong>Coverage:</strong> January 1, 2021 to October 19, 2026
        (the latest available date at time of retrieval). The {CURRENT_YEAR} data covers
        Jan 1 – Oct 19, and all comparisons are limited to days present in both {CURRENT_YEAR}
        and historical years.</p>
    </div>
</div>

</div>
</body>
</html>"""

    with open(HTML_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"HTML report saved: {HTML_OUTPUT} ({os.path.getsize(HTML_OUTPUT)} bytes)")

def main():
    print("Loading data...")
    data = load_data()

    print("Calculating daily comparisons...")
    results = calculate_daily_comparison(data)
    print(f"  {len(results)} days compared")

    monthly_diff = get_monthly_summary(results)
    monthly_temps = get_monthly_temps(data)

    print("Generating HTML report...")
    generate_html(results, monthly_diff, monthly_temps, data)

    print("\n=== SUMMARY ===")
    print(f"Days compared: {len(results)}")
    print(f"Warmer days: {sum(1 for r in results if r['diff'] > 0)}")
    print(f"Cooler days: {sum(1 for r in results if r['diff'] < 0)}")
    print(f"\nMonthly averages (°C):")
    for m in range(1, 13):
        if m in monthly_diff:
            print(f"  {MONTH_NAMES[m-1]:>10}: {monthly_diff[m]:+.2f}°C")

if __name__ == '__main__':
    main()
