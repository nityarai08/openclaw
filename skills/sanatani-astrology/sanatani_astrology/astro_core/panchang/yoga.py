"""
Yoga Calculator - Sun + Moon Combination

Yoga is determined by the sum of Sun and Moon longitudes.
There are 27 yogas, each spanning 13°20' (360/27 degrees).

Formula: Yoga = ((Sun° + Moon°) % 360) / 13.333
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from .constants import (
    YOGA_NAMES,
    YOGA_FAVORABILITY,
    CRITICAL_AVOID_YOGAS,
    DEGREES_PER_YOGA,
    MOON_MEAN_DAILY_MOTION,
    SUN_MEAN_DAILY_MOTION,
)

logger = logging.getLogger(__name__)


@dataclass
class YogaInfo:
    """Complete information about a yoga."""
    index: int               # 0-26
    name: str                # Yoga name
    balance_percent: float   # Percentage remaining (0-100)
    end_time: Optional[datetime]  # When this yoga ends
    is_auspicious: bool      # Generally favorable
    is_critical_avoid: bool  # Vyatipata, Vaidhriti
    favorability: float      # 0.0-1.0


class YogaCalculator:
    """
    Calculator for Yoga (Sun + Moon combination).

    Yoga represents the combined influence of Sun and Moon.
    Unlike tithi (difference), yoga uses the sum of their longitudes.
    """

    def calculate(
        self,
        sun_longitude: float,
        moon_longitude: float,
        moon_speed: Optional[float] = None,
        sun_speed: Optional[float] = None,
        calculation_time: Optional[datetime] = None,
        timezone_offset: float = 0.0,
    ) -> YogaInfo:
        """
        Calculate yoga from Sun and Moon longitudes.

        Args:
            sun_longitude: Sun's longitude in degrees (0-360)
            moon_longitude: Moon's longitude in degrees (0-360)
            moon_speed: Moon's daily motion in degrees (optional)
            sun_speed: Sun's daily motion in degrees (optional)
            calculation_time: Time of calculation (optional)
            timezone_offset: Timezone offset from UTC in hours (for iterative calc)

        Returns:
            YogaInfo with complete yoga details
        """
        # Calculate sum of Sun and Moon longitudes
        yoga_sum = (sun_longitude + moon_longitude) % 360

        # Calculate yoga index (0-26)
        yoga_position = yoga_sum / DEGREES_PER_YOGA
        yoga_index = int(yoga_position)

        if yoga_index >= 27:
            yoga_index = 26

        # Calculate position within yoga
        position_in_yoga = (yoga_position - yoga_index) * DEGREES_PER_YOGA

        # Calculate balance (percentage remaining)
        remaining_degrees = DEGREES_PER_YOGA - position_in_yoga
        balance_percent = (remaining_degrees / DEGREES_PER_YOGA) * 100

        # Get yoga details
        name = YOGA_NAMES[yoga_index]
        favorability = YOGA_FAVORABILITY.get(yoga_index, 0.5)

        # Check if auspicious
        is_auspicious = favorability >= 0.6
        is_critical_avoid = yoga_index in CRITICAL_AVOID_YOGAS

        # Calculate end time if speeds provided
        end_time = None
        if moon_speed is not None and calculation_time is not None:
            end_time = self._calculate_end_time(
                remaining_degrees,
                moon_speed,
                sun_speed or SUN_MEAN_DAILY_MOTION,
                calculation_time,
                sun_longitude,
                moon_longitude,
                timezone_offset,
            )

        return YogaInfo(
            index=yoga_index,
            name=name,
            balance_percent=round(balance_percent, 2),
            end_time=end_time,
            is_auspicious=is_auspicious,
            is_critical_avoid=is_critical_avoid,
            favorability=favorability
        )

    def _calculate_end_time(
        self,
        remaining_degrees: float,
        moon_speed: float,
        sun_speed: float,
        calculation_time: datetime,
        sun_longitude: float = None,
        moon_longitude: float = None,
        timezone_offset: float = 0.0,
    ) -> datetime:
        """
        Calculate when the current yoga ends using iterative refinement.

        Yoga changes when (Sun + Moon) crosses the next 13.333° boundary.
        Both Sun and Moon contribute to the motion.

        Args:
            remaining_degrees: Degrees remaining in current yoga
            moon_speed: Moon's daily motion in degrees
            sun_speed: Sun's daily motion in degrees
            calculation_time: Current time
            sun_longitude: Current Sun longitude (optional, for iterative calc)
            moon_longitude: Current Moon longitude (optional, for iterative calc)
            timezone_offset: Timezone offset from UTC in hours

        Returns:
            Datetime when yoga ends
        """
        # Try iterative calculation with Swiss Ephemeris for precision
        try:
            import swisseph as swe

            if sun_longitude is not None and moon_longitude is not None:
                # Calculate current yoga and target sum
                yoga_sum = (sun_longitude + moon_longitude) % 360
                current_yoga = int(yoga_sum / DEGREES_PER_YOGA)
                target_sum = (current_yoga + 1) * DEGREES_PER_YOGA

                # Convert to Julian Day (UTC)
                utc_time = calculation_time - timedelta(hours=timezone_offset)
                jd = swe.julday(
                    utc_time.year, utc_time.month, utc_time.day,
                    utc_time.hour + utc_time.minute / 60.0 + utc_time.second / 3600.0
                )

                # Set Lahiri ayanamsa
                swe.set_sid_mode(swe.SIDM_LAHIRI)

                # Newton-Raphson iteration
                for _ in range(10):
                    moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL | swe.FLG_SPEED)
                    sun_pos = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL | swe.FLG_SPEED)

                    current_sum = (moon_pos[0][0] + sun_pos[0][0]) % 360
                    combined_speed = moon_pos[0][3] + sun_pos[0][3]

                    error = (target_sum - current_sum) % 360
                    if error > 180:
                        error -= 360

                    if abs(error) < 0.0001:  # High precision
                        break

                    jd += error / combined_speed

                # Convert JD back to datetime
                year, month, day, hour_frac = swe.revjul(jd)
                hours = int(hour_frac)
                remaining_frac = (hour_frac - hours) * 60
                minutes = int(remaining_frac)
                seconds = int((remaining_frac - minutes) * 60)

                end_utc = datetime(year, month, day, hours, minutes, seconds)
                return end_utc + timedelta(hours=timezone_offset)

        except (ImportError, Exception) as e:
            logger.debug(f"Iterative calc failed, using linear: {e}")

        # Fallback: Linear calculation
        combined_speed = moon_speed + sun_speed
        if combined_speed <= 0:
            combined_speed = MOON_MEAN_DAILY_MOTION + SUN_MEAN_DAILY_MOTION

        days_remaining = remaining_degrees / combined_speed
        return calculation_time + timedelta(days=days_remaining)

    def find_yoga_start(
        self,
        target_yoga: int,
        sun_longitude: float,
        moon_longitude: float,
        moon_speed: float,
        sun_speed: float,
        calculation_time: datetime
    ) -> Optional[datetime]:
        """
        Find when a specific yoga starts.

        Args:
            target_yoga: Yoga index (0-26)
            sun_longitude: Current Sun longitude
            moon_longitude: Current Moon longitude
            moon_speed: Moon's daily motion
            sun_speed: Sun's daily motion
            calculation_time: Current time

        Returns:
            Datetime when the yoga starts
        """
        # Current yoga sum
        current_sum = (sun_longitude + moon_longitude) % 360

        # Target sum (start of target yoga)
        target_sum = target_yoga * DEGREES_PER_YOGA

        # Degrees until target
        degrees_needed = (target_sum - current_sum) % 360

        # Combined speed
        combined_speed = moon_speed + sun_speed
        if combined_speed <= 0:
            combined_speed = MOON_MEAN_DAILY_MOTION + SUN_MEAN_DAILY_MOTION

        # Days until target
        days_until = degrees_needed / combined_speed

        return calculation_time + timedelta(days=days_until)


# Singleton instance
_calculator: Optional[YogaCalculator] = None


def get_yoga_calculator() -> YogaCalculator:
    """Get singleton YogaCalculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = YogaCalculator()
    return _calculator


def calculate_yoga(
    sun_longitude: float,
    moon_longitude: float,
    moon_speed: Optional[float] = None,
    sun_speed: Optional[float] = None,
    calculation_time: Optional[datetime] = None
) -> YogaInfo:
    """
    Convenience function to calculate yoga.

    Args:
        sun_longitude: Sun's longitude in degrees
        moon_longitude: Moon's longitude in degrees
        moon_speed: Moon's daily motion (optional)
        sun_speed: Sun's daily motion (optional)
        calculation_time: Time of calculation (optional)

    Returns:
        YogaInfo object
    """
    return get_yoga_calculator().calculate(
        sun_longitude,
        moon_longitude,
        moon_speed,
        sun_speed,
        calculation_time
    )
