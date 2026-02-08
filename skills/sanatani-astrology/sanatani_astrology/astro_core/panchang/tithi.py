"""
Tithi Calculator - Lunar Day Calculation

Tithi is the angular distance between Sun and Moon divided by 12°.
There are 30 tithis in a lunar month (15 in Shukla + 15 in Krishna paksha).

Formula: Tithi = ((Moon° - Sun°) % 360) / 12
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass

from .constants import (
    TITHI_NAMES,
    TITHI_FAVORABILITY,
    DEGREES_PER_TITHI,
    RIKTA_TITHIS,
    MOON_MEAN_DAILY_MOTION,
    SUN_MEAN_DAILY_MOTION,
)

logger = logging.getLogger(__name__)


@dataclass
class TithiInfo:
    """Complete information about a tithi."""
    number: int              # 1-30
    name: str                # Full name with paksha
    paksha: str              # "Shukla" or "Krishna"
    paksha_tithi: int        # 1-15 within the paksha
    balance_percent: float   # Percentage remaining (0-100)
    end_time: Optional[datetime]  # When this tithi ends
    is_purnima: bool         # Full moon
    is_amavasya: bool        # New moon
    is_rikta: bool           # Empty tithi (inauspicious for beginnings)
    favorability: float      # 0.0-1.0


class TithiCalculator:
    """
    Calculator for Tithi (Lunar Day).

    Tithi represents the phase of the Moon relative to the Sun.
    Each tithi spans 12° of Moon-Sun angular separation.
    """

    def calculate(
        self,
        sun_longitude: float,
        moon_longitude: float,
        moon_speed: Optional[float] = None,
        sun_speed: Optional[float] = None,
        calculation_time: Optional[datetime] = None,
        timezone_offset: float = 0.0,
    ) -> TithiInfo:
        """
        Calculate tithi from Sun and Moon longitudes.

        Args:
            sun_longitude: Sun's longitude in degrees (0-360)
            moon_longitude: Moon's longitude in degrees (0-360)
            moon_speed: Moon's daily motion in degrees (optional, for end time)
            sun_speed: Sun's daily motion in degrees (optional, for end time)
            calculation_time: Time of calculation (optional, for end time)
            timezone_offset: Timezone offset from UTC in hours (for iterative calc)

        Returns:
            TithiInfo with complete tithi details
        """
        # Calculate Moon-Sun elongation
        elongation = (moon_longitude - sun_longitude) % 360

        # Calculate tithi number (1-30)
        tithi_number = int(elongation / DEGREES_PER_TITHI) + 1
        if tithi_number > 30:
            tithi_number = 30

        # Calculate balance (percentage remaining in current tithi)
        position_in_tithi = elongation % DEGREES_PER_TITHI
        balance_percent = ((DEGREES_PER_TITHI - position_in_tithi) / DEGREES_PER_TITHI) * 100

        # Determine paksha
        if tithi_number <= 15:
            paksha = "Shukla"
            paksha_tithi = tithi_number
        else:
            paksha = "Krishna"
            paksha_tithi = tithi_number - 15

        # Get tithi name
        if tithi_number == 15:
            name = "Purnima"
        elif tithi_number == 30:
            name = "Amavasya"
        else:
            base_name = TITHI_NAMES[(paksha_tithi - 1) % 15]
            name = f"{paksha} {base_name}"

        # Calculate end time if speeds are provided
        end_time = None
        if moon_speed is not None and calculation_time is not None:
            end_time = self._calculate_end_time(
                position_in_tithi,
                moon_speed,
                sun_speed or SUN_MEAN_DAILY_MOTION,
                calculation_time,
                sun_longitude,
                moon_longitude,
                timezone_offset,
            )

        # Special markers
        is_purnima = tithi_number == 15
        is_amavasya = tithi_number == 30
        is_rikta = tithi_number in RIKTA_TITHIS

        # Get favorability
        favorability = TITHI_FAVORABILITY.get(tithi_number, 0.5)

        return TithiInfo(
            number=tithi_number,
            name=name,
            paksha=paksha,
            paksha_tithi=paksha_tithi,
            balance_percent=round(balance_percent, 2),
            end_time=end_time,
            is_purnima=is_purnima,
            is_amavasya=is_amavasya,
            is_rikta=is_rikta,
            favorability=favorability
        )

    def _calculate_end_time(
        self,
        position_in_tithi: float,
        moon_speed: float,
        sun_speed: float,
        calculation_time: datetime,
        sun_longitude: float = None,
        moon_longitude: float = None,
        timezone_offset: float = 0.0,
    ) -> datetime:
        """
        Calculate when the current tithi ends using iterative refinement.

        The tithi ends when Moon-Sun elongation crosses the next 12° boundary.
        Uses Newton-Raphson iteration for precision when Swiss Ephemeris is available.

        Args:
            position_in_tithi: Current position within tithi (0-12 degrees)
            moon_speed: Moon's daily motion in degrees
            sun_speed: Sun's daily motion in degrees
            calculation_time: Current time
            sun_longitude: Current Sun longitude (optional, for iterative calc)
            moon_longitude: Current Moon longitude (optional, for iterative calc)
            timezone_offset: Timezone offset from UTC in hours

        Returns:
            Datetime when tithi ends
        """
        # Try iterative calculation with Swiss Ephemeris for precision
        try:
            import swisseph as swe

            # Calculate current tithi number from elongation
            if moon_longitude is not None and sun_longitude is not None:
                elongation = (moon_longitude - sun_longitude) % 360
                current_tithi = int(elongation / DEGREES_PER_TITHI) + 1
                target_elongation = current_tithi * DEGREES_PER_TITHI  # Next boundary

                # Convert calculation_time to Julian Day (UTC)
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

                    if abs(error) < 0.0001:  # ~0.36 seconds precision
                        break

                    relative_speed = moon_pos[0][3] - sun_pos[0][3]
                    jd += error / relative_speed

                # Convert JD back to datetime
                year, month, day, hour_frac = swe.revjul(jd)
                hours = int(hour_frac)
                remaining = (hour_frac - hours) * 60
                minutes = int(remaining)
                seconds = int((remaining - minutes) * 60)

                end_utc = datetime(year, month, day, hours, minutes, seconds)
                end_time = end_utc + timedelta(hours=timezone_offset)
                return end_time

        except (ImportError, Exception) as e:
            logger.debug(f"Iterative calc failed, using linear: {e}")

        # Fallback: Linear extrapolation
        degrees_remaining = DEGREES_PER_TITHI - position_in_tithi
        relative_speed = moon_speed - sun_speed

        if relative_speed <= 0:
            relative_speed = MOON_MEAN_DAILY_MOTION - SUN_MEAN_DAILY_MOTION

        days_remaining = degrees_remaining / relative_speed
        end_time = calculation_time + timedelta(days=days_remaining)

        return end_time

    def get_tithi_at_time(
        self,
        sun_longitude: float,
        moon_longitude: float,
        target_time: datetime,
        moon_speed: float,
        sun_speed: float,
        base_time: datetime
    ) -> TithiInfo:
        """
        Calculate tithi at a specific time given base positions and speeds.

        Useful for finding tithi at sunrise, sunset, or other specific times.

        Args:
            sun_longitude: Sun's longitude at base_time
            moon_longitude: Moon's longitude at base_time
            target_time: Time for which to calculate tithi
            moon_speed: Moon's daily motion in degrees
            sun_speed: Sun's daily motion in degrees
            base_time: Time of the base positions

        Returns:
            TithiInfo for the target time
        """
        # Calculate time difference in days
        time_diff = (target_time - base_time).total_seconds() / 86400

        # Adjust positions
        adjusted_moon = (moon_longitude + moon_speed * time_diff) % 360
        adjusted_sun = (sun_longitude + sun_speed * time_diff) % 360

        return self.calculate(
            adjusted_sun,
            adjusted_moon,
            moon_speed,
            sun_speed,
            target_time
        )

    def find_tithi_start(
        self,
        target_tithi: int,
        sun_longitude: float,
        moon_longitude: float,
        moon_speed: float,
        sun_speed: float,
        calculation_time: datetime
    ) -> Optional[datetime]:
        """
        Find when a specific tithi starts.

        Args:
            target_tithi: Tithi number to find (1-30)
            sun_longitude: Current Sun longitude
            moon_longitude: Current Moon longitude
            moon_speed: Moon's daily motion
            sun_speed: Sun's daily motion
            calculation_time: Current time

        Returns:
            Datetime when the tithi starts, or None if calculation fails
        """
        # Current elongation
        current_elongation = (moon_longitude - sun_longitude) % 360

        # Target elongation for tithi start
        target_elongation = (target_tithi - 1) * DEGREES_PER_TITHI

        # Degrees until target
        degrees_needed = (target_elongation - current_elongation) % 360

        # Relative speed
        relative_speed = moon_speed - sun_speed
        if relative_speed <= 0:
            relative_speed = MOON_MEAN_DAILY_MOTION - SUN_MEAN_DAILY_MOTION

        # Days until target
        days_until = degrees_needed / relative_speed

        return calculation_time + timedelta(days=days_until)


# Singleton instance
_calculator: Optional[TithiCalculator] = None


def get_tithi_calculator() -> TithiCalculator:
    """Get singleton TithiCalculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = TithiCalculator()
    return _calculator


def calculate_tithi(
    sun_longitude: float,
    moon_longitude: float,
    moon_speed: Optional[float] = None,
    sun_speed: Optional[float] = None,
    calculation_time: Optional[datetime] = None
) -> TithiInfo:
    """
    Convenience function to calculate tithi.

    Args:
        sun_longitude: Sun's longitude in degrees (0-360)
        moon_longitude: Moon's longitude in degrees (0-360)
        moon_speed: Moon's daily motion (optional)
        sun_speed: Sun's daily motion (optional)
        calculation_time: Time of calculation (optional)

    Returns:
        TithiInfo object
    """
    return get_tithi_calculator().calculate(
        sun_longitude,
        moon_longitude,
        moon_speed,
        sun_speed,
        calculation_time
    )
