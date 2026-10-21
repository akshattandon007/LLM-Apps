# 🔍 DocFinder — Healthcare Provider Search MCP Agent

**Find any doctor, dentist, specialist, or clinic in the US — by location, specialty, name, or NPI number.**

DocFinder is an [MCP (Model Context Protocol)](https://modelcontextprotocol.io) server that searches the official **CMS NPPES NPI Registry** — the same database doctors, hospitals, and insurers use to verify provider credentials. No API key, no signup, no cost.

## What it does

- **Find providers** by specialty and location — "dentists in Chicago", "cardiologists in Austin TX"
- **Search by name** — individual names ("John Smith") or organizations ("Mayo Clinic")
- **Find by ZIP code** — search providers near any US ZIP code, optionally filtered by specialty
- **Get full provider details** — addresses, phone, fax, all taxonomy specialties, license numbers, NPI status
- **300+ specialties** — dentists, physicians, surgeons, physical therapists, counselors, chiropractors, optometrists, and every CMS-recognized taxonomy

## How it works

DocFinder wraps the **NPPES NPI Registry** public API (`npiregistry.cms.hhs.gov`), which indexes every healthcare provider enrolled with Medicare/Medicaid — nearly **10 million provider records**, including both individuals and organizations.

The MCP server exposes 5 tools that any MCP client (Claude Desktop, any MCP-compatible agent) can call directly.

## Tools

| Tool | Description |
|------|-------------|
| `find_providers` | Search by specialty + city/state |
| `find_by_name` | Search by provider name (first, last, or organization) |
| `find_by_zip` | Find providers near a ZIP code |
| `get_provider_details` | Full report for a specific NPI |
| `find_by_specialty` | Alias for specialty-focused search |

## Example queries

- "Find me dentists in Chicago" → `find_providers(specialty="dentist", city="Chicago", state="IL")`
- "Is there a cardiologist in Austin?" → `find_by_specialty(specialty="cardiology", city="Austin", state="TX")`
- "Look up NPI 1942649421" → `get_provider_details(npi="1942649421")`
- "Pediatricians near 60601" → `find_by_zip(zip_code="60601", specialty="pediatrics")`
- "Show me clinics in San Francisco" → `find_providers(city="San Francisco", state="CA")`

## Installation

```bash
# Install from the mcp-agents directory
cd mcp-agents/docfinder
pip install -e .

# Or add to your MCP server config:
# "docfinder": { "command": "python3", "args": ["-m", "docfinder.server"] }
```

## Requirements

- Python 3.10+
- Dependencies: `mcp`, `httpx`, `pydantic` (installed automatically)

## API Source

All data comes from the **NPPES (National Plan & Provider Enumeration System)** — the official US government registry of healthcare providers. The API is free, requires no authentication, and has no rate limits for reasonable usage.

🔗 [NPPES API Docs](https://npiregistry.cms.hhs.gov/registry/help-api)

## Tests

```bash
cd mcp-agents/docfinder
python3 -m pytest tests/ -v
```

The test suite covers:
- Provider parsing (individual and organization types)
- Address and taxonomy extraction
- Search parameter construction
- Tool handler dispatch
- Edge cases (not-found, empty results, unknown tools)

## License

MIT — part of the [LLM-Apps](https://github.com/akshattandon007/LLM-Apps) collection.