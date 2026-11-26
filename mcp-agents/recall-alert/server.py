"""
server.py — Recall Alert MCP Server

Provides tools for checking product safety recalls across multiple sources:
- openFDA: food, drug, medical device, and cosmetic recalls
- NHTSA: vehicle safety recalls by VIN

Usage:
    mcp run server.py
    # or
    python server.py
"""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP

from recall_client import (
    search_food_recall,
    search_vehicle_recall,
    RecallResult,
    set_client,
)

# ── Server setup ─────────────────────────────────────────────────────────────

mcp = FastMCP(
    "recall-alert",
    instructions="Check if products, food, drugs, or vehicles have been recalled. "
    "Search by product name for food/drug recalls, or by VIN for vehicle recalls.",
)


# ── Helper ───────────────────────────────────────────────────────────────────

def _format_recall(r: RecallResult) -> str:
    lines = [
        f"**{r.product}**",
        f"📅 {r.date}  |  ⚠️ {r.classification}",
        f"{r.description}",
    ]
    if r.remedy:
        lines.append(f"🔧 Remedy: {r.remedy}")
    if r.url:
        lines.append(f"🔗 {r.url}")
    return "\n".join(lines)


# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def check_food_recall(product_name: str, limit: int = 10) -> str:
    """Search for food, drug, medical device, or cosmetic recalls by product name.

    Args:
        product_name: The product name or brand to search for (e.g. 'peanut butter', 'infant formula')
        limit: Maximum number of results to return (default 10, max 50)
    """
    try:
        results = search_food_recall(product_name, limit=limit)
    except Exception as e:
        return f"❌ Error searching FDA recalls: {e}"

    if not results:
        return f"✅ No recalls found for '{product_name}'. Product appears safe based on available data."

    output = [f"⚠️ **{len(results)} recall(s) found for '{product_name}'** (source: openFDA)\n"]
    for i, r in enumerate(results, 1):
        output.append(f"---\n### {i}. {_format_recall(r)}")
    return "\n".join(output)


@mcp.tool()
def check_vehicle_recall(vin: str) -> str:
    """Check if a vehicle has open safety recalls by VIN (17 characters).

    Args:
        vin: The 17-character Vehicle Identification Number
    """
    clean = vin.strip().upper()
    if len(clean) != 17:
        return "❌ Invalid VIN. A VIN must be exactly 17 characters (letters A-Z, 0-9)."

    try:
        results = search_vehicle_recall(clean)
    except Exception as e:
        return f"❌ Error searching NHTSA recalls: {e}"

    if not results:
        return f"✅ VIN `{clean}` has no open safety recalls. Vehicle appears safe."

    output = [f"⚠️ **{len(results)} safety recall(s) found for VIN `{clean}`** (source: NHTSA)\n"]
    for i, r in enumerate(results, 1):
        output.append(f"---\n### {i}. {_format_recall(r)}")
    return "\n".join(output)


# ── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()
