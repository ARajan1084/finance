import traceback
import yfinance as yf
from trader.models import TickerInfo, DailyStockMarketData
from django.core.management.base import BaseCommand, CommandError
from multiprocessing import Pool
from datetime import date, datetime, timedelta
import time
import pandas as pd
from ta import trend, volatility


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            tickers = []  # list of tickers
            for ticker in TickerInfo.objects.all():
                tickers.append(ticker.ticker)

            df = yf.download(tickers=tickers, period='1d', interval='1d', group_by='ticker')
            entries = self.process_entries(df)
            DailyStockMarketData.objects.bulk_create(entries, batch_size=1000)

            # self.generate_ta_metrics(tickers)

            self.stdout.write(self.style.SUCCESS('Successfully updated the daily stock market table'))
        except Exception:
            traceback.print_exc()
            raise CommandError('unable to update daily stock market data table')

    def process_entries(self, df):
        entries = []
        for ticker, data in df.groupby(level=0, axis=1):
            entry = DailyStockMarketData(ticker=ticker,
                                         date=data.index[0].date(),
                                         open=data[ticker]['Open'][0],
                                         high=data[ticker]['High'][0],
                                         low=data[ticker]['Low'][0],
                                         close=data[ticker]['Close'][0],
                                         adj_close=data[ticker]['Adj Close'][0],
                                         volume=data[ticker]['Volume'][0])
            entries.append(entry)
        return entries

    def generate_ta_metrics(self, tickers):
        for ticker in tickers:
            query = list(DailyStockMarketData.objects.all().filter(ticker=ticker,
                                                                   date__gte=datetime.now() - timedelta(200)).only(
                'close'))
            closes = pd.Series([entry.close for entry in query])

            sma_50_list = trend.sma_indicator(closes, window=50).tolist()
            sma_200_list = trend.sma_indicator(closes, window=200).tolist()
            bbands = volatility.BollingerBands(closes, window=20, window_dev=2)
            bband_h_list = bbands.bollinger_hband().tolist()
            bband_l_list = bbands.bollinger_lband().tolist()

            for entry, sma_50, sma_200, bband_h, bband_l in zip(query, sma_50_list, sma_200_list, bband_h_list,
                                                                bband_l_list):
                if sma_50:
                    entry.sma_50 = sma_50
                if sma_200:
                    entry.sma_200 = sma_200
                if bband_h:
                    entry.bband_h = bband_h
                if bband_l:
                    entry.bband_l = bband_l
                entry.save()

