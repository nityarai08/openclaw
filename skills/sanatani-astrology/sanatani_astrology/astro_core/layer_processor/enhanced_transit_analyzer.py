"""
Enhanced Transit Analysis with Traditional Vedic Rules

This module provides comprehensive transit analysis including Gochara rules,
Sade Sati analysis, Jupiter transits, eclipse effects, and traditional
Vedic transit principles for enhanced timing accuracy.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..core.data_models import KundaliData, PlanetaryPosition
from ..kundali_generator.comprehensive_ephemeris_engine import ComprehensiveEphemerisEngine


class EnhancedTransitAnalyzer:
    """
    Comprehensive transit analyzer with traditional Vedic rules.
    
    Analyzes planetary transits using classical Gochara principles,
    Sade Sati effects, Jupiter's 12-year cycle, eclipse impacts,
    and other traditional transit rules for enhanced timing accuracy.
    """
    
    def __init__(self, kundali_data: KundaliData):
        """
        Initialize enhanced transit analyzer.
        
        Args:
            kundali_data: Complete kundali data with planetary positions
        """
        self.kundali_data = kundali_data
        self.logger = logging.getLogger(self.__class__.__name__)
        self._ephemeris_engine = ComprehensiveEphemerisEngine()
        
        # Cache natal planetary positions
        self._natal_positions = kundali_data.planetary_positions if kundali_data.planetary_positions else {}
        
        # Cache birth details
        if kundali_data.birth_details:
            self._birth_latitude = kundali_data.birth_details.latitude
            self._birth_longitude = kundali_data.birth_details.longitude
            self._birth_timezone = kundali_data.birth_details.timezone_offset
        else:
            raise ValueError("Birth details required for transit analysis")
        
        # Traditional Gochara rules
        self._initialize_gochara_rules()
        
        # Eclipse calculation parameters
        self._eclipse_orb = 15.0  # degrees
        
        # Transit cycle information
        self._transit_cycles = {
            'sun': 30,      # days per sign
            'moon': 2.25,   # days per sign
            'mars': 45,     # days per sign (average)
            'mercury': 25,  # days per sign (average)
            'jupiter': 365, # days per sign (1 year)
            'venus': 25,    # days per sign (average)
            'saturn': 900,  # days per sign (2.5 years)
            'rahu': -548,   # days per sign (retrograde, 1.5 years)
            'ketu': -548    # days per sign (retrograde, 1.5 years)
        }
    
    def _initialize_gochara_rules(self):
        """Initialize traditional Gochara (transit) rules."""
        
        # Gochara favorability from Moon sign
        self._gochara_from_moon = {
            'sun': {
                1: 0.6, 2: 0.4, 3: 0.8, 4: 0.3, 5: 0.7, 6: 0.9,
                7: 0.5, 8: 0.2, 9: 0.8, 10: 0.7, 11: 0.9, 12: 0.4
            },
            'moon': {
                1: 0.8, 2: 0.6, 3: 0.9, 4: 0.5, 5: 0.7, 6: 0.9,
                7: 0.8, 8: 0.3, 9: 0.6, 10: 0.7, 11: 0.9, 12: 0.4
            },
            'mars': {
                1: 0.5, 2: 0.4, 3: 0.8, 4: 0.3, 5: 0.6, 6: 0.9,
                7: 0.5, 8: 0.2, 9: 0.7, 10: 0.6, 11: 0.8, 12: 0.3
            },
            'mercury': {
                1: 0.7, 2: 0.8, 3: 0.6, 4: 0.9, 5: 0.7, 6: 0.8,
                7: 0.5, 8: 0.4, 9: 0.6, 10: 0.8, 11: 0.9, 12: 0.5
            },
            'jupiter': {
                1: 0.6, 2: 0.8, 3: 0.5, 4: 0.9, 5: 0.8, 6: 0.4,
                7: 0.9, 8: 0.3, 9: 0.7, 10: 0.8, 11: 0.9, 12: 0.6
            },
            'venus': {
                1: 0.8, 2: 0.9, 3: 0.7, 4: 0.8, 5: 0.9, 6: 0.5,
                7: 0.6, 8: 0.4, 9: 0.8, 10: 0.7, 11: 0.9, 12: 0.9
            },
            'saturn': {
                1: 0.3, 2: 0.4, 3: 0.8, 4: 0.2, 5: 0.3, 6: 0.9,
                7: 0.4, 8: 0.2, 9: 0.5, 10: 0.6, 11: 0.8, 12: 0.5
            },
            'rahu': {
                1: 0.4, 2: 0.3, 3: 0.7, 4: 0.3, 5: 0.4, 6: 0.8,
                7: 0.4, 8: 0.2, 9: 0.3, 10: 0.6, 11: 0.8, 12: 0.5
            },
            'ketu': {
                1: 0.6, 2: 0.4, 3: 0.5, 4: 0.4, 5: 0.6, 6: 0.7,
                7: 0.4, 8: 0.7, 9: 0.8, 10: 0.4, 11: 0.3, 12: 0.8
            }
        }
        
        # Gochara favorability from Lagna
        self._gochara_from_lagna = {
            'sun': {
                1: 0.8, 2: 0.5, 3: 0.9, 4: 0.4, 5: 0.8, 6: 0.9,
                7: 0.6, 8: 0.3, 9: 0.9, 10: 0.8, 11: 0.9, 12: 0.5
            },
            'jupiter': {
                1: 0.8, 2: 0.9, 3: 0.6, 4: 0.9, 5: 0.8, 6: 0.5,
                7: 0.9, 8: 0.4, 9: 0.8, 10: 0.9, 11: 0.9, 12: 0.7
            },
            'saturn': {
                1: 0.4, 2: 0.5, 3: 0.8, 4: 0.3, 5: 0.4, 6: 0.9,
                7: 0.5, 8: 0.3, 9: 0.6, 10: 0.7, 11: 0.8, 12: 0.6
            }
        }
        
        # Special transit combinations
        self._special_transits = {
            'guru_chandal': {
                'planets': ['jupiter', 'rahu'],
                'condition': 'conjunction',
                'effect': 0.3,
                'description': 'Jupiter-Rahu conjunction (Guru Chandal)'
            },
            'shani_mangal': {
                'planets': ['saturn', 'mars'],
                'condition': 'conjunction',
                'effect': 0.2,
                'description': 'Saturn-Mars conjunction'
            },
            'surya_grahan': {
                'planets': ['sun', 'rahu'],
                'condition': 'eclipse',
                'effect': 0.2,
                'description': 'Solar eclipse effect'
            },
            'chandra_grahan': {
                'planets': ['moon', 'rahu'],
                'condition': 'eclipse',
                'effect': 0.2,
                'description': 'Lunar eclipse effect'
            }
        }
    
    def calculate_transit_favorability(self, date: datetime) -> float:
        """
        Calculate comprehensive transit favorability for a date.
        
        Args:
            date: Date for transit analysis
            
        Returns:
            Transit favorability score between 0.0 and 1.0
        """
        try:
            # Get current planetary positions
            current_positions = self._get_current_positions(date)
            if not current_positions:
                return 0.5
            
            # Calculate individual transit factors
            gochara_score = self._calculate_gochara_score(current_positions)
            sade_sati_score = self._calculate_sade_sati_score(current_positions)
            jupiter_transit_score = self._calculate_jupiter_transit_score(current_positions)
            eclipse_score = self._calculate_eclipse_effects(current_positions, date)
            special_transit_score = self._calculate_special_transits(current_positions)
            
            # Weight the factors
            weights = {
                'gochara': 0.35,
                'sade_sati': 0.20,
                'jupiter': 0.20,
                'eclipse': 0.15,
                'special': 0.10
            }
            
            total_score = (
                gochara_score * weights['gochara'] +
                sade_sati_score * weights['sade_sati'] +
                jupiter_transit_score * weights['jupiter'] +
                eclipse_score * weights['eclipse'] +
                special_transit_score * weights['special']
            )
            
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating transit favorability: {e}")
            return 0.5
    
    def _calculate_gochara_score(self, current_positions: Dict[str, PlanetaryPosition]) -> float:
        """Calculate Gochara (traditional transit) score."""
        try:
            if 'moon' not in self._natal_positions or 'lagna' not in self._natal_positions:
                return 0.5
            
            natal_moon_rasi = self._natal_positions['moon'].rasi
            natal_lagna_rasi = self._natal_positions['lagna'].rasi
            
            total_score = 0.0
            planet_count = 0
            
            # Calculate Gochara from Moon
            for planet, position in current_positions.items():
                if planet in self._gochara_from_moon:
                    # Calculate house from Moon
                    house_from_moon = ((position.rasi - natal_moon_rasi) % 12) + 1
                    
                    # Get Gochara score
                    moon_gochara = self._gochara_from_moon[planet].get(house_from_moon, 0.5)
                    
                    # Weight by planet importance
                    planet_weight = self._get_planet_weight(planet)
                    total_score += moon_gochara * planet_weight
                    planet_count += planet_weight
            
            # Calculate Gochara from Lagna for important planets
            important_planets = ['sun', 'jupiter', 'saturn']
            for planet in important_planets:
                if planet in current_positions and planet in self._gochara_from_lagna:
                    position = current_positions[planet]
                    house_from_lagna = ((position.rasi - natal_lagna_rasi) % 12) + 1
                    
                    lagna_gochara = self._gochara_from_lagna[planet].get(house_from_lagna, 0.5)
                    
                    # Add Lagna Gochara with reduced weight
                    planet_weight = self._get_planet_weight(planet) * 0.5
                    total_score += lagna_gochara * planet_weight
                    planet_count += planet_weight
            
            # Calculate average
            if planet_count > 0:
                gochara_score = total_score / planet_count
            else:
                gochara_score = 0.5
            
            return max(0.0, min(1.0, gochara_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating Gochara score: {e}")
            return 0.5
    
    def _calculate_sade_sati_score(self, current_positions: Dict[str, PlanetaryPosition]) -> float:
        """Calculate Sade Sati (Saturn's 7.5-year cycle) effects."""
        try:
            if 'saturn' not in current_positions or 'moon' not in self._natal_positions:
                return 1.0  # No Sade Sati effect
            
            saturn_rasi = current_positions['saturn'].rasi
            natal_moon_rasi = self._natal_positions['moon'].rasi
            
            # Sade Sati positions: 12th, 1st, and 2nd from Moon
            sade_sati_positions = [
                (natal_moon_rasi - 1) % 12,  # 12th from Moon
                natal_moon_rasi,             # Same as Moon
                (natal_moon_rasi + 1) % 12   # 2nd from Moon
            ]
            
            if saturn_rasi in sade_sati_positions:
                # Determine Sade Sati phase
                if saturn_rasi == (natal_moon_rasi - 1) % 12:
                    phase = "Rising"
                    effect = 0.4  # Challenging but building
                elif saturn_rasi == natal_moon_rasi:
                    phase = "Peak"
                    effect = 0.3  # Most challenging
                else:  # 2nd from Moon
                    phase = "Setting"
                    effect = 0.5  # Challenging but improving
                
                # Apply retrograde modifier
                if current_positions['saturn'].retrograde:
                    effect += 0.1  # Slightly better when retrograde
                
                return max(0.2, min(0.8, effect))
            
            return 1.0  # No Sade Sati
            
        except Exception as e:
            self.logger.error(f"Error calculating Sade Sati score: {e}")
            return 1.0
    
    def _calculate_jupiter_transit_score(self, current_positions: Dict[str, PlanetaryPosition]) -> float:
        """Calculate Jupiter transit effects (12-year cycle)."""
        try:
            if 'jupiter' not in current_positions or 'moon' not in self._natal_positions:
                return 0.5
            
            jupiter_rasi = current_positions['jupiter'].rasi
            natal_moon_rasi = self._natal_positions['moon'].rasi
            
            # Calculate house from Moon
            house_from_moon = ((jupiter_rasi - natal_moon_rasi) % 12) + 1
            
            # Jupiter transit favorability from Moon
            jupiter_effects = {
                1: 0.6,   # Self - moderate, can bring ego issues
                2: 0.8,   # Wealth - very favorable
                3: 0.5,   # Siblings - neutral
                4: 0.9,   # Home - excellent
                5: 0.9,   # Children - excellent
                6: 0.4,   # Enemies - challenging
                7: 0.8,   # Partnership - good
                8: 0.3,   # Obstacles - difficult
                9: 0.9,   # Fortune - excellent
                10: 0.8,  # Career - good
                11: 0.9,  # Gains - excellent
                12: 0.4   # Loss - mixed
            }
            
            base_score = jupiter_effects.get(house_from_moon, 0.5)
            
            # Apply retrograde modifier
            if current_positions['jupiter'].retrograde:
                base_score *= 0.8  # Reduce for retrograde
            
            # Check for Jupiter's own signs (Sagittarius, Pisces)
            if jupiter_rasi in [8, 11]:  # Sagittarius, Pisces
                base_score *= 1.2  # Enhance in own signs
            
            # Check for Jupiter's exaltation (Cancer)
            if jupiter_rasi == 3:  # Cancer
                base_score *= 1.3  # Maximum enhancement
            
            # Check for Jupiter's debilitation (Capricorn)
            if jupiter_rasi == 9:  # Capricorn
                base_score *= 0.7  # Reduce in debilitation
            
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating Jupiter transit score: {e}")
            return 0.5
    
    def _calculate_eclipse_effects(self, current_positions: Dict[str, PlanetaryPosition], date: datetime) -> float:
        """Calculate eclipse effects on favorability."""
        try:
            eclipse_score = 1.0  # No eclipse effect by default
            
            # Check for solar eclipse (Sun-Rahu/Ketu conjunction)
            if 'sun' in current_positions:
                sun_pos = current_positions['sun']
                
                for node in ['rahu', 'ketu']:
                    if node in current_positions:
                        node_pos = current_positions[node]
                        angular_diff = abs(sun_pos.longitude - node_pos.longitude)
                        
                        if angular_diff <= self._eclipse_orb:
                            # Solar eclipse effect
                            eclipse_intensity = 1.0 - (angular_diff / self._eclipse_orb)
                            eclipse_score *= (0.3 + 0.4 * (1.0 - eclipse_intensity))
            
            # Check for lunar eclipse (Moon-Rahu/Ketu opposition)
            if 'moon' in current_positions:
                moon_pos = current_positions['moon']
                
                for node in ['rahu', 'ketu']:
                    if node in current_positions:
                        node_pos = current_positions[node]
                        angular_diff = abs(moon_pos.longitude - node_pos.longitude)
                        
                        # Check for opposition (180 degrees)
                        if angular_diff > 180:
                            angular_diff = 360 - angular_diff
                        
                        opposition_diff = abs(angular_diff - 180)
                        
                        if opposition_diff <= self._eclipse_orb:
                            # Lunar eclipse effect
                            eclipse_intensity = 1.0 - (opposition_diff / self._eclipse_orb)
                            eclipse_score *= (0.3 + 0.4 * (1.0 - eclipse_intensity))
            
            return max(0.2, min(1.0, eclipse_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating eclipse effects: {e}")
            return 1.0
    
    def _calculate_special_transits(self, current_positions: Dict[str, PlanetaryPosition]) -> float:
        """Calculate effects of special transit combinations."""
        try:
            special_score = 1.0
            
            # Check each special transit combination
            for transit_name, transit_info in self._special_transits.items():
                planets = transit_info['planets']
                condition = transit_info['condition']
                effect = transit_info['effect']
                
                if all(planet in current_positions for planet in planets):
                    if condition == 'conjunction':
                        pos1 = current_positions[planets[0]]
                        pos2 = current_positions[planets[1]]
                        
                        angular_diff = abs(pos1.longitude - pos2.longitude)
                        if angular_diff <= 10:  # 10-degree orb for conjunction
                            special_score *= effect
                    
                    elif condition == 'eclipse':
                        # Already handled in eclipse effects
                        pass
            
            return max(0.2, min(1.0, special_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating special transits: {e}")
            return 1.0
    
    def _get_current_positions(self, date: datetime) -> Dict[str, PlanetaryPosition]:
        """Get current planetary positions for a date."""
        try:
            julian_day = self._ephemeris_engine.julian_day_from_datetime(
                date, self._birth_timezone
            )
            
            return self._ephemeris_engine.calculate_planetary_positions(
                julian_day, self._birth_latitude, self._birth_longitude
            )
            
        except Exception as e:
            self.logger.error(f"Error getting current positions: {e}")
            return {}
    
    def _get_planet_weight(self, planet: str) -> float:
        """Get weight for a planet in calculations."""
        weights = {
            'sun': 1.0,
            'moon': 1.0,
            'mars': 0.8,
            'mercury': 0.7,
            'jupiter': 1.2,
            'venus': 0.8,
            'saturn': 1.1,
            'rahu': 0.9,
            'ketu': 0.6
        }
        return weights.get(planet, 0.5)
    
    def get_transit_analysis(self, date: datetime) -> Dict[str, Any]:
        """
        Get comprehensive transit analysis for a date.
        
        Args:
            date: Date for analysis
            
        Returns:
            Dictionary with detailed transit analysis
        """
        try:
            current_positions = self._get_current_positions(date)
            
            analysis = {
                'date': date.isoformat(),
                'overall_favorability': self.calculate_transit_favorability(date),
                'gochara_analysis': self._get_gochara_analysis(current_positions),
                'sade_sati_status': self._get_sade_sati_status(current_positions),
                'jupiter_transit': self._get_jupiter_transit_analysis(current_positions),
                'eclipse_effects': self._get_eclipse_analysis(current_positions, date),
                'special_transits': self._get_special_transit_analysis(current_positions),
                'recommendations': self._generate_transit_recommendations(current_positions)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error generating transit analysis: {e}")
            return {'error': str(e)}
    
    def _get_gochara_analysis(self, current_positions: Dict[str, PlanetaryPosition]) -> Dict[str, Any]:
        """Get detailed Gochara analysis."""
        try:
            if 'moon' not in self._natal_positions:
                return {}
            
            natal_moon_rasi = self._natal_positions['moon'].rasi
            gochara_details = {}
            
            for planet, position in current_positions.items():
                if planet in self._gochara_from_moon:
                    house_from_moon = ((position.rasi - natal_moon_rasi) % 12) + 1
                    favorability = self._gochara_from_moon[planet].get(house_from_moon, 0.5)
                    
                    gochara_details[planet] = {
                        'current_rasi': position.rasi,
                        'house_from_moon': house_from_moon,
                        'favorability': favorability,
                        'retrograde': position.retrograde
                    }
            
            return gochara_details
            
        except Exception as e:
            self.logger.error(f"Error getting Gochara analysis: {e}")
            return {}
    
    def _get_sade_sati_status(self, current_positions: Dict[str, PlanetaryPosition]) -> Dict[str, Any]:
        """Get Sade Sati status analysis."""
        try:
            if 'saturn' not in current_positions or 'moon' not in self._natal_positions:
                return {'active': False}
            
            saturn_rasi = current_positions['saturn'].rasi
            natal_moon_rasi = self._natal_positions['moon'].rasi
            
            sade_sati_positions = [
                (natal_moon_rasi - 1) % 12,
                natal_moon_rasi,
                (natal_moon_rasi + 1) % 12
            ]
            
            if saturn_rasi in sade_sati_positions:
                if saturn_rasi == (natal_moon_rasi - 1) % 12:
                    phase = "Rising (12th from Moon)"
                elif saturn_rasi == natal_moon_rasi:
                    phase = "Peak (Same as Moon)"
                else:
                    phase = "Setting (2nd from Moon)"
                
                return {
                    'active': True,
                    'phase': phase,
                    'saturn_rasi': saturn_rasi,
                    'saturn_retrograde': current_positions['saturn'].retrograde,
                    'effect_level': 'High' if saturn_rasi == natal_moon_rasi else 'Moderate'
                }
            
            return {'active': False}
            
        except Exception as e:
            self.logger.error(f"Error getting Sade Sati status: {e}")
            return {'active': False}
    
    def _get_jupiter_transit_analysis(self, current_positions: Dict[str, PlanetaryPosition]) -> Dict[str, Any]:
        """Get Jupiter transit analysis."""
        try:
            if 'jupiter' not in current_positions or 'moon' not in self._natal_positions:
                return {}
            
            jupiter_pos = current_positions['jupiter']
            natal_moon_rasi = self._natal_positions['moon'].rasi
            house_from_moon = ((jupiter_pos.rasi - natal_moon_rasi) % 12) + 1
            
            return {
                'current_rasi': jupiter_pos.rasi,
                'house_from_moon': house_from_moon,
                'retrograde': jupiter_pos.retrograde,
                'favorability': self._calculate_jupiter_transit_score(current_positions),
                'cycle_position': f"Year {((jupiter_pos.rasi - natal_moon_rasi) % 12) + 1} of 12-year cycle"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Jupiter transit analysis: {e}")
            return {}
    
    def _get_eclipse_analysis(self, current_positions: Dict[str, PlanetaryPosition], date: datetime) -> Dict[str, Any]:
        """Get eclipse effects analysis."""
        try:
            eclipse_info = {'solar_eclipse': False, 'lunar_eclipse': False, 'effects': []}
            
            # Check solar eclipse
            if 'sun' in current_positions:
                sun_pos = current_positions['sun']
                for node in ['rahu', 'ketu']:
                    if node in current_positions:
                        node_pos = current_positions[node]
                        angular_diff = abs(sun_pos.longitude - node_pos.longitude)
                        
                        if angular_diff <= self._eclipse_orb:
                            eclipse_info['solar_eclipse'] = True
                            eclipse_info['effects'].append(f'Solar eclipse effect with {node.title()}')
            
            # Check lunar eclipse
            if 'moon' in current_positions:
                moon_pos = current_positions['moon']
                for node in ['rahu', 'ketu']:
                    if node in current_positions:
                        node_pos = current_positions[node]
                        angular_diff = abs(moon_pos.longitude - node_pos.longitude)
                        if angular_diff > 180:
                            angular_diff = 360 - angular_diff
                        
                        opposition_diff = abs(angular_diff - 180)
                        if opposition_diff <= self._eclipse_orb:
                            eclipse_info['lunar_eclipse'] = True
                            eclipse_info['effects'].append(f'Lunar eclipse effect with {node.title()}')
            
            return eclipse_info
            
        except Exception as e:
            self.logger.error(f"Error getting eclipse analysis: {e}")
            return {}
    
    def _get_special_transit_analysis(self, current_positions: Dict[str, PlanetaryPosition]) -> List[Dict[str, Any]]:
        """Get special transit combinations analysis."""
        try:
            special_transits = []
            
            for transit_name, transit_info in self._special_transits.items():
                planets = transit_info['planets']
                condition = transit_info['condition']
                
                if all(planet in current_positions for planet in planets):
                    if condition == 'conjunction':
                        pos1 = current_positions[planets[0]]
                        pos2 = current_positions[planets[1]]
                        
                        angular_diff = abs(pos1.longitude - pos2.longitude)
                        if angular_diff <= 10:
                            special_transits.append({
                                'name': transit_name,
                                'description': transit_info['description'],
                                'planets': planets,
                                'effect': transit_info['effect'],
                                'angular_difference': angular_diff
                            })
            
            return special_transits
            
        except Exception as e:
            self.logger.error(f"Error getting special transit analysis: {e}")
            return []
    
    def _generate_transit_recommendations(self, current_positions: Dict[str, PlanetaryPosition]) -> List[str]:
        """Generate recommendations based on current transits."""
        recommendations = []
        
        try:
            # Sade Sati recommendations
            sade_sati_status = self._get_sade_sati_status(current_positions)
            if sade_sati_status.get('active', False):
                phase = sade_sati_status.get('phase', '')
                if 'Peak' in phase:
                    recommendations.append("Sade Sati peak phase - exercise patience and avoid major decisions")
                else:
                    recommendations.append("Sade Sati active - focus on discipline and steady progress")
            
            # Jupiter transit recommendations
            jupiter_analysis = self._get_jupiter_transit_analysis(current_positions)
            if jupiter_analysis.get('favorability', 0.5) > 0.7:
                recommendations.append("Jupiter transit favorable - good time for growth and expansion")
            elif jupiter_analysis.get('favorability', 0.5) < 0.4:
                recommendations.append("Jupiter transit challenging - avoid overexpansion and speculation")
            
            # Eclipse recommendations
            eclipse_analysis = self._get_eclipse_analysis(current_positions, datetime.now())
            if eclipse_analysis.get('solar_eclipse') or eclipse_analysis.get('lunar_eclipse'):
                recommendations.append("Eclipse effects active - avoid important new beginnings")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating transit recommendations: {e}")
            return ["General period - maintain balance and positive attitude"]