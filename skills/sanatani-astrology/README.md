# Sanatani Astrology Skill

Vedic Astrology (Jyotish) capabilities for OpenClaw.

This skill provides comprehensive astrophysical calculations based on the Swiss Ephemeris (`pyswisseph`) and PyEphem, validated against Drik Panchang standards.

## Features

- **Panchang**: Daily Tithi, Nakshatra, Yoga, Karana, and auspicious/inauspicious times (Rahu Kaal, Yamaganda, Gulika).
- **Birth Charts (Kundali)**: Calculates planetary positions and 16 divisional charts (D1-D16).
- **Matchmaking (Gun Milan)**: Detailed Ashta-Koota compatibility analysis with scoring breakdown.
- **Geocoding**: Built-in place name resolution to coordinates.

## Installation

### Prerequisites

- Python 3.10+
- A C compiler (gcc/clang) may be required on some systems to build `pyswisseph` wheels if binary wheels are unavailable.

### Install

From the root of the `openclaw` workspace:

```bash
pip install -e skills/sanatani-astrology
```

Or from within the skill directory:

```bash
cd skills/sanatani-astrology
pip install -e .
```

## Usage

### 1. As an OpenClaw Agent Tool (Recommended)

Once installed, the `sanatani-astrology` skill is automatically available to any OpenClaw agent configured to use it.
You can ask natural language queries:

> "Calculate Panchang for today in Mumbai."
> "What is my D9 Lagna Rasi? (Born 1990-01-01 12:00 in Delhi)"
> "Check compatibility between Person A (Alice, ...) and Person B (Bob, ...)"

### 2. Standalone Scripts (For Developers)

You can run the core logic directly via the provided scripts in `scripts/`:

**Panchang:**

```bash
python scripts/panchang.py --date 2026-02-07 --lat 19.076 --lon 72.877
```

**Chart Generation:**

```bash
python scripts/chart.py charts --year 1990 --month 1 --day 1 --hour 12 --minute 0 --lat 28.6 --lon 77.2 --divisions D1,D9
```

**Geocoding:**

```bash
python scripts/geocoding.py --place "Ayodhya"
```

**Matchmaking:**
First create a JSON file with birth details for `person_a` and `person_b`, then run:

```bash
python scripts/matchmaking.py --json input.json
```

## Testing

A comprehensive test suite validates the deterministic accuracy of the calculations.

```bash
# Run all tests
python scripts/test_runner.py
```

The test runner compares agent outputs against a verified "Golden Dataset" (`tests/golden_data.json`) for specific scenarios (D1-D16 charts, Panchang Tithi, Matchmaking Score).

Reference documentation for PanditJi persona and workflows can be found in `references/`.
