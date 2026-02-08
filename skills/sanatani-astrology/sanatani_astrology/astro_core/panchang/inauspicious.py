"""
Inauspicious Periods Calculator - Rahu Kaal, Yamaganda, Gulika, Abhijit

These are time periods calculated based on sunrise and weekday.
The day (sunrise to sunset) is divided into 8 equal parts.
Each inauspicious period occupies one slot, with the slot varying by weekday.

Abhijit Muhurta is the most auspicious time, occurring around local noon.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from dataclasses import dataclass

from .constants import (
    RAHU_KAAL_SLOTS,
    YAMAGANDA_SLOTS,
    GULIKA_SLOTS,
    WEEKDAY_NAMES,
)

logger = logging.getLogger(__name__)


@dataclass
class InauspiciousPeriod:
    """Information about an inauspicious time period."""
    name: str
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    slot_number: int         # Which slot (1-8)
    severity: str            # "high", "medium", "low"
    description: str


@dataclass
class AuspiciousPeriod:
    """Information about an auspicious time period."""
    name: str
    start_time: datetime
    end_time: datetime
    duration_minutes: float
    description: str


@dataclass
class DailyInauspiciousPeriods:
    """All inauspicious and auspicious periods for a day."""
    date: datetime
    weekday: str
    rahu_kaal: InauspiciousPeriod
    yamaganda: InauspiciousPeriod
    gulika_kaal: InauspiciousPeriod
    abhijit_muhurta: AuspiciousPeriod
    brahma_muhurta: Optional[AuspiciousPeriod]


class InauspiciousPeriodsCalculator:
    """
    Calculator for daily inauspicious periods.

    Rahu Kaal: Most inauspicious, avoid starting important work
    Yamaganda: Inauspicious, avoid journeys and beginnings
    Gulika Kaal: Son of Saturn, inauspicious for new ventures

    Abhijit Muhurta: Most auspicious time around local noon
    Brahma Muhurta: Auspicious pre-dawn time for spiritual activities
    """

    def calculate_all(
        self,
        date: datetime,
        sunrise: datetime,
        sunset: datetime,
        next_sunrise: Optional[datetime] = None
    ) -> DailyInauspiciousPeriods:
        """
        Calculate all inauspicious and auspicious periods for a day.

        Args:
            date: Date for calculation
            sunrise: Sunrise time
            sunset: Sunset time
            next_sunrise: Next day's sunrise (for Brahma Muhurta)

        Returns:
            DailyInauspiciousPeriods with all periods
        """
        weekday = date.weekday()

        # Calculate day duration and slot duration
        day_duration = (sunset - sunrise).total_seconds()
        slot_duration = day_duration / 8

        # Calculate inauspicious periods
        rahu_kaal = self._calculate_period(
            "Rahu Kaal",
            RAHU_KAAL_SLOTS[weekday],
            sunrise,
            slot_duration,
            "high",
            "Highly inauspicious. Avoid starting important activities, signing documents, or beginning journeys."
        )

        yamaganda = self._calculate_period(
            "Yamaganda",
            YAMAGANDA_SLOTS[weekday],
            sunrise,
            slot_duration,
            "medium",
            "Inauspicious period. Avoid new beginnings and travel."
        )

        gulika_kaal = self._calculate_period(
            "Gulika Kaal",
            GULIKA_SLOTS[weekday],
            sunrise,
            slot_duration,
            "medium",
            "Saturn's son period. Avoid new ventures and important decisions."
        )

        # Calculate Abhijit Muhurta (around local noon)
        abhijit_muhurta = self._calculate_abhijit(sunrise, sunset)

        # Calculate Brahma Muhurta (pre-dawn)
        brahma_muhurta = None
        if next_sunrise:
            brahma_muhurta = self._calculate_brahma_muhurta(next_sunrise)
        else:
            # Approximate next sunrise
            approx_next_sunrise = sunrise + timedelta(days=1)
            brahma_muhurta = self._calculate_brahma_muhurta(approx_next_sunrise)

        return DailyInauspiciousPeriods(
            date=date,
            weekday=WEEKDAY_NAMES[weekday],
            rahu_kaal=rahu_kaal,
            yamaganda=yamaganda,
            gulika_kaal=gulika_kaal,
            abhijit_muhurta=abhijit_muhurta,
            brahma_muhurta=brahma_muhurta
        )

    def _calculate_period(
        self,
        name: str,
        slot: int,
        sunrise: datetime,
        slot_duration: float,
        severity: str,
        description: str
    ) -> InauspiciousPeriod:
        """
        Calculate a single inauspicious period.

        Args:
            name: Period name
            slot: Slot number (1-8)
            sunrise: Sunrise time
            slot_duration: Duration of each slot in seconds
            severity: Severity level
            description: Description text

        Returns:
            InauspiciousPeriod object
        """
        # Slots are 1-indexed
        start_time = sunrise + timedelta(seconds=slot_duration * (slot - 1))
        end_time = sunrise + timedelta(seconds=slot_duration * slot)

        return InauspiciousPeriod(
            name=name,
            start_time=start_time,
            end_time=end_time,
            duration_minutes=slot_duration / 60,
            slot_number=slot,
            severity=severity,
            description=description
        )

    def _calculate_abhijit(
        self,
        sunrise: datetime,
        sunset: datetime
    ) -> AuspiciousPeriod:
        """
        Calculate Abhijit Muhurta.

        Abhijit is the 8th muhurta of the day (out of 15 day muhurtas).
        It occurs around local noon and lasts approximately 48 minutes.

        Args:
            sunrise: Sunrise time
            sunset: Sunset time

        Returns:
            AuspiciousPeriod for Abhijit Muhurta
        """
        day_duration = (sunset - sunrise).total_seconds()
        muhurta_duration = day_duration / 15

        # Abhijit is the 8th muhurta (index 7, 0-based)
        start_time = sunrise + timedelta(seconds=muhurta_duration * 7)
        end_time = sunrise + timedelta(seconds=muhurta_duration * 8)

        return AuspiciousPeriod(
            name="Abhijit Muhurta",
            start_time=start_time,
            end_time=end_time,
            duration_minutes=muhurta_duration / 60,
            description="Most auspicious time of the day. Excellent for starting important work, ceremonies, and new ventures."
        )

    def _calculate_brahma_muhurta(
        self,
        sunrise: datetime
    ) -> AuspiciousPeriod:
        """
        Calculate Brahma Muhurta.

        Brahma Muhurta is 1.5 hours before sunrise, lasting 48 minutes.
        It's the second-to-last muhurta of the night.

        Args:
            sunrise: Sunrise time

        Returns:
            AuspiciousPeriod for Brahma Muhurta
        """
        # Traditionally 96 minutes to 48 minutes before sunrise
        start_time = sunrise - timedelta(minutes=96)
        end_time = sunrise - timedelta(minutes=48)

        return AuspiciousPeriod(
            name="Brahma Muhurta",
            start_time=start_time,
            end_time=end_time,
            duration_minutes=48,
            description="Auspicious pre-dawn time for meditation, prayer, and spiritual practices."
        )

    def calculate_rahu_kaal(
        self,
        sunrise: datetime,
        sunset: datetime,
        weekday: int
    ) -> InauspiciousPeriod:
        """
        Calculate only Rahu Kaal.

        Args:
            sunrise: Sunrise time
            sunset: Sunset time
            weekday: Day of week (0=Monday, 6=Sunday)

        Returns:
            InauspiciousPeriod for Rahu Kaal
        """
        day_duration = (sunset - sunrise).total_seconds()
        slot_duration = day_duration / 8

        return self._calculate_period(
            "Rahu Kaal",
            RAHU_KAAL_SLOTS[weekday],
            sunrise,
            slot_duration,
            "high",
            "Highly inauspicious. Avoid starting important activities."
        )

    def is_in_inauspicious_period(
        self,
        check_time: datetime,
        periods: DailyInauspiciousPeriods
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a time falls within any inauspicious period.

        Args:
            check_time: Time to check
            periods: DailyInauspiciousPeriods object

        Returns:
            Tuple of (is_inauspicious, period_name)
        """
        # Check Rahu Kaal
        if periods.rahu_kaal.start_time <= check_time < periods.rahu_kaal.end_time:
            return True, "Rahu Kaal"

        # Check Yamaganda
        if periods.yamaganda.start_time <= check_time < periods.yamaganda.end_time:
            return True, "Yamaganda"

        # Check Gulika Kaal
        if periods.gulika_kaal.start_time <= check_time < periods.gulika_kaal.end_time:
            return True, "Gulika Kaal"

        return False, None

    def is_in_abhijit(
        self,
        check_time: datetime,
        abhijit: AuspiciousPeriod
    ) -> bool:
        """
        Check if a time falls within Abhijit Muhurta.

        Args:
            check_time: Time to check
            abhijit: AuspiciousPeriod for Abhijit

        Returns:
            True if within Abhijit Muhurta
        """
        return abhijit.start_time <= check_time < abhijit.end_time

    def get_next_good_time(
        self,
        check_time: datetime,
        periods: DailyInauspiciousPeriods
    ) -> datetime:
        """
        Find the next time that's not in any inauspicious period.

        Args:
            check_time: Starting time to check
            periods: DailyInauspiciousPeriods object

        Returns:
            Next good time
        """
        is_bad, period_name = self.is_in_inauspicious_period(check_time, periods)

        if not is_bad:
            return check_time

        # Find which period and get its end time
        if period_name == "Rahu Kaal":
            return periods.rahu_kaal.end_time
        elif period_name == "Yamaganda":
            return periods.yamaganda.end_time
        elif period_name == "Gulika Kaal":
            return periods.gulika_kaal.end_time

        return check_time


# Singleton instance
_calculator: Optional[InauspiciousPeriodsCalculator] = None


def get_inauspicious_calculator() -> InauspiciousPeriodsCalculator:
    """Get singleton InauspiciousPeriodsCalculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = InauspiciousPeriodsCalculator()
    return _calculator


def calculate_inauspicious_periods(
    date: datetime,
    sunrise: datetime,
    sunset: datetime,
    next_sunrise: Optional[datetime] = None
) -> DailyInauspiciousPeriods:
    """
    Convenience function to calculate all inauspicious periods.

    Args:
        date: Date for calculation
        sunrise: Sunrise time
        sunset: Sunset time
        next_sunrise: Next day's sunrise (optional)

    Returns:
        DailyInauspiciousPeriods object
    """
    return get_inauspicious_calculator().calculate_all(
        date, sunrise, sunset, next_sunrise
    )
