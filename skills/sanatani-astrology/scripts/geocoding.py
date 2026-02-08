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
    "ahmedabad": {"latitude": 23.0225, "longitude": 72.5714, "timezone_offset": 5.5, "country": "India"},
    "jaipur": {"latitude": 26.9124, "longitude": 75.7873, "timezone_offset": 5.5, "country": "India"},
    "lucknow": {"latitude": 26.8467, "longitude": 80.9462, "timezone_offset": 5.5, "country": "India"},
    "varanasi": {"latitude": 25.3176, "longitude": 82.9739, "timezone_offset": 5.5, "country": "India"},
    "ayodhya": {"latitude": 26.7991, "longitude": 82.2047, "timezone_offset": 5.5, "country": "India"},
    "patna": {"latitude": 25.5941, "longitude": 85.1376, "timezone_offset": 5.5, "country": "India"},
    "bhopal": {"latitude": 23.2599, "longitude": 77.4126, "timezone_offset": 5.5, "country": "India"},
    "indore": {"latitude": 22.7196, "longitude": 75.8577, "timezone_offset": 5.5, "country": "India"},
    "nagpur": {"latitude": 21.1458, "longitude": 79.0882, "timezone_offset": 5.5, "country": "India"},
    "chandigarh": {"latitude": 30.7333, "longitude": 76.7794, "timezone_offset": 5.5, "country": "India"},
    "kochi": {"latitude": 9.9312, "longitude": 76.2673, "timezone_offset": 5.5, "country": "India"},
    "thiruvananthapuram": {"latitude": 8.5241, "longitude": 76.9366, "timezone_offset": 5.5, "country": "India"},
    "coimbatore": {"latitude": 11.0168, "longitude": 76.9558, "timezone_offset": 5.5, "country": "India"},
    "surat": {"latitude": 21.1702, "longitude": 72.8311, "timezone_offset": 5.5, "country": "India"},
    "agra": {"latitude": 27.1767, "longitude": 78.0081, "timezone_offset": 5.5, "country": "India"},
    "amritsar": {"latitude": 31.6340, "longitude": 74.8723, "timezone_offset": 5.5, "country": "India"},
    # USA - Major Cities
    "new york": {"latitude": 40.7128, "longitude": -74.0060, "timezone_offset": -5.0, "country": "USA"},
    "los angeles": {"latitude": 34.0522, "longitude": -118.2437, "timezone_offset": -8.0, "country": "USA"},
    "chicago": {"latitude": 41.8781, "longitude": -87.6298, "timezone_offset": -6.0, "country": "USA"},
    "houston": {"latitude": 29.7604, "longitude": -95.3698, "timezone_offset": -6.0, "country": "USA"},
    "phoenix": {"latitude": 33.4484, "longitude": -112.0740, "timezone_offset": -7.0, "country": "USA"},
    "san francisco": {"latitude": 37.7749, "longitude": -122.4194, "timezone_offset": -8.0, "country": "USA"},
    "seattle": {"latitude": 47.6062, "longitude": -122.3321, "timezone_offset": -8.0, "country": "USA"},
    "boston": {"latitude": 42.3601, "longitude": -71.0589, "timezone_offset": -5.0, "country": "USA"},
    "miami": {"latitude": 25.7617, "longitude": -80.1918, "timezone_offset": -5.0, "country": "USA"},
    "denver": {"latitude": 39.7392, "longitude": -104.9903, "timezone_offset": -7.0, "country": "USA"},
    "atlanta": {"latitude": 33.7490, "longitude": -84.3880, "timezone_offset": -5.0, "country": "USA"},
    "dallas": {"latitude": 32.7767, "longitude": -96.7970, "timezone_offset": -6.0, "country": "USA"},
    "austin": {"latitude": 30.2672, "longitude": -97.7431, "timezone_offset": -6.0, "country": "USA"},
    "washington dc": {"latitude": 38.9072, "longitude": -77.0369, "timezone_offset": -5.0, "country": "USA"},
    # International
    "london": {"latitude": 51.5074, "longitude": -0.1278, "timezone_offset": 0.0, "country": "UK"},
    "paris": {"latitude": 48.8566, "longitude": 2.3522, "timezone_offset": 1.0, "country": "France"},
    "berlin": {"latitude": 52.5200, "longitude": 13.4050, "timezone_offset": 1.0, "country": "Germany"},
    "tokyo": {"latitude": 35.6762, "longitude": 139.6503, "timezone_offset": 9.0, "country": "Japan"},
    "sydney": {"latitude": -33.8688, "longitude": 151.2093, "timezone_offset": 10.0, "country": "Australia"},
    "singapore": {"latitude": 1.3521, "longitude": 103.8198, "timezone_offset": 8.0, "country": "Singapore"},
    "dubai": {"latitude": 25.2048, "longitude": 55.2708, "timezone_offset": 4.0, "country": "UAE"},
    "toronto": {"latitude": 43.6532, "longitude": -79.3832, "timezone_offset": -5.0, "country": "Canada"},
    "vancouver": {"latitude": 49.2827, "longitude": -123.1207, "timezone_offset": -8.0, "country": "Canada"},
    "hong kong": {"latitude": 22.3193, "longitude": 114.1694, "timezone_offset": 8.0, "country": "Hong Kong"},
    "bangkok": {"latitude": 13.7563, "longitude": 100.5018, "timezone_offset": 7.0, "country": "Thailand"},
    "kuala lumpur": {"latitude": 3.1390, "longitude": 101.6869, "timezone_offset": 8.0, "country": "Malaysia"},
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
    """Estimate timezone offset from coordinates.

    Strategy:
    1. Find nearest city in local DB within 2000km
    2. Fall back to longitude-based estimation
    """
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
    """Search local database for exact or fuzzy match."""
    place_lower = place.lower().strip()

    # Extract country hint if "City, Country" format
    country_hint = None
    city_query = place_lower
    if "," in place_lower:
        city_query = place_lower.split(",")[0].strip()
        country_hint = place_lower.split(",")[1].strip()

    # Exact match (full string)
    if place_lower in LOCATION_DB:
        data = LOCATION_DB[place_lower]
        if not country_hint or country_hint in data.get("country", "").lower():
            return data

    # Exact match on city part
    if city_query in LOCATION_DB:
        data = LOCATION_DB[city_query]
        if not country_hint or country_hint in data.get("country", "").lower():
            return data

    # Partial match with country filtering
    for key, data in LOCATION_DB.items():
        if key in place_lower or place_lower in key or city_query in key or key in city_query:
            if not country_hint or country_hint in data.get("country", "").lower():
                return data

    return None


def _search_geonames(place: str) -> dict | None:
    """Search geonamescache database (23,000+ cities)."""
    cities, countries = _get_geonames_cache()
    if not cities:
        return None

    place_lower = place.lower().strip()
    city_query = place_lower.split(",")[0].strip() if "," in place_lower else place_lower
    country_hint = place_lower.split(",")[1].strip() if "," in place_lower else None

    matches = []
    for city in cities.values():
        city_name = city.get("name", "").lower()
        if city_name == city_query:
            matches.append((city, 0))
        elif city_name.startswith(city_query):
            matches.append((city, 1))
        elif city_query.startswith(city_name):
            matches.append((city, 2))
        elif city_query in city_name:
            matches.append((city, 3))

    if not matches:
        return None

    matches.sort(key=lambda x: (x[1], -x[0].get("population", 0)))

    # If country hint provided, prefer matches from that country
    if country_hint:
        for city, _ in matches:
            country_code = city.get("countrycode", "")
            country_name = countries.get(country_code, {}).get("name", "").lower()
            if country_hint in country_name or country_hint == country_code.lower():
                lat = float(city["latitude"])
                lon = float(city["longitude"])
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "timezone_offset": _estimate_timezone_offset(lat, lon),
                    "country": countries.get(country_code, {}).get("name", country_code),
                    "city": city["name"],
                }

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
    """Search using Nominatim/OpenStreetMap (free geocoding API)."""
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
            country = address.get("country", "Unknown")
            city = (
                address.get("city") or
                address.get("town") or
                address.get("village") or
                address.get("municipality") or
                address.get("state") or
                place
            )

            return {
                "latitude": lat,
                "longitude": lon,
                "timezone_offset": _estimate_timezone_offset(lat, lon),
                "country": country,
                "city": city,
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
        return {
            "success": False,
            "error": "Place name is required.",
            "hint": "Please provide a city name, e.g., 'Mumbai' or 'New York, USA'",
        }

    place = place.strip()

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
        "hint": "Try a larger nearby city, or ask the user for exact coordinates (latitude, longitude) and timezone offset in hours from UTC.",
        "suggestions": [
            "Use a well-known city name (e.g., 'Mumbai' not 'Andheri')",
            "Include country for disambiguation (e.g., 'Springfield, USA')",
            "For small towns, ask user for coordinates from Google Maps",
        ],
    }


def search_locations(query: str, limit: int = 5) -> dict:
    """
    Search for locations matching a query string.

    Returns multiple matching locations for user selection.

    Args:
        query: Search string (e.g., "Spring" to find Springfield, etc.)
        limit: Maximum number of results (default 5)

    Returns:
        Dict with list of matching locations sorted by population.
    """
    if not query or len(query.strip()) < 2:
        return {
            "success": False,
            "error": "Query must be at least 2 characters.",
            "results": [],
        }

    query = query.strip().lower()
    results = []
    seen = set()

    # Search geonames first (largest database)
    cities, countries = _get_geonames_cache()
    if cities:
        matches = []
        for city in cities.values():
            city_name = city.get("name", "").lower()
            if query in city_name or city_name.startswith(query):
                matches.append(city)

        matches.sort(key=lambda x: -x.get("population", 0))

        for city in matches[:limit * 2]:
            country_code = city.get("countrycode", "")
            country_name = countries.get(country_code, {}).get("name", country_code)
            display_name = f"{city['name']}, {country_name}"

            if display_name.lower() in seen:
                continue
            seen.add(display_name.lower())

            lat = float(city["latitude"])
            lon = float(city["longitude"])

            results.append({
                "name": display_name,
                "latitude": lat,
                "longitude": lon,
                "timezone_offset": _estimate_timezone_offset(lat, lon),
                "country": country_name,
                "population": city.get("population", 0),
            })

            if len(results) >= limit:
                break

    # Add from local DB if not enough results
    if len(results) < limit:
        for name, data in LOCATION_DB.items():
            if query in name:
                display_name = f"{name.title()}, {data.get('country', 'Unknown')}"
                if display_name.lower() in seen:
                    continue
                seen.add(display_name.lower())

                results.append({
                    "name": display_name,
                    "latitude": data["latitude"],
                    "longitude": data["longitude"],
                    "timezone_offset": data["timezone_offset"],
                    "country": data.get("country", "Unknown"),
                })

                if len(results) >= limit:
                    break

    return {
        "success": True,
        "query": query,
        "count": len(results),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Geocode location to coordinates")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--place", "-p", help="Place name to geocode")
    group.add_argument("--search", "-s", help="Search for matching locations")
    parser.add_argument("--limit", type=int, default=5, help="Max results for search (default 5)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.search:
        result = search_locations(args.search, args.limit)
        print(json.dumps(result, indent=2))
        sys.exit(0 if result.get("success") else 1)

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
