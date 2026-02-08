"""
Comprehensive ephemeris calculation engine without PyJHora dependencies.

This module provides planetary position calculations using
Swiss Ephemeris as primary with simplified calculations as fallback.
"""

import math
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

try:
    import swisseph as swe
    SWISS_EPHEMERIS_AVAILABLE = True
except ImportError:
    SWISS_EPHEMERIS_AVAILABLE = False
    print("Warning: Swiss Ephemeris not available, using fallback methods")

from ..core.data_models import PlanetaryPosition, ValidationResult


class Planet(Enum):
    """Planetary constants for calculations."""
    SUN = 0
    MOON = 1
    MARS = 2
    MERCURY = 3
    JUPITER = 4
    VENUS = 5
    SATURN = 6
    RAHU = 7  # North Node
    KETU = 8  # South Node
    LAGNA = 9  # Ascendant


class CalculationMethod(Enum):
    """Available calculation methods."""
    SWISS_EPHEMERIS = "SWISS_EPHEMERIS"
    SIMPLIFIED = "SIMPLIFIED"


AYANAMSA_MAP = {
    # Most Popular Vedic Systems
    "TRUE_CITRA": swe.SIDM_TRUE_CITRA if SWISS_EPHEMERIS_AVAILABLE else None,
    "LAHIRI": swe.SIDM_LAHIRI if SWISS_EPHEMERIS_AVAILABLE else None,
    "KRISHNAMURTI": swe.SIDM_KRISHNAMURTI if SWISS_EPHEMERIS_AVAILABLE else None,
    "RAMAN": swe.SIDM_RAMAN if SWISS_EPHEMERIS_AVAILABLE else None,
    # Traditional Systems
    "TRUE_REVATI": swe.SIDM_TRUE_REVATI if SWISS_EPHEMERIS_AVAILABLE else None,
    "TRUE_PUSHYA": swe.SIDM_TRUE_PUSHYA if SWISS_EPHEMERIS_AVAILABLE else None,
    "SURYASIDDHANTA": swe.SIDM_SURYASIDDHANTA if SWISS_EPHEMERIS_AVAILABLE else None,
    "ARYABHATA": swe.SIDM_ARYABHATA if SWISS_EPHEMERIS_AVAILABLE else None,
    # Western Sidereal Systems
    "FAGAN_BRADLEY": swe.SIDM_FAGAN_BRADLEY if SWISS_EPHEMERIS_AVAILABLE else None,
    "DELUCE": swe.SIDM_DELUCE if SWISS_EPHEMERIS_AVAILABLE else None,
    # Research & Specialized Systems
    "YUKTESHWAR": swe.SIDM_YUKTESHWAR if SWISS_EPHEMERIS_AVAILABLE else None,
    "JN_BHASIN": swe.SIDM_JN_BHASIN if SWISS_EPHEMERIS_AVAILABLE else None,
    "DJWHAL_KHUL": swe.SIDM_DJWHAL_KHUL if SWISS_EPHEMERIS_AVAILABLE else None,
    "USHASHASHI": swe.SIDM_USHASHASHI if SWISS_EPHEMERIS_AVAILABLE else None,
    # Galactic Systems
    "GALCENT_0SAG": swe.SIDM_GALCENT_0SAG if SWISS_EPHEMERIS_AVAILABLE else None,
    "TRUE_MULA": swe.SIDM_TRUE_MULA if SWISS_EPHEMERIS_AVAILABLE else None,
    # Historical Systems
    "HIPPARCHOS": swe.SIDM_HIPPARCHOS if SWISS_EPHEMERIS_AVAILABLE else None,
    "SASSANIAN": swe.SIDM_SASSANIAN if SWISS_EPHEMERIS_AVAILABLE else None,
    # Modern Variants
    "LAHIRI_1940": swe.SIDM_LAHIRI_1940 if SWISS_EPHEMERIS_AVAILABLE else None,
    "LAHIRI_ICRC": swe.SIDM_LAHIRI_ICRC if SWISS_EPHEMERIS_AVAILABLE else None,
    "KRISHNAMURTI_VP291": swe.SIDM_KRISHNAMURTI_VP291 if SWISS_EPHEMERIS_AVAILABLE else None,
}

HOUSE_SYSTEM_CODES = {
    'EQUAL': 'A',
    'EQUAL_START': 'A',
    'EQUAL_MID': 'V',
    # SRIPATI uses Swiss Ephemeris native Sripati system
    'SRIPATI': 'S',
    # BHAVA_CHALIT uses Sripati cusps with midpoint-based planet placement
    # This is handled specially in calculate_house_cusps()
    'BHAVA_CHALIT': 'SRIPATI_SPECIAL',  # Marker for special handling
    'PLACIDUS': 'P',
    'KP': 'P',
    'KOCH': 'K',
    'PORPHYRY': 'O',
    'REGIOMONTANUS': 'R',
    'CAMPANUS': 'C',
    'VEHLOW': 'V',
}


class ComprehensiveEphemerisEngine:
    """
    Comprehensive ephemeris calculation engine with Swiss Ephemeris and simplified fallback.
    """
    
    def __init__(self, ephemeris_path: Optional[str] = None):
        """
        Initialize ephemeris engine.
        
        Args:
            ephemeris_path: Path to Swiss Ephemeris data files
        """
        # Allow override via env var if no explicit path provided
        default_ephe = os.getenv("ASTRO_CORE_EPHEMERIS_PATH", "/usr/share/ephe")
        self.ephemeris_path = ephemeris_path or default_ephe
        self.preferred_method = self._determine_preferred_method()
        self.fallback_methods = self._get_fallback_methods()
        
        # Initialize Swiss Ephemeris if available
        if SWISS_EPHEMERIS_AVAILABLE:
            try:
                swe.set_ephe_path(self.ephemeris_path)
            except Exception as e:
                print(f"Warning: Could not set Swiss Ephemeris path: {e}")
    
    def calculate_planetary_positions(
        self,
        julian_day: float,
        latitude: float,
        longitude: float,
        ayanamsa: str = "LAHIRI"
    ) -> Dict[str, PlanetaryPosition]:
        """
        Calculate planetary positions for all planets.
        
        Args:
            julian_day: Julian Day Number for calculation
            latitude: Observer latitude in degrees
            longitude: Observer longitude in degrees
            ayanamsa: Ayanamsa system to use
            
        Returns:
            Dictionary of planetary positions
        """
        positions = {}
        
        # Calculate positions for all planets
        for planet in Planet:
            if planet == Planet.LAGNA:
                # Calculate Lagna (Ascendant) separately
                position = self.calculate_lagna(julian_day, latitude, longitude, ayanamsa)
            else:
                position = self.calculate_planet_position(planet, julian_day, ayanamsa)
            
            if position:
                positions[planet.name.lower()] = position
        
        return positions

    def calculate_house_cusps(
        self,
        julian_day: float,
        latitude: float,
        longitude: float,
        ayanamsa: str = "LAHIRI",
        house_system: str = "PLACIDUS",
    ) -> Optional[List[float]]:
        """
        Calculate house cusps using Swiss Ephemeris.

        For SRIPATI and BHAVA_CHALIT, implements true Sripati calculation:
        Sripati_cusp[i] = (Equal_cusp[i] + Placidus_cusp[i]) / 2

        Args:
            julian_day: Julian Day Number
            latitude: Observer latitude in degrees
            longitude: Observer longitude in degrees
            ayanamsa: Ayanamsa system to use
            house_system: House system (EQUAL, PLACIDUS, SRIPATI, BHAVA_CHALIT, etc.)

        Returns:
            List of 12 house cusp longitudes in degrees, or None if unavailable
        """
        if not SWISS_EPHEMERIS_AVAILABLE:
            return None

        system_key = (house_system or 'PLACIDUS').upper()
        swe_mode = AYANAMSA_MAP.get(ayanamsa.upper(), swe.SIDM_TRUE_CITRA)
        swe.set_sid_mode(swe_mode)

        house_code = HOUSE_SYSTEM_CODES.get(system_key, HOUSE_SYSTEM_CODES['PLACIDUS'])

        # Handle true Sripati calculation: (Equal + Placidus) / 2
        if house_code == 'SRIPATI_SPECIAL':
            return self._calculate_sripati_cusps(julian_day, latitude, longitude)

        houses, _ = swe.houses_ex(
            julian_day,
            latitude,
            longitude,
            house_code.encode('ascii'),
            swe.FLG_SIDEREAL,
        )
        return [house % 360 for house in houses]

    def _calculate_sripati_cusps(
        self,
        julian_day: float,
        latitude: float,
        longitude: float,
    ) -> List[float]:
        """
        Calculate Sripati house cusps using Swiss Ephemeris native implementation.

        Sripati is a traditional Vedic house system that uses:
        - 10th house cusp = MC (Midheaven)
        - 1st house cusp = Ascendant
        - Intermediate houses calculated using a specific trisection formula

        This is NOT the same as (Equal + Placidus) / 2, which was an incorrect
        approximation used previously.

        Args:
            julian_day: Julian Day Number
            latitude: Observer latitude in degrees
            longitude: Observer longitude in degrees

        Returns:
            List of 12 Sripati house cusp longitudes in degrees
        """
        # Use Swiss Ephemeris native Sripati house system (code 'S')
        sripati_houses, ascmc = swe.houses_ex(
            julian_day,
            latitude,
            longitude,
            b'S',  # Sripati
            swe.FLG_SIDEREAL,
        )

        # Return normalized cusps (0-360)
        return [cusp % 360 for cusp in sripati_houses[:12]]
    
    def calculate_planet_position(
        self, 
        planet: Planet, 
        julian_day: float,
        ayanamsa: str = "LAHIRI"
    ) -> Optional[PlanetaryPosition]:
        """
        Calculate position for a specific planet using available methods.
        
        Args:
            planet: Planet to calculate
            julian_day: Julian Day Number
            ayanamsa: Ayanamsa system to use
            
        Returns:
            PlanetaryPosition object or None if calculation fails
        """
        # Try preferred method first
        position = self._calculate_with_method(planet, julian_day, ayanamsa, self.preferred_method)
        
        if position:
            return position
        
        # Try fallback methods
        for method in self.fallback_methods:
            position = self._calculate_with_method(planet, julian_day, ayanamsa, method)
            if position:
                return position
        
        print(f"Warning: Could not calculate position for {planet.name}")
        return None
    
    def calculate_lagna(
        self, 
        julian_day: float, 
        latitude: float, 
        longitude: float,
        ayanamsa: str = "LAHIRI"
    ) -> Optional[PlanetaryPosition]:
        """
        Calculate Lagna (Ascendant) position.
        
        Args:
            julian_day: Julian Day Number
            latitude: Observer latitude in degrees
            longitude: Observer longitude in degrees
            ayanamsa: Ayanamsa system to use
            
        Returns:
            PlanetaryPosition for Lagna or None if calculation fails
        """
        try:
            if SWISS_EPHEMERIS_AVAILABLE:
                return self._calculate_lagna_swiss(julian_day, latitude, longitude, ayanamsa)
            else:
                return self._calculate_lagna_simplified(julian_day, latitude, longitude)
        except Exception as e:
            print(f"Error calculating Lagna: {e}")
            return None
    
    def julian_day_from_datetime(self, dt: datetime, timezone_offset: float = 0.0) -> float:
        """
        Convert datetime to Julian Day Number.
        
        Args:
            dt: Datetime object
            timezone_offset: Timezone offset in hours
            
        Returns:
            Julian Day Number
        """
        # Convert to UTC
        utc_dt = dt - timedelta(hours=timezone_offset)
        
        # Calculate Julian Day
        a = (14 - utc_dt.month) // 12
        y = utc_dt.year + 4800 - a
        m = utc_dt.month + 12 * a - 3
        
        jd = utc_dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        
        # Add time fraction
        time_fraction = (utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0) / 24.0
        
        return jd + time_fraction - 0.5
    
    def datetime_from_julian_day(self, jd: float, timezone_offset: float = 0.0) -> datetime:
        """
        Convert Julian Day Number to datetime.
        
        Args:
            jd: Julian Day Number
            timezone_offset: Timezone offset in hours
            
        Returns:
            Datetime object
        """
        # Convert Julian Day to UTC datetime
        jd = jd + 0.5
        z = int(jd)
        f = jd - z
        
        if z < 2299161:
            a = z
        else:
            alpha = int((z - 1867216.25) / 36524.25)
            a = z + 1 + alpha - alpha // 4
        
        b = a + 1524
        c = int((b - 122.1) / 365.25)
        d = int(365.25 * c)
        e = int((b - d) / 30.6001)
        
        day = b - d - int(30.6001 * e)
        month = e - 1 if e < 14 else e - 13
        year = c - 4716 if month > 2 else c - 4715
        
        # Calculate time
        time_fraction = f
        hours = time_fraction * 24
        hour = int(hours)
        minutes = (hours - hour) * 60
        minute = int(minutes)
        seconds = (minutes - minute) * 60
        second = int(seconds)
        
        utc_dt = datetime(year, month, day, hour, minute, second)
        
        # Convert to local time
        local_dt = utc_dt + timedelta(hours=timezone_offset)
        
        return local_dt

    def calculate_ayanamsa(self, julian_day: float, system: str = "LAHIRI") -> float:
        """
        Calculate ayanamsa (precessional offset) in degrees for a given Julian Day.
        Uses Swiss Ephemeris when available, with a robust fallback approximation.
        
        Args:
            julian_day: Julian Day Number (UT)
            system: Ayanamsa system key (matches mapping used elsewhere)
        Returns:
            Ayanamsa in degrees (0-360)
        """
        try:
            if SWISS_EPHEMERIS_AVAILABLE:
                # Align sidereal mode to requested system
                ayanamsa_map = {
                    "TRUE_CITRA": swe.SIDM_TRUE_CITRA,
                    "LAHIRI": swe.SIDM_LAHIRI,
                    "KRISHNAMURTI": swe.SIDM_KRISHNAMURTI,
                    "RAMAN": swe.SIDM_RAMAN,
                    "TRUE_REVATI": swe.SIDM_TRUE_REVATI,
                    "TRUE_PUSHYA": swe.SIDM_TRUE_PUSHYA,
                    "SURYASIDDHANTA": swe.SIDM_SURYASIDDHANTA,
                    "ARYABHATA": swe.SIDM_ARYABHATA,
                    "FAGAN_BRADLEY": swe.SIDM_FAGAN_BRADLEY,
                    "DELUCE": swe.SIDM_DELUCE,
                    "YUKTESHWAR": swe.SIDM_YUKTESHWAR,
                    "JN_BHASIN": swe.SIDM_JN_BHASIN,
                    "DJWHAL_KHUL": swe.SIDM_DJWHAL_KHUL,
                    "USHASHASHI": swe.SIDM_USHASHASHI,
                    "GALCENT_0SAG": swe.SIDM_GALCENT_0SAG,
                    "TRUE_MULA": swe.SIDM_TRUE_MULA,
                    "HIPPARCHOS": swe.SIDM_HIPPARCHOS,
                    "SASSANIAN": swe.SIDM_SASSANIAN,
                    "LAHIRI_1940": swe.SIDM_LAHIRI_1940,
                    "LAHIRI_ICRC": swe.SIDM_LAHIRI_ICRC,
                    "KRISHNAMURTI_VP291": swe.SIDM_KRISHNAMURTI_VP291
                }
                swe.set_sid_mode(ayanamsa_map.get(system, swe.SIDM_TRUE_CITRA))
                value = swe.get_ayanamsa_ut(julian_day)
                # Normalize to 0-360
                return value % 360
            else:
                # Fallback: simple linear precession approximation relative to J2000
                # Approx 50.29 arcseconds/year ≈ 0.01397°/year
                jd_j2000 = 2451545.0
                years_since = (julian_day - jd_j2000) / 365.25
                approx_ayanamsa_2000 = 24.0  # rough degrees at J2000 for Lahiri-like systems
                value = approx_ayanamsa_2000 + years_since * 0.01397
                return value % 360
        except Exception:
            # Safe fallback
            return 24.0
    
    def _determine_preferred_method(self) -> CalculationMethod:
        """Determine the preferred calculation method based on availability."""
        if SWISS_EPHEMERIS_AVAILABLE:
            return CalculationMethod.SWISS_EPHEMERIS
        else:
            return CalculationMethod.SIMPLIFIED
    
    def _get_fallback_methods(self) -> List[CalculationMethod]:
        """Get list of fallback methods in order of preference."""
        methods = []
        
        if self.preferred_method != CalculationMethod.SWISS_EPHEMERIS and SWISS_EPHEMERIS_AVAILABLE:
            methods.append(CalculationMethod.SWISS_EPHEMERIS)
        
        if self.preferred_method != CalculationMethod.SIMPLIFIED:
            methods.append(CalculationMethod.SIMPLIFIED)
        
        return methods
    
    def _calculate_with_method(
        self, 
        planet: Planet, 
        julian_day: float, 
        ayanamsa: str,
        method: CalculationMethod
    ) -> Optional[PlanetaryPosition]:
        """Calculate planet position using specific method."""
        try:
            if method == CalculationMethod.SWISS_EPHEMERIS:
                return self._calculate_swiss_ephemeris(planet, julian_day, ayanamsa)
            elif method == CalculationMethod.SIMPLIFIED:
                return self._calculate_simplified(planet, julian_day)
        except Exception as e:
            print(f"Error with {method.value} for {planet.name}: {e}")
        
        return None
    
    def _calculate_swiss_ephemeris(
        self, 
        planet: Planet, 
        julian_day: float, 
        ayanamsa: str
    ) -> Optional[PlanetaryPosition]:
        """Calculate using Swiss Ephemeris."""
        if not SWISS_EPHEMERIS_AVAILABLE:
            return None
        
        try:
            # Map planet to Swiss Ephemeris constants
            planet_map = {
                Planet.SUN: swe.SUN,
                Planet.MOON: swe.MOON,
                Planet.MARS: swe.MARS,
                Planet.MERCURY: swe.MERCURY,
                Planet.JUPITER: swe.JUPITER,
                Planet.VENUS: swe.VENUS,
                Planet.SATURN: swe.SATURN,
                Planet.RAHU: swe.MEAN_NODE,
                Planet.KETU: swe.MEAN_NODE  # Ketu is 180° from Rahu
            }
            
            if planet not in planet_map:
                return None
            
            # Set ayanamsa - comprehensive mapping of popular systems
            swe.set_sid_mode(AYANAMSA_MAP.get(ayanamsa.upper(), swe.SIDM_TRUE_CITRA))
            
            # Calculate position
            result, ret_flag = swe.calc_ut(julian_day, planet_map[planet], swe.FLG_SIDEREAL)
            
            if ret_flag < 0:
                print(f"Swiss Ephemeris error flag: {ret_flag}")
                return None
            
            longitude = result[0]
            
            # Handle Ketu (180° from Rahu)
            if planet == Planet.KETU:
                longitude = (longitude + 180) % 360
            
            # Check if retrograde (speed is in result[3])
            speed = result[3] if len(result) > 3 else 0
            retrograde = speed < 0
            
            # Convert to rasi and nakshatra
            rasi = int(longitude // 30)
            degree_in_sign = longitude % 30
            nakshatra = int(longitude * 27 / 360) % 27
            
            return PlanetaryPosition(
                longitude=longitude,
                rasi=rasi,
                nakshatra=nakshatra,
                degree_in_sign=degree_in_sign,
                retrograde=retrograde
            )
            
        except Exception as e:
            print(f"Swiss Ephemeris calculation error for {planet.name}: {e}")
            return None
    
    def _calculate_simplified(self, planet: Planet, julian_day: float) -> Optional[PlanetaryPosition]:
        """Calculate using simplified astronomical formulas."""
        try:
            # Days since J2000.0
            d = julian_day - 2451545.0
            
            # Simplified orbital elements (approximate)
            orbital_elements = {
                Planet.SUN: {'L': 280.460, 'g': 357.528, 'e': 0.0167, 'a': 1.0},
                Planet.MOON: {'L': 218.316, 'g': 134.963, 'e': 0.0549, 'a': 60.2666},
                Planet.MERCURY: {'L': 252.251, 'g': 149.472, 'e': 0.2056, 'a': 0.3871},
                Planet.VENUS: {'L': 181.980, 'g': 162.552, 'e': 0.0068, 'a': 0.7233},
                Planet.MARS: {'L': 355.433, 'g': 319.529, 'e': 0.0934, 'a': 1.5237},
                Planet.JUPITER: {'L': 34.351, 'g': 225.328, 'e': 0.0484, 'a': 5.2026},
                Planet.SATURN: {'L': 50.078, 'g': 175.476, 'e': 0.0542, 'a': 9.5549}
            }
            
            if planet not in orbital_elements:
                # For Rahu/Ketu, use simplified node calculation
                if planet == Planet.RAHU:
                    longitude = (125.0 - 0.0529539 * d) % 360
                elif planet == Planet.KETU:
                    longitude = (125.0 - 0.0529539 * d + 180) % 360
                else:
                    return None
            else:
                elements = orbital_elements[planet]
                
                # Mean longitude
                L = (elements['L'] + d * self._get_daily_motion(planet)) % 360
                
                # Mean anomaly
                M = math.radians((L - elements['g']) % 360)
                
                # Equation of center (simplified)
                C = elements['e'] * math.sin(M) * 180 / math.pi
                
                # True longitude
                longitude = (L + C) % 360
            
            # Convert to tropical longitude (simplified - no proper ayanamsa)
            # Apply approximate ayanamsa of 24 degrees
            longitude = (longitude - 24) % 360
            
            # Convert to rasi and nakshatra
            rasi = int(longitude // 30)
            degree_in_sign = longitude % 30
            nakshatra = int(longitude * 27 / 360) % 27
            
            return PlanetaryPosition(
                longitude=longitude,
                rasi=rasi,
                nakshatra=nakshatra,
                degree_in_sign=degree_in_sign,
                retrograde=False  # Simplified calculation doesn't include retrograde
            )
            
        except Exception as e:
            print(f"Simplified calculation error for {planet.name}: {e}")
            return None
    
    def _get_daily_motion(self, planet: Planet) -> float:
        """Get approximate daily motion for planets in degrees per day."""
        daily_motions = {
            Planet.SUN: 0.9856,
            Planet.MOON: 13.1764,
            Planet.MERCURY: 1.3833,
            Planet.VENUS: 1.6021,
            Planet.MARS: 0.5240,
            Planet.JUPITER: 0.0831,
            Planet.SATURN: 0.0335
        }
        return daily_motions.get(planet, 0.0)
    
    def _calculate_lagna_swiss(
        self, 
        julian_day: float, 
        latitude: float, 
        longitude: float, 
        ayanamsa: str
    ) -> Optional[PlanetaryPosition]:
        """Calculate Lagna using Swiss Ephemeris."""
        try:
            # Set ayanamsa - comprehensive mapping of popular systems
            ayanamsa_map = {
                # Most Popular Vedic Systems
                "TRUE_CITRA": swe.SIDM_TRUE_CITRA,           # True Chitra Paksha (default)
                "LAHIRI": swe.SIDM_LAHIRI,                   # Lahiri (most common in India)
                "KRISHNAMURTI": swe.SIDM_KRISHNAMURTI,       # KP System
                "RAMAN": swe.SIDM_RAMAN,                     # B.V. Raman
                
                # Traditional Systems
                "TRUE_REVATI": swe.SIDM_TRUE_REVATI,         # True Revati Paksha
                "TRUE_PUSHYA": swe.SIDM_TRUE_PUSHYA,         # True Pushya Paksha
                "SURYASIDDHANTA": swe.SIDM_SURYASIDDHANTA,   # Surya Siddhanta
                "ARYABHATA": swe.SIDM_ARYABHATA,             # Aryabhata
                
                # Western Sidereal Systems
                "FAGAN_BRADLEY": swe.SIDM_FAGAN_BRADLEY,     # Fagan-Bradley
                "DELUCE": swe.SIDM_DELUCE,                   # De Luce
                
                # Research & Specialized Systems
                "YUKTESHWAR": swe.SIDM_YUKTESHWAR,           # Sri Yukteshwar
                "JN_BHASIN": swe.SIDM_JN_BHASIN,             # J.N. Bhasin
                "DJWHAL_KHUL": swe.SIDM_DJWHAL_KHUL,         # Djwhal Khul
                "USHASHASHI": swe.SIDM_USHASHASHI,           # Usha-Shashi
                
                # Galactic Systems
                "GALCENT_0SAG": swe.SIDM_GALCENT_0SAG,       # Galactic Center at 0° Sagittarius
                "TRUE_MULA": swe.SIDM_TRUE_MULA,             # True Mula
                
                # Historical Systems
                "HIPPARCHOS": swe.SIDM_HIPPARCHOS,           # Hipparchos
                "SASSANIAN": swe.SIDM_SASSANIAN,             # Sassanian
                
                # Modern Variants
                "LAHIRI_1940": swe.SIDM_LAHIRI_1940,         # Lahiri 1940
                "LAHIRI_ICRC": swe.SIDM_LAHIRI_ICRC,         # Lahiri ICRC
                "KRISHNAMURTI_VP291": swe.SIDM_KRISHNAMURTI_VP291  # KP VP291
            }
            
            swe.set_sid_mode(ayanamsa_map.get(ayanamsa, swe.SIDM_TRUE_CITRA))
            
            # Calculate houses using Placidus system
            houses, ascmc = swe.houses_ex(julian_day, latitude, longitude, b'P', swe.FLG_SIDEREAL)
            ascendant_longitude = ascmc[0]  # Ascendant is first element in ascmc
            
            # Convert to rasi and nakshatra
            rasi = int(ascendant_longitude // 30)
            degree_in_sign = ascendant_longitude % 30
            nakshatra = int(ascendant_longitude * 27 / 360) % 27
            
            return PlanetaryPosition(
                longitude=ascendant_longitude,
                rasi=rasi,
                nakshatra=nakshatra,
                degree_in_sign=degree_in_sign,
                retrograde=False
            )
            
        except Exception as e:
            print(f"Swiss Ephemeris Lagna calculation error: {e}")
            return None
    
    def _calculate_lagna_simplified(
        self, 
        julian_day: float, 
        latitude: float, 
        longitude: float
    ) -> Optional[PlanetaryPosition]:
        """Calculate Lagna using simplified method."""
        try:
            # Convert Julian Day to datetime
            dt = self.datetime_from_julian_day(julian_day)
            
            # Calculate Local Sidereal Time
            # Days since J2000.0
            d = julian_day - 2451545.0
            
            # Greenwich Mean Sidereal Time at 0h UT
            gmst = (18.697374558 + 24.06570982441908 * d) % 24
            
            # Local Sidereal Time
            lst = (gmst + longitude / 15.0) % 24
            
            # Convert to degrees
            lst_degrees = lst * 15.0
            
            # Simple ascendant calculation (very approximate)
            # This is a rough approximation and not accurate for precise calculations
            ascendant_longitude = (lst_degrees + latitude * 0.5) % 360
            
            # Apply approximate ayanamsa
            ascendant_longitude = (ascendant_longitude - 24) % 360
            
            # Convert to rasi and nakshatra
            rasi = int(ascendant_longitude // 30)
            degree_in_sign = ascendant_longitude % 30
            nakshatra = int(ascendant_longitude * 27 / 360) % 27
            
            return PlanetaryPosition(
                longitude=ascendant_longitude,
                rasi=rasi,
                nakshatra=nakshatra,
                degree_in_sign=degree_in_sign,
                retrograde=False
            )
            
        except Exception as e:
            print(f"Simplified Lagna calculation error: {e}")
            return None
    
    def get_calculation_info(self) -> Dict[str, Any]:
        """Get information about available calculation methods."""
        return {
            'preferred_method': self.preferred_method.value,
            'fallback_methods': [method.value for method in self.fallback_methods],
            'swiss_ephemeris_available': SWISS_EPHEMERIS_AVAILABLE,
            'ephemeris_path': self.ephemeris_path
        }
