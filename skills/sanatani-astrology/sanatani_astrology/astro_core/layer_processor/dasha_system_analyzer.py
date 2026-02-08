"""
Dasha System Analyzer for Enhanced Astrological Timing

This module provides comprehensive analysis of Vimshottari Dasha periods and their
influence on daily favorability calculations, including current dasha periods,
transitions, and planetary period effects.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..core.data_models import KundaliData, PlanetaryPosition
from ..kundali_generator.dasha_calculator import DashaCalculator


class DashaSystemAnalyzer:
    """
    Comprehensive analyzer for Vimshottari Dasha system with timing precision.
    
    Analyzes current Mahadasha, Antardasha, and Pratyantardasha periods to provide
    enhanced timing accuracy for favorability calculations.
    """
    
    def __init__(self, kundali_data: KundaliData):
        """
        Initialize dasha system analyzer.
        
        Args:
            kundali_data: Complete kundali data with birth details
        """
        self.kundali_data = kundali_data
        self.logger = logging.getLogger(self.__class__.__name__)
        self._dasha_calculator = DashaCalculator()
        
        # Cache birth details
        if kundali_data.birth_details:
            self._birth_date = kundali_data.birth_details.date
            self._birth_time = kundali_data.birth_details.time
        else:
            raise ValueError("Birth details required for Dasha calculations")
        
        # Cache natal planetary positions for dasha lord analysis
        self._natal_positions = kundali_data.planetary_positions
        
        # Dasha period lengths in years (Vimshottari system)
        self._dasha_periods = {
            'sun': 6,
            'moon': 10,
            'mars': 7,
            'rahu': 18,
            'jupiter': 16,
            'saturn': 19,
            'mercury': 17,
            'ketu': 7,
            'venus': 20
        }
        
        # Planetary favorability ratings for dasha periods
        self._dasha_favorability = {
            'sun': 0.8,      # Leadership, authority, confidence
            'moon': 0.7,     # Emotions, intuition, public relations
            'mars': 0.6,     # Energy, action, conflicts
            'rahu': 0.4,     # Illusion, materialism, sudden changes
            'jupiter': 0.9,  # Wisdom, spirituality, growth
            'saturn': 0.5,   # Discipline, delays, hard work
            'mercury': 0.8,  # Communication, intellect, business
            'ketu': 0.6,     # Spirituality, detachment, research
            'venus': 0.8     # Relationships, arts, luxury
        }
        
        # Dasha combination effects (Mahadasha-Antardasha)
        self._combination_modifiers = {
            # Benefic combinations
            ('jupiter', 'venus'): 1.2,
            ('venus', 'jupiter'): 1.2,
            ('jupiter', 'mercury'): 1.1,
            ('mercury', 'jupiter'): 1.1,
            ('venus', 'mercury'): 1.1,
            ('mercury', 'venus'): 1.1,
            ('sun', 'jupiter'): 1.1,
            ('jupiter', 'sun'): 1.1,
            
            # Challenging combinations
            ('saturn', 'mars'): 0.8,
            ('mars', 'saturn'): 0.8,
            ('rahu', 'ketu'): 0.7,
            ('ketu', 'rahu'): 0.7,
            ('saturn', 'rahu'): 0.7,
            ('rahu', 'saturn'): 0.7,
            
            # Neutral combinations
            ('sun', 'moon'): 1.0,
            ('moon', 'sun'): 1.0
        }
    
    def calculate_dasha_influence(self, date: datetime) -> float:
        """
        Calculate comprehensive dasha influence for a specific date.
        
        Args:
            date: Date for dasha analysis
            
        Returns:
            Dasha influence score between 0.0 and 1.0
        """
        try:
            # Get current dasha periods
            dasha_info = self.get_current_dasha_periods(date)
            
            if not dasha_info:
                return 0.5  # Neutral fallback
            
            # Calculate Mahadasha influence
            mahadasha_influence = self._calculate_mahadasha_influence(dasha_info)
            
            # Calculate Antardasha influence
            antardasha_influence = self._calculate_antardasha_influence(dasha_info)
            
            # Calculate Pratyantardasha influence
            pratyantardasha_influence = self._calculate_pratyantardasha_influence(dasha_info)
            
            # Calculate transition effects
            transition_effect = self._calculate_transition_effects(dasha_info, date)
            
            # Calculate planetary strength of dasha lords
            lord_strength = self._calculate_dasha_lord_strength(dasha_info)
            
            # Combine all influences with weights
            total_influence = (
                mahadasha_influence * 0.40 +
                antardasha_influence * 0.25 +
                pratyantardasha_influence * 0.15 +
                transition_effect * 0.10 +
                lord_strength * 0.10
            )
            
            return max(0.0, min(1.0, total_influence))
            
        except Exception as e:
            self.logger.error(f"Error calculating dasha influence for {date}: {e}")
            return 0.5
    
    def get_current_dasha_periods(self, date: datetime) -> Dict[str, Any]:
        """
        Get current Mahadasha, Antardasha, and Pratyantardasha for a date.
        
        Args:
            date: Date for dasha calculation
            
        Returns:
            Dictionary with current dasha period information
        """
        try:
            # Calculate birth moon nakshatra for dasha starting point
            if 'moon' not in self._natal_positions:
                return {}
            
            moon_position = self._natal_positions['moon']
            birth_nakshatra_index, birth_nakshatra_name, birth_nakshatra_lord = \
                self._dasha_calculator.get_nakshatra_from_longitude(moon_position.longitude)
            
            # Calculate dasha periods from birth
            birth_datetime = datetime.combine(self._birth_date, self._birth_time)
            days_since_birth = (date - birth_datetime).days
            
            # Get current dasha periods
            mahadasha_info = self._get_current_mahadasha(days_since_birth, birth_nakshatra_lord)
            antardasha_info = self._get_current_antardasha(mahadasha_info, days_since_birth)
            pratyantardasha_info = self._get_current_pratyantardasha(antardasha_info, days_since_birth)
            
            return {
                'date': date.isoformat(),
                'days_since_birth': days_since_birth,
                'birth_nakshatra': {
                    'index': birth_nakshatra_index,
                    'name': birth_nakshatra_name,
                    'lord': birth_nakshatra_lord
                },
                'mahadasha': mahadasha_info,
                'antardasha': antardasha_info,
                'pratyantardasha': pratyantardasha_info
            }
            
        except Exception as e:
            self.logger.error(f"Error getting current dasha periods: {e}")
            return {}
    
    def _get_current_mahadasha(self, days_since_birth: int, starting_lord: str) -> Dict[str, Any]:
        """Get current Mahadasha period information."""
        try:
            # Dasha sequence starting from birth nakshatra lord
            dasha_sequence = self._get_dasha_sequence(starting_lord)
            
            total_days = 0
            
            for i, (lord, period_years) in enumerate(dasha_sequence):
                period_days = int(period_years * 365.25)
                
                if total_days + period_days > days_since_birth:
                    # Found current Mahadasha
                    days_into_period = days_since_birth - total_days
                    progress_percent = (days_into_period / period_days) * 100
                    remaining_days = period_days - days_into_period
                    
                    return {
                        'lord': lord,
                        'period_years': period_years,
                        'period_days': period_days,
                        'days_completed': days_into_period,
                        'days_remaining': remaining_days,
                        'progress_percent': round(progress_percent, 2),
                        'favorability': self._dasha_favorability.get(lord, 0.5)
                    }
                
                total_days += period_days
            
            # If we reach here, we've completed all dashas (shouldn't happen in normal lifespan)
            return {'lord': 'unknown', 'favorability': 0.5}
            
        except Exception as e:
            self.logger.error(f"Error calculating Mahadasha: {e}")
            return {'lord': 'unknown', 'favorability': 0.5}
    
    def _get_current_antardasha(self, mahadasha_info: Dict[str, Any], days_since_birth: int) -> Dict[str, Any]:
        """Get current Antardasha period information."""
        try:
            if 'lord' not in mahadasha_info:
                return {'lord': 'unknown', 'favorability': 0.5}
            
            mahadasha_lord = mahadasha_info['lord']
            days_into_mahadasha = mahadasha_info.get('days_completed', 0)
            
            # Antardasha sequence starts with Mahadasha lord
            antardasha_sequence = self._get_dasha_sequence(mahadasha_lord)
            
            # Calculate Antardasha periods (proportional to Mahadasha)
            mahadasha_years = mahadasha_info.get('period_years', 1)
            total_antardasha_days = 0
            
            for lord, period_years in antardasha_sequence:
                # Antardasha period = (Planet's years / 120) * Mahadasha years * 365.25
                antardasha_years = (period_years / 120) * mahadasha_years
                antardasha_days = int(antardasha_years * 365.25)
                
                if total_antardasha_days + antardasha_days > days_into_mahadasha:
                    # Found current Antardasha
                    days_into_antardasha = days_into_mahadasha - total_antardasha_days
                    progress_percent = (days_into_antardasha / antardasha_days) * 100
                    remaining_days = antardasha_days - days_into_antardasha
                    
                    return {
                        'lord': lord,
                        'period_years': round(antardasha_years, 2),
                        'period_days': antardasha_days,
                        'days_completed': days_into_antardasha,
                        'days_remaining': remaining_days,
                        'progress_percent': round(progress_percent, 2),
                        'favorability': self._dasha_favorability.get(lord, 0.5)
                    }
                
                total_antardasha_days += antardasha_days
            
            return {'lord': 'unknown', 'favorability': 0.5}
            
        except Exception as e:
            self.logger.error(f"Error calculating Antardasha: {e}")
            return {'lord': 'unknown', 'favorability': 0.5}
    
    def _get_current_pratyantardasha(self, antardasha_info: Dict[str, Any], days_since_birth: int) -> Dict[str, Any]:
        """Get current Pratyantardasha period information."""
        try:
            if 'lord' not in antardasha_info:
                return {'lord': 'unknown', 'favorability': 0.5}
            
            antardasha_lord = antardasha_info['lord']
            days_into_antardasha = antardasha_info.get('days_completed', 0)
            
            # Pratyantardasha sequence starts with Antardasha lord
            pratyantardasha_sequence = self._get_dasha_sequence(antardasha_lord)
            
            # Calculate Pratyantardasha periods
            antardasha_years = antardasha_info.get('period_years', 1)
            total_pratyantardasha_days = 0
            
            for lord, period_years in pratyantardasha_sequence:
                # Pratyantardasha period = (Planet's years / 120) * Antardasha years * 365.25
                pratyantardasha_years = (period_years / 120) * antardasha_years
                pratyantardasha_days = int(pratyantardasha_years * 365.25)
                
                if total_pratyantardasha_days + pratyantardasha_days > days_into_antardasha:
                    # Found current Pratyantardasha
                    days_into_pratyantardasha = days_into_antardasha - total_pratyantardasha_days
                    progress_percent = (days_into_pratyantardasha / pratyantardasha_days) * 100
                    remaining_days = pratyantardasha_days - days_into_pratyantardasha
                    
                    return {
                        'lord': lord,
                        'period_years': round(pratyantardasha_years, 3),
                        'period_days': pratyantardasha_days,
                        'days_completed': days_into_pratyantardasha,
                        'days_remaining': remaining_days,
                        'progress_percent': round(progress_percent, 2),
                        'favorability': self._dasha_favorability.get(lord, 0.5)
                    }
                
                total_pratyantardasha_days += pratyantardasha_days
            
            return {'lord': 'unknown', 'favorability': 0.5}
            
        except Exception as e:
            self.logger.error(f"Error calculating Pratyantardasha: {e}")
            return {'lord': 'unknown', 'favorability': 0.5}
    
    def _get_dasha_sequence(self, starting_lord: str) -> List[Tuple[str, int]]:
        """Get the dasha sequence starting from a specific lord."""
        # Standard Vimshottari sequence
        standard_sequence = [
            ('sun', 6), ('moon', 10), ('mars', 7), ('rahu', 18), ('jupiter', 16),
            ('saturn', 19), ('mercury', 17), ('ketu', 7), ('venus', 20)
        ]
        
        # Find starting position
        start_index = 0
        for i, (lord, _) in enumerate(standard_sequence):
            if lord == starting_lord:
                start_index = i
                break
        
        # Create sequence starting from the specified lord
        sequence = []
        for i in range(9):  # 9 planets in Vimshottari
            index = (start_index + i) % 9
            sequence.append(standard_sequence[index])
        
        return sequence
    
    def _calculate_mahadasha_influence(self, dasha_info: Dict[str, Any]) -> float:
        """Calculate Mahadasha influence on favorability."""
        try:
            mahadasha = dasha_info.get('mahadasha', {})
            lord = mahadasha.get('lord', 'unknown')
            progress = mahadasha.get('progress_percent', 50)
            
            # Base favorability of the Mahadasha lord
            base_favorability = self._dasha_favorability.get(lord, 0.5)
            
            # Progress modifier (middle period is generally more stable)
            if 20 <= progress <= 80:
                progress_modifier = 1.1  # Stable middle period
            elif progress < 20 or progress > 80:
                progress_modifier = 0.9  # Beginning or end periods
            else:
                progress_modifier = 1.0
            
            return base_favorability * progress_modifier
            
        except Exception as e:
            self.logger.error(f"Error calculating Mahadasha influence: {e}")
            return 0.5
    
    def _calculate_antardasha_influence(self, dasha_info: Dict[str, Any]) -> float:
        """Calculate Antardasha influence on favorability."""
        try:
            mahadasha = dasha_info.get('mahadasha', {})
            antardasha = dasha_info.get('antardasha', {})
            
            mahadasha_lord = mahadasha.get('lord', 'unknown')
            antardasha_lord = antardasha.get('lord', 'unknown')
            
            # Base favorability of Antardasha lord
            base_favorability = self._dasha_favorability.get(antardasha_lord, 0.5)
            
            # Combination modifier
            combination_key = (mahadasha_lord, antardasha_lord)
            combination_modifier = self._combination_modifiers.get(combination_key, 1.0)
            
            return base_favorability * combination_modifier
            
        except Exception as e:
            self.logger.error(f"Error calculating Antardasha influence: {e}")
            return 0.5
    
    def _calculate_pratyantardasha_influence(self, dasha_info: Dict[str, Any]) -> float:
        """Calculate Pratyantardasha influence on favorability."""
        try:
            pratyantardasha = dasha_info.get('pratyantardasha', {})
            lord = pratyantardasha.get('lord', 'unknown')
            
            # Base favorability with reduced weight for sub-sub period
            base_favorability = self._dasha_favorability.get(lord, 0.5)
            
            # Pratyantardasha has less influence, so moderate the effect
            return 0.5 + (base_favorability - 0.5) * 0.5
            
        except Exception as e:
            self.logger.error(f"Error calculating Pratyantardasha influence: {e}")
            return 0.5
    
    def _calculate_transition_effects(self, dasha_info: Dict[str, Any], date: datetime) -> float:
        """Calculate effects of dasha transitions (sandhi periods)."""
        try:
            # Check if we're near any dasha transitions
            transition_effect = 1.0
            
            # Check Mahadasha transition
            mahadasha = dasha_info.get('mahadasha', {})
            days_remaining = mahadasha.get('days_remaining', 365)
            
            if days_remaining <= 30:  # Within 30 days of Mahadasha change
                transition_effect *= 0.8  # Reduce favorability during transition
            elif days_remaining <= 90:  # Within 3 months
                transition_effect *= 0.9
            
            # Check Antardasha transition
            antardasha = dasha_info.get('antardasha', {})
            antardasha_remaining = antardasha.get('days_remaining', 30)
            
            if antardasha_remaining <= 7:  # Within a week of Antardasha change
                transition_effect *= 0.9
            
            return min(1.0, max(0.3, transition_effect))
            
        except Exception as e:
            self.logger.error(f"Error calculating transition effects: {e}")
            return 1.0
    
    def _calculate_dasha_lord_strength(self, dasha_info: Dict[str, Any]) -> float:
        """Calculate strength of current dasha lords in natal chart."""
        try:
            mahadasha_lord = dasha_info.get('mahadasha', {}).get('lord', 'unknown')
            antardasha_lord = dasha_info.get('antardasha', {}).get('lord', 'unknown')
            
            # Get natal positions of dasha lords
            mahadasha_strength = self._get_planetary_strength(mahadasha_lord)
            antardasha_strength = self._get_planetary_strength(antardasha_lord)
            
            # Weighted combination
            combined_strength = (mahadasha_strength * 0.7 + antardasha_strength * 0.3)
            
            return combined_strength
            
        except Exception as e:
            self.logger.error(f"Error calculating dasha lord strength: {e}")
            return 0.5
    
    def _get_planetary_strength(self, planet_name: str) -> float:
        """Get natal strength of a planet."""
        try:
            if planet_name not in self._natal_positions:
                return 0.5
            
            planet_position = self._natal_positions[planet_name]
            
            # Simple strength calculation based on dignity
            # In a full implementation, this would use Shadbala or similar
            rasi = planet_position.rasi
            
            # Simplified dignity assessment
            if planet_name == 'sun' and rasi == 0:  # Sun in Aries (exalted)
                return 1.0
            elif planet_name == 'moon' and rasi == 1:  # Moon in Taurus (exalted)
                return 1.0
            elif planet_name == 'mars' and rasi == 9:  # Mars in Capricorn (exalted)
                return 1.0
            elif planet_name == 'mercury' and rasi == 5:  # Mercury in Virgo (exalted)
                return 1.0
            elif planet_name == 'jupiter' and rasi == 3:  # Jupiter in Cancer (exalted)
                return 1.0
            elif planet_name == 'venus' and rasi == 11:  # Venus in Pisces (exalted)
                return 1.0
            elif planet_name == 'saturn' and rasi == 6:  # Saturn in Libra (exalted)
                return 1.0
            else:
                # Default moderate strength
                return 0.6
                
        except Exception as e:
            self.logger.error(f"Error getting planetary strength for {planet_name}: {e}")
            return 0.5
    
    def get_dasha_analysis_summary(self, date: datetime) -> Dict[str, Any]:
        """
        Get comprehensive dasha analysis summary for a date.
        
        Args:
            date: Date for analysis
            
        Returns:
            Dictionary with detailed dasha analysis
        """
        try:
            dasha_info = self.get_current_dasha_periods(date)
            dasha_influence = self.calculate_dasha_influence(date)
            
            return {
                'date': date.isoformat(),
                'overall_dasha_influence': dasha_influence,
                'current_periods': dasha_info,
                'recommendations': self._generate_dasha_recommendations(dasha_info),
                'upcoming_changes': self._get_upcoming_dasha_changes(dasha_info, date)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating dasha analysis summary: {e}")
            return {'error': str(e)}
    
    def _generate_dasha_recommendations(self, dasha_info: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on current dasha periods."""
        recommendations = []
        
        try:
            mahadasha_lord = dasha_info.get('mahadasha', {}).get('lord', 'unknown')
            antardasha_lord = dasha_info.get('antardasha', {}).get('lord', 'unknown')
            
            # Mahadasha-specific recommendations
            if mahadasha_lord == 'jupiter':
                recommendations.append("Excellent time for spiritual growth, education, and wisdom-seeking activities")
            elif mahadasha_lord == 'venus':
                recommendations.append("Favorable for relationships, arts, luxury, and creative pursuits")
            elif mahadasha_lord == 'sun':
                recommendations.append("Good time for leadership roles, government work, and building authority")
            elif mahadasha_lord == 'saturn':
                recommendations.append("Focus on discipline, hard work, and long-term planning")
            elif mahadasha_lord == 'rahu':
                recommendations.append("Be cautious of illusions; good for material gains but watch for sudden changes")
            
            # Combination-specific recommendations
            combination = (mahadasha_lord, antardasha_lord)
            if combination in [('jupiter', 'venus'), ('venus', 'jupiter')]:
                recommendations.append("Exceptionally favorable period for marriage, partnerships, and prosperity")
            elif combination in [('saturn', 'mars'), ('mars', 'saturn')]:
                recommendations.append("Exercise patience and avoid conflicts; focus on steady progress")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["General period - maintain balance and positive attitude"]
    
    def _get_upcoming_dasha_changes(self, dasha_info: Dict[str, Any], current_date: datetime) -> List[Dict[str, Any]]:
        """Get information about upcoming dasha changes."""
        upcoming_changes = []
        
        try:
            # Check for upcoming Antardasha change
            antardasha = dasha_info.get('antardasha', {})
            days_remaining = antardasha.get('days_remaining', 0)
            
            if days_remaining <= 90:  # Within 3 months
                change_date = current_date + timedelta(days=days_remaining)
                upcoming_changes.append({
                    'type': 'Antardasha Change',
                    'date': change_date.isoformat(),
                    'days_remaining': days_remaining,
                    'current_lord': antardasha.get('lord', 'unknown'),
                    'significance': 'Medium'
                })
            
            # Check for upcoming Mahadasha change
            mahadasha = dasha_info.get('mahadasha', {})
            maha_days_remaining = mahadasha.get('days_remaining', 0)
            
            if maha_days_remaining <= 365:  # Within a year
                change_date = current_date + timedelta(days=maha_days_remaining)
                upcoming_changes.append({
                    'type': 'Mahadasha Change',
                    'date': change_date.isoformat(),
                    'days_remaining': maha_days_remaining,
                    'current_lord': mahadasha.get('lord', 'unknown'),
                    'significance': 'High'
                })
            
            return upcoming_changes
            
        except Exception as e:
            self.logger.error(f"Error getting upcoming changes: {e}")
            return []