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
    print('Looking for golden and death crosses...')
    crosses = find_golden_and_death_crosses(ticker_entries)
    print('Looking for bband signals...')
    bband_signals = find_bband_signals()
    print('Looking for rsi signals...')
    rsi_signals = find_rsi_signals()
    return crosses + bband_signals + rsi_signals


def find_golden_and_death_crosses(ticker_entries):
    signals = []
    for ticker, entries in tdqm(ticker_entries):
        for i in range(0, len(entries) - 1):
            window = entries[i:i+2]
            start = window[0]
            end = window[1]
            if start.sma_50 < start.sma_200 and end.sma_50 >= end.sma_200:
                signals.append(DailyTASignal(ticker=ticker, date=end.date, description='golden_cross', signal='buy'))
            if start.sma_50 > start.sma_200 and end.sma_50 <= end.sma_200:
                signals.append(DailyTASignal(ticker=ticker, date=end.date, description='death_cross', signal='sell'))
    return signals


def find_bband_signals():
    query_bband_l = DailyStockMarketData.objects.all().filter(close__lt=F('bband_l')).only('ticker', 'date')
    query_bband_h = DailyStockMarketData.objects.all().filter(close__gt=F('bband_h')).only('ticker', 'date')
    l_signals = [DailyTASignal(ticker=entry.ticker, date=entry.date, description='lt_bband_l', signal='buy') for entry in tdqm(query_bband_l)]
    h_signals = [DailyTASignal(ticker=entry.ticker, date=entry.date, description='gt_bband_h', signal='sell') for entry in tdqm(query_bband_h)]
    return l_signals + h_signals


def find_rsi_signals():
    query_rsi_b = DailyStockMarketData.objects.all().filter(rsi__lte=30).only('ticker', 'date')
    query_rsi_s = DailyStockMarketData.objects.all().filter(rsi__gte=70).only('ticker', 'date')
    b_signals = [DailyTASignal(ticker=entry.ticker, date=entry.date, description='rsi_lte_30', signal='buy') for entry in tdqm(query_rsi_b)]
    s_signals = [DailyTASignal(ticker=entry.ticker, date=entry.date, description='rsi_gte_70', signal='sell') for entry in tdqm(query_rsi_s)]
    return b_signals + s_signals


def fetch_all_ticker_entries():
    query = DailyStockMarketData.objects.all().only('ticker', 'date', 'sma_50', 'sma_200').order_by('ticker', 'date')
    keys = [entry.ticker for entry in query]
    ticker_entries = dict.fromkeys(keys)
    for entry in tdqm(query):
        if ticker_entries[entry.ticker] is not None:
            ticker_entries[entry.ticker].append(entry)
        else:
            ticker_entries[entry.ticker] = [entry]
    return ticker_entries


def fetch_ticker_entries_3d():
    query = DailyStockMarketData.objects.all().filter(date__gte=datetime.now() - timedelta(10)).only('date', 'sma_50', 'sma_200').order_by('ticker', 'date')
    ticker_entries = {}
    for entry in query:
        if entry.ticker in ticker_entries:
            ticker_entries[entry.ticker].append(entry)
        else:
            ticker_entries.update({entry.ticker: [entry]})
    return ticker_entries
