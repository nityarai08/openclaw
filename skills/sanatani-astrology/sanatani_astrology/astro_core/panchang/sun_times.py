"""
Sun Times Calculator - Accurate sunrise/sunset using Swiss Ephemeris.

Provides astronomical sunrise and sunset times with high accuracy.
Falls back to simplified calculations if Swiss Ephemeris is unavailable.
"""

import math
import logging
from datetime import datetime, date as date_type, timedelta
from typing import Dict, Optional, Tuple, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import Swiss Ephemeris
try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
except ImportError:
    SWISSEPH_AVAILABLE = False
    logger.warning("Swiss Ephemeris not available, using simplified sunrise calculations")


@dataclass
class SunTimes:
    """Sun times data for a specific date and location."""
    sunrise: datetime
    sunset: datetime
    noon: datetime
    day_duration_seconds: float
    night_duration_seconds: float

    @property
    def day_duration_hours(self) -> float:
        """Day duration in hours."""
        return self.day_duration_seconds / 3600

    @property
    def night_duration_hours(self) -> float:
        """Night duration in hours."""
        return self.night_duration_seconds / 3600


class SunTimesCalculator:
    """
    Calculator for sunrise and sunset times.

    Uses Swiss Ephemeris for accurate calculations when available,
    with fallback to simplified astronomical formulas.
    """

    def __init__(self):
        """Initialize the calculator."""
        self._use_swisseph = SWISSEPH_AVAILABLE
        if self._use_swisseph:
            # Set ephemeris path if needed (uses built-in if not set)
            try:
                swe.set_ephe_path(None)
            except Exception:
                pass

    def calculate(
        self,
        date: Union[datetime, date_type],
        latitude: float,
        longitude: float,
        timezone_offset: float = 0.0
    ) -> SunTimes:
        """
        Calculate sunrise and sunset for a given date and location.

        Args:
            date: Date for calculation (time component ignored, uses midnight)
            latitude: Latitude in degrees (-90 to 90)
            longitude: Longitude in degrees (-180 to 180)
            timezone_offset: Timezone offset in hours from UTC

        Returns:
            SunTimes object with sunrise, sunset, and duration info
        """
        # Convert date to datetime if needed
        if isinstance(date, date_type) and not isinstance(date, datetime):
            date = datetime.combine(date, datetime.min.time())

        if self._use_swisseph:
            return self._calculate_swisseph(date, latitude, longitude, timezone_offset)
        else:
            return self._calculate_simplified(date, latitude, longitude, timezone_offset)

    def _calculate_swisseph(
        self,
        date: datetime,
        latitude: float,
        longitude: float,
        timezone_offset: float
    ) -> SunTimes:
        """Calculate using Swiss Ephemeris for high accuracy."""
        try:
            # Convert to Julian Day at midnight UTC
            midnight_local = date.replace(hour=0, minute=0, second=0, microsecond=0)
            midnight_utc = midnight_local - timedelta(hours=timezone_offset)

            jd = swe.julday(
                midnight_utc.year,
                midnight_utc.month,
                midnight_utc.day,
                midnight_utc.hour + midnight_utc.minute / 60.0
            )

            # Geographic position: (longitude, latitude, altitude)
            geopos = (longitude, latitude, 0)

            # Calculate sunrise
            # rsmi flags: SE_CALC_RISE = 1, SE_BIT_DISC_CENTER = 256
            sunrise_result = swe.rise_trans(
                jd,
                swe.SUN,
                geopos=geopos,
                rsmi=swe.CALC_RISE | swe.BIT_DISC_CENTER
            )

            # Calculate sunset
            # rsmi flags: SE_CALC_SET = 2, SE_BIT_DISC_CENTER = 256
            sunset_result = swe.rise_trans(
                jd,
                swe.SUN,
                geopos=geopos,
                rsmi=swe.CALC_SET | swe.BIT_DISC_CENTER
            )

            # Extract Julian Days
            sunrise_jd = sunrise_result[1][0]
            sunset_jd = sunset_result[1][0]

            # Convert back to datetime
            sunrise_dt = self._jd_to_datetime(sunrise_jd, timezone_offset)
            sunset_dt = self._jd_to_datetime(sunset_jd, timezone_offset)

            # Calculate noon and durations
            day_duration = (sunset_jd - sunrise_jd) * 24 * 3600  # seconds
            night_duration = 24 * 3600 - day_duration
            noon_dt = sunrise_dt + timedelta(seconds=day_duration / 2)

            return SunTimes(
                sunrise=sunrise_dt,
                sunset=sunset_dt,
                noon=noon_dt,
                day_duration_seconds=day_duration,
                night_duration_seconds=night_duration
            )

        except Exception as e:
            logger.warning(f"Swiss Ephemeris calculation failed, using fallback: {e}")
            return self._calculate_simplified(date, latitude, longitude, timezone_offset)

    def _calculate_simplified(
        self,
        date: datetime,
        latitude: float,
        longitude: float,
        timezone_offset: float
    ) -> SunTimes:
        """
        Calculate using simplified astronomical formulas.

        Accuracy: Within 5-10 minutes of actual sunrise/sunset.
        Based on NOAA solar calculator formulas.
        """
        # Day of year (1-366)
        day_of_year = date.timetuple().tm_yday

        # Solar declination (simplified)
        # Declination varies from +23.45° (summer solstice) to -23.45° (winter solstice)
        declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))

        # Convert to radians
        lat_rad = math.radians(latitude)
        dec_rad = math.radians(declination)

        # Hour angle at sunrise/sunset
        # cos(HA) = -tan(lat) * tan(dec)
        cos_hour_angle = -math.tan(lat_rad) * math.tan(dec_rad)

        # Handle polar regions
        if cos_hour_angle > 1:
            # Polar night - sun doesn't rise
            # Use civil twilight approximation
            sunrise_hour = 9.0
            sunset_hour = 15.0
        elif cos_hour_angle < -1:
            # Midnight sun - sun doesn't set
            sunrise_hour = 3.0
            sunset_hour = 21.0
        else:
            hour_angle = math.degrees(math.acos(cos_hour_angle))

            # Equation of time correction (simplified)
            b = 2 * math.pi * (day_of_year - 81) / 365
            eot = 9.87 * math.sin(2 * b) - 7.53 * math.cos(b) - 1.5 * math.sin(b)
            eot_hours = eot / 60

            # Local solar noon (without timezone)
            # Longitude correction: 4 minutes per degree from standard meridian
            # Standard meridian = timezone_offset * 15
            standard_meridian = timezone_offset * 15
            longitude_correction = (longitude - standard_meridian) * 4 / 60  # hours

            solar_noon = 12.0 - longitude_correction - eot_hours

            # Sunrise and sunset
            sunrise_hour = solar_noon - hour_angle / 15
            sunset_hour = solar_noon + hour_angle / 15

        # Create datetime objects
        base_date = date.replace(hour=0, minute=0, second=0, microsecond=0)

        sunrise_minutes = sunrise_hour * 60
        sunset_minutes = sunset_hour * 60

        sunrise_dt = base_date + timedelta(minutes=sunrise_minutes)
        sunset_dt = base_date + timedelta(minutes=sunset_minutes)

        # Ensure times are valid
        if sunrise_dt < base_date:
            sunrise_dt = base_date + timedelta(hours=6)  # Fallback
        if sunset_dt > base_date + timedelta(hours=23, minutes=59):
            sunset_dt = base_date + timedelta(hours=18)  # Fallback

        # Calculate durations
        day_duration = (sunset_dt - sunrise_dt).total_seconds()
        night_duration = 24 * 3600 - day_duration
        noon_dt = sunrise_dt + timedelta(seconds=day_duration / 2)

        return SunTimes(
            sunrise=sunrise_dt,
            sunset=sunset_dt,
            noon=noon_dt,
            day_duration_seconds=day_duration,
            night_duration_seconds=night_duration
        )

    def _jd_to_datetime(self, jd: float, timezone_offset: float) -> datetime:
        """Convert Julian Day to datetime with timezone offset."""
        # Use Swiss Ephemeris for conversion if available
        if self._use_swisseph:
            try:
                result = swe.revjul(jd)
                year, month, day, hour_float = result

                hours = int(hour_float)
                minutes = int((hour_float - hours) * 60)
                seconds = int(((hour_float - hours) * 60 - minutes) * 60)

                utc_dt = datetime(int(year), int(month), int(day), hours, minutes, seconds)
                local_dt = utc_dt + timedelta(hours=timezone_offset)

                return local_dt
            except Exception:
                pass

        # Fallback: manual Julian Day conversion
        # JD 2451545.0 = January 1, 2000, 12:00 TT
        jd_diff = jd - 2451545.0
        days_since_epoch = jd_diff

        epoch = datetime(2000, 1, 1, 12, 0, 0)
        utc_dt = epoch + timedelta(days=days_since_epoch)
        local_dt = utc_dt + timedelta(hours=timezone_offset)

        return local_dt

    def get_day_muhurtas(
        self,
        sunrise: datetime,
        sunset: datetime,
        count: int = 15
    ) -> list:
        """
        Divide day into muhurtas (traditionally 15 for day, 15 for night).

        Args:
            sunrise: Sunrise datetime
            sunset: Sunset datetime
            count: Number of muhurtas (default 15)

        Returns:
            List of (start, end) datetime tuples
        """
        day_duration = (sunset - sunrise).total_seconds()
        muhurta_duration = day_duration / count

        muhurtas = []
        for i in range(count):
            start = sunrise + timedelta(seconds=muhurta_duration * i)
            end = sunrise + timedelta(seconds=muhurta_duration * (i + 1))
            muhurtas.append((start, end))

        return muhurtas

    def get_abhijit_muhurta(
        self,
        sunrise: datetime,
        sunset: datetime
    ) -> Tuple[datetime, datetime]:
        """
        Get Abhijit Muhurta (8th muhurta of the day - most auspicious).

        The day is divided into 15 muhurtas. Abhijit is the 8th one,
        occurring around local noon.

        Returns:
            Tuple of (start, end) datetimes
        """
        muhurtas = self.get_day_muhurtas(sunrise, sunset, 15)

        if len(muhurtas) >= 8:
            return muhurtas[7]  # 8th muhurta (0-indexed as 7)
        else:
            # Fallback: approximate noon ± 24 minutes
            noon = sunrise + (sunset - sunrise) / 2
            return (noon - timedelta(minutes=24), noon + timedelta(minutes=24))


# Singleton instance
_calculator: Optional[SunTimesCalculator] = None


def get_sun_times_calculator() -> SunTimesCalculator:
    """Get singleton SunTimesCalculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = SunTimesCalculator()
    return _calculator


def calculate_sun_times(
    date: Union[datetime, date_type],
    latitude: float,
    longitude: float,
    timezone_offset: float = 0.0
) -> SunTimes:
    """
    Convenience function to calculate sun times.

    Args:
        date: Date for calculation
        latitude: Latitude in degrees
        longitude: Longitude in degrees
        timezone_offset: Timezone offset from UTC in hours

    Returns:
        SunTimes object
    """
    return get_sun_times_calculator().calculate(date, latitude, longitude, timezone_offset)
