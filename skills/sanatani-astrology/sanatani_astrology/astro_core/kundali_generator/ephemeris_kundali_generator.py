"""
Ephemeris-based Kundali Generator Implementation.

This module provides a clean kundali generator implementation that uses
Swiss Ephemeris as primary with simplified calculations as fallback.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

try:
    import swisseph as swe
    SWISS_EPHEMERIS_AVAILABLE = True
except ImportError:
    SWISS_EPHEMERIS_AVAILABLE = False

from ..core.data_models import BirthDetails, PlanetaryPosition
from .base_kundali_generator import BaseKundaliGenerator
from .comprehensive_ephemeris_engine import ComprehensiveEphemerisEngine
from .dasha_calculator import DashaCalculator
from .jaimini_engine import JaiminiEngine
from .varga_engine import VargaEngine
from .varga_calculator import calculate_varga_position


class EphemerisKundaliGenerator(BaseKundaliGenerator):
    """
    Clean ephemeris-based kundali generator.
    
    This implementation uses Swiss Ephemeris as primary calculation engine
    with simplified astronomical calculations as fallback.
    """

    GENERATOR_ID = 'ephemeris'
    GENERATOR_LABEL = 'Swiss Ephemeris'
    
    def __init__(self, ephemeris_path: Optional[str] = None):
        """
        Initialize the ephemeris-based kundali generator.
        
        Args:
            ephemeris_path: Path to Swiss Ephemeris data files
        """
        super().__init__()
        self.ephemeris_engine = ComprehensiveEphemerisEngine(ephemeris_path)
    
    def _calculate_planetary_positions(
        self, 
        birth_data: BirthDetails,
        ayanamsa: str = "LAHIRI"
    ) -> Dict[str, PlanetaryPosition]:
        """
        Calculate planetary positions using ephemeris engine.
        
        Args:
            birth_data: Validated birth details
            ayanamsa: Ayanamsa system to use
            
        Returns:
            Dictionary of planetary positions
        """
        # Create proper datetime from birth data
        if hasattr(birth_data.date, 'date'):
            # birth_data.date is already a datetime object
            birth_datetime = birth_data.date.replace(
                hour=birth_data.time.hour,
                minute=birth_data.time.minute,
                second=birth_data.time.second
            )
        else:
            # birth_data.date is a date object
            birth_datetime = datetime.combine(birth_data.date, birth_data.time)
        
        # Calculate Julian Day (use proper timezone offset)
        jd = self.ephemeris_engine.julian_day_from_datetime(
            birth_datetime, birth_data.timezone_offset  # Use actual timezone offset
        )
        
        # Store Julian Day and coordinates for downstream calculations
        self._current_julian_day = jd
        self._current_latitude = birth_data.latitude
        self._current_longitude = birth_data.longitude

        # Calculate planetary positions with specified ayanamsa
        positions = self.ephemeris_engine.calculate_planetary_positions(
            jd, birth_data.latitude, birth_data.longitude, ayanamsa
        )
        
        return positions
    
    def _calculate_divisional_charts(
        self,
        planetary_positions: Dict[str, PlanetaryPosition],
        lagna_longitude: float,
        birth_data: BirthDetails,
        ayanamsa: str,
        house_system: str,
    ) -> Dict[str, Any]:
        """
        Calculate enhanced divisional charts using ephemeris-based positions.
        
        Args:
            planetary_positions: Basic planetary positions
            lagna_longitude: Lagna longitude in degrees
            
        Returns:
            Dictionary of divisional chart data
        """
        charts = {}
        
        # Calculate basic divisional charts (core vargas used in the app)
        divisional_factors = {
            'D1': {'factor': 1, 'name': 'Rasi Chart'},
            'D2': {'factor': 2, 'name': 'Hora Chart'},
            'D3': {'factor': 3, 'name': 'Drekkana Chart'},
            'D4': {'factor': 4, 'name': 'Chaturthamsa Chart'},
            'D5': {'factor': 5, 'name': 'Panchamsa Chart'},
            'D6': {'factor': 6, 'name': 'Shashtamsa Chart'},
            'D7': {'factor': 7, 'name': 'Saptamsa Chart'},
            'D8': {'factor': 8, 'name': 'Ashtamsa Chart'},
            'D9': {'factor': 9, 'name': 'Navamsa Chart'},
            'D10': {'factor': 10, 'name': 'Dasamsa Chart'},
            'D11': {'factor': 11, 'name': 'Ekadashamsa Chart'},
            'D12': {'factor': 12, 'name': 'Dwadasamsa Chart'},
            'D16': {'factor': 16, 'name': 'Shodasamsa Chart'},
            'D20': {'factor': 20, 'name': 'Vimsamsa Chart'},
            'D24': {'factor': 24, 'name': 'Chaturvimsamsa Chart'},
            'D27': {'factor': 27, 'name': 'Nakshatramsa Chart'},
            'D30': {'factor': 30, 'name': 'Trimsamsa Chart'},
            'D40': {'factor': 40, 'name': 'Khavedamsa Chart'},
            'D45': {'factor': 45, 'name': 'Akshavedamsa Chart'},
            'D60': {'factor': 60, 'name': 'Shashtiamsa Chart'}
        }
        
        for chart_name, chart_info in divisional_factors.items():
            factor = chart_info['factor']
            chart_positions = {}
            house_cusps = []
            lagna_div_position = calculate_varga_position(lagna_longitude, factor)
            lagna_div_rasi = lagna_div_position.rasi
            lagna_div_longitude = lagna_div_position.longitude
            
            for planet_name, position in planetary_positions.items():
                base_longitude = lagna_longitude if planet_name == 'lagna' else position.longitude
                varga_pos = calculate_varga_position(base_longitude, factor)
                div_longitude = varga_pos.longitude
                div_rasi = varga_pos.rasi
                div_degree = varga_pos.degree_in_sign
                div_nakshatra = int(div_longitude * 27 / 360) % 27
                house = ((div_rasi - lagna_div_rasi) % 12) + 1
                
                entry = {
                    'longitude': div_longitude,
                    'rasi': div_rasi,
                    'house': house,
                    'degree_in_sign': div_degree,
                    'nakshatra': div_nakshatra,
                    'dignity': self._calculate_dignity(planet_name, div_rasi),
                    'strength_points': self._calculate_basic_strength(planet_name, div_rasi),
                    'retrograde': position.retrograde if hasattr(position, 'retrograde') else False
                }

                # --- Varga Quality Calculations ---
                if planet_name != 'lagna':
                    # VargaEngine needs D1 sign/degree
                    d1_rasi = position.rasi
                    d1_deg = position.degree_in_sign
                    
                    if chart_name == 'D16':
                        q = VargaEngine.calculate_d16_quality(d1_deg, d1_rasi)
                        entry['quality'] = q['quality']
                        entry['deity'] = q['deity']
                    elif chart_name == 'D60':
                        q = VargaEngine.calculate_d60_quality(d1_deg, d1_rasi)
                        entry['quality'] = q['quality']
                        entry['shashtiamsa_name'] = q['name']
                
                chart_positions[planet_name] = entry

            system_key = (house_system or 'EQUAL').upper()
            if factor == 1:
                if system_key in {'RASI', 'WHOLE_SIGN'}:
                    # Whole sign houses: each house = one complete rasi/sign
                    # Planets assigned based on their rasi, not cusp boundaries
                    lagna_rasi = int(lagna_div_longitude / 30.0)  # 0-11
                    self._assign_whole_sign_houses(chart_positions, lagna_rasi)
                    house_cusps = self._whole_sign_house_cusps(lagna_div_longitude)
                elif system_key in {'EQUAL', 'EQUAL_START', 'EQUAL_MID'}:
                    # Equal houses: cusps start from exact lagna degree
                    house_cusps = self._equal_house_cusps(lagna_div_longitude)
                    self._assign_houses_to_positions(chart_positions, house_cusps)
                elif system_key == 'BHAVA_CHALIT':
                    house_cusps = self._compute_d1_house_cusps(
                        lagna_div_longitude,
                        birth_data,
                        ayanamsa,
                        system_key,
                    ) or self._equal_house_cusps(lagna_div_longitude)
                    self._assign_bhava_chalit_houses(chart_positions, house_cusps)
                else:
                    # Other cusp-based systems (SRIPATI, PLACIDUS, etc.)
                    house_cusps = self._compute_d1_house_cusps(
                        lagna_div_longitude,
                        birth_data,
                        ayanamsa,
                        system_key,
                    ) or self._equal_house_cusps(lagna_div_longitude)
                    self._assign_houses_to_positions(chart_positions, house_cusps)
                # Always calculate bhava_house for reference, regardless of house system
                if house_cusps:
                    self._assign_bhava_chalit_houses_to_field(chart_positions, house_cusps)
            else:
                house_cusps = self._equal_house_cusps(lagna_div_longitude)
            
            chart_data = {
                'chart_name': chart_info['name'],
                'division_number': factor,
                'planetary_positions': chart_positions,
                'house_cusps': house_cusps,
                'aspects': self._calculate_basic_aspects(chart_positions),
                'yogas': self._find_chart_yogas(chart_positions),
                'strength_summary': self._calculate_chart_strength_summary(chart_positions)
            }

            if chart_name == 'D1':
                chart_data['house_lords'] = self._calculate_house_lordships(house_cusps)
                chart_data['house_aspects'] = self._calculate_house_aspects(chart_positions)
                
                relationships = self._calculate_planetary_relationships(chart_positions)
                for planet_name, rel_data in relationships.items():
                    if planet_name in chart_data['planetary_positions']:
                        chart_data['planetary_positions'][planet_name]['relationships'] = rel_data
            
            charts[chart_name] = chart_data
        
        # --- Jaimini Calculations (Post-Loop) ---
        if 'D1' in charts:
            d1_chart = charts['D1']
            d1_positions = d1_chart['planetary_positions']
            house_lords = d1_chart.get('house_lords', {})
            house_cusps = d1_chart.get('house_cusps', [])
            
            # Arudha Padas
            arudhas = JaiminiEngine.calculate_arudha_padas(d1_positions, house_cusps, house_lords)
            
            # Karakamsa (requires D9)
            karakamsa_info = {}
            atmakaraka = JaiminiEngine.get_atmakaraka(d1_positions)
            if atmakaraka and 'D9' in charts:
                d9_positions = charts['D9']['planetary_positions']
                ak_in_d9 = d9_positions.get(atmakaraka)
                if ak_in_d9:
                    karakamsa_info = {
                        'atmakaraka': atmakaraka,
                        'sign': self._get_sign_name(ak_in_d9['rasi']),
                        'rasi_index': ak_in_d9['rasi']
                    }

            # Inject into D1
            d1_chart['special_lagnas'] = {
                'arudha_padas': arudhas,
                'karakamsa': karakamsa_info
            }
        
        return charts

    def _get_sign_name(self, rasi_index: int) -> str:
        signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 
                 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
        return signs[rasi_index % 12] if 0 <= rasi_index < 12 else 'Unknown'

    def _compute_d1_house_cusps(
        self,
        lagna_longitude: float,
        birth_data: BirthDetails,
        ayanamsa: str,
        house_system: str,
    ) -> Optional[List[float]]:
        system = (house_system or 'EQUAL').upper()
        if system in {'RASI', 'WHOLE_SIGN'}:
            return self._whole_sign_house_cusps(lagna_longitude)
        if system in {'EQUAL', 'EQUAL_START', 'EQUAL_MID'}:
            return self._equal_house_cusps(lagna_longitude)
        # BHAVA_CHALIT uses Sripati cusps with midpoint-based planet placement
        # SRIPATI uses Swiss Ephemeris native Sripati (traditional Vedic system)
        if system == 'BHAVA_CHALIT':
            system = 'SRIPATI'

        if not getattr(self, '_current_julian_day', None):
            return None

        try:
            return self.ephemeris_engine.calculate_house_cusps(
                self._current_julian_day,
                birth_data.latitude,
                birth_data.longitude,
                ayanamsa,
                system,
            )
        except Exception as exc:
            print(f"Warning: Ephemeris house calculation failed with system {system}: {exc}")
            return None
    
    def _calculate_yogas_and_doshas(
        self, 
        planetary_positions: Dict[str, PlanetaryPosition],
        divisional_charts: Dict[str, Any],
        lagna_longitude: float
    ) -> Tuple[List[Any], List[Any]]:
        """
        Calculate basic yogas and doshas.
        
        Args:
            planetary_positions: Basic planetary positions
            divisional_charts: Divisional chart data
            lagna_longitude: Lagna longitude in degrees
            
        Returns:
            Tuple of (yogas_list, doshas_list)
        """
        yogas = []
        doshas = []
        
        # Get planet positions
        sun = planetary_positions.get('sun')
        moon = planetary_positions.get('moon')
        mars = planetary_positions.get('mars')
        mercury = planetary_positions.get('mercury')
        jupiter = planetary_positions.get('jupiter')
        venus = planetary_positions.get('venus')
        saturn = planetary_positions.get('saturn')
        rahu = planetary_positions.get('rahu')
        ketu = planetary_positions.get('ketu')
        lagna = planetary_positions.get('lagna')
        
        # Enhanced Yoga calculations
        if sun and mercury:
            # Budh Aditya Yoga - Sun and Mercury together
            sun_mercury_diff = abs(sun.longitude - mercury.longitude)
            if sun_mercury_diff <= 10:  # Within 10 degrees
                yogas.append({
                    'name': 'Budh Aditya Yoga',
                    'type': 'beneficial',
                    'strength': 'medium',
                    'planets_involved': ['sun', 'mercury'],
                    'houses_involved': [sun.rasi + 1, mercury.rasi + 1],
                    'description': 'Sun and Mercury conjunction enhances intelligence and communication',
                    'effects': ['Enhanced intelligence', 'Good communication skills', 'Success in education'],
                    'strength_points': 60.0
                })
        
        if moon and jupiter:
            # Gaja Kesari Yoga - Moon and Jupiter in mutual kendras
            moon_house = (moon.rasi - lagna.rasi) % 12 + 1
            jupiter_house = (jupiter.rasi - lagna.rasi) % 12 + 1
            house_diff = abs(moon_house - jupiter_house)
            if house_diff in [0, 3, 6, 9]:  # Kendras
                yogas.append({
                    'name': 'Gaja Kesari Yoga',
                    'type': 'beneficial',
                    'strength': 'strong',
                    'planets_involved': ['moon', 'jupiter'],
                    'houses_involved': [moon_house, jupiter_house],
                    'description': 'Moon and Jupiter in kendras brings wisdom and prosperity',
                    'effects': ['Wisdom and knowledge', 'Financial prosperity', 'Good reputation'],
                    'strength_points': 80.0
                })
        
        # Enhanced Dosha calculations
        if mars and lagna:
            # Manglik Dosha - Mars in 1st, 4th, 7th, 8th, 12th houses
            mars_house = (mars.rasi - lagna.rasi) % 12 + 1
            if mars_house in [1, 4, 7, 8, 12]:
                severity = 'strong' if mars_house in [1, 7, 8] else 'medium'
                doshas.append({
                    'name': 'Manglik Dosha',
                    'type': 'challenging',
                    'severity': severity,
                    'planets_involved': ['mars'],
                    'houses_involved': [mars_house],
                    'description': 'Mars in challenging houses affects marriage and relationships',
                    'effects': ['Delays in marriage', 'Relationship challenges', 'Need for compatibility'],
                    'remedies': ['Mars remedies', 'Compatibility matching', 'Proper timing'],
                    'strength_points': -40.0 if severity == 'medium' else -60.0
                })
        
        if rahu and ketu:
            # Check for Kaal Sarpa Dosha - All planets between Rahu and Ketu
            planets_between = []
            all_planets = []
            
            for planet_name, position in planetary_positions.items():
                if planet_name not in ['rahu', 'ketu', 'lagna']:
                    all_planets.append(planet_name)
                    # Check if planet is between Rahu and Ketu
                    rahu_long = rahu.longitude
                    ketu_long = ketu.longitude
                    planet_long = position.longitude
                    
                    # Normalize to check if planet is in the arc between Rahu and Ketu
                    if rahu_long < ketu_long:
                        if rahu_long <= planet_long <= ketu_long:
                            planets_between.append(planet_name)
                    else:
                        if planet_long >= rahu_long or planet_long <= ketu_long:
                            planets_between.append(planet_name)
            
            if len(planets_between) == len(all_planets):
                rahu_house = (rahu.rasi - lagna.rasi) % 12 + 1
                ketu_house = (ketu.rasi - lagna.rasi) % 12 + 1
                doshas.append({
                    'name': 'Kaal Sarpa Dosha',
                    'type': 'challenging',
                    'severity': 'strong',
                    'planets_involved': ['rahu', 'ketu'] + planets_between,
                    'houses_involved': [rahu_house, ketu_house],
                    'description': 'All planets hemmed between Rahu and Ketu',
                    'effects': ['Obstacles in life', 'Delays in achievements', 'Spiritual inclination'],
                    'remedies': ['Rahu-Ketu remedies', 'Spiritual practices', 'Charity and service'],
                    'strength_points': -70.0
                })
        
        return yogas, doshas
    
    def _calculate_dasha_periods(
        self, 
        birth_data: BirthDetails,
        moon_position: Optional[PlanetaryPosition]
    ) -> Optional[Any]:
        """
        Calculate Vimshottari dasha periods with current maha/antardasha tracking.
        
        Args:
            birth_data: Birth details
            moon_position: Moon's position
            
        Returns:
            Dasha analysis data or None
        """
        if not moon_position:
            return None

        dasha_calculator = DashaCalculator()

        # Combine birth date and time; BirthDetails.date may already be datetime
        birth_date_value = birth_data.date.date() if hasattr(birth_data.date, 'date') else birth_data.date
        birth_datetime = datetime.combine(birth_date_value, birth_data.time)

        # Calculate complete Vimshottari analysis
        dasha_analysis = dasha_calculator.calculate_vimshottari_dasha(
            birth_datetime,
            moon_position.longitude
        )

        nakshatra_index, nakshatra_name, nakshatra_lord = dasha_calculator.get_nakshatra_from_longitude(
            moon_position.longitude
        )

        def serialize_period(period: Optional[Any]) -> Optional[Dict[str, Any]]:
            if not period:
                return None

            def _serialize(period_obj: Any) -> Dict[str, Any]:
                entry = {
                    'planet': period_obj.planet.title(),
                    'start_date': period_obj.start_date.isoformat() if getattr(period_obj, 'start_date', None) else None,
                    'end_date': period_obj.end_date.isoformat() if getattr(period_obj, 'end_date', None) else None,
                    'duration_years': round(period_obj.duration_years, 2)
                }
                sub_periods = getattr(period_obj, 'sub_periods', None) or []
                if sub_periods:
                    entry['sub_periods'] = [_serialize(sub) for sub in sub_periods]
                return entry

            return _serialize(period)

        return {
            'birth_nakshatra': nakshatra_index + 1,  # 1-based indexing for display
            'birth_nakshatra_name': nakshatra_name,
            'birth_nakshatra_lord': nakshatra_lord.title(),
            'dasha_balance_at_birth': round(dasha_analysis.dasha_balance_at_birth, 2),
            'total_dasha_period': round(dasha_calculator.vimshottari_periods[nakshatra_lord], 2),
            'current_dasha_lord': dasha_analysis.current_mahadasha.planet.title() if dasha_analysis.current_mahadasha else None,
            'current_mahadasha': serialize_period(dasha_analysis.current_mahadasha),
            'current_antardasha': serialize_period(dasha_analysis.current_antardasha),
            'current_pratyantardasha': serialize_period(dasha_analysis.current_pratyantardasha),
            'current_sookshma': serialize_period(dasha_analysis.current_sookshma),
            'current_prana': serialize_period(dasha_analysis.current_prana),
            'mahadasha_sequence': [
                serialize_period(period)
                for period in dasha_analysis.all_mahadashas[:10]
            ]
        }
    
    def _get_implementation_info(self) -> Dict[str, Any]:
        """
        Get information about the ephemeris implementation.
        
        Returns:
            Dictionary with implementation details
        """
        ephemeris_info = self.ephemeris_engine.get_calculation_info()
        
        return {
            'method': 'EPHEMERIS',
            'primary_engine': ephemeris_info.get('preferred_method', 'SIMPLIFIED'),
            'fallback_methods': ephemeris_info.get('fallback_methods', []),
            'swiss_ephemeris_available': SWISS_EPHEMERIS_AVAILABLE,
            'library': 'Swiss Ephemeris',
            'version': getattr(swe, '__version__', 'unknown') if SWISS_EPHEMERIS_AVAILABLE else 'n/a',
            'available': SWISS_EPHEMERIS_AVAILABLE,
            'description': 'Ephemeris-based calculations using Swiss Ephemeris with simplified fallback',
            'accuracy': 'high' if SWISS_EPHEMERIS_AVAILABLE else 'medium',
            'features': [
                'Swiss Ephemeris calculations' if SWISS_EPHEMERIS_AVAILABLE else 'Simplified calculations',
                'Enhanced divisional charts',
                'Detailed yoga/dosha analysis',
                'Complete dasha sequences',
                'Comprehensive error handling',
                'Consistent output schema'
            ]
        }
    
    def _create_astronomical_data(self, ayanamsa: str = "LAHIRI") -> Dict[str, Any]:
        """Create enhanced astronomical data section."""
        jd = getattr(self, '_current_julian_day', None)
        ephemeris_info = self.ephemeris_engine.get_calculation_info()
        context = getattr(self, '_calculation_context', {}) if hasattr(self, '_calculation_context') else {}

        return {
            'julian_day': jd,
            'ayanamsa': ayanamsa,
            'calculation_method': ephemeris_info.get('preferred_method', 'SIMPLIFIED'),
            'house_system': context.get('house_system', 'UNKNOWN'),
            'ephemeris_info': ephemeris_info,
            'implementation_info': self._get_implementation_info()
        }
    
    def _get_nakshatra_name(self, nakshatra_index: int) -> str:
        """Get nakshatra name from index."""
        nakshatra_names = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
            "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
            "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        return nakshatra_names[nakshatra_index] if 0 <= nakshatra_index < 27 else "Unknown"
    
    def _calculate_dignity(self, planet_name: str, rasi: int) -> str:
        """Calculate basic planetary dignity."""
        # Simplified dignity calculation
        dignity_map = {
            'sun': {0: 'Exalted', 6: 'Debilitated'},  # Aries exalted, Libra debilitated
            'moon': {1: 'Exalted', 7: 'Debilitated'},  # Taurus exalted, Scorpio debilitated
            'mars': {9: 'Exalted', 5: 'Debilitated'},  # Capricorn exalted, VIRGO debilitated
            'mercury': {5: 'Exalted', 11: 'Debilitated'},  # Virgo exalted, Pisces debilitated
            'jupiter': {3: 'Exalted', 6: 'Debilitated'},  # Cancer exalted, LIBRA debilitated
            'venus': {11: 'Exalted', 9: 'Debilitated'},  # Pisces exalted, CAPRICORN debilitated
            'saturn': {6: 'Exalted', 0: 'Debilitated'}  # Libra exalted, Aries debilitated
        }
        
        # Check for exaltation/debilitation first
        if planet_name in dignity_map and rasi in dignity_map[planet_name]:
            return dignity_map[planet_name][rasi]
        
        # Check for own signs
        own_signs = {
            'sun': [4],  # Leo
            'moon': [3],  # Cancer
            'mars': [0, 7],  # Aries, Scorpio
            'mercury': [2, 5],  # Gemini, Virgo
            'jupiter': [8, 11],  # Sagittarius, Pisces
            'venus': [1, 6],  # Taurus, Libra
            'saturn': [9, 10]  # Capricorn, Aquarius
        }
        
        if planet_name in own_signs and rasi in own_signs[planet_name]:
            return 'Own Sign'
        
        return 'Neutral'
    
    def _calculate_basic_strength(self, planet_name: str, rasi: int) -> float:
        """Calculate basic strength points for a planet."""
        dignity = self._calculate_dignity(planet_name, rasi)
        if dignity == 'Exalted':
            return 90.0
        elif dignity == 'Own Sign':
            return 75.0
        elif dignity == 'Debilitated':
            return 15.0
        else:
            return 50.0  # Neutral strength
    
    def _calculate_basic_aspects(self, chart_positions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate basic planetary aspects."""
        aspects = []
        planets = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn']
        
        for i, planet1 in enumerate(planets):
            if planet1 not in chart_positions:
                continue
            for planet2 in planets[i+1:]:
                if planet2 not in chart_positions:
                    continue
                
                pos1 = chart_positions[planet1]
                pos2 = chart_positions[planet2]
                
                # Calculate angular difference
                angle_diff = abs(pos1['longitude'] - pos2['longitude'])
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                
                # Check for major aspects (conjunction, opposition, trine, square)
                aspect_type = None
                if angle_diff <= 10:
                    aspect_type = 'conjunction'
                elif 170 <= angle_diff <= 190:
                    aspect_type = 'opposition'
                elif 110 <= angle_diff <= 130:
                    aspect_type = 'trine'
                elif 80 <= angle_diff <= 100:
                    aspect_type = 'square'
                
                if aspect_type:
                    aspects.append({
                        'planet1': planet1,
                        'planet2': planet2,
                        'type': aspect_type,
                        'angle': round(angle_diff, 2)
                    })
        
        return aspects
    
    def _find_chart_yogas(self, chart_positions: Dict[str, Any]) -> List[str]:
        """Find basic yogas in the chart."""
        yogas = []
        
        # Check for basic yogas
        if 'sun' in chart_positions and 'mercury' in chart_positions:
            sun_house = chart_positions['sun']['house']
            mercury_house = chart_positions['mercury']['house']
            if sun_house == mercury_house:
                yogas.append('Budh Aditya Yoga')
        
        if 'moon' in chart_positions and 'jupiter' in chart_positions:
            moon_house = chart_positions['moon']['house']
            jupiter_house = chart_positions['jupiter']['house']
            house_diff = abs(moon_house - jupiter_house)
            if house_diff in [0, 3, 6, 9]:  # Kendras
                yogas.append('Gaja Kesari Yoga')
        
        return yogas
    
    def _calculate_chart_strength_summary(self, chart_positions: Dict[str, Any]) -> Dict[str, float]:
        """Calculate overall chart strength summary."""
        total_strength = 0.0
        planet_count = 0
        
        for planet_name, position in chart_positions.items():
            if planet_name != 'lagna' and 'strength_points' in position:
                total_strength += position['strength_points']
                planet_count += 1
        
        average_strength = total_strength / planet_count if planet_count > 0 else 0.0
        
        return {
            'total_strength': round(total_strength, 2),
            'average_strength': round(average_strength, 2),
            'planet_count': planet_count
        }

    def _calculate_house_lordships(self, house_cusps: List[float]) -> Dict[int, str]:
        """Calculate the lord of each house."""
        lordships = {}
        # Mapping of sign index (0=Aries) to planet lord
        sign_lords = {
            0: 'mars', 1: 'venus', 2: 'mercury', 3: 'moon', 4: 'sun', 5: 'mercury',
            6: 'venus', 7: 'mars', 8: 'jupiter', 9: 'saturn', 10: 'saturn', 11: 'jupiter'
        }
        for i, cusp_longitude in enumerate(house_cusps):
            house_number = i + 1
            sign_index = int(cusp_longitude // 30)
            lordships[house_number] = sign_lords.get(sign_index, 'unknown')
        return lordships

    def _calculate_house_aspects(self, chart_positions: Dict[str, Any]) -> Dict[int, List[str]]:
        """Calculate which planets aspect each house."""
        aspects_on_houses = {i: [] for i in range(1, 13)}
        
        aspect_rules = {
            'mars': [4, 7, 8],
            'jupiter': [5, 7, 9],
            'saturn': [3, 7, 10],
            'sun': [7], 'moon': [7], 'mercury': [7], 'venus': [7]
        }

        for planet_name, aspect_list in aspect_rules.items():
            if planet_name not in chart_positions:
                continue
            
            planet_pos = chart_positions[planet_name]
            planet_house = planet_pos.get('house')
            if not planet_house:
                continue

            for aspect in aspect_list:
                aspected_house_num = (planet_house + aspect - 1) % 12
                if aspected_house_num == 0:
                    aspected_house_num = 12
                
                if planet_name not in aspects_on_houses[aspected_house_num]:
                    aspects_on_houses[aspected_house_num].append(planet_name)

        return aspects_on_houses

    def _calculate_planetary_relationships(self, chart_positions: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """
        Calculate five-fold (Panchadha) planetary relationships for the D1 chart.
        Combines natural and temporary relationships.
        """
        NATURAL_RELATIONSHIPS = {
            'sun': {'friends': ['moon', 'mars', 'jupiter'], 'enemies': ['venus', 'saturn'], 'neutral': ['mercury']},
            'moon': {'friends': ['sun', 'mercury'], 'enemies': [], 'neutral': ['mars', 'jupiter', 'venus', 'saturn']},
            'mars': {'friends': ['sun', 'moon', 'jupiter'], 'enemies': ['mercury'], 'neutral': ['venus', 'saturn']},
            'mercury': {'friends': ['sun', 'venus'], 'enemies': ['moon'], 'neutral': ['mars', 'jupiter', 'saturn']},
            'jupiter': {'friends': ['sun', 'moon', 'mars'], 'enemies': ['mercury', 'venus'], 'neutral': ['saturn']},
            'venus': {'friends': ['mercury', 'saturn'], 'enemies': ['sun', 'moon'], 'neutral': ['mars', 'jupiter']},
            'saturn': {'friends': ['mercury', 'venus'], 'enemies': ['sun', 'moon', 'mars'], 'neutral': ['jupiter']},
        }
        
        all_planets = list(NATURAL_RELATIONSHIPS.keys())
        final_relationships = {p: {} for p in all_planets}

        for planet1 in all_planets:
            if planet1 not in chart_positions: continue
            
            for planet2 in all_planets:
                if planet1 == planet2 or planet2 not in chart_positions: continue

                p1_house = chart_positions[planet1].get('house')
                p2_house = chart_positions[planet2].get('house')

                if not p1_house or not p2_house: continue

                relative_house = (p2_house - p1_house + 12) % 12
                if relative_house in [1, 2, 3, 9, 10, 11]:
                    temp_status = 'friend'
                else:
                    temp_status = 'enemy'

                natural_status = 'neutral'
                if planet2 in NATURAL_RELATIONSHIPS[planet1]['friends']:
                    natural_status = 'friend'
                elif planet2 in NATURAL_RELATIONSHIPS[planet1]['enemies']:
                    natural_status = 'enemy'

                if natural_status == 'friend' and temp_status == 'friend':
                    final_status = 'great_friend'
                elif natural_status == 'enemy' and temp_status == 'enemy':
                    final_status = 'great_enemy'
                elif (natural_status == 'friend' and temp_status == 'enemy') or \
                     (natural_status == 'enemy' and temp_status == 'friend'):
                    final_status = 'neutral'
                elif natural_status == 'neutral' and temp_status == 'friend':
                    final_status = 'friend'
                elif natural_status == 'neutral' and temp_status == 'enemy':
                    final_status = 'enemy'
                else:
                    final_status = 'neutral'

                final_relationships[planet1][planet2] = final_status
                
        return final_relationships
