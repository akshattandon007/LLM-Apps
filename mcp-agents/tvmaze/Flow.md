# TVMaze MCP Server — Flow

## Execution Trace

```
mcp run server.py
│
├─ mcp.server.fastmcp.FastMCP (__init__)
│  └─ Registers 6 tools from decorators in server.py
│
├─ Agent invokes tool → FastMCP dispatches to registered async function
│
├─ search_tv_shows(query: str)
│  ├─ tvmaze_client.search_shows(query)
│  │  ├─ _get_client() → httpx.Client (or injected mock)
│  │  ├─ GET /search/shows?q=<query>
│  │  ├─ resp.raise_for_status()
│  │  └─ Show.from_dict(item["show"]) for each result
│  ├─ fallback: simulate_search_shows(query)
│  │  └─ Returns 2 simulated Show objects with source="simulated"
│  └─ Returns formatted Markdown string
│
├─ get_show_details(show_id: int)
│  ├─ tvmaze_client.get_show_by_id(show_id)
│  │  ├─ _get_client()
│  │  ├─ GET /shows/<id>
│  │  ├─ resp.raise_for_status()
│  │  └─ Show.from_dict(resp.json())
│  └─ Returns formatted Markdown string with all fields
│
├─ get_episode_list(show_id: int, season: int?)
│  ├─ tvmaze_client.get_episodes(show_id)
│  │  ├─ _get_client()
│  │  ├─ GET /shows/<id>/episodes
│  │  ├─ resp.raise_for_status()
│  │  └─ [Episode.from_dict(e) for e in resp.json()]
│  ├─ Optionally filters by season
│  ├─ fallback: simulate_episodes(show_name, season_count)
│  │  └─ Returns 2-3 episodes per season with source="simulated"
│  └─ Returns formatted Markdown string
│
├─ get_cast_list(show_id: int)
│  ├─ tvmaze_client.get_cast(show_id)
│  │  ├─ _get_client()
│  │  ├─ GET /shows/<id>/cast
│  │  ├─ resp.raise_for_status()
│  │  └─ [CastMember.from_dict(c) for c in resp.json()]
│  └─ Returns formatted Markdown string
│
├─ get_tv_schedule(country: str, date: str?)
│  ├─ tvmaze_client.get_schedule(country, date)
│  │  ├─ _get_client()
│  │  ├─ GET /schedule?country=<country>[&date=<date>]
│  │  ├─ resp.raise_for_status()
│  │  └─ Builds list of ScheduleItem objects
│  └─ Returns formatted Markdown string
│
└─ search_celebrities(name: str)
   ├─ tvmaze_client.search_people(name)
   │  ├─ _get_client()
   │  ├─ GET /search/people?q=<name>
   │  ├─ resp.raise_for_status()
   │  └─ Returns raw API response (dicts)
   └─ Returns formatted Markdown string
```

## Module Dependency Graph

```
server.py
  ├── mcp.server.fastmcp  (FastMCP framework)
  └── tvmaze_client.py
       ├── httpx           (HTTP client)
       └── dataclasses     (data models)
            └── Show
            └── Episode
            └── CastMember
            └── ScheduleItem

tests/test_tvmaze.py
  ├── tvmaze_client.py     (testing client functions)
  ├── server.py            (testing tool imports)
  └── httpx                (MockTransport for mocks)
```

## Data Flow

```
User Query
    │
    ▼
Agent decides which tool to call
    │
    ├─ "find shows about dogs"  → search_tv_shows("dogs")
    ├─ "details for show 42"    → get_show_details(42)
    ├─ "episodes of show 42"    → get_episode_list(42)
    ├─ "cast of show 42"        → get_cast_list(42)
    ├─ "what's on TV tonight"   → get_tv_schedule(country="US")
    └─ "who is Tom Hanks"       → search_celebrities("Tom Hanks")
    │
    ▼
server.py tool function
    │
    ├─ Tries tvmaze_client.*() → HTTP to api.tvmaze.com
    │   │
    │   ├─ On success: Parse JSON → Data model → Markdown string
    │   │
    │   └─ On failure: Fall back to simulated data
    │
    └─ Returns formatted Markdown response
    │
    ▼
Agent sees structured result and formulates final answer
```

## Key Design Decisions in Data Flow

1. **All responses are Markdown strings** — the MCP protocol passes tool results as text to the LLM. Structured Markdown (bold headers, bullet lists) maximizes agent comprehension.

2. **Live API first, simulated fallback** — every tool tries the real TVMaze API first. If that fails (network error, rate limit, API down), the tool gracefully degrades to procedurally generated mock data marked with `source="simulated"`.

3. **Source tracking on every model** — the `source: str` field on Show, Episode, CastMember, and ScheduleItem records whether the data came from the live API (`"live"`) or simulation (`"simulated"`), enabling auditability.

4. **No caching layer** — TV show data changes slowly (new episodes, updated ratings). The TVMaze API is fast enough that caching adds complexity without measurable benefit for an agent tool.