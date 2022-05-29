from django.db import transaction
from tdqm import tqdm as tdqm
from trader.models import DailyStockMarketData, DailyTechnicalAnalysis
from datetime import datetime, timedelta
import pandas as pd
from ta import trend, volatility
from django.db import connection
from django.db.models import F


def fetch_1d_ta_metrics(ticker):
    connection.close()
    query = DailyStockMarketData.objects.all().filter(ticker=ticker, date__gte=datetime.now() - timedelta(200))\
        .order_by('date')\
        .only('close')
    closes = pd.Series([entry.close for entry in query], dtype='float64')

    sma_50_list = trend.sma_indicator(closes, window=50).tolist()
    sma_200_list = trend.sma_indicator(closes, window=200).tolist()
    bbands = volatility.BollingerBands(closes, window=20, window_dev=2)
    bband_h_list = bbands.bollinger_hband().tolist()
    bband_l_list = bbands.bollinger_lband().tolist()

    entries = []
    for entry, sma_50, sma_200, bband_h, bband_l in zip(query, sma_50_list, sma_200_list, bband_h_list,
                                                        bband_l_list):
        entry.sma_50 = sma_50
        entry.sma_200 = sma_200
        entry.bband_h = bband_h
        entry.bband_l = bband_l
        entries.append(entry)

    del sma_50_list
    del sma_200_list
    del bbands
    del closes
    return entries


def generate_ta_metric(ticker):
    connection.close()
    query = DailyStockMarketData.objects.all().filter(ticker=ticker).order_by('date').only('close').exclude(close__isnull=True)
    closes = pd.Series([entry.close for entry in query], dtype='float64')

    sma_50_list = trend.sma_indicator(closes, window=50).tolist()
    sma_200_list = trend.sma_indicator(closes, window=200).tolist()
    bbands = volatility.BollingerBands(closes, window=20, window_dev=2)
    bband_h_list = bbands.bollinger_hband().tolist()
    bband_l_list = bbands.bollinger_lband().tolist()

    entries = []
    for entry, sma_50, sma_200, bband_h, bband_l in zip(query, sma_50_list, sma_200_list, bband_h_list,
                                                        bband_l_list):
        entry.sma_50 = sma_50
        entry.sma_200 = sma_200
        entry.bband_h = bband_h
        entry.bband_l = bband_l
        entries.append(entry)

    del sma_50_list
    del sma_200_list
    del bbands
    del closes
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


@transaction.atomic
def update_golden_crosses(tickers):
    for ticker in tickers:
        query = DailyStockMarketData.objects.all().filter(ticker=ticker,
                                                          date__gte=datetime.now() - timedelta(3)).order_by('date')
        old = None
        for entry in query:
            if entry.sma_50 is None or entry.sma_200 is None:
                continue
            if entry.sma_50 > entry.sma_200:
                if old is None:
                    break
                elif old is True:
                    DailyTechnicalAnalysis(ticker=ticker, date=entry.date, category='golden_cross').save()
                    break
            else:
                old = True


@transaction.atomic
def update_death_crosses(tickers):
    for ticker in tickers:
        query = DailyStockMarketData.objects.all().filter(ticker=ticker, sma_50__lte=F('sma_200'),
                                                          date__gte=datetime.now() - timedelta(3)).order_by('date')
        old = None
        for entry in query:
            if entry.sma_50 is None or entry.sma_200 is None:
                continue
            if entry.sma_50 < entry.sma_200:
                if old is None:
                    break
                elif old is True:
                    DailyTechnicalAnalysis(ticker=ticker, date=entry.date, category='').save()
                    break
            else:
                old = True