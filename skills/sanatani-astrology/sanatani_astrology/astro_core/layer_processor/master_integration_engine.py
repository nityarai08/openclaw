"""
Master Integration Engine for World-Class Astrological Accuracy

This module provides the ultimate integration of all astrological factors
with dynamic weighting, cross-validation, and expert-level synthesis
for the world's most accurate kundali favorability calculations.
"""

import math
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..core.data_models import KundaliData
from .shadbala_calculator import ShadbalaCalculator
from .ashtakavarga_analyzer import AshtakavargaAnalyzer
from .yoga_detection_system import YogaDetectionSystem
from .divisional_chart_analyzer import DivisionalChartAnalyzer
from .dasha_system_analyzer import DashaSystemAnalyzer
from .enhanced_transit_analyzer import EnhancedTransitAnalyzer


class MasterIntegrationEngine:
    """
    Master integration engine for world-class astrological accuracy.
    
    Combines all astrological factors with expert-level synthesis:
    - Dynamic layer weighting based on chart strength
    - Cross-validation between different systems
    - Shadbala-weighted planetary influences
    - Comprehensive yoga and dasha integration
    - Expert-level conflict resolution
    """
    
    def __init__(self, kundali_data: KundaliData):
        """Initialize master integration engine."""
        self.kundali_data = kundali_data
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize all analyzers
        self._shadbala_calc = ShadbalaCalculator(
kundali_data)
        self._ashtakavarga_analyzer = AshtakavargaAnalyzer(kundali_data)
        self._yoga_detector = YogaDetectionSystem(kundali_data)
        self._divisional_analyzer = DivisionalChartAnalyzer(kundali_data)
        self._dasha_analyzer = DashaSystemAnalyzer(kundali_data)
        self._transit_analyzer = EnhancedTransitAnalyzer(kundali_data)
        
        # Calculate chart strength profile for dynamic weighting
        self._chart_strength_profile = self._calculate_chart_strength_profile()
        
        # Expert-level integration weights (dynamically adjusted)
        self._base_integration_weights = {
            'shadbala_strength': 0.25,      # Planetary strength foundation
            'yoga_formations': 0.20,        # Yoga combinations
            'dasha_periods': 0.20,          # Time period analysis
            'divisional_strength': 0.15,    # Divisional chart analysis
            'ashtakavarga_points': 0.10,    # Ashtakavarga strength
            'transit_effects': 0.10         # Current transit influences
        }
    
    def calculate_master_favorability(self, date: datetime) -> Dict[str, Any]:
        """
        Calculate master favorability with world-class accuracy.
        
        Args:
            date: Date for calculation
            
        Returns:
            Comprehensive favorability analysis with confidence metrics
        """
        try:
            # Calculate all component strengths
            shadbala_strength = self._calculate_shadbala_strength(date)
            yoga_strength = self._calculate_yoga_strength(date)
            dasha_strength = self._calculate_dasha_strength(date)
            divisional_strength = self._calculate_divisional_strength(date)
            ashtakavarga_strength = self._calculate_ashtakavarga_strength(date)
            transit_strength = self._calculate_transit_strength(date)
            
            # Apply dynamic weighting based on chart strength
            dynamic_weights = self._calculate_dynamic_weights(date)
            
            # Calculate weighted favorability
            weighted_favorability = (
                shadbala_strength * dynamic_weights['shadbala_strength'] +
                yoga_strength * dynamic_weights['yoga_formations'] +
                dasha_strength * dynamic_weights['dasha_periods'] +
                divisional_strength * dynamic_weights['divisional_strength'] +
                ashtakavarga_strength * dynamic_weights['ashtakavarga_points'] +
                transit_strength * dynamic_weights['transit_effects']
            )
            
            # Cross-validation and conflict resolution
            validated_score = self._cross_validate_and_resolve(
                weighted_favorability, date, {
                    'shadbala': shadbala_strength,
                    'yoga': yoga_strength,
                    'dasha': dasha_strength,
                    'divisional': divisional_strength,
                    'ashtakavarga': ashtakavarga_strength,
                    'transit': transit_strength
                }
            )
            
            # Calculate confidence metrics
            confidence_metrics = self._calculate_confidence_metrics(date, {
                'shadbala': shadbala_strength,
                'yoga': yoga_strength,
                'dasha': dasha_strength,
                'divisional': divisional_strength,
                'ashtakavarga': ashtakavarga_strength,
                'transit': transit_strength
            })
            
            return {
                'master_favorability': validated_score,
                'confidence_level': confidence_metrics['overall_confidence'],
                'component_strengths': {
                    'shadbala_strength': shadbala_strength,
                    'yoga_strength': yoga_strength,
                    'dasha_strength': dasha_strength,
                    'divisional_strength': divisional_strength,
                    'ashtakavarga_strength': ashtakavarga_strength,
                    'transit_strength': transit_strength
                },
                'dynamic_weights': dynamic_weights,
                'confidence_metrics': confidence_metrics,
                'expert_recommendations': self._generate_expert_recommendations(
                    validated_score, date, confidence_metrics
                )
            }
            
        except Exception as e:
            self.logger.error(f"Error in master favorability calculation: {e}")
            return {
                'master_favorability': 0.5,
                'confidence_level': 0.3,
                'error': str(e)
            }
    
    def _calculate_chart_strength_profile(self) -> Dict[str, float]:
        """Calculate overall chart strength profile for dynamic weighting."""
        try:
            profile = {}
            
            # Analyze planetary strengths
            planetary_strengths = []
            for planet in ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']:
                if planet in self.kundali_data.planetary_positions:
                    # Use a reference date for natal strength
                    birth_date = datetime.combine(
                        self.kundali_data.birth_details.date,
                        self.kundali_data.birth_details.time
                    )
                    strength = self._shadbala_calc.calculate_total_shadbala(planet, birth_date)
                    planetary_strengths.append(strength)
            
            profile['average_planetary_strength'] = sum(planetary_strengths) / len(planetary_strengths) if planetary_strengths else 0.5
            
            # Analyze yoga strength
            birth_date = datetime.combine(
                self.kundali_data.birth_details.date,
                self.kundali_data.birth_details.time
            )
            yoga_analysis = self._yoga_detector.get_yoga_analysis_summary(birth_date)
            profile['yoga_strength'] = yoga_analysis.get('yoga_favorability', 0.5)
            
            # Analyze divisional chart strength
            divisional_analysis = self._divisional_analyzer.get_comprehensive_divisional_analysis(birth_date)
            life_area_strengths = divisional_analysis.get('life_area_strengths', {})
            profile['divisional_strength'] = sum(life_area_strengths.values()) / len(life_area_strengths) if life_area_strengths else 0.5
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Error calculating chart strength profile: {e}")
            return {'average_planetary_strength': 0.5, 'yoga_strength': 0.5, 'divisional_strength': 0.5}
    
    def _calculate_shadbala_strength(self, date: datetime) -> float:
        """Calculate comprehensive Shadbala-based strength."""
        try:
            planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
            total_strength = 0.0
            
            for planet in planets:
                planet_strength = self._shadbala_calc.calculate_total_shadbala(planet, date)
                total_strength += planet_strength
            
            return total_strength / len(planets)
            
        except Exception as e:
            self.logger.error(f"Error calculating Shadbala strength: {e}")
            return 0.5
    
    def _calculate_yoga_strength(self, date: datetime) -> float:
        """Calculate yoga-based strength."""
        try:
            return self._yoga_detector.calculate_yoga_favorability(date)
        except Exception as e:
            self.logger.error(f"Error calculating yoga strength: {e}")
            return 0.5
    
    def _calculate_dasha_strength(self, date: datetime) -> float:
        """Calculate dasha-based strength."""
        try:
            return self._dasha_analyzer.calculate_dasha_influence(date)
        except Exception as e:
            self.logger.error(f"Error calculating dasha strength: {e}")
            return 0.5
    
    def _calculate_divisional_strength(self, date: datetime) -> float:
        """Calculate divisional chart strength."""
        try:
            planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
            total_strength = 0.0
            
            for planet in planets:
                planet_strength = self._divisional_analyzer.calculate_divisional_strength(
                    planet, date, 'general'
                )
                total_strength += planet_strength
            
            return total_strength / len(planets)
            
        except Exception as e:
            self.logger.error(f"Error calculating divisional strength: {e}")
            return 0.5
    
    def _calculate_ashtakavarga_strength(self, date: datetime) -> float:
        """Calculate Ashtakavarga-based strength."""
        try:
            return self._ashtakavarga_analyzer.calculate_sarvashtakavarga_strength(date)
        except Exception as e:
            self.logger.error(f"Error calculating Ashtakavarga strength: {e}")
            return 0.5
    
    def _calculate_transit_strength(self, date: datetime) -> float:
        """Calculate current transit strength."""
        try:
            return self._transit_analyzer.calculate_transit_favorability(date)
        except Exception as e:
            self.logger.error(f"Error calculating transit strength: {e}")
            return 0.5
    
    def _calculate_dynamic_weights(self, date: datetime) -> Dict[str, float]:
        """Calculate dynamic weights based on chart strength and current conditions."""
        try:
            dynamic_weights = self._base_integration_weights.copy()
            
            # Adjust weights based on chart strength profile
            if self._chart_strength_profile['average_planetary_strength'] > 0.7:
                dynamic_weights['shadbala_strength'] *= 1.2
            elif self._chart_strength_profile['average_planetary_strength'] < 0.4:
                dynamic_weights['shadbala_strength'] *= 0.8
            
            if self._chart_strength_profile['yoga_strength'] > 0.7:
                dynamic_weights['yoga_formations'] *= 1.2
            elif self._chart_strength_profile['yoga_strength'] < 0.4:
                dynamic_weights['yoga_formations'] *= 0.8
            
            # Normalize weights to sum to 1.0
            total_weight = sum(dynamic_weights.values())
            for key in dynamic_weights:
                dynamic_weights[key] /= total_weight
            
            return dynamic_weights
            
        except Exception as e:
            self.logger.error(f"Error calculating dynamic weights: {e}")
            return self._base_integration_weights
    
    def _cross_validate_and_resolve(self, initial_score: float, date: datetime, 
                                   component_scores: Dict[str, float]) -> float:
        """Cross-validate and resolve conflicts between different systems."""
        try:
            # Check for major disagreements between systems
            scores = list(component_scores.values())
            score_range = max(scores) - min(scores)
            
            if score_range > 0.4:  # Major disagreement
                # Apply conflict resolution
                # Weight more reliable systems higher
                reliable_systems = ['shadbala', 'dasha', 'yoga']
                reliable_scores = [component_scores[sys] for sys in reliable_systems if sys in component_scores]
                
                if reliable_scores:
                    resolved_score = sum(reliable_scores) / len(reliable_scores)
                    # Blend with initial score
                    return (initial_score * 0.6) + (resolved_score * 0.4)
            
            return initial_score
            
        except Exception as e:
            self.logger.error(f"Error in cross-validation: {e}")
            return initial_score
    
    def _calculate_confidence_metrics(self, date: datetime, 
                                    component_scores: Dict[str, float]) -> Dict[str, float]:
        """Calculate confidence metrics for the analysis."""
        try:
            scores = list(component_scores.values())
            
            # Calculate agreement between systems
            mean_score = sum(scores) / len(scores)
            variance = sum((score - mean_score) ** 2 for score in scores) / len(scores)
            agreement_confidence = max(0.0, 1.0 - (variance * 4))  # Higher variance = lower confidence
            
            # Calculate data completeness confidence
            required_data = ['planetary_positions', 'birth_details']
            optional_data = ['divisional_charts', 'panchanga', 'yogas_and_doshas']
            
            completeness_score = 1.0  # Start with full confidence
            for data in required_data:
                if not hasattr(self.kundali_data, data) or not getattr(self.kundali_data, data):
                    completeness_score *= 0.5  # Significant reduction for missing required data
            
            for data in optional_data:
                if not hasattr(self.kundali_data, data) or not getattr(self.kundali_data, data):
                    completeness_score *= 0.9  # Minor reduction for missing optional data
            
            # Overall confidence
            overall_confidence = (agreement_confidence * 0.6) + (completeness_score * 0.4)
            
            return {
                'agreement_confidence': agreement_confidence,
                'data_completeness_confidence': completeness_score,
                'overall_confidence': overall_confidence,
                'score_variance': variance,
                'component_agreement': 'High' if variance < 0.1 else 'Medium' if variance < 0.25 else 'Low'
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence metrics: {e}")
            return {'overall_confidence': 0.5, 'agreement_confidence': 0.5, 'data_completeness_confidence': 0.5}
    
    def _generate_expert_recommendations(self, favorability_score: float, date: datetime, 
                                       confidence_metrics: Dict[str, float]) -> List[str]:
        """Generate expert-level recommendations based on analysis."""
        try:
            recommendations = []
            
            # Score-based recommendations
            if favorability_score >= 0.8:
                recommendations.append("Highly favorable period - excellent time for important activities")
            elif favorability_score >= 0.6:
                recommendations.append("Generally favorable period - good for most activities")
            elif favorability_score >= 0.4:
                recommendations.append("Mixed period - exercise caution and choose activities carefully")
            else:
                recommendations.append("Challenging period - focus on patience and avoid major decisions")
            
            # Confidence-based recommendations
            if confidence_metrics['overall_confidence'] < 0.6:
                recommendations.append("Analysis confidence is moderate - consider consulting additional sources")
            
            if confidence_metrics['component_agreement'] == 'Low':
                recommendations.append("Mixed signals from different astrological systems - proceed with extra caution")
            
            # Time-specific recommendations
            hour = date.hour
            if 4 <= hour <= 6:
                recommendations.append("Brahma Muhurta period - excellent for spiritual practices")
            elif 11 <= hour <= 13:
                recommendations.append("Midday period - good for worldly activities and business")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["General period - maintain balance and positive attitude"]