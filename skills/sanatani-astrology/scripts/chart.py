#!/usr/bin/env python3
"""
Chart calculation tools for Vedic astrology.

Provides:
- Divisional charts (D1, D9, D10, etc.)
- Vimshottari Dasha periods
- Yogas (beneficial combinations)
- Doshas (afflictions)
"""

import argparse
import json
import sys
from datetime import datetime

# Add parent to path for local development
sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from sanatani_astrology.astro_core.core.data_models import BirthDetails
from sanatani_astrology.astro_core.kundali_generator import get_default_generator
from sanatani_astrology.astro_core.kundali_generator.ephemeris_kundali_generator import EphemerisKundaliGenerator

# Initialize generator once
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        _generator = get_default_generator()
        if not isinstance(_generator, EphemerisKundaliGenerator):
            _generator = EphemerisKundaliGenerator()
    return _generator


def create_birth_details(
    year: int, month: int, day: int,
    hour: int, minute: int,
    latitude: float, longitude: float,
    timezone_offset: float, place_name: str = "Unknown"
) -> BirthDetails:
    """Create BirthDetails from parameters."""
    dt = datetime(year, month, day, hour, minute)
    return BirthDetails(
        date=dt,
        time=dt.time(),
        place=place_name,
        latitude=latitude,
        longitude=longitude,
        timezone_offset=timezone_offset
    )


def calculate_divisional_charts(
    year: int, month: int, day: int,
    hour: int, minute: int,
    latitude: float, longitude: float,
    timezone_offset: float,
    divisional_charts: str = "D1,D9",
    place_name: str = "Unknown",
    ayanamsa: str = "LAHIRI",
) -> dict:
    """
    Get specific divisional charts.

    Args:
        divisional_charts: Comma-separated chart names (e.g., "D1,D9,D10")
        Common: D1 (Rashi), D9 (Navamsa), D10 (Dasamsa), D7 (Saptamsa)

    Returns:
        Dict with chart data including planetary_positions for visualization.
    """
    generator = get_generator()
    details = create_birth_details(
        year, month, day, hour, minute, 
        latitude, longitude, timezone_offset, place_name
    )
    positions = generator._calculate_planetary_positions(details, ayanamsa=ayanamsa)

    lagna = positions.get('lagna')
    lagna_long = lagna.longitude if lagna else 0.0

    all_charts = generator._calculate_divisional_charts(
        positions, lagna_long, details, ayanamsa, house_system="BHAVA_CHALIT"
    )

    requested = [c.strip().upper() for c in divisional_charts.split(",")]
    result = {k: all_charts[k] for k in requested if k in all_charts}
    
    return result


def calculate_dasha_periods(
    year: int, month: int, day: int,
    hour: int, minute: int,
    latitude: float, longitude: float,
    timezone_offset: float,
    place_name: str = "Unknown",
) -> dict:
    """
    Get Vimshottari Dasha sequence and current period.

    Returns:
        Dict with dasha analysis including current mahadasha, antardasha, etc.
    """
    generator = get_generator()
    details = create_birth_details(
        year, month, day, hour, minute,
        latitude, longitude, timezone_offset, place_name
    )
    positions = generator._calculate_planetary_positions(details)
    moon = positions.get('moon')
    
    dasha = generator._calculate_dasha_periods(details, moon)
    return generator._serialize_dasha_analysis(dasha)


def get_yogas(
    year: int, month: int, day: int,
    hour: int, minute: int,
    latitude: float, longitude: float,
    timezone_offset: float,
    place_name: str = "Unknown",
) -> list:
    """
    Get Yoga analysis - beneficial planetary combinations.

    Returns:
        List of yogas like Raja Yoga, Dhana Yoga, Gaja Kesari Yoga, etc.
    """
    generator = get_generator()
    details = create_birth_details(
        year, month, day, hour, minute,
        latitude, longitude, timezone_offset, place_name
    )
    positions = generator._calculate_planetary_positions(details)
    lagna = positions.get('lagna')
    lagna_long = lagna.longitude if lagna else 0.0

    charts = generator._calculate_divisional_charts(
        positions, lagna_long, details, "LAHIRI", "BHAVA_CHALIT"
    )

    yogas, _ = generator._calculate_yogas_and_doshas(positions, charts, lagna_long)

    return [
        yoga.to_dict() if hasattr(yoga, 'to_dict') else 
        yoga.__dict__ if hasattr(yoga, '__dict__') else str(yoga)
        for yoga in yogas
    ]


def get_doshas(
    year: int, month: int, day: int,
    hour: int, minute: int,
    latitude: float, longitude: float,
    timezone_offset: float,
    place_name: str = "Unknown",
) -> list:
    """
    Get Dosha analysis - afflictions and challenging combinations.

    Returns:
        List of doshas like Manglik, Kaal Sarpa, Pitra Dosha, etc.
    """
    generator = get_generator()
    details = create_birth_details(
        year, month, day, hour, minute,
        latitude, longitude, timezone_offset, place_name
    )
    positions = generator._calculate_planetary_positions(details)
    lagna = positions.get('lagna')
    lagna_long = lagna.longitude if lagna else 0.0

    charts = generator._calculate_divisional_charts(
        positions, lagna_long, details, "LAHIRI", "BHAVA_CHALIT"
    )

    _, doshas = generator._calculate_yogas_and_doshas(positions, charts, lagna_long)

    return [
        dosha.to_dict() if hasattr(dosha, 'to_dict') else
        dosha.__dict__ if hasattr(dosha, '__dict__') else str(dosha)
        for dosha in doshas
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Vedic chart calculations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python chart.py charts --year 1990 --month 5 --day 15 --hour 10 --minute 30 --lat 28.6 --lon 77.2 --tz 5.5
  python chart.py dasha --year 1990 --month 5 --day 15 --hour 10 --minute 30 --lat 28.6 --lon 77.2 --tz 5.5
  python chart.py yogas --year 1990 --month 5 --day 15 --hour 10 --minute 30 --lat 28.6 --lon 77.2 --tz 5.5
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Common arguments
    def add_birth_args(p):
        p.add_argument("--year", type=int, required=True)
        p.add_argument("--month", type=int, required=True)
        p.add_argument("--day", type=int, required=True)
        p.add_argument("--hour", type=int, required=True)
        p.add_argument("--minute", type=int, required=True)
        p.add_argument("--lat", type=float, required=True, help="Latitude")
        p.add_argument("--lon", type=float, required=True, help="Longitude")
        p.add_argument("--tz", type=float, required=True, help="Timezone offset from UTC")
        p.add_argument("--place", default="Unknown", help="Place name")
    
    # Divisional charts
    charts_parser = subparsers.add_parser("charts", help="Get divisional charts")
    add_birth_args(charts_parser)
    charts_parser.add_argument("--divisions", default="D1,D9", help="Charts to calculate (e.g., D1,D9,D10)")
    
    # Dasha
    dasha_parser = subparsers.add_parser("dasha", help="Get Vimshottari Dasha periods")
    add_birth_args(dasha_parser)
    
    # Yogas
    yogas_parser = subparsers.add_parser("yogas", help="Get beneficial yogas")
    add_birth_args(yogas_parser)
    
    # Doshas
    doshas_parser = subparsers.add_parser("doshas", help="Get doshas/afflictions")
    add_birth_args(doshas_parser)
    
    args = parser.parse_args()
    
    try:
        if args.command == "charts":
            result = calculate_divisional_charts(
                args.year, args.month, args.day, args.hour, args.minute,
                args.lat, args.lon, args.tz, args.divisions, args.place
            )
        elif args.command == "dasha":
            result = calculate_dasha_periods(
                args.year, args.month, args.day, args.hour, args.minute,
                args.lat, args.lon, args.tz, args.place
            )
        elif args.command == "yogas":
            result = {"yogas": get_yogas(
                args.year, args.month, args.day, args.hour, args.minute,
                args.lat, args.lon, args.tz, args.place
            )}
        elif args.command == "doshas":
            result = {"doshas": get_doshas(
                args.year, args.month, args.day, args.hour, args.minute,
                args.lat, args.lon, args.tz, args.place
            )}
        
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
