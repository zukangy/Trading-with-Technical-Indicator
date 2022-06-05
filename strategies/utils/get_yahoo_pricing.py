import pandas as pd
import pandas_datareader.data as yahoo_reader


def get_benchmark(start_d=None, end_d=None, return_rnt=True):
    bm = yahoo_reader.DataReader('SPY',
                                 'yahoo',
                                 pd.Timestamp(start_d),
                                 pd.Timestamp(end_d))['Close']
    bm.index = bm.index.tz_localize('UTC')
    if return_rnt:
        return bm.pct_change(periods=1).fillna(0)
    else:
        return bm


def get_price(tickers=None, start_d=None, end_d=None):
    bm = yahoo_reader.DataReader(tickers,
                                 'yahoo',
                                 pd.Timestamp(start_d),
                                 pd.Timestamp(end_d))
    bm.index = bm.index.tz_localize('UTC')
    return bm
