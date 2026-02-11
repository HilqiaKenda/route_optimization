import redis
import json
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from core.models import FuelStation
from core.utils.geocode import geocode_address
from core.utils.fuel_loader import FuelRepository
from core.utils.openroute import get_pois_along_route, get_route
from core.utils.optimizer import compute_stops

import traceback

log = logging.getLogger("__name__")

redis_client = redis.StrictRedis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True
)


class RouteAPIView(APIView):

    def get_cache_key(self, start_address, end_address, category_filter):
        return f"route:{start_address}:{end_address}:filter:{category_filter}"

    def post(self, request):
        try:

            start_address = request.data.get("start")
            end_address = request.data.get("end")
            category_filter = "bench"

            if not start_address or not end_address:
                log.error("Both 'start' and 'end' addresses were not provided")

                return Response(
                    {
                        "error": "Both 'start' and 'end' addresses are required",
                        "status": False,
                    },
                    status=400,
                )

            cache_key = self.get_cache_key(start_address, end_address, category_filter)
            cached_result = redis_client.get(cache_key)

            if cached_result:
                return Response(json.loads(cached_result))

            if isinstance(start_address, (tuple, list)) and isinstance(
                end_address, (tuple, list)
            ):
                start = tuple(start_address)
                end = tuple(end_address)

            else:
                address = geocode_address(start_address, end_address)
                start = address["start"]
                end = address["end"]

            coords, miles = get_route(start, end)
            pois = get_pois_along_route(coords, category_filter=category_filter)

            if not pois:
                log.warn("No POIs found along the route")

                return Response(
                    {"error": "No POIs found along the route", "status": False},
                    status=404,
                )

            class POIStation:
                def __init__(self, name, lat, lng, price=4.5, city=""):
                    self.station_name = name
                    self.latitude = lat
                    self.longitude = lng
                    self.price = price
                    self.city = city

            stations = [
                POIStation(
                    p["name"],
                    p["latitude"],
                    p["longitude"],
                    p.get("price", 4.5),
                    p.get("city", ""),
                )
                for p in pois
            ]

            repo = FuelRepository()
            repo.load_if_empty()

            stops, total = compute_stops(coords, repo.all())

            result = {
                "distance_miles": round(miles, 2),
                "fuel_stops": stops,
                "total_fuel_cost": total,
                "start_address": start,
                "end_address": end,
                "pois": pois,
            }

            redis_client.setex(cache_key, 3600, json.dumps(result))

        except FuelStation.DoesNotExist as exce:
            log.warning("FuelStation does not exist")

            return Response(
                {
                    "error": "FuelStation does not exist",
                    "status": False,
                    "details": str(exce),
                },
                status=500,
            )
        except Exception as exce:
            log.warn("Unknown error occurred")

            return Response(
                {
                    "error": "Unknown error occurred",
                    "status": False,
                    "details": str(exce),
                },
                status=500,
            )

        return Response(result, status=200)
