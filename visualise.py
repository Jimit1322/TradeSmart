'''
    Candlestick chart visualiser for suggested stocks
'''
from lightweight_charts import Chart
import yfinance as yf
import pandas as pd

def init_chart():
    '''
        Initialise a chart
    '''
    chart = Chart(toolbox=True, width=1000, inner_width=0.7, inner_height=1)
    chart.legend(visible=True)

    return chart

def init_line(chart: Chart, name):
    '''
        Initialise line on the chart
    '''
    return chart.create_line(name)

def init_table(chart: Chart, line):
    '''
        Initialise a table
    '''
    return chart.create_table(
                width=0.3,
                height=1,
                headings=('Symbol', 'Trades', 'PF', 'Return', 'CAGR'),
                widths=(0.2, 0.2, 0.2, 0.2, 0.2),
                alignments=('center', 'center', 'right', 'right', 'right'),
                position='left', func=lambda t: on_row_click(chart, line, t)
            )

def calculate_ema(df, period: int = 44):
    '''
        Caclulates Exponential Moving average for a stock
    '''
    return pd.DataFrame({
        'time': df.index,
        f'EMA {period}': df['Close'].ewm(span=period, adjust=False).mean()
    }).dropna()

def get_historic_data(sym):
    '''
        Gets historic data for a symbol
    '''
    stock = yf.Ticker(sym + ".NS")
    df = stock.history(start='2020-01-01', interval='1d')
    return df

def update_chart(df, chart, line, sym):
    '''
        Updates chart with new bar data
    '''
    line.set(
        calculate_ema(df, period=44)
    )
    chart.topbar['Symbol'].set(sym)
    chart.set(df)

def on_row_click(chart, line, row):
    '''
        Displays stock info for the clicked row
    '''
    df = get_historic_data(row['Symbol'])
    update_chart(df, chart, line, row['Symbol'])

def visualise(stock_data):
    '''
        Renders stock data in the form of candles
    '''
    chart = init_chart()
    line = init_line(chart, 'EMA 44')
    table = init_table(chart, line)

    for row in stock_data[1:]:
        table.new_row(row[0], row[1]+row[2], row[5], row[6], row[8])
    chart.topbar.textbox('Symbol', '')
    update_chart(
        get_historic_data(stock_data[1][0]),
        chart,
        line,
        stock_data[1][0]
    )

    chart.show(block=True)
