import multiprocessing
import traceback
from trader.models import TickerInfo, DailyTASignal
from django.core.management.base import BaseCommand, CommandError
from multiprocessing import Pool
from .trader_commands_functions import fetch_all_ticker_entries, fetch_ta_signals
from tdqm_l import tqdm as tdqm
import numpy as np


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            print('Fetching all entries...')
            ticker_entries = fetch_all_ticker_entries()
            ticker_entries = list(ticker_entries.items())

            signals = fetch_ta_signals(ticker_entries)
            print(len(signals), 'signals to create')
            DailyTASignal.objects.bulk_create(signals, batch_size=1000)

            self.stdout.write(self.style.SUCCESS('Successfully updated technical analysis'))
        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to update technical analysis data')
