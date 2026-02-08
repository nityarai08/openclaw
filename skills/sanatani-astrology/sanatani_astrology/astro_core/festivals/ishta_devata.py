"""
Ishta Devata Calculator

Determines the preferred deity for a person based on their birth chart.
Based on BPHS Chapter 33 - Atmakaraka and 9th house analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from .constants import PLANET_DEITY_MAP, DEITY_FESTIVALS


@dataclass
class IshtaDevataResult:
    """Result of Ishta Devata calculation."""
    primary_deity: str
    secondary_deities: List[str] = field(default_factory=list)
    determination_method: str = ""
    atmakaraka: Optional[str] = None
    reasoning: Optional[str] = None
    special_days: List[str] = field(default_factory=list)
    special_festivals: List[str] = field(default_factory=list)
    mantras: List[Dict[str, Any]] = field(default_factory=list)


class IshtaDevataCalculator:
    """
    Calculates Ishta Devata (preferred deity) from birth chart.
    
    Methods based on BPHS:
    1. Atmakaraka in Navamsa - primary method
    2. 9th lord in D1 - secondary method
    3. 5th lord analysis - tertiary method
    """
    
    # Default mantras for common deities
    DEITY_MANTRAS = {
        "Shiva": [
            {"mantra": "Om Namah Shivaya", "repetitions": 108, "deity": "Shiva"},
            {"mantra": "Mahamrityunjaya Mantra", "repetitions": 108, "deity": "Shiva"},
        ],
        "Vishnu": [
            {"mantra": "Om Namo Narayanaya", "repetitions": 108, "deity": "Vishnu"},
            {"mantra": "Om Namo Bhagavate Vasudevaya", "repetitions": 108, "deity": "Vishnu"},
        ],
        "Krishna": [
            {"mantra": "Hare Krishna Mahamantra", "repetitions": 108, "deity": "Krishna"},
            {"mantra": "Om Kleem Krishnaya Namaha", "repetitions": 108, "deity": "Krishna"},
        ],
        "Rama": [
            {"mantra": "Om Sri Ramaya Namaha", "repetitions": 108, "deity": "Rama"},
            {"mantra": "Sri Rama Jaya Rama Jaya Jaya Rama", "repetitions": 108, "deity": "Rama"},
        ],
        "Ganesha": [
            {"mantra": "Om Gam Ganapataye Namaha", "repetitions": 108, "deity": "Ganesha"},
            {"mantra": "Vakratunda Mahakaya", "repetitions": 21, "deity": "Ganesha"},
        ],
        "Durga": [
            {"mantra": "Om Dum Durgayei Namaha", "repetitions": 108, "deity": "Durga"},
            {"mantra": "Ya Devi Sarvabhuteshu", "repetitions": 9, "deity": "Durga"},
        ],
        "Lakshmi": [
            {"mantra": "Om Shreem Mahalakshmiyei Namaha", "repetitions": 108, "deity": "Lakshmi"},
            {"mantra": "Om Hreem Shreem Kleem Mahalakshmiyei Namaha", "repetitions": 108, "deity": "Lakshmi"},
        ],
        "Hanuman": [
            {"mantra": "Om Hanumate Namaha", "repetitions": 108, "deity": "Hanuman"},
            {"mantra": "Hanuman Chalisa", "repetitions": 1, "deity": "Hanuman"},
        ],
        "Surya": [
            {"mantra": "Om Suryaya Namaha", "repetitions": 12, "deity": "Surya"},
            {"mantra": "Gayatri Mantra", "repetitions": 108, "deity": "Surya"},
        ],
    }
    
    # Special days for each deity
    DEITY_SPECIAL_DAYS = {
        "Shiva": ["Monday", "Trayodashi (Pradosh)", "Chaturdashi"],
        "Vishnu": ["Thursday", "Ekadashi", "Saturday"],
        "Krishna": ["Wednesday", "Ashtami", "Ekadashi"],
        "Rama": ["Sunday", "Navami", "Ekadashi"],
        "Ganesha": ["Tuesday", "Chaturthi (Sankashti)"],
        "Durga": ["Tuesday", "Friday", "Ashtami", "Navami"],
        "Lakshmi": ["Friday", "Purnima", "Amavasya (Diwali)"],
        "Hanuman": ["Tuesday", "Saturday"],
        "Surya": ["Sunday", "Saptami"],
    }
    
    def calculate(self, kundali: Dict[str, Any]) -> IshtaDevataResult:
        """
        Calculate Ishta Devata from kundali data.
        
        Args:
            kundali: Comprehensive kundali data
            
        Returns:
            IshtaDevataResult with deity information
        """
        # Try Atmakaraka method first
        atmakaraka = self._get_atmakaraka(kundali)
        if atmakaraka:
            result = self._from_atmakaraka(atmakaraka, kundali)
            if result:
                return result
        
        # Fallback to 9th lord method
        ninth_lord = self._get_ninth_lord(kundali)
        if ninth_lord:
            result = self._from_ninth_lord(ninth_lord, kundali)
            if result:
                return result
        
        # Default fallback
        return self._default_result(kundali)
    
    def _get_atmakaraka(self, kundali: Dict[str, Any]) -> Optional[str]:
        """Get Atmakaraka (planet with highest degree) from kundali."""
        # Handle both field names: planetary_positions (new) or planets (old)
        planets = kundali.get("planetary_positions", kundali.get("planets", {}))

        # Exclude Rahu/Ketu from Atmakaraka calculation
        valid_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
        
        max_degree = -1
        atmakaraka = None
        
        for planet_name in valid_planets:
            planet_data = planets.get(planet_name.lower(), {})
            if isinstance(planet_data, dict):
                # Get degree within sign (0-30)
                longitude = planet_data.get("longitude", 0)
                degree_in_sign = longitude % 30
                
                if degree_in_sign > max_degree:
                    max_degree = degree_in_sign
                    atmakaraka = planet_name
        
        return atmakaraka
    
    def _from_atmakaraka(
        self, atmakaraka: str, kundali: Dict[str, Any]
    ) -> Optional[IshtaDevataResult]:
        """Determine deity from Atmakaraka placement."""
        deities = PLANET_DEITY_MAP.get(atmakaraka, [])
        
        if not deities:
            return None
        
        primary = deities[0]
        secondary = deities[1:] if len(deities) > 1 else []
        
        # Get special festivals for this deity
        festivals = DEITY_FESTIVALS.get(primary, [])
        special_days = self.DEITY_SPECIAL_DAYS.get(primary, [])
        mantras = self.DEITY_MANTRAS.get(primary, [])
        
        return IshtaDevataResult(
            primary_deity=primary,
            secondary_deities=secondary,
            determination_method="atmakaraka",
            atmakaraka=atmakaraka,
            reasoning=f"Your Atmakaraka is {atmakaraka}, indicating {primary} as your Ishta Devata.",
            special_days=special_days,
            special_festivals=festivals,
            mantras=mantras,
        )
    
    def _get_ninth_lord(self, kundali: Dict[str, Any]) -> Optional[str]:
        """Get 9th house lord from kundali."""
        houses = kundali.get("houses", {})
        
        # Get 9th house sign
        ninth_house = houses.get("9", houses.get("H9", {}))
        if isinstance(ninth_house, dict):
            sign = ninth_house.get("sign", "")
            return self._get_sign_lord(sign)
        
        return None
    
    def _get_sign_lord(self, sign: str) -> Optional[str]:
        """Get ruling planet for a sign."""
        sign_lords = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
            "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
            "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
        }
        return sign_lords.get(sign)
    
    def _from_ninth_lord(
        self, ninth_lord: str, kundali: Dict[str, Any]
    ) -> Optional[IshtaDevataResult]:
        """Determine deity from 9th lord."""
        deities = PLANET_DEITY_MAP.get(ninth_lord, [])
        
        if not deities:
            return None
        
        primary = deities[0]
        secondary = deities[1:] if len(deities) > 1 else []
        
        festivals = DEITY_FESTIVALS.get(primary, [])
        special_days = self.DEITY_SPECIAL_DAYS.get(primary, [])
        mantras = self.DEITY_MANTRAS.get(primary, [])
        
        return IshtaDevataResult(
            primary_deity=primary,
            secondary_deities=secondary,
            determination_method="ninth_lord",
            reasoning=f"Your 9th lord is {ninth_lord}, indicating {primary} as your Ishta Devata.",
            special_days=special_days,
            special_festivals=festivals,
            mantras=mantras,
        )
    
    def _default_result(self, kundali: Dict[str, Any]) -> IshtaDevataResult:
        """Return default deity when calculation is not possible."""
        # Default to Ganesha as the remover of obstacles
        return IshtaDevataResult(
            primary_deity="Ganesha",
            secondary_deities=["Vishnu", "Shiva"],
            determination_method="default",
            reasoning="Ganesha is recommended as the universal Ishta Devata for removing obstacles.",
            special_days=self.DEITY_SPECIAL_DAYS.get("Ganesha", []),
            special_festivals=DEITY_FESTIVALS.get("Ganesha", []),
            mantras=self.DEITY_MANTRAS.get("Ganesha", []),
        )
