from django.db import models


class Area(models.Model):
    min_lat = models.DecimalField(max_digits=9, decimal_places=6)
    max_lat = models.DecimalField(max_digits=9, decimal_places=6)
    min_lon = models.DecimalField(max_digits=9, decimal_places=6)
    max_lon = models.DecimalField(max_digits=9, decimal_places=6)
    poi_count = models.IntegerField(default=0)
    last_updated_at = models.DateTimeField()