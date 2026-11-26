# Recall Alert 🚨⚠️

**Know if your food, drugs, or car has been recalled — instantly.**

Recall Alert is an MCP (Model Context Protocol) server that checks product safety recalls from **openFDA** (food, drugs, medical devices, cosmetics) and **NHTSA** (vehicle safety recalls). Just tell it a product name or your car's VIN — it does the rest.

## Why?

Every week there are recalls on baby products, food, cars, appliances — and most people never hear about them. Instead of bookmarking government websites and checking manually, let an AI agent check for you.

## Features

- 🥜 **Food/Drug Recall Search** — search by product name against openFDA enforcement records
- 🚗 **Vehicle Recall by VIN** — check any 17-character VIN against NHTSA safety recalls
- ⚡ Clean, formatted output — classification, date, description, and remedy information
- 🧪 Fully tested with hermetic mock clients (no network required)

## Installation

```bash
# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run as an MCP server

```bash
# Standard mode
mcp run server.py

# Or as a direct Python script
python server.py
```

### Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `check_food_recall` | Search FDA recalls by product name | `product_name` (str), `limit` (int, default 10) |
| `check_vehicle_recall` | Check NHTSA recalls by VIN | `vin` (str, 17 chars) |

### Example queries (what an AI agent would ask)

- *"Is there a recall on Jif peanut butter?"*
- *"Check if my Honda Civic 2022 VIN has any open recalls"*
- *"Are there any recalls for infant formula right now?"*
- *"Look up recalls for Crest toothpaste"*

## How It Works

```
User/AI Agent
     │
     ▼
  MCP Tool (check_food_recall / check_vehicle_recall)
     │
     ├── openFDA API (no key needed) ──► Food/Drug/Device recalls
     │         GET /drug/enforcement.json?search=product_description:<query>
     │
     └── NHTSA API (no key needed) ──► Vehicle safety recalls
               GET /recalls/recallsByVehicle?vin=<17-char-VIN>
```

Both APIs are completely free and require **no API key**.

## Tests

```bash
pytest test_recall_alert.py -v
```

Tests use `httpx.MockTransport` to simulate API responses — no network calls required.

## Data Sources

| Source | Data | API Key | Rate Limit |
|--------|------|---------|------------|
| [openFDA](https://open.fda.gov/apis/drug/enforcement/) | Food, drug, medical device, cosmetic recalls | None | 240 req/min |
| [NHTSA](https://www.nhtsa.gov/partners/web-api) | Vehicle safety recalls by VIN | None | Unrestricted |

## License

MIT
