import traceback
from trader.models import TickerInfo, DailyStockMarketData
from django.core.management.base import BaseCommand, CommandError
from multiprocessing.pool import Pool
import numpy as np
from trader.trader_commands_functions import generate_ta_metric
import multiprocessing
from tdqm_l import tqdm as tdqm
from django.db import connection


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            tickers = []  # list of tickers
            for ticker in TickerInfo.objects.all():
                tickers.append(ticker.ticker)

            tickers_lists = np.array_split(tickers, 16)
            multiprocessing.set_start_method('fork')
            for tickers_list in tickers_lists:
                with Pool(multiprocessing.cpu_count()) as pool:
                    entries = [entry for sublist in tdqm(pool.imap(generate_ta_metric, tickers_list), total=len(tickers_list)) for entry in sublist]
                connection.close()
                DailyStockMarketData.objects.bulk_update(entries, fields=['sma_50', 'sma_200', 'bband_h', 'bband_l', 'rsi'], batch_size=1000)
                del entries
            self.stdout.write(self.style.SUCCESS('Successfully generated ta metrics'))
        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to populate daily stock market data table')
