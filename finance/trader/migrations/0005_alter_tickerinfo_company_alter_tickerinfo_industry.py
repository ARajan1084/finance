# Generated by Django 4.0.4 on 2022-05-28 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trader', '0004_alter_tickerinfo_ticker'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tickerinfo',
            name='company',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='tickerinfo',
            name='industry',
            field=models.CharField(max_length=100),
        ),
    ]
