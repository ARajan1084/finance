from django.db import models


class DailyTechnicalAnalysis(models.Model):
    ticker = models.CharField(unique=False, max_length=6, primary_key=False)
    date = models.DateField(unique=False)
    category = models.CharField(unique=False, null=False, max_length=15)

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

    class Meta:
        db_table = 'daily_stock_market_data'


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
