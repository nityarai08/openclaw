#!/usr/bin/env python3
import ast
import json
import subprocess
import os
import tempfile

GOLDEN_FILE = "tests/golden_data.json"

def run_script(script_name, args):
    """Run a Python script and return its stdout as parsed JSON."""
    cmd = ["python3", f"scripts/{script_name}"] + args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {script_name}: {result.stderr}")
        return None
    try:
        # Try to find JSON object at start of lines
        lines = result.stdout.splitlines()
        json_buffer = ""
        capture = False
        
        for line in lines:
            if line.strip().startswith('{') or line.strip().startswith('['):
                capture = True
            if capture:
                json_buffer += line + "\n"
        
        if json_buffer:
            return json.loads(json_buffer)
            
        # Fallback: scan for first { or [ if no clean line start
        json_start = result.stdout.find('{')
        list_start = result.stdout.find('[')
        start_idx = -1
        if json_start != -1 and list_start != -1:
            start_idx = min(json_start, list_start)
        elif json_start != -1:
            start_idx = json_start
        elif list_start != -1:
            start_idx = list_start
            
        if start_idx != -1:
            return json.loads(result.stdout[start_idx:])
            
        return json.loads(result.stdout)

    except json.JSONDecodeError as e:
        # Try parsing from the LAST '{' just in case multiple appeared (e.g. in logs)
        # Verify if there is a clean JSON block at the end
        try:
            last_brace = result.stdout.rfind("{")
            if last_brace != -1:
                return json.loads(result.stdout[last_brace:])
        except json.JSONDecodeError:
            pass

        print(f"Failed to parse JSON from {script_name}: {e}")
        # print(f"Output was: {result.stdout[:200]}...") # reduce noise
        return None


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


def get_primary_rule_entry(entries):
    return normalize_rule_entry(entries[0]) if entries else {}


def get_saturn_mahadasha(sequence):
    return next(item for item in sequence if item["planet"] == "Saturn")


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


def run_matchmaking_for_locations(a_lat, a_lon, a_tz, b_lat, b_lon, b_tz):
    payload = build_matchmaking_input(a_lat, a_lon, a_tz, b_lat, b_lon, b_tz)
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as tf:
        json.dump(payload, tf)
        temp_path = tf.name

    try:
        return run_script("matchmaking.py", ["--json", temp_path])
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


def generate_golden():
    golden_data = {}
    
    # 1. Panchang
    print("Generating Panchang Golden Data...")
    panchang_data = run_script("panchang.py", [
        "--date", "1947-08-15",
        "--lat", "19.076",
        "--lon", "72.8777",
        "--tz", "5.5"
    ])
    if panchang_data and "tithi" in panchang_data:
        golden_data["Panchang"] = {
            "tithi_name": panchang_data["tithi"]["name"],
            "nakshatra_name": panchang_data["nakshatra"]["name"]
        }
        golden_data["Panchang_Details"] = {
            "yoga_name": panchang_data["yoga"]["name"],
            "karana_name": panchang_data["karana"]["name"],
        }
        golden_data["Panchang_MonthPaksha"] = {
            "lunar_month": panchang_data["lunar_month"],
            "paksha": panchang_data["paksha"],
        }

    # 2. Geocoding
    print("Generating Geocoding Golden Data...")
    geo_data = run_script("geocoding.py", ["--place", "Ayodhya", "--json"])
    if geo_data and geo_data.get("success"):
        golden_data["Geocoding"] = {
            "latitude": geo_data["latitude"],
            "longitude": geo_data["longitude"]
        }
        golden_data["Geocoding_Metadata"] = {
            "timezone_offset": geo_data["timezone_offset"],
            "country": geo_data["country"],
        }

    # 2b. Implicit multi-tool fixtures (natural question style)
    print("Generating Implicit Multi-Tool Golden Data...")
    ayodhya_geo = geo_data if geo_data and geo_data.get("success") else run_script(
        "geocoding.py", ["--place", "Ayodhya", "--json"]
    )
    delhi_geo = run_script("geocoding.py", ["--place", "Delhi", "--json"])
    mumbai_geo = run_script("geocoding.py", ["--place", "Mumbai", "--json"])
    chart_delhi = None
    dasha_delhi = None

    panchang_ayodhya = None
    if ayodhya_geo and ayodhya_geo.get("success"):
        panchang_ayodhya = run_script("panchang.py", [
            "--date", "1947-08-15",
            "--lat", str(ayodhya_geo["latitude"]),
            "--lon", str(ayodhya_geo["longitude"]),
            "--tz", str(ayodhya_geo["timezone_offset"]),
        ])
        if panchang_ayodhya and "tithi" in panchang_ayodhya and "nakshatra" in panchang_ayodhya:
            golden_data["Implicit_Multi_2Tool"] = {
                "latitude": ayodhya_geo["latitude"],
                "longitude": ayodhya_geo["longitude"],
                "tithi_name": panchang_ayodhya["tithi"]["name"],
                "nakshatra_name": panchang_ayodhya["nakshatra"]["name"],
            }

    if delhi_geo and delhi_geo.get("success"):
        chart_delhi = run_script("chart.py", [
            "charts",
            "--year", "1990", "--month", "1", "--day", "1",
            "--hour", "12", "--minute", "0",
            "--lat", str(delhi_geo["latitude"]),
            "--lon", str(delhi_geo["longitude"]),
            "--tz", str(delhi_geo["timezone_offset"]),
            "--divisions", "D1",
        ])
        dasha_delhi = run_script("chart.py", [
            "dasha",
            "--year", "1990", "--month", "1", "--day", "1",
            "--hour", "12", "--minute", "0",
            "--lat", str(delhi_geo["latitude"]),
            "--lon", str(delhi_geo["longitude"]),
            "--tz", str(delhi_geo["timezone_offset"]),
        ])
        if chart_delhi and dasha_delhi:
            golden_data["Implicit_Multi_3Tool"] = {
                "delhi_latitude": delhi_geo["latitude"],
                "delhi_longitude": delhi_geo["longitude"],
                "d1_lagna_rasi": chart_delhi["D1"]["planetary_positions"]["lagna"]["rasi"],
                "birth_nakshatra_name": dasha_delhi["vimshottari"]["birth_nakshatra_name"],
            }

    if (
        panchang_ayodhya
        and delhi_geo and delhi_geo.get("success")
        and mumbai_geo and mumbai_geo.get("success")
    ):
        implicit_mm = run_matchmaking_for_locations(
            delhi_geo["latitude"],
            delhi_geo["longitude"],
            delhi_geo["timezone_offset"],
            mumbai_geo["latitude"],
            mumbai_geo["longitude"],
            mumbai_geo["timezone_offset"],
        )
        if implicit_mm and "total_points" in implicit_mm:
            chart_delhi_for_implicit = run_script("chart.py", [
                "charts",
                "--year", "1990", "--month", "1", "--day", "1",
                "--hour", "12", "--minute", "0",
                "--lat", str(delhi_geo["latitude"]),
                "--lon", str(delhi_geo["longitude"]),
                "--tz", str(delhi_geo["timezone_offset"]),
                "--divisions", "D1",
            ])
            if chart_delhi_for_implicit and "D1" in chart_delhi_for_implicit:
                golden_data["Implicit_Multi_4Tool"] = {
                    "ayodhya_tithi_name": panchang_ayodhya["tithi"]["name"],
                    "delhi_d1_lagna_rasi": chart_delhi_for_implicit["D1"]["planetary_positions"]["lagna"]["rasi"],
                    "compatibility_total_points": implicit_mm["total_points"],
                    "mumbai_longitude": mumbai_geo["longitude"],
                }
            dasha_delhi_for_implicit = dasha_delhi or run_script("chart.py", [
                "dasha",
                "--year", "1990", "--month", "1", "--day", "1",
                "--hour", "12", "--minute", "0",
                "--lat", str(delhi_geo["latitude"]),
                "--lon", str(delhi_geo["longitude"]),
                "--tz", str(delhi_geo["timezone_offset"]),
            ])
            if (
                chart_delhi_for_implicit and "D1" in chart_delhi_for_implicit
                and dasha_delhi_for_implicit and "vimshottari" in dasha_delhi_for_implicit
            ):
                golden_data["Implicit_Multi_5Tool"] = {
                    "ayodhya_nakshatra_name": panchang_ayodhya["nakshatra"]["name"],
                    "delhi_d1_lagna_rasi": chart_delhi_for_implicit["D1"]["planetary_positions"]["lagna"]["rasi"],
                    "delhi_birth_nakshatra_lord": dasha_delhi_for_implicit["vimshottari"]["birth_nakshatra_lord"],
                    "compatibility_total_points": implicit_mm["total_points"],
                    "mumbai_longitude": mumbai_geo["longitude"],
                }

    # 3. Chart (D1-D16)
    print("Generating Chart Golden Data (D1-D16)...")
    chart_data = run_script("chart.py", [
        "charts",  # subcommand
        "--year", "1990", "--month", "1", "--day", "1",
        "--hour", "12", "--minute", "0",
        "--lat", "28.61", "--lon", "77.20", "--tz", "5.5",
        "--divisions", "D1,D2,D3,D4,D7,D9,D10,D12,D16"
    ])
    if chart_data:
        divisions = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16"]
        for div in divisions:
            if div in chart_data:
                key = f"{div.lower()}_lagna_rasi"
                golden_data[f"Chart_{div}"] = {key: chart_data[div]["planetary_positions"]["lagna"]["rasi"]}
        golden_data["MoonRasi_D1"] = {
            "d1_moon_rasi": chart_data["D1"]["planetary_positions"]["moon"]["rasi"]
        }
        golden_data["MoonRasi_D9"] = {
            "d9_moon_rasi": chart_data["D9"]["planetary_positions"]["moon"]["rasi"]
        }

    # 4. Dasha
    print("Generating Dasha Golden Data...")
    dasha_data = run_script("chart.py", [
        "dasha",
        "--year", "1990", "--month", "1", "--day", "1",
        "--hour", "12", "--minute", "0",
        "--lat", "28.61", "--lon", "77.20", "--tz", "5.5",
    ])
    if dasha_data and "vimshottari" in dasha_data:
        vimshottari = dasha_data["vimshottari"]
        golden_data["Dasha_BirthProfile"] = {
            "birth_nakshatra": vimshottari["birth_nakshatra"],
            "birth_nakshatra_name": vimshottari["birth_nakshatra_name"],
            "birth_nakshatra_lord": vimshottari["birth_nakshatra_lord"],
        }
        sequence = vimshottari["mahadasha_sequence"]
        golden_data["Dasha_MahadashaSequence"] = {
            "first_mahadasha": sequence[0]["planet"],
            "second_mahadasha": sequence[1]["planet"],
            "third_mahadasha": sequence[2]["planet"],
            "fourth_mahadasha": sequence[3]["planet"],
        }
        golden_data["Dasha_MahadashaDurations"] = {
            "second_mahadasha_duration_years": sequence[1]["duration_years"],
            "fourth_mahadasha_duration_years": sequence[3]["duration_years"],
        }
        saturn_mahadasha = get_saturn_mahadasha(sequence)
        first_antardasha = saturn_mahadasha["sub_periods"][0]
        golden_data["Dasha_AntardashaDetection"] = {
            "saturn_mahadasha_first_antardasha": first_antardasha["planet"],
            "saturn_mahadasha_second_antardasha": saturn_mahadasha["sub_periods"][1]["planet"],
            "saturn_mahadasha_first_pratyantardasha": first_antardasha["sub_periods"][0]["planet"],
        }
        golden_data["Dasha_SaturnAntardashaOrder"] = {
            "saturn_third_antardasha": saturn_mahadasha["sub_periods"][2]["planet"],
            "saturn_seventh_antardasha": saturn_mahadasha["sub_periods"][6]["planet"],
        }

    # 5. Yogas/Doshas detection fixture
    print("Generating Yoga/Dosha Golden Data...")
    yoga_data = run_script("chart.py", [
        "yogas",
        "--year", "1978", "--month", "3", "--day", "5",
        "--hour", "14", "--minute", "20",
        "--lat", "13.0827", "--lon", "80.2707", "--tz", "5.5",
        "--place", "Chennai",
    ])
    dosha_data = run_script("chart.py", [
        "doshas",
        "--year", "1978", "--month", "3", "--day", "5",
        "--hour", "14", "--minute", "20",
        "--lat", "13.0827", "--lon", "80.2707", "--tz", "5.5",
        "--place", "Chennai",
    ])
    yogas = (yoga_data or {}).get("yogas", [])
    doshas = (dosha_data or {}).get("doshas", [])
    first_yoga = get_primary_rule_entry(yogas)
    first_dosha = get_primary_rule_entry(doshas)
    golden_data["Yoga_Detection"] = {
        "yoga_count": len(yogas),
        "primary_yoga_name": first_yoga.get("name", ""),
    }
    golden_data["Yoga_Profile"] = {
        "primary_yoga_type": first_yoga.get("type", ""),
        "primary_yoga_strength": first_yoga.get("strength", ""),
    }
    dosha_houses = first_dosha.get("houses_involved", [])
    first_dosha_house = dosha_houses[0] if isinstance(dosha_houses, list) and dosha_houses else None
    golden_data["Dosha_Detection"] = {
        "dosha_count": len(doshas),
        "primary_dosha_name": first_dosha.get("name", ""),
        "primary_dosha_severity": first_dosha.get("severity", ""),
    }
    golden_data["Dosha_Profile"] = {
        "primary_dosha_type": first_dosha.get("type", ""),
        "primary_dosha_first_house": first_dosha_house,
    }

    # 6. Matchmaking
    print("Generating Matchmaking Golden Data...")
    mm_data = run_matchmaking_for_locations(28.61, 77.20, 5.5, 19.076, 72.8777, 5.5)
    if mm_data and "total_points" in mm_data:
        golden_data["Matchmaking"] = {
            "total_points": mm_data["total_points"]
        }
        koota_by_name = {item["name"]: item for item in mm_data["koota_scores"]}
        golden_data["Matchmaking_Dosha"] = {
            "nadi_points": koota_by_name["Nadi"]["obtained_points"],
            "bhakoot_dosha": koota_by_name["Bhakoot"].get("dosha", False),
        }
        golden_data["Matchmaking_MoonSigns"] = {
            "person_a_moon_sign": mm_data["partners"]["person_a"]["moon_sign"],
            "person_b_moon_sign": mm_data["partners"]["person_b"]["moon_sign"],
        }
    
    # Save Golden Data
    with open(GOLDEN_FILE, "w") as f:
        json.dump(golden_data, f, indent=2)
    
    print(f"Golden data saved to {GOLDEN_FILE}")

if __name__ == "__main__":
    generate_golden()
