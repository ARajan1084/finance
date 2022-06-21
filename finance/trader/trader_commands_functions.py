from django.db import connection
from tdqm import tqdm as tdqm
from trader.models import DailyStockMarketData, DailyTASignal, TickerInfo
from datetime import datetime, timedelta
import pandas as pd
from ta import trend, volatility, momentum
from django.db import connection
from django.db.models import F
from tdqm import tqdm


def fetch_1d_ta_metrics(ticker):
    connection.close()
    query = DailyStockMarketData.objects.all().filter(ticker=ticker, date__gte=datetime.now() - timedelta(201))\
        .order_by('date')\
        .only('close')
    closes = pd.Series([entry.close for entry in query], dtype='float64')

    sma_50_list = trend.sma_indicator(closes, window=50).tolist()
    sma_200_list = trend.sma_indicator(closes, window=200).tolist()
    bbands = volatility.BollingerBands(closes, window=20, window_dev=2)
    bband_h_list = bbands.bollinger_hband().tolist()
    bband_l_list = bbands.bollinger_lband().tolist()

    entry = query.last()
    entry.sma_50 = sma_50_list[-1]
    entry.sma_200 = sma_200_list[-1]
    entry.bband_l = bband_l_list[-1]
    entry.bband_h = bband_h_list[-1]

    del sma_50_list
    del sma_200_list
    del bbands
    del closes
    return entry


def generate_ta_metric(ticker):
    connection.close()
    query = DailyStockMarketData.objects.all().filter(ticker=ticker).order_by('date').only('close').exclude(close__isnull=True)
    closes = pd.Series([entry.close for entry in query], dtype='float64')

    sma_50_list = trend.sma_indicator(closes, window=50).tolist()
    sma_200_list = trend.sma_indicator(closes, window=200).tolist()
    rsi_list = momentum.rsi(closes).tolist()
    bbands = volatility.BollingerBands(closes, window=20, window_dev=2)
    bband_h_list = bbands.bollinger_hband().tolist()
    bband_l_list = bbands.bollinger_lband().tolist()

    entries = []
    for entry, sma_50, sma_200, bband_h, bband_l, rsi in zip(query, sma_50_list, sma_200_list, bband_h_list,
                                                             bband_l_list, rsi_list):
        entry.sma_50 = sma_50
        entry.sma_200 = sma_200
        entry.bband_h = bband_h
        entry.bband_l = bband_l
        entry.rsi = rsi
        entries.append(entry)

    del sma_50_list
    del sma_200_list
    del bbands
    del closes
    del rsi_list
    return entries


def process_entries(narray):
    df = pd.DataFrame(narray)
    if df.empty:
        return []
    entries = []
    for ticker, data in df.groupby(level=0, axis=1):
        for row in data.itertuples():
            entry = DailyStockMarketData(ticker=ticker,
                                         date=row.Index.to_pydatetime(),
                                         open=row._1,
                                         high=row._2,
                                         low=row._3,
                                         close=row._4,
                                         adj_close=row._5,
                                         volume=row._6)
            if entry.close is not None and entry.close != float('NaN'):
                entries.append(entry)
    return entries


def fetch_ta_signals(ticker_entries):
    print('Looking for TA signals...')
    signals = []
    for ticker, entries in tdqm(ticker_entries):
        if entries is None:
            continue
        for i in range(0, len(entries) - 1):
            window = entries[i:i+2]
            start = window[0]
            end = window[1]
            if start.sma_50 < start.sma_200 and end.sma_50 >= end.sma_200:
                signals.append(DailyTASignal(ticker=ticker, date=end.date, description='golden_cross', signal='buy'))
            elif start.sma_50 > start.sma_200 and end.sma_50 <= end.sma_200:
                signals.append(DailyTASignal(ticker=ticker, date=end.date, description='death_cross', signal='sell'))
            if start.close > start.bband_l and end.close < end.bband_l:
                signals.append(DailyTASignal(ticker=ticker, date=end.date, description='bband_l_cross', signal='buy'))
            elif start.close < start.bband_h and end.close > end.bband_h:
                signals.append(DailyTASignal(ticker=ticker, date=end.date, description='bband_h_cross', signal='sell'))
    print('Looking for RSI signals...')
    signals += fetch_rsi_signals()
    return signals


def fetch_rsi_signals():
    signals = []
    query_buy = DailyStockMarketData.objects.filter(rsi__lte=30)
    query_sell = DailyStockMarketData.objects.filter(rsi__gte=70)
    for entry in tdqm(query_buy):
        signals.append(DailyTASignal(ticker=entry.ticker, date=entry.date, description='rsi_lte_30', signal='buy'))
    for entry in tdqm(query_sell):
        signals.append(DailyTASignal(ticker=entry.ticker, date=entry.date, description='rsi_gte_70', signal='buy'))


def fetch_all_ticker_entries(only):
    query = DailyStockMarketData.objects.all().only(*only).order_by('ticker', 'date')
    return query_to_dict(query)


def fetch_all_tickers():
    query = TickerInfo.objects.all()
    tickers = []
    for entry in query:
        tickers.append(entry.ticker)
    return tickers


def fetch_ticker_entries(only, tickers):
    query = DailyStockMarketData.objects.filter(ticker__in=tickers).only(*only).order_by('ticker', 'date')
    keys = [ticker for ticker in tickers]
    ticker_entries = dict.fromkeys(keys)

    for entry in tdqm(query):
        if ticker_entries[entry.ticker] is not None:
            ticker_entries[entry.ticker].append(entry)
        else:
            ticker_entries[entry.ticker] = [entry]
    return ticker_entries


def fetch_ticker_entries_by_date(only, start_date, end_date):
    query = DailyStockMarketData.objects.filter(date__gte=start_date, date__lt=end_date).only(*only)
    return query_to_dict(query)


def query_to_dict(query):
    keys = [entry.ticker for entry in query]
    ticker_entries = dict.fromkeys(keys)
    for entry in tdqm(query):
        if ticker_entries[entry.ticker] is not None:
            ticker_entries[entry.ticker].append(entry)
        else:
            ticker_entries[entry.ticker] = [entry]
    return ticker_entries


def fetch_ticker_entries_3d(only):
    query = DailyStockMarketData.objects.all().filter(date__gte=datetime.now() - timedelta(10)).only(*only).order_by('ticker', 'date')
    ticker_entries = {}
    for entry in query:
        if entry.ticker in ticker_entries:
            ticker_entries[entry.ticker].append(entry)
        else:
            ticker_entries.update({entry.ticker: [entry]})
    return ticker_entries
