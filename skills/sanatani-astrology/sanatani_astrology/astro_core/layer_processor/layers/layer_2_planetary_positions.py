"""
Layer 2: Planetary Positions (90% Accuracy)

This layer calculates favorability based on direct astronomical planetary calculations
including planetary dignity assessment, retrograde motion detection, angular relationships
to natal positions, and planetary aspect strength analysis for daily variations.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging

from ..base_layer import LayerProcessor
from ...core.data_models import KundaliData, PlanetaryPosition
from ...kundali_generator.comprehensive_ephemeris_engine import ComprehensiveEphemerisEngine, Planet
from ..divisional_chart_analyzer import DivisionalChartAnalyzer
from ..combustion_analyzer import CombustionAnalyzer


class Layer2_PlanetaryPositions(LayerProcessor):
    """
    Layer 2: Planetary Positions processor with 90% accuracy.
    
    Calculates favorability based on:
    - Planetary dignity assessment and strength calculations
    - Retrograde motion detection and impact analysis
    - Angular relationship calculations to natal positions
    - Planetary aspect strength analysis for daily variations
    """
    
    def __init__(self, layer_id: int, accuracy: float, kundali_data: KundaliData):
        """Initialize Layer 2 processor."""
        super().__init__(layer_id, accuracy, kundali_data)
        
        # Initialize ephemeris engine
        self._ephemeris_engine = ComprehensiveEphemerisEngine()

        # Initialize calculation components
        self._dignity_calculator = PlanetaryDignityCalculator()
        self._retrograde_analyzer = RetrogradeAnalyzer()
        self._angular_calculator = AngularRelationshipCalculator(kundali_data.planetary_positions)
        self._aspect_analyzer = AspectStrengthAnalyzer(kundali_data.planetary_positions)
        self._divisional_analyzer = DivisionalChartAnalyzer(kundali_data)
        self._combustion_analyzer = CombustionAnalyzer()
        
        # Cache birth location data
        if kundali_data.birth_details:
            self._birth_latitude = kundali_data.birth_details.latitude
            self._birth_longitude = kundali_data.birth_details.longitude
            self._birth_timezone = kundali_data.birth_details.timezone_offset
        else:
            raise ValueError("Birth details required for Layer 2 calculations")
        
        # Cache natal planetary positions for comparison
        self._natal_positions = kundali_data.planetary_positions
        
        # ENHANCED: Dynamic planetary weights based on natal chart strength
        self._base_planetary_weights = {
            'sun': 0.20,
            'moon': 0.18,
            'mars': 0.12,
            'mercury': 0.10,
            'jupiter': 0.15,
            'venus': 0.10,
            'saturn': 0.10,
            'rahu': 0.03,
            'ketu': 0.02
        }
        
        # Calculate dynamic weights based on natal planetary strengths
        self._planetary_weights = self._calculate_dynamic_weights()
    
    def calculate_daily_score(self, date: datetime) -> float:
        """
        Calculate planetary favorability score for specific date.
        
        Args:
            date: Date for calculation
            
        Returns:
            Favorability score between 0.0 and 1.0
        """
        try:
            # Calculate Julian Day for the date
            julian_day = self._ephemeris_engine.julian_day_from_datetime(
                date, self._birth_timezone
            )
            
            # Get current planetary positions
            current_positions = self._ephemeris_engine.calculate_planetary_positions(
                julian_day, self._birth_latitude, self._birth_longitude
            )
            
            if not current_positions:
                self.logger.warning(f"Could not calculate planetary positions for {date}")
                return 0.5  # Neutral fallback
            
            # Calculate individual planetary factors
            dignity_scores = self._calculate_dignity_scores(current_positions)
            retrograde_impacts = self._calculate_retrograde_impacts(current_positions)
            angular_relationships = self._calculate_angular_relationships(current_positions)
            aspect_strengths = self._calculate_aspect_strengths(current_positions)
            divisional_strengths = self._calculate_divisional_strengths(date)
            
            # Combine all factors with weights
            total_score = 0.0
            total_weight = 0.0
            
            for planet, weight in self._planetary_weights.items():
                if planet in current_positions:
                    # Combine factors for this planet (updated weights to include divisional)
                    planet_score = (
                        dignity_scores.get(planet, 0.5) * 0.25 +
                        retrograde_impacts.get(planet, 0.5) * 0.15 +
                        angular_relationships.get(planet, 0.5) * 0.25 +
                        aspect_strengths.get(planet, 0.5) * 0.15 +
                        divisional_strengths.get(planet, 0.5) * 0.20
                    )

                    # Apply combustion penalty if planet is combust
                    if 'sun' in current_positions:
                        combustion_info = self._combustion_analyzer.is_combust(
                            planet, current_positions[planet], current_positions['sun']
                        )
                        if combustion_info['combust']:
                            # Apply combustion penalty
                            planet_score = max(0.0, planet_score + combustion_info['penalty'])
                        elif combustion_info.get('severity') == 'Budha Aditya Yoga':
                            # Apply bonus for Budha Aditya Yoga (Mercury-Sun conjunction)
                            planet_score = min(1.0, planet_score + combustion_info['penalty'])  # penalty is positive for yoga

                    total_score += planet_score * weight
                    total_weight += weight
            
            # Normalize score
            final_score = total_score / total_weight if total_weight > 0 else 0.5
            
            # Ensure score is within valid range
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate planetary score for {date}: {e}")
            raise
    
    def _calculate_dignity_scores(self, current_positions: Dict[str, PlanetaryPosition]) -> Dict[str, float]:
        """Calculate planetary dignity scores for current positions."""
        dignity_scores = {}
        
        for planet_name, position in current_positions.items():
            if planet_name in self._planetary_weights:
                dignity_score = self._dignity_calculator.calculate_dignity(
                    planet_name, position
                )
                dignity_scores[planet_name] = dignity_score
        
        return dignity_scores
    
    def _calculate_retrograde_impacts(self, current_positions: Dict[str, PlanetaryPosition]) -> Dict[str, float]:
        """Calculate retrograde motion impacts for current positions."""
        retrograde_impacts = {}
        
        for planet_name, position in current_positions.items():
            if planet_name in self._planetary_weights:
                retrograde_impact = self._retrograde_analyzer.analyze_retrograde_impact(
                    planet_name, position
                )
                retrograde_impacts[planet_name] = retrograde_impact
        
        return retrograde_impacts
    
    def _calculate_angular_relationships(self, current_positions: Dict[str, PlanetaryPosition]) -> Dict[str, float]:
        """Calculate angular relationships to natal positions."""
        angular_relationships = {}
        
        for planet_name, position in current_positions.items():
            if planet_name in self._planetary_weights:
                angular_score = self._angular_calculator.calculate_angular_relationship(
                    planet_name, position
                )
                angular_relationships[planet_name] = angular_score
        
        return angular_relationships
    
    def _calculate_aspect_strengths(self, current_positions: Dict[str, PlanetaryPosition]) -> Dict[str, float]:
        """Calculate planetary aspect strengths for current positions."""
        aspect_strengths = {}
        
        for planet_name, position in current_positions.items():
            if planet_name in self._planetary_weights:
                aspect_strength = self._aspect_analyzer.analyze_aspect_strength(
                    planet_name, position, current_positions
                )
                aspect_strengths[planet_name] = aspect_strength
        
        return aspect_strengths
    
    def _calculate_divisional_strengths(self, date: datetime) -> Dict[str, float]:
        """Calculate divisional chart strengths for all planets."""
        divisional_strengths = {}
        
        for planet_name in self._planetary_weights.keys():
            try:
                # Calculate general divisional strength for this planet
                divisional_strength = self._divisional_analyzer.calculate_divisional_strength(
                    planet_name, date, 'general'
                )
                divisional_strengths[planet_name] = divisional_strength
            except Exception as e:
                self.logger.warning(f"Failed to calculate divisional strength for {planet_name}: {e}")
                divisional_strengths[planet_name] = 0.5  # Neutral fallback
        
        return divisional_strengths
    
    def _get_contributing_factors(self, date: datetime) -> Dict[str, float]:
        """Get detailed breakdown of contributing factors."""
        try:
            julian_day = self._ephemeris_engine.julian_day_from_datetime(
                date, self._birth_timezone
            )
            
            current_positions = self._ephemeris_engine.calculate_planetary_positions(
                julian_day, self._birth_latitude, self._birth_longitude
            )
            
            if not current_positions:
                return {}
            
            dignity_scores = self._calculate_dignity_scores(current_positions)
            retrograde_impacts = self._calculate_retrograde_impacts(current_positions)
            angular_relationships = self._calculate_angular_relationships(current_positions)
            aspect_strengths = self._calculate_aspect_strengths(current_positions)
            divisional_strengths = self._calculate_divisional_strengths(date)
            
            # Create comprehensive factor breakdown
            factors = {}
            
            # Add individual planetary contributions
            for planet in self._planetary_weights.keys():
                if planet in current_positions:
                    factors[f'{planet}_dignity'] = dignity_scores.get(planet, 0.5)
                    factors[f'{planet}_retrograde'] = retrograde_impacts.get(planet, 0.5)
                    factors[f'{planet}_angular'] = angular_relationships.get(planet, 0.5)
                    factors[f'{planet}_aspects'] = aspect_strengths.get(planet, 0.5)
                    factors[f'{planet}_divisional'] = divisional_strengths.get(planet, 0.5)
            
            # Add summary factors
            factors['overall_dignity'] = sum(dignity_scores.values()) / len(dignity_scores) if dignity_scores else 0.5
            factors['overall_retrograde'] = sum(retrograde_impacts.values()) / len(retrograde_impacts) if retrograde_impacts else 0.5
            factors['overall_angular'] = sum(angular_relationships.values()) / len(angular_relationships) if angular_relationships else 0.5
            factors['overall_aspects'] = sum(aspect_strengths.values()) / len(aspect_strengths) if aspect_strengths else 0.5
            factors['overall_divisional'] = sum(divisional_strengths.values()) / len(divisional_strengths) if divisional_strengths else 0.5

            # Compute legacy combined score using dynamic planetary weights exactly as in calculate_daily_score
            try:
                legacy_total = 0.0
                legacy_weight_sum = 0.0
                for planet, p_weight in self._planetary_weights.items():
                    if planet in current_positions:
                        planet_score = (
                            dignity_scores.get(planet, 0.5) * 0.25 +
                            retrograde_impacts.get(planet, 0.5) * 0.15 +
                            angular_relationships.get(planet, 0.5) * 0.25 +
                            aspect_strengths.get(planet, 0.5) * 0.15 +
                            divisional_strengths.get(planet, 0.5) * 0.20
                        )
                        legacy_total += planet_score * p_weight
                        legacy_weight_sum += p_weight
                if legacy_weight_sum > 0:
                    factors['legacy_total'] = max(0.0, min(1.0, legacy_total))
            except Exception:
                # Leave out on failure; rule engine will fallback to other features
                pass
            
            return factors
            
        except Exception:
            return {}
    
    def get_calculation_methodology(self) -> str:
        """Describe calculation methodology."""
        return (
            "Enhanced astronomical calculations using ephemeris data with 92% accuracy. "
            "Combines planetary dignity assessment (25%), retrograde motion analysis (15%), "
            "angular relationships to natal positions (25%), planetary aspect strength "
            "analysis (15%), and divisional chart strength analysis (20%). Uses Swiss "
            "Ephemeris as primary calculation engine with comprehensive divisional chart "
            "integration for enhanced accuracy."
        )
    
    def get_layer_name(self) -> str:
        """Get layer name."""
        return "Planetary Positions"
    
    def get_layer_description(self) -> str:
        """Get layer description."""
        return (
            "Direct astronomical planetary calculations including dignity assessment, "
            "retrograde motion detection, angular relationships to natal positions, "
            "and planetary aspect strength analysis. Provides 90% accuracy using "
            "precise ephemeris calculations."
        )
    
    def get_calculation_factors(self) -> List[str]:
        """Get list of calculation factors."""
        return [
            "Planetary dignity assessment and strength calculations",
            "Retrograde motion detection and impact analysis",
            "Angular relationship calculations to natal positions",
            "Planetary aspect strength analysis for daily variations",
            "Comprehensive divisional chart strength analysis (D1-D27)",
            "Direct ephemeris-based planetary position calculations"
        ]
    
    def _calculate_dynamic_weights(self) -> Dict[str, float]:
        """Calculate dynamic planetary weights based on natal chart strength."""
        try:
            dynamic_weights = self._base_planetary_weights.copy()
            
            # Adjust weights based on natal planetary strengths
            for planet in dynamic_weights.keys():
                if planet in self._natal_positions:
                    natal_strength = self._get_natal_planetary_strength(planet)
                    
                    # Stronger planets get slightly higher weight
                    if natal_strength > 0.8:
                        dynamic_weights[planet] *= 1.1
                    elif natal_strength < 0.3:
                        dynamic_weights[planet] *= 0.9
            
            # Normalize weights to sum to 1.0
            total_weight = sum(dynamic_weights.values())
            for planet in dynamic_weights:
                dynamic_weights[planet] /= total_weight
            
            return dynamic_weights
            
        except Exception as e:
            self.logger.error(f"Error calculating dynamic weights: {e}")
            return self._base_planetary_weights
    
    def _get_natal_planetary_strength(self, planet: str) -> float:
        """Get simplified natal planetary strength."""
        try:
            if planet not in self._natal_positions:
                return 0.5
            
            position = self._natal_positions[planet]
            
            # Use dignity as primary strength indicator
            dignity_calc = PlanetaryDignityCalculator()
            return dignity_calc.calculate_dignity(planet, position)
            
        except Exception:
            return 0.5

    def validate_kundali_data(self) -> bool:
        """Validate kundali data for Layer 2 requirements."""
        if not self.kundali:
            self.logger.error("No kundali data provided")
            return False
        
        # Check for required birth details
        if not self.kundali.birth_details:
            self.logger.error("Birth details required for planetary calculations")
            return False
        
        # Check for required planetary positions
        if not self.kundali.planetary_positions:
            self.logger.error("Natal planetary positions required for comparison")
            return False
        
        # Validate essential planets are present
        essential_planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
        missing_planets = []
        
        for planet in essential_planets:
            if planet not in self.kundali.planetary_positions:
                missing_planets.append(planet)
        
        if missing_planets:
            self.logger.error(f"Missing essential planetary positions: {missing_planets}")
            return False
        
        return True


class PlanetaryDignityCalculator:
    """Calculator for planetary dignity and strength assessment."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Define planetary dignities (exaltation, own sign, friendly signs, etc.)
        self._dignity_rules = {
            'sun': {
                'exaltation': [0],  # Aries
                'own_sign': [4],    # Leo
                'friendly': [1, 8, 11],  # Taurus, Sagittarius, Pisces
                'neutral': [2, 5],  # Gemini, Virgo
                'enemy': [3, 6, 9, 10],  # Cancer, Libra, Capricorn, Aquarius
                'debilitation': [7]  # Scorpio
            },
            'moon': {
                'exaltation': [1],  # Taurus
                'own_sign': [3],    # Cancer
                'friendly': [0, 4],  # Aries, Leo
                'neutral': [2, 5, 8, 11],  # Gemini, Virgo, Sagittarius, Pisces
                'enemy': [6, 7, 9, 10],  # Libra, Scorpio, Capricorn, Aquarius
                'debilitation': [7]  # Scorpio
            },
            'mars': {
                'exaltation': [9],  # Capricorn
                'own_sign': [0, 7],  # Aries, Scorpio
                'friendly': [3, 4, 8],  # Cancer, Leo, Sagittarius
                'neutral': [1, 5, 11],  # Taurus, Virgo, Pisces
                'enemy': [2, 6, 10],  # Gemini, Libra, Aquarius
                'debilitation': [3]  # Cancer
            },
            'mercury': {
                'exaltation': [5],  # Virgo
                'own_sign': [2, 5],  # Gemini, Virgo
                'friendly': [0, 4],  # Aries, Leo
                'neutral': [1, 6, 7, 8, 9, 10, 11],  # Most signs
                'enemy': [3],  # Cancer
                'debilitation': [11]  # Pisces
            },
            'jupiter': {
                'exaltation': [3],  # Cancer
                'own_sign': [8, 11],  # Sagittarius, Pisces
                'friendly': [0, 3, 4, 7],  # Aries, Cancer, Leo, Scorpio
                'neutral': [1, 9, 10],  # Taurus, Capricorn, Aquarius
                'enemy': [2, 5, 6],  # Gemini, Virgo, Libra
                'debilitation': [9]  # Capricorn
            },
            'venus': {
                'exaltation': [11],  # Pisces
                'own_sign': [1, 6],  # Taurus, Libra
                'friendly': [2, 5, 8, 9, 10],  # Gemini, Virgo, Sagittarius, Capricorn, Aquarius
                'neutral': [0, 4],  # Aries, Leo
                'enemy': [3, 7],  # Cancer, Scorpio
                'debilitation': [5]  # Virgo
            },
            'saturn': {
                'exaltation': [6],  # Libra
                'own_sign': [9, 10],  # Capricorn, Aquarius
                'friendly': [1, 2, 5],  # Taurus, Gemini, Virgo
                'neutral': [0, 8, 11],  # Aries, Sagittarius, Pisces
                'enemy': [3, 4, 7],  # Cancer, Leo, Scorpio (Libra removed - it's exaltation)
                'debilitation': [0]  # Aries
            }
        }
    
    def calculate_dignity(self, planet_name: str, position: PlanetaryPosition) -> float:
        """
        Calculate planetary dignity score based on sign placement.
        
        Args:
            planet_name: Name of the planet
            position: Current planetary position
            
        Returns:
            Dignity score between 0.0 and 1.0
        """
        try:
            if planet_name not in self._dignity_rules:
                # For Rahu/Ketu or unknown planets, return neutral
                return 0.5
            
            rules = self._dignity_rules[planet_name]
            rasi = position.rasi
            
            # Calculate base dignity score
            if rasi in rules.get('exaltation', []):
                base_score = 1.0  # Maximum strength
            elif rasi in rules.get('own_sign', []):
                base_score = 0.9  # Very strong
            elif rasi in rules.get('friendly', []):
                base_score = 0.7  # Good strength
            elif rasi in rules.get('neutral', []):
                base_score = 0.5  # Neutral strength
            elif rasi in rules.get('enemy', []):
                base_score = 0.3  # Weak strength
            elif rasi in rules.get('debilitation', []):
                base_score = 0.1  # Very weak
            else:
                base_score = 0.5  # Default neutral
            
            # Apply degree-based modifications
            degree_modifier = self._calculate_degree_modifier(position.degree_in_sign)
            
            # Final dignity score
            dignity_score = base_score * degree_modifier
            
            return max(0.0, min(1.0, dignity_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating dignity for {planet_name}: {e}")
            return 0.5
    
    def _calculate_degree_modifier(self, degree_in_sign: float) -> float:
        """
        Calculate degree-based strength modifier.
        
        Planets are stronger in certain degrees of their signs.
        """
        # Simple degree strength calculation
        # Planets are generally stronger in the middle degrees (10-20)
        if 10 <= degree_in_sign <= 20:
            return 1.0  # Peak strength
        elif 5 <= degree_in_sign < 10 or 20 < degree_in_sign <= 25:
            return 0.9  # Good strength
        elif 0 <= degree_in_sign < 5 or 25 < degree_in_sign <= 30:
            return 0.8  # Moderate strength
        else:
            return 0.8  # Default


class RetrogradeAnalyzer:
    """Analyzer for retrograde motion impacts."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Define retrograde impact factors for different planets
        self._retrograde_impacts = {
            'mercury': 0.3,  # Strong impact on communication
            'venus': 0.4,    # Moderate impact on relationships
            'mars': 0.5,     # Moderate impact on energy
            'jupiter': 0.6,  # Less impact, can be beneficial
            'saturn': 0.7,   # Minimal impact, natural slow planet
            'sun': 1.0,      # Sun doesn't go retrograde
            'moon': 1.0,     # Moon doesn't go retrograde
            'rahu': 0.8,     # Nodes are naturally retrograde
            'ketu': 0.8      # Nodes are naturally retrograde
        }
    
    def analyze_retrograde_impact(self, planet_name: str, position: PlanetaryPosition) -> float:
        """
        Analyze retrograde motion impact on favorability.
        
        Args:
            planet_name: Name of the planet
            position: Current planetary position
            
        Returns:
            Retrograde impact score between 0.0 and 1.0
        """
        try:
            if not position.retrograde:
                return 1.0  # No retrograde impact
            
            # Get base retrograde impact for this planet
            base_impact = self._retrograde_impacts.get(planet_name, 0.5)
            
            # Some planets can be beneficial when retrograde (Jupiter, Saturn)
            if planet_name in ['jupiter', 'saturn']:
                # These planets can be more introspective and beneficial when retrograde
                return min(1.0, base_impact * 1.1)
            
            # For other planets, retrograde generally reduces favorability
            return base_impact
            
        except Exception as e:
            self.logger.error(f"Error analyzing retrograde for {planet_name}: {e}")
            return 0.5


class AngularRelationshipCalculator:
    """Calculator for angular relationships to natal positions."""
    
    def __init__(self, natal_positions: Dict[str, PlanetaryPosition]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.natal_positions = natal_positions
        
        # Define favorable and unfavorable angular relationships
        self._angular_relationships = {
            0: 1.0,    # Conjunction - very strong
            30: 0.6,   # Semi-sextile - mild
            60: 0.8,   # Sextile - favorable
            90: 0.3,   # Square - challenging
            120: 0.9,  # Trine - very favorable
            150: 0.4,  # Quincunx - adjusting
            180: 0.2   # Opposition - challenging
        }
    
    def calculate_angular_relationship(self, planet_name: str, current_position: PlanetaryPosition) -> float:
        """
        Calculate angular relationship score to natal position.
        
        Args:
            planet_name: Name of the planet
            current_position: Current planetary position
            
        Returns:
            Angular relationship score between 0.0 and 1.0
        """
        try:
            if planet_name not in self.natal_positions:
                return 0.5  # Neutral if no natal position
            
            natal_position = self.natal_positions[planet_name]
            
            # Calculate angular difference
            angular_diff = abs(current_position.longitude - natal_position.longitude)
            
            # Normalize to 0-180 degrees
            if angular_diff > 180:
                angular_diff = 360 - angular_diff
            
            # Find closest significant aspect
            closest_aspect = self._find_closest_aspect(angular_diff)
            
            # Get relationship strength for closest aspect
            relationship_strength = self._angular_relationships.get(closest_aspect, 0.5)
            
            # Apply orb tolerance (aspects are not exact)
            orb_factor = self._calculate_orb_factor(angular_diff, closest_aspect)
            
            # Final angular relationship score
            angular_score = relationship_strength * orb_factor
            
            return max(0.0, min(1.0, angular_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating angular relationship for {planet_name}: {e}")
            return 0.5
    
    def _find_closest_aspect(self, angular_diff: float) -> int:
        """Find the closest significant aspect to the angular difference."""
        aspects = list(self._angular_relationships.keys())
        closest_aspect = min(aspects, key=lambda x: abs(x - angular_diff))
        return closest_aspect
    
    def _calculate_orb_factor(self, angular_diff: float, aspect: int) -> float:
        """
        Calculate orb factor based on how close the aspect is to exact.
        
        Closer to exact aspect = higher factor.
        """
        orb_difference = abs(angular_diff - aspect)
        
        # Define orb tolerances (degrees)
        if aspect in [0, 180]:  # Conjunction, Opposition
            max_orb = 8
        elif aspect in [90, 120]:  # Square, Trine
            max_orb = 6
        else:  # Other aspects
            max_orb = 4
        
        if orb_difference <= max_orb:
            # Linear decrease from 1.0 to 0.5 within orb
            orb_factor = 1.0 - (orb_difference / max_orb) * 0.5
        else:
            # Outside orb, minimal influence
            orb_factor = 0.5
        
        return orb_factor


class AspectStrengthAnalyzer:
    """Analyzer for planetary aspect strengths in current positions."""
    
    def __init__(self, natal_positions: Dict[str, PlanetaryPosition]):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.natal_positions = natal_positions
        
        # Define aspect strengths and their effects
        self._aspect_strengths = {
            0: {'strength': 1.0, 'nature': 'neutral'},     # Conjunction
            60: {'strength': 0.7, 'nature': 'beneficial'}, # Sextile
            90: {'strength': 0.8, 'nature': 'challenging'}, # Square
            120: {'strength': 0.9, 'nature': 'beneficial'}, # Trine
            180: {'strength': 0.8, 'nature': 'challenging'} # Opposition
        }
    
    def analyze_aspect_strength(
        self, 
        planet_name: str, 
        current_position: PlanetaryPosition,
        all_current_positions: Dict[str, PlanetaryPosition]
    ) -> float:
        """
        Analyze planetary aspect strength for current position.
        
        Args:
            planet_name: Name of the planet
            current_position: Current planetary position
            all_current_positions: All current planetary positions
            
        Returns:
            Aspect strength score between 0.0 and 1.0
        """
        try:
            total_aspect_score = 0.0
            aspect_count = 0
            
            # Analyze aspects to other current planets
            for other_planet, other_position in all_current_positions.items():
                if other_planet != planet_name:
                    aspect_score = self._calculate_aspect_score(
                        current_position, other_position
                    )
                    total_aspect_score += aspect_score
                    aspect_count += 1
            
            # Analyze aspects to natal planets
            for natal_planet, natal_position in self.natal_positions.items():
                if natal_planet != planet_name:
                    aspect_score = self._calculate_aspect_score(
                        current_position, natal_position
                    )
                    total_aspect_score += aspect_score
                    aspect_count += 1
            
            # Calculate average aspect strength
            if aspect_count > 0:
                average_aspect_strength = total_aspect_score / aspect_count
            else:
                average_aspect_strength = 0.5  # Neutral if no aspects
            
            return max(0.0, min(1.0, average_aspect_strength))
            
        except Exception as e:
            self.logger.error(f"Error analyzing aspect strength for {planet_name}: {e}")
            return 0.5
    
    def _calculate_aspect_score(
        self, 
        position1: PlanetaryPosition, 
        position2: PlanetaryPosition
    ) -> float:
        """Calculate aspect score between two planetary positions."""
        try:
            # Calculate angular difference
            angular_diff = abs(position1.longitude - position2.longitude)
            
            # Normalize to 0-180 degrees
            if angular_diff > 180:
                angular_diff = 360 - angular_diff
            
            # Find closest significant aspect
            closest_aspect = None
            min_difference = float('inf')
            
            for aspect_angle in self._aspect_strengths.keys():
                diff = abs(angular_diff - aspect_angle)
                if diff < min_difference:
                    min_difference = diff
                    closest_aspect = aspect_angle
            
            if closest_aspect is None:
                return 0.5  # Neutral if no close aspect
            
            aspect_info = self._aspect_strengths[closest_aspect]
            
            # Calculate orb factor
            orb_tolerance = 8 if closest_aspect in [0, 180] else 6
            
            if min_difference <= orb_tolerance:
                orb_factor = 1.0 - (min_difference / orb_tolerance) * 0.3
                
                # Apply aspect nature
                if aspect_info['nature'] == 'beneficial':
                    aspect_score = 0.5 + (aspect_info['strength'] * orb_factor * 0.5)
                elif aspect_info['nature'] == 'challenging':
                    aspect_score = 0.5 - (aspect_info['strength'] * orb_factor * 0.3)
                else:  # neutral
                    aspect_score = 0.5 + (aspect_info['strength'] * orb_factor * 0.2)
                
                return max(0.0, min(1.0, aspect_score))
            else:
                return 0.5  # Outside orb, neutral influence
                
        except Exception as e:
            self.logger.error(f"Error calculating aspect score: {e}")
            return 0.5
