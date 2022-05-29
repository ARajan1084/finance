from django.contrib import admin
from django.urls import path, include
import trader.views as views

urlpatterns = [
    path('', views.home, name='trader_home'),
    path('stockinfo/<str:ticker>/<int:num_days>/', views.stock_info, name='stock_info'),
    path('json/stockinfo/<str:ticker>/<int:num_days>/', views.stock_info_by_day, name='json_stock_info_day')
]
