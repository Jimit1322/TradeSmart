'''
  Module for defining trading parameters
'''
params = [
    {
      "strat": "EMA",
      "pivot_d": None,
      "index": "Nifty 500",
      "ema": 44,
      "trend_coefficient": 0.15,
      "adjusted_entry_coefficient": 0.01,
      "target": 0.08,
      "sl": 0.02,
      "window": 50,
      "tfs": ["1d"]
    },
    # {
    #   "strat": "index",
    #   "pivot_d": [5, 10],
    #   "index": "Nifty 500",
    #   "from": '01-01-2021',
    #   "tfs": ["1d"]
    # },
    # {
    #   "strat": "price-action",
    #   "pivot_d": [5, 10],
    #   "pivot_w": [5, 10],
    #   "pivot_m": [5, 10],
    #   "index": "Nifty 500",
    #   "window": 100,
    #   "ema": 44,
    #   "tfs": ["1d", "1wk", "1mo"]
    # }
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
