"""
Centralized Combustion Analyzer for Planetary Combustion Detection

This module provides centralized combustion analysis for all planets.
Combustion occurs when a planet is too close to the Sun, losing its strength
and becoming "burned" by the Sun's powerful rays.
"""

import logging
from typing import Dict, Any, Optional
from ..core.data_models import PlanetaryPosition


class CombustionAnalyzer:
    """
    Analyzer for planetary combustion (proximity to Sun).

    Combustion weakens a planet's benefic qualities and can make
    malefic planets more challenging. The orb of combustion varies
    by planet based on traditional Vedic astrology texts.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Combustion orbs in degrees (traditional values)
        self._combustion_orbs = {
            'moon': 12,      # Most sensitive to combustion
            'mars': 17,      # Wide orb due to fierce nature
            'mercury': 14,   # When not in same sign as Sun
            'jupiter': 11,   # Benefic, moderate orb
            'venus': 10,     # Benefic, tight orb
            'saturn': 15,    # Malefic, moderate-wide orb
            'rahu': None,    # Nodes don't get combust
            'ketu': None     # Nodes don't get combust
        }

        # Severity thresholds (% of orb)
        self._severity_thresholds = {
            'critical': 0.33,   # Within 33% of orb (very close)
            'high': 0.50,       # Within 50% of orb
            'moderate': 0.75,   # Within 75% of orb
            'low': 1.0          # Within full orb
        }

        # Combustion penalties by severity
        self._combustion_penalties = {
            'critical': -0.25,  # 25% penalty
            'high': -0.18,      # 18% penalty
            'moderate': -0.12,  # 12% penalty
            'low': -0.08        # 8% penalty
        }

    def is_combust(
        self,
        planet: str,
        planet_position: PlanetaryPosition,
        sun_position: PlanetaryPosition
    ) -> Dict[str, Any]:
        """
        Check if planet is combust and provide detailed analysis.

        Args:
            planet: Planet name (lowercase)
            planet_position: Planet's position
            sun_position: Sun's position

        Returns:
            dict with combust, severity, distance, penalty, recommendation
        """
        try:
            planet_lower = planet.lower()

            # Get combustion orb for this planet
            orb = self._combustion_orbs.get(planet_lower)

            # Nodes and planets without orb definitions don't get combust
            if orb is None:
                return {
                    'combust': False,
                    'distance': None,
                    'severity': 'None',
                    'penalty': 0.0,
                    'recommendation': 'Not applicable for combustion'
                }

            # Calculate angular distance from Sun
            distance = abs(planet_position.longitude - sun_position.longitude)
            if distance > 180:
                distance = 360 - distance

            # Check if within combustion orb
            if distance >= orb:
                return {
                    'combust': False,
                    'distance': distance,
                    'severity': 'None',
                    'penalty': 0.0,
                    'recommendation': 'Not combust'
                }

            # Determine severity based on proximity
            distance_ratio = distance / orb

            if distance_ratio <= self._severity_thresholds['critical']:
                severity = 'Critical'
                penalty = self._combustion_penalties['critical']
                recommendation = 'CRITICAL COMBUSTION: Planet severely weakened. Avoid matters related to this planet.'
            elif distance_ratio <= self._severity_thresholds['high']:
                severity = 'High'
                penalty = self._combustion_penalties['high']
                recommendation = 'HIGH COMBUSTION: Planet significantly weakened. Use caution for related matters.'
            elif distance_ratio <= self._severity_thresholds['moderate']:
                severity = 'Moderate'
                penalty = self._combustion_penalties['moderate']
                recommendation = 'MODERATE COMBUSTION: Planet moderately weakened. Consider remedies.'
            else:
                severity = 'Low'
                penalty = self._combustion_penalties['low']
                recommendation = 'LOW COMBUSTION: Planet slightly weakened.'

            # Special case: Mercury within 12° in same sign is "Budha Aditya Yoga" (benefic)
            if planet_lower == 'mercury' and planet_position.rasi == sun_position.rasi and distance <= 12:
                return {
                    'combust': False,  # Exception: Budha Aditya Yoga
                    'distance': distance,
                    'severity': 'Budha Aditya Yoga',
                    'penalty': 0.15,  # BONUS, not penalty!
                    'recommendation': 'BUDHA ADITYA YOGA: Auspicious combination of Sun-Mercury in same sign. Excellent for intellect, communication, business.'
                }

            return {
                'combust': True,
                'distance': distance,
                'distance_ratio': distance_ratio,
                'orb': orb,
                'severity': severity,
                'penalty': penalty,
                'recommendation': recommendation
            }

        except Exception as e:
            self.logger.error(f"Error checking combustion for {planet}: {e}")
            return {
                'combust': False,
                'distance': None,
                'severity': 'Error',
                'penalty': 0.0,
                'recommendation': 'Error in combustion detection'
            }

    def analyze_all_planets(
        self,
        planetary_positions: Dict[str, PlanetaryPosition]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Analyze combustion for all planets.

        Args:
            planetary_positions: Dictionary of all planetary positions

        Returns:
            dict mapping planet names to combustion analysis
        """
        try:
            if 'sun' not in planetary_positions:
                return {}

            sun_position = planetary_positions['sun']
            results = {}

            # Check each planet except Sun itself
            for planet, position in planetary_positions.items():
                if planet.lower() in ['sun', 'lagna', 'ascendant']:
                    continue

                combustion_info = self.is_combust(planet, position, sun_position)
                results[planet] = combustion_info

            return results

        except Exception as e:
            self.logger.error(f"Error analyzing combustion for all planets: {e}")
            return {}

    def get_combust_planets_summary(
        self,
        planetary_positions: Dict[str, PlanetaryPosition]
    ) -> Dict[str, Any]:
        """
        Get summary of all combust planets.

        Args:
            planetary_positions: Dictionary of all planetary positions

        Returns:
            dict with combust_count, combust_planets, total_penalty
        """
        try:
            combustion_analysis = self.analyze_all_planets(planetary_positions)

            combust_planets = []
            total_penalty = 0.0

            for planet, analysis in combustion_analysis.items():
                if analysis['combust']:
                    combust_planets.append({
                        'planet': planet,
                        'severity': analysis['severity'],
                        'distance': analysis['distance'],
                        'penalty': analysis['penalty']
                    })
                    total_penalty += analysis['penalty']

            return {
                'combust_count': len(combust_planets),
                'combust_planets': combust_planets,
                'total_penalty': total_penalty,
                'has_combustion': len(combust_planets) > 0
            }

        except Exception as e:
            self.logger.error(f"Error getting combustion summary: {e}")
            return {
                'combust_count': 0,
                'combust_planets': [],
                'total_penalty': 0.0,
                'has_combustion': False
            }
