from django.shortcuts import render
from .models import DailyStockMarketData, TickerInfo
from datetime import datetime, date, timedelta
from django.http import JsonResponse
from django.core import serializers


def home(request):
    return render(request, 'trader/home.html')


def stock_info(request, ticker):
    queryset = DailyStockMarketData.objects.all().filter(ticker=ticker, date__gte=datetime.now().date() - timedelta(200))
    ticker_info = TickerInfo.objects.get(ticker=ticker)
    return render(request, 'trader/stock_info.html', context={'ticker_info': ticker_info,
                                                              'query': list(queryset)})


def stock_info_by_day(request, ticker, num_days):
    queryset = DailyStockMarketData.objects.all().filter(ticker=ticker,
                                                         date__gte=datetime.now().date() - timedelta(num_days))
    return JsonResponse(serializers.serialize('json', queryset), safe=False)
