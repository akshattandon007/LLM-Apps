"""
MediMate MCP Server — Drug safety & pharmacy intelligence.

Provides MCP tools to search drug labels, check adverse events,
find generic alternatives, and browse NDC codes — all via OpenFDA (free, zero-auth).

Run as an MCP stdio server:
    python server.py
"""

import asyncio
from typing import Any

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import TextContent, Tool

from medimate.client import OpenFDAClient

# ── Server setup ──────────────────────────────────────────────────────

server = Server("medimate")
client = OpenFDAClient()


def _format_result(data: dict[str, Any], label: str = "") -> str:
    """Render a result dict as readable Markdown."""
    lines: list[str] = []
    if label:
        lines.append(f"## {label}")
    lines.append(f"_{data['total']} result(s) found_")
    if data.get("pages", 1) > 1:
        lines.append(f"_Page 1 of {data['pages']}_")
    lines.append("")

    for i, r in enumerate(data.get("results", []), 1):
        lines.append(f"### #{i}: {r.get('_brand_name', 'Unknown')}")
        if r.get("_generic_name"):
            lines.append(f"**Generic:** {r['_generic_name']}")
        if r.get("_active_ingredients"):
            ingredients = ", ".join(r["_active_ingredients"])
            lines.append(f"**Active ingredients:** {ingredients}")
        if r.get("_manufacturer"):
            lines.append(f"**Manufacturer:** {r['_manufacturer']}")

        for fld, label_fld in [
            ("_warnings", "⚠️ Warnings"),
            ("_drug_interactions", "⚡ Interactions"),
            ("_purpose", "🎯 Purpose / Uses"),
            ("_stop_use", "🛑 When to stop use"),
            ("_do_not_use", "🚫 Do not use if"),
            ("_pregnancy_or_breast_feeding", "🤰 Pregnancy / Breastfeeding"),
            ("_questions", "📞 Questions / Contact"),
        ]:
            if r.get(fld):
                lines.append(f"\n**{label_fld}:**\n{r[fld]}")

        lines.append("")
    return "\n".join(lines)


# ── Tool definitions ──────────────────────────────────────────────────

@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_drug",
            description="Search for a prescription or OTC drug by brand or generic name. Returns label info including warnings, interactions, active ingredients, and manufacturer.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Drug brand name or generic name (e.g. 'Tylenol', 'acetaminophen')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 10)",
                        "default": 10,
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="check_adverse_events",
            description="Search adverse drug event reports for a specific drug. Returns reported patient reactions, outcomes, and severity.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Drug name to search adverse events for",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 10)",
                        "default": 10,
                    },
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="find_generic_alternatives",
            description="Find brand-name drugs that contain a given active ingredient / substance. Use this to find cheaper generic alternatives.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ingredient": {
                        "type": "string",
                        "description": "Active ingredient / substance name (e.g. 'acetaminophen', 'ibuprofen', 'atorvastatin')",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results (default 20)",
                        "default": 20,
                    },
                },
                "required": ["ingredient"],
            },
        ),
        Tool(
            name="ndc_lookup",
            description="Look up a drug product by its National Drug Code (NDC). Returns product details, labeler, and active ingredients.",
            inputSchema={
                "type": "object",
                "properties": {
                    "ndc": {
                        "type": "string",
                        "description": "Full NDC code (e.g. '15631-0404-0')",
                    },
                },
                "required": ["ndc"],
            },
        ),
        Tool(
            name="browse_drugs",
            description="Browse recently updated drug labels with pagination. Use this to explore available drugs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {
                        "type": "integer",
                        "description": "Page number (default 1)",
                        "default": 1,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Items per page (default 50)",
                        "default": 50,
                    },
                },
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[TextContent]:
    args = arguments or {}
    try:
        if name == "search_drug":
            data = client.search_drug(args["name"], args.get("limit", 10))
            text = _format_result(data, f"🔍 Drug: {args['name']}")
        elif name == "check_adverse_events":
            data = client.get_adverse_events(args["name"], args.get("limit", 10))
            text = _format_result(data, f"⚠️ Adverse Events for: {args['name']}")
        elif name == "find_generic_alternatives":
            data = client.find_generic_brands(args["ingredient"], args.get("limit", 20))
            text = _format_result(data, f"💊 Brands containing: {args['ingredient']}")
            if data["total"] == 0:
                text = f"❌ No brand-name drugs found containing '{args['ingredient']}'. Try a different spelling or active ingredient name."
        elif name == "ndc_lookup":
            ndc = args["ndc"]
            data = client.get_by_ndc(ndc)
            if data["total"] == 0:
                data = client.get_label_by_ndc(ndc)
            text = _format_result(data, f"📦 NDC: {ndc}")
            if data["total"] == 0:
                text = f"❌ No drug found for NDC '{ndc}'. Check the format (e.g. '12345-1234-0')."
        elif name == "browse_drugs":
            data = client.browse_ingredients(
                args.get("limit", 50), args.get("page", 1)
            )
            text = _format_result(data, "📋 Recent Drug Labels")
        else:
            text = f"Unknown tool: {name}"

        return [TextContent(type="text", text=text)]
    except Exception as exc:
        return [TextContent(type="text", text=f"❌ Error: {exc}")]


# ── Entry point ───────────────────────────────────────────────────────

async def main() -> None:
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="medimate",
                server_version="0.1.0",
                capabilities=server.get_capabilities(),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())