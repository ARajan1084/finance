# Generated by Django 4.0.4 on 2022-05-31 02:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0007_dailystockmarketdata_rsi'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='DailyTechnicalAnalysis',
            new_name='DailyTASignal',
        ),
    ]
