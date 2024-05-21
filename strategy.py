'''
    Trading strategies are defined here
'''
import helper as hp

def ema(df, i, param, trades):
    '''
        Checks the validity of the EMA setup and takes trade accordingly
    '''
    t = param["trend_coefficient"]
    e = param["adjusted_entry_coefficient"]
    sl = param["sl"]
    target = param["target"]
    d = param["window"]

    slope1 = hp.get_slope(df, d, i)
    slope2 = hp.get_slope(df, int(d/2), int(i - d/2))

    daily = df.iloc[i]
    if(slope1 > t and slope2 > t and df["Low"].iloc[i-1] >= df["EMA"].iloc[i-1]):
        for k in range(1, 3):
            if((1-k*e) * daily["EMA"]  <= daily["High"] and (1-k*e) * daily["EMA"] >= daily["Low"]):
                trades.append(
                    {
                        "entry": (1-k*e) * daily["EMA"],
                        "target": (1 + target) * (1-k*e) * daily["EMA"],
                        "stoploss": (1 - sl) * (1-k*e) * daily["EMA"],
                        "multiplier": 1,
                        "date": df.index[i],
                    }
                )

        if param["pivot_d"] is not None:
            pivot_window = param["pivot_d"]
            pivots = hp.get_pivots(df, pivot_window, i - 100, i)
            if not pivots[1]["High"] or pivots[0]["High"][-1][1] > pivots[1]["High"][-1][1]:
                target = pivots[0]["High"][-1][1]
            else:
                target = pivots[1]["High"][-1][1]
            # if target/entry >= 1.05:
            #     return entry, target

def price_action():
    '''
        In an uptrending stock, check if the price is taking support on any pivots.
        If yes, take a trade.
        Support can be of types:
            1) Retesting a high pivot after a breakout
            2) Retesting a low pivot
            3) Retesting a confluence of multiple pivots.
    '''


def index(data, pivots, benchmark_data, sector_data, row):
    '''
        Populates sector_data with the change in price of stock for each swing in the index
    '''
    for df in data.values():
        for p in enumerate(pivots):
            p = p[0]
            q = p + 1
            if q >= len(pivots):
                continue

            benchmark_change = round((pivots[q][1] - pivots[p][1]) * 100/pivots[p][1], 2)
            benchmark_data.append(benchmark_change)

            data_p = df[df.index == pivots[p][0]]
            data_q = df[df.index == pivots[q][0]]

            if not data_p.empty and not data_q.empty:
                if pivots[p][2] == 'H':
                    delta = (data_q["Low"].values[0] - data_p["High"].values[0])/ \
                        data_p["High"].values[0]
                else:
                    delta = (data_q["High"].values[0] - data_p["Low"].values[0])/data_p["Low"].values[0]

                delta = round(delta, 2)
            else:
                delta = "NaN"

            if row["INDUSTRY"] in sector_data:
                if row["SYMBOL"] in sector_data[row["INDUSTRY"]]:
                    sector_data[row["INDUSTRY"]][row["SYMBOL"]].append(delta)
                else:
                    sector_data[row["INDUSTRY"]][row["SYMBOL"]] = [delta]
            else:
                sector_data[row["INDUSTRY"]] = { row["SYMBOL"]: [delta] }
