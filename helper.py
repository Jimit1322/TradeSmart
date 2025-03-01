'''
    Helpers
'''

from pathlib import Path
import csv
from datetime import datetime, timedelta
from itertools import combinations
from nselib import capital_market
import pandas as pd
from params import params

mapper = {
    'Financial Services': 'Finserv', 
    'Diversified': 'Diverse', 
    'Capital Goods': 'Cap Goods',
    'Construction Materials': 'Construct. Mat.', 
    'Chemicals': 'Chemicals', 
    'Healthcare': 'Health', 
    'Power': 'Power', 
    'Metals & Mining': 'Metal', 
    'Services': 'Services', 
    'Oil Gas & Consumable Fuels': 'OilGas', 
    'Fast Moving Consumer Goods': 'FMCG', 
    'Consumer Services': 'Cons. Serv.', 
    'Information Technology': 'IT', 
    'Textiles': 'Textiles', 
    'Automobile and Auto Components': 'Auto', 
    'Consumer Durables': 'Cons. Dura.', 
    'Telecommunication': 'Telecom', 
    'Realty': 'Realty', 
    'Forest Materials': 'Forest Mat.', 
    'Construction': 'Cons.', 
    'Media Entertainment & Publication': 'Media'
}

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

def verify_slope(df, d, i, trend):
    '''
        slope in terms of percentage for 2 price points separated over d days
    '''
    if abs(i-d) > len(df):
        return False
    change_percentage = (df["EMA"].iloc[i] - df["EMA"].iloc[i-d]) * 100 / df["EMA"].iloc[i-d]
    return change_percentage/d > trend

def pivot_helper(df, p_window, i, result, level, multiplier):
    '''
       Helper for checking if the High / Low of the candle is a pivot
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

def filter_pivots(pivots):
    '''
        Pivots filter
    '''
    filtered_pivots = []
    high = 0
    low = float('inf')
    high_tup = low_tup = []
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

    if filtered_pivots[0][2] == 'L':
        filtered_pivots = filtered_pivots[1:]
    return filtered_pivots

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

def get_support_levels(df, p_window, window):
    '''
        Checks for price support in the last 100 days
    '''
    if df.empty:
        return None
    if len(df) > window:
        start_date = df.iloc[-window].name
        start = len(df) - window
        # slope1 = get_slope(df, 50, -1)
        # slope2 = get_slope(df, 50, -51)
    else:
        start_date = df.iloc[0].name
        start = 0
        # slope1 = get_slope(df, int(len(df)/2), -1)
        # slope2 = get_slope(df, int(len(df)/2), int(-len(df)/2) + 1)
    pivots = get_pivots(df, p_window, start, len(df) - 1)
    end_date = df.iloc[-1].name
    valid_pivots = []
    for pivot in pivots[::-1]:
        if pivot[0] < start_date or pivot[0] > end_date:
            break
        valid_pivots.append(pivot)
    return valid_pivots

def get_index_pivots(param):
    '''
        Get pivots for an index. Index data is not supplied by yahoo finance
    '''
    p_window = param["pivot_d"]
    index = param["index"]
    from_date = param["from"]
    df = capital_market.index_data(index=index,
                                   from_date=from_date,
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
    return filter_pivots(pivots)

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
    holding_period_years = holding_period/252
    cagr = ((end_value / begin_value) ** (1 / holding_period_years)) - 1
    return round(cagr * 100)

def csv_to_list(sector):
    '''
        Converts csv sector data to python list data structure
    '''
    sector_data = {}
    directory_path = Path(f"data/{sector}")
    for item in directory_path.iterdir():
        if item.is_file():
            data = []
            with item.open('r') as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if not row[0]:
                        break
                    data.append(row)
            sector_data[item.name.split('.')[0]] = data
    return sector_data

def csv_recommend_to_list():
    '''
        Converts csv stock recommendation data to python list data structure
    '''
    for param in params:
        csv_file = f'output/{param["strat"]}.csv'
        data = []
        with open(csv_file, mode='r', encoding='utf-8') as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                if not row[0]:
                    break
                data.append(row)
        param["data"] = data

def intersection_helper(l1, l2):
    '''
        Finds intersection of 2 lists of stocks
    '''
    d = {}
    intersection = []
    for stock in l1:
        d[stock] = 1

    for stock in l2:
        if stock in d:
            intersection.append(stock)
    return intersection

def find_confluences():
    '''
        Finds the confluence of stocks suggested by various strategies
    '''
    confluences = {}
    strats = [str(i) for i in range(len(params))]
    result = []
    for r in range(1, len(strats) + 1):
        comb = combinations(strats, r)
        result.extend([''.join(c) for c in comb])

    for r in result:
        if len(r) == 1:
            confluences[f"{r}"] = [row[0] for row in params[int(r)]["data"][1:]]
        else:
            confluences[f"{r}"] = intersection_helper(confluences[r[0:-1]], confluences[r[-1]])

    return confluences
