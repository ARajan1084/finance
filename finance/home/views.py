from django.shortcuts import render

from home.forms import SearchTickerForm


def home(request):
    search_ticker_form = SearchTickerForm()
    return render(request, 'home/home.html', context={'active': 'home',
                                                      'search_ticker_form': search_ticker_form})
