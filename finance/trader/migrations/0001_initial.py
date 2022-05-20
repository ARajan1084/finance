# Generated by Django 4.0.4 on 2022-05-20 03:32

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TickerInfo',
            fields=[
                ('ticker', models.CharField(max_length=5, primary_key=True, serialize=False, unique=True)),
                ('security', models.CharField(max_length=50)),
                ('sector', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='StockMarketData',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticker', models.CharField(max_length=5)),
                ('date_time', models.DateTimeField()),
                ('open', models.FloatField()),
                ('close', models.FloatField()),
                ('adj_close', models.FloatField()),
                ('volume', models.FloatField()),
            ],
            options={
                'db_table': 'stock_market_data',
                'order_with_respect_to': 'date_time',
            },
        ),
    ]