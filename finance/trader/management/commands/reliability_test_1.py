import traceback
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError

from trader.models import BackTest, BackTestTransaction
from trader.signal_reliability import BuySignalReliability
import numpy as np
import multiprocessing
from tdqm_l import tqdm
from django.db.models import Sum
from threading import Thread


def run_sim(sim_list):
    for sim in sim_list:
        sim.determine_reliability()
        sim.clear_entries()
    return True


class Command(BaseCommand):

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            start = datetime(2018, 1, 1).date()
            end = datetime(2022, 2, 1).date()

            simulations = []
            signal_min = 0.0
            signal_max = 1.1
            signal_inc = 0.2

            for exp_return in np.arange(0.1, 0.11, 0.1):  # possible profits
                for loss_tol in np.arange(0.2, 0.21, 0.1):  # possible losses
                    for bband_l_cross in np.arange(signal_min, signal_max, signal_inc):
                        for golden_cross in np.arange(signal_min, signal_max, signal_inc):
                            for rsi_lte_30 in np.arange(signal_min, signal_max, signal_inc):
                                for buy_threshold in np.arange(1.0, 3.0, 0.2):
                                    if bband_l_cross + golden_cross + rsi_lte_30 < buy_threshold:
                                        continue
                                    simulations.append(BuySignalReliability(start=start,
                                                                            end=end,
                                                                            hold_period=30,
                                                                            ticker='AAPL',
                                                                            interval_length=300,
                                                                            expected_return=loss_tol,
                                                                            loss_tolerance=exp_return,
                                                                            coefs={
                                                                                'bband_l_cross': bband_l_cross,
                                                                                'golden_cross': golden_cross,
                                                                                'rsi_lte_30': rsi_lte_30,
                                                                            },
                                                                            buy_threshold=buy_threshold))

            simulations_lists = np.array_split(simulations, multiprocessing.cpu_count())
            threads = []
            for simulation_list in simulations_lists:
                thread = Thread(target=run_sim, args=[simulation_list])
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            for simulation in sorted(simulations, key=lambda sim: sim.reliability_score, reverse=True):
                print(simulation.coefs)
                print('buy_threshold:', simulation.buy_threshold)
                print('score:', simulation.reliability_score)

        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to run simulations')

