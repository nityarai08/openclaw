---
name: muhurat-timing
description: >
  Auspicious timing (muhurat) and daily panchang analysis. Use when user asks about:
  muhurat, auspicious time, good day, panchang, today's tithi, nakshatra, best date for
  wedding, marriage date, griha pravesh, housewarming, property purchase, mundan,
  travel timing, business start, ceremony date, or any timing-related astrological query.
---

# Muhurat & Panchang

Find auspicious dates and times for ceremonies, and provide daily panchang analysis.

## Tools

### Geocoding

**Use this when user provides only place name without coordinates.**

```bash
python3 {baseDir}/scripts/geocoding.py --place "Mumbai, India"
```

Returns `latitude`, `longitude`, and `timezone_offset` for panchang calculations.

### Panchang (Single Day)

Full panchang for a single date with detailed timing.

```bash
python3 {baseDir}/scripts/panchang.py \
  --date 2024-01-15 \
  --lat 28.6 --lon 77.2 --tz 5.5
```

**Returns:**

- **tithi**: Lunar day with paksha (shukla/krishna)
- **nakshatra**: Lunar mansion with pada
- **yoga**: Sun-moon combination
- **karana**: Half-tithi
- **weekday**: Day of the week
- **sun_times**: Sunrise, sunset
- **special_yogas**: sarvartha_siddhi, amrit_siddhi, guru_pushya, ravi_pushya

### Panchang Range (Multiple Days)

Compact panchang for date range (for finding muhurat).

```bash
python3 {baseDir}/scripts/panchang.py \
  --date 2024-01-15 --days 30 \
  --lat 28.6 --lon 77.2 --tz 5.5
```

## Universal Panchang Factors

### Tithi Rules

- **Rikta Tithis (4, 9, 14)**: Avoid for auspicious activities
- **Amavasya (30)**: Avoid new beginnings
- **Purnima (15)**: Spiritual activities only
- **Shukla Paksha**: Waxing moon - growth, beginnings
- **Krishna Paksha**: Waning moon - completion

### Nakshatra Classification

| Type    | Nakshatras                                                 | Good For                       |
| ------- | ---------------------------------------------------------- | ------------------------------ |
| Fixed   | Rohini, Uttara Phalguni, Uttara Ashadha, Uttara Bhadrapada | Property, marriage, foundation |
| Movable | Punarvasu, Swati, Shravana, Dhanishta, Shatabhisha         | Travel, vehicles               |
| Soft    | Mrigashira, Chitra, Anuradha, Revati                       | Arts, romance                  |
| Sharp   | Ardra, Ashlesha, Jyeshtha, Moola                           | Surgery, destruction           |
| Light   | Ashwini, Pushya, Hasta, Abhijit                            | Quick tasks, learning          |

### Avoid These

- **Yoga**: Vyatipata (17), Vaidhriti (27), Parigha (19), Vishkumbha (1)
- **Karana**: is_vishti = true (Bhadra karana)
- **Periods**: Rahu Kaal, Yamaganda, Gulika Kaal

### Special Auspicious Yogas

- **Sarvartha Siddhi**: Excellent for all work
- **Amrit Siddhi**: Nectar combination
- **Guru Pushya**: Thursday + Pushya - best for education, gold, business
- **Ravi Pushya**: Sunday + Pushya - excellent for beginnings

### Planetary Considerations

- **Venus combust**: Avoid marriage, love matters
- **Jupiter combust**: Avoid ceremonies, education
- **Jupiter retrograde**: Delays in blessings

### Hora (Planetary Hours)

| Planet  | Best For                          |
| ------- | --------------------------------- |
| Sun     | Authority, government, medicine   |
| Moon    | Travel, public dealings           |
| Mars    | Competition, surgery              |
| Mercury | Business, communication, learning |
| Jupiter | Education, ceremonies, children   |
| Venus   | Marriage, arts, relationships     |
| Saturn  | Land, long-term, agriculture      |

## Individual Factors (Personalization)

### Tarabala (Star Strength)

Calculate: `(current_nakshatra - birth_nakshatra) mod 9 + 1`

| Tara | Name         | Effect                 |
| ---- | ------------ | ---------------------- |
| 1    | Janma        | Avoid major beginnings |
| 2    | Sampat       | FAVORABLE              |
| 3    | Vipat        | AVOID                  |
| 4    | Kshema       | FAVORABLE              |
| 5    | Pratyari     | Avoid                  |
| 6    | Sadhaka      | FAVORABLE              |
| 7    | Vadha        | CRITICAL AVOID         |
| 8    | Mitra        | FAVORABLE              |
| 9    | Parama Mitra | VERY FAVORABLE         |

### Chandrabala

Count from birth Moon sign to transit Moon sign:

- **Favorable**: 1, 3, 6, 7, 10, 11
- **Unfavorable**: 4, 8, 12

## Muhurat Workflow

### For Single Date Query

1. If only place name provided, run `geocoding.py --place "Place"` first
2. Run `panchang.py --date YYYY-MM-DD --lat LAT --lon LON --tz TZ`
3. Check nakshatra suitability for activity
4. Find appropriate hora times
5. Avoid inauspicious periods
6. Recommend Abhijit Muhurta if timing allows

### For Date Range Query

1. If only place name provided, run `geocoding.py --place "Place"` first
2. Run `panchang.py --date YYYY-MM-DD --days N --lat LAT --lon LON --tz TZ`
3. Filter by ceremony-specific rules
4. Calculate tarabala for person(s) involved
5. Shortlist best candidates
6. Run single-day panchang for best date to get detailed timing
7. Present with transparency

## Ceremony Quick Reference

| Ceremony       | Key Nakshatras                                          | Avoid                   | Best Hora        |
| -------------- | ------------------------------------------------------- | ----------------------- | ---------------- |
| Marriage       | Rohini, Uttara Phalguni, Hasta, Swati, Anuradha, Revati | Tue/Sat, Venus combust  | Venus, Jupiter   |
| Griha Pravesh  | Fixed nakshatras                                        | Jupiter retrograde      | Jupiter, Sun     |
| Property       | Fixed + Pushya, Shravana                                | Vishti karana           | Jupiter, Venus   |
| Business Start | Ashwini, Pushya, Hasta, Shravana                        | Rikta tithi             | Mercury, Jupiter |
| Travel         | Movable nakshatras                                      | Rahu Kaal, Yamaganda    | Moon, Mercury    |
| Mundan         | Ashwini, Pushya, Hasta, Revati                          | Child's birth nakshatra | Moon             |

## Examples

### Today's Panchang

**User**: "What is today's panchang?"

```bash
python3 {baseDir}/scripts/geocoding.py --place "Delhi"
python3 {baseDir}/scripts/panchang.py --date 2024-01-15 --lat 28.6 --lon 77.2 --tz 5.5
```

**Response**: Interpret tithi, nakshatra, yoga. Note Rahu Kaal and auspicious windows.

### Personalized Day

**User**: "How is today for me?" (birth Moon in Rohini from context)

```bash
python3 {baseDir}/scripts/panchang.py --date 2024-01-15 --lat 28.6 --lon 77.2 --tz 5.5
```

Calculate Tarabala from Rohini to today's nakshatra.

**Response**: Personalized assessment based on tarabala + panchang quality.

### Travel Muhurat

**User**: "Good time for travel tomorrow?"

```bash
python3 {baseDir}/scripts/panchang.py --date 2024-01-16 --lat 28.6 --lon 77.2 --tz 5.5
```

**Response**: Find Moon/Mercury/Venus hora times, avoid Rahu Kaal/Yamaganda.

### Find Wedding Dates

**User**: "Find marriage dates in February-March" (couple's birth nakshatras in context)

```bash
python3 {baseDir}/scripts/panchang.py --date 2024-02-01 --days 60 --lat 28.6 --lon 77.2 --tz 5.5
```

Filter for marriage nakshatras, avoid Tue/Sat, check venus combust. Calculate tarabala for both.

Then get details for best date:

```bash
python3 {baseDir}/scripts/panchang.py --date 2024-02-15 --lat 28.6 --lon 77.2 --tz 5.5
```

**Response**: Present best dates with reasoning and timing.

### Business Launch

**User**: "Best day to start my business in January?"

```bash
python3 {baseDir}/scripts/panchang.py --date 2024-01-01 --days 31 --lat 28.6 --lon 77.2 --tz 5.5
```

Look for guru_pushya or ravi_pushya in special_yogas.

**Response**: Recommend Guru Pushya date if found, with timing.
