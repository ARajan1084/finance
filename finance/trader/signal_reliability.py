import datetime
import math
from colorama import Fore, Style
from tdqm_l import tqdm

import pandas as pd
from queue import PriorityQueue, Queue

from trader.trader_commands_functions import fetch_ticker_entries_by_date
from trader.models import BackTest, DailyStockMarketData, BackTestTransaction, DailyTASignal


class BuySignalReliability:
    def __init__(self, start: datetime.date, end: datetime.date, ticker: str, interval_length: int,
                 expected_return: float, loss_tolerance: float, hold_period: int, coefs: dict, buy_threshold: int):
        self.start = start
        self.end = end
        self.ticker = ticker

        self.expected_return = 1 + expected_return
        self.loss_tolerance = 1 - loss_tolerance
        self.hold_period = hold_period

        self.signal_list = ['bband_l_cross', 'bband_h_cross', 'rsi_lte_30', 'rsi_gte_70', 'golden_cross', 'death_cross']
        self.__process_coefficients(coefs)
        self.buy_threshold = buy_threshold

        self.reliability_score = 0
        self.__generate_ticker_entries()
        self.__init_buy_signals()

    def determine_reliability(self):
        for date in (self.start + datetime.timedelta(n) for n in range((self.end - self.start).days)):
            self.process_buy_signals(date)

    def process_buy_signals(self, date):
        signals = self.buy_signals[date]
        if signals is None:  # no buy signals to look at for the day
            return
        coef_sum = self.__process_signals(signals)
        if coef_sum >= self.buy_threshold:
            start = self.ticker_entries[date]
            for i in (date + datetime.timedelta(n) for n in range((date + datetime.timedelta(self.hold_period) - date).days)):
                if i in self.ticker_entries:
                    entry = self.ticker_entries[i]
                    if entry.close >= self.expected_return * start.close:
                        self.reliability_score += 1
                        break
                    elif entry.close <= self.loss_tolerance * start.close:
                        self.reliability_score -= 1
                        break

    def __init_buy_signals(self):
        query_buy_ta_signals = DailyTASignal.objects.filter(signal='buy', ticker=self.ticker, date__gte=self.start,
                                                            date__lte=self.end).order_by('date')
        keys = (self.start + datetime.timedelta(n) for n in range((self.end - self.start).days))
        self.buy_signals = dict.fromkeys(keys)
        for signal in query_buy_ta_signals:
            if self.buy_signals[signal.date] is not None:
                self.buy_signals[signal.date].append(signal)
            else:
                self.buy_signals[signal.date] = [signal]

    def __process_signals(self, signals):
        signal_sum = 0
        for signal in signals:
            signal_sum += self.coefs[signal.description]
        return signal_sum

    def __process_coefficients(self, coefs: dict):
        self.coefs = {}
        for signal in self.signal_list:
            self.coefs.update({signal: coefs.get(signal, 0.0)})

    def __generate_ticker_entries(self):
        query = DailyStockMarketData.objects.filter(ticker=self.ticker, date__gte=self.start, date__lte=self.end).only('date', 'ticker', 'close')
        keys = [entry.date for entry in query]
        self.ticker_entries = dict.fromkeys(keys)
        for entry in query:
            self.ticker_entries[entry.date] = entry

    def clear_entries(self):
        del self.ticker_entries
