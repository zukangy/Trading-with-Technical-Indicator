#  Moving Average Crossover

# Strategy breakdown
# 1. Select SPY100 as our universe
# 2. Enter a position if the stock's 5-day moving average crosses its 60-day moving average from below
# 3. Exit: 1) Sell a stock if its 5-day moving average crosses its 60-day moving average from above
#          2) or sell a stock if its close price is 5% below or above its entry price
# 4. Weights: rebalance the portfolio based on equal weights

import pandas as pd
from datetime import datetime
import pytz
import matplotlib.pyplot as plt

from zipline.api import (
    symbol,
    order_target_percent,
    schedule_function,
    set_slippage,
    set_commission
)
from zipline import run_algorithm
from zipline.utils.events import date_rules, time_rules
from zipline.finance.slippage import FixedSlippage, VolumeShareSlippage
from zipline.finance.commission import PerDollar, PerShare

from utils.universe import get_sp100
from utils.get_yahoo_pricing import get_benchmark


def initialize(context):
    context.universe = [symbol(t) for t in get_sp100()]
    context.short_term_window = 5
    context.long_term_window = 60
    context.SL = 0.03
    context.TP = 0.05

    schedule_function(func=handle_data, date_rule=date_rules.every_day(),
                      time_rule=time_rules.market_open(minutes=30))

    set_commission(PerDollar(0.001))
    set_slippage(VolumeShareSlippage(volume_limit=0.025,
                                     price_impact=0.05))


def handle_data(context, data):
    # always ascending by date from data.history() 2022-01-01 -> 2022-01-02
    short_term_close = data.history(context.universe, 'close', context.short_term_window + 1, '1d')
    long_term_close = data.history(context.universe, 'close', context.long_term_window + 1, '1d')
    avg_5d_today = short_term_close.iloc[1:, ].mean()
    avg_60d_today = long_term_close.iloc[1:, ].mean()
    avg_5d_yesterday = short_term_close.iloc[:-1, ].mean()
    avg_60d_yesterday = long_term_close.iloc[:-1, ].mean()
    crossover_up = (avg_5d_today > avg_60d_today) & (avg_5d_yesterday < avg_60d_yesterday)
    buy_list = crossover_up[crossover_up].index.to_list()

    crossover_down = (avg_5d_today < avg_60d_today) & (avg_5d_yesterday > avg_60d_yesterday)
    sell_list = crossover_down[crossover_down].index.to_list()

    # Exit due to stop-loss or take-profit, or when short-term ma crosses below long-term ma
    curr_holding = context.portfolio.positions
    curr_holding_stocks = list(curr_holding.keys())
    if curr_holding_stocks:
        for p in curr_holding_stocks:
            entry_price = curr_holding[p].cost_basis
            curr_price = short_term_close[p].iloc[-1,]
            if curr_price > entry_price * (1. + context.TP) or curr_price < entry_price * (1. - context.SL) \
                    or p in sell_list:
                order_target_percent(p, 0.)
                curr_holding_stocks.remove(p)

    # Enter and/or rebalance positions
    if buy_list:
        if curr_holding_stocks:
            for p in curr_holding_stocks:
                if p not in buy_list:
                    buy_list.append(p)
        weight = 1. / len(buy_list)
        for s in buy_list:
            if data.can_trade(s):
                order_target_percent(s, weight)


def before_trading_start(context, data):
    pass


start = pd.Timestamp(datetime(2015, 1, 1, tzinfo=pytz.UTC))
end = pd.Timestamp(datetime(2022, 6, 1, tzinfo=pytz.UTC))

r = run_algorithm(start=start,
                  end=end,
                  initialize=initialize,
                  # handle_data=handle_data,
                  # before_trading_start=before_trading_start,
                  benchmark_returns=get_benchmark(start_d=start.date().isoformat(),
                                                  end_d=end.date().isoformat()),
                  capital_base=1e6,
                  bundle='sharadar-eqfd')

fig, axes = plt.subplots(1, 1, figsize=(16, 5), sharex=True)
r.algorithm_period_return.plot(color='blue')
r.benchmark_period_return.plot(color='red')
plt.legend(['Algo', 'Benchmark'])
plt.ylabel("Returns", color='black', size=20)
plt.show()
