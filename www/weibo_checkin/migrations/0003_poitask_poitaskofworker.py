# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-07 15:33
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('weibo_checkin', '0002_auto_20170304_0354'),
    ]

    operations = [
        migrations.CreateModel(
            name='POITask',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(default=0)),
                ('progress', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('poi_count', models.IntegerField(default=0)),
                ('area_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weibo_checkin.Area')),
            ],
        ),
        migrations.CreateModel(
            name='POITaskOfWorker',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('worker', models.IntegerField(default=0)),
                ('is_working', models.IntegerField(default=0)),
                ('is_done', models.IntegerField(default=0)),
                ('is_error', models.IntegerField(default=0)),
                ('error_message', models.CharField(max_length=100)),
                ('min_lat', models.DecimalField(decimal_places=6, max_digits=9)),
                ('max_lat', models.DecimalField(decimal_places=6, max_digits=9)),
                ('min_lon', models.DecimalField(decimal_places=6, max_digits=9)),
                ('max_lon', models.DecimalField(decimal_places=6, max_digits=9)),
                ('cur_lat', models.DecimalField(decimal_places=6, max_digits=9)),
                ('cur_lon', models.DecimalField(decimal_places=6, max_digits=9)),
                ('progress', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('start_time', models.DateTimeField()),
                ('end_time', models.DateTimeField()),
                ('poi_incr_count', models.IntegerField(default=0)),
                ('poi_repeat_count', models.IntegerField(default=0)),
                ('poi_count', models.IntegerField(default=0)),
                ('task_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='weibo_checkin.POITask')),
            ],
        ),
    ]
