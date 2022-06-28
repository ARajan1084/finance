import datetime
import math
from colorama import Fore, Style
from tdqm_l import tqdm

import pandas as pd
from queue import PriorityQueue, Queue

from trader.trader_commands_functions import fetch_ticker_entries_by_date
from trader.models import BackTest, DailyStockMarketData, BackTestTransaction, DailyTASignal


class BuySignalReliability:
    def __init__(self, start: datetime.date, end: datetime.date, init_investment: int, interval_length: int,
                 expected_return: float, hold_period: int, coefs: dict):
        self.start = start
        self.end = end

        self.expected_return = 1 + expected_return
        self.hold_period = hold_period

        self.signal_list = ['bband_l_cross', 'bband_h_cross', 'rsi_lte_30', 'rsi_gte_70', 'golden_cross', 'death_cross']
        self.__process_coefficients(coefs)

        self.date_intervals = self.__generate_date_intervals(interval_length)

    def determine_reliability(self):
        pass

    def process_buy_signals(self, date):
        if self.bank > 0:  # if we have money
            query_buy_ta_signals = DailyTASignal.objects.filter(date=date, signal='buy')
            signal_processing = self.__process_signal_query(query_buy_ta_signals)
            for ticker, coef_sum in signal_processing.items():
                if coef_sum >= self.buy_threshold:
                    entry = self.fetch_entry(date, ticker)
                    if self.price_cap >= entry.close >= self.price_min:
                        self.buy_transaction_queue.put(ticker, entry.volume)  # buy this the next day when the market opens

    def __process_coefficients(self, coefs: dict):
        self.coefs = {}
        for signal in self.signal_list:
            self.coefs.update({signal: coefs.get(signal, 0.0)})

    def __generate_date_intervals(self, interval_length):
        date_intervals = []
        day_diff = (self.end - self.start).days
        for date in (self.start + datetime.timedelta(n) for n in range(0, day_diff, interval_length)):
            date_intervals.append(date)
        return date_intervals
