# Flow — MoveMate

## Execution Trace

### Primary Path: `main.py` → CLI → Orchestrator → 5 Agents → Playbook → stdout

```
main()
 ├── parse_args()                    # argparse: --current-zip, --new-zip, etc.
 │   └── Returns argparse.Namespace
 ├── [if --interactive]
 │   └── _interactive_mode()         # Prompts user for each field, returns MoveDetails
 ├── MoveDetails(...)                # Data class with all move info
 ├── run_orchestrator(details)
 │   └── orchestrator.run(details)
 │       │
 │       ├── utility_scheduler.run(details)
 │       │   └── UtilityInfo         # Utility lookup table + household size notes
 │       │
 │       ├── address_changer.run(details)
 │       │   └── AddressChangeInfo   # Categorized checklist (gov/finance/subs/ins)
 │       │
 │       ├── cost_estimator.run(details)
 │       │   ├── _estimate_distance_miles(zip1, zip2)
 │       │   │   └── int, float: distance + multiplier (zip-first-digit heuristic)
 │       │   └── CostEstimate        # Itemized costs + 15% buffer
 │       │
 │       ├── neighborhood_scout.run(details)
 │       │   ├── utils.nominatim_geocode(query)
 │       │   │   └── dict {lat, lon, display_name, address} or None
 │       │   ├── [if geo succeeds]
 │       │   │   ├── utils.osm_nearby_amenities(lat, lon, radius=1000)
 │       │   │   │   └── list[str]: "Name (type)" for up to 15 amenities
 │       │   │   ├── utils.wikipedia_summary(city_part, sentences=2)
 │       │   │   │   └── str|None: extract paragraph
 │       │   │   └── utils.openmeteo_forecast(lat, lon)
 │       │   │       └── dict|None: 7-day temperature/precipitation
 │       │   └── NeighborhoodInfo    # Amenities, transit, parks, weather
 │       │
 │       ├── timeline_architect.run(details)
 │       │   └── list[TimelineEntry] # 8 entries: T-8w → T-6w → T-4w → T-2w
 │       │                              → T-1w → Move Day → T+1w → T+2w
 │       │
 │       └── Playbook(move_details, utilities, address_changes, costs,
 │                     neighborhood, timeline)
 │
 ├── playbook.to_markdown()          # Renders everything as formatted Markdown
 │   └── str
 └── [if -o flag] write file / else print() 
```

### Secondary Path: Help / Validation Errors
```
main()
 ├── parse_args()                    # --help shows argparse epilog (__doc__)
 ├── [missing required flags]        # Prints error + usage hint
 └── return 1
```

## Module Dependency Graph

```
main.py
  ├── models.py        [MoveDetails, Playbook, UtilityInfo, ...]
  ├── orchestrator.py
  │   ├── models.py
  │   ├── agents/utility_scheduler.py
  │   │   └── models.py
  │   ├── agents/address_changer.py
  │   │   └── models.py
  │   ├── agents/cost_estimator.py
  │   │   └── models.py
  │   ├── agents/neighborhood_scout.py
  │   │   ├── models.py
  │   │   └── utils.py     [nominatim_geocode, osm_nearby_amenities,
  │   │                       openmeteo_forecast, wikipedia_summary]
  │   └── agents/timeline_architect.py
  │       └── models.py
  │
  └── models.py    (indirect, via orchestrator)
```

## Data Flow

```
User Input (CLI / interactive)
         │
         ▼
  MoveDetails {current_zip, new_zip, move_date, household_size, is_renting}
         │
         ├──────────────────────────────────────────────────────────┐
         │                                                          │
         ▼                                                          ▼
  5 Specialized Agents                                      utils.py helpers
  (each returns its own data model)                         (free web APIs)
         │                                                          │
         ├── UtilityInfo ───────────────────────────────────────────┤
         ├── AddressChangeInfo                                      │
         ├── CostEstimate ─── _estimate_distance_miles() ───────────┤
         ├── NeighborhoodInfo ─── nominatim_geocode() ──────────────┤
         │                     ├── osm_nearby_amenities() ──────────┤
         │                     ├── wikipedia_summary() ─────────────┤
         │                     └── openmeteo_forecast() ────────────┤
         └── list[TimelineEntry] ───────────────────────────────────┘
                  │
                  ▼
         Playbook (aggregates all models)
                  │
                  ▼
         Playbook.to_markdown()
                  │
                  ▼
         stdout OR file (Markdown)
```

## Agent Communication Pattern

Unlike sequential pipeline architectures, MoveMate uses an **independent-agent** pattern:

1. The orchestrator receives `MoveDetails`
2. It calls all 5 agents **sequentially** (not in parallel — Python GIL makes threading unnecessary for simple I/O calls)
3. Each agent returns its own dataclass
4. The orchestrator assembles them into `Playbook`
5. Agents do NOT talk to each other — no inter-agent message passing
6. Result: `Playbook` is a flat aggregate, not a nested dependency chain

This makes agents independently testable and swappable. Adding a 6th agent requires: write the agent module + add one line to the orchestrator.