from django.contrib import admin
from django.urls import path, include
from trader import urls as trader_urls
import trader.views as views

urlpatterns = [
    path('', views.home, name='home')
]