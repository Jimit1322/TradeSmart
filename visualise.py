'''
    Candlestick chart visualiser for suggested stocks
'''
from lightweight_charts import Chart
import yfinance as yf
import pandas as pd
from params import params
import helper as hp

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
                alignments=('center', 'center', 'center', 'center', 'center'),
                position='left', func=lambda t: on_row_click(chart, line, t)
            )

def ema(df, period: int = 44):
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
    df_w = stock.history(start='2020-01-01', interval='1wk')
    levels = hp.get_support_levels(df_w, [5, 10], 0.1)
    return df, levels

def update_chart(df, chart: Chart, line, sym, levels):
    '''
        Updates chart with new bar data
    '''
    line.set(
        ema(df, period=44)
    )
    for level in levels:
        line = chart.horizontal_line(level[1])

    chart.topbar['Symbol'].set(sym)
    chart.set(df)

def on_row_click(chart: Chart, line, row):
    '''
        Displays stock info for the clicked row
    '''
    if row['Symbol'] != " ":
        chart.clear_horizontal_lines()
        df, levels = get_historic_data(row['Symbol'])
        update_chart(df, chart, line, row['Symbol'], levels)

def visualise():
    '''
        Renders stock data in the form of candles
    '''
    chart = init_chart()
    line = init_line(chart, 'EMA 44')
    table = init_table(chart, line)

    for param in params:
        strat = param["strat"]
        stock_data = param["data"]
        r = table.new_row(" ", " ", strat, " ", " ")
        r.background_color('Symbol', "#ffffff")
        r.background_color('Trades', "#ffffff")
        r.background_color('Return', "#ffffff")
        r.background_color('CAGR', "#ffffff")
        if strat in ["EMA", "MACD", "BTST"]:
            for row in stock_data[1:]:
                if not row:
                    break
                table.new_row(row[0], row[1]+row[2], row[5], row[6], row[8])
    chart.topbar.textbox('Symbol', '')
    df, levels = get_historic_data(stock_data[1][0])
    update_chart(
        df,
        chart,
        line,
        stock_data[1][0],
        levels
    )

    chart.show(block=True)
