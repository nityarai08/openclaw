"""
Divisional chart generation system.

This module implements divisional chart calculations for D1 through D60,
including planetary positions, house placements, dignity calculations,
and aspect analysis.
"""

import math
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field

from ..core.data_models import PlanetaryPosition
from .varga_calculator import calculate_varga_position


class DivisionalChart(Enum):
    """Divisional chart types with their division numbers."""
    D1 = 1    # Rasi Chart (Birth Chart)
    D2 = 2    # Hora Chart (Wealth)
    D3 = 3    # Drekkana Chart (Siblings)
    D4 = 4    # Chaturthamsa Chart (Fortune)
    D5 = 5    # Panchamamsa Chart (Fame)
    D6 = 6    # Shashthamsa Chart (Health)
    D7 = 7    # Saptamsa Chart (Children)
    D8 = 8    # Ashtamsa Chart (Longevity)
    D9 = 9    # Navamsa Chart (Marriage)
    D10 = 10  # Dasamsa Chart (Career)
    D11 = 11  # Rudramsa Chart (Destruction)
    D12 = 12  # Dvadasamsa Chart (Parents)
    D16 = 16  # Shodasamsa Chart (Vehicles)
    D20 = 20  # Vimsamsa Chart (Spirituality)
    D24 = 24  # Chaturvimsamsa Chart (Learning)
    D27 = 27  # Nakshatramsa Chart (Strengths/Weaknesses)
    D30 = 30  # Trimsamsa Chart (Misfortunes)
    D40 = 40  # Khavedamsa Chart (Maternal)
    D45 = 45  # Akshavedamsa Chart (Paternal)
    D60 = 60  # Shashtyamsa Chart (Karma)


class PlanetaryDignity(Enum):
    """Planetary dignity states."""
    EXALTED = "Exalted"
    OWN_SIGN = "Own Sign"
    MOOLATRIKONA = "Moolatrikona"
    FRIENDLY = "Friendly"
    NEUTRAL = "Neutral"
    ENEMY = "Enemy"
    DEBILITATED = "Debilitated"


@dataclass
class PlanetaryStrength:
    """Planetary strength assessment."""
    dignity: PlanetaryDignity
    strength_points: float
    shadbala_points: float = 0.0
    aspects_received: List[str] = field(default_factory=list)
    aspects_given: List[str] = field(default_factory=list)


@dataclass
class ChartPosition:
    """Position of a planet in a divisional chart."""
    planet: str
    longitude: float
    rasi: int
    degree_in_sign: float
    nakshatra: int
    house: int
    dignity: PlanetaryDignity
    strength: PlanetaryStrength
    retrograde: bool = False


@dataclass
class DivisionalChartData:
    """Complete divisional chart data."""
    chart_type: DivisionalChart
    chart_name: str
    division_number: int
    planetary_positions: Dict[str, ChartPosition]
    house_cusps: List[float]
    aspects: Dict[str, List[str]]
    yogas: List[str] = field(default_factory=list)
    strength_summary: Dict[str, float] = field(default_factory=dict)


class DivisionalChartGenerator:
    """Generator for all divisional charts D1 through D60."""
    
    def __init__(self):
        self.chart_names = self._get_chart_names()
        self.exaltation_degrees = self._get_exaltation_degrees()
        self.debilitation_degrees = self._get_debilitation_degrees()
        self.own_signs = self._get_own_signs()
        self.moolatrikona_signs = self._get_moolatrikona_signs()
        self.friendship_table = self._get_friendship_table()
    
    def generate_all_charts(
        self, 
        planetary_positions: Dict[str, PlanetaryPosition],
        lagna_longitude: float
    ) -> Dict[str, DivisionalChartData]:
        """
        Generate all divisional charts from D1 to D60.
        
        Args:
            planetary_positions: Base planetary positions from D1
            lagna_longitude: Lagna longitude for house calculations
            
        Returns:
            Dictionary of all divisional charts
        """
        charts = {}
        
        # Generate standard divisional charts
        for chart_type in DivisionalChart:
            chart_data = self.generate_divisional_chart(
                chart_type, planetary_positions, lagna_longitude
            )
            charts[f"D{chart_type.value}"] = chart_data
        
        return charts
    
    def generate_divisional_chart(
        self,
        chart_type: DivisionalChart,
        planetary_positions: Dict[str, PlanetaryPosition],
        lagna_longitude: float
    ) -> DivisionalChartData:
        """
        Generate a specific divisional chart.
        
        Args:
            chart_type: Type of divisional chart to generate
            planetary_positions: Base planetary positions
            lagna_longitude: Lagna longitude
            
        Returns:
            Complete divisional chart data
        """
        division = chart_type.value
        chart_positions = {}
        lagna_div_longitude = calculate_varga_position(lagna_longitude, division).longitude
        
        # Calculate divisional positions for each planet
        for planet_name, position in planetary_positions.items():
            div_position = self._calculate_divisional_position(
                position.longitude, division
            )
            
            # Calculate house position
            house = self._calculate_house_position(div_position, lagna_div_longitude)
            
            # Calculate dignity and strength
            dignity = self._calculate_planetary_dignity(planet_name, div_position)
            strength = self._calculate_planetary_strength(planet_name, div_position, dignity)
            
            chart_positions[planet_name] = ChartPosition(
                planet=planet_name,
                longitude=div_position,
                rasi=int(div_position // 30),
                degree_in_sign=div_position % 30,
                nakshatra=int(div_position * 27 / 360) % 27,
                house=house,
                dignity=dignity,
                strength=strength,
                retrograde=position.retrograde
            )
        
        # Calculate house cusps
        house_cusps = self._calculate_house_cusps(lagna_div_longitude)
        
        # Calculate aspects
        aspects = self._calculate_aspects(chart_positions)
        
        # Identify yogas
        yogas = self._identify_yogas(chart_positions)
        
        # Calculate strength summary
        strength_summary = self._calculate_strength_summary(chart_positions)
        
        return DivisionalChartData(
            chart_type=chart_type,
            chart_name=self.chart_names.get(chart_type, f"D{division}"),
            division_number=division,
            planetary_positions=chart_positions,
            house_cusps=house_cusps,
            aspects=aspects,
            yogas=yogas,
            strength_summary=strength_summary
        )
    
    def _calculate_divisional_position(self, longitude: float, division: int) -> float:
        """
        Calculate divisional chart position using standard Parashari method.
        
        Args:
            longitude: Original longitude in degrees
            division: Division number (2, 3, 4, etc.)
            
        Returns:
            Divisional longitude in degrees
        """
        varga_pos = calculate_varga_position(longitude, division)
        return varga_pos.longitude
    
    def _calculate_house_position(self, longitude: float, lagna_longitude: float) -> int:
        """Calculate house position from longitude and lagna."""
        # Simple equal house system
        lagna_rasi = int(lagna_longitude // 30)
        planet_rasi = int(longitude // 30)
        
        house = ((planet_rasi - lagna_rasi) % 12) + 1
        return house
    
    def _calculate_planetary_dignity(self, planet: str, longitude: float) -> PlanetaryDignity:
        """Calculate planetary dignity in a sign."""
        rasi = int(longitude // 30)
        degree = longitude % 30
        
        planet_lower = planet.lower()
        
        # Check exaltation
        if planet_lower in self.exaltation_degrees:
            exalt_rasi, exalt_degree = self.exaltation_degrees[planet_lower]
            if rasi == exalt_rasi:
                return PlanetaryDignity.EXALTED
        
        # Check debilitation
        if planet_lower in self.debilitation_degrees:
            debil_rasi, debil_degree = self.debilitation_degrees[planet_lower]
            if rasi == debil_rasi:
                return PlanetaryDignity.DEBILITATED
        
        # Check own sign
        if planet_lower in self.own_signs:
            if rasi in self.own_signs[planet_lower]:
                return PlanetaryDignity.OWN_SIGN
        
        # Check moolatrikona
        if planet_lower in self.moolatrikona_signs:
            mool_rasi, min_deg, max_deg = self.moolatrikona_signs[planet_lower]
            if rasi == mool_rasi and min_deg <= degree <= max_deg:
                return PlanetaryDignity.MOOLATRIKONA
        
        # Check friendship
        if planet_lower in self.friendship_table:
            friends = self.friendship_table[planet_lower]['friends']
            enemies = self.friendship_table[planet_lower]['enemies']
            
            # Get rasi lord
            rasi_lord = self._get_rasi_lord(rasi)
            
            if rasi_lord in friends:
                return PlanetaryDignity.FRIENDLY
            elif rasi_lord in enemies:
                return PlanetaryDignity.ENEMY
        
        return PlanetaryDignity.NEUTRAL
    
    def _calculate_planetary_strength(
        self, 
        planet: str, 
        longitude: float, 
        dignity: PlanetaryDignity
    ) -> PlanetaryStrength:
        """Calculate planetary strength points."""
        # Basic strength based on dignity
        dignity_points = {
            PlanetaryDignity.EXALTED: 20.0,
            PlanetaryDignity.MOOLATRIKONA: 18.0,
            PlanetaryDignity.OWN_SIGN: 15.0,
            PlanetaryDignity.FRIENDLY: 10.0,
            PlanetaryDignity.NEUTRAL: 5.0,
            PlanetaryDignity.ENEMY: 2.0,
            PlanetaryDignity.DEBILITATED: 0.0
        }
        
        base_strength = dignity_points.get(dignity, 5.0)
        
        # Additional strength factors can be added here
        # (Shadbala, aspects, etc.)
        
        return PlanetaryStrength(
            dignity=dignity,
            strength_points=base_strength,
            shadbala_points=0.0,  # To be calculated separately
            aspects_received=[],
            aspects_given=[]
        )
    
    def _calculate_house_cusps(self, lagna_longitude: float) -> List[float]:
        """Calculate house cusps using equal house system."""
        cusps = []
        lagna_rasi = int(lagna_longitude // 30)
        lagna_degree = lagna_longitude % 30
        
        for house in range(12):
            cusp_rasi = (lagna_rasi + house) % 12
            cusp_longitude = cusp_rasi * 30 + lagna_degree
            cusps.append(cusp_longitude % 360)
        
        return cusps
    
    def _calculate_aspects(self, chart_positions: Dict[str, ChartPosition]) -> Dict[str, List[str]]:
        """Calculate planetary aspects."""
        aspects = {}
        
        # Standard Vedic aspects
        aspect_rules = {
            'mars': [4, 7, 8],      # 4th, 7th, 8th houses
            'jupiter': [5, 7, 9],   # 5th, 7th, 9th houses
            'saturn': [3, 7, 10],   # 3rd, 7th, 10th houses
            'rahu': [5, 7, 9],      # Same as Jupiter
            'ketu': [5, 7, 9]       # Same as Jupiter
        }
        
        # All planets aspect 7th house
        default_aspects = [7]
        
        for planet_name, position in chart_positions.items():
            planet_aspects = []
            planet_house = position.house
            
            # Get aspect houses for this planet
            if planet_name.lower() in aspect_rules:
                aspect_houses = aspect_rules[planet_name.lower()]
            else:
                aspect_houses = default_aspects
            
            # Find planets in aspected houses
            for aspect_house in aspect_houses:
                target_house = ((planet_house - 1 + aspect_house - 1) % 12) + 1
                
                for other_planet, other_position in chart_positions.items():
                    if other_planet != planet_name and other_position.house == target_house:
                        planet_aspects.append(other_planet)
            
            aspects[planet_name] = planet_aspects
        
        return aspects
    
    def _identify_yogas(self, chart_positions: Dict[str, ChartPosition]) -> List[str]:
        """Identify yoga formations in the chart."""
        yogas = []
        
        # Simple yoga identification
        # This can be expanded with more complex yoga rules
        
        # Check for planets in own signs
        for planet_name, position in chart_positions.items():
            if position.dignity == PlanetaryDignity.OWN_SIGN:
                yogas.append(f"{planet_name} in own sign")
        
        # Check for exalted planets
        for planet_name, position in chart_positions.items():
            if position.dignity == PlanetaryDignity.EXALTED:
                yogas.append(f"{planet_name} exalted")
        
        # Check for conjunctions (planets in same house)
        house_occupants = {}
        for planet_name, position in chart_positions.items():
            house = position.house
            if house not in house_occupants:
                house_occupants[house] = []
            house_occupants[house].append(planet_name)
        
        for house, planets in house_occupants.items():
            if len(planets) > 1:
                yogas.append(f"Conjunction in house {house}: {', '.join(planets)}")
        
        return yogas
    
    def _calculate_strength_summary(self, chart_positions: Dict[str, ChartPosition]) -> Dict[str, float]:
        """Calculate overall strength summary for the chart."""
        summary = {}
        
        total_strength = 0.0
        planet_count = 0
        
        for planet_name, position in chart_positions.items():
            strength = position.strength.strength_points
            summary[planet_name] = strength
            total_strength += strength
            planet_count += 1
        
        if planet_count > 0:
            summary['average_strength'] = total_strength / planet_count
            summary['total_strength'] = total_strength
        
        return summary
    
    def _get_chart_names(self) -> Dict[DivisionalChart, str]:
        """Get traditional names for divisional charts."""
        return {
            DivisionalChart.D1: "Rasi Chart (Birth Chart)",
            DivisionalChart.D2: "Hora Chart (Wealth)",
            DivisionalChart.D3: "Drekkana Chart (Siblings)",
            DivisionalChart.D4: "Chaturthamsa Chart (Fortune)",
            DivisionalChart.D5: "Panchamamsa Chart (Fame)",
            DivisionalChart.D6: "Shashthamsa Chart (Health)",
            DivisionalChart.D7: "Saptamsa Chart (Children)",
            DivisionalChart.D8: "Ashtamsa Chart (Longevity)",
            DivisionalChart.D9: "Navamsa Chart (Marriage)",
            DivisionalChart.D10: "Dasamsa Chart (Career)",
            DivisionalChart.D11: "Rudramsa Chart (Destruction)",
            DivisionalChart.D12: "Dvadasamsa Chart (Parents)",
            DivisionalChart.D16: "Shodasamsa Chart (Vehicles)",
            DivisionalChart.D20: "Vimsamsa Chart (Spirituality)",
            DivisionalChart.D24: "Chaturvimsamsa Chart (Learning)",
            DivisionalChart.D27: "Nakshatramsa Chart (Strengths/Weaknesses)",
            DivisionalChart.D30: "Trimsamsa Chart (Misfortunes)",
            DivisionalChart.D40: "Khavedamsa Chart (Maternal)",
            DivisionalChart.D45: "Akshavedamsa Chart (Paternal)",
            DivisionalChart.D60: "Shashtyamsa Chart (Karma)"
        }
    
    def _get_exaltation_degrees(self) -> Dict[str, Tuple[int, float]]:
        """Get exaltation signs and degrees for planets."""
        return {
            'sun': (0, 10.0),      # Aries 10°
            'moon': (1, 3.0),      # Taurus 3°
            'mars': (9, 28.0),     # Capricorn 28°
            'mercury': (5, 15.0),  # Virgo 15°
            'jupiter': (3, 5.0),   # Cancer 5°
            'venus': (11, 27.0),   # Pisces 27°
            'saturn': (6, 20.0),   # Libra 20°
            'rahu': (2, 20.0),     # Gemini 20°
            'ketu': (8, 20.0)      # Sagittarius 20°
        }
    
    def _get_debilitation_degrees(self) -> Dict[str, Tuple[int, float]]:
        """Get debilitation signs and degrees for planets."""
        return {
            'sun': (6, 10.0),      # Libra 10°
            'moon': (7, 3.0),      # Scorpio 3°
            'mars': (3, 28.0),     # Cancer 28°
            'mercury': (11, 15.0), # Pisces 15°
            'jupiter': (9, 5.0),   # Capricorn 5°
            'venus': (5, 27.0),    # Virgo 27°
            'saturn': (0, 20.0),   # Aries 20°
            'rahu': (8, 20.0),     # Sagittarius 20°
            'ketu': (2, 20.0)      # Gemini 20°
        }
    
    def _get_own_signs(self) -> Dict[str, List[int]]:
        """Get own signs for planets."""
        return {
            'sun': [4],           # Leo
            'moon': [3],          # Cancer
            'mars': [0, 7],       # Aries, Scorpio
            'mercury': [2, 5],    # Gemini, Virgo
            'jupiter': [8, 11],   # Sagittarius, Pisces
            'venus': [1, 6],      # Taurus, Libra
            'saturn': [9, 10],    # Capricorn, Aquarius
            'rahu': [],           # No own signs
            'ketu': []            # No own signs
        }
    
    def _get_moolatrikona_signs(self) -> Dict[str, Tuple[int, float, float]]:
        """Get moolatrikona signs with degree ranges."""
        return {
            'sun': (4, 0.0, 20.0),      # Leo 0°-20°
            'moon': (1, 3.0, 30.0),     # Taurus 3°-30°
            'mars': (0, 0.0, 12.0),     # Aries 0°-12°
            'mercury': (5, 15.0, 20.0), # Virgo 15°-20°
            'jupiter': (8, 0.0, 10.0),  # Sagittarius 0°-10°
            'venus': (6, 0.0, 15.0),    # Libra 0°-15°
            'saturn': (10, 0.0, 20.0)   # Aquarius 0°-20°
        }
    
    def _get_friendship_table(self) -> Dict[str, Dict[str, List[str]]]:
        """Get planetary friendship relationships."""
        return {
            'sun': {
                'friends': ['moon', 'mars', 'jupiter'],
                'enemies': ['venus', 'saturn', 'rahu', 'ketu'],
                'neutral': ['mercury']
            },
            'moon': {
                'friends': ['sun', 'mercury'],
                'enemies': ['rahu', 'ketu'],
                'neutral': ['mars', 'jupiter', 'venus', 'saturn']
            },
            'mars': {
                'friends': ['sun', 'moon', 'jupiter'],
                'enemies': ['mercury', 'rahu', 'ketu'],
                'neutral': ['venus', 'saturn']
            },
            'mercury': {
                'friends': ['sun', 'venus'],
                'enemies': ['moon', 'mars', 'rahu', 'ketu'],
                'neutral': ['jupiter', 'saturn']
            },
            'jupiter': {
                'friends': ['sun', 'moon', 'mars'],
                'enemies': ['mercury', 'venus', 'rahu', 'ketu'],
                'neutral': ['saturn']
            },
            'venus': {
                'friends': ['mercury', 'saturn', 'rahu', 'ketu'],
                'enemies': ['sun', 'moon', 'mars'],
                'neutral': ['jupiter']
            },
            'saturn': {
                'friends': ['mercury', 'venus', 'rahu', 'ketu'],
                'enemies': ['sun', 'moon', 'mars'],
                'neutral': ['jupiter']
            },
            'rahu': {
                'friends': ['venus', 'saturn'],
                'enemies': ['sun', 'moon', 'mars', 'jupiter'],
                'neutral': ['mercury', 'ketu']
            },
            'ketu': {
                'friends': ['venus', 'saturn'],
                'enemies': ['sun', 'moon', 'mars', 'jupiter'],
                'neutral': ['mercury', 'rahu']
            }
        }
    
    def _get_rasi_lord(self, rasi: int) -> str:
        """Get the lord of a rasi."""
        rasi_lords = [
            'mars',     # Aries
            'venus',    # Taurus
            'mercury',  # Gemini
            'moon',     # Cancer
            'sun',      # Leo
            'mercury',  # Virgo
            'venus',    # Libra
            'mars',     # Scorpio
            'jupiter',  # Sagittarius
            'saturn',   # Capricorn
            'saturn',   # Aquarius
            'jupiter'   # Pisces
        ]
        return rasi_lords[rasi] if 0 <= rasi < 12 else 'unknown'
