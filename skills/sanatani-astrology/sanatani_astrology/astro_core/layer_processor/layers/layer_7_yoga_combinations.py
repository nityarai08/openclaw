"""
Layer 7: Enhanced Yoga Combinations (50% Accuracy)

This layer calculates favorability based on advanced yoga detection including
Raj Yogas, Dhana Yogas, Panch Mahapurusha Yogas, daily yoga formations,
temporary yoga creation analysis, and comprehensive yoga strength assessment
with classical interpretation methods.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..base_layer import LayerProcessor
from ...core.data_models import KundaliData, PlanetaryPosition
from ..yoga_detection_system import YogaDetectionSystem


class Layer7_YogaCombinations(LayerProcessor):
    """
    Layer 7: Enhanced Yoga Combinations processor with 50% accuracy.
    
    Calculates favorability based on:
    - Advanced Raj Yoga and Dhana Yoga detection with strength assessment
    - Panch Mahapurusha Yoga identification and timing analysis
    - Daily yoga formation detection with transit-based temporary yogas
    - Classical yoga interpretation with modern computational precision
    - Comprehensive yoga strength assessment and dissolution timing
    """
    
    def __init__(self, layer_id: int, accuracy: float, kundali_data: KundaliData):
        """Initialize Layer 7 processor."""
        super().__init__(layer_id, accuracy, kundali_data)
        
        # Initialize advanced yoga detection system
        self._yoga_detector = YogaDetectionSystem(kundali_data)
        
        # Cache birth data
        if kundali_data.birth_details:
            self._birth_date = kundali_data.birth_details.date
            self._birth_time = kundali_data.birth_details.time
        else:
            raise ValueError("Birth details required for Layer 7 calculations")
        
        # Cache natal planetary positions
        self._natal_positions = kundali_data.planetary_positions
        
        # Factor weights for final score calculation
        self._factor_weights = {
            'yoga_favorability': 0.40,    # Primary yoga influence
            'natal_yoga_strength': 0.25,  # Natal yoga background influence
            'temporary_yogas': 0.20,      # Transit-formed temporary yogas
            'yoga_timing': 0.15           # Yoga formation/dissolution timing
        }
    
    def calculate_daily_score(self, date: datetime) -> float:
        """
        Calculate yoga combinations favorability score for specific date.
        
        Args:
            date: Date for calculation
            
        Returns:
            Favorability score between 0.0 and 1.0
        """
        try:
            # Calculate primary yoga favorability
            yoga_favorability = self._yoga_detector.calculate_yoga_favorability(date)
            
            # Calculate natal yoga strength influence
            natal_yoga_strength = self._calculate_natal_yoga_strength()
            
            # Calculate temporary yoga effects
            temporary_yoga_score = self._calculate_temporary_yoga_score(date)
            
            # Calculate yoga timing effects
            yoga_timing_score = self._calculate_yoga_timing_score(date)
            
            # Combine all factors with weights
            total_score = (
                yoga_favorability * self._factor_weights['yoga_favorability'] +
                natal_yoga_strength * self._factor_weights['natal_yoga_strength'] +
                temporary_yoga_score * self._factor_weights['temporary_yogas'] +
                yoga_timing_score * self._factor_weights['yoga_timing']
            )
            
            # Ensure score is within valid range
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate yoga combinations score for {date}: {e}")
            raise
    
    def _calculate_natal_yoga_strength(self) -> float:
        """Calculate background influence of natal yogas."""
        try:
            # This provides a baseline yoga strength from the natal chart
            # that influences all daily calculations
            
            # Get natal yoga analysis
            natal_analysis = self._yoga_detector.get_yoga_analysis_summary(
                datetime.combine(self._birth_date, self._birth_time)
            )
            
            natal_favorability = natal_analysis.get('yoga_favorability', 0.5)
            
            # Moderate the natal influence (it's background, not primary)
            moderated_influence = 0.5 + (natal_favorability - 0.5) * 0.3
            
            return max(0.0, min(1.0, moderated_influence))
            
        except Exception as e:
            self.logger.error(f"Error calculating natal yoga strength: {e}")
            return 0.5
    
    def _calculate_temporary_yoga_score(self, date: datetime) -> float:
        """Calculate score for temporary yogas formed by transits."""
        try:
            # Get active yogas for the date
            active_yogas = self._yoga_detector.detect_active_yogas(date)
            
            if not active_yogas:
                return 0.5
            
            # Focus on temporary formations (not natal)
            temporary_score = 0.5
            
            # Check for strong temporary Raj Yogas
            raj_yogas = active_yogas.get('raj_yogas', [])
            if raj_yogas:
                raj_strength = sum(yoga.get('strength', 0.5) for yoga in raj_yogas) / len(raj_yogas)
                temporary_score += (raj_strength - 0.5) * 0.3
            
            # Check for temporary Dhana Yogas
            dhana_yogas = active_yogas.get('dhana_yogas', [])
            if dhana_yogas:
                dhana_strength = sum(yoga.get('strength', 0.5) for yoga in dhana_yogas) / len(dhana_yogas)
                temporary_score += (dhana_strength - 0.5) * 0.2
            
            # Check for active Panch Mahapurusha Yogas
            mahapurusha_yogas = active_yogas.get('panch_mahapurusha', [])
            if mahapurusha_yogas:
                mahapurusha_strength = sum(yoga.get('strength', 0.5) for yoga in mahapurusha_yogas) / len(mahapurusha_yogas)
                temporary_score += (mahapurusha_strength - 0.5) * 0.25
            
            # Reduce for malefic yogas
            malefic_yogas = active_yogas.get('malefic_yogas', [])
            if malefic_yogas:
                malefic_impact = sum(yoga.get('strength', 0.5) for yoga in malefic_yogas) / len(malefic_yogas)
                temporary_score -= (0.5 - malefic_impact) * 0.2
            
            # ENHANCEMENT: Add Panchanga-based yoga timing
            panchanga_bonus = self._calculate_panchanga_yoga_bonus(date)
            temporary_score += panchanga_bonus * 0.1
            
            # ENHANCEMENT: Add divisional chart yoga support
            divisional_yoga_bonus = self._calculate_divisional_yoga_bonus(date)
            temporary_score += divisional_yoga_bonus * 0.15
            
            return max(0.0, min(1.0, temporary_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating temporary yoga score: {e}")
            return 0.5
    
    def _calculate_panchanga_yoga_bonus(self, date: datetime) -> float:
        """Calculate bonus from Panchanga-based yoga timing."""
        try:
            if not self.kundali.panchanga:
                return 0.0
            
            # Use Panchanga data for enhanced yoga timing
            # This would analyze Tithi, Nakshatra, Yoga, Karana combinations
            # that enhance or diminish yoga effects
            
            # Simplified implementation - in practice would use full Panchanga
            day_of_week = date.weekday()
            
            # Certain days are more favorable for specific yogas
            favorable_days = {
                0: 0.1,  # Monday - Moon day, good for emotional yogas
                3: 0.15, # Thursday - Jupiter day, excellent for Raj yogas
                4: 0.12, # Friday - Venus day, good for Dhana yogas
                6: 0.08  # Sunday - Sun day, moderate for authority yogas
            }
            
            return favorable_days.get(day_of_week, 0.0)
            
        except Exception:
            return 0.0
    
    def _calculate_divisional_yoga_bonus(self, date: datetime) -> float:
        """Calculate bonus from divisional chart yogas."""
        try:
            if not self.kundali.divisional_charts:
                return 0.0
            
            # Check for yogas in key divisional charts
            divisional_bonus = 0.0
            
            # D9 (Navamsa) yogas are most important
            if 'D9' in self.kundali.divisional_charts:
                d9_yogas = self.kundali.divisional_charts['D9'].get('yogas', [])
                if d9_yogas:
                    divisional_bonus += 0.2
            
            # D10 (Dasamsa) yogas for career-related periods
            if 'D10' in self.kundali.divisional_charts:
                d10_yogas = self.kundali.divisional_charts['D10'].get('yogas', [])
                if d10_yogas:
                    divisional_bonus += 0.15
            
            # D2 (Hora) yogas for wealth periods
            if 'D2' in self.kundali.divisional_charts:
                d2_yogas = self.kundali.divisional_charts['D2'].get('yogas', [])
                if d2_yogas:
                    divisional_bonus += 0.1
            
            return min(0.3, divisional_bonus)  # Cap at 0.3
            
        except Exception:
            return 0.0
    
    def _calculate_yoga_timing_score(self, date: datetime) -> float:
        """Calculate yoga formation and dissolution timing effects."""
        try:
            # This analyzes whether yogas are forming, stable, or dissolving
            timing_score = 0.5  # Base neutral score
            
            # Check yoga stability over a few days
            yesterday = date - timedelta(days=1)
            tomorrow = date + timedelta(days=1)
            
            try:
                yesterday_yogas = self._yoga_detector.detect_active_yogas(yesterday)
                today_yogas = self._yoga_detector.detect_active_yogas(date)
                tomorrow_yogas = self._yoga_detector.detect_active_yogas(tomorrow)
                
                # Count yoga formations
                yesterday_count = self._count_significant_yogas(yesterday_yogas)
                today_count = self._count_significant_yogas(today_yogas)
                tomorrow_count = self._count_significant_yogas(tomorrow_yogas)
                
                # Analyze trend
                if today_count > yesterday_count:
                    timing_score += 0.1  # Yogas forming
                elif today_count < yesterday_count:
                    timing_score -= 0.1  # Yogas dissolving
                
                if tomorrow_count > today_count:
                    timing_score += 0.05  # More yogas coming
                elif tomorrow_count < today_count:
                    timing_score -= 0.05  # Yogas will dissolve
                
                # Stability bonus
                if yesterday_count == today_count == tomorrow_count and today_count > 0:
                    timing_score += 0.1  # Stable yoga period
                
            except Exception:
                # If we can't calculate adjacent days, use neutral timing
                pass
            
            return max(0.0, min(1.0, timing_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating yoga timing score: {e}")
            return 0.5
    
    def _count_significant_yogas(self, yogas_dict: Dict[str, Any]) -> int:
        """Count significant yogas from a yoga detection result."""
        try:
            count = 0
            
            # Count Raj Yogas
            raj_yogas = yogas_dict.get('raj_yogas', [])
            count += len([y for y in raj_yogas if y.get('strength', 0) > 0.6])
            
            # Count Dhana Yogas
            dhana_yogas = yogas_dict.get('dhana_yogas', [])
            count += len([y for y in dhana_yogas if y.get('strength', 0) > 0.6])
            
            # Count Panch Mahapurusha Yogas
            mahapurusha_yogas = yogas_dict.get('panch_mahapurusha', [])
            count += len([y for y in mahapurusha_yogas if y.get('strength', 0) > 0.7])
            
            # Count Special Yogas
            special_yogas = yogas_dict.get('special_yogas', [])
            count += len([y for y in special_yogas if y.get('strength', 0) > 0.6])
            
            return count
            
        except Exception:
            return 0
    
    def _get_contributing_factors(self, date: datetime) -> Dict[str, float]:
        """Get detailed breakdown of contributing factors."""
        try:
            # Get comprehensive yoga analysis
            yoga_analysis = self._yoga_detector.get_yoga_analysis_summary(date)
            
            factors = {
                'yoga_favorability': yoga_analysis.get('yoga_favorability', 0.5),
                'natal_yoga_strength': self._calculate_natal_yoga_strength(),
                'temporary_yoga_score': self._calculate_temporary_yoga_score(date),
                'yoga_timing_score': self._calculate_yoga_timing_score(date)
            }
            
            # Add active yoga counts
            active_yogas = yoga_analysis.get('active_yogas', {})
            factors.update({
                'active_raj_yogas': len(active_yogas.get('raj_yogas', [])),
                'active_dhana_yogas': len(active_yogas.get('dhana_yogas', [])),
                'active_mahapurusha_yogas': len(active_yogas.get('panch_mahapurusha', [])),
                'active_special_yogas': len(active_yogas.get('special_yogas', [])),
                'active_malefic_yogas': len(active_yogas.get('malefic_yogas', [])),
                'overall_yoga_strength': active_yogas.get('overall_yoga_strength', 0.5)
            })
            
            return factors
            
        except Exception:
            return {}
    
    def get_calculation_methodology(self) -> str:
        """Describe calculation methodology."""
        return (
            "Advanced yoga detection and analysis system with 50% accuracy. "
            "Combines comprehensive yoga favorability calculation (40%), natal yoga "
            "strength background influence (25%), temporary yoga formations from "
            "transits (20%), and yoga timing analysis including formation and "
            "dissolution patterns (15%). Uses classical Vedic yoga definitions "
            "with modern computational precision for Raj Yogas, Dhana Yogas, "
            "Panch Mahapurusha Yogas, and other significant combinations."
        )
    
    def get_layer_name(self) -> str:
        """Get layer name."""
        return "Enhanced Yoga Combinations"
    
    def get_layer_description(self) -> str:
        """Get layer description."""
        return (
            "Comprehensive analysis of Vedic astrological yogas including Raj Yogas, "
            "Dhana Yogas, Panch Mahapurusha Yogas, and other significant planetary "
            "combinations. Analyzes both natal and transit-formed temporary yogas "
            "with strength assessment and timing analysis. Provides enhanced accuracy "
            "through advanced yoga detection algorithms and classical interpretation "
            "methods combined with modern computational precision."
        )
    
    def get_calculation_factors(self) -> List[str]:
        """Get list of calculation factors."""
        return [
            "Advanced Raj Yoga and Dhana Yoga detection with strength assessment",
            "Panch Mahapurusha Yoga identification and timing analysis",
            "Daily yoga formation detection with transit-based temporary yogas",
            "Classical yoga interpretation with modern computational precision",
            "Comprehensive yoga strength assessment and dissolution timing",
            "Natal yoga background influence on daily calculations"
        ]
    
    def validate_kundali_data(self) -> bool:
        """Validate kundali data for Layer 7 requirements."""
        if not self.kundali:
            self.logger.error("No kundali data provided")
            return False
        
        # Check for required birth details
        if not self.kundali.birth_details:
            self.logger.error("Birth details required for yoga calculations")
            return False
        
        # Check for required planetary positions
        if not self.kundali.planetary_positions:
            self.logger.error("Planetary positions required for yoga analysis")
            return False
        
        # Check for essential planets for yoga detection
        essential_planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'lagna']
        missing_planets = []
        
        for planet in essential_planets:
            if planet not in self.kundali.planetary_positions:
                missing_planets.append(planet)
        
        if missing_planets:
            self.logger.error(f"Missing essential positions for yoga analysis: {missing_planets}")
            return False
        
        return True
    
    def get_detailed_yoga_analysis(self, date: datetime) -> Dict[str, Any]:
        """
        Get detailed yoga analysis for a specific date.
        
        Args:
            date: Date for analysis
            
        Returns:
            Comprehensive yoga analysis dictionary
        """
        try:
            return self._yoga_detector.get_yoga_analysis_summary(date)
            
        except Exception as e:
            self.logger.error(f"Error getting detailed yoga analysis: {e}")
            return {'error': str(e)}
    
    def get_yoga_recommendations(self, date: datetime) -> List[str]:
        """
        Get yoga-based recommendations for a specific date.
        
        Args:
            date: Date for recommendations
            
        Returns:
            List of recommendations based on active yogas
        """
        try:
            yoga_analysis = self._yoga_detector.get_yoga_analysis_summary(date)
            return yoga_analysis.get('recommendations', [])
            
        except Exception as e:
            self.logger.error(f"Error getting yoga recommendations: {e}")
            return ["General period - maintain balance and positive attitude"]