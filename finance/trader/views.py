from django.shortcuts import render, redirect
from .models import DailyStockMarketData, TickerInfo
from datetime import datetime, date, timedelta
from django.http import JsonResponse
from django.core import serializers
from django.contrib import messages
from home.forms import SearchTickerForm
import json
import pandas as pd
from ta import volatility


def home(request):
    if request.method == 'POST':
        search_ticker_form = SearchTickerForm(request.POST)
        if search_ticker_form.is_valid():
            ticker = search_ticker_form.cleaned_data['ticker']
            if len(TickerInfo.objects.filter(ticker=ticker)) < 1:
                messages.error(request, "Ticker does not exist.")
                return redirect('trader_home')
            return redirect('stock_info', ticker=ticker)
        else:
            messages.error(request, "Ticker is invalid.")
    search_ticker_form = SearchTickerForm()
    return render(request, 'trader/home.html', context={'active': 'trader',
                                                        'search_ticker_form': search_ticker_form})


def stock_info(request, ticker):
    queryset = DailyStockMarketData.objects.all().filter(ticker=ticker, date__gte=datetime.now().date() - timedelta(200))
    ticker_info = TickerInfo.objects.get(ticker=ticker)
    search_ticker_form = SearchTickerForm()

    time_x = []
    stock_price_y = []
    for entry in queryset:
        time_x.append(str(entry.date.strftime("%m/%d/%Y")))
        stock_price_y.append(entry.close)

    df = pd.DataFrame(list(queryset.values()))
    print(df)
    ta_bbands = volatility.BollingerBands(close=df["adj_close"],
                                          window=20,
                                          window_dev=2)
    return render(request, 'trader/stock_info.html', context={'active': 'trader',
                                                              'ticker_info': ticker_info,
                                                              'time_x': json.dumps(time_x),
                                                              'stock_price_y': json.dumps(stock_price_y),
                                                              'bollinger_hband': json.dumps(ta_bbands.bollinger_hband().tolist()),
                                                              'bollinger_lband': json.dumps(ta_bbands.bollinger_lband().tolist()),
                                                              'search_ticker_form': search_ticker_form})


def stock_info_by_day(request, ticker, num_days):
    queryset = DailyStockMarketData.objects.all().filter(ticker=ticker,
                                                         date__gte=datetime.now().date() - timedelta(num_days))
    return JsonResponse(serializers.serialize('json', queryset), safe=False)
