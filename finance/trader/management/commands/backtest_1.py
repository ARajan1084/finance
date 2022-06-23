import traceback
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from trader.simulations import Simulation


class Command(BaseCommand):

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:

            start = datetime(2018, 1, 1).date()
            end = datetime(2022, 5, 17).date()
            sim = Simulation(start=start,
                             end=end,
                             test_name='test_2',
                             init_investment=50000,
                             interval_length=1826,
                             price_cap=3000,
                             buys_per_day=10)
            sim.run_simulation()

        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to populate daily stock market data table')
