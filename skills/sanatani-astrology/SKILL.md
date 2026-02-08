---
name: sanatani-astrology
description: >
  Vedic astrology (Jyotish) computational tools for birth chart analysis,
  divisional charts, dasha periods, yogas, doshas, panchang, muhurat selection,
  and matchmaking. ALWAYS use these tools when asked about horoscope, kundali,
  astrology, compatibility, muhurat, Hindu calendar, or panchang. Do NOT guess
  or use training data - these tools perform precise astronomical calculations.
metadata: { "openclaw": { "requires": { "bins": ["python3"] } } }
---

# Sanatani Astrology

Vedic astrology capabilities powered by the astro-core library.

**IMPORTANT**: All calculations require running the Python scripts. Do NOT guess values - always execute the tools to get accurate astronomical data.

## Installation

```bash
cd {baseDir}
pip install -e .
```

## Available Tools

### 1. Geocoding - Resolve Place to Coordinates

Resolve place names to latitude, longitude, and timezone. **Use this first when user provides a place name without coordinates.**

```bash
python3 {baseDir}/scripts/geocoding.py --place "Mumbai, India"
```

**Output**: JSON with `latitude`, `longitude`, `timezone_offset`, `country`.

### 1b. Search Locations (Multiple Results)

Search for locations when a name is ambiguous or you need the user to pick from options.

```bash
python3 {baseDir}/scripts/geocoding.py --search "Springfield" --limit 5
```

**Parameters**:

- `--search`: Search query (minimum 2 characters)
- `--limit`: Maximum results to return (default 5)

**Output**: JSON with array of matching locations sorted by population, each with `name`, `latitude`, `longitude`, `timezone_offset`, `country`, `population`.

**Use this when**: A place name could refer to multiple cities (e.g., "Hyderabad" in India vs Pakistan, "Springfield" in multiple US states).

### 2. Birth Charts (Divisional Charts)

Calculate divisional charts (D1, D9, D10, etc.) with planetary positions.

```bash
python3 {baseDir}/scripts/chart.py charts \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5 \
  --divisions "D1,D9,D10" \
  --place "Delhi"
```

**Parameters**:

- `--year`, `--month`, `--day`: Birth date
- `--hour`, `--minute`: Birth time (24-hour format)
- `--lat`, `--lon`: Latitude and longitude
- `--tz`: Timezone offset from UTC (e.g., 5.5 for IST)
- `--divisions`: Comma-separated chart types (D1=Rashi, D9=Navamsa, D10=Dasamsa, D7=Saptamsa)
- `--place`: Place name (optional, for display)

### 3. Dasha Periods (Vimshottari)

Calculate Vimshottari Dasha sequence and current planetary period.

```bash
python3 {baseDir}/scripts/chart.py dasha \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5
```

**Output**: Current Mahadasha, Antardasha, Pratyantardasha with dates.

### 4. Yogas (Beneficial Combinations)

Identify beneficial planetary combinations like Raja Yoga, Dhana Yoga, Gaja Kesari.

```bash
python3 {baseDir}/scripts/chart.py yogas \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5
```

### 5. Doshas (Afflictions)

Identify afflictions like Manglik Dosha, Kaal Sarpa, Pitra Dosha.

```bash
python3 {baseDir}/scripts/chart.py doshas \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5
```

### 6. Panchang (Daily Vedic Calendar)

Get daily panchang with tithi, nakshatra, yoga, karana, and auspicious periods.

**CRITICAL**: Panchang values (tithi, nakshatra, yoga, karana) are calculated from precise astronomical positions for a specific date and location. You MUST run this script - do NOT guess or use cached/training data as values change daily.

```bash
python3 {baseDir}/scripts/panchang.py \
  --date 2024-01-15 \
  --lat 28.6 --lon 77.2 --tz 5.5
```

**Output**: JSON with tithi, nakshatra, yoga, karana, sunrise/sunset, rahu_kaal, special yogas.

### 7. Panchang Range (Multiple Days)

Get panchang for a date range (for muhurat selection).

```bash
python3 {baseDir}/scripts/panchang.py \
  --date 2024-01-15 --days 7 \
  --lat 28.6 --lon 77.2 --tz 5.5
```

### 8. Matchmaking (Ashta-Koota Compatibility)

Calculate marriage compatibility using the 8-factor Ashta-Koota system.

```bash
python3 {baseDir}/scripts/matchmaking.py --json input.json
```

**Input JSON format**:

```json
{
  "person_a": {
    "name": "Person A",
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 10,
    "minute": 30,
    "lat": 19.076,
    "lon": 72.877,
    "tz": 5.5
  },
  "person_b": {
    "name": "Person B",
    "year": 1992,
    "month": 8,
    "day": 20,
    "hour": 14,
    "minute": 15,
    "lat": 28.614,
    "lon": 77.209,
    "tz": 5.5
  }
}
```

**Output**: Total score (out of 36), percentage, band (Excellent/Good/Average/Below Average), individual koota scores.

## Workflows

### Kundali Reading

1. **Get coordinates**: If only place name provided, run `geocoding.py --place "City"`
2. **Generate chart**: Run `chart.py charts` with D1,D9
3. **Analyze dasha**: Run `chart.py dasha` for current periods
4. **Check yogas/doshas**: Run `chart.py yogas` and `chart.py doshas`

### Muhurat Selection

1. **Get panchang range**: Run `panchang.py --days 7` (or more)
2. **Filter dates**: Look for favorable nakshatra, avoid rikta tithi, vishti karana
3. **Check special yogas**: Look for sarvartha_siddhi, amrit_siddhi, guru_pushya
4. **Avoid inauspicious**: Check rahu_kaal, yamaganda periods

### Matchmaking

1. **Get coordinates for both**: Run `geocoding.py` for each person's birthplace
2. **Create input JSON**: With both persons' birth details and coordinates
3. **Calculate compatibility**: Run `matchmaking.py --json input.json`
4. **Interpret**: Focus on total score, Nadi dosha, Bhakoot dosha

## Reference Documents

Load these for detailed guidance:

- `references/PERSONA.md` - PanditJi communication style
- `references/kundali-reading.md` - Chart interpretation workflow
- `references/matchmaking.md` - Compatibility analysis workflow
- `references/muhurat-timing.md` - Auspicious timing workflow
