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
            #Trade success
            win += 1
            profit += trade["multiplier"] * (trade["target"] - trade["entry"])/trade["entry"]
            cumu_return *= trade["target"]/trade["entry"]
            holding_period += hp.calculate_trade_period(trade["date"], current_date)
            # print(f"{trade['date']}\t{current_date}\t Win")
            trades.remove(trade)
            continue

        if(trade["stoploss"] <= day["High"] and trade["stoploss"] >= day["Low"]):

            #Trade failure
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
        For each stock scan through the historic data and check if a strategy setup is met.
        If yes, create a trade. 
        While iterating over the data, we create trades and check existing trades.
    '''
    win = lose = 0
    profit = loss = 0
    trades = []
    potential_trades = []
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

            st.ema(df, day, param, False, trades, potential_trades)

        cumu_return = cumu_return - 1
        cagr = hp.calculate_cagr(1, 1 + cumu_return, holding_period)

        #Backtesting completed, check profits and losses
        profit, loss = round(profit, 2), round(loss, 2)
        return win, lose, profit, loss, round(cumu_return, 2), cagr, holding_period

def is_ema(df):
    '''
        Check for the EMA setup on the present day
    '''
    upper_bound = df["EMA"].iloc[-1] * 1.02
    lower_bound = df["EMA"].iloc[-1] * 0.98
    if not (df["Low"].iloc[-1] > upper_bound or df["High"].iloc[-1] < lower_bound):

        slope1 = hp.get_slope(df, 25, -1)
        slope2 = hp.get_slope(df, 25, -26)

        #Check uptrend
        if(slope1 > 0.1 and slope2 > 0.1):
            return True

    return False


nifty500_stocks = pd.read_csv('data/nifty500.csv')

for i in enumerate(params):
    i = i[0]
    if params[i]["strat"] == "index":
        pivots = hp.get_pivots_index(params[i])
        sector_data = {}
    if params[i]["strat"] == "EMA":
        print("Stock\t\t\tWin\tLose\tP\tL\tPF\tReturn\tCAGR")
        TP = [0 for param in params]
        TL = [0 for param in params]
        C = 0
        H = 0
    for index, row in nifty500_stocks.iterrows():
        stock = yf.Ticker(row['SYMBOL'] + ".NS")
        listing_date = hp.parse_date(row['DATE OF LISTING'], "%d-%b-%Y", "%Y-%m-%d")
        df_D = stock.history(start=listing_date, interval='1d')
        if df_D.empty:
            print("Dataframe is empty")
            continue
        df_D = df_D.drop(['Dividends', 'Stock Splits'], axis = 1)
        df_D.index = hp.timestamp_to_date(df_D.index)

        if params[i]["strat"] == "index":
            benchmark_data = []
            st.index(df_D, pivots, benchmark_data, sector_data, row)

        if params[i]["strat"] == "EMA":
            #Creating Exponential Moving Average
            df_D['EMA'] = df_D['Close'].ewm(span=params[i]["ema"], adjust=False).mean()
            if is_ema(df_D):
                s, f, P, L, c_r, c, h = backtest(df_D, params[i])

                if L == 0:
                    continue

                H += h
                C += c*h
                TP[i] = TP[i] + P
                TL[i] = TL[i] + L

                if len(row['SYMBOL']) > 7:
                    print(f"{row['SYMBOL']}\t\t{s}\t{f}\t{P}\t{L}\t{round(P/L, 2)}\t{c_r}\t{c}")
                else:
                    print(f"{row['SYMBOL']}\t\t\t{s}\t{f}\t{P}\t{L}\t{round(P/L, 2)}\t{c_r}\t{c}")


for i in enumerate(params):
    i = i[0]
    if params[i]["strat"] == "EMA":
        print(f"Profit Factor: {TP[i]/TL[i]}")
        print(f"Net CAGR: {C/H}")
    elif params[i]["strat"] == "index":
        data = []
        row = ['Date','Nifty500']
        for sector, stocks in sector_data.items():
            row.append(hp.mapper[sector])
        data.append(row)
        for k in enumerate(benchmark_data):
            k = k[0]
            row = [f"{pivots[k][0]} - {pivots[k+1][0]}",benchmark_data[k]]
            for sector, stocks in sector_data.items():
                T = 0
                S = 0
                for stock, change in stocks.items():
                    if change[k] == "NaN":
                        continue
                    S += 1
                    T += change[k]
                row.append(round(T * 100/S, 2))
            data.append(row)

        # Write data to the CSV file
        pd.DataFrame(data).to_csv('output.csv', index=False)
