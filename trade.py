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

def backtest(df, param):
    '''
        For each stock, scan through the historic data and check if a strategy setup is met.
        If yes, create a trade. 
        While iterating over the data, we create trades and check existing trades.
    '''
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

def is_ema(df_data, trend, bound):
    '''
        Check for the EMA setup on the present candle
    '''
    upper_bound = df_data["EMA"].iloc[-1] * (1 + bound)
    lower_bound = df_data["EMA"].iloc[-1] * (1 - bound)
    if not (df_data["Low"].iloc[-1] > upper_bound or df_data["High"].iloc[-1] < lower_bound):
        return hp.verify_slope(df_data, 25, -1, trend) and hp.verify_slope(df_data, 25, -26, trend)

    return False

def check_price_action(df_data, param):
    '''
        Check if stock is taking support on any daily, weekly, monthly pivots
        Reliability of pivots: monthly > weekly > daily
    '''
    t_f = None
    levels = hp.get_support_levels(df_data['1mo'], param["pivot_m"], 0.01)
    if levels:
        t_f = "M"
    if t_f is None:
        levels = hp.get_support_levels(df_data['1wk'], param["pivot_w"], 0.01)
        if levels:
            t_f = "W"
    if t_f is None:
        levels = hp.get_support_levels(df_data['1d'], param["pivot_d"], 0.01)
        if levels:
            t_f = "D"

    return t_f, levels


for i in enumerate(params):
    i = i[0]
    nifty500_stocks = pd.read_csv(f'data/{params[i]["index"]}.csv')
    if params[i]["strat"] == "EMA":
        data = {}
        for tf in params[i]["tfs"]:
            data[tf] = \
                [["Stock", "Win", "Lose", "Profit", "Loss", "PF", "Return", "Period", "CAGR"]]
    if params[i]["strat"] == "index":
        pivots = hp.get_index_pivots(params[i])
        sector_data = {}
    if params[i]["strat"] == "price-action":
        ema = [ ['Stock', 'Timeframe'] ]
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
            for index in enumerate(params[i]["tfs"]):
                index = index[0]
                tf = params[i]["tfs"][index]
                if is_ema(df_dict[tf],
                          0.1,
                          params[i]["adjusted_entry_coefficient"]):
                    s, f, P, L, c_r, c, h = backtest(df_dict[tf], params[i])
                    if L == 0:
                        data[tf].append([row["SYMBOL"], s, f, P, L, 0, c_r, h, c])
                    else:
                        data[tf].append([row["SYMBOL"], s, f, P, L, round(P/L, 2), c_r, h, c])

        if params[i]["strat"] == "price-action":
            tf, levels_tf = check_price_action(df_dict, params[i])
            if tf is None:
                continue
            if is_ema(df_dict[params[i]["tfs"][0]],
                        params[i]["trend_coefficient"],
                        params[i]["adjusted_entry_coefficient"]):
                ema.append([row["SYMBOL"], tf])
            else:
                data.append([row["SYMBOL"], tf])

for i in enumerate(params):
    i = i[0]
    if params[i]["strat"] == "EMA":
        for tf in params[i]["tfs"]:
            TP = sum(info[3] for info in data[tf][1:])
            TL = sum(info[4] for info in data[tf][1:])
            H = sum(info[7] for info in data[tf][1:])
            C = sum(info[7] * info[8] for info in data[tf][1:])
            W = sum(info[1] for info in data[tf][1:])
            L = sum(info[2] for info in data[tf][1:])

            PF = CAGR = 0
            if TL != 0:
                PF = round(TP/TL, 2)
            if H != 0:
                CAGR = round(C/H, 2)
            data[tf].extend([
                [],
                ["Profit Factor", PF],
                ["Net CAGR", CAGR],
                ["Total Trades", W+L],
                ["Winning %", W/(W+L)]
            ])
            pd.DataFrame(data[tf])\
                .to_csv(f'output/{params[i]["ema"]}{params[i]["strat"]}_{tf}.csv',
                        index=False,
                        header=False)
    elif params[i]["strat"] == "price-action":
        ema.extend(data)
        pd.DataFrame(ema).to_csv(f'output/{params[i]["strat"]}.csv', index=False, header=False)
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
