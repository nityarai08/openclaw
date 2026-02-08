"""
Activity Recommendations based on Panchang Elements.

Classical Vedic astrology recommends specific activities based on
tithi, nakshatra, yoga, karana, and weekday.

Sources:
- Muhurta Chintamani
- Brihat Samhita (Varahamihira)
- Dharmasindhu
- Traditional Panchanga practices

Note: Only well-established, widely-agreed-upon recommendations are included.
Uncertain or regionally-varying recommendations are excluded for accuracy.
"""

import logging
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# =============================================================================
# TITHI-BASED ACTIVITIES
# =============================================================================
# Classical sources agree on these tithi-activity associations

TITHI_FAVORABLE_ACTIVITIES: Dict[int, List[str]] = {
    # Shukla Paksha (1-15)
    1: ["Starting new ventures", "Initiations"],  # Pratipada
    2: ["Laying foundation", "Travel"],  # Dwitiya
    3: ["Hair cutting", "Shaving", "Agriculture"],  # Tritiya - very auspicious
    5: ["Education", "Learning", "Writing"],  # Panchami
    6: ["Medical treatment"],  # Shashthi
    7: ["Vehicle purchase", "Travel"],  # Saptami
    10: ["Government work", "Legal matters"],  # Dashami
    11: ["Fasting", "Spiritual practices", "Meditation"],  # Ekadashi
    12: ["Charity", "Donations"],  # Dwadashi
    13: ["Friendship", "Socializing"],  # Trayodashi
    15: ["Religious ceremonies", "Buying gold", "Celebrations"],  # Purnima
}

TITHI_UNFAVORABLE_ACTIVITIES: Dict[int, List[str]] = {
    4: ["Auspicious ceremonies"],  # Chaturthi (Rikta tithi)
    8: ["New ventures", "Long journeys"],  # Ashtami (Rikta tithi)
    9: ["Celebrations"],  # Navami
    14: ["Auspicious beginnings"],  # Chaturdashi (Rikta tithi)
    30: ["All auspicious activities"],  # Amavasya
}

# =============================================================================
# NAKSHATRA-BASED ACTIVITIES
# =============================================================================
# These are well-established nakshatra-activity associations from classical texts

# Nakshatra categories by nature (Muhurta Chintamani)
DHRUVA_NAKSHATRAS = [3, 11, 20, 25]  # Fixed/Stable: Rohini, Uttara Phalguni, Uttara Ashadha, Uttara Bhadrapada
CHARA_NAKSHATRAS = [6, 14, 23, 26]  # Movable: Punarvasu, Swati, Shatabhisha, Revati
UGRA_NAKSHATRAS = [1, 18, 17, 5]  # Fierce: Bharani, Mula, Jyeshtha, Ardra
KSHIPRA_NAKSHATRAS = [0, 7, 12]  # Swift: Ashwini, Pushya, Hasta
MRIDU_NAKSHATRAS = [4, 13, 16, 10]  # Soft/Tender: Mrigashira, Chitra, Anuradha, Purva Phalguni

NAKSHATRA_FAVORABLE_ACTIVITIES: Dict[int, List[str]] = {
    # Ashwini (0) - Swift healing
    0: ["Medical treatment", "Quick actions", "Starting medicines"],
    # Rohini (3) - Growth and beauty
    3: ["Buying property", "Agriculture", "Marriage discussions"],
    # Pushya (7) - Most auspicious for all beginnings
    7: ["All auspicious activities", "New ventures", "Buying precious items"],
    # Hasta (12) - Skilled work
    12: ["Artisan work", "Crafts", "Learning skills"],
    # Uttara Phalguni (11) - Patronage
    11: ["Marriage", "Partnerships", "Contracts"],
    # Uttara Ashadha (20) - Victory
    20: ["Important decisions", "Starting projects"],
    # Revati (26) - Completion
    26: ["Completing projects", "Journeys"],
}

NAKSHATRA_UNFAVORABLE_ACTIVITIES: Dict[int, List[str]] = {
    # Bharani (1) - Transformation/death
    1: ["Auspicious ceremonies", "New beginnings"],
    # Ardra (5) - Storms
    5: ["Travel", "New ventures"],
    # Ashlesha (8) - Serpent energy
    8: ["Trusting strangers", "Signing contracts"],
    # Mula (18) - Destruction (Gandanta)
    18: ["Major decisions", "New projects"],
    # Jyeshtha (17) - Elder challenges
    17: ["Marriage", "Partnerships"],
}

# =============================================================================
# YOGA-BASED ACTIVITIES
# =============================================================================
# Critical avoid yogas are well-documented

YOGA_CRITICAL_AVOID = {16, 26}  # Vyatipata, Vaidhriti

YOGA_FAVORABLE_ACTIVITIES: Dict[int, List[str]] = {
    1: ["Love matters", "Relationships"],  # Priti
    2: ["Health matters", "Long-term plans"],  # Ayushman
    3: ["Auspicious ceremonies"],  # Saubhagya
    15: ["Starting ventures", "Achievements"],  # Siddhi
    19: ["Spiritual practices", "Religious work"],  # Shiva
    20: ["Completing tasks"],  # Siddha
    22: ["All auspicious activities"],  # Shubha
}

YOGA_UNFAVORABLE_ACTIVITIES: Dict[int, List[str]] = {
    0: ["New ventures"],  # Vishkumbha
    5: ["Important decisions"],  # Atiganda
    8: ["Travel", "Journeys"],  # Shula
    9: ["New beginnings"],  # Ganda
    12: ["Major decisions"],  # Vyaghata
    16: ["All important activities"],  # Vyatipata - CRITICAL
    18: ["Starting projects"],  # Parigha
    26: ["All important activities"],  # Vaidhriti - CRITICAL
}

# =============================================================================
# KARANA-BASED ACTIVITIES
# =============================================================================

KARANA_FAVORABLE_ACTIVITIES: Dict[int, List[str]] = {
    0: ["Auspicious work"],  # Bava
    2: ["Partnerships", "Agreements"],  # Kaulava
    5: ["Business", "Trade"],  # Vanija
}

KARANA_UNFAVORABLE_ACTIVITIES: Dict[int, List[str]] = {
    6: ["All auspicious activities", "New ventures"],  # Vishti/Bhadra
}

# =============================================================================
# WEEKDAY-BASED ACTIVITIES
# =============================================================================
# Well-established day-activity associations

WEEKDAY_FAVORABLE_ACTIVITIES: Dict[int, List[str]] = {
    0: ["Meditation", "Family matters"],  # Monday - Moon
    1: ["Competitive activities", "Sports"],  # Tuesday - Mars
    2: ["Communication", "Business deals"],  # Wednesday - Mercury
    3: ["Education", "Spirituality", "Financial planning"],  # Thursday - Jupiter
    4: ["Arts", "Creativity", "Social events"],  # Friday - Venus
    5: ["Discipline", "Routine work", "Organizing"],  # Saturday - Saturn
    6: ["Government work", "Authority matters"],  # Sunday - Sun
}

WEEKDAY_UNFAVORABLE_ACTIVITIES: Dict[int, List[str]] = {
    1: ["Financial decisions requiring calm"],  # Tuesday - Mars aggression
    5: ["Celebrations", "New ventures"],  # Saturday - Saturn restrictions
}


# =============================================================================
# UNIVERSAL ACTIVITIES
# =============================================================================
# Activities that are generally safe on most days

UNIVERSAL_FAVORABLE: List[str] = [
    "Meditation",
    "Routine work",
    "Prayers",
]

UNIVERSAL_UNFAVORABLE_ON_CRITICAL: List[str] = [
    "Major decisions",
    "New ventures",
    "Signing contracts",
    "Long journeys",
]


@dataclass
class ActivityRecommendations:
    """Computed activity recommendations."""
    favorable: List[str]
    unfavorable: List[str]
    critical_warnings: List[str]
    confidence: str  # "high", "medium", "low"


def compute_activity_recommendations(
    tithi_number: int,
    nakshatra_index: int,
    yoga_index: int,
    karana_index: int,
    weekday: int,
    day_quality_score: float,
    is_rahu_kaal_now: bool = False,
    is_vishti_karana: bool = False,
    is_gandanta: bool = False,
    is_critical_yoga: bool = False,
) -> ActivityRecommendations:
    """
    Compute activity recommendations based on panchang elements.
    
    Args:
        tithi_number: Tithi number (1-30)
        nakshatra_index: Nakshatra index (0-26)
        yoga_index: Yoga index (0-26)
        karana_index: Karana index (0-10)
        weekday: Day of week (0=Monday, 6=Sunday)
        day_quality_score: Overall day score (0-100)
        is_rahu_kaal_now: Whether current time is in Rahu Kaal
        is_vishti_karana: Whether Vishti (Bhadra) karana is active
        is_gandanta: Whether in Gandanta nakshatra
        is_critical_yoga: Whether critical avoid yoga (Vyatipata, Vaidhriti)
    
    Returns:
        ActivityRecommendations with favorable and unfavorable lists
    """
    favorable: Set[str] = set()
    unfavorable: Set[str] = set()
    warnings: List[str] = []
    
    # Start with universal favorable
    favorable.update(UNIVERSAL_FAVORABLE)
    
    # Collect tithi-based recommendations
    if tithi_number in TITHI_FAVORABLE_ACTIVITIES:
        favorable.update(TITHI_FAVORABLE_ACTIVITIES[tithi_number])
    if tithi_number in TITHI_UNFAVORABLE_ACTIVITIES:
        unfavorable.update(TITHI_UNFAVORABLE_ACTIVITIES[tithi_number])
    
    # Collect nakshatra-based recommendations
    if nakshatra_index in NAKSHATRA_FAVORABLE_ACTIVITIES:
        favorable.update(NAKSHATRA_FAVORABLE_ACTIVITIES[nakshatra_index])
    if nakshatra_index in NAKSHATRA_UNFAVORABLE_ACTIVITIES:
        unfavorable.update(NAKSHATRA_UNFAVORABLE_ACTIVITIES[nakshatra_index])
    
    # Collect yoga-based recommendations
    if yoga_index in YOGA_FAVORABLE_ACTIVITIES:
        favorable.update(YOGA_FAVORABLE_ACTIVITIES[yoga_index])
    if yoga_index in YOGA_UNFAVORABLE_ACTIVITIES:
        unfavorable.update(YOGA_UNFAVORABLE_ACTIVITIES[yoga_index])
    
    # Collect karana-based recommendations
    if karana_index in KARANA_FAVORABLE_ACTIVITIES:
        favorable.update(KARANA_FAVORABLE_ACTIVITIES[karana_index])
    if karana_index in KARANA_UNFAVORABLE_ACTIVITIES:
        unfavorable.update(KARANA_UNFAVORABLE_ACTIVITIES[karana_index])
    
    # Collect weekday-based recommendations
    if weekday in WEEKDAY_FAVORABLE_ACTIVITIES:
        favorable.update(WEEKDAY_FAVORABLE_ACTIVITIES[weekday])
    if weekday in WEEKDAY_UNFAVORABLE_ACTIVITIES:
        unfavorable.update(WEEKDAY_UNFAVORABLE_ACTIVITIES[weekday])
    
    # Apply critical conditions
    if is_critical_yoga:
        unfavorable.update(UNIVERSAL_UNFAVORABLE_ON_CRITICAL)
        warnings.append("Critical yoga - avoid major decisions")
    
    if is_vishti_karana:
        unfavorable.update(["New ventures", "Auspicious ceremonies"])
        warnings.append("Vishti (Bhadra) karana - avoid new beginnings")
    
    if is_gandanta:
        unfavorable.update(["Major decisions", "Starting projects"])
        warnings.append("Gandanta nakshatra - junction point")
    
    if is_rahu_kaal_now:
        unfavorable.update(["Starting important work", "New ventures"])
        warnings.append("Rahu Kaal - inauspicious time")
    
    # Low day score means general caution
    if day_quality_score < 40:
        unfavorable.update(["High-stakes decisions", "New ventures"])
        # Remove ambitious favorable activities
        favorable.discard("Starting ventures")
        favorable.discard("New ventures")
        favorable.discard("All auspicious activities")
        favorable.add("Rest and reflection")
    
    # Remove conflicts (if something is both favorable and unfavorable, remove from favorable)
    favorable = favorable - unfavorable
    
    # Ensure we always have some recommendations
    if len(favorable) < 2:
        favorable.update(["Meditation", "Routine work"])
    
    if len(unfavorable) < 1:
        unfavorable.add("Rash decisions")
    
    # Determine confidence based on data quality
    confidence = "high"
    if is_critical_yoga or is_vishti_karana:
        confidence = "high"  # We're confident about critical conditions
    elif day_quality_score < 40 or day_quality_score > 80:
        confidence = "high"  # Clear good/bad days
    else:
        confidence = "medium"  # Average days have more uncertainty
    
    return ActivityRecommendations(
        favorable=sorted(list(favorable))[:6],  # Limit to top 6
        unfavorable=sorted(list(unfavorable))[:4],  # Limit to top 4
        critical_warnings=warnings,
        confidence=confidence,
    )


def get_tithi_activities(tithi_number: int) -> Tuple[List[str], List[str]]:
    """Get activities for a specific tithi."""
    favorable = TITHI_FAVORABLE_ACTIVITIES.get(tithi_number, [])
    unfavorable = TITHI_UNFAVORABLE_ACTIVITIES.get(tithi_number, [])
    return favorable, unfavorable


def get_nakshatra_activities(nakshatra_index: int) -> Tuple[List[str], List[str]]:
    """Get activities for a specific nakshatra."""
    favorable = NAKSHATRA_FAVORABLE_ACTIVITIES.get(nakshatra_index, [])
    unfavorable = NAKSHATRA_UNFAVORABLE_ACTIVITIES.get(nakshatra_index, [])
    return favorable, unfavorable


def is_pushya_yoga(nakshatra_index: int, day_quality_score: float) -> bool:
    """
    Check if this is effectively a 'Pushya Yoga' - most auspicious combination.
    
    Pushya nakshatra with high day quality is exceptional for all activities.
    """
    return nakshatra_index == 7 and day_quality_score >= 70
