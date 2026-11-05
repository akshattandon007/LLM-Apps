# Decisions — RateMate

## 1. Frankfurter over exchangerate.host for fiat data
- **Chosen:** Frankfurter API (api.frankfurter.app)
- **Rejected:** exchangerate.host (returned 401), Open Exchange Rates (requires API key), CurrencyFreaks (requires signup)
- **Why:** Frankfurter is the only zero-auth, free, unlimited forex API that resolved successfully during testing. Returns clean JSON with 32 currencies — sufficient coverage for consumer use.

## 2. CoinGecko over CoinMarketCap / CryptoCompare for crypto
- **Chosen:** CoinGecko free tier (no API key, ~10-30 req/min)
- **Rejected:** CoinMarketCap (needs API key), CryptoCompare (needs API key), Nomics (paid)
- **Why:** CoinGecko's `/simple/price` and `/coins/markets` endpoints need zero auth and return rich data (price, market cap, 24h change, ATH). Rate limits are generous for single-user MCP use.

## 3. MCP FastMCP pattern over raw server
- **Chosen:** `mcp.server.fastmcp.FastMCP`
- **Rejected:** Raw `mcp.Server` with manually registered handlers, FastAPI + MCP bridge
- **Why:** FastMCP gives shorter code (decorator-based tool registration), built-in arg validation via pydantic, and auto-generated schemas. All existing MCP agents in this repo use it — consistency matters.

## 4. Single module per domain over monolith
- **Chosen:** `src/exchange.py` + `src/crypto.py`
- **Rejected:** Single `src/client.py`, one function per file, no src/ dir at all
- **Why:** Separating fiat and crypto keeps imports clean and tests focused. Each module has its own API surface and error patterns. No shared state means they're independently testable.

## 5. Async httpx over requests / aiohttp
- **Chosen:** `httpx.AsyncClient`
- **Rejected:** `requests` (blocking), `aiohttp` (heavier dependency), `urllib` (verbose)
- **Why:** httpx is already in the project's dependency tree (used by GradPath, MediMate). async avoids blocking the MCP event loop. The API is clean and modern.

## 6. Direct price check over complex portfolio tracking
- **Chosen:** Simple `crypto_price(coin_id, currency)` — one coin, one price
- **Rejected:** Portfolio tracker with multiple coins in one call, wallet sync, historical portfolio value
- **Why:** MCP tools should be atomic. A user asking "what's Bitcoin at?" wants one answer. Complex portfolio tracking introduces state (held coins, amounts) that's better handled by the LLM, not the tool.

## 7. Curated POPULAR_COINS over dynamic list for fuzzy matching
- **Chosen:** Hardcoded dict of 10 popular coin IDs → display names
- **Rejected:** Auto-fetching /coins/list and fuzzy-searching, user provides exact CoinGecko ID
- **Why:** CoinGecko's /coins/list JSON is 3MB+ and changes. A curated list covers 95% of consumer queries. The `crypto_price` tool still accepts any valid coin ID for edge cases. Best of both worlds.

## 8. CLI via asyncio.run over click / typer
- **Chosen:** `argparse` + `asyncio.run()`
- **Rejected:** `click` (extra dep), `typer` (extra dep), subcommand-per-file pattern
- **Why:** argparse is stdlib — zero extra deps. Asyncio.run() bridges the async tools cleanly to sync CLI. The CLI is a secondary interface (MCP is primary), so keeping it lightweight makes sense.

## 9. Historical rates via date-string endpoint over /timeseries
- **Chosen:** Single `GET /{date}?from=X&to=Y` for each day, wrapped in prompt-hinted loop
- **Rejected:** Frankfurter's range endpoint (`/from..to`), aggregator with daily averages
- **Why:** Frankfurter supports `/from_date..to_date` natively — we use that directly in `historical_rates`. No need for looping.

## 10. Simulated mode via --simulate flag over env var
- **Chosen:** `--simulate` CLI flag
- **Rejected:** `RATEMATE_SIMULATE=1` env var, config file
- **Why:** The flag is explicit and visible in the command, not a hidden env. The user can see they're in sim mode. Only useful for CLI since MCP tools return live API data.

## 11. No database / caching layer
- **Chosen:** Stateless — every call hits the API fresh
- **Rejected:** SQLite cache, Redis, local rate store with TTL
- **Why:** Exchange rates change constantly. Caching adds complexity, a dependency, and stale-data bugs. Frankfurter's response time is ~200ms — fast enough for conversational use. CoinGecko has its own CDN caching.

## 12. Tool return as formatted strings over raw JSON
- **Chosen:** Human-readable markdown tables and sentences
- **Rejected:** Raw dicts, JSON dumps, pydantic models returned
- **Why:** MCP tools return strings that the LLM reads — structured text makes it easier for the model to extract values. The CLI also prints the same formatted output. Raw JSON would force the LLM to re-parse.

## 13. Table format for lists, inline for single results
- **Chosen:** `list_supported_currencies` returns a markdown table; `convert_currency` returns a sentence
- **Rejected:** Everything as a table, everything as a sentence
- **Why:** Lists of data (currencies, top coins) are more scannable as tables. Single conversions read naturally as sentences. The format follows the data shape.

## 14. Error returns as helpful messages over exceptions
- **Chosen:** Tools return descriptive error strings ("Coin 'x' not found. Popular IDs: ...")
- **Rejected:** Raising exceptions, returning None and letting MCP handle it
- **Why:** A descriptive error string includes guidance for the user (which coin IDs to try). The LLM reads the string and can correct itself. Exceptions would show as raw tracebacks to the user.

## 15. CLI demonstrates all tools, MCP is primary
- **Chosen:** CLI (`main.py`) implements every tool as a sub-command
- **Rejected:** CLI is just "python main.py" with no subcommands, CLI only for MCP stdio
- **Why:** Having both MCP and CLI modes means users can test individual tools without an MCP host. Every MCP tool has a matching `crypto-price`, `convert`, etc. CLI subcommand for parity.