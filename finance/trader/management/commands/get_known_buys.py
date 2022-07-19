import pandas as pd
import psycopg2
import sys
from tdqm_l import tqdm
from multiprocessing import Pool
import multiprocessing as mp

import traceback
from trader.models import TickerInfo, DailyStockMarketData, KnownBuy
from django.core.management.base import BaseCommand, CommandError
from multiprocessing.pool import Pool
import numpy as np
from trader.trader_commands_functions import generate_ta_metric
from django.db import connection


def connect(params_dic):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params_dic)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(1)
    print("Connection successful")
    return conn


param_dic = {
                "host": "localhost",
                "database": "finance_db",
                "user": "finance",
                "password": "finance@venv"
            }
db_con = connect(param_dic)
df = pd.read_sql("select * from \"daily_stock_market_data\" ORDER BY date, ticker", db_con)


def get_known_buys(ticker):
    known_buys = []
    profit = 0.1
    hold = 7

    ticker_df = df[df['ticker'] == ticker]
    for i in range(len(ticker_df)):
        start = ticker_df.iloc[i]
        for j in range(i, min(i + hold, len(ticker_df))):
            curr = ticker_df.iloc[j]
            if curr['close'] >= start['close'] * (1 + profit):
                known_buys.append(KnownBuy(date=curr['date'], ticker=curr['ticker']))
                break
    KnownBuy.objects.bulk_create(known_buys, batch_size=1000)
    del known_buys
    del ticker_df
    return


class Command(BaseCommand):
    def add_arguments(self, parser):
        pass

    def handle(self, *args, **kwargs):
        try:
            tickers = df['ticker'].unique().tolist()
            mp.set_start_method('fork')
            tickers_list = np.array_split(tickers, 50)
            for ticker_list in tickers_list:
                with Pool(int(mp.cpu_count() / 2)) as pool:
                    result = [entry for entry in tqdm(pool.imap(get_known_buys, ticker_list), total=len(ticker_list))]

        except Exception:
            traceback.print_exc()
            raise CommandError('Unable to get known buys')