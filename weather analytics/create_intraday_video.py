import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import rcParams

HOURLY_FILE = 'karachi_weather_hourly.json'
VIDEO_FILE = 'karachi_weather_intraday_race.mp4'
FPS = 10
HOLD_FRAMES = 2
TRANS_FRAMES = 3
YEARS = [2021, 2022, 2023, 2024, 2025, 2026]

COLORS = {
    2021: '#3498db',
    2022: '#2ecc71',
    2023: '#e74c3c',
    2024: '#f39c12',
    2025: '#9b59b6',
    2026: '#e91e63'
}

MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun',
               'Jul','Aug','Sep','Oct','Nov','Dec']

def load_data():
    with open(HOURLY_FILE, 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def build_hourly_month_map(data):
    """For each year/month/hour, compute average temperature across days in that month."""
    result = {}  # year -> month -> hour -> avg temp
    for year, records in data.items():
        result[year] = {}
        buckets = {}  # (month, hour) -> list of temps
        for rec in records:
            # time format: "2025-01-01T13:00"
            date_part, time_part = rec['time'].split('T')
            month = int(date_part.split('-')[1])
            hour = int(time_part.split(':')[0])
            buckets.setdefault((month, hour), []).append(rec['temp'])
        for (month, hour), temps in buckets.items():
            result[year].setdefault(month, {})[hour] = float(np.mean(temps))
    return result

def create_intraday_video():
    data = load_data()
    hourly_map = build_hourly_month_map(data)

    print(f"Loaded {len(data)} years of hourly data")

    # Build keyframes: for each month, iterate hours 0..23
    keyframes = []
    for month in range(1, 13):
        for hour in range(24):
            values = []
            for year in YEARS:
                v = hourly_map.get(year, {}).get(month, {}).get(hour, 0)
                values.append(v if v else 0)
            order = sorted(range(len(YEARS)), key=lambda i: -values[i])
            keyframes.append({
                'values': np.array(values, dtype=float),
                'order': order,
                'month': month,
                'hour': hour
            })

    print(f"Keyframes: {len(keyframes)} (12 months x 24 hours)")

    # Build interpolated frame list
    all_frames = []
    n = len(keyframes)
    for i, kf in enumerate(keyframes):
        for _ in range(HOLD_FRAMES):
            all_frames.append({
                'values': kf['values'].copy(),
                'order': kf['order'],
                'month': kf['month'],
                'hour': kf['hour'],
                'progress': (i + 1) / n
            })
        if i < n - 1:
            nxt = keyframes[i + 1]
            for t in range(1, TRANS_FRAMES + 1):
                frac = t / (TRANS_FRAMES + 1)
                smooth = frac * frac * (3 - 2 * frac)
                interp_vals = kf['values'] + (nxt['values'] - kf['values']) * smooth
                pos_now = {y: r for r, y in enumerate(kf['order'])}
                pos_next = {y: r for r, y in enumerate(nxt['order'])}
                interp_pos = np.array([
                    pos_now[yi] + (pos_next[yi] - pos_now[yi]) * smooth
                    for yi in range(len(YEARS))
                ])
                all_frames.append({
                    'values': interp_vals,
                    'positions': interp_pos,
                    'month': kf['month'] if frac < 0.5 else nxt['month'],
                    'hour': kf['hour'] if frac < 0.5 else nxt['hour'],
                    'progress': (i + frac) / n
                })

    total = len(all_frames)
    duration = total / FPS
    print(f"Total frames: {total}, Duration: {duration:.0f}s ({duration/60:.1f} min)")

    # Figure
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.patch.set_facecolor('#0f0f23')
    ax.set_facecolor('#0f0f23')
    rcParams['font.family'] = 'sans-serif'

    bar_h = 0.6
    bars = ax.barh(range(len(YEARS)), [0]*len(YEARS),
                   color=[COLORS[y] for y in YEARS],
                   edgecolor='white', linewidth=0.5,
                   height=bar_h, alpha=0.9)

    value_texts = []
    year_labels = []
    for i in range(len(YEARS)):
        vt = ax.text(0, i, '', va='center', ha='left',
                      color='white', fontsize=12, fontweight='bold')
        yt = ax.text(0, i, '', va='center', ha='left',
                      color='white', fontsize=11, fontweight='bold')
        value_texts.append(vt)
        year_labels.append(yt)

    ax.set_yticks([])
    ax.invert_yaxis()
    ax.set_xlim(0, 48)
    ax.set_xlabel('Hourly Average Temperature (°C)', color='#aaa', fontsize=11)
    ax.tick_params(colors='#888', labelsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#333')
    ax.spines['left'].set_color('#333')

    # Reserve headroom so title + hour + diff don't overlap
    fig.subplots_adjust(top=0.80, bottom=0.13, left=0.08, right=0.97)

    fig.text(0.5, 0.955, 'Karachi Intraday Temperature Race 2021-2026',
             ha='center', va='center', color='white', fontsize=18, fontweight='bold')

    title_text = ax.text(0.5, 1.16, '', transform=ax.transAxes,
                          ha='center', va='center', fontsize=17,
                          color='#e91e63', fontweight='bold')
    diff_text = ax.text(0.5, 1.08, '', transform=ax.transAxes,
                         ha='center', va='center', fontsize=11.5, color='#bbb')

    progress_bg = plt.Rectangle((0.05, -0.06), 0.9, 0.015,
                                 transform=fig.transFigure, color='#222', zorder=5)
    progress_bar = plt.Rectangle((0.05, -0.06), 0.0, 0.015,
                                  transform=fig.transFigure, color='#e91e63', zorder=6)
    fig.patches.append(progress_bg)
    fig.patches.append(progress_bar)

    fig.text(0.99, 0.01,
             'Source: Open-Meteo Archive API — ERA5 hourly (Copernicus/ECMWF)',
             ha='right', fontsize=8, color='#555')

    def animate(frame_idx):
        fd = all_frames[frame_idx]
        values = fd['values']

        if 'positions' in fd:
            positions = fd['positions']
        else:
            positions = np.array(
                [fd['order'].index(yi) for yi in range(len(YEARS))], dtype=float)

        for yi in range(len(YEARS)):
            rank = positions[yi]
            v = max(values[yi], 0)
            bars[yi].set_y(rank - bar_h / 2)
            bars[yi].set_height(bar_h)
            bars[yi].set_width(v)
            bars[yi].set_color(COLORS[YEARS[yi]])
            year_labels[yi].set_position((0.8, rank))
            year_labels[yi].set_text(str(YEARS[yi]))
            value_texts[yi].set_position((v + 0.5, rank))
            value_texts[yi].set_text(f'{v:.1f}°C')

        hour = fd['hour']
        ampm = 'AM' if hour < 12 else 'PM'
        h12 = hour % 12 or 12
        title_text.set_text(
            f"{MONTH_NAMES[fd['month']-1]}  —  {h12}:00 {ampm}")

        curr = values[YEARS.index(2026)]
        hist_vals = [values[yi] for yi in range(len(YEARS)) if YEARS[yi] != 2026]
        if curr > 0 and len(hist_vals) > 0:
            hist_avg = np.mean(hist_vals)
            d = curr - hist_avg
            diff_text.set_text(
                f"2026: {curr:.1f}°C  |  5yr Avg: {hist_avg:.1f}°C  |  Diff: {d:+.1f}°C")

        progress_bar.set_width(fd['progress'] * 0.9)
        return list(bars) + value_texts + year_labels + [title_text, diff_text, progress_bar]

    anim = animation.FuncAnimation(fig, animate, frames=total,
                                   interval=1000 // FPS, blit=False, repeat=True)
    writer = animation.FFMpegWriter(fps=FPS, bitrate=2000,
                                     extra_args=['-pix_fmt', 'yuv420p'])
    anim.save(VIDEO_FILE, writer=writer)
    plt.close()
    print(f"Saved: {VIDEO_FILE} — {total} frames, {duration:.1f}s")

if __name__ == '__main__':
    create_intraday_video()
