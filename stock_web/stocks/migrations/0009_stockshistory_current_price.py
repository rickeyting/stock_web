# Generated by Django 4.2.3 on 2023-07-07 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0008_stockshistory_strategymode'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockshistory',
            name='current_price',
            field=models.DateField(blank=True, null=True),
        ),
    ]
