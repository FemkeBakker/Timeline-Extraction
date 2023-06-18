from datetime import datetime
import pandas as pd
from IPython.display import SVG
import json

def display_svg_file(file_path):
    display(SVG(filename=file_path))

def calculate_month_difference(start_date, end_date):
    # Convert ISO dates to datetime objects
    start_datetime = datetime.fromisoformat(start_date)
    end_datetime = datetime.fromisoformat(end_date)

    # Extract year and month components
    start_year, start_month = start_datetime.year, start_datetime.month
    end_year, end_month = end_datetime.year, end_datetime.month

    # Calculate the difference in months
    month_difference = (end_year - start_year) * 12 + (end_month - start_month)

    # Account for remaining days
    if end_datetime.day < start_datetime.day:
        month_difference -= 1

    return month_difference

def json_timeline(df, file):
    df_timeline = df.loc[~df['ISO_date'].isna()]
    callouts = []
    for index, row in df_timeline.iterrows():
        if row['class'] == 'verzoek datum':
            callouts.append([row['class'], str(row['ISO_date']), "#0000FF"])
        elif row['class'] == 'besluit datum': 
            callouts.append([row['class'], str(row['ISO_date']), "#FF0000"])
        else:
            callouts.append([row['class'], str(row['ISO_date'])])

    start = min(df_timeline['ISO_date'].values)
    end = max(df_timeline['ISO_date'].values)
    # print(calculate_month_difference(start, end))
    json_dict = {
        "width" : 1000,
        "start" : str(start),
        "end" : str(end),	
        "num_ticks" : calculate_month_difference(start, end),
        "tick_format" : "%b %d, %Y",
        "callouts" : callouts,
    }
    with open(file, 'w') as file:
        json.dump(json_dict, file)
    return None