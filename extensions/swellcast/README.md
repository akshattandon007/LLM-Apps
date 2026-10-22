# 🌊 SwellCast

**Your daily surf condition forecaster, right in your terminal.**

SwellCast is a CLI tool that tells you if the surf is worth paddling out. Enter a beach name and get wave height, swell period, wind data, temperature, and a surf-ability score — all from free, keyless APIs.

## Install

```bash
pip install /path/to/swellcast
# or from the repo:
pip install -e /data/LLM-Apps/extensions/swellcast/
```

## Usage

```bash
# By place name (uses Open-Meteo geocoding)
swellcast "Santa Cruz, CA"
swellcast "Huntington Beach"

# By latitude/longitude
swellcast 36.97 -122.03

# Extended forecast (default 5 days, max 16)
swellcast "Pipeline, HI" --days 7

# Skip weather (waves only)
swellcast "Malibu" --no-weather

# Version
swellcast --version
swellcast --help
```

## Example Output

```
────────────────────────────────────────────────
  SwellCast — Santa Cruz, California, United States
  36.9741°N, 122.0308°W
────────────────────────────────────────────────

  Thu Oct 22 — Surf Score 8/10 🏄
  Waves: 1.5m from WSW (247°) · Period: 11s
  Swell: 1.2m from W (276°) · Period: 11s
  Wind: 11 km/h from WNW · High: 18°C · Moderate rain
  Conditions: Good size, Long period, Onshore wind

  Fri Oct 23 — Surf Score 6/10 👍
  Waves: 1.8m from WNW (287°) · Period: 10s
  Swell: 1.6m from WNW (296°) · Period: 7s
  Wind: 10 km/h from W · High: 20°C · Partly cloudy
  Conditions: Good size, Moderate period, Onshore wind
```

## Surf Score

| Score | Label | Meaning |
|-------|-------|---------|
| 7.5–10 | Excellent 🏄 | Perfect session — good size, long-period swell, clean wind |
| 5.5–7.5 | Good 👍 | Decent waves, worth going |
| 3.5–5.5 | Fair 🌊 | Marginal — short period or onshore wind |
| 0–3.5 | Poor 😞 | Flat, windy, or dangerous |

The score factors: wave height, swell period, wind speed, wind direction relative to swell.

## Data Sources (free, no API keys)

- **Open-Meteo Marine API** — wave height, wave period, swell data, wave direction
- **Open-Meteo Weather API** — wind speed, wind direction, temperature, weather conditions
- **Open-Meteo Geocoding API** — resolve place names to coordinates

## Tests

```bash
cd /path/to/swellcast
python3 -m pytest tests/ -v
```

Tests cover the scoring algorithm, wind direction labeling, and angle classification. All tests use deterministic inputs — no network required.

## License

MIT