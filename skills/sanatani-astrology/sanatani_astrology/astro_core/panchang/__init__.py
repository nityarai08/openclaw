"""
Panchang Module - Standalone Vedic Calendar Calculations

This module provides accurate panchang calculations independent of the
layer processing system. All calculations are verified against
DrikPanchang and Free Astrology API.

Components:
- sun_times: Sunrise/sunset using Swiss Ephemeris
- tithi: Lunar day calculation (1-30)
- nakshatra: Lunar mansion calculation (0-26)
- yoga: Sun+Moon combination (0-26)
- karana: Half-tithi calculation (0-10)
- hora: Planetary hours (24 per day)
- inauspicious: Rahu Kaal, Yamaganda, Gulika
- tarabala: Star compatibility from birth nakshatra
- calculator: Main orchestrator for complete panchang
"""

from .constants import (
    TITHI_NAMES,
    TITHI_FAVORABILITY,
    NAKSHATRA_NAMES,
    NAKSHATRA_LORDS,
    NAKSHATRA_FAVORABILITY,
    YOGA_NAMES,
    YOGA_FAVORABILITY,
    CRITICAL_AVOID_YOGAS,
    MOVABLE_KARANA_NAMES,
    FIXED_KARANA_NAMES,
    ALL_KARANA_NAMES,
    KARANA_FAVORABILITY,
    VISHTI_KARANA_INDEX,
    TARABALA_NAMES,
    TARABALA_FAVORABILITY,
    FAVORABLE_TARAS,
    CRITICAL_AVOID_TARAS,
    HORA_SEQUENCE,
    DAY_RULERS,
    WEEKDAY_NAMES,
    HORA_FAVORABILITY,
    RAHU_KAAL_SLOTS,
    YAMAGANDA_SLOTS,
    GULIKA_SLOTS,
    LUNAR_MONTH_NAMES,
    PAKSHA_NAMES,
    RASI_NAMES,
    RASI_NAMES_ENGLISH,
)

# Sun times
from .sun_times import (
    SunTimes,
    SunTimesCalculator,
    get_sun_times_calculator,
    calculate_sun_times,
)

# Tithi
from .tithi import (
    TithiInfo,
    TithiCalculator,
    get_tithi_calculator,
    calculate_tithi,
)

# Nakshatra
from .nakshatra import (
    NakshatraInfo,
    NakshatraCalculator,
    get_nakshatra_calculator,
    calculate_nakshatra,
)

# Yoga
from .yoga import (
    YogaInfo,
    YogaCalculator,
    get_yoga_calculator,
    calculate_yoga,
)

# Karana
from .karana import (
    KaranaInfo,
    KaranaCalculator,
    get_karana_calculator,
    calculate_karana,
)

# Hora
from .hora import (
    HoraInfo,
    HoraSequenceInfo,
    HoraCalculator,
    get_hora_calculator,
    calculate_current_hora,
)

# Inauspicious periods
from .inauspicious import (
    InauspiciousPeriod,
    AuspiciousPeriod,
    DailyInauspiciousPeriods,
    InauspiciousPeriodsCalculator,
    get_inauspicious_calculator,
    calculate_inauspicious_periods,
)

# Tarabala
from .tarabala import (
    TarabalaInfo,
    TarabalaCalculator,
    get_tarabala_calculator,
    calculate_tarabala,
)

# Main calculator
from .calculator import (
    GlobalPanchang,
    PersonalizedPanchang,
    PanchangCalculator,
    get_panchang_calculator,
    calculate_global_panchang,
    calculate_personalized_panchang,
)

# Activity recommendations
from .activities import (
    ActivityRecommendations,
    compute_activity_recommendations,
    get_tithi_activities,
    get_nakshatra_activities,
    is_pushya_yoga,
)

__all__ = [
    # Constants
    "TITHI_NAMES",
    "TITHI_FAVORABILITY",
    "NAKSHATRA_NAMES",
    "NAKSHATRA_LORDS",
    "NAKSHATRA_FAVORABILITY",
    "YOGA_NAMES",
    "YOGA_FAVORABILITY",
    "CRITICAL_AVOID_YOGAS",
    "MOVABLE_KARANA_NAMES",
    "FIXED_KARANA_NAMES",
    "ALL_KARANA_NAMES",
    "KARANA_FAVORABILITY",
    "VISHTI_KARANA_INDEX",
    "TARABALA_NAMES",
    "TARABALA_FAVORABILITY",
    "FAVORABLE_TARAS",
    "CRITICAL_AVOID_TARAS",
    "HORA_SEQUENCE",
    "DAY_RULERS",
    "WEEKDAY_NAMES",
    "HORA_FAVORABILITY",
    "RAHU_KAAL_SLOTS",
    "YAMAGANDA_SLOTS",
    "GULIKA_SLOTS",
    "LUNAR_MONTH_NAMES",
    "PAKSHA_NAMES",
    "RASI_NAMES",
    "RASI_NAMES_ENGLISH",
    # Sun times
    "SunTimes",
    "SunTimesCalculator",
    "get_sun_times_calculator",
    "calculate_sun_times",
    # Tithi
    "TithiInfo",
    "TithiCalculator",
    "get_tithi_calculator",
    "calculate_tithi",
    # Nakshatra
    "NakshatraInfo",
    "NakshatraCalculator",
    "get_nakshatra_calculator",
    "calculate_nakshatra",
    # Yoga
    "YogaInfo",
    "YogaCalculator",
    "get_yoga_calculator",
    "calculate_yoga",
    # Karana
    "KaranaInfo",
    "KaranaCalculator",
    "get_karana_calculator",
    "calculate_karana",
    # Hora
    "HoraInfo",
    "HoraSequenceInfo",
    "HoraCalculator",
    "get_hora_calculator",
    "calculate_current_hora",
    # Inauspicious periods
    "InauspiciousPeriod",
    "AuspiciousPeriod",
    "DailyInauspiciousPeriods",
    "InauspiciousPeriodsCalculator",
    "get_inauspicious_calculator",
    "calculate_inauspicious_periods",
    # Tarabala
    "TarabalaInfo",
    "TarabalaCalculator",
    "get_tarabala_calculator",
    "calculate_tarabala",
    # Main calculator
    "GlobalPanchang",
    "PersonalizedPanchang",
    "PanchangCalculator",
    "get_panchang_calculator",
    "calculate_global_panchang",
    "calculate_personalized_panchang",
    # Activity recommendations
    "ActivityRecommendations",
    "compute_activity_recommendations",
    "get_tithi_activities",
    "get_nakshatra_activities",
    "is_pushya_yoga",
]
