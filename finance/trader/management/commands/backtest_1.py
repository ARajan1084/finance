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
            start = datetime(2018, 1, 1).date()
            end = datetime(2022, 2, 1).date()

            simulations = []
            signal_min = 0.0
            signal_max = 2.0
            signal_inc = 1.0

            for imm_sc_profit in np.arange(0.1, 0.11, 0.1):  # possible profits
                for imm_sc_loss in np.arange(0.2, 0.21, 0.1):  # possible losses
                    for bband_l_cross in np.arange(signal_min, signal_max, signal_inc):
                        for bband_h_cross in np.arange(signal_min, signal_max, signal_inc):
                            for golden_cross in np.arange(signal_min, signal_max, signal_inc):
                                for death_cross in np.arange(signal_min, signal_max, signal_inc):
                                    for rsi_gte_70 in np.arange(signal_min, signal_max, signal_inc):
                                        for rsi_lte_30 in np.arange(signal_min, signal_max, signal_inc):
                                            for buy_threshold in np.arange(1.0, 3.0, 1.0):
                                                for sell_threshold in np.arange(0.0, 3.0, 1.0):
                                                    if bband_l_cross + golden_cross + rsi_gte_70 < buy_threshold or \
                                                            bband_h_cross + death_cross + rsi_lte_30 < sell_threshold:
                                                        continue
                                                    name = 'iscp_' + f"{imm_sc_profit:.9}" + '_' + \
                                                           'iscl_' + f"{imm_sc_loss:.9}" + '_' + \
                                                           'bblc_' + str(bband_l_cross) + '_' + \
                                                           'bbhc_' + str(bband_h_cross) + '_' + \
                                                           'gc_' + str(golden_cross) + '_' + \
                                                           'dc_' + str(death_cross) + '_' + \
                                                           'rsi70_' + str(rsi_gte_70) + '_' + \
                                                           'rsi30_' + str(rsi_lte_30) + '_' + \
                                                           'bt_' + str(buy_threshold) + '_' + \
                                                           'st_' + str(sell_threshold)
                                                    simulations.append(Simulation(start=start,
                                                                                  end=end,
                                                                                  test_name=name,
                                                                                  init_investment=50000,
                                                                                  interval_length=300,
                                                                                  price_min=10.0,
                                                                                  price_cap=1000.0,
                                                                                  buys_per_day=10,
                                                                                  imm_sc_loss=imm_sc_loss,
                                                                                  imm_sc_profit=imm_sc_profit,
                                                                                  coefs={
                                                                                      'bband_l_cross': bband_l_cross,
                                                                                      'bband_h_cross': bband_h_cross,
                                                                                      'golden_cross': golden_cross,
                                                                                      'death_cross': 1.0,
                                                                                      'rsi_lte_30': rsi_lte_30,
                                                                                      'rsi_gte_70': rsi_gte_70,
                                                                                  },
                                                                                  buy_threshold=buy_threshold,
                                                                                  sell_threshold=sell_threshold))
            # multiprocessing.set_start_method('fork')
            # with Pool(multiprocessing.cpu_count()) as pool:
            #     pool.map(run_sim, simulations)
            #     # tqdm(pool.imap(run_sim, simulations), total=len(simulations))

            simulations_lists = np.array_split(simulations, 16)
            threads = []
            for simulation_list in simulations_lists:
                thread = Thread(target=run_sim, args=[simulation_list])
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            max = -1000000
            max_name = ''
            for simulation in simulations:
                total = BackTestTransaction.objects.filter(back_test_id=simulation.test.id).aggregate(Sum('total'))['total__sum']
                if total > max:
                    max = total
                    max_name = simulation.test.name
            print(max_name, 'was the best simulation with a net total of', max)

        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to run simulations')

