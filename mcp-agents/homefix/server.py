"""HomeFix MCP Server — finds, vets, and books home service professionals.

Exposes MCP tools for AI agents to help users find licensed pros,
compare quotes, check licenses, estimate fair prices, and book appointments.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so src imports work
_project_root = str(Path(__file__).resolve().parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from mcp.server import FastMCP

from src.searcher import find_pros as searcher_find_pros
from src.licenser import check_license as licenser_check_license
from src.estimator import get_estimate as estimator_get_estimate
from src.reviewer import summarize_reviews as reviewer_summarize_reviews
from src.scheduler import book_appointment as scheduler_book_appointment
from src.scheduler import get_available_slots

# ── MCP Server Setup ─────────────────────────────────────────────────
server = FastMCP(
    name="homefix",
    instructions="HomeFix — find, vet, and book home service professionals. "
                "License verification, fair price estimates, review summaries, and appointment booking.",
)


# ── Tool: find_pros ──────────────────────────────────────────────────
@server.tool()
def tool_find_pros(service_type: str, zip_code: str, emergency: bool = False) -> str:
    """Find licensed, available home service professionals by type and ZIP code.
    Results sorted by rating descending. Set emergency=True for 24/7 dispatch.
    """
    try:
        results = searcher_find_pros(service_type, zip_code, emergency=emergency)
        if not results:
            return f"No {service_type}s found for ZIP {zip_code}."

        lines = [f"Found {len(results)} {service_type}(s) in area {zip_code}:\n"]
        for i, r in enumerate(results, 1):
            emergency_tag = " 🚨 AVAILABLE NOW" if r.get("available_now") else ""
            licensed_tag = " ✅ Licensed" if r.get("licensed") else " ⚠️ Unlicensed"
            lines.append(
                f"{i}. **{r['name']}** (⭐ {r['rating']} · {r['review_count']} reviews)"
                f"{emergency_tag}{licensed_tag}\n"
                f"   {r['company']} · {r['phone']} · {r['years_in_business']} yrs in business\n"
            )
        return "\n".join(lines)
    except Exception as e:
        return f"Error finding pros: {e}"


# ── Tool: get_estimate ──────────────────────────────────────────────
@server.tool()
def tool_get_estimate(service: str, description: str, zip_code: str) -> str:
    """Get a fair price range estimate for a home service job based on
    regional market data, service type, and job complexity.
    """
    try:
        return estimator_get_estimate(service, description, zip_code)
    except Exception as e:
        return f"Error estimating: {e}"


# ── Tool: check_license ─────────────────────────────────────────────
@server.tool()
def tool_check_license(company: str, state: str) -> str:
    """Verify a home service company's license, insurance, and bond status
    against official state licensing databases.
    """
    try:
        result = licenser_check_license(company, state)
        return (
            f"**License Check — {result['company']} ({result['state']})**\n"
            f"Source: {result['verification_source']}\n"
            f"License #: {result['license_number']}\n\n"
            f"{result['summary']}"
        )
    except Exception as e:
        return f"Error checking license: {e}"


# ── Tool: summarize_reviews ─────────────────────────────────────────
@server.tool()
def tool_summarize_reviews(professional: str) -> str:
    """Get a distilled sentiment summary of customer reviews for a
    home service professional.
    """
    try:
        result = reviewer_summarize_reviews(professional)
        if result["sentiment"] == "unknown":
            return f"No review data available for '{professional}'."

        return (
            f"**Review Summary — {result['company']}**\n"
            f"Rating: ⭐ {result['rating']}/5.0 ({result['review_count']} reviews)\n"
            f"Sentiment: {result['sentiment'].title()}\n\n"
            f"{result['summary']}"
        )
    except Exception as e:
        return f"Error summarizing reviews: {e}"


# ── Tool: compare_quotes ────────────────────────────────────────────
@server.tool()
def tool_compare_quotes(service_type: str, description: str, zip_code: str) -> str:
    """Get price estimates from multiple matched providers for comparison.
    Returns at least 3 quotes with price, duration, and availability.
    """
    try:
        pros = searcher_find_pros(service_type, zip_code)
        if not pros:
            return f"No providers found for {service_type} in {zip_code}."

        general_estimate = estimator_get_estimate(service_type, description, zip_code)

        lines = [
            f"**Quote Comparison — {service_type.title()} in {zip_code}**\n",
            f"Market estimate:\n{general_estimate}\n",
        ]

        for i, r in enumerate(pros[:4], 1):
            score_detail = f"⭐ {r['rating']} ({r['review_count']} reviews)"
            lic = "Licensed ✅" if r.get("licensed") else "Not licensed"
            lines.append(
                f"**Quote {i}: {r['name']}**\n"
                f"   Company: {r['company']}\n"
                f"   Rating: {score_detail}\n"
                f"   Status: {lic} | {r['years_in_business']} years in biz\n"
                f"   Contact: {r['phone']}\n"
            )

        lines.append("Tip: Use `check_license` and `summarize_reviews` to vet before booking.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error comparing quotes: {e}"


# ── Tool: emergency_services ────────────────────────────────────────
@server.tool()
def tool_emergency_services(zip_code: str) -> str:
    """Find 24/7 emergency home service professionals in your area —
    plumbers, electricians, locksmiths, and HVAC technicians available now.
    """
    try:
        emergency_types = ["plumber", "electrician", "locksmith", "hvac"]
        all_results = []

        for st in emergency_types:
            results = searcher_find_pros(st, zip_code, emergency=True)
            for r in results:
                r["service_type"] = st
                all_results.append(r)

        if not all_results:
            return f"No emergency services currently available in ZIP {zip_code}."

        lines = [f"🚨 **Emergency Services Available** near {zip_code}:\n"]
        for r in all_results:
            lines.append(
                f"• **{r['name']}** ({r['service_type'].title()})"
                f" — ⭐ {r['rating']} — {r['phone']}\n"
                f"  Licensed: {'✅' if r.get('licensed') else '❌'} "
                f"· Insured: {'✅' if r.get('insured') else '❌'}\n"
            )

        lines.append("Call now — these pros are available for immediate dispatch.")
        return "\n".join(lines)
    except Exception as e:
        return f"Error finding emergency services: {e}"


# ── Tool: book_appointment ──────────────────────────────────────────
@server.tool()
def tool_book_appointment(pro_name: str, time_slot: str, date_str: str = "") -> str:
    """Book an appointment with a home service professional.
    pro_name: name of the professional. time_slot: time (e.g. '9:00 am' or '14:00').
    date_str: optional YYYY-MM-DD (defaults to tomorrow).
    """
    try:
        date_param = date_str if date_str else None
        result = scheduler_book_appointment(pro_name, time_slot, date_param)
        if not result.get("success"):
            return f"Booking failed: {result.get('error', 'Unknown error')}"

        return (
            f"✅ **Appointment Confirmed!**\n"
            f"Confirmation: `{result['confirmation_number']}`\n"
            f"Professional: {result['professional']} ({result['company']})\n"
            f"Date: {result['appointment_date']} at {result['appointment_time']}\n"
            f"Status: {result['status']}\n\n"
            f"📝 {result.get('notes', '')}"
        )
    except Exception as e:
        return f"Error booking appointment: {e}"


# ── Run ──────────────────────────────────────────────────────────────
def main():
    """Run the HomeFix MCP server via stdio transport."""
    server.run(transport="stdio")


if __name__ == "__main__":
    main()