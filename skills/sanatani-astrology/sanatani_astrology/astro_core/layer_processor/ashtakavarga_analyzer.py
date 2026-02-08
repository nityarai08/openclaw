"""
Ashtakavarga System Analyzer for Enhanced Planetary Strength Assessment

This module provides comprehensive Ashtakavarga calculations for precise planetary
strength assessment, including individual planet Ashtakavarga charts and
Sarvashtakavarga (combined) analysis for enhanced timing accuracy.
"""

import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..core.data_models import KundaliData, PlanetaryPosition
from ..kundali_generator.comprehensive_ephemeris_engine import ComprehensiveEphemerisEngine


class AshtakavargaAnalyzer:
    """
    Comprehensive Ashtakavarga system analyzer for planetary strength assessment.
    
    Calculates Ashtakavarga bindus (points) for each planet and provides
    Sarvashtakavarga analysis for enhanced timing and strength calculations.
    """
    
    def __init__(self, kundali_data: KundaliData):
        """
        Initialize Ashtakavarga analyzer.
        
        Args:
            kundali_data: Complete kundali data with planetary positions
        """
        self.kundali_data = kundali_data
        self.logger = logging.getLogger(self.__class__.__name__)
        self._ephemeris_engine = ComprehensiveEphemerisEngine()
        
        # Cache natal planetary positions
        self._natal_positions = kundali_data.planetary_positions if kundali_data.planetary_positions else {}
        
        # Ashtakavarga contribution rules for each planet
        # Format: {contributing_planet: [favorable_houses_from_that_planet]}
        self._ashtakavarga_rules = {
            'sun': {
                'sun': [1, 2, 4, 7, 8, 9, 10, 11],
                'moon': [3, 6, 10, 11],
                'mars': [1, 2, 4, 7, 8, 9, 10, 11],
                'mercury': [3, 5, 6, 9, 10, 11, 12],
                'jupiter': [5, 6, 9, 11],
                'venus': [6, 7, 12],
                'saturn': [1, 2, 4, 7, 8, 9, 10, 11],
                'lagna': [3, 4, 6, 10, 11, 12]
            },
            'moon': {
                'sun': [3, 6, 7, 8, 10, 11],
                'moon': [1, 3, 6, 7, 10, 11],
                'mars': [2, 3, 5, 9, 10, 11],
                'mercury': [1, 3, 4, 5, 7, 8, 10, 11],
                'jupiter': [1, 4, 7, 8, 10, 11, 12],
                'venus': [3, 4, 5, 7, 9, 10, 11],
                'saturn': [3, 5, 6, 11],
                'lagna': [3, 6, 10, 11, 12]
            },
            'mars': {
                'sun': [3, 5, 6, 10, 11],
                'moon': [3, 6, 8, 10, 11],
                'mars': [1, 7, 8, 10, 11],
                'mercury': [3, 5, 6, 11],
                'jupiter': [6, 10, 11, 12],
                'venus': [6, 8, 11, 12],
                'saturn': [1, 4, 7, 8, 9, 10, 11],
                'lagna': [1, 3, 6, 10, 11]
            },
            'mercury': {
                'sun': [5, 6, 9, 11, 12],
                'moon': [2, 4, 6, 8, 10, 11],
                'mars': [1, 2, 4, 7, 8, 9, 10, 11],
                'mercury': [1, 3, 5, 6, 9, 10, 11, 12],
                'jupiter': [6, 8, 11, 12],
                'venus': [1, 2, 3, 4, 5, 8, 9, 11],
                'saturn': [1, 2, 4, 7, 8, 9, 10, 11],
                'lagna': [1, 2, 4, 6, 8, 10, 11]
            },
            'jupiter': {
                'sun': [1, 2, 3, 4, 7, 8, 9, 10, 11],
                'moon': [2, 5, 7, 9, 11],
                'mars': [1, 2, 4, 7, 8, 10, 11],
                'mercury': [1, 2, 4, 5, 6, 9, 10, 11],
                'jupiter': [1, 2, 3, 4, 7, 8, 10, 11],
                'venus': [2, 5, 6, 9, 10, 11],
                'saturn': [3, 5, 6, 12],
                'lagna': [1, 2, 4, 5, 6, 7, 9, 10, 11]
            },
            'venus': {
                'sun': [8, 11, 12],
                'moon': [1, 2, 3, 4, 5, 8, 9, 11, 12],
                'mars': [3, 5, 6, 9, 11, 12],
                'mercury': [3, 5, 6, 9, 11],
                'jupiter': [5, 8, 9, 10, 11],
                'venus': [1, 2, 3, 4, 5, 8, 9, 10, 11],
                'saturn': [3, 4, 5, 8, 9, 10, 11],
                'lagna': [1, 2, 3, 4, 5, 8, 9, 11]
            },
            'saturn': {
                'sun': [1, 2, 4, 7, 8, 10, 11],
                'moon': [3, 5, 6, 11],
                'mars': [3, 5, 10, 12],
                'mercury': [6, 8, 9, 10, 11, 12],
                'jupiter': [5, 6, 11, 12],
                'venus': [6, 11, 12],
                'saturn': [3, 5, 6, 11],
                'lagna': [1, 3, 4, 6, 10, 11, 12]
            }
        }
        
        # Calculate natal Ashtakavarga charts
        self._natal_ashtakavarga = self._calculate_natal_ashtakavarga()
        
        # Calculate Sarvashtakavarga (combined chart)
        self._sarvashtakavarga = self._calculate_sarvashtakavarga()
    
    def calculate_planetary_strength(self, planet_name: str, date: datetime) -> float:
        """
        Calculate Ashtakavarga-based planetary strength for a specific date.
        
        Args:
            planet_name: Name of the planet
            date: Date for calculation
            
        Returns:
            Strength score between 0.0 and 1.0
        """
        try:
            if planet_name not in self._natal_ashtakavarga:
                return 0.5  # Neutral fallback
            
            # Get current planetary position
            current_position = self._get_current_planetary_position(planet_name, date)
            if not current_position:
                return 0.5
            
            # Get current house position (1-12)
            current_house = self._get_house_from_position(current_position)
            
            # Get Ashtakavarga bindus for current house
            ashtakavarga_chart = self._natal_ashtakavarga[planet_name]
            bindus = ashtakavarga_chart.get(current_house, 0)
            
            # Convert bindus to strength score (0-8 bindus -> 0.0-1.0)
            strength_score = bindus / 8.0
            
            # Apply additional modifiers
            strength_score = self._apply_ashtakavarga_modifiers(
                planet_name, current_house, bindus, strength_score
            )
            
            return max(0.0, min(1.0, strength_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating Ashtakavarga strength for {planet_name}: {e}")
            return 0.5
    
    def calculate_sarvashtakavarga_strength(self, date: datetime) -> float:
        """
        Calculate overall Sarvashtakavarga strength for a date.
        
        Args:
            date: Date for calculation
            
        Returns:
            Overall strength score between 0.0 and 1.0
        """
        try:
            total_strength = 0.0
            planet_count = 0
            
            # Calculate strength for each planet
            planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
            
            for planet in planets:
                planet_strength = self.calculate_planetary_strength(planet, date)
                total_strength += planet_strength
                planet_count += 1
            
            # Calculate average strength
            if planet_count > 0:
                average_strength = total_strength / planet_count
            else:
                average_strength = 0.5
            
            return max(0.0, min(1.0, average_strength))
            
        except Exception as e:
            self.logger.error(f"Error calculating Sarvashtakavarga strength: {e}")
            return 0.5
    
    def _calculate_natal_ashtakavarga(self) -> Dict[str, Dict[int, int]]:
        """Calculate natal Ashtakavarga charts for all planets."""
        natal_ashtakavarga = {}
        
        try:
            planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
            
            for planet in planets:
                natal_ashtakavarga[planet] = self._calculate_planet_ashtakavarga(planet)
            
            return natal_ashtakavarga
            
        except Exception as e:
            self.logger.error(f"Error calculating natal Ashtakavarga: {e}")
            return {}
    
    def _calculate_planet_ashtakavarga(self, planet_name: str) -> Dict[int, int]:
        """Calculate Ashtakavarga chart for a specific planet."""
        try:
            if planet_name not in self._ashtakavarga_rules:
                return {}
            
            planet_chart = {}
            rules = self._ashtakavarga_rules[planet_name]
            
            # Initialize all houses with 0 bindus
            for house in range(1, 13):
                planet_chart[house] = 0
            
            # Calculate bindus for each house
            for contributing_planet, favorable_houses in rules.items():
                if contributing_planet == 'lagna':
                    # Use Lagna position
                    if 'lagna' in self._natal_positions:
                        lagna_house = self._get_house_from_position(self._natal_positions['lagna'])
                        contributing_house = lagna_house
                    else:
                        continue
                else:
                    # Use planetary position
                    if contributing_planet not in self._natal_positions:
                        continue
                    contributing_house = self._get_house_from_position(
                        self._natal_positions[contributing_planet]
                    )
                
                # Add bindus to favorable houses from contributing planet
                for favorable_house in favorable_houses:
                    # Calculate actual house position relative to contributing planet
                    actual_house = ((contributing_house - 1 + favorable_house - 1) % 12) + 1
                    planet_chart[actual_house] += 1
            
            return planet_chart
            
        except Exception as e:
            self.logger.error(f"Error calculating Ashtakavarga for {planet_name}: {e}")
            return {}
    
    def _calculate_sarvashtakavarga(self) -> Dict[int, int]:
        """Calculate Sarvashtakavarga (combined Ashtakavarga chart)."""
        try:
            sarvashtakavarga = {}
            
            # Initialize all houses with 0 bindus
            for house in range(1, 13):
                sarvashtakavarga[house] = 0
            
            # Sum bindus from all planetary Ashtakavarga charts
            for planet_chart in self._natal_ashtakavarga.values():
                for house, bindus in planet_chart.items():
                    sarvashtakavarga[house] += bindus
            
            return sarvashtakavarga
            
        except Exception as e:
            self.logger.error(f"Error calculating Sarvashtakavarga: {e}")
            return {}
    
    def _get_current_planetary_position(self, planet_name: str, date: datetime) -> Optional[PlanetaryPosition]:
        """Get current planetary position for a date."""
        try:
            if not self.kundali_data.birth_details:
                return None
            
            # Calculate Julian Day
            julian_day = self._ephemeris_engine.julian_day_from_datetime(
                date, self.kundali_data.birth_details.timezone_offset
            )
            
            # Get current planetary positions
            current_positions = self._ephemeris_engine.calculate_planetary_positions(
                julian_day,
                self.kundali_data.birth_details.latitude,
                self.kundali_data.birth_details.longitude
            )
            
            return current_positions.get(planet_name)
            
        except Exception as e:
            self.logger.error(f"Error getting current position for {planet_name}: {e}")
            return None
    
    def _get_house_from_position(self, position: PlanetaryPosition) -> int:
        """Get house number (1-12) from planetary position."""
        try:
            # Prefer calculating houses relative to natal Lagna when available
            if 'lagna' in self._natal_positions:
                lagna_rasi = self._natal_positions['lagna'].rasi
                return ((position.rasi - lagna_rasi) % 12) + 1
            # Fallback: approximate by treating rasi as house index (Aries Lagna assumption)
            return position.rasi + 1
            
        except Exception as e:
            self.logger.error(f"Error getting house from position: {e}")
            return 1
    
    def _apply_ashtakavarga_modifiers(self, planet_name: str, house: int, bindus: int, base_strength: float) -> float:
        """Apply additional modifiers to Ashtakavarga strength."""
        try:
            modified_strength = base_strength
            
            # Kakshya (sub-divisions) modifiers
            if bindus >= 6:
                modified_strength *= 1.2  # Very strong
            elif bindus >= 4:
                modified_strength *= 1.1  # Strong
            elif bindus <= 2:
                modified_strength *= 0.8  # Weak
            
            # Special house considerations
            if house in [1, 4, 7, 10]:  # Angular houses
                modified_strength *= 1.1
            elif house in [3, 6, 8, 12]:  # Challenging houses
                modified_strength *= 0.9
            
            # Planet-specific modifiers
            if planet_name == 'jupiter' and bindus >= 5:
                modified_strength *= 1.15  # Jupiter is especially strong with good bindus
            elif planet_name == 'saturn' and bindus <= 3:
                modified_strength *= 0.85  # Saturn is especially challenging with few bindus
            
            return max(0.0, min(1.0, modified_strength))
            
        except Exception as e:
            self.logger.error(f"Error applying Ashtakavarga modifiers: {e}")
            return base_strength
    
    def get_ashtakavarga_analysis(self, date: datetime) -> Dict[str, Any]:
        """
        Get comprehensive Ashtakavarga analysis for a date.
        
        Args:
            date: Date for analysis
            
        Returns:
            Dictionary with detailed Ashtakavarga analysis
        """
        try:
            analysis = {
                'date': date.isoformat(),
                'planetary_strengths': {},
                'sarvashtakavarga_strength': self.calculate_sarvashtakavarga_strength(date),
                'natal_ashtakavarga_charts': self._natal_ashtakavarga,
                'sarvashtakavarga_chart': self._sarvashtakavarga,
                'current_planetary_houses': {},
                'strength_recommendations': []
            }
            
            # Calculate individual planetary strengths
            planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
            
            for planet in planets:
                strength = self.calculate_planetary_strength(planet, date)
                analysis['planetary_strengths'][planet] = strength
                
                # Get current house position
                current_position = self._get_current_planetary_position(planet, date)
                if current_position:
                    current_house = self._get_house_from_position(current_position)
                    analysis['current_planetary_houses'][planet] = current_house
                    
                    # Get bindus for current house
                    bindus = self._natal_ashtakavarga.get(planet, {}).get(current_house, 0)
                    
                    # Generate recommendations
                    if bindus >= 6:
                        analysis['strength_recommendations'].append(
                            f"{planet.title()} is very strong ({bindus} bindus) - excellent for {planet}-related activities"
                        )
                    elif bindus <= 2:
                        analysis['strength_recommendations'].append(
                            f"{planet.title()} is weak ({bindus} bindus) - avoid important {planet}-related activities"
                        )
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error generating Ashtakavarga analysis: {e}")
            return {'error': str(e)}
    
    def get_favorable_periods(self, start_date: datetime, end_date: datetime, planet_name: str) -> List[Dict[str, Any]]:
        """
        Get favorable periods for a specific planet based on Ashtakavarga.
        
        Args:
            start_date: Start date for analysis
            end_date: End date for analysis
            planet_name: Planet to analyze
            
        Returns:
            List of favorable periods
        """
        try:
            favorable_periods = []
            current_date = start_date
            
            while current_date <= end_date:
                strength = self.calculate_planetary_strength(planet_name, current_date)
                
                if strength >= 0.7:  # Strong period
                    favorable_periods.append({
                        'date': current_date.isoformat(),
                        'strength': strength,
                        'level': 'Strong' if strength >= 0.8 else 'Good'
                    })
                
                current_date += timedelta(days=1)
            
            return favorable_periods
            
        except Exception as e:
            self.logger.error(f"Error getting favorable periods: {e}")
            return []
    
    def get_ashtakavarga_summary(self) -> Dict[str, Any]:
        """Get summary of natal Ashtakavarga charts."""
        try:
            summary = {
                'total_bindus_by_planet': {},
                'strongest_houses': {},
                'weakest_houses': {},
                'sarvashtakavarga_total': sum(self._sarvashtakavarga.values()),
                'average_bindus_per_house': 0
            }
            
            # Calculate totals for each planet
            for planet, chart in self._natal_ashtakavarga.items():
                total_bindus = sum(chart.values())
                summary['total_bindus_by_planet'][planet] = total_bindus
                
                # Find strongest and weakest houses
                strongest_house = max(chart, key=chart.get)
                weakest_house = min(chart, key=chart.get)
                
                summary['strongest_houses'][planet] = {
                    'house': strongest_house,
                    'bindus': chart[strongest_house]
                }
                summary['weakest_houses'][planet] = {
                    'house': weakest_house,
                    'bindus': chart[weakest_house]
                }
            
            # Calculate average bindus per house
            if self._sarvashtakavarga:
                summary['average_bindus_per_house'] = summary['sarvashtakavarga_total'] / 12
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error generating Ashtakavarga summary: {e}")
            return {'error': str(e)}
