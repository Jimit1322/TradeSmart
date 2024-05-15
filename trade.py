import pandas as pd
#import matplotlib.pyplot as plt
import yfinance as yf
#import mplfinance as mpf
import strategy as st
import helper as hp
from params import params
# from nsetools import Nse
# import nsepython

# Stock data: https://archives.nseindia.com/content/equities/EQUITY_L.csv
# Yahoo API doc: https://python-yahoofinance.readthedocs.io/en/latest/api.html
# index data: https://medium.com/@TejasEkawade/getting-indian-stock-prices-using-python-19f8c83d2015

def check_trades(trades,
                 day,
                 profit, loss,
                 win, lose,
                 holding_period,
                 cumu_return):
    current_date = day.name
    for trade in trades[:]: #Looping over trades[:] instead of trades as we are modifying

        # if(trade["date"] == current_date):
        #     check_5min(trade, ticker)

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
    #print(profit, loss, win, lose)
    return profit, loss, win, lose, holding_period, cumu_return

def backtest(df, param):
    win = lose = 0
    profit = loss = 0
    trades = []
    potential_trades = []
    holding_period = 0
    cumu_return = 1

    if param["strat"] == "EMA":

        #Creating Exponential Moving Average
        df["EMA"] = df['Close'].ewm(span=param["ema"], adjust=False).mean()

        for k in range(100 + param["ema"], len(df)):

            #hp.check_entry(df, i, trades, potential_trades)

            profit, loss, win, lose, holding_period, cumu_return = check_trades(trades,
                                                                                df.iloc[k],
                                                                                profit, loss,
                                                                                win, lose,
                                                                                holding_period,
                                                                                cumu_return)

            st.ema(df, k, param, False, trades, potential_trades)

        cumu_return = cumu_return - 1
        cagr = hp.calculate_cagr(1, 1 + cumu_return, holding_period)

        #Backtesting completed, check profits and losses
        profit, loss = round(profit, 2), round(loss, 2)
        return win, lose, profit, loss, round(cumu_return, 2), cagr, holding_period

    # elif(param["strat"] == "index"):
    #     st.index(df)


def is_44EMA(df):

    #Creating Exponential Moving Average
    df['EMA'] = df['Close'].ewm(span=44, adjust=False).mean()

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

TP = [0 for param in params]
TL = [0 for param in params]
C = 0
H = 0
pf_stocks = {}

for i in enumerate(params):
    i = i[0]
    if params[i]["strat"] == "index":
        pivots = hp.get_pivots_index("Nifty 500", params[i]["pivot_window"])
        sector_data = {}
    elif params[i]["strat"] == "EMA":
        print("Stock\t\t\tWin\tLose\tP\tL\tPF\tReturn\tCAGR")
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
            for p in enumerate(pivots):
                p = p[0]
                q = p + 1
                if q >= len(pivots):
                    continue
                
                benchmark_change = round((pivots[q][1] - pivots[p][1]) * 100/pivots[p][1], 2)
                benchmark_data.append(benchmark_change)

                data_p = df_D[df_D.index == pivots[p][0]]
                data_q = df_D[df_D.index == pivots[q][0]]

                if not data_p.empty and not data_q.empty:
                    if pivots[p][2] == 'H':
                        price_change = (data_q["Low"].values[0] - data_p["High"].values[0])/ data_p["High"].values[0]
                    else:
                        price_change = (data_q["High"].values[0] - data_p["Low"].values[0])/ data_p["Low"].values[0]

                    price_change = round(price_change, 2)
                else:
                    price_change = "NaN"

                if row["INDUSTRY"] in sector_data:
                    if row["SYMBOL"] in sector_data[row["INDUSTRY"]]:
                        sector_data[row["INDUSTRY"]][row["SYMBOL"]].append(price_change)
                    else:
                        sector_data[row["INDUSTRY"]][row["SYMBOL"]] = [price_change]
                else:
                    sector_data[row["INDUSTRY"]] = { row["SYMBOL"]: [price_change] }

        if params[i]["strat"] == "EMA":
            if is_44EMA(df_D):
                pf_stocks[row['SYMBOL']] = [0 for param in params]
                s, f, P, L, c_r, c, h = backtest(df_D, params[i])

                if L == 0:
                    continue

                H += h
                C += c*h
                TP[i] = TP[i] + P
                TL[i] = TL[i] + L

                pf_stocks[row['SYMBOL']][i] = P/L
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
        for k in enumerate(benchmark_data):
            k = k[0]
            print(f"Benchmark: {benchmark_data[k]}")
            for sector, stocks in sector_data.items():
                total = 0
                for stock, change in stocks.items():
                    total += change[k]
                print(f"{sector}:\t\t{round(total * 100/len(stocks), 2)}")
