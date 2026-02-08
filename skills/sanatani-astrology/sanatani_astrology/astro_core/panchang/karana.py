"""
Karana Calculator - Half-Tithi Calculation

Karana is half of a tithi. There are 60 karanas in a lunar month.
11 karanas total: 7 movable (repeat 8 times) + 4 fixed (occur once).

The 7 movable karanas cycle through positions 2-57.
The 4 fixed karanas occur at positions 1 (Kimstughna), 58-60 (Shakuni, Chatushpada, Naga).
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

from .constants import (
    MOVABLE_KARANA_NAMES,
    FIXED_KARANA_NAMES,
    ALL_KARANA_NAMES,
    KARANA_FAVORABILITY,
    VISHTI_KARANA_INDEX,
    DEGREES_PER_TITHI,
    MOON_MEAN_DAILY_MOTION,
    SUN_MEAN_DAILY_MOTION,
)

logger = logging.getLogger(__name__)


@dataclass
class KaranaInfo:
    """Complete information about a karana."""
    index: int               # 0-10 (karana type index)
    name: str                # Karana name
    position: int            # Position in lunar month (1-60)
    is_first_half: bool      # First or second half of tithi
    balance_percent: float   # Percentage remaining (0-100)
    end_time: Optional[datetime]  # When this karana ends
    is_vishti: bool          # Bhadra karana (inauspicious)
    is_fixed: bool           # One of 4 fixed karanas
    favorability: float      # 0.0-1.0


class KaranaCalculator:
    """
    Calculator for Karana (Half-Tithi).

    Each tithi has two karanas. The 7 movable karanas (Bava to Vishti)
    repeat in cycle, while 4 fixed karanas occur at specific positions.
    """

    def calculate(
        self,
        sun_longitude: float,
        moon_longitude: float,
        moon_speed: Optional[float] = None,
        sun_speed: Optional[float] = None,
        calculation_time: Optional[datetime] = None,
        timezone_offset: float = 0.0,
    ) -> KaranaInfo:
        """
        Calculate karana from Sun and Moon longitudes.

        Args:
            sun_longitude: Sun's longitude in degrees (0-360)
            moon_longitude: Moon's longitude in degrees (0-360)
            moon_speed: Moon's daily motion (optional, for end time)
            sun_speed: Sun's daily motion (optional, for end time)
            calculation_time: Time of calculation (optional)
            timezone_offset: Timezone offset from UTC in hours (for iterative calc)

        Returns:
            KaranaInfo with complete karana details
        """
        # Calculate Moon-Sun elongation
        elongation = (moon_longitude - sun_longitude) % 360

        # Calculate tithi number (1-30) and position within tithi
        tithi_number = int(elongation / DEGREES_PER_TITHI) + 1
        if tithi_number > 30:
            tithi_number = 30

        position_in_tithi = elongation % DEGREES_PER_TITHI
        tithi_balance = (position_in_tithi / DEGREES_PER_TITHI) * 100

        # Determine if first or second half of tithi
        is_first_half = tithi_balance < 50

        # Calculate karana position (1-60)
        if is_first_half:
            karana_position = (tithi_number - 1) * 2 + 1
        else:
            karana_position = (tithi_number - 1) * 2 + 2

        # Calculate balance within karana (each karana is 6 degrees)
        karana_degrees = DEGREES_PER_TITHI / 2  # 6 degrees
        position_in_karana = position_in_tithi % karana_degrees
        balance_percent = ((karana_degrees - position_in_karana) / karana_degrees) * 100

        # Determine karana index and name
        karana_index, karana_name, is_fixed = self._get_karana_details(karana_position)

        # Check for Vishti (Bhadra)
        is_vishti = karana_index == VISHTI_KARANA_INDEX

        # Get favorability
        favorability = KARANA_FAVORABILITY.get(karana_index, 0.5)

        # Calculate end time
        end_time = None
        if moon_speed is not None and calculation_time is not None:
            remaining_degrees = karana_degrees - position_in_karana
            end_time = self._calculate_end_time(
                remaining_degrees,
                moon_speed,
                sun_speed or SUN_MEAN_DAILY_MOTION,
                calculation_time,
                sun_longitude,
                moon_longitude,
                timezone_offset,
            )

        return KaranaInfo(
            index=karana_index,
            name=karana_name,
            position=karana_position,
            is_first_half=is_first_half,
            balance_percent=round(balance_percent, 2),
            end_time=end_time,
            is_vishti=is_vishti,
            is_fixed=is_fixed,
            favorability=favorability
        )

    def _get_karana_details(self, position: int) -> tuple:
        """
        Get karana index, name, and fixed status from position.

        Karana positions:
        - Position 1: Kimstughna (fixed)
        - Positions 2-57: 7 movable karanas cycling (Bava to Vishti)
        - Position 58: Shakuni (fixed)
        - Position 59: Chatushpada (fixed)
        - Position 60: Naga (fixed)

        Args:
            position: Karana position (1-60)

        Returns:
            Tuple of (karana_index, karana_name, is_fixed)
        """
        if position == 1:
            # Kimstughna (fixed) - occurs at start of Shukla Pratipada
            return 10, FIXED_KARANA_NAMES[3], True  # Kimstughna

        elif 2 <= position <= 57:
            # Movable karanas (cycle through 7)
            cycle_position = (position - 2) % 7
            return cycle_position, MOVABLE_KARANA_NAMES[cycle_position], False

        elif position == 58:
            return 7, FIXED_KARANA_NAMES[0], True  # Shakuni

        elif position == 59:
            return 8, FIXED_KARANA_NAMES[1], True  # Chatushpada

        elif position == 60:
            return 9, FIXED_KARANA_NAMES[2], True  # Naga

        else:
            # Fallback
            return 0, "Unknown", False

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
        Calculate when the current karana ends using iterative refinement.

        Args:
            remaining_degrees: Degrees remaining in current karana
            moon_speed: Moon's daily motion
            sun_speed: Sun's daily motion
            calculation_time: Current time
            sun_longitude: Current Sun longitude (optional, for iterative calc)
            moon_longitude: Current Moon longitude (optional, for iterative calc)
            timezone_offset: Timezone offset from UTC in hours

        Returns:
            Datetime when karana ends
        """
        # Karana is 6 degrees (half tithi)
        karana_degrees = DEGREES_PER_TITHI / 2

        # Try iterative calculation with Swiss Ephemeris for precision
        try:
            import swisseph as swe

            if moon_longitude is not None and sun_longitude is not None:
                # Calculate current elongation and karana position
                elongation = (moon_longitude - sun_longitude) % 360
                current_karana = int(elongation / karana_degrees)
                target_elongation = (current_karana + 1) * karana_degrees

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

                    current_elongation = (moon_pos[0][0] - sun_pos[0][0]) % 360
                    error = (target_elongation - current_elongation) % 360
                    if error > 180:
                        error -= 360

                    if abs(error) < 0.0001:  # High precision
                        break

                    relative_speed = moon_pos[0][3] - sun_pos[0][3]
                    jd += error / relative_speed

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
        relative_speed = moon_speed - sun_speed
        if relative_speed <= 0:
            relative_speed = MOON_MEAN_DAILY_MOTION - SUN_MEAN_DAILY_MOTION

        days_remaining = remaining_degrees / relative_speed
        return calculation_time + timedelta(days=days_remaining)

    def get_vishti_times(
        self,
        sun_longitude: float,
        moon_longitude: float,
        moon_speed: float,
        sun_speed: float,
        calculation_time: datetime,
        days_ahead: int = 7
    ) -> list:
        """
        Find upcoming Vishti (Bhadra) karana times.

        Vishti is highly inauspicious and should be avoided for
        important activities.

        Args:
            sun_longitude: Current Sun longitude
            moon_longitude: Current Moon longitude
            moon_speed: Moon's daily motion
            sun_speed: Sun's daily motion
            calculation_time: Current time
            days_ahead: Number of days to search

        Returns:
            List of (start_time, end_time) tuples for Vishti periods
        """
        vishti_periods = []

        # Vishti occurs in positions 7, 14, 21, 28, 35, 42, 49, 56
        # (7th karana in each cycle of 7, starting from position 2)
        vishti_positions = [7, 14, 21, 28, 35, 42, 49, 56]

        # Current elongation
        current_elongation = (moon_longitude - sun_longitude) % 360

        # Current karana position
        tithi_number = int(current_elongation / DEGREES_PER_TITHI) + 1
        position_in_tithi = current_elongation % DEGREES_PER_TITHI
        is_first_half = position_in_tithi < (DEGREES_PER_TITHI / 2)

        if is_first_half:
            current_position = (tithi_number - 1) * 2 + 1
        else:
            current_position = (tithi_number - 1) * 2 + 2

        # Find next Vishti positions
        for vishti_pos in vishti_positions:
            if vishti_pos >= current_position:
                # Calculate when this Vishti starts
                positions_ahead = vishti_pos - current_position

                # Each position is 6 degrees of Moon-Sun elongation
                degrees_ahead = positions_ahead * 6 - position_in_tithi % 6

                relative_speed = moon_speed - sun_speed
                if relative_speed <= 0:
                    relative_speed = MOON_MEAN_DAILY_MOTION - SUN_MEAN_DAILY_MOTION

                days_until = degrees_ahead / relative_speed

                if days_until <= days_ahead:
                    start_time = calculation_time + timedelta(days=days_until)
                    end_time = start_time + timedelta(days=6 / relative_speed)
                    vishti_periods.append((start_time, end_time))

        return vishti_periods


# Singleton instance
_calculator: Optional[KaranaCalculator] = None


def get_karana_calculator() -> KaranaCalculator:
    """Get singleton KaranaCalculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = KaranaCalculator()
    return _calculator


def calculate_karana(
    sun_longitude: float,
    moon_longitude: float,
    moon_speed: Optional[float] = None,
    sun_speed: Optional[float] = None,
    calculation_time: Optional[datetime] = None
) -> KaranaInfo:
    """
    Convenience function to calculate karana.

    Args:
        sun_longitude: Sun's longitude in degrees
        moon_longitude: Moon's longitude in degrees
        moon_speed: Moon's daily motion (optional)
        sun_speed: Sun's daily motion (optional)
        calculation_time: Time of calculation (optional)

    Returns:
        KaranaInfo object
    """
    return get_karana_calculator().calculate(
        sun_longitude,
        moon_longitude,
        moon_speed,
        sun_speed,
        calculation_time
    )
