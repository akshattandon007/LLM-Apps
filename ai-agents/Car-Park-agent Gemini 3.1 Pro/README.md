# 🅿️ ParkMate AI — UK Car Park Finder Agent

An AI-powered parking assistant that finds, compares, and books car parks across the UK. Built with **Google Gemini 3.1 Pro** (function-calling agent), **Google Maps Platform** (Geocoding + Routes + Places), and **UK parking booking platforms** (JustPark, YourParkingSpace, NCP).

> **"I'm leaving from Great Park in 30 mins, find me a car park by the time I reach Newcastle city centre"**
>
> The agent geocodes both locations, calculates a traffic-aware route, projects the arrival time, finds car parks with availability at that ETA, ranks them, and returns booking links — all autonomously through a multi-step tool-calling loop.

---

## Table of Contents

- [Demo](#demo)
- [Features](#features)
- [Architecture](#architecture)
- [Agent Workflow](#agent-workflow)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [How the Suitability Scoring Works](#how-the-suitability-scoring-works)
- [Booking Platforms](#booking-platforms)
- [Project Structure](#project-structure)
- [Model Fallback Chain](#model-fallback-chain)
- [Limitations and Future Work](#limitations-and-future-work)
- [License](#license)

---

## Demo

### Departure-based query (Mode A)

The user specifies where they're leaving from and when. The agent calculates the route, projects arrival, and finds parking available at that time.

```
🚗 You: I will be leaving from Great Park in 30 mins, suggest some car parks
         by the time I reach Newcastle city centre

  🤖 Using model: gemini-3.1-pro-preview-customtools
  🔧 Calling tool: geocode_destination({"destination": "Great Park Newcastle"})
  🔧 Calling tool: geocode_destination({"destination": "Newcastle city centre"})
  🔧 Calling tool: calculate_route({"origin_lat": 55.019, "origin_lng": -1.622,
      "destination_lat": 54.978, "destination_lng": -1.617,
      "departure_offset_minutes": 30, "travel_mode": "DRIVE"})
  🔧 Calling tool: search_nearby_car_parks({"lat": 54.978, "lng": -1.617})
  🔧 Calling tool: check_car_park_availability({"lat": 54.978,
      "arrival_datetime": "2026-03-24T17:12:00"})
  🔧 Calling tool: get_booking_link({"car_park_name": "Quayside Multi-Storey"...})
  🔧 Calling tool: get_booking_link({"car_park_name": "NCP Eldon Square"...})
  🔧 Calling tool: get_booking_link({"car_park_name": "NCP Dean Street"...})

╭─ 🅿️ ParkMate AI ──────────────────────────────────────────────────╮
│                                                                     │
│  🚗 Route: Great Park → Newcastle City Centre                       │
│  📏 Distance: 5.2 miles | ⏱️ Travel time: 22 min (traffic-aware)  │
│  🕐 Departing: 04:50 PM | 🏁 Arriving: 05:12 PM                   │
│                                                                     │
│  Here are your top 3 car parks, available at 5:12 PM:              │
│                                                                     │
│  🥇 Quayside Multi-Storey                                          │
│     📍 Broad Chare, NE1 3DQ — 0.4 miles from centre               │
│     🚗 280/630 spaces available                                     │
│     💷 £2.80/hr | ⚡ EV charging | Height: 2.2m ✅                 │
│     🔗 Book: https://www.justpark.com/search?q=...                 │
│                                                                     │
│  🥈 NCP Eldon Square                                                │
│     📍 Percy Street, NE1 7JB — 0.2 miles                          │
│     🚗 180/550 spaces available                                     │
│     💷 £3.80/hr | ⚡ EV charging | Height: 2.1m ✅                 │
│     🔗 Book: https://www.ncp.co.uk/find-a-car-park/...             │
│                                                                     │
│  🥉 NCP Dean Street                                                 │
│     📍 Dean Street, NE1 1PG — 0.3 miles                           │
│     🚗 95/420 spaces available                                      │
│     💷 £4.20/hr | ⚡ EV charging | Height: 2.0m ⚠️                │
│     🔗 Book: https://www.justpark.com/search?q=...                 │
│                                                                     │
│  💡 Tip: You're arriving during evening peak — I'd recommend       │
│  pre-booking Quayside for best value at £2.80/hr.                  │
╰─────────────────────────────────────────────────────────────────────╯
```

### Arrival-based query (Mode B)

```
🚗 You: Find a big car park for my Tesla near Newcastle city centre by 6:30pm
         with EV charging
```

---

## Features

- **Two query modes** — departure-based (origin + offset) and arrival-based (destination + time)
- **Traffic-aware routing** — Google Maps Routes API with `TRAFFIC_AWARE` computes real travel time and projects ETA
- **Smart car park discovery** — Google Maps Places API (New) finds parking within configurable radius
- **Real-time availability** — Parkopedia API (or curated fallback data) shows spaces at projected arrival time
- **Suitability scoring** — weighted algorithm ranks by proximity, availability, EV charging, price, capacity, and rating
- **Multi-platform booking** — generates pre-filled deep links for JustPark, YourParkingSpace, NCP, and Parkopedia
- **EV-aware** — detects Tesla/EV mentions, filters for chargers, flags height restrictions below 2.0m
- **Model fallback chain** — auto-selects best available Gemini model (3.1 Pro → 3 Flash → 2.5 Flash)
- **Rate limit resilience** — retries with exponential backoff on transient API errors
- **Rich CLI** — coloured output, live spinners, markdown rendering via Rich

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                            USER QUERY                                  │
│  "Leaving Great Park in 30 mins, find parking by the time I reach     │
│   Newcastle city centre" / "Big car park for my Tesla by 6:30pm"      │
└───────────────────────────┬────────────────────────────────────────────┘
                            │
                     ┌──────▼──────┐
                     │ Query type? │
                     └──┬──────┬───┘
            Has origin  │      │  Destination only
            + departure │      │
                        ▼      ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    GEMINI 3.1 PRO AGENT                                │
│     Model: gemini-3.1-pro-preview-customtools                         │
│     Function-calling loop · thinking_level=MEDIUM · max 12 iterations │
│                                                                        │
│  MODE A (Departure-based)          │  MODE B (Arrival-based)           │
│  ─────────────────────────         │  ─────────────────────            │
│  1. geocode(origin)                │  1. geocode(destination)          │
│  2. geocode(destination)           │  2. search_nearby_car_parks()     │
│  3. calculate_route()              │  3. check_availability()          │
│     → Google Maps Routes API       │  4. get_booking_link() × 3       │
│     → TRAFFIC_AWARE routing        │                                   │
│     → projects ETA                 │                                   │
│  4. search_nearby_car_parks()      │                                   │
│  5. check_availability(at ETA)     │                                   │
│  6. get_booking_link() × 3         │                                   │
│                                                                        │
│  5 Tool Functions:                                                     │
│  ┌────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │ geocode_destination()  │  │ calculate_route()                    │ │
│  │ Google Maps Geocoding  │  │ Google Maps Routes API (traffic)     │ │
│  └────────────────────────┘  └──────────────────────────────────────┘ │
│  ┌────────────────────────┐  ┌──────────────────────────────────────┐ │
│  │ search_nearby_car_     │  │ check_car_park_availability()        │ │
│  │ parks()                │  │ Parkopedia API v3 (+ fallback)       │ │
│  │ Google Maps Places     │  └──────────────────────────────────────┘ │
│  └────────────────────────┘  ┌──────────────────────────────────────┐ │
│                               │ get_booking_link()                   │ │
│                               │ JustPark / YourParkingSpace / NCP    │ │
│                               └──────────────────────────────────────┘ │
└───────────────────────────┬────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────────────────┐
│  🚗 ROUTE SUMMARY (Mode A only)                                       │
│     Origin → Destination | Distance | Travel time | ETA               │
│                                                                        │
│  🅿️ TOP 3 RECOMMENDATIONS                                            │
│     Name, address, distance | Spaces | Rate | EV | Height | Book     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Workflow

A step-by-step walkthrough of what happens when a user asks:

> *"I will be leaving from Great Park in 30 mins, suggest some car parks by the time I reach city centre"*

See [WORKFLOW.md](WORKFLOW.md) for the full annotated walkthrough with function signatures, parameters, and return data at each step.

**Summary:**

| Step | Tool | API Used | What Happens |
|------|------|----------|-------------|
| 0 | — | — | Gemini parses query → detects Mode A (origin + departure offset) |
| 1 | `geocode_destination` | Google Maps Geocoding | Resolves "Great Park Newcastle" → `55.019, -1.622` |
| 2 | `geocode_destination` | Google Maps Geocoding | Resolves "Newcastle city centre" → `54.978, -1.617` |
| 3 | `calculate_route` | Google Maps Routes API | Computes 5.2mi / 22min with traffic → ETA: 05:12 PM |
| 4 | `search_nearby_car_parks` | Google Maps Places (New) | Finds 7 car parks within 1.5km of destination |
| 5 | `check_car_park_availability` | Parkopedia (or fallback) | Checks spaces + pricing at the **projected 05:12 PM arrival** |
| 6 | `get_booking_link` ×3 | JustPark / YourParkingSpace / NCP | Generates pre-filled booking URLs for top 3 |
| 7 | — | — | Gemini synthesises route summary + 3 ranked recommendations |

**Total: 8 tool calls across 4 APIs in a single agent loop.**

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| AI Agent | Google Gemini 3.1 Pro | Multi-step function-calling with `thinking_level=MEDIUM` |
| Geocoding | Google Maps Geocoding API | Resolve place names to lat/lng coordinates |
| Routing | Google Maps Routes API | Traffic-aware travel time and ETA projection |
| Place Discovery | Google Maps Places API (New) | Find car parks within radius of destination |
| Availability | Parkopedia API v3 + fallback | Real-time spaces and pricing (optional) |
| Booking | JustPark / YourParkingSpace / NCP | Pre-filled deep link generation |
| CLI Interface | Rich (Python) | Coloured output, spinners, markdown rendering |
| Language | Python 3.10+ | Type hints, dataclasses, zoneinfo |

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- A Google Cloud account with billing enabled
- A Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/akshattandon007/parkmate-ai.git
cd parkmate-ai
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Get your API keys

You need **two keys** to run the agent. Parkopedia is optional.

#### Gemini API Key (required)

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key

> **Note:** Gemini 3.1 Pro requires a paid plan. The agent auto-falls back to Gemini 3 Flash (free tier) if 3.1 Pro quota is exhausted.

#### Google Maps API Key (required)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (e.g. `parkmate-ai`)
3. Enable billing (you get $200/month free credit for Maps)
4. Go to **APIs & Services → Library** and enable:
   - **Geocoding API**
   - **Places API (New)**
   - **Routes API**
5. Go to **APIs & Services → Credentials → Create Credentials → API Key**
6. Restrict the key to the three APIs above (recommended)

#### Parkopedia API Key (optional)

Parkopedia's API is enterprise-only. The agent uses curated fallback data for major UK cities when this key is not set — perfect for demos.

### 5. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
```

Load them:

```bash
export $(grep -v '^#' .env | xargs)
```

### 6. Run the agent

```bash
python carpark_agent.py
```

---

## Usage

Once running, you'll see the ParkMate AI welcome banner. Type your query at the `🚗 You:` prompt.

### Example queries

**Departure-based (Mode A)** — when you mention where you're leaving from:

```
I'm leaving from Great Park in 30 mins, find parking near city centre
Departing Heathrow in 1 hour, need parking near Paddington
Leaving home in 20 mins, cheap parking near Newcastle Quayside
```

**Arrival-based (Mode B)** — when you specify a destination and time:

```
Find a big car park for my Tesla near Newcastle city centre by 6:30pm
Car park in Manchester with EV charging for 3 hours
Cheap parking near London Bridge arriving at 9am tomorrow
```

**Simple queries:**

```
Parking near Newcastle Quayside
Where can I park near Eldon Square?
```

### Controls

- Type `quit`, `exit`, or `q` to stop the agent
- Press `Ctrl+C` to force stop

---

## How the Suitability Scoring Works

Each car park gets a weighted score from 0 to 100:

| Factor | Max Points | Logic |
|--------|-----------|-------|
| Base score | 50 | Starting score for all car parks |
| Proximity | 25 | ≤0.3 mi = 25, ≤0.5 mi = 20, ≤1.0 mi = 10 |
| Availability | 20 | >50 spaces = 20, >20 = 15, >5 = 10, >0 = 5 |
| EV Charging | 10 | Has chargers = 10 |
| Price | 10 | ≤£2/hr = 10, ≤£4/hr = 5 |
| Capacity | 5 | >200 total spaces = 5 |
| Rating | 5 | ≥4.0 stars = 5 |

The top 3 by suitability score are presented to the user.

---

## Booking Platforms

The agent generates pre-filled booking links for multiple UK platforms:

| Platform | Coverage | Notes |
|----------|----------|-------|
| [JustPark](https://www.justpark.com) | 50,000+ spaces UK-wide | Primary booking platform, pre-booking available |
| [YourParkingSpace](https://www.yourparkingspace.co.uk) | 250,000+ spaces | Good alternative with competitive pricing |
| [NCP](https://www.ncp.co.uk) | 500+ NCP car parks | Direct link for NCP-operated car parks |
| [Parkopedia](https://parkopedia.co.uk) | 90M+ spaces globally | Aggregator with deep linking |

Booking links include the arrival time and duration pre-filled, so the user can book in one click.

---

## Project Structure

```
parkmate-ai/
├── carpark_agent.py       # Main agent script (1100+ lines)
├── requirements.txt       # Python dependencies
├── .env.example           # API key template
├── .gitignore             # Git ignore rules
├── WORKFLOW.md            # Detailed agent workflow walkthrough
├── LICENSE                # MIT License
└── README.md              # This file
```

---

## Model Fallback Chain

The agent automatically selects the best available Gemini model:

```
Priority 1: gemini-3.1-pro-preview-customtools  (paid tier — best reasoning)
    ↓ quota error?
Priority 2: gemini-3-flash-preview              (free tier — fast, great at tools)
    ↓ quota error?
Priority 3: gemini-2.5-flash                    (always available — safe fallback)
```

On startup, the agent sends a lightweight ping to each model. The first one that responds without a quota error is selected. You'll see which model was chosen in the console:

```
🤖 Using model: gemini-3-flash-preview
```

Mid-conversation rate limits are handled with automatic retry (15s → 30s backoff).

---

## Limitations and Future Work

### Current limitations

- **Real-time availability** depends on Parkopedia API access (enterprise-only); fallback data is curated and static
- **Booking** is via deep links — not true in-app transactional booking
- **Fallback coverage** is currently focused on Newcastle; extend to more UK cities
- **Gemini 3.1 Pro** requires a paid Google AI plan; free tier users get Gemini 3 Flash

### Future improvements

- Add more UK cities to the fallback database (London, Manchester, Birmingham, Edinburgh, Leeds)
- Integrate NCP's public API for live availability
- Add TfL Open Data for London parking
- Route visualisation on a map (Folium / Google Maps embed)
- Parking reminders and timer notifications
- Apple Wallet / Google Wallet parking pass generation
- Payment integration via JustPark Partner API
- Multi-stop trip planning (park near stop 1, walk to stop 2)

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Author

Built by **Akshat Tandon** — Senior Product Manager exploring AI engineering.

- [GitHub](https://github.com/akshattandon007)
