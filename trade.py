'''
    Module for backtesting strategies
'''
import pandas as pd
#import matplotlib.pyplot as plt
import yfinance as yf
#import mplfinance as mpf
import strategy as st
import helper as hp
from params import params
# from nsetools import Nse
# import nsepython

def check_trades(trades,
                 day,
                 profit, loss,
                 win, lose,
                 holding_period,
                 cumu_return):
    '''
        Checks all the trades if they have hit the target or SL. If a target is hit, register a win.
        If SL is hit (trailed or otherwise), register a loss.
    '''
    current_date = day.name
    for trade in trades[:]: #Looping over trades[:] instead of trades as we are modifying

        if(trade["target"] <= day["High"] and trade["target"] >= day["Low"]):
            win += 1
            profit += trade["multiplier"] * (trade["target"] - trade["entry"])/trade["entry"]
            cumu_return *= trade["target"]/trade["entry"]
            holding_period += hp.calculate_trade_period(trade["date"], current_date)
            # print(f"{trade['date']}\t{current_date}\t Win")
            trades.remove(trade)
            continue

        if(trade["stoploss"] <= day["High"] and trade["stoploss"] >= day["Low"]):
            lose = lose + 1
            loss = loss + trade["multiplier"] * (trade["entry"] - trade["stoploss"])/trade["entry"]
            cumu_return *= trade["stoploss"]/trade["entry"]
            holding_period += hp.calculate_trade_period(trade["date"], current_date)
            # print(f"{trade['date']}\t{current_date}\t Lose")
            trades.remove(trade)
            continue

        #If reached midway, trail the stoploss to entry price
        mid_target_price = (trade["target"] + trade["entry"]) / 2
        if(mid_target_price <= day["High"] and mid_target_price >= day["Low"]):
            trade["stoploss"] = trade["entry"]

    return profit, loss, win, lose, holding_period, cumu_return

def backtest(df_data, param):
    '''
        For each stock, scan through the historic data and check if a strategy setup is met.
        If yes, create a trade. 
        While iterating over the data, we create trades and check existing trades.
    '''
    for df in df_data.values():
        win = lose = 0
        profit = loss = 0
        trades = []
        holding_period = 0
        cumu_return = 1

        if param["strat"] == "EMA":

            for day in range(100 + param["ema"], len(df)):

                profit, loss, win, lose, holding_period, cumu_return = check_trades(trades,
                                                                                    df.iloc[day],
                                                                                    profit, loss,
                                                                                    win, lose,
                                                                                    holding_period,
                                                                                    cumu_return)

                st.ema(df, day, param, trades)

            cumu_return = cumu_return - 1
            cagr = hp.calculate_cagr(1, 1 + cumu_return, holding_period)

            #Backtesting completed, check profits and losses
            profit, loss = round(profit, 2), round(loss, 2)
            return win, lose, profit, loss, round(cumu_return, 2), cagr, holding_period

def is_ema(df_data):
    '''
        Check for the EMA setup on the present candle
    '''
    upper_bound = df_data["EMA"].iloc[-1] * 1.02
    lower_bound = df_data["EMA"].iloc[-1] * 0.98
    if not (df_data["Low"].iloc[-1] > upper_bound or df_data["High"].iloc[-1] < lower_bound):

        slope1 = hp.get_slope(df_data, 25, -1)
        slope2 = hp.get_slope(df_data, 25, -26)

        return (slope1 > 0.1 and slope2 > 0.1)

    return False

def check_price_action(df_data, param):
    '''
        Check if stock is taking support on any daily, weekly, monthly pivots
        Reliability of pivots: monthly > weekly > daily
    '''
    valid_pivots = {
        "w": hp.get_support_levels(df_data['1wk'], param["pivot_w"], 0.05),
        "m": hp.get_support_levels(df_data['1mo'], param["pivot_m"], 0.1),
    }
    support = len(valid_pivots["m"]) + len(valid_pivots["w"]) != 0
    return support, valid_pivots["w"], valid_pivots["m"]


for i in enumerate(params):
    i = i[0]
    nifty500_stocks = pd.read_csv(f'data/{params[i]["index"]}.csv')
    if params[i]["strat"] == "EMA":
        TP = [0 for param in params]
        TL = [0 for param in params]
        C = 0
        H = 0
        data = [["Stock", "Win", "Lose", "Profit", "Loss", "PF", "Return", "CAGR"]]
    if params[i]["strat"] == "index":
        pivots = hp.get_index_pivots(params[i])
        sector_data = {}
    if params[i]["strat"] == "price-action":
        ema = [ ['Stock'] ]
        data = [ [] ]

    for index, row in nifty500_stocks.iterrows():
        stock = yf.Ticker(row['SYMBOL'] + ".NS")
        listing_date = hp.parse_date(row['DATE OF LISTING'], "%d-%b-%Y", "%Y-%m-%d")
        df_dict = {}
        for tf in params[i]["tfs"]:
            df_dict[tf] = stock.history(start=listing_date, interval=tf)
            if df_dict[tf].empty:
                print("Dataframe is empty")
                continue
            df_dict[tf] = df_dict[tf].drop(['Dividends', 'Stock Splits'], axis = 1)
            df_dict[tf].index = hp.timestamp_to_date(df_dict[tf].index)

            #Creating Exponential Moving Average
            df_dict[tf]['EMA'] = df_dict[tf]['Close'].ewm(span=params[i]["ema"],adjust=False).mean()

        if params[i]["strat"] == "index":
            benchmark_data = []
            st.index(df_dict, pivots, benchmark_data, sector_data, row)

        if params[i]["strat"] == "EMA":
            if is_ema(df_dict[params[i]["tfs"][0]]):
                s, f, P, L, c_r, c, h = backtest(df_dict, params[i])

                if L == 0:
                    continue

                H += h
                C += c*h
                TP[i] = TP[i] + P
                TL[i] = TL[i] + L

                data.append([row["SYMBOL"], s, f, P, L, round(P/L, 2), c_r, c])

        if params[i]["strat"] == "price-action":
            S, s_w, s_m = check_price_action(df_dict, params[i])
            if S:
                if is_ema(df_dict[params[i]["tfs"][0]]):
                    ema.append([row["SYMBOL"]])
                else:
                    data.append([row["SYMBOL"]])

for i in enumerate(params):
    i = i[0]
    if params[i]["strat"] == "EMA":
        data.extend([[], ["Profit Factor:", round(TP[i]/TL[i], 2)], ["Net CAGR:", round(C/H, 2)]])
        pd.DataFrame(data).to_csv(f'{params[i]["strat"]}.csv', index=False, header=False)
    elif params[i]["strat"] == "price-action":
        ema.extend(data)
        pd.DataFrame(ema).to_csv(f'{params[i]["strat"]}.csv', index=False, header=False)
    elif params[i]["strat"] == "index":
        for k in enumerate(benchmark_data):
            k = k[0]
            if k%2 == 0:
                sector_mean = {}
            for sector, stocks in sector_data.items():
                T = 0
                S = 0
                if hp.mapper[sector] not in sector_mean:
                    sector_mean[hp.mapper[sector]] = []
                for stock, change in stocks.items():
                    if change[k] == "NaN":
                        continue
                    S += 1
                    T += change[k]
                mean = round(T * 100/S, 2)
                sector_mean[hp.mapper[sector]].append(mean)
            if k%2 == 1:
                header = ['Date','Nifty500']
                row1 = [f"{pivots[k-1][0]} - {pivots[k][0]}",benchmark_data[k-1]]
                row2 = [f"{pivots[k][0]} - {pivots[k+1][0]}",benchmark_data[k]]
                sector_mean = dict(sorted(sector_mean.items(), key=lambda item: item[1][0]))
                for s, mean in sector_mean.items():
                    header.append(s)
                    row1.append(mean[0])
                    row2.append(mean[1])
                data = []
                data.extend([header, row1, row2, []])
                pd.DataFrame(data)\
                    .to_csv(f'{params[i]["strat"]}.csv', mode = 'a', index=False, header=False)
