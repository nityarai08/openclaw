"""
Hora Calculator - Planetary Hours

Each day is divided into 24 horas (planetary hours):
- 12 day horas (sunrise to sunset)
- 12 night horas (sunset to next sunrise)

The first hora of the day is ruled by the day's planetary ruler.
Subsequent horas follow the Chaldean order.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass

from .constants import (
    HORA_SEQUENCE,
    DAY_RULERS,
    WEEKDAY_NAMES,
    HORA_FAVORABILITY,
)

logger = logging.getLogger(__name__)


@dataclass
class HoraInfo:
    """Information about a single hora."""
    hora_number: int         # 1-24 (1-12 day, 13-24 night)
    ruler: str               # Planetary ruler
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    is_day_hora: bool        # Day or night hora
    favorability: float      # 0.0-1.0


@dataclass
class HoraSequenceInfo:
    """Complete hora sequence for a day."""
    date: datetime
    weekday: str
    day_ruler: str
    day_horas: List[HoraInfo]
    night_horas: List[HoraInfo]
    current_hora: Optional[HoraInfo]


class HoraCalculator:
    """
    Calculator for Hora (Planetary Hours).

    Horas are unequal hours based on day/night length.
    Day horas are from sunrise to sunset (12 horas).
    Night horas are from sunset to next sunrise (12 horas).
    """

    def __init__(self):
        """Initialize hora calculator."""
        # Build reverse mapping: planet -> index in HORA_SEQUENCE
        self._planet_to_index = {
            planet: idx for idx, planet in enumerate(HORA_SEQUENCE)
        }

    def calculate_current_hora(
        self,
        current_time: datetime,
        sunrise: datetime,
        sunset: datetime,
        weekday: int
    ) -> HoraInfo:
        """
        Calculate the current hora.

        Args:
            current_time: Time to check
            sunrise: Sunrise time for the day
            sunset: Sunset time for the day
            weekday: Day of week (0=Monday, 6=Sunday)

        Returns:
            HoraInfo for the current hora
        """
        # Determine if day or night
        is_day = sunrise <= current_time < sunset

        if is_day:
            # Day hora
            day_duration = (sunset - sunrise).total_seconds()
            hora_duration = day_duration / 12

            elapsed = (current_time - sunrise).total_seconds()
            hora_number = int(elapsed / hora_duration) + 1

            if hora_number > 12:
                hora_number = 12

            start_time = sunrise + timedelta(seconds=hora_duration * (hora_number - 1))
            end_time = sunrise + timedelta(seconds=hora_duration * hora_number)

        else:
            # Night hora
            # For night, we need next sunrise
            # Approximate: assume 24 hours from current sunrise
            next_sunrise = sunrise + timedelta(days=1)
            night_duration = (next_sunrise - sunset).total_seconds()
            hora_duration = night_duration / 12

            if current_time >= sunset:
                elapsed = (current_time - sunset).total_seconds()
            else:
                # After midnight but before sunrise
                elapsed = (current_time + timedelta(days=1) - sunset).total_seconds()

            hora_number = int(elapsed / hora_duration) + 13  # 13-24 for night

            if hora_number > 24:
                hora_number = 24

            night_hora_index = hora_number - 13
            start_time = sunset + timedelta(seconds=hora_duration * night_hora_index)
            end_time = sunset + timedelta(seconds=hora_duration * (night_hora_index + 1))

        # Calculate ruler
        ruler = self._get_hora_ruler(hora_number, weekday)
        favorability = HORA_FAVORABILITY.get(ruler, 0.5)

        return HoraInfo(
            hora_number=hora_number,
            ruler=ruler,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=hora_duration / 60,
            is_day_hora=is_day,
            favorability=favorability
        )

    def calculate_full_sequence(
        self,
        date: datetime,
        sunrise: datetime,
        sunset: datetime,
        next_sunrise: Optional[datetime] = None
    ) -> HoraSequenceInfo:
        """
        Calculate complete hora sequence for a day.

        Args:
            date: Date for calculation
            sunrise: Sunrise time
            sunset: Sunset time
            next_sunrise: Next day's sunrise (optional, estimated if not provided)

        Returns:
            HoraSequenceInfo with all 24 horas
        """
        weekday = date.weekday()
        day_ruler = DAY_RULERS[weekday]

        # Calculate day horas
        day_duration = (sunset - sunrise).total_seconds()
        day_hora_duration = day_duration / 12

        day_horas = []
        for i in range(12):
            hora_number = i + 1
            start = sunrise + timedelta(seconds=day_hora_duration * i)
            end = sunrise + timedelta(seconds=day_hora_duration * (i + 1))
            ruler = self._get_hora_ruler(hora_number, weekday)

            day_horas.append(HoraInfo(
                hora_number=hora_number,
                ruler=ruler,
                start_time=start,
                end_time=end,
                duration_minutes=day_hora_duration / 60,
                is_day_hora=True,
                favorability=HORA_FAVORABILITY.get(ruler, 0.5)
            ))

        # Calculate night horas
        if next_sunrise is None:
            next_sunrise = sunrise + timedelta(days=1)

        night_duration = (next_sunrise - sunset).total_seconds()
        night_hora_duration = night_duration / 12

        night_horas = []
        for i in range(12):
            hora_number = i + 13
            start = sunset + timedelta(seconds=night_hora_duration * i)
            end = sunset + timedelta(seconds=night_hora_duration * (i + 1))
            ruler = self._get_hora_ruler(hora_number, weekday)

            night_horas.append(HoraInfo(
                hora_number=hora_number,
                ruler=ruler,
                start_time=start,
                end_time=end,
                duration_minutes=night_hora_duration / 60,
                is_day_hora=False,
                favorability=HORA_FAVORABILITY.get(ruler, 0.5)
            ))

        # Find current hora
        now = datetime.now()
        current_hora = None
        all_horas = day_horas + night_horas

        for hora in all_horas:
            if hora.start_time <= now < hora.end_time:
                current_hora = hora
                break

        return HoraSequenceInfo(
            date=date,
            weekday=WEEKDAY_NAMES[weekday],
            day_ruler=day_ruler,
            day_horas=day_horas,
            night_horas=night_horas,
            current_hora=current_hora
        )

    def _get_hora_ruler(self, hora_number: int, weekday: int) -> str:
        """
        Get the planetary ruler for a specific hora.

        The sequence starts with the day ruler and follows Chaldean order:
        Saturn -> Jupiter -> Mars -> Sun -> Venus -> Mercury -> Moon

        Args:
            hora_number: Hora number (1-24)
            weekday: Day of week (0=Monday, 6=Sunday)

        Returns:
            Planet name ruling this hora
        """
        # Get day ruler
        day_ruler = DAY_RULERS[weekday]

        # Find starting index in Chaldean sequence
        # Note: HORA_SEQUENCE is already in Chaldean order
        start_index = self._planet_to_index.get(day_ruler, 0)

        # Calculate hora offset (0-based)
        hora_offset = hora_number - 1

        # Get ruler index (cycling through 7 planets)
        ruler_index = (start_index + hora_offset) % 7

        return HORA_SEQUENCE[ruler_index]

    def get_favorable_horas(
        self,
        date: datetime,
        sunrise: datetime,
        sunset: datetime,
        favorable_planets: List[str] = None
    ) -> List[HoraInfo]:
        """
        Get horas ruled by favorable planets.

        Args:
            date: Date for calculation
            sunrise: Sunrise time
            sunset: Sunset time
            favorable_planets: List of favorable planet names
                              (default: Jupiter, Venus, Mercury)

        Returns:
            List of favorable HoraInfo objects
        """
        if favorable_planets is None:
            favorable_planets = ["Jupiter", "Venus", "Mercury"]

        sequence = self.calculate_full_sequence(date, sunrise, sunset)
        all_horas = sequence.day_horas + sequence.night_horas

        return [
            hora for hora in all_horas
            if hora.ruler in favorable_planets
        ]

    def get_jupiter_hora(
        self,
        date: datetime,
        sunrise: datetime,
        sunset: datetime
    ) -> List[HoraInfo]:
        """
        Get Jupiter horas (most auspicious).

        Returns:
            List of Jupiter hora times
        """
        return self.get_favorable_horas(
            date, sunrise, sunset,
            favorable_planets=["Jupiter"]
        )


# Singleton instance
_calculator: Optional[HoraCalculator] = None


def get_hora_calculator() -> HoraCalculator:
    """Get singleton HoraCalculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = HoraCalculator()
    return _calculator


def calculate_current_hora(
    current_time: datetime,
    sunrise: datetime,
    sunset: datetime,
    weekday: int
) -> HoraInfo:
    """
    Convenience function to calculate current hora.

    Args:
        current_time: Time to check
        sunrise: Sunrise time
        sunset: Sunset time
        weekday: Day of week (0=Monday, 6=Sunday)

    Returns:
        HoraInfo object
    """
    return get_hora_calculator().calculate_current_hora(
        current_time, sunrise, sunset, weekday
    )
