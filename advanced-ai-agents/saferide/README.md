# 🚗 SafeRide — Multi-Agent Pre-Trip Safety Checker

**Check your vehicle and route before you drive — all in one command.**

SafeRide is a multi-agent orchestration system that combines three specialized agents to give you a complete trip safety report:

1. **Vehicle Safety Scout** — checks NHTSA for open recalls on your specific vehicle (by VIN or make/model/year)
2. **Route Weather Scanner** — forecasts conditions at your origin, destination, and every waypoint along the way
3. **Trip Advisor** — compiles results into a clear verdict with hazard warnings

No API keys. No signup. No subscriptions.

## How It Works

```
You ──> saferide "Toyota Camry 2020" "New York, NY" "Los Angeles, CA"
          │
          ├── Vehicle Safety Agent ──> NHTSA API ──> Open recalls found?
          ├── Weather Agent ─────────> Open-Meteo ─> Weather hazards on route?
          └── Trip Advisor ──────────> Compile report with verdict
          │
          └── Rich terminal output: recalls table + weather grid + final verdict
```

## Quick Start

```bash
# Install
pip install httpx rich pydantic python-dotenv

# Interactive mode (asks for vehicle + route)
cd saferide
python -m saferide

# One-shot: vehicle by make/model/year + origin/destination
python -m saferide "Toyota" "Camry" 2020 "New York, NY" "Los Angeles, CA"

# With waypoints
python -m saferide "Honda" "Civic" 2019 "Chicago, IL" "Miami, FL" \
  -w "Nashville, TN" "Atlanta, GA"

# By VIN (17-character vehicle identification number)
python -m saferide --vin 1HGCM82633A004352 "Boston, MA" "Washington, DC"
```

## Architecture

### Three Specialized Agents

| Agent | File | API | What It Does |
|-------|------|-----|-------------|
| **Vehicle Safety Scout** | `agents/vehicle_agent.py` | [NHTSA API](https://vpic.nhtsa.dot.gov/api/) (zero-auth) | Checks open recalls by VIN or make/model/year. Rates severity from keywords (critical/high/medium/low). |
| **Route Weather Scanner** | `agents/weather_agent.py` | [Open-Meteo](https://open-meteo.com/) (zero-auth) | Geocodes locations, forecasts temp/precip/wind/visibility, flags hazards per segment. |
| **Trip Advisor** | `agents/trip_advisor.py` | (no API — pure logic) | Compiles vehicle + weather data, generates overall rating and actionable verdict. |

### Coordinator

`coordinator.py` runs the three agents sequentially and passes their outputs to the CLI renderer. Each agent is stateless — all state lives in the dataclass models.

## Output Example

```
╔══════════════════════════════════════════════════════╗
║  ⚠️  1 critical/high-severity recall(s) — address   ║
║      before driving                                 ║
╚══════════════════════════════════════════════════════╝

┌────────────────────── 🚗 Vehicle: 2019 HONDA CIVIC ──────────────────────┐
│ Open Recalls                                                              │
│ ID        │ Component  │ Severity │ Summary                │ Remedy      │
│ 24V-001   │ Air Bags   │ CRITICAL │ Front passenger ...    │ Replace ... │
└──────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────── Route Weather ──────────────────────────────┐
│ Location   │ Temp     │ Conditions │ Wind           │ Visibility │ Hazard │
│ Chicago    │ 8°C      │ Rain       │ 25 km/h        │ 8.0 km     │ ✅     │
│ Nashville  │ 12°C     │ Clear      │ 10 km/h        │ 16.0 km    │ ✅     │
│ Miami      │ 28°C     │ Storm      │ 65 km/h        │ 2.0 km     │ ⚠️     │
└──────────────────────────────────────────────────────────────────────────┘

✅ All clear — safe to drive!
```

## API Keys

**None required.** All APIs are free and require zero authentication:
- [NHTSA Vehicle Recalls](https://vpic.nhtsa.dot.gov/api/) — unlimited, no API key
- [Open-Meteo Weather](https://open-meteo.com/) — unlimited, no API key
- [Open-Meteo Geocoding](https://open-meteo.com/en/docs/geocoding-api) — unlimited, no API key

## Tests

```bash
cd saferide
python -m pytest tests/ -v
```

14 tests covering:
- Vehicle recall severity classification
- NHTSA API error handling with simulated fallback
- Empty recall results → clear status
- Weather condition classification (clear/rain/fog/snow/storm)
- Hazard detection (precipitation, wind gusts, visibility)
- Geocoding API error fallback
- Overall route rating (good/caution/avoid)
- Full report compilation

## Files

| File | Purpose |
|------|---------|
| `__main__.py` | CLI entry point (argparse + interactive mode) |
| `coordinator.py` | Orchestrates all three agents |
| `models.py` | Shared dataclass definitions |
| `agents/vehicle_agent.py` | NHTSA recall checker |
| `agents/weather_agent.py` | Geocoding + weather forecast |
| `agents/trip_advisor.py` | Report compilation and verdict |
| `tests/test_vehicle_agent.py` | Vehicle agent tests (5) |
| `tests/test_weather_agent.py` | Weather agent tests (5) |
| `tests/test_trip_advisor.py` | Trip advisor tests (4) |

## Related

- [NHTSA API Docs](https://vpic.nhtsa.dot.gov/api/)
- [Open-Meteo Weather API](https://open-meteo.com/en/docs)
- [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)