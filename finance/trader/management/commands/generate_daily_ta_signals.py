import traceback
from trader.models import DailyTASignal
from django.core.management.base import BaseCommand, CommandError
from trader.trader_commands_functions import fetch_all_tickers, fetch_ticker_entries, fetch_ta_signals
import numpy as np
from colorama import Fore, Style


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            print('Fetching all entries...')
            tickers = fetch_all_tickers()
            tickers_lists = np.array_split(tickers, 5)
            for i, ticker_list in zip(range(1, len(tickers_lists) + 1), tickers_lists):
                print(f'{Fore.YELLOW}iteration: {i}/{len(tickers_lists)}{Style.RESET_ALL}')
                ticker_entries = fetch_ticker_entries(['ticker', 'date', 'sma_50', 'sma_200', 'close', 'bband_h', 'bband_l', 'rsi'], ticker_list)
                ticker_entries = list(ticker_entries.items())

                signals = fetch_ta_signals(ticker_entries)
                print(len(signals), 'signals to create')
                DailyTASignal.objects.bulk_create(signals, batch_size=1000)

            self.stdout.write(self.style.SUCCESS('Successfully updated technical analysis'))
        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to update technical analysis data')
