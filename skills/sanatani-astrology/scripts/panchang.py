#!/usr/bin/env python3
"""
Panchang calculation tool for Vedic calendar.

Provides daily panchang including:
- Tithi (lunar day)
- Nakshatra (lunar mansion)
- Yoga (sun-moon combination)
- Karana (half-tithi)
- Sun/moon times
- Auspicious/inauspicious periods
"""

import argparse
import json
import sys
from datetime import date, datetime

# Add parent to path for local development
sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from sanatani_astrology.astro_core.panchang import PanchangCalculator

# Lazy-loaded calculator
_calculator = None


def get_calculator():
    global _calculator
    if _calculator is None:
        _calculator = PanchangCalculator()
    return _calculator


# Sarvartha Siddhi Yoga: nakshatra index (0-26) -> allowed weekdays (0=Mon, 6=Sun)
SARVARTHA_SIDDHI_YOGA = {
    0: [2], 1: [5], 2: [6], 3: [0, 2, 4], 4: [1, 5], 5: [2, 5],
    6: [3, 4], 7: [5], 8: [2], 9: [6], 10: [2, 4], 11: [6, 0],
    12: [2], 13: [3], 14: [1, 4, 5], 15: [3, 4], 16: [5, 2],
    17: [1, 2], 18: [1], 19: [2, 4], 20: [6], 21: [2, 4],
    22: [5], 23: [5], 24: [3], 25: [2, 6], 26: [2, 3],
}

AMRIT_SIDDHI_YOGA = {
    6: [3], 7: [6], 12: [0], 16: [5], 21: [2], 26: [4],
}


def _calculate_special_yogas(nakshatra_index: int, weekday: int) -> dict:
    """Calculate special yogas based on nakshatra and weekday."""
    return {
        "sarvartha_siddhi": weekday in SARVARTHA_SIDDHI_YOGA.get(nakshatra_index, []),
        "amrit_siddhi": weekday in AMRIT_SIDDHI_YOGA.get(nakshatra_index, []),
        "guru_pushya": nakshatra_index == 7 and weekday == 3,
        "ravi_pushya": nakshatra_index == 7 and weekday == 6,
    }


def get_panchang(
    target_date: date,
    latitude: float,
    longitude: float,
    timezone_offset: float = 5.5,
) -> dict:
    """
    Get panchang for a specific date and location.

    Args:
        target_date: Date to calculate panchang for
        latitude: Location latitude
        longitude: Location longitude
        timezone_offset: Timezone offset from UTC

    Returns:
        Dict with complete panchang data.
    """
    calculator = get_calculator()
    
    # Calculate global panchang
    # Calculate global panchang
    panchang = calculator.calculate_global(
        date=target_date,
        latitude=latitude,
        longitude=longitude,
        timezone_offset=timezone_offset,
    )
    
    # Convert to dict
    result = {
        "date": str(target_date),
        "weekday": target_date.strftime("%A"),
        "latitude": latitude,
        "longitude": longitude,
        "timezone_offset": timezone_offset,
    }
    
    # Add panchang elements
    if hasattr(panchang, 'to_dict'):
        result.update(panchang.to_dict())
    elif hasattr(panchang, '__dict__'):
        for k, v in panchang.__dict__.items():
            if not k.startswith('_'):
                if hasattr(v, 'to_dict'):
                    result[k] = v.to_dict()
                elif hasattr(v, '__dict__'):
                    result[k] = {k2: v2 for k2, v2 in v.__dict__.items() if not k2.startswith('_')}
                else:
                    result[k] = v
    
    # Add special yogas if nakshatra available
    nakshatra_index = result.get("nakshatra", {}).get("index")
    if nakshatra_index is not None:
        weekday = target_date.weekday()
        result["special_yogas"] = _calculate_special_yogas(nakshatra_index, weekday)
    
    return result


def get_panchang_range(
    start_date: date,
    days: int,
    latitude: float,
    longitude: float,
    timezone_offset: float = 5.5,
) -> list:
    """Get panchang for a range of dates."""
    from datetime import timedelta
    
    results = []
    for i in range(days):
        target = start_date + timedelta(days=i)
        try:
            panchang = get_panchang(target, latitude, longitude, timezone_offset)
            results.append(panchang)
        except Exception as e:
            results.append({"date": str(target), "error": str(e)})
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Calculate Vedic panchang",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python panchang.py --date 2024-01-15 --lat 28.6 --lon 77.2 --tz 5.5
  python panchang.py --days 7 --lat 28.6 --lon 77.2
        """
    )
    
    parser.add_argument("--date", "-d", help="Date (YYYY-MM-DD), default: today")
    parser.add_argument("--days", type=int, default=1, help="Number of days (for range)")
    parser.add_argument("--lat", type=float, required=True, help="Latitude")
    parser.add_argument("--lon", type=float, required=True, help="Longitude")
    parser.add_argument("--tz", type=float, default=5.5, help="Timezone offset (default: 5.5)")
    
    args = parser.parse_args()
    
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today()
    
    try:
        if args.days > 1:
            result = get_panchang_range(target_date, args.days, args.lat, args.lon, args.tz)
        else:
            result = get_panchang(target_date, args.lat, args.lon, args.tz)
        
        print(json.dumps(result, indent=2, default=str))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
