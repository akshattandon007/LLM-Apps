# Flow.md — Pack Light

## Architecture Overview

```
┌─────────────┐     ┌─────────────────┐     ┌──────────────┐     ┌──────────────────┐
│  __main__.py │────▶│    cli.py       │────▶│  weather.py   │────▶│ Open-Meteo API  │
│  (entry)     │     │  build_parser() │     │  geocode()    │     │ (external)       │
│              │     │  main()         │     │  get_forecast()│    │                  │
└─────────────┘     └────────┬────────┘     └───────┬──────┘     └──────────────────┘
                             │                       │
                             │                       │
                             ▼                       ▼
                      ┌──────────────┐      ┌─────────────────┐
                      │  packer.py    │      │ DayWeather      │
                      │ PackingEngine │◀─────│ (dataclass)     │
                      │  _aggregate() │      └─────────────────┘
                      │  generate()   │
                      └──────┬───────┘
                             │
                             ▼
                      ┌──────────────┐
                      │  rules.yaml   │
                      │  (user-editable config)
                      └──────────────┘
```

## Execution Trace

### Path 1: `python -m packlight "Tokyo" --from 2026-10-15 --to 2026-10-20`

```
1. __main__.py → cli.main()
2. cli.main()
   ├── build_parser() → argparse.ArgumentParser
   ├── args = parser.parse_args(["Tokyo", "--from", "2026-10-15", "--to", "2026-10-20"])
   │
   ├── WeatherClient().geocode("Tokyo")
   │   ├── requests.get(geocoding-url, params={"name": "Tokyo", ...})
   │   ├── parse JSON response → extract lat, lon, resolved_name
   │   └── return (35.6762, 139.6503, "Tokyo, Japan (Tōkyō)")
   │
   ├── WeatherClient().get_forecast(35.68, 139.65, date(2026,10,15), date(2026,10,20))
   │   ├── requests.get(forecast-url, params={latitude, longitude, daily params})
   │   ├── parse JSON → build list of DayWeather objects
   │   └── return [DayWeather(...), DayWeather(...), ...]  # 6 days
   │
   ├── PackingEngine(rules_path)
   │   ├── _load_rules() → parses rules.yaml via pyyaml
   │   └── store rules in self._rules list
   │
   ├── engine.generate(daily_weather)
   │   ├── _aggregate(days) → compute trip-level stats
   │   │   ├── max_temp, min_temp, avg temps
   │   │   ├── total_precip, rain_days
   │   │   ├── max_wind, avg_wind
   │   │   ├── max_uv, min_daylight
   │   │   ├── snow_any, thunder_any, fog_any
   │   │   └── trip_days
   │   │
   │   ├── for each rule in self._rules:
   │   │   ├── _evaluate_rule(rule, agg) → true/false per condition
   │   │   └── if true: PackItem(category, item, reason) → selected list
   │   │
   │   └── return [PackItem(...), ...]
   │
   └── render output (list format):
       ├── group items by category
       ├── print "═══ CATEGORY ═══"
       ├── print "  ☐ item1"
       ├── print "  ☐ item2"
       └── print summary line
```

### Path 2: `python -m packlight --lat 48.85 --lon 2.35 -d 5` (Paris, winter)

```
1. __main__.py → cli.main()
2. cli.main()
   ├── No city → lat=48.85, lon=2.35 from args
   ├── No --from → date_from = today
   ├── No --to → date_to = today + 4 days (from -d 5)
   │
   ├── WeatherClient().get_forecast(48.85, 2.35, today, today+4)
   │   └── returns [DayWeather(...)]  # 5 days, likely cold/rainy
   │
   ├── PackingEngine().generate(daily)
   │   ├── Cold rules fire: warm coat, gloves, beanie, scarf
   │   ├── Rain rules fire: umbrella, raincoat
   │   ├── Baseline rules fire: phone charger, passport, toiletries
   │   └── returns ~15 items across 5 categories
   │
   └── render output (list format with checkboxes)
```

### Path 3: Geocode failure (e.g. `python -m packlight "Atlantis"`)

```
1. WeatherClient().geocode("Atlantis")
2. requests.get() → API returns {"results": []}
3. raise GeocodeError("No results for 'Atlantis'")
4. cli.main() catches → print error → return 1
```

### Path 4: Network failure (no internet)

```
1. WeatherClient().get_forecast(...)
2. requests.get() → raises ConnectionError / Timeout
3. raise ForecastError("API error: ...")
4. cli.main() catches → print error → return 1
```

## Module Dependency Graph

```
packlight
├── packlight/
│   ├── __init__.py       (version string, no deps)
│   ├── __main__.py       [depends on: cli]
│   ├── cli.py            [depends on: weather, packer]
│   │   ├── weather.py    [depends on: requests (external), datetime]
│   │   └── packer.py     [depends on: yaml (external), weather.DayWeather]
│   └── ...
├── rules.yaml            (data file, no deps)
├── tests/
│   ├── __init__.py
│   └── test_packlight.py [depends on: weather, packer, pytest, yaml]
├── requirements.txt
├── Decisions.md
└── Flow.md
```

## Key Data Flow

```
User input (city + dates)
        │
        ▼
Parse args ─────────────────────────────┐
        │                               │
        ▼                               │
Geocode city ──→ (lat, lon)             │
        │                               │
        ▼                               ▼
Fetch 16-day forecast ──→ list of DayWeather objects
        │                               │
        ▼                               │
Filter to trip dates ──→ daily[DayWeather, ...]
        │
        ▼
Aggregate weather ──→ agg dict (max_temp, total_precip, ...)
        │
        ▼
Evaluate rules ──→ list of PackItem (category, item, reason)
        │
        ▼
Group by category ──→ render checklist
        │
        ▼
User sees: "═══ CLOTHING ═══\n  ☐ T-shirts / short sleeves\n  ☐ Light jacket / hoodie\n..."
```

## File-Level Call Chain

```
__main__.py::main()
  └── cli.py::main(argv)
        ├── (argparse) build_parser()
        ├── weather.WeatherClient.__init__()
        ├── weather.WeatherClient.geocode(city)
        │     └── requests.get(geocoding-url)
        ├── weather.WeatherClient.get_forecast(lat, lon, date_from, date_to)
        │     └── requests.get(forecast-url)
        ├── packer.PackingEngine.__init__(rules_path)
        │     └── self._load_rules()
        │           └── yaml.safe_load(file)
        ├── packer.PackingEngine.generate(daily)
        │     ├── self._aggregate(days)
        │     └── self._evaluate_rule(rule, agg)  [× N rules]
        └── print output (grouped packing list)
```