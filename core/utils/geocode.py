import concurrent.futures
import geopandas as gpd
from functools import lru_cache


@lru_cache(maxsize=1000)
def geocode_single_cached(address: str):
    """Geocode a single address with caching."""
    loc = gpd.tools.geocode(address)

    if loc.empty:
        raise ValueError(f"Address not found: {address}")

    return loc.geometry.iloc[0].x, loc.geometry.iloc[0].y


def geocode_address(starting_address: str, ending_address: str):
    """Geocode two addresses in parallel, using cached results if available."""

    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(
            executor.map(geocode_single_cached, [starting_address, ending_address])
        )

    return {"start": results[0], "end": results[1]}
