# 🔧 HomeFix — MCP Server for Home Service Professionals

> *Find, vet, and book home services without the headache.*

**HomeFix** is an MCP server that gives AI agents the tools to help users find licensed, well-reviewed home service professionals, compare quotes, verify licenses, estimate fair prices, and book appointments. When a pipe bursts at 9 PM or the HVAC dies in July, HomeFix has your back.

## MCP Tools

| Tool | Description |
|------|-------------|
| `find_pros(service_type, zip)` | Find licensed, available pros sorted by rating + proximity |
| `get_estimate(service, description, zip)` | Fair price range based on regional market data |
| `check_license(company, state)` | License/insurance/bond status verification |
| `summarize_reviews(professional)` | Review sentiment summary from mock data |
| `compare_quotes(description)` | Get estimates from 3+ matched providers |
| `emergency_services(zip)` | 24/7 plumbers, electricians, locksmiths |
| `book_appointment(pro, time_slot)` | Schedule the appointment with confirmation code |

## Service Types

| Service | Common Issues | Expected Range |
|---------|---------------|----------------|
| 🔧 Plumber | Burst pipe, clogged drain, water heater | $150–$2,000 |
| ⚡ Electrician | Outage, wiring, panel upgrade | $100–$3,000 |
| ❄️ HVAC | AC dead, furnace, thermostat | $150–$5,000 |
| 🛠️ Handyman | Assembly, drywall, painting | $50–$500 |
| 🔑 Locksmith | Locked out, rekey, new locks | $50–$300 |
| 🏗️ General Contractor | Renovation, roofing, structural | $500–$20,000+ |

## Usage

```bash
# Find plumbers in a zip code
python main.py find "plumber" "10001"

# Get an emergency service estimate
python main.py estimate "burst pipe" "10001"

# Check a company's license
python main.py license "Rapid Rooter" "NY"

# Start the MCP server
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

## Testing

```bash
pytest tests/ -v
```

## Project Files

| File | Purpose |
|------|---------|
| `Decisions.md` | Why every architectural choice was made |
| `Flow.md` | Execution trace through files and functions |
| `README.md` | Getting started guide |