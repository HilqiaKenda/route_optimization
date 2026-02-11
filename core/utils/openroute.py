import requests
import logging
from django.conf import settings
from django.core.cache import cache
from concurrent.futures import ThreadPoolExecutor, as_completed


log = logging.getLogger("__name__")
executor = ThreadPoolExecutor(max_workers=4)


def get_route(start, end):
    """
    Get addresses as strings and Returns route coordinates and total miles.
    get: start, end
    return -> coordinates
    """
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    params = {
        "api_key": settings.ORS_API_KEY,
        "start": f"{start[0]},{start[1]}",
        "end": f"{end[0]},{end[1]}",
    }

    try:
        cache_key = f"route:{start}:{end}"
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        response = requests.get(url, params=params, timeout=3)
        response.raise_for_status()
        data = response.json()

        feature = data["features"][0]
        distance_m = feature["properties"]["summary"]["distance"]
        miles = distance_m * 0.000621371  # Convert meters to miles

        route_coords = [(lat, lon) for lon, lat in feature["geometry"]["coordinates"]]

        cache.set(cache_key, (route_coords, miles), timeout=3600)
        return route_coords, miles

    except requests.exceptions.RequestException as e:
        log.error(f"Error in get_route: {e}")
        return [], 0
    except Exception as e:
        log.error(f"Error processing route: {e}")
        return [], 0


def bbox_from_coords(coords):
    """
    Calculate the bounding box from a list of coordinates.
    coords: list of (lat, lon) tuples
    return: list[list]
    """
    return [
        [coords[0][1] - 0.001, coords[0][0] - 0.001],
        [coords[1][1] + 0.001, coords[1][0] + 0.001],
    ]


def get_pois_along_route(coords, buffer_meters=200, category_filter=None):
    """
    Fetch POIs along a route using OpenRouteService based on the provided coordinates,
    and filter by the specified category.
    """
    cache_key = f"pois_{str(coords)}_{buffer_meters}:filter:{category_filter}"
    cached_pois = cache.get(cache_key)

    if cached_pois:
        return cached_pois

    bbox = bbox_from_coords(coords)
    url = "https://api.openrouteservice.org/pois"

    payload = {
        "request": "pois",
        "geometry": {
            "bbox": bbox,
            "geojson": {
                "type": "Point",
                "coordinates": bbox[0],
            },
            "buffer": buffer_meters,
        },
    }

    headers = {
        "Authorization": settings.ORS_API_KEY,
        "Content-Type": "application/json; charset=utf-8",
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=3)
        response.raise_for_status()
        data = response.json()
        pois = []

        for feature in data.get("features", []):
            props = feature["properties"]
            res_coords = feature["geometry"]["coordinates"]

            osm_tags = props.get("osm_tags", {})
            name = osm_tags.get("name", "Unknown")
            website = osm_tags.get("website", "")
            opening_hours = osm_tags.get("opening_hours", "")

            categories = [
                category["category_name"]
                for category in props.get("category_ids", {}).values()
            ]

            if category_filter:
                if category_filter in categories:
                    pois.append(
                        {
                            "name": name,
                            "latitude": res_coords[1],
                            "longitude": res_coords[0],
                            "categories": categories,
                            "website": website,
                            "opening_hours": opening_hours,
                        }
                    )
            else:
                pois.append(
                    {
                        "name": name,
                        "latitude": res_coords[1],
                        "longitude": res_coords[0],
                        "categories": categories,
                        "website": website,
                        "opening_hours": opening_hours,
                    }
                )

        cache.set(cache_key, pois, timeout=5)
        return pois

    except requests.exceptions.RequestException as e:
        log.error(f"Error making request to OpenRouteService: {e}")
        return []
    except Exception as e:
        log.error(f"Error processing POIs: {e}")
        return []


def fetch_data_concurrently(start, end, coords, category_filter=None):
    """
    Use ThreadPoolExecutor to fetch routes and POIs concurrently.
    """

    futures = []
    route_future = executor.submit(get_route, start, end)
    pois_future = executor.submit(get_pois_along_route, coords, 500, category_filter)
    futures.extend([route_future, pois_future])
    results = {}

    for future in as_completed(futures):
        try:
            result = future.result()
            if future == route_future:
                results["route"] = result
            if future == pois_future:
                results["pois"] = result
        except Exception as e:
            log.error(f"Error in concurrent fetching: {e}")
    return results
