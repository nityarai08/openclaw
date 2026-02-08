#!/usr/bin/env python3
"""
Matchmaking tool for Vedic compatibility analysis.

Calculates Ashta-Koota (8 factors) compatibility between two people:
- Varna (spiritual compatibility)
- Vashya (mutual attraction)
- Tara (birth star harmony)
- Yoni (instinctive chemistry)
- Graha Maitri (planetary friendship)
- Gana (temperament match)
- Bhakoot (moon sign relationship)
- Nadi (health and genetics)
"""

import argparse
import json
import sys
from datetime import datetime

# Add parent to path for local development
sys.path.insert(0, str(__file__).rsplit("/scripts", 1)[0])

from sanatani_astrology.astro_core.core.data_models import BirthDetails
from sanatani_astrology.astro_core.kundali_generator import get_default_generator

# Initialize generator
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        _generator = get_default_generator()
    return _generator


# Nakshatra data for compatibility calculations
NAKSHATRA_DATA = [
    ("Ashwini", "deva", "adi", "horse"),
    ("Bharani", "manushya", "madhya", "elephant"),
    ("Krittika", "rakshasa", "antya", "goat"),
    ("Rohini", "manushya", "antya", "serpent"),
    ("Mrigashira", "deva", "madhya", "serpent"),
    ("Ardra", "manushya", "adi", "dog"),
    ("Punarvasu", "deva", "adi", "cat"),
    ("Pushya", "deva", "madhya", "goat"),
    ("Ashlesha", "rakshasa", "antya", "cat"),
    ("Magha", "rakshasa", "antya", "rat"),
    ("Purva Phalguni", "manushya", "madhya", "rat"),
    ("Uttara Phalguni", "manushya", "adi", "cow"),
    ("Hasta", "deva", "adi", "buffalo"),
    ("Chitra", "rakshasa", "madhya", "tiger"),
    ("Swati", "deva", "antya", "buffalo"),
    ("Vishakha", "rakshasa", "antya", "tiger"),
    ("Anuradha", "deva", "madhya", "deer"),
    ("Jyeshtha", "rakshasa", "adi", "deer"),
    ("Mula", "rakshasa", "adi", "dog"),
    ("Purva Ashadha", "manushya", "madhya", "monkey"),
    ("Uttara Ashadha", "manushya", "antya", "mongoose"),
    ("Shravana", "deva", "antya", "monkey"),
    ("Dhanishtha", "rakshasa", "madhya", "lion"),
    ("Shatabhisha", "rakshasa", "adi", "horse"),
    ("Purva Bhadrapada", "manushya", "adi", "lion"),
    ("Uttara Bhadrapada", "manushya", "madhya", "cow"),
    ("Revati", "deva", "antya", "elephant"),
]

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

SIGN_LORDS = {
    0: "mars", 1: "venus", 2: "mercury", 3: "moon", 4: "sun", 5: "mercury",
    6: "venus", 7: "mars", 8: "jupiter", 9: "saturn", 10: "saturn", 11: "jupiter",
}

SIGN_VARNA = {
    0: "kshatriya", 1: "vaishya", 2: "shudra", 3: "brahmin",
    4: "kshatriya", 5: "vaishya", 6: "shudra", 7: "brahmin",
    8: "kshatriya", 9: "vaishya", 10: "shudra", 11: "brahmin",
}

VARNA_RANK = {"shudra": 0, "vaishya": 1, "kshatriya": 2, "brahmin": 3}

GANA_POINTS = {
    ("deva", "deva"): 6, ("deva", "manushya"): 5, ("deva", "rakshasa"): 1,
    ("manushya", "deva"): 5, ("manushya", "manushya"): 6, ("manushya", "rakshasa"): 0,
    ("rakshasa", "deva"): 1, ("rakshasa", "manushya"): 0, ("rakshasa", "rakshasa"): 6,
}


def _create_birth_details(
    year: int, month: int, day: int,
    hour: int, minute: int,
    latitude: float, longitude: float,
    timezone_offset: float, place_name: str = "Unknown"
) -> BirthDetails:
    dt = datetime(year, month, day, hour, minute)
    return BirthDetails(
        date=dt,
        time=dt.time(),
        place=place_name,
        latitude=latitude,
        longitude=longitude,
        timezone_offset=timezone_offset
    )


def _extract_moon_data(kundali_dict: dict) -> tuple[int, int] | None:
    """Extract moon sign index and nakshatra index from kundali."""
    charts = kundali_dict.get("divisional_charts", {})
    d1 = charts.get("D1") or charts.get("d1")
    if not d1:
        return None

    planets = d1.get("planetary_positions", {})
    moon = planets.get("moon", {})
    if not moon:
        return None

    moon_sign_index = moon.get("rasi")
    nakshatra_index = moon.get("nakshatra")

    if moon_sign_index is None or nakshatra_index is None:
        return None

    return int(moon_sign_index), int(nakshatra_index)


def _score_varna(g_sign: int, b_sign: int) -> dict:
    g_varna = SIGN_VARNA[g_sign]
    b_varna = SIGN_VARNA[b_sign]
    score = 1.0 if VARNA_RANK[g_varna] >= VARNA_RANK[b_varna] else 0.0
    return {"name": "Varna", "max_points": 1.0, "obtained_points": score}


def _score_tara(g_nak: int, b_nak: int) -> dict:
    def tara_score(from_idx: int, to_idx: int) -> float:
        steps = (to_idx - from_idx) % 27
        tara_num = steps % 9 or 9
        return 0.0 if tara_num in {3, 5, 7} else 1.5
    score = tara_score(g_nak, b_nak) + tara_score(b_nak, g_nak)
    return {"name": "Tara", "max_points": 3.0, "obtained_points": score}


def _score_yoni(g_yoni: str, b_yoni: str) -> dict:
    score = 4.0 if g_yoni == b_yoni else 2.0
    return {"name": "Yoni", "max_points": 4.0, "obtained_points": score}


def _score_gana(g_gana: str, b_gana: str) -> dict:
    score = float(GANA_POINTS.get((g_gana, b_gana), 3))
    return {"name": "Gana", "max_points": 6.0, "obtained_points": score}


def _score_bhakoot(g_sign: int, b_sign: int) -> dict:
    diff = (b_sign - g_sign) % 12
    inauspicious = {(1, 11), (11, 1), (4, 8), (8, 4), (5, 7), (7, 5)}
    forward_back = (diff, (12 - diff) % 12)
    if forward_back in inauspicious or forward_back[::-1] in inauspicious:
        return {"name": "Bhakoot", "max_points": 7.0, "obtained_points": 0.0, "dosha": True}
    return {"name": "Bhakoot", "max_points": 7.0, "obtained_points": 7.0}


def _score_nadi(g_nadi: str, b_nadi: str) -> dict:
    if g_nadi == b_nadi:
        return {"name": "Nadi", "max_points": 8.0, "obtained_points": 0.0, "dosha": True}
    return {"name": "Nadi", "max_points": 8.0, "obtained_points": 8.0}


def calculate_compatibility(
    person_a: dict,
    person_b: dict,
) -> dict:
    """
    Calculate Ashta-Koota compatibility.

    Args:
        person_a: Dict with year, month, day, hour, minute, lat, lon, tz
        person_b: Dict with year, month, day, hour, minute, lat, lon, tz

    Returns:
        Dict with total_points (out of 36), percentage, and koota breakdown.
    """
    generator = get_generator()
    
    # Generate kundalis
    details_a = _create_birth_details(
        person_a["year"], person_a["month"], person_a["day"],
        person_a["hour"], person_a["minute"],
        person_a["lat"], person_a["lon"], person_a["tz"],
        person_a.get("name", "Person A")
    )
    details_b = _create_birth_details(
        person_b["year"], person_b["month"], person_b["day"],
        person_b["hour"], person_b["minute"],
        person_b["lat"], person_b["lon"], person_b["tz"],
        person_b.get("name", "Person B")
    )
    
    kundali_a = generator.generate_from_birth_details(details_a)
    kundali_b = generator.generate_from_birth_details(details_b)
    
    dict_a = json.loads(kundali_a.to_json())
    dict_b = json.loads(kundali_b.to_json())
    
    moon_a = _extract_moon_data(dict_a)
    moon_b = _extract_moon_data(dict_b)
    
    if not moon_a or not moon_b:
        return {"success": False, "error": "Could not extract moon data"}
    
    a_sign, a_nak = moon_a
    b_sign, b_nak = moon_b
    
    a_nak_data = NAKSHATRA_DATA[a_nak]
    b_nak_data = NAKSHATRA_DATA[b_nak]
    
    # Calculate all 8 kootas
    koota_scores = [
        _score_varna(a_sign, b_sign),
        {"name": "Vashya", "max_points": 2.0, "obtained_points": 1.5},  # Simplified
        _score_tara(a_nak, b_nak),
        _score_yoni(a_nak_data[3], b_nak_data[3]),
        {"name": "Graha Maitri", "max_points": 5.0, "obtained_points": 3.0},  # Simplified
        _score_gana(a_nak_data[1], b_nak_data[1]),
        _score_bhakoot(a_sign, b_sign),
        _score_nadi(a_nak_data[2], b_nak_data[2]),
    ]
    
    total = sum(s["obtained_points"] for s in koota_scores)
    percentage = (total / 36.0) * 100
    
    band = "Excellent" if percentage >= 75 else "Good" if percentage >= 60 else "Average" if percentage >= 45 else "Below Average"
    
    return {
        "success": True,
        "total_points": round(total, 2),
        "max_points": 36.0,
        "percentage": round(percentage, 1),
        "band": band,
        "koota_scores": koota_scores,
        "partners": {
            "person_a": {"moon_sign": SIGN_NAMES[a_sign], "nakshatra": a_nak_data[0]},
            "person_b": {"moon_sign": SIGN_NAMES[b_sign], "nakshatra": b_nak_data[0]},
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Calculate Ashta-Koota compatibility")
    parser.add_argument("--json", required=True, help="JSON file with person_a and person_b data")
    
    args = parser.parse_args()
    
    try:
        with open(args.json) as f:
            data = json.load(f)
        
        result = calculate_compatibility(data["person_a"], data["person_b"])
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
