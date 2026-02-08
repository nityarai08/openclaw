"""
Birth details validation and coordinate lookup system.

This module provides comprehensive validation for birth details and coordinate
lookup services using geopy and timezonefinder.
"""

import os
import re
import importlib
from datetime import datetime, time
from typing import Dict, Any, Optional, Tuple

try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
except Exception:  # pragma: no cover - geopy optional in some environments
    Nominatim = None  # type: ignore[assignment]

    class GeocoderTimedOut(Exception):  # type: ignore[assignment]
        pass

    class GeocoderServiceError(Exception):  # type: ignore[assignment]
        pass

import pytz

from ..core.data_models import BirthDetails, ValidationResult, LocationData


class BirthDetailsValidator:
    """Comprehensive birth details validation system."""
    
    def __init__(self):
        self.coordinate_service = CoordinateService()
    
    def validate_birth_details(self, birth_data: BirthDetails) -> ValidationResult:
        """
        Validate birth details for completeness and accuracy.
        
        Args:
            birth_data: BirthDetails object to validate
            
        Returns:
            ValidationResult with validation status and messages
        """
        result = ValidationResult(is_valid=True)
        
        # Validate date
        self._validate_date(birth_data.date, result)
        
        # Validate time
        self._validate_time(birth_data.time, result)
        
        # Validate place
        self._validate_place(birth_data.place, result)
        
        # Validate coordinates
        self._validate_coordinates(birth_data.latitude, birth_data.longitude, result)
        
        # Validate timezone offset
        self._validate_timezone_offset(birth_data.timezone_offset, result)
        
        # Cross-validate coordinates with place if possible
        if result.is_valid:
            self._cross_validate_location(birth_data, result)
        
        return result
    
    def _validate_date(self, birth_date: datetime, result: ValidationResult) -> None:
        """Validate birth date."""
        if not isinstance(birth_date, datetime):
            result.add_error("Birth date must be a datetime object")
            return
        
        # Check if date is reasonable (not too far in past or future)
        current_year = datetime.now().year
        birth_year = birth_date.year
        
        if birth_year < 1900:
            result.add_warning(f"Birth year {birth_year} is very old, calculations may be less accurate")
        elif birth_year > current_year:
            result.add_error(f"Birth year {birth_year} cannot be in the future")
        elif birth_year > current_year - 1:
            result.add_warning("Birth date is very recent, ensure accuracy")
        
        # Validate month and day
        if not (1 <= birth_date.month <= 12):
            result.add_error(f"Invalid month: {birth_date.month}")
        
        if not (1 <= birth_date.day <= 31):
            result.add_error(f"Invalid day: {birth_date.day}")
    
    def _validate_time(self, birth_time: time, result: ValidationResult) -> None:
        """Validate birth time."""
        if not isinstance(birth_time, time):
            result.add_error("Birth time must be a time object")
            return
        
        # Check if time components are valid
        if not (0 <= birth_time.hour <= 23):
            result.add_error(f"Invalid hour: {birth_time.hour}")
        
        if not (0 <= birth_time.minute <= 59):
            result.add_error(f"Invalid minute: {birth_time.minute}")
        
        if not (0 <= birth_time.second <= 59):
            result.add_error(f"Invalid second: {birth_time.second}")
    
    def _validate_place(self, place: str, result: ValidationResult) -> None:
        """Validate birth place."""
        if not isinstance(place, str):
            result.add_error("Birth place must be a string")
            return
        
        if not place.strip():
            result.add_error("Birth place cannot be empty")
            return
        
        if len(place.strip()) < 2:
            result.add_error("Birth place must be at least 2 characters long")
        
        # Check for reasonable place name format
        if not re.match(r'^[a-zA-Z\s,.-]+$', place):
            result.add_warning("Birth place contains unusual characters, verify accuracy")
    
    def _validate_coordinates(self, latitude: float, longitude: float, result: ValidationResult) -> None:
        """Validate latitude and longitude coordinates."""
        if not isinstance(latitude, (int, float)):
            result.add_error("Latitude must be a number")
            return
        
        if not isinstance(longitude, (int, float)):
            result.add_error("Longitude must be a number")
            return
        
        if not (-90 <= latitude <= 90):
            result.add_error(f"Latitude {latitude} must be between -90 and 90 degrees")
        
        if not (-180 <= longitude <= 180):
            result.add_error(f"Longitude {longitude} must be between -180 and 180 degrees")
        
        # Check for obviously invalid coordinates (0,0 is suspicious unless specifically intended)
        if latitude == 0 and longitude == 0:
            result.add_warning("Coordinates (0,0) detected - verify this is correct (Gulf of Guinea)")
    
    def _validate_timezone_offset(self, timezone_offset: float, result: ValidationResult) -> None:
        """Validate timezone offset."""
        if not isinstance(timezone_offset, (int, float)):
            result.add_error("Timezone offset must be a number")
            return
        
        if not (-12 <= timezone_offset <= 14):
            result.add_error(f"Timezone offset {timezone_offset} must be between -12 and +14 hours")
        
        # Check for common timezone offset formats (multiples of 0.25 or 0.5)
        if (timezone_offset * 4) % 1 != 0:
            result.add_warning(f"Unusual timezone offset {timezone_offset} - most timezones are multiples of 0.25 hours")
    
    def _cross_validate_location(self, birth_data: BirthDetails, result: ValidationResult) -> None:
        """Cross-validate coordinates with place name."""
        try:
            # Try to lookup coordinates for the place name
            location_data = self.coordinate_service.lookup_coordinates(birth_data.place)
            
            if location_data:
                # Check if coordinates are reasonably close (within ~50km)
                lat_diff = abs(location_data.latitude - birth_data.latitude)
                lon_diff = abs(location_data.longitude - birth_data.longitude)
                
                # Rough approximation: 1 degree ≈ 111km
                distance_km = ((lat_diff ** 2 + lon_diff ** 2) ** 0.5) * 111
                
                if distance_km > 50:
                    result.add_warning(
                        f"Coordinates seem far from place '{birth_data.place}' "
                        f"(~{distance_km:.1f}km difference). Verify accuracy."
                    )
                
                # Check timezone consistency
                expected_tz_offset = self.coordinate_service.get_timezone_offset(
                    location_data.latitude, location_data.longitude, birth_data.date
                )
                
                if expected_tz_offset is not None:
                    tz_diff = abs(expected_tz_offset - birth_data.timezone_offset)
                    if tz_diff > 1:  # Allow 1 hour difference for DST variations
                        result.add_warning(
                            f"Timezone offset {birth_data.timezone_offset} differs from expected "
                            f"{expected_tz_offset} for location '{birth_data.place}'"
                        )
        
        except Exception as e:
            result.add_warning(f"Could not cross-validate location: {str(e)}")


class CoordinateService:
    """Service for coordinate lookup and timezone resolution."""
    
    def __init__(self):
        self.geocoder = Nominatim(user_agent="kundali_generator_v2.0") if Nominatim else None
        self._timezone_finder_cls = self._resolve_timezone_finder()
        self._timezone_finder_instance = None
        self._cache = {}  # Simple cache for repeated lookups

    @staticmethod
    def _resolve_timezone_finder():
        """Lazily import TimezoneFinder when explicitly enabled to avoid segfaults in constrained envs."""
        if os.getenv("ENABLE_TIMEZONEFINDER", "").strip().lower() not in {"1", "true", "yes"}:
            return None
        try:
            spec = importlib.util.find_spec("timezonefinder")  # type: ignore[attr-defined]
        except Exception:
            spec = None
        if spec is None:
            return None
        try:
            module = importlib.import_module("timezonefinder")
            return getattr(module, "TimezoneFinder", None)
        except Exception:
            return None
    
    def lookup_coordinates(self, place_name: str) -> Optional[LocationData]:
        """
        Lookup coordinates for a place name using geopy.
        
        Args:
            place_name: Name of the place to lookup
            
        Returns:
            LocationData object with coordinates and timezone info, or None if not found
        """
        # Check cache first
        cache_key = place_name.lower().strip()
        if cache_key in self._cache:
            return self._cache[cache_key]

        if self.geocoder is None:
            return None
        
        try:
            location = self.geocoder.geocode(place_name, timeout=10)
            
            if location:
                # Get timezone information
                timezone_offset = self.get_timezone_offset(
                    location.latitude, location.longitude
                )
                
                location_data = LocationData(
                    place_name=place_name,
                    latitude=location.latitude,
                    longitude=location.longitude,
                    timezone_offset=timezone_offset or 0.0,
                    country=getattr(location.raw.get('address', {}), 'country', None),
                    region=getattr(location.raw.get('address', {}), 'state', None)
                )
                
                # Cache the result
                self._cache[cache_key] = location_data
                return location_data
            
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            print(f"Geocoding service error for '{place_name}': {e}")
        except Exception as e:
            print(f"Unexpected error during geocoding for '{place_name}': {e}")
        
        return None
    
    def get_timezone_offset(self, latitude: float, longitude: float, 
                          reference_date: Optional[datetime] = None) -> Optional[float]:
        """
        Get timezone offset for coordinates at a specific date.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            reference_date: Date for timezone calculation (for DST handling)
            
        Returns:
            Timezone offset in hours, or None if not found
        """
        if self._timezone_finder_cls is None or pytz is None:
            return None

        try:
            if self._timezone_finder_instance is None:
                self._timezone_finder_instance = self._timezone_finder_cls()
            timezone_name = self._timezone_finder_instance.timezone_at(lat=latitude, lng=longitude)
            
            if timezone_name:
                tz = pytz.timezone(timezone_name)
                
                # Use reference date or current date for DST calculation
                if reference_date is None:
                    reference_date = datetime.now()
                
                # Get timezone offset for the specific date
                localized_dt = tz.localize(reference_date.replace(tzinfo=None))
                offset_seconds = localized_dt.utcoffset().total_seconds()
                offset_hours = offset_seconds / 3600
                
                return offset_hours
            
        except Exception as e:
            print(f"Timezone lookup error for ({latitude}, {longitude}): {e}")
        
        return None
    
    def parse_coordinates(self, coord_string: str) -> Optional[Tuple[float, float]]:
        """
        Parse coordinates from various string formats.
        
        Supported formats:
        - Decimal: "28.6441, 77.0936"
        - DMS: "28°38'39"N, 77°05'37"E"
        - Mixed: "28.6441N, 77.0936E"
        
        Args:
            coord_string: String containing coordinates
            
        Returns:
            Tuple of (latitude, longitude) or None if parsing fails
        """
        try:
            coord_string = coord_string.strip()
            
            # Try decimal format first
            decimal_match = re.match(
                r'^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$', 
                coord_string
            )
            if decimal_match:
                lat, lon = float(decimal_match.group(1)), float(decimal_match.group(2))
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            
            # Try DMS format
            dms_match = re.match(
                r'^(\d+)°(\d+)\'(\d+)"?([NS])\s*,\s*(\d+)°(\d+)\'(\d+)"?([EW])$',
                coord_string.upper()
            )
            if dms_match:
                lat_deg, lat_min, lat_sec, lat_dir = dms_match.groups()[:4]
                lon_deg, lon_min, lon_sec, lon_dir = dms_match.groups()[4:]
                
                lat = float(lat_deg) + float(lat_min)/60 + float(lat_sec)/3600
                lon = float(lon_deg) + float(lon_min)/60 + float(lon_sec)/3600
                
                if lat_dir == 'S':
                    lat = -lat
                if lon_dir == 'W':
                    lon = -lon
                
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            
            # Try decimal with direction
            decimal_dir_match = re.match(
                r'^(\d+\.?\d*)([NS])\s*,\s*(\d+\.?\d*)([EW])$',
                coord_string.upper()
            )
            if decimal_dir_match:
                lat, lat_dir, lon, lon_dir = decimal_dir_match.groups()
                lat, lon = float(lat), float(lon)
                
                if lat_dir == 'S':
                    lat = -lat
                if lon_dir == 'W':
                    lon = -lon
                
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
            
        except (ValueError, AttributeError) as e:
            print(f"Coordinate parsing error for '{coord_string}': {e}")
        
        return None
    
    def validate_coordinates_format(self, coord_string: str) -> ValidationResult:
        """
        Validate coordinate string format without parsing.
        
        Args:
            coord_string: String containing coordinates
            
        Returns:
            ValidationResult with format validation status
        """
        result = ValidationResult(is_valid=True)
        
        if not isinstance(coord_string, str):
            result.add_error("Coordinates must be provided as a string")
            return result
        
        if not coord_string.strip():
            result.add_error("Coordinate string cannot be empty")
            return result
        
        # Try to parse coordinates
        parsed_coords = self.parse_coordinates(coord_string)
        
        if parsed_coords is None:
            result.add_error(
                f"Could not parse coordinates '{coord_string}'. "
                "Supported formats: '28.6441, 77.0936', '28°38'39\"N, 77°05'37\"E', '28.6441N, 77.0936E'"
            )
        else:
            lat, lon = parsed_coords
            result.add_warning(f"Parsed coordinates: {lat:.6f}, {lon:.6f}")
        
        return result


def create_birth_details_from_input(
    date_str: str,
    time_str: str,
    place: str,
    coordinates: Optional[str] = None,
    timezone_offset: Optional[float] = None
) -> Tuple[BirthDetails, ValidationResult]:
    """
    Create BirthDetails object from string inputs with validation.
    
    Args:
        date_str: Date string in format "YYYY-MM-DD"
        time_str: Time string in format "HH:MM:SS" or "HH:MM"
        place: Place name
        coordinates: Optional coordinate string to parse
        timezone_offset: Optional timezone offset in hours
        
    Returns:
        Tuple of (BirthDetails object, ValidationResult)
    """
    result = ValidationResult(is_valid=True)
    coordinate_service = CoordinateService()
    
    # Parse date
    try:
        birth_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            birth_date = datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            result.add_error(f"Invalid date format '{date_str}'. Use YYYY-MM-DD or DD-MM-YYYY")
            birth_date = datetime.now()  # Fallback
    
    # Parse time
    try:
        if len(time_str.split(':')) == 2:
            birth_time = datetime.strptime(time_str, "%H:%M").time()
        else:
            birth_time = datetime.strptime(time_str, "%H:%M:%S").time()
    except ValueError:
        result.add_error(f"Invalid time format '{time_str}'. Use HH:MM or HH:MM:SS")
        birth_time = time(12, 0)  # Fallback to noon
    
    # Handle coordinates
    latitude, longitude = 0.0, 0.0
    
    if coordinates:
        parsed_coords = coordinate_service.parse_coordinates(coordinates)
        if parsed_coords:
            latitude, longitude = parsed_coords
        else:
            result.add_error(f"Could not parse coordinates: {coordinates}")
    else:
        # Try to lookup coordinates from place name
        location_data = coordinate_service.lookup_coordinates(place)
        if location_data:
            latitude = location_data.latitude
            longitude = location_data.longitude
            if timezone_offset is None:
                timezone_offset = location_data.timezone_offset
        else:
            result.add_error(f"Could not find coordinates for place '{place}' and no coordinates provided")
    
    # Handle timezone offset
    if timezone_offset is None:
        timezone_offset = coordinate_service.get_timezone_offset(latitude, longitude, birth_date)
        if timezone_offset is None:
            result.add_warning("Could not determine timezone offset, using UTC (0.0)")
            timezone_offset = 0.0
    
    # Create BirthDetails object
    birth_details = BirthDetails(
        date=birth_date,
        time=birth_time,
        place=place,
        latitude=latitude,
        longitude=longitude,
        timezone_offset=timezone_offset
    )
    
    return birth_details, result
