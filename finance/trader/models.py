import uuid

from django.db import models


class BackTest(models.Model):
    id = models.UUIDField(unique=True, primary_key=True, default=uuid.uuid4)
    name = models.CharField(unique=False, max_length=50, null=False)
    start = models.DateField(unique=False)
    end = models.DateField(unique=False)
    description = models.CharField(unique=False, max_length=300, null=True)

    class Meta:
        db_table = 'back_tests'


class BackTestTransaction(models.Model):
    id = models.UUIDField(unique=True, primary_key=True, default=uuid.uuid4)
    back_test_id = models.UUIDField(unique=False, null=False)
    action = models.CharField(unique=False, max_length=4, null=False)
    date = models.DateField(null=False)
    ticker = models.CharField(unique=False, max_length=6, null=False)
    shares = models.IntegerField(null=False)
    price_per_share = models.FloatField(null=False)

    class Meta:
        db_table = 'back_test_transactions'


class Transaction(models.Model):
    id = models.UUIDField(unique=True, primary_key=True, default=uuid.uuid4)
    action = models.CharField(unique=False, max_length=4, null=False)
    date = models.DateField(null=False)
    ticker = models.CharField(unique=False, max_length=6, null=False)
    shares = models.IntegerField(null=False)
    price_per_share = models.FloatField(null=False)

    class Meta:
        db_table = 'transactions'


class DailyTASignal(models.Model):
    ticker = models.CharField(unique=False, max_length=6, primary_key=False)
    date = models.DateField(unique=False)
    description = models.CharField(unique=False, null=False, max_length=15)
    signal = models.CharField(unique=False, null=False, max_length=5)

    class Meta:
        db_table = 'daily_technical_analysis'


class DailyStockMarketData(models.Model):
    ticker = models.CharField(unique=False, max_length=6, primary_key=False)
    date = models.DateField(unique=False)
    open = models.FloatField(null=True)
    high = models.FloatField(null=True)
    low = models.FloatField(null=True)
    close = models.FloatField(null=True)
    adj_close = models.FloatField(null=True)
    volume = models.FloatField(null=True)
    sma_50 = models.FloatField(null=True)
    sma_200 = models.FloatField(null=True)
    bband_h = models.FloatField(null=True)
    bband_l = models.FloatField(null=True)
    rsi = models.FloatField(null=True)

    class Meta:
        db_table = 'daily_stock_market_data'
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['ticker'])
        ]


class StockMarketData(models.Model):
    ticker = models.CharField(unique=False, max_length=6, primary_key=False)
    date_time = models.DateTimeField(unique=False)
    open = models.FloatField(null=True)
    high = models.FloatField(null=True)
    low = models.FloatField(null=True)
    close = models.FloatField(null=True)
    adj_close = models.FloatField(null=True)
    volume = models.FloatField(null=True)

    class Meta:
        db_table = 'stock_market_data'


class TickerInfo(models.Model):
    ticker = models.CharField(unique=True, max_length=6, primary_key=True)
    company = models.CharField(unique=False, max_length=100)
    industry = models.CharField(unique=False, max_length=100)

    class Meta:
        db_table = 'ticker_info'
