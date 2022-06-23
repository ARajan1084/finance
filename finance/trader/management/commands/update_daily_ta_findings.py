import multiprocessing
import traceback
from trader.models import DailyTASignal
from django.core.management.base import BaseCommand, CommandError
from trader.trader_commands_functions import fetch_ticker_entries_3d, find_crosses


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            multiprocessing.set_start_method('fork')
            ticker_entries = fetch_ticker_entries_3d(['date', 'sma_50', 'sma_200'])
            ticker_entries = list(ticker_entries.items())

            crosses = [cross for cross in find_crosses(ticker_entries)]
            print(len(crosses), ' crosses to create')
            DailyTASignal.objects.bulk_create(crosses, batch_size=1000)

            self.stdout.write(self.style.SUCCESS('Successfully updated technical analysis'))
        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to update technical analysis data')
