import geopandas as gpd
from shapely.geometry import Point

CAR_RANGE = 500
MPG = 10


def stations_near(point, stations, radius=50):
    """Return stations within `radius` miles of `point`.
    Uses GeoPandas to efficiently calculate proximity.
    """
    if not stations:
        return []

    point_geom = Point(point[1], point[0])
    stations_data = [
        {
            "station_name": s.station_name,
            "latitude": s.latitude,
            "longitude": s.longitude,
            "price": s.price,
            "city": s.city,
        }
        for s in stations
        if s.latitude is not None and s.longitude is not None
    ]

    stations_gdf = gpd.GeoDataFrame(
        stations_data,
        geometry=[Point(s["longitude"], s["latitude"]) for s in stations_data],
        crs="EPSG:4326",
    )

    stations_gdf = stations_gdf.to_crs(epsg=3395)
    point_gdf = gpd.GeoDataFrame({"geometry": [point_geom]}, crs="EPSG:4326").to_crs(
        epsg=3395
    )
    buffer = point_gdf.geometry.buffer(radius * 1609.34)

    nearby_stations = stations_gdf[stations_gdf.geometry.within(buffer.unary_union)]

    return nearby_stations


def compute_stops(route_coords, stations):
    """Compute fuel stops along a route."""
    if not stations:
        raise ValueError("Stations cannot be None")

    stops = []
    next_mark = CAR_RANGE
    miles_so_far = 0

    route_gdf = gpd.GeoDataFrame(
        {"geometry": [Point(lon, lat) for lat, lon in route_coords]}, crs="EPSG:4326"
    )

    route_gdf = route_gdf.to_crs(epsg=3395)

    for i in range(1, len(route_coords)):
        segment_start = route_coords[i - 1]
        segment_end = route_coords[i]

        segment_miles = (
            gpd.GeoSeries([Point(segment_start[1], segment_start[0])]).distance(
                Point(segment_end[1], segment_end[0])
            )
            / 1609.34
        )

        miles_so_far += segment_miles.item()

        if miles_so_far >= next_mark:
            nearby_stations = stations_near(segment_end, stations, radius=50)

            if not nearby_stations.empty:
                cheapest = nearby_stations.loc[nearby_stations["price"].idxmin()]

                gallons = CAR_RANGE / MPG
                cost = gallons * cheapest["price"]

                stops.append(
                    {
                        "station": cheapest["station_name"],
                        "city": cheapest["city"],
                        "price_per_gallon": cheapest["price"],
                        "gallons": gallons,
                        "cost": round(cost, 2),
                    }
                )

            next_mark += CAR_RANGE

    total = round(sum(s["cost"] for s in stops), 2)
    return stops, total
