# Flow — execution trace from MCP tool call to output

## Architecture overview

```
MCP Host (Claude Desktop, Cline, etc.)
        │  stdio JSON-RPC
        ▼
┌────────────────────────────────────────────┐
│          server.py (MCP Server)             │
│                                              │
│  list_tools() → 5 tools advertised           │
│  call_tool(name, args) → route to handler    │
│                                              │
│  Handlers:                                    │
│    whats_on_right_now(args)                   │
│    whats_on_tonight(args)                     │
│    search_show(args)                          │
│    find_similar_shows(args)                   │
│    daily_schedule(args)                       │
└────────────┬────────────────────┬─────────────┘
             │                    │
             ▼                    ▼
     ┌──────────────┐   ┌──────────────────┐
     │ schedule.py  │   │   search.py      │
     │              │   │                  │
     │ • right_now  │   │ • search_show()  │
     │ • tonight    │   │ • search_genre() │
     │ • daily      │   └──────┬───────────┘
     └──────┬───────┘          │
            │                  │
            ▼                  ▼
     ┌──────────────────────────────┐
     │     tvmaze.py (API Client)    │
     │                               │
     │  TVMazeClient                 │
     │    • schedule(country, date)  │
     │    • search_show(query)       │
     │    • show_by_name(name)       │
     │    • shows_page(page)         │
     │    • _get(path, params)       │
     └────────────┬──────────────────┘
                  │
                  ▼
         api.tvmaze.com (REST)
```

## Tool call chains

### 1. whats_on_right_now("US", genre="comedy")

```
call_tool("whats_on_right_now", {"country": "US", "genre": "comedy"})
  → schedule.whats_on_right_now(client, "US", "comedy")
    → client.schedule("US", date=today_iso)
      → tvmaze.TVMazeClient._get("/schedule", {"country": "US", "date": "2026-09-12"})
        → httpx GET https://api.tvmaze.com/schedule?country=US&date=2026-09-12
        → returns list[dict] of episodes with nested show data
    → for each episode:
      → ScheduleEntry.from_tvmaze(episode_data)
        → Show.from_schedule_episode(episode_data)
      → filter: airtime hour in [current_hour, current_hour+2]
      → filter: if genre specified, check show.genres
    → _format_show_list(shows, heading)
      → builds string with numbered shows, rating, genres, summary
  → returns str
```

### 2. search_show("Breaking Bad")

```
call_tool("search_show", {"query": "Breaking Bad"})
  → search.search_show(client, "Breaking Bad")
    → client.search_show("Breaking Bad")
      → tvmaze.TVMazeClient._get("/search/shows", {"q": "Breaking Bad"})
        → httpx GET https://api.tvmaze.com/search/shows?q=Breaking+Bad
        → returns list[{score, show}]
    → for each result:
      → Show.from_tvmaze_show(result["show"])
    → format into string
  → returns str
```

### 3. find_similar_shows("The Office")

```
call_tool("find_similar_shows", {"show_name": "The Office"})
  → recommendations.find_similar_shows(client, "The Office")
    → client.show_by_name("The Office")
      → httpx GET https://api.tvmaze.com/singlesearch/shows?q=The+Office
      → returns dict (single show)
    → Show.from_tvmaze_show(source)
    → extract source genres + rating
    → genres.discover_by_genre(client, source_genres, limit=30)
      → paginate /shows?page=0..N
      → filter by genre overlap
    → for each candidate:
      → score = (genre_overlap * 3) + rating_proximity_score
    → sort by score descending, take top 8
    → format into string
  → returns str
```

### 4. daily_schedule("2026-09-12", "GB")

```
call_tool("daily_schedule", {"date": "2026-09-12", "country": "GB"})
  → schedule.daily_schedule(client, "2026-09-12", "GB")
    → client.schedule("GB", "2026-09-12")
      → httpx GET https://api.tvmaze.com/schedule?country=GB&date=2026-09-12
    → for each episode:
      → ScheduleEntry.from_tvmaze(episode)
      → collect shows
    → _format_show_list(shows, heading)
  → returns str
```

## Data flow

```
Raw TVMaze JSON  →  Pydantic Model  →  Filter/Score  →  Formatted string
                                       (genre, hour,    (numbered list with
                                        rating delta)     emoji, rating, summary)
```

## Error handling

- Network errors: TVMazeError → caught in call_tool → returned as TextContent error
- Empty results: each function returns a friendly "Nothing found" message
- Unknown genres: normalize_genre_input returns [] → user sees valid genre list
- Show not found (similar): "Could not find show '{name}' on TVMaze."