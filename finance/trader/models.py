from django.db import models


class DailyStockMarketData(models.Model):
    ticker = models.CharField(unique=False, max_length=5, primary_key=False)
    date = models.DateField(unique=False)
    open = models.FloatField()
    close = models.FloatField()
    adj_close = models.FloatField()
    volume = models.FloatField()

    class Meta:
        db_table = 'daily_stock_market_data'
        order_with_respect_to = 'date'


class StockMarketData(models.Model):
    ticker = models.CharField(unique=False, max_length=5, primary_key=False)
    date_time = models.DateTimeField(unique=False)
    open = models.FloatField()
    close = models.FloatField()
    adj_close = models.FloatField()
    volume = models.FloatField()

    class Meta:
        db_table = 'stock_market_data'
        order_with_respect_to = 'date_time'


class TickerInfo(models.Model):
    ticker = models.CharField(unique=True, max_length=5, primary_key=True)
    security = models.CharField(unique=False, max_length=50)
    sector = models.CharField(unique=False, max_length=30)

    class Meta:
        db_table = 'ticker_info'
        order_with_respect_to = 'ticker'
