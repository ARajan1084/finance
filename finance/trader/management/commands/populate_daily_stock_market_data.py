import traceback
import yfinance as yf
from trader.models import TickerInfo, DailyStockMarketData
from django.core.management.base import BaseCommand, CommandError
from django import db


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            tickers = []  # list of tickers
            for ticker in TickerInfo.objects.all():
                tickers.append(ticker.ticker)

            df = yf.download(tickers=tickers, period='200d', interval='1d', group_by='ticker')
            entries = []
            for ticker, data in df.groupby(level=0, axis=1):
                for date, row in data.iterrows():
                    entry = DailyStockMarketData(ticker=ticker,
                                                 date=date.date(),
                                                 open=row[ticker]['Open'],
                                                 close=row[ticker]['Close'],
                                                 adj_close=row[ticker]['Adj Close'],
                                                 volume=row[ticker]['Volume'])
                    entries.append(entry)
            print(len(entries), 'entries')
            DailyStockMarketData.objects.bulk_create(entries, 900)
            self.stdout.write(self.style.SUCCESS('Successfully populated the daily stock market table'))
        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to populate daily stock market data table')

