'''
    Candlestick chart visualiser for suggested stocks
'''
from lightweight_charts import Chart
import yfinance as yf
import pandas as pd
import helper as hp
from params import params

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

def init_table(chart: Chart, line, h_lines):
    '''
        Initialise a table
    '''
    return chart.create_table(
                width=0.3,
                height=1,
                headings=('Symbol', 'Trades', 'PF', 'Return', 'CAGR'),
                widths=(0.2, 0.2, 0.2, 0.2, 0.2),
                alignments=('center', 'center', 'center', 'center', 'center'),
                position='left',
                draggable=True,
                func=lambda t: on_row_click(chart, line, t, h_lines)
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
    levels = hp.get_support_levels(df_w, [5, 10], 50)
    return df, levels

def update_chart(df, chart: Chart, line, sym, levels, h_lines):
    '''
        Updates chart with new bar data
    '''
    line.set(
        ema(df, period=44)
    )
    for h_line in h_lines:
        h_line.delete()
    h_lines.clear()
    for level in levels:
        line = chart.horizontal_line(level[1])
        h_lines.append(line)

    chart.topbar['Symbol'].set(sym)
    chart.set(df)

def on_row_click(chart: Chart, line, row, h_lines):
    '''
        Displays stock info for the clicked row
    '''
    if row['Symbol'] != " ":
        df, levels = get_historic_data(row['Symbol'])
        update_chart(df, chart, line, row['Symbol'], levels, h_lines)

def visualise():
    '''
        Renders stock data in the form of candles
    '''
    chart = init_chart()
    line = init_line(chart, 'EMA 44')
    table = init_table(chart, line, [])

    for param in params:
        strat = param["strat"]
        stock_data = param["data"]
        if len(stock_data) < 2:
            continue
        r = table.new_row(" ", " ", strat, " ", " ")
        r.background_color('Symbol', "#ffffff")
        r.background_color('Trades', "#ffffff")
        r.background_color('Return', "#ffffff")
        r.background_color('CAGR', "#ffffff")
        if strat in ["EMA", "MACD", "BTST", "DIV"]:
            for row in stock_data[1:]:
                if not row or not row[0]:
                    break
                table.new_row(row[0], row[1]+row[2], row[5], row[6], row[8])
        else:
            for row in stock_data[1:]:
                if not row or not row[0]:
                    break
                table.new_row(row[0], "-", "-", "-", "-")

    confluences = hp.find_confluences()

    chart.topbar.textbox('Symbol', '')
    chart.show(block=True)

if __name__ == '__main__':
    hp.csv_to_list()
    visualise()
