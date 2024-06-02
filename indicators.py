'''
    Create indicators
'''

def sma(vals, period: int = 44):
    '''
        Create a simple moving average
    '''
    return vals.rolling(window=period).mean()

def ema(vals, period: int = 44):
    '''
        Create an exponential moving average
    '''
    return vals.ewm(span=period,adjust=False).mean()

def macd(vals, short_ema: int = 12, long_ema: int = 26, signal_ema: int = 9):
    '''
        Create a MACD indicator
    '''
    md = ema(vals, short_ema) - ema(vals, long_ema)
    signal = ema(md, signal_ema)

    return md, signal

def bollinger(vals, window: int = 20):
    '''
        Create bollinger bands for a defined window
    '''
    ma = sma(vals, window)
    std = vals.rolling(window=window).std()

    lower_band = ma - (std * 2)
    upper_band = ma + (std * 2)

    return lower_band, upper_band

def rsi(vals, window: int = 14):
    '''
        Calculate rsi for closing prices
    '''
    delta = vals.diff(1)
    gain = sma(delta.where(delta > 0, 0), window)
    loss = sma(-delta.where(delta < 0, 0), window)
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def stoch_rsi(vals, window: int = 14, smooth_k: int = 3, smooth_d: int = 3):
    '''
        Calculate stochastic RSI
    '''
    data = rsi(vals, window)
    min_rsi = data.rolling(window=window).min()
    max_rsi = data.rolling(window=window).max()
    stochrsi = (data - min_rsi) / (max_rsi - min_rsi)
    stochrsi_k = sma(stochrsi, smooth_k)
    stochrsi_d = sma(stochrsi_k, smooth_d)

    return stochrsi_k, stochrsi_d
