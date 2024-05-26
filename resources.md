# Resources

Check out the

[stocks](https://archives.nseindia.com/content/equities/EQUITY_L.csv)

[yahoo_api_doc](https://python-yahoofinance.readthedocs.io/en/latest/api.html)

[index_data](https://medium.com/@TejasEkawade/getting-indian-stock-prices-using-python-19f8c83d2015)

[Trading_Strategy](https://tradingstrategy.ai/)

[Kelly's Criterion](https://www.youtube.com/watch?v=_FuuYSM7yOo)

__f = (p/a) - (q/b)__, where

f = _fraction_ of wealth invested in every trade to _maximize_ gains
p = Probability of a _winning_ trade
q = Probability of a _losing_ trade
a = _Risk_
b = _Reward_

Let _(w, l)_ = ( N(_winning_ trades), N(_losing_ trades) )
Then, p = w/(w+l)
      q = l/(w+l)

Hence, __f = (w/a - l/b) / (w+l)__
