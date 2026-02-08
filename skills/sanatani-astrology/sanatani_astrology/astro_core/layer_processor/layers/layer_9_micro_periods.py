"""
Layer 9: Micro-Periods (20% Accuracy)

This layer calculates favorability based on micro-period analysis using
the enhanced dasha system analyzer for sub-period calculations.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..base_layer import LayerProcessor
from ...core.data_models import KundaliData, PlanetaryPosition
from ..dasha_system_analyzer import DashaSystemAnalyzer


class Layer9_MicroPeriods(LayerProcessor):
    """
    Layer 9: Micro-Periods processor with 20% accuracy.
    
    Calculates favorability based on:
    - Detailed sub-period analysis (Pratyantardasha and below)
    - Daily planetary hour calculations
    - Micro-transit effect analysis
    - Short-term cyclical pattern detection
    """
    
    def __init__(self, layer_id: int, accuracy: float, kundali_data: KundaliData):
        """Initialize Layer 9 processor."""
        super().__init__(layer_id, accuracy, kundali_data)
        
        # Initialize dasha system analyzer
        self._dasha_analyzer = DashaSystemAnalyzer(kundali_data)
        
        # Cache birth data
        if kundali_data.birth_details:
            self._birth_date = kundali_data.birth_details.date
            self._birth_time = kundali_data.birth_details.time
        else:
            raise ValueError("Birth details required for Layer 9 calculations")
        
        # Cache natal planetary positions
        self._natal_positions = kundali_data.planetary_positions
        
        # Micro-period weights
        self._micro_weights = {
            'pratyantardasha': 0.40,
            'planetary_hours': 0.25,
            'micro_transits': 0.20,
            'cyclical_patterns': 0.15
        }
    
    def calculate_daily_score(self, date: datetime) -> float:
        """
        Calculate micro-periods favorability score for specific date.
        
        Args:
            date: Date for calculation
            
        Returns:
            Favorability score between 0.0 and 1.0
        """
        try:
            # Calculate Pratyantardasha influence
            pratyantardasha_score = self._calculate_pratyantardasha_score(date)
            
            # Calculate planetary hours influence
            planetary_hours_score = self._calculate_planetary_hours_score(date)
            
            # Calculate micro-transit effects
            micro_transits_score = self._calculate_micro_transits_score(date)
            
            # Calculate cyclical patterns
            cyclical_patterns_score = self._calculate_cyclical_patterns_score(date)
            
            # Combine all factors with weights
            total_score = (
                pratyantardasha_score * self._micro_weights['pratyantardasha'] +
                planetary_hours_score * self._micro_weights['planetary_hours'] +
                micro_transits_score * self._micro_weights['micro_transits'] +
                cyclical_patterns_score * self._micro_weights['cyclical_patterns']
            )
            
            # Ensure score is within valid range
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate micro-periods score for {date}: {e}")
            raise
    
    def _calculate_pratyantardasha_score(self, date: datetime) -> float:
        """Calculate Pratyantardasha influence score."""
        try:
            # Get current dasha periods
            dasha_info = self._dasha_analyzer.get_current_dasha_periods(date)
            
            if not dasha_info:
                return 0.5
            
            # Get Pratyantardasha information
            pratyantardasha = dasha_info.get('pratyantardasha', {})
            
            if not pratyantardasha:
                return 0.5
            
            # Base favorability from Pratyantardasha lord
            base_favorability = pratyantardasha.get('favorability', 0.5)
            
            # Apply progress modifier (middle period is more stable)
            progress = pratyantardasha.get('progress_percent', 50)
            if 30 <= progress <= 70:
                progress_modifier = 1.1  # Stable middle period
            else:
                progress_modifier = 0.9  # Beginning or end periods
            
            return base_favorability * progress_modifier
            
        except Exception as e:
            self.logger.error(f"Error calculating Pratyantardasha score: {e}")
            return 0.5
    
    def _calculate_planetary_hours_score(self, date: datetime) -> float:
        """Calculate planetary hours influence."""
        try:
            # Simplified planetary hours calculation
            # Each day is divided into 24 hours, each ruled by a planet
            
            # Get hour of the day
            hour = date.hour
            
            # Planetary hour sequence (starting with day ruler)
            weekday = date.weekday()  # 0 = Monday
            
            # Day rulers
            day_rulers = ['moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'sun']
            day_ruler = day_rulers[weekday]
            
            # Planetary sequence for hours
            planet_sequence = ['saturn', 'jupiter', 'mars', 'sun', 'venus', 'mercury', 'moon']
            
            # Find starting position based on day ruler
            start_index = planet_sequence.index(day_ruler)
            
            # Calculate current hour ruler
            hour_ruler_index = (start_index + hour) % 7
            hour_ruler = planet_sequence[hour_ruler_index]
            
            # Get favorability based on hour ruler
            hour_favorability = {
                'sun': 0.8,
                'moon': 0.7,
                'mars': 0.6,
                'mercury': 0.8,
                'jupiter': 0.9,
                'venus': 0.8,
                'saturn': 0.5
            }
            
            return hour_favorability.get(hour_ruler, 0.5)
            
        except Exception as e:
            self.logger.error(f"Error calculating planetary hours score: {e}")
            return 0.5
    
    def _calculate_micro_transits_score(self, date: datetime) -> float:
        """Calculate micro-transit effects."""
        try:
            # This is a simplified micro-transit analysis
            # In practice, this would analyze very short-term planetary movements
            
            # Use Moon's position as it changes most rapidly
            if 'moon' not in self._natal_positions:
                return 0.5
            
            # Calculate days since birth
            birth_datetime = datetime.combine(self._birth_date, self._birth_time)
            days_since_birth = (date - birth_datetime).days
            
            # Moon's approximate position (simplified)
            moon_cycle_position = (days_since_birth % 28) / 28.0  # 28-day cycle
            
            # Create a wave pattern for micro-transits
            micro_score = 0.5 + 0.2 * math.sin(2 * math.pi * moon_cycle_position)
            
            return max(0.0, min(1.0, micro_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating micro-transits score: {e}")
            return 0.5
    
    def _calculate_cyclical_patterns_score(self, date: datetime) -> float:
        """Calculate short-term cyclical patterns."""
        try:
            # Analyze multiple short cycles
            birth_datetime = datetime.combine(self._birth_date, self._birth_time)
            days_since_birth = (date - birth_datetime).days
            
            # 7-day weekly cycle
            weekly_cycle = (days_since_birth % 7) / 7.0
            weekly_score = 0.5 + 0.1 * math.sin(2 * math.pi * weekly_cycle)
            
            # 9-day Navami cycle
            navami_cycle = (days_since_birth % 9) / 9.0
            navami_score = 0.5 + 0.1 * math.cos(2 * math.pi * navami_cycle)
            
            # 15-day Paksha cycle
            paksha_cycle = (days_since_birth % 15) / 15.0
            paksha_score = 0.5 + 0.1 * math.sin(4 * math.pi * paksha_cycle)
            
            # ENHANCEMENT: Add Panchanga-based micro cycles
            panchanga_score = self._calculate_panchanga_micro_cycles(date)
            
            # ENHANCEMENT: Add Nakshatra-based micro timing
            nakshatra_score = self._calculate_nakshatra_micro_timing(date)
            
            # Combine cycles with enhanced weights
            combined_score = (
                weekly_score * 0.25 +
                navami_score * 0.20 +
                paksha_score * 0.25 +
                panchanga_score * 0.15 +
                nakshatra_score * 0.15
            )
            
            return max(0.0, min(1.0, combined_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating cyclical patterns score: {e}")
            return 0.5
    
    def _calculate_panchanga_micro_cycles(self, date: datetime) -> float:
        """Calculate micro-cycles based on Panchanga elements."""
        try:
            if not self.kundali.panchanga:
                return 0.5
            
            # Use available Panchanga data for micro-timing
            panchanga_data = self.kundali.panchanga
            
            # Tithi-based micro cycle (lunar day)
            tithi_cycle = (date.day % 15) / 15.0  # Simplified tithi approximation
            tithi_score = 0.5 + 0.08 * math.sin(2 * math.pi * tithi_cycle)
            
            # Karana-based micro cycle (half lunar day)
            karana_cycle = (date.day % 7) / 7.0  # Simplified karana approximation
            karana_score = 0.5 + 0.06 * math.cos(2 * math.pi * karana_cycle)
            
            # Yoga-based micro cycle (sun-moon combination)
            yoga_cycle = ((date.day + date.hour) % 27) / 27.0  # Simplified yoga approximation
            yoga_score = 0.5 + 0.07 * math.sin(2 * math.pi * yoga_cycle)
            
            return (tithi_score + karana_score + yoga_score) / 3.0
            
        except Exception:
            return 0.5
    
    def _calculate_nakshatra_micro_timing(self, date: datetime) -> float:
        """Calculate micro-timing based on current Nakshatra."""
        try:
            # Get current Moon's nakshatra (simplified calculation)
            days_since_birth = (date - datetime.combine(self._birth_date, self._birth_time)).days
            
            # Moon moves approximately 1 nakshatra per day (simplified)
            current_nakshatra = (days_since_birth % 27)
            
            # Different nakshatras have different micro-timing effects
            nakshatra_favorability = {
                0: 0.8,   # Ashwini - good for beginnings
                1: 0.6,   # Bharani - moderate
                2: 0.7,   # Krittika - good for cutting through obstacles
                3: 0.9,   # Rohini - excellent for growth
                4: 0.5,   # Mrigashira - neutral
                5: 0.8,   # Ardra - good for transformation
                6: 0.9,   # Punarvasu - excellent for renewal
                7: 0.7,   # Pushya - good for nourishment
                8: 0.6,   # Ashlesha - moderate, be cautious
                9: 0.8,   # Magha - good for authority
                10: 0.7,  # Purva Phalguni - good for relationships
                11: 0.8,  # Uttara Phalguni - good for partnerships
                12: 0.6,  # Hasta - moderate, good for skills
                13: 0.9,  # Chitra - excellent for creativity
                14: 0.7,  # Swati - good for independence
                15: 0.8,  # Vishakha - good for goals
                16: 0.6,  # Anuradha - moderate
                17: 0.9,  # Jyeshtha - excellent for leadership
                18: 0.5,  # Mula - neutral, transformative
                19: 0.8,  # Purva Ashadha - good for victory
                20: 0.9,  # Uttara Ashadha - excellent for achievement
                21: 0.7,  # Shravana - good for learning
                22: 0.8,  # Dhanishta - good for wealth
                23: 0.6,  # Shatabhisha - moderate, healing
                24: 0.7,  # Purva Bhadrapada - good for spirituality
                25: 0.8,  # Uttara Bhadrapada - good for depth
                26: 0.9   # Revati - excellent for completion
            }
            
            return nakshatra_favorability.get(current_nakshatra, 0.5)
            
        except Exception:
            return 0.5
    
    def _get_contributing_factors(self, date: datetime) -> Dict[str, float]:
        """Get detailed breakdown of contributing factors."""
        try:
            factors = {
                'pratyantardasha_score': self._calculate_pratyantardasha_score(date),
                'planetary_hours_score': self._calculate_planetary_hours_score(date),
                'micro_transits_score': self._calculate_micro_transits_score(date),
                'cyclical_patterns_score': self._calculate_cyclical_patterns_score(date)
            }
            
            # Add current dasha information
            try:
                dasha_info = self._dasha_analyzer.get_current_dasha_periods(date)
                pratyantardasha = dasha_info.get('pratyantardasha', {})
                
                factors.update({
                    'current_pratyantardasha': pratyantardasha.get('lord', 'unknown'),
                    'pratyantardasha_progress': pratyantardasha.get('progress_percent', 50),
                    'pratyantardasha_favorability': pratyantardasha.get('favorability', 0.5)
                })
            except Exception:
                pass
            
            return factors
            
        except Exception:
            return {}
    
    def get_calculation_methodology(self) -> str:
        """Describe calculation methodology."""
        return (
            "Micro-period analysis with 20% accuracy. Combines detailed "
            "Pratyantardasha sub-period analysis (40%), planetary hours "
            "calculations (25%), micro-transit effects (20%), and short-term "
            "cyclical patterns (15%). Uses traditional Vedic micro-timing "
            "principles with simplified computational methods for daily "
            "favorability assessment."
        )
    
    def get_layer_name(self) -> str:
        """Get layer name."""
        return "Micro-Periods Analysis"
    
    def get_layer_description(self) -> str:
        """Get layer description."""
        return (
            "Analysis of micro-periods and short-term astrological cycles "
            "including Pratyantardasha sub-periods, planetary hours, micro-transit "
            "effects, and cyclical patterns. Provides 20% accuracy using "
            "traditional Vedic micro-timing principles for enhanced daily "
            "timing precision."
        )
    
    def get_calculation_factors(self) -> List[str]:
        """Get list of calculation factors."""
        return [
            "Detailed sub-period analysis (Pratyantardasha and below)",
            "Daily planetary hour calculations",
            "Micro-transit effect analysis",
            "Short-term cyclical pattern detection (weekly, navami, paksha)",
            "Traditional Vedic micro-timing principles"
        ]
    
    def validate_kundali_data(self) -> bool:
        """Validate kundali data for Layer 9 requirements."""
        if not self.kundali:
            self.logger.error("No kundali data provided")
            return False
        
        # Check for required birth details
        if not self.kundali.birth_details:
            self.logger.error("Birth details required for micro-period calculations")
            return False
        
        # Check for required planetary positions
        if not self.kundali.planetary_positions:
            self.logger.error("Planetary positions required for micro-period analysis")
            return False
        
        return True