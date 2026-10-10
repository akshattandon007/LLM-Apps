# breatheasy — Flow

Function-level call chains, module dependency graph, and data flow.
Entry surfaces: the argparse CLI (`cli.py`) and the FastMCP server
(`server.py`); both sit on the same core (`geo.py`, `api.py`, `advice.py`).

## Module dependency graph

```
                        ┌───────────────────────┐
                        │      breatheasy       │
                        └───────────┬───────────┘
        ┌───────────────┬───────────┼───────────┬──────────────┐
        ▼               ▼           ▼           ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌────────┐ ┌──────────┐ ┌───────────┐
│    cli.py    │ │  server.py  │ │ geo.py │ │  api.py  │ │ advice.py │
│ argparse     │ │ FastMCP     │ │ resolve│ │ httpx    │ │ EPA bands │
│ (stdlib only)│ │ stdio + 4   │ │ place  │ │ client + │ │ pollen    │
└──────┬───────┘ │ tools       │ │ + coords│ │ helpers  │ │ buckets   │
       │         └──────┬──────┘ └───┬────┘ └────┬─────┘ └─────┬─────┘
       │  imports       │            │           │             │
       └────────────────┴────────────┴───────────┴─────────────┘
                                    │
                              ┌─────▼──────┐
                              │ Open-Meteo │  REST, no API key
                              │ (2 GETs)   │
                              └────────────┘
```

- `cli.py → server.py`: lazy import, only inside `cmd_serve` (keeps CLI
  startup light and free of the `mcp` dependency until needed).
- `api.py → advice.py`: uses `POLLEN_TYPES` for the hourly variable list.
- No other cross-imports; no cycles.

## Data flow

```
┌────────────┐   ┌────────────────┐   ┌─────────────────┐   ┌─────────────┐   ┌───────────────────┐
│ user input │──►│ geo.resolve_    │──►│ api.OpenMeteo   │──►│ advice.band │──►│ formatted output   │
│ "Brooklyn" │   │ place →         │   │ Client.air_     │   │ /bucket +   │   │ CLI: plain text   │
│ or         │   │ (lat, lon,      │   │ quality() →     │   │ top_pollu-  │   │ MCP: markdown     │
│ "40.71,… " │   │  label)         │   │ parsed payload  │   │ tant text   │   │ stderr: exit 1    │
└────────────┘   └────────────────┘   └─────────────────┘   └─────────────┘   └───────────────────┘
```

## CLI call chains

### `python -m breatheasy now "Brooklyn"`

```
__main__.main
└─ cli.main(argv)
   └─ build_parser()              # argparse subparsers: now/forecast/pollen/serve
   └─ cmd_now(args, client)
      ├─ geo.resolve_place("Brooklyn", client)
      │  ├─ geo.parse_coords(...)             # regex miss → continue
      │  └─ client.geocode("Brooklyn")        # GET /v1/search → [GeoResult]
      │     └─ GeoLookupError → stderr "Could not find place" → return 1
      ├─ client.air_quality(lat, lon, days=1) # GET /v1/air-quality
      │  └─ httpx error → stderr "Could not fetch" → return 1
      ├─ advice.aqi_band(us_aqi or european_aqi)  # EPA band (cat/emoji/advice)
      ├─ advice.top_pollutant(current)             # pm2_5 vs pm10 vs ozone
      └─ print(...)                           # plain text, exit 0
```

### `python -m breatheasy forecast "Los Angeles" --days 3`

```
cli.main → cmd_forecast(args, client)
   ├─ days = clamp(args.days, 1, 7)
   ├─ geo.resolve_place(...)                  # as above
   ├─ client.air_quality(lat, lon, days=days) # forecast_days=days
   ├─ api.daily_max_aqi(hourly)              → [(date, max), ...]  (US→EU fallback)
   ├─ api.today_from_payload(data)            # "today" from current.time
   ├─ api.worst_hour_today(hourly, today)    → (HH:MM, aqi) | None
   ├─ advice.aqi_band(...)                    # per day + overall worst
   └─ print(table + worst hour + advice)
```

### `python -m breatheasy pollen "Chicago" --days 1`

```
cli.main → cmd_pollen(args, client)
   ├─ days = clamp(args.days, 1, 7)
   ├─ geo.resolve_place(...)
   ├─ client.air_quality(lat, lon, days=days) # pollen vars ride in hourly
   ├─ api.pollen_peak_per_type(hourly)        # {type: peak}, {} if all NULL
   ├─ advice.pollen_bucket(peak)              # none/low/medium/high
   └─ print(per-type rows or "No pollen data…")
```

### `python -m breatheasy serve`

```
cli.main → (args.command == "serve")
   └─ from .server import mcp      # lazy import
      └─ mcp.run()                 # FastMCP stdio transport, blocks on stdin
```

## MCP server call chain (all four tools)

```
mcp.run()  [stdio JSON-RPC]
└─ FastMCP dispatches tool by name
   └─ get_air_quality(place)  |  get_air_forecast(place, days)
      |  get_pollen_forecast(place, days)  |  get_wildfire_smoke_alert(place)
      ├─ server.get_client()                    # lazy singleton (test hook)
      ├─ server._resolve_or_error(client, place)
      │    └─ geo.resolve_place(...)
      │         ├─ parse_coords → (lat, lon, label)         # fast path
      │         └─ client.geocode(...) → results[0]         # 1st = most relevant
      │             └─ GeoLookupError → "😕 Could not find '…'" (no raise)
      ├─ client.air_quality(lat, lon, days=clamped)
      │    └─ api._get_json(url, params) → httpx.Client.get → resp.json()
      │        └─ any httpx/parse error → "⚠️ Could not fetch …" (no raise)
      ├─ advice.* + api helpers (daily_max_aqi, worst_hour_today,
      │    pollen_peak_per_type, top_pollutant)
      └─ format_*_() → returns Markdown string → JSON-RPC result
```

## Geocoding fallback chain

```
resolve_place(text, client)
  1. parse_coords(text) matches "lat,lon"?
        YES → (lat, lon, "40.7100, -74.0100")      ← zero network
        NO  → 2
  2. client.geocode(text)  (GET /v1/search, count=5)
        results non-empty → results[0] → (lat, lon, "Name, Admin1, Country")
        empty → raise GeoLookupError
            in tool → "😕 Could not find 'X' — try …, or 'lat,lon'."
            in CLI  → stderr + exit code 1
```

## Error paths

| Condition | MCP tool (returns string) | CLI |
|---|---|---|
| Unknown place | `😕 **Could not find 'X'** …` | stderr `Could not find place: …` → exit 1 |
| Geocoding API 4xx/5xx / timeout | `⚠️ Could not fetch location data for 'X'` | stderr `Could not fetch …` → exit 1 |
| Air-quality API 4xx/5xx / network timeout | `⚠️ Could not fetch … for {label}` | stderr `Could not fetch …` → exit 1 |
| `us_aqi` NULL, EU present | labeled EU fallback in `**European AQI (US AQI not reported)**` | `European AQI: 60` label |
| Both AQI NULL | `No current air quality data` | stdout message, exit 0 |
| Pollen all NULL / missing | per-type `no data 🚫` rows / wholesale message | `No pollen data for this region/season` |
| Empty hourly AQI | `No air quality forecast data` | stdout message, exit 0 |
| `days` out of range | clamped 1–7 before any request | clamped 1–7 before any request |
| Wildfire: AQI ≥ 151 or PM2.5 ≥ 55.4 | `Elevated pollution … may include wildfire smoke` | CLI has no wildfire command (tool only) |