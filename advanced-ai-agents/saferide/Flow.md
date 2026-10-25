# Flow — SafeRide

## Execution trace from CLI entry to final report

### Entry point

```
__main__.py:main()
  │
  ├── Parse CLI args (argparse)
  │     ├── make, model, year, origin, destination (positional)
  │     ├── --vin (optional, overrides make/model/year)
  │     ├── -w/--waypoints (optional list)
  │     └── Interactive mode if any positional arg missing
  │
  └── coordinator.run_full_check(make, model, year, origin, destination, waypoints, vin)
```

### Multi-agent pipeline (`coordinator.py`)

```
coordinator.run_full_check()
  │
  ├── Agent 1: Vehicle Safety Scout
  │     │
  │     ├── if vin:
  │     │     └── vehicle_agent.check_by_vin(vin)
  │     │           ├── GET https://api.nhtsa.gov/recalls/recallsByVehicle?vin=<VIN>
  │     │           ├── Parse response → list[Recall] with _rate_recall_severity()
  │     │           └── Return VehicleCheck (status: clear/recall_found/error)
  │     │
  │     └── else:
  │           └── vehicle_agent.check_by_ymm(make, model, year)
  │                 ├── GET https://api.nhtsa.gov/recalls/recallsByVehicle?make=&model=&modelYear=
  │                 ├── Parse response → list[Recall]
  │                 └── Return VehicleCheck
  │
  ├── Agent 2: Route Weather Scanner
  │     │
  │     └── weather_agent.get_route_forecast(origin, destination, waypoints)
  │           │
  │           ├── weather_agent.geocode(location)  × (origin + destination + each waypoint)
  │           │     └── GET https://geocoding-api.open-meteo.com/v1/search?name=<location>
  │           │           → Waypoint(name, lat, lon) or fallback coordinates
  │           │
  │           ├── weather_agent.get_forecast(lat, lon, name)  × (origin + destination + each waypoint)
  │           │     └── GET https://api.open-meteo.com/v1/forecast?latitude=&longitude=&current=...
  │           │           ├── _classify_condition(precip, wind, vis, temp) → str
  │           │           ├── _assess_hazard(precip, wind, gust, vis, condition) → (bool, str)
  │           │           └── Return SegmentForecast (temp, condition, hazard, etc.)
  │           │
  │           └── Return (origin_fc, dest_fc, list[waypoint_fcs])
  │
  └── Agent 3: Trip Advisor
        │
        └── trip_advisor.build_report(vehicle, origin_fc, dest_fc, waypoint_fcs, ...)
              ├── Construct RouteWeather from all forecasts
              ├── _overall_weather_rating(weather) → "good"|"moderate"|"caution"|"avoid"
              ├── _build_weather_summary(weather) → formatted string
              ├── _build_verdict(vehicle, weather) → "All clear" or "Issues found"
              └── Return TripReport(vehicle, weather, summary, verdict)
```

### CLI rendering (`__main__.py:_print_report`)

```
_print_report(report)
  │
  ├── Panel: Verdict (green/yellow)
  ├── Panel: Vehicle section
  │     ├── Green box if clear, or
  │     └── Table of open recalls (ID, Component, Severity, Summary, Remedy)
  ├── Panel: Weather section
  │     ├── Table with row per location
  │     └── Temp, Conditions, Wind, Visibility, Hazard flags
  └── Panel: Final verdict
```

### Module dependency graph

```
__main__.py
  └── coordinator
        ├── agents/vehicle_agent
        │     ├── httpx
        │     └── models (VehicleCheck, Recall)
        ├── agents/weather_agent
        │     ├── httpx
        │     └── models (SegmentForecast, Waypoint)
        └── agents/trip_advisor
              └── models (RouteWeather, TripReport, etc.)
```

### Data flow

```
User Input (VIN / Make+Model+Year + Origin + Destination + Waypoints)
  │
  ▼
[Vehicle Safety Agent] ──→ VehicleCheck {vin, make, model, recalls[]}
  │                           ↑ source: "live" | "simulated"
  │
  ▼
[Weather Agent (geocode)] ──→ Waypoint {name, lat, lon}  × N
  │
  ▼
[Weather Agent (forecast)] ──→ SegmentForecast {temp, precip, wind, condition, hazard}  × N
  │                             ↑ source: "live" | "simulated"
  │
  ▼
[Trip Advisor] ──→ RouteWeather {origin, destination, waypoints, hazards}
  │                 TripReport {vehicle, weather, verdict}
  │
  ▼
[CLI Render] ──→ Rich panels + tables → Terminal
```

### Error handling

| Failure | Agent | Behavior |
|---------|-------|----------|
| NHTSA API 500 / timeout | Vehicle | Caught by try/except → `status: "error"` with message |
| NHTSA returns empty | Vehicle | `status: "clear"` — no news is good news |
| Open-Meteo geocoding fails | Weather | Returns fallback coords (NYC/LA) for popular routes |
| Open-Meteo forecast fails | Weather | Returns simulated forecast (`source: "simulated"`) |
| Trip Report construction | Advisor | Always succeeds (all inputs are pre-validated by models) |