# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-09 08:23
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('weibo_checkin', '0006_auto_20170309_0815'),
    ]

    operations = [
        migrations.RenameField(
            model_name='poitask',
            old_name='area_id',
            new_name='area',
        ),
        migrations.RenameField(
            model_name='poitaskofworker',
            old_name='task_id',
            new_name='task',
        ),
    ]
