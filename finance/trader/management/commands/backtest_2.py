import traceback
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError

from trader.models import BackTest, BackTestTransaction
from trader.simulations import Simulation
import numpy as np
from multiprocessing import Pool
import multiprocessing
from tdqm_l import tqdm
from django.db.models import Sum
from threading import Thread


def run_sim(sim_list):
    for sim in sim_list:
        sim.run_simulation()
        sim.clear_entries()
    return True


class Command(BaseCommand):

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            simulation = Simulation(
                imm_sc_profit=0.1,
                imm_sc_loss=0.2,
                start=datetime(2018, 1, 1).date(),
                end=datetime(2022, 6, 23).date(),
                init_investment=50000,
                test_name='yee_boi_2',
                interval_length=1826,
                price_min=10.0,
                price_cap=10,
                buys_per_day=10,
                coefs={
                    'bband_h_cross': 1.0,
                    'death_cross': 1.0,
                    'rsi_gte_70': 1.0,
                    'rsi_lte_30': 1.0,
                },
                buy_threshold=1.0,
                sell_threshold=2.0
            )
            simulation.run_simulation()
            total = BackTestTransaction.objects.filter(back_test_id=simulation.test.id).aggregate(Sum('total'))['total__sum']
            print(total, 'dollars made')

        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to run simulations')

