'''
    Suggests stocks in the present
'''
import helper as hp

def ema(df_data, trend, bound):
    '''
        Checks for the EMA setup based on the current candle
    '''
    if df_data.empty:
        return False
    upper_bound = df_data["EMA"].iloc[-1] * (1 + bound)
    lower_bound = df_data["EMA"].iloc[-1] * (1 - bound)
    if not (df_data["Low"].iloc[-1] > upper_bound or df_data["High"].iloc[-1] < lower_bound):
        return hp.verify_slope(df_data, 25, -1, trend) and hp.verify_slope(df_data, 25, -26, trend)

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

    if (curr_open - prev_close) / prev_close < param["threshold"] \
        and (curr_close - prev_close) / prev_close < param["threshold"]:
        return False
    return True

def macd():
    '''
        Checks for macd strategy stocks based on the current candle
    '''
