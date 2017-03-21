from django.db import models
from django.utils import timezone
from django.core.cache import cache
# from django.core.serializers.json import DjangoJSONEncoder
import json
from datetime import datetime


def _convert_json(obj):
    d = {}
    d.update(obj.__dict__)
    return d


class Area(models.Model):
    name = models.CharField(max_length=100)
    min_lat = models.DecimalField(max_digits=9, decimal_places=6)
    max_lat = models.DecimalField(max_digits=9, decimal_places=6)
    min_lon = models.DecimalField(max_digits=9, decimal_places=6)
    max_lon = models.DecimalField(max_digits=9, decimal_places=6)
    poi_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated_at = models.DateTimeField(auto_now=True)


class POITask(models.Model):
    area = models.ForeignKey(Area, on_delete=models.CASCADE)
    status = models.IntegerField(default=0)
    last_error = models.CharField(max_length=100, default="")
    progress = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    poi_count = models.IntegerField(default=0)
    poi_add_count = models.IntegerField(default=0)


# class POITaskWorker(models.Model):
#     task = models.ForeignKey(POITask, on_delete=models.CASCADE)
#     worker = models.IntegerField(default=0)
#     min_lat = models.DecimalField(max_digits=9, decimal_places=6)
#     max_lat = models.DecimalField(max_digits=9, decimal_places=6)
#     min_lon = models.DecimalField(max_digits=9, decimal_places=6)
#     max_lon = models.DecimalField(max_digits=9, decimal_places=6)
#     created_at = models.DateTimeField(auto_now_add=True)
#     start_time = models.DateTimeField(null=True)
#     end_time = models.DateTimeField(null=True)
#     poi_incr_count = models.IntegerField(default=0)
#     poi_repeat_count = models.IntegerField(default=0)
#     poi_count = models.IntegerField(default=0)


# class POITaskOfWorker(models.Model):
#     task = models.ForeignKey(POITask, on_delete=models.CASCADE)
#     worker = models.IntegerField(default=0)
#     is_working = models.IntegerField(default=0)
#     is_done = models.IntegerField(default=0)
#     is_error = models.IntegerField(default=0)
#     error_message = models.CharField(max_length=100)
#     min_lat = models.DecimalField(max_digits=9, decimal_places=6)
#     max_lat = models.DecimalField(max_digits=9, decimal_places=6)
#     min_lon = models.DecimalField(max_digits=9, decimal_places=6)
#     max_lon = models.DecimalField(max_digits=9, decimal_places=6)
#     cur_lat = models.DecimalField(max_digits=9, decimal_places=6)
#     cur_lon = models.DecimalField(max_digits=9, decimal_places=6)
#     progress = models.IntegerField(default=0)
#     start_time = models.DateTimeField(auto_now_add=True, null=True)
#     end_time = models.DateTimeField(null=True)
#     poi_incr_count = models.IntegerField(default=0)
#     poi_repeat_count = models.IntegerField(default=0)
#     poi_count = models.IntegerField(default=0)


# class POIWorkerTask(object):
#     def __init__(self):
#         self.id = None
#         self.task_id = None
#         self.worker_id = None
#         self.is_working = False
#         self.is_done = False
#         self.is_error = False
#         self.error_message = None
#         self.min_lat = 0.0
#         self.max_lat = 0.0
#         self.min_lon = 0.0
#         self.max_lon = 0.0
#         self.cur_lat = 0.0
#         self.cur_lon = 0.0
#         self.progress = 0
#         self.created_at = timezone.now()
#         self.start_time = None
#         self.end_time = None
#         self.poi_incr_count = 0
#         self.poi_repeat_count = 0
#         self.poi_count = 0
