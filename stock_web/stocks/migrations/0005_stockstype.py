# Generated by Django 4.2.3 on 2023-07-06 08:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0004_accstocks_rmse'),
    ]

    operations = [
        migrations.CreateModel(
            name='StocksType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stock_id', models.CharField(max_length=50)),
                ('stock_type', models.CharField(max_length=50)),
            ],
        ),
    ]