# Generated by Django 4.2.3 on 2023-07-09 09:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stocks', '0013_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='file_name',
            field=models.CharField(default=11, max_length=50),
            preserve_default=False,
        ),
    ]
