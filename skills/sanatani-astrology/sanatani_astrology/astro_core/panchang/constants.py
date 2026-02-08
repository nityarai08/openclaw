"""
Panchang Constants - Verified names, mappings, and favorability ratings.

All constants are sourced from classical texts and cross-referenced with
DrikPanchang for accuracy.
"""

from typing import Dict, List, Tuple

# =============================================================================
# TITHI (Lunar Day) - 30 Tithis per lunar month
# =============================================================================

TITHI_NAMES: List[str] = [
    "Pratipada",      # 1
    "Dwitiya",        # 2
    "Tritiya",        # 3
    "Chaturthi",      # 4
    "Panchami",       # 5
    "Shashthi",       # 6
    "Saptami",        # 7
    "Ashtami",        # 8
    "Navami",         # 9
    "Dashami",        # 10
    "Ekadashi",       # 11
    "Dwadashi",       # 12
    "Trayodashi",     # 13
    "Chaturdashi",    # 14
    "Purnima",        # 15 (Full Moon)
    "Pratipada",      # 16 (Krishna Paksha starts)
    "Dwitiya",        # 17
    "Tritiya",        # 18
    "Chaturthi",      # 19
    "Panchami",       # 20
    "Shashthi",       # 21
    "Saptami",        # 22
    "Ashtami",        # 23
    "Navami",         # 24
    "Dashami",        # 25
    "Ekadashi",       # 26
    "Dwadashi",       # 27
    "Trayodashi",     # 28
    "Chaturdashi",    # 29
    "Amavasya",       # 30 (New Moon)
]

# Tithi favorability (0.0 - 1.0)
TITHI_FAVORABILITY: Dict[int, float] = {
    1: 0.75,   # Pratipada - new beginnings
    2: 0.70,   # Dwitiya - partnerships
    3: 0.85,   # Tritiya - very auspicious
    4: 0.55,   # Chaturthi - Ganesh (mixed)
    5: 0.90,   # Panchami - very favorable
    6: 0.70,   # Shashthi - good
    7: 0.80,   # Saptami - favorable
    8: 0.45,   # Ashtami - challenging (Rikta tithi)
    9: 0.60,   # Navami - moderate
    10: 0.80,  # Dashami - favorable
    11: 0.90,  # Ekadashi - very auspicious (spiritual)
    12: 0.70,  # Dwadashi - good
    13: 0.65,  # Trayodashi - moderate
    14: 0.40,  # Chaturdashi - challenging (Rikta tithi)
    15: 0.95,  # Purnima - most auspicious
    16: 0.70,  # Krishna Pratipada
    17: 0.65,
    18: 0.60,
    19: 0.50,
    20: 0.60,
    21: 0.65,
    22: 0.55,
    23: 0.40,  # Krishna Ashtami - challenging
    24: 0.50,
    25: 0.55,
    26: 0.85,  # Krishna Ekadashi - spiritual
    27: 0.60,
    28: 0.50,
    29: 0.30,  # Krishna Chaturdashi - very challenging
    30: 0.25,  # Amavasya - most challenging
}

# Rikta (empty) tithis - generally inauspicious for beginnings
RIKTA_TITHIS: List[int] = [4, 8, 9, 14, 19, 23, 24, 29]

# =============================================================================
# NAKSHATRA (Lunar Mansion) - 27 Nakshatras
# =============================================================================

NAKSHATRA_NAMES: List[str] = [
    "Ashwini",           # 0
    "Bharani",           # 1
    "Krittika",          # 2
    "Rohini",            # 3
    "Mrigashira",        # 4
    "Ardra",             # 5
    "Punarvasu",         # 6
    "Pushya",            # 7
    "Ashlesha",          # 8
    "Magha",             # 9
    "Purva Phalguni",    # 10
    "Uttara Phalguni",   # 11
    "Hasta",             # 12
    "Chitra",            # 13
    "Swati",             # 14
    "Vishakha",          # 15
    "Anuradha",          # 16
    "Jyeshtha",          # 17
    "Mula",              # 18
    "Purva Ashadha",     # 19
    "Uttara Ashadha",    # 20
    "Shravana",          # 21
    "Dhanishta",         # 22
    "Shatabhisha",       # 23
    "Purva Bhadrapada",  # 24
    "Uttara Bhadrapada", # 25
    "Revati",            # 26
]

# Nakshatra lords (for dasha calculations)
NAKSHATRA_LORDS: List[str] = [
    "Ketu",      # Ashwini
    "Venus",     # Bharani
    "Sun",       # Krittika
    "Moon",      # Rohini
    "Mars",      # Mrigashira
    "Rahu",      # Ardra
    "Jupiter",   # Punarvasu
    "Saturn",    # Pushya
    "Mercury",   # Ashlesha
    "Ketu",      # Magha
    "Venus",     # Purva Phalguni
    "Sun",       # Uttara Phalguni
    "Moon",      # Hasta
    "Mars",      # Chitra
    "Rahu",      # Swati
    "Jupiter",   # Vishakha
    "Saturn",    # Anuradha
    "Mercury",   # Jyeshtha
    "Ketu",      # Mula
    "Venus",     # Purva Ashadha
    "Sun",       # Uttara Ashadha
    "Moon",      # Shravana
    "Mars",      # Dhanishta
    "Rahu",      # Shatabhisha
    "Jupiter",   # Purva Bhadrapada
    "Saturn",    # Uttara Bhadrapada
    "Mercury",   # Revati
]

# Nakshatra favorability (general, not personalized)
NAKSHATRA_FAVORABILITY: Dict[int, float] = {
    0: 0.80,   # Ashwini - swift, healing
    1: 0.55,   # Bharani - transformation
    2: 0.65,   # Krittika - purification
    3: 0.90,   # Rohini - growth, beauty (excellent)
    4: 0.70,   # Mrigashira - gentle
    5: 0.50,   # Ardra - storms, renewal
    6: 0.80,   # Punarvasu - renewal
    7: 0.95,   # Pushya - most auspicious
    8: 0.40,   # Ashlesha - serpent, cunning
    9: 0.75,   # Magha - royal, ancestral
    10: 0.70,  # Purva Phalguni - pleasure
    11: 0.80,  # Uttara Phalguni - patronage
    12: 0.75,  # Hasta - skillful
    13: 0.70,  # Chitra - artistic
    14: 0.60,  # Swati - independence
    15: 0.65,  # Vishakha - determination
    16: 0.70,  # Anuradha - friendship
    17: 0.50,  # Jyeshtha - protection (challenging)
    18: 0.45,  # Mula - root, destruction (Gandanta)
    19: 0.70,  # Purva Ashadha - invincible
    20: 0.80,  # Uttara Ashadha - victory
    21: 0.75,  # Shravana - listening
    22: 0.60,  # Dhanishta - wealth
    23: 0.55,  # Shatabhisha - hundred healers
    24: 0.60,  # Purva Bhadrapada - purification
    25: 0.75,  # Uttara Bhadrapada - wisdom
    26: 0.85,  # Revati - prosperity, completion
}

# Gandanta nakshatras (junction points - inauspicious for beginnings)
# These are at water-fire sign junctions
GANDANTA_NAKSHATRAS: List[int] = [8, 17, 26]  # Ashlesha, Jyeshtha, Revati (end)
GANDANTA_NAKSHATRAS_START: List[int] = [0, 9, 18]  # Ashwini, Magha, Mula (start)

# =============================================================================
# YOGA (Sun + Moon combination) - 27 Yogas
# =============================================================================

YOGA_NAMES: List[str] = [
    "Vishkumbha",   # 0 - Poison pot (inauspicious)
    "Priti",        # 1 - Love
    "Ayushman",     # 2 - Long life
    "Saubhagya",    # 3 - Good fortune
    "Shobhana",     # 4 - Splendor
    "Atiganda",     # 5 - Great knot (inauspicious)
    "Sukarma",      # 6 - Good deeds
    "Dhriti",       # 7 - Steadiness
    "Shula",        # 8 - Spear (inauspicious)
    "Ganda",        # 9 - Knot (inauspicious)
    "Vriddhi",      # 10 - Growth
    "Dhruva",       # 11 - Fixed, stable
    "Vyaghata",     # 12 - Calamity (inauspicious)
    "Harshana",     # 13 - Joy
    "Vajra",        # 14 - Thunderbolt (mixed)
    "Siddhi",       # 15 - Accomplishment
    "Vyatipata",    # 16 - Great fall (VERY inauspicious)
    "Variyan",      # 17 - Comfort
    "Parigha",      # 18 - Iron bar (inauspicious)
    "Shiva",        # 19 - Auspicious
    "Siddha",       # 20 - Accomplished
    "Sadhya",       # 21 - Achievable
    "Shubha",       # 22 - Auspicious
    "Shukla",       # 23 - Bright
    "Brahma",       # 24 - Creator
    "Indra",        # 25 - King of gods
    "Vaidhriti",    # 26 - Great support (VERY inauspicious)
]

YOGA_FAVORABILITY: Dict[int, float] = {
    0: 0.30,   # Vishkumbha - inauspicious
    1: 0.75,   # Priti
    2: 0.85,   # Ayushman
    3: 0.90,   # Saubhagya
    4: 0.85,   # Shobhana
    5: 0.35,   # Atiganda - inauspicious
    6: 0.80,   # Sukarma
    7: 0.75,   # Dhriti
    8: 0.35,   # Shula - inauspicious
    9: 0.35,   # Ganda - inauspicious
    10: 0.80,  # Vriddhi
    11: 0.85,  # Dhruva
    12: 0.30,  # Vyaghata - inauspicious
    13: 0.80,  # Harshana
    14: 0.50,  # Vajra - mixed
    15: 0.95,  # Siddhi - excellent
    16: 0.15,  # Vyatipata - AVOID
    17: 0.75,  # Variyan
    18: 0.40,  # Parigha - inauspicious
    19: 0.90,  # Shiva - excellent
    20: 0.90,  # Siddha - excellent
    21: 0.85,  # Sadhya
    22: 0.95,  # Shubha - excellent
    23: 0.80,  # Shukla
    24: 0.90,  # Brahma
    25: 0.85,  # Indra
    26: 0.15,  # Vaidhriti - AVOID
}

# Critical avoid yogas (very inauspicious for any important work)
CRITICAL_AVOID_YOGAS: List[int] = [16, 26]  # Vyatipata, Vaidhriti

# =============================================================================
# KARANA (Half-Tithi) - 11 Karanas (7 movable + 4 fixed)
# =============================================================================

# 7 Movable karanas (repeat in cycle)
MOVABLE_KARANA_NAMES: List[str] = [
    "Bava",     # 0
    "Balava",   # 1
    "Kaulava",  # 2
    "Taitila",  # 3
    "Garaja",   # 4
    "Vanija",   # 5
    "Vishti",   # 6 - Bhadra (INAUSPICIOUS)
]

# 4 Fixed karanas (occur once per lunar month)
FIXED_KARANA_NAMES: List[str] = [
    "Shakuni",      # 7
    "Chatushpada",  # 8
    "Naga",         # 9
    "Kimstughna",   # 10
]

ALL_KARANA_NAMES: List[str] = MOVABLE_KARANA_NAMES + FIXED_KARANA_NAMES

KARANA_FAVORABILITY: Dict[int, float] = {
    0: 0.80,   # Bava - auspicious
    1: 0.75,   # Balava - strength
    2: 0.80,   # Kaulava - partnerships
    3: 0.70,   # Taitila - persistence
    4: 0.70,   # Garaja - creativity
    5: 0.75,   # Vanija - commerce
    6: 0.20,   # Vishti/Bhadra - AVOID
    7: 0.50,   # Shakuni - cunning
    8: 0.60,   # Chatushpada - stable
    9: 0.60,   # Naga - mystical
    10: 0.50,  # Kimstughna - difficult
}

# Vishti (Bhadra) karana - highly inauspicious
VISHTI_KARANA_INDEX: int = 6

# =============================================================================
# TARABALA (Star Compatibility) - 9 Tara positions
# =============================================================================
# Traditional Vedic order: The 5th tara (index 4) is the death star (Naidhana/Pratyari)
# This follows classical texts like Muhurta Chintamani and Brihat Samhita

TARABALA_NAMES: List[str] = [
    "Janma",         # 0 - Birth star (neutral, mixed results)
    "Sampat",        # 1 - Wealth (excellent)
    "Vipat",         # 2 - Danger (avoid)
    "Kshema",        # 3 - Well-being (good)
    "Naidhana",      # 4 - Death/Pratyari (CRITICAL AVOID - 5th tara)
    "Sadhaka",       # 5 - Accomplishment (excellent)
    "Vadha",         # 6 - Destruction (avoid)
    "Mitra",         # 7 - Friend (excellent)
    "Parama Mitra",  # 8 - Best friend (most favorable)
]

TARABALA_FAVORABILITY: Dict[int, float] = {
    0: 0.45,   # Janma - neutral/mixed (not as bad as vipat/vadha)
    1: 0.90,   # Sampat - excellent
    2: 0.35,   # Vipat - avoid
    3: 0.80,   # Kshema - good
    4: 0.15,   # Naidhana - CRITICAL AVOID (death star)
    5: 0.90,   # Sadhaka - excellent
    6: 0.35,   # Vadha - avoid (destruction)
    7: 0.85,   # Mitra - excellent
    8: 0.95,   # Parama Mitra - best
}

FAVORABLE_TARAS: List[int] = [1, 3, 5, 7, 8]  # Sampat, Kshema, Sadhaka, Mitra, Parama Mitra
CRITICAL_AVOID_TARAS: List[int] = [4]  # Naidhana (death star at 5th position)

# =============================================================================
# HORA (Planetary Hours) - Chaldean order
# =============================================================================

# Chaldean order (descending by geocentric distance)
HORA_SEQUENCE: List[str] = [
    "Saturn",
    "Jupiter",
    "Mars",
    "Sun",
    "Venus",
    "Mercury",
    "Moon",
]

# Day rulers (first hora of each day)
DAY_RULERS: Dict[int, str] = {
    0: "Moon",     # Monday
    1: "Mars",     # Tuesday
    2: "Mercury",  # Wednesday
    3: "Jupiter",  # Thursday
    4: "Venus",    # Friday
    5: "Saturn",   # Saturday
    6: "Sun",      # Sunday
}

WEEKDAY_NAMES: List[str] = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

# Hora favorability (general)
HORA_FAVORABILITY: Dict[str, float] = {
    "Sun": 0.75,      # Authority, government
    "Moon": 0.70,     # Emotions, travel
    "Mars": 0.50,     # Energy, aggression (mixed)
    "Mercury": 0.85,  # Communication, business (excellent)
    "Jupiter": 0.95,  # Spirituality, education (most auspicious)
    "Venus": 0.80,    # Love, arts, luxury
    "Saturn": 0.45,   # Discipline, structure (challenging)
}

# =============================================================================
# INAUSPICIOUS PERIODS - Slots based on weekday
# =============================================================================

# Rahu Kaal slots (1-8) for each weekday (0=Monday, 6=Sunday)
# Day is divided into 8 equal parts from sunrise to sunset
RAHU_KAAL_SLOTS: Dict[int, int] = {
    0: 2,  # Monday: 2nd slot (7:30-9:00 AM for 6AM sunrise)
    1: 7,  # Tuesday: 7th slot (3:00-4:30 PM)
    2: 5,  # Wednesday: 5th slot (12:00-1:30 PM)
    3: 6,  # Thursday: 6th slot (1:30-3:00 PM)
    4: 4,  # Friday: 4th slot (10:30-12:00 PM)
    5: 3,  # Saturday: 3rd slot (9:00-10:30 AM)
    6: 8,  # Sunday: 8th slot (4:30-6:00 PM)
}

# Yamagandam slots (per drikpanchang.com traditional method)
# Yamaganda follows: Sun=5, Mon=4, Tue=3, Wed=2, Thu=1, Fri=7, Sat=6
YAMAGANDA_SLOTS: Dict[int, int] = {
    0: 4,  # Monday
    1: 3,  # Tuesday
    2: 2,  # Wednesday
    3: 1,  # Thursday
    4: 7,  # Friday (was 1, corrected to 7)
    5: 6,  # Saturday
    6: 5,  # Sunday
}

# Gulika Kaal slots (per drikpanchang.com traditional method)
# Gulika follows: Sun=7, Mon=6, Tue=5, Wed=4, Thu=3, Fri=2, Sat=1
GULIKA_SLOTS: Dict[int, int] = {
    0: 6,  # Monday
    1: 5,  # Tuesday
    2: 4,  # Wednesday
    3: 3,  # Thursday
    4: 2,  # Friday (was 3, corrected to 2)
    5: 1,  # Saturday
    6: 7,  # Sunday
}

# =============================================================================
# LUNAR MONTHS
# =============================================================================

LUNAR_MONTH_NAMES: List[str] = [
    "Chaitra",       # 0 - Aries
    "Vaishakha",     # 1 - Taurus
    "Jyeshtha",      # 2 - Gemini
    "Ashadha",       # 3 - Cancer
    "Shravana",      # 4 - Leo
    "Bhadrapada",    # 5 - Virgo
    "Ashwina",       # 6 - Libra
    "Kartika",       # 7 - Scorpio
    "Margashirsha",  # 8 - Sagittarius
    "Pausha",        # 9 - Capricorn
    "Magha",         # 10 - Aquarius
    "Phalguna",      # 11 - Pisces
]

# =============================================================================
# PAKSHA (Lunar Fortnight)
# =============================================================================

PAKSHA_NAMES: Dict[str, str] = {
    "shukla": "Shukla Paksha",   # Waxing moon (bright fortnight)
    "krishna": "Krishna Paksha", # Waning moon (dark fortnight)
}

# =============================================================================
# RASI (Zodiac Signs) - for reference
# =============================================================================

RASI_NAMES: List[str] = [
    "Mesha",      # 0 - Aries
    "Vrishabha",  # 1 - Taurus
    "Mithuna",    # 2 - Gemini
    "Karka",      # 3 - Cancer
    "Simha",      # 4 - Leo
    "Kanya",      # 5 - Virgo
    "Tula",       # 6 - Libra
    "Vrishchika", # 7 - Scorpio
    "Dhanu",      # 8 - Sagittarius
    "Makara",     # 9 - Capricorn
    "Kumbha",     # 10 - Aquarius
    "Meena",      # 11 - Pisces
]

RASI_NAMES_ENGLISH: List[str] = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

# =============================================================================
# CALCULATION CONSTANTS
# =============================================================================

# Degrees per tithi (Moon-Sun elongation)
DEGREES_PER_TITHI: float = 12.0

# Degrees per nakshatra
DEGREES_PER_NAKSHATRA: float = 360.0 / 27  # 13.333...

# Degrees per yoga
DEGREES_PER_YOGA: float = 360.0 / 27  # 13.333...

# Degrees per pada (quarter of nakshatra)
DEGREES_PER_PADA: float = DEGREES_PER_NAKSHATRA / 4  # 3.333...

# Average daily motion
MOON_MEAN_DAILY_MOTION: float = 13.176  # degrees per day
SUN_MEAN_DAILY_MOTION: float = 0.9856   # degrees per day
