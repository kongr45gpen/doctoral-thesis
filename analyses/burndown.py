import sys
import logging
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import coloredlogs
from prompt_toolkit.shortcuts import choice as pt_choice
import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.ticker as mticker

def choose_sheet(sheet_names):
    options = [(name, name) for name in sheet_names]

    return pt_choice(
        message="Choose a sheet:",
        options=options,
        default=sheet_names[0] if sheet_names else None,
    )

def burndown(df, output):
    logger = logging.getLogger(__name__)

    n_old = df.shape[0]
    df = df.dropna(subset=['End Date'])
    n_new = df.shape[0]
    df = df.drop(columns=['Comment'], errors='ignore')
    logger.debug(f'Removed {n_old - n_new} rows with missing End Date')

    # If an end date is invalid, report an error
    if not pd.to_datetime(df['End Date'], errors='coerce').notna().all():
        for idx, value in df['End Date'].items():
            if pd.isna(pd.to_datetime(value, errors='coerce')):
                logger.error(f'Invalid date in row {idx + 2}: {value}')  

        raise ValueError('One or more invalid dates found in "End Date" column.')
    # Parse End Date
    df['End Date'] = pd.to_datetime(df['End Date'])

    earliest_spec_date = df['Specification Date'].min()
    logger.debug(f'Earliest Specification Date: {earliest_spec_date}')

    # Fill empty spec dates with the earliest one
    df['Specification Date'] = df['Specification Date'].fillna(earliest_spec_date)

    # PRINT
    print(df)

    total_tasks = len(df)
    start_date = df['Specification Date'].min().normalize()
    end_date = df['End Date'].max().normalize()
    if pd.isna(start_date) or pd.isna(end_date):
        raise ValueError('Could not determine start or end date for burndown chart.')
    dates = pd.date_range(start_date, end_date, freq='D')

    # STATUS COMPUTATION for STACKED plot
    # Custom order and color hinting for status
    status_priority = {'MUST': 0, 'SHOULD': 1, 'CAN': 2}
    status_hint_colors = {'MUST': (0.85, 0.2, 0.2, 0.7), 'SHOULD': (1.0, 0.6, 0.1, 0.6), 'CAN': (0.2, 0.4, 0.8, 0.5)}
    # Sort status_types by priority, then alphabetically
    status_types = sorted(df['Requirement Status'].dropna().unique(), key=lambda s: (status_priority.get(s, 99), s))
    # Assign colors: use hint if present, else tab20
    status_colors = cm.get_cmap('tab20', len(status_types))
    status_color_map = {status: status_hint_colors.get(status, status_colors(i)) for i, status in enumerate(status_types)}

    # For each date, count open tasks by status
    open_by_status = {status: [] for status in status_types}
    for date in dates:
        open_mask = (df['Specification Date'] <= date) & (df['End Date'] > date)
        for status in status_types:
            open_by_status[status].append(((df['Requirement Status'] == status) & open_mask).sum())


    # BURNDOWN chart data
    remaining = []
    current = 0
    first  = None
    for date in dates:
        current += df[df['Specification Date'] == date].shape[0]
        if first is None:
            first = current
        current -= df[df['End Date'] == date].shape[0]
        remaining.append(current)

    logger.info(f'Sanity check: Number of tasks at end must be zero: {remaining[-1]} tasks remaining')

    logger.info(f'Computed burndown from {start_date.date()} to {end_date.date()} for {total_tasks} tasks')

    # Plot
    fig, ax = plt.subplots(figsize=(10, 5))

    # Stacked area for open tasks by status
    status_arrays = [open_by_status[status] for status in status_types]
    colors = [status_color_map[status] for status in status_types]
    stack = ax.stackplot(dates, status_arrays, labels=status_types, colors=colors, alpha=0.5, zorder=0)

    # Ideal linear burndown (straight line from total_tasks to 0)
    ideal = np.linspace(first, 0, len(dates))
    ax.plot(dates, ideal, linestyle='--', color='gray', alpha=0.5, linewidth=1.5, label='Ideal', zorder=2)

    # Actual remaining tasks
    ax.plot(dates, remaining, color='black', label='Remaining', zorder=3)

    ax.set_xlabel('Date')
    ax.set_ylabel('Tasks Remaining')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', ncol=2)
    fig.autofmt_xdate()

    output_path = output
    plt.tight_layout()
    plt.show()
    #plt.savefig(output_path, dpi=150)
    logger.info(f'Saved burndown chart to {output_path}')

def nonconformance(df):
    logger = logging.getLogger(__name__)
    n_old = df.shape[0]
    df = df.dropna(subset=['Type', 'Introduction Revision', 'Resolution Revision'])
    n_new = df.shape[0]
    logger.info(f'Removed {n_old - n_new} rows with N/A')

    print(df)

    df = df.copy()
    df['Introduction Revision'] = pd.to_numeric(df['Introduction Revision'], errors='coerce').fillna(0).astype(int)
    df['Resolution Revision'] = pd.to_numeric(df['Resolution Revision'], errors='coerce').fillna(0).astype(int)

    min_rev = 1
    max_rev = max(df['Introduction Revision'].max(), df['Resolution Revision'].max())
    logger.info(f'Revision range: {min_rev} to {max_rev}')

    type_priority = {'Major': 0, 'Minor': 1}
    types = sorted(df['Type'].unique(), key=lambda t: (type_priority.get(t, 99), t))
    revs = list(range(min_rev, max_rev + 1))

    detected = {t: [] for t in types}
    resolved = {t: [] for t in types}
    for rev in revs:
        for t in types:
            detected[t].append(((df['Type'] == t) & (df['Introduction Revision'] <= rev) & (df['Introduction Revision'] > 0)).sum())
            resolved[t].append(((df['Type'] == t) & (df['Resolution Revision'] <= rev) & (df['Resolution Revision'] > 0)).sum())

    fig, ax = plt.subplots(figsize=(10, 6))

    # Use tab20 for TYPE color, detected=normal, resolved=lighter
    base_colors = plt.cm.Set1(np.linspace(0, 1, len(types)))
    def lighten(color, amount=0.5):
        c = mcolors.to_rgb(color)
        return tuple(1 - (1 - x) * (1 - amount) for x in c)

    for idx, t in enumerate(types):
        base = base_colors[idx]
        ax.plot(revs, detected[t], label=f"{t} detected", linestyle='-', marker='x', color=base)
        ax.plot(revs, resolved[t], label=f"{t} resolved", linestyle='-', marker=6, color=lighten(base, 0.5))
    ax.set_xlabel('Iteration')
    ax.set_ylabel('Cumulative Non-conformances')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5, which='both', axis='both')
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    plt.tight_layout()
    plt.show()

def main():
    parser = argparse.ArgumentParser(description='Process an Excel file.')
    parser.add_argument('action', type=str, choices=['burndown', 'nonconformance'], help='Action to perform (required). Supported: burndown, nonconformance')
    parser.add_argument('excel_file', type=str, help='The path to the Excel file')
    parser.add_argument('--sheet', type=str, help='The name of the sheet to process')
    parser.add_argument('--output', type=str, default='burndown.png', help='Path to save the burndown chart')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable DEBUG logging')
    args = parser.parse_args()

    level = logging.DEBUG if args.debug else logging.INFO
    log_fmt = '%(asctime)s %(levelname)s %(name)s: %(message)s'
    coloredlogs.install(level=level, fmt=log_fmt)
    logger = logging.getLogger(__name__)

    excel_file = args.excel_file
    logger.info(f'Loading Excel file: {excel_file}')

    sheet_names = pd.ExcelFile(excel_file).sheet_names
    logger.debug(f'Available sheets: {sheet_names}')

    selected_sheet = args.sheet or choose_sheet(sheet_names)
    logger.info(f'Selected sheet: {selected_sheet}')

    df = pd.read_excel(excel_file, sheet_name=selected_sheet)
    logger.info(f'Read DataFrame with shape: {df.shape[0]} rows x {df.shape[1]} columns')

    if args.action == 'burndown':
        burndown(df, args.output)
    elif args.action == 'nonconformance':
        nonconformance(df)
    
    

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.getLogger(__name__).exception('Error reading the Excel file')
