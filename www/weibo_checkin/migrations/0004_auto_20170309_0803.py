# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-09 08:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('weibo_checkin', '0003_poitask_poitaskofworker'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='poitaskofworker',
            name='created_at',
        ),
        migrations.AlterField(
            model_name='poitaskofworker',
            name='start_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
