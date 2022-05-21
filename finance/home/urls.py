from django.contrib import admin
from django.urls import path, include
from trader import urls as trader_urls
from . import views

urlpatterns = [
    path('', views.home, name='home')
]