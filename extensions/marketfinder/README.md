# MarketFinder

**Find farmers markets, CSAs, and food hubs near you — with SNAP/WIC filtering.**

MarketFinder is an [MCP](https://modelcontextprotocol.io) server that queries the USDA Local Food Portal API to help people find fresh, local food. It answers questions like:

> *"Where's the nearest farmers market that takes SNAP near 10001?"*
> *"Find CSAs with pickup spots near 97201."*
> *"What are the hours for the Portland Farmers Market?"*

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Run as MCP server (stdio)
python -m marketfinder.server

# Or via the mcp CLI
mcp run marketfinder/server.py
```

## Tools

| Tool | Description |
|------|-------------|
| `find_markets(zip, radius_miles=10)` | Markets, on-farm markets & food hubs near a ZIP |
| `filter_by_program(zip, program)` | Filter by SNAP / WIC / WICcash / SFMNP / all |
| `get_market_details(market_id)` | Hours, directions, products, social links, contact |
| `find_csa(zip)` | CSA pickup spots near a ZIP |

## Built-in Demo Mode

If the USDA API is unreachable (no internet, rate-limited, etc.), MarketFinder automatically falls back to **simulated Portland, OR** data so you can always demo the server.

## Project Structure

```
marketfinder/
├── __init__.py          # Package init
├── server.py            # MCP server & tool definitions
├── api.py               # USDA API client with fallback
├── models.py            # Pydantic models
tests/
├── test_marketfinder.py # pytest with mocked httpx
requirements.txt
README.md
Decisions.md
Flow.md
```

## Architecture

- **set_client() injection pattern** — swap `httpx.Client` for testing without touching production code
- **Graceful fallback** — every function catches exceptions and returns realistic simulated data
- **Pydantic all the way** — structured return types so AI agents can iterate on typed results
- **Zero auth** — the USDA API is public, no keys needed