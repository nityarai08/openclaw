"""
Yoga and Dosha identification system.

This module implements comprehensive yoga detection algorithms for beneficial
and challenging combinations, including raja yogas, doshas, and strength assessments.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import math

from ..core.data_models import PlanetaryPosition
from .divisional_charts import ChartPosition, DivisionalChartData


class YogaType(Enum):
    """Types of yogas."""
    RAJA_YOGA = "Raja Yoga"
    DHANA_YOGA = "Dhana Yoga"
    MAHAPURUSHA_YOGA = "Mahapurusha Yoga"
    PANCHA_MAHAPURUSHA = "Pancha Mahapurusha"
    GAJA_KESARI = "Gaja Kesari"
    CHANDRA_MANGAL = "Chandra Mangal"
    BUDH_ADITYA = "Budh Aditya"
    GURU_MANGAL = "Guru Mangal"
    NEECHA_BHANGA = "Neecha Bhanga"
    VIPARITA_RAJA = "Viparita Raja"
    EXCHANGE_YOGA = "Exchange Yoga"
    CONJUNCTION_YOGA = "Conjunction Yoga"


class DoshaType(Enum):
    """Types of doshas."""
    MANGLIK_DOSHA = "Manglik Dosha"
    KAAL_SARPA_DOSHA = "Kaal Sarpa Dosha"
    PITRA_DOSHA = "Pitra Dosha"
    NADI_DOSHA = "Nadi Dosha"
    GRAHAN_DOSHA = "Grahan Dosha"
    GURU_CHANDAL = "Guru Chandal"
    KEMADRUM_DOSHA = "Kemadrum Dosha"
    SHAKATA_DOSHA = "Shakata Dosha"
    DARIDRA_YOGA = "Daridra Yoga"
    PAPAKARTARI_YOGA = "Papakartari Yoga"


class YogaStrength(Enum):
    """Yoga strength levels."""
    VERY_STRONG = "Very Strong"
    STRONG = "Strong"
    MODERATE = "Moderate"
    WEAK = "Weak"
    VERY_WEAK = "Very Weak"


@dataclass
class YogaInfo:
    """Information about a detected yoga."""
    name: str
    type: YogaType
    strength: YogaStrength
    planets_involved: List[str]
    houses_involved: List[int]
    description: str
    effects: List[str]
    strength_points: float
    formation_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DoshaInfo:
    """Information about a detected dosha."""
    name: str
    type: DoshaType
    severity: YogaStrength  # Using same enum for severity levels
    planets_involved: List[str]
    houses_involved: List[int]
    description: str
    effects: List[str]
    remedies: List[str]
    strength_points: float  # Negative for doshas
    formation_details: Dict[str, Any] = field(default_factory=dict)


class YogaDoshaAnalyzer:
    """Comprehensive yoga and dosha identification system."""
    
    def __init__(self):
        self.benefic_planets = ['jupiter', 'venus', 'mercury', 'moon']
        self.malefic_planets = ['mars', 'saturn', 'rahu', 'ketu', 'sun']
        self.kendra_houses = [1, 4, 7, 10]
        self.trikona_houses = [1, 5, 9]
        self.dusthana_houses = [6, 8, 12]
        self.upachaya_houses = [3, 6, 10, 11]
    
    def analyze_yogas_and_doshas(
        self,
        planetary_positions: Dict[str, PlanetaryPosition],
        divisional_charts: Dict[str, DivisionalChartData],
        lagna_longitude: float
    ) -> Tuple[List[YogaInfo], List[DoshaInfo]]:
        """
        Comprehensive analysis of yogas and doshas.
        
        Args:
            planetary_positions: Base planetary positions
            divisional_charts: All divisional charts
            lagna_longitude: Lagna longitude for house calculations
            
        Returns:
            Tuple of (yogas_list, doshas_list)
        """
        yogas = []
        doshas = []
        
        # Get D1 chart for primary analysis
        d1_chart = divisional_charts.get('D1')
        if not d1_chart:
            return yogas, doshas
        
        # Analyze Raja Yogas
        yogas.extend(self._analyze_raja_yogas(d1_chart))
        
        # Analyze Dhana Yogas
        yogas.extend(self._analyze_dhana_yogas(d1_chart))
        
        # Analyze Mahapurusha Yogas
        yogas.extend(self._analyze_mahapurusha_yogas(d1_chart))
        
        # Analyze Special Yogas
        yogas.extend(self._analyze_special_yogas(d1_chart))
        
        # Analyze Exchange Yogas
        yogas.extend(self._analyze_exchange_yogas(d1_chart))
        
        # Analyze Conjunction Yogas
        yogas.extend(self._analyze_conjunction_yogas(d1_chart))
        
        # Analyze Neecha Bhanga Yogas
        yogas.extend(self._analyze_neecha_bhanga_yogas(d1_chart))
        
        # Analyze Doshas
        doshas.extend(self._analyze_manglik_dosha(d1_chart))
        doshas.extend(self._analyze_kaal_sarpa_dosha(d1_chart))
        doshas.extend(self._analyze_grahan_dosha(d1_chart))
        doshas.extend(self._analyze_guru_chandal_dosha(d1_chart))
        doshas.extend(self._analyze_kemadrum_dosha(d1_chart))
        doshas.extend(self._analyze_papakartari_yoga(d1_chart))
        
        return yogas, doshas
    
    def _analyze_raja_yogas(self, chart: DivisionalChartData) -> List[YogaInfo]:
        """Analyze Raja Yogas (combinations of Kendra and Trikona lords)."""
        yogas = []
        positions = chart.planetary_positions
        
        # Get house lords
        house_lords = self._get_house_lords(chart)
        
        # Check for Kendra-Trikona combinations
        kendra_lords = [house_lords.get(house, '') for house in self.kendra_houses]
        trikona_lords = [house_lords.get(house, '') for house in self.trikona_houses]
        
        for kendra_lord in kendra_lords:
            for trikona_lord in trikona_lords:
                if kendra_lord and trikona_lord and kendra_lord != trikona_lord:
                    # Check if they are conjunct or in mutual aspect
                    if self._are_planets_connected(kendra_lord, trikona_lord, positions):
                        strength = self._calculate_yoga_strength([kendra_lord, trikona_lord], positions)
                        
                        yogas.append(YogaInfo(
                            name=f"Raja Yoga ({kendra_lord.title()}-{trikona_lord.title()})",
                            type=YogaType.RAJA_YOGA,
                            strength=strength,
                            planets_involved=[kendra_lord, trikona_lord],
                            houses_involved=self._get_planet_houses([kendra_lord, trikona_lord], positions),
                            description=f"Combination of Kendra lord {kendra_lord.title()} and Trikona lord {trikona_lord.title()}",
                            effects=["Power and authority", "Success in endeavors", "Leadership qualities"],
                            strength_points=self._get_strength_points(strength)
                        ))
        
        return yogas
    
    def _analyze_dhana_yogas(self, chart: DivisionalChartData) -> List[YogaInfo]:
        """Analyze Dhana Yogas (wealth combinations)."""
        yogas = []
        positions = chart.planetary_positions
        house_lords = self._get_house_lords(chart)
        
        # 2nd and 11th house lord combinations
        second_lord = house_lords.get(2, '')
        eleventh_lord = house_lords.get(11, '')
        
        if second_lord and eleventh_lord and self._are_planets_connected(second_lord, eleventh_lord, positions):
            strength = self._calculate_yoga_strength([second_lord, eleventh_lord], positions)
            
            yogas.append(YogaInfo(
                name=f"Dhana Yoga (2nd-11th Lords)",
                type=YogaType.DHANA_YOGA,
                strength=strength,
                planets_involved=[second_lord, eleventh_lord],
                houses_involved=[2, 11],
                description="Combination of 2nd and 11th house lords for wealth",
                effects=["Financial prosperity", "Multiple income sources", "Material gains"],
                strength_points=self._get_strength_points(strength)
            ))
        
        # Check for planets in 2nd and 11th houses
        planets_in_2nd = self._get_planets_in_house(2, positions)
        planets_in_11th = self._get_planets_in_house(11, positions)
        
        if planets_in_2nd and planets_in_11th:
            benefic_in_wealth_houses = [p for p in planets_in_2nd + planets_in_11th if p in self.benefic_planets]
            if benefic_in_wealth_houses:
                yogas.append(YogaInfo(
                    name="Dhana Yoga (Benefics in Wealth Houses)",
                    type=YogaType.DHANA_YOGA,
                    strength=YogaStrength.MODERATE,
                    planets_involved=benefic_in_wealth_houses,
                    houses_involved=[2, 11],
                    description="Benefic planets in 2nd and 11th houses",
                    effects=["Steady income", "Financial stability", "Accumulation of wealth"],
                    strength_points=15.0
                ))
        
        return yogas
    
    def _analyze_mahapurusha_yogas(self, chart: DivisionalChartData) -> List[YogaInfo]:
        """Analyze Pancha Mahapurusha Yogas."""
        yogas = []
        positions = chart.planetary_positions
        
        mahapurusha_planets = {
            'mars': 'Ruchaka',
            'mercury': 'Bhadra',
            'jupiter': 'Hamsa',
            'venus': 'Malavya',
            'saturn': 'Sasa'
        }
        
        for planet, yoga_name in mahapurusha_planets.items():
            if planet in positions:
                position = positions[planet]
                
                # Check if planet is in Kendra and in own sign, exaltation, or moolatrikona
                if (position.house in self.kendra_houses and 
                    position.dignity.value in ['Own Sign', 'Exalted', 'Moolatrikona']):
                    
                    strength = YogaStrength.STRONG if position.dignity.value == 'Exalted' else YogaStrength.MODERATE
                    
                    yogas.append(YogaInfo(
                        name=f"{yoga_name} Yoga",
                        type=YogaType.MAHAPURUSHA_YOGA,
                        strength=strength,
                        planets_involved=[planet],
                        houses_involved=[position.house],
                        description=f"{planet.title()} in Kendra in own sign/exaltation",
                        effects=self._get_mahapurusha_effects(planet),
                        strength_points=self._get_strength_points(strength)
                    ))
        
        return yogas
    
    def _analyze_special_yogas(self, chart: DivisionalChartData) -> List[YogaInfo]:
        """Analyze special yogas like Gaja Kesari, Chandra Mangal, etc."""
        yogas = []
        positions = chart.planetary_positions
        
        # Gaja Kesari Yoga (Jupiter and Moon)
        if 'jupiter' in positions and 'moon' in positions:
            jupiter_house = positions['jupiter'].house
            moon_house = positions['moon'].house
            
            # Check if Jupiter is in Kendra from Moon
            house_diff = abs(jupiter_house - moon_house)
            if house_diff in [0, 3, 6, 9] or house_diff == 0:  # Kendra relationship
                strength = self._calculate_yoga_strength(['jupiter', 'moon'], positions)
                
                yogas.append(YogaInfo(
                    name="Gaja Kesari Yoga",
                    type=YogaType.GAJA_KESARI,
                    strength=strength,
                    planets_involved=['jupiter', 'moon'],
                    houses_involved=[jupiter_house, moon_house],
                    description="Jupiter in Kendra from Moon",
                    effects=["Wisdom and intelligence", "Respect in society", "Good fortune"],
                    strength_points=self._get_strength_points(strength)
                ))
        
        # Chandra Mangal Yoga (Moon and Mars conjunction)
        if 'moon' in positions and 'mars' in positions:
            if positions['moon'].house == positions['mars'].house:
                strength = self._calculate_yoga_strength(['moon', 'mars'], positions)
                
                yogas.append(YogaInfo(
                    name="Chandra Mangal Yoga",
                    type=YogaType.CHANDRA_MANGAL,
                    strength=strength,
                    planets_involved=['moon', 'mars'],
                    houses_involved=[positions['moon'].house],
                    description="Moon and Mars conjunction",
                    effects=["Business acumen", "Property gains", "Material success"],
                    strength_points=self._get_strength_points(strength)
                ))
        
        # Budh Aditya Yoga (Sun and Mercury conjunction)
        if 'sun' in positions and 'mercury' in positions:
            if positions['sun'].house == positions['mercury'].house:
                strength = self._calculate_yoga_strength(['sun', 'mercury'], positions)
                
                yogas.append(YogaInfo(
                    name="Budh Aditya Yoga",
                    type=YogaType.BUDH_ADITYA,
                    strength=strength,
                    planets_involved=['sun', 'mercury'],
                    houses_involved=[positions['sun'].house],
                    description="Sun and Mercury conjunction",
                    effects=["Intelligence", "Communication skills", "Administrative abilities"],
                    strength_points=self._get_strength_points(strength)
                ))
        
        return yogas
    
    def _analyze_exchange_yogas(self, chart: DivisionalChartData) -> List[YogaInfo]:
        """Analyze Parivartana (Exchange) Yogas."""
        yogas = []
        positions = chart.planetary_positions
        house_lords = self._get_house_lords(chart)
        
        # Check for mutual exchange of signs
        for planet1, position1 in positions.items():
            for planet2, position2 in positions.items():
                if planet1 != planet2:
                    # Check if planet1 is in planet2's sign and vice versa
                    if (self._is_planet_in_others_sign(planet1, planet2, position1, position2) and
                        self._is_planet_in_others_sign(planet2, planet1, position2, position1)):
                        
                        strength = self._calculate_yoga_strength([planet1, planet2], positions)
                        
                        yogas.append(YogaInfo(
                            name=f"Exchange Yoga ({planet1.title()}-{planet2.title()})",
                            type=YogaType.EXCHANGE_YOGA,
                            strength=strength,
                            planets_involved=[planet1, planet2],
                            houses_involved=[position1.house, position2.house],
                            description=f"Mutual exchange between {planet1.title()} and {planet2.title()}",
                            effects=["Mutual strengthening", "Enhanced results", "Karmic connections"],
                            strength_points=self._get_strength_points(strength)
                        ))
        
        return yogas
    
    def _analyze_conjunction_yogas(self, chart: DivisionalChartData) -> List[YogaInfo]:
        """Analyze significant conjunction yogas."""
        yogas = []
        positions = chart.planetary_positions
        
        # Group planets by house
        house_groups = {}
        for planet, position in positions.items():
            house = position.house
            if house not in house_groups:
                house_groups[house] = []
            house_groups[house].append(planet)
        
        # Analyze conjunctions
        for house, planets in house_groups.items():
            if len(planets) > 1:
                # Check for beneficial conjunctions
                benefic_count = sum(1 for p in planets if p in self.benefic_planets)
                malefic_count = sum(1 for p in planets if p in self.malefic_planets)
                
                if benefic_count >= 2:
                    strength = YogaStrength.MODERATE
                    if house in self.kendra_houses or house in self.trikona_houses:
                        strength = YogaStrength.STRONG
                    
                    yogas.append(YogaInfo(
                        name=f"Benefic Conjunction in House {house}",
                        type=YogaType.CONJUNCTION_YOGA,
                        strength=strength,
                        planets_involved=planets,
                        houses_involved=[house],
                        description=f"Multiple benefic planets in house {house}",
                        effects=["Enhanced positive results", "Multiple blessings", "Harmonious energy"],
                        strength_points=self._get_strength_points(strength)
                    ))
        
        return yogas
    
    def _analyze_neecha_bhanga_yogas(self, chart: DivisionalChartData) -> List[YogaInfo]:
        """Analyze Neecha Bhanga (Debilitation Cancellation) Yogas."""
        yogas = []
        positions = chart.planetary_positions
        
        for planet, position in positions.items():
            if position.dignity.value == 'Debilitated':
                # Check for cancellation conditions
                cancellation_found = False
                cancellation_reason = ""
                
                # Rule 1: Dispositor of debilitated planet in Kendra
                dispositor = self._get_sign_lord(position.rasi)
                if dispositor in positions:
                    dispositor_house = positions[dispositor].house
                    if dispositor_house in self.kendra_houses:
                        cancellation_found = True
                        cancellation_reason = f"Dispositor {dispositor.title()} in Kendra"
                
                # Rule 2: Exaltation lord in Kendra
                exalt_lord = self._get_exaltation_lord(planet)
                if exalt_lord and exalt_lord in positions:
                    exalt_house = positions[exalt_lord].house
                    if exalt_house in self.kendra_houses:
                        cancellation_found = True
                        cancellation_reason = f"Exaltation lord {exalt_lord.title()} in Kendra"
                
                if cancellation_found:
                    yogas.append(YogaInfo(
                        name=f"Neecha Bhanga Yoga ({planet.title()})",
                        type=YogaType.NEECHA_BHANGA,
                        strength=YogaStrength.MODERATE,
                        planets_involved=[planet],
                        houses_involved=[position.house],
                        description=f"Debilitation of {planet.title()} cancelled: {cancellation_reason}",
                        effects=["Transformation of weakness to strength", "Unexpected gains", "Karmic redemption"],
                        strength_points=12.0
                    ))
        
        return yogas
    
    def _analyze_manglik_dosha(self, chart: DivisionalChartData) -> List[DoshaInfo]:
        """Analyze Manglik Dosha."""
        doshas = []
        positions = chart.planetary_positions
        
        if 'mars' in positions:
            mars_house = positions['mars'].house
            
            # Manglik houses: 1, 2, 4, 7, 8, 12
            manglik_houses = [1, 2, 4, 7, 8, 12]
            
            if mars_house in manglik_houses:
                # Calculate severity
                severity_map = {
                    1: YogaStrength.STRONG,
                    2: YogaStrength.MODERATE,
                    4: YogaStrength.MODERATE,
                    7: YogaStrength.VERY_STRONG,
                    8: YogaStrength.STRONG,
                    12: YogaStrength.MODERATE
                }
                
                severity = severity_map.get(mars_house, YogaStrength.MODERATE)
                
                doshas.append(DoshaInfo(
                    name="Manglik Dosha",
                    type=DoshaType.MANGLIK_DOSHA,
                    severity=severity,
                    planets_involved=['mars'],
                    houses_involved=[mars_house],
                    description=f"Mars in {mars_house}th house causing Manglik Dosha",
                    effects=["Delays in marriage", "Marital discord", "Relationship challenges"],
                    remedies=["Marry another Manglik", "Kuja Dosha remedies", "Mars pacification rituals"],
                    strength_points=-self._get_strength_points(severity)
                ))
        
        return doshas
    
    def _analyze_kaal_sarpa_dosha(self, chart: DivisionalChartData) -> List[DoshaInfo]:
        """Analyze Kaal Sarpa Dosha."""
        doshas = []
        positions = chart.planetary_positions
        
        if 'rahu' in positions and 'ketu' in positions:
            rahu_house = positions['rahu'].house
            ketu_house = positions['ketu'].house
            
            # Check if all planets are between Rahu and Ketu
            other_planets = [p for p in positions.keys() if p not in ['rahu', 'ketu', 'lagna']]
            
            # Calculate if planets are hemmed between Rahu and Ketu
            planets_between = 0
            total_planets = len(other_planets)
            
            for planet in other_planets:
                planet_house = positions[planet].house
                if self._is_between_rahu_ketu(planet_house, rahu_house, ketu_house):
                    planets_between += 1
            
            # If most planets are between Rahu-Ketu, it's Kaal Sarpa
            if planets_between >= total_planets * 0.7:  # 70% threshold
                severity = YogaStrength.STRONG if planets_between == total_planets else YogaStrength.MODERATE
                
                doshas.append(DoshaInfo(
                    name="Kaal Sarpa Dosha",
                    type=DoshaType.KAAL_SARPA_DOSHA,
                    severity=severity,
                    planets_involved=['rahu', 'ketu'],
                    houses_involved=[rahu_house, ketu_house],
                    description=f"All planets hemmed between Rahu (H{rahu_house}) and Ketu (H{ketu_house})",
                    effects=["Obstacles in life", "Delays in achievements", "Karmic challenges"],
                    remedies=["Rahu-Ketu remedies", "Sarpa Dosha puja", "Spiritual practices"],
                    strength_points=-self._get_strength_points(severity)
                ))
        
        return doshas
    
    def _analyze_grahan_dosha(self, chart: DivisionalChartData) -> List[DoshaInfo]:
        """Analyze Grahan Dosha (Eclipse Dosha)."""
        doshas = []
        positions = chart.planetary_positions
        
        # Sun-Rahu conjunction
        if ('sun' in positions and 'rahu' in positions and 
            positions['sun'].house == positions['rahu'].house):
            
            doshas.append(DoshaInfo(
                name="Surya Grahan Dosha",
                type=DoshaType.GRAHAN_DOSHA,
                severity=YogaStrength.MODERATE,
                planets_involved=['sun', 'rahu'],
                houses_involved=[positions['sun'].house],
                description="Sun conjunct with Rahu causing Solar Eclipse Dosha",
                effects=["Father-related issues", "Authority problems", "Health concerns"],
                remedies=["Sun remedies", "Rahu pacification", "Surya mantras"],
                strength_points=-10.0
            ))
        
        # Moon-Rahu conjunction
        if ('moon' in positions and 'rahu' in positions and 
            positions['moon'].house == positions['rahu'].house):
            
            doshas.append(DoshaInfo(
                name="Chandra Grahan Dosha",
                type=DoshaType.GRAHAN_DOSHA,
                severity=YogaStrength.MODERATE,
                planets_involved=['moon', 'rahu'],
                houses_involved=[positions['moon'].house],
                description="Moon conjunct with Rahu causing Lunar Eclipse Dosha",
                effects=["Mother-related issues", "Mental stress", "Emotional instability"],
                remedies=["Moon remedies", "Rahu pacification", "Chandra mantras"],
                strength_points=-10.0
            ))
        
        return doshas
    
    def _analyze_guru_chandal_dosha(self, chart: DivisionalChartData) -> List[DoshaInfo]:
        """Analyze Guru Chandal Dosha."""
        doshas = []
        positions = chart.planetary_positions
        
        # Jupiter-Rahu conjunction
        if ('jupiter' in positions and 'rahu' in positions and 
            positions['jupiter'].house == positions['rahu'].house):
            
            doshas.append(DoshaInfo(
                name="Guru Chandal Dosha",
                type=DoshaType.GURU_CHANDAL,
                severity=YogaStrength.MODERATE,
                planets_involved=['jupiter', 'rahu'],
                houses_involved=[positions['jupiter'].house],
                description="Jupiter conjunct with Rahu",
                effects=["Spiritual confusion", "Wrong guidance", "Religious conflicts"],
                remedies=["Jupiter strengthening", "Rahu remedies", "Spiritual practices"],
                strength_points=-12.0
            ))
        
        return doshas
    
    def _analyze_kemadrum_dosha(self, chart: DivisionalChartData) -> List[DoshaInfo]:
        """Analyze Kemadrum Dosha."""
        doshas = []
        positions = chart.planetary_positions
        
        if 'moon' in positions:
            moon_house = positions['moon'].house
            
            # Check if Moon has no planets in adjacent houses
            prev_house = (moon_house - 2) % 12 + 1
            next_house = moon_house % 12 + 1
            
            planets_in_adjacent = []
            for planet, position in positions.items():
                if planet != 'moon' and position.house in [prev_house, next_house]:
                    planets_in_adjacent.append(planet)
            
            if not planets_in_adjacent:
                doshas.append(DoshaInfo(
                    name="Kemadrum Dosha",
                    type=DoshaType.KEMADRUM_DOSHA,
                    severity=YogaStrength.MODERATE,
                    planets_involved=['moon'],
                    houses_involved=[moon_house],
                    description="Moon with no planets in adjacent houses",
                    effects=["Mental stress", "Lack of support", "Emotional isolation"],
                    remedies=["Moon strengthening", "Mental peace practices", "Social connections"],
                    strength_points=-8.0
                ))
        
        return doshas
    
    def _analyze_papakartari_yoga(self, chart: DivisionalChartData) -> List[DoshaInfo]:
        """Analyze Papakartari Yoga."""
        doshas = []
        positions = chart.planetary_positions
        
        # Check each planet for malefic hemming
        for planet, position in positions.items():
            if planet in ['rahu', 'ketu']:  # Skip nodes for this analysis
                continue
                
            planet_house = position.house
            prev_house = (planet_house - 2) % 12 + 1
            next_house = planet_house % 12 + 1
            
            malefics_adjacent = []
            for other_planet, other_position in positions.items():
                if (other_planet in self.malefic_planets and 
                    other_position.house in [prev_house, next_house]):
                    malefics_adjacent.append(other_planet)
            
            if len(malefics_adjacent) >= 2:
                doshas.append(DoshaInfo(
                    name=f"Papakartari Yoga ({planet.title()})",
                    type=DoshaType.PAPAKARTARI_YOGA,
                    severity=YogaStrength.MODERATE,
                    planets_involved=[planet] + malefics_adjacent,
                    houses_involved=[planet_house, prev_house, next_house],
                    description=f"{planet.title()} hemmed between malefics",
                    effects=["Obstacles", "Delays", "Negative influences"],
                    remedies=["Strengthen the hemmed planet", "Malefic pacification", "Protective measures"],
                    strength_points=-6.0
                ))
        
        return doshas
    
    # Helper methods
    
    def _get_house_lords(self, chart: DivisionalChartData) -> Dict[int, str]:
        """Get house lords based on chart positions."""
        house_lords = {}
        
        # Standard house lordship
        lordship_map = {
            0: 'mars',     # Aries
            1: 'venus',    # Taurus
            2: 'mercury',  # Gemini
            3: 'moon',     # Cancer
            4: 'sun',      # Leo
            5: 'mercury',  # Virgo
            6: 'venus',    # Libra
            7: 'mars',     # Scorpio
            8: 'jupiter',  # Sagittarius
            9: 'saturn',   # Capricorn
            10: 'saturn',  # Aquarius
            11: 'jupiter'  # Pisces
        }
        
        # Calculate house cusps and determine lords
        for house in range(1, 13):
            # Simplified: assume equal house system
            if 'lagna' in chart.planetary_positions:
                lagna_rasi = chart.planetary_positions['lagna'].rasi
                house_rasi = (lagna_rasi + house - 1) % 12
                house_lords[house] = lordship_map.get(house_rasi, '')
        
        return house_lords
    
    def _are_planets_connected(self, planet1: str, planet2: str, positions: Dict[str, ChartPosition]) -> bool:
        """Check if two planets are connected by conjunction or aspect."""
        if planet1 not in positions or planet2 not in positions:
            return False
        
        pos1 = positions[planet1]
        pos2 = positions[planet2]
        
        # Conjunction (same house)
        if pos1.house == pos2.house:
            return True
        
        # Mutual aspect (simplified - 7th house aspect)
        house_diff = abs(pos1.house - pos2.house)
        if house_diff == 6 or house_diff == 6:  # 7th house aspect
            return True
        
        return False
    
    def _calculate_yoga_strength(self, planets: List[str], positions: Dict[str, ChartPosition]) -> YogaStrength:
        """Calculate overall strength of a yoga."""
        total_strength = 0.0
        planet_count = 0
        
        for planet in planets:
            if planet in positions:
                strength_points = positions[planet].strength.strength_points
                total_strength += strength_points
                planet_count += 1
        
        if planet_count == 0:
            return YogaStrength.VERY_WEAK
        
        average_strength = total_strength / planet_count
        
        if average_strength >= 18:
            return YogaStrength.VERY_STRONG
        elif average_strength >= 15:
            return YogaStrength.STRONG
        elif average_strength >= 10:
            return YogaStrength.MODERATE
        elif average_strength >= 5:
            return YogaStrength.WEAK
        else:
            return YogaStrength.VERY_WEAK
    
    def _get_strength_points(self, strength: YogaStrength) -> float:
        """Convert strength enum to numerical points."""
        strength_map = {
            YogaStrength.VERY_STRONG: 25.0,
            YogaStrength.STRONG: 20.0,
            YogaStrength.MODERATE: 15.0,
            YogaStrength.WEAK: 10.0,
            YogaStrength.VERY_WEAK: 5.0
        }
        return strength_map.get(strength, 10.0)
    
    def _get_planet_houses(self, planets: List[str], positions: Dict[str, ChartPosition]) -> List[int]:
        """Get house positions for a list of planets."""
        houses = []
        for planet in planets:
            if planet in positions:
                houses.append(positions[planet].house)
        return houses
    
    def _get_planets_in_house(self, house: int, positions: Dict[str, ChartPosition]) -> List[str]:
        """Get all planets in a specific house."""
        planets = []
        for planet, position in positions.items():
            if position.house == house:
                planets.append(planet)
        return planets
    
    def _get_mahapurusha_effects(self, planet: str) -> List[str]:
        """Get effects for Mahapurusha yogas."""
        effects_map = {
            'mars': ["Courage and valor", "Military success", "Leadership in action"],
            'mercury': ["Intelligence and learning", "Communication skills", "Business acumen"],
            'jupiter': ["Wisdom and knowledge", "Spiritual growth", "Teaching abilities"],
            'venus': ["Artistic talents", "Beauty and charm", "Material comforts"],
            'saturn': ["Discipline and perseverance", "Administrative skills", "Long-term success"]
        }
        return effects_map.get(planet, ["Enhanced planetary qualities"])
    
    def _is_planet_in_others_sign(self, planet1: str, planet2: str, pos1: ChartPosition, pos2: ChartPosition) -> bool:
        """Check if planet1 is in planet2's sign."""
        # Simplified check - would need full sign lordship logic
        return False  # Placeholder
    
    def _get_sign_lord(self, rasi: int) -> str:
        """Get the lord of a rasi."""
        lordship_map = {
            0: 'mars', 1: 'venus', 2: 'mercury', 3: 'moon',
            4: 'sun', 5: 'mercury', 6: 'venus', 7: 'mars',
            8: 'jupiter', 9: 'saturn', 10: 'saturn', 11: 'jupiter'
        }
        return lordship_map.get(rasi, '')
    
    def _get_exaltation_lord(self, planet: str) -> Optional[str]:
        """Get the lord of planet's exaltation sign."""
        exalt_lords = {
            'sun': 'mars',     # Sun exalts in Aries (Mars' sign)
            'moon': 'venus',   # Moon exalts in Taurus (Venus' sign)
            'mars': 'saturn',  # Mars exalts in Capricorn (Saturn's sign)
            'mercury': 'mercury', # Mercury exalts in Virgo (own sign)
            'jupiter': 'moon', # Jupiter exalts in Cancer (Moon's sign)
            'venus': 'jupiter', # Venus exalts in Pisces (Jupiter's sign)
            'saturn': 'venus'  # Saturn exalts in Libra (Venus' sign)
        }
        return exalt_lords.get(planet)
    
    def _is_between_rahu_ketu(self, planet_house: int, rahu_house: int, ketu_house: int) -> bool:
        """Check if planet is between Rahu and Ketu."""
        # Simplified logic for circular house system
        if rahu_house < ketu_house:
            return rahu_house < planet_house < ketu_house
        else:
            return planet_house > rahu_house or planet_house < ketu_house