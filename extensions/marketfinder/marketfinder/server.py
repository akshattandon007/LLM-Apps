"""MarketFinder MCP server — USDA farmers market locator.

Run with:
    python -m marketfinder.server
    mcp run marketfinder/server.py
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .api import (
    filter_by_program as _filter_by_program,
    get_market_details as _get_market_details,
    search_by_zip as _search_by_zip,
    search_csa as _search_csa,
)
from .models import CSASearchResult, MarketSearchResult, Program

mcp = FastMCP(
    "MarketFinder",
    instructions=(
        "Find farmers markets, CSAs, and food hubs near you. "
        "Filter by SNAP/WIC acceptance, check operating hours, and get directions."
    ),
)


# ── Tools ─────────────────────────────────────────────────────────────


@mcp.tool()
def find_markets(zip: str, radius_miles: int = 10) -> str:
    """Find farmers markets, on-farm markets, and food hubs near a ZIP code.

    Args:
        zip: 5-digit US ZIP code to search around.
        radius_miles: Search radius in miles (default 10).
    """
    result = _search_by_zip(zip, radius_miles)
    return _format_market_result(result)


@mcp.tool()
def filter_by_program(zip: str, program: str) -> str:
    """Filter markets by food-assistance program (SNAP, WIC, WICcash, SFMNP, or 'all').

    Args:
        zip: 5-digit US ZIP code.
        program: One of 'SNAP', 'WIC', 'WICcash', 'SFMNP', or 'all'.
    """
    normalized = program.strip().lower().capitalize()
    valid = {p.value for p in Program}
    if normalized not in valid:
        normalized = "all"
    result = _filter_by_program(zip, normalized)
    return _format_market_result(result)


@mcp.tool()
def get_market_details(market_id: str) -> str:
    """Get operating hours, directions, products, social links, and contact info for a specific market.

    Args:
        market_id: The USDA market ID (e.g. 'sim-pdx-001' or a real USDA id).
    """
    details = _get_market_details(market_id)
    lines = [
        f"**{details.market_name}**",
        f"📍 {details.directions or 'Address not available'}",
        f"📅 Season: {details.season_dates or 'N/A'}",
        f"⏰ Hours: {details.season_hours or 'N/A'}",
        f"📞 Contact: {details.contact_name or 'N/A'}",
        f"  Phone: {details.contact_phone or 'N/A'}",
        f"  Email: {details.contact_email or 'N/A'}",
        f"🌐 Website: {details.website or 'N/A'}",
        f"📘 Facebook: {details.facebook or 'N/A'}",
        f"🐦 Twitter: {details.twitter or 'N/A'}",
        f"▶️ YouTube: {details.youtube or 'N/A'}",
    ]
    programs = []
    if details.accepts_snap:
        programs.append("SNAP ✅")
    if details.accepts_wic:
        programs.append("WIC ✅")
    if details.accepts_wic_cash:
        programs.append("WICcash ✅")
    if details.accepts_sfmnp:
        programs.append("SFMNP ✅")
    if programs:
        lines.append(f"💳 Accepted: {', '.join(programs)}")

    schedule = details.schedule or details.season_dates or ""
    if schedule:
        lines.append(f"📆 Schedule: {schedule}")
    if details.products:
        lines.append(f"🛒 Products: {details.products}")

    return "\n".join(lines)


@mcp.tool()
def find_csa(zip: str) -> str:
    """Find Community Supported Agriculture (CSA) pickup spots near a ZIP code.

    Args:
        zip: 5-digit US ZIP code.
    """
    result = _search_csa(zip)
    return _format_csa_result(result)


# ── formatters ────────────────────────────────────────────────────────


def _format_market_result(result: MarketSearchResult) -> str:
    if not result.markets:
        return f"No markets found near {result.zip} within {result.radius_miles} miles."

    lines = [
        f"Found **{result.count}** market(s) near {result.zip} (within {result.radius_miles} mi):",
        "",
    ]
    for i, m in enumerate(result.markets, 1):
        programs = []
        if m.accepts_snap:
            programs.append("SNAP")
        if m.accepts_wic:
            programs.append("WIC")
        if m.accepts_wic_cash:
            programs.append("WICcash")
        if m.accepts_sfmnp:
            programs.append("SFMNP")
        prog_str = f" [{', '.join(programs)}]" if programs else ""

        items = [
            f"**{i}. {m.market_name}**{prog_str}",
            f"   📍 {m.address or 'N/A'}, {m.city or ''} {m.state or ''} {m.zip_code or ''}",
            f"   📏 {m.distance or 'N/A'}",
        ]
        if m.products:
            items.append(f"   🛒 {m.products}")
        if m.season_dates:
            items.append(f"   📅 {m.season_dates} — {m.season_hours or ''}")
        if m.website:
            items.append(f"   🌐 {m.website}")
        lines.extend(items)
        lines.append("")

    return "\n".join(lines).strip()


def _format_csa_result(result: CSASearchResult) -> str:
    if not result.csa_locations:
        return f"No CSA locations found near {result.zip}."

    lines = [
        f"Found **{result.count}** CSA location(s) near {result.zip}:",
        "",
    ]
    for i, c in enumerate(result.csa_locations, 1):
        items = [
            f"**{i}. {c.operation_name}**",
            f"   📍 {c.address or 'N/A'}, {c.city or ''} {c.state or ''} {c.zip_code or ''}",
            f"   📏 {c.distance or 'N/A'}",
        ]
        if c.website:
            items.append(f"   🌐 {c.website}")
        if c.contact_name or c.contact_phone or c.contact_email:
            contact = "   📞 " + ", ".join(
                filter(None, [c.contact_name, c.contact_phone, c.contact_email])
            )
            items.append(contact)
        lines.extend(items)
        lines.append("")

    return "\n".join(lines).strip()


# ── entry point ───────────────────────────────────────────────────────


def main() -> None:
    """Run the MCP server (stdio transport by default)."""
    mcp.run()


if __name__ == "__main__":
    main()