"""
Divisional Chart Analyzer for Enhanced Astrological Accuracy

This module provides comprehensive analysis of divisional charts (D1-D16) to enhance
the accuracy of favorability calculations by incorporating specialized chart strengths.
"""

import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..core.data_models import KundaliData, PlanetaryPosition
from ..kundali_generator.comprehensive_ephemeris_engine import ComprehensiveEphemerisEngine


class DivisionalChartAnalyzer:
    """
    Comprehensive analyzer for divisional charts with specialized interpretations.
    
    Analyzes planetary strength and favorability across multiple divisional charts
    to provide enhanced accuracy for timing and life area predictions.
    """
    
    def __init__(self, kundali_data: KundaliData):
        """
        Initialize divisional chart analyzer.
        
        Args:
            kundali_data: Complete kundali data with divisional charts
        """
        self.kundali_data = kundali_data
        self.logger = logging.getLogger(self.__class__.__name__)
        self._ephemeris_engine = ComprehensiveEphemerisEngine()
        
        # Cache divisional charts for quick access
        self._divisional_charts = kundali_data.divisional_charts if kundali_data.divisional_charts else {}
        
        # Chart significance weights for different life areas
        self._chart_weights = {
            'D1': {'general': 1.0, 'personality': 1.0, 'health': 0.8},
            'D2': {'wealth': 1.0, 'family': 0.8, 'speech': 0.7},
            'D3': {'siblings': 1.0, 'courage': 0.9, 'communication': 0.6},
            'D4': {'fortune': 1.0, 'property': 0.9, 'mother': 0.7},
            'D5': {'fame': 1.0, 'intelligence': 0.9, 'children': 0.6},
            'D6': {'health': 1.0, 'enemies': 0.9, 'obstacles': 0.8},
            'D7': {'children': 1.0, 'creativity': 0.8, 'progeny': 0.9},
            'D8': {'longevity': 1.0, 'accidents': 0.9, 'chronic_issues': 0.8},
            'D9': {'dharma': 1.0, 'spouse': 0.9, 'spiritual': 0.8},
            'D10': {'career': 1.0, 'profession': 0.9, 'status': 0.8},
            'D11': {'gains': 1.0, 'income': 0.9, 'fulfillment': 0.7},
            'D12': {'parents': 1.0, 'ancestry': 0.8, 'lineage': 0.7},
            'D16': {'vehicles': 1.0, 'comforts': 0.8, 'happiness': 0.7},
            'D20': {'spirituality': 1.0, 'worship': 0.9, 'devotion': 0.8},
            'D24': {'education': 1.0, 'learning': 0.9, 'knowledge': 0.8},
            'D27': {'strength': 1.0, 'weakness': 0.9, 'vitality': 0.8}
        }
        
        # Initialize chart-specific analyzers
        self._chart_analyzers = {
            'D1': self._analyze_rasi_chart,
            'D2': self._analyze_hora_chart,
            'D3': self._analyze_drekkana_chart,
            'D4': self._analyze_chaturthamsa_chart,
            'D5': self._analyze_panchamamsa_chart,
            'D6': self._analyze_shashthamsa_chart,
            'D7': self._analyze_saptamsa_chart,
            'D9': self._analyze_navamsa_chart,
            'D10': self._analyze_dasamsa_chart,
            'D11': self._analyze_rudramsa_chart,
            'D12': self._analyze_dwadasamsa_chart,
            'D16': self._analyze_shodasamsa_chart,
            'D20': self._analyze_vimsamsa_chart,
            'D24': self._analyze_chaturvimsamsa_chart,
            'D27': self._analyze_nakshatramsa_chart
        }
    
    def calculate_divisional_strength(self, planet_name: str, date: datetime, 
                                    life_area: str = 'general') -> float:
        """
        Calculate comprehensive divisional chart strength for a planet.
        
        Args:
            planet_name: Name of the planet
            date: Date for calculation
            life_area: Specific life area to focus on
            
        Returns:
            Divisional strength score between 0.0 and 1.0
        """
        try:
            total_strength = 0.0
            total_weight = 0.0
            
            # Analyze relevant charts for the life area
            relevant_charts = self._get_relevant_charts(life_area)
            
            for chart_name in relevant_charts:
                if chart_name in self._divisional_charts:
                    chart_strength = self._analyze_chart_strength(
                        chart_name, planet_name, date
                    )
                    chart_weight = self._chart_weights.get(chart_name, {}).get(life_area, 0.5)
                    
                    total_strength += chart_strength * chart_weight
                    total_weight += chart_weight
            
            # Calculate weighted average
            if total_weight > 0:
                divisional_strength = total_strength / total_weight
            else:
                divisional_strength = 0.5  # Neutral fallback
            
            return max(0.0, min(1.0, divisional_strength))
            
        except Exception as e:
            self.logger.error(f"Error calculating divisional strength for {planet_name}: {e}")
            return 0.5
    
    def _get_relevant_charts(self, life_area: str) -> List[str]:
        """Get list of charts most relevant to a specific life area."""
        chart_relevance = {
            'general': ['D1', 'D9', 'D10'],
            'wealth': ['D1', 'D2', 'D11'],
            'health': ['D1', 'D6', 'D8'],
            'career': ['D1', 'D9', 'D10'],
            'relationships': ['D1', 'D7', 'D9'],
            'spirituality': ['D1', 'D9', 'D20'],
            'education': ['D1', 'D9', 'D24'],
            'family': ['D1', 'D2', 'D12'],
            'children': ['D1', 'D5', 'D7'],
            'property': ['D1', 'D4', 'D16']
        }
        
        return chart_relevance.get(life_area, ['D1', 'D9'])
    
    def _analyze_chart_strength(self, chart_name: str, planet_name: str, date: datetime) -> float:
        """Analyze planetary strength in a specific divisional chart."""
        try:
            if chart_name not in self._divisional_charts:
                return 0.5
            
            chart_data = self._divisional_charts[chart_name]
            
            # Get planetary position in this chart
            if 'planetary_positions' not in chart_data:
                return 0.5
            
            planetary_positions = chart_data['planetary_positions']
            if planet_name not in planetary_positions:
                return 0.5
            
            planet_data = planetary_positions[planet_name]
            
            # Use chart-specific analyzer if available
            if chart_name in self._chart_analyzers:
                return self._chart_analyzers[chart_name](planet_data, chart_data)
            else:
                return self._analyze_generic_chart(planet_data, chart_data)
                
        except Exception as e:
            self.logger.error(f"Error analyzing {chart_name} strength for {planet_name}: {e}")
            return 0.5
    
    def _analyze_rasi_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D1 (Rasi/Birth Chart)."""
        try:
            # Base strength from dignity
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # House strength (angular houses are stronger)
            house_strength = self._get_house_strength(planet_data.get('house', 1))
            
            # Aspect strength
            aspect_strength = self._get_aspect_strength(planet_data, chart_data)
            
            # ENHANCEMENT: Add strength points from kundali data
            strength_points_factor = self._get_strength_points_factor(planet_data)
            
            # ENHANCEMENT: Add yoga participation bonus
            yoga_participation_bonus = self._get_yoga_participation_bonus(planet_data, chart_data)
            
            # Combine factors with enhanced weights
            total_strength = (
                dignity_strength * 0.30 +
                house_strength * 0.25 +
                aspect_strength * 0.20 +
                strength_points_factor * 0.15 +
                yoga_participation_bonus * 0.10
            )
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D1 analysis: {e}")
            return 0.5
    
    def _get_strength_points_factor(self, planet_data: Dict[str, Any]) -> float:
        """Get strength factor from available strength points."""
        try:
            strength_points = planet_data.get('strength_points', 5.0)
            # Normalize assuming max 20 points (as seen in kundali data)
            return min(1.0, strength_points / 20.0)
        except Exception:
            return 0.5
    
    def _get_yoga_participation_bonus(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Get bonus for participating in yogas."""
        try:
            yogas = chart_data.get('yogas', [])
            if not yogas:
                return 0.5
            
            # Count beneficial yoga participations
            yoga_bonus = 0.5
            
            for yoga in yogas:
                if isinstance(yoga, str):
                    # Check for exaltation yogas
                    if 'exalted' in yoga.lower():
                        yoga_bonus += 0.2
                    # Check for conjunction yogas (can be beneficial or challenging)
                    elif 'conjunction' in yoga.lower():
                        yoga_bonus += 0.1
            
            return min(1.0, yoga_bonus)
            
        except Exception:
            return 0.5
    
    def _analyze_hora_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D2 (Hora Chart) - Wealth indicators."""
        try:
            # Hora chart focuses on wealth and material prosperity
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # In Hora, placement in benefic signs is more important
            rasi = planet_data.get('rasi', 0)
            benefic_bonus = 0.2 if rasi in [1, 3, 5, 6, 9, 11] else 0.0  # Benefic signs
            
            # House placement for wealth
            house = planet_data.get('house', 1)
            wealth_house_bonus = 0.3 if house in [1, 2, 5, 9, 11] else 0.0
            
            total_strength = dignity_strength + benefic_bonus + wealth_house_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D2 analysis: {e}")
            return 0.5
    
    def _analyze_drekkana_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D3 (Drekkana Chart) - Siblings and courage."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # Drekkana focuses on courage and siblings
            house = planet_data.get('house', 1)
            courage_house_bonus = 0.2 if house in [1, 3, 6, 10, 11] else 0.0
            
            # Mars and Sun are particularly important in D3
            planet_name = self._get_planet_name_from_data(planet_data)
            mars_sun_bonus = 0.1 if planet_name in ['mars', 'sun'] else 0.0
            
            total_strength = dignity_strength + courage_house_bonus + mars_sun_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D3 analysis: {e}")
            return 0.5
    
    def _analyze_chaturthamsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D4 (Chaturthamsa Chart) - Fortune and property."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D4 focuses on fortune and property
            house = planet_data.get('house', 1)
            fortune_house_bonus = 0.2 if house in [1, 4, 5, 9, 10] else 0.0
            
            # Jupiter and Venus are important for fortune
            planet_name = self._get_planet_name_from_data(planet_data)
            benefic_bonus = 0.1 if planet_name in ['jupiter', 'venus'] else 0.0
            
            total_strength = dignity_strength + fortune_house_bonus + benefic_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D4 analysis: {e}")
            return 0.5
    
    def _analyze_panchamamsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D5 (Panchamamsa Chart) - Fame and intelligence."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D5 focuses on fame and intelligence
            house = planet_data.get('house', 1)
            fame_house_bonus = 0.2 if house in [1, 5, 9, 10, 11] else 0.0
            
            # Sun, Jupiter, and Mercury are important for fame and intelligence
            planet_name = self._get_planet_name_from_data(planet_data)
            intelligence_bonus = 0.1 if planet_name in ['sun', 'jupiter', 'mercury'] else 0.0
            
            total_strength = dignity_strength + fame_house_bonus + intelligence_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D5 analysis: {e}")
            return 0.5
    
    def _analyze_shashthamsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D6 (Shashthamsa Chart) - Health and enemies."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D6 focuses on health and overcoming obstacles
            house = planet_data.get('house', 1)
            health_house_bonus = 0.2 if house in [1, 6, 8, 10] else 0.0
            
            # Mars and Saturn are important for overcoming enemies
            planet_name = self._get_planet_name_from_data(planet_data)
            warrior_bonus = 0.1 if planet_name in ['mars', 'saturn'] else 0.0
            
            total_strength = dignity_strength + health_house_bonus + warrior_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D6 analysis: {e}")
            return 0.5
    
    def _analyze_saptamsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D7 (Saptamsa Chart) - Children and creativity."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D7 focuses on children and progeny
            house = planet_data.get('house', 1)
            children_house_bonus = 0.2 if house in [1, 5, 7, 9] else 0.0
            
            # Jupiter and Venus are important for children
            planet_name = self._get_planet_name_from_data(planet_data)
            progeny_bonus = 0.1 if planet_name in ['jupiter', 'venus'] else 0.0
            
            total_strength = dignity_strength + children_house_bonus + progeny_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D7 analysis: {e}")
            return 0.5
    
    def _analyze_navamsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D9 (Navamsa Chart) - Dharma and spouse."""
        try:
            # Navamsa is the most important divisional chart
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # Enhanced weight for Navamsa dignity
            navamsa_dignity_weight = 1.2
            
            # House strength in Navamsa
            house = planet_data.get('house', 1)
            dharma_house_bonus = 0.3 if house in [1, 5, 9] else 0.1
            
            # Aspect strength is crucial in Navamsa
            aspect_strength = self._get_aspect_strength(planet_data, chart_data) * 0.5
            
            total_strength = (
                dignity_strength * navamsa_dignity_weight +
                dharma_house_bonus +
                aspect_strength
            ) / 2.0  # Normalize
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D9 analysis: {e}")
            return 0.5
    
    def _analyze_dasamsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D10 (Dasamsa Chart) - Career and profession."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D10 focuses on career and professional success
            house = planet_data.get('house', 1)
            career_house_bonus = 0.3 if house in [1, 10, 11] else 0.1
            
            # Sun, Mars, and Saturn are important for career
            planet_name = self._get_planet_name_from_data(planet_data)
            career_planet_bonus = 0.1 if planet_name in ['sun', 'mars', 'saturn', 'mercury'] else 0.0
            
            total_strength = dignity_strength + career_house_bonus + career_planet_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D10 analysis: {e}")
            return 0.5
    
    def _analyze_rudramsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D11 (Rudramsa Chart) - Gains and income."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D11 focuses on gains and fulfillment of desires
            house = planet_data.get('house', 1)
            gains_house_bonus = 0.2 if house in [1, 2, 11] else 0.0
            
            total_strength = dignity_strength + gains_house_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D11 analysis: {e}")
            return 0.5
    
    def _analyze_dwadasamsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D12 (Dwadasamsa Chart) - Parents and ancestry."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D12 focuses on parents and lineage
            house = planet_data.get('house', 1)
            parent_house_bonus = 0.2 if house in [1, 4, 9, 10] else 0.0
            
            total_strength = dignity_strength + parent_house_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D12 analysis: {e}")
            return 0.5
    
    def _analyze_shodasamsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D16 (Shodasamsa Chart) - Vehicles and happiness."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D16 focuses on vehicles, comforts, and happiness
            house = planet_data.get('house', 1)
            comfort_house_bonus = 0.2 if house in [1, 4, 11, 12] else 0.0
            
            # Venus is particularly important for comforts
            planet_name = self._get_planet_name_from_data(planet_data)
            venus_bonus = 0.1 if planet_name == 'venus' else 0.0
            
            total_strength = dignity_strength + comfort_house_bonus + venus_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D16 analysis: {e}")
            return 0.5
    
    def _analyze_vimsamsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D20 (Vimsamsa Chart) - Spirituality and worship."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D20 focuses on spiritual development
            house = planet_data.get('house', 1)
            spiritual_house_bonus = 0.2 if house in [1, 5, 9, 12] else 0.0
            
            # Jupiter is most important for spirituality
            planet_name = self._get_planet_name_from_data(planet_data)
            jupiter_bonus = 0.15 if planet_name == 'jupiter' else 0.0
            
            total_strength = dignity_strength + spiritual_house_bonus + jupiter_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D20 analysis: {e}")
            return 0.5
    
    def _analyze_chaturvimsamsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D24 (Chaturvimsamsa Chart) - Education and learning."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D24 focuses on education and knowledge
            house = planet_data.get('house', 1)
            education_house_bonus = 0.2 if house in [1, 4, 5, 9] else 0.0
            
            # Mercury and Jupiter are important for education
            planet_name = self._get_planet_name_from_data(planet_data)
            knowledge_bonus = 0.1 if planet_name in ['mercury', 'jupiter'] else 0.0
            
            total_strength = dignity_strength + education_house_bonus + knowledge_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D24 analysis: {e}")
            return 0.5
    
    def _analyze_nakshatramsa_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Analyze planetary strength in D27 (Nakshatramsa Chart) - Strength and weakness."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            
            # D27 focuses on inherent strengths and weaknesses
            house = planet_data.get('house', 1)
            strength_house_bonus = 0.2 if house in [1, 3, 6, 10] else 0.0
            
            total_strength = dignity_strength + strength_house_bonus
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error in D27 analysis: {e}")
            return 0.5
    
    def _analyze_generic_chart(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Generic analysis for charts without specific analyzers."""
        try:
            dignity_strength = self._get_dignity_strength(planet_data.get('dignity', 'Neutral'))
            house_strength = self._get_house_strength(planet_data.get('house', 1))
            
            return (dignity_strength + house_strength) / 2.0
            
        except Exception as e:
            self.logger.error(f"Error in generic chart analysis: {e}")
            return 0.5
    
    def _get_dignity_strength(self, dignity: str) -> float:
        """Convert dignity to numerical strength."""
        dignity_values = {
            'Exalted': 1.0,
            'Own Sign': 0.9,
            'Friendly': 0.7,
            'Neutral': 0.5,
            'Enemy': 0.3,
            'Debilitated': 0.1
        }
        return dignity_values.get(dignity, 0.5)
    
    def _get_house_strength(self, house: int) -> float:
        """Calculate house-based strength."""
        # Angular houses (1, 4, 7, 10) are strongest
        # Succedent houses (2, 5, 8, 11) are moderate
        # Cadent houses (3, 6, 9, 12) are weakest
        
        if house in [1, 4, 7, 10]:
            return 1.0  # Angular - strongest
        elif house in [2, 5, 8, 11]:
            return 0.7  # Succedent - moderate
        else:
            return 0.5  # Cadent - weakest
    
    def _get_aspect_strength(self, planet_data: Dict[str, Any], chart_data: Dict[str, Any]) -> float:
        """Calculate aspect-based strength."""
        try:
            # This is a simplified aspect strength calculation
            # In a full implementation, you would analyze all aspects
            
            aspects = chart_data.get('aspects', {})
            planet_aspects = []
            
            # Find aspects for this planet (simplified approach)
            for planet, aspect_list in aspects.items():
                if isinstance(aspect_list, list) and len(aspect_list) > 0:
                    planet_aspects.extend(aspect_list)
            
            # More aspects generally indicate more influence
            aspect_count = len(planet_aspects)
            
            if aspect_count == 0:
                return 0.5  # Neutral
            elif aspect_count <= 2:
                return 0.6  # Few aspects
            elif aspect_count <= 4:
                return 0.8  # Moderate aspects
            else:
                return 1.0  # Many aspects
                
        except Exception:
            return 0.5
    
    def _get_planet_name_from_data(self, planet_data: Dict[str, Any]) -> str:
        """Extract planet name from planet data (simplified approach)."""
        # This is a placeholder - in practice, you'd need to track the planet name
        # through the analysis chain or modify the data structure
        return 'unknown'
    
    def get_comprehensive_divisional_analysis(self, date: datetime) -> Dict[str, Any]:
        """
        Get comprehensive divisional chart analysis for all planets.
        
        Args:
            date: Date for analysis
            
        Returns:
            Dictionary with detailed divisional analysis
        """
        try:
            analysis = {
                'date': date.isoformat(),
                'planetary_divisional_strengths': {},
                'chart_specific_analysis': {},
                'life_area_strengths': {}
            }
            
            # Analyze each planet across all charts
            planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
            
            for planet in planets:
                analysis['planetary_divisional_strengths'][planet] = {
                    'general': self.calculate_divisional_strength(planet, date, 'general'),
                    'wealth': self.calculate_divisional_strength(planet, date, 'wealth'),
                    'career': self.calculate_divisional_strength(planet, date, 'career'),
                    'health': self.calculate_divisional_strength(planet, date, 'health'),
                    'relationships': self.calculate_divisional_strength(planet, date, 'relationships')
                }
            
            # Analyze each chart
            for chart_name in self._divisional_charts.keys():
                if chart_name in self._chart_analyzers:
                    chart_analysis = {}
                    for planet in planets:
                        if chart_name in self._divisional_charts:
                            chart_data = self._divisional_charts[chart_name]
                            if 'planetary_positions' in chart_data and planet in chart_data['planetary_positions']:
                                planet_data = chart_data['planetary_positions'][planet]
                                chart_analysis[planet] = self._analyze_chart_strength(chart_name, planet, date)
                    
                    analysis['chart_specific_analysis'][chart_name] = chart_analysis
            
            # Calculate life area strengths
            life_areas = ['general', 'wealth', 'career', 'health', 'relationships', 'spirituality']
            for area in life_areas:
                area_strength = 0.0
                planet_count = 0
                
                for planet in planets:
                    planet_strength = self.calculate_divisional_strength(planet, date, area)
                    area_strength += planet_strength
                    planet_count += 1
                
                if planet_count > 0:
                    analysis['life_area_strengths'][area] = area_strength / planet_count
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive divisional analysis: {e}")
            return {'error': str(e)}