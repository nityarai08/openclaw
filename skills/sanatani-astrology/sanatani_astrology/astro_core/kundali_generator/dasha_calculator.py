"""
Dasha period calculation system.

This module implements Vimshottari Mahadasha calculation from moon position,
including Antardasha and Pratyantardasha periods, current period identification,
and dasha lord strength assessment.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass, field
import math

from ..core.data_models import PlanetaryPosition


class DashaSystem(Enum):
    """Types of dasha systems."""
    VIMSHOTTARI = "Vimshottari"
    ASHTOTTARI = "Ashtottari"
    YOGINI = "Yogini"
    CHARA = "Chara"


class DashaPlanet(Enum):
    """Planets in dasha sequence."""
    KETU = "Ketu"
    VENUS = "Venus"
    SUN = "Sun"
    MOON = "Moon"
    MARS = "Mars"
    RAHU = "Rahu"
    JUPITER = "Jupiter"
    SATURN = "Saturn"
    MERCURY = "Mercury"


@dataclass
class DashaPeriod:
    """Information about a dasha period."""
    planet: str
    start_date: datetime
    end_date: datetime
    duration_years: float
    duration_days: int
    level: str  # "Mahadasha", "Antardasha", "Pratyantardasha", "Sookshma", "Prana"
    parent_period: Optional['DashaPeriod'] = None
    sub_periods: List['DashaPeriod'] = field(default_factory=list)


@dataclass
class DashaAnalysis:
    """Complete dasha analysis."""
    birth_date: datetime
    moon_longitude: float
    birth_nakshatra: str
    birth_nakshatra_lord: str
    current_mahadasha: DashaPeriod
    current_antardasha: DashaPeriod
    current_pratyantardasha: Optional[DashaPeriod]
    current_sookshma: Optional[DashaPeriod]
    current_prana: Optional[DashaPeriod]
    all_mahadashas: List[DashaPeriod]
    dasha_balance_at_birth: float  # Years remaining in birth nakshatra dasha


class DashaCalculator:
    """Calculator for Vimshottari and other dasha systems."""
    
    def __init__(self):
        # Vimshottari dasha periods in years
        self.vimshottari_periods = {
            'ketu': 7,
            'venus': 20,
            'sun': 6,
            'moon': 10,
            'mars': 7,
            'rahu': 18,
            'jupiter': 16,
            'saturn': 19,
            'mercury': 17
        }
        
        # Nakshatra lords in Vimshottari sequence
        self.nakshatra_lords = [
            'ketu',    # Ashwini (0)
            'venus',   # Bharani (1)
            'sun',     # Krittika (2)
            'moon',    # Rohini (3)
            'mars',    # Mrigashira (4)
            'rahu',    # Ardra (5)
            'jupiter', # Punarvasu (6)
            'saturn',  # Pushya (7)
            'mercury', # Ashlesha (8)
            'ketu',    # Magha (9)
            'venus',   # Purva Phalguni (10)
            'sun',     # Uttara Phalguni (11)
            'moon',    # Hasta (12)
            'mars',    # Chitra (13)
            'rahu',    # Swati (14)
            'jupiter', # Vishakha (15)
            'saturn',  # Anuradha (16)
            'mercury', # Jyeshtha (17)
            'ketu',    # Mula (18)
            'venus',   # Purva Ashadha (19)
            'sun',     # Uttara Ashadha (20)
            'moon',    # Shravana (21)
            'mars',    # Dhanishta (22)
            'rahu',    # Shatabhisha (23)
            'jupiter', # Purva Bhadrapada (24)
            'saturn',  # Uttara Bhadrapada (25)
            'mercury'  # Revati (26)
        ]
        
        # Nakshatra names
        self.nakshatra_names = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
            "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
            "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
            "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha",
            "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        
        # Dasha sequence starting from any planet
        self.dasha_sequence = ['ketu', 'venus', 'sun', 'moon', 'mars', 'rahu', 'jupiter', 'saturn', 'mercury']
    
    def calculate_vimshottari_dasha(
        self,
        birth_date: datetime,
        moon_longitude: float
    ) -> DashaAnalysis:
        """
        Calculate complete Vimshottari dasha analysis.
        
        Args:
            birth_date: Birth date and time
            moon_longitude: Moon's longitude in degrees
            
        Returns:
            Complete dasha analysis
        """
        # Calculate birth nakshatra
        nakshatra_index = int(moon_longitude * 27 / 360) % 27
        birth_nakshatra = self.nakshatra_names[nakshatra_index]
        birth_nakshatra_lord = self.nakshatra_lords[nakshatra_index]
        
        # Calculate dasha balance at birth
        dasha_balance = self._calculate_dasha_balance_at_birth(moon_longitude, birth_nakshatra_lord)
        
        # Generate all mahadashas
        all_mahadashas = self._generate_all_mahadashas(birth_date, birth_nakshatra_lord, dasha_balance)
        
        # Find current periods
        current_date = datetime.now()
        current_mahadasha = self._find_current_period(current_date, all_mahadashas)
        
        # Generate antardashas for current mahadasha
        current_antardasha = None
        current_pratyantardasha = None
        current_sookshma = None
        current_prana = None
        
        if current_mahadasha:
            current_mahadasha.sub_periods = self._generate_antardashas(current_mahadasha)
            current_antardasha = self._find_current_period(current_date, current_mahadasha.sub_periods)
            
            # Generate pratyantardashas for current antardasha
            if current_antardasha:
                current_antardasha.sub_periods = self._generate_pratyantardashas(current_antardasha)
                current_pratyantardasha = self._find_current_period(current_date, current_antardasha.sub_periods)
                
                # Generate sookshma dashas for current pratyantardasha
                if current_pratyantardasha:
                    current_pratyantardasha.sub_periods = self._generate_sookshmas(current_pratyantardasha)
                    current_sookshma = self._find_current_period(current_date, current_pratyantardasha.sub_periods)

                    # Generate prana dashas for current sookshma
                    if current_sookshma:
                        current_sookshma.sub_periods = self._generate_pranas(current_sookshma)
                        current_prana = self._find_current_period(current_date, current_sookshma.sub_periods)
        
        return DashaAnalysis(
            birth_date=birth_date,
            moon_longitude=moon_longitude,
            birth_nakshatra=birth_nakshatra,
            birth_nakshatra_lord=birth_nakshatra_lord,
            current_mahadasha=current_mahadasha,
            current_antardasha=current_antardasha,
            current_pratyantardasha=current_pratyantardasha,
            current_sookshma=current_sookshma,
            current_prana=current_prana,
            all_mahadashas=all_mahadashas,
            dasha_balance_at_birth=dasha_balance
        )
    
    def get_dasha_at_date(
        self,
        target_date: datetime,
        dasha_analysis: DashaAnalysis
    ) -> Tuple[Optional[DashaPeriod], Optional[DashaPeriod], Optional[DashaPeriod]]:
        """
        Get dasha periods active at a specific date.
        
        Args:
            target_date: Date to check
            dasha_analysis: Complete dasha analysis
            
        Returns:
            Tuple of (Mahadasha, Antardasha, Pratyantardasha) at target date
        """
        # Find mahadasha at target date
        mahadasha = self._find_current_period(target_date, dasha_analysis.all_mahadashas)
        
        if not mahadasha:
            return None, None, None
        
        # Generate antardashas if not already generated
        if not mahadasha.sub_periods:
            mahadasha.sub_periods = self._generate_antardashas(mahadasha)
        
        # Find antardasha at target date
        antardasha = self._find_current_period(target_date, mahadasha.sub_periods)
        
        if not antardasha:
            return mahadasha, None, None
        
        # Generate pratyantardashas if not already generated
        if not antardasha.sub_periods:
            antardasha.sub_periods = self._generate_pratyantardashas(antardasha)
        
        # Find pratyantardasha at target date
        pratyantardasha = self._find_current_period(target_date, antardasha.sub_periods)
        
        return mahadasha, antardasha, pratyantardasha
    
    def calculate_dasha_strength(
        self,
        dasha_planet: str,
        planetary_positions: Dict[str, PlanetaryPosition]
    ) -> float:
        """
        Calculate strength of a dasha lord.
        
        Args:
            dasha_planet: Planet whose dasha strength to calculate
            planetary_positions: All planetary positions
            
        Returns:
            Strength score (0-100)
        """
        if dasha_planet not in planetary_positions:
            return 0.0
        
        position = planetary_positions[dasha_planet]
        strength = 0.0
        
        # Dignity-based strength
        dignity_scores = {
            'Exalted': 25.0,
            'Moolatrikona': 20.0,
            'Own Sign': 18.0,
            'Friendly': 12.0,
            'Neutral': 8.0,
            'Enemy': 4.0,
            'Debilitated': 0.0
        }
        
        # Get dignity from position (simplified)
        dignity = getattr(position, 'dignity', 'Neutral')
        if hasattr(dignity, 'value'):
            dignity = dignity.value
        
        strength += dignity_scores.get(dignity, 8.0)
        
        # House-based strength
        # Assuming we have house information
        house = getattr(position, 'house', 1)
        if hasattr(house, 'house'):
            house = house.house
        
        house_scores = {
            1: 20.0, 4: 15.0, 7: 15.0, 10: 20.0,  # Kendra houses
            5: 18.0, 9: 18.0,                      # Trikona houses
            2: 12.0, 11: 15.0,                     # Wealth houses
            3: 10.0, 6: 8.0, 8: 5.0, 12: 5.0      # Other houses
        }
        
        strength += house_scores.get(house, 8.0)
        
        # Retrograde consideration
        if getattr(position, 'retrograde', False):
            strength += 5.0  # Retrograde planets are considered stronger in some contexts
        
        # Normalize to 0-100 scale
        return min(strength, 100.0)
    
    def get_dasha_timeline(
        self,
        dasha_analysis: DashaAnalysis,
        start_year: int,
        end_year: int
    ) -> List[Dict[str, Any]]:
        """
        Get dasha timeline for a specific year range.
        
        Args:
            dasha_analysis: Complete dasha analysis
            start_year: Start year for timeline
            end_year: End year for timeline
            
        Returns:
            List of dasha periods in the specified range
        """
        timeline = []
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        
        for mahadasha in dasha_analysis.all_mahadashas:
            # Check if mahadasha overlaps with our date range
            if (mahadasha.end_date >= start_date and mahadasha.start_date <= end_date):
                
                # Generate antardashas if not already done
                if not mahadasha.sub_periods:
                    mahadasha.sub_periods = self._generate_antardashas(mahadasha)
                
                for antardasha in mahadasha.sub_periods:
                    # Check if antardasha overlaps with our date range
                    if (antardasha.end_date >= start_date and antardasha.start_date <= end_date):
                        
                        # Ensure dates are within the requested range
                        period_start = max(antardasha.start_date, start_date)
                        period_end = min(antardasha.end_date, end_date)
                        
                        timeline.append({
                            'start_date': period_start,
                            'end_date': period_end,
                            'mahadasha': mahadasha.planet,
                            'antardasha': antardasha.planet,
                            'level': 'Antardasha',
                            'duration_days': (period_end - period_start).days
                        })
        
        return sorted(timeline, key=lambda x: x['start_date'])
    
    def _calculate_dasha_balance_at_birth(self, moon_longitude: float, nakshatra_lord: str) -> float:
        """Calculate remaining dasha balance at birth."""
        # Calculate how much of the nakshatra is completed
        nakshatra_span = 360.0 / 27  # 13.333... degrees per nakshatra
        nakshatra_position = (moon_longitude * 27 / 360) % 1  # Fractional part
        
        # Calculate remaining portion
        remaining_portion = 1.0 - nakshatra_position
        
        # Calculate remaining years
        total_dasha_years = self.vimshottari_periods[nakshatra_lord]
        remaining_years = total_dasha_years * remaining_portion
        
        return remaining_years
    
    def _generate_all_mahadashas(
        self,
        birth_date: datetime,
        starting_planet: str,
        initial_balance: float
    ) -> List[DashaPeriod]:
        """Generate all mahadashas from birth."""
        mahadashas = []
        current_date = birth_date
        
        # Find starting index in dasha sequence
        start_index = self.dasha_sequence.index(starting_planet)
        
        # First mahadasha (partial)
        first_duration_days = int(initial_balance * 365.25)
        first_end_date = current_date + timedelta(days=first_duration_days)
        
        first_mahadasha = DashaPeriod(
            planet=starting_planet,
            start_date=current_date,
            end_date=first_end_date,
            duration_years=initial_balance,
            duration_days=first_duration_days,
            level="Mahadasha"
        )
        mahadashas.append(first_mahadasha)
        current_date = first_end_date
        
        # Generate remaining mahadashas (120 years total cycle)
        total_years_generated = initial_balance
        
        for cycle in range(2):  # Generate enough for 2+ full cycles
            for i in range(1, len(self.dasha_sequence)):  # Skip first planet in subsequent cycles
                planet_index = (start_index + i) % len(self.dasha_sequence)
                planet = self.dasha_sequence[planet_index]
                duration_years = self.vimshottari_periods[planet]
                duration_days = int(duration_years * 365.25)
                
                end_date = current_date + timedelta(days=duration_days)
                
                mahadasha = DashaPeriod(
                    planet=planet,
                    start_date=current_date,
                    end_date=end_date,
                    duration_years=duration_years,
                    duration_days=duration_days,
                    level="Mahadasha"
                )
                mahadashas.append(mahadasha)
                
                current_date = end_date
                total_years_generated += duration_years
                
                # Stop after generating enough periods (150+ years)
                if total_years_generated > 150:
                    break
            
            if total_years_generated > 150:
                break
        
        return mahadashas
    
    def _generate_antardashas(self, mahadasha: DashaPeriod) -> List[DashaPeriod]:
        """Generate antardashas for a mahadasha."""
        antardashas = []
        
        # Find starting index for the mahadasha planet
        start_index = self.dasha_sequence.index(mahadasha.planet)
        
        current_date = mahadasha.start_date
        # Use actual span in days for proportional calculations (handles partial periods)
        mahadasha_total_days = max(
            1,
            mahadasha.duration_days if mahadasha.duration_days else (mahadasha.end_date - mahadasha.start_date).days
        )
        
        # Generate antardashas in sequence
        for i in range(len(self.dasha_sequence)):
            planet_index = (start_index + i) % len(self.dasha_sequence)
            planet = self.dasha_sequence[planet_index]
            
            # Calculate antardasha duration
            planet_years = self.vimshottari_periods[planet]
            # Antardasha duration is proportional to 120-year Vimshottari cycle
            antardasha_days = max(1, int(round((mahadasha_total_days * planet_years) / 120)))
            antardasha_years = antardasha_days / 365.25
            
            end_date = current_date + timedelta(days=antardasha_days)
            
            # Ensure we don't exceed mahadasha end date
            if end_date > mahadasha.end_date:
                end_date = mahadasha.end_date
                antardasha_days = (end_date - current_date).days
                antardasha_years = antardasha_days / 365.25

            if antardasha_days <= 0:
                break
            
            antardasha = DashaPeriod(
                planet=planet,
                start_date=current_date,
                end_date=end_date,
                duration_years=antardasha_years,
                duration_days=antardasha_days,
                level="Antardasha",
                parent_period=mahadasha
            )
            antardashas.append(antardasha)
            
            current_date = end_date
            
            # Stop if we've reached the end of mahadasha
            if current_date >= mahadasha.end_date:
                break
        
        return antardashas
    
    def _generate_pratyantardashas(self, antardasha: DashaPeriod) -> List[DashaPeriod]:
        """Generate pratyantardashas for an antardasha."""
        pratyantardashas = []
        
        # Find starting index for the antardasha planet
        start_index = self.dasha_sequence.index(antardasha.planet)
        
        current_date = antardasha.start_date
        antardasha_total_days = max(
            1,
            antardasha.duration_days if antardasha.duration_days else (antardasha.end_date - antardasha.start_date).days
        )
        
        # Generate pratyantardashas in sequence
        for i in range(len(self.dasha_sequence)):
            planet_index = (start_index + i) % len(self.dasha_sequence)
            planet = self.dasha_sequence[planet_index]
            
            # Calculate pratyantardasha duration
            planet_years = self.vimshottari_periods[planet]
            pratyantardasha_days = max(1, int(round((antardasha_total_days * planet_years) / 120)))
            pratyantardasha_years = pratyantardasha_days / 365.25
            
            end_date = current_date + timedelta(days=pratyantardasha_days)
            
            # Ensure we don't exceed antardasha end date
            if end_date > antardasha.end_date:
                end_date = antardasha.end_date
                pratyantardasha_days = (end_date - current_date).days
                pratyantardasha_years = pratyantardasha_days / 365.25

            if pratyantardasha_days <= 0:
                break
            
            pratyantardasha = DashaPeriod(
                planet=planet,
                start_date=current_date,
                end_date=end_date,
                duration_years=pratyantardasha_years,
                duration_days=pratyantardasha_days,
                level="Pratyantardasha",
                parent_period=antardasha
            )
            pratyantardashas.append(pratyantardasha)
            
            current_date = end_date
            
            # Stop if we've reached the end of antardasha
            if current_date >= antardasha.end_date:
                break
        
        return pratyantardashas

    def _generate_sookshmas(self, pratyantardasha: DashaPeriod) -> List[DashaPeriod]:
        """Generate sookshma dashas for a pratyantardasha."""
        sookshmas: List[DashaPeriod] = []

        start_index = self.dasha_sequence.index(pratyantardasha.planet)
        current_date = pratyantardasha.start_date
        pratyantardasha_total_days = max(
            1,
            pratyantardasha.duration_days if pratyantardasha.duration_days else (pratyantardasha.end_date - pratyantardasha.start_date).days
        )

        for i in range(len(self.dasha_sequence)):
            planet_index = (start_index + i) % len(self.dasha_sequence)
            planet = self.dasha_sequence[planet_index]

            planet_years = self.vimshottari_periods[planet]
            sookshma_days = max(1, int(round((pratyantardasha_total_days * planet_years) / 120)))
            sookshma_years = sookshma_days / 365.25

            end_date = current_date + timedelta(days=sookshma_days)
            if end_date > pratyantardasha.end_date:
                end_date = pratyantardasha.end_date
                sookshma_days = (end_date - current_date).days
                sookshma_years = sookshma_days / 365.25

            if sookshma_days <= 0:
                break

            sookshma = DashaPeriod(
                planet=planet,
                start_date=current_date,
                end_date=end_date,
                duration_years=sookshma_years,
                duration_days=sookshma_days,
                level="Sookshma",
                parent_period=pratyantardasha
            )
            sookshmas.append(sookshma)

            current_date = end_date
            if current_date >= pratyantardasha.end_date:
                break

        return sookshmas

    def _generate_pranas(self, sookshma: DashaPeriod) -> List[DashaPeriod]:
        """Generate prana dashas for a sookshma dasha."""
        pranas: List[DashaPeriod] = []

        start_index = self.dasha_sequence.index(sookshma.planet)
        current_date = sookshma.start_date
        sookshma_total_days = max(
            1,
            sookshma.duration_days if sookshma.duration_days else (sookshma.end_date - sookshma.start_date).days
        )

        for i in range(len(self.dasha_sequence)):
            planet_index = (start_index + i) % len(self.dasha_sequence)
            planet = self.dasha_sequence[planet_index]

            planet_years = self.vimshottari_periods[planet]
            prana_days = max(1, int(round((sookshma_total_days * planet_years) / 120)))
            prana_years = prana_days / 365.25

            end_date = current_date + timedelta(days=prana_days)
            if end_date > sookshma.end_date:
                end_date = sookshma.end_date
                prana_days = (end_date - current_date).days
                prana_years = prana_days / 365.25

            if prana_days <= 0:
                break

            prana = DashaPeriod(
                planet=planet,
                start_date=current_date,
                end_date=end_date,
                duration_years=prana_years,
                duration_days=prana_days,
                level="Prana",
                parent_period=sookshma
            )
            pranas.append(prana)

            current_date = end_date
            if current_date >= sookshma.end_date:
                break

        return pranas
    
    def _find_current_period(self, target_date: datetime, periods: List[DashaPeriod]) -> Optional[DashaPeriod]:
        """Find the period active at a specific date."""
        for period in periods:
            if period.start_date <= target_date <= period.end_date:
                return period
        return None
    
    def get_nakshatra_from_longitude(self, longitude: float) -> Tuple[int, str, str]:
        """
        Get nakshatra information from longitude.
        
        Args:
            longitude: Longitude in degrees
            
        Returns:
            Tuple of (nakshatra_index, nakshatra_name, nakshatra_lord)
        """
        nakshatra_index = int(longitude * 27 / 360) % 27
        nakshatra_name = self.nakshatra_names[nakshatra_index]
        nakshatra_lord = self.nakshatra_lords[nakshatra_index]
        
        return nakshatra_index, nakshatra_name, nakshatra_lord
    
    def format_dasha_period(self, period: DashaPeriod) -> str:
        """Format dasha period for display."""
        return (f"{period.planet.title()} {period.level} "
                f"({period.start_date.strftime('%Y-%m-%d')} to {period.end_date.strftime('%Y-%m-%d')}) "
                f"- {period.duration_years:.2f} years")
    
    def get_dasha_summary(self, dasha_analysis: DashaAnalysis) -> Dict[str, Any]:
        """Get summary of dasha analysis."""
        current_date = datetime.now()
        
        summary = {
            'birth_nakshatra': dasha_analysis.birth_nakshatra,
            'birth_nakshatra_lord': dasha_analysis.birth_nakshatra_lord.title(),
            'dasha_balance_at_birth': f"{dasha_analysis.dasha_balance_at_birth:.2f} years",
            'current_mahadasha': dasha_analysis.current_mahadasha.planet.title() if dasha_analysis.current_mahadasha else "Unknown",
            'current_antardasha': dasha_analysis.current_antardasha.planet.title() if dasha_analysis.current_antardasha else "Unknown",
            'current_pratyantardasha': dasha_analysis.current_pratyantardasha.planet.title() if dasha_analysis.current_pratyantardasha else "Unknown",
            'current_sookshma': dasha_analysis.current_sookshma.planet.title() if dasha_analysis.current_sookshma else "Unknown",
            'current_prana': dasha_analysis.current_prana.planet.title() if dasha_analysis.current_prana else "Unknown",
            'total_mahadashas': len(dasha_analysis.all_mahadashas)
        }
        
        # Add current period end dates
        if dasha_analysis.current_mahadasha:
            summary['current_mahadasha_ends'] = dasha_analysis.current_mahadasha.end_date.strftime('%Y-%m-%d')
        
        if dasha_analysis.current_antardasha:
            summary['current_antardasha_ends'] = dasha_analysis.current_antardasha.end_date.strftime('%Y-%m-%d')

        if dasha_analysis.current_pratyantardasha:
            summary['current_pratyantardasha_ends'] = dasha_analysis.current_pratyantardasha.end_date.strftime('%Y-%m-%d')

        if dasha_analysis.current_sookshma:
            summary['current_sookshma_ends'] = dasha_analysis.current_sookshma.end_date.strftime('%Y-%m-%d')

        if dasha_analysis.current_prana:
            summary['current_prana_ends'] = dasha_analysis.current_prana.end_date.strftime('%Y-%m-%d')

        return summary
