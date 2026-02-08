"""
Base abstract class for Kundali Generator implementations.

This module provides the abstract base class that defines the common interface
for different kundali generation implementations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from ..core.data_models import BirthDetails, KundaliData, ValidationResult, PlanetaryPosition
from ..core.interfaces import KundaliGeneratorInterface
from .birth_details_validator import BirthDetailsValidator
from .jaimini_engine import JaiminiEngine


class BaseKundaliGenerator(KundaliGeneratorInterface, ABC):
    """
    Abstract base class for kundali generation implementations.
    
    This class provides common functionality and defines the interface
    that all kundali generator implementations must follow.
    """
    
    def __init__(self):
        """Initialize the base kundali generator."""
        self.validator = BirthDetailsValidator()
        self.schema_version = "2.0"
    
    @abstractmethod
    def _calculate_planetary_positions(
        self, 
        birth_data: BirthDetails,
        ayanamsa: str = "LAHIRI"
    ) -> Dict[str, PlanetaryPosition]:
        """
        Calculate planetary positions using the specific implementation.
        
        Args:
            birth_data: Validated birth details
            ayanamsa: Ayanamsa system to use
            
        Returns:
            Dictionary of planetary positions
        """
        pass
    
    @abstractmethod
    def _calculate_divisional_charts(
        self,
        planetary_positions: Dict[str, PlanetaryPosition],
        lagna_longitude: float,
        birth_data: BirthDetails,
        ayanamsa: str,
        house_system: str,
    ) -> Dict[str, Any]:
        """
        Calculate divisional charts using the specific implementation.
        
        Args:
            planetary_positions: Basic planetary positions
            lagna_longitude: Lagna longitude in degrees
            
        Returns:
            Dictionary of divisional chart data
        """
        pass
    
    @abstractmethod
    def _calculate_yogas_and_doshas(
        self, 
        planetary_positions: Dict[str, PlanetaryPosition],
        divisional_charts: Dict[str, Any],
        lagna_longitude: float
    ) -> Tuple[List[Any], List[Any]]:
        """
        Calculate yogas and doshas using the specific implementation.
        
        Args:
            planetary_positions: Basic planetary positions
            divisional_charts: Divisional chart data
            lagna_longitude: Lagna longitude in degrees
            
        Returns:
            Tuple of (yogas_list, doshas_list)
        """
        pass
    
    @abstractmethod
    def _calculate_dasha_periods(
        self, 
        birth_data: BirthDetails,
        moon_position: Optional[PlanetaryPosition]
    ) -> Optional[Any]:
        """
        Calculate dasha periods using the specific implementation.
        
        Args:
            birth_data: Birth details
            moon_position: Moon's position
            
        Returns:
            Dasha analysis data or None
        """
        pass
    
    @abstractmethod
    def _get_implementation_info(self) -> Dict[str, Any]:
        """
        Get information about the specific implementation.
        
        Returns:
            Dictionary with implementation details
        """
        pass
    
    def generate_from_birth_details(
        self,
        birth_data: BirthDetails,
        ayanamsa: str = "LAHIRI",
        house_system: str = "BHAVA_CHALIT"
    ) -> KundaliData:
        """
        Generate complete kundali from birth details.
        
        Args:
            birth_data: Validated birth details
            ayanamsa: Ayanamsa system to use (default: TRUE_CITRA)
            
        Returns:
            Complete kundali data structure
        """
        # Validate birth details
        validation_result = self.validate_birth_details(birth_data)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid birth details: {validation_result.errors}")
        
        # Calculate planetary positions using implementation-specific method
        planetary_positions = self._calculate_planetary_positions(birth_data, ayanamsa)

        # Get Lagna position
        lagna_position = planetary_positions.get('lagna')
        lagna_longitude = lagna_position.longitude if lagna_position else 0.0

        # Persist calculation context for metadata export
        generator_type = getattr(self, 'GENERATOR_ID', self.__class__.__name__).lower()
        generator_label = getattr(self, 'GENERATOR_LABEL', generator_type.replace('_', ' ').title())
        ayanamsa_code = (ayanamsa or 'LAHIRI').upper()
        house_code = (house_system or 'BHAVA_CHALIT').upper()
        ayanamsa_label = ayanamsa_code.replace('_', ' ').title()
        house_label = house_code.replace('_', ' ').title()
        self._calculation_context = {
            'ayanamsa': ayanamsa_code,
            'ayanamsa_label': ayanamsa_label,
            'house_system': house_code,
            'house_system_label': house_label,
            'generator_type': generator_type,
            'generator_label': generator_label,
        }

        # Calculate divisional charts
        divisional_charts = self._calculate_divisional_charts(
            planetary_positions,
            lagna_longitude,
            birth_data,
            ayanamsa,
            house_system,
        )
        
        # Analyze yogas and doshas
        yogas, doshas = self._calculate_yogas_and_doshas(
            planetary_positions, divisional_charts, lagna_longitude
        )
        
        # Calculate dasha periods
        moon_position = planetary_positions.get('moon')
        dasha_analysis = self._calculate_dasha_periods(birth_data, moon_position)
        
        # Calculate Panchanga (with Julian Day if available)
        jd = getattr(self, '_current_julian_day', None)
        panchanga = self._calculate_panchanga(moon_position, planetary_positions, jd)
        
        # Create complete kundali data
        kundali_data = KundaliData(
            schema_version=self.schema_version,
            generation_timestamp=datetime.now().isoformat(),
            birth_details=birth_data,
            astronomical_data=self._create_astronomical_data(ayanamsa) if hasattr(self, '_create_astronomical_data') else self._create_default_astronomical_data(ayanamsa),
            planetary_positions=planetary_positions,
            divisional_charts=self._serialize_divisional_charts(divisional_charts),
            panchanga=panchanga,
            yogas_and_doshas=self._serialize_yogas_and_doshas(yogas, doshas),
            dasha_periods=self._serialize_dasha_analysis(dasha_analysis),
            metadata=self._create_metadata()
        )

        # Clear calculation context to avoid leaking state
        if hasattr(self, '_calculation_context'):
            delattr(self, '_calculation_context')

        return kundali_data
    
    def validate_birth_details(self, birth_data: BirthDetails) -> ValidationResult:
        """
        Validate birth details for completeness and accuracy.
        
        Args:
            birth_data: Birth details to validate
            
        Returns:
            Validation result
        """
        return self.validator.validate_birth_details(birth_data)
    
    def export_standardized_json(self, kundali: KundaliData) -> str:
        """
        Export kundali in standardized JSON format.
        
        Args:
            kundali: Complete kundali data
            
        Returns:
            JSON string representation
        """
        import json
        
        # Validate kundali data before export
        validation_result = self._validate_kundali_data(kundali)
        if not validation_result.is_valid:
            raise ValueError(f"Invalid kundali data: {validation_result.errors}")
        
        try:
            # Convert to dictionary with proper serialization
            kundali_dict = self._serialize_kundali_data(kundali)

            # Enrich with Ashtakavarga data
            try:
                from ..layer_processor.ashtakavarga_analyzer import AshtakavargaAnalyzer
                # Use birth datetime as reference
                if kundali.birth_details and kundali.birth_details.date and kundali.birth_details.time:
                    from datetime import datetime as _dt
                    ref_dt = _dt.combine(kundali.birth_details.date, kundali.birth_details.time)
                else:
                    from datetime import datetime as _dt
                    ref_dt = _dt.utcnow()
                analyzer = AshtakavargaAnalyzer(kundali)
                analysis = analyzer.get_ashtakavarga_analysis(ref_dt)
                summary = analyzer.get_ashtakavarga_summary()

                def _house_to_sign_chart(
                    chart: Dict[Any, Any],
                    lagna_rasi_index: Optional[int],
                ) -> Dict[str, Any]:
                    if not chart:
                        return {}
                    chart_int = {int(key): value for key, value in chart.items()}
                    sign_map: Dict[int, Any] = {}
                    if lagna_rasi_index is None:
                        for house, value in chart_int.items():
                            sign_map[house] = value
                    else:
                        for house, value in chart_int.items():
                            sign_number = ((lagna_rasi_index + (house - 1)) % 12) + 1
                            sign_map[sign_number] = value
                    return {
                        str(sign): sign_map.get(sign)
                        for sign in range(1, 13)
                    }

                def _house_summary_to_sign(
                    summary_dict: Dict[str, Any],
                    lagna_rasi_index: Optional[int],
                    sign_names_list: List[str],
                ) -> Dict[str, Any]:
                    if not summary_dict:
                        return {}
                    summary_sign: Dict[str, Any] = {
                        "total_bindus_by_planet": summary_dict.get("total_bindus_by_planet", {}),
                        "sarvashtakavarga_total": summary_dict.get("sarvashtakavarga_total"),
                        "average_bindus_per_sign": summary_dict.get("average_bindus_per_house"),
                    }
                    strongest: Dict[str, Any] = {}
                    weakest: Dict[str, Any] = {}
                    if lagna_rasi_index is not None:
                        for planet, entry in (summary_dict.get("strongest_houses") or {}).items():
                            house_number = int(entry.get("house", 0) or 0)
                            if house_number:
                                sign_number = ((lagna_rasi_index + (house_number - 1)) % 12) + 1
                                strongest[planet] = {
                                    "sign": sign_number,
                                    "bindus": entry.get("bindus"),
                                    "sign_name": sign_names_list[sign_number - 1]
                                    if 1 <= sign_number <= len(sign_names_list)
                                    else None,
                                }
                        for planet, entry in (summary_dict.get("weakest_houses") or {}).items():
                            house_number = int(entry.get("house", 0) or 0)
                            if house_number:
                                sign_number = ((lagna_rasi_index + (house_number - 1)) % 12) + 1
                                weakest[planet] = {
                                    "sign": sign_number,
                                    "bindus": entry.get("bindus"),
                                    "sign_name": sign_names_list[sign_number - 1]
                                    if 1 <= sign_number <= len(sign_names_list)
                                    else None,
                                }
                    summary_sign["strongest_signs"] = strongest
                    summary_sign["weakest_signs"] = weakest
                    return summary_sign

                lagna_rasi_index: Optional[int] = None
                try:
                    lagna_rasi_index = int(
                        kundali_dict.get("divisional_charts", {})
                        .get("D1", {})
                        .get("planetary_positions", {})
                        .get("lagna", {})
                        .get("rasi")
                    )
                except (TypeError, ValueError, AttributeError):
                    lagna_rasi_index = None

                natal_by_house = analysis.get("natal_ashtakavarga_charts", {}) or {}
                sarva_by_house = analysis.get("sarvashtakavarga_chart", {}) or {}

                natal_by_sign = {
                    planet: _house_to_sign_chart(chart or {}, lagna_rasi_index)
                    for planet, chart in natal_by_house.items()
                }
                sarva_by_sign = _house_to_sign_chart(sarva_by_house, lagna_rasi_index)

                sign_names = [
                    "Aries",
                    "Taurus",
                    "Gemini",
                    "Cancer",
                    "Leo",
                    "Virgo",
                    "Libra",
                    "Scorpio",
                    "Sagittarius",
                    "Capricorn",
                    "Aquarius",
                    "Pisces",
                ]
                lagna_sign_number: Optional[int] = (
                    lagna_rasi_index + 1 if lagna_rasi_index is not None else None
                )
                lagna_sign_name: Optional[str] = (
                    sign_names[lagna_rasi_index]
                    if lagna_rasi_index is not None and 0 <= lagna_rasi_index < len(sign_names)
                    else None
                )

                kundali_dict["ashtakavarga"] = {
                    "natal_charts": natal_by_sign,
                    "sarvashtakavarga": sarva_by_sign,
                    "summary": _house_summary_to_sign(summary, lagna_rasi_index, sign_names),
                    "lagna_sign_number": lagna_sign_number,
                    "lagna_sign_name": lagna_sign_name,
                    "sign_labels": sign_names,
                }
            except Exception:
                # Be resilient; do not fail export on enrichment errors
                pass
            
            # Export as formatted JSON
            return json.dumps(kundali_dict, indent=2, ensure_ascii=False, default=str)
            
        except Exception as e:
            raise ValueError(f"JSON export failed: {str(e)}")

    @staticmethod
    def _equal_house_cusps(lagna_longitude: float) -> List[float]:
        """Generate equal house cusps offset by the lagna."""
        return [
            (lagna_longitude + house_index * 30.0) % 360.0
            for house_index in range(12)
        ]

    @staticmethod
    def _whole_sign_house_cusps(lagna_longitude: float) -> List[float]:
        """
        Generate whole sign (rasi) house cusps.

        In whole sign houses, each house occupies one complete zodiac sign (30°).
        House 1 starts at the beginning of the sign containing the Lagna.

        Args:
            lagna_longitude: Lagna longitude in degrees (0-360)

        Returns:
            List of 12 house cusp longitudes at sign boundaries
        """
        # Determine which rasi (0-11) the lagna is in
        lagna_rasi = int(lagna_longitude / 30.0)
        # House 1 starts at the beginning of lagna's rasi
        return [
            (lagna_rasi * 30.0 + house_index * 30.0) % 360.0
            for house_index in range(12)
        ]

    @staticmethod
    def _assign_whole_sign_houses(
        chart_positions: Dict[str, Dict[str, Any]],
        lagna_rasi: int,
    ) -> None:
        """
        Assign whole sign houses based on rasi.

        In whole sign houses, planets are assigned to houses based purely on
        which rasi (sign) they occupy, relative to the lagna's rasi:
        - Planets in lagna's rasi → House 1
        - Planets in next rasi → House 2, etc.

        Args:
            chart_positions: Dictionary of planetary positions
            lagna_rasi: The rasi (0-11) containing the lagna
        """
        for planet_data in chart_positions.values():
            if not isinstance(planet_data, dict):
                continue
            planet_rasi = planet_data.get('rasi')
            if planet_rasi is None:
                continue
            # Rasi values are 0-indexed (0-11) in the data
            # Calculate house based on rasi offset from lagna
            house = ((planet_rasi - lagna_rasi + 12) % 12) + 1
            planet_data['house'] = house

    @staticmethod
    def _assign_houses_to_positions(
        chart_positions: Dict[str, Dict[str, Any]],
        house_cusps: List[float],
    ) -> None:
        """Assign house numbers to planetary positions based on cusp boundaries."""
        if not house_cusps or len(house_cusps) != 12:
            return

        def _resolve_house(longitude: float) -> int:
            for index in range(12):
                start = house_cusps[index]
                end = house_cusps[(index + 1) % 12]
                adjusted_longitude = longitude
                if end < start:
                    end += 360.0
                if adjusted_longitude < start:
                    adjusted_longitude += 360.0
                if start <= adjusted_longitude < end:
                    return index + 1
            return 1

        for planet_data in chart_positions.values():
            if not isinstance(planet_data, dict):
                continue
            longitude = planet_data.get('longitude')
            if longitude is None:
                continue
            planet_data['house'] = _resolve_house(float(longitude))

    @classmethod
    def _assign_bhava_chalit_houses(
        cls,
        chart_positions: Dict[str, Dict[str, Any]],
        house_cusps: List[float],
    ) -> None:
        """Assign houses using bhava chalit midpoint boundaries."""
        if not house_cusps or len(house_cusps) != 12:
            return

        midpoints = cls._calculate_house_midpoints(house_cusps)

        for planet_data in chart_positions.values():
            if not isinstance(planet_data, dict):
                continue
            longitude = planet_data.get("longitude")
            if longitude is None:
                continue
            planet_data["house"] = cls._resolve_house_from_midpoints(float(longitude), midpoints)

    @classmethod
    def _assign_bhava_chalit_houses_to_field(
        cls,
        chart_positions: Dict[str, Dict[str, Any]],
        house_cusps: List[float],
        field: str = "bhava_house",
    ) -> None:
        """Annotate positions with bhava chalit houses without overwriting house."""
        if not house_cusps or len(house_cusps) != 12:
            return
        midpoints = cls._calculate_house_midpoints(house_cusps)

        for planet_data in chart_positions.values():
            if not isinstance(planet_data, dict):
                continue
            longitude = planet_data.get("longitude")
            if longitude is None:
                continue
            planet_data[field] = cls._resolve_house_from_midpoints(float(longitude), midpoints)

    @staticmethod
    def _calculate_house_midpoints(house_cusps: List[float]) -> List[float]:
        """
        Calculate midpoints between successive house cusps for Bhava Chalit.

        In Bhava Chalit, planets are assigned to houses based on these midpoints:
        - House 1 spans from midpoint[11] to midpoint[0]
        - House 2 spans from midpoint[0] to midpoint[1]
        - etc.

        Args:
            house_cusps: List of 12 house cusp longitudes in degrees

        Returns:
            List of 12 midpoint longitudes
        """
        midpoints = []
        for index in range(12):
            start = house_cusps[index]
            end = house_cusps[(index + 1) % 12]
            if end < start:
                end += 360.0
            midpoint = (start + end) / 2.0
            midpoints.append(midpoint % 360.0)
        return midpoints

    @staticmethod
    def _resolve_house_from_midpoints(longitude: float, midpoints: List[float]) -> int:
        """
        Resolve house number given midpoint boundaries for Bhava Chalit.

        The planet's house is determined by which pair of midpoints contains its longitude:
        - House N is bounded by midpoint[N-2] (start) and midpoint[N-1] (end)
        - Handles 360° wraparound correctly

        Args:
            longitude: Planet's longitude in degrees (0-360)
            midpoints: List of 12 midpoint longitudes from _calculate_house_midpoints()

        Returns:
            House number (1-12)
        """
        for index in range(12):
            start = midpoints[index - 1]
            end = midpoints[index]
            adjusted_longitude = longitude
            if end < start:
                end += 360.0
            if adjusted_longitude < start:
                adjusted_longitude += 360.0
            if start <= adjusted_longitude < end:
                return index + 1
        return 1
    
    # Common helper methods that can be shared across implementations
    
    def _calculate_panchanga(
        self,
        moon_position: Optional[PlanetaryPosition],
        planetary_positions: Dict[str, PlanetaryPosition],
        jd: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate Panchanga elements (enhanced implementation)."""
        panchanga = {}
        
        if moon_position:
            # Calculate Tithi (lunar day)
            sun_position = planetary_positions.get('sun')
            if sun_position:
                moon_sun_diff = (moon_position.longitude - sun_position.longitude) % 360
                tithi_number = int(moon_sun_diff / 12) + 1
                tithi_balance = (moon_sun_diff % 12) / 12 * 100

                # Enhanced Moon Phase Calculation
                phase_info = JaiminiEngine.calculate_moon_phase_detailed(
                    sun_position.longitude, 
                    moon_position.longitude
                )
                panchanga['moon_phase'] = phase_info

                shukla_names = [
                    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
                    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
                    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima"
                ]
                krishna_names = [
                    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
                    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
                    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
                ]

                if tithi_number <= 15:
                    tithi_name = shukla_names[tithi_number - 1]
                    paksha = "Shukla"
                else:
                    index = min(tithi_number - 16, len(krishna_names) - 1)
                    tithi_name = krishna_names[index]
                    paksha = "Krishna"

                panchanga['tithi'] = {
                    'number': tithi_number,
                    'name': tithi_name,
                    'balance': round(tithi_balance, 2)
                }
                panchanga['paksha'] = paksha
            
            # Calculate Nakshatra
            nakshatra_span = 360.0 / 27
            nakshatra_index = int(moon_position.longitude / nakshatra_span)
            nakshatra_position = (moon_position.longitude * 27 / 360) % 1
            nakshatra_balance = (1.0 - nakshatra_position) * 100
            
            nakshatra_names = [
                "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
                "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
                "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
                "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
                "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
            ]
            
            nakshatra_lords = [
                "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
                "Jupiter", "Saturn", "Mercury", "Ketu", "Venus", "Sun",
                "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
                "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu",
                "Jupiter", "Saturn", "Mercury"
            ]
            
            panchanga['nakshatra'] = {
                'number': nakshatra_index + 1,
                'name': nakshatra_names[nakshatra_index],
                'lord': nakshatra_lords[nakshatra_index],
                'balance': round(nakshatra_balance, 2)
            }
            
            # Calculate Paksha fallback if not set (should already be set above)
            if 'paksha' not in panchanga and 'tithi' in panchanga:
                panchanga['paksha'] = 'Shukla' if panchanga['tithi']['number'] <= 15 else 'Krishna'
        
        # Calculate weekday if Julian Day is provided
        if jd is not None:
            # Julian Day 0 was a Monday, correct formula for weekday calculation
            weekday_index = int(jd + 0.5) % 7
            weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            weekday_lords = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]
            
            panchanga['weekday'] = {
                'name': weekday_names[weekday_index],
                'lord': weekday_lords[weekday_index]
            }
        
        return panchanga
    
    def _create_default_astronomical_data(self, ayanamsa: str = "LAHIRI") -> Dict[str, Any]:
        """Create default astronomical data section."""
        return {
            'ayanamsa': ayanamsa,
            'calculation_method': self._get_implementation_info().get('method', 'UNKNOWN'),
            'implementation_info': self._get_implementation_info()
        }
    
    @staticmethod
    def get_available_ayanamsa_systems() -> Dict[str, str]:
        """Get all available ayanamsa systems with descriptions."""
        return {
            # Most Popular Vedic Systems
            "TRUE_CITRA": "True Chitra Paksha - Based on fixed star Spica (default)",
            "LAHIRI": "Lahiri Ayanamsa - Most commonly used in India (N.C. Lahiri)",
            "KRISHNAMURTI": "Krishnamurti Paddhati (KP) System",
            "RAMAN": "B.V. Raman Ayanamsa - Popular in South India",
            
            # Traditional Systems
            "TRUE_REVATI": "True Revati Paksha - Based on fixed star Revati",
            "TRUE_PUSHYA": "True Pushya Paksha - Based on Pushya nakshatra",
            "SURYASIDDHANTA": "Surya Siddhanta - Ancient astronomical text",
            "ARYABHATA": "Aryabhata - Ancient Indian mathematician/astronomer",
            
            # Western Sidereal Systems
            "FAGAN_BRADLEY": "Fagan-Bradley - Western sidereal astrology",
            "DELUCE": "De Luce - Alternative western sidereal system",
            
            # Research & Specialized Systems
            "YUKTESHWAR": "Sri Yukteshwar - Spiritual teacher's system",
            "JN_BHASIN": "J.N. Bhasin - Research-based ayanamsa",
            "DJWHAL_KHUL": "Djwhal Khul - Theosophical system",
            "USHASHASHI": "Usha-Shashi - Research system",
            
            # Galactic Systems
            "GALCENT_0SAG": "Galactic Center at 0° Sagittarius",
            "TRUE_MULA": "True Mula - Based on galactic center alignment",
            
            # Historical Systems
            "HIPPARCHOS": "Hipparchos - Ancient Greek astronomer",
            "SASSANIAN": "Sassanian - Persian astronomical system",
            
            # Modern Variants
            "LAHIRI_1940": "Lahiri 1940 - Historical Lahiri calculation",
            "LAHIRI_ICRC": "Lahiri ICRC - Indian Calendar Reform Committee",
            "KRISHNAMURTI_VP291": "KP VP291 - Modern KP variant"
        }
    
    def _serialize_divisional_charts(self, charts: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize divisional charts for JSON export."""
        # This is a simplified serialization - implementations can override
        return charts
    
    def _serialize_yogas_and_doshas(self, yogas: List[Any], doshas: List[Any]) -> Dict[str, Any]:
        """Serialize yogas and doshas for JSON export."""
        def serialize_yoga(yoga):
            if isinstance(yoga, dict):
                return {
                    'name': yoga.get('name', 'Unknown'),
                    'type': yoga.get('type', 'unknown'),
                    'strength': yoga.get('strength', 'medium'),
                    'planets_involved': yoga.get('planets_involved', []),
                    'houses_involved': yoga.get('houses_involved', []),
                    'description': yoga.get('description', ''),
                    'effects': yoga.get('effects', []),
                    'strength_points': yoga.get('strength_points', 0.0)
                }
            else:
                return {
                    'name': getattr(yoga, 'name', str(yoga)),
                    'type': getattr(yoga, 'type', 'unknown'),
                    'strength': getattr(yoga, 'strength', 'medium'),
                    'planets_involved': getattr(yoga, 'planets_involved', []),
                    'houses_involved': getattr(yoga, 'houses_involved', []),
                    'description': getattr(yoga, 'description', ''),
                    'effects': getattr(yoga, 'effects', []),
                    'strength_points': getattr(yoga, 'strength_points', 0.0)
                }
        
        def serialize_dosha(dosha):
            if isinstance(dosha, dict):
                return {
                    'name': dosha.get('name', 'Unknown'),
                    'type': dosha.get('type', 'unknown'),
                    'severity': dosha.get('severity', 'medium'),
                    'planets_involved': dosha.get('planets_involved', []),
                    'houses_involved': dosha.get('houses_involved', []),
                    'description': dosha.get('description', ''),
                    'effects': dosha.get('effects', []),
                    'remedies': dosha.get('remedies', []),
                    'strength_points': dosha.get('strength_points', 0.0)
                }
            else:
                return {
                    'name': getattr(dosha, 'name', str(dosha)),
                    'type': getattr(dosha, 'type', 'unknown'),
                    'severity': getattr(dosha, 'severity', 'medium'),
                    'planets_involved': getattr(dosha, 'planets_involved', []),
                    'houses_involved': getattr(dosha, 'houses_involved', []),
                    'description': getattr(dosha, 'description', ''),
                    'effects': getattr(dosha, 'effects', []),
                    'remedies': getattr(dosha, 'remedies', []),
                    'strength_points': getattr(dosha, 'strength_points', 0.0)
                }
        
        serialized_yogas = [serialize_yoga(yoga) for yoga in yogas]
        serialized_doshas = [serialize_dosha(dosha) for dosha in doshas]
        
        # Calculate summary statistics
        total_yoga_strength = sum(yoga['strength_points'] for yoga in serialized_yogas)
        total_dosha_impact = sum(abs(dosha['strength_points']) for dosha in serialized_doshas)
        
        return {
            'beneficial_yogas': serialized_yogas,
            'challenging_doshas': serialized_doshas,
            'summary': {
                'total_yogas': len(yogas),
                'total_doshas': len(doshas),
                'net_yoga_strength': round(total_yoga_strength, 2),
                'net_dosha_impact': round(total_dosha_impact, 2)
            }
        }
    
    def _serialize_dasha_analysis(self, dasha_analysis: Optional[Any]) -> Dict[str, Any]:
        """Serialize dasha analysis for JSON export."""
        if not dasha_analysis:
            return {}
        
        # Handle both dictionary and object formats
        if isinstance(dasha_analysis, dict):
            vimshottari_data = {
                'birth_nakshatra': dasha_analysis.get('birth_nakshatra', ''),
                'birth_nakshatra_name': dasha_analysis.get('birth_nakshatra_name', ''),
                'birth_nakshatra_lord': dasha_analysis.get('birth_nakshatra_lord', ''),
                'current_dasha_lord': dasha_analysis.get('current_dasha_lord', ''),
                'dasha_balance_at_birth': dasha_analysis.get('dasha_balance_at_birth', 0.0),
                'total_dasha_period': dasha_analysis.get('total_dasha_period', 0)
            }

            # Add enhanced dasha information if available
            if 'current_mahadasha' in dasha_analysis:
                vimshottari_data['current_mahadasha'] = dasha_analysis['current_mahadasha']

            if 'current_antardasha' in dasha_analysis:
                vimshottari_data['current_antardasha'] = dasha_analysis['current_antardasha']

            if 'current_pratyantardasha' in dasha_analysis:
                vimshottari_data['current_pratyantardasha'] = dasha_analysis['current_pratyantardasha']

            if 'current_sookshma' in dasha_analysis:
                vimshottari_data['current_sookshma'] = dasha_analysis['current_sookshma']

            if 'current_prana' in dasha_analysis:
                vimshottari_data['current_prana'] = dasha_analysis['current_prana']

            if 'mahadasha_sequence' in dasha_analysis:
                vimshottari_data['mahadasha_sequence'] = dasha_analysis['mahadasha_sequence']

            return {'vimshottari': vimshottari_data}
        else:
            return {
                'vimshottari': {
                    'birth_nakshatra': getattr(dasha_analysis, 'birth_nakshatra', ''),
                    'birth_nakshatra_lord': getattr(dasha_analysis, 'birth_nakshatra_lord', ''),
                    'dasha_balance_at_birth': getattr(dasha_analysis, 'dasha_balance_at_birth', 0.0)
                }
            }
    
    def _create_metadata(self) -> Dict[str, Any]:
        """Create metadata section."""
        context = getattr(self, '_calculation_context', {}) if hasattr(self, '_calculation_context') else {}
        return {
            'generator': f'{self.__class__.__name__} v{self.schema_version}',
            'implementation_info': self._get_implementation_info(),
            'generation_timestamp': datetime.now().isoformat(),
            'hash': self._generate_hash(),
            'calculation_settings': {
                'ayanamsa': context.get('ayanamsa', 'UNKNOWN'),
                'ayanamsa_label': context.get('ayanamsa_label', 'Unknown'),
                'house_system': context.get('house_system', 'UNKNOWN'),
                'house_system_label': context.get('house_system_label', 'Unknown'),
                'generator_type': context.get('generator_type', self.__class__.__name__),
                'generator_label': context.get('generator_label', context.get('generator_type', self.__class__.__name__))
            }
        }
    
    def _generate_hash(self) -> str:
        """Generate a hash for the kundali data."""
        import hashlib
        timestamp = datetime.now().isoformat()
        implementation = self.__class__.__name__
        return hashlib.md5(f"{timestamp}_{implementation}".encode()).hexdigest()[:16]
    
    def _validate_kundali_data(self, kundali: KundaliData) -> ValidationResult:
        """Validate kundali data structure."""
        result = ValidationResult(is_valid=True)
        
        # Check required fields
        if not kundali.schema_version:
            result.add_error("Schema version is required")
        
        if not kundali.birth_details:
            result.add_error("Birth details are required")
        
        if not kundali.planetary_positions:
            result.add_error("Planetary positions are required")
        
        # Check planetary positions completeness
        required_planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu', 'lagna']
        missing_planets = [p for p in required_planets if p not in kundali.planetary_positions]
        
        if missing_planets:
            result.add_warning(f"Missing planetary positions: {missing_planets}")
        
        return result
    
    def _serialize_kundali_data(self, kundali: KundaliData) -> Dict[str, Any]:
        """Serialize kundali data to dictionary."""
        return {
            'schema_version': kundali.schema_version,
            'generation_timestamp': kundali.generation_timestamp,
            'birth_details': kundali.birth_details.to_dict() if kundali.birth_details else None,
            'astronomical_data': kundali.astronomical_data,
            'planetary_positions': {
                planet: position.to_dict() 
                for planet, position in kundali.planetary_positions.items()
            },
            'divisional_charts': kundali.divisional_charts,
            'panchanga': kundali.panchanga,
            'yogas_and_doshas': kundali.yogas_and_doshas,
            'dasha_periods': kundali.dasha_periods,
            'metadata': kundali.metadata
        }
