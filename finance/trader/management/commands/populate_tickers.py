import traceback

import pandas as pd
from trader.models import TickerInfo
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        try:
            df = pd.read_csv('trader/management/commands/ticker_info.csv')
            for index, row in df.iterrows():
                ticker = TickerInfo(ticker=row['Symbol'], company=row['Company Name'], industry=row['Industry'])
                ticker.save()
            self.stdout.write(self.style.SUCCESS('Successfully populated ticker info table'))
        except Exception as e:
            traceback.print_exc()
            raise CommandError('Unable to populate ticker info table')

