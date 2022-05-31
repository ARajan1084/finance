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
