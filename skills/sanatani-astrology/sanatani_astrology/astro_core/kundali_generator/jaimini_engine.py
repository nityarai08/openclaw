"""
Jaimini Calculation Engine.

This module provides shared logic for calculating Jaimini indicators
(Arudha Padas, Upapada, Karakamsa) and other specialized astrological points.
It is designed to be used by both PyJHora and Ephemeris generators.
"""

from typing import Dict, Any, List, Optional

class JaiminiEngine:
    """
    Engine for Jaimini and special point calculations.
    """

    @staticmethod
    def calculate_arudha_padas(
        planetary_positions: Dict[str, Any],
        house_cusps: List[float],
        house_lords: Dict[int, str]
    ) -> Dict[str, Any]:
        """
        Calculate Arudha Padas for all 12 houses (AL, UL, A3, etc.).
        
        Args:
            planetary_positions: Dictionary of planet positions (must include 'house' and 'longitude').
            house_cusps: List of house cusp longitudes.
            house_lords: Dictionary mapping house number (1-12) to lord planet name.
            
        Returns:
            Dictionary mapping 'A1'...'A12', 'AL', 'UL' to house numbers (1-12).
        """
        padas = {}
        
        # Helper to get planet's house
        def get_planet_house(planet_name: str) -> Optional[int]:
            p_data = planetary_positions.get(planet_name.lower())
            if p_data and 'house' in p_data:
                return int(p_data['house'])
            return None

        # Calculate Arudha for each house
        for house_num in range(1, 13):
            lord = house_lords.get(house_num)
            if not lord:
                continue
            
            lord_house = get_planet_house(lord)
            if not lord_house:
                continue
            
            # Count houses from House to Lord
            # If lord is in 2nd from house (e.g. house=1, lord in 2), count is 2.
            # Formula: (lord_house - house_num + 12) % 12 + 1
            # But conventionally we count steps: House=1, Lord=2 -> 2nd house. distance=1.
            # Arudha is same distance from Lord.
            
            # Distance in houses (1-based count):
            # House 1 to House 1 = 1
            # House 1 to House 2 = 2
            dist = (lord_house - house_num + 12) % 12
            
            # Arudha is 'dist' houses away from Lord
            arudha_house = (lord_house + dist) % 12
            if arudha_house == 0: 
                arudha_house = 12
            
            # Jaimini Exceptions (Swasthe Daraha - BPHS Ch 30)
            # If Arudha falls in the house itself or the 7th from it, apply shifts.
            # 1. If Lord is in the House itself (dist=0), Arudha is 10th from it.
            # 2. If Lord is in 7th from House (dist=6), Arudha is 10th from it (i.e. 4th from House).
            
            # Let's check exact BPHS/Jaimini Sutra rules.
            # Sutra 1.1.30-32:
            # - If lord is in 1st or 7th from house, Arudha is 10th from the house.
            # - (Some interpretations say 10th from Lord, which is same if in 1st).
            
            # Standard Exceptions Implementation:
            # Calculate raw Arudha.
            # If raw Arudha == House_Num -> Shift to 10th from Arudha.
            # If raw Arudha == 7th from House_Num -> Shift to 10th from Arudha.
            
            # Let's re-verify against standard practice (e.g. Jagannatha Hora software logic):
            # If Arudha falls in same house -> 10th house.
            # If Arudha falls in 7th house -> 4th house.
            
            if arudha_house == house_num:
                arudha_house = (arudha_house + 9) % 12 # +10th house (1-based logic: +9 steps)
                if arudha_house == 0: arudha_house = 12
            elif arudha_house == ((house_num + 6 - 1) % 12 + 1):
                arudha_house = (arudha_house + 9) % 12 # +10th house
                if arudha_house == 0: arudha_house = 12
                
            pada_key = f"A{house_num}"
            padas[pada_key] = arudha_house
            
            # Special aliases
            if house_num == 1:
                padas['AL'] = arudha_house # Arudha Lagna
            elif house_num == 12:
                padas['UL'] = arudha_house # Upapada Lagna
            elif house_num == 7:
                padas['A7'] = arudha_house # Dara Pada (often just A7)

        return padas

    @staticmethod
    def calculate_karakamsa(
        d9_planetary_positions: Dict[str, Any]
    ) -> Optional[str]:
        """
        Determine the Karakamsa sign (Navamsa sign of Atmakaraka).
        
        Args:
            d9_planetary_positions: Planetary positions from D9 chart.
            
        Returns:
            Name of the Karakamsa sign (e.g., 'Leo').
        """
        # Find Atmakaraka (AK) - planet with highest degree in sign
        # Note: This assumes we have access to D1 degrees.
        # But if we only have D9 positions passed here, we might miss the precise degree data.
        # Ideally, calculate_karakamsa should take D1 positions to find AK, 
        # then look up that planet's sign in D9.
        return None # Placeholder, logic should be in generator using D1 data

    @staticmethod
    def get_atmakaraka(planetary_positions: Dict[str, Any]) -> Optional[str]:
        """
        Identify the Atmakaraka (AK) from D1 positions.
        7-Karaka scheme (excluding Rahu/Ketu usually, or 8-karaka including Rahu).
        Using 7-karaka scheme as standard BPHS default unless specified.
        """
        candidates = []
        # Standard 7 planets
        grahas = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
        # Add Rahu for 8-karaka scheme if needed (BPHS allows both, 7 is safer default)
        
        for p in grahas:
            pos = planetary_positions.get(p)
            if pos:
                deg = pos.get('degree_in_sign', 0.0)
                candidates.append((p, deg))
        
        if not candidates:
            return None
            
        # Sort by degree descending
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0] # Planet name of AK

    @staticmethod
    def calculate_moon_phase_detailed(
        sun_long: float,
        moon_long: float
    ) -> Dict[str, Any]:
        """
        Calculate detailed Moon phase (Waxing/Waning, Tithi, Paksha).
        """
        diff = (moon_long - sun_long) % 360.0
        tithi_num = int(diff / 12) + 1
        
        if 0 <= diff < 180:
            paksha = "Shukla" # Waxing
            phase_state = "waxing"
        else:
            paksha = "Krishna" # Waning
            phase_state = "waning"
            
        return {
            "tithi": tithi_num,
            "paksha": paksha,
            "state": phase_state,
            "angle": diff
        }
