"""
Kundali Query API - Contract Interface

This module defines the contract that all kundali generators must implement.
The rule evaluation engine can ONLY use this interface to query kundali data.

This ensures:
1. Decoupling between kundali structure and rule engine
2. Type safety for all queries
3. Clear documentation of what operations are supported
4. Ability to validate rules against API capabilities
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


# ============================================================================
# ENUMS - Standardized values
# ============================================================================

class Dignity(Enum):
    """Planetary dignity states"""
    EXALTED = "exalted"
    EXALTATION = "exaltation"  # Alias
    OWN = "own"
    MOOLATRIKONA = "moolatrikona"
    MULATRIKONA = "mulatrikona"
    NEUTRAL = "neutral"
    FRIENDLY = "friendly"
    ENEMY = "enemy"
    DEBILITATED = "debilitated"
    DEBILITATION = "debilitation"  # Alias

    @classmethod
    def normalize(cls, value: str) -> Optional['Dignity']:
        """Normalize string to Dignity enum"""
        try:
            val = value.lower()
            # Map aliases to canonical
            if val == "exaltation": return cls.EXALTED
            if val == "debilitation": return cls.DEBILITATED
            if val == "mulatrikona": return cls.MOOLATRIKONA
            return cls(val)
        except (ValueError, AttributeError):
            return None


class AspectType(Enum):
    """Types of planetary aspects"""
    CONJUNCTION = "conjunction"
    OPPOSITION = "opposition"
    TRINE = "trine"
    SQUARE = "square"
    SEXTILE = "sextile"


class ParivartanaType(Enum):
    """Types of Parivartana (mutual exchange) yogas"""
    MAHA_PARIVARTANA = "maha_parivartana"  # Between kendra/trikona lords
    DAINYA_PARIVARTANA = "dainya_parivartana"  # Involving dusthana
    KHALA_PARIVARTANA = "khala_parivartana"  # Others


class RelationshipType(Enum):
    """Five-fold (Panchadha) planetary relationship"""
    GREAT_FRIEND = "great_friend"
    FRIEND = "friend"
    NEUTRAL = "neutral"
    ENEMY = "enemy"
    GREAT_ENEMY = "great_enemy"


class KarakaType(Enum):
    """Jaimini Chara Karakas"""
    ATMAKARAKA = "atma"
    AMATYAKARAKA = "amatya"
    BHRATRIKARAKA = "bhratri"
    MATRIKARAKA = "matri"
    PUTRAKARAKA = "putra"
    GNATIKARAKA = "gnati"
    DARAKARAKA = "dara"


class SpecialLagnaType(Enum):
    """Special lagnas (reference points)"""
    UPAPADA = "upapada"  # UL
    ARUDHA = "arudha"  # AL
    DARAPADA = "darapada"  # A7
    KARAKAMSA = "karakamsa"
    PRANAPADA = "pranapada"


# ============================================================================
# DATA MODELS - Structured query results
# ============================================================================

@dataclass
class PlanetQuery:
    """Result of querying planet information"""
    name: str
    house: int  # Bhava number 1-12
    sign: str  # Sign name (e.g., "aries", "taurus")
    sign_index: int  # 0-11
    dignity: Dignity
    longitude: float  # Absolute longitude 0-360
    degree_in_sign: float  # Degrees within sign 0-30
    is_combust: bool
    is_retrograde: bool
    nakshatra: str
    nakshatra_index: int  # 0-26
    nakshatra_lord: str

    # Optional fields for specific charts
    navamsa_sign: Optional[str] = None
    navamsa_dignity: Optional[Dignity] = None
    is_vargottama: bool = False


@dataclass
class AspectQuery:
    """Aspect between two planets"""
    planet1: str
    planet2: str
    aspect_type: AspectType
    angle: float  # Angle in degrees
    is_applying: bool = True  # Whether aspect is applying or separating


@dataclass
class HouseQuery:
    """House (bhava) information"""
    number: int  # 1-12
    sign: str
    sign_index: int
    lord: str  # Planet that rules this house
    cusp_longitude: float
    planets_in_house: List[str]
    aspected_by: List[str]  # Planets aspecting this house


@dataclass
class ParivartanaQuery:
    """Mutual exchange between planets"""
    planet1: str
    planet2: str
    planet1_in_house: int
    planet2_in_house: int
    planet1_rules_houses: List[int]
    planet2_rules_houses: List[int]
    exchange_type: ParivartanaType


@dataclass
class DashaQuery:
    """Dasha period information"""
    level: str  # mahadasha/antardasha/pratyantardasha/sookshma/prana
    planet: str
    start_date: datetime
    end_date: datetime
    duration_years: float
    is_current: bool


@dataclass
class AshtakavargaQuery:
    """Ashtakavarga bindu information"""
    planet: str
    house: int
    bindus: int
    sarvashtakavarga: int  # Total bindus for this house


# ============================================================================
# MAIN API CONTRACT
# ============================================================================

class KundaliQueryAPI(ABC):
    """
    Contract that all kundali generators must implement.
    This is the ONLY interface the rule engine can use.

    Design principles:
    1. All queries return structured data (dataclasses), not raw dicts
    2. Methods are read-only (no mutations)
    3. Invalid queries return None, not exceptions
    4. Chart parameter defaults to "D1" (Rasi chart)
    5. Planet/karaka names are normalized to lowercase
    """

    # ============ PLANET QUERIES ============

    @abstractmethod
    def get_planet(self, planet: str, chart: str = "D1") -> Optional[PlanetQuery]:
        """
        Get complete planet information from specified chart.

        Args:
            planet: Planet name or karaka type (e.g., "sun", "atma", "lord_of_10")
            chart: Chart name (D1, D2, D3, D9, D10, D12, D16, D60)

        Returns:
            PlanetQuery with all planet details, or None if not found
        """
        pass

    @abstractmethod
    def get_planets_in_house(self, house: int, chart: str = "D1") -> List[str]:
        """
        Get all planets occupying a specific house.

        Args:
            house: House number 1-12
            chart: Chart name

        Returns:
            List of planet names (lowercase)
        """
        pass

    @abstractmethod
    def is_planet_in_houses(
        self,
        planet: str,
        houses: Set[int],
        chart: str = "D1"
    ) -> bool:
        """
        Check if planet is in any of the specified houses.

        Args:
            planet: Planet name or karaka
            houses: Set of house numbers to check
            chart: Chart name

        Returns:
            True if planet is in any of the houses
        """
        pass

    @abstractmethod
    def get_planets_by_dignity(
        self,
        dignity: Dignity,
        chart: str = "D1"
    ) -> List[str]:
        """
        Get all planets with specified dignity.

        Args:
            dignity: Dignity state to match
            chart: Chart name

        Returns:
            List of planet names matching dignity
        """
        pass

    @abstractmethod
    def is_planet_combust(self, planet: str) -> bool:
        """
        Check if planet is combust (too close to Sun).

        Args:
            planet: Planet name

        Returns:
            True if planet is combust
        """
        pass

    @abstractmethod
    def get_combust_planets(self) -> List[str]:
        """
        Get all combust planets in the chart.

        Returns:
            List of planet names that are combust
        """
        pass

    # ============ HOUSE QUERIES ============

    @abstractmethod
    def get_house(self, house_number: int, chart: str = "D1") -> Optional[HouseQuery]:
        """
        Get complete house information.

        Args:
            house_number: House number 1-12
            chart: Chart name

        Returns:
            HouseQuery with all house details, or None if invalid
        """
        pass

    @abstractmethod
    def get_house_lord(self, house: int, chart: str = "D1") -> Optional[str]:
        """
        Get lord (ruler) of specified house.

        Args:
            house: House number 1-12
            chart: Chart name

        Returns:
            Planet name that rules this house, or None
        """
        pass

    @abstractmethod
    def is_lord_in_house(
        self,
        lord_of: int,
        in_house: int,
        chart: str = "D1"
    ) -> bool:
        """
        Check if lord of house X is positioned in house Y.

        Args:
            lord_of: House whose lord to check (1-12)
            in_house: Target house position (1-12)
            chart: Chart name

        Returns:
            True if lord of house X is in house Y

        Example:
            is_lord_in_house(10, 1)  # Is 10th lord in 1st house?
        """
        pass

    @abstractmethod
    def get_house_cusps(self, chart: str = "D1") -> List[float]:
        """
        Get all 12 house cusp longitudes.

        Args:
            chart: Chart name

        Returns:
            List of 12 cusp longitudes in degrees (0-360)
        """
        pass

    # ============ ASPECT QUERIES ============

    @abstractmethod
    def get_aspects(
        self,
        planet: Optional[str] = None,
        chart: str = "D1"
    ) -> List[AspectQuery]:
        """
        Get aspects involving specified planet, or all aspects if None.

        Args:
            planet: Planet name to filter by, or None for all aspects
            chart: Chart name

        Returns:
            List of AspectQuery objects
        """
        pass

    @abstractmethod
    def has_aspect(
        self,
        planet1: str,
        planet2: str,
        aspect_type: Optional[AspectType] = None
    ) -> bool:
        """
        Check if aspect exists between two planets.

        Args:
            planet1: First planet name
            planet2: Second planet name
            aspect_type: Specific aspect type to check, or None for any aspect

        Returns:
            True if aspect exists
        """
        pass

    @abstractmethod
    def get_drishti(
        self,
        planet: Optional[str] = None,
        chart: str = "D1"
    ) -> List[Dict[str, Any]]:
        """
        Get Vedic drishti (aspects) by house count.
        All planets aspect 7th house; Mars 4th & 8th; Jupiter 5th & 9th; Saturn 3rd & 10th.

        Args:
            planet: Planet name to filter by, or None for all
            chart: Chart name

        Returns:
            List of drishti relationships with house-based aspects
        """
        pass

    @abstractmethod
    def is_house_aspected_by(
        self,
        house: int,
        planets: List[str],
        chart: str = "D1"
    ) -> bool:
        """
        Check if a house is aspected by specific planets.

        Args:
            house: House number 1-12
            planets: List of planet names
            chart: Chart name

        Returns:
            True if house receives aspect from all specified planets
        """
        pass

    # ============ PARIVARTANA (MUTUAL EXCHANGE) QUERIES ============

    @abstractmethod
    def has_parivartana(self, planet1: str, planet2: str) -> bool:
        """
        Check if mutual exchange (parivartana) exists between two planets.
        Parivartana occurs when two planets are placed in each other's signs.

        Args:
            planet1: First planet name
            planet2: Second planet name

        Returns:
            True if parivartana exists
        """
        pass

    @abstractmethod
    def get_parivartana_pairs(self) -> List[ParivartanaQuery]:
        """
        Get all parivartana (mutual exchange) pairs in the chart.

        Returns:
            List of ParivartanaQuery objects with exchange details
        """
        pass

    @abstractmethod
    def get_parivartana_type(
        self,
        planet1: str,
        planet2: str
    ) -> Optional[ParivartanaType]:
        """
        Get type of parivartana between two planets.

        Args:
            planet1: First planet name
            planet2: Second planet name

        Returns:
            ParivartanaType, or None if no exchange exists
        """
        pass

    # ============ PLANETARY RELATIONSHIP QUERIES ============

    @abstractmethod
    def get_planetary_relationship(
        self,
        planet1: str,
        planet2: str
    ) -> Optional[RelationshipType]:
        """
        Get five-fold (Panchadha) relationship between two planets.
        Combines natural and temporary relationships.

        Args:
            planet1: First planet name
            planet2: Second planet name

        Returns:
            RelationshipType, or None if relationship cannot be determined
        """
        pass

    # ============ RELATIVE POSITION QUERIES ============

    @abstractmethod
    def get_house_from_planet(
        self,
        target: str,
        from_planet: str,
        chart: str = "D1"
    ) -> Optional[int]:
        """
        Get house position of target planet relative to reference planet.

        Args:
            target: Target planet name
            from_planet: Reference planet name (e.g., "moon" for lunar reference)
            chart: Chart name

        Returns:
            House number (1-12) relative to reference, or None

        Example:
            get_house_from_planet("jupiter", "moon")
            # Returns house position of Jupiter counted from Moon
        """
        pass

    @abstractmethod
    def is_in_kendra_from(
        self,
        planet: str,
        reference: str,
        chart: str = "D1"
    ) -> bool:
        """
        Check if planet is in kendra (1,4,7,10) from reference planet.

        Args:
            planet: Target planet name
            reference: Reference planet name (e.g., "lagna", "moon")
            chart: Chart name

        Returns:
            True if planet is in kendra from reference
        """
        pass

    @abstractmethod
    def is_in_trikona_from(
        self,
        planet: str,
        reference: str,
        chart: str = "D1"
    ) -> bool:
        """
        Check if planet is in trikona (1,5,9) from reference planet.

        Args:
            planet: Target planet name
            reference: Reference planet name
            chart: Chart name

        Returns:
            True if planet is in trikona from reference
        """
        pass

    # ============ DIVISIONAL CHART QUERIES ============

    @abstractmethod
    def get_vargottama_planets(self) -> List[str]:
        """
        Get planets that are vargottama (same sign in D1 and D9).

        Returns:
            List of planet names that are vargottama
        """
        pass

    @abstractmethod
    def get_divisional_quality(
        self,
        planet: str,
        chart: str
    ) -> Optional[str]:
        """
        Get quality classification in divisional chart (for D16, D60).

        Args:
            planet: Planet name
            chart: Chart name (D16 or D60)

        Returns:
            Quality string (e.g., "benefic", "malefic") or None
        """
        pass

    @abstractmethod
    def get_chart_names(self) -> List[str]:
        """
        Get list of available divisional charts.

        Returns:
            List of chart names (e.g., ["D1", "D2", "D9", "D10"])
        """
        pass

    # ============ KARAKA QUERIES ============

    @abstractmethod
    def get_karaka(self, karaka_name: str) -> Optional[str]:
        """
        Get planet for specified Jaimini Chara Karaka.

        Args:
            karaka_name: Karaka type (atma/amatya/bhratri/matri/putra/gnati/dara)

        Returns:
            Planet name, or None if karaka not computed
        """
        pass

    @abstractmethod
    def get_all_karakas(self) -> Dict[str, str]:
        """
        Get all Jaimini Chara Karakas.

        Returns:
            Dict mapping karaka name to planet name
            e.g., {"atma": "venus", "amatya": "mercury", ...}
        """
        pass

    # ============ SPECIAL LAGNAS ============

    @abstractmethod
    def get_special_lagna_house(self, lagna_name: str) -> Optional[int]:
        """
        Get house of special lagna (Upapada, Arudha Lagna, etc.).

        Args:
            lagna_name: Special lagna type (upapada/arudha/karakamsa/pranapada)

        Returns:
            House number (1-12), or None if not computed
        """
        pass

    @abstractmethod
    def get_arudha_padas(self) -> Dict[str, int]:
        """
        Get all Arudha Padas (AL, A2, A3, ... A12, UL).

        Returns:
            Dict mapping pada name to house number
            e.g., {"AL": 5, "A7": 11, "UL": 3, ...}
        """
        pass

    # ============ DASHA QUERIES ============

    @abstractmethod
    def is_dasha_system_supported(self, system_name: str) -> bool:
        """
        Check if a specific dasha system is supported by the kundali generator.
        
        Args:
            system_name: Dasha system name (e.g., "vimshottari", "kalachakra")
            
        Returns:
            True if supported
        """
        pass

    @abstractmethod
    def is_dasha_active(self, level: str, planet: str) -> bool:
        """
        Check if dasha is active at specified level.
        Requires current date for evaluation.

        Args:
            level: Dasha level (mahadasha/antardasha/pratyantardasha/sookshma/prana)
            planet: Planet name

        Returns:
            True if planet's dasha is active at specified level
        """
        pass

    @abstractmethod
    def get_current_dasha(self, level: str = "mahadasha") -> Optional[DashaQuery]:
        """
        Get current dasha period at specified level.
        Requires current date for evaluation.

        Args:
            level: Dasha level (mahadasha/antardasha/pratyantardasha/sookshma/prana)

        Returns:
            DashaQuery with period details, or None if cannot determine
        """
        pass

    @abstractmethod
    def get_dasha_sequence(
        self,
        level: str = "mahadasha",
        limit: int = 10
    ) -> List[DashaQuery]:
        """
        Get sequence of dasha periods at specified level.

        Args:
            level: Dasha level
            limit: Maximum number of periods to return

        Returns:
            List of DashaQuery objects in chronological order
        """
        pass

    # ============ ASHTAKAVARGA QUERIES ============

    @abstractmethod
    def get_ashtakavarga_bindus(
        self,
        planet: str,
        house: int
    ) -> Optional[int]:
        """
        Get Ashtakavarga bindus for planet in house.

        Args:
            planet: Planet name (sun/moon/mars/mercury/jupiter/venus/saturn)
            house: House number 1-12

        Returns:
            Number of bindus (0-8), or None if not computed
        """
        pass

    @abstractmethod
    def get_sarvashtakavarga(self, house: int) -> Optional[int]:
        """
        Get Sarvashtakavarga (total bindus) for house.

        Args:
            house: House number 1-12

        Returns:
            Total bindus across all planets, or None if not computed
        """
        pass

    @abstractmethod
    def get_ashtakavarga_for_planet(self, planet: str) -> Optional[List[int]]:
        """
        Get Ashtakavarga bindus for planet across all 12 houses.

        Args:
            planet: Planet name

        Returns:
            List of 12 bindu counts (one per house), or None if not computed
        """
        pass

    # ============ YOGA QUERIES ============

    @abstractmethod
    def has_neecha_bhanga(self, planet: str) -> bool:
        """
        Check if planet has Neecha Bhanga (debilitation cancellation).

        Args:
            planet: Planet name

        Returns:
            True if debilitation is cancelled
        """
        pass

    @abstractmethod
    def is_planet_in_war(self, planet: str) -> bool:
        """
        Check if planet is in planetary war (graha yuddha).
        Occurs when two planets are within 1 degree.

        Args:
            planet: Planet name

        Returns:
            True if planet is in war
        """
        pass

    # ============ PANCHANGA QUERIES ============

    @abstractmethod
    def get_tithi(self) -> Optional[Dict[str, Any]]:
        """
        Get Tithi (lunar day) at birth.

        Returns:
            Dict with tithi number, name, paksha, balance
        """
        pass

    @abstractmethod
    def get_nakshatra(self) -> Optional[Dict[str, Any]]:
        """
        Get birth nakshatra (Moon's nakshatra).

        Returns:
            Dict with nakshatra number, name, lord, pada, balance
        """
        pass

    @abstractmethod
    def get_weekday(self) -> Optional[str]:
        """
        Get day of week at birth.

        Returns:
            Day name (monday/tuesday/...) or None
        """
        pass

    @abstractmethod
    def get_moon_phase(self) -> Optional[str]:
        """
        Get moon phase at birth.

        Returns:
            Phase name (new/waxing/full/waning) or None
        """
        pass

    # ============ BIRTH DETAILS QUERIES ============

    @abstractmethod
    def get_birth_time_hour(self) -> Optional[int]:
        """
        Get birth hour (0-23).

        Returns:
            Hour of birth, or None
        """
        pass

    @abstractmethod
    def get_lagna_longitude(self) -> Optional[float]:
        """
        Get ascendant (lagna) longitude.

        Returns:
            Lagna longitude in degrees (0-360), or None
        """
        pass

    # ============ VALIDATION ============

    @abstractmethod
    def validate_api_coverage(self) -> Dict[str, Any]:
        """
        Validate that kundali has all data needed for API.

        Returns:
            Dict with validation results:
            {
                "complete": bool,
                "missing_features": List[str],
                "warnings": List[str],
                "available_charts": List[str],
                "has_karakas": bool,
                "has_dashas": bool,
                "has_ashtakavarga": bool,
                "has_special_lagnas": bool
            }
        """
        pass

    # ============ UTILITY METHODS ============

    @abstractmethod
    def resolve_planet_selector(self, selector: str) -> Optional[str]:
        """
        Resolve planet selector to actual planet name.

        Supports:
        - Direct names: "sun", "moon", "mars", etc.
        - Karakas: "atma", "putra", "dara", etc.
        - House lords: "lord_of_1", "lord_of_10", etc.
        - Special: "dispositor_of_debilitated"

        Args:
            selector: Planet selector string

        Returns:
            Actual planet name, or None if cannot resolve
        """
        pass

    @abstractmethod
    def get_sign_name(self, sign_index: int) -> str:
        """
        Get sign name from index.

        Args:
            sign_index: Sign index 0-11

        Returns:
            Sign name (aries/taurus/gemini/...)
        """
        pass

    @abstractmethod
    def get_nakshatra_name(self, nakshatra_index: int) -> str:
        """
        Get nakshatra name from index.

        Args:
            nakshatra_index: Nakshatra index 0-26

        Returns:
            Nakshatra name
        """
        pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_planet_name(name: str) -> str:
    """Normalize planet name to lowercase standard form"""
    return name.lower().strip()


def normalize_chart_name(chart: str) -> str:
    """Normalize chart name to uppercase standard form (D1, D9, etc.)"""
    chart = chart.upper().strip()
    if not chart.startswith("D"):
        chart = f"D{chart}"
    return chart


def is_benefic(planet: str) -> bool:
    """Check if planet is a natural benefic"""
    return planet.lower() in {"jupiter", "venus", "mercury", "moon"}


def is_malefic(planet: str) -> bool:
    """Check if planet is a natural malefic"""
    return planet.lower() in {"saturn", "mars", "sun", "rahu", "ketu"}


def is_kendra(house: int) -> bool:
    """Check if house is a kendra (angle: 1,4,7,10)"""
    return house in {1, 4, 7, 10}


def is_trikona(house: int) -> bool:
    """Check if house is a trikona (trine: 1,5,9)"""
    return house in {1, 5, 9}


def is_dusthana(house: int) -> bool:
    """Check if house is a dusthana (malefic: 6,8,12)"""
    return house in {6, 8, 12}


def is_upachaya(house: int) -> bool:
    """Check if house is upachaya (growth: 3,6,10,11)"""
    return house in {3, 6, 10, 11}
