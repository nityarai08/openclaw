"""
Festival Relevance Scorer

Calculates personalized relevance scores for festivals based on:
1. Ishta Devata alignment (0.25)
2. Planet strength/dignity (0.15)
3. Dasha alignment (0.15)
4. Nakshatra connection (0.20)
5. Regional preference (0.10)
6. Base relevance (0.15)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from .constants import PLANET_DEITY_MAP, DEITY_FESTIVALS


@dataclass
class RelevanceResult:
    """Result of relevance calculation."""
    score: float  # 0.0 to 1.0
    reasons: List[str] = field(default_factory=list)
    is_highly_relevant: bool = False
    breakdown: Dict[str, float] = field(default_factory=dict)


class RelevanceScorer:
    """
    Calculates festival relevance for a person.
    
    Scoring weights:
    - Ishta Devata: 0.25 (if festival deity matches)
    - Planet strength: 0.15 (if festival planet is strong in chart)
    - Dasha alignment: 0.15 (if dasha planet matches)
    - Nakshatra: 0.20 (if birth nakshatra matches)
    - Regional: 0.10 (if regional preference matches)
    - Base: 0.15 (for major/important festivals)
    """
    
    WEIGHTS = {
        "ishta_devata": 0.25,
        "planet_strength": 0.15,
        "dasha": 0.15,
        "nakshatra": 0.20,
        "regional": 0.10,
        "base": 0.15,
    }
    
    def calculate_relevance(
        self,
        festival: Dict[str, Any],
        kundali: Dict[str, Any],
        preferences: Optional[Dict[str, Any]] = None,
    ) -> RelevanceResult:
        """
        Calculate relevance score for a festival.
        
        Args:
            festival: Festival data dict
            kundali: User's kundali data
            preferences: User preferences (region, etc.)
            
        Returns:
            RelevanceResult with score and reasons
        """
        scores = {}
        reasons = []
        
        # 1. Ishta Devata alignment
        ishta_score, ishta_reason = self._score_ishta_devata(festival, kundali)
        scores["ishta_devata"] = ishta_score
        if ishta_reason:
            reasons.append(ishta_reason)
        
        # 2. Planet strength
        planet_score, planet_reason = self._score_planet_strength(festival, kundali)
        scores["planet_strength"] = planet_score
        if planet_reason:
            reasons.append(planet_reason)
        
        # 3. Dasha alignment
        dasha_score, dasha_reason = self._score_dasha(festival, kundali)
        scores["dasha"] = dasha_score
        if dasha_reason:
            reasons.append(dasha_reason)
        
        # 4. Nakshatra connection
        nak_score, nak_reason = self._score_nakshatra(festival, kundali)
        scores["nakshatra"] = nak_score
        if nak_reason:
            reasons.append(nak_reason)
        
        # 5. Regional preference
        regional_score, regional_reason = self._score_regional(festival, preferences)
        scores["regional"] = regional_score
        if regional_reason:
            reasons.append(regional_reason)
        
        # 6. Base relevance (major festivals get higher base)
        base_score = self._score_base(festival)
        scores["base"] = base_score
        
        # Calculate weighted total
        total_score = sum(
            scores[key] * self.WEIGHTS[key] for key in scores
        )
        
        # Normalize to 0-1 range
        total_score = min(1.0, max(0.0, total_score))
        
        return RelevanceResult(
            score=round(total_score, 3),
            reasons=reasons,
            is_highly_relevant=total_score >= 0.7,
            breakdown=scores,
        )
    
    def _score_ishta_devata(
        self, festival: Dict[str, Any], kundali: Dict[str, Any]
    ) -> tuple[float, Optional[str]]:
        """Score based on Ishta Devata alignment."""
        festival_deities = festival.get("ruling_deities", [])

        # Get Atmakaraka from kundali (handle both field names)
        planets = kundali.get("planetary_positions", kundali.get("planets", {}))
        atmakaraka = self._get_atmakaraka(planets)
        
        if not atmakaraka:
            return 0.0, None
        
        # Get deities associated with Atmakaraka
        ishta_deities = PLANET_DEITY_MAP.get(atmakaraka, [])
        
        # Check for match
        for deity in festival_deities:
            if deity in ishta_deities:
                return 1.0, f"This festival honors {deity}, your Ishta Devata"
        
        return 0.0, None
    
    def _get_atmakaraka(self, planets: Dict[str, Any]) -> Optional[str]:
        """Get Atmakaraka from planets data."""
        valid_planets = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"]
        
        max_degree = -1
        atmakaraka = None
        
        for planet_name in valid_planets:
            planet_data = planets.get(planet_name, {})
            if isinstance(planet_data, dict):
                longitude = planet_data.get("longitude", 0)
                degree_in_sign = longitude % 30
                
                if degree_in_sign > max_degree:
                    max_degree = degree_in_sign
                    atmakaraka = planet_name.capitalize()
        
        return atmakaraka
    
    def _score_planet_strength(
        self, festival: Dict[str, Any], kundali: Dict[str, Any]
    ) -> tuple[float, Optional[str]]:
        """Score based on festival planet strength in chart."""
        festival_planets = festival.get("ruling_planets", [])

        if not festival_planets:
            return 0.5, None  # Neutral if no planets specified

        # Handle both field names
        planets = kundali.get("planetary_positions", kundali.get("planets", {}))
        
        for planet in festival_planets:
            planet_data = planets.get(planet.lower(), {})
            if isinstance(planet_data, dict):
                # Check if planet is in own sign, exalted, or has good dignity
                dignity = planet_data.get("dignity", "")
                if dignity in ["exalted", "own_sign", "moolatrikona"]:
                    return 1.0, f"{planet} is strong in your chart"
                elif dignity in ["debilitated", "enemy"]:
                    return 0.3, None
        
        return 0.5, None
    
    def _score_dasha(
        self, festival: Dict[str, Any], kundali: Dict[str, Any]
    ) -> tuple[float, Optional[str]]:
        """Score based on current dasha alignment."""
        # Handle both field structures
        dasha = kundali.get("dasha_periods", kundali.get("dasha", {}))
        vimshottari = dasha.get("vimshottari", dasha.get("current", {}))

        if not vimshottari:
            return 0.5, None

        # Get current mahadasha planet (handle both structures)
        maha_planet = vimshottari.get("current_dasha_lord", "")
        if not maha_planet:
            maha_planet = vimshottari.get("mahadasha", {}).get("planet", "")
        
        festival_planets = festival.get("ruling_planets", [])
        festival_deities = festival.get("ruling_deities", [])
        
        # Check if dasha planet matches festival planet
        if maha_planet in festival_planets:
            return 1.0, f"You're in {maha_planet} Mahadasha - this festival is especially beneficial"
        
        # Check if dasha planet's deity matches
        dasha_deities = PLANET_DEITY_MAP.get(maha_planet, [])
        for deity in festival_deities:
            if deity in dasha_deities:
                return 0.8, f"This festival aligns with your {maha_planet} dasha period"
        
        return 0.4, None
    
    def _score_nakshatra(
        self, festival: Dict[str, Any], kundali: Dict[str, Any]
    ) -> tuple[float, Optional[str]]:
        """Score based on nakshatra connection."""
        festival_nakshatra = festival.get("nakshatra")

        # Get birth nakshatra from panchanga
        panchanga = kundali.get("panchanga", {})
        birth_nakshatra = panchanga.get("nakshatra", {})

        birth_nak_name = ""
        if isinstance(birth_nakshatra, dict):
            birth_nak_name = birth_nakshatra.get("name", "")
            if not birth_nak_name:
                index = birth_nakshatra.get("index") or birth_nakshatra.get("number")
                if isinstance(index, int):
                    birth_nak_name = self._nakshatra_number_to_name(index)
        elif isinstance(birth_nakshatra, str):
            birth_nak_name = birth_nakshatra

        # Fallback to Moon's nakshatra from planetary positions
        if not birth_nak_name:
            planets = kundali.get("planetary_positions", kundali.get("planets", {}))
            moon = planets.get("moon") or planets.get("Moon", {})
            if isinstance(moon, dict):
                nak_value = moon.get("nakshatra", "")
                # If nakshatra is a number, convert to name
                if isinstance(nak_value, int):
                    birth_nak_name = self._nakshatra_number_to_name(nak_value)
                else:
                    birth_nak_name = str(nak_value) if nak_value else ""

        if not birth_nak_name:
            return 0.3, None

        if festival_nakshatra and festival_nakshatra.lower() == birth_nak_name.lower():
            return 1.0, f"This festival falls on your birth nakshatra ({birth_nak_name})"

        return 0.3, None

    def _nakshatra_number_to_name(self, num: int) -> str:
        """Convert nakshatra number (1-27) to name."""
        from .constants import NAKSHATRA_LIST
        if 0 <= num < len(NAKSHATRA_LIST):
            return NAKSHATRA_LIST[num]
        if 1 <= num <= len(NAKSHATRA_LIST):
            return NAKSHATRA_LIST[num - 1]
        return ""
    
    def _score_regional(
        self, festival: Dict[str, Any], preferences: Optional[Dict[str, Any]]
    ) -> tuple[float, Optional[str]]:
        """Score based on regional preference."""
        if not preferences:
            return 0.5, None
        
        user_region = preferences.get("region")
        if not user_region:
            return 0.5, None
        if not isinstance(user_region, str):
            user_region = str(user_region)
        user_region = user_region.lower()
        if not user_region:
            return 0.5, None
        
        # Check festival category
        category = festival.get("category", "")
        if category == "regional":
            # Check if regional festival matches user's region
            regional_names = festival.get("regional_names", {})
            if regional_names and user_region in regional_names:
                return 1.0, f"This is a festival from your region ({user_region.title()})"
        
        return 0.5, None
    
    def _score_base(self, festival: Dict[str, Any]) -> float:
        """Get base relevance score for festival."""
        category = festival.get("category", "")
        
        # Major festivals get high base score
        if category == "major":
            return 1.0
        elif category == "deity_specific":
            return 0.8
        elif category == "recurring":
            return 0.6
        elif category == "regional":
            return 0.5
        elif category == "ancestral":
            return 0.7
        elif category == "solar":
            return 0.6
        
        return 0.5
