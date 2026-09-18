# SunGuard Execution Flow

## CLI Entry → Module Dependency Graph

```
python -m sunguard.server
         │
         ▼
    sunguard/server.py::main()
         │
         ▼
    mcp.run()
```

```
mcp run sunguard/server.py
         │
         ▼
    MCP SDK loads FastMCP("SunGuard", ...)
         │
         ▼
    Registers tools as @mcp.tool() handlers
         │
         ▼
    Listens on stdio transport for JSON-RPC requests
```

## Module Dependency Graph

```
server.py ──→ weather.py ──→ httpx (external)
    │               │
    │               └──→ Open-Meteo API (external)
    │               └──→ NWS API (external)
    │               └──→ math (stdlib, heat index)
    │
    └──→ models.py (Pydantic models, no external deps)
```

**Dependency direction**: `server.py → weather.py` and `server.py → models.py`. `weather.py` has no dependency on `server.py` or `models.py`.

---

## Tool Call Chains

### `sun_safety(zip_or_city)`

```
sun_safety(zip_or_city)
  │
  ├─→ _resolve_location(zip_or_city)
  │     └─→ weather.geocode(zip_or_city)
  │           ├─→ httpx GET geocoding-api.open-meteo.com/v1/search
  │           │     (on failure → _simulate_geocode → Portland)
  │           └─→ returns GeocodeResult(name, lat, lon, country)
  │
  ├─→ weather.get_uv_forecast(lat, lon)
  │     ├─→ httpx GET api.open-meteo.com/v1/forecast (hourly=uv_index, daily=uv_index_max,temperature_2m_max)
  │     │     (on failure → _simulate_uv_forecast → UV 6.5, temp 30°C)
  │     └─→ returns UVForecast(max_uv, hourly_uv, max_temp)
  │
  ├─→ weather.get_air_quality(lat, lon)
  │     ├─→ httpx GET air-quality-api.open-meteo.com/v1/air-quality (hourly=european_aqi)
  │     │     (on failure → _simulate_air_quality → AQI 50)
  │     └─→ returns AirQualityData(aqi, hourly_values)
  │
  ├─→ weather.get_heat_advisories(lat, lon)
  │     ├─→ httpx GET api.weather.gov/alerts/active?point={lat},{lon}
  │     │     (on failure → returns [])
  │     └─→ returns list[NWSAlert]
  │
  ├─→ weather.calculate_heat_index(temp_c, humidity=50%)
  │     └─→ Rothfusz regression → heat index °C
  │
  ├─→ weather.uv_risk_level(uv)          → "high"
  ├─→ weather.heat_index_risk(hi)        → "very_high"
  ├─→ weather.aqi_risk_level(aqi)        → "low"
  ├─→ weather.overall_risk(uv, heat, aqi) → "very_high"
  │
  └─→ returns SunSafetyResult(location, uv_index, uv_risk, temperature,
                               heat_index, heat_risk, aqi, aqi_risk,
                               overall_risk, recommendation, source)
```

### `hourly_uv(lat, lon, date)`

```
hourly_uv(lat, lon, date)
  │
  ├─→ weather.get_uv_forecast(lat, lon)
  │     └─→ (same as above)
  │
  ├─→ max(uv.hourly_uv, key=λh["uv_index"]) → peak hour
  │
  └─→ returns HourlyUVResult(location, date, hours, peak_uv, peak_hour, source)
```

### `skin_burn_time(skin_type, uv_index)`

```
skin_burn_time(skin_type, uv_index)
  │
  ├─→ weather.calculate_burn_time(skin_type, uv_index)
  │     ├─→ Lookup Fitzpatrick map → base time
  │     ├─→ Scale: base * (3.0 / uv_index)  [clamped 0.25-3.0]
  │     └─→ returns (burn_time_minutes, description)
  │
  └─→ returns BurnTimeResult(skin_type, uv_index, burn_time_minutes, description, recommendation)
```

### `heat_safety(zip_or_city)`

```
heat_safety(zip_or_city)
  │
  ├─→ _resolve_location(zip_or_city)
  │     └─→ weather.geocode(...)
  │
  ├─→ weather.get_uv_forecast(lat, lon)   → UVForecast (need max_temp)
  ├─→ weather.calculate_heat_index(temp_c) → heat index °C
  ├─→ weather.heat_index_risk(hi)          → risk level
  ├─→ weather.get_heat_advisories(lat, lon) → list[NWSAlert]
  │
  └─→ returns HeatSafetyResult(location, temperature, heat_index, heat_index_risk, advisories, recommendation, source)
```

### `air_quality_check(zip_or_city)`

```
air_quality_check(zip_or_city)
  │
  ├─→ _resolve_location(zip_or_city)
  │     └─→ weather.geocode(...)
  │
  ├─→ weather.get_air_quality(lat, lon)   → AirQualityData
  ├─→ weather.aqi_risk_level(aqi)          → risk level
  │
  └─→ returns AirQualityResult(location, aqi, aqi_level, risk, recommendation, source)
```

### `outdoor_plan(zip_or_city, activity, time)`

```
outdoor_plan(zip_or_city, activity, time)
  │
  ├─→ _resolve_location(zip_or_city)
  │     └─→ weather.geocode(...)
  │
  ├─→ weather.get_uv_forecast(lat, lon)   → UVForecast (hourly + max_temp)
  ├─→ weather.get_air_quality(lat, lon)    → AirQualityData
  ├─→ weather.calculate_heat_index(temp_c) → heat index °C
  │
  ├─→ Parse hour from time string
  ├─→ Look up UV at that hour from hourly_uv[]
  │
  ├─→ weather.uv_risk_level(uv_at_time)
  ├─→ weather.heat_index_risk(hi)
  ├─→ weather.aqi_risk_level(aqi)
  │
  ├─→ Build concerns list (if any risk is elevated)
  ├─→ is_safe = (len(concerns) == 0)
  │
  └─→ returns OutdoorPlanResult(location, activity, time, uv_index,
                                 temperature, heat_index, aqi, is_safe,
                                 concerns, recommendation, source)
```

---

## Parallelism Note

Within each tool that calls multiple APIs (e.g., `sun_safety`, `outdoor_plan`), the API calls are **serialized** in the current implementation because `httpx.Client` is synchronous. If parallelism were needed, the calls could be wrapped in `concurrent.futures.ThreadPoolExecutor` — each API call is I/O-bound and would benefit.

Current execution order for multi-API tools:
1. `geocode()` — must happen first (lat/lon needed for all others)
2. `get_uv_forecast()` — fastest API, also provides temperature (needed for heat index)
3. `get_air_quality()` — independent of UV
4. `get_heat_advisories()` — independent of UV/AQ

Steps 2-4 could be parallelized; step 1 must remain serial.