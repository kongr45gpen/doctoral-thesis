import sys
import logging
import argparse
import pandas as pd
import matplotlib.pyplot as plt
import coloredlogs
from prompt_toolkit.shortcuts import choice as pt_choice
import numpy as np

def choose_sheet(sheet_names):
    options = [(name, name) for name in sheet_names]

    return pt_choice(
        message="Choose a sheet:",
        options=options,
        default=sheet_names[0] if sheet_names else None,
    )


def main():
    parser = argparse.ArgumentParser(description='Process an Excel file.')
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

    # Prepare burndown data
    total_tasks = len(df)
    start_date = df['Specification Date'].min().normalize()
    end_date = df['End Date'].max().normalize()
    if pd.isna(start_date) or pd.isna(end_date):
        raise ValueError('Could not determine start or end date for burndown chart.')

    dates = pd.date_range(start_date, end_date, freq='D')

    remaining = []
    current = 0
    first  = None
    for date in dates:
        remaining.append(current)
        current += df[df['Specification Date'] == date].shape[0]
        if first is None:
            first = current
        current -= df[df['End Date'] == date].shape[0]

    logger.info(f'Computed burndown from {start_date.date()} to {end_date.date()} for {total_tasks} tasks')

    # Remove first date
    dates = dates[1:]
    remaining = remaining[1:]

    # Plot
    fig, ax = plt.subplots(figsize=(8, 4.5))

    # Ideal linear burndown (straight line from total_tasks to 0)
    ideal = np.linspace(first, 0, len(dates))
    ax.plot(dates, ideal, linestyle='--', color='gray', alpha=0.5, linewidth=1.5, label='Ideal', zorder=1)

    # Actual remaining tasks
    ax.plot(dates, remaining, markersize=4, label='Remaining', zorder=2)

    ax.set_title('Burndown Chart')
    ax.set_xlabel('Date')
    ax.set_ylabel('Tasks Remaining')
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend()
    fig.autofmt_xdate()

    output_path = args.output
    plt.tight_layout()
    plt.show()
    #plt.savefig(output_path, dpi=150)
    logger.info(f'Saved burndown chart to {output_path}')
    

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logging.getLogger(__name__).exception('Error reading the Excel file')
