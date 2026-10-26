# ⛽ fuel-tracker

**Find the cheapest fuel near you — through your AI assistant.**

fuel-tracker is an **MCP server** that wraps the free [FuelWide API](https://fuelwide.com/fuel-prices-api) so any MCP-capable AI client (Claude, Cursor, etc.) can look up live fuel prices by country and find nearby stations with prices.

## ✨ Features

- **🌍 National averages** — Get the latest petrol (95), diesel and LPG prices for 28+ countries
- **🔍 Country detail** — Drill into a specific country's fuel price data with full provenance
- **📍 Nearby stations** — Find stations sorted by price near any location (IT, ES, FR, AU)
- **🔌 MCP native** — Drop into any MCP host as a stdio server
- **🚫 No API key** — Zero registration, zero auth, zero cost

## 🚀 Quick Start

### 1. Install

```bash
pip install mcp httpx
git clone <repo-url>  # or copy the fuel-tracker/ directory
cd fuel-tracker
```

### 2. Configure your MCP host

Add to your MCP client config (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "fuel-tracker": {
      "command": "python",
      "args": ["-m", "fuel_tracker.server"],
      "cwd": "/absolute/path/to/fuel-tracker"
    }
  }
}
```

Or run it directly:

```bash
python -m fuel_tracker.server
```

### 3. Ask your AI

Once connected, ask your AI:

- *"What are fuel prices in Germany right now?"*
- *"Find cheap diesel stations near 52.52, 13.405 in Berlin"*
- *"Compare petrol prices across Europe"*

## 🛠️ Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_fuel_prices` | National average prices for all countries | *(none)* |
| `get_country_fuel_prices` | Detailed prices for one country | `country_code` (str, ISO alpha-2) |
| `get_nearby_stations` | Station-level prices near a location | `country`, `lat`, `lon`, `radius_km`, `fuel_type` |

## 📡 Data Source

All data comes from [FuelWide](https://fuelwide.com/) which aggregates fuel prices from 28+ national authorities (EIA/AAA for USA, UK government for UK, etc.). The API is free, open, and requires no key. Attribution is required — see each response's `attribution` field.

## 🧪 Tests

```bash
cd fuel-tracker
pip install pytest
python -m pytest tests/ -v
```

## 📁 Project Structure

```
fuel-tracker/
├── fuel_tracker/
│   ├── __init__.py
│   └── server.py          # MCP server + tools
├── tests/
│   ├── __init__.py
│   └── test_server.py     # 7 unit tests
├── pyproject.toml
├── requirements.txt
├── README.md
├── Decisions.md
└── Flow.md
```

## 📜 License

Code: MIT. Data: see the attribution in each API response — credit the original data publishers, not just FuelWide.