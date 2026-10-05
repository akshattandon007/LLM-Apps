"""RecallGuard MCP Server — Vehicle Recalls via NHTSA.

Run as a standalone MCP server, or use `main()` as a CLI entry point.
"""

from typing import Any

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from recallguard.nhtsa_client import NhtsaClient

server = Server("recallguard")
_client: NhtsaClient | None = None


def _get_client() -> NhtsaClient:
    global _client
    if _client is None:
        _client = NhtsaClient()
    return _client


# ── tool implementations ────────────────────────────────────────────────────


async def _get_recall_years() -> list[types.TextContent]:
    """Get all model years that have recall data available."""
    client = _get_client()
    years = client.get_model_years()
    if not years:
        return [types.TextContent(type="text", text="No recall data years found.")]
    text = "**📅 Available Model Years**\n\n"
    # Show ranges for readability
    nums = sorted(int(y) for y in years if y.isdigit() and int(y) > 1900)
    if nums:
        text += f"Range: {min(nums)} – {max(nums)}  ({len(nums)} years)\n\n"
        text += ", ".join(str(y) for y in nums)
    else:
        text += ", ".join(years)
    return [types.TextContent(type="text", text=text)]


async def _get_recall_makes(model_year: str) -> list[types.TextContent]:
    """Get all manufacturers (makes) with recalls in a given model year."""
    client = _get_client()
    makes = client.get_makes(model_year)
    if not makes:
        return [
            types.TextContent(
                type="text",
                text=f"No manufacturers found for model year {model_year}.",
            )
        ]
    text = (
        f"**🏭 Manufacturers with Recalls — {model_year}**\n\n"
        f"Total: {len(makes)} makes\n\n"
        + "\n".join(f"• {m}" for m in makes)
    )
    return [types.TextContent(type="text", text=text)]


async def _get_recall_models(make: str, model_year: str) -> list[types.TextContent]:
    """Get all models for a given make and year that have recalls."""
    client = _get_client()
    models = client.get_models(make, model_year)
    if not models:
        return [
            types.TextContent(
                type="text",
                text=f"No models found for {make} ({model_year}) with recalls.",
            )
        ]
    text = (
        f"**🚗 {make} Models with Recalls — {model_year}**\n\n"
        f"Total: {len(models)} models\n\n"
        + "\n".join(f"• {m}" for m in models)
    )
    return [types.TextContent(type="text", text=text)]


async def _check_recalls(
    make: str, model: str, model_year: str
) -> list[types.TextContent]:
    """Check recalls for a specific vehicle by year/make/model."""
    client = _get_client()
    records = client.check_vehicle_recalls(make, model, model_year)
    if not records:
        return [
            types.TextContent(
                type="text",
                text=(
                    f"✅ **No open recalls found** for "
                    f"{model_year} {make} {model}.\n\n"
                    "Stay safe out there! 🚗"
                ),
            )
        ]

    text = (
        f"**⚠ {len(records)} Recall(s) Found for "
        f"{model_year} {make} {model}**\n\n"
        + "\n\n".join(r.full_report() for r in records)
    )
    return [types.TextContent(type="text", text=text)]


async def _lookup_campaign(campaign_number: str) -> list[types.TextContent]:
    """Look up a specific recall by its NHTSA campaign number (e.g. '20V682000')."""
    client = _get_client()
    records = client.get_recall_by_campaign(campaign_number)
    if not records:
        return [
            types.TextContent(
                type="text",
                text=(
                    f"No recall found for campaign number **{campaign_number}**.\n"
                    "Check the number and try again."
                ),
            )
        ]
    text = (
        f"**🔍 Recall Campaign: {campaign_number}**\n\n"
        + "\n\n".join(r.full_report() for r in records)
    )
    return [types.TextContent(type="text", text=text)]


# ── tool registration ───────────────────────────────────────────────────────


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_recall_years",
            description="List all vehicle model years that have NHTSA recall data available.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_recall_makes",
            description="List manufacturers with recalls in a given model year.",
            inputSchema={
                "type": "object",
                "properties": {
                    "model_year": {
                        "type": "string",
                        "description": "Vehicle model year (e.g. '2020', '2023'). Use get_recall_years to see available years.",
                    }
                },
                "required": ["model_year"],
            },
        ),
        types.Tool(
            name="get_recall_models",
            description="List vehicle models for a make and year that have recalls.",
            inputSchema={
                "type": "object",
                "properties": {
                    "make": {
                        "type": "string",
                        "description": "Vehicle manufacturer (e.g. 'TOYOTA', 'FORD'). Use get_recall_makes to list available makes.",
                    },
                    "model_year": {
                        "type": "string",
                        "description": "Vehicle model year (e.g. '2020').",
                    },
                },
                "required": ["make", "model_year"],
            },
        ),
        types.Tool(
            name="check_vehicle_recalls",
            description="Check for open safety recalls on a specific vehicle by year, make, and model.",
            inputSchema={
                "type": "object",
                "properties": {
                    "make": {
                        "type": "string",
                        "description": "Vehicle manufacturer (e.g. 'TOYOTA', 'FORD').",
                    },
                    "model": {
                        "type": "string",
                        "description": "Vehicle model (e.g. 'COROLLA', 'F-150').",
                    },
                    "model_year": {
                        "type": "string",
                        "description": "Vehicle model year (e.g. '2020').",
                    },
                },
                "required": ["make", "model", "model_year"],
            },
        ),
        types.Tool(
            name="get_recall_by_campaign",
            description="Look up a specific recall by its NHTSA campaign number.",
            inputSchema={
                "type": "object",
                "properties": {
                    "campaign_number": {
                        "type": "string",
                        "description": "NHTSA campaign number (e.g. '20V682000', '23V865000').",
                    }
                },
                "required": ["campaign_number"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(
    name: str, arguments: dict[str, Any]
) -> list[types.TextContent]:
    try:
        if name == "get_recall_years":
            return await _get_recall_years()
        elif name == "get_recall_makes":
            return await _get_recall_makes(arguments["model_year"])
        elif name == "get_recall_models":
            return await _get_recall_models(
                arguments["make"], arguments["model_year"]
            )
        elif name == "check_vehicle_recalls":
            return await _check_recalls(
                arguments["make"],
                arguments["model"],
                arguments["model_year"],
            )
        elif name == "get_recall_by_campaign":
            return await _lookup_campaign(arguments["campaign_number"])
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Error: {e}\n\nPlease check your inputs and try again.",
            )
        ]


# ── entry point ─────────────────────────────────────────────────────────────


def main() -> None:
    """Run the MCP server over stdio."""
    try:
        mcp.server.stdio.run(
            server,
            InitializationOptions(
                server_name="recallguard",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    request_handler=None,
                ),
            ),
        )
    finally:
        if _client is not None:
            _client.close()


if __name__ == "__main__":
    main()