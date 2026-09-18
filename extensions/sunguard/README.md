# SunGuard ☀️

**Answers "Do I need sunscreen today?"** — a UV / sun / heat / air quality safety MCP server for everyday people.

## What it does

SunGuard combines real-time weather data with the Fitzpatrick skin typing system to give personalized outdoor safety advice. It answers questions like:

- "Do I need sunscreen today in Portland?"
- "How long until I burn with type II skin at UV 7?"
- "Is it safe to take the kids to the beach at 2pm?"
- "What's the air quality in Austin?"

## Tools

| Tool | Description |
|------|-------------|
| `sun_safety(zip_or_city)` | Combined UV + heat + AQI verdict for today |
| `hourly_uv(lat, lon, date)` | UV index hour-by-hour for a specific date |
| `skin_burn_time(skin_type, uv_index)` | How long until sunburn (Fitzpatrick I-VI) |
| `heat_safety(zip_or_city)` | Heat index + heat advisory check |
| `air_quality_check(zip_or_city)` | AQI with activity recommendations |
| `outdoor_plan(zip_or_city, activity, time)` | Safety assessment for an outdoor activity |

## Quick start

```bash
# Install
pip install -r requirements.txt

# Run as MCP server
mcp run sunguard/server.py

# Or directly
python -m sunguard.server
```

## Data sources

- **Open-Meteo Weather**: UV index, temperature forecasts (free, zero-auth)
- **Open-Meteo Air Quality**: European AQI (free, zero-auth)
- **Open-Meteo Geocoding**: ZIP → lat/lon resolution (free, zero-auth)
- **NWS Weather Alerts**: US heat advisories (free, zero-auth)

All APIs are free and require no API keys.

## Design

- **Simulated fallback**: If any API call fails, the server gracefully returns plausible simulated data — always demoable
- **Testability**: Module-level `set_client()` pattern for injecting mock httpx clients
- **Pydantic models**: Structured return types for AI agent iteration
- **One tool per operation**: Clean separation, not one giant tool