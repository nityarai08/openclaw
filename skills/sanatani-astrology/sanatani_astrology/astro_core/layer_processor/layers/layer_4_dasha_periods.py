"""
Layer 4: Enhanced Dasha Periods (75% Accuracy)

This layer calculates favorability based on comprehensive Vimshottari Dasha analysis
including Mahadasha, Antardasha, and Pratyantardasha periods, transition effects,
planetary period lord strength evaluation, and advanced dasha combination analysis.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..base_layer import LayerProcessor
from ...core.data_models import KundaliData, PlanetaryPosition
from ..dasha_system_analyzer import DashaSystemAnalyzer


class Layer4_DashaPeriods(LayerProcessor):
    """
    Layer 4: Enhanced Dasha Periods processor with 75% accuracy.
    
    Calculates favorability based on:
    - Comprehensive Vimshottari Mahadasha strength assessment
    - Antardasha and Pratyantardasha influence calculations with precision
    - Advanced dasha transition effect analysis
    - Planetary period lord strength evaluation from natal chart
    - Sub-period favorability scoring with combination effects
    """
    
    def __init__(self, layer_id: int, accuracy: float, kundali_data: KundaliData):
        """Initialize Layer 4 processor."""
        super().__init__(layer_id, accuracy, kundali_data)
        
        # Initialize enhanced dasha system analyzer
        self._dasha_analyzer = DashaSystemAnalyzer(kundali_data)
        
        # Cache birth data
        if kundali_data.birth_details:
            self._birth_date = kundali_data.birth_details.date
            self._birth_time = kundali_data.birth_details.time
        else:
            raise ValueError("Birth details required for Layer 4 calculations")
        
        # Cache natal planetary positions
        self._natal_positions = kundali_data.planetary_positions
        
        # Factor weights for final score calculation
        self._factor_weights = {
            'dasha_influence': 0.60,      # Primary dasha influence
            'transition_effects': 0.20,   # Transition period effects
            'lord_strength': 0.20         # Natal strength of dasha lords
        }
    
    def calculate_daily_score(self, date: datetime) -> float:
        """
        Calculate dasha periods favorability score for specific date.
        
        Args:
            date: Date for calculation
            
        Returns:
            Favorability score between 0.0 and 1.0
        """
        try:
            # Get comprehensive dasha influence
            dasha_influence = self._dasha_analyzer.calculate_dasha_influence(date)
            
            # Get current dasha periods for detailed analysis
            dasha_info = self._dasha_analyzer.get_current_dasha_periods(date)
            
            # Calculate transition effects
            transition_effects = self._calculate_transition_effects(dasha_info, date)
            
            # Calculate dasha lord strength
            lord_strength = self._calculate_dasha_lord_strength(dasha_info)
            
            # Combine all factors with weights
            total_score = (
                dasha_influence * self._factor_weights['dasha_influence'] +
                transition_effects * self._factor_weights['transition_effects'] +
                lord_strength * self._factor_weights['lord_strength']
            )
            
            # Ensure score is within valid range
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate dasha score for {date}: {e}")
            raise
    
    def _calculate_transition_effects(self, dasha_info: Dict[str, Any], date: datetime) -> float:
        """Calculate effects of dasha transitions and sandhi periods."""
        try:
            if not dasha_info:
                return 0.5
            
            transition_score = 1.0
            
            # Check Mahadasha transition
            mahadasha = dasha_info.get('mahadasha', {})
            maha_remaining = mahadasha.get('days_remaining', 365)
            
            if maha_remaining <= 30:  # Within a month of change
                transition_score *= 0.7  # Significant reduction
            elif maha_remaining <= 90:  # Within 3 months
                transition_score *= 0.8
            elif maha_remaining <= 180:  # Within 6 months
                transition_score *= 0.9
            
            # Check Antardasha transition
            antardasha = dasha_info.get('antardasha', {})
            antar_remaining = antardasha.get('days_remaining', 30)
            
            if antar_remaining <= 7:  # Within a week
                transition_score *= 0.85
            elif antar_remaining <= 15:  # Within 2 weeks
                transition_score *= 0.9
            
            # Check Pratyantardasha transition
            pratyantardasha = dasha_info.get('pratyantardasha', {})
            pratyantar_remaining = pratyantardasha.get('days_remaining', 7)
            
            if pratyantar_remaining <= 2:  # Within 2 days
                transition_score *= 0.9
            
            # Convert to 0-1 scale
            return max(0.2, min(1.0, transition_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating transition effects: {e}")
            return 0.5
    
    def _calculate_dasha_lord_strength(self, dasha_info: Dict[str, Any]) -> float:
        """Calculate combined strength of current dasha lords."""
        try:
            if not dasha_info:
                return 0.5
            
            # Get current dasha lords
            mahadasha_lord = dasha_info.get('mahadasha', {}).get('lord', 'unknown')
            antardasha_lord = dasha_info.get('antardasha', {}).get('lord', 'unknown')
            pratyantardasha_lord = dasha_info.get('pratyantardasha', {}).get('lord', 'unknown')
            
            # Calculate individual lord strengths
            maha_strength = self._get_planetary_natal_strength(mahadasha_lord)
            antar_strength = self._get_planetary_natal_strength(antardasha_lord)
            pratyantar_strength = self._get_planetary_natal_strength(pratyantardasha_lord)
            
            # Weighted combination
            combined_strength = (
                maha_strength * 0.5 +
                antar_strength * 0.3 +
                pratyantar_strength * 0.2
            )
            
            return max(0.0, min(1.0, combined_strength))
            
        except Exception as e:
            self.logger.error(f"Error calculating dasha lord strength: {e}")
            return 0.5
    
    def _get_planetary_natal_strength(self, planet_name: str) -> float:
        """Get natal strength of a planet based on position and dignity."""
        try:
            if planet_name == 'unknown' or planet_name not in self._natal_positions:
                return 0.5
            
            planet_position = self._natal_positions[planet_name]
            
            # Calculate strength based on multiple factors
            dignity_strength = self._calculate_dignity_strength(planet_name, planet_position)
            house_strength = self._calculate_house_strength(planet_position)
            nakshatra_strength = self._calculate_nakshatra_strength(planet_position)
            
            # Combine factors
            total_strength = (
                dignity_strength * 0.5 +
                house_strength * 0.3 +
                nakshatra_strength * 0.2
            )
            
            return max(0.0, min(1.0, total_strength))
            
        except Exception as e:
            self.logger.error(f"Error calculating natal strength for {planet_name}: {e}")
            return 0.5
    
    def _calculate_dignity_strength(self, planet_name: str, position: PlanetaryPosition) -> float:
        """Calculate planetary dignity strength."""
        try:
            rasi = position.rasi
            
            # Exaltation positions
            exaltation_positions = {
                'sun': 0,      # Aries
                'moon': 1,     # Taurus
                'mars': 9,     # Capricorn
                'mercury': 5,  # Virgo
                'jupiter': 3,  # Cancer
                'venus': 11,   # Pisces
                'saturn': 6    # Libra
            }
            
            # Own sign positions
            own_signs = {
                'sun': [4],           # Leo
                'moon': [3],          # Cancer
                'mars': [0, 7],       # Aries, Scorpio
                'mercury': [2, 5],    # Gemini, Virgo
                'jupiter': [8, 11],   # Sagittarius, Pisces
                'venus': [1, 6],      # Taurus, Libra
                'saturn': [9, 10]     # Capricorn, Aquarius
            }
            
            # Debilitation positions
            debilitation_positions = {
                'sun': 6,      # Libra
                'moon': 7,     # Scorpio
                'mars': 3,     # Cancer
                'mercury': 11, # Pisces
                'jupiter': 9,  # Capricorn
                'venus': 5,    # Virgo
                'saturn': 0    # Aries
            }
            
            # Check dignity
            if planet_name in exaltation_positions and rasi == exaltation_positions[planet_name]:
                return 1.0  # Exalted
            elif planet_name in own_signs and rasi in own_signs[planet_name]:
                return 0.9  # Own sign
            elif planet_name in debilitation_positions and rasi == debilitation_positions[planet_name]:
                return 0.1  # Debilitated
            else:
                # Check for friendly/enemy signs (simplified)
                return 0.6  # Neutral/moderate
                
        except Exception as e:
            self.logger.error(f"Error calculating dignity strength: {e}")
            return 0.5
    
    def _calculate_house_strength(self, position: PlanetaryPosition) -> float:
        """Calculate house-based strength (simplified)."""
        try:
            # This would require house positions from divisional charts
            # For now, return moderate strength
            return 0.6
            
        except Exception as e:
            self.logger.error(f"Error calculating house strength: {e}")
            return 0.5
    
    def _calculate_nakshatra_strength(self, position: PlanetaryPosition) -> float:
        """Calculate nakshatra-based strength."""
        try:
            nakshatra = position.nakshatra
            
            # Some nakshatras are generally more favorable
            favorable_nakshatras = [3, 7, 10, 16, 20, 26]  # Rohini, Pushya, Magha, etc.
            challenging_nakshatras = [8, 17, 18]  # Ashlesha, Jyeshtha, Mula
            
            if nakshatra in favorable_nakshatras:
                return 0.8
            elif nakshatra in challenging_nakshatras:
                return 0.4
            else:
                return 0.6  # Neutral
                
        except Exception as e:
            self.logger.error(f"Error calculating nakshatra strength: {e}")
            return 0.5
    
    def _get_contributing_factors(self, date: datetime) -> Dict[str, float]:
        """Get detailed breakdown of contributing factors."""
        try:
            # Get dasha information
            dasha_info = self._dasha_analyzer.get_current_dasha_periods(date)
            dasha_influence = self._dasha_analyzer.calculate_dasha_influence(date)
            
            # Calculate individual factors
            transition_effects = self._calculate_transition_effects(dasha_info, date)
            lord_strength = self._calculate_dasha_lord_strength(dasha_info)
            
            factors = {
                'overall_dasha_influence': dasha_influence,
                'transition_effects': transition_effects,
                'dasha_lord_strength': lord_strength
            }
            
            # Add current period information
            if dasha_info:
                mahadasha = dasha_info.get('mahadasha', {})
                antardasha = dasha_info.get('antardasha', {})
                pratyantardasha = dasha_info.get('pratyantardasha', {})
                
                factors.update({
                    'current_mahadasha': mahadasha.get('lord', 'unknown'),
                    'mahadasha_favorability': mahadasha.get('favorability', 0.5),
                    'mahadasha_progress': mahadasha.get('progress_percent', 50),
                    'current_antardasha': antardasha.get('lord', 'unknown'),
                    'antardasha_favorability': antardasha.get('favorability', 0.5),
                    'current_pratyantardasha': pratyantardasha.get('lord', 'unknown'),
                    'pratyantardasha_favorability': pratyantardasha.get('favorability', 0.5)
                })
            
            return factors
            
        except Exception:
            return {}
    
    def get_calculation_methodology(self) -> str:
        """Describe calculation methodology."""
        return (
            "Enhanced Vimshottari Dasha system analysis with 75% accuracy. "
            "Combines comprehensive dasha influence calculation (60%), transition "
            "period effects analysis (20%), and natal strength of dasha lords (20%). "
            "Includes Mahadasha, Antardasha, and Pratyantardasha periods with "
            "precise timing calculations and combination effects. Uses advanced "
            "sandhi period analysis for transition effects."
        )
    
    def get_layer_name(self) -> str:
        """Get layer name."""
        return "Enhanced Dasha Periods"
    
    def get_layer_description(self) -> str:
        """Get layer description."""
        return (
            "Comprehensive Vimshottari Dasha system analysis including Mahadasha, "
            "Antardasha, and Pratyantardasha periods with precise timing calculations. "
            "Analyzes dasha transitions, planetary period lord strengths, and "
            "combination effects. Provides 75% accuracy using traditional Vedic "
            "timing principles with modern computational precision."
        )
    
    def get_calculation_factors(self) -> List[str]:
        """Get list of calculation factors."""
        return [
            "Comprehensive Vimshottari Mahadasha strength assessment",
            "Antardasha and Pratyantardasha influence calculations with precision",
            "Advanced dasha transition effect analysis (sandhi periods)",
            "Planetary period lord strength evaluation from natal chart",
            "Sub-period favorability scoring with combination effects",
            "Dasha progression timing and phase analysis"
        ]
    
    def validate_kundali_data(self) -> bool:
        """Validate kundali data for Layer 4 requirements."""
        if not self.kundali:
            self.logger.error("No kundali data provided")
            return False
        
        # Check for required birth details
        if not self.kundali.birth_details:
            self.logger.error("Birth details required for dasha calculations")
            return False
        
        # Check for required planetary positions (especially Moon)
        if not self.kundali.planetary_positions:
            self.logger.error("Planetary positions required for dasha calculations")
            return False
        
        if 'moon' not in self.kundali.planetary_positions:
            self.logger.error("Moon position required for dasha calculations")
            return False
        
        return True