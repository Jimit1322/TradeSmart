'''
    Helpers
'''

from datetime import datetime, timedelta
from nselib import capital_market
import pandas as pd

def parse_date(date, format_from, format_to, delta = 0):
    '''
        Parse the input date string using datetime.strptime
        Format the date object into the desired format
    '''
    date_obj = datetime.strptime(date, format_from) + timedelta(days=delta)

    formatted_date = date_obj.strftime(format_to)
    return formatted_date

def timestamp_to_date(timestamp, f = '%Y-%m-%d'):
    '''
        Convert Timestamp to string
    '''
    return timestamp.strftime(f)

def get_slope(df, d, i):
    '''
        slope in terms of percentage for 2 price points separated over d days
    '''
    change_percentage = (df["EMA"].iloc[i] - df["EMA"].iloc[i-d]) * 100 / df["EMA"].iloc[i-d]
    return change_percentage/d

def pivot_helper(df, p_window, i, result, level, multiplier):
    '''
       Helper for checking if the Hi / Lo of the candle is a pivot
    '''
    l = r = j = p_window[0]
    while j:
        if i - j < 0 or multiplier * df.iloc[i-j][level] > multiplier * df.iloc[i][level]:
            l = j - 1
        if i + j >= len(df) or multiplier * df.iloc[i+j][level] > multiplier * df.iloc[i][level]:
            r = j - 1
        j = j - 1

    for k in enumerate(p_window):
        k = k[0]
        if p_window[k] <= min(l, r):
            if isinstance(df.index[i], int):
                date = df.iloc[i]["TIMESTAMP"]
            else:
                date = df.index[i]

            result.append((date, df.iloc[i][level], level[0]))
            return result, p_window[k]

    return result, 1

def get_pivots(df, p_window, start, end):
    '''
        Find pivots for the input stock dataframe over a certain period
    '''
    p_window = sorted(p_window, reverse=True)

    result = []

    i = start
    while i <= end:
        result, jump = pivot_helper(df, p_window, i, result, "Low", -1)
        i = i + jump

    i = start
    while i <= end:
        result, jump = pivot_helper(df, p_window, i, result, "High", 1)
        i = i + jump

    return sorted(result, key=lambda x: x[0])

def get_pivots_index(index, p_window):
    '''
        Get pivots for an index. Index data is not supplied by yahoo finance
    '''
    df = capital_market.index_data(index=index,
                                   from_date='01-04-2024',
                                   to_date=datetime.today().strftime("%d-%m-%Y"))

    df['TIMESTAMP'] = pd.to_datetime(df['TIMESTAMP'], format='%d-%m-%Y')
    df = df.sort_values('TIMESTAMP').reset_index(drop=True)

    df = df.drop(['INDEX_NAME', 'TRADED_QTY', 'TURN_OVER'], axis = 1)

    df = df.rename(columns={'OPEN_INDEX_VAL': 'Open',
                            'HIGH_INDEX_VAL': 'High',
                            'CLOSE_INDEX_VAL': 'Close',
                            'LOW_INDEX_VAL': 'Low'})

    df['TIMESTAMP'] = timestamp_to_date(pd.to_datetime(df['TIMESTAMP']).dt)

    pivots = get_pivots(df, p_window, 0, len(df) - 1)
    filtered_pivots = []
    high = 0
    low = float('inf')
    for i in enumerate(pivots):
        i = i[0]
        if pivots[i][2] == 'L':
            if high != 0:
                if(filtered_pivots and high_tup[1] < filtered_pivots[-1][1]):
                    filtered_pivots.pop()
                else:
                    filtered_pivots.append(high_tup)
                high = 0
            if pivots[i][1] < low:
                low = pivots[i][1]
                low_tup = pivots[i]
        else:
            if low != float('inf'):
                if(filtered_pivots and low_tup[1] > filtered_pivots[-1][1]):
                    filtered_pivots.pop()
                else:
                    filtered_pivots.append(low_tup)
                low = float('inf')
            if pivots[i][1] > high:
                high = pivots[i][1]
                high_tup = pivots[i]

    if high != 0:
        if(filtered_pivots and high_tup[1] < filtered_pivots[-1][1]):
            filtered_pivots.pop()
        else:
            filtered_pivots.append(high_tup)
    elif low != float('inf'):
        if(filtered_pivots and low_tup[1] > filtered_pivots[-1][1]):
            filtered_pivots.pop()
        else:
            filtered_pivots.append(low_tup)
        low = float('inf')

    return filtered_pivots

def check_entry(df, i, trades, potential_trades):
    '''
        Checks if a potential trade can be converted to an executed trade
    '''
    for trade in potential_trades[:]:
        if trade["expiry"] == 0:
            potential_trades.remove(trade)
        else:
            if(trade["entry"] <= df.iloc[i]["High"] and trade["entry"] >= df.iloc[i]["Low"]):
                if trade["expiry"]:
                    del trade["expiry"]
                trade["date"] = df.index[i]
                trades.append(trade)
                potential_trades.remove(trade)
            else:
                trade["expiry"] -= 1


def calculate_trade_period(date1, date2):
    '''
        Returns the number of days a partcular trade was held
    '''
    return abs((datetime.strptime(date1, '%Y-%m-%d') - datetime.strptime(date2, '%Y-%m-%d')).days)

def calculate_cagr(begin_value, end_value, holding_period):
    '''
        Returns the CAGR of a trade
    '''
    if holding_period == 0:
        return 0
    holding_period_years = holding_period/365
    cagr = ((end_value / begin_value) ** (1 / holding_period_years)) - 1
    return round(cagr * 100)
