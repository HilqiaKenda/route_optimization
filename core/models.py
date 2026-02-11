from django.db import models


# Create your models here.
class FuelStation(models.Model):
    opis_id = models.IntegerField(null=True, blank=True)
    station_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    rack_id = models.CharField(max_length=100, null=True, blank=True)
    price = models.FloatField()
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.station_name} - {self.city}, {self.state}"
