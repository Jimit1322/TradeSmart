'''
    Trading strategies are defined here
'''
import helper as hp

def ema(df, i, param, trades):
    '''
        Checks the validity of the EMA setup and takes trade accordingly
    '''
    t = param["trend"]
    e = param["adjusted_entry"]
    sl = param["sl"]
    target = param["target"]
    d = param["window"]

    daily = df.iloc[i]
    if(hp.verify_slope(df, d, i, t) and
       hp.verify_slope(df, int(d/2), int(i - d/2), t) and
       df["Low"].iloc[i-1] >= df["EMA"].iloc[i-1]):
        for k in range(1, 3):
            if((1-k*e) * daily["EMA"]  <= daily["High"] and (1-k*e) * daily["EMA"] >= daily["Low"]):
                trades.append(
                    {
                        "entry": (1-k*e) * daily["EMA"],
                        "target": (1 + target) * (1-k*e) * daily["EMA"],
                        "stoploss": (1 - sl) * (1-k*e) * daily["EMA"],
                        "multiplier": 1,
                        "date": df.index[i],
                        "expiry": None
                    }
                )

        if param["pivot"] is not None:
            pivot_window = param["pivot"]
            pivots = hp.get_pivots(df, pivot_window, i - 100, i)
            if not pivots[1]["High"] or pivots[0]["High"][-1][1] > pivots[1]["High"][-1][1]:
                target = pivots[0]["High"][-1][1]
            else:
                target = pivots[1]["High"][-1][1]
            # if target/entry >= 1.05:
            #     return entry, target

def macd(df, i, param, trades):
    '''
        If:
            1) Uptrend (Above 200 EMA)
            2) Both signal line and macd line below the zero line
            3) The abs difference of the signal line and zero line is lesser than that
               on the previous day
        
            Take a long trade  
    '''
    sl = param["sl"]
    target = param["target"]

    daily = df.iloc[i]
    prev = df.iloc[i-1]
    if not param["can_trade"]:
        if prev["MACD"] < prev["Signal"] and \
            abs(daily["MACD"] - daily["Signal"]) > abs(prev["MACD"] - prev["Signal"]):
            param["can_trade"] = True

    if daily["Low"] > daily["EMA"] and \
        daily["MACD"] < daily["Signal"] and daily["Signal"] < 0 and \
            abs(daily["MACD"] - daily["Signal"]) <= abs(prev["MACD"] - prev["Signal"]):

        if param["can_trade"]:
            trades.append(
                {
                    "entry": daily["Open"],
                    "target": (1 + target) * daily["Open"],
                    "stoploss": (1 - sl) * daily["Open"],
                    "multiplier": 1,
                    "date": df.index[i],
                    "expiry": None
                }
            )
            param["can_trade"] = False

def btst(df, i, param, trades):
    '''
        If a stock sustains a certain threshold for the day, buy it and sell the next day
    '''
    sl = param["sl"]
    target = param["target"]

    daily_close = df["Close"].iloc[i]
    daily_open = df["Open"].iloc[i]

    prev_close = df["Close"].iloc[i-1]

    if (daily_open - prev_close) / prev_close > param["threshold"] \
        or (daily_close - prev_close) / prev_close > param["threshold"]:
        trades.append(
            {
                "entry": daily_close,
                "target": (1 + target) * daily_close,
                "stoploss": (1 - sl) * daily_close,
                "multiplier": 1,
                "date": df.index[i],
                "expiry": 1
            }
        )

def div(df, i, param, trades):
    '''
        If a stock is having dividends in x days, buy today and sell 1 day before the ex-date
        (if target or SL is not hit)
    '''
    sl = param["sl"]
    target = param["target"]
    candles = param["candles"]

    daily_open = df["Open"].iloc[i]

    if i + candles < len(df) and df["Dividends"].iloc[i+candles] > 0.0:
        trades.append(
            {
                "entry": daily_open,
                "target": (1 + target) * daily_open,
                "stoploss": (1 - sl) * daily_open,
                "multiplier": 1,
                "date": df.index[i],
                "expiry": candles - 1
            }
        )

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
                    delta = (data_q["High"].values[0] - data_p["Low"].values[0])/ \
                        data_p["Low"].values[0]

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
