"""
Panchang Calculator - Main Orchestrator

This module provides the main calculator that combines all panchang
elements into a unified calculation.

Provides both global panchang (location-based) and personalized
panchang (with natal chart overlays).
"""

import logging
from datetime import datetime, date as date_type, timedelta
from typing import Dict, Optional, Any, Union
from dataclasses import dataclass, field

from .sun_times import get_sun_times_calculator, SunTimes
from .tithi import get_tithi_calculator, TithiInfo
from .nakshatra import get_nakshatra_calculator, NakshatraInfo
from .yoga import get_yoga_calculator, YogaInfo
from .karana import get_karana_calculator, KaranaInfo
from .hora import get_hora_calculator, HoraInfo, HoraSequenceInfo
from .inauspicious import (
    get_inauspicious_calculator,
    DailyInauspiciousPeriods,
    AuspiciousPeriod,
)
from .tarabala import get_tarabala_calculator, TarabalaInfo
from .constants import LUNAR_MONTH_NAMES, PAKSHA_NAMES

logger = logging.getLogger(__name__)


@dataclass
class GlobalPanchang:
    """Complete global panchang for a location and date."""
    # Date and location
    date: datetime
    latitude: float
    longitude: float
    timezone_offset: float
    timezone_name: str

    # Sun times
    sun_times: SunTimes

    # Five elements of panchang
    tithi: TithiInfo
    nakshatra: NakshatraInfo
    yoga: YogaInfo
    karana: KaranaInfo

    # Additional elements
    hora: HoraInfo  # Current hora
    hora_sequence: Optional[HoraSequenceInfo] = None  # Full 24 horas

    # Inauspicious/auspicious periods
    inauspicious_periods: Optional[DailyInauspiciousPeriods] = None

    # Lunar month info
    lunar_month: Optional[str] = None
    paksha: Optional[str] = None  # Shukla or Krishna

    # Day quality score (0-100)
    day_quality_score: float = 50.0
    day_quality_factors: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PersonalizedPanchang:
    """Personalized panchang with natal chart overlays."""
    # Base global panchang
    global_panchang: GlobalPanchang

    # Birth data used
    birth_nakshatra: int
    birth_nakshatra_name: str
    birth_moon_sign: Optional[int] = None

    # Tarabala (star compatibility)
    tarabala: Optional[TarabalaInfo] = None

    # Favorable horas for this person
    favorable_horas: list = field(default_factory=list)

    # Moon transit (which house Moon is transiting from natal Moon)
    moon_transit_house: Optional[int] = None
    moon_transit_quality: Optional[str] = None

    # Personal day quality score (0-100)
    personal_day_score: float = 50.0
    personal_factors: Dict[str, Any] = field(default_factory=dict)


class PanchangCalculator:
    """
    Main Panchang Calculator.

    Orchestrates all individual calculators to produce a complete
    panchang for any date and location.
    """

    def __init__(self, ephemeris_engine=None):
        """
        Initialize the panchang calculator.

        Args:
            ephemeris_engine: Optional ComprehensiveEphemerisEngine for
                            planetary calculations. If not provided,
                            will be created when needed.
        """
        self._ephemeris_engine = ephemeris_engine

        # Get calculator instances
        self._sun_times = get_sun_times_calculator()
        self._tithi = get_tithi_calculator()
        self._nakshatra = get_nakshatra_calculator()
        self._yoga = get_yoga_calculator()
        self._karana = get_karana_calculator()
        self._hora = get_hora_calculator()
        self._inauspicious = get_inauspicious_calculator()
        self._tarabala = get_tarabala_calculator()

    def _get_ephemeris_engine(self):
        """Get or create the ephemeris engine."""
        if self._ephemeris_engine is False:
            return None
        if self._ephemeris_engine is None:
            ephemeris_cls = None
            try:
                # Prefer package-qualified import; agent runtime may not expose
                # the legacy top-level `astro_core` module alias.
                from sanatani_astrology.astro_core.kundali_generator.comprehensive_ephemeris_engine import (
                    ComprehensiveEphemerisEngine as _ComprehensiveEphemerisEngine,
                )
                ephemeris_cls = _ComprehensiveEphemerisEngine
            except ImportError:
                pass

            if ephemeris_cls is None:
                try:
                    # Backward compatibility for environments where astro_core is top-level.
                    from astro_core.kundali_generator.comprehensive_ephemeris_engine import (
                        ComprehensiveEphemerisEngine as _ComprehensiveEphemerisEngine,
                    )
                    ephemeris_cls = _ComprehensiveEphemerisEngine
                except ImportError:
                    logger.warning("ComprehensiveEphemerisEngine not available")
                    self._ephemeris_engine = False
                    return None

            try:
                self._ephemeris_engine = ephemeris_cls()
            except Exception as exc:
                logger.warning(f"ComprehensiveEphemerisEngine init failed: {exc}")
                self._ephemeris_engine = False
                return None
        return self._ephemeris_engine

    def calculate_global(
        self,
        date: Union[datetime, date_type],
        latitude: float,
        longitude: float,
        timezone_offset: float = 5.5,
        timezone_name: str = "IST",
        include_hora_sequence: bool = False,
        include_inauspicious: bool = True
    ) -> GlobalPanchang:
        """
        Calculate global panchang for a location and date.

        Args:
            date: Date for calculation (time component used for current hora)
            latitude: Location latitude
            longitude: Location longitude
            timezone_offset: Timezone offset from UTC in hours
            timezone_name: Timezone name for display
            include_hora_sequence: Include full 24-hour hora sequence
            include_inauspicious: Include Rahu Kaal etc.

        Returns:
            GlobalPanchang with all panchang elements
        """
        # Convert date to datetime if needed
        if isinstance(date, date_type) and not isinstance(date, datetime):
            date = datetime.combine(date, datetime.min.time())

        # Calculate sun times first - needed for traditional panchang calculation
        sun_times = self._sun_times.calculate(
            date, latitude, longitude, timezone_offset
        )

        # Get planetary positions AT SUNRISE TIME (traditional Vedic panchang approach)
        # This matches drikpanchang.com and other authoritative sources
        sunrise_time = sun_times.sunrise
        sun_longitude, moon_longitude, moon_speed, sun_speed = self._get_planetary_data(
            sunrise_time, latitude, longitude, timezone_offset
        )

        # Calculate tithi at sunrise
        tithi = self._tithi.calculate(
            sun_longitude, moon_longitude,
            moon_speed, sun_speed, sunrise_time,
            timezone_offset=timezone_offset,
        )

        # Calculate nakshatra at sunrise
        nakshatra = self._nakshatra.calculate(
            moon_longitude, moon_speed, sunrise_time,
            timezone_offset=timezone_offset,
        )

        # Calculate yoga at sunrise
        yoga = self._yoga.calculate(
            sun_longitude, moon_longitude,
            moon_speed, sun_speed, sunrise_time,
            timezone_offset=timezone_offset,
        )

        # Calculate karana at sunrise
        karana = self._karana.calculate(
            sun_longitude, moon_longitude,
            moon_speed, sun_speed, sunrise_time,
            timezone_offset=timezone_offset,
        )

        # Calculate current hora
        weekday = date.weekday()
        hora = self._hora.calculate_current_hora(
            date, sun_times.sunrise, sun_times.sunset, weekday
        )

        # Full hora sequence (optional)
        hora_sequence = None
        if include_hora_sequence:
            hora_sequence = self._hora.calculate_full_sequence(
                date, sun_times.sunrise, sun_times.sunset
            )

        # Inauspicious periods (optional)
        inauspicious = None
        if include_inauspicious:
            inauspicious = self._inauspicious.calculate_all(
                date, sun_times.sunrise, sun_times.sunset
            )

        # Determine lunar month and paksha
        lunar_month, paksha = self._get_lunar_month_paksha(
            tithi.number,
            sun_longitude,
            sun_speed,
            moon_speed,
        )

        # Calculate day quality score
        day_score, factors = self._calculate_day_quality(
            tithi, nakshatra, yoga, karana, hora
        )

        return GlobalPanchang(
            date=date,
            latitude=latitude,
            longitude=longitude,
            timezone_offset=timezone_offset,
            timezone_name=timezone_name,
            sun_times=sun_times,
            tithi=tithi,
            nakshatra=nakshatra,
            yoga=yoga,
            karana=karana,
            hora=hora,
            hora_sequence=hora_sequence,
            inauspicious_periods=inauspicious,
            lunar_month=lunar_month,
            paksha=paksha,
            day_quality_score=day_score,
            day_quality_factors=factors
        )

    def calculate_personalized(
        self,
        date: Union[datetime, date_type],
        latitude: float,
        longitude: float,
        birth_nakshatra: int,
        birth_moon_sign: Optional[int] = None,
        timezone_offset: float = 5.5,
        timezone_name: str = "IST",
        favorable_planets: Optional[list] = None
    ) -> PersonalizedPanchang:
        """
        Calculate personalized panchang with natal overlays.

        Args:
            date: Date for calculation
            latitude: Location latitude
            longitude: Location longitude
            birth_nakshatra: Birth nakshatra index (0-26)
            birth_moon_sign: Birth Moon rashi index (0-11)
            timezone_offset: Timezone offset from UTC
            timezone_name: Timezone name
            favorable_planets: List of favorable planets for hora calculation

        Returns:
            PersonalizedPanchang with personalized overlays
        """
        # Get global panchang first
        global_panchang = self.calculate_global(
            date, latitude, longitude,
            timezone_offset, timezone_name,
            include_hora_sequence=True,
            include_inauspicious=True
        )

        # Calculate tarabala
        tarabala = self._tarabala.calculate(
            birth_nakshatra,
            global_panchang.nakshatra.index
        )

        # Get birth nakshatra name
        from .constants import NAKSHATRA_NAMES
        birth_nakshatra_name = NAKSHATRA_NAMES[birth_nakshatra % 27]

        # Find favorable horas
        favorable_horas = []
        if global_panchang.hora_sequence:
            if favorable_planets is None:
                # Default favorable planets
                favorable_planets = ["Jupiter", "Venus", "Mercury"]

            all_horas = (
                global_panchang.hora_sequence.day_horas +
                global_panchang.hora_sequence.night_horas
            )
            favorable_horas = [
                h for h in all_horas
                if h.ruler in favorable_planets
            ]

        # Calculate Moon transit house
        moon_transit_house = None
        moon_transit_quality = None
        if birth_moon_sign is not None:
            moon_transit_house = self._calculate_moon_transit(
                global_panchang.nakshatra.index,
                birth_moon_sign
            )
            moon_transit_quality = self._get_moon_transit_quality(moon_transit_house)

        # Calculate personal day score
        personal_score, personal_factors = self._calculate_personal_score(
            global_panchang.day_quality_score,
            tarabala,
            moon_transit_house,
            global_panchang.hora
        )

        return PersonalizedPanchang(
            global_panchang=global_panchang,
            birth_nakshatra=birth_nakshatra,
            birth_nakshatra_name=birth_nakshatra_name,
            birth_moon_sign=birth_moon_sign,
            tarabala=tarabala,
            favorable_horas=favorable_horas,
            moon_transit_house=moon_transit_house,
            moon_transit_quality=moon_transit_quality,
            personal_day_score=personal_score,
            personal_factors=personal_factors
        )

    def _get_planetary_data(
        self,
        date: datetime,
        latitude: float,
        longitude: float,
        timezone_offset: float = 0.0,
    ) -> tuple:
        """
        Get Sun and Moon positions from ephemeris.

        Returns:
            Tuple of (sun_longitude, moon_longitude, moon_speed, sun_speed)
        """
        engine = self._get_ephemeris_engine()

        if engine is None:
            # Fallback: use simplified calculation
            return self._simplified_planetary_data(date, timezone_offset)

        try:
            # Prefer ephemeris engine if available (julian-based API)
            if hasattr(engine, "calculate_planetary_positions"):
                jd = engine.julian_day_from_datetime(date, timezone_offset)
                positions = engine.calculate_planetary_positions(
                    jd, latitude, longitude
                )
            else:
                positions = engine.calculate_positions(
                    date, latitude, longitude
                )

            sun_data = positions.get("sun") or positions.get("Sun") or {}
            moon_data = positions.get("moon") or positions.get("Moon") or {}

            if hasattr(sun_data, "longitude"):
                sun_longitude = sun_data.longitude
                sun_speed = getattr(sun_data, "speed", None)
            else:
                sun_longitude = sun_data.get("longitude", 0.0)
                sun_speed = sun_data.get("speed")

            if hasattr(moon_data, "longitude"):
                moon_longitude = moon_data.longitude
                moon_speed = getattr(moon_data, "speed", None)
            else:
                moon_longitude = moon_data.get("longitude", 0.0)
                moon_speed = moon_data.get("speed")

            if sun_speed is None:
                sun_speed = 0.9856473
            if moon_speed is None:
                moon_speed = 13.176358

            return sun_longitude, moon_longitude, moon_speed, sun_speed

        except Exception as e:
            logger.warning(f"Ephemeris calculation failed: {e}, using fallback")
            return self._simplified_planetary_data(date, timezone_offset)

    def _simplified_planetary_data(self, date: datetime, timezone_offset: float = 0.0) -> tuple:
        """
        Simplified planetary calculation fallback.

        Uses mean motion from a reference epoch.
        Not accurate but provides reasonable approximation.
        """
        # Reference: Jan 1, 2000 00:00 UTC
        # Sun at ~280°, Moon at ~0° (approximately)
        reference = datetime(2000, 1, 1, 0, 0, 0)
        utc_date = date - timedelta(hours=timezone_offset)
        days_since = (utc_date - reference).total_seconds() / 86400.0

        # Mean daily motions
        sun_mean_motion = 0.9856473  # degrees per day
        moon_mean_motion = 13.176358  # degrees per day

        # Reference positions (approximate)
        sun_ref = 280.0
        moon_ref = 0.0

        sun_longitude = (sun_ref + sun_mean_motion * days_since) % 360
        moon_longitude = (moon_ref + moon_mean_motion * days_since) % 360

        return sun_longitude, moon_longitude, moon_mean_motion, sun_mean_motion

    def _get_lunar_month_paksha(
        self,
        tithi_number: int,
        sun_longitude: float,
        sun_speed: float,
        moon_speed: float,
    ) -> tuple:
        """
        Determine lunar month approximation and paksha.

        Lunar month is approximated from the Sun's sign at the last new moon
        (amanta month convention), using mean daily motion.

        Returns:
            Tuple of (lunar_month_name or None, paksha)
        """
        # Paksha: 1-15 is Shukla (waxing), 16-30 is Krishna (waning)
        if tithi_number <= 15:
            paksha = PAKSHA_NAMES["shukla"]  # Shukla Paksha
        else:
            paksha = PAKSHA_NAMES["krishna"]  # Krishna Paksha

        if not tithi_number or sun_speed is None or moon_speed is None:
            return None, paksha

        synodic_speed = moon_speed - sun_speed
        if synodic_speed <= 0:
            return None, paksha

        tithi_index = max(0, min(int(tithi_number) - 1, 29))
        days_since_new_moon = (tithi_index * 12.0) / synodic_speed

        sun_longitude_new_moon = (sun_longitude - sun_speed * days_since_new_moon) % 360
        sun_rasi = int(sun_longitude_new_moon / 30) % 12

        return LUNAR_MONTH_NAMES[sun_rasi], paksha

    def _calculate_day_quality(
        self,
        tithi: TithiInfo,
        nakshatra: NakshatraInfo,
        yoga: YogaInfo,
        karana: KaranaInfo,
        hora: HoraInfo
    ) -> tuple:
        """
        Calculate overall day quality score.

        Returns:
            Tuple of (score 0-100, factors dict)
        """
        factors = {}

        # Base from favorability scores (0-1 scale)
        tithi_score = tithi.favorability * 100
        nakshatra_score = nakshatra.favorability * 100
        yoga_score = yoga.favorability * 100
        karana_score = karana.favorability * 100
        hora_score = hora.favorability * 100

        factors['tithi'] = {
            'name': tithi.name,
            'score': round(tithi_score, 1),
            'is_purnima': tithi.is_purnima,
            'is_amavasya': tithi.is_amavasya
        }
        factors['nakshatra'] = {
            'name': nakshatra.name,
            'score': round(nakshatra_score, 1),
            'is_gandanta': nakshatra.is_gandanta
        }
        factors['yoga'] = {
            'name': yoga.name,
            'score': round(yoga_score, 1),
            'is_critical_avoid': yoga.is_critical_avoid
        }
        factors['karana'] = {
            'name': karana.name,
            'score': round(karana_score, 1),
            'is_vishti': karana.is_vishti
        }
        factors['hora'] = {
            'ruler': hora.ruler,
            'score': round(hora_score, 1)
        }

        # Weighted average
        # Tithi and Nakshatra are most important
        weights = {
            'tithi': 0.25,
            'nakshatra': 0.25,
            'yoga': 0.20,
            'karana': 0.15,
            'hora': 0.15
        }

        total_score = (
            tithi_score * weights['tithi'] +
            nakshatra_score * weights['nakshatra'] +
            yoga_score * weights['yoga'] +
            karana_score * weights['karana'] +
            hora_score * weights['hora']
        )

        # Apply penalties for critical conditions
        if yoga.is_critical_avoid:
            total_score *= 0.7
            factors['critical_warning'] = f"Critical avoid yoga: {yoga.name}"

        if karana.is_vishti:
            total_score *= 0.85
            factors['vishti_warning'] = "Vishti (Bhadra) karana - inauspicious"

        if nakshatra.is_gandanta:
            total_score *= 0.9
            factors['gandanta_warning'] = "Gandanta nakshatra - junction point"

        return round(total_score, 1), factors

    def _calculate_moon_transit(
        self,
        current_nakshatra: int,
        birth_moon_sign: int
    ) -> int:
        """
        Calculate which house Moon is transiting from natal Moon.

        Args:
            current_nakshatra: Current nakshatra index (0-26)
            birth_moon_sign: Birth Moon rashi (0-11)

        Returns:
            House number (1-12) from natal Moon
        """
        # Current Moon sign from nakshatra
        # Each sign spans 2.25 nakshatras
        current_sign = (current_nakshatra * 4) // 9  # 0-11

        # House from natal Moon (1-indexed)
        house = ((current_sign - birth_moon_sign) % 12) + 1

        return house

    def _get_moon_transit_quality(self, house: int) -> str:
        """
        Get quality of Moon transit through a house.

        Good houses: 1, 3, 6, 10, 11
        Bad houses: 4, 8, 12
        Neutral: 2, 5, 7, 9
        """
        if house in [1, 3, 6, 10, 11]:
            return "favorable"
        elif house in [4, 8, 12]:
            return "unfavorable"
        else:
            return "neutral"

    def _calculate_personal_score(
        self,
        base_score: float,
        tarabala: Optional[TarabalaInfo],
        moon_transit_house: Optional[int],
        hora: HoraInfo
    ) -> tuple:
        """
        Calculate personalized day score.

        Returns:
            Tuple of (score 0-100, factors dict)
        """
        factors = {}
        score = base_score

        # Tarabala impact (most important personal factor)
        if tarabala:
            tarabala_score = tarabala.favorability * 100
            factors['tarabala'] = {
                'tara': tarabala.tara_name,
                'score': round(tarabala_score, 1),
                'is_critical_avoid': tarabala.is_critical_avoid,
                'description': tarabala.description
            }

            # Weight: 40% tarabala, 60% global
            score = score * 0.6 + tarabala_score * 0.4

            if tarabala.is_critical_avoid:
                score *= 0.5
                factors['naidhana_warning'] = (
                    f"Naidhana (death) tara - strongly avoid important activities"
                )

        # Moon transit impact
        if moon_transit_house:
            transit_quality = self._get_moon_transit_quality(moon_transit_house)
            factors['moon_transit'] = {
                'house': moon_transit_house,
                'quality': transit_quality
            }

            if transit_quality == "favorable":
                score += 5
            elif transit_quality == "unfavorable":
                score -= 10

        # Ensure bounds
        score = max(0, min(100, score))

        return round(score, 1), factors


# Singleton instance
_calculator: Optional[PanchangCalculator] = None


def get_panchang_calculator(ephemeris_engine=None) -> PanchangCalculator:
    """Get singleton PanchangCalculator instance."""
    global _calculator
    if _calculator is None:
        _calculator = PanchangCalculator(ephemeris_engine)
    return _calculator


def calculate_global_panchang(
    date: Union[datetime, date_type],
    latitude: float,
    longitude: float,
    timezone_offset: float = 5.5,
    timezone_name: str = "IST"
) -> GlobalPanchang:
    """
    Convenience function for global panchang.

    Args:
        date: Date for calculation
        latitude: Location latitude
        longitude: Location longitude
        timezone_offset: Timezone offset from UTC
        timezone_name: Timezone name

    Returns:
        GlobalPanchang object
    """
    return get_panchang_calculator().calculate_global(
        date, latitude, longitude, timezone_offset, timezone_name
    )


def calculate_personalized_panchang(
    date: Union[datetime, date_type],
    latitude: float,
    longitude: float,
    birth_nakshatra: int,
    birth_moon_sign: Optional[int] = None,
    timezone_offset: float = 5.5,
    timezone_name: str = "IST"
) -> PersonalizedPanchang:
    """
    Convenience function for personalized panchang.

    Args:
        date: Date for calculation
        latitude: Location latitude
        longitude: Location longitude
        birth_nakshatra: Birth nakshatra index (0-26)
        birth_moon_sign: Birth Moon rashi (0-11)
        timezone_offset: Timezone offset from UTC
        timezone_name: Timezone name

    Returns:
        PersonalizedPanchang object
    """
    return get_panchang_calculator().calculate_personalized(
        date, latitude, longitude,
        birth_nakshatra, birth_moon_sign,
        timezone_offset, timezone_name
    )
