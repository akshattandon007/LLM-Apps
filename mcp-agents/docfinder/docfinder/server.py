"""DocFinder MCP Server — Healthcare Provider Search via NPPES NPI Registry.

Run as a standalone MCP server over stdio.
"""

import asyncio
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.models import InitializationOptions

from docfinder.nppes_client import NppesClient

server = Server("docfinder", version="1.0.0")
_client: NppesClient | None = None


def _get_client() -> NppesClient:
    global _client
    if _client is None:
        _client = NppesClient()
    return _client


# ── helpers ─────────────────────────────────────────────────────────────────


def _format_error(e: Exception) -> types.CallToolResult:
    return types.CallToolResult(
        content=[types.TextContent(text=f"❌ Error: {e}\n\nPlease check your inputs and try again.")],
        is_error=True,
    )


def _format_provider_list(providers: list, total: int, title: str) -> types.CallToolResult:
    if not providers:
        return types.CallToolResult(
            content=[types.TextContent(
                text=f"No providers found matching **{title}**.\n\nTry broadening your search — use a shorter specialty term, a larger city, or remove the city filter.",
            )]
        )

    lines = [f"**{title}** — {total} provider(s) found\n" if total > len(providers) else f"**{title}** — {len(providers)} provider(s) found\n"]
    
    for i, p in enumerate(providers, 1):
        lines.append(f"\n**{i}.** {p.summary_line()}")
        lines.append(f"   NPI: `{p.npi}`")
    
    if total > len(providers):
        lines.append(f"\n... and {total - len(providers)} more. Narrow your search for more precise results.")
    
    return types.CallToolResult(content=[types.TextContent(text="\n".join(lines))])


# ── tool handlers ──────────────────────────────────────────────────────────


async def handle_find_providers(arguments: dict[str, Any]) -> types.CallToolResult:
    """Find healthcare providers by specialty and/or location."""
    client = _get_client()
    specialty = arguments.get("specialty", "")
    city = arguments.get("city", "")
    state = arguments.get("state", "")
    limit = arguments.get("limit", 10)
    
    providers, total = client.search_providers(
        city=city,
        state=state,
        taxonomy_description=specialty,
        limit=limit,
    )
    title_parts = [part for part in [specialty, f"in {city}" if city else "", state] if part]
    title = "Providers" + (" — " + ", ".join(title_parts) if title_parts else "")
    return _format_provider_list(providers, total, title)


async def handle_find_by_name(arguments: dict[str, Any]) -> types.CallToolResult:
    """Search for providers by name."""
    client = _get_client()
    name = arguments["name"]
    city = arguments.get("city", "")
    state = arguments.get("state", "")
    limit = arguments.get("limit", 10)
    
    providers, total = client.search_by_name(name=name, city=city, state=state, limit=limit)
    loc_parts = [p for p in [city, state] if p]
    loc_str = f" in {', '.join(loc_parts)}" if loc_parts else ""
    title = f"Providers matching '{name}'{loc_str}"
    return _format_provider_list(providers, total, title)


async def handle_find_by_zip(arguments: dict[str, Any]) -> types.CallToolResult:
    """Find providers near a ZIP code."""
    client = _get_client()
    zip_code = arguments["zip_code"]
    specialty = arguments.get("specialty", "")
    limit = arguments.get("limit", 10)
    
    providers, total = client.find_by_zip(zip_code=zip_code, taxonomy_description=specialty, limit=limit)
    spec_str = f" — {specialty}" if specialty else ""
    title = f"Providers near ZIP {zip_code}{spec_str}"
    return _format_provider_list(providers, total, title)


async def handle_get_provider_details(arguments: dict[str, Any]) -> types.CallToolResult:
    """Get full details for a specific provider by NPI number."""
    client = _get_client()
    npi = arguments["npi"]
    provider = client.get_by_npi(npi)
    if not provider:
        return types.CallToolResult(
            content=[types.TextContent(text=f"No provider found with NPI **{npi}**.\n\nCheck the number and try again.")]
        )
    return types.CallToolResult(content=[types.TextContent(text=provider.full_report())])


async def handle_find_by_specialty(arguments: dict[str, Any]) -> types.CallToolResult:
    """Alias for find_providers — focused on specialty search."""
    return await handle_find_providers(arguments)


# ── tool definitions ───────────────────────────────────────────────────────

COMMON_SPECIALTIES = [
    "Dentist", "Physician", "Family Medicine", "Internal Medicine",
    "Pediatrics", "Cardiology", "Dermatology", "Neurology",
    "Optometry", "Chiropractic", "Physical Therapy", "Orthopedic",
    "Radiology", "Anesthesiology", "Surgery", "Obstetrics & Gynecology",
    "Nurse Practitioner", "Physician Assistant", "Counselor",
    "Psychiatry", "Ophthalmology", "Podiatry", "Speech Language Pathologist",
]

TOOL_DEFINITIONS = [
    types.Tool(
        name="find_providers",
        description="Find healthcare providers by specialty and/or location. Use this for general searches like 'dentists in Chicago' or 'cardiologists in Austin TX'. Returns a formatted list with NPI numbers for further detail lookups.",
        inputSchema={
            "type": "object",
            "properties": {
                "specialty": {
                    "type": "string",
                    "description": f"Specialty or taxonomy description. Common: {', '.join(COMMON_SPECIALTIES[:10])} and many more.",
                },
                "city": {"type": "string", "description": "Provider city (e.g. 'Chicago')."},
                "state": {"type": "string", "description": "Two-letter state code (e.g. 'IL', 'TX')."},
                "limit": {"type": "integer", "description": "Max results (1-50). Default 10.", "default": 10},
            },
        },
    ),
    types.Tool(
        name="find_by_name",
        description="Search for healthcare providers by name. Works for individual names ('Smith', 'John Smith') or organization names.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Provider last name, first+last, or organization name."},
                "city": {"type": "string", "description": "Optional city."},
                "state": {"type": "string", "description": "Optional two-letter state code."},
                "limit": {"type": "integer", "description": "Max results (1-50). Default 10.", "default": 10},
            },
            "required": ["name"],
        },
    ),
    types.Tool(
        name="find_by_zip",
        description="Find healthcare providers near a ZIP code. Optionally filter by specialty.",
        inputSchema={
            "type": "object",
            "properties": {
                "zip_code": {"type": "string", "description": "5-digit ZIP code."},
                "specialty": {"type": "string", "description": "Optional specialty filter (e.g. 'Dentist')."},
                "limit": {"type": "integer", "description": "Max results (1-50). Default 10.", "default": 10},
            },
            "required": ["zip_code"],
        },
    ),
    types.Tool(
        name="get_provider_details",
        description="Get full details for a specific provider by NPI number. Returns addresses, phone, all specialties, license numbers, and more.",
        inputSchema={
            "type": "object",
            "properties": {
                "npi": {"type": "string", "description": "10-digit National Provider Identifier (e.g. '1942649421')."},
            },
            "required": ["npi"],
        },
    ),
    types.Tool(
        name="find_by_specialty",
        description="Search providers by specialty across the US. Great for finding 'Dentist', 'Pediatrician', 'Cardiologist' in a city.",
        inputSchema={
            "type": "object",
            "properties": {
                "specialty": {"type": "string", "description": f"Specialty term. Common: {', '.join(COMMON_SPECIALTIES)}."},
                "city": {"type": "string", "description": "City to narrow results."},
                "state": {"type": "string", "description": "Two-letter state code."},
                "limit": {"type": "integer", "description": "Max results (1-50). Default 10.", "default": 10},
            },
            "required": ["specialty"],
        },
    ),
]

TOOL_HANDLERS: dict[str, Any] = {
    "find_providers": handle_find_providers,
    "find_by_name": handle_find_by_name,
    "find_by_zip": handle_find_by_zip,
    "get_provider_details": handle_get_provider_details,
    "find_by_specialty": handle_find_by_specialty,
}


# ── request handlers (registered, not decorated) ──────────────────────────


async def _handle_list_tools(req: types.ListToolsRequest) -> types.ListToolsResult:
    return types.ListToolsResult(tools=TOOL_DEFINITIONS)


async def _handle_call_tool(req: types.CallToolRequest) -> types.CallToolResult:
    handler = TOOL_HANDLERS.get(req.params.name)
    if handler is None:
        return types.CallToolResult(
            content=[types.TextContent(text=f"❌ Unknown tool: {req.params.name}")],
            is_error=True,
        )
    try:
        return await handler(dict(req.params.arguments or {}))
    except Exception as e:
        return _format_error(e)


# Register handlers
server.add_request_handler("tools/list", types.ListToolsRequest, _handle_list_tools)
server.add_request_handler("tools/call", types.CallToolRequest, _handle_call_tool)


# ── entry point ────────────────────────────────────────────────────────────


def main() -> None:
    """Run the DocFinder MCP server over stdio."""
    from mcp.server.stdio import stdio_server
    
    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="docfinder",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(),
                ),
            )
    
    try:
        asyncio.run(_run())
    finally:
        if _client is not None:
            _client.close()


if __name__ == "__main__":
    main()