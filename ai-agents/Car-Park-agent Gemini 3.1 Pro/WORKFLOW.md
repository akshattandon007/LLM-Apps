# Agent Workflow — Step-by-Step Walkthrough

This document traces the complete execution of ParkMate AI for a departure-based query, showing every tool call, its parameters, the API it hits, and the data it returns.

## Example Query

> **"I will be leaving from Great Park in 30 mins, suggest some car parks by the time I reach city centre"**

---

## Step 0 — Query Parsing (Gemini 3.1 Pro)

The agent receives the user's natural language query. Gemini 3.1 Pro's `thinking_level=MEDIUM` allows it to reason through the request before making any tool calls.

**What the model extracts:**

| Field | Extracted Value | How |
|-------|----------------|-----|
| Origin | "Great Park" | "leaving from Great Park" |
| Destination | "city centre" | "reach city centre" |
| Departure offset | 30 minutes | "in 30 mins" |
| Vehicle type | Not specified | Defaults to "large" |
| EV charging | Not required | No EV/Tesla mention |
| Parking duration | 3 hours | Default |

**Agent's internal reasoning:**

> "The user mentions an origin and a departure offset. This is a Mode A (departure-based) query. I need to geocode both locations, calculate the route to get travel time, project arrival, then search for car parks available at that projected time. 'Great Park' is ambiguous — I'll add 'Newcastle' for context since 'city centre' likely refers to Newcastle."

**Mode selected:** A (departure-based)

---

## Step 1 — Geocode Origin

**Tool:** `geocode_destination`
**API:** Google Maps Geocoding API
**Endpoint:** `GET https://maps.googleapis.com/maps/api/geocode/json`

```
geocode_destination({
    destination: "Great Park Newcastle"
                  ↑ agent adds city context for disambiguation
})
```

**API request parameters:**

```
address  = "Great Park Newcastle, UK"
region   = "uk"
components = "country:GB"
```

**Response:**

```json
{
    "success": true,
    "lat": 55.0190,
    "lng": -1.6220,
    "formatted_address": "Great Park, Newcastle upon Tyne NE13 9BD, UK"
}
```

**Data passed forward:** Origin coordinates `(55.019, -1.622)` → used in Step 3

---

## Step 2 — Geocode Destination

**Tool:** `geocode_destination`
**API:** Google Maps Geocoding API

```
geocode_destination({
    destination: "Newcastle city centre"
})
```

**Response:**

```json
{
    "success": true,
    "lat": 54.9783,
    "lng": -1.6178,
    "formatted_address": "Newcastle upon Tyne City Centre, NE1, UK"
}
```

**Data passed forward:** Destination coordinates `(54.978, -1.617)` → used in Steps 3, 4, 5, 6

---

## Step 3 — Calculate Route (the critical step)

**Tool:** `calculate_route`
**API:** Google Maps Routes API
**Endpoint:** `POST https://routes.googleapis.com/directions/v2:computeRoutes`

This is the step that makes departure-based queries work. It computes real driving time with live traffic conditions and projects when the user will actually arrive.

```
calculate_route({
    origin_lat: 55.0190,          // from Step 1
    origin_lng: -1.6220,
    destination_lat: 54.9783,     // from Step 2
    destination_lng: -1.6178,
    departure_offset_minutes: 30, // user said "in 30 mins"
    travel_mode: "DRIVE"
})
```

**Internal calculation:**

```
now                = 04:20 PM (current time)
departure_time     = 04:20 PM + 30 min = 04:50 PM
                     ↑ this is sent to Routes API as departureTime

Routes API returns  = 22 minutes (with traffic)

estimated_arrival   = 04:50 PM + 22 min = 05:12 PM
                      ↑ THIS drives all subsequent queries
```

**API request body:**

```json
{
    "origin": { "location": { "latLng": { "latitude": 55.019, "longitude": -1.622 } } },
    "destination": { "location": { "latLng": { "latitude": 54.978, "longitude": -1.617 } } },
    "travelMode": "DRIVE",
    "routingPreference": "TRAFFIC_AWARE",
    "departureTime": "2026-03-24T16:50:00Z",
    "languageCode": "en-GB",
    "units": "METRIC"
}
```

**Response:**

```json
{
    "success": true,
    "duration_seconds": 1320,
    "duration_text": "22 min",
    "distance_metres": 8368,
    "distance_text": "5.2 miles (8.4 km)",
    "departure_time": "2026-03-24T16:50:00",
    "departure_time_human": "04:50 PM",
    "estimated_arrival_time": "2026-03-24T17:12:00",
    "estimated_arrival_time_human": "05:12 PM",
    "travel_mode": "DRIVE"
}
```

**Data passed forward:** `estimated_arrival_time = "2026-03-24T17:12:00"` → used as `arrival_datetime` in Step 5

> **Fallback:** If the Routes API fails, the agent estimates travel time using straight-line distance ÷ 25mph + 5min buffer.

---

## Step 4 — Search Nearby Car Parks

**Tool:** `search_nearby_car_parks`
**API:** Google Maps Places API (New)
**Endpoint:** `POST https://places.googleapis.com/v1/places:searchNearby`

```
search_nearby_car_parks({
    lat: 54.9783,             // destination from Step 2
    lng: -1.6178,
    radius_metres: 1500,      // default 1.5km
    vehicle_size: "large",    // default (no vehicle specified)
    require_ev_charging: false
})
```

**API request body:**

```json
{
    "includedTypes": ["parking"],
    "locationRestriction": {
        "circle": {
            "center": { "latitude": 54.9783, "longitude": -1.6178 },
            "radius": 1500.0
        }
    },
    "maxResultCount": 10,
    "rankPreference": "DISTANCE"
}
```

**Response:** 7 car parks found, sorted by distance from destination:

| # | Name | Distance | Google Place ID |
|---|------|----------|----------------|
| 1 | NCP Eldon Square | 0.2 mi | ChIJ... |
| 2 | NCP Dean Street | 0.3 mi | ChIJ... |
| 3 | Eldon Garden Car Park | 0.3 mi | ChIJ... |
| 4 | Quayside Multi-Storey | 0.4 mi | ChIJ... |
| 5 | St James' Park Car Park | 0.5 mi | ChIJ... |
| 6 | Manors Car Park | 0.7 mi | ChIJ... |
| 7 | John Dobson Street | 0.9 mi | ChIJ... |

**Data passed forward:** List of 7 car park candidates → merged with availability in Step 5

---

## Step 5 — Check Availability at Projected Arrival

**Tool:** `check_car_park_availability`
**API:** Parkopedia API v3 (or curated fallback)
**Endpoint:** `GET https://api.parkopedia.com/v3/parking/search`

This is where the ETA from Step 3 pays off — the agent checks availability at 05:12 PM specifically, not the current time.

```
check_car_park_availability({
    lat: 54.9783,
    lng: -1.6178,
    arrival_datetime: "2026-03-24T17:12:00",  // from Step 3's ETA
    duration_hours: 3                          // default
})
```

**Response** (from fallback data when Parkopedia is unavailable):

| Car Park | Spaces | Total | Rate | EV | Height |
|----------|--------|-------|------|-----|--------|
| NCP Eldon Square | 180 | 550 | £3.80/hr | Yes | 2.1m |
| NCP Dean Street | 95 | 420 | £4.20/hr | Yes | 2.0m |
| Eldon Garden | 145 | 480 | £3.50/hr | No | 1.98m |
| Quayside Multi-Storey | 280 | 630 | £2.80/hr | Yes | 2.2m |
| St James' Park | 200 | 350 | £3.00/hr | No | N/A |

**Suitability ranking** (score computed by `CarPark.suitability_score`):

| Rank | Car Park | Score | Why |
|------|----------|-------|-----|
| 1 | Quayside Multi-Storey | 90 | Cheapest + most spaces + EV + large capacity |
| 2 | NCP Eldon Square | 85 | Closest + EV + good availability |
| 3 | NCP Dean Street | 80 | Close + EV + 24hr but pricier |

**Data passed forward:** Top 3 car parks → booking links generated in Step 6

---

## Step 6 — Generate Booking Links

**Tool:** `get_booking_link` (called 3 times — once per recommendation)
**APIs:** JustPark / YourParkingSpace / NCP deep link construction

```
// Call 1 of 3
get_booking_link({
    car_park_name: "Quayside Multi-Storey",
    lat: 54.9690,
    lng: -1.6040,
    arrival_datetime: "2026-03-24T17:12:00",
    duration_hours: 3
})

// Call 2 of 3
get_booking_link({
    car_park_name: "NCP Eldon Square",
    lat: 54.9753,  lng: -1.6147,
    arrival_datetime: "2026-03-24T17:12:00",
    duration_hours: 3
})

// Call 3 of 3
get_booking_link({
    car_park_name: "NCP Dean Street",
    lat: 54.9710,  lng: -1.6120,
    arrival_datetime: "2026-03-24T17:12:00",
    duration_hours: 3
})
```

**Response** (example for Quayside):

```json
{
    "success": true,
    "car_park_name": "Quayside Multi-Storey",
    "primary_booking_url": "https://www.justpark.com/search?q=Quayside%20Multi-Storey&lat=54.969&lng=-1.604&arriving=2026-03-24T17:12&leaving=2026-03-24T20:12",
    "alternatives": {
        "justpark": "https://www.justpark.com/search?...",
        "yourparkingspace": "https://www.yourparkingspace.co.uk/parking/search?...",
        "parkopedia": ""
    }
}
```

For NCP car parks, an additional direct NCP link is generated:

```
https://www.ncp.co.uk/find-a-car-park/car-parks/eldon-square/
```

---

## Step 7 — Final Response

Gemini 3.1 Pro synthesises all tool results into a structured response.

For departure-based queries, the response always leads with a **route summary** before the car park recommendations. This gives the user the full context of their journey.

The agent also adds proactive advice — in this case, noting the evening peak arrival and suggesting pre-booking.

---

## Data Flow Diagram

```
User Query
    │
    ▼
┌─ Geocode Origin ──────────┐  ┌─ Geocode Destination ──────┐
│  "Great Park Newcastle"    │  │  "Newcastle city centre"    │
│  → (55.019, -1.622)       │  │  → (54.978, -1.617)        │
└────────────┬───────────────┘  └────────────┬────────────────┘
             │                               │
             └───────────┬───────────────────┘
                         │
                         ▼
              ┌─ Calculate Route ──────────────────────────┐
              │  Routes API (TRAFFIC_AWARE)                 │
              │  departure_offset = 30 min                  │
              │  → distance: 5.2 mi                        │
              │  → duration: 22 min                        │
              │  → ETA: 05:12 PM  ◄── key output           │
              └─────────────────────┬──────────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
              ▼                     ▼                     │
   ┌─ Search Car Parks ──┐  ┌─ Check Availability ──┐    │
   │  Places API (New)   │  │  Parkopedia / fallback │    │
   │  7 parks found      │  │  at 05:12 PM          │    │
   └──────────┬──────────┘  └──────────┬────────────┘    │
              │                        │                  │
              └────────┬───────────────┘                  │
                       │                                  │
                       ▼                                  │
            ┌─ Merge + Rank ───────┐                     │
            │  Suitability scoring  │                     │
            │  Top 3 selected       │                     │
            └──────────┬────────────┘                     │
                       │                                  │
         ┌─────────────┼─────────────┐                   │
         │             │             │                    │
         ▼             ▼             ▼                    │
   ┌─ Book #1 ─┐ ┌─ Book #2 ─┐ ┌─ Book #3 ─┐          │
   │ Quayside  │ │ Eldon Sq  │ │ Dean St   │           │
   └─────┬─────┘ └─────┬─────┘ └─────┬─────┘          │
         │             │             │                   │
         └─────────────┼─────────────┘                   │
                       │                                  │
                       ▼                                  │
              ┌─ Final Response ──────────────────────┐  │
              │  Route: 5.2mi, 22min, ETA 05:12 PM    │  │
              │  🥇 Quayside — £2.80/hr — 280 spaces  │  │
              │  🥈 Eldon Sq — £3.80/hr — 180 spaces  │  │
              │  🥉 Dean St — £4.20/hr — 95 spaces    │  │
              │  + booking links for each              │  │
              └────────────────────────────────────────┘  │
```

---

## API Call Summary

| Step | API | Endpoint | Billing SKU |
|------|-----|----------|-------------|
| 1 | Geocoding | `maps.googleapis.com/maps/api/geocode/json` | Geocoding (£0.004/req) |
| 2 | Geocoding | Same | Same |
| 3 | Routes | `routes.googleapis.com/directions/v2:computeRoutes` | Routes Pro — TRAFFIC_AWARE (£0.008/req) |
| 4 | Places | `places.googleapis.com/v1/places:searchNearby` | Places Nearby (£0.025/req) |
| 5 | Parkopedia | `api.parkopedia.com/v3/parking/search` | Enterprise (or free fallback) |
| 6 | None | URL construction | Free |

**Total cost per query:** ~£0.041 in Google Maps API calls (well within the $200/month free credit).
