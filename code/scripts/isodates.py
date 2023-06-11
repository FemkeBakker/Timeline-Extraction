import pandas as pd
from datetime import datetime
import locale
import re

def convert_to_isodate(date_string):
    locale.setlocale(locale.LC_TIME, 'nl_NL')

    try:
        date = datetime.strptime(date_string, "%d %B %Y")
        return date.date().isoformat()
    except (ValueError, TypeError):
        return False

def is_month_before(date1, date2):
    maanden = ["januari", "februari", "maart", "april", "mei", "juni", "juli","augustus","september","oktober","november","december"]
    pattern = "(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)"
    match_date = re.search(pattern, date1)
    match_decision = re.search(pattern, date2)

    # get decision year
    year_pattern = "[0-2][0-9][0-9][0-9]"
    match_year = re.search(year_pattern, date2)
    if match_year:
        decision_year = match_year.group()

        if match_date:
            date_index = maanden.index(match_date.group())
    
            if match_decision:
                decision_index = maanden.index(match_decision.group())
                if decision_index >= date_index:
                
                    date1 = f"{date1} {decision_year}"

                else:
                    date1 = f"{date1} {int(decision_year)-1}"

        

    else: 
        print("decision has no year", date2)

    


    return date1

def other_date_in_sent(date, df_sent):
    df_sent = df_sent.sort_values(by=['start_in_text'])
    date_year = df_sent['date'].values[0]

    # check if date_year is not equal to the date itself
    if date_year != date:
        pattern = "[0-2][0-9][0-9][0-9]"
        year_match = re.search(pattern, date_year)
        if year_match:
            date = f"{date} {year_match.group()}"
            return date
        
def complete_dates(row, df):
    date = row['date']
    # return date if already complete
    standard_pattern = "^[0-9][0-9]?\s(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s[0-2][0-9][0-9][0-9]$"
    match = re.search(standard_pattern, date.lower())
    if match:
        return date
    
    # else make date complete
    else:
        # print(date)
        # first of may is highly likely to be the date of Woo
        if date.lower() == "1 mei":
            date = "1 mei 2020"

        else:
            # check if there is a complete
            pattern = "[0-9][0-9]?\s(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s[0-2][0-9][0-9][0-9]"
            match = re.search(pattern, date)  # Search for the first match

            # set complete date as date
            if match:
                date = match.group()
                return date

            # check if only day misses from date
            pattern = "(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)\s[0-2][0-9][0-9][0-9]"
            match = re.search(pattern, date)  # Search for the first match

            # set missing day to 15
            if match:
                date = f"15 {match.group()}"
                return date


            # check if only year is missing from date
            pattern = "[0-9][0-9]?\s(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)"
            match = re.search(pattern, date)  # Search for the first match

            if match:
                df_sent = df.loc[(df['doc_id']==row['doc_id']) & (df['sentence']==row['sentence'])]
                if len(df_sent) > 1 and "jl" not in date:
                    date = other_date_in_sent(date, df_sent)

                    return date

                else:
                    # set missing year to latest year since decision date
                    decision_date = df.loc[(df['doc_id'] == row['doc_id']) & (df['class'] == "besluit datum")]['date'].values[0]
                    date = is_month_before(match.group(), decision_date)
                    return date
            # if it did not take anything else -> means that only month is there
            pattern = "(?:januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)"
            match = re.search(pattern, date)
            if match:
                date = f"15 {match.group()}"
                df_sent = df.loc[(df['doc_id']==row['doc_id']) & (df['sentence']==row['sentence'])]
                if len(df_sent) > 1:
                    date = other_date_in_sent(date, df_sent)
                    return date
                else:
                    decision_date = df.loc[(df['doc_id'] == row['doc_id']) & (df['class'] == "besluit datum")]['date'].values[0]
                    date = is_month_before(date, decision_date)
                    return date

        return date
    
def convert_date(df):
    df['complete_date'] = df.apply(lambda row: complete_dates(row, df), axis=1)
    df['ISO_date'] = df['complete_date'].apply(convert_to_isodate)
    return df

    