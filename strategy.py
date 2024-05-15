import helper as hp

def ema(df, i, param, use_pivots, trades, potential_trades):
    
    t = param["trend_coefficient"]
    e = param["adjusted_entry_coefficient"]
    sl = param["sl"]
    target = param["target"]
    D = param["window"]
    pivot_window = param["pivot_window"]
    
    slope1 = hp.get_slope(df, D, i)
    slope2 = hp.get_slope(df, int(D/2), int(i - D/2))
    
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
            else:
                if k == 1:
                    return
                else:
                    potential_trades.append(
                        {
                            "entry": (1-k*e) * daily["EMA"],
                            "target": (1 + target) * (1-k*e) * daily["EMA"],
                            "stoploss": (1 - sl) * (1-k*e) * daily["EMA"],
                            "multiplier": 1,
                            "expiry": 5
                        }
                    )
                    
        if use_pivots:
            pivots = hp.get_pivots(df, pivot_window, i - 100, i)
            if not pivots[1]["High"] or pivots[0]["High"][-1][1] > pivots[1]["High"][-1][1]:
                target = pivots[0]["High"][-1][1]  
            else:
                target = pivots[1]["High"][-1][1]
            # if target/entry >= 1.05:
            #     return entry, target

def index():
    pass     
    