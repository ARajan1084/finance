import datetime
import math
from colorama import Fore, Style

import pandas as pd
from queue import PriorityQueue, Queue

from trader.trader_commands_functions import fetch_ticker_entries_by_date
from trader.models import BackTest, DailyStockMarketData, BackTestTransaction, DailyTASignal


class Simulation:
    def __init__(self, start: datetime.date, end: datetime.date, test_name: str, init_investment: int,
                 interval_length: int, price_cap: int, buys_per_day: int, imm_sc_profit: float, imm_sc_loss: float):
        self.start = start
        self.end = end
        self.net_worth_tracker = {}
        self.test = BackTest(name=test_name, start=start, end=end)
        self.price_cap = price_cap
        self.buys_per_day = buys_per_day

        self.imm_sc_profit_f = 1 + imm_sc_profit
        self.imm_sc_loss_f = 1 - imm_sc_loss

        self.buy_transaction_queue = PriorityQueue()
        self.sell_transaction_queue = Queue()
        self.portfolio = {}
        self.bank = init_investment
        self.init_invest = init_investment

        self.date_intervals = self.__generate_date_intervals(interval_length)

        self.ticker_entries = {}

    def run_simulation(self):
        self.test.save()
        print('started with', self.bank, 'dollars')

        for date in (self.start + datetime.timedelta(n) for n in range((self.end - self.start).days)):
            if date in self.date_intervals:
                self.__repopulate_ticker_entries(date)

            query_stock_data = DailyStockMarketData.objects.filter(date=date).only('date')
            if len(query_stock_data) == 0:  # market is closed
                continue

            # determine sells for today
            self.immediate_sell_conditions(date)

            # process buy and sell queues
            self.process_sell_queue(date)
            self.process_buy_queue(date)

            # determine buys for tomorrow based on TA today
            self.get_buy_signals(date)
            # determine sells for tomorrow based on TA today
            self.get_sell_signals(date)
            net_w = self.calculate_net_worth(date)
            self.net_worth_tracker.update({date: net_w})

            if net_w > self.init_invest:
                print(f'{Fore.GREEN}{date}: ${net_w}{Style.RESET_ALL}')
            else:
                print(f'{Fore.RED}{date}: ${net_w}{Style.RESET_ALL}')

        query = DailyStockMarketData.objects.filter(date__gte=self.end).order_by('date')
        sell_all_date = query[0].date
        for ticker in self.portfolio.keys():
            self.sell_transaction_queue.put(ticker)
        self.process_sell_queue(sell_all_date)
        self.net_worth_tracker.update({self.end: self.bank})

        df = pd.DataFrame(self.net_worth_tracker, index=self.net_worth_tracker.keys())
        df.to_csv('simulation_net_worth_data.csv')

        print('ended with', self.bank, 'dollars')

    def immediate_sell_conditions(self, date):
        # sell if +/- 10% of initial buy
        for ticker in self.portfolio:
            query_trans = BackTestTransaction.objects.filter(ticker=ticker, back_test_id=self.test.id) \
                .order_by('-date') \
                .only('ticker', 'date', 'price_per_share')
            entry = self.fetch_entry(date, ticker)
            if entry:
                price = entry.open
                if price >= query_trans[0].price_per_share * self.imm_sc_profit_f \
                        or price <= query_trans[0].price_per_share * self.imm_sc_loss_f:
                        # or date - query_trans[0].date >= timedelta(7):
                    self.sell_transaction_queue.put(ticker)

    def get_buy_signals(self, date):
        if self.bank > 0:  # if we have money
            query_buy_ta_signals = DailyTASignal.objects.filter(date=date, signal='buy', description='bband_l_cross')
            for signal in query_buy_ta_signals:
                entry = self.fetch_entry(date, signal.ticker)
                if entry.close <= self.price_cap:
                    self.buy_transaction_queue.put(signal.ticker, entry.volume)  # buy this the next day when the market opens

    def get_sell_signals(self, date):
        query_sell_ta_signals = DailyTASignal.objects.filter(date=date, signal='sell', description__in=['bband_h_cross', 'death_cross'])
        for signal in query_sell_ta_signals:
            if signal.ticker in self.portfolio:
                self.sell_transaction_queue.put(signal.ticker)  # sell this the next day when the market opens

    def process_buy_queue(self, date):
        i = 0
        while not self.buy_transaction_queue.empty() and i < self.buys_per_day:
            ticker = self.buy_transaction_queue.get()
            entry = self.fetch_entry(date, ticker)
            if not entry:
                continue
            shares = int(self.sigmoid(entry.volume) * 5)
            trans = BackTestTransaction(
                back_test_id=self.test.id,
                action='buy',
                date=date,
                ticker=ticker,
                shares=shares,
                price_per_share=entry.open
            )
            if trans.price_per_share == 0:
                continue
            if self.bank - trans.price_per_share > 0:  # if we have money
                shares = min(int(self.bank / trans.price_per_share), shares)
                trans.save()
                self.bank -= shares * trans.price_per_share
                if ticker in self.portfolio:
                    self.portfolio[ticker] += shares
                else:
                    self.portfolio.update({ticker: shares})
                i += 1

        with self.buy_transaction_queue.mutex:
            self.buy_transaction_queue.queue.clear()

    def process_sell_queue(self, date):
        while not self.sell_transaction_queue.empty():
            ticker = self.sell_transaction_queue.get()
            if ticker not in self.portfolio:
                continue
            entry = self.fetch_entry(date, ticker)
            if not entry:
                print(f'{ticker} not found for {date}')
                continue
            trans = BackTestTransaction(
                back_test_id=self.test.id,
                action='sell',
                date=date,
                ticker=ticker,
                shares=self.portfolio[ticker],
                price_per_share=entry.open
            )
            trans.save()
            self.bank += self.portfolio[ticker] * trans.price_per_share
            self.portfolio.pop(ticker)

    def fetch_entry(self, date, ticker):
        for entry in self.ticker_entries[ticker]:
            if entry.date == date:
                return entry

    def calculate_net_worth(self, date):
        net_worth = self.bank
        for ticker in self.portfolio:
            entry = self.fetch_entry(date, ticker)
            if entry:
                net_worth += self.portfolio[ticker] * entry.close
        return net_worth

    def sigmoid(self, x):
        return 1 / (1 + math.exp(-x))


    def __generate_date_intervals(self, interval_length):
        date_intervals = []
        day_diff = (self.end - self.start).days
        for date in (self.start + datetime.timedelta(n) for n in range(0, day_diff, interval_length)):
            date_intervals.append(date)
        return date_intervals

    def __repopulate_ticker_entries(self, date):
        start_i = self.date_intervals.index(date)
        start = date
        if start_i == len(self.date_intervals) - 1:
            end = self.end
        else:
            end = self.date_intervals[start_i + 1]
        self.ticker_entries = fetch_ticker_entries_by_date(['date', 'ticker', 'open', 'close'], start, end)
