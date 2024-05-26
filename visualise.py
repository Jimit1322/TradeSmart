'''
    Candlestick chart visualiser for suggested stocks
'''
from lightweight_charts import Chart
import yfinance as yf
import pandas as pd

def calculate_ema(df, period: int = 44):
    '''
        Caclulates Exponential Moving average for a stock
    '''
    return pd.DataFrame({
        'time': df.index,
        f'EMA {period}': df['Close'].ewm(span=period, adjust=False).mean()
    }).dropna()

def update_chart(df, sym):
    '''
        Updates chart with new bar data
    '''
    line.set(
        calculate_ema(df, period=44)
    )
    chart.topbar['symbol'].set(sym)
    chart.set(df)

def get_historic_data(sym):
    '''
        Gets historic data for a symbol
    '''
    stock = yf.Ticker(sym + ".NS")
    df = stock.history(start='2020-01-01', interval='1d')
    return df

def on_row_click(row):
    '''
        Displays stock info for the clicked row
    '''
    df = get_historic_data(row['symbol'])
    update_chart(df, row['symbol'])

if __name__ == '__main__':
    chart = Chart(toolbox=True, width=1000, inner_width=0.8, inner_height=1)
    chart.legend(visible=True)

    line = chart.create_line('EMA 44')

    ema_stocks = pd.read_csv('output/44EMA_1d.csv')
    symbols = ema_stocks["Stock"]
    symbols = symbols[0:len(symbols)-5]

    table = chart.create_table(
                width=0.2,
                height=1,
                headings=('symbol', 'value'),
                widths=(0.7, 0.3),
                alignments=('left', 'center'),
                position='left', func=on_row_click
            )

    for symbol in symbols:
        table.new_row(symbol, '')
    chart.topbar.textbox('symbol', '')
    update_chart(
        get_historic_data(symbols[0]),
        symbols[0]
    )
    chart.show(block=True)
