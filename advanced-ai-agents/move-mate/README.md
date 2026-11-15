# 📦 MoveMate — Multi-Agent Relocation Assistant

**Turn moving chaos into a clear, actionable playbook.** MoveMate coordinates 5 specialized AI agents — Utility Scheduler, Address Changer, Cost Estimator, Neighborhood Scout, and Timeline Architect — to build a complete relocation plan from just a few inputs. No API keys, no signup, no fuss.

## 🚀 What It Does

Tell MoveMate your current ZIP, new ZIP, move date, and household size. In seconds, 5 agents collaborate to produce a comprehensive relocation playbook covering:

- ⚡ **Utility Setup & Cancellation** — Electric, gas, water, internet, trash
- 📬 **Address Change Checklist** — Government, financial, subscriptions, insurance
- 💰 **Cost Estimate** — Truck rental, supplies, movers, deposits with buffer
- 🏘️ **Neighborhood Snapshot** — Amenities, transit, groceries, parks via OpenStreetMap
- 📅 **Moving Timeline** — Week-by-week from 8 weeks before to 2 weeks after

## 📋 Requirements

- Python 3.9+
- No external packages needed — uses only the standard library

## 🔧 Quick Start

```bash
# Clone the repo
cd advanced-ai-agents/move-mate/

# Run in interactive mode
python main.py --interactive

# Or pass everything as CLI args
python main.py --current-zip 10001 --new-zip 90210 --move-date 2025-12-15 --household-size 2br --renting

# Save output to a file
python main.py --current-zip 10001 --new-zip 90210 --move-date 2025-12-15 --household-size 1br -o my-playbook.md
```

## 🎮 Usage Modes

### Interactive Mode
```bash
python main.py -i
```
Walks you through each input with prompts and validation.

### CLI Mode
| Flag | Description | Required |
|------|-------------|----------|
| `--current-zip` | Current ZIP code | Yes (CLI mode) |
| `--new-zip` | New ZIP code | Yes (CLI mode) |
| `--move-date` | Move date (YYYY-MM-DD) | Yes (CLI mode) |
| `--household-size` | `studio`, `1br`, `2br`, `3br`, or `house` | Yes |
| `--renting` | Flag if renting (vs owning) | No |
| `-o / --output` | Save playbook to file | No |

## 🧪 Running Tests

```bash
python -m pytest tests/ -v
```

## 🏗️ Architecture

```
main.py              → CLI entry point
orchestrator.py      → Central coordinator — runs all 5 agents
agents/
  utility_scheduler.py  → Agent 1: Utility recommendations
  address_changer.py    → Agent 2: Address change checklist
  cost_estimator.py     → Agent 3: Cost estimate
  neighborhood_scout.py → Agent 4: Neighborhood research (OSM + Wikipedia)
  timeline_architect.py → Agent 5: Moving timeline
models.py            → Data models (MoveDetails, Playbook, etc.)
utils.py             → Free API helpers (Nominatim, Open-Meteo, Wikipedia)
tests/               → Pytest test suite
```

## 🌐 Free APIs Used

- **OpenStreetMap / Nominatim** — Geocoding and reverse geocoding
- **Overpass API** — Nearby amenities search
- **Open-Meteo** — Weather forecast (7-day)
- **Open-Meteo Geocoding** — City → coordinates
- **Wikipedia REST API** — Neighborhood/city summaries

All are free, open, and require no API keys or registration.

## ⚖️ License

MIT — build on it, fork it, make moving less terrible.