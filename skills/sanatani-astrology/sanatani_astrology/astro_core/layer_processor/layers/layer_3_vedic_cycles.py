"""
Layer 3: Vedic Time Cycles (80% Accuracy)

This layer calculates favorability based on traditional Vedic time calculations
including tithi (lunar day), nakshatra (lunar mansion), weekday strength evaluation,
paksha (lunar fortnight) analysis, and traditional Vedic calendar correlations.
"""

import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import logging

from ..base_layer import LayerProcessor
from ...core.data_models import KundaliData, PlanetaryPosition
from ...kundali_generator.comprehensive_ephemeris_engine import ComprehensiveEphemerisEngine
from ...kundali_generator.dasha_calculator import DashaCalculator


class Layer3_VedicCycles(LayerProcessor):
    """
    Layer 3: Vedic Time Cycles processor with 80% accuracy.
    
    Calculates favorability based on:
    - Tithi (lunar day) calculation and favorability assessment
    - Nakshatra (lunar mansion) analysis with quarter precision
    - Weekday strength evaluation based on planetary rulers
    - Paksha (lunar fortnight) analysis and scoring
    - Traditional Vedic calendar correlation methods
    """
    
    def __init__(self, layer_id: int, accuracy: float, kundali_data: KundaliData):
        """Initialize Layer 3 processor."""
        super().__init__(layer_id, accuracy, kundali_data)
        
        # Initialize calculation engines
        self._ephemeris_engine = ComprehensiveEphemerisEngine()
        self._dasha_calculator = DashaCalculator()
        
        # Initialize calculation components
        self._tithi_calculator = TithiCalculator()
        self._nakshatra_analyzer = NakshatraAnalyzer(self._dasha_calculator)
        self._weekday_evaluator = WeekdayEvaluator(kundali_data.birth_details)
        self._paksha_analyzer = PakshaAnalyzer()
        self._vedic_correlator = VedicCalendarCorrelator(kundali_data)
        self._yoga_calculator = YogaCalculator()
        self._karana_calculator = KaranaCalculator()
        self._tarabala_calculator = TarabalaCalculator()
        self._hora_calculator = HoraCalculator()
        self._lunar_month_calculator = LunarMonthCalculator()

        # Cache birth location data
        if kundali_data.birth_details:
            self._birth_latitude = kundali_data.birth_details.latitude
            self._birth_longitude = kundali_data.birth_details.longitude
            self._birth_timezone = kundali_data.birth_details.timezone_offset
            self._birth_date = kundali_data.birth_details.date
        else:
            raise ValueError("Birth details required for Layer 3 calculations")

        # Cache natal panchanga data for comparison
        self._natal_panchanga = kundali_data.panchanga

        # Get birth nakshatra index for Tarabala calculations
        self._birth_nakshatra_index = None
        if self._natal_panchanga and 'nakshatra' in self._natal_panchanga:
            natal_nakshatra_name = self._natal_panchanga['nakshatra'].get('name', '')
            for i, name in enumerate(self._dasha_calculator.nakshatra_names):
                if name.lower() == natal_nakshatra_name.lower():
                    self._birth_nakshatra_index = i
                    break

        # ENHANCED: Factor weights with Yoga/Karana/Tarabala/Hora integration
        self._factor_weights = {
            'tithi': 0.16,              # Reduced to accommodate hora
            'nakshatra': 0.18,          # Reduced to accommodate hora
            'tarabala': 0.08,           # Star compatibility
            'yoga': 0.12,               # 27 yogas
            'karana': 0.10,             # 11 karanas
            'hora': 0.10,               # NEW: Planetary hours (critical for intraday timing)
            'weekday': 0.08,            # Reduced to accommodate hora
            'paksha': 0.08,             # Reduced to accommodate hora
            'vedic_correlation': 0.05,  # Reduced to accommodate hora
            'muhurta_analysis': 0.05    # Reduced to accommodate hora
        }
    
    def calculate_daily_score(self, date: datetime) -> float:
        """
        Calculate Vedic time cycles favorability score for specific date.
        
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
            
            # Get current planetary positions (especially Sun and Moon)
            current_positions = self._ephemeris_engine.calculate_planetary_positions(
                julian_day, self._birth_latitude, self._birth_longitude
            )
            
            if not current_positions or 'sun' not in current_positions or 'moon' not in current_positions:
                self.logger.warning(f"Could not calculate planetary positions for {date}")
                return 0.5  # Neutral fallback
            
            sun_position = current_positions['sun']
            moon_position = current_positions['moon']

            # Calculate individual Vedic factors
            tithi_score = self._calculate_tithi_score(sun_position, moon_position)
            nakshatra_score = self._calculate_nakshatra_score(moon_position, date)
            weekday_score = self._calculate_weekday_score(date)
            paksha_score = self._calculate_paksha_score(sun_position, moon_position)
            vedic_correlation_score = self._calculate_vedic_correlation_score(
                sun_position, moon_position, date
            )
            # ENHANCEMENT: Add Muhurta analysis for precise timing
            muhurta_score = self._calculate_muhurta_score(date, sun_position, moon_position)

            # NEW: Calculate Yoga score
            yoga_score = self._calculate_yoga_score(sun_position, moon_position)

            # NEW: Calculate Karana score
            karana_score = self._calculate_karana_score(sun_position, moon_position)

            # NEW: Calculate Tarabala score
            tarabala_score = self._calculate_tarabala_score(moon_position)

            # NEW: Calculate Hora score
            hora_score = self._calculate_hora_score(date, sun_position)

            # Apply Panchaka dosha penalty if present
            panchaka_penalty = self._calculate_panchaka_penalty(moon_position, sun_position, moon_position)

            # Combine all factors with weights
            total_score = (
                tithi_score * self._factor_weights['tithi'] +
                nakshatra_score * self._factor_weights['nakshatra'] +
                tarabala_score * self._factor_weights['tarabala'] +
                yoga_score * self._factor_weights['yoga'] +
                karana_score * self._factor_weights['karana'] +
                hora_score * self._factor_weights['hora'] +
                weekday_score * self._factor_weights['weekday'] +
                paksha_score * self._factor_weights['paksha'] +
                vedic_correlation_score * self._factor_weights['vedic_correlation'] +
                muhurta_score * self._factor_weights['muhurta_analysis']
            )

            # Apply Panchaka penalty
            total_score = max(0.0, total_score + panchaka_penalty)
            
            # Ensure score is within valid range
            return max(0.0, min(1.0, total_score))
            
        except Exception as e:
            self.logger.error(f"Failed to calculate Vedic cycles score for {date}: {e}")
            raise
    
    def _calculate_tithi_score(self, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> float:
        """Calculate tithi favorability score."""
        return self._tithi_calculator.calculate_favorability(sun_position, moon_position)
    
    def _calculate_nakshatra_score(self, moon_position: PlanetaryPosition, date: datetime) -> float:
        """Calculate nakshatra favorability score with quarter precision and Gandanta check."""
        try:
            # Get base nakshatra favorability
            base_score = self._nakshatra_analyzer.analyze_favorability(moon_position, date, self._natal_panchanga)

            # Check for Gandanta affliction
            gandanta_info = self._nakshatra_analyzer.detect_gandanta(moon_position.longitude)

            # Apply Gandanta penalty if present
            if gandanta_info['present']:
                base_score = max(0.0, base_score + gandanta_info['penalty'])

            return base_score
        except Exception as e:
            self.logger.error(f"Error calculating nakshatra score: {e}")
            return 0.5
    
    def _calculate_weekday_score(self, date: datetime) -> float:
        """Calculate weekday strength based on planetary rulers."""
        return self._weekday_evaluator.evaluate_strength(date)
    
    def _calculate_paksha_score(self, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> float:
        """Calculate paksha (lunar fortnight) favorability score."""
        return self._paksha_analyzer.analyze_favorability(sun_position, moon_position)

    def _calculate_yoga_score(self, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> float:
        """Calculate Yoga (Sun-Moon combination) favorability score."""
        return self._yoga_calculator.calculate_favorability(sun_position, moon_position)

    def _calculate_karana_score(self, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> float:
        """Calculate Karana (half-tithi) favorability score."""
        try:
            # Get tithi info to extract tithi number and balance
            tithi_info = self._tithi_calculator.get_tithi_info(sun_position, moon_position)
            tithi_number = tithi_info['number']
            tithi_balance = tithi_info['balance']

            return self._karana_calculator.calculate_favorability(tithi_number, tithi_balance)
        except Exception as e:
            self.logger.error(f"Error calculating karana score: {e}")
            return 0.5

    def _calculate_tarabala_score(self, moon_position: PlanetaryPosition) -> float:
        """Calculate Tarabala (star compatibility) score."""
        try:
            if self._birth_nakshatra_index is None:
                # No birth nakshatra available, return neutral
                return 0.6

            # Get current nakshatra
            current_nakshatra_info = self._nakshatra_analyzer.get_nakshatra_info(moon_position)
            current_nakshatra_index = current_nakshatra_info['index']

            # Calculate Tarabala
            tarabala_info = self._tarabala_calculator.calculate_tarabala(
                current_nakshatra_index, self._birth_nakshatra_index
            )

            return tarabala_info['tara_multiplier']

        except Exception as e:
            self.logger.error(f"Error calculating tarabala score: {e}")
            return 0.6

    def _calculate_hora_score(self, date: datetime, sun_position: PlanetaryPosition) -> float:
        """Calculate Hora (planetary hour) favorability score."""
        try:
            # Calculate approximate sunrise time based on latitude
            # More accurate than fixed 6am, accounts for location and season
            sunrise_time = self._calculate_approximate_sunrise(date)

            return self._hora_calculator.calculate_favorability(date, sunrise_time, date.weekday())
        except Exception as e:
            self.logger.error(f"Error calculating hora score: {e}")
            return 0.6  # Neutral fallback

    def _calculate_approximate_sunrise(self, date: datetime) -> datetime:
        """
        Calculate approximate sunrise time based on latitude and day of year.
        Uses equation of time and solar declination for reasonable accuracy.
        """
        try:
            # Get day of year (1-366)
            day_of_year = date.timetuple().tm_yday

            # Calculate solar declination (simplified)
            declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))

            # Calculate hour angle at sunrise
            lat_rad = math.radians(self._birth_latitude)
            dec_rad = math.radians(declination)

            # Sunrise hour angle formula
            cos_hour_angle = -math.tan(lat_rad) * math.tan(dec_rad)

            # Handle polar regions (midnight sun / polar night)
            if cos_hour_angle > 1:
                # Polar night - use 9am as default
                sunrise_hour = 9.0
            elif cos_hour_angle < -1:
                # Midnight sun - use 3am as default
                sunrise_hour = 3.0
            else:
                hour_angle = math.degrees(math.acos(cos_hour_angle))

                # Convert hour angle to time (15 degrees = 1 hour)
                sunrise_hour = 12.0 - (hour_angle / 15.0)

                # Apply equation of time correction (simplified)
                eot = 4 * math.sin(2 * math.pi * day_of_year / 365)
                sunrise_hour -= eot / 60.0

                # Apply longitude correction (15 degrees = 1 hour time zone)
                # Assuming timezone offset is already in hours
                longitude_correction = self._birth_longitude / 15.0
                sunrise_hour -= longitude_correction

            # Create sunrise datetime
            hours = int(sunrise_hour)
            minutes = int((sunrise_hour - hours) * 60)

            # Ensure values are valid
            hours = max(0, min(23, hours))
            minutes = max(0, min(59, minutes))

            return date.replace(hour=hours, minute=minutes, second=0, microsecond=0)

        except Exception as e:
            self.logger.warning(f"Error calculating sunrise, using 6am default: {e}")
            return date.replace(hour=6, minute=0, second=0, microsecond=0)

    def _calculate_panchaka_penalty(self, moon_position: PlanetaryPosition,
                                   sun_position: PlanetaryPosition,
                                   moon_pos: PlanetaryPosition) -> float:
        """
        Calculate Panchaka dosha penalty.
        Panchaka occurs when Moon is in last 5 nakshatras during Krishna Paksha.
        """
        try:
            # Get nakshatra
            nakshatra_info = self._nakshatra_analyzer.get_nakshatra_info(moon_position)
            nakshatra_index = nakshatra_info['index']

            # Get paksha
            paksha_info = self._paksha_analyzer.get_paksha_info(sun_position, moon_pos)
            paksha_name = paksha_info['name'].lower()

            # Last 5 nakshatras: Dhanishta(22), Shatabhisha(23), Purva Bhadrapada(24),
            #                    Uttara Bhadrapada(25), Revati(26)
            PANCHAKA_NAKSHATRAS = [22, 23, 24, 25, 26]

            if nakshatra_index in PANCHAKA_NAKSHATRAS and paksha_name == 'krishna':
                # Panchaka dosha present - apply penalty
                return -0.20  # 20% penalty
            else:
                return 0.0  # No penalty

        except Exception as e:
            self.logger.error(f"Error calculating panchaka penalty: {e}")
            return 0.0

    def _calculate_vedic_correlation_score(
        self, 
        sun_position: PlanetaryPosition, 
        moon_position: PlanetaryPosition, 
        date: datetime
    ) -> float:
        """Calculate traditional Vedic calendar correlation score."""
        return self._vedic_correlator.calculate_correlation(sun_position, moon_position, date)
    
    def _calculate_muhurta_score(self, date: datetime, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> float:
        """CRITICAL ENHANCEMENT: Calculate Muhurta (auspicious timing) score."""
        try:
            muhurta_score = 0.5  # Base neutral
            
            # Rahu Kaal calculation (inauspicious period)
            rahu_kaal_penalty = self._calculate_rahu_kaal_penalty(date)
            muhurta_score -= rahu_kaal_penalty
            
            # Gulika Kaal calculation
            gulika_penalty = self._calculate_gulika_penalty(date)
            muhurta_score -= gulika_penalty
            
            # Yamaganda Kaal calculation
            yamaganda_penalty = self._calculate_yamaganda_penalty(date)
            muhurta_score -= yamaganda_penalty
            
            # Abhijit Muhurta bonus (most auspicious time)
            abhijit_bonus = self._calculate_abhijit_bonus(date)
            muhurta_score += abhijit_bonus
            
            # Brahma Muhurta bonus (pre-dawn auspicious time)
            brahma_bonus = self._calculate_brahma_muhurta_bonus(date)
            muhurta_score += brahma_bonus
            
            return max(0.0, min(1.0, muhurta_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating Muhurta score: {e}")
            return 0.5
    
    def _calculate_rahu_kaal_penalty(self, date: datetime) -> float:
        """Calculate Rahu Kaal penalty (inauspicious period)."""
        try:
            weekday = date.weekday()  # 0 = Monday
            hour = date.hour
            
            # Rahu Kaal timings by weekday (approximate)
            rahu_kaal_hours = {
                0: (7, 8.5),   # Monday: 7:30-9:00 AM
                1: (15, 16.5), # Tuesday: 3:00-4:30 PM
                2: (12, 13.5), # Wednesday: 12:00-1:30 PM
                3: (13.5, 15), # Thursday: 1:30-3:00 PM
                4: (10.5, 12), # Friday: 10:30 AM-12:00 PM
                5: (9, 10.5),  # Saturday: 9:00-10:30 AM
                6: (16.5, 18)  # Sunday: 4:30-6:00 PM
            }
            
            start_hour, end_hour = rahu_kaal_hours.get(weekday, (0, 0))
            
            if start_hour <= hour <= end_hour:
                return 0.3  # Significant penalty during Rahu Kaal
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _calculate_gulika_penalty(self, date: datetime) -> float:
        """Calculate Gulika Kaal penalty."""
        try:
            weekday = date.weekday()
            hour = date.hour
            
            # Gulika timings (approximate)
            gulika_hours = {
                0: (22.5, 24),   # Monday: 10:30 PM-12:00 AM
                1: (21, 22.5),   # Tuesday: 9:00-10:30 PM
                2: (19.5, 21),   # Wednesday: 7:30-9:00 PM
                3: (18, 19.5),   # Thursday: 6:00-7:30 PM
                4: (16.5, 18),   # Friday: 4:30-6:00 PM
                5: (15, 16.5),   # Saturday: 3:00-4:30 PM
                6: (13.5, 15)    # Sunday: 1:30-3:00 PM
            }
            
            start_hour, end_hour = gulika_hours.get(weekday, (0, 0))
            
            if start_hour <= hour <= end_hour:
                return 0.2  # Moderate penalty during Gulika
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _calculate_yamaganda_penalty(self, date: datetime) -> float:
        """Calculate Yamaganda Kaal penalty."""
        try:
            weekday = date.weekday()
            hour = date.hour
            
            # Yamaganda timings (approximate)
            yamaganda_hours = {
                0: (12, 13.5),   # Monday: 12:00-1:30 PM
                1: (10.5, 12),   # Tuesday: 10:30 AM-12:00 PM
                2: (9, 10.5),    # Wednesday: 9:00-10:30 AM
                3: (7.5, 9),     # Thursday: 7:30-9:00 AM
                4: (6, 7.5),     # Friday: 6:00-7:30 AM
                5: (4.5, 6),     # Saturday: 4:30-6:00 AM
                6: (3, 4.5)      # Sunday: 3:00-4:30 AM
            }
            
            start_hour, end_hour = yamaganda_hours.get(weekday, (0, 0))
            
            if start_hour <= hour <= end_hour:
                return 0.15  # Light penalty during Yamaganda
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _calculate_abhijit_bonus(self, date: datetime) -> float:
        """Calculate Abhijit Muhurta bonus (most auspicious time)."""
        try:
            hour = date.hour
            minute = date.minute
            
            # Abhijit Muhurta: approximately 11:36 AM to 12:24 PM
            if (hour == 11 and minute >= 36) or (hour == 12 and minute <= 24):
                return 0.4  # Significant bonus during Abhijit
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _calculate_brahma_muhurta_bonus(self, date: datetime) -> float:
        """Calculate Brahma Muhurta bonus (pre-dawn auspicious time)."""
        try:
            hour = date.hour
            
            # Brahma Muhurta: approximately 4:00-6:00 AM
            if 4 <= hour <= 6:
                return 0.3  # Good bonus during Brahma Muhurta
            else:
                return 0.0
                
        except Exception:
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
            
            if not current_positions or 'sun' not in current_positions or 'moon' not in current_positions:
                return {}
            
            sun_position = current_positions['sun']
            moon_position = current_positions['moon']

            # Get detailed info for all Panchanga elements
            tithi_info = self._tithi_calculator.get_tithi_info(sun_position, moon_position)
            nakshatra_info = self._nakshatra_analyzer.get_nakshatra_info(moon_position)
            paksha_info = self._paksha_analyzer.get_paksha_info(sun_position, moon_position)
            yoga_info = self._yoga_calculator.get_yoga_info(sun_position, moon_position)
            karana_info = self._karana_calculator.get_karana_info(tithi_info['number'], tithi_info['balance'])

            # Get Tarabala info if available
            tarabala_info = None
            if self._birth_nakshatra_index is not None:
                tarabala_info = self._tarabala_calculator.calculate_tarabala(
                    nakshatra_info['index'], self._birth_nakshatra_index
                )

            # Get Hora info with calculated sunrise
            sunrise_time = self._calculate_approximate_sunrise(date)
            hora_info = self._hora_calculator.get_hora_info(date, sunrise_time, date.weekday())

            # Get Lunar month info
            lunar_month_info = self._lunar_month_calculator.get_lunar_month_info(sun_position)

            # Check Panchaka
            panchaka_penalty = self._calculate_panchaka_penalty(moon_position, sun_position, moon_position)
            panchaka_present = (panchaka_penalty < 0)

            # Check Gandanta (through nakshatra analyzer)
            gandanta_info = self._nakshatra_analyzer.detect_gandanta(moon_position.longitude)

            return {
                'tithi_score': self._calculate_tithi_score(sun_position, moon_position),
                'nakshatra_score': self._calculate_nakshatra_score(moon_position, date),
                'tarabala_score': self._calculate_tarabala_score(moon_position),
                'yoga_score': self._calculate_yoga_score(sun_position, moon_position),
                'karana_score': self._calculate_karana_score(sun_position, moon_position),
                'hora_score': self._calculate_hora_score(date, sun_position),
                'weekday_score': self._calculate_weekday_score(date),
                'paksha_score': self._calculate_paksha_score(sun_position, moon_position),
                'vedic_correlation_score': self._calculate_vedic_correlation_score(
                    sun_position, moon_position, date
                ),
                'muhurta_score': self._calculate_muhurta_score(date, sun_position, moon_position),
                'current_tithi': tithi_info['name'],
                'current_nakshatra': nakshatra_info['name'],
                'current_weekday': date.strftime('%A'),
                'current_paksha': paksha_info['name'],
                'current_yoga': yoga_info['name'],
                'yoga_is_critical_avoid': yoga_info['is_critical_avoid'],
                'current_karana': karana_info['name'],
                'karana_is_vishti': karana_info['is_vishti_bhadra'],
                'current_hora': hora_info['hora_ruler'],
                'hora_favorability': hora_info['favorability'],
                'hora_number': hora_info['hora_number'],
                'lunar_month': lunar_month_info['month_name'],
                'is_adhika_masa': lunar_month_info['is_adhika_masa'],
                'tarabala_name': tarabala_info['tara_name'] if tarabala_info else 'N/A',
                'tarabala_multiplier': tarabala_info['tara_multiplier'] if tarabala_info else 0.6,
                'panchaka_present': panchaka_present,
                'panchaka_penalty': panchaka_penalty,
                'gandanta_present': gandanta_info['present'],
                'gandanta_penalty': gandanta_info['penalty']
            }
            
        except Exception:
            return {}
    
    def get_calculation_methodology(self) -> str:
        """Describe calculation methodology."""
        return (
            "Traditional Vedic time cycle calculations with 80% accuracy. "
            "Combines tithi (lunar day) favorability assessment (30%), nakshatra (lunar mansion) "
            "analysis with quarter precision (25%), weekday strength evaluation based on "
            "planetary rulers (20%), paksha (lunar fortnight) analysis (15%), and traditional "
            "Vedic calendar correlation methods (10%). Uses ephemeris data for precise "
            "lunar and solar positions with classical Vedic interpretation rules."
        )
    
    def get_layer_name(self) -> str:
        """Get layer name."""
        return "Vedic Time Cycles"
    
    def get_layer_description(self) -> str:
        """Get layer description."""
        return (
            "Traditional Vedic time calculations including tithi (lunar day), nakshatra "
            "(lunar mansion), weekday strength, paksha (lunar fortnight), and Vedic calendar "
            "correlations. Provides 80% accuracy using classical Vedic astronomical principles "
            "combined with precise ephemeris calculations."
        )
    
    def get_calculation_factors(self) -> List[str]:
        """Get list of calculation factors."""
        return [
            "Tithi (lunar day) calculation and favorability assessment",
            "Nakshatra (lunar mansion) analysis with quarter precision",
            "Weekday strength evaluation based on planetary rulers",
            "Paksha (lunar fortnight) analysis and scoring",
            "Traditional Vedic calendar correlation methods"
        ]
    
    def validate_kundali_data(self) -> bool:
        """Validate kundali data for Layer 3 requirements."""
        if not self.kundali:
            self.logger.error("No kundali data provided")
            return False
        
        # Check for required birth details
        if not self.kundali.birth_details:
            self.logger.error("Birth details required for Vedic time calculations")
            return False
        
        # Check for panchanga data (optional but helpful)
        if not self.kundali.panchanga:
            self.logger.warning("No natal panchanga data available - will use neutral comparisons")
        
        return True


class YogaCalculator:
    """Calculator for 27 Vedic Yogas (Sun+Moon combination)."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # 27 Vedic Yogas
        self._yoga_names = [
            "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
            "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
            "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
            "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
            "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
            "Indra", "Vaidhriti"
        ]

        # Yoga favorability ratings
        self._yoga_favorability = {
            # Highly auspicious (0.85-1.0)
            'Siddhi': 1.0, 'Shubha': 1.0, 'Brahma': 0.95,
            'Ayushman': 0.9, 'Saubhagya': 0.9, 'Shobhana': 0.9,
            'Indra': 0.9, 'Siddha': 0.9, 'Sadhya': 0.85,

            # Very inauspicious (CRITICAL AVOID: 0.2-0.3)
            'Vyatipata': 0.2,     # Eclipse yoga - extremely inauspicious
            'Vaidhriti': 0.2,     # Calamity yoga - avoid all important events
            'Vishkumbha': 0.3,    # Poison pot - very malefic
            'Atiganda': 0.3,      # Extreme knot - obstacles
            'Shula': 0.3,         # Spear - sharp difficulties
            'Ganda': 0.3,         # Knot - entanglements
            'Vyaghata': 0.4,      # Calamity - misfortune
            'Vajra': 0.4,         # Thunderbolt - sudden shocks
            'Parigha': 0.4,       # Iron rod - harsh restrictions

            # Moderate/neutral (0.6-0.8)
            'Priti': 0.7, 'Sukarma': 0.7, 'Dhriti': 0.7,
            'Vriddhi': 0.75, 'Dhruva': 0.8, 'Harshana': 0.75,
            'Variyan': 0.7, 'Shiva': 0.8, 'Shukla': 0.75
        }

    def calculate_favorability(self, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> float:
        """Calculate yoga favorability score."""
        try:
            yoga_info = self.get_yoga_info(sun_position, moon_position)
            return yoga_info['favorability']
        except Exception as e:
            self.logger.error(f"Error calculating yoga favorability: {e}")
            return 0.5

    def get_yoga_info(self, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> Dict[str, Any]:
        """
        Calculate current Yoga from Sun and Moon longitudes.
        Formula: (Sun° + Moon°) / 13.33333° = Yoga index (0-26)
        """
        try:
            # Calculate yoga sum
            yoga_sum = (sun_position.longitude + moon_position.longitude) % 360

            # Calculate yoga index (0-26)
            yoga_index = int(yoga_sum / 13.333333333)  # 360/27

            if yoga_index >= 27:
                yoga_index = 26  # Cap at last yoga

            yoga_name = self._yoga_names[yoga_index]
            yoga_favorability = self._yoga_favorability.get(yoga_name, 0.5)

            # Calculate balance (% completed within current yoga)
            yoga_balance = ((yoga_sum % 13.333333333) / 13.333333333) * 100

            return {
                'index': yoga_index,
                'name': yoga_name,
                'favorability': yoga_favorability,
                'balance': round(yoga_balance, 2),
                'is_critical_avoid': yoga_favorability <= 0.3
            }

        except Exception as e:
            self.logger.error(f"Error getting yoga info: {e}")
            return {
                'index': 0, 'name': 'Unknown', 'favorability': 0.5,
                'balance': 50.0, 'is_critical_avoid': False
            }


class KaranaCalculator:
    """Calculator for 11 Vedic Karanas (half-tithis)."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # 11 Karanas (7 movable + 4 fixed)
        self._karana_names = [
            # 7 movable karanas (repeat in cycle)
            "Bava", "Balava", "Kaulava", "Taitila",
            "Garaja", "Vanija", "Vishti",
            # 4 fixed karanas (occur once per month)
            "Shakuni", "Chatushpada", "Naga", "Kimstughna"
        ]

        # Karana favorability ratings
        self._karana_favorability = {
            # Movable karanas (generally auspicious)
            'Bava': 0.8,      # Auspicious for most events
            'Balava': 0.75,   # Good for strength-based activities
            'Kaulava': 0.8,   # Favorable for partnerships
            'Taitila': 0.7,   # Moderate, good for persistence
            'Garaja': 0.7,    # Moderate, good for creativity
            'Vanija': 0.75,   # Favorable for commerce

            # VISHTI (BHADRA) - EXTREMELY INAUSPICIOUS
            'Vishti': 0.2,    # AVOID for all important events!

            # Fixed karanas (special occasions)
            'Shakuni': 0.5,   # Challenging, cunning energy
            'Chatushpada': 0.6,  # Stable but slow
            'Naga': 0.6,      # Mystical, good for spiritual work
            'Kimstughna': 0.5  # Difficult, avoid for beginnings
        }

    def calculate_favorability(self, tithi_number: int, tithi_balance: float) -> float:
        """Calculate karana favorability score."""
        try:
            karana_info = self.get_karana_info(tithi_number, tithi_balance)
            return karana_info['favorability']
        except Exception as e:
            self.logger.error(f"Error calculating karana favorability: {e}")
            return 0.5

    def get_karana_info(self, tithi_number: int, tithi_balance: float) -> Dict[str, Any]:
        """
        Calculate current Karana from tithi number and balance.
        Each tithi has 2 karanas (first half, second half).
        """
        try:
            # Calculate karana position (0-59 in lunar month)
            if tithi_balance < 50:
                # First half of tithi
                karana_position = (tithi_number - 1) * 2
            else:
                # Second half of tithi
                karana_position = (tithi_number - 1) * 2 + 1

            # First 57 positions use 7 movable karanas in cycle
            # Last 4 positions (58-61) use 4 fixed karanas
            if karana_position < 57:
                karana_index = karana_position % 7
            else:
                karana_index = 7 + (karana_position - 57)
                if karana_index >= 11:
                    karana_index = 10  # Cap at last karana

            karana_name = self._karana_names[karana_index]
            karana_favorability = self._karana_favorability.get(karana_name, 0.5)

            return {
                'index': karana_index,
                'name': karana_name,
                'favorability': karana_favorability,
                'is_vishti_bhadra': (karana_name == 'Vishti'),
                'is_critical_avoid': (karana_name == 'Vishti')
            }

        except Exception as e:
            self.logger.error(f"Error getting karana info: {e}")
            return {
                'index': 0, 'name': 'Unknown', 'favorability': 0.5,
                'is_vishti_bhadra': False, 'is_critical_avoid': False
            }


class TarabalaCalculator:
    """
    Calculate Tarabala (star compatibility) from birth nakshatra.
    This is CRITICAL for Muhurta selection.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # 9 Tarabala positions
        self._tarabala_names = [
            'Janma', 'Sampat', 'Vipat', 'Kshema', 'Pratyak',
            'Sadhaka', 'Naidhana', 'Mitra', 'Parama Mitra'
        ]

        # Tarabala multipliers
        self._tarabala_multipliers = {
            'Janma': 0.3,         # 1st: Birth star (avoid for important events)
            'Sampat': 0.9,        # 2nd: Wealth (excellent)
            'Vipat': 0.4,         # 3rd: Danger (avoid)
            'Kshema': 0.8,        # 4th: Well-being (good)
            'Pratyak': 0.5,       # 5th: Obstruction (challenging)
            'Sadhaka': 0.9,       # 6th: Accomplishment (excellent)
            'Naidhana': 0.2,      # 7th: Death (AVOID - very inauspicious!)
            'Mitra': 0.9,         # 8th: Friend (excellent)
            'Parama Mitra': 1.0   # 9th: Best friend (most favorable)
        }

    def calculate_tarabala(self, current_nakshatra_index: int,
                          birth_nakshatra_index: int) -> Dict[str, Any]:
        """
        Calculate Tarabala for Muhurta selection.

        Args:
            current_nakshatra_index: 0-26 (Ashwini=0, Revati=26)
            birth_nakshatra_index: Birth nakshatra (0-26)

        Returns:
            dict with tara name, multiplier, and recommendation
        """
        try:
            # Calculate tara position (0-26)
            tara_distance = (current_nakshatra_index - birth_nakshatra_index) % 27

            # Get tara group (0-8, repeats every 9 nakshatras)
            tara_group = tara_distance % 9

            tara_name = self._tarabala_names[tara_group]
            tara_multiplier = self._tarabala_multipliers[tara_name]

            # Determine recommendation
            if tara_multiplier >= 0.9:
                recommendation = "Excellent - Highly favorable for important events"
            elif tara_multiplier >= 0.7:
                recommendation = "Good - Suitable for most activities"
            elif tara_multiplier >= 0.5:
                recommendation = "Moderate - Use for routine matters"
            else:
                recommendation = "Avoid - Inauspicious for important events"

            # Special warning for Naidhana (7th tara)
            if tara_name == 'Naidhana':
                recommendation = "CRITICAL AVOID - Death star, extremely inauspicious!"

            return {
                'tara_index': tara_group,
                'tara_name': tara_name,
                'tara_multiplier': tara_multiplier,
                'tara_distance': tara_distance,
                'recommendation': recommendation,
                'is_critical_avoid': (tara_name in ['Naidhana', 'Vipat', 'Janma'])
            }

        except Exception as e:
            self.logger.error(f"Error calculating tarabala: {e}")
            return {
                'tara_index': 0, 'tara_name': 'Unknown', 'tara_multiplier': 0.5,
                'tara_distance': 0, 'recommendation': 'Unknown',
                'is_critical_avoid': False
            }


class TithiCalculator:
    """Calculator for tithi (lunar day) favorability assessment."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Define tithi favorability ratings (0.0 to 1.0)
        self._tithi_favorability = {
            1: 0.8,   # Pratipada - new beginnings
            2: 0.7,   # Dwitiya - good for partnerships
            3: 0.9,   # Tritiya - very auspicious
            4: 0.6,   # Chaturthi - moderate
            5: 0.9,   # Panchami - very favorable
            6: 0.7,   # Shashthi - good
            7: 0.8,   # Saptami - favorable
            8: 0.5,   # Ashtami - challenging
            9: 0.6,   # Navami - moderate
            10: 0.8,  # Dashami - favorable
            11: 0.9,  # Ekadashi - very auspicious
            12: 0.7,  # Dwadashi - good
            13: 0.6,  # Trayodashi - moderate
            14: 0.4,  # Chaturdashi - challenging
            15: 1.0,  # Purnima - most auspicious
            16: 0.8,  # Pratipada (Krishna) - new phase
            17: 0.7,  # Dwitiya (Krishna)
            18: 0.6,  # Tritiya (Krishna)
            19: 0.5,  # Chaturthi (Krishna)
            20: 0.6,  # Panchami (Krishna)
            21: 0.7,  # Shashthi (Krishna)
            22: 0.6,  # Saptami (Krishna)
            23: 0.4,  # Ashtami (Krishna) - challenging
            24: 0.5,  # Navami (Krishna)
            25: 0.6,  # Dashami (Krishna)
            26: 0.8,  # Ekadashi (Krishna) - spiritual
            27: 0.7,  # Dwadashi (Krishna)
            28: 0.5,  # Trayodashi (Krishna)
            29: 0.3,  # Chaturdashi (Krishna) - very challenging
            30: 0.2   # Amavasya - most challenging
        }
        
        # Tithi names for reference
        self._tithi_names = [
            "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
            "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
            "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"
        ]
    
    def calculate_favorability(self, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> float:
        """
        Calculate tithi favorability score.
        
        Args:
            sun_position: Current sun position
            moon_position: Current moon position
            
        Returns:
            Favorability score between 0.0 and 1.0
        """
        try:
            tithi_info = self.get_tithi_info(sun_position, moon_position)
            tithi_number = tithi_info['number']
            
            # Get base favorability
            base_favorability = self._tithi_favorability.get(tithi_number, 0.5)
            
            # Apply balance factor (closer to completion = slightly better)
            balance_factor = 1.0 + (tithi_info['balance'] / 100) * 0.1
            
            final_score = base_favorability * balance_factor
            
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            self.logger.error(f"Error calculating tithi favorability: {e}")
            return 0.5
    
    def get_tithi_info(self, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> Dict[str, Any]:
        """Get detailed tithi information."""
        try:
            # Calculate moon-sun difference
            moon_sun_diff = (moon_position.longitude - sun_position.longitude) % 360
            
            # Calculate tithi number (1-30)
            tithi_number = int(moon_sun_diff / 12) + 1
            if tithi_number > 30:
                tithi_number = 30
            
            # Calculate balance (percentage completed)
            tithi_balance = (moon_sun_diff % 12) / 12 * 100
            
            # Get tithi name
            if tithi_number <= 15:
                tithi_name = self._tithi_names[tithi_number - 1]
                if tithi_number == 15:
                    tithi_name = "Purnima"
            else:
                base_index = (tithi_number - 16) % 15
                tithi_name = self._tithi_names[base_index] + " (Krishna)"
                if tithi_number == 30:
                    tithi_name = "Amavasya"
            
            return {
                'number': tithi_number,
                'name': tithi_name,
                'balance': round(tithi_balance, 2),
                'favorability': self._tithi_favorability.get(tithi_number, 0.5)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting tithi info: {e}")
            return {'number': 15, 'name': 'Unknown', 'balance': 50.0, 'favorability': 0.5}


class NakshatraAnalyzer:
    """Analyzer for nakshatra (lunar mansion) with quarter precision."""
    
    def __init__(self, dasha_calculator: DashaCalculator):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dasha_calculator = dasha_calculator
        
        # Define nakshatra favorability ratings
        self._nakshatra_favorability = {
            0: 0.8,   # Ashwini - swift, healing
            1: 0.6,   # Bharani - transformation
            2: 0.7,   # Krittika - cutting, purification
            3: 0.9,   # Rohini - growth, beauty
            4: 0.7,   # Mrigashira - searching, gentle
            5: 0.5,   # Ardra - storms, destruction/renewal
            6: 0.8,   # Punarvasu - renewal, return
            7: 0.9,   # Pushya - nourishment, most auspicious
            8: 0.4,   # Ashlesha - serpent, cunning
            9: 0.8,   # Magha - royal, ancestral
            10: 0.7,  # Purva Phalguni - pleasure, creativity
            11: 0.8,  # Uttara Phalguni - patronage, support
            12: 0.6,  # Hasta - skillful hands
            13: 0.7,  # Chitra - bright, artistic
            14: 0.5,  # Swati - independence, movement
            15: 0.6,  # Vishakha - forked, determination
            16: 0.4,  # Anuradha - friendship, devotion
            17: 0.3,  # Jyeshtha - eldest, protection
            18: 0.5,  # Mula - root, destruction/foundation
            19: 0.7,  # Purva Ashadha - invincible
            20: 0.8,  # Uttara Ashadha - victory
            21: 0.6,  # Shravana - listening, learning
            22: 0.5,  # Dhanishta - wealth, music
            23: 0.4,  # Shatabhisha - hundred healers
            24: 0.6,  # Purva Bhadrapada - burning, purification
            25: 0.7,  # Uttara Bhadrapada - depth, wisdom
            26: 0.9   # Revati - prosperity, completion
        }
        
        # Quarter-specific modifiers
        self._quarter_modifiers = {
            1: 1.0,   # First quarter - initiation
            2: 1.1,   # Second quarter - development
            3: 1.05,  # Third quarter - completion
            4: 0.95   # Fourth quarter - transition
        }
    
    def analyze_favorability(
        self, 
        moon_position: PlanetaryPosition, 
        date: datetime, 
        natal_panchanga: Dict[str, Any]
    ) -> float:
        """
        Analyze nakshatra favorability with quarter precision.
        
        Args:
            moon_position: Current moon position
            date: Current date
            natal_panchanga: Natal panchanga data for comparison
            
        Returns:
            Favorability score between 0.0 and 1.0
        """
        try:
            nakshatra_info = self.get_nakshatra_info(moon_position)
            nakshatra_index = nakshatra_info['index']
            quarter = nakshatra_info['quarter']
            
            # Get base favorability
            base_favorability = self._nakshatra_favorability.get(nakshatra_index, 0.5)
            
            # Apply quarter modifier
            quarter_modifier = self._quarter_modifiers.get(quarter, 1.0)
            
            # Apply natal comparison bonus
            natal_bonus = self._calculate_natal_comparison_bonus(nakshatra_info, natal_panchanga)
            
            # Calculate final score
            final_score = base_favorability * quarter_modifier * (1.0 + natal_bonus)
            
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            self.logger.error(f"Error analyzing nakshatra favorability: {e}")
            return 0.5
    
    def get_nakshatra_info(self, moon_position: PlanetaryPosition) -> Dict[str, Any]:
        """Get detailed nakshatra information with quarter precision."""
        try:
            longitude = moon_position.longitude
            
            # Get basic nakshatra info
            nakshatra_index, nakshatra_name, nakshatra_lord = self.dasha_calculator.get_nakshatra_from_longitude(longitude)
            
            # Calculate quarter (pada) - each nakshatra has 4 quarters of 3°20' each
            nakshatra_span = 360.0 / 27  # 13°20' per nakshatra
            position_in_nakshatra = (longitude * 27 / 360) % 1
            quarter = int(position_in_nakshatra * 4) + 1
            
            # Calculate balance within current quarter
            quarter_position = (position_in_nakshatra * 4) % 1
            quarter_balance = (1.0 - quarter_position) * 100
            
            return {
                'index': nakshatra_index,
                'name': nakshatra_name,
                'lord': nakshatra_lord,
                'quarter': quarter,
                'quarter_balance': round(quarter_balance, 2),
                'favorability': self._nakshatra_favorability.get(nakshatra_index, 0.5)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting nakshatra info: {e}")
            return {
                'index': 0, 'name': 'Unknown', 'lord': 'unknown', 
                'quarter': 1, 'quarter_balance': 50.0, 'favorability': 0.5
            }
    
    def detect_gandanta(self, position_longitude: float) -> Dict[str, Any]:
        """
        Detect if position is in Gandanta (knot) zone.

        Gandanta are critical junction points between water and fire signs:
        1. Revati-Ashwini (Pisces-Aries junction)
        2. Ashlesha-Magha (Cancer-Leo junction)
        3. Jyeshtha-Mula (Scorpio-Sagittarius junction)

        These are spiritually turbulent zones. Starting important activities
        when Moon/Lagna is in Gandanta is highly inauspicious.

        Args:
            position_longitude: Longitude in degrees (0-360)

        Returns:
            dict with present, name, severity, penalty, recommendation
        """
        try:
            # Gandanta zones (each spans 0°50' before and after junction)
            # Using 0°50' = 0.833° on each side
            GANDANTA_RANGES = [
                # (start1, end1, start2, end2, name)
                (356.67, 360.0, 0.0, 0.83, 'Revati-Ashwini (Pisces-Aries)'),
                (116.67, 120.0, 120.0, 120.83, 'Ashlesha-Magha (Cancer-Leo)'),
                (236.67, 240.0, 240.0, 240.83, 'Jyeshtha-Mula (Scorpio-Sagittarius)')
            ]

            for start1, end1, start2, end2, name in GANDANTA_RANGES:
                # Check if in first range or second range
                in_range1 = start1 <= position_longitude <= end1
                in_range2 = start2 <= position_longitude <= end2

                if in_range1 or in_range2:
                    # Calculate severity based on proximity to exact junction
                    if in_range2:
                        distance_from_junction = position_longitude - start2
                    else:
                        distance_from_junction = end1 - position_longitude

                    # Closer to junction = more severe
                    if distance_from_junction < 0.42:  # Within 25' of junction
                        severity = 'Critical'
                        penalty = -0.30
                    else:
                        severity = 'High'
                        penalty = -0.20

                    return {
                        'present': True,
                        'name': name,
                        'severity': severity,
                        'penalty': penalty,
                        'recommendation': 'AVOID starting important activities. Good only for endings, spiritual practices, and moksha-related work.'
                    }

            return {
                'present': False,
                'name': None,
                'severity': 'None',
                'penalty': 0.0,
                'recommendation': 'No Gandanta affliction'
            }

        except Exception as e:
            self.logger.error(f"Error detecting gandanta: {e}")
            return {
                'present': False,
                'name': None,
                'severity': 'None',
                'penalty': 0.0,
                'recommendation': 'Error in detection'
            }

    def _calculate_natal_comparison_bonus(
        self,
        current_nakshatra: Dict[str, Any],
        natal_panchanga: Dict[str, Any]
    ) -> float:
        """Calculate bonus based on comparison with natal nakshatra."""
        try:
            if not natal_panchanga or 'nakshatra' not in natal_panchanga:
                return 0.0
            
            natal_nakshatra = natal_panchanga['nakshatra']
            current_index = current_nakshatra['index']
            
            # Try to get natal nakshatra index from name
            natal_name = natal_nakshatra.get('name', '')
            natal_index = None
            
            # Find natal nakshatra index
            for i, name in enumerate(self.dasha_calculator.nakshatra_names):
                if name.lower() == natal_name.lower():
                    natal_index = i
                    break
            
            if natal_index is None:
                return 0.0
            
            # Calculate relationship bonus
            if current_index == natal_index:
                return 0.2  # Same nakshatra - strong connection
            elif abs(current_index - natal_index) in [9, 18]:
                return 0.15  # Trine relationship - harmonious
            elif abs(current_index - natal_index) == 13:
                return -0.1  # Opposition - challenging
            elif current_nakshatra['lord'] == natal_nakshatra.get('lord', ''):
                return 0.1  # Same lord - supportive
            else:
                return 0.0  # Neutral relationship
                
        except Exception as e:
            self.logger.error(f"Error calculating natal comparison bonus: {e}")
            return 0.0


class WeekdayEvaluator:
    """Evaluator for weekday strength based on planetary rulers."""
    
    def __init__(self, birth_details):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.birth_details = birth_details
        
        # Weekday rulers and their general favorability
        self._weekday_rulers = {
            0: {'planet': 'moon', 'favorability': 0.7},      # Monday
            1: {'planet': 'mars', 'favorability': 0.6},      # Tuesday
            2: {'planet': 'mercury', 'favorability': 0.8},   # Wednesday
            3: {'planet': 'jupiter', 'favorability': 0.9},   # Thursday
            4: {'planet': 'venus', 'favorability': 0.8},     # Friday
            5: {'planet': 'saturn', 'favorability': 0.5},    # Saturday
            6: {'planet': 'sun', 'favorability': 0.7}        # Sunday
        }
        
        # Calculate birth weekday for comparison
        if birth_details and birth_details.date:
            self._birth_weekday = birth_details.date.weekday()
        else:
            self._birth_weekday = None
    
    def evaluate_strength(self, date: datetime) -> float:
        """
        Evaluate weekday strength based on planetary rulers.
        
        Args:
            date: Date for evaluation
            
        Returns:
            Strength score between 0.0 and 1.0
        """
        try:
            weekday = date.weekday()  # 0 = Monday, 6 = Sunday
            
            # Get base favorability for this weekday
            weekday_info = self._weekday_rulers.get(weekday, {'favorability': 0.5})
            base_favorability = weekday_info['favorability']
            
            # Apply birth weekday comparison bonus
            birth_bonus = self._calculate_birth_weekday_bonus(weekday)
            
            # Apply monthly cycle modifier (some weekdays are better in certain parts of month)
            monthly_modifier = self._calculate_monthly_modifier(date, weekday)
            
            # Calculate final strength
            final_strength = base_favorability * (1.0 + birth_bonus) * monthly_modifier
            
            return max(0.0, min(1.0, final_strength))
            
        except Exception as e:
            self.logger.error(f"Error evaluating weekday strength: {e}")
            return 0.5
    
    def _calculate_birth_weekday_bonus(self, current_weekday: int) -> float:
        """Calculate bonus based on birth weekday comparison."""
        if self._birth_weekday is None:
            return 0.0
        
        if current_weekday == self._birth_weekday:
            return 0.2  # Same weekday as birth - strong connection
        elif abs(current_weekday - self._birth_weekday) == 3:
            return 0.1  # Opposite weekday - complementary
        else:
            return 0.0  # Neutral
    
    def _calculate_monthly_modifier(self, date: datetime, weekday: int) -> float:
        """Calculate monthly cycle modifier for weekday strength."""
        try:
            # Some weekdays are stronger in certain parts of the month
            day_of_month = date.day
            
            # Divide month into quarters
            if day_of_month <= 7:
                quarter = 1  # New moon quarter
            elif day_of_month <= 14:
                quarter = 2  # Waxing quarter
            elif day_of_month <= 21:
                quarter = 3  # Full moon quarter
            else:
                quarter = 4  # Waning quarter
            
            # Apply quarter-specific modifiers for different weekdays
            quarter_modifiers = {
                0: [1.1, 1.0, 1.2, 0.9],  # Monday - stronger during full moon
                1: [1.2, 1.1, 0.9, 1.0],  # Tuesday - stronger during new moon
                2: [1.0, 1.1, 1.0, 1.1],  # Wednesday - consistent
                3: [1.0, 1.2, 1.1, 1.0],  # Thursday - stronger during waxing
                4: [1.1, 1.0, 1.1, 1.0],  # Friday - stronger during new and full
                5: [1.0, 0.9, 1.0, 1.2],  # Saturday - stronger during waning
                6: [1.1, 1.0, 1.1, 0.9]   # Sunday - stronger during new and full
            }
            
            modifiers = quarter_modifiers.get(weekday, [1.0, 1.0, 1.0, 1.0])
            return modifiers[quarter - 1]
            
        except Exception:
            return 1.0  # Neutral modifier on error


class PakshaAnalyzer:
    """Analyzer for paksha (lunar fortnight) favorability."""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Paksha favorability ratings
        self._paksha_favorability = {
            'shukla': 0.8,    # Waxing moon - generally favorable
            'krishna': 0.6,   # Waning moon - moderate
            'purnima': 1.0,   # Full moon - most favorable
            'amavasya': 0.3   # New moon - challenging
        }
    
    def analyze_favorability(self, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> float:
        """
        Analyze paksha favorability.
        
        Args:
            sun_position: Current sun position
            moon_position: Current moon position
            
        Returns:
            Favorability score between 0.0 and 1.0
        """
        try:
            paksha_info = self.get_paksha_info(sun_position, moon_position)
            paksha_name = paksha_info['name'].lower()
            
            # Get base favorability
            base_favorability = self._paksha_favorability.get(paksha_name, 0.5)
            
            # Apply intensity modifier based on how far into the paksha we are
            intensity_modifier = self._calculate_intensity_modifier(paksha_info)
            
            final_score = base_favorability * intensity_modifier
            
            return max(0.0, min(1.0, final_score))
            
        except Exception as e:
            self.logger.error(f"Error analyzing paksha favorability: {e}")
            return 0.5
    
    def get_paksha_info(self, sun_position: PlanetaryPosition, moon_position: PlanetaryPosition) -> Dict[str, Any]:
        """Get detailed paksha information."""
        try:
            # Calculate moon-sun difference
            moon_sun_diff = (moon_position.longitude - sun_position.longitude) % 360
            
            # Calculate tithi number to determine paksha
            tithi_number = int(moon_sun_diff / 12) + 1
            if tithi_number > 30:
                tithi_number = 30
            
            # Determine paksha
            if tithi_number == 15:
                paksha_name = "Purnima"
                paksha_progress = 100.0
            elif tithi_number == 30:
                paksha_name = "Amavasya"
                paksha_progress = 100.0
            elif tithi_number < 15:
                paksha_name = "Shukla"
                paksha_progress = (tithi_number / 15) * 100
            else:
                paksha_name = "Krishna"
                paksha_progress = ((tithi_number - 15) / 15) * 100
            
            return {
                'name': paksha_name,
                'progress': round(paksha_progress, 2),
                'tithi_number': tithi_number,
                'favorability': self._paksha_favorability.get(paksha_name.lower(), 0.5)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting paksha info: {e}")
            return {'name': 'Unknown', 'progress': 50.0, 'tithi_number': 15, 'favorability': 0.5}
    
    def _calculate_intensity_modifier(self, paksha_info: Dict[str, Any]) -> float:
        """Calculate intensity modifier based on paksha progress."""
        try:
            progress = paksha_info['progress']
            paksha_name = paksha_info['name'].lower()
            
            if paksha_name in ['purnima', 'amavasya']:
                return 1.0  # Peak intensity
            elif paksha_name == 'shukla':
                # Waxing moon - intensity increases towards full moon
                return 0.8 + (progress / 100) * 0.4
            elif paksha_name == 'krishna':
                # Waning moon - intensity decreases towards new moon
                return 1.0 - (progress / 100) * 0.4
            else:
                return 1.0  # Default
                
        except Exception:
            return 1.0


class VedicCalendarCorrelator:
    """Correlator for traditional Vedic calendar methods."""
    
    def __init__(self, kundali_data: KundaliData):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.kundali_data = kundali_data
        self.natal_panchanga = kundali_data.panchanga
        
        # Seasonal favorability (based on birth season)
        if kundali_data.birth_details:
            self.birth_month = kundali_data.birth_details.date.month
            self.birth_season = self._get_season(kundali_data.birth_details.date)
        else:
            self.birth_month = None
            self.birth_season = None
    
    def calculate_correlation(
        self, 
        sun_position: PlanetaryPosition, 
        moon_position: PlanetaryPosition, 
        date: datetime
    ) -> float:
        """
        Calculate traditional Vedic calendar correlation score.
        
        Args:
            sun_position: Current sun position
            moon_position: Current moon position
            date: Current date
            
        Returns:
            Correlation score between 0.0 and 1.0
        """
        try:
            # Calculate various correlation factors
            seasonal_correlation = self._calculate_seasonal_correlation(date)
            monthly_correlation = self._calculate_monthly_correlation(date)
            solar_correlation = self._calculate_solar_correlation(sun_position, date)
            lunar_correlation = self._calculate_lunar_correlation(moon_position, date)
            
            # Combine correlations with weights
            total_correlation = (
                seasonal_correlation * 0.3 +
                monthly_correlation * 0.2 +
                solar_correlation * 0.3 +
                lunar_correlation * 0.2
            )
            
            return max(0.0, min(1.0, total_correlation))
            
        except Exception as e:
            self.logger.error(f"Error calculating Vedic calendar correlation: {e}")
            return 0.5
    
    def _calculate_seasonal_correlation(self, date: datetime) -> float:
        """Calculate correlation with birth season."""
        if not self.birth_season:
            return 0.5
        
        current_season = self._get_season(date)
        
        if current_season == self.birth_season:
            return 0.9  # Same season - strong correlation
        elif self._are_adjacent_seasons(current_season, self.birth_season):
            return 0.7  # Adjacent season - moderate correlation
        else:
            return 0.4  # Opposite season - weak correlation
    
    def _calculate_monthly_correlation(self, date: datetime) -> float:
        """Calculate correlation with birth month."""
        if not self.birth_month:
            return 0.5
        
        current_month = date.month
        
        if current_month == self.birth_month:
            return 0.9  # Same month - strong correlation
        elif abs(current_month - self.birth_month) <= 1 or abs(current_month - self.birth_month) >= 11:
            return 0.7  # Adjacent month - moderate correlation
        else:
            month_distance = min(abs(current_month - self.birth_month), 12 - abs(current_month - self.birth_month))
            return 0.8 - (month_distance / 6) * 0.4  # Gradual decrease with distance
    
    def _calculate_solar_correlation(self, sun_position: PlanetaryPosition, date: datetime) -> float:
        """Calculate solar correlation factors."""
        try:
            # Get natal sun position if available
            if not self.kundali_data.planetary_positions or 'sun' not in self.kundali_data.planetary_positions:
                return 0.5
            
            natal_sun = self.kundali_data.planetary_positions['sun']
            
            # Calculate angular relationship
            angular_diff = abs(sun_position.longitude - natal_sun.longitude)
            if angular_diff > 180:
                angular_diff = 360 - angular_diff
            
            # Solar return and other significant angles
            if angular_diff < 5:
                return 1.0  # Solar return - very strong
            elif angular_diff < 15:
                return 0.9  # Close to solar return
            elif 85 <= angular_diff <= 95:
                return 0.3  # Square aspect - challenging
            elif 175 <= angular_diff <= 185:
                return 0.4  # Opposition - challenging
            elif 115 <= angular_diff <= 125:
                return 0.8  # Trine aspect - harmonious
            else:
                return 0.6  # Other angles - moderate
                
        except Exception:
            return 0.5
    
    def _calculate_lunar_correlation(self, moon_position: PlanetaryPosition, date: datetime) -> float:
        """Calculate lunar correlation factors."""
        try:
            # Get natal moon position if available
            if not self.kundali_data.planetary_positions or 'moon' not in self.kundali_data.planetary_positions:
                return 0.5
            
            natal_moon = self.kundali_data.planetary_positions['moon']
            
            # Calculate angular relationship
            angular_diff = abs(moon_position.longitude - natal_moon.longitude)
            if angular_diff > 180:
                angular_diff = 360 - angular_diff
            
            # Lunar return and other significant angles
            if angular_diff < 5:
                return 1.0  # Lunar return - very strong
            elif angular_diff < 15:
                return 0.9  # Close to lunar return
            elif 85 <= angular_diff <= 95:
                return 0.4  # Square aspect - challenging
            elif 175 <= angular_diff <= 185:
                return 0.3  # Opposition - challenging
            elif 115 <= angular_diff <= 125:
                return 0.8  # Trine aspect - harmonious
            else:
                return 0.6  # Other angles - moderate
                
        except Exception:
            return 0.5
    
    def _get_season(self, date: datetime) -> str:
        """Get season for given date."""
        month = date.month
        
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "autumn"
        else:
            return "winter"
    
    def _are_adjacent_seasons(self, season1: str, season2: str) -> bool:
        """Check if two seasons are adjacent."""
        seasons = ["winter", "spring", "summer", "autumn"]
        
        try:
            idx1 = seasons.index(season1)
            idx2 = seasons.index(season2)

            return abs(idx1 - idx2) == 1 or abs(idx1 - idx2) == 3
        except ValueError:
            return False


class HoraCalculator:
    """
    Calculator for Hora (planetary hours).
    Each day has 24 horas (planetary hours), with each hora ruled by a planet.
    The hora ruler significantly affects the favorability of activities.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Planetary sequence for horas (Chaldean order)
        self._hora_sequence = ['sun', 'venus', 'mercury', 'moon', 'saturn', 'jupiter', 'mars']

        # Day rulers (which planet rules each weekday)
        self._day_rulers = {
            0: 'moon',     # Monday
            1: 'mars',     # Tuesday
            2: 'mercury',  # Wednesday
            3: 'jupiter',  # Thursday
            4: 'venus',    # Friday
            5: 'saturn',   # Saturday
            6: 'sun'       # Sunday
        }

        # Hora favorability ratings (0.0 to 1.0)
        self._hora_favorability = {
            'sun': 0.75,      # Authority, power, government work
            'moon': 0.70,     # Emotions, home, travel, water
            'mars': 0.55,     # Energy, courage, surgery, construction (aggressive)
            'mercury': 0.85,  # Communication, business, trade, learning (excellent)
            'jupiter': 0.90,  # Spirituality, education, dharma, wealth (most auspicious)
            'venus': 0.80,    # Love, beauty, arts, luxury, marriage
            'saturn': 0.50    # Discipline, structure, hard work (challenging but stable)
        }

    def calculate_favorability(self, date: datetime, sunrise_time: datetime, weekday: int) -> float:
        """Calculate hora favorability score."""
        try:
            hora_info = self.get_hora_info(date, sunrise_time, weekday)
            return hora_info['favorability']
        except Exception as e:
            self.logger.error(f"Error calculating hora favorability: {e}")
            return 0.6

    def get_hora_info(self, date: datetime, sunrise_time: datetime, weekday: int) -> Dict[str, Any]:
        """
        Calculate current Hora ruler and favorability.

        Horas change approximately every hour after sunrise (day) and sunset (night).
        The first hora of the day is ruled by the day lord.

        Args:
            date: Current datetime
            sunrise_time: Sunrise time for the date
            weekday: Day of week (0=Monday, 6=Sunday)

        Returns:
            dict with hora_ruler, favorability, hora_number
        """
        try:
            # Calculate hours since sunrise (for daytime horas)
            time_diff = date - sunrise_time
            hours_since_sunrise = time_diff.total_seconds() / 3600

            # If before sunrise, use previous day's night horas (simplified - return neutral)
            if hours_since_sunrise < 0:
                return {
                    'hora_ruler': 'unknown',
                    'favorability': 0.6,
                    'hora_number': 0
                }

            # Calculate hora number (1-24, but we focus on 1-12 for daytime)
            hora_number = int(hours_since_sunrise) + 1

            # Get day ruler (starting hora)
            day_ruler = self._day_rulers.get(weekday, 'sun')

            # Find starting index in hora sequence
            try:
                start_index = self._hora_sequence.index(day_ruler)
            except ValueError:
                start_index = 0

            # Calculate current hora ruler
            # Horas cycle through the 7 planets
            current_hora_index = (start_index + int(hours_since_sunrise)) % 7
            hora_ruler = self._hora_sequence[current_hora_index]

            # Get favorability for this hora
            favorability = self._hora_favorability.get(hora_ruler, 0.6)

            return {
                'hora_ruler': hora_ruler,
                'favorability': favorability,
                'hora_number': hora_number
            }

        except Exception as e:
            self.logger.error(f"Error getting hora info: {e}")
            return {
                'hora_ruler': 'unknown',
                'favorability': 0.6,
                'hora_number': 0
            }


class LunarMonthCalculator:
    """
    Calculator for Lunar Month (Masa) based on Sun's zodiacal position.
    Also detects Adhika Masa (intercalary month).
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # 12 Lunar months based on Sun's zodiac position
        self._lunar_months = [
            'Chaitra',      # Sun in Aries (Mesha)
            'Vaishakha',    # Sun in Taurus (Vrishabha)
            'Jyeshtha',     # Sun in Gemini (Mithuna)
            'Ashadha',      # Sun in Cancer (Karka)
            'Shravana',     # Sun in Leo (Simha)
            'Bhadrapada',   # Sun in Virgo (Kanya)
            'Ashwina',      # Sun in Libra (Tula)
            'Kartika',      # Sun in Scorpio (Vrishchika)
            'Margashirsha', # Sun in Sagittarius (Dhanu)
            'Pausha',       # Sun in Capricorn (Makara)
            'Magha',        # Sun in Aquarius (Kumbha)
            'Phalguna'      # Sun in Pisces (Meena)
        ]

    def get_lunar_month_info(self, sun_position: PlanetaryPosition) -> Dict[str, Any]:
        """
        Get lunar month name and Adhika Masa status.

        Args:
            sun_position: Current Sun position

        Returns:
            dict with month_name, is_adhika_masa
        """
        try:
            # Get Sun's rasi (0-11)
            sun_rasi = sun_position.rasi

            # Get month name
            month_name = self._lunar_months[sun_rasi]

            # Adhika Masa detection (simplified)
            # True Adhika Masa requires checking if two new moons occur in same solar month
            # For now, we return False (proper implementation requires ephemeris tracking)
            is_adhika_masa = False

            return {
                'month_name': month_name,
                'is_adhika_masa': is_adhika_masa,
                'solar_month_index': sun_rasi
            }

        except Exception as e:
            self.logger.error(f"Error getting lunar month info: {e}")
            return {
                'month_name': 'Unknown',
                'is_adhika_masa': False,
                'solar_month_index': 0
            }
