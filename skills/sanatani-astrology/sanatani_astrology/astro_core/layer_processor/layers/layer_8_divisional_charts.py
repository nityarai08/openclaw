"""
Layer 8: Divisional Charts (30% Accuracy)

This layer calculates favorability based on divisional chart analysis using
the enhanced divisional chart analyzer we created earlier.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..base_layer import LayerProcessor
from ...core.data_models import KundaliData, PlanetaryPosition
from ..divisional_chart_analyzer import DivisionalChartAnalyzer


class Layer8_DivisionalCharts(LayerProcessor):
    """
    Layer 8: Divisional Charts processor with 30% accuracy.
    
    Calculates favorability based on:
    - Comprehensive divisional chart analysis (D1-D27)
    - Multi-chart correlation analysis
    - Life-area specific chart strengths
    - Divisional strength variation calculations for daily scores
    """
    
    def __init__(self, layer_id: int, accuracy: float, kundali_data: KundaliData):
        """Initialize Layer 8 processor."""
        super().__init__(layer_id, accuracy, kundali_data)
        
        # Initialize divisional chart analyzer
        self._divisional_analyzer = DivisionalChartAnalyzer(kundali_data)
        
        # Cache birth data
        if kundali_data.birth_details:
            self._birth_date = kundali_data.birth_details.date
            self._birth_time = kundali_data.birth_details.time
        else:
            raise ValueError("Birth details required for Layer 8 calculations")
        
        # Cache natal planetary positions
        self._natal_positions = kundali_data.planetary_positions
        
        # Life area weights for analysis
        self._life_area_weights = {
            'general': 0.25,
            'wealth': 0.20,
            'career': 0.20,
            'health': 0.15,
            'relationships': 0.20
        }
    
    def calculate_daily_score(self, date: datetime) -> float:
        """
        Calculate divisional charts favorability score for specific date.
        
        Args:
            date: Date for calculation
            
        Returns:
            Favorability score between 0.0 and 1.0
        """
        try:
            total_score = 0.0
            total_weight = 0.0
            
            # Calculate divisional strength for different life areas
            for life_area, weight in self._life_area_weights.items():
                # Get average planetary strength for this life area
                area_strength = self._calculate_life_area_strength(date, life_area)
                
                total_score += area_strength * weight
                total_weight += weight
            
            # Calculate weighted average
            if total_weight > 0:
                final_score = total_score / total_weight
            else:
                final_score = 0.5
            
            # Ensure score is within valid range
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate divisional charts score for {date}: {e}")
            raise
    
    def _calculate_life_area_strength(self, date: datetime, life_area: str) -> float:
        """Calculate strength for a specific life area."""
        try:
            planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
            total_strength = 0.0
            planet_count = 0
            
            for planet in planets:
                try:
                    planet_strength = self._divisional_analyzer.calculate_divisional_strength(
                        planet, date, life_area
                    )
                    total_strength += planet_strength
                    planet_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to calculate {planet} strength for {life_area}: {e}")
                    continue
            
            if planet_count > 0:
                return total_strength / planet_count
            else:
                return 0.5
                
        except Exception as e:
            self.logger.error(f"Error calculating life area strength for {life_area}: {e}")
            return 0.5
    
    def _get_contributing_factors(self, date: datetime) -> Dict[str, float]:
        """Get detailed breakdown of contributing factors."""
        try:
            factors = {}
            
            # Calculate strength for each life area
            for life_area in self._life_area_weights.keys():
                area_strength = self._calculate_life_area_strength(date, life_area)
                factors[f'{life_area}_strength'] = area_strength
            
            # Get comprehensive divisional analysis
            try:
                divisional_analysis = self._divisional_analyzer.get_comprehensive_divisional_analysis(date)
                
                # Add planetary divisional strengths
                planetary_strengths = divisional_analysis.get('planetary_divisional_strengths', {})
                for planet, strengths in planetary_strengths.items():
                    factors[f'{planet}_general_divisional'] = strengths.get('general', 0.5)
                
                # Add life area strengths
                life_area_strengths = divisional_analysis.get('life_area_strengths', {})
                for area, strength in life_area_strengths.items():
                    factors[f'{area}_divisional_strength'] = strength
                    
            except Exception as e:
                self.logger.warning(f"Could not get comprehensive divisional analysis: {e}")
            
            return factors
            
        except Exception:
            return {}
    
    def get_calculation_methodology(self) -> str:
        """Describe calculation methodology."""
        return (
            "Comprehensive divisional chart analysis with 30% accuracy. "
            "Analyzes planetary strengths across multiple divisional charts (D1-D27) "
            "for different life areas including general (25%), wealth (20%), "
            "career (20%), health (15%), and relationships (20%). Uses traditional "
            "divisional chart principles with modern computational precision for "
            "enhanced timing accuracy."
        )
    
    def get_layer_name(self) -> str:
        """Get layer name."""
        return "Divisional Charts Analysis"
    
    def get_layer_description(self) -> str:
        """Get layer description."""
        return (
            "Comprehensive analysis of divisional charts (D1-D27) for enhanced "
            "astrological accuracy. Evaluates planetary strengths across multiple "
            "specialized charts for different life areas including wealth, career, "
            "health, and relationships. Provides 30% accuracy using traditional "
            "Vedic divisional chart principles with modern computational methods."
        )
    
    def get_calculation_factors(self) -> List[str]:
        """Get list of calculation factors."""
        return [
            "Comprehensive divisional chart analysis (D1-D27)",
            "Multi-chart correlation analysis",
            "Life-area specific chart strengths (wealth, career, health, relationships)",
            "Divisional strength variation calculations for daily scores",
            "Traditional Vedic divisional chart principles"
        ]
    
    def validate_kundali_data(self) -> bool:
        """Validate kundali data for Layer 8 requirements."""
        if not self.kundali:
            self.logger.error("No kundali data provided")
            return False
        
        # Check for required birth details
        if not self.kundali.birth_details:
            self.logger.error("Birth details required for divisional chart calculations")
            return False
        
        # Check for required planetary positions
        if not self.kundali.planetary_positions:
            self.logger.error("Planetary positions required for divisional analysis")
            return False
        
        # Check for divisional charts data
        if not self.kundali.divisional_charts:
            self.logger.warning("No divisional charts data available - will use basic analysis")
        
        return True