# Generated by Django 4.0.4 on 2022-05-25 09:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0008_dailystockmarketdata_sma_200_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailystockmarketdata',
            name='bband_h',
            field=models.FloatField(null=True),
        ),
        migrations.AddField(
            model_name='dailystockmarketdata',
            name='bband_l',
            field=models.FloatField(null=True),
        ),
    ]
