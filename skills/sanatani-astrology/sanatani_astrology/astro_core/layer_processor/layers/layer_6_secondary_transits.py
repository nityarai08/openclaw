"""
Layer 6: Enhanced Secondary Transits with Traditional Rules (55% Accuracy)

This layer calculates favorability based on comprehensive transit analysis including
traditional Gochara rules, Sade Sati effects, Jupiter transits, eclipse impacts,
faster-moving planet analysis, and classical Vedic transit principles.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..base_layer import LayerProcessor
from ...core.data_models import KundaliData, PlanetaryPosition
from ..enhanced_transit_analyzer import EnhancedTransitAnalyzer


class Layer6_SecondaryTransits(LayerProcessor):
    """
    Layer 6: Enhanced Secondary Transits processor with 55% accuracy.
    
    Calculates favorability based on:
    - Traditional Gochara rules from Moon and Lagna
    - Comprehensive Sade Sati analysis with phase detection
    - Jupiter's 12-year cycle effects and house-wise analysis
    - Eclipse effects and nodal transit impacts
    - Faster-moving planet transits (Mars, Venus, Mercury)
    - Classical Vedic transit principles with modern precision
    """
    
    def __init__(self, layer_id: int, accuracy: float, kundali_data: KundaliData):
        """Initialize Layer 6 processor."""
        super().__init__(layer_id, accuracy, kundali_data)
        
        # Initialize enhanced transit analyzer
        self._transit_analyzer = EnhancedTransitAnalyzer(kundali_data)
        
        # Cache birth data
        if kundali_data.birth_details:
            self._birth_date = kundali_data.birth_details.date
            self._birth_time = kundali_data.birth_details.time
        else:
            raise ValueError("Birth details required for Layer 6 calculations")
        
        # Cache natal planetary positions
        self._natal_positions = kundali_data.planetary_positions
        
        # Factor weights for final score calculation
        self._factor_weights = {
            'transit_favorability': 0.50,  # Primary transit analysis
            'fast_planet_transits': 0.25,  # Mars, Venus, Mercury
            'aspect_formations': 0.15,     # Current aspect patterns
            'cycle_analysis': 0.10         # Multi-planetary cycles
        }
    
    def calculate_daily_score(self, date: datetime) -> float:
        """
        Calculate enhanced secondary transits favorability score for specific date.
        
        Args:
            date: Date for calculation
            
        Returns:
            Favorability score between 0.0 and 1.0
        """
        try:
            # Calculate primary transit favorability
            transit_favorability = self._transit_analyzer.calculate_transit_favorability(date)
            
            # Calculate fast-moving planet effects
            fast_planet_score = self._calculate_fast_planet_transits(date)
            
            # Calculate current aspect formations
            aspect_score = self._calculate_aspect_formations(date)
            
            # Calculate multi-planetary cycle effects
            cycle_score = self._calculate_cycle_analysis(date)
            
            # Combine all factors with weights
            total_score = (
                transit_favorability * self._factor_weights['transit_favorability'] +
                fast_planet_score * self._factor_weights['fast_planet_transits'] +
                aspect_score * self._factor_weights['aspect_formations'] +
                cycle_score * self._factor_weights['cycle_analysis']
            )
            
            # Ensure score is within valid range
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate enhanced transits score for {date}: {e}")
            raise
    
    def _calculate_fast_planet_transits(self, date: datetime) -> float:
        """Calculate effects of faster-moving planets (Mars, Venus, Mercury)."""
        try:
            # Get current positions
            current_positions = self._get_current_positions(date)
            if not current_positions:
                return 0.5
            
            fast_planets = ['mars', 'venus', 'mercury']
            total_score = 0.0
            planet_count = 0
            
            for planet in fast_planets:
                if planet in current_positions and planet in self._natal_positions:
                    planet_score = self._calculate_individual_planet_transit(
                        planet, current_positions[planet], date
                    )
                    
                    # Weight planets differently
                    if planet == 'mars':
                        weight = 1.2  # Mars has strong effects
                    elif planet == 'venus':
                        weight = 1.0  # Venus moderate effects
                    else:  # mercury
                        weight = 0.8  # Mercury lighter effects
                    
                    total_score += planet_score * weight
                    planet_count += weight
            
            if planet_count > 0:
                return total_score / planet_count
            else:
                return 0.5
                
        except Exception as e:
            self.logger.error(f"Error calculating fast planet transits: {e}")
            return 0.5
    
    def _calculate_individual_planet_transit(self, planet: str, current_pos: PlanetaryPosition, date: datetime) -> float:
        """Calculate individual planet transit effects."""
        try:
            if 'moon' not in self._natal_positions:
                return 0.5
            
            natal_moon_rasi = self._natal_positions['moon'].rasi
            current_rasi = current_pos.rasi
            
            # Calculate house from Moon
            house_from_moon = ((current_rasi - natal_moon_rasi) % 12) + 1
            
            # Planet-specific transit effects from Moon
            transit_effects = {
                'mars': {
                    1: 0.5, 2: 0.4, 3: 0.8, 4: 0.3, 5: 0.6, 6: 0.9,
                    7: 0.5, 8: 0.2, 9: 0.7, 10: 0.6, 11: 0.8, 12: 0.3
                },
                'venus': {
                    1: 0.8, 2: 0.9, 3: 0.7, 4: 0.8, 5: 0.9, 6: 0.5,
                    7: 0.6, 8: 0.4, 9: 0.8, 10: 0.7, 11: 0.9, 12: 0.9
                },
                'mercury': {
                    1: 0.7, 2: 0.8, 3: 0.6, 4: 0.9, 5: 0.7, 6: 0.8,
                    7: 0.5, 8: 0.4, 9: 0.6, 10: 0.8, 11: 0.9, 12: 0.5
                }
            }
            
            base_score = transit_effects.get(planet, {}).get(house_from_moon, 0.5)
            
            # Apply retrograde modifier
            if current_pos.retrograde:
                if planet == 'mars':
                    base_score *= 0.8  # Mars retrograde is challenging
                elif planet == 'venus':
                    base_score *= 1.1  # Venus retrograde can be beneficial for introspection
                else:  # mercury
                    base_score *= 0.9  # Mercury retrograde is mildly challenging
            
            # Apply dignity modifier
            dignity_modifier = self._get_dignity_modifier(planet, current_rasi)
            base_score *= dignity_modifier
            
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating {planet} transit: {e}")
            return 0.5
    
    def _calculate_aspect_formations(self, date: datetime) -> float:
        """Calculate current aspect formations between planets."""
        try:
            current_positions = self._get_current_positions(date)
            if not current_positions:
                return 0.5
            
            aspect_score = 0.5  # Base neutral score
            aspect_count = 0
            
            planets = list(current_positions.keys())
            
            # Check aspects between all planet pairs
            for i, planet1 in enumerate(planets):
                for planet2 in planets[i+1:]:
                    if planet1 in current_positions and planet2 in current_positions:
                        pos1 = current_positions[planet1]
                        pos2 = current_positions[planet2]
                        
                        aspect_strength = self._calculate_aspect_strength(
                            planet1, planet2, pos1, pos2
                        )
                        
                        if aspect_strength != 0:
                            aspect_score += aspect_strength
                            aspect_count += 1
            
            # Normalize score
            if aspect_count > 0:
                aspect_score = aspect_score / (aspect_count + 1)  # +1 for base score
            
            return max(0.0, min(1.0, aspect_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating aspect formations: {e}")
            return 0.5
    
    def _calculate_cycle_analysis(self, date: datetime) -> float:
        """Calculate multi-planetary cycle effects."""
        try:
            current_positions = self._get_current_positions(date)
            if not current_positions:
                return 0.5
            
            cycle_score = 0.5
            
            # Analyze planetary cycles and their interactions
            # This is a simplified analysis - in practice, you would analyze
            # complex planetary cycles and their mutual relationships
            
            # Check for planets in similar phases of their cycles
            cycle_harmony = self._calculate_cycle_harmony(current_positions)
            cycle_score += (cycle_harmony - 0.5) * 0.3
            
            # Check for planetary returns (planets returning to natal positions)
            return_effects = self._calculate_return_effects(current_positions, date)
            cycle_score += (return_effects - 0.5) * 0.2
            
            return max(0.0, min(1.0, cycle_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating cycle analysis: {e}")
            return 0.5
    
    def _get_current_positions(self, date: datetime) -> Dict[str, PlanetaryPosition]:
        """Get current planetary positions."""
        try:
            return self._transit_analyzer._get_current_positions(date)
        except Exception as e:
            self.logger.error(f"Error getting current positions: {e}")
            return {}
    
    def _get_dignity_modifier(self, planet: str, rasi: int) -> float:
        """Get dignity modifier for a planet in a sign."""
        try:
            # Simplified dignity calculation
            dignity_modifiers = {
                'mars': {0: 1.2, 7: 1.1, 9: 1.3, 3: 0.7},  # Aries, Scorpio, Capricorn, Cancer
                'venus': {1: 1.2, 6: 1.1, 11: 1.3, 5: 0.7},  # Taurus, Libra, Pisces, Virgo
                'mercury': {2: 1.2, 5: 1.3, 11: 0.7}  # Gemini, Virgo, Pisces
            }
            
            return dignity_modifiers.get(planet, {}).get(rasi, 1.0)
            
        except Exception:
            return 1.0
    
    def _calculate_aspect_strength(self, planet1: str, planet2: str, 
                                 pos1: PlanetaryPosition, pos2: PlanetaryPosition) -> float:
        """Calculate aspect strength between two planets."""
        try:
            angular_diff = abs(pos1.longitude - pos2.longitude)
            if angular_diff > 180:
                angular_diff = 360 - angular_diff
            
            # Major aspects with their strengths
            aspects = {
                0: 0.8,    # Conjunction
                60: 0.6,   # Sextile
                90: -0.3,  # Square (challenging)
                120: 0.7,  # Trine
                180: -0.2  # Opposition (challenging)
            }
            
            orb_tolerance = 8  # degrees
            
            for aspect_angle, strength in aspects.items():
                if abs(angular_diff - aspect_angle) <= orb_tolerance:
                    # Apply planetary combination modifier
                    combination_modifier = self._get_combination_modifier(planet1, planet2)
                    return strength * combination_modifier
            
            return 0.0  # No significant aspect
            
        except Exception:
            return 0.0
    
    def _get_combination_modifier(self, planet1: str, planet2: str) -> float:
        """Get modifier for planetary combinations."""
        try:
            # Benefic combinations
            benefic_pairs = [
                ('jupiter', 'venus'), ('jupiter', 'mercury'), ('venus', 'mercury'),
                ('sun', 'jupiter'), ('moon', 'jupiter'), ('moon', 'venus')
            ]
            
            # Challenging combinations
            challenging_pairs = [
                ('mars', 'saturn'), ('sun', 'saturn'), ('mars', 'rahu'),
                ('saturn', 'rahu'), ('sun', 'rahu'), ('moon', 'rahu')
            ]
            
            pair = tuple(sorted([planet1, planet2]))
            
            if pair in benefic_pairs:
                return 1.2  # Enhance benefic combinations
            elif pair in challenging_pairs:
                return 0.8  # Reduce challenging combinations
            else:
                return 1.0  # Neutral
                
        except Exception:
            return 1.0
    
    def _calculate_cycle_harmony(self, current_positions: Dict[str, PlanetaryPosition]) -> float:
        """Calculate harmony between planetary cycles."""
        try:
            # This is a simplified calculation
            # In practice, you would analyze the phase relationships
            # between different planetary cycles
            
            harmony_score = 0.5
            
            # Check if multiple planets are in similar cycle phases
            # (This is a placeholder for more complex cycle analysis)
            
            return harmony_score
            
        except Exception:
            return 0.5
    
    def _calculate_return_effects(self, current_positions: Dict[str, PlanetaryPosition], date: datetime) -> float:
        """Calculate effects of planetary returns."""
        try:
            return_score = 0.5
            
            # Check for planets returning to natal positions
            for planet, current_pos in current_positions.items():
                if planet in self._natal_positions:
                    natal_pos = self._natal_positions[planet]
                    
                    # Check if planet is close to natal position
                    angular_diff = abs(current_pos.longitude - natal_pos.longitude)
                    if angular_diff > 180:
                        angular_diff = 360 - angular_diff
                    
                    if angular_diff <= 5:  # Within 5 degrees of return
                        # Planetary return effect
                        if planet in ['sun']:
                            return_score += 0.1  # Solar return (birthday)
                        elif planet in ['mars']:
                            return_score += 0.05  # Mars return
                        elif planet in ['venus', 'mercury']:
                            return_score += 0.03  # Venus/Mercury return
            
            return max(0.0, min(1.0, return_score))
            
        except Exception:
            return 0.5
    
    def _get_contributing_factors(self, date: datetime) -> Dict[str, float]:
        """Get detailed breakdown of contributing factors."""
        try:
            # Get comprehensive transit analysis
            transit_analysis = self._transit_analyzer.get_transit_analysis(date)
            
            factors = {
                'overall_transit_favorability': transit_analysis.get('overall_favorability', 0.5),
                'fast_planet_transits': self._calculate_fast_planet_transits(date),
                'aspect_formations': self._calculate_aspect_formations(date),
                'cycle_analysis': self._calculate_cycle_analysis(date)
            }
            
            # Add specific transit information
            gochara_analysis = transit_analysis.get('gochara_analysis', {})
            for planet, analysis in gochara_analysis.items():
                factors[f'{planet}_gochara_favorability'] = analysis.get('favorability', 0.5)
                factors[f'{planet}_house_from_moon'] = analysis.get('house_from_moon', 1)
            
            # Add Sade Sati information
            sade_sati = transit_analysis.get('sade_sati_status', {})
            factors['sade_sati_active'] = sade_sati.get('active', False)
            if sade_sati.get('active'):
                factors['sade_sati_phase'] = sade_sati.get('phase', 'Unknown')
            
            # Add Jupiter transit information
            jupiter_transit = transit_analysis.get('jupiter_transit', {})
            factors['jupiter_house_from_moon'] = jupiter_transit.get('house_from_moon', 1)
            factors['jupiter_favorability'] = jupiter_transit.get('favorability', 0.5)
            
            return factors
            
        except Exception:
            return {}
    
    def get_calculation_methodology(self) -> str:
        """Describe calculation methodology."""
        return (
            "Enhanced secondary transits with traditional Vedic rules (55% accuracy). "
            "Combines comprehensive transit favorability using Gochara principles (50%), "
            "faster-moving planet analysis for Mars, Venus, and Mercury (25%), "
            "current aspect formations between planets (15%), and multi-planetary "
            "cycle analysis (10%). Integrates traditional Sade Sati analysis, "
            "Jupiter's 12-year cycle effects, eclipse impacts, and classical "
            "Vedic transit principles with modern computational precision."
        )
    
    def get_layer_name(self) -> str:
        """Get layer name."""
        return "Enhanced Secondary Transits with Traditional Rules"
    
    def get_layer_description(self) -> str:
        """Get layer description."""
        return (
            "Comprehensive analysis of planetary transits using traditional Vedic "
            "principles including Gochara rules from Moon and Lagna, Sade Sati "
            "effects with phase analysis, Jupiter's 12-year cycle impacts, eclipse "
            "effects, and faster-moving planet transits. Combines classical Vedic "
            "transit wisdom with modern ephemeris precision for enhanced timing "
            "accuracy and daily favorability assessment."
        )
    
    def get_calculation_factors(self) -> List[str]:
        """Get list of calculation factors."""
        return [
            "Traditional Gochara rules from Moon and Lagna",
            "Comprehensive Sade Sati analysis with phase detection",
            "Jupiter's 12-year cycle effects and house-wise analysis",
            "Eclipse effects and nodal transit impacts",
            "Faster-moving planet transits (Mars, Venus, Mercury)",
            "Classical Vedic transit principles with modern precision",
            "Multi-planetary aspect formations and cycle harmony"
        ]
    
    def validate_kundali_data(self) -> bool:
        """Validate kundali data for Layer 6 requirements."""
        if not self.kundali:
            self.logger.error("No kundali data provided")
            return False
        
        # Check for required birth details
        if not self.kundali.birth_details:
            self.logger.error("Birth details required for transit calculations")
            return False
        
        # Check for required planetary positions
        if not self.kundali.planetary_positions:
            self.logger.error("Natal planetary positions required for transit comparison")
            return False
        
        # Check for essential planets
        essential_planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu']
        missing_planets = []
        
        for planet in essential_planets:
            if planet not in self.kundali.planetary_positions:
                missing_planets.append(planet)
        
        if missing_planets:
            self.logger.error(f"Missing essential positions for transit analysis: {missing_planets}")
            return False
        
        return True
    
    def get_detailed_transit_analysis(self, date: datetime) -> Dict[str, Any]:
        """
        Get detailed transit analysis for a specific date.
        
        Args:
            date: Date for analysis
            
        Returns:
            Comprehensive transit analysis dictionary
        """
        try:
            return self._transit_analyzer.get_transit_analysis(date)
            
        except Exception as e:
            self.logger.error(f"Error getting detailed transit analysis: {e}")
            return {'error': str(e)}
    
    def get_transit_recommendations(self, date: datetime) -> List[str]:
        """
        Get transit-based recommendations for a specific date.
        
        Args:
            date: Date for recommendations
            
        Returns:
            List of recommendations based on current transits
        """
        try:
            transit_analysis = self._transit_analyzer.get_transit_analysis(date)
            return transit_analysis.get('recommendations', [])
            
        except Exception as e:
            self.logger.error(f"Error getting transit recommendations: {e}")
            return ["General period - maintain balance and positive attitude"]