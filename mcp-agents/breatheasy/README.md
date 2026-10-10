# breatheasy

> **Is it OK to go outside?** Air quality and pollen answers for any place on Earth — zero API keys, zero signup.

breatheasy answers plain-language questions about air quality and pollen
for any place on the planet. It ships two surfaces over one core:

- an **MCP server** (stdio) with four tools you can wire into Claude or any
  MCP client, and
- a **CLI** for humans and scripts.

All data comes from [Open-Meteo](https://open-meteo.com/)'s free weather
APIs — no key, no account, no rate-limit paperwork.

## Features

- 🌍 **Any place on Earth** — "Brooklyn", "Los Angeles", or raw coordinates `40.71,-74.01` (coordinates skip geocoding entirely).
- 🫁 **Current air quality** — US AQI, European AQI, top pollutant, EPA category, plain-language advice.
- 📈 **Forecasts** — daily max AQI trend (1–7 days) plus the worst hour today.
- 🌼 **Pollen** — alder, birch, grass, mugwort, olive, ragweed peaks with low/medium/high labels and one-line guidance; regions without pollen data say so gracefully.
- 🔥 **Wildfire smoke check** — honest alerts when AQI/PM2.5 is elevated enough to *possibly* include wildfire smoke (never a false claim of confirmed smoke).
- 🧩 **MCP server** — formatted Markdown tool output (no raw JSON), friendly error strings instead of exceptions.
- 🧪 **100% offline test suite** — fixtures + `httpx.MockTransport`, no network, no keys.

## Quick start

```bash
pip install -e .            # or: pip install -r requirements.txt

# CLI examples
breatheasy now "Brooklyn"
breatheasy forecast "Los Angeles" --days 3
breatheasy pollen "Chicago" --days 1
breatheasy now "40.71,-74.01"      # coordinates skip geocoding
breatheasy serve                   # MCP stdio server
```

`python -m breatheasy` works identically without installing:

```bash
cd breatheasy && python -m breatheasy now "Brooklyn"
```

### MCP client configuration

Point any MCP client at the stdio server. For Claude Desktop:

```json
{
  "mcpServers": {
    "breatheasy": {
      "command": "python",
      "args": ["-m", "breatheasy", "serve"]
    }
  }
}
```

If you installed the package (`pip install .`), you can use the console
script instead: `"command": "breatheasy", "args": ["serve"]`.

## MCP tool reference

| Tool | Params | Returns |
|---|---|---|
| `get_air_quality` | `place: str` | Markdown: US AQI (European fallback if missing), European AQI, top pollutant, EPA category + emoji, advice |
| `get_air_forecast` | `place: str`, `days: int = 3` (clamped 1–7) | Markdown: daily max AQI table, worst hour today, advice |
| `get_pollen_forecast` | `place: str`, `days: int = 1` (clamped 1–7) | Markdown: per-type pollen peak (P/m³), low/medium/high label, one-line guidance; `no data` for nulls |
| `get_wildfire_smoke_alert` | `place: str` | Markdown: clear, or elevated pollution that *may* include wildfire smoke (AQI ≥ 151 or PM2.5 ≥ 55.4 µg/m³) |

## How it works

`geo.resolve_place` turns free text into coordinates (or parses `lat,lon`
locally with zero network), `api.OpenMeteoClient` fetches current + hourly
air quality and pollen from Open-Meteo, and `advice` maps values to EPA AQI
bands and pollen buckets with plain-language text — all embedded offline.
See `Flow.md` for call chains and `Decisions.md` for the design rationale.

## Project layout

```
breatheasy/
├── __init__.py      version
├── __main__.py      python -m breatheasy → cli.main()
├── cli.py           argparse CLI (stdlib only)
├── server.py        FastMCP server, stdio transport, 4 tools
├── api.py           OpenMeteoClient (httpx) + payload helpers
├── geo.py           place / "lat,lon" → (lat, lon, label)
└── advice.py        EPA AQI bands, pollen buckets, plain-language advice
tests/
├── fixtures/        real Open-Meteo samples + synthetic pollen sample
├── test_advice.py   band boundaries, pollen buckets, top pollutant
├── test_api.py      client parsing, params, null handling
├── test_geo.py      coords fast path, geocode success/failure
├── test_cli.py      output content and exit codes (capsys)
└── test_server.py   tool registration + behavior (MockTransport)
```

## Development

```bash
python -m pytest tests/ -v
```

The suite is fully offline: HTTP is mocked with `httpx.MockTransport` and
CLI output is captured with `capsys`.

## Disclaimer

breatheasy provides **indicative, non-clinical guidance**. AQI bands follow
the US EPA; pollen buckets are a rough heuristic (Open-Meteo pollen is NULL
outside Europe and pollen season). This is not medical advice — people with
asthma, allergies, or heart/lung conditions should follow their healthcare
provider's guidance and local official alerts.