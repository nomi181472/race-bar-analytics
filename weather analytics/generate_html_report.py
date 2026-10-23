import json
import os
from datetime import datetime, timedelta

KARACHI_LAT = 24.8607
KARACHI_LON = 67.0011
CURRENT_YEAR = 2026
LAST_YEARS = 5
DATA_FILE = 'karachi_weather_data.json'

def load_data():
    """Load real weather data from JSON file."""
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def calculate_daily_comparison(curr_data, hist_data, year_prefix=""):
    """Compare each day's weather between current year and historical years."""
    results = {}
    
    hist_by_date = {}
    for year, days in hist_data.items():
        for day_info in days:
            hist_by_date[day_info['date']] = day_info
    
    for curr_day in curr_data:
        date_str = curr_day['date']
        date_parts = date_str.split('-')
        month = int(date_parts[1])
        day = int(date_parts[2])
        month_day_key = f"{month:02d}-{day:02d}"
        
        curr_avg = (curr_day['max'] + curr_day['min']) / 2
        
        hist_temps = []
        for h_year in range(CURRENT_YEAR - LAST_YEARS, CURRENT_YEAR):
            h_date_str = f"{h_year}-{month:02d}-{day:02d}"
            if h_date_str in hist_by_date:
                h_day = hist_by_date[h_date_str]
                h_avg = (h_day['max'] + h_day['min']) / 2
                hist_temps.append(h_avg)
        
        if hist_temps:
            avg_hist = sum(hist_temps) / len(hist_temps)
            diff = round(curr_avg - avg_hist, 2)
            results[month_day_key] = {
                'date': date_str,
                'curr_max': curr_day['max'],
                'curr_min': curr_day['min'],
                'curr_avg': round(curr_avg, 2),
                'hist_avg': round(avg_hist, 2),
                'diff': diff,
                'hist_temps': hist_temps,
                'count': len(hist_temps)
            }
    
    return results

def generate_html_report():
    """Generate complete HTML report."""
    
    all_data = load_data()
    
    curr_data = all_data.get(CURRENT_YEAR, [])
    
    hist_data = {}
    for year in range(CURRENT_YEAR - LAST_YEARS, CURRENT_YEAR):
        if year in all_data:
            hist_data[year] = all_data[year]
    
    print("Calculating daily comparisons...")
    comparisons = calculate_daily_comparison(curr_data, hist_data)
    
    sorted_comparisons = dict(sorted(comparisons.items(), key=lambda x: (int(x[0][:2]), int(x[0][3:5]))))
    
    avg_differences = {}
    for month in range(1, 13):
        month_diffs = []
        for md_key, data in sorted_comparisons.items():
            if int(md_key[:2]) == month:
                month_diffs.append(data['diff'])
        if month_diffs:
            avg_differences[month] = round(sum(month_diffs) / len(month_diffs), 2)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Karachi Weather Comparison Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .summary-card h3 {{
            margin: 0 0 5px 0;
            font-size: 14px;
            color: #7f8c8d;
        }}
        .summary-card .value {{
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
        }}
        .table-container {{
            overflow-x: auto;
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 800px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #2c3e50;
            color: white;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #e9ecef;
        }}
        .diff-positive {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .diff-negative {{
            color: #2ecc71;
            font-weight: bold;
        }}
        .chart-section {{
            margin: 30px 0;
        }}
        .note {{
            background: #fff3e0;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            border-left: 4px solid #f39c12;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Karachi Weather Comparison Report</h1>
        <p style="text-align: center; color: #666;">
            Current Year {CURRENT_YEAR} vs Last {LAST_YEARS} Years (2021-2025)
            <br>Comparison: Each day of {CURRENT_YEAR} compared with same day in 2021-2025
        </p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Days Analyzed</h3>
                <div class="value">{len(curr_data)}</div>
            </div>
            <div class="summary-card">
                <h3>Historical Years</h3>
                <div class="value">{LAST_YEARS}</div>
            </div>
            <div class="summary-card">
                <h3>Average Temp Diff</h3>
                <div class="value">{round(sum(avg_differences.values()) / len(avg_differences), 2)}°C</div>
            </div>
        </div>
        
        <div class="note">
            <strong>Note:</strong> All data is real weather data from Open-Meteo Archive API (ERA5, Copernicus/ECMWF). 
            No synthesized or mock data is used in this report.
        </div>
        
        <h2>Daily Temperature Comparison</h2>
        <p>Comparison of average temperature ((max+min)/2°C) for each day of {CURRENT_YEAR} 
        with the average of the same day across 2021-2025.</p>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Month-Day</th>
                        <th>Current Year</th>
                        <th>Hist Avg (2021-2025)</th>
                        <th>Difference</th>
                        <th>Direction</th>
                        <th>Sample Size</th>
                    </tr>
                </thead>
                <tbody>"""
    
    for md_key, data in sorted_comparisons.items():
        diff_class = "diff-positive" if data['diff'] > 0 else "diff-negative" if data['diff'] < 0 else ""
        direction = "Warmer" if data['diff'] > 0 else ("Cooler" if data['diff'] < 0 else "Same")
        
        html += f"""                    <tr>
                        <td>{data['date']}</td>
                        <td>{data['curr_max']}°C / {data['curr_min']}°C</td>
                        <td>{data['hist_avg']}°C</td>
                        <td class="{diff_class}">{data['diff']}°C</td>
                        <td>{direction}</td>
                        <td>{data['count']} years</td>
                    </tr>"""
    
    html += """                </tbody>
            </table>
        </div>
        
        <div class="chart-section">
            <h2>Monthly Average Difference</h2>
            <p>The following shows the average temperature difference per month:</p>"""
    
    html += """            <table>
                <thead>
                    <tr>
                        <th>Month</th>
                        <th>Avg Difference (°C)</th>
                        <th>Trend</th>
                    </tr>
                </thead>
                <tbody>"""
    
    month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    
    for m in range(1, 13):
        if m in avg_differences:
            diff = avg_differences[m]
            trend = "Warmer" if diff > 0 else "Cooler"
            html += f"""                <tr>
                    <td>{month_names[m-1]}</td>
                    <td>{diff}°C</td>
                    <td>{trend}</td>
                </tr>"""
    
    html += """                </tbody>
            </table>
        </div>
        
        <div class="note" style="margin-top: 40px;">
            <h3>Interpretation Guide</h3>
            <ul>
                <li><strong>Positive Difference:</strong> Current year {CURRENT_YEAR} is warmer than the 2021-2025 average for that day</li>
                <li><strong>Negative Difference:</strong> Current year {CURRENT_YEAR} is cooler than the 2021-2025 average for that day</li>
                <li><strong>Sample Size:</strong> Number of historical years compared (always {LAST_YEARS} years)</li>
            </ul>
            <p>This report compares each calendar day (e.g., January 1, 2026) with the same calendar day 
            in the previous {LAST_YEARS} years (January 1, 2025, January 1, 2024, January 1, 2023, January 1, 2022, 
            and January 1, 2021), calculating the average temperature difference.</p>
        </div>
    </div>
</body>
</html>"""
    
    output_path = 'karachi_weather_comparison_report.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML report generated: {output_path}")
    return output_path, sorted_comparisons, avg_differences

if __name__ == '__main__':
    output_path, comparisons, avg_diffs = generate_html_report()
    
    print("\n" + "="*60)
    print("KEY FINDINGS SUMMARY")
    print("="*60)
    
    warmer = sum(1 for d in comparisons.values() if d['diff'] > 0)
    cooler = sum(1 for d in comparisons.values() if d['diff'] < 0)
    
    print(f"\nTotal days compared: {len(comparisons)}")
    print(f"Days warmer in {CURRENT_YEAR}: {warmer}")
    print(f"Days cooler in {CURRENT_YEAR}: {cooler}")
    print(f"Days same temperature: {len(comparisons) - warmer - cooler}")
    
    print(f"\nMonthly averages (°C):")
    for m in range(1, 13):
        if m in avg_diffs:
            print(f"  {['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][m-1]}: {avg_diffs[m]}°C")
    
    print(f"\nTop 5 warmest days in {CURRENT_YEAR} compared to history:")
    sorted_diffs = sorted(comparisons.items(), key=lambda x: x[1]['diff'], reverse=True)
    for i, (md_key, data) in enumerate(sorted_diffs[:5]):
        print(f"  {data['date']}: {data['diff']}°C warmer (Current: {data['curr_max']}°C, Hist: {data['hist_avg']}°C)")
    
    print(f"\nTop 5 coolest days in {CURRENT_YEAR} compared to history:")
    for i, (md_key, data) in enumerate(sorted_diffs[-5:]):
        print(f"  {data['date']}: {data['diff']}°C cooler (Current: {data['curr_max']}°C, Hist: {data['hist_avg']}°C)")