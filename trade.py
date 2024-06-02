'''
    Module for backtesting strategies
'''
import pandas as pd
import yfinance as yf
import strategy as st
import helper as hp
from params import params, INDEX
import visualise as vis
import indicators as ind

# import mplfinance as mpf
# import matplotlib.pyplot as plt
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

def is_ema(df_data, trend, bound, ema):
    '''
        Check for the EMA setup on the present candle
    '''
    if df_data.empty:
        return False
    #Creating Exponential Moving Average
    df_data['EMA'] = ind.ema(df_data['Close'], ema)
    upper_bound = df_data["EMA"].iloc[-1] * (1 + bound)
    lower_bound = df_data["EMA"].iloc[-1] * (1 - bound)
    if not (df_data["Low"].iloc[-1] > upper_bound or df_data["High"].iloc[-1] < lower_bound):
        return hp.verify_slope(df_data, 25, -1, trend) and hp.verify_slope(df_data, 25, -26, trend)

    return False

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

def backtest_pre():
    '''
        Initialise the placeholders to hold backtested data
    '''
    for param in params:
        if param["strat"] == "EMA":
            data = [["Stock", "Win", "Lose", "Profit", "Loss", "PF", "Return", "Period", "CAGR"]]
        elif param['strat'] == "price-action":
            data = [ ['Stock', 'Timeframe'] ]
        elif param['strat'] == "index":
            pivots = hp.get_index_pivots(param)
            sector_data = {}
            benchmark_data = []
            data = [pivots, benchmark_data, sector_data]
        param["data"] = data

def backtest_per():
    '''
        Backtest the strategies
    '''
    nifty500_stocks = pd.read_csv(f'data/{INDEX}.csv')
    for _, row in nifty500_stocks.iterrows():
        stock = yf.Ticker(row['SYMBOL'] + ".NS")
        listing_date = hp.parse_date(row['DATE OF LISTING'], "%d-%b-%Y", "%Y-%m-%d")
        df_dict = {}

        for param in params:
            strat = param["strat"]
            tf = param["tf"]
            if tf in df_dict:
                df = df_dict[tf]
            else:
                df = stock.history(start=listing_date, interval=tf)
                if df.empty:
                    print("Dataframe is empty")
                    continue
                df = df.drop(['Dividends', 'Stock Splits'], axis = 1)
                df.index = hp.timestamp_to_date(df.index)
                df_dict[tf] = df

            if strat == "EMA":
                ema = param["ema"]
                if is_ema(df,
                        0.1,
                        param["adjusted_entry_coefficient"],
                        ema):
                    s, f, p, l, c_r, c, h = backtest(df, param)
                    if l == 0:
                        param["data"].append([row["SYMBOL"], s, f, p, l, 0, c_r, h, c])
                    else:
                        param["data"].append([row["SYMBOL"], s, f, p, l, round(p/l, 2), c_r, h, c])

            if strat == "price-action":
                levels = hp.get_support_levels(df, param["pivot"], 0.01)
                if levels:
                    param["data"].append([row["SYMBOL"], tf])

            if strat == "index":
                param["data"][1] = []
                st.index(df, param["data"][0], param["data"][1], param["data"][2], row)

def backtest_post():
    '''
        Outputs a csv and visualises a candlestick chart for suggested stocks
    '''
    for param in params:
        data = param["data"]
        if param["strat"] == "EMA":
            tp = sum(info[3] for info in data[1:])
            tl = sum(info[4] for info in data[1:])
            h = sum(info[7] for info in data[1:])
            c = sum(info[7] * info[8] for info in data[1:])
            w = sum(info[1] for info in data[1:])
            l = sum(info[2] for info in data[1:])

            pf = cagr = 0
            if tl != 0:
                pf = round(tp/tl, 2)
            if h != 0:
                cagr = round(c/h, 2)
            vis.visualise(data)
            data.extend([
                [],
                ["Profit Factor", pf],
                ["Net CAGR", cagr],
                ["Total Trades", w+l],
                ["Winning %", w/(w+l)]
            ])
            pd.DataFrame(data).to_csv(f'output/{param["ema"]}{param["strat"]}.csv',
                                      index=False,
                                      header=False)
        elif param["strat"] == "price-action":
            pd.DataFrame(data).to_csv(f'output/{param["strat"]}.csv', index=False, header=False)
        elif param["strat"] == "index":
            pivots = data[0]
            benchmark_data = data[1]
            sector_data = data[2]
            for k in enumerate(benchmark_data):
                k = k[0]
                if k%2 == 0:
                    sector_mean = {}
                for sector, stocks in sector_data.items():
                    t = 0
                    s = 0
                    if hp.mapper[sector] not in sector_mean:
                        sector_mean[hp.mapper[sector]] = []
                    for change in stocks.values():
                        if change[k] == "NaN":
                            continue
                        s += 1
                        t += change[k]
                    mean = round(t * 100/s, 2)
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
                        .to_csv(f'{param["strat"]}.csv', mode = 'a', index=False, header=False)

def main():
    '''
        Entry point
    '''
    backtest_pre()

    backtest_per()

    backtest_post()

if __name__ == '__main__':
    main()
