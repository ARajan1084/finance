import traceback
import yfinance as yf
from trader.models import TickerInfo, DailyStockMarketData
from django.core.management.base import BaseCommand, CommandError
from multiprocessing.pool import Pool
import numpy as np
from .trader_commands_functions import process_entries
import multiprocessing
from tdqm_l import tqdm as tdqm


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            tickers = []  # list of tickers
            for ticker in TickerInfo.objects.all():
                tickers.append(ticker.ticker)
            tickers_lists = np.array_split(tickers, 2)
            for ticker_list in tickers_lists:
                df = yf.download(tickers=ticker_list.tolist(), period='5y', interval='1d', group_by='ticker', threads=True)
                entries = self.parallelize_dataframe(df, process_entries, multiprocessing.cpu_count())
                del df
                print(len(entries), 'entries to create.')
                DailyStockMarketData.objects.bulk_create(entries, batch_size=1000)
                del entries

            self.stdout.write(self.style.SUCCESS('Successfully populated the daily stock market table'))
        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to populate daily stock market data table')

    def parallelize_dataframe(self, df, func, n_cores=4):
        multiprocessing.set_start_method('fork', True)

        df_split = np.array_split(df, n_cores)
        with Pool(n_cores) as pool:
            entries = list(tdqm(pool.imap(func, df_split), total=len(df_split)))
        entries = [ent for sublist in entries for ent in sublist]
        return entries

