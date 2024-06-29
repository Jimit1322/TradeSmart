'''
  Module for defining trading parameters
'''

INDEX = "NIFTY 500"

params = [
    {
      "strat": "EMA",
      "pivot": None,
      "ema": 44,
      "trend": 0.15,
      "adjusted_entry": 0.01,
      "target": 0.08,
      "sl": 0.02,
      "window": 50,
      "tf": "1d"
    },
    # {
    #   "strat": "MACD",
    #   "pivot": None,
    #   "ema": 200,
    #   "adjusted_entry": 0.01,
    #   "target": 0.08,
    #   "sl": 0.02,
    #   "window": 50,
    #   "tf": "1d",
    #   "can_trade": True
    # },
    {
      "strat": "BTST",
      "pivot": None,
      "threshold": 0.045,
      "ema": 44,
      "trend": 0.15,
      "adjusted_entry": 0.01,
      "target": 0.03,
      "sl": 0.02,
      "window": 50,
      "tf": "1d"
    },
    # {
    #   "strat": "index",
    #   "pivot_d": [5, 10],
    #   "from": '01-01-2021',
    #   "tf": "1d"
    # },
]

API_KEY = 'GY7N4KU8V7BVEUNV'

industries = {
  'Financial Services': 92, 
  'Diversified': 4, 
  'Capital Goods': 61,
  'Construction Materials': 13, 
  'Chemicals': 34, 
  'Healthcare': 46, 
  'Power': 12, 
  'Metals & Mining': 16, 
  'Services': 16, 
  'Oil Gas & Consumable Fuels': 18, 
  'Fast Moving Consumer Goods': 31, 
  'Consumer Services': 24, 
  'Information Technology': 25, 
  'Textiles': 7, 
  'Automobile and Auto Components': 34, 
  'Consumer Durables': 25, 
  'Telecommunication': 11, 
  'Realty': 11, 
  'Forest Materials': 2, 
  'Construction': 13, 
  'Media Entertainment & Publication': 6
}
