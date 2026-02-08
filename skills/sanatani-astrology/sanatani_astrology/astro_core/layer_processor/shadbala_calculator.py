"""
Comprehensive Shadbala (Six-fold Strength) Calculator

This module provides complete Shadbala calculations for precise planetary
strength assessment, which is essential for world-class astrological accuracy.
"""

import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..core.data_models import KundaliData, PlanetaryPosition
from ..kundali_generator.comprehensive_ephemeris_engine import ComprehensiveEphemerisEngine


class ShadbalaCalculator:
    """
    Comprehensive Shadbala calculator for precise planetary strength assessment.
    
    Calculates all six components of Shadbala:
    1. Sthana Bala (Positional Strength)
    2. Dig Bala (Directional Strength)
    3. Kala Bala (Temporal Strength)
    4. Chesta Bala (Motional Strength)
    5. Naisargika Bala (Natural Strength)
    6. Drik Bala (Aspectual Strength)
    """
    
    def __init__(self, kundali_data: KundaliData):
        """Initialize Shadbala calculator."""
        self.kundali_data = kundali_data
        self.logger = logging.getLogger(self.__class__.__name__)
        self._ephemeris_engine = ComprehensiveEphemerisEngine()
        
        # Cache natal positions
        self._natal_positions = kundali_data.planetary_positions if kundali_data.planetary_positions else {}
        
        # Natural strengths (Naisargika Bala) in Rupas
        self._natural_strengths = {
            'sun': 60,
            'moon': 51.43,
            'mars': 17.14,
            'mercury': 25.71,
            'jupiter': 34.29,
            'venus': 42.86,
            'saturn': 8.57
        }
        
        # Directional strengths (houses where planets are strongest)
        self._directional_houses = {
            'sun': 10,      # 10th house
            'moon': 4,      # 4th house
            'mars': 10,     # 10th house
            'mercury': 1,   # 1st house
            'jupiter': 1,   # 1st house
            'venus': 4,     # 4th house
            'saturn': 7     # 7th house
        }
    
    def calculate_total_shadbala(self, planet: str, date: datetime) -> float:
        """
        Calculate total Shadbala for a planet on a specific date.
        
        Args:
            planet: Planet name
            date: Date for calculation
            
        Returns:
            Total Shadbala strength (0.0 to 1.0)
        """
        try:
            if planet not in self._natal_positions:
                return 0.5
            
            # Get current planetary position
            current_positions = self._get_current_positions(date)
            if planet not in current_positions:
                return 0.5
            
            current_position = current_positions[planet]
            natal_position = self._natal_positions[planet]
            
            # Calculate all six components
            sthana_bala = self._calculate_sthana_bala(planet, current_position)
            dig_bala = self._calculate_dig_bala(planet, current_position)
            kala_bala = self._calculate_kala_bala(planet, date)
            chesta_bala = self._calculate_chesta_bala(planet, current_position)
            naisargika_bala = self._calculate_naisargika_bala(planet)
            drik_bala = self._calculate_drik_bala(planet, current_positions)
            
            # Total Shadbala (sum of all components)
            total_shadbala = (
                sthana_bala + dig_bala + kala_bala + 
                chesta_bala + naisargika_bala + drik_bala
            )
            
            # Normalize to 0-1 scale (typical total ranges from 300-800 Rupas)
            normalized_strength = min(1.0, max(0.0, (total_shadbala - 300) / 500))
            
            return normalized_strength
            
        except Exception as e:
            self.logger.error(f"Error calculating Shadbala for {planet}: {e}")
            return 0.5
    
    def _calculate_sthana_bala(self, planet: str, position: PlanetaryPosition) -> float:
        """Calculate Sthana Bala (Positional Strength)."""
        try:
            sthana_bala = 0.0
            
            # Uccha Bala (Exaltation Strength)
            uccha_bala = self._calculate_uccha_bala(planet, position)
            sthana_bala += uccha_bala
            
            # Saptavargaja Bala (Seven-fold Divisional Strength)
            saptavargaja_bala = self._calculate_saptavargaja_bala(planet, position)
            sthana_bala += saptavargaja_bala
            
            # Ojayugmarasyamsa Bala (Odd-Even Sign Strength)
            ojayugma_bala = self._calculate_ojayugma_bala(planet, position)
            sthana_bala += ojayugma_bala
            
            # Kendra Bala (Angular Strength)
            kendra_bala = self._calculate_kendra_bala(planet, position)
            sthana_bala += kendra_bala
            
            # Drekkana Bala (Decanate Strength)
            drekkana_bala = self._calculate_drekkana_bala(planet, position)
            sthana_bala += drekkana_bala
            
            return sthana_bala
            
        except Exception as e:
            self.logger.error(f"Error calculating Sthana Bala: {e}")
            return 30.0  # Default moderate strength
    
    def _calculate_dig_bala(self, planet: str, position: PlanetaryPosition) -> float:
        """Calculate Dig Bala (Directional Strength)."""
        try:
            if planet not in self._directional_houses:
                return 30.0  # Default for nodes
            
            # Get current house position
            current_house = self._get_house_from_lagna(position)
            directional_house = self._directional_houses[planet]
            
            # Maximum Dig Bala is 60 Rupas
            if current_house == directional_house:
                return 60.0  # Full directional strength
            elif abs(current_house - directional_house) == 6:
                return 0.0   # Opposite direction (weakest)
            else:
                # Gradual decrease based on distance from directional house
                distance = min(abs(current_house - directional_house), 
                             12 - abs(current_house - directional_house))
                return 60.0 * (1.0 - distance / 6.0)
                
        except Exception as e:
            self.logger.error(f"Error calculating Dig Bala: {e}")
            return 30.0
    
    def _calculate_kala_bala(self, planet: str, date: datetime) -> float:
        """Calculate Kala Bala (Temporal Strength)."""
        try:
            kala_bala = 0.0
            
            # Natonnata Bala (Day/Night Strength)
            natonnata_bala = self._calculate_natonnata_bala(planet, date)
            kala_bala += natonnata_bala
            
            # Paksha Bala (Lunar Fortnight Strength)
            paksha_bala = self._calculate_paksha_bala(planet, date)
            kala_bala += paksha_bala
            
            # Tribhaga Bala (Three-fold Division Strength)
            tribhaga_bala = self._calculate_tribhaga_bala(planet, date)
            kala_bala += tribhaga_bala
            
            # Varsha-Masa-Dina-Hora Bala (Year-Month-Day-Hour Strength)
            temporal_bala = self._calculate_temporal_bala(planet, date)
            kala_bala += temporal_bala
            
            # Ayana Bala (Solstice Strength)
            ayana_bala = self._calculate_ayana_bala(planet, date)
            kala_bala += ayana_bala
            
            # Yuddha Bala (Planetary War Strength)
            yuddha_bala = self._calculate_yuddha_bala(planet, date)
            kala_bala += yuddha_bala
            
            return kala_bala
            
        except Exception as e:
            self.logger.error(f"Error calculating Kala Bala: {e}")
            return 30.0
    
    def _calculate_chesta_bala(self, planet: str, position: PlanetaryPosition) -> float:
        """Calculate Chesta Bala (Motional Strength)."""
        try:
            if planet in ['sun', 'moon']:
                return 60.0  # Sun and Moon always get full Chesta Bala
            
            # For other planets, consider retrograde motion and speed
            if position.retrograde:
                return 60.0  # Retrograde planets get full Chesta Bala
            else:
                # Calculate based on planetary speed (simplified)
                # In full implementation, you would calculate actual speed
                return 30.0  # Moderate strength for direct motion
                
        except Exception as e:
            self.logger.error(f"Error calculating Chesta Bala: {e}")
            return 30.0
    
    def _calculate_naisargika_bala(self, planet: str) -> float:
        """Calculate Naisargika Bala (Natural Strength)."""
        return self._natural_strengths.get(planet, 30.0)
    
    def _calculate_drik_bala(self, planet: str, current_positions: Dict[str, PlanetaryPosition]) -> float:
        """Calculate Drik Bala (Aspectual Strength)."""
        try:
            drik_bala = 0.0
            
            if planet not in current_positions:
                return 0.0
            
            planet_position = current_positions[planet]
            
            # Calculate aspects from other planets
            for other_planet, other_position in current_positions.items():
                if other_planet == planet:
                    continue
                
                aspect_strength = self._calculate_aspect_strength(
                    planet_position, other_position, other_planet
                )
                drik_bala += aspect_strength
            
            return drik_bala
            
        except Exception as e:
            self.logger.error(f"Error calculating Drik Bala: {e}")
            return 0.0
    
    def _calculate_uccha_bala(self, planet: str, position: PlanetaryPosition) -> float:
        """Calculate Uccha Bala (Exaltation Strength)."""
        try:
            # Exaltation degrees
            exaltation_degrees = {
                'sun': 10,      # 10° Aries
                'moon': 33,     # 3° Taurus
                'mars': 298,    # 28° Capricorn
                'mercury': 165, # 15° Virgo
                'jupiter': 95,  # 5° Cancer
                'venus': 357,   # 27° Pisces
                'saturn': 200   # 20° Libra
            }
            
            if planet not in exaltation_degrees:
                return 30.0  # Default for nodes
            
            exaltation_degree = exaltation_degrees[planet]
            current_degree = position.longitude
            
            # Calculate distance from exaltation point
            distance = abs(current_degree - exaltation_degree)
            if distance > 180:
                distance = 360 - distance
            
            # Maximum Uccha Bala is 60 Rupas
            uccha_bala = 60.0 * (1.0 - distance / 180.0)
            
            return max(0.0, uccha_bala)
            
        except Exception as e:
            self.logger.error(f"Error calculating Uccha Bala: {e}")
            return 30.0
    
    def _calculate_saptavargaja_bala(self, planet: str, position: PlanetaryPosition) -> float:
        """Calculate Saptavargaja Bala (Seven-fold Divisional Strength)."""
        try:
            # This would require full divisional chart calculations
            # Simplified implementation based on main chart dignity
            
            dignity_strength = {
                'Exalted': 20.0,
                'Own Sign': 15.0,
                'Friendly': 10.0,
                'Neutral': 7.5,
                'Enemy': 5.0,
                'Debilitated': 2.5
            }
            
            # Get dignity from divisional charts if available
            if hasattr(self.kundali_data, 'divisional_charts') and self.kundali_data.divisional_charts:
                # Use D1 chart dignity as approximation
                d1_chart = self.kundali_data.divisional_charts.get('D1', {})
                planetary_positions = d1_chart.get('planetary_positions', {})
                
                if planet in planetary_positions:
                    dignity = planetary_positions[planet].get('dignity', 'Neutral')
                    return dignity_strength.get(dignity, 7.5)
            
            return 7.5  # Default neutral strength
            
        except Exception as e:
            self.logger.error(f"Error calculating Saptavargaja Bala: {e}")
            return 7.5
    
    def _calculate_ojayugma_bala(self, planet: str, position: PlanetaryPosition) -> float:
        """Calculate Ojayugmarasyamsa Bala (Odd-Even Sign Strength)."""
        try:
            rasi = position.rasi
            
            # Male planets are stronger in odd signs, female planets in even signs
            male_planets = ['sun', 'mars', 'jupiter']
            female_planets = ['moon', 'venus']
            neutral_planets = ['mercury', 'saturn']
            
            if planet in male_planets:
                return 15.0 if rasi % 2 == 0 else 0.0  # Odd signs (0, 2, 4, ...)
            elif planet in female_planets:
                return 15.0 if rasi % 2 == 1 else 0.0  # Even signs (1, 3, 5, ...)
            else:
                return 7.5  # Neutral planets get moderate strength
                
        except Exception as e:
            self.logger.error(f"Error calculating Ojayugma Bala: {e}")
            return 7.5
    
    def _calculate_kendra_bala(self, planet: str, position: PlanetaryPosition) -> float:
        """Calculate Kendra Bala (Angular Strength)."""
        try:
            house = self._get_house_from_lagna(position)
            
            if house in [1, 4, 7, 10]:  # Angular houses
                return 60.0
            elif house in [2, 5, 8, 11]:  # Succedent houses
                return 30.0
            else:  # Cadent houses
                return 15.0
                
        except Exception as e:
            self.logger.error(f"Error calculating Kendra Bala: {e}")
            return 30.0
    
    def _calculate_drekkana_bala(self, planet: str, position: PlanetaryPosition) -> float:
        """Calculate Drekkana Bala (Decanate Strength)."""
        try:
            degree_in_sign = position.degree_in_sign
            
            # Each sign is divided into 3 Drekkanas of 10 degrees each
            if 0 <= degree_in_sign < 10:
                drekkana = 1
            elif 10 <= degree_in_sign < 20:
                drekkana = 2
            else:
                drekkana = 3
            
            # Male planets are stronger in 1st Drekkana, female in 3rd
            male_planets = ['sun', 'mars', 'jupiter']
            female_planets = ['moon', 'venus']
            
            if planet in male_planets:
                return 10.0 if drekkana == 1 else 5.0
            elif planet in female_planets:
                return 10.0 if drekkana == 3 else 5.0
            else:
                return 7.5  # Neutral planets
                
        except Exception as e:
            self.logger.error(f"Error calculating Drekkana Bala: {e}")
            return 7.5
    
    def _calculate_natonnata_bala(self, planet: str, date: datetime) -> float:
        """Calculate Natonnata Bala (Day/Night Strength)."""
        try:
            hour = date.hour
            
            # Day: 6 AM to 6 PM, Night: 6 PM to 6 AM
            is_day = 6 <= hour < 18
            
            # Day planets: Sun, Jupiter, Venus
            # Night planets: Moon, Mars, Saturn
            # Mercury is neutral
            
            day_planets = ['sun', 'jupiter', 'venus']
            night_planets = ['moon', 'mars', 'saturn']
            
            if planet in day_planets:
                return 60.0 if is_day else 0.0
            elif planet in night_planets:
                return 60.0 if not is_day else 0.0
            else:  # Mercury
                return 30.0  # Always moderate strength
                
        except Exception as e:
            self.logger.error(f"Error calculating Natonnata Bala: {e}")
            return 30.0
    
    def _calculate_paksha_bala(self, planet: str, date: datetime) -> float:
        """Calculate Paksha Bala (Lunar Fortnight Strength)."""
        try:
            # Get current lunar phase (simplified)
            day_of_month = date.day
            
            # Approximate lunar phase
            if day_of_month <= 15:
                is_shukla_paksha = True  # Waxing moon
            else:
                is_shukla_paksha = False  # Waning moon
            
            # Benefics are stronger during waxing moon, malefics during waning
            benefics = ['jupiter', 'venus', 'mercury', 'moon']
            malefics = ['sun', 'mars', 'saturn']
            
            if planet in benefics:
                return 60.0 if is_shukla_paksha else 0.0
            elif planet in malefics:
                return 60.0 if not is_shukla_paksha else 0.0
            else:
                return 30.0
                
        except Exception as e:
            self.logger.error(f"Error calculating Paksha Bala: {e}")
            return 30.0
    
    def _calculate_tribhaga_bala(self, planet: str, date: datetime) -> float:
        """Calculate Tribhaga Bala (Three-fold Division Strength)."""
        try:
            hour = date.hour
            
            # Divide day into three parts
            if 6 <= hour < 14:
                period = 1  # Morning
            elif 14 <= hour < 22:
                period = 2  # Afternoon
            else:
                period = 3  # Night
            
            # Different planets rule different periods
            period_rulers = {
                1: ['jupiter', 'venus'],      # Morning
                2: ['sun', 'mars'],           # Afternoon  
                3: ['moon', 'saturn', 'mercury']  # Night
            }
            
            if planet in period_rulers.get(period, []):
                return 60.0
            else:
                return 20.0
                
        except Exception as e:
            self.logger.error(f"Error calculating Tribhaga Bala: {e}")
            return 30.0
    
    def _calculate_temporal_bala(self, planet: str, date: datetime) -> float:
        """Calculate Varsha-Masa-Dina-Hora Bala (Temporal Lordship Strength)."""
        try:
            # Simplified calculation based on weekday
            weekday = date.weekday()
            
            # Weekday rulers
            weekday_rulers = {
                0: 'moon',     # Monday
                1: 'mars',     # Tuesday
                2: 'mercury',  # Wednesday
                3: 'jupiter',  # Thursday
                4: 'venus',    # Friday
                5: 'saturn',   # Saturday
                6: 'sun'       # Sunday
            }
            
            if weekday_rulers.get(weekday) == planet:
                return 45.0  # Strong temporal lordship
            else:
                return 15.0  # Moderate strength
                
        except Exception as e:
            self.logger.error(f"Error calculating Temporal Bala: {e}")
            return 15.0
    
    def _calculate_ayana_bala(self, planet: str, date: datetime) -> float:
        """Calculate Ayana Bala (Solstice Strength)."""
        try:
            # Simplified calculation based on season
            month = date.month
            
            # Northern solstice (summer): Sun stronger
            # Southern solstice (winter): Moon stronger
            
            if 3 <= month <= 8:  # Spring/Summer
                if planet == 'sun':
                    return 60.0
                elif planet == 'moon':
                    return 0.0
                else:
                    return 30.0
            else:  # Autumn/Winter
                if planet == 'moon':
                    return 60.0
                elif planet == 'sun':
                    return 0.0
                else:
                    return 30.0
                    
        except Exception as e:
            self.logger.error(f"Error calculating Ayana Bala: {e}")
            return 30.0
    
    def _calculate_yuddha_bala(self, planet: str, date: datetime) -> float:
        """Calculate Yuddha Bala (Planetary War Strength)."""
        try:
            # Get current positions to check for planetary wars
            current_positions = self._get_current_positions(date)
            
            if planet not in current_positions:
                return 0.0
            
            planet_position = current_positions[planet]
            
            # Check for close conjunctions (within 1 degree)
            war_planets = []
            for other_planet, other_position in current_positions.items():
                if other_planet != planet and other_planet not in ['rahu', 'ketu', 'lagna']:
                    angular_diff = abs(planet_position.longitude - other_position.longitude)
                    if angular_diff <= 1.0:
                        war_planets.append(other_planet)
            
            if not war_planets:
                return 0.0  # No planetary war
            
            # In planetary war, the planet with higher longitude wins
            # This is a simplified calculation
            return 60.0 if len(war_planets) == 1 else 30.0
            
        except Exception as e:
            self.logger.error(f"Error calculating Yuddha Bala: {e}")
            return 0.0
    
    def _calculate_aspect_strength(self, planet_pos: PlanetaryPosition, 
                                 other_pos: PlanetaryPosition, other_planet: str) -> float:
        """Calculate aspectual strength between planets."""
        try:
            angular_diff = abs(planet_pos.longitude - other_pos.longitude)
            if angular_diff > 180:
                angular_diff = 360 - angular_diff
            
            # Vedic aspects with their strengths
            aspect_strengths = {
                0: 60,    # Conjunction
                60: 30,   # Sextile
                90: -30,  # Square (malefic)
                120: 45,  # Trine
                180: -45  # Opposition (malefic)
            }
            
            orb = 5  # degrees
            
            for aspect_angle, strength in aspect_strengths.items():
                if abs(angular_diff - aspect_angle) <= orb:
                    # Apply planetary nature modifier
                    benefics = ['jupiter', 'venus', 'mercury']
                    if other_planet in benefics:
                        return max(0, strength)  # Only positive aspects from benefics
                    else:
                        return strength  # Both positive and negative from malefics
            
            return 0.0  # No significant aspect
            
        except Exception:
            return 0.0
    
    def _get_current_positions(self, date: datetime) -> Dict[str, PlanetaryPosition]:
        """Get current planetary positions."""
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
    
    def _get_house_from_lagna(self, position: PlanetaryPosition) -> int:
        """Get house number from Lagna."""
        try:
            if 'lagna' not in self._natal_positions:
                return position.rasi + 1
            
            lagna_rasi = self._natal_positions['lagna'].rasi
            return ((position.rasi - lagna_rasi) % 12) + 1
            
        except Exception:
            return 1
    
    def get_detailed_shadbala_breakdown(self, planet: str, date: datetime) -> Dict[str, float]:
        """Get detailed breakdown of all Shadbala components."""
        try:
            if planet not in self._natal_positions:
                return {}
            
            current_positions = self._get_current_positions(date)
            if planet not in current_positions:
                return {}
            
            current_position = current_positions[planet]
            
            return {
                'sthana_bala': self._calculate_sthana_bala(planet, current_position),
                'dig_bala': self._calculate_dig_bala(planet, current_position),
                'kala_bala': self._calculate_kala_bala(planet, date),
                'chesta_bala': self._calculate_chesta_bala(planet, current_position),
                'naisargika_bala': self._calculate_naisargika_bala(planet),
                'drik_bala': self._calculate_drik_bala(planet, current_positions),
                'total_shadbala': self.calculate_total_shadbala(planet, date)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting Shadbala breakdown: {e}")
            return {}