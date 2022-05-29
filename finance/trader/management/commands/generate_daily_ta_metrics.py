import multiprocessing
import traceback
import yfinance as yf
from trader.models import TickerInfo, DailyStockMarketData
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import pandas as pd
from multiprocessing.pool import Pool
import numpy as np
from ta import trend, volatility
from .trader_commands_functions import generate_ta_metric
import multiprocessing
import threading
from tdqm import tqdm as tdqm
import itertools
from django.db import connection


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            tickers = []  # list of tickers
            for ticker in TickerInfo.objects.all():
                tickers.append(ticker.ticker)

            tickers_lists = np.array_split(tickers, 10)
            multiprocessing.set_start_method('fork')
            for tickers_list in tickers_lists:
                with Pool(multiprocessing.cpu_count()) as pool:
                    entries = [entry for sublist in tdqm(pool.imap(generate_ta_metric, tickers_list), total=len(tickers_list)) for entry in sublist]
                connection.close()
                DailyStockMarketData.objects.bulk_update(entries, fields=['sma_50', 'sma_200', 'bband_h', 'bband_l'], batch_size=1000)
                del entries
            self.stdout.write(self.style.SUCCESS('Successfully generated ta metrics'))
        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to populate daily stock market data table')
