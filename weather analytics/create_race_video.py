import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import rcParams

DATA_FILE = 'karachi_weather_data.json'
VIDEO_FILE = 'karachi_weather_race_chart.mp4'
FPS = 10
HOLD_FRAMES = 2
TRANS_FRAMES = 5
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
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def build_day_maps(data):
    day_maps = {}
    for year in YEARS:
        day_maps[year] = {}
        for rec in data[year]:
            parts = rec['date'].split('-')
            md = f"{int(parts[1]):02d}-{int(parts[2]):02d}"
            if rec['max'] is not None and rec['min'] is not None:
                day_maps[year][md] = {
                    'max': rec['max'],
                    'min': rec['min'],
                    'avg': (rec['max'] + rec['min']) / 2
                }
    return day_maps

def create_race_video():
    data = load_data()
    day_maps = build_day_maps(data)

    sorted_days = sorted(
        day_maps[2026].keys(),
        key=lambda x: (int(x[:2]), int(x[3:]))
    )
    print(f"Days: {len(sorted_days)}, Hold={HOLD_FRAMES}, Trans={TRANS_FRAMES}, FPS={FPS}")

    # Pre-compute keyframes for each day
    keyframes = []
    for md in sorted_days:
        values = []
        for year in YEARS:
            if md in day_maps[year]:
                values.append(day_maps[year][md]['avg'])
            else:
                values.append(0)
        order = sorted(range(len(YEARS)), key=lambda i: -values[i])
        month = int(md[:2])
        day = int(md[3:])
        keyframes.append({
            'values': np.array(values, dtype=float),
            'order': order,
            'month': month,
            'day': day,
            'md': md
        })

    # Build interpolated frame list
    # Each day: HOLD_FRAMES frozen frames + TRANS_FRAMES transition to next day
    all_frames = []
    for i, kf in enumerate(keyframes):
        # Hold frames
        for _ in range(HOLD_FRAMES):
            all_frames.append({
                'values': kf['values'].copy(),
                'order': kf['order'],
                'month': kf['month'],
                'day': kf['day'],
                'progress': (i + 1) / len(keyframes)
            })

        # Transition frames to next day
        if i < len(keyframes) - 1:
            next_kf = keyframes[i + 1]
            for t in range(1, TRANS_FRAMES + 1):
                frac = t / (TRANS_FRAMES + 1)
                # Smooth ease-in-out
                smooth = frac * frac * (3 - 2 * frac)
                interp_values = kf['values'] + (next_kf['values'] - kf['values']) * smooth

                # Interpolate positions between old order and new order
                pos_now = {y: r for r, y in enumerate(kf['order'])}
                pos_next = {y: r for r, y in enumerate(next_kf['order'])}
                interp_positions = np.array([
                    pos_now[yi] + (pos_next[yi] - pos_now[yi]) * smooth
                    for yi in range(len(YEARS))
                ])

                all_frames.append({
                    'values': interp_values,
                    'positions': interp_positions,
                    'month': kf['month'] if frac < 0.5 else next_kf['month'],
                    'day': kf['day'] if frac < 0.5 else next_kf['day'],
                    'progress': (i + frac) / len(keyframes)
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
    ax.set_xlabel('Average Temperature (°C)', color='#aaa', fontsize=11)
    ax.tick_params(colors='#888', labelsize=10)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#333')
    ax.spines['left'].set_color('#333')

    # Reserve headroom so title + date + diff don't overlap
    fig.subplots_adjust(top=0.80, bottom=0.13, left=0.08, right=0.97)

    fig.text(0.5, 0.955, 'Karachi Day-by-Day Temperature Race 2021-2026',
             ha='center', va='center', color='white', fontsize=18, fontweight='bold')

    date_text = ax.text(0.5, 1.16, '', transform=ax.transAxes,
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

    fig.text(0.99, 0.01, 'Source: NASA POWER (NASA GSFC) & Open-Meteo Archive — ERA5 (Copernicus/ECMWF)',
             ha='right', fontsize=8, color='#555')

    def animate(frame_idx):
        fd = all_frames[frame_idx]
        values = fd['values']

        if 'positions' in fd:
            positions = fd['positions']
        else:
            order = fd['order']
            positions = np.array([order.index(yi) for yi in range(len(YEARS))], dtype=float)

        for yi in range(len(YEARS)):
            rank = positions[yi]
            v = max(values[yi], 0)

            bars[yi].set_y(rank - bar_h / 2)
            bars[yi].set_height(bar_h)
            bars[yi].set_width(v)
            bars[yi].set_color(COLORS[YEARS[yi]])

            year_labels[yi].set_position((1, rank))
            year_labels[yi].set_text(str(YEARS[yi]))

            value_texts[yi].set_position((v + 0.5, rank))
            value_texts[yi].set_text(f'{v:.1f}°C')

        date_text.set_text(f"{MONTH_NAMES[fd['month']-1]} {fd['day']}")

        curr = values[YEARS.index(2026)]
        hist_vals = [values[yi] for yi in range(len(YEARS)) if YEARS[yi] != 2026]
        if curr > 0 and len(hist_vals) > 0:
            hist_avg = np.mean(hist_vals)
            d = curr - hist_avg
            diff_text.set_text(
                f"2026: {curr:.1f}°C  |  5yr Avg: {hist_avg:.1f}°C  |  Diff: {d:+.1f}°C")

        progress_bar.set_width(fd['progress'] * 0.9)
        return list(bars) + value_texts + year_labels + [date_text, diff_text, progress_bar]

    anim = animation.FuncAnimation(fig, animate, frames=total,
                                   interval=1000 // FPS, blit=False, repeat=True)

    writer = animation.FFMpegWriter(fps=FPS, bitrate=2000,
                                     extra_args=['-pix_fmt', 'yuv420p'])
    anim.save(VIDEO_FILE, writer=writer)
    plt.close()
    print(f"Saved: {VIDEO_FILE} — {total} frames, {duration:.1f}s")

if __name__ == '__main__':
    create_race_video()
