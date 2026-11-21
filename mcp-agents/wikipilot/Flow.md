# Flow — WikiPilot

## Execution Trace

### 1. Startup

```
User/Client launches MCP server
  └─ python -m mcp run server.py
       └─ FastMCP creates server named "WikiPilot" with instructions
            └─ Tool definitions registered as @mcp.tool() decorators
                 └── Tools: search_wikipedia, summarize_article, read_article,
                      random_article, today_in_history, related_articles,
                      article_categories
                 └── FastMCP auto-generates JSON Schema from function signatures
            └── Server listens on stdin/stdout (stdio transport)
```

### 2. Tool Call: `search_wikipedia(query, limit)`

```
MCP Client sends {"method": "tools/call", "params": {"name": "search_wikipedia", "arguments": {"query": "quantum physics", "limit": 5}}}
  └─ FastMCP routes to search_wikipedia(query="quantum physics", limit=5)
       └─ wikipilot_client.search_articles("quantum physics", limit=5)
            └─ _fetch_legacy({"action": "query", "list": "search", "srsearch": "quantum physics", "srlimit": "5", "srprop": "snippet"})
                 └─ urllib.request.urlopen("https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch=quantum+physics&srlimit=5&srprop=snippet&format=json")
                      └─ Wikipedia API returns JSON
                 └─ Parse JSON, extract ["query"]["search"][]
                 └─ For each hit: clean snippet (_strip_html), build result dict
            └─ Returns list of {title, page_id, snippet, url}
       └─ Format results as markdown string with emoji headers
  └─ Returns CallToolResult(content=[TextContent(text="📚 Search results for **quantum physics**\n1. **Quantum mechanics**...")])
```

### 3. Tool Call: `summarize_article(title)`

```
MCP Client → FastMCP → summarize_article("Python (programming language)")
  └─ wikipilot_client.get_summary("Python (programming language)")
       └─ _fetch(f"{API_BASE}/page/summary/Python_(programming_language)")
            └─ urllib.request.urlopen("https://en.wikipedia.org/api/rest_v1/page/summary/Python_(programming_language)")
            └─ Returns JSON: {title, extract, thumbnail, content_urls, pageid, ...}
       └─ Return {title, extract[:2000], thumbnail_url, url, page_id}
  └─ Format as "## Python (programming language)\n![](...)\n\n{extract}\n\n🔗 [Read on Wikipedia](...)"
  └─ Returns formatted markdown string
```

### 4. Tool Call: `read_article(title)`

```
MCP Client → FastMCP → read_article("Earth")
  └─ wikipilot_client.get_article("Earth")
       └─ _fetch(f"{API_BASE}/page/summary/Earth")  → basic metadata
       └─ _fetch(f"{API_BASE}/page/html/Earth")      → full HTML content
            └─ _strip_html() to remove tags
       └─ Truncate to 25K chars if needed
       └─ Return {title, content, url, page_id}
  └─ Format as "# Earth\n\n{content}\n\n🔗 {url}"
  └─ Returns truncated article text
```

### 5. Tool Call: `random_article()`

```
MCP Client → FastMCP → random_article()
  └─ wikipilot_client.get_random_article()
       └─ _fetch(f"{API_BASE}/page/random/summary")
       └─ Returns same shape as get_summary but for a random page
  └─ Format as "## 🎲 Random article: {title}\n..."
  └─ Returns formatted markdown
```

### 6. Tool Call: `today_in_history(month, day)`

```
MCP Client → FastMCP → today_in_history(month=7, day=20)
  └─ wikipilot_client.on_this_day(month=7, day=20)
       └─ _fetch(f"{API_BASE}/feed/onthisday/events/7/20")
       └─ Parse ["events"][]: {year, text, content_urls, ...}
       └─ Return list of {year, description[:300], url}
  └─ Format as "## 📜 On this day (7/20)\n1. **1969** — Apollo 11 moon landing...\n..."
  └─ Returns up to 20 events with "… and N more" if exceeded
```

### 7. Tool Call: `related_articles(title)`

```
MCP Client → FastMCP → related_articles("Albert Einstein", limit=3)
  └─ wikipilot_client.get_related_articles("Albert Einstein", limit=3)
       └─ _fetch(f"{API_BASE}/page/related/Albert_Einstein")
       └─ Parse ["pages"][:limit]: {title, content_urls, ...}
       └─ Return list of {title, url}
  └─ Format as "## 🔗 Related to **Albert Einstein**\n1. **...**\n..."
```

### 8. Tool Call: `article_categories(title)`

```
MCP Client → FastMCP → article_categories("Moon")
  └─ wikipilot_client.get_article_categories("Moon")
       └─ _fetch_legacy({"action": "query", "titles": "Moon", "prop": "categories", "cllimit": "max"})
       └─ Parse ["query"]["pages"][*]["categories"][]
       └─ Strip "Category:" prefix, sort alphabetically
       └─ Return list of strings
  └─ Format as "## 🏷️ Categories for **Moon**\n1. Natural satellites\n2. Solar System\n..."
```

---

## Module Dependency Graph

```
server.py (FastMCP)
  ├── wikipilot_client.py (API client)
  │     └── urllib.request (stdlib HTTP)
  │     └── json (stdlib JSON)
  │     └── re (stdlib HTML stripping)
  │     └── datetime (on_this_day defaults)
  └── mcp.server.fastmcp (FastMCP framework)
        └── mcp.types (Tool, TextContent, CallToolResult)

tests/
  └── test_wikipilot.py
        └── wikipilot_client (direct unit tests of client module)
```

---

## Data Flow

```
User Question
  └─ "What's the history of the Eiffel Tower?"
       └─ LLM decides to call summarize_article("Eiffel Tower")
            └─ FastMCP dispatches to server.py handler
                 └─ wikipilot_client.get_summary("Eiffel Tower")
                      └─ GET https://en.wikipedia.org/api/rest_v1/page/summary/Eiffel_Tower
                           └─ Wikipedia returns JSON
                      └─ Clean and structure response
                 └─ Format as readable markdown with thumbnail link
            └─ Return to LLM as text
       └─ LLM reads summary, may call read_article for more depth
            └─ Same flow but with /page/html/ endpoint
       └─ LLM answers user with citations from Wikipedia
```

---

## Error Flow

```
Article Not Found:
  handler → wikipilot_client.get_summary("FakeArticle")
    → _fetch() catches HTTPError(404)
    → raises ArticleNotFound("Not found: https://...")
  → handler catches ArticleNotFound
  → returns "❌ Article not found: 'FakeArticle'. Try searching with search_wikipedia first."

Network Error:
  handler → wikipilot_client.get_summary("...")
    → _fetch() catches URLError (DNS failure, timeout, connection refused)
    → raises WikipediaError("Network error: [Errno ...]")
  → handler catches WikipediaError
  → returns "Wikipedia API error: Network error: ..."
```