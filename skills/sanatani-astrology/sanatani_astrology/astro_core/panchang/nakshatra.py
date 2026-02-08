"""
Nakshatra Calculator - Lunar Mansion Calculation

Nakshatra is the lunar mansion where the Moon is located.
There are 27 nakshatras, each spanning 13°20' (360/27 degrees).
Each nakshatra has 4 padas (quarters) of 3°20' each.

Formula: Nakshatra = (Moon° * 27 / 360)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass

from .constants import (
    NAKSHATRA_NAMES,
    NAKSHATRA_LORDS,
    NAKSHATRA_FAVORABILITY,
    GANDANTA_NAKSHATRAS,
    GANDANTA_NAKSHATRAS_START,
    DEGREES_PER_NAKSHATRA,
    DEGREES_PER_PADA,
    MOON_MEAN_DAILY_MOTION,
)

logger = logging.getLogger(__name__)


@dataclass
class NakshatraInfo:
    """Complete information about a nakshatra."""
    index: int               # 0-26
    name: str                # Nakshatra name
    lord: str                # Ruling planet
    pada: int                # 1-4 (quarter)
    balance_percent: float   # Percentage remaining (0-100)
    end_time: Optional[datetime]  # When Moon exits this nakshatra
    is_gandanta: bool        # At water-fire junction
    gandanta_type: Optional[str]  # "start" or "end" if gandanta
    favorability: float      # 0.0-1.0


class NakshatraCalculator:
    """
    Calculator for Nakshatra (Lunar Mansion).

    The Moon travels through 27 nakshatras, each associated with
    specific qualities and a ruling planet (lord).
    """

    def calculate(
        self,
        moon_longitude: float,
        moon_speed: Optional[float] = None,
        calculation_time: Optional[datetime] = None,
        timezone_offset: float = 0.0,
    ) -> NakshatraInfo:
        """
        Calculate nakshatra from Moon longitude.

        Args:
            moon_longitude: Moon's longitude in degrees (0-360)
            moon_speed: Moon's daily motion in degrees (optional, for end time)
            calculation_time: Time of calculation (optional, for end time)
            timezone_offset: Timezone offset from UTC in hours (for iterative calc)

        Returns:
            NakshatraInfo with complete nakshatra details
        """
        # Normalize longitude
        moon_longitude = moon_longitude % 360

        # Calculate nakshatra index (0-26)
        nakshatra_position = moon_longitude / DEGREES_PER_NAKSHATRA
        nakshatra_index = int(nakshatra_position)

        if nakshatra_index >= 27:
            nakshatra_index = 26

        # Calculate position within nakshatra
        position_in_nakshatra = (nakshatra_position - nakshatra_index) * DEGREES_PER_NAKSHATRA

        # Calculate pada (1-4)
        pada = int(position_in_nakshatra / DEGREES_PER_PADA) + 1
        if pada > 4:
            pada = 4

        # Calculate balance (percentage remaining in current nakshatra)
        remaining_degrees = DEGREES_PER_NAKSHATRA - position_in_nakshatra
        balance_percent = (remaining_degrees / DEGREES_PER_NAKSHATRA) * 100

        # Get nakshatra details
        name = NAKSHATRA_NAMES[nakshatra_index]
        lord = NAKSHATRA_LORDS[nakshatra_index]
        favorability = NAKSHATRA_FAVORABILITY.get(nakshatra_index, 0.5)

        # Check for Gandanta (junction points)
        is_gandanta, gandanta_type = self._check_gandanta(moon_longitude, nakshatra_index)

        # Calculate end time if speed is provided
        end_time = None
        if moon_speed is not None and calculation_time is not None:
            end_time = self._calculate_end_time(
                remaining_degrees,
                moon_speed,
                calculation_time,
                moon_longitude,
                timezone_offset,
            )

        return NakshatraInfo(
            index=nakshatra_index,
            name=name,
            lord=lord,
            pada=pada,
            balance_percent=round(balance_percent, 2),
            end_time=end_time,
            is_gandanta=is_gandanta,
            gandanta_type=gandanta_type,
            favorability=favorability
        )

    def _check_gandanta(
        self,
        moon_longitude: float,
        nakshatra_index: int
    ) -> tuple:
        """
        Check if Moon is in Gandanta zone.

        Gandanta are junction points between water and fire signs:
        - Ashlesha/Magha (Cancer/Leo)
        - Jyeshtha/Mula (Scorpio/Sagittarius)
        - Revati/Ashwini (Pisces/Aries)

        The zone extends 3°20' (1 pada) on each side of the junction.

        Returns:
            Tuple of (is_gandanta, gandanta_type)
        """
        # Check end gandanta nakshatras (last pada)
        if nakshatra_index in GANDANTA_NAKSHATRAS:
            # Check if in last pada (last 3°20' of nakshatra)
            position = (moon_longitude % DEGREES_PER_NAKSHATRA)
            if position >= (DEGREES_PER_NAKSHATRA - DEGREES_PER_PADA):
                return True, "end"

        # Check start gandanta nakshatras (first pada)
        if nakshatra_index in GANDANTA_NAKSHATRAS_START:
            # Check if in first pada (first 3°20' of nakshatra)
            position = (moon_longitude % DEGREES_PER_NAKSHATRA)
            if position < DEGREES_PER_PADA:
                return True, "start"

        return False, None

    def _calculate_end_time(
        self,
        remaining_degrees: float,
        moon_speed: float,
        calculation_time: datetime,
        moon_longitude: float = None,
        timezone_offset: float = 0.0,
    ) -> datetime:
        """
        Calculate when Moon exits current nakshatra using iterative refinement.

        Args:
            remaining_degrees: Degrees remaining in current nakshatra
            moon_speed: Moon's daily motion in degrees
            calculation_time: Current time
            moon_longitude: Current Moon longitude (optional, for iterative calc)
            timezone_offset: Timezone offset from UTC in hours

        Returns:
            Datetime when nakshatra changes
        """
        # Try iterative calculation with Swiss Ephemeris for precision
        try:
            import swisseph as swe

            if moon_longitude is not None:
                # Calculate next nakshatra boundary
                current_nakshatra = int(moon_longitude / DEGREES_PER_NAKSHATRA)
                target_longitude = (current_nakshatra + 1) * DEGREES_PER_NAKSHATRA

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
                    current_lon = moon_pos[0][0]
                    current_speed = moon_pos[0][3]

                    error = (target_longitude - current_lon) % 360
                    if error > 180:
                        error -= 360

                    if abs(error) < 0.0001:  # High precision
                        break

                    jd += error / current_speed

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
        if moon_speed <= 0:
            moon_speed = MOON_MEAN_DAILY_MOTION

        days_remaining = remaining_degrees / moon_speed
        return calculation_time + timedelta(days=days_remaining)

    def get_nakshatra_at_longitude(self, longitude: float) -> NakshatraInfo:
        """
        Get nakshatra for any longitude (not just Moon).

        Useful for checking planetary nakshatras.

        Args:
            longitude: Longitude in degrees (0-360)

        Returns:
            NakshatraInfo (without end_time)
        """
        return self.calculate(longitude)

    def find_nakshatra_start(
        self,
        target_nakshatra: int,
        moon_longitude: float,
        moon_speed: float,
        calculation_time: datetime
    ) -> Optional[datetime]:
        """
        Find when Moon enters a specific nakshatra.

        Args:
            target_nakshatra: Nakshatra index (0-26)
            moon_longitude: Current Moon longitude
            moon_speed: Moon's daily motion
            calculation_time: Current time

        Returns:
            Datetime when Moon enters the nakshatra
        """
        # Current nakshatra
        current_nakshatra = int(moon_longitude / DEGREES_PER_NAKSHATRA)

        # Target longitude (start of target nakshatra)
        target_longitude = target_nakshatra * DEGREES_PER_NAKSHATRA

        # Degrees until target
        degrees_needed = (target_longitude - moon_longitude) % 360

        if moon_speed <= 0:
            moon_speed = MOON_MEAN_DAILY_MOTION

        # Days until target
        days_until = degrees_needed / moon_speed

        return calculation_time + timedelta(days=days_until)

    def get_lord_for_nakshatra(self, nakshatra_index: int) -> str:
        """Get the ruling planet for a nakshatra."""
        if 0 <= nakshatra_index < 27:
            return NAKSHATRA_LORDS[nakshatra_index]
        return "Unknown"

    def get_deity_for_nakshatra(self, nakshatra_index: int) -> str:
        """Get the presiding deity for a nakshatra."""
        NAKSHATRA_DEITIES = [
            "Ashwini Kumaras",   # Ashwini
            "Yama",             # Bharani
            "Agni",             # Krittika
            "Brahma",           # Rohini
            "Soma",             # Mrigashira
            "Rudra",            # Ardra
            "Aditi",            # Punarvasu
            "Brihaspati",       # Pushya
            "Sarpa",            # Ashlesha
            "Pitris",           # Magha
            "Bhaga",            # Purva Phalguni
            "Aryaman",          # Uttara Phalguni
            "Savitar",          # Hasta
            "Vishwakarma",      # Chitra
            "Vayu",             # Swati
            "Indragni",         # Vishakha
            "Mitra",            # Anuradha
            "Indra",            # Jyeshtha
            "Nirriti",          # Mula
            "Apah",             # Purva Ashadha
            "Vishve Devas",     # Uttara Ashadha
            "Vishnu",           # Shravana
            "Vasus",            # Dhanishta
            "Varuna",           # Shatabhisha
            "Aja Ekapad",       # Purva Bhadrapada
            "Ahir Budhnya",     # Uttara Bhadrapada
            "Pushan",           # Revati
        ]
        if 0 <= nakshatra_index < 27:
            return NAKSHATRA_DEITIES[nakshatra_index]
        return "Unknown"


# Singleton instance
_calculator: Optional[NakshatraCalculator] = None


def get_nakshatra_calculator() -> NakshatraCalculator:
    """Get singleton NakshatraCalculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = NakshatraCalculator()
    return _calculator


def calculate_nakshatra(
    moon_longitude: float,
    moon_speed: Optional[float] = None,
    calculation_time: Optional[datetime] = None
) -> NakshatraInfo:
    """
    Convenience function to calculate nakshatra.

    Args:
        moon_longitude: Moon's longitude in degrees (0-360)
        moon_speed: Moon's daily motion (optional)
        calculation_time: Time of calculation (optional)

    Returns:
        NakshatraInfo object
    """
    return get_nakshatra_calculator().calculate(
        moon_longitude,
        moon_speed,
        calculation_time
    )
