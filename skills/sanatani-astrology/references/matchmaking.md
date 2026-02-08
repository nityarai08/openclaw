---
name: matchmaking
description: >
  Marriage compatibility analysis using Ashta-Koota system. Use when user asks about:
  compatibility, kundali milan, marriage matching, partner compatibility, guna milan,
  matchmaking, whether two people are compatible, Nadi dosha, Bhakoot dosha, or
  relationship compatibility based on horoscopes.
---

# Matchmaking & Compatibility

Analyze marriage compatibility between two people using the traditional Ashta-Koota (8 factors) system.

## The Ashta-Koota System

| Koota        | Points | What It Measures                           |
| ------------ | ------ | ------------------------------------------ |
| Varna        | 1      | Spiritual compatibility, ego levels        |
| Vashya       | 2      | Mutual attraction, control dynamics        |
| Tara         | 3      | Destiny compatibility, health              |
| Yoni         | 4      | Physical/sexual compatibility              |
| Graha Maitri | 5      | Mental wavelength, friendship              |
| Gana         | 6      | Temperament match (Deva/Manushya/Rakshasa) |
| Bhakoot      | 7      | Love, family welfare, financial prosperity |
| Nadi         | 8      | Health of progeny, genetic compatibility   |

**Maximum Score**: 36 points

**Compatibility Bands:**

- **28-36**: Excellent match
- **21-27**: Good match
- **18-20**: Average, proceed with caution
- **Below 18**: Significant challenges

## Critical Doshas

### Nadi Dosha (8 points at stake)

- Same Nadi = 0 points = Major concern for children's health
- Different Nadi = 8 points = Good

### Bhakoot Dosha (7 points at stake)

- Certain Moon sign combinations create financial/emotional friction
- 6-8, 9-5, 12-2 combinations are problematic

### Gana Dosha

- Deva-Rakshasa combination can cause temperament clashes

## Tools

### Geocoding

**Use this when user provides only place names without coordinates.**

```bash
python3 {baseDir}/scripts/geocoding.py --place "Mumbai, India"
```

Returns `latitude`, `longitude`, and `timezone_offset`. Call once for each person's birth place.

### Matchmaking

Calculate Ashta-Koota compatibility between two people.

**Step 1**: Create a JSON file with both persons' birth details:

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

**Step 2**: Run the matchmaking script:

```bash
python3 {baseDir}/scripts/matchmaking.py --json input.json
```

**Returns**: Total points, individual koota scores, doshas identified, compatibility band.

## Workflow

1. **Verify birth details for BOTH people**: Must have date, time, place for each.
2. **Resolve coordinates**: If only place names provided, run `geocoding.py --place` for each location.
3. **Create input JSON**: Write JSON file with both persons' details.
4. **Run matchmaking**: Execute `matchmaking.py --json input.json`.
5. **Interpret results**:
   - State total score and band (Excellent/Good/Average/Below Average)
   - Highlight critical doshas (especially Nadi, Bhakoot)
   - Note strongest matching factors
6. **Be direct**: "Good match" or "Significant challenges exist"

## Response Guidelines

- Lead with the bottom line: overall compatibility verdict
- Focus on critical doshas (Nadi, Bhakoot) first
- Mention remedies only if asked or if major dosha present
- Don't sugarcoat - be honest about challenges

## Examples

### Full Compatibility Check

**User**: "Check compatibility between me (1990-05-15, 10:30 AM, Mumbai) and my partner (1992-08-20, 2:15 PM, Delhi)"

First, get coordinates (if not known):

```bash
python3 {baseDir}/scripts/geocoding.py --place "Mumbai"
python3 {baseDir}/scripts/geocoding.py --place "Delhi"
```

Then create `input.json`:

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

Run:

```bash
python3 {baseDir}/scripts/matchmaking.py --json input.json
```

**Response**: State score (e.g., "28/36 - Excellent match"), highlight key factors, note any doshas.

### Missing Details

**User**: "Is my partner compatible with me?"

**Response**: "Namaste! To analyze compatibility, I need birth date, time, and place for both you and your partner."

### Partial Details

**User**: "Check match with someone born August 20, 1992"

**Response**: "I have one person's birth date but need: 1) Time and place for August 20, 1992 person, 2) Your complete birth details (date, time, place)."

### Dosha Inquiry

**User**: "Do we have Nadi dosha?"

Run matchmaking if not already done, then check Nadi score in results.

**Response**: "Yes, Nadi dosha is present (same Nadi)" or "No, your Nadis are different (8/8 points)."
