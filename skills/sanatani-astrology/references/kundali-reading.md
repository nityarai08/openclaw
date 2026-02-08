---
name: kundali-reading
description: >
  Birth chart (Kundali) analysis including planetary positions, divisional charts,
  yogas, doshas, and dasha periods. Use when user asks about: horoscope, birth chart,
  kundali, planetary positions, lagna, ascendant, D1, D9, navamsa, career chart, D10,
  yogas, doshas, Manglik, Kaal Sarpa, dasha, mahadasha, antardasha, or general chart reading.
---

# Kundali Reading

Analyze birth charts, calculate planetary positions, identify yogas and doshas, and interpret dasha periods.

## Tools

### Geocoding

**Use this first when user provides only a place name (city/country) without coordinates.**

```bash
python3 {baseDir}/scripts/geocoding.py --place "Mumbai, India"
```

Returns `latitude`, `longitude`, and `timezone_offset` for the location. Use these values in subsequent chart calculations.

### Divisional Charts

**Primary tool for all birth chart analysis.** Returns planetary positions for any divisional chart.

```bash
python3 {baseDir}/scripts/chart.py charts \
  --year YYYY --month M --day D \
  --hour H --minute M \
  --lat LAT --lon LON --tz TZ \
  --divisions "D1,D9" \
  --place "City"
```

**Chart Types:**

- **D1 (Rashi)**: Main birth chart - overall life, personality, general destiny
- **D9 (Navamsa)**: Marriage, spouse, dharma, inner nature, spiritual path
- **D10 (Dasamsa)**: Career, profession, public status, achievements
- **D7 (Saptamsa)**: Children, progeny, creativity

**Usage:**

- Single chart: `--divisions "D1"`
- Multiple charts: `--divisions "D1,D9,D10"`

### Dasha Periods

Vimshottari dasha timing cycles.

```bash
python3 {baseDir}/scripts/chart.py dasha \
  --year YYYY --month M --day D \
  --hour H --minute M \
  --lat LAT --lon LON --tz TZ
```

### Yogas

Beneficial planetary combinations (Raja Yoga, Dhana Yoga, Gaja Kesari, etc.).

```bash
python3 {baseDir}/scripts/chart.py yogas \
  --year YYYY --month M --day D \
  --hour H --minute M \
  --lat LAT --lon LON --tz TZ
```

### Doshas

Afflictions and challenging patterns (Manglik, Kaal Sarpa, Pitra Dosha, etc.).

```bash
python3 {baseDir}/scripts/chart.py doshas \
  --year YYYY --month M --day D \
  --hour H --minute M \
  --lat LAT --lon LON --tz TZ
```

## Workflow

1. **Check for birth details**: If missing, ask user for date, time, and place of birth.
2. **Resolve coordinates**: If user provides only place name (no lat/long), run `geocoding.py --place "Place"` first to get coordinates and timezone.
3. **Calculate chart**: Run `chart.py charts` with birth details and coordinates.
4. **Analyze specifics**: Run `chart.py yogas`, `chart.py doshas`, or `chart.py dasha` as needed.
5. **Interpret**: Combine tool results with your Vedic knowledge.

## Examples

### Show Birth Chart

**User**: "Show me my birth chart" (birth details: May 15, 1990, 10:30 AM, Delhi)

```bash
python3 {baseDir}/scripts/chart.py charts \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5 \
  --divisions "D1"
```

**Response**: Interpret Lagna, key planets, patterns.

### Navamsa Analysis

**User**: "Show my D9 chart"

```bash
python3 {baseDir}/scripts/chart.py charts \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5 \
  --divisions "D9"
```

**Response**: Interpret D9 for marriage, spouse characteristics, dharmic path.

### Career Analysis

**User**: "What does my chart say about career?"

```bash
python3 {baseDir}/scripts/chart.py charts \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5 \
  --divisions "D10"
```

**Response**: Interpret D10 placements for profession and public status.

### Multiple Charts

**User**: "Show my D1 and D9 charts together"

```bash
python3 {baseDir}/scripts/chart.py charts \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5 \
  --divisions "D1,D9"
```

**Response**: Compare main chart with Navamsa for deeper analysis.

### Yoga Check

**User**: "What yogas are in my chart?"

```bash
python3 {baseDir}/scripts/chart.py yogas \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5
```

**Response**: List yogas found, explain their effects and significance.

### Dosha Check

**User**: "Do I have Manglik dosha?"

```bash
python3 {baseDir}/scripts/chart.py doshas \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5
```

**Response**: Analyze Mars placement, state severity, suggest remedies if applicable.

### Dasha Analysis

**User**: "What dasha am I in?"

```bash
python3 {baseDir}/scripts/chart.py dasha \
  --year 1990 --month 5 --day 15 \
  --hour 10 --minute 30 \
  --lat 28.6 --lon 77.2 --tz 5.5
```

**Response**: State current Mahadasha/Antardasha, interpret the planetary period.

### Comprehensive Reading

**User**: "Give me a complete chart analysis"

Run all three commands:

1. `chart.py charts --divisions "D1"`
2. `chart.py yogas`
3. `chart.py doshas`

**Response**: Comprehensive interpretation covering placements, yogas, and doshas.

### Missing Details

**User**: "Tell me my future"

**Response**: "Namaste! To analyze your chart, I need your birth date, time, and place of birth."
