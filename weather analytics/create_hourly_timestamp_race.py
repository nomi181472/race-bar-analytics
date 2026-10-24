import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import rcParams

HOURLY_FILE = 'karachi_weather_hourly.json'
VIDEO_FILE = 'karachi_weather_hourly_timestamp_race.mp4'
FPS = 20
YEARS = [2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]

CONFIG = {
    'COLORS': {
        2015: '#fd79a8',
        2016: '#6c5ce7',
        2017: '#a29bfe',
        2018: '#74b9ff',
        2019: '#00b894',
        2020: '#1abc9c',
        2021: '#3498db',
        2022: '#2ecc71',
        2023: '#e74c3c',
        2024: '#f39c12',
        2025: '#9b59b6',
        2026: '#e91e63',
    },
    'BAR_ALPHA': 0.97,
    'BAR_EDGE_COLOR': 'white',
    'BAR_LINEWIDTH': 1.0,
    'BAR_HEIGHT': 0.6,
    'FIG_SIZE': (14, 8.0),
    'FIG_DPI': 90,
    'FIG_FACECOLOR': '#0f0f23',
    'AX_FACECOLOR': '#0f0f23',
    'FONT_FAMILY': 'sans-serif',
    'TITLE': 'Karachi Hourly Temperature Race 2015-2026',
    'TITLE_COLOR': 'white',
    'TITLE_FONTSIZE': 18,
    'TITLE_FONTWEIGHT': 'bold',
    'TITLE_Y': 0.955,
    'XLABEL': 'Temperature (°C)',
    'XLABEL_COLOR': '#aaa',
    'XLABEL_FONTSIZE': 11,
    'TICK_COLORS': '#888',
    'TICK_LABELSIZE': 10,
    'SPINE_COLOR': '#333',
    'CLOCK_COLOR': '#e91e63',
    'CLOCK_FONTSIZE': 17,
    'CLOCK_FONTWEIGHT': 'bold',
    'DIFF_COLOR': '#bbb',
    'DIFF_FONTSIZE': 11.5,
    'PROGRESS_BG_COLOR': '#222',
    'PROGRESS_BAR_COLOR': '#e91e63',
    'PROGRESS_BG_RECT': ((0.05, -0.07), 0.9, 0.014),
    'PROGRESS_BAR_RECT': ((0.05, -0.07), 0.0, 0.014),
    'PROGRESS_ZORDER_BG': 5,
    'PROGRESS_ZORDER_BAR': 6,
    'SOURCE_TEXT': 'Source: Open-Meteo Archive API — ERA5 hourly (Copernicus/ECMWF)',
    'SOURCE_COLOR': '#555',
    'SOURCE_FONTSIZE': 8,
    'SOURCE_POS': (0.99, 0.012),
    'SOURCE_HA': 'right',
    'SUBPLOTS_ADJUST': {'top': 0.80, 'bottom': 0.20, 'left': 0.07, 'right': 0.98},
    'TEXT_POS_X': 0.6,
    'BAR_TEXT_FONTSIZE': 9.2,
    'BAR_TEXT_FONTWEIGHT': 'bold',
    'BAR_TEXT_COLOR': 'white',
    'X_LIMIT': (0, 46),
    'SCORE_LABEL': 'Cumulative Rank-Points Score',
    'SCORE_LABEL_COLOR': '#fff',
    'SCORE_LABEL_FONTSIZE': 11,
    'SCORE_COLOR': '#fff',
    'SCORE_FONTSIZE': 10,
    'SCORE_POS_X': 0.5,
    'SCORE_START_Y': 0.84,
    'SCORE_LINE_SPACING': 0.025,
    'TREND_GRAPH_RECT': [0.04, 0.04, 0.92, 0.14],
    'TREND_GRAPH_TITLE': 'Cumulative Rank-Points Score by Year',
    'TREND_GRAPH_TITLE_COLOR': '#fff',
    'TREND_GRAPH_TITLE_FONTSIZE': 10,
    'TREND_GRAPH_YLABEL': 'Score',
    'TREND_GRAPH_YLABEL_COLOR': '#aaa',
    'TREND_GRAPH_YLABEL_FONTSIZE': 9,
    'TREND_GRAPH_XLABEL': 'Year',
    'TREND_GRAPH_XLABEL_COLOR': '#aaa',
    'TREND_GRAPH_XLABEL_FONTSIZE': 9,
    'TREND_GRAPH_TICK_COLOR': '#888',
    'TREND_GRAPH_DESCRIPTION': 'Each hour, every year earns rank-points (1st=1.00, 2nd=0.92, ..., 12th=0.08). Score accumulates live as the video plays.',
    'TREND_GRAPH_DESC_COLOR': '#bbb',
    'TREND_GRAPH_DESC_FONTSIZE': 7,
    'TREND_GRAPH_DESC_POS': (0.5, 0.008),
    'TREND_BAR_WIDTH': 0.7,
    'TREND_LABEL_FONTSIZE': 9,
    'TREND_LABEL_OFFSET': 0.5,
}

MONTH_NAMES = ['Jan','Feb','Mar','Apr','May','Jun',
               'Jul','Aug','Sep','Oct','Nov','Dec']

def load_data():
    with open(HOURLY_FILE, 'r') as f:
        data = json.load(f)
    return {int(k): v for k, v in data.items()}

def build_year_maps(data):
    """ year -> {(month, day, hour): temp} """
    maps = {}
    for year, records in data.items():
        m = {}
        for rec in records:
            date_part, time_part = rec['time'].split('T')
            y, mo, d = date_part.split('-')
            h = time_part.split(':')[0]
            m[(int(mo), int(d), int(h))] = rec['temp']
        maps[year] = m
    return maps

def build_timeline(year_maps):
    """Timeline = every available timestamp in 2026, sorted chronologically."""
    return sorted(year_maps[2026].keys())

def compute_timestamp_scores(year_maps, month, day, hour):
    """Compute rank-points scores for a single timestamp.

    rank 1 (hottest) -> 12/12, rank 2 -> 11/12, ..., rank 12 -> 1/12.
    Returns dict {year: score_for_this_timestamp}.
    """
    n_years = len(YEARS)
    values = []
    for year in YEARS:
        t = year_maps[year].get((month, day, hour))
        values.append(t if t is not None else 0.0)
    # Sort year indices by temperature descending (rank 1 = hottest)
    order = sorted(range(n_years), key=lambda i: -values[i])
    scores = {}
    for rank, yi in enumerate(order):
        scores[YEARS[yi]] = (n_years - rank) / n_years
    return scores

def create_video():
    data = load_data()
    year_maps = build_year_maps(data)
    timeline = build_timeline(year_maps)

    # Optional frame limit for quick previews (e.g. LIMIT=200 python3 script.py)
    limit = int(os.environ.get('LIMIT', '0'))
    if limit > 0:
        timeline = timeline[:limit]
        global VIDEO_FILE
        VIDEO_FILE = 'preview_hourly_race.mp4'

    print(f"Years: {YEARS}")
    print(f"Hourly timeline frames: {len(timeline)} "
          f"({timeline[0]} -> {timeline[-1]})")

    fig, ax = plt.subplots(figsize=CONFIG['FIG_SIZE'], dpi=CONFIG['FIG_DPI'])
    fig.patch.set_facecolor(CONFIG['FIG_FACECOLOR'])
    ax.set_facecolor(CONFIG['AX_FACECOLOR'])
    rcParams['font.family'] = CONFIG['FONT_FAMILY']

    bar_h = CONFIG['BAR_HEIGHT']
    bars = ax.barh(range(len(YEARS)), [0]*len(YEARS),
                   color=[CONFIG['COLORS'][y] for y in YEARS],
                   edgecolor=CONFIG['BAR_EDGE_COLOR'],
                   linewidth=CONFIG['BAR_LINEWIDTH'],
                   height=bar_h, alpha=CONFIG['BAR_ALPHA'])

    bar_texts = []
    for i in range(len(YEARS)):
        bt = ax.text(CONFIG['TEXT_POS_X'], i, '', va='center', ha='left',
                     color=CONFIG['BAR_TEXT_COLOR'],
                     fontsize=CONFIG['BAR_TEXT_FONTSIZE'],
                     fontweight=CONFIG['BAR_TEXT_FONTWEIGHT'])
        bar_texts.append(bt)

    ax.set_yticks([])
    ax.invert_yaxis()
    ax.set_xlim(*CONFIG['X_LIMIT'])
    ax.set_xlabel(CONFIG['XLABEL'], color=CONFIG['XLABEL_COLOR'],
                  fontsize=CONFIG['XLABEL_FONTSIZE'])
    ax.tick_params(colors=CONFIG['TICK_COLORS'], labelsize=CONFIG['TICK_LABELSIZE'])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color(CONFIG['SPINE_COLOR'])
    ax.spines['left'].set_color(CONFIG['SPINE_COLOR'])

    fig.subplots_adjust(**CONFIG['SUBPLOTS_ADJUST'])

    fig.text(0.5, CONFIG['TITLE_Y'], CONFIG['TITLE'],
             ha='center', va='center', color=CONFIG['TITLE_COLOR'],
             fontsize=CONFIG['TITLE_FONTSIZE'],
             fontweight=CONFIG['TITLE_FONTWEIGHT'])

    clock_text = ax.text(0.5, 1.16, '', transform=ax.transAxes,
                         ha='center', va='center',
                         fontsize=CONFIG['CLOCK_FONTSIZE'],
                         color=CONFIG['CLOCK_COLOR'],
                         fontweight=CONFIG['CLOCK_FONTWEIGHT'])
    diff_text = ax.text(0.5, 1.08, '', transform=ax.transAxes,
                        ha='center', va='center',
                        fontsize=CONFIG['DIFF_FONTSIZE'],
                        color=CONFIG['DIFF_COLOR'])

    progress_bg = plt.Rectangle(*CONFIG['PROGRESS_BG_RECT'],
                                transform=fig.transFigure,
                                color=CONFIG['PROGRESS_BG_COLOR'],
                                zorder=CONFIG['PROGRESS_ZORDER_BG'])
    progress_bar = plt.Rectangle(*CONFIG['PROGRESS_BAR_RECT'],
                                 transform=fig.transFigure,
                                 color=CONFIG['PROGRESS_BAR_COLOR'],
                                 zorder=CONFIG['PROGRESS_ZORDER_BAR'])
    fig.patches.append(progress_bg)
    fig.patches.append(progress_bar)

    fig.text(*CONFIG['SOURCE_POS'], CONFIG['SOURCE_TEXT'],
             ha=CONFIG['SOURCE_HA'], fontsize=CONFIG['SOURCE_FONTSIZE'],
             color=CONFIG['SOURCE_COLOR'])

    # ---- Trend graph: cumulative score by year (bottom of figure) ----
    trend_ax = fig.add_axes(CONFIG['TREND_GRAPH_RECT'])
    trend_ax.set_facecolor(CONFIG['AX_FACECOLOR'])
    trend_ax.spines['top'].set_visible(False)
    trend_ax.spines['right'].set_visible(False)
    trend_ax.spines['bottom'].set_color(CONFIG['TREND_GRAPH_TICK_COLOR'])
    trend_ax.spines['left'].set_color(CONFIG['TREND_GRAPH_TICK_COLOR'])
    trend_ax.tick_params(colors=CONFIG['TREND_GRAPH_TICK_COLOR'],
                         labelsize=CONFIG['TREND_GRAPH_XLABEL_FONTSIZE'])

    x_positions = range(len(YEARS))
    trend_bars = trend_ax.bar(x_positions, [0]*len(YEARS),
                              width=CONFIG['TREND_BAR_WIDTH'],
                              color=[CONFIG['COLORS'][y] for y in YEARS],
                              edgecolor=CONFIG['BAR_EDGE_COLOR'],
                              linewidth=CONFIG['BAR_LINEWIDTH'],
                              alpha=CONFIG['BAR_ALPHA'])

    trend_labels = []
    for i, year in enumerate(YEARS):
        tl = trend_ax.text(i, CONFIG['TREND_LABEL_OFFSET'], '',
                           ha='center', va='bottom',
                           color=CONFIG['TREND_GRAPH_YLABEL_COLOR'],
                           fontsize=CONFIG['TREND_LABEL_FONTSIZE'],
                           fontweight='bold')
        trend_labels.append(tl)

    trend_ax.set_xticks(list(x_positions))
    trend_ax.set_xticklabels([str(y) for y in YEARS],
                             color=CONFIG['TREND_GRAPH_XLABEL_COLOR'],
                             fontsize=CONFIG['TREND_GRAPH_XLABEL_FONTSIZE'])

    trend_ax.set_title(CONFIG['TREND_GRAPH_TITLE'],
                       color=CONFIG['TREND_GRAPH_TITLE_COLOR'],
                       fontsize=CONFIG['TREND_GRAPH_TITLE_FONTSIZE'],
                       fontweight='bold', pad=8)
    trend_ax.set_ylabel(CONFIG['TREND_GRAPH_YLABEL'],
                        color=CONFIG['TREND_GRAPH_YLABEL_COLOR'],
                        fontsize=CONFIG['TREND_GRAPH_YLABEL_FONTSIZE'])
    trend_ax.set_xlabel(CONFIG['TREND_GRAPH_XLABEL'],
                        color=CONFIG['TREND_GRAPH_XLABEL_COLOR'],
                        fontsize=CONFIG['TREND_GRAPH_XLABEL_FONTSIZE'])
    trend_ax.set_ylim(0, 1)  # will auto-expand as scores grow
    trend_ax.grid(axis='y', color='#333', linestyle='--', alpha=0.3, linewidth=0.5)

    trend_desc = fig.text(*CONFIG['TREND_GRAPH_DESC_POS'],
                          CONFIG['TREND_GRAPH_DESCRIPTION'],
                          ha='center', va='center',
                          color=CONFIG['TREND_GRAPH_DESC_COLOR'],
                          fontsize=CONFIG['TREND_GRAPH_DESC_FONTSIZE'])

    total = len(timeline)

    # Running cumulative rank-points score per year (accumulates frame by frame)
    year_scores = {y: 0.0 for y in YEARS}

    def animate(idx):
        month, day, hour = timeline[idx]

        values = []
        labels = []
        for year in YEARS:
            t = year_maps[year].get((month, day, hour))
            if t is None:
                values.append(0.0)
                labels.append(f'{year}-{month:02d}-{day:02d} {hour:02d}:00  N/A')
            else:
                values.append(t)
                labels.append(f'{year}-{month:02d}-{day:02d} {hour:02d}:00')

        order = sorted(range(len(YEARS)), key=lambda i: -values[i])

        # Accumulate rank-points score for this timestamp
        ts_scores = compute_timestamp_scores(year_maps, month, day, hour)
        for year in YEARS:
            year_scores[year] += ts_scores[year]

        for rank, yi in enumerate(order):
            v = max(values[yi], 0)
            bars[yi].set_y(rank - bar_h / 2)
            bars[yi].set_height(bar_h)
            bars[yi].set_width(v)
            bars[yi].set_color(CONFIG['COLORS'][YEARS[yi]])

            bar_texts[yi].set_position((CONFIG['TEXT_POS_X'], rank))
            bar_texts[yi].set_text(
                f'{labels[yi]}   {v:.1f}°C   score: {year_scores[YEARS[yi]]:.1f}'
            )

        # Update trend graph: cumulative score by year
        for i, year in enumerate(YEARS):
            trend_bars[i].set_height(year_scores[year])
            trend_labels[i].set_position((i, year_scores[year]))
            trend_labels[i].set_text(f'{year_scores[year]:.1f}')

        # Auto-expand y-limit as scores grow
        max_score = max(year_scores.values()) if year_scores else 1
        trend_ax.set_ylim(0, max_score * 1.1 if max_score > 0 else 1)

        ampm = 'AM' if hour < 12 else 'PM'
        h12 = hour % 12 or 12
        clock_text.set_text(
            f"{MONTH_NAMES[month-1]} {day:02d}, {h12}:00 {ampm}")

        curr = values[YEARS.index(2026)]
        hist = [values[YEARS.index(y)] for y in YEARS if y != 2026]
        if curr > 0 and hist:
            ha = np.mean(hist)
            diff_text.set_text(
                f"2026: {curr:.1f}°C  |  5yr Avg: {ha:.1f}°C  |  Diff: {curr-ha:+.1f}°C")
        else:
            diff_text.set_text('')

        progress_bar.set_width((idx + 1) / total * 0.9)
        return (list(bars) + bar_texts
                + [clock_text, diff_text, progress_bar]
                + list(trend_bars) + list(trend_labels)
                + [trend_desc])

    import subprocess

    W, H = fig.canvas.get_width_height()
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba',
        '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
        '-an', '-vcodec', 'libx264', '-preset', 'veryfast',
        '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
        '-crf', '24', '-pix_fmt', 'yuv420p', VIDEO_FILE,
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    for idx in range(total):
        animate(idx)
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())
        proc.stdin.write(buf.tobytes())
        if idx % 500 == 0:
            print(f"  rendered {idx}/{total}", flush=True)
    proc.stdin.close()
    proc.wait()
    plt.close()
    print(f"Saved: {VIDEO_FILE} — {total} frames, {total/FPS:.0f}s "
          f"({total/FPS/60:.1f} min)")

if __name__ == '__main__':
    create_video()