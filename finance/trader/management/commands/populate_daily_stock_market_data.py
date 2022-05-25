import multiprocessing
import traceback
import yfinance as yf
from trader.models import TickerInfo, DailyStockMarketData
from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from multiprocessing.pool import Pool
import numpy as np
from ta import trend, volatility


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            tickers = []  # list of tickers
            for ticker in TickerInfo.objects.all():
                tickers.append(ticker.ticker)

            df = yf.download(tickers=tickers, period='3y', interval='1d', group_by='ticker', threads=True)
            entries = self.process_entries(df)
            print(len(entries), 'entries to create.')
            DailyStockMarketData.objects.bulk_create(entries, 900)

            for ticker in tickers:
                query = DailyStockMarketData.objects.all().filter(ticker=ticker).order_by('date').only('close')
                closes = pd.Series([entry.close for entry in query])

                sma_50_list = trend.sma_indicator(closes, window=50).tolist()
                sma_200_list = trend.sma_indicator(closes, window=200).tolist()
                bbands = volatility.BollingerBands(closes, window=20, window_dev=2)
                bband_h_list = bbands.bollinger_hband().tolist()
                bband_l_list = bbands.bollinger_lband().tolist()

                for entry, sma_50, sma_200, bband_h, bband_l in zip(query, sma_50_list, sma_200_list, bband_h_list, bband_l_list):
                    entry.sma_50 = sma_50
                    entry.sma_200 = sma_200
                    entry.bband_h = bband_h
                    entry.bband_l = bband_l
                    entry.save()

            self.stdout.write(self.style.SUCCESS('Successfully populated the daily stock market table'))
        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to populate daily stock market data table')

    def parallelize_dataframe(self, df, func, n_cores=4):
        multiprocessing.set_start_method('fork')
        df_split = np.array_split(df, n_cores)
        with Pool(n_cores) as pool:
            entries = pool.map(func, df_split)
        return entries

    def process_entries(self, df):
        entries = []
        for ticker, data in df.groupby(level=0, axis=1):
            for date, row in data.iterrows():
                entry = DailyStockMarketData(ticker=ticker,
                                             date=date,
                                             open=row[ticker]['Open'],
                                             close=row[ticker]['Close'],
                                             adj_close=row[ticker]['Adj Close'],
                                             volume=row[ticker]['Volume'])
                entries.append(entry)
        return entries
