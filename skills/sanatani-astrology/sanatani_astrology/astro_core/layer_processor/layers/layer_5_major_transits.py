"""
Layer 5: Enhanced Major Transits with Ashtakavarga (65% Accuracy)

This layer calculates favorability based on major planetary transits enhanced with
Ashtakavarga strength analysis, including Jupiter and Saturn transits, Rahu/Ketu
nodal patterns, major aspect formations, and comprehensive transit-to-natal
comparison with Ashtakavarga-based strength assessment.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..base_layer import LayerProcessor
from ...core.data_models import KundaliData, PlanetaryPosition
from ...kundali_generator.comprehensive_ephemeris_engine import ComprehensiveEphemerisEngine
from ..ashtakavarga_analyzer import AshtakavargaAnalyzer
from ..combustion_analyzer import CombustionAnalyzer


class Layer5_MajorTransits(LayerProcessor):
    """
    Layer 5: Enhanced Major Transits processor with 65% accuracy.
    
    Calculates favorability based on:
    - Jupiter transit analysis with Ashtakavarga strength assessment
    - Saturn transit effects with 29-year cycle and Ashtakavarga integration
    - Rahu/Ketu nodal transit analysis with 18-year patterns
    - Major aspect formation detection with strength assessment
    - Enhanced transit-to-natal comparison with Ashtakavarga weighting
    """
    
    def __init__(self, layer_id: int, accuracy: float, kundali_data: KundaliData):
        """Initialize Layer 5 processor."""
        super().__init__(layer_id, accuracy, kundali_data)
        
        # Initialize calculation engines
        self._ephemeris_engine = ComprehensiveEphemerisEngine()
        self._ashtakavarga_analyzer = AshtakavargaAnalyzer(kundali_data)
        self._combustion_analyzer = CombustionAnalyzer()
        self._house_cusps = self._extract_house_cusps(kundali_data)
        
        # Cache birth data
        if kundali_data.birth_details:
            self._birth_date = kundali_data.birth_details.date
            self._birth_time = kundali_data.birth_details.time
            self._birth_latitude = kundali_data.birth_details.latitude
            self._birth_longitude = kundali_data.birth_details.longitude
            self._birth_timezone = kundali_data.birth_details.timezone_offset
        else:
            raise ValueError("Birth details required for Layer 5 calculations")
        
        # Cache natal planetary positions
        self._natal_positions = kundali_data.planetary_positions
        
        # Transit weights for final score calculation
        self._transit_weights = {
            'jupiter': 0.25,      # Major benefic
            'saturn': 0.25,       # Major malefic
            'rahu_ketu': 0.20,    # Nodal axis
            'major_aspects': 0.15, # Aspect formations
            'ashtakavarga': 0.15   # Ashtakavarga strength
        }
        
        # Transit cycle information
        self._transit_cycles = {
            'jupiter': {'years': 12, 'houses_per_year': 1},
            'saturn': {'years': 29, 'houses_per_year': 0.4},
            'rahu': {'years': 18, 'retrograde': True},
            'ketu': {'years': 18, 'retrograde': True}
        }

        self._dignity_profiles = {
            'jupiter': {
                'exaltation': 3,   # Cancer
                'debilitation': 9, # Capricorn
                'own': {8, 11},    # Sagittarius, Pisces
                'mooltrikona': {8}
            },
            'saturn': {
                'exaltation': 6,   # Libra
                'debilitation': 0, # Aries
                'own': {9, 10},    # Capricorn, Aquarius
                'mooltrikona': {10}
            }
        }
    
    def calculate_daily_score(self, date: datetime) -> float:
        """
        Calculate major transits favorability score for specific date.
        
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
            
            # Calculate individual transit factors
            jupiter_score = self._calculate_jupiter_transit_score(current_positions, date)
            saturn_score = self._calculate_saturn_transit_score(current_positions, date)
            nodal_score = self._calculate_nodal_transit_score(current_positions, date)
            aspects_score = self._calculate_major_aspects_score(current_positions, date)
            ashtakavarga_score = self._calculate_ashtakavarga_transit_score(date)

            # NEW: Calculate Chandrashtama penalty
            chandrashtama_penalty = self._calculate_chandrashtama_penalty(current_positions)

            # Combine all factors with weights
            total_score = (
                jupiter_score * self._transit_weights['jupiter'] +
                saturn_score * self._transit_weights['saturn'] +
                nodal_score * self._transit_weights['rahu_ketu'] +
                aspects_score * self._transit_weights['major_aspects'] +
                ashtakavarga_score * self._transit_weights['ashtakavarga']
            )

            # Apply Chandrashtama penalty
            total_score = max(0.0, total_score + chandrashtama_penalty)
            
            # Ensure score is within valid range
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate major transits score for {date}: {e}")
            raise
    
    def _calculate_jupiter_transit_score(self, current_positions: Dict[str, PlanetaryPosition], date: datetime) -> float:
        """Calculate Jupiter transit favorability score."""
        try:
            if 'jupiter' not in current_positions:
                return 0.5
            
            jupiter_position = current_positions['jupiter']
            
            # Get Jupiter's current house from natal Lagna
            current_house = self._get_house_from_lagna(jupiter_position)
            
            # Jupiter transit favorability by house from Lagna
            jupiter_house_scores = {
                1: 0.8,   # Self, personality - good
                2: 0.7,   # Wealth, family - good
                3: 0.6,   # Siblings, courage - moderate
                4: 0.9,   # Home, mother - excellent
                5: 0.9,   # Children, creativity - excellent
                6: 0.4,   # Enemies, health - challenging
                7: 0.8,   # Partnership, marriage - good
                8: 0.3,   # Transformation, obstacles - difficult
                9: 0.9,   # Fortune, dharma - excellent
                10: 0.8,  # Career, status - good
                11: 0.9,  # Gains, fulfillment - excellent
                12: 0.4   # Loss, spirituality - mixed
            }
            
            base_score = jupiter_house_scores.get(current_house, 0.5)
            
            # Apply Ashtakavarga strength
            jupiter_ashtakavarga = self._ashtakavarga_analyzer.calculate_planetary_strength('jupiter', date)
            
            # Combine base score with Ashtakavarga
            combined_score = (base_score * 0.7) + (jupiter_ashtakavarga * 0.3)
            
            # Apply retrograde modifier
            if jupiter_position.retrograde:
                combined_score *= 0.8  # Reduce for retrograde

            # Apply dignity modifier
            combined_score *= self._get_dignity_modifier('jupiter', jupiter_position)

            # Apply combustion penalty using centralized analyzer
            combustion_info = self._combustion_analyzer.is_combust('jupiter', jupiter_position, current_positions.get('sun'))
            if combustion_info['combust']:
                combined_score = max(0.0, combined_score + combustion_info['penalty'])
            
            return max(0.0, min(1.0, combined_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating Jupiter transit score: {e}")
            return 0.5
    
    def _calculate_saturn_transit_score(self, current_positions: Dict[str, PlanetaryPosition], date: datetime) -> float:
        """Calculate Saturn transit favorability score."""
        try:
            if 'saturn' not in current_positions:
                return 0.5
            
            saturn_position = current_positions['saturn']
            
            # Get Saturn's current house from natal Lagna
            current_house = self._get_house_from_lagna(saturn_position)
            
            # Saturn transit favorability by house from Lagna
            saturn_house_scores = {
                1: 0.3,   # Self - challenging, discipline needed
                2: 0.4,   # Wealth - financial restrictions
                3: 0.7,   # Siblings - good for courage
                4: 0.2,   # Home - difficult period
                5: 0.3,   # Children - delays in creativity
                6: 0.8,   # Enemies - excellent for overcoming obstacles
                7: 0.4,   # Partnership - relationship challenges
                8: 0.2,   # Transformation - very difficult
                9: 0.5,   # Fortune - mixed results
                10: 0.6,  # Career - slow but steady progress
                11: 0.8,  # Gains - good for long-term gains
                12: 0.5   # Loss - spiritual growth
            }
            
            base_score = saturn_house_scores.get(current_house, 0.5)
            
            # Apply Ashtakavarga strength
            saturn_ashtakavarga = self._ashtakavarga_analyzer.calculate_planetary_strength('saturn', date)
            
            # Combine base score with Ashtakavarga
            combined_score = (base_score * 0.7) + (saturn_ashtakavarga * 0.3)
            
            # Check for Sade Sati (Saturn in 12th, 1st, or 2nd from Moon)
            sade_sati_phase = self._get_sade_sati_phase(saturn_position)
            if sade_sati_phase:
                combined_score *= sade_sati_phase['intensity']
            
            # Apply retrograde modifier
            if saturn_position.retrograde:
                combined_score *= 1.1  # Saturn retrograde can be beneficial

            # Apply dignity modifier
            combined_score *= self._get_dignity_modifier('saturn', saturn_position)

            # Apply combustion penalty using centralized analyzer
            combustion_info = self._combustion_analyzer.is_combust('saturn', saturn_position, current_positions.get('sun'))
            if combustion_info['combust']:
                combined_score = max(0.0, combined_score + combustion_info['penalty'])
            
            return max(0.0, min(1.0, combined_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating Saturn transit score: {e}")
            return 0.5
    
    def _calculate_nodal_transit_score(self, current_positions: Dict[str, PlanetaryPosition], date: datetime) -> float:
        """Calculate Rahu/Ketu nodal transit favorability score."""
        try:
            if 'rahu' not in current_positions or 'ketu' not in current_positions:
                return 0.5
            
            rahu_position = current_positions['rahu']
            ketu_position = current_positions['ketu']
            
            # Get current houses from natal Lagna
            rahu_house = self._get_house_from_lagna(rahu_position)
            ketu_house = self._get_house_from_lagna(ketu_position)
            
            # Rahu favorability by house
            rahu_house_scores = {
                1: 0.4,   # Self - identity confusion
                2: 0.3,   # Wealth - material obsession
                3: 0.7,   # Siblings - good for courage
                4: 0.3,   # Home - domestic issues
                5: 0.4,   # Children - creative blocks
                6: 0.8,   # Enemies - excellent for competition
                7: 0.4,   # Partnership - relationship illusions
                8: 0.2,   # Transformation - very challenging
                9: 0.3,   # Fortune - spiritual confusion
                10: 0.6,  # Career - worldly success
                11: 0.8,  # Gains - material gains
                12: 0.5   # Loss - spiritual seeking
            }
            
            # Ketu favorability by house
            ketu_house_scores = {
                1: 0.6,   # Self - spiritual insight
                2: 0.4,   # Wealth - detachment from money
                3: 0.5,   # Siblings - karmic relationships
                4: 0.4,   # Home - emotional detachment
                5: 0.6,   # Children - spiritual creativity
                6: 0.7,   # Enemies - overcoming through detachment
                7: 0.4,   # Partnership - relationship detachment
                8: 0.7,   # Transformation - spiritual transformation
                9: 0.8,   # Fortune - spiritual wisdom
                10: 0.4,  # Career - detachment from status
                11: 0.3,  # Gains - loss of material desires
                12: 0.8   # Loss - spiritual liberation
            }
            
            rahu_score = rahu_house_scores.get(rahu_house, 0.5)
            ketu_score = ketu_house_scores.get(ketu_house, 0.5)
            
            # Combine Rahu and Ketu scores
            nodal_score = (rahu_score + ketu_score) / 2.0
            
            return max(0.0, min(1.0, nodal_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating nodal transit score: {e}")
            return 0.5
    
    def _calculate_major_aspects_score(self, current_positions: Dict[str, PlanetaryPosition], date: datetime) -> float:
        """Calculate major aspects formation score."""
        try:
            aspect_score = 0.5  # Base neutral score
            aspect_count = 0
            
            # Check major aspects between slow-moving planets
            slow_planets = ['jupiter', 'saturn', 'rahu', 'ketu']
            
            for i, planet1 in enumerate(slow_planets):
                if planet1 not in current_positions:
                    continue
                    
                for planet2 in slow_planets[i+1:]:
                    if planet2 not in current_positions:
                        continue
                    
                    # Calculate angular difference
                    pos1 = current_positions[planet1]
                    pos2 = current_positions[planet2]
                    
                    angular_diff = abs(pos1.longitude - pos2.longitude)
                    if angular_diff > 180:
                        angular_diff = 360 - angular_diff
                    
                    # Check for major aspects (with 5-degree orb)
                    aspect_strength = self._get_aspect_strength(angular_diff, planet1, planet2)
                    
                    if aspect_strength > 0:
                        aspect_score += aspect_strength
                        aspect_count += 1
            
            # Normalize score
            if aspect_count > 0:
                aspect_score = aspect_score / (aspect_count + 1)  # +1 for base score
            
            return max(0.0, min(1.0, aspect_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating major aspects score: {e}")
            return 0.5
    
    def _calculate_ashtakavarga_transit_score(self, date: datetime) -> float:
        """Calculate overall Ashtakavarga-based transit strength."""
        try:
            # Get Sarvashtakavarga strength for the date
            sarvashtakavarga_strength = self._ashtakavarga_analyzer.calculate_sarvashtakavarga_strength(date)
            
            return sarvashtakavarga_strength
            
        except Exception as e:
            self.logger.error(f"Error calculating Ashtakavarga transit score: {e}")
            return 0.5
    
    def _get_house_from_lagna(self, position: PlanetaryPosition) -> int:
        """Get house number from Lagna for a planetary position."""
        try:
            resolved = self._resolve_house_from_cusps(position.longitude)
            if resolved is not None:
                return resolved

            if 'lagna' not in self._natal_positions:
                return position.rasi + 1
            
            lagna_rasi = self._natal_positions['lagna'].rasi
            planet_rasi = position.rasi
            return ((planet_rasi - lagna_rasi) % 12) + 1
            
        except Exception as e:
            self.logger.error(f"Error calculating house from Lagna: {e}")
            return 1
    
    def _get_sade_sati_phase(self, saturn_position: PlanetaryPosition) -> Optional[Dict[str, Any]]:
        """Get Sade Sati phase details when Saturn surrounds natal Moon."""
        try:
            if 'moon' not in self._natal_positions:
                return None
            
            moon_rasi = self._natal_positions['moon'].rasi
            saturn_rasi = saturn_position.rasi
            
            sade_sati_positions = [
                ((moon_rasi - 1) % 12, {'phase': 'rising', 'intensity': 0.85}),
                (moon_rasi, {'phase': 'peak', 'intensity': 0.65}),
                ((moon_rasi + 1) % 12, {'phase': 'setting', 'intensity': 0.8})
            ]
            
            for rasi_index, phase in sade_sati_positions:
                if saturn_rasi == rasi_index:
                    return phase
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking Sade Sati: {e}")
            return None
    
    def _get_aspect_strength(self, angular_diff: float, planet1: str, planet2: str) -> float:
        """Get aspect strength between two planets."""
        try:
            # Major aspects with orbs
            aspects = {
                0: {'strength': 1.0, 'orb': 5, 'nature': 'conjunction'},
                60: {'strength': 0.7, 'orb': 4, 'nature': 'sextile'},
                90: {'strength': 0.8, 'orb': 5, 'nature': 'square'},
                120: {'strength': 0.9, 'orb': 5, 'nature': 'trine'},
                180: {'strength': 0.8, 'orb': 5, 'nature': 'opposition'}
            }
            
            for aspect_angle, aspect_info in aspects.items():
                if abs(angular_diff - aspect_angle) <= aspect_info['orb']:
                    # Calculate exact strength based on orb
                    orb_factor = 1.0 - (abs(angular_diff - aspect_angle) / aspect_info['orb'])
                    base_strength = aspect_info['strength'] * orb_factor
                    
                    # Apply planetary combination modifiers
                    combination_modifier = self._get_planetary_combination_modifier(planet1, planet2, aspect_info['nature'])
                    
                    return base_strength * combination_modifier
            
            return 0.0  # No major aspect
            
        except Exception as e:
            self.logger.error(f"Error calculating aspect strength: {e}")
            return 0.0
    
    def _get_planetary_combination_modifier(self, planet1: str, planet2: str, aspect_nature: str) -> float:
        """Get modifier for planetary combinations in aspects."""
        try:
            # Benefic combinations
            benefic_combinations = [
                ('jupiter', 'venus'),
                ('jupiter', 'mercury'),
                ('venus', 'mercury')
            ]
            
            # Challenging combinations
            challenging_combinations = [
                ('saturn', 'mars'),
                ('saturn', 'rahu'),
                ('mars', 'rahu'),
                ('rahu', 'ketu')
            ]
            
            combination = tuple(sorted([planet1, planet2]))
            
            if combination in benefic_combinations:
                if aspect_nature in ['trine', 'sextile']:
                    return 1.2  # Very favorable
                elif aspect_nature == 'conjunction':
                    return 1.1  # Favorable
                else:
                    return 1.0  # Neutral
            elif combination in challenging_combinations:
                if aspect_nature in ['square', 'opposition']:
                    return 0.7  # More challenging
                elif aspect_nature == 'conjunction':
                    return 0.8  # Challenging
                else:
                    return 0.9  # Slightly challenging
            else:
                return 1.0  # Neutral
                
        except Exception as e:
            self.logger.error(f"Error calculating combination modifier: {e}")
            return 1.0

    def _calculate_chandrashtama_penalty(self, current_positions: Dict[str, PlanetaryPosition]) -> float:
        """
        Calculate Chandrashtama penalty.
        Chandrashtama occurs when Moon transits 8th sign from natal Moon.
        This is considered HIGHLY INAUSPICIOUS for starting important activities.

        Returns:
            Negative penalty value (0.0 to -0.30) or 0.0 if no affliction
        """
        try:
            if 'moon' not in current_positions or 'moon' not in self._natal_positions:
                return 0.0

            transit_moon = current_positions['moon']
            natal_moon = self._natal_positions['moon']

            # Get sign numbers (0-11)
            transit_moon_sign = int(transit_moon.longitude / 30)
            natal_moon_sign = int(natal_moon.longitude / 30)

            # Calculate sign distance
            sign_distance = (transit_moon_sign - natal_moon_sign) % 12

            if sign_distance == 7:  # 8th house (0-indexed = 7)
                # Critical Chandrashtama - apply heavy penalty
                return -0.30  # 30% penalty to favorability

            elif sign_distance in [6, 8]:  # Adjacent to 8th (7th or 9th house)
                # Moderate Chandrashtama influence
                return -0.12  # 12% penalty

            else:
                # No Chandrashtama affliction
                return 0.0

        except Exception as e:
            self.logger.error(f"Error calculating Chandrashtama penalty: {e}")
            return 0.0

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
            
            # Provide granular features to enable rule-driven scoring from YAML
            factors = {
                # Precomputed aggregate factors (for backward compatibility / direct usage)
                'major_aspects': self._calculate_major_aspects_score(current_positions, date),
                'ashtakavarga_strength': self._calculate_ashtakavarga_transit_score(date)
            }
            # Jupiter features
            if 'jupiter' in current_positions:
                factors['jupiter_house'] = self._get_house_from_lagna(current_positions['jupiter'])
                factors['jupiter_retrograde'] = bool(current_positions['jupiter'].retrograde)
            # Saturn features
            if 'saturn' in current_positions:
                factors['saturn_house'] = self._get_house_from_lagna(current_positions['saturn'])
                factors['saturn_retrograde'] = bool(current_positions['saturn'].retrograde)
                phase = self._get_sade_sati_phase(current_positions['saturn'])
                if phase:
                    factors['sade_sati_phase'] = phase.get('phase')
                    factors['sade_sati_intensity'] = phase.get('intensity')
            # Node features
            if 'rahu' in current_positions:
                factors['rahu_house'] = self._get_house_from_lagna(current_positions['rahu'])
            if 'ketu' in current_positions:
                factors['ketu_house'] = self._get_house_from_lagna(current_positions['ketu'])
            # Ashtakavarga per-planet (for blending if rules need it)
            try:
                factors['ashtakavarga_jupiter'] = self._ashtakavarga_analyzer.calculate_planetary_strength('jupiter', date)
            except Exception:
                factors['ashtakavarga_jupiter'] = 0.5
            try:
                factors['ashtakavarga_saturn'] = self._ashtakavarga_analyzer.calculate_planetary_strength('saturn', date)
            except Exception:
                factors['ashtakavarga_saturn'] = 0.5

            # NEW: Chandrashtama detection
            chandrashtama_penalty = self._calculate_chandrashtama_penalty(current_positions)
            factors['chandrashtama_present'] = (chandrashtama_penalty < -0.20)
            factors['chandrashtama_penalty'] = chandrashtama_penalty

            return factors
            
        except Exception:
            return {}

    def _extract_house_cusps(self, kundali_data: KundaliData) -> List[float]:
        """Extract D1 house cusps for bhava calculations."""
        try:
            divisional = (kundali_data.divisional_charts or {}).get('D1') or {}
            cusps = divisional.get('house_cusps')
            if isinstance(cusps, list) and len(cusps) == 12:
                return [float(value) % 360.0 for value in cusps]
        except Exception:
            pass

        try:
            lagna = kundali_data.planetary_positions.get('lagna')
            if lagna:
                return [
                    (float(lagna.longitude) + house_index * 30.0) % 360.0
                    for house_index in range(12)
                ]
        except Exception:
            pass
        return []

    def _resolve_house_from_cusps(self, longitude: float) -> Optional[int]:
        """Resolve the bhava based on stored cusps."""
        if not self._house_cusps:
            return None
        normalized_long = float(longitude) % 360.0
        for index in range(12):
            start = self._house_cusps[index]
            end = self._house_cusps[(index + 1) % 12]
            adj_start = start
            adj_end = end
            adj_long = normalized_long
            if adj_end <= adj_start:
                adj_end += 360.0
                if adj_long < adj_start:
                    adj_long += 360.0
            if adj_start <= adj_long < adj_end:
                return index + 1
        return None

    def _get_dignity_modifier(self, planet: str, position: PlanetaryPosition) -> float:
        """Return multiplier based on planetary dignity."""
        profile = self._dignity_profiles.get(planet)
        if not profile:
            return 1.0
        rasi = position.rasi
        if rasi == profile.get('exaltation'):
            return 1.25
        if rasi == profile.get('debilitation'):
            return 0.75
        if rasi in profile.get('mooltrikona', set()):
            return 1.15
        if rasi in profile.get('own', set()):
            return 1.1
        return 1.0

    def _is_combust_legacy(
        self,
        planet: str,
        planet_position: PlanetaryPosition,
        current_positions: Dict[str, PlanetaryPosition]
    ) -> bool:
        """
        DEPRECATED: Legacy combustion check method.
        Use CombustionAnalyzer.is_combust() instead for detailed analysis.
        """
        sun_position = current_positions.get('sun')
        if not sun_position:
            return False

        combustion_info = self._combustion_analyzer.is_combust(planet, planet_position, sun_position)
        return combustion_info['combust']
    
    def get_calculation_methodology(self) -> str:
        """Describe calculation methodology."""
        return (
            "Enhanced major planetary transits analysis with Ashtakavarga integration (65% accuracy). "
            "Combines Jupiter transit analysis with Ashtakavarga strength (25%), Saturn transit "
            "effects including Sade Sati analysis (25%), Rahu/Ketu nodal patterns (20%), "
            "major aspect formations between slow planets (15%), and comprehensive "
            "Ashtakavarga-based transit strength assessment (15%). Uses precise ephemeris "
            "calculations with traditional Vedic transit principles."
        )
    
    def get_layer_name(self) -> str:
        """Get layer name."""
        return "Enhanced Major Transits with Ashtakavarga"
    
    def get_layer_description(self) -> str:
        """Get layer description."""
        return (
            "Comprehensive analysis of major planetary transits enhanced with Ashtakavarga "
            "strength calculations. Focuses on slow-moving planets (Jupiter, Saturn, Rahu, Ketu) "
            "and their long-term influences on daily favorability. Includes Sade Sati analysis, "
            "major aspect formations, and traditional Ashtakavarga-based strength assessment "
            "for enhanced timing accuracy."
        )
    
    def get_calculation_factors(self) -> List[str]:
        """Get list of calculation factors."""
        return [
            "Jupiter transit analysis with Ashtakavarga strength assessment",
            "Saturn transit effects with 29-year cycle and Sade Sati analysis",
            "Rahu/Ketu nodal transit analysis with 18-year patterns",
            "Major aspect formation detection between slow-moving planets",
            "Enhanced transit-to-natal comparison with Ashtakavarga weighting",
            "Sarvashtakavarga-based overall transit strength calculation"
        ]
    
    def validate_kundali_data(self) -> bool:
        """Validate kundali data for Layer 5 requirements."""
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
        essential_planets = ['jupiter', 'saturn', 'rahu', 'ketu', 'moon', 'lagna']
        missing_planets = []
        
        for planet in essential_planets:
            if planet not in self.kundali.planetary_positions:
                missing_planets.append(planet)
        
        if missing_planets:
            self.logger.error(f"Missing essential positions for transit analysis: {missing_planets}")
            return False
        
        return True
