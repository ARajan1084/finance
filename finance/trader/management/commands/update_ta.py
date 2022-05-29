import multiprocessing
import multitasking
import traceback
import yfinance as yf
from trader.models import TickerInfo, DailyStockMarketData, DailyTechnicalAnalysis
from django.core.management.base import BaseCommand, CommandError
from multiprocessing import Pool
from datetime import date, datetime, timedelta
from django.db import transaction
import time
import pandas as pd
from ta import trend, volatility
import importlib.util
import sys
from tdqm import tqdm as tdqm
from .trader_commands_functions import update_golden_crosses, update_death_crosses
import multitasking


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            multiprocessing.set_start_method('fork')
            tickers = []  # list of tickers
            for ticker in TickerInfo.objects.all():
                tickers.append(ticker.ticker)

            with Pool(multitasking.cpu_count() * 2) as pool:
                pool.map(update_golden_crosses, tickers)
            with Pool(multitasking.cpu_count() * 2) as pool:
                pool.map(update_death_crosses, tickers)

            self.stdout.write(self.style.SUCCESS('Successfully updated technical analysis'))
        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to update technical analysis data')



