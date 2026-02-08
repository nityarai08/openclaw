#!/usr/bin/env python3
"""
Geocoding tool for location lookup.

Resolves place names to coordinates and timezone.
Uses multiple providers with fallback chain:
1. Local database (instant, common cities)
2. geonamescache (23,000+ cities, offline)
3. Nominatim/OpenStreetMap (free online)
"""

import argparse
import json
import math
import sys

# Lazy-loaded optional dependencies
_NOMINATIM = None
_NOMINATIM_TRIED = False
_GEONAMES_CACHE = None
_GEONAMES_COUNTRIES = None


def _get_nominatim():
    """Lazy load Nominatim geocoder."""
    global _NOMINATIM, _NOMINATIM_TRIED
    if _NOMINATIM_TRIED:
        return _NOMINATIM
    _NOMINATIM_TRIED = True
    try:
        from geopy.geocoders import Nominatim
        _NOMINATIM = Nominatim
    except ImportError:
        _NOMINATIM = None
    return _NOMINATIM


def _get_geonames_cache():
    """Lazy load geonamescache (23,000+ cities)."""
    global _GEONAMES_CACHE, _GEONAMES_COUNTRIES
    if _GEONAMES_CACHE is not None:
        return _GEONAMES_CACHE, _GEONAMES_COUNTRIES
    try:
        import geonamescache
        gc = geonamescache.GeonamesCache()
        _GEONAMES_CACHE = gc.get_cities()
        _GEONAMES_COUNTRIES = gc.get_countries()
    except ImportError:
        _GEONAMES_CACHE = {}
        _GEONAMES_COUNTRIES = {}
    return _GEONAMES_CACHE, _GEONAMES_COUNTRIES


# Local fallback database (common cities)
LOCATION_DB = {
    # India - Major Cities
    "delhi": {"latitude": 28.6139, "longitude": 77.2090, "timezone_offset": 5.5, "country": "India"},
    "new delhi": {"latitude": 28.6139, "longitude": 77.2090, "timezone_offset": 5.5, "country": "India"},
    "mumbai": {"latitude": 19.0760, "longitude": 72.8777, "timezone_offset": 5.5, "country": "India"},
    "bangalore": {"latitude": 12.9716, "longitude": 77.5946, "timezone_offset": 5.5, "country": "India"},
    "bengaluru": {"latitude": 12.9716, "longitude": 77.5946, "timezone_offset": 5.5, "country": "India"},
    "chennai": {"latitude": 13.0827, "longitude": 80.2707, "timezone_offset": 5.5, "country": "India"},
    "kolkata": {"latitude": 22.5726, "longitude": 88.3639, "timezone_offset": 5.5, "country": "India"},
    "hyderabad": {"latitude": 17.3850, "longitude": 78.4867, "timezone_offset": 5.5, "country": "India"},
    "pune": {"latitude": 18.5204, "longitude": 73.8567, "timezone_offset": 5.5, "country": "India"},
    "jaipur": {"latitude": 26.9124, "longitude": 75.7873, "timezone_offset": 5.5, "country": "India"},
    "varanasi": {"latitude": 25.3176, "longitude": 82.9739, "timezone_offset": 5.5, "country": "India"},
    "ayodhya": {"latitude": 26.7991, "longitude": 82.2047, "timezone_offset": 5.5, "country": "India"},
    # USA - Major Cities
    "new york": {"latitude": 40.7128, "longitude": -74.0060, "timezone_offset": -5.0, "country": "USA"},
    "los angeles": {"latitude": 34.0522, "longitude": -118.2437, "timezone_offset": -8.0, "country": "USA"},
    "chicago": {"latitude": 41.8781, "longitude": -87.6298, "timezone_offset": -6.0, "country": "USA"},
    "san francisco": {"latitude": 37.7749, "longitude": -122.4194, "timezone_offset": -8.0, "country": "USA"},
    "seattle": {"latitude": 47.6062, "longitude": -122.3321, "timezone_offset": -8.0, "country": "USA"},
    # International
    "london": {"latitude": 51.5074, "longitude": -0.1278, "timezone_offset": 0.0, "country": "UK"},
    "tokyo": {"latitude": 35.6762, "longitude": 139.6503, "timezone_offset": 9.0, "country": "Japan"},
    "sydney": {"latitude": -33.8688, "longitude": 151.2093, "timezone_offset": 10.0, "country": "Australia"},
    "singapore": {"latitude": 1.3521, "longitude": 103.8198, "timezone_offset": 8.0, "country": "Singapore"},
    "dubai": {"latitude": 25.2048, "longitude": 55.2708, "timezone_offset": 4.0, "country": "UAE"},
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great circle distance between two points in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def _estimate_timezone_offset(latitude: float, longitude: float) -> float:
    """Estimate timezone offset from coordinates."""
    nearest_dist = float("inf")
    nearest_offset = None

    for data in LOCATION_DB.values():
        dist = _haversine(latitude, longitude, data["latitude"], data["longitude"])
        if dist < nearest_dist:
            nearest_dist = dist
            nearest_offset = data["timezone_offset"]

    if nearest_dist < 2000 and nearest_offset is not None:
        return nearest_offset

    raw_offset = longitude / 15.0
    return round(raw_offset * 2) / 2


def _search_local_db(place: str) -> dict | None:
    """Search local database for match."""
    place_lower = place.lower().strip()
    
    if place_lower in LOCATION_DB:
        return LOCATION_DB[place_lower]
    
    if "," in place_lower:
        city_part = place_lower.split(",")[0].strip()
        if city_part in LOCATION_DB:
            return LOCATION_DB[city_part]
    
    for key, data in LOCATION_DB.items():
        if key in place_lower or place_lower in key:
            return data
    
    return None


def _search_geonames(place: str) -> dict | None:
    """Search geonamescache database."""
    cities, countries = _get_geonames_cache()
    if not cities:
        return None

    place_lower = place.lower().strip()
    city_query = place_lower.split(",")[0].strip() if "," in place_lower else place_lower

    matches = []
    for city in cities.values():
        city_name = city.get("name", "").lower()
        if city_name == city_query:
            matches.append((city, 0))
        elif city_name.startswith(city_query):
            matches.append((city, 1))

    if not matches:
        return None

    matches.sort(key=lambda x: (x[1], -x[0].get("population", 0)))
    best_city = matches[0][0]
    country_code = best_city.get("countrycode", "")
    lat = float(best_city["latitude"])
    lon = float(best_city["longitude"])

    return {
        "latitude": lat,
        "longitude": lon,
        "timezone_offset": _estimate_timezone_offset(lat, lon),
        "country": countries.get(country_code, {}).get("name", country_code),
        "city": best_city["name"],
    }


def _search_nominatim(place: str) -> dict | None:
    """Search using Nominatim/OpenStreetMap."""
    Nominatim = _get_nominatim()
    if Nominatim is None:
        return None

    try:
        geolocator = Nominatim(user_agent="sanatani_astrology_geocoder")
        location = geolocator.geocode(place, addressdetails=True, timeout=10)

        if location:
            lat = float(location.latitude)
            lon = float(location.longitude)
            address = location.raw.get("address", {})
            
            return {
                "latitude": lat,
                "longitude": lon,
                "timezone_offset": _estimate_timezone_offset(lat, lon),
                "country": address.get("country", "Unknown"),
                "city": address.get("city") or address.get("town") or address.get("state") or place,
            }
    except Exception:
        pass

    return None


def geocode_location(place: str) -> dict:
    """
    Resolve a place name to coordinates and timezone.

    Args:
        place: Place name (e.g., "Mumbai", "New York, USA")

    Returns:
        Dict with latitude, longitude, timezone_offset, country.
    """
    if not place or not place.strip():
        return {"success": False, "error": "Place name is required."}

    place = place.strip()
    
    # Try each source
    for search_fn, source in [
        (_search_local_db, "local"),
        (_search_geonames, "geonames"),
        (_search_nominatim, "nominatim"),
    ]:
        result = search_fn(place)
        if result:
            return {
                "success": True,
                "place": place,
                "resolved_place": result.get("city", place),
                "latitude": result["latitude"],
                "longitude": result["longitude"],
                "timezone_offset": result["timezone_offset"],
                "country": result.get("country", "Unknown"),
                "source": source,
            }

    return {
        "success": False,
        "error": f"Location '{place}' not found.",
        "hint": "Try a larger nearby city, or provide exact coordinates.",
    }


def main():
    parser = argparse.ArgumentParser(description="Geocode location to coordinates")
    parser.add_argument("--place", "-p", required=True, help="Place name to geocode")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    result = geocode_location(args.place)
    
    if args.json or not result.get("success"):
        print(json.dumps(result, indent=2))
    else:
        print(f"Place: {result['resolved_place']}, {result['country']}")
        print(f"Latitude: {result['latitude']}")
        print(f"Longitude: {result['longitude']}")
        print(f"Timezone: UTC{result['timezone_offset']:+.1f}")
    
    sys.exit(0 if result.get("success") else 1)


if __name__ == "__main__":
    main()
