import traceback
from trader.models import TickerInfo, DailyStockMarketData
from django.core.management.base import BaseCommand, CommandError
from multiprocessing.pool import Pool
import numpy as np
from trader.trader_commands_functions import fetch_1d_ta_metrics
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

            tickers_lists = np.array_split(tickers, 5)
            multiprocessing.set_start_method('fork')
            for tickers_list in tickers_lists:
                with Pool(multiprocessing.cpu_count()) as pool:
                    entries = tdqm(pool.imap(fetch_1d_ta_metrics, tickers_list), total=len(tickers_list))
                connection.close()
                DailyStockMarketData.objects.bulk_update(entries, fields=['sma_50', 'sma_200', 'bband_h', 'bband_l'], batch_size=1000)
                del entries

            self.stdout.write(self.style.SUCCESS('Successfully updated yesterday\'s ta metrics'))

        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to update yesterday\'s ta metrics')
