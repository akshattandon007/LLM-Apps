# Flow — SwellCast

## Execution Trace

### CLI Entry Point: `swellcast.cli.main()`

```
swellcast <place> [--days N] [--no-weather] [--version]
```

**Main execution path:**

```
cli.main()                                    # argparse: parse args → place, days, no_weather
 │
 ├─ [Place name given]
 │  geo.geocode(query)                        # Open-Meteo Geocoding API
 │  │  GET https://geocoding-api.open-meteo.com/v1/search?name=...
 │  └─ returns Location(name, lat, lon, ...)
 │
 ├─ [lat/lon given]
 │  Location(lat, lon) constructed directly
 │
 ├─ core.fetch_report(location, days)         # Fetch all data
 │  │
 │  ├─ GET https://marine-api.open-meteo.com/v1/marine?latitude=...
 │  │     &daily=wave_height_max,wave_direction_dominant,wave_period_max,
 │  │             swell_wave_height_max,swell_wave_direction_dominant,swell_wave_period_max
 │  │  └─ Returns daily arrays of wave/swell data
 │  │
 │  ├─ GET https://api.open-meteo.com/v1/forecast?latitude=...
 │  │     &daily=temperature_2m_max,wind_speed_10m_max,wind_direction_10m_dominant,weather_code
 │  │  └─ Returns daily weather arrays
 │  │
 │  └─ For each day:
 │       core._compute_score(day)             # Apply scoring formula
 │       │  ├─ Wave height check (flat/good/big/dangerous)
 │       │  ├─ Swell period check (short/moderate/long/excellent)
 │       │  ├─ Wind direction vs wave direction (offshore/onshore/cross-shore)
 │       │  ├─ Wind speed penalty (gusty/windy)
 │       │  └─ Returns (score, label, condition_note)
 │       └─ Append SurfDay to report.days[]
 │
 └─ Print each SurfDay:
      ├─ Date header + surf score + emoji
      ├─ Waves: height, direction, period
      ├─ Swell: height, direction, period (if present)
      ├─ Wind: speed + direction, temperature, weather code
      └─ Conditions: short description
```

### Score Computation Detail (`_compute_score`)

```
Input: SurfDay{wave_height, wave_dir, wave_period, swell_height, ..., wind_speed, wind_dir}
Output: (score: float 0-10, label: str, condition: str)

  score = 5.0  # baseline

  # Wave height adjustment
  wave_h < 0.3m  → -2.5 (Flat)
  wave_h < 0.6m  → -1.0 (Small)
  0.6m ≤ h ≤ 2.0m → +2.0 (Good size)
  2.0m < h ≤ 3.5m → +1.0 (Big)
  h > 3.5m        → -1.0 (Dangerous)

  # Swell period adjustment (uses swell period if available, else wave period)
  period < 7s  → -1.5 (Short period — wind swell)
  7s ≤ p < 10s → +0.5 (Moderate period)
  10s ≤ p < 14s → +1.5 (Long period — groundswell)
  p ≥ 14s       → +2.0 (Excellent period — hurricane/tropical swell)

  # Wind direction relative to swell
  angle_diff = abs(wave_dir - wind_dir)  [wrapped to 0-180]
  diff ≤ 45°  → -1.0 (Onshore — messes up the waves)
  diff ≥ 135° → +1.0 (Offshore — holds up the wave face)
  otherwise   → no adjustment (Cross-shore)

  # Wind speed
  speed > 40 km/h → -1.5 (Gusty — dangerous/difficult)
  speed > 25 km/h → -0.5 (Windy — choppy)

  score = clamp(0, score, 10)
```

## Module Dependency Graph

```
swellcast/
├── __init__.py          # Version constant, no imports
├── cli.py               # Entry point. Imports: geo, core, models
│   import: geo.geocode()
│   import: core.fetch_report()
│   import: models.Location
│   import: core._wind_dir_label()
│   import: core.WMO_CODES
├── core.py              # Business logic + API fetching. Imports: models
│   import: models.Location, SurfDay, SurfReport
│   functions:
│     _fetch_json()          # HTTP GET → JSON (urllib)
│     _wind_dir_label()      # deg → compass label
│     _wave_origin_angle()   # wave_dir, wind_dir → offshore/onshore/cross-shore
│     _compute_score()       # SurfDay → (score, label, condition)
│     fetch_report()         # Location → SurfReport (orchestrates API calls + scoring)
├── geo.py               # Geocoding. Imports: models
│   import: models.Location
│   functions:
│     geocode()              # place name → Location
└── models.py             # Dataclasses. No imports beyond stdlib dataclasses
    Location: name, country, lat, lon, admin1, timezone
    Coordinates: lat, lon
    SurfDay: dt, wave_height, wave_dir, wave_period, swell_*, wind_*, score, ...
    SurfReport: location, days[], generated
```

## Data Flow

```
User types "swellcast Huntington Beach"
     │
     ▼
cli.main()
  │  place = "Huntington Beach"
  │
  ▼
geo.geocode("Huntington Beach")
  │  GET https://geocoding-api.open-meteo.com/v1/search?name=Huntington+Beach
  │
  ▼
Location{name="Huntington Beach", lat=33.66, lon=-117.99, admin1="California", ...}
  │
  ▼
core.fetch_report(location, days=5)
  │
  ├─ GET marine-api.open-meteo.com/v1/marine?lat=33.66&lon=-117.99&daily=...
  │     → {"daily": {"time":["2026-10-22",...], "wave_height_max":[1.2,...], ...}}
  │
  ├─ GET api.open-meteo.com/v1/forecast?lat=33.66&lon=-117.99&daily=...
  │     → {"daily": {"temperature_2m_max":[22.5,...], "wind_speed_10m_max":[12,...], ...}}
  │
  ▼
SurfReport{location=..., days=[
  SurfDay{dt=2026-10-22, wave_height=1.2, swell_period=12, ..., score=8.0, ...},
  SurfDay{dt=2026-10-23, ...},
  ...
]}
  │
  ▼
cli.main() prints formatted output
  "────────────────────────────────────────────────"
  "  SwellCast — Huntington Beach, California, United States"
  "────────────────────────────────────────────────"
  ...
  "  Thu Oct 22 — Surf Score 8/10 🏄"
  "  Waves: 1.2m from SW (225°) · Period: 12s"
  ...
```