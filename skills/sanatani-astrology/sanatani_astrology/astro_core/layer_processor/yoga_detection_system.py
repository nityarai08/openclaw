"""
Advanced Yoga Detection System for Enhanced Astrological Analysis

This module provides comprehensive detection and analysis of Vedic astrological yogas
including Raj Yogas, Dhana Yogas, Panch Mahapurusha Yogas, and other significant
planetary combinations for enhanced timing and favorability calculations.
"""

import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
import logging

from ..core.data_models import KundaliData, PlanetaryPosition
from ..kundali_generator.comprehensive_ephemeris_engine import ComprehensiveEphemerisEngine


class YogaDetectionSystem:
    """
    Comprehensive system for detecting and analyzing Vedic astrological yogas.
    
    Identifies various types of yogas including Raj Yogas, Dhana Yogas,
    Panch Mahapurusha Yogas, and other significant combinations with
    strength assessment and timing analysis.
    """
    
    def __init__(self, kundali_data: KundaliData):
        """
        Initialize yoga detection system.
        
        Args:
            kundali_data: Complete kundali data with planetary positions
        """
        self.kundali_data = kundali_data
        self.logger = logging.getLogger(self.__class__.__name__)
        self._ephemeris_engine = ComprehensiveEphemerisEngine()
        
        # Cache natal planetary positions and houses
        self._natal_positions = kundali_data.planetary_positions if kundali_data.planetary_positions else {}
        self._natal_houses = self._calculate_natal_houses()
        
        # Yoga definitions and rules
        self._initialize_yoga_rules()
        
        # Calculate natal yogas
        self._natal_yogas = self._detect_natal_yogas()
    
    def _initialize_yoga_rules(self):
        """Initialize yoga detection rules and definitions."""
        
        # Raj Yoga combinations (combinations of trine and angular lords)
        self._raj_yoga_houses = {
            'angular': [1, 4, 7, 10],  # Kendra houses
            'trine': [1, 5, 9],        # Trikona houses
            'combined': [1, 4, 5, 7, 9, 10]  # Raj Yoga houses
        }
        
        # Dhana Yoga combinations (wealth-producing combinations)
        self._dhana_yoga_houses = {
            'wealth': [2, 11],         # Direct wealth houses
            'supporting': [1, 5, 9],   # Supporting houses
            'combined': [1, 2, 5, 9, 11]  # Dhana Yoga houses
        }
        
        # Panch Mahapurusha Yoga definitions
        self._panch_mahapurusha_yogas = {
            'ruchaka': {
                'planet': 'mars',
                'positions': [0, 7, 9],  # Aries, Scorpio, Capricorn (own/exaltation)
                'houses': [1, 4, 7, 10], # Angular houses
                'strength': 0.9
            },
            'bhadra': {
                'planet': 'mercury',
                'positions': [2, 5],     # Gemini, Virgo (own/exaltation)
                'houses': [1, 4, 7, 10],
                'strength': 0.8
            },
            'hamsa': {
                'planet': 'jupiter',
                'positions': [3, 8, 11], # Cancer, Sagittarius, Pisces
                'houses': [1, 4, 7, 10],
                'strength': 1.0
            },
            'malavya': {
                'planet': 'venus',
                'positions': [1, 6, 11], # Taurus, Libra, Pisces
                'houses': [1, 4, 7, 10],
                'strength': 0.8
            },
            'sasa': {
                'planet': 'saturn',
                'positions': [6, 9, 10], # Libra, Capricorn, Aquarius
                'houses': [1, 4, 7, 10],
                'strength': 0.7
            }
        }
        
        # Other significant yogas
        self._special_yogas = {
            'gaja_kesari': {
                'description': 'Moon and Jupiter in mutual kendras',
                'planets': ['moon', 'jupiter'],
                'condition': 'mutual_kendra',
                'strength': 0.9
            },
            'chandra_mangal': {
                'description': 'Moon and Mars conjunction/aspect',
                'planets': ['moon', 'mars'],
                'condition': 'conjunction_or_aspect',
                'strength': 0.6
            },
            'budh_aditya': {
                'description': 'Sun and Mercury conjunction',
                'planets': ['sun', 'mercury'],
                'condition': 'conjunction',
                'strength': 0.7
            },
            'neecha_bhanga': {
                'description': 'Cancellation of debilitation',
                'condition': 'debilitation_cancellation',
                'strength': 0.8
            }
        }
        
        # Malefic yogas (to be avoided)
        self._malefic_yogas = {
            'kemadruma': {
                'description': 'Moon isolated without benefic support',
                'condition': 'moon_isolation',
                'strength': 0.2
            },
            'shakata': {
                'description': 'Moon and Jupiter in 6/8 relationship',
                'planets': ['moon', 'jupiter'],
                'condition': '6_8_relationship',
                'strength': 0.3
            },
            'grahan': {
                'description': 'Sun/Moon with Rahu/Ketu (eclipse yoga)',
                'condition': 'eclipse_combination',
                'strength': 0.2
            }
        }
    
    def detect_active_yogas(self, date: datetime) -> Dict[str, Any]:
        """
        Detect active yogas for a specific date.
        
        Args:
            date: Date for yoga detection
            
        Returns:
            Dictionary with active yogas and their strengths
        """
        try:
            # Get current planetary positions
            current_positions = self._get_current_positions(date)
            if not current_positions:
                return {}
            
            active_yogas = {
                'raj_yogas': self._detect_raj_yogas(current_positions),
                'dhana_yogas': self._detect_dhana_yogas(current_positions),
                'panch_mahapurusha': self._detect_panch_mahapurusha_yogas(current_positions),
                'special_yogas': self._detect_special_yogas(current_positions),
                'malefic_yogas': self._detect_malefic_yogas(current_positions),
                'overall_yoga_strength': 0.0
            }
            
            # Calculate overall yoga strength
            active_yogas['overall_yoga_strength'] = self._calculate_overall_yoga_strength(active_yogas)
            
            return active_yogas
            
        except Exception as e:
            self.logger.error(f"Error detecting active yogas for {date}: {e}")
            return {}
    
    def calculate_yoga_favorability(self, date: datetime) -> float:
        """
        Calculate overall yoga-based favorability for a date.
        
        Args:
            date: Date for calculation
            
        Returns:
            Favorability score between 0.0 and 1.0
        """
        try:
            active_yogas = self.detect_active_yogas(date)
            
            if not active_yogas:
                return 0.5  # Neutral fallback
            
            # Get overall yoga strength
            yoga_strength = active_yogas.get('overall_yoga_strength', 0.5)
            
            # Apply natal yoga influence
            natal_influence = self._calculate_natal_yoga_influence()
            
            # Combine current and natal influences
            combined_favorability = (yoga_strength * 0.7) + (natal_influence * 0.3)
            
            return max(0.0, min(1.0, combined_favorability))
            
        except Exception as e:
            self.logger.error(f"Error calculating yoga favorability: {e}")
            return 0.5
    
    def _detect_natal_yogas(self) -> Dict[str, Any]:
        """Detect yogas in the natal chart."""
        try:
            natal_yogas = {
                'raj_yogas': self._detect_raj_yogas(self._natal_positions),
                'dhana_yogas': self._detect_dhana_yogas(self._natal_positions),
                'panch_mahapurusha': self._detect_panch_mahapurusha_yogas(self._natal_positions),
                'special_yogas': self._detect_special_yogas(self._natal_positions),
                'malefic_yogas': self._detect_malefic_yogas(self._natal_positions)
            }
            
            return natal_yogas
            
        except Exception as e:
            self.logger.error(f"Error detecting natal yogas: {e}")
            return {}
    
    def _detect_raj_yogas(self, positions: Dict[str, PlanetaryPosition]) -> List[Dict[str, Any]]:
        """Detect Raj Yogas (royal combinations)."""
        raj_yogas = []
        
        try:
            # Get house lords
            house_lords = self._get_house_lords(positions)
            
            # Check for angular-trine lord combinations
            angular_houses = self._raj_yoga_houses['angular']
            trine_houses = self._raj_yoga_houses['trine']
            
            for angular_house in angular_houses:
                angular_lord = house_lords.get(angular_house)
                if not angular_lord:
                    continue
                
                for trine_house in trine_houses:
                    if trine_house == angular_house:  # Same house (especially 1st)
                        continue
                    
                    trine_lord = house_lords.get(trine_house)
                    if not trine_lord:
                        continue
                    
                    # Check if lords are in conjunction or mutual aspect
                    if self._check_planetary_relationship(positions, angular_lord, trine_lord):
                        raj_yogas.append({
                            'type': 'Angular-Trine Raj Yoga',
                            'houses': [angular_house, trine_house],
                            'lords': [angular_lord, trine_lord],
                            'strength': self._calculate_raj_yoga_strength(positions, angular_lord, trine_lord)
                        })
            
            return raj_yogas
            
        except Exception as e:
            self.logger.error(f"Error detecting Raj Yogas: {e}")
            return []
    
    def _detect_dhana_yogas(self, positions: Dict[str, PlanetaryPosition]) -> List[Dict[str, Any]]:
        """Detect Dhana Yogas (wealth combinations)."""
        dhana_yogas = []
        
        try:
            house_lords = self._get_house_lords(positions)
            
            # Check for 2nd and 11th lord combinations
            second_lord = house_lords.get(2)
            eleventh_lord = house_lords.get(11)
            
            if second_lord and eleventh_lord:
                if self._check_planetary_relationship(positions, second_lord, eleventh_lord):
                    dhana_yogas.append({
                        'type': '2nd-11th Lord Dhana Yoga',
                        'houses': [2, 11],
                        'lords': [second_lord, eleventh_lord],
                        'strength': self._calculate_dhana_yoga_strength(positions, second_lord, eleventh_lord)
                    })
            
            # Check for other wealth combinations
            wealth_houses = [1, 2, 5, 9, 11]
            for i, house1 in enumerate(wealth_houses):
                lord1 = house_lords.get(house1)
                if not lord1:
                    continue
                
                for house2 in wealth_houses[i+1:]:
                    lord2 = house_lords.get(house2)
                    if not lord2:
                        continue
                    
                    if self._check_planetary_relationship(positions, lord1, lord2):
                        dhana_yogas.append({
                            'type': f'{house1}-{house2} Wealth Combination',
                            'houses': [house1, house2],
                            'lords': [lord1, lord2],
                            'strength': self._calculate_dhana_yoga_strength(positions, lord1, lord2)
                        })
            
            return dhana_yogas
            
        except Exception as e:
            self.logger.error(f"Error detecting Dhana Yogas: {e}")
            return []
    
    def _detect_panch_mahapurusha_yogas(self, positions: Dict[str, PlanetaryPosition]) -> List[Dict[str, Any]]:
        """Detect Panch Mahapurusha Yogas."""
        mahapurusha_yogas = []
        
        try:
            for yoga_name, yoga_info in self._panch_mahapurusha_yogas.items():
                planet = yoga_info['planet']
                
                if planet not in positions:
                    continue
                
                planet_position = positions[planet]
                planet_rasi = planet_position.rasi
                planet_house = self._get_house_from_lagna(planet_position)
                
                # Check if planet is in own/exaltation sign
                if planet_rasi in yoga_info['positions']:
                    # Check if planet is in angular house
                    if planet_house in yoga_info['houses']:
                        mahapurusha_yogas.append({
                            'type': f'{yoga_name.title()} Yoga',
                            'planet': planet,
                            'rasi': planet_rasi,
                            'house': planet_house,
                            'strength': yoga_info['strength']
                        })
            
            return mahapurusha_yogas
            
        except Exception as e:
            self.logger.error(f"Error detecting Panch Mahapurusha Yogas: {e}")
            return []
    
    def _detect_special_yogas(self, positions: Dict[str, PlanetaryPosition]) -> List[Dict[str, Any]]:
        """Detect special yogas like Gaja Kesari, Chandra Mangal, etc."""
        special_yogas = []
        
        try:
            # Gaja Kesari Yoga
            if 'moon' in positions and 'jupiter' in positions:
                moon_house = self._get_house_from_lagna(positions['moon'])
                jupiter_house = self._get_house_from_lagna(positions['jupiter'])
                
                # Check if Moon and Jupiter are in mutual kendras
                if self._are_in_mutual_kendras(moon_house, jupiter_house):
                    special_yogas.append({
                        'type': 'Gaja Kesari Yoga',
                        'planets': ['moon', 'jupiter'],
                        'houses': [moon_house, jupiter_house],
                        'strength': 0.9
                    })
            
            # Budh Aditya Yoga
            if 'sun' in positions and 'mercury' in positions:
                sun_pos = positions['sun']
                mercury_pos = positions['mercury']
                
                # Check conjunction (within 10 degrees)
                if abs(sun_pos.longitude - mercury_pos.longitude) <= 10:
                    special_yogas.append({
                        'type': 'Budh Aditya Yoga',
                        'planets': ['sun', 'mercury'],
                        'strength': 0.7
                    })
            
            # Chandra Mangal Yoga
            if 'moon' in positions and 'mars' in positions:
                moon_pos = positions['moon']
                mars_pos = positions['mars']
                
                # Check conjunction or aspect
                if (abs(moon_pos.longitude - mars_pos.longitude) <= 10 or
                    self._check_aspect(moon_pos, mars_pos)):
                    special_yogas.append({
                        'type': 'Chandra Mangal Yoga',
                        'planets': ['moon', 'mars'],
                        'strength': 0.6
                    })
            
            return special_yogas
            
        except Exception as e:
            self.logger.error(f"Error detecting special yogas: {e}")
            return []
    
    def _detect_malefic_yogas(self, positions: Dict[str, PlanetaryPosition]) -> List[Dict[str, Any]]:
        """Detect malefic yogas that reduce favorability."""
        malefic_yogas = []
        
        try:
            # Kemadruma Yoga (Moon isolated)
            if 'moon' in positions:
                if self._check_kemadruma_yoga(positions):
                    malefic_yogas.append({
                        'type': 'Kemadruma Yoga',
                        'description': 'Moon isolated without benefic support',
                        'strength': 0.2
                    })
            
            # Grahan Yoga (Eclipse combinations)
            eclipse_combinations = self._check_eclipse_yogas(positions)
            malefic_yogas.extend(eclipse_combinations)
            
            return malefic_yogas
            
        except Exception as e:
            self.logger.error(f"Error detecting malefic yogas: {e}")
            return []
    
    def _calculate_overall_yoga_strength(self, active_yogas: Dict[str, Any]) -> float:
        """Calculate overall yoga strength from all active yogas."""
        try:
            total_strength = 0.0
            yoga_count = 0
            
            # Weight different types of yogas
            weights = {
                'raj_yogas': 0.3,
                'dhana_yogas': 0.25,
                'panch_mahapurusha': 0.25,
                'special_yogas': 0.15,
                'malefic_yogas': -0.05  # Negative weight for malefic yogas
            }
            
            for yoga_type, yogas in active_yogas.items():
                if yoga_type == 'overall_yoga_strength':
                    continue
                
                if not yogas:
                    continue
                
                type_strength = 0.0
                for yoga in yogas:
                    type_strength += yoga.get('strength', 0.5)
                
                if yogas:
                    avg_type_strength = type_strength / len(yogas)
                    weighted_strength = avg_type_strength * weights.get(yoga_type, 0.1)
                    total_strength += weighted_strength
                    yoga_count += 1
            
            # Normalize and ensure within bounds
            if yoga_count > 0:
                overall_strength = 0.5 + (total_strength / 2.0)  # Center around 0.5
            else:
                overall_strength = 0.5
            
            return max(0.0, min(1.0, overall_strength))
            
        except Exception as e:
            self.logger.error(f"Error calculating overall yoga strength: {e}")
            return 0.5
    
    def _calculate_natal_yoga_influence(self) -> float:
        """Calculate influence of natal yogas on current timing."""
        try:
            if not self._natal_yogas:
                return 0.5
            
            return self._calculate_overall_yoga_strength(self._natal_yogas)
            
        except Exception as e:
            self.logger.error(f"Error calculating natal yoga influence: {e}")
            return 0.5
    
    # Helper methods
    
    def _get_current_positions(self, date: datetime) -> Dict[str, PlanetaryPosition]:
        """Get current planetary positions for a date."""
        try:
            if not self.kundali_data.birth_details:
                return {}
            
            julian_day = self._ephemeris_engine.julian_day_from_datetime(
                date, self.kundali_data.birth_details.timezone_offset
            )
            
            return self._ephemeris_engine.calculate_planetary_positions(
                julian_day,
                self.kundali_data.birth_details.latitude,
                self.kundali_data.birth_details.longitude
            )
            
        except Exception as e:
            self.logger.error(f"Error getting current positions: {e}")
            return {}
    
    def _calculate_natal_houses(self) -> Dict[str, int]:
        """Calculate house positions for natal planets."""
        houses = {}
        
        try:
            if 'lagna' not in self._natal_positions:
                return houses
            
            lagna_rasi = self._natal_positions['lagna'].rasi
            
            for planet, position in self._natal_positions.items():
                if planet == 'lagna':
                    houses[planet] = 1
                else:
                    house = ((position.rasi - lagna_rasi) % 12) + 1
                    houses[planet] = house
            
            return houses
            
        except Exception as e:
            self.logger.error(f"Error calculating natal houses: {e}")
            return {}
    
    def _get_house_lords(self, positions: Dict[str, PlanetaryPosition]) -> Dict[int, str]:
        """Get house lords based on planetary positions."""
        # Simplified house lordship (traditional rulership)
        house_lords = {
            1: 'mars',     # Aries
            2: 'venus',    # Taurus
            3: 'mercury',  # Gemini
            4: 'moon',     # Cancer
            5: 'sun',      # Leo
            6: 'mercury',  # Virgo
            7: 'venus',    # Libra
            8: 'mars',     # Scorpio
            9: 'jupiter',  # Sagittarius
            10: 'saturn',  # Capricorn
            11: 'saturn',  # Aquarius
            12: 'jupiter'  # Pisces
        }
        
        # Adjust based on actual Lagna
        if 'lagna' in positions:
            lagna_rasi = positions['lagna'].rasi
            adjusted_lords = {}
            
            for house in range(1, 13):
                rasi = (lagna_rasi + house - 1) % 12
                adjusted_lords[house] = house_lords[rasi + 1]
            
            return adjusted_lords
        
        return house_lords
    
    def _get_house_from_lagna(self, position: PlanetaryPosition) -> int:
        """Get house number from Lagna."""
        try:
            if 'lagna' not in self._natal_positions:
                return position.rasi + 1
            
            lagna_rasi = self._natal_positions['lagna'].rasi
            return ((position.rasi - lagna_rasi) % 12) + 1
            
        except Exception:
            return 1
    
    def _check_planetary_relationship(self, positions: Dict[str, PlanetaryPosition], 
                                    planet1: str, planet2: str) -> bool:
        """Check if two planets are in conjunction or mutual aspect."""
        try:
            if planet1 not in positions or planet2 not in positions:
                return False
            
            pos1 = positions[planet1]
            pos2 = positions[planet2]
            
            # Check conjunction (within 10 degrees)
            if abs(pos1.longitude - pos2.longitude) <= 10:
                return True
            
            # Check mutual aspect
            return self._check_aspect(pos1, pos2)
            
        except Exception:
            return False
    
    def _check_aspect(self, pos1: PlanetaryPosition, pos2: PlanetaryPosition) -> bool:
        """Check if two planetary positions are in aspect."""
        try:
            angular_diff = abs(pos1.longitude - pos2.longitude)
            if angular_diff > 180:
                angular_diff = 360 - angular_diff
            
            # Major aspects with 5-degree orb
            major_aspects = [60, 90, 120, 180]
            
            for aspect in major_aspects:
                if abs(angular_diff - aspect) <= 5:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _are_in_mutual_kendras(self, house1: int, house2: int) -> bool:
        """Check if two houses are in mutual kendra relationship."""
        kendra_relationships = [
            (1, 4), (1, 7), (1, 10),
            (4, 7), (4, 10),
            (7, 10)
        ]
        
        relationship = tuple(sorted([house1, house2]))
        return relationship in kendra_relationships
    
    def _calculate_raj_yoga_strength(self, positions: Dict[str, PlanetaryPosition], 
                                   lord1: str, lord2: str) -> float:
        """Calculate strength of a Raj Yoga."""
        try:
            base_strength = 0.8
            
            # Check if lords are strong
            if lord1 in positions:
                lord1_strength = self._get_planetary_strength(positions[lord1])
                base_strength += (lord1_strength - 0.5) * 0.2
            
            if lord2 in positions:
                lord2_strength = self._get_planetary_strength(positions[lord2])
                base_strength += (lord2_strength - 0.5) * 0.2
            
            return max(0.0, min(1.0, base_strength))
            
        except Exception:
            return 0.8
    
    def _calculate_dhana_yoga_strength(self, positions: Dict[str, PlanetaryPosition], 
                                     lord1: str, lord2: str) -> float:
        """Calculate strength of a Dhana Yoga."""
        try:
            base_strength = 0.7
            
            # Similar to Raj Yoga but slightly lower base strength
            if lord1 in positions:
                lord1_strength = self._get_planetary_strength(positions[lord1])
                base_strength += (lord1_strength - 0.5) * 0.15
            
            if lord2 in positions:
                lord2_strength = self._get_planetary_strength(positions[lord2])
                base_strength += (lord2_strength - 0.5) * 0.15
            
            return max(0.0, min(1.0, base_strength))
            
        except Exception:
            return 0.7
    
    def _get_planetary_strength(self, position: PlanetaryPosition) -> float:
        """Get planetary strength using dignity and degree modifiers."""
        try:
            # Dignity rules (mirrors simplified scheme)
            dignity_rules = {
                'sun': {
                    'exaltation': [0], 'own_sign': [4], 'friendly': [1, 8, 11],
                    'neutral': [2, 5], 'enemy': [3, 6, 9, 10], 'debilitation': [7]
                },
                'moon': {
                    'exaltation': [1], 'own_sign': [3], 'friendly': [0, 4],
                    'neutral': [2, 5, 8, 11], 'enemy': [6, 7, 9, 10], 'debilitation': [7]
                },
                'mars': {
                    'exaltation': [9], 'own_sign': [0, 7], 'friendly': [3, 4, 8],
                    'neutral': [1, 5, 11], 'enemy': [2, 6, 10], 'debilitation': [3]
                },
                'mercury': {
                    'exaltation': [5], 'own_sign': [2, 5], 'friendly': [0, 4],
                    'neutral': [1, 6, 7, 8, 9, 10, 11], 'enemy': [3], 'debilitation': [11]
                },
                'jupiter': {
                    'exaltation': [3], 'own_sign': [8, 11], 'friendly': [0, 3, 4, 7],
                    'neutral': [1, 9, 10], 'enemy': [2, 5, 6], 'debilitation': [9]
                },
                'venus': {
                    'exaltation': [11], 'own_sign': [1, 6], 'friendly': [2, 5, 8, 9, 10],
                    'neutral': [0, 4], 'enemy': [3, 7], 'debilitation': [5]
                },
                'saturn': {
                    'exaltation': [6], 'own_sign': [9, 10], 'friendly': [1, 2, 5],
                    'neutral': [0, 8, 11], 'enemy': [3, 4, 6, 7], 'debilitation': [0]
                }
            }
            # Determine planet name from position context is not available here.
            # We approximate by using sign-only strength for generic calculation.
            rasi = position.rasi
            degree_in_sign = position.degree_in_sign
            # Generic sign strength: angular houses stronger when relative to Lagna
            base = 0.5
            # Degree modifier: middle degrees are stronger
            if 10 <= degree_in_sign <= 20:
                degree_mod = 1.0
            elif 5 <= degree_in_sign < 10 or 20 < degree_in_sign <= 25:
                degree_mod = 0.9
            else:
                degree_mod = 0.8
            return max(0.0, min(1.0, base * degree_mod))
        except Exception:
            return 0.6
    
    def _check_kemadruma_yoga(self, positions: Dict[str, PlanetaryPosition]) -> bool:
        """Check for Kemadruma Yoga (Moon isolation)."""
        try:
            if 'moon' not in positions:
                return False
            
            moon_house = self._get_house_from_lagna(positions['moon'])
            
            # Check if there are benefics in houses adjacent to Moon
            adjacent_houses = [(moon_house % 12) + 1, ((moon_house - 2) % 12) + 1]
            
            benefics = ['jupiter', 'venus', 'mercury']
            
            for benefic in benefics:
                if benefic in positions:
                    benefic_house = self._get_house_from_lagna(positions[benefic])
                    if benefic_house in adjacent_houses:
                        return False  # Kemadruma cancelled
            
            return True  # Kemadruma present
            
        except Exception:
            return False
    
    def _check_eclipse_yogas(self, positions: Dict[str, PlanetaryPosition]) -> List[Dict[str, Any]]:
        """Check for eclipse yogas (Grahan Yoga)."""
        eclipse_yogas = []
        
        try:
            # Sun with Rahu/Ketu
            if 'sun' in positions:
                sun_pos = positions['sun']
                
                for node in ['rahu', 'ketu']:
                    if node in positions:
                        node_pos = positions[node]
                        if abs(sun_pos.longitude - node_pos.longitude) <= 15:
                            eclipse_yogas.append({
                                'type': f'Solar Eclipse Yoga (Sun-{node.title()})',
                                'planets': ['sun', node],
                                'strength': 0.2
                            })
            
            # Moon with Rahu/Ketu
            if 'moon' in positions:
                moon_pos = positions['moon']
                
                for node in ['rahu', 'ketu']:
                    if node in positions:
                        node_pos = positions[node]
                        if abs(moon_pos.longitude - node_pos.longitude) <= 15:
                            eclipse_yogas.append({
                                'type': f'Lunar Eclipse Yoga (Moon-{node.title()})',
                                'planets': ['moon', node],
                                'strength': 0.2
                            })
            
            return eclipse_yogas
            
        except Exception as e:
            self.logger.error(f"Error checking eclipse yogas: {e}")
            return []
    
    def get_yoga_analysis_summary(self, date: datetime) -> Dict[str, Any]:
        """Get comprehensive yoga analysis summary."""
        try:
            active_yogas = self.detect_active_yogas(date)
            favorability = self.calculate_yoga_favorability(date)
            
            return {
                'date': date.isoformat(),
                'yoga_favorability': favorability,
                'active_yogas': active_yogas,
                'natal_yogas': self._natal_yogas,
                'recommendations': self._generate_yoga_recommendations(active_yogas)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating yoga analysis summary: {e}")
            return {'error': str(e)}
    
    def _generate_yoga_recommendations(self, active_yogas: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on active yogas."""
        recommendations = []
        
        try:
            # Raj Yoga recommendations
            raj_yogas = active_yogas.get('raj_yogas', [])
            if raj_yogas:
                recommendations.append("Excellent time for leadership and authority-related activities")
            
            # Dhana Yoga recommendations
            dhana_yogas = active_yogas.get('dhana_yogas', [])
            if dhana_yogas:
                recommendations.append("Favorable period for financial investments and wealth-building")
            
            # Panch Mahapurusha recommendations
            mahapurusha_yogas = active_yogas.get('panch_mahapurusha', [])
            for yoga in mahapurusha_yogas:
                planet = yoga.get('planet', '')
                if planet == 'mars':
                    recommendations.append("Good time for physical activities and competitive endeavors")
                elif planet == 'jupiter':
                    recommendations.append("Excellent for spiritual growth and educational pursuits")
                elif planet == 'venus':
                    recommendations.append("Favorable for artistic and relationship activities")
            
            # Malefic yoga warnings
            malefic_yogas = active_yogas.get('malefic_yogas', [])
            if malefic_yogas:
                recommendations.append("Exercise caution and avoid important new beginnings")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating yoga recommendations: {e}")
            return ["General period - maintain balance and positive attitude"]