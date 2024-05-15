# import requests
# from params import API_KEY
# from alpha_vantage.timeseries import TimeSeries

# # # replace the "demo" apikey below with your own key from https://www.alphavantage.co/support/#api-key
# # url = 'https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=IBM&interval=5min&month=2024-01&outputsize=full&apikey='+API_KEY
# # r = requests.get(url)
# # data = r.json()

# # print(data['Time Series (5min)']['2024-01-30 17:30:00'])

# # Initialize the TimeSeries object with your API key
# ts = TimeSeries(key=API_KEY, output_format='pandas')

# # Specify the stock symbol (for example, SBIN.NS for State Bank of India on NSE)
# symbol = 'RELIANCE'
# interval = '5min'
# date = '2022-04-20'

# # Get the intraday data for the specific date
# data, meta_data = ts.get_intraday(symbol=symbol, interval=interval, outputsize='compact')

# print(data)

import pandas as pd
import csv
import yfinance as yf
from nselib import capital_market
import datetime
import helper as hp

# nifty500_stocks = pd.read_csv('data/nifty500.csv')
# stocks = pd.read_csv('data/EQUITY_L.csv')

# path = 'data/media/others.csv'

# with open(path, mode='a', newline='') as file:
#         writer = csv.writer(file)
        
#         # Write the data to the CSV file
#         writer.writerow([
#             "SYMBOL","NAME OF COMPANY","SERIES","DATE OF LISTING","PAID UP VALUE","MARKET LOT","ISIN NUMBER","FACE VALUE", "TYPE"
#         ])
# for index, row in nifty500_stocks.iterrows():
#     if(row['INDUSTRY'] == 'Media Entertainment & Publication'):
#         with open(path, mode='a', newline='') as file:
#             writer = csv.writer(file)
            
#             # Write the data to the CSV file
#             writer.writerow(row)
            
# df = pd.read_csv(path)
# df = df.drop(['TYPE'], axis=1)
# df.to_csv(path, index=False)

# for index, row in nifty500_stocks.iterrows():
#     for index2, row2 in stocks.iterrows():
#         if(row['Symbol'] == row2['SYMBOL']):
#             with open('data/output.csv', mode='a', newline='') as file:
#                 writer = csv.writer(file)
                
#                 # Write the data to the CSV file
#                 writer.writerow(row2)
                
                

# # Select the column you want to append from the first DataFrame (e.g., 'column_to_append')
# column_to_append = nifty500_stocks['Industry']

# # Append the selected column as a new column to the second DataFrame
# stocks['INDUSTRY'] = column_to_append

# # Write the updated DataFrame to a new CSV file
# stocks.to_csv('data/output.csv', index=False)