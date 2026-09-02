"""Subscription Slayer — MCP Server (FastAPI + MCP SDK)

An MCP server that exposes tools for AI agents to scan bank statements
and detect forgotten subscriptions, categorize them, and generate
cancellation information.
"""

import asyncio
import json
import os
import sys
from datetime import date
from typing import Any

# Ensure src is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.fastmcp import FastMCP

from src.canceller import batch_cancellation_info, get_cancellation_info
from src.categorizer import (
    categorize,
    detect_recurring,
    estimate_annual_cost,
    identify_unused,
    track_trials,
)
from src.models import CategorizedSub, Charge, Subscription
from src.scanner import scan_statements, scan_statement_text

# ── MCP Server ─────────────────────────────────────────────────────────────

mcp = FastMCP(
    "subscription-slayer",
    instructions="Find forgotten subscriptions in bank statements and help cancel them. "
    "Scan CSV exports, detect recurring charges, categorize them, "
    "estimate annual costs, and generate cancellation URLs.",
)


# ── Helper: Pydantic → dict serialization ──────────────────────────────────


def _charge_to_dict(c: Charge) -> dict[str, Any]:
    return {
        "date": str(c.transaction_date),
        "description": c.description,
        "amount": c.amount,
        "merchant": c.merchant,
    }


def _sub_to_dict(s: Subscription) -> dict[str, Any]:
    return {
        "merchant": s.merchant,
        "amount": s.amount,
        "frequency": s.frequency.value,
        "first_seen": str(s.first_seen) if s.first_seen else None,
        "last_seen": str(s.last_seen),
        "occurrences": s.occurrences,
    }


def _cat_sub_to_dict(cs: CategorizedSub) -> dict[str, Any]:
    return {
        "merchant": cs.merchant,
        "amount": cs.amount,
        "frequency": cs.frequency.value,
        "category": cs.category.value,
        "annual_cost": cs.annual_cost,
        "is_trial": cs.is_trial,
        "trial_end": str(cs.trial_end) if cs.trial_end else None,
        "first_seen": str(cs.first_seen) if cs.first_seen else None,
        "last_seen": str(cs.last_seen),
        "occurrences": cs.occurrences,
    }


# ── MCP Tools ──────────────────────────────────────────────────────────────


@mcp.tool()
def scan_statements_tool(csv_path: str) -> str:
    """Parse a bank statement CSV file and return all detected transactions.

    Args:
        csv_path: Path to a CSV bank statement file.

    Returns:
        JSON string with list of charges and any parsing errors.
    """
    result = scan_statements(csv_path)
    output = {
        "total_transactions": result.total_transactions,
        "charges": [_charge_to_dict(c) for c in result.charges],
        "errors": result.errors,
    }
    return json.dumps(output, indent=2)


@mcp.tool()
def detect_recurring_tool(charges_json: str) -> str:
    """Identify which charges are recurring subscriptions.

    Args:
        charges_json: JSON string with list of charges (from scan_statements).

    Returns:
        JSON string with detected subscriptions.
    """
    charges_data = json.loads(charges_json)
    charges = [
        Charge(
            date=date.fromisoformat(c["date"]) if isinstance(c.get("date"), str) else c.get("date"),
            description=c.get("description", ""),
            amount=c.get("amount", 0.0),
            merchant=c.get("merchant"),
        )
        for c in charges_data
    ]
    subs = detect_recurring(charges)
    return json.dumps([_sub_to_dict(s) for s in subs], indent=2)


@mcp.tool()
def categorize_tool(subscriptions_json: str) -> str:
    """Categorize subscriptions into groups (streaming, cloud, fitness, etc.) and estimate annual cost.

    Args:
        subscriptions_json: JSON string of subscriptions (from detect_recurring).

    Returns:
        JSON string with categorized subscriptions including annual cost.
    """
    subs_data = json.loads(subscriptions_json)
    subs = [
        Subscription(
            merchant=s.get("merchant", ""),
            amount=s.get("amount", 0.0),
            frequency=s.get("frequency", "monthly"),
            first_seen=date.fromisoformat(s["first_seen"]) if s.get("first_seen") else None,
            last_seen=date.fromisoformat(s["last_seen"]) if s.get("last_seen") else date.today(),
            occurrences=s.get("occurrences", 1),
        )
        for s in subs_data
    ]
    categorized = categorize(subs)
    return json.dumps([_cat_sub_to_dict(cs) for cs in categorized], indent=2)


@mcp.tool()
def estimate_annual_cost_tool(categorized_json: str) -> str:
    """Calculate and display annual cost per category and overall total.

    Args:
        categorized_json: JSON string of categorized subscriptions.

    Returns:
        Human-readable annual cost summary.
    """
    cats_data = json.loads(categorized_json)
    subs = [
        CategorizedSub(
            merchant=c.get("merchant", ""),
            amount=c.get("amount", 0.0),
            frequency=c.get("frequency", "monthly"),
            category=c.get("category", "other"),
            annual_cost=c.get("annual_cost", 0.0),
            is_trial=c.get("is_trial", False),
            trial_end=date.fromisoformat(c["trial_end"]) if c.get("trial_end") else None,
            first_seen=date.fromisoformat(c["first_seen"]) if c.get("first_seen") else None,
            last_seen=date.fromisoformat(c["last_seen"]) if c.get("last_seen") else date.today(),
            occurrences=c.get("occurrences", 1),
        )
        for c in cats_data
    ]
    return estimate_annual_cost(subs)


@mcp.tool()
def identify_unused_tool(categorized_json: str, user_answers_json: str) -> str:
    """Cross-reference user input to find forgotten/unused subscriptions.

    Args:
        categorized_json: JSON string of categorized subscriptions.
        user_answers_json: JSON object mapping merchant names to boolean
            (true=still use it, false=forgotten/don't need).

    Returns:
        JSON array of forgotten subscription names.
    """
    cats_data = json.loads(categorized_json)
    user_answers = json.loads(user_answers_json)
    subs = [
        CategorizedSub(
            merchant=c.get("merchant", ""),
            amount=c.get("amount", 0.0),
            frequency=c.get("frequency", "monthly"),
            category=c.get("category", "other"),
            annual_cost=c.get("annual_cost", 0.0),
        )
        for c in cats_data
    ]
    forgotten = identify_unused(subs, user_answers)
    return json.dumps(forgotten, indent=2)


@mcp.tool()
def get_cancellation_info_tool(service_name: str) -> str:
    """Get cancellation URL and process for a known subscription service.

    Args:
        service_name: Name of the service (e.g., 'netflix', 'spotify').

    Returns:
        Human-readable cancellation information.
    """
    return get_cancellation_info(service_name)


@mcp.tool()
def track_trials_tool(categorized_json: str) -> str:
    """Check which subscriptions are in trial period or about to convert.

    Args:
        categorized_json: JSON string of categorized subscriptions.

    Returns:
        Human-readable trial warnings and status.
    """
    cats_data = json.loads(categorized_json)
    subs = [
        CategorizedSub(
            merchant=c.get("merchant", ""),
            amount=c.get("amount", 0.0),
            frequency=c.get("frequency", "monthly"),
            category=c.get("category", "other"),
            annual_cost=c.get("annual_cost", 0.0),
            is_trial=c.get("is_trial", False),
            trial_end=date.fromisoformat(c["trial_end"]) if c.get("trial_end") else None,
        )
        for c in cats_data
    ]
    result = track_trials(subs)
    return "\n".join(result)


@mcp.tool()
def scan_statement_text_tool(csv_text: str) -> str:
    """Parse a bank statement from raw CSV text (no file needed).

    Args:
        csv_text: Raw CSV content of a bank statement.

    Returns:
        JSON string with list of charges and any parsing errors.
    """
    result = scan_statement_text(csv_text)
    output = {
        "total_transactions": result.total_transactions,
        "charges": [_charge_to_dict(c) for c in result.charges],
        "errors": result.errors,
    }
    return json.dumps(output, indent=2)


# ── Entry points ───────────────────────────────────────────────────────────


def run_server(transport: str = "stdio") -> None:
    """Run the MCP server.

    Args:
        transport: Transport type ('stdio' or 'sse').
          'stdio' (default) is for MCP-compatible clients.
          'sse' serves via HTTP at http://localhost:8000.
    """
    if transport == "sse":
        mcp.run(transport="sse")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    import sys
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    run_server(transport)