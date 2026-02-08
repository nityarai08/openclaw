#!/usr/bin/env python3
import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import time

# Configuration
OPENCLAW_CMD = ["openclaw", "agent", "--agent", "main", "--json", "--message"]
GOLDEN_FILE = "tests/golden_data.json"
CHART_DIVISIONS = "D1,D2,D3,D4,D7,D9,D10,D12,D16"


class TestCase:
    def __init__(self, name, prompt, golden_key=None, expected_keywords=None):
        self.name = name
        self.prompt = prompt
        self.golden_key = golden_key
        self.expected_keywords = expected_keywords or []
        self.status = "PENDING"
        self.output = ""
        self.error = ""
        self.duration = 0
        self.diff = []
        self.actual_json = None
        self.mode_used = ""


TEST_CASES = [
    TestCase(
        "Panchang",
        "Calculate Panchang for August 15, 1947 in Mumbai. Return a raw JSON object with keys \"tithi_name\" and \"nakshatra_name\". Do not add commentary.",
        golden_key="Panchang",
    ),
    TestCase(
        "Panchang_Details",
        "Calculate Panchang for August 15, 1947 in Mumbai. Return a raw JSON object with keys \"yoga_name\" and \"karana_name\". Use only that date and location. Do not add commentary.",
        golden_key="Panchang_Details",
    ),
    TestCase(
        "Panchang_MonthPaksha",
        "Calculate Panchang for August 15, 1947 in Mumbai. Return a raw JSON object with keys \"lunar_month\" and \"paksha\". Use only that date and location. Do not add commentary.",
        golden_key="Panchang_MonthPaksha",
    ),
    TestCase(
        "Geocoding",
        "What are coordinates for Ayodhya? Return a raw JSON object with keys \"latitude\" and \"longitude\".",
        golden_key="Geocoding",
    ),
    TestCase(
        "Geocoding_Metadata",
        "What are coordinates for Ayodhya? Return a raw JSON object with keys \"timezone_offset\" and \"country\". Do not add commentary.",
        golden_key="Geocoding_Metadata",
    ),
    TestCase(
        "Chart_D1",
        "What is the D1 Lagna Rasi Index (0-11) for User (1990-01-01 12:00 Delhi)? Return raw JSON with key \"d1_lagna_rasi\".",
        golden_key="Chart_D1",
    ),
    TestCase(
        "Chart_D2",
        "What is the D2 Lagna Rasi Index (0-11) for User (1990-01-01 12:00 Delhi)? Return raw JSON with key \"d2_lagna_rasi\".",
        golden_key="Chart_D2",
    ),
    TestCase(
        "Chart_D3",
        "What is the D3 Lagna Rasi Index (0-11) for User (1990-01-01 12:00 Delhi)? Return raw JSON with key \"d3_lagna_rasi\".",
        golden_key="Chart_D3",
    ),
    TestCase(
        "Chart_D4",
        "What is the D4 Lagna Rasi Index (0-11) for User (1990-01-01 12:00 Delhi)? Return raw JSON with key \"d4_lagna_rasi\".",
        golden_key="Chart_D4",
    ),
    TestCase(
        "Chart_D7",
        "What is the D7 Lagna Rasi Index (0-11) for User (1990-01-01 12:00 Delhi)? Return raw JSON with key \"d7_lagna_rasi\".",
        golden_key="Chart_D7",
    ),
    TestCase(
        "Chart_D9",
        "What is the D9 Lagna Rasi Index (0-11) for User (1990-01-01 12:00 Delhi)? Return raw JSON with key \"d9_lagna_rasi\".",
        golden_key="Chart_D9",
    ),
    TestCase(
        "Chart_D10",
        "What is the D10 Lagna Rasi Index (0-11) for User (1990-01-01 12:00 Delhi)? Return raw JSON with key \"d10_lagna_rasi\".",
        golden_key="Chart_D10",
    ),
    TestCase(
        "Chart_D12",
        "What is the D12 Lagna Rasi Index (0-11) for User (1990-01-01 12:00 Delhi)? Return raw JSON with key \"d12_lagna_rasi\".",
        golden_key="Chart_D12",
    ),
    TestCase(
        "Chart_D16",
        "What is the D16 Lagna Rasi Index (0-11) for User (1990-01-01 12:00 Delhi)? Return raw JSON with key \"d16_lagna_rasi\".",
        golden_key="Chart_D16",
    ),
    TestCase(
        "MoonRasi_D1",
        "For User (1990-01-01 12:00 Delhi), what is the Moon Rasi Index (0-11) in D1 chart? Return raw JSON with key \"d1_moon_rasi\" only.",
        golden_key="MoonRasi_D1",
    ),
    TestCase(
        "MoonRasi_D9",
        "For User (1990-01-01 12:00 Delhi), what is the Moon Rasi Index (0-11) in D9 chart? Return raw JSON with key \"d9_moon_rasi\" only.",
        golden_key="MoonRasi_D9",
    ),
    TestCase(
        "Dasha_BirthProfile",
        "For User (1990-01-01 12:00 Delhi IST), compute Vimshottari dasha and read ONLY the birth profile fields from vimshottari: birth_nakshatra, birth_nakshatra_name, birth_nakshatra_lord. Return ONLY raw JSON with exactly those three keys. Do not return any key containing \"mahadasha\" or \"antardasha\".",
        golden_key="Dasha_BirthProfile",
    ),
    TestCase(
        "Dasha_MahadashaSequence",
        "For User (1990-01-01 12:00 Delhi IST), compute Vimshottari dasha and use vimshottari.mahadasha_sequence to return ONLY the first four mahadasha planet names. Return ONLY raw JSON with keys \"first_mahadasha\", \"second_mahadasha\", \"third_mahadasha\", and \"fourth_mahadasha\". Do not return antardasha keys.",
        golden_key="Dasha_MahadashaSequence",
    ),
    TestCase(
        "Dasha_AntardashaDetection",
        "For User (1990-01-01 12:00 Delhi), compute Vimshottari dasha and return a raw JSON object with keys \"saturn_mahadasha_first_antardasha\", \"saturn_mahadasha_second_antardasha\", and \"saturn_mahadasha_first_pratyantardasha\" only.",
        golden_key="Dasha_AntardashaDetection",
    ),
    TestCase(
        "Dasha_MahadashaDurations",
        "For User (1990-01-01 12:00 Delhi IST), from the major-period timeline return the duration in years of the 2nd and 4th major periods. Return ONLY raw JSON with keys \"second_mahadasha_duration_years\" and \"fourth_mahadasha_duration_years\".",
        golden_key="Dasha_MahadashaDurations",
    ),
    TestCase(
        "Dasha_SaturnAntardashaOrder",
        "For User (1990-01-01 12:00 Delhi IST), inside Saturn major period return the 3rd and 7th sub-period planet names. Return ONLY raw JSON with keys \"saturn_third_antardasha\" and \"saturn_seventh_antardasha\".",
        golden_key="Dasha_SaturnAntardashaOrder",
    ),
    TestCase(
        "Matchmaking",
        "Check compatibility between Person A (1990-01-01 12:00 Delhi) and Person B (1992-02-02 14:00 Mumbai). Return a raw JSON object with key \"total_points\".",
        golden_key="Matchmaking",
    ),
    TestCase(
        "Matchmaking_Dosha",
        "Check compatibility between Person A (1990-01-01 12:00 Delhi) and Person B (1992-02-02 14:00 Mumbai). Return a raw JSON object with keys \"nadi_points\" and \"bhakoot_dosha\" only.",
        golden_key="Matchmaking_Dosha",
    ),
    TestCase(
        "Matchmaking_MoonSigns",
        "Check compatibility between Person A (1990-01-01 12:00 Delhi) and Person B (1992-02-02 14:00 Mumbai). Return a raw JSON object with keys \"person_a_moon_sign\" and \"person_b_moon_sign\" only.",
        golden_key="Matchmaking_MoonSigns",
    ),
    TestCase(
        "Yoga_Detection",
        "For User (1978-03-05 14:20 Chennai), detect yogas and return a raw JSON object with keys \"yoga_count\" and \"primary_yoga_name\" only.",
        golden_key="Yoga_Detection",
    ),
    TestCase(
        "Dosha_Detection",
        "For User (1978-03-05 14:20 Chennai), detect doshas and return a raw JSON object with keys \"dosha_count\", \"primary_dosha_name\", and \"primary_dosha_severity\" only.",
        golden_key="Dosha_Detection",
    ),
    TestCase(
        "Yoga_Profile",
        "For User (1978-03-05 14:20 Chennai), from detected yogas return the first yoga's type and strength. Return ONLY raw JSON with keys \"primary_yoga_type\" and \"primary_yoga_strength\".",
        golden_key="Yoga_Profile",
    ),
    TestCase(
        "Dosha_Profile",
        "For User (1978-03-05 14:20 Chennai), from detected doshas return the first dosha's type and the first house number from houses_involved. Return ONLY raw JSON with keys \"primary_dosha_type\" and \"primary_dosha_first_house\".",
        golden_key="Dosha_Profile",
    ),
    TestCase(
        "Implicit_Multi_2Tool",
        "For Ayodhya on 1947-08-15, what are the latitude, longitude, tithi name, and nakshatra name? Return ONLY a raw JSON object with keys \"latitude\", \"longitude\", \"tithi_name\", and \"nakshatra_name\".",
        golden_key="Implicit_Multi_2Tool",
    ),
    TestCase(
        "Implicit_Multi_3Tool",
        "For a person born in Delhi on 1990-01-01 at 12:00 IST, return Delhi latitude/longitude, D1 lagna rasi index, and birth nakshatra name from the Vimshottari birth profile. Return ONLY raw JSON with keys \"delhi_latitude\", \"delhi_longitude\", \"d1_lagna_rasi\", and \"birth_nakshatra_name\".",
        golden_key="Implicit_Multi_3Tool",
    ),
    TestCase(
        "Implicit_Multi_4Tool",
        "For Ayodhya on 1947-08-15 and for compatibility of Person A (1990-01-01 12:00 Delhi) with Person B (1992-02-02 14:00 Mumbai), return ONLY raw JSON with keys \"ayodhya_tithi_name\", \"delhi_d1_lagna_rasi\", \"compatibility_total_points\", and \"mumbai_longitude\".",
        golden_key="Implicit_Multi_4Tool",
    ),
    TestCase(
        "Implicit_Multi_5Tool",
        "For Ayodhya on 1947-08-15 and compatibility of Person A (1990-01-01 12:00 Delhi) with Person B (1992-02-02 14:00 Mumbai), return ONLY raw JSON with Ayodhya nakshatra name, Person A Delhi D1 lagna rasi index, Person A birth nakshatra lord, total compatibility points, and Mumbai longitude. Use keys \"ayodhya_nakshatra_name\", \"delhi_d1_lagna_rasi\", \"delhi_birth_nakshatra_lord\", \"compatibility_total_points\", and \"mumbai_longitude\".",
        golden_key="Implicit_Multi_5Tool",
    ),
]

_chart_cache = None
_panchang_cache = None
_geocoding_cache = None
_geocoding_place_cache = {}
_dasha_cache = None
_matchmaking_cache = None
_yogas_cache = None
_doshas_cache = None
_panchang_dynamic_cache = {}


def load_golden_data():
    if not os.path.exists(GOLDEN_FILE):
        print(f"Golden file {GOLDEN_FILE} not found. Run generate_golden_data.py first.")
        sys.exit(1)
    with open(GOLDEN_FILE, encoding="utf-8") as f:
        return json.load(f)


def extract_json_from_text(text):
    # Try to find markdown code blocks first.
    pattern = r"```(?:json)?\s*(\{.*\}|\[.*\])\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    if matches:
        try:
            return json.loads(matches[-1])
        except Exception:
            pass

    try:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
    except Exception:
        pass

    return None


def parse_json_mixed_output(raw_output):
    stripped = raw_output.strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    lines = raw_output.splitlines()
    for idx, line in enumerate(lines):
        lead = line.strip()
        if lead.startswith("{") or lead.startswith("["):
            candidate = "\n".join(lines[idx:])
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                continue

    obj_start = raw_output.find("{")
    arr_start = raw_output.find("[")
    starts = [i for i in (obj_start, arr_start) if i != -1]
    if starts:
        start_idx = min(starts)
        return json.loads(raw_output[start_idx:])

    raise json.JSONDecodeError("No JSON object found in output", raw_output, 0)


def extract_agent_text(payload):
    payloads = []
    if isinstance(payload, dict):
        if isinstance(payload.get("result"), dict):
            payloads = payload["result"].get("payloads") or []
        elif isinstance(payload.get("payloads"), list):
            payloads = payload.get("payloads") or []

    text_chunks = []
    for item in payloads:
        if isinstance(item, dict) and isinstance(item.get("text"), str):
            text_chunks.append(item["text"])
    return "\n".join(text_chunks).strip()


def is_quota_error(text):
    lowered = text.lower()
    return "cloud code assist api error (429)" in lowered or (
        "quota" in lowered and "reset" in lowered
    )


def compare_values(actual, expected, path=""):
    diffs = []

    if isinstance(actual, dict) and isinstance(expected, dict):
        for key, value in expected.items():
            child_path = f"{path}.{key}" if path else key
            if key not in actual:
                diffs.append(f"Missing key: {child_path}")
            else:
                diffs.extend(compare_values(actual[key], value, child_path))
    elif isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            diffs.append(
                f"List length mismatch at {path}: actual {len(actual)} vs expected {len(expected)}"
            )
        else:
            for idx, (a_item, e_item) in enumerate(zip(actual, expected)):
                diffs.extend(compare_values(a_item, e_item, f"{path}[{idx}]"))
    elif isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        try:
            if abs(float(actual) - float(expected)) > 0.1:
                diffs.append(
                    f"Value mismatch at {path}: actual {actual} != expected {expected}"
                )
        except Exception:
            diffs.append(
                f"Type mismatch at {path}: actual {type(actual)} vs expected {type(expected)}"
            )
    elif str(actual) != str(expected):
        if "time" not in path.lower() and "date" not in path.lower():
            diffs.append(
                f"Value mismatch at {path}: actual '{actual}' != expected '{expected}'"
            )

    return diffs


def run_json_command(cmd, verbose=False, timeout=120):
    if verbose:
        print(f"    Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        err_text = (result.stderr or result.stdout).strip()
        raise RuntimeError(f"Exit code {result.returncode}: {err_text}")
    return parse_json_mixed_output(result.stdout)


def get_chart_data(verbose=False):
    global _chart_cache
    if _chart_cache is None:
        _chart_cache = run_json_command(
            [
                "python3",
                "scripts/chart.py",
                "charts",
                "--year",
                "1990",
                "--month",
                "1",
                "--day",
                "1",
                "--hour",
                "12",
                "--minute",
                "0",
                "--lat",
                "28.61",
                "--lon",
                "77.20",
                "--tz",
                "5.5",
                "--divisions",
                CHART_DIVISIONS,
            ],
            verbose=verbose,
            timeout=180,
        )
    return _chart_cache


def get_panchang_data(verbose=False):
    global _panchang_cache
    if _panchang_cache is None:
        _panchang_cache = run_json_command(
            [
                "python3",
                "scripts/panchang.py",
                "--date",
                "1947-08-15",
                "--lat",
                "19.076",
                "--lon",
                "72.8777",
                "--tz",
                "5.5",
            ],
            verbose=verbose,
        )
    return _panchang_cache


def get_geocoding_data(verbose=False):
    global _geocoding_cache
    if _geocoding_cache is None:
        _geocoding_cache = get_geocoding_for_place("Ayodhya", verbose=verbose)
    return _geocoding_cache


def get_geocoding_for_place(place, verbose=False):
    global _geocoding_place_cache
    key = place.strip().lower()
    if key not in _geocoding_place_cache:
        _geocoding_place_cache[key] = run_json_command(
            ["python3", "scripts/geocoding.py", "--place", place, "--json"],
            verbose=verbose,
        )
    return _geocoding_place_cache[key]


def get_panchang_for_location(target_date, latitude, longitude, timezone_offset, verbose=False):
    global _panchang_dynamic_cache
    cache_key = (
        target_date,
        round(float(latitude), 6),
        round(float(longitude), 6),
        round(float(timezone_offset), 3),
    )
    if cache_key not in _panchang_dynamic_cache:
        _panchang_dynamic_cache[cache_key] = run_json_command(
            [
                "python3",
                "scripts/panchang.py",
                "--date",
                target_date,
                "--lat",
                str(latitude),
                "--lon",
                str(longitude),
                "--tz",
                str(timezone_offset),
            ],
            verbose=verbose,
        )
    return _panchang_dynamic_cache[cache_key]


def get_d1_chart_for_location(latitude, longitude, timezone_offset, verbose=False):
    chart = run_json_command(
        [
            "python3",
            "scripts/chart.py",
            "charts",
            "--year",
            "1990",
            "--month",
            "1",
            "--day",
            "1",
            "--hour",
            "12",
            "--minute",
            "0",
            "--lat",
            str(latitude),
            "--lon",
            str(longitude),
            "--tz",
            str(timezone_offset),
            "--divisions",
            "D1",
        ],
        verbose=verbose,
        timeout=180,
    )
    return chart["D1"]


def get_dasha_for_location(latitude, longitude, timezone_offset, verbose=False):
    return run_json_command(
        [
            "python3",
            "scripts/chart.py",
            "dasha",
            "--year",
            "1990",
            "--month",
            "1",
            "--day",
            "1",
            "--hour",
            "12",
            "--minute",
            "0",
            "--lat",
            str(latitude),
            "--lon",
            str(longitude),
            "--tz",
            str(timezone_offset),
        ],
        verbose=verbose,
        timeout=240,
    )


def get_matchmaking_for_locations(
    a_lat, a_lon, a_tz, b_lat, b_lon, b_tz, verbose=False
):
    mm_input = build_matchmaking_input(a_lat, a_lon, a_tz, b_lat, b_lon, b_tz)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tf:
        json.dump(mm_input, tf)
        tmp_path = tf.name
    try:
        return run_json_command(
            ["python3", "scripts/matchmaking.py", "--json", tmp_path], verbose=verbose
        )
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def get_dasha_data(verbose=False):
    global _dasha_cache
    if _dasha_cache is None:
        _dasha_cache = run_json_command(
            [
                "python3",
                "scripts/chart.py",
                "dasha",
                "--year",
                "1990",
                "--month",
                "1",
                "--day",
                "1",
                "--hour",
                "12",
                "--minute",
                "0",
                "--lat",
                "28.61",
                "--lon",
                "77.20",
                "--tz",
                "5.5",
            ],
            verbose=verbose,
            timeout=240,
        )
    return _dasha_cache


def build_matchmaking_input(a_lat, a_lon, a_tz, b_lat, b_lon, b_tz):
    return {
        "person_a": {
            "year": 1990,
            "month": 1,
            "day": 1,
            "hour": 12,
            "minute": 0,
            "lat": a_lat,
            "lon": a_lon,
            "tz": a_tz,
        },
        "person_b": {
            "year": 1992,
            "month": 2,
            "day": 2,
            "hour": 14,
            "minute": 0,
            "lat": b_lat,
            "lon": b_lon,
            "tz": b_tz,
        },
    }


def get_primary_rule_entry(entries):
    return normalize_rule_entry(entries[0]) if entries else {}


def get_saturn_mahadasha(sequence):
    return next(item for item in sequence if item["planet"] == "Saturn")


def get_matchmaking_data(verbose=False):
    global _matchmaking_cache
    if _matchmaking_cache is None:
        mm_input = build_matchmaking_input(28.61, 77.20, 5.5, 19.076, 72.8777, 5.5)
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as tf:
            json.dump(mm_input, tf)
            tmp_path = tf.name
        try:
            _matchmaking_cache = run_json_command(
                ["python3", "scripts/matchmaking.py", "--json", tmp_path], verbose=verbose
            )
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
    return _matchmaking_cache


def normalize_rule_entry(entry):
    if isinstance(entry, dict):
        return entry
    if isinstance(entry, str):
        try:
            parsed = ast.literal_eval(entry)
            if isinstance(parsed, dict):
                return parsed
        except (ValueError, SyntaxError):
            return {}
    return {}


def get_yogas_data(verbose=False):
    global _yogas_cache
    if _yogas_cache is None:
        _yogas_cache = run_json_command(
            [
                "python3",
                "scripts/chart.py",
                "yogas",
                "--year",
                "1978",
                "--month",
                "3",
                "--day",
                "5",
                "--hour",
                "14",
                "--minute",
                "20",
                "--lat",
                "13.0827",
                "--lon",
                "80.2707",
                "--tz",
                "5.5",
                "--place",
                "Chennai",
            ],
            verbose=verbose,
        )
    return _yogas_cache


def get_doshas_data(verbose=False):
    global _doshas_cache
    if _doshas_cache is None:
        _doshas_cache = run_json_command(
            [
                "python3",
                "scripts/chart.py",
                "doshas",
                "--year",
                "1978",
                "--month",
                "3",
                "--day",
                "5",
                "--hour",
                "14",
                "--minute",
                "20",
                "--lat",
                "13.0827",
                "--lon",
                "80.2707",
                "--tz",
                "5.5",
                "--place",
                "Chennai",
            ],
            verbose=verbose,
        )
    return _doshas_cache


def run_local_skill_case(test_case, verbose=False):
    if test_case.name == "Panchang":
        panchang = get_panchang_data(verbose=verbose)
        return {
            "tithi_name": panchang["tithi"]["name"],
            "nakshatra_name": panchang["nakshatra"]["name"],
        }

    if test_case.name == "Panchang_Details":
        panchang = get_panchang_data(verbose=verbose)
        return {
            "yoga_name": panchang["yoga"]["name"],
            "karana_name": panchang["karana"]["name"],
        }

    if test_case.name == "Panchang_MonthPaksha":
        panchang = get_panchang_data(verbose=verbose)
        return {"lunar_month": panchang["lunar_month"], "paksha": panchang["paksha"]}

    if test_case.name == "Geocoding":
        geocoding = get_geocoding_data(verbose=verbose)
        return {"latitude": geocoding["latitude"], "longitude": geocoding["longitude"]}

    if test_case.name == "Geocoding_Metadata":
        geocoding = get_geocoding_data(verbose=verbose)
        return {
            "timezone_offset": geocoding["timezone_offset"],
            "country": geocoding["country"],
        }

    if test_case.name.startswith("Chart_"):
        division = test_case.name.split("_", 1)[1]
        chart = get_chart_data(verbose=verbose)
        key = f"{division.lower()}_lagna_rasi"
        return {key: chart[division]["planetary_positions"]["lagna"]["rasi"]}

    if test_case.name == "MoonRasi_D1":
        chart = get_chart_data(verbose=verbose)
        return {"d1_moon_rasi": chart["D1"]["planetary_positions"]["moon"]["rasi"]}

    if test_case.name == "MoonRasi_D9":
        chart = get_chart_data(verbose=verbose)
        return {"d9_moon_rasi": chart["D9"]["planetary_positions"]["moon"]["rasi"]}

    if test_case.name == "Dasha_BirthProfile":
        dasha = get_dasha_data(verbose=verbose)
        vimshottari = dasha["vimshottari"]
        return {
            "birth_nakshatra": vimshottari["birth_nakshatra"],
            "birth_nakshatra_name": vimshottari["birth_nakshatra_name"],
            "birth_nakshatra_lord": vimshottari["birth_nakshatra_lord"],
        }

    if test_case.name == "Dasha_MahadashaSequence":
        dasha = get_dasha_data(verbose=verbose)
        sequence = dasha["vimshottari"]["mahadasha_sequence"]
        return {
            "first_mahadasha": sequence[0]["planet"],
            "second_mahadasha": sequence[1]["planet"],
            "third_mahadasha": sequence[2]["planet"],
            "fourth_mahadasha": sequence[3]["planet"],
        }

    if test_case.name == "Dasha_AntardashaDetection":
        dasha = get_dasha_data(verbose=verbose)
        sequence = dasha["vimshottari"]["mahadasha_sequence"]
        saturn_mahadasha = get_saturn_mahadasha(sequence)
        first_antardasha = saturn_mahadasha["sub_periods"][0]
        return {
            "saturn_mahadasha_first_antardasha": first_antardasha["planet"],
            "saturn_mahadasha_second_antardasha": saturn_mahadasha["sub_periods"][1]["planet"],
            "saturn_mahadasha_first_pratyantardasha": first_antardasha["sub_periods"][0]["planet"],
        }

    if test_case.name == "Dasha_MahadashaDurations":
        dasha = get_dasha_data(verbose=verbose)
        sequence = dasha["vimshottari"]["mahadasha_sequence"]
        return {
            "second_mahadasha_duration_years": sequence[1]["duration_years"],
            "fourth_mahadasha_duration_years": sequence[3]["duration_years"],
        }

    if test_case.name == "Dasha_SaturnAntardashaOrder":
        dasha = get_dasha_data(verbose=verbose)
        sequence = dasha["vimshottari"]["mahadasha_sequence"]
        saturn_mahadasha = get_saturn_mahadasha(sequence)
        return {
            "saturn_third_antardasha": saturn_mahadasha["sub_periods"][2]["planet"],
            "saturn_seventh_antardasha": saturn_mahadasha["sub_periods"][6]["planet"],
        }

    if test_case.name == "Matchmaking":
        mm = get_matchmaking_data(verbose=verbose)
        return {"total_points": mm["total_points"]}

    if test_case.name == "Matchmaking_Dosha":
        mm = get_matchmaking_data(verbose=verbose)
        koota_by_name = {item["name"]: item for item in mm["koota_scores"]}
        return {
            "nadi_points": koota_by_name["Nadi"]["obtained_points"],
            "bhakoot_dosha": koota_by_name["Bhakoot"].get("dosha", False),
        }

    if test_case.name == "Matchmaking_MoonSigns":
        mm = get_matchmaking_data(verbose=verbose)
        return {
            "person_a_moon_sign": mm["partners"]["person_a"]["moon_sign"],
            "person_b_moon_sign": mm["partners"]["person_b"]["moon_sign"],
        }

    if test_case.name == "Yoga_Detection":
        yogas = get_yogas_data(verbose=verbose).get("yogas", [])
        primary = get_primary_rule_entry(yogas)
        return {
            "yoga_count": len(yogas),
            "primary_yoga_name": primary.get("name", ""),
        }

    if test_case.name == "Dosha_Detection":
        doshas = get_doshas_data(verbose=verbose).get("doshas", [])
        primary = get_primary_rule_entry(doshas)
        return {
            "dosha_count": len(doshas),
            "primary_dosha_name": primary.get("name", ""),
            "primary_dosha_severity": primary.get("severity", ""),
        }

    if test_case.name == "Yoga_Profile":
        yogas = get_yogas_data(verbose=verbose).get("yogas", [])
        primary = get_primary_rule_entry(yogas)
        return {
            "primary_yoga_type": primary.get("type", ""),
            "primary_yoga_strength": primary.get("strength", ""),
        }

    if test_case.name == "Dosha_Profile":
        doshas = get_doshas_data(verbose=verbose).get("doshas", [])
        primary = get_primary_rule_entry(doshas)
        houses = primary.get("houses_involved", [])
        first_house = houses[0] if isinstance(houses, list) and houses else None
        return {
            "primary_dosha_type": primary.get("type", ""),
            "primary_dosha_first_house": first_house,
        }

    if test_case.name == "Implicit_Multi_2Tool":
        ayodhya = get_geocoding_for_place("Ayodhya", verbose=verbose)
        panchang = get_panchang_for_location(
            "1947-08-15",
            ayodhya["latitude"],
            ayodhya["longitude"],
            ayodhya["timezone_offset"],
            verbose=verbose,
        )
        return {
            "latitude": ayodhya["latitude"],
            "longitude": ayodhya["longitude"],
            "tithi_name": panchang["tithi"]["name"],
            "nakshatra_name": panchang["nakshatra"]["name"],
        }

    if test_case.name == "Implicit_Multi_3Tool":
        delhi = get_geocoding_for_place("Delhi", verbose=verbose)
        d1 = get_d1_chart_for_location(
            delhi["latitude"], delhi["longitude"], delhi["timezone_offset"], verbose=verbose
        )
        dasha = get_dasha_for_location(
            delhi["latitude"], delhi["longitude"], delhi["timezone_offset"], verbose=verbose
        )
        return {
            "delhi_latitude": delhi["latitude"],
            "delhi_longitude": delhi["longitude"],
            "d1_lagna_rasi": d1["planetary_positions"]["lagna"]["rasi"],
            "birth_nakshatra_name": dasha["vimshottari"]["birth_nakshatra_name"],
        }

    if test_case.name == "Implicit_Multi_4Tool":
        ayodhya = get_geocoding_for_place("Ayodhya", verbose=verbose)
        delhi = get_geocoding_for_place("Delhi", verbose=verbose)
        mumbai = get_geocoding_for_place("Mumbai", verbose=verbose)
        panchang = get_panchang_for_location(
            "1947-08-15",
            ayodhya["latitude"],
            ayodhya["longitude"],
            ayodhya["timezone_offset"],
            verbose=verbose,
        )
        d1 = get_d1_chart_for_location(
            delhi["latitude"], delhi["longitude"], delhi["timezone_offset"], verbose=verbose
        )
        matchmaking = get_matchmaking_for_locations(
            delhi["latitude"],
            delhi["longitude"],
            delhi["timezone_offset"],
            mumbai["latitude"],
            mumbai["longitude"],
            mumbai["timezone_offset"],
            verbose=verbose,
        )
        return {
            "ayodhya_tithi_name": panchang["tithi"]["name"],
            "delhi_d1_lagna_rasi": d1["planetary_positions"]["lagna"]["rasi"],
            "compatibility_total_points": matchmaking["total_points"],
            "mumbai_longitude": mumbai["longitude"],
        }

    if test_case.name == "Implicit_Multi_5Tool":
        ayodhya = get_geocoding_for_place("Ayodhya", verbose=verbose)
        delhi = get_geocoding_for_place("Delhi", verbose=verbose)
        mumbai = get_geocoding_for_place("Mumbai", verbose=verbose)
        panchang = get_panchang_for_location(
            "1947-08-15",
            ayodhya["latitude"],
            ayodhya["longitude"],
            ayodhya["timezone_offset"],
            verbose=verbose,
        )
        d1 = get_d1_chart_for_location(
            delhi["latitude"], delhi["longitude"], delhi["timezone_offset"], verbose=verbose
        )
        dasha = get_dasha_for_location(
            delhi["latitude"], delhi["longitude"], delhi["timezone_offset"], verbose=verbose
        )
        matchmaking = get_matchmaking_for_locations(
            delhi["latitude"],
            delhi["longitude"],
            delhi["timezone_offset"],
            mumbai["latitude"],
            mumbai["longitude"],
            mumbai["timezone_offset"],
            verbose=verbose,
        )
        return {
            "ayodhya_nakshatra_name": panchang["nakshatra"]["name"],
            "delhi_d1_lagna_rasi": d1["planetary_positions"]["lagna"]["rasi"],
            "delhi_birth_nakshatra_lord": dasha["vimshottari"]["birth_nakshatra_lord"],
            "compatibility_total_points": matchmaking["total_points"],
            "mumbai_longitude": mumbai["longitude"],
        }

    raise RuntimeError(f"No local mapping implemented for test {test_case.name}")


def run_agent_case(test_case, verbose=False):
    cmd = OPENCLAW_CMD + [test_case.prompt]
    if verbose:
        print(f"    Command: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if result.returncode != 0:
        err = (result.stderr or "").strip()
        return {
            "ok": False,
            "error": f"Exit code {result.returncode}" + (f": {err}" if err else ""),
            "output": result.stdout,
            "agent_text": "",
            "actual_json": None,
        }

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": "Invalid JSON output from CLI",
            "output": result.stdout,
            "agent_text": "",
            "actual_json": None,
        }

    agent_text = extract_agent_text(payload)
    if is_quota_error(agent_text):
        return {
            "ok": False,
            "error": "Provider quota exceeded (429)",
            "output": result.stdout,
            "agent_text": agent_text,
            "actual_json": None,
        }

    actual = extract_json_from_text(agent_text)
    if actual is None:
        return {
            "ok": False,
            "error": "Failed to extract JSON from response",
            "output": result.stdout,
            "agent_text": agent_text,
            "actual_json": None,
        }

    return {
        "ok": True,
        "error": "",
        "output": result.stdout,
        "agent_text": agent_text,
        "actual_json": actual,
    }


def run_test(test_case, golden_data, mode="auto", verbose=False):
    print(f"\nRunning Test: {test_case.name}...")
    print(f"[?] Question: {test_case.prompt}")

    start = time.time()
    expected_json = golden_data.get(test_case.golden_key)
    actual_json = None

    try:
        if mode == "local":
            test_case.mode_used = "local"
            actual_json = run_local_skill_case(test_case, verbose=verbose)
        else:
            agent_result = run_agent_case(test_case, verbose=verbose)
            test_case.output = agent_result["output"]

            if agent_result["ok"]:
                test_case.mode_used = "agent"
                actual_json = agent_result["actual_json"]
            elif mode == "auto":
                print(f"[i] Agent path unavailable ({agent_result['error']}); using local fallback")
                test_case.mode_used = "local-fallback"
                actual_json = run_local_skill_case(test_case, verbose=verbose)
            else:
                test_case.status = "ERROR"
                test_case.error = agent_result["error"]
                print(f"[!] Error: {test_case.error}")
                if verbose and agent_result["agent_text"]:
                    print(agent_result["agent_text"])
                return

        test_case.actual_json = actual_json
        print(f"[E] Expected: {json.dumps(expected_json, separators=(',', ':'))}")
        print(f"[A] Actual:   {json.dumps(actual_json, separators=(',', ':'))}")

        diffs = compare_values(actual_json, expected_json)
        if diffs:
            test_case.status = "FAIL"
            test_case.diff = diffs
            test_case.error = f"Structural mismatch ({len(diffs)} diffs)"
            print("[Status] FAIL")
            if verbose:
                for diff in diffs:
                    print(f"    - {diff}")
        else:
            test_case.status = "PASS"
            print("[Status] PASS")

    except subprocess.TimeoutExpired:
        test_case.status = "TIMEOUT"
        test_case.error = "Timed out"
        print("[!] Error: TIMEOUT")
    except Exception as exc:
        test_case.status = "ERROR"
        test_case.error = str(exc)
        print(f"[!] Error: {exc}")
    finally:
        test_case.duration = time.time() - start


def print_summary(golden_data):
    print("\n" + "=" * 95)
    print(f"{'TEST SUMMARY':^95}")
    print("=" * 95)
    print(f"{'TEST NAME':<20} | {'STATUS':<10} | {'MODE':<14} | {'TIME':<6} | DETAILS")
    print("-" * 95)

    passed = 0
    failed = 0
    failures = []
    for test in TEST_CASES:
        if test.status == "PASS":
            passed += 1
        else:
            failed += 1
            failures.append(test)
        print(
            f"{test.name:<20} | {test.status:<10} | {test.mode_used or '-':<14} | "
            f"{test.duration:.1f}s  | {test.error or 'OK'}"
        )

    print("-" * 95)
    print(f"Total: {len(TEST_CASES)} | Passed: {passed} | Failed: {failed}")
    print("=" * 95)

    if failed > 0:
        print("\n" + "!" * 80)
        print(f"{'HUMAN VALIDATION REQUIRED':^80}")
        print("!" * 80)
        for test in failures:
            print(f"\nTEST: {test.name}")
            print(f"MODE USED: {test.mode_used or 'n/a'}")
            print(f"PROMPT: {test.prompt}")
            if test.golden_key:
                print("-" * 40)
                print("EXPECTED (Golden Data):")
                print(json.dumps(golden_data.get(test.golden_key), indent=2))
                print("-" * 40)
                print("ACTUAL:")
                if test.actual_json is not None:
                    print(json.dumps(test.actual_json, indent=2))
                elif test.diff:
                    for diff in test.diff:
                        print(f"  MISMATCH: {diff}")
                else:
                    print(f"  ERROR: {test.error}")
            print("=" * 80)

    sys.exit(1 if failed > 0 else 0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run skill validation tests.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument(
        "--mode",
        choices=["auto", "agent", "local"],
        default="auto",
        help="Execution mode: agent only, local scripts only, or auto fallback",
    )
    args = parser.parse_args()

    print(f"Loading golden data from {GOLDEN_FILE}...")
    golden_data = load_golden_data()

    print(
        f"Starting Deterministic Skill Test Suite... Verbose: {args.verbose} | Mode: {args.mode}"
    )
    for test in TEST_CASES:
        run_test(test, golden_data, mode=args.mode, verbose=args.verbose)

    print_summary(golden_data)
