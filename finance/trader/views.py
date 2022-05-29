from django.shortcuts import render, redirect
from django.db.models import F
from .models import DailyStockMarketData, TickerInfo, DailyTechnicalAnalysis
from datetime import datetime, date, timedelta
from django.http import JsonResponse
from django.core import serializers
from django.contrib import messages
from home.forms import SearchTickerForm
import json
import pandas as pd
from ta import volatility, trend


# def get_tickers():
#     tickers = []
#     for entry in TickerInfo.objects.all():
#         tickers.append(entry.ticker)
#     return tickers
#
#
# TICKERS = get_tickers()
TICKERS = []


def home(request):
    if request.method == 'POST':
        search_ticker_form = SearchTickerForm(request.POST)
        if search_ticker_form.is_valid():
            ticker = search_ticker_form.cleaned_data['ticker']
            if len(TickerInfo.objects.filter(ticker=ticker)) < 1:
                messages.error(request, "Ticker does not exist.")
                return redirect('trader_home')
            return redirect('stock_info', ticker=ticker, num_days=365)
        else:
            messages.error(request, "Ticker is invalid.")

    golden_crosses = [TickerInfo.objects.get(ticker=entry.ticker)
                      for entry in list(DailyTechnicalAnalysis.objects.all().filter(date__gte=datetime.now() - timedelta(3),
                                                                                                 category='golden_cross').only('ticker'))]
    death_crosses = [TickerInfo.objects.get(ticker=entry.ticker)
                     for entry in list(DailyTechnicalAnalysis.objects.all().filter(date__gte=datetime.now() - timedelta(3),
                                                                                                category='death_cross').only('ticker'))]

    search_ticker_form = SearchTickerForm()
    return render(request, 'trader/home.html', context={'active': 'trader',
                                                        'golden_crosses': golden_crosses,
                                                        'death_crosses': death_crosses,
                                                        'search_ticker_form': search_ticker_form})


def stock_info(request, ticker, num_days):
    queryset = DailyStockMarketData.objects.all().filter(ticker=ticker, date__gte=datetime.now().date() - timedelta(num_days)).order_by('date')
    ticker_info = TickerInfo.objects.get(ticker=ticker)
    search_ticker_form = SearchTickerForm()

    time_x = []
    close = []
    open = []
    high = []
    low = []
    sma_50 = []
    sma_200 = []
    bollinger_hband = []
    bollinger_lband = []
    for entry in queryset:
        time_x.append(str(entry.date.strftime("%m/%d/%Y")))
        close.append(entry.close)
        open.append(entry.open)
        sma_50.append(entry.sma_50)
        sma_200.append(entry.sma_200)
        bollinger_hband.append(entry.bband_h)
        bollinger_lband.append(entry.bband_l)

    return render(request, 'trader/stock_info.html', context={'active': 'trader',
                                                              'num_days': num_days,
                                                              'ticker_info': ticker_info,
                                                              'time_x': json.dumps(time_x),
                                                              'close': json.dumps(close),
                                                              'bollinger_hband': json.dumps(bollinger_hband),
                                                              'bollinger_lband': json.dumps(bollinger_lband),
                                                              'sma_50': json.dumps(sma_50),
                                                              'sma_200': json.dumps(sma_200),
                                                              'search_ticker_form': search_ticker_form})


def stock_info_by_day(request, ticker, num_days):
    queryset = DailyStockMarketData.objects.all().filter(ticker=ticker,
                                                         date__gte=datetime.now().date() - timedelta(num_days))
    return JsonResponse(serializers.serialize('json', queryset), safe=False)
