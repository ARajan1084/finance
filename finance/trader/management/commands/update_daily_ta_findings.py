import multiprocessing
import traceback
from trader.models import DailyTASignal
from django.core.management.base import BaseCommand, CommandError
from .trader_commands_functions import fetch_ticker_entries_3d, find_golden_and_death_crosses


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            multiprocessing.set_start_method('fork')
            ticker_entries = fetch_ticker_entries_3d()
            ticker_entries = list(ticker_entries.items())

            crosses = [cross for cross in find_golden_and_death_crosses(ticker_entries)]
            print(len(crosses), ' crosses to create')
            DailyTASignal.objects.bulk_create(crosses, batch_size=1000)

            self.stdout.write(self.style.SUCCESS('Successfully updated technical analysis'))
        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to update technical analysis data')
