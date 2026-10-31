# Flow.md — BookWorm MCP

## Execution Trace

### Entry Point
```
user query (Claude Desktop)
  → MCP protocol (stdio JSON-RPC)
    → bookworm/__main__.py::main()
      → bookworm/server.py::main()
        → mcp.run(transport="stdio")              # FastMCP event loop
```

### Tool Dispatch
```
FastMCP receives JSON-RPC "tools/call" request
  → Matches tool name to registered @mcp.tool()
  → Validates arguments via Pydantic
  → Calls the tool function
  → Returns JSON-RPC result
```

### Tool Call Chains

#### search_books(query, limit, page)
```
search_books(query="harry potter", limit=5, page=1)
  → get_client()  # Lazy-init OpenLibraryClient singleton
  → OpenLibraryClient.search_books("harry potter", limit=5, page=1)
    → RateLimiter.wait()  # 3 req/sec cap
    → httpx.GET https://openlibrary.org/search.json?q=harry+potter&limit=5&page=1
    → Response JSON parse
  → _clean_book_doc(doc)  # Extract fields from each result
  → Return [{"total_results": N, "page": 1, "results_returned": 5}, {book1}, ...]
```

#### get_book(isbn, olid)
```
get_book(isbn="0451526538", olid="")
  → get_client()
  → if isbn:
      OpenLibraryClient.get_book_by_isbn("0451526538")
        → RateLimiter.wait()
        → httpx.GET https://openlibrary.org/api/books?bibkeys=ISBN:0451526538&format=json&jscmd=data
        → Parse response
      → Build result dict (title, authors, publish_date, cover_url, etc.)
  → elif olid:
      OpenLibraryClient.get_book_by_olid(olid)
        → RateLimiter.wait()
        → httpx.GET https://openlibrary.org/books/{olid}.json
      → _clean_edition(edition)
  → Return dict
```

#### get_author(author_id, include_works)
```
get_author("OL23919A", include_works=True)
  → get_client()
  → OpenLibraryClient.get_author("OL23919A")
    → RateLimiter.wait()
    → httpx.GET https://openlibrary.org/authors/OL23919A.json
  → OpenLibraryClient.get_author_photo_url("OL23919A")  # Build covers URL
  → if include_works:
      OpenLibraryClient.get_author_works("OL23919A", limit=10)
        → RateLimiter.wait()
        → httpx.GET https://openlibrary.org/authors/OL23919A/works.json?limit=10
  → Return author dict with notable works list
```

#### search_subject(subject, limit, page)
```
search_subject("fantasy", limit=10, page=1)
  → get_client()
  → OpenLibraryClient.search_subject("fantasy", limit=10, page=1)
    → RateLimiter.wait()
    → httpx.GET https://openlibrary.org/subjects/fantasy.json?limit=10&offset=0
  → _clean_book_doc(doc) for each work
  → Return [{"subject": "fantasy", "total_works": N}, {book1}, ...]
```

#### search_authors(query, limit)
```
search_authors("tolkien", limit=10)
  → get_client()
  → OpenLibraryClient.search_authors("tolkien", limit=10)
    → RateLimiter.wait()
    → httpx.GET https://openlibrary.org/search/authors.json?q=tolkien&limit=10
  → Build clean author dicts with key, name, dates, top subjects
  → Return [{"total_results": N}, {author1}, ...]
```

#### get_book_cover(olid, size)
```
get_book_cover("OL123M", size="M")
  → get_client()
  → OpenLibraryClient.get_book_cover_url("OL123M", "M")
    → Build URL: https://covers.openlibrary.org/b/olid/OL123M-M.jpg
  → Return URL string
```

#### get_trending(limit)
```
get_trending(limit=10)
  → get_client()
  → OpenLibraryClient.get_trending(limit=10)
    → RateLimiter.wait()
    → httpx.GET https://openlibrary.org/search.json?q=*&sort=latest_revision&limit=10
  → _clean_book_doc(doc) for each
  → Return [{"total_results": N}, {book1}, ...]
```

## Module Dependency Graph

```
bookworm/__main__.py
  └── bookworm/server.py          (MCP tool definitions, entry point)
        ├── mcp (FastMCP)         (MCP framework — external dep)
        │     └── Pydantic        (argument validation — external dep)
        └── bookworm/open_library_client.py  (API HTTP client)
              ├── httpx           (HTTP client — external dep)
              └── time            (rate limiting — stdlib)
```

## Key Data Flow

```
User: "Find me books about machine learning"

  ┌─────────────────────┐
  │ Claude Desktop       │
  │ (MCP Client)         │
  └───────┬──────────────┘
          │ JSON-RPC "tools/call"
          │ method=search_books
          │ params={query: "machine learning", limit: 5}
          ▼
  ┌─────────────────────┐
  │ FastMCP Router       │  ← bookworm/server.py
  │ @mcp.tool()          │
  └───────┬──────────────┘
          │ search_books("machine learning", 5, 1)
          ▼
  ┌─────────────────────┐
  │ OpenLibraryClient    │  ← bookworm/open_library_client.py
  │ search_books()       │
  └───────┬──────────────┘
          │ http GET
          ▼
  ┌─────────────────────┐
  │ Open Library API     │  ← openlibrary.org/search.json
  │ (free, zero-auth)    │
  └───────┬──────────────┘
          │ JSON response
          ▼
  ┌─────────────────────┐
  │ _clean_book_doc()    │  ← bookworm/server.py
  │ Extract: title,      │
  │ author, year, ISBN,  │
  │ cover URL, subjects   │
  └───────┬──────────────┘
          │ Cleaned dict
          ▼
  ┌─────────────────────┐
  │ Claude Desktop       │
  │ "Here are 5 books    │
  │ about machine        │
  │ learning..."         │
  └──────────────────────┘
```

## Test Coverage Map

| Test File | What it covers |
|-----------|---------------|
| tests/test_server.py::TestSearchBooks | Client search with results, empty, pagination |
| tests/test_server.py::TestGetBook | ISBN lookup, OLID lookup |
| tests/test_server.py::TestAuthor | Author details, author works |
| tests/test_server.py::TestSubject | Subject search |
| tests/test_server.py::TestCleanBookDoc | Field extraction edge cases (all present, all missing) |
| tests/test_server.py::TestCleanEdition | Edition cleaning edge cases |
| tests/test_server.py::TestServerTools | MCP tool dispatch and response shape |
| tests/test_server.py::TestLiveAPI | Integration tests (skipped by default, use -m integration) |