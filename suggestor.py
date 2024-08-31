'''
    Suggests stocks in the present
'''
import helper as hp

def ema(df, bound):
    '''
        Checks for the EMA setup based on the current candle
    '''
    if df.empty:
        return False
    upper_bound = df["EMA"].iloc[-1] * (1 + bound)
    if df["Close"].iloc[-1] > df["EMA"].iloc[-1] and df["Close"].iloc[-1] < upper_bound:
        return True

    return False

def btst(df_data, param):
    '''
        Checks for stocks who have sustained a certain % on the current candle
    '''
    if len(df_data) < 2:
        return False
    curr_close = df_data["Close"].iloc[-1]
    curr_open = df_data["Open"].iloc[-1]
    prev_close = df_data["Close"].iloc[-2]

    if ((curr_open - prev_close) / prev_close < param["threshold"] \
        and (curr_close - prev_close) / prev_close < param["threshold"]) \
            or curr_close == curr_open:
        return False
    return True

def circuit(df_data, param):
    '''
        Check for consistent UC stocks. Capital Multiplication strategy.
    '''
    if len(df_data) < param["candles"]:
        return False
    for i in range(1, param["candles"]):
        curr_close = df_data["Close"].iloc[-i]
        curr_open = df_data["Open"].iloc[-i]
        prev_close = df_data["Close"].iloc[-i-1]

        if (curr_open - prev_close) / prev_close < param["threshold"] \
            or curr_close != curr_open:
            return False
    return True

def momentum(df_data, param):
    '''
        Check for bullish momentum in 5m tf.
    '''
    if len(df_data) < param["candles"]:
        return False
    for i in range(1, param["candles"]+1):
        curr_close = df_data["Close"].iloc[-i]
        prev_close = df_data["Close"].iloc[-i-1]

        if (curr_close - prev_close) / prev_close < param["threshold"]:
            return False
    return True

def dividend(df_data, param, ex_date):
    '''
        Buy x number of days before dividend (with some target and stoploss)
        and sell it 1 day before (at most) the ex-date
    '''
    ex_date = hp.timestamp_to_date(ex_date)
    if hp.parse_date(df_data.iloc[-1].name, "%Y-%m-%d", "%Y-%m-%d", param["candles"]) == ex_date:
        return True

def macd():
    '''
        Checks for macd strategy stocks based on the current candle
    '''
