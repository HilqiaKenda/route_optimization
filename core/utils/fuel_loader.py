import os
import pandas as pd
from django.conf import settings
from core.models import FuelStation
from geopy.geocoders import Nominatim

INPUT_CSV = "fuel-prices-for-be-assessment.csv"
geolocator = Nominatim(user_agent="fuel_app")


class FuelRepository:
    def load_if_empty(self):

        if FuelStation.objects.exists():
            return

        path = os.path.join(settings.BASE_DIR, INPUT_CSV)
        df = pd.read_csv(path)

        for _, row in df.iterrows():
            address = f"{row['Address']}, {row['City']}, {row['State']}"
            location = geolocator.geocode(address)
            FuelStation.objects.create(
                opis_id=row.get("OPIS Truckstop ID"),
                station_name=row.get("Truckstop Name"),
                address=address,
                city=row.get("City"),
                state=row.get("State"),
                rack_id=row.get("Rack ID"),
                price=row.get("Retail Price"),
                latitude=location.latitude if location else None,
                longitude=location.longitude if location else None,
            )

    def all(self):
        return FuelStation.objects.all()
